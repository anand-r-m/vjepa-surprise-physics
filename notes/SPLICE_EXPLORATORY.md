# Splice-detector analysis (EXPLORATORY, post-hoc, not preregistered)

Script: `scripts/splice_exploratory.py` (runs in about 5 min, CPU). Output: `results/analysis/exploratory/splice_EXPLORATORY.json`, `figures/splice_EXPLORATORY_post-hoc.pdf`.
Inputs: stored clean M1 fp16 run `results/raw/p4_clean_m1/.../P4_M1_ipdev_clean_s1` (its B1/B2 arrays), M0r clean init0/1/2, `results/raw/g2_controls` M1 vflip/hflip/reversal, dev pixels in `kaggle/datasets/intphys-dev-npz`. Frozen scoring (`vjepa_study.analysis.prereg`) is imported, not edited: mean aggregation, tau_m = 2e-4 x median of the 360 per-video scores of that method, tie-half primary, strict reported. Edited runs use the clean tau_m of the same model. CIs: scene-cluster bootstrap stratified by block (10,000 resamples, prereg seed) or Wilson for counts. No run ids are new; no GPU was used. These numbers are not in VERIFIED.json.

Fixed before looking at outcomes (also in the script docstring): splice position = first native frame where the impossible video leaves its paired possible video (derived by exact pixel equality against the quadruplet's possible videos); bins = terciles of that frame over 180 pairs (<=43.7, 43.7 to 53.3, >53.3; 60 pairs each); verdict rule = hypothesis "supported" only if E1 (Spearman of M1 margin vs B2 margin, CI lower bound > 0) and E2 (M1 accuracy on B2-right minus B2-wrong pairs, CI lower bound > 0) both hold, "not supported" if neither, else "inconclusive".

## Reproduction checks
- Clean M1 fp16: 80.8 tie-half / 81.1 strict; B1 58.1; B2 76.1 (0 ties). Matches `notes/P4_CLEAN_G2.md`.
- Pixel structure: 90 of 90 quadruplets; every impossible frame is byte-identical to a frame of exactly one possible video of its quadruplet, and the frame-0 source is always the pair's own possible video. **120 single (one switch) and 60 double (out-and-back) impossible videos, 0 other**; 40 single and 20 double per block. Switch frame t1: min 16, median 49, max 88. Median double-splice insert length 9.5 frames.

## (1) Margin correlation, M1 vs baselines (180 pairs)
| pair | Spearman (95% CI) | Pearson (95% CI) |
|---|---|---|
| M1 vs B2 | 0.54 (0.42, 0.64) | 0.42 (0.32, 0.54) |
| M1 vs B1 | 0.58 (0.46, 0.68) | 0.48 (0.37, 0.59) |
| B1 vs B2 | 0.87 (0.78, 0.94) | 0.95 (0.92, 0.97) |
| M0r init0 vs B2 | 0.13 (-0.07, 0.32) | |
M1 vs B2 by block: O1 0.76, O2 0.40, O3 0.42 (all CI above 0). Single 0.58, double 0.45. M0r init1 and init2: -0.02 and -0.19 (CIs include 0); M0r is almost all ties, so these are noise-level margins.

## (2) M1 accuracy by whether the baseline is right
| group (n) | M1 tie-half (95% CI) | M1 strict |
|---|---|---|
| B2 right (137) | 91.2 (86.7, 95.4 boot; Wilson 85.3, 94.9) | 92.0 |
| B2 wrong (43) | 47.7 (33.3, 62.2 boot; Wilson 33.6, 62.2) | 46.5 |
| B1 right (101) | 92.1 (86.7, 96.6) | 93.1 |
| B1 wrong (72) | 65.3 (54.7, 75.7) | 63.9 |
| B1 tie (7) | 78.6 | 85.7 |
Right minus wrong: B2 +43.6 pp (28.0, 58.7), strict +45.5 pp; B1 +26.8 pp (14.0, 39.2). Reverse direction: B2 is 86.6% where M1 is right (142), 32.3% where M1 is wrong (31). Joint (M1 tie-half verdicts): both right 123, M1 only 19, B2 only 10, both wrong 21, M1 ties 7. M1 is at chance (47.7%) on the 43 pairs where B2 is wrong; its entire above-chance accuracy comes from pairs where pixel drift also separates the two videos.

## (3) Splice position, single vs double, block
| M1 clean | n | tie-half (boot 95% CI) | strict |
|---|---|---|---|
| early (t1<=43.7) | 60 | 83.3 (75.0, 91.2) | 83.3 |
| middle | 60 | 77.5 (68.6, 86.5) | 78.3 |
| late (t1>53.3) | 60 | 81.7 (73.1, 90.1) | 81.7 |
| single | 120 | 75.0 (68.9, 81.3) | 75.8 |
| double | 60 | 92.5 (86.3, 97.7) | 91.7 |
| O1 / O2 / O3 | 60 each | 75.8 / 81.7 / 85.0 | 75.0 / 83.3 / 85.0 |
- Position: Spearman of M1 margin vs t1 is -0.08 (-0.22, 0.06); distance to clip end is the mirror (+0.08). Tercile 3 minus tercile 1 accuracy is -1.7 pp (-13.2, +10.2). B2 and B1 margins also show no position trend (0.05, 0.03). **No dependence on splice position was found.**
- Single vs double: M1 is 17.5 pp more accurate on double splices (92.5 vs 75.0; difference double-minus-single CI 8.6 to 25.7). B2 shows 78.3 vs 75.0 and B1 50.8 vs 61.7 (B1 near chance on double splices), so the double-splice gain is specific to M1, not shared with the baselines. Double-splice inserts are short (median 9.5 frames), and the splice position does not differ much between types (median t1 45.5 vs 51).
- Peak window: the window with the highest M1 surprise (min over C) contains a switch frame in 73.9% of impossible videos vs 46.9% expected if the peak were uniform over windows, and in 53.9% of the paired possible videos (same frame set). B2: 55.0% impossible, 41.1% possible. So M1's peak is displaced toward the switch region relative to its own possible partner, more than B2's.

## (4) M0r and edited runs
- M0r clean (init0/1/2): 180/180/178 ties, accuracy 50.0%, so the by-splice, by-B2 tables are all 50% and uninformative. The M0r vflip and reversal runs contain possible videos only (180 videos, no impossible members), so no pairwise table exists for them; they were skipped.
- M1 under edits, tie-half accuracy (strict), by B2 right / wrong: clean 91.2 / 47.7; vflip 83.9 (82.2), right 93.8 / wrong 52.3; hflip 83.1 (83.9), 93.1 / 51.2; reversal 74.7 (73.3), 84.7 / 43.0. The B2-right minus B2-wrong gap persists in every edit (+41.5, +41.9, +41.6 pp, CIs above 0).
- Does the correct-verdict set change (strict correctness vs clean)? vflip: 135 correct in both, 11 lost, 13 gained, 21 wrong in both; Jaccard 0.85; McNemar exact p = 0.84; clean vs vflip margin Spearman 0.85. hflip: 139 / 7 / 12 / 22, p = 0.36, Spearman 0.83. Reversal: 123 / 23 lost / 9 gained / 25, p = 0.020, Spearman 0.71; 16 of the 23 lost pairs are B2-right pairs. On the B2-wrong pairs M1 strict accuracy is 46.5 (clean), 46.5 (vflip), 44.2 (reversal).
- Position bins under edits: vflip early/middle/late 90.0 / 75.0 / 86.7; reversal 75.0 / 65.8 / 83.3 (bins use the original t1; in the reversed clip the switch lies at 99 - t1). Spearman of margin vs t1 stays within CIs including 0 (vflip -0.10, reversal +0.08, hflip -0.12).

## What the data show
- M1's per-pair margin is moderately correlated with the margins of the pixel baselines (rho 0.54 vs B2; 0.58 vs B1), while a random-init encoder shows none. M1 is correct about 91% of the time where B2 is correct and at chance (48%) where B2 is wrong. By the pre-stated rule (E1 and E2 both hold) the splice-detector hypothesis is **supported**, in this narrow sense: M1's correct verdicts on IntPhys dev co-occur with pixel-level divergence between the video and its spliced partner.
- M1's accuracy does not vary with where the splice is (terciles, rho -0.08), and the vflip/hflip edits leave the correct set essentially unchanged (McNemar p 0.84 / 0.36). Reversal costs 14 net pairs (p = 0.02), concentrated in B2-right pairs.
- M1 is much better on double splices (92.5%) than on single (75.0%), and B2 is not.

## What the data do not show
- They do not show that M1 detects the splice discontinuity itself rather than the same scene change that B2 sees. In IntPhys the violation is realised by the splice, so B2 correctness and M1 correctness are both functions of how large the swapped-in content is; the correlation cannot separate "detects the cut" from "detects the changed object state". A causal test would need splice-free impossible videos, or an inserted splice into a possible video, neither of which exists here (no GPU, and not in the frozen design).
- The margin is not shown to be unrelated to physics: M1 is at chance only on a 43-pair subset defined by B2 failing, and B2 itself may fail for reasons unrelated to M1.
- The no-position and no-vflip-change results are absences of evidence at n = 180 (position CI roughly +-0.14 in rho); they are compatible with, but do not prove, a position-independent splice cue.
- All results are post-hoc and descriptive. Tercile bins, the verdict rule and the correlation set were fixed before the outcome tables were read; the peak-window analysis, the single/double split and the edited-run tables were added in the same pass with no tuning. Multiple comparisons are not corrected. The vflip/reversal arrays are fp16 GPU runs; M0r edited runs have no impossible videos.
- B1 and B2 margins are strongly correlated (rho 0.87), so "M1 tracks B2" and "M1 tracks B1" are almost the same statement; B1 is the weaker discriminator (58%) yet M1's margin correlates with it slightly more than with B2.
