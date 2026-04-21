"""One-shot helper: normalize Part 5 clips and build v6 body chunks.
Runs CPU-bound libx264 CRF 20 fast encodes, which can execute in parallel
with another Part's GPU NVENC final render.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from creative_suite.engine.config import Config
from creative_suite.engine.render_part_v6 import normalize_and_expand, build_body_chunks

ROOT = Path("G:/QUAKE_LEGACY")

def main():
    part = 5
    cfg = Config()
    clip_list = cfg.clip_lists_dir / f"part{part:02d}_styleb.txt"
    print(f"Normalizing + expanding {clip_list.name}")
    normalized = normalize_and_expand(part, clip_list, cfg)
    print(f"  {len(normalized)} segments")
    chunks_dir = ROOT / "output" / f"_part{part:02d}_v6_body_chunks"
    print(f"Building chunks -> {chunks_dir}")
    concat, chunks = build_body_chunks(part, normalized, chunks_dir, cfg)
    print(f"[DONE] {len(chunks)} chunks, concat = {concat}")

if __name__ == "__main__":
    main()
