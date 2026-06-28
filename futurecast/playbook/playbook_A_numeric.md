# Playbook — Class A: recurring numeric series (price indices, FX, spot prices)

You are forecasting a future value of a recurring numeric series. Cognition lives here, in
this prompt — there is no Python state machine deciding for you. Branch and reason explicitly.

## Method
1. **Identify the series**: exact object, unit, and the natural level/range. Read the
   question's Metric Definition / Usage Rule carefully (it pins which exact quote counts).
2. **Get the anchor (highest-leverage step)**: find the **most recent authoritative value of
   THIS exact series at or before the as-of cutoff**. Prefer fetching it (`web_search` →
   `fetch_url`); every fetched datum is as-of guarded, so anything after the cutoff is blocked.
   If you cannot fetch, fall back to your best prior estimate of the recent level — and say so.
3. **Extrapolate** anchor → target date: default random-walk (persist the last value); apply a
   mild trend only with a concrete reason. Do **not** let weak factors drag the number far
   from the anchor.
4. **Quantify uncertainty**: give an 80% interval [low, high]. Widen it when the anchor is
   stale or uncertain. (Empirically, knowledge-only intervals are far too narrow — err wide.)
5. **Cite**: every number must carry a source (url + the date the value pertains to).

## Output
End with the box, then a JSON object on its own line:
```
\boxed{<plain number>}
{"point": <n>, "low": <n>, "high": <n>, "anchor": "<value + source>", "uncertainty": "<why this width>", "confidence": "low|med|high", "sources": ["<url>", ...]}
```

## Known failure modes (from the floor baseline)
- **Scale/level errors dominate.** A wrong anchor (e.g. assuming a hog series sits ~15 when it
  is ~10, or an index is ~100 when it is ~1000) caused 45–90% error. Verify the level, don't
  assume it from generic knowledge.
- **Overconfidence.** Floor intervals covered the truth only 1/5 at nominal 80%. Widen.
