"""EXPLORATORY (post-freeze, human-approved Q11): onset-aligned magnitude matching.

Identical to scripts/make_matched_strengths.py (same match_job / amend.event_window / amend.match_pair; imported, not
copied) except that the event threshold tau_D is the pixel-only onset threshold chosen by the rule in
notes/ONSET_ALIGNED.md instead of the frozen max(2/255, 99.9th pct of the prefix), so that t_on is the true splice time
and the fallback draw is not used. Pixels only: no model output is read. Writes a SEPARATE file
(kaggle/h2_onset/matches.json); the frozen kaggle/h2_spec_*/matches.json are never touched.

  python scripts/make_onset_matches.py --dev-root data/intphys_dev/extracted/dev --out kaggle/h2_onset/matches.json --workers 4
"""
import argparse
import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_matched_strengths as M          # noqa: E402  (frozen helpers, reused unchanged)
from vjepa_study import amend, data         # noqa: E402

GRID_GRAY = (0.0, 0.1, 0.2, 0.3, 0.5, 0.75, 1.0, 1.5, 2.0)      # candidate thresholds, gray levels of 255
MIN_DEFINED = 0.90


def choose_threshold(divs):
    """Pixel-only rule (no model output): theta = smallest grid value (gray levels /255) that is >= the prefix noise floor
    (99.9th percentile of D over the first 10 frames of all dev pairs) and at which >= 90% of pairs have a defined onset
    (some frame with D > theta). Returns (theta in [0,1] units, table)."""
    D = [np.asarray(d, float) for d in divs]
    floor = float(np.percentile(np.concatenate([d[:10] for d in D]), 99.9))
    table = []
    theta = None
    for g in GRID_GRAY:
        th = g / 255.0
        on = [int(np.flatnonzero(d > th)[0]) if (d > th).any() else None for d in D]
        defined = float(np.mean([o is not None for o in on]))
        t = np.array([o for o in on if o is not None])
        table.append(dict(theta_gray=g, frac_defined=defined, t_on_median=float(np.median(t)) if len(t) else None,
                          frac_t_on_gt94=float((t > 94).mean()) if len(t) else None, n_defined=int(len(t))))
        if theta is None and th >= floor and defined >= MIN_DEFINED:
            theta = th
    return theta, floor, table


def run(dev_root, out, workers=4, limit=None):
    cfg = dict(dev_root=str(dev_root), res=224, frame_step=2, seeds=[1, 2, 3], fallback_seed=1)
    scenes = data.list_dev_scenes(dev_root, data.BLOCKS)
    jobs = [(b, s, k) for b, s in scenes for k in (0, 1)]
    if limit:
        jobs = jobs[:limit]
    with Pool(workers, initializer=M._init, initargs=(cfg,)) as pool:
        divs = dict(pool.map(M.divergence_job, jobs))
        theta, floor, table = choose_threshold(divs.values())
        pairs = dict(pool.map(M.match_job, [(j, theta) for j in jobs]))
    ratios = {k: [] for k in M.KINDS}
    for pid, d in pairs.items():
        for kind in M.KINDS:
            ms = d[kind].values() if kind in M.SEEDED else [d[kind]]
            ratios[kind] += [m["levels"]["mid"]["ratio"] for m in ms]
    summary = {k: dict(median=float(np.nanmedian(v)), frac_within_0p9_1p1=float(np.mean((np.array(v) > 0.9) & (np.array(v) < 1.1))),
                       n=len(v)) for k, v in ratios.items()}
    ev = [d["event"] for d in pairs.values()]
    meta = dict(exploratory=True, tau=theta, tau_gray=theta * 255, prefix_noise_floor=floor, threshold_table=table,
                n_pairs=len(pairs), n_fallback=int(sum(e["fallback"] for e in ev)), n_transient=int(sum(e["transient"] for e in ev)),
                n_excluded_late=int(sum(e["excluded_late"] for e in ev)), res=224, frame_step=2, seeds=[1, 2, 3], mid_ratio_summary=summary)
    Path(out).write_text(json.dumps(dict(meta=meta, pairs=pairs)))
    return meta


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dev-root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limit", type=int)
    a = ap.parse_args()
    print(json.dumps(run(a.dev_root, a.out, a.workers, a.limit), indent=1))
