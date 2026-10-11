"""CPU check: M2 surprise with mask_index 0 (the only trained mask token) vs 1 (wrapper default, zero vector).
Reuses the src wrapper unmodified; torch.load patched to mmap. Subset: pairs every STEP-th, windows WIN, C in CS."""
import sys, time, json, numpy as np, torch
from pathlib import Path
torch.set_num_threads(6)
_tl=torch.load
torch.load=lambda *a,**k: _tl(*a,**{**k,'mmap':True,'weights_only':False})
from vjepa_study import schema
from vjepa_study.analysis import prereg as P
from vjepa_study.models.m2_vjepa2 import M2VJEPA2
from vjepa_study.models import common
CK=sys.argv[1]; STEP=int(sys.argv[2]); OUT=sys.argv[3]
WIN=[14]; CS=[6]
R=Path('results/raw/p4_clean_m2/results/P4_M2_ipdev_clean_s1/surprise.npz')
d=schema.load_surprise(R); px=P.pair_index(d)
vid=np.asarray(d['video_ids']); Sst=np.stack([np.asarray(d['S'][i])[:17] for i in range(360)])
m=M2VJEPA2(CK,device='cpu',precision='fp32',mask_index=1,batch_windows=3)
root=Path('kaggle/datasets/intphys-dev-npz')
res={}
sel=list(range(0,len(px['pos']),STEP))
t0=time.time()
for n,p in enumerate(sel):
    for role in ('pos','imp'):
        i=int(px[role][p]); b,s,k=str(vid[i]).split('/')
        with np.load(root/f'{b}_{s}_{k}.npz') as z: fr=z['frames']
        sub,idx=common.sample(fr,2,16,2)
        x=common.preprocess(sub,256,m.device); W=common.make_windows(x,16,2)[WIN].contiguous()
        out={}
        with torch.no_grad():
            for mi in (0,1):
                m.mask_index=mi; h=None; arr=[]
                for c in CS:
                    l,h=m._window_losses(W,c,h); arr.append(l.float().numpy())
                out[mi]=np.stack(arr,1)   # (nWIN, nC)
        res[int(i)]=dict(idx1=out[1].tolist(),idx0=out[0].tolist(),stored=Sst[i][WIN][:,[2]].tolist())
    print(n,len(sel),round(time.time()-t0),flush=True)
    json.dump(dict(sel=sel,res=res,pos=px['pos'].tolist(),imp=px['imp'].tolist()),open(OUT,'w'))
