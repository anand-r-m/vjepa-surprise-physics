"""T4 Ablations (M1): A1 aggregation, A2 fixed context length C, effect on clean accuracy and specificity AUROC.
All rows from VERIFIED (abl.* keys, recomputed by the verifier; primary row from h2.M1.* / clean.M1_fp16.*). -> paper/tables/t4_ablations.tex"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import *

g = lambda x, nd=3: f(x, nd)


def jr(name, label):
    k = f"abl.{name}."
    return (f"{label} & {f(val(k + 'clean_pct'))} & {f(100 * val(k + 'A0'))} & {fci(val(k + 'A'), ci(k + 'A'), 3)} & "
            f"{fci(val(k + 'D_1'), ci(k + 'D_1'), 3)} & {fci(val(k + 'D_2'), ci(k + 'D_2'), 3)} \\\\")


prim = (f"Event-aligned max, min over $C$ (primary) & {f(val('clean.M1_fp16.tiehalf'))} & {f(100 * val('h2.M1.A0'))} & {fci(val('h2.M1.A'), ci('h2.M1.A'), 3)} & "
        f"{fci(val('h2.M1.D_B1'), ci('h2.M1.D_B1'), 3)} & {fci(val('h2.M1.D_B2'), ci('h2.M1.D_B2'), 3)} \\\\")
a1 = [prim, jr("A1_full_max", "Full-clip max"), jr("A1_mean", "Full-clip mean")]
a2 = [jr(f"A2_C{C_}", f"Fixed $C={C_}$ (event-aligned max)") for C_ in (2, 6, 10)]
tex = r"""\begin{table*}[t]
\caption{Ablations for M1 (V-JEPA ViT-L). Clean = IntPhys-dev pairwise accuracy in \% (tie-half) under the stated aggregation (mean for the A2 rows and the primary row; full-clip max for the full-clip-max row); $A_0$ = clean accuracy under the specificity aggregation of that row. $A$, $D_1$, $D_2$ as in Table~\ref{tab:t5} (supplement). A3 (dose-response) is Table~\ref{tab:t2b} and Fig.~\ref{fig:f3}. Fixed $C=2$ gives below-chance clean accuracy, so the default minimum over $C$ is dominated by the $C=2$ column.}
\label{tab:t4}
\centering\scriptsize
\setlength{\tabcolsep}{3pt}
\begin{tabular}{@{}lccccc@{}}
\toprule
Setting & Clean (\%) & $A_0$ (\%) & $A$ [95\% CI] & $D_1$ [CI] & $D_2$ [CI] \\
\midrule
\multicolumn{6}{@{}l}{\textit{A1 aggregation}} \\
""" + "\n".join(a1) + r"""
\midrule
\multicolumn{6}{@{}l}{\textit{A2 context length (min over $C$ = primary row)}} \\
""" + "\n".join(a2) + r"""
\bottomrule
\end{tabular}
\end{table*}
"""
write_tex("t4_ablations.tex", tex)
write_sidecar("T4", "scripts/figs/t4_ablations.py", ["paper/tables/t4_ablations.tex"],
              extra=dict(notes=["All rows use VERIFIED abl.* keys", "M2 ablations not run (A1/A2 H2 variants for M2 not produced)"]))
