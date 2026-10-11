"""P6 verifier: event times (prereg sec 4) and crop retention, from dev pixels. Writes verify/_events.json"""
import numpy as np, json, os, cv2, glob
D='kaggle/datasets/intphys-dev-npz'; RES=224; T=100
raw=json.load(open('verify/_cache_pairs_events_raw.json'))
out={'pairs':{}}
def events(key):
    pids=sorted(raw)
    Dm=np.array([raw[p][key] for p in pids])           # (180,100)
    first10=Dm[:,:10].ravel()
    tauD=max(2/255,float(np.percentile(first10,99.9)))
    ev={}
    for p,d in zip(pids,Dm):
        above=np.where(d>tauD)[0]
        if len(above)==0: ev[p]=dict(t_on=None,t_off=None,fallback=True,transient=False); continue
        ton=int(above[0]); toff=T
        # last run of >=5 consecutive frames with D<=tauD after t_on, before T
        run_start=None; best=None; i=ton+1
        while i<T:
            if d[i]<=tauD:
                j=i
                while j<T and d[j]<=tauD: j+=1
                if j-i>=5: best=i
                i=j
            else: i+=1
        if best is not None: toff=best
        ev[p]=dict(t_on=ton,t_off=toff,fallback=False,transient=toff<T)
    return tauD,ev
res={}
for key in ('D_area','D_linear'):
    tauD,ev=events(key)
    res[key]=dict(tau_D=tauD,n_fallback=sum(e['fallback'] for e in ev.values()),n_transient=sum(e['transient'] for e in ev.values()),
        n_late=sum((e['t_on'] is not None and e['t_on']>94) for e in ev.values()),events=ev,
        Dmax_median=float(np.median([max(raw[p][key]) for p in raw])),Dmax_max=float(max(max(raw[p][key]) for p in raw)))
json.dump(res,open('verify/_events.json','w'))
for k,v in res.items(): print(k,{a:b for a,b in v.items() if a!='events'})
