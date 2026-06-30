---
name: stock-market
description: "Predicts stock prices, market indices, and equity market metrics including market capitalization, daily highs/lows, and index levels. Covers Chinese A-shares (SSE, SZSE), US markets (S&P 500, NASDAQ), Hong Kong Stock Connect, and global indices like CSI 300. Use this skill when predicting stock closing prices, daily highs/lows, market capitalization, index values, or fund NAV — triggered by mentions of stock, share price, market cap, index, CSI 300, SSE, SZSE, Ping An Bank, agricultural bank, fund LOF, Stock Connect, or any specific equity ticker."
---

# Stock Market & Equity Prediction

## When to Use

- Predicting stock daily highs/lows or closing prices
- Forecasting market index levels (CSI 300, S&P 500)
- Estimating market capitalization for specific stocks
- Predicting Stock Connect (港股通/沪港通) trading volumes
- Any equity market metric prediction

## Data Sources

- **Wind / Choice (东方财富)**: Chinese market real-time data and historical prices
- **Shanghai Stock Exchange (SSE)**: Official market data, Stock Connect statistics
- **Shenzhen Stock Exchange (SZSE)**: Official market data
- **Yahoo Finance / Google Finance**: US and international market data
- **TradingView**: Technical analysis and price charts
- **Bloomberg / Reuters**: Professional market data terminals
- **Xueqiu (雪球)**: Chinese retail investor sentiment

## Methodology

### Daily Price Predictions (High/Low/Close)
1. **Previous close as baseline** — today's price centers around yesterday's close
2. **Pre-market / overnight signals** — futures, overseas markets, overnight news
3. **Historical daily range** — calculate average daily range as % of price: Chinese A-shares typically ±1-3%
4. **Earnings / events** — check if the company has earnings, ex-dividend, or other events today
5. **Technical levels** — support/resistance from recent price action (not highly predictive but useful for ranges)

### Index Level Predictions
1. **Current level** — the index's current value is the best starting point
2. **Overnight signals** — if predicting CSI 300 for tomorrow, check S&P 500 tonight and futures
3. **Macro calendar** — check for economic data releases (CPI, PMI, employment)
4. **Seasonal patterns** — end-of-quarter, end-of-year window dressing effects
5. **Prediction window** — for same-day predictions, range narrows; for next-week, wider

### Market Capitalization
1. **Current market cap** = shares outstanding × current price
2. **Price change estimate** — apply expected daily return range
3. **Note**: market cap changes only through price changes (and occasionally share issuance/buyback)

### Stock Connect Volume
1. **Historical average** — average daily buy/sell value over past 20 trading days
2. **Trend adjustment** — is there a recent trend in northbound/southbound flows?
3. **Market sentiment** — strong market moves increase trading volumes
4. **MSCI / index rebalancing** — rebalancing dates cause volume spikes

## Prediction Tips

- Chinese A-shares have ±10% daily limit (±20% for STAR Market/ChiNext); prices can't exceed these bounds
- CSI 300 daily range is typically 0.5-2% from open
- Market cap predictions boil down to price predictions — use the stock's recent price and volatility
- For "daily high" predictions, estimate as current price + 1-2× ATR (Average True Range)
- Friday afternoon volumes tend to be lower; Monday opens can gap from weekend news
- Stock Connect flows are influenced by mainland vs HK market valuation gaps
- For fund LOF prices, the intraday price can deviate from NAV due to market sentiment (premium/discount)
- Shanghai SSE trading hours: 9:30-11:30, 13:00-15:00 (China Standard Time)

## Example Predictions

**Input**: "What will be the total market cap of Ping An Bank (000001) on SZSE?"
**Approach**: Get current Ping An Bank price and shares outstanding. Calculate current market cap. Apply ±2% range for the target date. Format answer in 亿元 (hundred millions of yuan) to two decimal places.

**Input**: "What will be the low for CSI 300 today?"
**Approach**: Get current CSI 300 level. Historical daily low is typically 0.5-1.5% below the open. Check overnight signals (US market, Asian futures) for directional bias. Estimate low = current level × (1 - expected drawdown%).
