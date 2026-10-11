"""Deterministic video edits (PROJECT_SPEC section 4).

All edits are pure functions ``edit(frames, params, seed) -> frames`` with
``frames`` a uint8 array of shape (T, H, W, 3). Output has the same shape and dtype.
``params`` is a dict containing at least ``amount`` (strength 0 -> exact identity).
Specificity edits also use ``t_star`` (int frame index); if None it is drawn from the
seeded RNG uniformly in the middle 50% of the clip.

Strength tables come from configs/edit_params.yaml. They are PLACEHOLDERS
(TODO-calibrate in P3); nothing here fixes the final values.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
import yaml

cv2.setNumThreads(1)

LEVEL_NAMES = {"low": 1.0, "mid": 2.0, "high": 3.0, "identity": 0.0}


# ----------------------------------------------------------------- helpers
def _check(frames):
    frames = np.asarray(frames)
    if frames.dtype != np.uint8 or frames.ndim != 4 or frames.shape[-1] != 3:
        raise ValueError(f"frames must be uint8 (T,H,W,3); got {frames.dtype} {frames.shape}")
    return frames


def _rng(seed):
    return np.random.default_rng(int(seed))


def _clip_u8(x):
    return np.clip(np.rint(x), 0, 255).astype(np.uint8)


def resolve_t_star(T, params, seed):
    """Event time: params['t_star'] if given, else seeded uniform in the middle 50%."""
    t = params.get("t_star")
    if t is not None:
        return int(min(max(int(t), 0), T - 1))
    lo, hi = T // 4, max(T // 4 + 1, (3 * T) // 4)
    # independent stream so the draw does not depend on other edit randomness
    return int(np.random.default_rng([int(seed), 7919]).integers(lo, hi))


def _warp_frames(frames, mats, interp=cv2.INTER_LINEAR):
    """Apply a 2x3 affine matrix per frame (mats: list aligned with frames, None = keep)."""
    T, H, W, _ = frames.shape
    out = frames.copy()
    for i in range(T):
        if mats[i] is not None:
            out[i] = cv2.warpAffine(frames[i], mats[i], (W, H), flags=interp,
                                    borderMode=cv2.BORDER_REPLICATE)
    return out


def _zoom_matrix(H, W, frac):
    """Centre-crop removing `frac` of each side-length, resized back to (H,W)."""
    z = 1.0 / max(1.0 - frac, 1e-6)
    cx, cy = (W - 1) / 2.0, (H - 1) / 2.0
    return np.array([[z, 0, cx * (1 - z)], [0, z, cy * (1 - z)]], dtype=np.float64)


# ------------------------------------------------------------------- edits
def brightness(frames, params, seed):
    a = float(params["amount"])
    if a == 0:
        return frames.copy()
    rng = _rng(seed)
    sign = rng.choice([-1.0, 1.0])
    jitter = rng.uniform(-a / 2, a / 2, size=3)
    gain = (1.0 + sign * a) * (1.0 + jitter)
    return _clip_u8(frames.astype(np.float32) * gain.astype(np.float32))


def blur(frames, params, seed):
    s = float(params["amount"])
    if s == 0:
        return frames.copy()
    return np.stack([cv2.GaussianBlur(f, (0, 0), s) for f in frames])


def jpeg(frames, params, seed):
    drop = float(params["amount"])
    if drop == 0:
        return frames.copy()
    q = int(min(max(round(100 - drop), 1), 100))
    out = np.empty_like(frames)
    for i, f in enumerate(frames):
        ok, buf = cv2.imencode(".jpg", f[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, q])
        assert ok
        out[i] = cv2.imdecode(buf, cv2.IMREAD_COLOR)[..., ::-1]
    return out


def noise(frames, params, seed):
    s = float(params["amount"])
    if s == 0:
        return frames.copy()
    n = _rng(seed).normal(0.0, s, size=frames.shape).astype(np.float32)
    return _clip_u8(frames.astype(np.float32) + n)


def zoom(frames, params, seed):
    f = float(params["amount"])
    if f == 0:
        return frames.copy()
    T, H, W, _ = frames.shape
    M = _zoom_matrix(H, W, f)
    return _warp_frames(frames, [M] * T)


def hflip(frames, params, seed):
    return frames.copy() if float(params["amount"]) == 0 else frames[:, :, ::-1].copy()


def fps_halve(frames, params, seed):
    """Frame-rate halving is NOT a frame edit (A1.9/B10): it is a doubled native sampling
    stride, see ``amend.sampling_plan(halve=True)``. Frame duplication is prohibited.
    amount 0 -> identity; amount > 0 -> NotImplementedError."""
    if float(params["amount"]) == 0:
        return frames.copy()
    raise NotImplementedError("frame duplication is prohibited (B10); use amend.sampling_plan(halve=True)")


def lighting_step(frames, params, seed):
    a = float(params["amount"])
    if a == 0:
        return frames.copy()
    t = resolve_t_star(len(frames), params, seed)
    out = frames.copy()
    out[t:] = _clip_u8(frames[t:].astype(np.float32) * (1.0 + a))
    return out


def camera_jolt(frames, params, seed):
    k = float(params["amount"])
    if k == 0:
        return frames.copy()
    T = len(frames)
    t = resolve_t_star(T, params, seed)
    theta = _rng(seed).uniform(0, 2 * np.pi)
    M = np.array([[1, 0, k * np.cos(theta)], [0, 1, k * np.sin(theta)]], dtype=np.float64)
    return _warp_frames(frames, [None] * t + [M] * (T - t))


def sudden_zoom(frames, params, seed):
    f = float(params["amount"])
    if f == 0:
        return frames.copy()
    T, H, W, _ = frames.shape
    t = resolve_t_star(T, params, seed)
    M = _zoom_matrix(H, W, f)
    return _warp_frames(frames, [None] * t + [M] * (T - t))


def vflip(frames, params, seed):
    return frames.copy() if float(params["amount"]) == 0 else frames[:, ::-1].copy()


def time_reversal(frames, params, seed):
    return frames.copy() if float(params["amount"]) == 0 else frames[::-1].copy()


EDIT_FUNCS = {
    "brightness": brightness, "blur": blur, "jpeg": jpeg, "noise": noise, "zoom": zoom,
    "hflip": hflip, "fps_halve": fps_halve,
    "lighting_step": lighting_step, "camera_jolt": camera_jolt, "sudden_zoom": sudden_zoom,
    "vflip": vflip, "time_reversal": time_reversal,
}
# edits whose randomness is in params/seed (different seed -> different output)
RANDOM_EDITS = {"brightness", "noise", "camera_jolt", "lighting_step", "sudden_zoom"}


# ---------------------------------------------------------------- registry
def default_config_path() -> Path:
    env = os.environ.get("VJEPA_EDIT_PARAMS")
    if env:
        return Path(env)
    # repo layout: <root>/src/vjepa_study/edits.py -> <root>/configs/edit_params.yaml
    return Path(__file__).resolve().parents[2] / "configs" / "edit_params.yaml"


@lru_cache(maxsize=8)
def _load_table(path: str):
    with open(path) as fh:
        cfg = yaml.safe_load(fh)
    return cfg


def load_registry(path=None) -> dict:
    """Return {edit_name: {'kind', 'unit', 'levels', 'amounts', 'fn'}} (placeholder table)."""
    cfg = _load_table(str(path or default_config_path()))
    reg = {}
    for name, e in cfg["edits"].items():
        if name not in EDIT_FUNCS:
            raise KeyError(f"config edit {name!r} has no implementation")
        reg[name] = dict(kind=e["kind"], unit=e.get("unit", ""), levels=list(cfg["levels"]),
                         amounts=[float(x) for x in e["amounts"]], fn=EDIT_FUNCS[name])
    missing = set(EDIT_FUNCS) - set(reg)
    if missing:
        raise KeyError(f"edits missing from config: {sorted(missing)}")
    return reg


def edit_names(kind=None, path=None):
    reg = load_registry(path)
    return [n for n, e in reg.items() if kind is None or e["kind"] == kind]


def params_for(name, strength, path=None) -> dict:
    """strength -> params. strength: 0/'identity', 'low'|'mid'|'high', or a float in level
    units (piecewise-linear interpolation, linear extrapolation beyond the last level)."""
    e = load_registry(path)[name]
    s = LEVEL_NAMES[strength] if isinstance(strength, str) else float(strength)
    lv, am = e["levels"], e["amounts"]
    if s <= 0:
        amount = 0.0
    elif s <= lv[-1]:
        amount = float(np.interp(s, lv, am))
    else:
        slope = (am[-1] - am[-2]) / (lv[-1] - lv[-2])
        amount = am[-1] + slope * (s - lv[-1])
    return {"amount": amount, "t_star": None}


def edit(frames, params, seed, name=None):
    """Generic entry point: edit(frames, params, seed, name=...)."""
    name = name or params["name"]
    return EDIT_FUNCS[name](_check(frames), params, seed)


def apply_edit(frames, name, strength, seed, t_star=None, path=None):
    p = params_for(name, strength, path)
    p["t_star"] = t_star
    return EDIT_FUNCS[name](_check(frames), p, seed)


def pair_edit(frames_a, frames_b, name, params, seed):
    """Apply IDENTICAL params and seed to both members of a pair (PROJECT_SPEC section 8).

    The event time t* is resolved once (from params or the seed) and shared. Returns
    (edited_a, edited_b, used_params).
    """
    frames_a, frames_b = _check(frames_a), _check(frames_b)
    if frames_a.shape != frames_b.shape:
        raise ValueError("pair members must have the same shape")
    used = dict(params)
    used["t_star"] = resolve_t_star(len(frames_a), params, seed)
    fn = EDIT_FUNCS[name]
    return fn(frames_a, used, seed), fn(frames_b, used, seed), used


# --------------------------------------------------- magnitude (section 4)
def pixel_delta(impossible, possible, t_event=0) -> float:
    """|Delta| = mean |impossible - possible| over frames from t_event on (0-255 scale)."""
    a, b = _check(impossible), _check(possible)
    if a.shape != b.shape:
        raise ValueError("shape mismatch")
    return float(np.abs(a[t_event:].astype(np.float32) - b[t_event:].astype(np.float32)).mean())


def edit_delta(frames, name, strength, seed, t_star=None, path=None) -> float:
    """|Delta| of an abrupt edit: mean |edited - original| over frames from t*."""
    p = params_for(name, strength, path)
    p["t_star"] = t_star
    t = resolve_t_star(len(frames), p, seed)
    out = EDIT_FUNCS[name](_check(frames), p, seed)
    return pixel_delta(out, frames, t)


def match_strength(clips, name, target_median, seeds=None, t_stars=None, tol=0.1,
                   max_iter=40, hi0=1.0, path=None):
    """Bisection on strength (level units) so the median |Delta| over `clips` equals
    `target_median` within relative `tol` (default 10%).

    Returns dict(strength, median, rel_err, converged, deltas). Assumes |Delta| is
    non-decreasing in strength (true for the abrupt edits up to saturation).
    """
    n = len(clips)
    seeds = list(range(n)) if seeds is None else list(seeds)
    t_stars = [None] * n if t_stars is None else list(t_stars)

    def med(s):
        d = [edit_delta(c, name, s, sd, ts, path) for c, sd, ts in zip(clips, seeds, t_stars)]
        return float(np.median(d)), d

    lo, hi = 0.0, hi0
    m_hi, d_hi = med(hi)
    for _ in range(12):
        if m_hi >= target_median:
            break
        lo, hi = hi, hi * 2
        m_hi, d_hi = med(hi)
    best = (hi, m_hi, d_hi)
    for _ in range(max_iter):
        mid = (lo + hi) / 2
        m, d = med(mid)
        best = (mid, m, d)
        if abs(m - target_median) <= tol * target_median:
            break
        if m < target_median:
            lo = mid
        else:
            hi = mid
    s, m, d = best
    rel = abs(m - target_median) / target_median if target_median else float("nan")
    return dict(strength=s, median=m, rel_err=rel, converged=bool(rel <= tol), deltas=d)
