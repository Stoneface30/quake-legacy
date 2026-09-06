"""Film PRESENTER_CAMERA_DIALOGUE_PROOF_02 — the camera comes to Crash.

BACKEND module: the only place this proof touches Wolfcam. The scene itself
is built headless by presenter_performance_proof.build(camera=True,
line=True); this module films it under the shared RenderPermit, colours the
analysis rail through timed cvars for the freeze window only, muxes the one
DialogueCue on the edit clock, and validates the artefact against the launch
before anything is claimed.

    python -m engine.pantheon.presenter_camera_film
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from engine.pantheon.backends import BackendUse, render
from engine.pantheon.dialogue_mix import build_dialogue_stem, mux
from engine.pantheon.presenter_performance_proof import build
from engine.pantheon.shot import (PassKind, ShotSpec, SourceKind, VisualProfile,
                                  analysis_graphic_commands)

SCENE_ID = "PRESENTER_CAMERA_DIALOGUE_PROOF_02"
SHOT_START = 0.8
FFPROBE = Path("G:/QUAKE_LEGACY/creative_suite/tools/ffmpeg/ffprobe.exe")


def main() -> int:
    demo, scene, built, rep = build(camera=True, line=True, scene_id=SCENE_ID)
    b = rep["breaks"][0]
    freeze_ms = int((b["edit_freeze_start_s"] - SHOT_START) * 1000)
    resume_ms = int((b["edit_freeze_end_s"] - SHOT_START) * 1000)
    end_s = rep["edit_duration_s"] - 0.3
    spec = ShotSpec(
        shot_id=SCENE_ID, source=demo.resolve(), source_kind=SourceKind.SYNTHETIC,
        start_s=SHOT_START, end_s=end_s,
        visual=VisualProfile(name="PRESENTER_CAMERA", extra={
            # history keeps its own rail colours: the family is UNSET here and
            # only switched to ANALYSIS_GRAPHIC inside the freeze by `at`
            "cg_railUseOwnColors": 0,
            "cg_teamRailColor1": '""', "cg_teamRailColor2": '""',
            "cg_enemyRailColor1": '""', "cg_enemyRailColor2": '""',
            "cg_enemyLegsColor": '""', "cg_enemyTorsoColor": '""',
            "cg_enemyHeadColor": '""', "cg_teamLegsColor": '""',
            "cg_teamTorsoColor": '""', "cg_teamHeadColor": '""',
            "r_mapOverBrightBits": 2, "r_gamma": 1.2, "cg_shadows": 0}),
        passes=(PassKind.BEAUTY,), provenance=SCENE_ID,
        timed_commands=tuple(analysis_graphic_commands(freeze_ms, resume_ms)),
        truth_reference=Path(".tmp/synthetic") / f"{SCENE_ID}.composite.frametruth.json")
    print(f"analysis graphic window: shot +{freeze_ms}ms .. +{resume_ms}ms "
          f"({len(spec.timed_commands)} timed cvars)", flush=True)
    avi = render("WOLFCAM_REFERENCE", shot=spec, out_dir=Path(".tmp/shots"),
                 use=BackendUse.REFERENCE_RENDER)
    man = spec.manifest["BEAUTY"]
    print(f"filmed  : {avi} ({avi.stat().st_size/1e6:.1f} MB) probe={man['duration_s']}s "
          f"requested={man['requested_s']}s exit={man['engine_exit']} "
          f"profile={man['profile']} provenance={man['provenance']}", flush=True)
    stem = build_dialogue_stem(Path(".tmp/synthetic") / f"{SCENE_ID}.dialogue.json",
                               Path(".tmp/shots") / f"{SCENE_ID}_dialogue.wav",
                               shot_start_s=SHOT_START, duration_s=end_s - SHOT_START)
    out = mux(avi, stem, Path(".tmp/shots") / f"{SCENE_ID}.mp4")
    probe = subprocess.run([str(FFPROBE), "-v", "error", "-show_entries",
                            "stream=codec_type,codec_name,width,height,duration",
                            "-of", "csv=p=0", str(out)], capture_output=True, text=True).stdout
    print(f"delivered: {out} ({out.stat().st_size/1e6:.1f} MB)\n{probe.strip()}", flush=True)
    (Path(".tmp/shots") / f"{SCENE_ID}.manifest.json").write_text(
        json.dumps({"beauty": man, "deliverable": str(out), "probe": probe}, indent=1))
    return 0


if __name__ == "__main__":                     # pragma: no cover - CLI
    raise SystemExit(main())
