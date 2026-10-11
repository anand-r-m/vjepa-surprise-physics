import numpy as np
from pathlib import Path
from vjepa_study import schema
from vjepa_study.analysis import prereg as P
R=Path('results/raw')
np.set_printoptions(precision=3,suppress=True,linewidth=170)
for nm,p in (('M1','p4_clean_m1/results/P4_M1_ipdev_clean_s1'),('M2','p4_clean_m2/results/P4_M2_ipdev_clean_s1')):
    d=schema.load_surprise(R/p/'surprise.npz'); px=P.pair_index(d); pos,imp=px['pos'],px['imp']
    G=np.asarray(d['target_feats'],np.float32)[:,:17]
    ch=np.abs(G[:,:,1:]-G[:,:,:-1]).mean(-1)   # 360,17,7 change into tubelet j (1..7)
    print(nm,'frac imp>pos of feature change, by incoming tubelet j (mean over windows):',[round(float((ch[imp,:,j].mean(1)>ch[pos,:,j].mean(1)).mean()),2) for j in range(7)])
    print(nm,'by window (mean over tubelets):',[round(float((ch[imp,w].mean(1)>ch[pos,w].mean(1)).mean()),2) for w in range(17)])
    print(nm,'mean change magnitude by tubelet j',ch.mean((0,1)))
    # pixel-level: global time-mean pooled feature drift
    pn=np.linalg.norm(G,axis=-1)  # 360,17,8
    print(nm,'pooled norm by tubelet',pn.mean((0,1)))
    # does feature change correlate with B1 (pixel change) across videos?
    b1=P.video_scores(d,'B1','mean'); b3=P.video_scores(d,'B3','mean'); print(nm,'corr(B1,B3) videos',np.corrcoef(b1,b3)[0,1],' pair-diff corr',np.corrcoef(b1[imp]-b1[pos],b3[imp]-b3[pos])[0,1])
    # per-block B3 accuracy
    y=(b3[imp]>b3[pos]); print(nm,'B3 imp>pos by block',{b:round(float(y[px['block']==b].mean()),2) for b in np.unique(px['block'])})
