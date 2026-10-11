"""T1 Reproduction: clean IntPhys-dev pairwise accuracy (mean aggregation), ours vs published. -> paper/tables/t1_reproduction.tex"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import *

g = jload("results/analysis/p4/p4_clean_g1.json")
m0 = g["M0r_summary"]["mean"]
rows = []


def row(label, tie, strict, pub, mark=""):
    rows.append(f"{label}{mark} & {f(tie)} & {f(strict)} & {pub} \\\\")


row("M1 V-JEPA ViT-L, fp32", val("g1_m1_clean_acc"), val("clean.M1_fp32.strict"),
    r"$\approx$98$^{\rm a}$")
row("M1 V-JEPA ViT-L, fp16", val("m1_fp16_clean_acc"), val("clean.M1_fp16.strict"), "--")
row("M1H V-JEPA ViT-H (diagn.)", val("g1_vith_clean_acc"), val("clean.M1H_fp16.strict"), "--", "$^{\\rm b}$")
row("M2 V-JEPA 2 ViT-L", val("m2_new_acc"), val("clean.M2_mi0.strict"), "--")
rows.append("M3 VideoMAE V2 & \\multicolumn{2}{c}{\\textit{not run}} & -- \\\\")
V("m3.*")
row("M0r random init (3)", 100 * m0["tiehalf_mean"], 100 * m0["strict_mean"], "expected $\\approx$50")
row("B1 frame difference", val("clean.B1_P2.tiehalf"), val("clean.B1_P2.strict"), "expected $\\approx$50")
row("B2 copy-last-frame", val("b2_clean_acc"), val("clean.B2_P2.strict"), "--")
old = [f"M2 old run (mask idx 1)$^{{\\rm c}}$ & {f(val('m2_old_acc'))} & {f(val('clean.M2_old.strict'))} & -- \\\\"]

d = val("m1_minus_b2_diff"); dc = ci("m1_minus_b2_ci", "m1_minus_b2_ci")
tex = r"""\begin{table}[t]
\caption{Reproduction on IntPhys dev (180 pairs, 3 blocks): pairwise accuracy in \% of the impossible video having the higher surprise (mean aggregation; tie-half = primary, strict = ties counted wrong). Published: Garrido et al.\ headline $\approx$98\%, obtained with checkpoints that are not released; the gap to our public checkpoints is unexplained and we make no reproduction claim. M1 minus B2 (paired): """ + f"{f(d, 1, True)} pp [{f(dc[0])}, {f(dc[1])}]" + r""".}
\label{tab:t1}
\centering\scriptsize
\setlength{\tabcolsep}{2.5pt}
\begin{tabular}{@{}lrrr@{}}
\toprule
Model & Tie-half & Strict & Published \\
\midrule
""" + "\n".join(rows) + r"""
\midrule
\multicolumn{4}{@{}l}{\textit{Superseded, disclosure only (not the M2 number)}} \\
""" + "\n".join(old) + r"""
\bottomrule
\end{tabular}
\vspace{2pt}

\raggedright\scriptsize $^{\rm a}$Literature value, not our run. $^{\rm b}$Prereg-tau tie-half 88.3; the 88.1 in the pre-registration text is the superseded fixed-$\tau$ figure (strict 87.8). $^{\rm c}$Wrapper deviation (query mask index 1), excluded from every M2 contrast.
\end{table}
"""
p = write_tex("t1_reproduction.tex", tex)
write_sidecar("T1", "scripts/figs/t1_reproduction.py", ["paper/tables/t1_reproduction.tex"],
              extra=dict(notes=["M0r row from results/analysis/p4/p4_clean_g1.json M0r_summary.mean (no VERIFIED key; mean over 3 inits)",
                                "Published column = literature value (98%) from docs/PREREGISTRATION.md s0 / notes/PROTOCOL_NOTES.md, not VERIFIED",
                                "M3 row = pending (m3.* pending in VERIFIED)",
                                "g1_vith_clean_acc and clean.B1_P2.tiehalf carry status mismatch (superseded-tau convention in analysis files); prereg-tau value used"]))
print(p)
