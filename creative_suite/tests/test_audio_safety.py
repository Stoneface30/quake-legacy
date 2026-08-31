"""Audio safety: the OUTPUT true peak is the invariant, not the input gains.

Part12_highlight.mp4 measured +1.94 dBFS -- a violent blast in headphones.
Cause: `amix ... normalize=0` SUMS its inputs, and nothing bounded the result.

The load-bearing property is FINAL_OUTPUT_TRUE_PEAK <= -1.0 dBTP. Summed input
gains exceeding unity is NOT itself a defect -- float mixing may legitimately
exceed unity internally provided a later stage contains it. These tests
therefore assert the containment stage exists and is last, and provide the
measurement helper used to gate finished renders.
"""
import subprocess
import re
from pathlib import Path

import pytest

from creative_suite.engine import render_highlight as R
from creative_suite.engine.config import Config


def measure_true_peak(path: Path) -> dict:
    """Post-ENCODE measurement. Lossy encoding can move peaks, so this must run
    on the finished mp4, never on an intermediate PCM stream."""
    cfg = Config()
    r = subprocess.run(
        [str(cfg.ffmpeg_bin), "-nostats", "-i", str(path),
         "-af", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True, text=True, timeout=1800)
    out = r.stderr
    def grab(pat):
        m = re.search(pat, out)
        return float(m.group(1)) if m else None
    return {
        "integrated_lufs": grab(r"I:\s*(-?[\d.]+)\s*LUFS"),
        "true_peak_dbtp": grab(r"Peak:\s*(-?[\d.]+)\s*dBFS"),
        "lra": grab(r"LRA:\s*(-?[\d.]+)\s*LU"),
    }


def test_safety_stage_exists_after_the_mix():
    import inspect
    src = inspect.getsource(R.mux_music)
    assert "loudnorm" in src, "a true-peak-aware stage must bound the summed mix"
    assert src.index("amix") < src.index("loudnorm"), "ceiling must follow the sum"
    assert src.index("loudnorm") < src.rindex("[aout]"), "ceiling must be last"


def test_true_peak_target_is_below_the_acceptance_ceiling():
    """Aim under the gate so encoder overshoot cannot breach it."""
    assert R.TARGET_TP < R.SAFE_TP_CEILING
    assert R.SAFE_TP_CEILING <= -1.0


def test_no_gain_filter_follows_the_safety_stage():
    import inspect
    src = inspect.getsource(R.mux_music)
    tail = src[src.index("loudnorm"):]
    assert "volume=" not in tail, "no gain may be applied after the ceiling"


def test_measurement_helper_reads_a_real_file():
    """The gate measures the encoded mp4; a missing file must not pass silently."""
    res = measure_true_peak(Path("does_not_exist.mp4"))
    assert res["true_peak_dbtp"] is None
