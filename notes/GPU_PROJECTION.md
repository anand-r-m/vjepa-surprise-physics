# GPU PROJECTION (coder, block 3; updated after fp16/fixed-sharding decision and M2 bench)

## Measured unit costs (wall seconds per video on 2 T4s unless stated; T4, full protocol incl. B1/B2/B3 + feature pooling)
| config | s/video | source |
|---|---|---|
| M1 fp16, 2 GPUs, fixed sharding, cudnn.benchmark=False (**default now**) | **2.54** | results/raw/p2_det2/results/P2D2_M1_dev12_fp16_2gpu_A_s1/meta.json |
| M1 fp16, 1 GPU | 5.17 | results/raw/p2_det2/results/P2D2_M1_dev12_fp16_1gpu_A_s1/meta.json |
| M1 fp32, 2 GPUs (p2_clean uses this) | 10.81 | results/raw/p2_bench/results/P2B_M1_ipdev_clean12_fp32_2gpu_s1/meta.json |
| M1 fp32, 1 GPU | 21.01 | .../P2B_M1_ipdev_clean12_fp32_1gpu_s1/meta.json |
| M1 bf16, 1 GPU (T4 lacks native bf16) | 35.74 | .../P2B_M1_ipdev_clean12_bf16_1gpu_s1/meta.json |
| **M2 (official vjepa2 vitl.pt) fp16, 2 GPUs** | **5.22** | results/raw/p2_m2/results/P2M_M2_dev12_fp16_2gpu_s1/meta.json |
M2/M1 cost ratio measured = 2.06x (earlier guess 1.4x was too low). M3: no measurement (no usable checkpoint, see below); keep out of the budget until a checkpoint exists.
Earlier "p1_timing 5.19 s/video" was fp16 on 1 GPU (reconciled in notes/FP16_DETERMINISM.md).

## Formulas
hours = N_videos x s_per_video / 3600. Full condition = 360 videos; half condition = 180 possible videos. Deterministic edits run once (seed aliasing); A1/A2 need no runs. Kernel overhead (pip + 5 GB checkpoint + load) ~ 3-6 min per kernel; assume 12 kernels = 1 h.

## Conditions per latent model (M1 basis; M2 identical list)
Full (360): brightness 3 strengths x 3 seeds = 9, noise 9, blur 3, jpeg 3, zoom 3, hflip 1, fps_halve 1 (doubled stride), dither 3 (seeds), vflip 1, time_reversal 1 -> **34**.
Half (180): lighting_global 9, lighting_local 9, jolt_base 9, zoom_base 3 (deterministic), base_ref 1 -> **31**.
M0r extra (half): spec mid x4 types, base_ref, vflip, time_reversal -> 7. (Clean x3 inits are in P2.)
IntPhys 2 Main (optional, M1 and M2): clean 1012 + 11 half conditions on 506 possible videos = 6578 video-passes.

## Projection (fp16, 2 GPUs, fixed sharding)
| item | hours |
|---|---|
| M1 main (34 full + 31 half) | 12.6 |
| M0r extra | 0.9 |
| M2 main (same list at 5.22 s/video) | 25.8 |
| IntPhys 2 Main, M1 | 4.6 |
| IntPhys 2 Main, M2 | 9.5 |
| kernel overhead (12 kernels) | 1.0 |
| **M1 + M0r + M2 + overhead** | **40.3** |
| + IntPhys 2 Main (M1, M2) | 54.5 |
fp32 equivalents (for reference): M1 main 53.5 h, i.e. 4.3x more; not affordable.

## What fits
- Quota: 22.53 h remaining before P2 (kaggle quota 2026-10-06 17:01 UTC); P2 (5 fp32 full conditions) = 5.4 h + det/bench/M2 side kernels (~1 h). After P2 ~ 17.0 h before the Oct 10 00:00 reset (+30 h at reset; the next reset is outside the sprint). Pool through Oct 12 ~ 47.0 h.
- **Before Oct 10 00:00 (~17 h):** M1 main + M0r + overhead = 14.0 h fits (3.1 h spare); M2 (25.8 h) does not fit in the same window.
- **By Oct 12 (pool ~47 h):** M1 + M0r + M2 + overhead = 40.3 h fits with 6.7 h margin; adding IntPhys 2 Main for both models does not (54.5 h) -- M1-only IntPhys 2 Main (+4.6 h) would just fit. M3: cannot be scheduled until a checkpoint exists; if it is ViT-g it would cost ~3-4x M1 (unmeasured guess).
- Remaining levers if needed: run dose-response (low/high) for M2 on 1 seed only (saves ~5 h region), skip IntPhys 2 Main for M2.

## Actuals
- P2 clean kernel (vjepa-p2-clean, fp32, 2 GPUs, 5 full conditions): `kernel total 19290 s` = 5.36 h (results/raw/p2_clean/results/kernel_log.txt). `kaggle quota` after it: 13.21 h used, **16.79 h remaining** (reset 2026-10-10 00:00).
- Side kernels this block (bench, det, det2, m2): each <= ~20 min.
