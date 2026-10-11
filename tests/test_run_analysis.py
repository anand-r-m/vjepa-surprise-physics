import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import run_analysis as RA  # noqa: E402
from vjepa_study import schema  # noqa: E402
from vjepa_study.analysis import prereg as P  # noqa: E402

BLOCKS = ["O1", "O2", "O3"]
PAIRS = [(b, q, k) for b in BLOCKS for q in (1, 2) for k in (0, 1)]       # 12 pairs, 6 quadruplets


def make_run(root, rid, members="all", seed=0, shift_imp=0.05, shift_all=0.0, W=17, base=False):
    rng = np.random.default_rng(abs(hash(rid)) % 2**31 if seed is None else seed)
    ids, S, lab, pid, sc, blk = [], [], [], [], [], []
    for (b, q, k) in PAIRS:
        for label in (0, 1):
            if members == "possible" and label:
                continue
            base_lvl = np.random.default_rng(hash((b, q, k, label)) % 2**31 if False else (q * 7 + k * 3 + BLOCKS.index(b))).normal(0.55, 0.02)
            s = base_lvl + 0.01 * rng.normal(size=(W, 5)) + shift_all + (shift_imp if label else 0.0)
            ids.append(f"{b}/{q}/{k}/{label}"); S.append(s.astype(np.float32)); lab.append(label)
            pid.append(f"{b}/{q:02d}/p{k}"); sc.append(f"{b}/{q:02d}"); blk.append(b)
    bl = {n: [np.abs(rng.normal(0.05, 0.01, s.shape)).astype(np.float32) for s in S] for n in ("B1", "B2", "B3")}
    schema.save_run(root / rid / "surprise.npz", ids, S, None, baselines=bl, label=np.array(lab), pair_id=np.array(pid),
                    scene_id=np.array(sc), block=np.array(blk))


@pytest.fixture
def runs(tmp_path):
    root = tmp_path / "runs"
    P4 = "P4_M1_ipdev_"
    make_run(root, P4 + "clean_s1", seed=1)
    make_run(root, P4 + "clean-skip4_s1", seed=2, W=5)
    for e in RA.H1_EDITS:
        for s in ((1, 2, 3) if e in RA.SEEDED else (1,)):
            make_run(root, f"{P4}{e}-high_s{s}", seed=10 + s, W=5 if e == "fps_halve" else 17)
    for s in (1, 2, 3):
        make_run(root, f"{P4}dither-on_s{s}", seed=20 + s)
    for t in RA.SPEC_TYPES:
        for s in ((1, 2, 3) if t in RA.SEEDED else (1,)):
            make_run(root, f"{P4}{t}-mid_s{s}", members="possible", seed=30 + s, shift_all=0.01)
    make_run(root, P4 + "base_ref-ref_s1", members="possible", seed=40)
    for e in ("vflip", "time_reversal", "hflip"):
        make_run(root, f"{P4}{e}-high_s1", seed=50, shift_all=0.05 if e == "vflip" else 0.0)
    make_run(root, "P4_M0r_ipdev_clean-init0_s1", seed=60, shift_imp=0.0)
    make_run(root, "P4_M0r_ipdev_vflip-high_s1", members="possible", seed=61, shift_imp=0.0)
    matches = dict(pairs={f"{b}/{q:02d}/p{k}": dict(event=dict(t_on=10 + 4 * k, t_off=100, fallback=False, excluded_late=(k == 1 and q == 2 and b == "O3")), onset_abrupt=bool(q % 2), onset_diff=0.05, affected_area_fraction=0.02)
                          for (b, q, k) in PAIRS})
    (tmp_path / "matches.json").write_text(json.dumps(matches))
    return tmp_path


def test_end_to_end_clean_h1_h2_h3(runs):
    out = runs / "out"
    RA.main(["--runs", str(runs / "runs"), "--out", str(out), "--matches", str(runs / "matches.json"),
             "--models", "M1", "--stages", "clean", "h1", "h2", "h3", "--n-boot", "40"])
    clean = json.loads((out / "clean.json").read_text())
    assert clean["tau"]["M1"]["tau"] == pytest.approx(2e-4 * clean["tau"]["M1"]["median_score"])
    assert set(clean["tau"]) >= {"M1", "B1(M1)", "B2(M1)", "B3(M1)"}
    assert clean["models"]["M1"]["mean"]["n_pairs"] == 12 and clean["models"]["M1"]["mean"]["acc_tiehalf"] > 0.9
    assert clean["T1_M1_minus_B2_paired_clean_mean"]["ci"]
    h1 = json.loads((out / "h1_M1.json").read_text())
    assert set(h1["per_edit"]) == set(RA.H1_EDITS) and h1["f0_valid"]
    assert h1["status"] in ("confirmatory",) or h1["status"].startswith("descriptive")
    assert all("holm_sign" in v and "decision" in v for v in h1["per_edit"].values())
    h2 = json.loads((out / "h2.json").read_text())
    assert h2["n_excluded_late"] == 1 and h2["n_pairs_used"] == 11
    assert "D_B1" in h2 and "D_B2" in h2 and h2["outcome_M1"][0]
    assert set(h2["strata_block_descriptive"]) == {"O1", "O2", "O3"} and set(h2["strata_onset_proxy_descriptive"]) == {"abrupt", "gradual/occluded"}
    assert h2["descriptors"]["median_onset_diff"] == 0.05
    h3 = json.loads((out / "h3_M1.json").read_text())
    assert h3["a"] > 0.9 and "g2" in h3 and "reversal_detection" in h3 and "pairwise_acc_vflip" in h3


def test_missing_run_fails_loudly(runs):
    (runs / "runs" / "P4_M1_ipdev_noise-high_s2" / "surprise.npz").unlink()
    with pytest.raises(FileNotFoundError, match="noise-high_s2"):
        RA.main(["--runs", str(runs / "runs"), "--out", str(runs / "o"), "--models", "M1", "--stages", "clean", "h1", "--n-boot", "10"])


def test_tau_scale_zero_gives_exact_tie_sensitivity(runs):
    RA.main(["--runs", str(runs / "runs"), "--out", str(runs / "o"), "--models", "M1", "--stages", "clean", "h1", "--n-boot", "10", "--tau-scale", "0"])
    assert (runs / "o" / "h1_M1_exactties.json").exists() and not (runs / "o" / "h1_M1.json").exists()


def test_make_retention_synthetic(tmp_path):
    import make_retention as MR
    from test_data import _make_quad
    root = tmp_path / "dev"
    _make_quad(root, "O1", "01", T=30)
    m = tmp_path / "m.json"
    m.write_text(json.dumps(dict(pairs={f"O1/01/p{k}": dict(event=dict(t_on=12, t_off=30)) for k in (0, 1)})))
    R = MR.run(root, m, tmp_path / "r.json", res=32)
    r = json.loads((tmp_path / "r.json").read_text())
    assert set(r["zoom"]) == {"O1/01/p0", "O1/01/p1"} and all(0 <= v <= 1 for v in r["zoom"].values())


def test_eligibility_uses_fp32_run_and_A1_A2(runs, tmp_path):
    f32 = tmp_path / "fp32"
    make_run(f32, "P2_M1_ipdev_clean_s1", seed=1, shift_imp=-0.05)           # fp32 run with inverted pairs: accuracy ~0
    RA.main(["--runs", str(runs / "runs"), "--out", str(runs / "o2"), "--models", "M1", "--stages", "clean", "h1",
             "--n-boot", "10", "--fp32-runs", str(f32), "--h1-agg", "max"])
    h1 = json.loads((runs / "o2" / "h1_M1_A1_max.json").read_text())
    assert h1["eligibility_clean_acc_tiehalf"] < 0.2 and h1["status"].startswith("descriptive")
    clean = json.loads((runs / "o2" / "clean.json").read_text())
    assert set(clean["models"]["M1"]["A2_fixed_C_mean_agg"]) == {"2", "6", "10"}


ARGS = lambda runs, out, *x: ["--runs", str(runs / "runs"), "--out", str(out), "--matches", str(runs / "matches.json"),
                              "--models", "M1", "--n-boot", "20", *x]


def test_strict_tie_sensitivities_h1_h2_h3(runs):
    out = runs / "strict"
    RA.main(ARGS(runs, out, "--stages", "clean", "h1", "h2", "h3", "--tie-mode", "strict"))
    for f in ("h1_M1_strict.json", "h2_strict.json", "h3_M1_strict.json"):
        assert (out / f).exists(), f
    assert json.loads((out / "h2_strict.json").read_text())["variant"]["tie_value"] == 0.0
    h3 = json.loads((out / "h3_M1_strict.json").read_text())
    assert h3["variant"]["tau_scale"] == 0.0 and 0 <= h3["a"] <= 1
    base = runs / "tiehalf"
    RA.main(ARGS(runs, base, "--stages", "clean", "h3"))
    assert 0 <= json.loads((base / "h3_M1.json").read_text())["a"] <= 1


def test_exact_tie_sensitivity_names_h2_h3(runs):
    out = runs / "exact"
    RA.main(ARGS(runs, out, "--stages", "clean", "h2", "h3", "--tau-scale", "0"))
    assert (out / "h2_exactties.json").exists() and (out / "h3_M1_exactties.json").exists()


def test_h2_h3_A1_A2_variants(runs):
    out = runs / "abl"
    RA.main(ARGS(runs, out, "--stages", "clean", "h2", "h3", "--agg", "A1_mean"))
    RA.main(ARGS(runs, out, "--stages", "clean", "h2", "h3", "--agg", "A1_full_max"))
    RA.main(ARGS(runs, out, "--stages", "clean", "h1", "h2", "h3", "--fixed-c", "6"))
    for f in ("h2_A1_mean", "h2_A1_full_max", "h2_A2_C6", "h3_M1_A1_mean", "h3_M1_A1_full_max", "h3_M1_A2_C6", "h1_M1_A2_C6"):
        assert (out / (f + ".json")).exists(), f
    v = json.loads((out / "h2_A2_C6.json").read_text())["variant"]
    assert v["c_index"] == 2 and v["event_aligned"] is True and v["how"] == "max"
    assert json.loads((out / "h2_A1_mean.json").read_text())["variant"] == dict(how="mean", event_aligned=False, c_index=None, tie_value=0.5, tau_scale=1.0)
    # tau of the variant is the 2e-4 x median of the variant's own clean scores
    clean = schema.load_surprise(runs / "runs" / "P4_M1_ipdev_clean_s1" / "surprise.npz")
    var = RA.make_var("h3", "primary", 6)
    assert var.tau(clean) == pytest.approx(2e-4 * np.median(P.video_scores(clean, "S", "max", None, 2)))


def test_tau_aggregation_per_prereg_sec2(runs):
    """H2 (event-aligned) and H3 tau come from full-clip-MAX clean scores; H1 / clean accuracy tau from mean scores."""
    clean = schema.load_surprise(runs / "runs" / "P4_M1_ipdev_clean_s1" / "surprise.npz")
    t_max = 2e-4 * np.median(P.video_scores(clean, "S", "max"))
    t_mean = 2e-4 * np.median(P.video_scores(clean, "S", "mean"))
    assert t_max != t_mean
    for stage in ("h2", "h3"):
        v = RA.make_var(stage, "primary")
        assert v.how == "max" and v.event == (stage == "h2")
        assert v.tau(clean) == pytest.approx(t_max)           # event alignment never enters tau
    assert RA.h1_var("mean").tau(clean) == pytest.approx(t_mean)


def test_match_target_missed_filter(runs):
    m = json.loads((runs / "matches.json").read_text())
    m["meta"] = dict(mid_ratio_summary={
        "lighting_global": dict(median=1.0, frac_within_0p9_1p1=0.95), "lighting_local": dict(median=1.02, frac_within_0p9_1p1=0.92),
        "jolt_base": dict(median=0.7, frac_within_0p9_1p1=0.2), "zoom_base": dict(median=1.0, frac_within_0p9_1p1=0.5)})
    (runs / "m2.json").write_text(json.dumps(m))
    out = runs / "o"
    RA.main(["--runs", str(runs / "runs"), "--out", str(out), "--matches", str(runs / "m2.json"), "--models", "M1",
             "--stages", "clean", "h2", "--n-boot", "20"])
    h2 = json.loads((out / "h2.json").read_text())
    assert h2["match_target_missed"] == ["jolt_base", "zoom_base"]
    sens = h2["sensitivity_exclude_missed_types"]
    assert sens["dropped_types"] == ["jolt_base", "zoom_base"] and set(sens["per_type"]) == {"lighting_global", "lighting_local"}
    assert "D_B1" in sens and "outcome" in sens
    assert set(h2["M1"]["per_type"]) == set(RA.SPEC_TYPES)            # primary unchanged
    # no meta -> no sensitivity, flag unavailable
    RA.main(ARGS(runs, runs / "o3", "--stages", "clean", "h2"))
    h2b = json.loads((runs / "o3" / "h2.json").read_text())
    assert h2b["match_target_missed"] == [] and h2b["match_target_missed_available"] is False


def _put_meta(runs, rid, **kw):
    meta = dict(status="done", n_gpus=2, precision="fp16", env=dict(bundle=dict(repo_head=RA.REPO_HEAD_ALLOWLIST[0], repo_dirty=False)))
    meta.update(kw)
    (runs / "runs" / rid / "meta.json").write_text(json.dumps(meta))


def test_run_meta_check_consistent_and_mismatch(runs):
    ids = [p.name for p in (runs / "runs").iterdir()]
    for rid in ids:
        _put_meta(runs, rid)
    r = RA.run_meta_check(runs / "runs", ["M1"], runs / "mo")
    assert r["ok"] and r["n_runs"] == len(ids) and r["missing"] == []
    _put_meta(runs, "P4_M1_ipdev_noise-high_s1", precision="fp32")
    with pytest.raises(RuntimeError, match="precision"):
        RA.main(ARGS(runs, runs / "mo2", "--stages", "clean"))
    r = json.loads((runs / "mo2" / "meta_check.json").read_text())
    assert not r["ok"] and r["mismatches"][0]["key"] == "precision"
    with pytest.raises(RuntimeError, match="precision"):                                  # --allow-meta-mismatch never bypasses precision
        RA.main(ARGS(runs, runs / "mo3", "--stages", "clean", "--allow-meta-mismatch"))
    assert not json.loads((runs / "mo3" / "meta_check.json").read_text())["ok"]
    _put_meta(runs, "P4_M1_ipdev_noise-high_s1", n_gpus=1)
    with pytest.raises(RuntimeError, match="n_gpus"):
        RA.main(ARGS(runs, runs / "mo4", "--stages", "clean", "--allow-meta-mismatch"))
    _put_meta(runs, "P4_M1_ipdev_noise-high_s1", env=dict(bundle=dict(repo_head="def")))   # head outside allowlist
    with pytest.raises(RuntimeError, match="repo_head"):
        RA.main(ARGS(runs, runs / "mo5", "--stages", "clean"))
    RA.main(ARGS(runs, runs / "mo6", "--stages", "clean", "--allow-meta-mismatch"))      # repo_head override is recorded, not silent
    assert json.loads((runs / "mo6" / "meta_check.json").read_text())["bypassed"]


def test_repo_head_allowlist_equivalence():
    mk = lambda h, **kw: dict(status="done", n_gpus=2, precision="fp16", env=dict(bundle=dict(repo_head=h)), **kw)
    metas = {"P4_M1_ipdev_a_s1": mk("A"), "P4_M1_ipdev_b_s1": mk("B"), "P4_M2_ipdev_a_s1": mk("A")}
    assert not P.check_run_meta(metas)["ok"]                                               # strict equality without allowlist
    assert P.check_run_meta(metas, allowed_heads=("A", "B"))["ok"]                         # allowlisted heads are equivalent
    r = P.check_run_meta(metas, allowed_heads=("A",))
    assert not r["ok"] and r["mismatches"][0]["not_in_allowlist"] == ["B"]
    metas["P4_M1_ipdev_b_s1"]["precision"] = "fp32"                                        # allowlist never covers precision
    assert any(m["key"] == "precision" for m in P.check_run_meta(metas, allowed_heads=("A", "B"))["mismatches"])


def test_check_run_meta_skips_aliases_and_reports_missing():
    ok = dict(status="done", n_gpus=2, precision="fp16", env=dict(bundle=dict(repo_head="a")))
    r = P.check_run_meta({"P4_M1_ipdev_hflip-high_s1": ok, "P4_M1_ipdev_hflip-high_s2": dict(status="identical_by_construction"),
                          "P4_M1_ipdev_x_s1": None, "P4_M2_ipdev_y_s1": {**ok, "precision": "fp32"}})
    assert r["ok"] and r["missing"] == ["P4_M1_ipdev_x_s1"]          # different models may differ in precision; repo_head same


def test_strict_equals_y_strict_and_missed_rule():
    x, ref = np.array([1.0, 1.0, 0.5, 2.0]), np.array([1.0, 0.9, 0.9, 2.0])
    assert (P.y_tiehalf(x, ref, 0.0, 0.0) == P.y_strict(x, ref)).all()
    assert P.auroc_tau([1, 1], [1, 0], 0.0, 0.0) == 0.5 and P.auroc_tau([1, 1], [1, 0], 0.0) == 0.75
    assert P.match_missed({"a": dict(median=1.0, frac_within_0p9_1p1=0.9), "b": dict(median=1.06, frac_within_0p9_1p1=1.0),
                           "c": dict(median=1.0, frac_within_0p9_1p1=0.89), "d": dict(median=float("nan"), frac_within_0p9_1p1=1.0)}) == ["b", "c", "d"]


def test_old_m2_clean_run_excluded_from_m2_contrasts(tmp_path):
    ok = dict(status="done", n_gpus=2, precision="fp16", env=dict(bundle=dict(repo_head="a")))
    runs = tmp_path / "runs"
    for rid_ in ("P4_M2_ipdev_clean_s1", "P4_M2_ipdev_clean-mi0_s1"):
        (runs / rid_).mkdir(parents=True)
        (runs / rid_ / "surprise.npz").write_bytes(b"x")
        (runs / rid_ / "meta.json").write_text(json.dumps(dict(ok, precision="fp32") if rid_ == "P4_M2_ipdev_clean_s1" else ok))
    assert RA.Runs(runs).clean_id("M2") == "P4_M2_ipdev_clean-mi0_s1"
    assert RA.Runs(runs).clean_id("M1") == "P4_M1_ipdev_clean_s1"
    r = RA.run_meta_check(runs, ["M2"], tmp_path / "o", allowed_heads=("a",))      # old run (fp32 here) would abort if it were included
    assert r["n_runs"] == 1
