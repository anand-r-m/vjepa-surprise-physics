"""Amendment A1 edit/matching code (reviews/P0_spec_review.md B3-B6, B9, B10).

Conventions
-----------
* frames: uint8 (T,H,W,3), native resolution. Divergences and matching are measured at the
  MODEL INPUT resolution (default 224, bilinear, values in [0,1]) per B4.
* Event edits switch on at ``t_on`` and (if given) revert at ``t_off`` (dynamic-2).
* All float work is float32 with ONE final uint8 rounding (B6).
* Seeds drive only random nuisance parameters. ``is_deterministic(name)`` is True for
  edits whose output does not depend on the seed so runners can dedupe (MJ6).
* Matching is pixel-only and outcome-blind (no model outputs).
"""
from __future__ import annotations

import numpy as np
import cv2

from . import edits as _edits

cv2.setNumThreads(1)

MODEL_RES = 224
LEVEL_MULT = {"low": 0.5, "mid": 1.0, "high": 2.0}      # x s*  (A1.4)
BASE_FRAC = 0.9                                          # B6 base window (central 90%)

# ------------------------------------------------------------ determinism flags
DETERMINISTIC_EDITS = {"blur", "jpeg", "zoom", "hflip", "fps_halve", "vflip", "time_reversal",
                       "base_ref", "halve",
                       "zoom_base"}   # zoom-in only (zoom-out is capped by the 90% window)
SEEDED_EDITS = {"brightness", "noise", "dither", "lighting_global", "lighting_local",
                "jolt_base"}


def is_deterministic(name: str) -> bool:
    """True if the edit output is independent of the seed (runner runs seed 1 only and
    records the others as identical by construction, frame-hash verified)."""
    if name in DETERMINISTIC_EDITS:
        return True
    if name in SEEDED_EDITS or name in _edits.RANDOM_EDITS:
        return False
    raise KeyError(name)


# ---------------------------------------------------------------- resolution
def to_model_res(frames, res=MODEL_RES):
    """uint8 (T,H,W,3) -> float32 (T,res,res,3) in [0,1], bilinear (no antialias), the
    released loader's resize."""
    f = np.asarray(frames)
    if f.shape[1] == res and f.shape[2] == res:
        return f.astype(np.float32) / 255.0
    out = np.stack([cv2.resize(x, (res, res), interpolation=cv2.INTER_LINEAR) for x in f])
    return out.astype(np.float32) / 255.0


def divergence(a, b, res=MODEL_RES):
    """D(t) = mean over pixels and channels of |a(t) - b(t)| at model resolution, [0,1]."""
    A, B = to_model_res(a, res), to_model_res(b, res)
    n = min(len(A), len(B))
    return np.abs(A[:n] - B[:n]).mean(axis=(1, 2, 3))


# ---------------------------------------------------------------- B3 event window
def tau_rule(prefix_divergences, n_first=10):
    """tau = max(2/255, 99.9th percentile of D over the first `n_first` frames of all
    pairs). `prefix_divergences`: iterable of D(t) arrays (one per pair)."""
    vals = np.concatenate([np.asarray(d, float)[:n_first] for d in prefix_divergences])
    return float(max(2.0 / 255.0, np.percentile(vals, 99.9)))


def event_window(D, tau, min_quiet=5, seed=0, last_window_start_on=94):
    """Prereg section 4. t_on = first t with D>tau. t_off: if, after t_on, there is a run of >= `min_quiet`
    consecutive frames with D <= tau before frame T, t_off = first frame of the LAST such run, else T.
    No D > tau anywhere: seeded uniform draw in the middle 50% (fallback=True, count logged).
    `transient` = t_off < T; `excluded_late` = t_on > 94 (after the last window; excluded from H2)."""
    D = np.asarray(D, float)
    T = len(D)
    above = np.flatnonzero(D > tau)
    if len(above) == 0:
        lo, hi = T // 4, max(T // 4 + 1, (3 * T) // 4)
        t_on = int(np.random.default_rng([int(seed), 7919]).integers(lo, hi))
        return dict(t_on=t_on, t_off=T, fallback=True, transient=False, excluded_late=bool(t_on > last_window_start_on))
    t_on = int(above[0])
    quiet = D[t_on:] <= tau
    runs, start = [], None
    for j, q in enumerate(list(quiet) + [False]):
        if q and start is None:
            start = j
        elif not q and start is not None:
            if j - start >= min_quiet:
                runs.append(t_on + start)
            start = None
    t_off = int(runs[-1]) if runs else T
    return dict(t_on=t_on, t_off=t_off, fallback=False, transient=bool(t_off < T), excluded_late=bool(t_on > last_window_start_on))


# ---------------------------------------------------------------- spatial support (B5)
def violation_support(possible, impossible, t_on, t_off, res=MODEL_RES, thr=8.0 / 255.0,
                      min_area_px=64):
    """Support {x : |v-p| > thr for any t in the event window} at model resolution.
    Returns dict(center=(cy,cx) normalised to [0,1], area_frac, mask (res,res) bool)."""
    A = to_model_res(possible[t_on:t_off], res)
    B = to_model_res(impossible[t_on:t_off], res)
    n = min(len(A), len(B))
    m = (np.abs(A[:n] - B[:n]).mean(axis=-1) > thr).any(axis=0)
    area = max(int(m.sum()), int(min_area_px))
    if m.any():
        ys, xs = np.nonzero(m)
        cy, cx = (ys.mean() + 0.5) / res, (xs.mean() + 0.5) / res
    else:
        cy = cx = 0.5
    return dict(center=(float(cy), float(cx)), area_frac=float(area) / (res * res), mask=m)


def soft_disk(H, W, center, area_frac, edge=0.2):
    """Soft-edged disk in [0,1]: 1 inside, smoothstep fall-off over +-edge*R around R, with
    pi R^2 = area_frac*H*W (centre normalised (cy,cx))."""
    R = np.sqrt(area_frac * H * W / np.pi)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.hypot(yy + 0.5 - center[0] * H, xx + 0.5 - center[1] * W)
    w = max(edge * R, 1e-3)
    u = np.clip((R + w - r) / (2 * w), 0.0, 1.0)
    return (u * u * (3 - 2 * u)).astype(np.float32)


# ---------------------------------------------------------------- lighting edits
def gain_sign(seed):
    return float(np.random.default_rng([int(seed), 101]).choice([-1.0, 1.0]))


def _round_u8(x):
    return np.clip(np.rint(x), 0, 255).astype(np.uint8)


def lighting_event(frames, params, seed):
    """Multiplicative gain (1 + sign*amount*mask) on frames [t_on, t_off). `params`: amount,
    t_on, t_off (None = to end), region (None = global, else dict(center, area_frac, edge))."""
    f = _edits._check(frames)
    a = float(params["amount"])
    if a == 0:
        return f.copy()
    T, H, W, _ = f.shape
    t_on = int(params["t_on"])
    t_off = T if params.get("t_off") is None else int(params["t_off"])
    reg = params.get("region")
    mask = 1.0 if reg is None else soft_disk(H, W, reg["center"], reg["area_frac"], reg.get("edge", 0.2))[..., None]
    gain = 1.0 + gain_sign(seed) * a * mask
    out = f.copy()
    seg = f[t_on:t_off].astype(np.float32) * gain
    out[t_on:t_off] = _round_u8(seg)
    return out


def dither(frames, params, seed):
    """+-1 LSB noise floor (B9): integer noise uniform on {-1,0,+1} per pixel and channel.
    amount 0 = identity."""
    f = _edits._check(frames)
    if float(params["amount"]) == 0:
        return f.copy()
    n = np.random.default_rng([int(seed), 55]).integers(-1, 2, size=f.shape, dtype=np.int16)
    return np.clip(f.astype(np.int16) + n, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------- base window (B6)
def _window_matrix(H, W, frac, dx, dy):
    """cv2 inverse-map matrix: output pixel -> source pixel for a window of relative size
    `frac` centred at the frame centre plus (dx,dy) px, clamped to stay inside the frame.
    Returns (M, clipped)."""
    mx, my = (1 - frac) / 2 * W, (1 - frac) / 2 * H
    cdx, cdy = float(np.clip(dx, -mx, mx)), float(np.clip(dy, -my, my))
    cx, cy = (W - 1) / 2.0 + cdx, (H - 1) / 2.0 + cdy
    M = np.array([[frac, 0, cx - frac * (W - 1) / 2.0], [0, frac, cy - frac * (H - 1) / 2.0]], np.float64)
    return M, bool(cdx != dx or cdy != dy)


def window_video(frames, per_frame):
    """Render each frame through its window. per_frame: list of (frac, dx, dy). Float32
    bilinear warp, single final rounding. Returns (uint8 video, any_clipped)."""
    f = _edits._check(frames)
    T, H, W, _ = f.shape
    out = np.empty((T, H, W, 3), np.float32)
    clipped = False
    for i in range(T):
        M, c = _window_matrix(H, W, *per_frame[i])
        clipped |= c
        out[i] = cv2.warpAffine(f[i].astype(np.float32), M, (W, H),
                                flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP,
                                borderMode=cv2.BORDER_REPLICATE)
    return _round_u8(out), clipped


def base_ref(frames, params=None, seed=0):
    """Reference video: base window (central 90%) on all frames, no event (B6)."""
    T = len(frames)
    return window_video(frames, [(BASE_FRAC, 0.0, 0.0)] * T)[0]


def _event_mask(T, t_on, t_off):
    t_off = T if t_off is None else int(t_off)
    return np.array([int(t_on) <= t < t_off for t in range(T)])


def jolt_base(frames, params, seed):
    """Window offset shifts by `amount` px (native units, direction from seed) during
    [t_on, t_off). Returns (video, clipped_flag)."""
    f = _edits._check(frames)
    T = len(f)
    k = float(params["amount"])
    th = np.random.default_rng([int(seed), 202]).uniform(0, 2 * np.pi)
    ev = _event_mask(T, params["t_on"], params.get("t_off"))
    pf = [(BASE_FRAC, k * np.cos(th) * e, k * np.sin(th) * e) for e in ev]
    return window_video(f, pf)


def zoom_base(frames, params, seed=0):
    """Window scale shrinks from BASE_FRAC to BASE_FRAC*(1-amount) (zoom IN) during
    [t_on, t_off). Zoom-out is not offered: it is capped at 1/BASE_FRAC by the frame, so
    it cannot span the matched magnitudes. Seed-independent (deterministic)."""
    f = _edits._check(frames)
    T = len(f)
    a = float(params["amount"])
    ev = _event_mask(T, params["t_on"], params.get("t_off"))
    pf = [(BASE_FRAC * (1 - a * e), 0.0, 0.0) for e in ev]
    return window_video(f, pf)


# ---------------------------------------------------------------- B4 matching
def event_magnitude(edited, ref, t_on, t_off, res=MODEL_RES):
    """m = mean_{t in [t_on,t_off)} D(edited, ref) at model resolution."""
    D = divergence(edited, ref, res)
    t_off = len(D) if t_off is None else t_off
    return float(D[t_on:t_off].mean())


def pair_magnitude(possible, impossible, t_on, t_off, res=MODEL_RES):
    """m_i: violation magnitude of the pair over the event window (pixels only)."""
    return event_magnitude(impossible, possible, t_on, t_off, res)


def _bisect(fn, target, lo, hi, n_iter=30):
    """Solve fn(s)=target for non-decreasing fn on [lo,hi]. Returns (s, feasible)."""
    f_hi = fn(hi)
    if f_hi < target:
        return hi, False
    for _ in range(n_iter):
        mid = 0.5 * (lo + hi)
        if fn(mid) < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi), True


KINDS = ("lighting_global", "lighting_local", "jolt_base", "zoom_base")
AMOUNT_MAX = {"lighting_global": 3.0, "lighting_local": 3.0, "jolt_base": None, "zoom_base": 0.6}


def _edit_and_ref(kind, seg, amount, seed, region):
    """Edit and reference for a segment whose event spans the whole segment."""
    p = dict(amount=amount, t_on=0, t_off=None)
    if kind == "lighting_global":
        return lighting_event(seg, p, seed), seg
    if kind == "lighting_local":
        p["region"] = region
        return lighting_event(seg, p, seed), seg
    if kind == "jolt_base":
        return jolt_base(seg, p, seed)[0], base_ref(seg)
    if kind == "zoom_base":
        return zoom_base(seg, p, seed)[0], base_ref(seg)
    raise KeyError(kind)


def magnitude_of(kind, frames, amount, seed, t_on, t_off, region=None, res=MODEL_RES):
    """m_ik(amount) for the segment [t_on,t_off) of `frames` (full-video wrapper)."""
    seg = frames[t_on:t_off]
    e, r = _edit_and_ref(kind, seg, amount, seed, region)
    return event_magnitude(e, r, 0, None, res)


def solve_strength(kind, possible, m_i, t_on, t_off, seed, region=None, res=MODEL_RES,
                   n_refine=4):
    """s* with m_ik(s*) = m_i. Lighting: closed form (gain x unit-gain magnitude) then a
    few fixed-point corrections for clipping/rounding; jolt/zoom: bisection (sub-pixel).
    Returns dict(s_star, feasible, clipped_range). Infeasible -> clipped strength."""
    if kind not in KINDS:
        raise KeyError(kind)
    if m_i <= 0:
        return dict(s_star=0.0, feasible=False, clipped_range=True)
    fn = lambda s: magnitude_of(kind, possible, s, seed, t_on, t_off, region, res)
    if kind.startswith("lighting"):
        cap = AMOUNT_MAX[kind]
        unit = fn(0.05) / 0.05                   # slope of m vs amount (closed form, probe above rounding)
        s = m_i / max(unit, 1e-12)
        for _ in range(n_refine):                   # clipping / rounding correction
            m = fn(min(s, cap))
            if m <= 0:
                break
            s *= m_i / m
        feasible = s <= cap
        return dict(s_star=float(min(s, cap)), feasible=bool(feasible), clipped_range=not feasible)
    if kind == "jolt_base":
        hi = (1 - BASE_FRAC) / 2 * min(possible.shape[1], possible.shape[2])   # px margin
    else:
        hi = AMOUNT_MAX[kind]
    s, ok = _bisect(fn, m_i, 0.0, hi)
    return dict(s_star=float(s), feasible=bool(ok), clipped_range=not ok)


def match_pair(kind, possible, impossible, t_on, t_off, seed, res=MODEL_RES, use_region=None):
    """Full per-pair matching for one abrupt type. Returns dict with m_i, s_star, per-level
    strengths (low/mid/high = 0.5/1/2 x s*), achieved ratio r_k = m_ik/(level*m_i)."""
    t_off_ = len(possible) if t_off is None else t_off
    m_i = pair_magnitude(possible, impossible, t_on, t_off_, res)
    region = None
    if kind == "lighting_local":
        sup = violation_support(possible, impossible, t_on, t_off_, res)
        region = dict(center=sup["center"], area_frac=sup["area_frac"], edge=0.2)
    sol = solve_strength(kind, possible, m_i, t_on, t_off_, seed, region, res)
    out = dict(kind=kind, m_i=m_i, s_star=sol["s_star"], feasible=sol["feasible"], region=region)
    lv = {}
    for name, mult in LEVEL_MULT.items():
        s = sol["s_star"] * mult
        cap = AMOUNT_MAX[kind]
        if cap is not None:
            s = min(s, cap)
        m = magnitude_of(kind, possible, s, seed, t_on, t_off_, region, res)
        lv[name] = dict(amount=float(s), m=float(m), ratio=float(m / (mult * m_i)) if m_i > 0 else float("nan"))
    out["levels"] = lv
    return out


def apply_matched(kind, frames, match, level, seed, t_on, t_off):
    """Apply a matched edit at `level` to a full video. Returns (edited, reference)."""
    p = dict(amount=match["levels"][level]["amount"], t_on=t_on, t_off=t_off, region=match.get("region"))
    if kind.startswith("lighting"):
        return lighting_event(frames, p, seed), frames
    if kind == "jolt_base":
        return jolt_base(frames, p, seed)[0], base_ref(frames)
    return zoom_base(frames, p, seed)[0], base_ref(frames)


# ---------------------------------------------------------------- B10 sampling plans
def sampling_plan(T, frame_step, window=16, stride=2, halve=False, max_context=10):
    """Native-frame sampling plan. Released: n = (T-1)//step sampled frames (99//step for
    T=100), windows of `window` sampled frames every `stride`. Frame-rate halving doubles
    the native stride (frame duplication is prohibited). If the window no longer fits,
    reduce W' (even, >= max_context+2) and return the matched reference plan as well."""
    def plan(step, w):
        n = (min(T, 100) - 1) // step if T <= 100 else (T - 1) // step
        idx = np.arange(0, n * step, step)
        if len(idx) < w:
            return None
        return dict(frame_step=step, idx=idx, window=w, stride=stride,
                    n_windows=(len(idx) - w) // stride + 1)
    base = plan(frame_step, window)
    if not halve:
        if base is None:
            raise ValueError("window does not fit the clip")
        return dict(plan=base, reference=None, reduced=False)
    h_step = 2 * frame_step
    w = window
    while w >= max_context + 2 and plan(h_step, w) is None:
        w -= 2
    if w < max_context + 2:
        raise ValueError("no feasible window for halved stride")
    hp = plan(h_step, w)
    ref = plan(frame_step, w) if w != window else base
    return dict(plan=hp, reference=ref, reduced=(w != window))


def frame_hash(frames) -> str:
    """sha256 of a uint8 video; runners use it to verify 'identical by construction' for
    deterministic edits across seeds (MJ6)."""
    import hashlib
    f = np.ascontiguousarray(frames)
    return hashlib.sha256(f.tobytes() + str(f.shape).encode()).hexdigest()


def support_retention(mask, crop_frac):
    """MJ4: fraction of the violation-difference support (res x res bool mask) that stays
    inside a centre crop keeping `crop_frac` of each side (zoom/crop invariance edit).
    Pairs with retention < 0.9 are excluded from the confirmatory H1 test for that edit."""
    m = np.asarray(mask, bool)
    if not m.any():
        return 1.0
    H, W = m.shape
    mh, mw = int(round((1 - crop_frac) / 2 * H)), int(round((1 - crop_frac) / 2 * W))
    return float(m[mh:H - mh, mw:W - mw].sum() / m.sum())
