import numpy as np
from pathlib import Path
from vjepa_study import schema
from vjepa_study.analysis import prereg as P
R=Path('results/raw')
D={'M1':schema.load_surprise(R/'p4_clean_m1/results/P4_M1_ipdev_clean_s1/surprise.npz'),
   'M2':schema.load_surprise(R/'p4_clean_m2/results/P4_M2_ipdev_clean_s1/surprise.npz')}
px=P.pair_index(D['M1']); pos,imp=px['pos'],px['imp']
np.set_printoptions(precision=3,suppress=True,linewidth=170)
def acc(sc): 
    t=P.tau_m(sc); return round(P.y_tiehalf(sc[imp],sc[pos],t).mean(),3)
for nm,d in D.items():
    print('=====',nm,'per block tiehalf', {b:round(float(P.y_tiehalf(P.video_scores(d,'S','mean')[imp],P.video_scores(d,'S','mean')[pos],P.tau_m(P.video_scores(d,'S','mean')))[px['block']==b].mean()),3) for b in np.unique(px['block'])})
    G=np.asarray(d['target_feats'],np.float32)[:, :17]  # 360,17,8,1024
    print('feat shape',G.shape,' pooled-feat L2 norm per tubelet mean',np.linalg.norm(G,axis=-1).mean(), ' mean |g|',np.abs(G).mean())
    S=np.stack([np.asarray(d['S'][i])[:17] for i in range(360)])
    # feature-space persistence baselines per C
    out={}
    for ci,c in enumerate((2,4,6,8,10)):
        k=c//2
        last=G[:,:,k-1:k,:]
        e=np.abs(G[:,:,k:,:]-last).mean((2,3))      # 360,17
        zero=np.abs(G[:,:,k:,:]).mean((2,3))
        out[c]=(e,zero)
    for c,(e,z) in out.items():
        sce=e.mean(1); scz=z.mean(1)
        ci=(2,4,6,8,10).index(c)
        sS=S[:,:,ci].mean(1)
        print(f' C={c:2d} featPersistence acc {acc(sce)}  featNorm acc {acc(scz)}  corr(S,persist) {np.corrcoef(sS,sce)[0,1]:.2f} corr(S,norm) {np.corrcoef(sS,scz)[0,1]:.2f}  S-acc {acc(sS)}')
    # pooled-feature norm over time: is there a systematic shift for possible vs impossible?
    sn=np.linalg.norm(G,axis=-1).mean((1,2))
    print(' pooled feature norm acc(imp>pos)',acc(sn))
    # per-video min-over-C vs mean-over-C with variance across windows
    sS=S.min(2).mean(1)
    print(' corr S with pooled-norm', np.corrcoef(sS,sn)[0,1])
    # per pair: do pos/imp share prefix windows? count windows with exactly equal S
    eq=(np.abs(S.min(2)[imp]-S.min(2)[pos])<1e-4).sum(1)
    print(' windows tied (<1e-4) per pair: mean',eq.mean())
    # post-divergence mean diff: windows after first non-tied window
    diffs=[];
    for p in range(len(pos)):
        dw=np.abs(S.min(2)[imp[p]]-S.min(2)[pos[p]])>1e-4
        if dw.any():
            f=dw.argmax(); diffs.append((S.min(2)[imp[p],f:]-S.min(2)[pos[p],f:]).mean())
    diffs=np.array(diffs); print(' post-divergence mean S(imp)-S(pos): mean',diffs.mean(),' frac>0',(diffs>0).mean(),'n',len(diffs))
    # per-C post-divergence frac>0
    for ci,c in enumerate((2,4,6,8,10)):
        fr=[]
        for p in range(len(pos)):
            a=S[imp[p],:,ci]-S[pos[p],:,ci]; dw=np.abs(a)>1e-4
            if dw.any(): fr.append(a[dw.argmax():].mean()>0)
        print('   C',c,'post-div frac imp>pos',np.mean(fr))
# cross: pair-level agreement between M2 acc verdict and B3(M2)
s2=P.video_scores(D['M2'],'S','mean'); b3=P.video_scores(D['M2'],'B3','mean')
print('M2 S verdict vs B3 verdict agreement', np.mean((s2[imp]>s2[pos])==(b3[imp]>b3[pos])))
s1=P.video_scores(D['M1'],'S','mean')
print('M1 vs M2 S verdict agreement', np.mean((s1[imp]>s1[pos])==(s2[imp]>s2[pos])))
print('B3 M2 vs M1 verdict agreement', np.mean((P.video_scores(D['M1'],'B3','mean')[imp]>P.video_scores(D['M1'],'B3','mean')[pos])==(b3[imp]>b3[pos])))
# B3 per C
for nm,d in D.items():
    for ci,c in enumerate((2,4,6,8,10)):
        print(nm,'B3 C',c, acc(P.video_scores(d,'B3','mean',c_index=ci)), ' B1',acc(P.video_scores(d,'B1','mean',c_index=ci)))
