"""review.conchita.uk is the curation workstation, and nothing else.

THE DEFECT THIS FIXES. The review hostname pointed at the whole Creative
Suite, and `GET /` there redirects to `/studio` -- the authoring shell, with
STUDIO, LAB, CREATIVE, FORGE, GRAPH, a Part selector, GENERATE INTRO and
REBUILD. The media audit was clean; the FRONT DOOR was wrong. Opening the
review host handed the user a movie editor and no reviewer.

TWO THINGS ARE WRONG WITH THAT, not one. The obvious one is that the user
landed on the wrong page. The quieter one is that a hostname published to the
internet was exposing every authoring, render-control and filesystem route in
the process, simply because they shared a FastAPI app.

SO THE HOST GETS A ROOT AND AN ALLOWLIST. On `review.conchita.uk`:

    GET /            renders the reviewer, server-side
    /api/review/*    the review API, media, rounds, filters, session
    /health          liveness
    everything else  404

Rendering, not redirecting: the product URL is `https://review.conchita.uk/`
and the user should never see or need `/api/review/ui`. Not a JS redirect
either -- that would mean shipping the legacy HTML first and hoping the
browser leaves.

NOTHING IS DELETED. The authoring app is untouched and still answers on
localhost and its own routes. The rule is only that it does not belong on
this hostname.
"""
from __future__ import annotations

import os
from pathlib import Path

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse

FRONTEND = Path(__file__).resolve().parents[1] / "frontend"
REVIEW_PAGE = FRONTEND / "review.html"

# Paths the curation workstation genuinely needs. Everything the reviewer
# fetches is under /api/review; both pages are self-contained HTML with
# inline CSS and JS, so there is no asset tree to open up.
ALLOWED_EXACT = {"/", "/health", "/favicon.ico"}
ALLOWED_PREFIXES = ("/api/review/",)


def review_hosts() -> set[str]:
    raw = os.getenv("CF_ACCESS_HOSTS", "review.conchita.uk")
    return {h.strip().lower() for h in raw.split(",") if h.strip()}


def is_allowed(path: str) -> bool:
    return path in ALLOWED_EXACT or path.startswith(ALLOWED_PREFIXES)


class ReviewHostMiddleware(BaseHTTPMiddleware):
    """Serve the reviewer at the root of the review host, and only that.

    Runs INSIDE the Access guard: authentication happens first, so an
    unauthenticated request never reaches this and never learns which routes
    exist.
    """

    async def dispatch(self, request: Request, call_next):
        host = (request.headers.get("host") or "").split(":")[0].lower()
        if host not in review_hosts():
            return await call_next(request)

        path = request.url.path
        if path == "/":
            # Rendered here, not redirected. The product URL is the bare
            # hostname; the user should never have to know an API path.
            if not REVIEW_PAGE.exists():
                return JSONResponse(status_code=500,
                                    content={"error": "review.html missing"})
            return HTMLResponse(REVIEW_PAGE.read_text(encoding="utf-8"))

        if not is_allowed(path):
            # A curation workstation has no business answering for Forge,
            # Studio, render control or the filesystem. Sharing a process is
            # not a reason to share a surface.
            return JSONResponse(
                status_code=404,
                content={"error": "not part of the review workstation",
                         "detail": ("review.conchita.uk serves the human "
                                    "curation UI and its API. The authoring "
                                    "application lives on its own routes, "
                                    "locally."),
                         "path": path})
        return await call_next(request)
