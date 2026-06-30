---
name: national-election
description: "Predicts outcomes of national and state-level elections, including parliamentary elections, presidential races, gubernatorial contests, and party vote share forecasts. Use this skill when predicting election winners, party seat counts, vote share changes, or coalition formation — triggered by mentions of election, vote, party, candidate, polls, ballot, campaign, primary, or any specific election event like Dutch elections, Bolivian elections, German Bundestag, US midterms, UK general election."
---

# National & State Election Prediction

## When to Use

- Predicting which party or candidate will win an election
- Forecasting vote share or seat counts for parties
- Determining which parties will outperform/underperform previous results
- Predicting coalition formation outcomes
- Any national or state-level electoral contest

## Data Sources

- **Polling aggregators**: FiveThirtyEight, The Economist, Politico Europe Poll of Polls, Wikipedia polling pages
- **Prediction markets**: Polymarket, Manifold, Metaculus, PredictIt (US-focused)
- **Election commissions**: Official results databases for historical data
- **Electoral Calculus / Swing models**: Seat projection models (UK)
- **Advanced models**: MRP (multilevel regression with poststratification) polls
- **Betting odds**: Oddschecker, Betfair Exchange for election markets

## Methodology

### Pre-Election Predictions
1. **Poll aggregation** — average recent polls, weight by recency, sample size, and pollster quality
2. **Prediction market prices** — convert to implied probabilities; often better than polls alone
3. **Historical patterns** — incumbency advantage, economic factors (GDP growth, unemployment)
4. **Fundamentals models** — "bread and peace" models using economic indicators
5. **Turnout modeling** — differential turnout can swing results by 2-5 points

### Vote Share Change Predictions
1. **Previous election baseline** — start with last election's vote share for each party
2. **National swing** — apply uniform swing model from current polls
3. **Local factors** — popular local candidates, regional issues, tactical voting
4. **New party dynamics** — new parties or splits absorb votes from specific existing parties
5. **Regression to mean** — parties with extreme previous results tend to revert

### Election Night Predictions
1. **Early results analysis** — compare actual vs expected results in bellwether regions
2. **Exit polls** — when available, these are highly predictive (within 2-3 seats usually)

## Prediction Tips

- Polls are most accurate within 2 weeks of the election; earlier polls have ~5% error
- Prediction markets often outperform polls for binary outcomes (winner prediction)
- Incumbents have a 3-5% structural advantage in most democracies
- Local elections have much higher variance than national elections (lower turnout, local issues)
- In proportional representation systems, smaller parties often outperform polls
- In Dutch elections, the political landscape is highly fragmented — many parties near 5-15%
- For "which parties will outperform", look at enthusiasm differential and mobilization capacity
- National parties in local elections often underperform relative to local/independent parties

## Example Predictions

**Input**: "Dutch 2026 local election: Which parties will outperform the 2025 general election?"
**Approach**: In Dutch local elections, local parties typically take 25-30% of votes, compressing national party shares. Right-wing parties (PVV, FVD) typically underperform in local elections where they run fewer candidates. Progressive urban parties (D66, GL-PvdA) and traditional local parties (CDA, VVD) tend to outperform their national share in local contexts.

**Input**: "Sucre Mayoral Election Winner (Bolivia)?"
**Approach**: Check recent polls, candidate name recognition, party strength in Sucre. In Bolivian local elections, MAS (ruling party) candidates and strong independents are typically competitive. Check prediction market prices on Polymarket.
