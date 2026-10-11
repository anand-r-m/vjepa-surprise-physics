"""P7 verifier library: independent recomputation from raw arrays (no src/ imports, no analysis outputs).
Definitions from docs/PREREGISTRATION.md (sections 2, 4, 6). Extends verify/p6_recompute.py conventions."""
import numpy as np, json, glob, os
from math import comb
R = 'results/raw'
SEED = int(os.environ.get('P7_SEED', '20261015')); NB = 10000


def find(name, must=True):
    c = [p for p in glob.glob(f'{R}/*/results/{name}') if '_v1_' not in p]
    if not c:
        assert not must, name
        return None
    assert len(c) == 1, (name, c)
    z = np.load(c[0] + '/surprise.npz')
    d = {k: z[k] for k in z.files if k != 'target_feats'}
    d['_path'] = c[0]
    return d


clean1 = find('P4_M1_ipdev_clean_s1')
ids = list(clean1['video_ids']); pair = clean1['pair_id']; lab = clean1['label']
scene = clean1['scene_id']; block = clean1['block']
upair = sorted(set(pair)); P = len(upair)
pos_i = np.zeros(P, int); imp_i = np.zeros(P, int)
for k, pid in enumerate(upair):
    m = np.where(pair == pid)[0]; assert len(m) == 2
    a, b = m; pos_i[k], imp_i[k] = (a, b) if lab[a] == 0 else (b, a); assert lab[a] != lab[b]
pair_scene = np.array([scene[pos_i[k]] for k in range(P)])
scenes = sorted(set(pair_scene)); assert len(scenes) == 90
sc_idx = {s: i for i, s in enumerate(scenes)}; pair_sc = np.array([sc_idx[s] for s in pair_scene])
sc_block = np.array([s.split('/')[0] for s in scenes])

rng = np.random.default_rng(SEED)
counts = np.zeros((NB, 90))
for b in sorted(set(sc_block)):
    ix = np.where(sc_block == b)[0]
    draw = rng.integers(0, len(ix), (NB, len(ix)))
    for r in range(len(ix)): np.add.at(counts, (np.arange(NB), ix[draw[:, r]]), 1)
pair_w = counts[:, pair_sc]
assert (counts.sum(1) == 90).all()


def boot_mean(v): return (pair_w @ v) / pair_w.sum(1)


def align(r):
    out = {}
    ri = {v: i for i, v in enumerate(r['video_ids'])}
    sel = np.array([ri.get(v, -1) for v in ids])
    for k in ('surprise', 'S', 'B1', 'B2', 'B3'):
        if k in r:
            a = r[k]; o = np.full((len(ids),) + a.shape[1:], np.nan, np.float64)
            m = sel >= 0; o[m] = a[sel[m]]; out[k] = o
    return out


def W(r, key):
    """key in M (model surprise), B1, B2, B3 -> (V, windows), min over C for baselines"""
    a = align(r)
    return a['surprise'] if key == 'M' else np.nanmin(a[key], axis=-1)


def tau_of(scores, mult=2e-4): return mult * np.median(scores)


def cls(diff, tau): return np.where(diff > tau, 1, np.where(diff < -tau, -1, 0))


def acc_from_diff(diff, tau, mode='tiehalf'):
    if mode == 'tiehalf': return np.where(np.abs(diff) <= tau, 0.5, (diff > 0).astype(float))
    return (diff > 0).astype(float)


def holm(ps):
    ps = np.array(ps, float); o = np.argsort(ps); m = len(ps); adj = np.empty(m); run = 0
    for r, i in enumerate(o):
        run = max(run, (m - r) * ps[i]); adj[i] = min(1, run)
    return adj


def clean_acc_of(r, key='surprise'):
    a = r[key]
    s = np.nanmean(a if a.ndim == 2 else a.min(-1), axis=1)
    tau = tau_of(s); d = s[imp_i] - s[pos_i]
    return dict(tau=float(tau), median=float(np.median(s)), tiehalf=float(acc_from_diff(d, tau).mean()),
                strict=float(acc_from_diff(d, tau, 'strict').mean()), n_ties=int((np.abs(d) <= tau).sum()),
                tiehalf_credits=float(acc_from_diff(d, tau).sum()), exact_tie_tau0=float(acc_from_diff(d, 0.0).mean()),
                tiehalf_fixed_tau1e4=float(acc_from_diff(d, 1e-4).mean()), n_ties_fixed_tau1e4=int((np.abs(d) <= 1e-4).sum()))


# ---------------- H1
def runs_of(model, cond, seeds=(1, 2, 3)):
    out = []
    for s in seeds:
        r = find(f'P4_{model}_ipdev_{cond}_s{s}', must=False)
        if r is not None: out.append(r)
    return out


def h1_arrays(runs, ref, tau):
    s0 = np.nanmean(align(ref)['surprise'], 1); d0 = s0[imp_i] - s0[pos_i]
    y0 = acc_from_diff(d0, tau); c0 = cls(d0, tau)
    ys = []; fl = []; ys_s = []; fl_s = []
    for r in runs:
        s = np.nanmean(align(r)['surprise'], 1); d = s[imp_i] - s[pos_i]
        ys.append(acc_from_diff(d, tau)); fl.append((cls(d, tau) != c0).astype(float))
        # strict convention: tau = 0 (class = sign), accuracy (d>0)
        ys_s.append((d > 0).astype(float)); fl_s.append((cls(d, 0.0) != cls(d0, 0.0)).astype(float))
    return dict(n_runs=len(runs), y=np.mean(ys, 0), y0=y0, flip=np.mean(fl, 0), flip_strict=np.mean(fl_s, 0),
                y_strict=np.mean(ys_s, 0), y0_strict=(d0 > 0).astype(float))


def h1_stats(a, f0pair, keep, f0pair_strict=None):
    y, y0, f = a['y'], a['y0'], a['flip']
    k = keep.astype(float)

    def bm(v): return ((pair_w * (v * k)) @ np.ones(P)) / (pair_w * k).sum(1)
    dacc = float(((y - y0) * k).sum() / k.sum()); flip = float((f * k).sum() / k.sum()); f0 = float((f0pair * k).sum() / k.sum())
    bd = bm(y - y0); bf = bm(f) - bm(f0pair)
    p_d = min(1.0, 2 * min((bd >= 0).mean(), (bd <= 0).mean())); p_f = float((bf <= 0).mean())
    lo, hi = np.percentile(bd, [2.5, 97.5]); flo, fhi = np.percentile(bf, [2.5, 97.5])
    dd = (y - y0) * k; npos = int((dd > 0).sum()); nneg = int((dd < 0).sum()); n = npos + nneg
    ps = min(1.0, 2 * sum(comb(n, j) for j in range(0, min(npos, nneg) + 1)) / 2 ** n) if n > 0 else 1.0
    out = dict(n_pairs=int(k.sum()), dacc=dacc, flip=flip, f0=f0, flip_minus_f0=flip - f0, p_dacc_cluster=p_d,
               p_flip_vs_floor=p_f, dacc_ci=[float(lo), float(hi)], flip_minus_f0_ci=[float(flo), float(fhi)], p_sign=ps,
               acc_edit_tiehalf=float(((y) * k).sum() / k.sum()), acc_clean_tiehalf=float(((y0) * k).sum() / k.sum()),
               dacc_strict=float((((a['y_strict'] - a['y0_strict'])) * k).sum() / k.sum()),
               flip_strict=float((a['flip_strict'] * k).sum() / k.sum()))
    if f0pair_strict is not None:
        out['f0_strict'] = float((f0pair_strict * k).sum() / k.sum())
        ds_ = (a['y_strict'] - a['y0_strict']); bds = bm(ds_); bfs = bm(a['flip_strict']) - bm(f0pair_strict)
        out['dacc_strict_ci'] = [float(x) for x in np.percentile(bds, [2.5, 97.5])]
        out['p_dacc_cluster_strict'] = min(1.0, 2 * min((bds >= 0).mean(), (bds <= 0).mean())); out['p_flip_vs_floor_strict'] = float((bfs <= 0).mean())
        dd = ds_ * k; npos = int((dd > 0).sum()); nneg = int((dd < 0).sum()); n = npos + nneg
        out['p_sign_strict'] = min(1.0, 2 * sum(comb(n, j) for j in range(0, min(npos, nneg) + 1)) / 2 ** n) if n > 0 else 1.0
    return out


def holm_family(h, edits, hk_d='holm_dacc', hk_f='holm_flip', hk_s='holm_sign', hk_sf='holm_signfam_flip'):
    ps = [h[e]['p_dacc_cluster'] for e in edits] + [h[e]['p_flip_vs_floor'] for e in edits]
    a = holm(ps); m = len(edits)
    for j, e in enumerate(edits): h[e][hk_d] = float(a[j]); h[e][hk_f] = float(a[m + j])
    ps2 = [h[e]['p_sign'] for e in edits] + [h[e]['p_flip_vs_floor'] for e in edits]
    a2 = holm(ps2)
    for j, e in enumerate(edits): h[e][hk_s] = float(a2[j]); h[e][hk_sf] = float(a2[m + j])
    if 'p_dacc_cluster_strict' in h[edits[0]]:
        a3 = holm([h[e]['p_dacc_cluster_strict'] for e in edits] + [h[e]['p_flip_vs_floor_strict'] for e in edits])
        a4 = holm([h[e]['p_sign_strict'] for e in edits] + [h[e]['p_flip_vs_floor_strict'] for e in edits])
        for j, e in enumerate(edits):
            h[e]['holm_dacc_strict'] = float(a3[j]); h[e]['holm_flip_strict'] = float(a3[m + j]); h[e]['holm_sign_strict'] = float(a4[j])
    return h


# ---------------- H2
def mask_from_ton(tons):
    ww = np.arange(17); return np.array([[(4 * w + 30) >= t for w in ww] for t in tons])


def evmax(w, mask, idxs): return np.where(mask, w[idxs], -np.inf).max(1)


def cmpmat(dv, da, tau):
    d = dv[:, None] - da[None, :]
    return np.where(np.abs(d) <= tau, 0.5, (d > 0).astype(float))


TYPES = {'lighting_global': 'clean', 'lighting_local': 'clean', 'jolt_base': 'base', 'zoom_base': 'base'}
KEYS = ('M', 'B1', 'B2')


class Ctx:
    def __init__(self, model, clean_name, base_ref_name):
        self.model = model
        self.clean = find(clean_name)
        assert list(self.clean['video_ids']) == ids
        self.cw = {k: W(self.clean, k) for k in KEYS}
        self.full_max = {k: np.nanmax(self.cw[k], 1) for k in KEYS}
        self.TAU2 = {k: tau_of(self.full_max[k]) for k in KEYS}
        self.base = find(base_ref_name) if base_ref_name else None
        self.bw = {k: W(self.base, k) for k in KEYS} if self.base else None
        s = np.nanmean(self.clean['surprise'], 1)
        self.tau_mean = tau_of(s)


def h2_core(ctx, name_fn, tons, types=TYPES, tau=None):
    """name_fn(type, seed)->run name or None. returns per-type point & boot arrays for M,B1,B2."""
    tons = np.array(tons); mask = mask_from_ton(tons); excl = tons > 94; keepp = ~excl
    k0 = keepp.astype(float)
    wk = pair_w * keepp[None, :]; den = (wk.sum(1)) ** 2
    ER = {}
    for t in types:
        runs = [find(name_fn(t, s), must=False) if name_fn(t, s) else None for s in (1, 2, 3)]
        assert runs[0] is not None, (t, name_fn(t, 1))
        ER[t] = (runs, sum(r is not None for r in runs))
    pt = {k: {} for k in KEYS}; bt = {k: {} for k in KEYS}
    for k in KEYS:
        tauk = ctx.TAU2[k]
        dv = evmax(ctx.cw[k], mask, imp_i) - evmax(ctx.cw[k], mask, pos_i)
        for t, ref in types.items():
            ps_ = []; bs_ = []
            refw = ctx.cw[k] if ref == 'clean' else ctx.bw[k]
            sr = evmax(refw, mask, pos_i)
            for s in range(3):
                r = ER[t][0][s] if ER[t][0][s] is not None else ER[t][0][0]
                se = evmax(W(r, k), mask, pos_i)
                C = cmpmat(dv, se - sr, tauk)
                ps_.append((k0 @ C @ k0) / k0.sum() ** 2)
                bs_.append(((wk @ C) * wk).sum(1) / den)
            pt[k][t] = float(np.mean(ps_)); bt[k][t] = np.mean(bs_, 0)
    # A0
    a0 = {}
    for k in KEYS:
        tauk = ctx.TAU2[k]; d = evmax(ctx.cw[k], mask, imp_i) - evmax(ctx.cw[k], mask, pos_i)
        y = np.where(np.abs(d) <= tauk, 0.5, (d > 0).astype(float))
        a0[k] = dict(A0=float(y[keepp].mean()), ci=[float(x) for x in np.percentile(((pair_w * keepp) @ y) / (pair_w * keepp).sum(1), [2.5, 97.5])],
                     n_ties=int((np.abs(d) <= tauk).sum()), strict=float(((d > 0).astype(float))[keepp].mean()))
    return dict(pt=pt, bt=bt, a0=a0, n_late=int(excl.sum()), n_used=int(keepp.sum()), nseeds={t: ER[t][1] for t in types})


def summarize_h2(core, drop=()):
    ts = [t for t in core['pt']['M'] if t not in drop]
    A = {k: float(np.mean([core['pt'][k][t] for t in ts])) for k in KEYS}
    Ab = {k: np.mean([core['bt'][k][t] for t in ts], 0) for k in KEYS}
    out = dict(types=ts, A_point=A, A_ci={k: [float(x) for x in np.percentile(Ab[k], [2.5, 97.5])] for k in KEYS},
               per_type={k: {t: core['pt'][k][t] for t in ts} for k in KEYS})
    ps = []; D = {}
    for kk in ('B1', 'B2'):
        Db = Ab['M'] - Ab[kk]; p = max(float((Db <= 0).mean()), 1 / (NB + 1))
        D[kk] = dict(D=A['M'] - A[kk], ci=[float(x) for x in np.percentile(Db, [2.5, 97.5])], p_onesided=p); ps.append(p)
    a = holm(ps); D['B1']['holm2'] = float(a[0]); D['B2']['holm2'] = float(a[1])
    out['D'] = D
    return out


def outcome_row(summ, a0_m):
    A = summ['A_point']['M']; pt = summ['per_type']['M']; D = summ['D']
    sig = D['B1']['holm2'] < .05 and D['B2']['holm2'] < .05
    below = [t for t, v in pt.items() if v < 0.65]
    if A >= .8 and sig and not below: row = 'Specific'
    elif A >= .8 and sig: row = 'Specific except types'
    elif A >= .8: row = 'Separable but not beyond baseline'
    elif A > 0.65: row = 'Partial'
    else: row = 'Not specific'
    if summ['A_ci']['M'][1] < 0.5: row += ' (Reversed)'
    if a0_m < 0.85 and row.startswith(('Not specific', 'Partial')): row = 'Detection-limited (' + row + ')'
    return row, below


def per_type_D(core):
    """per-type paired bootstrap D_k for dose-response cells"""
    out = {}
    for t in core['pt']['M']:
        out[t] = {}
        for kk in ('B1', 'B2'):
            Db = core['bt']['M'][t] - core['bt'][kk][t]
            out[t][kk] = dict(A=core['pt']['M'][t], A_base=core['pt'][kk][t], D=core['pt']['M'][t] - core['pt'][kk][t],
                              ci=[float(x) for x in np.percentile(Db, [2.5, 97.5])], p_onesided=max(float((Db <= 0).mean()), 1 / (NB + 1)))
    return out
