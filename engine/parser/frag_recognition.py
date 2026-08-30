"""Full recognition taxonomy for recorder frags -- wraps frag_classify.

Takes the parsed demo (demo_parse.DM73Parser.parse() output) plus the tag
layer from frag_classify.classify() and produces, per recorder frag:

  CLASSES      named recognition classes with per-class confidence + detail
  ATTRIBUTES   raw numeric measurements (distance, air height, speeds, ...)
  COMPONENTS   per-dimension scores that compose the highlight_score
  REASONS      human-readable list explaining every point awarded

HONESTY CONTRACT (user mandate, non-negotiable):
  * DIRECT_ROCKET is CONFIRMED from MOD alone -- MOD 6 (MOD_ROCKET) is a
    direct hit by definition; MOD 7 is splash. No inference involved.
  * LG accuracy is the server scoreboard's OVERALL accuracy -- QL's CA
    scoreboard has no per-weapon breakdown. Every LG label says so.
  * PIXEL_SHOT stays _CANDIDATE: distance + entity-stream visibility are
    evidence, not visual verification.
  * PREDICTION classes are CANDIDATES -- the geometric preshot signature is
    real but a PVS trace is not computed.
  * visibility_ms is entity-stream PRESENCE: an entity appearing in the
    recorder's client snapshots IS PVS-visibility evidence (the server only
    sends entities the client could see), but gaps can also come from the
    entity simply not changing. It is stored when computable and labeled.

Confidence ladder (mapped from frag_classify's solid/proxy/needs_data):
  CONFIRMED       derived from a recorded fact that admits no other reading
                  (a MOD id, groundEntityNum from the engine itself)
  HIGH            frag_classify SOLID -- recorded state, minimal inference
  MEDIUM          frag_classify PROXY -- measured, but through a stand-in
  LOW_CANDIDATE   heuristic or partial data; needs eyes before trusting
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Sequence

import frag_classify as fc
from frag_classify import (  # noqa: F401  (re-exported for callers)
    GRENADE, RAIL, ROCKET, SHAFT, Timeline,
    W_GRENADE, W_GRENADE_SPLASH, W_RAILGUN, W_ROCKET, W_ROCKET_SPLASH,
)

# ── confidence ladder ───────────────────────────────────────────────────────
CONFIRMED = "CONFIRMED"
HIGH = "HIGH"
MEDIUM = "MEDIUM"
LOW_CANDIDATE = "LOW_CANDIDATE"

_CONF_MAP = {fc.SOLID: HIGH, fc.PROXY: MEDIUM, fc.NEEDS_DATA: LOW_CANDIDATE}


def map_confidence(classify_conf: str) -> str:
    """frag_classify solid/proxy/needs_data -> recognition ladder."""
    return _CONF_MAP.get(classify_conf, LOW_CANDIDATE)


# ── thresholds ──────────────────────────────────────────────────────────────
MEANINGFUL_AIR_HEIGHT = 90.0    # a real launch, not the tail of a strafe hop
TRIVIAL_AIR_HEIGHT = fc.AIRSHOT_CLEARANCE   # below this classify already said no
FLICK_MIN_DPS = 220.0           # deg/s -- below this it's smooth tracking
VIS_GAP_MS = 700                # entity-row gap that breaks a presence run
VIS_SHORT_MS = 1200             # visible less than this before a long-range
                                # kill = the hard part of a pixel shot
CONSEC_RAIL_WINDOW_MS = 6000    # back-to-back rails
MULTIKILL_CHAIN_GAP_MS = fc.MULTIKILL_WINDOW_MS   # 3000: chain link, not sliding
LG_TRACK_WINDOW_MS = 1000
LG_TRACK_ON_AXIS_DEG = 15.0
LG_TRACK_MIN_SAMPLES = 4
LG_TRACK_MIN_MOVE = 200.0       # victim displacement (units) over the window
# Demos replay the same obituary event multiple times in bursts (observed:
# one victim "killed" 10x at 25 ms intervals -- event-sequence duplicates,
# not ten frags). A player cannot die twice inside respawn time, so a repeat
# (killer, victim) obituary this close is the SAME kill and must collapse
# before multikill / consecutive-rail counting, or an artifact scores 22.
DUPLICATE_OBITUARY_MS = 1000


@dataclass
class RecognizedFrag:
    """One recorder frag with its full recognition record."""
    demo_name: str
    time_ms: int
    round: int
    killer: int
    victim: int
    weapon: int
    weapon_name: str
    classes: list[dict] = field(default_factory=list)      # {name, confidence, detail}
    attributes: dict[str, Any] = field(default_factory=dict)
    components: dict[str, float] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)
    highlight_score: float = 0.0

    @property
    def class_names(self) -> list[str]:
        return [c["name"] for c in self.classes]

    def add_class(self, name: str, confidence: str, detail: str = "") -> None:
        if name not in self.class_names:
            self.classes.append({"name": name, "confidence": confidence,
                                 "detail": detail})

    def add_score(self, component: str, value: float, reason: str) -> None:
        if value <= 0:
            return
        self.components[component] = round(
            self.components.get(component, 0.0) + value, 3)
        self.reasons.append(reason)
        self.highlight_score = round(self.highlight_score + value, 3)


COMPONENT_NAMES = ["multikill_score", "air_score", "accuracy_score",
                   "flick_score", "distance_score", "visibility_difficulty",
                   "weapon_combo_score", "prediction_score", "movement_score"]


# ── measurement helpers ─────────────────────────────────────────────────────

def flick_attributes(tl: Timeline, killer: int, t_ms: int) -> dict | None:
    """Measured yaw sweep in the pre-kill window.

    Returns {flick_degrees, flick_duration_ms, deg_per_sec} or None when
    fewer than two yaw samples exist. Duration is first->last sample time,
    so deg_per_sec is the average rate over the actual sweep, not the
    nominal window.
    """
    rows = [r for r in tl.window(killer, t_ms - fc.FLICK_WINDOW_MS, t_ms)
            if r.get("angle_yaw") is not None]
    if len(rows) < 2:
        return None
    sweep = 0.0
    for a, b in zip(rows, rows[1:]):
        d = abs((b["angle_yaw"] - a["angle_yaw"] + 180.0) % 360.0 - 180.0)
        sweep += d
    dur = (rows[-1].get("server_time_ms") or 0) - (rows[0].get("server_time_ms") or 0)
    if dur <= 0:
        return None
    return {"flick_degrees": round(sweep, 1),
            "flick_duration_ms": int(dur),
            "deg_per_sec": round(sweep / dur * 1000.0, 1)}


def visibility_ms(tl: Timeline, victim: int, t_ms: int,
                  max_back_ms: int = 15000) -> int | None:
    """How long the victim entity was continuously present before the kill.

    Entity presence in a client demo snapshot IS PVS-visibility evidence:
    the server only transmits entities the client could potentially see.
    A gap > VIS_GAP_MS in the victim's entity rows breaks the run (either
    they left PVS or their state stopped changing -- we cannot distinguish,
    which is why pixel-shot classification built on this stays _CANDIDATE).
    Returns None when the victim has no row near the kill at all.
    """
    rows = [r.get("server_time_ms") or 0
            for r in tl.window(victim, t_ms - max_back_ms, t_ms)]
    if not rows:
        return None
    rows.sort(reverse=True)          # walk back from the kill
    if t_ms - rows[0] > VIS_GAP_MS:
        return None                  # no presence at the kill itself
    run_start = rows[0]
    for prev, older in zip(rows, rows[1:]):
        if prev - older > VIS_GAP_MS:
            break
        run_start = older
    return int(t_ms - run_start)


def _victim_motion(tl: Timeline, victim: int, t_ms: int) -> dict:
    """Speed / vertical speed / air height of the victim at the kill."""
    out: dict[str, float] = {}
    s = tl.at(victim, t_ms)
    if not s:
        return out
    vx, vy, vz = s.get("vel_x"), s.get("vel_y"), s.get("vel_z")
    if vx is not None and vy is not None:
        out["victim_speed"] = round(
            math.sqrt(vx * vx + vy * vy + (vz or 0.0) ** 2), 1)
    if vz is not None:
        out["victim_vertical_speed"] = round(vz, 1)
    z = s.get("origin_z")
    floor = tl.recent_floor(victim, t_ms)
    if z is not None and floor is not None:
        out["victim_air_height"] = round(z - floor, 1)
    return out


def lg_tracking(tl: Timeline, killer: int, victim: int,
                t_ms: int) -> tuple[bool, str]:
    """Beam-window continuity: aim stayed on a MOVING victim before the kill.

    Requires >= LG_TRACK_MIN_SAMPLES paired samples in the pre-kill window
    where killer aim is within LG_TRACK_ON_AXIS_DEG of the victim, while the
    victim displaced >= LG_TRACK_MIN_MOVE units. That is tracking, not a
    parked crosshair. Returns (tracked, detail).
    """
    t0 = t_ms - LG_TRACK_WINDOW_MS
    k_rows = [r for r in tl.window(killer, t0, t_ms)
              if r.get("angle_yaw") is not None]
    v_rows = [r for r in tl.window(victim, t0, t_ms)
              if r.get("origin_x") is not None]
    if len(k_rows) < LG_TRACK_MIN_SAMPLES or len(v_rows) < 2:
        return False, ""

    # pair each killer sample with the nearest victim sample in time
    on_axis = total = 0
    for k in k_rows:
        kt = k.get("server_time_ms") or 0
        v = min(v_rows, key=lambda r: abs((r.get("server_time_ms") or 0) - kt))
        if abs((v.get("server_time_ms") or 0) - kt) > 250:
            continue
        ang = fc._angle_to_target(k, v)
        if ang is None:
            continue
        total += 1
        if ang <= LG_TRACK_ON_AXIS_DEG:
            on_axis += 1
    if total < LG_TRACK_MIN_SAMPLES or on_axis / total < 0.75:
        return False, ""

    try:
        move = math.dist(
            (v_rows[0]["origin_x"], v_rows[0]["origin_y"], v_rows[0]["origin_z"]),
            (v_rows[-1]["origin_x"], v_rows[-1]["origin_y"], v_rows[-1]["origin_z"]))
    except (KeyError, TypeError):
        return False, ""
    if move < LG_TRACK_MIN_MOVE:
        return False, ""
    return True, (f"aim on a moving victim {on_axis}/{total} samples over "
                  f"{LG_TRACK_WINDOW_MS} ms, victim moved {move:.0f}u")


def multikill_chains(frags: Sequence[fc.Frag]) -> dict[int, dict]:
    """CHAIN-linked multikills: consecutive kills each <= gap apart.

    A sliding count merges across long downtime ("3 kills in the last 3 s"
    is true for the third kill of two separate doubles). A chain does not:
    the link BETWEEN successive kills must be <= MULTIKILL_CHAIN_GAP_MS.
    Returns {frag time_ms of the chain's LAST kill: chain info} so the
    closing kill carries the class.
    """
    out: dict[int, dict] = {}
    ordered = sorted(frags, key=lambda f: f.time_ms)
    chain: list[fc.Frag] = []
    for f in ordered:
        if chain and f.time_ms - chain[-1].time_ms <= MULTIKILL_CHAIN_GAP_MS:
            chain.append(f)
        else:
            if len(chain) >= 2:
                out[chain[-1].time_ms] = _chain_info(chain)
            chain = [f]
    if len(chain) >= 2:
        out[chain[-1].time_ms] = _chain_info(chain)
    return out


def _chain_info(chain: list[fc.Frag]) -> dict:
    gaps = [b.time_ms - a.time_ms for a, b in zip(chain, chain[1:])]
    return {
        "count": len(chain),
        "duration_ms": chain[-1].time_ms - chain[0].time_ms,
        "weapons": [f.weapon_name for f in chain],
        "victims": [f.victim for f in chain],
        "gaps_ms": gaps,
    }


def _drop_duplicate_obituaries(frags: list[fc.Frag]) -> list[fc.Frag]:
    """Collapse replayed obituary events -- see DUPLICATE_OBITUARY_MS."""
    out: list[fc.Frag] = []
    last: dict[tuple[int, int], int] = {}
    for f in sorted(frags, key=lambda f: f.time_ms):
        key = (f.killer, f.victim)
        prev = last.get(key)
        if prev is not None and f.time_ms - prev <= DUPLICATE_OBITUARY_MS:
            last[key] = f.time_ms          # extend the burst window
            continue
        last[key] = f.time_ms
        out.append(f)
    return out


# ── main entry point ────────────────────────────────────────────────────────

def recognize(parsed: dict, player: int | None = None,
              demo_name: str = "") -> list[RecognizedFrag]:
    """Full recognition pass over the RECORDER's frags in one parsed demo.

    `player` defaults to the demo taker (parser client identity -- the
    playerstate stream only ever carries whoever recorded, never a name
    match).
    """
    if player is None:
        player = fc.demo_taker(parsed)
    tagged = _drop_duplicate_obituaries(fc.classify(parsed, player=player))
    tl = Timeline(list(parsed.get("entities") or [])
                  + list(parsed.get("snapshots") or []))
    acc = fc.Accuracy(parsed.get("accuracy", []))

    chains = multikill_chains(tagged)
    times = [f.time_ms for f in tagged]

    out: list[RecognizedFrag] = []
    for i, f in enumerate(tagged):
        r = RecognizedFrag(
            demo_name=demo_name, time_ms=f.time_ms, round=f.round,
            killer=f.killer, victim=f.victim,
            weapon=f.weapon, weapon_name=f.weapon_name)
        tags = {t.name: t for t in f.tags}

        # ---- raw attributes ------------------------------------------------
        attrs = r.attributes
        d = fc._distance(tl, f.killer, f.victim, f.time_ms)
        if d is not None:
            attrs["distance"] = round(d, 1)
        attrs.update(_victim_motion(tl, f.victim, f.time_ms))
        if f.killer_speed is not None:
            attrs["killer_speed"] = round(f.killer_speed, 1)
        vis = visibility_ms(tl, f.victim, f.time_ms)
        if vis is not None:
            attrs["visibility_ms"] = vis
        fl = flick_attributes(tl, f.killer, f.time_ms)
        if fl:
            attrs.update(fl)
        if i > 0:
            attrs["time_to_prev_kill_ms"] = f.time_ms - times[i - 1]
        if i + 1 < len(times):
            attrs["time_to_next_kill_ms"] = times[i + 1] - f.time_ms

        air_tag = tags.get("airshot")
        air_h = attrs.get("victim_air_height")

        # ---- DIRECT_ROCKET: MOD 6 is a direct hit by definition -----------
        if f.weapon == W_ROCKET:
            r.add_class("DIRECT_ROCKET", CONFIRMED,
                        "MOD_ROCKET (6): direct hit, splash is MOD 7")
            r.add_score("accuracy_score", 1.0, "+ direct rocket (MOD-confirmed)")
        # No DIRECT_LIKELY: splash MOD carries no evidence of near-directness
        # we can measure, and faking it violates the honesty contract.

        # ---- AIR_ROCKET / AIR_GRENADE --------------------------------------
        if air_tag and f.weapon in ROCKET:
            conf = map_confidence(air_tag.confidence)
            meaningful = air_h is not None and air_h >= MEANINGFUL_AIR_HEIGHT
            detail = air_tag.detail + (" (meaningful air)" if meaningful
                                       else " (low air)")
            r.add_class("AIR_ROCKET", conf, detail)
            base = 2.0 if not meaningful else 3.5
            if f.weapon == W_ROCKET:
                base += 1.0          # direct hit on an airborne target
            r.add_score("air_score", base,
                        f"+ air rocket (h={air_h:.0f})" if air_h is not None
                        else "+ air rocket")
        if air_tag and f.weapon in GRENADE:
            conf = map_confidence(air_tag.confidence)
            direct = f.weapon == W_GRENADE
            detail = air_tag.detail + ("; MOD_GRENADE direct" if direct
                                       else "; grenade splash")
            r.add_class("AIR_GRENADE", conf, detail)
            base = 3.0 + (1.5 if direct else 0.0)
            if air_h is not None and air_h >= MEANINGFUL_AIR_HEIGHT:
                base += 1.0
            r.add_score("air_score", base,
                        f"+ air grenade{' direct' if direct else ''}"
                        + (f" (h={air_h:.0f})" if air_h is not None else ""))
        vvs = attrs.get("victim_vertical_speed")
        if air_tag and vvs is not None and abs(vvs) >= 250:
            r.add_score("air_score", 0.5, f"+ victim falling/rising {vvs:.0f} ups")

        # ---- FLICK_SHOT ----------------------------------------------------
        if "big_flick" in tags and fl and fl["deg_per_sec"] >= FLICK_MIN_DPS:
            r.add_class("FLICK_SHOT", HIGH,
                        f"{fl['flick_degrees']:.0f} deg in "
                        f"{fl['flick_duration_ms']} ms "
                        f"({fl['deg_per_sec']:.0f} deg/s)")
            r.add_score("flick_score",
                        min(3.0, fl["deg_per_sec"] / 200.0),
                        f"+ flick {fl['flick_degrees']:.0f} deg @ "
                        f"{fl['deg_per_sec']:.0f} deg/s")
        # A big sweep at low rate is smooth tracking -- deliberately no class.

        # ---- PIXEL_SHOT_CANDIDATE (data-stage only) ------------------------
        if d is not None and f.weapon in RAIL and d >= fc.PIXEL_DIST_MIN:
            detail = f"{d:.0f} units"
            if vis is not None:
                detail += f"; victim in entity stream {vis} ms before kill"
            r.add_class("PIXEL_SHOT_CANDIDATE", LOW_CANDIDATE,
                        detail + " (needs visual verification)")
            r.add_score("distance_score", min(3.0, d / 1500.0),
                        f"+ long rail ({d:.0f}u)")
            if vis is not None and vis <= VIS_SHORT_MS:
                r.add_score("visibility_difficulty",
                            min(3.0, (VIS_SHORT_MS - vis) / 400.0 + 1.0),
                            f"+ visible only {vis} ms before the kill")
        elif d is not None and f.weapon in RAIL:
            r.add_score("distance_score", min(1.5, d / 1500.0),
                        f"+ rail range ({d:.0f}u)") if d >= 800 else None

        # ---- RAIL precision family -----------------------------------------
        if f.weapon in RAIL:
            r.add_class("RAIL_FRAG", CONFIRMED, "MOD_RAILGUN")
            if air_tag:
                r.add_class("RAIL_AIR", map_confidence(air_tag.confidence),
                            f"rail on airborne victim; {air_tag.detail}")
                r.add_score("air_score", 2.5, "+ air rail")
            if "FLICK_SHOT" in r.class_names:
                r.add_class("RAIL_FLICK", HIGH, "flick rail")
                r.add_score("flick_score", 0.5, "+ flick was a rail")
            prev_rails = [g for g in tagged[:i]
                          if g.weapon in RAIL
                          and 0 < f.time_ms - g.time_ms <= CONSEC_RAIL_WINDOW_MS]
            if prev_rails:
                n = len(prev_rails) + 1
                r.add_class("RAIL_CONSECUTIVE", HIGH,
                            f"{n} rails within {CONSEC_RAIL_WINDOW_MS} ms")
                r.add_score("accuracy_score", 0.75 * len(prev_rails),
                            f"+ {n} consecutive rails")

        # ---- LG: high accuracy / tracking ----------------------------------
        a = acc.at(f.killer, f.time_ms)
        if f.weapon in SHAFT:
            if "high_acc_shaft" in tags and a is not None:
                r.add_class(
                    "LG_HIGH_ACCURACY", HIGH,
                    f"{a:.0f}% OVERALL accuracy (server scoreboard; QL has "
                    "no per-weapon breakdown -- this is not LG-specific)")
                r.add_score("accuracy_score", min(3.0, (a - 30.0) / 10.0),
                            f"+ {a:.0f}% overall acc on an LG kill")
            tracked, why = lg_tracking(tl, f.killer, f.victim, f.time_ms)
            if tracked:
                r.add_class("LG_TRACKING", MEDIUM,
                            why + " (entity-stream continuity, not beam data)")
                r.add_score("accuracy_score", 1.5, "+ LG tracked a moving victim")

        # ---- MULTIKILL (chain-based, never merged across downtime) ---------
        chain = chains.get(f.time_ms)
        if chain:
            n = chain["count"]
            dur = chain["duration_ms"] / 1000.0
            name = {2: "MULTIKILL_DOUBLE", 3: "MULTIKILL_TRIPLE",
                    4: "MULTIKILL_QUAD"}.get(n, "MULTIKILL_MEGA")
            r.add_class(name, HIGH,
                        f"{n} kills / {dur:.1f}s, weapons="
                        + "+".join(chain["weapons"])
                        + f", max gap {max(chain['gaps_ms'])} ms")
            r.attributes["multikill"] = chain
            r.add_score("multikill_score", 1.5 * (n - 1),
                        f"+ {n} kills / {dur:.1f}s")

        # ---- WEAPON_COMBO --------------------------------------------------
        for combo in ("rocket_rail", "shaft_rail", "shaft_rocket",
                      "rocket_shaft"):
            if combo in tags:
                r.add_class("WEAPON_COMBO", HIGH,
                            f"{combo}: {tags[combo].detail}")
                r.add_score("weapon_combo_score", 1.5,
                            f"+ weapon combo {combo}")

        # ---- PREDICTION candidates (rocket/grenade preshot) ----------------
        if "preshot" in tags and f.weapon in (ROCKET | GRENADE):
            kind = "grenade" if f.weapon in GRENADE else "rocket"
            r.add_class("PREDICTION_CANDIDATE", LOW_CANDIDATE,
                        f"{kind} preshot: {tags['preshot'].detail} "
                        "(geometric signature only, no PVS trace)")
            r.add_score("prediction_score", 1.5, f"+ predicted {kind}")

        # ---- movement: killer air + speed ----------------------------------
        if "airborne_kill" in tags:
            r.add_score("movement_score", 1.5,
                        "+ killer airborne at the kill")
        spd = f.killer_speed
        if spd is not None and spd >= fc.VERY_FAST_UPS:
            r.add_score("movement_score", 1.5, f"+ killer at {spd:.0f} ups")
        elif spd is not None and spd >= fc.FAST_UPS:
            r.add_score("movement_score", 0.75, f"+ killer at {spd:.0f} ups")

        out.append(r)
    return out


def summary(recs: Sequence[RecognizedFrag]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in recs:
        for c in r.classes:
            counts[c["name"]] = counts.get(c["name"], 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: -kv[1]))
