"""EXPLORATORY (post-freeze, no GPU): sign and size of the paired shift S(vflip) - S(clean) per video for M0r and M1,
from existing raw arrays. Full-clip max (H3 aggregation), mean, and per window. Writes results/analysis/m0r_vflip_check.json."""
import json
from pathlib import Path
import numpy as np
from vjepa_study import schema
from vjepa_study.analysis import prereg as P

R = Path(__file__).resolve().parents[1] / "results/raw"
G2, CL = R / "g2_controls/results", R / "p4_clean_m1/results"
L = lambda root, rid: schema.load_surprise(root / rid / "surprise.npz")


def sel(d, ids):
    pos = {str(v): i for i, v in enumerate(d["video_ids"])}
    return [pos[str(v)] for v in ids]


def stats(x, tau):
    x = np.asarray(x, float)
    return dict(n=len(x), mean=float(x.mean()), median=float(np.median(x)), sd=float(x.std(ddof=1)),
                frac_pos=float((x > 0).mean()), frac_neg=float((x < 0).mean()), frac_zero=float((x == 0).mean()),
                frac_abs_le_tau=float((np.abs(x) <= tau).mean()), mean_over_sd=float(x.mean() / x.std(ddof=1)),
                detection_tiehalf=float(P.detection(x, 0.0, tau).mean()))


out = {}
cases = [("M1", "P4_M1_ipdev_vflip-high_s1", "P4_M1_ipdev_clean_s1"),
         ("M0r_init0", "P4_M0r_ipdev_vflip-high_s1", "P4_M0r_ipdev_clean-init0_s1"),
         ("M1_hflip", "P4_M1_ipdev_hflip-high_s1", "P4_M1_ipdev_clean_s1"),
         ("M1_timerev", "P4_M1_ipdev_time_reversal-high_s1", "P4_M1_ipdev_clean_s1"),
         ("M0r_init0_timerev", "P4_M0r_ipdev_time_reversal-high_s1", "P4_M0r_ipdev_clean-init0_s1")]
for name, edit_id, clean_id in cases:
    e, c = L(G2, edit_id), L(CL, clean_id)
    ie = [i for i, l in enumerate(e["label"]) if l == 0] if "label" in e else list(range(len(e["video_ids"])))
    ids = [e["video_ids"][i] for i in ie]
    ic = sel(c, ids)
    # tau_m from the model's own 360 clean videos (max aggregation), as in the frozen H3
    tau_max = P.tau_m(P.video_scores(c, "S", "max"))
    tau_mean = P.tau_m(P.video_scores(c, "S", "mean"))
    r = dict(edit_run=edit_id, clean_run=clean_id, n_videos=len(ids), tau_max=tau_max, tau_mean=tau_mean)
    for how, tau in (("max", tau_max), ("mean", tau_mean)):
        se = np.array([P.video_score(np.asarray(e["S"][i])[: int(e["lengths"][i])], how) for i in ie])
        sc = np.array([P.video_score(np.asarray(c["S"][i])[: int(c["lengths"][i])], how) for i in ic])
        r[f"fullclip_{how}"] = dict(S_clean_mean=float(sc.mean()), S_edit_mean=float(se.mean()), **stats(se - sc, tau),
                                    rel_shift=float((se - sc).mean() / sc.mean()))
    # per window: min-over-C curve, edit minus clean, window by window
    W = min(int(e["lengths"][ie[0]]), int(c["lengths"][ic[0]]))
    dw = np.full((len(ie), W), np.nan)
    for j, (i, k) in enumerate(zip(ie, ic)):
        a, b = P.curve(np.asarray(e["S"][i])[: int(e["lengths"][i])]), P.curve(np.asarray(c["S"][k])[: int(c["lengths"][k])])
        n = min(len(a), len(b), W)
        dw[j, :n] = a[:n] - b[:n]
    out_w = []
    for w in range(W):
        col = dw[:, w][~np.isnan(dw[:, w])]
        out_w.append(dict(w=w, mean=float(col.mean()), frac_pos=float((col > 0).mean()), n=len(col)))
    r["per_window"] = out_w
    r["per_window_summary"] = dict(mean_of_window_means=float(np.mean([x["mean"] for x in out_w])),
                                   frac_windows_mean_pos=float(np.mean([x["mean"] > 0 for x in out_w])),
                                   frac_pos_all_cells=float((dw[~np.isnan(dw)] > 0).mean()))
    # where does the max fall (window index), edit vs clean
    r["argmax_window_mean"] = dict(edit=float(np.mean([np.nanargmax(P.curve(np.asarray(e["S"][i])[: int(e["lengths"][i])])) for i in ie])),
                                   clean=float(np.mean([np.nanargmax(P.curve(np.asarray(c["S"][k])[: int(c["lengths"][k])])) for k in ic])))
    out[name] = r
Path(__file__).resolve().parents[1].joinpath("results/analysis/m0r_vflip_check.json").write_text(json.dumps(out, indent=1))
for k, r in out.items():
    print(k, r["n_videos"], "tau_max", r["tau_max"])
    for how in ("fullclip_max", "fullclip_mean"):
        s = r[how]
        print("  ", how, {x: round(s[x], 6) for x in ("S_clean_mean", "S_edit_mean", "mean", "sd", "frac_pos", "frac_neg", "frac_abs_le_tau", "mean_over_sd", "detection_tiehalf", "rel_shift")})
    print("   per-window", {k2: round(v, 4) for k2, v in r["per_window_summary"].items()}, r["argmax_window_mean"])
