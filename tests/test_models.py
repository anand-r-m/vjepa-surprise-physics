import warnings

import numpy as np
import pytest

torch = pytest.importorskip("torch")
warnings.filterwarnings("ignore")


def _tiny(**kw):
    from vjepa_study.models.m1_vjepa import M1VJEPA
    return M1VJEPA(model_name="vit_base", resolution=32, device="cpu", batch_windows=4, **kw)


def test_m0r_surprise_contract_and_determinism():
    from vjepa_study.models.m0r import M0r
    m = M0r(init_seed=0, model_name="vit_base", resolution=32, device="cpu", batch_windows=4)
    fr = np.random.default_rng(0).integers(0, 255, (40, 40, 40, 3), dtype=np.uint8)
    r = m.surprise(fr, frame_step=2)
    assert r["S"].shape == (2, 5) and r["S"].dtype == np.float32 and np.isfinite(r["S"]).all()
    assert r["target_feats"].shape == (2, 8, 768) and r["target_feats"].dtype == np.float16
    assert len(r["idx"]) == 19 and r["S"].std() > 0
    r2 = m.surprise(fr, frame_step=2)
    assert np.abs(r["S"] - r2["S"]).max() < 1e-6
    m1 = M0r(init_seed=1, model_name="vit_base", resolution=32, device="cpu")
    assert np.abs(m1.surprise(fr)["S"] - r["S"]).max() > 0        # different init -> different surprise
    with pytest.raises(ValueError):
        m.surprise(fr, window=12)


def test_checkpoint_coverage_check(tmp_path):
    m = _tiny(random_init_seed=0)
    pref = lambda sd, p: {p + k: v for k, v in sd.items()}
    good = dict(encoder=pref(m.encoder.state_dict(), "module."), target_encoder=pref(m.target_encoder.state_dict(), "module."),
                predictor=pref(m.predictor.state_dict(), "module."), epoch=1)
    torch.save(good, tmp_path / "ok.pth")
    ok = _tiny(ckpt_path=str(tmp_path / "ok.pth"))
    assert all(r["n_missing"] == 0 for r in ok.info["load_report"].values())
    # key naming without 'backbone.' is repaired
    renamed = dict(good, encoder={k.replace("module.backbone.", "module."): v for k, v in good["encoder"].items()})
    torch.save(renamed, tmp_path / "ren.pth")
    assert all(r["n_missing"] == 0 for r in _tiny(ckpt_path=str(tmp_path / "ren.pth")).info["load_report"].values())
    # wrong content raises
    bad = dict(good, predictor={"nonsense": torch.zeros(1)})
    torch.save(bad, tmp_path / "bad.pth")
    with pytest.raises(RuntimeError):
        _tiny(ckpt_path=str(tmp_path / "bad.pth"))


def test_target_cache_equals_recompute():
    from vjepa_study.models.m0r import M0r
    m = M0r(init_seed=0, model_name="vit_base", resolution=32, device="cpu")
    x = torch.randn(2, 3, 16, 32, 32)
    with torch.no_grad():
        l1, h = m._window_losses(x, 4)
        l2, _ = m._window_losses(x, 4, h)
        l3, _ = m._window_losses(x, 4)
    assert torch.equal(l2, l3) and torch.equal(l1, l3)


def test_m2_mask_index_is_zero():
    """Human-approved fix (Q10 B, 2026-10-08): the V-JEPA 2 predictor is queried with mask token 0 (official
    training value; tokens 1-9 of the released vitl.pt are zero). kernel_main builds M2VJEPA2 with the default."""
    import inspect
    from vjepa_study.models import m2_vjepa2
    assert inspect.signature(m2_vjepa2.M2VJEPA2.__init__).parameters["mask_index"].default == 0
    src = inspect.getsource(m2_vjepa2.M2VJEPA2)
    assert "mask_index=self.mask_index" in src
    kmain = (__import__("pathlib").Path(__file__).resolve().parents[1] / "kaggle" / "common" / "kernel_main.py").read_text()
    assert "M2VJEPA2(ckpt_path=str(p), repo_root=CODE, device=dev, precision=prec)" in kmain   # no override
