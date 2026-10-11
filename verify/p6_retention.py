import numpy as np, json, os, cv2
D='kaggle/datasets/intphys-dev-npz'; RES=224
raw=json.load(open('verify/_cache_pairs_events_raw.json')); ev=json.load(open('verify/_events.json'))['D_area']['events']
st=json.load(open('kaggle/h2_spec_a/matches.json'))['pairs']
def rs(f): return np.stack([cv2.resize(x,(RES,RES),interpolation=cv2.INTER_AREA) for x in f]).astype(np.float32)/255.
out={}
cache={}
for pid in sorted(raw):
    sc=pid.rsplit('/',1)[0].replace('/','_'); r=raw[pid]
    P=rs(np.load(f'{D}/{sc}_{r["pos"]}.npz')['frames']); V=rs(np.load(f'{D}/{sc}_{r["imp"]}.npz')['frames'])
    d=np.abs(V-P)
    ton,toff=(ev[pid]['t_on'],ev[pid]['t_off']) if not ev[pid]['fallback'] else (48,100)
    rec={}
    for nm,dd in (('cm',d.mean(3)),('mx',d.max(3))):
        for wn,(a,b) in (('win',(ton,toff)),('clip',(0,100))):
            sup=(dd[a:b]>8/255).any(0)
            n=sup.sum()
            for s in (0.9,0.8,0.7):
                lo=int(round((1-s)/2*RES)); hi=RES-lo
                inside=sup[lo:hi,lo:hi].sum()
                rec[f'{nm}_{wn}_{s}']=float(inside/n) if n>0 else None
            rec[f'{nm}_{wn}_area']=float(n/RES**2)
    out[pid]=rec
    print(pid,flush=True) if pid.endswith('p0') and pid.split('/')[1]=='01' else None
json.dump(out,open('verify/_retention.json','w'))
