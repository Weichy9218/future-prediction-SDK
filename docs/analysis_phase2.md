# Phase-2 分析：轨迹驱动的系统合理性检查与优化方向

本轮在"租用 agent + 外部控制"的架构上做了三件事，并用**新题（FutureWorld 2026-06-24..30）**
实跑、据**轨迹**检查系统合理性。结论先行，证据在后。

## 做了什么（已验证）

1. **rollout 保留 reasoning/thinking**：ccr 两个 provider 开 `reasoning` transformer + Agent SDK
   开 `thinking`，模型的中间思考作为 Anthropic `thinking` content-block 写进 rollout.jsonl（与
   assistant 文本、tool_use 并列）。glm-5 上已实测：`thinking content-blocks in rollout.jsonl: 2/9`。
2. **runner 改用新题 + 轨迹优先输出**：读 `{task_id, task_question}`，用 `data.loader` 取
   per-question as_of(=target-1)；沿用题面自带的 `\boxed{number}` 契约（不再叠加自定义格式）；
   result.json 记录 `answer`(最终答案) + `reasoning_summary`(思考) + `final_text`。
3. **as-of 守卫大幅强化**（#1 正确性）：见下"泄漏"一节。

## 轨迹暴露的三个系统问题

### 问题 A：as-of 泄漏（已修复并验证）
- **现象**：glm-5 在 CSI300(target 06-26, as_of 06-25) 轨迹里推理"系统显示今天 06-28，目标 06-26
  是 2 天前 → 实际值已存在 → 我去搜真实值"，随后从 Yahoo snippet "CSI 300 … 4,868.22 … At close:
  June 26" 取到**已实现值**当答案。
- **根因**：(1) snippet 日期扫描漏了 `MM-DD-YYYY`(CEIC "06-26-2026") 与**紧贴 CJK** 的日期(`\b`
  在中文+数字间不成立)；(2) 更关键：**yearless 日期**("At close: June 26" 无年份)绕过需要年份的
  扫描；(3) 系统时钟把"今天=06-28"泄给模型，诱导它去取已发生值。
- **修复**：① 日期扫描补 `MM-DD-YYYY` + 用数字 lookaround 替 `\b`（CJK 紧贴可捕获）；② 新增
  **目标日脱敏**——守卫已知 `FUTURECAST_TARGET`，凡 snippet/页面行提到目标日(任意格式，含
  `June 26`/`6月26日`/`06-26-2026`)即脱敏，保留标题+链接但抹掉泄漏值；③ prompt 加**"感知今天=
  as_of"重构**，把目标日变成"尚未发生、不可查"。
- **验证**(离线确定性)：同一 CSI300 查询，已实现值 4,868.22 被彻底移除（7 snippet 脱敏，含
  Yahoo），`contains 4868: False`。

### 问题 B：开 thinking 后 glm-5 工具入参重复（ccr bug，glm 独有）
- **现象**：glm-5 + thinking 时，tool 入参变成 `{"url":"X"}{"url":"X"}` 拼接 → JSON 解析失败，
  模型卡住重试 ~8 次。不开 thinking 时 glm 工具调用干净(曾 11 次)。**gpt-5.5 + thinking 工具入参
  干净**——故是 ccr `reasoning` transformer 对 glm 工具流式增量的序列化 bug。
- **影响**：glm 上"reasoning 与可用工具"目前二选一。

### 问题 C：gpt-5.5 的 reasoning 经 haoxiang chat/completions 不稳定
- **现象**：开 thinking 跑 gpt，`thinking_blocks=0`。直连探测：haoxiang 同样 `reasoning_effort`
  参数**时有时无** reasoning_content(网关非确定行为)；ccr 发的 nested `reasoning:{effort}` 更拿不到。
- **可靠路径**：gpt reasoning summary 只有 Responses API(`/v1/responses`, `summary:auto`)稳定可得
  ——即保留的 `futurecast/llm/`。ccr 只说 chat/completions，拿不到。

## reasoning × tools 权衡矩阵（当前 ccr 2.0.0）

| 模型 | 工具入参 | reasoning 进轨迹 |
|---|---|---|
| glm-5 + thinking | ✗ 重复(问题B) | ✅ 稳定 |
| glm-5 无 thinking | ✅ 干净 | ✗ |
| gpt-5.5 + thinking | ✅ 干净 | ✗ 不稳(问题C) |

## 优化方向（按价值/可行）

1. **自有 model-adapter 层**（解 B+C 的正道，契合"外部控制 llm"）：在 ccr 与网关之间放一个我们
   拥有的 OpenAI 兼容小代理：① glm——干净地把 `reasoning_content` 注入 thinking，**不碰**
   tool_call 增量（绕过 ccr 的重复 bug）；② gpt——内部改调 `/v1/responses` 取 reasoning summary
   再以 `reasoning_content` 回吐。这样两模型都能"工具干净 + reasoning 进轨迹"。
2. **诚实评测纪律**：题面目标日落在"可索引的过去"时，已实现值天然可被检索，as-of 守卫只是尽力的
   第二道防线。**应在 target_date > 真实今天时运行**（本轮 gpt 跑的 Gold 06-30 即此类，给出
   `\boxed{4008.8}` 的真预测，无法泄漏），或在断网沙箱内跑。守卫负责"防手滑"，纪律负责"防作弊"。
3. **read_webpage 升级**(见下)：可选加一个"抓取后本地抽取"模式，逼近 WebFetch 的 fetch+extract。
4. **最终答案 = 题面 \boxed 契约**(已落地，避免过度规则化)；如需更稳的结构化抽取，用一次**轻量 LLM
   抽取**读轨迹产出 `{answer, drivers}`，而非正则兜底——但仅作分析侧，不作 gate。

## read_webpage 与原生 WebSearch/WebFetch 的差异（回答提问）

- **不是原生工具的改写**：Anthropic 原生 `WebSearch`/`WebFetch` 是**服务端工具**，只在 Claude API
  内执行，路由到 glm/gpt 时不运行、也无法复制。我们用第三方 API 自建等价物。
- **web_search ≈ WebSearch**：Serper(Google SERP)，返回 title/link/snippet；功能等价、provider 不同。
- **read_webpage vs WebFetch——差异较大**：
  - 原生 `WebFetch` = 抓取 URL → 转 markdown → **再用一个模型按你给的 `prompt` 抽取/作答**，返回的是
    *模型抽取后的结论*。
  - 我们的 `read_webpage` = Jina `r.jina.ai` reader，抓取 → 返回**干净 markdown 原文**(截断 12k)，**不**
    含内置 LLM 抽取；抽取交给 agent 自己的模型在上下文里做。
  - 取舍：对预测任务，返回原文更利于模型自行核对锚点(无中间有损抽取)，且**能挂 as-of 守卫**(原生
    WebFetch 的内部抽取不可控、无法插守卫)。代价是 token 更多。若要逼近 WebFetch，可加可选
    `extract_prompt` 触发一次 tool 侧小模型抽取(用 `futurecast/llm/` 的廉价 client)。
