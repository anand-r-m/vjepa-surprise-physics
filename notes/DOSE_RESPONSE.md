# A3 dose-response, M1 (secondary; human request 2026-10-09)

Script `scripts/run_dose.py` (new; imports the frozen `scripts/run_analysis.py` helpers and `vjepa_study.analysis.prereg` unchanged). Outputs `results/analysis/h1/dose/{dose_M1,dose_M1_strict,dose_M1_exactties,meta_check}.json`. Same definitions as the H1 driver: fp16 clean reference `P4_M1_ipdev_clean_s1`, tie-half with tau = 1.057e-4, seed-averaged pair-level y/flip, dither floor f0 = 21.5% (tie-half) / 15.6% (strict, exact-ties), scene-cluster bootstrap stratified by block, 10,000 draws, seed 20261015. Meta check ok (precision/n_gpus uniform). Sanity: the five `@high` cells reproduce `h1_M1.json` dAcc and flip to 1e-12 (n = 180, zoom 112).

## What the spec / prereg require vs what exists

| Requirement | Source | Exists for M1? |
|---|---|---|
| low/mid/high for every graded invariance edit: brightness, noise (3 seeds each), blur, jpeg, zoom (deterministic) | spec s6 A3; prereg s3, s6 | **Yes, complete**: 27 runs, `P4_M1_ipdev_{brightness,noise}-{low,mid,high}_s{1,2,3}` (h1_inv_a, h1_inv_b) and `{blur,jpeg,zoom}-{low,mid,high}_s1` (h1_inv_c); all fp16, 2 GPUs, head 4c4017b |
| hflip, fps_halve, dither | prereg s3: single strength ("on") | No dose axis by design, not a gap (spec s6 "every edit" is broader than the prereg table) |
| low/high of the four specificity types (lighting_global, lighting_local, jolt_base, zoom_base) for AUROC-vs-strength (F3 right panel; prereg 0.5x / 1x / 2x of matched strength) | spec s6 A3, s7 F3; prereg s3, s6, s8 | **No. Never ran.** h2_spec_a failed (18/18, matches.json missing), h2_spec_b 2/18 ok (only `base_ref` for M1 and M0r). matches.json has since been embedded (bundles rebuilt at 4c4017b) but nothing was re-pushed |
| M2 dose-response (low/mid invariance, low/high spec; prereg s8 tier 3) | prereg s8 | **No.** No M2 edited run exists (M2 clean only); M2 is H1-ineligible (60.8%), groups built (`m2_dose_*`) but unrun |

Precisely, the missing low/mid/high cells are all in the H2 (specificity) family. Mid strength of those types is the **confirmatory H2** input, not A3, so the 10 mid runs are a larger gap than A3 (flag for the lead: H2 itself has no data yet).

## A3 result for H1 edits (M1, tie-half, fp16; 15 graded cells, Holm over 30 p = 15 dAcc + 15 flip-vs-floor)

| edit | strength | n | dAcc pp [95% CI] | flip % | flip - f0 pp | Holm p dAcc | Holm p flip | label |
|---|---|---|---|---|---|---|---|---|
| brightness | low | 180 | -0.0 [-2.0, 2.0] | 7.0 | -14.4 | 1.00 | 1.00 | invariant |
| | mid | 180 | +0.7 [-1.9, 3.5] | 9.6 | -11.9 | 1.00 | 1.00 | invariant |
| | high | 180 | -2.4 [-5.2, 0.2] | 12.4 | -9.1 | 1.00 | 1.00 | inconclusive |
| noise | low | 180 | -17.7 [-22.6, -13.1] | 33.1 | +11.7 | 0.000 | 0.000 | violated |
| | mid | 180 | -19.9 [-25.2, -14.8] | 35.0 | +13.5 | 0.000 | 0.000 | violated |
| | high | 180 | -20.6 [-25.8, -15.4] | 37.8 | +16.3 | 0.000 | 0.000 | violated |
| blur | low | 180 | -4.7 [-9.2, -0.3] | 18.3 | -3.1 | 0.656 | 1.00 | inconclusive |
| | mid | 180 | -11.9 [-16.9, -7.2] | 25.6 | +4.1 | 0.000 | 1.00 | violated (dAcc route) |
| | high | 180 | -14.4 [-19.4, -9.7] | 31.1 | +9.6 | 0.000 | 0.004 | violated |
| jpeg | low | 180 | +5.8 [1.1, 10.6] | 14.4 | -7.0 | 0.332 | 1.00 | invariant |
| | mid | 180 | +0.8 [-3.6, 5.3] | 17.2 | -4.3 | 1.00 | 1.00 | invariant |
| | high | 180 | -10.8 [-16.4, -5.6] | 28.3 | +6.9 | 0.000 | 0.332 | violated (dAcc route) |
| zoom | low (0.9) | 134 | +4.5 [0.8, 8.5] | 14.9 | -9.7 | 0.371 | 1.00 | invariant |
| | mid (0.8) | 120 | -2.1 [-7.5, 3.4] | 15.0 | -8.9 | 1.00 | 1.00 | inconclusive |
| | high (0.7) | 112 | -0.4 [-5.6, 4.9] | 14.3 | -8.9 | 1.00 | 1.00 | inconclusive |

Crop exclusion uses retention at the level's own scale (>= 0.9 of violation support kept; `all_scales` key of `retention_full.json`): n = 134 / 120 / 112. (The frozen driver could not read that key; the new script does.)

Monotone with strength (dAcc non-increasing and flip non-decreasing): noise, blur, jpeg, brightness-flip yes; brightness dAcc no (noise level of +/-2 pp); zoom no (neither; crop is the strongest edit by SSIM at every level and is cut by retention exclusion, a different pair subset per level). Take-aways, descriptive only because f0 >= 10% makes M1 H1 descriptive: noise breaks verdicts already at the lowest level (SSIM 0.95; flip - f0 = +11.7 pp); blur and JPEG show a dose-dependent break (blur from mid, JPEG only at the high q = 3 level); brightness and zoom do not clearly move accuracy at any level. Flip rates at low/mid for brightness (7.0/9.6%) are below the 21.5% floor, i.e. the floor, not the edit, sets the flips.

## Variants and the Holm family

- Strict (`<`) and exact-ties give identical numbers (no exact ties): dAcc pp noise -18.1/-20.0/-20.6, blur -3.3/-10.6/-14.4, jpeg +5.6/+1.1/-9.4, brightness -0.9/+0.9/-1.7, zoom +3.0/-2.5/-0.9; f0 = 15.6%. Labels differ only for jpeg mid (invariant -> inconclusive).
- Prereg says "Holm over all 21". With 5 graded edits x 3 strengths the family has 15 cells (30 p-values with the flip test, as in Holm-14). 21 would need 7 edits x 3 strengths, but hflip and fps_halve have one strength. I used Holm-30 as primary for A3 and also stored a conservative Holm over 42 slots (`holm42_*` keys; 12 phantom p = 1). No cell changes Holm significance under the 42-slot version (checked). Please confirm which family the paper should quote.
- High-strength cells here are Holm-adjusted within the 30-family, so their adjusted p differ from the confirmatory Holm-14 in `h1_M1.json` (e.g. jpeg-high flip: 0.332 vs 0.153). The confirmatory table is unchanged.

## Scope gap (not dropped; cost estimates)

Unit costs: measured M1 half-condition (180 videos, feats stored) = 582.6 s = 0.162 h (`P4_M1_ipdev_base_ref-ref_s1`, 3.24 s/video); projection basis 2.54 s/video = 0.127 h. M1 full condition measured 0.32 h. M2 = 5.22 s/video projected (x1.27 if the same projection error applies).

| Gap | Runs | GPU-h (2 T4) |
|---|---|---|
| M1 H2 spec low + high (A3 proper): lighting_global 6, lighting_local 6, jolt_base 6, zoom_base 2 | 20 half | 2.5 (projection) to 3.2 (measured) |
| M1 H2 spec mid (confirmatory H2, not A3, for completeness): lighting_global 3 + lighting_local 3 + jolt_base 3 + zoom_base 1 = 10 runs | 10 half | 1.3 to 1.6 |
| (total M1 spec grid = 30 half runs; lead's DECISIONS estimate for the whole h2_spec incl. M0r extras and overhead is ~10 h) | 30 half | 3.8 to 4.9 |
| M2 dose-response tier 3 (`m2_dose_inv_*`: 18 full runs brightness/noise 6+6, blur/jpeg/zoom 2 each) | 18 full | 9.4 (projected) to 11.9 |
| M2 dose-response tier 3 (`m2_dose_spec_*`: 20 half runs) | 20 half | 5.2 to 6.6 |
| M2 dose total | 38 | 14.6 to 18.6 |

Kaggle quota per RUNS.md: 1.05 h left until the Oct 10 00:00 IST reset (then +30 h). M2 tier 3 is the lowest-priority group (prereg s8: after M1 confirmatory, M2 confirmatory); M2 tier 2 (7 invariance edits, dither, H2 mid, controls) is also unrun and is a larger prerequisite (about 25.8 h per GPU_PROJECTION).

---

# A3 specificity dose-response, M1 (secondary; added 2026-10-10 after h2_spec_a/b landed)

The earlier "never ran" gap above is closed: `h2_spec_a` (lighting_global, lighting_local) and `h2_spec_b` (jolt_base, zoom_base) now hold low/mid/high for all four types (seeds 1-3 for the seeded types, zoom_base seed 1) plus `base_ref`. Script `scripts/run_dose_spec.py` (new) calls the frozen `h2_stage` (scripts/run_analysis.py, unmodified) once per level pooled over the four types and once per (type, level) cell (the type tuple the stage loops over is restricted inside the process). Same definitions as the confirmatory H2 (event-aligned max, own tau 2e-4 x median clean score, tie-half, seed-mean AUROC A, scene-cluster bootstrap stratified by block, 10,000 draws, seed 20261015, matches `kaggle/h2_spec_a/matches.json`). Strengths 0.5x / 1x / 2x of the matched strength. Outputs `results/analysis/h2/dose/dose_spec_M1{,_strict,_exactties}.json` (collated), per-cell stage outputs under `h2/dose/<variant>/cells/`. Sanity: the mid level reproduces `h2.json` (A 0.546 [0.501, 0.591], D_1 +0.211, D_2 +0.166; strict 0.540).

Holm convention: the H1 dose family is 15 cells x 2 tests = Holm-30. The analogue here is 12 (type, level) cells x 2 contrasts (D_1 vs B1, D_2 vs B2) = **Holm-24**; the pooled-level contrasts are also Holm-adjusted over 6 (3 levels x 2). Holm-30 itself is not reproducible for this family (12 cells). Per-cell p-values are the frozen one-sided bootstrap p (floor 1e-4), so every adjusted p is >= 0.0024.

Pooled over the four types (tie-half):
| level | A [95% CI] | lighting_global | lighting_local | jolt_base | zoom_base | A_B1 | A_B2 | D_1 [CI] | D_2 [CI] | Holm-6 p (D_1, D_2) | A0 | outcome |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| low (0.5x) | 0.594 [0.546, 0.642] | 0.662 | 0.524 | 0.607 | 0.582 | 0.375 | 0.430 | +0.219 [0.165, 0.274] | +0.164 [0.109, 0.218] | 0.001, 0.001 | 0.722 | Detection-limited |
| mid (1x) | 0.546 [0.501, 0.591] | 0.622 | 0.480 | 0.553 | 0.528 | 0.335 | 0.379 | +0.211 [0.161, 0.262] | +0.166 [0.117, 0.216] | 0.001, 0.001 | 0.722 | Detection-limited |
| high (2x) | 0.501 [0.458, 0.544] | 0.555 | 0.459 | 0.501 | 0.487 | 0.289 | 0.324 | +0.212 [0.167, 0.258] | +0.177 [0.132, 0.221] | 0.001, 0.001 | 0.722 | Detection-limited |
Strict (`<`, tau 0): A 0.586 / 0.540 / 0.496; exact-ties: 0.594 / 0.545 / 0.500 (same per-type ordering). Foil accuracy (tie-half) 0.653 / 0.605 / 0.557.

Per (type, level) cell, tie-half (A with 95% CI; D_1, D_2 vs the baselines; all Holm-24 adjusted p = 0.0024 in both contrasts):
| type | low A [CI] | mid A [CI] | high A [CI] | D_1 low / mid / high | D_2 low / mid / high |
|---|---|---|---|---|---|
| lighting_global | 0.662 [0.606, 0.719] | 0.622 [0.569, 0.675] | 0.555 [0.508, 0.604] | +.240 / +.260 / +.278 | +.192 / +.228 / +.249 |
| lighting_local | 0.524 [0.475, 0.576] | 0.480 [0.431, 0.531] | 0.459 [0.410, 0.509] | +.211 / +.207 / +.227 | +.158 / +.164 / +.199 |
| jolt_base | 0.607 [0.557, 0.658] | 0.553 [0.506, 0.602] | 0.501 [0.456, 0.547] | +.217 / +.181 / +.147 | +.154 / +.123 / +.102 |
| zoom_base | 0.582 [0.532, 0.632] | 0.528 [0.479, 0.578] | 0.487 [0.440, 0.533] | +.210 / +.194 / +.195 | +.151 / +.150 / +.157 |
Observation (no interpretation): A decreases monotonically low > mid > high in the pooled score and in each of the four types (so the `monotone_A_with_strength` field in the JSON, which tests non-decreasing A, is false by construction); the baselines B1 and B2 also fall with strength. No cell reaches 0.65 except lighting_global at low (0.662) and none reaches 0.80. Caveats carried over: lighting_global match target missed at mid (and 84 of 180 of its abrupt effects are inside the tie band); the dose levels are scalings of the mid-matched strength, so the achieved pixel-magnitude ratios at low/high are not separately verified.

---

# A3 dose-response, M2 (V-JEPA 2; DESCRIPTIVE, added 2026-10-10 after `m2_dose_inv_s1_a` and `m2_dose_spec_s1_a` landed)

M2 is H1-ineligible (clean 60.8% < 80%, f0 24.6% > 10%), so every H1 row is descriptive, and the H2 rows follow the descriptive M2 H2 convention. New script `scripts/run_dose_m2.py` (imports the frozen driver, the frozen statistics, `run_dose.py` and `run_dose_spec.py::one`; nothing frozen edited). Meta check first, inside the script: ok, 53 runs, no mismatch, no bypass (`results/analysis/m2/dose/meta_check.json`). Definitions as in the M1 dose analyses; M2 clean reference = `clean-mi0`; dither floor from the three M2 dither seeds. Outputs: `results/analysis/m2/dose/dose_M2{,_strict,_exactties}_{s1,asrun}.json` (H1) and `dose_spec_M2{,_strict,_exactties}.json` (H2), per-cell stage files under `m2/dose/spec/<variant>/cells/`.

**Seeds.** Low and mid strengths exist for seed 1 only. Variant `s1` (primary dose reading) uses seed 1 for every cell, so levels are comparable. Variant `asrun` uses seeds 1-3 for brightness-high and noise-high (as in `h1_M2.json`; its high rows reproduce `h1_M2.json` to the digit). H2 dose is seed 1 for every type and level (inside this process `RA.SEEDED` is emptied so the frozen `h2_stage` loads seed 1 only); the seed-1 mid pooled A (0.449) matches the 3-seed mid in `h2.json`.

**Holm families.** H1: only 11 cells exist (brightness, noise, blur x low/mid/high; jpeg-high; zoom-high), so Holm over **22** p-values (11 dAcc + 11 flip-vs-floor), the analogue of the M1 Holm-30. H2: 12 (type, level) cells x 2 contrasts = **Holm-24**, and pooled-level Holm-6, as for M1.

## H1 dose, M2 (tie-half, seed 1 matched; dAcc in pp with 95% CI; flip rate; excess = flip - f0, f0 = 24.6%; Holm-22 adjusted)
| cell | n | dAcc pp [CI] | flip | flip - f0 pp | Holm p dAcc | Holm p flip | label |
|---|---|---|---|---|---|---|---|
| brightness low | 180 | +1.4 [-1.1, +4.2] | 11.7% | -13.0 | 1.000 | 1.000 | invariant |
| brightness mid | 180 | +2.8 [-0.8, +6.4] | 16.1% | -8.5 | 1.000 | 1.000 | invariant |
| brightness high | 180 | -0.6 [-4.4, +3.6] | 15.0% | -9.6 | 1.000 | 1.000 | invariant |
| noise low | 180 | -4.4 [-10.3, +1.4] | 26.1% | +1.5 | 1.000 | 1.000 | inconclusive |
| noise mid | 180 | -8.1 [-13.9, -2.2] | 30.0% | +5.4 | 0.096 | 0.245 | inconclusive |
| noise high | 180 | -7.8 [-13.1, -2.5] | 25.6% | +0.9 | 0.096 | 1.000 | inconclusive |
| blur low | 180 | +15.8 [+10.0, +21.9] | 35.6% | +10.9 | 0.000 | 0.065 | inconclusive |
| blur mid | 180 | +18.6 [+13.1, +24.4] | 34.4% | +9.8 | 0.000 | 0.096 | inconclusive |
| blur high | 180 | +12.8 [+6.4, +19.4] | 42.2% | +17.6 | 0.007 | 0.000 | violated |
| jpeg high | 180 | -1.7 [-7.8, +4.7] | 40.6% | +15.9 | 1.000 | 0.000 | violated (flip route) |
| zoom high | 112 | +7.1 [+1.8, +12.7] | 25.0% | -5.7 | 0.156 | 1.000 | invariant |
`asrun` differs only for brightness-high (-0.4 [-3.1, +2.5], flip 15.4%) and noise-high (-6.4 [-11.6, -1.1], flip 28.3%, Holm dAcc 0.226, Holm flip 0.388, inconclusive). Strict (`<`, tau 0, f0 17.4%): labels change at brightness-high (invariant -> inconclusive), noise-mid (-> violated via the flip test, Holm 0.043), blur-low (-> violated, Holm flip 0.007) and zoom-high (-> inconclusive); dAcc within about 1 pp of tie-half. Exact-ties file is stored (`dose_M2_exactties_*`).
Observation, no interpretation: dAcc is not monotone in strength for any of the three three-level edits (brightness +1.4/+2.8/-0.6; noise -4.4/-8.1/-7.8; blur +15.8/+18.6/+12.8), and the flip rate is also non-monotone for all three (noise 26.1/30.0/25.6; blur 35.6/34.4/42.2; brightness 11.7/16.1/15.0). Blur dAcc is large and positive at every strength (the corrupted-pair accuracy is higher than clean).

## H2 spec dose, M2 (event-aligned max, tie-half, seed 1; strengths 0.5x / 1x / 2x of the matched strength)
Pooled over the four types:
| level | A [95% CI] | lighting_global | lighting_local | jolt_base | zoom_base | A_B1 | A_B2 | D_1 | D_2 | Holm-6 p (D_1, D_2) | A0 | foil |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| low | 0.483 [0.434, 0.533] | 0.580 | 0.412 | 0.480 | 0.460 | 0.366 | 0.429 | +0.117 | +0.054 | 0.0006, 0.024 | 0.600 | 0.548 |
| mid | 0.449 [0.403, 0.497] | 0.551 | 0.357 | 0.447 | 0.442 | 0.324 | 0.375 | +0.125 | +0.074 | 0.0006, 0.006 | 0.600 | 0.515 |
| high | 0.420 [0.375, 0.469] | 0.534 | 0.326 | 0.416 | 0.406 | 0.276 | 0.317 | +0.145 | +0.103 | 0.0006, 0.0006 | 0.600 | 0.461 |
Driver outcome "Detection-limited (not specific / partial)" at all three levels (A0 = 0.600 < 0.85). Strict A 0.468 / 0.438 / 0.415, exact-ties 0.481 / 0.448 / 0.422.

Per (type, level), tie-half (A [CI]; D_2 = A_M2 - A_B2 with Holm-24 p; D_1 significant at all 12 cells, Holm-24 p 0.0024 except lighting_local low 0.010, mid 0.046, high 0.034):
| type | low A | mid A | high A | D_1 low / mid / high | D_2 low / mid / high | Holm-24 p of D_2 low / mid / high |
|---|---|---|---|---|---|---|
| lighting_global | 0.580 [0.523, 0.637] | 0.551 [0.492, 0.610] | 0.534 [0.475, 0.594] | +.159 / +.191 / +.259 | +.110 / +.158 / +.229 | 0.003 / 0.002 / 0.002 |
| lighting_local | 0.412 [0.351, 0.475] | 0.357 [0.295, 0.422] | 0.326 [0.265, 0.390] | +.099 / +.085 / +.094 | +.047 / +.041 / +.066 | 0.58 / 0.58 / 0.145 |
| jolt_base | 0.480 [0.433, 0.528] | 0.447 [0.400, 0.493] | 0.416 [0.372, 0.461] | +.100 / +.091 / +.090 | +.026 / +.023 / +.032 | 0.58 / 0.58 / 0.58 |
| zoom_base | 0.460 [0.412, 0.509] | 0.442 [0.398, 0.484] | 0.406 [0.361, 0.450] | +.108 / +.133 / +.136 | +.032 / +.073 / +.085 | 0.58 / 0.042 / 0.010 |
Observation: A decreases monotonically low > mid > high pooled and in each type (as for M1; the baselines B1, B2 fall faster, so D_1 and D_2 grow with strength). No cell reaches 0.65 (maximum: lighting_global low, 0.580); every cell except lighting_global is below 0.5, and lighting_global stays above 0.5 at all three levels. Caveat carried over: the lighting_global match target was missed at mid (89 of 180 abrupt effects inside the tie band), and low/high are scalings of the mid-matched strength whose achieved pixel-magnitude ratios were not separately verified. The Holm-24 p of D_1 and D_2 are significant mostly because the baselines are below 0.5.

## Cells that do not exist (scope gap, not dropped)
| Gap | Runs | GPU-h (2 T4; M2 5.22 s/video projected, x1.27 if the projection error repeats) |
|---|---|---|
| `m2_dose_inv_s1_b`: jpeg low/mid, zoom low/mid (4 cells, seed 1) | 4 full | 2.1 to 2.6 |
| seed 2-3 groups for the low/mid seeded edits: brightness, noise x low/mid x seeds 2-3 | 8 full | 4.2 to 5.3 |
| seed 2-3 for H2 spec low/high: lighting_global, lighting_local, jolt_base x low/high x seeds 2-3 | 12 half | 3.1 to 4.0 |
| Total | 24 | 9.4 to 11.9 |
Consequences: the H1 dose family has 11 of the 15 M1-analogue cells (Holm-22 instead of Holm-30; jpeg and zoom have a high-strength point only, so no dose curve for them); low/mid H1 cells and all H2 dose cells are single-seed (the seed-averaged tie-aware flip rate and AUROC are therefore noisier than the M1 equivalents; no seed-to-seed estimate at those cells).
