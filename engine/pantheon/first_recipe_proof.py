"""THE FIRST COMPLETE RECIPE, END TO END.

ReviewMoment -> MomentPossibilities -> EffectRecipe -> ChoreographyPlan ->
ShotSpec -> BackendPlan -> one offscreen render -> a proof bundle a person can
judge.

Nothing here shortcuts the chain. The moment is resolved through the ordinary
production API, the reveal is placed by a measurement over the real map, the
backend is chosen by the planner, and the render happens ONCE. If the answer
is technical the machine fixes it; if the answer is visual it goes to the
person, and their verdict ends the experiment.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

TARGET = "PERF:FIRE_ROCKET:acd726fd089a1011:7:447500"
RECIPE = "XRAY_ACTOR"


@dataclass
class ProofRun:
    performance_id: str
    recipe: str
    moment: dict = field(default_factory=dict)
    plan: dict = field(default_factory=dict)
    shot: dict = field(default_factory=dict)
    backend_plan: dict = field(default_factory=dict)
    render: dict = field(default_factory=dict)
    bundle: dict = field(default_factory=dict)
    proof_id: str = ""

    def as_dict(self) -> dict:
        return {"performance_id": self.performance_id, "recipe": self.recipe,
                "moment": self.moment, "choreography": self.plan,
                "shot_spec": self.shot, "backend_plan": self.backend_plan,
                "render": self.render, "bundle": self.bundle,
                "proof_id": self.proof_id}


def _shot_spec(plan, *, demo: Path, shot_id: str, profile: str = "REVIEW"):
    """A plan becomes a ShotSpec HERE, on the backend side of the boundary.

    The passes come from the cues: a plan that reveals anything needs the
    X-ray pass as well as the beauty pass, and ShotSpec already knows which
    passes this backend has proven.
    """
    from engine.pantheon import shot as SHOT

    reveals = any(c.semantic.startswith("XRAY") for c in plan.cues)
    passes = ((SHOT.PassKind.BEAUTY, SHOT.PassKind.ACTOR_XRAY) if reveals
              else (SHOT.PassKind.BEAUTY,))
    return SHOT.ShotSpec(
        shot_id=shot_id, source=demo, source_kind=SHOT.SourceKind.HISTORICAL,
        start_s=plan.time.start_ms / 1000.0, end_s=plan.time.end_ms / 1000.0,
        visual=SHOT.VisualProfile(name=profile, xray=reveals),
        passes=passes, provenance=f"RECIPE:{plan.recipe}")


def preflight(performance_id: str = TARGET, recipe_id: str = RECIPE) -> dict:
    """Everything that can fail without filming anything."""
    from engine.pantheon import effect_recipes as ER
    from engine.pantheon import possibilities as POSS
    from engine.pantheon import review_moment as RM

    rm = RM.load(performance_id)
    mp = POSS.for_moment(performance_id)
    mine = next(p for p in mp.possibilities if p.recipe == recipe_id)
    return {"moment": rm, "possibilities": mp, "chosen": mine,
            "compatible": mine.compatible,
            "recipe_status": ER.status(recipe_id).value}


def run(performance_id: str = TARGET, recipe_id: str = RECIPE, *,
        out_dir: Path | None = None, staging: Path | None = None,
        render: bool = True) -> ProofRun:
    from creative_suite.engine import master_profile as mp_cfg
    from creative_suite.engine import wolfcam_capture as wc
    from engine.pantheon import backend_planner as BP
    from engine.pantheon import choreography as CH
    from engine.pantheon import offscreen as O
    from engine.pantheon import performance_index as PI
    from engine.pantheon import store as S
    from engine.pantheon import visual_profile as VP

    staging = staging or (S.PROJECT_ROOT / "output" / "demo_v2" / "_wolfcam_staging")
    out_dir = out_dir or (S.PROJECT_ROOT / "docs" / "visual-record"
                          / time.strftime("%Y-%m-%d") / "xray_actor_proof")
    out_dir.mkdir(parents=True, exist_ok=True)

    pre = preflight(performance_id, recipe_id)
    if not pre["compatible"]:
        raise RuntimeError(
            f"{recipe_id} is not compatible with {performance_id}: "
            f"{pre['chosen'].reasons}")

    rm = pre["moment"]
    out = ProofRun(performance_id, recipe_id, moment=rm.as_dict())

    con = PI._ro()
    (path,) = con.execute("select path from demos where demo_hash = ?",
                          (rm.playback.demo_hash,)).fetchone()
    demo = Path(path)

    # THE GATE: recipe + moment -> plan, and plan -> shot. No render call may
    # exist outside this chain.
    plan = CH.plan_xray_actor(rm, demo=demo)
    out.plan = plan.as_dict()
    if not plan.cues:
        raise RuntimeError(f"no plan: {plan.deferred}")

    shot_id = f"xray_{rm.playback.demo_hash[:8]}_{rm.playback.server_time_ms}"
    spec = _shot_spec(plan, demo=demo, shot_id=shot_id)
    # THE REPORT IS COMMITTED, AND A DEMO FILENAME CARRIES A PLAYER'S HANDLE.
    # The hash identifies the source completely and names nobody, which is the
    # repository's rule and not a preference.
    out.shot = {**spec.as_dict(), "source": f"demo_hash:{rm.playback.demo_hash}"}

    bplan = BP.plan(recipes=(recipe_id,))
    out.backend_plan = bplan.as_dict()
    beauty = bplan.passes[0]
    if beauty.backend is None:
        raise RuntimeError("the planner found no backend for the beauty pass")

    if not render:
        return out

    safe = wc.stage_demo(demo, staging=staging)
    windows = [{"clip_name": shot_id,
                "start_ms": plan.time.start_ms, "end_ms": plan.time.end_ms}]
    cues = [{"at_ms": c.at_ms, "semantic": c.semantic} for c in plan.cues]
    res = O.capture(safe, windows, staging=staging,
                    profile=mp_cfg.REVIEW_PROFILE_NAME,
                    profile_cvars=VP.profile("REVIEW").resolve(),
                    cues=cues,
                    purpose=f"first recipe proof: {recipe_id}")
    out.render = {k: v for k, v in res.items() if k != "avis"}
    out.render["avi"] = res["avis"].get(shot_id)
    return out


def bundle(out: ProofRun, *, out_dir: Path) -> dict:
    """Three frames and one short clip. Nothing else: a twenty-image contact
    sheet is a diagnostic, and this is a question for a person."""
    import subprocess

    from engine.pantheon import measure as M

    avi = out.render.get("avi")
    if not avi:
        return {"made": False, "why": out.render.get("detail")}

    reveal = out.plan["measurements"]["reveal"]
    t0 = out.plan["time"]["start_ms"]
    at = {"A_before_xray": (reveal["on_ms"] - t0 - 400) / 1000.0,
          "B_xray": ((reveal["on_ms"] + reveal["off_ms"]) / 2 - t0) / 1000.0,
          "C_after_xray": (reveal["off_ms"] - t0 + 500) / 1000.0}
    frames = {}
    for name, t in at.items():
        dest = out_dir / f"{name}.png"
        M.save_still(Path(avi), max(t, 0.05), dest)
        frames[name] = str(dest)

    mp4 = out_dir / "xray_actor_proof.mp4"
    subprocess.run([str(M.FFMPEG), "-v", "error", "-y", "-i", str(avi),
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                    str(mp4)], check=True, timeout=900)
    return {"made": True, "frames": frames, "mp4": str(mp4),
            "seconds_at": {k: round(v, 2) for k, v in at.items()}}


def record_proof(out: ProofRun) -> str:
    """Bank it as NEEDS_VISUAL_CONFIRMATION. Only a person makes it PROVEN."""
    from engine.pantheon import visual_proof as VP

    pid = (f"{out.recipe}/{time.strftime('%Y-%m-%d')}/"
           f"{out.performance_id.split(':')[2][:8]}")
    VP.record(VP.VisualProof(
        capability=out.recipe, proof_id=pid,
        semantic_expectation=(
            "During the approach the enemy is hidden by the geometry and reads "
            "through it as a green silhouette; when they step into normal view "
            "the overlay clears and the kill plays as ordinary Quake."),
        artifact_refs=tuple(str(v) for v in
                            list(out.bundle.get("frames", {}).values())
                            + ([out.bundle["mp4"]] if out.bundle.get("mp4") else [])),
        automated_results={
            "occlusion": out.plan["measurements"].get("counts")
            or out.plan["measurements"],
            "reveal_ms": out.plan["measurements"]["reveal"]["on_ms"],
            "clear_ms": out.plan["measurements"]["reveal"]["off_ms"],
            "visible_windows": out.render.get("visible_windows"),
            "stole_focus": out.render.get("stole_focus"),
            "confined_cursor": out.render.get("confined_cursor"),
            "seconds": out.render.get("seconds")},
        status=VP.Status.NEEDS_VISUAL_CONFIRMATION,
        backend="PANTHEON_QUAKE_OFFSCREEN", profile="REVIEW",
        engine_version="wolfcamql-11.3", recorded_at=time.time()))
    return pid


def main() -> int:                                           # pragma: no cover
    import argparse
    from engine.pantheon import store as S

    ap = argparse.ArgumentParser(description="the first end-to-end recipe")
    ap.add_argument("--performance", default=TARGET)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    out_dir = (S.PROJECT_ROOT / "docs" / "visual-record" / time.strftime("%Y-%m-%d")
               / "xray_actor_proof")
    out = run(a.performance, out_dir=out_dir, render=not a.dry_run)
    if not a.dry_run:
        out.bundle = bundle(out, out_dir=out_dir)
        out.proof_id = record_proof(out)
    dest = (S.REPO_ROOT / "docs" / "reference"
            / f"{time.strftime('%Y-%m-%d')}-xray-actor-first-recipe.json")
    dest.write_text(json.dumps(out.as_dict(), indent=1), encoding="utf-8")
    print(json.dumps({"plan_cues": [c["semantic"] for c in out.plan["cues"]],
                      "render": {k: out.render.get(k) for k in
                                 ("ok", "visible_windows", "stole_focus",
                                  "confined_cursor", "seconds")},
                      "bundle": out.bundle.get("frames"),
                      "proof": out.proof_id, "report": str(dest)}, indent=1))
    return 0


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main())
