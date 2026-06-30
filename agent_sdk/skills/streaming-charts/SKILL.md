---
name: streaming-charts
description: "Predicts rankings on global streaming platform charts and TV viewership rankings. Covers Apple TV, Netflix, Hulu, Disney+, Amazon Prime Video global and regional charts, plus linear TV Nielsen ratings. Use this skill when predicting what movies or shows will be ranked at specific positions on streaming charts or TV viewership rankings — triggered by mentions of Apple TV chart, Netflix top 10, Hulu ranking, FlixPatrol, Nielsen ratings, streaming ranking, Linear TV Top 10, or specific show/movie chart positions on any streaming platform."
---

# Streaming & TV Chart Prediction

## When to Use

- Predicting rankings on Apple TV Store, Netflix, Hulu, Disney+ charts
- Forecasting Nielsen Linear TV Top 10 rankings
- Estimating viewership or engagement rankings
- Any streaming platform chart position prediction
- Predicting FlixPatrol global/regional rankings

## Data Sources

- **FlixPatrol (flixpatrol.com)**: Aggregated daily streaming rankings across all platforms (Apple TV, Netflix, Hulu, Disney+, Amazon) — the primary data source for global streaming chart questions
- **Nielsen (nielsenmedia.com)**: Weekly US TV viewership data for streaming and linear TV
- **JustWatch**: Streaming availability and trending data
- **Apple TV/Netflix/Hulu official**: Platform-specific trending lists
- **The Numbers**: Box office and digital sales data
- **TV Series Finale**: Ratings and cancellation tracking for TV shows

## Methodology

### Streaming Chart Predictions
1. **Check current charts** — FlixPatrol and platform-specific charts show real-time rankings
2. **Release date timing** — newly released content dominates charts for 1-2 weeks, then declines
3. **Content type matters** — blockbuster movies peak higher but fade faster; TV series sustain longer
4. **Franchise/sequel boost** — familiar IP (Marvel, Star Wars, established series) ranks higher initially
5. **Platform exclusivity** — exclusive content ranks higher than multi-platform content
6. **Regional variation** — global vs. US vs. regional charts can differ significantly

### Nielsen Linear TV Predictions
1. **Schedule analysis** — what shows air in the measurement week?
2. **Historical ratings** — established shows have consistent audience levels
3. **Sports events** — live sports dominate Linear TV; NFL, NBA, etc. consistently #1
4. **Awards/event shows** — Oscars, Grammys cause one-week spikes
5. **Season premieres/finales** — higher ratings than mid-season episodes

### Chart Position Prediction Strategy
1. **Inertia** — items in top positions tend to stay there for several days/weeks
2. **New releases displace** — identify what new content releases during the prediction period
3. **Day-of-week patterns** — weekend viewing differs from weekday
4. **"Long-tail" shows** — some shows (like popular catalog titles) persist in mid-chart positions for months

## Prediction Tips

- FlixPatrol "TOP 10 in World" charts aggregate across all countries; heavily skewed toward English-language content
- Apple TV Store chart is influenced by purchase/rental pricing promotions
- Nielsen data has a ~2 week lag; "week ending on date X" means data published 10-14 days later
- For "programs ranked 7-9 in Linear TV Top 10": these are typically second-tier shows — think popular network procedurals and sitcoms
- Streaming charts are more volatile than linear TV (3-4 positions can change daily)
- Movies top streaming charts for 1-2 weeks then drop; TV series can sustain for 4-8 weeks
- For week-ahead predictions: check what new releases are scheduled and assume they'll enter top positions

## Example Predictions

**Input**: "Which movies ranked 3 to 5 on Apple TV Store World chart?"
**Approach**: Check current FlixPatrol Apple TV Store global chart. If predicting a future date, identify upcoming movie releases that will be available on Apple TV. Currently-ranked movies 3-5 are likely to still be there if no major new release displaces them.

**Input**: "Which programs ranked 7-9 in Nielsen Linear TV Top 10 TOTAL view?"
**Approach**: Check recent Nielsen weekly reports. Positions 7-9 tend to be occupied by stable performers — network shows with 2-4M viewers. Check the TV schedule for the measurement week for any high-profile premieres that could shift rankings.
