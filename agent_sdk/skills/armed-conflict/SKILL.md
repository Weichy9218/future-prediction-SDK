---
name: armed-conflict
description: "Predicts outcomes related to armed conflicts, protests, civil unrest, and security crises. Covers casualty estimates, conflict escalation/de-escalation, protest outcomes, and ceasefire probabilities. Use this skill when predicting death tolls, conflict intensity, protest dynamics, or whether new conflicts will start — triggered by mentions of protest, conflict, war, casualties, death toll, ceasefire, military, unrest, revolution, or specific ongoing conflicts like Iranian protests, Ukraine war, Gaza, or any geopolitical crisis."
---

# Armed Conflict & Protest Prediction

## When to Use

- Predicting casualty or death toll ranges for ongoing conflicts
- Forecasting whether a new international conflict will start
- Estimating protest scale, duration, or outcome
- Predicting ceasefire or peace agreement probabilities
- Any conflict-related prediction

## Data Sources

- **ACLED (Armed Conflict Location & Event Data)**: Granular conflict event tracking worldwide
- **UCDP (Uppsala Conflict Data Program)**: Systematic conflict data with fatality estimates
- **Crisis Group (International Crisis Group)**: Expert analysis and conflict watch lists
- **Wikipedia "Casualties" pages**: Crowdsourced tracking for active conflicts  
- **OSINT sources**: Bellingcat, Oryx (military equipment losses), Mediazona
- **Prediction markets**: Manifold, Metaculus for geopolitical events
- **Good Judgment Open**: Expert forecaster platforms
- **News APIs**: Reuters, AP for breaking conflict news

## Methodology

### Casualty Estimation
1. **Check existing estimates** — ACLED, UCDP, and OSINT trackers provide running totals
2. **Rate extrapolation** — calculate recent daily/weekly casualty rate and extrapolate to target date
3. **Acceleration/deceleration** — is the conflict intensifying or de-escalating? Adjust the rate
4. **Undercounting adjustment** — official counts typically undercount by 30-60% in active conflicts
5. **Confidence intervals** — widen the range for volatile situations

### New Conflict Prediction
1. **Base rate** — new interstate conflicts are rare (~2-5 per year globally)
2. **Hotspot analysis** — which regions have rising tensions? (Crisis Group "CrisisWatch")
3. **Warning indicators** — troop movements, diplomatic breakdowns, economic sanctions escalation
4. **Seasonal patterns** — conflicts have weak seasonal patterns (spring offensives in some contexts)
5. **Week-ahead prediction** — the probability of a *new* major conflict in any given week is ~2-5%

### Protest Dynamics
1. **Trigger events** — protests escalate after government crackdowns, economic shocks, or political events
2. **Historical comparison** — similar past protests and their trajectories
3. **Government response capacity** — authoritarian regimes can suppress protests but at high cost
4. **Social media momentum** — online activity can be a leading indicator of protest size

## Prediction Tips

- "Will a new international conflict start next week?" — the base rate is low (~3-5%). Without specific crisis escalation signals, predict "No" with ~95% confidence
- For Iranian protests, death tolls have historically been in the hundreds per wave (2019: ~1,500; 2022: ~500+)
- Casualty estimates have heavy right tails — there's always a small probability of dramatic escalation
- Prediction markets and GJOpen tend to be better calibrated than pundits for geopolitical questions
- The "fog of war" means early estimates are often wrong — look for convergence across multiple sources
- For "how many will die" questions, check the current verified count and project forward

## Example Predictions

**Input**: "How many people will die as a part of the 2025-26 Iranian protests before March 20th?"
**Approach**: Check current verified death toll from ACLED/human rights organizations. Assess current protest intensity trend. If current confirmed deaths are ~200-300, and protests are ongoing but not at peak intensity, the likely range is the lower brackets. Adjust upward if there's been a recent escalation event.

**Input**: "Will a new international conflict start next week?"
**Approach**: Check Crisis Group CrisisWatch for escalating situations. Base rate says "No" with ~95% confidence. Only deviate if there's a concrete, specific crisis at the brink of military action (e.g., active military mobilization, ultimatums issued).
