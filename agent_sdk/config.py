"""Single typed surface for one forecast RUN's parameters.

These are loop / tool / guard knobs — NOT forecasting cognition (that lives in the playbook).
Design (scientific + cheap to sweep):

  ONE default per knob lives here  →  an ENV var overrides it  →  an explicit CLI flag overrides env.

ENV is the source of truth because the run spans TWO processes: the runner+tools and the separate
`llm_adapter` (started by run.sh). Both call `from_env()` and read the same environment, so a knob
set once (in run.sh, a shell, or a sweep script) reaches every process. `config_summary()` is logged
at run start so every rollout records the exact parameters it was produced with.

To sweep a parameter, set its env var — e.g.:
    FUTURECAST_MAX_TURNS=8 FUTURECAST_ASOF_SCREEN=off bash agent_sdk/run.sh --model gpt-5.5 --tools ...
"""
from __future__ import annotations

import os
from dataclasses import dataclass, fields, replace

# All new runs land here unless overridden (FUTURECAST_RUN_GROUP).
DEFAULT_RUN_GROUP = "futureworld-0629"

# field name -> env var that overrides it
ENV = {
    "model": "FUTURECAST_MODEL",
    "reasoning_effort": "FUTURECAST_REASONING_EFFORT",
    "max_tokens": "FUTURECAST_MAX_TOKENS",
    "max_turns": "FUTURECAST_MAX_TURNS",
    "thinking_budget": "FUTURECAST_THINKING_BUDGET",
    "run_group": "FUTURECAST_RUN_GROUP",
    "asof_screen": "FUTURECAST_ASOF_SCREEN",
    "return_budget": "FUTURECAST_RETURN_BUDGET",
    "extract_input_cap": "FUTURECAST_EXTRACT_INPUT_CAP",
}

_ASOF_MODES = {"off", "loose", "strict"}


@dataclass(frozen=True)
class RunConfig:
    # --- model routing (read by the adapter process) ---
    model: str = "glm-5"                 # gateway model; apihy glm/qwen/deepseek or haoxiang gpt-*
    reasoning_effort: str = "high"       # low | medium | high  (upstream reasoning.effort)
    max_tokens: int = 8192               # per-turn completion cap

    # --- agent loop (read by the runner process) ---
    max_turns: int = 30                  # agent turns when --tools (knowledge-only is capped at 3)
    thinking_budget: int = 8000          # Anthropic extended-thinking budget_tokens
    run_group: str = DEFAULT_RUN_GROUP   # output dir: log/<run_group>/<task>-<model>[-tools]/

    # --- as-of guard at the tool boundary (read by the tools) ---
    asof_screen: str = "loose"           # off | loose | strict  (the dedicated screening model)

    # --- content reduction in read_webpage (read by the tools) ---
    return_budget: int = 30000           # return a fetched page untouched up to this many chars
    extract_input_cap: int = 45000       # max chars fed to the cheap extractor (window first if larger)

    def __post_init__(self):
        if self.asof_screen not in _ASOF_MODES:
            raise ValueError(f"asof_screen must be one of {_ASOF_MODES}, got {self.asof_screen!r}")


def from_env(**cli_overrides) -> RunConfig:
    """Build a config: defaults <- env vars (ENV) <- explicit CLI overrides (non-None only)."""
    base = RunConfig()
    env_vals: dict = {}
    for f in fields(base):
        raw = os.environ.get(ENV[f.name])
        if raw is None or raw == "":
            continue
        cur = getattr(base, f.name)
        env_vals[f.name] = int(raw) if isinstance(cur, int) else raw
    cfg = replace(base, **env_vals)
    cfg = replace(cfg, **{k: v for k, v in cli_overrides.items() if v is not None})
    return cfg


def export_env(cfg: RunConfig) -> None:
    """Push the resolved config back into os.environ so in-process tools + child reads agree."""
    for name, env in ENV.items():
        os.environ[env] = str(getattr(cfg, name))


def config_summary(cfg: RunConfig) -> str:
    return (f"model={cfg.model} effort={cfg.reasoning_effort} max_tokens={cfg.max_tokens} "
            f"max_turns={cfg.max_turns} thinking={cfg.thinking_budget} run_group={cfg.run_group} "
            f"asof_screen={cfg.asof_screen} return_budget={cfg.return_budget}")
