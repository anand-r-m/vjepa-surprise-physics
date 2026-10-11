"""SSIM-based strength calibration of the graded invariance edits (PREREGISTRATION 'Edit
parameters'): strength giving mean SSIM to the original of 0.95 / 0.85 / 0.70. CPU only."""
from __future__ import annotations

import cv2
import numpy as np

from . import edits

TARGETS = {"low": 0.95, "mid": 0.85, "high": 0.70}
C1, C2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2


def ssim(a, b):
    """Mean SSIM of two uint8 (H,W,3) images (gaussian 11x11, sigma 1.5, per channel, valid
    region), the standard Wang et al. formulation."""
    a, b = a.astype(np.float64), b.astype(np.float64)
    k = cv2.getGaussianKernel(11, 1.5)
    f = lambda x: cv2.sepFilter2D(x, -1, k, k)[5:-5, 5:-5]
    out = []
    for c in range(a.shape[2]):
        x, y = a[..., c], b[..., c]
        mx, my = f(x), f(y)
        sxx, syy, sxy = f(x * x) - mx * mx, f(y * y) - my * my, f(x * y) - mx * my
        s = ((2 * mx * my + C1) * (2 * sxy + C2)) / ((mx * mx + my * my + C1) * (sxx + syy + C2))
        out.append(s.mean())
    return float(np.mean(out))


def mean_ssim(frames, edited):
    return float(np.mean([ssim(a, b) for a, b in zip(frames, edited)]))


def clip_square(frames, size=288):
    """Centre-crop to a square then resize to size x size (bilinear), like dev geometry."""
    T, H, W, _ = frames.shape
    s = min(H, W)
    y0, x0 = (H - s) // 2, (W - s) // 2
    out = [cv2.resize(f[y0:y0 + s, x0:x0 + s], (size, size), interpolation=cv2.INTER_AREA) for f in frames]
    return np.stack(out)


# --- edits in calibration units -------------------------------------------------------
def _apply(name, amount, frames, seed):
    return edits.EDIT_FUNCS[name](frames, dict(amount=amount, t_star=None), seed)


def edit_ssim(name, amount, frames, seeds=(1, 2, 3)):
    seeds = seeds if name in edits.RANDOM_EDITS else (1,)
    return float(np.mean([mean_ssim(frames, _apply(name, amount, frames, s)) for s in seeds]))


def clipped_fraction(frames, amount, seeds=(1, 2, 3)):
    """Fraction of pixel-channel values changed by clipping to [0,255] for the brightness
    gain edit (unclipped gain applied in float vs clipped result)."""
    fr = []
    for s in seeds:
        rng = np.random.default_rng(s)
        sign = rng.choice([-1.0, 1.0])
        jitter = rng.uniform(-amount / 2, amount / 2, size=3)
        raw = frames.astype(np.float32) * ((1.0 + sign * amount) * (1.0 + jitter)).astype(np.float32)
        fr.append(float(((raw > 255.5) | (raw < -0.5)).mean()))
    return float(np.mean(fr))


def solve(name, target, frames, lo, hi, n_iter=22, integer=False, increasing=True):
    """Bisection for the amount whose mean SSIM equals `target` (SSIM decreasing in amount
    if increasing=True). For integer parameters (JPEG quality) returns the nearest integer."""
    f = lambda a: edit_ssim(name, a, frames)
    if integer:
        best = min(range(int(lo), int(hi) + 1), key=lambda q: abs(edit_ssim(name, float(q), frames) - target))
        return float(best), edit_ssim(name, float(best), frames)
    a, b = lo, hi
    for _ in range(n_iter):
        m = 0.5 * (a + b)
        if (f(m) > target) == increasing:
            a = m
        else:
            b = m
    m = 0.5 * (a + b)
    return float(m), f(m)


def lab_L(frames):
    """CIELAB L* (0-100) of uint8 RGB frames (float32 conversion, D65)."""
    return np.stack([cv2.cvtColor(f.astype(np.float32) / 255.0, cv2.COLOR_RGB2Lab)[..., 0] for f in frames])


def mean_abs_dL(frames, edited):
    return float(np.abs(lab_L(edited) - lab_L(frames)).mean())


def brightness_dL(amount, frames, seeds=(1, 2, 3), L0=None):
    L0 = lab_L(frames) if L0 is None else L0
    return float(np.mean([np.abs(lab_L(_apply("brightness", amount, frames, s)) - L0).mean() for s in seeds]))


def solve_brightness_dL(target, frames, lo=0.0, hi=3.0, n_iter=24):
    L0 = lab_L(frames)
    a, b = lo, hi
    for _ in range(n_iter):
        m = 0.5 * (a + b)
        if brightness_dL(m, frames, L0=L0) < target:
            a = m
        else:
            b = m
    m = 0.5 * (a + b)
    return float(m), brightness_dL(m, frames, L0=L0)


DL_TARGETS = {"low": 5.0, "mid": 10.0, "high": 20.0}
CROP_SCALE = {"low": 0.9, "mid": 0.8, "high": 0.7}      # fixed by rule (SSIM ~0.99 is uninformative)
