"""PANDORA LAB: hot-swappable cinematic layers (directive 30-40).

FOUNDATION ONLY. This module opens the architecture and nothing else: no
bulk generation, no corpus-wide conversion, no mutation of original Quake
assets. It answers three questions and stops.

1. WHAT CAN BE SWAPPED. Twelve independent domains (textures, skins,
   models, shader FX, grade, ...). Independent means a pack may touch one
   domain and leave the rest alone, and two packs touching different
   domains compose without either knowing about the other.

2. WHERE ASSETS LIVE. Three tiers that are never conflated:
   ORIGINAL (Steam pak, read-only per ENG-4), MASTER (a generated artifact,
   kept forever, hashed), RUNTIME (a derivative built for the engine,
   disposable). Nothing is ever written back over an original.

3. WHEN AN EFFECT FIRES. On SceneRecipe SEMANTICS -- a rocket impact, an
   LG burst, a dodge -- never on wall-clock time. The project already
   learned this the hard way: an effect keyed to a hand-authored timestamp
   fires for the one clip somebody typed it into and silently does nothing
   everywhere else.

THE SAFETY RULE (directive 39) is enforced here rather than documented.
Every effect declares OFF / SUBTLE / HERO, OFF must be a genuine no-op,
and the movie has to render with every Pandora effect disabled. That is
what stops the project becoming dependent on one experimental gimmick.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
import hashlib
import json
from typing import Any

PANDORA_SCHEMA_VERSION = 1

# ── domains (directive 31) ──────────────────────────────────────────────────
WORLD_TEXTURES = "WORLD_TEXTURES"
WEAPON_SKINS = "WEAPON_SKINS"
PLAYER_SKINS = "PLAYER_SKINS"
PLAYER_MODELS = "PLAYER_MODELS"
WEAPON_MODELS = "WEAPON_MODELS"
ANIMATION_PRESENTATION = "ANIMATION_PRESENTATION"
SHADER_FX = "SHADER_FX"
PARTICLE_FX = "PARTICLE_FX"
LIGHTING = "LIGHTING"
POST_GRADE = "POST_GRADE"
TRANSITION_STYLE = "TRANSITION_STYLE"
HUD_STYLE = "HUD_STYLE"

DOMAINS = (WORLD_TEXTURES, WEAPON_SKINS, PLAYER_SKINS, PLAYER_MODELS,
           WEAPON_MODELS, ANIMATION_PRESENTATION, SHADER_FX, PARTICLE_FX,
           LIGHTING, POST_GRADE, TRANSITION_STYLE, HUD_STYLE)

# Domains that change what the ENGINE loads, so a change invalidates a
# capture. The rest are post-only. This split is the Pandora equivalent of
# the visual_capture_key / preview_assembly_key split and exists for the
# same reason: a post-only change must not throw away a capture.
CAPTURE_AFFECTING = frozenset({
    WORLD_TEXTURES, WEAPON_SKINS, PLAYER_SKINS, PLAYER_MODELS, WEAPON_MODELS,
    ANIMATION_PRESENTATION, SHADER_FX, PARTICLE_FX, LIGHTING, HUD_STYLE})
POST_ONLY = frozenset({POST_GRADE, TRANSITION_STYLE})
assert CAPTURE_AFFECTING | POST_ONLY == set(DOMAINS)

# ── intensity (directive 39) ────────────────────────────────────────────────
OFF = "OFF"
SUBTLE = "SUBTLE"
HERO = "HERO"
INTENSITIES = (OFF, SUBTLE, HERO)

# ── asset tiers (directive 32) ──────────────────────────────────────────────
TIER_ORIGINAL = "ORIGINAL"   # Steam pak / pak00 -- READ ONLY (ENG-4)
TIER_MASTER = "MASTER"       # generated, kept, hashed
TIER_RUNTIME = "RUNTIME"     # engine-ready derivative, disposable
TIERS = (TIER_ORIGINAL, TIER_MASTER, TIER_RUNTIME)

PROFILE_ORIGINAL = "ORIGINAL"
PROFILE_UHD_FAITHFUL = "UHD_FAITHFUL"
PROFILE_PANTHEON = "PANTHEON"
PROFILE_RETRO = "RETRO"
PROFILE_DARK = "DARK"
PROFILE_HERO = "HERO"
PROFILES = (PROFILE_ORIGINAL, PROFILE_UHD_FAITHFUL, PROFILE_PANTHEON,
            PROFILE_RETRO, PROFILE_DARK, PROFILE_HERO)

# ── semantic events an effect may bind to (directive 33) ────────────────────
# Every one already exists as SceneRecipe/recognition evidence. Adding a
# name here without evidence behind it is how effects come to fire nowhere.
EV_PROJECTILE_LAUNCH = "PROJECTILE_LAUNCH"
EV_PROJECTILE_IMPACT = "PROJECTILE_IMPACT"
EV_LG_BURST = "LG_BURST"
EV_DODGE_HERO = "DODGE_HERO"
EV_FRAG = "FRAG"
EV_ROUND_WIN = "ROUND_WIN"
EV_MULTIKILL = "MULTIKILL"
BINDABLE_EVENTS = (EV_PROJECTILE_LAUNCH, EV_PROJECTILE_IMPACT, EV_LG_BURST,
                   EV_DODGE_HERO, EV_FRAG, EV_ROUND_WIN, EV_MULTIKILL)


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True)


@dataclass(frozen=True)
class AssetVariant:
    """One generated asset, traced end to end (directive 35).

    Every hash is required because an unreproducible experiment is not a
    result. ``source_hash`` identifies the ORIGINAL it derives from and is
    never overwritten by anything here.
    """
    domain: str
    asset_key: str            # e.g. "textures/base_wall/concrete_dark"
    tier: str
    source_hash: str          # the ORIGINAL this derives from
    workflow_hash: str        # ComfyUI workflow identity
    master_hash: str          # the generated master
    runtime_hash: str = ""    # the engine-ready derivative, if built
    parameters: tuple = ()

    def __post_init__(self) -> None:
        if self.domain not in DOMAINS:
            raise ValueError("unknown domain: " + str(self.domain))
        if self.tier not in TIERS:
            raise ValueError("unknown tier: " + str(self.tier))
        if self.tier == TIER_ORIGINAL:
            raise ValueError(
                "originals are read-only (ENG-4); a variant is MASTER or "
                "RUNTIME and records the original as source_hash")
        for name in ("source_hash", "workflow_hash", "master_hash"):
            if not getattr(self, name):
                raise ValueError(
                    name + " is required: an unreproducible variant is not "
                    "a result")

    def canonical(self) -> dict:
        d = asdict(self)
        d["parameters"] = {k: v for k, v in self.parameters}
        return d

    @property
    def variant_id(self) -> str:
        return hashlib.sha256(
            canonical_json(self.canonical()).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ReactiveEffect:
    """An effect bound to a semantic event, with a mandatory OFF state."""
    name: str
    domain: str
    event: str
    intensity: str = OFF
    lead_us: int = 0            # fire this long BEFORE the event
    hold_us: int = 0            # and sustain this long after
    parameters: tuple = ()

    def __post_init__(self) -> None:
        if self.domain not in DOMAINS:
            raise ValueError("unknown domain: " + str(self.domain))
        if self.event not in BINDABLE_EVENTS:
            raise ValueError(
                f"{self.event} is not bindable evidence; effects must attach "
                f"to recognised events, never to wall-clock time")
        if self.intensity not in INTENSITIES:
            raise ValueError("unknown intensity: " + str(self.intensity))
        for name in ("lead_us", "hold_us"):
            v = getattr(self, name)
            if not isinstance(v, int) or isinstance(v, bool) or v < 0:
                raise ValueError(name + " must be a non-negative int")

    @property
    def enabled(self) -> bool:
        return self.intensity != OFF

    def canonical(self) -> dict:
        d = asdict(self)
        d["parameters"] = {k: v for k, v in self.parameters}
        return d


@dataclass(frozen=True)
class AssetPack:
    """A named set of domain overrides plus reactive effects."""
    name: str
    profile: str
    domains: tuple = ()          # (domain, variant_id) pairs
    effects: tuple = ()          # ReactiveEffect
    version: int = 1
    schema_version: int = PANDORA_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.profile not in PROFILES:
            raise ValueError("unknown profile: " + str(self.profile))
        seen = set()
        for domain, _ in self.domains:
            if domain not in DOMAINS:
                raise ValueError("unknown domain: " + str(domain))
            if domain in seen:
                raise ValueError(
                    f"{domain} overridden twice; domains are independent and "
                    f"a pack must not fight itself")
            seen.add(domain)

    @property
    def touched_domains(self) -> frozenset:
        return frozenset(d for d, _ in self.domains)

    @property
    def affects_capture(self) -> bool:
        """Whether enabling this pack invalidates a captured frame."""
        if self.touched_domains & CAPTURE_AFFECTING:
            return True
        return any(e.enabled and e.domain in CAPTURE_AFFECTING
                   for e in self.effects)

    def with_all_effects_off(self) -> "AssetPack":
        """The same pack with every effect disabled (directive 39).

        The normal movie must still render through this. It is a method
        rather than a convention so a test can assert it.
        """
        return AssetPack(
            name=self.name, profile=self.profile, domains=self.domains,
            effects=tuple(ReactiveEffect(
                name=e.name, domain=e.domain, event=e.event, intensity=OFF,
                lead_us=e.lead_us, hold_us=e.hold_us,
                parameters=e.parameters) for e in self.effects),
            version=self.version, schema_version=self.schema_version)

    def canonical(self) -> dict:
        return {"name": self.name, "profile": self.profile,
                "domains": [list(x) for x in self.domains],
                "effects": [e.canonical() for e in self.effects],
                "version": self.version,
                "schema_version": self.schema_version}

    @property
    def pack_id(self) -> str:
        return hashlib.sha256(
            canonical_json(self.canonical()).encode("utf-8")).hexdigest()


def resolve_effects(pack: AssetPack, anchors: list) -> list:
    """Place a pack's enabled effects on the scene's edit clock.

    ``anchors`` are ``(event_type, edit_us)`` pairs from the SceneRecipe --
    the same evidence the camera and the music use. An effect whose event
    does not occur in this scene simply does not fire; it is never
    relocated to a nearby timestamp to make it appear.
    """
    out = []
    for effect in pack.effects:
        if not effect.enabled:
            continue
        for event_type, edit_us in anchors:
            if event_type != effect.event:
                continue
            out.append({"name": effect.name, "domain": effect.domain,
                        "event": effect.event,
                        "intensity": effect.intensity,
                        "start_edit_us": max(0, int(edit_us) - effect.lead_us),
                        "end_edit_us": int(edit_us) + effect.hold_us})
    out.sort(key=lambda r: (r["start_edit_us"], r["name"]))
    return out
