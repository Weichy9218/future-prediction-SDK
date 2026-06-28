# 新 Session 交接 Prompt（futurecast 预测 agent）

> 复制下面整段到新 session。它能让新 session 定位现有 rollout、读懂当前架构、完成本轮任务。

---

你接手 **`/Users/weichy/Desktop/Doing-Right-Things/FutureX/papers/futurecast`**——一个用**标准通用
agent（Claude Agent SDK / claude CLI）跑未来预测题**的仓库。核心理念：**租用 agent 的 harness
（context/plan/memory/loop 保持 Agent SDK 原样不动），只在外部控制 LLM 路由、工具、io、prompt**。
**不要重建 agent loop**，不要写 Python 预测状态机（认知只在 playbook + 经验库）。

先读（不要重新探索这些已确立的结论）：`README.md`、`AGENTS.md`、`docs/analysis_phase2.md`、
`docs/analysis_phase3.md`。

## 当前架构（已建成、已验证）

- **自有 LLM adapter**：`agent_sdk/llm_adapter.py`——自有 Anthropic `/v1/messages` 端点（Starlette），
  后端用 `futurecast/llm` 客户端（gpt-5.5→`GPTSub2APIClient`/haoxiang Responses API；glm-5→
  `OpenRouterNewAPIClient`/apihy chat）。它替代了 claude-code-router；claude CLI 的
  `ANTHROPIC_BASE_URL` 指向它，每回合以缓冲式 SSE（thinking→text→tool_use）回放。**harness 不变**。
- **工具**：`agent_sdk/tools_mcp.py`——in-process MCP：`web_search`(Serper)、`read_webpage`(Jina，
  含直连兜底 + 大页廉价模型抽取)、`exa_search`。
- **runner**：`agent_sdk/run_forecast.py`，入口 `bash agent_sdk/run.sh`。
- **playbook**：`futurecast/playbook/playbook_A_numeric.md`（已按"先验→因子校准→聚合"四步重写）、
  `playbook_B_event.md`（**尚未**重写，见任务4）。

## 怎么运行

```bash
cd /Users/weichy/Desktop/Doing-Right-Things/FutureX/papers/futurecast
bash agent_sdk/run.sh --model glm-5  --tools --question-file tasks/standardized_data.jsonl --task-index 0
bash agent_sdk/run.sh --model gpt-5.5 --tools --question-file tasks/standardized_data.jsonl --task-index 0
```
- run.sh 启动 adapter(:3456)、设 `HOME=agent_sdk/ccr_home`、`unset` 所有代理（apihy/haoxiang 直连）。
- 密钥在 `.env`（gitignored）。**直连网关前务必 unset `ALL_PROXY/HTTP(S)_PROXY`**。
- 模型：apihy=glm-5/glm-5.1/qwen3-235b-a22b-instruct-2507/deepseek-v4-flash；
  haoxiang=gpt-5.5/gpt-5.4/gpt-5.4-mini。

## 现有 rollout 在哪（先去读，理解现状）

标准布局：`log/<run_group>/<task_id>-<model_short>[-tools]/{rollout.jsonl, result.json}`。
adapter 自身日志：`log/adapter.log`（含每次请求的 `tools=N` 计数 + blocks）。最新有代表性的：
- `log/futureworld_2026-06-26/20260622191311492040-glm5-tools/`（glm CSI300，四步预测，14 thinking，
  answer 5015，未抄泄漏值 4868——**正例**）
- `log/futureworld_2026-06-30/20260622191311302231-gpt55-tools/`（gpt Gold，answer 4008.8，**仅 2 次
  工具、thinking=0**——任务2 要查的反例）

`rollout.jsonl` 是 claude CLI 的完整 transcript；thinking 在 `message.content[*].type=="thinking"`。

## 已核实事实（别重新查）

- **glm reasoning 稳定进 rollout、工具入参干净**（ccr 的重复 bug 已被 adapter 消除）。**gpt 的
  reasoning 由 haoxiang Responses API 间歇暴露**（有则捕获）；gpt 倾向少调工具。
- **当前 `--tools` 实际暴露 ~25 个工具**（adapter.log `tools=25`）= 3 个 MCP + ~22 个 Claude Code
  内置核心工具——**核心工具其实在场**，模型只是主要用了 web_search/read_webpage。
- `tasks/standardized_data.jsonl`：**35 道 FutureX 事件题（Class B）**，schema
  `{task_id, task_question, ground_truth(空), metadata{level 1-4, end_time 2026-06-29/30, source}}`。
  **全是未来题→无可泄漏答案**；无 ground_truth→暂不能打分。
- 沙箱里 **Jina r.jina.ai 不可达(000)**，且 macromicro/eastmoney/WSJ 等数据页多 JS/403→read_webpage
  实测命中率低（已加直连兜底）。数据页抓取**不重要**：沙箱抓不到就让用户本地跑代码。

## 本轮任务（可适当调整顺序/做法，但都要落地）

**T1 — 让预测用的 Claude Code 工具面"干净且能代表官方 loop"。**
当前同时挂着一堆非必要的**自定义 skill**：`deep-research, update-config, keybindings-help, verify,
code-review, simplify, fewer-permission-prompts, loop, claude-api, run, init, review, security-review`。
跑预测时应**隐藏/关闭**它们。但**必须保留官方核心工具**（用 Agent SDK 不用它的核心工具就没价值）：
参照 https://code.claude.com/docs/en/tools-reference ——至少
`Read/Glob/Grep`、`Edit/Write/NotebookEdit`、`Bash/Monitor`、`TodoWrite/Task/Agent`、`WebFetch/WebSearch
（这里用我们的 MCP 等价物）/Skill/ToolSearch`。可以精简，但要**代表官方 agent loop**。
做法：用 `ClaudeAgentOptions` 的 `allowed_tools/disallowed_tools/setting_sources` 或 skill 配置，确认
最终工具/skill 清单（在 adapter 里打印每次请求的 tool 名清单来核对），把非必要 skill 排除、核心工具保留。

**T2 — 查清 gpt 为何"工具调用少 + 无 reasoning/thinking"，修复后用 gpt-5.5 / gpt-5.4 重跑。**
先检查是不是 client/config 没开对：`futurecast/llm/openai_client.py` + `gpt_sub2api_client.py` 的
`reasoning_effort`（试 `high`）、`summary:auto`、`max_tokens`；adapter 里 gpt 是否把 `tools` 正确传给
Responses API、tool_calls 是否正确解析回 Anthropic `tool_use`。判断 reasoning 间歇是上游(haoxiang)还是
配置问题。修好后在 `standardized_data.jsonl` 上用 gpt-5.5 和 gpt-5.4 各跑几题，确认会多步用工具 + thinking 进轨迹。

**T3 — as-of 拦截改由"专门的小模型"做，不能交给 main agent，也不要只靠正则。**
现在 `tools_mcp.py` 用正则在工具边界脱敏（会漏）。改为：**每条工具输出（search 结果 + 抓取页面）在
返回 main agent 之前，先过一个独立小模型筛选**（用 `qwen3-next-80b-a3b-instruct`，经
`OpenRouterNewAPIClient`/apihy），由它判断并删除"晚于 as-of cutoff / 透露目标日值"的内容。这样
main agent 永远看不到 cutoff 之后的信息——把 as-of 这个"唯一不交给 prompt 的信任"交给一个专职筛选模型。
（注意：未来题本就不太泄漏，这条主要为历史题/稳健性；但要按此架构实现。）

**T4 — 从 `tasks/standardized_data.jsonl` 选几题跑，据轨迹验证"有理有据的预测"。**
这些是 **Class B 事件题**（如"谁会赢 Pro Tour Amsterdam 2026"），会用到 `playbook_B_event.md`——
**该 playbook 还没按新 insight 重写**，先把它改成：**理解 resolution rule → 取先验(预测市场/赔率/民调/
base rate，先验即一个预测) → 1~3 个因子校准(只微调、别把概率推到 0/1) → 输出校准概率/分布 + 来源**。
然后按 level 选 3~5 题，glm-5 + gpt-5.5 各跑，检查轨迹是否在做"先验+校准"而非搜答案。

**T5（可选）— 打分**：standardized_data 暂无 ground_truth、且题目未到期；待 end_time 过后用
`verl-tool-future`（`benchmark.scoring.score_submission_file` / `rewards/brier.py`）打 Brier。

## 守则（勿违反）

- **不重建 agent loop / harness**：context、plan、memory、循环都用 Agent SDK 的；只控制 LLM 路由+工具+prompt。
- **不写 Python 预测状态机**；预测认知只在 playbook + 经验库。`futurecast/` 核心不硬编码具体站点/序列
  （站点特例进 `experience/`）。
- **as-of 由专职小模型在工具边界筛选**（T3），不交给 main agent。
- 预测的本质：**先验(同序列最近值/市场定价/base rate) + 因子校准 → 聚合**，**不是搜答案**（未来题没有
  可搜的答案）。轨迹必须能看出系统在"有理有据地预测"。
- git：commit 末尾加 `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`；**推送用 SSH remote**
  （`git@github.com:Weichy9218/future-prediction-SDK.git`——HTTPS 会因缓存的 xhliu911 凭据 403）。
