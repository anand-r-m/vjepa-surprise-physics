import json,math
mine=json.load(open('verify/p6_recompute.json'))
H1=json.load(open('results/analysis/h1/h1_M1.json')); H2=json.load(open('results/analysis/h2/h2.json')); H3=json.load(open('results/analysis/h3_final/h3_M1.json'))
CL=json.load(open('results/analysis/h1/clean.json'))['models']['M1']['mean']
rows=[]
def cmp(name,a,b,tol,kind='abs'):
    if a is None or b is None: rows.append((name,a,b,None,tol,'AMBIG')); return
    d=abs(a-b); rows.append((name,a,b,d,tol,'match' if d<=tol else 'MISMATCH'))
# clean
c=mine['clean_acc']['P4_M1_fp16']
cmp('clean fp16 tie-half',c['tiehalf'],CL['acc_tiehalf'],.001); cmp('clean fp16 strict',c['strict'],CL['acc_strict'],.001); cmp('clean fp16 ties',c['n_ties_tau'],CL['n_ties'],0); cmp('clean fp16 tau',c['tau'],CL['tau_used'],1e-7)
cmp('H1 eligibility fp32 tie-half',mine['clean_acc']['P2_M1_fp32']['tiehalf'],H1['eligibility_clean_acc_tiehalf'],.001)
cmp('H1 f0',mine['h1_dither']['f0_mean_flip'],H1['f0'],.001)
cmp('H1 tau',mine['clean_acc']['P4_M1_fp16']['tau'],H1['tau'],1e-7)
HK={'zoom':mine['h1']['alt_keep=stored_support_retention_crop']['zoom']}
for e in ('brightness','noise','blur','jpeg','zoom','hflip','fps_halve'):
    m=mine['h1']['primary_keep=cm_win_0.7'][e] if e!='zoom' else HK['zoom']; t=H1['per_edit'][e]
    cmp(f'H1 {e} n',m['n_pairs'],t['n'],0)
    cmp(f'H1 {e} dAcc',m['dacc'],t['dacc'],.001); cmp(f'H1 {e} flip',m['flip'],t['flip'],.001)
    cmp(f'H1 {e} flip-f0',m['flip_minus_f0'],t['excess'],.001)
    cmp(f'H1 {e} f0 (retained)',m['f0'],t['flip']-t['excess'],.001)
    cmp(f'H1 {e} dAcc CI lo',m['dacc_ci'][0],t['dacc_ci'][0],.01); cmp(f'H1 {e} dAcc CI hi',m['dacc_ci'][1],t['dacc_ci'][1],.01)
    cmp(f'H1 {e} p_dacc_cluster',m['p_dacc_cluster'],t['p_dacc_cluster'],.015); cmp(f'H1 {e} p_flip_cluster',m['p_flip_vs_floor'],t['p_flip_cluster'],.015)
    cmp(f'H1 {e} holm14 dacc',m['holm14_dacc'],t['holm_dacc_cluster'],.03); cmp(f'H1 {e} holm14 flip',m['holm14_flip'],t['holm_flip_cluster'],.03)
    cmp(f'H1 {e} sign p',m['p_sign'],t['sign']['p'],1e-6)
# zoom primary (my own retention) vs theirs
m=mine['h1']['primary_keep=cm_win_0.7']['zoom']; t=H1['per_edit']['zoom']
for k,tk in (('n_pairs','n'),('dacc','dacc'),('flip','flip')): rows.append((f'H1 zoom {k} (my own retention 110 pairs vs analysis 112)',m[k],t[tk],abs(m[k]-t[tk]),'-','info'))
# H2
Rk='R1b_stored_matches_t_on'; h=mine['h2'][Rk]; h1p=mine['h2']['R1_pixel_fb48']
for mod in ('M1','B1','B2'):
    cmp(f'H2 A {mod} (R1b stored t_on)',h['A_point'][mod],H2[mod]['A'],.002); cmp(f'H2 A {mod} (R1 pixel t_on)',h1p['A_point'][mod],H2[mod]['A'],.002)
    for ty,v in H2[mod]['per_type'].items(): cmp(f'H2 {mod} {ty} (R1b)',h['per_type_auroc'][mod][ty],v,.002)
    cmp(f'H2 A0 {mod}',h['A0'][mod]['A0'],H2[mod]['A0'],.001); cmp(f'H2 tau {mod}',mine['h2_tau_fullclip_max'][mod],H2[mod]['tau'],1e-9)
    cmp(f'H2 A CI lo {mod}',h['A_boot_ci'][mod][0],H2[mod]['A_ci'][0],.01); cmp(f'H2 A CI hi {mod}',h['A_boot_ci'][mod][1],H2[mod]['A_ci'][1],.01)
for k,dk in (('B1','D_B1'),('B2','D_B2')):
    cmp(f'H2 D_{k}',h['D'][k]['D'],H2[dk]['D'],.002); cmp(f'H2 D_{k} CI lo',h['D'][k]['ci'][0],H2[dk]['ci'][0],.01); cmp(f'H2 D_{k} CI hi',h['D'][k]['ci'][1],H2[dk]['ci'][1],.01)
    cmp(f'H2 p_{k}',h['D'][k]['p_onesided'],H2[dk]['p'],.0005); cmp(f'H2 Holm-2 {k}',h['D'][k]['holm2'],H2[dk]['p_holm'],.001)
rows.append(('H2 outcome','Not specific/Detection-limited',H2['outcome_M1'][0],None,'-','match' if 'Detection-limited' in H2['outcome_M1'][0] else 'MISMATCH'))
rows.append(('H2 n_excluded_late / fallback',(mine['h2']['R1_pixel_fb48']['n_excluded_late'],mine['h2_event_info']['n_fallback_mine'],mine['h2_event_info']['n_transient_mine']),(H2['n_excluded_late'],H2['descriptors'].get('n_fallback','n/a'),H2['descriptors']['n_transient']),None,'-','info'))
# H3
h3=mine['h3']
cmp('H3 vflip (a)',h3['vflip_a_ref_p']['det'],H3['a'],.001); cmp('H3 vflip (a) CI lo',h3['vflip_a_ref_p']['ci'][0],H3['a_ci'][0],.01); cmp('H3 vflip (a) CI hi',h3['vflip_a_ref_p']['ci'][1],H3['a_ci'][1],.01)
cmp('H3 vflip (b) hflip-ref',h3['vflip_b_ref_hflip']['det'],H3['b'],.001); cmp('H3 (b) CI lo',h3['vflip_b_ref_hflip']['ci'][0],H3['b_ci'][0],.01); cmp('H3 (b) CI hi',h3['vflip_b_ref_hflip']['ci'][1],H3['b_ci'][1],.01)
cmp('H3 M1-M0r vflip',h3['M1_minus_M0r_vflip']['diff'],H3['diff_m0r'],.001); cmp('H3 diff CI lo',h3['M1_minus_M0r_vflip']['ci'][0],H3['diff_m0r_ci'][0],.01); cmp('H3 diff CI hi',h3['M1_minus_M0r_vflip']['ci'][1],H3['diff_m0r_ci'][1],.01)
cmp('H3 reversal',h3['reversal_ref_p']['det'],H3['reversal_detection'],.001)
cmp('H3 pairwise vflip tiehalf',h3['pairwise_acc_vflip']['tiehalf'],H3['pairwise_acc_vflip']['tiehalf'],.001); cmp('H3 pairwise vflip strict',h3['pairwise_acc_vflip']['strict'],H3['pairwise_acc_vflip']['strict'],.001)
cmp('H3 pairwise rev tiehalf',h3['pairwise_acc_reversal']['tiehalf'],H3['pairwise_acc_time_reversal']['tiehalf'],.001); cmp('H3 pairwise rev strict',h3['pairwise_acc_reversal']['strict'],H3['pairwise_acc_time_reversal']['strict'],.001)
cmp('H3 tau',mine['h2_tau_fullclip_max']['M1'],H3['variant']['tau'],1e-9)
rows.append(('H3 G2 pass',mine['h3_G2']['pass_ge_0p8'],H3['g2'],None,'-','match' if mine['h3_G2']['pass_ge_0p8']==H3['g2'] else 'MISMATCH'))
# print + md
L=['# P6 comparison: verifier recompute vs results/analysis (written AFTER p6_recompute.*)\n','| quantity | verifier | analysis | abs diff | tol | status |','|---|---|---|---|---|---|']
def f(x): return f'{x:.5g}' if isinstance(x,float) else str(x)
for n,a,b,d,t,s in rows: L.append(f'| {n} | {f(a)} | {f(b)} | {"" if d is None else f(d)} | {t} | {s} |')
mm=[r for r in rows if r[5]=='MISMATCH']; L.append(f'\nTotal {len(rows)}; match {sum(r[5]=="match" for r in rows)}; MISMATCH {len(mm)}; info/ambiguous {sum(r[5] in ("info","AMBIG") for r in rows)}')
open('verify/p6_compare.md','w').write('\n'.join(L)); print('\n'.join(L[-1:])); 
for r in mm: print(r)
