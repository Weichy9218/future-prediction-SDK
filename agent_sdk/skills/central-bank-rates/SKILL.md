---
name: central-bank-rates
description: "Predicts central bank interest rate decisions and monetary policy outcomes. Covers Federal Reserve (Fed), European Central Bank (ECB), Bank of England (BoE), Bank of Japan (BoJ), People's Bank of China (PBoC), and other major central banks including Brazil's SELIC rate. Use this skill when predicting rate hikes, cuts, holds, or any monetary policy decision — triggered by mentions of interest rate, rate decision, central bank, MPC, FOMC, ECB deposit facility, SELIC, base rate, monetary policy, or specific central bank names."
---

# Central Bank Interest Rate Prediction

## When to Use

- Predicting whether a central bank will raise, cut, or hold rates
- Forecasting the magnitude of rate changes
- Predicting forward guidance or policy shifts
- Any monetary policy decision outcome

## Data Sources

- **Fed Funds Futures / OIS** (Overnight Index Swaps): Market-implied rate probabilities — the single best predictor
- **CME FedWatch Tool**: Visual Fed rate probability tracker
- **ECB rate expectations**: Euro area OIS curve
- **Good Judgment Open (GJOpen)**: High-quality forecaster predictions on rate decisions
- **Central bank communications**: Meeting minutes, speeches, press conferences
- **Economic indicators**: CPI, employment data, GDP growth, PMI surveys
- **Prediction markets**: Manifold, Polymarket for rate decisions

## Methodology

### Days/Weeks Before Decision
1. **Check market-implied probabilities** — OIS/futures prices directly encode the market's expectation. CME FedWatch for the Fed, Bloomberg for ECB/BoE.
2. **Read prediction market prices** — for major central bank decisions, Manifold/Polymarket often have active markets
3. **Evaluate recent economic data** — CPI inflation readings, jobs reports released since last meeting
4. **Central bank forward guidance** — what did policymakers signal at the previous meeting?
5. **"Blackout period" constraints** — central bankers stop speaking publicly before meetings; signals from before blackout are your last clues

### Rate Decision Framework
| Signal | Likely Action |
|--------|---------------|
| Inflation above target + strong employment | Hold or Hike |
| Inflation falling + weakening employment | Cut |
| Inflation at target + stable economy | Hold |
| Financial stress / crisis | Emergency cut |

## Central Bank Specifics

### Federal Reserve (US)
- Target: 2% PCE inflation
- FOMC meets 8 times/year
- "Dot plot" shows individual member projections
- Market pricing is >95% accurate for the next meeting's decision

### ECB (Europe)
- Target: 2% HICP inflation
- Governing Council meets every 6 weeks
- More consensus-driven than Fed; rarely surprises markets

### Bank of England (UK)
- MPC has 9 members; individual votes are published
- Close votes (5-4, 6-3) signal potential direction change
- More prone to split decisions than Fed or ECB

### Brazil SELIC
- Copom meets every 45 days
- Brazil has historically volatile rates (currently ~14%+)
- Inflation and fiscal concerns drive decisions
- Copom tends to signal moves in advance through meeting minutes

## Prediction Tips

- For "will the rate be higher/lower/same than on date X": check if any meeting occurs between the two dates. If no meeting is scheduled, the rate stays the same with ~99% probability.
- Market-implied probabilities (futures) are right about the direction of the next move ~90% of the time
- The BoE is more likely to deliver "hawkish holds" (holding but with hawkish language) than surprise cuts
- ECB has been on a cutting cycle since mid-2024; each cut is typically 25bps
- When prediction market price is >85% for one outcome, trust it heavily — it's rarely wrong

## Example Predictions

**Input**: "At close of business on 19 March 2026, will the BoE Bank Rate be lower, same, or higher than on 5 February 2026?"
**Approach**: Check BoE MPC meeting schedule — is there a meeting between Feb 5 and Mar 19? If yes, check market-implied probabilities for that meeting. If no meeting, answer "Same" with very high confidence.

**Input**: "Outcome of the Bank of England MPC rate decision on 19th March?"
**Approach**: Check OIS-implied probability, recent UK CPI data, labor market data. If market prices 70%+ for "hold", predict "Rate unchanged".
