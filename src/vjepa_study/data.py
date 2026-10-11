"""Data loaders and pair construction (PROJECT_SPEC Amendments A1.2).

IntPhys dev layout: <root>/O{1,2,3}/<scene>/<1-4>/scene/scene_###.png + status.json
(header.is_possible). IntPhys 2: <root>/{Debug,Main}/metadata.csv + Videos/*.mp4.

Pair rule = the released jepa-intuitive-physics code (``get_breaking_points`` /
``get_matches``): video 0 is paired with the video that diverges LATEST from it
(prefix-sharing pair); the remaining two videos form the second pair.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import cv2
import numpy as np

cv2.setNumThreads(1)

BLOCKS = ("O1", "O2", "O3")


# --------------------------------------------------------------- frames
def sample_indices(T, frame_step, num_frames=None):
    """Native-frame indices used by the released loader: frames[0 : n*step : step],
    n = 99 // frame_step by default (IntPhys: 49 frames at step 2)."""
    n = (99 // frame_step) if num_frames is None else num_frames
    return np.arange(0, min(T, n * frame_step), frame_step)


def load_png_sequence(scene_dir):
    """Load <scene_dir>/scene_###.png (sorted) -> uint8 (T,H,W,3) RGB."""
    files = sorted(Path(scene_dir).glob("scene_*.png"))
    if not files:
        raise FileNotFoundError(f"no scene_*.png under {scene_dir}")
    out = []
    for f in files:
        im = cv2.imread(str(f), cv2.IMREAD_COLOR)
        if im is None:
            raise IOError(f"cannot read {f}")
        out.append(im[..., ::-1])
    return np.ascontiguousarray(np.stack(out))


def load_mp4(path, max_frames=None, stride=1):
    """Decode an mp4 to uint8 (T,H,W,3) RGB; keep every `stride`-th frame."""
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise IOError(f"cannot open {path}")
    fr, i = [], 0
    while True:
        ok, f = cap.read()
        if not ok:
            break
        if i % stride == 0:
            fr.append(f[..., ::-1])
            if max_frames is not None and len(fr) >= max_frames:
                break
        i += 1
    cap.release()
    if not fr:
        raise IOError(f"no frames in {path}")
    return np.ascontiguousarray(np.stack(fr))


# --------------------------------------------------------- IntPhys dev
def _read_status(video_dir):
    p = Path(video_dir) / "status.json"
    with open(p) as fh:
        return bool(json.load(fh)["header"]["is_possible"])


def list_dev_scenes(root, blocks=BLOCKS):
    """Sorted [(block, scene_name)] for every scene dir containing 4 videos."""
    root = Path(root)
    if is_npz_root(root):
        names = sorted({tuple(p.stem.split("_")[:2]) for p in root.glob("O*_*_1.npz")})
        return [(b, sc) for b, sc in names if b in blocks]
    out = []
    for b in blocks:
        if not (root / b).exists():
            continue
        for s in sorted(p.name for p in (root / b).iterdir() if p.is_dir()):
            out.append((b, s))
    return out


def is_npz_root(root):
    return any(Path(root).glob("O1_01_1.npz")) or any(Path(root).glob("O*_*_1.npz"))


def load_dev_quadruplet(root, block, scene):
    """Return (frames (4,T,H,W,3) uint8, is_possible (4,) bool, video_ids list).
    Accepts the PNG tree or the packed one-npz-per-video layout (scripts/make_dev_npz.py)."""
    if is_npz_root(root):
        vids, lab, ids = [], [], []
        for k in (1, 2, 3, 4):
            with np.load(Path(root) / f"{block}_{scene}_{k}.npz") as z:
                vids.append(z["frames"]); lab.append(bool(z["is_possible"]))
            ids.append(f"{block}/{scene}/{k}")
        T = min(len(v) for v in vids)
        return np.stack([v[:T] for v in vids]), np.array(lab, bool), ids
    vids, lab, ids = [], [], []
    for k in (1, 2, 3, 4):
        d = Path(root) / block / scene / str(k)
        vids.append(load_png_sequence(d / "scene"))
        lab.append(_read_status(d))
        ids.append(f"{block}/{scene}/{k}")
    T = min(len(v) for v in vids)
    return np.stack([v[:T] for v in vids]), np.array(lab, bool), ids


def breaking_points(frames4, frame_step=2, signed=True):
    """Released ``get_breaking_points``: first subsampled-frame index where video 0 differs
    from video j (j=1,2,3); T_sub if never. ``signed=True`` replicates the released
    signed sum over (C,H,W); ``signed=False`` uses an absolute-value test (safer)."""
    idx = sample_indices(frames4.shape[1], frame_step)
    sub = frames4[:, idx].astype(np.float64)
    bps = []
    for j in (1, 2, 3):
        d = sub[0] - sub[j]
        if not signed:
            d = np.abs(d)
        nz = np.flatnonzero(d.sum(axis=(1, 2, 3)) != 0)
        bps.append(int(nz[0]) if len(nz) else len(idx))
    return bps


def get_matches(bps):
    """Released ``get_matches`` (np.argmax picks the first max, as in the original)."""
    a = int(np.argmax(bps))
    if a == 0:
        return [[0, 1], [2, 3]]
    if a == 1:
        return [[0, 2], [1, 3]]
    return [[0, 3], [1, 2]]


def make_pairs(frames4, is_possible, frame_step=2, signed=True):
    """Pairs for one quadruplet -> list of (idx_possible, idx_impossible).

    Raises if a matched pair does not contain exactly one possible and one impossible
    video (the released evaluation assumes this).
    """
    pairs = []
    for a, b in get_matches(breaking_points(frames4, frame_step, signed)):
        if bool(is_possible[a]) == bool(is_possible[b]):
            raise ValueError("matched pair does not contain one possible and one impossible video")
        pairs.append((a, b) if is_possible[a] else (b, a))
    return pairs


def prefix_partner(frames_pos, frames_imp_candidates):
    """Index of the impossible candidate that diverges LATEST from `frames_pos`
    (its prefix-sharing partner, A1.2). Used for t* / matching regardless of the
    evaluation pairing."""
    best, best_t = None, -1
    for i, v in enumerate(frames_imp_candidates):
        d = np.abs(frames_pos.astype(np.int16) - v.astype(np.int16)).sum(axis=(1, 2, 3))
        nz = np.flatnonzero(d)
        t = int(nz[0]) if len(nz) else len(d)
        if t > best_t:
            best, best_t = i, t
    return best


def iter_dev_pairs(root, blocks=BLOCKS, frame_step=2):
    """Yield dict(pair_id, scene_id (quadruplet), block, possible, impossible (frames),
    possible_id, impossible_id, quad (4,T,H,W,3)). 2 pairs per quadruplet."""
    for block, scene in list_dev_scenes(root, blocks):
        frames4, lab, ids = load_dev_quadruplet(root, block, scene)
        for k, (ip, ii) in enumerate(make_pairs(frames4, lab, frame_step)):
            yield dict(pair_id=f"{block}/{scene}/p{k}", scene_id=f"{block}/{scene}", block=block,
                       possible=frames4[ip], impossible=frames4[ii],
                       possible_id=ids[ip], impossible_id=ids[ii])


def dev_manifest(root, frame_step=2):
    """Counts only (no model outputs): n scenes, n pairs, per block."""
    n_scene = {b: 0 for b in BLOCKS}
    n_pairs = {b: 0 for b in BLOCKS}
    for b, s in list_dev_scenes(root):
        n_scene[b] += 1
        f4, lab, _ = load_dev_quadruplet(root, b, s)
        n_pairs[b] += len(make_pairs(f4, lab, frame_step))
    return dict(scenes_per_block=n_scene, pairs_per_block=n_pairs,
                n_scenes=sum(n_scene.values()), n_pairs=sum(n_pairs.values()))


# ------------------------------------------------------------ IntPhys 2
def read_ip2_metadata(split_dir):
    with open(Path(split_dir) / "metadata.csv", newline="") as fh:
        return list(csv.DictReader(fh))


def ip2_pairs(split_dir):
    """Pairs (possible_row, impossible_row, scene_index, k) from metadata: rows of one
    SceneIndex with types '<k>_Possible' / '<k>_Impossible'. IntPhys 2 pairs are NOT
    pixel-matched (checked on Debug)."""
    rows = read_ip2_metadata(split_dir)
    by = {}
    for r in rows:
        k, kind = r["type"].split("_", 1)
        by.setdefault((r["SceneIndex"], k), {})[kind] = r
    out = []
    for (scene, k), d in sorted(by.items()):
        if "Possible" in d and "Impossible" in d:
            out.append((d["Possible"], d["Impossible"], scene, k))
    return out


def load_ip2_video(split_dir, row, max_frames=None, stride=1):
    return load_mp4(Path(split_dir) / row["file_name"], max_frames=max_frames, stride=stride)
