"""Scoring (kit #3 backend) — reuse verl-tool-future, do NOT re-implement metrics.

verl-tool-future (https://github.com/ZhixinHan/verl-tool-future) replaces the missing
`benchmark_merge_v8` scorer. Two reusable entry points:
  - benchmark.scoring.score_submission_file(...)  -> full FutureWorld/FutureX metrics
  - rewards.brier.brier_score(text, gold)         -> zero-dep binary Brier (handy for unit tests)

Add verl-tool-future to the env (path dep in pyproject) so these import. Imports are lazy so
the rest of the repo works without the heavy akshare/transformers stack installed.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional


def score_submission(
    benchmark_dir: str | Path,
    submission_file: str | Path,
    *,
    gold_path: Optional[str | Path] = None,
    scoring_rule: str = "futureworld",   # "futureworld" | "futurex"
    output_dir: Optional[str | Path] = None,
) -> dict[str, Path]:
    """Thin pass-through to verl_tool_future's scorer. Returns the written metric file paths."""
    from verl_tool_future.benchmark.scoring import score_submission_file
    return score_submission_file(
        benchmark_dir, submission_file,
        gold_path=gold_path, output_dir=output_dir, scoring_rule=scoring_rule,
    )


def brier(prediction_text: str, ground_truth: Any) -> dict[str, Any]:
    """Zero-dep binary Brier; parses \\boxed{p} or <probability>p</probability>."""
    from verl_tool_future.rewards.brier import brier_score
    return brier_score(prediction_text, ground_truth)
