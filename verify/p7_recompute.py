"""P7 verifier recompute. Run from repo root: .venv/bin/python verify/p7_recompute.py
Writes verify/p7_recompute.json. No src/ imports; no results/analysis; no notes."""
import sys, os, json, csv, time
sys.path.insert(0, 'verify')
from p7_lib import *

T0 = time.time()
def log(*a): print(f'[{time.time()-T0:6.0f}s]', *a, flush=True)

SPA = json.load(open('kaggle/h2_spec_a/matches.json')); SP = SPA['pairs']
SPO = json.load(open('kaggle/expl_onset_spec/matches.json')); SPOP = SPO['pairs']
assert sorted(SP) == upair == sorted(SPOP)
def entries(e):
    if 'levels' in e: return {'1': e}
    return {k: d for k, d in e.items() if isinstance(d, dict) and 'levels' in d}
res = {'meta': {'bootstrap_seed': SEED, 'n_boot': NB, 'n_pairs': P, 'n_scenes': 90}}

m1 = Ctx('M1', 'P4_M1_ipdev_clean_s1', 'P4_M1_ipdev_base_ref-ref_s1')
m2 = Ctx('M2', 'P4_M2_ipdev_clean-mi0_s1', 'P4_M2_ipdev_base_ref-ref_s1')
m2_old = find('P4_M2_ipdev_clean_s1')
p2 = find('P2_M1_ipdev_clean_s1'); skip4_m1 = find('P4_M1_ipdev_clean-skip4_s1'); skip4_m2 = find('P4_M2_ipdev_clean-skip4_s1')
vith = find('P2H_M1H_ipdev_clean_s1')
log('loaded')

# ======================= clean accuracies
ca = {}
ca['M1_fp16_P4'] = clean_acc_of(m1.clean)
ca['M1_fp32_P2'] = clean_acc_of(p2)
ca['M1H_fp16_P2H'] = clean_acc_of(vith)
ca['M2_mi0'] = clean_acc_of(m2.clean)
ca['M2_mi1_old'] = clean_acc_of(m2_old)
ca['M1_skip4'] = clean_acc_of(skip4_m1); ca['M2_skip4'] = clean_acc_of(skip4_m2)
for nm, r in (('P2_fp32', p2), ('P4_fp16_M1', m1.clean), ('P4_fp16_M2', m2.clean)):
    for b in ('B1', 'B2', 'B3'):
        ca[f'{b}_{nm}'] = clean_acc_of(r, b)
# per-block clean accuracy (M1 fp16, fp32; strict and tie-half)
def per_block(r, key='surprise'):
    a = r[key]; s = np.nanmean(a if a.ndim == 2 else a.min(-1), 1); tau = tau_of(s); d = s[imp_i] - s[pos_i]
    pb = np.array([block[pos_i[k]] for k in range(P)]); out = {}
    for b in sorted(set(pb)):
        m = pb == b
        out[b] = dict(n=int(m.sum()), tiehalf=float(acc_from_diff(d, tau)[m].mean()), strict=float(acc_from_diff(d, tau, 'strict')[m].mean()))
    return out
ca['per_block'] = {nm: per_block(r, k) for nm, r, k in (('M1_fp32_P2', p2, 'surprise'), ('M1_fp16_P4', m1.clean, 'surprise'), ('B1_P2', p2, 'B1'), ('B2_P2', p2, 'B2'))}
res['clean_acc'] = ca
# paired M1 - B2 (clean, mean aggregation): fp32 P2 M1 and fp16 P4 M1
def paired_diff(rM, rB, keyB='B2'):
    sM = np.nanmean(rM['surprise'], 1); sB = np.nanmean(rB[keyB].min(-1), 1)
    yM = acc_from_diff(sM[imp_i] - sM[pos_i], tau_of(sM)); yB = acc_from_diff(sB[imp_i] - sB[pos_i], tau_of(sB))
    b = boot_mean(yM - yB); yMs = (sM[imp_i] > sM[pos_i]).astype(float); yBs = (sB[imp_i] > sB[pos_i]).astype(float)
    bs = boot_mean(yMs - yBs)
    return dict(diff=float((yM - yB).mean()), ci=[float(x) for x in np.percentile(b, [2.5, 97.5])],
                p_two_sided=float(min(1, 2 * min((b >= 0).mean(), (b <= 0).mean()))), diff_strict=float((yMs - yBs).mean()),
                ci_strict=[float(x) for x in np.percentile(bs, [2.5, 97.5])], M_acc=float(yM.mean()), B_acc=float(yB.mean()))
res['paired_M1_minus_B2'] = {'fp32_P2': paired_diff(p2, p2), 'fp16_P4': paired_diff(m1.clean, m1.clean)}
res['paired_M1_minus_B1'] = {'fp32_P2': paired_diff(p2, p2, 'B1'), 'fp16_P4': paired_diff(m1.clean, m1.clean, 'B1')}
log('clean done')

# ======================= precision: fp16 (P4) vs fp32 (P2) same inputs, 360 videos
A16 = align(m1.clean); A32 = align(p2)
assert list(p2['video_ids']) == ids
s16 = np.nanmean(A16['surprise'], 1); s32 = np.nanmean(A32['surprise'], 1)
d16 = s16[imp_i] - s16[pos_i]; d32 = s32[imp_i] - s32[pos_i]
prec = {}
for nm, t16, t32 in (('own_tau', tau_of(s16), tau_of(s32)), ('common_tau_fp16', tau_of(s16), tau_of(s16)), ('common_tau_fp32', tau_of(s32), tau_of(s32))):
    c16 = cls(d16, t16); c32 = cls(d32, t32)
    y16 = acc_from_diff(d16, t16); y32 = acc_from_diff(d32, t32)
    prec[nm] = dict(class_change_frac=float((c16 != c32).mean()), n_class_change=int((c16 != c32).sum()),
                    credit_change_frac=float((y16 != y32).mean()), n_credit_change=int((y16 != y32).sum()), tau16=float(t16), tau32=float(t32),
                    correct_flag_change_frac=float(((y16 > 0.5) != (y32 > 0.5)).mean()))
c16 = cls(d16, 0.0); c32 = cls(d32, 0.0); prec['strict_tau0'] = dict(sign_change_frac=float((c16 != c32).mean()), n=int((c16 != c32).sum()))
# per-window noise: elementwise fp16 vs fp32 surprise (min over C), per-window margin (impossible - possible)
w16 = A16['surprise']; w32 = A32['surprise']
prec['max_abs_window_score_diff'] = float(np.nanmax(np.abs(w16 - w32)))
mg16 = w16[imp_i] - w16[pos_i]; mg32 = w32[imp_i] - w32[pos_i]
prec['max_abs_window_margin_diff'] = float(np.nanmax(np.abs(mg16 - mg32)))
prec['max_abs_S_wc_diff'] = float(np.nanmax(np.abs(A16['S'] - A32['S'])))
prec['median_abs_window_margin_diff'] = float(np.nanmedian(np.abs(mg16 - mg32)))
prec['p99_abs_window_margin_diff'] = float(np.nanpercentile(np.abs(mg16 - mg32), 99))
prec['max_abs_pair_mean_margin_diff'] = float(np.max(np.abs(d16 - d32)))
prec['tau_M1_fp16'] = float(tau_of(s16))
res['precision'] = prec
log('precision done')

# ======================= H1 (high) for M1 and M2
EDITS = ['brightness', 'noise', 'blur', 'jpeg', 'zoom', 'hflip', 'fps_halve']
keep112 = np.array([SP[p]['support_retention_crop'] >= 0.9 for p in upair])
ALL = np.ones(P, bool)
def h1_model(ctx, skip4):
    out = {}
    tau = ctx.tau_mean
    dith = h1_arrays(runs_of(ctx.model, 'dither-on'), ctx.clean, tau)
    f0p, f0ps = dith['flip'], dith['flip_strict']
    arrs = {}
    for e in EDITS:
        cond = f'{e}-high'
        if e == 'hflip' or e == 'fps_halve':
            runs = runs_of(ctx.model, cond, (1,))
        else:
            runs = runs_of(ctx.model, cond)
        ref = skip4 if e == 'fps_halve' else ctx.clean
        arrs[e] = h1_arrays(runs, ref, tau)
    stats = {e: h1_stats(arrs[e], f0p, keep112 if e == 'zoom' else ALL, f0ps) for e in EDITS}
    stats = holm_family(stats, EDITS)
    alt = {'zoom_allpairs': h1_stats(arrs['zoom'], f0p, ALL, f0ps)}
    dith_stats = dict(f0_all=float(f0p.mean()), f0_strict_all=float(f0ps.mean()), n_runs=dith['n_runs'],
                      dacc=float((dith['y'] - dith['y0']).mean()),
                      acc_dither_tiehalf=float(dith['y'].mean()), flip_binary_correct=float(np.mean([( (dith['y'] > .5) != (dith['y0'] > .5)).mean()])))
    ident = bool(np.array_equal(arrs['fps_halve']['y'], arrs['fps_halve']['y0']))
    return dict(tau_mean=float(tau), runs={e: arrs[e]['n_runs'] for e in EDITS}, stats=stats, alt=alt, dither=dith_stats,
                fps_halve_identical_to_skip4_clean=ident), arrs, dith
h1_M1, arrs_M1, dith_M1 = h1_model(m1, skip4_m1)
h1_M2, arrs_M2, dith_M2 = h1_model(m2, skip4_m2)
res['h1'] = {'M1': h1_M1, 'M2': h1_M2}
log('H1 done')

# ======================= H1 dose (M1): brightness noise blur jpeg zoom x low/mid/high
RET = json.load(open('verify/_retention.json'))   # verifier pixel retention (p6_retention.py)
def keep_ret(key): return np.array([(RET[p][key] is None) or (RET[p][key] >= 0.9) for p in upair])
ZKEEP = {'low': keep_ret('cm_win_0.9'), 'mid': keep_ret('cm_win_0.8'), 'high': keep112}
res['zoom_keep_counts'] = {k: int(v.sum()) for k, v in ZKEEP.items()}
DOSE_E = ['brightness', 'noise', 'blur', 'jpeg', 'zoom']
dose = {}
tau = m1.tau_mean
for e in DOSE_E:
    for lv in ('low', 'mid', 'high'):
        runs = runs_of('M1', f'{e}-{lv}')
        a = h1_arrays(runs, m1.clean, tau)
        keep = ZKEEP[lv] if e == 'zoom' else ALL
        dose[f'{e}-{lv}'] = h1_stats(a, dith_M1['flip'], keep, dith_M1['flip_strict'])
        dose[f'{e}-{lv}']['n_runs'] = a['n_runs']
        if e == 'zoom':
            dose[f'{e}-{lv}_allpairs'] = h1_stats(a, dith_M1['flip'], ALL, dith_M1['flip_strict'])
            dose[f'{e}-{lv}_keep112'] = h1_stats(a, dith_M1['flip'], keep112, dith_M1['flip_strict'])
cells = [f'{e}-{lv}' for e in DOSE_E for lv in ('low', 'mid', 'high')]
ps = [dose[c]['p_dacc_cluster'] for c in cells] + [dose[c]['p_flip_vs_floor'] for c in cells]
ad = holm(ps)
for j, c in enumerate(cells): dose[c]['holm30_dacc'] = float(ad[j]); dose[c]['holm30_flip'] = float(ad[15 + j])
res['h1_dose_M1'] = dose
log('H1 dose done')

# ======================= H2 (M1, M2) at mid with stored matches
tons_st = [SP[p]['event']['t_on'] for p in upair]
def name_fn_p4(model, level):
    return lambda t, s: f'P4_{model}_ipdev_{t}-{level}_s{s}'
def h2_pack(ctx, level='mid', tons=tons_st, name_fn=None):
    nf = name_fn or name_fn_p4(ctx.model, level)
    core = h2_core(ctx, nf, tons)
    summ = summarize_h2(core); nolg = summarize_h2(core, drop=('lighting_global',))
    row, below = outcome_row(summ, core['a0']['M']['A0'])
    return core, dict(all=summ, no_lighting_global=nolg, A0=core['a0'], outcome=row, types_below_0p65=below, n_late=core['n_late'],
                      nseeds=core['nseeds'], tau=ctx.TAU2)
core_M1, h2_M1 = h2_pack(m1); log('H2 M1')
core_M2, h2_M2 = h2_pack(m2); log('H2 M2')
res['h2'] = {'M1': h2_M1, 'M2': h2_M2}
ev_info = dict(n_fallback_stored=int(sum(SP[p]['event']['fallback'] for p in upair)), n_transient_stored=int(sum(SP[p]['event']['transient'] for p in upair)),
               n_late_stored=int(sum(SP[p]['event']['t_on'] > 94 for p in upair)), meta_n_fallback=SPA['meta']['n_fallback'], meta_n_pairs=SPA['meta']['n_pairs'],
               m_i_median_gray=float(255 * np.median([SP[p]['m_i'] for p in upair])), m_i_iqr_gray=[float(255 * x) for x in np.percentile([SP[p]['m_i'] for p in upair], [25, 75])],
               m_i_min_gray=float(255 * min(SP[p]['m_i'] for p in upair)), m_i_max_gray=float(255 * max(SP[p]['m_i'] for p in upair)),
               t_on_median=float(np.median(tons_st)), t_on_fallback_values=sorted(set(SP[p]['event']['t_on'] for p in upair if SP[p]['event']['fallback']))[:10])
# ratios at mid
rat = {}
for t in TYPES:
    v = []
    for p in upair:
        for sk, d in entries(SP[p][t]).items(): v.append(d['levels']['mid']['ratio'])
    v = np.array(v); rat[t] = dict(n=int(len(v)), median=float(np.nanmedian(v)), n_nan=int(np.isnan(v).sum()), frac_in_0p9_1p1=float(((v >= 0.9) & (v <= 1.1)).mean()),
                                  q25=float(np.nanpercentile(v, 25)), q75=float(np.nanpercentile(v, 75)))
ev_info['mid_ratio'] = rat
# per-seed entries for lighting_global
lg_seed = {}
for p in upair:
    for sk, d in entries(SP[p]['lighting_global']).items(): lg_seed.setdefault(sk, []).append(d['levels']['mid']['ratio'])
ev_info['lg_mid_in_band_by_seed'] = {sk: float(((np.array(v) >= .9) & (np.array(v) <= 1.1)).mean()) for sk, v in lg_seed.items()}
RAWP = json.load(open('verify/_cache_pairs_events_raw.json'))   # verifier pixel D(t) (p6_pixels.py), linear resize to 224
mi_pix = np.array([np.mean(RAWP[p]['D_linear'][SP[p]['event']['t_on']:SP[p]['event']['t_off']]) for p in upair]); mi_st = np.array([SP[p]['m_i'] for p in upair])
ev_info['m_i_pixel_recompute_median_gray'] = float(255 * np.median(mi_pix)); ev_info['m_i_pixel_vs_stored_max_abs_diff'] = float(np.abs(mi_pix - mi_st).max())
res['h2_event_info'] = ev_info
# no-op global lighting entries: edited-run surprise identical to clean (all 17 windows bitwise), per seed
lgn = {}
cs = align(m1.clean)['surprise']
for s in (1, 2, 3):
    r = find(f'P4_M1_ipdev_lighting_global-mid_s{s}')
    e = align(r)['surprise']
    same = np.array([np.array_equal(e[i], cs[i]) for i in pos_i])
    # tie-band: max over windows of |e-c| <= tau? (score diff within tau_M1 mean) and mean-score diff <= tau
    sm_e = np.nanmean(e[pos_i], 1); sm_c = np.nanmean(cs[pos_i], 1)
    within = np.abs(sm_e - sm_c) <= m1.tau_mean
    wmax = np.nanmax(np.where(mask_from_ton(tons_st), e[pos_i], -np.inf), 1); cmax = np.nanmax(np.where(mask_from_ton(tons_st), cs[pos_i], -np.inf), 1)
    within_ev = np.abs(wmax - cmax) <= m1.TAU2['M']
    lgn[f's{s}'] = dict(n_entries=int(len(pos_i)), n_bitwise_identical_to_clean=int(same.sum()), n_mean_score_within_tau=int(within.sum()),
                        n_evmax_within_tau2=int(within_ev.sum()))
for t in ('lighting_local',):
    r = find(f'P4_M1_ipdev_{t}-mid_s1'); e = align(r)['surprise']
    lgn['local_s1_bitwise_identical'] = int(np.array([np.array_equal(e[i], cs[i]) for i in pos_i]).sum())
res['lg_noop'] = lgn
log('lg noop done')

# ======================= H3 (M1 and M2)
def h3_pack(ctx, vf, hf, tr, m0_vf, m0_tr, m0_clean, tau_m0):
    tauM = ctx.TAU2['M']; c0 = ctx.cw['M']
    def detect(ctrl, ref, tau):
        d = np.nanmax(ctrl, 1)[pos_i] - np.nanmax(ref, 1)[pos_i]
        return np.where(np.abs(d) <= tau, 0.5, (d > 0).astype(float)), d
    def bootci(y): return [float(x) for x in np.percentile(boot_mean(y), [2.5, 97.5])]
    yv, dvf = detect(vf, c0, tauM); yh, dhf = detect(hf, c0, tauM); yvh, dvh = detect(vf, hf, tauM); yr, dr = detect(tr, c0, tauM)
    ym0v, _ = detect(m0_vf, m0_clean, tau_m0); ym0r, _ = detect(m0_tr, m0_clean, tau_m0)
    H3 = {}
    for nm, y, d in (('vflip_a_ref_p', yv, dvf), ('hflip_ref_p', yh, dhf), ('vflip_b_ref_hflip', yvh, dvh), ('reversal_ref_p', yr, dr)):
        H3[nm] = dict(det=float(y.mean()), ci=bootci(y), n_ties=int((np.abs(d) <= tauM).sum()), strict=float((d > tauM).mean()))
    H3['M0r_vflip'] = dict(det=float(ym0v.mean()), ci=bootci(ym0v), n_ties=int((ym0v == .5).sum()), tau=float(tau_m0))
    H3['M0r_reversal'] = dict(det=float(ym0r.mean()), ci=bootci(ym0r))
    for nm, a, b in (('model_minus_M0r_vflip', yv, ym0v), ('model_minus_M0r_reversal', yr, ym0r)):
        H3[nm] = dict(diff=float((a - b).mean()), ci=bootci(a - b))
    for nm, wm in (('vflip', vf), ('reversal', tr), ('hflip', hf)):
        s = np.nanmean(wm, 1); d = s[imp_i] - s[pos_i]
        H3['pairwise_acc_' + nm] = dict(tiehalf=float(acc_from_diff(d, ctx.tau_mean).mean()), strict=float(acc_from_diff(d, ctx.tau_mean, 'strict').mean()))
    H3['tau'] = float(tauM); H3['G2_pass'] = bool(yv.mean() >= 0.8)
    return H3
m0c = find('P4_M0r_ipdev_clean-init0_s1'); m0_clean = align(m0c)['surprise']; tau_m0 = tau_of(np.nanmax(m0_clean, 1))
m0_vf = W(find('P4_M0r_ipdev_vflip-high_s1'), 'M'); m0_tr = W(find('P4_M0r_ipdev_time_reversal-high_s1'), 'M')
def ctrl_w(model, c): return W(find(f'P4_{model}_ipdev_{c}-high_s1'), 'M')
res['h3'] = {'M1': h3_pack(m1, ctrl_w('M1', 'vflip'), ctrl_w('M1', 'hflip'), ctrl_w('M1', 'time_reversal'), m0_vf, m0_tr, m0_clean, tau_m0),
             'M2': h3_pack(m2, ctrl_w('M2', 'vflip'), ctrl_w('M2', 'hflip'), ctrl_w('M2', 'time_reversal'), m0_vf, m0_tr, m0_clean, tau_m0)}
log('H3 done')

# ======================= (B) M1 spec dose-response
dose2 = {}
per_cells = []
for lv in ('low', 'mid', 'high'):
    core, pack = h2_pack(m1, lv)
    dose2[lv] = pack; dose2[lv]['per_type_D'] = per_type_D(core)
    log('H2 dose', lv)
# Holm-24: 12 cells (4 types x 3 levels) x 2 contrasts; pooled Holm-6 (3 levels x 2)
cells24 = [(lv, t, kk) for lv in ('low', 'mid', 'high') for t in TYPES for kk in ('B1', 'B2')]
a24 = holm([dose2[lv]['per_type_D'][t][kk]['p_onesided'] for lv, t, kk in cells24])
for (lv, t, kk), a in zip(cells24, a24): dose2[lv]['per_type_D'][t][kk]['holm24'] = float(a)
cells6 = [(lv, kk) for lv in ('low', 'mid', 'high') for kk in ('B1', 'B2')]
a6 = holm([dose2[lv]['all']['D'][kk]['p_onesided'] for lv, kk in cells6])
for (lv, kk), a in zip(cells6, a6): dose2[lv]['all']['D'][kk]['holm6'] = float(a)
# keep spec dose JSON light: drop nested duplicate? keep
res['h2_dose_M1'] = dose2

# ======================= (C) EXPLORATORY onset-aligned and halve_hold
tons_on = [SPOP[p]['event']['t_on'] for p in upair]
def name_fn_on(t, s): return f'EXPL_M1_ipdev_onset-{t}-mid_s{s}'
core_on, onset = h2_pack(m1, 'mid', tons=tons_on, name_fn=name_fn_on)
onset['event_info'] = dict(t_on_median=float(np.median(tons_on)), t_on_min=int(min(tons_on)), t_on_max=int(max(tons_on)), n_fallback=int(sum(SPOP[p]['event']['fallback'] for p in upair)),
                           n_transient=int(sum(SPOP[p]['event']['transient'] for p in upair)), m_i_median_gray=float(255 * np.median([SPOP[p]['m_i'] for p in upair])))
onset['mid_ratio_in_band'] = {t: float(np.mean([ (0.9 <= d['levels']['mid']['ratio'] <= 1.1) for p in upair for sk, d in entries(SPOP[p][t]).items()])) for t in TYPES}
onset['per_type_D'] = per_type_D(core_on)
res['expl_onset'] = onset
log('onset done')
hh = find('EXPL_M1_ipdev_halve_hold-high_s1')
a = h1_arrays([hh], m1.clean, m1.tau_mean)
hs = h1_stats(a, dith_M1['flip'], ALL, dith_M1['flip_strict'])
hs['n_runs'] = 1; hs['f0_dither'] = float(dith_M1['flip'].mean())
res['expl_halve_hold'] = hs

# ======================= (D) IntPhys 2 Main
mn = find('P4_M1_ip2main_clean_s1')
meta = list(csv.DictReader(open('kaggle/datasets/intphys2/Main/metadata.csv')))
dbg = list(csv.DictReader(open('kaggle/datasets/intphys2/Debug/metadata.csv')))
typ = {r['name']: r['type'] for r in meta}; dbg_names = {r['name'] for r in dbg}
mid = list(mn['video_ids']); mpair = mn['pair_id']; mlab = mn['label']
up = sorted(set(mpair)); NP = len(up)
mpos = np.zeros(NP, int); mimp = np.zeros(NP, int)
for k, pid in enumerate(up):
    ix = np.where(mpair == pid)[0]; assert len(ix) == 2
    a_, b_ = ix; mpos[k], mimp[k] = (a_, b_) if mlab[a_] == 0 else (b_, a_)
    assert mlab[a_] != mlab[b_]
assert all('Possible' in typ[mid[i]] and 'Impossible' not in typ[mid[i]] for i in mpos), 'label 0 != Possible'
assert all('Impossible' in typ[mid[i]] for i in mimp)
mblock = np.array([mn['block'][mpos[k]] for k in range(NP)]); mscene = np.array([mn['scene_id'][mpos[k]] for k in range(NP)])
overlap_pair = np.array([(mid[mpos[k]] in dbg_names) or (mid[mimp[k]] in dbg_names) for k in range(NP)])
n_overlap_videos = int(sum(v in dbg_names for v in mid))
msc = sorted(set(mscene)); msi = np.array([msc.index(s) for s in mscene]); msb = np.array([mblock[list(msi).index(i)] for i in range(len(msc))])
rng2 = np.random.default_rng(SEED); MC = np.zeros((NB, len(msc)))
for b in sorted(set(msb)):
    ix = np.where(msb == b)[0]; dr_ = rng2.integers(0, len(ix), (NB, len(ix)))
    for r_ in range(len(ix)): np.add.at(MC, (np.arange(NB), ix[dr_[:, r_]]), 1)
mw = MC[:, msi]
def main_acc(score_key, mask=None):
    a = mn[score_key]; sc = np.nanmean(a if a.ndim == 2 else a.min(-1), 1)
    tau = tau_of(sc); d = sc[mimp] - sc[mpos]
    yt = acc_from_diff(d, tau); ys = (d > 0).astype(float)
    k = np.ones(NP, bool) if mask is None else mask
    o = dict(n=int(k.sum()), tau=float(tau), tiehalf=float(yt[k].mean()), strict=float(ys[k].mean()), n_ties=int((np.abs(d) <= tau)[k].sum()))
    w = mw * k[None, :]; bm = (w @ yt) / w.sum(1); o['tiehalf_ci'] = [float(x) for x in np.percentile(bm, [2.5, 97.5])]
    bs = (w @ ys) / w.sum(1); o['strict_ci'] = [float(x) for x in np.percentile(bs, [2.5, 97.5])]
    o['per_block'] = {b: dict(n=int((mblock == b)[k].sum()), tiehalf=float(yt[k & (mblock == b)].mean()), strict=float(ys[k & (mblock == b)].mean())) for b in sorted(set(mblock))}
    return o
main = {'n_videos': len(mid), 'n_pairs': NP, 'n_blocks': {b: int((mblock == b).sum()) for b in sorted(set(mblock))}, 'n_debug_name_overlap_videos': n_overlap_videos,
        'n_pairs_with_debug_overlap': int(overlap_pair.sum()), 'n_scenes': len(msc)}
for nm, key in (('M1', 'surprise'), ('B1', 'B1'), ('B2', 'B2'), ('B3', 'B3')):
    main[nm] = {'all': main_acc(key), 'without_debug_overlap': main_acc(key, ~overlap_pair)}
main['M1']['tau_note'] = 'tau = 2e-4 x median of 1012 per-video mean scores (mean aggregation)'
res['ip2_main'] = main
log('main done')

# ======================= P2 / G1' ladder precision facts
res['g1prime'] = {'P2_fp32_M1': ca['M1_fp32_P2'], 'P2H_fp16_M1H': ca['M1H_fp16_P2H'],
                  'P2_B1': ca['B1_P2_fp32'], 'P2_B2': ca['B2_P2_fp32'], 'P2_B3': ca['B3_P2_fp32']}
res['g1prime']['M1H_runs_meta'] = json.load(open(vith['_path'] + '/meta.json'))['run']['precision']
res['g1prime']['P2_meta_precision'] = json.load(open(p2['_path'] + '/meta.json'))['run']['precision']
res['g1prime']['M1_P4_meta_precision'] = json.load(open(m1.clean['_path'] + '/meta.json'))['run']['precision']
# P2 B1 whole-window is not stored in the npz: not recomputed here
res['g1prime']['b1_whole_window_available'] = 'b1_whole_window' in p2

def clean_(o):
    if isinstance(o, dict): return {str(k): clean_(v) for k, v in o.items() if not str(k).startswith('_')}
    if isinstance(o, (list, tuple)): return [clean_(v) for v in o]
    if isinstance(o, np.floating): return float(o)
    if isinstance(o, np.integer): return int(o)
    if isinstance(o, np.bool_): return bool(o)
    if isinstance(o, np.ndarray): return o.tolist()
    return o
json.dump(clean_(res), open(os.environ.get('P7_OUT', 'verify/p7_recompute.json'), 'w'), indent=1)
log('written')
