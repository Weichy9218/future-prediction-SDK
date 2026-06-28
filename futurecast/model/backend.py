"""ModelBackend — the seam that decouples the agent loop from any specific provider.

This is how the repo satisfies two constraints at once:
  - run the loop on CHEAP models (no Claude tokens needed)  -> CoreLLMBackend (default)
  - keep Claude available + fully controllable                -> ClaudeBackend (optional)

The loop (../loop/agent.py) only ever sees this protocol, never a vendor SDK.
"""
from __future__ import annotations

from typing import Any, Optional, Protocol, runtime_checkable


@runtime_checkable
class ModelBackend(Protocol):
    """Minimal contract: take a message list (+ optional tool schemas), return one turn.

    Return shape (a plain dict, vendor-neutral):
      {
        "content": str,                       # assistant text
        "tool_calls": [                       # empty if the model answered directly
            {"id": str, "name": str, "arguments": dict}, ...
        ],
        "raw": Any,                           # backend-native response, for debugging
      }
    """

    name: str

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: Optional[list[dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        ...
