"""Task 9.1 — OllamaClient unit tests (no real network).

All tests use ``httpx.MockTransport`` so no actual Ollama server is
required. Verifies:
  - Happy path: 3 suggestions parsed from JSON payload
  - Dict-wrapped payload (gemma3 sometimes returns {"suggestions": [...]})
  - Timeout → OllamaUnavailable
  - HTTP 500 → OllamaUnavailable
  - Empty response string → OllamaUnavailable
  - Non-list JSON → OllamaUnavailable
"""
from __future__ import annotations

import json
from typing import Callable

import httpx
import pytest

from creative_suite.ollama.client import OllamaClient, OllamaUnavailable


def _make_transport(
    responder: Callable[[httpx.Request], httpx.Response],
) -> httpx.MockTransport:
    return httpx.MockTransport(responder)


def _ok_response(suggestions: list[str]) -> httpx.Response:
    return httpx.Response(
        200,
        json={"response": json.dumps(suggestions), "done": True},
    )


def test_suggest_prompts_happy_path() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/generate"
        body = json.loads(request.content)
        assert body["model"] == "gemma3:4b"
        assert body["stream"] is False
        assert body["format"] == "json"
        assert len(body["images"]) == 1  # base64-encoded
        return _ok_response([
            "photoreal PBR wet concrete, subtle moss, 4k",
            "chipped industrial panel, grime, raking light",
            "weathered steel plates, rivets, rust streaks",
        ])

    c = OllamaClient(transport=_make_transport(handler))
    out = c.suggest_prompts(b"fake-png-bytes", "surface", "base_wall")
    c.close()
    assert len(out) == 3
    assert out[0].startswith("photoreal")


def test_suggest_prompts_accepts_dict_wrapped_payload() -> None:
    """gemma3:4b sometimes returns {"suggestions": [...]}; we unwrap."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "response": json.dumps({"suggestions": ["a", "b", "c", "d"]}),
                "done": True,
            },
        )

    c = OllamaClient(transport=_make_transport(handler))
    out = c.suggest_prompts(b"x", "skin", "visor")
    assert out == ["a", "b", "c"]  # capped at 3


def test_suggest_prompts_on_http_error_raises_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="boom")

    c = OllamaClient(transport=_make_transport(handler))
    with pytest.raises(OllamaUnavailable):
        c.suggest_prompts(b"x", "surface", None)


def test_suggest_prompts_on_timeout_raises_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timeout", request=request)

    c = OllamaClient(transport=_make_transport(handler))
    with pytest.raises(OllamaUnavailable):
        c.suggest_prompts(b"x", "surface", None)


def test_suggest_prompts_on_empty_response_raises_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"response": "", "done": True})

    c = OllamaClient(transport=_make_transport(handler))
    with pytest.raises(OllamaUnavailable):
        c.suggest_prompts(b"x", "surface", None)


def test_suggest_prompts_on_non_list_payload_raises_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"response": json.dumps("just a string"), "done": True}
        )

    c = OllamaClient(transport=_make_transport(handler))
    with pytest.raises(OllamaUnavailable):
        c.suggest_prompts(b"x", "surface", None)
