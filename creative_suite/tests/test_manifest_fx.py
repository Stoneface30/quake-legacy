"""Tests for FX-to-manifest override mapping."""
from creative_suite.engine.manifest_generator import _fx_to_overrides


def test_slowmo_maps_to_slow():
    fx = [{"effect_type": "slowmo", "enabled": 1, "params": '{"rate": 0.5}'}]
    out = _fx_to_overrides(fx)
    assert out == {"slow": "0.5"}


def test_speedup_maps_to_slow():
    fx = [{"effect_type": "speedup", "enabled": 1, "params": '{"rate": 2.0}'}]
    out = _fx_to_overrides(fx)
    assert out == {"slow": "2.0"}


def test_shine_maps_to_shine_key():
    fx = [{"effect_type": "shine_on_kill", "enabled": 1, "params": "{}"}]
    out = _fx_to_overrides(fx)
    assert out.get("shine") == "1"
    assert "flag" not in out  # no longer uses flag= for shine


def test_zoom_maps_to_zoom_key():
    fx = [{"effect_type": "zoom", "enabled": 1, "params": '{"scale": 1.15}'}]
    out = _fx_to_overrides(fx)
    assert out.get("zoom") == "1.15"


def test_vignette_maps_to_vignette_key():
    fx = [{"effect_type": "vignette", "enabled": 1, "params": "{}"}]
    out = _fx_to_overrides(fx)
    assert out.get("vignette") == "1"


def test_bass_drop_maps_to_bass_drop_key():
    fx = [{"effect_type": "bass_drop", "enabled": 1, "params": "{}"}]
    out = _fx_to_overrides(fx)
    assert out.get("bass_drop") == "1"


def test_disabled_fx_excluded():
    fx = [{"effect_type": "shine_on_kill", "enabled": 0, "params": "{}"}]
    out = _fx_to_overrides(fx)
    assert "shine" not in out
    assert "flag" not in out
