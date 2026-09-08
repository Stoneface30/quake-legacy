"""Netcode / delivery anomalies as numeric evidence -- never as verdicts.

WHAT THIS IS. A NetcodeAnomaly is a numerically interesting networking,
prediction or delivery situation preserved with its evidence so it can
later be investigated, rendered as a forensic replay, documented, or used
creatively. It compares truth layers (recorded event, recorded snapshot
state, physics-reconstructed state, event-constrained state) and reports the
residuals between them. It never merges the layers and never edits them.

WHAT THIS IS NOT. Not a netcode rewrite, not a hit-registration study, not a
bug tracker. ANOMALY DOES NOT MEAN BUG: every record carries an assessment,
and the only assessments a detector may assign on its own are the ones that
say "this is how a client-side recording behaves" or "the evidence is
insufficient". SUSPECTED_BUG needs a stated reason; CONFIRMED_BUG needs a
named confirmation. A projectile the client recorded for 25 ms and then lost
is a CLIENT_OBSERVATION_GAP, and when the physics continuation lands on the
recorded explosion it is an excellent forensic case -- not a Quake bug.

IDENTITY. (content_hash, server_time_ms, entity/event) -- see round_context.
The same map replayed produces identical-looking kills that are different
occurrences; an anomaly id therefore hashes the recording identity, never
map + time.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field, replace
import hashlib
import json
import math
from typing import Any, Sequence

from creative_suite.engine import demo_truth as dt

ANOMALY_VERSION = "netcode-anomaly-v1.0.0"
UNKNOWN = "UNKNOWN"

# ── taxonomy ────────────────────────────────────────────────────────────────

NETCODE_HIT_DISAGREEMENT = "NETCODE_HIT_DISAGREEMENT"
PREDICTION_CORRECTION_SPIKE = "PREDICTION_CORRECTION_SPIKE"
REMOTE_TELEPORT = "REMOTE_TELEPORT"
SNAPSHOT_GAP = "SNAPSHOT_GAP"
DAMAGE_WITHOUT_EXPECTED_CONTACT = "DAMAGE_WITHOUT_EXPECTED_CONTACT"
CONTACT_WITHOUT_DAMAGE = "CONTACT_WITHOUT_DAMAGE"
PROJECTILE_VISUAL_DISAGREEMENT = "PROJECTILE_VISUAL_DISAGREEMENT"
REWIND_LIMIT_EDGE = "REWIND_LIMIT_EDGE"
SPLASH_FALLOFF_EDGE = "SPLASH_FALLOFF_EDGE"
PLAYERSTATE_ENTITYSTATE_DISAGREEMENT = "PLAYERSTATE_ENTITYSTATE_DISAGREEMENT"
PROJECTILE_RECONSTRUCTION_DISAGREEMENT = "PROJECTILE_RECONSTRUCTION_DISAGREEMENT"
CLIENT_OBSERVATION_GAP = "CLIENT_OBSERVATION_GAP"
PROJECTILE_TERMINATION_DISAGREEMENT = "PROJECTILE_TERMINATION_DISAGREEMENT"
REMOTE_STATE_DISCONTINUITY = "REMOTE_STATE_DISCONTINUITY"

ANOMALY_TYPES = (
    NETCODE_HIT_DISAGREEMENT, PREDICTION_CORRECTION_SPIKE, REMOTE_TELEPORT,
    SNAPSHOT_GAP, DAMAGE_WITHOUT_EXPECTED_CONTACT, CONTACT_WITHOUT_DAMAGE,
    PROJECTILE_VISUAL_DISAGREEMENT, REWIND_LIMIT_EDGE, SPLASH_FALLOFF_EDGE,
    PLAYERSTATE_ENTITYSTATE_DISAGREEMENT, PROJECTILE_RECONSTRUCTION_DISAGREEMENT,
    CLIENT_OBSERVATION_GAP, PROJECTILE_TERMINATION_DISAGREEMENT,
    REMOTE_STATE_DISCONTINUITY)

# Detectors exist for these only. The rest of the taxonomy is reserved so
# records from later work share one vocabulary; nothing populates them yet.
DETECTED_TYPES = (CLIENT_OBSERVATION_GAP, PROJECTILE_RECONSTRUCTION_DISAGREEMENT,
                  PROJECTILE_TERMINATION_DISAGREEMENT, SNAPSHOT_GAP,
                  REMOTE_TELEPORT, REMOTE_STATE_DISCONTINUITY)

# ── assessment ──────────────────────────────────────────────────────────────

EXPECTED_NETCODE_BEHAVIOR = "EXPECTED_NETCODE_BEHAVIOR"
CLIENT_OBSERVATION_LIMITATION = "CLIENT_OBSERVATION_LIMITATION"
RECONSTRUCTION_DISAGREEMENT = "RECONSTRUCTION_DISAGREEMENT"
SUSPICIOUS = "SUSPICIOUS"
SUSPECTED_BUG = "SUSPECTED_BUG"
CONFIRMED_BUG = "CONFIRMED_BUG"
INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"

ASSESSMENTS = (EXPECTED_NETCODE_BEHAVIOR, CLIENT_OBSERVATION_LIMITATION,
               RECONSTRUCTION_DISAGREEMENT, SUSPICIOUS, SUSPECTED_BUG,
               CONFIRMED_BUG, INSUFFICIENT_EVIDENCE)

# What a detector may conclude on its own. Anything stronger is a human's.
AUTOMATIC_ASSESSMENTS = (EXPECTED_NETCODE_BEHAVIOR, CLIENT_OBSERVATION_LIMITATION,
                         RECONSTRUCTION_DISAGREEMENT, INSUFFICIENT_EVIDENCE)

# Creative utility is a hint for the opportunity graph, not a placement.
UTILITY_NONE = "NONE"
UTILITY_REFERENCE = "FORENSIC_REFERENCE"
UTILITY_INTERLUDE = "INTERLUDE_CANDIDATE"
UTILITIES = (UTILITY_NONE, UTILITY_REFERENCE, UTILITY_INTERLUDE)

# ── code spaces (two different enumerations, easy to confuse) ───────────────
#
# WP_* (bg_public.h weapon_t) is the LAUNCHER space. It is what
# missile_samples_v1.weapon holds, what entityState.weapon holds, and -- measured
# on 2026-09-02 across the v1.0.3 demos (grenade frags -> 4, rocket -> 5,
# plasma -> 8) -- what entity-sourced missile_hit / missile_miss events carry,
# because g_missile.c sets bolt->s.weapon = WP_* and the event rides that
# entity. MOD_* (meansOfDeath) is the OBITUARY space: EV_OBITUARY eventParm.
# A playerstate-sourced event's `weapon` is the recorder's HELD weapon at that
# tick (playerState.weapon), never the missile's: do not match on it.

WP_GRENADE_LAUNCHER = 4
WP_ROCKET_LAUNCHER = 5
WP_LIGHTNING = 6
WP_PLASMAGUN = 8
MOD_GRENADE = 4
MOD_GRENADE_SPLASH = 5
MOD_ROCKET = 6
MOD_ROCKET_SPLASH = 7
MOD_PLASMA = 8
MOD_PLASMA_SPLASH = 9

MOD_TO_WP = {MOD_GRENADE: WP_GRENADE_LAUNCHER, MOD_GRENADE_SPLASH: WP_GRENADE_LAUNCHER,
             MOD_ROCKET: WP_ROCKET_LAUNCHER, MOD_ROCKET_SPLASH: WP_ROCKET_LAUNCHER,
             MOD_PLASMA: WP_PLASMAGUN, MOD_PLASMA_SPLASH: WP_PLASMAGUN}
DIRECT_MODS = (MOD_GRENADE, MOD_ROCKET, MOD_PLASMA)

SOURCE_ENTITY = "entity"
SOURCE_PLAYERSTATE = "playerstate"


def wp_for_mod(mod: int | None) -> int | None:
    """The launcher (WP_) that an obituary means-of-death (MOD_) belongs to."""
    return None if mod is None else MOD_TO_WP.get(int(mod))


def mod_matches_wp(mod: int | None, wp: int | None) -> bool:
    return mod is not None and wp is not None and wp_for_mod(mod) == int(wp)


def event_weapon_is_missile(event: dict[str, Any]) -> bool:
    """Only an entity-sourced missile event's `weapon` names the missile."""
    return (event.get("type", "").startswith("missile")
            and event.get("source", SOURCE_ENTITY) != SOURCE_PLAYERSTATE)


def missile_event_matches(event: dict[str, Any], wp: int) -> bool:
    """The event belongs to a missile of launcher `wp` (WP space)."""
    return event_weapon_is_missile(event) and event.get("weapon") == wp


def merge_delta_pos(previous: Sequence[float | None] | None,
                    current: Sequence[float | None]) -> tuple[float | None, ...]:
    """Delta-coded positions: a missing component means UNCHANGED, so it is
    filled from the previous known state. Unknown only when never seen."""
    prev = tuple(previous) if previous is not None else (None, None, None)
    return tuple(c if c is not None else p for c, p in zip(current, prev))


# ── the record ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class NetcodeAnomaly:
    """Numeric evidence for one situation. Unsupported fields stay None and
    serialise as UNKNOWN; nothing is guessed to fill a column."""
    content_hash: str
    server_time_ms: int
    anomaly_type: str
    assessment: str
    detector_version: str = ANOMALY_VERSION
    round_index: int | None = None
    subject_client: int | None = None
    target_client: int | None = None
    entity_num: int | None = None
    weapon_wp: int | None = None          # launcher of the subject missile (WP space)
    event_weapon_wp: int | None = None    # weapon carried by the matched event (WP space)
    weapon_mod: int | None = None         # obituary means-of-death when a frag is involved
    event_type: str = ""
    recorded_before: dict[str, Any] = field(default_factory=dict)
    recorded_after: dict[str, Any] = field(default_factory=dict)
    expected_state: dict[str, Any] = field(default_factory=dict)
    spatial_residual_u: float | None = None
    temporal_residual_us: int | None = None
    damage_evidence: dict[str, Any] = field(default_factory=dict)
    snapshot_gap_us: int | None = None
    provenance_classes: tuple[str, ...] = ()
    confidence: str = ""                # reconstruction confidence when relevant
    reason: str = ""                    # required for SUSPECTED_BUG
    confirmed_by: str = ""              # required for CONFIRMED_BUG
    creative_utility: str = UTILITY_REFERENCE
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.anomaly_type not in ANOMALY_TYPES:
            raise ValueError(f"unknown anomaly type {self.anomaly_type!r}")
        if self.assessment not in ASSESSMENTS:
            raise ValueError(f"unknown assessment {self.assessment!r}")
        if self.assessment == SUSPECTED_BUG and not self.reason.strip():
            raise ValueError("SUSPECTED_BUG needs a stated reason")
        if self.assessment == CONFIRMED_BUG and not self.confirmed_by.strip():
            raise ValueError("CONFIRMED_BUG needs a named confirmation")
        for p in self.provenance_classes:
            if dt.is_synthetic(p) if hasattr(dt, "is_synthetic") else p == dt.CINEMATIC_SYNTHETIC:
                raise ValueError("synthetic evidence cannot enter an anomaly record")
        if self.creative_utility not in UTILITIES:
            raise ValueError(f"unknown creative utility {self.creative_utility!r}")
        if len(self.content_hash) < 8:
            raise ValueError("an anomaly needs the recording's content hash")

    @property
    def demo_us(self) -> int:
        return self.server_time_ms * 1000

    @property
    def is_bug_claim(self) -> bool:
        return self.assessment in (SUSPECTED_BUG, CONFIRMED_BUG)

    def evidence_dict(self) -> dict[str, Any]:
        """The fields that define the record (identity + evidence); notes and
        utility are commentary and do not change the id."""
        d = asdict(self)
        for k in ("notes", "creative_utility"):
            d.pop(k, None)
        return d

    @property
    def anomaly_id(self) -> str:
        blob = json.dumps(self.evidence_dict(), sort_keys=True, default=_jsonable)
        return hashlib.sha256(blob.encode()).hexdigest()[:24]

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["anomaly_id"] = self.anomaly_id
        d["demo_us"] = self.demo_us
        for k, v in list(d.items()):
            if v is None:
                d[k] = UNKNOWN
        return d


def _jsonable(o: Any) -> Any:
    if isinstance(o, float) and (math.isnan(o) or math.isinf(o)):
        return str(o)
    return str(o)


# ── detectors ───────────────────────────────────────────────────────────────

def from_projectile(cont: Any, res: Any, *, content_hash: str,
                    subject_client: int | None, entity_num: int | None,
                    weapon_wp: int | None, event_weapon_wp: int | None = None,
                    round_index: int | None = None,
                    target_client: int | None = None,
                    damage_evidence: dict[str, Any] | None = None
                    ) -> NetcodeAnomaly:
    """A lost projectile with a physics continuation checked against a
    recorded later event (projectile_reconstruction.Continuation +
    ConstraintResult). The client stopped seeing it: CLIENT_OBSERVATION_GAP.
    When the recorded event agrees with the continuation the assessment is
    the client-side limitation it is. When it disagrees, the anomaly is a
    RECONSTRUCTION disagreement -- still not a bug: an unseen body, a mover
    or a pad explains most of them and nothing here can tell which."""
    from creative_suite.engine import projectile_reconstruction as pr
    segs = pr.provenance_segments(cont)
    recorded = [s for s in segs if dt.is_recorded(s.evidence)]
    derived = [s for s in segs if not dt.is_recorded(s.evidence)]
    gap_us = sum(s.duration_us for s in derived)
    last_recorded = max((s.end_us for s in recorded), default=cont.points[0].t_us)
    before = {"t_us": last_recorded, "samples": sum(s.points for s in recorded),
              "launch_pos": list(cont.launch.pos), "launch_vel": list(cont.points[0].vel),
              "launch_speed_u_s": round(pr._length(cont.points[0].vel), 1)}
    expected = {"end_reason": cont.end_reason, "end_t_us": cont.end_t_us,
                "end_pos": list(cont.end_pos), "bounces": len(cont.bounces),
                "flight_us": cont.flight_us}
    after = {"event_kind": res.event_kind, "event_t_us": res.event_t_us,
             "event_pos": list(res.event_pos) if res.event_pos is not None else None}
    compatible = bool(res.compatible)
    # A recorded run AFTER a derived run means an entity re-observed at its
    # terminal state was fed to the continuation as an input; any residual
    # measured there is 0 by construction and proves nothing.
    re_observed = any(dt.is_recorded(b.evidence) and not dt.is_recorded(a.evidence)
                      for a, b in zip(segs, segs[1:]))
    if re_observed:
        a_type, assess = PROJECTILE_TERMINATION_DISAGREEMENT, INSUFFICIENT_EVIDENCE
        note = ("the entity was re-observed after the gap and that observation was "
                "used as a path input; propagate the recorded PREFIX only and treat "
                "the re-observation as the recorded event")
    elif gap_us <= 0:
        a_type, assess = PROJECTILE_TERMINATION_DISAGREEMENT, INSUFFICIENT_EVIDENCE
        note = "no observation gap: nothing was reconstructed"
    elif compatible:
        a_type, assess = CLIENT_OBSERVATION_GAP, CLIENT_OBSERVATION_LIMITATION
        note = (f"client stopped seeing the projectile after {before['samples']} "
                f"samples; physics continuation ({cont.confidence}) agrees with the "
                f"recorded {res.event_kind}")
    elif res.space_residual_u is not None:
        a_type, assess = PROJECTILE_RECONSTRUCTION_DISAGREEMENT, RECONSTRUCTION_DISAGREEMENT
        note = (f"recorded {res.event_kind} is {res.space_residual_u:.0f}u off the "
                f"continuation; possible unseen body, mover or pad -- not a bug claim")
    else:
        a_type, assess = PROJECTILE_TERMINATION_DISAGREEMENT, INSUFFICIENT_EVIDENCE
        note = "time-only disagreement; no recorded position to test against"
    return NetcodeAnomaly(
        content_hash=content_hash, server_time_ms=int(res.event_t_us // 1000),
        anomaly_type=a_type, assessment=assess, round_index=round_index,
        subject_client=subject_client, target_client=target_client,
        entity_num=entity_num, weapon_wp=weapon_wp, event_weapon_wp=event_weapon_wp,
        event_type=res.event_kind, recorded_before=before, recorded_after=after,
        expected_state=expected, spatial_residual_u=res.space_residual_u,
        temporal_residual_us=int(res.time_residual_us),
        damage_evidence=dict(damage_evidence or {}), snapshot_gap_us=gap_us,
        provenance_classes=tuple(dict.fromkeys(s.evidence for s in segs)),
        confidence=cont.confidence, notes=(note,))


def snapshot_gaps(content_hash: str, snapshot_times_ms: Sequence[int], *,
                  nominal_ms: int = 25, factor: int = 4,
                  subject_client: int | None = None) -> list[NetcodeAnomaly]:
    """Snapshot intervals longer than `factor` nominal frames. A client-side
    recording drops and delays snapshots for ordinary reasons (loss, rate
    limits, the recorder itself); the record says how long, not why."""
    out: list[NetcodeAnomaly] = []
    ts = sorted(int(t) for t in snapshot_times_ms)
    for a, b in zip(ts, ts[1:]):
        gap = b - a
        if gap >= nominal_ms * factor:
            out.append(NetcodeAnomaly(
                content_hash=content_hash, server_time_ms=a, anomaly_type=SNAPSHOT_GAP,
                assessment=CLIENT_OBSERVATION_LIMITATION, subject_client=subject_client,
                recorded_before={"snapshot_ms": a}, recorded_after={"snapshot_ms": b},
                snapshot_gap_us=gap * 1000, temporal_residual_us=(gap - nominal_ms) * 1000,
                provenance_classes=(dt.SNAPSHOT_OBSERVED,),
                notes=(f"{gap} ms between snapshots ({gap / nominal_ms:.0f}x nominal)",)))
    return out


PLAYER_SPEED_CAP_U_S = 3200.0   # far above any legitimate movement (pads ~1,600)


def remote_discontinuities(content_hash: str, entity_num: int,
                           samples: Sequence[tuple[int, float, float, float]], *,
                           teleport_times_ms: Sequence[int] = (),
                           teleport_window_ms: int = 100,
                           speed_cap: float = PLAYER_SPEED_CAP_U_S
                           ) -> list[NetcodeAnomaly]:
    """A remote entity moving faster than a body can between consecutive
    samples. With a teleport event nearby it is REMOTE_TELEPORT and expected;
    without one the evidence is a discontinuity of unknown cause."""
    out: list[NetcodeAnomaly] = []
    pts = sorted(samples)
    tps = sorted(int(t) for t in teleport_times_ms)
    for (t0, *p0), (t1, *p1) in zip(pts, pts[1:]):
        dt_ms = t1 - t0
        if dt_ms <= 0:
            continue
        d = math.dist(p0, p1)
        speed = d / (dt_ms / 1000.0)
        if speed < speed_cap:
            continue
        near_tp = any(abs(tp - t1) <= teleport_window_ms for tp in tps)
        out.append(NetcodeAnomaly(
            content_hash=content_hash, server_time_ms=t1, entity_num=entity_num,
            anomaly_type=REMOTE_TELEPORT if near_tp else REMOTE_STATE_DISCONTINUITY,
            assessment=EXPECTED_NETCODE_BEHAVIOR if near_tp else INSUFFICIENT_EVIDENCE,
            recorded_before={"t_ms": t0, "pos": list(p0)},
            recorded_after={"t_ms": t1, "pos": list(p1)},
            spatial_residual_u=round(d, 1), temporal_residual_us=dt_ms * 1000,
            provenance_classes=(dt.ENTITY_OBSERVED,),
            notes=(f"{d:.0f}u in {dt_ms} ms = {speed:.0f} u/s"
                   + (" with a teleport event nearby" if near_tp else
                      "; no teleport event within the window"),)))
    return out


# ── archive ─────────────────────────────────────────────────────────────────

def write_archive(records: Sequence[NetcodeAnomaly], path: Any) -> int:
    """JSON Lines, one record per line, sorted by id for stable diffs."""
    from pathlib import Path
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = sorted(json.dumps(r.to_dict(), sort_keys=True, default=_jsonable)
                   for r in records)
    p.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return len(lines)
