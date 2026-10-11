# P9 audit (verifier), HEAD b491acb

## A. Citation audit
Sources read: alphaXiv full text of each paper; ACL/arXiv/HF pages. 18 bib keys, all cited, all present.

### Garrido et al. (garrido2025), the \chk in 01_introduction.tex line 12
From the paper itself (arXiv 2502.11831v1):
- Headline 98% (95% CI [95,99]) is V-JEPA **ViT-H/16 pretrained on VideoMix2M** (the "flagship" model, Fig. 1A), pairwise accuracy on the **IntPhys dev set**, averaged over the three properties, with the **context size chosen per property to maximise accuracy** ("best achievable"). GRASP 66% [64,68], InfLevel-lab 62% [60,63].
- Per-property analysis (Figs 2, S7) uses ViT-L trained on HowTo100M (n=5), IntPhys per-property means 83.7 to 86.3. Fig. 3C: ViT-L stays "over 85%" even at 115M params.
- Baselines VideoMAEv2-g, Qwen2-VL, Gemini 1.5 Pro "only marginally above" random-init networks.
- 96.7 and 89.4 are NOT in Garrido. They are our independent recomputation from the released per-video surprise files (verify/released_dev_accuracy.md, strict rule, mean over 17 windows of min over 5 contexts): ViT-H VM2M 96.67 (174/180), ViT-L VM2M 89.44 (161/180), ViT-L HowTo 90.00, VideoMAEv2-g 53.33. They do not appear in the paper text (fine; do not attribute them to Garrido).
Resolution: the 98% is the ViT-H number, not ViT-L. Our confirmatory model is ViT-L, so "published accuracy" for M1 is not 98%. Required text fixes:
- 01_introduction l.12: "reported pairwise accuracy of 98% on IntPhys" -> "reported 98% pairwise accuracy on the IntPhys dev set for their flagship ViT-H model, with the context length tuned per property"; delete the \chk.
- 02_related_work l.5: same qualifier ("ViT-H").
- 04_results l.7 "The published 98% is not reproduced": say "published 98% (ViT-H)"; the ViT-H comparison (88.3) is the like-for-like one. Intro l.24, 03_method l.31, 05 l.3/l.13 "published accuracy/figure" should name ViT-H, and note that the ViT-L figure in Garrido is only given per property (about 84 to 86, HowTo100M-trained) and as 89.4 in our released-surprise recomputation.
- Garrido's context-length-per-property selection means 98% is an optimistic max; one clause is worth adding.
- "above-chance results on two further benchmarks (GRASP and InfLevel-lab)": supported (66%, 62%).

### Reference table
| key | status | notes |
|---|---|---|
| garrido2025 | OK (text fix above) | authors/title/year correct; arXiv only. |
| bardes2024 | OK | authors/title correct. Published in TMLR 2024 (per Bordes et al. refs); arXiv form acceptable. Optional: venue TMLR. |
| assran2025 | OK | title correct. First author appears as "Mahmoud Assran" in the PDF header (arXiv metadata "Mido"); bib "Mido" while garrido2025 entry is consistent with "Mahmoud" elsewhere; optional harmonise. Claim "adds a robot-planning stage" supported (V-JEPA 2-AC). |
| riochet2022 | OK | TPAMI 44(9):5016-5025, doi 10.1109/TPAMI.2021.3083839 (matches Garrido/Physion++ refs). "matched pixel for pixel" is IntPhys design. |
| bordes2025 | OK | Debug 60 videos, Main 1012 videos/506 pairs, V-JEPA 2-h overall 57.51 (text "57.5" ok), debug qualitative (Fig. 9) supported. Licence CC BY-NC 4.0, evaluation-only: confirmed on HF dataset card facebook/IntPhys2 (not stated inside the paper; cite the dataset card if the licence sentence needs a source). |
| su2025 | OK | NeurIPS 2025 workshop paper; V-JEPA models 0.50 (SAYCam), 0.52 (VJEPA2-H VM22M), 0.54 (VJEPA-L HowTo); "similar surprise for possible and impossible" supported. |
| begiristain2026 | OK | CRONOS: interventions viewpoint/scene/category/appearance on video generators; claim supported. |
| michaelov2025 | OK | arXiv abstract page: "Accepted to Findings of ACL 2025". |
| li2026 | OK (venue unconfirmed) | V-JEPA2 ViT-L Physion 73.2 vs human 74.2, disagreement 26.4% vs 4.8%; arXiv 19 Sep 2026. Keep as arXiv. |
| yocausal2026 | OK | denoising loss as surprise, temporal reversal; supported. |
| likephys2025 | FIXED | PDF header "Published as a conference paper at ICLR 2026". Applied to paper/refs.bib: journal field now "arXiv preprint arXiv:2510.11512 (ICLR 2026)". Supports the sentence. |
| wang2023 | OK | VideoMAE V2, CVPR 2023, pp. 14549-14560 (matches Garrido ref). Text correctly says M3 planned but not run (03_method l.6, 02 l.5); no claim it was run. |
| bear2021 | OK | Physion, NeurIPS D&B 2021. |
| tung2023 | OK | Physion++, NeurIPS D&B 2023; mass/friction/elasticity/deformability inference. |
| piloto2022 | OK | Nat Hum Behav 6:1257-1267. |
| weihs2022 | OK | TMLR 2022. |
| joseph2026 | OK | layerwise probing, "Physics Emergence Zone" at about one-third depth, peaks in middle layers; text "concentrated at intermediate layers" fine. |
| motamed2025 | OK | Physics-IQ. |
No removals. Bib change applied: likephys2025 only.

## B. Number audit
Method: own script over paper/NUMBER_TRACE.md rows vs results/VERIFIED.json (round half up of stored value/CI to printed precision), then a scan of all numeric tokens in sections/*.tex against the set of traced strings.
- Trace rows checked: 219 key-resolved rows. Rendering mismatches (half-up): **0**. CI strings: 0 mismatches.
- Status != verified (quoted in text): 5 rows. g1_vith_clean_acc 88.3 (mismatch, 03_method l.32, 04_results l.7) and clean.B1_P2.tiehalf 58.1 (mismatch): both are the superseded-fixed-tau status; documented lead decision 2026-10-11 (prereg tau, strict alongside 87.8 / 57.2); keep, but the paper must say the tie convention (it does). m1_minus_b2_diff_fp32 +5.6 and CI 0.0 to 11.1 (info-only): quoted once as info; acceptable per decision, label as fp32.
- Keys not in VERIFIED: 5 trace rows with pseudo keys (m2.dose.h2.pooled.{low,mid,high}.A.ci, m2.dose.h2.pooled.low.D_2.ci, m2.dose.h1.noise.mid.dacc_pp.ci). Values checked against the CI of the base key and all agree (0.434 to 0.533; 0.403 to 0.497; 0.375 to 0.468; -0.001 to 0.108; -13.9 to -2.2). Fix: fix the trace labels (no new VERIFIED entry needed).
- Text numbers with no VERIFIED key (not results): external citations 98%, 57.5%, 0.50-0.54, 506 (Su/Bordes/Garrido, checked above); design constants 0.65/0.80/0.85, 80%, 90%, 5 points, 10%, SSIM 0.95/0.85/0.70, 0.689 (JPEG achieved SSIM; no key, add or accept as design/calibration number), L* 5/10/20, crop 0.9/0.8/0.7, 2/255, 99.9th pct, 180 pairs/90 quadruplets/60-video Debug, Holm sizes 14/30/21/15/22/24/6/42/12, 112 (h1_zoom_n traced), 10,000 resamples, 0.95-1.05 / 0.9-1.1 matching targets. The trace itself marks 506 as TODO; 04_results l.42 should be keyed (ip2main.M1.all.n_pairs).
- Trace file:line labels are stale for moved text (supplement rows carry 04_results labels etc.); cosmetic.
- No numeric token in the prose lacking either a trace row or a constant above was found (token scan of all 7 sections).
- Pending-status values quoted: none.
- Repaired strings: 04_results exploratory paragraph "A_0 = 0.722": h2_A0 and expl.onset.A0 both 0.7222 (verified) OK. "-3.3 to 7.5" (halve-hold dacc +1.9): expl.halve_hold.dacc_pp = 1.94, CI [-3.33, 7.5], verified OK. NB trace puts the CI at 06_supplement l.27 and the main text copy at 04_results; both identical.
- Prose-number checker: scripts/check_prose_numbers.py check (baseline json) = 49 diffs; check-git HEAD~3 = 44 diffs. All diffs are additions from the last commit (M2 dose numbers in 04_results: e.g. 0.375, 0.420, 12.8, 13.9, 15.8, 18.6, 22, 24, 30.0, 34.4, 35.6, 42.2, 8.1; removal of 569/722 mangled tokens replaced by repaired strings; supplement \chk macro removed). Each new token is covered by the m2.dose trace rows I checked. Baseline is stale: re-snapshot after fixes. Intro \chk is still present (counted unchanged).
- Table cells: tables are generated from VERIFIED keys by scripts/figs/t*.py (json lists verified_keys_used, all verified for T5). I spot-checked T2b/T7 values against keys (0.065 [0.023, 0.109] etc., OK); a cell-by-cell recomputation of every table was not completed.

### T2b caption, Holm family
Recomputed Holm from the raw M2 p-values in verify/p8_recompute.json (11 existing M2 cells x {dAcc cluster p, flip-vs-floor p} = 22 p-values): stored keys m2.dose.h1.*.holm30_* match Holm over **22** in all 22 cases and differ from a 30-family in 7 (e.g. noise-mid dAcc 0.111 stored; Holm-30 would give 0.170; flip 0.246 vs 0.410). So the M2 columns use Holm-22, M1 columns Holm-30.
Required caption (scripts/figs/t2_invariance.py line 80 generates it; table .tex must be regenerated): "Holm-adjusted p: 30-test family for M1 (all graded cells), 22-test family for M2 (11 seed-1 cells x two tests; JPEG and zoom exist at high strength only)." Also delete the stale sentence "M2 low and mid cells read 'pend.' until those runs land": the table still contains 5 "pend" strings (JPEG/zoom low and mid were not run), so replace it with "dashes/pend. mark cells that were not run (GPU quota)". 03_method l.37 and 06_supplement l.17 already state 22/24/6 correctly.

## Required fixes (list)
1. 01_introduction l.12: qualify 98% as ViT-H flagship, per-property tuned context; remove \chk.
2. 02_related_work l.5, 04_results l.7, 01 l.24, 03_method l.31, 05 l.3/l.13, 06_supplement l.5: say "published 98% (ViT-H)"; ViT-L has no 98%.
3. T2b caption: Holm-30 (M1) / Holm-22 (M2); fix "pend." sentence; regenerate paper/tables/t2b_invariance_dose.tex.
4. Key 506 (and optionally 0.689) in VERIFIED or move to design constants in NUMBER_TRACE.
5. NUMBER_TRACE: rename the 5 pseudo-key rows, refresh stale line labels; re-snapshot scripts/prose_baseline.json.
6. Optional: likephys venue (applied), bardes2024 -> TMLR, harmonise Assran first name.
