# agent_sdk/ — the owned run harness (futurecast's analog of galaxy `pipeline/`)

Run a standard Claude-Code agent **from this repo's own code**, on a chosen cheap gateway model,
with the LLM-routing and tool layers fully OURS. No Claude tokens spent.

```
agent_sdk/
  llm_adapter.py   # OUR Anthropic /v1/messages endpoint, backed by futurecast/llm
  tools_mcp.py     # Serper/Jina/Exa MCP tools + as-of guard (regex + dedicated screening model)
  run_forecast.py  # Agent-SDK runner: load a question, pick playbook, capture thinking, write log/
  config.py        # one typed surface for all run params (defaults <- env FUTURECAST_* <- CLI)
  run.sh           # fixed entry: start the adapter, run the agent
  cli_home/        # the claude CLI's HOME (config/state + transcripts land here)   [gitignore]
```

## What we own vs rent (the project thesis)
- **Rent, unchanged:** the Agent SDK harness — context management, planning, memory, the agent loop.
  The `claude` CLI still speaks the Anthropic API; we do not touch the loop.
- **Own:** the **model-routing layer** (`llm_adapter.py`), the **tools** (`tools_mcp.py`), and the
  **prompt** (`futurecast/playbook/`). This is where LLM-client usage, tool feedback, and forecasting
  cognition are made explicit and controllable.

## The adapter
`llm_adapter.py` is a minimal Starlette server exposing `POST /v1/messages`. The claude CLI points
`ANTHROPIC_BASE_URL` at it; it translates Anthropic⇄OpenAI and calls our `futurecast/llm` clients:

```
Agent SDK → claude CLI → ANTHROPIC_BASE_URL=127.0.0.1:3456 → llm_adapter (ours)
    gpt-5.5 → GPTSub2APIClient      (haoxiang Responses API: reasoning summary + tools)
    glm-5   → OpenRouterNewAPIClient (apihy chat/completions: reasoning_content + tools)
```
Each turn is built fully, then replayed as buffered Anthropic SSE (thinking → text → tool_use), so
the model's intermediate reasoning lands in the rollout. Model is chosen by `--model` (exported as
`FUTURECAST_MODEL`); reasoning effort by `FUTURECAST_REASONING_EFFORT` (default `high`). The
Anthropic `model` field the CLI sends is an ignored dummy.

The adapter logs `[tool-surface]` (the exact tool-name list) on the first request of each run to
`log/adapter.log` — use it to confirm the surface is the clean official-loop slice, not host noise.

## Run
```bash
bash agent_sdk/run.sh --model glm-5  --tools                              # glm-5, tools, reasoning in rollout
bash agent_sdk/run.sh --model gpt-5.5 --tools \                           # one specific question
     --question-file tasks/2026-07-06_..._question.jsonl --task-index 0
```
`run.sh` starts the adapter on :3456, sets `HOME=cli_home`, unsets proxies (gateways are reached
directly), then runs `run_forecast.py`. The runner loads a question from `tasks/`, picks the
type-matched playbook (A numeric / B event), and enforces the effective as-of at the tool boundary:
`min(target_date - 1 day, run_date)` unless `FUTURECAST_AS_OF` / `--as-of` explicitly overrides it.
It writes `log/<group>/<backend>/<task>-<model>[-tools]/{rollout.jsonl, result.json}` (default
group is the run-start timestamp, `YYYYMMDD-HHMMSS`).

**Run parameters** live in `config.py` (one default each), overridable by env then CLI:
`FUTURECAST_MODEL/REASONING_EFFORT/MAX_TOKENS/MAX_TURNS/THINKING_BUDGET/RUN_GROUP/RUN_DATE/AS_OF/ASOF_SCREEN/…`.
The resolved set is logged as a `config:` line at run start and saved into `result.json`. Sweep by
setting env, e.g. `FUTURECAST_MAX_TURNS=8 FUTURECAST_ASOF_SCREEN=off bash agent_sdk/run.sh …`.

## Tools (`tools_mcp.py`)
- `web_search` (Serper, paginated + dedup, as-of guarded), `read_webpage` (Jina reader — **no blind
  truncation**: small pages whole, large pages reduced to instruction-relevant facts via a cheap
  extractor), `exa_search` (neural, optional).
- **Tool surface:** `ALLOWED` is a representative slice of the official loop
  (`Read/Glob/Grep/Edit/Write/NotebookEdit/Bash/Agent/Skill/Task*`) + our 3 MCP tools.
  `DISALLOWED_BUILTINS` drops Anthropic's off-Claude `WebSearch/WebFetch` and the host harness's
  orchestration noise (cron/worktree/workflow/design-sync/…). `allowed_tools` only gates permission,
  so `disallowed_tools` is what actually shapes what the model sees.
- **as-of guard (two layers):** deterministic regex date-cap + target/post-cutoff redaction, then a
  **dedicated screening model** (qwen3-next-80b) that flags any remaining leaking spans verbatim,
  removed deterministically. Post-cutoff data never reaches the main agent.
