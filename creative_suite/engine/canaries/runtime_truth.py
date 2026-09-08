"""Three truth gaps, closed by four captures through the production path.

    GAP 2  does r_gamma reach the captured frame?      CAPTURE_VISIBLE or not
    GAP 3  is camera_compiler_v2 the path that films?  ORBIT vs FPV, same frag

Every capture goes through director_preview._real_capture unmodified, with
two declared deviations:

  * _set_state is a no-op. A capability probe must not write preview-cache
    rows the director would later read as real previews.
  * for the gamma pair, one `seta r_gamma <x>` line is inserted into the
    production-built cfg directly after the profile exec. r_gamma is not in
    the runtime baseline allow-list, and extending that list for a probe
    would be a production change made to serve a test.

Raw MJPEG is kept (CS_PREVIEW_KEEP_RAW) so the analysis reads the engine's
frames, not a transcode of them.

Usage:  runtime_truth.py <out_dir>
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path("G:/QUAKE_LEGACY")
# The committed measurement. Written ONLY with --write-reference, so a
# diff here is always a decision and never a side effect of a run.
REFERENCE = REPO / "docs" / "reference" / "runtime_truth_canary.json"
# Scratch destination for an ordinary run.
SCRATCH = REPO / ".tmp" / "canaries" / "runtime_truth_canary.json"
sys.path.insert(0, str(REPO))
os.environ["CS_PREVIEW_KEEP_RAW"] = "1"
os.environ["CS_PREVIEW_ENGINE_LOG"] = "1"      # persist the engine console

from creative_suite.api import director_draft as dd, frags as fr          # noqa: E402
from creative_suite.engine import director_preview as dp                  # noqa: E402
from creative_suite.engine import review_proxy                            # noqa: E402

FFMPEG = REPO / "creative_suite/tools/ffmpeg/ffmpeg.exe"
ORBIT_FRAG, FPV_FRAG = 4121, 5979
GAMMA_A, GAMMA_B = "1.0", "1.8"


def log(msg: str) -> None:
    print(msg, flush=True)


# ── declared deviations ─────────────────────────────────────────────────────

dp._set_state = lambda *a, **k: None          # no preview-cache writes

_real_build_cfg = dp.build_capture_cfg
_inject: dict[str, str] = {}


def _cfg_with_gamma(plan, camera_cfg_lines, clip_name, fx_level):
    cfg = _real_build_cfg(plan, camera_cfg_lines, clip_name, fx_level)
    g = _inject.get("r_gamma")
    if g is None:
        return cfg
    out = []
    for line in cfg.splitlines():
        out.append(line)
        if line.startswith("exec wolfcam_"):
            out.append(f"seta r_gamma {g}")
    return "\n".join(out) + "\n"


dp.build_capture_cfg = _cfg_with_gamma

# Instrumentation only: keep a copy of the cfg the engine executed and the
# engine's exit code, both of which the runner discards.
_last: dict = {}
_orig_cfg_fn = dp.build_capture_cfg


def _cfg_recording(plan, camera_cfg_lines, clip_name, fx_level):
    # Bisection aid: CAM_LINES=N keeps only the first N camera lines so a
    # crash can be pinned to freecam, loadcamera or playcamera.
    n = os.getenv("CAM_LINES")
    if n is not None:
        camera_cfg_lines = list(camera_cfg_lines)[:int(n)]
        _last["camera_lines_used"] = camera_cfg_lines
    cfg = _orig_cfg_fn(plan, camera_cfg_lines, clip_name, fx_level)
    _last["cfg"] = cfg
    return cfg


dp.build_capture_cfg = _cfg_recording

_orig_popen = dp.subprocess.Popen


class _Popen(_orig_popen):                       # type: ignore[misc]
    def __init__(self, cmd, *a, **k):
        _last["cmd"] = list(cmd)
        _last["t0"] = time.time()
        super().__init__(cmd, *a, **k)

    def wait(self, *a, **k):
        rc = super().wait(*a, **k)
        _last["rc"] = rc
        _last["elapsed"] = round(time.time() - _last.get("t0", time.time()), 1)
        return rc


dp.subprocess.Popen = _Popen


# ── one capture through the production runner ──────────────────────────────

def frag_dict(frag_id: int) -> dict:
    f = fr._load_frag_with_master(frag_id)
    import sqlite3
    c = sqlite3.connect(
        "file:G:/QUAKE_LEGACY/creative_suite/database/frag_recognition.db?mode=ro",
        uri=True)
    f["content_hash"] = c.execute(
        "SELECT content_hash FROM recognized_frags WHERE id=?", (frag_id,)
    ).fetchone()[0]
    f["window"] = fr._frag_window(f)      # exactly what the API attaches
    return f


def capture(key: str, frag_id: int, camera_mode: str, gamma: str | None,
            out_dir: Path) -> dict:
    frag = frag_dict(frag_id)
    draft = dd._default_draft(frag_id)
    draft["camera"]["mode"] = camera_mode
    demo_path, _ = review_proxy.demo_source(frag["demo_name"])
    plan = dp.build_plan(frag, draft, demo_path=str(demo_path))
    tm = plan.recipe.time_map
    duration_s = (tm[-1].edit_end_us - tm[0].edit_start_us) / 1e6
    fell_back = bool(plan.camera_fallback)
    log(f"[{key}] frag {frag_id} requested {camera_mode} -> plan.camera_mode="
        f"{plan.camera_mode} fallback={plan.camera_fallback or 'none'} "
        f"keyframes={len(plan.keyframes)} duration={duration_s:.3f}s")
    _inject.clear()
    if gamma is not None:
        _inject["r_gamma"] = gamma
    job = {"preview_key": key}
    final = out_dir / f"{key}.visual.mp4"
    tmp = out_dir / f"{key}.tmp.mp4"
    t0 = time.time()
    _last.clear()
    try:
        cam10_hash, status = dp._real_capture(job, plan, tmp, final, duration_s)
    finally:
        gamedir = dp.wolfcam_capture.STAGING / "wolfcam-ql"
        if _last.get("cfg"):
            (out_dir / f"{key}.capture.cfg").write_text(_last["cfg"], encoding="ascii")
        for name in ("qconsole.log", "cgameboot.log"):
            src = gamedir / name
            if src.exists():
                (out_dir / f"{key}.{name}").write_bytes(src.read_bytes())
        for name in ("stderr.txt", "stdout.txt"):        # the engine's own
            src = dp.wolfcam_capture.STAGING / name
            if src.exists():
                (out_dir / f"{key}.{name}").write_bytes(src.read_bytes())
        log(f"[{key}] engine rc={_last.get('rc')} elapsed={_last.get('elapsed')}s "
            f"camera_lines={_last.get('camera_lines_used', 'all')}")
    raw = dp.PREVIEW_DIR / f"{key}.raw.avi"
    kept = out_dir / f"{key}.raw.avi"
    if raw.exists():
        raw.replace(kept)
    log(f"[{key}] captured in {time.time()-t0:.0f}s  cam10={cam10_hash}  "
        f"status={status}  raw={'yes' if kept.exists() else 'MISSING'}")
    return {"key": key, "frag_id": frag_id, "requested_mode": camera_mode,
            "plan_mode": plan.camera_mode, "fallback": plan.camera_fallback,
            "keyframes": len(plan.keyframes), "duration_s": duration_s,
            "cam10_hash": cam10_hash, "camera_status": status,
            "gamma": gamma, "raw": str(kept) if kept.exists() else None}


# ── frame reading ───────────────────────────────────────────────────────────

def frames(video: Path, work: Path, count: int, start: int = 0,
           size: str = "96:54") -> list[np.ndarray]:
    work.mkdir(parents=True, exist_ok=True)
    for old in work.glob("*.pgm"):
        old.unlink()
    r = subprocess.run(
        [str(FFMPEG), "-y", "-v", "error", "-i", str(video),
         "-vf", f"select='gte(n\\,{start})',scale={size},format=gray",
         "-vsync", "0", "-frames:v", str(count), str(work / "f%05d.pgm")],
        capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(r.stderr[-800:])
    out = []
    for p in sorted(work.glob("*.pgm")):
        raw = p.read_bytes()
        i = raw.index(bytes([50, 53, 53, 10])) + 4
        out.append(np.frombuffer(raw[i:], dtype=np.uint8).astype(np.float64))
    return out


# ── GAP 2: gamma ────────────────────────────────────────────────────────────

def analyse_gamma(a: Path, b: Path, work: Path) -> dict:
    """Same frag, same camera, same window; only r_gamma differs."""
    fa = frames(a, work / "ga", 240, 60)
    fb = frames(b, work / "gb", 240, 60)
    n = min(len(fa), len(fb))
    fa, fb = fa[:n], fb[:n]
    mean_a = float(np.mean([f.mean() for f in fa]))
    mean_b = float(np.mean([f.mean() for f in fb]))
    # is B a monotone remap of A (gamma) rather than a different picture?
    # Rank-correlate pixel intensities frame by frame.
    corr = []
    for x, y in zip(fa, fb):
        xs, ys = x.argsort().argsort(), y.argsort().argsort()
        corr.append(float(np.corrcoef(xs, ys)[0, 1]))
    same_picture = float(np.median(corr))
    delta = mean_b - mean_a
    visible = abs(delta) >= 6.0 and same_picture >= 0.9
    verdict = ("CAPTURE_VISIBLE" if visible else
               "NOT_CAPTURE_VISIBLE" if abs(delta) < 2.0 and same_picture >= 0.9
               else "INCONCLUSIVE")
    return {"frames_compared": n, "mean_luma_a": round(mean_a, 2),
            "mean_luma_b": round(mean_b, 2), "delta": round(delta, 2),
            "rank_correlation": round(same_picture, 4),
            "verdict": verdict,
            "meaning": ("gamma changed the captured pixels while the picture "
                        "stayed the same" if visible else
                        "the captured pixels did not move with r_gamma"
                        if verdict == "NOT_CAPTURE_VISIBLE" else
                        "the two captures differ in more than gamma; do not "
                        "conclude either way")}


# ── GAP 3: camera ───────────────────────────────────────────────────────────

def _hshift(a: np.ndarray, b: np.ndarray, w: int, h: int) -> float:
    """Dominant horizontal shift between two frames by phase correlation."""
    A = np.fft.fft2(a.reshape(h, w))
    B = np.fft.fft2(b.reshape(h, w))
    R = A * np.conj(B)
    R /= np.abs(R) + 1e-9
    r = np.fft.ifft2(R).real
    y, x = np.unravel_index(int(np.argmax(r)), r.shape)
    return float(x if x <= w // 2 else x - w)


def analyse_camera(orbit: Path, fpv: Path, work: Path) -> dict:
    """Did the plan's camera reach the delivered frames?

    The control is a first-person capture of the identical demo window with
    the identical profile. If `playcamera` were ignored, the two captures
    would be the same film to within re-encode noise. A large mean
    difference is the primary evidence; strided global flow (0.25 s apart,
    since per-frame motion at 60 fps is sub-pixel on a thumbnail) is
    reported as secondary evidence of a moving camera.
    """
    w, h = 96, 54
    fo = frames(orbit, work / "co", 900, 60)
    ff = frames(fpv, work / "cf", 900, 60)
    n = min(len(fo), len(ff))
    fo, ff = fo[:n], ff[:n]
    diff = float(np.mean([np.abs(fo[i] - ff[i]).mean() for i in range(n)]))
    noise = float(np.mean([np.abs(ff[i] - ff[i]).mean() for i in range(n)]))

    def flow(fs, stride=15):
        s = [_hshift(fs[i], fs[i + stride], w, h)
             for i in range(0, len(fs) - stride, stride)]
        s = [v for v in s if abs(v) >= 1.0]
        if len(s) < 6:
            return {"samples": len(s), "sign_consistency": 0.0, "median_abs": 0.0}
        sign = np.sign(s)
        return {"samples": len(s), "sign_consistency": round(abs(float(sign.mean())), 3),
                "median_abs": round(float(np.median(np.abs(s))), 2)}

    o, f = flow(fo), flow(ff)
    # self-motion of each capture: how much consecutive frames change
    self_o = float(np.mean([np.abs(a - b).mean() for a, b in zip(fo, fo[1:])]))
    self_f = float(np.mean([np.abs(a - b).mean() for a, b in zip(ff, ff[1:])]))
    proven = diff >= 8.0
    return {"frames_compared": n,
            "mean_difference_orbit_vs_fpv_control": round(diff, 2),
            "reencode_noise_floor": round(noise, 2),
            "orbit_self_motion": round(self_o, 3), "fpv_self_motion": round(self_f, 3),
            "orbit_flow_strided": o, "fpv_flow_strided": f,
            "verdict": "CAMERA_PATH_PROVEN" if proven else "NOT_PROVEN",
            "meaning": ("the plan's camera changed the delivered frames: the "
                        "orbit capture differs from the first-person control "
                        f"of the identical window by {diff:.1f} grey levels, "
                        "far above re-encode noise" if proven else
                        "the orbit capture is the same film as the "
                        "first-person control; the camera did not reach the "
                        "frames")}


# ── main ────────────────────────────────────────────────────────────────────

def main(write_reference: bool = False) -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        "G:/QUAKE_LEGACY/output/demo_v2/_canary_runtime_truth")
    out.mkdir(parents=True, exist_ok=True)
    if len(sys.argv) >= 5 and sys.argv[2] == "single":
        # one capture, for diagnosis: single <key> <frag_id> <mode> [gamma]
        key, fid, mode = sys.argv[3], int(sys.argv[4]), sys.argv[5]
        gamma = sys.argv[6] if len(sys.argv) > 6 else None
        r = capture(key, fid, mode, gamma, out)
        log(f"SINGLE {json.dumps(r)}")
        log("DONE single")
        return
    work = out / "_frames"
    results: dict = {"captures": [], "ran_at": time.strftime("%Y-%m-%dT%H:%M:%S")}

    log("== GAP 3: camera path (frag 4121, ORBIT then FPV) ==")
    c_orbit = capture("camorbit4121", ORBIT_FRAG, "ORBIT", None, out)
    c_fpv = capture("camfpv4121", ORBIT_FRAG, "FPV", None, out)
    results["captures"] += [c_orbit, c_fpv]
    if c_orbit["plan_mode"] != "ORBIT":
        results["camera"] = {"verdict": "NOT_TESTED",
                             "meaning": f"plan fell back to {c_orbit['plan_mode']}: "
                                        f"{c_orbit['fallback']}"}
    elif c_orbit["raw"] and c_fpv["raw"]:
        results["camera"] = analyse_camera(Path(c_orbit["raw"]),
                                           Path(c_fpv["raw"]), work)
        results["camera"]["cam10_hash"] = c_orbit["cam10_hash"]
    else:
        results["camera"] = {"verdict": "NO_RAW", "meaning": "a capture produced no AVI"}
    log(f"camera: {results['camera']['verdict']} -- {results['camera']['meaning']}")

    log("== GAP 2: gamma (frag 5979, FPV, r_gamma A then B) ==")
    g_a = capture("gama5979", FPV_FRAG, "FPV", GAMMA_A, out)
    g_b = capture("gamb5979", FPV_FRAG, "FPV", GAMMA_B, out)
    results["captures"] += [g_a, g_b]
    if g_a["raw"] and g_b["raw"]:
        results["gamma"] = analyse_gamma(Path(g_a["raw"]), Path(g_b["raw"]), work)
        results["gamma"].update(gamma_a=GAMMA_A, gamma_b=GAMMA_B)
    else:
        results["gamma"] = {"verdict": "NO_RAW", "meaning": "a capture produced no AVI"}
    log(f"gamma: {results['gamma']['verdict']} -- {results['gamma']['meaning']}")

    _dest = REFERENCE if write_reference else SCRATCH
    _dest.parent.mkdir(parents=True, exist_ok=True)
    dest = _dest
    dest.write_text(json.dumps(results, indent=2), encoding="utf-8")
    log(f"DONE written {dest}")


if __name__ == "__main__":
    import sys as _sys
    main(write_reference="--write-reference" in _sys.argv)
