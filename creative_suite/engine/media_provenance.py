"""Where V2 media is allowed to come from, enforced rather than assumed.

V1 IS CLOSED. Its rendered output stays on disk as reference history and must
never enter a V2 review queue or production pass. The distinction is not
aesthetic: a V1 render is a finished editorial decision -- trimmed, graded,
speed-ramped, cut to music that is no longer the plan. Reviewing one and
calling it a moment would be judging an old edit and recording the verdict
against a canonical occurrence.

WHAT IS AUTHORITATIVE. Media reaches V2 by capturing from a raw demo, or from
something deterministically derived from one:

    demos/*.dm_73  ->  current capture              RAW_DEMO_CAPTURE
    demos/*.dm_73  ->  derived round  ->  capture   DERIVED_ROUND_CAPTURE
    cached game truth  ->  reconstruction           RECONSTRUCTED_CURRENT
    authored, from game truth                       SYNTHETIC_CURRENT

There is deliberately no constant for a V1 render. A source that cannot be
labelled with one of the above is not eligible, and `V1_RENDER_SOURCE` exists
here only as the name of a refusal.

THE AUDIT THAT PROMPTED THIS FOUND NOTHING WRONG. Every one of 4,292 demo
rows points inside demos/ and ends .dm_73; all 63 cached proxies were built
from one; no module on the media path references a V1 directory, and there is
no glob or fallback that could wander into one. That is the state today, and
`demo_source()` still returns whatever path a database row happens to hold --
so the invariant is now checked at the moment of use rather than left to
remain true by luck.
"""
from __future__ import annotations

from pathlib import Path

# DATA, not code: under a worktree these differ, and opening a
# database beneath the wrong one silently CREATES an empty file
# rather than failing. See engine.pantheon.store.
from engine.pantheon.store import data_root as _data_root
REPO_ROOT = _data_root()

# Provenance labels. Every active media asset carries one of these.
RAW_DEMO_CAPTURE = "RAW_DEMO_CAPTURE"
DERIVED_ROUND_CAPTURE = "DERIVED_ROUND_CAPTURE"
RECONSTRUCTED_CURRENT = "RECONSTRUCTED_CURRENT"
SYNTHETIC_CURRENT = "SYNTHETIC_CURRENT"

# A re-encode of a V2 capture for delivery -- the 720p variant a phone gets.
# Same window, same frames, same timing, fewer bits. It is NOT a capture, and
# labelling it RAW_DEMO_CAPTURE would let a lossy delivery copy be mistaken
# for the master later, when something wants the best available pixels.
V2_REVIEW_DELIVERY_DERIVATIVE = "V2_REVIEW_DELIVERY_DERIVATIVE"

AUTHORITATIVE = (RAW_DEMO_CAPTURE, DERIVED_ROUND_CAPTURE,
                 RECONSTRUCTED_CURRENT, SYNTHETIC_CURRENT,
                 V2_REVIEW_DELIVERY_DERIVATIVE)

# Which of those may be treated as the best available pixels for production.
# The delivery derivative may not: it is for looking at, not for cutting.
MASTER_GRADE = (RAW_DEMO_CAPTURE, DERIVED_ROUND_CAPTURE,
                RECONSTRUCTED_CURRENT, SYNTHETIC_CURRENT)

# Not a provenance a V2 asset may hold. Named so a refusal can say what it
# refused.
V1_RENDER_SOURCE = "V1_RENDER_SOURCE"

# V1 and archive rendered media. Historical, readable, never a V2 source.
#
# `output/` is the awkward one: it holds the V1 Part renders at its root AND
# the V2 proxy cache underneath it, so the rule cannot be "output is legacy".
# The exception below is what makes the split exact.
LEGACY_MEDIA_ROOTS = (
    REPO_ROOT / "QUAKE VIDEO",          # T1/T2/T3 source AVIs for the V1 cut
    REPO_ROOT / "FRAGMOVIE VIDEOS",     # V1 intro / delivered movies
    REPO_ROOT / "output",               # V1 Part renders -- see the exception
)
LEGACY_EXCEPTIONS = (
    REPO_ROOT / "output" / "demo_v2",   # the V2 capture and proxy cache
)

# Where a V2 media source may legitimately live.
SOURCE_ROOTS = (
    REPO_ROOT / "demos",                # the raw corpus
    REPO_ROOT / "output" / "demo_v2",   # derived and captured V2 assets
    REPO_ROOT / "exchange",             # what has been exported
)

DEMO_SUFFIX = ".dm_73"


class LegacySourceRefused(Exception):
    """A V2 media lookup resolved inside V1 or archive rendered output."""


def _under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except (ValueError, OSError):
        return False


def is_legacy(path: str | Path) -> bool:
    """True when this path is V1 or archive rendered media."""
    p = Path(path)
    if any(_under(p, ex) for ex in LEGACY_EXCEPTIONS):
        return False
    return any(_under(p, r) for r in LEGACY_MEDIA_ROOTS)


def is_authoritative_source(path: str | Path) -> bool:
    """True when this path may be used as a V2 media source."""
    p = Path(path)
    return not is_legacy(p) and any(_under(p, r) for r in SOURCE_ROOTS)


def assert_demo_source(path: str | Path, what: str = "media source") -> Path:
    """Refuse anything that is not a raw demo in the corpus.

    Called where a stored path is turned into a capture. `demo_source()`
    returns whatever a database row holds, and a row is not a guarantee.
    """
    p = Path(path)
    if is_legacy(p):
        raise LegacySourceRefused(
            f"{what} resolved inside V1/archive rendered output: {p.name}. "
            f"V1 is reference history; V2 media comes from a raw demo. "
            f"({V1_RENDER_SOURCE} is not an eligible provenance)")
    if p.suffix.lower() != DEMO_SUFFIX:
        raise LegacySourceRefused(
            f"{what} is not a raw demo: {p.name} (expected {DEMO_SUFFIX})")
    # Containment, but only where it protects something.
    #
    # An earlier version demanded every source sit under demos/. That is
    # stricter than the invariant and it refused two legitimate cases: the
    # V2 wolfcam staging area, which holds 83 real .dm_73 copies under
    # output/demo_v2/, and test fixtures outside the repo entirely. Neither
    # is V1 -- V1 has ZERO .dm_73 files anywhere, so the suffix check plus
    # the legacy-root check already carry the whole rule.
    #
    # What remains is the case worth refusing: a demo sitting somewhere else
    # INSIDE the repository, which is either a stray copy or a path nobody
    # meant to capture from.
    if _under(p, REPO_ROOT) and not any(_under(p, r) for r in SOURCE_ROOTS):
        raise LegacySourceRefused(
            f"{what} is inside the repository but outside the demo corpus "
            f"and the V2 staging area: {p.name}")
    return p


def audit() -> dict[str, object]:
    """What the invariant currently covers. Paths only, no media is opened."""
    return {
        "legacy_roots": [str(r) for r in LEGACY_MEDIA_ROOTS],
        "legacy_exceptions": [str(r) for r in LEGACY_EXCEPTIONS],
        "source_roots": [str(r) for r in SOURCE_ROOTS],
        "authoritative_provenance": list(AUTHORITATIVE),
        "refused_provenance": V1_RENDER_SOURCE,
        "rule": ("a V2 media source is a raw demo in demos/, or something "
                 "deterministically derived from one and captured now"),
    }
