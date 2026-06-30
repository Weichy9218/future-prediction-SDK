---
name: public-health
description: "Predicts public health outcomes including disease surveillance data, outbreak statistics, epidemic trends, and health system metrics. Covers influenza monitoring, COVID-19 trends, CDC/ECDC reports, China CDC weekly reports, and other epidemiological data. Use this skill when predicting disease outbreak numbers, influenza-like illness reports, epidemic curve trends, or health surveillance metrics — triggered by mentions of influenza, flu, outbreak, epidemic, pandemic, CDC, China CDC, disease surveillance, ILI (influenza-like illness), weekly health report, or specific disease monitoring systems."
---

# Public Health & Epidemiological Prediction

## When to Use

- Predicting influenza outbreak counts from CDC/China CDC weekly reports
- Forecasting epidemic curve trends (rising, peaking, declining)
- Estimating disease case counts for specific reporting periods
- Predicting public health surveillance metric values
- Any epidemiological data prediction

## Data Sources

- **China CDC (中国疾控中心)**: China Influenza Weekly Report (中国流感监测周报)
- **US CDC FluView**: Weekly US influenza surveillance
- **ECDC (European CDC)**: European surveillance reports
- **WHO FluNet/FluID**: Global influenza monitoring
- **Our World in Data**: Aggregated health data with good visualizations
- **ProMED**: Emerging infectious disease reports
- **HealthMap**: Real-time disease surveillance

## Methodology

### Influenza Outbreak Count Predictions
1. **Seasonal pattern** — influenza follows predictable seasonal curves (Northern Hemisphere peaks Dec-Feb, Southern peaks Jun-Aug)
2. **Recent trend** — check the last 3-4 weekly reports for direction (increasing/decreasing/plateauing)
3. **Current position on epidemic curve** — are we pre-peak, at peak, or post-peak?
4. **Year-over-year comparison** — compare to the same week in previous years
5. **Dominant strain** — H3N2 seasons tend to be more severe than H1N1 or B-lineage seasons

### Epidemic Curve Modeling
1. **SIR/SEIR model baseline** — simple compartmental models give rough trajectory
2. **Reporting delays** — there's typically a 1-2 week delay in surveillance data
3. **Behavioral factors** — holiday travel amplifies transmission; school holidays reduce it
4. **Sub-national variation** — southern provinces may peak at different times than northern

### China-Specific Surveillance
- China CDC publishes 中国流感监测周报 weekly (typically Friday)
- Reports include: sentinel hospital ILI rates, outbreak counts, pathogen subtype distribution
- Outbreak count definition: ≥10 ILI cases in one institution within one week  
- Typical winter peak: 10-40 outbreaks per week nationally
- Spring decline: outbreaks drop to 1-10 per week by late March

## Prediction Tips

- By mid-March in the Northern Hemisphere, influenza season is typically declining
- Week-to-week outbreak counts can be volatile (±50%) even in a clear trend
- If the most recent report showed N outbreaks and it's declining season, predict N × 0.6-0.9 for next week
- School closures (spring break, holidays) dramatically reduce outbreak counts
- New influenza strains can cause anomalous seasons — check CDC/WHO strain characterization updates
- Round numbers are reasonable predictions — the system reports whole-number outbreak counts
- For "how many outbreaks", ranges of 5-15 are typical for late-season reports

## Example Predictions

**Input**: "According to the latest China Influenza Weekly Report, how many outbreaks of influenza-like illness will be reported nationwide?"
**Approach**: Check the most recent available China CDC weekly flu report. If it's mid-March (late season, declining), expect 3-15 outbreaks. If the previous week reported 8, predict ~5-7 for the next week. Check if there are any anomalous strain reports suggesting an unusual pattern.
