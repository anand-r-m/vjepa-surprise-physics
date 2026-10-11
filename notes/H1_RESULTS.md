# H1 confirmatory analysis, M1 (frozen driver, no interpretation beyond the prereg decision rule)

Date 2026-10-08. Driver `scripts/run_analysis.py --models M1 --stages h1` (unmodified; src/analysis untouched), n_boot 10000, bootstrap seed 20261015 (in code).
Runs dir (symlinks, scratchpad): 41 runs from `results/raw/{p4_clean_m1,g2_controls,h1_inv_a,h1_inv_b,h1_inv_c}/results/P4_*` (M1 clean, clean-skip4, M0r clean x3, g2 controls incl. hflip, 31 H1 runs). Not included: h2_spec_*, any M2 run.
Meta check (run first): ok, 41 runs, no mismatch, no bypass (`results/analysis/h1/meta_check.json`; precision fp16, 2 GPUs).
Eligibility: M1 judged on P2 fp32 clean run (`results/raw/p2_clean/results/P2_M1_ipdev_clean_s1`): 81.7% tie-half, eligible. fp16 clean (P4_M1_ipdev_clean_s1) 80.8% tie-half, 81.1% strict.
Crop retention exclusion: `results/analysis/h1/retention.json` (zoom key of `retention_full.json`, produced by `scripts/make_retention.py` on dev pixels + `kaggle/h2_spec_a/matches.json`; the driver cannot read the script's extra `all_scales` key, so only `zoom` was kept). 68 of 180 pairs have retention < 0.9 and are excluded for crop only (n = 112).
Outputs: `results/analysis/h1/h1_M1.json` (tie-half, tau 1.057e-4, primary), `h1/strict/h1_M1_strict.json` (released `<`), `h1/exactties/h1_M1_exactties.json` (tau 0, ties 0.5). Clean + meta in each dir.
Family completeness: complete. All 7 high-strength H1 edits (brightness x3 seeds, noise x3, blur, jpeg, zoom, hflip [g2_controls], fps_halve) plus dither x3 floor and skip-4 reference are present. Holm-14 = 7 dacc + 7 flip-vs-floor. M0r has no H1 stage in the driver or in the prereg (H1 is per eligible model), so none was run. Low/mid dose-response (A3, secondary) not run: the driver computes high strength only.

## Floor
f0 (mean dither flip rate) = 21.5% (tie-half), 15.6% (strict and exact-ties). f0 >= 10%, so per prereg sec 6 **M1 H1 is descriptive ("verdicts unstable under an invisible perturbation")** in all three variants (`status`, `f0_valid=false`).

## Tie-half (primary), clean y0 mean 80.8%
| edit (high) | n | dacc pp [95% CI] | flip f_e | flip - f0 pp | Holm p dacc | Holm p flip | verdict |
|---|---|---|---|---|---|---|---|
| brightness | 180 | -2.4 [-5.2, +0.2] | 12.4% | -9.1 | 0.56 | 1.000 | inconclusive |
| noise | 180 | -20.6 [-25.8, -15.4] | 37.8% | +16.3 | 0.000 | 0.000 | violated |
| blur | 180 | -14.4 [-19.4, -9.7] | 31.1% | +9.6 | 0.000 | 0.002 | violated |
| jpeg | 180 | -10.8 [-16.4, -5.6] | 28.3% | +6.9 | 0.000 | 0.153 | violated (dacc route) |
| zoom (crop) | 112 | -0.4 [-5.6, +4.9] | 14.3% | -8.9 | 1.000 | 1.000 | inconclusive |
| hflip | 180 | +2.2 [-1.9, +6.7] | 15.0% | -6.5 | 1.000 | 1.000 | invariant |
| fps_halve | 180 | 0.0 [0.0, 0.0] | 0.0% | -21.5 | 1.000 | 1.000 | invariant (degenerate, see anomalies) |

## Strict (`<`, tau 0, ties 0), f0 = 15.6%
| edit | n | dacc pp | flip | Holm p dacc | Holm p flip | verdict |
|---|---|---|---|---|---|---|
| brightness | 180 | -1.7 | 9.4% | 1.00 | 1.000 | inconclusive |
| noise | 180 | -20.6 | 26.1% | 0.000 | 0.000 | violated |
| blur | 180 | -14.4 | 23.3% | 0.000 | 0.018 | violated |
| jpeg | 180 | -9.4 | 22.8% | 0.018 | 0.140 | violated (sign test disagrees: Holm sign 0.115) |
| zoom | 112 | -0.9 | 11.6% | 1.00 | 1.000 | inconclusive |
| hflip | 180 | +2.8 | 10.6% | 1.00 | 1.000 | invariant |
| fps_halve | 180 | 0.0 | 0.0% | 1.00 | 1.000 | invariant (degenerate) |

Exact-ties (tau 0, ties 0.5) is numerically identical to strict, because no pair is an exact tie (0 ties in every run at tau 0).

## Tie counts (pairs with |difference| <= tau 1.057e-4 of 180; per run, `ties` output computed with the same P functions)
clean 7; brightness-high s1/s2/s3 10/6/9; noise-high 37/43/33; blur 29; jpeg 14; zoom 4 (of 180 before exclusion); hflip 7; fps_halve 9; clean-skip4 reference 9; dither 19/17/16. At tau 0: all 0.

## Anomalies
1. **fps_halve is bit-identical to its reference.** `P4_M1_ipdev_fps_halve-high_s1` S array equals `P4_M1_ipdev_clean-skip4_s1` exactly (360x5x5, max abs diff 0), so dacc = flip = 0 by construction; the "invariant" verdict has CI [0,0] and tests nothing about the model. Cause: the halve edit with frame_step 2 reproduces native skip 4, which is also the reference. Reported as is; no change made.
2. Floor f0 = 21.5% (tie-half) / 15.6% (strict) exceeds the 10% threshold: H1 for M1 is descriptive by rule.
3. Crop: 68/180 pairs excluded by the 90% retention rule; its verdict rests on 112 pairs.
4. jpeg: strict variant has cluster/sign disagreement (counted in `dacc_sig_disagree`); jpeg tie-half verdict comes from the dacc route only, flip route not Holm-significant (0.153).
5. `make_retention.py` output has an extra `all_scales` key the frozen driver cannot parse; a `zoom`-only file was derived (no code edited).
