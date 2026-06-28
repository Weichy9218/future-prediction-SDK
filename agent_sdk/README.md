# agent_sdk/ — the owned Agent run harness (futurecast's analog of galaxy `pipeline/`)

Everything needed to run the standard ccr / Claude-Code agent **from this repo's own code**,
on a chosen cheap gateway model, with full control to relocate and modify it. No global install,
no Claude tokens.

## What's vendored / generated here
```
agent_sdk/
  claude-code-router/       # ccr code, copied from the npm package (bundled dist, zero npm deps)  [gitignore]
  ccr_home/                 # LOCAL ccr state + the live config (real keys, generated per run)     [gitignore]
  ccr_config.template.json  # single source of truth: Providers (apihy + haoxiang) with ${ENV} keys
  gen_ccr_config.py         # render template -> live config + point ccr Router at the chosen model
  tools_mcp.py              # Serper/Jina/Exa MCP tools + the as-of guard at the tool boundary
  run_forecast.py           # the Agent-SDK runner (select model, enforce as-of, write standardized log)
  run.sh                    # fixed entry point
```

## Run (one command, all local)
```bash
bash agent_sdk/run.sh                          # glm-5, knowledge-only
bash agent_sdk/run.sh --tools                  # glm-5, tool-enabled multi-step rollout
bash agent_sdk/run.sh --model gpt-5.5 --tools  # gpt-5.5 (haoxiang) through the SAME agent + tools
```
`run.sh` sets `HOME=agent_sdk/ccr_home` (the **vendored** ccr reads the **local** config; nothing
in your real `~` is touched), regenerates the live config for the chosen model, starts
`node claude-code-router/dist/cli.js`, then runs the agent.

## The routing chain
```
Agent SDK (claude_agent_sdk) → claude CLI → ANTHROPIC_BASE_URL=127.0.0.1:3456
  → vendored ccr (local config) → gateway     # no Claude tokens
      apihy    https://zgc.apihy.com/v1        glm-5 / glm-5.1 / qwen3-235b / deepseek-v4-flash
      haoxiang https://ie-crs.haoxiang.ai/v1   gpt-5.5 / gpt-5.4 / gpt-5.4-mini
```
The model is chosen by `--model` (which `gen_ccr_config.py` writes into ccr's `Router`); to add a
provider/model, edit `ccr_config.template.json`.

## Tools: your keys, not Anthropic's built-ins
Built-in `WebSearch`/`WebFetch` do **not** execute when routed off-Claude, so they are disallowed.
`--tools` exposes in-process MCP tools backed by **your** keys — `web_search` (Serper, paginated +
dedup), `read_webpage` (Jina reader, robust + size-capped), `exa_search` (Exa neural, optional) —
plus the local `Bash/Read/Edit/Write` CLI tools (which DO execute off-Claude). Verified: both
glm-5 and gpt-5.5 call these tools (11 tool_use calls each on the hog question).

**as-of is enforced here, mechanically.** `run_forecast.py` exports `FUTURECAST_AS_OF`; the tools
cap search results at the cutoff, redact post-cutoff dates embedded in snippets, and block pages
published after the cutoff. See the README's "as-of guard" section.

## Output
`run_forecast.py` writes a standardized rollout + parsed result:
```
log/<run_group>/<task_id>-<model_short>[-tools]/{rollout.jsonl, result.json}
```
`rollout.jsonl` is the claude CLI's full session transcript (copied out of `ccr_home/.claude/...`);
`result.json` is the parsed `{answer, point, low, high, anchor, uncertainty, confidence, sources}`.

> Reasoning note (verified): ccr translates via `/chat/completions`, which carries no reasoning for
> gpt and whose `reasoning_content` for glm ccr does not forward — so **no model's reasoning lands
> in the rollout**. A hidden reasoning summary requires the Responses API (`futurecast/llm/`),
> outside the agent loop.
