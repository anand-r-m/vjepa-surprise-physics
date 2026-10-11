import numpy as np
import pytest

from vjepa_study import amend as A

RES = 48


@pytest.fixture(scope="module")
def pair():
    rng = np.random.default_rng(7)
    base = cv2_blur(rng.integers(30, 220, (1, 64, 64, 3)).astype(np.uint8))
    p = np.repeat(base, 30, axis=0).copy()
    p = np.clip(p.astype(int) + rng.integers(-2, 3, p.shape), 0, 255).astype(np.uint8)
    v = p.copy()
    v[10:22, 20:36, 24:40] = 250            # object appears at t=10, vanishes after t=22
    return p, v


def cv2_blur(x):
    import cv2
    return np.stack([cv2.GaussianBlur(f, (0, 0), 2) for f in x])


def test_flags():
    assert A.is_deterministic("blur") and A.is_deterministic("hflip")
    assert not A.is_deterministic("dither") and not A.is_deterministic("lighting_local")
    assert not A.is_deterministic("brightness") and A.is_deterministic("zoom_base")
    assert not A.is_deterministic("jolt_base")
    with pytest.raises(KeyError):
        A.is_deterministic("nope")


def test_event_window_and_tau(pair):
    p, v = pair
    D = A.divergence(p, v, RES)
    assert D[:10].max() == 0
    tau = A.tau_rule([D, D])
    assert tau == pytest.approx(2 / 255)
    w = A.event_window(D, tau)
    assert (w["t_on"], w["t_off"], w["fallback"]) == (10, 22, False)
    # divergence that persists to the end -> t_off = T
    v2 = p.copy(); v2[10:, 20:36, 24:40] = 250
    assert A.event_window(A.divergence(p, v2, RES), tau)["t_off"] == 30
    # no divergence -> seeded fallback in middle 50%
    f1 = A.event_window(A.divergence(p, p, RES), tau, seed=3)
    f2 = A.event_window(A.divergence(p, p, RES), tau, seed=3)
    assert f1["fallback"] and f1 == f2 and 7 <= f1["t_on"] < 23


def test_support_and_disk(pair):
    p, v = pair
    s = A.violation_support(p, v, 10, 22, RES)
    assert abs(s["center"][0] - 28 / 64) < 0.06 and abs(s["center"][1] - 32 / 64) < 0.06
    assert 0.05 < s["area_frac"] < 0.15
    d = A.soft_disk(64, 64, s["center"], s["area_frac"])
    assert d.max() == pytest.approx(1.0) and d.min() == 0.0
    assert abs(d.sum() / (64 * 64) - s["area_frac"]) < 0.01
    # minimum area at model resolution
    tiny = A.violation_support(p, p, 10, 22, RES)
    assert tiny["area_frac"] == pytest.approx(64 / RES**2)


def test_lighting_event_regions(pair):
    p, _ = pair
    prm = dict(amount=0.2, t_on=10, t_off=22, region=None)
    g = A.lighting_event(p, prm, 1)
    assert np.array_equal(g[:10], p[:10]) and np.array_equal(g[22:], p[22:])
    assert not np.array_equal(g[10:22], p[10:22])
    assert np.array_equal(A.lighting_event(p, dict(prm, amount=0.0), 1), p)
    reg = dict(center=(0.5, 0.5), area_frac=0.05, edge=0.2)
    l = A.lighting_event(p, dict(prm, region=reg), 1)
    changed = (l != p).any(axis=(0, 3))
    assert changed.any() and not changed[:5].any() and not changed[-5:].any()
    # sign is seed-driven only
    assert A.gain_sign(1) == A.gain_sign(1)
    assert {A.gain_sign(s) for s in range(30)} == {-1.0, 1.0}


def test_dither(pair):
    p, _ = pair
    d = A.dither(p, dict(amount=1.0), 5)
    diff = d.astype(int) - p.astype(int)
    assert np.abs(diff).max() == 1 and (diff != 0).mean() > 0.5
    assert np.array_equal(d, A.dither(p, dict(amount=1.0), 5))
    assert not np.array_equal(d, A.dither(p, dict(amount=1.0), 6))
    assert np.array_equal(A.dither(p, dict(amount=0.0), 5), p)


def test_base_window_reference(pair):
    p, _ = pair
    ref = A.base_ref(p)
    assert ref.shape == p.shape and ref.dtype == np.uint8
    j0 = A.jolt_base(p, dict(amount=0.0, t_on=10, t_off=None), 1)[0]
    z0 = A.zoom_base(p, dict(amount=0.0, t_on=10, t_off=None), 1)[0]
    assert np.array_equal(j0, ref) and np.array_equal(z0, ref)      # zero-strength == reference
    j, clipped = A.jolt_base(p, dict(amount=3.0, t_on=10, t_off=22), 1)
    assert np.array_equal(j[:10], ref[:10]) and np.array_equal(j[22:], ref[22:])
    assert not np.array_equal(j[10:22], ref[10:22]) and not clipped
    _, clipped = A.jolt_base(p, dict(amount=50.0, t_on=10, t_off=22), 1)
    assert clipped
    z = A.zoom_base(p, dict(amount=0.2, t_on=10, t_off=None), 1)[0]
    assert np.array_equal(z[:10], ref[:10]) and not np.array_equal(z[10:], ref[10:])


@pytest.mark.parametrize("kind", ["lighting_global", "lighting_local", "jolt_base", "zoom_base"])
def test_matching_hits_target(pair, kind):
    p, v = pair
    # event window with enough magnitude: use a large, persistent violation
    d = 6 if kind in ("jolt_base", "zoom_base") else 25
    v = p.copy(); v[10:22, 8:56, 8:56] = np.clip(v[10:22, 8:56, 8:56].astype(int) + d, 0, 255)
    m = A.match_pair(kind, p, v, 10, 22, seed=2, res=RES)
    assert m["feasible"]
    assert abs(m["levels"]["mid"]["ratio"] - 1) < 0.05, m["levels"]
    assert m["levels"]["low"]["amount"] == pytest.approx(0.5 * m["s_star"])
    assert m["levels"]["high"]["amount"] == pytest.approx(2 * m["s_star"], rel=1e-9) or m["levels"]["high"]["amount"] <= 3.0
    ed, ref = A.apply_matched(kind, p, m, "mid", 2, 10, 22)
    assert A.event_magnitude(ed, ref, 10, 22, RES) == pytest.approx(m["m_i"], rel=0.06)


def test_matching_is_outcome_blind_deterministic(pair):
    p, v = pair
    a = A.match_pair("lighting_local", p, v, 10, 22, seed=1, res=RES)
    b = A.match_pair("lighting_local", p, v, 10, 22, seed=1, res=RES)
    assert a["s_star"] == b["s_star"]


def test_infeasible_reports_clipped(pair):
    p, _ = pair
    v = p.copy(); v[10:22] = 255 - v[10:22]          # huge violation, jolt cannot match
    m = A.match_pair("jolt_base", p, v, 10, 22, seed=1, res=RES)
    assert not m["feasible"]
    assert m["levels"]["mid"]["ratio"] < 0.95


def test_sampling_plan():
    s = A.sampling_plan(100, 2)["plan"]
    assert len(s["idx"]) == 49 and s["n_windows"] == 17
    h = A.sampling_plan(100, 2, halve=True)
    assert h["plan"]["frame_step"] == 4 and len(h["plan"]["idx"]) == 24 and not h["reduced"]
    assert (np.diff(h["plan"]["idx"]) == 4).all()
    r = A.sampling_plan(100, 4, halve=True)           # step 8 -> 12 frames < 16: W'=12
    assert r["reduced"] and r["plan"]["window"] == 12 and r["reference"]["window"] == 12
    assert r["reference"]["frame_step"] == 4
    with pytest.raises(ValueError):
        A.sampling_plan(100, 5, halve=True)             # step 10 -> 9 frames: infeasible
    with pytest.raises(NotImplementedError):
        from vjepa_study import edits
        edits.fps_halve(np.zeros((4, 8, 8, 3), np.uint8), {"amount": 1.0}, 0)


def test_support_retention():
    m = np.zeros((20, 20), bool)
    m[9:11, 9:11] = True
    assert A.support_retention(m, 0.7) == 1.0
    m2 = np.zeros((20, 20), bool); m2[0:2, 0:2] = True
    assert A.support_retention(m2, 0.7) == 0.0
    m3 = np.zeros((20, 20), bool); m3[:, :] = True
    assert A.support_retention(m3, 0.5) == pytest.approx(0.25)
    assert A.support_retention(np.zeros((4, 4), bool), 0.5) == 1.0


def test_make_matched_strengths_synthetic(tmp_path):
    import json, sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import make_matched_strengths as mm
    from test_data import _make_quad
    root = tmp_path / "dev"
    rng = np.random.default_rng(3)
    import cv2
    for s in ("01", "02"):
        _make_quad(root, "O1", s, T=30)
    out = tmp_path / "m.json"
    meta = mm.run(root, out, res=32, frame_step=1, seeds=(1, 2), workers=1, blocks=("O1",))
    d = json.loads(out.read_text())
    assert meta["n_pairs"] == 4 and meta["n_fallback"] == 0 and meta["tau"] >= 2 / 255
    p0 = next(iter(d["pairs"].values()))
    assert p0["event"]["t_on"] == 12 and set(p0["lighting_global"]) == {"1", "2"} and "levels" in p0["zoom_base"]
    assert p0["lighting_global"]["1"]["levels"]["mid"]["ratio"] == pytest.approx(1.0, abs=0.1)
    # consumed by run_lib.apply_run_edit
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "kaggle" / "common"))
    import run_lib
    from vjepa_study import data
    f4, lab, ids = data.load_dev_quadruplet(root, "O1", "01")
    ip, ii = data.make_pairs(f4, lab, 1)[0]
    item = dict(frames=f4[ip], pair_id="O1/01/p0")
    fr, mult = run_lib.apply_run_edit(item, dict(name="lighting_global", level="mid"), 1, d)
    assert fr.shape == f4[ip].shape and not np.array_equal(fr, f4[ip]) and mult == 1


def test_event_window_spec_last_quiet_run_and_flags():
    tau = 2 / 255
    D = np.zeros(40)
    D[10:20] = 0.1                      # event, then a 4-frame quiet gap (< 5), event again, then quiet to the end
    D[24:30] = 0.1
    w = A.event_window(D, tau)
    assert (w["t_on"], w["t_off"], w["transient"]) == (10, 30, True)
    D2 = np.zeros(40); D2[10:20] = 0.1; D2[26:30] = 0.1      # 6-frame quiet gap then more event: LAST run (30..)
    assert A.event_window(D2, tau)["t_off"] == 30
    D3 = np.zeros(100); D3[96:] = 0.1
    w3 = A.event_window(D3, tau)
    assert w3["t_on"] == 96 and w3["excluded_late"] and not w3["transient"] and w3["t_off"] == 100
