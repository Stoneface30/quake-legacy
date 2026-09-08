"""External tools live with the PROJECT, not beside the code.

CODE_ROOT   the checkout these lines were loaded from
DATA_ROOT   the checkout that owns the corpus and the databases
TOOL_ROOT   where ffmpeg, ffprobe and the game binaries actually are

The first two were reconciled when a worktree quietly created an empty
review database. The third is the same bug wearing different clothes, and
it bit in the same session: `delivered_sync` and `capture_qa` resolved
`ffmpeg.exe` beside the integration worktree, where no such file exists,
and every transient search and capture QA died on WinError 2.

THIS FILE DOES NOT FIX THE DEBT. Seventeen modules still derive a tool
path from their own location. They are listed below, classified, and frozen:
the guard's job is to keep the list from growing, so existing debt stays
visible and new debt is blocked at the door. Fixing them is a separate piece
of work with its own tests, not a side effect of an integration.
"""
from __future__ import annotations

import re
from pathlib import Path

CODE_ROOT = Path(__file__).resolve().parents[2]

TOOL = re.compile(r"ffmpeg|ffprobe|wolfcamql|UDT_json", re.I)
SHARED = ("_data_root()", "S.PROJECT_ROOT", "store.data_root")

# Frozen 2026-09-06. Every entry resolves an external tool relative to the
# file's own location instead of the shared root.
#
#   ACTIVE_PRODUCTION_PATH  runs in the app; fix first, with its own tests
#   LEGACY                  canaries, music tooling, one-shot builders
#   TEST_ONLY               only reached from a test
#   UNKNOWN                 not currently exercised by the suite
KNOWN_TOOL_DEBT = frozenset({
    # ACTIVE_PRODUCTION_PATH (4) -- fix these first, each with its own test
    "creative_suite/api/phase1.py",
    "creative_suite/engine/audio_onsets.py",
    "creative_suite/engine/event_reference.py",
    "creative_suite/engine/forensic_replay.py",
    # LEGACY (7) -- canaries, music tooling, one-shot builders
    "creative_suite/engine/canaries/v2_cadence.py",
    "creative_suite/engine/music/audit_library.py",
    "creative_suite/engine/music/bulk_sc.py",
    "creative_suite/engine/music/bulk_spotdl.py",
    "creative_suite/engine/music/download_library.py",
    "creative_suite/engine/music/rotate_fresh_stems.py",
    "creative_suite/engine/scrub_normalize_cache.py",
    # TEST_ONLY (4)
    "creative_suite/engine/tests/test_template_matching.py",
    "creative_suite/tests/test_effect_templates.py",
    "creative_suite/tests/test_forensic_replay.py",
    "creative_suite/tests/test_prologue_proof.py",
    # UNKNOWN (1) -- not exercised by the suite today
    "creative_suite/prologue/build_proof.py",
    # engine/pantheon/voice.py left this list on 2026-09-08: it now resolves
    # ffmpeg through store.PROJECT_ROOT rather than counting parents from its
    # own file. The list is asserted not to rot precisely so that a fix shows
    # up as a number going down instead of as nothing at all.
})


def _offenders() -> set[str]:
    out: set[str] = set()
    for base in ("creative_suite", "engine"):
        root = CODE_ROOT / base
        if not root.is_dir():
            continue
        for p in root.rglob("*.py"):
            if "__pycache__" in p.parts:
                continue
            try:
                t = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if "Path(__file__).resolve().parents[" not in t:
                continue
            if any(s in t for s in SHARED):
                continue
            if not any(TOOL.search(l) and ("ROOT" in l or "tools" in l)
                       for l in t.splitlines()):
                continue
            out.add(str(p.relative_to(CODE_ROOT)).replace("\\", "/"))
    return out


def test_no_new_module_finds_its_tools_beside_the_code():
    """The guard. Existing debt is listed; anything NEW fails here.

    If you are reading this because your file is in the failure, use
    `engine.pantheon.store.data_root()` rather than
    `Path(__file__).resolve().parents[n]` -- the tools live with the
    project, and a worktree is a different checkout.
    """
    new = sorted(_offenders() - KNOWN_TOOL_DEBT)
    assert not new, (
        "these resolve an external tool from the code root:\n  "
        + "\n  ".join(new))


def test_the_debt_list_does_not_rot():
    """An entry that has been fixed should leave the list, so the number
    means something."""
    stale = sorted(KNOWN_TOOL_DEBT - _offenders())
    assert not stale, (
        "these are listed as tool-path debt but no longer are; remove them "
        "from KNOWN_TOOL_DEBT:\n  " + "\n  ".join(stale))


def test_the_review_capture_path_is_already_clean():
    """The modules this integration actually renders through. They were the
    two that failed, and they are the two that matter today."""
    from creative_suite.engine import review_proxy, wolfcam_capture
    from creative_suite.engine import capture_qa, delivered_sync
    from engine.pantheon import store
    for m in (review_proxy, wolfcam_capture, capture_qa, delivered_sync):
        assert Path(m.REPO_ROOT) == store.data_root(), \
            f"{m.__name__} resolves {m.REPO_ROOT}"
