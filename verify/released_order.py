import numpy as np, torch
R="/home/anand-r-m/Research & Dev/Vjepa/"
z=np.load(R+"results/raw/p2_clean/results/P2_M1_ipdev_clean_s1/surprise.npz",allow_pickle=True)
rel=lambda m,b: torch.load(f"{R}scratch_data/verify_released_raw/data_intphys/{m}/intphys/raw_surprises/{b}_16frames.pth",weights_only=False)
def perm(h,ws=6,n=30):
    if h=="H0": return list(range(n))
    return [k for r in range(ws) for k in range(r,n,ws)]  # released position p holds scene perm[p]
for m in ["vit-l-rope-vm2m","vit-l-rope-howto","vit-h-rope-vm2m","vit-h-rope-howto","vit-l-rope-random-0"]:
    for b in ["O1","O2","O3"]:
        d=rel(m,b); lab=d["labels"].numpy().astype(int)
        mk=z["block"]==b; ol=z["label"][mk]; sc=z["scene_id"][mk]
        res={}
        for h in ["H0","H1"]:
            p=perm(h); ex=np.concatenate([ol[4*k:4*k+4] for k in p])
            res[h]=int((ex==lab).sum())
        print(m,b,"label agreement of 120 rows:",res)

print("---- correlation test of order hypotheses (per-video score, min over C, mean over windows)")
from scipy.stats import pearsonr, spearmanr
ours=z["S"].astype(float).min(2).mean(1)
def mapped(b,h,lab,flip_scene=False):
    mk=np.where(z["block"]==b)[0]; p=perm(h); idx=[]
    for k in p:
        for pr in range(2):
            rows=mk[4*k+2*pr:4*k+2*pr+2]; 
            idx+= [r for r in sorted(rows,key=lambda r:-z["label"][r])]  # possible (label 1) first? placeholder
    return idx
out={}
for m in ["vit-l-rope-vm2m","vit-l-rope-howto","vit-h-rope-vm2m"]:
    for b in ["O1","O2","O3"]:
        d=rel(m,b); lab=d["labels"].numpy().astype(int); L=d["losses"].numpy().astype(float); sc=L.min(1).mean(1)
        mk=np.where(z["block"]==b)[0]; r={}
        for h in ["H0","H1"]:
            for pairmode in ["p-order","p-swap"]:
                idx=[]
                for k in perm(h):
                    for pr in (range(2) if pairmode=="p-order" else (1,0)):
                        rows=list(mk[4*k+2*pr:4*k+2*pr+2]); idx+=rows
                # within-pair label alignment
                o=[]
                for i in range(0,120,2):
                    a,bb=idx[i],idx[i+1]
                    pair={int(z["label"][a]):a,int(z["label"][bb]):bb}
                    o+= [pair[int(lab[i])],pair[int(lab[i+1])]]
                r[h+pairmode]=round(float(spearmanr(sc,ours[o])[0]),3)
        print(m,b,r)

print("---- scene-mean correlation (30 scenes/block), released 4-row groups vs our scene groups")
for m in ["vit-l-rope-vm2m","vit-l-rope-howto","vit-h-rope-vm2m"]:
    for b in ["O1","O2","O3"]:
        d=rel(m,b); sc=d["losses"].numpy().astype(float).min(1).mean(1).reshape(30,4).mean(1)
        mk=np.where(z["block"]==b)[0]; om=ours[mk].reshape(30,4).mean(1)
        r={h:round(float(spearmanr(sc,om[perm(h)])[0]),3) for h in ["H0","H1"]}
        # best-case any-permutation sanity: sorted-rank match not meaningful; report
        print(m,b,r)
