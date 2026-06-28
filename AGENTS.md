# AGENTS.md — futurecast working rules

Successor to `galaxy-selfevolve`. That system's recurring disease (see its
`docs/reflection_v4.md`) was **externalizing "can the model predict?" into a Python state
machine** — a readiness ladder, then an audit tower, then a ForecastFrame/coverage layer —
each cleanup deleting one incarnation and accidentally growing the next. These rules exist to
make that failure mode structurally impossible here.

## Hard guardrails

1. **No Python cognition state machine.** No `readiness` / `coverage` / typed `ForecastFrame`
   / pillar reducers deciding whether/what the model can predict. Forecasting cognition lives
   **only** in the prompt (`playbook/`), the model context, and the experience library. A typed
   "forecastability" object is a regression.
2. **One source of truth, zero audit projections.** Keep at most a single serialized run record
   + run telemetry. Do **not** add replay engines, trace auditors, manifests, or a matched-hash
   invariant. (The hash invariant is what made the old repo "delete-proof" — without it, refactor
   never degenerates into merge.)
3. **Core knows no specific source or task.** No `wta_*` / `boc_*` / `dongchedi_*` / `woshi_*`
   names in `futurecast/`. Site/series specifics go into `experience/` skills, disclosed on
   demand — never preloaded (that would leak across questions and kill generality).
4. **The invariant is "scorable", not "self-consistent".** Every change is judged by whether it
   moves Brier / numeric error / calibration — not by whether some field got filled. Use the
   `verl-tool-future` scorer; don't reinvent metrics.
5. **as-of is the only trust we don't hand to the prompt.** Post-cutoff data must be blocked at
   the tool boundary (`guard/as_of.py`), mechanically. Everything else is the model's job.

## Boundaries of ownership (what we control vs rent)

- **Own** (small, ours, ~hundreds of lines): playbook, as-of guard, scorable output, experience
  library, and the run harness (`agent_sdk/`: ccr config generation + tools + runner).
- **Harvest** (generic, well-tested, copied in): `futurecast/llm/` (from core/llm — kept as the
  reasoning-capable direct client; see below); scoring + question collection from `verl-tool-future`.
- **Rent** (don't rebuild): the agent loop machinery (Claude Agent SDK) AND the model routing
  (claude-code-router). A run picks its gateway model via `agent_sdk/gen_ccr_config.py`
  (apihy glm/qwen, haoxiang gpt); the same agent + tool surface serves all of them. There is no
  hand-written Python loop here — it was removed once ccr covered gpt too.

> Reasoning note (verified): ccr routes via `/chat/completions`, which carries `reasoning_content`
> for glm but NOT for gpt. To capture a hidden gpt reasoning *summary* you must use the Responses
> API (`futurecast/llm/`, `summary:auto`) outside the agent loop. The agent rollout still captures
> each model's *visible* reasoning text.

## When adding code, ask
- Does this put forecasting cognition in Python instead of the prompt? → stop (guardrail #1).
- Does this create a second copy/projection of run state? → stop (guardrail #2).
- Does `futurecast/` now mention a specific website/series? → move it to `experience/` (guardrail #3).
