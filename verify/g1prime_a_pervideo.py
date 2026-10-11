"""G1' (a): per-video comparison of our public-checkpoint M1/M1H surprise vs released RoPE raw surprises on the 360 dev videos.
Row->video mapping reconstructed from the released pairing rule (pixel breakpoint) and rank-interleaved scene order (world size found by label check)."""
import sys, json, numpy as np
sys.path.insert(0, "/home/anand-r-m/Research & Dev/Vjepa/verify")
import released_dev_accuracy as R
from scipy.stats import pearsonr, spearmanr
ROOT = R.ROOT
dev = R.load_dev()
ours = {"ours_L_fp32": ROOT + "/results/raw/p2_clean/results/P2_M1_ipdev_clean_s1/surprise.npz",
        "ours_H_fp32": ROOT + "/results/raw/p2_vith/results/P2H_M1H_ipdev_clean_s1/surprise.npz"}
Z = {k: np.load(v, allow_pickle=True) for k, v in ours.items()}
for k, z in Z.items(): print(k, z.files, z["S"].shape)
def rows(b, W):
    out = []  # list of "block/scene/video" in released row order
    for r in range(W):
        for si in range(r, 30, W):
            sc = dev[b][si]
            for mt in sc["matches"]:
                out += [(f"{b}/{sc['scene']}/{i+1}", int(sc["labels"][i])) for i in mt]
    return out
res = {}
rels = ["vit-l-rope-vm2m", "vit-l-rope-howto", "vit-h-rope-vm2m", "vit-h-rope-howto"]
data = {}
for m in rels:
    for b in R.BLOCKS:
        data[(m, b)] = R.load_pth(f"{R.RAW}/data_intphys/{m}/intphys/raw_surprises/{b}_16frames.pth")
W = None
for w in (1, 2, 3, 5, 6, 10, 15, 30):
    if all(np.array_equal([l for _, l in rows(b, w)], data[(rels[0], b)]["labels"].astype(int)) for b in R.BLOCKS): W = w; break
print("world size matching all label sequences:", W)
def agg(L):  # L [N,5,W]: min over contexts, mean over windows (released avg)
    return L.astype(float).min(1).mean(1)
def aggmax(L): return L.astype(float).min(1).max(1)
for kname, z in Z.items():
    ids = [str(x) for x in z["video_ids"]]
    lab_ok = None
    for m in rels:
        for aname, af in (("mean", agg), ("max", aggmax)):
            rs, os_, rel_all, our_all = [], [], [], []
            per_block = {}
            for b in R.BLOCKS:
                mp = rows(b, W); L = data[(m, b)]["losses"]; s_rel = af(L)
                idx = [ids.index(v) for v, _ in mp]
                if aname == "mean":
                    s_our = z["S"][idx].astype(float).min(2).mean(1) if z["S"].shape[2] == 5 else z["S"][idx].astype(float).min(1).mean(1)
                else:
                    s_our = z["S"][idx].astype(float).min(2).max(1) if z["S"].shape[2] == 5 else z["S"][idx].astype(float).min(1).max(1)
                rel_all += list(s_rel); our_all += list(s_our)
                per_block[b] = dict(pearson=float(pearsonr(s_rel, s_our)[0]), spearman=float(spearmanr(s_rel, s_our)[0]))
            rel_all = np.array(rel_all); our_all = np.array(our_all)
            res[f"{kname}|{m}|{aname}"] = dict(n=len(rel_all), pearson=float(pearsonr(rel_all, our_all)[0]), spearman=float(spearmanr(rel_all, our_all)[0]),
                    per_block=per_block, rel_mean=float(rel_all.mean()), our_mean=float(our_all.mean()), rel_sd=float(rel_all.std(ddof=1)), our_sd=float(our_all.std(ddof=1)))
# label consistency of our npz labels (1=impossible) vs mapping
z = Z["ours_L_fp32"]; ids = [str(x) for x in z["video_ids"]]
bad = 0
for b in R.BLOCKS:
    for v, l in rows(b, W):
        if (1 - int(z["label"][ids.index(v)])) != l: bad += 1
res["_label_mismatch_rows_vs_npz"] = bad; res["_world_size"] = W
# ours L vs ours H, and released L vs released H as reference ceiling
a = np.array([z["S"][i].astype(float).min(1).mean() if z["S"].ndim == 3 and z["S"].shape[2] != 5 else z["S"][i].astype(float).min(1).mean() for i in range(len(ids))])
json.dump(res, open(ROOT + "/verify/g1prime_a_pervideo.json", "w"), indent=1)
for k, v in res.items():
    if isinstance(v, dict): print(k, "n", v["n"], "pearson %.3f spearman %.3f" % (v["pearson"], v["spearman"]), "means rel/our %.4f/%.4f sd %.4f/%.4f" % (v["rel_mean"], v["our_mean"], v["rel_sd"], v["our_sd"]))
    else: print(k, v)
