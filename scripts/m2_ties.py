"""M2 tie counts per run (descriptive; frozen P functions only). python scripts/m2_ties.py <runs dir> <out json>"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_analysis as RA
from vjepa_study.analysis import prereg as P

R = RA.Runs(sys.argv[1]); out = {}
clean = R.need(R.clean_id("M2")); tau = RA.h1_var("mean").tau(clean)
def nt(d, key="S", how="mean", tv=None):
    px = P.pair_index(d); s = P.video_scores(d, key, how, tv)
    return int((np.abs(s[px["imp"]] - s[px["pos"]]) <= tau_k).sum())
out["H1_mean_agg"] = {"tau": tau}
for tag, rid in [("clean", R.clean_id("M2")), ("clean-skip4", R.clean_id("M2", "skip4"))] + \
        [(f"{e}-high s{s}", R.id("M2", e, "high", s)) for e, ss in (("brightness", 3), ("noise", 3), ("blur", 1), ("jpeg", 1), ("zoom", 1), ("hflip", 1), ("fps_halve", 1)) for s in range(1, ss + 1)] + \
        [(f"dither-on s{s}", R.id("M2", "dither", "on", s)) for s in (1, 2, 3)]:
    d = R.need(rid); px = P.pair_index(d); s = P.video_scores(d, "S", "mean")
    df = s[px["imp"]] - s[px["pos"]]
    out["H1_mean_agg"][tag] = dict(n_tie_tau=int((np.abs(df) <= tau).sum()), n_exact0=int((df == 0).sum()))
d1, d2 = R.need(R.id("M2", "fps_halve", "high", 1)), R.need(R.clean_id("M2", "skip4"))
out["fps_halve_equals_skip4_bitwise"] = bool(np.array_equal(d1["S"], d2["S"]))
# H2: event-aligned max
matches = json.load(open("kaggle/h2_spec_a/matches.json")); px = P.pair_index(clean)
t_on, late = RA.event_times(matches, px["pair_ids"]); keep = ~late; tvc = P._per_video_t(clean, px, t_on)
h2 = {}
for name, key in (("M2", "S"), ("B1", "B1"), ("B2", "B2"), ("B3", "B3")):
    tk = RA.make_var("h2").tau(clean, key); s = P.video_scores(clean, key, "max", tvc)
    dv = (s[px["imp"]] - s[px["pos"]])[keep]
    h2[name] = dict(tau=tk, clean_dv_tie=int((np.abs(dv) <= tk).sum()), exact0=int((dv == 0).sum()))
tk = RA.make_var("h2").tau(clean, "S"); s_pos = P.video_scores(clean, "S", "max", tvc)[px["pos"]]
dv = (P.video_scores(clean, "S", "max", tvc)[px["imp"]] - s_pos)[keep]
h2["abrupt_tie"], h2["auroc_cmp_in_band"] = {}, {}
for t in RA.SPEC_TYPES:
    h2["abrupt_tie"][t], h2["auroc_cmp_in_band"][t] = [], []
    for sd in ((1, 2, 3) if t in RA.SEEDED else (1,)):
        de = R.need(R.id("M2", t, "mid", sd)); pe = P.pair_index(de)
        se = P.video_scores(de, "S", "max", P._per_video_t(de, pe, t_on))[pe["pos"]]
        if t in ("jolt_base", "zoom_base"):
            dr = R.need(R.id("M2", "base_ref", "ref", 1)); pr = P.pair_index(dr)
            sr = P.video_scores(dr, "S", "max", P._per_video_t(dr, pr, t_on))[pr["pos"]]
        else:
            sr = s_pos
        da = (se - sr)[keep]
        h2["abrupt_tie"][t].append(int((np.abs(da) <= tk).sum()))
        h2["auroc_cmp_in_band"][t].append(round(float((np.abs(dv[:, None] - da[None, :]) <= tk).mean()), 4))
out["H2_event_aligned_max"] = h2
# H3 ties
ctrl = lambda e: R.need(R.id("M2", e, "high", 1))
tau3 = RA.make_var("h3").tau(clean); s0 = P.video_scores(clean, "S", "max")[px["pos"]]
out["H3"] = {e: int((np.abs(P.video_scores(ctrl(e), "S", "max")[P.pair_index(ctrl(e))["pos"]] - s0) <= tau3).sum()) for e in ("vflip", "hflip", "time_reversal")}
out["H3"]["tau"] = tau3
Path(sys.argv[2]).write_text(json.dumps(out, indent=1))
