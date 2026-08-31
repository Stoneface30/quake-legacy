"""Which clips a Part has already spent, so a corpus can be exhausted in episodes.

User direction 2026-08-29:

    "you have 5min baseline using ALL the T1 clips, if too much T1 clips you keep
     them for the following video (same with t2 filler) also keep the clip that
     are not used so we can generate another videos to finish all the rendered
     clip."

A Part holds ~102 clips (T1 43 / T2 47 / T3 12) and a 5-minute reel spends ~35 of
them, so a Part is roughly three episodes. The ledger records the clips each
episode consumed; the next episode skips them and picks up where the last left
off. Nothing is discarded -- an unused clip stays available until it ships.

The ledger is keyed by the clip's path relative to the corpus root, so it stays
valid if the repo moves.

    from creative_suite.engine import highlight_ledger as L
    used = L.load_used(part=4)                 # clips already shipped
    L.mark_used(part=4, clips=[...], episode=2)
    L.remaining(part=4, frags)                 # what is still unspent
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

LEDGER_DIRNAME = "_hl_ledger"


def ledger_path(part: int, root: Path | None = None) -> Path:
    from creative_suite.engine.config import REPO_ROOT

    base = Path(root) if root else (Path(REPO_ROOT) / "output")
    return base / LEDGER_DIRNAME / f"part{part:02d}.json"


def _key(clip: Path) -> str:
    """Stable identity for a clip: the last two path components.

    Full paths would break if the corpus moves; a bare filename would collide
    across Parts. `Demo (152)  - 84/Demo (152FL1).avi` is unique and portable.
    """
    clip = Path(clip)
    return f"{clip.parent.name}/{clip.name}"


def _read(part: int, root: Path | None = None) -> dict[str, Any]:
    p = ledger_path(part, root)
    if not p.exists():
        return {"part": part, "episodes": []}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        # A corrupt ledger must not silently erase history.
        raise RuntimeError(f"ledger unreadable, refusing to overwrite: {p}")


def load_used(part: int, root: Path | None = None) -> set[str]:
    """Keys of every clip already spent on a shipped episode of this Part."""
    data = _read(part, root)
    used: set[str] = set()
    for ep in data.get("episodes", []):
        used.update(ep.get("clips", []))
    return used


def episode_count(part: int, root: Path | None = None) -> int:
    return len(_read(part, root).get("episodes", []))


def next_episode(part: int, root: Path | None = None) -> int:
    return episode_count(part, root) + 1


def mark_used(part: int, clips: Iterable[Path | str], episode: int | None = None,
              output: str | None = None, root: Path | None = None) -> int:
    """Record an episode's clips. Returns the episode number written.

    Call this only AFTER the render succeeds -- a failed render must not burn
    clips.
    """
    data = _read(part, root)
    keys = sorted({_key(Path(c)) for c in clips})
    ep = episode if episode is not None else len(data["episodes"]) + 1
    # Replacing an episode (a re-render) rather than appending a duplicate.
    data["episodes"] = [e for e in data["episodes"] if e.get("episode") != ep]
    data["episodes"].append({"episode": ep, "output": output, "clips": keys})
    data["episodes"].sort(key=lambda e: e.get("episode", 0))

    p = ledger_path(part, root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return ep


def remaining(part: int, frags: Sequence[Any], root: Path | None = None) -> list:
    """Subset of `frags` whose POV clip has not shipped yet."""
    used = load_used(part, root)
    return [f for f in frags if _key(Path(f.fp)) not in used]


def reset(part: int, root: Path | None = None) -> None:
    p = ledger_path(part, root)
    if p.exists():
        p.unlink()


MUSIC_REGISTRY = "music_used.json"


def _music_registry_path(root: Path | None = None) -> Path:
    from creative_suite.engine.config import REPO_ROOT

    base = Path(root) if root else (Path(REPO_ROOT) / "output")
    return base / LEDGER_DIRNAME / MUSIC_REGISTRY


def song_id(path: Path) -> str:
    """Content hash. Two slots can hold the SAME song under different names --
    measured: 4 such pairs across the 46 slot files. Filenames are not identity.
    """
    import hashlib

    return hashlib.md5(Path(path).read_bytes()).hexdigest()[:16]


def used_songs(root: Path | None = None) -> dict[str, str]:
    p = _music_registry_path(root)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def claim_song(path: Path, label: str, root: Path | None = None) -> None:
    """Mark a song as spent so no other video reuses it."""
    reg = used_songs(root)
    reg[song_id(path)] = f"{label}:{Path(path).name}"
    p = _music_registry_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(reg, indent=2), encoding="utf-8")


def pick_unused_song(candidates: Sequence[Path],
                     root: Path | None = None) -> Path | None:
    """First candidate whose CONTENT has not been used by another video."""
    spent = set(used_songs(root))
    for c in candidates:
        try:
            if song_id(c) not in spent:
                return Path(c)
        except OSError:
            continue
    return None


UNUSED_DIRNAME = "_hl_unused"


def unused_dir(part: int, root: Path | None = None) -> Path:
    from creative_suite.engine.config import REPO_ROOT

    base = Path(root) if root else (Path(REPO_ROOT) / "output")
    return base / UNUSED_DIRNAME / f"Part{part}"


def stage_unused(part: int, frags: Sequence[Any], used_clips: Iterable[Path | str],
                 root: Path | None = None) -> tuple[int, Path]:
    """Collect every clip this episode did NOT use into a dedicated folder.

    User direction 2026-08-29: "put all the non used clip in a dedicated folder
    we will do them LATER not now."

    Clips are HARD-LINKED, not copied: the corpus is ~50-100 MB per AVI and a
    Part leaves ~65 unused, so copying would cost several GB per Part for files
    that already exist. A hard link is a real file at a real path, costs no
    extra space on the same volume, and deleting the staged copy never touches
    the original. Falls back to a copy across volumes.

    Angle clips follow their POV so a staged frag stays whole.
    Returns (count, folder).
    """
    import shutil

    used = {_key(Path(c)) for c in used_clips}
    out = unused_dir(part, root)
    out.mkdir(parents=True, exist_ok=True)

    staged = 0
    manifest: list[str] = []
    for f in frags:
        if _key(Path(f.fp)) in used:
            continue
        group = [Path(f.fp)] + [Path(x) for x in getattr(f, "fls", [])]
        # Preserve the folder-per-frag layout that pairs angles to their POV.
        dest_dir = out / Path(f.fp).parent.name if len(group) > 1 else out
        dest_dir.mkdir(parents=True, exist_ok=True)
        for src in group:
            dst = dest_dir / src.name
            if dst.exists():
                continue
            try:
                import os

                os.link(src, dst)
            except OSError:
                try:
                    shutil.copy2(src, dst)
                except OSError:
                    continue
            staged += 1
            manifest.append(str(src))

    (out / "MANIFEST.txt").write_text(
        f"# Part {part} — clips not used by the shipped episode(s)\n"
        f"# {staged} file(s). Hard-linked from the corpus: deleting anything\n"
        f"# here does NOT touch the original in QUAKE VIDEO/.\n\n"
        + "\n".join(sorted(manifest)) + "\n",
        encoding="utf-8")
    return staged, out


@dataclass
class Coverage:
    total: int
    used: int
    left: int
    episodes: int

    @property
    def pct(self) -> float:
        return (self.used / self.total * 100.0) if self.total else 0.0


def coverage(part: int, frags: Sequence[Any], root: Path | None = None) -> Coverage:
    used = load_used(part, root)
    hit = sum(1 for f in frags if _key(Path(f.fp)) in used)
    return Coverage(total=len(frags), used=hit, left=len(frags) - hit,
                    episodes=episode_count(part, root))
