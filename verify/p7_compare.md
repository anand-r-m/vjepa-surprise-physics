# P7 comparison: verifier recompute vs results/analysis (written AFTER verify/p7_recompute.*)

Compared 699 quantities: match 695, MISMATCH 3, info 1, unmapped 0.

Tolerances: accuracy/rate/detection 0.001; AUROC and A/D 0.002; bootstrap CI bounds 0.01; bootstrap p within Monte-Carlo error (8 SE of a 10,000-draw proportion + 3e-4; Holm-adjusted p scaled by the Holm multiplier); exact sign-test p 1e-5; counts exact; tau 1e-8 to 1e-9. Bootstrap draws differ (own RNG streams), so CI bounds and p differ by MC noise only.

## Mismatches (cause)

| quantity | verifier | analysis | abs diff | tol | likely cause |
|---|---|---|---|---|---|
| ViT-H tie-half under prereg tau (mine) vs analysis file | 0.883333 | 0.880556 | 0.00277778 | 0.001 | results/analysis/p2_vith_g1.json (and PREREG s7, "88.1") score ViT-H tie-half with the SUPERSEDED fixed tau = 1e-4 (3 ties, 158.5 credits); under the prereg scale-relative tau_m = 2e-4 x median = 1.195e-4 there are 4 ties and 159 credits = 88.33. Reproduced exactly: fixed-tau 0.88056 matches the file (row above). Strict (87.8) is identical. Convention difference, not a data difference. |
| P2 B1 tie-half (analysis file; old fixed tau?) | 0.580556 | 0.5 | 0.0805556 | 0.001 | p2_clean_g1.json B1 "acc" 0.500 uses the superseded fixed 1e-4 tau (96 ties); under the prereg tau 58.1 (PREREG s0 quotes 58.1/58.6 under the prereg tau). Strict 57.2 matches. Convention difference. |
| P2 B2 tie-half (analysis file; old fixed tau?) | 0.761111 | 0.625 | 0.136111 | 0.001 | p2_clean_g1.json B2 "acc" 0.625 is the superseded fixed-tau figure (59 ties); under the prereg tau 76.1 (PREREG s0 explicitly records 62.5 as the old-tau figure). Strict 76.1 matches. Convention difference. |

No other mismatch: all remaining quantities agree within tolerance, including one correction made during this pass: zoom dose-response low/mid initially used the 112-pair high-strength retention set (22 / 8 pairs too few vs the analysis); the analysis uses scale-specific retention (134 at 0.9, 120 at 0.8, 112 stored at 0.7), which my pixel retention reproduces exactly (134 / 120), after which every dose cell matched.

Informational (not mismatches):

- Zoom high-strength keep set: stored matches.json retention gives 112 (analysis and PLACEHOLDERS h1_zoom_n); my own pixel retention at 0.7 gives 110 (cm_win) - the p6 finding, unchanged.
- M2 H1 noise: p_dacc_cluster 0.0132 (mine) vs 0.0174 (analysis), Holm-14 0.132 vs 0.174: MC noise on the same data (both far above the Holm-significance line only after Holm; neither crosses 0.05 after Holm). Decision labels unaffected.
- Onset-aligned D_1 Holm-2: 0.0026 (mine) vs 0.0018 (analysis); raw p 0.0013 vs 0.0009: MC noise; same conclusion.
- H1 sign-family Holm values differ at the 4th decimal where the bootstrap flip-vs-floor p enters the family; tolerance 0.03; all matched.

## Largest normalised deviations among matches (diff / tol)

| quantity | verifier | analysis | diff | tol |
|---|---|---|---|---|
| EXPL halve_hold p_dacc | 0.5066 | 0.525 | 0.0184 | 0.0403 |
| H1 dose jpeg-low p_dacc | 0.012 | 0.0166 | 0.0046 | 0.0105214 |
| H1 M1 brightness p_dacc_cluster | 0.0786 | 0.07 | 0.0086 | 0.0218291 |
| H1 dose brightness-high p_dacc | 0.0786 | 0.07 | 0.0086 | 0.0218291 |
| H1 M2 noise p_dacc_cluster | 0.0132 | 0.0174 | 0.0042 | 0.0107605 |
| H1 strict brightness p_dacc_cluster | 0.2978 | 0.2836 | 0.0142 | 0.0368833 |
| H1 M1 zoom p_dacc_cluster | 0.9248 | 0.9386 | 0.0138 | 0.0403 |
| H1 dose zoom-high p_dacc | 0.9248 | 0.9386 | 0.0138 | 0.0403 |
| H1 M2 brightness p_dacc_cluster | 0.7596 | 0.7722 | 0.0126 | 0.0403 |
| H1 dose blur-mid p_flip | 0.0983 | 0.106 | 0.0077 | 0.024927 |
| H1 M1 blur dAcc CI hi | -0.0944444 | -0.0972222 | 0.00277778 | 0.01 |
| T1 CI hi | 0.105556 | 0.102778 | 0.00277778 | 0.01 |

## Full table

| quantity | verifier | analysis | abs diff | tol | status |
|---|---|---|---|---|---|
| M2 mi0 clean tie-half | 0.608333 | 0.608333 | 0 | 0.001 | match |
| M2 mi0 clean strict | 0.605556 | 0.605556 | 0 | 0.001 | match |
| M2 mi0 ties | 17 | 17 | 0 | 0 | match |
| M2 mi0 tau | 0.000110861 | 0.000110861 | 8.32027e-13 | 1e-08 | match |
| M2 mi1 old clean tie-half | 0.469444 | 0.469444 | 0 | 0.001 | match |
| M2 mi1 old strict | 0.466667 | 0.466667 | 0 | 0.001 | match |
| H1 M1 f0 | 0.214815 | 0.214815 | 0 | 0.001 | match |
| H1 M1 brightness n | 180 | 180 | 0 | 0 | match |
| H1 M1 brightness dAcc | -0.0240741 | -0.0240741 | 0 | 0.001 | match |
| H1 M1 brightness flip | 0.124074 | 0.124074 | 0 | 0.001 | match |
| H1 M1 brightness flip-f0 | -0.0907407 | -0.0907407 | 0 | 0.001 | match |
| H1 M1 brightness dAcc CI lo | -0.0509259 | -0.0518519 | 0.000925926 | 0.01 | match |
| H1 M1 brightness dAcc CI hi | 0.00277778 | 0.00185185 | 0.000925926 | 0.01 | match |
| H1 M1 brightness p_dacc_cluster | 0.0786 | 0.07 | 0.0086 | 0.0218291 | match |
| H1 M1 brightness p_flip_cluster | 0.9999 | 0.9999 | 0 | 0.0403 | match |
| H1 M1 brightness Holm-14 dAcc | 0.6288 | 0.56 | 0.0688 | 0.5642 | match |
| H1 M1 brightness Holm-14 flip | 1 | 1 | 0 | 0.5642 | match |
| H1 M1 brightness sign p | 0.065994 | 0.065994 | 0 | 1e-05 | match |
| H1 M1 brightness Holm-14 sign-fam sign | 0.527952 | 0.527952 | 0 | 0.03 | match |
| H1 M1 noise n | 180 | 180 | 0 | 0 | match |
| H1 M1 noise dAcc | -0.205556 | -0.205556 | 0 | 0.001 | match |
| H1 M1 noise flip | 0.377778 | 0.377778 | 0 | 0.001 | match |
| H1 M1 noise flip-f0 | 0.162963 | 0.162963 | 0 | 0.001 | match |
| H1 M1 noise dAcc CI lo | -0.257407 | -0.258333 | 0.000925926 | 0.01 | match |
| H1 M1 noise dAcc CI hi | -0.152778 | -0.153704 | 0.000925926 | 0.01 | match |
| H1 M1 noise p_dacc_cluster | 0 | 0 | 0 | 0.00109996 | match |
| H1 M1 noise p_flip_cluster | 0 | 0 | 0 | 0.00109996 | match |
| H1 M1 noise Holm-14 dAcc | 0 | 0 | 0 | 0.0153994 | match |
| H1 M1 noise Holm-14 flip | 0 | 0 | 0 | 0.0153994 | match |
| H1 M1 noise sign p | 1.00986e-12 | 1.00986e-12 | 0 | 1e-05 | match |
| H1 M1 noise Holm-14 sign-fam sign | 1.31282e-11 | 1.31282e-11 | 0 | 0.03 | match |
| H1 M1 blur n | 180 | 180 | 0 | 0 | match |
| H1 M1 blur dAcc | -0.144444 | -0.144444 | 0 | 0.001 | match |
| H1 M1 blur flip | 0.311111 | 0.311111 | 0 | 0.001 | match |
| H1 M1 blur flip-f0 | 0.0962963 | 0.0962963 | 0 | 0.001 | match |
| H1 M1 blur dAcc CI lo | -0.194444 | -0.194444 | 0 | 0.01 | match |
| H1 M1 blur dAcc CI hi | -0.0944444 | -0.0972222 | 0.00277778 | 0.01 | match |
| H1 M1 blur p_dacc_cluster | 0 | 0 | 0 | 0.00109996 | match |
| H1 M1 blur p_flip_cluster | 0.0001 | 0.0002 | 0.0001 | 0.00143126 | match |
| H1 M1 blur Holm-14 dAcc | 0 | 0 | 0 | 0.0153994 | match |
| H1 M1 blur Holm-14 flip | 0.001 | 0.002 | 0.001 | 0.0542378 | match |
| H1 M1 blur sign p | 1.24545e-06 | 1.24545e-06 | 0 | 1e-05 | match |
| H1 M1 blur Holm-14 sign-fam sign | 1.49454e-05 | 1.49454e-05 | 0 | 0.03 | match |
| H1 M1 jpeg n | 180 | 180 | 0 | 0 | match |
| H1 M1 jpeg dAcc | -0.108333 | -0.108333 | 0 | 0.001 | match |
| H1 M1 jpeg flip | 0.283333 | 0.283333 | 0 | 0.001 | match |
| H1 M1 jpeg flip-f0 | 0.0685185 | 0.0685185 | 0 | 0.001 | match |
| H1 M1 jpeg dAcc CI lo | -0.163889 | -0.163889 | 0 | 0.01 | match |
| H1 M1 jpeg dAcc CI hi | -0.0527778 | -0.0555556 | 0.00277778 | 0.01 | match |
| H1 M1 jpeg p_dacc_cluster | 0 | 0 | 0 | 0.00109996 | match |
| H1 M1 jpeg p_flip_cluster | 0.0171 | 0.017 | 0.0001 | 0.0106715 | match |
| H1 M1 jpeg Holm-14 dAcc | 0 | 0 | 0 | 0.0153994 | match |
| H1 M1 jpeg Holm-14 flip | 0.1539 | 0.153 | 0.0009 | 0.408355 | match |
| H1 M1 jpeg sign p | 0.0017692 | 0.0017692 | 0 | 1e-05 | match |
| H1 M1 jpeg Holm-14 sign-fam sign | 0.017692 | 0.017692 | 0 | 0.03 | match |
| H1 M1 zoom n | 112 | 112 | 0 | 0 | match |
| H1 M1 zoom dAcc | -0.00446429 | -0.00446429 | 0 | 0.001 | match |
| H1 M1 zoom flip | 0.142857 | 0.142857 | 0 | 0.001 | match |
| H1 M1 zoom flip-f0 | -0.0892857 | -0.0892857 | 0 | 0.001 | match |
| H1 M1 zoom dAcc CI lo | -0.0564516 | -0.0560345 | 0.00041713 | 0.01 | match |
| H1 M1 zoom dAcc CI hi | 0.0487838 | 0.0491071 | 0.000323341 | 0.01 | match |
| H1 M1 zoom p_dacc_cluster | 0.9248 | 0.9386 | 0.0138 | 0.0403 | match |
| H1 M1 zoom p_flip_cluster | 0.9921 | 0.9901 | 0.002 | 0.0403 | match |
| H1 M1 zoom Holm-14 dAcc | 1 | 1 | 0 | 0.5642 | match |
| H1 M1 zoom Holm-14 flip | 1 | 1 | 0 | 0.5642 | match |
| H1 M1 zoom sign p | 1 | 1 | 0 | 1e-05 | match |
| H1 M1 zoom Holm-14 sign-fam sign | 1 | 1 | 0 | 0.03 | match |
| H1 M1 hflip n | 180 | 180 | 0 | 0 | match |
| H1 M1 hflip dAcc | 0.0222222 | 0.0222222 | 0 | 0.001 | match |
| H1 M1 hflip flip | 0.15 | 0.15 | 0 | 0.001 | match |
| H1 M1 hflip flip-f0 | -0.0648148 | -0.0648148 | 0 | 0.001 | match |
| H1 M1 hflip dAcc CI lo | -0.0222222 | -0.0194444 | 0.00277778 | 0.01 | match |
| H1 M1 hflip dAcc CI hi | 0.0666667 | 0.0666667 | 0 | 0.01 | match |
| H1 M1 hflip p_dacc_cluster | 0.3446 | 0.342 | 0.0026 | 0.038319 | match |
| H1 M1 hflip p_flip_cluster | 0.9782 | 0.9779 | 0.0003 | 0.0403 | match |
| H1 M1 hflip Holm-14 dAcc | 1 | 1 | 0 | 0.5642 | match |
| H1 M1 hflip Holm-14 flip | 1 | 1 | 0 | 0.5642 | match |
| H1 M1 hflip sign p | 0.442068 | 0.442068 | 0 | 1e-05 | match |
| H1 M1 hflip Holm-14 sign-fam sign | 1 | 1 | 0 | 0.03 | match |
| H1 M1 fps_halve n | 180 | 180 | 0 | 0 | match |
| H1 M1 fps_halve dAcc | 0 | 0 | 0 | 0.001 | match |
| H1 M1 fps_halve flip | 0 | 0 | 0 | 0.001 | match |
| H1 M1 fps_halve flip-f0 | -0.214815 | -0.214815 | 0 | 0.001 | match |
| H1 M1 fps_halve dAcc CI lo | 0 | 0 | 0 | 0.01 | match |
| H1 M1 fps_halve dAcc CI hi | 0 | 0 | 0 | 0.01 | match |
| H1 M1 fps_halve p_dacc_cluster | 1 | 1 | 0 | 0.0403 | match |
| H1 M1 fps_halve p_flip_cluster | 1 | 1 | 0 | 0.0403 | match |
| H1 M1 fps_halve Holm-14 dAcc | 1 | 1 | 0 | 0.5642 | match |
| H1 M1 fps_halve Holm-14 flip | 1 | 1 | 0 | 0.5642 | match |
| H1 M1 fps_halve sign p | 1 | 1 | 0 | 1e-05 | match |
| H1 M1 fps_halve Holm-14 sign-fam sign | 1 | 1 | 0 | 0.03 | match |
| H1 M2 f0 | 0.246296 | 0.246296 | 0 | 0.001 | match |
| H1 M2 brightness n | 180 | 180 | 0 | 0 | match |
| H1 M2 brightness dAcc | -0.0037037 | -0.0037037 | 0 | 0.001 | match |
| H1 M2 brightness flip | 0.153704 | 0.153704 | 0 | 0.001 | match |
| H1 M2 brightness flip-f0 | -0.0925926 | -0.0925926 | 0 | 0.001 | match |
| H1 M2 brightness dAcc CI lo | -0.0305556 | -0.0305556 | 0 | 0.01 | match |
| H1 M2 brightness dAcc CI hi | 0.025 | 0.025 | 0 | 0.01 | match |
| H1 M2 brightness p_dacc_cluster | 0.7596 | 0.7722 | 0.0126 | 0.0403 | match |
| H1 M2 brightness p_flip_cluster | 1 | 1 | 0 | 0.0403 | match |
| H1 M2 brightness Holm-14 dAcc | 1 | 1 | 0 | 0.5642 | match |
| H1 M2 brightness Holm-14 flip | 1 | 1 | 0 | 0.5642 | match |
| H1 M2 brightness sign p | 0.222053 | 0.222053 | 0 | 1e-05 | match |
| H1 M2 brightness Holm-14 sign-fam sign | 1 | 1 | 0 | 0.03 | match |
| H1 M2 noise n | 180 | 180 | 0 | 0 | match |
| H1 M2 noise dAcc | -0.0638889 | -0.0638889 | 0 | 0.001 | match |
| H1 M2 noise flip | 0.283333 | 0.283333 | 0 | 0.001 | match |
| H1 M2 noise flip-f0 | 0.037037 | 0.037037 | 0 | 0.001 | match |
| H1 M2 noise dAcc CI lo | -0.114815 | -0.115741 | 0.000925926 | 0.01 | match |
| H1 M2 noise dAcc CI hi | -0.012963 | -0.0111111 | 0.00185185 | 0.01 | match |
| H1 M2 noise p_dacc_cluster | 0.0132 | 0.0174 | 0.0042 | 0.0107605 | match |
| H1 M2 noise p_flip_cluster | 0.0335 | 0.0353 | 0.0018 | 0.015063 | match |
| H1 M2 noise Holm-14 dAcc | 0.132 | 0.174 | 0.042 | 0.428803 | match |
| H1 M2 noise Holm-14 flip | 0.3015 | 0.3177 | 0.0162 | 0.525652 | match |
| H1 M2 noise sign p | 0.129918 | 0.129918 | 2.77556e-17 | 1e-05 | match |
| H1 M2 noise Holm-14 sign-fam sign | 1 | 1 | 0 | 0.03 | match |
| H1 M2 blur n | 180 | 180 | 0 | 0 | match |
| H1 M2 blur dAcc | 0.127778 | 0.127778 | 0 | 0.001 | match |
| H1 M2 blur flip | 0.422222 | 0.422222 | 0 | 0.001 | match |
| H1 M2 blur flip-f0 | 0.175926 | 0.175926 | 0 | 0.001 | match |
| H1 M2 blur dAcc CI lo | 0.0638889 | 0.0638889 | 0 | 0.01 | match |
| H1 M2 blur dAcc CI hi | 0.191667 | 0.194444 | 0.00277778 | 0.01 | match |
| H1 M2 blur p_dacc_cluster | 0 | 0.0004 | 0.0004 | 0.00189968 | match |
| H1 M2 blur p_flip_cluster | 0 | 0 | 0 | 0.00109996 | match |
| H1 M2 blur Holm-14 dAcc | 0 | 0.0048 | 0.0048 | 0.0816094 | match |
| H1 M2 blur Holm-14 flip | 0 | 0 | 0 | 0.0153994 | match |
| H1 M2 blur sign p | 0.00176187 | 0.00176187 | 6.50521e-19 | 1e-05 | match |
| H1 M2 blur Holm-14 sign-fam sign | 0.0211425 | 0.0211425 | 1.04083e-17 | 0.03 | match |
| H1 M2 jpeg n | 180 | 180 | 0 | 0 | match |
| H1 M2 jpeg dAcc | -0.0166667 | -0.0166667 | 0 | 0.001 | match |
| H1 M2 jpeg flip | 0.405556 | 0.405556 | 0 | 0.001 | match |
| H1 M2 jpeg flip-f0 | 0.159259 | 0.159259 | 0 | 0.001 | match |
| H1 M2 jpeg dAcc CI lo | -0.0777778 | -0.0777778 | 0 | 0.01 | match |
| H1 M2 jpeg dAcc CI hi | 0.0444444 | 0.0472222 | 0.00277778 | 0.01 | match |
| H1 M2 jpeg p_dacc_cluster | 0.6118 | 0.6118 | 0 | 0.0403 | match |
| H1 M2 jpeg p_flip_cluster | 0 | 0 | 0 | 0.00109996 | match |
| H1 M2 jpeg Holm-14 dAcc | 1 | 1 | 0 | 0.5642 | match |
| H1 M2 jpeg Holm-14 flip | 0 | 0 | 0 | 0.0153994 | match |
| H1 M2 jpeg sign p | 0.639973 | 0.639973 | 1.11022e-16 | 1e-05 | match |
| H1 M2 jpeg Holm-14 sign-fam sign | 1 | 1 | 0 | 0.03 | match |
| H1 M2 zoom n | 112 | 112 | 0 | 0 | match |
| H1 M2 zoom dAcc | 0.0714286 | 0.0714286 | 0 | 0.001 | match |
| H1 M2 zoom flip | 0.25 | 0.25 | 0 | 0.001 | match |
| H1 M2 zoom flip-f0 | -0.0565476 | -0.0565476 | 5.55112e-17 | 0.001 | match |
| H1 M2 zoom dAcc CI lo | 0.0172414 | 0.0178571 | 0.000615764 | 0.01 | match |
| H1 M2 zoom dAcc CI hi | 0.127551 | 0.127273 | 0.000278293 | 0.01 | match |
| H1 M2 zoom p_dacc_cluster | 0.0114 | 0.012 | 0.0006 | 0.00901082 | match |
| H1 M2 zoom p_flip_cluster | 0.9031 | 0.9062 | 0.0031 | 0.0403 | match |
| H1 M2 zoom Holm-14 dAcc | 0.1254 | 0.132 | 0.0066 | 0.38331 | match |
| H1 M2 zoom Holm-14 flip | 1 | 1 | 0 | 0.5642 | match |
| H1 M2 zoom sign p | 0.0871586 | 0.0871586 | 0 | 1e-05 | match |
| H1 M2 zoom Holm-14 sign-fam sign | 0.871586 | 0.871586 | 0 | 0.03 | match |
| H1 M2 hflip n | 180 | 180 | 0 | 0 | match |
| H1 M2 hflip dAcc | 0.0333333 | 0.0333333 | 0 | 0.001 | match |
| H1 M2 hflip flip | 0.155556 | 0.155556 | 0 | 0.001 | match |
| H1 M2 hflip flip-f0 | -0.0907407 | -0.0907407 | 0 | 0.001 | match |
| H1 M2 hflip dAcc CI lo | -0.00277778 | -0.00277778 | 0 | 0.01 | match |
| H1 M2 hflip dAcc CI hi | 0.0694444 | 0.0694444 | 0 | 0.01 | match |
| H1 M2 hflip p_dacc_cluster | 0.0726 | 0.0744 | 0.0018 | 0.0212937 | match |
| H1 M2 hflip p_flip_cluster | 1 | 0.9997 | 0.0003 | 0.0403 | match |
| H1 M2 hflip Holm-14 dAcc | 0.5808 | 0.5952 | 0.0144 | 0.5642 | match |
| H1 M2 hflip Holm-14 flip | 1 | 1 | 0 | 0.5642 | match |
| H1 M2 hflip sign p | 0.344928 | 0.344928 | 0 | 1e-05 | match |
| H1 M2 hflip Holm-14 sign-fam sign | 1 | 1 | 0 | 0.03 | match |
| H1 M2 fps_halve n | 180 | 180 | 0 | 0 | match |
| H1 M2 fps_halve dAcc | 0 | 0 | 0 | 0.001 | match |
| H1 M2 fps_halve flip | 0 | 0 | 0 | 0.001 | match |
| H1 M2 fps_halve flip-f0 | -0.246296 | -0.246296 | 0 | 0.001 | match |
| H1 M2 fps_halve dAcc CI lo | 0 | 0 | 0 | 0.01 | match |
| H1 M2 fps_halve dAcc CI hi | 0 | 0 | 0 | 0.01 | match |
| H1 M2 fps_halve p_dacc_cluster | 1 | 1 | 0 | 0.0403 | match |
| H1 M2 fps_halve p_flip_cluster | 1 | 1 | 0 | 0.0403 | match |
| H1 M2 fps_halve Holm-14 dAcc | 1 | 1 | 0 | 0.5642 | match |
| H1 M2 fps_halve Holm-14 flip | 1 | 1 | 0 | 0.5642 | match |
| H1 M2 fps_halve sign p | 1 | 1 | 0 | 1e-05 | match |
| H1 M2 fps_halve Holm-14 sign-fam sign | 1 | 1 | 0 | 0.03 | match |
| H2 M2 A | 0.448875 | 0.448875 | 5.55112e-17 | 0.002 | match |
| H2 M2 A CI lo | 0.402909 | 0.402688 | 0.000221258 | 0.01 | match |
| H2 M2 A CI hi | 0.496435 | 0.49629 | 0.000144901 | 0.01 | match |
| H2 M2 A lighting_global | 0.550957 | 0.550957 | 0 | 0.002 | match |
| H2 M2 A lighting_local | 0.356651 | 0.356651 | 0 | 0.002 | match |
| H2 M2 A jolt_base | 0.445962 | 0.445962 | 0 | 0.002 | match |
| H2 M2 A zoom_base | 0.441929 | 0.441929 | 0 | 0.002 | match |
| H2 M2 A0 | 0.6 | 0.6 | 0 | 0.001 | match |
| H2 M2 A_B1 | 0.324127 | 0.324127 | 5.55112e-17 | 0.002 | match |
| H2 M2 A0_B1 | 0.555556 | 0.555556 | 0 | 0.001 | match |
| H2 M2 D_B1 | 0.124748 | 0.124748 | 0 | 0.002 | match |
| H2 M2 D_B1 CI lo | 0.0765134 | 0.0780707 | 0.00155729 | 0.01 | match |
| H2 M2 D_B1 CI hi | 0.172703 | 0.172913 | 0.000210037 | 0.01 | match |
| H2 M2 p_B1 | 9.999e-05 | 9.999e-05 | 0 | 0.00109996 | match |
| H2 M2 Holm-2 B1 | 0.00019998 | 0.00019998 | 0 | 0.0028624 | match |
| H2 M2 A_B2 | 0.376151 | 0.376151 | 5.55112e-17 | 0.002 | match |
| H2 M2 A0_B2 | 0.6 | 0.6 | 0 | 0.001 | match |
| H2 M2 D_B2 | 0.0727238 | 0.0727238 | 0 | 0.002 | match |
| H2 M2 D_B2 CI lo | 0.0199212 | 0.0219245 | 0.00200331 | 0.01 | match |
| H2 M2 D_B2 CI hi | 0.124484 | 0.124761 | 0.000277167 | 0.01 | match |
| H2 M2 p_B2 | 0.0029 | 0.0032 | 0.0003 | 0.00481824 | match |
| H2 M2 Holm-2 B2 | 0.0029 | 0.0032 | 0.0003 | 0.00963647 | match |
| H2 M2 tau | 0.000115661 | 0.000115661 | 0 | 1e-09 | match |
| H2 M2 A excl lighting_global | 0.414847 | 0.414847 | 1.11022e-16 | 0.002 | match |
| H2 M2 A excl lg CI lo | 0.368501 | 0.369775 | 0.00127405 | 0.01 | match |
| H2 M2 A excl lg CI hi | 0.461514 | 0.462018 | 0.000503772 | 0.01 | match |
| H2 M2 D_B1 excl lg | 0.10256 | 0.10256 | 1.11022e-16 | 0.002 | match |
| H2 M2 p_B1 excl lg | 9.999e-05 | 9.999e-05 | 0 | 0.00109996 | match |
| H2 M2 Holm-2 B1 excl lg | 0.00019998 | 0.00019998 | 0 | 0.0028624 | match |
| H2 M2 D_B2 excl lg | 0.0443621 | 0.0443621 | 1.11022e-16 | 0.002 | match |
| H2 M2 p_B2 excl lg | 0.0506 | 0.0477 | 0.0029 | 0.0178344 | match |
| H2 M2 Holm-2 B2 excl lg | 0.0506 | 0.0477 | 0.0029 | 0.0356687 | match |
| H2 M2 outcome | DL | DL | None | 0 | match |
| H3 M2 vflip (a) | 0.719444 | 0.719444 | 0 | 0.001 | match |
| H3 M2 vflip (a) CI lo | 0.644444 | 0.644444 | 0 | 0.01 | match |
| H3 M2 vflip (a) CI hi | 0.788889 | 0.791667 | 0.00277778 | 0.01 | match |
| H3 M2 vflip (b) | 0.727778 | 0.727778 | 0 | 0.001 | match |
| H3 M2 (b) CI lo | 0.652778 | 0.652778 | 0 | 0.01 | match |
| H3 M2 minus M0r vflip | -0.158333 | -0.158333 | 0 | 0.001 | match |
| H3 M2 reversal | 0.463889 | 0.463889 | 0 | 0.001 | match |
| H3 M2 pairwise vflip tie-half | 0.644444 | 0.644444 | 0 | 0.001 | match |
| H3 M2 pairwise rev tie-half | 0.608333 | 0.608333 | 0 | 0.001 | match |
| H3 M2 tau | 0.000115661 | 0.000115661 | 0 | 1e-09 | match |
| H3 M2 G2 | False | False | None | 0 | match |
| H3 M1 vflip (a) | 0.211111 | 0.211111 | 0 | 0.001 | match |
| H3 M1 vflip (b) | 0.258333 | 0.258333 | 0 | 0.001 | match |
| H3 M1 minus M0r vflip | -0.666667 | -0.666667 | 0 | 0.001 | match |
| H3 M1 reversal | 0.608333 | 0.608333 | 0 | 0.001 | match |
| H3 M1 pairwise vflip tie-half | 0.838889 | 0.838889 | 0 | 0.001 | match |
| H2 M1 A | 0.545721 | 0.545721 | 0 | 0.002 | match |
| H2 M1 A CI lo | 0.501041 | 0.501265 | 0.00022399 | 0.01 | match |
| H2 M1 A CI hi | 0.590545 | 0.59115 | 0.00060452 | 0.01 | match |
| H2 M1 A lighting_global | 0.621543 | 0.621543 | 0 | 0.002 | match |
| H2 M1 A lighting_local | 0.480448 | 0.480448 | 0 | 0.002 | match |
| H2 M1 A jolt_base | 0.552824 | 0.552824 | 0 | 0.002 | match |
| H2 M1 A zoom_base | 0.528071 | 0.528071 | 0 | 0.002 | match |
| H2 M1 A0 | 0.722222 | 0.722222 | 0 | 0.001 | match |
| H2 M1 A_B1 | 0.335208 | 0.335208 | 0 | 0.002 | match |
| H2 M1 A0_B1 | 0.555556 | 0.555556 | 0 | 0.001 | match |
| H2 M1 D_B1 | 0.210513 | 0.210513 | 0 | 0.002 | match |
| H2 M1 D_B1 CI lo | 0.159 | 0.160829 | 0.00182912 | 0.01 | match |
| H2 M1 D_B1 CI hi | 0.263227 | 0.26193 | 0.00129784 | 0.01 | match |
| H2 M1 p_B1 | 9.999e-05 | 9.999e-05 | 0 | 0.00109996 | match |
| H2 M1 Holm-2 B1 | 0.00019998 | 0.00019998 | 0 | 0.0028624 | match |
| H2 M1 A_B2 | 0.379343 | 0.379343 | 5.55112e-17 | 0.002 | match |
| H2 M1 A0_B2 | 0.6 | 0.6 | 0 | 0.001 | match |
| H2 M1 D_B2 | 0.166379 | 0.166379 | 5.55112e-17 | 0.002 | match |
| H2 M1 D_B2 CI lo | 0.11634 | 0.116871 | 0.000530382 | 0.01 | match |
| H2 M1 D_B2 CI hi | 0.218506 | 0.216219 | 0.00228697 | 0.01 | match |
| H2 M1 p_B2 | 9.999e-05 | 9.999e-05 | 0 | 0.00109996 | match |
| H2 M1 Holm-2 B2 | 0.00019998 | 0.00019998 | 0 | 0.0028624 | match |
| H2 M1 tau | 0.000108754 | 0.000108754 | 0 | 1e-09 | match |
| H2 M1 A excl lighting_global | 0.520448 | 0.520448 | 1.11022e-16 | 0.002 | match |
| H2 M1 A excl lg CI lo | 0.474823 | 0.475882 | 0.00105898 | 0.01 | match |
| H2 M1 A excl lg CI hi | 0.565283 | 0.566383 | 0.00110022 | 0.01 | match |
| H2 M1 D_B1 excl lg | 0.1941 | 0.1941 | 1.11022e-16 | 0.002 | match |
| H2 M1 p_B1 excl lg | 9.999e-05 | 9.999e-05 | 0 | 0.00109996 | match |
| H2 M1 Holm-2 B1 excl lg | 0.00019998 | 0.00019998 | 0 | 0.0028624 | match |
| H2 M1 D_B2 excl lg | 0.145886 | 0.145886 | 1.11022e-16 | 0.002 | match |
| H2 M1 p_B2 excl lg | 9.999e-05 | 9.999e-05 | 0 | 0.00109996 | match |
| H2 M1 Holm-2 B2 excl lg | 0.00019998 | 0.00019998 | 0 | 0.0028624 | match |
| H2 M1 outcome | DL | DL | None | 0 | match |
| dose-spec low A | 0.593894 | 0.593894 | 1.11022e-16 | 0.002 | match |
| dose-spec low A CI lo | 0.54597 | 0.546408 | 0.000437275 | 0.01 | match |
| dose-spec low A CI hi | 0.64158 | 0.641948 | 0.000368666 | 0.01 | match |
| dose-spec low A_B1 | 0.374706 | 0.374706 | 0 | 0.002 | match |
| dose-spec low A_B2 | 0.430279 | 0.430279 | 5.55112e-17 | 0.002 | match |
| dose-spec low D_1 | 0.219189 | 0.219189 | 1.11022e-16 | 0.002 | match |
| dose-spec low D_2 | 0.163615 | 0.163615 | 1.66533e-16 | 0.002 | match |
| dose-spec low D_1 CI lo | 0.162892 | 0.165064 | 0.00217178 | 0.01 | match |
| dose-spec low D_2 CI lo | 0.107807 | 0.108807 | 0.00100051 | 0.01 | match |
| dose-spec low Holm-6 B1 | 0.00059994 | 0.00059994 | 0 | 0.001 | match |
| dose-spec low Holm-6 B2 | 0.00059994 | 0.00059994 | 0 | 0.001 | match |
| dose-spec low A0 | 0.722222 | 0.722222 | 0 | 0.001 | match |
| dose-spec low lighting_global A | 0.662253 | 0.662253 | 0 | 0.002 | match |
| dose-spec low lighting_global D_1 | 0.239583 | 0.239583 | 0 | 0.002 | match |
| dose-spec low lighting_global D_2 | 0.192052 | 0.192052 | 0 | 0.002 | match |
| dose-spec low lighting_global Holm-24 B1 | 0.00239976 | 0.00239976 | 0 | 0.001 | match |
| dose-spec low lighting_global Holm-24 B2 | 0.00239976 | 0.00239976 | 0 | 0.001 | match |
| dose-spec low lighting_local A | 0.524444 | 0.524444 | 0 | 0.002 | match |
| dose-spec low lighting_local D_1 | 0.210787 | 0.210787 | 0 | 0.002 | match |
| dose-spec low lighting_local D_2 | 0.158333 | 0.158333 | 0 | 0.002 | match |
| dose-spec low lighting_local Holm-24 B1 | 0.00239976 | 0.00239976 | 0 | 0.001 | match |
| dose-spec low lighting_local Holm-24 B2 | 0.00239976 | 0.00239976 | 0 | 0.001 | match |
| dose-spec low jolt_base A | 0.607027 | 0.607027 | 0 | 0.002 | match |
| dose-spec low jolt_base D_1 | 0.216878 | 0.216878 | 0 | 0.002 | match |
| dose-spec low jolt_base D_2 | 0.153503 | 0.153503 | 0 | 0.002 | match |
| dose-spec low jolt_base Holm-24 B1 | 0.00239976 | 0.00239976 | 0 | 0.001 | match |
| dose-spec low jolt_base Holm-24 B2 | 0.00239976 | 0.00239976 | 0 | 0.001 | match |
| dose-spec low zoom_base A | 0.581852 | 0.581852 | 0 | 0.002 | match |
| dose-spec low zoom_base D_1 | 0.209506 | 0.209506 | 0 | 0.002 | match |
| dose-spec low zoom_base D_2 | 0.150571 | 0.150571 | 5.55112e-17 | 0.002 | match |
| dose-spec low zoom_base Holm-24 B1 | 0.00239976 | 0.00239976 | 0 | 0.001 | match |
| dose-spec low zoom_base Holm-24 B2 | 0.00239976 | 0.00239976 | 0 | 0.001 | match |
| dose-spec mid A | 0.545721 | 0.545721 | 0 | 0.002 | match |
| dose-spec mid A CI lo | 0.501041 | 0.501265 | 0.00022399 | 0.01 | match |
| dose-spec mid A CI hi | 0.590545 | 0.59115 | 0.00060452 | 0.01 | match |
| dose-spec mid A_B1 | 0.335208 | 0.335208 | 0 | 0.002 | match |
| dose-spec mid A_B2 | 0.379343 | 0.379343 | 5.55112e-17 | 0.002 | match |
| dose-spec mid D_1 | 0.210513 | 0.210513 | 0 | 0.002 | match |
| dose-spec mid D_2 | 0.166379 | 0.166379 | 5.55112e-17 | 0.002 | match |
| dose-spec mid D_1 CI lo | 0.159 | 0.160829 | 0.00182912 | 0.01 | match |
| dose-spec mid D_2 CI lo | 0.11634 | 0.116871 | 0.000530382 | 0.01 | match |
| dose-spec mid Holm-6 B1 | 0.00059994 | 0.00059994 | 0 | 0.001 | match |
| dose-spec mid Holm-6 B2 | 0.00059994 | 0.00059994 | 0 | 0.001 | match |
| dose-spec mid A0 | 0.722222 | 0.722222 | 0 | 0.001 | match |
| dose-spec mid lighting_global A | 0.621543 | 0.621543 | 0 | 0.002 | match |
| dose-spec mid lighting_global D_1 | 0.259753 | 0.259753 | 0 | 0.002 | match |
| dose-spec mid lighting_global D_2 | 0.227855 | 0.227855 | 0 | 0.002 | match |
| dose-spec mid lighting_global Holm-24 B1 | 0.00239976 | 0.00239976 | 0 | 0.001 | match |
| dose-spec mid lighting_global Holm-24 B2 | 0.00239976 | 0.00239976 | 0 | 0.001 | match |
| dose-spec mid lighting_local A | 0.480448 | 0.480448 | 0 | 0.002 | match |
| dose-spec mid lighting_local D_1 | 0.207346 | 0.207346 | 0 | 0.002 | match |
| dose-spec mid lighting_local D_2 | 0.164367 | 0.164367 | 0 | 0.002 | match |
| dose-spec mid lighting_local Holm-24 B1 | 0.00239976 | 0.00239976 | 0 | 0.001 | match |
| dose-spec mid lighting_local Holm-24 B2 | 0.00239976 | 0.00239976 | 0 | 0.001 | match |
| dose-spec mid jolt_base A | 0.552824 | 0.552824 | 0 | 0.002 | match |
| dose-spec mid jolt_base D_1 | 0.180895 | 0.180895 | 0 | 0.002 | match |
| dose-spec mid jolt_base D_2 | 0.123323 | 0.123323 | 0 | 0.002 | match |
| dose-spec mid jolt_base Holm-24 B1 | 0.00239976 | 0.00239976 | 0 | 0.001 | match |
| dose-spec mid jolt_base Holm-24 B2 | 0.00239976 | 0.00239976 | 0 | 0.001 | match |
| dose-spec mid zoom_base A | 0.528071 | 0.528071 | 0 | 0.002 | match |
| dose-spec mid zoom_base D_1 | 0.194059 | 0.194059 | 0 | 0.002 | match |
| dose-spec mid zoom_base D_2 | 0.149969 | 0.149969 | 5.55112e-17 | 0.002 | match |
| dose-spec mid zoom_base Holm-24 B1 | 0.00239976 | 0.00239976 | 0 | 0.001 | match |
| dose-spec mid zoom_base Holm-24 B2 | 0.00239976 | 0.00239976 | 0 | 0.001 | match |
| dose-spec high A | 0.500517 | 0.500517 | 0 | 0.002 | match |
| dose-spec high A CI lo | 0.457811 | 0.458254 | 0.000443383 | 0.01 | match |
| dose-spec high A CI hi | 0.542774 | 0.543861 | 0.00108664 | 0.01 | match |
| dose-spec high A_B1 | 0.28879 | 0.28879 | 0 | 0.002 | match |
| dose-spec high A_B2 | 0.323881 | 0.323881 | 0 | 0.002 | match |
| dose-spec high D_1 | 0.211727 | 0.211727 | 0 | 0.002 | match |
| dose-spec high D_2 | 0.176636 | 0.176636 | 0 | 0.002 | match |
| dose-spec high D_1 CI lo | 0.16556 | 0.166511 | 0.000951292 | 0.01 | match |
| dose-spec high D_2 CI lo | 0.131208 | 0.132195 | 0.000986626 | 0.01 | match |
| dose-spec high Holm-6 B1 | 0.00059994 | 0.00059994 | 0 | 0.001 | match |
| dose-spec high Holm-6 B2 | 0.00059994 | 0.00059994 | 0 | 0.001 | match |
| dose-spec high A0 | 0.722222 | 0.722222 | 0 | 0.001 | match |
| dose-spec high lighting_global A | 0.554769 | 0.554769 | 0 | 0.002 | match |
| dose-spec high lighting_global D_1 | 0.277948 | 0.277948 | 0 | 0.002 | match |
| dose-spec high lighting_global D_2 | 0.248858 | 0.248858 | 0 | 0.002 | match |
| dose-spec high lighting_global Holm-24 B1 | 0.00239976 | 0.00239976 | 0 | 0.001 | match |
| dose-spec high lighting_global Holm-24 B2 | 0.00239976 | 0.00239976 | 0 | 0.001 | match |
| dose-spec high lighting_local A | 0.459059 | 0.459059 | 0 | 0.002 | match |
| dose-spec high lighting_local D_1 | 0.22716 | 0.22716 | 0 | 0.002 | match |
| dose-spec high lighting_local D_2 | 0.19892 | 0.19892 | 0 | 0.002 | match |
| dose-spec high lighting_local Holm-24 B1 | 0.00239976 | 0.00239976 | 0 | 0.001 | match |
| dose-spec high lighting_local Holm-24 B2 | 0.00239976 | 0.00239976 | 0 | 0.001 | match |
| dose-spec high jolt_base A | 0.50142 | 0.50142 | 0 | 0.002 | match |
| dose-spec high jolt_base D_1 | 0.146785 | 0.146785 | 0 | 0.002 | match |
| dose-spec high jolt_base D_2 | 0.101605 | 0.101605 | 0 | 0.002 | match |
| dose-spec high jolt_base Holm-24 B1 | 0.00239976 | 0.00239976 | 0 | 0.001 | match |
| dose-spec high jolt_base Holm-24 B2 | 0.00239976 | 0.00239976 | 0 | 0.001 | match |
| dose-spec high zoom_base A | 0.486821 | 0.486821 | 0 | 0.002 | match |
| dose-spec high zoom_base D_1 | 0.195015 | 0.195015 | 0 | 0.002 | match |
| dose-spec high zoom_base D_2 | 0.15716 | 0.15716 | 0 | 0.002 | match |
| dose-spec high zoom_base Holm-24 B1 | 0.00239976 | 0.00239976 | 0 | 0.001 | match |
| dose-spec high zoom_base Holm-24 B2 | 0.00239976 | 0.00239976 | 0 | 0.001 | match |
| H1 dose brightness-low n | 180 | 180 | 0 | 0 | match |
| H1 dose brightness-low dAcc | -1.85037e-18 | -1.85037e-18 | 0 | 0.001 | match |
| H1 dose brightness-low flip | 0.0703704 | 0.0703704 | 0 | 0.001 | match |
| H1 dose brightness-low p_dacc | 0.9834 | 0.9748 | 0.0086 | 0.0403 | match |
| H1 dose brightness-low p_flip | 1 | 1 | 0 | 0.0403 | match |
| H1 dose brightness-low Holm-30 dAcc | 1 | 1 | 0 | 1.209 | match |
| H1 dose brightness-low Holm-30 flip | 1 | 1 | 0 | 1.209 | match |
| H1 dose brightness-mid n | 180 | 180 | 0 | 0 | match |
| H1 dose brightness-mid dAcc | 0.00740741 | 0.00740741 | 0 | 0.001 | match |
| H1 dose brightness-mid flip | 0.0962963 | 0.0962963 | 0 | 0.001 | match |
| H1 dose brightness-mid p_dacc | 0.603 | 0.6056 | 0.0026 | 0.0403 | match |
| H1 dose brightness-mid p_flip | 1 | 1 | 0 | 0.0403 | match |
| H1 dose brightness-mid Holm-30 dAcc | 1 | 1 | 0 | 1.209 | match |
| H1 dose brightness-mid Holm-30 flip | 1 | 1 | 0 | 1.209 | match |
| H1 dose brightness-high n | 180 | 180 | 0 | 0 | match |
| H1 dose brightness-high dAcc | -0.0240741 | -0.0240741 | 0 | 0.001 | match |
| H1 dose brightness-high flip | 0.124074 | 0.124074 | 0 | 0.001 | match |
| H1 dose brightness-high p_dacc | 0.0786 | 0.07 | 0.0086 | 0.0218291 | match |
| H1 dose brightness-high p_flip | 0.9999 | 0.9999 | 0 | 0.0403 | match |
| H1 dose brightness-high Holm-30 dAcc | 1 | 1 | 0 | 1.209 | match |
| H1 dose brightness-high Holm-30 flip | 1 | 1 | 0 | 1.209 | match |
| H1 dose noise-low n | 180 | 180 | 0 | 0 | match |
| H1 dose noise-low dAcc | -0.176852 | -0.176852 | 0 | 0.001 | match |
| H1 dose noise-low flip | 0.331481 | 0.331481 | 0 | 0.001 | match |
| H1 dose noise-low p_dacc | 0 | 0 | 0 | 0.00109996 | match |
| H1 dose noise-low p_flip | 0 | 0 | 0 | 0.00109996 | match |
| H1 dose noise-low Holm-30 dAcc | 0 | 0 | 0 | 0.0329988 | match |
| H1 dose noise-low Holm-30 flip | 0 | 0 | 0 | 0.0329988 | match |
| H1 dose noise-mid n | 180 | 180 | 0 | 0 | match |
| H1 dose noise-mid dAcc | -0.199074 | -0.199074 | 0 | 0.001 | match |
| H1 dose noise-mid flip | 0.35 | 0.35 | 0 | 0.001 | match |
| H1 dose noise-mid p_dacc | 0 | 0 | 0 | 0.00109996 | match |
| H1 dose noise-mid p_flip | 0 | 0 | 0 | 0.00109996 | match |
| H1 dose noise-mid Holm-30 dAcc | 0 | 0 | 0 | 0.0329988 | match |
| H1 dose noise-mid Holm-30 flip | 0 | 0 | 0 | 0.0329988 | match |
| H1 dose noise-high n | 180 | 180 | 0 | 0 | match |
| H1 dose noise-high dAcc | -0.205556 | -0.205556 | 0 | 0.001 | match |
| H1 dose noise-high flip | 0.377778 | 0.377778 | 0 | 0.001 | match |
| H1 dose noise-high p_dacc | 0 | 0 | 0 | 0.00109996 | match |
| H1 dose noise-high p_flip | 0 | 0 | 0 | 0.00109996 | match |
| H1 dose noise-high Holm-30 dAcc | 0 | 0 | 0 | 0.0329988 | match |
| H1 dose noise-high Holm-30 flip | 0 | 0 | 0 | 0.0329988 | match |
| H1 dose blur-low n | 180 | 180 | 0 | 0 | match |
| H1 dose blur-low dAcc | -0.0472222 | -0.0472222 | 0 | 0.001 | match |
| H1 dose blur-low flip | 0.183333 | 0.183333 | 0 | 0.001 | match |
| H1 dose blur-low p_dacc | 0.037 | 0.0386 | 0.0016 | 0.0157112 | match |
| H1 dose blur-low p_flip | 0.8626 | 0.863 | 0.0004 | 0.0403 | match |
| H1 dose blur-low Holm-30 dAcc | 0.629 | 0.6562 | 0.0272 | 1.209 | match |
| H1 dose blur-low Holm-30 flip | 1 | 1 | 0 | 1.209 | match |
| H1 dose blur-mid n | 180 | 180 | 0 | 0 | match |
| H1 dose blur-mid dAcc | -0.119444 | -0.119444 | 0 | 0.001 | match |
| H1 dose blur-mid flip | 0.255556 | 0.255556 | 0 | 0.001 | match |
| H1 dose blur-mid p_dacc | 0 | 0 | 0 | 0.00109996 | match |
| H1 dose blur-mid p_flip | 0.0983 | 0.106 | 0.0077 | 0.024927 | match |
| H1 dose blur-mid Holm-30 dAcc | 0 | 0 | 0 | 0.0329988 | match |
| H1 dose blur-mid Holm-30 flip | 1 | 1 | 0 | 1.209 | match |
| H1 dose blur-high n | 180 | 180 | 0 | 0 | match |
| H1 dose blur-high dAcc | -0.144444 | -0.144444 | 0 | 0.001 | match |
| H1 dose blur-high flip | 0.311111 | 0.311111 | 0 | 0.001 | match |
| H1 dose blur-high p_dacc | 0 | 0 | 0 | 0.00109996 | match |
| H1 dose blur-high p_flip | 0.0001 | 0.0002 | 0.0001 | 0.00143126 | match |
| H1 dose blur-high Holm-30 dAcc | 0 | 0 | 0 | 0.0329988 | match |
| H1 dose blur-high Holm-30 flip | 0.0021 | 0.0042 | 0.0021 | 0.164211 | match |
| H1 dose jpeg-low n | 180 | 180 | 0 | 0 | match |
| H1 dose jpeg-low dAcc | 0.0583333 | 0.0583333 | 0 | 0.001 | match |
| H1 dose jpeg-low flip | 0.144444 | 0.144444 | 0 | 0.001 | match |
| H1 dose jpeg-low p_dacc | 0.012 | 0.0166 | 0.0046 | 0.0105214 | match |
| H1 dose jpeg-low p_flip | 0.9917 | 0.9903 | 0.0014 | 0.0403 | match |
| H1 dose jpeg-low Holm-30 dAcc | 0.24 | 0.332 | 0.092 | 1.13923 | match |
| H1 dose jpeg-low Holm-30 flip | 1 | 1 | 0 | 1.209 | match |
| H1 dose jpeg-mid n | 180 | 180 | 0 | 0 | match |
| H1 dose jpeg-mid dAcc | 0.00833333 | 0.00833333 | 0 | 0.001 | match |
| H1 dose jpeg-mid flip | 0.172222 | 0.172222 | 0 | 0.001 | match |
| H1 dose jpeg-mid p_dacc | 0.757 | 0.7526 | 0.0044 | 0.0403 | match |
| H1 dose jpeg-mid p_flip | 0.9122 | 0.9128 | 0.0006 | 0.0403 | match |
| H1 dose jpeg-mid Holm-30 dAcc | 1 | 1 | 0 | 1.209 | match |
| H1 dose jpeg-mid Holm-30 flip | 1 | 1 | 0 | 1.209 | match |
| H1 dose jpeg-high n | 180 | 180 | 0 | 0 | match |
| H1 dose jpeg-high dAcc | -0.108333 | -0.108333 | 0 | 0.001 | match |
| H1 dose jpeg-high flip | 0.283333 | 0.283333 | 0 | 0.001 | match |
| H1 dose jpeg-high p_dacc | 0 | 0 | 0 | 0.00109996 | match |
| H1 dose jpeg-high p_flip | 0.0171 | 0.017 | 0.0001 | 0.0106715 | match |
| H1 dose jpeg-high Holm-30 dAcc | 0 | 0 | 0 | 0.0329988 | match |
| H1 dose jpeg-high Holm-30 flip | 0.3249 | 0.332 | 0.0071 | 1.13923 | match |
| H1 dose zoom-low n | 134 | 134 | 0 | 0 | match |
| H1 dose zoom-low dAcc | 0.0447761 | 0.0447761 | 0 | 0.001 | match |
| H1 dose zoom-low flip | 0.149254 | 0.149254 | 0 | 0.001 | match |
| H1 dose zoom-low p_dacc | 0.0178 | 0.0206 | 0.0028 | 0.0116633 | match |
| H1 dose zoom-low p_flip | 0.9939 | 0.9938 | 0.0001 | 0.0403 | match |
| H1 dose zoom-low Holm-30 dAcc | 0.3249 | 0.3708 | 0.0459 | 1.16825 | match |
| H1 dose zoom-low Holm-30 flip | 1 | 1 | 0 | 1.209 | match |
| H1 dose zoom-mid n | 120 | 120 | 0 | 0 | match |
| H1 dose zoom-mid dAcc | -0.0208333 | -0.0208333 | 0 | 0.001 | match |
| H1 dose zoom-mid flip | 0.15 | 0.15 | 0 | 0.001 | match |
| H1 dose zoom-mid p_dacc | 0.4912 | 0.4934 | 0.0022 | 0.0402965 | match |
| H1 dose zoom-mid p_flip | 0.9946 | 0.9943 | 0.0003 | 0.0403 | match |
| H1 dose zoom-mid Holm-30 dAcc | 1 | 1 | 0 | 1.209 | match |
| H1 dose zoom-mid Holm-30 flip | 1 | 1 | 0 | 1.209 | match |
| H1 dose zoom-high n | 112 | 112 | 0 | 0 | match |
| H1 dose zoom-high dAcc | -0.00446429 | -0.00446429 | 0 | 0.001 | match |
| H1 dose zoom-high flip | 0.142857 | 0.142857 | 0 | 0.001 | match |
| H1 dose zoom-high p_dacc | 0.9248 | 0.9386 | 0.0138 | 0.0403 | match |
| H1 dose zoom-high p_flip | 0.9921 | 0.9901 | 0.002 | 0.0403 | match |
| H1 dose zoom-high Holm-30 dAcc | 1 | 1 | 0 | 1.209 | match |
| H1 dose zoom-high Holm-30 flip | 1 | 1 | 0 | 1.209 | match |
| EXPL onset A | 0.391712 | 0.391712 | 5.55112e-17 | 0.002 | match |
| EXPL onset A CI lo | 0.353834 | 0.353995 | 0.000161555 | 0.01 | match |
| EXPL onset A CI hi | 0.428057 | 0.428418 | 0.000360725 | 0.01 | match |
| EXPL onset A lighting_global | 0.390201 | 0.390201 | 0 | 0.002 | match |
| EXPL onset A lighting_local | 0.459537 | 0.459537 | 0 | 0.002 | match |
| EXPL onset A jolt_base | 0.400149 | 0.400149 | 0 | 0.002 | match |
| EXPL onset A zoom_base | 0.31696 | 0.31696 | 0 | 0.002 | match |
| EXPL onset A0 | 0.722222 | 0.722222 | 0 | 0.001 | match |
| EXPL onset A_B1 | 0.327229 | 0.327229 | 0 | 0.002 | match |
| EXPL onset A0_B1 | 0.583333 | 0.583333 | 0 | 0.001 | match |
| EXPL onset D_B1 | 0.064483 | 0.064483 | 5.55112e-17 | 0.002 | match |
| EXPL onset D_B1 CI lo | 0.0225034 | 0.0227571 | 0.000253762 | 0.01 | match |
| EXPL onset D_B1 CI hi | 0.108758 | 0.108055 | 0.000703189 | 0.01 | match |
| EXPL onset p_B1 | 0.0013 | 0.0009 | 0.0004 | 0.00318257 | match |
| EXPL onset Holm-2 B1 | 0.0026 | 0.0018 | 0.0008 | 0.00874782 | match |
| EXPL onset A_B2 | 0.380761 | 0.380761 | 0 | 0.002 | match |
| EXPL onset A0_B2 | 0.661111 | 0.661111 | 0 | 0.001 | match |
| EXPL onset D_B2 | 0.0109504 | 0.0109504 | 5.55112e-17 | 0.002 | match |
| EXPL onset D_B2 CI lo | -0.0260738 | -0.0271661 | 0.00109227 | 0.01 | match |
| EXPL onset D_B2 CI hi | 0.0505821 | 0.0508772 | 0.000295075 | 0.01 | match |
| EXPL onset p_B2 | 0.277 | 0.2793 | 0.0023 | 0.0361924 | match |
| EXPL onset Holm-2 B2 | 0.277 | 0.2793 | 0.0023 | 0.0723848 | match |
| EXPL onset tau | 0.000108754 | 0.000108754 | 0 | 1e-09 | match |
| EXPL onset A excl lighting_global | 0.392215 | 0.392215 | 0 | 0.002 | match |
| EXPL onset A excl lg CI lo | 0.35674 | 0.357217 | 0.000476209 | 0.01 | match |
| EXPL onset A excl lg CI hi | 0.426401 | 0.426143 | 0.000258531 | 0.01 | match |
| EXPL onset D_B1 excl lg | 0.058534 | 0.058534 | 0 | 0.002 | match |
| EXPL onset p_B1 excl lg | 0.0022 | 0.0021 | 0.0001 | 0.0040482 | match |
| EXPL onset Holm-2 B1 excl lg | 0.0044 | 0.0042 | 0.0002 | 0.0111898 | match |
| EXPL onset D_B2 excl lg | 0.00224451 | 0.00224451 | 0 | 0.002 | match |
| EXPL onset p_B2 excl lg | 0.4377 | 0.4368 | 0.0009 | 0.0399883 | match |
| EXPL onset Holm-2 B2 excl lg | 0.4377 | 0.4368 | 0.0009 | 0.0799766 | match |
| EXPL onset outcome | DL | DL | None | 0 | match |
| EXPL onset B3-free: A0 B1 | 0.583333 | 0.583333 | 0 | 0.001 | match |
| EXPL halve_hold dacc | 0.0194444 | 0.0194444 | 0 | 0.001 | match |
| EXPL halve_hold flip | 0.2 | 0.2 | 0 | 0.001 | match |
| EXPL halve_hold flip_minus_f0 | -0.0148148 | -0.0148148 | 0 | 0.001 | match |
| EXPL halve_hold p_dacc | 0.5066 | 0.525 | 0.0184 | 0.0403 | match |
| EXPL halve_hold p_flip | 0.6698 | 0.6804 | 0.0106 | 0.0403 | match |
| EXPL halve_hold acc halve | 0.827778 | 0.827778 | 0 | 0.001 | match |
| EXPL halve_hold f0 | 0.214815 | 0.214815 | 0 | 0.001 | match |
| Main n pairs | 506 | 506 | 0 | 0 | match |
| Main overlap videos | 8 | 8 | 0 | 0 | match |
| Main overlap pairs | 4 | 4 | 0 | 0 | match |
| Main M1 tau | 0.000111543 | 0.000111543 | 1.60037e-12 | 1e-08 | match |
| Main M1 all tie-half | 0.476285 | 0.476285 | 0 | 0.001 | match |
| Main M1 all strict | 0.478261 | 0.478261 | 0 | 0.001 | match |
| Main M1 all ties | 30 | 30 | 0 | 0 | match |
| Main M1 all boot CI lo | 0.436759 | 0.436759 | 0 | 0.01 | match |
| Main M1 all boot CI hi | 0.516798 | 0.51581 | 0.000988142 | 0.01 | match |
| Main M1 all continuity tie-half | 0.466667 | 0.466667 | 0 | 0.001 | match |
| Main M1 all continuity strict | 0.475 | 0.475 | 0 | 0.001 | match |
| Main M1 all continuity n | 120 | 120 | 0 | 0 | match |
| Main M1 all immutability tie-half | 0.420833 | 0.420833 | 0 | 0.001 | match |
| Main M1 all immutability strict | 0.416667 | 0.416667 | 0 | 0.001 | match |
| Main M1 all immutability n | 120 | 120 | 0 | 0 | match |
| Main M1 all permanence tie-half | 0.495833 | 0.495833 | 0 | 0.001 | match |
| Main M1 all permanence strict | 0.5 | 0.5 | 0 | 0.001 | match |
| Main M1 all permanence n | 120 | 120 | 0 | 0 | match |
| Main M1 all solidity tie-half | 0.513699 | 0.513699 | 0 | 0.001 | match |
| Main M1 all solidity strict | 0.513699 | 0.513699 | 0 | 0.001 | match |
| Main M1 all solidity n | 146 | 146 | 0 | 0 | match |
| Main M1 without_debug_overlap tie-half | 0.476096 | 0.476096 | 0 | 0.001 | match |
| Main M1 without_debug_overlap strict | 0.478088 | 0.478088 | 0 | 0.001 | match |
| Main M1 without_debug_overlap ties | 30 | 30 | 0 | 0 | match |
| Main M1 without_debug_overlap boot CI lo | 0.435771 | 0.435259 | 0.000511787 | 0.01 | match |
| Main M1 without_debug_overlap boot CI hi | 0.516865 | 0.515936 | 0.000928824 | 0.01 | match |
| Main M1 without_debug_overlap continuity tie-half | 0.466667 | 0.466667 | 0 | 0.001 | match |
| Main M1 without_debug_overlap continuity strict | 0.475 | 0.475 | 0 | 0.001 | match |
| Main M1 without_debug_overlap continuity n | 120 | 120 | 0 | 0 | match |
| Main M1 without_debug_overlap immutability tie-half | 0.420833 | 0.420833 | 0 | 0.001 | match |
| Main M1 without_debug_overlap immutability strict | 0.416667 | 0.416667 | 0 | 0.001 | match |
| Main M1 without_debug_overlap immutability n | 120 | 120 | 0 | 0 | match |
| Main M1 without_debug_overlap permanence tie-half | 0.495833 | 0.495833 | 0 | 0.001 | match |
| Main M1 without_debug_overlap permanence strict | 0.5 | 0.5 | 0 | 0.001 | match |
| Main M1 without_debug_overlap permanence n | 120 | 120 | 0 | 0 | match |
| Main M1 without_debug_overlap solidity tie-half | 0.514085 | 0.514085 | 0 | 0.001 | match |
| Main M1 without_debug_overlap solidity strict | 0.514085 | 0.514085 | 0 | 0.001 | match |
| Main M1 without_debug_overlap solidity n | 142 | 142 | 0 | 0 | match |
| Main B1 tau | 6.2967e-06 | 6.2967e-06 | 3.61572e-13 | 1e-08 | match |
| Main B1 all tie-half | 0.511858 | 0.511858 | 0 | 0.001 | match |
| Main B1 all strict | 0.511858 | 0.511858 | 0 | 0.001 | match |
| Main B1 all ties | 8 | 8 | 0 | 0 | match |
| Main B1 all continuity tie-half | 0.570833 | 0.570833 | 0 | 0.001 | match |
| Main B1 all continuity strict | 0.575 | 0.575 | 0 | 0.001 | match |
| Main B1 all continuity n | 120 | 120 | 0 | 0 | match |
| Main B1 all immutability tie-half | 0.4625 | 0.4625 | 0 | 0.001 | match |
| Main B1 all immutability strict | 0.458333 | 0.458333 | 0 | 0.001 | match |
| Main B1 all immutability n | 120 | 120 | 0 | 0 | match |
| Main B1 all permanence tie-half | 0.495833 | 0.495833 | 0 | 0.001 | match |
| Main B1 all permanence strict | 0.5 | 0.5 | 0 | 0.001 | match |
| Main B1 all permanence n | 120 | 120 | 0 | 0 | match |
| Main B1 all solidity tie-half | 0.517123 | 0.517123 | 0 | 0.001 | match |
| Main B1 all solidity strict | 0.513699 | 0.513699 | 0 | 0.001 | match |
| Main B1 all solidity n | 146 | 146 | 0 | 0 | match |
| Main B1 without_debug_overlap tie-half | 0.511952 | 0.511952 | 0 | 0.001 | match |
| Main B1 without_debug_overlap strict | 0.511952 | 0.511952 | 0 | 0.001 | match |
| Main B1 without_debug_overlap ties | 8 | 8 | 0 | 0 | match |
| Main B1 without_debug_overlap continuity tie-half | 0.570833 | 0.570833 | 0 | 0.001 | match |
| Main B1 without_debug_overlap continuity strict | 0.575 | 0.575 | 0 | 0.001 | match |
| Main B1 without_debug_overlap continuity n | 120 | 120 | 0 | 0 | match |
| Main B1 without_debug_overlap immutability tie-half | 0.4625 | 0.4625 | 0 | 0.001 | match |
| Main B1 without_debug_overlap immutability strict | 0.458333 | 0.458333 | 0 | 0.001 | match |
| Main B1 without_debug_overlap immutability n | 120 | 120 | 0 | 0 | match |
| Main B1 without_debug_overlap permanence tie-half | 0.495833 | 0.495833 | 0 | 0.001 | match |
| Main B1 without_debug_overlap permanence strict | 0.5 | 0.5 | 0 | 0.001 | match |
| Main B1 without_debug_overlap permanence n | 120 | 120 | 0 | 0 | match |
| Main B1 without_debug_overlap solidity tie-half | 0.517606 | 0.517606 | 0 | 0.001 | match |
| Main B1 without_debug_overlap solidity strict | 0.514085 | 0.514085 | 0 | 0.001 | match |
| Main B1 without_debug_overlap solidity n | 142 | 142 | 0 | 0 | match |
| Main B2 tau | 1.26654e-05 | 1.26654e-05 | 7.54816e-13 | 1e-08 | match |
| Main B2 all tie-half | 0.518775 | 0.518775 | 0 | 0.001 | match |
| Main B2 all strict | 0.519763 | 0.519763 | 0 | 0.001 | match |
| Main B2 all ties | 19 | 19 | 0 | 0 | match |
| Main B2 all continuity tie-half | 0.508333 | 0.508333 | 0 | 0.001 | match |
| Main B2 all continuity strict | 0.5 | 0.5 | 0 | 0.001 | match |
| Main B2 all continuity n | 120 | 120 | 0 | 0 | match |
| Main B2 all immutability tie-half | 0.466667 | 0.466667 | 0 | 0.001 | match |
| Main B2 all immutability strict | 0.466667 | 0.466667 | 0 | 0.001 | match |
| Main B2 all immutability n | 120 | 120 | 0 | 0 | match |
| Main B2 all permanence tie-half | 0.5375 | 0.5375 | 0 | 0.001 | match |
| Main B2 all permanence strict | 0.541667 | 0.541667 | 0 | 0.001 | match |
| Main B2 all permanence n | 120 | 120 | 0 | 0 | match |
| Main B2 all solidity tie-half | 0.554795 | 0.554795 | 0 | 0.001 | match |
| Main B2 all solidity strict | 0.561644 | 0.561644 | 0 | 0.001 | match |
| Main B2 all solidity n | 146 | 146 | 0 | 0 | match |
| Main B2 without_debug_overlap tie-half | 0.518924 | 0.518924 | 0 | 0.001 | match |
| Main B2 without_debug_overlap strict | 0.51992 | 0.51992 | 0 | 0.001 | match |
| Main B2 without_debug_overlap ties | 19 | 19 | 0 | 0 | match |
| Main B2 without_debug_overlap continuity tie-half | 0.508333 | 0.508333 | 0 | 0.001 | match |
| Main B2 without_debug_overlap continuity strict | 0.5 | 0.5 | 0 | 0.001 | match |
| Main B2 without_debug_overlap continuity n | 120 | 120 | 0 | 0 | match |
| Main B2 without_debug_overlap immutability tie-half | 0.466667 | 0.466667 | 0 | 0.001 | match |
| Main B2 without_debug_overlap immutability strict | 0.466667 | 0.466667 | 0 | 0.001 | match |
| Main B2 without_debug_overlap immutability n | 120 | 120 | 0 | 0 | match |
| Main B2 without_debug_overlap permanence tie-half | 0.5375 | 0.5375 | 0 | 0.001 | match |
| Main B2 without_debug_overlap permanence strict | 0.541667 | 0.541667 | 0 | 0.001 | match |
| Main B2 without_debug_overlap permanence n | 120 | 120 | 0 | 0 | match |
| Main B2 without_debug_overlap solidity tie-half | 0.556338 | 0.556338 | 0 | 0.001 | match |
| Main B2 without_debug_overlap solidity strict | 0.56338 | 0.56338 | 0 | 0.001 | match |
| Main B2 without_debug_overlap solidity n | 142 | 142 | 0 | 0 | match |
| Main B3 tau | 3.8307e-05 | 3.8307e-05 | 3.35002e-12 | 1e-08 | match |
| Main B3 all tie-half | 0.466403 | 0.466403 | 0 | 0.001 | match |
| Main B3 all strict | 0.466403 | 0.466403 | 0 | 0.001 | match |
| Main B3 all ties | 10 | 10 | 0 | 0 | match |
| Main B3 all continuity tie-half | 0.475 | 0.475 | 0 | 0.001 | match |
| Main B3 all continuity strict | 0.475 | 0.475 | 0 | 0.001 | match |
| Main B3 all continuity n | 120 | 120 | 0 | 0 | match |
| Main B3 all immutability tie-half | 0.416667 | 0.416667 | 0 | 0.001 | match |
| Main B3 all immutability strict | 0.425 | 0.425 | 0 | 0.001 | match |
| Main B3 all immutability n | 120 | 120 | 0 | 0 | match |
| Main B3 all permanence tie-half | 0.5 | 0.5 | 0 | 0.001 | match |
| Main B3 all permanence strict | 0.483333 | 0.483333 | 0 | 0.001 | match |
| Main B3 all permanence n | 120 | 120 | 0 | 0 | match |
| Main B3 all solidity tie-half | 0.472603 | 0.472603 | 0 | 0.001 | match |
| Main B3 all solidity strict | 0.479452 | 0.479452 | 0 | 0.001 | match |
| Main B3 all solidity n | 146 | 146 | 0 | 0 | match |
| Main B3 without_debug_overlap tie-half | 0.466135 | 0.466135 | 0 | 0.001 | match |
| Main B3 without_debug_overlap strict | 0.466135 | 0.466135 | 0 | 0.001 | match |
| Main B3 without_debug_overlap ties | 10 | 10 | 0 | 0 | match |
| Main B3 without_debug_overlap continuity tie-half | 0.475 | 0.475 | 0 | 0.001 | match |
| Main B3 without_debug_overlap continuity strict | 0.475 | 0.475 | 0 | 0.001 | match |
| Main B3 without_debug_overlap continuity n | 120 | 120 | 0 | 0 | match |
| Main B3 without_debug_overlap immutability tie-half | 0.416667 | 0.416667 | 0 | 0.001 | match |
| Main B3 without_debug_overlap immutability strict | 0.425 | 0.425 | 0 | 0.001 | match |
| Main B3 without_debug_overlap immutability n | 120 | 120 | 0 | 0 | match |
| Main B3 without_debug_overlap permanence tie-half | 0.5 | 0.5 | 0 | 0.001 | match |
| Main B3 without_debug_overlap permanence strict | 0.483333 | 0.483333 | 0 | 0.001 | match |
| Main B3 without_debug_overlap permanence n | 120 | 120 | 0 | 0 | match |
| Main B3 without_debug_overlap solidity tie-half | 0.471831 | 0.471831 | 0 | 0.001 | match |
| Main B3 without_debug_overlap solidity strict | 0.478873 | 0.478873 | 0 | 0.001 | match |
| Main B3 without_debug_overlap solidity n | 142 | 142 | 0 | 0 | match |
| prec verdicts changed (tie-half) n | 5 | 5 | 0 | 0 | match |
| prec verdicts changed strict n | 1 | 1 | 0 | 0 | match |
| prec max pair-margin diff | 0.000550719 | 0.000550719 | 0 | 1e-07 | match |
| ViT-H tie-half (analysis file, fixed 1e-4 tau) vs mine fixed | 0.880556 | 0.880556 | 0 | 0.001 | match |
| ViT-H tie-half under prereg tau (mine) vs analysis file | 0.883333 | 0.880556 | 0.00277778 | 0.001 | MISMATCH |
| ViT-H strict | 0.877778 | 0.877778 | 0 | 0.001 | match |
| P2 fp32 tie-half | 0.816667 | 0.816667 | 0 | 0.001 | match |
| P2 fp32 strict | 0.805556 | 0.805556 | 0 | 0.001 | match |
| P2 B1 tie-half (analysis file; old fixed tau?) | 0.580556 | 0.5 | 0.0805556 | 0.001 | MISMATCH |
| P2 B2 tie-half (analysis file; old fixed tau?) | 0.761111 | 0.625 | 0.136111 | 0.001 | MISMATCH |
| P2 B1 strict | 0.572222 | 0.572222 | 0 | 0.001 | match |
| P2 B2 strict | 0.761111 | 0.761111 | 0 | 0.001 | match |
| T1 M1(fp16)-B2 diff | 0.0472222 | 0.0472222 | 0 | 0.001 | match |
| T1 CI lo | -0.0111111 | -0.0111111 | 0 | 0.01 | match |
| T1 CI hi | 0.105556 | 0.102778 | 0.00277778 | 0.01 | match |
| M1 fp16 clean tie-half | 0.808333 | 0.808333 | 0 | 0.001 | match |
| M1 fp16 clean strict | 0.811111 | 0.811111 | 0 | 0.001 | match |
| M1 fp16 clean ties | 7 | 7 | 0 | 0 | match |
| H1 M1 strict f0 | 0.155556 | 0.155556 | 0 | 0.001 | match |
| H1 strict brightness dAcc | -0.0166667 | -0.0166667 | 0 | 0.001 | match |
| H1 strict brightness flip | 0.0944444 | 0.0944444 | 0 | 0.001 | match |
| H1 strict brightness p_dacc_cluster | 0.2978 | 0.2836 | 0.0142 | 0.0368833 | match |
| H1 strict brightness p_sign | 0.296206 | 0.296206 | 0 | 1e-05 | match |
| H1 strict brightness Holm-14 dAcc | 1 | 1 | 0 | 0.5642 | match |
| H1 strict brightness Holm-14 sign | 1 | 1 | 0 | 0.03 | match |
| H1 strict noise dAcc | -0.205556 | -0.205556 | 0 | 0.001 | match |
| H1 strict noise flip | 0.261111 | 0.261111 | 0 | 0.001 | match |
| H1 strict noise p_dacc_cluster | 0 | 0 | 0 | 0.00109996 | match |
| H1 strict noise p_sign | 7.63814e-11 | 7.63814e-11 | 0 | 1e-05 | match |
| H1 strict noise Holm-14 dAcc | 0 | 0 | 0 | 0.0153994 | match |
| H1 strict noise Holm-14 sign | 1.06934e-09 | 9.92958e-10 | 7.63814e-11 | 0.03 | match |
| H1 strict blur dAcc | -0.144444 | -0.144444 | 0 | 0.001 | match |
| H1 strict blur flip | 0.233333 | 0.233333 | 0 | 0.001 | match |
| H1 strict blur p_dacc_cluster | 0 | 0 | 0 | 0.00109996 | match |
| H1 strict blur p_sign | 6.87711e-05 | 6.87711e-05 | 1.35525e-20 | 1e-05 | match |
| H1 strict blur Holm-14 dAcc | 0 | 0 | 0 | 0.0153994 | match |
| H1 strict blur Holm-14 sign | 0.000894024 | 0.000825253 | 6.87711e-05 | 0.03 | match |
| H1 strict jpeg dAcc | -0.0944444 | -0.0944444 | 0 | 0.001 | match |
| H1 strict jpeg flip | 0.227778 | 0.227778 | 0 | 0.001 | match |
| H1 strict jpeg p_dacc_cluster | 0.0008 | 0.0016 | 0.0008 | 0.00349744 | match |
| H1 strict jpeg p_sign | 0.0115078 | 0.0115078 | 0 | 1e-05 | match |
| H1 strict jpeg Holm-14 dAcc | 0.0088 | 0.0176 | 0.0088 | 0.151471 | match |
| H1 strict jpeg Holm-14 sign | 0.115078 | 0.115078 | 0 | 0.03 | match |
| H1 strict zoom dAcc | -0.00892857 | -0.00892857 | 0 | 0.001 | match |
| H1 strict zoom flip | 0.116071 | 0.116071 | 0 | 0.001 | match |
| H1 strict zoom p_dacc_cluster | 0.88 | 0.8908 | 0.0108 | 0.0403 | match |
| H1 strict zoom p_sign | 1 | 1 | 0 | 1e-05 | match |
| H1 strict zoom Holm-14 dAcc | 1 | 1 | 0 | 0.5642 | match |
| H1 strict zoom Holm-14 sign | 1 | 1 | 0 | 0.03 | match |
| H1 strict hflip dAcc | 0.0277778 | 0.0277778 | 0 | 0.001 | match |
| H1 strict hflip flip | 0.105556 | 0.105556 | 0 | 0.001 | match |
| H1 strict hflip p_dacc_cluster | 0.2618 | 0.261 | 0.0008 | 0.0354691 | match |
| H1 strict hflip p_sign | 0.359283 | 0.359283 | 0 | 1e-05 | match |
| H1 strict hflip Holm-14 dAcc | 1 | 1 | 0 | 0.5642 | match |
| H1 strict hflip Holm-14 sign | 1 | 1 | 0 | 0.03 | match |
| H1 strict fps_halve dAcc | 0 | 0 | 0 | 0.001 | match |
| H1 strict fps_halve flip | 0 | 0 | 0 | 0.001 | match |
| H1 strict fps_halve p_dacc_cluster | 1 | 1 | 0 | 0.0403 | match |
| H1 strict fps_halve p_sign | 1 | 1 | 0 | 1e-05 | match |
| H1 strict fps_halve Holm-14 dAcc | 1 | 1 | 0 | 0.5642 | match |
| H1 strict fps_halve Holm-14 sign | 1 | 1 | 0 | 0.03 | match |
| M0r vflip detection | 0.877778 | 0.877778 | 0 | 0.001 | match |
| M1 hflip detection | 0.386111 | 0.386111 | 0 | 0.001 | match |
| M0r reversal detection | 0.516667 | 0.516667 | 0 | 0.001 | match |
| lighting_global mid no-op (effect<=tau) seed 1 | 84 | 84 | 0 | 0 | match |
| lighting_global mid no-op (effect<=tau) seed 2 | 84 | 84 | 0 | 0 | match |
| lighting_global mid no-op (effect<=tau) seed 3 | 84 | 84 | 0 | 0 | match |
| LG bitwise-identical-to-clean videos (info; mine only) | 66 | None | None | None | info |
