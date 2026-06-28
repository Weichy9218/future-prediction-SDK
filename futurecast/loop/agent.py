"""The thin forecasting loop — the ONLY orchestration code in this repo.

observe -> act -> (tool) -> observe ... until the model emits a final answer or we hit the
step cap. This is intentionally small (~one screen): we are NOT rebuilding a general agent
harness (that is solved work). Everything provider-specific lives behind ModelBackend, and
every forecasting-specific behaviour lives in the prompt (playbook), the as-of guard, the
scorable output, and the experience library — never here.

If you'd rather rent a mature loop (subagents, context mgmt), swap this for the Claude Agent
SDK via ClaudeBackend; this loop stays as the cheap, fully-owned default.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional

from ..model.backend import ModelBackend

# A tool is just an async callable taking parsed args -> string result. The registry
# (../tools/registry.py) supplies both the JSON schema (for the model) and this executor.
ToolExecutor = Callable[[dict[str, Any]], Awaitable[str]]


@dataclass
class LoopResult:
    final_text: str
    steps: int
    transcript: list[dict[str, Any]] = field(default_factory=list)


async def run_loop(
    backend: ModelBackend,
    system_prompt: str,
    user_prompt: str,
    tool_schemas: Optional[list[dict[str, Any]]] = None,
    executors: Optional[dict[str, ToolExecutor]] = None,
    max_steps: int = 8,
) -> LoopResult:
    """Drive `backend` with tools until it answers. Returns the final assistant text."""
    tool_schemas = tool_schemas or []
    executors = executors or {}
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    for step in range(1, max_steps + 1):
        turn = await backend.chat(messages, tools=tool_schemas or None)
        calls = turn.get("tool_calls") or []
        if not calls:
            return LoopResult(final_text=turn.get("content", ""), steps=step, transcript=messages)

        # record the assistant's tool-call turn, then execute each tool and feed results back
        messages.append({"role": "assistant", "content": turn.get("content", ""), "tool_calls": calls})
        for call in calls:
            name = call.get("name")
            args = call.get("arguments") or {}
            executor = executors.get(name)
            result = await executor(args) if executor else f"[no executor for tool {name!r}]"
            messages.append({"role": "tool", "tool_call_id": call.get("id"), "name": name, "content": result})

    # step cap hit — return whatever the last assistant text was
    last = next((m["content"] for m in reversed(messages) if m.get("role") == "assistant"), "")
    return LoopResult(final_text=last, steps=max_steps, transcript=messages)
