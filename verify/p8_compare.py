"""P8: compare verify/p8_recompute.json with results/analysis (opened only after p8_recompute.json was written).
Writes verify/p8_rows.json (label -> status) and verify/p8_compare.md."""
import json, math
V = json.load(open('verify/p8_recompute.json')); A = lambda f: json.load(open('results/analysis/' + f))
rows = []
NB = 10000
def ptol(p, mult=1): return mult * (8 * math.sqrt(max(p, 1e-4) * (1 - p) / NB) + 0.0003)
def add(label, mine, theirs, tol):
    if theirs is None or mine is None: rows.append([label, mine, theirs, None, tol, 'UNMAPPED']); return
    d = abs(mine - theirs); rows.append([label, mine, theirs, d, tol, 'match' if d <= tol + 1e-12 else 'MISMATCH'])
def addp(label, mine, theirs, mult=1):
    if theirs is None or mine is None: rows.append([label, mine, theirs, None, None, 'UNMAPPED']); return
    pp = max(mine, theirs, 1e-4); pp = pp if pp < 0.5 else 0.5
    add(label, mine, theirs, ptol(pp, mult))
def holm(ps):
    o = sorted(range(len(ps)), key=lambda i: ps[i]); m = len(ps); adj = [0] * m; run = 0
    for r, i in enumerate(o): run = max(run, (m - r) * ps[i]); adj[i] = min(1, run)
    return adj

# ===== (1a) M2 H1 dose
cells = list(V['h1_dose_M2'])
for var, mine_k, files in (('asrun', 'h1_dose_M2', ('m2/dose/dose_M2_asrun.json', 'm2/dose/dose_M2_strict_asrun.json')),
                           ('s1', 'h1_dose_M2_seed1only', ('m2/dose/dose_M2_s1.json', 'm2/dose/dose_M2_strict_s1.json'))):
    for strict, fn in ((False, files[0]), (True, files[1])):
        th = A(fn); pe = th['per_edit']; sfx = '_strict' if strict else ''
        tag = f'M2 dose H1 {var}{" strict" if strict else ""}'
        add(f'{tag} f0', V['h1_dose_M2_meta']['f0_strict' if strict else 'f0'], th['f0'], .001)
        keys = [c.replace('-', '@') for c in cells]
        hp = holm([pe[k]['p_dacc_cluster'] for k in keys] + [pe[k]['p_flip_cluster'] for k in keys]); n = len(cells)
        for j, c in enumerate(cells):
            k = c.replace('-', '@'); x = V[mine_k][c]; t = pe[k]
            add(f'{tag} {c} n', x['n_pairs'], t['n'], 0)
            add(f'{tag} {c} dAcc', x['dacc' + sfx], t['dacc'], .001)
            add(f'{tag} {c} flip', x['flip' + sfx], t['flip'], .001)
            add(f'{tag} {c} flip-f0', x['flip' + sfx] - V['h1_dose_M2_meta']['f0_strict' if strict else 'f0'] if False else x['flip' + sfx] - (x['f0_strict'] if strict else x['f0']), t['excess'], .001)
            if not strict:
                add(f'{tag} {c} dAcc CI lo', x['dacc_ci'][0], t['dacc_ci'][0], .01); add(f'{tag} {c} dAcc CI hi', x['dacc_ci'][1], t['dacc_ci'][1], .01)
                add(f'{tag} {c} flip CI lo', x['flip_ci'][0], t['flip_ci'][0], .01); add(f'{tag} {c} flip CI hi', x['flip_ci'][1], t['flip_ci'][1], .01)
            else:
                add(f'{tag} {c} dAcc CI lo', x['dacc_strict_ci'][0], t['dacc_ci'][0], .01); add(f'{tag} {c} dAcc CI hi', x['dacc_strict_ci'][1], t['dacc_ci'][1], .01)
            addp(f'{tag} {c} p_dacc', x['p_dacc_cluster' + sfx], t['p_dacc_cluster']); addp(f'{tag} {c} p_flip', x['p_flip_vs_floor' + sfx], t['p_flip_cluster'])
            addp(f'{tag} {c} Holm-22 dAcc', x['holm22_dacc' + sfx], hp[j], 22); addp(f'{tag} {c} Holm-22 flip', x['holm22_flip' + sfx], hp[n + j], 22)

# ===== (1b) M2 H2 dose
th = A('m2/dose/dose_spec_M2.json'); d2 = V['h2_dose_M2']
for lv in ('low', 'mid', 'high'):
    L = th['levels'][lv]; m = d2[lv]['all']; tg = f'M2 spec dose {lv}'
    add(f'{tg} A', m['A_point']['M'], L['A'], .002); add(f'{tg} A CI lo', m['A_ci']['M'][0], L['A_ci'][0], .01); add(f'{tg} A CI hi', m['A_ci']['M'][1], L['A_ci'][1], .01)
    add(f'{tg} A_B1', m['A_point']['B1'], L['A_B1'], .002); add(f'{tg} A_B2', m['A_point']['B2'], L['A_B2'], .002); add(f'{tg} A_B3', m['A_point']['B3'], L['A_B3'], .002)
    add(f'{tg} A0', d2[lv]['A0']['M']['A0'], L['A0'], .001)
    for t, v in m['per_type']['M'].items(): add(f'{tg} A {t}', v, L['per_type'][t], .002)
    for b in ('B1', 'B2'):
        add(f'{tg} D_{b}', m['D'][b]['D'], L['D_' + b]['D'], .002); add(f'{tg} D_{b} CI lo', m['D'][b]['ci'][0], L['D_' + b]['ci'][0], .01); add(f'{tg} D_{b} CI hi', m['D'][b]['ci'][1], L['D_' + b]['ci'][1], .01)
        addp(f'{tg} p_{b}', m['D'][b]['p_onesided'], L['D_' + b]['p'])
cl = [(lv, kk) for lv in ('low', 'mid', 'high') for kk in ('B1', 'B2')]
h6 = holm([th['levels'][lv]['D_' + kk]['p'] for lv, kk in cl])
for (lv, kk), v in zip(cl, h6): addp(f'M2 spec dose {lv} Holm-6 {kk}', d2[lv]['all']['D'][kk]['holm6'], v, 6)
for lv in ('low', 'mid', 'high'):
    for t in ('lighting_global', 'lighting_local', 'jolt_base', 'zoom_base'):
        c = th['cells'][f'{t}@{lv}']; x = d2[lv]['per_type_D'][t]; tg = f'M2 spec dose {lv} {t}'
        add(f'{tg} A', x['B1']['A'], c['A'], .002)
        for b in ('B1', 'B2'):
            add(f'{tg} D_{b}', x[b]['D'], c['D_' + b], .002); add(f'{tg} D_{b} CI lo', x[b]['ci'][0], c['D_' + b + '_ci'][0], .01); add(f'{tg} D_{b} CI hi', x[b]['ci'][1], c['D_' + b + '_ci'][1], .01)
            addp(f'{tg} p_{b}', x[b]['p_onesided'], c['p_' + b]); addp(f'{tg} Holm-24 {b}', x[b]['holm24'], c['holm24_' + b], 24)

# ===== (2) ablations
for nm in ('A1_full_max', 'A1_mean', 'A2_C2', 'A2_C6', 'A2_C10'):
    h = A(f'ablations/{nm}/h2_{nm}.json'); c = A(f'ablations/{nm}/clean.json')['models']['M1']; m = V['ablations'][nm]; tg = f'abl {nm}'
    add(f'{tg} A', m['A']['M'], h['M1']['A'], .002); add(f'{tg} A CI lo', m['A_ci']['M'][0], h['M1']['A_ci'][0], .01); add(f'{tg} A CI hi', m['A_ci']['M'][1], h['M1']['A_ci'][1], .01)
    add(f'{tg} A0', m['A0']['M']['A0'], h['M1']['A0'], .001)
    for t, v in m['per_type']['M'].items(): add(f'{tg} A {t}', v, h['M1']['per_type'][t], .002)
    for b in ('B1', 'B2', 'B3'):
        add(f'{tg} A_{b}', m['A'][b], h[b]['A'], .002); add(f'{tg} A0_{b}', m['A0'][b]['A0'], h[b]['A0'], .001)
        add(f'{tg} A_{b} CI lo', m['A_ci'][b][0], h[b]['A_ci'][0], .01); add(f'{tg} A_{b} CI hi', m['A_ci'][b][1], h[b]['A_ci'][1], .01)
    for b in ('B1', 'B2'):
        add(f'{tg} D_{b}', m['D'][b]['D'], h['D_' + b]['D'], .002); add(f'{tg} D_{b} CI lo', m['D'][b]['ci'][0], h['D_' + b]['ci'][0], .01); add(f'{tg} D_{b} CI hi', m['D'][b]['ci'][1], h['D_' + b]['ci'][1], .01)
        addp(f'{tg} p_{b}', m['D'][b]['p_onesided'], h['D_' + b]['p']); addp(f'{tg} Holm-2 {b}', m['D'][b]['holm2'], h['D_' + b]['p_holm'], 2)
    if nm.startswith('A1'):
        add(f'{tg} clean', m['clean']['tiehalf'], c['max' if nm == 'A1_full_max' else 'mean']['acc_tiehalf'], .001)
    else:
        C = nm.split('C')[1]; add(f'{tg} clean (mean agg, fixed C)', m['clean_meanagg']['tiehalf'], c['A2_fixed_C_mean_agg'][C]['acc_tiehalf'], .001)

# ===== (3) T5 baselines
for M, fn, key in (('M1', 'h2/h2.json', 'M1'), ('M2', 'm2/h2.json', 'M2')):
    h = A(fn); b = V['h2_baselines'][M]
    for k in ('B1', 'B2', 'B3'):
        add(f'T5 {M} A_{k}', b['A'][k], h[k]['A'], .002); add(f'T5 {M} A_{k} CI lo', b['A_ci'][k][0], h[k]['A_ci'][0], .01); add(f'T5 {M} A_{k} CI hi', b['A_ci'][k][1], h[k]['A_ci'][1], .01)
        add(f'T5 {M} A0_{k}', b['A0'][k]['A0'], h[k]['A0'], .001)
        for t, v in b['per_type'][k].items(): add(f'T5 {M} A_{k} {t}', v, h[k]['per_type'][t], .002)
    add(f'T5 {M} A0_M', b['A0']['M']['A0'], h[key]['A0'], .001)

# ===== (4) T6 blocks (P4 clean.json per_block; b2_checks breakdown for visible/occluded and block x vis)
cj = A('p4/clean.json')['models']
for mine_k, ak in (('M1_fp16_P4', 'M1'), ('B1_P4', 'B1(M1)'), ('B2_P4', 'B2(M1)'), ('B3_P4', 'B3(M1)'), ('M2_P4', 'M2')):
    pb = cj[ak]['mean']['per_block']
    for b in ('O1', 'O2', 'O3'):
        add(f'T6 {mine_k} {b} tiehalf', V['t6'][mine_k][b]['tiehalf'], pb[b]['acc_tiehalf'], .001); add(f'T6 {mine_k} {b} strict', V['t6'][mine_k][b]['strict'], pb[b]['acc_strict'], .001)
bd = A('b2_checks.json')['breakdown_mean_agg']
for cell in bd:
    if cell not in V['t6']['M1_fp32_P2']: continue
    for mine_k, ak in (('M1_fp32_P2', 'M1'), ('B1_P2', 'B1_windowed'), ('B2_P2', 'B2_copy_last_context')):
        add(f'T6 {mine_k} {cell} tiehalf', V['t6'][mine_k][cell]['tiehalf'], bd[cell][ak]['tiehalf'], .001); add(f'T6 {mine_k} {cell} strict', V['t6'][mine_k][cell]['strict'], bd[cell][ak]['strict'], .001)

# ===== (5) M0r clean
g = A('p2_clean_g1.json')['M0r']
for i in range(3):
    add(f'M0r P2 init{i} tiehalf', V['m0r_clean'][f'P2_init{i}']['tiehalf'], g['mean']['all']['per_init'][i], .001)
add('M0r P2 strict mean over inits', sum(V['m0r_clean'][f'P2_init{i}']['strict'] for i in range(3)) / 3, g['mean']['all']['strict_mean'], .001)
add('M0r P2 tie rate mean over inits', sum(V['m0r_clean'][f'P2_init{i}']['n_ties'] for i in range(3)) / 3 / 180, g['mean']['all']['tie_rate_mean'], .001)
h3 = A('p4/h3_M1.json')
add('M0r reversal detection', V['m0r_h3']['reversal']['det'], None, .001)
# ===== (6) flip CI bands (M1 dose)
dm = A('h1/dose/dose_M1.json')['per_edit']
for c, x in V['flip_ci_M1'].items():
    if c == 'dither': continue
    k = c.replace('-', '@'); t = dm[k]
    add(f'F3 M1 {c} flip', x['flip'], t['flip'], .001); add(f'F3 M1 {c} flip CI lo', x['flip_ci'][0], t['flip_ci'][0], .01); add(f'F3 M1 {c} flip CI hi', x['flip_ci'][1], t['flip_ci'][1], .01)

json.dump(rows, open('verify/_p8_rows.json', 'w'))
n = len(rows); ok = sum(r[5] == 'match' for r in rows); bad = [r for r in rows if r[5] == 'MISMATCH']; un = [r for r in rows if r[5] == 'UNMAPPED']
print(n, ok, len(bad), len(un))
for r in bad: print('MISMATCH', r)
for r in un: print('UNMAPPED', r[0])
