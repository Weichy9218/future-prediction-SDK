"""Run one FutureWorld/FutureX question through the Claude Agent SDK, driven by a CHEAP
non-Claude model, with the model's THINKING captured into the rollout.

Routing (no Claude tokens spent):
  Claude Agent SDK -> claude CLI -> ANTHROPIC_BASE_URL=127.0.0.1:3456 -> OUR llm_adapter
  -> gateway model (glm-5 @ apihy, gpt-5.5 @ haoxiang). The model is chosen by env
  FUTURECAST_MODEL (set by run.sh); the SAME agent + tool surface serves all models.

Reasoning capture (the trajectory must explain HOW/WHY the answer was produced):
  We enable extended thinking on the Agent SDK side; the adapter maps it to the upstream
  `reasoning.effort` and replays the returned reasoning summary as Anthropic `thinking` blocks.
  So glm/gpt's intermediate reasoning lands in the CLI rollout transcript alongside each
  assistant turn — analyzable, not dropped.

Tools (`--tools`): our in-process Serper/Jina/Exa MCP tools (real keys, as-of guarded) plus a
  representative slice of the official agent loop (Read/Glob/Grep/Edit/Write/Bash/Agent/Task/Skill);
  host-harness noise and Anthropic's off-Claude WebSearch/WebFetch are disallowed (see tools_mcp).
  as-of is enforced at the tool boundary (FUTURECAST_AS_OF) using the effective cutoff:
  min(target-1, run_date), unless explicitly overridden.

Output: the question's OWN answer contract governs output (`\boxed{...}`); we do not impose a
  second format. The final answer is extracted lightly from the box; the process is the rollout.

Usage (prefer the run.sh entry point, which also starts the adapter):
  .venv/bin/python agent_sdk/run_forecast.py [--model glm-5|gpt-5.5] [--tools]
      [--question-file tasks/<file>.jsonl] [--task-index 0]
      [--run-date YYYY-MM-DD] [--as-of YYYY-MM-DD]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

import anyio
from claude_agent_sdk import (
    query, ClaudeAgentOptions, AssistantMessage, ResultMessage,
    TextBlock, ThinkingBlock, ToolUseBlock, project_key_for_directory,
)

ROUTER = "http://127.0.0.1:3456"
HERE = Path(__file__).resolve().parent
CWD = HERE.parent  # the futurecast repo root
sys.path.insert(0, str(HERE))   # tools_mcp
sys.path.insert(0, str(CWD))    # futurecast package

from config import from_env, export_env  # noqa: E402  sibling: typed run parameters
from common import (  # noqa: E402
    DEFAULT_QFILE, config_summary, extract_boxed, load_question_and_prompt, run_output_dir,
)
from sync_skills import CLAUDE_PLUGIN_DIR, skill_names, sync_claude  # noqa: E402


async def main(cfg, use_tools: bool, qfile: str, task_index: int) -> None:
    export_env(cfg)   # make the resolved config the source of truth for in-process tools + the adapter
    enabled_skills = skill_names()
    if enabled_skills and not CLAUDE_PLUGIN_DIR.exists():
        sync_claude()
    q, desired_as_of, effective_as_of, system_prompt = load_question_and_prompt(qfile, task_index, cfg)
    os.environ["FUTURECAST_AS_OF"] = effective_as_of   # the as-of guard (tools_mcp) reads this
    os.environ["FUTURECAST_TARGET"] = q.target_date or ""  # the date whose value must NOT leak

    env = dict(os.environ)
    env.update(
        ANTHROPIC_BASE_URL=ROUTER,
        ANTHROPIC_API_KEY="dummy-router-key",
        ANTHROPIC_AUTH_TOKEN="dummy-router-key",
    )
    mcp_servers: dict = {}
    allowed: list[str] = []
    disallowed = [
        "WebSearch", "WebFetch",
        "Bash", "Read", "Glob", "Grep", "Edit", "Write", "NotebookEdit",
        "Agent", "Skill",
        "TaskCreate", "TaskGet", "TaskList", "TaskUpdate",
    ]
    if use_tools:
        from tools_mcp import create_server, ALLOWED, DISALLOWED_BUILTINS
        mcp_servers = {"futurecast": create_server()}
        allowed, disallowed = ALLOWED, DISALLOWED_BUILTINS

    options = ClaudeAgentOptions(
        system_prompt=system_prompt,
        model="claude-sonnet-4-5",                 # dummy; adapter routes to FUTURECAST_MODEL
        permission_mode="bypassPermissions",
        mcp_servers=mcp_servers,
        allowed_tools=allowed,
        disallowed_tools=disallowed,
        thinking={"type": "enabled", "budget_tokens": cfg.thinking_budget},  # -> adapter -> reasoning.effort
        max_turns=cfg.max_turns if use_tools else 3,
        cwd=str(CWD),
        env=env,
        plugins=[{"type": "local", "path": str(CLAUDE_PLUGIN_DIR)}],
        skills=enabled_skills,
        setting_sources=[],
    )

    print(f"# routing: Agent SDK -> {ROUTER} -> {cfg.model} | tools={use_tools} | "
          f"task={q.task_id} target={q.target_date} desired_as_of={desired_as_of} "
          f"effective_as_of={effective_as_of} run_date={cfg.run_date}\n"
          f"# config: {config_summary(cfg)}\n",
          flush=True)
    final_text, thinking_text, session_id, result, n_tool, n_think = "", "", None, None, 0, 0
    run_error = None
    try:
        async for msg in query(prompt=q.task_question, options=options):
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, ThinkingBlock):
                        n_think += 1
                        thinking_text += block.thinking + "\n"
                        print(f"\n[thinking] {block.thinking[:240]}…", flush=True)
                    elif isinstance(block, TextBlock):
                        final_text += block.text
                        print(block.text, end="", flush=True)
                    elif isinstance(block, ToolUseBlock):
                        n_tool += 1
                        print(f"\n[tool_use {block.name} {block.input}]", flush=True)
            elif isinstance(msg, ResultMessage):
                result = msg
                session_id = getattr(msg, "session_id", None)
    except Exception as exc:  # e.g. "Reached maximum number of turns" — keep the partial rollout
        # The SDK raises on max-turns / mid-stream errors. Don't lose the run: record the error and
        # fall through to write whatever was captured (rollout + thinking + any boxed answer).
        run_error = f"{type(exc).__name__}: {exc}"
        print(f"\n[run-error captured, writing partial result] {run_error}", flush=True)

    print("\n\n=== RESULT ===", flush=True)
    print(f"session_id: {session_id} | tool_use={n_tool} | thinking_blocks={n_think}"
          f"{' | ERROR: ' + run_error if run_error else ''}")
    usage = getattr(result, "usage", None) if result else None
    if result is not None:
        print("total_cost_usd:", getattr(result, "total_cost_usd", None))

    # --- standardized, trajectory-first log output -------------------------------------
    out_dir = run_output_dir(cfg, q, backend="claude_code", use_tools=use_tools)
    out_dir.mkdir(parents=True, exist_ok=True)

    proj = Path.home() / ".claude/projects" / project_key_for_directory(str(CWD))
    transcript = (proj / f"{session_id}.jsonl") if session_id else None
    if transcript is None or not transcript.exists():
        cands = sorted(proj.glob("*.jsonl"), key=lambda p: p.stat().st_mtime) if proj.exists() else []
        transcript = cands[-1] if cands else None
    if transcript and transcript.exists():
        shutil.copy(transcript, out_dir / "rollout.jsonl")

    result_json = {
        "backend": "claude_code",
        "task_id": q.task_id, "model": cfg.model, "as_of": effective_as_of,
        "target_date": q.target_date, "desired_as_of": desired_as_of,
        "effective_as_of": effective_as_of, "run_date": cfg.run_date,
        "as_of_override": cfg.as_of_override or None,
        "forecast_type": q.forecast_type, "tools": use_tools, "config": config_summary(cfg),
        "tool_use_count": n_tool, "thinking_blocks": n_think, "session_id": session_id,
        "answer": extract_boxed(final_text),          # the one final answer (benchmark contract)
        "run_error": run_error,                        # set if the SDK raised (e.g. max-turns); else None
        "reasoning_summary": thinking_text.strip(),    # the captured thinking (process/why)
        "final_text": final_text.strip(),
        "usage": dict(usage) if isinstance(usage, dict) else (dict(usage) if usage else None),
    }
    (out_dir / "result.json").write_text(json.dumps(result_json, ensure_ascii=False, indent=2), encoding="utf-8")
    print("ROLLOUT:", out_dir / "rollout.jsonl", "(exists:", (out_dir / "rollout.jsonl").exists(), ")")
    print("RESULT :", out_dir / "result.json", "| answer:", result_json["answer"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    # --model is the routing knob; the rest default from env (config.from_env) and are
    # overridden here only when explicitly passed (default=None below).
    ap.add_argument("--model", default=None)
    ap.add_argument("--tools", action="store_true")
    ap.add_argument("--question-file", default=DEFAULT_QFILE)
    ap.add_argument("--task-index", type=int, default=0)
    ap.add_argument("--max-turns", type=int, default=None, help="agent turns when --tools")
    ap.add_argument("--run-group", default=None, help="output dir log/<run_group>/...")
    ap.add_argument("--run-date", default=None,
                    help="date the forecast is made; defaults to local today")
    ap.add_argument("--as-of", dest="as_of_override", default=None,
                    help="explicit effective cutoff; overrides min(target-1, run_date)")
    ap.add_argument("--asof-screen", choices=["off", "loose", "strict"], default=None,
                    help="tool-boundary as-of screening strictness")
    a = ap.parse_args()
    cfg = from_env(model=a.model, max_turns=a.max_turns, run_group=a.run_group,
                   run_date=a.run_date, as_of_override=a.as_of_override,
                   asof_screen=a.asof_screen)
    anyio.run(main, cfg, a.tools, a.question_file, a.task_index)
