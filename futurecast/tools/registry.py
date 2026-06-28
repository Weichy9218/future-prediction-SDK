"""Generic minimal tool set — NOT per-source tools (AGENTS.md guardrail #3).

Fetching is a generic capability; site specifics belong in experience/ skills, never in a
`wta_rankings` / `boc_fx` tool. Here we expose only: web_search, fetch_url, run_python,
write_note. Each entry = an OpenAI-style JSON schema (for the model) + an async executor
(for the loop). Executors here are SKELETONS — wire them to real providers (the harvested
core/tools, or SERPER/EXA from .env) in the next phase.

Fetch executors should be wrapped by guard.as_of.guarded_fetch before use, so post-cutoff
content never reaches the model.
"""
from __future__ import annotations

from typing import Any

# ---- schemas (what the model sees) ------------------------------------------------------
SCHEMAS: list[dict[str, Any]] = [
    {"type": "function", "function": {
        "name": "web_search", "description": "Search the web for sources. Returns titles + urls + snippets.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {
        "name": "fetch_url", "description": "Fetch a URL and return readable text (as-of guarded).",
        "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
    {"type": "function", "function": {
        "name": "run_python", "description": "Run short Python for extrapolation / calibration math.",
        "parameters": {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]}}},
]


# ---- executors (skeletons; raise so missing wiring is loud, not silent) ------------------
async def web_search(args: dict[str, Any]) -> str:
    raise NotImplementedError("wire web_search to SERPER/EXA (.env) or core/tools")


async def fetch_url(args: dict[str, Any]) -> str:
    raise NotImplementedError("wire fetch_url to a reader, then wrap with guard.as_of.guarded_fetch")


async def run_python(args: dict[str, Any]) -> str:
    raise NotImplementedError("wire run_python to E2B (.env E2B_API_KEY) or a local sandbox")


EXECUTORS = {"web_search": web_search, "fetch_url": fetch_url, "run_python": run_python}
