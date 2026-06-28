"""ClaudeBackend — optional Claude backend (answer to Q1: controllable, searchable, not required).

Use this only when you want Claude-grade reasoning and have tokens. Two ways to drive
Claude, both fully inspectable locally — you do NOT have to modify either:

  1. `anthropic` SDK (already installed, v0.60.0). Source is in your venv's site-packages,
     greppable line-by-line. This file uses it directly (Messages API).
  2. `claude-agent-sdk` (pip-installable; `pip install claude-agent-sdk`). Also open source;
     once installed its source sits in site-packages and is equally greppable. It gives the
     mature observe->act->subagent loop if you'd rather rent that than use our thin loop.

Routing/cost control is external and already wired on this machine: ANTHROPIC_BASE_URL can
point at the apihy gateway / claude-code-router, so even "Claude" calls can be cost-managed.

Kept off the default path on purpose — the default is CoreLLMBackend (cheap, no Claude tokens).
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional


class ClaudeBackend:
    """Vendor-neutral ModelBackend backed by the local `anthropic` SDK."""

    def __init__(self, model: str = "claude-opus-4-8", max_tokens: int = 4096) -> None:
        try:
            from anthropic import AsyncAnthropic  # local, inspectable
        except ImportError as e:  # pragma: no cover
            raise ImportError("pip install anthropic (or claude-agent-sdk) to use ClaudeBackend") from e
        self.name = f"claude:{model}"
        self._model = model
        self._max_tokens = max_tokens
        self._client = AsyncAnthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"),
            base_url=os.environ.get("ANTHROPIC_BASE_URL") or None,
        )

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: Optional[list[dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        system = "\n\n".join(m["content"] for m in messages if m.get("role") == "system")
        convo = [m for m in messages if m.get("role") != "system"]
        resp = await self._client.messages.create(
            model=self._model, max_tokens=self._max_tokens,
            system=system or None, messages=convo,
            tools=_to_anthropic_tools(tools) if tools else [],
        )
        text, calls = "", []
        for block in resp.content:
            if block.type == "text":
                text += block.text
            elif block.type == "tool_use":
                calls.append({"id": block.id, "name": block.name, "arguments": block.input})
        return {"content": text, "tool_calls": calls, "raw": resp}


def _to_anthropic_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Map OpenAI-style tool schemas to Anthropic's, so the same registry serves both backends."""
    out = []
    for t in tools:
        fn = t.get("function", t)
        out.append({"name": fn["name"], "description": fn.get("description", ""),
                    "input_schema": fn.get("parameters", {"type": "object", "properties": {}})})
    return out
