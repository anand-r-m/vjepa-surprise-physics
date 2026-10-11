# M2 (V-JEPA 2) H1 / H2 / H3, DESCRIPTIVE (M2 is H1-ineligible: clean 60.8% < 80%; no interpretation beyond the prereg decision rules)

Date 2026-10-10. Script `scripts/run_m2.py` (new) calls the frozen driver `scripts/run_analysis.py` (unmodified: clean, h1, h2 via `main`) and its `h3_stage` function for H3 (the driver's `main` only dispatches H3 for M1). `scripts/m2_ties.py` (new) writes the tie counts using the frozen P functions. n_boot 10000, bootstrap seed 20261015, matches `kaggle/h2_spec_a/matches.json`, crop retention `results/analysis/h1/retention.json` (same 68 pairs excluded, zoom n = 112).
Runs: M2 clean = `P4_M2_ipdev_clean-mi0_s1` (mask_index 0; the old mask_index-1 run is in `EXCLUDED_RUNS`), clean-skip4, all high-strength H1 runs, dither x3, mid spec runs, base_ref, controls (hflip, vflip, time_reversal); M0r clean init0 and M0r vflip are the frozen H3 reference. Meta check run first (inside the driver): ok, 39 runs, no mismatch, no bypass (`results/analysis/m2/meta_check.json`).
Outputs: `results/analysis/m2/{clean,h1_M2,h2,h3_M2,m2_ties}.json`, `m2/strict/{clean,h1_M2_strict,h2_strict,h3_M2_strict}.json`, `m2/exactties/{...}_exactties.json`. All labelled descriptive. M2 H1 `status` (all variants): "descriptive (floor f0 >= 10%)"; also descriptive by eligibility (clean 60.8% tie-half; 60.6% strict).
Also done: `results/analysis/p4/{clean,strict/clean,exactties/clean}.json` rerun with the corrected M2 row; old files kept as `clean_old_mask_index1.json` in each dir.

## Clean (P4 clean.json, mean aggregation, tie-half / strict / ties)
| score | tau | acc tie-half | strict | n ties | O1 / O2 / O3 |
|---|---|---|---|---|---|
| M2 (mi0) | 1.109e-4 | 60.8% | 60.6% | 17 | 61.7 / 54.2 / 66.7 |
| M2 old (mask_index 1, excluded) | 1.158e-4 | 46.9% | 46.7% | 19 | |
| B1(M2) | 7.20e-7 | 57.8% | 58.3% | 10 | |
| B2(M2) | 1.36e-6 | 76.1% | 76.1% | 2 | |
| B3(M2) | 3.57e-5 | 17.2% | 17.2% | 0 | 28.3 / 8.3 / 15.0 |
| M1 for reference | 1.057e-4 | 80.8% | 81.1% | 7 | |
Max aggregation: M2 64.7% (41 ties), B3(M2) 38.9%. Fixed-C (A2, mean agg): C=2 71.7%, C=6 54.7%, C=10 59.7%. T1 (M1 minus B2 paired) unchanged: +4.7 pp [-1.1, 10.3].

## H1, M2 (tie-half primary; tau 1.109e-4; clean y0 60.8%; f0 = 24.6%, strict 17.4%)
| edit (high) | n | dacc pp [95% CI] | flip f_e | flip - f0 pp | Holm p dacc | Holm p flip | verdict |
|---|---|---|---|---|---|---|---|
| brightness | 180 | -0.4 [-3.1, +2.5] | 15.4% | -9.3 | 1.000 | 1.000 | invariant |
| noise | 180 | -6.4 [-11.6, -1.1] | 28.3% | +3.7 | 0.174 | 0.318 | inconclusive |
| blur | 180 | +12.8 [+6.4, +19.4] | 42.2% | +17.6 | 0.005 | 0.000 | violated |
| jpeg | 180 | -1.7 [-7.8, +4.7] | 40.6% | +15.9 | 1.000 | 0.000 | violated (flip route) |
| zoom (crop) | 112 | +7.1 [+1.8, +12.7] | 25.0% | -5.7 | 0.132 | 1.000 | invariant |
| hflip | 180 | +3.3 [-0.3, +6.9] | 15.6% | -9.1 | 0.595 | 1.000 | invariant |
| fps_halve | 180 | 0.0 [0.0, 0.0] | 0.0% | -24.6 | 1.000 | 1.000 | invariant (degenerate) |

Strict (`<`, tau 0, ties 0), f0 = 17.4%; exact-ties (tau 0, ties 0.5) is numerically identical to strict (0 exact ties in every run at tau 0):
| edit | n | dacc pp [95% CI] | flip | flip - f0 pp | Holm p dacc | Holm p flip | verdict |
|---|---|---|---|---|---|---|---|
| brightness | 180 | -0.7 [-4.4, +3.0] | 10.0% | -7.4 | 1.000 | 1.000 | invariant |
| noise | 180 | -6.9 [-12.8, -0.9] | 21.7% | +4.3 | 0.210 | 0.098 | inconclusive |
| blur | 180 | +14.4 [+7.2, +21.7] | 31.1% | +13.7 | 0.005 | 0.004 | violated |
| jpeg | 180 | +1.7 [-5.6, +8.9] | 35.0% | +17.6 | 1.000 | 0.000 | violated (flip route) |
| zoom | 112 | +7.1 [0.0, +14.3] | 19.6% | -0.9 | 0.598 | 1.000 | inconclusive |
| hflip | 180 | +3.3 [-1.7, +8.3] | 12.2% | -5.2 | 1.000 | 1.000 | invariant |
| fps_halve | 180 | 0.0 | 0.0% | -17.4 | 1.000 | 1.000 | invariant (degenerate) |

Tie counts (pairs with |difference| <= tau of 180; mean aggregation): clean 17; skip-4 reference 8; brightness s1/s2/s3 9/10/16; noise 19/22/23; blur 19; jpeg 27; zoom 15 (before the 68-pair crop exclusion); hflip 9; fps_halve 8; dither 8/22/18. At tau 0 all 0.

## H2, M2 (event-aligned max, own tau, tie-half; matches h2_spec_a; 180 pairs, 0 late; 178 of 180 are no-event fallback windows as for M1)
tau (event-aligned max): M2 1.157e-4, B1 1.464e-6, B2 2.920e-6, B3 4.464e-5.
| score | A [95% CI] | lighting_global | lighting_local | jolt_base | zoom_base | A0 [CI] |
|---|---|---|---|---|---|---|
| M2 | 0.449 [0.403, 0.496] | 0.551 | 0.357 | 0.446 | 0.442 | 0.600 [0.542, 0.658] |
| B1 | 0.324 [0.280, 0.368] | 0.360 | 0.272 | 0.356 | 0.308 | 0.556 [0.522, 0.592] |
| B2 | 0.376 [0.329, 0.426] | 0.393 | 0.316 | 0.426 | 0.369 | 0.600 [0.561, 0.644] |
| B3 (descr.) | 0.372 [0.328, 0.415] | 0.347 | 0.283 | 0.442 | 0.416 | 0.344 [0.294, 0.392] |

| contrast | D [95% CI] | p (one-sided) | Holm-2 p | sig |
|---|---|---|---|---|
| D_1 = A_M2 - A_B1 | +0.125 [0.078, 0.173] | 1.0e-4 (floor) | 2.0e-4 | yes |
| D_2 = A_M2 - A_B2 | +0.073 [0.022, 0.125] | 0.0032 | 0.0032 | yes |
Seed AUROCs M2 0.449 / 0.449 / 0.448. Foil accuracy (secondary) 0.498. R = (A-0.5)/(A0-0.5) = -0.511.
Verdict by the rule: A <= 0.65 -> "Not specific"; A0 = 0.600 < 0.85 -> driver outcome **"Detection-limited (not specific / partial)"**. Reversed sub-label (prereg: upper CI of A < 0.50): upper CI 0.496 < 0.50, so the sub-label applies; the driver's `outcome_M2` tuple shows reversed = False because `h2_stage` calls `h2_outcome` without `A_hi` (frozen; same for M1 where upper CI 0.591 does not meet it). Per-type AUROC < 0.65 for all four types.

| variant | A_M2 [CI] | per-type (lg, ll, jb, zb) | A0 | A_B1 | A_B2 | D_1 (Holm p) | D_2 (Holm p) | foil |
|---|---|---|---|---|---|---|---|---|
| primary tie-half | 0.449 [0.403, 0.496] | .551 .357 .446 .442 | 0.600 | 0.324 | 0.376 | +0.125 (2e-4) | +0.073 (0.0032) | 0.498 |
| strict | 0.438 [0.390, 0.487] | .511 .356 .444 .441 | 0.506 | 0.311 | 0.363 | +0.127 (2e-4) | +0.075 (0.0038) | 0.477 |
| exact-ties | 0.448 [0.401, 0.496] | .544 .358 .447 .443 | 0.594 | 0.322 | 0.374 | +0.126 (2e-4) | +0.074 (0.0033) | 0.492 |
| excl. lighting_global (match target missed), tie-half | 0.415 [0.370, 0.462] | - .357 .446 .442 | 0.600 | - | - | +0.103 (2e-4) | +0.044 [-0.007, 0.097] (0.0477) | - |
| excl. lighting_global, strict | 0.414 [0.369, 0.461] | - .356 .444 .441 | | | | +0.106 (2e-4) | +0.049 (0.0351) | |
| excl. lighting_global, exact-ties | 0.416 [0.371, 0.463] | - .358 .447 .443 | | | | +0.106 (2e-4) | +0.048 (0.0345) | |
Descriptive strata (primary): by block M2 A O1 0.458, O2 0.438, O3 0.449 (B2: 0.396, 0.422, 0.323). By onset proxy: abrupt (n 86) M2 0.477 vs B2 0.306; gradual/occluded (n 94) M2 0.423 vs B2 0.453. Median target-feature distance edit vs ref: lighting_global 0.0049, lighting_local 0.0356, jolt_base 0.0186, zoom_base 0.0239.

Tie counts (primary tau, 180 pairs; `m2_ties.json`): clean event-aligned |dv| <= tau: M2 34 (32 exactly 0), B1 42, B2 42, B3 42. Abrupt-edit effect |S(edit)-S(ref)| <= tau per seed: lighting_global 89/89/89, lighting_local 15/15/15, jolt_base 19/29/15, zoom_base 19. Fraction of the 180 x 180 AUROC comparisons in the tie band: lighting_global 10.4%, lighting_local 2.2%, jolt_base 3.2/4.2/2.7%, zoom_base 3.0%.

## H3 / G2, M2 (controls from `m2_g2_controls`; M0r reference as for M1)
| quantity | tie-half | strict | exact-ties |
|---|---|---|---|
| (a) vflip detection vs clean | 0.719 [0.644, 0.792] | 0.722 [0.644, 0.794] | 0.722 [0.644, 0.794] |
| (b) vflip vs hflip reference | 0.728 [0.653, 0.800] | 0.739 [0.661, 0.811] | 0.739 [0.661, 0.811] |
| detection_M2 - detection_M0r | -0.158 [-0.250, -0.067] | -0.156 [-0.256, -0.056] | -0.156 [-0.256, -0.056] |
| time-reversal detection (not gating) | 0.464 | 0.450 | 0.450 |
| pairwise acc on vflipped pairs | 0.644 (strict 0.656) | 0.656 | 0.656 |
| pairwise acc on reversed pairs | 0.608 (strict 0.611) | 0.611 | 0.611 |
Rule outputs: learned sensitivity credited = false; G2 flag = false (vflip detection 71.9% < 80%; lower bound of (b) 0.653 > 0.5). detection_M0r = 0.719 + 0.158 = 0.877 (same M0r runs as M1). Tie counts at tau 1.157e-4 for control-vs-clean: vflip 3, hflip 6, time_reversal 5 (of 180). Time reversal detection < 0.5 triggers `reversal_below_half_diagnostic_needed = true`.

## Peculiarities
1. M2 is H1-ineligible (clean 60.8%); every H1 row is descriptive. f0 = 24.6% / 17.4% also exceeds the 10% rule.
2. fps_halve is again bit-identical to the clean skip-4 reference (`np.array_equal` of S, true), so dacc = flip = 0 by construction (as for M1).
3. M2 blur has a significantly positive dacc (+12.8 pp, Holm 0.005) and an unusually large flip (42%); the rule labels it "violated" via the two-sided dacc and the flip test. Not investigated.
4. B3(M2) clean accuracy is 17.2% (mean, 0 ties) versus 45.3% for B3(M1); max aggregation 38.9% vs 62.2%. Cause not investigated (B3 is descriptive, an M2-specific latent baseline).
5. B1(M2) and B1(M1) differ slightly (clean 57.8 vs 58.1%, tau 7.20e-7 vs 7.23e-7, H2 A 0.324 vs 0.335); B2 clean accuracy is identical (76.1%). The baselines are therefore not bit-identical across the M1 and M2 runs (preprocessing differs); cause not investigated.
6. H2: both M2 A = 0.449 (upper CI 0.496) and the lighting_global-excluded 0.415 are below 0.5; D_1, D_2 are significant only because the baselines are below 0.5 (as for M1). D_2 excluding lighting_global has CI [-0.007, 0.097] and Holm p 0.048.
7. lighting_global: 89 of 180 abrupt-edit effects are inside the tie band (M1: 84); same match miss.
8. H3: M2 vflip detection 71.9% is far above M1's 21%, still below the 80% G2 gate; time-reversal detection 46.4% (< 0.5).

---

## Dose-response, M2 (added 2026-10-10; descriptive; script `scripts/run_dose_m2.py`, outputs `results/analysis/m2/dose/`)
Full tables, families (H1 Holm-22 over the 11 existing cells; H2 Holm-24 over 12 cells x 2 contrasts) and the list of missing cells with GPU-hours are in `notes/DOSE_RESPONSE.md` (section "A3 dose-response, M2"). Meta check ok (53 runs). Seed 1 only for every dose cell (the as-run variant adds seeds 2-3 at high for brightness/noise and reproduces `h1_M2.json`).
Summary: H1 (tie-half, s1): brightness invariant at low/mid/high (dAcc +1.4/+2.8/-0.6 pp); noise inconclusive at all three (-4.4/-8.1/-7.8 pp); blur dAcc positive and large at every strength (+15.8/+18.6/+12.8 pp, Holm-22 0.000/0.000/0.007; "violated" only at high); jpeg-high violated via flip (40.6%), zoom-high invariant (112 pairs). None of the three-level edits shows a monotone dose pattern. H2: pooled A 0.483 / 0.449 / 0.420 at low / mid / high (decreasing with strength in every type; all below 0.65; D_1 significant everywhere, D_2 not significant at the Holm-24 level in lighting_local (all levels), jolt_base (all levels) and zoom_base low).
Not run: jpeg/zoom low/mid, seed 2-3 groups (about 9.4-11.9 GPU-h).
