# NEXT SESSION — futurecast handoff prompt

> Paste this whole file as the opening prompt of the new session. It encodes the background,
> the verified facts (so you don't re-explore), the architecture decision, and the task list.

You are continuing work on **`/Users/weichy/Desktop/Doing-Right-Things/FutureX/papers/futurecast`**,
a clean-room forecasting-agent repo for the **FutureWorld / FutureX** benchmarks. Read this fully
before acting. Do NOT re-explore what is already established below.

---

## 0. What this project is (the one idea)

Use a **standard general agent (Claude Code / ccr / Codex / Claude Agent SDK)** to solve
*future-prediction* questions, and control everything **outside** that agent — the **LLM choice,
tools, io (scorable output), skills/experience, and prompt/playbook**. Do **NOT** rebuild the
agent loop (that was the mistake of the predecessor repo `galaxy-selfevolve-runtime-cleanup`,
which kept re-growing a Python "can-the-model-predict" state machine). Keep only the
*future-prediction insight*, not the agent plumbing.

**Background to read first (core conclusions, don't re-derive):**
- `galaxy-selfevolve-runtime-cleanup/docs/reflection_v4.md` — why we rebuilt instead of refactored;
  the disease was externalizing prediction cognition into Python state; the cure = rent the loop +
  add only 4 pieces (playbook / as-of guard / scorable output / experience library).
- Prior session transcript with the rollout analysis + decisions:
  `/Users/weichy/.claude/projects/-Users-weichy-Desktop-Doing-Right-Things-FutureX-papers-galaxy-selfevolve-runtime-cleanup/01b9fd76-399b-42b7-ade9-3f8e5ca2bbbb.jsonl`
- This repo's `README.md`, `AGENTS.md` (guardrails), `config/README.md`, `agent_sdk/README.md`.

**The research bet (keep in the prompt/README):** prediction is harder than typical agent tasks —
it stresses search, modeling, uncertainty estimation, probability calibration, reasoning, and
experience accumulation at once; answers don't leak so it's hard to hack; micro-random but
macro-deterministic → optimize **group calibration (Brier/log-loss)**, not single answers.

---

## 1. Current state (already built & WORKING — verify, don't rebuild)

Two model-access paths exist today (this duplication is the thing to clean up — see §3):

- **Path A — Agent SDK + ccr (the rented loop).** `claude_agent_sdk` (v0.2.110, installed in
  `.venv`) → spawns the `claude` CLI → `ANTHROPIC_BASE_URL=127.0.0.1:3456` → **vendored** ccr at
  `agent_sdk/claude-code-router/` (bundled `dist/cli.js`, zero npm deps) → **apihy** gateway
  (`https://zgc.apihy.com/v1`) model **glm-5**. Runs fully local via `./agent_sdk/run.sh [--tools]`
  (`HOME=agent_sdk/ccr_home` so it reads the local ccr config, not `~`). Produces real
  Claude-Code rollout `.jsonl`. **No Claude tokens used.**
- **Path B — futurecast/llm + a thin hand-written loop.** `futurecast/model/coremllm_backend.py`
  wraps the harvested `futurecast/llm/` clients (`gpt_sub2api`→haoxiang `https://ie-crs.haoxiang.ai/v1`
  gpt-5.5; `openrouter_newapi`→apihy). `scripts/run_forecast_corellm.py` ran **gpt-5.5** on the
  hog question. This path RE-IMPLEMENTS the agent loop = the wheel we said not to rebuild.

**Demonstrated runs (trajectories in `log/`):**
- `log/agent_sdk/glm5_notools.jsonl` — glm-5 single-turn (Agent SDK).
- `log/agent_sdk/glm5_tools_serper_multistep.jsonl` — glm-5 multi-step, **62 tool_use** via custom
  Serper/Jina tools that REALLY execute (`agent_sdk/tools_mcp.py`).
- `log/corellm/gpt55_20260628_120620.jsonl` — gpt-5.5 via core/llm, **no tools** (by design).
- `log/experiments/baseline_floor_0501/` — the knowledge-only floor (median 45% rel err).

**Config (mirrors galaxy, leaner):** `config/agent/{default,llm/*,tool/default,profile}.yaml`,
`config/run/*.yaml`. Tool enable = `tool/default.yaml` `toolsets.<name>` allow-list.

**Keys:** `.env` (gitignored, copied from galaxy). apihy per-model keys (`apihy_API_KEY_glm`…),
`GPT_sub2api_apikey`/`GPT_sub2api_URL`, `SERPER_API_KEY`, `JINA_API_KEY`, `EXA_API_KEY`.
**haoxiang & apihy are reached DIRECTLY — drop SOCKS/HTTP proxy** (the openai client otherwise
reads `ALL_PROXY` from env and fails with a socks error; `pop` the proxy vars before constructing).

---

## 2. Verified facts (so you DON'T re-investigate)

1. **reasoning/thinking summary is ALREADY captured** at the client layer:
   `futurecast/llm/base.py:39` `LLMResponse.reasoning_summary`; populated in
   `futurecast/llm/openai_client.py:423` via the Responses API (`summary:auto`). **The bug is that
   `CoreLLMBackend.chat()` (`futurecast/model/coremllm_backend.py`) DROPS it** — it returns only
   `content` + `tool_calls`. Fix = forward `resp.reasoning_summary` and write it into the trajectory.
2. **"gpt doesn't call tools" root cause:** `scripts/run_forecast_corellm.py` calls
   `backend.chat(messages, tools=None)` ONCE — no tools, no loop. Not a client bug. To make gpt use
   tools, run it through an agent loop **with tools** (preferably Path A; see §3).
3. **Built-in `WebSearch`/`WebFetch` are Anthropic SERVER-SIDE tools** — they execute on Anthropic's
   API and need the Claude API. They are not local code to copy, and there is no non-Anthropic API
   for them. When routed to glm/gpt they DO NOT execute. → **You cannot reuse them off-Claude.** The
   correct path is to build robust **Serper/Jina/Exa** equivalents (improve on the toy versions in
   `agent_sdk/tools_mcp.py`). `WebFetch≈Jina reader`, `WebSearch≈Serper + Exa neural`.
4. **`Bash`/`Read`/`Edit`/`Write` are LOCAL CLI tools** (executed by the claude CLI locally) → they
   work off-Claude and **must be kept enabled** in the Agent SDK path.
5. **ccr is a 2.7M bundled single file, zero npm deps** — vendoring + `node dist/cli.js` works.
   Config path is `$HOME/.claude-code-router/config.json`; redirect `HOME` to use a local one.

---

## 3. Architecture decision to implement (resolves the "agent_sdk vs futurecast is messy" worry)

**Converge on Path A. Demote/remove Path B.** Concretely:

- **`agent_sdk/` = the rented agent substrate** (ccr + Agent SDK runner + custom tools). Choose the
  model purely via ccr's `Router`/`Providers` config. **Add a haoxiang provider to the ccr config**
  so **gpt-5.5 also runs through the Agent SDK** with the same tool surface (Bash/Read/Edit/Write +
  Serper/Jina/Exa). This is what fixes "gpt doesn't call tools" the right way (no second loop).
- **`futurecast/` = the prediction control layer ONLY**: `playbook/` (prompt), `guard/as_of.py`,
  `io/` (scorable schema + scoring via verl-tool-future), `experience/` (skills), `data/`→`tasks/`,
  `config/`. **Remove the wheel-reinvention**: `futurecast/model/coremllm_backend.py` + `loop/agent.py`
  (the hand-written loop) should go away once Path A covers gpt too.
- **`futurecast/llm/` decision (reasoning tradeoff):** keep it ONLY if you need (a) direct non-agent
  calls (e.g. a cheap tool-side summarizer) or (b) reasoning_summary that ccr may drop. FIRST CHECK
  whether ccr surfaces gpt/glm reasoning in the transcript; if yes, `futurecast/llm/` can shrink to
  a tiny tool-side client or be removed. If reasoning matters and ccr drops it, keep a thin direct
  client just for that. Do not maintain two full loops.

> Net: don't deep-merge ccr and futurecast/llm into one blob; instead let **ccr own all model
> routing** (gpt via haoxiang, glm/qwen via apihy, claude via its own), and keep futurecast/llm
> minimal or gone. This removes the duplication and the code bloat you flagged.

---

## 4. TASKS (priority order)

1. **Converge model routing on ccr (Path A).** Add a haoxiang `gpt_sub2api` provider to the ccr
   config (base `https://ie-crs.haoxiang.ai/v1`, key `GPT_sub2api_apikey`, models `gpt-5.5`,
   `gpt-5.4`…); add a Router alias so a run can pick gpt-5.5 or glm-5. Run the SAME hog question on
   **gpt-5.5 through the Agent SDK WITH tools** → this both fixes "gpt no tools" and gives a fair
   gpt-vs-glm comparison with tools. Keep `Bash/Read/Edit/Write` enabled; disallow `WebSearch/WebFetch`.
2. **Reasoning/thinking summary must be preserved in gpt output.** First check if ccr passes gpt
   reasoning into the transcript. If not, ensure it is captured: `LLMResponse.reasoning_summary`
   already exists (§2.1); forward it in any direct-call path and write it into the saved trajectory.
3. **Upgrade the search/fetch tools** in `agent_sdk/tools_mcp.py` to be at least as capable as the
   built-ins: Serper (search, with pagination + result dedup), Jina reader (fetch, robust extraction
   + size limits), optional Exa neural search. **Wire `futurecast/guard/as_of.py` into these tools**
   so any page/result dated after the question cutoff is blocked (the current `--tools` run leaks —
   glm-5 searched *today* for the realized value). This as-of guard on tools is the #1 correctness fix.
4. **Standardize `log/` layout.** One subfolder per run/question-group, then per model, e.g.
   `log/<run_or_date_group>/<task_id>-<model_short>/rollout.jsonl` (+ `result.json` with the parsed
   `{answer, prob/dist, uncertainty, sources}`). Have every runner write there directly (Agent SDK
   transcripts too — set `HOME` or copy post-run). Migrate the existing `log/` files into this scheme.
5. **Slim `config/` to the minimum non-duplicated YAML.** It need NOT match galaxy 1:1 — keep only
   what's used: one `run` yaml (model + toolset + as_of), model entries, one `tool` toolset list.
   Drop anything not read by the runners.
6. **Restructure `futurecast/` to a lean core-like layout** AFTER §3 removes Path B:
   `futurecast/{tasks (was data), config, utils, forecasting (question_contract+playbook+schema),
   io, guard, experience, playbook}`. Update the ~3 runner imports + `tests/test_smoke.py`; keep
   green. (Don't do this before §1–§3, to avoid churn.)
7. **Rewrite `README.md` in Chinese** (中文重写), reflecting the converged architecture.
8. **Init + push to GitHub** (the user created the remote; repo may be renamed):
   ```bash
   cd /Users/weichy/Desktop/Doing-Right-Things/FutureX/papers/futurecast
   echo "# future-prediction-SDK" >> README.md     # or keep the Chinese README; just ensure a README exists
   git init && git add -A                            # NOTE: add -A, not just README.md, to push the whole repo
   git commit -m "first commit"
   git branch -M main
   git remote add origin https://github.com/Weichy9218/future-prediction-SDK.git
   git push -u origin main
   ```
   Ensure `.gitignore` excludes `.venv/`, `.env`, `agent_sdk/claude-code-router/` (12M vendored),
   `agent_sdk/ccr_home/`, `log/`, `__pycache__/`.

---

## 5. Guardrails (from AGENTS.md — do not violate)
- Do NOT rebuild the agent loop or add any Python "can-the-model-predict" state machine / coverage /
  readiness / typed pillar frame. Cognition lives in the prompt + experience library.
- `core`/`futurecast` must not hardcode specific sites/series; site specifics go in `experience/`.
- Invariant is "scorable" (Brier/numeric error/calibration), not state-machine self-consistency.
- as-of is the one trust not given to the prompt — enforce it mechanically at the tool boundary.
- Scoring & question generation reuse **verl-tool-future** (`/Users/weichy/code/verl-tool-future`:
  `benchmark.scoring.score_submission_file`, `rewards/brier.py`; `vtf benchmark create`). The GLM
  repo's `create_futureworld_benchmark.sh` shows the question-gen invocation.

## 6. Quick environment notes
- venv: `futurecast/.venv` (uv). Installed: claude-agent-sdk, anthropic, openai, omegaconf, tiktoken,
  httpx[socks], pytest. `claude` CLI v2.1.195 present.
- Start local router: `node agent_sdk/claude-code-router/dist/cli.js start` with
  `HOME=agent_sdk/ccr_home` (or just `./agent_sdk/run.sh`).
- apihy models: glm-5, glm-5.1, qwen3-235b-a22b(-instruct/-thinking), kimi-k2.6, deepseek-v4-flash.
  haoxiang models: gpt-5.5, gpt-5.4, gpt-5.4-mini, gpt-5.3-codex, …
- Always `pop`/`unset` `ALL_PROXY/HTTP(S)_PROXY` before direct gateway calls.
