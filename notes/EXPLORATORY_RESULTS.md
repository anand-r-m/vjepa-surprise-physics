# EXPLORATORY results (post-freeze; not pre-registered; M1; frozen functions, nothing tuned)

Script `scripts/run_exploratory.py` (new; frozen driver and `vjepa_study.analysis.prereg` unmodified). Outputs under `results/analysis/exploratory/` (file names carry EXPLORATORY; `ip2main/` is descriptive per prereg s8). n_boot 10000, seed 20261015. Meta check (P4 M1 + M0r runs) ok. Runs symlinked from `results/raw/{expl_onset_spec,expl_halve_hold,ip2main_clean_m1,p4_clean_m1,h1_inv_b}`.

## 1. EXPLORATORY onset-aligned specificity (`onset_spec/EXPLORATORY_h2_onset_M1*.json`, `EXPLORATORY_onset_ties*.json`)
Frozen `h2_stage` with `kaggle/expl_onset_spec/matches.json` (180 data-derived onsets, 0 fallback, 0 late; 60 transient). Edited runs `EXPL_M1_ipdev_onset-<type>-mid_s<seed>`; clean and `base_ref` references are the frozen P4 runs. tau (event-aligned max): M1 1.088e-4, B1 1.467e-6, B2 2.920e-6, B3 4.528e-5.
| score | A [95% CI] | lighting_global | lighting_local | jolt_base | zoom_base | A0 [CI] |
|---|---|---|---|---|---|---|
| M1 | 0.392 [0.354, 0.428] | 0.390 | 0.460 | 0.400 | 0.317 | 0.722 [0.650, 0.792] |
| B1 | 0.327 [0.291, 0.361] | 0.308 | 0.278 | 0.378 | 0.345 | 0.583 [0.544, 0.625] |
| B2 | 0.381 [0.351, 0.407] | 0.353 | 0.351 | 0.433 | 0.386 | 0.661 [0.614, 0.711] |
| B3 (descr.) | 0.360 [0.315, 0.407] | 0.271 | 0.687 | 0.244 | 0.238 | 0.639 [0.572, 0.706] |

| contrast | D [95% CI] | p | Holm-2 p |
|---|---|---|---|
| D_1 = A_M1 - A_B1 | +0.064 [0.023, 0.108] | 0.0009 | 0.0018 |
| D_2 = A_M1 - A_B2 | +0.011 [-0.027, 0.051] | 0.279 | 0.279 |
Confirmatory (random-window) values for comparison: A 0.546, D_1 +0.211, D_2 +0.166. Rule outputs (prereg thresholds applied as written, labelled exploratory): A <= 0.65 and A0 = 0.722 < 0.85 -> "Detection-limited (not specific / partial)"; upper CI of A = 0.428 < 0.50, so the "Reversed" sub-label applies (the driver's reversed field is False because `h2_stage` does not pass `A_hi`). Seed AUROCs 0.393 / 0.392 / 0.390. Foil accuracy 0.367. Match target for lighting_global still missed (in-band 80%).

With / without lighting_global (the type with the missed match target):
| set | A [CI] | per-type | D_1 [CI] (Holm-2 p) | D_2 [CI] (Holm-2 p) |
|---|---|---|---|---|
| all four types | 0.392 [0.354, 0.428] | .390 .460 .400 .317 | +0.064 [0.023, 0.108] (0.0018) | +0.011 [-0.027, 0.051] (0.279) |
| without lighting_global | 0.392 [0.357, 0.426] | - .460 .400 .317 | +0.059 [0.018, 0.101] (0.0042) | +0.002 [-0.033, 0.040] (0.437) |
Variants: strict (tau 0, ties 0) A 0.391 [0.353, 0.427], D_1 +0.075 (Holm 0.0006), D_2 +0.026 [-0.014, 0.068] (0.100), A0 0.694; exact-ties A 0.392 [0.354, 0.428], D_1 +0.063 (0.0026), D_2 +0.010 (0.288), A0 0.717. Without lighting_global: strict A 0.391, exact-ties A 0.392. Same rule outcome in all.
Descriptive strata (primary): by block M1 A O1 0.427, O2 0.392, O3 0.359 (B2 0.367, 0.393, 0.384); onset proxy abrupt (n 162) M1 0.391 vs B2 0.385, gradual/occluded (n 18) M1 0.385 vs B2 0.344. Median target-feature distance edit vs ref: lighting_global 0.028, lighting_local 0.021, jolt_base 0.033, zoom_base 0.036 (confirmatory: 0.005, 0.018, 0.011, 0.016).

Tie counts (primary tau, 180 pairs): clean event-aligned |dv| <= tau: M1 10 (8 exactly 0), B1 34, B2 36, B3 10. Abrupt-edit effect <= tau per seed: lighting_global 20/20/20, lighting_local 13/13/13, jolt_base 12/12/17, zoom_base 8. Fraction of 180 x 180 AUROC comparisons in the tie band: lighting_global 1.4%, lighting_local 1.4%, jolt_base 1.2/1.1/1.2%, zoom_base 1.0% (confirmatory: 6.3, 2.2, 2.5, 2.0%). At tau 0: clean ties 8 / 28 / 32 / 8, abrupt ties lg 6, ll 8, jb 8, zb 4.

## 2. EXPLORATORY halve_hold vs clean skip-2 reference (`halve_hold/EXPLORATORY_halve_hold_M1*.json`)
Run `EXPL_M1_ipdev_halve_hold-high_s1` vs `P4_M1_ipdev_clean_s1` (same 17 windows, pairable), frozen H1 functions (tau from the clean run, seed-1 deterministic edit), floor f0 from the three dither seeds. One edit only; the Holm fields are over 2 p-values, not a pre-registered family. S is not identical to the clean S (max abs diff 0.0438), unlike the pre-registered fps_halve.
| variant | clean acc -> halve_hold acc | dAcc pp [95% CI] | flip rate [CI] | f0 | flip - f0 pp [CI] | p dacc / p flip (cluster) | flipped pairs | ties halve_hold / clean / dither s1-3 | rule label |
|---|---|---|---|---|---|---|---|---|---|
| tie-half (tau 1.057e-4) | 80.8 -> 82.8% | +1.9 [-3.3, +7.2] | 20.0% [14.4, 25.6] | 21.5% | -1.5 [-8.1, +5.2] | 0.525 / 0.680 | 36 (18 up, 18 down) | 10 / 7 / 19, 17, 16 | inconclusive |
| strict = exact-ties (tau 0) | 81.1 -> 82.8% | +1.7 [-3.9, +7.2] | 15.0% [10.6, 20.0] | 15.6% | -0.6 [-6.3, +5.0] | 0.631 / 0.595 | 27 (15 up, 12 down) | 0 / 0 / 0, 0, 0 | inconclusive |
Sign test (exact): tie-half p 1.0 (18 up / 18 down), strict p 0.70. The flip rate is within the dither floor. Caveat from EXPLORATORY_GROUPS.md: with tubelet size 2 and even window starts every tubelet is a static pair (phase-specific); deterministic, one seed.

## 3. IntPhys 2 Main, M1 clean (descriptive; prereg s8) (`ip2main/IP2MAIN_M1_clean_descriptive.json`)
Run `P4_M1_ip2main_clean_s1` (1012 videos, 506 pairs, fp16). tau = 2e-4 x median per-video score of the Main run itself (mean aggregation 1.115e-4; max 1.149e-4). 8 videos share a name with Debug (4 pairs contain one; the pairs are dropped for "without"; tau kept from the full run). CIs: Wilson and scene-cluster bootstrap (block-stratified).
| score (mean agg) | set | n pairs | acc tie-half | strict | ties | Wilson 95% | cluster-boot 95% |
|---|---|---|---|---|---|---|---|
| M1 | all | 506 | 47.6% | 47.8% | 30 | [43.3, 52.0] | [43.7, 51.6] |
| M1 | without the 8 Debug-name videos | 502 | 47.6% | 47.8% | 30 | [43.3, 52.0] | [43.5, 51.6] |
| M1 (max agg) | all / without | 506 / 502 | 50.5% / 50.5% | 50.6% / 50.6% | 11 / 11 | [46.2, 54.8] / [46.1, 54.9] | |
| B1 | all | 506 | 51.2% | 51.2% | 8 | [46.8, 55.5] | |
| B2 | all | 506 | 51.9% | 52.0% | 19 | [47.5, 56.2] | |
| B3 | all | 506 | 46.6% | 46.6% | 10 | [42.3, 51.0] | |
By block (M1, mean agg, tie-half / n pairs / ties), all: continuity 46.7% (120, 8), immutability 42.1% (120, 7), permanence 49.6% (120, 11), solidity 51.4% (146, 4); without the overlap: identical except solidity 51.4% (142, 4). Max agg by block (all): continuity 53.3%, immutability 48.3%, permanence 45.0%, solidity 54.5%. Baselines by block are in the JSON.

## Anomalies / notes
1. Onset-aligned A (0.392) is lower than the random-window A (0.546), and its D_2 is no longer distinguishable from 0; B1 and B2 stay near 0.33 / 0.38. M1's A0 is unchanged at 0.722.
2. B3 per-type AUROC for lighting_local is 0.687 versus 0.24-0.27 for the other three types (descriptive baseline).
3. M1 on IntPhys 2 Main is at chance in the mean aggregation (47.6%), below its IntPhys-dev accuracy (80.8%); Main pairs are not pixel-matched.
