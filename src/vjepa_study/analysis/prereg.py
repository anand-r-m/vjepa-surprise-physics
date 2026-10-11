"""Statistics exactly as specified in docs/PREREGISTRATION.md (DRAFT v2) sections 2, 6, 7.

Conventions
-----------
* Scores: per video S[w, C] -> min over C -> aggregate over windows (mean for H1, event-aligned max for
  H2, full-clip max for H3).
* Ties: tau_m = 2e-4 x median over the 360 clean dev videos of the per-video score S_m. |diff| <= tau_m
  is a tie and counts 0.5 (tie-half). Strict and exact-tie versions are sensitivity analyses.
* Window w spans native frames 4w .. 4w+30 (skip 2, 16 sampled frames, stride 2 sampled frames).
* All bootstraps are scene-cluster (quadruplet) resamples stratified by block, seed 20261015.
"""
from __future__ import annotations

import json

import numpy as np
from scipy import stats

from .metrics import stratified_cluster_indices

BOOT_SEED = 20261015
TAU_FACTOR = 2e-4
WIN_STRIDE_NATIVE, WIN_SPAN_NATIVE = 4, 30




# ----------------------------------------------------------------------------- scores, ties (sec 2)
def curve(S):
    """(W,nC) -> per-window score = min over C (the released 'Filtered' curve)."""
    return np.nanmin(np.asarray(S, float), axis=-1)


def video_score(S, how="mean", t_on=None, c_index=None):
    """Per-video scalar. how: 'mean' | 'max'. t_on: event-aligned window set W_i = {w: 4w+30 >= t_on}
    (same set for every score of pair i). c_index: fixed C (A2) instead of min over C."""
    S = np.asarray(S, float)
    c = S[:, c_index] if c_index is not None else curve(S)
    c = c[~np.isnan(c)]
    if t_on is not None:
        w = np.arange(len(c))
        keep = WIN_STRIDE_NATIVE * w + WIN_SPAN_NATIVE >= t_on
        if not keep.any():
            keep[-1] = True
        c = c[keep]
    return float(np.max(c) if how == "max" else np.mean(c))


def video_scores(d, key="S", how="mean", t_on=None, c_index=None):
    """Scores of all videos of a run dict. t_on: None | scalar | per-video array."""
    n = len(d["video_ids"])
    t = np.broadcast_to(np.asarray(np.nan if t_on is None else t_on, float), (n,))
    return np.array([video_score(np.asarray(d[key][i])[: int(d["lengths"][i])], how,
                                 None if np.isnan(t[i]) else t[i], c_index) for i in range(n)])


def tau_m(scores_360):
    """tau_m = 2e-4 x median over the 360 clean videos of the per-video score S_m."""
    return TAU_FACTOR * float(np.median(np.asarray(scores_360, float)))


def y_tiehalf(x, ref, tau, tie=0.5):
    """1 if x - ref > tau, `tie` (0.5) if |x - ref| <= tau, 0 otherwise. tau=0: exact ties only.
    Strict sensitivity (the released '<' convention): tau=0, tie=0, identical to y_strict."""
    d = np.asarray(x, float) - np.asarray(ref, float)
    return np.where(np.abs(d) <= tau, float(tie), (d > 0).astype(float))


def y_strict(x, ref):
    return (np.asarray(x, float) > np.asarray(ref, float)).astype(float)


def flip3(y_edit, y_clean):
    """Flip over {imp-higher, tie, poss-higher}: any change of the verdict (y in {0,.5,1})."""
    return (np.asarray(y_edit) != np.asarray(y_clean)).astype(float)


def pair_index(d):
    """Pairs of a run dict with label/pair_id: returns dict(pair_ids, pos, imp, scene, block)."""
    pid, lab = np.asarray(d["pair_id"]), np.asarray(d["label"])
    ids, pos, imp = [], [], []
    for p in dict.fromkeys(pid.tolist()):
        i = np.flatnonzero(pid == p)
        ids.append(p)
        pos.append(int(i[lab[i] == 0][0]))
        imp.append(int(i[lab[i] == 1][0]) if (lab[i] == 1).any() else -1)
    pos, imp = np.array(pos), np.array(imp)
    return dict(pair_ids=np.array(ids), pos=pos, imp=imp,
                scene=np.asarray(d["scene_id"])[pos], block=np.asarray(d["block"])[pos])


def clean_pair_y(d, tau, how="mean", t_on=None, key="S", tie=0.5):
    """Clean pairwise verdict y (tie-half) and strict per pair from a run dict containing both
    members. t_on: per-pair event time (event-aligned aggregation, same window set for both members)."""
    px = pair_index(d)
    tv = None if t_on is None else _per_video_t(d, px, np.asarray(t_on, float))
    s = video_scores(d, key=key, how=how, t_on=tv)
    return y_tiehalf(s[px["imp"]], s[px["pos"]], tau, tie), y_strict(s[px["imp"]], s[px["pos"]]), px


def _per_video_t(d, px, t):
    """Per-video t_on array from per-pair t_on (both members of a pair share it)."""
    if t is None:
        return None
    out = np.full(len(d["video_ids"]), np.nan)
    out[px["pos"]] = t
    ok = px["imp"] >= 0
    out[px["imp"][ok]] = t[ok]
    return out


# ----------------------------------------------------------------------------- H1 (sec 6)
def seed_average(per_seed_arrays):
    return np.mean(np.stack([np.asarray(a, float) for a in per_seed_arrays]), axis=0)


def h1_pair_level(y_seeds, y0):
    """y_e,i (seed-averaged) and flip_e,i (mean over seeds of 1[y_seed != y0]); deterministic edits
    pass a single seed."""
    y_seeds = [np.asarray(y, float) for y in y_seeds]
    return seed_average(y_seeds), seed_average([flip3(y, y0) for y in y_seeds])


def sign_test_exact(y_e, y0):
    """Exact two-sided sign test on pairs with y_e,i != y_0,i (direction of the change)."""
    dif = np.asarray(y_e, float) - np.asarray(y0, float)
    pos, neg = int((dif > 1e-12).sum()), int((dif < -1e-12).sum())
    n = pos + neg
    p = 1.0 if n == 0 else float(min(1.0, 2 * stats.binom.cdf(min(pos, neg), n, 0.5)))
    return dict(n_discordant=n, n_up=pos, n_down=neg, p=p)


def h1_eligible(acc_tiehalf, threshold=0.80):
    """H1-confirmatory iff clean tie-half accuracy (mean aggregation, 180 pairs) >= 80.0%."""
    return bool(acc_tiehalf >= threshold - 1e-12)


def _boot_p_two_sided(x):
    x = np.asarray(x, float)
    return float(min(1.0, 2 * min(np.mean(x >= 0), np.mean(x <= 0))))


def h1_family(edits, y0, f0_pair, scene, block, n_boot=10_000, seed=BOOT_SEED, valid=None):
    """H1 for one model. edits: {name: dict(y=(n,), flip=(n,))} for the 7 edits at high strength
    (pair level, seed-averaged). f0_pair: per-pair dither flip (mean over its 3 seeds). valid: {name:
    bool mask} (crop retention exclusion). Returns per-edit stats and Holm-14 decisions."""
    y0, f0_pair = np.asarray(y0, float), np.asarray(f0_pair, float)
    names = list(edits)
    masks = {k: np.ones(len(y0), bool) if valid is None or k not in valid else np.asarray(valid[k], bool) for k in names}
    rng = np.random.default_rng(seed)
    draws = {k: dict(dacc=[], flip=[], excess=[]) for k in names}
    for _ in range(n_boot):
        idx = stratified_cluster_indices(scene, block, rng)
        for k in names:
            i = idx[masks[k][idx]]
            fl = np.mean(edits[k]["flip"][i])
            draws[k]["dacc"].append(np.mean(edits[k]["y"][i] - y0[i]))
            draws[k]["flip"].append(fl)
            draws[k]["excess"].append(fl - np.mean(f0_pair[i]))
    f0 = float(np.mean(f0_pair))
    res = {}
    for k in names:
        m = masks[k]
        dacc = float(np.mean(edits[k]["y"][m] - y0[m]))
        fl = float(np.mean(edits[k]["flip"][m]))
        dr = {a: np.array(v) for a, v in draws[k].items()}
        res[k] = dict(n=int(m.sum()), n_excluded=int((~m).sum()), dacc=dacc,
                      dacc_ci=tuple(np.percentile(dr["dacc"], [2.5, 97.5]).tolist()),
                      flip=fl, flip_ci=tuple(np.percentile(dr["flip"], [2.5, 97.5]).tolist()),
                      excess=fl - float(np.mean(f0_pair[m])), excess_ci=tuple(np.percentile(dr["excess"], [2.5, 97.5]).tolist()),
                      sign=sign_test_exact(edits[k]["y"][m], y0[m]),
                      p_dacc_cluster=_boot_p_two_sided(dr["dacc"]),
                      p_flip_cluster=float(np.mean(dr["excess"] <= 0)))
    # Holm over 14 p-values (prereg sec 4/6): 7 Delta-acc + 7 flip-vs-floor (one-sided cluster bootstrap), two
    # families: exact sign test (sensitivity) and cluster bootstrap (governing, also for flip significance)
    p_sign = [res[k]["sign"]["p"] for k in names]
    p_clu = [res[k]["p_dacc_cluster"] for k in names]
    p_flip = [res[k]["p_flip_cluster"] for k in names]
    h_sign = holm(p_sign + p_flip)
    h_clu = holm(p_clu + p_flip)
    n = len(names)
    for j, k in enumerate(names):
        r = res[k]
        r["holm_sign"], r["holm_flip"], r["holm_dacc_cluster"] = float(h_sign[j]), float(h_sign[n + j]), float(h_clu[j])
        sig_sign, sig_clu = h_sign[j] < 0.05, h_clu[j] < 0.05
        r["dacc_sig"] = bool(sig_clu)                 # cluster result governs on disagreement
        r["dacc_sig_disagree"] = bool(sig_sign != sig_clu)
        r["holm_flip_cluster"] = float(h_clu[n + j])
        f0_k = float(np.mean(f0_pair[masks[k]]))      # masked floor under crop exclusion
        r["decision"] = h1_decision(r["dacc"], r["dacc_sig"], r["flip"], f0_k, bool(h_clu[n + j] < 0.05),
                                    r["dacc_ci"], r["excess_ci"])
    return dict(f0=f0, f0_valid=bool(f0 < 0.10), per_edit=res)


def h1_decision(dacc, dacc_sig, flip, f0, flip_sig, dacc_ci, excess_ci):
    """Violated: [dacc <= -5pp and Holm-sig] or [flip >= 10% and flip - f0 >= 5pp and Holm-sig flip test].
    Invariant: lower bound of dacc > -5pp and upper bound of (flip - f0) < 5pp. Else inconclusive."""
    if (dacc <= -0.05 and dacc_sig) or (flip >= 0.10 and flip - f0 >= 0.05 and flip_sig):
        return "violated"
    if dacc_ci[0] > -0.05 and excess_ci[1] < 0.05:
        return "invariant"
    return "inconclusive"


def h1_model_status(f0, clean_acc_tiehalf):
    """'confirmatory' | 'descriptive (floor unstable)' | 'descriptive (ineligible)'."""
    if f0 >= 0.10:
        return "descriptive (floor f0 >= 10%: verdicts unstable under an invisible perturbation)"
    if not h1_eligible(clean_acc_tiehalf):
        return "descriptive (clean accuracy < 80%)"
    return "confirmatory"


# ----------------------------------------------------------------------------- H2 (sec 6)
def auroc_tau(x, y, tau, tie=0.5):
    """P(x > y) + tie * P(|x - y| <= tau) over all pairs (x: delta_viol, y: delta_abrupt)."""
    x, y = np.asarray(x, float)[:, None], np.asarray(y, float)[None, :]
    d = x - y
    return float(((d > tau).sum() + tie * (np.abs(d) <= tau).sum()) / d.size)


def h2_point(dv, da, tau, tie=0.5):
    """da: {type: (n_seed, n)} (deterministic types: n_seed 1). Per seed: mean over types of per-type
    AUROC; then mean over seeds. Returns dict(auroc, seed_auroc, per_type)."""
    n_seed = max(np.asarray(v).shape[0] for v in da.values())
    row = lambda v, s: np.asarray(v)[min(s, np.asarray(v).shape[0] - 1)]
    seed_vals = [float(np.mean([auroc_tau(dv, row(v, s), tau, tie) for v in da.values()])) for s in range(n_seed)]
    per = {k: float(np.mean([auroc_tau(dv, row(v, s), tau, tie) for s in range(n_seed)])) for k, v in da.items()}
    return dict(auroc=float(np.mean(seed_vals)), seed_auroc=seed_vals, per_type=per)


def foil_acc(s_imp, s_foil, tau, tie=0.5):
    """mean over types and seeds of mean_i y(S(v_i) vs S(edit_k(p_i))) with ties at tau counted 0.5.
    s_foil: {type: (n_seed, n)}."""
    return float(np.mean([y_tiehalf(s_imp, np.asarray(v)[s], tau, tie).mean()
                          for v in s_foil.values() for s in range(np.asarray(v).shape[0])]))


def h2_bootstrap(models, scene, block, refs=("B1", "B2"), main="M1", n_boot=10_000, seed=BOOT_SEED):
    """models: {name: dict(dv=(n,), da={type:(n_seed,n)}, tau=float, y0=(n,) clean pair y under the
    H2 aggregation)}. All models on the same draw. Returns per-model A, CI, per-type, A0, R and
    D_k = A_main - A_ref_k with paired CIs, the one-sided paired-bootstrap p_k = P*[D_k* <= 0]
    (floored at 1/(n_boot+1)) and Holm-2 adjusted p's across the refs (prereg sec 6, v3.3)."""
    def stat(idx):
        r = {}
        for n, m in models.items():
            r[n] = h2_point(m["dv"][idx], {k: np.asarray(v)[:, idx] for k, v in m["da"].items()}, m["tau"], m.get("tie", 0.5))["auroc"]
            r[n + "|A0"] = float(np.mean(m["y0"][idx]))
        for ref in refs:
            if ref in models and main in models:
                r[f"D_{ref}"] = r[main] - r[ref]
        return r
    rng = np.random.default_rng(seed)
    rows = [stat(stratified_cluster_indices(scene, block, rng)) for _ in range(n_boot)]
    dr = {k: np.array([r[k] for r in rows]) for k in rows[0]}
    ci = lambda x: tuple(np.percentile(x, [2.5, 97.5]).tolist())
    out = {}
    for n, m in models.items():
        pt = h2_point(m["dv"], m["da"], m["tau"], m.get("tie", 0.5))
        a0 = float(np.mean(m["y0"]))
        out[n] = dict(A=pt["auroc"], A_ci=ci(dr[n]), per_type=pt["per_type"], seed_auroc=pt["seed_auroc"],
                      seed_sd=float(np.std(pt["seed_auroc"], ddof=1)) if len(pt["seed_auroc"]) > 1 else float("nan"),
                      A0=a0, A0_ci=ci(dr[n + "|A0"]), R=float((pt["auroc"] - 0.5) / (a0 - 0.5)) if abs(a0 - 0.5) > 1e-9 else float("nan"),
                      tau=m["tau"])
    for ref in refs:
        if f"D_{ref}" in dr:
            out[f"D_{ref}"] = dict(D=out[main]["A"] - out[ref]["A"], ci=ci(dr[f"D_{ref}"]),
                                   p=max(float(np.mean(dr[f"D_{ref}"] <= 0)), 1.0 / (n_boot + 1)))
    adj = holm([out[f"D_{r}"]["p"] for r in refs if f"D_{r}" in out])
    for r, a in zip([r for r in refs if f"D_{r}" in out], adj):
        out[f"D_{r}"]["p_holm"] = a
    return out


def holm(ps):
    """Holm step-down adjusted p-values, returned in the input order."""
    ps = np.asarray(ps, float)
    order = np.argsort(ps, kind="stable")
    adj, run = np.empty(len(ps)), 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = run
    return adj.tolist()


def h2_outcome(A, p_adj, per_type, A_hi=None, A0=None, type_floor=0.65, a0_floor=0.85, alpha=0.05, n_required=2):
    """Outcome table (sec 6, v3.3) with the detection-limited rule. p_adj: Holm-2 adjusted p-values of
    D_1 (vs B1) and D_2 (vs B2). 'Specific' needs n_required (=2) adjusted p < alpha; fewer supplied
    values than required counts as not significant. Returns (label, reversed_flag)."""
    rev = A_hi is not None and A_hi < 0.5
    if A >= 0.80:
        p_adj = list(p_adj) if np.ndim(p_adj) else [float(p_adj)]
        if len(p_adj) < n_required or not all(p < alpha for p in p_adj):
            return "Separable but not beyond low-level baseline", rev
        low = sorted(k for k, v in per_type.items() if v < type_floor)
        return ("Specific" if not low else f"Specific, except type {', '.join(low)}"), rev
    label = "Partial / inconclusive" if A > 0.65 else "Not specific"
    if A0 is not None and A0 < a0_floor:
        label = "Detection-limited (not specific / partial)"
    return label, rev


# ----------------------------------------------------------------------------- H3, G2 (sec 6, 7)
def detection(s_ctrl, s_ref, tau, tie=0.5):
    """d_i = 1 if S(ctrl) - S(ref) > tau, `tie` (0.5) if |.| <= tau, else 0."""
    return y_tiehalf(s_ctrl, s_ref, tau, tie)


def h3_analysis(det_a, det_b, det_a_m0, scene, block, n_boot=10_000, seed=BOOT_SEED):
    """det_a: (a) detection vs p for M1; det_b: (b) vflip vs hflip; det_a_m0: M0r (a). Credited iff the
    lower bound of det_a - det_a_m0 > 0 and the lower bound of (b) > 0.5."""
    rng = np.random.default_rng(seed)
    d, b, m = (np.asarray(x, float) for x in (det_a, det_b, det_a_m0))
    rows = []
    for _ in range(n_boot):
        i = stratified_cluster_indices(scene, block, rng)
        rows.append((d[i].mean(), b[i].mean(), d[i].mean() - m[i].mean()))
    r = np.array(rows)
    ci = lambda x: tuple(np.percentile(x, [2.5, 97.5]).tolist())
    out = dict(a=float(d.mean()), a_ci=ci(r[:, 0]), b=float(b.mean()), b_ci=ci(r[:, 1]),
               diff_m0r=float(d.mean() - m.mean()), diff_m0r_ci=ci(r[:, 2]))
    out["learned_sensitivity_credited"] = bool(out["diff_m0r_ci"][0] > 0 and out["b_ci"][0] > 0.5)
    out["g2"] = g2_pass(out["a"], out["b_ci"][0])
    return out


def g2_pass(det_a, b_lower):
    """G2: (a) >= 0.80 (point, tie-half) and (b) lower bound > 0.5. Reversal never gates."""
    return bool(det_a >= 0.80 and b_lower > 0.5)


# ----------------------------------------------------------------------------- strata, T1 (sec 6, 9)
def abrupt_onset_proxy(D, t_on, t_off):
    """Visible/occluded proxy: 'abrupt onset' iff D(t_on) >= 0.5 x mean D over the event window."""
    D = np.asarray(D, float)
    return bool(D[t_on] >= 0.5 * D[t_on:t_off].mean())


def stratified_values(values, groups):
    """Descriptive mean (and n) per group (block or onset proxy)."""
    values, groups = np.asarray(values, float), np.asarray(groups)
    return {str(g): dict(mean=float(values[groups == g].mean()), n=int((groups == g).sum())) for g in np.unique(groups)}


def paired_difference(y_a, y_b, scene, block, n_boot=10_000, seed=BOOT_SEED):
    """T1: paired clean difference (e.g. M1 - B2) with scene-cluster bootstrap CI."""
    d = np.asarray(y_a, float) - np.asarray(y_b, float)
    rng = np.random.default_rng(seed)
    bs = np.array([d[stratified_cluster_indices(scene, block, rng)].mean() for _ in range(n_boot)])
    return dict(diff=float(d.mean()), ci=tuple(np.percentile(bs, [2.5, 97.5]).tolist()))


def wilson(k, n, z=1.959964):
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return float(c - h), float(c + h)


def feature_distance(feats_edit, feats_ref):
    """Descriptor: mean over windows/tubelets/dims of |g(edited) - g(ref)| on stored pooled target features
    (M1 target encoder), (W, n_tub, D) arrays."""
    a, b = np.asarray(feats_edit, np.float32), np.asarray(feats_ref, np.float32)
    n = min(len(a), len(b))
    return float(np.nanmean(np.abs(a[:n] - b[:n])))


def h2_strata(models, groups, main="M1"):
    """Descriptive pooled AUROC (point estimates) of every model within each stratum (block / onset proxy)."""
    groups = np.asarray(groups)
    out = {}
    for g in np.unique(groups):
        m = groups == g
        out[str(g)] = {n: dict(A=h2_point(v["dv"][m], {k: np.asarray(x)[:, m] for k, x in v["da"].items()}, v["tau"], v.get("tie", 0.5))["auroc"],
                               n=int(m.sum())) for n, v in models.items()}
    return out


# ----------------------------------------------------------------------------- matching diagnostics, run meta (sec 3, 1)
def match_missed(ratio_summary, median_band=(0.95, 1.05), frac_min=0.90):
    """Types whose achieved-ratio summary (make_matched_strengths meta.mid_ratio_summary:
    {type: dict(median, frac_within_0p9_1p1)}) misses the target: median r in [0.95, 1.05] and
    >= 90% of pairs in [0.9, 1.1]. NaN median counts as missed."""
    out = []
    for t, v in ratio_summary.items():
        med, frac = v.get("median", float("nan")), v.get("frac_within_0p9_1p1", float("nan"))
        if not (median_band[0] <= med <= median_band[1] and frac >= frac_min - 1e-12):
            out.append(t)
    return sorted(out)


def restrict_types(models, drop):
    """Copy of an h2_bootstrap `models` dict with the types in `drop` removed from every model's da."""
    return {n: {**m, "da": {k: v for k, v in m["da"].items() if k not in set(drop)}} for n, m in models.items()}


def check_run_meta(metas, keys=("precision", "n_gpus", "repo_head"), allowed_heads=None):
    """metas: {run_id: meta dict or None}. Every contrast must compare runs of identical precision and
    code: within one model (the run id's model field) precision and n_gpus must agree, and repo_head
    must agree across all runs, or, if `allowed_heads` (the pre-registered allowlist of heads whose bundles are
    logged as equivalent, prereg sec 1) is given, every repo_head must be in it. Alias runs (status != done) are skipped. Returns dict(ok, mismatches, missing,
    dirty)."""
    def get(m, k):
        if k in m:
            return m[k]
        return (m.get("env", {}).get("bundle", {}) or {}).get(k)
    vals, missing, dirty = {}, [], []
    for rid, m in metas.items():
        if m is None:
            missing.append(rid)
            continue
        if m.get("status", "done") != "done":
            continue
        model = rid.split("_")[1] if "_" in rid else rid
        for k in keys:
            vals.setdefault((model if k != "repo_head" else "*", k), {})[rid] = get(m, k)
        if (m.get("env", {}).get("bundle", {}) or {}).get("repo_dirty"):
            dirty.append(rid)
    mism = []
    for (grp, k), d in vals.items():
        distinct = {json.dumps(v, sort_keys=True) for v in d.values()}
        if k == "repo_head" and allowed_heads is not None:
            bad = sorted(str(h) for h in d.values() if h not in set(allowed_heads))
            if bad:
                mism.append(dict(group=grp, key=k, values=sorted(distinct), not_in_allowlist=bad,
                                 runs={r: v for r, v in d.items()}))
            continue
        if len(distinct) > 1:
            mism.append(dict(group=grp, key=k, values=sorted(distinct),
                             runs={r: v for r, v in d.items()}))
    return dict(ok=not mism, mismatches=mism, missing=sorted(missing), dirty=sorted(dirty))
