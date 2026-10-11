# P6 independent recompute (verifier)

Written before any analysis output was opened. Code: verify/p6_recompute.py, p6_pixels.py, p6_events.py, p6_retention.py (no src/ imports). Bootstrap: numpy default_rng seed 20261015, 10,000 draws, 30 scenes per block with replacement, all quantities on common draws.

## 1. Clean accuracy (mean aggregation, 180 pairs, tau = 2e-4 x median of 360 per-video mean scores)

| run | tau | tie-half | strict | exact-tie (tau=0) | ties at tau | tie-half credits |
|---|---|---|---|---|---|---|
| P4_M1_fp16 | 1.0570e-04 | 0.8083 | 0.8111 | 0.8111 | 7 | 145.5 |
| P2_M1_fp32 | 1.0571e-04 | 0.8167 | 0.8056 | 0.8056 | 8 | 147.0 |
| B1_fp16run | 7.229e-07 | 0.5806 | 0.5722 | | 7 | |
| B2_fp16run | 1.356e-06 | 0.7611 | 0.7611 | | 0 | |
| B3_fp16run | 4.253e-05 | 0.4528 | 0.4500 | | 9 | |
| P4_M1_skip4 | 1.083e-04 | 0.8222 | 0.8222 | | 10 | |

Pair/label structure derived from pixels agrees with the stored pair_id/label for all 180 pairs (every pair has one possible and one impossible member; prefix-sharing partner unique, no divergence ties).

## 2. H1 (high strength; fp16 clean reference; skip-4 clean reference for fps_halve)

Reading: y averaged over seeds per pair; flip = mean over seeds of 1[class changed]; tau = clean fp16 mean-aggregation tau for all edited runs (alt for fps_halve: skip-4 clean tau). f0 = dither flip rate (3 seeds) over the same retained pairs. Zoom retention: pairs whose violation support (|v-p|>8/255, channel-mean, frames [t_on,t_off), fallback window [48,100)) retains <90% inside the central 0.7 crop are excluded. Stored-match retention (matches.json) excludes 68 pairs; mine 70 (cm), 74 (max-channel); alt keep sets in JSON (h1 -> alt_keep=...).

| edit | n pairs | dAcc (pp) | dAcc 95% CI | p cluster (2-sided) | Holm-14 | p sign | flip | f0 | flip-f0 | p flip-vs-floor | Holm-14 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| brightness | 180 | -2.41 | [-5.1, 0.3] | 0.0786 | 0.6288 | 0.0660 | 0.1241 | 0.2148 | -9.07 pp | 0.9999 | 1.0000 |
| noise | 180 | -20.56 | [-25.7, -15.3] | 0.0000 | 0.0000 | 0.0000 | 0.3778 | 0.2148 | 16.30 pp | 0.0000 | 0.0000 |
| blur | 180 | -14.44 | [-19.4, -9.4] | 0.0000 | 0.0000 | 0.0000 | 0.3111 | 0.2148 | 9.63 pp | 0.0001 | 0.0010 |
| jpeg | 180 | -10.83 | [-16.4, -5.3] | 0.0000 | 0.0000 | 0.0018 | 0.2833 | 0.2148 | 6.85 pp | 0.0171 | 0.1539 |
| zoom | 110 | -0.45 | [-5.7, 5.0] | 0.9248 | 1.0000 | 1.0000 | 0.1455 | 0.2364 | -9.09 pp | 0.9921 | 1.0000 |
| hflip | 180 | 2.22 | [-2.2, 6.7] | 0.3446 | 1.0000 | 0.4421 | 0.1500 | 0.2148 | -6.48 pp | 0.9782 | 1.0000 |
| fps_halve | 180 | 0.00 | [0.0, 0.0] | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.2148 | -21.48 pp | 1.0000 | 1.0000 |

Dither floor over all 180 pairs: f0 = 0.2148 (dither dAcc -9.54 pp). f0 >= 10% so M1 H1 is descriptive by the prereg rule.
fps_halve edited run is bit-identical to the clean skip-4 run (flip 0, dAcc 0 by construction): True.

Bootstrap p of 0.0000 means no draw of 10,000 crossed; report as < 1e-4.

## 3. H2 (event-aligned max, mid strength, 4 types)

Event times from pixels: tau_D = 0.00784 (2/255 binds); fallback pairs (no D > tau_D) = 178 of 180 (matches stored meta 178), transient = 2, late (t_on>94) = 0. The max over time of the mean-pixel D(t) is below tau_D for 178 pairs, so the t* rule degenerates to the fallback; fallback t_on = 48 (value taken from kaggle/h2_spec_a/matches.json; the prereg says only 'uniform in middle 50% seeded'). tau for H2/H3 (2e-4 x median clean full-clip max): M1 1.088e-04, B1 1.467e-06, B2 2.920e-06.

Readings computed: R1 pixel-derived t_on with fallback 48 (PRIMARY); R1b stored matches.json t_on verbatim; R1c linear-resize D; R1d fallback 50; R2 t* = first frame where the two pair members differ at all (A1.3 wording); R3 full-clip max (no alignment).

| reading | A_M1 | A_B1 | A_B2 | D_1 [95% CI] | p1 | Holm-2 | D_2 [95% CI] | p2 | Holm-2 | A0_M1 | M1 row |
|---|---|---|---|---|---|---|---|---|---|---|---|
| R1_pixel_fb48 | 0.5461 | 0.3352 | 0.3793 | 0.2109 [0.160, 0.264] | 0.00010 | 0.00020 | 0.1668 [0.117, 0.219] | 0.00010 | 0.00020 | 0.7222 | Not specific |
| R1b_stored_matches_t_on | 0.5457 | 0.3352 | 0.3793 | 0.2105 [0.159, 0.263] | 0.00010 | 0.00020 | 0.1664 [0.116, 0.219] | 0.00010 | 0.00020 | 0.7222 | Not specific |
| R1c_pixel_linear_resize_fb48 | 0.5457 | 0.3352 | 0.3793 | 0.2105 [0.159, 0.263] | 0.00010 | 0.00020 | 0.1664 [0.116, 0.219] | 0.00010 | 0.00020 | 0.7222 | Not specific |
| R1d_pixel_fb50 | 0.5461 | 0.3352 | 0.3793 | 0.2109 [0.160, 0.264] | 0.00010 | 0.00020 | 0.1668 [0.117, 0.219] | 0.00010 | 0.00020 | 0.7222 | Not specific |
| R2_pair_first_divergence | 0.5836 | 0.4127 | 0.4822 | 0.1710 [0.118, 0.226] | 0.00010 | 0.00020 | 0.1014 [0.047, 0.155] | 0.00020 | 0.00020 | 0.7222 | Not specific |
| R3_fullclip_max | 0.5529 | 0.3945 | 0.4709 | 0.1584 [0.110, 0.209] | 0.00010 | 0.00020 | 0.0820 [0.036, 0.128] | 0.00010 | 0.00020 | 0.7250 | Not specific |

Per-type AUROC, primary reading:

| model | lighting_global | lighting_local | jolt_base | zoom_base |
|---|---|---|---|---|
| M1 | 0.6217 | 0.4802 | 0.5531 | 0.5296 |
| B1 | 0.3618 | 0.2731 | 0.3719 | 0.3340 |
| B2 | 0.3937 | 0.3161 | 0.4295 | 0.3781 |

D_k = A_M1 - A_Bk is POSITIVE because the baselines have AUROC < 0.5 (their Delta_abrupt exceeds Delta_viol): M1 beats both baselines under Holm-2, but A_M1 is about 0.55 (Not specific, all four types < 0.65). A0 (clean pairwise accuracy under the H2 aggregation): M1 0.7222 (< 0.85), so the prereg outcome is "Detection-limited (not specific)". Pooling the types into one AUROC gives the same value as the mean of per-type AUROCs (equal n per type), so the A reading is not ambiguous in value.

A0 detail: M1 A0=0.7222 (ties 22, strict 0.6667, CI [0.664,0.781]); B1 A0=0.5556 (ties 38, strict 0.4556, CI [0.522,0.592]); B2 A0=0.6000 (ties 48, strict 0.5056, CI [0.558,0.644]).

## 4. H3 (full-clip max; tau as H2; 180 possible videos)

| quantity | detection | 95% cluster CI | ties | note |
|---|---|---|---|---|
| vflip_a_ref_p | 0.2111 | [0.147, 0.281] | 2 | |
| hflip_ref_p | 0.3861 | [0.311, 0.464] | 7 | |
| vflip_b_ref_hflip | 0.2583 | [0.186, 0.333] | 3 | |
| reversal_ref_p | 0.6083 | [0.517, 0.694] | 3 | |
| M0r_vflip | 0.8778 | [0.822, 0.931] | 16 | |
| M0r_reversal | 0.5167 | [0.500, 0.539] | 172 | |
| M1_minus_M0r_vflip | -0.6667 | [-0.761, -0.567] | | difference |
| M1_minus_M0r_reversal | 0.0917 | [-0.003, 0.183] | | difference |
| pairwise_acc_vflip | tie-half 0.8389 / strict 0.8222 | | | pairwise acc, mean aggregation, tau_mean |
| pairwise_acc_reversal | tie-half 0.7472 / strict 0.7333 | | | pairwise acc, mean aggregation, tau_mean |
| pairwise_acc_hflip | tie-half 0.8306 / strict 0.8389 | | | pairwise acc, mean aggregation, tau_mean |

G2 (vflip detection (a) >= 0.80): 0.2111 -> pass = False. M0r references use the init0 clean run with its own tau (M0r clean full-clip max median x 2e-4 = 1.704e-04).

## 5. Ties and fallbacks

- M1 clean ties at tau: fp16 7, fp32 8; exact ties 0 in both.
- H1 edited runs (ties at tau_mean, per seed): {'brightness': [10, 6, 9], 'noise': [37, 43, 33], 'blur': [29], 'jpeg': [14], 'zoom': [4], 'hflip': [7], 'dither': [19, 17, 16]}.
- No-event fallback pairs: 178 (mine) / 178 (matches.json meta). Transient pairs: 2 (O3/17/p0, p1: my t_on 55 / t_off 59 vs stored 54 / 59; the one-frame difference moves the first window index from 6 to 7 for those two pairs and changes A by < 0.001).
- H2 fraction of tie cells (|dv - da| <= tau) per model: {'M1': 0.032608024691358026, 'B1': 0.0408641975308642, 'B2': 0.05648148148148148}.

## 6. Ambiguities and readings
- t* fallback: prereg says uniform in the middle 50% (seeded); the seed/value is not in the prereg, so 48 from matches.json is used; 50 and the pair first-divergence frame (R2) and no alignment (R3) are reported; the conclusion (A about 0.55-0.58, Not specific) does not change.
- Baseline score per window: min over C of stored B1/B2 arrays (same rule as M1); baselines use their own tau (2e-4 x median clean full-clip max of that baseline).
- Strict accuracy: pair counted correct iff imp > pos (ties wrong). Exact-tie: tau = 0.
- Zoom retention uses channel-mean |v-p| > 8/255; max-channel and stored values give 106 and 112 retained pairs; alt rows in JSON.
- fps_halve tau: clean fp16 skip-2 tau (primary) vs skip-4 clean tau: identical result (flip 0).
- Bootstrap p for flip-vs-floor is P*[(flip-f0)* <= 0]; zero means < 1e-4. H2 p floored at 1/10001.
