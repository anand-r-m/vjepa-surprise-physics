"""F4 Example surprise curves (M1): clean possible, impossible, possible + abrupt event (lighting_local, mid, seed 1), event time marked.
Pair choice is not hand-picked: the pair of each IntPhys block (O1,O2,O3) whose event-aligned max delta_viol is closest to that block's median.
 -> paper/figures/f4_curves.pdf"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import *
import numpy as np

sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT / "src"))
import run_analysis as RA
from vjepa_study.analysis import prereg as P

plt = mpl()
R = RA.Runs(RUNS_DIR)
arr = h2_arrays(("M1",))["M1"]
matches = jload("kaggle/h2_spec_a/matches.json")
clean = R.need(R.clean_id("M1")); edit = R.need(R.id("M1", "lighting_local", "mid", 1))
I("results/raw/p4_clean_m1/results/P4_M1_ipdev_clean_s1/surprise.npz"); I("results/raw/h2_spec_a/results/P4_M1_ipdev_lighting_local-mid_s1/surprise.npz")
pc, pe = P.pair_index(clean), P.pair_index(edit)
pid = list(arr["pair_ids"]); dv = arr["dv"]; blocks = arr["block"]
chosen = []
for b in ("O1", "O2", "O3"):
    idx = np.flatnonzero(blocks == b)
    med = np.median(dv[idx]); chosen.append(idx[np.argmin(np.abs(dv[idx] - med))])
fig, axs = plt.subplots(1, 3, figsize=(7.16, 2.35), sharey=True, gridspec_kw=dict(wspace=0.06))
info = []
for ax, i in zip(axs, chosen):
    p = pid[i]; ev = matches["pairs"][p]["event"]; t_on = ev["t_on"]
    ic = list(pc["pair_ids"]).index(p); ie = list(pe["pair_ids"]).index(p)
    cur = lambda d, k: P.curve(np.asarray(d["S"][k])[: int(d["lengths"][k])])
    cp, ci_ = cur(clean, pc["pos"][ic]), cur(clean, pc["imp"][ic])
    ce = cur(edit, pe["pos"][ie])
    w = np.arange(len(cp))
    w_on = max(0, int(np.ceil((t_on - 30) / 4)))        # first window with 4w+30 >= t_on (event-aligned window set starts here)
    ax.axvspan(w_on, len(cp) - 1, color="#eeeeee", zorder=0)
    ax.axvline(w_on, color="#333333", lw=1.0, ls="--", zorder=2)
    ax.plot(w, cp, color=C["M1"], lw=1.5, label="possible (clean)")
    ax.plot(w, ci_, color=C["M2"], lw=1.5, ls=(0, (4, 1.5)), label="impossible (clean)")
    ax.plot(np.arange(len(ce)), ce, color="#222222", lw=1.1, ls=":", marker="o", ms=2.2, label="possible + abrupt lighting event")
    ax.set_title(f"{p}  (block {pc['block'][ic]}, $t^*$ = frame {int(t_on)}{'*' if ev['fallback'] else ''})", loc="left", fontsize=6.5)
    ax.set_xlabel("window index (stride 4 frames)")
    info.append(dict(pair=p, t_on_frame=int(t_on), first_event_window=w_on, fallback_onset=bool(ev["fallback"])))
axs[0].set_ylabel("surprise (min over $C$)")
h, l = axs[0].get_legend_handles_labels()
fig.legend(h, l, loc="upper center", ncol=3, frameon=False, fontsize=6.2, bbox_to_anchor=(0.5, 1.07))
fig.text(0.01, -0.07, "Dashed line / grey region: event time $t^*$ and the windows covering it (event-aligned set). * random-onset fallback ($t^*$ in the middle of the clip;\n"
         "178 of 180 pairs have no measurable violation onset). Each pair is the median-$\\Delta_{\\rm viol}$ pair of its block, not chosen by eye.", fontsize=5.8, color="#444444", ha="left", va="top")
out = FIGS / "f4_curves.pdf"; fig.savefig(out); plt.close(fig)
write_sidecar("F4", "scripts/figs/f4_curves.py", ["paper/figures/f4_curves.pdf"], extra=dict(pairs=info))
