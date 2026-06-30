---
name: supply-chain
description: "Predicts outcomes related to global supply chains, industrial production, trade flows, and critical mineral/material supply shifts. Covers nickel production, graphite supply chains, lithium, semiconductor supply, and other strategic resource flows. Use this skill when predicting production volumes, supply chain shifts, industrial output thresholds, or strategic material availability — triggered by mentions of supply chain, production target, nickel, graphite, lithium, semiconductor, mining output, industrial production, or specific supply chain metrics."
---

# Supply Chain & Industrial Production Prediction

## When to Use

- Predicting whether production targets will be met (e.g., nickel output exceeding X tonnes)
- Forecasting supply chain geographic shifts
- Estimating industrial production metrics
- Predicting strategic material availability changes
- Any supply chain disruption or capacity prediction

## Data Sources

- **USGS (US Geological Survey)**: Mineral production statistics and reserves
- **IEA (International Energy Agency)**: Critical minerals outlook and supply data
- **Company filings and earnings calls**: Production guidance from mining/industrial companies
- **S&P Global / Wood Mackenzie**: Commodity market and supply chain analytics
- **Trade data (UN Comtrade, customs data)**: Import/export flows
- **Benchmark Mineral Intelligence**: Battery material supply chain tracking
- **Prediction markets**: Manifold for specific production threshold questions

## Methodology

### Production Target Predictions
1. **Company guidance** — what has the company/consortium publicly stated as production targets?
2. **Current production rate** — annualize recent quarterly production data
3. **Ramp-up curves** — new facilities follow S-curve ramp-up; compare to planned timeline
4. **Technical challenges** — metallurgical/processing difficulties can delay targets
5. **Historical delivery track record** — has this company/consortium met past targets?

### Supply Chain Shift Predictions
1. **Quantify "shift"** — define the metric clearly (% of processing, # of new facilities, trade flow changes)
2. **Policy drivers** — Inflation Reduction Act, EU Critical Raw Materials Act, China export controls
3. **Investment pipeline** — $X billion committed doesn't mean operational for 3-5 years
4. **Permitting and construction timelines** — Western mining/processing projects face long permitting delays
5. **Technology readiness** — some alternative processing methods are still at pilot scale

## Prediction Tips

- Mining and industrial production projects routinely miss deadlines by 1-3 years
- "Will production exceed X by date Y" — check if the facility is even operational yet
- New nickel processing facilities (HPAL, RKEF) in Indonesia have had mixed track records
- For "supply chain shift score" type questions, these are typically subjective aggregates — calibrate against the scale definition
- Graphite supply chain shift from China takes decades, not years — 90%+ of processing is still Chinese
- Battery-grade mineral production is more constrained than raw mining; processing is the bottleneck
- For near-term predictions (weeks), production targets that haven't been met yet are unlikely to suddenly be met

## Example Predictions

**Input**: "Will Indonesia-Altilium nickel production exceed 20,000 tonnes by March 22, 2026?"
**Approach**: Check Altilium's current production status. Are they operational? What's their current annual rate? If they're still in commissioning or early ramp-up, 20,000 tonnes is very ambitious. Check company announcements for production updates.

**Input**: "Will the US graphite supply chain shift exceed 50 on a 1-100 scale by March 2026?"
**Approach**: Assess current US graphite processing capacity (very limited). Check if any announced facilities are operational. A score of 50/100 implies a major shift — unlikely given the 3-5 year timeline for new processing facilities. Predict "No" with high confidence.
