# EXPLORATORY: onset-aligned specificity variant (post-freeze, human-approved Q11)

Everything here is outside the pre-registration. It does not replace or modify the confirmatory H2 (frozen `kaggle/h2_spec_*/matches.json` untouched). Pixels only: no model output was read to build it.

## Onset rule (documented before any model output on these windows exists)
Per pair, D(t) = mean over pixels/channels of |impossible(t) - possible(t)| at 224 px (`amend.divergence`, as in the frozen rule). t_on = first frame with D > theta.
Threshold rule: theta = the smallest value on the grid {0, 0.1, 0.2, 0.3, 0.5, 0.75, 1, 1.5, 2} gray levels (of 255) that (i) is >= the prefix noise floor (99.9th percentile of D over the first 10 frames of all 180 dev pairs) and (ii) gives a defined onset in >= 90% of the 180 pairs. Choosing the smallest feasible value puts t_on at the earliest frame at which the two videos differ, i.e. the splice.

Result: the prefix noise floor is exactly 0 (the first 10 frames of possible and impossible are bit-identical in all 180 pairs), so **theta = 0, i.e. t_on = first frame with D > 0**; 180/180 pairs have a defined onset, no fallback, 0 pairs with t_on > 94.

| theta (gray /255) | frac pairs with onset | median t_on | frac t_on > 94 |
|---|---|---|---|
| 0 | 1.000 | 49 | 0 |
| 0.1 | 1.000 | 49 | 0 |
| 0.2 | 1.000 | 49 | 0 |
| 0.3 | 1.000 | 52 | 0 |
| 0.5 | 0.878 | 53 | 0.063 |
| 0.75 | 0.644 | 53 | 0.069 |
| 1.0 | 0.356 | 52.5 | 0.094 |
| 1.5 | 0.100 | 53 | 0.111 |
| 2.0 | 0.011 | 54 | 0 |

The frozen floor of 2 gray levels (2/255) defines an onset for 1.1% of pairs on this table (the frozen run found 2 of 180 events), which is the design flaw the critic flagged (A1): a whole-frame mean moves by under 1 gray level when a local object changes.

## Matching (same code path as the frozen matching)
`scripts/make_onset_matches.py` imports `make_matched_strengths.match_job` / `amend.event_window` / `amend.match_pair` unchanged and only passes tau_D = theta = 0 in place of the frozen tau. Same 180 pairs (same pair ids as the frozen file), res 224, frame step 2, seeds 1-3 for the seeded kinds, mid strength = 1 x s*. t_off follows the frozen rule (a run of >= 5 frames with D <= theta before T). Output (separate file): `kaggle/expl_onset_spec/matches.json`, generated 2026-10-10 about 1.5 h CPU with 6 workers, one run, no tuning.

- Events: 180 data-derived, 0 fallback, 60 transient (t_off < 100, the videos re-converge), t_on range 16-88, median 49; median event length 39 frames.
- m_i (mean D over [t_on, t_off)): median 0.53 gray levels of 255 (IQR 0.39-0.66), no zero. Frozen (random windows): median 0.33. The onset-aligned violations are still sub-gray-level at whole-frame mean, only about 1.6 x larger.
- Achieved ratio at mid (target: median in [0.95, 1.05] and >= 90% in [0.9, 1.1]):

| type | n | median r | frac in [0.9,1.1] | infeasible | target |
|---|---|---|---|---|---|
| lighting_global | 540 | 0.995 | 0.800 | 0 | MISSED (frac 80% < 90%; gain steps near the uint8 rounding step) |
| lighting_local | 540 | 1.000 | 0.983 | 6 | met |
| jolt_base | 540 | 1.000 | 1.000 | 0 | met |
| zoom_base | 180 | 1.000 | 1.000 | 0 | met |

Versus the frozen matching: lighting_global in-band fraction 0.50 -> 0.80 (still short of 0.90; no m_i = 0 pairs now), the others stay met. Per the frozen "match failure" convention lighting_global would be flagged and A excluding it reported.

## Reuse of existing runs as references
Clean possible and impossible videos: `P4_M1_ipdev_clean_s1` (for Delta_viol and the lighting reference). Jolt/zoom reference: existing `P4_M1_ipdev_base_ref-ref_s1` (the base-window reference does not depend on the event time). Hence no base_ref in the new group. The window set for onset-aligned analysis is W_i = {w : 4w + 30 >= t_on} with the new t_on.

Not done here: any model-output analysis of these runs (they are not yet run).
