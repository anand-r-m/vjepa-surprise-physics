"""MJ4 / prereg sec 3: per-pair fraction of the violation-difference support retained by the centre crop
(scale 0.7 = high strength), from dev pixels via matches.json events. Output {"zoom": {pair_id: R}}
consumed by run_analysis --retention (pairs with R < 0.9 are excluded from confirmatory H1 for crop)."""
import json, sys
from pathlib import Path
from vjepa_study import amend, data

def run(dev_root, matches, out, res=224, scales=(0.9, 0.8, 0.7)):
    m = json.load(open(matches))["pairs"]
    R = {}
    for block, scene in data.list_dev_scenes(dev_root):
        f4, lab, _ = data.load_dev_quadruplet(dev_root, block, scene)
        for k, (ip, ii) in enumerate(data.make_pairs(f4, lab, 2)):
            pid = f"{block}/{scene}/p{k}"
            if pid not in m:
                continue
            ev = m[pid]["event"]
            sup = amend.violation_support(f4[ip], f4[ii], ev["t_on"], ev["t_off"], res)
            R[pid] = {str(s): amend.support_retention(sup["mask"], s) for s in scales}
    json.dump({"zoom": {pid: v["0.7"] for pid, v in R.items()}, "all_scales": R}, open(out, "w"))
    return R

if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2], sys.argv[3])
