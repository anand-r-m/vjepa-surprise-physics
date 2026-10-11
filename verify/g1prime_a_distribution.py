"""G1'(a) fallback: released row->video order is not reproducible, so compare (i) row-wise agreement among released models (same row order),
(ii) video-id-wise agreement ours L vs ours H, (iii) distribution (sorted-value) comparison ours vs released."""
import sys, json, numpy as np
sys.path.insert(0, "/home/anand-r-m/Research & Dev/Vjepa/verify")
import released_dev_accuracy as R
from scipy.stats import pearsonr, spearmanr
rels = ["vit-l-rope-vm2m","vit-l-rope-howto","vit-h-rope-vm2m","vit-h-rope-howto"]
rel = {m: np.concatenate([R.load_pth(f"{R.RAW}/data_intphys/{m}/intphys/raw_surprises/{b}_16frames.pth")["losses"].astype(float).min(1).mean(1) for b in R.BLOCKS]) for m in rels}
zl = np.load(R.ROOT+"/results/raw/p2_clean/results/P2_M1_ipdev_clean_s1/surprise.npz", allow_pickle=True)
zh = np.load(R.ROOT+"/results/raw/p2_vith/results/P2H_M1H_ipdev_clean_s1/surprise.npz", allow_pickle=True)
sl = zl["S"].astype(float).min(2).mean(1); sh = zh["S"].astype(float).min(2).mean(1)
assert [str(x) for x in zl["video_ids"]]==[str(x) for x in zh["video_ids"]]
out = {"released_rowwise": {}, "ours_L_vs_H_by_video_id": [float(pearsonr(sl,sh)[0]), float(spearmanr(sl,sh)[0])], "quantile": {}}
for i,a in enumerate(rels):
    for b in rels[i+1:]: out["released_rowwise"][a+" vs "+b] = [float(pearsonr(rel[a],rel[b])[0]), float(spearmanr(rel[a],rel[b])[0])]
for k,o in (("ours_L",sl),("ours_H",sh)):
    for m in rels:
        out["quantile"][f"{k} vs {m}"] = dict(qq_pearson=float(pearsonr(np.sort(o),np.sort(rel[m]))[0]), ours_mean=float(o.mean()), ours_sd=float(o.std(ddof=1)), rel_mean=float(rel[m].mean()), rel_sd=float(rel[m].std(ddof=1)), n=360)
json.dump(out, open(R.ROOT+"/verify/g1prime_a_distribution.json","w"), indent=1); print(json.dumps(out, indent=1))
