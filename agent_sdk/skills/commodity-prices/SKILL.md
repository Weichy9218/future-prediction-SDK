---
name: commodity-prices
description: "Predicts commodity prices and agricultural product price indices. Covers crude oil, lumber, gold, pork, agricultural indices, and other physical commodities. Use this skill when predicting commodity closing prices, price ranges, volatility levels, or agricultural price indices — triggered by mentions of crude oil, lumber, gold, pork, commodity price, agricultural index, Trading Economics, futures, or references to wholesale market prices or price indices from organizations like China's Ministry of Agriculture."
---

# Commodity Price Prediction

## When to Use

- Predicting closing prices for traded commodities (lumber, crude oil, gold)
- Forecasting commodity price volatility
- Predicting agricultural product price indices (China agricultural 200 index, pork prices)
- Any commodity-related price or index prediction

## Data Sources

- **Trading Economics**: Real-time commodity prices and historical data
- **CME Group**: Futures prices for major commodities
- **China Ministry of Agriculture (MOA)**: Agricultural product wholesale price indices
- **USDA / FAO**: Global agricultural commodity reports
- **EIA (Energy Information Administration)**: Oil and energy forecasts
- **Bloomberg / Reuters**: Commodity market data and analysis

## Methodology

### Short-term Price Predictions (days to weeks)
1. **Current price as anchor** — the best predictor of tomorrow's price is today's price
2. **Futures curve** — check the forward curve; contango (upward) vs backwardation (downward) signals market expectations
3. **Recent trend** — calculate 5-day and 20-day moving averages; trend-following has weak but positive predictive power
4. **Volatility regime** — in high-volatility periods, prediction intervals widen significantly
5. **Supply/demand news** — OPEC decisions, weather events, trade policy changes

### Price Range/Level Predictions
1. **Calculate historical daily range** — use ATR (Average True Range) for the commodity
2. **Apply range to current price** — typical lumber daily change is ±2-3%, crude oil ±1.5-2%
3. **Widen confidence intervals** — for multi-day predictions, uncertainty grows roughly with √(days)

### Agricultural Index Predictions
1. **Seasonal patterns** — agricultural prices have strong seasonal cycles (harvest timing)
2. **Recent index trend** — check the last 5-10 data points for direction
3. **Weather impact** — extreme weather events (drought, flooding) cause price spikes with 2-4 week lag
4. **Policy changes** — government subsidies, import/export restrictions affect prices

## Commodity-Specific Tips

### Lumber
- Highly seasonal: peaks in spring (construction season), dips in winter
- Volatile — daily swings of 3-5% are normal
- Housing starts data is a leading indicator
- Typical range: $400-$700 per thousand board feet in 2024-2026

### Crude Oil
- OPEC+ production decisions are the dominant short-term driver
- Geopolitical risk premium can add $5-15/barrel
- OVX (Crude Oil Volatility Index) measures expected volatility
- OVX above 40 indicates a high-volatility regime; above 60 is extremely volatile
- Normal OVX range: 25-35

### Pork (China)
- Strong seasonal cycle: prices rise before Chinese New Year and fall after
- Hog cycle: ~3-4 year price cycle driven by breeding stock dynamics
- Government pork reserves release can temporarily suppress prices
- Typical range: 15-25 yuan/kg

### China Agricultural 200 Index
- Composite index of 200 agricultural products at wholesale markets
- Livestock sub-index is the most volatile component
- Published daily by China's National Agricultural Product Wholesale Market Price Information System
- Moves in narrow ranges most days; seasonal and policy shocks cause breaks

## Example Predictions

**Input**: "What will be the closing price of lumber on 20 March 2026?"
**Approach**: Get current lumber price from Trading Economics, check recent trend direction, apply ±3% daily range uncertainty. If current price is ~$550, the most likely range is $500-$600 for a 1-week forecast. Choose the range bucket that contains the current price.

**Input**: "How high will crude oil volatility get next week?"
**Approach**: Check current OVX level. If currently at 100-110, "Above 120" is plausible (~60%), "Above 150" less likely (~25%), "Above 180" unlikely (~10%), "Above 210" very unlikely (~3%). Key risk events (OPEC meetings, inventory reports) could spike it.
