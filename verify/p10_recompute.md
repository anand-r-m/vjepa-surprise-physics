# P10 verifier recompute (exploratory splice analyses), written before opening the analyst's outputs

Script: `verify/p10_recompute.py` (own code, uses `verify/p7_lib.py`; raw arrays + dev npz pixels only). Output: `verify/p10_recompute.json`.
Conventions: clean M1 = `P4_M1_ipdev_clean_s1` (fp16), per-video score = mean over 17 windows of min over 5 contexts (baselines: min over C of the stored B1/B2 arrays, then mean), tie-half with tau = 2e-4 x median of that method's own per-video scores, bootstrap = 10,000 scene-cluster draws stratified by block, seed 20261015. All of this section is EXPLORATORY.

## 1. Splice structure (dev pixels, exact frame equality at the same native index, 100 native frames)
- 90 scenes, each with 2 possible + 2 impossible videos. All 180 impossible videos have every one of the 100 frames exactly equal to the same-index frame of one of the two possible partners (0 unmatched frames, 0 frames shared by both partners). Each impossible video uses both partners (180/180). So "each impossible dev video is a splice of its possible partners" holds without exception (90/90 quadruplets).
- Single splice (2 segments, one switch): 120. Double splice (3 segments, two switches, a-b-a): 60. Per block: O1/O2/O3 each 40 single + 20 double.
- First switch frame (native index of first frame from the new source): median 49, range 16 to 88 (single: median 51; double: median 45.5). Second switch (double only): median 57.5, range 47 to 80.

## 2. M1 vs baselines, per-pair margins (S_imp - S_pos), 180 pairs
Clean accuracy (tie-half / strict / ties): M1 80.83 / 81.11 / 7; B1 58.06 / 57.22 / 7; B2 76.11 / 76.11 / 0.
Spearman of margins, scene-cluster bootstrap 95% CI: M1 vs B2 rho = 0.541 (0.418 to 0.645); M1 vs B1 rho = 0.577 (0.460 to 0.679).

## 3. M1 tie-half accuracy by baseline correctness (right = margin > tau_b, wrong = margin < -tau_b)
| baseline | n right / wrong / tie | M1 acc on right (CI) | M1 acc on wrong (CI) | difference pp (CI) |
|---|---|---|---|---|
| B2 | 137 / 43 / 0 | 91.24 (86.59 to 95.45) | 47.67 (33.33 to 62.23) | +43.57 (28.04 to 58.82) |
| B1 | 101 / 72 / 7 | 92.08 (86.67 to 96.70) | 65.28 (54.61 to 75.35) | +26.80 (14.29 to 39.40) |

## 4. Single vs double splice (pair = class of its impossible video), tie-half accuracy % (CI)
| | n | M1 | B1 | B2 |
|---|---|---|---|---|
| single | 120 | 75.00 (68.5 to 81.3) | 61.67 (56.6 to 67.2) | 75.00 (68.6 to 81.3) |
| double | 60 | 92.50 (86.3 to 97.8) | 50.83 (50.0 to 52.8) | 78.33 (70.0 to 86.7) |
| single - double (pp) | | -17.5 (-26.1 to -8.7) | +10.8 (+5.4 to +16.5) | -3.3 (-13.6 to +7.2) |

Peak-window-contains-switch-frame (impossible videos, window with the largest windowed score; window w covers sampled frames 2w to 2w+15, i.e. native 4w to 4w+30; first sampled frame at or after the first switch): M1 71.7% (129/180), B1 48.9%, B2 52.2%; uniform-window chance for the same switch frames 43.8%. "Any switch" (double splices count if either switch is in the window): M1 75.6, B1 49.4, B2 55.6. Control, same test on the POSSIBLE partner video (window vs the partner's first switch): M1 53.3, B1 35.0, B2 38.3.

## 5. Splice position terciles (first switch frame; cutoffs 43.67 and 53.33; 60 pairs each), tie-half %
| tercile (switch range) | M1 | B1 | B2 |
|---|---|---|---|
| early (16 to 43) | 83.3 (75.0 to 91.3) | 58.3 (52.0 to 65.6) | 76.7 (67.6 to 85.7) |
| mid (44 to 53) | 77.5 (68.6 to 86.1) | 52.5 (50.0 to 56.4) | 70.0 (61.4 to 78.6) |
| late (54 to 88) | 81.7 (72.9 to 90.0) | 63.3 (55.8 to 71.4) | 81.7 (72.7 to 90.0) |

## 6. Edits, M1 pairwise correctness clean vs edited (both pair members edited; 180 pairs; strict d>0 binary; exact two-sided McNemar)
Mean aggregation (clean accuracy convention):
| edit | acc clean -> edit (strict) | correct both | lost | gained | wrong both | McNemar p |
|---|---|---|---|---|---|---|
| vflip | 81.1 -> 82.2 | 135 | 11 | 13 | 21 | 0.839 |
| hflip | 81.1 -> 83.9 | 139 | 7 | 12 | 22 | 0.359 |
| time reversal | 81.1 -> 73.3 | 123 | 23 | 9 | 25 | 0.020 |
(tie-half accuracy: vflip 80.83 -> 83.89, hflip 80.83 -> 83.06, reversal 80.83 -> 74.72; the tie-half-credit>0.5 binary version gives reversal lost 22 / gained 10, p = 0.050.) Full-clip max aggregation gives vflip lost 11 / gained 23 (p = 0.058), hflip 13 / 17 (0.585), reversal 24 / 31 (0.419); see JSON. The M1 reversal run contains both possible and impossible videos (360; 180 each), so the pairwise test is valid for M1. The M0r reversal and vflip runs contain only the 180 possible videos (labels all 0), so no pairwise accuracy exists for M0r edits.

## 7. Vertical-flip shift of full-clip max surprise, paired by video, edited minus clean
- M1 possible videos (n = 180): S(vflip) - S(clean) < 0 in 143 (79.44%), > 0 in 37 (20.56%); tau_m = 1.0875e-4; detection tie-half 21.11% (37 above tau, 2 ties); sign test p = 6.6e-16. All 360 videos: 273 negative (75.83%), 87 positive. Impossible 180: 130 negative (72.2%).
- M0r init0, possible videos (n = 180): positive in 158 (87.78%), negative 22; above tau 150, ties 16 (tau = 1.704e-4), tie-half detection 87.78%; sign test p = 1.5e-26.

## 8. Released-file recompute (data present: `scratch_data/verify_released_raw`)
Reran `verify/released_dev_accuracy.py`: ViT-H vit-h-rope-vm2m mean 96.67 (174/180), ViT-L vit-l-rope-vm2m mean 89.44 (161/180); output files byte-identical to the earlier committed ones. Status: verified from raw released surprise files.

## 9. Claim in notes/B2_CHECKS.md
Section (iii) says "120 of 180 impossible videos are a single splice ...; 60 (20 per block, dynamic_2) switch twice" and, by implication of the heading, that dev impossibles are splices. Recomputed: 120 single, 60 double, 20 per block, 0 non-splices: reproduced. (The "dynamic_2" assignment of the doubles rests on scene-type metadata that I did not recompute; counts per block are confirmed.)

## 4b. Peak-window variant (added after the comparison; see p10_compare.md)
Native-frame containment (switch frame s with 4w <= s <= 4w+30, either switch, no sampled-frame rounding; uniform-window chance 46.9%): impossible videos M1 73.9%, B1 49.4%, B2 55.0%; possible partner control M1 53.9%, B1 36.7%, B2 41.1%. This reproduces the analyst's definition exactly; the sampled-frame-aligned first-switch-only numbers in section 4 (71.7 / 48.9 / 52.2, chance 43.8) are the stricter reading. Both are reported in VERIFIED (`expl.splice.peak_covers.*`, native-any as value).
