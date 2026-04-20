"""Query the Quake Legacy rules Qdrant collection.

Usage:
  python query_rules.py "how loud should the music be"
  python query_rules.py --top 10 "beat match"
"""

from __future__ import annotations

import argparse
import sys

import requests

QDRANT_URL = "http://localhost:6333"
OLLAMA_URL = "http://localhost:11434"
EMBED_MODEL = "nomic-embed-text"
COLLECTION = "quake_legacy_rules"


def embed(text: str) -> list[float]:
    r = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=60,
    )
    r.raise_for_status()
    emb = r.json().get("embedding")
    if not emb:
        raise RuntimeError("Ollama returned no embedding")
    return emb


def search(query: str, top: int) -> list[dict]:
    vec = embed(query)
    r = requests.post(
        f"{QDRANT_URL}/collections/{COLLECTION}/points/search",
        json={"vector": vec, "limit": top, "with_payload": True},
        timeout=30,
    )
    r.raise_for_status()
    return r.json().get("result", [])


def label(payload: dict) -> str:
    st = payload.get("source_type", "?")
    if st == "claude_md_rule":
        return f"{payload.get('rule_id')} {payload.get('version', '')}".strip()
    if st == "learning":
        return payload.get("lesson_id", "L?")
    if st in ("memory", "research"):
        return f"{payload.get('file', '?')}#{payload.get('section', '?')[:40]}"
    return st


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("query", help="natural-language query")
    p.add_argument("--top", type=int, default=5)
    args = p.parse_args()

    hits = search(args.query, args.top)
    if not hits:
        print("no hits")
        return 0

    print(f"\nQuery: {args.query}\n")
    for i, h in enumerate(hits, 1):
        score = h.get("score", 0.0)
        payload = h.get("payload") or {}
        text = payload.get("text", "")
        snippet = text.replace("\n", " ").strip()
        if len(snippet) > 220:
            snippet = snippet[:220] + "..."
        # Strip non-ASCII for console safety (Windows cp1252).
        snippet_ascii = snippet.encode("ascii", "replace").decode("ascii")
        print(f"{i}. [{score:.3f}] {label(payload)}")
        print(f"     src: {payload.get('source_file', '?')}")
        print(f"     {snippet_ascii}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
