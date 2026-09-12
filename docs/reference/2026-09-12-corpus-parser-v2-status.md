# Corpus status: pre-parser-v2 entity data is STALE (2026-09-12)

**Decision (user, 2026-09-12):** do not reparse yet. Mark the current corpus
stale for entity-derived data, finish gate G1, and only after G1 fully passes
rebuild the corpus **once**, into a new versioned database. Keep the old corpus
for comparison, produce a quantified old-vs-new migration report, and promote
the new corpus only after the downstream mining and highlight regressions pass.
Protocol 91 is a compatibility gate. It does not block a protocol-73-only
rebuild when no real p91 fixture exists.

## What changed

`engine/parser/demo_parse.py` declares `PARSER_VERSION = 2`. Gate G1 proved
that it agrees with the engine's own decoder (`host/pantheon_demo_feed.c`) on
every playerstate and entity field, on the configstring set at every snapshot,
on the command stream and on the gamestate. G1 covered 12.8 M entity fields on
two demos, and a mutation check showed the comparison is not blind. The v1
defects it fixed:

| defect | effect in v1 data |
|---|---|
| delta-reference history recorded before the snapshot's entity deltas | every entity field one frame stale where it changed in the reference; after an uncompressed run, players rebuilt from partial deltas with no eType |
| full frames seeded every gamestate baseline | baseline entities the frame never sent looked present |
| entering entities started from `{}`, not their baseline; empty deltas dropped | missing fields, missing entities |
| fields changed to zero were omitted | stale non-zero values survived (eFlags, event, weapon ...) |
| repeated reliable commands applied again | duplicated chat, print and scoreboard rows |
| `bcs0/1/2` ignored | long configstrings lost |
| `%` kept in strings; high bytes in gamestate strings became `.` | text and names differ from the engine's |
| signed playerstate fields read unsigned | crouch viewheight −8 read as 248 |
| persistant/ammo/powerups discarded | not available |

Obituaries are entity temp-events, so **every frag and every table keyed on
one is entity-derived.** The full map is in
`docs/reference/2026-09-12-corpus-entity-derived-map.md`.

## How staleness is marked (read-only)

`engine/parser/corpus_status.py`:

- **When a database counts as current:** only if it carries a `corpus_build`
  row with `dm73_parser_version >= 2`.
- **The existing corpus:** no database built before 2026-09-12 has that row,
  so every one of them reads as `STALE_PRE_PARSER_V2`. Marking it stale wrote
  nothing into any database. The tool only ever opens a database with
  `mode=ro`.
- **Reporting:** `python -m engine.parser.corpus_status --write` writes
  `CORPUS_STATUS.json` beside the databases, for people and tools.
- **Blocking stale data:** `require_current(db)` raises `StaleCorpus` for code
  that must not consume pre-v2 entity data.
- **Stamping:** `stamp()` is called only on databases a v2 rebuild has just
  created.

## Order from here

1. G1 complete: done (commits `9cb0d2d8`, `0957d29d`).
2. One rebuild into a separate, versioned build root, never over the live
   corpus. See the rebuild plan.
3. Migration report: old vs new, quantified per table.
4. Downstream mining and highlight regressions pass on the new corpus.
5. Promotion, with the user's go. The old corpus is kept.
