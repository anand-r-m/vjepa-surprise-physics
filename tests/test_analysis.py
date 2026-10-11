import numpy as np
import pytest
from scipy import stats

from vjepa_study.analysis import metrics as M
from vjepa_study.analysis import baselines as B


def test_pairwise_accuracy_flip():
    imp = np.array([2., 1., 3., 5.]); pos = np.array([1., 2., 3., 4.])
    assert M.verdicts(imp, pos).tolist() == [True, False, False, True]  # tie -> wrong
    assert M.pairwise_accuracy(imp, pos) == 0.5
    v_edit = np.array([True, True, False, False])
    assert M.flip_rate(v_edit, M.verdicts(imp, pos)) == 0.5
    assert M.flip_rate(M.verdicts(imp, pos), M.verdicts(imp, pos)) == 0.0


def test_aggregate():
    c = [np.array([1., 5., 2.]), np.array([4., 4.])]
    assert M.aggregate(c, "max").tolist() == [5., 4.]
    assert M.aggregate(c, "mean").tolist() == pytest.approx([8 / 3, 4.])


def test_mcnemar_hand_computed():
    # b=1 (clean right, edit wrong), c=7: n=8, p = 2*P(X<=1), X~Bin(8,.5) = 2*9/256
    clean = np.array([1] * 1 + [0] * 7 + [1] * 5, bool)
    edit = np.array([0] * 1 + [1] * 7 + [1] * 5, bool)
    r = M.mcnemar_exact(clean, edit)
    assert (r["b"], r["c"]) == (1, 7)
    assert r["p"] == pytest.approx(18 / 256)
    # b = c -> p = 1 ; no discordant -> 1
    assert M.mcnemar_exact([1, 0], [0, 1])["p"] == 1.0
    assert M.mcnemar_exact([1, 1], [1, 1])["p"] == 1.0
    # b=0,c=5: p = 2 * (1/32) = 1/16
    assert M.mcnemar_exact([0] * 5, [1] * 5)["p"] == pytest.approx(1 / 16)


def test_holm_hand_computed():
    # p = [0.01, 0.04, 0.03, 0.005], m=4: sorted .005,.01,.03,.04 -> 4*.005=.02, 3*.01=.03,
    # 2*.03=.06, 1*.04=.04 -> cummax .02,.03,.06,.06
    adj = M.holm([0.01, 0.04, 0.03, 0.005])
    assert adj == pytest.approx([0.03, 0.06, 0.06, 0.02])
    assert M.holm([0.5, 0.9]) == pytest.approx([1.0, 1.0])  # 2*.5=1, then cummax with .9
    assert M.holm([0.4]) == pytest.approx([0.4])


def test_auroc_known():
    assert M.auroc([2, 3], [0, 1]) == 1.0
    assert M.auroc([0, 1], [2, 3]) == 0.0
    assert M.auroc([1, 1], [1, 1]) == 0.5
    assert M.auroc([1, 3], [2]) == 0.5
    rng = np.random.default_rng(0)
    # Gaussians d' = 1: AUROC = Phi(1/sqrt2)
    x = rng.normal(1, 1, 20000); y = rng.normal(0, 1, 20000)
    assert M.specificity_auroc(x, y) == pytest.approx(stats.norm.cdf(1 / np.sqrt(2)), abs=0.01)


def test_auroc_matches_bruteforce():
    rng = np.random.default_rng(1)
    x = rng.integers(0, 5, 30).astype(float); y = rng.integers(0, 5, 25).astype(float)
    bf = np.mean([(a > b) + 0.5 * (a == b) for a in x for b in y])
    assert M.auroc(x, y) == pytest.approx(bf)


def test_bootstrap_ci_deterministic_and_brackets():
    rng = np.random.default_rng(2)
    x = rng.normal(1, 1, 100); y = rng.normal(0, 1, 100)
    a = M.bootstrap_auroc(x, y, n_boot=500, seed=7)
    b = M.bootstrap_auroc(x, y, n_boot=500, seed=7)
    assert a == b
    assert a["lo"] < a["auroc"] < a["hi"]
    assert M.bootstrap_auroc(x, y, n_boot=500, seed=8) != a


def test_bootstrap_coverage_sanity():
    true = stats.norm.cdf(1 / np.sqrt(2))
    rng = np.random.default_rng(3)
    hits, R = 0, 150
    for _ in range(R):
        x = rng.normal(1, 1, 60); y = rng.normal(0, 1, 60)
        ci = M.bootstrap_auroc(x, y, n_boot=300, seed=int(rng.integers(1e9)))
        hits += ci["lo"] <= true <= ci["hi"]
    assert 0.85 <= hits / R <= 1.0


def test_bootstrap_scene_clusters_and_unequal():
    rng = np.random.default_rng(4)
    sv = np.repeat(np.arange(20), 3); sa = np.repeat(np.arange(20), 2)
    x = rng.normal(1, 1, 60); y = rng.normal(0, 1, 40)
    r = M.bootstrap_auroc(x, y, n_boot=300, seed=1, scene_viol=sv, scene_abrupt=sa)
    assert r["lo"] < r["auroc"] < r["hi"]
    r2 = M.bootstrap_auroc(x, y, n_boot=300, seed=1)  # unequal lengths
    assert r2["lo"] < r2["auroc"] < r2["hi"]


def test_bootstrap_default_10000():
    import inspect
    assert inspect.signature(M.bootstrap_auroc).parameters["n_boot"].default == 10_000
    assert inspect.signature(M.bootstrap_auroc_diff).parameters["n_boot"].default == 10_000


def test_paired_difference():
    rng = np.random.default_rng(5)
    n = 150
    common = rng.normal(0, 1, n)
    # model A separates well, B at chance; same items
    dv_a = common + 1.5; da_a = rng.normal(0, 1, n)
    dv_b = rng.normal(0, 1, n); da_b = rng.normal(0, 1, n)
    r = M.bootstrap_auroc_diff(dv_a, da_a, dv_b, da_b, n_boot=1000, seed=0)
    assert r["diff"] == pytest.approx(M.auroc(dv_a, da_a) - M.auroc(dv_b, da_b))
    assert r["lo"] > 0
    # identical models -> diff exactly 0 with degenerate CI
    z = M.bootstrap_auroc_diff(dv_a, da_a, dv_a, da_a, n_boot=200, seed=0)
    assert z["diff"] == 0 and z["lo"] == 0 == z["hi"]
    with pytest.raises(ValueError):
        M.bootstrap_auroc_diff(dv_a, da_a, dv_b[:-1], da_b)


def test_clopper_pearson_known():
    lo, hi = M.clopper_pearson(8, 10)
    assert lo == pytest.approx(0.4439, abs=1e-3) and hi == pytest.approx(0.9748, abs=1e-3)
    assert M.clopper_pearson(0, 10)[0] == 0 and M.clopper_pearson(10, 10)[1] == 1
    assert M.clopper_pearson(0, 10)[1] == pytest.approx(1 - 0.025 ** (1 / 10), abs=1e-6)


def test_detection_rate():
    r = M.detection_rate([2, 3, 1, 5], [1, 4, 1, 2])
    assert (r["k"], r["n"], r["rate"]) == (2, 4, 0.5) and r["lo"] < 0.5 < r["hi"]


def test_mean_sd():
    m, s = M.mean_sd_across_seeds([1, 2, 3])
    assert m == 2 and s == 1


# ---- baselines
def _frames(T=6):
    f = np.zeros((T, 4, 4, 3), np.uint8)
    for t in range(T):
        f[t] = t * 10
    return f


def test_b1_framediff():
    f = _frames(); f[3:] += 50
    b1 = B.b1_framediff(f)
    assert len(b1) == 5 and b1.tolist() == pytest.approx([10, 10, 60, 10, 10])
    assert B.b1_framediff(np.zeros((5, 4, 4, 3), np.uint8)).max() == 0


def test_b1_no_uint8_wraparound():
    f = np.zeros((2, 2, 2, 3), np.uint8); f[1] = 255
    assert B.b1_framediff(f)[0] == 255


def test_b2_copy_last():
    f = _frames()
    assert B.b2_copy_last(f).tolist() == pytest.approx([10] * 5)
    assert B.b2_copy_last(f, window=(3, 6)).tolist() == pytest.approx([10, 10, 10])
    ctx = B.b2_copy_last(f, window=(3, 6), mode="context")
    assert ctx.tolist() == pytest.approx([10, 20, 30])
    with pytest.raises(ValueError):
        B.b2_copy_last(f, window=(0, 3))
