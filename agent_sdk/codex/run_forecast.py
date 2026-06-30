"""Run one forecast question through Codex non-interactive mode.

The Codex backend rents Codex's own agent loop via `codex exec --json`. It
shares question loading, prompt assembly, as-of resolution, boxed extraction,
and result schema with the Claude Code backend, while keeping the raw Codex
event stream in a backend-separated rollout file.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
AGENT_DIR = HERE.parent
CWD = AGENT_DIR.parent
sys.path.insert(0, str(AGENT_DIR))
sys.path.insert(0, str(CWD))

from config import from_env, export_env  # noqa: E402
from common import (  # noqa: E402
    DEFAULT_QFILE, config_summary, extract_boxed, load_question_and_prompt, run_output_dir,
)


def _codex_model(cfg) -> str:
    """Model name for Codex. Defaults to the same FUTURECAST_MODEL used by Claude runs."""
    return (os.environ.get("FUTURECAST_CODEX_MODEL") or cfg.model).strip()


def _build_codex_config_args(use_tools: bool) -> list[str]:
    args = [
        "-c", 'model_provider="sub2api"',
        "-c", 'model_providers.sub2api.name="Sub2API Responses"',
        "-c", 'model_providers.sub2api.base_url="https://ie-crs.haoxiang.ai/v1"',
        "-c", 'model_providers.sub2api.env_key="SUB2API_API_KEY"',
        "-c", 'model_providers.sub2api.wire_api="responses"',
        "-c", 'model_reasoning_summary="auto"',
        "-c", 'model_supports_reasoning_summaries=true',
        "-c", 'model_verbosity="low"',
    ]
    if not use_tools:
        args.extend(["-c", 'tools.web_search=false'])
    return args


def _build_prompt(system_prompt: str, question: str, use_tools: bool) -> str:
    tool_note = (
        "Use Codex live web search when it can materially improve the prior. Keep searches few and "
        "respect the as-of cutoff in every query and source choice."
        if use_tools
        else "Do not use tools or shell commands. Produce the best calibrated forecast from the prompt and your prior knowledge."
    )
    return (
        system_prompt
        + "\n\n## Codex backend instructions\n"
        + tool_note
        + "\nYou are running under the Codex backend. Do not edit files. Do not run shell commands. "
        + "Return the forecast answer required by the question, ending with the required \\boxed{}.\n\n"
        + "## Question\n"
        + question
    )


def _safe_event(line: str) -> dict[str, Any] | None:
    try:
        return json.loads(line)
    except ValueError:
        return None


def _item_kind(event: dict[str, Any]) -> str:
    item = event.get("item")
    if isinstance(item, dict):
        return str(item.get("type") or "")
    return ""


def _collect_rollout(raw: str) -> dict[str, Any]:
    final_text = ""
    reasoning_parts: list[str] = []
    tool_count = 0
    thinking_blocks = 0
    thread_id = None
    usage = None

    for line in raw.splitlines():
        event = _safe_event(line)
        if not event:
            continue
        if event.get("type") == "thread.started":
            thread_id = event.get("thread_id") or thread_id
        if event.get("type") == "turn.completed":
            usage = event.get("usage") or usage

        item = event.get("item") if isinstance(event.get("item"), dict) else {}
        kind = str(item.get("type") or "")
        text = item.get("text") or item.get("content") or ""
        if kind == "agent_message" and text:
            final_text = str(text)
        elif kind == "reasoning":
            thinking_blocks += 1
            if text:
                reasoning_parts.append(str(text))
        elif event.get("type") == "item.completed" and kind in {"mcp_tool_call", "web_search", "command_execution"}:
            tool_count += 1

    return {
        "final_text": final_text,
        "reasoning_summary": "\n".join(reasoning_parts).strip(),
        "thinking_blocks": thinking_blocks,
        "tool_use_count": tool_count,
        "session_id": thread_id,
        "usage": usage,
    }


def main(cfg, use_tools: bool, qfile: str, task_index: int) -> None:
    export_env(cfg)
    q, desired_as_of, effective_as_of, system_prompt = load_question_and_prompt(
        qfile, task_index, cfg, tool_boundary="codex_native_search",
    )
    os.environ["FUTURECAST_AS_OF"] = effective_as_of
    os.environ["FUTURECAST_TARGET"] = q.target_date or ""

    out_dir = run_output_dir(cfg, q, backend="codex", use_tools=use_tools)
    out_dir.mkdir(parents=True, exist_ok=True)
    rollout_path = out_dir / "rollout.jsonl"
    stderr_path = out_dir / "stderr.log"

    env = dict(os.environ)
    env.setdefault("SUB2API_API_KEY", env.get("GPT_sub2api_apikey", ""))
    env.setdefault("SUB2API_BASE_URL", "https://ie-crs.haoxiang.ai/v1")
    env["CODEX_HOME"] = str(AGENT_DIR / "codex" / "cli_home")
    Path(env["CODEX_HOME"]).mkdir(parents=True, exist_ok=True)

    prompt = _build_prompt(system_prompt, q.task_question, use_tools)
    cmd = ["codex", "--ask-for-approval", "never"]
    if use_tools:
        cmd.append("--search")
    cmd.extend([
        "exec", "--json", "--skip-git-repo-check", "--sandbox", "read-only",
        "--model", _codex_model(cfg), "--cd", str(CWD),
        *_build_codex_config_args(use_tools),
        "-",
    ])

    print(f"# routing: Codex exec -> {_codex_model(cfg)} | tools={use_tools} | "
          f"task={q.task_id} target={q.target_date} desired_as_of={desired_as_of} "
          f"effective_as_of={effective_as_of} run_date={cfg.run_date}\n"
          f"# config: {config_summary(cfg)}\n",
          flush=True)

    proc = subprocess.run(
        cmd, input=prompt, text=True, capture_output=True, cwd=str(CWD), env=env, check=False,
    )
    rollout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")

    parsed = _collect_rollout(proc.stdout)
    run_error = None if proc.returncode == 0 else f"codex exec exited {proc.returncode}"
    final_text = parsed["final_text"] or proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""
    result_json = {
        "backend": "codex",
        "task_id": q.task_id, "model": _codex_model(cfg), "as_of": effective_as_of,
        "target_date": q.target_date, "desired_as_of": desired_as_of,
        "effective_as_of": effective_as_of, "run_date": cfg.run_date,
        "as_of_override": cfg.as_of_override or None,
        "forecast_type": q.forecast_type, "tools": use_tools, "config": config_summary(cfg),
        "tool_use_count": parsed["tool_use_count"], "thinking_blocks": parsed["thinking_blocks"],
        "session_id": parsed["session_id"],
        "answer": extract_boxed(final_text),
        "run_error": run_error,
        "reasoning_summary": parsed["reasoning_summary"],
        "final_text": final_text.strip(),
        "usage": parsed["usage"],
        "stderr_path": str(stderr_path),
    }
    (out_dir / "result.json").write_text(json.dumps(result_json, ensure_ascii=False, indent=2), encoding="utf-8")
    print("ROLLOUT:", rollout_path, "(exists:", rollout_path.exists(), ")")
    print("RESULT :", out_dir / "result.json", "| answer:", result_json["answer"],
          f"| error: {run_error}" if run_error else "")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None)
    ap.add_argument("--tools", action="store_true")
    ap.add_argument("--question-file", default=DEFAULT_QFILE)
    ap.add_argument("--task-index", type=int, default=0)
    ap.add_argument("--max-turns", type=int, default=None)
    ap.add_argument("--run-group", default=None)
    ap.add_argument("--run-date", default=None)
    ap.add_argument("--as-of", dest="as_of_override", default=None)
    ap.add_argument("--asof-screen", choices=["off", "loose", "strict"], default=None)
    a = ap.parse_args()
    cfg = from_env(model=a.model, max_turns=a.max_turns, run_group=a.run_group,
                   run_date=a.run_date, as_of_override=a.as_of_override,
                   asof_screen=a.asof_screen)
    main(cfg, a.tools, a.question_file, a.task_index)
