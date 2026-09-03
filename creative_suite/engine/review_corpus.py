"""The whole career, reviewable. The machine organises; the user decides.

WHY THIS EXISTS. There is no shortage of information any more -- 4,292
demos, 36,607 canonical frags, 34.3M semantic events. What was missing is a
way to sit down and go through it. This is that: one item at a time, five
buttons, one answer, an optional note, and the next one starts playing.

THREE RULES THE CODE ENFORCES.

Nothing is hidden. A machine score is an ORDER, never a filter. The
lowest-scoring frag in the corpus is as reachable as the highest, because
the machine does not know why a moment is good -- it knows how it looked to
a scorer written months ago.

Nothing is thrown away. PASS means "not wanted as primary gameplay
material", and a passed moment stays in the corpus for the two-frame flash,
the background plate, the death motif, the thing nobody thought of yet.

Reviewed is not consumed. A verdict says what a moment is FOR. It does not
spend it. Consumption still happens only when a moment is placed in an
actual production under the existing no-reuse rules.

GENERIC BY CONSTRUCTION. A frag is one item type. A telefrag, a jump-pad
dodge, a death, a teleport and a movement moment are others, and every one
of them gets the same five questions, because the system already knows WHAT
the event is. What it cannot know is what the event is FOR.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
RECOGNITION_DB = REPO_ROOT / "creative_suite/database/frag_recognition.db"
EDITORIAL_DB = REPO_ROOT / "creative_suite/database/editorial.db"

REVIEW_VERSION = "review-corpus-v1"

# ── who wrote this verdict ──────────────────────────────────────────────────
# A creative judgement is the user's and nobody else's. Automated tests drove
# the live UI during implementation and wrote rows that were indistinguishable
# from real review; that must never be possible again. Only the first two
# count towards reviewed totals, human pools, or anything the composer
# prefers.
HUMAN_USER = "HUMAN_USER"
IMPORTED_LEGACY_HUMAN = "IMPORTED_LEGACY_HUMAN"
TEST = "TEST"
SYSTEM = "SYSTEM"
AI_SUGGESTION = "AI_SUGGESTION"
PROVENANCES = (HUMAN_USER, IMPORTED_LEGACY_HUMAN, TEST, SYSTEM, AI_SUGGESTION)
HUMAN_PROVENANCE = (HUMAN_USER, IMPORTED_LEGACY_HUMAN)

# ── the five roles ──────────────────────────────────────────────────────────
# One click, one answer. Not a tag cloud: the machine already knows what the
# event IS, and the only thing it cannot infer is what the event is FOR.

T1_FEATURE_FX = "T1_FEATURE_FX"          # deserves special treatment
T2_TRANSITION = "T2_TRANSITION"          # connects scenes
T3_RHYTHM_MONTAGE = "T3_RHYTHM_MONTAGE"  # belongs in a repeated sequence
T4_KEEP_NORMAL = "T4_KEEP_NORMAL"        # good, plain gameplay
T5_PASS_FILLER = "T5_PASS_FILLER"        # not primary -- and never deleted
ROLES = (T1_FEATURE_FX, T2_TRANSITION, T3_RHYTHM_MONTAGE, T4_KEEP_NORMAL,
         T5_PASS_FILLER)

ROLE_LABEL = {
    T1_FEATURE_FX: "FEATURE / FX",
    T2_TRANSITION: "TRANSITION",
    T3_RHYTHM_MONTAGE: "RHYTHM / MONTAGE",
    T4_KEEP_NORMAL: "KEEP / NORMAL",
    T5_PASS_FILLER: "PASS / FILLER",
}
ROLE_HINT = {
    T1_FEATURE_FX: "hero shot, cinematic replay, big effect",
    T2_TRANSITION: "teleport, flyby, death, jump, weapon switch",
    T3_RHYTHM_MONTAGE: "one of many, cut to the music",
    T4_KEEP_NORMAL: "clean gameplay, no special treatment",
    T5_PASS_FILLER: "kept forever: flashes, plates, motifs",
}
ROLE_BY_KEY = {str(i + 1): r for i, r in enumerate(ROLES)}

# ── item types ──────────────────────────────────────────────────────────────
# Only families that exist in the caches today. Inventing a type to pad the
# list would put the user in front of an empty queue.

# FRAG is the historical archive family: `recognized_frags`, built on "the
# killer recorded this demo". It is kept for provenance and is NOT the user's
# frags -- see RECORDER_OWN_ARCHIVE below.
FRAG = "FRAG"
TELEFRAG = "TELEFRAG"
DEATH = "DEATH"
USER_FRAG = "USER_FRAG"
CLAN_FRAG = "CLAN_FRAG"
ALL_KILL = "ALL_KILL"
TELEPORT = "TELEPORT"
DODGE = "DODGE"
LG_TRACKING = "LG_TRACKING"
PROJECTILE = "PROJECTILE"
ITEM_TYPES = (USER_FRAG, FRAG, TELEFRAG, DEATH, CLAN_FRAG, ALL_KILL,
              TELEPORT, DODGE, LG_TRACKING, PROJECTILE)

# Families served by the CANONICAL OCCURRENCE layer rather than by raw
# observations. A kill happened once; several demos may have recorded it. One
# historical frag gets one review, shown through its best observation, and
# the alternatives stay available.
KILL_BACKED = (USER_FRAG, DEATH, CLAN_FRAG, ALL_KILL)

# The teleport queue reads its own cache. Only the recorder's OWN transits,
# and only the ones the attribution actually confirmed -- an UNKNOWN or
# AMBIGUOUS outcome is a transit we could not attribute, and putting it in
# front of the user as "your teleport" would be asserting what the
# attribution declined to.
TELEPORT_CONFIRMED = "TELEPORT_PLAYER_CONFIRMED"

# Why a family is not offered as a review queue. A machine feature is not a
# review moment, and the difference is not visible from the row count.
#
# DODGE looked ready: 36,586 rows against 36,607 frags is close enough to
# assume one per frag. It is a coincidence. The rows carry `kill_anchor_ms`,
# and they collapse to 19,877 distinct anchors -- every one of which matches
# an existing recognized_frags row exactly, up to eight rows per frag. So a
# dodge row is a near-miss THREAT measured on the way into a kill the user
# already has in MY_FRAGS, not an independent moment. `survived` is 1 on all
# 36,586 rows, so the table has no contrast case either: it only ever
# recorded threats that missed.
#
# Reviewing it as 36,586 clips would show the same frag up to eight times and
# call each showing a different moment.
NOT_A_REVIEW_MOMENT = {
    DODGE: ("a per-frag feature, not a moment: 36,586 rows collapse to "
            "19,877 kill anchors, all of which are frags already reviewable "
            "in MY_FRAGS, up to 8 rows per frag, and survived=1 on every row"),
}

# The review window. Three seconds of run-up, the moment, three seconds of
# consequence -- clamped honestly at the recording's own edges rather than
# padded with something that was never recorded.
PRE_MS = 3000
POST_MS = 3000

# MOD_TELEFRAG. Read off the vendored enum (bg_public.h: MOD_UNKNOWN=0 ..
# MOD_CRUSH=17, MOD_TELEFRAG=18), not assumed -- an earlier query used 12,
# which is MOD_BFG, and returned zero.
MOD_TELEFRAG = 18

# ── corpora ─────────────────────────────────────────────────────────────────
# A corpus is WHOSE moments are reviewed. Separate from item type, which is
# WHAT happened.
#
# MY_FRAGS is the recorder's own kills -- the only killer-attributed set the
# caches hold.
#
# PTN_FRAGS is unavailable, and the reason is specific rather than a shrug.
# It needs a killer for every kill, and the cached `death` events do not
# carry one: victim and weapon are NULL across all 133,279 rows, leaving
# only the dying entity and the means of death. Killer attribution lives in
# EV_OBITUARY's otherEntityNum2, which the enrichment read and never
# persisted. Until a derivation pass writes it, a pTn corpus could only be
# guessed, and a guess about who killed whom is exactly what this project
# does not do.
# WHOSE moments. The names are exact on purpose: three different datasets
# were previously all called "my frags", and the user was about to spend
# hours curating one of them under a label that did not describe it.
#
# USER_FRAGS       killer is a CONFIRMED USER identity. The default.
# RECORDER_OWN_ARCHIVE  the historical `recognized_frags` set, built on
#                  "killer recorded this demo". Preserved, never deleted,
#                  and no longer presented as the user's own.
# PTN_FRAGS        killer is a CONFIRMED clan member, excluding the user.
# USER_AND_PTN     union by canonical occurrence, so a frag that is both
#                  appears once.
# ALL_PLAYERS      every canonical player-kill occurrence.
USER_FRAGS = "USER_FRAGS"
RECORDER_OWN_ARCHIVE = "RECORDER_OWN_ARCHIVE"
PTN_FRAGS = "PTN_FRAGS"
USER_AND_PTN = "USER_AND_PTN"
ALL_PLAYERS = "ALL_PLAYERS"
CORPORA = (USER_FRAGS, RECORDER_OWN_ARCHIVE, PTN_FRAGS, USER_AND_PTN,
           ALL_PLAYERS)

# The old names, kept so nothing that referenced them breaks silently. They
# are deliberately not in CORPORA: "MY_FRAGS" was the misnomer.
MY_FRAGS = RECORDER_OWN_ARCHIVE
MY_AND_PTN = USER_AND_PTN

# ── the pTn clan tag ────────────────────────────────────────────────────────
# The tag is NOT part of a player name. It is set with /clan and the server
# prepends it to connect and chat lines, which is why player_names_v1 never
# had it: the parser reads only the `n` key from the player configstring.
#
# Observed spelling, from 45,551 cached text lines:
#
#     ^4pTn^3.        29,530 lines
#     ^4pTn^3.^7      15,944 lines   (^7 begins the name)
#
# Colour codes verified against the vendored table (q_shared.h:468-475,
# g_color_table in q_math.c), which has eight entries and no extension:
#
#     ^4 = COLOR_BLUE    3266fe     "pTn"
#     ^3 = COLOR_YELLOW  fefe00     the dot
#     ^2 = COLOR_GREEN   00fe00     -- green, not gold
#
# So blue pTn, yellow dot, as the user described. ^2 would have been green.
PTN_TAG = chr(94) + "4pTn" + chr(94) + "3."
PTN_TAG_COLOURS = {"pTn": ("^4", "COLOR_BLUE", "3266fe"),
                   ".": ("^3", "COLOR_YELLOW", "fefe00")}

# How a name got onto the roster. Membership is evidence or the user's word,
# never a string match on "pTn" appearing somewhere.
TAG_OBSERVED = "TAG_OBSERVED"          # seen wearing the tag in cached text
USER_DECLARED = "USER_DECLARED"        # the user says so; tag evidence may
                                       # be absent for good reasons -- joining
                                       # late, or playing untagged
ALIAS_CANDIDATE = "CLAN_ALIAS_CANDIDATE"   # wears the tag, not yet confirmed

# Line counts are how often the name was seen next to the tag in
# server_text_v1 -- connect messages and chat prefixes.
PTN_ROSTER: dict[str, dict[str, Any]] = {
    "Tr4sH": {"basis": TAG_OBSERVED, "tag_lines": 15940,
              "note": "the recorder"},
    "NaikoMarie": {"basis": TAG_OBSERVED, "tag_lines": 4248,
                   "names": ("NaikoMarie", "naikomarie")},
    "jibyjibs": {"basis": TAG_OBSERVED, "tag_lines": 1279,
                 "names": ("jibyjibs", "^7jib^1y^7jib^1s^7")},
    "S73rn": {"basis": TAG_OBSERVED, "tag_lines": 329,
              "names": ("s73rn", "^7s73rN", "^7s^47^73r^4N^7"),
              "note": "S7ern not present as its own spelling"},
    "sereke": {"basis": TAG_OBSERVED, "tag_lines": 49,
               "names": ("sereke", "^7sere^4k^7e")},
    # b3nto is a real player -- 218 rows in player_names_v1 and 4,174 text
    # lines -- and appears in ZERO pTn-tagged lines. Per the user: he joined
    # later and sometimes played without the tag. So the absence of tag
    # evidence is explained rather than suspicious, and the membership rests
    # on the user's word, which is labelled as such rather than dressed up
    # as evidence it does not have.
    "b3nto": {"basis": USER_DECLARED, "tag_lines": 0,
              "names": ("b3nto",),
              "note": "joined later and sometimes played untagged, per the "
                      "user; real player, no tag lines in cache"},
}

# Wearing the tag but not on the user's list. Surfaced for a decision, never
# added: a tag is a costume, and this project does not merge human
# identities on its own.
PTN_ALIAS_CANDIDATES: dict[str, dict[str, Any]] = {
    "Xhipper": {"basis": ALIAS_CANDIDATE, "tag_lines": 1421},
    "rctmyouen": {"basis": ALIAS_CANDIDATE, "tag_lines": 842},
    "Kabuu": {"basis": ALIAS_CANDIDATE, "tag_lines": 279},
}


# The corpus a review queue is drawn from, expressed as the item type that
# serves it. MY_FRAGS keeps the recognized_frags path: it is scored, ranked,
# and the user is already reviewing it.
CORPUS_ITEM_TYPE = {
    USER_FRAGS: USER_FRAG,
    RECORDER_OWN_ARCHIVE: FRAG,
    PTN_FRAGS: CLAN_FRAG,
    USER_AND_PTN: ALL_KILL,    # narrowed to user + roster in the SQL
    ALL_PLAYERS: ALL_KILL,
}

# What the user is actually looking at, in words, so a denominator is never
# ambiguous.
CORPUS_LABEL = {
    USER_FRAGS: "CONFIRMED USER FRAGS",
    RECORDER_OWN_ARCHIVE: "RECORDER-OWN ARCHIVE FRAGS",
    PTN_FRAGS: "pTn CONFIRMED-MEMBER FRAGS",
    USER_AND_PTN: "USER + pTn (unique occurrences)",
    ALL_PLAYERS: "ALL CANONICAL PLAYER KILLS",
}

DEFAULT_CORPUS = USER_FRAGS


# The user's own recorder identity. Only what is certain: "Tr4sH" wears the
# clan tag on 15,940 cached text lines and records 3,825 of the 3,997 demos
# that contain a recorder kill.
#
# The corpus is NOT all the user's demos. 172 demos were recorded by someone
# else -- clanmates and opponents whose demos are in the archive -- and their
# kills therefore appear as "the recorder's own". "stoneface" (20 demos) is
# very probably the user under another handle, but probably is not a basis
# for merging a human identity, so it is surfaced as a candidate and left
# for the user to confirm or reject.
USER_RECORDER_NAMES = ("tr4sh",)
USER_RECORDER_CANDIDATES = ("stoneface", ". stoneface")


def recorder_identity_spread(limit: int = 20) -> dict[str, Any]:
    """Who actually recorded the demos behind MY_FRAGS.

    `is_recorder_killer` means the killer recorded THIS demo, which is the
    user for 94.8% of the corpus and somebody else for the rest. Reporting
    that is the difference between "your frags" and "frags from whoever held
    the camera".
    """
    if not _kill_table_exists():
        return {"available": False}
    with _rec() as c:
        rows = c.execute(
            "SELECT killer_name_norm n, COUNT(DISTINCT content_hash) demos, "
            "COUNT(*) kills FROM kill_events_v1 WHERE is_recorder_killer=1 "
            "GROUP BY 1 ORDER BY demos DESC LIMIT ?", (limit,)).fetchall()
        total = int(c.execute("SELECT COUNT(*) FROM kill_events_v1 "
                              "WHERE is_recorder_killer=1").fetchone()[0])
        marks = ",".join("?" * len(USER_RECORDER_NAMES))
        mine = int(c.execute(
            f"SELECT COUNT(*) FROM kill_events_v1 WHERE is_recorder_killer=1 "
            f"AND killer_name_norm IN ({marks})",
            USER_RECORDER_NAMES).fetchone()[0])
        n_ident = int(c.execute(
            "SELECT COUNT(DISTINCT killer_name_norm) FROM kill_events_v1 "
            "WHERE is_recorder_killer=1").fetchone()[0])
    return {
        "available": True, "total_recorder_kills": total,
        "confirmed_user": mine, "not_the_user": total - mine,
        "distinct_recorder_identities": n_ident,
        "top": [{"name": r["n"], "demos": r["demos"], "kills": r["kills"]}
                for r in rows],
        "candidates": list(USER_RECORDER_CANDIDATES),
        "meaning": ("is_recorder_killer means the killer recorded THAT demo. "
                    "The archive holds demos recorded by other people, so a "
                    "slice of MY_FRAGS is somebody else's kill in their own "
                    "demo. Narrowing it needs the user to confirm which "
                    "recorder identities are theirs -- not a string match"),
    }


def corpus_status(corpus: str) -> dict[str, Any]:
    """Whether a corpus can be reviewed, and if not, exactly what is missing."""
    if corpus == RECORDER_OWN_ARCHIVE:
        return {"corpus": corpus, "label": CORPUS_LABEL[corpus],
                "available": True, "total": count_items(FRAG),
                "item_type": FRAG, "scored": True,
                "note": ("the historical archive set, built on 'the killer "
                         "recorded this demo'. Kept for provenance. This is "
                         "NOT the user's own frags -- see USER_FRAGS"),
                "recorder_identity": recorder_identity_spread(limit=8)}
    if corpus == USER_FRAGS:
        total = count_items(USER_FRAG)
        from creative_suite.engine import identity as idn
        st = idn.status()
        out = {"corpus": corpus, "label": CORPUS_LABEL[corpus],
               "item_type": USER_FRAG, "available": total > 0, "total": total,
               "confirmed_identities": st["user_confirmed"],
               "unanswered_recorder_identities": st["unanswered"],
               "scoring": ("machine scores exist only where the actor IS the "
                           "recorder. Foreign-camera frags are unscored, not "
                           "scored zero, and the two are not comparable"),
               "note": ("canonical occurrences whose killer is a CONFIRMED "
                        "user identity. Grows as the user confirms aliases; "
                        "nothing is merged on resemblance")}
        if total == 0:
            out["blocked_by"] = ("no confirmed user identity has any "
                                 "attributed kill")
        return out
    if corpus in (PTN_FRAGS, USER_AND_PTN, ALL_PLAYERS):
        it = CORPUS_ITEM_TYPE[corpus]
        total = count_items(it, corpus=corpus)
        out = {
            "corpus": corpus, "label": CORPUS_LABEL[corpus],
            "item_type": it, "available": total > 0, "total": total,
            "roster": PTN_ROSTER,
            "alias_candidates": PTN_ALIAS_CANDIDATES,
            "tag": PTN_TAG, "tag_colours": PTN_TAG_COLOURS,
            "clan_membership": ("recoverable from server_text_v1: 45,551 "
                                "lines carry the tag and connect messages "
                                "bind it to a name. It is NOT in "
                                "player_names_v1, because the parser reads "
                                "only the `n` configstring key"),
            # Said plainly rather than left for the user to discover: a frag
            # by somebody else, seen from this recorder's camera, cannot
            # carry the recogniser's score. Every feature behind that score
            # -- aim, tracking, movement, visibility -- is computed from the
            # recorder's own player state, which is not the actor's.
            "scoring": ("machine scores exist only where the actor IS the "
                        "recorder. Foreign-camera frags are unscored, not "
                        "scored zero, and the two are not comparable"),
        }
        if total == 0:
            out["blocked_by"] = ("kill_events_v1 is empty or not yet derived; "
                                 "run engine/parser/derive_kill_events.py")
        return out
    return {"corpus": corpus, "available": False, "total": 0,
            "blocked_by": "unknown corpus"}


# ── kill-event-backed families ──────────────────────────────────────────────
# Every roster spelling, normalized the same way the derivation normalized
# the killer name. Matching is on this set and nothing else -- never on the
# substring "pTn", which is a costume anyone can wear.

def roster_norms() -> set[str]:
    """CONFIRMED clan identities, from the identity store.

    Not a string match on "pTn", and not everything the tag evidence turned
    up. Membership is the user's answer; candidates are surfaced separately
    by `identity.ptn_candidates()` and are not in here.
    """
    from creative_suite.engine import identity as idn
    return idn.confirmed_ptn_identities()


def user_norms() -> set[str]:
    """CONFIRMED user identities. Starts as the one the project asserts."""
    from creative_suite.engine import identity as idn
    return idn.confirmed_user_identities()


import re as _re                                                # noqa: E402
# One authority for what a colour code is: caret plus ONE DIGIT.
from creative_suite.engine.quake_names import COLOR_CODE as _COLOR_RE


def _strip_colors(name: str) -> str:
    return _COLOR_RE.sub("", name or "")


def _in(names: set[str]) -> tuple[str, list[Any]]:
    ns = sorted(names)
    if not ns:
        # An empty confirmed set must select NOTHING, not everything. An
        # unanswered identity question is not permission to guess. `IN (NULL)`
        # is valid SQL that matches no row -- a bare 0 was not.
        return "(NULL)", []
    return "(" + ",".join("?" * len(ns)) + ")", ns


def _kill_where(item_type: str, corpus: str | None = None
                ) -> tuple[str, list[Any]]:
    """The WHERE clause for one occurrence family, plus its parameters.

    Identity is by CONFIRMED NAME, never by "the killer held the camera".
    Those are different claims and conflating them is what produced a corpus
    labelled "my frags" that was 5% somebody else's.
    """
    users, up = _in(user_norms())
    if item_type == USER_FRAG:
        return f"o.killer_class = 'PLAYER' AND o.killer_name_norm IN {users}", up
    if item_type == DEATH:
        # The user's own deaths, by identity -- not "a death the recorder
        # happened to be the victim of", which is a different set whenever
        # the recorder is not the user.
        return f"o.victim_name_norm IN {users}", up
    clan, cp = _in(roster_norms() - user_norms())
    if item_type == CLAN_FRAG:
        return (f"o.killer_class = 'PLAYER' AND o.killer_name_norm IN {clan}",
                cp)
    if item_type == ALL_KILL and corpus == USER_AND_PTN:
        both, bp = _in(roster_norms() | user_norms())
        return (f"o.killer_class = 'PLAYER' AND o.killer_name_norm IN {both}",
                bp)
    if item_type == ALL_KILL:
        return "o.killer_class = 'PLAYER'", []
    raise ValueError(f"not an occurrence-backed family: {item_type!r}")


_TELEPORT_SELECT = """
SELECT t.rowid AS id, t.content_hash, s.demo_name, t.server_time_ms,
       t.client, t.outcome, t.teleporter, t.kind, s.recorder_client
FROM teleport_transits_v1 t
JOIN scanned_demos s ON s.content_hash = t.content_hash
                    AND s.recorder_client = t.client
WHERE t.outcome = ?
"""


def _teleport_item(r: sqlite3.Row, rank: int, total: int,
                   rv: dict[str, Any]) -> ReviewItem:
    return ReviewItem(
        item_id=f"{TELEPORT}:{r['id']}", item_type=TELEPORT,
        source_id=int(r["id"]), content_hash=r["content_hash"] or "",
        demo_name=r["demo_name"] or "",
        server_time_ms=int(r["server_time_ms"]),
        # A transit has no highlight score and never had one. -1.0 is the
        # sentinel for unscored, and `scored` says so plainly.
        machine_score=-1.0, machine_rank=rank, total_items=total,
        why=f"teleport, {r['outcome'].lower().replace('_', ' ')}",
        scored=False,
        human_role=(rv.get("human_role") or None) or None,
        note=rv.get("note") or "")


def _kill_table_exists() -> bool:
    with _rec() as c:
        return c.execute("SELECT 1 FROM sqlite_master WHERE type='table' "
                         "AND name='kill_occurrences_v1'").fetchone() is not None


# One row per CANONICAL OCCURRENCE, shown through the observation chosen for
# review. The observation supplies the media; the occurrence supplies the
# identity of the historical event.
# A death is watched from the dying player's camera, a frag from the
# killer's. Same occurrence, different question, so the observation the media
# comes from depends on which queue is asking.
_DEATH_SELECT = """
SELECT o.occurrence_id AS id, k.content_hash, s.demo_name, o.server_time_ms,
       o.round, o.mod_name, o.mod, o.victim_client, o.killer_client, o.map,
       k.killer_name_raw, k.victim_name_raw, o.death_cause, o.killer_class,
       k.is_recorder_killer, k.is_recorder_victim, r.highlight_score,
       o.n_observations, o.actor_pov_available,
       CASE WHEN k.is_recorder_victim THEN 'VICTIM_POV'
            WHEN k.is_recorder_killer THEN 'ACTOR_POV'
            ELSE 'OTHER_POV' END AS best_observation_pov,
       o.merge_confidence
FROM kill_occurrences_v1 o
JOIN kill_events_v1 k
  ON k.kill_event_id = COALESCE(o.victim_pov_observation_id,
                                o.best_observation_id)
JOIN scanned_demos s ON s.content_hash = k.content_hash
LEFT JOIN recognized_frags r
       ON r.content_hash = k.content_hash
      AND r.server_time_ms = k.server_time_ms
      AND k.is_recorder_killer = 1
"""

_KILL_SELECT = """
SELECT o.occurrence_id AS id, k.content_hash, s.demo_name, o.server_time_ms,
       o.round, o.mod_name, o.mod, o.victim_client, o.killer_client, o.map,
       k.killer_name_raw, k.victim_name_raw, o.death_cause, o.killer_class,
       k.is_recorder_killer, k.is_recorder_victim, r.highlight_score,
       o.n_observations, o.actor_pov_available, o.best_observation_pov,
       o.merge_confidence
FROM kill_occurrences_v1 o
JOIN kill_events_v1 k ON k.kill_event_id = o.best_observation_id
JOIN scanned_demos s ON s.content_hash = k.content_hash
LEFT JOIN recognized_frags r
       ON r.content_hash = k.content_hash
      AND r.server_time_ms = k.server_time_ms
      AND k.is_recorder_killer = 1
"""


def _kill_why(row: sqlite3.Row) -> str:
    """What is known about this moment. For a foreign-camera frag that is
    genuinely less than for the actor's own, and saying so is better than
    padding it out."""
    who = _strip_colors(row["killer_name_raw"] or "") or "unknown"
    weap = row["mod_name"] or "kill"
    n = row["n_observations"] if "n_observations" in row.keys() else 1
    extra = f", {n} camera angles" if n and n > 1 else ""
    if row["is_recorder_victim"]:
        return f"killed by {who}, {weap}{extra}"
    if row["is_recorder_killer"]:
        return f"{weap}, actor's own camera{extra}"
    return f"{who}, {weap}, observed from another camera{extra}"


@dataclass(frozen=True)
class ReviewItem:
    """One reviewable moment, of any family."""
    item_id: str                  # "FRAG:24326"
    item_type: str
    source_id: int
    content_hash: str
    demo_name: str
    server_time_ms: int
    machine_score: float
    machine_rank: int
    total_items: int
    weapon: str = ""
    map_name: str = ""
    victim: int | None = None
    round_no: int | None = None
    why: str = ""
    # Who did it, and whether this footage is their own view. A clanmate's
    # frag inside somebody else's demo is that clanmate's frag seen from a
    # foreign camera -- it is not their first-person view, and calling it one
    # would be wrong in the review UI, in an export, and in the film.
    actor_name: str | None = None
    is_actor_pov: bool = True
    death_cause: str | None = None
    # How many demos recorded this one historical kill, and which camera the
    # review is being shown through. One frag, one review -- the alternatives
    # are preserved, not shown.
    n_observations: int = 1
    observation_pov: str | None = None
    merge_confidence: str | None = None
    # False when the recogniser never scored this moment, which is every
    # moment whose actor is not the recorder. Distinct from a low score.
    scored: bool = True
    human_role: str | None = None
    note: str = ""

    @property
    def start_ms(self) -> int:
        return max(0, self.server_time_ms - PRE_MS)

    @property
    def end_ms(self) -> int:
        return self.server_time_ms + POST_MS

    @property
    def reviewed(self) -> bool:
        return self.human_role is not None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.update(start_ms=self.start_ms, end_ms=self.end_ms,
                 reviewed=self.reviewed,
                 frag_offset_s=(self.server_time_ms - self.start_ms) / 1000.0,
                 duration_s=(self.end_ms - self.start_ms) / 1000.0)
        return d


# ── persistence ─────────────────────────────────────────────────────────────

_SCHEMA = """
CREATE TABLE IF NOT EXISTS human_reviews (
    item_id        TEXT PRIMARY KEY,
    item_type      TEXT NOT NULL,
    source_id      INTEGER NOT NULL,
    human_role     TEXT NOT NULL,
    note           TEXT NOT NULL DEFAULT '',
    reviewed_at    TEXT NOT NULL,
    review_version TEXT NOT NULL,
    provenance     TEXT NOT NULL DEFAULT 'HUMAN_USER'
);
CREATE TABLE IF NOT EXISTS human_review_log (
    rowid_         INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id        TEXT NOT NULL,
    human_role     TEXT,
    note           TEXT,
    at             TEXT NOT NULL
);
"""

# Indexes run AFTER the column migration below: an index on a column an old
# database has not grown yet fails the whole script.
_INDEXES = """
CREATE INDEX IF NOT EXISTS ix_hr_role ON human_reviews(human_role);
CREATE INDEX IF NOT EXISTS ix_hr_type ON human_reviews(item_type, human_role);
CREATE INDEX IF NOT EXISTS ix_hr_prov ON human_reviews(provenance);
"""


def conn() -> sqlite3.Connection:
    c = sqlite3.connect(EDITORIAL_DB, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.executescript(_SCHEMA)
    cols = {r[1] for r in c.execute("PRAGMA table_info(human_reviews)")}
    if "provenance" not in cols:      # rows written before provenance existed
        c.execute("ALTER TABLE human_reviews ADD COLUMN provenance TEXT "
                  "NOT NULL DEFAULT 'HUMAN_USER'")
    c.executescript(_INDEXES)
    return c


def _rec() -> sqlite3.Connection:
    c = sqlite3.connect(f"file:{RECOGNITION_DB}?mode=ro", uri=True, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA busy_timeout=30000")
    return c


def record(item_id: str, item_type: str, source_id: int, role: str,
           note: str | None = None, provenance: str = HUMAN_USER
           ) -> dict[str, Any]:
    """Save a verdict. Immediate, and appended to a log so a mistake is
    recoverable rather than merely regretted.

    `provenance` says who decided. It defaults to HUMAN_USER because the UI
    is the only thing that should be calling this without thinking; a test
    must pass TEST explicitly, and a guard in the test suite holds that line.
    """
    if role not in ROLES:
        raise ValueError(f"unknown role {role!r}")
    if provenance not in PROVENANCES:
        raise ValueError(f"unknown provenance {provenance!r}")
    with conn() as c:
        prev = c.execute("SELECT note FROM human_reviews WHERE item_id=?",
                         (item_id,)).fetchone()
        keep = prev["note"] if (prev and note is None) else (note or "")
        c.execute(
            "INSERT INTO human_reviews(item_id,item_type,source_id,human_role,"
            "note,reviewed_at,review_version,provenance) "
            "VALUES(?,?,?,?,?,datetime('now'),?,?) "
            "ON CONFLICT(item_id) DO UPDATE SET human_role=excluded.human_role,"
            "note=excluded.note, reviewed_at=excluded.reviewed_at, "
            "provenance=excluded.provenance",
            (item_id, item_type, source_id, role, keep, REVIEW_VERSION,
             provenance))
        c.execute("INSERT INTO human_review_log(item_id,human_role,note,at) "
                  "VALUES(?,?,?,datetime('now'))", (item_id, role, keep))
    return {"item_id": item_id, "human_role": role, "note": keep}


def annotate(item_id: str, note: str) -> dict[str, Any]:
    """A note without a verdict. Saving a thought must never force a
    decision."""
    with conn() as c:
        row = c.execute("SELECT human_role, item_type, source_id "
                        "FROM human_reviews WHERE item_id=?",
                        (item_id,)).fetchone()
        if row:
            c.execute("UPDATE human_reviews SET note=?, reviewed_at="
                      "datetime('now') WHERE item_id=?", (note, item_id))
        else:
            kind, _, sid = item_id.partition(":")
            c.execute(
                "INSERT INTO human_reviews(item_id,item_type,source_id,"
                "human_role,note,reviewed_at,review_version) "
                "VALUES(?,?,?,'',?,datetime('now'),?)",
                (item_id, kind, int(sid or 0), note, REVIEW_VERSION))
        c.execute("INSERT INTO human_review_log(item_id,human_role,note,at) "
                  "VALUES(?,NULL,?,datetime('now'))", (item_id, note))
    return {"item_id": item_id, "note": note}


def undo_last() -> dict[str, Any] | None:
    """Take back the most recent verdict. Reviewing thousands of items means
    mis-clicking some of them."""
    with conn() as c:
        row = c.execute("SELECT item_id FROM human_review_log "
                        "ORDER BY rowid_ DESC LIMIT 1").fetchone()
        if not row:
            return None
        item = row["item_id"]
        c.execute("DELETE FROM human_reviews WHERE item_id=?", (item,))
        c.execute("DELETE FROM human_review_log WHERE rowid_ = "
                  "(SELECT MAX(rowid_) FROM human_review_log)")
    return {"undone": item}


def reviews(item_ids: Sequence[str]) -> dict[str, dict[str, Any]]:
    if not item_ids:
        return {}
    with conn() as c:
        qs = ",".join("?" * len(item_ids))
        return {r["item_id"]: dict(r) for r in c.execute(
            f"SELECT * FROM human_reviews WHERE item_id IN ({qs})",
            list(item_ids))}


# ── the queue ───────────────────────────────────────────────────────────────

ORDER_WORST_FIRST = "WORST_FIRST"
ORDER_BEST_FIRST = "BEST_FIRST"
ORDERS = (ORDER_WORST_FIRST, ORDER_BEST_FIRST)


def _frag_rows(order: str, limit: int, offset: int, unreviewed_only: bool,
               item_type: str = FRAG) -> list[sqlite3.Row]:
    direction = "ASC" if order == ORDER_WORST_FIRST else "DESC"
    where = "WHERE mod = ?" if item_type == TELEFRAG else ""
    pre: list[Any] = [MOD_TELEFRAG] if item_type == TELEFRAG else []
    sql = ("SELECT id, content_hash, demo_name, server_time_ms, round, "
           "weapon_name, victim_client, highlight_score, classes, reasons "
           f"FROM recognized_frags {where} "
           f"ORDER BY highlight_score {direction}, id ASC "
           "LIMIT ? OFFSET ?")
    with _rec() as c:
        rows = c.execute(sql, (*pre, limit, offset)).fetchall()
    if not unreviewed_only:
        return rows
    got = reviews([f"{item_type}:{r['id']}" for r in rows])
    return [r for r in rows if f"{item_type}:{r['id']}" not in got]


def _why(row: sqlite3.Row) -> str:
    """One line saying what the machine noticed. Not a justification -- the
    user is about to disagree with it regularly, and should be able to see
    exactly what it thought."""
    import json
    try:
        cls = [c.get("name") for c in json.loads(row["classes"] or "[]")]
    except Exception:
        cls = []
    if cls:
        return ", ".join(cls[:4])
    return f"{row['weapon_name'] or 'kill'}, no class detected"


def _kill_rows(order: str, limit: int, offset: int, unreviewed_only: bool,
               item_type: str, corpus: str | None) -> list[sqlite3.Row]:
    where, params = _kill_where(item_type, corpus)
    select = _DEATH_SELECT if item_type == DEATH else _KILL_SELECT
    direction = "ASC" if order == ORDER_WORST_FIRST else "DESC"
    # Unscored rows sort after scored ones in both directions rather than
    # being treated as a score of zero. A missing score is not a low score.
    sql = (f"{select} WHERE {where} "
           f"ORDER BY (r.highlight_score IS NULL), r.highlight_score {direction}, "
           "o.occurrence_id ASC LIMIT ? OFFSET ?")
    with _rec() as c:
        rows = c.execute(sql, (*params, limit, offset)).fetchall()
    if not unreviewed_only:
        return rows
    got = reviews([f"{item_type}:{r['id']}" for r in rows])
    return [r for r in rows if f"{item_type}:{r['id']}" not in got]


def _kill_item(r: sqlite3.Row, item_type: str, rank: int, total: int,
               rv: dict[str, Any]) -> ReviewItem:
    score = r["highlight_score"]
    return ReviewItem(
        item_id=f"{item_type}:{r['id']}", item_type=item_type,
        source_id=int(r["id"]), content_hash=r["content_hash"] or "",
        demo_name=r["demo_name"] or "",
        server_time_ms=int(r["server_time_ms"]),
        # -1.0 is the sentinel for "the recogniser never scored this", which
        # is the truth for every frag seen from a camera that is not the
        # actor's. It is not a score of zero and must not be compared.
        machine_score=float(score) if score is not None else -1.0,
        machine_rank=rank, total_items=total,
        weapon=r["mod_name"] or "", map_name=r["map"] or "",
        victim=r["victim_client"], round_no=r["round"], why=_kill_why(r),
        actor_name=_strip_colors(r["killer_name_raw"] or "") or None,
        is_actor_pov=bool(r["is_recorder_killer"]),
        death_cause=r["death_cause"],
        n_observations=int(r["n_observations"] or 1),
        observation_pov=r["best_observation_pov"],
        merge_confidence=r["merge_confidence"],
        scored=score is not None,
        human_role=(rv.get("human_role") or None) or None,
        note=rv.get("note") or "")


def queue(order: str = ORDER_WORST_FIRST, limit: int = 50, offset: int = 0,
          item_type: str = FRAG, unreviewed_only: bool = False,
          corpus: str | None = None) -> list[ReviewItem]:
    """A slice of the corpus in the requested order.

    The default is WORST FIRST because that is what was asked for, and it is
    also the honest direction: the bottom of a machine ranking is exactly
    where the machine is most likely to be wrong.
    """
    if order not in ORDERS:
        raise ValueError(f"unknown order {order!r}")
    if corpus is not None and item_type in (FRAG, None):
        item_type = CORPUS_ITEM_TYPE.get(corpus, item_type)
    if item_type == TELEPORT:
        total = count_items(TELEPORT)
        with _rec() as c:
            rows = c.execute(
                f"{_TELEPORT_SELECT} ORDER BY t.rowid LIMIT ? OFFSET ?",
                (TELEPORT_CONFIRMED, limit, offset)).fetchall()
        ids = [f"{TELEPORT}:{r['id']}" for r in rows]
        got = reviews(ids)
        if unreviewed_only:
            rows = [r for r in rows if f"{TELEPORT}:{r['id']}" not in got]
        return [_teleport_item(r, offset + i + 1, total,
                               got.get(f"{TELEPORT}:{r['id']}") or {})
                for i, r in enumerate(rows)]
    if item_type in KILL_BACKED:
        if not _kill_table_exists():
            return []
        total = count_items(item_type, corpus=corpus)
        rows = _kill_rows(order, limit, offset, unreviewed_only, item_type,
                          corpus)
        got = reviews([f"{item_type}:{r['id']}" for r in rows])
        return [_kill_item(r, item_type, offset + i + 1, total,
                           got.get(f"{item_type}:{r['id']}") or {})
                for i, r in enumerate(rows)]
    if item_type not in (FRAG, TELEFRAG):
        return []                       # other families wire in next
    total = count_items(item_type)
    rows = _frag_rows(order, limit, offset, unreviewed_only, item_type)
    ids = [f"{item_type}:{r['id']}" for r in rows]
    got = reviews(ids)
    out: list[ReviewItem] = []
    for i, r in enumerate(rows):
        iid = f"{item_type}:{r['id']}"
        rv = got.get(iid) or {}
        rank = offset + i + 1
        out.append(ReviewItem(
            item_id=iid, item_type=item_type, source_id=int(r["id"]),
            content_hash=r["content_hash"] or "", demo_name=r["demo_name"] or "",
            server_time_ms=int(r["server_time_ms"]),
            machine_score=float(r["highlight_score"]),
            machine_rank=rank, total_items=total,
            weapon=r["weapon_name"] or "", victim=r["victim_client"],
            round_no=r["round"], why=_why(r),
            human_role=(rv.get("human_role") or None) or None,
            note=rv.get("note") or ""))
    return out


def count_items(item_type: str = FRAG, corpus: str | None = None) -> int:
    if item_type in KILL_BACKED:
        if not _kill_table_exists():
            return 0
        where, params = _kill_where(item_type, corpus)
        with _rec() as c:
            return int(c.execute(
                f"SELECT COUNT(*) FROM kill_occurrences_v1 o WHERE {where}",
                params).fetchone()[0])
    if item_type == TELEPORT:
        with _rec() as c:
            return int(c.execute(
                "SELECT COUNT(*) FROM teleport_transits_v1 t "
                "JOIN scanned_demos s ON s.content_hash = t.content_hash "
                "AND s.recorder_client = t.client WHERE t.outcome = ?",
                (TELEPORT_CONFIRMED,)).fetchone()[0])
    if item_type == FRAG:
        with _rec() as c:
            return int(c.execute("SELECT COUNT(*) FROM recognized_frags")
                       .fetchone()[0])
    if item_type == TELEFRAG:
        with _rec() as c:
            return int(c.execute("SELECT COUNT(*) FROM recognized_frags "
                                 "WHERE mod = ?", (MOD_TELEFRAG,)).fetchone()[0])
    return 0


def item(item_id: str) -> ReviewItem | None:
    kind, _, sid = item_id.partition(":")
    if kind == TELEPORT:
        with _rec() as c:
            r = c.execute(f"{_TELEPORT_SELECT} AND t.rowid = ?",
                          (TELEPORT_CONFIRMED, int(sid))).fetchone()
        if not r:
            return None
        return _teleport_item(r, 0, count_items(TELEPORT),
                              reviews([item_id]).get(item_id) or {})
    if kind in KILL_BACKED:
        if not _kill_table_exists():
            return None
        with _rec() as c:
            sel = _DEATH_SELECT if kind == DEATH else _KILL_SELECT
            r = c.execute(f"{sel} WHERE o.occurrence_id = ?",
                          (int(sid),)).fetchone()
        if not r:
            return None
        rv = reviews([item_id]).get(item_id) or {}
        return _kill_item(r, kind, 0, count_items(kind), rv)
    if kind not in (FRAG, TELEFRAG):
        return None
    with _rec() as c:
        r = c.execute(
            "SELECT id, content_hash, demo_name, server_time_ms, round, "
            "weapon_name, victim_client, highlight_score, classes, reasons "
            "FROM recognized_frags WHERE id=?", (int(sid),)).fetchone()
        if not r:
            return None
        rank = int(c.execute(
            "SELECT COUNT(*) FROM recognized_frags WHERE highlight_score < ? "
            "OR (highlight_score = ? AND id <= ?)",
            (r["highlight_score"], r["highlight_score"], r["id"])).fetchone()[0])
    rv = reviews([item_id]).get(item_id) or {}
    return ReviewItem(
        item_id=item_id, item_type=kind, source_id=int(r["id"]),
        content_hash=r["content_hash"] or "", demo_name=r["demo_name"] or "",
        server_time_ms=int(r["server_time_ms"]),
        machine_score=float(r["highlight_score"]), machine_rank=rank,
        total_items=count_items(kind), weapon=r["weapon_name"] or "",
        victim=r["victim_client"], round_no=r["round"], why=_why(r),
        human_role=(rv.get("human_role") or None) or None,
        note=rv.get("note") or "")


# ── progress and pools ──────────────────────────────────────────────────────

def progress(item_type: str = FRAG, corpus: str | None = None) -> dict[str, Any]:
    # MY_AND_PTN and ALL_PLAYERS share an item type but not a total: the
    # combined corpus is narrowed by the roster in SQL. Counting without the
    # corpus would report all-player progress against a smaller queue.
    total = count_items(item_type, corpus=corpus)
    with conn() as c:
        qs = ",".join("?" * len(HUMAN_PROVENANCE))
        counts = {r["human_role"]: r["n"] for r in c.execute(
            "SELECT human_role, COUNT(*) n FROM human_reviews "
            f"WHERE item_type=? AND human_role<>'' AND provenance IN ({qs}) "
            "GROUP BY 1", (item_type, *HUMAN_PROVENANCE))}
        other = {r["provenance"]: r["n"] for r in c.execute(
            "SELECT provenance, COUNT(*) n FROM human_reviews "
            f"WHERE item_type=? AND provenance NOT IN ({qs}) GROUP BY 1",
            (item_type, *HUMAN_PROVENANCE))}
    reviewed = sum(counts.values())
    return {"item_type": item_type, "total": total, "reviewed": reviewed,
            "unreviewed": total - reviewed,
            "roles": {r: counts.get(r, 0) for r in ROLES},
            "non_human_rows": other, "labels": ROLE_LABEL}


def pool(role: str, item_type: str | None = None, weapon: str | None = None,
         limit: int = 200) -> list[dict[str, Any]]:
    """Everything the user gave one role. This is what makes the review
    worth doing: ten rails in a row is a query, not a memory."""
    if role not in ROLES:
        raise ValueError(f"unknown role {role!r}")
    with conn() as c:
        # Pools feed the composer, so only human judgement enters them.
        qs = ",".join("?" * len(HUMAN_PROVENANCE))
        sql = (f"SELECT * FROM human_reviews WHERE human_role=? "
               f"AND provenance IN ({qs})")
        args: list[Any] = [role, *HUMAN_PROVENANCE]
        if item_type:
            sql += " AND item_type=?"
            args.append(item_type)
        sql += " ORDER BY reviewed_at DESC LIMIT ?"
        args.append(limit)
        rows = [dict(r) for r in c.execute(sql, args)]
    if not weapon:
        return rows
    ids = [int(r["source_id"]) for r in rows if r["item_type"] == FRAG]
    if not ids:
        return []
    with _rec() as c:
        qs = ",".join("?" * len(ids))
        keep = {r[0] for r in c.execute(
            f"SELECT id FROM recognized_frags WHERE id IN ({qs}) "
            "AND weapon_name = ?", ids + [weapon])}
    return [r for r in rows if int(r["source_id"]) in keep]


def search_notes(text: str, limit: int = 100) -> list[dict[str, Any]]:
    with conn() as c:
        return [dict(r) for r in c.execute(
            "SELECT * FROM human_reviews WHERE note LIKE ? "
            "ORDER BY reviewed_at DESC LIMIT ?", (f"%{text}%", limit))]


def import_legacy() -> dict[str, Any]:
    """Bring forward verdicts from the older editorial_reviews table.

    Only where the mapping is unambiguous. A guess here would put words in
    the user's mouth about their own career.
    """
    mapping = {"FEATURE": T1_FEATURE_FX, "TRANSITION": T2_TRANSITION,
               "RHYTHM": T3_RHYTHM_MONTAGE, "KEEP": T4_KEEP_NORMAL,
               "PASS": T5_PASS_FILLER}
    moved, skipped = 0, []
    with conn() as c:
        try:
            rows = c.execute("SELECT frag_id, verdict, notes FROM "
                             "editorial_reviews").fetchall()
        except sqlite3.OperationalError:
            return {"imported": 0, "skipped": [], "note": "no legacy table"}
    for r in rows:
        role = mapping.get((r["verdict"] or "").upper())
        if not role:
            skipped.append({"frag_id": r["frag_id"], "verdict": r["verdict"]})
            continue
        record(f"{FRAG}:{r['frag_id']}", FRAG, int(r["frag_id"]), role,
               r["notes"] or "")
        moved += 1
    return {"imported": moved, "skipped": skipped}
