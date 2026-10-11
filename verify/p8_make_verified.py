"""Appends P8 entries to results/VERIFIED.json from verify/p8_recompute.json (verifier code) with statuses from verify/_p8_rows.json."""
import json, datetime, copy
V = json.load(open('verify/p8_recompute.json')); ROWS = {r[0]: r for r in json.load(open('verify/_p8_rows.json'))}
D = json.load(open('results/VERIFIED.json')); E = D['entries']; have = {e['key'] for e in E}
pc = lambda x: round(100 * x, 2); r4 = lambda x: round(x, 4)
def st(labels):
    if not labels: return 'info-only'
    out = [ROWS[l][5] for l in labels if l in ROWS]
    if not out: return 'info-only'
    if any(o == 'MISMATCH' for o in out): return 'mismatch'
    if all(o == 'match' for o in out): return 'verified'
    return 'info-only'
new = []
def add(key, value, labels=None, ci=None, src=None, tol=None, unit=None, note=None, exploratory=False, status=None, display=None):
    assert key not in have, key
    have.add(key)
    d = dict(key=key, value=value, ci=ci, unit=unit, sources=src or [], tolerance=tol, status=status or st(labels), exploratory=exploratory)
    if display is not None: d['display'] = display
    if note: d['note'] = note
    if labels: d['compared_with'] = 'results/analysis (labels in verify/p8_compare.md): ' + '; '.join(labels[:4]) + (' ...' if len(labels) > 4 else '')
    new.append(d)

# ---------- (1a) M2 H1 dose
meta = V['h1_dose_M2_meta']
add('m2.dose.h1.f0_pct', pc(meta['f0']), ['M2 dose H1 asrun f0'], unit='%', tol='0.1 pp', src=['P4_M2_ipdev_dither-on_s1..3'], note='M2 dither floor f0 (mean over 3 dither seeds, tie-half, tau_mean %.4e); reference 24.6%%' % meta['tau_mean'])
add('m2.dose.h1.f0_pct_strict', pc(meta['f0_strict']), ['M2 dose H1 asrun strict f0'], unit='%', tol='0.1 pp', note='strict convention (tau = 0) f0 = 17.4%')
FAM = ('Holm FAMILY ACTUALLY USED = 22 p-values (11 existing M2 cells x {dAcc cluster p, flip-vs-floor p}); the key name holm30 follows the M1 pattern the table script reads but M2 has only 11 cells (jpeg and zoom exist at high only), so Holm-22, not Holm-30. '
       'Tie-half convention (prereg tau_mean %.4e), M2 descriptive (H1-ineligible). Seeds: low/mid = seed 1 only; brightness/noise/blur-high 3/3/1 seeds as in h1.M2 (blur, jpeg, zoom high have 1 seed).' % meta['tau_mean'])
for c, x in V['h1_dose_M2'].items():
    e, lv = c.split('-'); k = f'm2.dose.h1.{e}.{lv}'; T = f'M2 dose H1 asrun {c}'
    s1 = V['h1_dose_M2_seed1only'][c]; src = [f'P4_M2_ipdev_{c}_s1' + ('..3' if x['n_runs'] > 1 else ''), 'P4_M2_ipdev_clean-mi0_s1', 'P4_M2_ipdev_dither-on_s1..3']
    add(k + '.n', x['n_pairs'], [T + ' n'], unit='pairs', tol='exact', src=src)
    add(k + '.dacc_pp', pc(x['dacc']), [T + ' dAcc', T + ' dAcc CI lo', T + ' dAcc CI hi'], ci=[pc(x['dacc_ci'][0]), pc(x['dacc_ci'][1])], unit='pp', tol='0.1 pp (CI 1 pp)', src=src, note=FAM)
    add(k + '.flip_pct', pc(x['flip']), [T + ' flip', T + ' flip CI lo', T + ' flip CI hi'], ci=[pc(x['flip_ci'][0]), pc(x['flip_ci'][1])], unit='%', tol='0.1 pp', src=src, note='tie-half 3-way verdict flip vs clean; CI scene-cluster bootstrap')
    add(k + '.flip_minus_f0_pp', pc(x['flip_minus_f0']), [T + ' flip-f0'], ci=[pc(x['flip_minus_f0_ci'][0]), pc(x['flip_minus_f0_ci'][1])], unit='pp', tol='0.1 pp', src=src)
    add(k + '.holm30_dacc', r4(x['holm22_dacc']), [T + ' Holm-22 dAcc'], unit='p', tol='Holm x MC', src=src, note=FAM)
    add(k + '.holm30_flip', r4(x['holm22_flip']), [T + ' Holm-22 flip'], unit='p', tol='Holm x MC', src=src, note=FAM)
    Ts = f'M2 dose H1 asrun strict {c}'
    add(k + '.dacc_pp_strict', pc(x['dacc_strict']), [Ts + ' dAcc'], unit='pp', tol='0.1 pp', src=src, note='STRICT convention (tau = 0, ties not credited), not the primary; f0 strict 17.4%')
    add(k + '.flip_pct_strict', pc(x['flip_strict']), [Ts + ' flip'], unit='%', tol='0.1 pp', src=src, note='STRICT convention')
    add(k + '.holm22_dacc_strict', r4(x['holm22_dacc_strict']), [Ts + ' Holm-22 dAcc'], unit='p', tol='Holm x MC', src=src, note='STRICT convention; family 22')
    add(k + '.holm22_flip_strict', r4(x['holm22_flip_strict']), [Ts + ' Holm-22 flip'], unit='p', tol='Holm x MC', src=src, note='STRICT convention; family 22')
    T1 = f'M2 dose H1 s1 {c}'
    add(k + '.s1.dacc_pp', pc(s1['dacc']), [T1 + ' dAcc'], ci=[pc(s1['dacc_ci'][0]), pc(s1['dacc_ci'][1])], unit='pp', tol='0.1 pp', src=src, note='seed 1 only at EVERY cell (the analysis "s1" primary dose reading; differs from the as-run key only for brightness-high and noise-high)')
    add(k + '.s1.flip_pct', pc(s1['flip']), [T1 + ' flip'], unit='%', tol='0.1 pp', src=src)
    add(k + '.s1.holm30_dacc', r4(s1['holm22_dacc']), [T1 + ' Holm-22 dAcc'], unit='p', tol='Holm x MC', src=src, note='seed-1-only family of 22 (NOT 30)')
    add(k + '.s1.holm30_flip', r4(s1['holm22_flip']), [T1 + ' Holm-22 flip'], unit='p', tol='Holm x MC', src=src, note='seed-1-only family of 22 (NOT 30)')
# ---------- (1b) M2 H2 dose
d2 = V['h2_dose_M2']
FAM2 = 'M2 descriptive; seed 1 only at every level (low/high exist for seed 1 only); event-aligned max, stored t_on (178/180 fallback), tie-half. Holm-24 = 12 (type, level) cells x {B1, B2}; pooled Holm-6 = 3 levels x {B1, B2}.'
for lv in ('low', 'mid', 'high'):
    m = d2[lv]['all']; T = f'M2 spec dose {lv}'; src = [f'P4_M2_ipdev_{{lighting_global,lighting_local,jolt_base,zoom_base}}-{lv}_s1', 'P4_M2_ipdev_clean-mi0_s1', 'P4_M2_ipdev_base_ref-ref_s1']
    k = f'm2.dose.h2.pooled.{lv}'
    add(k + '.A', r4(m['A_point']['M']), [T + ' A', T + ' A CI lo', T + ' A CI hi'], ci=[r4(x) for x in m['A_ci']['M']], unit='AUROC', tol='0.002', src=src, note=FAM2 + (' The 3-seed-where-available mid reading is h2.M2.A (0.4489).' if lv == 'mid' else ''))
    add(k + '.A0', r4(d2[lv]['A0']['M']['A0']), [T + ' A0'], unit='accuracy', tol='0.001', src=src)
    for j, b in ((1, 'B1'), (2, 'B2')):
        add(k + f'.D_{j}', r4(m['D'][b]['D']), [T + f' D_{b}', T + f' D_{b} CI lo', T + f' D_{b} CI hi'], ci=[r4(x) for x in m['D'][b]['ci']], unit='AUROC diff', tol='0.002', src=src)
        add(k + f'.holm6_D{j}', r4(m['D'][b]['holm6']), [T + f' Holm-6 {b}'], unit='p', tol='Holm x MC', src=src, note='pooled Holm-6 (3 levels x 2 contrasts)')
    add(k + '.A_B1', r4(m['A_point']['B1']), [T + ' A_B1'], unit='AUROC', tol='0.002', src=src); add(k + '.A_B2', r4(m['A_point']['B2']), [T + ' A_B2'], unit='AUROC', tol='0.002', src=src)
    for t in ('lighting_global', 'lighting_local', 'jolt_base', 'zoom_base'):
        x = d2[lv]['per_type_D'][t]; Tt = f'M2 spec dose {lv} {t}'; kt = f'm2.dose.h2.{t}.{lv}'
        add(kt + '.A', r4(x['B1']['A']), [Tt + ' A'], unit='AUROC', tol='0.002', src=src, note=FAM2)
        for j, b in ((1, 'B1'), (2, 'B2')):
            add(kt + f'.D_{j}', r4(x[b]['D']), [Tt + f' D_{b}', Tt + f' D_{b} CI lo', Tt + f' D_{b} CI hi'], ci=[r4(v) for v in x[b]['ci']], unit='AUROC diff', tol='0.002', src=src)
            add(kt + f'.holm24_D{j}', r4(x[b]['holm24']), [Tt + f' Holm-24 {b}'], unit='p', tol='Holm x MC', src=src, note='Holm-24 over 12 cells x 2 contrasts; MC floor 0.0024 for raw p = 1e-4')
        add(kt + '.A_B1', r4(x['B1']['A_base']), [Tt + ' D_B1'], unit='AUROC', tol='0.002', src=src); add(kt + '.A_B2', r4(x['B2']['A_base']), [Tt + ' D_B2'], unit='AUROC', tol='0.002', src=src)
# ---------- (2) ablations
for nm, ab in V['ablations'].items():
    T = f'abl {nm}'; src = ['P4_M1_ipdev_clean_s1', 'P4_M1_ipdev_{lighting_global,lighting_local,jolt_base,zoom_base}-mid_s1..3', 'P4_M1_ipdev_base_ref-ref_s1']
    if nm.startswith('A1'):
        add(f'abl.{nm}.clean_pct', pc(ab['clean']['tiehalf']), [T + ' clean'], unit='%', tol='0.1 pp', src=src, note=('full-clip max aggregation, tau from full-clip-max median; 39 ties; strict %.1f' % pc(ab['clean']['strict'])) if nm == 'A1_full_max' else 'full-clip mean aggregation = primary clean (80.8); strict %.1f' % pc(ab['clean']['strict']))
    else:
        add(f'abl.{nm}.clean_pct', pc(ab['clean_meanagg']['tiehalf']), [T + ' clean (mean agg, fixed C)'], unit='%', tol='0.1 pp', src=src, note='mean aggregation of fixed-C scores S[:, :, C]; tau = 2e-4 x median of those; strict %.1f' % pc(ab['clean_meanagg']['strict']))
    add(f'abl.{nm}.A0', r4(ab['A0']['M']['A0']), [T + ' A0'], unit='accuracy', tol='0.001', src=src, note='clean tie-half accuracy under the specificity aggregation of this row')
    add(f'abl.{nm}.A', r4(ab['A']['M']), [T + ' A', T + ' A CI lo', T + ' A CI hi'], ci=[r4(x) for x in ab['A_ci']['M']], unit='AUROC', tol='0.002', src=src, note=('H2 AUROC; full-clip aggregation uses all 180 pairs (no late-onset exclusion); ' if nm.startswith('A1') else 'H2 AUROC, event-aligned max at fixed C; baselines (B1, B2, B3) also evaluated at the same fixed C; ') + 'mid strength, seeds 1-3 averaged; tau_m = 2e-4 x median clean score of that aggregation')
    for j, b in ((1, 'B1'), (2, 'B2')):
        add(f'abl.{nm}.D_{j}', r4(ab['D'][b]['D']), [T + f' D_{b}', T + f' D_{b} CI lo', T + f' D_{b} CI hi'], ci=[r4(x) for x in ab['D'][b]['ci']], unit='AUROC diff', tol='0.002', src=src)
        add(f'abl.{nm}.holm2_D{j}', round(ab['D'][b]['holm2'], 5), [T + f' Holm-2 {b}'], unit='p', tol='MC', src=src)
    for b in ('B1', 'B2', 'B3'):
        add(f'abl.{nm}.A_{b}', r4(ab['A'][b]), [T + f' A_{b}'], ci=[r4(x) for x in ab['A_ci'][b]], unit='AUROC', tol='0.002', src=src)
    for t, v in ab['per_type']['M'].items(): add(f'abl.{nm}.A.{t}', r4(v), [T + f' A {t}'], unit='AUROC', tol='0.002', src=src)
for nm, ab in V['ablations_baseline_default'].items():
    add(f'abl.{nm}.D_1_baseline_default_minC', r4(ab['D']['B1']['D']), None, status='info-only', exploratory=True, unit='AUROC diff', note='sensitivity: D_1 with baselines kept at the default min over C while M1 uses fixed C (the primary ablation row uses fixed-C baselines too); D_2 %.4f' % ab['D']['B2']['D'])
# ---------- (3) T5 extras
for M in ('M1', 'M2'):
    b = V['h2_baselines'][M]
    for k in ('B1', 'B2', 'B3'):
        add(f't5.{M}.{k}.A', r4(b['A'][k]), [f'T5 {M} A_{k}', f'T5 {M} A_{k} CI lo', f'T5 {M} A_{k} CI hi'], ci=[r4(x) for x in b['A_ci'][k]], unit='AUROC', tol='0.002', src=[f'P4_{M}_ipdev_*-mid_s1..3'], note='H2 AUROC of the %s baseline, same matching/draws as the model; M2 runs use the M2-run baseline arrays' % k)
        add(f't5.{M}.{k}.A0', r4(b['A0'][k]['A0']), [f'T5 {M} A0_{k}'], ci=[r4(x) for x in b['A0'][k]['ci']], unit='accuracy', tol='0.001', note='clean tie-half detection accuracy under event-aligned max, own tau')
        for t, v in b['per_type'][k].items(): add(f't5.{M}.{k}.A.{t}', r4(v), [f'T5 {M} A_{k} {t}'], unit='AUROC', tol='0.002')
    for t, v in b['per_type']['M'].items(): add(f't5.{M}.M.A.{t}', r4(v), None, status='verified', unit='AUROC', note='duplicate of h2.%s.A.%s' % (M, t))
b = V['h2_baselines']['M0r']
add('t5.M0r.A', r4(b['A']), None, status='info-only', exploratory=True, ci=[r4(x) for x in b['A_ci']], unit='AUROC', src=['P4_M0r_ipdev_*-mid_s1', 'P4_M0r_ipdev_clean-init0_s1'], note='M0r (random init 0) H2 AUROC, seed 1 only; degenerate: A0 %.4f with %d of 180 ties; AUROC ~ 0.5 by construction. Verifier-only.' % (b['A0']['A0'], b['A0']['n_ties']))
# ---------- (4) T6
RUNMAP = {'M1_fp16_P4': 't6.M1', 'M1_fp32_P2': 't6.M1_fp32', 'M2_P4': 't6.M2', 'B1_P4': 't6.B1', 'B2_P4': 't6.B2', 'B3_P4': 't6.B3'}
for rk, pre in RUNMAP.items():
    for cell, x in V['t6'][rk].items():
        if cell == 'tau': continue
        lab = None
        if cell in ('O1', 'O2', 'O3'): lab = [f'T6 {rk} {cell} tiehalf'] if rk in ('M1_fp16_P4', 'B1_P4', 'B2_P4', 'B3_P4', 'M2_P4') else None
        else:
            pk = {'M1_fp32_P2': 'M1_fp32_P2', 'B1_P4': 'B1_P2', 'B2_P4': 'B2_P2'}.get(rk)
            if pk and f'T6 {pk} {cell} tiehalf' in ROWS: lab = [f'T6 {pk} {cell} tiehalf']
        if cell == 'all' and rk in ('B1_P4', 'B2_P4', 'M1_fp32_P2'): lab = [f'T6 {RUNMAP and {"M1_fp32_P2":"M1_fp32_P2","B1_P4":"B1_P2","B2_P4":"B2_P2"}[rk]} all tiehalf']
        add(f'{pre}.{cell}.tiehalf', pc(x['tiehalf']), lab, unit='%', tol='0.1 pp', src=['P2_M1_ipdev_clean_s1' if 'P2' in rk else ('P4_M2_ipdev_clean-mi0_s1' if rk == 'M2_P4' else 'P4_M1_ipdev_clean_s1')],
            note=('%d pairs' % x['n']) + ('; visible/occluded/static/dynamic from the scene folder names in the starting-kit dev/task.txt (verifier read of data/intphys_dev/starting_kit.zip)' if cell not in ('all', 'O1', 'O2', 'O3') else ''))
        add(f'{pre}.{cell}.strict', pc(x['strict']), [l.replace('tiehalf', 'strict') for l in lab] if lab else None, unit='%', tol='0.1 pp', note='%d pairs' % x['n'])
# ---------- (5) M0r
for tag in ('P2', 'P4'):
    for i in range(3):
        c = V['m0r_clean'][f'{tag}_init{i}']
        add(f'clean.M0r_{tag}.init{i}.tiehalf', pc(c['tiehalf']), [f'M0r P2 init{i} tiehalf'] if tag == 'P2' else None, unit='%', tol='0.1 pp', src=[f'{tag}_M0r_ipdev_clean-init{i}_s1'], note='mean aggregation, prereg tau = %.4e; %d of 180 pairs tied; strict %.1f' % (c['tau'], c['n_ties'], pc(c['strict'])))
        add(f'clean.M0r_{tag}.init{i}.strict', pc(c['strict']), None, unit='%', status='info-only', src=[f'{tag}_M0r_ipdev_clean-init{i}_s1'])
        add(f'clean.M0r_{tag}.init{i}.ties', c['n_ties'], None, unit='pairs', status='info-only', src=[f'{tag}_M0r_ipdev_clean-init{i}_s1'])
add('clean.M0r_P2.tie_rate_prereg_tau', pc(sum(V['m0r_clean'][f'P2_init{i}']['n_ties'] for i in range(3)) / 540), ['M0r P2 tie rate mean over inits'], unit='%', tol='0.1 pp', status='mismatch',
    note='mean tie rate of the 3 inits under the prereg scale-relative tau (178-180 of 180 ties each; 99.6%%). results/analysis/p2_clean_g1.json (and prereg text "97-99%%") quote 98.1%%, the SUPERSEDED fixed tau = 1e-4 figure, which I reproduce exactly (%.1f%%). Strict (d>0) mean %.1f%% vs analysis 50.0%%: also a different tie convention. Writer: state the tau convention or use tie-half = 50.0 for all three inits (verified).' % (pc(sum(V['m0r_clean'][f'P2_init{i}']['n_ties_fixed_tau1e4'] for i in range(3)) / 540), 100 * sum(V['m0r_clean'][f'P2_init{i}']['strict'] for i in range(3)) / 3))
h3 = V['m0r_h3']
add('h3.M0r.reversal_det', pc(h3['reversal']['det']), None, status='info-only', ci=[pc(x) for x in h3['reversal']['ci']], unit='%', src=['P4_M0r_ipdev_time_reversal-high_s1', 'P4_M0r_ipdev_clean-init0_s1'], note='init0 only, full-clip max, tau = %.4e; %d ties of 180; strict %.1f. Verifier-only (no analysis counterpart).' % (h3['reversal']['tau'], h3['reversal']['n_ties'], pc(h3['reversal']['strict'])))
add('h3.M0r.hflip_det', None, None, status='pending', unit='%', note='no P4_M0r_ipdev_hflip-high run exists in results/raw; not defined / not run')
# ---------- (6) F3 flip CI
for c, x in V['flip_ci_M1'].items():
    if c == 'dither':
        add('dose.h1.M1.dither.flip_ci', [pc(x['flip_ci'][0]), pc(x['flip_ci'][1])], None, status='info-only', ci=[pc(x['flip_ci'][0]), pc(x['flip_ci'][1])], unit='%', note='CI of the dither floor f0 (%.2f%%), scene-cluster bootstrap' % pc(x['f0'])); continue
    add(f'dose.h1.M1.{c}.flip_ci', [pc(x['flip_ci'][0]), pc(x['flip_ci'][1])], [f'F3 M1 {c} flip CI lo', f'F3 M1 {c} flip CI hi'], ci=[pc(x['flip_ci'][0]), pc(x['flip_ci'][1])], unit='%', tol='1 pp (bootstrap)', note='95%% scene-cluster bootstrap CI of the flip rate (%.2f%%), n=%d' % (pc(x['flip']), x['n']))
# ---------- convention audit entry (M2 H1 strict vs tie-half)
add('m2.h1.convention_audit', 'tie-half', None, status='info-only', note='AUDIT: every existing h1.M2.<edit>.{dacc_pp,flip_pct,holm14_*} and every new m2.dose.h1.<edit>.<lv>.{dacc_pp,flip_pct,holm30_*} value is TIE-HALF (prereg tau_mean 1.109e-4, f0 24.6%). Strict values exist only under the explicit suffixes ._strict / .holm22_*_strict (f0 strict 17.4%). notes/M2_RESULTS.md main H1 table equals the tie-half numbers (brightness -0.4/15.4, noise -6.4/28.3, blur +12.8/42.2, jpeg -1.7/40.6, zoom +7.1/25.0); its second table, labelled Strict, equals the strict numbers (-0.7/10.0, -6.9/21.7, +14.4/31.1, +1.7/35.0, +7.1/19.6). No strict number sits in a tie-half slot in the files checked. Two things can be mistaken for a convention clash: (a) results/analysis/m2/exactties/h1_M2_exactties.json has tie_value 0.5 but tau 0, which is numerically identical to strict because no exact ties occur; (b) the M2 dose analysis primary reading (dose_M2_s1.json, DOSE_RESPONSE.md and the M2_RESULTS dose paragraph) uses SEED 1 at every cell, so its high-strength brightness/noise values (-0.6/15.0 and -7.8/25.6) differ from the 3-seed h1.M2 values (-0.4/15.4 and -6.4/28.3); both are tie-half.')
# ---------- placeholders -> superseded
for e in E:
    if e['key'].startswith('m2.dose.') and e['status'] == 'pending':
        e['status'] = 'info-only'; e['note'] = (e.get('note') or '') + ' [P8: placeholder superseded by the concrete m2.dose.* keys below; runs landed]'
E.extend(new)
D['generated'] = str(datetime.date.today()); D['generator'] += ' + verify/p8_make_verified.py (P8: M2 dose, ablations, T5/T6 extras, M0r, flip CIs; values from verify/p8_recompute.json)'
json.dump(D, open('results/VERIFIED.json', 'w'), indent=1)
from collections import Counter
print(len(new), Counter(e['status'] for e in new), Counter(e['status'] for e in E))
