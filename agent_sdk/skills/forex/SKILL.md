---
name: forex
description: "Predicts foreign exchange rates, currency pair movements, and central parity rates. Covers major currency pairs (EUR/USD, GBP/USD, USD/CNY, USD/JPY), PBoC central parity rates (中间价), and cross rates. Use this skill when predicting exchange rates, currency values, or central parity rates — triggered by mentions of exchange rate, forex, currency pair, 中间价 (central parity), GBP/CNY, USD/CNY, or phrases like '100 units of British Pound in Chinese Yuan'."
---

# Foreign Exchange Rate Prediction

## When to Use

- Predicting PBoC central parity rates (人民币汇率中间价)
- Forecasting major currency pair levels (EUR/USD, GBP/USD, USD/JPY)
- Predicting cross rates (GBP/CNY, EUR/JPY)
- Any foreign exchange rate prediction

## Data Sources

- **PBoC (中国人民银行)**: Official daily central parity rates published at 9:15 AM CST
- **SAFE (国家外汇管理局)**: China's official forex administration
- **Forex Factory**: Economic calendar and real-time rates
- **Bloomberg / Reuters**: Professional FX data
- **TradingView**: FX charts and technical analysis
- **OANDA**: Historical exchange rate data
- **Interest rate differentials**: Central bank rate differences drive longer-term FX moves

## Methodology

### Central Parity Rate Predictions (人民币中间价)
1. **Previous day's fixing as anchor** — the PBoC sets rates daily with limited deviation
2. **Counter-cyclical factor** — PBoC uses a counter-cyclical factor to limit volatility
3. **Overnight offshore CNH movement** — USD/CNH overnight changes signal the next fixing direction
4. **Basket reference** — PBoC references a basket of currencies (CFETS RMB Index)
5. **Typical daily change** — central parity rates move by ±0.05-0.3% per day for major currencies

### Short-term FX Predictions
1. **Current spot rate** — best predictor of the near-future rate
2. **Interest rate differentials** — higher-yielding currencies appreciate in carry trade environments
3. **Economic data surprises** — CPI, employment data that beat/miss expectations move currencies
4. **Central bank signals** — hawkish vs dovish forward guidance
5. **Risk sentiment** — "risk off" episodes strengthen USD, JPY, CHF

### Technical Approach
1. **Support/resistance levels** — round numbers (e.g., GBPUSD 1.30) act as psychological barriers
2. **Moving averages** — 50-day and 200-day MA crossovers signal trend changes
3. **Implied volatility** — FX options volatility indicates expected range

## Currency-Specific Notes

### USD/CNY (美元/人民币)
- Managed float with ±2% daily trading band around central parity
- PBoC intervenes to prevent excessive depreciation/appreciation
- Trade war rhetoric and capital flow concerns are key drivers

### GBP/CNY (英镑/人民币)
- Cross rate = GBP/USD × USD/CNY
- Answer format often requested as: "100 GBP = XXX.XX CNY"
- GBP influenced by BoE rate decisions and UK economic data

### EUR/USD
- Most traded pair globally; most liquid
- ECB vs Fed policy divergence is the primary driver

## Prediction Tips

- For central parity rate predictions, the daily change is small — predict within ±0.5% of previous fixing
- "100 units of X in CNY" format: check the previous day's rate, apply expected small change
- Weekend events (geopolitics, central bank speeches) can cause Monday gap openings
- Month-end and quarter-end flows can temporarily distort rates by 0.1-0.3%
- Carry trade dynamics mean high-yield currency advantage persists for weeks/months
- For same-day predictions, the rate is already set by 9:15 AM CST — just look it up if possible

## Example Predictions

**Input**: "What will be the value of 100 units of British Pound at the central parity rate?"
**Approach**: Check the most recent PBoC GBP/CNY fixing. The next day's fixing will be very close (±0.3%). If yesterday's fixing was 940.50, predict approximately 938-943 range. Check overnight GBP/USD movement for directional bias.
