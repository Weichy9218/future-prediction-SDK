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

# Cues that a free-form question wants a NUMBER (a quantity/series value), vs. an event/entity.
# Source-agnostic (no site/series names) — just the vocabulary of quantities and units.
_NUMERIC_CUES = re.compile(
    r"\b(price|value|level|index|rate|ratio|yield|share of|capitali[sz]ation|market cap|"
    r"amount|total|number of|how many|how much|percentage|usd|dollar|yuan|rmb|cny|"
    r"kg|kilogram|tonne|ton|barrel|bushel|decimal places)\b"
    r"|总市值|市值|价格|指数|百分|元|公斤|吨", re.I)


@dataclass
class Question:
    task_id: str
    task_question: str
    forecast_type: str
    target_date: Optional[str]
    as_of: Optional[str]
    task_description: str = ""


def _infer_type(q: str) -> str:
    """Classify the answer space so the runner can pick the numeric (A) vs event (B) playbook.

    The benchmark's answer contract is the strongest signal: a Yes/No box or enumerated A./B.
    options are clearly events; an explicit `\\boxed{number}` is numeric. The hard case is the
    generic `\\boxed{YOUR_PREDICTION}` free-form contract, which covers BOTH numeric quantities
    (a price, a market cap) and open events/entities (who wins, which names) — there we fall back
    to numeric-vocabulary cues. Everything non-numeric routes to the event playbook (no third
    playbook: B already spans market/odds/base-rate priors and latest-known-state priors).
    """
    if re.search(r"\\boxed\{\s*(yes|no)\s*\}", q, re.I):
        return "binary event"
    opts = re.findall(r"^[A-Z]\.\s", q, re.MULTILINE)
    if len(opts) >= 2:
        return "multiple choice"
    if "numeric prediction" in q or "\\boxed{number}" in q:
        return "number"
    # generic free-form contract: decide by whether a quantity is being asked for.
    return "number" if _NUMERIC_CUES.search(q) else "open event"


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
