"""P10 verifier recompute: splice structure from dev pixels + exploratory splice-detector analyses from stored arrays.
Run from repo root: .venv/bin/python verify/p10_recompute.py -> verify/p10_recompute.json
Independent: verify/p7_lib.py (own code), raw surprise arrays, dev npz pixels. No src/, no scripts/, no results/analysis, no notes."""
import sys, os, json, glob
sys.path.insert(0, 'verify')
import numpy as np
import p7_lib as L
from p7_lib import (clean1, ids, pair, lab, upair, P, pos_i, imp_i, pair_w, pair_sc, find, align, tau_of, SEED, NB)
from scipy.stats import rankdata, binomtest
D = 'kaggle/datasets/intphys-dev-npz'
res = {'meta': {'seed': SEED, 'n_boot': NB, 'exploratory': True}}

# ------------------------------------------------ (1) splice structure from pixels
spl = {}   # impossible video id -> dict
quad = {'n_scenes': 0, 'n_quads_2pos_2imp': 0, 'n_imp_total': 0, 'n_imp_fully_matched': 0, 'n_imp_both_sources': 0, 'frames_unmatched_total': 0, 'frames_shared_total': 0}
scenes = sorted({os.path.basename(p).rsplit('_', 1)[0] for p in glob.glob(D + '/*.npz')})
for sc in scenes:
    V = {k: np.load(f'{D}/{sc}_{k}.npz') for k in (1, 2, 3, 4)}
    fr = {k: V[k]['frames'] for k in V}; isp = {k: bool(V[k]['is_possible']) for k in V}
    pos = [k for k in V if isp[k]]; imp = [k for k in V if not isp[k]]
    quad['n_scenes'] += 1
    if len(pos) == 2 and len(imp) == 2: quad['n_quads_2pos_2imp'] += 1
    for i in imp:
        m = np.stack([(fr[i] == fr[p]).reshape(100, -1).all(1) for p in pos], 1)   # [100,2] exact equality at same index
        nm = (~m.any(1)).sum(); sh = (m.all(1)).sum()
        quad['n_imp_total'] += 1; quad['frames_unmatched_total'] += int(nm); quad['frames_shared_total'] += int(sh)
        full = nm == 0
        quad['n_imp_fully_matched'] += int(full)
        src = np.where(m.all(1), -1, np.argmax(m, 1))  # 0/1 source; -1 shared
        seq = [s for s in src if s >= 0]
        segs = [seq[0]] + [seq[j] for j in range(1, len(seq)) if seq[j] != seq[j - 1]] if seq else []
        nseg = len(segs)
        both = len(set(segs)) == 2
        quad['n_imp_both_sources'] += int(both)
        sw = [j for j in range(1, 100) if src[j] >= 0 and src[j - 1] >= 0 and src[j] != src[j - 1]]
        spl[f"{sc.replace('_', '/')}/{i}"] = dict(n_seg=nseg, switches=sw, full=bool(full), n_sources=len(set(segs)))
imps = sorted(spl)
assert len(imps) == 180
nseg = np.array([spl[v]['n_seg'] for v in imps])
sw1 = np.array([spl[v]['switches'][0] if spl[v]['switches'] else -1 for v in imps])
sw2 = np.array([spl[v]['switches'][1] for v in imps if len(spl[v]['switches']) > 1])
res['splice'] = dict(
    quad=quad, n_single=int((nseg == 2).sum()), n_double=int((nseg == 3).sum()), n_other=int(((nseg != 2) & (nseg != 3)).sum()),
    n_no_switch=int((sw1 < 0).sum()),
    switch1_median=float(np.median(sw1)), switch1_min=int(sw1.min()), switch1_max=int(sw1.max()),
    switch1_median_single=float(np.median([spl[v]['switches'][0] for v in imps if spl[v]['n_seg'] == 2])),
    switch1_median_double=float(np.median([spl[v]['switches'][0] for v in imps if spl[v]['n_seg'] == 3])),
    switch2_median=float(np.median(sw2)) if len(sw2) else None, switch2_min=int(sw2.min()) if len(sw2) else None, switch2_max=int(sw2.max()) if len(sw2) else None,
    double_by_block={b: int(sum(1 for v in imps if v.startswith(b) and spl[v]['n_seg'] == 3)) for b in ('O1', 'O2', 'O3')},
    single_by_block={b: int(sum(1 for v in imps if v.startswith(b) and spl[v]['n_seg'] == 2)) for b in ('O1', 'O2', 'O3')})

# ------------------------------------------------ per-pair margins (clean M1 fp16, mean agg)
def vid_scores(key):
    a = clean1[key]
    a = a if key == 'surprise' else np.nanmin(a, -1)
    return np.nanmean(a, 1)
SC = {'M1': vid_scores('surprise'), 'B1': vid_scores('B1'), 'B2': vid_scores('B2')}
TAU = {k: tau_of(v) for k, v in SC.items()}
MARG = {k: SC[k][imp_i] - SC[k][pos_i] for k in SC}
CORR = {k: L.acc_from_diff(MARG[k], TAU[k]) for k in SC}                    # tie-half credit
STRICT = {k: (MARG[k] > 0).astype(float) for k in SC}
res['clean'] = {k: dict(tau=float(TAU[k]), tiehalf=float(CORR[k].mean() * 100), strict=float(STRICT[k].mean() * 100),
                        n_ties=int((np.abs(MARG[k]) <= TAU[k]).sum())) for k in SC}

def spearman(a, b): return float(np.corrcoef(rankdata(a), rankdata(b))[0, 1])
def boot_spearman(a, b):
    out = np.empty(NB)
    for t in range(NB):
        idx = np.repeat(np.arange(P), pair_w[t].astype(int))
        out[t] = np.corrcoef(rankdata(a[idx]), rankdata(b[idx]))[0, 1]
    return out
res['spearman'] = {}
for k in ('B2', 'B1'):
    bs = boot_spearman(MARG['M1'], MARG[k])
    res['spearman'][k] = dict(rho=spearman(MARG['M1'], MARG[k]), ci=[float(x) for x in np.percentile(bs, [2.5, 97.5])], n=P)
    # also on correctness (credit) is not needed

# ------------------------------------------------ (3) M1 accuracy by baseline-right / wrong
def wmean(v, k):
    k = k.astype(float); return float((v * k).sum() / k.sum()), ((pair_w * k) @ v) / (pair_w * k).sum(1)
res['by_baseline'] = {}
y = CORR['M1']
for k in ('B2', 'B1'):
    right = MARG[k] > TAU[k]; wrong = MARG[k] < -TAU[k]; tie = ~right & ~wrong
    m_r, b_r = wmean(y, right); m_w, b_w = wmean(y, wrong)
    d = m_r - m_w; bd = b_r - b_w
    res['by_baseline'][k] = dict(n_right=int(right.sum()), n_wrong=int(wrong.sum()), n_tie=int(tie.sum()),
        m1_acc_right=m_r * 100, m1_acc_right_ci=[float(x) * 100 for x in np.percentile(b_r, [2.5, 97.5])],
        m1_acc_wrong=m_w * 100, m1_acc_wrong_ci=[float(x) * 100 for x in np.percentile(b_w, [2.5, 97.5])],
        diff_pp=d * 100, diff_ci=[float(x) * 100 for x in np.percentile(bd, [2.5, 97.5])],
        m1_strict_right=float(STRICT['M1'][right].mean() * 100), m1_strict_wrong=float(STRICT['M1'][wrong].mean() * 100),
        m1_right_credit=float(y[right].sum()), m1_wrong_credit=float(y[wrong].sum()))

# ------------------------------------------------ (4)(5) splice class / position
pair_imp_vid = [ids[imp_i[k]] for k in range(P)]
cls_n = np.array([spl[v]['n_seg'] for v in pair_imp_vid]); first = np.array([spl[v]['switches'][0] if spl[v]['switches'] else -1 for v in pair_imp_vid])
def grp_acc(mask):
    out = {}
    for k in ('M1', 'B1', 'B2'):
        m, b = wmean(CORR[k], mask)
        out[k] = dict(acc=m * 100, ci=[float(x) * 100 for x in np.percentile(b, [2.5, 97.5])], strict=float(STRICT[k][mask].mean() * 100))
    out['n'] = int(mask.sum()); return out
res['by_class'] = {'single': grp_acc(cls_n == 2), 'double': grp_acc(cls_n == 3)}
# difference single - double (cluster bootstrap)
res['by_class']['diff_single_minus_double'] = {}
for k in ('M1', 'B1', 'B2'):
    _, bs_ = wmean(CORR[k], cls_n == 2); _, bd_ = wmean(CORR[k], cls_n == 3)
    dd = bs_ - bd_
    res['by_class']['diff_single_minus_double'][k] = dict(diff_pp=float((CORR[k][cls_n == 2].mean() - CORR[k][cls_n == 3].mean()) * 100), ci=[float(x) * 100 for x in np.percentile(dd, [2.5, 97.5])])
q = np.quantile(first, [1 / 3, 2 / 3])
terc = np.where(first <= q[0], 0, np.where(first <= q[1], 1, 2))
res['by_position'] = dict(cutoffs=[float(x) for x in q], terciles={})
for t, nm in enumerate(('early', 'mid', 'late')):
    g = grp_acc(terc == t); g['switch_range'] = [int(first[terc == t].min()), int(first[terc == t].max())]; res['by_position']['terciles'][nm] = g

# peak window contains switch (first switch, then any switch), impossible videos, model windows
def peak_rate(key):
    a = clean1[key]; a = a if key == 'surprise' else np.nanmin(a, -1)   # [V,17]
    hits1 = []; hitsany = []; chance = []
    for k in range(P):
        v = imp_i[k]; sw = spl[ids[v]]['switches']
        if not sw: continue
        w = int(np.nanargmax(a[v]))
        def cont(s):
            j = -(-s // 2)  # first sampled index with native frame >= s
            return (2 * w <= j <= 2 * w + 15) and j <= 48
        hits1.append(cont(sw[0])); hitsany.append(any(cont(s) for s in sw))
        chance.append(np.mean([ (2 * ww <= -(-sw[0] // 2) <= 2 * ww + 15) for ww in range(17)]))
    return dict(n=len(hits1), first_switch_rate=float(np.mean(hits1) * 100), any_switch_rate=float(np.mean(hitsany) * 100), chance_uniform_first=float(np.mean(chance) * 100))
res['peak_window'] = {k: peak_rate(k) for k in ('surprise', 'B1', 'B2')}
# the same for possible videos' counterpart (control: peak in possible video relative to partner's switch)
def peak_rate_pos(key):
    a = clean1[key]; a = a if key == 'surprise' else np.nanmin(a, -1); h = []
    for k in range(P):
        sw = spl[ids[imp_i[k]]]['switches']
        if not sw: continue
        w = int(np.nanargmax(a[pos_i[k]])); j = -(-sw[0] // 2); h.append((2 * w <= j <= 2 * w + 15) and j <= 48)
    return float(np.mean(h) * 100)
res['peak_window_possible_control'] = {k: peak_rate_pos(k) for k in ('surprise', 'B1', 'B2')}

# ------------------------------------------------ (6) edits: clean vs edited pairwise correctness for M1
def pairs_corr(r, agg):
    a = align(r)['surprise']
    s = np.nanmean(a, 1) if agg == 'mean' else np.nanmax(a, 1)
    return s
def mcnemar(c0, c1):
    both = int(((c0 == 1) & (c1 == 1)).sum()); lost = int(((c0 == 1) & (c1 == 0)).sum()); gained = int(((c0 == 0) & (c1 == 1)).sum()); neither = int(((c0 == 0) & (c1 == 0)).sum())
    n = lost + gained
    p = binomtest(lost, n, 0.5).pvalue if n else 1.0
    return dict(correct_both=both, lost=lost, gained=gained, wrong_both=neither, mcnemar_p=float(p))
res['edits_pairwise'] = {}
for agg in ('mean', 'max'):
    s0 = pairs_corr(clean1, agg); t0 = tau_of(s0); d0 = s0[imp_i] - s0[pos_i]
    for ed in ('vflip', 'hflip', 'time_reversal'):
        r = find(f'P4_M1_ipdev_{ed}-high_s1')
        s1 = pairs_corr(r, agg); n_nan = int(np.isnan(s1).sum())
        d1 = s1[imp_i] - s1[pos_i]
        strict = mcnemar((d0 > 0).astype(int), (d1 > 0).astype(int))
        tau1 = tau_of(s0)  # tau from clean, as in H1
        c0 = L.acc_from_diff(d0, t0); c1 = L.acc_from_diff(d1, t0)
        res['edits_pairwise'][f'{ed}_{agg}'] = dict(n_videos=int(len(r['video_ids'])), n_nan=n_nan, acc_clean_strict=float((d0 > 0).mean() * 100), acc_edit_strict=float((d1 > 0).mean() * 100),
            acc_clean_tiehalf=float(c0.mean() * 100), acc_edit_tiehalf=float(c1.mean() * 100), strict=strict,
            tiehalf_binary_credit_gt_half=mcnemar((c0 > 0.5).astype(int), (c1 > 0.5).astype(int)))
# reversal run contents
rr = find('P4_M1_ipdev_time_reversal-high_s1'); rm = find('P4_M0r_ipdev_time_reversal-high_s1', must=False)
res['reversal_runs'] = dict(M1_n_videos=int(len(rr['video_ids'])), M1_labels={int(k): int((rr['label'] == k).sum()) for k in (0, 1)},
    M0r_n_videos=None if rm is None else int(len(rm['video_ids'])), M0r_labels=None if rm is None else {int(k): int((rm['label'] == k).sum()) for k in (0, 1)})

# ------------------------------------------------ (7) vflip shift direction (full-clip max, paired by video)
def shift(edit_run, clean_run, mask_possible=None):
    se = np.nanmax(edit_run['surprise'], 1); ids_e = list(edit_run['video_ids'])
    sc = np.nanmax(align(clean_run)['surprise'], 1) if False else None
    ci = {v: i for i, v in enumerate(clean_run['video_ids'])}
    c = np.nanmax(clean_run['surprise'], 1)[[ci[v] for v in ids_e]]
    d = se - c; tau = 2e-4 * np.median(c)
    return d, tau, np.array(edit_run['label'])
vf = find('P4_M1_ipdev_vflip-high_s1'); d, tau, lb = shift(vf, clean1)
res['vflip_shift_M1'] = {}
for nm, msk in (('all360', np.ones(len(d), bool)), ('possible180', lb == 0), ('impossible180', lb == 1)):
    dd = d[msk]
    res['vflip_shift_M1'][nm] = dict(n=int(msk.sum()), tau=float(tau), n_neg=int((dd < 0).sum()), n_pos=int((dd > 0).sum()), n_zero=int((dd == 0).sum()),
        frac_neg=float((dd < 0).mean() * 100), frac_pos=float((dd > 0).mean() * 100),
        n_up_gt_tau=int((dd > tau).sum()), n_tie=int((np.abs(dd) <= tau).sum()), detect_tiehalf=float(np.where(np.abs(dd) <= tau, .5, dd > tau).mean() * 100),
        sign_p=float(binomtest(int((dd > 0).sum()), int((dd != 0).sum()), .5).pvalue))
m0e = find('P4_M0r_ipdev_vflip-high_s1')
m0c = find('P4_M0r_ipdev_clean-init0_s1')
d0_, tau0, lb0 = shift(m0e, m0c)
res['vflip_shift_M0r_init0'] = dict(n=int(len(d0_)), tau=float(tau0), n_neg=int((d0_ < 0).sum()), n_pos=int((d0_ > 0).sum()), n_up_gt_tau=int((d0_ > tau0).sum()), n_tie=int((np.abs(d0_) <= tau0).sum()),
    frac_pos=float((d0_ > 0).mean() * 100), frac_neg=float((d0_ < 0).mean() * 100), detect_tiehalf=float(np.where(np.abs(d0_) <= tau0, .5, d0_ > tau0).mean() * 100),
    detect_strict_gt_tau=float((d0_ > tau0).mean() * 100), sign_p=float(binomtest(int((d0_ > 0).sum()), int((d0_ != 0).sum()), .5).pvalue))
json.dump(res, open('verify/p10_recompute.json', 'w'), indent=1)
print(json.dumps(res, indent=1)[:12000])
