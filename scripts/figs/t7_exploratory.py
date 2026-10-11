"""T7 EXPLORATORY analyses (post-hoc, not pre-registered): onset-aligned H2 and halve-and-hold H1. -> paper/tables/t7_exploratory.tex"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import *

k = "expl.onset"
tex = r"""\begin{table}[t]
\caption{EXPLORATORY (post-hoc, not pre-registered). (a) H2 re-run with the event onset defined from the data (first frame at which the impossible and possible videos differ), instead of the frozen threshold that found an onset in only 2 of 180 pairs; """ + f"{int(val('expl.onset.n_transient'))}" + r""" of the 180 events are transient. $A$ = specificity AUROC [95\% CI]; $D_1$, $D_2$ vs B1, B2 (Holm-2 $p$). (b) Halve-and-hold edit for H1 (frame rate halved, clip length held), replacing the frame-rate-halving edit, which was a design error.}
\label{tab:t7}
\centering\scriptsize
\setlength{\tabcolsep}{2.6pt}
\begin{tabular}{@{}lc@{}}
\toprule
\multicolumn{2}{@{}l}{\textbf{EXPLORATORY (a) onset-aligned H2, M1}} \\
\midrule
$A$ [95\% CI] & """ + fci(val(k + ".A"), ci(k + ".A"), 3) + r""" \\
$A_0$ (clean, same aggregation) [CI] & """ + fci(val(k + ".A0"), ci(k + ".A0"), 3) + r""" \\
$A$ without lighting\_global [CI] & """ + fci(val(k + ".A_nolg"), ci(k + ".A_nolg"), 3) + r""" \\
$D_1$ vs B1 [CI] (Holm $p$) & """ + fci(val(k + ".D_1"), ci(k + ".D_1"), 3) + f" ({fp(val(k + '.holm2_D_1'))})" + r""" \\
$D_2$ vs B2 [CI] (Holm $p$) & """ + fci(val(k + ".D_2"), ci(k + ".D_2"), 3) + f" ({fp(val(k + '.holm2_D_2'))})" + r""" \\
$A_{B1}$, $A_{B2}$ & """ + f"{f(val(k + '.A_B1'), 3)}, {f(val(k + '.A_B2'), 3)}" + r""" \\
$A$ by type (lg / ll / jolt / zoom) & """ + " / ".join(f(val(f"{k}.A.{t}"), 3) for t in ("lighting_global", "lighting_local", "jolt_base", "zoom_base")) + r""" \\
\midrule
\multicolumn{2}{@{}l}{\textbf{EXPLORATORY (b) halve-and-hold, M1}} \\
\midrule
$\Delta$Acc [CI] (pp) & """ + fci(val("expl.halve_hold.dacc_pp"), ci("expl.halve_hold.dacc_pp"), 1, True) + r""" \\
Flip rate (\%) / floor $f_0$ (\%) & """ + f"{f(val('expl.halve_hold.flip_pct'))} / {f(val('expl.halve_hold.f0_pct'))}" + r""" \\
Flip $-$ $f_0$ [CI] (pp) & """ + fci(val("expl.halve_hold.flip_minus_f0_pp"), ci("expl.halve_hold.flip_minus_f0_pp"), 1, True) + r""" \\
\bottomrule
\end{tabular}
\end{table}
"""
write_tex("t7_exploratory.tex", tex)
write_sidecar("T7", "scripts/figs/t7_exploratory.py", ["paper/tables/t7_exploratory.tex"], extra=dict(notes=["Extra item (not in PROJECT_SPEC Expected outputs); all keys have exploratory=True"]))
