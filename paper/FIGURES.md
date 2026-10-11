# Paper tables and figures (generated)

Regenerate any item: `.venv/bin/python scripts/figs/<script>.py` (needs the symlink dir `~/.cache/claude-tmp/figs_runs`, built from `results/raw/*/results/P*` excluding `*_v1_*`, only for F2/F3/F4 panel data). Each item writes a sidecar `<output>.json` listing the VERIFIED keys used (with status), missing keys, and input files. `scripts/figs/common.py` holds shared helpers. T2 and T2b share the sidecar `paper/tables/t2_invariance.json`.
Conventions: Okabe-Ito palette, hatch/marker/linestyle redundancy (greyscale-safe), CIs shown, H1 driver verdict labels never printed (dAcc, flip, flip minus dither floor f0 only), fps_halve only in a footnote, M2 descriptive, M2 old mask_index-1 run only as a marked row in T1, M3 = "pend.".
Re-run all scripts after VERIFIED.json gains the M2 dose-response keys and M3 keys; pending cells/panels fill from the key names listed below.

| ID | File | Script | Keys (summary; full list in sidecar) | Caption draft |
|---|---|---|---|---|
| T1 | tables/t1_reproduction.tex (`tab:t1`) | t1_reproduction.py | g1_m1_clean_acc, m1_fp16_clean_acc, g1_vith_clean_acc (mismatch: prereg-tau value 88.3 used), m2_new_acc, m2_old_acc, clean.*.strict, clean.B1_P2.tiehalf (mismatch status), b2_clean_acc, m1_minus_b2_diff/ci; M0r from analysis json | Reproduction on IntPhys dev: pairwise accuracy of the public checkpoints vs published; the published RoPE models are not released and the gap is unexplained. M2 old run shown only as a superseded disclosure row. |
| T2 | tables/t2_invariance.tex (`tab:t2`) | t2_invariance.py | h1.{M1,M2}.{edit}.{dacc_pp,flip_pct,flip_minus_f0_pp,holm14_*,n}, h1.*.f0_pct, h1_f0_strict, h1.M1.fps_halve.identical_to_skip4_clean | Invariance (H1) at high strength: dAcc, flip rate, and flip minus the dither floor; M1 confirmatory, M2 descriptive. |
| T2b | tables/t2b_invariance_dose.tex (`tab:t2b`) | t2_invariance.py | dose.h1.M1.{edit}-{level}.*, h1.M2.* (high); PENDING m2.dose.h1.{edit}.{low,mid}.{dacc_pp,flip_pct,holm30_dacc,holm30_flip} | Invariance dose-response (A3), low/mid/high; M2 low/mid pending. |
| T3 | tables/t3_controls.tex (`tab:t3`) | t3_controls.py | g2_vflip_det/_ci, g2_rev_det, g2_hflip_det, g2_m0r_vflip_det, g2_vflip_pair_acc, h3.M1.*, h3.M2.* | Positive controls: detection rate [95% CI] for M1, M2, M0r; M3 pending. G2 not met for M1 and M2. |
| T4 | tables/t4_ablations.tex (`tab:t4`) | t4_ablations.py | primary row: clean.M1_fp16.tiehalf, h2.M1.{A,A0,D_B1,D_B2}; ablation rows from results/analysis/ablations/* (NOT in VERIFIED) | Ablations A1 (aggregation) and A2 (fixed C) on clean accuracy and specificity AUROC for M1. A3 = T2b/F3. |
| T5 | tables/t5_specificity.tex (`tab:t5`) | t5_specificity.py | h2.{M1,M2}.{A,A0,A_nolg,D_B1,D_B2,*.no_lg,holm2_*,A.<type>}, h2.M1.A_B1/A_B2, h2_lg_noop_n, h2_entries_n, h2_mi_median, h2_fallback_n, h2_pairs_n; B CIs/A0/per-type from results/analysis/h2/h2.json | Specificity AUROC against 0.5 (primary); D1/D2 secondary with B1, B2 below chance; with and without lighting_global. |
| T6 | tables/t6_blocks.tex (`tab:t6`) | t6_blocks.py | ip2main.{M1,B1,B2,B3}.all.*; dev per-block from results/analysis/p4/clean.json | Clean accuracy by block: IntPhys dev O1-O3 and IntPhys 2 Main by category (Main = evaluation only, near chance). |
| T7 | tables/t7_exploratory.tex (`tab:t7`) | t7_exploratory.py | expl.onset.*, expl.halve_hold.* | EXPLORATORY: onset-aligned H2 and halve-and-hold H1. |
| F1 | figures/f1_invariance.pdf | f1_invariance.py | h1.{M1,M2}.{edit}.{flip_pct,flip_minus_f0_pp(+ci),f0_pct} | Invariance: flip rate per edit at high strength with the dither floor f0 (a), excess over the floor with 95% CI (b). fps_halve omitted. |
| F2 | figures/f2_specificity.pdf | f2_specificity.py | h2.M1.A, h2.M1.A_B1/A_B2, h2.M2.A(+_nolg); panel (a) arrays from raw runs, B CIs/B3 from h2.json | Specificity: CDFs of delta_viol vs matched delta_abrupt for M1 and B1 (a); AUROC with CIs for all scores against 0.5 (b). |
| F3 | figures/f3_dose.pdf | f3_dose.py | dose.h1.M1.*, dose.h2.M1.*, h1.M2.*.flip_pct, h2.M2.A(+type); PENDING m2.dose.h1.*, m2.dose.h2.{pooled,type}.{low,high}.A; M1 flip CI band from h1/dose/dose_M1.json | Dose-response: flip rate vs strength (H1 edits) and AUROC vs strength (H2 types), M1 and M2. |
| F4 | figures/f4_curves.pdf | f4_curves.py | none (raw runs + kaggle/h2_spec_a/matches.json) | Example M1 surprise curves for three median pairs: possible, impossible, possible + abrupt lighting event; event time t* marked (random-onset fallback pairs). |
| F5 | figures/f5_dither_floor_EXPLORATORY.pdf | f5_dither_floor.py | none (copy of figures/dither_floor_EXPLORATORY_post-hoc.pdf) | EXPLORATORY post-hoc: verdict margin vs dither noise floor. |
| F0 | figures/f0_schematic.pdf | (existing, not touched) | | |

## LaTeX wiring (the writer does this)
All tables use booktabs only; no multirow. Floats: T1, T3 (table*), T2, T2b, T4, T5 are table*; T6, T7 single column (T1 single column). Labels: tab:t1, tab:t2, tab:t2b, tab:t3, tab:t4, tab:t5, tab:t6, tab:t7; F3 is referenced by T4 as `fig:f3` (add `\label{fig:f3}` where the figure is included). Include figures with `\includegraphics[width=\textwidth]{figures/fN_*.pdf}` in `figure*`. Tables standalone-compile with tectonic under IEEEtran (checked, no overfull boxes).

## Caveats
- T4 ablation rows and the F3 M1 CI band are not VERIFIED keys: the verifier must recompute them (new outputs in results/analysis/ablations/).
- T1 values flagged `mismatch` in VERIFIED (g1_vith_clean_acc, clean.B1_P2.tiehalf): the prereg-tau convention value is printed; see the key notes.
- M3 (VideoMAE V2) not run: T1, T3, T5 and F2 show pending.
- M2 dose-response keys absent from VERIFIED (only brace-pattern placeholders exist): T2b/F3 cells show pending.
- F5 is the existing figure, not restyled.
