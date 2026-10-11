"""F1 Invariance: flip rate per edit (high strength), grouped by model, with the dither floor f0 as reference; right panel: flip - f0 with CI.
fps_halve excluded (design error). -> paper/figures/f1_invariance.pdf"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import *
import numpy as np

plt = mpl()
EDITS = [("brightness", "brightness"), ("noise", "noise"), ("blur", "blur"), ("jpeg", "JPEG"), ("zoom", "zoom*"), ("hflip", "h-flip")]
MODELS = ["M1", "M2"]
SHORT = dict(M1="M1 (solid)", M2="M2 (hatched)")
fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.16, 2.5), gridspec_kw=dict(wspace=0.22))
x = np.arange(len(EDITS)); w = 0.36
for j, m in enumerate(MODELS):
    fl = [val(f"h1.{m}.{e}.flip_pct") for e, _ in EDITS]
    ex = [val(f"h1.{m}.{e}.flip_minus_f0_pp") for e, _ in EDITS]
    exc = np.array([ci(f"h1.{m}.{e}.flip_minus_f0_pp") for e, _ in EDITS])
    off = (j - 0.5) * w
    a1.bar(x + off, fl, w, color=C[m], hatch=HATCH[m], edgecolor="white", linewidth=0.3, label=SHORT[m], zorder=3)
    a1.axhline(val(f"h1.{m}.f0_pct"), color=C[m] if m == "M1" else "#7a2f00", ls=LS[m], lw=1.3, zorder=4, label=f"dither floor $f_0$, {m} ({f(val(f'h1.{m}.f0_pct'))}%)")
    a2.errorbar(x + off, ex, yerr=[np.array(ex) - exc[:, 0], exc[:, 1] - np.array(ex)], fmt=MARK[m], color=C[m], mfc=C[m] if m == "M1" else "white",
                ms=4.5, capsize=2, elinewidth=0.9, ls="none", label=SHORT[m], zorder=3)
a1.set_ylabel("flip rate (% of 180 pairs)"); a1.set_ylim(0, 60)
a1.set_title("(a) flip rate at high strength", loc="left")
a2.axhline(0, color="#333333", lw=0.8, zorder=2)
a2.set_ylabel("flip rate minus floor $f_0$ (pp), 95% CI")
a2.set_title("(b) flip rate minus floor", loc="left")
for a in (a1, a2):
    a.set_xticks(x); a.set_xticklabels([l for _, l in EDITS]); a.tick_params(axis="x", length=0)
a1.legend(loc="upper left", frameon=False, ncol=2, columnspacing=0.8, handlelength=1.6)
fig.text(0.01, -0.04, "* zoom: 112 of 180 pairs retained. M2 descriptive. Frame-rate halving omitted (design error: edited input identical to the skip-4 clean input).",
         fontsize=5.8, color="#444444", ha="left")
out = FIGS / "f1_invariance.pdf"
fig.savefig(out); plt.close(fig)
write_sidecar("F1", "scripts/figs/f1_invariance.py", ["paper/figures/f1_invariance.pdf"])
