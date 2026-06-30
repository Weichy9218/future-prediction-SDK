---
name: shipping-index
description: "Predicts shipping freight rates, indices, and maritime trade metrics. Covers the Baltic Dry Index (BDI), China Coastal Bulk Freight Index (CCBFI), container shipping rates, and product-specific shipping indices. Use this skill when predicting shipping rates, freight indices, or maritime trade costs — triggered by mentions of shipping index, freight rate, Baltic Dry, coastal bulk, Shanghai Shipping Exchange (上海航运交易所), product oil index (成品油货种指数), or container rate references."
---

# Shipping & Freight Index Prediction

## When to Use

- Predicting China Coastal Bulk Freight Index (中国沿海散货运价指数) sub-indices
- Forecasting Baltic Dry Index (BDI) levels
- Estimating container shipping rates
- Any shipping freight rate or index prediction

## Data Sources

- **Shanghai Shipping Exchange (上海航运交易所)**: China Coastal Bulk Freight Index, SCFI (Shanghai Containerized Freight Index)
- **Baltic Exchange**: Baltic Dry Index, tanker rate assessments
- **Freightos Baltic Index**: Container shipping rates
- **Clarksons Research**: Shipping market analytics
- **Marine Traffic / VesselFinder**: Vessel positioning and congestion data

## Methodology

### Chinese Coastal Freight Indices
1. **Previous week's value as anchor** — indices move incrementally week-to-week
2. **Seasonal patterns** — pre-holiday demand peaks (Chinese New Year, National Day), post-holiday dips
3. **Fuel costs** — bunker fuel prices directly affect freight rates (especially product oil index)
4. **Demand signals** — industrial production, construction activity, coal consumption data
5. **Fleet supply** — new vessel deliveries and scrapping affect capacity

### Baltic Dry Index
1. **Iron ore demand** — China is the largest dry bulk importer; steel production drives BDI
2. **Tonnage supply** — check vessel availability and fleet utilization rates
3. **Route-specific analysis** — Capesize vs Panamax vs Supramax markets
4. **Environmental regulations** — IMO regulations affecting sailing speeds and capacity

## Sub-Index Specifics

### Product Oil Index (成品油货种指数)
- Tracks coastal refined petroleum product shipping costs
- Driven by: refinery output, seasonal demand (heating oil vs gasoline), pipeline capacity constraints
- Relatively stable in calm periods; spikes during supply disruptions or holidays
- Typical weekly change: ±1-3%

### Coal Index
- Largest component of CCBFI by volume
- Seasonal: high in winter (heating demand), lower in spring/fall
- Policy-sensitive: government coal price caps and import regulations

## Prediction Tips

- Shipping indices are mean-reverting over medium term but can trend for months
- Chinese holidays cause predictable demand patterns — pre-holiday stocking-up then post-holiday lull
- Geopolitical disruptions (Suez Canal, Red Sea) cause sudden index spikes
- The product oil index is less volatile than coal or grain indices
- For same-week predictions, the previous week's value ± 2-3% is usually the right range
- New IMO environmental regulations create gradual upward pressure on rates

## Example Predictions

**Input**: "What will be the Product Oil Index of the China Coastal Bulk Freight Index?"
**Approach**: Check the most recently published CCBFI product oil sub-index. Apply expected weekly change (±1-3%) based on current fuel prices and demand conditions. Seasonal adjustment if applicable.
