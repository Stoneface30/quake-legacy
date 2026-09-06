"""WHAT WE KNOW BECAUSE SOMEONE LOOKED, AND WHEN IT STOPPED COUNTING.

Some questions this engine asks are settled by arithmetic: was the field
parsed, does the timestamp match, did the trace reconstruct. Those are tests.

Other questions are only answerable by a person with eyes: is the enemy
visibly Keel, does this camera feel right, does the effect communicate the
action. Those are not test failures waiting to be automated -- they are the
part of filmmaking that needs a human, and the answer is worth keeping.

THE POINT OF THIS MODULE IS TO STOP RE-PROVING. Five A/B renders of the same
green Keel is not rigour, it is a loop nobody chose. A proof is banked against
the three things that could invalidate it -- the backend, the profile and the
engine version -- and consumed until one of them changes.

    UNTESTED                    nobody has tried
    AUTOMATED_PASS              a machine measured it; no eye yet
    NEEDS_VISUAL_CONFIRMATION   a bundle exists and is waiting on a person
    VISUALLY_PROVEN             a person looked and said yes
    VISUALLY_REJECTED           a person looked and said no
    REGRESSION                  it was proven, and an input it depended on moved

A verdict that lives only in a chat message is not data. It is recorded here,
with what was on screen when it was given.
"""
from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from engine.pantheon import store as S

REGISTRY_DB = "visual_proofs.db"

SCHEMA = """
create table if not exists proofs (
  proof_id text primary key,
  capability text not null,
  semantic_expectation text not null,
  artifact_refs text not null,
  automated_results text not null,
  status text not null,
  human_verdict text,
  human_note text,
  engine_version text,
  backend text,
  profile text,
  recorded_at real,
  judged_at real);
create index if not exists ix_proofs_capability on proofs(capability, recorded_at);
"""


class Status(str, Enum):
    UNTESTED = "UNTESTED"
    AUTOMATED_PASS = "AUTOMATED_PASS"
    NEEDS_VISUAL_CONFIRMATION = "NEEDS_VISUAL_CONFIRMATION"
    VISUALLY_PROVEN = "VISUALLY_PROVEN"
    VISUALLY_REJECTED = "VISUALLY_REJECTED"
    REGRESSION = "REGRESSION"


USABLE = (Status.VISUALLY_PROVEN,)


class ProofUnavailable(RuntimeError):
    """Raised by require() when a capability has no usable visual proof."""


@dataclass
class VisualProof:
    capability: str
    proof_id: str
    semantic_expectation: str        # in film words: what a viewer should see
    artifact_refs: tuple[str, ...] = ()   # stills, clips, contact sheets
    automated_results: dict = field(default_factory=dict)
    status: Status = Status.UNTESTED
    human_verdict: str | None = None
    human_note: str | None = None
    engine_version: str | None = None
    backend: str | None = None
    profile: str | None = None
    recorded_at: float = 0.0
    judged_at: float | None = None

    @property
    def usable(self) -> bool:
        return self.status in USABLE

    def depends_on(self) -> dict:
        """The three inputs that can invalidate this proof."""
        return {"backend": self.backend, "profile": self.profile,
                "engine_version": self.engine_version}

    def as_dict(self) -> dict:
        return {"capability": self.capability, "proof_id": self.proof_id,
                "semantic_expectation": self.semantic_expectation,
                "artifact_refs": list(self.artifact_refs),
                "automated_results": self.automated_results,
                "status": self.status.value, "human_verdict": self.human_verdict,
                "human_note": self.human_note, "depends_on": self.depends_on(),
                "recorded_at": self.recorded_at, "judged_at": self.judged_at}


# Names this project used for the same fact before the handoff settled on one.
# Kept so an older caller resolves rather than reading UNTESTED.
ALIASES = {"GREEN_KEEL_REVIEW": "REVIEW_GREEN_KEEL"}


def canonical(capability: str) -> str:
    return ALIASES.get(capability, capability)


def db_path() -> Path:
    return S.store_root() / REGISTRY_DB


def _open() -> sqlite3.Connection:
    p = db_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(p, timeout=60)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con


def _row(r: sqlite3.Row) -> VisualProof:
    return VisualProof(
        capability=r["capability"], proof_id=r["proof_id"],
        semantic_expectation=r["semantic_expectation"],
        artifact_refs=tuple(json.loads(r["artifact_refs"])),
        automated_results=json.loads(r["automated_results"]),
        status=Status(r["status"]), human_verdict=r["human_verdict"],
        human_note=r["human_note"], engine_version=r["engine_version"],
        backend=r["backend"], profile=r["profile"],
        recorded_at=r["recorded_at"], judged_at=r["judged_at"])


def record(proof: VisualProof) -> VisualProof:
    """Bank a proof, or update the one with this id."""
    con = _open()
    try:
        con.execute(
            "insert or replace into proofs values(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (proof.proof_id, proof.capability, proof.semantic_expectation,
             json.dumps(list(proof.artifact_refs)),
             json.dumps(proof.automated_results), proof.status.value,
             proof.human_verdict, proof.human_note, proof.engine_version,
             proof.backend, proof.profile, proof.recorded_at or time.time(),
             proof.judged_at))
        con.commit()
    finally:
        con.close()
    return proof


def get(proof_id: str) -> VisualProof | None:
    con = _open()
    try:
        r = con.execute("select * from proofs where proof_id=?", (proof_id,)).fetchone()
    finally:
        con.close()
    return _row(r) if r else None


def for_capability(capability: str) -> list[VisualProof]:
    """Every proof for a capability, newest first."""
    con = _open()
    try:
        rows = con.execute("select * from proofs where capability=? "
                           "order by recorded_at desc",
                           (canonical(capability),)).fetchall()
    finally:
        con.close()
    return [_row(r) for r in rows]


def judge(proof_id: str, *, verdict: str, note: str = "") -> VisualProof:
    """Record what the person said. This is the only way a proof becomes
    VISUALLY_PROVEN -- no automated result promotes itself."""
    proof = get(proof_id)
    if proof is None:
        raise KeyError(f"no such proof: {proof_id}")
    yes = str(verdict).strip().upper() in {"YES", "PASS", "APPROVED", "PROVEN", "OK"}
    proof.status = Status.VISUALLY_PROVEN if yes else Status.VISUALLY_REJECTED
    proof.human_verdict = str(verdict).strip().upper()
    proof.human_note = note or None
    proof.judged_at = time.time()
    return record(proof)


def status(capability: str, *, backend: str | None = None,
           profile: str | None = None, engine_version: str | None = None) -> Status:
    """What do we know about this capability, for THESE inputs?

    A proof taken against a different backend, profile or engine version is
    not evidence about this one -- it is a REGRESSION signal saying the
    question is open again.
    """
    proofs = for_capability(capability)
    if not proofs:
        return Status.UNTESTED
    asked = {"backend": backend, "profile": profile,
             "engine_version": engine_version}
    matching = [p for p in proofs
                if all(v is None or getattr(p, k) == v for k, v in asked.items())]
    if matching:
        return matching[0].status
    # There IS a proof, but not for what was asked.
    if any(p.status is Status.VISUALLY_PROVEN for p in proofs):
        return Status.REGRESSION
    return proofs[0].status


def proven(capability: str, **inputs) -> bool:
    return status(capability, **inputs) is Status.VISUALLY_PROVEN


def require(capability: str, **inputs) -> VisualProof:
    """Consume a banked proof. Never re-runs anything; if the proof is not
    there, it says what would settle it instead of silently filming."""
    st = status(capability, **inputs)
    if st is not Status.VISUALLY_PROVEN:
        raise ProofUnavailable(
            f"{capability} is {st.value} for {inputs or 'any inputs'}; "
            f"produce a bundle and ask the user, do not assume")
    proofs = for_capability(capability)
    return next(p for p in proofs if p.status is Status.VISUALLY_PROVEN)


def awaiting_human() -> list[VisualProof]:
    """Everything with a bundle sitting in front of nobody."""
    con = _open()
    try:
        rows = con.execute("select * from proofs where status=? order by recorded_at",
                           (Status.NEEDS_VISUAL_CONFIRMATION.value,)).fetchall()
    finally:
        con.close()
    return [_row(r) for r in rows]


def report() -> dict:
    con = _open()
    try:
        by = {r[0]: r[1] for r in con.execute(
            "select status, count(*) from proofs group by status")}
        caps = con.execute("select count(distinct capability) from proofs").fetchone()[0]
    finally:
        con.close()
    return {"db": str(db_path()), "capabilities": caps, "by_status": by,
            "awaiting_human": len(awaiting_human())}


# -- seeding from what was actually filmed ---------------------------------
#
# Conservative on purpose. A proof is VISUALLY_PROVEN only where the user
# looked at the artefact and said so in the session that produced it; where
# the artefact exists but the judgement was mine, it is
# NEEDS_VISUAL_CONFIRMATION and stays there until a person answers.

VR = "docs/visual-record"

SEED: tuple[VisualProof, ...] = (
    VisualProof(
        # The name the handoff brief uses. GREEN_KEEL_REVIEW was the id an
        # earlier sprint gave the same fact; ALIASES below keeps a lookup of
        # the old name working rather than pretending it never existed.
        capability="REVIEW_GREEN_KEEL",
        proof_id="REVIEW_GREEN_KEEL/2026-09-06/offscreen-review",
        semantic_expectation="ENEMY = KEEL / BRIGHT / GREEN, unmistakable at a "
                             "glance. TEAM = preserved. SELF = preserved. The "
                             "teammate and the recorder keep the look the demo "
                             "authored.",
        artifact_refs=(f"{VR}/2026-09-06/green_keel/A_authentic.png",
                       f"{VR}/2026-09-06/green_keel/B_review.png",
                       f"{VR}/2026-09-06/green_keel/green_keel_proof.json",
                       f"{VR}/2026-09-06/green_keel/rebuild_proof.py"),
        automated_results={
            "strong_green_pixels_review": 49509,
            "strong_green_pixels_authentic": 2,
            "mean_rgb_of_green": [85, 230, 125],
            "verdict": "GREEN_ENEMY_PROVEN",
            "measured_at_units": 81,
            "moment": {"demo_hash": "e4bd2a36495928d0", "client": 2,
                       "victim": 1, "server_time_ms": 579825},
            "controlled": ("same demo, same serverTime, same camera; the ONLY "
                           "variable is the VisualProfile"),
            "offscreen": {"visible_windows": [], "stole_focus": False},
            # Hashes so the proof survives the files moving or being edited.
            # A changed hash means the artefact is no longer the one that was
            # judged, which is a reason to look again rather than to trust it.
            "artifact_sha256_16": {
                "A_authentic.png": "499ed9a2179ff9be",
                "B_review.png": "652afb5a611d9423",
                "green_keel_proof.json": "ccb857277d043e98",
                "rebuild_proof.py": "785e482fe8a57e9f"}},
        status=Status.VISUALLY_PROVEN,
        human_verdict="YES", human_note="accepted in the sprint-7 brief: "
                                        "'green Keel review enemy proven in pixels'",
        backend="PANTHEON_QUAKE_OFFSCREEN", profile="REVIEW",
        engine_version="wolfcamql-11.3"),

    VisualProof(
        capability="OFFSCREEN_NO_VISIBLE_WINDOW",
        proof_id="OFFSCREEN_NO_VISIBLE_WINDOW/2026-09-06/hidden-desktop",
        semantic_expectation="While a capture runs, nothing appears on the "
                             "operator's screen.",
        artifact_refs=("docs/reference/pantheon_engine_architecture.md",),
        automated_results={"visible_windows": [], "probe": "notepad on the "
                           "hidden desktop, then real captures"},
        status=Status.VISUALLY_PROVEN,
        human_verdict="YES", human_note="accepted in the sprint-8 brief: "
                                        "'hidden/offscreen hardware Quake capture'",
        backend="PANTHEON_QUAKE_OFFSCREEN", profile="REVIEW",
        engine_version="wolfcamql-11.3"),

    VisualProof(
        capability="OFFSCREEN_NO_FOCUS_STEAL",
        proof_id="OFFSCREEN_NO_FOCUS_STEAL/2026-09-06/hidden-desktop",
        semantic_expectation="A capture never takes the foreground from "
                             "whatever the operator is doing.",
        artifact_refs=("docs/reference/pantheon_engine_architecture.md",),
        automated_results={"stole_focus": False,
                           "sampled": "throughout every run, not only after"},
        status=Status.VISUALLY_PROVEN,
        human_verdict="YES", human_note="accepted in the sprint-8 brief",
        backend="PANTHEON_QUAKE_OFFSCREEN", profile="REVIEW",
        engine_version="wolfcamql-11.3"),

    VisualProof(
        capability="OFFSCREEN_POINTER_FREE",
        proof_id="OFFSCREEN_POINTER_FREE/2026-09-06/in-nograb",
        semantic_expectation="While a capture runs the operator's mouse moves "
                             "over the whole desktop, not just the render's "
                             "invisible rectangle.",
        artifact_refs=(),
        automated_results={
            "reported_by": "the user, against the hidden desktop",
            "as_shipped_clip": [107, 130, 2027, 1210],
            "virtual_screen": [0, 0, 3000, 1440],
            "in_nograb_1": "released, still filmed",
            "in_mouse_0": "released, still filmed",
            "after_fix": {"confined_cursor": False, "visible_windows": [],
                          "stole_focus": False, "filmed": True}},
        status=Status.NEEDS_VISUAL_CONFIRMATION,
        human_note="measured on a real capture; the user reported the defect "
                   "and should confirm it is gone on their own desktop",
        backend="PANTHEON_QUAKE_OFFSCREEN", profile="REVIEW",
        engine_version="wolfcamql-11.3"),

    VisualProof(
        capability="XRAY_PLAYER",
        proof_id="XRAY_PLAYER/2026-09-05/cg-wh",
        semantic_expectation="Enemies read through walls as coloured "
                             "silhouettes, teammates a different colour.",
        artifact_refs=(f"{VR}/2026-09-05/cg_wh_ab_overlay_proof.png",
                       f"{VR}/2026-09-05/cg_wh_enemy_green_teammate_blue.png",
                       f"{VR}/2026-09-05/cg_wh_colour_proof.png",
                       f"{VR}/2026-09-05/cg_wh_enemy_green_zoom.png"),
        automated_results={"note": "A/B stills with the overlay on and off"},
        status=Status.NEEDS_VISUAL_CONFIRMATION,
        human_note="filmed under the WOLFCAM_REFERENCE window before the "
                   "offscreen backend existed; not re-shot",
        backend="WOLFCAM_REFERENCE", profile="REVIEW",
        engine_version="wolfcamql-11.3"),

    VisualProof(
        capability="SYNTHETIC_KEEL_MODEL",
        proof_id="SYNTHETIC_KEEL_MODEL/2026-09-05/compiled-demo",
        semantic_expectation="A compiled synthetic .dm_73 plays in a real "
                             "client and the actor is the intended character.",
        artifact_refs=(f"{VR}/2026-09-05/green_keel_synthetic_proof_01.png",),
        automated_results={"note": "compiled demo played back in the client"},
        status=Status.NEEDS_VISUAL_CONFIRMATION,
        backend="WOLFCAM_REFERENCE", profile="REVIEW",
        engine_version="wolfcamql-11.3"),

    VisualProof(
        capability="TORSO_GESTURE",
        proof_id="TORSO_GESTURE/2026-09-05/gesture-proof-01",
        semantic_expectation="An authored torso gesture reads as a deliberate "
                             "movement, not a twitch or a T-pose.",
        artifact_refs=(f"{VR}/2026-09-05/gesture_proof_01_torso_gesture.png",),
        automated_results={"note": "single still from a compiled performance"},
        status=Status.NEEDS_VISUAL_CONFIRMATION,
        backend="WOLFCAM_REFERENCE", profile="REVIEW",
        engine_version="wolfcamql-11.3"),

    VisualProof(
        capability="PUBLIC_EXPORT_NO_BURNED_NAME",
        proof_id="PUBLIC_EXPORT_NO_BURNED_NAME/2026-09-04/export-profile",
        semantic_expectation="A clip meant for the public carries no player "
                             "name anywhere in the frame.",
        artifact_refs=(f"{VR}/2026-09-04/before_public_export_burns_victim_name.png",
                       f"{VR}/2026-09-04/after_public_export_profile_no_name.png",
                       f"{VR}/2026-09-04/after_exported_clip_clean_same_window.png"),
        automated_results={"note": "before/after on the same window"},
        status=Status.VISUALLY_PROVEN,
        human_verdict="YES",
        human_note="the defect and its fix were both reviewed by the user",
        backend="WOLFCAM_REFERENCE", profile="PUBLIC_EXPORT",
        engine_version="wolfcamql-11.3"),

    VisualProof(
        capability="REVIEW_EXPOSURE_READABLE",
        proof_id="REVIEW_EXPOSURE_READABLE/2026-09-03/network-brightness",
        semantic_expectation="The review picture is readable: not blown out, "
                             "not crushed, shadowed areas still legible.",
        artifact_refs=(f"{VR}/2026-09-03/before_network_brightness_enemy_green_review.png",),
        automated_results={"env_mean": 65.8, "blown_pct": 6.36,
                           "crushed_pct": 16.90, "contrast": 76.2,
                           "chosen": "gamma/intensity 0.85, overbright 1"},
        status=Status.NEEDS_VISUAL_CONFIRMATION,
        backend="WOLFCAM_REFERENCE", profile="REVIEW",
        engine_version="wolfcamql-11.3"),
)


def seed(*, overwrite: bool = False) -> dict:
    """Put the known proofs in the registry. Existing rows are left alone
    unless asked, because a human verdict recorded here outranks this file."""
    added, kept = 0, 0
    for p in SEED:
        if not overwrite and get(p.proof_id) is not None:
            kept += 1
            continue
        record(VisualProof(**{**p.__dict__, "recorded_at": p.recorded_at or time.time()}))
        added += 1
    return {"seeded": added, "already_present": kept, **report()}


def main() -> int:                                           # pragma: no cover
    import argparse
    ap = argparse.ArgumentParser(description="the visual proof registry")
    ap.add_argument("--seed", action="store_true")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--capability")
    ap.add_argument("--judge", metavar="PROOF_ID")
    ap.add_argument("--verdict", default="YES")
    ap.add_argument("--note", default="")
    a = ap.parse_args()
    if a.seed:
        print(json.dumps(seed(overwrite=a.overwrite), indent=1))
    if a.judge:
        print(json.dumps(judge(a.judge, verdict=a.verdict, note=a.note).as_dict(), indent=1))
    if a.capability:
        print(json.dumps([p.as_dict() for p in for_capability(a.capability)], indent=1))
    if not (a.seed or a.judge or a.capability):
        print(json.dumps(report(), indent=1))
        for p in awaiting_human():
            print(f"  awaiting a person: {p.proof_id}\n    {p.semantic_expectation}")
    return 0


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main())
