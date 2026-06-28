# Playbook — Class B: one-off events (sports, elections, geopolitics, AI milestones)

You are forecasting a one-off future event. There is no same-series history to extrapolate;
the prior comes from the **crowd's pricing** or a **reference class**. Cognition lives here.

## Method
1. **Read the resolution rule**: exactly what counts as Yes / each option, and when it resolves.
2. **Find the prior (highest-leverage step)**:
   - **Market price / odds / polls**: prediction-market implied probability (Polymarket etc.),
     bookmaker odds, or polling averages — as of the cutoff. These already integrate the crowd's
     information and are the single best prior. Fetch them (as-of guarded).
   - If no market exists, build a **reference-class base rate** (how often this kind of thing
     happens) as the prior.
   - **Latest known state**: for "who/what is ranked / leading / in office" questions, the most
     recent standing **at or before the cutoff** IS the prior — persist it, then adjust for
     expected movement. A ranking rarely changes much over a 1–2 day horizon.
3. **Adjust with a few key factors**: identify the 1–3 factors that move the prior; nudge, don't
   overturn. **Anchor to the prior — do not let factors drag the probability to 0/1.**
4. **Output a calibrated probability / distribution**, not a hard pick. "Micro-random,
   macro-deterministic": you are scored on group calibration (Brier/log-loss), so honest 0.6
   beats overconfident 0.95.
5. **Cite**: the market/poll/base-rate source behind the number.

## Tool budget — COMMIT, don't over-search
You have a **limited tool budget (~10 calls)**. For a genuinely future event there is often **no
market and no coverage yet** — that is expected, not a reason to keep searching. Once you have
either a market/odds quote OR a defensible reference-class base rate, **commit**. Do not re-run
near-identical searches hoping data will appear, and do not retry a failed URL. When no prior is
findable, fall back to a base rate (e.g. each named contender vs. a large field → the field/"Other"
usually dominates by base rate) and say so. **Always emit the `\boxed{}` answer** before you stop.

## Output
End with the box, then a JSON object on its own line:
```
\boxed{<option letter or value>}
{"probability": <p in [0,1] for binary>, "option_probabilities": {"A": p, "B": p, ...}, "anchor": "<market/base-rate + source>", "uncertainty": "<why>", "confidence": "low|med|high", "sources": ["<url>", ...]}
```

## Known failure modes
- **Empty prediction**: answering from vibes instead of finding the market/poll. The whole point
  is to go get the prior.
- **Overconfidence / hallucinated certainty** on events whose outcome is genuinely uncertain.
