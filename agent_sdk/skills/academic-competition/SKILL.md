---
name: academic-competition
description: "Predicts outcomes of academic competitions, math olympiads, programming contests, and educational events. Covers USAMO/USAJMO cutoff scores, ICPC World Finals qualifiers, IMO results, Science Olympiad, and other academic competitions. Use this skill when predicting competition cutoffs, team qualifications, or academic competition outcomes — triggered by mentions of USAMO, USAJMO, AMC, AIME, ICPC, IMO, olympiad, math competition, programming contest, Science Bowl, or any academic competition result."
---

# Academic Competition Prediction

## When to Use

- Predicting USAMO/USAJMO cutoff scores
- Forecasting ICPC World Finals qualifying teams
- Estimating Math Olympiad results or cutoffs
- Predicting programming competition outcomes
- Any academic competition result or threshold prediction

## Data Sources

- **Art of Problem Solving (AoPS)**: Community discussion forums with historical cutoff data and real-time predictions
- **ICPC official site (icpc.global)**: Regional results and qualification criteria
- **MAA (Mathematical Association of America)**: Official AMC, AIME, USAMO announcements
- **Codeforces / Competitive Programming**: Track records of programming teams
- **CP-Algorithms**: Programming competition community data
- **Historical cutoff databases**: AoPS wiki has comprehensive historical data

## Methodology

### Cutoff Score Predictions (USAMO, USAJMO)
1. **Historical cutoff trends** — USAMO cutoffs have been in 215-240 range (AMC 12 + AIME composite) historically
2. **Test difficulty assessment** — AoPS community discussion post-test gives immediate difficulty read
3. **Score distribution modeling** — AMC 12 scores follow approximate normal distribution; AIME scores are right-skewed
4. **Composite calculation** — USAMO cutoff = 10 × AMC 12 score + AIME score
5. **Qualifying pool size** — MAA qualifies ~250-270 students for USAMO each year (roughly fixed)

### USAMO Cutoff Specifics
- AMC 12A + AIME I path vs AMC 12B + AIME I path may have different cutoffs
- Historical composite cutoffs: typically 215-245 range
- Harder AMC/AIME years → lower cutoffs; easier years → higher cutoffs
- AoPS community predictions converge to within ±5 points of actual cutoffs within 48 hours of AIME

### ICPC Qualification Predictions
1. **Regional results** — check North American Regional Contest results 
2. **Historical qualifying teams** — MIT, Waterloo, CMU consistently qualify
3. **Number of qualifying spots** — North America gets ~12-15 spots typically
4. **University track record** — schools with strong competitive programming programs (MIT, CMU, Stanford, Waterloo) are reliable qualifiers
5. **Regional diversity rules** — ICPC has rules to ensure geographic diversity

## Prediction Tips

- For USAMO cutoffs: check AoPS forums where students report their scores and community members run crowd-sourced estimates
- Strong predictor schools for ICPC: University of Waterloo, MIT, CMU, and Stanford qualify almost every year (>80% base rate)
- AMC 12B + AIME I cutoff and AMC 12A + AIME II cutoff are often similar but not identical
- "Will MAA release cutoffs by date X?" — MAA typically releases within 2-3 weeks of AIME; check their announcement calendar
- ICPC qualifications depend on the specific year's regional structure — verify the current season's rules
- For "which teams will qualify": start with the historical regulars and then check this year's regional performance

## Example Predictions

**Input**: "What will be the 2026 USAMO cutoff for AMC 12B and AIME I?"
**Approach**: Check AoPS community threads for 2026 AMC 12B difficulty assessment and 2026 AIME I difficulty. Compare to historical years with similar difficulty. If both tests were of moderate difficulty, expect cutoffs in the 330-345 range (composite = 10 × AMC12B + AIME I). Adjust based on community score reports and estimates.

**Input**: "Which North American teams will qualify for the 2026 ICPC World Finals?"
**Approach**: Look up 2026 NAC (North American Championship) results. MIT, Waterloo, and CMU are almost always in. Check which other schools performed well at regionals. Historical 80%+ qualifiers: University of Maryland, Georgia Tech, Stanford.
