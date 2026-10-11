# H2 (specificity) and H3 confirmatory analysis, M1 (frozen driver; no interpretation beyond the prereg decision rule)

Date 2026-10-10. Driver `scripts/run_analysis.py --models M1 --stages h2` (and `--stages h3`), unmodified; src/analysis, prereg and frozen parameters untouched. n_boot 10000, bootstrap seed 20261015 (in code). Matches: `kaggle/h2_spec_a/matches.json`.
Runs dir (symlinks, scratchpad): 46 runs (M1 and M0r) from `results/raw/{p4_clean_m1,g2_controls,h2_spec_a,h2_spec_b}`. Not opened: any m2_* / p4_clean_m2* run, ip2main_clean_m1 (descriptive clean only per prereg s8; not analysed here).
Meta check (run first, by the driver): ok, 46 runs, no mismatch, no bypass (`results/analysis/h2/meta_check.json`; the repo_head allowlist covers the heads present).
Outputs: `results/analysis/h2/h2.json` (primary, tie-half, event-aligned max), `h2/strict/h2_strict.json` (tau 0, ties 0), `h2/exactties/h2_exactties.json` (tau 0, ties 0.5), `h2/extra_ties_m0r.json` (tie counts and the M0r row, from a scratch script that only calls the frozen functions; see M0r). H3: `results/analysis/h3_final/{h3_M1,strict/h3_M1_strict,exactties/h3_M1_exactties}.json`. `results/analysis/p4/` untouched.
Process note: my first invocation of the strict / exact-ties variants had a shell word-splitting bug and silently wrote the primary result into `h2/strict/h2.json` and `h2/exactties/h2.json`; those two files were deleted and the variants rerun correctly (variant fields verified: strict tie_value 0, tau_scale 0; exact-ties tie_value 0.5, tau_scale 0).

## Setup facts
- 180 pairs used, 0 excluded as late (t_on > 94).
- **No-event fallback: 178 of 180 pairs** (`event.fallback = true`; t_on is a seeded uniform draw in the middle 50 percent of the video, t_off = T). Only 2 pairs (O3/17 p0 and p1) have a data-derived event (both transient). Expected 0 under the prereg; the fixed rule was executed as written. The event-aligned window set, the matched edits and m_i all use these drawn times, not the true splice time.
- tau (full-clip-max clean scores, 2e-4 x median): M1 1.088e-4, B1 1.467e-6, B2 2.920e-6, B3 4.528e-5, M0r 1.704e-4.
- Match quality at mid (from matches.json meta): lighting_global median r 0.906, 50.0% in [0.9,1.1], **target MISSED**; lighting_local 1.000 / 96.7% met; jolt_base 1.000 / 97.8% met; zoom_base 1.000 / 97.8% met. 12 of 540 seeded entries and 4 of 180 zoom entries have m_i = 0 (ratio NaN). Cause of the lighting_global miss per MATCHES.md: required gain below the uint8 step (edit rounds to no change); 84 of 180 pairs have |Delta_abrupt| <= tau for lighting_global (see ties).
- Descriptors: median onset frame-diff 0.0, median affected-area fraction 0.018, 2 transient pairs. Median M1 target-feature distance edit vs ref: lighting_global 0.0049, lighting_local 0.0178, jolt_base 0.0113, zoom_base 0.0158.

## Primary (tie-half), aggregated A and per type, M1 vs baselines
A = seed-mean pooled AUROC (mean of per-type AUROCs), 95% percentile CI (scene-cluster bootstrap, block-stratified). The driver outputs no per-type CIs.

| score | A [95% CI] | lighting_global | lighting_local | jolt_base | zoom_base | A0 (clean pair acc, H2 aggregation) [CI] |
|---|---|---|---|---|---|---|
| M1 | 0.546 [0.501, 0.591] | 0.622 | 0.480 | 0.553 | 0.528 | 0.722 [0.664, 0.781] |
| B1 (windowed frame diff) | 0.335 [0.293, 0.378] | 0.362 | 0.273 | 0.372 | 0.334 | 0.556 [0.522, 0.592] |
| B2 (copy-last-context) | 0.379 [0.332, 0.429] | 0.394 | 0.316 | 0.430 | 0.378 | 0.600 [0.561, 0.644] |
| B3 (descriptive) | 0.552 [0.509, 0.595] | 0.560 | 0.736 | 0.466 | 0.446 | 0.614 [0.550, 0.678] |

| contrast | D [95% CI] | one-sided p | Holm-2 adjusted p | significant (adj p < .05) |
|---|---|---|---|---|
| D_1 = A_M1 - A_B1 | +0.211 [0.161, 0.262] | 1.0e-4 (floor) | 2.0e-4 | yes |
| D_2 = A_M1 - A_B2 | +0.166 [0.117, 0.216] | 1.0e-4 (floor) | 2.0e-4 | yes |

Seed AUROCs M1: 0.5456, 0.5473, 0.5443 (SD 0.0015). Foil accuracy (secondary) M1: 0.605. Retention R = (A-0.5)/(A0-0.5) = 0.206 (descriptive).

## Verdict per the prereg rule
A = 0.546 <= 0.65 -> "Not specific". A0_M1 = 0.722 < 0.85 -> by the detection-precondition rule the outcome is reported as **"Detection-limited (not specific / partial)"** (driver `outcome_M1`). A is not "Reversed" (upper CI 0.591 >= 0.5). D_1 and D_2 are both Holm-2 significant, but that is only a condition of the "Specific" and "Separable" rows (both require A >= 0.80), which are not reached. Per-type AUROC < 0.65 for all four types (lighting_local 0.480 is below 0.5). Not "Specific" (also not "Specific, except type k"). Same verdict in all three variants and in the lighting_global-excluded sensitivity.

## Sensitivities
| variant | A_M1 [CI] | per-type (lg, ll, jb, zb) | A0 | A_B1 | A_B2 | D_1 (adj p) | D_2 (adj p) | foil acc | outcome |
|---|---|---|---|---|---|---|---|---|---|
| primary (tie-half, tau) | 0.546 [0.501, 0.591] | .622 .480 .553 .528 | 0.722 | 0.335 | 0.379 | +0.211 (2e-4) | +0.166 (2e-4) | 0.605 | Detection-limited |
| strict (`<`, tau 0, ties 0) | 0.540 [0.494, 0.585] | .602 .480 .551 .525 | 0.667 | 0.322 | 0.368 | +0.218 (2e-4) | +0.172 (2e-4) | 0.593 | Detection-limited |
| exact-ties (tau 0, ties 0.5) | 0.545 [0.501, 0.591] | .622 .481 .552 .527 | 0.719 | 0.333 | 0.378 | +0.212 (2e-4) | +0.167 (2e-4) | 0.607 | Detection-limited |
| exclude lighting_global (match target missed), tie-half | 0.520 [0.476, 0.566] | - .480 .553 .528 | 0.722 | - | - | +0.194 (2e-4) | +0.146 (2e-4) | - | Detection-limited |
| exclude lighting_global, strict | 0.519 | - .480 .551 .525 | 0.667 | - | - | see json | see json | - | Detection-limited |
| exclude lighting_global, exact-ties | 0.520 | - .481 .552 .527 | 0.719 | - | - | see json | see json | - | Detection-limited |

Strict / exact-ties CIs: strict A_B1 [0.278, 0.367], A_B2 [0.320, 0.419], D_1 CI [0.167, 0.270], D_2 CI [0.122, 0.223]; exact-ties D_1 CI [0.163, 0.264], D_2 CI [0.118, 0.217].
Descriptive strata (primary; not decision-bearing): by block M1 A: O1 0.548, O2 0.555, O3 0.535 (B2: 0.398, 0.426, 0.327). By onset proxy: abrupt (n 86) M1 0.555 vs B2 0.310; gradual/occluded (n 94) M1 0.537 vs B2 0.455.

## Tie counts (primary tau, 180 pairs unless noted)
- Clean event-aligned Delta_viol: |dv| <= tau for 22 pairs (19 exactly zero). Baselines: B1 38, B2 48, B3 19.
- Abrupt-edit effect |S(edit) - S(ref)| <= tau (M1), per seed: lighting_global 84/84/84, lighting_local 17/17/17, jolt_base 23/23/19, zoom_base 13.
- Fraction of the 180 x 180 AUROC comparisons falling in the tie band (M1): lighting_global 6.3%, lighting_local 2.2%, jolt_base 2.5%, zoom_base 2.0%.
- At tau 0 (strict / exact-ties) only exact zeros tie; the variant outputs above are the evidence that the conclusion does not depend on the tie rule.

## T1b (descriptive; not part of any decision rule)
Source `results/analysis/b2_checks.json` (`breakdown_mean_agg`, P2 fp32 clean run, mean aggregation, tie-half / strict). The file's all / visible / occluded cells for M1, B1 (windowed), B2 agree with the table in docs/PREREGISTRATION.md section 6 (e.g. all 81.7/80.6, 58.1/57.2, 76.1/76.1; visible M1 86.7/85.6; occluded M1 76.7/75.6); the full per-block and visible x block T1b table is that prereg table, not regenerated here (no new H2 data enter T1b).

## M0r row (descriptive only; prereg designates M0r descriptive)
The driver cannot run `--models M1 M0r` for H2: M0r mid-strength runs exist for seed 1 only (no seeds 2, 3 for the seeded types), and the driver requires all three. I therefore computed M0r with the same frozen functions (event-aligned max, own tau, tie-half) in a scratch script using seed 1 only; this is a point estimate with no CI and no bootstrap, labelled descriptive.
- M0r A = 0.503 (lighting_global 0.504, lighting_local 0.503, jolt_base 0.504, zoom_base 0.501). A0 = 0.503. Clean |dv| <= tau for 179 of 180 pairs.
- 98.1 to 99.4 percent of AUROC comparisons are tie-band (0.5 by construction); |Delta_abrupt| <= tau for 179 to 180 of 180 pairs in every type.
- (M1 with the same code path reproduces the driver's A exactly: 0.54572.)

## H3 (g2_controls + M0r vflip; `h3_final`, identical numerically to `results/analysis/p4/h3_M1.json`, which was not overwritten)
| quantity | tie-half | strict | exact-ties |
|---|---|---|---|
| (a) vflip detection vs clean, M1 | 0.211 [0.147, 0.283] | 0.206 [0.139, 0.278] | 0.206 [0.139, 0.278] |
| (b) vflip detection vs hflip reference, M1 | 0.258 [0.186, 0.333] | 0.261 [0.189, 0.339] | 0.261 [0.189, 0.339] |
| detection_M1 - detection_M0r | -0.667 [-0.761, -0.567] | -0.672 [-0.778, -0.556] | -0.672 [-0.778, -0.556] |
| time-reversal detection (reported, not gating) | 0.608 | 0.600 | 0.600 |
| pairwise acc on vflipped pairs (mean agg) | 0.839 / 0.822 strict | | |
| pairwise acc on reversed pairs | 0.747 / 0.733 strict | | |
Decision rule results: learned sensitivity credited = false (lower bound of M1 - M0r is below 0; lower bound of (b) 0.186 is not > 0.5). G2 flag from the driver = false (vflip detection 21 percent, far below 80 percent). Pairwise accuracies are the free secondary (tie-half value / strict value).

## Anomalies
1. **Fallback event times for 178 of 180 pairs** (already in MATCHES.md); all t*-dependent H2 quantities use drawn windows.
2. **Both baselines have A well below 0.5** (B1 0.335, B2 0.379): Delta_abrupt of the pixel baselines exceeds Delta_viol on the fallback windows more often than not. So D_1, D_2 are large and Holm-significant only because the baselines are below chance, while M1 itself is at 0.546 with CI lower bound 0.501. B3 (descriptive) is at 0.552, equal to M1.
3. lighting_global match target missed; 84/180 abrupt-edit effects are inside the tie band (edit rounds to no change); it is also M1's highest-AUROC type (0.622), and dropping it lowers A to 0.520.
4. lighting_local per-type AUROC 0.480 (< 0.5).
5. **H3 positive control fails on vflip**: detection 21 percent (G2 requires >= 80 percent), M1 below M0r by 0.667 because M0r (97 to 99 percent ties) is credited 0.88 in detection_M0r (diff = a - M0r detection); the prereg says M0r detection should be about 0.5 by construction, so detection_M0r = 0.878 is itself unexpected (not investigated; reported only). Time-reversal detection 61 percent. vflip pairwise accuracy (83.9 percent tie-half) is higher than the clean 80.8 percent. This is a G2/pipeline-suspect flag for the lead; nothing was changed.
6. M0r H2 cannot be run through the driver (seed-1-only runs); descriptive point estimate from a scratch script instead.
7. Per-type CIs are not produced by the frozen driver.
