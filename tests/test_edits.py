import numpy as np
import pytest

from vjepa_study import edits as E

ALL = [n for n in E.EDIT_FUNCS if n != "fps_halve"]  # fps_halve: see test_amend
SPEC_EDITS = {"brightness", "blur", "jpeg", "noise", "zoom", "hflip", "fps_halve",
              "lighting_step", "camera_jolt", "sudden_zoom", "vflip", "time_reversal"}


def test_registry_covers_spec():
    reg = E.load_registry()
    assert set(reg) == SPEC_EDITS
    assert {reg[n]["kind"] for n in reg} == {"invariance", "specificity", "positive"}
    assert E.edit_names("positive") == ["vflip", "time_reversal"]
    for e in reg.values():
        assert len(e["amounts"]) == len(e["levels"]) == 4 and e["amounts"][0] == 0


@pytest.mark.parametrize("name", ALL)
def test_identity_at_strength_zero_exact(clip, name):
    out = E.apply_edit(clip, name, 0, seed=3, t_star=5)
    assert out.dtype == np.uint8 and out.shape == clip.shape
    assert np.array_equal(out, clip) and out is not clip


@pytest.mark.parametrize("name", ALL)
@pytest.mark.parametrize("level", ["low", "mid", "high"])
def test_shape_dtype_and_input_untouched(clip, name, level):
    orig = clip.copy()
    out = E.apply_edit(clip, name, level, seed=1)
    assert out.shape == clip.shape and out.dtype == np.uint8
    assert np.array_equal(clip, orig)


@pytest.mark.parametrize("name", ALL)
def test_high_strength_changes_clip(clip, name):
    assert not np.array_equal(E.apply_edit(clip, name, "high", seed=1, t_star=4), clip)


@pytest.mark.parametrize("name", ALL)
def test_determinism_same_seed(clip, name):
    a = E.apply_edit(clip, name, "mid", seed=11)
    b = E.apply_edit(clip, name, "mid", seed=11)
    assert np.array_equal(a, b)


@pytest.mark.parametrize("name", sorted(E.RANDOM_EDITS))
def test_different_seed_differs_where_random(clip, name):
    a = E.apply_edit(clip, name, "high", seed=1)
    outs = [E.apply_edit(clip, name, "high", seed=s) for s in range(2, 8)]
    assert any(not np.array_equal(a, o) for o in outs)


@pytest.mark.parametrize("name", ["blur", "jpeg", "zoom", "hflip", "vflip", "time_reversal"])
def test_deterministic_edits_ignore_seed(clip, name):
    assert np.array_equal(E.apply_edit(clip, name, "high", 1), E.apply_edit(clip, name, "high", 2))


def test_specificity_edits_leave_frames_before_t_star(clip):
    for name in ["lighting_step", "camera_jolt", "sudden_zoom"]:
        out = E.apply_edit(clip, name, "high", seed=0, t_star=8)
        assert np.array_equal(out[:8], clip[:8])
        assert not np.array_equal(out[8:], clip[8:])


def test_t_star_seeded_middle_half():
    for T in (16, 40, 100):
        ts = {E.resolve_t_star(T, {"t_star": None}, s) for s in range(200)}
        assert min(ts) >= T // 4 and max(ts) < 3 * T // 4 + 1
        assert len(ts) > 1
    assert E.resolve_t_star(30, {"t_star": 12}, 5) == 12
    assert E.resolve_t_star(30, {"t_star": None}, 5) == E.resolve_t_star(30, {"t_star": None}, 5)


def test_simple_semantics(clip):
    assert np.array_equal(E.apply_edit(clip, "hflip", 1, 0), clip[:, :, ::-1])
    assert np.array_equal(E.apply_edit(clip, "vflip", 1, 0), clip[:, ::-1])
    assert np.array_equal(E.apply_edit(clip, "time_reversal", 1, 0), clip[::-1])
    with pytest.raises(NotImplementedError):
        E.apply_edit(clip, "fps_halve", 1, 0)
    assert np.array_equal(E.apply_edit(clip, "fps_halve", 0, 0), clip)


def test_time_reversal_and_flips_involutive(clip):
    for n in ["hflip", "vflip", "time_reversal"]:
        once = E.apply_edit(clip, n, 1, 0)
        assert np.array_equal(E.apply_edit(once, n, 1, 0), clip)


def test_blur_smooths_noise_adds_variance(clip):
    assert E.apply_edit(clip, "blur", "high", 0).astype(float).std() < clip.astype(float).std()
    flat = np.full((4, 16, 16, 3), 128, np.uint8)
    n = E.apply_edit(flat, "noise", "high", 0)
    assert n.astype(float).std() > 1


def test_dose_response_monotone_pixel_change(clip):
    for name in ["brightness", "blur", "noise", "zoom", "jpeg", "lighting_step", "sudden_zoom", "camera_jolt"]:
        d = [E.edit_delta(clip, name, s, seed=1, t_star=4) for s in (0, 1, 2, 3)]
        assert d[0] == 0 and d[1] > 0 and d[1] <= d[2] <= d[3], (name, d)


def test_params_for_interp_and_extrapolation():
    reg = E.load_registry()
    a = reg["blur"]["amounts"]
    assert E.params_for("blur", "low")["amount"] == a[1]
    assert E.params_for("blur", 1.5)["amount"] == pytest.approx((a[1] + a[2]) / 2)
    assert E.params_for("blur", 4)["amount"] > a[3]
    assert E.params_for("blur", 0)["amount"] == 0


def test_check_rejects_bad_input():
    with pytest.raises(ValueError):
        E.apply_edit(np.zeros((2, 4, 4, 3), np.float32), "blur", 1, 0)


# ------------------------------------------------------ pairs (SPEC section 8)
@pytest.mark.parametrize("name", ALL)
def test_pair_edit_identical_params_and_seed(clip, name):
    rng = np.random.default_rng(5)
    b = np.clip(clip.astype(int) + rng.integers(-20, 20, clip.shape), 30, 225).astype(np.uint8)
    p = E.params_for(name, "high")
    ea, eb, used = E.pair_edit(clip, b, name, p, seed=9)
    # identical members -> identical outputs (same params and seed on both)
    sa, sb, _ = E.pair_edit(clip, clip, name, p, seed=9)
    assert np.array_equal(sa, sb)
    # each member equals the single-clip edit with the shared resolved params and seed
    assert np.array_equal(ea, E.EDIT_FUNCS[name](clip, used, 9))
    assert np.array_equal(eb, E.EDIT_FUNCS[name](b, used, 9))
    assert used["t_star"] is not None and used["amount"] == p["amount"]


def test_pair_edit_noise_is_same_noise(clip):
    b = np.clip(clip.astype(int) // 2 + 60, 60, 190).astype(np.uint8)
    a0 = np.full_like(clip, 128); b0 = np.full_like(clip, 100)
    p = E.params_for("noise", "mid")
    ea, eb, _ = E.pair_edit(a0, b0, "noise", p, seed=4)
    assert np.array_equal(ea.astype(int) - 128, eb.astype(int) - 100)


def test_pair_edit_shares_t_star(clip):
    p = E.params_for("lighting_step", "high")
    ea, eb, used = E.pair_edit(clip, clip[::-1].copy(), "lighting_step", p, seed=2)
    t = used["t_star"]
    assert np.array_equal(ea[:t], clip[:t]) and np.array_equal(eb[:t], clip[::-1][:t])


def test_pair_shape_mismatch(clip):
    with pytest.raises(ValueError):
        E.pair_edit(clip, clip[:-1], "blur", E.params_for("blur", 1), 0)


# --------------------------------------------------------- magnitude
def test_pixel_delta(clip):
    other = clip.copy(); other[8:] = np.clip(other[8:].astype(int) + 10, 0, 255)
    d_all = E.pixel_delta(other, clip, 0)
    d_after = E.pixel_delta(other, clip, 8)
    assert d_after > d_all
    assert d_after == pytest.approx(np.abs(other[8:].astype(float) - clip[8:]).mean(), rel=1e-5)
    assert E.pixel_delta(clip, clip, 3) == 0


@pytest.mark.parametrize("name", ["lighting_step", "sudden_zoom", "camera_jolt"])
def test_match_strength_converges(clip, name):
    import cv2
    # smooth content so the pixel change does not saturate at 1 px (white-noise textures do)
    clip = np.stack([cv2.GaussianBlur(f, (0, 0), 4) for f in clip])
    clips = [clip, np.roll(clip, 3, axis=2), np.roll(clip, 5, axis=1)]
    ts = [6, 7, 8]
    ref = np.median([E.edit_delta(c, name, 2.0, s, t) for c, s, t in zip(clips, [1, 2, 3], ts)])
    r = E.match_strength(clips, name, target_median=ref * 1.7, seeds=[1, 2, 3], t_stars=ts)
    assert r["converged"] and r["rel_err"] <= 0.1
    assert r["median"] == pytest.approx(ref * 1.7, rel=0.1)
    # reported median really is the median of the achieved deltas
    assert np.median(r["deltas"]) == pytest.approx(r["median"])


def test_match_strength_reports_unreachable(clip):
    # a hflip-like saturating edit cannot reach an absurd target: converged must be False
    r = E.match_strength([clip], "lighting_step", target_median=1e6, t_stars=[4], max_iter=5)
    assert not r["converged"]
