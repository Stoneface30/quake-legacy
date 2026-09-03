"""The review workstation must never answer an unauthenticated stranger.

These tests exist because of one specific failure: a hostname can be created
in DNS and in the tunnel BEFORE anyone creates the Access application for it.
In that window the edge has no policy to apply and forwards everything. The
origin's own check is what makes that window safe.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from creative_suite.api import access_guard as ag         # noqa: E402


@pytest.fixture
def app():
    a = FastAPI()
    a.add_middleware(ag.CloudflareAccessMiddleware)

    @a.get("/secret")
    def secret():
        return {"notes": "player identities and creative truth"}

    return a


def test_a_guarded_host_without_a_token_is_refused(app):
    """The whole point. No Access application yet means no header, and the
    correct answer is 403 rather than the data."""
    c = TestClient(app)
    r = c.get("/secret", headers={"host": "review.conchita.uk"})
    assert r.status_code == 403
    assert "access required" in r.json()["error"]
    assert "player identities" not in r.text


def test_the_refusal_explains_the_likely_cause(app):
    r = TestClient(app).get("/secret", headers={"host": "review.conchita.uk"})
    d = r.json()["detail"]
    assert "Access application" in d and "Google account" in d


def test_a_forged_token_is_refused(app):
    c = TestClient(app)
    r = c.get("/secret", headers={"host": "review.conchita.uk",
                                  ag.HEADER: "not.a.jwt"})
    assert r.status_code == 403
    assert r.json()["error"] == "invalid access token"


def test_loopback_does_not_bypass_the_guard(app):
    """The bug this replaced. cloudflared runs on THIS machine and connects
    to http://localhost:8766, so tunnel traffic arrives from 127.0.0.1. A
    client-address exemption would have switched the guard off for exactly
    the requests it exists to inspect -- confirmed against the running origin,
    which answered 200 with real data before this was fixed."""
    c = TestClient(app, client=("127.0.0.1", 5555))
    r = c.get("/secret", headers={"host": "review.conchita.uk"})
    assert r.status_code == 403
    assert "player identities" not in r.text
    assert ag.status()["exempt_by_client_address"] == []


def test_local_use_of_the_machine_is_unchanged(app):
    """Local work goes to localhost:8766, which is not a guarded host."""
    assert TestClient(app).get(
        "/secret", headers={"host": "localhost"}).status_code == 200


def test_an_unguarded_host_is_not_affected(app):
    r = TestClient(app).get("/secret", headers={"host": "127.0.0.1"})
    assert r.status_code == 200


def test_the_issuer_is_pinned_to_this_team():
    """A valid signature is not enough. Without the issuer check, a token
    from any Cloudflare team would pass."""
    import inspect
    src = inspect.getsource(ag.verify)
    assert 'issuer=f"https://{TEAM_DOMAIN}"' in src
    assert '"RS256"' in src


def test_status_reports_the_policy_and_leaks_nothing():
    s = ag.status()
    assert s["team_domain"].endswith("cloudflareaccess.com")
    assert "review.conchita.uk" in s["guarded_hosts"]
    assert "closed" in s["default"]
    assert not any("token" in str(v).lower() and "jwt" in str(v).lower()
                   for v in s.values())
