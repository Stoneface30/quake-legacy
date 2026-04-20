"""Pre-flight check that every segment in partNN_styleb.txt resolves to a real
file on one of the three tier trees, and report the tier distribution."""
from pathlib import Path
from phase1.config import Config
from phase1.clip_list import parse_clip_entry
from phase1.experiment import resolve_clip_path


def audit(part: int, cfg: Config) -> None:
    path = cfg.clip_lists_dir / f"part{part:02d}_styleb.txt"
    if not path.exists():
        print(f"Part {part}: MISSING {path.name}")
        return
    lines = path.read_text(encoding="utf-8").splitlines()
    entries = [
        parse_clip_entry(l) for l in lines
        if l.strip() and not l.strip().startswith("#")
    ]
    total_segs = 0
    missing: list[str] = []
    tiers = {"T1": 0, "T2": 0, "T3": 0, "?": 0}
    multi_angle = 0
    for e in entries:
        if len(e.segments) > 1:
            multi_angle += 1
        for seg in e.segments:
            total_segs += 1
            src = resolve_clip_path(seg, part, cfg)
            if src is None:
                missing.append(seg)
                continue
            s = str(src).replace("\\", "/").upper()
            if "/T1/" in s:
                tiers["T1"] += 1
            elif "/T2/" in s:
                tiers["T2"] += 1
            elif "/T3/" in s:
                tiers["T3"] += 1
            else:
                tiers["?"] += 1
    print(
        f"Part {part}: {len(entries)} entries ({multi_angle} multi-angle), "
        f"{total_segs} segments, tiers={tiers}, missing={len(missing)}"
    )
    for m in missing[:10]:
        print(f"   MISSING: {m}")


def main() -> None:
    cfg = Config()
    for part in (4, 5, 6, 7):
        audit(part, cfg)


if __name__ == "__main__":
    main()
