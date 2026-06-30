---
name: ai-model-benchmark
description: "Predicts AI model performance on benchmarks, capability evaluations, and safety assessments. Covers METR evaluations, LMSYS chatbot arena, MMLU, HumanEval, and other AI benchmarks. Use this skill when predicting AI model scores, time horizons, ranking changes, or capability milestones — triggered by mentions of AI benchmark, METR, model evaluation, time horizon, chatbot arena, LLM performance, Gemini, GPT, Claude, or any AI model capability assessment."
---

# AI Model Benchmark Prediction

## When to Use

- Predicting AI model performance on specific benchmarks (METR time horizon, MMLU, HumanEval)
- Forecasting which model will lead on a particular evaluation
- Estimating AI capability milestones and timelines
- Predicting AI safety evaluation outcomes
- Any AI model performance prediction

## Data Sources

- **METR (Model Evaluation and Threat Research)**: Autonomous capability evaluations
- **LMSYS Chatbot Arena**: ELO-based model comparison from human votes
- **Artificial Analysis**: LLM performance and pricing benchmarks
- **Papers With Code**: Benchmark leaderboards across tasks
- **Model cards and technical reports**: Official capabilities from model providers
- **Prediction markets**: Manifold, Metaculus for AI capability milestones
- **Epoch AI**: AI compute and capability tracking

## Methodology

### Benchmark Score Predictions
1. **Previous model generation scores** — performance improvement between generations is typically 10-30%
2. **Scaling law extrapolation** — larger models with more compute generally perform better on benchmarks
3. **Architecture and training approach** — novel approaches (o1-style reasoning, test-time compute) can produce discontinuous jumps
4. **Release timing** — check if the model has already been evaluated or if this is a pre-release prediction
5. **Benchmark saturation** — some benchmarks (early MMLU) are near-saturated; improvements are smaller

### METR Time Horizon Predictions
- METR evaluates how long a task can be where an AI agent achieves 50% success rate
- This measures autonomous capability — longer time horizons = more capable agents
- **Previous results**: GPT-4 ~30min, Claude 3.5 Sonnet ~1-2h, o1 ~2-4h (approximate)
- **Scaling pattern**: Each generation roughly doubles the time horizon
- **Task complexity factors**: API usage, multi-step planning, error recovery
- For predicting a specific model (e.g., Gemini 3.1 Pro): estimate based on the model's known capability tier relative to predecessors

### Model Ranking Predictions
1. **Current rankings** — which models are currently leading on each benchmark?
2. **Release schedule intelligence** — has a new model update been announced?
3. **Provider competition cycles** — Google, OpenAI, Anthropic release in competitive cycles
4. **Diminishing returns** — leading models are increasingly close in performance

## Prediction Tips

- AI benchmarks improve roughly 20-50% per year for frontier models
- METR time horizon has been roughly doubling every 6-12 months
- For Gemini 3.1 Pro METR prediction: if Gemini 2.0 Pro scored ~3-4h, expect Gemini 3.1 Pro in the 4-8h range
- Model providers often cherry-pick favorable benchmarks in launch announcements
- Chatbot Arena ELO is the most robust single measure of "overall quality" but has biases toward verbose responses
- Prediction markets for AI milestones tend to be overconfident on near-term breakthroughs and underconfident on long-term progress
- The announcement date matters — check if official benchmark results have already been leaked or published

## Example Predictions

**Input**: "Gemini 3.1 Pro METR 50% time horizon?"
**Approach**: Check Gemini 2.0 Pro's known METR score. Estimate scaling improvement. If 2.0 Pro was ~3-5h, 3.1 Pro likely 5-8h. Check if any METR evaluation data has been leaked. Compare to the competition (Claude 3.5 was ~1-2h, o1 was ~2-4h). Select the range bucket that matches the estimate.
