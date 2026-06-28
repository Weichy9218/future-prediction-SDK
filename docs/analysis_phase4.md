# Phase-4 分析：工具面收敛 + gpt 修复 + as-of 专职筛选 + 题型分派

本轮按用户优先级落地四件事，全部**实跑取证**（FutureX `standardized_data.jsonl`，35→实际 20 道
Class B/数值未来题）。结论先行，证据在后。harness 仍是 Agent SDK 原样不动，只控 LLM 路由+工具+prompt。

## T1 — 工具面"干净且代表官方 loop"（已验证）

**诊断（关键）**：给 adapter 加 `[tool-surface]` 日志后实测，forecast agent 暴露的 **25 个工具不是官方
Claude Code loop**，而是 *宿主 harness* 的杂项：`CronCreate/CronDelete/CronList、DesignSync、Workflow、
SendMessage、ScheduleWakeup、EnterWorktree/ExitWorktree、TaskOutput/TaskStop`——对预测无用且污染轨迹；
同时**缺**官方核心 `Glob/Grep/WebFetch/WebSearch/TodoWrite`。且 `allowed_tools` 在本 CLI 构建里**只管
权限、不限暴露面**（设了 5 项仍暴露 25 个）。

**修复**：在 `tools_mcp.py` 重写工具策略——`DISALLOWED_BUILTINS` 显式剔除上述 harness 杂项 + 不可
离 Claude 执行的 `WebSearch/WebFetch`；`ALLOWED` 用我们的 MCP（web_search/read_webpage/exa_search）
作 web 等价物，并补回 `Read/Glob/Grep/Edit/Write/NotebookEdit/Bash/Agent/Skill/Task*`。

**结果**：暴露面收敛为 **16 个干净工具**，代表官方 loop：
`['Agent','Bash','Edit','Glob','Grep','NotebookEdit','Read','Skill','TaskCreate/Get/List/Update',
'Write'] + 3 个 MCP`。harness 杂项全部消失。

## T2 — gpt 工具少/无 reasoning（已诊断 + 修复 + 重跑）

**诊断**：直连探测 haoxiang Responses API 证明——gpt-5.5 在 `reasoning_effort` = medium **和** high 下
都**稳定**返回 `reasoning_summary` + 干净 `tool_call`（单轮）。所以 reasoning 在**客户端层是好的**，
旧"thinking=0、2 次工具"的反例是 **ccr 时代的产物**，非现 adapter 的问题。

**修复**：`run.sh` 设 `FUTURECAST_REASONING_EFFORT=high`（adapter 启动时读）。adapter 的
`_build_anthropic_blocks` 已把 `reasoning_summary` 构造成 `thinking` 块回放。

**重跑（gpt-5.5, 事件题 idx0 Pro Tour Amsterdam）**：`tool_use=10, thinking_blocks=5`（反例 2/0）——
reasoning 进轨迹、多步用工具。二元题 idx5：`tool_use=3, thinking=1`，果断。reasoning summary 偶有
"weather/conversation premature"的上游噪声，但策略执行正确（haoxiang summary 的已知瑕疵，可接受）。

## T3 — as-of 改"专职小模型在工具边界筛选"（已实现 + 验证）

**架构**：`futurecast/guard/as_of.py` 新增 `screen_leaks` / `screen_and_redact`（core、client 注入、
source-agnostic）。**关键设计：小模型只"指认"逐字泄漏 span，删除由我们确定性 `str.replace` 做**——
模型永远不重写整页，杜绝摘要/截断/篡改正文；只保留它在 ≤cutoff 历史值之外删掉的部分。fail-open 到
确定性 regex 守卫（floor）。`tools_mcp.py` 接 `qwen3-next-80b-a3b-instruct`（OpenRouterNewAPIClient/
apihy），`web_search`/`read_webpage`/`exa_search` 每次返回前过 `_apply_screen`。

**验证**：
- 离线确定性：同时抓到显式目标日值"4,868.22 at close June 26"**和** regex 全漏的相对泄漏
  "Yesterday it slipped to a fresh low"，保留 ≤cutoff 历史值（5012.30/5020.10）。
- live（glm 事件题）：qwen 在多次工具输出上 redact **1~13 个 span/次**，而 regex 层几乎全 0——这道
  真实未来题的赛果在当前 wall-clock 下确实已存在于 web，**语义筛选器删掉了 regex 全漏的泄漏**。glm
  自身 thinking 明确："I'm seeing redacted results... the event already happened from the target
  perspective, but I'm not allowed to see those because they're post-cutoff"——main agent 看不到答案。

## T4 — runner 按题型分派 playbook + 跑事件题（已修 + 验证）

**两处缺口**：
1. `run_forecast.py` 原把 `PLAYBOOK` **硬编码为 `playbook_A_numeric.md`**，事件题也喂数值 playbook。
   → 改为 `build_system_prompt(q)` 按 `forecast_type` 选 A/B，且 boundary/vantage 文案随题型适配
   （数值："anchor 最近序列值→外推"；事件："anchor 市场/赔率/base rate→因子校准、别搜赛果"）。
2. `loader._infer_type` **分类太弱**：原把 Yes/No 二元题与 `\boxed{YOUR_PREDICTION}` 自由格式题**全
   默认 "number"**（idx5–19 全部误判）。→ 新增：`\boxed{Yes/No}`→事件；`A./B.` 选项→多选事件；自由
   格式用**数值词典**区分 number(价格/市值/指数/yuan/kg/decimal places…) vs open event(who/which/names)。
   20 题正确分流：**4 道数值→A**（idx10/14/15/18 市值/猪价/CSI300 low），**16 道事件→B**。

**playbook B** 补：①"COMMIT, don't over-search"工具预算段（缓解 glm 过度探索）；②"latest known state"
先验（排名/榜单类题：最近排名 ≤cutoff 即先验、持久化）。

**实跑证据（轨迹在"先验+校准"而非搜答案）**：
- gpt-5.5 事件 idx0：`\boxed{F}`（Other/field，大型 MTG 赛事按 base rate 最可能）。
- glm-5 事件 idx0：30 工具/11 thinking，输出"无预测市场→reference-class base rate→校准概率分布→
  `\boxed{F}`" + uncertainty/confidence=low/3 来源。两模型殊途同归到 F。
- gpt-5.5 二元 idx5（Larry Wheels divorce→B）：搜 Polymarket 先验→`\boxed{Yes}`。
- gpt-5.5 数值 idx18（CSI300 low→A）：四步法、anchor 4868.22(06-26 close ≤cutoff)、
  `\boxed{4840}` + JSON `{point 4840, [4735,4940], confidence medium-low, sources}`。

## 残余待优化（诚实记录）

- **过度探索**：glm（事件 idx0：30 工具）与 gpt（数值 idx18：12 工具）都会反复发近重复 query 撞
  max_turns；wall-clock(06-28) 早于部分题 as_of(06-29) 时尤甚（追一个尚不存在的更新值）。playbook 已有
  "COMMIT"段缓解但模型仍倾向多搜。可选：按模型设 turn 软预算 / runner 在"已有锚点+临近预算"时注入
  "now commit"。非本轮阻塞项。
- **haoxiang reasoning summary 噪声**：gpt 的 thinking 偶现"weather forecast/conversation premature"
  等与题无关措辞（上游 summary 瑕疵），但工具策略与最终答案正确。

## 结论

四项全部落地并 live 验证：工具面代表官方 loop；gpt reasoning+多步工具恢复；as-of 由专职 qwen 在
工具边界语义筛选（main agent 永不见 cutoff 后信息）；runner 按题型正确分派 A/B playbook。系统**可见
地在做有理有据的预测**（先验→因子校准→聚合/校准概率），harness 保持 Agent SDK 原样。
