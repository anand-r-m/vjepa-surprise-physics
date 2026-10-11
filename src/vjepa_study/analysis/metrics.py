"""CPU-only metrics for PROJECT_SPEC section 5. numpy/scipy only."""
from __future__ import annotations

import numpy as np
from scipy import stats

__all__ = ["aggregate", "pairwise_accuracy", "verdicts", "flip_rate", "mcnemar_exact",
           "holm", "auroc", "specificity_auroc", "bootstrap_auroc", "bootstrap_auroc_diff",
           "clopper_pearson", "detection_rate", "mean_sd_across_seeds"]


def aggregate(curves, how="max"):
    """Per-video scalar surprise from per-timestep curves (list of 1-D arrays or 2-D)."""
    f = {"max": np.max, "mean": np.mean}[how]
    return np.array([f(np.asarray(c, dtype=np.float64)) for c in curves])


def verdicts(s_imp, s_pos):
    """True where surprise(impossible) > surprise(possible) (strict; ties count as wrong)."""
    return np.asarray(s_imp, float) > np.asarray(s_pos, float)


def pairwise_accuracy(s_imp, s_pos):
    return float(verdicts(s_imp, s_pos).mean())


def flip_rate(verdict_edit, verdict_clean):
    """Fraction of pairs whose verdict differs from the clean verdict."""
    return float((np.asarray(verdict_edit, bool) != np.asarray(verdict_clean, bool)).mean())


def mcnemar_exact(correct_clean, correct_edit):
    """Exact two-sided McNemar test on paired correctness. Returns dict(b, c, p).
    b = clean correct & edit wrong, c = clean wrong & edit correct."""
    a, e = np.asarray(correct_clean, bool), np.asarray(correct_edit, bool)
    b, c = int((a & ~e).sum()), int((~a & e).sum())
    n = b + c
    p = 1.0 if n == 0 else float(min(1.0, 2 * stats.binom.cdf(min(b, c), n, 0.5)))
    return dict(b=b, c=c, p=p)


def holm(pvals):
    """Holm-Bonferroni adjusted p-values (same order as input)."""
    p = np.asarray(pvals, float)
    m = len(p)
    order = np.argsort(p)
    adj = np.empty(m)
    run = 0.0
    for rank, i in enumerate(order):
        run = max(run, (m - rank) * p[i])
        adj[i] = min(1.0, run)
    return adj


def auroc(x, y):
    """P(x > y) + 0.5 P(x = y) for x ~ first sample, y ~ second (Mann-Whitney)."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    r = stats.rankdata(np.concatenate([x, y]))
    u = r[: len(x)].sum() - len(x) * (len(x) + 1) / 2
    return float(u / (len(x) * len(y)))


def specificity_auroc(d_viol, d_abrupt):
    """P(Delta_viol > Delta_abrupt)."""
    return auroc(d_viol, d_abrupt)


def bootstrap_auroc(d_viol, d_abrupt, n_boot=10_000, seed=0, scene_viol=None,
                    scene_abrupt=None, alpha=0.05):
    """Percentile bootstrap CI for the specificity AUROC.

    Resamples scenes/pairs. If scene ids are given for both arrays, scenes are drawn
    with replacement from their union and all items in a drawn scene are included.
    Otherwise, equal-length arrays are resampled jointly by index (paired by pair),
    and unequal-length arrays are resampled independently.
    Returns dict(auroc, lo, hi, n_boot).
    """
    dv, da = np.asarray(d_viol, float), np.asarray(d_abrupt, float)
    rng = np.random.default_rng(seed)
    est = np.empty(n_boot)
    if scene_viol is not None and scene_abrupt is not None:
        sv, sa = np.asarray(scene_viol), np.asarray(scene_abrupt)
        uniq = np.unique(np.concatenate([sv, sa]))
        iv = {u: np.flatnonzero(sv == u) for u in uniq}
        ia = {u: np.flatnonzero(sa == u) for u in uniq}
        for b in range(n_boot):
            pick = uniq[rng.integers(0, len(uniq), size=len(uniq))]
            vi = np.concatenate([iv[u] for u in pick])
            ai = np.concatenate([ia[u] for u in pick])
            est[b] = auroc(dv[vi], da[ai]) if len(vi) and len(ai) else np.nan
    elif len(dv) == len(da):
        for b in range(n_boot):
            i = rng.integers(0, len(dv), size=len(dv))
            est[b] = auroc(dv[i], da[i])
    else:
        for b in range(n_boot):
            est[b] = auroc(dv[rng.integers(0, len(dv), size=len(dv))],
                           da[rng.integers(0, len(da), size=len(da))])
    lo, hi = np.nanpercentile(est, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return dict(auroc=auroc(dv, da), lo=float(lo), hi=float(hi), n_boot=n_boot)


def bootstrap_auroc_diff(dv_a, da_a, dv_b, da_b, n_boot=10_000, seed=0, alpha=0.05):
    """Paired AUROC_A - AUROC_B with percentile CI. Both models must be scored on the same
    items in the same order (arrays of equal length; item i is the same scene for A and B).
    Resamples items jointly for both models and both arrays."""
    dv_a, da_a, dv_b, da_b = (np.asarray(x, float) for x in (dv_a, da_a, dv_b, da_b))
    if not (len(dv_a) == len(dv_b) and len(da_a) == len(da_b)):
        raise ValueError("models must be scored on the same items")
    rng = np.random.default_rng(seed)
    same = len(dv_a) == len(da_a)
    est = np.empty(n_boot)
    for b in range(n_boot):
        iv = rng.integers(0, len(dv_a), size=len(dv_a))
        ia = iv if same else rng.integers(0, len(da_a), size=len(da_a))
        est[b] = auroc(dv_a[iv], da_a[ia]) - auroc(dv_b[iv], da_b[ia])
    lo, hi = np.percentile(est, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return dict(diff=auroc(dv_a, da_a) - auroc(dv_b, da_b), lo=float(lo), hi=float(hi),
                n_boot=n_boot)


def clopper_pearson(k, n, alpha=0.05):
    lo = 0.0 if k == 0 else float(stats.beta.ppf(alpha / 2, k, n - k + 1))
    hi = 1.0 if k == n else float(stats.beta.ppf(1 - alpha / 2, k + 1, n - k))
    return lo, hi


def detection_rate(s_edited, s_original, alpha=0.05):
    """Fraction of videos with S(edited) > S(original) with exact binomial CI."""
    k = int((np.asarray(s_edited, float) > np.asarray(s_original, float)).sum())
    n = len(s_edited)
    lo, hi = clopper_pearson(k, n, alpha)
    return dict(rate=k / n, k=k, n=n, lo=lo, hi=hi)


def mean_sd_across_seeds(values):
    v = np.asarray(values, float)
    return float(v.mean()), float(v.std(ddof=1)) if len(v) > 1 else float("nan")


# ======================================================================================
# Amendment A1 statistics (B2 ties, B7 H2 estimand, B8 outcome table, B9 H1, B11 H3)
# ======================================================================================
TIE_TOL = 1e-4
__all__ += ["TIE_TOL", "verdict_scores", "accuracy_ties", "tie_rate", "flip_rate_ties",
            "aggregate_S", "delta_viol", "pooled_type_auroc", "foil_accuracy",
            "h2_point", "stratified_cluster_indices", "cluster_bootstrap", "h2_bootstrap",
            "h2_outcome", "h1_bootstrap", "h1_decision", "h3_detection", "g2_pass"]


def aggregate_S(S, how="mean", c_index=None):
    """S: (W, nC) surprise for one video. c_index None -> min over C (released 'Filtered');
    int -> that fixed C (A2). how: 'mean' (avg over windows) | 'max'. NaN windows ignored."""
    S = np.asarray(S, float)
    s = S.min(axis=1) if c_index is None else S[:, c_index]
    return float(np.nanmax(s) if how == "max" else np.nanmean(s))


def verdict_scores(s_imp, s_pos, tol=TIE_TOL):
    """1 if S_imp - S_pos > tol, 0.5 if |.| <= tol (tie), 0 otherwise."""
    d = np.asarray(s_imp, float) - np.asarray(s_pos, float)
    return np.where(np.abs(d) <= tol, 0.5, (d > 0).astype(float))


def accuracy_ties(s_imp, s_pos, tol=TIE_TOL):
    return float(verdict_scores(s_imp, s_pos, tol).mean())


def tie_rate(s_imp, s_pos, tol=TIE_TOL):
    return float((np.abs(np.asarray(s_imp, float) - np.asarray(s_pos, float)) <= tol).mean())


def flip_rate_ties(v_edit, v_clean):
    """Flip = any change among {imp, poss, tie} (verdict_scores arrays)."""
    return float((np.asarray(v_edit) != np.asarray(v_clean)).mean())


def delta_viol(s_imp, s_pos):
    return np.asarray(s_imp, float) - np.asarray(s_pos, float)


def pooled_type_auroc(dv, da_by_type):
    """Equal weight per abrupt type: mean over types of AUROC(dv, da[type]) (tie = 0.5).
    Returns (pooled, {type: auroc})."""
    per = {k: auroc(dv, v) for k, v in da_by_type.items()}
    return float(np.mean(list(per.values()))), per


def foil_accuracy(s_imp, s_foil_by_type, tol=0.0):
    """mean_i 1[S(v_i) > S(edit_k(p_i))] pooled over types (ties 0.5)."""
    vals = []
    for v in s_foil_by_type.values():
        vals.append(verdict_scores(s_imp, v, tol).mean())
    return float(np.mean(vals))


def h2_point(dv, da, seeds_axis=True):
    """da: {type: array (n_seeds, n_pairs)} (deterministic types: repeat/ (1,n)).
    Per-seed pooled AUROC then average over seeds. Returns dict(auroc, seed_auroc, per_type)."""
    n_seed = max(np.asarray(v).shape[0] for v in da.values())
    seed_vals = []
    for s in range(n_seed):
        d = {k: np.asarray(v)[min(s, np.asarray(v).shape[0] - 1)] for k, v in da.items()}
        seed_vals.append(pooled_type_auroc(dv, d)[0])
    per = {k: float(np.mean([auroc(dv, np.asarray(v)[min(s, np.asarray(v).shape[0] - 1)])
                             for s in range(n_seed)])) for k, v in da.items()}
    return dict(auroc=float(np.mean(seed_vals)), seed_auroc=seed_vals, per_type=per)


def stratified_cluster_indices(scene_ids, blocks, rng):
    """One resample: draw scenes with replacement WITHIN each block (stratified), return
    the concatenated item indices of the drawn scenes."""
    scene_ids, blocks = np.asarray(scene_ids), np.asarray(blocks)
    out = []
    for b in np.unique(blocks):
        sc = np.unique(scene_ids[blocks == b])
        pick = sc[rng.integers(0, len(sc), size=len(sc))]
        for s in pick:
            out.append(np.flatnonzero(scene_ids == s))
    return np.concatenate(out)


def cluster_bootstrap(stat_fn, scene_ids, blocks, n_boot=10_000, seed=20261015):
    """Draw n_boot stratified cluster resamples; stat_fn(idx) -> dict[name]->float, evaluated
    on the SAME draw for every name (joint resampling across models)."""
    rng = np.random.default_rng(seed)
    rows = [stat_fn(stratified_cluster_indices(scene_ids, blocks, rng)) for _ in range(n_boot)]
    keys = rows[0].keys()
    return {k: np.array([r[k] for r in rows], float) for k in keys}


def _ci(x, alpha=0.05):
    lo, hi = np.nanpercentile(x, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return float(lo), float(hi)


def h2_bootstrap(models, scene_ids, blocks, n_boot=10_000, seed=20261015, ref="B1"):
    """DEPRECATED: superseded by prereg.py Holm-2 rule; do not use for confirmatory H2.

    models: {name: dict(dv=(n,), da={type: (n_seed, n)})}. Joint stratified cluster
    bootstrap; returns {name: dict(auroc, lo, hi, per_type)} plus paired differences
    'diff_<name>_minus_<ref>' CIs. Items are pairs; clusters are quadruplets."""
    def stat(idx):
        r = {}
        for n, m in models.items():
            r[n] = h2_point(m["dv"][idx], {k: np.asarray(v)[:, idx] for k, v in m["da"].items()})["auroc"]
        if ref in models:
            for n in models:
                if n != ref:
                    r[f"diff_{n}_minus_{ref}"] = r[n] - r[ref]
        return r
    draws = cluster_bootstrap(stat, scene_ids, blocks, n_boot, seed)
    out = {}
    for n, m in models.items():
        pt = h2_point(m["dv"], m["da"])
        lo, hi = _ci(draws[n])
        out[n] = dict(auroc=pt["auroc"], lo=lo, hi=hi, per_type=pt["per_type"], seed_auroc=pt["seed_auroc"])
    for k in draws:
        if k.startswith("diff_"):
            a, b = k[5:].split("_minus_")
            lo, hi = _ci(draws[k])
            out[k] = dict(diff=out[a]["auroc"] - out[b]["auroc"], lo=lo, hi=hi)
    return out


def h2_outcome(A, D_lo, per_type, A_hi=None, type_floor=0.65):
    """DEPRECATED: superseded by prereg.py Holm-2 rule; do not use for confirmatory H2.

    Exhaustive, mutually exclusive H2 outcome (B8). A = seed-mean pooled AUROC of the
    model, D_lo = lower paired-bootstrap CI bound of AUROC_M - AUROC_B1, per_type = {type:
    AUROC}. Returns (label, reversed_flag)."""
    rev = A_hi is not None and A_hi < 0.5
    if A >= 0.80:
        if D_lo <= 0:
            label = "Separable but not beyond low-level baseline"
        else:
            low = sorted(k for k, v in per_type.items() if v < type_floor)
            label = "Specific" if not low else f"Specific, except type {', '.join(low)}"
    elif A > 0.65:
        label = "Partial / inconclusive"
    else:
        label = "Not specific"
    return label, bool(rev)


# ---------------------------------------------------------------- H1 (B9)
def h1_bootstrap(scene_ids, blocks, v_clean, v_edit, v_dither_by_seed, n_boot=10_000,
                 seed=20261015, valid=None):
    """Cluster bootstrap for one edit. v_* are verdict_scores arrays (1/0.5/0) per pair.
    Returns dict(d_acc, d_acc_ci, flip, flip_ci, f0, p_flip_gt_floor) where
    p = one-sided bootstrap p(flip_e - f0 <= 0). `valid` masks pairs excluded by MJ4."""
    v_clean, v_edit = np.asarray(v_clean), np.asarray(v_edit)
    vd = [np.asarray(v) for v in v_dither_by_seed]
    ok = np.ones(len(v_clean), bool) if valid is None else np.asarray(valid, bool)

    def stat(idx):
        i = idx[ok[idx]]
        f0 = np.mean([np.mean(v[i] != v_clean[i]) for v in vd])
        fl = np.mean(v_edit[i] != v_clean[i])
        return dict(d_acc=v_edit[i].mean() - v_clean[i].mean(), flip=fl, excess=fl - f0)
    draws = cluster_bootstrap(stat, scene_ids, blocks, n_boot, seed)
    i = np.flatnonzero(ok)
    f0 = float(np.mean([np.mean(v[i] != v_clean[i]) for v in vd]))
    fl = float(np.mean(v_edit[i] != v_clean[i]))
    return dict(d_acc=float(v_edit[i].mean() - v_clean[i].mean()), d_acc_ci=_ci(draws["d_acc"]),
                flip=fl, flip_ci=_ci(draws["flip"]), f0=f0,
                p_flip_gt_floor=float(np.mean(draws["excess"] <= 0)), n=int(len(i)))


def h1_decision(d_acc, p_mcnemar_holm, flip, f0, p_flip_holm, d_acc_ci, flip_ci,
                clean_acc, eligible_min=0.80):
    """B9 rule. Returns 'descriptive' (clean acc < 80%), 'violated', 'invariant' or 'inconclusive'.
    d_acc in absolute fractions (-0.05 = -5 pp)."""
    if clean_acc < eligible_min:
        return "descriptive"
    if (d_acc <= -0.05 and p_mcnemar_holm < 0.05) or \
       (flip >= 0.10 and flip - f0 >= 0.05 and p_flip_holm < 0.05):
        return "violated"
    if d_acc_ci[0] > -0.05 and flip_ci[1] < 0.10:
        return "invariant"
    return "inconclusive"


# ---------------------------------------------------------------- H3 / G2 (B11)
def h3_detection(s_ctrl, s_ref, scene_ids=None, blocks=None, s_ctrl_m0=None, s_ref_m0=None,
                 n_boot=10_000, seed=20261015):
    """Detection rate 1[S(ctrl) > S(ref)] (point + Clopper-Pearson). ref = original video
    (a) or the hflip video (b). If M0r arrays given, also the paired difference
    detection_M1 - detection_M0r with a stratified cluster-bootstrap CI."""
    r = detection_rate(s_ctrl, s_ref)
    if s_ctrl_m0 is not None and scene_ids is not None:
        d1 = (np.asarray(s_ctrl, float) > np.asarray(s_ref, float)).astype(float)
        d0 = (np.asarray(s_ctrl_m0, float) > np.asarray(s_ref_m0, float)).astype(float)
        draws = cluster_bootstrap(lambda i: dict(d=d1[i].mean() - d0[i].mean()), scene_ids, blocks, n_boot, seed)
        r["diff_vs_m0r"] = float(d1.mean() - d0.mean())
        r["diff_ci"] = _ci(draws["d"])
    return r


def g2_pass(det_vflip, diff_ci_lo):
    """G2 (A1.10): vflip detection point estimate >= 0.80 and M1 - M0r CI above 0.
    Reversal alone cannot fail G2."""
    return bool(det_vflip >= 0.80 and diff_ci_lo > 0)
