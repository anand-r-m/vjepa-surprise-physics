# P6 comparison: verifier recompute vs results/analysis (written AFTER p6_recompute.*)

| quantity | verifier | analysis | abs diff | tol | status |
|---|---|---|---|---|---|
| clean fp16 tie-half | 0.80833 | 0.80833 | 0 | 0.001 | match |
| clean fp16 strict | 0.81111 | 0.81111 | 0 | 0.001 | match |
| clean fp16 ties | 7 | 7 | 0 | 0 | match |
| clean fp16 tau | 0.0001057 | 0.0001057 | 1.0534e-11 | 1e-07 | match |
| H1 eligibility fp32 tie-half | 0.81667 | 0.81667 | 0 | 0.001 | match |
| H1 f0 | 0.21481 | 0.21481 | 0 | 0.001 | match |
| H1 tau | 0.0001057 | 0.0001057 | 1.0534e-11 | 1e-07 | match |
| H1 brightness n | 180 | 180 | 0 | 0 | match |
| H1 brightness dAcc | -0.024074 | -0.024074 | 0 | 0.001 | match |
| H1 brightness flip | 0.12407 | 0.12407 | 0 | 0.001 | match |
| H1 brightness flip-f0 | -0.090741 | -0.090741 | 0 | 0.001 | match |
| H1 brightness f0 (retained) | 0.21481 | 0.21481 | 0 | 0.001 | match |
| H1 brightness dAcc CI lo | -0.050926 | -0.051852 | 0.00092593 | 0.01 | match |
| H1 brightness dAcc CI hi | 0.0027778 | 0.0018519 | 0.00092593 | 0.01 | match |
| H1 brightness p_dacc_cluster | 0.0786 | 0.07 | 0.0086 | 0.015 | match |
| H1 brightness p_flip_cluster | 0.9999 | 0.9999 | 0 | 0.015 | match |
| H1 brightness holm14 dacc | 0.6288 | 0.56 | 0.0688 | 0.03 | MISMATCH |
| H1 brightness holm14 flip | 1 | 1 | 0 | 0.03 | match |
| H1 brightness sign p | 0.065994 | 0.065994 | 0 | 1e-06 | match |
| H1 noise n | 180 | 180 | 0 | 0 | match |
| H1 noise dAcc | -0.20556 | -0.20556 | 0 | 0.001 | match |
| H1 noise flip | 0.37778 | 0.37778 | 0 | 0.001 | match |
| H1 noise flip-f0 | 0.16296 | 0.16296 | 0 | 0.001 | match |
| H1 noise f0 (retained) | 0.21481 | 0.21481 | 0 | 0.001 | match |
| H1 noise dAcc CI lo | -0.25741 | -0.25833 | 0.00092593 | 0.01 | match |
| H1 noise dAcc CI hi | -0.15278 | -0.1537 | 0.00092593 | 0.01 | match |
| H1 noise p_dacc_cluster | 0 | 0 | 0 | 0.015 | match |
| H1 noise p_flip_cluster | 0 | 0 | 0 | 0.015 | match |
| H1 noise holm14 dacc | 0 | 0 | 0 | 0.03 | match |
| H1 noise holm14 flip | 0 | 0 | 0 | 0.03 | match |
| H1 noise sign p | 1.0099e-12 | 1.0099e-12 | 0 | 1e-06 | match |
| H1 blur n | 180 | 180 | 0 | 0 | match |
| H1 blur dAcc | -0.14444 | -0.14444 | 0 | 0.001 | match |
| H1 blur flip | 0.31111 | 0.31111 | 0 | 0.001 | match |
| H1 blur flip-f0 | 0.096296 | 0.096296 | 0 | 0.001 | match |
| H1 blur f0 (retained) | 0.21481 | 0.21481 | 0 | 0.001 | match |
| H1 blur dAcc CI lo | -0.19444 | -0.19444 | 0 | 0.01 | match |
| H1 blur dAcc CI hi | -0.094444 | -0.097222 | 0.0027778 | 0.01 | match |
| H1 blur p_dacc_cluster | 0 | 0 | 0 | 0.015 | match |
| H1 blur p_flip_cluster | 0.0001 | 0.0002 | 0.0001 | 0.015 | match |
| H1 blur holm14 dacc | 0 | 0 | 0 | 0.03 | match |
| H1 blur holm14 flip | 0.001 | 0.002 | 0.001 | 0.03 | match |
| H1 blur sign p | 1.2455e-06 | 1.2455e-06 | 0 | 1e-06 | match |
| H1 jpeg n | 180 | 180 | 0 | 0 | match |
| H1 jpeg dAcc | -0.10833 | -0.10833 | 0 | 0.001 | match |
| H1 jpeg flip | 0.28333 | 0.28333 | 0 | 0.001 | match |
| H1 jpeg flip-f0 | 0.068519 | 0.068519 | 0 | 0.001 | match |
| H1 jpeg f0 (retained) | 0.21481 | 0.21481 | 0 | 0.001 | match |
| H1 jpeg dAcc CI lo | -0.16389 | -0.16389 | 0 | 0.01 | match |
| H1 jpeg dAcc CI hi | -0.052778 | -0.055556 | 0.0027778 | 0.01 | match |
| H1 jpeg p_dacc_cluster | 0 | 0 | 0 | 0.015 | match |
| H1 jpeg p_flip_cluster | 0.0171 | 0.017 | 0.0001 | 0.015 | match |
| H1 jpeg holm14 dacc | 0 | 0 | 0 | 0.03 | match |
| H1 jpeg holm14 flip | 0.1539 | 0.153 | 0.0009 | 0.03 | match |
| H1 jpeg sign p | 0.0017692 | 0.0017692 | 0 | 1e-06 | match |
| H1 zoom n | 112 | 112 | 0 | 0 | match |
| H1 zoom dAcc | -0.0044643 | -0.0044643 | 0 | 0.001 | match |
| H1 zoom flip | 0.14286 | 0.14286 | 0 | 0.001 | match |
| H1 zoom flip-f0 | -0.089286 | -0.089286 | 0 | 0.001 | match |
| H1 zoom f0 (retained) | 0.23214 | 0.23214 | 0 | 0.001 | match |
| H1 zoom dAcc CI lo | -0.056452 | -0.056034 | 0.00041713 | 0.01 | match |
| H1 zoom dAcc CI hi | 0.048784 | 0.049107 | 0.00032334 | 0.01 | match |
| H1 zoom p_dacc_cluster | 0.9248 | 0.9386 | 0.0138 | 0.015 | match |
| H1 zoom p_flip_cluster | 0.9921 | 0.9901 | 0.002 | 0.015 | match |
| H1 zoom holm14 dacc | 1 | 1 | 0 | 0.03 | match |
| H1 zoom holm14 flip | 1 | 1 | 0 | 0.03 | match |
| H1 zoom sign p | 1 | 1 | 0 | 1e-06 | match |
| H1 hflip n | 180 | 180 | 0 | 0 | match |
| H1 hflip dAcc | 0.022222 | 0.022222 | 0 | 0.001 | match |
| H1 hflip flip | 0.15 | 0.15 | 0 | 0.001 | match |
| H1 hflip flip-f0 | -0.064815 | -0.064815 | 0 | 0.001 | match |
| H1 hflip f0 (retained) | 0.21481 | 0.21481 | 0 | 0.001 | match |
| H1 hflip dAcc CI lo | -0.022222 | -0.019444 | 0.0027778 | 0.01 | match |
| H1 hflip dAcc CI hi | 0.066667 | 0.066667 | 0 | 0.01 | match |
| H1 hflip p_dacc_cluster | 0.3446 | 0.342 | 0.0026 | 0.015 | match |
| H1 hflip p_flip_cluster | 0.9782 | 0.9779 | 0.0003 | 0.015 | match |
| H1 hflip holm14 dacc | 1 | 1 | 0 | 0.03 | match |
| H1 hflip holm14 flip | 1 | 1 | 0 | 0.03 | match |
| H1 hflip sign p | 0.44207 | 0.44207 | 0 | 1e-06 | match |
| H1 fps_halve n | 180 | 180 | 0 | 0 | match |
| H1 fps_halve dAcc | 0 | 0 | 0 | 0.001 | match |
| H1 fps_halve flip | 0 | 0 | 0 | 0.001 | match |
| H1 fps_halve flip-f0 | -0.21481 | -0.21481 | 0 | 0.001 | match |
| H1 fps_halve f0 (retained) | 0.21481 | 0.21481 | 0 | 0.001 | match |
| H1 fps_halve dAcc CI lo | 0 | 0 | 0 | 0.01 | match |
| H1 fps_halve dAcc CI hi | 0 | 0 | 0 | 0.01 | match |
| H1 fps_halve p_dacc_cluster | 1 | 1 | 0 | 0.015 | match |
| H1 fps_halve p_flip_cluster | 1 | 1 | 0 | 0.015 | match |
| H1 fps_halve holm14 dacc | 1 | 1 | 0 | 0.03 | match |
| H1 fps_halve holm14 flip | 1 | 1 | 0 | 0.03 | match |
| H1 fps_halve sign p | 1 | 1 | 0 | 1e-06 | match |
| H1 zoom n_pairs (my own retention 110 pairs vs analysis 112) | 110 | 112 | 2 | - | info |
| H1 zoom dacc (my own retention 110 pairs vs analysis 112) | -0.0045455 | -0.0044643 | 8.1169e-05 | - | info |
| H1 zoom flip (my own retention 110 pairs vs analysis 112) | 0.14545 | 0.14286 | 0.0025974 | - | info |
| H2 A M1 (R1b stored t_on) | 0.54572 | 0.54572 | 0 | 0.002 | match |
| H2 A M1 (R1 pixel t_on) | 0.54615 | 0.54572 | 0.00042824 | 0.002 | match |
| H2 M1 lighting_global (R1b) | 0.62154 | 0.62154 | 0 | 0.002 | match |
| H2 M1 lighting_local (R1b) | 0.48045 | 0.48045 | 0 | 0.002 | match |
| H2 M1 jolt_base (R1b) | 0.55282 | 0.55282 | 0 | 0.002 | match |
| H2 M1 zoom_base (R1b) | 0.52807 | 0.52807 | 0 | 0.002 | match |
| H2 A0 M1 | 0.72222 | 0.72222 | 0 | 0.001 | match |
| H2 tau M1 | 0.00010875 | 0.00010875 | 0 | 1e-09 | match |
| H2 A CI lo M1 | 0.50104 | 0.50127 | 0.00022399 | 0.01 | match |
| H2 A CI hi M1 | 0.59055 | 0.59115 | 0.00060452 | 0.01 | match |
| H2 A B1 (R1b stored t_on) | 0.33521 | 0.33521 | 0 | 0.002 | match |
| H2 A B1 (R1 pixel t_on) | 0.33521 | 0.33521 | 0 | 0.002 | match |
| H2 B1 lighting_global (R1b) | 0.36179 | 0.36179 | 0 | 0.002 | match |
| H2 B1 lighting_local (R1b) | 0.2731 | 0.2731 | 0 | 0.002 | match |
| H2 B1 jolt_base (R1b) | 0.37193 | 0.37193 | 0 | 0.002 | match |
| H2 B1 zoom_base (R1b) | 0.33401 | 0.33401 | 0 | 0.002 | match |
| H2 A0 B1 | 0.55556 | 0.55556 | 0 | 0.001 | match |
| H2 tau B1 | 1.4669e-06 | 1.4669e-06 | 0 | 1e-09 | match |
| H2 A CI lo B1 | 0.29226 | 0.29258 | 0.00031546 | 0.01 | match |
| H2 A CI hi B1 | 0.37859 | 0.37784 | 0.00075829 | 0.01 | match |
| H2 A B2 (R1b stored t_on) | 0.37934 | 0.37934 | 0 | 0.002 | match |
| H2 A B2 (R1 pixel t_on) | 0.37934 | 0.37934 | 0 | 0.002 | match |
| H2 B2 lighting_global (R1b) | 0.39369 | 0.39369 | 0 | 0.002 | match |
| H2 B2 lighting_local (R1b) | 0.31608 | 0.31608 | 0 | 0.002 | match |
| H2 B2 jolt_base (R1b) | 0.4295 | 0.4295 | 0 | 0.002 | match |
| H2 B2 zoom_base (R1b) | 0.3781 | 0.3781 | 0 | 0.002 | match |
| H2 A0 B2 | 0.6 | 0.6 | 0 | 0.001 | match |
| H2 tau B2 | 2.9196e-06 | 2.9196e-06 | 0 | 1e-09 | match |
| H2 A CI lo B2 | 0.33146 | 0.33192 | 0.00046486 | 0.01 | match |
| H2 A CI hi B2 | 0.42829 | 0.42909 | 0.00079135 | 0.01 | match |
| H2 D_B1 | 0.21051 | 0.21051 | 0 | 0.002 | match |
| H2 D_B1 CI lo | 0.159 | 0.16083 | 0.0018291 | 0.01 | match |
| H2 D_B1 CI hi | 0.26323 | 0.26193 | 0.0012978 | 0.01 | match |
| H2 p_B1 | 9.999e-05 | 9.999e-05 | 0 | 0.0005 | match |
| H2 Holm-2 B1 | 0.00019998 | 0.00019998 | 0 | 0.001 | match |
| H2 D_B2 | 0.16638 | 0.16638 | 0 | 0.002 | match |
| H2 D_B2 CI lo | 0.11634 | 0.11687 | 0.00053038 | 0.01 | match |
| H2 D_B2 CI hi | 0.21851 | 0.21622 | 0.002287 | 0.01 | match |
| H2 p_B2 | 9.999e-05 | 9.999e-05 | 0 | 0.0005 | match |
| H2 Holm-2 B2 | 0.00019998 | 0.00019998 | 0 | 0.001 | match |
| H2 outcome | Not specific/Detection-limited | Detection-limited (not specific / partial) |  | - | match |
| H2 n_excluded_late / fallback | (0, 178, 2) | (0, 'n/a', 2) |  | - | info |
| H3 vflip (a) | 0.21111 | 0.21111 | 0 | 0.001 | match |
| H3 vflip (a) CI lo | 0.14715 | 0.14722 | 6.9444e-05 | 0.01 | match |
| H3 vflip (a) CI hi | 0.28056 | 0.28333 | 0.0027778 | 0.01 | match |
| H3 vflip (b) hflip-ref | 0.25833 | 0.25833 | 0 | 0.001 | match |
| H3 (b) CI lo | 0.18611 | 0.18611 | 0 | 0.01 | match |
| H3 (b) CI hi | 0.33333 | 0.33333 | 0 | 0.01 | match |
| H3 M1-M0r vflip | -0.66667 | -0.66667 | 0 | 0.001 | match |
| H3 diff CI lo | -0.76111 | -0.76111 | 0 | 0.01 | match |
| H3 diff CI hi | -0.56667 | -0.56667 | 0 | 0.01 | match |
| H3 reversal | 0.60833 | 0.60833 | 0 | 0.001 | match |
| H3 pairwise vflip tiehalf | 0.83889 | 0.83889 | 0 | 0.001 | match |
| H3 pairwise vflip strict | 0.82222 | 0.82222 | 0 | 0.001 | match |
| H3 pairwise rev tiehalf | 0.74722 | 0.74722 | 0 | 0.001 | match |
| H3 pairwise rev strict | 0.73333 | 0.73333 | 0 | 0.001 | match |
| H3 tau | 0.00010875 | 0.00010875 | 0 | 1e-09 | match |
| H3 G2 pass | False | False |  | - | match |

Total 152; match 147; MISMATCH 1; info/ambiguous 4