"""EXPLORATORY (not pre-registered) analyses on the post-freeze groups, all through the frozen functions, nothing tuned.

  1. onset-aligned specificity (expl_onset_spec): frozen h2_stage with kaggle/expl_onset_spec/matches.json; spec-type edit runs are
     EXPL_M1_ipdev_onset-<type>-mid_s<seed>; clean / base_ref references are the frozen P4 runs. Tie counts + the lighting_global-excluded variant.
  2. halve_hold vs the clean skip-2 reference: paired dAcc and flip rate vs the dither floor f0 (frozen h1 functions).
  3. IntPhys 2 Main clean accuracy, M1 (descriptive, prereg s8): by block, with / without the 8 same-name Debug videos.

  python scripts/run_exploratory.py --runs <dir of run symlinks> --out results/analysis/exploratory
"""
import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_analysis as RA                      # frozen driver (unmodified)
from vjepa_study.analysis import prereg as P

VARIANTS = {"tiehalf": ("tiehalf", 1.0), "strict": ("strict", 1.0), "exactties": ("tiehalf", 0.0)}


class OnsetRuns(RA.Runs):
    """spec-type edit runs come from the EXPL onset group; everything else (clean, base_ref, dither, skip4) from the frozen P4 runs."""
    def id(self, model, edit, tag, seed=1):
        if edit in RA.SPEC_TYPES:
            return f"EXPL_{model}_ipdev_onset-{edit}-{tag}_s{seed}"
        return super().id(model, edit, tag, seed)


def onset_ties(R, clean, matches, var):
    px = P.pair_index(clean)
    t_on, late = RA.event_times(matches, px["pair_ids"])
    keep = ~late
    tvc = P._per_video_t(clean, px, t_on)
    out = {"n_pairs": int(keep.sum()), "clean_dv_tie": {}, "abrupt_tie": {}, "auroc_cmp_in_band": {}}
    for name, key in (("M1", "S"), ("B1", "B1"), ("B2", "B2"), ("B3", "B3")):
        tau = var.tau(clean, key)
        s = P.video_scores(clean, key, var.how, tvc, None)
        dv = (s[px["imp"]] - s[px["pos"]])[keep]
        out["clean_dv_tie"][name] = dict(tau=tau, n_tie=int((np.abs(dv) <= tau).sum()), n_exact_zero=int((dv == 0).sum()))
    tau = var.tau(clean, "S")
    s_clean = P.video_scores(clean, "S", var.how, tvc, None)
    s_pos = s_clean[px["pos"]]
    dv = (s_clean[px["imp"]] - s_pos)[keep]
    for t in RA.SPEC_TYPES:
        seeds = (1, 2, 3) if t in RA.SEEDED else (1,)
        out["abrupt_tie"][t], out["auroc_cmp_in_band"][t] = [], []
        for sd in seeds:
            de = R.need(R.id("M1", t, "mid", sd))
            pe = P.pair_index(de)
            tv = P._per_video_t(de, pe, t_on)
            se = P.video_scores(de, "S", var.how, tv, None)[pe["pos"]]
            if t in ("jolt_base", "zoom_base"):
                dr = R.need(R.id("M1", "base_ref", "ref", 1))
                pr = P.pair_index(dr)
                sr = P.video_scores(dr, "S", var.how, P._per_video_t(dr, pr, t_on), None)[pr["pos"]]
            else:
                sr = s_pos
            da = (se - sr)[keep]
            out["abrupt_tie"][t].append(int((np.abs(da) <= tau).sum()))
            out["auroc_cmp_in_band"][t].append(float((np.abs(dv[:, None] - da[None, :]) <= tau).mean()))
    return out


def onset(R, out, n_boot):
    matches = json.load(open("kaggle/expl_onset_spec/matches.json"))
    R = OnsetRuns(R.root)
    RA.run_meta_check(R.root, ["M1"], out / "onset_spec")
    clean = R.need(R.clean_id("M1"))
    for v, (tm, ts) in VARIANTS.items():
        var = RA.make_var("h2", "primary", None, tm, ts)
        sub = out / "onset_spec" / ("" if v == "tiehalf" else v)
        r = RA.h2_stage(R, ["M1"], {"M1": clean}, matches, sub, n_boot, var)
        (sub / f"h2{var.tag}.json").rename(sub / f"EXPLORATORY_h2_onset_M1{var.tag}.json")
        RA.wj(sub, f"EXPLORATORY_onset_ties{var.tag}.json", onset_ties(R, clean, matches, var))
    return matches


def halve_hold(R, out, n_boot):
    clean = R.need(R.clean_id("M1"))
    hh = R.need("EXPL_M1_ipdev_halve_hold-high_s1")
    px = P.pair_index(clean)
    for v, (tm, ts) in VARIANTS.items():
        var = RA.h1_var("mean", None, tm, ts)
        tau = var.tau(clean)
        cpy = lambda d: P.clean_pair_y(d, tau, var.how, tie=var.tie)[0]
        y0, yh = cpy(clean), cpy(hh)
        dith = [cpy(R.need(R.id("M1", "dither", "on", s))) for s in (1, 2, 3)]
        f0p = P.seed_average([P.flip3(y, y0) for y in dith])
        y, fl = P.h1_pair_level([yh], y0)
        r = P.h1_family({"halve_hold": dict(y=y, flip=fl)}, y0, f0p, px["scene"], px["block"], n_boot=n_boot)
        sh, sc = P.video_scores(hh, "S", var.how), P.video_scores(clean, "S", var.how)
        ih, ic = P.pair_index(hh), px
        r["EXPLORATORY"] = dict(
            reference="P4_M1_ipdev_clean_s1 (clean skip-2)", run="EXPL_M1_ipdev_halve_hold-high_s1", tau=tau, tie_value=var.tie,
            f0=float(np.mean(f0p)), clean_acc=float(y0.mean()), halve_hold_acc=float(yh.mean()),
            n_flipped_pairs_of_180=float(fl.sum()),
            ties_halve_hold=int((np.abs(sh[ih["imp"]] - sh[ih["pos"]]) <= tau).sum()),
            ties_clean=int((np.abs(sc[ic["imp"]] - sc[ic["pos"]]) <= tau).sum()),
            ties_dither=[int((np.abs(d_ - 0.5) < 1e-9).sum()) for d_ in dith],
            S_identical_to_clean=bool(np.array_equal(hh["S"], clean["S"])),
            max_abs_S_diff=float(np.nanmax(np.abs(hh["S"] - clean["S"]))),
            note="family of one: the Holm fields in this file are Holm over 2 p-values (dacc, flip); not a pre-registered family")
        RA.wj(out / "halve_hold", f"EXPLORATORY_halve_hold_M1{var.tag}.json", r)


def ip2main(R, out, n_boot):
    d = R.need("P4_M1_ip2main_clean_s1")
    names = np.asarray(d["video_ids"])
    dbg = {r["name"] for r in csv.DictReader(open("data/intphys2/extracted/Debug/metadata.csv"))}
    overlap = np.array([n in dbg for n in names])
    px = P.pair_index(d)
    ok_pair = ~(overlap[px["pos"]] | overlap[px["imp"]])
    res = dict(n_videos=int(len(names)), n_pairs=int(len(px["pos"])), n_overlap_videos=int(overlap.sum()),
               n_pairs_with_overlap=int((~ok_pair).sum()), tau_from="full Main clean run (2e-4 x median per-video score of this aggregation)")
    rng_idx = lambda sc, bl: P.stratified_cluster_indices(sc, bl, np.random.default_rng(P.BOOT_SEED))
    for key in ("S", "B1", "B2", "B3"):
        for how in ("mean", "max"):
            tau = P.tau_m(P.video_scores(d, key, how))
            y, ys, _ = P.clean_pair_y(d, tau, how, key=key)
            ex = {}
            for lab, m in (("all", np.ones(len(y), bool)), ("without_debug_overlap", ok_pair)):
                blocks = {str(b): dict(n=int((m & (px["block"] == b)).sum()), acc_tiehalf=float(y[m & (px["block"] == b)].mean()),
                                       acc_strict=float(ys[m & (px["block"] == b)].mean()), n_ties=int((y[m & (px["block"] == b)] == 0.5).sum()))
                          for b in np.unique(px["block"])}
                rng = np.random.default_rng(P.BOOT_SEED)
                sc, bl, yy = px["scene"][m], px["block"][m], y[m]
                bs = [yy[P.stratified_cluster_indices(sc, bl, rng)].mean() for _ in range(n_boot)]
                ex[lab] = dict(n=int(m.sum()), acc_tiehalf=float(yy.mean()), acc_strict=float(ys[m].mean()), n_ties=int((yy == 0.5).sum()),
                               wilson95=P.wilson(float(yy.sum()), len(yy)), cluster_boot95=np.percentile(bs, [2.5, 97.5]).tolist(), per_block=blocks)
            res.setdefault(key, {})[how] = dict(tau=tau, **ex)
    RA.wj(out / "ip2main", "IP2MAIN_M1_clean_descriptive.json", res)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--out", default="results/analysis/exploratory")
    ap.add_argument("--n-boot", type=int, default=10000)
    ap.add_argument("--only", nargs="+", default=["onset", "halve", "ip2main"])
    a = ap.parse_args(argv)
    R, out = RA.Runs(a.runs), Path(a.out)
    if "onset" in a.only:
        onset(R, out, a.n_boot)
    if "halve" in a.only:
        halve_hold(R, out, a.n_boot)
    if "ip2main" in a.only:
        ip2main(R, out, a.n_boot)


if __name__ == "__main__":
    main()
