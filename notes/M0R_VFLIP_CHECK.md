# EXPLORATORY: does M0r shift systematically under vertical flip? (post-freeze, no GPU)

Script `scripts/m0r_vflip_check.py` -> `results/analysis/m0r_vflip_check.json`. Existing raw arrays only: edited runs in `results/raw/g2_controls/results/`, clean references in `results/raw/p4_clean_m1/results/`. Paired per possible video (180), difference = S(edit) - S(clean), per-video score = min over C then full-clip max (H3 aggregation) or mean, and per window (min over C). tau = 2e-4 x median per-video score of the model's own 360 clean videos (same as the frozen H3). Only M0r init 0 has an edited run (the g2 group ran vflip and reversal for init 0 only), so "all three inits" is not available for the edit; the clean M0r inits 1 and 2 have no vflip partner.

## Result (full-clip max, n = 180)
| model / edit | mean S clean | mean shift | shift SD | frac shift > 0 | frac shift < 0 | frac within tau | mean/SD | detection (tie-half) |
|---|---|---|---|---|---|---|---|---|
| M0r init0, vflip | 0.85183 | +8.6e-4 (+0.10%) | 7.2e-4 | **0.878** | 0.122 | 0.089 | +1.20 | 0.878 |
| M0r init0, reversal (control) | 0.85183 | +1.2e-5 | 7.7e-5 | 0.533 | 0.467 | 0.956 | +0.15 | 0.517 |
| M1, vflip | 0.54129 | -3.56e-3 (-0.66%) | 4.8e-3 | 0.206 | **0.794** | 0.011 | -0.75 | 0.211 |
| M1, hflip | 0.54129 | -8.6e-4 | 2.9e-3 | 0.383 | 0.617 | 0.039 | -0.29 | 0.386 |
| M1, reversal | 0.54129 | +1.4e-3 | 4.1e-3 | 0.600 | 0.400 | 0.017 | +0.34 | 0.608 |

tau (max) is 1.70e-4 for M0r and 1.09e-4 for M1. Mean aggregation gives the same picture (M0r vflip 0.883 positive, detection 0.864; M1 vflip 0.867 negative, detection 0.139).

Per window (min over C): the M0r vflip-minus-clean mean is positive in 17 of 17 windows (overall 88.1% of the 180 x 17 cells positive; mean of window means +9.0e-4). M1 vflip is negative in 17 of 17 windows (19.1% of cells positive; mean -4.4e-3). The window of the maximum moves later for the edited clip in both models (M0r mean argmax window 11.05 vs 10.06; M1 7.18 vs 6.83).

## What the data establish
- M0r's vflip detection of 0.88 is a systematic positive shift in surprise, not a tie/noise effect. The shift is +8.6e-4 on average, about 5 x tau and 1.2 shift-SDs from zero, positive in 88% of videos and in every window.
- The fp16-noise explanation (P4_CLEAN_G2 surprise 2, H2_RESULTS) is not supported. The same M0r init, same tau and same aggregation on time reversal give 95.6% of videos inside tau and a 53/47 sign split, i.e. the noise floor of M0r produces detection about 0.5, not 0.88. Noise of the size seen in the reversal control (SD 7.7e-5) cannot make 88% of shifts positive.
- The direction for M0r (up) is opposite to M1 (down, 79% of videos) for the same edit on the same videos. For M1 the shift is a decrease, so the vflip control does not raise M1 surprise; for M0r it raises it slightly.
- The prereg statement "M0r detection about 0.5 by construction" is false for vflip under max aggregation (it holds for reversal).

## What is NOT established
- Why the randomly initialised network scores flipped clips higher. The check supports "an orientation-dependent systematic effect of the untrained features on vertically flipped frames" and nothing more specific; we did not test low-level image statistics (sky/ground gradients, layout, vertical asymmetry of the stimuli), other inits, or hflip for M0r (no run exists).
- That the M0r shift is large in an absolute sense: it is 0.1% of the score. It is systematic and larger than the tie band, which is what moves detection away from 0.5.
- Anything about M1's mechanism for its negative vflip shift.
- Consequence for H3: M1 minus M0r detection (-0.667) compares a down-shift against an up-shift; it is not an interpretable "learned sensitivity" contrast, and vflip is confounded with a systematic low-level effect (critic B4). No frozen result changes.
