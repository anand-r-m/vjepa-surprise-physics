# PROTOCOL NOTES (coder, 2026-10-06)

Source: code read in `external/` (gitignored). Pinned commits:

| repo | commit | date |
|---|---|---|
| facebookresearch/jepa-intuitive-physics | `302a2e821d908b4a8667e0c0e48fe733e43c9156` | 2026-06-03 |
| facebookresearch/vjepa2 | `204698b45b3712590f06245fbfba32d3be539812` | 2026-03-23 |
| facebookresearch/jepa (original V-JEPA, for checkpoints) | `51c59d518fc63c08464af6de585f78ac0c7ed4d5` | 2025-02-27 |

Everything marked CONFIRMED was read in code or recomputed from the released raw surprises. UNCONFIRMED means not verifiable without running or without material the repo does not contain.

## 1. IntPhys eval config (CONFIRMED, `evaluation_code/evals/intuitive_physics/{eval.py,utils.py,intphys_dataset.py,configs/default_intphys.yaml}`)

- Config: resolution 224, `frame_steps: 2` (native-frame skip), `frames_per_clip: 16` (window C+M = 16 *sampled* frames = 32 native), `context_lengths [2,4,6,8,10]` (sampled frames; tubelet 2, so the context is 1..5 tubelets), `stride_sliding_window: 2` (sampled frames), batch of one quadruplet, fp16 autocast, `normalize_targets=True`.
- Frames: dev videos have 100 PNG frames (288x288). The loader takes `num_frames = 99 // frame_step` = 49 sampled frames at skip 2, starting at frame 0 (`length_clip > 90 -> start = 0`). Then `clip.unfold(2, 16, 2)` gives **17 windows** per video.
- Preprocessing: full-frame bilinear resize 288 -> 224 (scale 1.0, ratio 1:1, no antialias, no crop, no flip), ImageNet mean/std on the 0-255 scale.
- Surprise per window and per C: target = `layer_norm(target_encoder(full window))` restricted to tokens after the context; prediction = `predictor(encoder(context tokens only), ...)`; surprise = L1 mean over target tokens and feature dim. So the "timestep" of the released S is the **window start index (17 values), not a frame**. Raw file shape `losses[N_videos, 5 (C), 17 (windows)]`, confirmed on `data_intphys/*/intphys/raw_surprises/O?_16frames.pth`.
- Aggregation: `Filtered` = **min over C** per window, then mean (avg) or max over the 17 windows. The CSV reports both ("Relative Accuracy (avg)" / "(max)").
- Pairing (CONFIRMED): for each scene (quadruplet, 4 videos) `get_breaking_points` = first sampled frame where `sum_{H,W}(clip0 - clip_j)` summed over channels is non-zero (on the transformed, subsampled clip; signed sum). `get_matches`: video 0 is paired with the video that diverges **latest** from it (prefix-sharing pair), the other two are paired. Each pair contains one possible and one impossible video. 90 quadruplets, 180 pairs, 30 quadruplets / 60 pairs per block, verified from the raw-surprise labels (120 videos per block, label order like [1,0,0,1,0,1]).
- Pairwise accuracy: `loss_real.mean(1) < loss_fake.mean(1)` (strict `<`; no tie rule). Max variant uses `.max(1)`.
- Scenario labels (visible/occluded, static/dynamic) are **not** in file names or status.json (only scene number 01-30, video 1-4 and `is_possible`). Local layout: `dev/O{1,2,3}/<NN>/<1-4>/scene/scene_###.png`.

### Which aggregation gives the published number
- The released `performance.csv` files contain **only frame skip 2 / 16-frame windows** for dev. Recomputed from the raw surprises (mean of 3 blocks x 60 pairs, "Filtered" = min over C):
  - `vit-l-rope-vm2m`: avg 89.4% (O1 85.0, O2 91.7, O3 91.7); max 66.7%.
  - `vit-l-rope-howto`: avg 90.0%, max 65.0%. `vit-h-rope-vm2m`: avg 96.7%, max 87.8%. `vit-l-rope-random-*` (20 inits): avg 46.7-51.1%.
  - `videomaev2_g`: avg 53.3%, max 33.9%.
- So **average** is the aggregation that works for pairs (matches B1 expectation), and **ViT-L reaches about 89-90% on dev at skip 2, not 98%**. The ~98% in the abstract is not reproduced by any released dev file. We cannot confirm which model/skip/split it refers to (likely ViT-H, a different skip/window chosen in the paper, or the test set). **G1 (>= 90% for ViT-L) is therefore at the edge of the released reference value (89.4%).** Lead decision needed (section 6).
- Whether frame skip 5/10 or window 32 was used for the headline number: UNCONFIRMED (not in repo).

## 2. Checkpoints (CONFIRMED absence)
- The repo ships **no weights and no URLs** for the Garrido models (`vit-l-rope-vm2m` etc.). The config points to a private path (`/checkpoint/garridoq/...`). HF search for them returned nothing. So the exact Garrido ViT-L RoPE checkpoint is NOT obtainable.
- Closest public M1: original V-JEPA ViT-L/16 (VideoMix2M, non-RoPE, sincos pos-embed, uniform_power, pred depth 12, 224 px, 16 frames): `https://dl.fbaipublicfiles.com/jepa/vitl16/vitl16.pth.tar` (also vith16, vith16-384). Loadable with the released `init_model` with `model_name: vit_large` (predictor uses sincos when "rope" is not in the name). Expected to be comparable to `vit-l-rope-vm2m` but is not the same model; the accuracy is UNCONFIRMED until run. Checkpoint keys (`encoder`, `target_encoder`, `predictor`) UNCONFIRMED (not downloaded locally, 3GB scale).
- V-JEPA 2 official: `https://dl.fbaipublicfiles.com/vjepa2/vitl.pt` (ViT-L/16, 256 px; keys `encoder`, `target_encoder`, `predictor`). **Caution:** `vjepa2/src/hub/backbones.py` has `VJEPA_BASE_URL = "http://localhost:8300"` (testing value), so `torch.hub.load` pretrained downloads fail; download the URL directly and build with `_make_vjepa2_model(pretrained=False)`.
- hflip: random horizontal flip is on in both V-JEPA pretraining transforms (`jepa/app/vjepa/transforms.py`, `vjepa2/app/vjepa/train.py`). So hflip invariance is expected (mn3 holds). No vflip in pretraining.

## 3. VideoMAEv2 (M3)
- `evals/intuitive_physics/videomae.py` (model `pretrain_videomae_giant_patch14_224`, loaded with `init_ckpt`, key `model`); `is_mae: true` path: targets are per-patch normalised pixels (16x16x2), prediction = decoder output from `encoder(pieces, masks_pred)`, surprise = L1 on those. Eval config for MAE (model_name, checkpoint path, decoder blocks) is **not in the repo** and the checkpoint source is UNCONFIRMED (likely OpenGVLab VideoMAEv2 giant pretrain weights; do not assume). M3 stays descriptive per MJ7.

## 4. V-JEPA 2 predictor with masks and variable frame counts
- **Official repo (usable): CONFIRMED by code reading, NOT run.** `src/models/predictor.py` `VisionTransformerPredictor.forward(x, masks_x, masks_y, mask_index=1)` takes context tokens plus index masks exactly like V-JEPA 1; the encoder `forward(x, masks=None)` drops unmasked tokens before the blocks. Positions are RoPE derived from the flat token index (`d,h,w = separate_positions(ids)`), no learned pos-embed, so any frame count is accepted provided masks index a (T/2, 16, 16) grid. Build with `num_frames=16` (or T) for the released window layout; weights load `strict=False`.
- **HF `facebook/vjepa2-vitl-fpc64-256` (not faithful for our protocol): CONFIRMED in `transformers` 5.18 `modeling_vjepa2.py`.** `VJEPA2Model.forward(pixel_values_videos, context_mask, target_mask, skip_predictor)` accepts masks, BUT the encoder runs on the **full** video and the context is then selected from its output, so context tokens have attended to future frames (leakage); the target is the un-layer-normed encoder output. This breaks the "context predicts future" semantics. **Use the official repo for M2**, with the same C-set, skip, 16-frame windows (M2 is trained at fpc64/256 px; 16-frame windows at 256 px are a distribution shift, to be recorded). Whether the checkpoint's predictor gives sensible surprises at 16 frames: UNCONFIRMED until run.
- Mask token index: official default `mask_index=1`; V-JEPA 2 has 10 mask tokens. Which index suits future prediction: UNCONFIRMED (record as deviation).
- Both repos use the top-level package name `src`: they cannot be imported in one process; the wrappers purge `sys.modules` before switching repos.

## 5. Other facts
- IntPhys 2 Debug: 60 videos = 15 scenes (SceneIndex values like `0`, `0_1`) x 4 types (`1_Possible, 1_Impossible, 2_Impossible, 2_Possible`), 636 frames, 60 fps, 512x512. Possible/impossible videos of one SceneIndex are **not** pixel-matched (mean |diff| ~3-4/255 already at frame 0). Natural pairs: `k_Possible` vs `k_Impossible`, k in {1,2} -> 30 pairs. Metadata has no event times.
- Dev frame count/size: 100 frames, 288x288 (checked).

## 6. Needs a lead decision / could NOT confirm
1. M1 checkpoint: Garrido RoPE ViT-L not public -> using released V-JEPA ViT-L/16 (non-RoPE). G1 at >= 90% vs reference 89.4% (their own vit-l-rope-vm2m, skip 2) may be unreachable; published 98% not reproduced from any released dev file. Consider G1 = within a stated tolerance of the released raw-surprise accuracy, plus a direct comparison against `raw_surprises` for the closest model.
2. 98% provenance, VideoMAEv2 weights source, M2 mask-token index and 16-frame behaviour: unconfirmed.
3. t = window index in released surprises: B3 event times (frame units) must be mapped to windows (window w covers sampled frames 2w..2w+15).
