"""IntPhys 2 Main dataset support, kept OUT of kaggle/common/run_lib.py on purpose.

prereg s1 same-code-path rule: the decoded kernel bundles of contrasted groups must be byte-identical except the
permitted files; kaggle/common/run_lib.py is not permitted to differ from the 4c4017b h1/h2 bundles. This module is
therefore bundled ONLY into ip2main_* groups (kaggle/build_kernel.py) and patches run_lib at import time of the kernel:
  - run_lib.iter_items gains dataset "ip2main" (identical loading and preprocessing to "ip2debug": same
    data.ip2_pairs / data.load_ip2_video(max_frames=100, stride=4), i.e. 60 fps -> 15 fps, first 100 frames),
    every other dataset is delegated unchanged;
  - run_lib.main is wrapped only to resolve the IntPhys 2 root (run_lib.main resolves it for "ip2debug" only).
Models, windows, baselines, aggregation, fp16 flags and sharding are untouched (run_lib.run_one is not patched).
"""
from __future__ import annotations

import json
from pathlib import Path

from vjepa_study import data

SPLIT = "Main"
_STATE = {"ip2_root": None}


def iter_items_main(run, ip2_root):
    """Same item dicts as run_lib.iter_items for ip2debug, over <root>/Main. block = metadata `condition`."""
    members = run.get("members", "all")
    sub = run.get("subset") or {}
    split = Path(ip2_root) / SPLIT
    pairs = data.ip2_pairs(split)
    pairs = pairs[:: sub.get("every", 1)][: sub.get("n", len(pairs))]
    for pos, imp, scene, k in pairs:
        for row, label in ((pos, 0), (imp, 1)):
            if members == "possible" and label == 1:
                continue
            fr = data.load_ip2_video(split, row, max_frames=100, stride=4)   # identical to the ip2debug branch
            yield dict(video_id=row["name"], label=label, pair_id=f"ip2m/{scene}/{k}", scene_id=f"ip2m/{scene}",
                       block=row["condition"], frames=fr)


def install(run_lib):
    """Patch `run_lib` (the imported module object) in place; idempotent."""
    if getattr(run_lib, "_ip2main_installed", False):
        return run_lib
    orig_iter, orig_main = run_lib.iter_items, run_lib.main

    def iter_items(run, dev_root=None, ip2_root=None):
        if run["dataset"] == "ip2main":
            yield from iter_items_main(run, ip2_root or _STATE["ip2_root"])
        else:
            yield from orig_iter(run, dev_root, ip2_root)

    def main(runs_json, out_root, input_root="/kaggle/input", work="/kaggle/working", build_model=None,
             bundle_info=None, log=print):
        cfg = json.load(open(runs_json))
        if any(r["dataset"] == "ip2main" for r in cfg["runs"]):
            _STATE["ip2_root"] = run_lib.find_ip2(Path(cfg.get("ip2_path") or Path(input_root) / cfg.get("ip2_dataset", "intphys2")))
            if not (_STATE["ip2_root"] / SPLIT / "metadata.csv").exists():
                raise FileNotFoundError(f"IntPhys 2 {SPLIT}/metadata.csv missing under {_STATE['ip2_root']}")
            log(f"ip2main root {_STATE['ip2_root']}")
        return orig_main(runs_json, out_root, input_root, work, build_model, bundle_info, log)

    run_lib.iter_items, run_lib.main, run_lib._ip2main_installed = iter_items, main, True
    return run_lib
