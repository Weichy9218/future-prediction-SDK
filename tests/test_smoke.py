"""Smoke tests — the new repo's first spec. Run: .venv/bin/python -m pytest -q"""
from __future__ import annotations


def test_imports():
    # the spine must import without the heavy optional deps (claude/verl-tool-future)
    from futurecast.io.schema import ScorableForecast, Source
    from futurecast.io.to_submission import to_submission_row
    from futurecast.loop.agent import run_loop
    from futurecast.model.backend import ModelBackend
    from futurecast.guard.as_of import check_as_of
    from futurecast.data.loader import Question
    assert ModelBackend is not None


def test_submission_roundtrip_number():
    from futurecast.io.schema import ScorableForecast
    from futurecast.io.to_submission import to_submission_row
    fc = ScorableForecast(task_id="t1", forecast_type="number", as_of="2026-06-14", point=16.2)
    row = to_submission_row(fc)
    assert row["id"] == "t1"
    assert "\\boxed{16.2}" in row["prediction"]


def test_submission_binary_has_probability():
    from futurecast.io.schema import ScorableForecast
    from futurecast.io.to_submission import to_submission_row
    fc = ScorableForecast(task_id="t2", forecast_type="binary choice", as_of="2026-06-14",
                          answer="A", probability=0.62)
    row = to_submission_row(fc)
    assert "<probability>0.62</probability>" in row["prediction"]
    assert "\\boxed{A}" in row["prediction"]


def test_as_of_blocks_post_cutoff():
    from futurecast.guard.as_of import check_as_of
    v = check_as_of("value on 2026-06-20", cutoff="2026-06-14", extract_timestamp=lambda s: "2026-06-20")
    assert not v.allowed and v.reason == "post_cutoff"
    v2 = check_as_of("value on 2026-06-10", cutoff="2026-06-14", extract_timestamp=lambda s: "2026-06-10")
    assert v2.allowed
