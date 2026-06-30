---
name: space-event
description: "Predicts outcomes of astronomical events, space missions, spacecraft observations, and celestial phenomena. Covers asteroid flyby observations, interstellar object detections, spacecraft mission milestones, rocket launches, and space-related discoveries. Use this skill when predicting whether a space event will occur, observation results, mission success/failure, or astronomical detection outcomes — triggered by mentions of asteroid, interstellar object, spacecraft, rocket launch, space mission, NASA, ESA, observatory, Jupiter, comet, 3I/ATLAS, Oumuamua, or any space/astronomy prediction."
---

# Space Event & Astronomical Prediction

## When to Use

- Predicting interstellar object observation outcomes (3I/ATLAS, Oumuamua-like)
- Forecasting rocket launch success/schedules
- Predicting spacecraft mission milestones
- Estimating astronomical observation results
- Any space or astronomy event prediction

## Data Sources

- **NASA JPL Small-Body Database**: Orbital elements and close approach data
- **Minor Planet Center (MPC)**: Discovery announcements and orbital updates
- **SpaceFlightNow**: Launch schedule and tracking
- **Heavens-Above**: Satellite and spacecraft visibility predictions
- **The Astronomer's Telegram (ATel)**: Time-critical astronomical observations
- **arXiv astro-ph**: Pre-print research papers on observations  
- **Amateur astronomer networks**: AAVSO, BAA for optical observations
- **Prediction markets**: Manifold, Metaculus for space mission milestones

## Methodology

### Interstellar Object Observations
1. **Check object trajectory** — JPL Horizons system provides precise ephemeris data
2. **Observation feasibility** — can ground-based or space telescopes see it at the time?
3. **Signal detection probability** — for RF signatures, consider power output, distance, receiver sensitivity
4. **Historical precedent** — only 2 interstellar objects confirmed (Oumuamua 2017, Borisov 2019); no RF detected from either
5. **Physical constraints** — natural objects don't produce radio signals; this prediction tests the "alien artifact" hypothesis

### Rocket Launch Predictions
1. **Launch provider track record** — SpaceX ~98% success rate, others vary
2. **Weather constraints** — ~30% of launches delay due to weather
3. **Vehicle maturity** — maiden flights have ~85% success; operational vehicles ~95-98%
4. **Range schedule** — check for conflicts at the launch site

### Mission Milestone Predictions
1. **Mission timeline** — compare current status to planned milestones
2. **Phase completion rates** — most mission phases complete successfully for mature agencies
3. **Technical complexity** — novel maneuvers (e.g., asteroid sample return) have higher failure risk

## Prediction Tips

- For "will X produce an RF signature" tipo of questions: the base rate for detecting non-natural radio signals from space objects is essentially 0% so far. Predict "No" with very high confidence (~99%) unless there's extraordinary evidence.
- Interstellar objects are confirmed natural (cometary/asteroidal) by spectroscopic observations
- Rocket launch dates slip by 1-7 days ~40% of the time; weeks ~15%
- SpaceX Falcon 9 has the highest launch rate and reliability of any current rocket
- For Jupiter Hill Sphere entry predictions: this is a purely orbital mechanics question — trajectory data from JPL is definitive
- Space mission predictions are highly deterministic (physical trajectories are well-modeled) except for equipment failures

## Example Predictions

**Input**: "Will 3I/ATLAS produce an RF signature during its Jupiter Hill Sphere entry?"
**Approach**: 3I/ATLAS is identified as an interstellar comet. Natural comets do not produce RF signals. While the "alien probe" hypothesis exists in speculation, no interstellar object has ever produced detected RF signals. Predict "No" with ~99% confidence.
