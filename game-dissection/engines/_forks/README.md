# engines/_forks/

Live, writable source trees we intend to build, patch, and ship.

Unlike `engines/variants/` (thin near-dup reference dirs) and `engines/_canonical/`
(read-only deduped merge), trees under `_forks/` are full upstream checkouts WITH
their own `.git/` directories preserved so we can `git pull` upstream and rebase
our patches on top.

## Current forks

- **`q3mme/`** — Quake 3 Movie Maker's Edition. Promoted here from
  `tools/quake-source/q3mme/` (retired 2026-04-19). This is the base for
  Phase 3.5 Track A: the protocol-73 port (Gate ENG-1 Path A approved per
  `docs/research/gate-eng-1-decision-2026-04-19.md`).
  Upstream: `git remote -v` in this dir. Patches to port: see
  `engines/wolfcam-knowledge/patches/0001..0007`.

## Not in _forks/ (yet)

- quake3e — kept as a reference variant under `variants/quake3e/` — reactivate
  to `_forks/` when we start a dual-protocol fork pass.
