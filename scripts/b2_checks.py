"""Pre-freeze checks on baseline B2 (copy-last-context-frame). Clean runs only (no edited outputs exist).
(i) bug checks: independent recomputation, within-pair label shuffle, video-vs-itself, B1/B2 definitions side by side;
(ii) encoding/length/splice-jump artifact check on IntPhys dev; (iii) accuracy by visible/occluded, scene type, block.
Writes results/analysis/b2_checks.json. Run: PYTHONPATH=src .venv/bin/python scripts/b2_checks.py"""
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
from scipy import stats

from vjepa_study import amend, data, schema
from vjepa_study.analysis import baselines as bl, prereg as P

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "results/raw/p2_clean/results/P2_M1_ipdev_clean_s1/surprise.npz"
NPZ = ROOT / "kaggle/datasets/intphys-dev-npz"
DEVDIR = ROOT / "data/intphys_dev/extracted/dev"
KIT = ROOT / "data/intphys_dev/starting_kit.zip"
OUT = ROOT / "results/analysis/b2_checks.json"
N_SHUF, SEED = 5000, 20261007


# ------------------------------------------------------------------ pure helpers (unit-tested)
def pair_acc(s, px, how_tau=True):
    """(tie-half, strict, n_ties) from per-video scalar scores s and pair index px, prereg tau = 2e-4 x median."""
    tau = P.tau_m(s) if how_tau else 0.0
    y = P.y_tiehalf(s[px["imp"]], s[px["pos"]], tau)
    return float(y.mean()), float(P.y_strict(s[px["imp"]], s[px["pos"]]).mean()), int((y == 0.5).sum())


def shuffle_within_pairs(s, px, n, seed, tau):
    """Accuracy distribution (tie-half) when possible/impossible labels are randomly swapped inside each pair."""
    rng = np.random.default_rng(seed)
    a, b = s[px["imp"]], s[px["pos"]]
    out = np.empty(n)
    for i in range(n):
        sw = rng.random(len(a)) < 0.5
        x, r = np.where(sw, b, a), np.where(sw, a, b)
        out[i] = P.y_tiehalf(x, r, tau).mean()
    return out


def auroc(x_imp, x_pos):
    """P(x_imp > x_pos) + 0.5 P(tie) (Mann-Whitney)."""
    u = stats.mannwhitneyu(np.asarray(x_imp, float), np.asarray(x_pos, float), alternative="two-sided").statistic
    return float(u / (len(x_imp) * len(x_pos)))


def recompute_b2(frames_sub, ctx=(2, 4, 6, 8, 10), window=16, stride=2):
    """Independent loop implementation of copy-last-context-frame error (not calling baselines.py)."""
    f = np.asarray(frames_sub, np.float32)
    rows = []
    for s in range(0, len(f) - window + 1, stride):
        row = []
        for c in ctx:
            err = [np.abs(f[p] - f[s + c - 1]).mean() for p in range(s + c, s + window)]
            row.append(np.mean(err))
        rows.append(row)
    return np.array(rows, np.float32)


def recompute_b1(frames_sub, ctx=(2, 4, 6, 8, 10), window=16, stride=2):
    f = np.asarray(frames_sub, np.float32)
    rows = []
    for s in range(0, len(f) - window + 1, stride):
        row = []
        for c in ctx:
            row.append(np.mean([np.abs(f[p] - f[p - 1]).mean() for p in range(s + c, s + window)]))
        rows.append(row)
    return np.array(rows, np.float32)


def native_jumps(fr):
    """mean abs pixel change between consecutive native frames (T-1,)."""
    f = fr.astype(np.int16)
    return np.abs(f[1:] - f[:-1]).mean(axis=(1, 2, 3))


def first_divergence(a, b):
    d = np.abs(a.astype(np.int16) - b.astype(np.int16)).sum(axis=(1, 2, 3))
    nz = np.flatnonzero(d)
    return int(nz[0]) if len(nz) else len(d)


def local_max(j, t, w=3):
    lo, hi = max(0, t - 1 - w), min(len(j), t + w)
    return float(j[lo:hi].max()) if hi > lo else float("nan")


def cond_from_name(name):
    tok = name.split("_")
    vis = "visible" if "visible" in tok else "occluded"
    typ = "static" if "static" in tok else ("dynamic_1" if "dynamic_1" in name else "dynamic_2")
    return vis, typ


def quad_size_balance():
    """Per quadruplet: sum of PNG bytes of the 2 possible vs the 2 impossible videos (pure encoding-size balance)."""
    diffs = []
    for q in sorted(DEVDIR.glob("O*/*")):
        pos = imp = 0
        for k in "1234":
            sz = sum(f.stat().st_size for f in (q / k / "scene").glob("*.png"))
            ok = json.loads((q / k / "status.json").read_text())["header"]["is_possible"]
            pos, imp = (pos + sz, imp) if ok else (pos, imp + sz)
        diffs.append(pos - imp)
    return dict(n_quadruplets=len(diffs), n_exactly_equal=int(sum(x == 0 for x in diffs)), max_abs_diff_bytes=int(max(map(abs, diffs))))


# ------------------------------------------------------------------ main
def main():
    d = schema.load_surprise(RUN)
    px = P.pair_index(d)
    vids = [str(v) for v in d["video_ids"]]
    n = len(vids)
    res = dict(run=str(RUN.relative_to(ROOT)), n_videos=n, n_pairs=len(px["pos"]), tau_rule="2e-4 x median over 360 videos of the per-video score (mean agg: mean over windows of min over C)",
               n_shuffle=N_SHUF, shuffle_seed=SEED)
    frames = {}
    for v in vids:
        b, sc, k = v.split("/")
        with np.load(NPZ / f"{b}_{sc}_{k}.npz") as z:
            frames[v] = z["frames"]
    subs = {v: amend.to_model_res(frames[v][data.sample_indices(len(frames[v]), 2)], 224) for v in vids}

    # ---- (i)(c) definitions and accuracies side by side
    B = {"B1_windowed(stored B1; spec-literal frame-diff over predicted window)": np.array([np.asarray(d["B1"][i]) for i in range(n)]),
         "B2_copy_last_context(stored B2)": np.array([np.asarray(d["B2"][i]) for i in range(n)])}
    keys = {"B1": d["B1"], "B2": d["B2"], "M1": d["S"]}
    dd = dict(d)
    wh = [bl.b1_whole_window(subs[v]) for v in vids]
    W = max(map(len, wh))
    dd["B1whole"] = np.full((n, W, 1), np.nan, np.float32)
    for i, w in enumerate(wh):
        dd["B1whole"][i, : len(w), 0] = w
    keymap = {"M1": "S", "B1_windowed": "B1", "B1_whole_window": "B1whole", "B2_copy_last_context": "B2"}
    scores = {"mean": {}, "max": {}}
    for nm, k in keymap.items():
        for how in ("mean", "max"):
            s = P.video_scores(dd, k, how)
            scores[how][nm] = s
    res["accuracy_clean"] = {}
    for how in ("mean", "max"):
        res["accuracy_clean"][how] = {}
        for nm in keymap:
            th, st, nt = pair_acc(scores[how][nm], px)
            res["accuracy_clean"][how][nm] = dict(acc_tiehalf=th, acc_strict=st, n_ties=nt, tau=P.tau_m(scores[how][nm]))

    # ---- (i)(a') independent recomputation of stored B1/B2 from frames
    dev_b2 = dev_b1 = 0.0
    for i, v in enumerate(vids):
        dev_b2 = max(dev_b2, float(np.abs(recompute_b2(subs[v]) - np.asarray(d["B2"][i])).max()))
        dev_b1 = max(dev_b1, float(np.abs(recompute_b1(subs[v]) - np.asarray(d["B1"][i])).max()))
    res["independent_recompute_max_abs_dev_vs_stored"] = dict(B2=dev_b2, B1=dev_b1)

    # ---- (i)(a) label shuffle within pairs
    res["label_shuffle"] = {}
    for nm in keymap:
        s = scores["mean"][nm]
        tau = P.tau_m(s)
        dist = shuffle_within_pairs(s, px, N_SHUF, SEED, tau)
        obs = pair_acc(s, px)[0]
        res["label_shuffle"][nm] = dict(observed_tiehalf=obs, null_mean=float(dist.mean()), null_sd=float(dist.std(ddof=1)),
                                        null_q025=float(np.quantile(dist, .025)), null_q975=float(np.quantile(dist, .975)),
                                        frac_null_ge_observed=float((dist >= obs).mean()), n_shuffles=N_SHUF)

    # ---- (i)(b) video vs itself
    t_self = {}
    for nm, k in keymap.items():
        s = scores["mean"][nm]
        tau = P.tau_m(s)
        y_pos = P.y_tiehalf(s[px["pos"]], s[px["pos"]], tau)
        y_imp = P.y_tiehalf(s[px["imp"]], s[px["imp"]], tau)
        t_self[nm] = dict(all_ties=bool((y_pos == .5).all() and (y_imp == .5).all()),
                          strict_acc=float(P.y_strict(s[px["pos"]], s[px["pos"]]).mean()))
    z = max(float(np.abs(frames[v].astype(np.int16) - frames[v].astype(np.int16)).max()) for v in vids)
    rng = np.random.default_rng(SEED)
    chk = rng.choice(n, 24, replace=False)
    redec = []
    for i in chk:  # re-decode PNGs independently and score against the stored npz frames
        from PIL import Image
        b, sc, k = vids[i].split("/")
        files = sorted((DEVDIR / b / sc / k / "scene").glob("scene_*.png"))
        png = np.stack([np.asarray(Image.open(f).convert("RGB")) for f in files])
        redec.append(float(np.abs(png.astype(np.int16) - frames[vids[i]].astype(np.int16)).max()) if png.shape == frames[vids[i]].shape else float("nan"))
        sub = amend.to_model_res(png[data.sample_indices(len(png), 2)], 224)
        redec[-1] = max(redec[-1], float(np.abs(bl.b2_windows(sub) - np.asarray(d["B2"][i])).max()))
    res["video_vs_itself"] = dict(per_baseline=t_self, max_pixel_diff_v_minus_v=z,
                                  png_redecode_vs_npz_and_stored_B2_max_dev_24_videos=float(np.nanmax(redec)))

    # ---- (ii) artifact check
    from PIL import Image
    feat = {k: np.zeros(n) for k in ("n_frames", "total_png_bytes", "mean_bytes_per_frame", "max_native_jump", "mean_native_jump", "max_jump_near_event", "mean_jump_near_event")}
    png_info, png_modes, sizes = set(), set(), set()
    jumps = {}
    for i, v in enumerate(vids):
        b, sc, k = v.split("/")
        files = sorted((DEVDIR / b / sc / k / "scene").glob("scene_*.png"))
        bytes_ = np.array([f.stat().st_size for f in files])
        feat["n_frames"][i], feat["total_png_bytes"][i], feat["mean_bytes_per_frame"][i] = len(files), bytes_.sum(), bytes_.mean()
        if i % 30 == 0 or True:
            with Image.open(files[0]) as im:
                png_modes.add(im.mode); sizes.add(im.size); png_info.add(tuple(sorted(im.info.keys())))
        j = native_jumps(frames[v])
        jumps[v] = j
        feat["max_native_jump"][i], feat["mean_native_jump"][i] = j.max(), j.mean()
    tdiv = np.zeros(len(px["pos"]), int)
    for p in range(len(px["pos"])):
        ip, ii = px["pos"][p], px["imp"][p]
        t = first_divergence(frames[vids[ip]], frames[vids[ii]])
        tdiv[p] = t
        for q in (ip, ii):
            feat["max_jump_near_event"][q] = local_max(jumps[vids[q]], t)
            feat["mean_jump_near_event"][q] = float(jumps[vids[q]][max(0, t - 4): t + 3].mean())
    lab = np.zeros(n, int)
    lab[px["imp"]] = 1
    art = {}
    for k, x in feat.items():
        xi, xp = x[px["imp"]], x[px["pos"]]
        d_ = xi - xp
        art[k] = dict(auroc_pooled_videos=auroc(x[lab == 1], x[lab == 0]) if x.std() > 0 else 0.5,
                      pair_acc_tiehalf=float(np.where(np.abs(d_) <= 1e-12, .5, (d_ > 0)).mean()),
                      pair_acc_strict=float((d_ > 0).mean()),
                      sign_test_p=float(stats.binomtest(int((d_ > 0).sum()), int((d_ != 0).sum()), .5).pvalue) if (d_ != 0).any() else 1.0,
                      mean_possible=float(xp.mean()), mean_impossible=float(xi.mean()), n_pairs_equal=int((d_ == 0).sum()),
                      per_block={bk: dict(pair_acc_tiehalf=float(np.where(np.abs(d_[px["block"] == bk]) <= 1e-12, .5, (d_[px["block"] == bk] > 0)).mean()),
                                          auroc_pooled=auroc(xi[px["block"] == bk], xp[px["block"] == bk]) if x.std() > 0 else .5) for bk in ("O1", "O2", "O3")})
    res["artifact_check"] = dict(
        container="PNG image sequences (scene_###.png, lossless, no video codec/bitrate; ffprobe and cv2 not installed, PIL used)",
        png_modes=sorted(png_modes), png_sizes=[list(s) for s in sizes], png_info_keys_first_frame=[list(k) for k in png_info],
        frame_counts=sorted(set(feat["n_frames"].astype(int).tolist())), npz_frame_counts=sorted({len(frames[v]) for v in vids}),
        first_divergence_frame=dict(min=int(tdiv.min()), median=float(np.median(tdiv)), max=int(tdiv.max()), n_never_diverge=int((tdiv >= 100).sum())),
        features=art, quadruplet_png_size_balance=quad_size_balance())

    # ---- (iii) breakdowns
    names = {}
    with zipfile.ZipFile(KIT) as zf:
        for line in zf.read("dev/task.txt").decode().split():
            blk_sc, vid = line.rsplit("/", 1)
            blk, rest = blk_sc.split("/")[0], blk_sc.split("/", 1)[1]
            names[(blk, rest[:2])] = rest
    cond = [cond_from_name(names[(b, sc)]) for (b, sc, _) in (v.split("/") for v in vids)]
    cvis = np.array([c[0] for c in cond])
    ctyp = np.array([c[1] for c in cond])
    res["metadata_note"] = "dev folders hold only status.json is_possible; visible/occluded and static/dynamic come from folder names in data/intphys_dev/starting_kit.zip dev/task.txt (e.g. O1/09_test_occluded_static_nobj2)"
    groups = {"all": np.ones(len(px["pos"]), bool)}
    for g in ("visible", "occluded"):
        groups[g] = cvis[px["pos"]] == g
    for g in ("static", "dynamic_1", "dynamic_2"):
        groups[g] = ctyp[px["pos"]] == g
    for bk in ("O1", "O2", "O3"):
        groups[bk] = px["block"] == bk
    for bk in ("O1", "O2", "O3"):
        for g in ("visible", "occluded"):
            groups[f"{bk}_{g}"] = (px["block"] == bk) & (cvis[px["pos"]] == g)
    res["breakdown_mean_agg"] = {}
    for g, m in groups.items():
        row = dict(n_pairs=int(m.sum()))
        for nm in keymap:
            s = scores["mean"][nm]
            tau = P.tau_m(s)  # tau fixed from all 360 videos, as pre-registered
            y = P.y_tiehalf(s[px["imp"][m]], s[px["pos"][m]], tau)
            ys = P.y_strict(s[px["imp"][m]], s[px["pos"][m]])
            row[nm] = dict(tiehalf=float(y.mean()), strict=float(ys.mean()), n_ties=int((y == .5).sum()))
        res["breakdown_mean_agg"][g] = row
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1))
    print(json.dumps({k: res[k] for k in ("accuracy_clean", "independent_recompute_max_abs_dev_vs_stored", "label_shuffle", "video_vs_itself")}, indent=1))
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "per_block"} for k, v in res["artifact_check"]["features"].items()}, indent=1))
    print(json.dumps(res["breakdown_mean_agg"], indent=1))


if __name__ == "__main__":
    if "--only-quadsum" in sys.argv:  # fast refresh of one field of an existing b2_checks.json
        r = json.loads(OUT.read_text())
        r["artifact_check"]["quadruplet_png_size_balance"] = quad_size_balance()
        OUT.write_text(json.dumps(r, indent=1))
        print(r["artifact_check"]["quadruplet_png_size_balance"])
    else:
        main()
