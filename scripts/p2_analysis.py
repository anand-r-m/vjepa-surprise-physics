"""G1-type outputs only (MJ9): pairwise accuracy per block, finiteness, determinism.
No per-pair margins are printed or stored."""
import json, sys
from pathlib import Path
import numpy as np
from vjepa_study import schema
from vjepa_study.analysis import metrics as M

R = Path(sys.argv[1])
OUT = Path(sys.argv[2])


def load(rid):
    return schema.load_surprise(R / rid / "surprise.npz")


def acc(d, key="S", how="mean"):
    lab, pid, blk = d["label"], d["pair_id"], d["block"]
    sc = np.array([M.aggregate_S(d[key][i][: d["lengths"][i]], how) for i in range(len(lab))])
    res = {b: ([], []) for b in sorted(set(blk))}
    for p in sorted(set(pid)):
        i = np.flatnonzero(pid == p)
        a, b = i[lab[i] == 0][0], i[lab[i] == 1][0]
        res[blk[a]][0].append(sc[b]); res[blk[a]][1].append(sc[a])
    strict = lambda v: float((np.array(v[0]) > np.array(v[1])).mean())
    out = {b: dict(acc=M.accuracy_ties(*v), acc_strict=strict(v), n_pairs=len(v[0]), n_ties=int(round(M.tie_rate(*v) * len(v[0]))), tie_rate=M.tie_rate(*v)) for b, v in res.items()}
    allimp = np.concatenate([np.array(v[0]) for v in res.values()]); allpos = np.concatenate([np.array(v[1]) for v in res.values()])
    out["all"] = dict(acc=M.accuracy_ties(allimp, allpos), acc_strict=strict((allimp, allpos)), n_pairs=len(allimp), n_ties=int(round(M.tie_rate(allimp, allpos) * len(allimp))), tie_rate=M.tie_rate(allimp, allpos))
    return out


res = {}
m1 = load("P2_M1_ipdev_clean_s1")
res["finite"] = {k: bool(np.isfinite(m1[k][~np.isnan(m1[k])]).all()) for k in ("S", "B1", "B2", "B3")}
res["n_videos"] = int(len(m1["video_ids"]))
for name, key in (("M1", "S"), ("B1", "B1"), ("B2", "B2"), ("B3", "B3")):
    res[name] = {how: acc(m1, key, how) for how in ("mean", "max")}
m0 = [load(f"P2_M0r_ipdev_clean-init{i}_s1") for i in range(3)]
res["M0r"] = {}
for how in ("mean", "max"):
    per = [acc(d, "S", how) for d in m0]
    res["M0r"][how] = {b: dict(strict_mean=float(np.mean([p[b]["acc_strict"] for p in per])), tie_rate_mean=float(np.mean([p[b]["tie_rate"] for p in per])), mean=float(np.mean([p[b]["acc"] for p in per])),
                               min=float(np.min([p[b]["acc"] for p in per])),
                               max=float(np.max([p[b]["acc"] for p in per])),
                               per_init=[p[b]["acc"] for p in per]) for b in per[0]}
res["M0r_finite"] = all(bool(np.isfinite(d["S"][~np.isnan(d["S"])]).all()) for d in m0)
rep = load("P2_M1_ipdev_clean-rep_s1")
assert list(rep["video_ids"]) == list(m1["video_ids"])
diff = np.abs(m1["S"] - rep["S"])
res["determinism"] = dict(max_abs_dS=float(np.nanmax(diff)), mean_abs_dS=float(np.nanmean(diff)), atol=1e-4,
                          passed=bool(np.nanmax(diff) <= 1e-4), n_videos=int(len(rep["video_ids"])),
                          same_pixel_hashes=bool((m1["video_hash"] == rep["video_hash"]).all()))
res["S_range"] = [float(np.nanmin(m1["S"])), float(np.nanmax(m1["S"]))]
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(res, indent=1))
print(json.dumps(res, indent=1))
