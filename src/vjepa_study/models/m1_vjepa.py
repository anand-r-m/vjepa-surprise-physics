"""M1: V-JEPA via the RELEASED jepa-intuitive-physics code (init_model, get_time_masks).

The per-window loss block below is a VERBATIM transcription of the non-MAE branch of
``evals/intuitive_physics/eval.py::extract_losses`` (commit pinned in notes/PROTOCOL_NOTES.md):

    h = target_encoder(pieces, full_mask)[0]; h = layer_norm(h)
    targets = apply_masks(h, masks_pred); context = encoder(pieces, masks_enc)
    preds = predictor(context, targets, masks_enc, masks_pred)
    loss = l1(preds, targets).mean(tokens, features)

The only additions are (i) chunking windows into batches, (ii) returning per-tubelet spatially
pooled target features (for baseline B3), (iii) a `spatial_dim` argument so non-224 resolutions
build the right mask grid (identical to the release at 224).
"""
from __future__ import annotations

import os
import tempfile

import numpy as np

from . import common

DEFAULT_CKPT_URL = "https://dl.fbaipublicfiles.com/jepa/vitl16/vitl16.pth.tar"


class M1VJEPA:
    name = "M1"

    def __init__(self, ckpt_path=None, model_name="vit_large", resolution=224, patch_size=16,
                 tubelet_size=2, frames_per_clip=16, device=None, precision="fp32", pred_depth=12,
                 use_silu=False, wide_silu=True, uniform_power=True, repo_root=None,
                 random_init_seed=None, batch_windows=6):
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
        self.bw = batch_windows
        common.use_repo(common.external_dir("jepa-intuitive-physics", repo_root) / "evaluation_code")
        import evals.intuitive_physics.eval as ev          # released code
        import evals.intuitive_physics.utils as ut
        from src.masks.utils import apply_masks
        self.ev, self.ut, self.apply_masks = ev, ut, apply_masks
        torch.backends.cudnn.benchmark = False      # released eval.py sets True (timing-based autotune => run-to-run jitter)
        torch.backends.cudnn.deterministic = True
        self.F = torch.nn.functional
        tmp = None
        if random_init_seed is not None:        # M0r: released init_model with an empty checkpoint
            torch.manual_seed(int(random_init_seed))
            tmp = tempfile.NamedTemporaryFile(suffix=".pth.tar", delete=False)
            torch.save(dict(encoder={}, target_encoder={}, predictor={}, epoch=0), tmp.name)
            ckpt_path = tmp.name
        elif ckpt_path is None:
            raise ValueError("ckpt_path required for a trained M1")
        self.ckpt_path = ckpt_path
        self.encoder, self.target_encoder, self.predictor = ev.init_model(
            device=self.device, pretrained=ckpt_path, model_name=model_name, patch_size=patch_size,
            crop_size=resolution, frames_per_clip=frames_per_clip, tubelet_size=tubelet_size,
            use_sdpa=True, use_SiLU=use_silu, wide_SiLU=wide_silu, uniform_power=uniform_power,
            pred_depth=pred_depth)
        self.info = dict(precision=precision, device=str(self.device), ckpt=str(ckpt_path), model_name=model_name, resolution=resolution,
                         random_init_seed=random_init_seed)
        if random_init_seed is None:
            self._verify_loaded(ckpt_path)
        for m in (self.encoder, self.target_encoder, self.predictor):
            m.eval()
            for p in m.parameters():
                p.requires_grad = False
        if tmp is not None:
            os.unlink(tmp.name)

    def _verify_loaded(self, ckpt_path):
        """The released load_pretrained loads non-strictly and only logs missing keys. Check
        coverage ourselves; if the key naming differs (module./backbone. prefixes) remap and
        reload; raise if any model parameter is still not covered."""
        torch = self.torch
        ck = torch.load(ckpt_path, map_location="cpu")
        report = {}
        for attr, key in (("encoder", "encoder"), ("target_encoder", "target_encoder"), ("predictor", "predictor")):
            mod = getattr(self, attr)
            want = set(mod.state_dict().keys())
            raw = {k.replace("module.", ""): v for k, v in ck[key].items()}
            variants = [raw,
                        {("backbone." + k if not k.startswith("backbone.") else k): v for k, v in raw.items()},
                        {k.replace("backbone.", ""): v for k, v in raw.items()}]
            best = max(variants, key=lambda d: len(want & set(d)))
            if best is not raw:
                mod.load_state_dict({k: v for k, v in best.items() if k in want and v.shape == mod.state_dict()[k].shape},
                                    strict=False)
            shapes_ok = {k for k in want & set(best) if best[k].shape == mod.state_dict()[k].shape}
            missing = sorted(want - shapes_ok)
            report[attr] = dict(n_params=len(want), n_missing=len(missing), missing_head=missing[:5],
                                remapped=best is not raw)
        self.info["load_report"] = report
        if any(r["n_missing"] for r in report.values()):
            raise RuntimeError(f"checkpoint does not cover the model: {report}")

    # ---- verbatim loss block ------------------------------------------------------------
    def _window_losses(self, pieces, ctx_len, h=None):
        torch, F = self.torch, self.F
        B = pieces.shape[0]
        m, m_, full_m = self.ut.get_time_masks(ctx_len, spatial_size=(self.patch, self.patch),
                                               spatial_dim=(self.res, self.res), temporal_dim=self.fpc)
        full_m = full_m.unsqueeze(0).to(self.device)
        m = m.unsqueeze(0).to(self.device)
        m_ = m_.unsqueeze(0).to(self.device)
        masks_enc, masks_pred, full_mask = [m.repeat(B, 1)], [m_.repeat(B, 1)], [full_m.repeat(B, 1)]
        with torch.autocast(device_type=self.device.type, dtype=self.amp_dtype or torch.float16, enabled=self.amp_dtype is not None):
            if h is None:   # target features do not depend on C: computed once per window batch
                h = self.target_encoder(pieces, full_mask)[0]
                h = F.layer_norm(h, (h.size(-1),))
            targets = self.apply_masks(h, masks_pred, concat=False)
            context = self.encoder(pieces, masks_enc)
            preds = self.predictor(context, targets, masks_enc, masks_pred)
            loss = F.l1_loss(preds[0].float(), targets[0].float(), reduction="none").mean((1, 2))
        return loss.detach(), h

    @property
    def n_tub(self):
        return self.fpc // self.tub

    def surprise(self, frames, frame_step=2, ctx=common.DEFAULT_CTX, window=None, stride=2):
        torch = self.torch
        window = window or self.fpc
        if window != self.fpc:
            raise ValueError("window must equal frames_per_clip of the loaded model (build a "
                             "matching wrapper for the reduced window W' of B10)")
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
                # pooled target features per tubelet (same forward quantities; ctx independent)
                hp = h.float().view(h.shape[0], self.n_tub, -1, h.shape[-1]).mean(2).half().cpu().numpy()
                feats = hp if feats is None else np.concatenate([feats, hp])
        return dict(S=S, target_feats=feats, idx=idx)
