"""Peak-window variant: native-frame containment (4w <= s <= 4w+30), any switch. Appends to verify/p10_recompute.json."""
import sys, json; sys.path.insert(0, 'verify')
import numpy as np
exec(open('verify/p10_recompute.py').read().split('# ------------------------------------------------ (6)')[0].replace("json.dump(res, open('verify/p10_recompute.json', 'w'), indent=1)", ''))
out = {}
for role, ix in (('imp', imp_i), ('pos', pos_i)):
    for key in ('surprise', 'B1', 'B2'):
        a = clean1[key]; a = a if key == 'surprise' else np.nanmin(a, -1)
        hit = []; ch = []
        for k in range(P):
            sw = spl[ids[imp_i[k]]]['switches']; w = int(np.nanargmax(a[ix[k]]))
            cov = lambda ww: any(4 * ww <= s <= 4 * ww + 30 for s in sw)
            hit.append(cov(w)); ch.append(np.mean([cov(ww) for ww in range(17)]))
        out[f'{role}_{key}'] = dict(rate=float(np.mean(hit) * 100), chance=float(np.mean(ch) * 100))
print(out)
r = json.load(open('verify/p10_recompute.json')); r['peak_window_native_any_switch'] = out; json.dump(r, open('verify/p10_recompute.json', 'w'), indent=1)
