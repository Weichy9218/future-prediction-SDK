"""Run one forecast question through the Claude Agent SDK, driven by a CHEAP non-Claude model.

Routing (no Claude tokens spent):
  Claude Agent SDK -> spawns the `claude` CLI -> ANTHROPIC_BASE_URL=127.0.0.1:3456
  -> vendored claude-code-router (local config) -> a gateway model. The model is chosen by
  ccr's Router (regenerated per run by gen_ccr_config.py): `glm-5` (apihy) or `gpt-5.5`
  (haoxiang). Same agent loop, same tool surface for both — this is what makes a gpt-vs-glm
  comparison fair and what fixes "gpt doesn't call tools" without a second hand-written loop.

Tools (`--tools`): our in-process Serper/Jina/Exa MCP tools (real keys, as-of guarded) PLUS the
local Bash/Read/Edit/Write CLI tools. Anthropic's built-in WebSearch/WebFetch are disallowed
(they don't execute off-Claude). as-of is enforced at the tool boundary via FUTURECAST_AS_OF.

Output: a standardized rollout + parsed result under
  log/<run_group>/<task_id>-<model_short>/{rollout.jsonl, result.json}

Usage:
  .venv/bin/python agent_sdk/run_forecast.py [--model glm-5|gpt-5.5] [--tools]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

import anyio
from claude_agent_sdk import (
    query, ClaudeAgentOptions, AssistantMessage, ResultMessage,
    TextBlock, ToolUseBlock, project_key_for_directory,
)

ROUTER = "http://127.0.0.1:3456"
HERE = Path(__file__).resolve().parent
CWD = HERE.parent  # the futurecast repo root
sys.path.insert(0, str(HERE))  # make tools_mcp importable

PLAYBOOK = (CWD / "futurecast/playbook/playbook_A_numeric.md").read_text(encoding="utf-8")

# The forecast task. as-of is enforced mechanically at the tool boundary (FUTURECAST_AS_OF),
# not merely stated in the prompt.
TASK_ID = "futureworld_hog"
RUN_GROUP = os.environ.get("FUTURECAST_RUN_GROUP", "futureworld_hog_0615")
AS_OF = "2026-06-14"
QUESTION = (
    "You are forecasting a recurring numeric series.\n"
    f"AS-OF CUTOFF: {AS_OF}. Use only information available up to this date; do not use any "
    "knowledge of the realized value.\n\n"
    "On 2026-06-15 (UTC+8), what will Local Hybrid Hog (土杂猪) hog price (生猪价格) be, in CNY "
    "per kilogram (元/公斤)?\n\n"
    "End with: \\boxed{<plain number>} then a one-line JSON "
    '{"point":n,"low":n,"high":n,"anchor":"...","uncertainty":"...","confidence":"low|med|high","sources":["..."]}.'
)

_MODEL_SHORT = {"glm-5": "glm5", "glm-5.1": "glm51", "gpt-5.5": "gpt55", "gpt-5.4": "gpt54"}


def _parse_result(text: str) -> dict:
    """Pull the boxed answer + trailing JSON object out of the model's final text."""
    out: dict = {}
    m = re.search(r"\\boxed\{([^}]*)\}", text)
    if m:
        out["answer"] = m.group(1).strip()
    # last {...} JSON object in the text
    for m in reversed(list(re.finditer(r"\{[^{}]*\}", text))):
        try:
            obj = json.loads(m.group(0))
            if isinstance(obj, dict) and ("point" in obj or "anchor" in obj):
                out.update(obj)
                break
        except json.JSONDecodeError:
            continue
    return out


async def main(model: str, use_tools: bool) -> None:
    os.environ["FUTURECAST_AS_OF"] = AS_OF  # the as-of guard (tools_mcp) reads this
    env = dict(os.environ)
    env.update(
        ANTHROPIC_BASE_URL=ROUTER,
        ANTHROPIC_API_KEY="dummy-router-key",
        ANTHROPIC_AUTH_TOKEN="dummy-router-key",
    )
    mcp_servers: dict = {}
    allowed: list[str] = []
    disallowed = ["WebSearch", "WebFetch", "Bash", "Read", "Edit", "Write"]
    if use_tools:
        from tools_mcp import create_server, ALLOWED, DISALLOWED_BUILTINS
        mcp_servers = {"futurecast": create_server()}
        allowed, disallowed = ALLOWED, DISALLOWED_BUILTINS
    options = ClaudeAgentOptions(
        system_prompt=PLAYBOOK,
        model="claude-sonnet-4-5",          # ccr Router overrides -> chosen gateway model
        permission_mode="bypassPermissions",
        mcp_servers=mcp_servers,
        allowed_tools=allowed,
        disallowed_tools=disallowed,
        max_turns=8 if use_tools else 3,
        cwd=str(CWD),
        env=env,
        setting_sources=[],
    )
    prompt = QUESTION if use_tools else QUESTION + "\n\nDo not use any tools; answer from your own reasoning."

    print(f"# routing: Agent SDK -> {ROUTER} -> {model} | tools={use_tools} | as_of={AS_OF}\n", flush=True)
    final_text, session_id, result, n_tool = "", None, None, 0
    async for msg in query(prompt=prompt, options=options):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    final_text += block.text
                    print(block.text, end="", flush=True)
                elif isinstance(block, ToolUseBlock):
                    n_tool += 1
                    print(f"\n[tool_use {block.name} {block.input}]", flush=True)
        elif isinstance(msg, ResultMessage):
            result = msg
            session_id = getattr(msg, "session_id", None)

    print("\n\n=== RESULT ===", flush=True)
    print("session_id:", session_id, "| tool_use count:", n_tool)
    usage = getattr(result, "usage", None) if result else None
    if result is not None:
        print("usage:", usage)
        print("total_cost_usd:", getattr(result, "total_cost_usd", None))

    # --- standardized log output -------------------------------------------------------
    short = _MODEL_SHORT.get(model, model.replace(".", "").replace("-", ""))
    out_dir = CWD / "log" / RUN_GROUP / f"{TASK_ID}-{short}{'-tools' if use_tools else ''}"
    out_dir.mkdir(parents=True, exist_ok=True)

    proj = Path.home() / ".claude/projects" / project_key_for_directory(str(CWD))
    transcript = (proj / f"{session_id}.jsonl") if session_id else None
    if transcript is None or not transcript.exists():
        cands = sorted(proj.glob("*.jsonl"), key=lambda p: p.stat().st_mtime) if proj.exists() else []
        transcript = cands[-1] if cands else None
    if transcript and transcript.exists():
        shutil.copy(transcript, out_dir / "rollout.jsonl")

    parsed = _parse_result(final_text)
    result_json = {
        "task_id": TASK_ID, "model": model, "as_of": AS_OF, "tools": use_tools,
        "tool_use_count": n_tool, "session_id": session_id,
        "answer": parsed.get("answer"), "point": parsed.get("point"),
        "low": parsed.get("low"), "high": parsed.get("high"),
        "anchor": parsed.get("anchor", ""), "uncertainty": parsed.get("uncertainty", ""),
        "confidence": parsed.get("confidence", ""), "sources": parsed.get("sources", []),
        "usage": usage if isinstance(usage, dict) else (dict(usage) if usage else None),
    }
    (out_dir / "result.json").write_text(json.dumps(result_json, ensure_ascii=False, indent=2), encoding="utf-8")
    print("ROLLOUT:", out_dir / "rollout.jsonl", "(exists:", (out_dir / "rollout.jsonl").exists(), ")")
    print("RESULT :", out_dir / "result.json")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="glm-5")
    ap.add_argument("--tools", action="store_true")
    a = ap.parse_args()
    anyio.run(main, a.model, a.tools)
