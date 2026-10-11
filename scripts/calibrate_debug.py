"""Debug-split edit-strength calibration (PREREGISTRATION 'Edit parameters'). Single re-runnable script.

  python scripts/calibrate_debug.py [--split data/intphys2/extracted/Debug] [--out results/analysis/calibration_debug.json]

Rules (CPU only, IntPhys 2 Debug only, no model, no dev frames):
  blur sigma, JPEG quality, noise std : mean SSIM to the original = 0.95 / 0.85 / 0.70
  brightness gain                     : mean absolute CIELAB L* change = 5 / 10 / 20
  centre crop                         : scale kept = 0.9 / 0.8 / 0.7 (fixed; SSIM is reported only)
Frames: 8 evenly spaced per Debug video (stride 80, first 8), centre-cropped square, INTER_AREA to 288x288.
Random edits (brightness, noise) are averaged over seeds 1-3. Writes the JSON, configs/edit_params_candidate.yaml
(configs/edit_params.yaml is not touched) and the [CAL] table in notes/CALIBRATION.md.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import yaml

from vjepa_study import calibrate as C, data

ROOT = Path(__file__).resolve().parents[1]
SSIM_SPEC = {"blur": (0.0, 40.0, False), "jpeg": (0, 99, True), "noise": (0.0, 200.0, False)}   # name: (lo, hi, integer)
LEVELS = ("low", "mid", "high")


def calibrate(frames):
    res = {}
    for name, (lo, hi, integer) in SSIM_SPEC.items():
        res[name] = {}
        for lvl, tgt in C.TARGETS.items():
            a, s = C.solve(name, tgt, frames, lo, hi, integer=integer)
            res[name][lvl] = dict(amount=a, ssim=s)
    res["brightness"] = {}
    for lvl, tgt in C.DL_TARGETS.items():
        a, d = C.solve_brightness_dL(tgt, frames)
        res["brightness"][lvl] = dict(amount=a, mean_abs_dL=d, ssim=C.edit_ssim("brightness", a, frames),
                                      clipped_fraction=C.clipped_fraction(frames, a))
    res["zoom"] = {}
    for lvl, sc in C.CROP_SCALE.items():
        res["zoom"][lvl] = dict(amount=1 - sc, crop_scale=sc, ssim=C.edit_ssim("zoom", 1 - sc, frames))
    return res


def cal_table(res):
    """Markdown [CAL] value table in the units used by the prereg (not registry units)."""
    g = lambda n, l, k: res[n][l][k]
    f = lambda n, k, fmt, conv=lambda x: x: " | ".join(format(conv(g(n, l, k)), fmt) for l in LEVELS)
    return "\n".join([
        "| edit | unit | low | mid | high | achieved low / mid / high |", "|---|---|---|---|---|---|",
        f"| brightness gain a | multiplicative gain 1 +- a (registry `amount`) | {f('brightness', 'amount', '.4f')} | mean abs dL* "
        + " / ".join(f"{g('brightness', l, 'mean_abs_dL'):.2f}" for l in LEVELS) + "; SSIM "
        + " / ".join(f"{g('brightness', l, 'ssim'):.3f}" for l in LEVELS) + "; clipped fraction "
        + " / ".join(f"{g('brightness', l, 'clipped_fraction'):.3f}" for l in LEVELS) + " |",
        f"| blur sigma | px at 224 (x288/224 on native 288 frames) | {f('blur', 'amount', '.3f', lambda x: x * 224 / 288)} | SSIM "
        + " / ".join(f"{g('blur', l, 'ssim'):.3f}" for l in LEVELS) + " |",
        f"| JPEG quality | quality factor (registry `amount` = 100 - quality) | {f('jpeg', 'amount', '.0f', lambda x: 100 - x)} | SSIM "
        + " / ".join(f"{g('jpeg', l, 'ssim'):.3f}" for l in LEVELS) + " (integer qualities) |",
        f"| noise std | [0,1] intensity units (registry = x255) | {f('noise', 'amount', '.4f', lambda x: x / 255)} | SSIM "
        + " / ".join(f"{g('noise', l, 'ssim'):.3f}" for l in LEVELS) + " |",
        "| centre crop | scale kept (registry `amount` = 1 - scale) | 0.9 | 0.8 | 0.7 | SSIM "
        + " / ".join(f"{g('zoom', l, 'ssim'):.3f}" for l in LEVELS) + " (reported only) |"])


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default=str(ROOT / "data/intphys2/extracted/Debug"))
    ap.add_argument("--out", default=str(ROOT / "results/analysis/calibration_debug.json"))
    ap.add_argument("--notes", default=str(ROOT / "notes/CALIBRATION.md"))
    ap.add_argument("--candidate", default=str(ROOT / "configs/edit_params_candidate.yaml"))
    a = ap.parse_args(argv)
    split = Path(a.split)
    assert split.name == "Debug", "calibration uses the IntPhys 2 Debug split only"
    rows = data.read_ip2_metadata(split)
    frames = np.concatenate([C.clip_square(data.load_ip2_video(split, r, stride=80)[:8], 288) for r in rows])
    res = calibrate(frames)
    Path(a.out).write_text(json.dumps(dict(
        n_videos=len(rows), n_frames=int(len(frames)), geometry="centre-crop square + INTER_AREA resize to 288x288",
        rules=dict(ssim=C.TARGETS, brightness_dL=C.DL_TARGETS, crop_scale=C.CROP_SCALE), version="v3 (single script)", res=res), indent=1))
    cfg = yaml.safe_load(open(ROOT / "configs/edit_params.yaml"))
    for name in ("brightness", "blur", "jpeg", "noise", "zoom"):
        cfg["edits"][name]["amounts"] = [0.0] + [round(res[name][l]["amount"], 4) for l in LEVELS]
    Path(a.candidate).write_text(
        "# CANDIDATE strength table from IntPhys 2 Debug calibration (scripts/calibrate_debug.py).\n"
        "# blur/JPEG/noise: mean SSIM 0.95/0.85/0.70; brightness: mean |dL*| 5/10/20; crop scale kept 0.9/0.8/0.7 (rule).\n"
        "# Registry units on 288-px (dev native) frames. configs/edit_params.yaml untouched.\n"
        "# Specificity amounts are placeholders (per-pair matched later).\n" + yaml.safe_dump(cfg, sort_keys=False))
    md = ["# CALIBRATION (IntPhys 2 Debug only; CPU; no model, no dev frames)", "",
          f"Data: {len(rows)} Debug videos x 8 evenly spaced frames = {len(frames)} frames, centre-cropped to a square and resized to 288x288 (INTER_AREA). "
          "Random edits (brightness, noise) averaged over seeds 1-3. Re-run: `python scripts/calibrate_debug.py` (deterministic). "
          "Raw: `results/analysis/calibration_debug.json`; registry-unit candidate: `configs/edit_params_candidate.yaml`.",
          "Rules: blur sigma, JPEG quality, noise std: mean SSIM to the original = 0.95 / 0.85 / 0.70 (Gaussian 11x11, sigma 1.5, per channel). "
          "Brightness: mean absolute CIELAB L* change = 5 / 10 / 20. Centre crop: scale kept = 0.9 / 0.8 / 0.7 fixed by rule. "
          "Brightness = multiplicative gain (1 +- a) with per-channel jitter +-a/2, sign and jitter seed-driven, clipped to [0,255].", "",
          "## [CAL] final values (paste into the prereg)", "", cal_table(res)]
    Path(a.notes).write_text("\n".join(md) + "\n")
    print("\n".join(md))
    return res


if __name__ == "__main__":
    main()
