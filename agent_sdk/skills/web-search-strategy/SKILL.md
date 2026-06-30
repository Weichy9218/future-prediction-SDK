---
name: web-search-strategy
description: "Provides strategies for effectively searching the web to gather prediction-relevant information. Covers search query formulation, source evaluation, information synthesis, and multi-language search techniques. Use this skill when you need to search the web for current data, recent events, or real-time information to inform a prediction — triggered by any prediction task that requires current information beyond what's available in historical data or the model's training data. Especially important for questions with near-term resolution dates."
---

# Web Search Strategy for Predictions

## When to Use

- Any prediction requiring up-to-date information (events after training data cutoff)
- When historical data alone is insufficient for the prediction
- When the prediction resolution is within days/weeks (current state matters most)
- For rankings, prices, and other real-time data that changes frequently

## Search Strategy Framework

### Step 1: Identify Information Needs
Before searching, list what you need to know:
1. **Current state** — what is the latest value/ranking/status?
2. **Recent trends** — has the situation been changing? In what direction?
3. **Upcoming events** — are there scheduled events that could affect the outcome?
4. **Expert opinion** — what do domain experts predict?
5. **Market prices** — what do prediction or financial markets imply?

### Step 2: Formulate Effective Queries

**For Chinese-language data sources:**
- Use Chinese keywords directly: "豆瓣电影 本周口碑榜 2026年3月"
- Include the platform name in Chinese: "猫眼想看榜", "懂车帝热门榜"
- Add date qualifiers: "最新", "本周", "今日"
- Use the official terminology from the question

**For English-language sources:**
- Use domain-specific terminology: "USAMO cutoff 2026" not "math competition score"
- Include source names: "FlixPatrol Apple TV top 10 March 2026"
- For financial data: include ticker symbols and exchange names

**For prediction markets:**
- Search directly on the platform: "site:manifold.markets [question keywords]"
- Or format the slug URL from question metadata

### Step 3: Source Reliability Hierarchy

| Priority | Source Type | Example | Reliability |
|----------|-----------|---------|-------------|
| 1 | Official/primary data sources | Exchange websites, company filings, government reports | Highest |
| 2 | Established data aggregators | FlixPatrol, TradingView, ProCyclingStats | High |
| 3 | Prediction markets | Manifold, Polymarket, Metaculus | High (for traded markets) |
| 4 | Quality news sources | Reuters, AP, Bloomberg | High |
| 5 | Expert analysis | Think tanks, research reports | Medium-High |
| 6 | Community forums | Reddit, AoPS, Weibo | Medium (verify independently) |
| 7 | Social media | Twitter/X, Weibo | Low-Medium (good for recency) |

### Step 4: Multi-Language Search Strategy

Many prediction questions require searching in the language of the data source:

- **Chinese rankings** (Douban, Maoyan, Dongchedi, KolRank, etc.): Search in Chinese
- **English rankings** (Box Office, FlixPatrol, GitHub, Steam): Search in English
- **Financial data**: Use both Chinese and English terms depending on the exchange
- **Sports**: Usually English for international sports; Chinese for domestic Chinese sports
- **Political events**: Use the local language + English for cross-referencing

### Step 5: Information Synthesis
1. **Cross-reference** — verify key facts across at least 2 sources
2. **Recency check** — ensure the data is current enough for the prediction time horizon
3. **Contradiction resolution** — when sources disagree, favor official/primary sources
4. **Missing data handling** — note what you couldn't find; this itself is informative (if data should exist but doesn't, the event may not have happened)

## Prediction-Specific Search Patterns

### For Ranking Predictions
1. Search for the most recent published ranking
2. Search for the previous 2-3 rankings for trend analysis
3. Search for upcoming releases or events that could disrupt rankings

### For Event Outcome Predictions
1. Search for the latest news about the event
2. Search for expert predictions or analysis
3. Search for prediction market prices
4. Search for official schedules or announcements

### For Numeric Predictions
1. Search for the most recent value of the metric
2. Search for the last 5-10 data points for trend analysis
3. Search for any news that might cause an abnormal change

## Tools Available
- `web_search_tool` / `fetch_webpage` — for real-time web data retrieval
- Existing skill scrapers (in `scripts/`) — for specific ranking data sources
- `prediction_market_analysis` skill — for extracting market probabilities

## Prediction Tips

- For questions resolving in <48 hours, current state is the strongest predictor (~70-90% weight)
- For questions resolving in 1-4 weeks, trends and upcoming events matter more
- When you can't find current data, the most recent available data + trend extrapolation is your best bet
- Schedule-dependent predictions (e.g., "by date X") often come down to: "has it already happened?"
- Don't over-search — 3-5 targeted queries usually suffice. Diminishing returns set in quickly.
