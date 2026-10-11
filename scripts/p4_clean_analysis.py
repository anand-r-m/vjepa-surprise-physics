"""Clean-run outputs only (MJ9): tau_m, accuracies (tie-half and strict, mean and max aggregation), tie counts,
finiteness, fp16-vs-fp32 clean difference for M1, B1/B2 variants, M0r degeneracy. No t*-dependent statistic,
no per-pair margins. Reads results/runs/<run_id>/surprise.npz (copy kernel outputs there first)."""
import json
import sys
from pathlib import Path
import numpy as np
from vjepa_study import amend, data, schema
from vjepa_study.analysis import baselines as bl, prereg as P

ROOT = Path(__file__).resolve().parents[1]
RUNS = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "results/runs"
FP32 = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "results/raw/p2_clean/results"
OUT = ROOT / "results/analysis/p4_clean_g1.json"
L = lambda root, rid: schema.load_surprise(Path(root) / rid / "surprise.npz")


def accs(d, key, tau_mean, tau_max):
    r = {"finite": bool(np.isfinite(d[key][~np.isnan(d[key])]).all())}
    for how in ("mean", "max"):
        tau = tau_mean if how == "mean" else tau_max          # tau is aggregation-specific (prereg sec 2)
        y, ys, px = P.clean_pair_y(d, tau, how, key=key)
        r[how] = dict(tau_used=tau, acc_tiehalf=float(y.mean()), acc_strict=float(ys.mean()), n_pairs=len(y), n_ties=int((y == 0.5).sum()),
                      per_block={str(b): dict(acc_tiehalf=float(y[px["block"] == b].mean()), acc_strict=float(ys[px["block"] == b].mean()),
                                              n_ties=int((y[px["block"] == b] == 0.5).sum())) for b in np.unique(px["block"])})
    return r


res = dict(runs_dir=str(RUNS), tau={}, models={})
# Corrected M2 (Q10 B, mask_index 0). The old P4_M2_ipdev_clean_s1 (mask_index 1) is reported separately as the wrapper deviation.
clean = {"M1": L(RUNS, "P4_M1_ipdev_clean_s1"), "M2": L(RUNS, "P4_M2_ipdev_clean-mi0_s1"), "M1_skip4": L(RUNS, "P4_M1_ipdev_clean-skip4_s1")}
for i in range(3):
    clean[f"M0r_init{i}"] = L(RUNS, f"P4_M0r_ipdev_clean-init{i}_s1")
for name, d in clean.items():
    keys = ["S"] + [k for k in ("B1", "B2", "B3") if k in d]
    for key in keys:
        nm = name if key == "S" else f"{key}({name})"
        sc = P.video_scores(d, key, "mean")
        tau = P.tau_m(sc)
        tau_max = P.tau_m(P.video_scores(d, key, "max"))
        res["tau"][nm] = dict(tau_mean=tau, tau_max=tau_max, median_per_video_mean_score=float(np.median(sc)),
                              median_per_video_max_score=float(np.median(P.video_scores(d, key, "max"))), n_videos=int(len(sc)))
        res["models"][nm] = accs(d, key, tau, tau_max)
# M0r summary (mean +- range over inits)
for how in ("mean", "max"):
    a = [res["models"][f"M0r_init{i}"][how]["acc_tiehalf"] for i in range(3)]
    s = [res["models"][f"M0r_init{i}"][how]["acc_strict"] for i in range(3)]
    t = [res["models"][f"M0r_init{i}"][how]["n_ties"] for i in range(3)]
    res.setdefault("M0r_summary", {})[how] = dict(tiehalf_mean=float(np.mean(a)), tiehalf_range=[min(a), max(a)],
                                                  strict_mean=float(np.mean(s)), strict_range=[min(s), max(s)], n_ties=t)
# M0r between-video SD of S relative to M1
sd = lambda d: float(np.std(P.video_scores(d, "S", "mean"), ddof=1))
res["between_video_sd_of_S"] = dict(M1=sd(clean["M1"]), M2=sd(clean["M2"]), **{f"M0r_init{i}": sd(clean[f"M0r_init{i}"]) for i in range(3)})
res["between_video_sd_of_S"]["M0r_over_M1"] = [res["between_video_sd_of_S"][f"M0r_init{i}"] / res["between_video_sd_of_S"]["M1"] for i in range(3)]
# B1 / B2 variants. Stored B1 = frame difference over the PREDICTED window (== spec-literal B2 wording); stored B2 =
# copy-last-context-frame error. B1 whole-window = spec B1 (all frames of the window), recomputed from clean frames.
dev = ROOT / "kaggle/datasets/intphys-dev-npz"
d = clean["M1"]
vals = []
for vid in d["video_ids"]:
    b, sc, k = str(vid).split("/")
    with np.load(dev / f"{b}_{sc}_{k}.npz") as z:
        fr = z["frames"]
    sub = amend.to_model_res(fr[data.sample_indices(len(fr), 2)], 224)
    vals.append(bl.b1_whole_window(sub))
dd = dict(d)
dd["B1whole"] = np.full((len(vals), max(map(len, vals)), 1), np.nan, np.float32)
for i, v in enumerate(vals):
    dd["B1whole"][i, : len(v), 0] = v
sc = P.video_scores(dd, "B1whole", "mean")
tau = P.tau_m(sc)
tau_max = P.tau_m(P.video_scores(dd, "B1whole", "max"))
res["tau"]["B1_whole_window(M1)"] = dict(tau_mean=tau, tau_max=tau_max, median_per_video_mean_score=float(np.median(sc)))
res["models"]["B1_whole_window(M1)"] = accs(dd, "B1whole", tau, tau_max)
res["B2_wording"] = dict(
    literal_frame_diff_over_predicted_window=res["models"]["B1(M1)"], copy_last_context_frame=res["models"]["B2(M1)"],
    note="spec-literal B2 (|f_t - f_{t-1}| over the predicted window) is the stored B1 restricted to predicted frames; B1 whole-window is the spec's B1")
# fp16 (P4) vs fp32 (P2) clean M1
f32 = L(FP32, "P2_M1_ipdev_clean_s1")
assert list(f32["video_ids"]) == list(d["video_ids"])
diff = np.abs(f32["S"] - d["S"])
t32 = P.tau_m(P.video_scores(f32, "S", "mean"))
y32, ys32, _ = P.clean_pair_y(f32, t32, "mean")
y16, ys16, _ = P.clean_pair_y(d, res["tau"]["M1"]["tau_mean"], "mean")
res["fp16_vs_fp32_M1"] = dict(max_abs_dS=float(np.nanmax(diff)), mean_abs_dS=float(np.nanmean(diff)),
                              video_mean_score_max_abs=float(np.abs(P.video_scores(f32, "S", "mean") - P.video_scores(d, "S", "mean")).max()),
                              acc_tiehalf_fp32=float(y32.mean()), acc_tiehalf_fp16=float(y16.mean()),
                              acc_strict_fp32=float(ys32.mean()), acc_strict_fp16=float(ys16.mean()),
                              n_pairs_verdict_changed=int((y32 != y16).sum()), tau_fp32=t32, tau_fp16=res["tau"]["M1"]["tau_mean"])
res["m1_h1_eligibility_note"] = "judged on the P2 fp32 run per prereg sec 6, never on this fp16 run"
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(res, indent=1))
print(json.dumps({k: res[k] for k in ("tau", "fp16_vs_fp32_M1", "between_video_sd_of_S", "M0r_summary")}, indent=1))
