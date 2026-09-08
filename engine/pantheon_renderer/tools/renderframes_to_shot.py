"""Turn a saved RenderFrame JSON into a shot script the cgame host can read.

WHY THIS EXISTS. The .shot files sitting in the worktrees were written by an
older revision of ``render_frame.save_shot_script`` and no longer match the
parser: eighteen fields on an actor line where the host wants twenty-two. The
host answered that by segfaulting, because ParseShot raises Com_Error before
Com_Init has brought the zone allocator up -- a stale file therefore looked
exactly like a crash in the renderer.

The JSON is the durable artefact; the shot script is a wire format. This
regenerates the second from the first, so a stale script is a re-run rather
than an archaeology problem.

WHAT IS NOT WRITTEN HERE. The per-part frame/oldframe/backlerp columns are
emitted as zeros. Those are PANTHEON's own headless evaluation of the engine's
stateful lerp rule, and they exist to CHECK cgame, not to feed it -- with cgame
rendering, it runs its own interpolation from the animation numbers. Writing a
computed pose into a file that cgame will ignore would invite someone later to
trust a column nothing reads.

    python renderframes_to_shot.py IN.json OUT.shot OUTDIR [--fps N]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def convert(src: Path, dest: Path, out_dir: Path, stem: str = "pf") -> int:
    doc = json.loads(src.read_text(encoding="utf-8"))
    frames = doc["frames"]
    if not frames:
        raise SystemExit(f"{src}: no frames")

    roster: list[tuple[str, str]] = []
    models: list[str] = []
    for f in frames:
        for a in f.get("actors", []):
            key = (a["model"], a.get("skin") or "default")
            if key not in roster:
                roster.append(key)
            wm = a.get("weapon_model")
            if wm and wm not in models:
                models.append(wm)
        for pr in f.get("projectiles", []):
            if pr["model"] not in models:
                models.append(pr["model"])

    first = frames[0]
    out = [
        "# pantheon shot script v1 -- regenerated from RenderFrame JSON",
        "map %s" % first["map"],
        "size 1280 720",
        "provenance %s" % first.get("camera", {}).get("source", "UNKNOWN"),
        "demo %s" % doc.get("demo_hash", "UNKNOWN"),
        "lighting CINEMATIC",
    ]
    out += ["player %s %s" % (m, sk) for m, sk in roster]
    out += ["model %s" % m for m in models]

    for i, f in enumerate(frames):
        c = f["camera"]
        out.append(
            "frame %d %d %.3f %.3f %.3f %.3f %.3f %.3f %.2f %s"
            % (f["frame_index"], f["server_time_ms"],
               c["origin"][0], c["origin"][1], c["origin"][2],
               c["angles"][0], c["angles"][1], c["angles"][2],
               c.get("fov", 90.0),
               (out_dir / ("%s_%05d.tga" % (stem, i))).as_posix()))
        for a in f.get("actors", []):
            wm = a.get("weapon_model")
            out.append(
                "actor %d %.3f %.3f %.3f %d %d 0 0 0.000000 0 0 0.000000 "
                "%.4f %.4f %.4f %.4f %.4f %.4f %.4f %.4f %.4f %d"
                % (roster.index((a["model"], a.get("skin") or "default")),
                   a["origin"][0], a["origin"][1], a["origin"][2],
                   a["legs_anim"], a["torso_anim"],
                   0.0, a.get("legs_yaw", 0.0), 0.0,
                   a.get("torso_pitch", 0.0), a.get("torso_yaw", 0.0), 0.0,
                   a.get("view_pitch", 0.0), a.get("torso_yaw", 0.0), 0.0,
                   models.index(wm) if wm else -1))
        for pr in f.get("projectiles", []):
            out.append(
                "projectile %d %.3f %.3f %.3f %.3f %.3f %.3f"
                % (models.index(pr["model"]),
                   pr["origin"][0], pr["origin"][1], pr["origin"][2],
                   pr["angles"][0], pr["angles"][1], pr["angles"][2]))

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(out) + "\n", encoding="utf-8")
    return len(frames)


if __name__ == "__main__":
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    n = convert(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
    print("%s: %d frames -> %s" % (sys.argv[1], n, sys.argv[2]))
