# EXPLORATORY post-freeze kernel groups (built, NOT pushed)

All labelled EXPLORATORY. No frozen parameter, analysis code, or bundle was changed. Bundle head **28f44a7a047a67b449f46205b6c6a3b474bbccfd** (built in one pass from a clean worktree, `repo_dirty: false`, `scripts/check_bundle_hash.py` OK, head added to `REPO_HEAD_ALLOWLIST` in a separate one-line commit 7a64fb2). Definitions: `scripts/make_expl_runs.py`; tests: `tests/test_expl.py`.

| group | runs (ids) | size | est. GPU-h (2xT4, fp16) |
|---|---|---|---|
| `expl_onset_spec` | 10 half-size M1 runs, members possible, mid level, onset-aligned `matches.json`: `EXPL_M1_ipdev_onset-{lighting_global,lighting_local,jolt_base}-mid_s{1,2,3}` and `EXPL_M1_ipdev_onset-zoom_base-mid_s1` | 10 x 180 videos | 1.60 (10 x 0.16; measured mean of 32 M1 half runs 0.159, range 0.145-0.165) |
| `expl_halve_hold` | 1 full-size M1 run, both members, seed 1: `EXPL_M1_ipdev_halve_hold-high_s1` | 360 videos | 0.31 (equal to P4_M1_ipdev_clean_s1 wall, 0.311; same 17 windows) |
| total | 11 runs | | 1.91 GPU-h plus kernel start-up (2 kernels) |

Seeds: as the frozen mid runs (seeded kinds 1-3, zoom_base 1). No M0r, base_ref or M2 run (see ONSET_ALIGNED.md: the clean runs and the existing `P4_M1_ipdev_base_ref-ref_s1` are the references; the task scoped M1 only).

## Onset group
Matches file `kaggle/expl_onset_spec/matches.json` (pixel-only onset rule, theta = 0; details and achieved-ratio table in `notes/ONSET_ALIGNED.md`). Same `run_lib` code path: the matches format is unchanged, so the run configs read it exactly as the frozen groups do.

## Corrected frame-rate edit: `halve_hold`
Definition: g[t] = f[t - t mod 4] for every native frame (hold the previous kept frame). At frame step 2 the model samples native frames 0, 2, 4, ...; sampled frames 2m and 2m+1 both show native frame 4m. Effective temporal resolution is halved while the time span, the number of sampled frames (49), tubelets and windows (17) are those of the clean skip-2 run. Reference = existing clean skip-2 run (`P4_M1_ipdev_clean_s1`), window-by-window pairable; high strength = on; seed 1 (deterministic); applied to both pair members.

Why this one: it is the simplest edit that differs from the clean skip-4 reference (the pre-registered fps_halve is bit-identical to it) and keeps everything else of the clean run identical, so the paired contrast isolates temporal resolution. Not the skip-4-with-duplication alternative: that changes the span/windows and has no same-window reference.
Caveats to carry into any write-up: (i) duplicated frames were prohibited for the pre-registered edit because the content is not physically neutral; here the duplication is the point and the edit is not an invariance in the physical sense (apparent motion becomes stepwise); (ii) with tubelet size 2 and window starts on even sampled indices, every tubelet is a static pair (f_4m, f_4m), so the model sees no intra-tubelet motion; this is phase-specific, and a phase-shifted variant (tubelets straddling the held pair) was not built; (iii) deterministic: one seed.

## Same-code-path statement (decoded bundles vs h1_inv_a, the 4c4017b family)
`kaggle/common/run_lib.py`, `kernel_main.py` body, `configs/edit_params.yaml`, `src/` (except `models/m2_vjepa2.py`, the already-permitted A-Q10 amendment), and the pinned externals are byte-identical. Differing files:
- `expl_onset_spec`: `BUNDLE_INFO.json`, `runs.json`, `matches.json` (the onset file; differs from the h2_spec_* file), new `kaggle/expl/expl_lib.py`, `kaggle/expl/preamble.py`, and `src/vjepa_study/models/m2_vjepa2.py` (permitted).
- `expl_halve_hold`: the same minus `matches.json`.
The preamble patches only `run_lib.apply_run_edit` for edit name `halve_hold` and delegates every other edit unchanged; the onset group never exercises that branch. `kaggle/build_kernel.py` (not in any bundle) gained an `expl*` prefix branch. Locked by `tests/test_expl.py::test_same_code_path_vs_frozen_bundles`.

## Analysis plan hooks (not run)
Onset specificity: same frozen functions with t_on from the new matches, outcome labelled EXPLORATORY; compare A (all, excluding lighting_global) against the confirmatory A = 0.546. halve_hold: paired dAcc and flip rate against clean skip-2 with the dither floor as reference. Kaggle quota is the lead's call; nothing was pushed.
