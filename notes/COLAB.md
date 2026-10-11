# COLAB runbook (single T4, overflow groups)

Files: `notebooks/colab/vjepa_colab.ipynb` (one parameterised notebook, set `GROUP`), `vjepa_colab.py` (helpers), `dev_npz.sha256` (360 dev files), `bundles.sha256` (built `run.py` hashes), `test_shard_dryrun.py` (CPU sharding test), `make_notebook.py`. Nothing in `src/`, `kaggle/` or `configs/` was changed; the bundle `run.py` is executed unchanged.

## 1. What to run, in order (bundles at head 4c4017b, hash-checked)
| order | GROUP | runs | already done on Kaggle | est. T4 time |
|---|---|---|---|---|
| 1 | `h1_inv_c` | 9 x 360 videos (blur, jpeg, zoom; low/mid/high; M1) | none | ~5.7 h (9 x 38 min) + ~5 min load |
| 2 | `h2_spec_b` | 18 x 180 possible videos (M1 jolt_base x9, zoom_base x3, base_ref; M0r x5) | base_ref M1 and M0r (2 runs, copy them to Drive, see below) | 16 runs ~ 5.2 h (16 x ~19 min) |
| 3 | `h2_spec_a` | 18 x 180 (M1 lighting_global/local x low/mid/high x s1-3) | none (all 18 failed: no matches.json) | ~5.8 h |
| later | `m2_*` groups (df52a7c) | gated on M2 mi0 eligibility (60.8%, not eligible): do NOT run unless the lead says | | M2 is ~2x M1 |

Assumption behind the estimates: a Colab T4 equals a Kaggle T4; one T4 costs 2x the 2xT4 wall (measured 5.17 vs 2.54 s/video, notes/FP16_DETERMINISM.md, bitwise-identical arrays); 2xT4 wall per run from state/RUNS.md (h1_inv_a: ~1135 s per 360-video run; h2_spec_b base_ref 582 s and M0r 566 s per 180-video run). Total 3 groups ~16.5 h = 2-3 Colab sessions; free-tier sessions often end earlier than 12 h, so expect to rerun the notebook (it resumes). `p4_clean`-style IntPhys-2-Main groups **do not exist**: `make_p4_runs.py` defines none and `run_lib.iter_items` supports only datasets `ipdev` and `ip2debug` (Debug), so IP2-Main would need a run_lib change (not made; propose separately if wanted).

## 2. The n_gpus finding (decision needed)
`kernel_main.build_model` creates `n = min(run["n_gpus"], torch.cuda.device_count())` wrappers; on one T4 that is 1, and `run_lib.run_one` then shards `i % 1` (all videos sequentially on one GPU; there is no emulation of 2 shards) and writes `meta.json["n_gpus"] = 1` (the string `device_assignment: "i % n_gpus"` is identical either way). Consequences, shown by `notebooks/colab/test_shard_dryrun.py` (CPU, real dev npz, dummy model; run with `.venv/bin/python`):
- Per-video computation does not depend on the shard: arrays (S, ids, hashes, baselines) of the n=1 and n=2 runs are bitwise equal; item order and the `i % 2` assignment are as in run_lib; `meta.json` differs only in `n_gpus` and timing fields. This agrees with the Kaggle measurement `p2_det2` (1 GPU vs 2 GPU fp16, 12 videos, max|dS| = 0.0).
- BUT `check_run_meta` (src/vjepa_study/analysis/prereg.py) keys `precision` and `n_gpus` per model; `run_meta_check` treats a mismatch as a hard abort (never bypassed by `--allow-meta-mismatch`). The same dry run reproduces it: `ABORT: n_gpus ['1','2']`. So Colab outputs of M1/M0r would abort the analysis if mixed with the Kaggle 2-GPU runs of the same model (all M1 groups share one `n_gpus` expectation).
- Cannot be fixed without touching code or data: emulating two shards needs a second wrapper in `build_model`/`run_one` (src change), or the recorded `n_gpus` must be overridden.

Minimal proposals (lead picks; I made neither):
- **A (preferred, 1 edit in analysis code, not in kernels):** in `check_run_meta`, drop `n_gpus` from the default keys (or normalise it) and instead require `precision` to match and a documented equivalence: "n_gpus affects only wall time; fixed sharding is bitwise-equivalent to 1 GPU (p2_det2, Colab cross-check below)". Needs a DECISIONS entry and a prereg s1 deviation note, because s1 states "2-GPU fixed sharding". Pre-registered equivalence statement is stronger if the cross-check below passes.
- **B (no code change):** patch the returned `meta.json` files (`n_gpus` 2) and add `n_gpus_actual: 1, colab: true` fields. This edits raw outputs, so I would only do it with a DECISIONS entry; I consider A cleaner.
- **C:** keep the Colab runs but analyse them separately as a sensitivity set (loses the confirmatory contrasts for these conditions; not recommended).

Second risk (not covered by the meta check): Colab's torch/CUDA/cuDNN build differs from Kaggle's (Kaggle: torch 2.11.0+cu128, python 3.13.15, numpy 2.1.3, timm 1.0.29, T4). fp16 results are bitwise only on the same stack. Hence the **cross-check**: set `RUN_XCHECK = True` in the `h2_spec_b` session; it reruns the first 15 scenes (30 possible videos, ~3 min) of `P4_M1_ipdev_base_ref-ref_s1` through the same kernel_main code and compares per-video S with the Kaggle 2-GPU output. Bitwise equal -> proposal A is well supported; max|dS| > 0 (expected scale 1e-4 to 4e-4, cf. benchmark=True jitter) -> report to the lead: confirmatory contrasts then mix numerical stacks and the lead must decide (the pre-registered tie tolerance relies on bitwise determinism). Cell-by-cell the notebook also prints the Colab `torch`/`cuda` (also in each `env.json`).

## 3. One-time setup (human)
1. Local, before uploading: `.venv/bin/python scripts/check_bundle_hash.py h1_inv_c h2_spec_a h2_spec_b` must print OK x3. (The notebook repeats an equivalent check in cell 4.)
2. Create Drive folder `MyDrive/vjepa_colab/` with:
   - `code/`: `notebooks/colab/vjepa_colab.py`, `dev_npz.sha256`, `bundles.sha256`.
   - `bundles/<GROUP>/run.py`: copy of `kaggle/<GROUP>/run.py`, unmodified (hashes: h1_inv_c f3e223e8..., h2_spec_b 7512f59b..., h2_spec_a 982da72c...).
   - `dev_npz/`: the 360 `O?_??_?.npz` files from `kaggle/datasets/intphys-dev-npz` (3.8 GB). IntPhys dev is not redistributed by us; upload from your own copy to your own Drive only. The notebook verifies every file's sha256.
   - `h2_spec_b` only: copy `results/raw/h2_spec_b/results/P4_M1_ipdev_base_ref-ref_s1` and `.../P4_M0r_ipdev_base_ref-ref_s1` into `out/h2_spec_b/results/` (skips those two runs), and the M1 dir also into `reference/` (cross-check).
3. Open `notebooks/colab/vjepa_colab.ipynb` in Colab, Runtime = T4 GPU (one GPU; the notebook asserts it), set `GROUP`, Run all. Internet is on in Colab (pip einops/beartype, checkpoint from dl.fbaipublicfiles.com; SHA256 recorded in meta.json).

## 4. Behaviour, resume, hand-back
- Environment: the bundle hard-codes `/kaggle/working` and `/kaggle/input`; Colab runs as root, so the notebook just creates them and symlinks the dataset. Kernel precision fp16 autocast, `cudnn.benchmark=False`, deterministic cuBLAS (`CUBLAS_WORKSPACE_CONFIG`) come from run.py itself, unchanged. Batching (6 windows) is per video, hence identical.
- Resume: `run_lib.run_one` skips any run whose `surprise.npz` exists. The notebook restores finished run dirs from Drive and copies each newly finished one (meta.json present, written last) back every 60 s, so a disconnect loses at most the run in progress (~20-40 min). Just rerun all cells.
- Output: `MyDrive/vjepa_colab/out/<GROUP>_colab.zip` (+ `.sha256`), containing `results/<run_id>/{meta.json,surprise.npz,log.txt}` and `results/{kernel_log.txt,env.json,status.json}` (same layout as `kaggle kernels output`). Send back these zips. Suggested unzip: `results/raw/<GROUP>_colab/` (do not overwrite `results/raw/<GROUP>/`; for h2_spec_b the two Kaggle-done runs are copies, bit-identical). Each run's `meta.json` carries wall_s for the RUNS.md rows (GPU min = wall_s/60, note "Colab T4, n_gpus=1").
- Validation printed before the zip: all requested runs present, finite, `n_videos` matches, precision fp16. n_gpus is reported as 1 (see s2).
- Do not delete the Drive `out/<GROUP>/results` folder until the zip is on the lead's disk.

## 5. Needs a decision
1. n_gpus (s2): A, B or C. Until decided, Colab outputs are collected but not analysed with Kaggle outputs.
2. Whether to request an IP2-Main run_lib extension (no such groups exist today).
3. Colab-vs-Kaggle numerical stack: act on the cross-check result.

Status 2026-10-08: not used, human declined Colab 2026-10-08 (everything waits for Kaggle after the Oct 10 reset).
