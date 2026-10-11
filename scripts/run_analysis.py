"""Run the pre-registered analysis (docs/PREREGISTRATION.md sec 2, 6, 7) from results/runs/<run_id>/.

  python scripts/run_analysis.py --runs results/runs --out results/analysis --matches matches.json \
         --models M1 M2 --stages clean h1 h2 h3 [--n-boot 10000]

Run ids follow PROJECT_SPEC: P4_<model>_ipdev_<edit>-<tag>_s<seed> (kaggle/make_p4_runs.py). Stages that need
edited-dev runs must NOT be run before the freeze (MJ9); `clean` only needs the clean runs. Every output is JSON.
"""
import argparse
import json
from pathlib import Path

import numpy as np

from vjepa_study import schema
from vjepa_study.analysis import prereg as P

SPEC_TYPES = ("lighting_global", "lighting_local", "jolt_base", "zoom_base")
SEEDED = {"brightness", "noise", "dither", "lighting_global", "lighting_local", "jolt_base"}
H1_EDITS = ("brightness", "noise", "blur", "jpeg", "zoom", "hflip", "fps_halve")
BASELINES = ("B1", "B2", "B3")
C_INDEX = {2: 0, 6: 2, 10: 4}                     # A2: fixed context length -> column of S[w, C]
VARIANTS = {"primary": None, "A1_full_max": dict(how="max", event=False), "A1_mean": dict(how="mean", event=False)}


class Var:
    """H2/H3 analysis variant: aggregation (how), event alignment (H2 only), fixed C (A2), tie handling."""
    def __init__(self, how, event, c_index=None, tie=0.5, tau_scale=1.0, tag=""):
        self.how, self.event, self.c_index, self.tie, self.tau_scale, self.tag = how, event, c_index, tie, tau_scale, tag

    def tau(self, d, key="S"):
        """tau for the score being compared: 2e-4 x median per-video score of this aggregation (and C) on the clean run."""
        return self.tau_scale * P.tau_m(P.video_scores(d, key, self.how, None, self.c_index))


def make_var(stage, agg="primary", c=None, tie_mode="tiehalf", tau_scale=1.0):
    """stage 'h2' (primary: event-aligned max) or 'h3' (primary: full-clip max). agg in primary|A1_full_max|A1_mean."""
    if agg == "primary":
        how, event = "max", stage == "h2"
    else:
        how, event = VARIANTS[agg]["how"], False
    strict = tie_mode == "strict"
    tag = ("" if agg == "primary" else "_" + agg) + ("" if c is None else f"_A2_C{c}") + ("_strict" if strict else "") \
        + ("_exactties" if (tau_scale == 0 and not strict) else "")
    return Var(how, event, None if c is None else C_INDEX[c], 0.0 if strict else 0.5, 0.0 if strict else tau_scale, tag)


M2_CLEAN_TAG = "mi0"
# Old M2 clean run (mask_index 1, untrained query token, documented wrapper deviation): reported separately, never part of an M2 contrast.
EXCLUDED_RUNS = ("P4_M2_ipdev_clean_s1",)


class Runs:
    def __init__(self, root, phase="P4"):
        self.root, self.phase = Path(root), phase

    def id(self, model, edit, tag, seed=1):
        return f"{self.phase}_{model}_ipdev_{edit}-{tag}_s{seed}"

    def clean_id(self, model, tag=None):
        if model == "M2" and tag is None:
            tag = M2_CLEAN_TAG      # Q10 B: the corrected (mask_index 0) M2 clean run is the M2 reference; the old run is excluded
        return f"{self.phase}_{model}_ipdev_clean{'-' + tag if tag else ''}_s1"

    def load(self, rid):
        f = self.root / rid / "surprise.npz"
        return schema.load_surprise(f) if f.exists() else None

    def need(self, rid):
        d = self.load(rid)
        if d is None:
            raise FileNotFoundError(f"missing run {rid} under {self.root}")
        return d


def wj(out, name, obj):
    out.mkdir(parents=True, exist_ok=True)
    (out / name).write_text(json.dumps(obj, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
    return obj


# ------------------------------------------------------------------ clean (G1-type, tau_m, T1)
def score_keys(d):
    return ("S",) + tuple(k for k in BASELINES if k in d)


def clean_stage(R, models, out, extra=None):
    res = dict(models={}, tau={})
    clean = {}
    for m in models:
        d = R.need(R.clean_id(m))
        clean[m] = d
        info = {}
        for key in score_keys(d):
            name = m if key == "S" else f"{key}({m})"
            sc_mean = P.video_scores(d, key, "mean")
            tau = P.tau_m(sc_mean)
            tau_max = P.tau_m(P.video_scores(d, key, "max"))
            res["tau"][name] = dict(tau=tau, tau_mean=tau, tau_max=tau_max, median_score=float(np.median(sc_mean)))
            rec = {"finite": bool(np.isfinite(d[key][~np.isnan(d[key])]).all())}
            for how in ("mean", "max"):
                y, ys, px = P.clean_pair_y(d, tau if how == "mean" else tau_max, how, key=key)
                rec[how] = dict(tau_used=tau if how == "mean" else tau_max, acc_tiehalf=float(y.mean()), acc_strict=float(ys.mean()), n_pairs=len(y),
                                n_ties=int((y == 0.5).sum()),
                                per_block={str(b): dict(acc_tiehalf=float(y[px["block"] == b].mean()),
                                                        acc_strict=float(ys[px["block"] == b].mean()),
                                                        n_ties=int((y[px["block"] == b] == 0.5).sum()))
                                           for b in np.unique(px["block"])},
                                wilson95_tiehalf=P.wilson(float(y.sum()), len(y)))
            if key == "S":      # A2: fixed C in {2,6,10} (indices 0,2,4) vs min over C, from stored S[w,C]; mean aggregation
                rec["A2_fixed_C_mean_agg"] = {}
                for ci, cl in ((0, 2), (2, 6), (4, 10)):
                    sc_c = P.video_scores(d, key, "mean", c_index=ci)
                    tc = P.tau_m(sc_c)
                    pxx = P.pair_index(d)
                    yc = P.y_tiehalf(sc_c[pxx["imp"]], sc_c[pxx["pos"]], tc)
                    rec["A2_fixed_C_mean_agg"][str(cl)] = dict(acc_tiehalf=float(yc.mean()), tau=tc)
            info[name] = rec
        res["models"].update(info)
    res["T1_M1_minus_B2_paired_clean_mean"] = None
    if "M1" in clean and "B2" in clean["M1"]:
        d = clean["M1"]
        tm, tb = res["tau"]["M1"]["tau"], res["tau"]["B2(M1)"]["tau"]
        y1, _, px = P.clean_pair_y(d, tm, "mean")
        y2, _, _ = P.clean_pair_y(d, tb, "mean", key="B2")
        res["T1_M1_minus_B2_paired_clean_mean"] = P.paired_difference(y1, y2, px["scene"], px["block"], n_boot=extra or 2000)
    return wj(out, "clean.json", res), clean, res["tau"]


# ------------------------------------------------------------------ H1
def h1_var(agg="mean", c=None, tie_mode="tiehalf", tau_scale=1.0):
    strict = tie_mode == "strict"
    tag = ("" if agg == "mean" else f"_A1_{agg}") + ("" if c is None else f"_A2_C{c}") + ("_strict" if strict else "") \
        + ("_exactties" if (tau_scale == 0 and not strict) else "")
    return Var(agg, False, None if c is None else C_INDEX[c], 0.0 if strict else 0.5, 0.0 if strict else tau_scale, tag)


def h1_stage(R, model, clean, var, out, n_boot, retention=None, elig_clean=None):
    dc = clean
    tau, how, ci, tie = var.tau(dc), var.how, var.c_index, var.tie
    cpy = lambda d: P.clean_pair_y(d, tau, how, tie=tie)[0] if ci is None else \
        P.y_tiehalf(*[P.video_scores(d, "S", how, None, ci)[P.pair_index(d)[k]] for k in ("imp", "pos")], tau, tie)
    y0 = cpy(dc)
    px = P.pair_index(dc)
    seeds = (1, 2, 3)
    edits = {}
    for e in H1_EDITS:
        ids = [R.id(model, e, "high", s) for s in (seeds if e in SEEDED else (1,))]
        if e == "fps_halve":
            y_ref = cpy(R.need(R.clean_id(model, "skip4")))
            ys = [cpy(R.need(i)) for i in ids]
            y, fl = P.h1_pair_level(ys, y_ref)
            edits[e] = dict(y=y, flip=fl, y_ref=y_ref)
        else:
            ys = [cpy(R.need(i)) for i in ids]
            y, fl = P.h1_pair_level(ys, y0)
            edits[e] = dict(y=y, flip=fl, y_ref=y0)
    dith = [cpy(R.need(R.id(model, "dither", "on", s))) for s in seeds]
    f0p = P.seed_average([P.flip3(y, y0) for y in dith])
    valid = None
    if retention:
        valid = {e: np.array([retention[e].get(p, 1.0) >= 0.9 for p in px["pair_ids"]]) for e in retention}
    # edits whose reference differs from y0 (halving) are compared against their own reference
    fam_in = {k: dict(y=v["y"] - v["y_ref"] + y0 if k == "fps_halve" else v["y"], flip=v["flip"]) for k, v in edits.items()}
    r = P.h1_family(fam_in, y0, f0p, px["scene"], px["block"], n_boot=n_boot, valid=valid)
    r["aggregation"], r["tie_value"], r["c_index"], r["tau"] = how, tie, ci, tau
    r["clean_acc_tiehalf_run"] = float(y0.mean())
    elig = float(elig_clean) if elig_clean is not None else float(y0.mean())     # M1: P2 fp32 run (prereg sec 6)
    r["eligibility_clean_acc_tiehalf"] = elig
    r["status"] = P.h1_model_status(r["f0"], elig)
    return wj(out, f"h1_{model}{var.tag}.json", r)


# ------------------------------------------------------------------ H2
def event_times(matches, pair_ids):
    ev = [matches["pairs"][p]["event"] for p in pair_ids]
    return np.array([e["t_on"] for e in ev], float), np.array([bool(e.get("excluded_late", False)) for e in ev])


def h2_stage(R, models, clean_by_model, matches, out, n_boot, var, level="mid"):
    px = P.pair_index(clean_by_model[models[0]])
    t_on, late = event_times(matches, px["pair_ids"])
    keep = ~late
    how, ci, tie = var.how, var.c_index, var.tie
    tv_of = (lambda d, p: P._per_video_t(d, p, t_on)) if var.event else (lambda d, p: None)
    names = {}
    for m in models:
        names[m] = (m, "S")
        for b in BASELINES:
            if b in clean_by_model[m] and m == models[0]:
                names[b] = (m, b)

    mod, foil = {}, {}
    for name, (m, key) in names.items():
        dc = clean_by_model[m]
        tau = var.tau(dc, key)                                    # its own tau, same aggregation / C as the compared score
        vs = lambda d, p: P.video_scores(d, key, how, tv_of(d, p), ci)
        s_clean = vs(dc, px)
        s_pos, s_imp = s_clean[px["pos"]], s_clean[px["imp"]]
        dv = s_imp - s_pos
        y0 = P.y_tiehalf(s_imp, s_pos, tau, tie)
        da, s_ref_by_type = {}, {}
        for t in SPEC_TYPES:
            seeds = (1, 2, 3) if t in SEEDED else (1,)
            rows = []
            for s in seeds:
                de = R.need(R.id(m, t, level, s))
                pe = P.pair_index(de)
                se = vs(de, pe)[pe["pos"]]
                if t in ("jolt_base", "zoom_base"):
                    dr = R.need(R.id(m, "base_ref", "ref", 1))
                    pr = P.pair_index(dr)
                    sr = vs(dr, pr)[pr["pos"]]
                else:
                    sr = s_pos
                rows.append(se - sr)
            da[t] = np.stack(rows)
            s_ref_by_type[t] = sr
        mod[name] = dict(dv=dv[keep], da={t: v[:, keep] for t, v in da.items()}, tau=tau, tie=tie, y0=y0[keep])
        # foil accuracy: S(v_i) vs S(edit_k(p_i)) = dv_i + s_pos_i vs da + s_ref ; computed from raw scores
        foil[name] = P.foil_acc(s_imp[keep], {t: (da[t] + s_ref_by_type[t])[:, keep] for t in da}, tau, tie)
    res = P.h2_bootstrap(mod, px["scene"][keep], px["block"][keep], refs=("B1", "B2"), main=models[0], n_boot=n_boot)
    res["variant"] = dict(how=how, event_aligned=var.event, c_index=ci, tie_value=tie, tau_scale=var.tau_scale)
    res["n_pairs_used"], res["n_excluded_late"] = int(keep.sum()), int(late.sum())
    pm = [matches["pairs"][p] for p in px["pair_ids"][keep]]
    res["strata_block_descriptive"] = P.h2_strata(mod, px["block"][keep])
    if all("onset_abrupt" in x for x in pm):
        res["strata_onset_proxy_descriptive"] = P.h2_strata(mod, [("abrupt" if x["onset_abrupt"] else "gradual/occluded") for x in pm])
        res["descriptors"] = dict(median_onset_diff=float(np.median([x["onset_diff"] for x in pm])),
                                  median_affected_area_fraction=float(np.median([x["affected_area_fraction"] for x in pm])),
                                  n_transient=int(sum(x["event"].get("transient", False) for x in pm)))
    fd = {}
    for t in SPEC_TYPES:
        de = R.load(R.id(models[0], t, level, 1))
        if de is not None and "target_feats" in de:
            ref = R.load(R.id(models[0], "base_ref", "ref", 1)) if t in ("jolt_base", "zoom_base") else clean_by_model[models[0]]
            if ref is not None and "target_feats" in ref:
                pe, pr = P.pair_index(de), P.pair_index(ref)
                fd[t] = float(np.median([P.feature_distance(de["target_feats"][i], ref["target_feats"][j])
                                         for i, j in zip(pe["pos"][keep], pr["pos"][keep])]))
    res["target_feature_distance_median_by_type"] = fd
    p_adj = [res[f"D_{b}"]["p_holm"] for b in ("B1", "B2") if f"D_{b}" in res]
    mm = models[0]
    res["outcome_" + mm] = P.h2_outcome(res[mm]["A"], p_adj, res[mm]["per_type"], A0=res[mm]["A0"])
    res["foil_accuracy_" + mm] = foil[mm]
    # matching diagnostics: types missing the achieved-ratio target stay in A (flagged); A without them is a sensitivity
    summ = (matches.get("meta") or {}).get("mid_ratio_summary")
    missed = P.match_missed(summ) if summ else []
    res["match_target_missed"] = missed
    res["match_target_missed_available"] = summ is not None
    if missed and len(missed) < len(SPEC_TYPES):
        sub = P.h2_bootstrap(P.restrict_types(mod, missed), px["scene"][keep], px["block"][keep], refs=("B1", "B2"), main=mm, n_boot=n_boot)
        sens = dict(dropped_types=missed, A=sub[mm]["A"], A_ci=sub[mm]["A_ci"], per_type=sub[mm]["per_type"])
        for b in ("B1", "B2"):
            if f"D_{b}" in sub:
                sens[f"D_{b}"] = sub[f"D_{b}"]
        sens["outcome"] = P.h2_outcome(sub[mm]["A"], [sub[f"D_{b}"]["p_holm"] for b in ("B1", "B2") if f"D_{b}" in sub],
                                       sub[mm]["per_type"], A0=sub[mm]["A0"])
        res["sensitivity_exclude_missed_types"] = sens
    return wj(out, f"h2{var.tag}.json", res)


# ------------------------------------------------------------------ H3 / G2
def h3_stage(R, model, clean, clean_m0, out, n_boot, var):
    px = P.pair_index(clean)
    pos = px["pos"]
    how, ci, tie = var.how, var.c_index, var.tie
    tau, tau_m0 = var.tau(clean), var.tau(clean_m0)
    ctrl = lambda e, m=model: R.need(R.id(m, e, "high", 1))
    sc = lambda d: P.video_scores(d, "S", how, None, ci)[P.pair_index(d)["pos"]]
    s0 = P.video_scores(clean, "S", how, None, ci)[pos]
    vf, hf = sc(ctrl("vflip")), sc(ctrl("hflip"))
    det_a, det_b = P.detection(vf, s0, tau, tie), P.detection(vf, hf, tau, tie)
    m0 = R.need(R.id("M0r", "vflip", "high", 1))
    s0m = P.video_scores(clean_m0, "S", how, None, ci)[P.pair_index(clean_m0)["pos"]]
    det_m0 = P.detection(sc(m0), s0m, tau_m0, tie)
    res = P.h3_analysis(det_a, det_b, det_m0, px["scene"], px["block"], n_boot=n_boot)
    res["variant"] = dict(how=how, c_index=ci, tie_value=tie, tau_scale=var.tau_scale, tau=tau)
    rev = sc(ctrl("time_reversal"))
    res["reversal_detection"] = float(P.detection(rev, s0, tau, tie).mean())
    res["reversal_below_half_diagnostic_needed"] = bool(res["reversal_detection"] < 0.5)
    # free secondary: pairwise accuracy on flipped / reversed pairs (mean aggregation, own tau)
    for e in ("vflip", "time_reversal"):
        d = ctrl(e)
        tm = P.tau_m(P.video_scores(clean, "S", "mean")) * var.tau_scale
        y, ys, _ = P.clean_pair_y(d, tm, "mean", tie=tie)
        res[f"pairwise_acc_{e}"] = dict(tiehalf=float(y.mean()), strict=float(ys.mean()))
    return wj(out, f"h3_{model}{var.tag}.json", res)


# ------------------------------------------------------------------ run meta consistency (prereg sec 1)
# Pre-registered repo_head allowlist (prereg sec 1): heads whose kernel bundles are logged in DECISIONS as equivalent
# for the contrasts (differences confined to the exempted files). Not bundled into kernels, so the final build
# head can be appended after the build. Any other head, and any precision / n_gpus mismatch, aborts.
REPO_HEAD_ALLOWLIST = (
    "606d7324dd814c1ec21077b8091fbd7b2dc866b7",   # clean M1 / M2 bundles (M2 clean run already done here)
    "beea21e0dd289df2d6ee73088729b548fbe0ede0",   # six edited P4 bundles (g2_controls, h1_inv_a/b/c, h2_spec_a/b), one-pass clean build
    "4c4017bd0c9fd7185490a754fd39ffac0bc9c974",   # procedural amendment 2026-10-07: six edited bundles rebuilt with matches.json embedded in h2_spec_a/b (otherwise byte-identical to beea21e except BUNDLE_INFO)
    "649988dfe284e950d167a9f7a1ec91e3dc74a3f7",   # Q10 B 2026-10-08: M2 predictor mask_index 0 (only src/vjepa_study/models/m2_vjepa2.py differs from 4c4017b bundles; used by M2 only); p4_clean_m2_mi0 bundle
    "df52a7c41d601d1a61629b659b60c98e2ec67efa",   # 2026-10-08: twelve M2 edited-group bundles (m2_*), one-pass clean build; src/ and kaggle/common identical to 649988d
    "b8f604b3951ee6a3a7f3a0299f9c3f5b0a6a92f5",   # 2026-10-08: ip2main_clean_m1 bundle (IntPhys 2 Main, M1 clean, descriptive); run_lib and src/ identical to df52a7c, adds only kaggle/ip2main/*
    "28f44a7a047a67b449f46205b6c6a3b474bbccfd",   # 2026-10-10: EXPLORATORY expl_onset_spec / expl_halve_hold bundles (onset-aligned matches, halve_hold); run_lib and src/ identical to the h1/h2 bundles, adds only kaggle/expl/*
)


def run_meta_check(root, models, out, allow=False, allowed_heads=REPO_HEAD_ALLOWLIST):
    """Every contrast must compare runs of identical precision and code: reads meta.json of every run directory of
    the given models (and M0r) under `root`; mismatching precision / n_gpus (per model) always abort; a repo_head
    outside the allowlist aborts unless allow=True (then recorded in meta_check.json)."""
    root = Path(root)
    wanted = tuple(f"P4_{m}_" for m in list(models) + ["M0r"])
    metas = {}
    for d in sorted(root.iterdir()) if root.exists() else []:
        if d.is_dir() and d.name.startswith(wanted) and d.name not in EXCLUDED_RUNS and (d / "surprise.npz").exists():
            f = d / "meta.json"
            metas[d.name] = json.loads(f.read_text()) if f.exists() else None
    r = P.check_run_meta(metas, allowed_heads=allowed_heads)
    r["n_runs"] = len(metas)
    r["allowed_heads"] = list(allowed_heads)
    r["bypassed"] = bool(allow and not r["ok"])
    wj(Path(out), "meta_check.json", r)
    hard = [m for m in r["mismatches"] if m["key"] != "repo_head"]    # precision / n_gpus are never bypassed
    if hard or (not r["ok"] and not allow):
        raise RuntimeError("run meta mismatch (precision / n_gpus / repo_head); see meta_check.json: "
                           + json.dumps([(m["group"], m["key"], m["values"]) for m in r["mismatches"]]))
    return r


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="results/runs")
    ap.add_argument("--out", default="results/analysis")
    ap.add_argument("--matches")
    ap.add_argument("--retention")
    ap.add_argument("--models", nargs="+", default=["M1"])
    ap.add_argument("--stages", nargs="+", default=["clean"])
    ap.add_argument("--n-boot", type=int, default=10000)
    ap.add_argument("--tau-scale", type=float, default=1.0, help="0 = exact-tie sensitivity (ties counted 0.5)")
    ap.add_argument("--tie-mode", default="tiehalf", choices=["tiehalf", "strict"],
                    help="strict = released '<' convention (no tolerance, ties count 0); applies to h1/h2/h3")
    ap.add_argument("--fp32-runs", help="dir with the P2 fp32 clean run (M1 H1 eligibility is judged on it)")
    ap.add_argument("--h1-agg", default="mean", choices=["mean", "max"], help="A1 ablation: H1 with max aggregation")
    ap.add_argument("--agg", default="primary", choices=list(VARIANTS), help="A1 ablation for h2/h3: full-clip max or mean aggregation")
    ap.add_argument("--fixed-c", type=int, choices=sorted(C_INDEX), help="A2 ablation: fixed context length C instead of min over C (h1/h2/h3)")
    ap.add_argument("--allow-meta-mismatch", action="store_true")
    a = ap.parse_args(argv)
    R, out = Runs(a.runs), Path(a.out)
    run_meta_check(R.root, a.models, out, a.allow_meta_mismatch)
    _, clean, taus = clean_stage(R, a.models, out, a.n_boot)
    matches = json.load(open(a.matches)) if a.matches else None
    for m in a.models:
        if "h1" in a.stages:
            elig = None
            if m == "M1" and a.fp32_runs:
                f32 = schema.load_surprise(Path(a.fp32_runs) / "P2_M1_ipdev_clean_s1" / "surprise.npz")
                elig = float(P.clean_pair_y(f32, P.tau_m(P.video_scores(f32, "S", "mean")), "mean")[0].mean())
            h1_stage(R, m, clean[m], h1_var(a.h1_agg, a.fixed_c, a.tie_mode, a.tau_scale), out, a.n_boot,
                     json.load(open(a.retention)) if a.retention else None, elig)
        if "h3" in a.stages and m == "M1":
            h3_stage(R, m, clean[m], R.need(R.clean_id("M0r", "init0")), out, a.n_boot,
                     make_var("h3", a.agg, a.fixed_c, a.tie_mode, a.tau_scale))
    if "h2" in a.stages:
        h2_stage(R, a.models, clean, matches, out, a.n_boot, make_var("h2", a.agg, a.fixed_c, a.tie_mode, a.tau_scale))


if __name__ == "__main__":
    main()
