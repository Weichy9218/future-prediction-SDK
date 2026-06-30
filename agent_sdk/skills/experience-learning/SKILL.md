---
name: experience-learning
description: "Provides methodology for the prediction system to learn from past predictions, accumulate experience, and self-improve over time. This is the core self-evolution skill. Covers prediction outcome tracking, error analysis, strategy effectiveness measurement, and knowledge base updates. Use this skill after receiving ground truth for past predictions, during system performance reviews, or when deciding how to improve prediction strategies — triggered by mentions of learning from experience, improving predictions, self-evolution, past performance analysis, strategy optimization, or when processing ground truth data for completed predictions."
---

# Experience Learning & Self-Evolution

## When to Use

- After receiving ground truth for completed predictions (post-mortem analysis)
- During periodic system performance reviews
- When a prediction strategy consistently underperforms
- When deciding whether to adjust skill weights or strategies
- For building and updating the knowledge base

## Self-Evolution Loop

```
Predict → Resolve → Evaluate → Learn → Update → Predict (improved)
```

### Phase 1: Prediction Recording
For every prediction, record:
1. **Task metadata** — task_id, question, category, level, resolution date
2. **Selected strategy** — which skill(s) and tools were used
3. **Key evidence** — what information informed the prediction
4. **Confidence level** — calibrated probability for each option
5. **Final answer** — the prediction submitted

Store in: `memory/predictions/`

### Phase 2: Resolution & Scoring
When ground truth becomes available:
1. **Record resolution** — what actually happened
2. **Compute scores** — Brier score, log score, accuracy for the prediction
3. **Compare to baselines** — how did the prediction compare to: market price, naive baseline, random guess?
4. **Flag outliers** — identify predictions that were significantly wrong

### Phase 3: Error Analysis
For wrong predictions, classify the error:

| Error Type | Description | Example |
|------------|-------------|---------|
| **Information gap** | Critical data was unavailable | Could not access real-time ranking |
| **Model error** | Had the data but drew wrong conclusion | Misread the trend direction |
| **Base rate error** | Ignored or misjudged the base rate | Predicted rare event as likely |
| **Stale data** | Used outdated information | Ranking had changed since last scrape |
| **Overconfidence** | Was too confident in one direction | Said 95% but turned out wrong |
| **Category error** | Applied wrong analytical framework | Used sports analysis for finance |
| **Execution error** | Tool failure or data processing bug | Scraper returned partial data |

### Phase 4: Strategy Update Rules

**When to strengthen a strategy:**
- Brier score < 0.15 over 10+ predictions in a category
- Consistently outperforms the market price baseline
- High coverage (successfully applied to many questions in the category)

**When to weaken a strategy:**
- Brier score > 0.3 over 10+ predictions
- Consistently underperforms random guessing in a category
- Frequent execution errors or data availability issues

**When to create a new strategy:**
- A cluster of similar questions has no matching skill
- An existing skill covers the topic but performs poorly
- A new data source becomes available

### Phase 5: Knowledge Base Updates

Update these knowledge stores after each evaluation cycle:

| Store | Location | Update Trigger |
|-------|----------|----------------|
| Skill registry | `memory/skill_registry.json` | After each prediction (usage stats) |
| Domain knowledge | `memory/domain_knowledge/` | When learning a new fact about a domain |
| Calibration data | `memory/calibration/` | After ground truth comparison |
| Strategy effectiveness | `memory/strategy_effectiveness/` | After batch evaluation |
| Experience logs | `memory/experience/` | After significant predictions |

## Specific Learning Patterns

### Ranking Prediction Learning
- Track rank stability per item across time
- Build item-specific "likelihood of rank change" estimates
- Identify which ranking positions are most volatile
- Learn platform-specific update schedules

### Financial Prediction Learning
- Track prediction errors by magnitude and direction
- Build asset-specific volatility estimates from experience
- Identify which macro events caused largest forecast errors
- Learn the effective lag time between event and price impact

### Event Prediction Learning
- Build category-specific base rates from accumulated outcomes
- Track which information sources were most predictive
- Identify which prediction markets are most well-calibrated by topic
- Learn the "surprise rate" for different event categories

## Implementation Priorities

1. **Always record** — every prediction should be stored with its reasoning
2. **Score regularly** — compute Brier scores after each batch of resolutions
3. **Focus on error patterns** — single errors teach less than systematic patterns
4. **Update incrementally** — small, evidence-based adjustments beat dramatic overhauls
5. **Preserve what works** — don't change strategies that are performing well
6. **Test changes** — when modifying a strategy, run shadow predictions before committing

## Metrics Dashboard

Track these system-level metrics over time:
- **Overall Brier score** — primary performance metric
- **Category-specific Brier scores** — identify weak domains
- **Skill selection accuracy** — is the classifier picking the right skill?
- **Information retrieval success rate** — how often do tools return useful data?
- **Prediction coverage** — % of questions where the system makes a confident prediction
- **Calibration plot** — predicted probability vs observed frequency curve
