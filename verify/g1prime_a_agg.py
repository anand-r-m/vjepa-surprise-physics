# NOTE: npz label 1 = IMPOSSIBLE (verified vs data status.json is_possible for O1/01/1 and O1/01/2)
import numpy as np, torch, json
R="/home/anand-r-m/Research & Dev/Vjepa/"
z=np.load(R+"results/raw/p2_clean/results/P2_M1_ipdev_clean_s1/surprise.npz",allow_pickle=True)
sc=z["S"].astype(float).min(2).mean(1); out={}
def acc_ours(b):
    mk=z["block"]==b; s=sc[mk]; l=z["label"][mk]; p=z["pair_id"][mk]; n=0;t=0
    for pid in set(p): 
        i=np.where(p==pid)[0]; r=i[l[i]==0][0]; f=i[l[i]==1][0]; n+= s[r]<s[f]; t+=1
    return 100*n/t, t
rel=lambda m,b: torch.load(f"{R}scratch_data/verify_released_raw/data_intphys/{m}/intphys/raw_surprises/{b}_16frames.pth",weights_only=False)
for b in ["O1","O2","O3"]:
    a,t=acc_ours(b); mk=z["block"]==b
    row={"ours_M1_acc_filtered_avg":a,"pairs":t,"ours_mean_score":float(sc[mk].mean()),"ours_sd_score":float(sc[mk].std(ddof=1))}
    for m in ["vit-l-rope-vm2m","vit-l-rope-howto","vit-h-rope-vm2m","vit-h-rope-howto"]:
        d=rel(m,b); L=d["losses"].numpy().astype(float); s=L.min(1).mean(1); l=d["labels"].numpy()
        acc=100*np.mean([s[2*k+(l[2*k]==0)]<s[2*k+(l[2*k]!=0)] for k in range(60)])
        row[m]={"acc":float(acc),"mean_score":float(s.mean()),"sd_score":float(s.std(ddof=1))}
    out[b]=row
json.dump(out,open(R+"verify/g1prime_a_agg.json","w"),indent=1); print(json.dumps(out,indent=1))
