# CALIBRATION (IntPhys 2 Debug only; CPU; no model, no dev frames)

Data: 60 Debug videos x 8 evenly spaced frames = 480 frames, centre-cropped to a square and resized to 288x288 (INTER_AREA). Random edits (brightness, noise) averaged over seeds 1-3. Re-run: `python scripts/calibrate_debug.py` (deterministic). Raw: `results/analysis/calibration_debug.json`; registry-unit candidate: `configs/edit_params_candidate.yaml`.
Rules: blur sigma, JPEG quality, noise std: mean SSIM to the original = 0.95 / 0.85 / 0.70 (Gaussian 11x11, sigma 1.5, per channel). Brightness: mean absolute CIELAB L* change = 5 / 10 / 20. Centre crop: scale kept = 0.9 / 0.8 / 0.7 fixed by rule. Brightness = multiplicative gain (1 +- a) with per-channel jitter +-a/2, sign and jitter seed-driven, clipped to [0,255].

## [CAL] final values (paste into the prereg)

| edit | unit | low | mid | high | achieved low / mid / high |
|---|---|---|---|---|---|
| brightness gain a | multiplicative gain 1 +- a (registry `amount`) | 0.0769 | 0.1545 | 0.3397 | mean abs dL* 5.00 / 10.00 / 20.00; SSIM 0.995 / 0.982 / 0.913; clipped fraction 0.004 / 0.021 / 0.179 |
| blur sigma | px at 224 (x288/224 on native 288 frames) | 0.716 | 1.435 | 3.994 | SSIM 0.949 / 0.850 / 0.700 |
| JPEG quality | quality factor (registry `amount` = 100 - quality) | 63 | 14 | 3 | SSIM 0.950 / 0.853 / 0.689 (integer qualities) |
| noise std | [0,1] intensity units (registry = x255) | 0.0094 | 0.0177 | 0.0291 | SSIM 0.950 / 0.850 / 0.700 |
| centre crop | scale kept (registry `amount` = 1 - scale) | 0.9 | 0.8 | 0.7 | SSIM 0.551 / 0.497 / 0.480 (reported only) |

## Final edit_params.yaml hash

`configs/edit_params.yaml` is a byte copy of `configs/edit_params_candidate.yaml` (the placeholder table stays in git history; only the fps_halve unit text and header comment differ from the generated candidate: stride doubling, not frame duplication).
edit_params.yaml sha256: d7e4a9453e5f683ecf726a40f389c779c77c1b55f6b2b9b3155baac407e7c4eb
Bundles are checked against this hash with `python scripts/check_bundle_hash.py` before any push.
