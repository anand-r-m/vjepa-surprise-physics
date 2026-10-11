"""P6 verifier: independent pair / event-time computation from dev pixels (no src/ imports)."""
import numpy as np, json, glob, os, cv2, sys
D='kaggle/datasets/intphys-dev-npz'
RES=224
def rs(f, interp):
    return np.stack([cv2.resize(x,(RES,RES),interpolation=interp) for x in f]).astype(np.float32)/255.
out={}
Dts={}
interps={'area':cv2.INTER_AREA,'linear':cv2.INTER_LINEAR}
scenes=sorted({os.path.basename(p).rsplit('_',1)[0] for p in glob.glob(D+'/*.npz')})
for sc in scenes:
    vids={}
    for k in (1,2,3,4):
        z=np.load(f'{D}/{sc}_{k}.npz'); vids[k]=(z['frames'],bool(z['is_possible']))
    # first divergence frame per pair of videos
    def div(a,b):
        d=(vids[a][0]!=vids[b][0]).reshape(100,-1).any(1)
        return int(np.argmax(d)) if d.any() else 100
    dv={(a,b):div(a,b) for a in (1,2,3,4) for b in (1,2,3,4) if a<b}
    partner=max((2,3,4),key=lambda b:(dv[(1,b)],-b))  # latest divergence; tie -> lowest index
    ties=[b for b in (2,3,4) if dv[(1,b)]==dv[(1,partner)]]
    others=[b for b in (2,3,4) if b!=partner]
    pairs=[(1,partner),tuple(others)]
    blk=sc.split('_')[0]; s=sc.replace('_','/')
    for pi,(a,b) in enumerate(pairs):
        pid=f'{s}/p{pi}'
        # NB: pair index convention (p0 = pair containing video 1?) compared later with stored pair_id
        pos,imp=(a,b) if vids[a][1] else (b,a)
        ok=vids[a][1]!=vids[b][1]
        rec=dict(a=a,b=b,pos=pos,imp=imp,valid=bool(ok),div_ab=dv[tuple(sorted((a,b)))],tie_partner=len(ties)>1)
        for nm,ip in interps.items():
            P=rs(vids[pos][0],ip); V=rs(vids[imp][0],ip)
            d=np.abs(V-P)
            Dt=d.mean((1,2,3))
            rec['D_'+nm]=Dt.tolist()
            # violation support for retention: |v-p|>8/255 any channel? use max over channel mean? -> two readings
            if nm=='area':
                sup=(d.mean(3)>8/255)  # per-pixel channel-mean reading
                sup2=(d.max(3)>8/255)
                rec['sup_cm_any']=sup.any(0).sum()/ (RES*RES)
                np.save(f'verify/_cache_sup_{s.replace("/","_")}_{pi}.npy',np.stack([sup.any(0),sup2.any(0)]))
        out[pid]=rec
    print(sc,flush=True)
json.dump(out,open('verify/_cache_pairs_events_raw.json','w'))
