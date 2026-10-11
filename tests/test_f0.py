def test_f0_builds(tmp_path):
    from vjepa_study.figures.f0_schematic import build
    out = build(tmp_path / "f0.pdf")
    assert out.exists() and out.stat().st_size > 1000
