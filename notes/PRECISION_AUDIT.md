# Precision audit (human request, 2026-10-09)

Sources: `meta.json` of every run under `results/raw/*/results/*` (field `run.precision`; table in `results/analysis/precision_audit.json`, key `precision_by_run`), `results/analysis/{p2_clean_g1,p2_vith_g1}.json`, `results/analysis/p4/*`, `results/analysis/h1/*`. Pair-level comparison: `scripts/precision_audit.py` (frozen prereg functions only) -> `results/analysis/precision_audit.json`. No frozen file touched.

Meta census (all 71 runs with a run block): fp16 60, fp32 10, bf16 1, not recorded 2 (P1 sanity and P1 timing, 2026-10-06, bundle e3a8acc; no number from them is reported as a result). Every P4 run (clean, controls, H1, dither, M0r, M2) is fp16, 2 GPUs. fp32 exists only for P2 clean (M1 x2, M0r x3), the P2 benchmark (2 runs) and the 6-video Debug check (3 runs).

## 1. Which precision produced each reported number

| Number | Value | Run id (meta precision) | Where used |
|---|---|---|---|
| G1' M1 ViT-L clean, mean agg | 81.7 tie-half / 80.6 strict (143 right, 8 ties, 29 wrong; max agg 73.1 / 62.2) | `P2_M1_ipdev_clean_s1` (**fp32**, head 2605fc8); rerun `P2_M1_ipdev_clean-rep_s1` fp32, bitwise identical | G1', M1 H1 eligibility, T1b / `b2_checks.json`, fp16-vs-fp32 row |
| G1' attempt 2, public ViT-H | 88.1 / 87.8 (max 83.1 / 80.0) | `P2H_M1H_ipdev_clean_s1` (**fp16**, head 499d7c9) | descriptive diagnostic |
| M1 clean (production) | 80.8 tie-half / 81.1 strict (142 right, 7 ties, 31 wrong at tau 1.057e-4; max agg 72.5 / 62.2) | `P4_M1_ipdev_clean_s1` (**fp16**, head 606d732) | y0 reference of every H1 contrast, tau, dither floor, G2/H3, dose |
| M1 skip-4 clean | 82.2 / 82.2 | `P4_M1_ipdev_clean-skip4_s1` (fp16) | reference for fps_halve only |
| M0r x3 | P2: 50.0 (97-99% ties); P4: 50.0 (ties 180/180/178) | P2 runs fp32; P4 runs fp16 | G2 M0r reference uses the **fp16** `P4_M0r_ipdev_clean-init0_s1` |
| B1 / B2 | 58.1/57.2 and 76.1/76.1 (mean agg) | stored in both runs | arrays **bit-identical** between fp32 and fp16 runs (pixel baselines, no model); precision-free |
| B3 (encoder change) | fp32 41.1 / 44; fp16 45.3 / 45.0 | P2 fp32 vs P4 fp16 | **precision-dependent** (max array diff 1.6e-3); secondary, quote with its run |
| M2, mask_index 1 (documented deviation) | 46.9 / 46.7 (19 ties) | `P4_M2_ipdev_clean_s1` (fp16, 606d732) | excluded from contrasts (`EXCLUDED_RUNS`) |
| M2, mask_index 0 (corrected) | 60.8 / 60.6 (17 ties, tau 1.109e-4) | `P4_M2_ipdev_clean-mi0_s1` (fp16, 649988d) | M2 eligibility (not eligible). Only fp16 exists for M2 |
| G2 (vflip 21.1%, hflip-referenced 25.8%, reversal 60.8%, M1-M0r -66.7pp) | `results/analysis/p4/h3_M1.json` | `P4_M1_ipdev_{vflip,time_reversal,hflip}-high_s1` fp16 (beea21e); clean ref `P4_M1_ipdev_clean_s1` fp16; M0r `P4_M0r_ipdev_vflip-high_s1` fp16 vs `P4_M0r_..clean-init0` fp16 | all fp16 |
| H1 (all 7 edits + dither + dose) | `results/analysis/h1/h1_M1.json` | edited `P4_M1_ipdev_*` fp16 (head 4c4017b; hflip beea21e), reference `P4_M1_ipdev_clean_s1` fp16 (606d732) | all fp16 |

Note on traceability: `results/analysis/p4/p4_clean_g1.json` and `notes/P4_CLEAN_G2.md` still carry the old M2 row (46.9); the 60.8 / 17 ties figure exists only in DECISIONS.md. I recomputed it now from `P4_M2_ipdev_clean-mi0_s1` (matches: 60.8 / 60.6 / 17 / 1.109e-4), stored under `M2_mi0_fp16_clean_recomputed` in `results/analysis/precision_audit.json`. `scripts/p4_clean_analysis.py` already points at the mi0 run; the JSON just was not regenerated. Recommend regenerating before the verifier pass (not done here: output path is a frozen-analysis artifact).

## 2. H1 reference and precision consistency

- `h1_M1.json` reference y0 = `P4_M1_ipdev_clean_s1` (fp16): `clean_acc_tiehalf_run` = 0.8083. Edited runs, dither runs (floor f0) and the high-strength halving run are all fp16/2 GPU; fps_halve is compared with the fp16 skip-4 clean. `meta_check.json` (41 runs): no precision or n_gpus mismatch, no bypass.
- The single place an fp32 number enters H1 is the eligibility field: `eligibility_clean_acc_tiehalf` = 0.8167 (P2 fp32), as the prereg fixes (sec 6: M1 judged on fp32, never re-evaluated). It affects only `status`; f0 = 21.5% >= 10% makes M1 H1 descriptive regardless. No contrast mixes fp32 with fp16.
- Heads: clean 606d732 vs edited 4c4017b / beea21e differ, but all are on the prereg allowlist with logged equivalence (same precision/sharding/code path).

## 3. fp16 vs fp32 clean, same 180 pairs (M1, mean aggregation, own tau 1.057e-4 each)

| | fp32 | fp16 | difference |
|---|---|---|---|
| tie-half acc | 81.67% | 80.83% | **-0.83 pp** (-1.5 pair credits) |
| strict acc | 80.56% | 81.11% | **+0.56 pp** (+1 pair) |
| ties (<= tau) | 8 | 7 | tie sets: 5 shared, 3 fp32-only, 2 fp16-only |

(Credits: fp32 = 143 right + 4 tie-credits = 147; fp16 = 142 + 3.5 = 145.5; both above the 144 threshold.)
- Pair-level tie-half verdict changes: **5 of 180 (2.8%)**: 3 pairs tie -> wrong, 1 wrong -> tie, 1 right -> tie; net 4 pairs worse, 1 better. Strict verdict changes: **1** (pair index 46, margin -2.9e-5 -> +3.8e-5, i.e. inside the tie band). No pair with |margin| above ~1e-3 changes verdict.
- Margin noise: |S_imp-S_pos| differs by mean 6.8e-5, max 5.5e-4 between precisions (median |margin| 1.6e-3); per-window |dS| mean 1.65e-4, max 2.65e-3 (`p4_clean_g1.json`).
- Reading: fp16 is lower than fp32 by 0.83 pp under the primary tie-half rule and higher by 0.56 pp under strict; the sign of the "precision effect" depends on the tie convention, so it is tie-band reshuffling, not a systematic degradation. Both runs clear 80%. The fp16 shift (2.8% verdict changes) is about 8x smaller than the dither floor (f0 = 21.5% tie-half, 15.6% strict), so fp16 arithmetic is not what produces the floor (dither contrasts are fp16 vs fp16, same code path).

## 4. Flags

1. No mixed-precision contrast found in H1, G2/H3 or the new dose analysis (all fp16 vs fp16).
2. M1 eligibility is judged on fp32, M2's on fp16 (prereg-fixed asymmetry). Outcome-neutral here (M1 80.8 fp16 also >= 80; M2 60.8) but state it in Methods.
3. The G1' ladder compares ViT-L fp32 (81.7) with ViT-H fp16 (88.1). The precision confound is of the order of the 1 pp difference above, small against the 6.4 pp gap; mention it.
4. B3 numbers are precision-dependent; B1/B2 are not. T1 should state the run behind every row (M1 from fp32 or fp16).
5. `p4_clean_g1.json` M2 row is stale (see above).
6. P1 runs have no precision in meta (not used for results).
