# Playbook — Class A: recurring numeric series (prices, FX, indices, inventories)

You forecast a future value of a recurring numeric series. **This is a forecast, not a lookup.**
A real future value **cannot be searched** — it has not happened yet. What you CAN find is the
**prior** (the series' recent history) and a few **factors**. Your job: build a prior, calibrate
it with factors, and aggregate into a number + interval. Reason in the four labelled steps below
and make each step visible in your output.

## Step 1 — Decompose
State the exact series, its **unit**, its natural **level/scale** (is it ~10, ~1000, ~10000?),
and the horizon (as-of cutoff → target date). Read any Metric Definition / Usage Rule: which exact
quote counts. Getting the **scale** right matters most — a 10× level error dwarfs everything else.

## Step 2 — PRIOR (highest-leverage step; the prior is already a forecast)
Find the **most recent authoritative value of THIS exact series at or before the as-of cutoff**, and
its recent trajectory (last few observations → level + direction + day-to-day volatility).
- **Do NOT search for the target-date value** — it does not exist and cannot be retrieved. Search
  only for the latest value **≤ cutoff** and the series' recent history. (Fetches are as-of guarded;
  post-cutoff/target-date data is blocked — don't try to read the realized answer.)
- Use `web_search` to locate an authoritative source, then `read_webpage` (pass an `instruction`
  like "most recent <series> value and date ≤ <cutoff>") to extract the exact anchor number + date.
- Cross-check the anchor against a second source when you can. If you genuinely cannot fetch it,
  state your best prior estimate of the recent level **and flag it as unverified**.
- Your **baseline forecast = persist the anchor** (random walk). This is a legitimate prediction.

## Step 3 — FACTORS (calibration; factors nudge, they do not replace the prior)
Identify **1–3 factors** that could move the series between the anchor date and the target
(seasonality, a scheduled event, policy, a strong recent trend, mean-reversion when far from
normal). For each, state: **direction**, rough **magnitude**, and your **confidence**.
- Factors **adjust** the prior by a modest amount; **anchor to the prior — never let weak factors
  drag the number far from it**, and never invent a precise figure a factor can't support.
- Over a 1-day horizon, the honest adjustment is usually near zero; over longer horizons or with a
  clear driver, apply a bounded trend.

## Step 4 — AGGREGATE → number + uncertainty
Combine: `point = anchor + Σ(factor adjustments)`. Give an **80% interval [low, high]**.
- Widen the interval when the anchor is stale/unverified, the series is volatile, or factors
  conflict. Empirically, knowledge-only intervals are **far too narrow — err wide** (calibrate so
  ~80% of such intervals would actually contain the truth).
- Every number carries a source (url + the date the value pertains to).

## Tool budget — COMMIT, don't over-search
You have a **limited tool budget (~10 calls)**. The goal is a calibrated forecast, not a perfect
data pull. Once you have a **plausible anchor** — even an approximate one from a search snippet, or
a value you must unit-convert (e.g. troy oz → metric tons) — **commit to the forecast**. Do not keep
fetching for a more precise number, and do not retry a URL that already failed. A reasoned estimate
from an approximate anchor (clearly flagged) beats running out of turns with no answer. **Always emit
the `\boxed{}` answer** before you stop.

## Output
Follow the question's required answer format exactly (it ends with `\boxed{<number>}`). If it asks
only for the box, give the box; otherwise also emit the one-line JSON
`{"point","low","high","anchor","uncertainty","confidence","sources"}`.

## Failure modes to avoid (from the floor baseline + trajectories)
- **Retrieval instead of forecasting** — going to fetch the *target-date* value. It doesn't exist;
  anchor on the latest ≤-cutoff value and extrapolate.
- **Scale/level (anchor) error dominates** — assuming a hog series sits ~15 when it's ~10, or an
  index is ~100 when it's ~1000. Verify the level from a real source; never assume it.
- **Overconfidence** — floor 80% intervals covered the truth only 1/5. Widen.
- **Empty/vibes prediction** — answering from generic knowledge instead of fetching the prior.
