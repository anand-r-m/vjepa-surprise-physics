"""A3 dose-response for the M1 specificity (H2) types: low / mid / high (0.5x / 1x / 2x of the matched strength).

New script; calls the frozen H2 stage (scripts/run_analysis.py::h2_stage, unmodified) once per strength level, pooled over the
four types, and once per (type, level) cell by restricting the type tuple the stage loops over (module constant RA.SPEC_TYPES,
set temporarily in this process only). Everything else is the frozen pipeline: event-aligned max, own tau per score (2e-4 x median clean
score), tie-half, seed-mean AUROC A, B1/B2 baselines, scene-cluster bootstrap stratified by block, 10,000 draws, seed 20261015.

Holm convention (analogue of the H1 dose Holm-30 = 15 cells x 2 tests): 12 (type, level) cells x 2 contrasts (D_1 vs B1, D_2 vs B2)
= Holm over 24 one-sided bootstrap p-values (the frozen floor 1/(n_boot+1) applies). Also stored: Holm-6 over the pooled
(level x {D_1, D_2}) p-values. Holm-30 itself is not reproducible: this family has 12 cells, not 15.

  python scripts/run_dose_spec.py --runs <dir of run symlinks> --out results/analysis/h2/dose
"""
import argparse
import copy
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_analysis as RA                      # frozen driver (unmodified)
from vjepa_study.analysis import prereg as P

LEVELS = ("low", "mid", "high")
TYPES = ("lighting_global", "lighting_local", "jolt_base", "zoom_base")


def one(R, model, clean, matches, out, n_boot, var, level, types):
    """frozen h2_stage restricted to `types` at `level`; returns the result dict (also written under out/cells/)."""
    saved = RA.SPEC_TYPES
    RA.SPEC_TYPES = tuple(types)
    try:
        m = matches if len(types) == len(TYPES) else {**matches, "meta": {k: v for k, v in matches["meta"].items() if k != "mid_ratio_summary"}}
        r = RA.h2_stage(R, [model], {model: clean}, m, Path(out) / "cells" / ("pooled" if len(types) == len(TYPES) else types[0]) / level, n_boot, var, level=level)
    finally:
        RA.SPEC_TYPES = saved
    return r


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--matches", default="kaggle/h2_spec_a/matches.json")
    ap.add_argument("--out", default="results/analysis/h2/dose")
    ap.add_argument("--n-boot", type=int, default=10000)
    ap.add_argument("--variants", nargs="+", default=["tiehalf", "strict", "exactties"])
    a = ap.parse_args(argv)
    R, out = RA.Runs(a.runs), Path(a.out)
    RA.run_meta_check(R.root, ["M1"], out)
    clean = R.need(R.clean_id("M1"))
    matches = json.load(open(a.matches))
    for v in a.variants:
        tie_mode, ts = {"tiehalf": ("tiehalf", 1.0), "strict": ("strict", 1.0), "exactties": ("tiehalf", 0.0)}[v]
        var = RA.make_var("h2", "primary", None, tie_mode, ts)
        vout = out / v
        res = dict(variant=v, levels={}, cells={})
        for lv in LEVELS:
            r = one(R, "M1", clean, matches, vout, a.n_boot, var, lv, TYPES)
            res["levels"][lv] = dict(A=r["M1"]["A"], A_ci=r["M1"]["A_ci"], per_type=r["M1"]["per_type"], A0=r["M1"]["A0"],
                                     A_B1=r["B1"]["A"], A_B2=r["B2"]["A"], A_B3=r["B3"]["A"],
                                     D_B1=r["D_B1"], D_B2=r["D_B2"], outcome=r["outcome_M1"], foil=r["foil_accuracy_M1"],
                                     seed_auroc=r["M1"]["seed_auroc"], n_pairs_used=r["n_pairs_used"],
                                     target_feature_distance=r["target_feature_distance_median_by_type"])
            for t in TYPES:
                c = one(R, "M1", clean, matches, vout, a.n_boot, var, lv, (t,))
                res["cells"][f"{t}@{lv}"] = dict(A=c["M1"]["A"], A_ci=c["M1"]["A_ci"], A_B1=c["B1"]["A"], A_B2=c["B2"]["A"],
                                                 D_B1=c["D_B1"]["D"], D_B1_ci=c["D_B1"]["ci"], p_B1=c["D_B1"]["p"],
                                                 D_B2=c["D_B2"]["D"], D_B2_ci=c["D_B2"]["ci"], p_B2=c["D_B2"]["p"])
        names = list(res["cells"])
        pc = [res["cells"][k]["p_B1"] for k in names] + [res["cells"][k]["p_B2"] for k in names]
        h = P.holm(pc)
        for j, k in enumerate(names):
            res["cells"][k]["holm24_B1"], res["cells"][k]["holm24_B2"] = float(h[j]), float(h[len(names) + j])
        pl = [res["levels"][lv][d]["p"] for lv in LEVELS for d in ("D_B1", "D_B2")]
        h6 = P.holm(pl)
        for i, lv in enumerate(LEVELS):
            res["levels"][lv]["holm6_B1"], res["levels"][lv]["holm6_B2"] = float(h6[2 * i]), float(h6[2 * i + 1])
        res["monotone_A_with_strength"] = bool(res["levels"]["low"]["A"] <= res["levels"]["mid"]["A"] <= res["levels"]["high"]["A"])
        res["family"] = "12 (type, level) cells x 2 contrasts, Holm-24; pooled-level Holm-6"
        RA.wj(out, f"dose_spec_M1{'' if v == 'tiehalf' else '_' + v}.json", res)


if __name__ == "__main__":
    main()
