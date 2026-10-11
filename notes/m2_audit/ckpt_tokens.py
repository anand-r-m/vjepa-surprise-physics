import torch,sys
p=sys.argv[1]
sd=torch.load(p,map_location='cpu',mmap=True,weights_only=False)
print(sd.keys())
for k in ('predictor','encoder','target_encoder'):
    ks=list(sd[k].keys()); print(k,len(ks),ks[:3])
pr=sd['predictor']
for k,v in pr.items():
    if 'mask_token' in k: print(k,tuple(v.shape),'norm=%.5f'%v.float().norm(),'absmax=%.5f'%v.float().abs().max())
for k in sd:
    if k not in('predictor','encoder','target_encoder'): print(k, sd[k] if not hasattr(sd[k],'keys') else '...')
print([k for k in pr if 'pos_embed' in k])
