"""surprise.npz schema (PROJECT_SPEC section 10: results/runs/<run_id>/surprise.npz).

Keys
----
video_ids : (N,) str      unique id per video (e.g. 'scene12_pair3_impossible')
surprise  : (N, Tmax) float32   per-video per-timestep surprise; entries at t >= lengths[i]
                          are NaN padding. Entries t < lengths[i] must be finite.
lengths   : (N,) int      number of valid timesteps per video (>= 1)
Optional (analysis helpers use them when present)
label     : (N,) int      1 = impossible, 0 = possible
pair_id   : (N,) str/int  video pairs share a pair_id (one possible + one impossible)
scene_id  : (N,) str/int  scene/group used for bootstrap resampling
t_star    : (N,) int      event timestep (-1 if none)

Amendment A1 optional keys (written by kaggle/common/run_lib.py)
S            (N, Wmax, nC) float32   released-protocol surprise per window and context length (NaN pad);
                                    `surprise` = min over C of S (the released "Filtered" curve)
context_lengths (nC,) int           C values (sampled frames)
target_feats (N, Wmax, n_tub, D) float16   spatially pooled layer-normed target features (B3)
B1, B2, B3   (N, Wmax, nC) float32  baselines on the same windows/preprocessing (MJ2)
block        (N,) str               IntPhys block O1/O2/O3 (bootstrap strata)
video_hash   (N,) str               sha256 of the (edited) uint8 input frames (dedupe check, MJ6)

Timestep indexing is the model's own surprise timestep; an adapter should document its
mapping from video frames in the run's meta.json.
"""
from __future__ import annotations

import numpy as np

REQUIRED = ("video_ids", "surprise", "lengths")
OPTIONAL = ("label", "pair_id", "scene_id", "t_star", "S", "context_lengths", "target_feats",
            "B1", "B2", "B3", "block", "video_hash")


class SchemaError(ValueError):
    pass


def save_surprise(path, video_ids, curves, **optional):
    """Save a list of 1-D surprise curves (ragged OK) in the standard layout."""
    lengths = np.array([len(c) for c in curves], dtype=np.int64)
    S = np.full((len(curves), int(lengths.max())), np.nan, dtype=np.float32)
    for i, c in enumerate(curves):
        S[i, : len(c)] = np.asarray(c, dtype=np.float32)
    d = dict(video_ids=np.asarray(video_ids).astype(str), surprise=S, lengths=lengths)
    d.update({k: np.asarray(v) for k, v in optional.items()})
    np.savez(path, **d)


def load_surprise(path, validate=True) -> dict:
    with np.load(path, allow_pickle=False) as z:
        d = {k: z[k] for k in z.files}
    if validate:
        validate_arrays(d)
    return d


def validate_arrays(d, expected_ids=None) -> None:
    """Raise SchemaError on any violation; optionally check ids equal `expected_ids`."""
    for k in REQUIRED:
        if k not in d:
            raise SchemaError(f"missing key {k!r}")
    ids, S, L = np.asarray(d["video_ids"]), np.asarray(d["surprise"]), np.asarray(d["lengths"])
    if S.ndim != 2:
        raise SchemaError("surprise must be 2-D (N, Tmax)")
    N, Tmax = S.shape
    if ids.shape != (N,) or L.shape != (N,):
        raise SchemaError("video_ids/lengths must have shape (N,) matching surprise rows")
    if len(set(ids.tolist())) != N:
        raise SchemaError("video_ids are not unique")
    if not np.issubdtype(L.dtype, np.integer) or (L < 1).any() or (L > Tmax).any():
        raise SchemaError("lengths must be integers in [1, Tmax]")
    if not np.issubdtype(S.dtype, np.floating):
        raise SchemaError("surprise must be floating point")
    valid = np.arange(Tmax)[None, :] < L[:, None]
    if not np.isfinite(S[valid]).all():
        raise SchemaError("non-finite surprise inside valid region")
    if not np.isnan(S[~valid]).all():
        raise SchemaError("padding beyond lengths must be NaN")
    for k in OPTIONAL:
        if k == "context_lengths":
            continue
        if k in d and np.asarray(d[k]).shape[0] != N:
            raise SchemaError(f"{k!r} must have length N")
    if "label" in d and not set(np.unique(d["label"]).tolist()) <= {0, 1}:
        raise SchemaError("label must be 0/1")
    if expected_ids is not None and list(ids.astype(str)) != list(np.asarray(expected_ids).astype(str)):
        raise SchemaError("video ids do not match expected ids (order matters)")


def check_matching_ids(a: dict, b: dict) -> None:
    """Two runs that will be compared must cover the same videos in the same order."""
    validate_arrays(a)
    validate_arrays(b, expected_ids=a["video_ids"])


def curves(d: dict):
    """List of 1-D valid-length arrays."""
    return [d["surprise"][i, : d["lengths"][i]] for i in range(len(d["lengths"]))]


def save_run(path, video_ids, S_list, feats_list=None, ctx=(2, 4, 6, 8, 10), baselines=None, **optional):
    """Write a run in the A1 layout. S_list: list of (W_i, nC) arrays; `surprise` = min over C.
    baselines: optional dict name -> list of (W_i, nC) arrays (B1/B2/B3)."""
    from pathlib import Path
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    N = len(S_list)
    nC = len(ctx)
    lengths = np.array([len(s) for s in S_list], np.int64)
    Wm = int(lengths.max())

    def pad(lst, tail):
        out = np.full((N, Wm) + tail, np.nan, np.float32)
        for i, a in enumerate(lst):
            out[i, : len(a)] = a
        return out
    S = pad(S_list, (nC,))
    d = dict(video_ids=np.asarray(video_ids).astype(str), surprise=np.nanmin(S, axis=2).astype(np.float32),
             lengths=lengths, S=S, context_lengths=np.asarray(ctx, np.int64))
    if feats_list is not None and feats_list[0] is not None:
        f0 = feats_list[0]
        tf = np.full((N, Wm) + f0.shape[1:], np.nan, np.float16)
        for i, a in enumerate(feats_list):
            tf[i, : len(a)] = a
        d["target_feats"] = tf
    for k, lst in (baselines or {}).items():
        d[k] = pad(lst, (nC,))
    d.update({k: np.asarray(v) for k, v in optional.items()})
    np.savez(path, **d)
