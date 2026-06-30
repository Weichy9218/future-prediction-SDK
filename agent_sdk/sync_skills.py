"""Sync tracked forecast skills into Claude Code and Codex CLI homes."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "skills"
CLAUDE_PLUGIN_DIR = HERE / "cli_home" / ".claude" / "plugins" / "forecast-skills"
CLAUDE_TARGET = CLAUDE_PLUGIN_DIR / "skills"
CLAUDE_LEGACY_PLUGIN_DIRS = (
    HERE / "cli_home" / ".claude" / "plugins" / "futurecast-skills",
)
CLAUDE_LEGACY_TARGET = HERE / "cli_home" / ".claude" / "skills"
CODEX_TARGET = HERE / "codex" / "cli_home" / "skills"
LEGACY_MANAGED_PREFIXES = ("futurecast-", "playbook-")


def _iter_source_skills() -> list[Path]:
    if not SOURCE.exists():
        return []
    return sorted(p for p in SOURCE.iterdir() if (p / "SKILL.md").is_file())


def skill_names() -> list[str]:
    return [p.name for p in _iter_source_skills()]


def _clear_managed(target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    managed_names = set(skill_names())
    for child in target.iterdir():
        if child.is_dir() and (
            child.name in managed_names or child.name.startswith(LEGACY_MANAGED_PREFIXES)
        ):
            shutil.rmtree(child)


def sync_to(target: Path) -> list[str]:
    """Replace managed forecast skills in target and return copied names."""
    _clear_managed(target)
    copied: list[str] = []
    for skill in _iter_source_skills():
        shutil.copytree(skill, target / skill.name, dirs_exist_ok=True)
        copied.append(skill.name)
    return copied


def _write_claude_plugin_manifest() -> None:
    manifest_dir = CLAUDE_PLUGIN_DIR / ".claude-plugin"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "name": "forecast-skills",
        "description": "Forecasting skills shared by Claude Code and Codex backends",
        "version": "0.1.0",
        "author": {"name": "futurecast"},
    }
    (manifest_dir / "plugin.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def sync_claude() -> list[str]:
    """Sync skills into a Claude Code local plugin directory."""
    for legacy_plugin_dir in CLAUDE_LEGACY_PLUGIN_DIRS:
        if legacy_plugin_dir.exists():
            shutil.rmtree(legacy_plugin_dir)
    if CLAUDE_PLUGIN_DIR.exists():
        shutil.rmtree(CLAUDE_PLUGIN_DIR)
    copied = sync_to(CLAUDE_TARGET)
    _write_claude_plugin_manifest()
    if CLAUDE_LEGACY_TARGET.exists():
        _clear_managed(CLAUDE_LEGACY_TARGET)
    return copied


def sync_codex() -> list[str]:
    """Sync skills into CODEX_HOME/skills while preserving .system skills."""
    return sync_to(CODEX_TARGET)


def sync_all(*, codex_only: bool = False, claude_only: bool = False) -> dict[str, list[str]]:
    targets = {}
    if not codex_only:
        targets["claude_code"] = sync_claude
    if not claude_only:
        targets["codex"] = sync_codex
    return {name: sync_fn() for name, sync_fn in targets.items()}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--codex-only", action="store_true")
    ap.add_argument("--claude-only", action="store_true")
    args = ap.parse_args()
    if args.codex_only and args.claude_only:
        raise SystemExit("--codex-only and --claude-only are mutually exclusive")
    result = sync_all(codex_only=args.codex_only, claude_only=args.claude_only)
    for target, names in result.items():
        print(f"{target}: {', '.join(names) if names else '(none)'}")


if __name__ == "__main__":
    main()
