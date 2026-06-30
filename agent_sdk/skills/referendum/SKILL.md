---
name: referendum
description: "Predicts outcomes of referendums, ballot measures, plebiscites, and public votes on specific policy questions. Use this skill when predicting referendum results, voter turnout for referendums, or outcomes of constitutional amendments and policy votes — triggered by mentions of referendum, ballot measure, plebiscite, constitutional amendment, voter turnout threshold, or specific referendum topics like judicial reform, independence, EU membership."
---

# Referendum & Ballot Measure Prediction

## When to Use

- Predicting referendum pass/fail outcomes
- Forecasting voter turnout for referendums (especially vs quorum thresholds)
- Predicting constitutional amendment votes
- Any public vote on a specific policy question (not candidate elections)

## Data Sources

- **Polling data**: Specific referendum polls are the best predictor
- **Prediction markets**: Manifold, Polymarket, Metaculus for high-profile referendums
- **Historical referendum data**: Past turnout and results in the same country/region
- **Academic research**: UCLA referendum database, direct democracy research
- **News coverage intensity**: Media attention correlates with turnout

## Methodology

### Will It Pass?
1. **Check polls** — referendum polls are less reliable than election polls (people decide late on policy questions)
2. **Status quo bias** — on average, the "No" / "reject change" side gains 3-5% from final polls to results
3. **Prediction markets** — aggregate wisdom, especially for well-traded markets
4. **Elite consensus** — when major parties align for/against, that's a strong signal
5. **Economic context** — economic anxiety makes voters more risk-averse (favor status quo)

### Will Turnout Exceed Threshold?
1. **Historical turnout** — what's the typical referendum turnout in this country?
2. **Salience** — how important is the issue to daily life? Controversial issues drive turnout
3. **Campaign intensity** — organized campaigns on both sides increase turnout
4. **Boycott dynamics** — if one side boycotts, turnout drops significantly
5. **Concurrent elections** — referendums held alongside elections have higher turnout

## Prediction Tips

- Italian referendums have a 50% turnout quorum — historically, roughly half of Italian referendums fail to reach quorum
- Italy referendum turnout has been declining: 2016 (65%), 2020 (51%), 2022 (20%)
- Technical/institutional reform referendums (like judicial reform) typically get lower turnout than social issues
- "Status quo bias" means undecided voters break toward "No" ~60/40
- International referendums (constitutional, EU-related) tend to have higher engagement
- Weather on election day can affect turnout by 1-2%

## Example Predictions

**Input**: "Italy judicial reform: Will turnout at the March 2026 referendum exceed 50%?"
**Approach**: Check Italy's recent referendum turnout trend (declining). Judicial reform is institutional rather than directly personal — lower salience. Recent Italian referendums have struggled to reach 50%. Unless there's a strong campaign mobilization, predict "No" (turnout below 50%) with ~65-70% confidence.
