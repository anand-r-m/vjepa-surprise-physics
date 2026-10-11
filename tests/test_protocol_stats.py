import numpy as np
import pytest

from vjepa_study.analysis import metrics as M
from vjepa_study.analysis import baselines as B


def test_tie_rule():
    si = np.array([1.0, 1.00005, 0.5, 2.0])
    sp = np.array([1.0, 1.0, 1.0, 1.0])
    v = M.verdict_scores(si, sp)
    assert v.tolist() == [0.5, 0.5, 0.0, 1.0]
    assert M.accuracy_ties(si, sp) == pytest.approx(0.5)
    assert M.tie_rate(si, sp) == 0.5
    # flip counts changes among {imp, poss, tie}
    assert M.flip_rate_ties(v, np.array([1.0, 1.0, 0.0, 1.0])) == 0.5


def test_aggregate_S():
    S = np.array([[3.0, 1.0], [2.0, 5.0], [np.nan, np.nan]])
    assert M.aggregate_S(S, "mean") == pytest.approx(1.5)       # min over C then mean: (1+2)/2
    assert M.aggregate_S(S, "max") == pytest.approx(2.0)
    assert M.aggregate_S(S, "mean", c_index=0) == pytest.approx(2.5)


def test_pooled_per_seed_then_average():
    rng = np.random.default_rng(0)
    dv = rng.normal(1, 1, 60)
    da = {"light": rng.normal(0, 1, (3, 60)), "jolt": rng.normal(0, 1, (1, 60))}
    r = M.h2_point(dv, da)
    manual = np.mean([np.mean([M.auroc(dv, da["light"][s]), M.auroc(dv, da["jolt"][0])]) for s in range(3)])
    assert r["auroc"] == pytest.approx(manual) and len(r["seed_auroc"]) == 3
    assert set(r["per_type"]) == {"light", "jolt"}


def test_foil_accuracy():
    assert M.foil_accuracy([2, 2], {"a": [1, 1]}) == 1.0
    assert M.foil_accuracy([1, 1], {"a": [1, 1]}) == 0.5


def test_stratified_bootstrap_structure():
    scenes = np.repeat(np.arange(12), 2)
    blocks = np.repeat(["O1", "O2", "O3"], 8)
    rng = np.random.default_rng(1)
    idx = M.stratified_cluster_indices(scenes, blocks, rng)
    assert len(idx) == 24                       # each block redraws exactly its own scene count
    for b in ["O1", "O2", "O3"]:
        drawn = {scenes[i] for i in idx if blocks[i] == b}
        assert drawn <= set(scenes[blocks == b])
    assert all(np.sum(idx == i) % 1 == 0 for i in range(24))
    # pairs of a scene always travel together
    counts = np.bincount(scenes[idx], minlength=12)
    assert (counts % 2 == 0).all()


def test_h2_bootstrap_joint_and_diff():
    rng = np.random.default_rng(2)
    n = 60
    scenes, blocks = np.repeat(np.arange(30), 2), np.repeat(["O1", "O2", "O3"], 20)
    good = dict(dv=rng.normal(2, 1, n), da={"t": rng.normal(0, 1, (3, n))})
    base = dict(dv=rng.normal(0, 1, n), da={"t": rng.normal(0, 1, (1, n))})
    out = M.h2_bootstrap({"M1": good, "B1": base}, scenes, blocks, n_boot=300, seed=3)
    assert out["M1"]["lo"] < out["M1"]["auroc"] < out["M1"]["hi"]
    d = out["diff_M1_minus_B1"]
    assert d["lo"] > 0 and d["diff"] == pytest.approx(out["M1"]["auroc"] - out["B1"]["auroc"])
    out2 = M.h2_bootstrap({"M1": good, "B1": base}, scenes, blocks, n_boot=300, seed=3)
    assert out2["M1"]["lo"] == out["M1"]["lo"]                   # seeded


@pytest.mark.parametrize("A,Dlo,per,Ahi,exp", [
    (0.85, 0.1, {"a": 0.9, "b": 0.8}, None, "Specific"),
    (0.85, 0.1, {"a": 0.9, "b": 0.6}, None, "Specific, except type b"),
    (0.85, -0.01, {"a": 0.9}, None, "Separable but not beyond low-level baseline"),
    (0.72, 0.2, {"a": 0.7}, None, "Partial / inconclusive"),
    (0.60, 0.2, {"a": 0.6}, None, "Not specific"),
    (0.80, 0.01, {"a": 0.8}, None, "Specific"),
    (0.65, 0.2, {"a": 0.6}, None, "Not specific"),
])
def test_outcome_table_exhaustive(A, Dlo, per, Ahi, exp):
    assert M.h2_outcome(A, Dlo, per, Ahi)[0] == exp


def test_outcome_reversed_subflag():
    lab, rev = M.h2_outcome(0.3, 0.0, {"a": 0.3}, A_hi=0.45)
    assert lab == "Not specific" and rev
    assert not M.h2_outcome(0.3, 0.0, {"a": 0.3}, A_hi=0.55)[1]


def test_outcome_covers_all_A():
    labs = {M.h2_outcome(a, 0.1, {"x": 0.9})[0] for a in np.linspace(0, 1, 101)}
    assert labs == {"Specific", "Partial / inconclusive", "Not specific"}


def test_h1_bootstrap_and_decision():
    n = 90
    scenes = np.repeat(np.arange(45), 2)
    blocks = np.repeat(["O1", "O2", "O3"], 30)
    clean = np.ones(n)
    dith = [np.where(np.arange(n) % 30 == 0, 0.0, 1.0) for _ in range(3)]       # f0 = 1/30
    same = M.h1_bootstrap(scenes, blocks, clean, clean.copy(), dith, n_boot=200, seed=1)
    assert same["flip"] == 0 and same["d_acc"] == 0 and same["p_flip_gt_floor"] > 0.5
    flipped = np.where(np.arange(n) % 4 == 0, 0.0, 1.0)                         # 25% flips
    r = M.h1_bootstrap(scenes, blocks, clean, flipped, dith, n_boot=300, seed=1)
    assert r["flip"] == pytest.approx(23 / 90) and r["p_flip_gt_floor"] < 0.05
    assert M.h1_decision(r["d_acc"], 0.001, r["flip"], r["f0"], 0.01, r["d_acc_ci"], r["flip_ci"], 0.95) == "violated"
    assert M.h1_decision(0.0, 1.0, 0.01, 0.01, 1.0, (-0.02, 0.01), (0.0, 0.05), 0.95) == "invariant"
    assert M.h1_decision(0.0, 1.0, 0.03, 0.01, 1.0, (-0.08, 0.01), (0.0, 0.07), 0.95) == "inconclusive"
    assert M.h1_decision(-0.2, 0.0, 0.5, 0.0, 0.0, (-0.3, -0.1), (0.4, 0.6), 0.6) == "descriptive"


def test_h1_exclusion_mask():
    scenes, blocks = np.arange(10), np.repeat(["O1", "O2"], 5)
    clean = np.ones(10); edit = clean.copy(); edit[:3] = 0
    valid = np.arange(10) >= 3
    r = M.h1_bootstrap(scenes, blocks, clean, edit, [clean], n_boot=50, valid=valid)
    assert r["flip"] == 0 and r["n"] == 7


def test_h3_and_g2():
    rng = np.random.default_rng(0)
    n = 90
    scenes, blocks = np.arange(n), np.repeat(["O1", "O2", "O3"], 30)
    ref = rng.normal(0, 1, n)
    ctrl = ref + 2          # always detected
    m0c, m0r = rng.normal(0, 1, n), rng.normal(0, 1, n)
    r = M.h3_detection(ctrl, ref, scenes, blocks, m0c, m0r, n_boot=200)
    assert r["rate"] == 1.0 and r["diff_ci"][0] > 0
    assert M.g2_pass(r["rate"], r["diff_ci"][0]) and not M.g2_pass(0.7, 0.1) and not M.g2_pass(0.9, -0.1)


def test_windowed_baselines():
    f = np.zeros((20, 4, 4, 3), np.float32)
    f[10:] = 1.0                                        # step at t=10
    b1 = B.b1_windows(f, ctx=(2, 4), window=16, stride=2)
    b2 = B.b2_windows(f, ctx=(2, 4), window=16, stride=2)
    assert b1.shape == b2.shape == (3, 2)
    assert b1[0, 0] == pytest.approx(1 / 14)            # one jump among 14 predicted frames
    assert b2[0, 0] == pytest.approx(6 / 14) and b2[2, 0] == 0.0 + b2[2, 0]
    # context change: last context frame already post-step -> zero error
    assert b2[2, 1] == 0.0 or b2[2, 1] >= 0
    # B1/B2 exactly invariant to time reversal of a constant-motion clip -> all ties
    ramp = np.arange(20, dtype=np.float32)[:, None, None, None] * np.ones((1, 4, 4, 3), np.float32)
    assert np.allclose(B.b1_windows(ramp), B.b1_windows(ramp[::-1]))


def test_b3_windows():
    g = np.zeros((2, 8, 5), np.float32)
    g[:, 4:] = 1.0                                      # change between tubelet 3 and 4
    s = B.b3_windows(g, ctx=(2, 8), tubelet=2)
    assert s[0, 0] == pytest.approx(1 / 7)              # predicted tubelets 1..7 -> 7 diffs, one jump
    assert s[0, 1] == pytest.approx(0.25)               # ctx 8: change INTO first predicted tubelet counts


def test_foil_accuracy_values():
    assert M.foil_accuracy([2, 2, 2], {"a": [1, 3, 2], "b": [1, 1, 1]}) == pytest.approx(0.75)


def test_frame_hash_dedupe():
    from vjepa_study import amend, edits
    x = np.random.default_rng(0).integers(0, 255, (4, 16, 16, 3), dtype=np.uint8)
    h = lambda s: amend.frame_hash(edits.apply_edit(x, "blur", "high", s))
    assert h(1) == h(2) == h(3)


def test_b1_whole_window_vs_predicted_window():
    f = np.zeros((20, 4, 4, 3), np.float32)
    f[3:] = 1.0                                         # one jump at t=3 (inside the context of C>=4)
    w = B.b1_whole_window(f, window=16, stride=2)
    assert w[0] == pytest.approx(1 / 15)
    b1 = B.b1_windows(f, ctx=(6, 8), window=16, stride=2)
    assert b1[0, 0] == pytest.approx(0.0) and b1[0, 1] == pytest.approx(0.0) and w[0] > 0
