"""Case A review pack: nine handoff durations, one screen, one clock.

The nine captures share an absolute timeline, so a grid synchronised on
shot time shows every variant leaving FPV on the same frame and arriving at
nine different ones. That is the comparison the eye needs; a sequential reel
would make the viewer hold 800 ms in memory while watching 100 ms.

Two artefacts:
  grid.mp4     3x3, each cell labelled with its requested duration
  strip.png    the same nine at four instants, for still comparison

The pack stays in output/. The captures are unmodified gameplay and Quake
Live burns opponent names into the frame, so nothing here is committed.

Usage:  camera_case_a_pack.py <case_a_dir>
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path("G:/QUAKE_LEGACY")
FFMPEG = REPO / "creative_suite/tools/ffmpeg/ffmpeg.exe"

# The interesting stretch, in shot-relative seconds: a beat of locked FPV,
# every variant's move, the impact at 4.5 s, and enough tail to settle.
CLIP_FROM_S = 2.8
CLIP_TO_S = 6.4
CELL_W, CELL_H = 640, 360
# drawtext needs an explicit face: this ffmpeg has libfreetype but no
# fontconfig, so it cannot resolve a default and fails inside a long chain.
FONT = r"C\:/Windows/Fonts/arial.ttf"


def run(args: list[str], timeout: int = 900) -> None:
    r = subprocess.run([str(a) for a in args], capture_output=True, text=True,
                       timeout=timeout)
    if r.returncode != 0:
        raise SystemExit(r.stderr[-1500:])


def delivered_handoff(raw: Path, launch_s: float, requested_ms: int) -> dict:
    """How long the move actually lasts in the delivered frames.

    The camera is locked before the handoff and locked after it, so the span
    where consecutive frames change fastest IS the move. Measured rather
    than assumed: this is what says the requested duration reached the
    picture instead of merely reaching the cfg.
    """
    import numpy as np
    work = raw.parent / f"_dh_{raw.stem}"
    work.mkdir(exist_ok=True)
    for old in work.glob("*.pgm"):
        old.unlink()
    lead, tail = 0.8, 1.4
    t0 = max(0.0, launch_s - lead)
    dur = lead + requested_ms / 1000.0 + tail
    run([FFMPEG, "-y", "-v", "error", "-ss", f"{t0:.3f}", "-t", f"{dur:.3f}",
         "-i", raw, "-vf", "scale=96:54,format=gray", "-vsync", "0",
         work / "f%05d.pgm"])
    frames = []
    for f in sorted(work.glob("*.pgm")):
        b = f.read_bytes()
        i = b.index(bytes([50, 53, 53, 10])) + 4
        frames.append(np.frombuffer(b[i:], dtype=np.uint8).astype(np.float64))
    for f in work.glob("*.pgm"):
        f.unlink()
    work.rmdir()
    if len(frames) < 6:
        return {"error": "too few frames"}
    d = np.array([float(np.abs(a - b).mean()) for a, b in zip(frames, frames[1:])])
    # The locked stretches set the floor; the move is everything well above it.
    floor = float(np.percentile(d, 20))
    peak = float(d.max())
    if peak <= floor * 1.5:
        return {"floor": round(floor, 2), "peak": round(peak, 2),
                "verdict": "NO_MOVE_DETECTED"}
    thr = floor + (peak - floor) * 0.25
    above = np.flatnonzero(d >= thr)
    span_frames = int(above[-1] - above[0] + 1)
    delivered_ms = span_frames * (1000.0 / 60.0)
    return {"floor": round(floor, 2), "peak": round(peak, 2),
            "moving_frames": span_frames,
            "delivered_ms": round(delivered_ms, 1),
            "requested_ms": requested_ms,
            "error_ms": round(delivered_ms - requested_ms, 1),
            "first_moving_frame_s": round(t0 + int(above[0]) / 60.0, 3)}


def main() -> None:
    d = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "output/demo_v2/_case_a"
    data = json.loads((d / "case_a.json").read_text())
    # The DELIVERED artefact, not the raw capture. The raw AVI still carries
    # 500 ms of head guard, so sampling it at shot-relative times lands half
    # a second early -- which made every variant look identical because the
    # move had not started in any of them.
    for r in data["ladder"]:
        vis = Path(str(r.get("raw", ""))).with_name(
            Path(str(r.get("raw", "x"))).name.replace(".raw.avi", ".visual.mp4"))
        if vis.exists():
            r["delivered_media"] = str(vis)
    rows = [r for r in data["ladder"] if r.get("delivered_media")]
    if len(rows) < 2:
        raise SystemExit(f"only {len(rows)} captures have raw video")

    launch_s = 3.375        # handoff start, identical in every variant
    impact_s = 4.5

    inputs: list[str] = []
    for r in rows:
        inputs += ["-ss", f"{CLIP_FROM_S:.3f}", "-t",
                   f"{CLIP_TO_S - CLIP_FROM_S:.3f}", "-i", r["delivered_media"]]

    # Each cell: scale, burn its duration, mark the move with a moving bar.
    parts, labels = [], []
    for i, r in enumerate(rows):
        ms = r["requested_duration_ms"]
        end_s = launch_s + ms / 1000.0
        # a progress bar that fills only while that variant is moving
        parts.append(
            f"[{i}:v]scale={CELL_W}:{CELL_H},"
            f"drawbox=x=0:y={CELL_H-26}:w={CELL_W}:h=26:color=black@0.55:t=fill,"
            f"drawtext=fontfile='{FONT}':text='{ms} ms':x=10:y={CELL_H-22}:"
            f"fontsize=20:fontcolor=white,"
            f"drawtext=fontfile='{FONT}':text='MOVING':x={CELL_W-90}:"
            f"y={CELL_H-22}:fontsize=18:fontcolor=yellow:"
            f"enable='between(t\\,{launch_s-CLIP_FROM_S:.3f}\\,{end_s-CLIP_FROM_S:.3f})',"
            f"drawbox=x=0:y={CELL_H-30}:w='{CELL_W}*"
            f"min(1\\,max(0\\,(t-{launch_s-CLIP_FROM_S:.3f})/{ms/1000.0:.3f}))'"
            f":h=4:color=yellow:t=fill[c{i}]")
        labels.append(f"[c{i}]")

    # ';' between chains, not '': concatenated, part i's trailing [ci] runs
    # straight into part i+1's leading [i+1:v] and the graph is malformed.
    grid = (f"{';'.join(parts)};{''.join(labels)}"
            f"xstack=inputs={len(rows)}:layout="
            + "|".join(f"{(i%3)*CELL_W}_{(i//3)*CELL_H}" for i in range(len(rows)))
            + f",drawtext=fontfile='{FONT}':text='CASE A   FPV to SIDE spline "
              f"handoff   one scene one path':x=12:y=8:fontsize=22:"
              f"fontcolor=white:box=1:boxcolor=black@0.6"
            + f",drawtext=fontfile='{FONT}':text='impact':x=12:y=40:"
              f"fontsize=18:fontcolor=red"
              f":enable='gte(t\\,{impact_s-CLIP_FROM_S:.3f})'[v]")

    for r in rows:
        r["delivered_handoff"] = delivered_handoff(
            Path(r["delivered_media"]), launch_s, r["requested_duration_ms"])
        dh = r["delivered_handoff"]
        print(f"  {r['requested_duration_ms']:>4} ms -> delivered "
              f"{dh.get('delivered_ms')} ms ({dh.get('moving_frames')} frames, "
              f"error {dh.get('error_ms')} ms)")
    (d / "case_a.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    (REPO / "docs/reference/camera_case_a.json").write_text(
        json.dumps(data, indent=2), encoding="utf-8")

    # The filter goes in a file. Passed inline this exact graph is rejected
    # with a bare "Error : Invalid argument" on Windows, while every one of
    # its filters works alone -- a quoting or length limit in argument
    # passing, not in the graph.
    fs = d / "_grid.filter"
    fs.write_text(grid, encoding="ascii")
    out = d / "case_a_grid.mp4"
    run([FFMPEG, "-y", "-v", "error", *inputs, "-filter_complex_script", fs,
         "-map", "[v]", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
         "-pix_fmt", "yuv420p", "-r", "60", out])
    print(f"grid: {out}")

    # stills: every variant at four instants across the move. Written as a
    # numbered sequence and tiled from one input -- a 36-input xstack is
    # rejected the same way the inline grid filter was.
    marks = [launch_s - 0.10, launch_s + 0.15, launch_s + 0.45, impact_s + 0.20]
    n = 0
    for r in rows:
        for t in marks:
            n += 1
            run([FFMPEG, "-y", "-v", "error", "-ss", f"{t:.3f}",
                 "-i", r["delivered_media"],
                 "-frames:v", "1", "-vf", f"scale={CELL_W//2}:{CELL_H//2}",
                 d / f"_tile_{n:03d}.png"])
    strip = d / "case_a_strip.png"
    run([FFMPEG, "-y", "-v", "error", "-i", str(d / "_tile_%03d.png"),
         "-vf", f"tile=4x{len(rows)}", "-frames:v", "1", strip])
    for f in d.glob("_tile_*.png"):
        f.unlink(missing_ok=True)
    print(f"strip: {strip}")


if __name__ == "__main__":
    main()
