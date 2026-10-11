"""F2 Specificity (headline). Left: distributions of delta_viol vs delta_abrupt for M1 and B1 (units: % of the score's median clean value,
event-aligned max, mid strength, 4 abrupt types x seeds pooled). Right: AUROC with 95% CIs for all models / baselines, against 0.5.
 -> paper/figures/f2_specificity.pdf"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import *
import numpy as np

plt = mpl()
arr = h2_arrays(("M1",))
h2 = jload("results/analysis/h2/h2.json"); h2m2 = jload("results/analysis/m2/h2.json")
fig = plt.figure(figsize=(7.16, 2.5))
gs = fig.add_gridspec(2, 2, width_ratios=[1.0, 1.0], wspace=0.34, hspace=0.75)
axl = [fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[1, 0])]
axr = fig.add_subplot(gs[:, 1])
for ax, name in zip(axl, ["M1", "B1"]):
    a = arr[name]
    dv = 100 * a["dv"] / a["med"]
    da = 100 * np.concatenate([v.ravel() for v in a["da"].values()]) / a["med"]
    lo, hi = np.percentile(np.concatenate([dv, da]), [2, 98])
    for v, lab, kw in ((da, r"$\Delta_{\rm abrupt}$: possible + abrupt event", dict(color="#222222", ls="--", lw=1.3)),
                       (dv, r"$\Delta_{\rm viol}$: impossible $-$ possible", dict(color=C[name], ls="-", lw=1.8))):
        xs = np.sort(v)
        ax.plot(xs, np.arange(1, len(xs) + 1) / len(xs), label=lab, **kw)
    ax.set_xlim(lo, hi)
    ax.axvline(0, color="#999999", lw=0.6, zorder=1)
    A = val("h2.M1.A") if name == "M1" else val("h2.M1.A_B1")
    ax.text(0.98, 0.04, f"AUROC $A$ = {f(A,3)}", transform=ax.transAxes, ha="right", va="bottom", fontsize=6.5, fontweight="bold")
    ax.set_title(("M1 V-JEPA ViT-L" if name == "M1" else "B1 frame difference") + f" ({len(dv)} pairs, {da.size} abrupt)", loc="left")
    ax.set_ylim(0, 1.02)
    if name == "B1":
        ax.set_xlabel("surprise change, % of median clean score")
    ax.legend(loc="lower right", frameon=False, fontsize=5.6, handlelength=2.2, bbox_to_anchor=(1.0, 0.12))
axl[0].set_ylabel("cumulative share"); axl[1].set_ylabel("cumulative share")
axl[0].text(0.0, 1.3, "(a) violations vs matched abrupt events (CDFs)", transform=axl[0].transAxes, fontsize=7.5, fontweight="bold")

rows = []   # (label, model-key, A, ci, A_nolg, ci_nolg, descriptive?)
rows.append(("M1", "M1", val("h2.M1.A"), ci("h2.M1.A"), val("h2.M1.A_nolg"), ci("h2.M1.A_nolg"), False))
rows.append(("M2 (descr.)", "M2", val("h2.M2.A"), ci("h2.M2.A"), val("h2.M2.A_nolg"), ci("h2.M2.A_nolg"), True))
rows.append(("B1 frame diff.", "B1", val("h2.M1.A_B1"), h2["B1"]["A_ci"], None, None, False))
rows.append(("B2 copy-last", "B2", val("h2.M1.A_B2"), h2["B2"]["A_ci"], None, None, False))
rows.append(("B3 target-feat. (descr.)", "B3", h2["B3"]["A"], h2["B3"]["A_ci"], None, None, True))
y = np.arange(len(rows))[::-1] + 1
for yi, (lab, k, A, c, An, cn, desc) in zip(y, rows):
    axr.errorbar(A, yi + 0.12, xerr=[[A - c[0]], [c[1] - A]], fmt=MARK[k], color=C[k], mfc="white" if desc else C[k], ms=5, capsize=2.2, elinewidth=1.0, zorder=3)
    axr.text(1.02, yi + 0.12, f"{f(A,3)}", fontsize=6, va="center", transform=axr.get_yaxis_transform())
    if An is not None:
        axr.errorbar(An, yi - 0.18, xerr=[[An - cn[0]], [cn[1] - An]], fmt=MARK[k], color=C[k], mfc="white", ms=3.4, capsize=1.8, elinewidth=0.8, alpha=0.9, zorder=3)
axr.axvline(0.5, color="#333333", ls="--", lw=0.9, zorder=2)
axr.text(0.5, len(rows) + 0.75, "chance 0.5", fontsize=6, ha="center", va="bottom")
axr.axvline(0.8, color="#888888", ls=":", lw=0.8, zorder=2)
axr.text(0.8, len(rows) + 0.75, "support 0.80", fontsize=6, ha="center", va="bottom", color="#555555")
axr.axhline(0.45 - 0.0, color="none")
V("m3.*")
axr.text(0.5, 0.0, "M3 VideoMAE V2: not run", fontsize=6.2, ha="center", va="center", style="italic", color="#555555")
axr.set_yticks(list(y)); axr.set_yticklabels([r[0] for r in rows]); axr.set_ylim(-0.6, len(rows) + 1.4)
axr.set_xlim(0.2, 0.9); axr.set_xlabel("specificity AUROC $A$ (95% CI)\nsmall open marker = without lighting_global")
axr.set_title("(b) AUROC against abrupt events", loc="left", fontweight="bold", fontsize=7.5, y=1.0); axr.grid(axis="y", visible=False)
out = FIGS / "f2_specificity.pdf"; fig.savefig(out); plt.close(fig)
write_sidecar("F2", "scripts/figs/f2_specificity.py", ["paper/figures/f2_specificity.pdf"],
              extra=dict(notes=["Panel (a) arrays recomputed from raw runs with the frozen analysis functions (scripts/run_analysis.h2_stage logic, event-aligned max, mid, tie-half not needed)",
                                "B1/B2/B3 CIs and B3 A from results/analysis/h2/h2.json (no VERIFIED key); M3 pending"]))
