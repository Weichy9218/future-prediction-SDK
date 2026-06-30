---
name: combat-sport
description: "Predicts outcomes of individual combat sports events including sumo wrestling, boxing, MMA/UFC, and martial arts tournaments. Use this skill when predicting sumo basho winners, yokozuna promotions, boxing match outcomes, UFC fight results, or any combat sports ranking changes — triggered by mentions of sumo, basho, yokozuna, ozeki, UFC, boxing, or specific fighter names like Onosato, Hoshoryu, Aonishiki."
---

# Combat Sports Prediction

## When to Use

- Predicting sumo tournament (basho) winners and promotion decisions
- Forecasting boxing match outcomes and title fights
- Predicting MMA/UFC fight results
- Any individual combat sport outcome prediction

## Data Sources

- **Sumo Reference (sumodb.sumogames.de)**: Complete historical records, head-to-head data
- **Japan Sumo Association**: Official schedules and results
- **BoxRec**: Boxing records and rankings
- **UFC Stats**: Official MMA statistics
- **Betting odds**: Specialized combat sports bookmakers
- **Prediction markets**: Manifold for popular fights

## Methodology

### Sumo Tournament Predictions
1. **Current rank (banzuke) analysis** — higher-ranked wrestlers (yokozuna, ozeki) win more often
2. **Recent form** — results in the previous 2-3 basho
3. **Head-to-head records** — sumo has strong patterns in matchups
4. **Injury status** — sumo wrestlers often compete through injuries
5. **Day-by-day tracking** — after Day 8, the leader board becomes highly predictive

### Sumo Promotion Criteria
- **Yokozuna promotion** requires: currently ozeki, back-to-back yusho (tournament wins) or equivalent dominant performance (e.g., 13-2 followed by a yusho)
- **Ozeki promotion** requires: ~33 wins over 3 consecutive basho at sekiwake or above
- The Yokozuna Deliberation Council makes subjective judgments — consistency and "hinkaku" (dignity) matter

### Boxing/MMA Predictions
1. **Betting odds** — strongest single predictor
2. **Style matchup analysis** — striker vs grappler, orthodox vs southpaw
3. **Recent activity** — ring rust after long layoffs
4. **Weight/experience** — moving up in weight is a significant disadvantage
5. **Method of victory** — some fighters have strong finish rates, others go to decision

## Prediction Tips

### Sumo-Specific
- An ozeki typically needs 12+ wins to be in yokozuna promotion discussion
- The Tournament leader after Day 10 wins the basho ~70% of the time
- First-time yusho winners are relatively rare at the top ranks
- Injury withdrawals (kyujo) significantly affect tournament outcomes
- Young rising stars (like Onosato, Aonishiki) tend to be overhyped by markets relative to veterans

### Boxing/MMA-Specific
- Heavyweight boxing upsets occur ~20-25% of the time
- In UFC title fights, champions win ~60-65% of the time
- "Unbeaten" records are overvalued by casual bettors — look at quality of opposition
- Late-career fighters have higher knockout vulnerability

## Example Predictions

**Input**: "Who will win the March 2026 grand sumo tournament?"
**Approach**: Check the banzuke (ranking), recent basho results, current win-loss records if tournament is in progress. Onosato and Hoshoryu as ozeki are strong favorites, with Aonishiki as a rising star.

**Input**: "Will Aonishiki be promoted to yokozuna?"
**Approach**: Check his current rank and recent results. He needs to be ozeki with back-to-back dominant results. If he's not yet ozeki, promotion to yokozuna is almost certainly No.
