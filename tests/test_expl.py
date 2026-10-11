"""EXPLORATORY post-freeze groups: halve_hold edit, onset threshold rule, group definitions, same-code-path of the bundle."""
import base64
import io
import json
import re
import sys
import tarfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "kaggle" / "common"), str(ROOT / "kaggle" / "expl"), str(ROOT / "scripts")]
import expl_lib  # noqa: E402
import make_expl_runs as X  # noqa: E402
import make_onset_matches as O  # noqa: E402
import run_lib  # noqa: E402
from vjepa_study import data  # noqa: E402


def _video(T=100):
    rng = np.random.default_rng(0)
    return rng.integers(0, 256, (T, 8, 8, 3), dtype=np.uint8)


def test_hold_halve_values_and_sampling():
    f = _video()
    g = expl_lib.hold_halve(f)
    assert g.shape == f.shape and g.dtype == np.uint8
    for t in range(100):
        assert (g[t] == f[t - t % 4]).all()
    idx = data.sample_indices(100, 2)                     # clean skip-2 sampling: 49 frames
    s = g[idx]
    assert len(s) == 49
    # sampled frames 2m and 2m+1 are identical (tubelet-aligned hold); consecutive tubelets differ
    for m in range(24):
        assert (s[2 * m] == s[2 * m + 1]).all() and (s[2 * m] == f[4 * m]).all()
        assert not (s[2 * m] == s[2 * m + 2]).all()
    assert (g[0] == f[0]).all()
    # differs from the skip-4 clean reference (the pre-registered fps_halve design error)
    assert not np.array_equal(s, f[data.sample_indices(100, 4)][: len(s)]) 


def test_install_delegates_and_is_idempotent():
    f = _video(20)
    item = dict(frames=f, pair_id="x")
    expl_lib.install(run_lib)
    expl_lib.install(run_lib)
    out, mult = run_lib.apply_run_edit(item, dict(name="halve_hold", strength="high"), 1)
    assert mult == 1 and np.array_equal(out, expl_lib.hold_halve(f))
    out, mult = run_lib.apply_run_edit(item, None, 1)
    assert out is f and mult == 1
    out, mult = run_lib.apply_run_edit(item, dict(name="halve"), 1)       # frozen skip-4 edit untouched
    assert out is f and mult == 2
    out, _ = run_lib.apply_run_edit(item, dict(name="dither"), 3)
    assert out.shape == f.shape


def test_threshold_rule_pixel_only():
    # prefix identical (D=0 exactly), onset at 40 with D growing: theta = 0 (smallest grid value above the zero noise floor)
    D = [np.r_[np.zeros(40), np.full(60, 0.004)] for _ in range(10)]
    th, floor, table = O.choose_threshold(D)
    assert floor == 0.0 and th == 0.0
    # 9 of 10 pairs never exceed 0.5 gray, so the rule still picks the smallest feasible grid value
    D2 = [np.r_[np.zeros(40), np.full(60, 0.004)] for _ in range(9)] + [np.r_[np.zeros(40), np.full(60, 0.01)]]
    assert O.choose_threshold(D2)[0] == 0.0
    # a noisy prefix (floor 0.4 gray) forces theta >= floor
    Dn = [np.r_[np.full(10, 0.4 / 255), np.full(90, 5.0 / 255)] for _ in range(10)]
    th, floor, _ = O.choose_threshold(Dn)
    assert floor > 0 and th >= floor and np.isclose(th * 255, 0.5)
    # too few pairs defined at larger thresholds does not matter; but if nothing reaches 90% theta is None
    assert O.choose_threshold([np.zeros(100)] * 5)[0] is None


def test_group_definitions_and_hours():
    g = X.groups()
    assert set(g) == {"expl_onset_spec", "expl_halve_hold"}
    on = g["expl_onset_spec"]
    ids = [r["run_id"] for r in on]
    assert len(on) == 10 and len(set(ids)) == 10 and all(i.startswith("EXPL_M1_ipdev_onset-") for i in ids)
    assert all(r["members"] == "possible" and r["edit"]["level"] == "mid" and r["model"] == "M1" and r["n_gpus"] == 2
               and r["precision"] == "fp16" and r["frame_step"] == 2 for r in on)
    seeds = {k: sorted(r["seed"] for r in on if r["edit"]["name"] == k) for k in ("lighting_global", "lighting_local", "jolt_base", "zoom_base")}
    assert seeds == {"lighting_global": [1, 2, 3], "lighting_local": [1, 2, 3], "jolt_base": [1, 2, 3], "zoom_base": [1]}
    h = g["expl_halve_hold"]
    assert len(h) == 1 and h[0]["edit"] == dict(name="halve_hold", strength="high") and h[0]["members"] == "all" and h[0]["seed"] == 1
    s = X.summarize(g)
    assert s["expl_onset_spec"]["hours"] == 1.6 and s["expl_halve_hold"]["hours"] == 0.31
    # no id collides with a frozen group
    frozen = {r["run_id"] for f in (ROOT / "kaggle").glob("*/runs.json") if f.parent.name not in g for r in json.load(open(f))["runs"]}
    assert not frozen & ({r["run_id"] for r in on} | {r["run_id"] for r in h})


def _decode(run_py):
    b = re.search(r"^_B = '([A-Za-z0-9+/=]+)'", Path(run_py).read_text(), re.M).group(1)
    with tarfile.open(fileobj=io.BytesIO(base64.b64decode(b)), mode="r:gz") as tf:
        return {m.name: tf.extractfile(m).read() for m in tf.getmembers() if m.isfile()}


def test_same_code_path_vs_frozen_bundles():
    onset, hold = ROOT / "kaggle/expl_onset_spec/run.py", ROOT / "kaggle/expl_halve_hold/run.py"
    if not (onset.exists() and hold.exists()):
        import pytest
        pytest.skip("expl bundles not built yet")
    ref = _decode(ROOT / "kaggle/h1_inv_a/run.py")
    allowed = {"BUNDLE_INFO.json", "runs.json", "matches.json", "src/vjepa_study/models/m2_vjepa2.py"}
    for p in (onset, hold):
        b = _decode(p)
        diff = {n for n in set(ref) | set(b) if ref.get(n) != b.get(n)}
        new = {n for n in diff if n.startswith("kaggle/expl/")}
        assert diff - allowed - new == set(), diff
        assert new == {"kaggle/expl/expl_lib.py", "kaggle/expl/preamble.py"}
        assert ref["kaggle/common/run_lib.py"] == b["kaggle/common/run_lib.py"] == (ROOT / "kaggle/common/run_lib.py").read_bytes()
        assert p.read_text().endswith((ROOT / "kaggle/common/kernel_main.py").read_text())
    assert _decode(onset)["matches.json"] != _decode(ROOT / "kaggle/h2_spec_a/run.py")["matches.json"]
