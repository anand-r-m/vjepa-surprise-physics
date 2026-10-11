"""M2: V-JEPA 2 via the OFFICIAL vjepa2 repo (not HF: HF encodes the full clip so context
tokens see future frames, see notes/PROTOCOL_NOTES.md section 4).

Same protocol as M1: context tokens come from `encoder(pieces, masks_enc)`; targets are the
layer-normed `target_encoder` outputs on the full window; surprise = L1 between predictor
output and targets over the target tokens. Deviations from the M1 release (recorded in
meta): 256 px input, RoPE, 16-frame windows (model pretrained at fpc 16/64), predictor
mask_index = `mask_index` (default 0, the value the official training code passes: PredictorMultiSeqWrapper
enumerates fpc groups from 0 and the released vitl.pt trained only mask token 0; see notes/M2_AUDIT.md,
notes/M2_FIX.md. Until 2026-10-08 the default was 1, an untrained zero token).
"""
from __future__ import annotations

import numpy as np

from . import common

CKPT_URL = "https://dl.fbaipublicfiles.com/vjepa2/vitl.pt"


class M2VJEPA2:
    name = "M2"

    def __init__(self, ckpt_path, resolution=256, patch_size=16, tubelet_size=2,
                 frames_per_clip=16, device=None, precision="fp32", mask_index=0, repo_root=None,
                 batch_windows=4, arch="vit_large"):
        import torch
        self.torch = torch
        self.device = torch.device(device or ("cuda:0" if torch.cuda.is_available() else "cpu"))
        self.res, self.patch, self.tub, self.fpc = resolution, patch_size, tubelet_size, frames_per_clip
        self.precision = precision
        self.amp_dtype = None
        if self.device.type == "cuda" and precision in ("fp16", "bf16"):
            self.amp_dtype = torch.float16 if precision == "fp16" else torch.bfloat16
        elif precision not in ("fp32", "fp16", "bf16"):
            raise ValueError(precision)
        self.mask_index, self.bw = mask_index, batch_windows
        common.use_repo(common.external_dir("vjepa2", repo_root), stub_videomae=False)
        from src.hub import backbones as bb
        from src.masks.utils import apply_masks
        self.apply_masks = apply_masks
        torch.backends.cudnn.benchmark = False      # released eval.py sets True (timing-based autotune => run-to-run jitter)
        torch.backends.cudnn.deterministic = True
        # build encoder/predictor shells with the official hub code, then load weights ourselves
        # (hub's VJEPA_BASE_URL points to localhost in the released file)
        enc_t, pred = bb._make_vjepa2_model(model_name=arch, img_size=resolution, pretrained=False,
                                            num_frames=frames_per_clip)
        enc_c, _ = bb._make_vjepa2_model(model_name=arch, img_size=resolution, pretrained=False,
                                         num_frames=frames_per_clip)
        sd = torch.load(ckpt_path, map_location="cpu")
        self.load_msgs = {
            "target_encoder": enc_t.load_state_dict(bb._clean_backbone_key(sd["target_encoder"]), strict=False),
            "encoder": enc_c.load_state_dict(bb._clean_backbone_key(sd["encoder"]), strict=False),
            "predictor": pred.load_state_dict(bb._clean_backbone_key(sd["predictor"]), strict=False),
        }
        self.target_encoder, self.encoder, self.predictor = (m.to(self.device).eval() for m in (enc_t, enc_c, pred))
        for m in (self.encoder, self.target_encoder, self.predictor):
            for p in m.parameters():
                p.requires_grad = False

    def _masks(self, ctx_len, B):
        g = self.res // self.patch
        per_t = g * g
        n_all = (self.fpc // self.tub) * per_t
        n_ctx = (ctx_len // self.tub) * per_t
        ids = self.torch.arange(n_all, device=self.device)
        rep = lambda t: t.unsqueeze(0).repeat(B, 1)
        return [rep(ids[:n_ctx])], [rep(ids[n_ctx:])], [rep(ids)]

    def _window_losses(self, pieces, ctx_len, h=None):
        torch, F = self.torch, self.torch.nn.functional
        B = pieces.shape[0]
        masks_enc, masks_pred, full_mask = self._masks(ctx_len, B)
        with torch.autocast(device_type=self.device.type, dtype=self.amp_dtype or torch.float16, enabled=self.amp_dtype is not None):
            if h is None:
                h = self.target_encoder(pieces)
                h = F.layer_norm(h, (h.size(-1),))
            targets = self.apply_masks(h, masks_pred, concat=False)[0]
            context = self.encoder(pieces, masks_enc)
            preds = self.predictor(context, masks_enc, masks_pred, mask_index=self.mask_index)
            loss = F.l1_loss(preds.float(), targets.float(), reduction="none").mean((1, 2))
        return loss.detach(), h

    def surprise(self, frames, frame_step=2, ctx=common.DEFAULT_CTX, window=None, stride=2):
        torch = self.torch
        window = window or self.fpc
        if window != self.fpc:
            raise ValueError("window must equal frames_per_clip")
        sub, idx = common.sample(frames, frame_step, window, stride)
        x = common.preprocess(sub, self.res, self.device)
        W = common.make_windows(x, window, stride)
        nW = W.shape[0]
        S = np.zeros((nW, len(ctx)), np.float32)
        feats = None
        with torch.no_grad():
            for a in range(0, nW, self.bw):
                piece = W[a:a + self.bw].contiguous()
                h = None
                for j, c in enumerate(ctx):
                    loss, h = self._window_losses(piece, c, h)
                    S[a:a + piece.shape[0], j] = loss.float().cpu().numpy()
                hp = h.float().view(h.shape[0], self.fpc // self.tub, -1, h.shape[-1]).mean(2).half().cpu().numpy()
                feats = hp if feats is None else np.concatenate([feats, hp])
        return dict(S=S, target_feats=feats, idx=idx)
