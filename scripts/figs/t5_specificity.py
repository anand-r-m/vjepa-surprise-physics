"""T5 Specificity (H2): AUROC A = P(delta_viol > delta_abrupt) against 0.5 (primary); D_1 = A - A_B1, D_2 = A - A_B2 secondary.
Includes the with / without lighting_global rows. B1 and B2 below chance are shown as they are. -> paper/tables/t5_specificity.tex"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import *

h2 = jload("results/analysis/h2/h2.json")
h2m2 = jload("results/analysis/m2/h2.json")
TY = ["lighting_global", "lighting_local", "jolt_base", "zoom_base"]
g = lambda x, nd=3: f(x, nd)
gc = lambda x, c, nd=3: fci(x, c, nd)


def model_row(m, label):
    k = f"h2.{m}"
    d1, d2 = val(k + ".D_B1"), val(k + ".D_B2")
    return " & ".join([label, gc(val(k + ".A"), ci(k + ".A")), g(val(k + ".A0")),
                       gc(d1, ci(k + ".D_B1")), gc(d2, ci(k + ".D_B2"))] +
                      [g(val(f"{k}.A.{t}")) for t in TY]) + r" \\"


def base_row(b, label, src):
    # A from VERIFIED (h2.M1.A_B1 / A_B2); CI, A0, per-type from the analysis json (no VERIFIED key)
    A = val(f"h2.M1.A_{b}")
    return " & ".join([label, gc(A, src[b]["A_ci"]), g(src[b]["A0"]), "--", "--"] + [g(src[b]["per_type"][t]) for t in TY]) + r" \\"


def nolg_row(m, label):
    k = f"h2.{m}"
    return " & ".join([label, gc(val(k + ".A_nolg"), ci(k + ".A_nolg")), "--",
                       gc(val(k + ".D_B1.no_lg"), ci(k + ".D_B1.no_lg")), gc(val(k + ".D_B2.no_lg"), ci(k + ".D_B2.no_lg")),
                       "--", g(val(f"{k}.A.lighting_local")), g(val(f"{k}.A.jolt_base")), g(val(f"{k}.A.zoom_base"))]) + r" \\"


rows = [model_row("M1", "M1 V-JEPA ViT-L"), model_row("M2", "M2 V-JEPA 2 (descr.)"),
        base_row("B1", "B1 frame diff.", h2), base_row("B2", "B2 copy-last", h2), r"M3 VideoMAE V2 & \multicolumn{8}{c}{\textit{not run}} \\"]
V("m3.*")
nolg = [nolg_row("M1", "M1"), nolg_row("M2", "M2 (descr.)")]
lgn = val("h2_lg_noop_n"); lgt = val("h2_entries_n"); mi = val("h2_mi_median"); fb = val("h2_fallback_n"); pn = val("h2_pairs_n")
tex = r"""\begin{table*}[t]
\caption{Specificity (H2). $A$ is the AUROC of $\Delta_{\rm viol}$ against $\Delta_{\rm abrupt}$ (matched-magnitude abrupt events on possible videos), judged against 0.5 (chance); $A_0$ is the clean detection precondition. $D_1=A-A_{B1}$ and $D_2=A-A_{B2}$ are secondary: both baselines sit \emph{below} 0.5, so a positive $D$ does not mean the model is specific. CI: 10,000 scene-cluster bootstrap draws. Holm-2 $p$ for $(D_1, D_2)$: M1 """ + f"{fp(val('h2.M1.holm2_B1'))}, {fp(val('h2.M1.holm2_B2'))}; M2 {fp(val('h2.M2.holm2_B1'))}, {fp(val('h2.M2.holm2_B2'))}" + r""". Right block: AUROC by abrupt-event type. The lower block repeats the analysis without lighting\_global, whose magnitude match missed its target (""" + f"{int(lgn)} of {int(lgt)}" + r""" entries are no-ops inside the tie band). M2 is descriptive. Events: """ + f"{int(fb)} of {int(pn)}" + r""" pairs use the random-onset fallback; median matched violation magnitude """ + f"{f(mi,3)}" + r""" grey levels (of 255).}
\label{tab:t5}
\centering\scriptsize
\setlength{\tabcolsep}{1.8pt}
\begin{tabular}{@{}lccccrrrr@{}}
\toprule
Score & $A$ [95\% CI] & $A_0$ & $D_1$ [95\% CI] & $D_2$ [95\% CI] & lighting\_g & lighting\_l & jolt & zoom \\
\midrule
\multicolumn{9}{@{}l}{\textit{All four abrupt-event types}} \\
""" + "\n".join(rows) + r"""
\midrule
\multicolumn{9}{@{}l}{\textit{Excluding lighting\_global}} \\
""" + "\n".join(nolg) + r"""
\bottomrule
\end{tabular}
\end{table*}
"""
write_tex("t5_specificity.tex", tex)
write_sidecar("T5", "scripts/figs/t5_specificity.py", ["paper/tables/t5_specificity.tex"],
              extra=dict(notes=["B1/B2 CI, A0 and per-type AUROC come from results/analysis/h2/h2.json (no VERIFIED key); A itself from h2.M1.A_B1/A_B2",
                                "Pre-registered H2 outcome for M1 per VERIFIED h2.M1.outcome: " + str(val("h2.M1.outcome")), "M3 not run"]))
