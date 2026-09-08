"""CAMERA_CUT: do the four frames either side of a cut have the right identity?

The insert sweep showed the inserted DURATION is exact. That is necessary and
not sufficient: two equal and opposite boundary offsets preserve the total
while putting both cuts on the wrong frame. This checks the frames
themselves.

Real gameplay, no synthetic counters. Each source frame is fingerprinted by
hashing a downscaled grayscale version, so a frame in the output can be
matched back to the exact frame it came from.

    A  last outgoing source frame       expect source[k-1]
    B  first inserted frame             expect insert[j]
    C  last inserted frame              expect insert[j+m-1]
    D  first source frame after return  expect source[k]
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

FFMPEG = Path("G:/QUAKE_LEGACY/creative_suite/tools/ffmpeg/ffmpeg.exe")
WORK = Path("C:/Users/STONEF~1/AppData/Local/Temp/claude/G--QUAKE-LEGACY/"
            "d45475ae-45f3-46d3-a1c3-d4282ba81b1e/scratchpad/cutproof")
FPS = 30          # the source footage is natively 30; forcing 60 duplicates
                  # every frame, which makes frame identity undecidable
K = 30          # frames of source before the cut
M = 24          # frames of insert
TAIL = 30       # frames of source after the return


def run(args):
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        print(" ".join(str(a) for a in args[:8]), "...")
        print(r.stderr[-1500:])
        raise SystemExit(f"ffmpeg failed ({r.returncode})")
    return r


def fingerprints(video: Path, out_dir: Path, limit: int | None = None):
    """One small grayscale thumbnail per frame.

    Not a hash. The output is re-encoded, so its pixels differ slightly from
    the source's and any exact digest would fail to match a frame with
    itself. Identity is therefore established by nearest thumbnail, with a
    margin check so a near-tie is never reported as a match.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*.pgm"):
        old.unlink()
    args = [str(FFMPEG), "-y", "-v", "error", "-i", str(video),
            "-vf", "scale=32:18,format=gray", "-vsync", "0"]
    if limit:
        args += ["-frames:v", str(limit)]
    args += [str(out_dir / "f%05d.pgm")]
    run(args)
    out = []
    for p in sorted(out_dir.glob("*.pgm")):
        raw = p.read_bytes()
        i = raw.index(bytes([50, 53, 53, 10])) + 4      # skip the PGM header
        out.append(np.frombuffer(raw[i:], dtype=np.uint8).astype(np.int16))
    return out


def identify(frame, pool):
    """Which frame of `pool` this is, and how confident that is.

    Returns (index, distance, margin). The margin is how much better the best
    match is than the runner-up; without it, a static shot could match any of
    several frames and we would report a coincidence as a proof.
    """
    d = np.array([float(np.abs(frame - c).mean()) for c in pool])
    order = np.argsort(d)
    best = int(order[0])
    second = float(d[order[1]]) if len(order) > 1 else float("inf")
    return best, float(d[best]), second - float(d[best])


# How much better the winner must be than the runner-up before a match counts.
# In thumbnail grey levels; small because the identity is exact when it holds
# and the alternative is an adjacent frame of moving gameplay.
MIN_MARGIN = 0.5


def normalise(src: Path, dst: Path, start_frame: int, count: int):
    """One clip at a known frame rate, so frame indices mean something."""
    run([str(FFMPEG), "-y", "-v", "error", "-i", str(src),
         "-vf", f"select='gte(n\\,{start_frame})',setpts=N/{FPS}/TB",
         "-vsync", "cfr", "-r", str(FPS), "-frames:v", str(count),
         "-c:v", "libx264", "-crf", "15", "-preset", "veryfast",
         "-pix_fmt", "yuv420p", "-an", str(dst)])


def main():
    global FPS
    if len(sys.argv) >= 4:
        vids = [Path(sys.argv[1]), Path(sys.argv[2])]
        FPS = int(sys.argv[3])
    else:
        raise SystemExit("usage: cut_identity.py <source> <insert> <fps>")
    if not all(v.exists() for v in vids):
        raise SystemExit("both clips must exist")
    print(f"source: {vids[0].name}   insert: {vids[1].name}   fps: {FPS}")
    WORK.mkdir(parents=True, exist_ok=True)

    def moving_window(raw: Path, need: int, probe: Path, scan: int = 200):
        """Find a run of frames the footage actually distinguishes.

        A frame-identity proof needs frames that differ from their
        neighbours. Static footage -- a warmup, a held view -- cannot support
        it, so the window is chosen from the clip rather than assumed.
        """
        normalise(raw, probe, 0, scan)
        fp = fingerprints(probe, probe.parent / (probe.stem + "_fp"))
        diffs = [float(np.abs(a - b).mean()) for a, b in zip(fp, fp[1:])]
        best_i, best_v = None, -1.0
        for i in range(0, max(1, len(diffs) - need)):
            v = min(diffs[i:i + need])
            if v > best_v:
                best_i, best_v = i, v
        return best_i or 0, best_v

    src_raw, ins_raw = vids[0], vids[1]
    source = WORK / "source.mp4"
    insert = WORK / "insert.mp4"
    s_off, s_move = moving_window(src_raw, K + TAIL, WORK / "probe_src.mp4")
    i_off, i_move = moving_window(ins_raw, M, WORK / "probe_ins.mp4")
    print(f"source window at frame {s_off} (min adjacent motion {s_move:.2f})")
    print(f"insert window at frame {i_off} (min adjacent motion {i_move:.2f})")
    normalise(src_raw, source, s_off, K + TAIL)
    normalise(ins_raw, insert, i_off, M)

    src_fp = fingerprints(source, WORK / "fp_src")
    ins_fp = fingerprints(insert, WORK / "fp_ins")
    print(f"source frames {len(src_fp)}  insert frames {len(ins_fp)}")

    # Each reference frame must be distinguishable from its own neighbours,
    # or a match proves nothing.
    for label, pool, idx in (("source[K-1]", src_fp, K - 1),
                             ("source[K]", src_fp, K),
                             ("insert[0]", ins_fp, 0),
                             ("insert[M-1]", ins_fp, M - 1)):
        i, dist, margin = identify(pool[idx], pool)
        if i != idx or margin < MIN_MARGIN:
            raise SystemExit(
                f"{label} is not distinguishable from its neighbours "
                f"(nearest {i}, margin {margin:.2f}); choose a window with "
                f"motion before trusting this proof")
    print("all four reference frames are distinguishable from their neighbours")

    # cut out and back: source[0..K) + insert[0..M) + source[K..)
    head = WORK / "head.mp4"
    tail = WORK / "tail.mp4"
    run([str(FFMPEG), "-y", "-v", "error", "-i", str(source),
         "-frames:v", str(K), "-c", "copy", str(head)])
    run([str(FFMPEG), "-y", "-v", "error", "-i", str(source),
         "-vf", f"select='gte(n\\,{K})',setpts=N/{FPS}/TB",
         "-vsync", "cfr", "-r", str(FPS), "-c:v", "libx264", "-crf", "15",
         "-preset", "veryfast", "-pix_fmt", "yuv420p", "-an", str(tail)])

    lst = WORK / "concat.txt"
    lst.write_text("".join(f"file '{p.as_posix()}'\n"
                           for p in (head, insert, tail)), encoding="utf-8")
    out = WORK / "cut_proof.mp4"
    run([str(FFMPEG), "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", str(lst), "-vsync", "cfr", "-r", str(FPS),
         "-c:v", "libx264", "-crf", "15", "-preset", "veryfast",
         "-pix_fmt", "yuv420p", "-an", str(out)])

    got = fingerprints(out, WORK / "fp_out")
    print(f"delivered frames {len(got)}  expected {K + M + TAIL}")

    checks = [
        ("A_last_outgoing_source", K - 1, src_fp, K - 1, "source"),
        ("B_first_inserted", K, ins_fp, 0, "insert"),
        ("C_last_inserted", K + M - 1, ins_fp, M - 1, "insert"),
        ("D_first_returning_source", K + M, src_fp, K, "source"),
    ]
    result = {"fps": FPS, "k": K, "m": M, "tail": TAIL,
              "delivered_frames": len(got),
              "expected_frames": K + M + TAIL,
              "method": "nearest 32x18 grayscale thumbnail, with a margin "
                        "check so a near-tie is never called a match",
              "checks": []}
    ok_all = True
    header = ("IDENTITY", "OUT", "WANT", "GOT", "DIST", "MARGIN")
    print()
    print(f"  {header[0]:<28}{header[1]:>4}{header[2]:>6}{header[3]:>6}"
          f"{header[4]:>7}{header[5]:>8}   verdict")
    for name, out_idx, pool, want_idx, which in checks:
        if out_idx >= len(got):
            print(f"  {name:<28} missing frame")
            ok_all = False
            continue
        got_idx, dist, margin = identify(got[out_idx], pool)
        ok = (got_idx == want_idx) and margin >= MIN_MARGIN
        ok_all &= ok
        note = "" if ok else f"  (off by {got_idx - want_idx} in {which})"
        print(f"  {name:<28}{out_idx:>4}{want_idx:>6}{got_idx:>6}{dist:>7.2f}"
              f"{margin:>8.2f}   {'MATCH' if ok else 'WRONG'}{note}")
        result["checks"].append({"identity": name, "output_frame": out_idx,
                                 "expected_index": want_idx,
                                 "identified_index": got_idx,
                                 "distance": round(dist, 3),
                                 "margin": round(margin, 3),
                                 "pool": which, "match": bool(ok)})
    result["all_four_agree"] = bool(ok_all)
    result["duration_exact"] = len(got) == K + M + TAIL
    print(f"\n  all four agree: {ok_all}")
    print(f"  duration exact: {result['duration_exact']}")
    dest = Path(f"G:/QUAKE_LEGACY/docs/reference/camera_cut_frame_identity_{FPS}fps.json")
    dest.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"  written: {dest}")


if __name__ == "__main__":
    main()
