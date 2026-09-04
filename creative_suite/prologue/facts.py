"""Every number the prologue puts on screen, re-derived from the live caches.

WHY THIS EXISTS. The prologue makes factual claims to an audience: how many
demos, how many rounds, how many hours. The brief arrived carrying a figure
("~452 hours") that no longer had a derivation behind it, and a rounds total
that was inflated by a broken counter in 26 demos. Both would have been
printed in 60-point type over a montage.

So the rule is: a figure appears on screen only if this module can derive it
today. `verify()` re-runs every derivation and reports drift against what the
ledger says. Copy is locked against this, not against a memory of it.

Read-only throughout. This module never writes to a cache.
"""
from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[2]

# The caches are 10 GB and live once, in the main checkout. This workstream
# runs in its own worktree so it cannot collide with human review, and reads
# those caches across the worktree boundary rather than copying them.
DB_ROOT = Path(os.environ.get("QL_DB_ROOT", REPO_ROOT / "creative_suite/database"))
RECOGNITION_DB = DB_ROOT / "frag_recognition.db"
REBUILT_DB = DB_ROOT / "frags_rebuilt.db"

# Provenance for anything generated to teach a rule. It is deliberately NOT a
# corpus name: synthetic material must never be countable as career history.
SYNTHETIC_EXPLAINER = "SYNTHETIC_EXPLAINER"

# Demos whose round counter is not believable. A Clan Arena demo has a median
# of 25 rounds; these run to 10,599. They are not excluded from the archive --
# only from any ROUND total shown to an audience.
ROUND_COUNTER_SANE_MAX = 200


def _ro(path: Path) -> sqlite3.Connection:
    if not path.exists():                       # pragma: no cover - env guard
        raise FileNotFoundError(f"cache not present: {path}")
    return sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)


@dataclass(frozen=True)
class Fact:
    """One claim, with the derivation that pays for it."""
    key: str
    value: int | float
    derivation: str
    on_screen: str | None      # exact permitted wording, None = never shown
    note: str = ""


# ── derivations ─────────────────────────────────────────────────────────────
# Each returns the measured value. Kept separate from the ledger so a drifting
# number is visible as drift rather than being silently absorbed.

def demos_scanned() -> int:
    with _ro(RECOGNITION_DB) as c:
        return c.execute("select count(*) from scanned_demos").fetchone()[0]


def clan_arena_demos() -> int:
    with _ro(REBUILT_DB) as c:
        return c.execute(
            "select count(*) from demos where gametype='CA'").fetchone()[0]


def maps_recorded() -> int:
    with _ro(REBUILT_DB) as c:
        return c.execute(
            "select count(distinct map_name) from demos").fetchone()[0]


def canonical_rounds() -> int:
    """Rounds that actually contain a kill, from the V2 derivation.

    NOT `sum(demos.rounds)`. That column sums to 138,301 because 26 demos
    carry a runaway counter; this is the count the audience is shown.
    """
    with _ro(RECOGNITION_DB) as c:
        return c.execute("select count(*) from round_kills_v1").fetchone()[0]


def recording_hours() -> float:
    """A LOWER BOUND on hours recorded: per demo, first kill to last.

    Warmup, the run-up to the first kill and the tail after the last are all
    outside this span, so the true figure is larger. Shown as "over 450",
    never as an exact number, because an exact number would be wrong.
    """
    with _ro(RECOGNITION_DB) as c:
        rows = c.execute(
            "select max(demo_us) - min(demo_us) from kill_events_v1 "
            "where demo_us is not null group by content_hash").fetchall()
    return sum(r[0] for r in rows if r[0] and r[0] > 0) / 3.6e9


def _corpus(name: str) -> int:
    """A corpus total, straight from the code the review workstation uses.

    `review_corpus` resolves its own caches relative to its checkout. This
    workstream lives in a separate worktree, so when QL_DB_ROOT points
    elsewhere the module is redirected at import time -- reading the same
    caches the user is reviewing against, never a stale copy of them.
    """
    from creative_suite.engine import identity as idn
    from creative_suite.engine import review_corpus as rc
    for mod in (rc, idn):
        if getattr(mod, "RECOGNITION_DB", DB_ROOT).parent != DB_ROOT:
            mod.RECOGNITION_DB = RECOGNITION_DB
            mod.EDITORIAL_DB = DB_ROOT / "editorial.db"
    return int(rc.corpus_status(name)["total"])


def user_frags() -> int:
    return _corpus("USER_FRAGS")


def all_player_kills() -> int:
    return _corpus("ALL_PLAYERS")


def ptn_frags() -> int:
    return _corpus("PTN_FRAGS")


# ── the ledger ──────────────────────────────────────────────────────────────
# `on_screen` is the ONLY permitted wording. "36,607 frags" has no wording
# because that set means "the killer recorded this demo" -- it is somebody
# else's kill often enough that showing it as the user's would be a lie.

LEDGER: tuple[tuple[str, Callable[[], Any], int | float, str | None, str], ...] = (
    ("demos_scanned", demos_scanned, 4292, "4,292 DEMOS",
     "one demo may span several matches -- never call these 'matches'"),
    ("clan_arena_demos", clan_arena_demos, 4222, "98% CLAN ARENA",
     "4,222 of 4,292; the archive is a Clan Arena archive"),
    ("maps_recorded", maps_recorded, 61, "61 MAPS",
     "distinct map_name; only 58 carry a canonical kill"),
    ("canonical_rounds", canonical_rounds, 78730, "78,730 ROUNDS",
     "round_kills_v1; NOT sum(demos.rounds)=138,301 which is counter-inflated"),
    ("recording_hours", recording_hours, 453.1, "OVER 450 HOURS",
     "lower bound: first kill to last, per demo"),
    ("user_frags", user_frags, 33316, "33,316 CONFIRMED USER FRAGS",
     "killer is a confirmed user identity; grows as aliases are confirmed"),
    ("all_player_kills", all_player_kills, 203536, "203,536 PLAYER KILLS",
     "every player-vs-player canonical kill -- NOT the user's own"),
    ("ptn_frags", ptn_frags, 14212, "14,212 CLAN FRAGS",
     "confirmed clan identities, excluding the user"),
)

# Counts that legitimately grow as the user confirms identities and review
# continues. Drift upward is expected; drift downward means something broke.
MAY_GROW = {"user_frags", "ptn_frags", "canonical_rounds"}


def verify(tolerance: float = 0.02) -> list[dict[str, Any]]:
    """Re-derive every ledger figure and report drift.

    Returns one row per fact. `ok` is False when a figure moved enough that
    the on-screen copy would now be wrong.
    """
    out: list[dict[str, Any]] = []
    for key, fn, expected, on_screen, note in LEDGER:
        try:
            actual = fn()
        except Exception as exc:                # pragma: no cover - env guard
            out.append({"key": key, "ok": False, "expected": expected,
                        "actual": None, "error": f"{type(exc).__name__}: {exc}",
                        "on_screen": on_screen, "note": note})
            continue
        drift = abs(actual - expected) / expected if expected else 0.0
        ok = drift <= tolerance
        if not ok and key in MAY_GROW and actual > expected:
            ok = True                            # growth is the healthy direction
        out.append({"key": key, "ok": ok, "expected": expected,
                    "actual": actual, "drift": round(drift, 4),
                    "on_screen": on_screen, "note": note})
    return out


def screen_copy() -> dict[str, str]:
    """The only wordings permitted on screen, keyed by fact."""
    return {k: s for k, _, _, s, _ in LEDGER if s}


if __name__ == "__main__":                      # pragma: no cover - CLI
    rows = verify()
    width = max(len(r["key"]) for r in rows)
    for r in rows:
        mark = "OK  " if r["ok"] else "DRIFT"
        print(f"{mark} {r['key']:<{width}}  expected={r['expected']!r:>10} "
              f"actual={r['actual']!r:>10}  \"{r['on_screen']}\"")
    bad = [r for r in rows if not r["ok"]]
    print(f"\n{len(rows) - len(bad)}/{len(rows)} facts verified")
    raise SystemExit(1 if bad else 0)
