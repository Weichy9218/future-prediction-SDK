"""Smoke tests — the converged repo's spec. Run: .venv/bin/python -m pytest -q

Covers the CONTROL LAYER only (futurecast/) plus the as-of tool guard in agent_sdk/. The
agent loop itself is rented (Claude Agent SDK + our llm_adapter) and is exercised by agent_sdk/run.sh,
not here.
"""
from __future__ import annotations

import sys
import re
import tempfile
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


def test_run_group_defaults_to_timestamp_and_can_be_overridden(monkeypatch):
    import config

    monkeypatch.delenv("FUTURECAST_RUN_GROUP", raising=False)
    cfg = config.from_env(run_date="2026-06-30")
    assert re.fullmatch(r"\d{8}-\d{6}", cfg.run_group)

    monkeypatch.setenv("FUTURECAST_RUN_GROUP", "env-group")
    assert config.from_env(run_date="2026-06-30").run_group == "env-group"
    assert config.from_env(run_group="cli-group", run_date="2026-06-30").run_group == "cli-group"


def test_codex_rollout_counts_completed_tool_items_only():
    from codex.run_forecast import _collect_rollout

    raw = "\n".join([
        '{"type":"thread.started","thread_id":"t1"}',
        '{"type":"item.started","item":{"type":"web_search","query":""}}',
        '{"type":"item.completed","item":{"type":"web_search","query":"q"}}',
        '{"type":"item.completed","item":{"type":"reasoning","text":"why"}}',
        '{"type":"item.completed","item":{"type":"agent_message","text":"final \\\\boxed{B}"}}',
        '{"type":"turn.completed","usage":{"input_tokens":1}}',
    ])
    parsed = _collect_rollout(raw)
    assert parsed["session_id"] == "t1"
    assert parsed["tool_use_count"] == 1
    assert parsed["thinking_blocks"] == 1
    assert parsed["reasoning_summary"] == "why"
    assert parsed["final_text"] == "final \\boxed{B}"


def test_forecast_skills_are_valid_and_sync_preserves_system_dir(monkeypatch):
    import sync_skills

    source_skills = sorted((Path(sync_skills.HERE) / "skills").glob("*/SKILL.md"))
    names = []
    for skill_md in source_skills:
        text = skill_md.read_text(encoding="utf-8")
        assert text.startswith("---\n")
        frontmatter = text.split("---", 2)[1]
        name_match = re.search(r"^name:\s*([a-z0-9-]+)\s*$", frontmatter, re.MULTILINE)
        description_match = re.search(r"^description:\s*(.+)$", frontmatter, re.MULTILINE)
        assert name_match, skill_md
        assert description_match, skill_md
        name = name_match.group(1)
        assert name == skill_md.parent.name
        assert len(description_match.group(1).strip()) > 40
        names.append(name)
    assert "as-of-research" in names
    assert "numeric-series" in names
    assert "stock-market" in names
    assert "calibration" in names
    assert "futurecast-core-forecasting" not in names
    assert "futurecast-election-polling" not in names
    assert all(not name.startswith(("futurecast-", "playbook-")) for name in names)

    with tempfile.TemporaryDirectory() as td:
        target = Path(td)
        (target / ".system").mkdir()
        (target / ".system" / "KEEP").write_text("system", encoding="utf-8")
        (target / "stock-market").mkdir()
        (target / "stock-market" / "SKILL.md").write_text("stale", encoding="utf-8")
        (target / "futurecast-old").mkdir()
        (target / "futurecast-old" / "SKILL.md").write_text("stale", encoding="utf-8")
        (target / "playbook-old").mkdir()
        (target / "playbook-old" / "SKILL.md").write_text("stale", encoding="utf-8")
        copied = sync_skills.sync_to(target)
        assert sorted(copied) == names
        assert (target / ".system" / "KEEP").read_text(encoding="utf-8") == "system"
        assert not (target / "futurecast-old").exists()
        assert not (target / "playbook-old").exists()
        assert (target / "stock-market" / "SKILL.md").is_file()
        for name in names:
            assert (target / name / "SKILL.md").is_file()

    with tempfile.TemporaryDirectory() as td:
        plugin_dir = Path(td) / "forecast-skills"
        legacy_plugin_dir = Path(td) / "futurecast-skills"
        legacy_dir = Path(td) / "legacy-skills"
        legacy_plugin_dir.mkdir()
        monkeypatch.setattr(sync_skills, "CLAUDE_PLUGIN_DIR", plugin_dir)
        monkeypatch.setattr(sync_skills, "CLAUDE_TARGET", plugin_dir / "skills")
        monkeypatch.setattr(sync_skills, "CLAUDE_LEGACY_PLUGIN_DIRS", (legacy_plugin_dir,))
        monkeypatch.setattr(sync_skills, "CLAUDE_LEGACY_TARGET", legacy_dir)
        copied = sync_skills.sync_claude()
        assert sorted(copied) == names
        assert (plugin_dir / ".claude-plugin" / "plugin.json").is_file()
        assert not legacy_plugin_dir.exists()
        for name in names:
            assert (plugin_dir / "skills" / name / "SKILL.md").is_file()


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
