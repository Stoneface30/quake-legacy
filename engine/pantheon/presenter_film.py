"""Film DIEGETIC_PRESENTER_PROOF_01 and mux its dialogue.

    python -m engine.pantheon.presenter_film

Build (`presenter_proof`) and film are separate on purpose: authoring is cheap
and repeatable, filming costs five minutes of engine time.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from engine.pantheon.dialogue_mix import build_dialogue_stem, mux
from engine.pantheon.shot import (PassKind, ShotSpec, SourceKind, VisualProfile,
                                  render)

SCENE = "DIEGETIC_PRESENTER_PROOF_01"
SYNTH = Path(".tmp/synthetic")
# The capture seeks SEEK_SETTLE_MS before `start_s`, so the shot cannot open on
# the demo's first snapshot. 0.7s is the earliest legal frame.
START_S, END_S = 0.7, 20.4


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=Path(".tmp/shots"))
    args = ap.parse_args()

    spec = ShotSpec(shot_id="PRES01_beauty",
                    source=(SYNTH / f"{SCENE}.dm_73").resolve(),
                    source_kind=SourceKind.SYNTHETIC,
                    start_s=START_S, end_s=END_S,
                    visual=VisualProfile(name="PRES01_BEAUTY"),
                    passes=(PassKind.BEAUTY,),
                    truth_reference=SYNTH / f"{SCENE}.frametruth.json")
    avi = render(spec, args.out)
    print(f"filmed : {avi}  ({avi.stat().st_size/1e6:.1f} MB)")

    stem = build_dialogue_stem(SYNTH / f"{SCENE}.dialogue.json",
                               args.out / "PRES01_dialogue.wav",
                               shot_start_s=START_S,
                               duration_s=END_S - START_S)
    out = mux(avi, stem, args.out / f"{SCENE}.mp4")
    print(f"delivered: {out}  ({out.stat().st_size/1e6:.1f} MB)")
    return 0


if __name__ == "__main__":                     # pragma: no cover - CLI
    raise SystemExit(main())
