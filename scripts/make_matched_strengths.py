"""Per-pair, outcome-blind magnitude matching for the H2 abrupt edits (A1.4/B3-B6).

Pixels only (no model outputs). To be run ONCE, AFTER the pre-registration freeze (MJ9),
producing the JSON consumed by kaggle/common/run_lib.py (edit.matches).

  python scripts/make_matched_strengths.py --dev-root <dev dir or npz dir> --out matches.json

Output: {"meta": {...}, "pairs": {pair_id: {"event": {t_on,t_off,fallback}, "m_i": ..,
          kind: {...match_pair dict...} | {"1": {...}, "2": {...}, "3": {...}}}}}
Seeded kinds (lighting_global, lighting_local, jolt_base) are matched per seed (gain sign /
jolt direction change clipping); zoom_base is seed-free.
"""
import argparse
import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from vjepa_study import amend, data

SEEDED = ("lighting_global", "lighting_local", "jolt_base")
KINDS = ("lighting_global", "lighting_local", "jolt_base", "zoom_base")
_CFG = {}


def _init(cfg):
    _CFG.update(cfg)


def _pair(block, scene, k):
    f4, lab, ids = data.load_dev_quadruplet(_CFG["dev_root"], block, scene)
    ip, ii = data.make_pairs(f4, lab, _CFG["frame_step"])[k]
    return f4[ip], f4[ii], f"{block}/{scene}/p{k}"


def divergence_job(job):
    p, v, pid = _pair(*job)
    return pid, amend.divergence(p, v, _CFG["res"])


def match_job(job):
    (block, scene, k), tau = job
    p, v, pid = _pair(block, scene, k)
    D = amend.divergence(p, v, _CFG["res"])
    ev = amend.event_window(D, tau, seed=_CFG["fallback_seed"])
    t_on, t_off = ev["t_on"], ev["t_off"]
    sup = amend.violation_support(p, v, t_on, t_off, _CFG["res"])
    out = dict(event=ev, m_i=amend.pair_magnitude(p, v, t_on, t_off, _CFG["res"]),
               onset_diff=float(D[t_on]), affected_area_fraction=float((sup["mask"]).mean()),
               onset_abrupt=bool(D[t_on] >= 0.5 * D[t_on:t_off].mean()),           # visible/occluded proxy (prereg sec 9)
               support_retention_crop=amend.support_retention(sup["mask"], 0.7))
    for kind in KINDS:
        if kind in SEEDED:
            out[kind] = {str(s): amend.match_pair(kind, p, v, t_on, t_off, s, _CFG["res"]) for s in _CFG["seeds"]}
        else:
            out[kind] = amend.match_pair(kind, p, v, t_on, t_off, 1, _CFG["res"])
    return pid, out


def run(dev_root, out, res=224, frame_step=2, seeds=(1, 2, 3), workers=4, limit=None, blocks=data.BLOCKS):
    cfg = dict(dev_root=str(dev_root), res=res, frame_step=frame_step, seeds=list(seeds), fallback_seed=1)
    scenes = data.list_dev_scenes(dev_root, blocks)
    jobs = [(b, s, k) for b, s in scenes for k in (0, 1)]
    if limit:
        jobs = jobs[:limit]
    with Pool(workers, initializer=_init, initargs=(cfg,)) as pool:
        divs = dict(pool.map(divergence_job, jobs))
        tau = amend.tau_rule(divs.values())
        pairs = dict(pool.map(match_job, [(j, tau) for j in jobs]))
    ratios = {k: [] for k in KINDS}
    for pid, d in pairs.items():
        for kind in KINDS:
            ms = d[kind].values() if kind in SEEDED else [d[kind]]
            ratios[kind] += [m["levels"]["mid"]["ratio"] for m in ms]
    summary = {k: dict(median=float(np.nanmedian(v)), frac_within_0p9_1p1=float(np.mean((np.array(v) > 0.9) & (np.array(v) < 1.1))),
                       n=len(v)) for k, v in ratios.items()}
    meta = dict(tau=tau, n_pairs=len(pairs), n_fallback=int(sum(d["event"]["fallback"] for d in pairs.values())),
                res=res, frame_step=frame_step, seeds=list(seeds), mid_ratio_summary=summary)
    Path(out).write_text(json.dumps(dict(meta=meta, pairs=pairs)))
    return meta


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dev-root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--res", type=int, default=224)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limit", type=int)
    a = ap.parse_args()
    print(json.dumps(run(a.dev_root, a.out, a.res, workers=a.workers, limit=a.limit), indent=1))
