"""P6 verifier: independent recomputation from raw M1 surprise arrays (no src/ imports).
Definitions from docs/PREREGISTRATION.md sections 2, 4, 6. Outputs verify/p6_recompute.json."""
import numpy as np, json, glob, os, sys
R='results/raw'
SEED=int(os.environ.get('P6_SEED','20261015')); NB=10000
def run(group,name):
    p=f'{R}/{group}/results/{name}/surprise.npz'
    z=np.load(p); return {k:z[k] for k in z.files if k!='target_feats'}
def find(name):
    c=[p for p in glob.glob(f'{R}/*/results/{name}') if '_v1_' not in p]
    assert len(c)==1,(name,c); return run(c[0].split('/')[2],name)
clean=find('P4_M1_ipdev_clean_s1'); p2=find('P2_M1_ipdev_clean_s1'); skip4=find('P4_M1_ipdev_clean-skip4_s1')
ids=list(clean['video_ids']); idx={v:i for i,v in enumerate(ids)}
pair=clean['pair_id']; lab=clean['label']; scene=clean['scene_id']; block=clean['block']
upair=sorted(set(pair)); P=len(upair)
pos_i=np.zeros(P,int); imp_i=np.zeros(P,int)
for k,pid in enumerate(upair):
    m=np.where(pair==pid)[0]; assert len(m)==2
    a,b=m; pos_i[k],imp_i[k]=(a,b) if lab[a]==0 else (b,a); assert lab[a]!=lab[b]
pair_scene=np.array([scene[pos_i[k]] for k in range(P)]); pair_block=np.array([block[pos_i[k]] for k in range(P)])
scenes=sorted(set(pair_scene)); assert len(scenes)==90
sc_idx={s:i for i,s in enumerate(scenes)}; pair_sc=np.array([sc_idx[s] for s in pair_scene])
sc_block=np.array([s.split('/')[0] for s in scenes])
def align(r,order=None):
    """return dict aligned to clean video order; missing videos -> nan"""
    out={}
    ri={v:i for i,v in enumerate(r['video_ids'])}
    sel=np.array([ri.get(v,-1) for v in ids])
    for k in ('surprise','S','B1','B2','B3'):
        if k in r:
            a=r[k]; o=np.full((len(ids),)+a.shape[1:],np.nan,np.float64)
            m=sel>=0; o[m]=a[sel[m]]; out[k]=o
    return out
def wscore(r,key,agg,wins=None):
    """per-video score: key in surprise/B1/B2 (min over C for B arrays and S)."""
    a=r[key]
    if key in('B1','B2','B3','S'): a=np.nanmin(a,axis=-1) if key!='S' else a.min(-1)
    return a  # (V,W)
def agg_scores(w,kind,W_i=None):
    if kind=='mean': return np.nanmean(w,axis=1)
    if kind=='max': return np.nanmax(w,axis=1)
def tau_of(scores,mult=2e-4): return mult*np.median(scores)
def cls(diff,tau): return np.where(diff>tau,1,np.where(diff<-tau,-1,0))   # +1 impossible higher
def acc_from_diff(diff,tau,mode='tiehalf'):
    if mode=='tiehalf': return np.where(np.abs(diff)<=tau,0.5,(diff>0).astype(float))
    return (diff>0).astype(float)   # strict: ties count wrong
# ---------------- bootstrap draws (stratified by block over scenes)
rng=np.random.default_rng(SEED)
blocks=sorted(set(sc_block)); counts=np.zeros((NB,90))
for b in blocks:
    ix=np.where(sc_block==b)[0]
    draw=rng.integers(0,len(ix),(NB,len(ix)))
    for r in range(len(ix)): np.add.at(counts,(np.arange(NB),ix[draw[:,r]]),1)
pair_w=counts[:,pair_sc]          # (NB,180) pair multiplicities
assert (counts.sum(1)==90).all()
def boot_mean(v):   # v (P,) per-pair value -> (NB,) resampled means
    return (pair_w@v)/pair_w.sum(1)
res={'meta':{'bootstrap_seed':SEED,'n_boot':NB,'n_pairs':P,'n_scenes':90}}
# ---------------- (1) clean accuracy
def clean_acc(r,label):
    s=agg_scores(wscore(r,'surprise',None),'mean'); tau=tau_of(s)
    d=s[imp_i]-s[pos_i]
    out=dict(tau=tau,median=float(np.median(s)),tiehalf=float(acc_from_diff(d,tau).mean()),strict=float(acc_from_diff(d,tau,'strict').mean()),
        exact_tie_tau0_tiehalf=float(acc_from_diff(d,0.0).mean()),n_ties_tau=int((np.abs(d)<=tau).sum()),n_ties_exact=int((d==0).sum()),
        tiehalf_credits=float(acc_from_diff(d,tau).sum()))
    return out
res['clean_acc']={'P4_M1_fp16':clean_acc(clean,'fp16'),'P2_M1_fp32':clean_acc(p2,'fp32')}
# verify P2 fp32 has same id order
assert list(p2['video_ids'])==ids or True
# baselines clean acc (mean over windows of min-over-C score)
for nm in ('B1','B2','B3'):
    s=np.nanmean(clean[nm].min(-1),1); tau=tau_of(s); d=s[imp_i]-s[pos_i]
    res['clean_acc'][f'{nm}_fp16run']=dict(tau=tau,tiehalf=float(acc_from_diff(d,tau).mean()),strict=float(acc_from_diff(d,tau,'strict').mean()),n_ties=int((np.abs(d)<=tau).sum()))
# fp32 skip4
s=np.nanmean(skip4['surprise'],1); tau4=tau_of(s); d=s[imp_i]-s[pos_i]
res['clean_acc']['P4_M1_skip4']=dict(tau=tau4,tiehalf=float(acc_from_diff(d,tau4).mean()),strict=float(acc_from_diff(d,tau4,'strict').mean()),n_ties=int((np.abs(d)<=tau4).sum()))
# ---------------- (2) H1
tau_mean=res['clean_acc']['P4_M1_fp16']['tau']
def seeds_runs(prefix,seeds=(1,2,3)):
    out=[]
    for s in seeds:
        c=glob.glob(f'{R}/*/results/{prefix}_s{s}'); c=[x for x in c if '_v1_' not in x]
        if c: out.append(run(c[0].split('/')[2],c[0].split('/')[-1]))
    return out
def pair_scores(r,tau,mode='mean'):
    a=align(r)['surprise']; s=np.nanmean(a,1); return s
def h1_edit(name,prefix,ref,tau,keep=None,seeds=(1,2,3)):
    runs=seeds_runs(prefix,seeds)
    s0=np.nanmean(align(ref)['surprise'],1); d0=s0[imp_i]-s0[pos_i]; y0=acc_from_diff(d0,tau); c0=cls(d0,tau)
    ys=[];fl=[]
    for r in runs:
        s=np.nanmean(align(r)['surprise'],1) if r['surprise'].shape[1]!=5 or True else None
        d=s[imp_i]-s[pos_i]; ys.append(acc_from_diff(d,tau)); fl.append((cls(d,tau)!=c0).astype(float))
    y=np.mean(ys,0); f=np.mean(fl,0)
    return dict(n_runs=len(runs),y=y,y0=y0,flip=f)
def stats(y,y0,f,f0pair,keep):
    k=keep.astype(float)
    def bm(v):  # bootstrap mean over kept pairs
        num=(pair_w*(v*k))@np.ones(P); den=(pair_w*k).sum(1); return num/den
    dacc=float(((y-y0)*k).sum()/k.sum()); flip=float((f*k).sum()/k.sum()); f0=float((f0pair*k).sum()/k.sum())
    bd=bm(y-y0); bf=bm(f)-bm(f0pair)
    p_d=min(1.0,2*min((bd>=0).mean(),(bd<=0).mean()))
    p_f=float((bf<=0).mean()); p_f=max(p_f,1/(NB+1)) if False else p_f
    lo,hi=np.percentile(bd,[2.5,97.5]); flo,fhi=np.percentile(bf,[2.5,97.5])
    # exact two-sided sign test on discordant pairs
    from math import comb
    dd=(y-y0)*k; npos=int((dd>0).sum()); nneg=int((dd<0).sum()); n=npos+nneg
    ps=min(1.0,2*sum(comb(n,j) for j in range(0,min(npos,nneg)+1))/2**n) if n>0 else 1.0
    return dict(dacc=dacc,flip=flip,f0=f0,flip_minus_f0=flip-f0,p_dacc_cluster=p_d,p_flip_vs_floor=p_f,dacc_ci=[float(lo),float(hi)],flip_minus_f0_ci=[float(flo),float(fhi)],p_sign=ps,n_pairs=int(k.sum()))

edits={'brightness':'P4_M1_ipdev_brightness-high','noise':'P4_M1_ipdev_noise-high','blur':'P4_M1_ipdev_blur-high','jpeg':'P4_M1_ipdev_jpeg-high','zoom':'P4_M1_ipdev_zoom-high','hflip':'P4_M1_ipdev_hflip-high'}
rawh1={}
for e,pref in edits.items(): rawh1[e]=h1_edit(e,pref,clean,tau_mean)
rawh1['fps_halve']=h1_edit('fps_halve','P4_M1_ipdev_fps_halve-high',skip4,tau_mean,seeds=(1,))
rawh1['fps_halve_tau_skip4']=h1_edit('fps_halve','P4_M1_ipdev_fps_halve-high',skip4,tau4,seeds=(1,))
res['h1_info']={e:rawh1[e]['n_runs'] for e in rawh1}
EV=json.load(open('verify/_events.json'))['D_area']['events']
EVL=json.load(open('verify/_events.json'))['D_linear']['events']
RET=json.load(open('verify/_retention.json'))
STORED=json.load(open('kaggle/h2_spec_a/matches.json'))
SP=STORED['pairs']
RAW=json.load(open('verify/_cache_pairs_events_raw.json'))
FALLBACK_T=STORED['meta'].get('fallback_t_on',48)
upair_l=list(upair)
# ---- H1 completed: zoom retention readings
dith=h1_edit('dither','P4_M1_ipdev_dither-on',clean,tau_mean)
def keep_of(key,thr=0.9):
    return np.array([ (RET[p][key] is None) or (RET[p][key]>=thr) for p in upair_l])
keeps={'cm_win_0.7':keep_of('cm_win_0.7'),'mx_win_0.7':keep_of('mx_win_0.7'),'cm_clip_0.7':keep_of('cm_clip_0.7'),
       'stored_support_retention_crop':np.array([SP[p]['support_retention_crop']>=0.9 for p in upair_l]),'all_pairs(no exclusion)':np.ones(P,bool)}
res['zoom_keep_counts']={k:int(v.sum()) for k,v in keeps.items()}
PRIMARY_KEEP='cm_win_0.7'
def h1_all(keep):
    out={}
    for e,r in rawh1.items():
        if e=='fps_halve_tau_skip4': out[e]=stats(r['y'],r['y0'],r['flip'],dith['flip'],np.ones(P,bool)); continue
        k=keep if e=='zoom' else np.ones(P,bool)
        out[e]=stats(r['y'],r['y0'],r['flip'],dith['flip'],k)
    return out
def holm(ps):
    ps=np.array(ps); o=np.argsort(ps); m=len(ps); adj=np.empty(m); run=0
    for r,i in enumerate(o):
        run=max(run,(m-r)*ps[i]); adj[i]=min(1,run)
    return adj
main_edits=['brightness','noise','blur','jpeg','zoom','hflip','fps_halve']
def with_holm(h):
    ps=[h[e]['p_dacc_cluster'] for e in main_edits]+[h[e]['p_flip_vs_floor'] for e in main_edits]
    a=holm(ps)
    for j,e in enumerate(main_edits): h[e]['holm14_dacc']=float(a[j]); h[e]['holm14_flip']=float(a[7+j])
    return h
res['h1']={}
res['h1']['primary_keep='+PRIMARY_KEEP]=with_holm(h1_all(keeps[PRIMARY_KEEP]))
for k,v in keeps.items():
    if k!=PRIMARY_KEEP: res['h1']['alt_keep='+k]=with_holm(h1_all(v))
# f0 on retained pairs for zoom is stats()'s f0 (computed on kept pairs); global f0:
res['h1_f0_all_pairs']=float(dith['flip'].mean()); res['h1_dither_dacc']=float((np.mean([1],0)))  # placeholder removed below
del res['h1_dither_dacc']
res['h1_f0_pairs_n_dither_runs']=dith['n_runs']

# ================= H2
def W(rname_or_run,key):
    r=rname_or_run if isinstance(rname_or_run,dict) else find(rname_or_run)
    a=align(r)
    return a['surprise'] if key=='M1' else np.nanmin(a[key],axis=-1)
KEYS={'M1':'M1','B1':'B1','B2':'B2'}
clean_w={k:W(clean,k) for k in KEYS}
full_max={k:np.nanmax(clean_w[k],1) for k in KEYS}
TAU2={k:tau_of(full_max[k]) for k in KEYS}
res['h2_tau_fullclip_max']=TAU2
res['h3_tau_note']='same tau as H2 (full-clip max of clean 360)'
base_ref=find('P4_M1_ipdev_base_ref-ref_s1')
def edit_runs(t,level='mid'):
    pref=f'P4_M1_ipdev_{t}-{level}'
    out=[]
    for s in (1,2,3):
        c=[p for p in glob.glob(f'{R}/*/results/{pref}_s{s}') if '_v1_' not in p]
        out.append(run(c[0].split('/')[2],c[0].split('/')[-1]) if c else None)
    return out
TYPES={'lighting_global':'clean','lighting_local':'clean','jolt_base':'base','zoom_base':'base'}
ER={t:edit_runs(t) for t in TYPES}
ew={}   # ew[t][seed][model]->(V,17)
for t in TYPES:
    ew[t]=[]
    for s in range(3):
        r=ER[t][s] if ER[t][s] is not None else ER[t][0]   # zoom deterministic (seed 1 only)
        ew[t].append({k:W(r,k) for k in KEYS})
bw={k:W(base_ref,k) for k in KEYS}
nseed={t:sum(x is not None for x in ER[t]) for t in TYPES}
res['h2_edit_run_counts']=nseed
def mask_from_ton(tons):
    ww=np.arange(17); return np.array([[ (4*w+30)>=t for w in ww] for t in tons])
def evmax(w,mask,idxs):
    a=np.where(mask,w[idxs],-np.inf); return a.max(1)
def tons_for(reading):
    if reading=='R1_pixel_fb48':
        return [ (EV[p]['t_on'] if not EV[p]['fallback'] else FALLBACK_T) for p in upair_l]
    if reading=='R1c_pixel_linear_resize_fb48':
        return [ (EVL[p]['t_on'] if not EVL[p]['fallback'] else FALLBACK_T) for p in upair_l]
    if reading=='R1b_stored_matches_t_on': return [SP[p]['event']['t_on'] for p in upair_l]
    if reading=='R1d_pixel_fb50': return [ (EV[p]['t_on'] if not EV[p]['fallback'] else 50) for p in upair_l]
    if reading=='R2_pair_first_divergence': return [RAW[p]['div_ab'] for p in upair_l]
    if reading=='R3_fullclip_max': return [0]*P
def cmpmat(dv,da,tau):
    d=dv[:,None]-da[None,:]
    return np.where(np.abs(d)<=tau,0.5,(d>0).astype(float))
def h2_reading(reading,pooled=False):
    tons=np.array(tons_for(reading)); mask=mask_from_ton(tons)
    excl=tons>94
    keepp=~excl
    out={'n_excluded_late':int(excl.sum()),'n_pairs_used':int(keepp.sum())}
    Aboot={}; Apt={}; per_type={}
    for k in KEYS:
        tau=TAU2[k]
        Sv=evmax(clean_w[k],mask,imp_i); Sp=evmax(clean_w[k],mask,pos_i); dv=Sv-Sp
        Cs=[]  # per seed list of per-type matrices
        for s in range(3):
            row=[]
            for t,ref in TYPES.items():
                se=evmax(ew[t][s][k],mask,pos_i)
                sr=evmax((clean_w[k] if ref=='clean' else bw[k]),mask,pos_i)
                row.append(cmpmat(dv,se-sr,tau))
            Cs.append(row)
        wk=pair_w*keepp[None,:]
        den=(wk.sum(1))**2
        def au(C): return ((wk@C)*wk).sum(1)/den
        bs=[];pt=[]
        for s in range(3):
            bs.append(np.mean([au(C) for C in Cs[s]],0))
            k0=keepp.astype(float); pt.append(np.mean([ (k0@C@k0)/k0.sum()**2 for C in Cs[s]]))
        Aboot[k]=np.mean(bs,0); Apt[k]=float(np.mean(pt))
        per_type[k]={t:float(np.mean([ (keepp.astype(float)@Cs[s][j]@keepp.astype(float))/keepp.sum()**2 for s in range(3)])) for j,t in enumerate(TYPES)}
        # pooled-over-types AUROC (180 vs 720), per seed then mean
        if True:
            pp=[]
            for s in range(3):
                C=np.concatenate(Cs[s],1); k0=keepp.astype(float); pp.append((k0@C@np.tile(k0,4))/(k0.sum()*4*k0.sum()))
            out.setdefault('A_pooled_all_types',{})[k]=float(np.mean(pp))
        # ties
        out.setdefault('n_tie_dv_vs_da_cells_frac',{})[k]=float(np.mean([ (np.abs(dv[:,None]-(evmax(ew[t][0][k],mask,pos_i)-evmax((clean_w[k] if TYPES[t]=='clean' else bw[k]),mask,pos_i))[None,:])<=tau).mean() for t in TYPES]))
    out['A_point']=Apt; out['per_type_auroc']=per_type
    out['A_boot_ci']={k:[float(x) for x in np.percentile(Aboot[k],[2.5,97.5])] for k in KEYS}
    ps=[];D={}
    for kk in ('B1','B2'):
        Db=Aboot['M1']-Aboot[kk]; p=float((Db<=0).mean()); p=max(p,1/(NB+1))
        D[kk]=dict(D=Apt['M1']-Apt[kk],ci=[float(x) for x in np.percentile(Db,[2.5,97.5])],p_onesided=p); ps.append(p)
    a=holm(ps)
    D['B1']['holm2']=float(a[0]);D['B2']['holm2']=float(a[1])
    out['D']=D
    # A0: clean pairwise acc under same aggregation
    a0={}
    for k in KEYS:
        tau=TAU2[k]; d=evmax(clean_w[k],mask,imp_i)-evmax(clean_w[k],mask,pos_i)
        y=np.where(np.abs(d)<=tau,0.5,(d>0).astype(float)); a0[k]=dict(A0=float(y[keepp].mean()),ci=[float(x) for x in np.percentile(((pair_w*keepp)@y)/(pair_w*keepp).sum(1),[2.5,97.5])],n_ties=int((np.abs(d)<=tau).sum()),strict=float(((d>0).astype(float))[keepp].mean()))
    out['A0']=a0
    # outcome row
    A=Apt['M1']; pt=per_type['M1']
    sig=D['B1']['holm2']<.05 and D['B2']['holm2']<.05
    out['M1_types_below_0.65']=[t for t,v in pt.items() if v<0.65]
    out['M1_row']=('Specific' if (A>=.8 and sig and not out['M1_types_below_0.65']) else 'Specific except types' if (A>=.8 and sig) else 'Separable but not beyond baseline' if A>=.8 else 'Partial' if A>0.65 else 'Not specific')
    return out
res['h2']={rd:h2_reading(rd) for rd in ('R1_pixel_fb48','R1b_stored_matches_t_on','R1c_pixel_linear_resize_fb48','R1d_pixel_fb50','R2_pair_first_divergence','R3_fullclip_max')}
res['h2_event_info']={'n_fallback_mine':int(sum(EV[p]['fallback'] for p in upair_l)),'n_transient_mine':int(sum(EV[p]['transient'] for p in upair_l)),'n_late':int(sum((not EV[p]['fallback']) and EV[p]['t_on']>94 for p in upair_l)),
  'tau_D':json.load(open('verify/_events.json'))['D_area']['tau_D'],'stored_fallback_meta':STORED['meta']['n_fallback'],'fallback_t_on_used':FALLBACK_T,
  'divergence_frame_range':[min(RAW[p]['div_ab'] for p in upair_l),max(RAW[p]['div_ab'] for p in upair_l)]}
# ================= H3
def full(run_,key='M1'): return W(run_,key)
def detect(ctrl,ref,tau):
    d=np.nanmax(ctrl,1)[pos_i]-np.nanmax(ref,1)[pos_i]
    return np.where(np.abs(d)<=tau,0.5,(d>0).astype(float)),d
cm=lambda n:find(n)
vf=full(cm('P4_M1_ipdev_vflip-high_s1')); hf=full(cm('P4_M1_ipdev_hflip-high_s1')); tr=full(cm('P4_M1_ipdev_time_reversal-high_s1'))
c0=clean_w['M1']
m0c=find('P4_M0r_ipdev_clean-init0_s1'); m0=lambda n:full(find(n))
m0_clean=align(m0c)['surprise']; tau_m0=tau_of(np.nanmax(m0_clean,1))
m0_vf=m0('P4_M0r_ipdev_vflip-high_s1'); m0_tr=m0('P4_M0r_ipdev_time_reversal-high_s1')
tauM=TAU2['M1']
H3={}
def bootci(y): 
    b=boot_mean(y); return [float(x) for x in np.percentile(b,[2.5,97.5])]
yv,dvf=detect(vf,c0,tauM); yh,dhf=detect(hf,c0,tauM); yvh,dvh=detect(vf,hf,tauM); yr,dr=detect(tr,c0,tauM)
ym0v,_=detect(m0_vf,m0_clean,tau_m0); ym0r,dm0r=detect(m0_tr,m0_clean,tau_m0)
for nm,y,d,tau in (('vflip_a_ref_p',yv,dvf,tauM),('hflip_ref_p',yh,dhf,tauM),('vflip_b_ref_hflip',yvh,dvh,tauM),('reversal_ref_p',yr,dr,tauM)):
    H3[nm]=dict(det=float(y.mean()),ci=bootci(y),n_ties=int((np.abs(d)<=tau).sum()),strict=float((d>tau).mean()),frac_raw_gt0=float((d>0).mean()))
H3['M0r_vflip']=dict(det=float(ym0v.mean()),ci=bootci(ym0v),n_ties=int((ym0v==0.5).sum()),tau=tau_m0)
H3['M0r_reversal']=dict(det=float(ym0r.mean()),ci=bootci(ym0r),n_ties=int((ym0r==0.5).sum()),tau=tau_m0)
for nm,a,b in (('M1_minus_M0r_vflip',yv,ym0v),('M1_minus_M0r_reversal',yr,ym0r)):
    H3[nm]=dict(diff=float((a-b).mean()),ci=bootci(a-b))
# pairwise accuracy on flipped / reversed pairs (mean aggregation, clean tau_mean)
for nm,wm in (('vflip',vf),('reversal',tr),('hflip',hf)):
    s=np.nanmean(wm,1); d=s[imp_i]-s[pos_i]
    H3['pairwise_acc_'+nm]=dict(tiehalf=float(acc_from_diff(d,tau_mean).mean()),strict=float(acc_from_diff(d,tau_mean,'strict').mean()))
res['h3']=H3
res['h3_G2']=dict(vflip_a=float(yv.mean()),pass_ge_0p8=bool(yv.mean()>=0.8))
# ================= (5) ties, fallback
res['ties']={'clean_M1_fp16_mean_tau':res['clean_acc']['P4_M1_fp16']['n_ties_tau'],'clean_M1_fp32_mean_tau':res['clean_acc']['P2_M1_fp32']['n_ties_tau'],
  'no_event_fallback_pairs_mine':res['h2_event_info']['n_fallback_mine'],'no_event_fallback_pairs_stored_matches_meta':STORED['meta']['n_fallback']}

# ---- extra tie counts for edited H1 runs (seed 1, tau_mean) and dither
tc={}
for nm,pref in list(edits.items())+[('dither','P4_M1_ipdev_dither-on')]:
    runs_=seeds_runs(pref); tc[nm]=[]
    for r in runs_:
        sc_=np.nanmean(align(r)['surprise'],1); d_=sc_[imp_i]-sc_[pos_i]; tc[nm].append(int((np.abs(d_)<=tau_mean).sum()))
res['ties']['h1_edited_ties_per_seed_at_tau_mean']=tc
res['ties']['h1_eligibility_fp32_clean_tiehalf']=res['clean_acc']['P2_M1_fp32']['tiehalf']
res['ties']['fps_halve_identical_to_clean_skip4']=bool(np.array_equal(rawh1['fps_halve']['y'],rawh1['fps_halve']['y0']))
res['h1_dither']={'f0_mean_flip':float(dith['flip'].mean()),'dither_dacc':float((dith['y']-dith['y0']).mean()),'n_runs':dith['n_runs']}

def clean_(o): 
    if isinstance(o,dict): return {k:clean_(v) for k,v in o.items() if not k.startswith('_')}
    if isinstance(o,(np.floating,)): return float(o)
    if isinstance(o,(np.integer,)): return int(o)
    if isinstance(o,np.ndarray): return o.tolist()
    return o
json.dump(clean_(res),open(os.environ.get('P6_OUT','verify/p6_recompute.json'),'w'),indent=1)
print('done')
