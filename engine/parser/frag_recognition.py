"""Full recognition taxonomy for recorder frags -- wraps frag_classify.

Takes the parsed demo (demo_parse.DM73Parser.parse() output) plus the tag
layer from frag_classify.classify() and produces, per recorder frag:

  CLASSES      named recognition classes with per-class confidence + detail
  ATTRIBUTES   raw numeric measurements (distance, air height, speeds, ...)
  COMPONENTS   per-dimension scores that compose the highlight_score
  REASONS      human-readable list explaining every point awarded

TAXONOMY v2 (pTn.Tr4sH skill taxonomy, 2026-08-30) adds the movement family
(speed percentile labels, rocket-jump entry, strafe chains, target transfers),
context classes (low-health wins, fast weapon switches), penalties, and
archive-normalized scoring via recognition_norms (rule L: percentile labels
come from the archive distribution, never hardcoded speeds; without a norms
table the built-in thresholds apply and every reason that used them says
"provisional").

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
  * ROCKET_JUMP_* is MEDIUM: a +z velocity step is the observable half of a
    self-rocket impulse; damage attribution is not recorded.
  * REACTION_SHOT stays _CANDIDATE at stage 1: real reaction_ms needs the
    stage-2 visibility trace -- the attribute ships as a None placeholder.
  * "Cleanup kill" (victim already damaged by someone ELSE) is NOT derivable
    from this data -- obituaries carry no damage-attribution history. No
    penalty is fabricated for it.
  * round_end_helpless needs round-deciding context that only the clutch
    join (clutch_recorder.csv, downstream) carries -- not applied here.

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
try:
    from engine.parser import round_context as rc
except ImportError:                                         # flat import
    import round_context as rc
from frag_classify import (  # noqa: F401  (re-exported for callers)
    GRENADE, RAIL, ROCKET, SHAFT, Timeline,
    W_GRENADE, W_GRENADE_SPLASH, W_RAILGUN, W_ROCKET, W_ROCKET_SPLASH,
    W_SHOTGUN,
)

# Bump on any taxonomy/scoring change so the corpus scan recomputes.
# v4: ROUND_OPENING_FRAG and the round countdown window.
# v3: round/team context traits. Rounds reconstructed from the round
# configstrings (the native counter over-reports), round windows run one
# snapshot past the end command (the round-winning frag lands 25ms after
# it), and Clan Arena alive-counts come from the round's own obituaries.
RECOGNITION_VERSION = 4

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

# ── v2: movement / context thresholds ───────────────────────────────────────
# PROVISIONAL speed cut-offs, used ONLY when no archive norms table exists.
# With norms present the labels are percentile-driven: FAST>p90, VERY_FAST
# >p97, EXTREME_SPEED>p99 of the archive attacker-speed distribution.
PROV_FAST_UPS = 700.0
PROV_VERY_FAST_UPS = 1000.0
PROV_EXTREME_UPS = 1300.0
PROV_RAPID_KPS = 1.0            # kills/second inside a chain (provisional p90)

TRANSFER_MAX_GAP_MS = 2500      # consecutive kills this close = a transfer
TRANSFER_MIN_DEG = 40.0         # angular change between victim directions
ROCKETJUMP_IMPULSE_UPS = 600.0  # +z velocity step = the observable self-rocket
ROCKETJUMP_LOOKBACK_MS = 1500
ROCKETJUMP_STEP_MAX_MS = 600    # the step must happen between close samples
SWITCH_KILL_MAX_MS = 800        # weapon-change -> kill gap
SWITCH_LOOKBACK_MS = 2500
HEALTH_WINDOW_MS = 2000
LOW_HEALTH_MAX = 25
LAST_HP_MAX = 10
STATIONARY_UPS = 40.0           # victim slower than this = parked
STATIONARY_PAIN_LOOKBACK_MS = 3000
REACTION_VIS_MAX_MS = 400       # entity appears this late -> reaction candidate
POPUP_WINDOW_MS = 1200          # rocket-pop -> finisher window
POPUP_RISE_VZ = 200.0           # victim heading up = was popped
STRAFE_WINDOW_MS = 3000
STRAFE_MIN_DIR_CHANGES = 3
STRAFE_PROV_MEAN_UPS = 450.0    # provisional; norms attacker_speed p75 wins
VERTICAL_WINDOW_MS = 2000
VERTICAL_MIN_DZ = 250.0
DODGE_WINDOW_MS = 1000
DODGE_MIN_DEG = 90.0
DODGE_MIN_UPS = 250.0
TURNAROUND_WINDOW_MS = 1200
TURNAROUND_MIN_DEG = 120.0

# Named finisher pairs (prev weapon family -> kill weapon family).
_FINISHER_PAIRS = {
    ("SHAFT", "ROCKET"): "lg_rocket",
    ("SHAFT", "RAIL"): "lg_rail",
    ("ROCKET", "RAIL"): "rocket_rail",
    ("RAIL", "ROCKET"): "rail_rocket",
}

_MULTIKILL_NAMES = {2: "MULTIKILL_DOUBLE", 3: "MULTIKILL_TRIPLE",
                    4: "MULTIKILL_QUAD", 5: "MULTIKILL_PENTA",
                    6: "MULTIKILL_HEXA", 7: "MULTIKILL_HEPTA",
                    8: "MULTIKILL_OCTA"}


def _weapon_family(mod: int) -> str | None:
    if mod in ROCKET:
        return "ROCKET"
    if mod in RAIL:
        return "RAIL"
    if mod in SHAFT:
        return "SHAFT"
    if mod in GRENADE:
        return "GRENADE"
    return None


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

    def add_penalty(self, value: float, reason: str) -> None:
        """Negative score component (rule K). `value` is the positive
        magnitude; the reason text must start with '- ' and say why."""
        if value <= 0:
            return
        self.components["penalty_score"] = round(
            self.components.get("penalty_score", 0.0) - value, 3)
        self.reasons.append(reason)
        self.highlight_score = round(self.highlight_score - value, 3)


COMPONENT_NAMES = ["speed_score", "precision_score", "flick_score",
                   "visibility_score", "air_score", "prediction_score",
                   "tracking_score", "multikill_score", "combo_score",
                   "clutch_score", "movement_score", "drama_score",
                   "penalty_score"]


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


def _attacker_motion(tl: Timeline, killer: int, t_ms: int) -> dict:
    """Horizontal + total speed of the attacker at the kill.

    Recorder velocity lives in the PLAYERSTATE stream (a client never
    receives its own entity); other killers come from the entity stream.
    Timeline merges both, so tl.at() finds whichever exists.
    """
    out: dict[str, float] = {}
    s = tl.at(killer, t_ms)
    if not s:
        return out
    vx, vy, vz = s.get("vel_x"), s.get("vel_y"), s.get("vel_z")
    if vx is not None and vy is not None:
        out["attacker_horizontal_speed"] = round(math.sqrt(vx * vx + vy * vy), 1)
        out["attacker_speed"] = round(
            math.sqrt(vx * vx + vy * vy + (vz or 0.0) ** 2), 1)
    return out


def speed_tier(value: float | None, norms=None,
               metric: str = "attacker_speed"
               ) -> tuple[str | None, float | None, bool]:
    """Percentile-based speed label (rule L).

    Returns (label, percentile, provisional). Labels: FAST (>p90),
    VERY_FAST (>p97), EXTREME_SPEED (>p99) of the ARCHIVE distribution.
    Without a norms table the provisional ups thresholds apply and
    `provisional` is True so every reason can say so.
    """
    if value is None:
        return None, None, False
    if norms is not None and norms.has(metric):
        pct = norms.percentile_of(metric, value)
        if pct is None:
            return None, None, False
        if pct >= 99.0:
            return "EXTREME_SPEED", pct, False
        if pct >= 97.0:
            return "VERY_FAST", pct, False
        if pct >= 90.0:
            return "FAST", pct, False
        return None, pct, False
    if value >= PROV_EXTREME_UPS:
        return "EXTREME_SPEED", None, True
    if value >= PROV_VERY_FAST_UPS:
        return "VERY_FAST", None, True
    if value >= PROV_FAST_UPS:
        return "FAST", None, True
    return None, None, True


def rocket_jump_impulse(tl: Timeline, killer: int, t_ms: int
                        ) -> tuple[float, int] | None:
    """Observable self-rocket signature: a large +z velocity step.

    Scans the attacker's rows in the ROCKETJUMP_LOOKBACK_MS pre-kill window
    for a step of >= ROCKETJUMP_IMPULSE_UPS between samples close in time.
    Returns (step_ups, step_time_ms) or None. This is the observable HALF
    of a rocket jump -- damage attribution is not recorded, hence MEDIUM.
    """
    rows = [r for r in tl.window(killer, t_ms - ROCKETJUMP_LOOKBACK_MS, t_ms)
            if r.get("vel_z") is not None]
    best = None
    for a, b in zip(rows, rows[1:]):
        dt = (b.get("server_time_ms") or 0) - (a.get("server_time_ms") or 0)
        if dt <= 0 or dt > ROCKETJUMP_STEP_MAX_MS:
            continue
        step = b["vel_z"] - a["vel_z"]
        if step >= ROCKETJUMP_IMPULSE_UPS and b["vel_z"] > 0:
            if best is None or step > best[0]:
                best = (round(step, 1), int(b.get("server_time_ms") or 0))
    return best


def weapon_switch_gap(tl: Timeline, killer: int, t_ms: int) -> int | None:
    """ms between the attacker's last weapon change and the kill, or None."""
    rows = [r for r in tl.window(killer, t_ms - SWITCH_LOOKBACK_MS, t_ms)
            if r.get("weapon") is not None]
    if len(rows) < 2:
        return None
    final = rows[-1]["weapon"]
    change_t = None
    for a, b in zip(rows, rows[1:]):
        if b["weapon"] == final and a["weapon"] != final:
            change_t = b.get("server_time_ms") or 0
    if change_t is None:
        return None
    return int(t_ms - change_t)


def strafe_chain(tl: Timeline, killer: int, t_ms: int,
                 min_mean_ups: float) -> dict | None:
    """Sustained speed + direction changes + hop pattern over the pre-kill 3s.

    Direction changes are sign flips of the yaw delta (>3 deg to ignore
    jitter); the ground-contact pattern is airborne-flag transitions where
    the entity stream carries them, else vel_z sign flips (playerstate).
    Proxy pattern -> MEDIUM.
    """
    rows = tl.window(killer, t_ms - STRAFE_WINDOW_MS, t_ms)
    speeds = []
    for r in rows:
        vx, vy = r.get("vel_x"), r.get("vel_y")
        if vx is not None and vy is not None:
            speeds.append(math.sqrt(vx * vx + vy * vy))
    if len(speeds) < 4:
        return None
    mean_speed = sum(speeds) / len(speeds)
    if mean_speed < min_mean_ups:
        return None

    yaws = [r["angle_yaw"] for r in rows if r.get("angle_yaw") is not None]
    dir_changes = 0
    last_sign = 0
    for a, b in zip(yaws, yaws[1:]):
        d = (b - a + 180.0) % 360.0 - 180.0
        if abs(d) < 3.0:
            continue
        sign = 1 if d > 0 else -1
        if last_sign and sign != last_sign:
            dir_changes += 1
        last_sign = sign
    if dir_changes < STRAFE_MIN_DIR_CHANGES:
        return None

    hops = 0
    airs = [r.get("airborne") for r in rows if r.get("airborne") is not None]
    if len(airs) >= 2:
        hops = sum(1 for a, b in zip(airs, airs[1:]) if a != b)
    else:
        vzs = [r["vel_z"] for r in rows if r.get("vel_z")]
        hops = sum(1 for a, b in zip(vzs, vzs[1:])
                   if (a > 0) != (b > 0) and abs(a) > 50 and abs(b) > 50)
    if hops < 2:
        return None
    return {"strafe_mean_speed": round(mean_speed, 1),
            "strafe_dir_changes": dir_changes,
            "strafe_hop_transitions": hops}


def vertical_travel(tl: Timeline, killer: int, t_ms: int) -> float | None:
    """|dz| of the attacker across the pre-kill window."""
    zs = [r["origin_z"] for r in tl.window(killer, t_ms - VERTICAL_WINDOW_MS,
                                           t_ms)
          if r.get("origin_z") is not None]
    if len(zs) < 2:
        return None
    return round(max(zs) - min(zs), 1)


def velocity_direction_change(tl: Timeline, client: int, t_ms: int,
                              window_ms: int = DODGE_WINDOW_MS
                              ) -> float | None:
    """Largest change (deg) in the horizontal VELOCITY heading pre-kill,
    considering only samples moving faster than DODGE_MIN_UPS."""
    heads = []
    for r in tl.window(client, t_ms - window_ms, t_ms):
        vx, vy = r.get("vel_x"), r.get("vel_y")
        if vx is None or vy is None:
            continue
        if math.sqrt(vx * vx + vy * vy) < DODGE_MIN_UPS:
            continue
        heads.append(math.degrees(math.atan2(vy, vx)))
    if len(heads) < 2:
        return None
    best = 0.0
    for a, b in zip(heads, heads[1:]):
        d = abs((b - a + 180.0) % 360.0 - 180.0)
        best = max(best, d)
    return round(best, 1)


def yaw_turn(tl: Timeline, client: int, t_ms: int,
             window_ms: int = TURNAROUND_WINDOW_MS) -> float | None:
    """Net yaw change (deg, shortest arc) first->last over the window."""
    yaws = [r["angle_yaw"] for r in tl.window(client, t_ms - window_ms, t_ms)
            if r.get("angle_yaw") is not None]
    if len(yaws) < 2:
        return None
    return round(abs((yaws[-1] - yaws[0] + 180.0) % 360.0 - 180.0), 1)


def min_health(tl: Timeline, client: int, t_ms: int) -> int | None:
    """Lowest recorded health in the pre-kill window (recorder playerstate
    only -- the entity stream carries no health, so non-recorder killers
    return None)."""
    hs = [r["health"] for r in tl.window(client, t_ms - HEALTH_WINDOW_MS, t_ms)
          if r.get("health") is not None]
    return int(min(hs)) if hs else None


def transfer_angle(tl: Timeline, killer: int, prev_victim: int,
                   prev_t: int, victim: int, t_ms: int) -> float | None:
    """Angle (deg) between attacker->victim directions of two kills."""
    k1, v1 = tl.at(killer, prev_t), tl.at(prev_victim, prev_t)
    k2, v2 = tl.at(killer, t_ms), tl.at(victim, t_ms)
    if not all((k1, v1, k2, v2)):
        return None

    def _dir(k, v):
        try:
            d = (v["origin_x"] - k["origin_x"], v["origin_y"] - k["origin_y"],
                 v["origin_z"] - k["origin_z"])
        except (KeyError, TypeError):
            return None
        n = math.sqrt(sum(c * c for c in d))
        return None if n < 1e-6 else (d[0] / n, d[1] / n, d[2] / n)

    a, b = _dir(k1, v1), _dir(k2, v2)
    if a is None or b is None:
        return None
    dot = max(-1.0, min(1.0, sum(x * y for x, y in zip(a, b))))
    return round(math.degrees(math.acos(dot)), 1)


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
    dur = chain[-1].time_ms - chain[0].time_ms
    info = {
        "count": len(chain),
        "duration_ms": dur,
        "weapons": [f.weapon_name for f in chain],
        "victims": [f.victim for f in chain],
        "gaps_ms": gaps,
        "kills_per_second": round(len(chain) / (dur / 1000.0), 2)
        if dur > 0 else None,
    }
    speeds = [f.killer_speed for f in chain if f.killer_speed is not None]
    if speeds:
        info["speed_mean"] = round(sum(speeds) / len(speeds), 1)
        info["speed_min"] = round(min(speeds), 1)
        info["speed_peak"] = round(max(speeds), 1)
        info["speed_samples"] = len(speeds)
    return info


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


def _event_times(parsed: dict, ev_type: str,
                 client: int | None = None) -> list[int]:
    """Times of a given event type (optionally for one client)."""
    out = []
    for e in parsed.get("events", []):
        if e.get("type") != ev_type:
            continue
        if client is not None:
            c = e.get("client_num")
            if c is None:
                c = e.get("entity_num")
            if c != client:
                continue
        t = e.get("server_time_ms")
        if t is not None:
            out.append(int(t))
    out.sort()
    return out


# ── main entry point ────────────────────────────────────────────────────────

def recognize(parsed: dict, player: int | None = None,
              demo_name: str = "", norms=None) -> list[RecognizedFrag]:
    """Full recognition pass over the RECORDER's frags in one parsed demo.

    `player` defaults to the demo taker (parser client identity -- the
    playerstate stream only ever carries whoever recorded, never a name
    match). `norms` is an optional recognition_norms.Norms table; without
    it the provisional thresholds apply (marked in every reason that
    used them).
    """
    if player is None:
        player = fc.demo_taker(parsed)
    tagged = _drop_duplicate_obituaries(fc.classify(parsed, player=player))
    tl = Timeline(list(parsed.get("entities") or [])
                  + list(parsed.get("snapshots") or []))
    acc = fc.Accuracy(parsed.get("accuracy", []))

    chains = multikill_chains(tagged)
    # Round/team context. Empty when the demo carries no team field --
    # a missing team stays missing rather than becoming a guess.
    ctxs = rc.build_context(parsed, player)
    times = [f.time_ms for f in tagged]
    missile_hits = _event_times(parsed, "missile_hit")
    prov = " [provisional]"   # appended when no norms table backed a label

    # provisional strafe threshold; archive p75 wins when norms exist
    strafe_min = STRAFE_PROV_MEAN_UPS
    if norms is not None and norms.has("attacker_speed"):
        v = norms.value_at("attacker_speed", 75)
        if v is not None:
            strafe_min = v

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
        attrs.update(_attacker_motion(tl, f.killer, f.time_ms))
        if f.killer_speed is not None:
            attrs["killer_speed"] = round(f.killer_speed, 1)
            attrs.setdefault("attacker_speed", round(f.killer_speed, 1))
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

        # speed percentiles stored on EVERY frag when norms exist (rule L)
        atk_speed = attrs.get("attacker_speed")
        vic_speed = attrs.get("victim_speed")
        atk_tier, atk_pct, atk_prov = speed_tier(atk_speed, norms,
                                                 "attacker_speed")
        vic_tier, vic_pct, vic_prov = speed_tier(vic_speed, norms,
                                                 "victim_speed")
        if atk_pct is not None:
            attrs["attacker_speed_percentile"] = atk_pct
        if vic_pct is not None:
            attrs["victim_speed_percentile"] = vic_pct

        air_tag = tags.get("airshot")
        air_h = attrs.get("victim_air_height")

        # ---- DIRECT_ROCKET: MOD 6 is a direct hit by definition -----------
        if f.weapon == W_ROCKET:
            r.add_class("DIRECT_ROCKET", CONFIRMED,
                        "MOD_ROCKET (6): direct hit, splash is MOD 7")
            r.add_score("precision_score", 1.0, "+ direct rocket (MOD-confirmed)")
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
            r.add_score("precision_score", min(3.0, d / 1500.0),
                        f"+ long rail ({d:.0f}u)")
            if vis is not None and vis <= VIS_SHORT_MS:
                r.add_score("visibility_score",
                            min(3.0, (VIS_SHORT_MS - vis) / 400.0 + 1.0),
                            f"+ visible only {vis} ms before the kill")
        elif d is not None and f.weapon in RAIL:
            r.add_score("precision_score", min(1.5, d / 1500.0),
                        f"+ rail range ({d:.0f}u)") if d >= 800 else None

        # ---- REACTION_SHOT_CANDIDATE (stage-2 gated) -----------------------
        # visibility_ms is entity-stream presence; a victim who appears
        # < REACTION_VIS_MAX_MS before a hitscan kill is a reaction-shot
        # CANDIDATE. Real reaction_ms needs the stage-2 visibility trace.
        if (vis is not None and vis < REACTION_VIS_MAX_MS
                and (f.weapon in RAIL or f.weapon == W_SHOTGUN)):
            attrs["reaction_ms"] = None      # stage-2 fills this in
            r.add_class("REACTION_SHOT_CANDIDATE", LOW_CANDIDATE,
                        f"victim in entity stream only {vis} ms before a "
                        f"{f.weapon_name} kill (stage-2 reaction_ms pending)")
            r.add_score("visibility_score", 1.0,
                        f"+ reaction candidate (visible {vis} ms)")

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
                r.add_score("precision_score", 0.75 * len(prev_rails),
                            f"+ {n} consecutive rails")

        # ---- LG: high accuracy / tracking ----------------------------------
        a = acc.at(f.killer, f.time_ms)
        if f.weapon in SHAFT:
            if "high_acc_shaft" in tags and a is not None:
                r.add_class(
                    "LG_HIGH_ACCURACY", HIGH,
                    f"{a:.0f}% OVERALL accuracy (server scoreboard; QL has "
                    "no per-weapon breakdown -- this is not LG-specific)")
                r.add_score("precision_score", min(3.0, (a - 30.0) / 10.0),
                            f"+ {a:.0f}% overall acc on an LG kill")
            tracked, why = lg_tracking(tl, f.killer, f.victim, f.time_ms)
            if tracked:
                r.add_class("LG_TRACKING", MEDIUM,
                            why + " (entity-stream continuity, not beam data)")
                r.add_score("tracking_score", 1.5, "+ LG tracked a moving victim")

        # ---- MULTIKILL (chain-based, never merged across downtime) ---------
        chain = chains.get(f.time_ms)
        if chain:
            n = chain["count"]
            dur = chain["duration_ms"] / 1000.0
            name = _MULTIKILL_NAMES.get(n, "MULTIKILL_MEGA")
            r.add_class(name, HIGH,
                        f"{n} kills / {dur:.1f}s, weapons="
                        + "+".join(chain["weapons"])
                        + f", max gap {max(chain['gaps_ms'])} ms")
            r.attributes["multikill"] = chain
            r.add_score("multikill_score", 1.5 * (n - 1),
                        f"+ {n} kills / {dur:.1f}s")

            # RAPID_MULTIKILL: kills/second, archive-percentile ranked
            kps = chain.get("kills_per_second")
            if kps is not None:
                rapid = False
                if norms is not None and norms.has("chain_kps"):
                    kps_pct = norms.percentile_of("chain_kps", kps)
                    if kps_pct is not None and kps_pct >= 90.0:
                        rapid = True
                        r.add_class("RAPID_MULTIKILL", HIGH,
                                    f"{kps:.2f} kills/s (archive p{kps_pct})")
                        r.add_score("multikill_score", 1.5,
                                    f"+ rapid chain {kps:.2f} kills/s "
                                    f"p{kps_pct} (+1.5)")
                elif kps >= PROV_RAPID_KPS:
                    rapid = True
                    r.add_class("RAPID_MULTIKILL", HIGH,
                                f"{kps:.2f} kills/s{prov}")
                    r.add_score("multikill_score", 1.5,
                                f"+ rapid chain {kps:.2f} kills/s{prov} (+1.5)")

            # HIGH_SPEED_MULTIKILL: every kill in the chain at speed
            if chain.get("speed_samples") == n and n >= 2:
                mn = chain["speed_min"]
                mn_tier, mn_pct, mn_prov = speed_tier(mn, norms,
                                                      "attacker_speed")
                if mn_tier is not None:
                    r.add_class(
                        "HIGH_SPEED_MULTIKILL", HIGH,
                        f"{n} kills, speed mean={chain['speed_mean']:.0f} "
                        f"min={mn:.0f} peak={chain['speed_peak']:.0f} ups"
                        + (f" (min at archive p{mn_pct})"
                           if mn_pct is not None else prov))
                    r.add_score("speed_score", 2.0,
                                f"+ whole chain at speed (min {mn:.0f} ups"
                                + (f" p{mn_pct}" if mn_pct is not None
                                   else prov) + ") (+2.0)")

            # MULTI_WEAPON_CHAIN: the chain crossed weapons
            if len(set(chain["weapons"])) >= 2:
                r.add_class("MULTI_WEAPON_CHAIN", HIGH,
                            "chain weapons: " + "+".join(chain["weapons"]))
                r.add_score("combo_score", 1.0,
                            f"+ multi-weapon chain ({len(set(chain['weapons']))}"
                            " weapons)")

        # ---- WEAPON_COMBO / COMBO_KILL (named finisher pairs) --------------
        combo_scored = False
        for combo in ("rocket_rail", "shaft_rail", "shaft_rocket",
                      "rocket_shaft"):
            if combo in tags:
                r.add_class("WEAPON_COMBO", HIGH,
                            f"{combo}: {tags[combo].detail}")
                if not combo_scored:
                    r.add_score("combo_score", 1.5,
                                f"+ weapon combo {combo}")
                    combo_scored = True
        if i > 0:
            prev = tagged[i - 1]
            gap = f.time_ms - prev.time_ms
            if 0 < gap <= fc.COMBO_WINDOW_MS:
                pair = _FINISHER_PAIRS.get(
                    (_weapon_family(prev.weapon) or "",
                     _weapon_family(f.weapon) or ""))
                if pair:
                    r.add_class("COMBO_KILL", HIGH,
                                f"{pair} finisher, {gap} ms after "
                                f"{prev.weapon_name}")
                    if not combo_scored:
                        r.add_score("combo_score", 1.5,
                                    f"+ finisher pair {pair}")
                        combo_scored = True

        # ---- POPUP_COMBO: rocket-pop -> rail/LG finisher -------------------
        # Victim airborne AND heading up within the pop window, finished with
        # a hitscan. A missile impact in the window is supporting evidence;
        # damage ATTRIBUTION is not recorded, hence never above MEDIUM.
        if air_tag and f.weapon in (RAIL | SHAFT):
            rise = None
            for row in tl.window(f.victim, f.time_ms - POPUP_WINDOW_MS,
                                 f.time_ms):
                vz_row = row.get("vel_z")
                if vz_row is not None and vz_row >= POPUP_RISE_VZ:
                    rise = vz_row
                    break
            if rise is not None:
                hit_near = any(f.time_ms - POPUP_WINDOW_MS <= t <= f.time_ms
                               for t in missile_hits)
                conf = MEDIUM if hit_near else LOW_CANDIDATE
                r.add_class("POPUP_COMBO", conf,
                            f"victim rising {rise:.0f} ups within "
                            f"{POPUP_WINDOW_MS} ms of a {f.weapon_name} finish"
                            + ("; missile impact in window" if hit_near
                               else "; no missile-impact evidence"))
                attrs["popup_rise_vz"] = round(rise, 1)
                r.add_score("combo_score", 2.0 if hit_near else 1.0,
                            "+ pop-up finished with "
                            + ("rail" if f.weapon in RAIL else "LG"))

        # ---- TARGET_TRANSFER ----------------------------------------------
        if i > 0:
            prev = tagged[i - 1]
            gap = f.time_ms - prev.time_ms
            if 0 < gap < TRANSFER_MAX_GAP_MS and prev.victim != f.victim:
                deg = transfer_angle(tl, f.killer, prev.victim, prev.time_ms,
                                     f.victim, f.time_ms)
                if deg is not None and deg > TRANSFER_MIN_DEG:
                    attrs["transfer_deg"] = deg
                    attrs["transfer_ms"] = gap
                    r.add_class("TARGET_TRANSFER", HIGH,
                                f"{deg:.0f} deg between victims, {gap} ms apart")
                    r.add_score("tracking_score", min(2.5, deg / 60.0),
                                f"+ target transfer {deg:.0f} deg in {gap} ms")
                    if prev.weapon in SHAFT and f.weapon in SHAFT:
                        r.add_class("LG_TRANSFER", HIGH,
                                    f"LG->LG transfer {deg:.0f} deg / {gap} ms")
                        r.add_score("tracking_score", 1.0, "+ LG-to-LG transfer")

        # ---- PREDICTION candidates (rocket/grenade preshot) ----------------
        if "preshot" in tags and f.weapon in (ROCKET | GRENADE):
            kind = "grenade" if f.weapon in GRENADE else "rocket"
            r.add_class("PREDICTION_CANDIDATE", LOW_CANDIDATE,
                        f"{kind} preshot: {tags['preshot'].detail} "
                        "(geometric signature only, no PVS trace)")
            r.add_score("prediction_score", 1.5, f"+ predicted {kind}")

        # ---- movement family (v2) ------------------------------------------
        if "airborne_kill" in tags:
            r.add_score("movement_score", 1.5,
                        "+ killer airborne at the kill")

        # HIGH_SPEED_FRAG: archive-percentile speed labels (rule L)
        if atk_tier is not None:
            pts = {"FAST": 1.5, "VERY_FAST": 3.0, "EXTREME_SPEED": 5.0}[atk_tier]
            where = (f"archive p{atk_pct}" if atk_pct is not None
                     else f"{atk_speed:.0f} ups{prov}")
            r.add_class("HIGH_SPEED_FRAG", HIGH,
                        f"{atk_tier}: attacker {atk_speed:.0f} ups ({where})")
            r.add_score("speed_score", pts,
                        f"+ {atk_tier.lower().replace('_', '-')} "
                        f"{atk_speed:.0f} ups "
                        + (f"p{atk_pct}" if atk_pct is not None else prov.strip())
                        + f" (+{pts})")
            if "airborne_kill" in tags:
                r.add_class("HIGH_SPEED_AIR_FRAG", HIGH,
                            f"airborne attacker at {atk_speed:.0f} ups")
                r.add_score("speed_score", 1.0,
                            f"+ airborne at {atk_speed:.0f} ups (+1.0)")

        # SPEED_TARGET_FRAG: hitting a FAST victim
        if vic_tier is not None:
            conf = HIGH if not vic_prov else MEDIUM
            where = (f"archive p{vic_pct}" if vic_pct is not None
                     else f"{vic_speed:.0f} ups{prov}")
            r.add_class("SPEED_TARGET_FRAG", conf,
                        f"victim at {vic_speed:.0f} ups ({where})")
            pts = {"FAST": 1.0, "VERY_FAST": 1.5, "EXTREME_SPEED": 2.0}[vic_tier]
            r.add_score("speed_score", pts,
                        f"+ fast-moving victim {vic_speed:.0f} ups "
                        + (f"p{vic_pct}" if vic_pct is not None else prov.strip())
                        + f" (+{pts})")

        # ROCKET_JUMP_ENTRY / ROCKET_JUMP_FRAG
        impulse = rocket_jump_impulse(tl, f.killer, f.time_ms)
        if impulse is not None and "airborne_kill" in tags:
            step, step_t = impulse
            attrs["rocket_jump_impulse_ups"] = step
            if f.weapon in ROCKET:
                r.add_class("ROCKET_JUMP_FRAG", MEDIUM,
                            f"+{step:.0f} ups vertical impulse "
                            f"{f.time_ms - step_t} ms pre-kill, airborne "
                            "rocket kill (impulse observed, self-damage "
                            "attribution not recorded)")
                r.add_score("movement_score", 2.5,
                            f"+ rocket-jump kill (impulse +{step:.0f} ups)")
            else:
                r.add_class("ROCKET_JUMP_ENTRY", MEDIUM,
                            f"+{step:.0f} ups vertical impulse "
                            f"{f.time_ms - step_t} ms pre-kill, airborne "
                            f"{f.weapon_name} kill")
                r.add_score("movement_score", 1.5,
                            f"+ jump-entry kill (impulse +{step:.0f} ups)")

        # STRAFE_CHAIN_FRAG
        sc = strafe_chain(tl, f.killer, f.time_ms, strafe_min)
        if sc is not None:
            attrs.update(sc)
            r.add_class("STRAFE_CHAIN_FRAG", MEDIUM,
                        f"mean {sc['strafe_mean_speed']:.0f} ups, "
                        f"{sc['strafe_dir_changes']} direction changes, "
                        f"{sc['strafe_hop_transitions']} hop transitions over "
                        f"{STRAFE_WINDOW_MS} ms (pattern proxy)")
            r.add_score("movement_score", 1.5,
                        f"+ strafe chain into the kill "
                        f"({sc['strafe_mean_speed']:.0f} ups avg)")

        # VERTICAL_ACTION
        dz = vertical_travel(tl, f.killer, f.time_ms)
        if dz is not None and dz >= VERTICAL_MIN_DZ:
            attrs["vertical_travel"] = dz
            r.add_class("VERTICAL_ACTION", HIGH,
                        f"attacker moved {dz:.0f}u vertically in the last "
                        f"{VERTICAL_WINDOW_MS} ms")
            r.add_score("movement_score", 1.0,
                        f"+ vertical action ({dz:.0f}u)")

        # DODGE_AND_KILL / ESCAPE_TURNAROUND -- honest proxies, LOW_CANDIDATE
        dodge = velocity_direction_change(tl, f.killer, f.time_ms)
        if dodge is not None and dodge >= DODGE_MIN_DEG:
            attrs["dodge_deg"] = dodge
            r.add_class("DODGE_AND_KILL", LOW_CANDIDATE,
                        f"velocity heading changed {dodge:.0f} deg at speed "
                        "just before the kill (direction-change proxy -- "
                        "incoming fire not verified)")
            r.add_score("movement_score", 0.75,
                        f"+ dodge-and-kill proxy ({dodge:.0f} deg)")
        turn = yaw_turn(tl, f.killer, f.time_ms)
        if turn is not None and turn >= TURNAROUND_MIN_DEG:
            attrs["turnaround_deg"] = turn
            r.add_class("ESCAPE_TURNAROUND", LOW_CANDIDATE,
                        f"net {turn:.0f} deg yaw turn within "
                        f"{TURNAROUND_WINDOW_MS} ms then a kill (turn proxy "
                        "-- pursuit not verified)")
            r.add_score("movement_score", 0.75,
                        f"+ turnaround kill proxy ({turn:.0f} deg)")

        # ---- context classes (J) -------------------------------------------
        # Recorder health IS recorded (playerstate STAT_HEALTH); non-recorder
        # killers have no health rows and silently skip.
        hp = min_health(tl, f.killer, f.time_ms)
        if hp is not None and 0 < hp <= LAST_HP_MAX:
            attrs["min_health_prekill"] = hp
            r.add_class("LAST_HP_FRAG", HIGH,
                        f"{hp} HP (recorded playerstate) in the "
                        f"{HEALTH_WINDOW_MS} ms before the kill")
            r.add_score("drama_score", 3.5, f"+ kill at {hp} HP (+3.5)")
        elif hp is not None and 0 < hp <= LOW_HEALTH_MAX:
            attrs["min_health_prekill"] = hp
            r.add_class("LOW_HEALTH_WIN", HIGH,
                        f"{hp} HP (recorded playerstate) in the "
                        f"{HEALTH_WINDOW_MS} ms before the kill")
            r.add_score("drama_score", 2.0, f"+ kill at {hp} HP (+2.0)")

        # FAST_WEAPON_SWITCH / WEAPON_SWITCH_FINISH
        sw = weapon_switch_gap(tl, f.killer, f.time_ms)
        if sw is not None and 0 <= sw < SWITCH_KILL_MAX_MS:
            attrs["weapon_switch_gap_ms"] = sw
            r.add_class("FAST_WEAPON_SWITCH", HIGH,
                        f"weapon changed {sw} ms before the kill "
                        "(recorded weapon field)")
            r.add_score("combo_score", 0.75,
                        f"+ switch-to-kill in {sw} ms")
            if i > 0 and 0 < f.time_ms - times[i - 1] <= fc.COMBO_WINDOW_MS:
                r.add_class("WEAPON_SWITCH_FINISH", HIGH,
                            f"switched {sw} ms before finishing a "
                            f"{f.time_ms - times[i - 1]} ms combo")
                r.add_score("combo_score", 0.5, "+ switch finished a combo")

        # ---- penalties (K) -------------------------------------------------
        # stationary_easy_target: parked victim with no sign of a fight.
        # "Cleanup" (victim pre-damaged by someone ELSE) is NOT derivable --
        # obituaries carry no damage attribution -- so no penalty exists for
        # it. round_end_helpless needs the clutch join (downstream).
        if vic_speed is not None and vic_speed < STATIONARY_UPS:
            pains = _event_times(parsed, "pain", client=f.victim)
            fought = any(f.time_ms - STATIONARY_PAIN_LOOKBACK_MS <= t
                         < f.time_ms for t in pains)
            if not fought:
                r.add_penalty(1.0,
                              f"- stationary victim ({vic_speed:.0f} ups, "
                              "no recent pain events) (-1.0)")

        # ---- round and team context (v3) -----------------------------------
        # Clan Arena has no respawn inside a round, so the round's own
        # obituaries give an exact alive count. Everything below is a counted
        # fact, not an impression -- but only because the round window now
        # ends one snapshot AFTER the end command.
        ctx = ctxs.get(f.time_ms)
        if ctx:
            attrs.update(ctx)
            mates = ctx["alive_teammates_at_kill"]
            foes = ctx["alive_opponents_at_kill"]

            if ctx["is_round_winning_frag"]:
                r.add_class("ROUND_WINNING_FRAG", CONFIRMED,
                            f"last opponent alive in round "
                            f"{ctx['round_index']} ({ctx['round_end_basis']})")
                r.add_score("round_score", 2.0, "+ closed the round")

            if ctx["is_last_alive"] and foes >= 1:
                r.add_class("LAST_MAN_STANDING", CONFIRMED,
                            f"only survivor on {ctx['team']} vs {foes}")
                if foes >= 2:
                    r.add_class("CLUTCH_1VN", CONFIRMED,
                                f"1v{foes} while last alive")
                    r.add_score("round_score", 1.0 + min(foes, 4),
                                f"+ 1v{foes} clutch")
                if ctx["is_round_winning_frag"]:
                    r.add_class("CLUTCH_ROUND_WIN", CONFIRMED,
                                f"won the round 1v{foes} as the last alive")
                    r.add_score("round_score", 3.0, "+ clutch round win")

            elif ctx["outnumbered_by"] >= 1:
                r.add_class("OUTNUMBERED_FRAG", HIGH,
                            f"{mates}v{foes} at the kill")
                r.add_score("round_score", 0.5 * ctx["outnumbered_by"],
                            f"+ killed while {mates}v{foes}")

            if ctx["is_round_opening_frag"]:
                r.add_class("ROUND_OPENING_FRAG", CONFIRMED,
                            f"{ctx['ms_into_round']} ms into round "
                            f"{ctx['round_index']}; "
                            f"{ctx['countdown_available_ms']} ms of countdown "
                            "precedes the start")
                # Not a score change. An opening frag is not better, it is
                # SHAPED differently -- it has a countdown in front of it, and
                # that is an editing fact rather than a quality one.

            if ctx["is_first_blood"]:
                r.add_class("FIRST_BLOOD", CONFIRMED,
                            f"first kill of round {ctx['round_index']}")

            if ctx["is_trade_kill"]:
                r.add_class("TRADE_KILL", HIGH,
                            "the victim had killed a teammate within "
                            f"{rc.TRADE_WINDOW_MS} ms")

            if ctx["is_revenge"]:
                r.add_class("REVENGE_FRAG", MEDIUM,
                            "killed the opponent who killed him in the "
                            "previous round")

            # An opponent who entered the recorder's snapshot moments before
            # dying was never tracked -- the shot resolved on first sight.
            # This is only meaningful now that presence is exported: before,
            # an absent state row could equally mean "present and unchanged".
            if vis is not None and vis <= rc.AMBUSH_MAX_VISIBLE_MS:
                r.add_class("SNAP_ON_ARRIVAL", HIGH,
                            f"opponent observable for only {vis} ms before "
                            "the kill")

        out.append(r)
    return out


def summary(recs: Sequence[RecognizedFrag]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in recs:
        for c in r.classes:
            counts[c["name"]] = counts.get(c["name"], 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: -kv[1]))
