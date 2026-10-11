# B2 pre-freeze checks (clean P2 fp32 run only)

Script: `scripts/b2_checks.py` (tests: `tests/test_b2_checks.py`). Output: `results/analysis/b2_checks.json`.
Input: `results/raw/p2_clean/results/P2_M1_ipdev_clean_s1/surprise.npz` (360 videos, 180 pairs); frames from `kaggle/datasets/intphys-dev-npz`.
Scoring: per-video score = mean over windows of min over C; tau = 2e-4 x median per-video score of that method (prereg). No edited outputs used.

## Verdict: NO BUG found. B2 = 76.1% is a real property of the clean dev pairs.

## (i) Bug checks
- **Independent recomputation.** A separate loop implementation of B1-windowed and B2 from the frames reproduces the stored arrays for all 360 videos (max abs deviation 9e-8 for B2, 1e-8 for B1). Re-decoding 24 videos from the raw PNGs gives the same frames and the same stored B2 (max dev 7e-8).
- **Label shuffle** (5000 within-pair swaps, seed 20261007, tie-half, mean agg): null mean 50.1% (SD 3.7 pts, 95% band 42.8-57.2%) for B2; observed B2 76.1%, null fraction >= observed = 0.0000. M1 81.7% also 0/5000. B1-windowed 58.1% (p = 0.016), B1-whole 58.6% (p = 0.010). So the scoring/pairing code returns chance when labels carry no signal.
- **Video vs itself.** Frames minus themselves are exactly zero. Scoring any video against itself gives all ties for M1, B1-windowed, B1-whole and B2 (strict accuracy 0.0, tie-half 0.5).
- **Definitions** (spec s2: "B1 Frame-difference surprise: surprise_t = mean |f_t - f_{t-1}|"; "B2 Copy-last-frame error: pixel error of predicting f_t = f_{t-1} over the predicted window").
  - Stored `B1` = `baselines.b1_windows`: `d[s+c-1 : e-1].mean()` with `d[t-1] = |f_t - f_{t-1}|`, i.e. frame difference over the predicted frames p = C..15 of each window. This is the spec's literal B2 wording.
  - Spec B1 over the whole window = `baselines.b1_whole_window` (`d[s:e-1].mean()`), recomputed here.
  - Stored `B2` = `baselines.b2_windows`: `last = f[s+c-1]; mean |f[s+c:e] - last|`, i.e. predict every predicted frame by the last context frame (DECISIONS 2026-10-06: the literal wording collapses to B1, so B2 was defined as copy-last-context-frame).
  - Difference in kind: B1 compares consecutive frames (local motion); B2 accumulates drift away from a frozen context frame (error grows with horizon), so any post-event change that persists (object gone or displaced) adds to B2 over the rest of the window but to B1 only at the change step.

| Clean accuracy, mean agg, 180 pairs | tie-half | strict | ties |
|---|---|---|---|
| M1 | 81.7 | 80.6 | 8 |
| B1 windowed (spec-literal B2 wording) | 58.1 | 57.2 | 7 |
| B1 whole window (spec B1) | 58.6 | 58.3 | 7 |
| B2 copy-last-context | 76.1 | 76.1 | 0 |

Max aggregation: M1 73.1/62.2, B1-windowed 58.3/45.0, B1-whole 57.5/37.8, B2 64.4/42.2 (tie-half/strict; 39-83 ties because tau is scale-relative).
(Note: M1 strict is 80.6 here and 80.6 in DECISIONS; the 80.55 in the JSON is the same number.)

## (ii) Artifact check (IntPhys dev possible vs impossible)
- Container: dev videos are **PNG image sequences** (scene_###.png, RGB, 288x288, lossless, no metadata chunks), not video files. No codec or bitrate exists; ffprobe and cv2 are not installed, so PIL and file sizes were used.
- Frame count: 100 for all 360 videos. AUROC of frame count = 0.5 (no variation).
- File size: pooled AUROC 0.500, pair accuracy 50.0% (90/180). Within **every one of the 90 quadruplets the summed PNG bytes of the two possible videos equal those of the two impossible videos exactly** (0 byte difference), i.e. the quadruplet design balances any additive per-frame property between classes.
- Splice jumps (mean abs pixel change between consecutive native frames; "near event" = +-3 frames around the first frame where the pair members diverge; divergence frame: min 16, median 49, max 88, always found):

| feature | pooled AUROC (360 videos) | pair acc tie-half (strict) | sign-test p | mean poss -> imp |
|---|---|---|---|---|
| max jump, whole clip | 0.535 | 60.6 (37.2), 84 equal pairs | 1e-4 | 4.99 -> 5.12 |
| mean jump, whole clip | 0.514 | 58.3 (58.3) | 0.030 | 1.603 -> 1.605 |
| max jump near event | 0.579 | 62.5 (45.0), 63 equal pairs | <1e-3 | 1.12 -> 1.27 |
| mean jump near event | 0.537 | 59.4 (59.4) | 0.014 | 0.903 -> 0.922 |

  Reading: no encoding, length or file-size cue. Frame-to-frame jumps give a weak cue (pair accuracy 58-63% tie-half; pooled AUROC 0.51-0.58), about the level of B1 (58%), far below B2 (76%). Ties inflate the tie-half figure of the max-jump features (the maxima are often shared prefix frames). Per-block values are in the JSON.
- Interpretation of B2: B2 is not explained by a trivial encoding/length/size cue; it reads genuine post-event pixel divergence between a possible video and its prefix-sharing impossible partner (the impossible video's scene state differs from the possible one, e.g. an object disappearing, moving differently, or being replaced), accumulated against a frozen context frame. That is real signal available to pixel-only methods in IntPhys pairs, not a bug. It raises the bar for H2 (D vs B2), as already noted in DECISIONS.

## (iii) Accuracy by condition (mean agg, tie-half / strict; tau fixed from all 360 videos)
Metadata: dev folders hold only `status.json` (is_possible). Visible/occluded and static/dynamic_1/dynamic_2 are encoded in the **scene folder names of `starting_kit.zip` dev/task.txt** (e.g. `O1/09_test_occluded_static_nobj2`), mapped by block and scene number.

| group | n pairs | M1 | B1 windowed | B2 copy-last |
|---|---|---|---|---|
| all | 180 | 81.7 / 80.6 | 58.1 / 57.2 | 76.1 / 76.1 |
| visible | 90 | 86.7 / 85.6 | 56.7 / 55.6 | 76.7 / 76.7 |
| occluded | 90 | 76.7 / 75.6 | 59.4 / 58.9 | 75.6 / 75.6 |
| static | 60 | 76.7 / 76.7 | 58.3 / 58.3 | 76.7 / 76.7 |
| dynamic_1 | 60 | 87.5 / 86.7 | 58.3 / 56.7 | 78.3 / 78.3 |
| dynamic_2 | 60 | 80.8 / 78.3 | 57.5 / 56.7 | 73.3 / 73.3 |
| O1 | 60 | 75.8 / 73.3 | 58.3 / 58.3 | 68.3 / 68.3 |
| O2 | 60 | 83.3 / 83.3 | 58.3 / 58.3 | 78.3 / 78.3 |
| O3 | 60 | 85.8 / 85.0 | 57.5 / 55.0 | 81.7 / 81.7 |
| O1 visible / occluded | 30 each | 81.7 / 70.0 | 56.7 / 60.0 | 70.0 / 66.7 |
| O2 visible / occluded | 30 each | 85.0 / 81.7 | 60.0 / 56.7 | 76.7 / 80.0 |
| O3 visible / occluded | 30 each | 93.3 / 78.3 | 53.3 / 61.7 | 83.3 / 80.0 |

(B1 whole-window and strict values for every cell are in the JSON.) Descriptive only; cells of 30 pairs have a binomial SE of about 8 points. B2 is roughly equal across visible and occluded (76.7 vs 75.6) and rises from O1 to O3; M1 is higher on visible than occluded.

## (iii) Splice finding (critic frame-hash check, clean dev PNGs, pixels only)
- In 90/90 quadruplets the multiset of frames of the two impossible videos equals that of the two possible videos; every impossible frame at time t is byte-identical to one of the two possible frames at the same t.
- 120 of 180 impossible videos are a single splice (prefix of one possible video + suffix of the other); 60 (20 per block, dynamic_2) switch twice.
- Consequences: any per-frame, order-free statistic is at chance by construction (the artifact check had no power beyond this); B2's 76.1% is a splice/discontinuity detector (scene difference between the two possible videos against a frozen pre-splice frame); about one third of pairs (the double splices) will be transient under the t*_off rule of prereg section 4, expect that count in the report.
