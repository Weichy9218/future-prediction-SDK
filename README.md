# futurecast

面向 **FutureWorld / FutureX** 基准的预测智能体（forecasting agent）。一句话定位：

> **租用一个标准通用 agent（Claude Code / claude-code-router / Claude Agent SDK）来解未来预测题，
> 只控制 agent *之外* 的东西——模型选择、工具、可打分输出、经验/技能、prompt/playbook。
> 绝不重建 agent loop。**

它是 `galaxy-selfevolve` 的 clean-room 继任者（为什么是"重建"而非"重构"，见该仓库
`docs/reflection_v4.md`）。前身的病根是把"模型能不能预测"的认知**外化成 Python 状态机**
（readiness 阶梯 → audit 塔 → ForecastFrame/coverage 层），每次清理都长出新的化身。本仓库用
硬性守则（见 `AGENTS.md`）从结构上杜绝这一点：**认知只存在于 prompt + 经验库，loop 是租来的。**

## 为什么选预测（研究赌注）

预测比多数 agent 任务都**更难**，而这正是价值所在：一个好预测同时压榨 agent 的每个维度——
**检索**（找对先验）、**建模**（把历史/市场变成先验）、**不确定性估计**、**概率校准**、
**推理**、**经验积累**。而且答案在推理时**尚不存在**，所以**难以作弊**：你拿不到标签，只能预测它。
序列**微观随机**（逐日答案抖动）但**宏观确定**（结构在一组问题上浮现），因此优化目标是
**组校准（Brier / log-loss）**，而非赢下任何单题。

## 架构：租 loop，造四件套

```
问题 ──► playbook 提示词 ──►   [ 租用的 agent loop ]   ──► 可打分预测 ──► 打分 (verl-tool-future)
          (件#1)         Claude Agent SDK (harness 不变)       (件#3)
                          → 自有 LLM adapter → 网关模型 (glm/gpt/qwen…)
                          + 工具 (Serper/Jina/Exa, 含 WebFetch 抽取 + as-of 守卫, 件#2)
                                      │
                              经验/技能库 (件#4，按需披露)
```

**租（不重建）**：agent loop 的 **harness**——context 管理、plan、memory、循环——保持 Claude Agent
SDK **原样不动**。**自有（明确可控）**：**模型路由层** `agent_sdk/llm_adapter.py`（自有 Anthropic
`/v1/messages` 端点，后端用 `futurecast/llm` 客户端）+ **工具层** `agent_sdk/tools_mcp.py`。一次 run
用 `--model` 选网关模型，路由进**同一个 agent + 同一套工具**：

- `apihy`（`https://zgc.apihy.com/v1`）→ `glm-5` / `glm-5.1` / `qwen3-235b` / `deepseek-v4-flash`
- `haoxiang`（`https://ie-crs.haoxiang.ai/v1`）→ `gpt-5.5` / `gpt-5.4` / `gpt-5.4-mini`

**全程零 Claude token**：claude CLI 只是壳，`ANTHROPIC_BASE_URL` 指向本地 adapter，adapter 在
Anthropic⇄OpenAI 之间翻译并把每一回合以缓冲式 SSE（thinking→text→tool_use）回放给 CLI。
（早期用 claude-code-router，因它在 thinking 下重复 glm 工具入参、且拿不到 reasoning，已被自有
adapter 替换。）

**造（我们拥有的小部件）—— `futurecast/` 控制层 + `agent_sdk/` 运行底座：**

| 件 | 位置 | 职责 |
|---|---|---|
| #1 playbook | `futurecast/playbook/` | 预测认知写在**提示词**里（A:数值序列, B:事件）。没有 Python 状态机 |
| #2 as-of 守卫 | `futurecast/guard/as_of.py` + `agent_sdk/tools_mcp.py` | 唯一不交给提示词的机制：在**工具边界**机械拦截 cutoff 之后的数据 |
| #3 可打分输出 | `futurecast/io/` | `ScorableForecast` schema + 提交写出 + `score`/`brier` 包装 |
| #4 经验库 | `futurecast/experience/` | 题类笔记，**按需**检索，绝不预载（预载会跨题泄漏、毁掉泛化性） |
| 题面契约 | `futurecast/data/loader.py` | 通用 FutureWorld/FutureX 题面解析（无任何站点/序列特例） |
| reasoning 直连 | `futurecast/llm/` | Responses API（`summary:auto`）直连客户端——见下方 reasoning 说明 |

## 运行

```bash
# 入口固定为 agent_sdk/run.sh：启动自有 LLM adapter → 跑 Agent SDK 预测
bash agent_sdk/run.sh                          # glm-5，纯知识（无工具）
bash agent_sdk/run.sh --tools                  # glm-5，带工具多步 rollout（thinking 进轨迹）
bash agent_sdk/run.sh --model gpt-5.5 --tools  # gpt-5.5（haoxiang），同一 agent + 同一套工具
```

`run.sh` 启动 `agent_sdk/llm_adapter.py`（:3456），设 `HOME=agent_sdk/ccr_home`（claude CLI 把
transcript 写在这里），并在调用网关前 `unset` 所有 `ALL_PROXY/HTTP(S)_PROXY`（haoxiang、apihy 直连）。

**输出（标准化 log 布局）**——runner 直接写入：
```
log/<run_group>/<task_id>-<model_short>[-tools]/
    rollout.jsonl   # claude CLI 的完整会话 transcript
    result.json     # 解析出的 {answer, point, low, high, anchor, uncertainty, confidence, sources, usage}
```

## as-of 守卫：本仓库的 #1 正确性机制

通用 agent 天然缺这个，且**提示词级约束不可信**：任何自身时间戳晚于 cutoff 的数据都必须挡在
推理上下文之外，否则预测被泄漏（基准"答案不泄漏"的可贵性质也随之毁掉）。cutoff 经
`FUTURECAST_AS_OF` 传入工具，`agent_sdk/tools_mcp.py` 在工具边界**三层**机械执行：

1. **检索日期上限**：`web_search` 给 Serper 加 `tbs` 自定义日期范围 `cd_max=cutoff`，把 Google
   索引日期压到 cutoff 及以前；`exa_search` 用 `endPublishedDate=cutoff`。
2. **结果发布日过滤**：丢弃 Serper `date` 字段晚于 cutoff 的结果。
3. **snippet 内嵌动态日期脱敏**（真正的泄漏面）：动态价格页发布日可能在 cutoff 前，但 snippet 里
   嵌着"今天"的价格（如 `江苏 2026/6/27 … 土杂猪 9.80`）。检测到 snippet 内含 cutoff 后日期就把
   该 snippet 脱敏（保留标题+链接，模型仍可去抓**历史**值）。`read_webpage` 则在检测到页面
   **发布日**晚于 cutoff 时整页拦截。

> 源特定的时间戳抽取（Serper `date`、Jina `Published Time`、Exa `publishedDate`）放在
> `agent_sdk/`（运行底座），**不进** `futurecast/` 核心——核心只保留 source-agnostic 的
> `check_as_of` 策略（`AGENTS.md` 守则 #3）。

## 已验证结论（2026-06，hog 问题，cutoff=2026-06-14，预测 2026-06-15 土杂猪价）

- **预测（非检索）已在轨迹中显式可见**：新 playbook 把方法固化为四步——**拆解 → 先验(同序列最近
  值/市场价/base rate，先验即一个预测) → 因子校准(只微调先验、不推翻) → 聚合(点+区间)**。实跑
  glm-5 CSI300：thinking 显式"follow the four-step process"，锚 5,020.10@06-25(WSJ 等多源交叉) →
  逼近 52 周高点的阻力因子微降 → `\boxed{5015}` + 区间 + 来源（**没有去抄已泄漏的 06-26 实际值
  4868**）。14 个 thinking 块全进 rollout。
- **reasoning 保留**：自有 adapter 把每回合以 Anthropic SSE 回放、含由 `reasoning_summary` 构造的
  `thinking` 块 → 模型中间思考进 rollout。glm 稳定且工具入参干净（ccr 重复 bug 已消除）；gpt 的
  reasoning summary 由 haoxiang Responses API 间歇暴露，有则捕获。
- **WebFetch（read_webpage）**：不再盲截断——小页全文、大页用廉价模型按 instruction 抽取相关事实
  (数字/日期保留)；Jina 不可达时直连兜底。完整轨迹分析见 **`docs/analysis_phase2.md`**。
- **as-of**（次要）：未来题一般无可泄漏答案；守卫(检索日期上限/目标日脱敏)主要服务于历史测试题。
- **知识地板**（无工具、纯知识）：`log/baseline_floor_0501/`，中位相对误差 ~45%；区间在名义 80%
  覆盖下只命中 1/5 → 系统性过自信。playbook 据此要求"先核对量级、把区间放宽"。

## 目录结构

```
agent_sdk/                    # 运行底座（≈ galaxy 的 pipeline/）——租来的 agent，全在本仓库代码里跑
  llm_adapter.py              # 自有 Anthropic /v1/messages 端点，后端 futurecast/llm（替代 ccr）
  claude-code-router/         # 早期 vendored ccr，已弃用              [gitignore]
  ccr_home/                   # claude CLI 的 HOME（transcript 落这里）  [gitignore]
  tools_mcp.py                # Serper/Jina/Exa 工具 + WebFetch 抽取 + as-of 守卫（in-process MCP）
  run_forecast.py             # Agent SDK runner（选模型、传 as-of、捕获 thinking、写标准化 log）
  run.sh                      # 固定入口
futurecast/                   # 预测控制层（只控制 agent 之外）
  playbook/ guard/ io/ experience/ data/ llm/
tests/test_smoke.py           # 控制层 + as-of 工具守卫的冒烟测试
log/                          # 标准化 rollout/result（gitignore）
```

## 与 verl-tool-future 对接（打分 & 出题）

打分与出题复用 **verl-tool-future**（`/Users/weichy/code/verl-tool-future`）：
`benchmark.scoring.score_submission_file` + `rewards/brier.py` 打分；`vtf benchmark create` 出题
（调用方式见 GLM 仓库 `create_futureworld_benchmark.sh`）。本仓库经 `futurecast/io/scoring.py` 接入。

## 守则（摘自 `AGENTS.md`，勿违反）

- **不重建 agent loop**，不加任何"模型能不能预测"的 Python 状态机 / coverage / readiness /
  typed pillar frame。认知只在 prompt + 经验库。
- `futurecast/` 核心**不硬编码**任何站点/序列；站点特例进 `experience/`，按需披露。
- 不变量是"**可打分**"（Brier/数值误差/校准），不是状态机自洽。
- as-of 是唯一不交给 prompt 的信任——在工具边界机械执行。
