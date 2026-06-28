# futurecast

A thin forecasting agent for the **FutureWorld / FutureX** benchmarks. It is the clean-room
successor to `galaxy-selfevolve` (see that repo's `docs/reflection_v4.md` for why we rebuilt
rather than refactored): a **provider-agnostic agent loop** plus **four forecasting-specific
pieces**, and nothing else.

## Why forecasting (the research bet)

Prediction is a *harder* problem than most agent tasks, and that is exactly the point. A good
forecast demands more of the agent on every axis at once — **search** (find the right prior),
**modeling** (turn history/market into a prior), **uncertainty estimation**, **probability
calibration**, **reasoning**, and **experience accumulation**. And because the answer does not
exist at inference time, the task is **hard to hack**: you cannot retrieve the label, you can
only forecast it. The series are **micro-random** (day-to-day answer drift) but
**macro-deterministic** (structure emerges over a group of questions), so the optimization
target is *group calibration* (Brier / log-loss), not winning any single question. That
macro-determinism under non-leakable answers is the research value we want an agent to chase.

## Architecture: buy the loop, build the kit

```
question ──► playbook prompt ──►  [ thin loop ]  ──► scorable forecast ──► score (verl-tool-future)
                 (kit #1)         model backend          (kit #3)
                                  + tools + as-of guard (kit #2)
                                          │
                                  experience library (kit #4, on-demand)
```

- `futurecast/loop/agent.py` — the **only** orchestration code (~one screen). observe→act→tool.
- `futurecast/model/` — **pluggable backend** behind one `ModelBackend` protocol:
  - `CoreLLMBackend` (default) — wraps the harvested `core/llm` clients → **cheap models, no Claude tokens**.
  - `ClaudeBackend` (optional) — `anthropic` SDK / Claude Agent SDK, for when you want Claude.
- `futurecast/playbook/` — kit #1: cognition in the **prompt** (A: numeric series, B: events). No state machine.
- `futurecast/guard/as_of.py` — kit #2: the one mechanism-level hook — block post-cutoff data from context.
- `futurecast/io/` — kit #3: `ScorableForecast` schema + submission writer + `score`/`brier` wrappers.
- `futurecast/experience/` — kit #4: question-class notes, retrieved **on demand**, never preloaded.
- `futurecast/llm/` — **harvested** from `galaxy-selfevolve/core/llm` (generic, no task leakage).

## Answers to the three setup questions

**1. Is the Claude Agent SDK local / controllable / searchable?** Yes. `claude-agent-sdk`
(v0.2.110) is installed into `.venv`; its source sits at
`.venv/lib/python3.12/site-packages/claude_agent_sdk/` — fully greppable, you don't have to
modify it. `anthropic` (v0.112) is also local. See `agent_sdk/`.

**2. Can we use the `core/llm` clients / cheap models?** Yes, and it's the default. The harvested
clients (`gpt_sub2api` → haoxiang; `openrouter_newapi` → OpenRouter / apihy qwen·glm·kimi·deepseek)
already do OpenAI-compatible **tool-calling**, so the loop runs on cheap models with **zero Claude
tokens**. Keys reuse the `galaxy-selfevolve/.env` conventions.

**3. Scoring & question collection.** Reuse **verl-tool-future**
(https://github.com/ZhixinHan/verl-tool-future): `benchmark.scoring.score_submission_file` +
`rewards/brier.py` replace the missing `benchmark_merge_v8`; `vtf benchmark create` (see the
GLM repo's `create_futureworld_benchmark.sh`) generates new questions/gold. Wire it via
`futurecast/io/scoring.py`.

## Running the Agent SDK on a cheap (non-Claude) model

The Claude Agent SDK speaks the Anthropic API; `claude-code-router` translates that to the
apihy OpenAI-compatible gateway and serves **glm-5**:

```
Agent SDK → claude CLI → ANTHROPIC_BASE_URL=http://127.0.0.1:3456 (claude-code-router)
          → apihy https://zgc.apihy.com/v1  model glm-5     # no Claude tokens
```

Setup + run:
```bash
uv venv && uv pip install claude-agent-sdk anthropic           # SDK local + controllable
# router config (apihy glm-5) is at ~/.claude-code-router/config.json; template in agent_sdk/
ccr start
.venv/bin/python agent_sdk/run_forecast.py            # one forecast question, glm-5
.venv/bin/python agent_sdk/run_forecast.py --tools    # tool-enabled (multi-step) rollout
```

The CLI writes the **full rollout transcript** to
`~/.claude/projects/<project-key>/<session-id>.jsonl` (same format as the old
`main_agent.jsonl`); `run_forecast.py` prints its path at the end. See `agent_sdk/README.md`.

## Status

Skeleton + harvested assets + a working Agent-SDK-on-glm-5 smoke run. Not yet end-to-end
scored — next: wire tools (search/fetch) + as-of guard into the loop, then batch-run and score
FutureWorld with `verl-tool-future`. The first reproducible measurement (knowledge-only floor)
lives in `experiments/baseline_floor_0501/`.
