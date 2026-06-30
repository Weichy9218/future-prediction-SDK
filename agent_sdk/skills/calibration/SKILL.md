---
name: calibration
description: "Provides probability calibration techniques and de-biasing methods for prediction tasks. Ensures predicted probabilities are well-calibrated (i.e., events predicted at 70% actually occur ~70% of the time). Use this skill when the prediction system needs to output calibrated probabilities, when reviewing prediction track records, or when adjusting for known cognitive biases — triggered by mentions of calibration, probability estimate, confidence level, Brier score, overconfidence, de-biasing, or when the system needs to convert qualitative confidence to calibrated numeric probabilities."
---

# Probability Calibration

## When to Use

- Converting qualitative confidence ("likely", "very unlikely") to calibrated probabilities
- Adjusting raw probability estimates for known biases
- Reviewing and scoring past predictions for calibration
- Any situation where well-calibrated probability output is important

## Core Calibration Principles

### The Calibration Standard
A well-calibrated forecaster's predictions match reality: of all events you predict at 70%, approximately 70% should occur. This is measured by **calibration plots** (predicted probability vs observed frequency) and **Brier scores** (lower = better; 0.0 = perfect, 0.25 = random).

### Common Biases and Corrections

| Bias | Description | Correction |
|------|-------------|------------|
| **Overconfidence** | Giving 90%+ confidence too often | Shrink toward 50%: adjust extreme probabilities toward the base rate |
| **Anchoring** | Over-weighting the first piece of information | Seek multiple independent estimates before committing |
| **Base rate neglect** | Ignoring how frequently the event type occurs | Always start with the base rate, then update |
| **Availability bias** | Overweighting vivid or recent examples | Use statistical data over memorable anecdotes |
| **Confirmation bias** | Seeking evidence that supports initial belief | Actively seek disconfirming evidence |
| **Scope insensitivity** | Treating very different magnitudes similarly | Explicitly think about scale and magnitude |

## Methodology

### Step 1: Establish the Base Rate
Before analyzing any specific details, determine: "How often does this type of event happen in general?"
- For yes/no questions: what's the historical frequency?
- For multi-choice: what's the uniform probability (1/N options)?
- For numeric: what's the historical mean and standard deviation?

### Step 2: Update with Evidence
Use a Bayesian updating mental model:
1. Start with the base rate (prior)
2. For each piece of evidence, ask: "How much more/less likely is this evidence under the hypothesis?"
3. Update the probability proportionally
4. Stop when additional evidence provides diminishing returns

### Step 3: Apply Extremizing/Shrinkage
- If you're making a single prediction: **shrink toward 50%** by ~10-20% (reduce overconfidence)
- If you're aggregating multiple forecasters: **extremize away from 50%** by ~20-30% (crowds are typically underconfident when averaged)

### Step 4: Probability Hygiene
- Never say 0% or 100% — use 1% to 99% as practical bounds
- For "nearly certain" events: use 95-98%, not 99%+
- For "nearly impossible" events: use 2-5%, not 1%
- For genuinely uncertain binary questions: 35-65% is a perfectly valid range

## Calibrated Probability Reference Table

| Verbal Expression | Calibrated Range | Notes |
|-------------------|-----------------|-------|
| "Almost certain" | 93-97% | Reserve for events with overwhelming evidence |
| "Very likely" | 80-92% | Strong evidence in one direction |
| "Likely" | 65-79% | More evidence for than against |
| "About even" | 40-60% | Genuinely uncertain |
| "Unlikely" | 21-35% | More evidence against than for |
| "Very unlikely" | 8-20% | Strong evidence against |
| "Almost impossible" | 3-7% | Overwhelming evidence against, but not impossible |

## Scoring Predictions

### Brier Score
$$BS = \frac{1}{N} \sum_{i=1}^{N} (p_i - o_i)^2$$

Where $p_i$ is predicted probability and $o_i$ is outcome (0 or 1).
- BS = 0.0: perfect
- BS = 0.25: random (for binary prediction at 50%)
- BS < 0.2: good forecasting
- BS < 0.1: excellent forecasting

### Log Score  
$$LS = \frac{1}{N} \sum_{i=1}^{N} [o_i \ln(p_i) + (1-o_i) \ln(1-p_i)]$$

More harshly penalizes confident wrong predictions. Used by GJOpen and Metaculus.

## Prediction Tips

- Superforecasters (top 2% of forecasters) consistently apply base rates and update incrementally
- The #1 forecasting improvement: look up and use the base rate
- For multi-choice questions with N options, start at 1/N and update from there
- Don't be afraid of "boring" predictions near the base rate — they're often the most accurate
- Track your predictions over time; review calibration monthly to identify systematic biases
- When in doubt, express more uncertainty (closer to 50%) rather than less

## Self-Evolution Integration

This skill should be used to:
1. **Score past predictions** — after ground truth is available, compute Brier scores
2. **Identify calibration gaps** — are you systematically overconfident in certain domains?
3. **Adjust future predictions** — apply domain-specific calibration corrections based on track record
4. **Store calibration data** — save prediction-outcome pairs in `memory/calibration/` for analysis
