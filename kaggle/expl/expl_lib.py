"""EXPLORATORY post-freeze edits, kept OUT of kaggle/common/run_lib.py and src/ on purpose (prereg s1 same-code-path rule,
same pattern as kaggle/ip2main). Bundled only into expl_* groups (kaggle/build_kernel.py) and patched into the imported
run_lib by kaggle/expl/preamble.py. Delegates every other edit unchanged.

halve_hold (corrected frame-rate halving, human request 2026-10-09: the pre-registered fps_halve is a design error,
its output is bit-identical to the skip-4 clean reference):
    g[t] = f[t - t % 4]  for every native frame t.
At frame step 2 the model samples native frames 0, 2, 4, ... ; sampled frames 2m and 2m+1 (native 4m and 4m+2) both
show native frame 4m. Temporal resolution is halved (25 Hz -> 12.5 Hz effective for a 25 Hz source), the time span and the
number and positions of sampled frames, tubelets and windows are those of the clean skip-2 run, so the clean skip-2
run is the paired reference window by window. It is deterministic (seed-free) and applied to both pair members.
"""
from __future__ import annotations

import numpy as np

EXPL_EDITS = ("halve_hold",)


def hold_halve(frames):
    """uint8 (T,H,W,3) -> same shape; frame t replaced by frame t - t % 4 (hold the previous kept frame)."""
    f = np.asarray(frames)
    idx = np.arange(len(f))
    return f[idx - idx % 4].copy()


def install(run_lib):
    """Patch `run_lib.apply_run_edit` in place; idempotent."""
    if getattr(run_lib, "_expl_installed", False):
        return run_lib
    orig = run_lib.apply_run_edit

    def apply_run_edit(item, edit, seed, matches=None):
        if edit and edit["name"] == "halve_hold":
            return hold_halve(item["frames"]), 1
        return orig(item, edit, seed, matches)

    run_lib.apply_run_edit, run_lib._expl_installed = apply_run_edit, True
    return run_lib
