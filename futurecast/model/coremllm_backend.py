"""CoreLLMBackend — drive the loop with the harvested core/llm clients (kit answer to Q2).

These clients (gpt_sub2api -> haoxiang.ai Responses API; openrouter_newapi -> Chat
Completions for OpenRouter / apihy.com qwen/glm/kimi/deepseek) already implement
OpenAI-compatible tool-calling. So the forecasting loop runs on CHEAP models and needs
NO Claude tokens. Keys come from the same .env conventions as galaxy-selfevolve
(GPT_sub2api_*, OPENROUTER_*, apihy_*).

The clients' public method is `async chat(messages, tools=None, **kwargs) -> LLMResponse`,
where LLMResponse has `.content` and `.tool_calls`. We adapt that to the vendor-neutral
dict the loop expects.
"""
from __future__ import annotations

from typing import Any, Optional

from ..llm import instantiate_llm_client  # harvested package


# Cheap, tool-calling-capable presets. Tune freely; these are sensible defaults.
PRESETS: dict[str, dict[str, Any]] = {
    # haoxiang.ai gateway, Responses API, reasoning summaries available
    "gpt_sub2api": {
        "client": "gpt_sub2api",
        "args": {"model": "gpt-5.5", "temperature": 0.2, "max_tokens": 8192,
                 "api_key_env": "GPT_sub2api_apikey", "base_url_env": "GPT_sub2api_URL"},
    },
    # OpenRouter / apihy Chat Completions — point base_url_env/api_key_env at a cheap model
    "qwen": {
        "client": "openrouter_newapi",
        "args": {"model": "qwen/qwen-2.5-72b-instruct", "temperature": 0.2,
                 "api_key_env": "OPENROUTER_API_KEY", "base_url_env": "OPENROUTER_BASE_URL"},
    },
}


class CoreLLMBackend:
    """Wrap a registered core/llm client as a vendor-neutral ModelBackend."""

    def __init__(self, preset: str = "gpt_sub2api", **overrides: Any) -> None:
        if preset not in PRESETS:
            raise KeyError(f"unknown preset {preset!r}; have {list(PRESETS)}")
        spec = PRESETS[preset]
        args = {**spec["args"], **overrides, "async_mode": True}
        self.name = f"corellm:{preset}:{args.get('model')}"
        self._client = instantiate_llm_client(spec["client"], args)

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: Optional[list[dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        resp = await self._client.chat(messages, tools=tools, **kwargs)
        return {
            "content": getattr(resp, "content", "") or "",
            "tool_calls": [
                {"id": tc.get("id"), "name": (tc.get("function") or {}).get("name") or tc.get("name"),
                 "arguments": (tc.get("function") or {}).get("arguments") or tc.get("arguments") or {}}
                for tc in (getattr(resp, "tool_calls", None) or [])
            ],
            "raw": resp,
        }

    async def aclose(self) -> None:
        close = getattr(self._client, "aclose", None)
        if close:
            await close()
