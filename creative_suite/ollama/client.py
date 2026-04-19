"""Ollama vision client — local gemma3:4b-vision at 127.0.0.1:11434.

Spec §4.5: optional prompt-suggestion sidecar. Returns 3 short suffixes
the user can append to `user_prompt`. Treats ANY failure (timeout, bad
JSON, HTTP error, empty response, Ollama not running) as a single
``OllamaUnavailable`` — the UI disables itself and the user keeps typing.

Design notes:
  - Default 5s timeout — gemma3:4b-vision on CPU does 2-3s per prompt on
    the dev machine. 5s is the cutoff before we declare "not available".
  - `format=json` with `stream=False` so we get one complete response
    and don't have to parse NDJSON streaming frames.
  - We cap the returned list at 3 items; model sometimes returns more.
"""
from __future__ import annotations

import base64
import json
from typing import Any, cast

import httpx


class OllamaUnavailable(Exception):
    """Raised for any failure talking to Ollama — timeout, HTTP error,
    parse error, empty response. The API layer translates this to a
    503, frontend disables the suggest button for the session."""


def _encode_b64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("ascii")


def _build_prompt(category: str, subcategory: str | None) -> str:
    sub = subcategory or "unknown"
    return (
        f"This is a Quake 3 texture (category: {category}, subcategory: {sub}). "
        "Suggest 3 short prompt suffixes that would turn this into a "
        "photorealistic PBR surface for a fragmovie. Each suffix under 20 "
        "words. Return as a JSON array of exactly 3 strings, no extra keys."
    )


class OllamaClient:
    """Minimal vision client. One method — ``suggest_prompts`` — keeps
    the surface area tight."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:11434",
        model: str = "gemma3:4b",
        *,
        timeout_s: float = 5.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_s = timeout_s
        # Test injection: MockTransport makes httpx calls deterministic.
        self._client = httpx.Client(transport=transport, timeout=timeout_s)

    def suggest_prompts(
        self, image_bytes: bytes, category: str, subcategory: str | None
    ) -> list[str]:
        """Return 3 prompt suffix suggestions for ``image_bytes``.

        Raises ``OllamaUnavailable`` on ANY failure — timeout, HTTP
        error, unparseable JSON, empty response, non-list payload.
        """
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": _build_prompt(category, subcategory),
            "images": [_encode_b64(image_bytes)],
            "format": "json",
            "stream": False,
        }
        try:
            r = self._client.post(f"{self.base_url}/api/generate", json=payload)
            r.raise_for_status()
            outer = r.json()
            raw = outer.get("response")
            if not isinstance(raw, str) or not raw.strip():
                raise OllamaUnavailable("empty response from Ollama")
            parsed: Any = json.loads(raw)
            # Accept either `["a","b","c"]` or `{"suggestions":[...]}`.
            if isinstance(parsed, dict):
                d = cast(dict[str, Any], parsed)
                parsed = (
                    d.get("suggestions")
                    or d.get("prompts")
                    or d.get("items")
                )
            if not isinstance(parsed, list):
                raise OllamaUnavailable("Ollama payload is not a list")
            items = [str(s).strip() for s in cast(list[Any], parsed) if str(s).strip()]
            if not items:
                raise OllamaUnavailable("Ollama returned empty list")
            return items[:3]
        except OllamaUnavailable:
            raise
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            raise OllamaUnavailable(str(exc)) from exc

    def close(self) -> None:
        self._client.close()
