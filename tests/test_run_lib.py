import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "kaggle" / "common"))
import run_lib  # noqa: E402

from test_data import _make_quad  # noqa: E402
from vjepa_study import schema  # noqa: E402


class FakeModel:
    info = {"fake": True}

    def __init__(self):
        self.calls = []

    def surprise(self, frames, frame_step=2, ctx=(2, 4, 6, 8, 10), **kw):
        self.calls.append(frame_step)
        from vjepa_study import amend
        pl = amend.sampling_plan(len(frames), frame_step, 16, 2)["plan"]
        idx, nW = pl["idx"], pl["n_windows"]
        v = float(frames.astype(np.float32).mean()) / 255 + 0.1
        S = np.full((nW, len(ctx)), v, np.float32) + np.linspace(0, 0.01, nW)[:, None]
        f = np.random.default_rng(int(frames.sum()) % 1000).random((nW, 8, 4)).astype(np.float16)
        return dict(S=S, target_feats=f, idx=idx)


@pytest.fixture
def dev(tmp_path):
    root = tmp_path / "dev"
    _make_quad(root, "O1", "01", T=50)
    _make_quad(root, "O2", "01", T=50)
    return root


def _runs(tmp_path, runs):
    p = tmp_path / "runs.json"
    p.write_text(json.dumps(dict(runs=runs)))
    return p


def test_run_and_resume(tmp_path, dev):
    runs = [dict(run_id="T_M1_ipdev_clean_s1", model="M1", dataset="ipdev", frame_step=1,
                 subset=dict(scenes=["O1/01", "O2/01"]), edit=None, seed=1)]
    fm = FakeModel()
    out = tmp_path / "out"
    # run_lib.main expects the dataset under input_root/<dev_dataset>; here the tree is directly given
    for r in runs:
        res = run_lib.run_one(r, fm, out, dev_root=dev, log=lambda *a: None)
    assert res == "done"
    d = schema.load_surprise(out / runs[0]["run_id"] / "surprise.npz")
    assert len(d["video_ids"]) == 8 and set(d["label"].tolist()) == {0, 1}
    assert d["S"].shape == (8, 17, 5) and d["B1"].shape == (8, 17, 5) and d["B3"].shape == (8, 17, 5)
    assert len(set(d["pair_id"].tolist())) == 4 and len(set(d["scene_id"].tolist())) == 2
    meta = json.loads((out / runs[0]["run_id"] / "meta.json").read_text())
    assert meta["status"] == "done" and meta["n_videos"] == 8 and "sec_per_video" in meta
    n_calls = len(fm.calls)
    assert run_lib.run_one(runs[0], fm, out, dev_root=dev, log=lambda *a: None) == "skipped"
    assert len(fm.calls) == n_calls


def test_edits_same_params_for_both_members_and_alias(tmp_path, dev):
    out = tmp_path / "out"
    fm = FakeModel()
    base = dict(model="M1", dataset="ipdev", frame_step=1, subset=dict(scenes=["O1/01"]))
    r1 = dict(base, run_id="T_M1_ipdev_blur-high_s1", edit=dict(name="blur", strength="high"), seed=1)
    r2 = dict(base, run_id="T_M1_ipdev_blur-high_s2", edit=dict(name="blur", strength="high"), seed=2)
    assert run_lib.run_one(r1, fm, out, dev_root=dev, log=lambda *a: None) == "done"
    assert run_lib.run_one(r2, fm, out, dev_root=dev, log=lambda *a: None) == "alias"
    assert not (out / r2["run_id"] / "surprise.npz").exists()
    # random edit (dither) is NOT aliased
    r3 = dict(base, run_id="T_M1_ipdev_dither_s2", edit=dict(name="dither"), seed=2)
    assert run_lib.run_one(r3, fm, out, dev_root=dev, log=lambda *a: None) == "done"
    # halving doubles the native stride and never duplicates frames
    r4 = dict(base, run_id="T_M1_ipdev_halve_s1", edit=dict(name="halve"), seed=1)
    fm.calls.clear()
    run_lib.run_one(r4, fm, out, dev_root=dev, log=lambda *a: None)
    assert set(fm.calls) == {2}
    # pixel hashes: dither differs from clean, blur identical across seeds
    h1 = schema.load_surprise(out / r1["run_id"] / "surprise.npz")["video_hash"]
    h3 = schema.load_surprise(out / r3["run_id"] / "surprise.npz")["video_hash"]
    assert (h1 != h3).all()


def test_nan_surprise_fails_cleanly(tmp_path, dev):
    class Bad(FakeModel):
        def surprise(self, frames, **kw):
            r = super().surprise(frames, **kw)
            r["S"][0, 0] = np.nan
            return r
    inp = tmp_path / "in" / "intphys-dev"
    inp.mkdir(parents=True)
    (inp / "dev").symlink_to(dev)
    rj = _runs(tmp_path, [dict(run_id="T_bad", model="M1", dataset="ipdev", frame_step=1, subset=dict(scenes=["O1/01"]))])
    st = run_lib.main(rj, tmp_path / "o", input_root=tmp_path / "in", work=tmp_path / "w",
                      build_model=lambda n, r: Bad(), log=lambda *a: None)
    assert st["T_bad"] == "FAILED" and (tmp_path / "o" / "T_bad" / "error.txt").exists()


def test_ensure_dev_tar(tmp_path):
    import subprocess
    src = tmp_path / "src"
    _make_quad(src / "dev", "O1", "01", T=6)
    (src / "dev" / "O1" / "01" / "1" / "depth").mkdir()
    (src / "dev" / "O1" / "01" / "1" / "depth" / "depth_001.png").write_bytes(b"x")
    inp = tmp_path / "in"
    inp.mkdir()
    subprocess.run(["tar", "czf", str(inp / "dev.tar.gz"), "-C", str(src), "dev"], check=True)
    d = run_lib.ensure_dev(inp, tmp_path / "work", scenes=["O1/01"])
    assert (d / "O1" / "01" / "1" / "scene" / "scene_001.png").exists()
    assert not (d / "O1" / "01" / "1" / "depth").exists()


def test_sharding_identical_to_single(tmp_path, dev):
    base = dict(model="M1", dataset="ipdev", frame_step=1, subset=dict(scenes=["O1/01", "O2/01"]), edit=None, seed=1)
    o1, o2 = tmp_path / "a", tmp_path / "b"
    run_lib.run_one(dict(base, run_id="r"), FakeModel(), o1, dev_root=dev, log=lambda *a: None)
    run_lib.run_one(dict(base, run_id="r"), [FakeModel(), FakeModel()], o2, dev_root=dev, log=lambda *a: None)
    a = schema.load_surprise(o1 / "r" / "surprise.npz"); b = schema.load_surprise(o2 / "r" / "surprise.npz")
    assert list(a["video_ids"]) == list(b["video_ids"])
    for k in ("S", "B1", "B2", "B3", "target_feats"):
        assert np.allclose(a[k], b[k], equal_nan=True, atol=0)
    assert json.loads((o2 / "r" / "meta.json").read_text())["n_gpus"] == 2


def test_verify_dev_npz_fails_fast(tmp_path):
    with pytest.raises(FileNotFoundError, match="incomplete"):
        run_lib.verify_dev_npz(tmp_path)


def test_fixed_gpu_assignment(tmp_path, dev):
    class Tag(FakeModel):
        def __init__(self, name):
            super().__init__(); self.device = name; self.seen = []

        def surprise(self, frames, **kw):
            self.seen.append(float(frames.sum()))
            return super().surprise(frames, **kw)
    base = dict(model="M1", dataset="ipdev", frame_step=1, subset=dict(scenes=["O1/01", "O2/01"]), edit=None, seed=1)
    seen = []
    for rep in range(2):
        a, b = Tag("cuda:0"), Tag("cuda:1")
        run_lib.run_one(dict(base, run_id=f"r{rep}"), [a, b], tmp_path / "o", dev_root=dev, log=lambda *x: None)
        seen.append((a.seen, b.seen))
    assert seen[0] == seen[1] and len(seen[0][0]) == 4 and len(seen[0][1]) == 4
