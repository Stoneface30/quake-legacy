# PANTHEON Production Capture Implementation Plan (revision 4)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `pantheon_cgame.exe` the engine that renders production demo clips, behind a switch, replacing `wolfcamql.exe` only after four measured gates pass and the user signs off.

**The milestone:** one normal mining command whose logs prove, end to end, *demo → our parser → our cgame → our renderer → our FBO → our frames*, with wolfcam nowhere in the production path.

**Architecture:** The host gains a demo reader (`pantheon_demo_feed.c`) that decodes `.dm_73` with the engine's *own* `msg.c`/`huffman.c` — the exact decoder that produces cgame's snapshots inside wolfcam — keeps the gamestate current as `cs` commands arrive, and pushes recorded snapshots and server commands through the existing feed seam (`pantheon_cg_feed.c`). A Python backend (`engine/pantheon/pantheon_capture.py`) matches `capture_demo`'s return contract; `wolfcam_capture.capture_demo` dispatches on `PANTHEON_CAPTURE_BACKEND` (default `wolfcam`). Audio is produced from cgame's own sound calls, logged by the host and mixed offline. Wolfcam stays as the oracle (HL-2).

**Tech Stack:** C (MinGW i686, `gcc -m32`, WolfcamQL 11.3 sources), Python 3 (`E:/PersonalAI/venv`), pytest, ffmpeg (`store.PROJECT_ROOT/creative_suite/tools/ffmpeg/ffmpeg.exe`).

---

## Revision 2 — what an independent review changed (2026-09-12)

Seventeen findings, every cited source line checked before accepting. The ones that change behaviour:

| # | Finding | Where it is fixed |
|---|---|---|
| 1 | **Blocker.** `cs` changes before the window never reached cgame: the reader never updated its own gamestate | Task 2: the reader applies `cs`/`bcs*` as it parses, exactly as `CL_ConfigstringModified` |
| 2 | Parse ring 2048, engine uses `MAX_PARSE_ENTITIES = PACKET_BACKUP × MAX_SNAPSHOT_ENTITIES = 8192`; deltas up to 31 back would read overwritten slots | Task 2 |
| 3 | Command ring 32, engine keeps `MAX_RELIABLE_COMMANDS = 64` | Task 2 |
| 4 | `--dump-snapshots` would exit at the host's `--map or --shot is required` check (`pantheon_frame.c:674`) | Task 3 |
| 5 | G1 compared only `ps.origin`, which never touches the entity ring; wrong key names (`origin_x/y/z`) | Task 3: entity-level comparison |
| 6 | Adjacent frags (pre-roll before previous end) cannot be served by a forward-only reader | Task 4: windows merge into continuous passes |
| 7 | cgame started at the wrong command sequence, and with zeroed demo info | Task 4: first snapshot's sequence; a pre-scan fills demo info |
| 8 | Compile errors hidden by `-w` | Task 2: host files compile with `-Werror=implicit-function-declaration` |
| 9 | Sound handles re-issued per window, exhausted by window 3; entity-attached sounds at full volume | Task 6 |
| 10 | The public-export profile and the `wolfcam-ql` gamedir were dropped — the first would reintroduce burned-in names | Task 7 maps profiles to `--set`s (revision 3); Task 4 uses `--game wolfcam-ql` |
| 11 | `_mix` was a placeholder with no path to the paks | Task 7, specified in full |
| 12 | G4 asserted keys the same function set; semantics differed from wolfcam's | Task 7: keys derived from `capture_demo` itself; shared helpers |
| 13 | **The HDR probe could only ever answer "no"**: fixed-function GL clamps colour to [0,1] unless `glClampColor` disables it | Task 10: clamps off, and a positive control that must exceed 1.0 |
| 14 | G2 compared by fraction of AVI length, not by server time | Task 5 |

---

## Revision 4 — the user's corrections (2026-09-12)

| Change | Why | Where |
|---|---|---|
| The WolfcamQL source becomes a **reproducible dependency**: pinned manifest, deterministic download, SHA-256 verified *before* extraction, automatic bootstrap from the normal build, clean-clone proof. The archive is **not** committed to git. | Binary archives accumulate in history and diff badly; a hash-pinned bootstrap is reproducible. Licence, attribution and provenance travel with it — the bootstrap never downloads anonymous code. | **Task 0.5** |
| **G2 is state-first.** Pixel equality with wolfcam is not the criterion; every material visual difference is classified, and `UNKNOWN` blocks cutover. | PANTHEON is already more correct than wolfcam in places (the window-era black triangle). Demanding a match would recreate defects. | Rollout gates; Task 5 |
| **G1 is checked at the interface cgame consumes**: snapshot header, every `entityState_t`/`playerState_t` field, configstrings after every preceding `cs`, command ordering, gamestate, `clientNum`, `checksumFeed` — and the rings are **deliberately wrapped** (8191→8193 parse entities, 63→65 reliable commands). | A renderer can produce beautiful output while showing the wrong game state. Short tests that never wrap a ring prove nothing about it. | Task 3 |
| **Machine gates are hard assertions before any contact sheet reaches the user.** Humans judge what only eyes can (the POV, the rocket's instant, whether blur is cleaner); timestamps, snapshots, sizes and stale configstrings never reach a human. | A human should never be asked to spot a 31 ms offset. | Human eye-check stops |
| **Runtime handshake**: the host announces engine, build, backend, protocol, profile + profile hash, requested and render size; Python validates it or fails. | A concrete contract instead of trusting that the right binary ran with the right settings. | Task 7 |
| **Task 1 fixes the boundary, not just the linker**: every `PANTHEON_CG_*` symbol is classified required / obsolete experiment / wrong boundary, behind one narrow interface. | Deterministic rendering and seeking will be tested through that interface. | Task 1 |
| **Music and edit work stay out of this branch.** | When a beat lands wrong, the cause must be attributable: demo timing, extraction, frame timestamps, audio, clip construction, retiming, music analysis or muxing. Finish the capture box first. | Out of scope; separate follow-up |

## Revision 3 — second review (2026-09-12)

| # | Finding | Fixed in |
|---|---|---|
| 1 | **Blocker.** A second `PANTHEON_CMD_RING` define left `cg_cmds` at 32 slots while indexing used `% 64` — a buffer overrun | Task 2 Step 1: *replace* line 52 |
| 2 | After `bcs2`, cgame was handed the raw `bcs2` instead of the assembled `cs` | Task 2 Step 1 (`cl_cgame.c:647-661`) |
| 3 | Commands between the first and second snapshot of a pass were never queued | Task 4 Step 3 |
| 4 | **Blocker.** `s_demoPath` referenced one task before it was declared | Task 3 Step 1 |
| 5 | Shared `_frames/` let a shorter re-capture encode stale frames; ~580 MB of TGAs per clip never deleted | Task 7: per-capture temp dir, removed after encoding |
| 6 | The HDR probe would have edited the untracked vendored tree — through the worktree junction, the main checkout's source | Task 10: a separate probe build on a copied file |
| 7 | `profile=None` is the **batch profile**, not the stock view; refusing profiles would break `review_proxy` and `public_clip_export` and make G2 compare different HUDs | Task 7: profiles mapped to host `--set`s; H2 includes a public-profile disclosure check |
| 7b | *(found while fixing 7)* The host appends `--set`s to a 1024-byte buffer with `Q_strcat`, which **truncates silently** | Task 7 Step 5 |
| 8 | A completeness test compared the shared rule with itself | Task 7: concrete values |
| 9 | `pantheon_capture` unclassified between Task 1 and Task 7 — HL-1 suite red | Task 1 |
| 10 | "Byte-identical to the Task 0 build" with no Task 0 render | Task 0 Step 2 |
| 11 | `CG_INIT` given `serverMessageNum = 1`; wolfcam passes the current message sequence | Task 4 Step 1 |
| 12 | G2 assumed both AVIs hold every frame | Task 5 Step 2 |
| 13 | G1 would fail on snapshots `DM73Parser` keeps without their delta base | Task 3 Step 3 |
| 14 | `real_protocol` not set from `com_protocol` 66–71 | Task 2 Step 2 |
| 15 | Cutover said "push" | Task 11: feature branch + PR, never `main` |

## Constraints (user decisions, 2026-09-12 — do not relitigate)

1. **The 64×64 WGL device-context window stays.** Output size is independent of the monitor (proven: 5120×2880, commit `cf27b8ac`). It still needs a valid interactive Windows graphics session; that is acceptable. Windowless context creation is **out of scope** unless the renderer must run as a service.
2. **No supersampling merge until accumulation is linear-light.** Our own motion-blur accumulator has the same flaw and is fixed here (Task 9); `codex/capture-supersampling` must adopt the same resolve before it merges.
3. **No HDR/EXR, floating-point targets or asset work in this plan.** Task 10 *measures* whether values above 1.0 survive the renderer before tonemap/gamma/clamp. Its result decides whether an HDR plan is written at all.

## Rollout gates

| Gate | Proves | Pass condition |
|---|---|---|
| **G1** decoder agreement *(the most important gate)* | What cgame is fed is what the demo says | 3 demos (2 maps, ≥1 protocol 91). Every snapshot: `serverTime`, `snapFlags`, `serverCommandSequence`, `numEntities`, **every** `playerState_t` and `entityState_t` netfield, and the configstring set after all preceding `cs`/`bcs*` agree with an independent Python implementation; reliable commands arrive in the same order; gamestate, `clientNum`, `checksumFeed` agree. The parse ring must be seen to wrap (≥1 snapshot straddling the 8192 boundary) and the command ring must pass its 63→64→65 unit test. |
| **G2** state-first parity | PANTHEON shows the right moment from the right eyes; every visual difference from wolfcam is explained | Machine: for every comparison frame, server time, snapshot number, camera origin/angles/FOV, POV client, weapon, animation state, entity origins, configstring generation, score/round state and viewport size match demo truth. Then an image diff against wolfcam, each difference **classified**: `PASS_EQUAL` · `PASS_EXPECTED_RENDERER_DIFFERENCE` · `PASS_PANTHEON_FIX` · `FAIL_GAME_STATE` · `FAIL_CAMERA` · `FAIL_TIMING` · `FAIL_RENDERING` · `UNKNOWN`. Any `FAIL_*` or `UNKNOWN` blocks cutover. |
| **G3** audio parity | cgame's own sounds, mixed offline, land where wolfcam's do | 10 frags: envelope lag ≤ 40 ms and correlation ≥ 0.6 |
| **G4** contract parity | Callers cannot tell the backends apart, and the right binary ran | Keys and types derived from `capture_demo` itself; completeness from the shared rule; **handshake** validated (build, backend, profile hash, sizes); suite at or better than the Task 0 baseline |

The default flips (Task 11) only after G1–G4 **and** the user's explicit go.

## Human eye-check stops (never skip)

**Machine gates first.** Nothing reaches the user until that stage's machine assertions have passed: timestamps, snapshot numbers, frame counts, render size, configstring state, profile hash. The user is asked only what needs eyes.

| Stop | After | The user looks at |
|---|---|---|
| **H1** | Task 4 | 3 frames of a demo window through PANTHEON's eyes: does it read as the first-person capture? |
| **H2** | Task 5 | 10 parity sheets, same server times, same profile, wolfcam vs PANTHEON: PASS/FAIL each — plus one public-profile clip checked frame by frame for opponent names |
| **H3** | Task 8 | The same 10 clips with sound: rockets, hits, announcer where wolfcam has them |
| **H4** | Task 9 | Before/after crop of a bright moving edge: no dark fringe |
| **H5** | Task 10 | The HDR measurement and its decision |
| **H6** | Task 11 | Go/no-go; then one real frag through the normal mining command, watched end to end |

## Known limits, stated up front

- **Pre-roll replaces seeking.** Deltas force the reader to parse from the file's start, but cgame starts `PREROLL_MS` (1500) before a pass. Effects begun earlier are absent — the same property as wolfcam's `seekclock`.
- **Looping sounds are out of G3** (logged, not mixed in v1). **Spatial audio is approximate**: Q3's distance attenuation and pan, no room acoustics. G3 measures timing.
- **Demo info is approximate where wolfcam pre-scans**: `firstServerTime`/`lastServerTime` are exact (pre-scan); `gameStartTime` comes from `CS_LEVEL_START_TIME`; `gameEndTime` is the last server time. Kill/victim/pickup look-ahead stays `-1` (as in a live game).
- **Profiles** are mapped from `master_profile.PROFILES` to host `--set`s, with `None` resolving to `PROFILE_NAME` exactly as `profile_fps` does. A cvar the host never registers is a **silent no-op** (the engine accepts and ignores it), so parity is proven by eye at H2, and the public-export profile is checked for burned-in names there.

---

## File Structure

| File | Responsibility |
|---|---|
| **Create** `engine/pantheon_renderer/host/pantheon_demo_feed.c` | `.dm_73` → current gamestate + snapshots + server commands, via `msg.c`. Owns the delta rings and its own gamestate. Knows nothing about rendering. |
| **Create** `engine/pantheon_renderer/host/pantheon_sound_log.c` | Registered sound names and start/local events → TSV. Plays nothing. |
| Modify `engine/pantheon_renderer/host/pantheon_cg_feed.c` | 64-slot, sequence-numbered command ring; `cs`/`bcs*` applied when cgame reads them; entity origin lookup for sounds; last-executed tracking. |
| Modify `engine/pantheon_renderer/host/pantheon_cg_run.c` | `PANTHEON_CG_Init(clientNum, serverCommandSequence)`; sound time. |
| Modify `engine/pantheon_renderer/host/pantheon_cg_syscall.c` | Sound cases → logger; last-executed command. |
| Modify `engine/pantheon_renderer/host/pantheon_frame.c` | `--demo`, `--window` (repeatable), `--fps`, `--dump-snapshots`, `--sound-log`, `--probe-hdr`; passes; linear-light blur. |
| Modify `engine/pantheon_renderer/build_cgame.sh`, `build_host.sh` | New files; strict implicit-declaration errors on host files; no standalone exe. |
| Modify `engine/parser/demo_parse.py` | Optional per-snapshot entity capture (`capture_entities=True`) for G1. Default off: no behaviour change. |
| **Create** `engine/pantheon/pantheon_capture.py` | The backend. |
| **Create** `engine/pantheon/sound_mix.py` | Sound log + samples → stereo float PCM. Pure. |
| **Create** `engine/pantheon/capture_parity.py` | G2 sheets and G3 measurement. |
| Modify `creative_suite/engine/wolfcam_capture.py` | `capture_backend()`, dispatch, and `completeness()` extracted so both backends share it. |
| Modify `engine/pantheon/backends.py`, `engine/pantheon/model_assets.py:28` | Register `PANTHEON_NATIVE`; resolve the host through `store`. |
| Tests | `test_pantheon_capture.py` (new), `test_pantheon_demo_feed.py` (new), `test_render_permit.py` (`LAUNCH_SITES`), `test_pantheon_headless_boundary.py` (classification). |

Python tests: `E:/PersonalAI/venv/Scripts/python.exe -m pytest <path> -q`
Build (Git Bash): `cd engine/pantheon_renderer && ./build_host.sh && ./build_cgame.sh`

**Worktree note:** `engine/pantheon_renderer/wolfcamql-11.3-src/` is deliberately untracked (extracted from the archive pinned in `SOURCE.sha256`). In a worktree, junction it from the main checkout before building:
`MSYS_NO_PATHCONV=1 cmd /c mklink /J "<worktree>\engine\pantheon_renderer\wolfcamql-11.3-src" "G:\QUAKE_LEGACY\engine\pantheon_renderer\wolfcamql-11.3-src"`

---

### Task 0: Baseline

- [ ] **Step 1:** Worktree exists (`G:/QUAKE_LEGACY_WORKTREES/pantheon-capture`, branch `feature/pantheon-production-capture`), source junctioned, `./build_cgame.sh` exits 0.
- [ ] **Step 2: A reference render.** With the Task 0 build, render the regenerated `v2.shot` (66 frames, `--cgame --set cg_draw2D 0`) into `G:/QUAKE_LEGACY_WORKTREES/pc_reference/` (outside git — TGAs are large) and commit their MD5 list as `docs/reference/2026-09-12-v2shot-reference.md5`. Task 2 compares against it.
- [ ] **Step 2b: The baseline, in chunks.** Never run the suite as one process: it grows to ~12.6 GB and, on this workstation's normal background load, starved Windows (`0xc0000142` start-up failures, 2026-09-12). Run `E:/PersonalAI/venv/Scripts/python.exe scripts/run_tests_chunked.py creative_suite/tests --out docs/reference/2026-09-12-capture-baseline.txt` — one pytest process per test file, nothing else heavy running, and it stops itself if free RAM falls below 6 GB. Expected: failures only in `test_scene_editor.py` (live frags DB) and `test_tool_root.py::test_no_new_module_finds_its_tools_beside_the_code` (another session's untracked `engine/music/`). Anything else: stop and report.
- [ ] **Step 3:** `git add docs/reference/2026-09-12-capture-baseline.txt && git commit -m "docs: test baseline before the PANTHEON capture work"`

---

### Task 0.5: The WolfcamQL source, reproducible from a clean clone

PANTHEON compiles against WolfcamQL 11.3, extracted from the tarball bundled with WolfWhisperer (`wolfcamql-src.tar.gz`, 4,101,307 bytes, SHA-256 `3051397d08f15ee9345f71c4eac35eaedc568ac2bf8b3ad3de3d9aa4349ee8dc`, dated 2016-08-13 — the same day as the shipped `qagamex86` compile timestamp). Upstream project: `https://github.com/brugal/wolfcamql`. Today the extracted tree is gitignored and nothing extracts it, so a clean clone cannot build.

**Decision (user, 2026-09-12):** do not commit the archive. Pinned manifest → deterministic download → SHA-256 verified before extraction → deterministic extraction → automatic from the normal build → clean-clone proof. If no immutable upstream URL serves these exact bytes, mirror the *identical* archive in a project-controlled store (a GitHub Release asset) — **ask the user before publishing it**, since a Release on a public repo is public. Vendor into git only if air-gapped clean-clone builds are ever required.

**Files:**
- Create: `third_party/wolfcamql/SOURCE.json`, `third_party/wolfcamql/LICENSE` (the archive's `COPYING.txt`), `third_party/wolfcamql/NOTICE` (lists `COPYING-backtrace.txt`, `unifont-LICENSE.txt`, `CREDITS-openarena.txt`, `README-ioquake3.txt`, all shipped inside the archive)
- Create: `scripts/bootstrap_wolfcamql.py` (stdlib only)
- Modify: `engine/pantheon_renderer/build_host.sh`, `build_cgame.sh` (bootstrap if absent); delete `engine/pantheon_renderer/SOURCE.sha256` (superseded by `SOURCE.json`)
- Test: `creative_suite/tests/test_bootstrap_wolfcamql.py`

- [ ] **Step 1: Find an immutable upstream for these bytes.** Check `brugal/wolfcamql` releases and tags from the 11.x era (`gh api repos/brugal/wolfcamql/releases`, `.../tags`). If an asset's SHA-256 equals the pin, it is the primary URL. If a tag's source tree matches the extracted tree file-for-file (diff, not hash — GitHub's generated archives are not byte-stable), record it in `SOURCE.json` as `upstream_commit` for provenance, but it cannot be the download (different bytes). Record what was checked and the outcome in `SOURCE.json.provenance_notes`.

- [ ] **Step 2: The manifest**

```json
{
  "name": "wolfcamql",
  "version": "11.3 (WolfWhisperer source bundle)",
  "archive": "wolfcamql-src.tar.gz",
  "sha256": "3051397d08f15ee9345f71c4eac35eaedc568ac2bf8b3ad3de3d9aa4349ee8dc",
  "size": 4101307,
  "top_level_dir": "wolfcamql-src",
  "extract_to": "engine/pantheon_renderer/wolfcamql-11.3-src",
  "upstream_project": "https://github.com/brugal/wolfcamql",
  "upstream_commit": null,
  "license": "GPL-2.0 (COPYING.txt in the archive; see NOTICE for bundled components)",
  "mirrors": [],
  "local_fallback_env": "WOLFCAMQL_ARCHIVE",
  "provenance_notes": "Bundled with WolfWhisperer; archive date 2016-08-13 matches qagamex86 compile time 1471095929."
}
```

`mirrors` is filled by Step 1 (upstream asset) and/or Step 6 (project Release, after the user approves).

- [ ] **Step 3: Failing tests** — build tiny archives in `tmp_path`; no network.

```python
# creative_suite/tests/test_bootstrap_wolfcamql.py
import hashlib
import io
import json
import tarfile
from pathlib import Path

import pytest


def _tar(tmp_path: Path, members: dict[str, bytes], name="src.tar.gz") -> Path:
    p = tmp_path / name
    with tarfile.open(p, "w:gz") as t:
        for n, data in members.items():
            info = tarfile.TarInfo(n); info.size = len(data)
            t.addfile(info, io.BytesIO(data))
    return p


def _manifest(tmp_path, archive: Path, **over) -> Path:
    m = {"name": "t", "version": "1", "archive": archive.name,
         "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
         "size": archive.stat().st_size, "top_level_dir": "top",
         "extract_to": str(tmp_path / "out"), "mirrors": [],
         "local_fallback_env": "T_ARCHIVE"}
    m.update(over)
    p = tmp_path / "SOURCE.json"; p.write_text(json.dumps(m)); return p


def test_extracts_after_verifying(tmp_path, monkeypatch):
    from scripts import bootstrap_wolfcamql as B
    a = _tar(tmp_path, {"top/a.c": b"int x;"})
    monkeypatch.setenv("T_ARCHIVE", str(a))
    out = B.bootstrap(_manifest(tmp_path, a))
    assert (out / "top" / "a.c").read_bytes() == b"int x;"
    assert json.loads((out / ".bootstrap.json").read_text())["sha256"] == \
        hashlib.sha256(a.read_bytes()).hexdigest()


def test_a_wrong_checksum_fails_before_anything_is_extracted(tmp_path, monkeypatch):
    from scripts import bootstrap_wolfcamql as B
    a = _tar(tmp_path, {"top/a.c": b"int x;"})
    monkeypatch.setenv("T_ARCHIVE", str(a))
    with pytest.raises(B.ChecksumMismatch):
        B.bootstrap(_manifest(tmp_path, a, sha256="0" * 64))
    assert not (tmp_path / "out").exists()


def test_a_path_escaping_member_is_refused(tmp_path, monkeypatch):
    from scripts import bootstrap_wolfcamql as B
    a = _tar(tmp_path, {"top/../../evil.c": b"x"})
    monkeypatch.setenv("T_ARCHIVE", str(a))
    with pytest.raises(B.UnsafeArchive):
        B.bootstrap(_manifest(tmp_path, a))
    assert not (tmp_path / "evil.c").exists()


def test_an_existing_tree_is_adopted_only_if_it_matches(tmp_path, monkeypatch):
    from scripts import bootstrap_wolfcamql as B
    a = _tar(tmp_path, {"top/a.c": b"int x;"})
    monkeypatch.setenv("T_ARCHIVE", str(a))
    out = tmp_path / "out"; (out / "top").mkdir(parents=True)
    (out / "top" / "a.c").write_bytes(b"int y;")          # differs
    with pytest.raises(B.TreeMismatch):
        B.bootstrap(_manifest(tmp_path, a), adopt=True)
    (out / "top" / "a.c").write_bytes(b"int x;")          # matches
    B.bootstrap(_manifest(tmp_path, a), adopt=True)
    assert (out / ".bootstrap.json").exists()


def test_no_source_is_a_hard_failure(tmp_path, monkeypatch):
    from scripts import bootstrap_wolfcamql as B
    a = _tar(tmp_path, {"top/a.c": b"x"})
    monkeypatch.delenv("T_ARCHIVE", raising=False)
    m = _manifest(tmp_path, a); a.unlink()
    with pytest.raises(B.NoSource):
        B.bootstrap(m)
```

Add `scripts/__init__.py` if `scripts` is not yet a package.

- [ ] **Step 4: The bootstrap**

```python
# scripts/bootstrap_wolfcamql.py
"""Make the WolfcamQL source PANTHEON builds against exist -- exactly, or not at all.

Reads third_party/wolfcamql/SOURCE.json. Obtains the archive from (in order)
the local fallback env var, the download cache, then each mirror; verifies
size and SHA-256 BEFORE extracting anything; refuses members that would
escape the target; writes a stamp. A mismatch is a hard failure: PANTHEON is
never built against bytes nobody pinned.

    python scripts/bootstrap_wolfcamql.py            # extract if absent
    python scripts/bootstrap_wolfcamql.py --adopt    # verify an existing tree, then stamp it
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "third_party" / "wolfcamql" / "SOURCE.json"
CACHE = ROOT / ".cache" / "third_party"          # gitignored


class ChecksumMismatch(RuntimeError): ...
class UnsafeArchive(RuntimeError): ...
class TreeMismatch(RuntimeError): ...
class NoSource(RuntimeError): ...


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _verify(path: Path, m: dict) -> Path:
    if path.stat().st_size != m["size"] or _sha(path) != m["sha256"]:
        raise ChecksumMismatch(f"{path}: expected {m['sha256']} ({m['size']} bytes)")
    return path


def _obtain(m: dict) -> Path:
    env = os.getenv(m.get("local_fallback_env", ""))
    if env and Path(env).exists():
        return _verify(Path(env), m)
    cached = CACHE / m["sha256"] / m["archive"]
    if cached.exists():
        return _verify(cached, m)
    for url in m.get("mirrors", []):
        cached.parent.mkdir(parents=True, exist_ok=True)
        tmp = cached.with_suffix(".part")
        try:
            with urllib.request.urlopen(url, timeout=60) as r, open(tmp, "wb") as f:
                shutil.copyfileobj(r, f)
            _verify(tmp, m)
        except ChecksumMismatch:
            tmp.unlink(missing_ok=True)
            raise
        except OSError:
            tmp.unlink(missing_ok=True)
            continue
        tmp.replace(cached)
        return cached
    raise NoSource(f"no verified copy of {m['archive']}: set {m.get('local_fallback_env')} "
                   f"or add a mirror to {MANIFEST}")


def _safe_members(t: tarfile.TarFile, top: str):
    for mem in t.getmembers():
        p = Path(mem.name)
        if p.is_absolute() or ".." in p.parts or (p.parts and p.parts[0] != top) \
                or mem.issym() or mem.islnk() or mem.isdev():
            raise UnsafeArchive(f"refusing member {mem.name!r}")
    return t.getmembers()


def bootstrap(manifest: Path = MANIFEST, *, adopt: bool = False) -> Path:
    m = json.loads(Path(manifest).read_text(encoding="utf-8"))
    out = Path(m["extract_to"])
    if not out.is_absolute():
        out = ROOT / out
    stamp = out / ".bootstrap.json"
    if stamp.exists() and json.loads(stamp.read_text())["sha256"] == m["sha256"]:
        return out
    archive = _obtain(m)                        # verified before anything else
    with tarfile.open(archive, "r:gz") as t:
        members = _safe_members(t, m["top_level_dir"])
        if adopt and out.exists():
            for mem in members:
                if mem.isfile():
                    disk = out / mem.name
                    if not disk.exists() or disk.read_bytes() != t.extractfile(mem).read():
                        raise TreeMismatch(f"{disk} differs from the pinned archive")
        else:
            if out.exists() and any(out.iterdir()):
                raise TreeMismatch(f"{out} exists without a stamp; rerun with --adopt to verify it")
            staging = Path(tempfile.mkdtemp(dir=out.parent if out.parent.exists() else None))
            try:
                t.extractall(staging, members=members)
                out.parent.mkdir(parents=True, exist_ok=True)
                if out.exists():
                    out.rmdir()
                shutil.move(str(staging), str(out))
            finally:
                shutil.rmtree(staging, ignore_errors=True)
    stamp.write_text(json.dumps({"sha256": m["sha256"], "archive": m["archive"],
                                 "version": m["version"]}, indent=2))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--adopt", action="store_true")
    a = ap.parse_args()
    try:
        print(bootstrap(adopt=a.adopt))
    except (ChecksumMismatch, UnsafeArchive, TreeMismatch, NoSource) as e:
        print(f"bootstrap_wolfcamql: {e}", file=sys.stderr)
        sys.exit(2)
```

Note: the extraction lands the archive's `wolfcamql-src/` directory *inside* `extract_to`, reproducing today's `wolfcamql-11.3-src/wolfcamql-src/code/...` layout, so no include path changes.

- [ ] **Step 5: Wire the build** — at the top of `build_host.sh` and `build_cgame.sh`, after `HERE=`:

```bash
# The WolfcamQL source is a pinned dependency, not a checked-in tree
# (third_party/wolfcamql/SOURCE.json). Absent or unstamped: bootstrap it.
if [ ! -f "$HERE/wolfcamql-11.3-src/.bootstrap.json" ]; then
    python "$HERE/../../scripts/bootstrap_wolfcamql.py" || {
        echo "WolfcamQL source unavailable -- see third_party/wolfcamql/SOURCE.json" >&2; exit 2; }
fi
```

Adopt the existing tree on this machine once: `WOLFCAMQL_ARCHIVE="WOLF WHISPERER/WolfcamQL/wolfcamql-src.tar.gz" python scripts/bootstrap_wolfcamql.py --adopt` — expected: prints the path; every file matched.

Add `.cache/` to `.gitignore`. Delete `engine/pantheon_renderer/SOURCE.sha256`; mention `third_party/wolfcamql/SOURCE.json` in the `.gitignore` comment above `wolfcamql-11.3-src/`.

- [ ] **Step 6: The clean-clone proof.** `git clone --no-local` the branch into a scratch directory; with `WOLFCAMQL_ARCHIVE` **unset** and no cache, run `engine/pantheon_renderer/build_host.sh && build_cgame.sh`. Expected: the bootstrap downloads from a mirror, verifies, extracts, and `pantheon_cgame.exe` builds. If no mirror exists yet: **stop and ask the user** whether to publish the identical archive as a GitHub Release asset on `Stoneface30/quake-legacy` (public). Only after a yes: create the release, add its URL to `mirrors`, rerun the proof. Record the clone path, commands and output in `docs/reference/<date>-clean-clone-build.md`. Delete the scratch clone.

- [ ] **Step 7:** `pytest creative_suite/tests/test_bootstrap_wolfcamql.py -q` → 5 passed. Commit: `build: WolfcamQL source is a pinned, verified, bootstrapped dependency`

---

### Task 1: One binary, found through the store

The standalone `pantheon_frame.exe` has not linked since 2026-09-08 and does not exist; `model_assets.py:28` points at it by a hardcoded `G:/` path (HL-9). `pantheon_cgame.exe` accepts `--dump-model` (same `pantheon_frame.c`).

**Files:** `engine/pantheon_renderer/build_host.sh`, `engine/pantheon/model_assets.py:28`, create `engine/pantheon/pantheon_capture.py`, test `creative_suite/tests/test_pantheon_capture.py`

- [ ] **Step 0: Fix the boundary, not only the linker.** The 25 undefined references are 13 symbols: `PANTHEON_CG_AddExplosion`, `AddPlayer`, `AddPlayerInfo`, `AddRocket`, `BindRenderer`, `BuildGameState`, `ComposeSnapshot`, `Frame`, `Init`, `PushSnapshot`, `Reset`, `SetGameState`, `Shutdown`. Trace each call site in `host/pantheon_frame.c` and classify it:

| Class | Meaning | Action |
|---|---|---|
| **required runtime API** | The host must say this to cgame | Declared in one header, `host/pantheon_cgame.h` |
| **obsolete experiment** | CLI proofs (`--rocket`, `--explosion`, composed test snapshots) | Kept only behind the proof flags, declared in `host/pantheon_cg_compose.h`, never on the demo path |
| **wrong boundary** | The host reaching into cgame internals | Replaced by the narrow interface |

The target interface — everything the production path may call:

```c
/* host/pantheon_cgame.h -- the ONLY cgame surface the host uses. */
void     PANTHEON_CG_BindRenderer(refexport_t *re, const glconfig_t *cfg);
void     PANTHEON_CG_LoadGameState(const gameState_t *gs, int clientNum);
void     PANTHEON_CG_ApplyServerCommand(int seq, const char *text);
void     PANTHEON_CG_SetSnapshot(int messageNum, const snapshot_t *snap);
void     PANTHEON_CG_SetDemoInfo(int gameStart, int gameEnd, int firstServerTime,
                                 int lastServerTime, const char *mapName);
void     PANTHEON_CG_Init(int clientNum, int serverMessageNum, int serverCommandSequence);
void     PANTHEON_CG_DrawActiveFrame(int serverTime, qboolean firstFrame);
void     PANTHEON_CG_Shutdown(void);
```

`LoadGameState` replaces `Reset` + `SetGameState`; `ApplyServerCommand` replaces `QueueServerCommandSeq`; `SetSnapshot` replaces `PushSnapshot`; `DrawActiveFrame` replaces `Frame`. The old names stay as thin wrappers only if a proof flag still needs them. Write the classification table, with every call site, to `docs/reference/<date>-cgame-host-interface.md`. Behaviour must not change: the Task 0 `v2.shot` MD5s still match after the rename.

Later tasks use the new names; where their text still says `PushSnapshot`/`QueueServerCommandSeq`/`Frame`, read `SetSnapshot`/`ApplyServerCommand`/`DrawActiveFrame`.

- [ ] **Step 1: Failing test**

```python
# creative_suite/tests/test_pantheon_capture.py
from pathlib import Path

from engine.pantheon import store as S


def test_host_exe_is_resolved_through_the_store_not_a_drive_letter():
    from engine.pantheon import pantheon_capture as PC
    assert PC.host_exe() == S.CODE_ROOT / "engine" / "pantheon_renderer" / "build" / "pantheon_cgame.exe"


def test_model_assets_uses_the_one_binary_that_exists():
    from engine.pantheon import model_assets, pantheon_capture as PC
    assert model_assets.HOST_EXE == PC.host_exe()
```

- [ ] **Step 2:** Run it: FAIL (`ModuleNotFoundError: engine.pantheon.pantheon_capture`).

- [ ] **Step 3: Implement**

```python
# engine/pantheon/pantheon_capture.py
"""PANTHEON_NATIVE capture backend.

Renders production demo clips with pantheon_cgame.exe: our own binary, the
WolfcamQL 11.3 renderer and cgame linked statically, drawing into its own
framebuffer object. Matches creative_suite.engine.wolfcam_capture.capture_demo's
return contract so callers cannot tell the two backends apart (gate G4).
"""
from __future__ import annotations

from pathlib import Path

from engine.pantheon import store as S


def host_exe() -> Path:
    """The one PANTHEON binary, from the code root (HL-9): a worktree runs its
    own build, never the main checkout's."""
    return S.CODE_ROOT / "engine" / "pantheon_renderer" / "build" / "pantheon_cgame.exe"
```

`engine/pantheon/model_assets.py`, replacing line 28:

```python
from engine.pantheon.pantheon_capture import host_exe as _host_exe
HOST_EXE = _host_exe()
```

`build_host.sh`: replace the final `-o "$OUT/pantheon_frame.exe"` link with

```bash
# One binary: build_cgame.sh links these objects into pantheon_cgame.exe.
# The standalone pantheon_frame.exe stopped linking on 2026-09-08.
echo "built objects in $OUT (link with ./build_cgame.sh)"
```

and add `-Werror=implicit-function-declaration` to the compile flags used for `host/*.c` only (not the vendored tree — it would not build).

In `creative_suite/tests/test_pantheon_headless_boundary.py`, add `"pantheon_capture"` to `BACKEND_ALLOWED` ("launches the PANTHEON renderer") now — the HL-1 suite fails on any unclassified module under `engine/pantheon/`.

- [ ] **Step 4:** `test_pantheon_capture.py` (2) and `test_pantheon_headless_boundary.py` pass; both builds exit 0. If the stricter flag surfaces errors in existing host files, fix each with a real prototype — never with `-w`.
- [ ] **Step 5:** `git commit -am "fix: one PANTHEON binary, found through the store"` (add the new files explicitly).

---

### Task 2: The demo reader, and the command ring it feeds

Mirrors `CL_ReadDemoMessage` (`cl_main.c:1063`), `CL_ParseServerMessage` (`cl_parse.c:1703`), `CL_ParseGamestate` (`:830`), `CL_ParseSnapshot` (`:383`), `CL_ParsePacketEntities` (`:108`), `CL_DeltaEntity` (`:80`), `CL_ParseCommandString` (`:1338`), and — for the reader's own gamestate — `CL_GetServerCommand`'s `bcs*`/`cs` handling and `CL_ConfigstringModified` (`cl_cgame.c`). Copy logic, not ideas.

**Files:** create `host/pantheon_demo_feed.c`; modify `host/pantheon_cg_feed.c`, `build_cgame.sh`

- [ ] **Step 1: The command ring in `pantheon_cg_feed.c`** — **replace** line 52 (`#define PANTHEON_CMD_RING 32`). Do not add a second define: the compiler only warns, `-w` hides it, and `cg_cmds` would stay 32 slots while indexing uses `% 64`.

```c
/* 64, as MAX_RELIABLE_COMMANDS: a round start can carry more than 32
 * configstring updates between two snapshots. */
#define PANTHEON_CMD_RING MAX_RELIABLE_COMMANDS
static int  cg_cmd_num[PANTHEON_CMD_RING];   /* which seq owns each slot */
static int  cg_cmd_executed;                 /* CG_GETLASTEXECUTEDSERVERCOMMAND */
static char cg_bigcs[BIG_INFO_STRING];
```

Replace `PANTHEON_CG_QueueServerCommand` so composed shots keep working, and add the sequence-numbered form:

```c
void PANTHEON_CG_QueueServerCommandSeq(int seq, const char *text)
{
    if (!text || seq <= 0) return;
    Q_strncpyz(cg_cmds[seq % PANTHEON_CMD_RING], text, BIG_INFO_STRING);
    cg_cmd_num[seq % PANTHEON_CMD_RING] = seq;
    if (seq > cg_cmd_seq) cg_cmd_seq = seq;
}

void PANTHEON_CG_QueueServerCommand(const char *text)
{
    PANTHEON_CG_QueueServerCommandSeq(cg_cmd_seq + 1, text);
}
```

Add the configstring rewrite (`CL_ConfigstringModified`, including its early return):

```c
/* Rebuild the string pool with one index replaced. Shared by the reader's
 * gamestate and cgame's, so the two cannot apply a change differently. */
void PANTHEON_GameState_Set(gameState_t *gs, int index, const char *value)
{
    gameState_t old;
    int i, len;
    const char *cur;

    if (index < 0 || index >= MAX_CONFIGSTRINGS) return;
    cur = gs->stringOffsets[index] ? gs->stringData + gs->stringOffsets[index] : "";
    if (!strcmp(cur, value)) return;                      /* unchanged */
    old = *gs;
    memset(gs, 0, sizeof(*gs));
    gs->dataCount = 1;
    for (i = 0; i < MAX_CONFIGSTRINGS; i++) {
        const char *s = (i == index) ? value
                      : (old.stringOffsets[i] ? old.stringData + old.stringOffsets[i] : "");
        if (!s[0]) continue;
        len = strlen(s);
        if (len + 1 + gs->dataCount > MAX_GAMESTATE_CHARS)
            Com_Error(ERR_DROP, "PANTHEON: MAX_GAMESTATE_CHARS applying cs %d", index);
        gs->stringOffsets[i] = gs->dataCount;
        memcpy(gs->stringData + gs->dataCount, s, len + 1);
        gs->dataCount += len + 1;
    }
}

/* CL_GetServerCommand's reassembly of big configstrings. Returns qtrue when
 * `text` (already tokenised) completes a `cs` for `gs`; qfalse for bcs0/bcs1
 * pieces, which are absorbed. */
qboolean PANTHEON_GameState_Command(gameState_t *gs, char *bigcs, int bigcsSize)
{
    const char *cmd = Cmd_Argv(0);
    if (!strcmp(cmd, "bcs0")) { Com_sprintf(bigcs, bigcsSize, "cs %s \"%s", Cmd_Argv(1), Cmd_Argv(2)); return qfalse; }
    if (!strcmp(cmd, "bcs1")) { Q_strcat(bigcs, bigcsSize, Cmd_Argv(2)); return qfalse; }
    if (!strcmp(cmd, "bcs2")) {
        Q_strcat(bigcs, bigcsSize, va("%s\"", Cmd_Argv(2)));
        Cmd_TokenizeString(bigcs);
        cmd = Cmd_Argv(0);
    }
    if (!strcmp(cmd, "cs")) PANTHEON_GameState_Set(gs, atoi(Cmd_Argv(1)), Cmd_ArgsFrom(2));
    return qtrue;
}
```

Replace `PANTHEON_CG_GetServerCommand`:

```c
qboolean PANTHEON_CG_GetServerCommand(int seq)
{
    char *text;
    qboolean wasBcs2, isCs;

    if (seq <= 0 || seq > cg_cmd_seq) return qfalse;
    if (cg_cmd_num[seq % PANTHEON_CMD_RING] != seq) return qfalse;   /* aged out */
    text = cg_cmds[seq % PANTHEON_CMD_RING];
    Cmd_TokenizeString(text);
    cg_cmd_executed = seq;
    wasBcs2 = !strcmp(Cmd_Argv(0), "bcs2");
    isCs = wasBcs2 || !strcmp(Cmd_Argv(0), "cs");
    if (!PANTHEON_GameState_Command(&cg_gs, cg_bigcs, sizeof(cg_bigcs)))
        return qfalse;                             /* bcs0/bcs1: nothing for cgame yet */
    /* cl_cgame.c:647-661: after bcs2 the client rescans the ASSEMBLED string,
     * so cgame sees `cs <n> "<value>"`, never `bcs2`. The gamestate update may
     * have re-tokenised; tokenise again for cgame, from the right string. */
    if (isCs) Cmd_TokenizeString(wasBcs2 ? cg_bigcs : text);
    return qtrue;
}

int PANTHEON_CG_LastExecutedServerCommand(void) { return cg_cmd_executed; }
```

In `PANTHEON_CG_Reset`: `memset(cg_cmd_num, 0, sizeof(cg_cmd_num)); cg_cmd_executed = 0; cg_bigcs[0] = 0;` — and **do not** zero `cg_di` there any more (demo info is set once per demo, after Reset; see Task 4).

In `pantheon_cg_syscall.c`: `case CG_GETLASTEXECUTEDSERVERCOMMAND: return PANTHEON_CG_LastExecutedServerCommand();`

- [ ] **Step 2: The reader** — `host/pantheon_demo_feed.c`

```c
/*
 * A .dm_73 BECOMES A SNAPSHOT FEED.
 *
 * Decoded with the engine's own msg.c and huffman.c -- the functions that fill
 * cl.snapshots inside WolfcamQL -- so a snapshot handed to cgame here is the
 * one wolfcam would hand it. Every branch has a counterpart in cl_parse.c /
 * cl_main.c / cl_cgame.c (line numbers in comments). DM73Parser in Python is
 * the independent cross-check (gate G1).
 *
 * The reader keeps ITS OWN gamestate current as `cs` commands arrive
 * (CL_ConfigstringModified). cgame is started only at a pass's pre-roll, so
 * every configstring change before that -- joins, scores, models, the round
 * clock -- must already be in the gamestate cgame is handed.
 */
#include "../wolfcamql-11.3-src/wolfcamql-src/code/qcommon/q_shared.h"
#include "../wolfcamql-11.3-src/wolfcamql-src/code/qcommon/qcommon.h"
#include "../wolfcamql-11.3-src/wolfcamql-src/code/cgame/cg_public.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define PD_MAX_PARSE_ENTITIES (PACKET_BACKUP * MAX_SNAPSHOT_ENTITIES)   /* client.h:96 */

typedef struct {
    qboolean      valid;
    int           messageNum, deltaNum, serverTime, snapFlags, serverCommandNum;
    byte          areamask[MAX_MAP_AREA_BYTES];
    playerState_t ps;
    int           numEntities, parseEntitiesNum;
} pdSnap_t;

static struct {
    FILE         *f;
    int           messageSeq, commandSeq, clientNum;
    gameState_t   gs;
    char          bigcs[BIG_INFO_STRING];
    entityState_t baselines[MAX_GENTITIES];
    pdSnap_t      snaps[PACKET_BACKUP];
    entityState_t parse[PD_MAX_PARSE_ENTITIES];
    int           parseNum;
    pdSnap_t      latest;
    qboolean      haveLatest;
    int           queueFrom;      /* commands with seq > this go to cgame */
} pd;

/* pantheon_cg_feed.c */
void     PANTHEON_CG_QueueServerCommandSeq(int seq, const char *text);
void     PANTHEON_GameState_Set(gameState_t *gs, int index, const char *value);
qboolean PANTHEON_GameState_Command(gameState_t *gs, char *bigcs, int bigcsSize);

#define PD_ENT(base, i) (&pd.parse[((base) + (i)) & (PD_MAX_PARSE_ENTITIES - 1)])

static void PD_DeltaEntity(msg_t *msg, pdSnap_t *frame, int newnum,
                           entityState_t *old, qboolean unchanged)        /* :80 */
{
    entityState_t *state = PD_ENT(pd.parseNum, 0);
    if (unchanged) *state = *old;
    else           MSG_ReadDeltaEntity(msg, old, state, newnum);
    if (state->number == MAX_GENTITIES - 1) return;
    pd.parseNum++;
    frame->numEntities++;
}

static void PD_ParsePacketEntities(msg_t *msg, const pdSnap_t *oldframe,
                                   pdSnap_t *newframe)                   /* :108 */
{
    int newnum, oldindex = 0, oldnum;
    entityState_t *oldstate = NULL;

    newframe->parseEntitiesNum = pd.parseNum;
    newframe->numEntities = 0;
    if (!oldframe || oldframe->numEntities == 0) oldnum = 99999;
    else { oldstate = PD_ENT(oldframe->parseEntitiesNum, 0); oldnum = oldstate->number; }

#define PD_NEXT_OLD() do { oldindex++; \
        if (!oldframe || oldindex >= oldframe->numEntities) oldnum = 99999; \
        else { oldstate = PD_ENT(oldframe->parseEntitiesNum, oldindex); oldnum = oldstate->number; } \
    } while (0)

    for (;;) {
        newnum = MSG_ReadBits(msg, GENTITYNUM_BITS);
        if (newnum == MAX_GENTITIES - 1) break;
        if (msg->readcount > msg->cursize)
            Com_Error(ERR_DROP, "PANTHEON demo: packet entities past end of message");
        while (oldnum < newnum) { PD_DeltaEntity(msg, newframe, oldnum, oldstate, qtrue); PD_NEXT_OLD(); }
        if (oldnum == newnum) { PD_DeltaEntity(msg, newframe, newnum, oldstate, qfalse); PD_NEXT_OLD(); continue; }
        if (oldnum > newnum) PD_DeltaEntity(msg, newframe, newnum, &pd.baselines[newnum], qfalse);
    }
    while (oldnum != 99999) { PD_DeltaEntity(msg, newframe, oldnum, oldstate, qtrue); PD_NEXT_OLD(); }
#undef PD_NEXT_OLD
}

static void PD_ParseSnapshot(msg_t *msg)                                 /* :383 */
{
    pdSnap_t ns, *old;
    int deltaNum, len;

    memset(&ns, 0, sizeof(ns));
    ns.serverCommandNum = pd.commandSeq;
    ns.serverTime = MSG_ReadLong(msg);
    ns.messageNum = pd.messageSeq;
    deltaNum = MSG_ReadByte(msg);
    ns.deltaNum = deltaNum ? ns.messageNum - deltaNum : -1;
    ns.snapFlags = MSG_ReadByte(msg);

    if (ns.deltaNum <= 0) { ns.valid = qtrue; old = NULL; }
    else {
        old = &pd.snaps[ns.deltaNum & PACKET_MASK];
        ns.valid = old->valid && old->messageNum == ns.deltaNum;
    }

    len = MSG_ReadByte(msg);
    if (len > (int)sizeof(ns.areamask))
        Com_Error(ERR_DROP, "PANTHEON demo: areamask length %d", len);
    MSG_ReadData(msg, &ns.areamask, len);
    MSG_ReadDeltaPlayerstate(msg, old ? &old->ps : NULL, &ns.ps);
    PD_ParsePacketEntities(msg, old, &ns);

    if (!ns.valid) return;
    pd.snaps[ns.messageNum & PACKET_MASK] = ns;
    pd.latest = ns;
    pd.haveLatest = qtrue;
}

static void PD_ParseGamestate(msg_t *msg)                                /* :830 */
{
    entityState_t nullstate;
    int cmd, i, len, newnum;
    char *s;

    memset(&pd.gs, 0, sizeof(pd.gs));
    memset(pd.baselines, 0, sizeof(pd.baselines));
    memset(pd.snaps, 0, sizeof(pd.snaps));
    pd.haveLatest = qfalse;                    /* a new gamestate invalidates it */
    pd.commandSeq = MSG_ReadLong(msg);
    pd.gs.dataCount = 1;
    for (;;) {
        cmd = MSG_ReadByte(msg);
        if (cmd == svc_EOF) break;
        if (cmd == svc_configstring) {
            i = MSG_ReadShort(msg);
            if (i < 0 || i >= MAX_CONFIGSTRINGS)
                Com_Error(ERR_DROP, "PANTHEON demo: configstring %d", i);
            s = MSG_ReadBigString(msg);
            len = strlen(s);
            if (len + 1 + pd.gs.dataCount > MAX_GAMESTATE_CHARS)
                Com_Error(ERR_DROP, "PANTHEON demo: MAX_GAMESTATE_CHARS");
            if (i == 0) {                      /* :862 -- msg.c picks field tables from this */
                const char *value = Info_ValueForKey(s, "protocol");
                int p = atoi(value), cp;
                Cvar_Set("real_protocol", value);
                value = Info_ValueForKey(s, "com_protocol");
                cp = atoi(value);
                if (cp >= 66 && cp <= 71) Cvar_Set("real_protocol", value);   /* :917 */
                if ((p >= 66 && p <= 71) || (cp >= 66 && cp <= 71))
                    Cvar_Set("protocol", va("%d", PROTOCOL_Q3));
                else if (p == 73 || p == 90) Cvar_Set("protocol", va("%d", p));
                else Cvar_Set("protocol", va("%d", PROTOCOL_QL));
            }
            pd.gs.stringOffsets[i] = pd.gs.dataCount;
            memcpy(pd.gs.stringData + pd.gs.dataCount, s, len + 1);
            pd.gs.dataCount += len + 1;
        } else if (cmd == svc_baseline) {
            newnum = MSG_ReadBits(msg, GENTITYNUM_BITS);
            if (newnum < 0 || newnum >= MAX_GENTITIES)
                Com_Error(ERR_DROP, "PANTHEON demo: baseline %d", newnum);
            memset(&nullstate, 0, sizeof(nullstate));
            MSG_ReadDeltaEntity(msg, &nullstate, &pd.baselines[newnum], newnum);
        } else Com_Error(ERR_DROP, "PANTHEON demo: bad gamestate byte %d", cmd);
    }
    pd.clientNum = MSG_ReadLong(msg);
    (void)MSG_ReadLong(msg);                   /* checksumFeed */
}

static void PD_ServerCommand(msg_t *msg)                                 /* :1338 */
{
    int seq = MSG_ReadLong(msg);
    char *s = MSG_ReadString(msg);
    char text[BIG_INFO_STRING];

    if (pd.commandSeq >= seq) return;
    pd.commandSeq = seq;
    Q_strncpyz(text, s, sizeof(text));
    /* Keep the reader's gamestate current, whether or not cgame is running. */
    Cmd_TokenizeString(text);
    PANTHEON_GameState_Command(&pd.gs, pd.bigcs, sizeof(pd.bigcs));
    /* Hand it to cgame only once cgame exists for this pass. */
    if (seq > pd.queueFrom) PANTHEON_CG_QueueServerCommandSeq(seq, s);
}

static void PD_ParseServerMessage(msg_t *msg)                            /* :1703 */
{
    int cmd;
    MSG_Bitstream(msg);
    (void)MSG_ReadLong(msg);                   /* reliableAcknowledge */
    for (;;) {
        if (msg->readcount > msg->cursize)
            Com_Error(ERR_DROP, "PANTHEON demo: read past end of message");
        cmd = MSG_ReadByte(msg);
        if (cmd == svc_EOF && MSG_LookaheadByte(msg) == svc_extension) {
            MSG_ReadByte(msg);
            cmd = MSG_ReadByte(msg);
            if (cmd == -1) cmd = svc_EOF;
        }
        if (cmd == svc_EOF) break;
        switch (cmd) {
        case svc_nop: break;
        case svc_serverCommand: PD_ServerCommand(msg); break;
        case svc_gamestate:     PD_ParseGamestate(msg); break;
        case svc_snapshot:      PD_ParseSnapshot(msg); break;
        default:
            /* svc_download / svc_voip carry no length prefix we could skip. A
             * demo containing one is reported, not guessed past. */
            Com_Error(ERR_DROP, "PANTHEON demo: unsupported server message %d", cmd);
        }
    }
}

qboolean PANTHEON_Demo_Open(const char *path)
{
    memset(&pd, 0, sizeof(pd));
    pd.queueFrom = 0x7fffffff;                 /* nothing queued until a pass starts */
    pd.f = fopen(path, "rb");
    return pd.f != NULL;
}

qboolean PANTHEON_Demo_ReadMessage(void)                                 /* cl_main.c:1063 */
{
    static byte data[MAX_MSGLEN];
    msg_t buf;
    int seq, len;

    if (!pd.f || fread(&seq, 4, 1, pd.f) != 1) return qfalse;
    pd.messageSeq = LittleLong(seq);
    if (fread(&len, 4, 1, pd.f) != 1) return qfalse;
    len = LittleLong(len);
    if (len == -1) return qfalse;
    if (len < 0 || len > MAX_MSGLEN)
        Com_Error(ERR_DROP, "PANTHEON demo: message length %d", len);
    MSG_Init(&buf, data, sizeof(data));
    if ((int)fread(buf.data, 1, len, pd.f) != len) return qfalse;
    buf.cursize = len;
    buf.readcount = 0;
    PD_ParseServerMessage(&buf);
    return qtrue;
}

/* cl_cgame.c CL_GetSnapshot, including its staleness check (:184). */
qboolean PANTHEON_Demo_Latest(snapshot_t *out, int *messageNum)
{
    int i, n;
    if (!pd.haveLatest) return qfalse;
    if (pd.parseNum - pd.latest.parseEntitiesNum >= PD_MAX_PARSE_ENTITIES) return qfalse;
    memset(out, 0, sizeof(*out));
    out->snapFlags = pd.latest.snapFlags;
    out->serverCommandSequence = pd.latest.serverCommandNum;
    out->ping = 0;
    out->serverTime = pd.latest.serverTime;
    out->messageNum = pd.latest.messageNum;
    memcpy(out->areamask, pd.latest.areamask, sizeof(out->areamask));
    out->ps = pd.latest.ps;
    n = pd.latest.numEntities;
    if (n > MAX_ENTITIES_IN_SNAPSHOT) n = MAX_ENTITIES_IN_SNAPSHOT;
    for (i = 0; i < n; i++) out->entities[i] = *PD_ENT(pd.latest.parseEntitiesNum, i);
    out->numEntities = n;
    *messageNum = pd.latest.messageNum;
    return qtrue;
}

/* From now on, commands after `seq` are cgame's to execute. */
void PANTHEON_Demo_QueueCommandsAfter(int seq) { pd.queueFrom = seq; }
int  PANTHEON_Demo_ClientNum(void)             { return pd.clientNum; }
const gameState_t *PANTHEON_Demo_GameState(void) { return &pd.gs; }
void PANTHEON_Demo_Close(void) { if (pd.f) fclose(pd.f); pd.f = NULL; }
```

Before building, open `wolfcamql-11.3-src/.../cgame/cg_public.h` and confirm `snapshot_t` has `messageNum` and `ping` (the composed-snapshot code already sets `messageNum`). Remove either line if the field is absent.

- [ ] **Step 3:** `build_cgame.sh`, after the `pantheon_cg_feed.c` line: `$CC $CGFLAGS $HOSTSTRICT $INC -c "$HERE/host/pantheon_demo_feed.c" -o "$OBJ/pantheon_demo_feed.o"` (where `HOSTSTRICT=-Werror=implicit-function-declaration`, applied to every `host/*.c` line in the script).
- [ ] **Step 4:** Build, exit 0. Render `v2.shot` exactly as Task 0 Step 2 did: the 66 MD5s must equal `docs/reference/2026-09-12-v2shot-reference.md5` (composed shots are unchanged by the reader).
- [ ] **Step 5:** Commit: `feat: PANTHEON reads .dm_73 with the engine's own decoder, gamestate kept current`

---

### Task 3: Gate G1 — two decoders agree, down to the entities

**Files:** `host/pantheon_frame.c`, `engine/parser/demo_parse.py`, create `creative_suite/tests/test_pantheon_demo_feed.py`

- [ ] **Step 1: `--dump-snapshots` in `pantheon_frame.c`**

Prototypes beside the other `PANTHEON_CG_*` declarations:

```c
qboolean PANTHEON_Demo_Open(const char *path);
qboolean PANTHEON_Demo_ReadMessage(void);
qboolean PANTHEON_Demo_Latest(snapshot_t *out, int *messageNum);
int      PANTHEON_Demo_ClientNum(void);
const gameState_t *PANTHEON_Demo_GameState(void);
void     PANTHEON_Demo_QueueCommandsAfter(int seq);
void     PANTHEON_Demo_Close(void);
static const char *s_dumpSnapshots;
static const char *s_demoPath;        /* --demo; parsed in Task 4 */
```

Argument: `else if (!strcmp(argv[i], "--dump-snapshots") && i + 1 < argc) s_dumpSnapshots = argv[++i];`

The `--map or --shot is required` check (line ~673) becomes `if (!cliMap[0] && !s_dumpModel && !s_dumpSnapshots && !s_demoPath)`.

Immediately after `Com_Init(cmdline);`:

```c
    if (s_dumpSnapshots) {
        /* G1. One S line per valid snapshot, one E line per player/missile
         * entity in it. No GL context: runs anywhere. */
        snapshot_t snap;
        int num, last = -1, k;
        if (!PANTHEON_Demo_Open(s_dumpSnapshots)) {
            fprintf(stderr, "PANTHEON: cannot open %s\n", s_dumpSnapshots);
            return 2;
        }
        while (PANTHEON_Demo_ReadMessage())
            if (PANTHEON_Demo_Latest(&snap, &num) && num != last) {
                printf("S\t%d\t%d\t%.1f\t%.1f\t%.1f\t%d\n", num, snap.serverTime,
                       snap.ps.origin[0], snap.ps.origin[1], snap.ps.origin[2],
                       snap.numEntities);
                for (k = 0; k < snap.numEntities; k++) {
                    const entityState_t *e = &snap.entities[k];
                    if (e->eType == ET_PLAYER || e->eType == ET_MISSILE)
                        printf("E\t%d\t%d\t%d\t%.1f\t%.1f\t%.1f\n", snap.serverTime,
                               e->number, e->eType, e->pos.trBase[0],
                               e->pos.trBase[1], e->pos.trBase[2]);
                }
                last = num;
            }
        PANTHEON_Demo_Close();
        return 0;
    }
```

- [ ] **Step 2: Optional entity capture in `DM73Parser`** (`engine/parser/demo_parse.py`). Add `capture_entities: bool = False` to `__init__`, store it, and initialise `self._entity_capture: dict[int, dict[int, tuple]] = {}`. At the point where the snapshot is appended (`snapshots.append(snap)`, ~line 894), add:

```python
        if self._capture_entities:
            # G1: the entity state AFTER this snapshot, keyed by server time.
            # Players and missiles only -- the entities the picture is made of.
            self._entity_capture[server_time] = {
                num: (st.get(_F_ETYPE), st.get(_F_POS_X), st.get(_F_POS_Y), st.get(_F_POS_Z))
                for num, st in self._entity_states.items()
                if st.get(_F_ETYPE) in (1, 3)
            }
```

and include `"entities_by_time": self._entity_capture` in `parse()`'s returned dict when capture is on. Confirm `_F_POS_Y`/`_F_POS_Z` exist beside `_F_POS_X`; use the file's actual names. Default off: run `E:/PersonalAI/venv/Scripts/python.exe -m pytest engine/parser/tests -q` and confirm no change.

Note on what "the entity state after this snapshot" means: `_entity_states` in DM73Parser is the accumulated delta state, which is the same quantity `PD_ENT` holds for the entities present in the snapshot. An entity DM73Parser still holds but the C snapshot omits (removed this frame) is a real disagreement; report it rather than filter it.

- [ ] **Step 3: The G1 test**

```python
# creative_suite/tests/test_pantheon_demo_feed.py
"""G1: the C demo reader and DM73Parser agree on every snapshot and on every
player and missile in it. Two independent decoders agreeing is the proof;
neither is trusted alone. Skips cleanly without the corpus or the exe."""
from __future__ import annotations

import sqlite3
import subprocess
from pathlib import Path

import pytest

from engine.pantheon import store as S
from engine.pantheon.pantheon_capture import host_exe

G1_HASHES = ("4db16c445bcaafce",)   # + two more at execution: another map, protocol 91


def _demo(prefix: str) -> Path:
    if not S.FRAGS_DB.exists():
        pytest.skip("no corpus catalogue")
    con = sqlite3.connect(f"file:{S.FRAGS_DB.as_posix()}?mode=ro", uri=True)
    row = con.execute("select path from demos where content_hash like ? limit 1",
                      (prefix + "%",)).fetchone()
    con.close()
    if not row or not Path(row[0]).exists():
        pytest.skip(f"demo {prefix} not on this machine")
    return Path(row[0])


def _c_dump(demo: Path):
    if not host_exe().exists():
        pytest.skip("pantheon_cgame.exe not built")
    out = subprocess.run([str(host_exe()), "--dump-snapshots", str(demo)],
                         capture_output=True, text=True, timeout=900, check=True).stdout
    snaps, ents = {}, {}
    for line in out.splitlines():
        f = line.split("\t")
        if f[0] == "S":
            snaps[int(f[2])] = tuple(map(float, f[3:6]))
        elif f[0] == "E":
            ents.setdefault(int(f[1]), {})[int(f[2])] = (int(f[3]), *map(float, f[4:7]))
    return snaps, ents


def _close(a, b, tol=0.5):
    return all(x is not None and abs(float(x) - float(y)) <= tol for x, y in zip(a, b))


@pytest.mark.parametrize("prefix", G1_HASHES)
def test_c_reader_agrees_with_dm73parser_on_every_snapshot(prefix):
    from engine.parser.demo_parse import DM73Parser
    demo = _demo(prefix)
    parser = DM73Parser(demo, capture_entities=True)
    py = parser.parse()
    c_snaps, c_ents = _c_dump(demo)
    # DM73Parser keeps snapshots whose delta base it never saw; the engine
    # (and so the C reader) drops them as invalid. Expected gaps: counted,
    # bounded, reported -- not hidden.
    expected_gaps = parser._missing_delta_refs

    bad, missing = [], []
    for s in py["snapshots"]:
        t = int(s["server_time_ms"])
        if t not in c_snaps:
            missing.append(t)
            continue
        if not _close((s["origin_x"], s["origin_y"], s["origin_z"]), c_snaps[t]):
            bad.append((t, "ps.origin", c_snaps[t]))
        want = py["entities_by_time"].get(t, {})
        got = c_ents.get(t, {})
        for num in set(want) | set(got):
            if num not in got or num not in want:
                bad.append((t, "entity presence", num, num in want, num in got))
            elif want[num][0] != got[num][0] or not _close(want[num][1:], got[num][1:]):
                bad.append((t, "entity", num, want[num], got[num]))
    assert len(missing) <= expected_gaps, (len(missing), expected_gaps, missing[:10])
    assert not bad, bad[:15]
```

- [ ] **Step 4:** Build and run. **A failure is a decoder bug: stop and fix it before Task 4** — every later gate stands on this one. Then add two more hashes (another map; a protocol-91 demo) and rerun.
- [ ] **Step 4b: Every field, not a sample.** Extend the dump and the comparison to the whole interface cgame consumes:
  - **Generate** `host/pantheon_netfields.inc` from `engine/parser/netfields_generated.py` (which is itself generated from `msg.c` and test-guarded): one row per field, `{ "pos.trBase[0]", offsetof(entityState_t, pos.trBase[0]), <float|int> }`, for the protocol-73 and -91 entity and playerstate tables. A small generator `engine/parser/gen_netfields_c.py`, and a test that the `.inc` is current (same pattern as `netfields_generated`).
  - `--dump-snapshots` prints, per snapshot: `S` (messageNum, serverTime, snapFlags, serverCommandSequence, numEntities, parseEntitiesNum), `P` (every playerstate field by name), `E` (every entity field by name, for **every** entity, not only players and missiles), `C` (an MD5 of the reader's configstring set, and the indices changed since the previous snapshot), `Q` (each reliable command as it is sequenced: seq, text), and once, `G` (clientNum, checksumFeed, protocol, gamestate MD5).
  - `DM73Parser(capture_entities=True)` also records the raw gamestate strings and every server command. The **test** applies `cs`/`bcs0/1/2` to that gamestate in Python — an implementation independent of the C one — and compares the configstring MD5 at every snapshot, the command order, and every named field.

- [ ] **Step 4c: Wrap the rings on purpose.**
  - **Parse entities:** the G1 run must report at least one snapshot whose entities straddle the ring boundary (`parseEntitiesNum % 8192 + numEntities > 8192`) and compare it field by field. Real demos pass 8192 parse entities within a few hundred snapshots; assert the dump's maximum `parseEntitiesNum` exceeds `3 * 8192`, so a short fixture cannot pass G1 without exercising the mask.
  - **Reliable commands:** a C unit test, `engine/pantheon_renderer/tests/test_rings.c`, linked with `pantheon_cg_feed.c` and built by `build_cgame.sh --tests`: queue sequences 1..130; for every seq assert `GetServerCommand(seq)` is true for the last 64 and false (aged out) for everything older, and check the slot owner at 63, 64, 65 and 127, 128, 129. Run it from pytest (`test_pantheon_demo_feed.py::test_command_ring_wraps_like_wolfcam`).
  - **Parse ring:** the same test program compiles `pantheon_demo_feed.c` with `-DPANTHEON_TEST`, which exposes `PD_EntSlot(base, i)`; assert slots for (8191, 0), (8191, 1), (8192, 0), (8193, 0) are 8191, 0, 0, 1.

- [ ] **Step 5:** Commit: `test: G1 -- the C reader agrees with DM73Parser, entities included`

---

### Task 4: Render demo passes from the recorder's eyes — then stop H1

**Files:** `host/pantheon_cg_run.c`, `host/pantheon_frame.c`

- [ ] **Step 1: `PANTHEON_CG_Init` takes the recorder, a message number and a command sequence** (as `cl_cgame.c:1473`: `serverMessageSequence`, `lastExecutedServerCommand`, `clientNum`, `demoplaying`)

```c
void PANTHEON_CG_Init(int clientNum, int serverMessageNum, int serverCommandSequence)
{
    if (!PANTHEON_CG_Ready())
        Com_Error(ERR_FATAL, "PANTHEON: CG_Init before a gamestate and two "
                             "snapshots were fed");
    dllEntry(PANTHEON_CG_Syscall);
    /* Commands at or below serverCommandSequence are already reflected in the
     * gamestate cgame is handed (the reader applied them); cgame executes
     * only the ones after. */
    vmMain(CG_INIT, serverMessageNum, serverCommandSequence, clientNum, qtrue, 0, 0, 0, 0, 0, 0, 0, 0);
    PANTHEON_CG_RegisterAllWeapons();
}
```

Update the prototype at `pantheon_frame.c:50` to `void PANTHEON_CG_Init(int clientNum, int serverMessageNum, int serverCommandSequence);` and the two existing call sites to `PANTHEON_CG_Init(0, 1, 0);` (composed shots number their snapshots from 1). Every call to `PANTHEON_CG_Frame` keeps its two arguments `(t, firstFrame)`.

- [ ] **Step 2: Arguments**

```c
#define PA_MAX_WINDOWS 64
#define PREROLL_MS     1500
typedef struct { char clip[MAX_QPATH]; int start, end; char outdir[MAX_OSPATH]; int frames; } paWindow_t;
static paWindow_t  s_windows[PA_MAX_WINDOWS];   /* s_demoPath is declared in Task 3 */
static int         s_numWindows;
static int         s_fps = 60;
```

```c
        else if (!strcmp(argv[i], "--demo") && i + 1 < argc)
            s_demoPath = argv[++i];
        else if (!strcmp(argv[i], "--fps") && i + 1 < argc)
            s_fps = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--window") && i + 4 < argc) {
            paWindow_t *w;
            if (s_numWindows >= PA_MAX_WINDOWS) ShotError("more than %d windows", PA_MAX_WINDOWS);
            w = &s_windows[s_numWindows++];
            Q_strncpyz(w->clip, argv[++i], sizeof(w->clip));
            w->start = atoi(argv[++i]);
            w->end   = atoi(argv[++i]);
            Q_strncpyz(w->outdir, argv[++i], sizeof(w->outdir));
            if (w->end <= w->start) ShotError("window %s ends before it starts", w->clip);
        }
```

Validation after parsing: `--demo` excludes `--shot`; windows sorted by `start` (else `ShotError`); `s_fps` in 1..240.

**Frame count must equal wolfcam's** (`frames_expected`, `wolfcam_capture.py:394`, which rounds): per window `n = (int)((end - start) * s_fps / 1000.0 + 0.5)`; frame `k` at `t_k = start + (int)((k * 1000.0) / s_fps + 0.5)`.

- [ ] **Step 3: Passes, and the registration window**

Windows whose pre-roll would start before the previous window ends are **merged into one pass**: a pass renders continuously from `firstStart − PREROLL_MS` to `lastEnd`, and each frame time is written into every window that contains it. Separate passes need `pass[n].start − PREROLL_MS ≥ pass[n−1].end`.

Before any GL registration closes:

1. **Pre-scan** (a first `PANTHEON_Demo_Open` → read all → `Close`): record the first and last valid snapshot server times, and the value of `CS_LEVEL_START_TIME` in the gamestate at the first snapshot. Call `PANTHEON_CG_SetDemoInfo(levelStart, lastTime, firstTime, lastTime, mapname)` — after any `PANTHEON_CG_Reset`, never before (Reset no longer clears it; it is set once per demo).
2. **Reopen**, read until the latest snapshot's `serverTime ≥ pass0.start − PREROLL_MS`.
3. The map comes from the reader's `CS_SERVERINFO` `mapname`; cgame loads it (`CG_R_LOADWORLDMAP`) inside `CG_Init`, which must therefore run **before** `re->EndRegistration()` — the existing composed-shot ordering (`pantheon_frame.c:853`). Restructure `main` so the demo path reaches this point before `EndRegistration`.
4. `PANTHEON_CG_Reset(); PANTHEON_CG_SetGameState(PANTHEON_Demo_GameState());` push the current snapshot (its `serverCommandSequence` is `seq0`, its `messageNum` is `msg0`); **immediately** `PANTHEON_Demo_QueueCommandsAfter(seq0)` — before reading on, or commands that arrive with the next snapshot are applied to the reader's gamestate but never queued, and cgame loses them with no error; read to the next valid snapshot and push it; `PANTHEON_CG_SetDemoInfo(...)`; `PANTHEON_CG_Init(PANTHEON_Demo_ClientNum(), msg0, seq0);` then the existing drains. At the end of every pass call `PANTHEON_Demo_QueueCommandsAfter(0x7fffffff)` so nothing is queued while reading forward to the next pass.

Later passes: read forward to the pass's pre-roll, `PANTHEON_CG_Shutdown()`, then step 4 again (without the EndRegistration constraint — the world is resident; `CG_R_LOADWORLDMAP` already answers a same-map repeat with nothing).

Feeding during a pass:

```c
/* Push snapshots until the newest one is PAST t_ms, so cgame always has a
 * nextSnap beyond the frame being drawn. qfalse at end of demo. */
static qboolean PANTHEON_DemoFeedTo(int t_ms, int *pushed)
{
    snapshot_t snap;
    int num;
    for (;;) {
        if (PANTHEON_Demo_Latest(&snap, &num) && num != *pushed) {
            PANTHEON_CG_PushSnapshot(num, &snap);
            *pushed = num;
            if (snap.serverTime > t_ms) return qtrue;
        }
        if (!PANTHEON_Demo_ReadMessage()) return qfalse;
    }
}
```

Pre-roll frames (`t` from pass start to `firstStart`, step `1000 / s_fps`): feed, `BeginFrame`, clear, `PANTHEON_CG_Frame(t, qfalse)`, `EndFrame`, **no readback** — they only bring trails, marks and local entities to their state at the window start.

Capture frames: feed, render through the existing path (FBO checks, blur, depth all apply), write `outdir/<clip>_<k:06d>.tga` for each window containing `t_k`; count `w->frames`. If the demo ends early: stop the pass, keep what exists.

At the end print one line per window: `PANTHEON: window <clip> frames=<n> expected=<m> start=<s> end=<e>`.

- [ ] **Step 4: Two adjacent windows test** — windows 1 s apart in the proof demo must both be complete (`frames == expected`) and the log must show one pass.

- [ ] **Step 5: Smoke render and stop H1**

`$DEMO` from `test_pantheon_demo_feed._demo("4db16c445bcaafce")`; staging `$S=$PWD/output/demo_v2/_wolfcam_staging` (main checkout data root):
```bash
engine/pantheon_renderer/build/pantheon_cgame.exe --basepath "$S" --game wolfcam-ql --cgame --width 1280 --height 720 --fps 60 --demo "$DEMO" --window proof 1197225 1200725 /tmp/pc_proof
```
Expected: exit 0; `frames=210 expected=210`; 210 TGAs at 1280×720; the log shows `wolfcam-ql/zzz_*.pk3` loaded. Save frames 0, 105, 209 as PNG to `docs/visual-record/<date>/pantheon_demo_window_*.png` (VIS-1).

**STOP H1.** Send the three PNGs to the user with the question: *"Is this the first-person capture you'd expect for this moment — view, HUD, weapon, effects?"* Do not start Task 5 without a yes.

- [ ] **Step 6:** Commit: `feat: PANTHEON renders demo passes from the recorder's eyes`

---

### Task 5: Gate G2 harness — frames by server time — then stop H2

**Files:** create `engine/pantheon/capture_parity.py`; classify it `BACKEND_ALLOWED` in `test_pantheon_headless_boundary.py`

- [ ] **Step 1: Harness**

```python
# engine/pantheon/capture_parity.py
"""G2 and G3: wolfcam and PANTHEON at the same SERVER TIMES, side by side.

A frame is chosen by server time, never by a fraction of the file: wolfcam's
AVIs are retimed and can differ in length. Frame k of a window is the frame
rendered at start + k*1000/fps in both backends (both round the same way).
The verdict is a human's; this makes the question impossible to dodge.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from engine.pantheon import review_sheet, store as S

FFMPEG = S.PROJECT_ROOT / "creative_suite" / "tools" / "ffmpeg" / "ffmpeg.exe"


def frame_index(t_ms: int, start_ms: int, fps: int) -> int:
    return int(round((t_ms - start_ms) * fps / 1000.0))


def frame_at(avi: Path, index: int, dest: Path) -> Path:
    subprocess.run([str(FFMPEG), "-y", "-loglevel", "error", "-i", str(avi),
                    "-vf", f"select=eq(n\\,{index})", "-frames:v", "1", str(dest)],
                   check=True)
    return dest


def parity_sheet(window: dict, fps: int, wolfcam_avi: Path, pantheon_avi: Path,
                 work: Path) -> dict:
    s, e = int(window["start_ms"]), int(window["end_ms"])
    times = (s, (s + e) // 2, e - int(1000 / fps))
    work.mkdir(parents=True, exist_ok=True)
    legs = {}
    for t in times:
        i = frame_index(t, s, fps)
        legs[f"wolfcam t={t}"] = frame_at(wolfcam_avi, i, work / f"w_{t}.png")
        legs[f"pantheon t={t}"] = frame_at(pantheon_avi, i, work / f"p_{t}.png")
    return review_sheet.compare(
        f"parity_{window['clip_name']}",
        "Same moment, same eyes, same HUD and effects?", "renderer", legs,
        note="G2. PASS only if nothing is missing or wrong in PANTHEON's frames.")
```

- [ ] **Step 2 (after Task 7): Run on 10 frags** the user picks (RL, rail, LG, a multi-kill, three maps). Capture each window with `PANTHEON_CAPTURE_BACKEND=wolfcam` then `=pantheon` through `capture_demo`, **with the same profile both times**. Before building a sheet, require `frames_written == frames_expected` for **both** captures — otherwise a frame index is not a server time; report the clip instead of sheeting it. Add one extra clip captured with the public-export profile (`master_profile.profile_for_intent(PUBLIC_INTENT)`) and check every frame for opponent names. Save the sheets to `docs/visual-record/<date>/`.

**STOP H2.** Send the ten sheets; record each verdict in `docs/reference/<date>-capture-parity.md` as `clip | verdict | note`.

- [ ] **Step 2b: Machine state checks, then a classified image diff.**
  - The host gains `--frame-state <path>`: one JSON line per captured frame, written by `pantheon_cg_probe.c` (compiled with `cg_local.h`, so it reads cgame's own state): `{k, serverTime, snapNum, vieworg, viewangles, fov_x, fov_y, clientNum, weapon, legsAnim, torsoAnim, entities: {num: origin}, cs_md5, scores, round, width, height}`.
  - `capture_parity.check_state(frame_state, demo)` compares each line with demo truth from `DM73Parser` at the same server time (interpolated between the bracketing snapshots, as cgame does): camera origin within 1 u, angles within 0.5°, FOV exact, weapon/animation exact, entity origins within 1 u, `cs_md5` equal to the Python-applied configstrings, viewport exact. A failure assigns `FAIL_GAME_STATE`, `FAIL_CAMERA` or `FAIL_TIMING` automatically, and the frame never reaches a sheet.
  - Frames that pass get an image diff against wolfcam at the same index: mean absolute difference, fraction of pixels differing by more than 8, and the bounding box of the difference. Below 0.5 % of pixels: `PASS_EQUAL` automatically. Anything else is `UNKNOWN` until the user classifies it at H2 as `PASS_EXPECTED_RENDERER_DIFFERENCE`, `PASS_PANTHEON_FIX` or `FAIL_RENDERING`, with a one-line reason.
  - Verdicts live in `docs/reference/<date>-capture-parity.md` as `clip | frame | class | reason`. **Any `FAIL_*` or `UNKNOWN` blocks Task 11.**

- [ ] **Step 3:** Commit: `feat: G2 parity sheets at matching server times`

---

### Task 6: Sound, from cgame's own calls

**Files:** create `host/pantheon_sound_log.c`; modify `host/pantheon_cg_syscall.c`, `host/pantheon_cg_run.c`, `host/pantheon_cg_feed.c`, `host/pantheon_frame.c`, `build_cgame.sh`

- [ ] **Step 1: The logger**

```c
/*
 * THE SOUNDS CGAME ASKED FOR, WITH WHERE AND WHEN.
 *
 * Plays nothing: engine/pantheon/sound_mix.py turns the log into a WAV, so the
 * audio is a pure function of the log and the pak samples. Tab-separated:
 *   R <sfx> <name>                               registration (once per name)
 *   S <time> <entity> <channel> <sfx> <x> <y> <z> positional start
 *   L <time> <sfx> <channel>                     local (announcer, UI)
 *   E <time> <x> <y> <z> <pitch> <yaw> <roll>    listener, per captured frame
 * Times are server ms. Passes never overlap in time (Task 4), so an event
 * belongs to every window whose range contains its time and to no other.
 */
#include "../wolfcamql-11.3-src/wolfcamql-src/code/qcommon/q_shared.h"
#include <stdio.h>
#include <string.h>

#define PS_MAX_SFX 4096
static FILE *s_log;
static char  s_names[PS_MAX_SFX][MAX_QPATH];
static int   s_numSfx, s_time;

qboolean PANTHEON_CG_EntityOrigin(int entityNum, vec3_t out);   /* pantheon_cg_feed.c */

void PANTHEON_Sound_Open(const char *path)  { s_log = fopen(path, "w"); }
void PANTHEON_Sound_Close(void)             { if (s_log) fclose(s_log); s_log = NULL; }
void PANTHEON_Sound_SetTime(int t)          { s_time = t; }

/* A name keeps its handle for the life of the process: every pass's CG_Init
 * re-registers every sound, and issuing new handles would exhaust the table
 * by the third window. Handle 0 is "no sound" to cgame, so handles start at 1. */
int PANTHEON_Sound_Register(const char *name)
{
    int i;
    for (i = 1; i <= s_numSfx; i++)
        if (!Q_stricmp(s_names[i], name)) return i;
    if (s_numSfx + 1 >= PS_MAX_SFX) return 0;
    s_numSfx++;
    Q_strncpyz(s_names[s_numSfx], name, MAX_QPATH);
    if (s_log) fprintf(s_log, "R\t%d\t%s\n", s_numSfx, name);
    return s_numSfx;
}

void PANTHEON_Sound_Start(const float *origin, int ent, int chan, int sfx)
{
    vec3_t o;
    if (!s_log || sfx <= 0) return;
    /* An entity-attached sound (origin NULL) -- another player's shot, a hit
     * -- is placed where that entity is in the snapshot now, so it is not
     * mixed at full volume from inside the listener's head. */
    if (!origin && PANTHEON_CG_EntityOrigin(ent, o)) origin = o;
    if (origin) fprintf(s_log, "S\t%d\t%d\t%d\t%d\t%.1f\t%.1f\t%.1f\n",
                        s_time, ent, chan, sfx, origin[0], origin[1], origin[2]);
    else        fprintf(s_log, "S\t%d\t%d\t%d\t%d\t\t\t\n", s_time, ent, chan, sfx);
}

void PANTHEON_Sound_Local(int sfx, int chan)
{
    if (s_log && sfx > 0) fprintf(s_log, "L\t%d\t%d\t%d\n", s_time, sfx, chan);
}

void PANTHEON_Sound_Listener(const float *o, const float *a)
{
    if (s_log) fprintf(s_log, "E\t%d\t%.1f\t%.1f\t%.1f\t%.2f\t%.2f\t%.2f\n",
                       s_time, o[0], o[1], o[2], a[0], a[1], a[2]);
}
```

`pantheon_cg_feed.c`:

```c
/* Where an entity is in the newest snapshot fed; the recorder is the
 * playerstate. Used to place entity-attached sounds. */
qboolean PANTHEON_CG_EntityOrigin(int entityNum, vec3_t out)
{
    const snapshot_t *s;
    int i;
    if (cg_latest <= 0) return qfalse;
    s = &cg_ring[cg_latest % PANTHEON_SNAP_RING];
    if (entityNum == s->ps.clientNum) { VectorCopy(s->ps.origin, out); return qtrue; }
    for (i = 0; i < s->numEntities; i++)
        if (s->entities[i].number == entityNum) { VectorCopy(s->entities[i].pos.trBase, out); return qtrue; }
    return qfalse;
}
```

- [ ] **Step 2: Syscalls** (`pantheon_cg_syscall.c`, with prototypes for all four logger functions at the top):

```c
    case CG_S_REGISTERSOUND:    return PANTHEON_Sound_Register(VMA(1));
    case CG_S_STARTSOUND:       PANTHEON_Sound_Start(VMA(1), args[2], args[3], args[4]); return 0;
    case CG_S_STARTLOCALSOUND:  PANTHEON_Sound_Local(args[1], args[2]); return 0;
```

Remove those three from the counted-and-dropped group. `PANTHEON_CG_Frame` calls `PANTHEON_Sound_SetTime(serverTime)` before `vmMain` (prototype in `pantheon_cg_run.c`).

- [ ] **Step 3:** `--sound-log <path>`: open **before** the first `PANTHEON_CG_Init` (so every `R` line is logged), close at exit. After each captured frame, `PANTHEON_Sound_Listener(snap.ps.origin, snap.ps.viewangles)` from the newest pushed snapshot.
- [ ] **Step 4:** Build; rerun the Task 4 smoke with `--sound-log /tmp/pc_proof/sound.tsv`. Expected: `R` lines each unique; `S` lines for the rocket fire and explosion near the proof's times; 210 `E` lines. Run a 3-window, 3-pass render: the `R` count does not grow after the first pass.
- [ ] **Step 5:** Commit: `feat: PANTHEON logs every sound cgame asks for, placed where it happens`

---

### Task 7: The backend, the mixer and the switch (gate G4)

**Files:** create `engine/pantheon/sound_mix.py`; complete `engine/pantheon/pantheon_capture.py`; modify `creative_suite/engine/wolfcam_capture.py`, `engine/pantheon/backends.py`, `host/pantheon_frame.c` (command-line buffer), `test_render_permit.py`, `test_pantheon_headless_boundary.py`; tests in `test_pantheon_capture.py`

- [ ] **Step 1: Extract the completeness rules** so both backends compute them identically. In `wolfcam_capture.py`, move the tail of `capture_demo` into:

```python
def completeness(windows: list[dict], avis: dict, frames_written: int,
                 fps: int) -> dict:
    """ok / under_sampled / frames_expected, one definition for every backend."""
    want = frames_expected(windows, fps)
    return {"ok": len(avis) == len(windows),
            "frames_expected": want,
            "under_sampled": bool(avis) and want > 0 and frames_written < want * COMPLETE_ENOUGH,
            "error": None if len(avis) == len(windows)
            else f"missing {len(windows) - len(avis)} AVIs"}
```

and have `capture_demo` use it (behaviour unchanged — run the existing capture tests to prove it).

- [ ] **Step 2: Failing tests**

```python
# append to creative_suite/tests/test_pantheon_capture.py
import os

import numpy as np
import pytest


@pytest.fixture(autouse=True)
def _permit(monkeypatch):
    from engine.pantheon import render_permit
    monkeypatch.setattr(render_permit, "require", lambda *a, **k: None)


def _wolfcam_mock_result(tmp_path, monkeypatch, windows):
    from creative_suite.engine import wolfcam_capture as W
    monkeypatch.setenv("CS_CAPTURE_MOCK", "1")
    monkeypatch.delenv("PANTHEON_CAPTURE_BACKEND", raising=False)
    (tmp_path / "wolfcam-ql" / "videos").mkdir(parents=True)
    (tmp_path / "wolfcam-ql" / "demos").mkdir(parents=True)
    return W.capture_demo("d.dm_73", windows, staging=tmp_path)


def _fake_host(monkeypatch, frames_by_clip):
    from engine.pantheon import pantheon_capture as PC
    text = "".join(f"PANTHEON: window {c} frames={n} expected=0 start=0 end=0\n"
                   for c, n in frames_by_clip.items())
    monkeypatch.setattr(PC, "_run_host", lambda argv, timeout: (0, text))
    monkeypatch.setattr(PC, "_encode", lambda frames_dir, clip, wav, fps, dest: dest.write_bytes(b"x") or dest)
    monkeypatch.setattr(PC, "_mix", lambda log, windows, out_dir, staging: {c: None for c in frames_by_clip})


def test_the_default_backend_is_still_wolfcam(monkeypatch):
    from creative_suite.engine import wolfcam_capture as W
    monkeypatch.delenv("PANTHEON_CAPTURE_BACKEND", raising=False)
    assert W.capture_backend() == "wolfcam"


def test_an_unknown_backend_is_refused(monkeypatch):
    from creative_suite.engine import wolfcam_capture as W
    monkeypatch.setenv("PANTHEON_CAPTURE_BACKEND", "blender")
    with pytest.raises(ValueError):
        W.capture_backend()


def test_pantheon_returns_the_same_keys_and_types_as_wolfcam(tmp_path, monkeypatch):
    """Keys and types come from capture_demo itself, not from a list in this test."""
    from engine.pantheon import pantheon_capture as PC
    windows = [{"clip_name": "c1", "start_ms": 1000, "end_ms": 2000}]
    ref = _wolfcam_mock_result(tmp_path / "w", monkeypatch, windows)
    _fake_host(monkeypatch, {"c1": 60})
    got = PC.capture(tmp_path / "d.dm_73", windows, out_dir=tmp_path / "p", fps=60)
    assert set(got) == set(ref)
    for k in ref:
        if ref[k] is not None and got[k] is not None:
            assert type(got[k]) is type(ref[k]), (k, type(ref[k]), type(got[k]))


@pytest.mark.parametrize("n,under", [(60, False), (30, True)])
def test_completeness_values(tmp_path, monkeypatch, n, under):
    """Concrete values, so a wrong shared rule fails here too."""
    from engine.pantheon import pantheon_capture as PC
    windows = [{"clip_name": "c1", "start_ms": 1000, "end_ms": 2000}]
    _fake_host(monkeypatch, {"c1": n})
    got = PC.capture(tmp_path / "d.dm_73", windows, out_dir=tmp_path / f"p{n}", fps=60)
    assert got["frames_expected"] == 60
    assert got["frames_written"] == n
    assert got["under_sampled"] is under
    assert got["ok"] is True


def test_no_profile_means_the_batch_profile_not_the_stock_view():
    """profile=None resolves exactly as profile_fps does: to PROFILE_NAME."""
    from creative_suite.engine import master_profile as MP
    from engine.pantheon import pantheon_capture as PC
    assert PC.profile_sets(None) == PC.profile_sets(MP.PROFILE_NAME)
    assert PC.profile_sets(None), "the batch profile carries the de-gaming cvars"


def test_the_public_profile_reaches_the_host(monkeypatch, tmp_path):
    """The public profile is what keeps opponent names out of clips; it must
    arrive as --set pairs on the host's command line, every cvar of it."""
    from creative_suite.engine import master_profile as MP
    from engine.pantheon import pantheon_capture as PC
    name = MP.profile_for_intent(MP.PUBLIC_INTENT)
    seen = {}
    monkeypatch.setattr(PC, "_run_host", lambda argv, timeout: (seen.setdefault("argv", argv), (0, ""))[1])
    monkeypatch.setattr(PC, "_mix", lambda *a: {})
    PC.capture(tmp_path / "d.dm_73", [{"clip_name": "c", "start_ms": 0, "end_ms": 100}],
               out_dir=tmp_path, fps=60, profile=name)
    argv = seen["argv"]
    for k, v in MP.PROFILES[name].items():
        i = argv.index(str(k))
        assert argv[i - 1] == "--set" and argv[i + 1] == str(v), k


def test_an_unknown_profile_is_refused():
    from engine.pantheon import pantheon_capture as PC
    with pytest.raises(ValueError):
        PC.profile_sets("NO_SUCH_PROFILE")


def test_the_mix_places_a_sample_at_its_logged_time(tmp_path):
    from engine.pantheon import sound_mix as M
    sr = 48000
    click = np.zeros(480, dtype=np.float32); click[0] = 1.0
    log = tmp_path / "s.tsv"
    log.write_text("R\t1\tsound/test.wav\nE\t1000\t0\t0\t0\t0\t0\t0\nL\t1250\t1\t0\n",
                   encoding="utf-8")
    wav = M.mix(log, start_ms=1000, end_ms=2000, samples={"sound/test.wav": click}, sr=sr)
    assert abs(int(np.argmax(np.abs(wav[:, 0]) > 0.5)) - int(0.250 * sr)) <= 1


def test_a_distant_sound_is_quieter_than_a_near_one(tmp_path):
    from engine.pantheon import sound_mix as M
    sr = 48000
    tone = np.ones(480, dtype=np.float32) * 0.5
    log = tmp_path / "s.tsv"
    log.write_text("R\t1\ta.wav\nE\t0\t0\t0\t0\t0\t0\t0\n"
                   "S\t100\t5\t0\t1\t50\t0\t0\nS\t500\t6\t0\t1\t900\t0\t0\n", encoding="utf-8")
    wav = M.mix(log, start_ms=0, end_ms=1000, samples={"a.wav": tone}, sr=sr)
    near = np.abs(wav[int(0.1 * sr):int(0.1 * sr) + 400]).max()
    far = np.abs(wav[int(0.5 * sr):int(0.5 * sr) + 400]).max()
    assert far < near
```

- [ ] **Step 3: The mixer** — `engine/pantheon/sound_mix.py`

```python
"""Sound log + samples -> stereo float32 PCM for one capture window.

A pure function of its inputs. Positional sounds use Q3's distance
attenuation (snd_dma.c: SOUND_FULLVOLUME 80, SOUND_ATTENUATE 0.0008) and a pan
from the listener's right vector at the moment the sound starts. Looping
sounds are not mixed in v1.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np

SOUND_FULLVOLUME = 80.0
SOUND_ATTENUATE = 0.0008


def _right(angles) -> np.ndarray:
    yaw = math.radians(angles[1])
    return np.array([math.sin(yaw), -math.cos(yaw), 0.0])


def _gains(origin, listener) -> tuple[float, float]:
    if origin is None or listener is None:
        return 1.0, 1.0
    lo, la = listener
    d = np.asarray(origin, float) - np.asarray(lo, float)
    n = float(np.linalg.norm(d))
    vol = max(0.0, 1.0 - max(0.0, n - SOUND_FULLVOLUME) * SOUND_ATTENUATE)
    pan = float(np.dot(d / n, _right(la))) if n > 1e-3 else 0.0
    return vol * (1.0 - max(0.0, pan) * 0.5), vol * (1.0 + min(0.0, pan) * 0.5)


def parse(log: Path):
    names, events, listeners = {}, [], []
    for line in Path(log).read_text(encoding="utf-8").splitlines():
        f = line.split("\t")
        if f[0] == "R":
            names[int(f[1])] = f[2]
        elif f[0] == "S":
            org = None if f[5] == "" else tuple(float(x) for x in f[5:8])
            events.append((int(f[1]), int(f[4]), org))
        elif f[0] == "L":
            events.append((int(f[1]), int(f[2]), None))
        elif f[0] == "E":
            listeners.append((int(f[1]), tuple(map(float, f[2:5])), tuple(map(float, f[5:8]))))
    listeners.sort()
    return names, events, listeners


def mix(log: Path, *, start_ms: int, end_ms: int,
        samples: dict[str, np.ndarray], sr: int = 48000) -> np.ndarray:
    names, events, listeners = parse(log)
    out = np.zeros((int((end_ms - start_ms) * sr / 1000), 2), dtype=np.float32)
    for t, sfx, org in events:
        if not (start_ms <= t < end_ms):
            continue
        pcm = samples.get(names.get(sfx, ""))
        if pcm is None:
            continue
        before = [l for l in listeners if l[0] <= t]
        lst = before[-1] if before else (listeners[0] if listeners else None)
        gl, gr = _gains(org, (lst[1], lst[2]) if lst else None)
        i = int((t - start_ms) * sr / 1000)
        n = min(len(pcm), len(out) - i)
        if n > 0:
            out[i:i + n, 0] += pcm[:n] * gl
            out[i:i + n, 1] += pcm[:n] * gr
    return np.clip(out, -1.0, 1.0)
```

- [ ] **Step 4: The backend** — complete `engine/pantheon/pantheon_capture.py` (below `host_exe`):

```python
import re
import shutil
import subprocess
import tempfile
import time
import wave
import zipfile

import numpy as np

from engine.pantheon import sound_mix

FFMPEG = S.PROJECT_ROOT / "creative_suite" / "tools" / "ffmpeg" / "ffmpeg.exe"
_WINDOW = re.compile(r"PANTHEON: window (\S+) frames=(\d+)")
PER_FRAME_S = 0.08           # measured 2026-09-12 (66 frames ~4-6 s incl. load)
LAUNCH_S = 30.0
SR = 48000


def _run_host(argv: list[str], timeout: float) -> tuple[int, str]:
    from creative_suite.engine.capture_guard import quiet_startup_info
    p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout,
                       cwd=str(host_exe().parent), startupinfo=quiet_startup_info())
    return p.returncode, p.stdout + p.stderr


def _encode(frames_dir: Path, clip: str, wav: Path | None, fps: int, dest: Path) -> Path:
    """Lossless AVI (UT Video) + PCM, so nothing downstream sees a new loss."""
    cmd = [str(FFMPEG), "-y", "-loglevel", "error", "-framerate", str(fps),
           "-i", str(frames_dir / f"{clip}_%06d.tga")]
    if wav:
        cmd += ["-i", str(wav), "-c:a", "pcm_s16le", "-shortest"]
    cmd += ["-c:v", "utvideo", "-pix_fmt", "rgb24", str(dest)]
    subprocess.run(cmd, check=True)
    return dest


def _paks(staging: Path) -> list[Path]:
    """wolfcam-ql first, then baseq3; within each, reverse alphabetical so a
    zzz_ override wins, as the engine's own search order does. Read-only (ENG-4)."""
    out = []
    for game in ("wolfcam-ql", "baseq3"):
        out += sorted((staging / game).glob("*.pk3"), reverse=True)
    return out


def _decode(raw: bytes) -> np.ndarray:
    p = subprocess.run([str(FFMPEG), "-loglevel", "error", "-i", "-", "-f", "f32le",
                        "-ac", "1", "-ar", str(SR), "-"], input=raw,
                       capture_output=True, check=True)
    return np.frombuffer(p.stdout, dtype=np.float32).copy()


def _sample(name: str, paks: list[Path], cache: Path) -> np.ndarray | None:
    key = cache / (name.replace("/", "__") + ".f32")
    if key.exists():
        return np.fromfile(key, dtype=np.float32)
    stem = name.rsplit(".", 1)[0]
    for cand in (name, stem + ".wav", stem + ".ogg"):
        for pak in paks:
            with zipfile.ZipFile(pak) as z:
                try:
                    raw = z.read(cand)
                except KeyError:
                    continue
            pcm = _decode(raw)
            cache.mkdir(parents=True, exist_ok=True)
            pcm.tofile(key)
            return pcm
    return None


def _write_wav(path: Path, stereo: np.ndarray) -> Path:
    pcm = (np.clip(stereo, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return path


def _mix(log: Path, windows: list[dict], out_dir: Path, staging: Path) -> dict[str, Path | None]:
    if not log.exists():
        return {w["clip_name"]: None for w in windows}
    names, events, _ = sound_mix.parse(log)
    paks, cache = _paks(staging), S.store_root() / "sfx_cache"
    samples = {n: pcm for n in set(names.values())
               if (pcm := _sample(n, paks, cache)) is not None}
    result = {}
    for w in windows:
        s, e = int(w["start_ms"]), int(w["end_ms"])
        if not any(s <= t < e for t, _, _ in events):
            result[w["clip_name"]] = None
            continue
        stereo = sound_mix.mix(log, start_ms=s, end_ms=e, samples=samples, sr=SR)
        result[w["clip_name"]] = _write_wav(out_dir / f"{w['clip_name']}.wav", stereo)
    return result


def profile_sets(profile: str | None) -> list[str]:
    """The profile wolfcam would run, as host --set pairs.

    profile=None is NOT the stock view: wolfcam resolves it to the batch
    profile (master_profile.PROFILE_NAME), exactly as profile_fps does. The
    public-export profile is what keeps opponent names out of clips, so a
    profile dropped silently is a disclosure bug, not a style choice.
    """
    from creative_suite.engine import master_profile as _mp
    name = profile or _mp.PROFILE_NAME
    cv = _mp.PROFILES.get(name)
    if not isinstance(cv, dict):
        raise ValueError(f"unknown capture profile {name!r}")
    out: list[str] = []
    for k, v in cv.items():
        out += ["--set", str(k), str(v)]
    return out


def resolve_demo(path: Path) -> Path:
    """safe_demo may arrive without its extension (wolfcam_capture.py:510)."""
    return path if path.exists() else path.with_suffix(".dm_73")


def capture(demo: Path, windows: list[dict], *, out_dir: Path, fps: int,
            staging: Path | None = None, profile: str | None = None) -> dict:
    from creative_suite.engine import wolfcam_capture as W
    from engine.pantheon import render_permit
    render_permit.require(f"pantheon_capture:{Path(demo).name}")
    t0 = time.time()
    staging = staging or W.STAGING
    out_dir.mkdir(parents=True, exist_ok=True)
    # A directory owned by THIS capture, removed after encoding. A shared one
    # let a shorter re-capture encode the previous run's extra frames through
    # %06d, and uncompressed TGAs are ~580 MB per clip at 1280x720 (HL-8).
    frames_dir = Path(tempfile.mkdtemp(prefix="pc_frames_", dir=out_dir))
    log = frames_dir / "sound.tsv"
    ws = sorted(windows, key=lambda w: int(w["start_ms"]))
    for w in ws:                                   # as wolfcam_capture.py:489-491
        for old in out_dir.glob(f"{w['clip_name']}*.avi"):
            old.unlink()
    argv = [str(host_exe()), "--cgame", "--fps", str(fps),
            "--basepath", str(staging), "--game", "wolfcam-ql",
            "--demo", str(resolve_demo(Path(demo))), "--sound-log", str(log)]
    argv += profile_sets(profile)
    for w in ws:
        argv += ["--window", w["clip_name"], str(int(w["start_ms"])),
                 str(int(w["end_ms"])), str(frames_dir)]
    want = W.frames_expected(ws, fps)
    base = {"returncode": None, "avis": {}, "frames_written": 0, "capture_fps": 0,
            "played_too_fast_by": 0.0, "retimed": []}
    try:
        rc, text = _run_host(argv, timeout=LAUNCH_S + want * PER_FRAME_S * 3)
    except subprocess.TimeoutExpired:
        shutil.rmtree(frames_dir, ignore_errors=True)
        r = {**base, **W.completeness(ws, {}, 0, fps), "elapsed_s": time.time() - t0}
        r["error"] = "TIMEOUT"
        return r
    got = {m.group(1): int(m.group(2)) for m in _WINDOW.finditer(text)}
    wavs = _mix(log, ws, frames_dir, staging) if rc == 0 else {}
    avis = {w["clip_name"]: _encode(frames_dir, w["clip_name"], wavs.get(w["clip_name"]),
                                    fps, out_dir / f"{w['clip_name']}.avi")
            for w in ws if got.get(w["clip_name"])}
    shutil.rmtree(frames_dir, ignore_errors=True)
    written = sum(got.values())
    r = {**base, "returncode": rc, "elapsed_s": time.time() - t0, "avis": avis,
         "frames_written": written,
         # Frames are rendered at exact server times, never against a wall
         # clock: the declared rate is the true rate, nothing to retime.
         "capture_fps": round(float(fps), 2) if written else 0,
         "played_too_fast_by": 1.0 if written else 0.0,
         **W.completeness(ws, avis, written, fps)}
    if rc != 0 and not r["error"]:
        r["error"] = (text.strip().splitlines() or ["no output"])[-1]
    return r
```

- [ ] **Step 5: The switch** in `wolfcam_capture.py`:

```python
BACKENDS = ("wolfcam", "pantheon")


def capture_backend() -> str:
    """One setting, two backends. wolfcam until G1-G4 pass and the user signs
    off (docs/superpowers/plans/2026-09-12-pantheon-production-capture.md)."""
    b = os.getenv("PANTHEON_CAPTURE_BACKEND", "wolfcam").strip().lower()
    if b not in BACKENDS:
        raise ValueError(f"PANTHEON_CAPTURE_BACKEND={b!r}; expected one of {BACKENDS}")
    return b
```

First statements of `capture_demo`:

```python
    if capture_backend() == "pantheon" and not os.getenv("CS_CAPTURE_MOCK"):
        from engine.pantheon import pantheon_capture as PC
        return PC.capture(staging / "wolfcam-ql" / "demos" / safe_demo, windows,
                          out_dir=staging / "wolfcam-ql" / "videos",
                          fps=profile_fps(profile), staging=staging, profile=profile)
```

The AVIs land in the same `videos` directory, so `publish_avi` and every caller are unchanged.

**The host's command-line buffer.** `pantheon_frame.c` builds the engine command line in `char cmdline[1024]` with `Q_strcat`, which **truncates silently** — a full profile would lose its last `--set`s without a word (the same failure family as `+demo` dropped past 32 `+` groups). Raise it to 16384, and in the `--set` branch `ShotError("command line too long at --set %s", ...)` if `strlen(cmdline) + strlen(new) >= sizeof(cmdline)`. Add a Task 7 smoke: a profile's last cvar is visible in the host log (`cvarlist`-style echo or the engine's own `+set` report).

- [ ] **Step 5b: The runtime handshake.** First line the host prints on a demo run:

```text
PANTHEON_HANDSHAKE {"engine":"PANTHEON","build":"<git short hash>","backend":"wgl-fbo","demo_protocol":73,"capture_profile":"<name>","capture_profile_hash":"<sha256>","requested_size":[1280,720],"render_size":[1280,720]}
```

  - `build` comes from `-DPANTHEON_BUILD="\"$(git -C "$HERE" rev-parse --short HEAD)\""` added to the `pantheon_frame.c` compile line in `build_cgame.sh`.
  - `backend` is `wgl-fbo` only when `PANTHEON_RequireOffscreenTarget` has passed; `render_size` is `glConfig.vidWidth/vidHeight` **after** the FBO exists; `demo_protocol` is the `protocol` cvar after the reader's gamestate.
  - Python passes `--profile-id <name> <sha256>`, where the hash is SHA-256 of the sorted `--set` pairs from `profile_sets(profile)`; the host echoes both.
  - `pantheon_capture.validate_handshake(text, *, profile, size)` fails the capture (`error="HANDSHAKE: ..."`) when the line is missing, `build` differs from `git rev-parse --short HEAD` of `S.CODE_ROOT` (a stale binary — "rebuild pantheon_cgame.exe"), `backend != "wgl-fbo"`, the profile or its hash differ, or `render_size != requested_size`. Tests cover each refusal with fake host text.

- [ ] **Step 6: Register and classify.** `backends.py`: `PantheonNative` (`name = "PANTHEON_NATIVE"`, `supports = {REFERENCE_RENDER, FINAL_QUAKE_BEAUTY}`, `render` raises `NotImplementedError("demo capture goes through pantheon_capture.capture; ShotSpecs through --shot")`), added to `BACKENDS`. `test_render_permit.py`: add `"engine/pantheon/pantheon_capture.py"` to `LAUNCH_SITES`. `test_pantheon_headless_boundary.py`: `"sound_mix"` into `BACKEND_ALLOWED` (`pantheon_capture` was classified in Task 1, `capture_parity` in Task 5).
- [ ] **Step 7:** Run `test_pantheon_capture.py test_render_permit.py test_pantheon_headless_boundary.py` and every existing `test_*capture*.py`: all pass.
- [ ] **Step 8:** Commit: `feat: PANTHEON_NATIVE capture backend behind PANTHEON_CAPTURE_BACKEND`

Now run Task 5 Step 2 (G2 / stop H2).

---

### Task 8: Gate G3 — audio parity — then stop H3

**Files:** `engine/pantheon/capture_parity.py`

- [ ] **Step 1:**

```python
def envelope(avi: Path, sr: int = 8000):
    import numpy as np
    raw = subprocess.run([str(FFMPEG), "-loglevel", "error", "-i", str(avi), "-vn",
                          "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    x = np.abs(np.frombuffer(raw, dtype=np.float32))
    k = sr // 100                                       # 10 ms windows
    return x[: len(x) // k * k].reshape(-1, k).mean(axis=1)


def audio_lag_ms(wolfcam_avi: Path, pantheon_avi: Path) -> tuple[float, float]:
    """(lag in ms, peak normalised correlation) of the two 10 ms envelopes."""
    import numpy as np
    a, b = envelope(wolfcam_avi), envelope(pantheon_avi)
    n = min(len(a), len(b))
    a, b = a[:n] - a[:n].mean(), b[:n] - b[:n].mean()
    c = np.correlate(a, b, mode="full")
    i = int(np.argmax(c))
    return (i - (n - 1)) * 10.0, float(c[i]) / (float(np.linalg.norm(a) * np.linalg.norm(b)) or 1.0)
```

Add a self-test to `test_pantheon_capture.py` proving the metric can fail: two synthetic WAVs with a known 120 ms offset must report `|lag| ≈ 120` (so a 40 ms gate is meaningful).

- [ ] **Step 2:** Run on the ten G2 frags; pass per clip `|lag| ≤ 40` and `corr ≥ 0.6`. A consistent offset across all clips is one pipeline offset (fix once); scattered failures are missing sounds (inspect that clip's `S` lines).

**STOP H3.** Send the ten PANTHEON clips (with the wolfcam versions) for listening. Record verdicts beside the G2 ones.

- [ ] **Step 3:** Commit: `test: G3 -- PANTHEON audio lands where wolfcam's does`

---

### Task 9: Linear-light accumulation — then stop H4

Averaging display-encoded values darkens edges. Decode to linear, average, re-encode. **The same resolve is required of `codex/capture-supersampling` before it merges** — note it on that branch.

The framebuffer is not clean sRGB (`r_gamma` is baked into textures at upload; overbright is off on this host). sRGB is the standard decode; Step 3 checks the result by eye.

**Files:** `host/pantheon_frame.c`

- [ ] **Step 1:** Replace the accumulator:

```c
/* Averaging ENCODED values averages numbers, not light: a half-covered edge
 * between 255 and 0 averages to 128 -- 22 % of the light, not 50 %. That is
 * the dark fringe. */
static float s_toLinear[256];
static byte  s_toSrgb[4097];

static void PANTHEON_LinearTables(void)
{
    int i;
    for (i = 0; i < 256; i++) {
        float c = i / 255.0f;
        s_toLinear[i] = c <= 0.04045f ? c / 12.92f : powf((c + 0.055f) / 1.055f, 2.4f);
    }
    for (i = 0; i <= 4096; i++) {
        float l = i / 4096.0f;
        float c = l <= 0.0031308f ? l * 12.92f : 1.055f * powf(l, 1.0f / 2.4f) - 0.055f;
        s_toSrgb[i] = (byte)(c * 255.0f + 0.5f);
    }
}

static void PANTHEON_BlurAccumulate(float *acc, const byte *rgb, int n)
{
    int i;
    for (i = 0; i < n; i++) acc[i] += s_toLinear[rgb[i]];
}

static void PANTHEON_BlurResolve(byte *rgb, const float *acc, int n, int samples)
{
    int i;
    for (i = 0; i < n; i++) {
        float l = acc[i] / samples;
        if (l < 0.0f) l = 0.0f;
        if (l > 1.0f) l = 1.0f;
        rgb[i] = s_toSrgb[(int)(l * 4096.0f + 0.5f)];
    }
}
```

`blurAccum` becomes `float *` (`calloc(np * 3, sizeof(float))`, reset with `sizeof(float)`); `PANTHEON_LinearTables()` once at startup; `#include <math.h>`.

- [ ] **Step 2:** `--blur 8 --shutter 0` vs `--blur 1` on the Task 4 window: differs by no more than the documented 0.038 % per-call region (`docs/reference/2026-09-08-engine-comparison-and-improvement-scan.md` §6.5) plus ±1 level. (sRGB round trips on integer inputs are exact to ±1.)
- [ ] **Step 3:** Render the Task 4 window at `--blur 8 --shutter 0.7` with the old and new accumulator; `review_sheet.compare` cropped on the rocket's light against the ceiling.

**STOP H4.** Send the sheet: *"Is the dark halo around the moving light gone, and is nothing else worse?"*

- [ ] **Step 4:** Commit: `fix: motion blur averages light, not encoded values`

---

### Task 10: Measure whether HDR exists before building it — then stop H5

**No production behaviour changes.** One question: do values above 1.0 survive this renderer before the final clamp?

**Files:** create `engine/pantheon_renderer/build_probe.sh` (copies `renderer/tr_init.c` from the vendored tree into `build/probe/`, patches the copy, links `build/pantheon_probe.exe`); `--probe-hdr` in `host/pantheon_frame.c`; create `docs/reference/<date>-hdr-survival-probe.md`. **Never edit the vendored tree in place**: it is untracked, and in a worktree it is a junction to the main checkout's copy, so an edit would change every session's source invisibly to git.

- [ ] **Step 1: Write down every clamp on the path, with file:line, before any code.** At minimum: texture upload internal formats (`GL_RGB8`/`GL_RGBA8`) and `R_LightScaleTexture`; lightmaps (`R_ColorShiftLightingBytes`, `tr_bsp.c`, clamps to 255); vertex colours (bytes); `tr.overbrightBits` / `r_mapOverBrightBits`; and **fixed-function colour clamping**: vertex and fragment colours are clamped to [0,1] before blending unless `GL_ARB_color_buffer_float` clamping is turned off.

- [ ] **Step 2: The probe.** Under `--probe-hdr`:
  - in the probe build's **copy** of `tr_init.c`, the FBO scene texture is created `GL_RGBA16F` instead of `GL_RGB8` (`InitFrameBufferAndRenderBuffer`);
  - `glClampColorARB(GL_CLAMP_VERTEX_COLOR_ARB, GL_FALSE)`, `glClampColorARB(GL_CLAMP_FRAGMENT_COLOR_ARB, GL_FALSE)`, `glClampColorARB(GL_CLAMP_READ_COLOR_ARB, GL_FALSE)` right after the FBO is bound (resolve `glClampColorARB` through `PANTHEON_GetProcAddress`; if absent, the probe reports INVALID, not "no HDR");
  - **positive control:** before the scene, draw two additive full-screen quads at colour (0.8, 0.8, 0.8) into a scratch region; read it back. If it does not read ≈ 1.6, the probe is **INVALID** and says so — a probe that cannot see 1.6 on purpose cannot see HDR by accident.
  - Render the Task 4 window's frames at 0 %, 50 %, 100 %; read back with `glReadPixels(..., GL_RGB, GL_FLOAT, ...)`; report per frame the max channel value and the fraction of pixels with any channel > 1.0.

- [ ] **Step 3: Record the result and the decision**

| Result | Meaning | Decision |
|---|---|---|
| Control INVALID | The measurement cannot see range | Fix the probe; decide nothing |
| Max ≤ 1.0 on every frame | Range gone before the target (8-bit inputs, clamped lightmaps) | No FP target, no EXR. An HDR plan would start at lighting and texture inputs. |
| > 1.0 only in additive effects | Some range survives in blending | A narrow FP16 plan scoped to effects is defensible |
| Broad values > 1.0 | Real HDR survives | Write the HDR/EXR plan |

**STOP H5.** Send the doc; the user decides.

- [ ] **Step 4:** Delete `build_probe.sh`, `build/probe/` and the `--probe-hdr` branch unless the decision is "write the HDR plan"; commit the doc either way. `git status` of the main checkout's vendored tree must show nothing (it is untracked; confirm with an MD5 of `renderer/tr_init.c` before and after).

---

### Task 11: Cutover — only with the user's explicit go — stop H6

**Precondition:** G1, G2 (ten human PASS), G3, G4 recorded as passing; suite at or better than the Task 0 baseline; the user says go in chat.

- [ ] **Step 1:** `capture_backend()` default → `"pantheon"`; rename the default test accordingly.
- [ ] **Step 2:** Full suite vs baseline: no new failures.
- [ ] **Step 3: STOP H6.** One real frag through the mining session's normal command (not a harness); ffprobe the AVI (duration, frame count, audio stream present); extract one frame to the visual record; the user watches it.
- [ ] **Step 4:** `CLAUDE.md` HL-2: PANTHEON_NATIVE is the production renderer; wolfcam keeps its four oracle jobs. Commit, push the **feature branch**, and open a PR to the protected branch for the user to merge — never push to `main`. Rollback is `PANTHEON_CAPTURE_BACKEND=wolfcam`.

---

## Explicitly not in this plan

- Windowless GL context (EGL/pbuffer).
- FP16 targets, EXR masters, tonemapping — gated by Task 10.
- Merging `codex/capture-supersampling` — gated by Task 9's resolve being adopted there.
- rend2, Vulkan, IQM, OpenAL Soft, FX-script authoring, texture/asset work.
- Free-camera (FL) angles from demos — after G2 proves FP parity.
- Vendoring the WolfcamQL archive into git (decided against, 2026-09-12; Task 0.5 bootstraps it — vendor only if air-gapped clean-clone builds are ever required).
- **Music, edit and effects work** (`render_highlight.py`, beat sync, transitions). Banked as a separate follow-up (`docs/reference/2026-09-12-music-sync-and-effects-wiring-audit.md`); nothing on this branch changes the second box of *demo → PANTHEON → raw capture → render_highlight → edit/music/output*.
