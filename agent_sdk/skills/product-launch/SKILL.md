---
name: product-launch
description: "Predicts technology product launches, game releases, software announcements, and corporate M&A in the tech and entertainment industry. Covers game announcements (Assassin's Creed, GTA), streaming platform content, corporate acquisitions (Warner Bros), and major tech product reveals. Use this skill when predicting product release dates, game announcements, corporate deals, or entertainment industry business decisions — triggered by mentions of game announcement, product launch, release date, acquisition, merger, streaming platform, or specific products/companies like Assassin's Creed, Nintendo, Warner Bros, Netflix."
---

# Product Launch & Corporate Event Prediction

## When to Use

- Predicting game or software announcement dates
- Forecasting corporate M&A outcomes (acquisition votes, deal closures)
- Estimating streaming platform chart rankings
- Predicting tech product release timing
- Any technology/entertainment industry event prediction

## Data Sources

- **Industry insider accounts**: Reliable leakers (Jason Schreier, Tom Henderson for gaming)
- **SEC filings**: Proxy statements, 8-K filings for corporate events
- **Company earnings calls**: Forward guidance on product timelines
- **Event schedules**: E3, Game Awards, Nintendo Direct, Apple WWDC dates
- **Bloomberg / Reuters**: M&A reporting and deal tracking
- **Prediction markets**: Manifold for specific product/announcement questions
- **Patent filings**: Indirect signals of product development direction

## Methodology

### Game/Product Announcement Predictions
1. **Check leaks and rumors** — credible industry insiders often leak announcements 1-4 weeks ahead
2. **Event calendar** — align predictions with known showcase events (Nintendo Direct, State of Play)
3. **Company release cadence** — studios have typical development cycles (2-5 years between major releases)
4. **Marketing campaign analysis** — teaser trailers, social media activity, age rating submissions
5. **Voice actor / developer LinkedIn** — publicly visible project credits can confirm development

### Corporate M&A Predictions
1. **Shareholder vote requirements** — check proxy statement for vote threshold
2. **Regulatory approval status** — FTC/DOJ/EU Commission review status
3. **Deal premium vs current price** — large premium = higher likelihood of approval
4. **Opposition analysis** — activist shareholders, regulatory concerns
5. **Precedent** — similar deals in the same industry and their outcomes

### Streaming Chart Predictions
- See existing ranking skills for platform-specific charts (Hulu, Apple TV, Netflix)
- **FlixPatrol** provides aggregated streaming rankings
- **Nielsen weekly rankings** cover US viewing data with ~2 week lag
- New release timing dominates chart positions in the first 1-2 weeks

## Prediction Tips

- For "will X be announced on date Y": check if there's a scheduled showcase event on that date. If not, random-date announcements are uncommon for AAA games
- Warner Bros Discovery acquisition scenarios: check proxy statement language, board recommendation, and institutional investor positioning
- For corporate acquisition votes: if the board recommends approval, shareholders approve ~90% of the time
- Game remakes/remasters have 2-3 year development cycles from announcement to release
- "Will X be announced at event Y" for unconfirmed games: base rate is low (~10-20%) unless there are strong leaks
- Apple TV, Hulu, Netflix charts are dominated by recency — new releases dominate top positions for 1-2 weeks

## Example Predictions

**Input**: "Assassin's Creed: Black Flag Resynced (remake) Announced March 20th?"
**Approach**: Check if there's a Ubisoft showcase or gaming event on March 20th. Check industry insider reports. If no event is scheduled and no reliable leak points to this date, predict "No" with high confidence. If there IS a Ubisoft event, check rumors about the lineup.

**Input**: "How will Warner Bros Discovery shareholders vote regarding a sale?"
**Approach**: Check the proxy statement, board recommendation, institutional investor letters. If the board unanimously recommends a specific buyer, that deal passes ~90%+ of the time. If no deal is on the table, "Not acquired" is the answer.
