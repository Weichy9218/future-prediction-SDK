---
name: football-match
description: "Predicts outcomes of football (soccer) match results, tournament progressions, and aggregate statistics. Covers UEFA Champions League, World Cup, domestic leagues, and continental competitions. Use this skill whenever the prediction involves football/soccer match winners, scorelines, goal totals, team advancement, or tournament brackets — even if the user doesn't say 'football' explicitly but mentions teams like Real Madrid, Bayern, Liverpool, Barcelona, or competitions like UCL, Europa League, La Liga, Premier League, Serie A, Bundesliga, Ligue 1."
---

# Football Match Prediction

## When to Use

- Predicting match outcomes (win/draw/loss) for specific fixtures
- Forecasting which teams advance in knockout rounds
- Estimating aggregate goal totals across tournament rounds
- Predicting tournament winners or final standings
- Any question involving Champions League, World Cup, Europa League, or domestic league results

## Data Sources

- **Betting odds**: Aggregate from major bookmakers (Bet365, William Hill, Betfair) — strongest short-term signal
- **UEFA/FIFA official rankings**: Team coefficient rankings for seeding context
- **FBref / Transfermarkt**: Squad value, player availability, recent form
- **WhoScored / SofaScore**: Match-level xG (expected goals) statistics
- **Prediction markets**: Manifold, Polymarket for crowd-sourced probabilities

## Methodology

### For Single Match Outcomes
1. **Check betting odds** — convert decimal odds to implied probabilities; these are the strongest baseline
2. **Adjust for context** — home/away, recent form (last 5 matches), head-to-head record, injury reports
3. **Factor in stakes** — teams may rotate squads in dead rubbers or when already qualified
4. **xG analysis** — compare underlying performance (xG created vs conceded) rather than just results

### For Tournament Progression
1. **Aggregate two-leg analysis** — consider away goals rule (if applicable), first-leg result momentum
2. **Historical precedent** — how often does a team with X-goal lead progress? (~85% for 2-goal leads)
3. **Squad depth** — fixture congestion matters in later tournament stages

### For Aggregate Statistics (e.g., total goals in a round)
1. **Base rate** — calculate the historical average for similar rounds (e.g., UCL R16 2nd legs average ~2.8 goals/match)
2. **Match-by-match estimation** — sum expected goals from individual fixture predictions
3. **Variance consideration** — use Poisson distribution for goal modeling

## Prediction Tips

- Betting odds are well-calibrated for match outcomes within 48 hours; use them as anchors
- In knockout rounds, the team that scores first at home advances ~75% of the time
- UCL Round of 16 tends to produce more upsets than Quarter-finals (favorites are ~60% vs ~70%)
- "Stoppage time winner" probability in any given match is roughly 5-8%
- Red card probability per match is roughly 8-12% per team
- Penalty shootout probability in a knockout tie is roughly 15-20%
- Away goals rule was abolished in UCL from 2021-22 onward
- Consider the "second leg motivation asymmetry" — trailing teams attack more, creating open games with more goals

## Example Predictions

**Input**: "Which teams will rank top 8 in UCL league phase?"
**Approach**: Check current standings, remaining fixtures, goal difference tiebreakers, run Monte Carlo simulation on remaining matches, weight by betting odds for each fixture.

**Input**: "How many total goals in UCL R16 second legs?"
**Approach**: Historical average is 22-25 goals across 8 second-leg matches. Adjust upward if multiple ties are close on aggregate (more open play) or downward if several are already decided.
