import json, numpy as np
j=json.load(open('notes/m2_audit/cpu_maskindex.json')); res=j['res']; pos=j['pos']; imp=j['imp']
n=0; a1=a0=0; r=[]
for p in j['sel']:
    P_,I_=str(pos[p]),str(imp[p])
    if P_ not in res or I_ not in res: continue
    n+=1
    for k,nm in (('idx1','i1'),('idx0','i0')):
        pass
    d1=res[I_]['idx1'][0][0]-res[P_]['idx1'][0][0]; d0=res[I_]['idx0'][0][0]-res[P_]['idx0'][0][0]
    a1+=d1>0; a0+=d0>0
    r.append((res[P_]['stored'][0][0],res[P_]['idx1'][0][0],res[P_]['idx0'][0][0],res[I_]['stored'][0][0],res[I_]['idx1'][0][0],res[I_]['idx0'][0][0]))
r=np.array(r)
print('pairs',n,' window14 C=6 imp>pos: idx1',a1,' idx0',a0)
print('mean S stored/idx1(fp32 CPU)/idx0 (pos):',r[:,0].mean(),r[:,1].mean(),r[:,2].mean(),' (imp):',r[:,3].mean(),r[:,4].mean(),r[:,5].mean())
print('max|stored-idx1| (fp16 vs fp32 repro):',np.abs(r[:,0]-r[:,1]).max(),np.abs(r[:,3]-r[:,4]).max())
