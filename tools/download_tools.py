"""
download_tools.py — Automated tool downloader for QUAKE LEGACY project.

Downloads and installs all required tools into tools/ subdirectories.
Run from the project root: python tools/download_tools.py

Each tool is documented, versioned, and stored in its own subdirectory.
"""

import os
import sys
import subprocess
import urllib.request
import zipfile
import tarfile
import shutil
from pathlib import Path

TOOLS_DIR = Path(__file__).parent
PROJECT_ROOT = TOOLS_DIR.parent

# ─── Tool Definitions ────────────────────────────────────────────────────────

TOOLS = {
    "ffmpeg": {
        "description": "FFmpeg — video encode/decode/filter engine",
        "url": "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
        "type": "zip",
        "install_dir": TOOLS_DIR / "ffmpeg",
        "binary_check": TOOLS_DIR / "ffmpeg" / "ffmpeg.exe",
        "notes": "Windows essentials build from gyan.dev. Includes ffmpeg, ffprobe, ffplay.",
    },
    "uberdemotools": {
        "description": "UberDemoTools — Quake Live demo parser (C++)",
        "url": "https://github.com/mightycow/uberdemotools/releases/latest",
        "type": "github_release",
        "install_dir": TOOLS_DIR / "uberdemotools",
        "binary_check": TOOLS_DIR / "uberdemotools" / "UDT_json.exe",
        "notes": "Get the Windows binary release. Key tool: UDT_json.exe for frag extraction.",
    },
    "wolfcamql": {
        "description": "WolfcamQL — Quake Live demo renderer + freecam",
        "url": "https://github.com/brugal/wolfcamql/releases/latest",
        "type": "github_release",
        "install_dir": TOOLS_DIR / "wolfcamql",
        "binary_check": TOOLS_DIR / "wolfcamql" / "wolfcamql.exe",
        "notes": (
            "After download, copy Quake Live .pk3 files to tools/wolfcamql/baseq3/\n"
            "QL paks: Steam\\steamapps\\common\\Quake Live\\baseq3\\"
        ),
    },
    "qldemo_python": {
        "description": "qldemo-python — Python Quake Live demo parser",
        "url": "https://github.com/Quakecon/qldemo-python",
        "type": "git_clone",
        "install_dir": TOOLS_DIR / "qldemo-python",
        "notes": "Requires C compiler for pyhuffman extension. Run: pip install -e tools/qldemo-python",
    },
    "blur": {
        "description": "f0e/blur — cinematic motion blur (VapourSynth + FFmpeg)",
        "url": "https://github.com/f0e/blur/releases/latest",
        "type": "github_release",
        "install_dir": TOOLS_DIR / "blur",
        "binary_check": TOOLS_DIR / "blur" / "blur.exe",
        "notes": (
            "Requires VapourSynth: https://github.com/vapoursynth/vapoursynth/releases\n"
            "Config in tools/blur/config.yaml"
        ),
    },
    "ghidra": {
        "description": "Ghidra — binary reverse engineering (for WolfWhisperer.exe)",
        "url": "https://github.com/NationalSecurityAgency/ghidra/releases/latest",
        "type": "zip",
        "install_dir": TOOLS_DIR / "ghidra",
        "binary_check": TOOLS_DIR / "ghidra" / "ghidraRun.bat",
        "notes": "Requires Java 17+ JDK. Download from adoptium.net.",
    },
}

# ─── Python Packages ─────────────────────────────────────────────────────────

PYTHON_PACKAGES = [
    "ffmpeg-python",
    "moviepy>=2.0.0",
    "streamlit>=1.30.0",
    "requests>=2.31.0",
    "tqdm>=4.66.0",
]

# ─── Helpers ──────────────────────────────────────────────────────────────────

def print_header(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print('='*60)

def print_step(msg):
    print(f"  → {msg}")

def print_ok(msg):
    print(f"  ✓ {msg}")

def print_warn(msg):
    print(f"  ⚠ {msg}")

def already_installed(tool_name, tool_cfg):
    check = tool_cfg.get("binary_check")
    if check and Path(check).exists():
        return True
    return Path(tool_cfg["install_dir"]).exists() and any(Path(tool_cfg["install_dir"]).iterdir())

# ─── Installers ──────────────────────────────────────────────────────────────

def install_python_packages():
    print_header("Python packages")
    for pkg in PYTHON_PACKAGES:
        print_step(f"pip install {pkg}")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", pkg],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print_ok(pkg)
        else:
            print_warn(f"Failed: {pkg}\n{result.stderr[:200]}")

def install_zip_tool(name, cfg):
    """Download a zip, extract to install_dir."""
    install_dir = Path(cfg["install_dir"])
    install_dir.mkdir(parents=True, exist_ok=True)
    zip_path = install_dir / f"{name}.zip"

    print_step(f"Downloading {cfg['url']}")
    try:
        urllib.request.urlretrieve(cfg["url"], zip_path,
            reporthook=lambda b, bs, t: print(f"\r  {b*bs/1024/1024:.1f}MB", end=""))
        print()
    except Exception as e:
        print_warn(f"Download failed: {e}")
        print_warn(f"Manual download: {cfg['url']}")
        print_warn(f"Extract to: {install_dir}")
        return

    print_step("Extracting...")
    with zipfile.ZipFile(zip_path, 'r') as z:
        # Extract top-level contents (strip leading dir if single root folder)
        members = z.namelist()
        top_dirs = set(m.split('/')[0] for m in members)
        if len(top_dirs) == 1:
            top = list(top_dirs)[0]
            z.extractall(install_dir.parent)
            extracted = install_dir.parent / top
            if extracted != install_dir:
                shutil.move(str(extracted), str(install_dir))
        else:
            z.extractall(install_dir)
    zip_path.unlink(missing_ok=True)
    print_ok(f"Installed to {install_dir}")

def install_git_clone(name, cfg):
    """Clone a git repository."""
    install_dir = Path(cfg["install_dir"])
    if install_dir.exists():
        print_step("Updating existing clone...")
        subprocess.run(["git", "pull"], cwd=install_dir)
    else:
        print_step(f"Cloning {cfg['url']}")
        result = subprocess.run(["git", "clone", cfg["url"], str(install_dir)])
        if result.returncode != 0:
            print_warn(f"Clone failed. Manual: git clone {cfg['url']} {install_dir}")
            return
    print_ok(f"Cloned to {install_dir}")

def install_github_release(name, cfg):
    """Print instructions for GitHub release download (requires manual step)."""
    print_warn(f"GitHub release download requires manual step:")
    print(f"    1. Go to: {cfg['url']}")
    print(f"    2. Download the Windows binary zip/exe")
    print(f"    3. Extract to: {cfg['install_dir']}")

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print_header("QUAKE LEGACY — Tool Downloader")
    print(f"  Project root: {PROJECT_ROOT}")
    print(f"  Tools dir:    {TOOLS_DIR}")

    # Python packages first
    install_python_packages()

    # Tools
    for name, cfg in TOOLS.items():
        print_header(f"{name}: {cfg['description']}")

        if already_installed(name, cfg):
            print_ok(f"Already installed at {cfg['install_dir']}")
            if "notes" in cfg:
                print_warn(f"Notes: {cfg['notes']}")
            continue

        tool_type = cfg["type"]
        if tool_type == "zip":
            install_zip_tool(name, cfg)
        elif tool_type == "git_clone":
            install_git_clone(name, cfg)
        elif tool_type == "github_release":
            install_github_release(name, cfg)

        if "notes" in cfg:
            print()
            print(f"  NOTES: {cfg['notes']}")

    # Write version manifest
    manifest_path = TOOLS_DIR / "INSTALLED.md"
    with open(manifest_path, "w") as f:
        f.write("# Installed Tools\n\n")
        f.write("| Tool | Description | Location |\n")
        f.write("|---|---|---|\n")
        for name, cfg in TOOLS.items():
            status = "✓" if already_installed(name, cfg) else "⬜"
            f.write(f"| {status} {name} | {cfg['description']} | `{cfg['install_dir'].relative_to(PROJECT_ROOT)}` |\n")

    print_header("Done")
    print(f"  Manifest: {manifest_path}")
    print(f"  Review tools/README.md for manual steps (GitHub releases, Java for Ghidra, etc.)")

if __name__ == "__main__":
    main()
