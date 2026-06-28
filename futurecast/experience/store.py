"""Experience library (kit #4) — the real "self-evolve", and what stock coding agents lack.

After each question (especially once ground truth lands) we distill a compact note:
  question-class -> which source/method worked -> calibration outcome.
On the NEXT question of the same class we retrieve those notes ON DEMAND and inject them into
the prompt. We NEVER preload the whole library — that would (a) leak across questions and
(b) destroy generality. The with-experience vs without-experience calibration delta is the
measurable evidence of self-evolution.

Storage is deliberately dumb: one JSON line per note under experience/notes/. No state machine.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

NOTES_DIR = Path(__file__).resolve().parent / "notes"


@dataclass
class ExperienceNote:
    question_class: str          # e.g. "futureworld:hog_price", "futurex:nba_game"
    source: str                  # the source/method that worked (or failed)
    method: str                  # e.g. "latest same-series value + random walk"
    calibration: str             # e.g. "rel_err 2%", "interval too narrow, widen", "anchor was ~10 not ~15"
    as_of: Optional[str] = None


def record(note: ExperienceNote, notes_dir: Path = NOTES_DIR) -> None:
    notes_dir.mkdir(parents=True, exist_ok=True)
    with (notes_dir / "notes.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(asdict(note), ensure_ascii=False) + "\n")


def retrieve(question_class: str, notes_dir: Path = NOTES_DIR, limit: int = 5) -> list[ExperienceNote]:
    """On-demand retrieval by question class. Returns most-recent matching notes only."""
    path = notes_dir / "notes.jsonl"
    if not path.exists():
        return []
    hits = [ExperienceNote(**json.loads(l)) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    hits = [n for n in hits if n.question_class == question_class]
    return hits[-limit:]


# TODO: question_class taxonomy + a fuzzy match (embedding) so "内三元" and "瘦肉型猪价"
# can share hog-price experience. Keep the taxonomy generic — no per-site code in core.
