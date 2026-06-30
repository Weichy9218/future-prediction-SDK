---
name: base-rate-estimation
description: "Provides methods for estimating base rates (prior probabilities) for different types of prediction questions. Base rates are the foundational prior for any prediction — they represent how often a type of event occurs before considering case-specific details. Use this skill at the start of any prediction task to establish a reasonable prior, ESPECIALLY when you don't have a strong domain-specific signal — triggered by any prediction task, or when the system needs to establish a prior probability for an unfamiliar question type."
---

# Base Rate Estimation

## When to Use

- At the beginning of every prediction task to establish a prior
- When encountering a question type you haven't seen before
- When domain-specific data is unavailable or unreliable
- When sanity-checking your prediction against what's "normal"

## Base Rate Reference Library

### Binary (Yes/No) Events by Category

| Event Category | Typical Base Rate | Example |
|----------------|-------------------|---------|
| Leader meeting within timeframe (no known plan) | 5-10% | "Will leaders X and Y meet before date Z?" |
| Specific tech announcement on specific date | 10-20% | "Will product X be announced on date Y?" |
| New international conflict in any given week | 3-5% | "Will a new conflict start next week?" |
| Government policy implementation on time | 30-50% | "Will reform X be implemented by date Y?" |
| Industrial production target met | 25-40% | "Will factory X exceed target Y by date Z?" |
| Referendum reaching turnout quorum | Varies by country | Italy: ~40-50% reach quorum historically |
| Major sporting upset (top vs bottom) | 15-25% | "Will underdog X beat favorite Y?" |
| Prediction market >80% outcome occurring | ~85% | Most well-traded markets are well-calibrated |

### Multi-Choice Events

| Question Type | Strategy |
|---------------|----------|
| N equally-likely options | Start at 1/N, then update |
| "Which items will be in top X" (from a list) | Start with current rankings or favorites |
| Range predictions (numeric buckets) | Start with the bucket containing the current value/recent average |
| Multi-select (choose all correct options) | Treat each option independently |

### Ranking/Chart Predictions

| Scenario | Base Rate Insight |
|----------|-------------------|
| Item stays at same rank next period | 60-80% for top items, 30-50% for mid-chart |
| New entry reaches #1 in first period | 10-30% depending on platform |
| Top 3 items remain in top 3 next period | ~50-70% |
| Item drops out of top 10 entirely | 10-20% per period for items currently ranked 7-10 |

### Financial Base Rates

| Metric | Base Rate |
|--------|-----------|
| Stock daily return (Chinese A-shares) | Mean ~0%, daily std ±2% |
| CSI 300 daily range (high-low) | Typically 1-2% of index value |
| Central bank holds rate at next meeting | ~60-70% (varies by cycle) |
| Commodity stays within ±5% of current price over 1 week | ~70-80% |
| Forex central parity daily change | ±0.1-0.3% typically |

## Methodology

### Finding Base Rates
1. **Reference class forecasting** — identify similar past events and calculate the frequency
2. **Official statistics** — government, organizational databases for event frequencies
3. **Academic research** — published studies on event frequencies in specific domains
4. **Prediction market history** — past market resolutions provide base rates by topic
5. **Personal experience data** — track your own past predictions by category

### Adjusting from Base Rate
The base rate is your starting point. Adjust using specific evidence:

```
P(event) = Base_Rate × Likelihood_Ratio

Where Likelihood_Ratio = P(evidence | event) / P(evidence | no event)
```

**Practical adjustment scale:**
- Weak evidence (suggestive but not definitive): adjust by ×1.5-2
- Moderate evidence (clear but not conclusive): adjust by ×2-5
- Strong evidence (nearly dispositive): adjust by ×5-20

### When Base Rates Are Most Important
1. **Low base rate events** — even strong evidence may not make them likely (e.g., 2% base rate × 5 = 10%)
2. **Unfamiliar domains** — when you lack expertise, the base rate is your best friend
3. **Long time horizons** — the further out, the more dominant the base rate becomes
4. **Surprising claims** — extraordinary claims need to overcome low base rates

## Self-Evolution Integration

As the system makes predictions and receives ground truth:
1. **Build domain-specific base rates** — store observed frequencies by question category in `memory/calibration/`
2. **Update base rates** — use Bayesian updating as new data comes in
3. **Identify domains where your base rates are off** — if you're consistently surprised, your base rates need updating
4. **Share cross-domain insights** — a base rate learned in one context may apply to similar contexts
