import numpy as np
import pytest

from vjepa_study import schema as S


def _good():
    curves = [np.array([1., 2., 3.]), np.array([4., 5.])]
    return curves, ["a", "b"]


def test_roundtrip(tmp_path):
    c, ids = _good()
    p = tmp_path / "surprise.npz"
    S.save_surprise(p, ids, c, label=[1, 0])
    d = S.load_surprise(p)
    assert d["surprise"].shape == (2, 3) and np.isnan(d["surprise"][1, 2])
    assert [x.tolist() for x in S.curves(d)] == [[1, 2, 3], [4, 5]]


def test_nonfinite_rejected(tmp_path):
    c, ids = _good(); c[0][1] = np.inf
    S.save_surprise(tmp_path / "x.npz", ids, c)
    with pytest.raises(S.SchemaError, match="non-finite"):
        S.load_surprise(tmp_path / "x.npz")


def test_missing_key_dup_ids_and_bad_label():
    c, ids = _good()
    d = dict(video_ids=np.array(ids), surprise=np.array([[1, 2, 3], [4, 5, np.nan]], np.float32),
             lengths=np.array([3, 2]))
    S.validate_arrays(d)
    with pytest.raises(S.SchemaError, match="missing"):
        S.validate_arrays({k: v for k, v in d.items() if k != "lengths"})
    with pytest.raises(S.SchemaError, match="unique"):
        S.validate_arrays({**d, "video_ids": np.array(["a", "a"])})
    with pytest.raises(S.SchemaError, match="label"):
        S.validate_arrays({**d, "label": np.array([0, 2])})
    with pytest.raises(S.SchemaError, match="padding"):
        S.validate_arrays({**d, "surprise": np.array([[1, 2, 3], [4, 5, 0]], np.float32)})


def test_matching_ids():
    c, ids = _good()
    a = dict(video_ids=np.array(ids), surprise=np.array([[1, 2, 3], [4, 5, np.nan]], np.float32), lengths=np.array([3, 2]))
    S.check_matching_ids(a, dict(a))
    with pytest.raises(S.SchemaError, match="match"):
        S.check_matching_ids(a, {**a, "video_ids": np.array(["b", "a"])})


def test_save_run_a1_layout(tmp_path):
    from vjepa_study import schema
    S = [np.random.default_rng(0).random((4, 5)).astype(np.float32), np.random.default_rng(1).random((3, 5)).astype(np.float32)]
    feats = [np.zeros((4, 8, 6), np.float16), np.zeros((3, 8, 6), np.float16)]
    p = tmp_path / "r.npz"
    schema.save_run(p, ["a", "b"], S, feats, baselines={"B1": S}, label=np.array([0, 1]), pair_id=np.array(["p", "p"]))
    d = schema.load_surprise(p)
    assert d["surprise"].shape == (2, 4) and np.allclose(d["surprise"][0], S[0].min(axis=1))
    assert d["S"].shape == (2, 4, 5) and d["target_feats"].shape == (2, 4, 8, 6) and d["B1"].shape == (2, 4, 5)
    assert np.isnan(d["S"][1, 3]).all()
