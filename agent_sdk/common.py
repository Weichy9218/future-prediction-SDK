"""Shared forecast-run plumbing used by both Claude Code and Codex backends.

This module owns only backend-neutral pieces: prompt assembly, boxed-answer
extraction, model/run naming, and standardized result paths.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from futurecast.data.loader import load_questions, resolve_effective_as_of

HERE = Path(__file__).resolve().parent
CWD = HERE.parent
PLAYBOOK_DIR = CWD / "futurecast/playbook"
DEFAULT_QFILE = "tasks/sample_futureworld_0624_30.jsonl"

_MODEL_SHORT = {
    "glm-5": "glm5",
    "glm-5.1": "glm51",
    "gpt-5.5": "gpt55",
    "gpt-5.4": "gpt54",
}


def is_numeric(forecast_type: str) -> bool:
    """Numeric-series questions use playbook A; events/choices use playbook B."""
    return forecast_type == "number"


def build_system_prompt(
    q,
    effective_as_of: str,
    desired_as_of: str,
    run_date: str,
    *,
    tool_boundary: str = "futurecast_mcp",
) -> str:
    """Assemble the type-specific playbook + tool boundary + as-of vantage frame."""
    as_of, target = effective_as_of, q.target_date or ""
    desired_note = (
        f"The benchmark desired cutoff is {desired_as_of}, but this live run date is {run_date}; "
        f"the effective cutoff is therefore {effective_as_of}."
        if desired_as_of and desired_as_of != effective_as_of
        else f"The effective cutoff for this run is {effective_as_of}."
    )
    guarded_tools = tool_boundary == "futurecast_mcp"
    if is_numeric(q.forecast_type):
        playbook = (PLAYBOOK_DIR / "playbook_A_numeric.md").read_text(encoding="utf-8")
        if guarded_tools:
            boundary = (
                "Use `web_search` / `read_webpage` / `exa_search` to find the most recent authoritative "
                "value of THIS exact series at or before the as-of cutoff. Every fetch is as-of guarded: "
                "anything dated after the cutoff is blocked or redacted, so do not try to read the "
                "realized value.\nFollow the question's required answer format exactly."
            )
        else:
            boundary = (
                "Use the backend's live web search only when it materially improves the prior. There is "
                "no Futurecast MCP fetch guard in this backend, so you must restrict queries and source "
                "choice to information published on or before the as-of cutoff. Ignore resolved values "
                "or post-cutoff reporting.\nFollow the question's required answer format exactly."
            )
        vantage = (
            f"its realized value does not exist and cannot be looked up. You must FORECAST it from "
            f"information available on or before {as_of}. If any source appears to state the value "
            f"AT the target date, it is post-cutoff — ignore it"
            + (" (the fetch guard also blocks/redacts such data)." if guarded_tools else ".")
            + f" Anchor on the latest value at/<= {as_of}, then extrapolate."
        )
    else:
        playbook = (PLAYBOOK_DIR / "playbook_B_event.md").read_text(encoding="utf-8")
        if guarded_tools:
            boundary = (
                "Use `web_search` / `read_webpage` / `exa_search` to find the PRIOR for this event as of "
                "the cutoff: the prediction-market price / bookmaker odds / polling average, or — if none "
                "exists — a reference-class base rate. Every fetch is as-of guarded: anything dated after "
                "the cutoff is blocked or redacted, so do not try to read the resolved outcome.\n"
                "Follow the question's required answer format exactly."
            )
        else:
            boundary = (
                "Use the backend's live web search only when it materially improves the prior: market "
                "price, bookmaker odds, polling average, reference-class base rate, or latest known "
                "state. There is no Futurecast MCP fetch guard in this backend, so you must restrict "
                "queries and source choice to information published on or before the as-of cutoff. "
                "Ignore resolved outcomes or post-cutoff reporting.\n"
                "Follow the question's required answer format exactly."
            )
        vantage = (
            f"the event has NOT resolved yet from your vantage point: the outcome does not exist and "
            f"cannot be looked up. You must FORECAST it from information (markets/odds/polls/base "
            f"rates) available on or before {as_of}. If any source appears to state the resolved "
            f"outcome, it is post-cutoff — ignore it"
            + (" (the fetch guard also blocks/redacts such data)." if guarded_tools else ".")
            + f" Anchor on the prior available at/<= {as_of}, then adjust with a few factors."
        )
    return (
        playbook
        + "\n\n## Tools & boundary\n" + boundary
        + "\n\n## Vantage point (hard rule)\n"
        + desired_note + "\n"
        + f"Treat **{as_of}** as the current date ('today'). The target **{target}** has NOT "
        f"happened yet from your vantage point: " + vantage
    )


def extract_boxed(text: str) -> str | None:
    """Light extraction of the benchmark's own ``\\boxed{...}`` answer contract."""
    matches = re.findall(r"\\boxed\{([^}]*)\}", text or "")
    return matches[-1].strip() if matches else None


def model_short(model: str) -> str:
    return _MODEL_SHORT.get(model, model.replace(".", "").replace("-", ""))


def load_question_and_prompt(
    qfile: str,
    task_index: int,
    cfg,
    *,
    tool_boundary: str = "futurecast_mcp",
) -> tuple[Any, str, str, str]:
    """Load one question and return (question, desired_as_of, effective_as_of, system_prompt)."""
    path = CWD / qfile if not Path(qfile).is_absolute() else Path(qfile)
    questions = load_questions(path)
    if not questions:
        raise SystemExit(f"no questions in {qfile}")
    q = questions[task_index]
    desired_as_of = q.as_of or ""
    effective_as_of = resolve_effective_as_of(desired_as_of, cfg.run_date, cfg.as_of_override)
    system_prompt = build_system_prompt(
        q, effective_as_of, desired_as_of, cfg.run_date, tool_boundary=tool_boundary,
    )
    return q, desired_as_of, effective_as_of, system_prompt


def run_output_dir(cfg, q, *, backend: str, use_tools: bool) -> Path:
    """Standardized output root with backend separation."""
    suffix = "-tools" if use_tools else ""
    return CWD / "log" / cfg.run_group / backend / f"{q.task_id}-{model_short(cfg.model)}{suffix}"


def config_summary(cfg) -> str:
    return (f"model={cfg.model} effort={cfg.reasoning_effort} max_tokens={cfg.max_tokens} "
            f"max_turns={cfg.max_turns} thinking={cfg.thinking_budget} run_group={cfg.run_group} "
            f"run_date={cfg.run_date} as_of_override={cfg.as_of_override or '-'} "
            f"asof_screen={cfg.asof_screen} return_budget={cfg.return_budget}")
