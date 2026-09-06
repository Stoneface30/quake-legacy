"""Public-repository privacy contract for the promoted master pool."""

from engine.parser import promote_masters as pm


def test_render_proof_identity_uses_anonymous_stable_keys(monkeypatch):
    demo = "CA-private-recorder-map-2012_01_02-03_04_05.dm_73"
    proof_key = pm.render_proof_key(demo, 123_456)
    assert "private-recorder" not in proof_key
    assert len(proof_key) == 64

    monkeypatch.setattr(pm, "RENDER_PROOFED_KEYS", {proof_key})
    assert pm.is_render_proofed(demo, 123_456)
    assert not pm.is_render_proofed(demo, 123_457)


def test_promoted_master_source_contains_no_private_demo_aliases():
    source = pm.__file__ and open(pm.__file__, encoding="utf-8").read().lower()
    assert "ptntr4sh" not in source
    assert "gr0str4sh" not in source
