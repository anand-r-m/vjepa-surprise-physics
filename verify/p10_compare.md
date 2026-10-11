# P10 compare: verifier recompute (verify/p10_recompute.json) vs analyst (results/analysis/exploratory/splice_EXPLORATORY.json)
Opened only after verify/p10_recompute.{json,md} were written. Tolerances: counts exact; percentages 0.1 pp; bootstrap CI ends 1 pp / 0.01 rho.

| item | verifier | analyst | status |
|---|---|---|---|
| single / double splice | 120 / 60 (40+20 per block) | 120 / 60 (same per block) | match |
| non-splice impossible videos | 0 (0 unmatched frames of 18,000) | n_other 0 | match |
| first switch median [min, max] | 49 [16, 88] | 49 [16, 88]; terciles cutoffs 43.67 / 53.33 | match |
| double vs single median first switch | 45.5 / 51.0 | 45.5 / 51.0 | match |
| clean M1 / B1 / B2 tie-half | 80.83 / 58.06 / 76.11 | 80.83 / 58.06 / 76.11 | match |
| tau (M1, B1, B2) | 1.0570e-4, 7.2286e-7, 1.3560e-6 | 1.0570e-4, 7.2286e-7, 1.3560e-6 | match (differences < 1e-12 relative 1e-7) |
| Spearman M1-B2 | 0.5410 [0.418, 0.645] | 0.5410 [0.418, 0.643] | match (CI upper differs 0.002: different bootstrap draw stream; same seed, scene-stratified resampling coded independently) |
| Spearman M1-B1 | 0.5770 [0.460, 0.679] | 0.5770 [0.460, 0.675] | match (CI upper differs 0.004, same cause) |
| M1 acc on B2 right / wrong (n) | 91.24 (137) / 47.67 (43), diff +43.57 [28.04, 58.82] | 91.24 (137) / 47.67 (43), diff +43.57 [28.03, 58.74] | match |
| M1 acc on B1 right / wrong (n, ties) | 92.08 (101) / 65.28 (72), 7 ties, diff +26.80 [14.29, 39.40] | same; diff [14.05, 39.20] | match (CI ends within 0.3 pp) |
| single vs double, M1 / B1 / B2 | 75.0 / 92.5; 61.7 / 50.8; 75.0 / 78.3 | 75.0 / 92.5; 61.7 / 50.8; 75.0 / 78.3 | match |
| M1 single - double | -17.5 [-26.1, -8.7] | -17.5 [-25.7, -8.6] | match (CI within 0.4 pp) |
| tercile accuracy M1 early / mid / late | 83.3 / 77.5 / 81.7 | 83.3 / 77.5 / 81.7 | match |
| tercile B2, B1 | 76.7 / 70.0 / 81.7; 58.3 / 52.5 / 63.3 | same | match |
| vflip counts (both, lost, gained, neither), McNemar p | 135, 11, 13, 21; 0.839 | 135, 11, 13, 21; 0.839 | match |
| hflip | 139, 7, 12, 22; 0.359 | same | match |
| reversal | 123, 23, 9, 25; 0.0201 | same | match |
| vflip detection M1 (tie-half) | 21.11 (possible videos) | (not in the analyst's file; in VERIFIED g2_vflip_det) | n/a |
| peak window covers a switch frame, M1 imp | 71.7 (sampled-aligned, first switch) / 73.9 (native, either switch) | 73.9 | MISMATCH in my primary definition, explained: the analyst tests 4w <= s <= 4w+30 on native frames with either switch; I first used sampled-frame alignment and the first switch only. Re-run with the analyst's definition: 73.9 / B1 49.4 / B2 55.0, chance 46.9, possible-partner control 53.9 / 41.1 -- exact match (M1 73.89, B2 55.0, pos M1 53.89, pos B2 41.11, chance 46.93 vs 46.93). |
| M0r vflip / reversal pairwise | not definable (possible videos only, labels all 0) | skipped for the same reason | match |
| "79%" M1 vflip shift negative | 79.44% (143/180 possible videos); 75.83% over all 360 | not in analyst file | verifier-only, in VERIFIED |
| M0r 87.8% positive | 158/180 = 87.78% | not in analyst file (VERIFIED g2_m0r_vflip_det 87.78) | match with VERIFIED |

Not recomputed (analyst-only items, so no VERIFIED key): B1-B2 margin correlation, per-block and single/double Spearman, M0r-vs-B2 Spearman, Pearson, B2 accuracy given M1 correctness (142/31/7), margin median/mean, the edited-run B2-stratified tables, lost/gained by tercile and by B2 correctness, verdict-flip rates, the verdict_rule_result flags. Any of these quoted in the paper needs a key first. Also note: "supported" in `verdict_rule_result` is the analyst's label for a pre-set rule (E1: rho CI lower > 0; E2: right-minus-wrong CI lower > 0); the two inputs are reproduced here (E1 lower 0.418, E2 lower 28.0 pp), the label is the analyst's. Both E1 and E2 are association statements and cannot separate "M1 detects splices" from "M1 and B2 both respond to scenes where the post-splice content differs".

Cause summary: only mismatch was a definition difference (peak window); CI end differences <= 0.4 pp / 0.004 rho are bootstrap-stream differences.

## Writer-facing keys for the Discussion splice paragraph and Method splice sentence (verified, exploratory)
- 120 / 60 splices: `expl.splice.n_single`, `expl.splice.n_double`; none unspliced: `expl.splice.n_nonsplice` (=0)
- 91.2 / 47.7 and counts 137 / 43: `expl.splice.m1acc_right.B2`, `expl.splice.m1acc_wrong.B2`, `expl.splice.n_b2_right`, `expl.splice.n_b2_wrong`
- Spearman 0.54 (0.42 to 0.65): `expl.splice.spearman.M1_B2`
- single / double 75.0, 92.5 (M1), 75.0, 78.3 (B2): `expl.splice.single.M1`, `.double.M1`, `.single.B2`, `.double.B2`
- peak window 73.9 and chance 46.9: `expl.splice.peak_covers.M1`, `expl.splice.peak_chance`
- position trend: `expl.splice.tercile.{early,mid,late}.M1` (83.3 / 77.5 / 81.7). "No trend" rests on these tercile values only (overlapping CIs); the analyst's rank correlation is not VERIFIED.
- McNemar vflip p = 0.84, reversal lost 23 / gained 9, p = 0.02: `expl.splice.edit.vflip.mcnemar_p`, `expl.splice.edit.time_reversal.{lost,gained}`, `expl.splice.edit.time_reversal.mcnemar_p`
- 79.4% (vflip decrease in possible videos): `expl.vflip.m1_frac_neg_possible`; 87.8%: `expl.vflip.m0r_frac_pos_possible`
