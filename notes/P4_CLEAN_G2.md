# P4 clean + G2 analysis (CPU, frozen analysis code; tag prereg-frozen)

Commands (runs dir = symlinks to results/raw/{p4_clean_m1,p4_clean_m2,g2_controls}/results/*, in the scratchpad):
- `run_analysis.py --models M1 M2 --stages clean h3 --out results/analysis/p4` (tie-half, primary); same with `--tie-mode strict` (`p4/strict/`) and `--tau-scale 0` (`p4/exactties/`).
- `scripts/p4_clean_analysis.py <runs>` (M0r x3, skip-4, B-baselines, fp16 vs fp32) -> `results/analysis/p4/p4_clean_g1.json`.
- **2026-10-10 regeneration (exploratory bookkeeping):** `p4_clean_g1.json` was regenerated with `scripts/p4_clean_analysis.py` unchanged (it already reads `P4_M2_ipdev_clean-mi0_s1`). Only M2-keyed fields (`models.M2`, `tau.M2`, `between_video_sd_of_S.M2`) and `runs_dir` changed versus the committed file; M1, M0r, skip-4, B-baselines (including B1/B2/B3 of M2, whose values are identical), fp16-vs-fp32 and every other field are byte-identical in value. The old mask_index-1 rows are kept in `results/analysis/p4/p4_clean_g1_M2_old_mask_index1.json`. NOT regenerated (frozen driver outputs, left untouched): `p4/clean.json`, `p4/strict/clean.json`, `p4/exactties/clean.json` still carry the OLD M2 row (46.9% tie-half); they need a rerun of `run_analysis.py` with the corrected M2 run before the verifier pass.
- `run_meta_check`: ok, 11 runs, no mismatch, no bypass (`p4/meta_check.json`; precision fp16, 2 GPUs everywhere; heads 606d732 / beea21e both in allowlist).
- No H1 edited stage was run (no edited H1 data). H1 eligibility is a clean-accuracy rule, read from clean.json / the fp32 run.

## Clean accuracy, mean aggregation, 180 pairs (tie-half primary / strict; n ties at tau_m)
| score | tie-half | strict | ties | tau_m |
|---|---|---|---|---|
| M1 fp16 | 80.8 | 81.1 | 7 | 1.06e-4 |
| M1 fp32 (P2, eligibility run) | 81.7 | 80.6 | - | 1.06e-4 |
| M1 skip-4 (fp16) | 82.2 | 82.2 | 10 | 1.08e-4 |
| M2 fp16, corrected (mask_index 0, P4_M2_ipdev_clean-mi0_s1) | 60.8 | 60.6 | 17 | 1.11e-4 |
| M2 fp16, OLD (mask_index 1 wrapper deviation, P4_M2_ipdev_clean_s1; superseded, disclosure only) | 46.9 | 46.7 | 19 | 1.16e-4 |
| M0r init0/1/2 | 50.0 / 50.0 / 50.0 | 50.0 / 50.6 (init2) / 50.0 | 180 / 180 / 178 | ~1.7e-4 |
| B1 (M1 run) / B2 / B3 | 58.1 / 76.1 / 45.3 | 57.2 / 76.1 / 45.0 | 7 / 0 / 9 | |
| B1 / B2 / B3 (M2 run) | 57.8 / 76.1 / 17.2 | 58.3 / 76.1 / 17.2 | 10 / 2 / 0 | |
| B1 / B2 / B3 (skip-4) | 68.9 / 79.4 / 69.4 | 65.6 / 76.1 / 68.9 | 14 / 12 / 2 | |
| B1 whole-window (descriptive) | 58.6 | 58.3 | 7 | |
M1 per block (strict, O1/O2/O3): 75.0 / 83.3 / 85.0. M1 minus B2 paired clean difference: +4.7 pp, 95% CI [-1.1, 10.3] (T1). M1 fixed-C (A2, tie-half): C=2 34.4, C=6 79.2, C=10 78.9. Full-clip-max aggregation (H3 aggregation): M1 72.5 tie-half / 62.2 strict (39 ties), M2 (corrected) 64.7 / 53.9 (41 ties); old M2 64.4 / 48.3.
Between-video SD of S: M1 0.0161, M2 0.0113 (old run 0.0078), M0r 0.0020/0.0008/0.0011 (5 to 12 percent of M1).

## H1 eligibility (prereg sec 6: clean acc >= 80.0% tie-half, point estimate)
- M1: judged on the P2 fp32 run, 81.7% (strict 80.6%): ELIGIBLE, H1-confirmatory (never re-evaluated on fp16; for information the fp16 run gives 80.8 / 81.1, also >= 80).
- M2: judged on its corrected fp16 clean run (mask_index 0), 60.8% tie-half (strict 60.6%) < 80.0: NOT ELIGIBLE, H1 descriptive for M2. (The old mask_index-1 run gave 46.9%; kept separately, not the M2 number.)

## G2 (prereg sec 7)
Criterion (quoted): "M1 vflip detection (a) >= 80% (point estimate, tie-half) and (b) lower bound > 0.5. Reversal is reported; if its point estimate < 50% a 10-curve diagnostic is logged and reversal reported as 'not detected'; G2 does not depend on it."
Measured (H3 detection, full-clip max, tau_m = 1.09e-4, 180 possible videos): (a) vflip vs clean = 21.1% (95% cluster CI 14.7 to 28.3); (b) vflip vs hflip = 25.8% (CI 18.6 to 33.3, lower bound far below 0.5). Strict: (a) 20.6, (b) 26.1; exact-ties: same. **G2 NOT MET** (both parts). Reversal detection 60.8% (strict 60.0), not below 50, no diagnostic required. hflip vs clean detection (frac higher) 38.3%. M1 minus M0r detection -66.7 pp (CI -76.1, -56.7); learned sensitivity not credited. Free secondary pairwise accuracy on edited pairs: vflip 83.9 / 82.2 strict, reversal 74.7 / 73.3.
Mean full-clip-max S: clean 0.5413, vflip 0.5377, hflip 0.5404, reversal 0.5427 (none of the edited arrays is identical to clean, so the edit was applied).
Per prereg sec 7, any fix follows the G1' rules (cause logged before rerun). Nothing was fixed or rerun here.

## Surprises / inconsistencies (report only, nothing changed)
1. G2 fails clearly: M1 surprise is not higher for vflipped clips (lower in 79% of videos).
2. M0r vflip detection is about 0.88 (so M1 - M0r = -0.67): under max aggregation M0r's fp16 noise exceeds its tiny tau_m (about 1.7e-4), so M0r is not "all ties" there (97 to 99% ties holds for mean aggregation only). Prereg H3 text "detection approx 0.5 by construction" does not hold for full-clip max.
3. fp16 versus fp32 M1 clean: per-video mean score max abs difference 8.2e-4 (about 8x tau_m), per-window max 2.65e-3, mean 1.65e-4; 5 pairs change verdict; tie-half 80.8 vs 81.7. This exceeds the expected 1e-4 per video (the earlier 1.06e-4 came from 12 videos; verifier saw 2.5e-4 to 5.3e-4 per window). Same precision rule (fp16 vs fp16) is unaffected.
4. M2 corrected clean accuracy is 60.8% (old mask_index-1 run: 46.9%, at chance). B3(M2) = 17.2% is unchanged by the fix (B3 uses target-encoder features only) and is far below chance (consistently inverted direction), unlike B3(M1) 45.3. This is not explained by the mask_index; M2 feature/scoring convention for B3 remains unexamined (frozen code).
5. M1 fixed C=2 accuracy 34.4% (below chance), C=6/10 about 79%: the min over C is dominated by the C=2 column. Descriptive (A2).
6. skip-4 baselines B1/B2/B3 are much higher (68.9/79.4/69.4) than skip 2; tie-half for M1 skip-4 is 82.2.
