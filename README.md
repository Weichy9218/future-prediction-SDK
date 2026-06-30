# futurecast

> **租用标准通用 agent loop（Claude Agent SDK / claude CLI 或 Codex CLI）来解未来预测题——只控制 agent *之外* 的
> 东西：模型路由、工具、prompt、tool-边界 hook、可打分输出、经验库。绝不重建 agent loop。**

它是 `galaxy-selfevolve` 的 clean-room 继任者。前身的病根：把"模型能不能预测"的认知**外化成 Python
状态机**（readiness 阶梯 → audit 塔 → ForecastFrame/coverage 层），每次清理都长出新化身。本仓库用
硬性守则（`AGENTS.md`）从结构上杜绝：**认知只在 prompt + 经验库，loop 是租来的。**

## 基本原则（不可违反）

1. **不重建 loop。** context / plan / memory / 循环全用 Agent SDK 原样，我们一行都不改。
2. **认知只在 prompt + 经验库。** 没有 Python 预测状态机 / coverage / readiness / typed frame。
3. **as-of 是唯一不交给 prompt 的信任** —— 在**工具边界**机械执行（cutoff 后的数据进不了上下文）。
4. **不变量是"可打分"**（Brier / 数值误差 / 校准），不是状态机自洽。
5. **`futurecast/` 核心不硬编码任何站点/序列**；站点特例进 `experience/`，按需披露。

## 架构：租 / 自有 / harvest

```
            ┌────────────── 租 (rent, 原样不动) ──────────────┐
问题 ─playbook─►  Claude Agent SDK / claude CLI  或  Codex CLI  ─► \boxed{答案}
 (prompt)          │                  [agent loop]                  │
                   ▼                                                ▼
       ┌─ 自有 harness (own) ─────────────────────────┐     可打分输出 → 打分
       │ client  llm_adapter.py → futurecast/llm       │   (verl-tool-future)
       │ tool    tools_mcp.py 或 Codex native search   │
       │ prompt  playbook/ + runner 组装的 system prompt│
       │ hook    guard/as_of  (Claude MCP 工具边界过滤)│
       └───────────────────────────────────────────────┘
```

三类所有权，分清楚才不会越界：

| 类别 | 是什么 | 在哪 |
|---|---|---|
| **租 (rent)** | agent loop 的 **harness**：上下文管理、规划、记忆、循环本身。**不重建、不改。** | Claude Agent SDK / claude CLI；Codex CLI |
| **自有 (own)** | 我们**自行提供**给租来的 loop 的四件 harness：**client / tool / prompt / hook**（见下） | `agent_sdk/` + `futurecast/playbook,guard` |
| **harvest** | **拿来主义**：把别处已验证的*通用*基础设施**整段拷进来**复用，而不是重写——它是管线，不是"agent" | `futurecast/llm`（源自 core/llm）、打分/出题（源自 verl-tool-future） |

### 1) "harvest" 是什么
**harvest = 收割现成的通用件**。不是我们的创新，也不属于"agent loop"，而是**经过验证、与任务无关
的基础设施**，直接拷贝进来用，省得重造轮子：
- `futurecast/llm/` —— 收割自 `core/llm` 的多家 LLM 客户端（OpenAI Responses / OpenRouter chat），
  我们只把它当作 adapter 的后端。**它能拿到 reasoning summary（Responses `summary:auto`），这是租来的
  chat/completions 循环拿不到的**——所以保留它是有理由的。
- **打分 / 出题** —— 收割自 `verl-tool-future`（`score_submission_file` + `rewards/brier.py`）。
判断标准：**通用 + 别处已验证 + 与"预测认知"无关** → harvest；**预测专属** → 自有；**循环本身** → 租。

### 2) 我们自行提供的 harness：client / tool / prompt / hook
租来的 loop 缺这四样（或默认实现不可控），我们**自供**并完全掌控：
- **client（模型路由）** = `agent_sdk/llm_adapter.py`：自有 Anthropic `/v1/messages` 端点，把每回合
  翻译给 `futurecast/llm` 后端（`gpt-5.5`→haoxiang Responses；`glm-5`→apihy chat），再以缓冲式 SSE
  （thinking→text→tool_use）回放。**全程零 Claude token**；模型由 `FUTURECAST_MODEL` 选。
- **tool** = `agent_sdk/tools_mcp.py`：in-process MCP——`web_search`(Serper)、`read_webpage`(Jina，
  小页全文/大页廉价模型抽取，不盲截断)、`exa_search`。并把暴露面**收敛为官方 loop 的代表性切片**
  （`Read/Glob/Grep/Edit/Write/Bash/Agent/Task/Skill` + 3 个 MCP），剔除宿主 harness 杂项。
- **prompt** = `futurecast/playbook/`（A 数值 / B 事件）+ runner 按题型组装的 system prompt + as-of
  vantage 重构。**预测认知只在这里。**
- **skills** = `agent_sdk/skills/`：Claude Code 和 Codex 共用的 lightweight forecast skills。旧
  `galaxy-agent_old/skills/playbook` 已导入为无前缀 hyphen-case skill（如 `stock-market`、
  `calibration`、`national-election`）；另外保留本仓库特有的 `as-of-research` 和 `numeric-series`。
  运行入口会自动同步到各自 CLI home；source skill 纳入 git，运行态 CLI home 仍 gitignored。
- **hook** = `futurecast/guard/as_of.py` 在 Claude/Futurecast MCP **工具边界**的拦截（我们对租来 loop 的唯一"插桩"）：
  ① 确定性 regex（检索日期上限 + 目标日/cutoff 后脱敏）；② **专职筛选模型**（qwen3-next-80b）逐字
  指认残余泄漏 span，由我们确定性删除。Claude backend 的 main agent **永远看不到 cutoff 之后的信息**；
  Codex backend 当前用原生 search，靠 prompt/source 选择约束 as-of，尚未接入这层机械过滤。

### 3) 预测任务的 insight（方法论）
**预测 ≠ 检索。** 未来值**搜不到**（尚未发生）；能搜到的是**先验**和几个**因子**。轨迹必须能看出
系统在"有理有据地预测"，而非"搜答案"：

- **先验即一个预测（最高杠杆）。** 数值题：同序列 **≤cutoff 的最近值**（随机游走基线）；事件题：
  **市场/赔率/民调**，无市场则 **reference-class base rate** 或**最新已知状态**（排名持久化）。
- **因子只校准、不推翻。** 1~3 个因子微调先验；**别把概率推到 0/1、别让弱因子把数拖离先验**。
- **聚合 + 诚实不确定性。** 数值题给点 + **80% 区间**（经验上区间太窄→**放宽**）；事件题给**校准概率
  分布**。"微观随机、宏观确定"——按**组校准（Brier/log-loss）**优化，诚实 0.6 胜过过自信 0.95。
- **量级先对。** 10× 的 level 错误盖过一切——先核对序列量级再谈因子。
- **预算内提交，别过度搜索。** 有了可用锚点就 `\boxed{}` 收尾；别反复搜一个不存在的更新值。

## 运行

前置：`.venv` 就绪、`.env` 含密钥（gitignored）、网关直连（run.sh 会 `unset` 所有代理）。

```bash
cd /Users/weichy/Desktop/Doing-Right-Things/FutureX/papers/futurecast

# 跑某个基准文件里的第 N 题（默认 Claude Code backend；--tools 开多步检索 rollout；--model 选网关模型）
bash agent_sdk/run.sh --backend claude_code --model glm-5  --tools \
    --question-file tasks/2026-07-06_2026-07-06_futureworld_futurex_UTC+8__question.jsonl --task-index 0
bash agent_sdk/run.sh --backend claude_code --model gpt-5.5 --tools \
    --question-file tasks/2026-07-06_2026-07-06_futureworld_futurex_UTC+8__question.jsonl --task-index 0

# 切到 Codex backend（同一题面/同一 playbook/result schema；raw rollout 是 Codex JSONL event stream）
bash agent_sdk/run.sh --backend codex --model gpt-5.5 --tools \
    --question-file tasks/2026-07-06_2026-07-06_futureworld_futurex_UTC+8__question.jsonl --task-index 0
```
- `--backend claude_code` 启动 adapter(:3456)、设 `HOME=agent_sdk/cli_home`（claude CLI 写 transcript 处）、unset 代理。
- `--backend codex` 调用 `codex exec --json`，使用同一个 gpt-5.5/Sub2API gateway；`--tools` 使用 Codex 原生 web search。
- 两个 backend 启动前都会从 `agent_sdk/skills/` 同步全部 forecast skills 到各自 CLI home：
  Claude Code -> 本地 plugin `agent_sdk/cli_home/.claude/plugins/forecast-skills/skills/`，
  Codex -> `agent_sdk/codex/cli_home/skills/`。
- skills 的调用不是业务代码手动分派：Claude Code 通过 `ClaudeAgentOptions.plugins/skills` 暴露 plugin，
  模型可用 `Skill` 工具按 `description` 触发；Codex 通过 `CODEX_HOME/skills` 自动发现，同样按 metadata
  在 agent loop 内选择加载。
- 重复项已删除：旧 `futurecast-core-forecasting` 被 `base-rate-estimation`、`calibration`、
  `web-search-strategy` 和现有 system prompt 覆盖；旧 `futurecast-election-polling` 被
  `national-election` / `referendum` 覆盖。
- 模型：apihy=`glm-5`/`glm-5.1`/`qwen3-235b…`/`deepseek-v4-flash`；haoxiang=`gpt-5.5`/`gpt-5.4`/`gpt-5.4-mini`。
- 题型**自动分派**：数值题→playbook A，事件/选择/二元题→playbook B（`run_forecast.build_system_prompt`）。
- 输出默认落 `log/YYYYMMDD-HHMMSS/`（`run_group` 默认为运行开始 timestamp）。
- 工具边界使用 `effective_as_of = min(target_date - 1 day, run_date)`；历史回测或手工复现可用
  `FUTURECAST_AS_OF` / `--as-of` 显式覆盖。

### 参数管理（`agent_sdk/config.py`）
所有运行参数有**唯一一处默认**（`config.py`），优先级：**默认 ← 环境变量 ← CLI 显式参数**。env 是
跨进程真源（runner 与独立的 adapter 进程都读同一组 `FUTURECAST_*`），每次跑的 `config:` 行会记进
rollout 头部，可复现。要做 sweep 就设环境变量：

| 参数 | env | 默认 | 作用 |
|---|---|---|---|
| `model` | `FUTURECAST_MODEL`（或 `--model`） | `glm-5` | 网关模型路由 |
| `reasoning_effort` | `FUTURECAST_REASONING_EFFORT` | `high` | low/medium/high |
| `max_tokens` | `FUTURECAST_MAX_TOKENS` | `8192` | 单回合 completion 上限 |
| `max_turns` | `FUTURECAST_MAX_TURNS`（或 `--max-turns`） | `50` | 带工具时的 agent 回合上限 |
| `thinking_budget` | `FUTURECAST_THINKING_BUDGET` | `8000` | extended-thinking token 预算 |
| `run_group` | `FUTURECAST_RUN_GROUP`（或 `--run-group`） | 运行开始 timestamp（`YYYYMMDD-HHMMSS`） | 输出目录 `log/<run_group>/` |
| `run_date` | `FUTURECAST_RUN_DATE`（或 `--run-date`） | 本地今天 | 本次 forecast 的实际日期，用来 cap desired cutoff |
| `as_of_override` | `FUTURECAST_AS_OF`（或 `--as-of`） | 空 | 显式 effective cutoff；设置后跳过 `min(target-1, run_date)` |
| `asof_screen` | `FUTURECAST_ASOF_SCREEN`（或 `--asof-screen`） | `loose` | 工具边界 as-of 强度：`off`/`loose`/`strict` |
| `return_budget` | `FUTURECAST_RETURN_BUDGET` | `30000` | read_webpage 整页返回上限（字符） |

```bash
# 例：medium 推理 + 8 回合上限 + 关闭语义筛选（纯未来题、最省）
FUTURECAST_REASONING_EFFORT=medium FUTURECAST_MAX_TURNS=8 FUTURECAST_ASOF_SCREEN=off \
    bash agent_sdk/run.sh --model gpt-5.5 --tools --question-file tasks/<file>.jsonl --task-index 0
```
**as-of 强度**：默认 `loose`——只删*明确*晚于 cutoff / 透露目标日的内容，保留所有 ≤cutoff/无日期数据
（未来题无可泄漏答案，避免误删先验锚点）。历史回测改 `strict`（拿不准也删，防泄漏）；完全信任题面可 `off`（仅留确定性 regex 兜底）。

工具层会做轻量 loop control：用掉约 50% 工具预算后提醒模型已经过半、避免重复检索；用掉约 80%
后提醒尽快整理已有信息并作答。同一轮里重复/近似重复的 search/fetch 会被短路，不再访问外部 API。


**看结果（标准化布局）：**
```
log/<run_group>/<backend>/<task_id>-<model_short>[-tools]/
    rollout.jsonl   # claude_code: claude CLI transcript；codex: codex exec --json event stream
    result.json     # {answer, target_date, desired_as_of, effective_as_of, run_date, reasoning_summary, …}
log/adapter.log     # 每次请求的 tools=N + [tool-surface] 工具名单 + blocks（核对工具面/路由）
```
快速核对一次跑得对不对：`result.json` 的 `thinking_blocks>0`（reasoning 进轨迹）、`answer` 非空。
Claude/Futurecast MCP 工具 run 还应在 `rollout.jsonl` 的工具结果里看到 blocked/redacted/screened 这类
as-of guard 提示；Codex run 则看 `item.completed.item.type=="web_search"` 的 query/action。

### Claude Code vs Codex 轨迹差异

两种 backend 共享题面加载、playbook、`effective_as_of` 计算、`\boxed{}` 提取和 `result.json` schema；
输出目录按 backend 分开，方便同一个 `run_group` 下横向比较：

```
log/<run_group>/claude_code/<task_id>-<model_short>[-tools]/
log/<run_group>/codex/<task_id>-<model_short>[-tools]/
```

主要差异在 raw trajectory 和工具边界：

| 维度 | `claude_code` backend | `codex` backend |
|---|---|---|
| loop | Claude Agent SDK / claude CLI | `codex exec --json` |
| 模型路由 | 本地 `llm_adapter.py` 伪装 Anthropic `/v1/messages`，再转 `futurecast/llm` | Codex custom provider 直连 Sub2API Responses |
| 工具 | Futurecast MCP：`web_search` / `read_webpage` / `exa_search` | Codex 原生 web search（当前未接入 Futurecast MCP/Jina/Serper） |
| as-of 保护 | 工具结果进入上下文前由 Futurecast MCP regex + screening model 机械过滤 | prompt 约束 + 查询/source 选择约束；没有 Futurecast MCP 的机械 fetch guard |
| `rollout.jsonl` 形态 | Claude transcript：`assistant.message.content[]` 里可见 `thinking` / `tool_use` / `text`，后续 `user.tool_result` 保存工具返回 | Codex event stream：`item.completed.item.type` 为 `agent_message` / `reasoning` / `web_search` |
| 工具结果可见性 | 能看到具体 MCP tool args、tool result、as-of guard 提示（如 blocked/redacted/screened） | 能看到 Codex 搜索 query/action；搜索结果正文由 Codex event stream 抽象化，不等同于 MCP tool result |
| `result.json` | `backend=claude_code`，`tool_use_count` 来自 Claude tool_use 数 | `backend=codex`，`tool_use_count` 来自完成的 Codex tool/search items |

一个实测同题例子（Texas Attorney General Republican Primary Runoff，`gpt-5.5`，`effective_as_of=2026-05-25`）：
- `claude_code` + Futurecast MCP tools：2 次工具调用（Serper search + Jina read_webpage），raw rollout 能看到
  `mcp__futurecast__web_search`、`mcp__futurecast__read_webpage` 及 as-of guard 文本；结果为 `\boxed{B}`。
- `codex` + 原生 search：2 次完成的 web search item，raw rollout 记录为 `item.completed`/`web_search`；
  结果为 `\boxed{B, E}`，原因是它把 “Person B” 视作 Mayes Middleton 的重复选项一起选入。

因此：要审计“工具到底返回了什么、as-of 是否机械过滤”，优先看 `claude_code` 轨迹；要测试 Codex
agent loop 与同一 playbook/schema 的兼容性，看 `codex` 轨迹。后续如果需要严格同工具面对比，应把
Futurecast MCP 也接进 Codex，而不是使用 Codex 原生 search。

**打分**（题面有 ground_truth 时，例如历史回测）：经 `futurecast/io/scoring.py` 接
`verl-tool-future`（`score_submission_file` + `rewards/brier.py`）。未来题暂无标签 → 只看轨迹质量。

## 目录

```
agent_sdk/                # 自有运行底座（租来的 agent 在这里跑）—— 见 agent_sdk/README.md
  llm_adapter.py  tools_mcp.py  run_forecast.py  run.sh  config.py  sync_skills.py
  skills/        # Claude Code/Codex 共用 forecast skills 源目录；CLI home 内副本 gitignored
  cli_home/[gitignore]
futurecast/               # 预测控制层（只控制 agent 之外）
  playbook/   # 件#prompt：A 数值 / B 事件（先验+校准），无 Python 状态机
  guard/      # 件#hook：as_of 工具边界拦截（regex + 专职筛选模型）
  io/         # 件#输出：ScorableForecast schema + 提交写出 + score/brier 包装
  experience/ # 件#经验：题类笔记，按需检索，绝不预载
  data/       # 通用题面契约（loader：解析 target/as_of/题型，无站点特例）
  llm/        # harvest：reasoning-capable 直连客户端（Responses summary:auto）
docs/                     # analysis_phase2/3/4.md —— 历次轨迹分析与决策记录
tests/test_smoke.py       # 控制层 + as-of 工具守卫冒烟测试
log/                      # 标准化 rollout/result + adapter.log     [gitignore]
```

## 守则
完整守则见 **`AGENTS.md`**。一句话：**租 loop、不造预测状态机、core 无站点特例、as-of 在工具边界、
不变量是可打分。**
