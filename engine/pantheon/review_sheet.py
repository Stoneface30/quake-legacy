"""WHEN THE ANSWER IS A HUMAN'S, PUT IT IN FRONT OF THEM.

Three times in one day a measurement said nothing and one look settled it:

  * a HUD element measured +0.002 against a whole-frame -0.002 and was
    declared absent; cropped and stacked, the health readout is plainly there
    in one frame and plainly gone in the other.
  * a capture was called truncated on a frame count; its first and last frames
    showed the start and the end of the window, so it was complete.
  * two look packs were compared by saturation ratio, which turned out to be
    measuring camera phase.

Every one of those was a small subject inside a large frame, where a statistic
over the region is dominated by everything that is not the subject. The lesson
is not "measure better". It is that some questions are a person's to answer,
and the job of the engine is to make answering them cheap.

WHAT THIS PRODUCES. One labelled image per question, at a size a person can
judge, with the legs side by side and the variable named. Nothing here decides
anything: the sheet is evidence, and the verdict lives in `visual_proof` where
a human puts it.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from engine.pantheon import store as S

FFMPEG = S.PROJECT_ROOT / "creative_suite" / "tools" / "ffmpeg" / "ffmpeg.exe"
VISUAL_RECORD = S.PROJECT_ROOT / "docs" / "visual-record"

#: A crop wide enough to hold context but tight enough that the subject is not
#: a rounding error. Callers who know where the subject is should say so.
FULL_FRAME = None


@dataclass(frozen=True)
class Leg:
    """One side of a comparison: an image and what made it different."""
    image: Path
    label: str

    def exists(self) -> bool:
        return Path(self.image).is_file()


@dataclass(frozen=True)
class Sheet:
    """A question for a person, and the frames that answer it."""
    name: str
    question: str                 # what the viewer is being asked to decide
    variable: str                 # the ONE thing that differs between legs
    legs: tuple[Leg, ...]
    crop: tuple[int, int, int, int] | None = FULL_FRAME   # w,h,x,y
    stack: str = "auto"           # auto | h | v
    note: str = ""

    def __post_init__(self) -> None:
        if len(self.legs) < 2:
            raise ValueError("a comparison needs at least two legs")
        if self.stack not in ("auto", "h", "v"):
            raise ValueError(f"unknown stack: {self.stack}")

    @property
    def direction(self) -> str:
        """Wide crops stack vertically, tall ones side by side, so the two
        legs stay comparable rather than one becoming a stripe."""
        if self.stack != "auto":
            return self.stack
        if self.crop is None:
            return "v"
        w, h = self.crop[0], self.crop[1]
        return "v" if w > h * 1.6 else "h"


def _escape(text: str) -> str:
    """Make a label survive ffmpeg's filter parser.

    The text sits inside `text='...'`, so a literal apostrophe cannot simply be
    backslashed: the quote has to be closed, the character emitted, and the
    quote reopened. Colons separate filter options, backslashes escape, and
    percent introduces an expansion -- all of which appear in cvar names, paths
    and percentages, which is exactly what these labels are made of.
    """
    t = text.replace("\\", "\\\\")
    t = t.replace(":", r"\:").replace("%", r"\%")
    return t.replace("'", "'\\''")


def build(sheet: Sheet, dest: Path, *, width: int = 780) -> dict:
    """Render one comparison image. Returns what it made and what is missing.

    A missing leg is reported rather than silently dropped: a sheet with one
    side is not a comparison, and quietly showing it invites a verdict on
    nothing.
    """
    missing = [l.label for l in sheet.legs if not l.exists()]
    if missing:
        return {"ok": False, "sheet": sheet.name, "missing": missing,
                "why": "a comparison with a missing leg is not a comparison"}

    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)

    ins: list[str] = []
    for leg in sheet.legs:
        ins += ["-i", str(leg.image)]

    chains, labels = [], []
    for i, leg in enumerate(sheet.legs):
        crop = (f"crop={sheet.crop[0]}:{sheet.crop[1]}:"
                f"{sheet.crop[2]}:{sheet.crop[3]}," if sheet.crop else "")
        # The label is burned in, because a comparison whose legs are only
        # distinguished by filename gets mixed up the moment it is shared.
        chains.append(
            f"[{i}:v]{crop}scale={width}:-2,"
            f"drawtext=text='{_escape(leg.label)}':fontcolor=yellow:"
            f"fontsize=22:box=1:boxcolor=black@0.55:boxborderw=6:x=10:y=10"
            f"[v{i}]")
        labels.append(f"[v{i}]")

    join = "hstack" if sheet.direction == "h" else "vstack"
    graph = (";".join(chains) + ";" + "".join(labels)
             + f"{join}=inputs={len(sheet.legs)}[out]")

    r = subprocess.run(
        [str(FFMPEG), "-v", "error", "-y", *ins, "-filter_complex", graph,
         "-map", "[out]", "-frames:v", "1", str(dest)],
        capture_output=True, timeout=600)
    if r.returncode != 0 or not dest.exists():
        return {"ok": False, "sheet": sheet.name,
                "why": r.stderr.decode("utf-8", "replace").strip()[:300]}

    return {
        "ok": True, "sheet": sheet.name, "path": str(dest),
        "bytes": dest.stat().st_size,
        "question": sheet.question, "variable": sheet.variable,
        "legs": [l.label for l in sheet.legs],
        "note": sheet.note,
        # Said out loud, because a sheet is the thing people mistake for a
        # verdict.
        "verdict": "PENDING_HUMAN",
        "how_to_answer": "look at it and record the verdict in visual_proof",
    }


def for_today(name: str) -> Path:
    """Where a sheet belongs, under the project's visual-record convention."""
    from datetime import date
    return VISUAL_RECORD / date.today().isoformat() / f"{name}.png"


# ── the crops that keep coming up ──────────────────────────────────────────
#
# Each is a region where a subject small enough to be lost in a whole-frame
# statistic actually lives. Named so a caller does not re-derive them, and
# because the wrong crop is how a comparison ends up showing nothing.

CROPS: dict[str, tuple[int, int, int, int]] = {
    # w, h, x, y  -- against a 1920x1080 frame
    "HUD_BOTTOM_LEFT": (820, 260, 40, 800),    # health, armour, ammo
    "HUD_BOTTOM_RIGHT": (820, 260, 1060, 800),
    "HUD_TOP": (1920, 200, 0, 0),              # medals, item pickups, warmup
    "CENTRE": (900, 600, 510, 240),            # crosshair, the actor
    "FULL": (1920, 1080, 0, 0),
}


def compare(name: str, question: str, variable: str,
            legs: dict[str, Path], *, crop: str | None = None,
            note: str = "", dest: Path | None = None) -> dict:
    """The short form: name the question, the variable, and the legs.

        compare("hud_status", "Is the health readout drawn?",
                "cg_drawStatus", {"on": a, "off": b}, crop="HUD_BOTTOM_LEFT")
    """
    box = CROPS.get(crop) if crop else None
    if crop and box is None:
        raise KeyError(f"no such crop: {crop}; known: {sorted(CROPS)}")
    sheet = Sheet(name=name, question=question, variable=variable,
                  legs=tuple(Leg(Path(p), lab) for lab, p in legs.items()),
                  crop=box, note=note)
    return build(sheet, dest or for_today(name))
