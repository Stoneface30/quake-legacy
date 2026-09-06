"""Outgoing action accuracy: what the user hit during THIS action.

WHY THIS EXISTS RATHER THAN THE OBVIOUS FIELD. `recognition_lg_engagements`
looks like the answer and is not: 13,696 rows whose `series` is empty, zero
of 4,000 sampled carrying any `my_fire`. And `lg_incoming_hit_ratio`, which
does have data, is INCOMING -- the share of shots that hit the USER. It
measures the opponent's aim, and showing it as the user's would be exactly
backwards. Neither may be used here.

WHAT IS USED INSTEAD. Two streams already in `semantic_events_v1`:

    fire_weapon, source='playerstate'   3,074,889   the RECORDER's own shots
    pain, with client_num               1,000,344   who was hit, and when

The denominator is the user's own shots of that weapon inside the action
window. The numerator is pain landing on the victim inside the same window.
Both are per-tick server facts and neither needs a reparse.

A PAIN EVENT PROVES DAMAGE, NOT AUTHORSHIP. In a crossfire the victim's pain
may be a teammate's rocket. So every result carries a confidence, and where
another player was also shooting the same target the hits are reported as
ambiguous rather than counted as the user's. A range is more honest than a
number that is wrong.

LG COUNTS TICKS, NOT CLICKS. The lightning gun fires about twenty times a
second, so its denominator is attack ticks and the field says so. Comparing
an LG tick count to a rail shot count would be meaningless, which is why
there is no single generic accuracy field anywhere in this module.

AND FOR LG THERE IS NO HIT COUNT AT ALL. Pain events are throttled by the
server, not emitted per hit: measured across one demo, the gap between two
pain events on the same victim has a median of 925 ms, a minimum of 150 ms,
and NOT ONE gap under 100 ms. A weapon firing every 50 ms cannot have its
hits counted by a signal that arrives three times a second. The first version
of this module happily divided 3 pain events by 23 attack ticks and reported
13% for what was almost certainly a good kill.

So accuracy is derived ONLY for weapons whose fire interval is slower than
the pain throttle -- rail, rocket, grenade, shotgun. For lightning, plasma
and machinegun the shots and the engagement duration are reported and the
accuracy field says it is not derivable, with the reason. A missing number is
recoverable; a confident wrong one teaches the director the wrong thing about
their own aim.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
RECOGNITION_DB = REPO_ROOT / "creative_suite" / "database" / "frag_recognition.db"

# WP_ launcher space, from bg_public.h via demo_parse._WP_NAMES. NOT MOD_.
WP = {1: "GAUNTLET", 2: "MACHINEGUN", 3: "SHOTGUN", 4: "GRENADE_LAUNCHER",
      5: "ROCKET_LAUNCHER", 6: "LIGHTNING", 7: "RAILGUN", 8: "PLASMA",
      9: "BFG", 11: "NAILGUN", 12: "PROX_LAUNCHER", 13: "CHAINGUN", 14: "HMG"}
WP_BY_NAME = {v: k for k, v in WP.items()}

# MOD_ (means of death) -> the WP_ that fired it, for the weapons where the
# mapping is unambiguous. Splash and direct share a launcher.
MOD_TO_WP = {
    1: 3, 2: 1, 3: 2,            # SHOTGUN, GAUNTLET, MACHINEGUN
    4: 4, 5: 4,                  # GRENADE, GRENADE_SPLASH
    6: 5, 7: 5,                  # ROCKET, ROCKET_SPLASH
    8: 8, 9: 8,                  # PLASMA, PLASMA_SPLASH
    10: 7, 11: 6,                # RAILGUN, LIGHTNING
}

# How far back an engagement can begin. Long enough for a sustained LG duel,
# short enough that the previous fight is not swept in.
LG_WINDOW_MS = 4000
HITSCAN_WINDOW_MS = 2500
PROJECTILE_WINDOW_MS = 3500

# Weapons whose denominator is a tick count rather than a shot count.
CONTINUOUS = {6, 8, 2, 13, 14}    # LG, plasma, machinegun, chaingun, HMG

# Weapons that fire slower than the observed pain throttle (min 150 ms,
# median 925 ms) and can therefore have hits attributed at all.
ATTRIBUTABLE = {3, 4, 5, 7}       # shotgun, grenade, rocket, rail

NOT_DERIVABLE = "NOT_DERIVABLE"

CONF_HIGH = "HIGH"        # the user was the only one shooting this target
CONF_AMBIGUOUS = "AMBIGUOUS"   # someone else was firing too
CONF_UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ActionStats:
    weapon: str | None
    weapon_wp: int | None
    window_ms: int
    shots: int | None = None            # attack ticks for LG
    hits_confirmed: int | None = None
    hits_ambiguous: int = 0
    accuracy_pct: float | None = None
    accuracy_upper_pct: float | None = None
    engagement_ms: int | None = None
    damage_dealt: int | None = None     # only where a ledger exists
    target: str | None = None
    confidence: str = CONF_UNKNOWN
    unit: str = "shots"
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _conn(db: Path = RECOGNITION_DB) -> sqlite3.Connection:
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=60)
    c.row_factory = sqlite3.Row
    return c


def window_for(wp: int | None) -> int:
    if wp in CONTINUOUS:
        return LG_WINDOW_MS
    if wp in (5, 4, 8):                 # rocket, grenade, plasma
        return PROJECTILE_WINDOW_MS
    return HITSCAN_WINDOW_MS


def for_action(content_hash: str, frag_time_ms: int, mod: int | None,
               victim_client: int | None, is_actor_pov: bool,
               target_name: str | None = None,
               db: Path = RECOGNITION_DB) -> ActionStats:
    """Accuracy for one action, or an honest UNKNOWN.

    Requires the actor to have held the camera: `fire_weapon` from
    `playerstate` is the RECORDER's own trigger. On a foreign-camera
    observation those shots belong to the cameraman, and attributing them to
    the actor would be a false statement about whose aim this was.
    """
    wp = MOD_TO_WP.get(mod) if mod is not None else None
    name = WP.get(wp) if wp else None
    win = window_for(wp)
    if not is_actor_pov:
        return ActionStats(weapon=name, weapon_wp=wp, window_ms=win,
                           confidence=CONF_UNKNOWN,
                           note="the actor did not hold the camera, so their "
                                "own trigger is not in this demo")
    if wp is None:
        return ActionStats(weapon=name, weapon_wp=wp, window_ms=win,
                           confidence=CONF_UNKNOWN,
                           note="no unambiguous weapon for this means of death")

    t0, t1 = frag_time_ms - win, frag_time_ms + 100
    with _conn(db) as c:
        shots = c.execute(
            "SELECT COUNT(*) FROM semantic_events_v1 WHERE content_hash=? "
            "AND type='fire_weapon' AND source='playerstate' AND weapon=? "
            "AND server_time_ms BETWEEN ? AND ?",
            (content_hash, wp, t0, t1)).fetchone()[0]
        if victim_client is None:
            hits = None
            others = 0
        else:
            hits = c.execute(
                "SELECT COUNT(*) FROM semantic_events_v1 WHERE content_hash=? "
                "AND type='pain' AND client_num=? "
                "AND server_time_ms BETWEEN ? AND ?",
                (content_hash, victim_client, t0, t1)).fetchone()[0]
            # Was anyone else shooting in this window? Entity-sourced
            # fire_weapon covers every OTHER player. If so, the victim's pain
            # cannot all be claimed for the user.
            others = c.execute(
                "SELECT COUNT(*) FROM semantic_events_v1 WHERE content_hash=? "
                "AND type='fire_weapon' AND source='entity' "
                "AND entity_num IS NOT NULL AND entity_num<>? "
                "AND server_time_ms BETWEEN ? AND ?",
                (content_hash, victim_client, t0, t1)).fetchone()[0]
        first = c.execute(
            "SELECT MIN(server_time_ms) FROM semantic_events_v1 WHERE "
            "content_hash=? AND type='fire_weapon' AND source='playerstate' "
            "AND weapon=? AND server_time_ms BETWEEN ? AND ?",
            (content_hash, wp, t0, t1)).fetchone()[0]

    if not shots:
        return ActionStats(weapon=name, weapon_wp=wp, window_ms=win, shots=0,
                           confidence=CONF_UNKNOWN, target=target_name,
                           note="no shots of this weapon recorded in the window")

    unit = "attack ticks" if wp in CONTINUOUS else "shots"
    engagement = (frag_time_ms - int(first)) if first is not None else None
    if wp not in ATTRIBUTABLE:
        # Shots and duration are solid; hits are not countable for a weapon
        # that fires faster than the pain signal arrives.
        return ActionStats(
            weapon=name, weapon_wp=wp, window_ms=win, shots=shots, unit=unit,
            engagement_ms=engagement, target=target_name,
            confidence=NOT_DERIVABLE,
            note=("pain events are throttled -- median 925 ms apart, never "
                  f"under 100 ms -- so hits cannot be counted for a weapon "
                  f"firing this fast. {unit} and engagement duration are "
                  f"measured; accuracy is not derivable"))
    if hits is None:
        return ActionStats(weapon=name, weapon_wp=wp, window_ms=win,
                           shots=shots, unit=unit, engagement_ms=engagement,
                           target=target_name, confidence=CONF_UNKNOWN,
                           note="no victim slot, so hits cannot be attributed")

    # THE KILL ITSELF IS A CONFIRMED HIT. The obituary names this weapon and
    # this victim, so at least one shot landed -- that is server truth, not
    # an inference from pain. Without this a one-shot rail kill reported
    # zero hits, which is absurd on its face.
    capped = max(1, min(hits, shots))
    if others and capped > 1:
        # More than the killing blow is claimed, and someone else was firing.
        # The kill stays confirmed; the extra hits do not.
        # Someone else was firing. The user's share is between "none of the
        # pain was theirs" and "all of it was".
        return ActionStats(
            weapon=name, weapon_wp=wp, window_ms=win, shots=shots,
            hits_confirmed=1, hits_ambiguous=capped - 1,
            accuracy_pct=round(100 / shots, 1),
            accuracy_upper_pct=round(100 * capped / shots, 1),
            engagement_ms=engagement, target=target_name, unit=unit,
            confidence=CONF_AMBIGUOUS,
            note=(f"the killing shot is confirmed by the obituary; {capped - 1} "
                  f"further hit(s) cannot be attributed because {others} shots "
                  f"came from other players in the same window"))
    return ActionStats(
        weapon=name, weapon_wp=wp, window_ms=win, shots=shots,
        hits_confirmed=capped, hits_ambiguous=0,
        accuracy_pct=round(100 * capped / shots, 1),
        engagement_ms=engagement, target=target_name, unit=unit,
        confidence=CONF_HIGH,
        note="the user was the only player firing at this target in the window")
