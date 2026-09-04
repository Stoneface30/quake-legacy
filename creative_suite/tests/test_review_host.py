"""review.conchita.uk is the curation workstation, and nothing else.

The media audit was clean; the front door was not. `GET /` redirects to
`/studio` -- the authoring shell with STUDIO, LAB, CREATIVE, FORGE, GRAPH,
GENERATE INTRO and REBUILD -- and the review hostname inherited it because
the route is host-agnostic and the tunnel points at the whole app.

Two things were wrong, not one. The user landed on the wrong page, and a
hostname published to the internet was exposing every authoring and
render-control route in the process purely because they shared a FastAPI app.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from creative_suite.api import access_guard as ag           # noqa: E402
from creative_suite.api import review_host as rh            # noqa: E402
from creative_suite.app import create_app                   # noqa: E402

HOST = {"host": "review.conchita.uk", "Cf-Access-Jwt-Assertion": "stub"}
LEGACY_WORDS = ("FORGE", "GENERATE INTRO", "STUDIO", "CREATIVE", "GRAPH")


@pytest.fixture
def client(monkeypatch):
    # Signature verification is exercised in test_access_guard; here the
    # question is routing, so a request that HAS passed Access is simulated.
    monkeypatch.setattr(ag, "verify", lambda t: {"email": "test@local"})
    return TestClient(create_app())


def test_the_review_host_root_serves_the_reviewer(client):
    r = client.get("/", headers=HOST)
    assert r.status_code == 200
    assert "PANTHEON REVIEW" in r.text
    assert 'id="b1"' in r.text and 'id="v"' in r.text


def test_the_root_is_rendered_not_redirected(client):
    """A redirect would still work, but the product URL is the bare hostname
    and a JS bounce would mean shipping the legacy page first and hoping."""
    r = client.get("/", headers=HOST, follow_redirects=False)
    assert r.status_code == 200, "no redirect on the review host root"
    assert "text/html" in r.headers["content-type"]


def test_the_legacy_shell_is_never_served_on_the_review_host(client):
    body = client.get("/", headers=HOST).text.upper()
    for word in LEGACY_WORDS:
        assert word not in body, f"review host root mentions {word}"


def test_authoring_routes_are_not_reachable_on_the_review_host(client):
    """Sharing a process is not a reason to share a surface."""
    for path in ("/studio", "/creative", "/cinema", "/editor", "/annotate",
                 "/api/phase1/parts", "/api/forge/status"):
        r = client.get(path, headers=HOST)
        assert r.status_code == 404, f"{path} answered {r.status_code}"
        assert "review workstation" in r.text


def test_the_review_api_and_health_stay_open(client):
    for path in ("/api/review/progress", "/api/review/corpora", "/health"):
        assert client.get(path, headers=HOST).status_code == 200, path


def test_the_authoring_app_is_untouched_on_its_own_host(client):
    """Nothing was deleted. It simply does not belong on that hostname."""
    r = client.get("/", headers={"host": "localhost"}, follow_redirects=False)
    assert r.status_code == 307 and "/studio" in r.headers["location"]
    assert client.get("/studio", headers={"host": "localhost"}).status_code == 200


def test_the_allowlist_is_explicit():
    assert rh.is_allowed("/") and rh.is_allowed("/health")
    assert rh.is_allowed("/api/review/queue")
    for bad in ("/studio", "/api/phase1/x", "/api/forge/y", "/static/z"):
        assert not rh.is_allowed(bad), bad


# ── the reviewer itself ─────────────────────────────────────────────────────

def _page() -> str:
    return (Path(__file__).resolve().parents[1] / "frontend" / "review.html"
            ).read_text(encoding="utf-8")


def test_the_page_declares_a_mobile_viewport():
    """Without this a phone lays the page out at ~980px and scales it down,
    which is what made the review experience unusable on a phone. It was
    simply absent."""
    s = _page()
    assert 'name="viewport"' in s and "width=device-width" in s
    assert "viewport-fit=cover" in s, "needed for safe-area insets"


def test_the_five_verdicts_are_present_and_unchanged():
    s = _page()
    for role in ("T1_FEATURE_FX", "T2_TRANSITION", "T3_RHYTHM_MONTAGE",
                 "T4_KEEP_NORMAL", "T5_PASS_FILLER"):
        assert f'data-role="{role}"' in s, role


def test_the_layout_cannot_scroll_sideways():
    s = _page()
    assert "overflow-x:hidden" in s
    assert "max-width:100%" in s


def test_the_decisions_clear_the_home_indicator():
    s = _page()
    assert "safe-area-inset-bottom" in s
    assert "position:sticky;bottom:0" in s.replace(" ", "").replace("\n", "")


def test_secondary_panels_are_collapsible_and_video_is_not():
    """Filters, round and details are drawers. The video and the five
    buttons are the product and are never hidden behind a toggle."""
    s = _page()
    assert 'id="d-round"' in s and 'id="d-details"' in s
    assert 'id="togglefilters"' in s
    stage = s[s.index('<div class="stage">'):s.index('<div class="buttons">')]
    assert "<details" not in stage


def test_round_context_and_filters_survived_the_rebuild():
    s = _page()
    for hook in ('id="roundbox"', 'id="fdrawer"', 'id="f-funny"',
                 'id="usage"', 'id="filtercount"', "watchround"):
        assert hook in s, hook


def test_session_resume_survived_the_rebuild():
    s = _page()
    assert "restoreSession" in s and "saveSession" in s


def test_the_mobile_variant_is_the_same_clip_with_fewer_bits():
    """A review proxy is 1920x1080 at 8-23 Mbps -- measured mean 11.8 MiB for
    six seconds. Right for judging a frag on a desktop, punishing on a phone.
    The phone gets a smaller ENCODE: same window, same frames, same timing.

    Never a mass transcode. Most clips are never watched on a phone and
    re-encoding 33,316 to find out would cost more than it saves.
    """
    from creative_suite.api import review as rv
    import inspect
    src = inspect.getsource(rv._mobile_variant)
    # Derived from the existing proxy, not from a fresh capture and not from
    # anything in a V1 directory.
    assert "scale=-2:" in src and "libx264" in src
    assert rv.MOBILE_HEIGHT == 720
    # A failed shrink must never cost the reviewer the clip.
    assert "return None" in src
    page = _page()
    assert "?v=mobile" in page and "isSmallScreen" in page


def test_the_master_stays_the_desktop_default():
    page = _page()
    i = page.index("isSmallScreen() ?")
    assert '"?v=mobile"' in page[i:i + 120]
    assert ': ""' in page[i:i + 120], "desktop asks for the master"
