# P8 independent recompute (verifier)

Code: `verify/p8_lib` = `verify/p7_lib.py` (own code, unchanged) + `verify/p8_recompute.py` -> `verify/p8_recompute.json`; comparison `verify/p8_compare.py` -> `verify/_p8_rows.json`; entries `verify/p8_make_verified.py` -> `results/VERIFIED.json`. Inputs: `results/raw/<group>/results/<run>/surprise.npz`, `kaggle/h2_spec_a/matches.json`, `verify/_retention.json` (p6 pixel retention), `data/intphys_dev/starting_kit.zip` (dev/task.txt, for visible/occluded). Bootstrap: seed 20261015, 10,000 scene-cluster draws stratified by block, own RNG stream (p-values and CIs differ from the analysis by Monte-Carlo noise only; tolerances as p7_compare.md).

**Independence disclosure.** The recompute was written and run before `results/analysis/*`, `notes/*` result files, `scripts/run_*` or `src/vjepa_study/analysis` were opened for comparison. Before running it I did read (a) `scripts/figs/t2_invariance.py`, `f3_dose.py` and the other figure scripts for key names (as instructed), (b) `paper/tables/*.tex` for key names, and in doing so I saw the printed T4/T5/T6 numbers (ablation rows, baseline AUROC, per-block accuracies), and (c) `notes/B2_CHECKS.md` lines for the visible/occluded definition (scene folder names in dev/task.txt), which also printed its numbers. The computation itself is from raw arrays with the p7 code; the only choice that the visible numbers could have influenced is the A2 baseline definition (baselines at the same fixed C), which I fixed a priori from the array layout and for which I report the default-min-over-C baseline as a labelled sensitivity (`abl.A2_C*.D_1_baseline_default_minC`). `src/vjepa_study/analysis` and `scripts/run_analysis.py` were never opened.

## Summary

| block | match | MISMATCH | unmapped |
|---|---|---|---|
| 1a M2 H1 dose | 488 | 0 | 0 |
| 1b M2 H2 dose | 195 | 0 | 0 |
| 2 ablations | 155 | 0 | 0 |
| 3 T5 baselines | 50 | 0 | 0 |
| 4 T6 blocks | 120 | 0 | 0 |
| 5 M0r | 3 | 2 | 1 |
| 6 F3 flip CI | 45 | 0 | 0 |
| **total** | 1056 | 2 | 1 |

Mismatches (2) are both definitional and concern M0r only:
- M0r P2 strict mean over inits: mine 0.4981 vs analysis 0.5000
- M0r P2 tie rate mean over inits: mine 0.9963 vs analysis 0.9815
  Reason: `results/analysis/p2_clean_g1.json` summarises M0r with the SUPERSEDED fixed tau = 1e-4 (tie rate 98.1%, which I reproduce exactly: 176-178 of 180 per init). Under the prereg scale-relative tau the three inits tie on 180, 180, 178 of 180 pairs (99.6%), tie-half is exactly 50.0 for all three (verified), strict (d>0) 50.0 / 50.0 / 49.4. The prereg phrase "97-99% ties" is the fixed-tau number. Same class of issue as `g1_vith_clean_acc` and `clean.B1_P2.tiehalf` already logged.

## Findings

1. **M2 H1 strict vs tie-half.** Every `h1.M2.*` and every new `m2.dose.h1.*` value is tie-half; strict values exist only under `_strict` suffixes. `notes/M2_RESULTS.md` main H1 table = tie-half; its second table, labelled Strict, = strict. No inconsistency of that kind found. Two look-alikes: `results/analysis/m2/exactties/h1_M2_exactties.json` has tie_value 0.5 with tau 0, numerically identical to strict (no exact ties); and the M2 dose analysis primary reading is seed 1 at every cell, so its high-strength brightness/noise (-0.6/15.0, -7.8/25.6) differ from the 3-seed `h1.M2` values (-0.4/15.4, -6.4/28.3). Both tie-half. My keys use the as-run reading (matches the table high column, which reads `h1.M2.*`) and carry the seed-1 reading under `.s1.`.
2. **Holm family for M2 dose H1 is 22, not 30.** 11 cells (brightness, noise, blur at low/mid/high; jpeg and zoom at high) x 2 tests. Key names keep `holm30_*` because the table script reads them; every such entry carries the note. Seeds: low/mid cells seed 1 only; high cells use the available seeds (brightness 3, noise 3, blur/jpeg/zoom 1). Zoom-high n = 112.
3. **M2 H2 dose.** Low and high are seed 1 only; mid in the Holm family is also seed 1 (pooled A 0.4490; the 3-seed-where-available mid in `h2.M2.A` is 0.4489; note that M2 mid has zoom_base seed 1 only, jolt/lighting 3 seeds). Pooled A: low 0.4829, mid 0.4490, high 0.4204, all below 0.65 and decreasing; D_1 Holm-6 0.0006 everywhere; D_2 Holm-6: low 0.0278, mid 0.0058, high 0.0006.
4. **Ablations (M1).** A1 full-clip max: clean 72.5 (=A0), A 0.5529; A1 full-clip mean: clean 80.8, A 0.5930; A2 fixed C=2/6/10: clean (mean agg) 34.4 / 79.2 / 78.9, A 0.4377 / 0.5077 / 0.5277. The A2 rows hold the baselines at the same fixed C; with baselines at default min-over-C D_1 would be 0.1025 / 0.1725 / 0.1925 (C = 2/6/10).
5. **Not computable / not run.** `clean.B1_whole_window` (array not stored), M3, H2 on Main, M0r hflip (no run). M0r H2 AUROC (degenerate, ~0.50) is reported verifier-only.
6. **T6 visible/occluded** comes from scene folder names in the starting-kit `dev/task.txt` (90 pairs each). M1 fp16 P4: visible 85.6, occluded 76.1; fp32 P2: 86.7 / 76.7 (equals B2_CHECKS). Block x visible cells have 30 pairs.

## All compared rows (label | mine | analysis | |diff| | tol | status)

| label | mine | analysis | diff | tol | status |
|---|---|---|---|---|---|
| M2 dose H1 asrun f0 | 0.2463 | 0.2463 | 0 | 0.001 | match |
| M2 dose H1 asrun brightness-low n | 180 | 180 | 0 | 0 | match |
| M2 dose H1 asrun brightness-low dAcc | 0.013889 | 0.013889 | 0 | 0.001 | match |
| M2 dose H1 asrun brightness-low flip | 0.11667 | 0.11667 | 0 | 0.001 | match |
| M2 dose H1 asrun brightness-low flip-f0 | -0.12963 | -0.12963 | 0 | 0.001 | match |
| M2 dose H1 asrun brightness-low dAcc CI lo | -0.011111 | -0.011111 | 0 | 0.01 | match |
| M2 dose H1 asrun brightness-low dAcc CI hi | 0.041667 | 0.041667 | 0 | 0.01 | match |
| M2 dose H1 asrun brightness-low flip CI lo | 0.072222 | 0.072222 | 0 | 0.01 | match |
| M2 dose H1 asrun brightness-low flip CI hi | 0.16667 | 0.16667 | 0 | 0.01 | match |
| M2 dose H1 asrun brightness-low p_dacc | 0.3482 | 0.3528 | 0.0046 | 0.038527 | match |
| M2 dose H1 asrun brightness-low p_flip | 1 | 1 | 0 | 0.0403 | match |
| M2 dose H1 asrun brightness-low Holm-22 dAcc | 1 | 1 | 0 | 0.8866 | match |
| M2 dose H1 asrun brightness-low Holm-22 flip | 1 | 1 | 0 | 0.8866 | match |
| M2 dose H1 asrun brightness-mid n | 180 | 180 | 0 | 0 | match |
| M2 dose H1 asrun brightness-mid dAcc | 0.027778 | 0.027778 | 0 | 0.001 | match |
| M2 dose H1 asrun brightness-mid flip | 0.16111 | 0.16111 | 0 | 0.001 | match |
| M2 dose H1 asrun brightness-mid flip-f0 | -0.085185 | -0.085185 | 0 | 0.001 | match |
| M2 dose H1 asrun brightness-mid dAcc CI lo | -0.0083333 | -0.0083333 | 0 | 0.01 | match |
| M2 dose H1 asrun brightness-mid dAcc CI hi | 0.066667 | 0.063889 | 0.0027778 | 0.01 | match |
| M2 dose H1 asrun brightness-mid flip CI lo | 0.11111 | 0.11111 | 0 | 0.01 | match |
| M2 dose H1 asrun brightness-mid flip CI hi | 0.21667 | 0.21667 | 0 | 0.01 | match |
| M2 dose H1 asrun brightness-mid p_dacc | 0.1512 | 0.1492 | 0.002 | 0.028959 | match |
| M2 dose H1 asrun brightness-mid p_flip | 0.9996 | 0.9997 | 0.0001 | 0.0403 | match |
| M2 dose H1 asrun brightness-mid Holm-22 dAcc | 1 | 1 | 0 | 0.8866 | match |
| M2 dose H1 asrun brightness-mid Holm-22 flip | 1 | 1 | 0 | 0.8866 | match |
| M2 dose H1 asrun brightness-high n | 180 | 180 | 0 | 0 | match |
| M2 dose H1 asrun brightness-high dAcc | -0.0037037 | -0.0037037 | 0 | 0.001 | match |
| M2 dose H1 asrun brightness-high flip | 0.1537 | 0.1537 | 0 | 0.001 | match |
| M2 dose H1 asrun brightness-high flip-f0 | -0.092593 | -0.092593 | 0 | 0.001 | match |
| M2 dose H1 asrun brightness-high dAcc CI lo | -0.030556 | -0.030556 | 0 | 0.01 | match |
| M2 dose H1 asrun brightness-high dAcc CI hi | 0.025 | 0.025 | 0 | 0.01 | match |
| M2 dose H1 asrun brightness-high flip CI lo | 0.11111 | 0.10926 | 0.0018519 | 0.01 | match |
| M2 dose H1 asrun brightness-high flip CI hi | 0.2 | 0.19815 | 0.0018519 | 0.01 | match |
| M2 dose H1 asrun brightness-high p_dacc | 0.7596 | 0.7722 | 0.0126 | 0.0403 | match |
| M2 dose H1 asrun brightness-high p_flip | 1 | 1 | 0 | 0.0403 | match |
| M2 dose H1 asrun brightness-high Holm-22 dAcc | 1 | 1 | 0 | 0.8866 | match |
| M2 dose H1 asrun brightness-high Holm-22 flip | 1 | 1 | 0 | 0.8866 | match |
| M2 dose H1 asrun noise-low n | 180 | 180 | 0 | 0 | match |
| M2 dose H1 asrun noise-low dAcc | -0.044444 | -0.044444 | 0 | 0.001 | match |
| M2 dose H1 asrun noise-low flip | 0.26111 | 0.26111 | 0 | 0.001 | match |
| M2 dose H1 asrun noise-low flip-f0 | 0.014815 | 0.014815 | 0 | 0.001 | match |
| M2 dose H1 asrun noise-low dAcc CI lo | -0.10278 | -0.10278 | 0 | 0.01 | match |
| M2 dose H1 asrun noise-low dAcc CI hi | 0.013889 | 0.013889 | 0 | 0.01 | match |
| M2 dose H1 asrun noise-low flip CI lo | 0.2 | 0.2 | 0 | 0.01 | match |
| M2 dose H1 asrun noise-low flip CI hi | 0.32222 | 0.32222 | 0 | 0.01 | match |
| M2 dose H1 asrun noise-low p_dacc | 0.146 | 0.1512 | 0.0052 | 0.028959 | match |
| M2 dose H1 asrun noise-low p_flip | 0.1987 | 0.2086 | 0.0099 | 0.032805 | match |
| M2 dose H1 asrun noise-low Holm-22 dAcc | 1 | 1 | 0 | 0.8866 | match |
| M2 dose H1 asrun noise-low Holm-22 flip | 1 | 1 | 0 | 0.8866 | match |
| M2 dose H1 asrun noise-mid n | 180 | 180 | 0 | 0 | match |
| M2 dose H1 asrun noise-mid dAcc | -0.080556 | -0.080556 | 0 | 0.001 | match |
| M2 dose H1 asrun noise-mid flip | 0.3 | 0.3 | 0 | 0.001 | match |
| M2 dose H1 asrun noise-mid flip-f0 | 0.053704 | 0.053704 | 0 | 0.001 | match |
| M2 dose H1 asrun noise-mid dAcc CI lo | -0.13889 | -0.13889 | 0 | 0.01 | match |
| M2 dose H1 asrun noise-mid dAcc CI hi | -0.022222 | -0.022222 | 0 | 0.01 | match |
| M2 dose H1 asrun noise-mid flip CI lo | 0.23333 | 0.23333 | 0 | 0.01 | match |
| M2 dose H1 asrun noise-mid flip CI hi | 0.36667 | 0.36667 | 0 | 0.01 | match |
| M2 dose H1 asrun noise-mid p_dacc | 0.0074 | 0.0064 | 0.001 | 0.0071564 | match |
| M2 dose H1 asrun noise-mid p_flip | 0.0205 | 0.0204 | 0.0001 | 0.011636 | match |
| M2 dose H1 asrun noise-mid Holm-22 dAcc | 0.111 | 0.1008 | 0.0102 | 0.55947 | match |
| M2 dose H1 asrun noise-mid Holm-22 flip | 0.246 | 0.2448 | 0.0012 | 0.76459 | match |
| M2 dose H1 asrun noise-high n | 180 | 180 | 0 | 0 | match |
| M2 dose H1 asrun noise-high dAcc | -0.063889 | -0.063889 | 0 | 0.001 | match |
| M2 dose H1 asrun noise-high flip | 0.28333 | 0.28333 | 0 | 0.001 | match |
| M2 dose H1 asrun noise-high flip-f0 | 0.037037 | 0.037037 | 0 | 0.001 | match |
| M2 dose H1 asrun noise-high dAcc CI lo | -0.11481 | -0.11574 | 0.00092593 | 0.01 | match |
| M2 dose H1 asrun noise-high dAcc CI hi | -0.012963 | -0.011111 | 0.0018519 | 0.01 | match |
| M2 dose H1 asrun noise-high flip CI lo | 0.22407 | 0.22222 | 0.0018519 | 0.01 | match |
| M2 dose H1 asrun noise-high flip CI hi | 0.34444 | 0.3463 | 0.0018519 | 0.01 | match |
| M2 dose H1 asrun noise-high p_dacc | 0.0132 | 0.0174 | 0.0042 | 0.010761 | match |
| M2 dose H1 asrun noise-high p_flip | 0.0335 | 0.0353 | 0.0018 | 0.015063 | match |
| M2 dose H1 asrun noise-high Holm-22 dAcc | 0.1716 | 0.2262 | 0.0546 | 0.74293 | match |
| M2 dose H1 asrun noise-high Holm-22 flip | 0.3685 | 0.3883 | 0.0198 | 0.86436 | match |
| M2 dose H1 asrun blur-low n | 180 | 180 | 0 | 0 | match |
| M2 dose H1 asrun blur-low dAcc | 0.15833 | 0.15833 | 0 | 0.001 | match |
| M2 dose H1 asrun blur-low flip | 0.35556 | 0.35556 | 0 | 0.001 | match |
| M2 dose H1 asrun blur-low flip-f0 | 0.10926 | 0.10926 | 0 | 0.001 | match |
| M2 dose H1 asrun blur-low dAcc CI lo | 0.1 | 0.1 | 0 | 0.01 | match |
| M2 dose H1 asrun blur-low dAcc CI hi | 0.21944 | 0.21944 | 0 | 0.01 | match |
| M2 dose H1 asrun blur-low flip CI lo | 0.27778 | 0.27778 | 0 | 0.01 | match |
| M2 dose H1 asrun blur-low flip CI hi | 0.43333 | 0.43333 | 0 | 0.01 | match |
| M2 dose H1 asrun blur-low p_dacc | 0 | 0 | 0 | 0.0011 | match |
| M2 dose H1 asrun blur-low p_flip | 0.0045 | 0.0038 | 0.0007 | 0.0056545 | match |
| M2 dose H1 asrun blur-low Holm-22 dAcc | 0 | 0 | 0 | 0.024199 | match |
| M2 dose H1 asrun blur-low Holm-22 flip | 0.0765 | 0.0646 | 0.0119 | 0.4744 | match |
| M2 dose H1 asrun blur-mid n | 180 | 180 | 0 | 0 | match |
| M2 dose H1 asrun blur-mid dAcc | 0.18611 | 0.18611 | 0 | 0.001 | match |
| M2 dose H1 asrun blur-mid flip | 0.34444 | 0.34444 | 0 | 0.001 | match |
| M2 dose H1 asrun blur-mid flip-f0 | 0.098148 | 0.098148 | 0 | 0.001 | match |
| M2 dose H1 asrun blur-mid dAcc CI lo | 0.13056 | 0.13056 | 0 | 0.01 | match |
| M2 dose H1 asrun blur-mid dAcc CI hi | 0.24444 | 0.24444 | 0 | 0.01 | match |
| M2 dose H1 asrun blur-mid flip CI lo | 0.27222 | 0.26667 | 0.0055556 | 0.01 | match |
| M2 dose H1 asrun blur-mid flip CI hi | 0.41667 | 0.42222 | 0.0055556 | 0.01 | match |
| M2 dose H1 asrun blur-mid p_dacc | 0 | 0 | 0 | 0.0011 | match |
| M2 dose H1 asrun blur-mid p_flip | 0.0059 | 0.0063 | 0.0004 | 0.0066298 | match |
| M2 dose H1 asrun blur-mid Holm-22 dAcc | 0 | 0 | 0 | 0.024199 | match |
| M2 dose H1 asrun blur-mid Holm-22 flip | 0.0944 | 0.1008 | 0.0064 | 0.53647 | match |
| M2 dose H1 asrun blur-high n | 180 | 180 | 0 | 0 | match |
| M2 dose H1 asrun blur-high dAcc | 0.12778 | 0.12778 | 0 | 0.001 | match |
| M2 dose H1 asrun blur-high flip | 0.42222 | 0.42222 | 0 | 0.001 | match |
| M2 dose H1 asrun blur-high flip-f0 | 0.17593 | 0.17593 | 0 | 0.001 | match |
| M2 dose H1 asrun blur-high dAcc CI lo | 0.063889 | 0.063889 | 0 | 0.01 | match |
| M2 dose H1 asrun blur-high dAcc CI hi | 0.19167 | 0.19444 | 0.0027778 | 0.01 | match |
| M2 dose H1 asrun blur-high flip CI lo | 0.34444 | 0.34444 | 0 | 0.01 | match |
| M2 dose H1 asrun blur-high flip CI hi | 0.5 | 0.5 | 0 | 0.01 | match |
| M2 dose H1 asrun blur-high p_dacc | 0 | 0.0004 | 0.0004 | 0.0018997 | match |
| M2 dose H1 asrun blur-high p_flip | 0 | 0 | 0 | 0.0011 | match |
| M2 dose H1 asrun blur-high Holm-22 dAcc | 0 | 0.0072 | 0.0072 | 0.1554 | match |
| M2 dose H1 asrun blur-high Holm-22 flip | 0 | 0 | 0 | 0.024199 | match |
| M2 dose H1 asrun jpeg-high n | 180 | 180 | 0 | 0 | match |
| M2 dose H1 asrun jpeg-high dAcc | -0.016667 | -0.016667 | 0 | 0.001 | match |
| M2 dose H1 asrun jpeg-high flip | 0.40556 | 0.40556 | 0 | 0.001 | match |
| M2 dose H1 asrun jpeg-high flip-f0 | 0.15926 | 0.15926 | 0 | 0.001 | match |
| M2 dose H1 asrun jpeg-high dAcc CI lo | -0.077778 | -0.077778 | 0 | 0.01 | match |
| M2 dose H1 asrun jpeg-high dAcc CI hi | 0.044444 | 0.047222 | 0.0027778 | 0.01 | match |
| M2 dose H1 asrun jpeg-high flip CI lo | 0.32778 | 0.32778 | 0 | 0.01 | match |
| M2 dose H1 asrun jpeg-high flip CI hi | 0.48333 | 0.48333 | 0 | 0.01 | match |
| M2 dose H1 asrun jpeg-high p_dacc | 0.6118 | 0.6118 | 0 | 0.0403 | match |
| M2 dose H1 asrun jpeg-high p_flip | 0 | 0 | 0 | 0.0011 | match |
| M2 dose H1 asrun jpeg-high Holm-22 dAcc | 1 | 1 | 0 | 0.8866 | match |
| M2 dose H1 asrun jpeg-high Holm-22 flip | 0 | 0 | 0 | 0.024199 | match |
| M2 dose H1 asrun zoom-high n | 112 | 112 | 0 | 0 | match |
| M2 dose H1 asrun zoom-high dAcc | 0.071429 | 0.071429 | 0 | 0.001 | match |
| M2 dose H1 asrun zoom-high flip | 0.25 | 0.25 | 0 | 0.001 | match |
| M2 dose H1 asrun zoom-high flip-f0 | -0.056548 | -0.056548 | 5.5511e-17 | 0.001 | match |
| M2 dose H1 asrun zoom-high dAcc CI lo | 0.017241 | 0.017857 | 0.00061576 | 0.01 | match |
| M2 dose H1 asrun zoom-high dAcc CI hi | 0.12755 | 0.12727 | 0.00027829 | 0.01 | match |
| M2 dose H1 asrun zoom-high flip CI lo | 0.16964 | 0.16667 | 0.0029724 | 0.01 | match |
| M2 dose H1 asrun zoom-high flip CI hi | 0.33871 | 0.33696 | 0.0017468 | 0.01 | match |
| M2 dose H1 asrun zoom-high p_dacc | 0.0114 | 0.012 | 0.0006 | 0.0090108 | match |
| M2 dose H1 asrun zoom-high p_flip | 0.9031 | 0.9062 | 0.0031 | 0.0403 | match |
| M2 dose H1 asrun zoom-high Holm-22 dAcc | 0.1596 | 0.168 | 0.0084 | 0.6646 | match |
| M2 dose H1 asrun zoom-high Holm-22 flip | 1 | 1 | 0 | 0.8866 | match |
| M2 dose H1 asrun strict f0 | 0.17407 | 0.17407 | 0 | 0.001 | match |
| M2 dose H1 asrun strict brightness-low n | 180 | 180 | 0 | 0 | match |
| M2 dose H1 asrun strict brightness-low dAcc | 0.016667 | 0.016667 | 0 | 0.001 | match |
| M2 dose H1 asrun strict brightness-low flip | 0.083333 | 0.083333 | 0 | 0.001 | match |
| M2 dose H1 asrun strict brightness-low flip-f0 | -0.090741 | -0.090741 | 0 | 0.001 | match |
| M2 dose H1 asrun strict brightness-low dAcc CI lo | -0.027778 | -0.027778 | 0 | 0.01 | match |
| M2 dose H1 asrun strict brightness-low dAcc CI hi | 0.061111 | 0.061111 | 0 | 0.01 | match |
| M2 dose H1 asrun strict brightness-low p_dacc | 0.5528 | 0.5332 | 0.0196 | 0.0403 | match |
| M2 dose H1 asrun strict brightness-low p_flip | 0.9994 | 0.9995 | 0.0001 | 0.0403 | match |
| M2 dose H1 asrun strict brightness-low Holm-22 dAcc | 1 | 1 | 0 | 0.8866 | match |
| M2 dose H1 asrun strict brightness-low Holm-22 flip | 1 | 1 | 0 | 0.8866 | match |
| M2 dose H1 asrun strict brightness-mid n | 180 | 180 | 0 | 0 | match |
| M2 dose H1 asrun strict brightness-mid dAcc | 0.027778 | 0.027778 | 0 | 0.001 | match |
| M2 dose H1 asrun strict brightness-mid flip | 0.094444 | 0.094444 | 0 | 0.001 | match |
| M2 dose H1 asrun strict brightness-mid flip-f0 | -0.07963 | -0.07963 | 0 | 0.001 | match |
| M2 dose H1 asrun strict brightness-mid dAcc CI lo | -0.016667 | -0.016667 | 0 | 0.01 | match |
| M2 dose H1 asrun strict brightness-mid dAcc CI hi | 0.072222 | 0.072222 | 0 | 0.01 | match |
| M2 dose H1 asrun strict brightness-mid p_dacc | 0.2558 | 0.2574 | 0.0016 | 0.035276 | match |
| M2 dose H1 asrun strict brightness-mid p_flip | 0.9956 | 0.9975 | 0.0019 | 0.0403 | match |
| M2 dose H1 asrun strict brightness-mid Holm-22 dAcc | 1 | 1 | 0 | 0.8866 | match |
| M2 dose H1 asrun strict brightness-mid Holm-22 flip | 1 | 1 | 0 | 0.8866 | match |
| M2 dose H1 asrun strict brightness-high n | 180 | 180 | 0 | 0 | match |
| M2 dose H1 asrun strict brightness-high dAcc | -0.0074074 | -0.0074074 | 0 | 0.001 | match |
| M2 dose H1 asrun strict brightness-high flip | 0.1 | 0.1 | 0 | 0.001 | match |
| M2 dose H1 asrun strict brightness-high flip-f0 | -0.074074 | -0.074074 | 0 | 0.001 | match |
| M2 dose H1 asrun strict brightness-high dAcc CI lo | -0.044444 | -0.044444 | 0 | 0.01 | match |
| M2 dose H1 asrun strict brightness-high dAcc CI hi | 0.02963 | 0.02963 | 3.4694e-18 | 0.01 | match |
| M2 dose H1 asrun strict brightness-high p_dacc | 0.6418 | 0.6642 | 0.0224 | 0.0403 | match |
| M2 dose H1 asrun strict brightness-high p_flip | 0.9997 | 0.9993 | 0.0004 | 0.0403 | match |
| M2 dose H1 asrun strict brightness-high Holm-22 dAcc | 1 | 1 | 0 | 0.8866 | match |
| M2 dose H1 asrun strict brightness-high Holm-22 flip | 1 | 1 | 0 | 0.8866 | match |
| M2 dose H1 asrun strict noise-low n | 180 | 180 | 0 | 0 | match |
| M2 dose H1 asrun strict noise-low dAcc | -0.05 | -0.05 | 0 | 0.001 | match |
| M2 dose H1 asrun strict noise-low flip | 0.19444 | 0.19444 | 0 | 0.001 | match |
| M2 dose H1 asrun strict noise-low flip-f0 | 0.02037 | 0.02037 | 0 | 0.001 | match |
| M2 dose H1 asrun strict noise-low dAcc CI lo | -0.11111 | -0.11111 | 0 | 0.01 | match |
| M2 dose H1 asrun strict noise-low dAcc CI hi | 0.011111 | 0.011111 | 0 | 0.01 | match |
| M2 dose H1 asrun strict noise-low p_dacc | 0.1248 | 0.1346 | 0.0098 | 0.027604 | match |
| M2 dose H1 asrun strict noise-low p_flip | 0.0964 | 0.0948 | 0.0016 | 0.023911 | match |
| M2 dose H1 asrun strict noise-low Holm-22 dAcc | 1 | 1 | 0 | 0.8866 | match |
| M2 dose H1 asrun strict noise-low Holm-22 flip | 0.964 | 0.948 | 0.016 | 0.8866 | match |
| M2 dose H1 asrun strict noise-mid n | 180 | 180 | 0 | 0 | match |
| M2 dose H1 asrun strict noise-mid dAcc | -0.077778 | -0.077778 | 0 | 0.001 | match |
| M2 dose H1 asrun strict noise-mid flip | 0.23333 | 0.23333 | 0 | 0.001 | match |
| M2 dose H1 asrun strict noise-mid flip-f0 | 0.059259 | 0.059259 | 0 | 0.001 | match |
| M2 dose H1 asrun strict noise-mid dAcc CI lo | -0.15 | -0.15 | 0 | 0.01 | match |
| M2 dose H1 asrun strict noise-mid dAcc CI hi | -0.0055556 | -0.0055556 | 0 | 0.01 | match |
| M2 dose H1 asrun strict noise-mid p_dacc | 0.0396 | 0.0412 | 0.0016 | 0.0162 | match |
| M2 dose H1 asrun strict noise-mid p_flip | 0.0032 | 0.0027 | 0.0005 | 0.0048182 | match |
| M2 dose H1 asrun strict noise-mid Holm-22 dAcc | 0.4752 | 0.4944 | 0.0192 | 0.88654 | match |
| M2 dose H1 asrun strict noise-mid Holm-22 flip | 0.0512 | 0.0432 | 0.008 | 0.39451 | match |
| M2 dose H1 asrun strict noise-high n | 180 | 180 | 0 | 0 | match |
| M2 dose H1 asrun strict noise-high dAcc | -0.068519 | -0.068519 | 0 | 0.001 | match |
| M2 dose H1 asrun strict noise-high flip | 0.21667 | 0.21667 | 0 | 0.001 | match |
| M2 dose H1 asrun strict noise-high flip-f0 | 0.042593 | 0.042593 | 0 | 0.001 | match |
| M2 dose H1 asrun strict noise-high dAcc CI lo | -0.12593 | -0.12778 | 0.0018519 | 0.01 | match |
| M2 dose H1 asrun strict noise-high dAcc CI hi | -0.011111 | -0.0092593 | 0.0018519 | 0.01 | match |
| M2 dose H1 asrun strict noise-high p_dacc | 0.0198 | 0.021 | 0.0012 | 0.011771 | match |
| M2 dose H1 asrun strict noise-high p_flip | 0.0077 | 0.0089 | 0.0012 | 0.0078135 | match |
| M2 dose H1 asrun strict noise-high Holm-22 dAcc | 0.2574 | 0.273 | 0.0156 | 0.79068 | match |
| M2 dose H1 asrun strict noise-high Holm-22 flip | 0.1078 | 0.1246 | 0.0168 | 0.58787 | match |
| M2 dose H1 asrun strict blur-low n | 180 | 180 | 0 | 0 | match |
| M2 dose H1 asrun strict blur-low dAcc | 0.16111 | 0.16111 | 0 | 0.001 | match |
| M2 dose H1 asrun strict blur-low flip | 0.30556 | 0.30556 | 0 | 0.001 | match |
| M2 dose H1 asrun strict blur-low flip-f0 | 0.13148 | 0.13148 | 0 | 0.001 | match |
| M2 dose H1 asrun strict blur-low dAcc CI lo | 0.094444 | 0.094444 | 0 | 0.01 | match |
| M2 dose H1 asrun strict blur-low dAcc CI hi | 0.22778 | 0.22778 | 0 | 0.01 | match |
| M2 dose H1 asrun strict blur-low p_dacc | 0 | 0 | 0 | 0.0011 | match |
| M2 dose H1 asrun strict blur-low p_flip | 0.0008 | 0.0004 | 0.0004 | 0.0025618 | match |
| M2 dose H1 asrun strict blur-low Holm-22 dAcc | 0 | 0 | 0 | 0.024199 | match |
| M2 dose H1 asrun strict blur-low Holm-22 flip | 0.0136 | 0.0072 | 0.0064 | 0.21045 | match |
| M2 dose H1 asrun strict blur-mid n | 180 | 180 | 0 | 0 | match |
| M2 dose H1 asrun strict blur-mid dAcc | 0.18889 | 0.18889 | 0 | 0.001 | match |
| M2 dose H1 asrun strict blur-mid flip | 0.27778 | 0.27778 | 0 | 0.001 | match |
| M2 dose H1 asrun strict blur-mid flip-f0 | 0.1037 | 0.1037 | 0 | 0.001 | match |
| M2 dose H1 asrun strict blur-mid dAcc CI lo | 0.12778 | 0.12778 | 0 | 0.01 | match |
| M2 dose H1 asrun strict blur-mid dAcc CI hi | 0.25556 | 0.25556 | 0 | 0.01 | match |
| M2 dose H1 asrun strict blur-mid p_dacc | 0 | 0 | 0 | 0.0011 | match |
| M2 dose H1 asrun strict blur-mid p_flip | 0.0054 | 0.0056 | 0.0002 | 0.0062699 | match |
| M2 dose H1 asrun strict blur-mid Holm-22 dAcc | 0 | 0 | 0 | 0.024199 | match |
| M2 dose H1 asrun strict blur-mid Holm-22 flip | 0.081 | 0.084 | 0.003 | 0.4948 | match |
| M2 dose H1 asrun strict blur-high n | 180 | 180 | 0 | 0 | match |
| M2 dose H1 asrun strict blur-high dAcc | 0.14444 | 0.14444 | 0 | 0.001 | match |
| M2 dose H1 asrun strict blur-high flip | 0.31111 | 0.31111 | 0 | 0.001 | match |
| M2 dose H1 asrun strict blur-high flip-f0 | 0.13704 | 0.13704 | 0 | 0.001 | match |
| M2 dose H1 asrun strict blur-high dAcc CI lo | 0.072222 | 0.072222 | 0 | 0.01 | match |
| M2 dose H1 asrun strict blur-high dAcc CI hi | 0.21667 | 0.21667 | 0 | 0.01 | match |
| M2 dose H1 asrun strict blur-high p_dacc | 0 | 0.0004 | 0.0004 | 0.0018997 | match |
| M2 dose H1 asrun strict blur-high p_flip | 0 | 0.0003 | 0.0003 | 0.0016854 | match |
| M2 dose H1 asrun strict blur-high Holm-22 dAcc | 0 | 0.0072 | 0.0072 | 0.1554 | match |
| M2 dose H1 asrun strict blur-high Holm-22 flip | 0 | 0.0057 | 0.0057 | 0.1391 | match |
| M2 dose H1 asrun strict jpeg-high n | 180 | 180 | 0 | 0 | match |
| M2 dose H1 asrun strict jpeg-high dAcc | 0.016667 | 0.016667 | 0 | 0.001 | match |
| M2 dose H1 asrun strict jpeg-high flip | 0.35 | 0.35 | 0 | 0.001 | match |
| M2 dose H1 asrun strict jpeg-high flip-f0 | 0.17593 | 0.17593 | 0 | 0.001 | match |
| M2 dose H1 asrun strict jpeg-high dAcc CI lo | -0.05 | -0.055556 | 0.0055556 | 0.01 | match |
| M2 dose H1 asrun strict jpeg-high dAcc CI hi | 0.088889 | 0.088889 | 0 | 0.01 | match |
| M2 dose H1 asrun strict jpeg-high p_dacc | 0.7122 | 0.6986 | 0.0136 | 0.0403 | match |
| M2 dose H1 asrun strict jpeg-high p_flip | 0 | 0 | 0 | 0.0011 | match |
| M2 dose H1 asrun strict jpeg-high Holm-22 dAcc | 1 | 1 | 0 | 0.8866 | match |
| M2 dose H1 asrun strict jpeg-high Holm-22 flip | 0 | 0 | 0 | 0.024199 | match |
| M2 dose H1 asrun strict zoom-high n | 112 | 112 | 0 | 0 | match |
| M2 dose H1 asrun strict zoom-high dAcc | 0.071429 | 0.071429 | 0 | 0.001 | match |
| M2 dose H1 asrun strict zoom-high flip | 0.19643 | 0.19643 | 0 | 0.001 | match |
| M2 dose H1 asrun strict zoom-high flip-f0 | -0.0089286 | -0.0089286 | 0 | 0.001 | match |
| M2 dose H1 asrun strict zoom-high dAcc CI lo | 0 | 0 | 0 | 0.01 | match |
| M2 dose H1 asrun strict zoom-high dAcc CI hi | 0.14545 | 0.14286 | 0.0025974 | 0.01 | match |
| M2 dose H1 asrun strict zoom-high p_dacc | 0.0656 | 0.0664 | 0.0008 | 0.020218 | match |
| M2 dose H1 asrun strict zoom-high p_flip | 0.5802 | 0.5883 | 0.0081 | 0.0403 | match |
| M2 dose H1 asrun strict zoom-high Holm-22 dAcc | 0.7216 | 0.7304 | 0.0088 | 0.8866 | match |
| M2 dose H1 asrun strict zoom-high Holm-22 flip | 1 | 1 | 0 | 0.8866 | match |
| M2 dose H1 s1 f0 | 0.2463 | 0.2463 | 0 | 0.001 | match |
| M2 dose H1 s1 brightness-low n | 180 | 180 | 0 | 0 | match |
| M2 dose H1 s1 brightness-low dAcc | 0.013889 | 0.013889 | 0 | 0.001 | match |
| M2 dose H1 s1 brightness-low flip | 0.11667 | 0.11667 | 0 | 0.001 | match |
| M2 dose H1 s1 brightness-low flip-f0 | -0.12963 | -0.12963 | 0 | 0.001 | match |
| M2 dose H1 s1 brightness-low dAcc CI lo | -0.011111 | -0.011111 | 0 | 0.01 | match |
| M2 dose H1 s1 brightness-low dAcc CI hi | 0.041667 | 0.041667 | 0 | 0.01 | match |
| M2 dose H1 s1 brightness-low flip CI lo | 0.072222 | 0.072222 | 0 | 0.01 | match |
| M2 dose H1 s1 brightness-low flip CI hi | 0.16667 | 0.16667 | 0 | 0.01 | match |
| M2 dose H1 s1 brightness-low p_dacc | 0.3482 | 0.3528 | 0.0046 | 0.038527 | match |
| M2 dose H1 s1 brightness-low p_flip | 1 | 1 | 0 | 0.0403 | match |
| M2 dose H1 s1 brightness-low Holm-22 dAcc | 1 | 1 | 0 | 0.8866 | match |
| M2 dose H1 s1 brightness-low Holm-22 flip | 1 | 1 | 0 | 0.8866 | match |
| M2 dose H1 s1 brightness-mid n | 180 | 180 | 0 | 0 | match |
| M2 dose H1 s1 brightness-mid dAcc | 0.027778 | 0.027778 | 0 | 0.001 | match |
| M2 dose H1 s1 brightness-mid flip | 0.16111 | 0.16111 | 0 | 0.001 | match |
| M2 dose H1 s1 brightness-mid flip-f0 | -0.085185 | -0.085185 | 0 | 0.001 | match |
| M2 dose H1 s1 brightness-mid dAcc CI lo | -0.0083333 | -0.0083333 | 0 | 0.01 | match |
| M2 dose H1 s1 brightness-mid dAcc CI hi | 0.066667 | 0.063889 | 0.0027778 | 0.01 | match |
| M2 dose H1 s1 brightness-mid flip CI lo | 0.11111 | 0.11111 | 0 | 0.01 | match |
| M2 dose H1 s1 brightness-mid flip CI hi | 0.21667 | 0.21667 | 0 | 0.01 | match |
| M2 dose H1 s1 brightness-mid p_dacc | 0.1512 | 0.1492 | 0.002 | 0.028959 | match |
| M2 dose H1 s1 brightness-mid p_flip | 0.9996 | 0.9997 | 0.0001 | 0.0403 | match |
| M2 dose H1 s1 brightness-mid Holm-22 dAcc | 1 | 1 | 0 | 0.8866 | match |
| M2 dose H1 s1 brightness-mid Holm-22 flip | 1 | 1 | 0 | 0.8866 | match |
| M2 dose H1 s1 brightness-high n | 180 | 180 | 0 | 0 | match |
| M2 dose H1 s1 brightness-high dAcc | -0.0055556 | -0.0055556 | 0 | 0.001 | match |
| M2 dose H1 s1 brightness-high flip | 0.15 | 0.15 | 0 | 0.001 | match |
| M2 dose H1 s1 brightness-high flip-f0 | -0.096296 | -0.096296 | 0 | 0.001 | match |
| M2 dose H1 s1 brightness-high dAcc CI lo | -0.044444 | -0.044444 | 0 | 0.01 | match |
| M2 dose H1 s1 brightness-high dAcc CI hi | 0.036111 | 0.036111 | 0 | 0.01 | match |
| M2 dose H1 s1 brightness-high flip CI lo | 0.094444 | 0.094444 | 0 | 0.01 | match |
| M2 dose H1 s1 brightness-high flip CI hi | 0.20556 | 0.20556 | 0 | 0.01 | match |
| M2 dose H1 s1 brightness-high p_dacc | 0.8328 | 0.8444 | 0.0116 | 0.0403 | match |
| M2 dose H1 s1 brightness-high p_flip | 0.9999 | 1 | 0.0001 | 0.0403 | match |
| M2 dose H1 s1 brightness-high Holm-22 dAcc | 1 | 1 | 0 | 0.8866 | match |
| M2 dose H1 s1 brightness-high Holm-22 flip | 1 | 1 | 0 | 0.8866 | match |
| M2 dose H1 s1 noise-low n | 180 | 180 | 0 | 0 | match |
| M2 dose H1 s1 noise-low dAcc | -0.044444 | -0.044444 | 0 | 0.001 | match |
| M2 dose H1 s1 noise-low flip | 0.26111 | 0.26111 | 0 | 0.001 | match |
| M2 dose H1 s1 noise-low flip-f0 | 0.014815 | 0.014815 | 0 | 0.001 | match |
| M2 dose H1 s1 noise-low dAcc CI lo | -0.10278 | -0.10278 | 0 | 0.01 | match |
| M2 dose H1 s1 noise-low dAcc CI hi | 0.013889 | 0.013889 | 0 | 0.01 | match |
| M2 dose H1 s1 noise-low flip CI lo | 0.2 | 0.2 | 0 | 0.01 | match |
| M2 dose H1 s1 noise-low flip CI hi | 0.32222 | 0.32222 | 0 | 0.01 | match |
| M2 dose H1 s1 noise-low p_dacc | 0.146 | 0.1512 | 0.0052 | 0.028959 | match |
| M2 dose H1 s1 noise-low p_flip | 0.1987 | 0.2086 | 0.0099 | 0.032805 | match |
| M2 dose H1 s1 noise-low Holm-22 dAcc | 1 | 1 | 0 | 0.8866 | match |
| M2 dose H1 s1 noise-low Holm-22 flip | 1 | 1 | 0 | 0.8866 | match |
| M2 dose H1 s1 noise-mid n | 180 | 180 | 0 | 0 | match |
| M2 dose H1 s1 noise-mid dAcc | -0.080556 | -0.080556 | 0 | 0.001 | match |
| M2 dose H1 s1 noise-mid flip | 0.3 | 0.3 | 0 | 0.001 | match |
| M2 dose H1 s1 noise-mid flip-f0 | 0.053704 | 0.053704 | 0 | 0.001 | match |
| M2 dose H1 s1 noise-mid dAcc CI lo | -0.13889 | -0.13889 | 0 | 0.01 | match |
| M2 dose H1 s1 noise-mid dAcc CI hi | -0.022222 | -0.022222 | 0 | 0.01 | match |
| M2 dose H1 s1 noise-mid flip CI lo | 0.23333 | 0.23333 | 0 | 0.01 | match |
| M2 dose H1 s1 noise-mid flip CI hi | 0.36667 | 0.36667 | 0 | 0.01 | match |
| M2 dose H1 s1 noise-mid p_dacc | 0.0074 | 0.0064 | 0.001 | 0.0071564 | match |
| M2 dose H1 s1 noise-mid p_flip | 0.0205 | 0.0204 | 0.0001 | 0.011636 | match |
| M2 dose H1 s1 noise-mid Holm-22 dAcc | 0.1036 | 0.096 | 0.0076 | 0.54294 | match |
| M2 dose H1 s1 noise-mid Holm-22 flip | 0.246 | 0.2448 | 0.0012 | 0.76459 | match |
| M2 dose H1 s1 noise-high n | 180 | 180 | 0 | 0 | match |
| M2 dose H1 s1 noise-high dAcc | -0.077778 | -0.077778 | 0 | 0.001 | match |
| M2 dose H1 s1 noise-high flip | 0.25556 | 0.25556 | 0 | 0.001 | match |
| M2 dose H1 s1 noise-high flip-f0 | 0.0092593 | 0.0092593 | 0 | 0.001 | match |
| M2 dose H1 s1 noise-high dAcc CI lo | -0.13056 | -0.13056 | 0 | 0.01 | match |
| M2 dose H1 s1 noise-high dAcc CI hi | -0.025 | -0.025 | 0 | 0.01 | match |
| M2 dose H1 s1 noise-high flip CI lo | 0.19444 | 0.19444 | 0 | 0.01 | match |
| M2 dose H1 s1 noise-high flip CI hi | 0.31667 | 0.31667 | 0 | 0.01 | match |
| M2 dose H1 s1 noise-high p_dacc | 0.0052 | 0.006 | 0.0008 | 0.0064782 | match |
| M2 dose H1 s1 noise-high p_flip | 0.3627 | 0.3589 | 0.0038 | 0.038762 | match |
| M2 dose H1 s1 noise-high Holm-22 dAcc | 0.0832 | 0.096 | 0.0128 | 0.52508 | match |
| M2 dose H1 s1 noise-high Holm-22 flip | 1 | 1 | 0 | 0.8866 | match |
| M2 dose H1 s1 blur-low n | 180 | 180 | 0 | 0 | match |
| M2 dose H1 s1 blur-low dAcc | 0.15833 | 0.15833 | 0 | 0.001 | match |
| M2 dose H1 s1 blur-low flip | 0.35556 | 0.35556 | 0 | 0.001 | match |
| M2 dose H1 s1 blur-low flip-f0 | 0.10926 | 0.10926 | 0 | 0.001 | match |
| M2 dose H1 s1 blur-low dAcc CI lo | 0.1 | 0.1 | 0 | 0.01 | match |
| M2 dose H1 s1 blur-low dAcc CI hi | 0.21944 | 0.21944 | 0 | 0.01 | match |
| M2 dose H1 s1 blur-low flip CI lo | 0.27778 | 0.27778 | 0 | 0.01 | match |
| M2 dose H1 s1 blur-low flip CI hi | 0.43333 | 0.43333 | 0 | 0.01 | match |
| M2 dose H1 s1 blur-low p_dacc | 0 | 0 | 0 | 0.0011 | match |
| M2 dose H1 s1 blur-low p_flip | 0.0045 | 0.0038 | 0.0007 | 0.0056545 | match |
| M2 dose H1 s1 blur-low Holm-22 dAcc | 0 | 0 | 0 | 0.024199 | match |
| M2 dose H1 s1 blur-low Holm-22 flip | 0.0765 | 0.0646 | 0.0119 | 0.4744 | match |
| M2 dose H1 s1 blur-mid n | 180 | 180 | 0 | 0 | match |
| M2 dose H1 s1 blur-mid dAcc | 0.18611 | 0.18611 | 0 | 0.001 | match |
| M2 dose H1 s1 blur-mid flip | 0.34444 | 0.34444 | 0 | 0.001 | match |
| M2 dose H1 s1 blur-mid flip-f0 | 0.098148 | 0.098148 | 0 | 0.001 | match |
| M2 dose H1 s1 blur-mid dAcc CI lo | 0.13056 | 0.13056 | 0 | 0.01 | match |
| M2 dose H1 s1 blur-mid dAcc CI hi | 0.24444 | 0.24444 | 0 | 0.01 | match |
| M2 dose H1 s1 blur-mid flip CI lo | 0.27222 | 0.26667 | 0.0055556 | 0.01 | match |
| M2 dose H1 s1 blur-mid flip CI hi | 0.41667 | 0.42222 | 0.0055556 | 0.01 | match |
| M2 dose H1 s1 blur-mid p_dacc | 0 | 0 | 0 | 0.0011 | match |
| M2 dose H1 s1 blur-mid p_flip | 0.0059 | 0.0063 | 0.0004 | 0.0066298 | match |
| M2 dose H1 s1 blur-mid Holm-22 dAcc | 0 | 0 | 0 | 0.024199 | match |
| M2 dose H1 s1 blur-mid Holm-22 flip | 0.0885 | 0.096 | 0.0075 | 0.52508 | match |
| M2 dose H1 s1 blur-high n | 180 | 180 | 0 | 0 | match |
| M2 dose H1 s1 blur-high dAcc | 0.12778 | 0.12778 | 0 | 0.001 | match |
| M2 dose H1 s1 blur-high flip | 0.42222 | 0.42222 | 0 | 0.001 | match |
| M2 dose H1 s1 blur-high flip-f0 | 0.17593 | 0.17593 | 0 | 0.001 | match |
| M2 dose H1 s1 blur-high dAcc CI lo | 0.063889 | 0.063889 | 0 | 0.01 | match |
| M2 dose H1 s1 blur-high dAcc CI hi | 0.19167 | 0.19444 | 0.0027778 | 0.01 | match |
| M2 dose H1 s1 blur-high flip CI lo | 0.34444 | 0.34444 | 0 | 0.01 | match |
| M2 dose H1 s1 blur-high flip CI hi | 0.5 | 0.5 | 0 | 0.01 | match |
| M2 dose H1 s1 blur-high p_dacc | 0 | 0.0004 | 0.0004 | 0.0018997 | match |
| M2 dose H1 s1 blur-high p_flip | 0 | 0 | 0 | 0.0011 | match |
| M2 dose H1 s1 blur-high Holm-22 dAcc | 0 | 0.0072 | 0.0072 | 0.1554 | match |
| M2 dose H1 s1 blur-high Holm-22 flip | 0 | 0 | 0 | 0.024199 | match |
| M2 dose H1 s1 jpeg-high n | 180 | 180 | 0 | 0 | match |
| M2 dose H1 s1 jpeg-high dAcc | -0.016667 | -0.016667 | 0 | 0.001 | match |
| M2 dose H1 s1 jpeg-high flip | 0.40556 | 0.40556 | 0 | 0.001 | match |
| M2 dose H1 s1 jpeg-high flip-f0 | 0.15926 | 0.15926 | 0 | 0.001 | match |
| M2 dose H1 s1 jpeg-high dAcc CI lo | -0.077778 | -0.077778 | 0 | 0.01 | match |
| M2 dose H1 s1 jpeg-high dAcc CI hi | 0.044444 | 0.047222 | 0.0027778 | 0.01 | match |
| M2 dose H1 s1 jpeg-high flip CI lo | 0.32778 | 0.32778 | 0 | 0.01 | match |
| M2 dose H1 s1 jpeg-high flip CI hi | 0.48333 | 0.48333 | 0 | 0.01 | match |
| M2 dose H1 s1 jpeg-high p_dacc | 0.6118 | 0.6118 | 0 | 0.0403 | match |
| M2 dose H1 s1 jpeg-high p_flip | 0 | 0 | 0 | 0.0011 | match |
| M2 dose H1 s1 jpeg-high Holm-22 dAcc | 1 | 1 | 0 | 0.8866 | match |
| M2 dose H1 s1 jpeg-high Holm-22 flip | 0 | 0 | 0 | 0.024199 | match |
| M2 dose H1 s1 zoom-high n | 112 | 112 | 0 | 0 | match |
| M2 dose H1 s1 zoom-high dAcc | 0.071429 | 0.071429 | 0 | 0.001 | match |
| M2 dose H1 s1 zoom-high flip | 0.25 | 0.25 | 0 | 0.001 | match |
| M2 dose H1 s1 zoom-high flip-f0 | -0.056548 | -0.056548 | 5.5511e-17 | 0.001 | match |
| M2 dose H1 s1 zoom-high dAcc CI lo | 0.017241 | 0.017857 | 0.00061576 | 0.01 | match |
| M2 dose H1 s1 zoom-high dAcc CI hi | 0.12755 | 0.12727 | 0.00027829 | 0.01 | match |
| M2 dose H1 s1 zoom-high flip CI lo | 0.16964 | 0.16667 | 0.0029724 | 0.01 | match |
| M2 dose H1 s1 zoom-high flip CI hi | 0.33871 | 0.33696 | 0.0017468 | 0.01 | match |
| M2 dose H1 s1 zoom-high p_dacc | 0.0114 | 0.012 | 0.0006 | 0.0090108 | match |
| M2 dose H1 s1 zoom-high p_flip | 0.9031 | 0.9062 | 0.0031 | 0.0403 | match |
| M2 dose H1 s1 zoom-high Holm-22 dAcc | 0.1482 | 0.156 | 0.0078 | 0.64523 | match |
| M2 dose H1 s1 zoom-high Holm-22 flip | 1 | 1 | 0 | 0.8866 | match |
| M2 dose H1 s1 strict f0 | 0.17407 | 0.17407 | 0 | 0.001 | match |
| M2 dose H1 s1 strict brightness-low n | 180 | 180 | 0 | 0 | match |
| M2 dose H1 s1 strict brightness-low dAcc | 0.016667 | 0.016667 | 0 | 0.001 | match |
| M2 dose H1 s1 strict brightness-low flip | 0.083333 | 0.083333 | 0 | 0.001 | match |
| M2 dose H1 s1 strict brightness-low flip-f0 | -0.090741 | -0.090741 | 0 | 0.001 | match |
| M2 dose H1 s1 strict brightness-low dAcc CI lo | -0.027778 | -0.027778 | 0 | 0.01 | match |
| M2 dose H1 s1 strict brightness-low dAcc CI hi | 0.061111 | 0.061111 | 0 | 0.01 | match |
| M2 dose H1 s1 strict brightness-low p_dacc | 0.5528 | 0.5332 | 0.0196 | 0.0403 | match |
| M2 dose H1 s1 strict brightness-low p_flip | 0.9994 | 0.9995 | 0.0001 | 0.0403 | match |
| M2 dose H1 s1 strict brightness-low Holm-22 dAcc | 1 | 1 | 0 | 0.8866 | match |
| M2 dose H1 s1 strict brightness-low Holm-22 flip | 1 | 1 | 0 | 0.8866 | match |
| M2 dose H1 s1 strict brightness-mid n | 180 | 180 | 0 | 0 | match |
| M2 dose H1 s1 strict brightness-mid dAcc | 0.027778 | 0.027778 | 0 | 0.001 | match |
| M2 dose H1 s1 strict brightness-mid flip | 0.094444 | 0.094444 | 0 | 0.001 | match |
| M2 dose H1 s1 strict brightness-mid flip-f0 | -0.07963 | -0.07963 | 0 | 0.001 | match |
| M2 dose H1 s1 strict brightness-mid dAcc CI lo | -0.016667 | -0.016667 | 0 | 0.01 | match |
| M2 dose H1 s1 strict brightness-mid dAcc CI hi | 0.072222 | 0.072222 | 0 | 0.01 | match |
| M2 dose H1 s1 strict brightness-mid p_dacc | 0.2558 | 0.2574 | 0.0016 | 0.035276 | match |
| M2 dose H1 s1 strict brightness-mid p_flip | 0.9956 | 0.9975 | 0.0019 | 0.0403 | match |
| M2 dose H1 s1 strict brightness-mid Holm-22 dAcc | 1 | 1 | 0 | 0.8866 | match |
| M2 dose H1 s1 strict brightness-mid Holm-22 flip | 1 | 1 | 0 | 0.8866 | match |
| M2 dose H1 s1 strict brightness-high n | 180 | 180 | 0 | 0 | match |
| M2 dose H1 s1 strict brightness-high dAcc | -0.016667 | -0.016667 | 0 | 0.001 | match |
| M2 dose H1 s1 strict brightness-high flip | 0.10556 | 0.10556 | 0 | 0.001 | match |
| M2 dose H1 s1 strict brightness-high flip-f0 | -0.068519 | -0.068519 | 0 | 0.001 | match |
| M2 dose H1 s1 strict brightness-high dAcc CI lo | -0.066667 | -0.066667 | 0 | 0.01 | match |
| M2 dose H1 s1 strict brightness-high dAcc CI hi | 0.033333 | 0.033333 | 0 | 0.01 | match |
| M2 dose H1 s1 strict brightness-high p_dacc | 0.5672 | 0.5778 | 0.0106 | 0.0403 | match |
| M2 dose H1 s1 strict brightness-high p_flip | 0.9946 | 0.996 | 0.0014 | 0.0403 | match |
| M2 dose H1 s1 strict brightness-high Holm-22 dAcc | 1 | 1 | 0 | 0.8866 | match |
| M2 dose H1 s1 strict brightness-high Holm-22 flip | 1 | 1 | 0 | 0.8866 | match |
| M2 dose H1 s1 strict noise-low n | 180 | 180 | 0 | 0 | match |
| M2 dose H1 s1 strict noise-low dAcc | -0.05 | -0.05 | 0 | 0.001 | match |
| M2 dose H1 s1 strict noise-low flip | 0.19444 | 0.19444 | 0 | 0.001 | match |
| M2 dose H1 s1 strict noise-low flip-f0 | 0.02037 | 0.02037 | 0 | 0.001 | match |
| M2 dose H1 s1 strict noise-low dAcc CI lo | -0.11111 | -0.11111 | 0 | 0.01 | match |
| M2 dose H1 s1 strict noise-low dAcc CI hi | 0.011111 | 0.011111 | 0 | 0.01 | match |
| M2 dose H1 s1 strict noise-low p_dacc | 0.1248 | 0.1346 | 0.0098 | 0.027604 | match |
| M2 dose H1 s1 strict noise-low p_flip | 0.0964 | 0.0948 | 0.0016 | 0.023911 | match |
| M2 dose H1 s1 strict noise-low Holm-22 dAcc | 1 | 1 | 0 | 0.8866 | match |
| M2 dose H1 s1 strict noise-low Holm-22 flip | 0.964 | 0.948 | 0.016 | 0.8866 | match |
| M2 dose H1 s1 strict noise-mid n | 180 | 180 | 0 | 0 | match |
| M2 dose H1 s1 strict noise-mid dAcc | -0.077778 | -0.077778 | 0 | 0.001 | match |
| M2 dose H1 s1 strict noise-mid flip | 0.23333 | 0.23333 | 0 | 0.001 | match |
| M2 dose H1 s1 strict noise-mid flip-f0 | 0.059259 | 0.059259 | 0 | 0.001 | match |
| M2 dose H1 s1 strict noise-mid dAcc CI lo | -0.15 | -0.15 | 0 | 0.01 | match |
| M2 dose H1 s1 strict noise-mid dAcc CI hi | -0.0055556 | -0.0055556 | 0 | 0.01 | match |
| M2 dose H1 s1 strict noise-mid p_dacc | 0.0396 | 0.0412 | 0.0016 | 0.0162 | match |
| M2 dose H1 s1 strict noise-mid p_flip | 0.0032 | 0.0027 | 0.0005 | 0.0048182 | match |
| M2 dose H1 s1 strict noise-mid Holm-22 dAcc | 0.4752 | 0.4944 | 0.0192 | 0.88654 | match |
| M2 dose H1 s1 strict noise-mid Holm-22 flip | 0.0512 | 0.0432 | 0.008 | 0.39451 | match |
| M2 dose H1 s1 strict noise-high n | 180 | 180 | 0 | 0 | match |
| M2 dose H1 s1 strict noise-high dAcc | -0.083333 | -0.083333 | 0 | 0.001 | match |
| M2 dose H1 s1 strict noise-high flip | 0.21667 | 0.21667 | 0 | 0.001 | match |
| M2 dose H1 s1 strict noise-high flip-f0 | 0.042593 | 0.042593 | 0 | 0.001 | match |
| M2 dose H1 s1 strict noise-high dAcc CI lo | -0.14444 | -0.15 | 0.0055556 | 0.01 | match |
| M2 dose H1 s1 strict noise-high dAcc CI hi | -0.022222 | -0.016667 | 0.0055556 | 0.01 | match |
| M2 dose H1 s1 strict noise-high p_dacc | 0.0118 | 0.0138 | 0.002 | 0.0096328 | match |
| M2 dose H1 s1 strict noise-high p_flip | 0.0139 | 0.0137 | 0.0002 | 0.0096661 | match |
| M2 dose H1 s1 strict noise-high Holm-22 dAcc | 0.1652 | 0.1918 | 0.0266 | 0.69954 | match |
| M2 dose H1 s1 strict noise-high Holm-22 flip | 0.1807 | 0.1918 | 0.0111 | 0.69954 | match |
| M2 dose H1 s1 strict blur-low n | 180 | 180 | 0 | 0 | match |
| M2 dose H1 s1 strict blur-low dAcc | 0.16111 | 0.16111 | 0 | 0.001 | match |
| M2 dose H1 s1 strict blur-low flip | 0.30556 | 0.30556 | 0 | 0.001 | match |
| M2 dose H1 s1 strict blur-low flip-f0 | 0.13148 | 0.13148 | 0 | 0.001 | match |
| M2 dose H1 s1 strict blur-low dAcc CI lo | 0.094444 | 0.094444 | 0 | 0.01 | match |
| M2 dose H1 s1 strict blur-low dAcc CI hi | 0.22778 | 0.22778 | 0 | 0.01 | match |
| M2 dose H1 s1 strict blur-low p_dacc | 0 | 0 | 0 | 0.0011 | match |
| M2 dose H1 s1 strict blur-low p_flip | 0.0008 | 0.0004 | 0.0004 | 0.0025618 | match |
| M2 dose H1 s1 strict blur-low Holm-22 dAcc | 0 | 0 | 0 | 0.024199 | match |
| M2 dose H1 s1 strict blur-low Holm-22 flip | 0.0136 | 0.0072 | 0.0064 | 0.21045 | match |
| M2 dose H1 s1 strict blur-mid n | 180 | 180 | 0 | 0 | match |
| M2 dose H1 s1 strict blur-mid dAcc | 0.18889 | 0.18889 | 0 | 0.001 | match |
| M2 dose H1 s1 strict blur-mid flip | 0.27778 | 0.27778 | 0 | 0.001 | match |
| M2 dose H1 s1 strict blur-mid flip-f0 | 0.1037 | 0.1037 | 0 | 0.001 | match |
| M2 dose H1 s1 strict blur-mid dAcc CI lo | 0.12778 | 0.12778 | 0 | 0.01 | match |
| M2 dose H1 s1 strict blur-mid dAcc CI hi | 0.25556 | 0.25556 | 0 | 0.01 | match |
| M2 dose H1 s1 strict blur-mid p_dacc | 0 | 0 | 0 | 0.0011 | match |
| M2 dose H1 s1 strict blur-mid p_flip | 0.0054 | 0.0056 | 0.0002 | 0.0062699 | match |
| M2 dose H1 s1 strict blur-mid Holm-22 dAcc | 0 | 0 | 0 | 0.024199 | match |
| M2 dose H1 s1 strict blur-mid Holm-22 flip | 0.081 | 0.084 | 0.003 | 0.4948 | match |
| M2 dose H1 s1 strict blur-high n | 180 | 180 | 0 | 0 | match |
| M2 dose H1 s1 strict blur-high dAcc | 0.14444 | 0.14444 | 0 | 0.001 | match |
| M2 dose H1 s1 strict blur-high flip | 0.31111 | 0.31111 | 0 | 0.001 | match |
| M2 dose H1 s1 strict blur-high flip-f0 | 0.13704 | 0.13704 | 0 | 0.001 | match |
| M2 dose H1 s1 strict blur-high dAcc CI lo | 0.072222 | 0.072222 | 0 | 0.01 | match |
| M2 dose H1 s1 strict blur-high dAcc CI hi | 0.21667 | 0.21667 | 0 | 0.01 | match |
| M2 dose H1 s1 strict blur-high p_dacc | 0 | 0.0004 | 0.0004 | 0.0018997 | match |
| M2 dose H1 s1 strict blur-high p_flip | 0 | 0.0003 | 0.0003 | 0.0016854 | match |
| M2 dose H1 s1 strict blur-high Holm-22 dAcc | 0 | 0.0072 | 0.0072 | 0.1554 | match |
| M2 dose H1 s1 strict blur-high Holm-22 flip | 0 | 0.0057 | 0.0057 | 0.1391 | match |
| M2 dose H1 s1 strict jpeg-high n | 180 | 180 | 0 | 0 | match |
| M2 dose H1 s1 strict jpeg-high dAcc | 0.016667 | 0.016667 | 0 | 0.001 | match |
| M2 dose H1 s1 strict jpeg-high flip | 0.35 | 0.35 | 0 | 0.001 | match |
| M2 dose H1 s1 strict jpeg-high flip-f0 | 0.17593 | 0.17593 | 0 | 0.001 | match |
| M2 dose H1 s1 strict jpeg-high dAcc CI lo | -0.05 | -0.055556 | 0.0055556 | 0.01 | match |
| M2 dose H1 s1 strict jpeg-high dAcc CI hi | 0.088889 | 0.088889 | 0 | 0.01 | match |
| M2 dose H1 s1 strict jpeg-high p_dacc | 0.7122 | 0.6986 | 0.0136 | 0.0403 | match |
| M2 dose H1 s1 strict jpeg-high p_flip | 0 | 0 | 0 | 0.0011 | match |
| M2 dose H1 s1 strict jpeg-high Holm-22 dAcc | 1 | 1 | 0 | 0.8866 | match |
| M2 dose H1 s1 strict jpeg-high Holm-22 flip | 0 | 0 | 0 | 0.024199 | match |
| M2 dose H1 s1 strict zoom-high n | 112 | 112 | 0 | 0 | match |
| M2 dose H1 s1 strict zoom-high dAcc | 0.071429 | 0.071429 | 0 | 0.001 | match |
| M2 dose H1 s1 strict zoom-high flip | 0.19643 | 0.19643 | 0 | 0.001 | match |
| M2 dose H1 s1 strict zoom-high flip-f0 | -0.0089286 | -0.0089286 | 0 | 0.001 | match |
| M2 dose H1 s1 strict zoom-high dAcc CI lo | 0 | 0 | 0 | 0.01 | match |
| M2 dose H1 s1 strict zoom-high dAcc CI hi | 0.14545 | 0.14286 | 0.0025974 | 0.01 | match |
| M2 dose H1 s1 strict zoom-high p_dacc | 0.0656 | 0.0664 | 0.0008 | 0.020218 | match |
| M2 dose H1 s1 strict zoom-high p_flip | 0.5802 | 0.5883 | 0.0081 | 0.0403 | match |
| M2 dose H1 s1 strict zoom-high Holm-22 dAcc | 0.7216 | 0.7304 | 0.0088 | 0.8866 | match |
| M2 dose H1 s1 strict zoom-high Holm-22 flip | 1 | 1 | 0 | 0.8866 | match |
| M2 spec dose low A | 0.48286 | 0.48286 | 5.5511e-17 | 0.002 | match |
| M2 spec dose low A CI lo | 0.4336 | 0.43387 | 0.00027595 | 0.01 | match |
| M2 spec dose low A CI hi | 0.53306 | 0.53303 | 3.4915e-05 | 0.01 | match |
| M2 spec dose low A_B1 | 0.3663 | 0.3663 | 0 | 0.002 | match |
| M2 spec dose low A_B2 | 0.42911 | 0.42911 | 0 | 0.002 | match |
| M2 spec dose low A_B3 | 0.36324 | 0.36324 | 5.5511e-17 | 0.002 | match |
| M2 spec dose low A0 | 0.6 | 0.6 | 0 | 0.001 | match |
| M2 spec dose low A lighting_global | 0.57968 | 0.57968 | 0 | 0.002 | match |
| M2 spec dose low A lighting_local | 0.41218 | 0.41218 | 0 | 0.002 | match |
| M2 spec dose low A jolt_base | 0.47961 | 0.47961 | 5.5511e-17 | 0.002 | match |
| M2 spec dose low A zoom_base | 0.45997 | 0.45997 | 0 | 0.002 | match |
| M2 spec dose low D_B1 | 0.11655 | 0.11655 | 5.5511e-17 | 0.002 | match |
| M2 spec dose low D_B1 CI lo | 0.068498 | 0.070525 | 0.0020269 | 0.01 | match |
| M2 spec dose low D_B1 CI hi | 0.16452 | 0.16466 | 0.00014246 | 0.01 | match |
| M2 spec dose low p_B1 | 9.999e-05 | 9.999e-05 | 0 | 0.0011 | match |
| M2 spec dose low D_B2 | 0.05375 | 0.05375 | 5.5511e-17 | 0.002 | match |
| M2 spec dose low D_B2 CI lo | -0.00092631 | 0.00051678 | 0.0014431 | 0.01 | match |
| M2 spec dose low D_B2 CI hi | 0.10746 | 0.10817 | 0.00070785 | 0.01 | match |
| M2 spec dose low p_B2 | 0.0278 | 0.0241 | 0.0037 | 0.013452 | match |
| M2 spec dose mid A | 0.44902 | 0.44902 | 0 | 0.002 | match |
| M2 spec dose mid A CI lo | 0.40284 | 0.40261 | 0.00023582 | 0.01 | match |
| M2 spec dose mid A CI hi | 0.49688 | 0.49711 | 0.00023544 | 0.01 | match |
| M2 spec dose mid A_B1 | 0.324 | 0.324 | 0 | 0.002 | match |
| M2 spec dose mid A_B2 | 0.37546 | 0.37546 | 0 | 0.002 | match |
| M2 spec dose mid A_B3 | 0.36717 | 0.36717 | 0 | 0.002 | match |
| M2 spec dose mid A0 | 0.6 | 0.6 | 0 | 0.001 | match |
| M2 spec dose mid A lighting_global | 0.55096 | 0.55096 | 0 | 0.002 | match |
| M2 spec dose mid A lighting_local | 0.35665 | 0.35665 | 0 | 0.002 | match |
| M2 spec dose mid A jolt_base | 0.44656 | 0.44656 | 0 | 0.002 | match |
| M2 spec dose mid A zoom_base | 0.44193 | 0.44193 | 0 | 0.002 | match |
| M2 spec dose mid D_B1 | 0.12503 | 0.12503 | 0 | 0.002 | match |
| M2 spec dose mid D_B1 CI lo | 0.076995 | 0.077866 | 0.00087153 | 0.01 | match |
| M2 spec dose mid D_B1 CI hi | 0.17344 | 0.17322 | 0.00022579 | 0.01 | match |
| M2 spec dose mid p_B1 | 9.999e-05 | 9.999e-05 | 0 | 0.0011 | match |
| M2 spec dose mid D_B2 | 0.073569 | 0.073569 | 0 | 0.002 | match |
| M2 spec dose mid D_B2 CI lo | 0.01995 | 0.021844 | 0.0018939 | 0.01 | match |
| M2 spec dose mid D_B2 CI hi | 0.1261 | 0.12607 | 3.0285e-05 | 0.01 | match |
| M2 spec dose mid p_B2 | 0.0029 | 0.0032 | 0.0003 | 0.0048182 | match |
| M2 spec dose high A | 0.42037 | 0.42037 | 0 | 0.002 | match |
| M2 spec dose high A CI lo | 0.37448 | 0.37469 | 0.00020882 | 0.01 | match |
| M2 spec dose high A CI hi | 0.46774 | 0.46862 | 0.0008804 | 0.01 | match |
| M2 spec dose high A_B1 | 0.27566 | 0.27566 | 0 | 0.002 | match |
| M2 spec dose high A_B2 | 0.31723 | 0.31723 | 0 | 0.002 | match |
| M2 spec dose high A_B3 | 0.38314 | 0.38314 | 0 | 0.002 | match |
| M2 spec dose high A0 | 0.6 | 0.6 | 0 | 0.001 | match |
| M2 spec dose high A lighting_global | 0.5339 | 0.5339 | 0 | 0.002 | match |
| M2 spec dose high A lighting_local | 0.32596 | 0.32596 | 0 | 0.002 | match |
| M2 spec dose high A jolt_base | 0.41597 | 0.41597 | 0 | 0.002 | match |
| M2 spec dose high A zoom_base | 0.40566 | 0.40566 | 0 | 0.002 | match |
| M2 spec dose high D_B1 | 0.14471 | 0.14471 | 0 | 0.002 | match |
| M2 spec dose high D_B1 CI lo | 0.096539 | 0.097858 | 0.0013193 | 0.01 | match |
| M2 spec dose high D_B1 CI hi | 0.19169 | 0.19392 | 0.0022275 | 0.01 | match |
| M2 spec dose high p_B1 | 9.999e-05 | 9.999e-05 | 0 | 0.0011 | match |
| M2 spec dose high D_B2 | 0.10314 | 0.10314 | 0 | 0.002 | match |
| M2 spec dose high D_B2 CI lo | 0.052934 | 0.055477 | 0.0025432 | 0.01 | match |
| M2 spec dose high D_B2 CI hi | 0.15167 | 0.1524 | 0.00072733 | 0.01 | match |
| M2 spec dose high p_B2 | 9.999e-05 | 9.999e-05 | 0 | 0.0011 | match |
| M2 spec dose low Holm-6 B1 | 0.00059994 | 0.00059994 | 0 | 0.013553 | match |
| M2 spec dose low Holm-6 B2 | 0.0278 | 0.0241 | 0.0037 | 0.080712 | match |
| M2 spec dose mid Holm-6 B1 | 0.00059994 | 0.00059994 | 0 | 0.013553 | match |
| M2 spec dose mid Holm-6 B2 | 0.0058 | 0.0064 | 0.0006 | 0.040077 | match |
| M2 spec dose high Holm-6 B1 | 0.00059994 | 0.00059994 | 0 | 0.013553 | match |
| M2 spec dose high Holm-6 B2 | 0.00059994 | 0.00059994 | 0 | 0.013553 | match |
| M2 spec dose low lighting_global A | 0.57968 | 0.57968 | 0 | 0.002 | match |
| M2 spec dose low lighting_global D_B1 | 0.15877 | 0.15877 | 5.5511e-17 | 0.002 | match |
| M2 spec dose low lighting_global D_B1 CI lo | 0.10304 | 0.10326 | 0.00021605 | 0.01 | match |
| M2 spec dose low lighting_global D_B1 CI hi | 0.21335 | 0.21512 | 0.0017739 | 0.01 | match |
| M2 spec dose low lighting_global p_B1 | 9.999e-05 | 9.999e-05 | 0 | 0.0011 | match |
| M2 spec dose low lighting_global Holm-24 B1 | 0.0023998 | 0.0023998 | 0 | 0.10114 | match |
| M2 spec dose low lighting_global D_B2 | 0.11002 | 0.11002 | 0 | 0.002 | match |
| M2 spec dose low lighting_global D_B2 CI lo | 0.049537 | 0.049888 | 0.00035108 | 0.01 | match |
| M2 spec dose low lighting_global D_B2 CI hi | 0.17114 | 0.17164 | 0.00049884 | 0.01 | match |
| M2 spec dose low lighting_global p_B2 | 0.0001 | 0.0002 | 0.0001 | 0.0014313 | match |
| M2 spec dose low lighting_global Holm-24 B2 | 0.0023998 | 0.0026 | 0.00020024 | 0.10497 | match |
| M2 spec dose low lighting_local A | 0.41218 | 0.41218 | 0 | 0.002 | match |
| M2 spec dose low lighting_local D_B1 | 0.098812 | 0.098812 | 0 | 0.002 | match |
| M2 spec dose low lighting_local D_B1 CI lo | 0.035154 | 0.036203 | 0.0010494 | 0.01 | match |
| M2 spec dose low lighting_local D_B1 CI hi | 0.16221 | 0.16303 | 0.00081752 | 0.01 | match |
| M2 spec dose low lighting_local p_B1 | 0.0017 | 0.0008 | 0.0009 | 0.0035957 | match |
| M2 spec dose low lighting_local Holm-24 B1 | 0.0187 | 0.0096 | 0.0091 | 0.26729 | match |
| M2 spec dose low lighting_local D_B2 | 0.046667 | 0.046667 | 0 | 0.002 | match |
| M2 spec dose low lighting_local D_B2 CI lo | -0.026591 | -0.021854 | 0.0047369 | 0.01 | match |
| M2 spec dose low lighting_local D_B2 CI hi | 0.11628 | 0.11531 | 0.00097184 | 0.01 | match |
| M2 spec dose low lighting_local p_B2 | 0.1014 | 0.0966 | 0.0048 | 0.024449 | match |
| M2 spec dose low lighting_local Holm-24 B2 | 0.6084 | 0.5796 | 0.0288 | 0.9672 | match |
| M2 spec dose low jolt_base A | 0.47961 | 0.47961 | 5.5511e-17 | 0.002 | match |
| M2 spec dose low jolt_base D_B1 | 0.10037 | 0.10037 | 5.5511e-17 | 0.002 | match |
| M2 spec dose low jolt_base D_B1 CI lo | 0.052111 | 0.052885 | 0.00077392 | 0.01 | match |
| M2 spec dose low jolt_base D_B1 CI hi | 0.14948 | 0.14989 | 0.00041628 | 0.01 | match |
| M2 spec dose low jolt_base p_B1 | 9.999e-05 | 9.999e-05 | 0 | 0.0011 | match |
| M2 spec dose low jolt_base Holm-24 B1 | 0.0023998 | 0.0023998 | 0 | 0.10114 | match |
| M2 spec dose low jolt_base D_B2 | 0.025818 | 0.025818 | 5.5511e-17 | 0.002 | match |
| M2 spec dose low jolt_base D_B2 CI lo | -0.02809 | -0.027809 | 0.00028086 | 0.01 | match |
| M2 spec dose low jolt_base D_B2 CI hi | 0.079338 | 0.080171 | 0.00083295 | 0.01 | match |
| M2 spec dose low jolt_base p_B2 | 0.1789 | 0.1696 | 0.0093 | 0.030961 | match |
| M2 spec dose low jolt_base Holm-24 B2 | 0.6084 | 0.5796 | 0.0288 | 0.9672 | match |
| M2 spec dose low zoom_base A | 0.45997 | 0.45997 | 0 | 0.002 | match |
| M2 spec dose low zoom_base D_B1 | 0.10827 | 0.10827 | 5.5511e-17 | 0.002 | match |
| M2 spec dose low zoom_base D_B1 CI lo | 0.058564 | 0.05929 | 0.00072569 | 0.01 | match |
| M2 spec dose low zoom_base D_B1 CI hi | 0.15772 | 0.15823 | 0.00050926 | 0.01 | match |
| M2 spec dose low zoom_base p_B1 | 9.999e-05 | 9.999e-05 | 0 | 0.0011 | match |
| M2 spec dose low zoom_base Holm-24 B1 | 0.0023998 | 0.0023998 | 0 | 0.10114 | match |
| M2 spec dose low zoom_base D_B2 | 0.0325 | 0.0325 | 0 | 0.002 | match |
| M2 spec dose low zoom_base D_B2 CI lo | -0.022207 | -0.02017 | 0.002037 | 0.01 | match |
| M2 spec dose low zoom_base D_B2 CI hi | 0.085402 | 0.085804 | 0.00040162 | 0.01 | match |
| M2 spec dose low zoom_base p_B2 | 0.1177 | 0.1196 | 0.0019 | 0.026259 | match |
| M2 spec dose low zoom_base Holm-24 B2 | 0.6084 | 0.5796 | 0.0288 | 0.9672 | match |
| M2 spec dose mid lighting_global A | 0.55096 | 0.55096 | 0 | 0.002 | match |
| M2 spec dose mid lighting_global D_B1 | 0.19131 | 0.19131 | 0 | 0.002 | match |
| M2 spec dose mid lighting_global D_B1 CI lo | 0.13367 | 0.13093 | 0.0027423 | 0.01 | match |
| M2 spec dose mid lighting_global D_B1 CI hi | 0.25086 | 0.2517 | 0.00084221 | 0.01 | match |
| M2 spec dose mid lighting_global p_B1 | 9.999e-05 | 9.999e-05 | 0 | 0.0011 | match |
| M2 spec dose mid lighting_global Holm-24 B1 | 0.0023998 | 0.0023998 | 0 | 0.10114 | match |
| M2 spec dose mid lighting_global D_B2 | 0.15781 | 0.15781 | 5.5511e-17 | 0.002 | match |
| M2 spec dose mid lighting_global D_B2 CI lo | 0.096463 | 0.096063 | 0.00040008 | 0.01 | match |
| M2 spec dose mid lighting_global D_B2 CI hi | 0.22136 | 0.22204 | 0.0006794 | 0.01 | match |
| M2 spec dose mid lighting_global p_B2 | 9.999e-05 | 9.999e-05 | 0 | 0.0011 | match |
| M2 spec dose mid lighting_global Holm-24 B2 | 0.0023998 | 0.0023998 | 0 | 0.10114 | match |
| M2 spec dose mid lighting_local A | 0.35665 | 0.35665 | 0 | 0.002 | match |
| M2 spec dose mid lighting_local D_B1 | 0.084645 | 0.084645 | 0 | 0.002 | match |
| M2 spec dose mid lighting_local D_B1 CI lo | 0.016666 | 0.017066 | 0.00039969 | 0.01 | match |
| M2 spec dose mid lighting_local D_B1 CI hi | 0.15272 | 0.15338 | 0.00066397 | 0.01 | match |
| M2 spec dose mid lighting_local p_B1 | 0.0086 | 0.0058 | 0.0028 | 0.0076869 | match |
| M2 spec dose mid lighting_local Holm-24 B1 | 0.0688 | 0.0464 | 0.0224 | 0.49318 | match |
| M2 spec dose mid lighting_local D_B2 | 0.040741 | 0.040741 | 0 | 0.002 | match |
| M2 spec dose mid lighting_local D_B2 CI lo | -0.030232 | -0.028165 | 0.0020671 | 0.01 | match |
| M2 spec dose mid lighting_local D_B2 CI hi | 0.1113 | 0.10999 | 0.001311 | 0.01 | match |
| M2 spec dose mid lighting_local p_B2 | 0.1265 | 0.1236 | 0.0029 | 0.026893 | match |
| M2 spec dose mid lighting_local Holm-24 B2 | 0.6084 | 0.5796 | 0.0288 | 0.9672 | match |
| M2 spec dose mid jolt_base A | 0.44656 | 0.44656 | 0 | 0.002 | match |
| M2 spec dose mid jolt_base D_B1 | 0.090679 | 0.090679 | 0 | 0.002 | match |
| M2 spec dose mid jolt_base D_B1 CI lo | 0.043054 | 0.043981 | 0.00092631 | 0.01 | match |
| M2 spec dose mid jolt_base D_B1 CI hi | 0.13943 | 0.13875 | 0.00068056 | 0.01 | match |
| M2 spec dose mid jolt_base p_B1 | 9.999e-05 | 9.999e-05 | 0 | 0.0011 | match |
| M2 spec dose mid jolt_base Holm-24 B1 | 0.0023998 | 0.0023998 | 0 | 0.10114 | match |
| M2 spec dose mid jolt_base D_B2 | 0.022994 | 0.022994 | 0 | 0.002 | match |
| M2 spec dose mid jolt_base D_B2 CI lo | -0.032316 | -0.031467 | 0.00084915 | 0.01 | match |
| M2 spec dose mid jolt_base D_B2 CI hi | 0.075988 | 0.076452 | 0.00046335 | 0.01 | match |
| M2 spec dose mid jolt_base p_B2 | 0.2001 | 0.2021 | 0.002 | 0.032425 | match |
| M2 spec dose mid jolt_base Holm-24 B2 | 0.6084 | 0.5796 | 0.0288 | 0.9672 | match |
| M2 spec dose mid zoom_base A | 0.44193 | 0.44193 | 0 | 0.002 | match |
| M2 spec dose mid zoom_base D_B1 | 0.13347 | 0.13347 | 0 | 0.002 | match |
| M2 spec dose mid zoom_base D_B1 CI lo | 0.080431 | 0.081558 | 0.0011269 | 0.01 | match |
| M2 spec dose mid zoom_base D_B1 CI hi | 0.1863 | 0.1859 | 0.00040123 | 0.01 | match |
| M2 spec dose mid zoom_base p_B1 | 9.999e-05 | 9.999e-05 | 0 | 0.0011 | match |
| M2 spec dose mid zoom_base Holm-24 B1 | 0.0023998 | 0.0023998 | 0 | 0.10114 | match |
| M2 spec dose mid zoom_base D_B2 | 0.072731 | 0.072731 | 0 | 0.002 | match |
| M2 spec dose mid zoom_base D_B2 CI lo | 0.016882 | 0.017577 | 0.00069483 | 0.01 | match |
| M2 spec dose mid zoom_base D_B2 CI hi | 0.12608 | 0.12665 | 0.00057099 | 0.01 | match |
| M2 spec dose mid zoom_base p_B2 | 0.0055 | 0.0047 | 0.0008 | 0.0062166 | match |
| M2 spec dose mid zoom_base Holm-24 B2 | 0.0495 | 0.0423 | 0.0072 | 0.42367 | match |
| M2 spec dose high lighting_global A | 0.5339 | 0.5339 | 0 | 0.002 | match |
| M2 spec dose high lighting_global D_B1 | 0.2586 | 0.2586 | 0 | 0.002 | match |
| M2 spec dose high lighting_global D_B1 CI lo | 0.20098 | 0.19859 | 0.0023904 | 0.01 | match |
| M2 spec dose high lighting_global D_B1 CI hi | 0.31887 | 0.31991 | 0.0010328 | 0.01 | match |
| M2 spec dose high lighting_global p_B1 | 9.999e-05 | 9.999e-05 | 0 | 0.0011 | match |
| M2 spec dose high lighting_global Holm-24 B1 | 0.0023998 | 0.0023998 | 0 | 0.10114 | match |
| M2 spec dose high lighting_global D_B2 | 0.22901 | 0.22901 | 0 | 0.002 | match |
| M2 spec dose high lighting_global D_B2 CI lo | 0.16693 | 0.16614 | 0.00078974 | 0.01 | match |
| M2 spec dose high lighting_global D_B2 CI hi | 0.29148 | 0.29404 | 0.002561 | 0.01 | match |
| M2 spec dose high lighting_global p_B2 | 9.999e-05 | 9.999e-05 | 0 | 0.0011 | match |
| M2 spec dose high lighting_global Holm-24 B2 | 0.0023998 | 0.0023998 | 0 | 0.10114 | match |
| M2 spec dose high lighting_local A | 0.32596 | 0.32596 | 0 | 0.002 | match |
| M2 spec dose high lighting_local D_B1 | 0.093827 | 0.093827 | 2.7756e-17 | 0.002 | match |
| M2 spec dose high lighting_local D_B1 CI lo | 0.024379 | 0.025477 | 0.0010976 | 0.01 | match |
| M2 spec dose high lighting_local D_B1 CI hi | 0.16323 | 0.16389 | 0.00066397 | 0.01 | match |
| M2 spec dose high lighting_local p_B1 | 0.0043 | 0.0034 | 0.0009 | 0.0055347 | match |
| M2 spec dose high lighting_local Holm-24 B1 | 0.043 | 0.034 | 0.009 | 0.39669 | match |
| M2 spec dose high lighting_local D_B2 | 0.066235 | 0.066235 | 0 | 0.002 | match |
| M2 spec dose high lighting_local D_B2 CI lo | 0.00024653 | 0.0021292 | 0.0018827 | 0.01 | match |
| M2 spec dose high lighting_local D_B2 CI hi | 0.13244 | 0.13142 | 0.0010197 | 0.01 | match |
| M2 spec dose high lighting_local p_B2 | 0.0247 | 0.0207 | 0.004 | 0.012717 | match |
| M2 spec dose high lighting_local Holm-24 B2 | 0.1729 | 0.1449 | 0.028 | 0.73327 | match |
| M2 spec dose high jolt_base A | 0.41597 | 0.41597 | 0 | 0.002 | match |
| M2 spec dose high jolt_base D_B1 | 0.090355 | 0.090355 | 0 | 0.002 | match |
| M2 spec dose high jolt_base D_B1 CI lo | 0.040478 | 0.041358 | 0.00088002 | 0.01 | match |
| M2 spec dose high jolt_base D_B1 CI hi | 0.14139 | 0.14113 | 0.00026157 | 0.01 | match |
| M2 spec dose high jolt_base p_B1 | 0.0002 | 0.0001 | 0.0001 | 0.0014313 | match |
| M2 spec dose high jolt_base Holm-24 B1 | 0.0026 | 0.0023998 | 0.00020024 | 0.10497 | match |
| M2 spec dose high jolt_base D_B2 | 0.032454 | 0.032454 | 0 | 0.002 | match |
| M2 spec dose high jolt_base D_B2 CI lo | -0.020833 | -0.019245 | 0.0015883 | 0.01 | match |
| M2 spec dose high jolt_base D_B2 CI hi | 0.08216 | 0.083998 | 0.001838 | 0.01 | match |
| M2 spec dose high jolt_base p_B2 | 0.1117 | 0.1108 | 0.0009 | 0.0255 | match |
| M2 spec dose high jolt_base Holm-24 B2 | 0.6084 | 0.5796 | 0.0288 | 0.9672 | match |
| M2 spec dose high zoom_base A | 0.40566 | 0.40566 | 0 | 0.002 | match |
| M2 spec dose high zoom_base D_B1 | 0.13606 | 0.13606 | 0 | 0.002 | match |
| M2 spec dose high zoom_base D_B1 CI lo | 0.083071 | 0.084967 | 0.0018966 | 0.01 | match |
| M2 spec dose high zoom_base D_B1 CI hi | 0.18813 | 0.18826 | 0.00012461 | 0.01 | match |
| M2 spec dose high zoom_base p_B1 | 9.999e-05 | 9.999e-05 | 0 | 0.0011 | match |
| M2 spec dose high zoom_base Holm-24 B1 | 0.0023998 | 0.0023998 | 0 | 0.10114 | match |
| M2 spec dose high zoom_base D_B2 | 0.084877 | 0.084877 | 0 | 0.002 | match |
| M2 spec dose high zoom_base D_B2 CI lo | 0.031296 | 0.032252 | 0.00095563 | 0.01 | match |
| M2 spec dose high zoom_base D_B2 CI hi | 0.13628 | 0.13537 | 0.00090895 | 0.01 | match |
| M2 spec dose high zoom_base p_B2 | 0.0015 | 0.0008 | 0.0007 | 0.0033961 | match |
| M2 spec dose high zoom_base Holm-24 B2 | 0.018 | 0.0096 | 0.0084 | 0.26247 | match |
| abl A1_full_max A | 0.55292 | 0.55292 | 0 | 0.002 | match |
| abl A1_full_max A CI lo | 0.51278 | 0.51315 | 0.00036854 | 0.01 | match |
| abl A1_full_max A CI hi | 0.59333 | 0.59409 | 0.00075624 | 0.01 | match |
| abl A1_full_max A0 | 0.725 | 0.725 | 0 | 0.001 | match |
| abl A1_full_max A lighting_global | 0.62529 | 0.62529 | 0 | 0.002 | match |
| abl A1_full_max A lighting_local | 0.49452 | 0.49452 | 0 | 0.002 | match |
| abl A1_full_max A jolt_base | 0.56062 | 0.56062 | 0 | 0.002 | match |
| abl A1_full_max A zoom_base | 0.53123 | 0.53123 | 0 | 0.002 | match |
| abl A1_full_max A_B1 | 0.39454 | 0.39454 | 0 | 0.002 | match |
| abl A1_full_max A0_B1 | 0.58333 | 0.58333 | 0 | 0.001 | match |
| abl A1_full_max A_B1 CI lo | 0.35807 | 0.35767 | 0.00040082 | 0.01 | match |
| abl A1_full_max A_B1 CI hi | 0.43256 | 0.432 | 0.00055842 | 0.01 | match |
| abl A1_full_max A_B2 | 0.47088 | 0.47088 | 0 | 0.002 | match |
| abl A1_full_max A0_B2 | 0.64444 | 0.64444 | 0 | 0.001 | match |
| abl A1_full_max A_B2 CI lo | 0.43483 | 0.43413 | 0.00070923 | 0.01 | match |
| abl A1_full_max A_B2 CI hi | 0.50858 | 0.50908 | 0.00050074 | 0.01 | match |
| abl A1_full_max A_B3 | 0.55069 | 0.55069 | 0 | 0.002 | match |
| abl A1_full_max A0_B3 | 0.62222 | 0.62222 | 0 | 0.001 | match |
| abl A1_full_max A_B3 CI lo | 0.50836 | 0.50855 | 0.00019245 | 0.01 | match |
| abl A1_full_max A_B3 CI hi | 0.59237 | 0.59198 | 0.00039333 | 0.01 | match |
| abl A1_full_max D_B1 | 0.15837 | 0.15837 | 0 | 0.002 | match |
| abl A1_full_max D_B1 CI lo | 0.10976 | 0.10999 | 0.00023483 | 0.01 | match |
| abl A1_full_max D_B1 CI hi | 0.20859 | 0.20921 | 0.0006132 | 0.01 | match |
| abl A1_full_max p_B1 | 9.999e-05 | 9.999e-05 | 0 | 0.0011 | match |
| abl A1_full_max Holm-2 B1 | 0.00019998 | 0.00019998 | 0 | 0.0028624 | match |
| abl A1_full_max D_B2 | 0.082038 | 0.082038 | 0 | 0.002 | match |
| abl A1_full_max D_B2 CI lo | 0.035819 | 0.036061 | 0.00024199 | 0.01 | match |
| abl A1_full_max D_B2 CI hi | 0.12811 | 0.12924 | 0.0011338 | 0.01 | match |
| abl A1_full_max p_B2 | 0.0001 | 0.0004 | 0.0003 | 0.0018997 | match |
| abl A1_full_max Holm-2 B2 | 0.00019998 | 0.0004 | 0.00020002 | 0.0037994 | match |
| abl A1_full_max clean | 0.725 | 0.725 | 0 | 0.001 | match |
| abl A1_mean A | 0.59297 | 0.59297 | 0 | 0.002 | match |
| abl A1_mean A CI lo | 0.54539 | 0.54679 | 0.0014015 | 0.01 | match |
| abl A1_mean A CI hi | 0.64262 | 0.64259 | 2.7488e-05 | 0.01 | match |
| abl A1_mean A0 | 0.80833 | 0.80833 | 0 | 0.001 | match |
| abl A1_mean A lighting_global | 0.69577 | 0.69577 | 0 | 0.002 | match |
| abl A1_mean A lighting_local | 0.4986 | 0.4986 | 0 | 0.002 | match |
| abl A1_mean A jolt_base | 0.59976 | 0.59976 | 0 | 0.002 | match |
| abl A1_mean A zoom_base | 0.57775 | 0.57775 | 0 | 0.002 | match |
| abl A1_mean A_B1 | 0.37833 | 0.37833 | 5.5511e-17 | 0.002 | match |
| abl A1_mean A0_B1 | 0.58056 | 0.58056 | 0 | 0.001 | match |
| abl A1_mean A_B1 CI lo | 0.33765 | 0.33671 | 0.00094628 | 0.01 | match |
| abl A1_mean A_B1 CI hi | 0.41782 | 0.41751 | 0.00031179 | 0.01 | match |
| abl A1_mean A_B2 | 0.44458 | 0.44458 | 0 | 0.002 | match |
| abl A1_mean A0_B2 | 0.76111 | 0.76111 | 0 | 0.001 | match |
| abl A1_mean A_B2 CI lo | 0.39532 | 0.39575 | 0.0004349 | 0.01 | match |
| abl A1_mean A_B2 CI hi | 0.49772 | 0.49733 | 0.00039529 | 0.01 | match |
| abl A1_mean A_B3 | 0.49779 | 0.49779 | 0 | 0.002 | match |
| abl A1_mean A0_B3 | 0.45278 | 0.45278 | 0 | 0.001 | match |
| abl A1_mean A_B3 CI lo | 0.45378 | 0.45307 | 0.00071248 | 0.01 | match |
| abl A1_mean A_B3 CI hi | 0.5411 | 0.54162 | 0.00051415 | 0.01 | match |
| abl A1_mean D_B1 | 0.21464 | 0.21464 | 5.5511e-17 | 0.002 | match |
| abl A1_mean D_B1 CI lo | 0.15306 | 0.15595 | 0.0028933 | 0.01 | match |
| abl A1_mean D_B1 CI hi | 0.27674 | 0.27799 | 0.0012493 | 0.01 | match |
| abl A1_mean p_B1 | 9.999e-05 | 9.999e-05 | 0 | 0.0011 | match |
| abl A1_mean Holm-2 B1 | 0.00019998 | 0.00019998 | 0 | 0.0028624 | match |
| abl A1_mean D_B2 | 0.14839 | 0.14839 | 0 | 0.002 | match |
| abl A1_mean D_B2 CI lo | 0.10393 | 0.10423 | 0.00030478 | 0.01 | match |
| abl A1_mean D_B2 CI hi | 0.19475 | 0.1951 | 0.00035536 | 0.01 | match |
| abl A1_mean p_B2 | 9.999e-05 | 9.999e-05 | 0 | 0.0011 | match |
| abl A1_mean Holm-2 B2 | 0.00019998 | 0.00019998 | 0 | 0.0028624 | match |
| abl A1_mean clean | 0.80833 | 0.80833 | 0 | 0.001 | match |
| abl A2_C2 A | 0.43771 | 0.43771 | 5.5511e-17 | 0.002 | match |
| abl A2_C2 A CI lo | 0.38814 | 0.38847 | 0.00033626 | 0.01 | match |
| abl A2_C2 A CI hi | 0.48725 | 0.4877 | 0.00044821 | 0.01 | match |
| abl A2_C2 A0 | 0.48889 | 0.48889 | 0 | 0.001 | match |
| abl A2_C2 A lighting_global | 0.51059 | 0.51059 | 0 | 0.002 | match |
| abl A2_C2 A lighting_local | 0.34228 | 0.34228 | 0 | 0.002 | match |
| abl A2_C2 A jolt_base | 0.44875 | 0.44875 | 0 | 0.002 | match |
| abl A2_C2 A zoom_base | 0.44921 | 0.44921 | 0 | 0.002 | match |
| abl A2_C2 A_B1 | 0.35041 | 0.35041 | 5.5511e-17 | 0.002 | match |
| abl A2_C2 A0_B1 | 0.56111 | 0.56111 | 0 | 0.001 | match |
| abl A2_C2 A_B1 CI lo | 0.3084 | 0.30769 | 0.00071206 | 0.01 | match |
| abl A2_C2 A_B1 CI hi | 0.39277 | 0.39325 | 0.00047486 | 0.01 | match |
| abl A2_C2 A_B2 | 0.37479 | 0.37479 | 0 | 0.002 | match |
| abl A2_C2 A0_B2 | 0.66944 | 0.66944 | 0 | 0.001 | match |
| abl A2_C2 A_B2 CI lo | 0.32586 | 0.3268 | 0.00094235 | 0.01 | match |
| abl A2_C2 A_B2 CI hi | 0.42278 | 0.42265 | 0.00013027 | 0.01 | match |
| abl A2_C2 A_B3 | 0.58739 | 0.58739 | 0 | 0.002 | match |
| abl A2_C2 A0_B3 | 0.66111 | 0.66111 | 0 | 0.001 | match |
| abl A2_C2 A_B3 CI lo | 0.54401 | 0.54391 | 0.00010066 | 0.01 | match |
| abl A2_C2 A_B3 CI hi | 0.63178 | 0.63259 | 0.00080417 | 0.01 | match |
| abl A2_C2 D_B1 | 0.087294 | 0.087294 | 0 | 0.002 | match |
| abl A2_C2 D_B1 CI lo | 0.029048 | 0.029314 | 0.00026595 | 0.01 | match |
| abl A2_C2 D_B1 CI hi | 0.14571 | 0.14888 | 0.0031772 | 0.01 | match |
| abl A2_C2 p_B1 | 0.0013 | 0.0011 | 0.0002 | 0.0031826 | match |
| abl A2_C2 Holm-2 B1 | 0.0026 | 0.0022 | 0.0004 | 0.0087478 | match |
| abl A2_C2 D_B2 | 0.062918 | 0.062918 | 5.5511e-17 | 0.002 | match |
| abl A2_C2 D_B2 CI lo | 0.0063073 | 0.0057009 | 0.00060642 | 0.01 | match |
| abl A2_C2 D_B2 CI hi | 0.12158 | 0.12304 | 0.0014638 | 0.01 | match |
| abl A2_C2 p_B2 | 0.0149 | 0.0161 | 0.0012 | 0.010369 | match |
| abl A2_C2 Holm-2 B2 | 0.0149 | 0.0161 | 0.0012 | 0.020738 | match |
| abl A2_C2 clean (mean agg, fixed C) | 0.34444 | 0.34444 | 0 | 0.001 | match |
| abl A2_C6 A | 0.50771 | 0.50771 | 1.1102e-16 | 0.002 | match |
| abl A2_C6 A CI lo | 0.46027 | 0.45949 | 0.00077707 | 0.01 | match |
| abl A2_C6 A CI hi | 0.55603 | 0.55636 | 0.00032989 | 0.01 | match |
| abl A2_C6 A0 | 0.65 | 0.65 | 0 | 0.001 | match |
| abl A2_C6 A lighting_global | 0.5415 | 0.5415 | 0 | 0.002 | match |
| abl A2_C6 A lighting_local | 0.44352 | 0.44352 | 0 | 0.002 | match |
| abl A2_C6 A jolt_base | 0.53568 | 0.53568 | 0 | 0.002 | match |
| abl A2_C6 A zoom_base | 0.51014 | 0.51014 | 0 | 0.002 | match |
| abl A2_C6 A_B1 | 0.31927 | 0.31927 | 0 | 0.002 | match |
| abl A2_C6 A0_B1 | 0.55278 | 0.55278 | 0 | 0.001 | match |
| abl A2_C6 A_B1 CI lo | 0.27629 | 0.27704 | 0.00074968 | 0.01 | match |
| abl A2_C6 A_B1 CI hi | 0.36209 | 0.36261 | 0.00052459 | 0.01 | match |
| abl A2_C6 A_B2 | 0.36549 | 0.36549 | 0 | 0.002 | match |
| abl A2_C6 A0_B2 | 0.63889 | 0.63889 | 0 | 0.001 | match |
| abl A2_C6 A_B2 CI lo | 0.31746 | 0.31772 | 0.00025974 | 0.01 | match |
| abl A2_C6 A_B2 CI hi | 0.41436 | 0.41323 | 0.0011258 | 0.01 | match |
| abl A2_C6 A_B3 | 0.61047 | 0.61047 | 1.1102e-16 | 0.002 | match |
| abl A2_C6 A0_B3 | 0.69722 | 0.69722 | 0 | 0.001 | match |
| abl A2_C6 A_B3 CI lo | 0.56697 | 0.56714 | 0.00016705 | 0.01 | match |
| abl A2_C6 A_B3 CI hi | 0.65369 | 0.65491 | 0.0012136 | 0.01 | match |
| abl A2_C6 D_B1 | 0.18843 | 0.18843 | 1.1102e-16 | 0.002 | match |
| abl A2_C6 D_B1 CI lo | 0.13853 | 0.13914 | 0.00060876 | 0.01 | match |
| abl A2_C6 D_B1 CI hi | 0.2408 | 0.24097 | 0.00017351 | 0.01 | match |
| abl A2_C6 p_B1 | 9.999e-05 | 9.999e-05 | 0 | 0.0011 | match |
| abl A2_C6 Holm-2 B1 | 0.00019998 | 0.00019998 | 0 | 0.0028624 | match |
| abl A2_C6 D_B2 | 0.14222 | 0.14222 | 1.1102e-16 | 0.002 | match |
| abl A2_C6 D_B2 CI lo | 0.09298 | 0.092231 | 0.00074955 | 0.01 | match |
| abl A2_C6 D_B2 CI hi | 0.19309 | 0.19259 | 0.00050399 | 0.01 | match |
| abl A2_C6 p_B2 | 9.999e-05 | 9.999e-05 | 0 | 0.0011 | match |
| abl A2_C6 Holm-2 B2 | 0.00019998 | 0.00019998 | 0 | 0.0028624 | match |
| abl A2_C6 clean (mean agg, fixed C) | 0.79167 | 0.79167 | 0 | 0.001 | match |
| abl A2_C10 A | 0.52774 | 0.52774 | 0 | 0.002 | match |
| abl A2_C10 A CI lo | 0.47558 | 0.47514 | 0.00043409 | 0.01 | match |
| abl A2_C10 A CI hi | 0.58059 | 0.58126 | 0.00067361 | 0.01 | match |
| abl A2_C10 A0 | 0.64722 | 0.64722 | 0 | 0.001 | match |
| abl A2_C10 A lighting_global | 0.56008 | 0.56008 | 0 | 0.002 | match |
| abl A2_C10 A lighting_local | 0.46847 | 0.46847 | 0 | 0.002 | match |
| abl A2_C10 A jolt_base | 0.55156 | 0.55156 | 0 | 0.002 | match |
| abl A2_C10 A zoom_base | 0.53086 | 0.53086 | 0 | 0.002 | match |
| abl A2_C10 A_B1 | 0.29919 | 0.29919 | 0 | 0.002 | match |
| abl A2_C10 A0_B1 | 0.56111 | 0.56111 | 0 | 0.001 | match |
| abl A2_C10 A_B1 CI lo | 0.2554 | 0.25656 | 0.0011671 | 0.01 | match |
| abl A2_C10 A_B1 CI hi | 0.34338 | 0.3429 | 0.00047991 | 0.01 | match |
| abl A2_C10 A_B2 | 0.33686 | 0.33686 | 5.5511e-17 | 0.002 | match |
| abl A2_C10 A0_B2 | 0.60556 | 0.60556 | 0 | 0.001 | match |
| abl A2_C10 A_B2 CI lo | 0.28898 | 0.2892 | 0.00021624 | 0.01 | match |
| abl A2_C10 A_B2 CI hi | 0.38527 | 0.38559 | 0.00031768 | 0.01 | match |
| abl A2_C10 A_B3 | 0.50871 | 0.50871 | 0 | 0.002 | match |
| abl A2_C10 A0_B3 | 0.53611 | 0.53611 | 0 | 0.001 | match |
| abl A2_C10 A_B3 CI lo | 0.45768 | 0.45777 | 8.5262e-05 | 0.01 | match |
| abl A2_C10 A_B3 CI hi | 0.55869 | 0.55925 | 0.00056221 | 0.01 | match |
| abl A2_C10 D_B1 | 0.22855 | 0.22855 | 0 | 0.002 | match |
| abl A2_C10 D_B1 CI lo | 0.18143 | 0.18131 | 0.0001206 | 0.01 | match |
| abl A2_C10 D_B1 CI hi | 0.27507 | 0.27581 | 0.00074579 | 0.01 | match |
| abl A2_C10 p_B1 | 9.999e-05 | 9.999e-05 | 0 | 0.0011 | match |
| abl A2_C10 Holm-2 B1 | 0.00019998 | 0.00019998 | 0 | 0.0028624 | match |
| abl A2_C10 D_B2 | 0.19088 | 0.19088 | 5.5511e-17 | 0.002 | match |
| abl A2_C10 D_B2 CI lo | 0.13959 | 0.13753 | 0.0020633 | 0.01 | match |
| abl A2_C10 D_B2 CI hi | 0.24298 | 0.2432 | 0.00022843 | 0.01 | match |
| abl A2_C10 p_B2 | 9.999e-05 | 9.999e-05 | 0 | 0.0011 | match |
| abl A2_C10 Holm-2 B2 | 0.00019998 | 0.00019998 | 0 | 0.0028624 | match |
| abl A2_C10 clean (mean agg, fixed C) | 0.78889 | 0.78889 | 0 | 0.001 | match |
| T5 M1 A_B1 | 0.33521 | 0.33521 | 0 | 0.002 | match |
| T5 M1 A_B1 CI lo | 0.29226 | 0.29258 | 0.00031546 | 0.01 | match |
| T5 M1 A_B1 CI hi | 0.37859 | 0.37784 | 0.00075829 | 0.01 | match |
| T5 M1 A0_B1 | 0.55556 | 0.55556 | 0 | 0.001 | match |
| T5 M1 A_B1 lighting_global | 0.36179 | 0.36179 | 0 | 0.002 | match |
| T5 M1 A_B1 lighting_local | 0.2731 | 0.2731 | 0 | 0.002 | match |
| T5 M1 A_B1 jolt_base | 0.37193 | 0.37193 | 0 | 0.002 | match |
| T5 M1 A_B1 zoom_base | 0.33401 | 0.33401 | 0 | 0.002 | match |
| T5 M1 A_B2 | 0.37934 | 0.37934 | 5.5511e-17 | 0.002 | match |
| T5 M1 A_B2 CI lo | 0.33146 | 0.33192 | 0.00046486 | 0.01 | match |
| T5 M1 A_B2 CI hi | 0.42829 | 0.42909 | 0.00079135 | 0.01 | match |
| T5 M1 A0_B2 | 0.6 | 0.6 | 0 | 0.001 | match |
| T5 M1 A_B2 lighting_global | 0.39369 | 0.39369 | 0 | 0.002 | match |
| T5 M1 A_B2 lighting_local | 0.31608 | 0.31608 | 0 | 0.002 | match |
| T5 M1 A_B2 jolt_base | 0.4295 | 0.4295 | 0 | 0.002 | match |
| T5 M1 A_B2 zoom_base | 0.3781 | 0.3781 | 0 | 0.002 | match |
| T5 M1 A_B3 | 0.55201 | 0.55201 | 0 | 0.002 | match |
| T5 M1 A_B3 CI lo | 0.50842 | 0.50872 | 0.00030697 | 0.01 | match |
| T5 M1 A_B3 CI hi | 0.5948 | 0.59543 | 0.00062182 | 0.01 | match |
| T5 M1 A0_B3 | 0.61389 | 0.61389 | 0 | 0.001 | match |
| T5 M1 A_B3 lighting_global | 0.55988 | 0.55988 | 0 | 0.002 | match |
| T5 M1 A_B3 lighting_local | 0.73644 | 0.73644 | 0 | 0.002 | match |
| T5 M1 A_B3 jolt_base | 0.46617 | 0.46617 | 0 | 0.002 | match |
| T5 M1 A_B3 zoom_base | 0.44556 | 0.44556 | 0 | 0.002 | match |
| T5 M1 A0_M | 0.72222 | 0.72222 | 0 | 0.001 | match |
| T5 M2 A_B1 | 0.32413 | 0.32413 | 5.5511e-17 | 0.002 | match |
| T5 M2 A_B1 CI lo | 0.27995 | 0.28049 | 0.00053881 | 0.01 | match |
| T5 M2 A_B1 CI hi | 0.369 | 0.36808 | 0.00091882 | 0.01 | match |
| T5 M2 A0_B1 | 0.55556 | 0.55556 | 0 | 0.001 | match |
| T5 M2 A_B1 lighting_global | 0.35965 | 0.35965 | 0 | 0.002 | match |
| T5 M2 A_B1 lighting_local | 0.27201 | 0.27201 | 0 | 0.002 | match |
| T5 M2 A_B1 jolt_base | 0.3564 | 0.3564 | 0 | 0.002 | match |
| T5 M2 A_B1 zoom_base | 0.30846 | 0.30846 | 0 | 0.002 | match |
| T5 M2 A_B2 | 0.37615 | 0.37615 | 5.5511e-17 | 0.002 | match |
| T5 M2 A_B2 CI lo | 0.32829 | 0.32891 | 0.00062121 | 0.01 | match |
| T5 M2 A_B2 CI hi | 0.42521 | 0.42616 | 0.00094396 | 0.01 | match |
| T5 M2 A0_B2 | 0.6 | 0.6 | 0 | 0.001 | match |
| T5 M2 A_B2 lighting_global | 0.39315 | 0.39315 | 0 | 0.002 | match |
| T5 M2 A_B2 lighting_local | 0.31591 | 0.31591 | 0 | 0.002 | match |
| T5 M2 A_B2 jolt_base | 0.42635 | 0.42635 | 0 | 0.002 | match |
| T5 M2 A_B2 zoom_base | 0.3692 | 0.3692 | 0 | 0.002 | match |
| T5 M2 A_B3 | 0.37205 | 0.37205 | 5.5511e-17 | 0.002 | match |
| T5 M2 A_B3 CI lo | 0.32863 | 0.32754 | 0.0010986 | 0.01 | match |
| T5 M2 A_B3 CI hi | 0.41561 | 0.41481 | 0.00080324 | 0.01 | match |
| T5 M2 A0_B3 | 0.34444 | 0.34444 | 0 | 0.001 | match |
| T5 M2 A_B3 lighting_global | 0.3471 | 0.3471 | 0 | 0.002 | match |
| T5 M2 A_B3 lighting_local | 0.28293 | 0.28293 | 0 | 0.002 | match |
| T5 M2 A_B3 jolt_base | 0.44219 | 0.44219 | 0 | 0.002 | match |
| T5 M2 A_B3 zoom_base | 0.41597 | 0.41597 | 0 | 0.002 | match |
| T5 M2 A0_M | 0.6 | 0.6 | 0 | 0.001 | match |
| T6 M1_fp16_P4 O1 tiehalf | 0.75833 | 0.75833 | 0 | 0.001 | match |
| T6 M1_fp16_P4 O1 strict | 0.75 | 0.75 | 0 | 0.001 | match |
| T6 M1_fp16_P4 O2 tiehalf | 0.81667 | 0.81667 | 0 | 0.001 | match |
| T6 M1_fp16_P4 O2 strict | 0.83333 | 0.83333 | 0 | 0.001 | match |
| T6 M1_fp16_P4 O3 tiehalf | 0.85 | 0.85 | 0 | 0.001 | match |
| T6 M1_fp16_P4 O3 strict | 0.85 | 0.85 | 0 | 0.001 | match |
| T6 B1_P4 O1 tiehalf | 0.58333 | 0.58333 | 0 | 0.001 | match |
| T6 B1_P4 O1 strict | 0.58333 | 0.58333 | 0 | 0.001 | match |
| T6 B1_P4 O2 tiehalf | 0.58333 | 0.58333 | 0 | 0.001 | match |
| T6 B1_P4 O2 strict | 0.58333 | 0.58333 | 0 | 0.001 | match |
| T6 B1_P4 O3 tiehalf | 0.575 | 0.575 | 0 | 0.001 | match |
| T6 B1_P4 O3 strict | 0.55 | 0.55 | 0 | 0.001 | match |
| T6 B2_P4 O1 tiehalf | 0.68333 | 0.68333 | 0 | 0.001 | match |
| T6 B2_P4 O1 strict | 0.68333 | 0.68333 | 0 | 0.001 | match |
| T6 B2_P4 O2 tiehalf | 0.78333 | 0.78333 | 0 | 0.001 | match |
| T6 B2_P4 O2 strict | 0.78333 | 0.78333 | 0 | 0.001 | match |
| T6 B2_P4 O3 tiehalf | 0.81667 | 0.81667 | 0 | 0.001 | match |
| T6 B2_P4 O3 strict | 0.81667 | 0.81667 | 0 | 0.001 | match |
| T6 B3_P4 O1 tiehalf | 0.50833 | 0.50833 | 0 | 0.001 | match |
| T6 B3_P4 O1 strict | 0.5 | 0.5 | 0 | 0.001 | match |
| T6 B3_P4 O2 tiehalf | 0.41667 | 0.41667 | 0 | 0.001 | match |
| T6 B3_P4 O2 strict | 0.41667 | 0.41667 | 0 | 0.001 | match |
| T6 B3_P4 O3 tiehalf | 0.43333 | 0.43333 | 0 | 0.001 | match |
| T6 B3_P4 O3 strict | 0.43333 | 0.43333 | 0 | 0.001 | match |
| T6 M2_P4 O1 tiehalf | 0.61667 | 0.61667 | 0 | 0.001 | match |
| T6 M2_P4 O1 strict | 0.6 | 0.6 | 0 | 0.001 | match |
| T6 M2_P4 O2 tiehalf | 0.54167 | 0.54167 | 0 | 0.001 | match |
| T6 M2_P4 O2 strict | 0.55 | 0.55 | 0 | 0.001 | match |
| T6 M2_P4 O3 tiehalf | 0.66667 | 0.66667 | 0 | 0.001 | match |
| T6 M2_P4 O3 strict | 0.66667 | 0.66667 | 0 | 0.001 | match |
| T6 M1_fp32_P2 all tiehalf | 0.81667 | 0.81667 | 0 | 0.001 | match |
| T6 M1_fp32_P2 all strict | 0.80556 | 0.80556 | 0 | 0.001 | match |
| T6 B1_P2 all tiehalf | 0.58056 | 0.58056 | 0 | 0.001 | match |
| T6 B1_P2 all strict | 0.57222 | 0.57222 | 0 | 0.001 | match |
| T6 B2_P2 all tiehalf | 0.76111 | 0.76111 | 0 | 0.001 | match |
| T6 B2_P2 all strict | 0.76111 | 0.76111 | 0 | 0.001 | match |
| T6 M1_fp32_P2 visible tiehalf | 0.86667 | 0.86667 | 0 | 0.001 | match |
| T6 M1_fp32_P2 visible strict | 0.85556 | 0.85556 | 0 | 0.001 | match |
| T6 B1_P2 visible tiehalf | 0.56667 | 0.56667 | 0 | 0.001 | match |
| T6 B1_P2 visible strict | 0.55556 | 0.55556 | 0 | 0.001 | match |
| T6 B2_P2 visible tiehalf | 0.76667 | 0.76667 | 0 | 0.001 | match |
| T6 B2_P2 visible strict | 0.76667 | 0.76667 | 0 | 0.001 | match |
| T6 M1_fp32_P2 occluded tiehalf | 0.76667 | 0.76667 | 0 | 0.001 | match |
| T6 M1_fp32_P2 occluded strict | 0.75556 | 0.75556 | 0 | 0.001 | match |
| T6 B1_P2 occluded tiehalf | 0.59444 | 0.59444 | 0 | 0.001 | match |
| T6 B1_P2 occluded strict | 0.58889 | 0.58889 | 0 | 0.001 | match |
| T6 B2_P2 occluded tiehalf | 0.75556 | 0.75556 | 0 | 0.001 | match |
| T6 B2_P2 occluded strict | 0.75556 | 0.75556 | 0 | 0.001 | match |
| T6 M1_fp32_P2 static tiehalf | 0.76667 | 0.76667 | 0 | 0.001 | match |
| T6 M1_fp32_P2 static strict | 0.76667 | 0.76667 | 0 | 0.001 | match |
| T6 B1_P2 static tiehalf | 0.58333 | 0.58333 | 0 | 0.001 | match |
| T6 B1_P2 static strict | 0.58333 | 0.58333 | 0 | 0.001 | match |
| T6 B2_P2 static tiehalf | 0.76667 | 0.76667 | 0 | 0.001 | match |
| T6 B2_P2 static strict | 0.76667 | 0.76667 | 0 | 0.001 | match |
| T6 M1_fp32_P2 dynamic_1 tiehalf | 0.875 | 0.875 | 0 | 0.001 | match |
| T6 M1_fp32_P2 dynamic_1 strict | 0.86667 | 0.86667 | 0 | 0.001 | match |
| T6 B1_P2 dynamic_1 tiehalf | 0.58333 | 0.58333 | 0 | 0.001 | match |
| T6 B1_P2 dynamic_1 strict | 0.56667 | 0.56667 | 0 | 0.001 | match |
| T6 B2_P2 dynamic_1 tiehalf | 0.78333 | 0.78333 | 0 | 0.001 | match |
| T6 B2_P2 dynamic_1 strict | 0.78333 | 0.78333 | 0 | 0.001 | match |
| T6 M1_fp32_P2 dynamic_2 tiehalf | 0.80833 | 0.80833 | 0 | 0.001 | match |
| T6 M1_fp32_P2 dynamic_2 strict | 0.78333 | 0.78333 | 0 | 0.001 | match |
| T6 B1_P2 dynamic_2 tiehalf | 0.575 | 0.575 | 0 | 0.001 | match |
| T6 B1_P2 dynamic_2 strict | 0.56667 | 0.56667 | 0 | 0.001 | match |
| T6 B2_P2 dynamic_2 tiehalf | 0.73333 | 0.73333 | 0 | 0.001 | match |
| T6 B2_P2 dynamic_2 strict | 0.73333 | 0.73333 | 0 | 0.001 | match |
| T6 M1_fp32_P2 O1 tiehalf | 0.75833 | 0.75833 | 0 | 0.001 | match |
| T6 M1_fp32_P2 O1 strict | 0.73333 | 0.73333 | 0 | 0.001 | match |
| T6 B1_P2 O1 tiehalf | 0.58333 | 0.58333 | 0 | 0.001 | match |
| T6 B1_P2 O1 strict | 0.58333 | 0.58333 | 0 | 0.001 | match |
| T6 B2_P2 O1 tiehalf | 0.68333 | 0.68333 | 0 | 0.001 | match |
| T6 B2_P2 O1 strict | 0.68333 | 0.68333 | 0 | 0.001 | match |
| T6 M1_fp32_P2 O2 tiehalf | 0.83333 | 0.83333 | 0 | 0.001 | match |
| T6 M1_fp32_P2 O2 strict | 0.83333 | 0.83333 | 0 | 0.001 | match |
| T6 B1_P2 O2 tiehalf | 0.58333 | 0.58333 | 0 | 0.001 | match |
| T6 B1_P2 O2 strict | 0.58333 | 0.58333 | 0 | 0.001 | match |
| T6 B2_P2 O2 tiehalf | 0.78333 | 0.78333 | 0 | 0.001 | match |
| T6 B2_P2 O2 strict | 0.78333 | 0.78333 | 0 | 0.001 | match |
| T6 M1_fp32_P2 O3 tiehalf | 0.85833 | 0.85833 | 0 | 0.001 | match |
| T6 M1_fp32_P2 O3 strict | 0.85 | 0.85 | 0 | 0.001 | match |
| T6 B1_P2 O3 tiehalf | 0.575 | 0.575 | 0 | 0.001 | match |
| T6 B1_P2 O3 strict | 0.55 | 0.55 | 0 | 0.001 | match |
| T6 B2_P2 O3 tiehalf | 0.81667 | 0.81667 | 0 | 0.001 | match |
| T6 B2_P2 O3 strict | 0.81667 | 0.81667 | 0 | 0.001 | match |
| T6 M1_fp32_P2 O1_visible tiehalf | 0.81667 | 0.81667 | 0 | 0.001 | match |
| T6 M1_fp32_P2 O1_visible strict | 0.8 | 0.8 | 0 | 0.001 | match |
| T6 B1_P2 O1_visible tiehalf | 0.56667 | 0.56667 | 0 | 0.001 | match |
| T6 B1_P2 O1_visible strict | 0.56667 | 0.56667 | 0 | 0.001 | match |
| T6 B2_P2 O1_visible tiehalf | 0.7 | 0.7 | 0 | 0.001 | match |
| T6 B2_P2 O1_visible strict | 0.7 | 0.7 | 0 | 0.001 | match |
| T6 M1_fp32_P2 O1_occluded tiehalf | 0.7 | 0.7 | 0 | 0.001 | match |
| T6 M1_fp32_P2 O1_occluded strict | 0.66667 | 0.66667 | 0 | 0.001 | match |
| T6 B1_P2 O1_occluded tiehalf | 0.6 | 0.6 | 0 | 0.001 | match |
| T6 B1_P2 O1_occluded strict | 0.6 | 0.6 | 0 | 0.001 | match |
| T6 B2_P2 O1_occluded tiehalf | 0.66667 | 0.66667 | 0 | 0.001 | match |
| T6 B2_P2 O1_occluded strict | 0.66667 | 0.66667 | 0 | 0.001 | match |
| T6 M1_fp32_P2 O2_visible tiehalf | 0.85 | 0.85 | 0 | 0.001 | match |
| T6 M1_fp32_P2 O2_visible strict | 0.83333 | 0.83333 | 0 | 0.001 | match |
| T6 B1_P2 O2_visible tiehalf | 0.6 | 0.6 | 0 | 0.001 | match |
| T6 B1_P2 O2_visible strict | 0.6 | 0.6 | 0 | 0.001 | match |
| T6 B2_P2 O2_visible tiehalf | 0.76667 | 0.76667 | 0 | 0.001 | match |
| T6 B2_P2 O2_visible strict | 0.76667 | 0.76667 | 0 | 0.001 | match |
| T6 M1_fp32_P2 O2_occluded tiehalf | 0.81667 | 0.81667 | 0 | 0.001 | match |
| T6 M1_fp32_P2 O2_occluded strict | 0.83333 | 0.83333 | 0 | 0.001 | match |
| T6 B1_P2 O2_occluded tiehalf | 0.56667 | 0.56667 | 0 | 0.001 | match |
| T6 B1_P2 O2_occluded strict | 0.56667 | 0.56667 | 0 | 0.001 | match |
| T6 B2_P2 O2_occluded tiehalf | 0.8 | 0.8 | 0 | 0.001 | match |
| T6 B2_P2 O2_occluded strict | 0.8 | 0.8 | 0 | 0.001 | match |
| T6 M1_fp32_P2 O3_visible tiehalf | 0.93333 | 0.93333 | 0 | 0.001 | match |
| T6 M1_fp32_P2 O3_visible strict | 0.93333 | 0.93333 | 0 | 0.001 | match |
| T6 B1_P2 O3_visible tiehalf | 0.53333 | 0.53333 | 0 | 0.001 | match |
| T6 B1_P2 O3_visible strict | 0.5 | 0.5 | 0 | 0.001 | match |
| T6 B2_P2 O3_visible tiehalf | 0.83333 | 0.83333 | 0 | 0.001 | match |
| T6 B2_P2 O3_visible strict | 0.83333 | 0.83333 | 0 | 0.001 | match |
| T6 M1_fp32_P2 O3_occluded tiehalf | 0.78333 | 0.78333 | 0 | 0.001 | match |
| T6 M1_fp32_P2 O3_occluded strict | 0.76667 | 0.76667 | 0 | 0.001 | match |
| T6 B1_P2 O3_occluded tiehalf | 0.61667 | 0.61667 | 0 | 0.001 | match |
| T6 B1_P2 O3_occluded strict | 0.6 | 0.6 | 0 | 0.001 | match |
| T6 B2_P2 O3_occluded tiehalf | 0.8 | 0.8 | 0 | 0.001 | match |
| T6 B2_P2 O3_occluded strict | 0.8 | 0.8 | 0 | 0.001 | match |
| M0r P2 init0 tiehalf | 0.5 | 0.5 | 0 | 0.001 | match |
| M0r P2 init1 tiehalf | 0.5 | 0.5 | 0 | 0.001 | match |
| M0r P2 init2 tiehalf | 0.5 | 0.5 | 0 | 0.001 | match |
| M0r P2 strict mean over inits | 0.49815 | 0.5 | 0.0018519 | 0.001 | MISMATCH |
| M0r P2 tie rate mean over inits | 0.9963 | 0.98148 | 0.014815 | 0.001 | MISMATCH |
| M0r reversal detection | 0.51667 |  |  | 0.001 | UNMAPPED |
| F3 M1 brightness-low flip | 0.07037 | 0.07037 | 0 | 0.001 | match |
| F3 M1 brightness-low flip CI lo | 0.040741 | 0.040741 | 0 | 0.01 | match |
| F3 M1 brightness-low flip CI hi | 0.1037 | 0.10556 | 0.0018519 | 0.01 | match |
| F3 M1 brightness-mid flip | 0.096296 | 0.096296 | 0 | 0.001 | match |
| F3 M1 brightness-mid flip CI lo | 0.064815 | 0.064815 | 1.3878e-17 | 0.01 | match |
| F3 M1 brightness-mid flip CI hi | 0.12963 | 0.12963 | 2.7756e-17 | 0.01 | match |
| F3 M1 brightness-high flip | 0.12407 | 0.12407 | 0 | 0.001 | match |
| F3 M1 brightness-high flip CI lo | 0.088889 | 0.088889 | 0 | 0.01 | match |
| F3 M1 brightness-high flip CI hi | 0.16111 | 0.16111 | 0 | 0.01 | match |
| F3 M1 noise-low flip | 0.33148 | 0.33148 | 0 | 0.001 | match |
| F3 M1 noise-low flip CI lo | 0.26296 | 0.26477 | 0.0018056 | 0.01 | match |
| F3 M1 noise-low flip CI hi | 0.4 | 0.40185 | 0.0018519 | 0.01 | match |
| F3 M1 noise-mid flip | 0.35 | 0.35 | 0 | 0.001 | match |
| F3 M1 noise-mid flip CI lo | 0.28148 | 0.28148 | 0 | 0.01 | match |
| F3 M1 noise-mid flip CI hi | 0.41852 | 0.42222 | 0.0037037 | 0.01 | match |
| F3 M1 noise-high flip | 0.37778 | 0.37778 | 0 | 0.001 | match |
| F3 M1 noise-high flip CI lo | 0.30556 | 0.30556 | 5.5511e-17 | 0.01 | match |
| F3 M1 noise-high flip CI hi | 0.45 | 0.45 | 0 | 0.01 | match |
| F3 M1 blur-low flip | 0.18333 | 0.18333 | 0 | 0.001 | match |
| F3 M1 blur-low flip CI lo | 0.12778 | 0.12778 | 0 | 0.01 | match |
| F3 M1 blur-low flip CI hi | 0.23889 | 0.24444 | 0.0055556 | 0.01 | match |
| F3 M1 blur-mid flip | 0.25556 | 0.25556 | 0 | 0.001 | match |
| F3 M1 blur-mid flip CI lo | 0.18889 | 0.18889 | 0 | 0.01 | match |
| F3 M1 blur-mid flip CI hi | 0.32222 | 0.32222 | 0 | 0.01 | match |
| F3 M1 blur-high flip | 0.31111 | 0.31111 | 0 | 0.001 | match |
| F3 M1 blur-high flip CI lo | 0.24444 | 0.24444 | 0 | 0.01 | match |
| F3 M1 blur-high flip CI hi | 0.37778 | 0.37778 | 0 | 0.01 | match |
| F3 M1 jpeg-low flip | 0.14444 | 0.14444 | 0 | 0.001 | match |
| F3 M1 jpeg-low flip CI lo | 0.094444 | 0.094444 | 0 | 0.01 | match |
| F3 M1 jpeg-low flip CI hi | 0.2 | 0.2 | 0 | 0.01 | match |
| F3 M1 jpeg-mid flip | 0.17222 | 0.17222 | 0 | 0.001 | match |
| F3 M1 jpeg-mid flip CI lo | 0.11667 | 0.11667 | 0 | 0.01 | match |
| F3 M1 jpeg-mid flip CI hi | 0.23333 | 0.23333 | 0 | 0.01 | match |
| F3 M1 jpeg-high flip | 0.28333 | 0.28333 | 0 | 0.001 | match |
| F3 M1 jpeg-high flip CI lo | 0.21667 | 0.21667 | 0 | 0.01 | match |
| F3 M1 jpeg-high flip CI hi | 0.35556 | 0.35556 | 0 | 0.01 | match |
| F3 M1 zoom-low flip | 0.14925 | 0.14925 | 0 | 0.001 | match |
| F3 M1 zoom-low flip CI lo | 0.087838 | 0.086667 | 0.0011712 | 0.01 | match |
| F3 M1 zoom-low flip CI hi | 0.21918 | 0.21831 | 0.00087123 | 0.01 | match |
| F3 M1 zoom-mid flip | 0.15 | 0.15 | 0 | 0.001 | match |
| F3 M1 zoom-mid flip CI lo | 0.095238 | 0.094828 | 0.00041051 | 0.01 | match |
| F3 M1 zoom-mid flip CI hi | 0.20833 | 0.20909 | 0.00075758 | 0.01 | match |
| F3 M1 zoom-high flip | 0.14286 | 0.14286 | 0 | 0.001 | match |
| F3 M1 zoom-high flip CI lo | 0.081633 | 0.078934 | 0.0026982 | 0.01 | match |
| F3 M1 zoom-high flip CI hi | 0.21314 | 0.21296 | 0.00018107 | 0.01 | match |
