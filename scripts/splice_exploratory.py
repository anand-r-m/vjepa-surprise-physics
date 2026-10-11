"""EXPLORATORY, POST-HOC splice-detector analysis (no GPU; stored arrays + dev pixels only).

Run: PYTHONPATH=src .venv/bin/python scripts/splice_exploratory.py
Writes results/analysis/exploratory/splice_EXPLORATORY.json, figures/splice_EXPLORATORY_post-hoc.pdf.
Frozen scoring functions are imported from vjepa_study.analysis.prereg (not edited): per-video score = mean over
windows of min over C; tau_m = 2e-4 x median over the 360 clean videos of that score; tie-half and strict verdicts.
Edited-run verdicts use the tau_m of the same model's clean run.

Bins and decision rule fixed BEFORE looking at the outcome tables:
  * splice position = first frame (native index 0..99) at which the impossible video leaves its paired possible video;
    bins = terciles of that value over the 180 pairs (np.quantile at 1/3, 2/3; <= q1 | (q1,q2] | > q2).
  * single = 1 switch, double = 2 switches (out-and-back), derived from exact pixel equality with the quadruplet's possible videos.
  * Splice-detector hypothesis (operational): supported if BOTH E1 (Spearman rho of M1 margin vs B2 margin, scene-cluster
    bootstrap 95% CI lower bound > 0) and E2 (acc_tiehalf(M1 | B2 right) - acc_tiehalf(M1 | B2 wrong), CI lower bound > 0)
    hold; not supported if neither holds; inconclusive otherwise. Splice-position / single-vs-double / edit tables are descriptive.
"""
import json
from pathlib import Path

import numpy as np
from scipy import stats

from vjepa_study.analysis import prereg as P
from vjepa_study.analysis.metrics import stratified_cluster_indices

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "results/raw"
NPZ = ROOT / "kaggle/datasets/intphys-dev-npz"
N_BOOT = 10_000
RUNS = dict(
    M1_clean=RAW / "p4_clean_m1/results/P4_M1_ipdev_clean_s1",
    M0r_clean0=RAW / "p4_clean_m1/results/P4_M0r_ipdev_clean-init0_s1",
    M0r_clean1=RAW / "p4_clean_m1/results/P4_M0r_ipdev_clean-init1_s1",
    M0r_clean2=RAW / "p4_clean_m1/results/P4_M0r_ipdev_clean-init2_s1",
    M1_vflip=RAW / "g2_controls/results/P4_M1_ipdev_vflip-high_s1",
    M1_reversal=RAW / "g2_controls/results/P4_M1_ipdev_time_reversal-high_s1",
    M1_hflip=RAW / "g2_controls/results/P4_M1_ipdev_hflip-high_s1",
    M0r_vflip=RAW / "g2_controls/results/P4_M0r_ipdev_vflip-high_s1",
    M0r_reversal=RAW / "g2_controls/results/P4_M0r_ipdev_time_reversal-high_s1",
)
CLEAN_OF = {"M1_vflip": "M1_clean", "M1_reversal": "M1_clean", "M1_hflip": "M1_clean",
            "M0r_vflip": "M0r_clean0", "M0r_reversal": "M0r_clean0"}


def load(p):
    return {k: v for k, v in np.load(p / "surprise.npz", allow_pickle=True).items()}


# ------------------------------------------------------------------ splice structure from pixels
def splice_structure(d):
    ids = list(d["video_ids"])
    lab = d["label"]
    out = {}
    px = P.pair_index(d)
    for scene in sorted(set(d["scene_id"])):
        vs = [v for v in ids if v.startswith(scene + "/")]
        F = {v: np.load(NPZ / f"{v.replace('/', '_')}.npz")["frames"] for v in vs}
        pos = [v for v in vs if lab[ids.index(v)] == 0]
        for i in [v for v in vs if lab[ids.index(v)] == 1]:
            src = []
            for t in range(100):
                m = tuple(p for p in pos if (F[p][t] == F[i][t]).all())
                src.append(m)
            assert all(len(m) == 1 for m in src), f"{i}: frame not matched to exactly one possible video"
            sw = [t for t in range(1, 100) if src[t] != src[t - 1]]
            partner = src[0][0]
            pair_of_i = d["pair_id"][ids.index(i)]
            assert d["pair_id"][ids.index(partner)] == pair_of_i, f"{i}: pixel partner {partner} is not the paired possible video"
            out[pair_of_i] = dict(imp=i, pos=partner, switches=sw, n_switch=len(sw), t1=sw[0], t2=sw[1] if len(sw) > 1 else None)
    return out


# ------------------------------------------------------------------ per-pair quantities
def per_pair(d, key, tau, order):
    px = P.pair_index(d)
    s = P.video_scores(d, key, "mean")
    marg = s[px["imp"]] - s[px["pos"]]
    y = P.y_tiehalf(s[px["imp"]], s[px["pos"]], tau)
    ys = P.y_strict(s[px["imp"]], s[px["pos"]])
    ix = {p: k for k, p in enumerate(px["pair_ids"])}
    o = np.array([ix[p] for p in order])
    return marg[o], y[o], ys[o], s, px


def tau_of(d, key):
    return P.tau_m(P.video_scores(d, key, "mean"))


def wil(k, n):
    return None if n == 0 else [float(x) for x in P.wilson(float(k), n)]


class Boot:
    def __init__(self, scene, block, n=N_BOOT, seed=P.BOOT_SEED):
        rng = np.random.default_rng(seed)
        self.idx = [stratified_cluster_indices(scene, block, rng) for _ in range(n)]

    def ci(self, fn):
        v = []
        for ix in self.idx:
            try:
                r = fn(ix)
            except Exception:
                continue
            if r is not None and np.isfinite(r):
                v.append(r)
        return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] if len(v) > 100 else None


def sub_acc(y, ys, mask, B):
    n = int(mask.sum())
    if n == 0:
        return dict(n=0)
    k = float(y[mask].sum())
    return dict(n=n, n_ties=int((y[mask] == 0.5).sum()), acc_tiehalf=float(y[mask].mean()), acc_strict=float(ys[mask].mean()),
                wilson_tiehalf=wil(k, n), wilson_strict=wil(float(ys[mask].sum()), n),
                boot_tiehalf=B.ci(lambda ix: y[ix][mask[ix]].mean() if mask[ix].any() else None))


def sub_diff(y, mask_a, mask_b, B):
    f = lambda ix: (y[ix][mask_a[ix]].mean() - y[ix][mask_b[ix]].mean()) if mask_a[ix].any() and mask_b[ix].any() else None
    return dict(diff=float(y[mask_a].mean() - y[mask_b].mean()), boot95=B.ci(f))


def corr(a, b, B):
    rho = stats.spearmanr(a, b)[0]
    r = stats.pearsonr(a, b)[0]
    return dict(spearman=float(rho), spearman_boot95=B.ci(lambda ix: stats.spearmanr(a[ix], b[ix])[0]),
                pearson=float(r), pearson_boot95=B.ci(lambda ix: stats.pearsonr(a[ix], b[ix])[0]), n=len(a))


def main():
    R = {k: load(v) for k, v in RUNS.items()}
    d = R["M1_clean"]
    px0 = P.pair_index(d)
    order = list(px0["pair_ids"])
    scene = px0["scene"]
    block = px0["block"]
    B = Boot(scene, block)
    sp = splice_structure(d)
    t1 = np.array([sp[p]["t1"] for p in order])
    nsw = np.array([sp[p]["n_switch"] for p in order])
    q1, q2 = np.quantile(t1, [1 / 3, 2 / 3])
    tbin = np.where(t1 <= q1, 0, np.where(t1 <= q2, 1, 2))
    bin_names = [f"t1<={q1:.1f}", f"{q1:.1f}<t1<={q2:.1f}", f"t1>{q2:.1f}"]
    out = dict(label="EXPLORATORY post-hoc; not preregistered; not tuned on outcomes", n_pairs=len(order))
    out["splice_structure"] = dict(
        n_single=int((nsw == 1).sum()), n_double=int((nsw == 2).sum()), n_other=int(((nsw != 1) & (nsw != 2)).sum()),
        t1=dict(min=int(t1.min()), q1=float(q1), median=float(np.median(t1)), q2=float(q2), max=int(t1.max())),
        tercile_bin_names=bin_names, tercile_counts=[int((tbin == i).sum()) for i in range(3)],
        n_pairs_by_block={str(b): int((block == b).sum()) for b in np.unique(block)},
        single_by_block={str(b): int(((nsw == 1) & (block == b)).sum()) for b in np.unique(block)},
        double_by_block={str(b): int(((nsw == 2) & (block == b)).sum()) for b in np.unique(block)},
        double_t1_vs_single_t1_median=[float(np.median(t1[nsw == 2])), float(np.median(t1[nsw == 1]))],
        double_segment_len_median=float(np.median([sp[p]["t2"] - sp[p]["t1"] for p in order if sp[p]["t2"] is not None])),
        pixel_partner_equals_pair_possible=True)

    # clean per-pair for M1 and baselines (from the M1 run), M0r
    q = {}
    taus = {}
    for key in ("S", "B1", "B2", "B3"):
        taus[key] = tau_of(d, key)
        q[key] = per_pair(d, key, taus[key], order)[:3]
    m1m, m1y, m1ys = q["S"]
    b2m, b2y, b2ys = q["B2"]
    b1m, b1y, b1ys = q["B1"]
    out["clean_accuracy_check"] = dict(M1_tiehalf=float(m1y.mean()), M1_strict=float(m1ys.mean()), B1_tiehalf=float(b1y.mean()),
                                       B2_tiehalf=float(b2y.mean()), B2_strict=float(b2ys.mean()), tau=taus)

    # (1) correlations
    out["q1_margin_correlation"] = dict(
        M1_vs_B2=corr(m1m, b2m, B), M1_vs_B1=corr(m1m, b1m, B), B1_vs_B2=corr(b1m, b2m, B),
        M1_vs_B2_by_block={str(b): corr(m1m[block == b], b2m[block == b], Boot(scene[block == b], block[block == b], n=2000))
                           for b in np.unique(block)},
        M1_vs_B2_single=corr(m1m[nsw == 1], b2m[nsw == 1], Boot(scene[nsw == 1], block[nsw == 1], n=2000)),
        M1_vs_B2_double=corr(m1m[nsw == 2], b2m[nsw == 2], Boot(scene[nsw == 2], block[nsw == 2], n=2000)))
    for nm in ("M0r_clean0", "M0r_clean1", "M0r_clean2"):
        mm = per_pair(R[nm], "S", tau_of(R[nm], "S"), order)[0]
        out["q1_margin_correlation"][f"{nm}_vs_B2"] = corr(mm, b2m, B)

    # (2) accuracy by B2 / B1 right vs wrong (strict direction, tie-half for membership of exact ties reported)
    def groups(yr):
        return dict(right=yr == 1.0, wrong=yr == 0.0, tie=yr == 0.5)
    q2 = {}
    for nm, yb in (("B2", b2y), ("B1", b1y)):
        g = groups(yb)
        q2[nm] = {k: dict(M1=sub_acc(m1y, m1ys, m, B)) for k, m in g.items()}
        q2[nm]["M1_right_minus_wrong_tiehalf"] = sub_diff(m1y, g["right"], g["wrong"], B)
        q2[nm]["M1_right_minus_wrong_strict"] = sub_diff(m1ys, g["right"], g["wrong"], B)
        # reverse direction: B2 accuracy by M1 right/wrong
    gm = groups(m1y)
    q2["B2_acc_given_M1"] = {k: sub_acc(b2y, b2ys, m, B) for k, m in gm.items()}
    both = (b2y == 1) & (m1y == 1)
    q2["contingency_M1_vs_B2_tiehalf_verdicts"] = dict(both_right=int(both.sum()), m1_only=int(((m1y == 1) & (b2y == 0)).sum()),
                                                      b2_only=int(((m1y == 0) & (b2y == 1)).sum()),
                                                      both_wrong=int(((m1y == 0) & (b2y == 0)).sum()),
                                                      m1_tie=int((m1y == 0.5).sum()), b2_tie=int((b2y == 0.5).sum()))
    out["q2_accuracy_by_baseline_correctness"] = q2

    # (3) position / single-double / block
    def table(y, ys, margin, extra=None):
        t = {}
        for i, nm in enumerate(bin_names):
            m = tbin == i
            t["pos_tercile:" + nm] = dict(sub_acc(y, ys, m, B), margin_median=float(np.median(margin[m])), margin_mean=float(margin[m].mean()))
        for nm, m in (("single", nsw == 1), ("double", nsw == 2)):
            t[nm] = dict(sub_acc(y, ys, m, B), margin_median=float(np.median(margin[m])), margin_mean=float(margin[m].mean()))
        for b in np.unique(block):
            m = block == b
            t["block:" + str(b)] = dict(sub_acc(y, ys, m, B), margin_median=float(np.median(margin[m])), margin_mean=float(margin[m].mean()))
        t["spearman_margin_vs_t1"] = corr(margin, t1.astype(float), B)
        t["spearman_margin_vs_dist_to_end_100-t1"] = corr(margin, 100.0 - t1, B)
        return t
    q3 = dict(M1=table(m1y, m1ys, m1m), B2=table(b2y, b2ys, b2m), B1=table(b1y, b1ys, b1m))
    q3["M1_single_minus_double_tiehalf"] = sub_diff(m1y, nsw == 1, nsw == 2, B)
    q3["M1_tercile3_minus_tercile1_tiehalf"] = sub_diff(m1y, tbin == 2, tbin == 0, B)
    q3["B2_acc_within_M1_strata_single_double"] = {nm: sub_acc(b2y, b2ys, m, B) for nm, m in (("single", nsw == 1), ("double", nsw == 2))}
    # peak window vs switch frame (descriptive)
    pk = {}
    for nm, dd in (("M1", d), ("B2", d)):
        key = "S" if nm == "M1" else "B2"
        px = P.pair_index(dd)
        ix = {p: k for k, p in enumerate(px["pair_ids"])}
        res = {}
        for role in ("imp", "pos"):
            hit, chance = [], []
            for p in order:
                v = px[role][ix[p]]
                c = P.curve(np.asarray(dd[key][v])[: int(dd["lengths"][v])])
                w = int(np.nanargmax(c))
                sw = [sp[p]["t1"]] + ([sp[p]["t2"]] if sp[p]["t2"] is not None else [])
                cov = lambda ww: any(4 * ww <= s <= 4 * ww + 30 for s in sw)
                hit.append(cov(w))
                chance.append(np.mean([cov(ww) for ww in range(len(c))]))
            res[role] = dict(frac_peak_window_covers_switch=float(np.mean(hit)), chance_frac_if_peak_uniform=float(np.mean(chance)))
        pk[nm] = res
    q3["peak_window_covers_a_switch_frame"] = pk
    out["q3_splice_position_and_type"] = q3

    # (4) M0r and edited runs
    def run_block(nm):
        dd = R[nm]
        base = R[CLEAN_OF.get(nm, nm)]
        tau = tau_of(base, "S")
        mg, y, ys, s, _ = per_pair(dd, "S", tau, order)
        res = dict(tau_used=tau, acc_tiehalf=float(y.mean()), acc_strict=float(ys.mean()), n_ties=int((y == 0.5).sum()),
                   by_B2_correctness={k: sub_acc(y, ys, m, B) for k, m in groups(b2y).items() if k != "tie"},
                   by_B2_right_minus_wrong_tiehalf=sub_diff(y, b2y == 1, b2y == 0, B),
                   spearman_margin_vs_B2margin=corr(mg, b2m, B),
                   by_splice=table(y, ys, mg))
        return res, mg, y, ys
    q4, EM = {}, {}
    for nm in RUNS:
        if nm == "M1_clean":
            continue
        if (R[nm]["label"] == 1).sum() == 0:      # M0r vflip/reversal runs hold the 180 possible videos only: no pairs to score
            q4[nm] = dict(skipped="run contains possible videos only (no impossible members); pairwise verdicts undefined")
            continue
        q4[nm], mg, y, ys = run_block(nm)
        EM[nm] = (mg, y, ys)
    # does the correct-verdict set change under vflip/reversal/hflip (M1)? (strict-direction correctness sets)
    ch = {}
    for nm in ("M1_vflip", "M1_reversal", "M1_hflip"):
        mg, y, ys = EM[nm]
        c0, c1 = m1ys == 1, ys == 1
        c0h, c1h = m1y == 1, y == 1
        n01, n10 = int((~c0 & c1).sum()), int((c0 & ~c1).sum())
        ch[nm] = dict(both_correct=int((c0 & c1).sum()), lost=n10, gained=n01, both_wrong=int((~c0 & ~c1).sum()),
                      jaccard_correct_sets=float((c0 & c1).sum() / (c0 | c1).sum()),
                      mcnemar_exact_p=float(stats.binomtest(n01, n01 + n10, 0.5).pvalue) if n01 + n10 else None,
                      verdict_flip_rate_3way=float(np.mean(m1y != y)),
                      spearman_clean_margin_vs_edited_margin=corr(m1m, mg, B),
                      lost_by_position_tercile=[int((c0 & ~c1 & (tbin == i)).sum()) for i in range(3)],
                      gained_by_position_tercile=[int((~c0 & c1 & (tbin == i)).sum()) for i in range(3)],
                      lost_by_B2_right=int((c0 & ~c1 & (b2y == 1)).sum()), lost_by_B2_wrong=int((c0 & ~c1 & (b2y == 0)).sum()),
                      gained_by_B2_right=int((~c0 & c1 & (b2y == 1)).sum()), gained_by_B2_wrong=int((~c0 & c1 & (b2y == 0)).sum()),
                      acc_strict_on_B2_right_clean_vs_edited=[float(m1ys[b2y == 1].mean()), float(ys[b2y == 1].mean())],
                      acc_strict_on_B2_wrong_clean_vs_edited=[float(m1ys[b2y == 0].mean()), float(ys[b2y == 0].mean())])
    q4["M1_correct_set_change_vs_clean"] = ch
    q4["note"] = ("M0r vflip/reversal skipped (possible videos only). reversal: splice position bins use the ORIGINAL (unreversed) switch frame t1; in the reversed clip the switch is at 99-t1. "
                  "Edited-run verdicts use the same model's clean tau_m.")
    out["q4_edited_and_M0r"] = q4

    # verdict (rule fixed in docstring)
    e1 = out["q1_margin_correlation"]["M1_vs_B2"]["spearman_boot95"][0] > 0
    e2 = q2["B2"]["M1_right_minus_wrong_tiehalf"]["boot95"][0] > 0
    out["verdict_rule_result"] = dict(E1_rho_CI_lower_gt0=bool(e1), E2_acc_diff_CI_lower_gt0=bool(e2),
                                      splice_detector_hypothesis="supported" if (e1 and e2) else "not supported" if not (e1 or e2) else "inconclusive")
    p = ROOT / "results/analysis/exploratory"
    p.mkdir(parents=True, exist_ok=True)
    (p / "splice_EXPLORATORY.json").write_text(json.dumps(out, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
    make_fig(out, m1m, b2m, m1y, b2y, t1, nsw, tbin, bin_names, EM)
    print(json.dumps(out["verdict_rule_result"]), out["splice_structure"]["n_single"], out["splice_structure"]["n_double"])


def make_fig(out, m1m, b2m, m1y, b2y, t1, nsw, tbin, bin_names, EM):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 4, figsize=(15, 3.6))
    gr = ["0.1", "0.45", "0.75"]
    # a: scatter of ranks
    ra, rb = stats.rankdata(b2m) / len(b2m), stats.rankdata(m1m) / len(m1m)
    for m, mk, nm in ((nsw == 1, "o", "single"), (nsw == 2, "^", "double")):
        ax[0].scatter(ra[m], rb[m], marker=mk, facecolors="none" if mk == "o" else "0.3", edgecolors="0.1", s=18, label=nm)
    c = out["q1_margin_correlation"]["M1_vs_B2"]
    ax[0].set(xlabel="B2 margin (rank)", ylabel="M1 margin (rank)",
              title=f"(a) rho={c['spearman']:.2f} [{c['spearman_boot95'][0]:.2f},{c['spearman_boot95'][1]:.2f}]")
    ax[0].legend(fontsize=7, frameon=False)
    # b: accuracy by B2 / B1 right vs wrong
    q2 = out["q2_accuracy_by_baseline_correctness"]
    xs, k = [], 0
    for nm in ("B2", "B1"):
        for j, grp in enumerate(("right", "wrong")):
            a = q2[nm][grp]["M1"]
            if a["n"] == 0:
                continue
            lo, hi = a["boot_tiehalf"] or a["wilson_tiehalf"]
            ax[1].bar(k, a["acc_tiehalf"], color=gr[2] if grp == "wrong" else gr[0], hatch="//" if grp == "wrong" else "",
                      edgecolor="0.1", yerr=[[a["acc_tiehalf"] - lo], [hi - a["acc_tiehalf"]]], capsize=3)
            ax[1].text(k, 0.03, f"n={a['n']}", ha="center", fontsize=7, color="w" if grp == "right" else "0.1")
            xs.append((k, f"{nm}\n{grp}"))
            k += 1
        k += 0.6
    ax[1].set_xticks([x for x, _ in xs]); ax[1].set_xticklabels([l for _, l in xs], fontsize=7)
    ax[1].axhline(0.5, color="0.3", ls=":")
    ax[1].set(ylabel="M1 pairwise acc (tie-half)", ylim=(0, 1.05), title="(b) M1 acc by baseline verdict")
    # c: margin vs t1
    for m, mk, nm in ((nsw == 1, "o", "single"), (nsw == 2, "^", "double")):
        ax[2].scatter(t1[m], m1m[m], marker=mk, facecolors="none" if mk == "o" else "0.3", edgecolors="0.1", s=18, label=nm)
    ax[2].axhline(0, color="0.3", ls=":")
    cc = out["q3_splice_position_and_type"]["M1"]["spearman_margin_vs_t1"]
    ax[2].set(xlabel="splice switch frame t1 (native)", ylabel="M1 margin S_imp - S_pos",
              title=f"(c) rho={cc['spearman']:.2f} [{cc['spearman_boot95'][0]:.2f},{cc['spearman_boot95'][1]:.2f}]")
    ax[2].legend(fontsize=7, frameon=False)
    # d: acc by tercile for M1 clean, vflip, reversal, B2
    t = out["q3_splice_position_and_type"]
    series = [("M1 clean", [t["M1"]["pos_tercile:" + n]["acc_tiehalf"] for n in bin_names], "0.1", "o", "-"),
              ("M1 vflip", [out["q4_edited_and_M0r"]["M1_vflip"]["by_splice"]["pos_tercile:" + n]["acc_tiehalf"] for n in bin_names], "0.4", "s", "--"),
              ("M1 reversal", [out["q4_edited_and_M0r"]["M1_reversal"]["by_splice"]["pos_tercile:" + n]["acc_tiehalf"] for n in bin_names], "0.6", "^", "-."),
              ("B2", [t["B2"]["pos_tercile:" + n]["acc_tiehalf"] for n in bin_names], "0.1", "x", ":")]
    for nm, v, col, mk, ls in series:
        ax[3].plot(range(3), v, color=col, marker=mk, ls=ls, label=nm)
    ax[3].set_xticks(range(3)); ax[3].set_xticklabels(["early", "middle", "late"], fontsize=8)
    ax[3].axhline(0.5, color="0.3", ls=":", lw=0.6)
    ax[3].set(xlabel="splice position tercile", ylabel="acc (tie-half)", ylim=(0, 1.05), title="(d) acc by splice position")
    ax[3].legend(fontsize=7, frameon=False)
    fig.suptitle("EXPLORATORY, post-hoc (not preregistered): splice-detector analysis, IntPhys dev, 180 pairs", fontsize=9)
    fig.tight_layout()
    (ROOT / "figures").mkdir(exist_ok=True)
    fig.savefig(ROOT / "figures/splice_EXPLORATORY_post-hoc.pdf")


if __name__ == "__main__":
    main()
