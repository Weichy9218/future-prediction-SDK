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
  library, the run harness (`agent_sdk/`: the LLM adapter + tools + runner), and — deliberately —
  the **model-routing layer** (`agent_sdk/llm_adapter.py`, backed by `futurecast/llm/`).
- **Harvest** (generic, well-tested, copied in): `futurecast/llm/` (from core/llm — now the backend
  of the adapter); scoring + question collection from `verl-tool-future`.
- **Rent, unchanged** (don't rebuild): the agent **harness** — context management, planning, memory,
  the agent loop (Claude Agent SDK / claude CLI). We do NOT touch it; a run picks its gateway model
  via `--model` and the SAME agent + tool surface serves all models. (Owning model routing is the
  point; the harness stays rented.)

> Reasoning capture (verified, see `docs/analysis_phase2.md`–`phase4.md`): the adapter replays
> each turn as Anthropic SSE incl. `thinking` blocks built from the client's `reasoning_summary`, so
> the model's intermediate reasoning lands in the rollout. glm exposes reasoning reliably with clean
> tool-call args; gpt/haoxiang exposes a reasoning summary via the Responses API (captured when
> present, reliable at effort=high).

## When adding code, ask
- Does this put forecasting cognition in Python instead of the prompt? → stop (guardrail #1).
- Does this create a second copy/projection of run state? → stop (guardrail #2).
- Does `futurecast/` now mention a specific website/series? → move it to `experience/` (guardrail #3).
