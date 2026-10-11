import numpy as np
import pytest

from vjepa_study.analysis import prereg as P


def mk_run(S_list, labels, pair_ids, scenes, blocks):
    n = len(S_list)
    W = max(len(s) for s in S_list)
    S = np.full((n, W, S_list[0].shape[1]), np.nan, np.float32)
    for i, s in enumerate(S_list):
        S[i, : len(s)] = s
    return dict(video_ids=np.array([f"v{i}" for i in range(n)]), S=S, lengths=np.array([len(s) for s in S_list]),
                label=np.array(labels), pair_id=np.array(pair_ids), scene_id=np.array(scenes), block=np.array(blocks))


def test_video_score_aggregations_and_event_window():
    S = np.array([[3.0, 1.0], [2.0, 5.0], [9.0, 8.0], [0.5, 4.0]])      # min over C: 1,2,8,0.5
    assert P.video_score(S, "mean") == pytest.approx((1 + 2 + 8 + 0.5) / 4)
    assert P.video_score(S, "max") == pytest.approx(8.0)
    # windows w: 4w+30 >= t_on ; t_on=40 -> w>=3 (4*3+30=42>=40; w=2: 38<40)
    assert P.video_score(S, "max", t_on=40) == pytest.approx(0.5)
    assert P.video_score(S, "max", t_on=38) == pytest.approx(8.0)       # w=2 included (38>=38)
    assert P.video_score(S, "max", t_on=500) == pytest.approx(0.5)      # empty set -> last window
    assert P.video_score(S, "mean", c_index=0) == pytest.approx(np.mean([3, 2, 9, 0.5]))


def test_tau_and_tiehalf_rules():
    assert P.tau_m([0.5, 0.6, 0.7]) == pytest.approx(2e-4 * 0.6)
    y = P.y_tiehalf([1.0, 1.00005, 0.5, 2.0], [1.0, 1.0, 1.0, 1.0], 1e-4)
    assert y.tolist() == [0.5, 0.5, 0.0, 1.0]
    assert P.y_tiehalf([1.0], [1.0], 0.0).tolist() == [0.5]             # exact-tie sensitivity
    assert P.y_strict([1.0, 2.0], [1.0, 1.0]).tolist() == [0.0, 1.0]
    assert P.flip3(np.array([1, 0.5, 0, 1]), np.array([1, 1, 0, 0])).tolist() == [0, 1, 0, 1]


def test_pair_index_and_clean_y():
    S = [np.full((5, 2), v, np.float32) for v in (1.0, 2.0, 3.0, 1.0)]
    d = mk_run(S, [0, 1, 1, 0], ["p0", "p0", "p1", "p1"], ["s0", "s0", "s0", "s0"], ["O1"] * 4)
    y, ys, px = P.clean_pair_y(d, tau=1e-4)
    assert px["pos"].tolist() == [0, 3] and px["imp"].tolist() == [1, 2] and y.tolist() == [1.0, 1.0]
    d2 = mk_run([np.full((5, 2), 1.0, np.float32)] * 4, [0, 1, 1, 0], ["p0", "p0", "p1", "p1"], ["s"] * 4, ["O1"] * 4)
    assert P.clean_pair_y(d2, 1e-4)[0].tolist() == [0.5, 0.5]


def test_h1_pair_level_seed_average_and_sign_test():
    y0 = np.array([1.0, 1.0, 0.0, 0.5])
    seeds = [np.array([1.0, 0.0, 0.0, 0.5]), np.array([1.0, 1.0, 0.0, 1.0]), np.array([1.0, 0.0, 1.0, 0.5])]
    y, fl = P.h1_pair_level(seeds, y0)
    assert y.tolist() == pytest.approx([1.0, 1 / 3, 1 / 3, 2 / 3])
    assert fl.tolist() == pytest.approx([0.0, 2 / 3, 1 / 3, 1 / 3])
    s = P.sign_test_exact(np.array([0.0] * 9 + [1.0]), np.array([1.0] * 9 + [1.0]))
    assert s["n_discordant"] == 9 and s["n_down"] == 9 and s["p"] == pytest.approx(2 * 0.5 ** 9)
    assert P.sign_test_exact(y0, y0)["p"] == 1.0
    assert P.sign_test_exact(np.array([1.0, 0.0]), np.array([0.0, 1.0]))["p"] == 1.0


def test_h1_eligibility_and_status():
    assert P.h1_eligible(0.8167) and P.h1_eligible(0.80) and not P.h1_eligible(0.7944)
    assert P.h1_model_status(0.12, 0.9).startswith("descriptive (floor")
    assert P.h1_model_status(0.02, 0.7).startswith("descriptive (clean")
    assert P.h1_model_status(0.02, 0.9) == "confirmatory"


def _h1_data(n=60, drop=0.0, floor=0.0, seed=0):
    rng = np.random.default_rng(seed)
    scene = np.repeat(np.arange(n // 2), 2)
    block = np.repeat(["O1", "O2", "O3"], n // 3)
    y0 = np.ones(n)
    y = y0.copy()
    y[rng.random(n) < drop] = 0.0
    fl = (y != y0).astype(float)
    f0p = (rng.random(n) < floor).astype(float)
    return scene, block, y0, y, fl, f0p


def test_h1_family_invariant_violated_and_holm14():
    scene, block, y0, y, fl, f0p = _h1_data(drop=0.0, floor=0.0)
    names = ["brightness", "noise", "blur", "jpeg", "zoom", "hflip", "fps_halve"]
    ed = {k: dict(y=y.copy(), flip=fl.copy()) for k in names}
    r = P.h1_family(ed, y0, f0p, scene, block, n_boot=300)
    assert r["f0_valid"] and all(v["decision"] == "invariant" for v in r["per_edit"].values())
    scene, block, y0, y, fl, f0p = _h1_data(drop=0.4, floor=0.0, seed=1)
    ed = {k: dict(y=y.copy(), flip=fl.copy()) for k in names}
    r = P.h1_family(ed, y0, f0p, scene, block, n_boot=300)
    assert all(v["decision"] == "violated" for v in r["per_edit"].values())
    assert all(0 <= v["holm_sign"] <= 1 and v["holm_flip"] >= v["p_flip_cluster"] for v in r["per_edit"].values())
    # Holm over 14 (not 7): adjusted p >= min(1, 14 * smallest p / ...)  -> the smallest holm is >= 14*p_min
    ps = [v["sign"]["p"] for v in r["per_edit"].values()] + [v["p_flip_cluster"] for v in r["per_edit"].values()]
    assert min(min(v["holm_sign"], v["holm_flip"]) for v in r["per_edit"].values()) >= min(1.0, 14 * min(ps)) - 1e-12


def test_h1_floor_instability_and_exclusion_mask():
    scene, block, y0, y, fl, f0p = _h1_data(drop=0.0, floor=0.3, seed=2)
    r = P.h1_family({"x": dict(y=y, flip=fl)}, y0, f0p, scene, block, n_boot=100)
    assert not r["f0_valid"]
    valid = np.arange(len(y0)) >= 10
    r = P.h1_family({"x": dict(y=y, flip=fl)}, y0, f0p * 0, scene, block, n_boot=100, valid={"x": valid})
    assert r["per_edit"]["x"]["n"] == len(y0) - 10 and r["per_edit"]["x"]["n_excluded"] == 10


def test_h1_flip_significance_uses_cluster_family_and_masked_f0():
    scene, block, y0, y, fl, f0p = _h1_data(drop=0.4, floor=0.0, seed=1)
    r = P.h1_family({"x": dict(y=y, flip=fl)}, y0, f0p, scene, block, n_boot=200)
    e = r["per_edit"]["x"]
    assert e["holm_flip_cluster"] >= e["p_flip_cluster"] and "holm_flip" in e
    # flip-only violation (dacc ~ 0, flips cancel): flip significance must come from h_clu[n+j]
    n = 60
    scene, block, y0, _, _, _ = _h1_data(n=n)
    y = y0.copy(); fl = np.zeros(n); fl[:30] = 1.0   # 50% flips, y unchanged on average
    ed = {"x": dict(y=y, flip=fl)}
    r = P.h1_family(ed, y0, np.zeros(n), scene, block, n_boot=200)
    e = r["per_edit"]["x"]
    assert e["holm_flip_cluster"] < 0.05 and e["decision"] == "violated"
    # masked f0: floor lives only in excluded pairs -> excess uses masked f0 (0), not the global mean
    f0p = np.zeros(n); f0p[:30] = 0.5
    valid = np.arange(n) >= 30
    fl2 = np.zeros(n); fl2[30:] = 0.12 * (np.arange(30) % 8 < 1)  # tiny flips in kept pairs
    seen = {}
    orig = P.h1_decision
    def spy(dacc, sig, flip, f0, flip_sig, a, b):
        seen["f0"] = f0
        return orig(dacc, sig, flip, f0, flip_sig, a, b)
    P.h1_decision = spy
    try:
        P.h1_family({"x": dict(y=y0.copy(), flip=fl2)}, y0, f0p, scene, block, n_boot=50, valid={"x": valid})
    finally:
        P.h1_decision = orig
    assert seen["f0"] == 0.0


def test_h1_flip_decision_follows_cluster_family_when_families_disagree():
    # Deterministic fixture (no RNG in the data). 7 identical edits; delta-acc > 0 (never "violated" via
    # delta-acc) with a cluster-significant delta-acc p ~ 0 but a non-significant exact sign test, so the
    # 14-p Holm ranks of the flip p-values differ between the sign family and the cluster family.
    n = 60
    scene, block = np.repeat(np.arange(30), 2), np.repeat(["O1", "O2", "O3"], 20)
    y0 = np.ones(n); y0[:4] = 0; y0[40:52] = 0.5
    y = y0.copy(); y[:4] = 1.0; y[20:24] -= 0.1; y[40:52] = 1.0; y[4:8] = y0[4:8] - 0.1
    fl = np.zeros(n); fl[:4] = 1; fl[20:24] = 1; fl[56:58] = 1    # 10/60 = 16.7% flips
    names = list("abcdefg")
    r = P.h1_family({k: dict(y=y, flip=fl) for k in names}, y0, np.zeros(n), scene, block, n_boot=2000)
    e = r["per_edit"]["a"]
    assert e["dacc"] > 0
    # families disagree on flip significance for this edit
    assert e["holm_flip"] >= 0.05 > e["holm_flip_cluster"]
    # decision follows the cluster family: flip >= 10%, excess >= 5pp, cluster-Holm flip significant
    assert e["decision"] == "violated"
    assert all(v["decision"] == "violated" for v in r["per_edit"].values())


def test_auroc_tau_and_h2_point_per_seed():
    assert P.auroc_tau([2, 2], [1, 1], 0.0) == 1.0
    assert P.auroc_tau([1.00005], [1.0], 1e-4) == 0.5
    assert P.auroc_tau([1.0], [1.0], 0.0) == 0.5
    rng = np.random.default_rng(0)
    dv = rng.normal(1, 1, 40)
    da = {"a": rng.normal(0, 1, (3, 40)), "b": rng.normal(0, 1, (1, 40))}
    r = P.h2_point(dv, da, 1e-6)
    manual = np.mean([np.mean([P.auroc_tau(dv, da["a"][s], 1e-6), P.auroc_tau(dv, da["b"][0], 1e-6)]) for s in range(3)])
    assert r["auroc"] == pytest.approx(manual) and len(r["seed_auroc"]) == 3
    assert P.foil_acc(np.array([2.0, 2.0]), {"a": np.array([[1.0, 3.0]])}, 0.0) == 0.5


def test_h2_bootstrap_holm2_and_a0():
    rng = np.random.default_rng(3)
    n = 60
    scene, block = np.repeat(np.arange(30), 2), np.repeat(["O1", "O2", "O3"], 20)
    mk = lambda mu: dict(dv=rng.normal(mu, 1, n), da={"t": rng.normal(0, 1, (2, n))}, tau=1e-4, y0=(rng.random(n) < 0.8).astype(float))
    models = {"M1": mk(2.0), "B1": mk(0.0), "B2": mk(0.5)}
    out = P.h2_bootstrap(models, scene, block, n_boot=200)
    assert out["M1"]["A"] > 0.8 and out["D_B1"]["ci"][0] > 0 and out["D_B2"]["ci"][0] > 0
    for k in ("D_B1", "D_B2"):
        assert 1 / 201 <= out[k]["p"] <= out[k]["p_holm"] <= 1
    assert out["M1"]["R"] == pytest.approx((out["M1"]["A"] - 0.5) / (out["M1"]["A0"] - 0.5))
    assert out["D_B1"]["D"] == pytest.approx(out["M1"]["A"] - out["B1"]["A"])


@pytest.mark.parametrize("A,Dlos,per,A0,exp", [
    (0.85, [0.01, 0.02], {"a": 0.9, "b": 0.8}, 0.9, "Specific"),
    (0.85, [0.01, 0.02], {"a": 0.9, "b": 0.6}, 0.9, "Specific, except type b"),
    (0.85, [0.01, 0.06], {"a": 0.9}, 0.9, "Separable but not beyond low-level baseline"),
    (0.85, [0.01, 0.02], {"a": 0.9}, 0.7, "Specific"),                         # detection-limited never touches Specific rows
    (0.72, [0.01, 0.01], {"a": 0.7}, 0.9, "Partial / inconclusive"),
    (0.60, [0.01, 0.01], {"a": 0.6}, 0.9, "Not specific"),
    (0.72, [0.01, 0.01], {"a": 0.7}, 0.80, "Detection-limited (not specific / partial)"),
    (0.60, [0.01, 0.01], {"a": 0.6}, 0.80, "Detection-limited (not specific / partial)"),
    (0.65, [0.01, 0.01], {"a": 0.6}, 0.85, "Not specific"),
])
def test_h2_outcome_table(A, Dlos, per, A0, exp):
    assert P.h2_outcome(A, Dlos, per, A0=A0)[0] == exp


def test_h2_outcome_reversed():
    assert P.h2_outcome(0.3, [1, 1], {"a": 0.3}, A_hi=0.45, A0=0.9) == ("Not specific", True)


def test_h3_and_g2():
    rng = np.random.default_rng(0)
    n = 90
    scene, block = np.arange(n), np.repeat(["O1", "O2", "O3"], 30)
    a = P.detection(rng.normal(2, 0.1, n), np.zeros(n), 1e-4)             # always detected
    b = P.detection(rng.normal(1, 0.1, n), np.zeros(n), 1e-4)
    m0 = P.detection(np.zeros(n), np.zeros(n), 1e-4)                      # degenerate model: all ties -> 0.5
    assert (m0 == 0.5).all()
    r = P.h3_analysis(a, b, m0, scene, block, n_boot=200)
    assert r["a"] == 1.0 and r["diff_m0r_ci"][0] > 0 and r["b_ci"][0] > 0.5
    assert r["learned_sensitivity_credited"] and r["g2"]
    assert not P.g2_pass(0.79, 0.9) and not P.g2_pass(0.9, 0.5)


def test_strata_proxy_t1_wilson():
    D = np.zeros(40); D[10:20] = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    assert P.abrupt_onset_proxy(D, 10, 20)
    D[10:20] = np.linspace(0.05, 1, 10)
    assert not P.abrupt_onset_proxy(D, 10, 20)
    assert P.stratified_values([1, 0, 1, 1], ["a", "a", "b", "b"])["b"]["mean"] == 1.0
    scene, block = np.repeat(np.arange(30), 2), np.repeat(["O1", "O2", "O3"], 20)
    y_a, y_b = np.ones(60), np.full(60, 0.5)
    t = P.paired_difference(y_a, y_b, scene, block, n_boot=100)
    assert t["diff"] == 0.5 and t["ci"][0] == pytest.approx(0.5)
    lo, hi = P.wilson(147, 180)
    assert 0.74 < lo < 0.77 and 0.86 < hi < 0.88


def test_holm_values():
    assert P.holm([0.03, 0.02]) == pytest.approx([0.04, 0.04])
    assert P.holm([0.01, 0.04]) == pytest.approx([0.02, 0.04])
    assert P.holm([0.6, 0.7]) == pytest.approx([1.0, 1.0])


def test_h2_outcome_holm_vs_intersection_union_disagree():
    # (.02, .045): Holm-2 adjusted (.04, .045) -> Specific, although a one-sided 2.5% CI bound for the
    # .045 comparison would fail (old intersection-union: min(D_lo) <= 0 -> Separable).
    # (.03, .04): Holm-2 adjusted (.06, .06) -> not significant.
    per = {"a": 0.9}
    adj = P.holm([0.02, 0.045])
    assert adj == pytest.approx([0.04, 0.045])
    assert P.h2_outcome(0.85, adj, per, A0=0.9)[0] == "Specific"
    adj2 = P.holm([0.03, 0.04])
    assert adj2 == pytest.approx([0.06, 0.06])
    assert P.h2_outcome(0.85, adj2, per, A0=0.9)[0] == "Separable but not beyond low-level baseline"
    # one comparison missing -> cannot be Specific
    assert P.h2_outcome(0.85, [0.001], per, A0=0.9)[0] == "Separable but not beyond low-level baseline"


def test_h2_bootstrap_p_is_one_sided_and_floored():
    rng = np.random.default_rng(5)
    n = 60
    scene, block = np.repeat(np.arange(30), 2), np.repeat(["O1", "O2", "O3"], 20)
    mk = lambda mu: dict(dv=rng.normal(mu, 1, n), da={"t": rng.normal(0, 1, (2, n))}, tau=1e-4, y0=np.ones(n))
    strong = P.h2_bootstrap({"M1": mk(5.0), "B1": mk(0.0), "B2": mk(0.0)}, scene, block, n_boot=200)
    assert strong["D_B1"]["p"] == pytest.approx(1 / 201)
    weak = P.h2_bootstrap({"M1": mk(0.0), "B1": mk(3.0), "B2": mk(3.0)}, scene, block, n_boot=200)
    assert weak["D_B1"]["p"] > 0.9
