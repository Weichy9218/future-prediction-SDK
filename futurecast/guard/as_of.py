"""as-of fetch guard (kit #2) — the ONE mechanism-level hook that must stay.

A general agent fundamentally lacks this, and prompt-only enforcement can't be trusted:
any fetched datum whose own timestamp is AFTER the question cutoff must be kept OUT of the
reasoning context, or the forecast is leaked (and the benchmark's "answers don't leak"
property — the whole reason this task is hard to hack — is destroyed).

Design: wrap every fetch tool. The wrapper stamps each result with the cutoff and asks a
source-specific `extract_timestamp` to find the datum's time. Anything > cutoff is dropped
(or returned as an explicit "unavailable: post-cutoff" marker the model can cite but not use).
"""
from __future__ import annotations

import json as _json
import logging
import re
from dataclasses import dataclass
from datetime import date
from typing import Awaitable, Callable, List, Optional

_logger = logging.getLogger(__name__)

# Returns the ISO date the fetched content pertains to, or None if it can't be determined.
TimestampExtractor = Callable[[str], Optional[str]]

# An injected async chat callable: messages -> object with a `.content` str. Core stays
# client-agnostic; the run harness passes a small dedicated screening model (AGENTS.md #3/#5).
ScreenChat = Callable[[list], Awaitable[object]]


@dataclass
class GuardVerdict:
    allowed: bool
    reason: str
    extracted_as_of: Optional[str] = None


def check_as_of(content: str, cutoff: str, extract_timestamp: TimestampExtractor) -> GuardVerdict:
    """Decide whether `content` may enter the reasoning context under `cutoff` (ISO date)."""
    ts = extract_timestamp(content)
    if ts is None:
        # Unknown timestamp is treated as SUSPECT, not safe: a general fetch of "today's price"
        # has no embedded date but is post-cutoff by construction. Caller decides strictness.
        return GuardVerdict(allowed=False, reason="timestamp_unknown_treated_as_suspect")
    if date.fromisoformat(ts) > date.fromisoformat(cutoff):
        return GuardVerdict(allowed=False, reason="post_cutoff", extracted_as_of=ts)
    return GuardVerdict(allowed=True, reason="in_boundary", extracted_as_of=ts)


def guarded_fetch(
    fetch: Callable[..., Awaitable[str]],
    cutoff: str,
    extract_timestamp: TimestampExtractor,
    *,
    block_marker: str = "[BLOCKED: source is dated after the as-of cutoff and cannot be used]",
) -> Callable[..., Awaitable[str]]:
    """Wrap an async fetch tool so post-cutoff content never reaches the model."""
    async def _wrapped(*args, **kwargs) -> str:
        content = await fetch(*args, **kwargs)
        verdict = check_as_of(content, cutoff, extract_timestamp)
        return content if verdict.allowed else block_marker
    return _wrapped


# TODO: register per-source `extract_timestamp` implementations under experience/ skills,
# NOT here — core must not learn specific site formats (AGENTS.md guardrail #3).


# --------------------------------------------------------------------------------------
# model-based screening (the as-of trust we hand to a DEDICATED model, never the main agent)
# --------------------------------------------------------------------------------------
# Regex/date-field guards are mechanical but blind to phrasing ("the index closed yesterday at
# X", "the winner was announced as Y") and to yearless/relative leaks. So every tool output is
# additionally screened by a small dedicated model BEFORE it reaches the main agent. Crucially the
# model only *identifies* offending spans verbatim — the removal is applied deterministically by
# the caller — so a screening model can never summarize, truncate, or otherwise corrupt the
# in-boundary content it is supposed to protect.
#
# Two strictness regimes (the caller picks via `strict`):
#   - loose (default): we forecast FUTURE questions with no realized answer to leak, so only remove
#     CLEAR post-cutoff/target leaks and keep all <=cutoff / historical / undated data. This avoids
#     the false-positives that otherwise strip the very anchor the agent needs.
#   - strict: also flag anything ambiguous (for historical backtests, where one leak is fatal).
_SCREEN_PROMPT_HEAD = (
    "You are an as-of screening filter standing between a web tool and a forecasting agent. The "
    "agent may use ONLY information available on or before the cutoff date {cutoff}. The forecast "
    "target date is {target}; the realized value or outcome AT or AFTER the target date must never "
    "reach the agent (the benchmark answer would leak).\n\n"
    "From the web content below, find every span (one line or a short phrase, copied VERBATIM from "
    "the content) that:\n"
    "  - states a value, price, level, result, ranking, or outcome whose own date is strictly AFTER "
    "{cutoff} — including relative phrasing that clearly refers to after the cutoff ('today', 'as of "
    "<post-cutoff date>', 'at close <target date>'); OR\n"
    "  - reveals what happens / the realized value AT the target date {target}.\n"
)
_SCREEN_PROMPT_LOOSE = (
    "PRESERVE everything else — all values dated on/before {cutoff}, all historical series, and any "
    "undated figures (the agent needs these as its prior). Do NOT flag a span merely because it is "
    "recent, undated, or a forecast/projection. Only remove CLEAR post-cutoff or target-date leaks.\n"
)
_SCREEN_PROMPT_STRICT = (
    "Do NOT flag facts clearly dated on/before {cutoff}. When genuinely UNSURE whether a span is "
    "post-cutoff, flag it (for this run a leak is fatal, so false positives are acceptable).\n"
)
_SCREEN_PROMPT_TAIL = (
    "\nReturn STRICT JSON ONLY, no prose: {{\"leaks\": [\"<verbatim span>\", ...]}}. Use an empty "
    "list if nothing leaks. Each span MUST be copied exactly so it can be located and removed.\n\n"
    "=== CONTENT ===\n{content}"
)

REDACTION_MARKER = "[redacted: post-cutoff/target leak]"


def _parse_leak_spans(raw: str) -> List[str]:
    """Pull the `leaks` string list out of the model's (possibly fenced) JSON reply."""
    m = re.search(r"\{.*\}", raw or "", re.S)
    if not m:
        return []
    try:
        obj = _json.loads(m.group(0))
    except ValueError:
        return []
    leaks = obj.get("leaks") if isinstance(obj, dict) else None
    if not isinstance(leaks, list):
        return []
    return [s for s in leaks if isinstance(s, str) and s.strip()]


async def screen_leaks(content: str, cutoff: Optional[str], target: Optional[str],
                       chat: ScreenChat, strict: bool = False) -> List[str]:
    """Ask the injected screening model which verbatim spans of `content` leak post-cutoff info.

    `strict=False` (default) only removes clear post-cutoff/target leaks and preserves all
    <=cutoff/undated data; `strict=True` also flags ambiguous spans (historical-backtest safety).
    Returns only spans actually present in `content` (the model may paraphrase; we keep application
    deterministic). Fail-open to [] on any error — the regex guard is the floor, this is the extra
    semantic layer on top.
    """
    if not content or not content.strip() or not (cutoff or target):
        return []
    regime = _SCREEN_PROMPT_STRICT if strict else _SCREEN_PROMPT_LOOSE
    prompt = (_SCREEN_PROMPT_HEAD + regime + _SCREEN_PROMPT_TAIL).format(
        cutoff=cutoff or "(none)", target=target or "(none)", content=content)
    try:
        resp = await chat([{"role": "user", "content": prompt}])
        raw = (getattr(resp, "content", "") or "").strip()
    except Exception as exc:  # noqa: BLE001 — screener is best-effort over the regex floor
        _logger.debug("as-of screener failed; deterministic guard remains in force: %s", exc)
        return []
    return [s for s in _parse_leak_spans(raw) if s in content]


async def screen_and_redact(content: str, cutoff: Optional[str], target: Optional[str],
                            chat: ScreenChat, strict: bool = False) -> tuple[str, int]:
    """Run the screener and deterministically excise the spans it flags. Returns (text, n_redacted)."""
    spans = await screen_leaks(content, cutoff, target, chat, strict=strict)
    redacted = content
    for span in spans:
        redacted = redacted.replace(span, REDACTION_MARKER)
    return redacted, len(spans)
