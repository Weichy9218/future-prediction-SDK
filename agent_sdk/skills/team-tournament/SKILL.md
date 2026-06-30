---
name: team-tournament
description: "Predicts outcomes of team sports tournaments and championships beyond football. Covers rugby (Six Nations, World Cup), baseball (World Baseball Classic, MLB), basketball (March Madness, NBA), cricket, and other team competitions. Use this skill when predicting tournament winners, bracket progressions, championship outcomes, or team performance — triggered by mentions of Six Nations, WBC, March Madness, Sweet 16, NCAA, rugby, baseball tournament, or any team sport championship event."
---

# Team Sports Tournament Prediction

## When to Use

- Predicting rugby tournament outcomes (Six Nations, Rugby World Cup)
- Forecasting baseball tournament winners (World Baseball Classic, MLB Playoffs)
- Predicting basketball tournament results (March Madness, NBA Playoffs)
- Any multi-team elimination or round-robin tournament in team sports
- Bracket predictions and Sweet 16 / Final Four picks

## Data Sources

- **World Rugby Rankings**: Official ranking points for rugby predictions
- **WBSC Rankings**: World baseball/softball rankings
- **KenPom / BPI**: Advanced basketball analytics for March Madness
- **ESPN / Sports Reference**: Historical tournament data, team stats
- **Betting odds**: Sportsbook lines for individual matches and futures markets
- **Prediction markets**: Manifold, Polymarket for crowd probabilities

## Methodology

### Tournament Winner Predictions
1. **Gather betting futures** — futures odds for tournament winner are the best single predictor
2. **Check form and momentum** — recent results, especially in the same competition format
3. **Evaluate squad strength** — key player availability, home advantage rotation
4. **Historical dominance** — certain teams have structural advantages in specific tournaments

### Bracket/Advancement Predictions  
1. **Seed-based priors** — In March Madness, #1 seeds advance to Sweet 16 ~85% of the time
2. **Conference strength** — evaluate quality of competition faced
3. **Matchup specifics** — playing style interactions (e.g., pressing teams vs possession teams)

### Round-Robin Tournaments
1. **Head-to-head modeling** — predict each match, simulate final standings
2. **Home/away patterns** — in Six Nations, home advantage is worth ~5-7 points
3. **Grand Slam / Triple Crown scenarios** — track conditional probabilities

## Sport-Specific Tips

### Rugby (Six Nations)
- Home advantage is very significant (~65% home win rate)
- France and Ireland have been dominant in recent years
- Triple Crown (beating all home nations) requires beating England, Ireland, Scotland, and Wales
- Bonus point system matters for final standings

### Baseball (WBC)
- Japan has won 3 of the first 5 WBCs — they are historically the strongest
- USA has improved significantly since 2017
- Pitching depth matters more than batting in short tournaments
- Pool play format means early upsets are common

### Basketball (March Madness)
- #1 seeds have never all failed to reach the Sweet 16 in the same year
- A #16 seed has only beaten a #1 once (UMBC vs Virginia, 2018)
- Mid-major conference teams overperform their seed ~30% of the time
- "Power 5" conferences (Big Ten, SEC, Big 12, ACC, Big East) dominate Sweet 16 representation
- The "hot team" narrative has weak predictive power; pre-tournament metrics are stronger

## Example Predictions

**Input**: "Who will win the 2026 Six Nations?"
**Approach**: Check betting odds futures, current form, home/away schedule, key injuries. Weight heavily toward the top-2 favorites in odds.

**Input**: "Sweet 16 Predictions: at least one 1-seed won't advance?"
**Approach**: Historically, at least one #1 seed fails to reach Sweet 16 in ~40% of tournaments. Check current year bracket difficulty for each #1 seed's second-round opponent.
