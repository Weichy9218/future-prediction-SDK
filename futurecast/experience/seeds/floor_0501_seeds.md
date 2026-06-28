# Experience seeds (from the knowledge-only floor, experiments/baseline_floor_0501)

These are starter notes for the experience library (kit #4). They are the kind of per-class
calibration fact that, disclosed on demand, fixes the dominant "anchor" error — and that must
NOT be preloaded wholesale (that would leak across questions).

- **futureworld:hog_price** — this dataset's hog series (内三元 / 瘦肉型 / 土杂猪) sits around
  **~10 CNY/kg**, NOT the ~14–16 a model assumes from generic 2024–2025 knowledge. Anchor low.
- **futureworld:commodity_index (大宗商品价格)** — a **~1000-level** index, not a ~100 base.
  A model that assumes ~110 is off by 10×. Verify the scale before extrapolating.
- **calibration (all numeric)** — knowledge-only 80% intervals covered truth only **1/5**.
  Widen intervals substantially until empirical coverage approaches nominal.
- **futureworld:fx_boc (BOC 牌价)** — peg/policy-anchored series (e.g. HKD) move slowly;
  random-walk from the latest quote is strong (floor error ~5% on HKD).
