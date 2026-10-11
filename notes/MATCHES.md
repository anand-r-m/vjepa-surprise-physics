# Per-pair magnitude matching (prereg section 4, Q3): matches.json

Generated 2026-10-07 by `scripts/make_matched_strengths.py --dev-root data/intphys_dev/extracted/dev --workers 4` (about 2 h CPU), from IntPhys dev pixels only (no model output, no GPU). Run once, after the freeze, with no tuning, no parameter change and no rerun. Output: `kaggle/h2_spec_a/matches.json`, copied byte-identically to `kaggle/h2_spec_b/matches.json` (the two groups read the same file).

- 180 dev pairs (O1/O2/O3 x scene x p0/p1), res 224, frame_step 2, seeds 1-3 for seeded kinds (lighting_global, lighting_local, jolt_base), zoom_base seed-free.
- tau_D = 0.007843 (= 2/255, the floor; the 99.9th percentile of D over the first 10 frames is below it).
- **Event-window fallback: 178 of 180 pairs.** D(t) never exceeds tau_D = 2/255 = 0.0078 for these pairs (on the 10 pairs spot-checked, max D is 0.5-1.4 gray levels of 255, mean D 0.07-0.23), so by the frozen rule (amend.event_window) t*_on is a seeded uniform draw in the middle 50% of the video and t*_off = T. Only O3/17/p0 and p1 get a data-derived event (t_on 54, t_off 59, transient). m_i is therefore the mean D over a drawn window to the end of the video (median m_i = 0.33 gray levels of 255, IQR 0.12-0.50), not over the real violation. The frozen procedure was executed as written; this is reported, not fixed.
- 4 pairs have m_i = 0 (ratio NaN: 12 of 540 seeded entries, 4 of 180 zoom).

## Achieved ratio r = m_edit / (level x m_i), all pairs (seeded kinds: pairs x 3 seeds)

Target (prereg section 4): median r in [0.95, 1.05] and >= 90% of entries in [0.9, 1.1]. The target applies to the mid (1x) level; low/high are shown for information. "Violation" magnitude m_i is the 1x reference by construction; ratio 1 means the matched abrupt edit equals the violation magnitude.

| type | level | n | median r | IQR | frac in [0.9,1.1] | infeasible | NaN | target |
|---|---|---|---|---|---|---|---|---|
| lighting_global | low | 540 | 0.031 | 0.000-0.741 | 0.100 | 12 | 12 | MISSED |
| lighting_global | mid | 540 | 0.906 | 0.000-0.997 | 0.500 | 12 | 12 | MISSED |
| lighting_global | high | 540 | 1.020 | 0.625-1.162 | 0.239 | 12 | 12 | MISSED |
| lighting_local | low | 540 | 1.009 | 1.000-1.030 | 0.833 | 15 | 12 | MISSED |
| lighting_local | mid | 540 | 1.000 | 1.000-1.000 | 0.967 | 15 | 12 | met |
| lighting_local | high | 540 | 0.976 | 0.905-0.996 | 0.744 | 15 | 12 | MISSED |
| jolt_base | low | 540 | 1.047 | 1.025-1.080 | 0.800 | 12 | 12 | MISSED |
| jolt_base | mid | 540 | 1.000 | 1.000-1.000 | 0.978 | 12 | 12 | met |
| jolt_base | high | 540 | 0.960 | 0.945-0.973 | 0.876 | 12 | 12 | MISSED |
| zoom_base | low | 180 | 1.054 | 1.040-1.074 | 0.817 | 4 | 4 | MISSED |
| zoom_base | mid | 180 | 1.000 | 1.000-1.000 | 0.978 | 4 | 4 | met |
| zoom_base | high | 180 | 0.955 | 0.938-0.964 | 0.872 | 4 | 4 | MISSED |

Per-seed lighting_global mid is identical across seeds 1-3 (median 0.906, 0.500 in band; 62 of 180 pairs have r near 0).

## Match-failure flags (prereg section 4, "match target missed")
- **lighting_global: target MISSED** (mid median 0.906, 50% in band). Cause: m_i is about 0.3 gray levels (median), so the required global gain amount is below the uint8 rounding step and the edit rounds to no change (r about 0 in 62 of 180 pairs). It stays in A, is flagged in the evidence table, and "A excluding lighting_global" is the sensitivity analysis.
- lighting_local, jolt_base, zoom_base: target met at mid (medians 1.000; 96.7%, 97.8%, 97.8% in band).
- M2-resolution (256 px) achieved ratio is not computed here (needs separate matching run; not part of this file).

## Implication to flag
Because 178 of 180 events are fallback draws, "violation magnitude" in H2 is the divergence of a random window, and the matched edits are positioned at that random window, not at the true splice time. This follows the frozen rule (the 2/255 floor is above the dev pairs' per-frame pixel divergence) and touches the scientific meaning of the t*-based analyses. Lead / human decision, no change made.
