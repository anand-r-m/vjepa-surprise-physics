# M2 fix: predictor mask_index 1 -> 0 (Q10 B, human-approved 2026-10-08)

Only this one token change was made; no other token was tried.

## Diff (commit 649988d)
`src/vjepa_study/models/m2_vjepa2.py`: `M2VJEPA2.__init__(..., mask_index=1, ...)` -> `mask_index=0`; docstring updated. `kaggle/common/kernel_main.py` builds M2 with the default (no override), so the kernel now queries `predictor(..., mask_index=0)`. Reason: the official training wrapper passes the fpc-group index (0 for every mask), and in the released vitl.pt only `mask_tokens.0` is trained (tokens 1-9 are exactly zero; notes/m2_audit/ckpt_tokens_out.txt). Test: `tests/test_models.py::test_m2_mask_index_is_zero` (default is 0, predictor call uses self.mask_index, kernel_main does not override). Suite: 244 passed.

## Old run kept
`P4_M2_ipdev_clean_s1` (bundle head 606d732, mask_index=1, clean accuracy 46.9%, chance) stays in results/raw/p4_clean_m2 and is reported as a documented wrapper deviation (M2 with an untrained query token), not as a finding about V-JEPA 2. It is not overwritten; `kaggle/p4_clean_m2/run.py` is untouched.

## New bundle
- Group `p4_clean_m2_mi0` (new dir, so the old bundle and run id are preserved), run id `P4_M2_ipdev_clean-mi0_s1`, same settings as the old clean run (ipdev, step 2, fp16, 2 GPUs, all 360 videos, baselines and features stored). Added to `clean_groups()` in scripts/make_p4_runs.py.
- Built in one pass from a clean tree (detached git worktree at 649988d, `repo_dirty` false). Bundle head **649988dfe284e950d167a9f7a1ec91e3dc74a3f7**; added to REPO_HEAD_ALLOWLIST (separate commit). `check_bundle_hash.py p4_clean_m2_mi0`: OK.
- Decoded-bundle diff: vs p4_clean_m2 (606d732) the files that differ are BUNDLE_INFO.json, runs.json, analysis/{metrics,prereg}.py (permitted), configs/edit_params.yaml (E1: this bundle carries the frozen yaml, the old one the placeholder) and **models/m2_vjepa2.py (the fix)**. Vs h1_inv_a and h2_spec_b (4c4017b): BUNDLE_INFO.json, runs.json (and matches.json for h2_spec_b) and m2_vjepa2.py only; kaggle/common and run.py bodies byte-identical. m2_vjepa2.py is imported only for M2 runs, so M1/M0r behaviour of the 4c4017b bundles is unchanged.
- h1_inv_*, h2_spec_*, g2_controls and all clean M1 bundles were NOT rebuilt or touched.

## What to re-push
Only `p4_clean_m2_mi0` (about 0.5 GPU-h, 2 T4). There are currently NO M2 edited groups in scripts/make_p4_runs.py or kaggle/ (every existing edited group is M1/M0r), so no M2 edited bundle exists to rebuild. M2 edited groups (controls, specificity, invariance) still have to be defined and built; build them after the mi0 clean result is logged and eligibility judged, from a clean tree at the then-current head (their bundles will differ from p4_clean_m2_mi0 only by permitted files if that head changes nothing under src/ besides prereg/metrics; add that head to the allowlist as a separate commit).

## Follow-ups for the lead
- Analysis scripts that read `P4_M2_ipdev_clean_s1` (scripts/p4_clean_analysis.py:30) need to point to `P4_M2_ipdev_clean-mi0_s1` for the corrected M2 clean run; `run_meta_check` globs prefix `P4_M2_` so both runs would be compared (precision and n_gpus match; both heads are allowlisted), exclude the old run from M2 contrasts.
- PREREGISTRATION s1 same-code-path text lists the permitted differing files; m2_vjepa2.py (M2-only model file) should be added as a disclosed amendment (Q10 B).
