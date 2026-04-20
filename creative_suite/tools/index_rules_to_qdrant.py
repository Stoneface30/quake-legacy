"""Index Quake Legacy rules/learnings corpus into Qdrant collection `quake_legacy_rules`.

Sources:
  1. G:/QUAKE_LEGACY/CLAUDE.md                          -> one point per `### Rule ...` section
  2. ~/.claude/Vault/learnings.md                        -> one point per **L<N>: ...** entry
  3. ~/.claude/projects/G--QUAKE-LEGACY/memory/*.md      -> one point per `##` section
  4. G:/QUAKE_LEGACY/docs/research/*.md                  -> one point per H2 section

Embeddings: Ollama nomic-embed-text. Vector DB: Qdrant (http://localhost:6333).
Stdlib + requests only. Idempotent (uuid5 point IDs).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import requests

QDRANT_URL = "http://localhost:6333"
OLLAMA_URL = "http://localhost:11434"
EMBED_MODEL = "nomic-embed-text"
COLLECTION = "quake_legacy_rules"

NAMESPACE = uuid.UUID("6d9a5c1c-2b1e-4e2a-8e77-000000000001")

HOME = Path(os.path.expanduser("~"))
CLAUDE_MD = Path("G:/QUAKE_LEGACY/CLAUDE.md")
LEARNINGS_MD = HOME / ".claude" / "Vault" / "learnings.md"
MEMORY_DIR = HOME / ".claude" / "projects" / "G--QUAKE-LEGACY" / "memory"
RESEARCH_DIR = Path("G:/QUAKE_LEGACY/docs/research")


@dataclass
class Chunk:
    point_id: str
    text: str
    payload: dict[str, object] = field(default_factory=dict)


# ---------- chunkers ----------

RULE_HEADER_RE = re.compile(
    r"^###\s+Rule\s+(?P<rid>[A-Z0-9]+-[A-Z0-9]+)(?:\s+(?P<ver>v\d+))?\s*(?P<rest>.*)$"
)


def _rule_category(rule_id: str) -> str:
    prefix = rule_id.split("-", 1)[0]
    return {
        "P1": "phase1",
        "P3": "phase3",
        "ENG": "engine",
        "VIS": "visual",
        "FT": "funded_track",
    }.get(prefix, "misc")


def chunk_claude_md(path: Path) -> list[Chunk]:
    """Split CLAUDE.md by `### Rule X-Y` headings. Each rule = one chunk."""
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    chunks: list[Chunk] = []
    cur: list[str] = []
    cur_rule: str | None = None
    cur_ver: str | None = None
    cur_rest: str = ""

    def flush() -> None:
        nonlocal cur, cur_rule, cur_ver, cur_rest
        if cur_rule and cur:
            body = "\n".join(cur).strip()
            if body:
                superseded = "SUPERSEDED" in cur_rest.upper() or "SUPERSEDED" in body.upper()[:400]
                section_id = f"rule:{cur_rule}:{cur_ver or 'v0'}"
                pid = str(uuid.uuid5(NAMESPACE, f"{path}|{section_id}"))
                chunks.append(
                    Chunk(
                        point_id=pid,
                        text=body,
                        payload={
                            "source_file": str(path),
                            "source_type": "claude_md_rule",
                            "rule_id": cur_rule,
                            "version": cur_ver or "v1",
                            "category": _rule_category(cur_rule),
                            "superseded": superseded,
                            "title": cur_rest.strip(),
                            "section_id": section_id,
                        },
                    )
                )
        cur = []

    for line in lines:
        m = RULE_HEADER_RE.match(line)
        if m:
            flush()
            cur_rule = m.group("rid")
            cur_ver = m.group("ver")
            cur_rest = m.group("rest") or ""
            cur = [line]
        elif cur_rule is not None:
            # stop if next non-rule top-level section begins (## heading, not ###)
            if line.startswith("## ") and not line.startswith("### "):
                flush()
                cur_rule = None
                cur_ver = None
                cur_rest = ""
            else:
                cur.append(line)
    flush()
    return chunks


L_ENTRY_RE = re.compile(r"^\*\*L(?P<num>\d+):\s*(?P<title>[^*]+?)\*\*\s*$")
DATE_HEADER_RE = re.compile(r"^#{2,3}\s+(?P<date>\d{4}-\d{2}-\d{2})")


def chunk_learnings(path: Path) -> list[Chunk]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    chunks: list[Chunk] = []
    cur: list[str] = []
    cur_num: str | None = None
    cur_title: str = ""
    cur_date: str = ""
    running_date: str = ""

    def flush() -> None:
        nonlocal cur, cur_num, cur_title, cur_date
        if cur_num and cur:
            body = "\n".join(cur).strip()
            if body:
                # Extract category if present (e.g. "Category: `ARCHITECTURE`")
                cat_match = re.search(r"Category:\s*`([A-Z_]+)`", body)
                category = cat_match.group(1) if cat_match else "UNCATEGORIZED"
                section_id = f"L{cur_num}"
                pid = str(uuid.uuid5(NAMESPACE, f"{path}|{section_id}"))
                chunks.append(
                    Chunk(
                        point_id=pid,
                        text=body,
                        payload={
                            "source_file": str(path),
                            "source_type": "learning",
                            "lesson_id": f"L{cur_num}",
                            "title": cur_title.strip(),
                            "date": cur_date or running_date,
                            "category": category,
                            "section_id": section_id,
                        },
                    )
                )
        cur = []

    for line in lines:
        dm = DATE_HEADER_RE.match(line)
        if dm:
            running_date = dm.group("date")
        m = L_ENTRY_RE.match(line)
        if m:
            flush()
            cur_num = m.group("num")
            cur_title = m.group("title")
            cur_date = running_date
            cur = [line]
        elif cur_num is not None:
            # a new L-entry or a new date heading ends the chunk
            if L_ENTRY_RE.match(line):
                flush()
                cur_num = None
            else:
                cur.append(line)
    flush()
    return chunks


H2_RE = re.compile(r"^##\s+(?P<title>.+?)\s*$")


def chunk_h2(path: Path, source_type: str) -> list[Chunk]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    chunks: list[Chunk] = []
    cur: list[str] = []
    cur_title: str | None = None

    def flush() -> None:
        nonlocal cur, cur_title
        if cur_title is not None and cur:
            body = "\n".join(cur).strip()
            if body:
                section_id = cur_title[:80]
                pid = str(uuid.uuid5(NAMESPACE, f"{path}|{section_id}"))
                chunks.append(
                    Chunk(
                        point_id=pid,
                        text=body,
                        payload={
                            "source_file": str(path),
                            "source_type": source_type,
                            "file": path.name,
                            "section": cur_title,
                            "section_id": section_id,
                        },
                    )
                )
        cur = []

    # optionally include preamble (before first H2) as one chunk
    preamble: list[str] = []
    saw_h2 = False
    for line in lines:
        m = H2_RE.match(line)
        if m:
            if not saw_h2 and preamble:
                body = "\n".join(preamble).strip()
                if body:
                    section_id = "_preamble"
                    pid = str(uuid.uuid5(NAMESPACE, f"{path}|{section_id}"))
                    chunks.append(
                        Chunk(
                            point_id=pid,
                            text=body,
                            payload={
                                "source_file": str(path),
                                "source_type": source_type,
                                "file": path.name,
                                "section": "(preamble)",
                                "section_id": section_id,
                            },
                        )
                    )
            saw_h2 = True
            flush()
            cur_title = m.group("title")
            cur = [line]
        elif cur_title is None:
            preamble.append(line)
        else:
            cur.append(line)
    flush()
    return chunks


# ---------- qdrant + ollama ----------


MAX_EMBED_CHARS = 8000  # nomic-embed-text context ~8k tokens; char-truncate to be safe


def embed(text: str) -> list[float]:
    payload_text = text[:MAX_EMBED_CHARS]
    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            r = requests.post(
                f"{OLLAMA_URL}/api/embeddings",
                json={"model": EMBED_MODEL, "prompt": payload_text},
                timeout=120,
            )
            r.raise_for_status()
            data = r.json()
            emb = data.get("embedding")
            if not emb:
                raise RuntimeError(f"Ollama returned no embedding: {data}")
            return emb
        except Exception as exc:
            last_exc = exc
            # shrink and retry
            payload_text = payload_text[: max(500, len(payload_text) // 2)]
    raise RuntimeError(f"embed failed after retries: {last_exc}")


def ensure_collection(vector_size: int, force: bool) -> None:
    r = requests.get(f"{QDRANT_URL}/collections/{COLLECTION}", timeout=10)
    exists = r.status_code == 200
    if exists and force:
        requests.delete(f"{QDRANT_URL}/collections/{COLLECTION}", timeout=10)
        exists = False
    if not exists:
        payload = {
            "vectors": {"size": vector_size, "distance": "Cosine"},
        }
        r = requests.put(
            f"{QDRANT_URL}/collections/{COLLECTION}", json=payload, timeout=30
        )
        r.raise_for_status()
        print(f"[qdrant] created collection {COLLECTION} dim={vector_size}")
    else:
        print(f"[qdrant] collection {COLLECTION} already exists (use --force to recreate)")


def upsert_batch(points: list[dict]) -> None:
    if not points:
        return
    r = requests.put(
        f"{QDRANT_URL}/collections/{COLLECTION}/points?wait=true",
        json={"points": points},
        timeout=60,
    )
    r.raise_for_status()


def ping() -> None:
    try:
        r = requests.get(f"{QDRANT_URL}/collections", timeout=5)
        r.raise_for_status()
    except Exception as exc:
        print(f"FATAL: Qdrant not reachable at {QDRANT_URL}: {exc}", file=sys.stderr)
        sys.exit(2)
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        r.raise_for_status()
        names = [m["name"] for m in r.json().get("models", [])]
        if not any(EMBED_MODEL in n for n in names):
            print(
                f"FATAL: Ollama has no {EMBED_MODEL} model. Available: {names}",
                file=sys.stderr,
            )
            sys.exit(2)
    except Exception as exc:
        print(f"FATAL: Ollama not reachable at {OLLAMA_URL}: {exc}", file=sys.stderr)
        sys.exit(2)


# ---------- main ----------


def collect_chunks() -> tuple[list[Chunk], dict[str, int]]:
    buckets: list[tuple[str, Iterable[Chunk]]] = []

    buckets.append(("CLAUDE.md rules", chunk_claude_md(CLAUDE_MD)))
    buckets.append(("learnings.md L-entries", chunk_learnings(LEARNINGS_MD)))

    memory_chunks: list[Chunk] = []
    if MEMORY_DIR.exists():
        for f in sorted(MEMORY_DIR.glob("*.md")):
            memory_chunks.extend(chunk_h2(f, source_type="memory"))
    buckets.append(("memory/*.md H2", memory_chunks))

    research_chunks: list[Chunk] = []
    if RESEARCH_DIR.exists():
        for f in sorted(RESEARCH_DIR.glob("*.md")):
            research_chunks.extend(chunk_h2(f, source_type="research"))
    buckets.append(("docs/research/*.md H2", research_chunks))

    all_chunks: list[Chunk] = []
    counts: dict[str, int] = {}
    for name, chunks_iter in buckets:
        lst = list(chunks_iter)
        counts[name] = len(lst)
        all_chunks.extend(lst)
    return all_chunks, counts


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--force", action="store_true", help="recreate collection")
    p.add_argument("--dry-run", action="store_true", help="chunk but don't embed/upsert")
    args = p.parse_args()

    ping()

    chunks, counts = collect_chunks()
    print("---- chunk counts ----")
    for name, n in counts.items():
        print(f"  {name}: {n}")
    print(f"  TOTAL: {len(chunks)}")

    if args.dry_run:
        return 0

    if not chunks:
        print("no chunks; aborting", file=sys.stderr)
        return 1

    # probe embed dim from first chunk
    first_emb = embed(chunks[0].text)
    dim = len(first_emb)
    print(f"[ollama] embed dim = {dim}")
    ensure_collection(vector_size=dim, force=args.force)

    batch: list[dict] = []
    BATCH = 32
    for i, ch in enumerate(chunks):
        vec = first_emb if i == 0 else embed(ch.text)
        batch.append({"id": ch.point_id, "vector": vec, "payload": ch.payload | {"text": ch.text}})
        if len(batch) >= BATCH:
            upsert_batch(batch)
            print(f"  upserted {i + 1}/{len(chunks)}")
            batch = []
    if batch:
        upsert_batch(batch)
    print(f"[qdrant] upsert complete: {len(chunks)} points in {COLLECTION}")

    r = requests.get(f"{QDRANT_URL}/collections/{COLLECTION}", timeout=10)
    info = r.json().get("result", {})
    print(f"[qdrant] final points_count={info.get('points_count')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
