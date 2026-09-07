"""Inventory the playable Quake Live roster from the installed paks.

The Hall of Characters needs every playable character, not a favourite six,
and "playable" has to mean something checkable: three body parts and an
animation.cfg, because that is what cgame requires to assemble a player.

    python scripts/roster_inventory.py [--pak <path>] [--out docs/pantheon_world/roster.json]

Separates the three things the brief asks to keep apart:

  UNIQUE CHARACTER  a models/players/<name> directory that is assemblable
  MODEL VARIANT     lower_1 / lower_2 etc. are Q3 LOD levels, not variants
  SKIN VARIANT      <part>_<skin>.skin -- the skin exists only if all three
                    parts declare it, since a player wears one skin name
"""
from __future__ import annotations

import argparse
import collections
import json
import zipfile
from pathlib import Path

DEFAULT_PAK = Path("C:/Program Files (x86)/Steam/steamapps/common/Quake Live/baseq3")
PARTS = ("lower", "upper", "head")


def inventory(pak_dir: Path) -> dict:
    files: dict[str, set[str]] = collections.defaultdict(set)
    paks = sorted(pak_dir.glob("*.pk3"))
    for pak in paks:
        with zipfile.ZipFile(pak) as z:
            for n in z.namelist():
                p = n.split("/")
                if len(p) >= 4 and p[0] == "models" and p[1] == "players" and p[3]:
                    files[p[2]].add("/".join(p[3:]))

    roster, rejected = [], []
    for name in sorted(files):
        f = files[name]
        if not all(f"{part}.md3" in f for part in PARTS) or "animation.cfg" not in f:
            rejected.append({"name": name, "why": "not assemblable as a player"})
            continue
        # a skin is usable only when every part declares it
        per_part = {part: {s[len(part) + 1:-5] for s in f
                           if s.startswith(part + "_") and s.endswith(".skin")}
                    for part in PARTS}
        skins = sorted(set.intersection(*per_part.values()))
        lods = sorted(s for s in f if s.startswith("lower_") and s.endswith(".md3"))
        roster.append({"name": name, "skins": skins,
                       "lod_levels": len(lods),
                       "parts": {p: f"models/players/{name}/{p}.md3" for p in PARTS},
                       "animation_cfg": f"models/players/{name}/animation.cfg"})
    return {"source_paks": [p.name for p in paks],
            "unique_characters": len(roster),
            "skin_variants_total": sum(len(r["skins"]) for r in roster),
            "roster": roster, "rejected": rejected}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pak", type=Path, default=DEFAULT_PAK)
    ap.add_argument("--out", type=Path, default=Path("docs/pantheon_world/roster.json"))
    a = ap.parse_args()
    data = inventory(a.pak)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(data, indent=1), encoding="utf-8")
    print(f"{data['unique_characters']} playable characters, "
          f"{data['skin_variants_total']} usable skins -> {a.out}")
    for r in data["roster"]:
        print(f"  {r['name']:10s} {len(r['skins'])} skins: {', '.join(r['skins'])}")
    return 0


if __name__ == "__main__":                      # pragma: no cover - CLI
    raise SystemExit(main())
