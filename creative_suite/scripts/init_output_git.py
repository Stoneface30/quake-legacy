# scripts/init_output_git.py
"""Initialize the private git sub-repo at output/ for flow-plan history.

Safe to re-run — skips if already initialized.
"""
from __future__ import annotations

import subprocess
from pathlib import Path


def main() -> None:
    out = Path(__file__).resolve().parents[1] / "output"
    out.mkdir(exist_ok=True)
    if (out / ".git").exists():
        print(f"[init-output-git] {out}/.git already exists — skipping")
        return
    subprocess.run(["git", "init", "-q", str(out)], check=True)
    subprocess.run(["git", "-C", str(out), "config", "user.email", "cinema@local"], check=True)
    subprocess.run(["git", "-C", str(out), "config", "user.name", "Cinema Suite"], check=True)
    (out / ".gitignore").write_text(
        "*.mp4\n*.avi\n*.wav\n*.mp3\n_*\n!*_flow_plan.json\n", encoding="utf-8"
    )
    subprocess.run(["git", "-C", str(out), "add", ".gitignore"], check=True)
    subprocess.run(["git", "-C", str(out), "commit", "-q", "-m", "init: cinema suite flow-plan history"], check=True)
    print(f"[init-output-git] initialized {out}/.git")


if __name__ == "__main__":
    main()
