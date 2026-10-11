"""Shared preprocessing / windowing (identical for all models) + released-repo import helper."""
from __future__ import annotations

import sys
import types
from pathlib import Path

import numpy as np

from .. import amend

IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)
DEFAULT_CTX = (2, 4, 6, 8, 10)


def repo_root() -> Path:
    here = Path(__file__).resolve()
    for p in here.parents:
        if (p / "external").exists() or (p / "code" / "external").exists():
            return p
    return here.parents[3]


def external_dir(name: str, root: Path | None = None) -> Path:
    """Locate external/<name> (local checkout or the bundle unpacked inside a kernel)."""
    root = Path(root) if root else repo_root()
    for cand in (root / "external" / name, root / "code" / "external" / name):
        if cand.exists():
            return cand
    raise FileNotFoundError(f"external/{name} not found under {root}")


def use_repo(path: Path, stub_videomae: bool = True):
    """Make `src.*` / `evals.*` resolve to this repo (both released repos use the top-level
    package name `src`; only ONE repo can be active per process state, so purge first)."""
    for k in [k for k in sys.modules if k == "src" or k.startswith("src.") or k == "evals" or k.startswith("evals.")]:
        del sys.modules[k]
    sys.path[:] = [p for p in sys.path if "evaluation_code" not in p and not p.endswith("vjepa2")]
    sys.path.insert(0, str(path))
    if stub_videomae:  # eval.py imports videomae at module level; not needed for the V-JEPA path
        sys.modules.setdefault("evals.intuitive_physics.videomae", types.ModuleType("videomae_stub"))


def preprocess(frames_u8, res, device="cpu"):
    """Released transform for square IntPhys frames: bilinear resize (align_corners=False,
    no antialias), ImageNet mean/std on the 0-255 scale. Returns float32 (T,3,res,res)."""
    import torch
    import torch.nn.functional as F
    x = torch.from_numpy(np.ascontiguousarray(frames_u8)).to(device).permute(0, 3, 1, 2).float()
    if x.shape[-2:] != (res, res):
        x = F.interpolate(x, size=(res, res), mode="bilinear", align_corners=False)
    mean = torch.tensor(IMAGENET_MEAN, device=device).view(1, 3, 1, 1) * 255.0
    std = torch.tensor(IMAGENET_STD, device=device).view(1, 3, 1, 1) * 255.0
    return (x - mean) / std


def make_windows(x, window, stride):
    """x (T,3,H,W) -> (nW,3,window,H,W), windows start every `stride` sampled frames."""
    starts = range(0, x.shape[0] - window + 1, stride)
    return __import__("torch").stack([x[s:s + window].permute(1, 0, 2, 3) for s in starts])


def sample(frames, frame_step, window, stride):
    """Apply the native sampling plan; returns (sampled uint8 frames, idx)."""
    plan = amend.sampling_plan(len(frames), frame_step, window, stride)["plan"]
    return frames[plan["idx"]], plan["idx"]
