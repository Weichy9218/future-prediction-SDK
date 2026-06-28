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

# Content budgets (chars). We do NOT blind-truncate (Claude-Code-style): small pages return
# whole; large pages are reduced by relevance windowing, then an optional cheap-LLM extraction.
RETURN_BUDGET = 30000        # return a page untouched up to this size
EXTRACT_INPUT_CAP = 45000    # max chars fed to the extractor (window first if larger)


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

    # US order with year last: 06-26-2026 / 6/26/2026 (common in data-vendor snippets, e.g. CEIC)
    m = re.search(r"\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b", t)
    if m:
        return f"{int(m.group(3)):04d}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"

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
    r"(?<!\d)(\d{4})[-/](\d{1,2})[-/](\d{1,2})(?!\d)"   # 2026-06-26 / 2026/6/27
    r"|(?<!\d)(\d{1,2})[-/](\d{1,2})[-/](\d{4})(?!\d)"  # 06-26-2026 / 6/26/2026 (US, year last)
    r"|([A-Za-z]{3,9})\s+(\d{1,2}),?\s+(\d{4})"          # Jun 26, 2026
    r"|(\d{4})年(\d{1,2})月(\d{1,2})日")                  # 2026年6月26日 (may be glued to CJK)


def _has_post_cutoff_date(text: str, cutoff: str) -> bool:
    """True if `text` embeds any explicit date strictly after `cutoff`."""
    for m in _INLINE_DATE.finditer(text or ""):
        iso = parse_loose_date(m.group(0).replace("年", "-").replace("月", "-").replace("日", ""))
        if _after_cutoff(iso, cutoff):
            return True
    return False


def _target() -> Optional[str]:
    """The question's target date (ISO) — the value AT this date is what must NOT leak."""
    v = (os.environ.get("FUTURECAST_TARGET") or "").strip()
    return v or None


def _mentions_target(text: str, target: str) -> bool:
    """True if `text` names the target date in any common form, INCLUDING yearless ones.

    This is the precise leak guard: the realized value is usually presented next to the target
    date (e.g. Yahoo's 'At close: June 26', a 'June 26, 2026' quote, '6月26日'). Yearless dates
    evade the post-cutoff scan, so we match the target's month/day directly.
    """
    try:
        d = date.fromisoformat(target)
    except ValueError:
        return False
    mon_abbr = ["jan", "feb", "mar", "apr", "may", "jun",
                "jul", "aug", "sep", "oct", "nov", "dec"][d.month - 1]
    pats = [
        rf"(?<!\d){d.year}[-/]0?{d.month}[-/]0?{d.day}(?!\d)",       # 2026-06-26
        rf"(?<!\d)0?{d.month}[-/]0?{d.day}[-/]{d.year}(?!\d)",       # 06-26-2026
        rf"{d.year}年0?{d.month}月0?{d.day}日",                      # 2026年6月26日
        rf"0?{d.month}月0?{d.day}日",                                # 6月26日 (yearless)
        rf"(?i){mon_abbr}[a-z]*\.?\s+0?{d.day}(?!\d)",              # June 26 / Jun 26 (yearless)
    ]
    return any(re.search(p, text or "") for p in pats)




def _serper_tbs(cutoff: str) -> Optional[str]:
    """Google custom-date-range tbs that caps results at the cutoff (mechanical search guard)."""
    try:
        d = date.fromisoformat(cutoff)
    except ValueError:
        return None
    return f"cdr:1,cd_min:01/01/2000,cd_max:{d.month}/{d.day}/{d.year}"


# --------------------------------------------------------------------------------------
# content reduction (Claude-Code-style: never blind-truncate a fetched page)
# --------------------------------------------------------------------------------------
_NUMERIC_LINE = re.compile(r"\d")
_DATEY = re.compile(r"\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{4}|\d{4}年|\d{1,2}月")


def _relevance_window(text: str, instruction: str, budget: int) -> str:
    """Deterministic fallback reducer: keep the lines most relevant to `instruction`.

    Scores each line by (instruction-keyword overlap) + (has a number) + (has a date); keeps the
    highest-scoring lines in original order up to `budget` chars. This preserves the numeric anchor
    (recent value + date) that a forecast needs, instead of cutting the first N chars blindly.
    """
    kws = {w.lower() for w in re.findall(r"[\w一-鿿]{2,}", instruction or "")}
    lines = text.splitlines()
    scored = []
    for i, ln in enumerate(lines):
        low = ln.lower()
        score = sum(1 for k in kws if k in low)
        if _NUMERIC_LINE.search(ln):
            score += 1
        if _DATEY.search(ln):
            score += 1
        scored.append((score, i, ln))
    # greedily take highest-score lines until budget, then restore document order
    chosen: set = set()
    total = 0
    for score, i, ln in sorted(scored, key=lambda t: (-t[0], t[1])):
        if score <= 0:
            break
        if total + len(ln) + 1 > budget:
            continue
        chosen.add(i)
        total += len(ln) + 1
    if not chosen:
        return text[:budget]
    return "\n".join(lines[i] for i in sorted(chosen))


_EXTRACTOR = {"client": None, "tried": False}

_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
_TAG = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S | re.I)
_TAGS = re.compile(r"<[^>]+>")


def _html_to_text(html: str) -> str:
    """Crude HTML->text (no bs4 in env): drop script/style, strip tags, unescape, collapse blanks."""
    import html as _h
    txt = _TAG.sub(" ", html)
    txt = _TAGS.sub("\n", txt)
    txt = _h.unescape(txt)
    return re.sub(r"\n[ \t]*\n[ \t\n]*", "\n\n", txt).strip()


async def _fetch_clean(url: str) -> tuple[str, str]:
    """Fetch a URL as text. Primary: Jina reader (clean markdown). Fallback: direct GET + strip.

    Returns (text, source). Raises RuntimeError with a concise message if both fail, so the model
    gets a clear signal to move on rather than retrying the same dead URL.
    """
    jina_headers = {"X-Return-Format": "markdown"}
    jkey = os.environ.get("JINA_API_KEY")
    if jkey:
        jina_headers["Authorization"] = f"Bearer {jkey}"
    jina_err = None
    try:
        async with httpx.AsyncClient(timeout=30, trust_env=False, follow_redirects=True) as c:
            r = await c.get(f"{JINA_READER}/{url}", headers=jina_headers)
            r.raise_for_status()
            if r.text.strip():
                return r.text, "jina"
            jina_err = "empty"
    except Exception as exc:
        jina_err = f"{type(exc).__name__}"
    # Fallback: fetch the page directly (works where Jina is blocked + the site allows bots).
    try:
        async with httpx.AsyncClient(timeout=20, trust_env=False, follow_redirects=True,
                                     headers={"User-Agent": _UA}) as c:
            r = await c.get(url)
            r.raise_for_status()
            text = _html_to_text(r.text)
            if text:
                return text, "direct"
    except Exception as exc:
        raise RuntimeError(f"jina={jina_err}; direct={type(exc).__name__}") from exc
    raise RuntimeError(f"jina={jina_err}; direct=empty")


def _get_extractor():
    """Lazily build a cheap apihy client used only to extract relevant content from big pages."""
    if _EXTRACTOR["tried"]:
        return _EXTRACTOR["client"]
    _EXTRACTOR["tried"] = True
    if not os.environ.get("apihy_API_KEY_deepseek") and not os.environ.get("apihy_API_KEY_qwen"):
        return None
    try:
        from futurecast.llm import OpenRouterNewAPIClient  # lazy: avoid MCP-startup cost
        if os.environ.get("apihy_API_KEY_deepseek"):
            c = OpenRouterNewAPIClient(model="deepseek-v4-flash", api_key_env="apihy_API_KEY_deepseek",
                                       base_url_env="apihy_BASE_URL", async_mode=True, max_tokens=2000)
        else:
            c = OpenRouterNewAPIClient(model="qwen3-235b-a22b-instruct-2507",
                                       api_key_env="apihy_API_KEY_qwen", base_url_env="apihy_BASE_URL",
                                       async_mode=True, max_tokens=2000)
        _EXTRACTOR["client"] = c
    except Exception:
        _EXTRACTOR["client"] = None
    return _EXTRACTOR["client"]


async def _extract_relevant(content: str, instruction: str, cutoff: Optional[str]) -> Optional[str]:
    """Claude-Code-style extraction: a cheap model pulls the instruction-relevant facts from a big
    page (recent values, dates, units, figures), preserving numbers verbatim. None on failure."""
    client = _get_extractor()
    if client is None:
        return None
    windowed = content if len(content) <= EXTRACT_INPUT_CAP else _relevance_window(
        content, instruction, EXTRACT_INPUT_CAP)
    asof_note = (f" Only use values dated on or before {cutoff}; ignore anything later." if cutoff else "")
    prompt = (
        f"From the web page below, extract ONLY what is relevant to: {instruction}.{asof_note}\n"
        "Report the most recent value(s) of the series with their exact date(s), the unit, and any "
        "directly relevant figures. Preserve all numbers and dates verbatim. Be concise (<300 words). "
        "If the page has none of this, say 'no relevant data'.\n\n=== PAGE ===\n" + windowed)
    try:
        resp = await client.chat([{"role": "user", "content": prompt}])
        out = (getattr(resp, "content", "") or "").strip()
        return out or None
    except Exception:
        return None



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
    target = _target()
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
        # snippet (dynamic price pages), and the realized value is usually shown next to the
        # TARGET date — often yearless ("At close: June 26"). Redact such snippets; keep
        # title+link so the model knows the source exists and can fetch the *historical* value.
        leaks = (cutoff and _has_post_cutoff_date(snippet, cutoff)) or \
                (target and _mentions_target(snippet, target)) or \
                (target and _mentions_target(it.get('title', '') or '', target))
        if leaks:
            snippet = "[snippet redacted: references the target date or post-cutoff data]"
            redacted += 1
        tag = f" [{when}]" if when else ""
        lines.append(f"- {it.get('title','')}{tag}\n  {link}\n  {snippet}")
    head = (f"[as-of {cutoff} | target {target} blocked: {dropped} post-cutoff result(s) dropped, "
            f"{redacted} snippet(s) redacted]\n") if (cutoff or target) else ""
    body = "\n".join(lines) or "[no results]"
    return {"content": [{"type": "text", "text": head + body}]}


@tool("read_webpage",
      "Fetch a URL as clean reader text (Jina). Args: url (str), instruction (str, optional: what "
      "to extract, e.g. 'the most recent value and date of the series'). Small pages return whole; "
      "large pages are reduced to the instruction-relevant facts (numbers/dates preserved) rather "
      "than blindly truncated. Honors the as-of cutoff: post-cutoff/target-date lines are removed.",
      {"url": str, "instruction": str})
async def read_webpage(args: dict) -> dict:
    cutoff = _cutoff()
    instruction = (args.get("instruction") or
                   "the most recent value(s), date(s), unit, and figures of the series in question")
    try:
        text, src = await _fetch_clean(args["url"])
    except Exception as exc:
        return {"content": [{"type": "text", "text":
                f"[fetch failed for {args['url']}: {exc}. Do NOT retry this URL — use the search "
                f"snippets or try a different source.]"}]}

    banner = ""
    if cutoff:
        pub = None
        m = re.search(r"Published Time:\s*(.+)", text)
        if m:
            pub = parse_loose_date(m.group(1))
        verdict = check_as_of(text if pub is None else f"Published Time: {pub}", cutoff,
                              lambda _t: pub)
        if pub is not None and not verdict.allowed:
            return {"content": [{"type": "text", "text":
                    f"[BLOCKED: page published {pub} is after as-of cutoff {cutoff}; cannot be used]"}]}
        target = _target()
        stripped = 0
        kept = []
        for ln in text.splitlines():
            if (target and _mentions_target(ln, target)) or _has_post_cutoff_date(ln, cutoff):
                stripped += 1
                continue
            kept.append(ln)
        text = "\n".join(kept)
        banner = (f"[AS-OF {cutoff}] Ignore anything dated after {cutoff}; detected pub date "
                  f"{pub or 'unknown'}; {stripped} target/post-cutoff line(s) removed.\n\n")

    # No blind truncation. Small page -> return whole; large page -> extract relevant facts.
    if len(text) <= RETURN_BUDGET:
        return {"content": [{"type": "text", "text": banner + text}]}
    extracted = await _extract_relevant(text, instruction, cutoff)
    if extracted:
        body = (f"[large page reduced to instruction-relevant facts via extractor; "
                f"original {len(text)} chars]\nInstruction: {instruction}\n\n{extracted}")
    else:
        body = (f"[large page ({len(text)} chars) reduced by relevance windowing]\n\n"
                + _relevance_window(text, instruction, RETURN_BUDGET))
    return {"content": [{"type": "text", "text": banner + body}]}


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
