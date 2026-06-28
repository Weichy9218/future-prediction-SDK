# Phase-3 分析：自有 LLM adapter + 正式 WebFetch + 预测方法论落地

本轮按用户优先级做了三件事，并用**新题实跑**据轨迹检查"系统是否在做有理有据的预测"。

## 1. 自有 LLM adapter 替掉 ccr（任务1，已验证）

`agent_sdk/llm_adapter.py`：自有 Anthropic `/v1/messages` 端点（Starlette），后端用 `futurecast/llm`
客户端（gpt→Responses API，glm→apihy chat/completions）。claude CLI 的 `ANTHROPIC_BASE_URL` 指向它；
它做 Anthropic⇄OpenAI 翻译，并把每回合以**缓冲式 SSE**（thinking→text→tool_use）回放。

- **harness 不变**：context/plan/memory/loop 仍是 Agent SDK；我们只接管"模型路由层"。
- **两个 ccr bug 同时解决**（实测 glm-5+工具）：工具入参全程干净（`{..}{..}` 重复消失）；reasoning
  作为 `thinking` 块进 rollout（一次跑 14 thinking / 13 tools）。
- gpt 的 reasoning 由 haoxiang Responses API 间歇暴露（有则捕获）；glm 稳定。
- 附带修复 `futurecast/llm/base.py`：补读 apihy 的 `reasoning_content` 字段进 `reasoning_summary`。

## 2. 正式 WebFetch（任务2，已验证）

`read_webpage` 重做，去掉盲截断（旧版硬切 12k）：
- 小页（≤30k）返回全文；大页用**廉价模型(apihy deepseek-flash)按 instruction 抽取**相关事实（最近值/
  日期/单位，数字日期 verbatim）——仿 Claude Code 的 fetch+extract。离线实测：287k 噪声页 → 精准抽出
  "≤2026-06-25 最近收盘 5020.10@06-25"。
- **抓取兜底**：Jina r.jina.ai 在本机不可达(000)，加直连 httpx(浏览器 UA)+粗清洗兜底；双失败给清晰
  `[fetch failed…]` 让模型快速转向、不死磕同一 URL。

## 3. playbook 落地"预测=先验+校准"（任务12，已验证）

据从 galaxy 轨迹找回的核心 insight 重写 `playbook_A_numeric.md` 为显式四步：**拆解 → 先验(同序列
最近值≤cutoff，先验即一个预测) → 因子校准(只微调先验、不推翻、不拉到极端) → 聚合(点+80%区间)**，并
明令**禁止搜目标日的值**(不存在)、**有工具预算就提交**。

**实跑证据（glm-5, CSI300, target 06-26）**：thinking 显式"follow the four-step process"；锚
5,020.10@06-25(WSJ + 多源交叉) → 逼近 52 周高点 5,059.66 的阻力因子微降 → `\boxed{5015}` + 区间 +
来源。**没有去抄已泄漏的 06-26 实际值 4868**——这是真预测，不是检索。

## 轨迹暴露的待优化点（系统合理性）

1. **glm-5 过度探索**：倾向反复搜更精确的数，常逼近/撞 max_turns(14)；gpt-5.5 更果断(2~3 次工具即
   提交)。已加"预算内提交"prompt 缓解。优化方向：按模型设 turn 预算 / 软提醒 / 或预测任务首选更果断
   的模型；也可在 runner 侧检测"已有锚点且临近预算"时注入一句"now commit"。
2. **数据页多为 JS/反爬**（macromicro/eastmoney/WSJ 直连 403 或 JS 壳），本机又无 Jina → 高质量
   read_webpage 命中率受限，模型退化到 search snippet 锚点。优化方向：可达的 reader（自建 headless 取
   数 / 备用 reader 端点）或针对数据源的结构化取数 skill（放 experience/，不进 core）。
3. **as-of 残余泄漏**（次要，用户已降级）：未来题无可泄漏答案；历史测试题靠目标日脱敏+检索日期上限尽力。

## 结论

系统现在**可见地在做预测而非检索**：先验(锚点)→因子校准→聚合，全程 reasoning 进轨迹，最终一个
`\boxed{}` 答案 + 可打分结构。LLM 与工具反馈完全自有可控，harness 保持 Agent SDK 原样。
