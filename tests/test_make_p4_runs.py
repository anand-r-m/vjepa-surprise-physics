import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import make_p4_runs as P  # noqa: E402


def test_counts_match_projection():
    g = P.groups()
    s = P.summarize(g)
    allr = [r for rs in g.values() for r in rs]
    assert len({r["run_id"] for r in allr}) == len(allr)
    m1 = [r for r in allr if r["model"] == "M1"]
    assert sum(r["members"] == "all" for r in m1) == 34 and sum(r["members"] == "possible" for r in m1) == 31
    m0 = [r for r in allr if r["model"] == "M0r"]
    assert len(m0) == 7 and all(r["members"] == "possible" for r in m0)
    for r in allr:
        assert r["precision"] == "fp16" and r["n_gpus"] == 2 and r["frame_step"] == 2
        assert r["seed"] == 1 or r["edit"]["name"] in {"brightness", "noise", "dither", "lighting_global", "lighting_local", "jolt_base"}
    assert all(v["hours"] <= 3.3 for v in s.values())
    assert abs(sum(v["hours"] for v in s.values()) - (12.6 + 0.9)) < 0.3     # M1 main + M0r extra (GPU_PROJECTION)


def test_m2_groups_mirror_prereg_tier2_and_are_unique():
    g = P.m2_groups()
    allr = [r for rs in g.values() for r in rs]
    ids = [r["run_id"] for r in allr]
    assert len(set(ids)) == len(ids) and all(r["model"] == "M2" for r in allr)
    assert not set(ids) & {r["run_id"] for rs in list(P.groups().values()) + list(P.clean_groups().values()) for r in rs}
    for r in allr:
        assert r["precision"] == "fp16" and r["n_gpus"] == 2 and r["dataset"] == "ipdev"
    t2 = {r["run_id"] for k, rs in g.items() if "dose" not in k for r in rs}
    need = {f"P4_M2_ipdev_{e}-high_s{s}" for e in ("brightness", "noise") for s in (1, 2, 3)}
    need |= {f"P4_M2_ipdev_{e}-high_s1" for e in ("blur", "jpeg", "zoom", "hflip", "fps_halve", "vflip", "time_reversal")}
    need |= {f"P4_M2_ipdev_dither-on_s{s}" for s in (1, 2, 3)} | {"P4_M2_ipdev_base_ref-ref_s1", "P4_M2_ipdev_clean-skip4_s1"}
    need |= {f"P4_M2_ipdev_{k}-mid_s{s}" for k in ("lighting_global", "lighting_local", "jolt_base") for s in (1, 2, 3)}
    need |= {"P4_M2_ipdev_zoom_base-mid_s1"}
    assert t2 == need
    assert all(v["hours"] <= 3.3 for v in P.summarize(g).values())
    assert not any(r["run_id"] == "P4_M2_ipdev_clean_s1" for r in allr)      # old mask_index-1 run is never regenerated
