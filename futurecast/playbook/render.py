"""Build the prompt for one question (kit #1 = cognition in the prompt, not a state machine).

render() picks the playbook by forecast_type, injects the as-of cutoff and any ON-DEMAND
experience notes, and returns (system_prompt, user_prompt). No typed frame, no coverage.
"""
from __future__ import annotations

from pathlib import Path

from ..data.loader import Question
from ..experience.store import retrieve

_DIR = Path(__file__).resolve().parent
_A = (_DIR / "playbook_A_numeric.md").read_text(encoding="utf-8")
_B = (_DIR / "playbook_B_event.md").read_text(encoding="utf-8")


def _playbook_for(forecast_type: str) -> str:
    return _A if forecast_type == "number" else _B


def render(q: Question, *, question_class: str | None = None, use_experience: bool = True) -> tuple[str, str]:
    guard = (
        f"AS-OF CUTOFF: {q.as_of}. You may only use information available up to this date. "
        f"Any source dated after it is blocked from your context; do not infer the answer from "
        f"post-cutoff knowledge."
    )
    notes_block = ""
    if use_experience and question_class:
        notes = retrieve(question_class)
        if notes:
            notes_block = "\n\nRELEVANT EXPERIENCE (from past same-class questions):\n" + "\n".join(
                f"- [{n.question_class}] via {n.source}: {n.method} -> {n.calibration}" for n in notes
            )

    system_prompt = f"{_playbook_for(q.forecast_type)}\n\n{guard}{notes_block}"
    return system_prompt, q.task_question
