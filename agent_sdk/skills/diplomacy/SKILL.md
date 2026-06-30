---
name: diplomacy
description: "Predicts outcomes of diplomatic events, international meetings, summit results, sanctions decisions, and bilateral relations. Covers head-of-state meetings, treaty negotiations, UN resolutions, sanctions implementation, and international cooperation outcomes. Use this skill when predicting diplomatic meetings, summit outcomes, trade negotiations, sanctions, or whether specific leaders will meet — triggered by mentions of diplomatic meeting, summit, negotiate, treaty, sanctions, bilateral, UN resolution, head of state meeting, or specific diplomatic contexts like US-Venezuela, US-China, NATO."
---

# Diplomacy & International Relations Prediction

## When to Use

- Predicting whether specific leaders or officials will meet
- Forecasting summit or negotiation outcomes
- Estimating sanction implementation or removal probabilities
- Predicting trade deal or treaty signing likelihoods
- Any diplomatic event outcome prediction

## Data Sources

- **Official government schedules**: White House, Kremlin, Élysée schedules
- **UN meeting calendars**: General Assembly, Security Council sessions
- **Good Judgment Open**: Expert forecasts on geopolitical events
- **Prediction markets**: Manifold, Polymarket, Metaculus for diplomatic events
- **Wire services**: Reuters, AP for diplomatic reporting
- **Foreign policy think tanks**: CFR, Brookings, IISS, Chatham House analysis
- **Government press briefings**: State Department, Foreign Ministry spokesperson statements

## Methodology

### "Will X and Y Meet" Predictions
1. **Check official schedules** — have any meetings been announced or scheduled?
2. **Recent diplomatic trajectory** — are relations improving or deteriorating?
3. **Logistical feasibility** — are both leaders in the same region or attending the same event?
4. **Precedent** — have they met before? What was the context?
5. **Intermediary signals** — have lower-level officials been meeting? This often precedes summits
6. **Base rate** — if no meeting is scheduled, the default probability of an unscheduled meeting within a few weeks is very low (<10%)

### Summit/Negotiation Outcome Predictions
1. **Pre-negotiation signals** — what concessions have been publicly discussed?
2. **Domestic political constraints** — what can each leader realistically agree to?
3. **Past negotiation patterns** — similar negotiations and their historical outcomes
4. **Mediator involvement** — third-party mediators increase deal probability by ~20-30%
5. **Deadline pressure** — artificial deadlines (elections, sanctions expiry) can force outcomes

### Sanctions Predictions
1. **Current sanctions framework** — what's in place, what's the enforcement level?
2. **Triggering events** — what would cause new sanctions or removal of existing ones?
3. **Coalition politics** — sanctions require multilateral coordination; check for holdouts
4. **Economic impact** — sanctions creating domestic economic pain may face removal pressure

## Prediction Tips

- For "will leaders meet within X timeframe": if no meeting is publicly planned, predict "No" unless there's strong evidence of back-channel negotiations
- Diplomatic announcements are usually prepared weeks in advance — if nothing is leaked or scheduled within a week of the deadline, it's very unlikely
- US-Venezuela relations have been contentious since 2019; a face-to-face meeting would require significant diplomatic groundwork and would likely be pre-announced
- At international multilateral events (G7, G20, UNGA), bilateral sideline meetings are common and often unscheduled
- Prediction markets reflect crowd intelligence well for high-profile diplomatic events
- "Testify before X committee" questions depend on legal/legislative procedure — check if a subpoena was issued

## Example Predictions

**Input**: "Will the US president and Maduro meet in person before 19 March 2026?"
**Approach**: Check recent US-Venezuela diplomatic trajectory. Is there any reporting of planned meetings? Are diplomatic channels open? If sanctions are still in place and no diplomatic softening is reported, predict "No" with high confidence (~95%).
