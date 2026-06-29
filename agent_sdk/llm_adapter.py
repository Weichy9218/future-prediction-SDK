"""Owned LLM adapter — a minimal Anthropic /v1/messages endpoint backed by futurecast/llm.

WHY this exists (replaces claude-code-router): we keep the Agent SDK harness (context mgmt,
plan, memory, the agent loop) EXACTLY as-is — the claude CLI still speaks the Anthropic API —
but we OWN the model-routing layer so that (1) LLM-client usage is explicit and controllable and
(2) reasoning is captured cleanly for BOTH models. ccr 2.0.0 dropped/duplicated this: it mangled
glm tool-call args under thinking and never surfaced gpt's reasoning. Here we route through our
own OpenAI-compatible clients:

  gpt-5.5  -> GPTSub2APIClient   (haoxiang Responses API, reasoning summary + tools)
  glm-5    -> OpenRouterNewAPIClient (apihy chat/completions, reasoning_content + tools)

The claude CLI points ANTHROPIC_BASE_URL at this server. We translate Anthropic<->OpenAI, call
the client once per turn, and emit a *buffered* Anthropic SSE stream (we don't need token-level
streaming — we build the full turn, then replay it as well-formed SSE events the CLI accepts:
thinking -> text -> tool_use). Model is chosen by env FUTURECAST_MODEL (set by the runner), not by
the Anthropic `model` field (which is always a dummy claude-* name).
"""
from __future__ import annotations

import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Optional

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, StreamingResponse
from starlette.routing import Route

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))  # for sibling `config`
from futurecast.llm import GPTSub2APIClient, OpenRouterNewAPIClient  # noqa: E402
from config import from_env  # noqa: E402  sibling module: typed run parameters

_LOG = _REPO_ROOT / "log" / "adapter.log"


def _log(msg: str) -> None:
    try:
        _LOG.parent.mkdir(parents=True, exist_ok=True)
        with _LOG.open("a", encoding="utf-8") as fh:
            fh.write(msg.rstrip() + "\n")
    except Exception:
        pass


# --------------------------------------------------------------------------------------
# client factory (one per process; model fixed by env for the run)
# --------------------------------------------------------------------------------------
def _build_client():
    cfg = from_env()
    model, effort, max_tokens = cfg.model.strip(), cfg.reasoning_effort, cfg.max_tokens
    if model.startswith("gpt"):
        return model, GPTSub2APIClient(
            model=model, api_key_env="GPT_sub2api_apikey", base_url_env="GPT_sub2api_URL",
            reasoning_effort=effort, async_mode=True, max_tokens=max_tokens)
    # glm / qwen / deepseek via apihy chat-completions
    key_env = {"glm": "apihy_API_KEY_glm", "qwen": "apihy_API_KEY_qwen",
               "kimi": "apihy_API_KEY_kimi", "deepseek": "apihy_API_KEY_deepseek"}
    api_key_env = next((v for k, v in key_env.items() if model.startswith(k)), "apihy_API_KEY_glm")
    return model, OpenRouterNewAPIClient(
        model=model, api_key_env=api_key_env, base_url_env="apihy_BASE_URL",
        reasoning_effort=effort, async_mode=True, max_tokens=max_tokens)


_MODEL_NAME, _CLIENT = _build_client()
_log(f"=== adapter up: model={_MODEL_NAME} client={_CLIENT.__class__.__name__} ===")


# --------------------------------------------------------------------------------------
# Anthropic -> OpenAI request translation
# --------------------------------------------------------------------------------------
def _content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        out = []
        for b in content:
            if isinstance(b, dict) and b.get("type") == "text":
                out.append(b.get("text", ""))
        return "\n".join(out)
    return ""


def _anthropic_messages_to_openai(system: Any, messages: list) -> list:
    """Flatten Anthropic messages (with tool_use/tool_result/thinking blocks) to OpenAI roles."""
    out: list = []
    sys_text = _content_to_text(system) if system else ""
    if sys_text:
        out.append({"role": "system", "content": sys_text})
    for m in messages:
        role = m.get("role")
        content = m.get("content")
        if isinstance(content, str):
            out.append({"role": role, "content": content})
            continue
        if not isinstance(content, list):
            continue
        if role == "assistant":
            text_parts, tool_calls = [], []
            for b in content:
                t = b.get("type")
                if t == "text":
                    text_parts.append(b.get("text", ""))
                elif t == "tool_use":
                    tool_calls.append({
                        "id": b.get("id"), "type": "function",
                        "function": {"name": b.get("name"),
                                     "arguments": json.dumps(b.get("input") or {}, ensure_ascii=False)},
                    })
                # thinking blocks are dropped on the way upstream (the client re-derives reasoning)
            msg: dict = {"role": "assistant", "content": "\n".join(text_parts)}
            if tool_calls:
                msg["tool_calls"] = tool_calls
            out.append(msg)
        else:  # user
            tool_results, text_parts = [], []
            for b in content:
                t = b.get("type")
                if t == "tool_result":
                    tool_results.append(b)
                elif t == "text":
                    text_parts.append(b.get("text", ""))
            for tr in tool_results:
                out.append({"role": "tool", "tool_call_id": tr.get("tool_use_id"),
                            "content": _content_to_text(tr.get("content"))})
            if text_parts:
                out.append({"role": "user", "content": "\n".join(text_parts)})
    return out


def _anthropic_tools_to_openai(tools: Optional[list]) -> Optional[list]:
    if not tools:
        return None
    out = []
    for t in tools:
        if not isinstance(t, dict) or "name" not in t:
            continue
        out.append({"type": "function", "function": {
            "name": t["name"], "description": t.get("description", ""),
            "parameters": t.get("input_schema") or {"type": "object", "properties": {}},
        }})
    return out or None


def _normalize_tool_calls(raw: list) -> list:
    """Map our clients' tool_calls (OpenAI-ish) to Anthropic tool_use {id,name,input}."""
    out = []
    for tc in raw or []:
        fn = tc.get("function") or {}
        name = fn.get("name") or tc.get("name")
        args = fn.get("arguments")
        if args is None:
            args = tc.get("arguments")
        if isinstance(args, str):
            try:
                args = json.loads(args or "{}")
            except json.JSONDecodeError:
                args = {"_raw": args}
        out.append({"id": tc.get("id") or f"toolu_{uuid.uuid4().hex[:24]}",
                    "name": name, "input": args or {}})
    return out


# --------------------------------------------------------------------------------------
# OpenAI result -> Anthropic content blocks + SSE
# --------------------------------------------------------------------------------------
def _build_anthropic_blocks(resp) -> tuple[list, str]:
    blocks: list = []
    reasoning = getattr(resp, "reasoning_summary", None) or []
    thinking_text = "\n".join(reasoning) if isinstance(reasoning, list) else str(reasoning)
    if thinking_text.strip():
        blocks.append({"type": "thinking", "thinking": thinking_text,
                       "signature": "futurecast-adapter"})
    content = getattr(resp, "content", "") or ""
    if content.strip():
        blocks.append({"type": "text", "text": content})
    tool_uses = _normalize_tool_calls(getattr(resp, "tool_calls", None) or [])
    blocks.extend({"type": "tool_use", **tu} for tu in tool_uses)
    stop_reason = "tool_use" if tool_uses else "end_turn"
    if not blocks:  # never emit an empty assistant turn
        blocks.append({"type": "text", "text": ""})
    return blocks, stop_reason


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _stream_response(blocks: list, stop_reason: str, usage: dict):
    msg_id = f"msg_{uuid.uuid4().hex[:24]}"
    in_tok = int(usage.get("prompt_tokens", 0) or 0)
    out_tok = int(usage.get("completion_tokens", 0) or 0)
    yield _sse("message_start", {"type": "message_start", "message": {
        "id": msg_id, "type": "message", "role": "assistant", "model": _MODEL_NAME,
        "content": [], "stop_reason": None, "stop_sequence": None,
        "usage": {"input_tokens": in_tok, "output_tokens": 0}}})
    for i, blk in enumerate(blocks):
        t = blk["type"]
        if t == "thinking":
            yield _sse("content_block_start", {"type": "content_block_start", "index": i,
                       "content_block": {"type": "thinking", "thinking": "", "signature": ""}})
            yield _sse("content_block_delta", {"type": "content_block_delta", "index": i,
                       "delta": {"type": "thinking_delta", "thinking": blk["thinking"]}})
            yield _sse("content_block_delta", {"type": "content_block_delta", "index": i,
                       "delta": {"type": "signature_delta", "signature": blk.get("signature", "")}})
        elif t == "text":
            yield _sse("content_block_start", {"type": "content_block_start", "index": i,
                       "content_block": {"type": "text", "text": ""}})
            yield _sse("content_block_delta", {"type": "content_block_delta", "index": i,
                       "delta": {"type": "text_delta", "text": blk["text"]}})
        elif t == "tool_use":
            yield _sse("content_block_start", {"type": "content_block_start", "index": i,
                       "content_block": {"type": "tool_use", "id": blk["id"], "name": blk["name"], "input": {}}})
            yield _sse("content_block_delta", {"type": "content_block_delta", "index": i,
                       "delta": {"type": "input_json_delta",
                                 "partial_json": json.dumps(blk["input"], ensure_ascii=False)}})
        yield _sse("content_block_stop", {"type": "content_block_stop", "index": i})
    yield _sse("message_delta", {"type": "message_delta",
               "delta": {"stop_reason": stop_reason, "stop_sequence": None},
               "usage": {"output_tokens": out_tok}})
    yield _sse("message_stop", {"type": "message_stop"})


async def messages(request: Request):
    body = await request.json()
    system = body.get("system")
    msgs = body.get("messages", [])
    tools = _anthropic_tools_to_openai(body.get("tools"))
    want_stream = bool(body.get("stream"))
    oai_messages = _anthropic_messages_to_openai(system, msgs)
    raw_tools = body.get("tools") or []
    tool_names = [t.get("name") for t in raw_tools if isinstance(t, dict) and t.get("name")]
    _log(f"[req] msgs={len(msgs)} tools={len(tools) if tools else 0} stream={want_stream}")
    # Log the exact tool surface once per run (first turn) so we can audit that only the
    # representative official-loop tools + our MCP equivalents are exposed (no stray skills).
    if len(msgs) <= 1:
        _log(f"[tool-surface] {sorted(tool_names)}")

    try:
        resp = await _CLIENT.chat(oai_messages, tools=tools)
    except Exception as exc:  # surface upstream errors as a valid Anthropic error
        _log(f"[error] {type(exc).__name__}: {exc}")
        return JSONResponse(status_code=500, content={
            "type": "error", "error": {"type": "api_error", "message": f"{type(exc).__name__}: {exc}"}})

    blocks, stop_reason = _build_anthropic_blocks(resp)
    usage = getattr(resp, "usage", {}) or {}
    _log(f"[resp] blocks={[b['type'] for b in blocks]} stop={stop_reason}")

    if want_stream:
        return StreamingResponse(_stream_response(blocks, stop_reason, usage),
                                 media_type="text/event-stream")
    return JSONResponse({
        "id": f"msg_{uuid.uuid4().hex[:24]}", "type": "message", "role": "assistant",
        "model": _MODEL_NAME, "content": blocks, "stop_reason": stop_reason, "stop_sequence": None,
        "usage": {"input_tokens": int(usage.get("prompt_tokens", 0) or 0),
                  "output_tokens": int(usage.get("completion_tokens", 0) or 0)}})


async def count_tokens(request: Request):
    body = await request.json()
    text = json.dumps(body.get("messages", []), ensure_ascii=False) + _content_to_text(body.get("system"))
    return JSONResponse({"input_tokens": max(1, len(text) // 4)})


async def health(_request: Request):
    return JSONResponse({"status": "ok", "model": _MODEL_NAME})


app = Starlette(routes=[
    Route("/", health, methods=["GET"]),
    Route("/v1/messages", messages, methods=["POST"]),
    Route("/v1/messages/count_tokens", count_tokens, methods=["POST"]),
])


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("FUTURECAST_ADAPTER_PORT", "3456"))
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
