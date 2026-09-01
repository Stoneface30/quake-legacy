"""PANDORA LAB foundation: domains, asset tiers, and the OFF safety rule.

The properties worth enforcing before any asset is generated: originals are
never a write target, an unreproducible variant cannot be constructed,
effects bind to recognised evidence rather than wall-clock time, and every
effect can be switched OFF so the movie still renders without it.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import pandora as pd


def _variant(**kw):
    base = dict(domain=pd.WORLD_TEXTURES, asset_key="textures/base_wall/x",
                tier=pd.TIER_MASTER, source_hash="s" * 64,
                workflow_hash="w" * 64, master_hash="m" * 64)
    base.update(kw)
    return pd.AssetVariant(**base)


def _effect(**kw):
    base = dict(name="impact_flash", domain=pd.LIGHTING,
                event=pd.EV_PROJECTILE_IMPACT, intensity=pd.SUBTLE)
    base.update(kw)
    return pd.ReactiveEffect(**base)


# ── domains are a real partition ────────────────────────────────────────────

def test_twelve_domains_and_no_duplicates():
    assert len(pd.DOMAINS) == 12
    assert len(set(pd.DOMAINS)) == 12


def test_capture_affecting_and_post_only_partition_the_domains():
    assert pd.CAPTURE_AFFECTING | pd.POST_ONLY == set(pd.DOMAINS)
    assert not (pd.CAPTURE_AFFECTING & pd.POST_ONLY)


def test_grade_is_post_only_and_textures_are_not():
    """The Pandora echo of the preview key split: a grade change must not
    throw away a capture, a texture change must."""
    assert pd.POST_GRADE in pd.POST_ONLY
    assert pd.WORLD_TEXTURES in pd.CAPTURE_AFFECTING


# ── originals are never a write target (ENG-4) ──────────────────────────────

def test_a_variant_cannot_claim_the_original_tier():
    with pytest.raises(ValueError, match="read-only"):
        _variant(tier=pd.TIER_ORIGINAL)


def test_every_provenance_hash_is_required():
    for missing in ("source_hash", "workflow_hash", "master_hash"):
        with pytest.raises(ValueError, match="unreproducible"):
            _variant(**{missing: ""})


def test_variant_id_is_deterministic_and_tracks_parameters():
    a = _variant(parameters=(("denoise", 0.35),))
    b = _variant(parameters=(("denoise", 0.35),))
    c = _variant(parameters=(("denoise", 0.50),))
    assert a.variant_id == b.variant_id
    assert a.variant_id != c.variant_id


def test_unknown_domain_rejected():
    with pytest.raises(ValueError):
        _variant(domain="VIBES")


# ── effects bind to evidence, not to wall-clock time ────────────────────────

def test_effect_must_bind_to_recognised_evidence():
    with pytest.raises(ValueError, match="wall-clock"):
        _effect(event="AT_ABOUT_THREE_SECONDS")


def test_off_is_the_default_and_reads_as_disabled():
    assert pd.ReactiveEffect(name="x", domain=pd.LIGHTING,
                             event=pd.EV_FRAG).intensity == pd.OFF
    assert not pd.ReactiveEffect(name="x", domain=pd.LIGHTING,
                                 event=pd.EV_FRAG).enabled


def test_negative_timing_rejected():
    with pytest.raises(ValueError):
        _effect(lead_us=-1)


# ── the OFF safety rule (directive 39) ──────────────────────────────────────

def test_every_pack_can_be_switched_fully_off():
    pack = pd.AssetPack(
        name="lab", profile=pd.PROFILE_PANTHEON,
        domains=((pd.WORLD_TEXTURES, "v" * 64),),
        effects=(_effect(), _effect(name="grade_pulse", domain=pd.POST_GRADE,
                                    event=pd.EV_FRAG, intensity=pd.HERO)))
    off = pack.with_all_effects_off()
    assert all(not e.enabled for e in off.effects)
    assert off.touched_domains == pack.touched_domains   # domains survive
    assert off.pack_id != pack.pack_id


def test_off_effects_resolve_to_nothing():
    pack = pd.AssetPack(name="lab", profile=pd.PROFILE_HERO,
                        effects=(_effect(intensity=pd.HERO),))
    anchors = [(pd.EV_PROJECTILE_IMPACT, 4_000_000)]
    assert pd.resolve_effects(pack, anchors)
    assert pd.resolve_effects(pack.with_all_effects_off(), anchors) == []


# ── packs ───────────────────────────────────────────────────────────────────

def test_a_domain_cannot_be_overridden_twice():
    with pytest.raises(ValueError, match="fight itself"):
        pd.AssetPack(name="x", profile=pd.PROFILE_RETRO,
                     domains=((pd.WORLD_TEXTURES, "a" * 64),
                              (pd.WORLD_TEXTURES, "b" * 64)))


def test_pack_reports_whether_it_invalidates_a_capture():
    post = pd.AssetPack(name="grade only", profile=pd.PROFILE_DARK,
                        domains=((pd.POST_GRADE, "v" * 64),))
    assert not post.affects_capture
    tex = pd.AssetPack(name="textures", profile=pd.PROFILE_UHD_FAITHFUL,
                       domains=((pd.WORLD_TEXTURES, "v" * 64),))
    assert tex.affects_capture


def test_an_enabled_capture_affecting_effect_also_invalidates_a_capture():
    pack = pd.AssetPack(name="fx", profile=pd.PROFILE_PANTHEON,
                        effects=(_effect(domain=pd.PARTICLE_FX,
                                         intensity=pd.HERO),))
    assert pack.affects_capture
    assert not pack.with_all_effects_off().affects_capture


def test_packs_touching_different_domains_do_not_collide():
    a = pd.AssetPack(name="a", profile=pd.PROFILE_PANTHEON,
                     domains=((pd.WORLD_TEXTURES, "1" * 64),))
    b = pd.AssetPack(name="b", profile=pd.PROFILE_PANTHEON,
                     domains=((pd.WEAPON_SKINS, "2" * 64),))
    assert not (a.touched_domains & b.touched_domains)


def test_unknown_profile_rejected():
    with pytest.raises(ValueError):
        pd.AssetPack(name="x", profile="CHROME")


# ── effect placement on the scene clock ─────────────────────────────────────

def test_effects_place_on_the_events_that_actually_occur():
    pack = pd.AssetPack(
        name="lab", profile=pd.PROFILE_HERO,
        effects=(_effect(intensity=pd.HERO, lead_us=100_000,
                         hold_us=400_000),
                 _effect(name="dodge_trail", domain=pd.SHADER_FX,
                         event=pd.EV_DODGE_HERO, intensity=pd.SUBTLE)))
    # this scene has an impact but no dodge
    fired = pd.resolve_effects(pack, [(pd.EV_PROJECTILE_IMPACT, 4_000_000)])
    assert len(fired) == 1
    assert fired[0]["name"] == "impact_flash"
    assert fired[0]["start_edit_us"] == 3_900_000
    assert fired[0]["end_edit_us"] == 4_400_000


def test_an_absent_event_never_relocates_the_effect():
    """The failure this guards: an effect nudged to a nearby timestamp so it
    appears to fire. If the evidence is absent the effect is absent."""
    pack = pd.AssetPack(name="lab", profile=pd.PROFILE_HERO,
                        effects=(_effect(event=pd.EV_ROUND_WIN,
                                         intensity=pd.HERO),))
    assert pd.resolve_effects(pack, [(pd.EV_FRAG, 1_000_000)]) == []


def test_lead_never_produces_a_negative_start():
    pack = pd.AssetPack(name="lab", profile=pd.PROFILE_HERO,
                        effects=(_effect(intensity=pd.HERO,
                                         lead_us=5_000_000),))
    fired = pd.resolve_effects(pack, [(pd.EV_PROJECTILE_IMPACT, 1_000_000)])
    assert fired[0]["start_edit_us"] == 0


def test_repeated_events_fire_the_effect_each_time():
    pack = pd.AssetPack(name="lab", profile=pd.PROFILE_HERO,
                        effects=(_effect(intensity=pd.HERO),))
    fired = pd.resolve_effects(pack, [(pd.EV_PROJECTILE_IMPACT, 1_000_000),
                                      (pd.EV_PROJECTILE_IMPACT, 4_000_000)])
    assert [f["start_edit_us"] for f in fired] == [1_000_000, 4_000_000]
