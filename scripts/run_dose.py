"""A3 dose-response for M1 invariance edits (prereg sec 6: 'Low/mid strengths are dose-response A3, secondary').

New script; imports the frozen driver (scripts/run_analysis.py) and frozen statistics (vjepa_study.analysis.prereg)
unchanged. Same definitions as the H1 driver: tie-half y, tau = 2e-4 x median of the clean fp16 per-video mean score,
seed-averaged pair-level y/flip, dither floor f0 from the 3 dither seeds, scene-cluster bootstrap stratified by block
(seed 20261015, 10,000 draws), crop-retention exclusion (< 0.9 retained at the level's scale: 0.9/0.8/0.7).

Family: all 15 graded cells (brightness, noise, blur, jpeg, zoom x low/mid/high) through P.h1_family, i.e. Holm over
30 p-values (15 dAcc + 15 flip-vs-floor). Prereg text says 'Holm over all 21'; with only 5 graded edits that count is
not reproducible (7 edits x 3 levels would include hflip / fps_halve, which have a single strength), so a conservative
sensitivity is also written: the same 30 p-values Holm-adjusted among 42 slots (21 x 2, phantom p = 1).

  python scripts/run_dose.py --runs <dir of run symlinks> --out results/analysis/h1/dose
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_analysis as RA                      # frozen driver (unmodified)
from vjepa_study.analysis import prereg as P

GRADED = ("brightness", "noise", "blur", "jpeg", "zoom")
LEVELS = ("low", "mid", "high")
SCALE = {"low": "0.9", "mid": "0.8", "high": "0.7"}


def link_runs(raw, runs):
    runs.mkdir(parents=True, exist_ok=True)
    for d in sorted(Path(raw).glob("*/results/P4_*")):
        t = runs / d.name
        if not t.exists() and (d / "surprise.npz").exists():
            t.symlink_to(d.resolve())


def dose_stage(R, model, clean, var, out, n_boot, retention_all, elig_clean=None):
    tau, how = var.tau(clean), var.how
    cpy = lambda d: P.clean_pair_y(d, tau, how, tie=var.tie)[0]
    y0 = cpy(clean)
    px = P.pair_index(clean)
    fam, valid = {}, {}
    for e in GRADED:
        for lv in LEVELS:
            seeds = (1, 2, 3) if e in RA.SEEDED else (1,)
            ys = [cpy(R.need(R.id(model, e, lv, s))) for s in seeds]
            y, fl = P.h1_pair_level(ys, y0)
            fam[f"{e}@{lv}"] = dict(y=y, flip=fl)
            if e == "zoom":
                valid[f"{e}@{lv}"] = np.array([retention_all[p][SCALE[lv]] >= 0.9 for p in px["pair_ids"]])
    dith = [cpy(R.need(R.id(model, "dither", "on", s))) for s in (1, 2, 3)]
    f0p = P.seed_average([P.flip3(y, y0) for y in dith])
    r = P.h1_family(fam, y0, f0p, px["scene"], px["block"], n_boot=n_boot, valid=valid)
    # sensitivity: Holm over 42 slots (21 x 2) with phantom p = 1 for the 12 slots that do not exist
    names = list(fam)
    pc = [r["per_edit"][k]["p_dacc_cluster"] for k in names] + [r["per_edit"][k]["p_flip_cluster"] for k in names]
    h42 = P.holm(pc + [1.0] * 12)
    n = len(names)
    for j, k in enumerate(names):
        r["per_edit"][k]["holm42_dacc_cluster"], r["per_edit"][k]["holm42_flip_cluster"] = float(h42[j]), float(h42[n + j])
    # dose summaries: monotone non-increasing dAcc / non-decreasing flip over low -> mid -> high
    summ = {}
    for e in GRADED:
        c = [r["per_edit"][f"{e}@{lv}"] for lv in LEVELS]
        summ[e] = dict(dacc=[x["dacc"] for x in c], flip=[x["flip"] for x in c], excess=[x["excess"] for x in c],
                       n=[x["n"] for x in c], decision=[x["decision"] for x in c],
                       monotone_dacc=bool(c[0]["dacc"] >= c[1]["dacc"] >= c[2]["dacc"]),
                       monotone_flip=bool(c[0]["flip"] <= c[1]["flip"] <= c[2]["flip"]))
    r["dose_summary"] = summ
    r.update(aggregation=how, tie_value=var.tie, tau=tau, clean_acc_tiehalf_run=float(y0.mean()),
             family="15 graded cells, Holm over 30 p-values (secondary, A3)", n_holm_p=30)
    return RA.wj(out, f"dose_{model}{var.tag}.json", r)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="results/raw")
    ap.add_argument("--runs", required=True, help="dir of symlinks to run dirs (created from --raw if missing)")
    ap.add_argument("--retention-full", default="results/analysis/h1/retention_full.json")
    ap.add_argument("--out", default="results/analysis/h1/dose")
    ap.add_argument("--n-boot", type=int, default=10000)
    a = ap.parse_args(argv)
    runs, out = Path(a.runs), Path(a.out)
    link_runs(a.raw, runs)
    R = RA.Runs(runs)
    RA.run_meta_check(R.root, ["M1"], out)
    ret = json.load(open(a.retention_full))["all_scales"]
    clean = R.need(R.clean_id("M1"))
    for tie_mode, tau_scale in (("tiehalf", 1.0), ("strict", 1.0), ("tiehalf", 0.0)):
        dose_stage(R, "M1", clean, RA.h1_var("mean", None, tie_mode, tau_scale), out, a.n_boot, ret)


if __name__ == "__main__":
    main()
