import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import b2_checks as C  # noqa: E402
from vjepa_study.analysis import baselines as bl  # noqa: E402

PX = dict(pos=np.arange(0, 200, 2), imp=np.arange(1, 200, 2))


def test_shuffle_null_centred_at_half():
    s = np.random.default_rng(0).normal(size=200)
    s[PX["imp"]] += 5                      # perfect classifier
    assert C.pair_acc(s, PX)[0] == 1.0
    dist = C.shuffle_within_pairs(s, PX, 1000, 1, 0.0)
    assert abs(dist.mean() - 0.5) < 0.01 and dist.max() < 0.75


def test_self_comparison_all_ties():
    s = np.random.default_rng(1).normal(size=200)
    from vjepa_study.analysis import prereg as P
    y = P.y_tiehalf(s[PX["pos"]], s[PX["pos"]], 1e-4)
    assert (y == 0.5).all()


def test_independent_recompute_matches_baselines(clip):
    f = clip.astype(np.float32) / 255
    f = np.concatenate([f, f[::-1], f, f[::-1]])[:36]
    assert np.allclose(C.recompute_b2(f), bl.b2_windows(f), atol=1e-6)
    assert np.allclose(C.recompute_b1(f), bl.b1_windows(f), atol=1e-6)


def test_auroc_and_divergence():
    assert C.auroc([3, 4], [1, 2]) == 1.0 and C.auroc([1, 1], [1, 1]) == 0.5
    a = np.zeros((10, 2, 2, 3), np.uint8)
    b = a.copy(); b[6] = 5
    assert C.first_divergence(a, b) == 6
