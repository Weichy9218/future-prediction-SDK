---
name: cycling-race
description: "Predicts outcomes of professional cycling races and stage races. Covers one-day Monuments (Milano-Sanremo, Paris-Roubaix, Tour of Flanders), Grand Tours (Tour de France, Giro, Vuelta), and other UCI WorldTour events. Use this skill when predicting race winners, podium finishers, breakaway success, or key moments like mountain summit arrivals — triggered by mentions of cycling, Pogacar, Van der Poel, Philipsen, Poggio, peloton, or any professional road cycling race."
---

# Cycling Race Prediction

## When to Use

- Predicting winners of one-day classics and monuments
- Forecasting Grand Tour stage winners or GC standings
- Estimating specific race scenarios (e.g., "who will be first to summit X")
- Any professional road cycling outcome prediction

## Data Sources

- **ProCyclingStats**: Race histories, rider palmares, current form ratings
- **FirstCycling**: Detailed race results and head-to-head comparisons
- **UCI Rankings**: Official world ranking points
- **Betting odds**: Specialized cycling bookmakers (Unibet, Betfair)
- **Strava / Training data**: Publicly available rider activity (limited)
- **Team rosters**: Start lists and domestique assignments

## Methodology

### One-Day Race Winners
1. **Check betting odds** — they aggregate expert analysis effectively
2. **Historical performance** — how has each rider performed at this specific race before?
3. **Current form** — results in recent races (especially similar profile races)
4. **Course profile analysis** — flat sprint finish vs hilly vs cobblestones greatly narrows the contender list
5. **Team dynamics** — who has the strongest lead-out train? Multiple protected riders?

### Key Race Profiles
- **Milano-Sanremo** (flat with Poggio): Favors sprinters who can survive climbs (Poggio is the decisive point). Breakaway success rate is low (~15%). Usually decided in last 10km.
- **Paris-Roubaix** (cobblestones): Favors powerful time trialists and classics specialists. Mechanical failures and crashes add high variance.
- **Tour of Flanders** (short steep climbs): Favors explosive power riders. The Oude Kwaremont + Paterberg sequence is decisive.

### Key Rider Archetypes
- **Grand Tour GC riders** (Pogacar, Vingegaard): Dominate stage races but also competitive in hilly classics
- **Sprint specialists** (Philipsen, Démare): Only competitive on flat finishes
- **Classics specialists** (Van der Poel, Van Aert): Peak for one-day races, especially cobbled/hilly
- **Time trialists** (Ganna): Breakaway threats on flat courses, TT specialists

## Prediction Tips

- For Milano-Sanremo, the Poggio climb typically drops pure sprinters; look for "fast finishers" who can climb
- The favorite wins a Monument only ~25-30% of the time — these races are high-variance
- Recent winners of similar-profile races in the same season are strong contenders
- Weather (rain, wind, cold) significantly increases variance and favors experienced riders
- In the first 3-5 riders over a decisive climb, 80%+ of winners come from this group
- Pogacar's dominance has made him the default favorite for any hilly race since 2024

## Example Predictions

**Input**: "Milano-Sanremo 2026 Winner?"
**Approach**: Check start list, betting odds. Top contenders typically: Pogacar (if starting), Van der Poel, Philipsen. Poggio arrival order heavily predicts the winner. If Pogacar attacks on Poggio and gaps the field, he's 70%+ to win.

**Input**: "How many of Pogacar, Ganna, MVDP in top 3 at Poggio?"
**Approach**: All three are elite riders who target this race. Historical base rate of a top contender being in the first 3 at Poggio is ~50-60% each. They ride for different teams so are independently competitive. Expect 2 of 3 as the most likely outcome.
