import torch, numpy as np, json, itertools
R="/home/anand-r-m/Research & Dev/Vjepa/scratch_data/verify_released_raw/data_intphys/"
def stats(model):
    Ls=[];  # per block
    for b in ("O1","O2","O3"):
        d=torch.load(f"{R}{model}/intphys/raw_surprises/{b}_16frames.pth",weights_only=False)
        assert d["frame_step"]==2 and d["context_lengths"]==[2,4,6,8,10]
        Ls.append(d["losses"].numpy().astype(np.float64)); lab=d["labels"].numpy()
        # rows 2k,2k+1 are matched pairs (one real, one fake)
        assert all(lab[2*k]+lab[2*k+1]==1 for k in range(len(lab)//2))
    L=np.concatenate(Ls)            # [360,5,17]
    sc=L.min(1).mean(1)             # filtered (min over C), mean over windows -> per-video score
    medS=np.median(L); tau=2e-4*medS; tau_v=2e-4*np.median(sc)
    pm=np.abs(sc[0::2]-sc[1::2])    # 180 matched pairs
    allp=[]; 
    for i in range(3):
        s=sc[120*i:120*(i+1)]; allp.append(np.abs(s[:,None]-s[None,:])[np.triu_indices(120,1)])
    allp=np.concatenate(allp)
    return dict(n_videos=int(len(sc)),median_S=float(medS),tau=float(tau),tau_alt_median_score=float(tau_v),
      video_score_sd=float(sc.std(ddof=1)),video_score_mean=float(sc.mean()),
      sd_within_block_mean=float(np.mean([sc[120*i:120*(i+1)].std(ddof=1) for i in range(3)])),
      matched_pair_tie_rate=float((pm<tau).mean()),matched_pair_tie_count=int((pm<tau).sum()),
      allpair_within_block_tie_rate=float((allp<tau).mean()),median_matched_pair_absdiff=float(np.median(pm)))
out={"random":[stats(f"vit-l-rope-random-{i}") for i in range(20)],"vm2m":stats("vit-l-rope-vm2m")}
def agg(k): x=np.array([s[k] for s in out["random"]]); return dict(mean=float(x.mean()),min=float(x.min()),max=float(x.max()),sd_across_models=float(x.std(ddof=1)))
out["random_summary"]={k:agg(k) for k in out["random"][0]}
json.dump(out,open("/home/anand-r-m/Research & Dev/Vjepa/verify/tie_rate_random_vs_vm2m.json","w"),indent=1)
print(json.dumps(out["random_summary"],indent=1)); print(json.dumps(out["vm2m"],indent=1))
