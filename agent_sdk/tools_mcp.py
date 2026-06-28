"""Custom search/fetch tools for the Agent SDK, backed by YOUR keys (SERPER + JINA + EXA) —
NOT Anthropic's built-in WebSearch/WebFetch (which don't execute when routed off-Claude).

Two responsibilities live here, and ONLY here (they are run-harness concerns, not core):
  1. Capable search/fetch: Serper (paginated google search + dedup), Jina reader (robust
     extraction + size cap), optional Exa neural search.
  2. The as-of guard *at the tool boundary*. The generic policy is `futurecast.guard.as_of`
     (core, source-agnostic). The SOURCE-SPECIFIC timestamp extraction (Serper `date` field,
     Jina `Published Time:` header, Exa `publishedDate`) lives HERE — never in core
     (AGENTS.md guardrail #3). Cutoff is read from env FUTURECAST_AS_OF (ISO date); when set,
     anything dated after it is blocked mechanically before it can reach the model.

Tool names exposed to the model:
  mcp__futurecast__web_search, mcp__futurecast__read_webpage, mcp__futurecast__exa_search.
"""
from __future__ import annotations

import os
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

import httpx
from claude_agent_sdk import tool, create_sdk_mcp_server

# Make the futurecast package importable when this module is run from agent_sdk/.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
from futurecast.guard.as_of import check_as_of  # noqa: E402  generic as-of policy (core)

SERPER_URL = "https://google.serper.dev/search"
JINA_READER = (os.environ.get("JINA_BASE_URL") or "https://r.jina.ai").rstrip("/")
EXA_URL = "https://api.exa.ai/search"

# Per-fetch size cap fed to the model (chars). Jina pages can be huge; keep context bounded.
READ_CHAR_CAP = 12000


# --------------------------------------------------------------------------------------
# as-of helpers (SOURCE-SPECIFIC date parsing — allowed here, the run harness, not in core)
# --------------------------------------------------------------------------------------
def _cutoff() -> Optional[str]:
    """The active as-of cutoff (ISO date) or None if the run is unguarded."""
    v = (os.environ.get("FUTURECAST_AS_OF") or "").strip()
    return v or None


_MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def parse_loose_date(text: str) -> Optional[str]:
    """Best-effort: pull a single content date out of `text`, return ISO `YYYY-MM-DD` or None.

    Handles ISO dates, 'Jun 10, 2026' / '10 Jun 2026', and relative 'N days/weeks/months ago'
    (resolved against today). Conservative: returns the FIRST confident match only.
    """
    if not text:
        return None
    t = text.strip()

    # relative: "3 days ago", "2 weeks ago", "1 month ago", "5 hours ago"
    m = re.search(r"(\d+)\s+(hour|day|week|month|year)s?\s+ago", t, re.I)
    if m:
        n, unit = int(m.group(1)), m.group(2).lower()
        days = {"hour": 0, "day": 1, "week": 7, "month": 30, "year": 365}[unit] * (n if unit != "hour" else 0)
        return (date.today() - timedelta(days=days)).isoformat()
    if re.search(r"\b(today|yesterday)\b", t, re.I):
        off = 0 if re.search(r"today", t, re.I) else 1
        return (date.today() - timedelta(days=off)).isoformat()

    # ISO 2026-06-10  /  slash 2026/6/27
    m = re.search(r"\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b", t)
    if m:
        return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"

    # 'Jun 10, 2026' or 'June 10, 2026'
    m = re.search(r"\b([A-Za-z]{3,9})\s+(\d{1,2}),?\s+(\d{4})\b", t)
    if m and m.group(1)[:3].lower() in _MONTHS:
        mo = _MONTHS[m.group(1)[:3].lower()]
        return f"{int(m.group(3)):04d}-{mo:02d}-{int(m.group(2)):02d}"

    # '10 Jun 2026'
    m = re.search(r"\b(\d{1,2})\s+([A-Za-z]{3,9})\s+(\d{4})\b", t)
    if m and m.group(2)[:3].lower() in _MONTHS:
        mo = _MONTHS[m.group(2)[:3].lower()]
        return f"{int(m.group(3)):04d}-{mo:02d}-{int(m.group(1)):02d}"
    return None


def _after_cutoff(iso_date: Optional[str], cutoff: str) -> bool:
    if not iso_date:
        return False
    try:
        return date.fromisoformat(iso_date) > date.fromisoformat(cutoff)
    except ValueError:
        return False


# Date tokens that may appear INLINE in a snippet/page body (vs. the structured `date` field).
# Used to catch the real leak: a price page whose nominal publish date is pre-cutoff but whose
# snippet embeds today's (post-cutoff) value, e.g. "江苏 2026/6/27 ... 土杂猪 9.80".
_INLINE_DATE = re.compile(
    r"\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b"
    r"|\b([A-Za-z]{3,9})\s+(\d{1,2}),?\s+(\d{4})\b"
    r"|(\d{4})年(\d{1,2})月(\d{1,2})日")


def _has_post_cutoff_date(text: str, cutoff: str) -> bool:
    """True if `text` embeds any explicit date strictly after `cutoff`."""
    for m in _INLINE_DATE.finditer(text or ""):
        iso = parse_loose_date(m.group(0).replace("年", "-").replace("月", "-").replace("日", ""))
        if _after_cutoff(iso, cutoff):
            return True
    return False



def _serper_tbs(cutoff: str) -> Optional[str]:
    """Google custom-date-range tbs that caps results at the cutoff (mechanical search guard)."""
    try:
        d = date.fromisoformat(cutoff)
    except ValueError:
        return None
    return f"cdr:1,cd_min:01/01/2000,cd_max:{d.month}/{d.day}/{d.year}"


# --------------------------------------------------------------------------------------
# tools
# --------------------------------------------------------------------------------------
@tool("web_search",
      "Search the web (Serper/Google). Args: query (str), num (int<=10, default 8), "
      "page (int>=1, default 1). Honors the run's as-of cutoff: results are restricted to "
      "on/before the cutoff and any result with a later date is dropped.",
      {"query": str, "num": int, "page": int})
async def web_search(args: dict) -> dict:
    key = os.environ.get("SERPER_API_KEY")
    if not key:
        return {"content": [{"type": "text", "text": "[web_search error: SERPER_API_KEY not set]"}]}
    cutoff = _cutoff()
    num = max(1, min(int(args.get("num") or 8), 10))
    page = max(1, int(args.get("page") or 1))
    payload = {"q": args["query"], "num": num, "page": page}
    if cutoff:
        tbs = _serper_tbs(cutoff)
        if tbs:
            payload["tbs"] = tbs
    async with httpx.AsyncClient(timeout=45, trust_env=False) as c:
        r = await c.post(SERPER_URL, headers={"X-API-KEY": key, "Content-Type": "application/json"},
                         json=payload)
        r.raise_for_status()
        data = r.json()

    seen: set[str] = set()
    lines: list[str] = []
    dropped = 0
    redacted = 0
    for it in (data.get("organic") or []):
        link = (it.get("link") or "").rstrip("/")
        if not link or link in seen:
            continue
        seen.add(link)
        when = parse_loose_date(it.get("date") or "")
        if cutoff and _after_cutoff(when, cutoff):
            dropped += 1
            continue
        snippet = it.get("snippet", "") or ""
        # Second guard layer: a pre-cutoff page can still leak a post-cutoff value inside its
        # snippet (dynamic price pages). Redact such snippets; keep title+link so the model
        # knows the source exists and can fetch the *historical* value via read_webpage.
        if cutoff and _has_post_cutoff_date(snippet, cutoff):
            snippet = "[snippet redacted: embeds data dated after the as-of cutoff]"
            redacted += 1
        tag = f" [{when}]" if when else ""
        lines.append(f"- {it.get('title','')}{tag}\n  {link}\n  {snippet}")
    head = (f"[as-of {cutoff}: capped to <= cutoff; {dropped} post-cutoff result(s) dropped, "
            f"{redacted} snippet(s) redacted]\n") if cutoff else ""
    body = "\n".join(lines) or "[no results]"
    return {"content": [{"type": "text", "text": head + body}]}


@tool("read_webpage",
      "Fetch a URL as clean reader text (Jina r.jina.ai). Args: url (str). If the page's "
      "publication date is after the run's as-of cutoff, the page is blocked (it did not exist "
      "at as-of); otherwise an as-of banner is prepended and content is size-capped.",
      {"url": str})
async def read_webpage(args: dict) -> dict:
    cutoff = _cutoff()
    headers = {"X-Return-Format": "markdown"}
    key = os.environ.get("JINA_API_KEY")
    if key:
        headers["Authorization"] = f"Bearer {key}"
    async with httpx.AsyncClient(timeout=90, trust_env=False, follow_redirects=True) as c:
        r = await c.get(f"{JINA_READER}/{args['url']}", headers=headers)
        r.raise_for_status()
        text = r.text

    if cutoff:
        # Jina prepends a metadata block incl. "Published Time:" when the source exposes it.
        pub = None
        m = re.search(r"Published Time:\s*(.+)", text)
        if m:
            pub = parse_loose_date(m.group(1))
        verdict = check_as_of(text if pub is None else f"Published Time: {pub}", cutoff,
                              lambda _t: pub)
        # Policy here is LENIENT on unknown pub date (a reader of an undated page is still
        # useful), but STRICT when a publication date is known and post-cutoff: that page did
        # not exist at as-of, so block it outright.
        if pub is not None and not verdict.allowed:
            return {"content": [{"type": "text", "text":
                    f"[BLOCKED: page published {pub} is after as-of cutoff {cutoff}; cannot be used]"}]}
        banner = (f"[AS-OF {cutoff}] Ignore anything on this page dated after {cutoff}. "
                  f"Detected publication date: {pub or 'unknown'}.\n\n")
        text = banner + text
    return {"content": [{"type": "text", "text": text[:READ_CHAR_CAP]}]}


@tool("exa_search",
      "Neural/semantic web search (Exa). Args: query (str), num (int<=10, default 6). "
      "Restricted to documents published on/before the run's as-of cutoff.",
      {"query": str, "num": int})
async def exa_search(args: dict) -> dict:
    key = os.environ.get("EXA_API_KEY")
    if not key:
        return {"content": [{"type": "text", "text": "[exa_search error: EXA_API_KEY not set]"}]}
    cutoff = _cutoff()
    num = max(1, min(int(args.get("num") or 6), 10))
    payload: dict = {"query": args["query"], "numResults": num, "type": "auto"}
    if cutoff:
        payload["endPublishedDate"] = f"{cutoff}T23:59:59.000Z"
    async with httpx.AsyncClient(timeout=45, trust_env=False) as c:
        r = await c.post(EXA_URL, headers={"x-api-key": key, "Content-Type": "application/json"},
                         json=payload)
        r.raise_for_status()
        data = r.json()
    lines: list[str] = []
    dropped = 0
    for it in (data.get("results") or [])[:num]:
        when = parse_loose_date(it.get("publishedDate") or "")
        if cutoff and _after_cutoff(when, cutoff):
            dropped += 1
            continue
        tag = f" [{when}]" if when else ""
        lines.append(f"- {it.get('title','')}{tag}\n  {it.get('url','')}")
    head = f"[as-of {cutoff}: {dropped} post-cutoff result(s) dropped]\n" if cutoff else ""
    return {"content": [{"type": "text", "text": head + ("\n".join(lines) or "[no results]")}]}


def create_server():
    """In-process MCP server bundling the custom tools. Pass to ClaudeAgentOptions(mcp_servers=...).

    Exa is only registered when EXA_API_KEY is present (it is optional).
    """
    tools = [web_search, read_webpage]
    if os.environ.get("EXA_API_KEY"):
        tools.append(exa_search)
    return create_sdk_mcp_server(name="futurecast", version="0.2.0", tools=tools)


# Tool names the runner should allow. Built-in WebSearch/WebFetch are disallowed (they don't
# execute off-Claude); local Bash/Read/Edit/Write are kept enabled by the runner.
ALLOWED = [
    "mcp__futurecast__web_search",
    "mcp__futurecast__read_webpage",
    "mcp__futurecast__exa_search",
    "Bash", "Read", "Edit", "Write",
]
DISALLOWED_BUILTINS = ["WebSearch", "WebFetch"]
