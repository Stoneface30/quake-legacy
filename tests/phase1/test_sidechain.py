"""Unit tests for phase1.sidechain."""
from phase1.sidechain import build_sidechain_filter_chain, _parse_integrated_lufs


def test_build_sidechain_filter_chain_structure():
    fc = build_sidechain_filter_chain("music", "game")
    assert "sidechaincompress" in fc
    assert "threshold=0.05" in fc
    assert "attack=5" in fc
    assert "release=250" in fc
    assert "[music_ducked]" in fc
    assert fc.endswith("[mix]")


def test_build_sidechain_filter_chain_custom_params():
    fc = build_sidechain_filter_chain(
        "m", "g", threshold=0.08, ratio=4, attack_ms=10, release_ms=400
    )
    assert "threshold=0.08" in fc
    assert "ratio=4" in fc
    assert "attack=10" in fc
    assert "release=400" in fc


def test_parse_integrated_lufs():
    stderr = """
    [Parsed_ebur128_0 @ 0000] Integrated loudness:
      I:   -14.3 LUFS
      Threshold: -24.3 LUFS
    """
    from phase1.sidechain import _parse_integrated_lufs  # re-import for coverage
    assert _parse_integrated_lufs(stderr) == -14.3


def test_parse_integrated_lufs_none():
    assert _parse_integrated_lufs("no lufs here") is None
