# fp16 determinism, sharding and tie tolerance (coder, block 3)

## Reconciliation of precisions
`M1VJEPA` originally defaulted to fp16 autocast (the released config `use_bfloat16: true` is fp16 autocast, `torch.autocast(dtype=float16)`). So the block-2 numbers `P1T_M1_ipdev_clean12_s1` (5.19 s/video, 1 GPU) and `P1_M1_ip2debug_clean_s1` were fp16 runs, not fp32 (the `precision` switch did not exist yet; meta.json of those runs carries no precision field). Confirmed: `P2B ... fp16_1gpu` reproduces the stored P1 timing array with max|dS| = 0.0 (results/raw/p2_bench) and costs 5.28 s/video. fp32 costs 21.0 s/video (1 GPU).
Defaults now: kaggle/common (run_lib, kernel_main) default `precision="fp16"`, sharding is FIXED (video i -> GPU i % n_gpus); fp32 and bf16 remain options. Model classes keep fp32 as constructor default (CPU tests).

## Findings (files: results/raw/p2_det*, p2_bench; 12 dev videos, M1)
1. First 2-GPU fp16 versions were NOT reproducible: same config twice differed by up to 3.96e-4 in S (results/raw/p2_det/results/P2D_M1_dev12_fp16_2gpu_{A,B}_s1), while 1-GPU fp16 was bitwise reproducible (A==B, and equal to the stored block-2 result). fp32 2-GPU was exact vs 1-GPU. Cause: the released `eval.py` sets `torch.backends.cudnn.benchmark = True` (timing-based algorithm autotune; under two concurrent processes-threads the winner varies).
2. Fix: wrappers set `cudnn.benchmark=False`, `cudnn.deterministic=True`, and the kernel sets `CUBLAS_WORKSPACE_CONFIG=:4096:8`. Verified (results/raw/p2_det2/results/P2D2_M1_dev12_fp16_*): 2-GPU A vs B bitwise equal; 1-GPU A vs B bitwise equal; 2-GPU vs 1-GPU bitwise equal (max|dS| = 0.0). Speed 2.54 s/video (2 GPUs), 5.17 s/video (1 GPU). (The benchmark=False result differs from the benchmark=True one by 2.8e-4, i.e. the autotuned algorithms themselves differ at that level.)
3. Note p2_clean (fp32, benchmark=True at push time) is unaffected: fp32 2-GPU matched 1-GPU exactly in p2_bench.

## Tie tolerance evidence (IntPhys 2 Debug, 6 possible videos, not dev; results/raw/p2_det/results/P2D_M1_ip2dbg_*)
Video-level aggregate |change| under a +-1 LSB dither (the invisible-perturbation floor):
| precision | aggregation | median | max |
|---|---|---|---|
| fp16 | mean over windows | 4.9e-4 / 5.3e-4 (seeds 1/2) | 1.4e-3 / 1.5e-3 |
| fp16 | max over windows | 1.0e-3 / 9.7e-4 | 1.7e-3 / 2.7e-3 |
| fp32 | mean | 4.9e-4 / 4.9e-4 | 1.4e-3 / 1.5e-3 |
| fp32 | max | 9.5e-4 / 1.0e-3 | 1.7e-3 / 2.5e-3 |
Window-level max |dS| under dither: 2.3e-2 (both precisions). fp16-vs-fp32 clean difference at video level: <= 6.3e-5 (mean agg), <= 1.06e-4 (max agg). Old nondeterministic 2-GPU jitter: 4.0e-4 per window.
Interpretation: precision (fp16 vs fp32) noise at the video level (~1e-4) is 5-10x smaller than the effect of a visually null +-1 LSB perturbation (~5e-4 to 1e-3). The A1.2 tolerance 1e-4 is therefore tight enough for exact-duplicate detection in a deterministic pipeline (identical inputs give bitwise identical outputs now), but it is at the edge of fp16-vs-fp32 differences and far below any perturbation floor.
Proposal (lead to decide, to be frozen before looking at dev margins): keep ties = exact duplicates, tol 1e-4, valid only because the fp16 pipeline is now bitwise deterministic; do NOT compare fp16 against fp32 runs with that tolerance. Optional more conservative alternative: tol = 5e-4 (the median +-1 LSB effect on mean-aggregated S), which makes a "tie" mean "indistinguishable from an invisible perturbation". Pair margins on dev were not inspected (MJ9), so the fraction of pairs affected by 5e-4 is unknown.
The "clean vs edited tie" case (shared-prefix pairs whose maxima come from the shared prefix) cannot be tested without an edited dev condition (MJ9 forbids it before freeze); the bitwise determinism above guarantees that unchanged windows give exactly equal values when the batch composition is identical, so such ties are exact (<1e-4) not noisy, provided the same window batching (6 windows/batch, fixed order) is used for both members. Batch composition is deterministic in the code (windows in order, batch of 6).
