# M2 audit (CPU, stored data + official vjepa2 code at 204698b). Investigation only; nothing in src/ kaggle/ scripts/ prereg changed.
Scripts and raw outputs: notes/m2_audit/{audit.py,audit2.py,audit3.py,*_out.txt,ckpt_tokens.py,cpu_maskindex*.{py,json,log}}.

## Verdict
Most likely cause: the wrapper calls the official predictor with `mask_index=1` (the library default), but in the released `vitl.pt` ONLY `mask_tokens.0` is trained. Tokens 1-9 are exactly zero (checked by loading the checkpoint, notes/m2_audit/ckpt_tokens_out.txt: token0 norm 0.769, tokens 1..9 norm 0.000000). In training, `PredictorMultiSeqWrapper` passes `mask_index=i` where i enumerates fpc groups (src/utils/wrappers.py:42); all three datasets have the same fpc (16, or 64 at cooldown), so MaskCollator builds one group, i=0 for every mask. The predictor was therefore always fed token 0. With RoPE and no additive pos-embed, mask_index=1 feeds all target positions an all-zero input vector: out-of-distribution, so the predictions barely use the learned "predict masked content" pathway. Not proven to be the only cause (see ranked list), but it is a definite wrapper deviation from training, and was recorded in the code docstring as "not confirmed".

## What matches official code (checked, no bug found)
- Token order t-major (patch_embed Conv3d flatten); M2 `_masks`: context = ids[: (C/2)*256], target = ids[(C/2)*256:], full = arange(2048). Equivalent to M1's get_time_masks (same frame/tubelet indexing, C counted in sampled frames, tubelet 2 -> C=2..10 are 1..5 tubelets, valid for M2: same tubelet size 2, 16 frames -> 8 tubelets).
- Targets: `F.layer_norm(target_encoder(full window), (D,))` then select target tokens = train.py `forward_target`. Context: `encoder(pieces, masks_enc)` drops tokens before blocks. Loss: L1 mean over tokens and D (loss_exp=1.0 in all vitl16 configs; train.py `torch.abs(z-h)**loss_exp/loss_exp`). Predictor returns only target tokens (return_all_tokens False, chop 0). RoPE positions from flat token ids (grid 16x16 at 256 px), so 16-frame windows are fine. Normalisation ImageNet mean/std at 256 px = training crop_size 256. Checkpoint keys load with 0 missing/0 unexpected (meta.json). CPU fp32 recompute of window 14, C=6 for one pair reproduces the stored fp16 S to 6e-5/1.2e-4, so the pipeline is deterministic and the arrays are what the code computes.
- Not matched to training (design, not bugs): (a) training masks are spatial blocks over ALL frames (temporal_scale 1.0), never "past frames only -> all future tokens", for V-JEPA 1 as well; (b) training fps=4 (consecutive frames 0.25 s apart; IntPhys step 2 is far smaller); (c) released ckpt is the 64-frame cooldown (epoch 40, final train loss 0.5446, ours S about 0.58); (d) bf16 training vs fp16 inference (no fp32/bf16 M2 full run exists).

## Stored-array findings (clean dev, 180 pairs, tie-half unless stated)
| item | M1 | M2 |
|---|---|---|
| mean S by C (2,4,6,8,10) | .553 .538 .535 .539 .551 | .592 .588 .586 .581 .582 (nearly flat in C) |
| argmin-over-C histogram (C=2..10) | 2% 27% 48% 18% 5% | 8% 6% 2% 43% 41% |
| acc fixed C=2/4/6/8/10 (mean agg) | 34.4 / 76.9 / 79.2 / 79.4 / 78.9 | 65.8 / 54.2 / 53.3 / 50.8 / 41.4 |
| acc min-over-C (primary) | 80.8 | 46.9 |
| acc max-agg fixed C=2/4/6/8/10 | 52.8/66.9/67.5/61.9/61.9 | 70.8/71.1/64.4/57.5/55.3 |
| acc mean-over-C / max-over-C then mean windows | 75.3 / 62.8 | 53.1 / 61.7 |
| per block (O1/O2/O3) | 75.8/81.7/85.0 | 48.3/40.8/51.7 |
| within-video sd across windows (min-C) vs between-video sd | .0075 vs .0161 | .0084 vs .0078 |
| per-window strict imp>pos, windows 8-16 | .56 .61 .64 .63 .61 .58 .54 .47 .45 | .32 .38 .37 .37 .33 .38 .38 .36 .38 |
| post-divergence mean S(imp)-S(pos), frac>0 | +0.0032, 81% | +0.0011, 47% |
| corr(S, pooled-feature norm) across videos | -0.93 | -0.83 |
- Curves are non-constant and finite; no single column dominates the values. But min-over-C selects C=8/10 in 84% of M2 windows, and those are exactly M2's worst columns (C=10 is 41%, below chance; C=2 is its best at 66%). So the aggregation interacts badly: with min over C, M2 accuracy is 12 pp below its best fixed column and 20 pp below C=2. Under max aggregation tie-half is 64.4 (strict 48.3), i.e. the sign is also unstable across conventions.
- M1 has the mirror pattern: C=2 is 34% (inverted), C>=4 about 79%, and min-over-C avoids the C=2 column in 98% of windows (argmin C=2 only 2%). That asymmetry is why "same C set, min over C" works for M1 and not M2. M2's S is nearly flat in C, a sign that the predictor output depends weakly on how much context it sees (consistent with the zero mask token / OOD query), but this is inferred, not shown.
- Per pair: M1 and M2 S verdicts agree on only 55.6% of pairs. M2 S verdict agrees with B3(M2) on 43.9%.

## B3 (definition, and why 17.2%)
B3 (src/vjepa_study/analysis/baselines.py:69): spatial mean of layer-normed TARGET-encoder tokens per tubelet (8 vectors/window), S[w,c] = mean over tubelets j >= C/2 of mean_D |g_j - g_(j-1)|; same pooled features as M1 pipeline (no predictor involved). Facts:
- B3(M2) is 17-19% at EVERY C (stored: .169/.172/.189/.192/.189); M1: .547/.633/.647/.575/.397. By block M2 imp>pos: O1 28%, O2 8%, O3 15% (M1: 50/42/43). Per-window it is inverted from the first post-divergence window on.
- Feature-space persistence (|g_j - g_(C/2-1)|) accuracy: M2 10-29% at all C vs M1 32-79%. So the inversion is a property of the M2 ENCODER representation (what moves in pooled features), independent of the predictor and of mask_index. It also means B3 is a weak/odd baseline: across videos corr(B1 pixel change, B3) = -0.83 (M1) / -0.84 (M2), pair-diff corr -0.46 / -0.40 (more pixel change -> less pooled-feature change; B3 mostly measures scene content/global norm, not motion).
- Mean-pooling 256 spatial tokens before differencing throws away localized change; a token-level B3 (per-token L1 between tubelets) would be the faithful encoder-change baseline and may not be inverted. B3(M2)=17.2% is thus evidence that (i) M2's encoder codes IntPhys possible/impossible differently from M1's (impossible videos change pooled features less), and (ii) a naive 'surprise should rise with encoder change' reading fails for M2, so even a perfect predictor-side fix might not make S track encoder change.

## Hypotheses, ranked (evidence -> discriminating check)
1. mask_index=1 is an untrained (zero) token; training used token 0. Evidence: checkpoint tokens (definite), wrapper default, CPU test: for window 14, C=6, token 0 gives lower loss than token 1 (0.574 vs 0.595, pos video; 0.576 vs 0.595, imp) i.e. predictor does use token 0 differently; effect (0.02) is 2.5x the between-video sd 0.008. Check: rerun M2 clean with mask_index=0 (pair accuracy + fixed-C profile + B-correlations). GPU cost about 0.5 h on 2 T4 (M2 clean was 29.6 min wall; reuse targets: only the predictor side changes, still one full pass unless the coder caches). A 12-video/2-C reduced version is ~2 min per GPU. CPU variant (done partially): see 'CPU result' below.
2. Aggregation min-over-C is a poor fit for M2's C-profile (picks C=8/10). Evidence: argmin histogram and fixed-C table above. Check: zero GPU, already computed: best fixed-C is 65.8 (C=2) mean agg, still far below M1. So H2 alone cannot restore M1-like accuracy; it can only explain 47 -> ~66. Pre-registered aggregation cannot be changed post hoc (prereg) without human approval (item 3); report as exploratory.
3. Encoder representation of M2 does not carry possible/impossible differences in this layout (B3 17%, persistence 10-29%). Check: token-level encoder-feature baseline (encoder only, one ViT-L forward per window, ~0.15 GPU-h) and M2 with frame_step 4 or 8 (training fps 4).
4. Temporal-stride/horizon distribution shift (training 0.25 s steps vs IntPhys step 2; predictor trained on spatial blocks across all frames, 64-frame cooldown). Check: M2 skip-4/8 clean run (~0.5 h each) plus token 0 run.
5. fp16 vs bf16 degradation for V-JEPA 2 ViT-L. Evidence against: outputs finite, CPU fp32 reproduces fp16 S within 1e-4 on tested window. Check: fp32 CPU/GPU on 12 videos (no sign it matters).
6. Wrapper indexing / loss / normalisation bug: checked against train.py and predictor.py, no discrepancy found; ruled out as far as code reading goes.

## Summary lines
1. M2 wrapper matches official train.py on masks, token order, layer-normed targets, L1, 256 px, ImageNet norm, RoPE (no indexing bug found); CPU fp32 reproduces stored S.
2. Definite deviation: wrapper uses mask_index=1; the released vitl.pt trained only mask token 0 (tokens 1-9 are exactly zero; training wrapper passes i=0).
3. M2's S is nearly flat in C (0.592 to 0.582) and its post-divergence pair signal is inverted/near zero (S diff +0.0011, 47% vs M1 +0.0032, 81%).
4. Min over C picks C=8/10 in 84% of M2 windows, the worst columns (C=10: 41%, C=2: 66%); M1 mirror: C=2 is its inverted column and min-over-C avoids it.
5. B3(M2)=17% at every C and per-tubelet persistence 10-29%: inversion lives in the encoder features, independent of predictor/mask_index; B3 pooled baseline is crude (corr with pixel change -0.84).
6. Cheapest confirming experiment: M2 clean with mask_index=0 (about 0.5 GPU-h, 2 T4; or a 20-pair/1-window subset in minutes).

## CPU result (notes/m2_audit/cpu_maskindex.json, 2 pairs only, run stopped: ~7 min/pair on CPU)
Window 14, C=6, fp32: token 1 (wrapper) reproduces stored fp16 S (|diff| < 2e-4); token 0 lowers S by about 0.018 for both videos (0.591 -> 0.573) and keeps imp>pos in both pairs. Two pairs say nothing about accuracy; this only shows token 0 vs 1 changes the predictor output materially. Accuracy effect is untested: needs the GPU run.
