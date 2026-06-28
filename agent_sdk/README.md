# agent_sdk/ — the owned Agent run harness (futurecast's analog of galaxy `pipeline/`)

Everything needed to run the standard ccr / Claude-Code agent **from this repo's own code**,
with full control to relocate and modify it. No global install, no Claude tokens.

## What's vendored here
```
agent_sdk/
  claude-code-router/      # the ccr code, copied from the npm package (bundled dist, zero npm deps)
  ccr_home/                # LOCAL ccr state: .claude-code-router/config.json (apihy glm-5)
  ccr_config.template.json # the same config with the key redacted (for reference)
  tools_mcp.py             # custom web_search (Serper) + read_webpage (Jina) MCP tools — YOUR keys
  run_forecast.py          # the Agent-SDK runner (forecast one question)
  run.sh                   # fixed entry: starts local ccr + runs the forecast
```

## Run (one command, all local)
```bash
./agent_sdk/run.sh           # knowledge-only forecast on glm-5
./agent_sdk/run.sh --tools   # multi-step rollout using the custom Serper/Jina tools
```
`run.sh` sets `HOME=agent_sdk/ccr_home` so the **vendored** ccr reads the **local** config (nothing
in your real `~` is touched), starts `node claude-code-router/dist/cli.js`, then runs the agent.

## The routing chain
```
Agent SDK (claude_agent_sdk) → claude CLI → ANTHROPIC_BASE_URL=127.0.0.1:3456
  → vendored ccr (local config) → apihy https://zgc.apihy.com/v1  model glm-5   # no Claude tokens
```
Swap the model by editing `Router.default` in `ccr_home/.claude-code-router/config.json`
(e.g. `apihy,qwen3-235b-a22b-instruct-2507`).

## Tools: your keys, not Anthropic's built-ins
Built-in `WebSearch`/`WebFetch` do **not** execute when routed off-Claude. So `--tools` uses
`tools_mcp.py` — in-process MCP tools backed by **your** `SERPER_API_KEY` (search) and
`JINA_API_KEY` (read), and the runner **disallows** the built-ins. Verified: glm-5 calls
`mcp__futurecast__web_search` / `mcp__futurecast__read_webpage` and they return real data.
Add more tools (e.g. wind) the same way: a `@tool` in `tools_mcp.py` + a key in `.env`.
TODO: wrap fetch tools with `futurecast/guard/as_of.py` so post-cutoff pages are blocked.

## Rollout transcripts
The CLI writes the full transcript to `$HOME/.claude/projects/<key>/<session>.jsonl`. Under
`run.sh` that is `agent_sdk/ccr_home/.claude/projects/...`; the runner prints the path and copies
captured samples into `../log/agent_sdk/`.
