import numpy as np
import pytest


@pytest.fixture
def clip():
    rng = np.random.default_rng(123)
    base = rng.integers(40, 200, size=(1, 48, 64, 3))
    drift = rng.integers(-5, 6, size=(16, 48, 64, 3))
    x = np.clip(base + np.cumsum(drift, axis=0) // 3, 0, 255).astype(np.uint8)
    # add smooth structure so blur/zoom/shift change pixels
    x[:, 10:30, 20:40, :] = 220
    return x
