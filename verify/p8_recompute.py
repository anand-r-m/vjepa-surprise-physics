"""P8 verifier recompute (M2 dose, ablations, baselines AUROC, T6 blocks, M0r, flip CIs).
Run from repo root: .venv/bin/python verify/p8_recompute.py   -> verify/p8_recompute.json
Independent: uses only verify/p7_lib.py (own code) + raw arrays + stored matches/retention caches. No src/, no results/analysis, no notes."""
import sys, os, json, time, zipfile, re
sys.path.insert(0, 'verify')
import p7_lib as L
from p7_lib import *

T0 = time.time()
def log(*a): print(f'[{time.time()-T0:6.0f}s]', *a, flush=True)

SPA = json.load(open('kaggle/h2_spec_a/matches.json')); SP = SPA['pairs']
tons_st = [SP[p]['event']['t_on'] for p in upair]
res = {'meta': {'bootstrap_seed': SEED, 'n_boot': NB}}
L.KEYS = ('M', 'B1', 'B2', 'B3')
_W0, _EV0 = L.W, L.evmax


def set_mode(agg='max', C=None):
    """patch p7_lib so Ctx/h2_core use fixed context-length index C (None = min over C) and aggregation agg (max|mean)"""
    def W8(r, key):
        a = align(r)
        if C is None:
            return a['surprise'] if key == 'M' else np.nanmin(a[key], axis=-1)
        ci = list(r['context_lengths']).index(C) if 'context_lengths' in r else None
        return a['S'][..., ci] if key == 'M' else a[key][..., ci]
    L.W = W8
    if agg == 'mean':
        def ev(w, mask, idxs): return np.nanmean(np.where(mask, w[idxs], np.nan), axis=1)
        L.evmax = ev
    else:
        L.evmax = _EV0


def reset(): L.W = _W0; L.evmax = _EV0


# sanity: surprise == min over C of S
c1 = L.clean1
res['meta']['surprise_equals_nanmin_S'] = bool(np.allclose(np.nanmin(c1['S'], -1), c1['surprise'], equal_nan=True, atol=1e-7))
res['meta']['context_lengths'] = [int(x) for x in c1['context_lengths']]

m1 = Ctx('M1', 'P4_M1_ipdev_clean_s1', 'P4_M1_ipdev_base_ref-ref_s1')
m2 = Ctx('M2', 'P4_M2_ipdev_clean-mi0_s1', 'P4_M2_ipdev_base_ref-ref_s1')
log('loaded')


def flip_ci(a, keep):
    k = keep.astype(float); f = a['flip']
    bf = ((pair_w * k) @ f) / (pair_w * k).sum(1)
    bs = ((pair_w * k) @ a['flip_strict']) / (pair_w * k).sum(1)
    return [float(x) for x in np.percentile(bf, [2.5, 97.5])], [float(x) for x in np.percentile(bs, [2.5, 97.5])]


# ===================== (1a) M2 H1 dose cells
RET = json.load(open('verify/_retention.json'))
SPmap = SP
keep112 = np.array([SP[p]['support_retention_crop'] >= 0.9 for p in upair]); ALL = np.ones(P, bool)
tauM2 = m2.tau_mean
dith2 = h1_arrays(runs_of('M2', 'dither-on'), m2.clean, tauM2)
M2_CELLS = [(e, lv) for e in ('brightness', 'noise', 'blur') for lv in ('low', 'mid', 'high')] + [('jpeg', 'high'), ('zoom', 'high')]
assert len(M2_CELLS) == 11
h1d = {}
for e, lv in M2_CELLS:
    runs = runs_of('M2', f'{e}-{lv}')
    a = h1_arrays(runs, m2.clean, tauM2)
    keep = keep112 if e == 'zoom' else ALL
    st = h1_stats(a, dith2['flip'], keep, dith2['flip_strict'])
    st['n_runs'] = a['n_runs']; st['flip_ci'], st['flip_ci_strict'] = flip_ci(a, keep)
    h1d[f'{e}-{lv}'] = st
cells = [f'{e}-{lv}' for e, lv in M2_CELLS]; nC = len(cells)
for suf, kd, kf, ksign in (('', 'p_dacc_cluster', 'p_flip_vs_floor', 'p_sign'), ('_strict', 'p_dacc_cluster_strict', 'p_flip_vs_floor_strict', 'p_sign_strict')):
    ad = holm([h1d[c][kd] for c in cells] + [h1d[c][kf] for c in cells])
    asg = holm([h1d[c][ksign] for c in cells] + [h1d[c][kf] for c in cells])
    for j, c in enumerate(cells):
        h1d[c]['holm22_dacc' + suf] = float(ad[j]); h1d[c]['holm22_flip' + suf] = float(ad[nC + j])
        h1d[c]['holm22_sign' + suf] = float(asg[j])
res['h1_dose_M2'] = h1d

# seed-1-only variant of every M2 dose cell (same seeds everywhere; sensitivity)
h1s = {}
for e, lv in M2_CELLS:
    runs = runs_of('M2', f'{e}-{lv}', (1,))
    a = h1_arrays(runs, m2.clean, tauM2)
    keep = keep112 if e == 'zoom' else ALL
    st = h1_stats(a, dith2['flip'], keep, dith2['flip_strict']); st['flip_ci'], st['flip_ci_strict'] = flip_ci(a, keep); h1s[f'{e}-{lv}'] = st
for suf, kd, kf in (('', 'p_dacc_cluster', 'p_flip_vs_floor'), ('_strict', 'p_dacc_cluster_strict', 'p_flip_vs_floor_strict')):
    ad = holm([h1s[c][kd] for c in cells] + [h1s[c][kf] for c in cells])
    for j, c in enumerate(cells): h1s[c]['holm22_dacc' + suf] = float(ad[j]); h1s[c]['holm22_flip' + suf] = float(ad[nC + j])
res['h1_dose_M2_seed1only'] = h1s
res['h1_dose_M2_meta'] = dict(f0=float(dith2['flip'].mean()), f0_strict=float(dith2['flip_strict'].mean()), n_dither_runs=dith2['n_runs'], tau_mean=float(tauM2), family=2 * nC)
log('M2 H1 dose', {c: round(h1d[c]['dacc'] * 100, 1) for c in cells})

# ===================== (1b) M2 H2 dose (low/high seed 1 only; mid 3 seeds primary + seed-1 sensitivity)
def h2_run(ctx, nf, tons=tons_st):
    core = h2_core(ctx, nf, tons); summ = summarize_h2(core); return core, summ
dose2 = {}; cores = {}
for lv in ('low', 'mid', 'high'):   # seed 1 only at every level (the only seed available for low/high)
    core, summ = h2_run(m2, lambda t, s, lv=lv: f'P4_M2_ipdev_{t}-{lv}_s{s}' if s == 1 else None)
    cores[lv] = core; dose2[lv] = dict(all=summ, nseeds=core['nseeds'], A0=core['a0'], per_type_D=per_type_D(core))
core_m, summ_m = h2_run(m2, lambda t, s: f'P4_M2_ipdev_{t}-mid_s{s}')   # available seeds at mid (3,3,3 and 1 for zoom_base): the existing h2.M2 reading
dose2['mid_available_seeds'] = dict(all=summ_m, per_type_D=per_type_D(core_m), nseeds=core_m['nseeds'])
cells24 = [(lv, t, kk) for lv in ('low', 'mid', 'high') for t in TYPES for kk in ('B1', 'B2')]
a24 = holm([dose2[lv]['per_type_D'][t][kk]['p_onesided'] for lv, t, kk in cells24])
for (lv, t, kk), a in zip(cells24, a24): dose2[lv]['per_type_D'][t][kk]['holm24'] = float(a)
cells6 = [(lv, kk) for lv in ('low', 'mid', 'high') for kk in ('B1', 'B2')]
a6 = holm([dose2[lv]['all']['D'][kk]['p_onesided'] for lv, kk in cells6])
for (lv, kk), a in zip(cells6, a6): dose2[lv]['all']['D'][kk]['holm6'] = float(a)
# M1 same family for cross-check
res['h2_dose_M2'] = dose2
log('M2 H2 dose', {lv: round(dose2[lv]['all']['A_point']['M'], 4) for lv in ('low', 'mid', 'high')})

# ===================== (3) baselines AUROC with CIs, A0, per type (M1, M2, M0r) at mid, default aggregation
base = {}
for nm, ctx, pre in (('M1', m1, 'M1'), ('M2', m2, 'M2')):
    core, summ = h2_run(ctx, lambda t, s, pre=pre: f'P4_{pre}_ipdev_{t}-mid_s{s}')
    base[nm] = dict(A=summ['A_point'], A_ci=summ['A_ci'], per_type=summ['per_type'], A0={k: core['a0'][k] for k in core['a0']}, D=summ['D'], nseeds=core['nseeds'])
L.KEYS = ('M',)
m0 = Ctx('M0r', 'P4_M0r_ipdev_clean-init0_s1', 'P4_M0r_ipdev_base_ref-ref_s1')
core0 = h2_core(m0, lambda t, s: f'P4_M0r_ipdev_{t}-mid_s{s}' if s == 1 else None, tons_st)
Ab0 = np.mean([core0['bt']['M'][t] for t in TYPES], 0)
base['M0r'] = dict(A=float(np.mean([core0['pt']['M'][t] for t in TYPES])), A_ci=[float(x) for x in np.percentile(Ab0, [2.5, 97.5])],
                   per_type=core0['pt']['M'], A0=core0['a0']['M'], nseeds=core0['nseeds'], tau=m0.TAU2['M'])
L.KEYS = ('M', 'B1', 'B2', 'B3')
res['h2_baselines'] = base
log('baselines')

# ===================== (2) ablations (M1): A1 full-clip max / mean ; A2 fixed C = 2, 6, 10
abl = {}
def clean_mean_agg(ctx_clean, C):
    ci = list(ctx_clean['context_lengths']).index(C); s = np.nanmean(align(ctx_clean)['S'][..., ci], 1)
    tau = tau_of(s); d = s[imp_i] - s[pos_i]
    return dict(tiehalf=float(acc_from_diff(d, tau).mean()), strict=float(acc_from_diff(d, tau, 'strict').mean()), tau=float(tau))
for name, agg, C, tons in (('A1_full_max', 'max', None, [0] * P), ('A1_mean', 'mean', None, [0] * P),
                           ('A2_C2', 'max', 2, tons_st), ('A2_C6', 'max', 6, tons_st), ('A2_C10', 'max', 10, tons_st)):
    set_mode(agg, C)
    ctx = Ctx('M1', 'P4_M1_ipdev_clean_s1', 'P4_M1_ipdev_base_ref-ref_s1')
    if agg == 'mean':
        for k in L.KEYS: ctx.TAU2[k] = tau_of(np.nanmean(ctx.cw[k], 1))
    core, summ = h2_run(ctx, lambda t, s: f'P4_M1_ipdev_{t}-mid_s{s}', tons)
    d = dict(A=summ['A_point'], A_ci=summ['A_ci'], per_type=summ['per_type'], D=summ['D'], A0=core['a0'], tau=ctx.TAU2, n_used=core['n_used'])
    if C is not None: d['clean_meanagg'] = clean_mean_agg(ctx.clean, C)
    abl[name] = d
    reset(); log('abl', name, round(summ['A_point']['M'], 4))
# clean accuracy for A1 variants: full-clip max (tau from max), mean = primary
s_mean = np.nanmean(m1.clean['surprise'], 1); s_max = np.nanmax(m1.clean['surprise'], 1)
for nm, s in (('A1_full_max', s_max), ('A1_mean', s_mean)):
    tau = tau_of(s); dd = s[imp_i] - s[pos_i]
    abl[nm]['clean'] = dict(tiehalf=float(acc_from_diff(dd, tau).mean()), strict=float(acc_from_diff(dd, tau, 'strict').mean()), tau=float(tau), n_ties=int((np.abs(dd) <= tau).sum()))
res['ablations'] = abl
# A2 with baselines held at default min-over-C (sensitivity: baseline definition)
abl2 = {}
for C in (2, 6, 10):
    set_mode('max', C)
    ctx = Ctx('M1', 'P4_M1_ipdev_clean_s1', 'P4_M1_ipdev_base_ref-ref_s1')
    reset()
    # rebuild baseline windows at default for B1,B2,B3
    for k in ('B1', 'B2', 'B3'):
        ctx.cw[k] = _W0(ctx.clean, k); ctx.bw[k] = _W0(ctx.base, k)
        ctx.full_max[k] = np.nanmax(ctx.cw[k], 1); ctx.TAU2[k] = tau_of(ctx.full_max[k])
    set_mode('max', C)  # only affects W for model runs read in h2_core
    _W8 = L.W
    def Wmix(r, key, _W8=_W8): return _W0(r, key) if key != 'M' else _W8(r, key)
    L.W = Wmix
    core, summ = h2_run(ctx, lambda t, s: f'P4_M1_ipdev_{t}-mid_s{s}')
    abl2[f'A2_C{C}'] = dict(A=summ['A_point'], D=summ['D'])
    reset()
res['ablations_baseline_default'] = abl2
log('ablations done')

# ===================== (4) T6: per-block / visible-occluded / static-dynamic clean accuracy
zf = zipfile.ZipFile('data/intphys_dev/starting_kit.zip')
txt = zf.read('dev/task.txt').decode().split('\n')
sc_info = {}
for l in txt:
    m = re.match(r'(O\d)/(\d+)_test_(visible|occluded)_(static|dynamic_1|dynamic_2)_', l.strip())
    if m: sc_info[f'{m.group(1)}/{m.group(2)}'] = (m.group(3), m.group(4))
pair_vis = np.array([sc_info[s][0] for s in pair_scene]); pair_dyn = np.array([sc_info[s][1] for s in pair_scene])
pair_blk = np.array([block[pos_i[k]] for k in range(P)])
def strata_acc(r, key='surprise'):
    a = r[key]; a = align(r)[key] if key in ('surprise',) else align(r)[key]
    s = np.nanmean(a if a.ndim == 2 else np.nanmin(a, -1), 1); tau = tau_of(s); d = s[imp_i] - s[pos_i]
    yt = acc_from_diff(d, tau); ys = acc_from_diff(d, tau, 'strict'); out = {}
    def cell(m): return dict(n=int(m.sum()), tiehalf=float(yt[m].mean()), strict=float(ys[m].mean()), n_ties=int((np.abs(d) <= tau)[m].sum()))
    out['all'] = cell(np.ones(P, bool)); out['tau'] = float(tau)
    for b in sorted(set(pair_blk)): out[b] = cell(pair_blk == b)
    for v in ('visible', 'occluded'): out[v] = cell(pair_vis == v)
    for dn in sorted(set(pair_dyn)): out[dn] = cell(pair_dyn == dn)
    for b in sorted(set(pair_blk)):
        for v in ('visible', 'occluded'): out[f'{b}_{v}'] = cell((pair_blk == b) & (pair_vis == v))
    return out
t6 = {}
runs6 = {'M1_fp16_P4': (m1.clean, 'surprise'), 'M2_P4': (m2.clean, 'surprise'), 'M1_fp32_P2': (find('P2_M1_ipdev_clean_s1'), 'surprise')}
for nm, (r, k) in runs6.items(): t6[nm] = strata_acc(r, k)
for src_nm, r in (('P4', m1.clean), ('P2', find('P2_M1_ipdev_clean_s1'))):
    for b in ('B1', 'B2', 'B3'): t6[f'{b}_{src_nm}'] = strata_acc(r, b)
t6['counts'] = dict(visible=int((pair_vis == 'visible').sum()), occluded=int((pair_vis == 'occluded').sum()), n_sc_info=len(sc_info))
res['t6'] = t6
log('T6')

# ===================== (5) M0r clean rows (3 inits, P2 fp32 and P4 fp16) + reversal/vflip
m0rows = {}
for tag, pre in (('P2', 'P2'), ('P4', 'P4')):
    for i in range(3):
        r = find(f'{pre}_M0r_ipdev_clean-init{i}_s1')
        c = clean_acc_of(r)
        s = np.nanmean(r['surprise'], 1)
        c['frac_exact_tie_pairs'] = float((np.abs(s[imp_i] - s[pos_i]) == 0).mean())
        c['between_video_sd_mean_agg'] = float(np.std(s))
        m0rows[f'{tag}_init{i}'] = c
m1s = np.nanmean(m1.clean['surprise'], 1); m0rows['M1_P4_between_video_sd'] = float(np.std(m1s))
m0rows['mean_over_inits_P2_tiehalf'] = float(np.mean([m0rows[f'P2_init{i}']['tiehalf'] for i in range(3)]))
m0rows['mean_over_inits_P4_tiehalf'] = float(np.mean([m0rows[f'P4_init{i}']['tiehalf'] for i in range(3)]))
res['m0r_clean'] = m0rows
m0c = find('P4_M0r_ipdev_clean-init0_s1'); m0_clean = align(m0c)['surprise']; tau_m0 = tau_of(np.nanmax(m0_clean, 1))
def det0(name):
    w = W(find(name), 'M'); d = np.nanmax(w, 1)[pos_i] - np.nanmax(m0_clean, 1)[pos_i]
    y = np.where(np.abs(d) <= tau_m0, 0.5, (d > 0).astype(float))
    return dict(det=float(y.mean()), ci=[float(x) for x in np.percentile(boot_mean(y), [2.5, 97.5])], n_ties=int((np.abs(d) <= tau_m0).sum()), strict=float((d > tau_m0).mean()), tau=float(tau_m0))
res['m0r_h3'] = {'vflip': det0('P4_M0r_ipdev_vflip-high_s1'), 'reversal': det0('P4_M0r_ipdev_time_reversal-high_s1'), 'hflip': 'not run (no P4_M0r_ipdev_hflip-high run in results/raw)'}
log('M0r')

# ===================== (6) flip CI bands: M1 dose cells
ZKEEP = {'low': np.array([(RET[p]['cm_win_0.9'] is None) or (RET[p]['cm_win_0.9'] >= 0.9) for p in upair]),
         'mid': np.array([(RET[p]['cm_win_0.8'] is None) or (RET[p]['cm_win_0.8'] >= 0.8 + 0.1) for p in upair]), 'high': keep112}
ZKEEP['mid'] = np.array([(RET[p]['cm_win_0.8'] is None) or (RET[p]['cm_win_0.8'] >= 0.9) for p in upair])
dith1 = h1_arrays(runs_of('M1', 'dither-on'), m1.clean, m1.tau_mean)
fci = {}
for e in ('brightness', 'noise', 'blur', 'jpeg', 'zoom'):
    for lv in ('low', 'mid', 'high'):
        a = h1_arrays(runs_of('M1', f'{e}-{lv}'), m1.clean, m1.tau_mean)
        keep = ZKEEP[lv] if e == 'zoom' else ALL
        c, cs = flip_ci(a, keep); k = keep.astype(float)
        fci[f'{e}-{lv}'] = dict(flip=float((a['flip'] * k).sum() / k.sum()), flip_ci=c, flip_strict=float((a['flip_strict'] * k).sum() / k.sum()), flip_ci_strict=cs, n=int(k.sum()), n_runs=a['n_runs'])
c, cs = flip_ci(dith1, ALL); fci['dither'] = dict(f0=float(dith1['flip'].mean()), flip_ci=c, n_runs=dith1['n_runs'])
res['flip_ci_M1'] = fci
log('flip ci')


def clean_(o):
    if isinstance(o, dict): return {str(k): clean_(v) for k, v in o.items() if not str(k).startswith('_')}
    if isinstance(o, (list, tuple)): return [clean_(v) for v in o]
    if isinstance(o, np.floating): return float(o)
    if isinstance(o, np.integer): return int(o)
    if isinstance(o, np.bool_): return bool(o)
    if isinstance(o, np.ndarray): return o.tolist()
    return o
json.dump(clean_(res), open('verify/p8_recompute.json', 'w'), indent=1)
log('written')
