# Steam Asset Sources — Proof of Presence

**Captured:** 2026-04-17
**Rule:** ENG-1 — Steam paks are the authoritative source of truth for baseq3 assets. Wolfcam extracts are reference only.
**Access:** READ-ONLY. Never modify these files.

---

## Quake Live

**Path:** `C:\Program Files (x86)\Steam\steamapps\common\Quake Live\baseq3\`

| File | Size (bytes) | Size (MiB) | Purpose |
|---|---:|---:|---|
| `pak00.pk3` | 962,052,238 | 917 | Authoritative QL assets (2023-05-05 build) |
| `bin.pk3` | 1,381,099 | 1.3 | QL engine binaries |

Also in folder: `access.txt`, `mappool_*.txt` (CA, CTF, duel, FFA, race, TDM), `server.cfg`, `workshop.txt`.

---

## Quake 3 Arena

**Path:** `C:\Program Files (x86)\Steam\steamapps\common\Quake 3 Arena\baseq3\`

| File | Size (bytes) | Size (MiB) | Purpose |
|---|---:|---:|---|
| `pak0.pk3` | 479,493,658 | 457 | Original id release, main assets |
| `pak1.pk3` | 374,405 | 0.4 | v1.17 patch |
| `pak2.pk3` | 7,511,182 | 7.2 | v1.27 patch |
| `pak3.pk3` | 276,305 | 0.3 | v1.29 patch |
| `pak4.pk3` | 9,600,350 | 9.2 | v1.30 patch |
| `pak5.pk3` | 191,872 | 0.2 | v1.31 patch |
| `pak6.pk3` | 7,346,884 | 7.0 | v1.32 patch |
| `pak7.pk3` | 320,873 | 0.3 | point release |
| `pak8.pk3` | 454,478 | 0.4 | point release |

Also in folder: `q3config.cfg` (user's persisted config), `steam_autocloud.vdf`.

---

## Combined

- **QL pak00.pk3 alone:** 917 MiB
- **Q3A pak0-8 combined:** 481 MiB
- **Grand total:** **1,398 MiB** of authoritative Quake engine assets on disk

Plus the Q3 engine source at `tools/quake-source/quake3-source/` (id's GPL release), q3mme source (movie maker's edition), quake3e, ioquake3, and wolfcamql sources — everything we need to build our own pipeline end to end, no black boxes.

---

## Why This Matters

Wolfcam's `wolfcam-ql/baseq3/` dump is a SUBSET of `pak00.pk3`. Any inventory, style-pack override, or pk3-build pipeline that sources from wolfcam extracts is reading yesterday's cache. The command center inventories directly from these Steam paths.
