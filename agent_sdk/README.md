# agent_sdk/ — the owned run harness (futurecast's analog of galaxy `pipeline/`)

Run the standard Claude-Code agent **from this repo's own code**, on a chosen cheap gateway model,
with the LLM-routing and tool layers fully OURS. No Claude tokens.

```
agent_sdk/
  llm_adapter.py     # OUR Anthropic /v1/messages endpoint, backed by futurecast/llm (replaces ccr)
  tools_mcp.py       # Serper/Jina/Exa MCP tools: as-of guard + Claude-Code-style WebFetch extraction
  run_forecast.py    # Agent-SDK runner: load a FutureWorld question, capture thinking, write log/
  run.sh             # fixed entry: start the adapter, run the agent
  ccr_home/          # the claude CLI's HOME (transcripts land here)            [gitignore]
  claude-code-router/# legacy vendored ccr — no longer used (adapter replaced it) [gitignore]
```

## What we own vs rent (the project thesis)
- **Rent, unchanged:** the Agent SDK harness — context management, planning, memory, the agent loop.
  The claude CLI still speaks the Anthropic API; we do not touch it.
- **Own:** the **model-routing layer** (`llm_adapter.py`) and the **tools** (`tools_mcp.py`). This is
  where LLM-client usage and tool feedback are made explicit and controllable.

## The adapter (why it replaced claude-code-router)
`llm_adapter.py` is a minimal Starlette server exposing `POST /v1/messages`. The claude CLI points
`ANTHROPIC_BASE_URL` at it; it translates Anthropic⇄OpenAI and calls our `futurecast/llm` clients:

```
Agent SDK → claude CLI → ANTHROPIC_BASE_URL=127.0.0.1:3456 → llm_adapter (ours)
    gpt-5.5 → GPTSub2APIClient     (haoxiang Responses API: reasoning summary + tools)
    glm-5   → OpenRouterNewAPIClient (apihy chat/completions: reasoning_content + tools)
```
Each turn is built fully, then replayed as buffered Anthropic SSE (thinking → text → tool_use).
We switched off ccr 2.0.0 because it (a) duplicated glm tool-call args under thinking and (b) never
surfaced reasoning; the adapter fixes both — glm reasoning + clean tools always, gpt reasoning when
haoxiang's Responses API exposes a summary (intermittent upstream). Model is chosen by `--model`
(exported as `FUTURECAST_MODEL`), not by the dummy Anthropic `model` field.

## Run
```bash
bash agent_sdk/run.sh --model glm-5  --tools                 # glm-5, tools, reasoning in rollout
bash agent_sdk/run.sh --model gpt-5.5 --tools --task-index 4 # gpt-5.5 on a chosen FutureWorld question
```
`run.sh` starts the adapter on :3456, sets `HOME=ccr_home` (the CLI writes its transcript there),
then runs `run_forecast.py`, which loads a question from `tasks/`, enforces the per-question as-of
at the tool boundary, and writes `log/<group>/<task>-<model>[-tools]/{rollout.jsonl, result.json}`.

## Tools (`tools_mcp.py`)
`web_search` (Serper, paginated+dedup, as-of guarded), `read_webpage` (Jina reader — **no blind
truncation**: small pages whole, large pages reduced to instruction-relevant facts via a cheap
extractor, Claude-Code-style), `exa_search` (neural, optional). Plus local `Bash/Read/Edit/Write`.
The as-of guard (search date-cap + target-date/post-cutoff redaction) is best-effort and secondary —
future-prediction questions generally have no leakable answer; it mainly matters for past-dated test
questions.
