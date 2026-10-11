import numpy as np
import pytest

from vjepa_study import calibrate as C


@pytest.fixture(scope="module")
def frames():
    rng = np.random.default_rng(0)
    base = rng.integers(40, 200, (1, 64, 64, 3)).astype(np.float32)
    import cv2
    sm = cv2.GaussianBlur(base[0], (0, 0), 3)[None]
    return np.clip(np.repeat(sm, 3, 0) + rng.normal(0, 3, (3, 64, 64, 3)), 0, 255).astype(np.uint8)


def test_ssim_basics(frames):
    assert C.ssim(frames[0], frames[0]) == pytest.approx(1.0)
    noisy = np.clip(frames[0].astype(int) + np.random.default_rng(1).normal(0, 20, frames[0].shape), 0, 255).astype(np.uint8)
    assert C.ssim(frames[0], noisy) < 0.9


def test_identity_and_monotone(frames):
    assert C.edit_ssim("blur", 0.0, frames) == pytest.approx(1.0)
    vals = [C.edit_ssim("noise", a, frames) for a in (2, 8, 20)]
    assert vals[0] > vals[1] > vals[2]


@pytest.mark.parametrize("name,hi", [("blur", 8.0), ("noise", 80.0), ("zoom", 0.5)])
def test_solve_hits_target(frames, name, hi):
    a, s = C.solve(name, 0.85, frames, 0.0, hi)
    assert abs(s - 0.85) < 0.01 and 0 < a < hi


def test_jpeg_integer_and_clip_fraction(frames):
    q, s = C.solve("jpeg", 0.9, frames, 0, 90, integer=True)
    assert float(q).is_integer() and 0 < q < 90
    assert C.clipped_fraction(frames, 0.0) == 0.0
    assert C.clipped_fraction(frames, 1.5) > 0.0


def test_clip_square():
    f = np.zeros((2, 40, 60, 3), np.uint8)
    assert C.clip_square(f, 32).shape == (2, 32, 32, 3)


def test_brightness_dL_solver(frames):
    a, d = C.solve_brightness_dL(10.0, frames, n_iter=14)
    assert abs(d - 10.0) < 0.2 and a > 0
    assert C.mean_abs_dL(frames, frames) == 0.0


def test_calibrate_debug_script_rules_on_synthetic_frames(frames):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    import calibrate_debug as CD
    res = CD.calibrate(frames)
    for lvl, tgt in C.DL_TARGETS.items():
        assert res["brightness"][lvl]["mean_abs_dL"] == pytest.approx(tgt, rel=0.02)
    for lvl, sc in C.CROP_SCALE.items():
        assert res["zoom"][lvl]["crop_scale"] == sc and res["zoom"][lvl]["amount"] == pytest.approx(1 - sc)
    for name in ("blur", "noise"):
        for lvl in ("low", "mid"):      # synthetic smooth 64-px frames cannot reach SSIM 0.70 by blur
            assert res[name][lvl]["ssim"] == pytest.approx(C.TARGETS[lvl], abs=0.01)
    assert all(abs(res["jpeg"][l]["ssim"] - t) < 0.1 for l, t in C.TARGETS.items())
    table = CD.cal_table(res)
    assert table.count("\n") == 6 and "brightness gain" in table and "| 0.9 | 0.8 | 0.7 |" in table
