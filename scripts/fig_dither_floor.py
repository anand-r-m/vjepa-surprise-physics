"""EXPLORATORY, post-hoc: dither noise floor vs pairwise surprise margin (M1, fp16, IntPhys dev clean pairs).

Per clean pair i (180): margin m_i = S_imp - S_pos (per-video mean over windows of min-over-C surprise, the prereg H1
aggregation) on the fp16 clean run. Dither spread d_i = max over the 3 dither seeds of |m_i(dither,s) - m_i(clean)|
(RMS over seeds also stored). A verdict 'sits inside the noise floor' if |m_i| <= d_i. Flip = tie-half verdict change vs
clean (prereg H1 definition, tau = 2e-4 x median clean score), averaged over the 3 dither seeds.
Nothing here is confirmatory; no decision rule uses it.

  python scripts/fig_dither_floor.py --runs <run symlink dir> --out figures --numbers results/analysis/h1/dither_floor_EXPLORATORY.json
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_analysis as RA
from vjepa_study.analysis import prereg as P

OI = dict(blue="#0072B2", orange="#E69F00", vermillion="#D55E00", grey="#6b7280", green="#009E73")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--out", default="figures")
    ap.add_argument("--numbers", default="results/analysis/h1/dither_floor_EXPLORATORY.json")
    a = ap.parse_args(argv)
    R = RA.Runs(a.runs)
    c = R.need(R.clean_id("M1"))
    px = P.pair_index(c)
    sc = lambda d: P.video_scores(d, "S", "mean")
    tau = P.tau_m(sc(c))
    marg = lambda d: sc(d)[px["imp"]] - sc(d)[px["pos"]]
    m0 = marg(c)
    md = np.stack([marg(R.need(R.id("M1", "dither", "on", s))) for s in (1, 2, 3)])
    dev = np.abs(md - m0)
    spread_max, spread_rms = dev.max(0), np.sqrt((dev ** 2).mean(0))
    am = np.abs(m0)
    y0 = P.y_tiehalf(sc(c)[px["imp"]], sc(c)[px["pos"]], tau)
    yd = np.stack([P.y_tiehalf(sc(d)[P.pair_index(d)["imp"]], sc(d)[P.pair_index(d)["pos"]], tau)
                   for d in (R.need(R.id("M1", "dither", "on", s)) for s in (1, 2, 3))])
    flip = (yd != y0).mean(0)                                  # per-pair dither flip rate over 3 seeds
    sign_flip = (np.sign(md) != np.sign(m0)).any(0)
    inside = am <= spread_max
    correct = y0 == 1
    ratio = am / spread_max
    bins = [("inside floor (|m| <= d)", ratio <= 1), ("1 < |m|/d <= 3", (ratio > 1) & (ratio <= 3)), ("|m|/d > 3", ratio > 3)]
    tab = {n: dict(n=int(b.sum()), mean_flip_rate=float(flip[b].mean()) if b.any() else None,
                   n_pairs_any_flip=int((flip[b] > 0).sum()), n_sign_flip_any_seed=int(sign_flip[b].sum()),
                   n_clean_correct=int(correct[b].sum())) for n, b in bins}
    num = dict(label="EXPLORATORY, post-hoc", run_ids=dict(clean="P4_M1_ipdev_clean_s1", dither=[f"P4_M1_ipdev_dither-on_s{s}" for s in (1, 2, 3)]),
               precision="fp16", n_pairs=int(len(m0)), tau=tau,
               median_abs_margin=float(np.median(am)), median_spread_max=float(np.median(spread_max)), median_spread_rms=float(np.median(spread_rms)),
               n_inside_floor_max=int(inside.sum()), frac_inside_floor_max=float(inside.mean()),
               n_inside_floor_rms=int((am <= spread_rms).sum()),
               n_abs_margin_le_tau=int((am <= tau).sum()),
               n_pairs_any_dither_flip=int((flip > 0).sum()), mean_flip_rate_f0=float(flip.mean()),
               n_flip_pairs_inside_floor=int(((flip > 0) & inside).sum()), n_flip_pairs_outside_floor=int(((flip > 0) & ~inside).sum()),
               mean_flip_inside=float(flip[inside].mean()), mean_flip_outside=float(flip[~inside].mean()),
               n_sign_flip_any_seed=int(sign_flip.sum()), n_sign_flip_outside_floor=int((sign_flip & ~inside).sum()),
               by_ratio_bin=tab,
               clean_correct_inside=int((inside & correct).sum()), clean_wrong_inside=int((inside & (y0 == 0)).sum()),
               spearman_logabsmargin_vs_flip=float(__import__("scipy.stats", fromlist=["x"]).spearmanr(am, flip)[0]),
               definition="spread = max over 3 dither seeds of |margin_dither - margin_clean|; inside = |margin_clean| <= spread")
    Path(a.numbers).parent.mkdir(parents=True, exist_ok=True)
    Path(a.numbers).write_text(json.dumps(num, indent=1))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.alpha": .25, "figure.dpi": 150})
    fig, ax = plt.subplots(1, 2, figsize=(10, 4.2), gridspec_kw=dict(width_ratios=[1.35, 1]))
    eps = 1e-6
    x, y = np.maximum(am, eps), np.maximum(spread_max, eps)
    cols = np.where(flip == 0, OI["blue"], np.where(flip < 0.5, OI["orange"], OI["vermillion"]))
    ax[0].scatter(x[correct], y[correct], c=cols[correct], s=26, marker="o", edgecolor="white", linewidth=.4)
    ax[0].scatter(x[~correct], y[~correct], c=cols[~correct], s=34, marker="X", edgecolor="white", linewidth=.4)
    lim = [min(x.min(), y.min()) * .7, max(x.max(), y.max()) * 1.4]
    ax[0].plot(lim, lim, color=OI["grey"], lw=1)
    ax[0].fill_between(lim, lim, [lim[1]] * 2, color=OI["grey"], alpha=.08)
    ax[0].set_xscale("log"); ax[0].set_yscale("log"); ax[0].set_xlim(lim); ax[0].set_ylim(lim)
    ax[0].text(lim[0] * 1.2, lim[1] / 1.6, f"inside noise floor: {int(inside.sum())}/{len(am)} pairs", fontsize=9)
    ax[0].set_xlabel("clean margin |S_imp - S_pos|"); ax[0].set_ylabel("dither spread of the margin (max over 3 seeds)")
    from matplotlib.lines import Line2D
    ax[0].legend(handles=[Line2D([], [], marker="o", ls="", color=OI["blue"], label="no flip"), Line2D([], [], marker="o", ls="", color=OI["orange"], label="flip in 1 of 3 seeds"),
                          Line2D([], [], marker="o", ls="", color=OI["vermillion"], label="flip in >= 2 of 3 seeds"),
                          Line2D([], [], marker="X", ls="", color=OI["grey"], label="clean verdict wrong or tie"), Line2D([], [], marker="o", ls="", color=OI["grey"], label="clean verdict right")],
                 loc="lower right", fontsize=7.5, frameon=False)
    labs = ["inside\n(|m| <= d)", "1 < |m|/d <= 3", "|m|/d > 3"]
    vals = [tab[n]["mean_flip_rate"] * 100 if tab[n]["mean_flip_rate"] is not None else 0 for n, _ in bins]
    b = ax[1].bar(labs, vals, color=[OI["vermillion"], OI["orange"], OI["blue"]], width=.6)
    for r, (n, _) in zip(b, bins):
        ax[1].text(r.get_x() + r.get_width() / 2, r.get_height() + .8, f"n={tab[n]['n']}", ha="center", fontsize=8)
    ax[1].set_ylabel("mean dither flip rate (%)"); ax[1].set_xlabel("margin relative to dither spread")
    fig.suptitle("EXPLORATORY, post-hoc: verdict margin vs dither noise floor (M1, fp16, 180 IntPhys dev pairs)", fontsize=10, y=.995)
    fig.text(.01, .005, "EXPLORATORY, post-hoc; not part of any decision rule. Margin = clean S_imp - S_pos (mean aggregation). Spread = max over the 3 dither seeds of |margin_dither - margin_clean|.\n"
             "Flip = tie-half verdict change (tau = 2e-4 x median score). Source: results/analysis/h1/dither_floor_EXPLORATORY.json", fontsize=6.5, va="bottom")
    fig.tight_layout(rect=(0, .07, 1, .97))
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(out / f"dither_floor_EXPLORATORY_post-hoc.{ext}")
    return num


if __name__ == "__main__":
    main()
