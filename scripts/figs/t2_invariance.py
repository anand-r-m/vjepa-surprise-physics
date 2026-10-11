"""T2 Invariance (H1). T2a: high strength, M1 + M2 (descriptive). T2b: dose-response rows (low/mid/high), M2 low/mid pending.
No driver verdict labels are printed: only dAcc, flip rate, and flip minus the dither floor f0. fps_halve is not tabulated
(design error: its edited input is bit-identical to the skip-4 clean reference), mentioned in a footnote.
 -> paper/tables/t2_invariance.tex, paper/tables/t2b_invariance_dose.tex"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import *

EDITS = [("brightness", "Brightness"), ("noise", "Noise"), ("blur", "Blur"), ("jpeg", "JPEG"), ("zoom", "Zoom (crop)$^{\\rm a}$"), ("hflip", "Horiz.\\ flip")]
LV = ["low", "mid", "high"]


def cells_high(m, e):
    k = f"h1.{m}.{e}"
    return (val(k + ".dacc_pp"), ci(k + ".dacc_pp"), val(k + ".flip_pct"), val(k + ".flip_minus_f0_pp"), ci(k + ".flip_minus_f0_pp"),
            val(k + ".holm14_dacc"), val(k + ".holm14_flip"), val(k + ".n"))


def fmt_high(m, e):
    d, dc, fl, ex, exc, p1, p2, n = cells_high(m, e)
    return [fci(d, dc, 1, True), f(fl), fci(ex, exc, 1, True), f"{fp(p1)} / {fp(p2)}"]


# ---------------------------------------------------------------- T2a
rows = []
for e, lab in EDITS:
    n = val(f"h1.M1.{e}.n")
    rows.append(f"{lab} ({int(n)}) & " + " & ".join(fmt_high("M1", e)) + " & " + " & ".join(fmt_high("M2", e)) + r" \\")
f0 = {m: val(f"h1.{m}.f0_pct") for m in ("M1", "M2")}
f0s = val("h1_f0_strict")
hdr = r"""\begin{table*}[t]
\caption{Invariance (H1), high strength. $\Delta$Acc = accuracy under the same edit applied to both videos of a pair minus clean accuracy, in percentage points (scene-cluster 95\% CI); flip = share of pairs whose verdict changes; flip$-f_0$ = flip rate minus the dither floor $f_0$ (a perturbation that should not matter at all): M1 $f_0$ = """ + f(f0["M1"]) + r"""\% (strict """ + f(f0s) + r"""\%), M2 $f_0$ = """ + f(f0["M2"]) + r"""\%. A flip rate near $f_0$ is what an invisible perturbation produces. Holm-14 adjusted $p$ for $\Delta$Acc / flip. M1 is the confirmatory row; M2 is \textbf{descriptive only} (clean accuracy below the 80\% eligibility rule).}
\label{tab:t2}
\centering\scriptsize
\setlength{\tabcolsep}{1.9pt}
\begin{tabular}{@{}lrrrrrrrr@{}}
\toprule
 & \multicolumn{4}{c}{M1 V-JEPA ViT-L} & \multicolumn{4}{c}{M2 V-JEPA 2 (descriptive)} \\
\cmidrule(lr){2-5}\cmidrule(lr){6-9}
Edit ($n$ pairs) & $\Delta$Acc [CI] & Flip & Flip$-f_0$ [CI] & $p$ ($\Delta$/flip) & $\Delta$Acc [CI] & Flip & Flip$-f_0$ [CI] & $p$ ($\Delta$/flip) \\
\midrule
"""
ident = val("h1.M1.fps_halve.identical_to_skip4_clean")
assert ident is True
foot = r"""\bottomrule
\end{tabular}

\vspace{2pt}
\raggedright\scriptsize Flip and flip$-f_0$ in \%, $\Delta$Acc in pp. $^{\rm a}$Pairs where the crop keeps the scene support (112 of 180); the other 68 are excluded for both models. Frame-rate halving is not tabulated: its edited input is bit-identical to the skip-4 clean reference, so the edit is degenerate by design (a design error in the edit list, reported here for completeness).
\end{table*}
"""
write_tex("t2_invariance.tex", hdr + "\n".join(rows) + "\n" + foot)

# ---------------------------------------------------------------- T2b dose
rows = []
for e, lab in EDITS[:5]:
    for lv in LV:
        # M1
        k = f"dose.h1.M1.{e}-{lv}"
        d, dc, fl, p1, p2, n = val(k + ".dacc_pp"), ci(k + ".dacc_pp"), val(k + ".flip_pct"), val(k + ".holm30_dacc"), val(k + ".holm30_flip"), val(k + ".n")
        ex = None if fl is None else fl - f0["M1"]     # derived: flip minus f0 (no CI for low/mid)
        c1 = [fci(d, dc, 1, True), f(fl), f(ex, 1, True), f"{fp(p1)} / {fp(p2)}"]
        # M2: high from the H1 keys; low/mid from m2.dose.h1.* (pending until the runs land and the verifier writes them)
        if lv == "high":
            c2 = fmt_high("M2", e)
            c2 = [c2[0], c2[1], c2[2].split(" [")[0], c2[3]]
        else:
            mk = f"m2.dose.h1.{e}.{lv}"
            md, mfl = val(mk + ".dacc_pp"), val(mk + ".flip_pct")
            if md is None:
                V(mk + ".dacc_pp")
            mp = [val(mk + ".holm30_dacc"), val(mk + ".holm30_flip")]
            c2 = [fci(md, ci(mk + ".dacc_pp"), 1, True), f(mfl), f(None if mfl is None else mfl - f0["M2"], 1, True),
                  PEND if mp[0] is None else f"{fp(mp[0])} / {fp(mp[1])}"]
        first = lab if lv == "low" else ""
        rows.append(f"{first} & {lv} ({int(n)}) & " + " & ".join(c1) + " & " + " & ".join(c2) + r" \\")
    rows.append(r"\addlinespace[1pt]")
hdr = r"""\begin{table*}[t]
\caption{Invariance dose-response (A3): the same quantities as Table~\ref{tab:t2} of the main text at low / mid / high strength. Holm-adjusted $p$: 30-test family for the M1 columns (all graded cells), 22-test family for the M2 columns (11 seed-1 cells, two tests each; JPEG and zoom exist at high strength only). Flip$-f_0$ for low and mid is the difference of the two rates (no CI). M1 $f_0$ = """ + f(f0["M1"]) + r"""\%, M2 $f_0$ = """ + f(f0["M2"]) + r"""\%. The five ``pend.'' cells are M2 JPEG and zoom at low and mid strength, which were not run (GPU quota).}
\label{tab:t2b}
\centering\scriptsize
\setlength{\tabcolsep}{1.9pt}
\begin{tabular}{@{}llrrrrrrrr@{}}
\toprule
 & & \multicolumn{4}{c}{M1 V-JEPA ViT-L} & \multicolumn{4}{c}{M2 V-JEPA 2 (descriptive)} \\
\cmidrule(lr){3-6}\cmidrule(lr){7-10}
Edit & Strength ($n$) & $\Delta$Acc [CI] & Flip & Flip$-f_0$ & $p$ ($\Delta$/flip) & $\Delta$Acc [CI] & Flip & Flip$-f_0$ & $p$ ($\Delta$/flip) \\
\midrule
"""
foot = r"""\bottomrule
\end{tabular}
\end{table*}
"""
write_tex("t2b_invariance_dose.tex", hdr.replace("\\begin{table*}[t]", "\\begin{table*}[t]") + "\n".join(rows) + "\n" + foot)
write_sidecar("T2/T2b", "scripts/figs/t2_invariance.py", ["paper/tables/t2_invariance.tex", "paper/tables/t2b_invariance_dose.tex"],
              extra=dict(notes=["T2 absolute accuracy column omitted: dAcc is the pre-registered quantity and the zoom subset has a different baseline",
                                "T2b flip-f0 for low/mid is flip_pct - f0_pct computed in the script (arithmetic on two VERIFIED keys)",
                                "M2 low/mid read keys m2.dose.h1.<edit>.<low|mid>.{dacc_pp,flip_pct,holm30_dacc,holm30_flip}; pending until the verifier writes them; rerun the script to fill",
                                "no multirow dependency"]))
