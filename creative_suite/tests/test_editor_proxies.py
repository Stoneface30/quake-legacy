"""Tests for proxy generator (CS_FFMPEG_MOCK mode)."""
from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from creative_suite.editor.proxies import (
    ensure_proxy,
    generate_proxy,
    is_fresh,
    proxy_path,
)


@pytest.fixture(autouse=True)
def _mock_ffmpeg(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CS_FFMPEG_MOCK", "1")


def test_proxy_path_uses_stem_plus_proxy_mp4(tmp_path: Path) -> None:
    p = proxy_path(tmp_path, "chunk_0042.mp4")
    assert p.name == "chunk_0042.proxy.mp4"


def test_generate_proxy_writes_stub_in_mock_mode(tmp_path: Path) -> None:
    src = tmp_path / "chunk_0001.mp4"
    src.write_bytes(b"fake-mp4-source")
    proxy = proxy_path(tmp_path / "proxies", src.name)
    out = generate_proxy(src, proxy)
    assert out == proxy
    assert proxy.exists()
    assert proxy.read_bytes().startswith(b"PROXY")


def test_is_fresh_true_when_proxy_newer(tmp_path: Path) -> None:
    src = tmp_path / "c.mp4"
    src.write_bytes(b"x")
    proxy = tmp_path / "c.proxy.mp4"
    proxy.write_bytes(b"PROXY!!!")
    # Force proxy mtime newer
    future = time.time() + 100
    os.utime(proxy, (future, future))
    assert is_fresh(src, proxy) is True


def test_is_fresh_false_when_proxy_older(tmp_path: Path) -> None:
    src = tmp_path / "c.mp4"
    src.write_bytes(b"x")
    proxy = tmp_path / "c.proxy.mp4"
    proxy.write_bytes(b"PROXY!!!")
    # Force source mtime newer (simulate re-render)
    future = time.time() + 100
    os.utime(src, (future, future))
    assert is_fresh(src, proxy) is False


def test_is_fresh_false_when_proxy_missing(tmp_path: Path) -> None:
    src = tmp_path / "c.mp4"
    src.write_bytes(b"x")
    proxy = tmp_path / "c.proxy.mp4"
    assert is_fresh(src, proxy) is False


def test_is_fresh_false_when_proxy_empty(tmp_path: Path) -> None:
    src = tmp_path / "c.mp4"
    src.write_bytes(b"x")
    proxy = tmp_path / "c.proxy.mp4"
    proxy.write_bytes(b"")
    assert is_fresh(src, proxy) is False


def test_ensure_proxy_skips_when_fresh(tmp_path: Path) -> None:
    src = tmp_path / "chunk_0001.mp4"
    src.write_bytes(b"fake")
    proxies = tmp_path / "proxies"
    p1 = ensure_proxy(src, proxies)
    mtime1 = p1.stat().st_mtime
    time.sleep(0.05)
    # Second call should be a no-op (proxy fresh)
    p2 = ensure_proxy(src, proxies)
    assert p2 == p1
    assert p2.stat().st_mtime == mtime1


def test_ensure_proxy_regenerates_when_source_newer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    src = tmp_path / "chunk_0001.mp4"
    src.write_bytes(b"fake")
    proxies = tmp_path / "proxies"
    ensure_proxy(src, proxies)  # first generation

    calls: list[Path] = []
    from creative_suite.editor import proxies as proxies_mod
    real_generate = proxies_mod.generate_proxy

    def spy_generate(s: Path, p: Path) -> Path:
        calls.append(s)
        return real_generate(s, p)

    monkeypatch.setattr(proxies_mod, "generate_proxy", spy_generate)

    # Touch source to future to invalidate cache
    future = time.time() + 200
    os.utime(src, (future, future))
    ensure_proxy(src, proxies)
    assert len(calls) == 1


def test_generate_proxy_cleans_up_partial_on_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Disable mock mode so the ffmpeg-bin-missing path fires
    monkeypatch.delenv("CS_FFMPEG_MOCK", raising=False)
    monkeypatch.setattr(
        "creative_suite.editor.proxies._ffmpeg_bin",
        lambda: "nonexistent_ffmpeg_xyz",
    )
    src = tmp_path / "c.mp4"
    src.write_bytes(b"x")
    proxy = tmp_path / "out" / "c.proxy.mp4"
    with pytest.raises(Exception):
        generate_proxy(src, proxy)
    # No .partial should remain
    partials = list(proxy.parent.glob("*.partial")) if proxy.parent.exists() else []
    assert partials == []
