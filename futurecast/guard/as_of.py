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

from dataclasses import dataclass
from datetime import date
from typing import Awaitable, Callable, Optional

# Returns the ISO date the fetched content pertains to, or None if it can't be determined.
TimestampExtractor = Callable[[str], Optional[str]]


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
