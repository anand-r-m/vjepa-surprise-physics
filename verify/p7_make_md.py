import json
r = json.load(open('verify/p7_recompute.json')); L = []; a = L.append
f = lambda x, n=4: ('%.*f' % (n, x)) if isinstance(x, (int, float)) else str(x)
ci = lambda c, n=4: '[%s, %s]' % (f(c[0], n), f(c[1], n))
a('# P7 independent recompute (verifier)\n')
a('Written BEFORE any analysis output (results/analysis/*, notes/*_RESULTS.md, src/vjepa_study/analysis, scripts/run_*) was opened. Code: verify/p7_lib.py, verify/p7_recompute.py (+ p6 pixel/event/retention caches for the zoom keep set only via kaggle/h2_spec_a/matches.json). Inputs: results/raw/<group>/results/<run>/surprise.npz, meta.json; kaggle/h2_spec_a/matches.json, kaggle/expl_onset_spec/matches.json; IntPhys 2 metadata.csv. Bootstrap: numpy default_rng seed 20261015, 10,000 draws, 30 scenes per block with replacement (IntPhys 2 Main: 253 scenes stratified by condition), common draws within a table.\n')
a('Conventions (as p6): tau_m = 2e-4 x median of 360 per-video scores (mean aggregation for clean/H1; full-clip max of clean for H2/H3); tie-half primary; strict = d>0; flip = change among {+,0,-} at tau; H2 = event-aligned max with window w kept iff 4w+30 >= t_on (stored matches t_on, reading R1b); AUROC mean of 4 per-type AUROCs, per seed then averaged; Holm-2 on one-sided paired-bootstrap p; zoom keep set = stored support_retention_crop >= 0.9 (112 pairs).\n')
a('## 1. Clean accuracy (180 pairs, mean aggregation)\n')
a('| run | tau | tie-half | strict | ties | tie-half @ fixed 1e-4 |\n|---|---|---|---|---|---|')
for k, c in r['clean_acc'].items():
    if k == 'per_block' or 'tiehalf' not in c: continue
    a(f"| {k} | {c['tau']:.4e} | {f(c['tiehalf'])} | {f(c['strict'])} | {c['n_ties']} | {f(c['tiehalf_fixed_tau1e4'])} |")
a('\nPer block (tie-half / strict):\n\n| run | O1 | O2 | O3 |\n|---|---|---|---|')
for k, c in r['clean_acc']['per_block'].items(): a(f"| {k} | " + ' | '.join(f"{f(c[b]['tiehalf'],3)} / {f(c[b]['strict'],3)}" for b in ('O1', 'O2', 'O3')) + ' |')
a('\nPaired M1 - B2 clean (tie-half; scene-cluster bootstrap):\n')
a('| M1 run | M1 acc | B2 acc | diff | 95% CI | p (2-sided) | diff strict | CI strict |\n|---|---|---|---|---|---|---|---|')
for k, c in r['paired_M1_minus_B2'].items(): a(f"| {k} | {f(c['M_acc'])} | {f(c['B_acc'])} | {f(c['diff'])} | {ci(c['ci'])} | {f(c['p_two_sided'])} | {f(c['diff_strict'])} | {ci(c['ci_strict'])} |")
a('\n**Finding E1.** ViT-H fp16 tie-half under the prereg tau (scale-relative 1.195e-4) is %s, strict %s; the quoted 88.1%% reproduces only with the superseded fixed tau = 1e-4 (%s). fp32 P2 ViT-L: tie-half %s / strict %s (same under both taus).\n' % (f(r['clean_acc']['M1H_fp16_P2H']['tiehalf']), f(r['clean_acc']['M1H_fp16_P2H']['strict']), f(r['clean_acc']['M1H_fp16_P2H']['tiehalf_fixed_tau1e4']), f(r['clean_acc']['M1_fp32_P2']['tiehalf']), f(r['clean_acc']['M1_fp32_P2']['strict'])))
a('## 2. Precision (P2 fp32 vs P4 fp16, same 360 inputs, M1)\n')
a('```\n' + json.dumps(r['precision'], indent=1) + '\n```\n')
a('## 3. H1 high strength (M1 and M2)\n')
for M in ('M1', 'M2'):
    h = r['h1'][M]
    a(f"### {M} (tau_mean {h['tau_mean']:.4e}; dither f0 over all pairs {f(h['dither']['f0_all'])}, strict-convention f0 {f(h['dither']['f0_strict_all'])}; fps_halve identical to skip-4 clean: {h['fps_halve_identical_to_skip4_clean']})\n")
    a('| edit | n | dAcc | CI | p cluster | Holm-14 | p sign | Holm-14 sign fam | flip | f0 | flip-f0 | p flip | Holm-14 | strict flip | strict f0 |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|')
    for e, x in h['stats'].items():
        a(f"| {e} | {x['n_pairs']} | {f(x['dacc'])} | {ci(x['dacc_ci'],3)} | {f(x['p_dacc_cluster'])} | {f(x['holm_dacc'])} | {f(x['p_sign'])} | {f(x['holm_sign'])} | {f(x['flip'])} | {f(x['f0'])} | {f(x['flip_minus_f0'])} | {f(x['p_flip_vs_floor'])} | {f(x['holm_flip'])} | {f(x['flip_strict'])} | {f(x['f0_strict'])} |")
    a('')
a('## 4. H2 mid strength, stored-matches t_on (M1, M2)\n')
for M in ('M1', 'M2'):
    h = r['h2'][M]
    a(f"### {M}: outcome {h['outcome']}; A0 {f(h['A0']['M']['A0'])} {ci(h['A0']['M']['ci'])} (B1 {f(h['A0']['B1']['A0'])}, B2 {f(h['A0']['B2']['A0'])}); tau {', '.join(k + ' ' + format(v, '.4e') for k, v in h['tau'].items())}; seeds {h['nseeds']}; late-excluded {h['n_late']}\n")
    a('| set | A_M | A_B1 | A_B2 | A_M CI | D_1 [CI] | p1 | Holm-2 | D_2 [CI] | p2 | Holm-2 |\n|---|---|---|---|---|---|---|---|---|---|---|')
    for nm in ('all', 'no_lighting_global'):
        s = h[nm]; d1, d2 = s['D']['B1'], s['D']['B2']
        a(f"| {nm} | {f(s['A_point']['M'])} | {f(s['A_point']['B1'])} | {f(s['A_point']['B2'])} | {ci(s['A_ci']['M'])} | {f(d1['D'])} {ci(d1['ci'],3)} | {f(d1['p_onesided'],5)} | {f(d1['holm2'],5)} | {f(d2['D'])} {ci(d2['ci'],3)} | {f(d2['p_onesided'],5)} | {f(d2['holm2'],5)} |")
    a('\nPer-type AUROC (M / B1 / B2): ' + '; '.join(f"{t} {f(h['all']['per_type']['M'][t],3)} / {f(h['all']['per_type']['B1'][t],3)} / {f(h['all']['per_type']['B2'][t],3)}" for t in h['all']['per_type']['M']) + '\n')
e = r['h2_event_info']
a('### H2 event / matching facts (stored matches.json)\n```\n' + json.dumps(e, indent=1) + '\n```\n')
a('Global-lighting no-op counts (mid; per seed; 180 entries each): ```' + json.dumps(r['lg_noop']) + '```\n')
a('## 5. H3 positive controls (full-clip max; tau from clean full-clip max; M0r tau its own)\n')
for M in ('M1', 'M2'):
    h = r['h3'][M]
    a(f"### {M} (tau {h['tau']:.4e}; G2 pass: {h['G2_pass']})\n")
    a('| quantity | value | 95% CI |\n|---|---|---|')
    for k, v in h.items():
        if isinstance(v, dict) and 'det' in v: a(f"| {k} | {f(v['det'])} | {ci(v['ci'])} |")
        elif isinstance(v, dict) and 'diff' in v: a(f"| {k} | {f(v['diff'])} | {ci(v['ci'])} |")
        elif isinstance(v, dict) and 'tiehalf' in v: a(f"| {k} (tie-half / strict) | {f(v['tiehalf'])} / {f(v['strict'])} | |")
    a('')
a('## 6. (B) M1 specificity dose-response (low 0.5x / mid 1x / high 2x)\n')
a('| level | A (pooled) | CI | A_B1 | A_B2 | D_1 | Holm-6 | D_2 | Holm-6 | A0 | outcome |\n|---|---|---|---|---|---|---|---|---|---|---|')
for lv, h in r['h2_dose_M1'].items():
    s = h['all']; a(f"| {lv} | {f(s['A_point']['M'])} | {ci(s['A_ci']['M'])} | {f(s['A_point']['B1'])} | {f(s['A_point']['B2'])} | {f(s['D']['B1']['D'])} | {f(s['D']['B1']['holm6'],5)} | {f(s['D']['B2']['D'])} | {f(s['D']['B2']['holm6'],5)} | {f(h['A0']['M']['A0'])} | {h['outcome']} |")
a('\nPer type (A_M, D_1, D_2, Holm-24 of each):\n\n| level | type | A_M | D_1 | Holm-24 | D_2 | Holm-24 |\n|---|---|---|---|---|---|---|')
for lv, h in r['h2_dose_M1'].items():
    for t, v in h['per_type_D'].items(): a(f"| {lv} | {t} | {f(v['B1']['A'])} | {f(v['B1']['D'])} | {f(v['B1']['holm24'],5)} | {f(v['B2']['D'])} | {f(v['B2']['holm24'],5)} |")
a('\n## 7. (B) M1 H1 dose-response (dAcc, flip; f0 over the same pairs; Holm-30 over 15 dAcc + 15 flip tests)\n')
a('| cell | n | dAcc | CI | p cluster | Holm-30 | flip | f0 | flip-f0 | p flip | Holm-30 |\n|---|---|---|---|---|---|---|---|---|---|---|')
for c, x in r['h1_dose_M1'].items():
    a(f"| {c} | {x['n_pairs']} | {f(x['dacc'])} | {ci(x['dacc_ci'],3)} | {f(x['p_dacc_cluster'])} | {f(x.get('holm30_dacc','-'))} | {f(x['flip'])} | {f(x['f0'])} | {f(x['flip_minus_f0'])} | {f(x['p_flip_vs_floor'])} | {f(x.get('holm30_flip','-'))} |")
a('\n## 8. (C) EXPLORATORY: onset-aligned specificity and halve_hold\n')
o = r['expl_onset']; s = o['all']
a(f"Onset-aligned (t_on from kaggle/expl_onset_spec/matches.json; same tau): outcome {o['outcome']}; A {f(s['A_point']['M'])} {ci(s['A_ci']['M'])}; A_B1 {f(s['A_point']['B1'])}; A_B2 {f(s['A_point']['B2'])}; A0 M {f(o['A0']['M']['A0'])} {ci(o['A0']['M']['ci'])} (B1 {f(o['A0']['B1']['A0'])}, B2 {f(o['A0']['B2']['A0'])}); D_1 {f(s['D']['B1']['D'])} {ci(s['D']['B1']['ci'],3)} p {f(s['D']['B1']['p_onesided'],5)} Holm-2 {f(s['D']['B1']['holm2'],5)}; D_2 {f(s['D']['B2']['D'])} {ci(s['D']['B2']['ci'],3)} p {f(s['D']['B2']['p_onesided'],5)} Holm-2 {f(s['D']['B2']['holm2'],5)}; without lighting_global A {f(o['no_lighting_global']['A_point']['M'])}; per type {json.dumps({k: round(v, 4) for k, v in s['per_type']['M'].items()})}; events {o['event_info']}; mid ratio in band {o['mid_ratio_in_band']}; seeds {o['nseeds']}\n")
h = r['expl_halve_hold']
a(f"halve_hold vs clean skip-2 (EXPLORATORY): n {h['n_pairs']}, dAcc {f(h['ddacc'] if 'dacc' not in h else h['dacc'])} CI {ci(h['dacc_ci'],3)} p_cluster {f(h['p_dacc_cluster'])}; flip {f(h['flip'])}; f0 {f(h['f0'])}; flip-f0 {f(h['flip_minus_f0'])} CI {ci(h['flip_minus_f0_ci'],3)} p_flip {f(h['p_flip_vs_floor'])}; acc edit {f(h['acc_edit_tiehalf'])} vs clean {f(h['acc_clean_tiehalf'])}; strict flip {f(h['flip_strict'])} vs strict f0 {f(h['f0_strict'])}\n")
a('## 9. (D) IntPhys 2 Main, M1 clean fp16 (506 pairs)\n')
m = r['ip2_main']
a(f"{m['n_videos']} videos, {m['n_pairs']} pairs, {m['n_scenes']} scenes, blocks {m['n_blocks']}; {m['n_debug_name_overlap_videos']} videos share a name with Debug ({m['n_pairs_with_debug_overlap']} pairs affected).\n")
a('| score | set | n | tau | tie-half [CI] | strict [CI] | ties | continuity | immutability | permanence | solidity |\n|---|---|---|---|---|---|---|---|---|---|---|')
for k in ('M1', 'B1', 'B2', 'B3'):
    for st in ('all', 'without_debug_overlap'):
        x = m[k][st]; pb = x['per_block']
        a(f"| {k} | {st} | {x['n']} | {x['tau']:.3e} | {f(x['tiehalf'])} {ci(x['tiehalf_ci'],3)} | {f(x['strict'])} {ci(x['strict_ci'],3)} | {x['n_ties']} | " + ' | '.join(f"{f(pb[b]['tiehalf'],3)} / {f(pb[b]['strict'],3)}" for b in ('continuity', 'immutability', 'permanence', 'solidity')) + ' |')
a('\n## 10. (E) G1\' ladder facts\n')
g = r['g1prime']
for k in ('P2_fp32_M1', 'P2H_fp16_M1H', 'P2_B1', 'P2_B2', 'P2_B3'):
    c = g[k]; a(f"- {k}: tau {c['tau']:.4e}, tie-half {f(c['tiehalf'])}, strict {f(c['strict'])}, ties {c['n_ties']}, tie-half at fixed 1e-4 {f(c['tiehalf_fixed_tau1e4'])}")
a(f"- precisions from run meta: P2 {g['P2_meta_precision']}, ViT-H {g['M1H_runs_meta']}, P4 M1 {g['M1_P4_meta_precision']}. b1_whole_window stored in npz: {g['b1_whole_window_available']} (not recomputable from the arrays).")
open('verify/p7_recompute.md', 'w').write('\n'.join(L) + '\n')
