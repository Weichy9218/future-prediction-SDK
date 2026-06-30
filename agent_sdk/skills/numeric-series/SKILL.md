---
name: numeric-series
description: Numeric-series forecasting workflow for Futurecast tasks asking for prices, index values, rankings, counts, weather values, or other scalar targets. Use when the answer is a number, interval, bucket based on a number, or extrapolation from historical values.
---

# Futurecast Numeric Series

Use this skill for scalar targets. The latest same-series value before the cutoff is usually the
highest-leverage evidence.

## Workflow

1. Confirm the exact metric definition, unit, geography, source, and target date.
2. Find the latest value at or before the cutoff from the same source or a close official proxy.
3. Check scale: order of magnitude, unit conversions, percent vs percentage points, local timezone.
4. Estimate drift from recent values only if the series is trending or seasonal.
5. Apply known events between cutoff and target only if they are scheduled/known by the cutoff.
6. Return the required numeric format, not a long essay.

## Calibration

- For short horizons, default to a random-walk prior around the latest value.
- Small noisy series changes should not move the point estimate far from the anchor.
- If an interval is requested, make it wide enough for recent volatility; narrow intervals are a
  common failure mode.
- If the target date value appears in a source, treat it as post-cutoff leakage and ignore it.
