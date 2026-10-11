import json
import cv2
import numpy as np
import pytest

from vjepa_study import data


def _write_video(d, frames, possible):
    (d / "scene").mkdir(parents=True)
    for i, f in enumerate(frames):
        cv2.imwrite(str(d / "scene" / f"scene_{i+1:03d}.png"), f[..., ::-1])
    (d / "status.json").write_text(json.dumps({"header": {"is_possible": possible}}))


def _make_quad(root, block="O1", scene="01", T=20, order=(0, 1, 2, 3)):
    """Videos: A->A' (poss), A->B (imp, diverges at 12), B'->B (poss... ) built from
    2 beginnings x 2 endings. begin0=poss/imp split at t=12."""
    rng = np.random.default_rng(0)
    b0 = rng.integers(0, 255, (T, 16, 16, 3), dtype=np.uint8)
    b1 = rng.integers(0, 255, (T, 16, 16, 3), dtype=np.uint8)
    vids = []
    # (begin, ending) ; ending changes frames >= 12; beginnings differ from frame 0
    for beg, end, poss in [(b0, 0, True), (b0, 1, False), (b1, 0, False), (b1, 1, True)]:
        v = beg.copy()
        if end:
            v[12:] = np.clip(v[12:].astype(int) + 40, 0, 255).astype(np.uint8)
        vids.append((v, poss))
    for k, j in enumerate(order):
        _write_video(root / block / scene / str(k + 1), *vids[j])
    return vids


def test_png_roundtrip_and_quad(tmp_path):
    vids = _make_quad(tmp_path)
    f4, lab, ids = data.load_dev_quadruplet(tmp_path, "O1", "01")
    assert f4.shape == (4, 20, 16, 16, 3) and f4.dtype == np.uint8
    assert np.array_equal(f4[1], vids[1][0]) and lab.tolist() == [True, False, False, True]
    assert ids[0] == "O1/01/1"


@pytest.mark.parametrize("order", [(0, 1, 2, 3), (1, 0, 3, 2), (0, 2, 1, 3), (0, 3, 1, 2), (2, 0, 1, 3)])
def test_pairs_prefix_sharing_one_each(tmp_path, order):
    _make_quad(tmp_path, order=order)
    f4, lab, _ = data.load_dev_quadruplet(tmp_path, "O1", "01")
    pairs = data.make_pairs(f4, lab, frame_step=1)
    assert len(pairs) == 2
    for ip, ii in pairs:
        assert lab[ip] and not lab[ii]
        # prefix-sharing: pixel-identical for the first 12 frames
        assert np.array_equal(f4[ip][:12], f4[ii][:12])


def test_bad_pair_raises():
    f = np.zeros((4, 10, 4, 4, 3), np.uint8)
    f[1, 5:] = 1
    with pytest.raises(ValueError):
        data.make_pairs(f, np.array([True, False, True, False]), frame_step=1)


def test_iter_pairs_and_manifest(tmp_path):
    for s in ("01", "02"):
        _make_quad(tmp_path, "O1", s)
    _make_quad(tmp_path, "O2", "01")
    _make_quad(tmp_path, "O3", "01")
    m = data.dev_manifest(tmp_path, frame_step=1)
    assert m["n_scenes"] == 4 and m["n_pairs"] == 8
    pairs = list(data.iter_dev_pairs(tmp_path, frame_step=1))
    assert len(pairs) == 8 and pairs[0]["scene_id"] == "O1/01"


def test_sample_indices():
    assert len(data.sample_indices(100, 2)) == 49 and data.sample_indices(100, 4)[-1] == 92


def test_prefix_partner():
    a = np.zeros((6, 4, 4, 3), np.uint8)
    early, late = a.copy(), a.copy()
    early[2:] = 9
    late[4:] = 9
    assert data.prefix_partner(a, [early, late]) == 1


def test_mp4_and_ip2_pairs(tmp_path):
    split = tmp_path / "Debug"
    (split / "Videos").mkdir(parents=True)
    rows = []
    for i, ty in enumerate(["1_Possible", "1_Impossible", "2_Impossible", "2_Possible"]):
        fn = f"Videos/v{i}.mp4"
        w = cv2.VideoWriter(str(split / fn), cv2.VideoWriter_fourcc(*"mp4v"), 30, (32, 32))
        for t in range(10):
            w.write(np.full((32, 32, 3), 10 * t, np.uint8))
        w.release()
        rows.append(f"0,n{i},{fn},g,c,e,{ty},None,Easy,Fixed")
    (split / "metadata.csv").write_text("SceneIndex,name,file_name,game_name,condition,env,type,occluder,Difficulty,Camera\n" + "\n".join(rows) + "\n")
    pairs = data.ip2_pairs(split)
    assert len(pairs) == 2
    v = data.load_ip2_video(split, pairs[0][0], stride=2)
    assert v.shape == (5, 32, 32, 3) and v.dtype == np.uint8


def test_npz_layout_equivalent(tmp_path):
    _make_quad(tmp_path / "png", "O1", "01", T=20)
    f4, lab, ids = data.load_dev_quadruplet(tmp_path / "png", "O1", "01")
    nz = tmp_path / "npz"; nz.mkdir()
    for k in range(4):
        np.savez_compressed(nz / f"O1_01_{k+1}.npz", frames=f4[k], is_possible=np.array(bool(lab[k])))
    g4, glab, gids = data.load_dev_quadruplet(nz, "O1", "01")
    assert np.array_equal(f4, g4) and (lab == glab).all() and ids == gids
    assert data.list_dev_scenes(nz) == [("O1", "01")]
    assert data.make_pairs(g4, glab, 1) == data.make_pairs(f4, lab, 1)
