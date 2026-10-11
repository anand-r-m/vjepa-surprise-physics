# Released-surprise IntPhys dev pairwise accuracy (independent recomputation)

Structure: 360 videos, 90 quadruplets ({'O1': 30, 'O2': 30, 'O3': 30}), 180 pairs; 180 possible videos.

Rule: pairs = released rule: bp_k=first sampled frame (every 2nd of first 98, 49 frames) where video1 differs from video k+1; argmax(bps) selects matching [[0,1],[2,3]]/[[0,2],[1,3]]/[[0,3],[1,2]]; surprise rows are stored per pair as consecutive rows; correct iff S(possible) < S(impossible) strictly; S = agg_over_17_windows(min_over_5_contexts)

Accuracy % (strict S(possible) < S(impossible)), n=60 pairs per block, 180 overall; Wilson 95% CI on overall.

| model | agg | O1 | O2 | O3 | overall (k/n) | Wilson 95% |
|---|---|---|---|---|---|---|
| vit-l-rope-vm2m | mean | 85.00 | 91.67 | 91.67 | 89.44 (161/180) | [84.1, 93.1] |
| vit-l-rope-vm2m | max | 61.67 | 61.67 | 76.67 | 66.67 (120/180) | [59.5, 73.1] |
| vit-l-rope-howto | mean | 91.67 | 88.33 | 90.00 | 90.00 (162/180) | [84.7, 93.6] |
| vit-l-rope-howto | max | 68.33 | 56.67 | 70.00 | 65.00 (117/180) | [57.8, 71.6] |
| vit-h-rope-vm2m | mean | 95.00 | 100.00 | 95.00 | 96.67 (174/180) | [92.9, 98.5] |
| vit-h-rope-vm2m | max | 90.00 | 91.67 | 81.67 | 87.78 (158/180) | [82.2, 91.8] |
| videomaev2_g | mean | 53.33 | 53.33 | 53.33 | 53.33 (96/180) | [46.1, 60.5] |
| videomaev2_g | max | 38.33 | 33.33 | 30.00 | 33.89 (61/180) | [27.4, 41.1] |
| vit-l-rope-random-0 | mean | 51.67 | 50.00 | 50.00 | 50.56 (91/180) | [43.3, 57.8] |
| vit-l-rope-random-0 | max | 38.33 | 33.33 | 28.33 | 33.33 (60/180) | [26.9, 40.5] |
| vit-l-rope-random-1 | mean | 51.67 | 48.33 | 51.67 | 50.56 (91/180) | [43.3, 57.8] |
| vit-l-rope-random-1 | max | 26.67 | 16.67 | 35.00 | 26.11 (47/180) | [20.2, 33.0] |
| vit-l-rope-random-2 | mean | 50.00 | 50.00 | 50.00 | 50.00 (90/180) | [42.8, 57.2] |
| vit-l-rope-random-2 | max | 30.00 | 25.00 | 25.00 | 26.67 (48/180) | [20.7, 33.6] |
| vit-l-rope-random-3 | mean | 50.00 | 53.33 | 48.33 | 50.56 (91/180) | [43.3, 57.8] |
| vit-l-rope-random-3 | max | 48.33 | 48.33 | 46.67 | 47.78 (86/180) | [40.6, 55.0] |
| vit-l-rope-random-4 | mean | 43.33 | 48.33 | 48.33 | 46.67 (84/180) | [39.5, 53.9] |
| vit-l-rope-random-4 | max | 45.00 | 40.00 | 40.00 | 41.67 (75/180) | [34.7, 49.0] |
| vit-l-rope-random-5 | mean | 51.67 | 51.67 | 50.00 | 51.11 (92/180) | [43.9, 58.3] |
| vit-l-rope-random-5 | max | 51.67 | 43.33 | 41.67 | 45.56 (82/180) | [38.4, 52.8] |
| vit-l-rope-random-6 | mean | 51.67 | 46.67 | 48.33 | 48.89 (88/180) | [41.7, 56.1] |
| vit-l-rope-random-6 | max | 41.67 | 35.00 | 38.33 | 38.33 (69/180) | [31.5, 45.6] |
| vit-l-rope-random-7 | mean | 50.00 | 48.33 | 48.33 | 48.89 (88/180) | [41.7, 56.1] |
| vit-l-rope-random-7 | max | 38.33 | 33.33 | 36.67 | 36.11 (65/180) | [29.5, 43.4] |
| vit-l-rope-random-8 | mean | 48.33 | 51.67 | 48.33 | 49.44 (89/180) | [42.2, 56.7] |
| vit-l-rope-random-8 | max | 35.00 | 23.33 | 21.67 | 26.67 (48/180) | [20.7, 33.6] |
| vit-l-rope-random-9 | mean | 50.00 | 50.00 | 50.00 | 50.00 (90/180) | [42.8, 57.2] |
| vit-l-rope-random-9 | max | 41.67 | 31.67 | 46.67 | 40.00 (72/180) | [33.1, 47.3] |
| vit-l-rope-random-10 | mean | 50.00 | 48.33 | 48.33 | 48.89 (88/180) | [41.7, 56.1] |
| vit-l-rope-random-10 | max | 38.33 | 28.33 | 38.33 | 35.00 (63/180) | [28.4, 42.2] |
| vit-l-rope-random-11 | mean | 48.33 | 50.00 | 48.33 | 48.89 (88/180) | [41.7, 56.1] |
| vit-l-rope-random-11 | max | 38.33 | 28.33 | 25.00 | 30.56 (55/180) | [24.3, 37.6] |
| vit-l-rope-random-12 | mean | 50.00 | 51.67 | 50.00 | 50.56 (91/180) | [43.3, 57.8] |
| vit-l-rope-random-12 | max | 31.67 | 30.00 | 33.33 | 31.67 (57/180) | [25.3, 38.8] |
| vit-l-rope-random-13 | mean | 46.67 | 50.00 | 51.67 | 49.44 (89/180) | [42.2, 56.7] |
| vit-l-rope-random-13 | max | 46.67 | 36.67 | 50.00 | 44.44 (80/180) | [37.4, 51.7] |
| vit-l-rope-random-14 | mean | 51.67 | 46.67 | 48.33 | 48.89 (88/180) | [41.7, 56.1] |
| vit-l-rope-random-14 | max | 43.33 | 23.33 | 41.67 | 36.11 (65/180) | [29.5, 43.4] |
| vit-l-rope-random-15 | mean | 55.00 | 50.00 | 50.00 | 51.67 (93/180) | [44.4, 58.9] |
| vit-l-rope-random-15 | max | 53.33 | 40.00 | 40.00 | 44.44 (80/180) | [37.4, 51.7] |
| vit-l-rope-random-16 | mean | 50.00 | 50.00 | 48.33 | 49.44 (89/180) | [42.2, 56.7] |
| vit-l-rope-random-16 | max | 48.33 | 35.00 | 41.67 | 41.67 (75/180) | [34.7, 49.0] |
| vit-l-rope-random-17 | mean | 50.00 | 48.33 | 46.67 | 48.33 (87/180) | [41.1, 55.6] |
| vit-l-rope-random-17 | max | 31.67 | 26.67 | 30.00 | 29.44 (53/180) | [23.3, 36.5] |
| vit-l-rope-random-18 | mean | 50.00 | 48.33 | 50.00 | 49.44 (89/180) | [42.2, 56.7] |
| vit-l-rope-random-18 | max | 41.67 | 30.00 | 30.00 | 33.89 (61/180) | [27.4, 41.1] |
| vit-l-rope-random-19 | mean | 50.00 | 50.00 | 50.00 | 50.00 (90/180) | [42.8, 57.2] |
| vit-l-rope-random-19 | max | 50.00 | 36.67 | 33.33 | 40.00 (72/180) | [33.1, 47.3] |

Random-init ViT-L controls (20 seeds), overall acc: {"mean": {"n_models": 20, "mean_acc": 0.49611111111111106, "min": 0.4666666666666667, "max": 0.5166666666666667, "sd": 0.011125721388442878}, "max": {"n_models": 20, "mean_acc": 0.3647222222222223, "min": 0.2611111111111111, "max": 0.4777777777777778, "sd": 0.06672207736227465}}

Cross-check vs released performance.csv 'Filtered' rows: max abs diff 1.667 points (only near-tie random-init mean cases differ, float32 summation order).
