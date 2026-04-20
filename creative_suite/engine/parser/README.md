# dm73 Parser — Funded Track FT-1

C++17 static library + CLI tool that parses Quake Live `.dm_73` demo files
and emits frag events as JSON Lines.

## Status

**FT-1: SCAFFOLD** — directory structure, headers, CMake, and CLI are in place.
`read_frags()` and `read_header()` are stubs that return failure with a clear
error message. The build compiles only once the vendor `.c` files are populated
(see below).

## Directory Layout

```
parser/
  CMakeLists.txt          cmake project (C++17, static lib + CLI)
  include/dm73/reader.h   public API: Dm73Reader, FragEvent, DemoHeader, MOD_* enum
  src/
    dm73_reader.cpp        Dm73Reader implementation (scaffold stubs)
    frag_extractor.cpp     extract_frags_jsonl() convenience wrapper
    main.cpp               dm73dump CLI (--header mode + default frag stream)
  vendor/                  GPL-2.0 wolfcamql / Q3A sources (copy before build)
    msg.c  huffman.c  common.c  q_shared.h  bg_public.h
  tests/                   Python pytest fixtures (see creative_suite/tests/)
```

## Build

### Prerequisites

- CMake >= 3.20
- C++17 compiler (MSVC 2022, GCC 12+, or Clang 15+)
- Vendor sources populated (see below)

### Populate vendor sources

```bash
CANONICAL=G:/QUAKE_LEGACY/engine/engines/_canonical/code
cp $CANONICAL/qcommon/msg.c      vendor/msg.c
cp $CANONICAL/qcommon/huffman.c  vendor/huffman.c
cp $CANONICAL/qcommon/common.c   vendor/common.c
cp $CANONICAL/qcommon/q_shared.h vendor/q_shared.h
cp $CANONICAL/game/bg_public.h   vendor/bg_public.h
```

> **Note:** `common.c` pulls in substantial engine machinery. At FT-1 alpha,
> consider replacing it with a minimal shim that provides only the symbols
> `msg.c` and `huffman.c` actually import (`Com_Printf`, `Com_Error`,
> `Com_Memset`, `Com_Memcpy`). This avoids linker conflicts with the C++ stdlib.

### Configure and build

```bash
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build
```

### Install

```bash
cmake --install build --prefix /usr/local
```

## Usage

```bash
# Stream frag events as JSON Lines to stdout
dm73dump /path/to/demo.dm_73

# Dump demo header as JSON
dm73dump --header /path/to/demo.dm_73
```

### JSON Lines output schema

```json
{"server_time_ms": 532100, "killer": 3, "victim": 7, "weapon": 6, "headshot": false, "telefrag": false}
```

| Field | Type | Description |
|---|---|---|
| `server_time_ms` | int | Snapshot server_time in milliseconds |
| `killer` | int 0-63 | Client slot (`otherEntityNum2`) |
| `victim` | int 0-63 | Client slot (`otherEntityNum`) |
| `weapon` | int | `MeansOfDeath` value (see `include/dm73/reader.h`) |
| `headshot` | bool | `weapon == MOD_RAILGUN_HEADSHOT` |
| `telefrag` | bool | `weapon == MOD_TELEFRAG` |

## Format Reference

Full `.dm_73` format documentation:
`G:/QUAKE_LEGACY/docs/reference/dm73-format-deep-dive.md` (1,337 lines)

Key sections for FT-1 alpha implementation:
- §0 TL;DR cheat sheet (frame structure)
- §2 Gamestate (svc_gamestate — for read_header)
- §4 Snapshot (svc_snapshot — for frag event scanning)
- §5 Entity events (EV_OBITUARY detection pattern)

## Frag Detection Pattern

```c
// Inside svc_snapshot entity loop:
if ((entity.event & ~0x300) == EV_OBITUARY) {
    frag.killer_client = entity.otherEntityNum2;  // client slot 0-63
    frag.victim_client = entity.otherEntityNum;
    frag.weapon        = entity.eventParm;        // MeansOfDeath value
    frag.server_time_ms = snapshot.server_time;
}
```

## Tests

```bash
cd G:/QUAKE_LEGACY
python -m pytest creative_suite/tests/test_dm73_scaffold.py -v
```

## License

`src/` and `include/` are MIT (QUAKE LEGACY project).
`vendor/` files are GPL-2.0 (Id Software / wolfcam contributors) — headers preserved.
