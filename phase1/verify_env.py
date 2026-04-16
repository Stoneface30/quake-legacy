"""Verify all required tools and packages are present before running Phase 1."""
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
FFMPEG = ROOT / "tools" / "ffmpeg" / "ffmpeg.exe"

def check(label, ok, fix=""):
    status = "OK" if ok else "FAIL"
    print(f"  [{status}] {label}")
    if not ok and fix:
        print(f"    FIX: {fix}")
    return ok

def main():
    print("QUAKE LEGACY — Phase 1 Environment Check\n")
    all_ok = True

    all_ok &= check("Python 3.11+", sys.version_info >= (3, 11),
                    "Install Python 3.11+ from python.org")

    all_ok &= check("FFmpeg binary", FFMPEG.exists(),
                    f"Run: python tools/download_tools.py")

    # Check ffmpeg works
    if FFMPEG.exists():
        result = subprocess.run([str(FFMPEG), "-version"],
                                capture_output=True, text=True)
        version_line = result.stdout.split('\n')[0]
        all_ok &= check(f"FFmpeg version: {version_line}", result.returncode == 0)

    for pkg in ["ffmpeg", "moviepy", "streamlit", "tqdm"]:
        try:
            __import__(pkg.replace("-", "_"))
            all_ok &= check(f"Python: {pkg}", True)
        except ImportError:
            all_ok &= check(f"Python: {pkg}", False,
                           f"pip install {pkg}")

    # Check source clips exist
    clips_root = ROOT / "QUAKE VIDEO" / "T1"
    all_ok &= check("T1 clips directory", clips_root.exists(),
                    f"Expected: {clips_root}")

    for part in range(4, 13):
        part_dir = clips_root / f"Part{part}"
        count = len(list(part_dir.glob("*.avi"))) if part_dir.exists() else 0
        all_ok &= check(f"Part{part}: {count} AVI files", count > 0,
                        f"Expected AVI files in {part_dir}")

    print()
    if all_ok:
        print("All checks passed. Ready for Phase 1.")
    else:
        print("Fix issues above before proceeding.")
        sys.exit(1)

if __name__ == "__main__":
    main()
