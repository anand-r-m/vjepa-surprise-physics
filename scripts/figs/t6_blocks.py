"""T6 Clean accuracy by block: IntPhys dev blocks O1-O3 (M1, M2) and IntPhys 2 Main by category (M1, B1, B2, B3), tie-half, mean aggregation.
 -> paper/tables/t6_blocks.tex"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import *

cl = jload("results/analysis/p4/clean.json")["models"]
dev = []
for m, lab in (("M1", "M1 V-JEPA ViT-L"), ("M2", "M2 V-JEPA 2 (descr.)")):
    pb = cl[m]["mean"]["per_block"]
    dev.append(f"{lab} & " + " & ".join(f(100 * pb[b]["acc_tiehalf"]) for b in ("O1", "O2", "O3")) + f" & {f(100 * cl[m]['mean']['acc_tiehalf'])} \\\\")
cat = ["continuity", "immutability", "permanence", "solidity"]
main = []
for m, lab in (("M1", "M1 V-JEPA ViT-L"), ("B1", "B1 frame diff."), ("B2", "B2 copy-last"), ("B3", "B3 target-feat.")):
    k = f"ip2main.{m}.all"
    main.append(f"{lab} & " + " & ".join(f(val(f"{k}.{c}.tiehalf")) for c in cat) + f" & {fci(val(k + '.tiehalf'), ci(k + '.tiehalf'))} \\\\")
n = val("ip2main.M1.all.n_pairs")
tex = r"""\begin{table}[t]
\caption{Clean pairwise accuracy (\%, tie-half) by block. Top: IntPhys dev, 60 pairs per block, mean aggregation. Bottom: IntPhys 2 Main (""" + f"{int(n)}" + r""" pairs, evaluation only, descriptive), by physical-principle category; last column all pairs with 95\% CI. All Main scores, including the baselines, are near chance.}
\label{tab:t6}
\centering\scriptsize
\setlength{\tabcolsep}{2.2pt}
\begin{tabular}{@{}lrrrr@{}}
\toprule
\multicolumn{5}{@{}l}{\textit{IntPhys dev}} \\
Model & O1 & O2 & O3 & All \\
\midrule
""" + "\n".join(dev) + r"""
\midrule
\multicolumn{5}{@{}l}{\textit{IntPhys 2 Main}} \\
Model & Continuity & Immut. & Perman. & Solidity \\
\midrule
""" + "\n".join(m_.replace(" \\\\", "") .rsplit(" & ", 1)[0] + " \\\\" for m_ in main) + r"""
\midrule
\multicolumn{5}{@{}l}{\textit{All Main pairs [95\% CI]}} \\
""" + "\n".join(f"{m_.split(' & ')[0]} & \\multicolumn{{4}}{{l}}{{{m_.rsplit(' & ', 1)[1].replace(' \\\\', '')}}} \\\\" for m_ in main) + r"""
\bottomrule
\end{tabular}
\end{table}
"""
write_tex("t6_blocks.tex", tex)
I("results/analysis/exploratory/ip2main/IP2MAIN_M1_clean_descriptive.json")
write_sidecar("T6", "scripts/figs/t6_blocks.py", ["paper/tables/t6_blocks.tex"],
              extra=dict(notes=["IntPhys dev per-block accuracies from results/analysis/p4/clean.json (no VERIFIED key); Main values from VERIFIED ip2main.*"]))
