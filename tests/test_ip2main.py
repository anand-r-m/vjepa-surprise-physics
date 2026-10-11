"""IntPhys 2 Main support (kaggle/ip2main/ip2main_lib.py): same loader and preprocessing as ip2debug, run_lib untouched."""
import base64
import csv
import io
import json
import re
import sys
import tarfile
import types
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "kaggle" / "common"), str(ROOT / "kaggle" / "ip2main"), str(ROOT / "scripts")]
import ip2main_lib  # noqa: E402
import make_p4_runs as P  # noqa: E402
import run_lib  # noqa: E402
from vjepa_study import data  # noqa: E402

COLS = "SceneIndex,name,file_name,game_name,condition,env,type,occluder,Difficulty,Camera".split(",")


def _meta(split_dir, n_scenes=3):
    split_dir.mkdir(parents=True)
    rows = []
    for sc in range(n_scenes):
        for k in (1, 2):
            for kind in ("Possible", "Impossible"):
                nm = f"v{sc}{k}{kind[0]}"
                rows.append(dict(SceneIndex=str(sc), name=nm, file_name=f"Videos/{nm}.mp4", game_name="g",
                                 condition="solidity" if sc % 2 else "continuity", env="e", type=f"{k}_{kind}",
                                 occluder="None", Difficulty="Easy", Camera="Fixed"))
    with open(split_dir / "metadata.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, COLS)
        w.writeheader()
        w.writerows(rows)


@pytest.fixture
def fake_root(tmp_path, monkeypatch):
    for s in ("Debug", "Main"):
        _meta(tmp_path / s)
    calls = []

    def fake_load(split_dir, row, max_frames=None, stride=1):
        calls.append((Path(split_dir).name, row["name"], max_frames, stride))
        rng = np.random.default_rng(abs(hash(row["name"])) % 2**32)
        return rng.integers(0, 255, (max_frames, 8, 8, 3)).astype(np.uint8)
    monkeypatch.setattr(data, "load_ip2_video", fake_load)
    # hash() of str differs per process but is stable within it, which is all the comparison needs
    return tmp_path, calls


def test_main_items_match_debug_loader_exactly(fake_root):
    root, calls = fake_root
    ref = list(run_lib.iter_items(dict(dataset="ip2debug", members="all"), ip2_root=root))
    got = list(ip2main_lib.iter_items_main(dict(dataset="ip2main", members="all"), root))
    assert len(ref) == len(got) == 12
    for a, b in zip(ref, got):
        assert a["video_id"] == b["video_id"] and a["label"] == b["label"]
        np.testing.assert_array_equal(a["frames"], b["frames"])
        assert a["pair_id"].replace("ip2/", "ip2m/") == b["pair_id"] and a["scene_id"].replace("ip2/", "ip2m/") == b["scene_id"]
    assert {c[2:] for c in calls} == {(100, 4)}                      # 60 fps -> 15 fps, first 100 frames, both datasets
    assert {c[0] for c in calls} == {"Debug", "Main"}
    assert {b["block"] for b in got} == {"solidity", "continuity"}   # block = metadata condition


def test_members_possible_and_subset(fake_root):
    root, _ = fake_root
    got = list(ip2main_lib.iter_items_main(dict(members="possible", subset=dict(every=2, n=2)), root))
    assert [g["label"] for g in got] == [0, 0] and len(got) == 2


def _fake_run_lib(log):
    m = types.SimpleNamespace()
    m.iter_items = lambda run, dev_root=None, ip2_root=None: iter([dict(delegated=run["dataset"])])
    m.find_ip2 = lambda p: Path(p)
    m.main = lambda *a: log.append(a) or "ok"
    return m


def test_install_delegates_and_is_idempotent(fake_root):
    root, _ = fake_root
    log = []
    m = _fake_run_lib(log)
    ip2main_lib.install(m)
    first = m.iter_items
    ip2main_lib.install(m)
    assert m.iter_items is first
    assert list(m.iter_items(dict(dataset="ipdev"))) == [dict(delegated="ipdev")]
    assert list(m.iter_items(dict(dataset="ip2debug"))) == [dict(delegated="ip2debug")]
    cfg = root / "runs.json"
    cfg.write_text(json.dumps(dict(ip2_path=str(root), runs=[dict(dataset="ip2main")])))
    assert m.main(str(cfg), root / "out", build_model=None, log=lambda *a: None) == "ok"
    assert len(list(m.iter_items(dict(dataset="ip2main", members="possible")))) == 6   # root taken from the wrapped main
    (root / "Main" / "metadata.csv").unlink()
    with pytest.raises(FileNotFoundError):
        m.main(str(cfg), root / "out", build_model=None, log=lambda *a: None)


def test_run_lib_still_rejects_unpatched_dataset():
    with pytest.raises(KeyError):
        list(run_lib.iter_items(dict(dataset="ip2main")))   # run_lib.py itself is untouched; support exists only via the module


@pytest.mark.skipif(not (ROOT / "data/intphys2/extracted/Main/metadata.csv").exists(), reason="IntPhys 2 not on disk")
def test_real_main_counts_and_overlap_names():
    ex = ROOT / "data/intphys2/extracted"
    pairs = data.ip2_pairs(ex / "Main")
    assert len(pairs) == 506
    dbg = {r["name"]: r for r in data.read_ip2_metadata(ex / "Debug")}
    ov = [p for p in pairs if p[0]["name"] in dbg]
    assert ov, "8 Debug videos also appear in Main by name (prereg s8)"
    it = next(ip2main_lib.iter_items_main(dict(members="possible", subset=dict(n=1)), ex))
    assert it["frames"].shape == (100, 512, 512, 3) and it["frames"].dtype == np.uint8
    r = ov[0][0]
    a = data.load_ip2_video(ex / "Main", r, max_frames=100, stride=4)
    b = data.load_ip2_video(ex / "Debug", dbg[r["name"]], max_frames=100, stride=4)
    # same name, but the Main file is a re-encode of the Debug file (bytes differ, ~2 grey levels mean abs pixel difference)
    assert a.shape == b.shape and 0 < np.abs(a.astype(int) - b.astype(int)).mean() < 5


def test_group_definition_and_hours():
    g = P.ip2main_groups()
    assert list(g) == ["ip2main_clean_m1"]
    (r,) = g["ip2main_clean_m1"]
    assert (r["model"], r["dataset"], r["edit"], r["members"], r["precision"], r["n_gpus"], r["frame_step"]) == \
        ("M1", "ip2main", None, "all", "fp16", 2, 2)
    ids = {x["run_id"] for gg in (P.groups(), P.clean_groups(), P.m2_groups()) for rs in gg.values() for x in rs}
    assert r["run_id"] not in ids
    assert P.summarize(g)["ip2main_clean_m1"]["hours"] == pytest.approx(1012 * 2.73 / 3600, abs=0.01)
    # frozen groups unaffected
    assert abs(sum(v["hours"] for v in P.summarize(P.groups()).values()) - 13.5) < 0.3


def _decode(run_py):
    m = re.search(r"^_B = '([A-Za-z0-9+/=]+)'", run_py.read_text(), re.M)
    tf = tarfile.open(fileobj=io.BytesIO(base64.b64decode(m.group(1))), mode="r:gz")
    return {x.name: tf.extractfile(x).read() for x in tf.getmembers() if x.isfile()}


@pytest.mark.skipif(not (ROOT / "kaggle/ip2main_clean_m1/run.py").exists() or not (ROOT / "kaggle/h1_inv_a/run.py").exists(),
                    reason="bundles not built")
def test_same_code_path_vs_h1_bundle():
    """Decoded Main bundle vs the 4c4017b h1_inv_a bundle: only the permitted files plus the new ip2main module differ
    (m2_vjepa2.py is the A-Q10 amendment, already in the allowlist)."""
    a, b = _decode(ROOT / "kaggle/h1_inv_a/run.py"), _decode(ROOT / "kaggle/ip2main_clean_m1/run.py")
    diff = {n for n in set(a) | set(b) if a.get(n) != b.get(n)}
    allowed = {"BUNDLE_INFO.json", "runs.json", "matches.json", "src/vjepa_study/models/m2_vjepa2.py"}
    new = {n for n in diff if n.startswith("kaggle/ip2main/")}
    assert diff - allowed - new == set(), diff
    assert new == {"kaggle/ip2main/ip2main_lib.py", "kaggle/ip2main/preamble.py"}
    assert a["kaggle/common/run_lib.py"] == b["kaggle/common/run_lib.py"] == (ROOT / "kaggle/common/run_lib.py").read_bytes()
    body = (ROOT / "kaggle/common/kernel_main.py").read_text()
    assert (ROOT / "kaggle/ip2main_clean_m1/run.py").read_text().endswith(body)
