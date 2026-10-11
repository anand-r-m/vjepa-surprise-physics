# P7 independent recompute (verifier)

Written BEFORE any analysis output (results/analysis/*, notes/*_RESULTS.md, src/vjepa_study/analysis, scripts/run_*) was opened. Code: verify/p7_lib.py, verify/p7_recompute.py (+ p6 pixel/event/retention caches for the zoom keep set only via kaggle/h2_spec_a/matches.json). Inputs: results/raw/<group>/results/<run>/surprise.npz, meta.json; kaggle/h2_spec_a/matches.json, kaggle/expl_onset_spec/matches.json; IntPhys 2 metadata.csv. Bootstrap: numpy default_rng seed 20261015, 10,000 draws, 30 scenes per block with replacement (IntPhys 2 Main: 253 scenes stratified by condition), common draws within a table.

Conventions (as p6): tau_m = 2e-4 x median of 360 per-video scores (mean aggregation for clean/H1; full-clip max of clean for H2/H3); tie-half primary; strict = d>0; flip = change among {+,0,-} at tau; H2 = event-aligned max with window w kept iff 4w+30 >= t_on (stored matches t_on, reading R1b); AUROC mean of 4 per-type AUROCs, per seed then averaged; Holm-2 on one-sided paired-bootstrap p; zoom keep set = stored support_retention_crop >= 0.9 (112 pairs).

## 1. Clean accuracy (180 pairs, mean aggregation)

| run | tau | tie-half | strict | ties | tie-half @ fixed 1e-4 |
|---|---|---|---|---|---|
| M1_fp16_P4 | 1.0570e-04 | 0.8083 | 0.8111 | 7 | 0.8083 |
| M1_fp32_P2 | 1.0571e-04 | 0.8167 | 0.8056 | 8 | 0.8167 |
| M1H_fp16_P2H | 1.1955e-04 | 0.8833 | 0.8778 | 4 | 0.8806 |
| M2_mi0 | 1.1086e-04 | 0.6083 | 0.6056 | 17 | 0.6111 |
| M2_mi1_old | 1.1583e-04 | 0.4694 | 0.4667 | 19 | 0.4722 |
| M1_skip4 | 1.0826e-04 | 0.8222 | 0.8222 | 10 | 0.8194 |
| M2_skip4 | 1.1273e-04 | 0.5333 | 0.5278 | 8 | 0.5361 |
| B1_P2_fp32 | 7.2286e-07 | 0.5806 | 0.5722 | 7 | 0.5000 |
| B2_P2_fp32 | 1.3560e-06 | 0.7611 | 0.7611 | 0 | 0.6250 |
| B3_P2_fp32 | 4.2555e-05 | 0.4333 | 0.4111 | 10 | 0.4417 |
| B1_P4_fp16_M1 | 7.2286e-07 | 0.5806 | 0.5722 | 7 | 0.5000 |
| B2_P4_fp16_M1 | 1.3560e-06 | 0.7611 | 0.7611 | 0 | 0.6250 |
| B3_P4_fp16_M1 | 4.2533e-05 | 0.4528 | 0.4500 | 9 | 0.4500 |
| B1_P4_fp16_M2 | 7.1953e-07 | 0.5778 | 0.5833 | 10 | 0.5000 |
| B2_P4_fp16_M2 | 1.3571e-06 | 0.7611 | 0.7611 | 2 | 0.6278 |
| B3_P4_fp16_M2 | 3.5747e-05 | 0.1722 | 0.1722 | 0 | 0.1722 |

Per block (tie-half / strict):

| run | O1 | O2 | O3 |
|---|---|---|---|
| M1_fp32_P2 | 0.758 / 0.733 | 0.833 / 0.833 | 0.858 / 0.850 |
| M1_fp16_P4 | 0.758 / 0.750 | 0.817 / 0.833 | 0.850 / 0.850 |
| B1_P2 | 0.583 / 0.583 | 0.583 / 0.583 | 0.575 / 0.550 |
| B2_P2 | 0.683 / 0.683 | 0.783 / 0.783 | 0.817 / 0.817 |

Paired M1 - B2 clean (tie-half; scene-cluster bootstrap):

| M1 run | M1 acc | B2 acc | diff | 95% CI | p (2-sided) | diff strict | CI strict |
|---|---|---|---|---|---|---|---|
| fp32_P2 | 0.8167 | 0.7611 | 0.0556 | [0.0000, 0.1111] | 0.0534 | 0.0444 | [-0.0111, 0.1000] |
| fp16_P4 | 0.8083 | 0.7611 | 0.0472 | [-0.0111, 0.1056] | 0.1240 | 0.0500 | [-0.0056, 0.1056] |

**Finding E1.** ViT-H fp16 tie-half under the prereg tau (scale-relative 1.195e-4) is 0.8833, strict 0.8778; the quoted 88.1% reproduces only with the superseded fixed tau = 1e-4 (0.8806). fp32 P2 ViT-L: tie-half 0.8167 / strict 0.8056 (same under both taus).

## 2. Precision (P2 fp32 vs P4 fp16, same 360 inputs, M1)

```
{
 "own_tau": {
  "class_change_frac": 0.027777777777777776,
  "n_class_change": 5,
  "credit_change_frac": 0.027777777777777776,
  "n_credit_change": 5,
  "tau16": 0.0001057012373910231,
  "tau32": 0.00010570561289787293,
  "correct_flag_change_frac": 0.005555555555555556
 },
 "common_tau_fp16": {
  "class_change_frac": 0.027777777777777776,
  "n_class_change": 5,
  "credit_change_frac": 0.027777777777777776,
  "n_credit_change": 5,
  "tau16": 0.0001057012373910231,
  "tau32": 0.0001057012373910231,
  "correct_flag_change_frac": 0.005555555555555556
 },
 "common_tau_fp32": {
  "class_change_frac": 0.027777777777777776,
  "n_class_change": 5,
  "credit_change_frac": 0.027777777777777776,
  "n_credit_change": 5,
  "tau16": 0.00010570561289787293,
  "tau32": 0.00010570561289787293,
  "correct_flag_change_frac": 0.005555555555555556
 },
 "strict_tau0": {
  "sign_change_frac": 0.005555555555555556,
  "n": 1
 },
 "max_abs_window_score_diff": 0.001997530460357666,
 "max_abs_window_margin_diff": 0.0016880631446838379,
 "max_abs_S_wc_diff": 0.0026541948318481445,
 "median_abs_window_margin_diff": 5.3763389587402344e-05,
 "p99_abs_window_margin_diff": 0.0007592844963073718,
 "max_abs_pair_mean_margin_diff": 0.0005507188684800157,
 "tau_M1_fp16": 0.0001057012373910231
}
```

## 3. H1 high strength (M1 and M2)

### M1 (tau_mean 1.0570e-04; dither f0 over all pairs 0.2148, strict-convention f0 0.1556; fps_halve identical to skip-4 clean: True)

| edit | n | dAcc | CI | p cluster | Holm-14 | p sign | Holm-14 sign fam | flip | f0 | flip-f0 | p flip | Holm-14 | strict flip | strict f0 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| brightness | 180 | -0.0241 | [-0.051, 0.003] | 0.0786 | 0.6288 | 0.0660 | 0.5280 | 0.1241 | 0.2148 | -0.0907 | 0.9999 | 1.0000 | 0.0944 | 0.1556 |
| noise | 180 | -0.2056 | [-0.257, -0.153] | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.3778 | 0.2148 | 0.1630 | 0.0000 | 0.0000 | 0.2611 | 0.1556 |
| blur | 180 | -0.1444 | [-0.194, -0.094] | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.3111 | 0.2148 | 0.0963 | 0.0001 | 0.0010 | 0.2333 | 0.1556 |
| jpeg | 180 | -0.1083 | [-0.164, -0.053] | 0.0000 | 0.0000 | 0.0018 | 0.0177 | 0.2833 | 0.2148 | 0.0685 | 0.0171 | 0.1539 | 0.2278 | 0.1556 |
| zoom | 112 | -0.0045 | [-0.056, 0.049] | 0.9248 | 1.0000 | 1.0000 | 1.0000 | 0.1429 | 0.2321 | -0.0893 | 0.9921 | 1.0000 | 0.1161 | 0.1548 |
| hflip | 180 | 0.0222 | [-0.022, 0.067] | 0.3446 | 1.0000 | 0.4421 | 1.0000 | 0.1500 | 0.2148 | -0.0648 | 0.9782 | 1.0000 | 0.1056 | 0.1556 |
| fps_halve | 180 | 0.0000 | [0.000, 0.000] | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.2148 | -0.2148 | 1.0000 | 1.0000 | 0.0000 | 0.1556 |

### M2 (tau_mean 1.1086e-04; dither f0 over all pairs 0.2463, strict-convention f0 0.1741; fps_halve identical to skip-4 clean: True)

| edit | n | dAcc | CI | p cluster | Holm-14 | p sign | Holm-14 sign fam | flip | f0 | flip-f0 | p flip | Holm-14 | strict flip | strict f0 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| brightness | 180 | -0.0037 | [-0.031, 0.025] | 0.7596 | 1.0000 | 0.2221 | 1.0000 | 0.1537 | 0.2463 | -0.0926 | 1.0000 | 1.0000 | 0.1000 | 0.1741 |
| noise | 180 | -0.0639 | [-0.115, -0.013] | 0.0132 | 0.1320 | 0.1299 | 1.0000 | 0.2833 | 0.2463 | 0.0370 | 0.0335 | 0.3015 | 0.2167 | 0.1741 |
| blur | 180 | 0.1278 | [0.064, 0.192] | 0.0000 | 0.0000 | 0.0018 | 0.0211 | 0.4222 | 0.2463 | 0.1759 | 0.0000 | 0.0000 | 0.3111 | 0.1741 |
| jpeg | 180 | -0.0167 | [-0.078, 0.044] | 0.6118 | 1.0000 | 0.6400 | 1.0000 | 0.4056 | 0.2463 | 0.1593 | 0.0000 | 0.0000 | 0.3500 | 0.1741 |
| zoom | 112 | 0.0714 | [0.017, 0.128] | 0.0114 | 0.1254 | 0.0872 | 0.8716 | 0.2500 | 0.3065 | -0.0565 | 0.9031 | 1.0000 | 0.1964 | 0.2054 |
| hflip | 180 | 0.0333 | [-0.003, 0.069] | 0.0726 | 0.5808 | 0.3449 | 1.0000 | 0.1556 | 0.2463 | -0.0907 | 1.0000 | 1.0000 | 0.1222 | 0.1741 |
| fps_halve | 180 | 0.0000 | [0.000, 0.000] | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.2463 | -0.2463 | 1.0000 | 1.0000 | 0.0000 | 0.1741 |

## 4. H2 mid strength, stored-matches t_on (M1, M2)

### M1: outcome Detection-limited (Not specific); A0 0.7222 [0.6638, 0.7806] (B1 0.5556, B2 0.6000); tau M 1.0875e-04, B1 1.4669e-06, B2 2.9196e-06; seeds {'lighting_global': 3, 'lighting_local': 3, 'jolt_base': 3, 'zoom_base': 1}; late-excluded 0

| set | A_M | A_B1 | A_B2 | A_M CI | D_1 [CI] | p1 | Holm-2 | D_2 [CI] | p2 | Holm-2 |
|---|---|---|---|---|---|---|---|---|---|---|
| all | 0.5457 | 0.3352 | 0.3793 | [0.5010, 0.5905] | 0.2105 [0.159, 0.263] | 0.00010 | 0.00020 | 0.1664 [0.116, 0.219] | 0.00010 | 0.00020 |
| no_lighting_global | 0.5204 | 0.3263 | 0.3746 | [0.4748, 0.5653] | 0.1941 [0.142, 0.248] | 0.00010 | 0.00020 | 0.1459 [0.096, 0.198] | 0.00010 | 0.00020 |

Per-type AUROC (M / B1 / B2): lighting_global 0.622 / 0.362 / 0.394; lighting_local 0.480 / 0.273 / 0.316; jolt_base 0.553 / 0.372 / 0.430; zoom_base 0.528 / 0.334 / 0.378

### M2: outcome Detection-limited (Not specific (Reversed)); A0 0.6000 [0.5417, 0.6583] (B1 0.5556, B2 0.6000); tau M 1.1566e-04, B1 1.4644e-06, B2 2.9205e-06; seeds {'lighting_global': 3, 'lighting_local': 3, 'jolt_base': 3, 'zoom_base': 1}; late-excluded 0

| set | A_M | A_B1 | A_B2 | A_M CI | D_1 [CI] | p1 | Holm-2 | D_2 [CI] | p2 | Holm-2 |
|---|---|---|---|---|---|---|---|---|---|---|
| all | 0.4489 | 0.3241 | 0.3762 | [0.4029, 0.4964] | 0.1247 [0.077, 0.173] | 0.00010 | 0.00020 | 0.0727 [0.020, 0.124] | 0.00290 | 0.00290 |
| no_lighting_global | 0.4148 | 0.3123 | 0.3705 | [0.3685, 0.4615] | 0.1026 [0.053, 0.152] | 0.00010 | 0.00020 | 0.0444 [-0.010, 0.096] | 0.05060 | 0.05060 |

Per-type AUROC (M / B1 / B2): lighting_global 0.551 / 0.360 / 0.393; lighting_local 0.357 / 0.272 / 0.316; jolt_base 0.446 / 0.356 / 0.426; zoom_base 0.442 / 0.308 / 0.369

### H2 event / matching facts (stored matches.json)
```
{
 "n_fallback_stored": 178,
 "n_transient_stored": 2,
 "n_late_stored": 0,
 "meta_n_fallback": 178,
 "meta_n_pairs": 180,
 "m_i_median_gray": 0.3253200926701538,
 "m_i_iqr_gray": [
  0.11504823749419302,
  0.5030155240092427
 ],
 "m_i_min_gray": 0.0,
 "m_i_max_gray": 2.2496783081442118,
 "t_on_median": 48.0,
 "t_on_fallback_values": [
  48
 ],
 "mid_ratio": {
  "lighting_global": {
   "n": 540,
   "median": 0.906362659502172,
   "n_nan": 12,
   "frac_in_0p9_1p1": 0.5,
   "q25": 0.0,
   "q75": 0.9968092278869315
  },
  "lighting_local": {
   "n": 540,
   "median": 0.9999712331849349,
   "n_nan": 12,
   "frac_in_0p9_1p1": 0.9666666666666667,
   "q25": 0.9996843158472841,
   "q75": 1.000097955645621
  },
  "jolt_base": {
   "n": 540,
   "median": 1.0,
   "n_nan": 12,
   "frac_in_0p9_1p1": 0.9777777777777777,
   "q25": 0.9999790758711674,
   "q75": 1.000021824125641
  },
  "zoom_base": {
   "n": 180,
   "median": 1.0000002032536928,
   "n_nan": 4,
   "frac_in_0p9_1p1": 0.9777777777777777,
   "q25": 0.9999603171993863,
   "q75": 1.00003639783612
  }
 },
 "lg_mid_in_band_by_seed": {
  "1": 0.5,
  "2": 0.5,
  "3": 0.5
 },
 "m_i_pixel_recompute_median_gray": 0.32532007297469623,
 "m_i_pixel_vs_stored_max_abs_diff": 4.0745362639427185e-10
}
```

Global-lighting no-op counts (mid; per seed; 180 entries each): ```{"s1": {"n_entries": 180, "n_bitwise_identical_to_clean": 66, "n_mean_score_within_tau": 73, "n_evmax_within_tau2": 84}, "s2": {"n_entries": 180, "n_bitwise_identical_to_clean": 66, "n_mean_score_within_tau": 73, "n_evmax_within_tau2": 84}, "s3": {"n_entries": 180, "n_bitwise_identical_to_clean": 66, "n_mean_score_within_tau": 73, "n_evmax_within_tau2": 84}, "local_s1_bitwise_identical": 4}```

## 5. H3 positive controls (full-clip max; tau from clean full-clip max; M0r tau its own)

### M1 (tau 1.0875e-04; G2 pass: False)

| quantity | value | 95% CI |
|---|---|---|
| vflip_a_ref_p | 0.2111 | [0.1472, 0.2806] |
| hflip_ref_p | 0.3861 | [0.3111, 0.4639] |
| vflip_b_ref_hflip | 0.2583 | [0.1861, 0.3333] |
| reversal_ref_p | 0.6083 | [0.5167, 0.6944] |
| M0r_vflip | 0.8778 | [0.8222, 0.9306] |
| M0r_reversal | 0.5167 | [0.5000, 0.5389] |
| model_minus_M0r_vflip | -0.6667 | [-0.7611, -0.5667] |
| model_minus_M0r_reversal | 0.0917 | [-0.0028, 0.1833] |
| pairwise_acc_vflip (tie-half / strict) | 0.8389 / 0.8222 | |
| pairwise_acc_reversal (tie-half / strict) | 0.7472 / 0.7333 | |
| pairwise_acc_hflip (tie-half / strict) | 0.8306 / 0.8389 | |

### M2 (tau 1.1566e-04; G2 pass: False)

| quantity | value | 95% CI |
|---|---|---|
| vflip_a_ref_p | 0.7194 | [0.6444, 0.7889] |
| hflip_ref_p | 0.5111 | [0.4305, 0.5917] |
| vflip_b_ref_hflip | 0.7278 | [0.6528, 0.8000] |
| reversal_ref_p | 0.4639 | [0.3861, 0.5417] |
| M0r_vflip | 0.8778 | [0.8222, 0.9306] |
| M0r_reversal | 0.5167 | [0.5000, 0.5389] |
| model_minus_M0r_vflip | -0.1583 | [-0.2501, -0.0667] |
| model_minus_M0r_reversal | -0.0528 | [-0.1333, 0.0278] |
| pairwise_acc_vflip (tie-half / strict) | 0.6444 / 0.6556 | |
| pairwise_acc_reversal (tie-half / strict) | 0.6083 / 0.6111 | |
| pairwise_acc_hflip (tie-half / strict) | 0.6417 / 0.6389 | |

## 6. (B) M1 specificity dose-response (low 0.5x / mid 1x / high 2x)

| level | A (pooled) | CI | A_B1 | A_B2 | D_1 | Holm-6 | D_2 | Holm-6 | A0 | outcome |
|---|---|---|---|---|---|---|---|---|---|---|
| low | 0.5939 | [0.5460, 0.6416] | 0.3747 | 0.4303 | 0.2192 | 0.00060 | 0.1636 | 0.00060 | 0.7222 | Detection-limited (Not specific) |
| mid | 0.5457 | [0.5010, 0.5905] | 0.3352 | 0.3793 | 0.2105 | 0.00060 | 0.1664 | 0.00060 | 0.7222 | Detection-limited (Not specific) |
| high | 0.5005 | [0.4578, 0.5428] | 0.2888 | 0.3239 | 0.2117 | 0.00060 | 0.1766 | 0.00060 | 0.7222 | Detection-limited (Not specific) |

Per type (A_M, D_1, D_2, Holm-24 of each):

| level | type | A_M | D_1 | Holm-24 | D_2 | Holm-24 |
|---|---|---|---|---|---|---|
| low | lighting_global | 0.6623 | 0.2396 | 0.00240 | 0.1921 | 0.00240 |
| low | lighting_local | 0.5244 | 0.2108 | 0.00240 | 0.1583 | 0.00240 |
| low | jolt_base | 0.6070 | 0.2169 | 0.00240 | 0.1535 | 0.00240 |
| low | zoom_base | 0.5819 | 0.2095 | 0.00240 | 0.1506 | 0.00240 |
| mid | lighting_global | 0.6215 | 0.2598 | 0.00240 | 0.2279 | 0.00240 |
| mid | lighting_local | 0.4804 | 0.2073 | 0.00240 | 0.1644 | 0.00240 |
| mid | jolt_base | 0.5528 | 0.1809 | 0.00240 | 0.1233 | 0.00240 |
| mid | zoom_base | 0.5281 | 0.1941 | 0.00240 | 0.1500 | 0.00240 |
| high | lighting_global | 0.5548 | 0.2779 | 0.00240 | 0.2489 | 0.00240 |
| high | lighting_local | 0.4591 | 0.2272 | 0.00240 | 0.1989 | 0.00240 |
| high | jolt_base | 0.5014 | 0.1468 | 0.00240 | 0.1016 | 0.00240 |
| high | zoom_base | 0.4868 | 0.1950 | 0.00240 | 0.1572 | 0.00240 |

## 7. (B) M1 H1 dose-response (dAcc, flip; f0 over the same pairs; Holm-30 over 15 dAcc + 15 flip tests)

| cell | n | dAcc | CI | p cluster | Holm-30 | flip | f0 | flip-f0 | p flip | Holm-30 |
|---|---|---|---|---|---|---|---|---|---|---|
| brightness-low | 180 | -0.0000 | [-0.021, 0.020] | 0.9834 | 1.0000 | 0.0704 | 0.2148 | -0.1444 | 1.0000 | 1.0000 |
| brightness-mid | 180 | 0.0074 | [-0.019, 0.035] | 0.6030 | 1.0000 | 0.0963 | 0.2148 | -0.1185 | 1.0000 | 1.0000 |
| brightness-high | 180 | -0.0241 | [-0.051, 0.003] | 0.0786 | 1.0000 | 0.1241 | 0.2148 | -0.0907 | 0.9999 | 1.0000 |
| noise-low | 180 | -0.1769 | [-0.225, -0.130] | 0.0000 | 0.0000 | 0.3315 | 0.2148 | 0.1167 | 0.0000 | 0.0000 |
| noise-mid | 180 | -0.1991 | [-0.251, -0.147] | 0.0000 | 0.0000 | 0.3500 | 0.2148 | 0.1352 | 0.0000 | 0.0000 |
| noise-high | 180 | -0.2056 | [-0.257, -0.153] | 0.0000 | 0.0000 | 0.3778 | 0.2148 | 0.1630 | 0.0000 | 0.0000 |
| blur-low | 180 | -0.0472 | [-0.092, -0.006] | 0.0370 | 0.6290 | 0.1833 | 0.2148 | -0.0315 | 0.8626 | 1.0000 |
| blur-mid | 180 | -0.1194 | [-0.169, -0.069] | 0.0000 | 0.0000 | 0.2556 | 0.2148 | 0.0407 | 0.0983 | 1.0000 |
| blur-high | 180 | -0.1444 | [-0.194, -0.094] | 0.0000 | 0.0000 | 0.3111 | 0.2148 | 0.0963 | 0.0001 | 0.0021 |
| jpeg-low | 180 | 0.0583 | [0.014, 0.106] | 0.0120 | 0.2400 | 0.1444 | 0.2148 | -0.0704 | 0.9917 | 1.0000 |
| jpeg-mid | 180 | 0.0083 | [-0.033, 0.053] | 0.7570 | 1.0000 | 0.1722 | 0.2148 | -0.0426 | 0.9122 | 1.0000 |
| jpeg-high | 180 | -0.1083 | [-0.164, -0.053] | 0.0000 | 0.0000 | 0.2833 | 0.2148 | 0.0685 | 0.0171 | 0.3249 |
| zoom-low | 134 | 0.0448 | [0.008, 0.086] | 0.0178 | 0.3249 | 0.1493 | 0.2463 | -0.0970 | 0.9939 | 1.0000 |
| zoom-low_allpairs | 180 | 0.0472 | [0.014, 0.083] | 0.0068 | - | 0.1389 | 0.2148 | -0.0759 | 0.9929 | - |
| zoom-low_keep112 | 112 | 0.0312 | [-0.005, 0.073] | 0.1400 | - | 0.1339 | 0.2321 | -0.0982 | 0.9872 | - |
| zoom-mid | 120 | -0.0208 | [-0.074, 0.034] | 0.4912 | 1.0000 | 0.1500 | 0.2389 | -0.0889 | 0.9946 | 1.0000 |
| zoom-mid_allpairs | 180 | 0.0306 | [-0.017, 0.081] | 0.2360 | - | 0.1722 | 0.2148 | -0.0426 | 0.9110 | - |
| zoom-mid_keep112 | 112 | -0.0268 | [-0.082, 0.031] | 0.3946 | - | 0.1518 | 0.2321 | -0.0804 | 0.9863 | - |
| zoom-high | 112 | -0.0045 | [-0.056, 0.049] | 0.9248 | 1.0000 | 0.1429 | 0.2321 | -0.0893 | 0.9921 | 1.0000 |
| zoom-high_allpairs | 180 | 0.0083 | [-0.036, 0.053] | 0.7618 | - | 0.1500 | 0.2148 | -0.0648 | 0.9830 | - |
| zoom-high_keep112 | 112 | -0.0045 | [-0.056, 0.049] | 0.9248 | - | 0.1429 | 0.2321 | -0.0893 | 0.9921 | - |

## 8. (C) EXPLORATORY: onset-aligned specificity and halve_hold

Onset-aligned (t_on from kaggle/expl_onset_spec/matches.json; same tau): outcome Detection-limited (Not specific (Reversed)); A 0.3917 [0.3538, 0.4281]; A_B1 0.3272; A_B2 0.3808; A0 M 0.7222 [0.6528, 0.7889] (B1 0.5833, B2 0.6611); D_1 0.0645 [0.023, 0.109] p 0.00130 Holm-2 0.00260; D_2 0.0110 [-0.026, 0.051] p 0.27700 Holm-2 0.27700; without lighting_global A 0.3922; per type {"lighting_global": 0.3902, "lighting_local": 0.4595, "jolt_base": 0.4001, "zoom_base": 0.317}; events {'t_on_median': 49.0, 't_on_min': 16, 't_on_max': 88, 'n_fallback': 0, 'n_transient': 60, 'm_i_median_gray': 0.530129355029203}; mid ratio in band {'lighting_global': 0.8, 'lighting_local': 0.9833333333333333, 'jolt_base': 1.0, 'zoom_base': 1.0}; seeds {'lighting_global': 3, 'lighting_local': 3, 'jolt_base': 3, 'zoom_base': 1}

halve_hold vs clean skip-2 (EXPLORATORY): n 180, dAcc 0.0194 CI [-0.033, 0.075] p_cluster 0.5066; flip 0.2000; f0 0.2148; flip-f0 -0.0148 CI [-0.081, 0.052] p_flip 0.6698; acc edit 0.8278 vs clean 0.8083; strict flip 0.1500 vs strict f0 0.1556

## 9. (D) IntPhys 2 Main, M1 clean fp16 (506 pairs)

1012 videos, 506 pairs, 253 scenes, blocks {'continuity': 120, 'immutability': 120, 'permanence': 120, 'solidity': 146}; 8 videos share a name with Debug (4 pairs affected).

| score | set | n | tau | tie-half [CI] | strict [CI] | ties | continuity | immutability | permanence | solidity |
|---|---|---|---|---|---|---|---|---|---|---|
| M1 | all | 506 | 1.115e-04 | 0.4763 [0.437, 0.517] | 0.4783 [0.437, 0.522] | 30 | 0.467 / 0.475 | 0.421 / 0.417 | 0.496 / 0.500 | 0.514 / 0.514 |
| M1 | without_debug_overlap | 502 | 1.115e-04 | 0.4761 [0.436, 0.517] | 0.4781 [0.436, 0.522] | 30 | 0.467 / 0.475 | 0.421 / 0.417 | 0.496 / 0.500 | 0.514 / 0.514 |
| B1 | all | 506 | 6.297e-06 | 0.5119 [0.470, 0.552] | 0.5119 [0.470, 0.553] | 8 | 0.571 / 0.575 | 0.463 / 0.458 | 0.496 / 0.500 | 0.517 / 0.514 |
| B1 | without_debug_overlap | 502 | 6.297e-06 | 0.5120 [0.470, 0.553] | 0.5120 [0.470, 0.554] | 8 | 0.571 / 0.575 | 0.463 / 0.458 | 0.496 / 0.500 | 0.518 / 0.514 |
| B2 | all | 506 | 1.267e-05 | 0.5188 [0.478, 0.559] | 0.5198 [0.478, 0.561] | 19 | 0.508 / 0.500 | 0.467 / 0.467 | 0.537 / 0.542 | 0.555 / 0.562 |
| B2 | without_debug_overlap | 502 | 1.267e-05 | 0.5189 [0.478, 0.559] | 0.5199 [0.478, 0.562] | 19 | 0.508 / 0.500 | 0.467 / 0.467 | 0.537 / 0.542 | 0.556 / 0.563 |
| B3 | all | 506 | 3.831e-05 | 0.4664 [0.426, 0.507] | 0.4664 [0.425, 0.508] | 10 | 0.475 / 0.475 | 0.417 / 0.425 | 0.500 / 0.483 | 0.473 / 0.479 |
| B3 | without_debug_overlap | 502 | 3.831e-05 | 0.4661 [0.426, 0.507] | 0.4661 [0.425, 0.508] | 10 | 0.475 / 0.475 | 0.417 / 0.425 | 0.500 / 0.483 | 0.472 / 0.479 |

## 10. (E) G1' ladder facts

- P2_fp32_M1: tau 1.0571e-04, tie-half 0.8167, strict 0.8056, ties 8, tie-half at fixed 1e-4 0.8167
- P2H_fp16_M1H: tau 1.1955e-04, tie-half 0.8833, strict 0.8778, ties 4, tie-half at fixed 1e-4 0.8806
- P2_B1: tau 7.2286e-07, tie-half 0.5806, strict 0.5722, ties 7, tie-half at fixed 1e-4 0.5000
- P2_B2: tau 1.3560e-06, tie-half 0.7611, strict 0.7611, ties 0, tie-half at fixed 1e-4 0.6250
- P2_B3: tau 4.2555e-05, tie-half 0.4333, strict 0.4111, ties 10, tie-half at fixed 1e-4 0.4417
- precisions from run meta: P2 fp32, ViT-H fp16, P4 M1 fp16. b1_whole_window stored in npz: False (not recomputable from the arrays).
