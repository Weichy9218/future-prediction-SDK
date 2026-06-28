# config/ — run / model / tool configuration (mirrors galaxy-selfevolve/config)

A **run** yaml is the entry point; it selects a **model backend** and a **toolset** by name.

```
config/
  agent/
    default.yaml        # composition root: defaults [profile, llm, tool]
    profile/forecast.yaml
    llm/                # one per model backend
      gpt_sub2api.yaml  # gpt-5.5 (haoxiang Responses API)
      apihy_glm5.yaml   # glm-5  (apihy Chat Completions, cheap default)
    tool/default.yaml   # toolsets (the enable switch) + tool-llm routes + provider keys
  run/
    futureworld_hog_gpt55.yaml   # example run
```

## Resolution chain (run → agent → llm → client_args)
`run/<name>.yaml` `agent` block names `llm:` and `tool:` + `toolset:`. The llm name loads
`agent/llm/<name>.yaml` → `client` (registry name in `futurecast/llm`) + `client_args`
(constructor kwargs; `*_env` keys name **.env vars**, never literal secrets). A model is swapped
by changing one line: `agent.llm: gpt_sub2api` ↔ `apihy_glm5`.

## How tool availability is controlled (the answer to "should config control tools?")
**Yes — via `tool/default.yaml` `toolsets.<name>`**, an explicit allow-list of tool names. The
runner exposes to the model ONLY the tools in the selected toolset (`agent.toolset:`). There is
no per-tool flag; presence in the list = enabled. `no_tools` = knowledge-only; `main` =
web_search + read_webpage + execute_python_code.

## Do tools need EXA/JINA/SERPER like core/tools, or the agent's own search API?
**They use the third-party APIs directly — same as galaxy core/tools, NOT a provider's built-in
WebSearch.** Keys come from `.env`: `SERPER_API_KEY` (web_search/Serper), `JINA_API_KEY`
(read_webpage/Jina r.jina.ai), `EXA_API_KEY` (optional neural search). The Agent-SDK path proves
this: `agent_sdk/tools_mcp.py` implements `web_search`/`read_webpage` on your Serper/Jina keys and
the runner **disallows** the built-in `WebSearch`/`WebFetch`. So you are NOT forced to use the
agent's own search API — your keys drive the tools. `wind` and other special tools would be added
the same way (a tool module + a key in `.env` + a name in a toolset).
