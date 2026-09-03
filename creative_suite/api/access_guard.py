"""Cloudflare Access enforcement at the origin.

The review workstation holds player identities, chat, unpublished footage and
the director's own creative notes. It must never be reachable by anyone who
has not authenticated with the user's Google account.

WHY THE ORIGIN CHECKS TOO. Cloudflare Access already refuses unauthenticated
requests at the edge, so this looks redundant. It is not, and the failure it
guards against is specific: a hostname can exist in DNS and in the tunnel
BEFORE anyone creates the Access application for it. In that window the edge
has no policy to apply, forwards everything, and the review API is public.
That window is exactly when a mistake is easiest to make and hardest to
notice.

So the origin does its own check, and the default is closed. If no Access
application covers this hostname, Cloudflare injects no JWT, the origin sees
that and answers 403. The safe state is the one that needs no configuration.

WHAT IS VERIFIED. The `Cf-Access-Jwt-Assertion` header, RS256, against the
team's published public keys, with issuer pinned to the team domain and
audience pinned when the AUD tag is configured. A signature alone is not
enough: without the issuer check, a token from any Cloudflare team would
pass.

THE HOST HEADER IS THE ONLY CRITERION. An earlier version of this exempted
requests from 127.0.0.1, reasoning that a tunnel request would come from
outside. That is false here and dangerously so: cloudflared runs on THIS
machine and connects to http://localhost:8766, so every tunnel request
arrives from loopback. The exemption would have disabled the guard for
exactly the traffic it exists to check. Verified by asking the running origin
for a guarded host from loopback -- it answered 200 with real data.

So local use keeps working because it goes to `localhost:8766`, which is not
a guarded host. A request that names `review.conchita.uk` is answered only
with a valid Access token, wherever it came from.
"""
from __future__ import annotations

import os
import time
from typing import Any

import jwt
from jwt import PyJWKClient
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

# The user's existing Access team, read off the two hostnames already
# protected by it (odysseus and music both 302 here).
TEAM_DOMAIN = os.getenv("CF_ACCESS_TEAM_DOMAIN", "conchitata.cloudflareaccess.com")
# The Access application's AUD tag. Optional: without it the guard still
# requires a token issued by THIS team, which already excludes the world.
AUD = os.getenv("CF_ACCESS_AUD", "").strip()

HEADER = "Cf-Access-Jwt-Assertion"

# Hosts that must never be served without an Access token. Anything reached
# through the tunnel arrives with one of these in Host.
def _guarded_hosts() -> set[str]:
    raw = os.getenv("CF_ACCESS_HOSTS", "review.conchita.uk")
    return {h.strip().lower() for h in raw.split(",") if h.strip()}


_jwks: PyJWKClient | None = None
_jwks_at = 0.0
_JWKS_TTL = 3600.0


def _client() -> PyJWKClient:
    """Cached key client. Cloudflare rotates keys, so it is refreshed, but
    not per request -- that would put a network call in front of every clip."""
    global _jwks, _jwks_at
    now = time.monotonic()
    if _jwks is None or now - _jwks_at > _JWKS_TTL:
        _jwks = PyJWKClient(f"https://{TEAM_DOMAIN}/cdn-cgi/access/certs")
        _jwks_at = now
    return _jwks


def verify(token: str) -> dict[str, Any]:
    """Return the claims, or raise. Issuer is pinned; audience when known."""
    key = _client().get_signing_key_from_jwt(token).key
    opts = {"verify_aud": bool(AUD)}
    return jwt.decode(token, key, algorithms=["RS256"],
                      audience=AUD or None,
                      issuer=f"https://{TEAM_DOMAIN}",
                      options=opts)


class CloudflareAccessMiddleware(BaseHTTPMiddleware):
    """Refuse any guarded-host request that did not come through Access."""

    async def dispatch(self, request: Request, call_next):
        host = (request.headers.get("host") or "").split(":")[0].lower()
        if host not in _guarded_hosts():
            return await call_next(request)
        # No client-address exemption. cloudflared runs on this machine, so
        # tunnel traffic IS loopback traffic; trusting the source address
        # would switch the guard off for the only requests it must inspect.
        token = request.headers.get(HEADER)
        if not token:
            # The common cause is a hostname that exists before its Access
            # application does. Say so, because the fix is one dashboard
            # step and the alternative is a silent public endpoint.
            return JSONResponse(
                status_code=403,
                content={"error": "cloudflare access required",
                         "detail": ("no Cf-Access-Jwt-Assertion header. If "
                                    "this hostname has no Access application "
                                    "yet, create one for this host and allow "
                                    "your Google account; until then the "
                                    "origin refuses every remote request"),
                         "team": TEAM_DOMAIN})
        try:
            claims = verify(token)
        except Exception as exc:                                # noqa: BLE001
            return JSONResponse(status_code=403,
                                content={"error": "invalid access token",
                                         "detail": type(exc).__name__})
        request.state.access_email = claims.get("email")
        return await call_next(request)


def status() -> dict[str, Any]:
    """What the guard is currently enforcing. No secrets: a team domain and
    an AUD tag are public identifiers, and the token itself is never logged."""
    return {"team_domain": TEAM_DOMAIN,
            "aud_configured": bool(AUD),
            "guarded_hosts": sorted(_guarded_hosts()),
            "exempt_by_client_address": [],   # deliberately none; see module docstring
            "local_access": "http://127.0.0.1:8766 -- an unguarded host name",
            "default": "closed -- no token, no answer"}
