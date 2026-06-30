"""Smoke tests — the converged repo's spec. Run: .venv/bin/python -m pytest -q

Covers the CONTROL LAYER only (futurecast/) plus the as-of tool guard in agent_sdk/. The
agent loop itself is rented (Claude Agent SDK + our llm_adapter) and is exercised by agent_sdk/run.sh,
not here.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "agent_sdk"))


def test_imports():
    # the control-layer spine must import without the heavy optional deps
    from futurecast.io.schema import ScorableForecast, Source  # noqa: F401
    from futurecast.io.to_submission import to_submission_row  # noqa: F401
    from futurecast.guard.as_of import check_as_of  # noqa: F401
    from futurecast.data.loader import Question  # noqa: F401
    assert ScorableForecast is not None


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


def test_as_of_policy_blocks_post_cutoff():
    from futurecast.guard.as_of import check_as_of
    v = check_as_of("value on 2026-06-20", cutoff="2026-06-14", extract_timestamp=lambda s: "2026-06-20")
    assert not v.allowed and v.reason == "post_cutoff"
    v2 = check_as_of("value on 2026-06-10", cutoff="2026-06-14", extract_timestamp=lambda s: "2026-06-10")
    assert v2.allowed


def test_tool_guard_date_parsing_and_redaction():
    # the #1 correctness fix: post-cutoff dates embedded in search snippets must be detectable
    import tools_mcp as T
    assert T.parse_loose_date("2026-06-20") == "2026-06-20"
    assert T.parse_loose_date("2026/6/27") == "2026-06-27"
    assert T.parse_loose_date("Jun 10, 2026") == "2026-06-10"
    assert T._after_cutoff("2026-06-20", "2026-06-14") is True
    assert T._has_post_cutoff_date("江苏 2026/6/27 土杂猪 9.80", "2026-06-14") is True
    assert T._has_post_cutoff_date("2026年6月10日 价格 10.1", "2026-06-14") is False


def test_effective_as_of_caps_future_desired_cutoff():
    from futurecast.data.loader import desired_as_of_from_target, resolve_effective_as_of

    desired = desired_as_of_from_target("2026-07-06")
    assert desired == "2026-07-05"
    assert resolve_effective_as_of(desired, run_date="2026-06-30") == "2026-06-30"
    assert resolve_effective_as_of(desired, run_date="2026-07-10") == "2026-07-05"
    assert resolve_effective_as_of(desired, run_date="2026-06-30", override="2026-07-05") == "2026-07-05"


def test_tool_budget_nudge_and_repeat_suppression(monkeypatch):
    import tools_mcp as T

    monkeypatch.setenv("FUTURECAST_MAX_TURNS", "10")
    T._TOOL_STATE["count"] = 0
    T._TOOL_STATE["seen"] = []

    assert T._track_tool_request("web_search", "site:szse.cn 深证A股 股息率 2026-07-03") is None
    repeat = T._track_tool_request("web_search", "site szse cn 深证A股 股息率 2026 07 03")
    assert repeat is not None
    assert "repeat suppressed" in repeat
    assert "tool-budget nudge" not in repeat
    assert "answer now" not in repeat

    for i in range(3, 6):
        assert T._track_tool_request("web_search", f"unique half query {i}") is None
    half_note = T._budget_note()
    assert "5/10 tool requests used" in half_note
    assert "~half" in half_note
    assert "Avoid repeated searches" in half_note
    assert "answer now" not in half_note

    for i in range(6, 9):
        assert T._track_tool_request("web_search", f"unique urgent query {i}") is None
    urgent_note = T._budget_note()
    assert "8/10 tool requests used" in urgent_note
    assert ">=80%" in urgent_note
    assert "answer now" in urgent_note


def test_repeat_suppression_allows_distinct_search_pages(monkeypatch):
    import tools_mcp as T

    monkeypatch.setenv("FUTURECAST_MAX_TURNS", "10")
    T._TOOL_STATE["count"] = 0
    T._TOOL_STATE["seen"] = []

    query = "long repeated search terms about a series source historical value latest baseline"
    assert T._track_tool_request("web_search", f"{query} page=1") is None
    assert T._track_tool_request("web_search", f"{query} page=2") is None
    assert T._track_tool_request("web_search", f"{query} page=2") is not None
