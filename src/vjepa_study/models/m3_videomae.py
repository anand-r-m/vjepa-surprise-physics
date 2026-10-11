"""M3: VideoMAEv2 via the released `is_mae` branch of jepa-intuitive-physics (descriptive
only, MJ7). UNVERIFIED: the released repo has no MAE config or weight URL, so this requires a
checkpoint already converted to {'encoder': state_dict} for `videomae.<model_name>()`.

Surprise block = transcription of the `is_mae` branch with mae_decoder_blocks == -1:
targets are per-patch normalised pixels (p0=2 time, 16x16 space, unbiased std + 1e-6);
preds = encoder(pieces, masks_pred) (decoder output on the masked tokens); L1 over tokens.
"""
from __future__ import annotations

import numpy as np

from . import common


class M3VideoMAE:
    name = "M3"

    def __init__(self, ckpt_path, model_name="pretrain_videomae_giant_patch14_224", resolution=224,
                 patch_size=16, frames_per_clip=16, device=None, precision="fp32", repo_root=None,
                 batch_windows=2):
        import torch
        self.torch = torch
        self.device = torch.device(device or ("cuda:0" if torch.cuda.is_available() else "cpu"))
        self.res, self.patch, self.fpc = resolution, patch_size, frames_per_clip
        self.fp16 = precision == "fp16" and self.device.type == "cuda"
        self.bw = batch_windows
        common.use_repo(common.external_dir("jepa-intuitive-physics", repo_root) / "evaluation_code",
                        stub_videomae=False)
        import evals.intuitive_physics.eval as ev
        import evals.intuitive_physics.utils as ut
        self.ut = ut
        self.encoder, _, _ = ev.init_model(device=self.device, pretrained=ckpt_path, model_name=model_name,
                                           patch_size=patch_size, crop_size=resolution,
                                           frames_per_clip=frames_per_clip, is_mae=True,
                                           enc_checkpoint_key="encoder")
        self.encoder.eval()

    def _loss(self, pieces, ctx_len):
        from einops import rearrange
        torch = self.torch
        B = pieces.shape[0]
        m, m_, full_m = self.ut.get_time_masks(ctx_len, spatial_size=(self.patch, self.patch),
                                               spatial_dim=(self.res, self.res), temporal_dim=self.fpc, as_bool=True)
        masks_pred = m_.unsqueeze(0).to(self.device).repeat(B, 1)
        with torch.autocast(device_type=self.device.type, dtype=torch.float16, enabled=self.fp16):
            mean = torch.as_tensor((0.485, 0.456, 0.406), device=self.device)[None, :, None, None, None]
            std = torch.as_tensor((0.229, 0.224, 0.225), device=self.device)[None, :, None, None, None]
            unnorm = pieces * std + mean
            vs = rearrange(unnorm, "b c (t p0) (h p1) (w p2) -> b (t h w) (p0 p1 p2) c",
                           p0=2, p1=self.patch, p2=self.patch)
            var = vs.var(dim=-2, unbiased=True, keepdim=True).sqrt() + 1e-6
            vn = (vs - vs.mean(dim=-2, keepdim=True)) / var
            vp = rearrange(vn, "b n p c -> b n (p c)")
            targets = vp[masks_pred].reshape(B, -1, vp.shape[-1])
            preds = self.encoder(pieces, masks_pred, decoder_blocks=-1)
            return torch.nn.functional.l1_loss(preds.float(), targets.float(), reduction="none").mean((1, 2)).detach()

    def surprise(self, frames, frame_step=2, ctx=common.DEFAULT_CTX, window=None, stride=2):
        torch = self.torch
        window = window or self.fpc
        sub, idx = common.sample(frames, frame_step, window, stride)
        x = common.preprocess(sub, self.res, self.device)
        W = common.make_windows(x, window, stride)
        S = np.zeros((W.shape[0], len(ctx)), np.float32)
        with torch.no_grad():
            for a in range(0, W.shape[0], self.bw):
                piece = W[a:a + self.bw].contiguous()
                for j, c in enumerate(ctx):
                    S[a:a + piece.shape[0], j] = self._loss(piece, c).float().cpu().numpy()
        return dict(S=S, target_feats=None, idx=idx)
