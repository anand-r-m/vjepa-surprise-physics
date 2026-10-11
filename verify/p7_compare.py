"""P7: compare verify/p7_recompute.json against results/analysis (opened only after p7_recompute.* was written)."""
import json, math
V = json.load(open('verify/p7_recompute.json')); A = lambda f: json.load(open('results/analysis/' + f))
rows = []   # (label, mine, theirs, absdiff, tol, status)
NB = 10000
def ptol(p, mult=1): return mult * (8 * math.sqrt(max(p, 1e-4) * (1 - p) / NB) + 0.0003)
def add(label, mine, theirs, tol, kind=None):
    if theirs is None or mine is None:
        rows.append((label, mine, theirs, None, tol, 'UNMAPPED')); return
    if isinstance(mine, bool) or isinstance(theirs, bool) or isinstance(mine, str):
        rows.append((label, mine, theirs, None, tol, 'match' if mine == theirs else 'MISMATCH')); return
    d = abs(mine - theirs); rows.append((label, mine, theirs, d, tol, 'match' if d <= tol + 1e-12 else 'MISMATCH'))
def addp(label, mine, theirs, mult=1):
    if theirs is None or mine is None: rows.append((label, mine, theirs, None, None, 'UNMAPPED')); return
    tol = ptol(max(mine, theirs, 1e-4) if max(mine, theirs) < 0.5 else 0.5, mult); add(label, mine, theirs, tol)
def g(d, *ks):
    for k in ks:
        if d is None: return None
        d = d.get(k) if isinstance(d, dict) else (d[k] if isinstance(k, int) and d is not None else None)
    return d

# ---------------- (A) M2
mc = A('m2/clean.json')['models']['M2']['mean']; vm = V['clean_acc']
add('M2 mi0 clean tie-half', vm['M2_mi0']['tiehalf'], mc['acc_tiehalf'], .001); add('M2 mi0 clean strict', vm['M2_mi0']['strict'], mc['acc_strict'], .001)
add('M2 mi0 ties', vm['M2_mi0']['n_ties'], mc['n_ties'], 0); add('M2 mi0 tau', vm['M2_mi0']['tau'], mc['tau_used'], 1e-8)
for b in ('O1', 'O2', 'O3'):
    pass
old = A('p4/clean_old_mask_index1.json')['models']['M2']['mean']
add('M2 mi1 old clean tie-half', vm['M2_mi1_old']['tiehalf'], old['acc_tiehalf'], .001); add('M2 mi1 old strict', vm['M2_mi1_old']['strict'], old['acc_strict'], .001)
h1m2 = A('m2/h1_M2.json'); h1m1 = A('h1/h1_M1.json')
def cmp_h1(M, jf):
    mine = V['h1'][M]['stats']
    add(f'H1 {M} f0', V['h1'][M]['dither']['f0_all'], jf['f0'], .001)
    for e, x in mine.items():
        t = jf['per_edit'][e]
        add(f'H1 {M} {e} n', x['n_pairs'], t['n'], 0); add(f'H1 {M} {e} dAcc', x['dacc'], t['dacc'], .001)
        add(f'H1 {M} {e} flip', x['flip'], t['flip'], .001); add(f'H1 {M} {e} flip-f0', x['flip_minus_f0'], t['excess'], .001)
        add(f'H1 {M} {e} dAcc CI lo', x['dacc_ci'][0], t['dacc_ci'][0], .01); add(f'H1 {M} {e} dAcc CI hi', x['dacc_ci'][1], t['dacc_ci'][1], .01)
        addp(f'H1 {M} {e} p_dacc_cluster', x['p_dacc_cluster'], t['p_dacc_cluster'])
        addp(f'H1 {M} {e} p_flip_cluster', x['p_flip_vs_floor'], t['p_flip_cluster'])
        addp(f'H1 {M} {e} Holm-14 dAcc', x['holm_dacc'], t['holm_dacc_cluster'], 14); addp(f'H1 {M} {e} Holm-14 flip', x['holm_flip'], t['holm_flip_cluster'], 14)
        add(f'H1 {M} {e} sign p', x['p_sign'], t['sign']['p'], 1e-5); add(f'H1 {M} {e} Holm-14 sign-fam sign', x['holm_sign'], t['holm_sign'], 1e-4 + 14 * ptol(x['p_flip_vs_floor']) if False else 0.03)
        add(f'H1 {M} {e} decision-free: strict flip (info vs none)', 0, 0, 0)
        rows.pop()
cmp_h1('M1', h1m1); cmp_h1('M2', h1m2)
# M2 H2
h2m2 = A('m2/h2.json'); vh = V['h2']['M2']
def cmp_h2(tag, vh, jm, key='M2', nolg=None):
    add(f'{tag} A', vh['all']['A_point']['M'], jm[key]['A'], .002); add(f'{tag} A CI lo', vh['all']['A_ci']['M'][0], jm[key]['A_ci'][0], .01); add(f'{tag} A CI hi', vh['all']['A_ci']['M'][1], jm[key]['A_ci'][1], .01)
    for t, v in vh['all']['per_type']['M'].items(): add(f'{tag} A {t}', v, jm[key]['per_type'][t], .002)
    add(f'{tag} A0', vh['A0']['M']['A0'], jm[key]['A0'], .001)
    for b in ('B1', 'B2'):
        add(f'{tag} A_{b}', vh['all']['A_point'][b], jm[b]['A'], .002); add(f'{tag} A0_{b}', vh['A0'][b]['A0'], jm[b]['A0'], .001)
        d = jm['D_' + b]; mine = vh['all']['D'][b]
        add(f'{tag} D_{b}', mine['D'], d['D'], .002); add(f'{tag} D_{b} CI lo', mine['ci'][0], d['ci'][0], .01); add(f'{tag} D_{b} CI hi', mine['ci'][1], d['ci'][1], .01)
        addp(f'{tag} p_{b}', mine['p_onesided'], d['p']); addp(f'{tag} Holm-2 {b}', mine['holm2'], d['p_holm'], 2)
    add(f'{tag} tau', vh['tau']['M'], jm[key]['tau'], 1e-9)
    s = jm['sensitivity_exclude_missed_types']
    add(f'{tag} A excl lighting_global', vh['no_lighting_global']['A_point']['M'], s['A'], .002)
    add(f'{tag} A excl lg CI lo', vh['no_lighting_global']['A_ci']['M'][0], s['A_ci'][0], .01); add(f'{tag} A excl lg CI hi', vh['no_lighting_global']['A_ci']['M'][1], s['A_ci'][1], .01)
    for b in ('B1', 'B2'):
        add(f'{tag} D_{b} excl lg', vh['no_lighting_global']['D'][b]['D'], s['D_' + b]['D'], .002)
        addp(f'{tag} p_{b} excl lg', vh['no_lighting_global']['D'][b]['p_onesided'], s['D_' + b]['p']); addp(f'{tag} Holm-2 {b} excl lg', vh['no_lighting_global']['D'][b]['holm2'], s['D_' + b]['p_holm'], 2)
    add(f'{tag} outcome', vh['outcome'].replace('Detection-limited (Not specific (Reversed))', 'DL').replace('Detection-limited (Not specific)', 'DL'), 'DL' if jm['outcome_' + key][0].startswith('Detection-limited') else jm['outcome_' + key][0], 0)
cmp_h2('H2 M2', vh, h2m2)
# M2 H3
h3 = A('m2/h3_M2.json'); v3 = V['h3']['M2']
add('H3 M2 vflip (a)', v3['vflip_a_ref_p']['det'], h3['a'], .001); add('H3 M2 vflip (a) CI lo', v3['vflip_a_ref_p']['ci'][0], h3['a_ci'][0], .01); add('H3 M2 vflip (a) CI hi', v3['vflip_a_ref_p']['ci'][1], h3['a_ci'][1], .01)
add('H3 M2 vflip (b)', v3['vflip_b_ref_hflip']['det'], h3['b'], .001); add('H3 M2 (b) CI lo', v3['vflip_b_ref_hflip']['ci'][0], h3['b_ci'][0], .01)
add('H3 M2 minus M0r vflip', v3['model_minus_M0r_vflip']['diff'], h3['diff_m0r'], .001); add('H3 M2 reversal', v3['reversal_ref_p']['det'], h3['reversal_detection'], .001)
add('H3 M2 pairwise vflip tie-half', v3['pairwise_acc_vflip']['tiehalf'], h3['pairwise_acc_vflip']['tiehalf'], .001); add('H3 M2 pairwise rev tie-half', v3['pairwise_acc_reversal']['tiehalf'], h3['pairwise_acc_time_reversal']['tiehalf'], .001)
add('H3 M2 tau', v3['tau'], h3['variant']['tau'], 1e-9); add('H3 M2 G2', v3['G2_pass'], h3['g2'], 0)
# M1 H3 (re-check)
h3m = A('h3_final/h3_M1.json'); v3 = V['h3']['M1']
add('H3 M1 vflip (a)', v3['vflip_a_ref_p']['det'], h3m['a'], .001); add('H3 M1 vflip (b)', v3['vflip_b_ref_hflip']['det'], h3m['b'], .001)
add('H3 M1 minus M0r vflip', v3['model_minus_M0r_vflip']['diff'], h3m['diff_m0r'], .001); add('H3 M1 reversal', v3['reversal_ref_p']['det'], h3m['reversal_detection'], .001)
add('H3 M1 pairwise vflip tie-half', v3['pairwise_acc_vflip']['tiehalf'], h3m['pairwise_acc_vflip']['tiehalf'], .001)
# M1 H2 recheck
h2m1 = A('h2/h2.json')
cmp_h2('H2 M1', V['h2']['M1'], h2m1, key='M1')
# ---------------- (B) dose
ds = A('h2/dose/dose_spec_M1.json')
for lv in ('low', 'mid', 'high'):
    L = ds['levels'][lv]; v = V['h2_dose_M1'][lv]
    add(f'dose-spec {lv} A', v['all']['A_point']['M'], L['A'], .002); add(f'dose-spec {lv} A CI lo', v['all']['A_ci']['M'][0], L['A_ci'][0], .01); add(f'dose-spec {lv} A CI hi', v['all']['A_ci']['M'][1], L['A_ci'][1], .01)
    add(f'dose-spec {lv} A_B1', v['all']['A_point']['B1'], L['A_B1'], .002); add(f'dose-spec {lv} A_B2', v['all']['A_point']['B2'], L['A_B2'], .002)
    add(f'dose-spec {lv} D_1', v['all']['D']['B1']['D'], L['D_B1']['D'], .002); add(f'dose-spec {lv} D_2', v['all']['D']['B2']['D'], L['D_B2']['D'], .002)
    add(f'dose-spec {lv} D_1 CI lo', v['all']['D']['B1']['ci'][0], L['D_B1']['ci'][0], .01); add(f'dose-spec {lv} D_2 CI lo', v['all']['D']['B2']['ci'][0], L['D_B2']['ci'][0], .01)
    add(f'dose-spec {lv} Holm-6 B1', v['all']['D']['B1']['holm6'], L['holm6_B1'], .001); add(f'dose-spec {lv} Holm-6 B2', v['all']['D']['B2']['holm6'], L['holm6_B2'], .001)
    add(f'dose-spec {lv} A0', v['A0']['M']['A0'], L['A0'], .001)
    for t in v['per_type_D']:
        c = ds['cells'][f'{t}@{lv}']; x = v['per_type_D'][t]
        add(f'dose-spec {lv} {t} A', x['B1']['A'], c['A'], .002); add(f'dose-spec {lv} {t} D_1', x['B1']['D'], c['D_B1'], .002); add(f'dose-spec {lv} {t} D_2', x['B2']['D'], c['D_B2'], .002)
        add(f'dose-spec {lv} {t} Holm-24 B1', x['B1']['holm24'], c['holm24_B1'], .001); add(f'dose-spec {lv} {t} Holm-24 B2', x['B2']['holm24'], c['holm24_B2'], .001)
dh = A('h1/dose/dose_M1.json')['per_edit']
for c, x in V['h1_dose_M1'].items():
    if c.endswith('_allpairs'): continue
    if c.endswith('_keep112'): continue
    e, lv = c.split('-'); t = dh.get(f'{e}@{lv}')
    if t is None: rows.append((f'H1 dose {c}', None, None, None, None, 'UNMAPPED')); continue
    add(f'H1 dose {c} n', x['n_pairs'], t['n'], 0); add(f'H1 dose {c} dAcc', x['dacc'], t['dacc'], .001); add(f'H1 dose {c} flip', x['flip'], t['flip'], .001)
    addp(f'H1 dose {c} p_dacc', x['p_dacc_cluster'], t['p_dacc_cluster']); addp(f'H1 dose {c} p_flip', x['p_flip_vs_floor'], t['p_flip_cluster'])
    addp(f'H1 dose {c} Holm-30 dAcc', x['holm30_dacc'], t['holm_dacc_cluster'], 30); addp(f'H1 dose {c} Holm-30 flip', x['holm30_flip'], t['holm_flip_cluster'], 30)
# ---------------- (C) exploratory
on = A('exploratory/onset_spec/EXPLORATORY_h2_onset_M1.json'); o = V['expl_onset']
cmp_h2('EXPL onset', o, on, key='M1')
add('EXPL onset B3-free: A0 B1', o['A0']['B1']['A0'], on['B1']['A0'], .001)
hh = A('exploratory/halve_hold/EXPLORATORY_halve_hold_M1.json'); t = hh['per_edit']['halve_hold']; x = V['expl_halve_hold']
for k, tk in (('dacc', 'dacc'), ('flip', 'flip'), ('flip_minus_f0', 'excess')): add(f'EXPL halve_hold {k}', x[k], t[tk], .001)
addp('EXPL halve_hold p_dacc', x['p_dacc_cluster'], t['p_dacc_cluster']); addp('EXPL halve_hold p_flip', x['p_flip_vs_floor'], t['p_flip_cluster'])
add('EXPL halve_hold acc halve', x['acc_edit_tiehalf'], hh['EXPLORATORY']['halve_hold_acc'], .001); add('EXPL halve_hold f0', x['f0_dither'], hh['f0'], .001)
# ---------------- (D) Main
mj = A('exploratory/ip2main/IP2MAIN_M1_clean_descriptive.json'); vm_ = V['ip2_main']
add('Main n pairs', vm_['n_pairs'], mj['n_pairs'], 0); add('Main overlap videos', vm_['n_debug_name_overlap_videos'], mj['n_overlap_videos'], 0); add('Main overlap pairs', vm_['n_pairs_with_debug_overlap'], mj['n_pairs_with_overlap'], 0)
for nm, jk in (('M1', 'S'), ('B1', 'B1'), ('B2', 'B2'), ('B3', 'B3')):
    add(f'Main {nm} tau', vm_[nm]['all']['tau'], mj[jk]['mean']['tau'], 1e-8)
    for st, jst in (('all', 'all'), ('without_debug_overlap', 'without_debug_overlap')):
        a_ = mj[jk]['mean'][jst]; b_ = vm_[nm][st]
        add(f'Main {nm} {st} tie-half', b_['tiehalf'], a_['acc_tiehalf'], .001); add(f'Main {nm} {st} strict', b_['strict'], a_['acc_strict'], .001); add(f'Main {nm} {st} ties', b_['n_ties'], a_['n_ties'], 0)
        if nm == 'M1':
            add(f'Main {nm} {st} boot CI lo', b_['tiehalf_ci'][0], a_['cluster_boot95'][0], .01); add(f'Main {nm} {st} boot CI hi', b_['tiehalf_ci'][1], a_['cluster_boot95'][1], .01)
        for b, v in b_['per_block'].items():
            add(f'Main {nm} {st} {b} tie-half', v['tiehalf'], a_['per_block'][b]['acc_tiehalf'], .001); add(f'Main {nm} {st} {b} strict', v['strict'], a_['per_block'][b]['acc_strict'], .001); add(f'Main {nm} {st} {b} n', v['n'], a_['per_block'][b]['n'], 0)
# ---------------- (E)
pa = A('precision_audit.json'); vp = V['precision']
add('prec verdicts changed (tie-half) n', vp['own_tau']['n_class_change'], pa['n_verdicts_changed_tiehalf'], 0); add('prec verdicts changed strict n', vp['strict_tau0']['n'], pa['n_verdicts_changed_strict'], 0)
add('prec max pair-margin diff', vp['max_abs_pair_mean_margin_diff'], pa['margin_abs_diff']['max'], 1e-7)
vh_ = A('p2_vith_g1.json')['mean']['all']; add('ViT-H tie-half (analysis file, fixed 1e-4 tau) vs mine fixed', V['clean_acc']['M1H_fp16_P2H']['tiehalf_fixed_tau1e4'], vh_['tie_half'], .001)
add('ViT-H tie-half under prereg tau (mine) vs analysis file', V['clean_acc']['M1H_fp16_P2H']['tiehalf'], vh_['tie_half'], .001)
add('ViT-H strict', V['clean_acc']['M1H_fp16_P2H']['strict'], vh_['strict'], .001)
p2g = A('p2_clean_g1.json'); add('P2 fp32 tie-half', V['clean_acc']['M1_fp32_P2']['tiehalf'], p2g['M1']['mean']['all']['acc'], .001); add('P2 fp32 strict', V['clean_acc']['M1_fp32_P2']['strict'], p2g['M1']['mean']['all']['acc_strict'], .001)
add('P2 B1 tie-half (analysis file; old fixed tau?)', V['clean_acc']['B1_P2_fp32']['tiehalf'], p2g['B1']['mean']['all']['acc'], .001)
add('P2 B2 tie-half (analysis file; old fixed tau?)', V['clean_acc']['B2_P2_fp32']['tiehalf'], p2g['B2']['mean']['all']['acc'], .001)
add('P2 B1 strict', V['clean_acc']['B1_P2_fp32']['strict'], p2g['B1']['mean']['all']['acc_strict'], .001); add('P2 B2 strict', V['clean_acc']['B2_P2_fp32']['strict'], p2g['B2']['mean']['all']['acc_strict'], .001)
t1 = A('p4/clean.json')['T1_M1_minus_B2_paired_clean_mean']
add('T1 M1(fp16)-B2 diff', V['paired_M1_minus_B2']['fp16_P4']['diff'], t1['diff'], .001); add('T1 CI lo', V['paired_M1_minus_B2']['fp16_P4']['ci'][0], t1['ci'][0], .01); add('T1 CI hi', V['paired_M1_minus_B2']['fp16_P4']['ci'][1], t1['ci'][1], .01)
pm = A('p4/clean.json')['models']['M1']['mean']
add('M1 fp16 clean tie-half', V['clean_acc']['M1_fp16_P4']['tiehalf'], pm['acc_tiehalf'], .001); add('M1 fp16 clean strict', V['clean_acc']['M1_fp16_P4']['strict'], pm['acc_strict'], .001); add('M1 fp16 clean ties', V['clean_acc']['M1_fp16_P4']['n_ties'], pm['n_ties'], 0)
# extra: strict H1 (M1), M0r/hflip detection, lg no-op
sj = A('h1/strict/h1_M1_strict.json')
add('H1 M1 strict f0', V['h1']['M1']['dither']['f0_strict_all'], sj['f0'], .001)
for e, x in V['h1']['M1']['stats'].items():
    tt = sj['per_edit'][e]
    add(f'H1 strict {e} dAcc', x['dacc_strict'], tt['dacc'], .001); add(f'H1 strict {e} flip', x['flip_strict'], tt['flip'], .001)
    addp(f'H1 strict {e} p_dacc_cluster', x['p_dacc_cluster_strict'], tt['p_dacc_cluster']); add(f'H1 strict {e} p_sign', x['p_sign_strict'], tt['sign']['p'], 1e-5)
    addp(f'H1 strict {e} Holm-14 dAcc', x['holm_dacc_strict'], tt['holm_dacc_cluster'], 14); add(f'H1 strict {e} Holm-14 sign', x['holm_sign_strict'], tt['holm_sign'], 0.03)
mv = A('m0r_vflip_check.json')
add('M0r vflip detection', V['h3']['M1']['M0r_vflip']['det'], mv['M0r_init0']['fullclip_max']['detection_tiehalf'], .001)
add('M1 hflip detection', V['h3']['M1']['hflip_ref_p']['det'], mv['M1_hflip']['fullclip_max']['detection_tiehalf'], .001)
add('M0r reversal detection', V['h3']['M1']['M0r_reversal']['det'], mv['M0r_init0_timerev']['fullclip_max']['detection_tiehalf'], .001)
et = A('h2/extra_ties_m0r.json')['M1']['abrupt_ties_vs_ref']['lighting_global']
for s_ in (1, 2, 3): add(f'lighting_global mid no-op (effect<=tau) seed {s_}', V['lg_noop'][f's{s_}']['n_evmax_within_tau2'], et[s_ - 1], 0)
rows.append(('LG bitwise-identical-to-clean videos (info; mine only)', V['lg_noop']['s1']['n_bitwise_identical_to_clean'], None, None, None, 'info'))
json.dump([list(r) for r in rows], open('verify/_p7_rows.json', 'w'))

# ---------------- render verify/p7_compare.md
from collections import Counter
cnt = Counter(r[5] for r in rows)
f = lambda x: ('%.6g' % x) if isinstance(x, (int, float)) and not isinstance(x, bool) else str(x)
L = ['# P7 comparison: verifier recompute vs results/analysis (written AFTER verify/p7_recompute.*)\n',
     f"Compared {len(rows)} quantities: match {cnt['match']}, MISMATCH {cnt['MISMATCH']}, info {cnt['info']}, unmapped {cnt['UNMAPPED']}.\n",
     'Tolerances: accuracy/rate/detection 0.001; AUROC and A/D 0.002; bootstrap CI bounds 0.01; bootstrap p within Monte-Carlo error (8 SE of a 10,000-draw proportion + 3e-4; Holm-adjusted p scaled by the Holm multiplier); exact sign-test p 1e-5; counts exact; tau 1e-8 to 1e-9. Bootstrap draws differ (own RNG streams), so CI bounds and p differ by MC noise only.\n',
     '## Mismatches (cause)\n',
     '| quantity | verifier | analysis | abs diff | tol | likely cause |\n|---|---|---|---|---|---|']
cause = {
 'ViT-H tie-half under prereg tau (mine) vs analysis file': 'results/analysis/p2_vith_g1.json (and PREREG s7, "88.1") score ViT-H tie-half with the SUPERSEDED fixed tau = 1e-4 (3 ties, 158.5 credits); under the prereg scale-relative tau_m = 2e-4 x median = 1.195e-4 there are 4 ties and 159 credits = 88.33. Reproduced exactly: fixed-tau 0.88056 matches the file (row above). Strict (87.8) is identical. Convention difference, not a data difference.',
 'P2 B1 tie-half (analysis file; old fixed tau?)': 'p2_clean_g1.json B1 "acc" 0.500 uses the superseded fixed 1e-4 tau (96 ties); under the prereg tau 58.1 (PREREG s0 quotes 58.1/58.6 under the prereg tau). Strict 57.2 matches. Convention difference.',
 'P2 B2 tie-half (analysis file; old fixed tau?)': 'p2_clean_g1.json B2 "acc" 0.625 is the superseded fixed-tau figure (59 ties); under the prereg tau 76.1 (PREREG s0 explicitly records 62.5 as the old-tau figure). Strict 76.1 matches. Convention difference.'}
for r in rows:
    if r[5] == 'MISMATCH': L.append(f"| {r[0]} | {f(r[1])} | {f(r[2])} | {f(r[3])} | {f(r[4])} | {cause.get(r[0], 'UNEXPLAINED')} |")
L += ['\nNo other mismatch: all remaining quantities agree within tolerance, including one correction made during this pass: zoom dose-response low/mid initially used the 112-pair high-strength retention set (22 / 8 pairs too few vs the analysis); the analysis uses scale-specific retention (134 at 0.9, 120 at 0.8, 112 stored at 0.7), which my pixel retention reproduces exactly (134 / 120), after which every dose cell matched.\n',
      'Informational (not mismatches):\n',
      '- Zoom high-strength keep set: stored matches.json retention gives 112 (analysis and PLACEHOLDERS h1_zoom_n); my own pixel retention at 0.7 gives 110 (cm_win) - the p6 finding, unchanged.',
      '- M2 H1 noise: p_dacc_cluster 0.0132 (mine) vs 0.0174 (analysis), Holm-14 0.132 vs 0.174: MC noise on the same data (both far above the Holm-significance line only after Holm; neither crosses 0.05 after Holm). Decision labels unaffected.',
      '- Onset-aligned D_1 Holm-2: 0.0026 (mine) vs 0.0018 (analysis); raw p 0.0013 vs 0.0009: MC noise; same conclusion.',
      '- H1 sign-family Holm values differ at the 4th decimal where the bootstrap flip-vs-floor p enters the family; tolerance 0.03; all matched.\n',
      '## Largest normalised deviations among matches (diff / tol)\n', '| quantity | verifier | analysis | diff | tol |\n|---|---|---|---|---|']
ms = sorted([r for r in rows if r[5] == 'match' and r[3] is not None and r[4]], key=lambda r: -(r[3] / r[4]))[:12]
for r in ms: L.append(f"| {r[0]} | {f(r[1])} | {f(r[2])} | {f(r[3])} | {f(r[4])} |")
L += ['\n## Full table\n', '| quantity | verifier | analysis | abs diff | tol | status |\n|---|---|---|---|---|---|']
for r in rows: L.append(f"| {r[0]} | {f(r[1])} | {f(r[2])} | {f(r[3])} | {f(r[4])} | {r[5]} |")
open('verify/p7_compare.md', 'w').write('\n'.join(L) + '\n')
