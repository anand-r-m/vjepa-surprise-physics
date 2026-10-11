import numpy as np, sys
from pathlib import Path
from vjepa_study import schema
from vjepa_study.analysis import prereg as P
R=Path('results/raw')
M1=schema.load_surprise(R/'p4_clean_m1/results/P4_M1_ipdev_clean_s1/surprise.npz')
M2=schema.load_surprise(R/'p4_clean_m2/results/P4_M2_ipdev_clean_s1/surprise.npz')
px=P.pair_index(M1); assert (P.pair_index(M2)['pos']==px['pos']).all()
pos,imp=px['pos'],px['imp']
def acc(sc,tau=None):
    tau=P.tau_m(sc) if tau is None else tau
    return P.y_tiehalf(sc[imp],sc[pos],tau).mean(), P.y_strict(sc[imp],sc[pos]).mean()
np.set_printoptions(precision=4,suppress=True,linewidth=160)
for nm,d in (('M1',M1),('M2',M2)):
    print('=====',nm)
    S=np.stack([np.asarray(d['S'][i])[:17] for i in range(360)])   # 360,17,5
    print('mean S per C col', S.mean((0,1)), ' sd between-video of per-video mean per C', S.mean(1).std(0))
    print('mean S per window (min over C)', S.min(2).mean(0))
    print('argmin over C histogram', np.bincount(S.argmin(2).ravel(),minlength=5), ' (fraction)', np.bincount(S.argmin(2).ravel(),minlength=5)/S[...,0].size)
    # monotone in C?
    print('frac (window) with S monotone increasing in C', (np.diff(S,axis=2)>0).all(2).mean(), ' decreasing', (np.diff(S,axis=2)<0).all(2).mean())
    print('within-video sd across windows (min-over-C), median', np.median(S.min(2).std(1)), ' between-video sd of mean', S.min(2).mean(1).std())
    for how in ('mean','max'):
        for c in [None,0,1,2,3,4]:
            sc=P.video_scores(d,'S',how,c_index=c)
            print(f'  acc {how} C={"min" if c is None else d["context_lengths"][c]}: tiehalf/strict', np.round(acc(sc),3))
    # also max over C and mean over C
    for nm2,f in (('meanC',lambda S:S.mean(2)),('maxC',lambda S:S.max(2))):
        sc=f(S).mean(1); print('  agg',nm2,'mean-window',np.round(acc(sc),3))
    # per-window pair accuracy (min over C)
    c=S.min(2)
    pw=[ (c[imp,w]>c[pos,w]).mean() for w in range(17)]
    print('per-window strict acc (imp>pos):', np.round(pw,2))
    # signed pair difference mean
    dmean=P.video_scores(d,'S','mean'); dd=dmean[imp]-dmean[pos]
    print('pair diff mean, sd, frac>0', dd.mean(), dd.std(), (dd>0).mean(), ' d/sd(S)', dd.mean()/dmean.std())
    for k in ('B1','B2','B3'):
        sc=P.video_scores(d,k,'mean'); print(' ',k,'acc',np.round(acc(sc),3),' corr(S,%s) across videos'%k, np.corrcoef(dmean,sc)[0,1])
        # per-pair corr of diffs
        dk=sc[imp]-sc[pos]; print('     corr of pair diffs S vs',k,np.corrcoef(dd,dk)[0,1])
    # corr with window-level
