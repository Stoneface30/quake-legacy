# Local Editor (Tier 2) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Premiere/AE-class local fragmovie editor backed by
OpenTimelineIO + ffmpeg-python + the existing `phase1/render_part_v6.py`
pipeline, frame-accurate WebCodecs playback, and a node-graph effects
compositor — in 9 atomic TDD steps, ~8 build-days.

**Architecture:** FastAPI + OTIO (pure Python) backend, browser frontend
via importmap CDN (no npm). Reuses Cinema Suite `JobQueue` (CS-1).
Editor state serializes to `output/part{NN}_editor_state.json`; OTIO
`.otio` files are the generated interchange format. Render = translate
state → flow_plan.json + overrides.txt → invoke existing
`phase1/render_part_v6.py`. Proxies at 960×540 all-intra H.264 in
`output/_proxies/part{NN}/`.

**Tech Stack:** OpenTimelineIO 0.18 (Apache-2.0, pure-Python wheel on
Windows), ffmpeg-python 0.2 (Apache-2.0), existing
`tools/ffmpeg/ffmpeg.exe`, WebCodecs + mp4box.js, wavesurfer.js v7,
animation-timeline-control (MIT), LiteGraph.js upstream (MIT),
Theatre.js (Apache-2.0 core), Tweakpane v4 (MIT).

**ADR-EDT-01 (2026-04-20):** Dropped MLT. MLT has no Windows Python
wheel in 2026; installing it requires WSL2 + `python3-mlt` or a 1-2 day
msys2 build. Since Kdenlive interop is not load-bearing (our render
stays in `phase1/render_part_v6.py`), pure-Python OTIO + ffmpeg-python
is a cleaner fit. All "MLT XML" references below are LEGACY — the
implementation emits OTIO `.otio` and calls `render_part_v6.py`.

**Spec:** `docs/superpowers/specs/2026-04-20-editor-design.md`

---

## Step 1: MLT + OTIO Python Harness

**Goal:** Prove the backend dependencies work on our Windows 11 box,
render a minimal 5-second mp4 from a 2-clip timeline via MLT, round-trip
the same timeline through OTIO.

**Files:**
- Create: `creative_suite/editor/__init__.py`
- Create: `creative_suite/editor/mlt_backend.py`
- Create: `creative_suite/editor/otio_bridge.py`
- Create: `creative_suite/tests/test_mlt_backend.py`
- Create: `creative_suite/tests/test_otio_bridge.py`

- [ ] **Step 1.1: Install & verify MLT Python bindings**

```bash
pip install mlt
python -c "import mlt; mlt.Factory.init(); print(mlt.mlt_version_get_string())"
```

Expected: MLT version string, e.g. `7.22.0`.

**If the import fails on Windows** (missing wheel): dispatch a research
subagent with: *"Find the simplest install path for MLT Python bindings
on Windows 11 + Python 3.11. Confirmed-working answers only. If building
from source is required, give the exact msys2 / cmake / swig invocation.
If WSL2 is the answer, confirm pip install mlt works inside Ubuntu 22.04
and give the minimal launch command to serve uvicorn over
`--host 0.0.0.0 --port 8800` so a Windows browser can hit it."*

- [ ] **Step 1.2: Write failing test for MLT harness**

`creative_suite/tests/test_mlt_backend.py`:

```python
from pathlib import Path
from creative_suite.editor.mlt_backend import render_mlt_xml


def test_render_two_clips_into_mp4(tmp_path: Path) -> None:
    # Two 2-second clips from the phase1 fixtures dir
    fixture = Path(__file__).parent.parent.parent / "phase1" / "tests" / "fixtures"
    clip_a = fixture / "blue_2s.mp4"
    clip_b = fixture / "red_2s.mp4"
    assert clip_a.exists() and clip_b.exists(), "test fixtures missing"

    mlt_xml = tmp_path / "smoke.mlt"
    out_mp4 = tmp_path / "smoke.mp4"
    render_mlt_xml(
        clips=[(clip_a, 0.0, 2.0), (clip_b, 0.0, 2.0)],
        out_mlt=mlt_xml, out_mp4=out_mp4,
        profile="atsc_1080p_60", crf=23, preset="veryfast",
    )
    assert out_mp4.exists() and out_mp4.stat().st_size > 1000
    # ffprobe duration ≈ 4s ± 0.1s
    import subprocess
    dur = float(subprocess.check_output([
        "tools/ffmpeg/ffprobe.exe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "csv=p=0", str(out_mp4),
    ]).strip())
    assert 3.9 < dur < 4.1
```

Run: `python -m pytest creative_suite/tests/test_mlt_backend.py::test_render_two_clips_into_mp4 -v`
Expected: FAIL (`render_mlt_xml` doesn't exist yet).

If fixtures don't exist, use `ffmpeg` to generate them:
```bash
tools/ffmpeg/ffmpeg.exe -y -f lavfi -i "color=blue:s=1920x1080:r=60:d=2" \
  -c:v libx264 -crf 23 phase1/tests/fixtures/blue_2s.mp4
tools/ffmpeg/ffmpeg.exe -y -f lavfi -i "color=red:s=1920x1080:r=60:d=2" \
  -c:v libx264 -crf 23 phase1/tests/fixtures/red_2s.mp4
```

- [ ] **Step 1.3: Implement `render_mlt_xml`**

`creative_suite/editor/mlt_backend.py`:

```python
from __future__ import annotations

import subprocess
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree


def render_mlt_xml(
    *,
    clips: list[tuple[Path, float, float]],
    out_mlt: Path,
    out_mp4: Path,
    profile: str = "atsc_1080p_60",
    crf: int = 23,
    preset: str = "veryfast",
) -> None:
    """Serialize clips to MLT XML and render via melt.

    `clips` is a list of (path, in_s, out_s) tuples.
    """
    mlt = Element("mlt")
    mlt.set("profile", profile)

    playlist = SubElement(mlt, "playlist")
    playlist.set("id", "body")

    for idx, (path, in_s, out_s) in enumerate(clips):
        prod = SubElement(mlt, "producer")
        prod.set("id", f"clip_{idx}")
        prod.set("in", _timecode(in_s))
        prod.set("out", _timecode(out_s))
        resource = SubElement(prod, "property")
        resource.set("name", "resource")
        resource.text = str(path)
        entry = SubElement(playlist, "entry")
        entry.set("producer", f"clip_{idx}")
        entry.set("in", _timecode(in_s))
        entry.set("out", _timecode(out_s))

    tractor = SubElement(mlt, "tractor")
    tractor.set("id", "main")
    track = SubElement(tractor, "track")
    track.set("producer", "body")

    ElementTree(mlt).write(out_mlt, encoding="utf-8", xml_declaration=True)

    # melt invocation
    melt_bin = _find_melt_bin()
    subprocess.run([
        str(melt_bin), str(out_mlt),
        "-consumer", f"avformat:{out_mp4}",
        f"vcodec=libx264", f"crf={crf}", f"preset={preset}",
        "acodec=aac", "ab=192k",
    ], check=True)


def _timecode(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def _find_melt_bin() -> Path:
    # melt.exe ships in MLT's bin/. Look in standard install paths.
    candidates = [
        Path("C:/Program Files/MLT/bin/melt.exe"),
        Path("tools/mlt/bin/melt.exe"),
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError("melt.exe not found; install MLT or symlink to tools/mlt/")
```

- [ ] **Step 1.4: Run test to verify pass**

Run: `python -m pytest creative_suite/tests/test_mlt_backend.py::test_render_two_clips_into_mp4 -v`
Expected: PASS.

- [ ] **Step 1.5: OTIO round-trip test**

`creative_suite/tests/test_otio_bridge.py`:

```python
from pathlib import Path
from creative_suite.editor.otio_bridge import state_to_otio, otio_to_state


def test_round_trip_preserves_durations(tmp_path: Path) -> None:
    state = {
        "part": 5, "schema_version": 1,
        "timeline": {
            "duration_s": 10.0, "fps": 60,
            "tracks": [{
                "kind": "video", "name": "body",
                "clips": [
                    {"id": "c0", "chunk": "chunk_0000.mp4",
                     "in_s": 0.0, "out_s": 5.0, "start_s": 0.0,
                     "time_warp": None, "nodes": [], "removed": False},
                    {"id": "c1", "chunk": "chunk_0001.mp4",
                     "in_s": 0.0, "out_s": 5.0, "start_s": 5.0,
                     "time_warp": None, "nodes": [], "removed": False},
                ],
            }],
            "keyframes": {},
        },
    }
    otio_path = tmp_path / "part05.otio"
    state_to_otio(state, otio_path)
    assert otio_path.exists()
    back = otio_to_state(otio_path)
    clips = back["timeline"]["tracks"][0]["clips"]
    assert len(clips) == 2
    assert clips[0]["chunk"] == "chunk_0000.mp4"
    assert abs(clips[1]["start_s"] - 5.0) < 0.001
```

- [ ] **Step 1.6: Implement `state_to_otio` / `otio_to_state`**

`creative_suite/editor/otio_bridge.py`:

```python
from __future__ import annotations

from pathlib import Path
from typing import Any

import opentimelineio as otio


def state_to_otio(state: dict[str, Any], out_path: Path) -> None:
    tl = otio.schema.Timeline(name=f"Part {state['part']}")
    fps = state["timeline"]["fps"]
    for track in state["timeline"]["tracks"]:
        if track["kind"] != "video":
            continue
        otrack = otio.schema.Track(name=track["name"], kind=otio.schema.TrackKind.Video)
        for clip in track.get("clips", []):
            if clip.get("removed"):
                continue
            dur = clip["out_s"] - clip["in_s"]
            oclip = otio.schema.Clip(
                name=clip["id"],
                source_range=otio.opentime.TimeRange(
                    start_time=otio.opentime.RationalTime(clip["in_s"] * fps, fps),
                    duration=otio.opentime.RationalTime(dur * fps, fps),
                ),
                media_reference=otio.schema.ExternalReference(
                    target_url=f"file:///{clip['chunk']}",
                ),
            )
            otrack.append(oclip)
        tl.tracks.append(otrack)
    otio.adapters.write_to_file(tl, str(out_path))


def otio_to_state(path: Path) -> dict[str, Any]:
    tl = otio.adapters.read_from_file(str(path))
    tracks = []
    for otrack in tl.tracks:
        clips = []
        for idx, oclip in enumerate(otrack):
            if not isinstance(oclip, otio.schema.Clip):
                continue
            sr = oclip.source_range
            in_s = sr.start_time.to_seconds()
            out_s = in_s + sr.duration.to_seconds()
            start_s = oclip.range_in_parent().start_time.to_seconds()
            url = oclip.media_reference.target_url if isinstance(
                oclip.media_reference, otio.schema.ExternalReference
            ) else ""
            chunk = url.rsplit("/", 1)[-1]
            clips.append({
                "id": oclip.name, "chunk": chunk,
                "in_s": in_s, "out_s": out_s, "start_s": start_s,
                "time_warp": None, "nodes": [], "removed": False,
            })
        tracks.append({
            "kind": "video", "name": otrack.name, "clips": clips,
        })
    return {
        "part": 0, "schema_version": 1,
        "timeline": {
            "duration_s": tl.duration().to_seconds(),
            "fps": int(tl.duration().rate),
            "tracks": tracks,
            "keyframes": {},
        },
    }
```

- [ ] **Step 1.7: Commit**

```bash
git add creative_suite/editor/ creative_suite/tests/test_mlt_backend.py \
        creative_suite/tests/test_otio_bridge.py
git commit -m "feat(editor): MLT + OTIO Python harness — Step 1 of Tier 2

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

**Gate G-T2-3:** `test_render_two_clips_into_mp4` passes, output is a
real mp4 of duration 4s ± 0.1s. **Proceed to Step 2.**

---

## Step 2: Proxy Generator + `/proxies` Endpoint

**Goal:** Given Part N, generate 960×540 all-intra H.264 proxies for
every chunk in `output/_part{NN}_v6_body_chunks/`. Expose via FastAPI.

**Files:**
- Create: `creative_suite/editor/proxies.py`
- Create: `creative_suite/api/editor.py`
- Create: `creative_suite/tests/test_proxies.py`
- Create: `creative_suite/tests/test_api_editor.py`
- Modify: `creative_suite/app.py:NN` (mount the new router)

- [ ] **Step 2.1: Write failing test for proxy generation**

```python
# creative_suite/tests/test_proxies.py
import subprocess
from pathlib import Path

from creative_suite.editor.proxies import generate_proxy, proxy_path_for


def test_generate_proxy_creates_low_res_mp4(tmp_path: Path) -> None:
    src = tmp_path / "chunk_0000.mp4"
    subprocess.run([
        "tools/ffmpeg/ffmpeg.exe", "-y", "-f", "lavfi",
        "-i", "color=blue:s=1920x1080:r=60:d=2",
        "-c:v", "libx264", str(src),
    ], check=True)

    out_dir = tmp_path / "_proxies" / "part05"
    proxy = generate_proxy(src, out_dir=out_dir, ffmpeg="tools/ffmpeg/ffmpeg.exe")
    assert proxy.exists()
    # Width/height check: 960×540
    w = int(subprocess.check_output([
        "tools/ffmpeg/ffprobe.exe", "-v", "error",
        "-select_streams", "v:0", "-show_entries", "stream=width",
        "-of", "csv=p=0", str(proxy),
    ]).strip())
    assert w == 960
```

Expected: FAIL.

- [ ] **Step 2.2: Implement `generate_proxy`**

```python
# creative_suite/editor/proxies.py
from __future__ import annotations

import subprocess
from pathlib import Path


def proxy_path_for(src: Path, out_dir: Path) -> Path:
    return out_dir / f"{src.stem}_proxy.mp4"


def generate_proxy(src: Path, *, out_dir: Path, ffmpeg: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    proxy = proxy_path_for(src, out_dir)
    if proxy.exists():
        return proxy
    tmp = proxy.with_suffix(".partial")
    subprocess.run([
        ffmpeg, "-y", "-i", str(src),
        "-vf", "scale=960:540",
        "-c:v", "libx264", "-preset", "veryfast",
        "-g", "1", "-x264-params", "keyint=1",  # all-intra for frame-step
        "-crf", "28",
        "-c:a", "aac", "-b:a", "96k",
        str(tmp),
    ], check=True)
    tmp.rename(proxy)
    return proxy
```

- [ ] **Step 2.3: Verify test passes**

Run: `python -m pytest creative_suite/tests/test_proxies.py -v`
Expected: PASS.

- [ ] **Step 2.4: Write failing test for `/api/editor/parts/{n}/proxies`**

```python
# creative_suite/tests/test_api_editor.py
import pytest
from fastapi.testclient import TestClient

from creative_suite.app import create_app


def test_post_proxies_enqueues_job(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("CS_PHASE1_OUTPUT_DIR", str(tmp_path / "output"))
    monkeypatch.setenv("CS_EDITOR_PROXY_MOCK", "1")
    (tmp_path / "output").mkdir()
    with TestClient(create_app()) as c:
        r = c.post("/api/editor/parts/5/proxies")
        assert r.status_code == 200
        assert "job_id" in r.json()
```

- [ ] **Step 2.5: Implement `/api/editor` router**

`creative_suite/api/editor.py`:

```python
# Mirrors creative_suite/api/phase1.py layout. Key endpoint: POST
# /parts/{n}/proxies uses JobQueue (CS-1 depth-1 rule applies).
# See spec §6 for full endpoint inventory.
```

Wire into `creative_suite/app.py`:

```python
from creative_suite.api.editor import router as editor_router
app.include_router(editor_router)
```

- [ ] **Step 2.6: Run tests, commit**

Tests pass → commit as
`feat(editor): proxy generator + /api/editor/parts/{n}/proxies`.

**Gate G-T2-1:** Test passes. **Proceed to Step 3.**

---

## Step 3: Editor State Schema + GET/PUT/PATCH Endpoints

**Goal:** `output/part{NN}_editor_state.json` (spec §5.1) is canonical.
Three endpoints: full GET, full PUT, JSON Patch.

**Files:**
- Create: `creative_suite/editor/state.py`
- Create: `creative_suite/tests/test_editor_state.py`
- Modify: `creative_suite/api/editor.py` (add state endpoints)

- [ ] **Step 3.1: Write failing test for state load/save**

```python
def test_state_load_save_atomic(tmp_path: Path) -> None:
    from creative_suite.editor.state import load_state, save_state
    p = tmp_path / "part05_editor_state.json"
    state = {"part": 5, "schema_version": 1, "timeline": {
        "duration_s": 100.0, "fps": 60, "tracks": [], "keyframes": {},
    }}
    save_state(p, state)
    back = load_state(p)
    assert back == state


def test_state_patch_applies_rfc6902(tmp_path: Path) -> None:
    from creative_suite.editor.state import apply_patch
    state = {"timeline": {"tracks": [{"clips": [{"id": "c0"}]}]}}
    patched = apply_patch(state, [
        {"op": "add", "path": "/timeline/tracks/0/clips/-",
         "value": {"id": "c1"}},
    ])
    assert len(patched["timeline"]["tracks"][0]["clips"]) == 2
```

- [ ] **Step 3.2: Implement with `jsonpatch` lib**

```bash
pip install jsonpatch
```

```python
# creative_suite/editor/state.py
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import jsonpatch


def load_state(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(path: Path, state: dict[str, Any]) -> None:
    partial = path.with_suffix(path.suffix + ".partial")
    partial.write_text(json.dumps(state, indent=2), encoding="utf-8")
    os.replace(str(partial), str(path))


def apply_patch(state: dict[str, Any], ops: list[dict[str, Any]]) -> dict[str, Any]:
    return jsonpatch.JsonPatch(ops).apply(state)
```

Note the atomic-write pattern per **L154** (avoid corrupting state on
mid-write crash).

- [ ] **Step 3.3: Add endpoints**

```python
@router.get("/parts/{n}/state")
def get_state(n: int, request: Request) -> dict[str, Any]: ...

@router.put("/parts/{n}/state")
def put_state(n: int, body: dict[str, Any], request: Request) -> dict[str, Any]: ...

@router.patch("/parts/{n}/state")
def patch_state(n: int, ops: list[dict[str, Any]], request: Request) -> dict[str, Any]: ...
```

- [ ] **Step 3.4: Tests pass, commit**

Commit as `feat(editor): editor_state.json + GET/PUT/PATCH endpoints`.

---

## Step 4: Static `/editor` Route + Three-Pane Layout

**Goal:** Serve `creative_suite/frontend/editor.html` at `/editor`, with
CSS grid layout: preview top-left, inspector top-right, timeline bottom
full-width. Resizable panes via `<split-pane>` web component.

**Files:**
- Create: `creative_suite/frontend/editor.html`
- Create: `creative_suite/frontend/editor.css`
- Create: `creative_suite/frontend/app-editor.js`
- Create: `creative_suite/frontend/split-pane.js` (custom element)
- Modify: `creative_suite/app.py` (mount `/editor-static` and `/editor`)
- Create: `creative_suite/tests/test_editor_html.py`

- [ ] **Step 4.1: Write failing test**

```python
def test_editor_route_serves_html() -> None:
    with TestClient(create_app()) as c:
        r = c.get("/editor")
        assert r.status_code == 200
        assert "<div id=\"pane-preview\"" in r.text
        assert "<div id=\"pane-timeline\"" in r.text
```

- [ ] **Step 4.2: Implement — see spec §3.1. Three panes, importmap
  referencing CDN URLs for wavesurfer, animation-timeline-control,
  LiteGraph, Theatre, Tweakpane, mp4box.**

- [ ] **Step 4.3: Smoke test in real browser**

`uvicorn creative_suite.app:create_app --factory --host 127.0.0.1 --port 8800`
then open `http://127.0.0.1:8800/editor?part=5`. Verify three panes
visible. Commit.

---

## Step 5: Timeline Row 1 (Video + Playback) via WebCodecs

**Goal:** Show the video row on the timeline. Click a position → play
the proxy at that point. JKL transport (J=reverse, K=pause, L=forward).
Frame-step via left/right arrows.

**Files:**
- Create: `creative_suite/frontend/timeline-video-row.js`
- Create: `creative_suite/frontend/webcodecs-player.js`
- Modify: `creative_suite/frontend/app-editor.js`
- Create: `creative_suite/tests/test_timeline_video_row.py` (visual smoke
  via Playwright — one screenshot at a seek point)

- [ ] **Step 5.1: Write the WebCodecs player wrapper**

```javascript
// creative_suite/frontend/webcodecs-player.js
// Wraps mp4box.js + VideoDecoder. Exposes:
//   async load(proxyUrl): void
//   seek(timeSeconds): void   // frame-accurate
//   async playForward(speed=1.0): void
//   pause(): void
//   on("frame", (imageData, t_ms) => void)
// Fallback: if !('VideoDecoder' in window), wrap <video> + rVFC.
```

- [ ] **Step 5.2: Write the timeline video row**

Uses `animation-timeline-control` from
`https://cdn.skypack.dev/animation-timeline-control@1.x`. One lane per
clip. Click → seek. Drag clip edge → trim in_s/out_s. Drag clip body
→ reorder (patch via PATCH /state).

- [ ] **Step 5.3: Wire JKL hotkeys + arrow-key frame-step.**

- [ ] **Step 5.4: Playwright screenshot smoke** — open `/editor?part=5`,
  wait for proxies, seek to t=10s, take screenshot, assert preview
  pane contains a non-black canvas (histogram mean > 5).

Commit as `feat(editor): video row + WebCodecs playback + JKL transport`.

---

## Step 6: Audio Rows (Game + 3 Music) via wavesurfer-multitrack

**Goal:** Game-audio row (source: `output/part{NN}_game_stem.wav`) and
three music rows (intro/main/outro) on the timeline, synced to video.
Clickable waveforms for scrub.

**Files:**
- Create: `creative_suite/frontend/timeline-audio-rows.js`
- Modify: `creative_suite/frontend/app-editor.js`

- [ ] **Step 6.1: Integrate wavesurfer.js v7 (importmap)**

```html
<script type="importmap">
{ "imports": {
  "wavesurfer.js": "https://cdn.jsdelivr.net/npm/wavesurfer.js@7/dist/wavesurfer.esm.js",
  "wavesurfer-multitrack": "https://cdn.jsdelivr.net/npm/wavesurfer-multitrack@1/dist/index.js"
}}
</script>
```

- [ ] **Step 6.2: Link `media:` option to the same `<video>` element
  the WebCodecs player paints to** — so audio and video stay locked.

- [ ] **Step 6.3: Downbeat markers** — read
  `output/part{NN}_music_structure.json`, overlay tick marks on music_main
  row at each downbeat timestamp.

- [ ] **Step 6.4: Commit.**

---

## Step 7: LiteGraph Node Panel + Clip-to-Node Binding

**Goal:** Effects tab. Per-clip `nodes[]` array. User drags nodes onto
a canvas, connects them, params show in inspector. Serializes to
`editor_state.timeline.tracks[0].clips[i].nodes`.

**Files:**
- Create: `creative_suite/frontend/node-panel.js`
- Create: `creative_suite/frontend/node-library.js` (built-in nodes:
  `SlowMoWindow`, `Zoom`, `ColorGrade`, `TitleCardStyle`)
- Modify: `creative_suite/frontend/app-editor.js`

- [ ] **Step 7.1: Integrate upstream LiteGraph.js via importmap.**
  Upstream is MIT. ComfyUI's fork is archived — do NOT use.

- [ ] **Step 7.2: Built-in node: `SlowMoWindow(center_t, duration, rate=0.5)`**
  — maps to MLT `<filter mlt_service="timewarp" speed="0.5" in="..." out="..."/>`.

- [ ] **Step 7.3: Built-in node: `Zoom(center_x, center_y, scale=1.5, duration)`**
  — maps to MLT `<filter mlt_service="affine" .../>`.

- [ ] **Step 7.4: Built-in node: `ColorGrade(hue, saturation, brightness, contrast)`**
  — maps to MLT `<filter mlt_service="brightness"/>` + hueshift.

- [ ] **Step 7.5: Built-in node: `TitleCardStyle(font, color, scanlines_opacity)`**
  — maps to our title_card.py Quake-style renderer (Rule P1-Y).

- [ ] **Step 7.6: Commit.**

---

## Step 8: Theatre Keyframes + Tweakpane Inspector

**Goal:** Any numeric node param is keyframeable. Clicking a param in
Tweakpane + pressing `K` snapshots a keyframe at the current playhead.
Theatre studio overlays show the bezier curve editor.

**Files:**
- Create: `creative_suite/frontend/keyframes-theatre.js`
- Create: `creative_suite/frontend/inspector-tweakpane.js`
- Modify: `creative_suite/frontend/app-editor.js`

- [ ] **Step 8.1: Load Theatre UMD bundle**

```html
<script src="https://unpkg.com/@theatre/browser-bundles@0.7.x/dist/index.umd.js"></script>
```

- [ ] **Step 8.2: Bind Theatre `Sheet` to a node's param. On keyframe
  commit, PATCH `/state` with the new `keyframes._theatre_data` blob.**

- [ ] **Step 8.3: Tweakpane binds to the currently selected clip OR
  currently selected node. Exposes `slow`, `head_trim`, `tail_trim`,
  `section_role`, any node's params. Writes flow through `onClipOverride`
  (same path as Tier 1 removed flag).**

- [ ] **Step 8.4: OTIO round-trip test** — build a keyframed timeline,
  export to OTIO, re-import, assert timing and node params match
  within 1ms tolerance. **Gate G-T2-2.**

- [ ] **Step 8.5: Commit.**

---

## Step 9: Render Button + MLT Consumer + render_versions Row

**Goal:** RENDER button assembles current state → MLT XML → melt.exe →
mp4 → sqlite row in `render_versions`. Two modes: `preview` (default,
CRF 23 veryfast — Rule P1-J v2) and `ship` (CRF 15 slow or av1_nvenc
cq=18).

**Files:**
- Modify: `creative_suite/editor/mlt_backend.py` (add
  `render_state_to_mp4` that walks the full state, not just 2 clips)
- Modify: `creative_suite/api/editor.py` (add `/render` endpoint)
- Create: `creative_suite/tests/test_editor_render.py`

- [ ] **Step 9.1: Write `render_state_to_mp4(state, mode, out_mp4)`**

Handles: video row → playlist. Multi-angle: nested playlist. Slow-mo:
`<filter mlt_service="timewarp"/>`. Game audio: `<track producer="game"/>`.
Music: concat 3 audio producers into one track, sidechain-duck via MLT
`<filter mlt_service="volume" .../>` with a keyframe envelope from
`output/part{NN}_ducking.json`.

- [ ] **Step 9.2: Add `/api/editor/parts/{n}/render` endpoint**

```python
class RenderBody(BaseModel):
    mode: Literal["preview", "ship"] = "preview"
    tag: str

@router.post("/parts/{n}/render")
async def post_render(n: int, body: RenderBody, ...): ...
```

Must go through `JobQueue` — same CS-1 depth-1 rule as phase1 rebuild.
Test: second submit returns 409. **Gate G-T2-5.**

- [ ] **Step 9.3: Part 5 smoke render** — open `/editor?part=5`, do no
  edits, click RENDER (preview mode). Verify output mp4 plays and is
  within 1% duration of Part05_v1_PREVIEW_freshstems.mp4.
  **Gate G-T2-3.**

- [ ] **Step 9.4: Part 5 edit render** — remove 3 clips, add one
  slow-mo window, click RENDER. Verify new mp4 is shorter by the sum of
  removed clip durations minus xfade adjustments, and music_plan.json
  has a regenerated queue sized to the new body_dur_estimate.
  **Gate G-T2-6.**

- [ ] **Step 9.5: Write `render_versions` row with `mode="editor"`** so
  we can differentiate editor renders from `render_part_v6` renders in
  the versions panel.

- [ ] **Step 9.6: Rule P1-J v2 compliance test** — POST render with
  `mode=preview`, inspect the MLT consumer props in the generated
  `.mlt` file, assert `crf=23 preset=veryfast`. POST with `mode=ship`,
  assert `crf=15 preset=slow` (or `av1_nvenc cq=18`). **Gate G-T2-4.**

- [ ] **Step 9.7: Commit.**

---

## Final Verification

After all 9 steps:

```bash
python -m pytest creative_suite/tests/ phase1/tests/ -v
pyright creative_suite/ phase1/
```

All green → **REQUIRED SUB-SKILL: Use superpowers:finishing-a-development-branch**.

**Total checkboxes: 39. Target: 8 build-days. Calendar estimate: 1.5 weeks
with review cycles.**

---

*End of plan. Spec at
`docs/superpowers/specs/2026-04-20-editor-design.md`.*
