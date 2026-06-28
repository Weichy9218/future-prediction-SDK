"""Generate the live ccr config from the committed template.

The template (`ccr_config.template.json`) is the single source of truth: it lists the
Providers (apihy for glm/qwen, haoxiang for gpt) with `${ENV_VAR}` placeholders for keys.
This script substitutes the keys from the environment and points every Router category at the
requested model, then writes the live config into the local ccr home. This removes the
template-vs-live drift (the live file is gitignored; only the redacted template is committed).

Usage:
  python gen_ccr_config.py <model> <out_config_path>
e.g.
  python gen_ccr_config.py gpt-5.5  ccr_home/.claude-code-router/config.json
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "ccr_config.template.json"


def _resolve_env(obj):
    """Recursively replace ${VAR} occurrences in string leaves with os.environ values."""
    if isinstance(obj, str):
        return re.sub(r"\$\{([A-Za-z0-9_]+)\}", lambda m: os.environ.get(m.group(1), ""), obj)
    if isinstance(obj, list):
        return [_resolve_env(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _resolve_env(v) for k, v in obj.items()}
    return obj


def _provider_for(cfg: dict, model: str) -> str:
    for p in cfg.get("Providers", []):
        if model in (p.get("models") or []):
            return p["name"]
    have = {m for p in cfg.get("Providers", []) for m in (p.get("models") or [])}
    raise SystemExit(f"model {model!r} not in any provider; configured models: {sorted(have)}")


def main(model: str, out_path: str) -> None:
    cfg = _resolve_env(json.loads(TEMPLATE.read_text(encoding="utf-8")))
    route = f"{_provider_for(cfg, model)},{model}"
    cfg["Router"] = {k: route for k in ("default", "background", "think", "longContext", "webSearch")}
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"# ccr config written: {out}  (route={route})")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python gen_ccr_config.py <model> <out_config_path>")
    main(sys.argv[1], sys.argv[2])
