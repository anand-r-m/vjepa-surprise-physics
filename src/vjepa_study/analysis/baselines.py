"""Trivial baselines B1 and B2 on raw pixels (PROJECT_SPEC section 2). 0-255 scale."""
from __future__ import annotations

import numpy as np

__all__ = ["b1_framediff", "b2_copy_last", "b1_windows", "b2_windows", "b3_windows", "b1_whole_window"]


def _f(frames):
    return np.asarray(frames, dtype=np.float32)


def b1_framediff(frames):
    """B1: surprise_t = mean |f_t - f_{t-1}|, t = 1..T-1. Returns array of length T-1."""
    f = _f(frames)
    return np.abs(f[1:] - f[:-1]).mean(axis=(1, 2, 3))


def b2_copy_last(frames, window=None, mode="prev"):
    """B2: pixel error of the copy-last-frame predictor over the predicted window.

    window = (start, end) frame indices of the predicted frames (default: all frames
    from 1). mode='prev'  : predict f_t by f_{t-1}   (literal PROJECT_SPEC wording);
    mode='context': predict every window frame by f_{start-1}, the last context frame.
    Returns one error per predicted frame. NOTE: with mode='prev' B2 equals B1 restricted
    to the window; they differ only through the window (and aggregation).
    """
    f = _f(frames)
    T = len(f)
    s, e = (1, T) if window is None else window
    if s < 1 or e > T or s >= e:
        raise ValueError("window must satisfy 1 <= start < end <= T")
    ref = f[s - 1: e - 1] if mode == "prev" else np.repeat(f[s - 1: s], e - s, axis=0)
    if mode not in ("prev", "context"):
        raise ValueError(mode)
    return np.abs(f[s:e] - ref).mean(axis=(1, 2, 3))


# ----------------------------------------------------------------- windowed baselines (MJ1, MJ2)
# S[w, c] grids identical to the model's: windows of `window` SAMPLED frames every `stride`,
# context lengths `ctx` (sampled frames); baselines run on the same preprocessed frames
# (resized to model resolution, in [0,1]) at the same native stride.
def _windows(n_frames, window, stride):
    return [(s, s + window) for s in range(0, n_frames - window + 1, stride)]


def b1_windows(frames_sub, ctx=(2, 4, 6, 8, 10), window=16, stride=2):
    """B1: mean |f_p - f_{p-1}| over the predicted frames p = C..window-1 of each window."""
    f = np.asarray(frames_sub, np.float32)
    d = np.abs(f[1:] - f[:-1]).mean(axis=(1, 2, 3))           # d[t-1] = |f_t - f_{t-1}|
    W = _windows(len(f), window, stride)
    return np.array([[d[s + c - 1: e - 1].mean() for c in ctx] for s, e in W], np.float32)


def b2_windows(frames_sub, ctx=(2, 4, 6, 8, 10), window=16, stride=2):
    """B2 (A1/DECISIONS): copy-LAST-CONTEXT-frame error: predict every frame p >= C of the
    window by f_{C-1}; mean abs pixel error over predicted frames."""
    f = np.asarray(frames_sub, np.float32)
    out = []
    for s, e in _windows(len(f), window, stride):
        row = []
        for c in ctx:
            last = f[s + c - 1]
            row.append(np.abs(f[s + c: e] - last).mean())
        out.append(row)
    return np.array(out, np.float32)


def b3_windows(pooled_feats, ctx=(2, 4, 6, 8, 10), tubelet=2):
    """B3 encoder-change baseline: pooled_feats [W, n_tub, D] (spatially pooled, layer-normed
    target-encoder features per tubelet of each window). S[w,c] = mean over predicted
    tubelets j >= C/tubelet of mean_D |g_j - g_{j-1}|."""
    g = np.asarray(pooled_feats, np.float32)
    d = np.abs(g[:, 1:] - g[:, :-1]).mean(axis=-1)            # d[:, j-1] = change into tubelet j
    return np.stack([d[:, c // tubelet - 1:].mean(axis=1) for c in ctx], axis=1)


def b1_whole_window(frames_sub, window=16, stride=2):
    """Spec-literal B1: mean |f_t - f_{t-1}| over ALL frames of the window (C-independent; 15 differences
    per 16-frame window). Returned as (n_windows,). `b1_windows` restricts the same quantity to the
    predicted frames, which is the spec's literal B2 wording ("frame difference over the predicted window")."""
    f = np.asarray(frames_sub, np.float32)
    d = np.abs(f[1:] - f[:-1]).mean(axis=(1, 2, 3))
    return np.array([d[s:e - 1].mean() for s, e in _windows(len(f), window, stride)], np.float32)
