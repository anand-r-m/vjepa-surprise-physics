"""M2 dose-response (A3 analogue, DESCRIPTIVE: M2 is H1-ineligible, clean 60.8%), H1 invariance cells and H2 specificity cells.

New script; imports the frozen driver (scripts/run_analysis.py) and frozen statistics (vjepa_study.analysis.prereg) unchanged,
plus scripts/run_dose_spec.py::one for the per-cell H2 stage. Definitions identical to scripts/run_dose.py / run_dose_spec.py
(tie-half y, own tau = 2e-4 x median clean score, seed-averaged pair-level quantities, scene-cluster bootstrap stratified by
block, 10,000 draws, seed 20261015, crop-retention exclusion for zoom at the level's scale), with the model set to M2 and
the M2 clean reference mask_index 0 (RA.Runs.clean_id).

Cells that exist for M2 (all seed 1 only at low/mid):
  H1: brightness, noise, blur x low/mid/high (9 cells) + jpeg-high + zoom-high (2 cells) = 11 cells -> Holm over 22 p-values
      (11 dAcc + 11 flip-vs-floor). Dither floor f0 from the 3 high-strength-run dither seeds (m2_h1_inv_b).
      variant 's1'   : every cell uses seed 1 only (matched across levels; primary dose reading)
      variant 'asrun': high brightness/noise use their seeds 1-3 (as in h1_M2.json); low/mid seed 1
  H2: lighting_global, lighting_local, jolt_base, zoom_base x low/mid/high = 12 cells x 2 contrasts -> Holm-24 (as M1);
      seed 1 only for every level (mid also has seeds 1-3 in h2.json; RA.SEEDED is emptied inside this process only so the
      frozen h2_stage loads seed 1 only).

  python scripts/run_dose_m2.py --runs <run symlink dir> --out results/analysis/m2/dose
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_analysis as RA                      # frozen driver (unmodified)
import run_dose as RD
import run_dose_spec as RS
from vjepa_study.analysis import prereg as P

H1_CELLS = [(e, lv) for e in ("brightness", "noise", "blur") for lv in RD.LEVELS] + [("jpeg", "high"), ("zoom", "high")]


def h1_dose(R, clean, var, out, n_boot, ret, mode):
    tau, how = var.tau(clean), var.how
    cpy = lambda d: P.clean_pair_y(d, tau, how, tie=var.tie)[0]
    y0 = cpy(clean)
    px = P.pair_index(clean)
    fam, valid = {}, {}
    for e, lv in H1_CELLS:
        seeds = (1, 2, 3) if (mode == "asrun" and lv == "high" and e in ("brightness", "noise")) else (1,)
        y, fl = P.h1_pair_level([cpy(R.need(R.id("M2", e, lv, s))) for s in seeds], y0)
        fam[f"{e}@{lv}"] = dict(y=y, flip=fl)
        if e == "zoom":
            valid[f"{e}@{lv}"] = np.array([ret[p][RD.SCALE[lv]] >= 0.9 for p in px["pair_ids"]])
    dith = [cpy(R.need(R.id("M2", "dither", "on", s))) for s in (1, 2, 3)]
    f0p = P.seed_average([P.flip3(y, y0) for y in dith])
    r = P.h1_family(fam, y0, f0p, px["scene"], px["block"], n_boot=n_boot, valid=valid)
    summ = {}
    for e in ("brightness", "noise", "blur"):
        c = [r["per_edit"][f"{e}@{lv}"] for lv in RD.LEVELS]
        summ[e] = dict(dacc=[x["dacc"] for x in c], flip=[x["flip"] for x in c], excess=[x["excess"] for x in c],
                       decision=[x["decision"] for x in c],
                       monotone_dacc=bool(c[0]["dacc"] >= c[1]["dacc"] >= c[2]["dacc"]),
                       monotone_flip=bool(c[0]["flip"] <= c[1]["flip"] <= c[2]["flip"]))
    r["dose_summary"] = summ
    r.update(aggregation=how, tie_value=var.tie, tau=tau, clean_acc_tiehalf_run=float(y0.mean()), seed_mode=mode,
             family="11 existing M2 cells, Holm over 22 p-values (11 dAcc + 11 flip-vs-floor); descriptive (M2 H1-ineligible)",
             n_holm_p=22, missing_cells=[f"{e}@{lv}" for e in ("jpeg", "zoom") for lv in ("low", "mid")])
    return RA.wj(out, f"dose_M2{var.tag}_{mode}.json", r)


def spec_dose(R, clean, matches, out, n_boot, v):
    tie_mode, ts = {"tiehalf": ("tiehalf", 1.0), "strict": ("strict", 1.0), "exactties": ("tiehalf", 0.0)}[v]
    var = RA.make_var("h2", "primary", None, tie_mode, ts)
    vout = Path(out) / "spec" / v
    res = dict(variant=v, levels={}, cells={})
    saved = RA.SEEDED
    RA.SEEDED = set()                      # seed 1 only for every type and level (low/high exist for seed 1 only)
    try:
        for lv in RS.LEVELS:
            r = RS.one(R, "M2", clean, matches, vout, n_boot, var, lv, RS.TYPES)
            res["levels"][lv] = dict(A=r["M2"]["A"], A_ci=r["M2"]["A_ci"], per_type=r["M2"]["per_type"], A0=r["M2"]["A0"],
                                     A_B1=r["B1"]["A"], A_B2=r["B2"]["A"], A_B3=r["B3"]["A"], D_B1=r["D_B1"], D_B2=r["D_B2"],
                                     outcome=r["outcome_M2"], foil=r["foil_accuracy_M2"], seed_auroc=r["M2"]["seed_auroc"],
                                     n_pairs_used=r["n_pairs_used"], target_feature_distance=r["target_feature_distance_median_by_type"])
            for t in RS.TYPES:
                c = RS.one(R, "M2", clean, matches, vout, n_boot, var, lv, (t,))
                res["cells"][f"{t}@{lv}"] = dict(A=c["M2"]["A"], A_ci=c["M2"]["A_ci"], A_B1=c["B1"]["A"], A_B2=c["B2"]["A"],
                                                 D_B1=c["D_B1"]["D"], D_B1_ci=c["D_B1"]["ci"], p_B1=c["D_B1"]["p"],
                                                 D_B2=c["D_B2"]["D"], D_B2_ci=c["D_B2"]["ci"], p_B2=c["D_B2"]["p"])
    finally:
        RA.SEEDED = saved
    names = list(res["cells"])
    h = P.holm([res["cells"][k]["p_B1"] for k in names] + [res["cells"][k]["p_B2"] for k in names])
    for j, k in enumerate(names):
        res["cells"][k]["holm24_B1"], res["cells"][k]["holm24_B2"] = float(h[j]), float(h[len(names) + j])
    h6 = P.holm([res["levels"][lv][d]["p"] for lv in RS.LEVELS for d in ("D_B1", "D_B2")])
    for i, lv in enumerate(RS.LEVELS):
        res["levels"][lv]["holm6_B1"], res["levels"][lv]["holm6_B2"] = float(h6[2 * i]), float(h6[2 * i + 1])
    A = [res["levels"][lv]["A"] for lv in RS.LEVELS]
    res["monotone_A_decreasing_with_strength"] = bool(A[0] >= A[1] >= A[2])
    res["family"] = "12 (type, level) cells x 2 contrasts, Holm-24; pooled-level Holm-6; seed 1 only"
    return RA.wj(out, f"dose_spec_M2{'' if v == 'tiehalf' else '_' + v}.json", res)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="results/raw")
    ap.add_argument("--runs", required=True)
    ap.add_argument("--retention-full", default="results/analysis/h1/retention_full.json")
    ap.add_argument("--matches", default="kaggle/h2_spec_a/matches.json")
    ap.add_argument("--out", default="results/analysis/m2/dose")
    ap.add_argument("--n-boot", type=int, default=10000)
    a = ap.parse_args(argv)
    out = Path(a.out)
    RD.link_runs(a.raw, Path(a.runs))
    R = RA.Runs(a.runs)
    RA.run_meta_check(R.root, ["M2"], out)
    ret = json.load(open(a.retention_full))["all_scales"]
    matches = json.load(open(a.matches))
    clean = R.need(R.clean_id("M2"))
    for tie_mode, ts in (("tiehalf", 1.0), ("strict", 1.0), ("tiehalf", 0.0)):
        for mode in ("s1", "asrun"):
            h1_dose(R, clean, RA.h1_var("mean", None, tie_mode, ts), out, a.n_boot, ret, mode)
    for v in ("tiehalf", "strict", "exactties"):
        spec_dose(R, clean, matches, out, a.n_boot, v)


if __name__ == "__main__":
    main()
