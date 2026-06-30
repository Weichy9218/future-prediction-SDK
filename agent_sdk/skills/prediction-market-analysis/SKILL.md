---
name: prediction-market-analysis
description: "Provides methodology for using prediction markets as data sources for forecasting. Covers extracting probabilities from Manifold Markets, Polymarket, Metaculus, Good Judgment Open (GJOpen), Futuur, and PredictIt. Use this skill whenever a prediction question has an associated prediction market slug/URL, or when you need crowd-sourced probability estimates as an anchor — triggered by mentions of prediction market, Manifold, Polymarket, Metaculus, GJOpen, Futuur, PredictIt, crowd forecast, market probability, or when a question's metadata contains a non-null slug field pointing to a prediction market."
---

# Prediction Market Analysis

## When to Use

- Any prediction question that has an associated prediction market URL (check metadata.slug)
- When needing crowd-sourced probability anchors for binary or multi-choice predictions
- When calibrating your own prediction against market consensus
- For understanding the information content of prediction market prices

## Supported Platforms

| Platform | URL Pattern | Strength | Data Access |
|----------|-------------|----------|-------------|
| **Manifold Markets** | manifold.markets/... | High volume, diverse topics | Free API, no auth needed |
| **Polymarket** | polymarket.com/event/... | Large money at stake (crypto) | Free API, CLOB data |
| **Metaculus** | metaculus.com/questions/... | Expert community predictions | Free API |
| **Good Judgment Open** | gjopen.com/questions/... | Professional forecasters, calibrated | Web scraping required |
| **Futuur** | futuur.com/q/... | International coverage | Web scraping required |
| **PredictIt** | predictit.org/markets/... | US politics focus | Free API |

## Methodology

### Extracting Market Probabilities
1. **Identify the market** — check the question metadata for a `slug` field containing the market URL
2. **Fetch current prices** — use the platform's API to get the current probability/price
3. **Interpret multi-outcome markets** — each option's price ≈ implied probability (but may sum to >100% due to overround)
4. **Normalize** — divide each option's price by the sum of all option prices to get proper probabilities
5. **Check volume/liquidity** — low-volume markets (<$1000 traded) are less reliable

### Using Market Prices as Anchors
1. **Start with market price** — well-traded markets are the best available prior
2. **Adjust for information edge** — only adjust if you have specific information the market likely doesn't
3. **Typical adjustment magnitude** — rarely adjust by more than ±15% from market price
4. **Respect the wisdom of crowds** — markets aggregate many independent estimates; overriding them requires strong evidence

### When to Trust Markets More vs Less

**Trust more:**
- High trading volume (>$10K on Polymarket, >1000 traders on Manifold)
- Binary questions with clear resolution criteria
- Events in the near future (<1 month)
- Well-known topics (US politics, major sports)

**Trust less:**
- Low volume / few traders (<50 traders)
- Ambiguous resolution criteria
- Long time horizon (>6 months)
- Niche topics (Chinese rankings, local events)
- Markets just created (price hasn't stabilized)

## API Access Patterns

### Manifold Markets API
```
GET https://api.manifold.markets/v0/slug/{market-slug}
Response includes: probability, pool, volume, closeTime
```

### Polymarket (CLOB)
```
Market data available via Polymarket CLOB API
Requires parsing event/condition IDs from the URL
```

### Metaculus API
```
GET https://www.metaculus.com/api2/questions/{id}/
Response includes: community_prediction, metaculus_prediction
```

## Prediction Tips

- If a question has a Manifold/Polymarket slug and the market is well-traded, lead with the market probability
- For multi-choice questions, the market's top option is correct ~60-70% of the time
- For binary yes/no questions, markets with >80% probability are correct ~85% of the time
- Late-stage market movements (within hours of resolution) are the most informative
- Chinese ranking questions typically don't have prediction markets — rely on ranking skills instead
- Market manipulation is rare on small markets (<$10K) but possible; cross-reference when possible
- Polymarket prices embed a crypto-native risk premium that slightly distorts implied probabilities

## Integration with Prediction System

When a task arrives with a non-null `metadata.slug`:
1. First, fetch the current market price from the URL
2. Use this as your primary probability anchor
3. Then apply domain-specific skill analysis to potentially adjust
4. Document both the market price and your adjusted prediction in your reasoning
