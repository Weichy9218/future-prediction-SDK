"""Load FutureWorld / FutureX question files (harvested data contract).

Question files are JSONL with {task_id, task_question, task_description?}. The task_question
embeds the target date and the answer-space instructions. We parse out:
  - forecast_type (number | binary choice | ... ) from the answer-format instructions
  - target_date   (the date being predicted)
  - as_of         (the cutoff the forecaster may use = target_date - 1 day, by default)

Keep this generic — no per-series parsing here.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

_DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")


@dataclass
class Question:
    task_id: str
    task_question: str
    forecast_type: str
    target_date: Optional[str]
    as_of: Optional[str]
    task_description: str = ""


def _infer_type(q: str) -> str:
    if "numeric prediction" in q or "\\boxed{number}" in q:
        return "number"
    # choice questions enumerate "A. ... B. ..."; binary if exactly A/B
    opts = re.findall(r"^[A-Z]\.\s", q, re.MULTILINE)
    if len(opts) == 2:
        return "binary choice"
    if len(opts) > 2:
        return "simple multiple choice"
    return "number"


def load_questions(path: str | Path, as_of_offset_days: int = 1) -> list[Question]:
    out: list[Question] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        q = d["task_question"]
        m = _DATE_RE.search(q)
        target = m.group(1) if m else None
        as_of = None
        if target:
            as_of = (date.fromisoformat(target) - timedelta(days=as_of_offset_days)).isoformat()
        out.append(Question(
            task_id=d["task_id"], task_question=q, forecast_type=_infer_type(q),
            target_date=target, as_of=as_of, task_description=d.get("task_description", ""),
        ))
    return out
