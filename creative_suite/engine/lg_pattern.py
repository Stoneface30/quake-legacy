"""Pattern-level music matching for LG tracking (Canary 02, directive 7-14).

HITS ARE BEATS -- but not in the primitive sense. The question is no longer
"which beat is nearest the hero event?" but:

    WHICH MUSIC REGION NATURALLY COMPLEMENTS THIS TEMPORAL HIT PATTERN?

The gameplay pattern is TRUTH. Contacts are never shifted, dropped,
duplicated or quantized; the kill never moves. ``GameplayPattern`` is
frozen and carries the exact timestamps and the derived structure (bursts,
gaps, the breath) as separate facts.

Music is scored from CACHED MusicFeatureV2 features only -- onset curve,
energy curve, salient events, phrase estimates. Nothing is decoded here.
Every candidate placement puts the KILL on a sharp musical event (the one
hard-sync that matters) and is then scored by explainable components, so
three editorial philosophies are three weightings over the same facts:

    HIT_RHYTHM_FORWARD    music sparse enough that the ticks ARE the percussion
    PERCUSSIVE_COMPLEMENT music rhythm complements burst boundaries, never
                          one-onset-per-tick
    BUILD_AND_PAYOFF      tension through the tracking, space in the breath,
                          a strong return on the kill

No component asks for one musical onset per contact; that would sound
artificial and the directive forbids it. Burst structure outweighs
individual ticks; the breath and the kill outweigh bursts.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import hashlib
import json
from typing import Any

import numpy as np

from creative_suite.engine.music_features_v2 import MusicFeatureV2
from creative_suite.engine.music_intelligence_v2 import energy_shape_fit
from creative_suite.engine.scene_recipe import MusicPlacement
from creative_suite.engine import sync_contract as sc

BURST_GAP_MS = 300          # a gap longer than this separates bursts
BIN_MS = 250                # envelope resolution for density comparison
KILL_EVENT_TYPES = ("ACCENT", "STAB", "DROP_CANDIDATE", "BELL", "VOCAL_ENTRY")
# MUSIC PRESENCE GATE. "Sparse enough that the ticks are the percussion"
# still means music is THERE. Without this, HIT_RHYTHM_FORWARD is won by a
# silent intro/outro (measured: onset density 0.1/s, energy at the floor).
MIN_ONSET_DENSITY_PER_S = 0.3
MIN_MEAN_ENERGY = 0.15

HIT_RHYTHM_FORWARD = "HIT_RHYTHM_FORWARD"
PERCUSSIVE_COMPLEMENT = "PERCUSSIVE_COMPLEMENT"
BUILD_AND_PAYOFF = "BUILD_AND_PAYOFF"
PHILOSOPHIES = (HIT_RHYTHM_FORWARD, PERCUSSIVE_COMPLEMENT, BUILD_AND_PAYOFF)

# Semantic mix states (directive 17). Section-level, never per-hit.
MIX_MUSIC_FORWARD = "MUSIC_FORWARD"
MIX_BALANCED = "BALANCED"
MIX_GAMEPLAY_FORWARD = "GAMEPLAY_FORWARD"
MIX_HIT_RHYTHM_FORWARD = "HIT_RHYTHM_FORWARD"
MIX_STATES = (MIX_MUSIC_FORWARD, MIX_BALANCED, MIX_GAMEPLAY_FORWARD,
              MIX_HIT_RHYTHM_FORWARD)
# music gain relative to the balanced reference, per state (dB)
MIX_MUSIC_GAIN_DB = {MIX_MUSIC_FORWARD: +2.0, MIX_BALANCED: 0.0,
                     MIX_GAMEPLAY_FORWARD: -3.0, MIX_HIT_RHYTHM_FORWARD: -5.0}


# ── the gameplay pattern: exact, immutable ──────────────────────────────────

@dataclass(frozen=True)
class GameplayPattern:
    """Contact timestamps relative to the kill (ms, negative = before)."""
    contacts_rel_ms: tuple
    kill_rel_ms: int = 0
    burst_gap_ms: int = BURST_GAP_MS

    def __post_init__(self) -> None:
        c = tuple(int(x) for x in self.contacts_rel_ms)
        if not c:
            raise ValueError("a pattern needs at least one contact")
        if list(c) != sorted(c):
            raise ValueError("contacts must be in time order")
        if c[-1] >= self.kill_rel_ms:
            raise ValueError("every contact must precede the kill")
        object.__setattr__(self, "contacts_rel_ms", c)

    @property
    def bursts(self) -> tuple:
        out = [[self.contacts_rel_ms[0]]]
        for a, b in zip(self.contacts_rel_ms, self.contacts_rel_ms[1:]):
            if b - a <= self.burst_gap_ms:
                out[-1].append(b)
            else:
                out.append([b])
        return tuple(tuple(x) for x in out)

    @property
    def burst_boundaries_ms(self) -> tuple:
        """Starts and ends of every burst -- the structurally weighty moments."""
        return tuple(sorted({b[0] for b in self.bursts} | {b[-1] for b in self.bursts}))

    @property
    def gaps_ms(self) -> tuple:
        b = self.bursts
        return tuple(b[i + 1][0] - b[i][-1] for i in range(len(b) - 1))

    @property
    def breath_ms(self) -> int:
        return self.kill_rel_ms - self.contacts_rel_ms[-1]

    @property
    def span_ms(self) -> int:
        return self.kill_rel_ms - self.contacts_rel_ms[0]

    def notation(self) -> str:
        return " | ".join("x" * len(b) for b in self.bursts) + " | ... | KILL"

    def canonical(self) -> dict:
        return {"contacts_rel_ms": list(self.contacts_rel_ms),
                "kill_rel_ms": self.kill_rel_ms,
                "burst_gap_ms": self.burst_gap_ms}

    @property
    def pattern_id(self) -> str:
        return hashlib.sha256(json.dumps(self.canonical(), sort_keys=True,
                                         separators=(",", ":")).encode()).hexdigest()


# ── envelopes ───────────────────────────────────────────────────────────────

def _bins(start_us: int, end_us: int) -> np.ndarray:
    return np.arange(start_us, end_us + 1, BIN_MS * 1000)


def contact_envelope(pattern: GameplayPattern, kill_edit_us: int,
                     start_us: int, end_us: int) -> np.ndarray:
    """Contacts per bin over the edit window."""
    edges = _bins(start_us, end_us)
    env = np.zeros(len(edges) - 1)
    for c in pattern.contacts_rel_ms:
        t = kill_edit_us + c * 1000
        i = int((t - start_us) // (BIN_MS * 1000))
        if 0 <= i < len(env):
            env[i] += 1
    return env


def music_onset_envelope(feature: MusicFeatureV2, music_start_us: int,
                         duration_us: int) -> np.ndarray:
    """Summed onset strength per bin from the cached onset curve."""
    edges = _bins(music_start_us, music_start_us + duration_us)
    env = np.zeros(len(edges) - 1)
    for t, s in feature.onset_curve:
        i = int((t - music_start_us) // (BIN_MS * 1000))
        if 0 <= i < len(env):
            env[i] += max(0.0, float(s))
    return env


def music_energy(feature: MusicFeatureV2, music_us: int) -> float:
    if not feature.energy_curve:
        return 0.0
    return float(min(feature.energy_curve, key=lambda p: abs(p[0] - music_us))[1])


# ── components (each in [0, 1], each explainable) ───────────────────────────

def _norm(env: np.ndarray) -> np.ndarray:
    m = float(env.max()) if env.size else 0.0
    return env / m if m > 0 else env


def component_scores(pattern: GameplayPattern, feature: MusicFeatureV2,
                     placement: MusicPlacement, kill_edit_us: int,
                     scene_start_us: int, scene_end_us: int) -> dict:
    dur = scene_end_us - scene_start_us
    m0 = placement.edit_to_music(scene_start_us)
    g = contact_envelope(pattern, kill_edit_us, scene_start_us, scene_end_us)
    m = music_onset_envelope(feature, m0, dur)
    n = min(len(g), len(m)); g, m = g[:n], m[:n]
    gn, mn = _norm(g), _norm(m)
    active = gn > 0
    kill_music = placement.edit_to_music(kill_edit_us)

    # HIT_RHYTHM_FIT: how much room the music leaves where contacts are dense.
    # 1.0 = silent music under the ticks; 0.0 = music as busy as the ticks.
    hit_rhythm = float(1.0 - mn[active].mean()) if active.any() else 0.0

    # BURST_PATTERN_FIT: fraction of burst BOUNDARIES with a reasonably
    # strong onset within 120 ms -- structure, not one-onset-per-tick.
    # Threshold relative to THIS window's own onset strengths (60th pct):
    # an absolute 0.5 left the component under-powered on quiet tracks.
    win = [(t, s) for t, s in feature.onset_curve if m0 <= t <= m0 + dur]
    thr_on = float(np.percentile([s for _, s in win], 60)) if win else 1.0
    onsets = [t for t, s in win if s >= thr_on]
    hits = 0
    for b in pattern.burst_boundaries_ms:
        target = placement.edit_to_music(kill_edit_us + b * 1000)
        if onsets and min(abs(o - target) for o in onsets) <= 120_000:
            hits += 1
    burst_pattern = hits / max(1, len(pattern.burst_boundaries_ms))

    # MUSIC_SPACE_FIT: share of contact-active bins where music onset
    # strength is below its own 30th percentile -- genuine space, not gain.
    thr = float(np.percentile(mn, 30)) if mn.size else 0.0
    music_space = float((mn[active] <= thr).mean()) if active.any() else 0.0

    # ENERGY over the scene, resampled to five points for the shape fit
    e = [music_energy(feature, m0 + int(dur * k / 4)) for k in range(5)]

    # BREATH treatment: music onset density in the breath bin(s) relative to
    # the tracking bins. Low = space; the KILL then has room to land.
    breath_lo = kill_edit_us - pattern.breath_ms * 1000
    bi = int((breath_lo - scene_start_us) // (BIN_MS * 1000))
    bk = int((kill_edit_us - scene_start_us) // (BIN_MS * 1000))
    breath_bins = mn[max(0, bi):max(bi + 1, bk)]
    breath_space = float(1.0 - breath_bins.mean()) if breath_bins.size else 0.0

    # FINAL_KILL_FIT: the sharp event the kill lands on, weighted by strength
    ev = [x for x in feature.salient_events if x.event_type in KILL_EVENT_TYPES]
    near = min(ev, key=lambda x: abs(x.music_us - kill_music)) if ev else None
    kill_delta_ms = (near.music_us - kill_music) / 1000.0 if near else None
    kill_strength = (max(0.0, near.strength) * (near.confidence or 0.5)) if near else 0.0
    final_kill = kill_strength * (1.0 if kill_delta_ms is not None
                                  and abs(kill_delta_ms) <= 15 else 0.5)

    # PHRASE_PAYOFF_FIT: kill near a phrase/section estimate (PHRASE class)
    clocks = (*feature.phrase_boundary_estimates_us, *feature.section_boundary_estimates_us)
    pd = min(abs(c - kill_music) for c in clocks) / 1000.0 if clocks else None
    phrase_payoff = (max(0.0, 1.0 - pd / 500.0) if pd is not None else 0.0)

    # GAME_AUDIO_FOREGROUND_FIT: how quiet the music is during tracking,
    # relative to its own loudest moment in the window (lower energy = more
    # foreground for the game audio).
    track_e = [music_energy(feature, m0 + int(dur * k / 8)) for k in range(7)]
    peak = max(e + track_e) or 1.0
    game_fg = float(1.0 - (np.mean(track_e) / peak))

    present = (float(m.sum() / max(1e-9, dur / 1e6)) >= MIN_ONSET_DENSITY_PER_S
               and float(np.mean(track_e)) >= MIN_MEAN_ENERGY)

    return {
        "MUSIC_PRESENT": present,
        "HIT_RHYTHM_FIT": round(hit_rhythm, 4),
        "BURST_PATTERN_FIT": round(burst_pattern, 4),
        "MUSIC_SPACE_FIT": round(music_space, 4),
        "ENERGY_SHAPE_FIT_BUILD": round(energy_shape_fit((.3, .5, .7, .9, 1.0), e), 4),
        "ENERGY_SHAPE_FIT_FLAT": round(energy_shape_fit((.4, .4, .4, .4, .5), e), 4),
        "BREATH_SPACE_FIT": round(breath_space, 4),
        "FINAL_KILL_FIT": round(final_kill, 4),
        "KILL_EVENT": near.event_type if near else None,
        "KILL_DELTA_MS": (round(kill_delta_ms, 1) if kill_delta_ms is not None else None),
        "PHRASE_PAYOFF_FIT": round(phrase_payoff, 4),
        "GAME_AUDIO_FOREGROUND_FIT": round(game_fg, 4),
        "MUSIC_ONSET_DENSITY": round(float(m.sum() / max(1e-9, dur / 1e6)), 3),
        "energy_points": [round(x, 3) for x in e],
    }


WEIGHTS = {
    HIT_RHYTHM_FORWARD: {
        "HIT_RHYTHM_FIT": .30, "MUSIC_SPACE_FIT": .20, "GAME_AUDIO_FOREGROUND_FIT": .15,
        "BREATH_SPACE_FIT": .10, "FINAL_KILL_FIT": .20, "ENERGY_SHAPE_FIT_FLAT": .05},
    PERCUSSIVE_COMPLEMENT: {
        "BURST_PATTERN_FIT": .30, "HIT_RHYTHM_FIT": .15, "MUSIC_SPACE_FIT": .10,
        "FINAL_KILL_FIT": .25, "BREATH_SPACE_FIT": .10, "PHRASE_PAYOFF_FIT": .10},
    BUILD_AND_PAYOFF: {
        "ENERGY_SHAPE_FIT_BUILD": .30, "BREATH_SPACE_FIT": .20, "FINAL_KILL_FIT": .30,
        "PHRASE_PAYOFF_FIT": .10, "HIT_RHYTHM_FIT": .10},
}

HEAD_NOD = {
    HIT_RHYTHM_FORWARD: "the real LG tick train itself, in musical space",
    PERCUSSIVE_COMPLEMENT: "burst boundaries answering the music's percussion",
    BUILD_AND_PAYOFF: "the 875 ms breath, then the kill on the return",
}


def total(components: dict, philosophy: str) -> float:
    w = WEIGHTS[philosophy]
    return round(sum(w[k] * float(components.get(k) or 0.0) for k in w), 4)


@dataclass(frozen=True)
class Candidate:
    philosophy: str
    track_hash: str
    track_path: str
    music_start_us: int
    kill_music_us: int
    kill_event: str
    total: float
    components: tuple

    def placement(self, scene_start_us: int, scene_end_us: int) -> MusicPlacement:
        return MusicPlacement(track_id=self.track_hash,
                              source_start_us=self.music_start_us,
                              program_edit_start_us=scene_start_us,
                              source_end_us=self.music_start_us
                              + (scene_end_us - scene_start_us))

    def to_dict(self) -> dict:
        d = asdict(self); d["components"] = dict(self.components); return d


def search(pattern: GameplayPattern, features, *, kill_edit_us: int,
           scene_start_us: int, scene_end_us: int, philosophy: str,
           top_n: int = 5) -> list:
    """Every (track, sharp event) placement that puts the KILL on the event,
    scored for one philosophy. Gameplay is never moved: only music_start."""
    dur = scene_end_us - scene_start_us
    out = []
    for f in features:
        if f.duration_us < dur + 1_000_000:
            continue
        for ev in f.salient_events:
            if ev.event_type not in KILL_EVENT_TYPES:
                continue
            music_start = ev.music_us - (kill_edit_us - scene_start_us)
            if music_start < 0 or music_start + dur > f.duration_us:
                continue
            pl = MusicPlacement(track_id=f.track_hash, source_start_us=music_start,
                                program_edit_start_us=scene_start_us,
                                source_end_us=music_start + dur)
            comp = component_scores(pattern, f, pl, kill_edit_us,
                                    scene_start_us, scene_end_us)
            if not comp["MUSIC_PRESENT"]:
                continue
            out.append(Candidate(philosophy, f.track_hash, f.path, music_start,
                                 ev.music_us, ev.event_type,
                                 total(comp, philosophy),
                                 tuple(sorted(comp.items()))))
    out.sort(key=lambda c: (-c.total, c.track_hash, c.music_start_us))
    # one candidate per track keeps the shortlist a real choice
    seen, uniq = set(), []
    for c in out:
        if c.track_hash in seen:
            continue
        seen.add(c.track_hash); uniq.append(c)
        if len(uniq) >= top_n:
            break
    return uniq
