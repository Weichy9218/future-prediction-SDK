"""Serialize ScorableForecast -> verl-tool-future submission JSONL.

The scorer expects rows keyed by `id`/`task_id` with a prediction string that ends in
`\\boxed{...}`; for binary questions a probability may also be given as
`<probability>p</probability>` (brier.py parses both). We emit both so one record scores
under either rule.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .schema import ScorableForecast


def to_submission_row(fc: ScorableForecast) -> dict[str, str]:
    body = (fc.reasoning or "").strip()
    if fc.forecast_type == "binary choice" and fc.probability is not None:
        body += f"\n<probability>{fc.probability}</probability>"
    boxed = _boxed_answer(fc)
    return {"id": fc.task_id, "task_id": fc.task_id, "prediction": f"{body}\n\\boxed{{{boxed}}}".strip()}


def _boxed_answer(fc: ScorableForecast) -> str:
    if fc.answer is not None:
        return str(fc.answer)
    if fc.forecast_type == "number" and fc.point is not None:
        return str(fc.point)
    if fc.forecast_type == "binary choice" and fc.probability is not None:
        return str(fc.probability)
    if fc.option_probabilities:
        return max(fc.option_probabilities, key=fc.option_probabilities.get)
    if fc.ranking:
        return ",".join(fc.ranking)
    return ""


def write_submission(forecasts: Iterable[ScorableForecast], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for fc in forecasts:
            fh.write(json.dumps(to_submission_row(fc), ensure_ascii=False) + "\n")
    return path
