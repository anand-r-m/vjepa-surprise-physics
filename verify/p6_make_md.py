import json
r=json.load(open('verify/p6_recompute.json'))
L=[]
a=L.append
a('# P6 independent recompute (verifier)\n')
a('Written before any analysis output was opened. Code: verify/p6_recompute.py, p6_pixels.py, p6_events.py, p6_retention.py (no src/ imports). Bootstrap: numpy default_rng seed 20261015, 10,000 draws, 30 scenes per block with replacement, all quantities on common draws.\n')
a('## 1. Clean accuracy (mean aggregation, 180 pairs, tau = 2e-4 x median of 360 per-video mean scores)\n')
a('| run | tau | tie-half | strict | exact-tie (tau=0) | ties at tau | tie-half credits |\n|---|---|---|---|---|---|---|')
for k in ('P4_M1_fp16','P2_M1_fp32'):
    c=r['clean_acc'][k]; a(f"| {k} | {c['tau']:.4e} | {c['tiehalf']:.4f} | {c['strict']:.4f} | {c['exact_tie_tau0_tiehalf']:.4f} | {c['n_ties_tau']} | {c['tiehalf_credits']} |")
for k in ('B1_fp16run','B2_fp16run','B3_fp16run','P4_M1_skip4'):
    c=r['clean_acc'][k]; a(f"| {k} | {c['tau']:.3e} | {c['tiehalf']:.4f} | {c['strict']:.4f} | | {c['n_ties']} | |")
a('\nPair/label structure derived from pixels agrees with the stored pair_id/label for all 180 pairs (every pair has one possible and one impossible member; prefix-sharing partner unique, no divergence ties).\n')
a('## 2. H1 (high strength; fp16 clean reference; skip-4 clean reference for fps_halve)\n')
a('Reading: y averaged over seeds per pair; flip = mean over seeds of 1[class changed]; tau = clean fp16 mean-aggregation tau for all edited runs (alt for fps_halve: skip-4 clean tau). f0 = dither flip rate (3 seeds) over the same retained pairs. Zoom retention: pairs whose violation support (|v-p|>8/255, channel-mean, frames [t_on,t_off), fallback window [48,100)) retains <90% inside the central 0.7 crop are excluded. Stored-match retention (matches.json) excludes 68 pairs; mine 70 (cm), 74 (max-channel); alt keep sets in JSON (h1 -> alt_keep=...).\n')
a('| edit | n pairs | dAcc (pp) | dAcc 95% CI | p cluster (2-sided) | Holm-14 | p sign | flip | f0 | flip-f0 | p flip-vs-floor | Holm-14 |\n|---|---|---|---|---|---|---|---|---|---|---|---|')
h=r['h1']['primary_keep=cm_win_0.7']
for e in ('brightness','noise','blur','jpeg','zoom','hflip','fps_halve'):
    x=h[e]; a(f"| {e} | {x['n_pairs']} | {100*x['dacc']:.2f} | [{100*x['dacc_ci'][0]:.1f}, {100*x['dacc_ci'][1]:.1f}] | {x['p_dacc_cluster']:.4f} | {x['holm14_dacc']:.4f} | {x['p_sign']:.4f} | {x['flip']:.4f} | {x['f0']:.4f} | {100*x['flip_minus_f0']:.2f} pp | {x['p_flip_vs_floor']:.4f} | {x['holm14_flip']:.4f} |")
a(f"\nDither floor over all 180 pairs: f0 = {r['h1_dither']['f0_mean_flip']:.4f} (dither dAcc {100*r['h1_dither']['dither_dacc']:.2f} pp). f0 >= 10% so M1 H1 is descriptive by the prereg rule.")
a(f"fps_halve edited run is bit-identical to the clean skip-4 run (flip 0, dAcc 0 by construction): {r['ties']['fps_halve_identical_to_clean_skip4']}.")
a('\nBootstrap p of 0.0000 means no draw of 10,000 crossed; report as < 1e-4.\n')
a('## 3. H2 (event-aligned max, mid strength, 4 types)\n')
e=r['h2_event_info']
a(f"Event times from pixels: tau_D = {e['tau_D']:.5f} (2/255 binds); fallback pairs (no D > tau_D) = {e['n_fallback_mine']} of 180 (matches stored meta {e['stored_fallback_meta']}), transient = {e['n_transient_mine']}, late (t_on>94) = {e['n_late']}. The max over time of the mean-pixel D(t) is below tau_D for 178 pairs, so the t* rule degenerates to the fallback; fallback t_on = {e['fallback_t_on_used']} (value taken from kaggle/h2_spec_a/matches.json; the prereg says only 'uniform in middle 50% seeded'). tau for H2/H3 (2e-4 x median clean full-clip max): "+', '.join(f"{k} {v:.3e}" for k,v in r['h2_tau_fullclip_max'].items())+'.\n')
a('Readings computed: R1 pixel-derived t_on with fallback 48 (PRIMARY); R1b stored matches.json t_on verbatim; R1c linear-resize D; R1d fallback 50; R2 t* = first frame where the two pair members differ at all (A1.3 wording); R3 full-clip max (no alignment).\n')
a('| reading | A_M1 | A_B1 | A_B2 | D_1 [95% CI] | p1 | Holm-2 | D_2 [95% CI] | p2 | Holm-2 | A0_M1 | M1 row |\n|---|---|---|---|---|---|---|---|---|---|---|---|')
for k,v in r['h2'].items():
    d1,d2=v['D']['B1'],v['D']['B2']
    a(f"| {k} | {v['A_point']['M1']:.4f} | {v['A_point']['B1']:.4f} | {v['A_point']['B2']:.4f} | {d1['D']:.4f} [{d1['ci'][0]:.3f}, {d1['ci'][1]:.3f}] | {d1['p_onesided']:.5f} | {d1['holm2']:.5f} | {d2['D']:.4f} [{d2['ci'][0]:.3f}, {d2['ci'][1]:.3f}] | {d2['p_onesided']:.5f} | {d2['holm2']:.5f} | {v['A0']['M1']['A0']:.4f} | {v['M1_row']} |")
v=r['h2']['R1_pixel_fb48']
a('\nPer-type AUROC, primary reading:\n\n| model | '+' | '.join(v['per_type_auroc']['M1'])+' |\n|---|---|---|---|---|')
for k in ('M1','B1','B2'): a(f"| {k} | "+' | '.join(f"{x:.4f}" for x in v['per_type_auroc'][k].values())+' |')
a('\nD_k = A_M1 - A_Bk is POSITIVE because the baselines have AUROC < 0.5 (their Delta_abrupt exceeds Delta_viol): M1 beats both baselines under Holm-2, but A_M1 is about 0.55 (Not specific, all four types < 0.65). A0 (clean pairwise accuracy under the H2 aggregation): M1 '+f"{v['A0']['M1']['A0']:.4f}"+' (< 0.85), so the prereg outcome is "Detection-limited (not specific)". Pooling the types into one AUROC gives the same value as the mean of per-type AUROCs (equal n per type), so the A reading is not ambiguous in value.\n')
a('A0 detail: '+'; '.join(f"{k} A0={d['A0']:.4f} (ties {d['n_ties']}, strict {d['strict']:.4f}, CI [{d['ci'][0]:.3f},{d['ci'][1]:.3f}])" for k,d in v['A0'].items())+'.\n')
a('## 4. H3 (full-clip max; tau as H2; 180 possible videos)\n')
a('| quantity | detection | 95% cluster CI | ties | note |\n|---|---|---|---|---|')
for k,x in r['h3'].items():
    if 'det' in x: a(f"| {k} | {x['det']:.4f} | [{x['ci'][0]:.3f}, {x['ci'][1]:.3f}] | {x['n_ties']} | |")
    elif 'diff' in x: a(f"| {k} | {x['diff']:.4f} | [{x['ci'][0]:.3f}, {x['ci'][1]:.3f}] | | difference |")
    else: a(f"| {k} | tie-half {x['tiehalf']:.4f} / strict {x['strict']:.4f} | | | pairwise acc, mean aggregation, tau_mean |")
a(f"\nG2 (vflip detection (a) >= 0.80): {r['h3_G2']['vflip_a']:.4f} -> pass = {r['h3_G2']['pass_ge_0p8']}. M0r references use the init0 clean run with its own tau (M0r clean full-clip max median x 2e-4 = {r['h3']['M0r_vflip']['tau']:.3e}).\n")
a('## 5. Ties and fallbacks\n')
t=r['ties']
a(f"- M1 clean ties at tau: fp16 {t['clean_M1_fp16_mean_tau']}, fp32 {t['clean_M1_fp32_mean_tau']}; exact ties 0 in both.\n- H1 edited runs (ties at tau_mean, per seed): {t['h1_edited_ties_per_seed_at_tau_mean']}.\n- No-event fallback pairs: {t['no_event_fallback_pairs_mine']} (mine) / {t['no_event_fallback_pairs_stored_matches_meta']} (matches.json meta). Transient pairs: 2 (O3/17/p0, p1: my t_on 55 / t_off 59 vs stored 54 / 59; the one-frame difference moves the first window index from 6 to 7 for those two pairs and changes A by < 0.001).\n- H2 fraction of tie cells (|dv - da| <= tau) per model: {r['h2']['R1_pixel_fb48']['n_tie_dv_vs_da_cells_frac']}.\n")
a('## 6. Ambiguities and readings\n- t* fallback: prereg says uniform in the middle 50% (seeded); the seed/value is not in the prereg, so 48 from matches.json is used; 50 and the pair first-divergence frame (R2) and no alignment (R3) are reported; the conclusion (A about 0.55-0.58, Not specific) does not change.\n- Baseline score per window: min over C of stored B1/B2 arrays (same rule as M1); baselines use their own tau (2e-4 x median clean full-clip max of that baseline).\n- Strict accuracy: pair counted correct iff imp > pos (ties wrong). Exact-tie: tau = 0.\n- Zoom retention uses channel-mean |v-p| > 8/255; max-channel and stored values give 106 and 112 retained pairs; alt rows in JSON.\n- fps_halve tau: clean fp16 skip-2 tau (primary) vs skip-4 clean tau: identical result (flip 0).\n- Bootstrap p for flip-vs-floor is P*[(flip-f0)* <= 0]; zero means < 1e-4. H2 p floored at 1/10001.\n')
open('verify/p6_recompute.md','w').write('\n'.join(L))
