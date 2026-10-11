"""Pair-level fp32 (P2 clean) vs fp16 (P4 clean) M1 comparison on the same 180 dev pairs, plus a table of the precision
recorded in every meta.json under results/raw. Output results/analysis/precision_audit.json. Uses frozen prereg functions."""
import collections, glob, json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from vjepa_study import schema
from vjepa_study.analysis import prereg as P

L = lambda p: schema.load_surprise(f"results/raw/{p}/surprise.npz")
f32, f16 = L("p2_clean/results/P2_M1_ipdev_clean_s1"), L("p4_clean_m1/results/P4_M1_ipdev_clean_s1")
assert list(f32["video_ids"]) == list(f16["video_ids"])
px = P.pair_index(f32)
r = {}
for n, d in (("fp32", f32), ("fp16", f16)):
    s = P.video_scores(d, "S", "mean"); tau = P.tau_m(s); dm = s[px["imp"]] - s[px["pos"]]
    r[n] = dict(tau=tau, dm=dm, y=P.y_tiehalf(s[px["imp"]], s[px["pos"]], tau), ys=(dm > 0).astype(float))
y32, y16 = r["fp32"]["y"], r["fp16"]["y"]
dis = y32 != y16
disS = r["fp32"]["ys"] != r["fp16"]["ys"]
t32, t16 = abs(r["fp32"]["dm"]) <= r["fp32"]["tau"], abs(r["fp16"]["dm"]) <= r["fp16"]["tau"]
sg = np.where(np.sign(r["fp32"]["dm"]) != np.sign(r["fp16"]["dm"]))[0]
out = dict(
    n_pairs=len(y32),
    fp32=dict(run="P2_M1_ipdev_clean_s1", acc_tiehalf=float(y32.mean()), acc_strict=float(r["fp32"]["ys"].mean()), ties=int(t32.sum()), tau=r["fp32"]["tau"], pairs_right=int((y32 == 1).sum()), pairs_wrong=int((y32 == 0).sum())),
    fp16=dict(run="P4_M1_ipdev_clean_s1", acc_tiehalf=float(y16.mean()), acc_strict=float(r["fp16"]["ys"].mean()), ties=int(t16.sum()), tau=r["fp16"]["tau"], pairs_right=int((y16 == 1).sum()), pairs_wrong=int((y16 == 0).sum())),
    delta_acc_tiehalf_pp=float((y16.mean() - y32.mean()) * 100), delta_acc_strict_pp=float((r["fp16"]["ys"].mean() - r["fp32"]["ys"].mean()) * 100),
    n_verdicts_changed_tiehalf=int(dis.sum()), n_verdicts_changed_strict=int(disS.sum()),
    transitions_tiehalf_32_to_16={f"{a}->{b}": c for (a, b), c in collections.Counter(zip(y32[dis].tolist(), y16[dis].tolist())).items()},
    n_pairs_improved_in_fp16=int((y16 > y32).sum()), n_pairs_worsened_in_fp16=int((y16 < y32).sum()),
    tie_sets=dict(both=int((t32 & t16).sum()), fp32_only=int((t32 & ~t16).sum()), fp16_only=int((~t32 & t16).sum())),
    n_margin_sign_changes=int(len(sg)), sign_change_pair_idx=sg.tolist(),
    margin_abs_diff=dict(max=float(abs(r["fp16"]["dm"] - r["fp32"]["dm"]).max()), mean=float(abs(r["fp16"]["dm"] - r["fp32"]["dm"]).mean())),
    median_abs_margin_fp32=float(np.median(abs(r["fp32"]["dm"]))),
    B1_B2_arrays_identical_fp32_fp16=bool(all(np.array_equal(np.nan_to_num(f32[k]), np.nan_to_num(f16[k])) for k in ("B1", "B2"))),
)
m2 = L("p4_clean_m2_mi0/results/P4_M2_ipdev_clean-mi0_s1")
s2 = P.video_scores(m2, "S", "mean"); t2 = P.tau_m(s2); y2, ys2, _ = P.clean_pair_y(m2, t2, "mean")
out["M2_mi0_fp16_clean_recomputed"] = dict(run="P4_M2_ipdev_clean-mi0_s1", acc_tiehalf=float(y2.mean()), acc_strict=float(ys2.mean()), ties=int((y2 == .5).sum()), tau=t2)
tab = {}
for f in sorted(glob.glob("results/raw/*/results/*/meta.json")):
    m = json.load(open(f)); run = m.get("run", {})
    if not isinstance(run, dict) or "run_id" not in run:
        continue
    tab[run["run_id"]] = dict(group=f.split("/")[2], precision=run.get("precision") or m.get("precision"), n_gpus=run.get("n_gpus") or m.get("n_gpus"),
                              repo_head=((m.get("env", {}).get("bundle") or {}).get("repo_head") or "")[:7], frame_step=run.get("frame_step"))
out["precision_by_run"] = tab
Path("results/analysis/precision_audit.json").write_text(json.dumps(out, indent=1))
print(json.dumps({k: v for k, v in out.items() if k != "precision_by_run"}, indent=1))
print(collections.Counter(v["precision"] for v in tab.values()))
