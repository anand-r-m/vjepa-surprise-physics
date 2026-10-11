"""T3 Positive controls (H3/G2): detection rate = share of possible videos whose full-clip-max surprise rises after the edit.
 -> paper/tables/t3_controls.tex"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import *

NA = r"n/a"
c = lambda k, ck=None: fci(val(k), ci(k, ck), 1)
NOTRUN = r"\textit{not run}"
rows = [
    ("Vertical flip vs clean", c("g2_vflip_det", "g2_vflip_ci"), c("h3.M2.vflip_det"), c("g2_m0r_vflip_det"), NOTRUN),
    ("Vertical flip vs h-flip reference", c("h3.M1.vflip_det_ref_hflip"), c("h3.M2.vflip_det_ref_hflip"), NA, NOTRUN),
    ("Time reversal vs clean", c("g2_rev_det"), c("h3.M2.reversal_det"), NA, NOTRUN),
    ("Horizontal flip vs clean (neutral edit)", c("g2_hflip_det"), c("h3.M2.hflip_det"), NA, NOTRUN),
]
V("m3.*")
diff = (fci(val("h3.M1.minus_M0r_vflip"), ci("h3.M1.minus_M0r_vflip"), 1, True), fci(val("h3.M2.minus_M0r_vflip"), ci("h3.M2.minus_M0r_vflip"), 1, True))
g2 = lambda m: "met" if val(f"h3.{m}.G2_pass") else "not met"
g2m1 = "not met" if (val("g2_vflip_det") or 0) < 80 else "met"
body = "\n".join(f"{a} & {b} & {c_} & {d} & {e} \\\\" for a, b, c_, d, e in rows)
tex = r"""\begin{table*}[t]
\caption{Positive controls: detection rate in \% [95\% scene-cluster CI] of possible videos whose surprise rises after an edit that creates (or, for horizontal flip, does not create) a violation. The G2 gate required $\geq$80\% for vertical flip; the random-initialised M1 (M0r) is the reference for ``no learned sensitivity''. M1 and M2 differ from M0r by """ + f"{diff[0]} and {diff[1]}" + r""" pp (vflip). M2 is descriptive.}
\label{tab:t3}
\centering\scriptsize
\setlength{\tabcolsep}{4pt}
\begin{tabular}{@{}lcccc@{}}
\toprule
Control & M1 & M2 & M0r & M3 \\
\midrule
""" + body + r"""
\midrule
G2 gate (vflip $\geq$ 80\%) & """ + g2m1 + " & " + g2("M2") + r""" & -- & -- \\
Pairwise acc.\ on vflip pairs & """ + f(val("g2_vflip_pair_acc")) + " & " + f(val("h3.M2.pairwise_vflip_tiehalf")) + r""" & -- & """ + NOTRUN + r""" \\
\bottomrule
\end{tabular}
\end{table*}
"""
write_tex("t3_controls.tex", tex)
write_sidecar("T3", "scripts/figs/t3_controls.py", ["paper/tables/t3_controls.tex"],
              extra=dict(notes=["M0r reversal / hflip detection not in VERIFIED: shown n/a", "M3 column: not run",
                                "M1 reversal CI from entry ci of g2_rev_det; M1 hflip CI from entry ci"]))
