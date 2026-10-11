"""F3 Dose-response (A3): flip rate vs strength for the H1 edits (top) and AUROC vs strength for the H2 abrupt-event types (bottom);
M1 left, M2 right (descriptive). M2 low/mid points are drawn only when VERIFIED has the m2.dose.* keys; otherwise a 'not run' marker is shown.
 -> paper/figures/f3_dose.pdf"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import *
import numpy as np

plt = mpl()
LV = ["low", "mid", "high"]; X = np.arange(3)
E1 = [("brightness", "brightness", "#0072B2", "o", "-"), ("noise", "noise", "#D55E00", "s", "--"), ("blur", "blur", "#009E73", "^", "-."),
      ("jpeg", "JPEG", "#E69F00", "D", ":"), ("zoom", "zoom", "#CC79A7", "v", (0, (5, 1, 1, 1)))]
T2 = [("lighting_global", "lighting (global)", "#0072B2", "o", "-"), ("lighting_local", "lighting (local)", "#D55E00", "s", "--"),
      ("jolt_base", "camera jolt", "#009E73", "^", "-."), ("zoom_base", "sudden zoom", "#E69F00", "D", ":")]
dose = jload("results/analysis/h1/dose/dose_M1.json")["per_edit"]
fig, ax = plt.subplots(2, 2, figsize=(7.16, 4.6), gridspec_kw=dict(hspace=0.42, wspace=0.22))
pend = {"h1": False, "h2": False}


def h1_series(m, e):
    out = []
    for lv in LV:
        if m == "M1":
            out.append(val(f"dose.h1.M1.{e}-{lv}.flip_pct"))
        elif lv == "high":
            out.append(val(f"h1.M2.{e}.flip_pct"))
        else:
            v = val(f"m2.dose.h1.{e}.{lv}.flip_pct")
            if v is None:
                V(f"m2.dose.h1.{e}.{lv}.flip_pct"); pend["h1"] = True
            out.append(v)
    return out


for j, m in enumerate(["M1", "M2"]):
    a = ax[0, j]
    for e, lab, col, mk, ls in E1:
        y = h1_series(m, e)
        xs = [i for i, v in enumerate(y) if v is not None]
        ys = [y[i] for i in xs]
        if m == "M1":
            lo = [dose[f"{e}@{lv}"]["flip_ci"][0] * 100 for lv in LV]; hi = [dose[f"{e}@{lv}"]["flip_ci"][1] * 100 for lv in LV]
            a.fill_between(X, lo, hi, color=col, alpha=0.12, lw=0)
        a.plot(xs, ys, color=col, marker=mk, ls=ls, ms=4, label=lab, mfc=col if m == "M1" else "white")
    f0 = val(f"h1.{m}.f0_pct")
    a.axhline(f0, color="#222222", lw=1.0, ls=(0, (1, 1.5)))
    a.text(-0.15, f0 + 0.6, f"dither floor $f_0$ = {f(f0)}%", fontsize=5.8, va="bottom", ha="left", color="#222222")
    a.set_xticks(X); a.set_xticklabels(LV); a.set_xlim(-0.2, 2.65); a.set_ylim(0, 56)
    a.set_title(("(a) M1: " if m == "M1" else "(b) M2 (descr.): ") + "flip rate vs strength", loc="left", fontweight="bold", fontsize=7)
    if j == 0:
        a.set_ylabel("flip rate (%)  [band: 95% CI]"); a.legend(loc="upper left", ncol=2, frameon=False, fontsize=5.8, bbox_to_anchor=(0.0, 1.0))
    if m == "M2" and pend["h1"]:
        a.text(0.5, 0.55, "JPEG, zoom at low / mid:\nnot run (GPU quota)", transform=a.transAxes, ha="center", fontsize=6,
               bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#999999", ls="--"))

for j, m in enumerate(["M1", "M2"]):
    a = ax[1, j]
    # pooled A with CI
    ys, los, his, xs = [], [], [], []
    for i, lv in enumerate(LV):
        if m == "M1":
            A, c = val(f"dose.h2.M1.{lv}.A"), ci(f"dose.h2.M1.{lv}.A")
        else:
            k = "h2.M2.A" if lv == "mid" else f"m2.dose.h2.pooled.{lv}.A"
            A, c = val(k), (ci(k) if lv == "mid" else None)
            if A is None:
                V(k); pend["h2"] = True
        if A is not None:
            xs.append(i); ys.append(A); los.append(c[0] if c else A); his.append(c[1] if c else A)
    a.fill_between(xs, los, his, color="#555555", alpha=0.15, lw=0) if len(xs) > 1 else None
    a.errorbar(xs, ys, yerr=[np.array(ys) - los, np.array(his) - ys], color="#111111", marker="*", ms=7, lw=1.8, capsize=2, label="pooled (4 types)", zorder=5,
               ls="-" if len(xs) > 1 else "none")
    for t, lab, col, mk, ls in T2:
        yt = []
        for i, lv in enumerate(LV):
            if m == "M1":
                yt.append(val(f"dose.h2.M1.{lv}.{t}.A"))
            else:
                if lv == "mid":
                    yt.append(val(f"h2.M2.A.{t}"))
                else:
                    k = f"m2.dose.h2.{t}.{lv}.A"; v = val(k)
                    if v is None:
                        V(k)
                    yt.append(v)
        xt = [i for i, v in enumerate(yt) if v is not None]
        a.plot(xt, [yt[i] for i in xt], color=col, marker=mk, ls=ls, ms=3.6, lw=0.9, label=lab, mfc=col if m == "M1" else "white", alpha=0.95)
    a.axhline(0.5, color="#333333", ls="--", lw=0.9); a.text(2.6, 0.5, "chance", fontsize=5.8, va="bottom", ha="right")
    a.set_xticks(X); a.set_xticklabels(LV); a.set_xlim(-0.2, 2.65); a.set_ylim(0.3, 0.8)
    a.set_xlabel("abrupt-event strength (violation-matched at mid)")
    a.set_title(("(c) M1: " if m == "M1" else "(d) M2 (descr.): ") + "AUROC vs strength", loc="left", fontweight="bold", fontsize=7)
    if j == 0:
        a.set_ylabel("AUROC $A$"); a.legend(loc="upper right", ncol=2, frameon=False, fontsize=5.6)
    if m == "M2" and pend["h2"]:
        a.text(0.5, 0.2, "some cells not run (GPU quota)", transform=a.transAxes, ha="center", fontsize=6,
               bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#999999", ls="--"))
out = FIGS / "f3_dose.pdf"; fig.savefig(out); plt.close(fig)
write_sidecar("F3", "scripts/figs/f3_dose.py", ["paper/figures/f3_dose.pdf"],
              extra=dict(notes=["flip-rate CI bands (M1) from results/analysis/h1/dose/dose_M1.json (no VERIFIED key)",
                                "M2 pending cells are driven by VERIFIED keys m2.dose.h1.<edit>.<low|mid>.flip_pct and m2.dose.h2.<pooled|type>.<low|high>.A; rerun when they land (the current VERIFIED has only brace-pattern placeholders)",
                                "M2 H2 mid point = h2.M2.A and h2.M2.A.<type>"]))
