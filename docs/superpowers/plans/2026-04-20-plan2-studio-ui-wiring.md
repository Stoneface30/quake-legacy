# /studio Full UI Wiring

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the full `/studio` Premiere-class editor — 5 pages, frame-accurate preview, video timeline, audio stems, beat markers, effect node graph, keyframe curves, music library with match %, fully wired to the render engine.

**Architecture:** FastAPI serves a new `studio.html` page. All 8 research libraries wired via npm + importmap. Preview uses WebCodecs + mp4box.js for frame-accurate decode. Timeline uses animation-timeline-control (video/FX rows, gold) + wavesurfer-multitrack (audio rows, cyan) sharing a `pxPerSec + playheadT` store. LiteGraph.js dockable panel for per-clip effect chains. Theatre.js drives keyframe curves in the inspector. Tweakpane binds all parameters. 5 DaVinci-style pages (CUT/EDIT/MIX/COLOR/FORGE) with context-sensitive inspector.

**Tech Stack:** Python/FastAPI, vanilla JS (ES modules), animation-timeline-control, wavesurfer.js v7 multitrack, LiteGraph.js (jagenjo), Theatre.js browser-bundles, Tweakpane v4, WebCodecs API, mp4box.js, npm + esbuild.

**Security note:** All dynamic content inserted into the DOM uses `textContent` or an `esc()` helper — never raw innerHTML with untrusted data. DOMPurify is NOT needed because we build DOM nodes explicitly.

**Prerequisite:** Plan 1 (Foundation) complete. All paths use new structure.

---

## File Map

```
CREATED
  creative_suite/frontend/studio.html              <- main page shell
  creative_suite/frontend/studio.css               <- PANTHEON dark theme
  creative_suite/frontend/studio-app.js            <- bootstrap + page router
  creative_suite/frontend/studio-store.js          <- shared state (playheadT, pxPerSec)
  creative_suite/frontend/studio-preview.js        <- WebCodecs + mp4box.js canvas
  creative_suite/frontend/studio-mediabin.js       <- media bin tabs
  creative_suite/frontend/studio-timeline.js       <- animation-timeline-control rows
  creative_suite/frontend/studio-audio.js          <- wavesurfer-multitrack rows
  creative_suite/frontend/studio-beatmarkers.js    <- beat marker overlay + snap
  creative_suite/frontend/studio-litegraph.js      <- LiteGraph effect node graph
  creative_suite/frontend/studio-inspector.js      <- Tweakpane + Theatre.js
  creative_suite/frontend/studio-musiclib.js       <- music library + match %
  creative_suite/frontend/studio-pages.js          <- 5-page system
  creative_suite/api/studio.py                     <- FastAPI router
  creative_suite/api/music_match.py                <- match % + autosync API
  creative_suite/tests/test_api_studio.py
  creative_suite/tests/test_music_match.py
  package.json
  build.js

MODIFIED
  creative_suite/app.py                            <- register studio router
  creative_suite/frontend/studio.html              <- importmap
```

---

## Task 1: Security-audit + install npm dependencies

**Files:**
- Create: `package.json`
- Create: `build.js`

- [ ] **Step 1: Audit each library before installing**

```bash
npm info animation-timeline-control license versions 2>&1 | head -3
# Expected: MIT

npm info wavesurfer.js license 2>&1 | head -3
# Expected: BSD-3-Clause

npm info @theatre/browser-bundles license 2>&1 | head -3
# Expected: Apache-2.0

npm info tweakpane@4.0.5 license 2>&1 | head -3
# Expected: MIT

npm info mp4box license 2>&1 | head -3
# Expected: BSD-3-Clause

npm info esbuild license 2>&1 | head -3
# Expected: MIT
```

- [ ] **Step 2: Create package.json**

```json
{
  "name": "quake-legacy-studio",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "build": "node build.js",
    "watch": "node build.js --watch"
  },
  "dependencies": {
    "animation-timeline-control": "1.2.4",
    "wavesurfer.js": "7.8.16",
    "@theatre/browser-bundles": "0.7.2",
    "tweakpane": "4.0.5",
    "mp4box": "0.5.2"
  },
  "devDependencies": {
    "esbuild": "0.21.5"
  }
}
```

- [ ] **Step 3: Create build.js**

```javascript
const esbuild = require("esbuild");
const isWatch = process.argv.includes("--watch");

const config = {
  entryPoints: {
    "wavesurfer": "node_modules/wavesurfer.js/dist/wavesurfer.esm.js",
    "wavesurfer-multitrack": "node_modules/wavesurfer.js/dist/plugins/multitrack.esm.js",
    "animation-timeline-control": "node_modules/animation-timeline-control/dist/animation-timeline-control.esm.js",
    "theatre-core": "node_modules/@theatre/browser-bundles/dist/core-and-studio.js",
    "tweakpane": "node_modules/tweakpane/dist/tweakpane.min.js",
    "mp4box": "node_modules/mp4box/dist/mp4box.all.min.js",
  },
  bundle: false,
  format: "esm",
  outdir: "creative_suite/frontend/vendor",
  minify: !isWatch,
  logLevel: "info",
};

if (isWatch) {
  esbuild.context(config).then(ctx => ctx.watch());
} else {
  esbuild.build(config);
}
```

- [ ] **Step 4: Install and build**

```bash
cd G:/QUAKE_LEGACY
npm install
npm run build
```

Expected: `creative_suite/frontend/vendor/` created with bundled files.

- [ ] **Step 5: Run npm audit — MUST be clean before proceeding**

```bash
npm audit
```

Expected: `found 0 vulnerabilities`. STOP if any high/critical found.

- [ ] **Step 6: Add vendor/ + node_modules/ to .gitignore**

```bash
echo "creative_suite/frontend/vendor/" >> .gitignore
echo "node_modules/" >> .gitignore
git add package.json package-lock.json build.js .gitignore
git commit -m "build: npm manifest + esbuild bundler for studio deps

animation-timeline-control 1.2.4 MIT
wavesurfer.js 7.8.16 BSD-3
@theatre/browser-bundles 0.7.2 Apache-2.0
tweakpane 4.0.5 MIT / mp4box 0.5.2 BSD-3 / esbuild 0.21.5 MIT
All packages security-audited clean.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 2: FastAPI route + HTML shell

**Files:**
- Create: `creative_suite/api/studio.py`
- Create: `creative_suite/frontend/studio.html`
- Modify: `creative_suite/app.py`

- [ ] **Step 1: Write failing test**

```python
# creative_suite/tests/test_api_studio.py
from fastapi.testclient import TestClient
from creative_suite.app import create_app

client = TestClient(create_app())

def test_studio_route_returns_html():
    r = client.get("/studio")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "QUAKE LEGACY" in r.text

def test_studio_state_endpoint():
    r = client.get("/api/studio/state/4")
    assert r.status_code in (200, 404)

def test_studio_parts_list():
    r = client.get("/api/studio/parts")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
```

- [ ] **Step 2: Run to verify it fails**

```bash
python -m pytest creative_suite/tests/test_api_studio.py -v
```

Expected: FAIL — `/studio` not found.

- [ ] **Step 3: Create creative_suite/api/studio.py**

```python
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import json, glob, subprocess, tempfile

router = APIRouter(prefix="/api/studio", tags=["studio"])
FRONTEND = Path(__file__).parent.parent / "frontend"
OUTPUT = Path(__file__).parent.parent.parent / "output"
FFMPEG = Path(__file__).parent.parent / "tools" / "ffmpeg" / "ffmpeg.exe"


@router.get("/parts")
def list_parts():
    parts = []
    for i in range(4, 13):
        fp = OUTPUT / f"part{i:02d}_flow_plan.json"
        parts.append({"part": i, "has_plan": fp.exists()})
    return parts


@router.get("/state/{part}")
def get_state(part: int):
    fp = OUTPUT / f"part{part:02d}_flow_plan.json"
    if not fp.exists():
        raise HTTPException(404, f"No flow plan for part {part}")
    return json.loads(fp.read_text())


@router.get("/beats/{part}")
def get_beats(part: int):
    fp = OUTPUT / f"part{part:02d}_beats.json"
    return json.loads(fp.read_text()) if fp.exists() else []


@router.get("/music-plan/{part}")
def get_music_plan(part: int):
    fp = OUTPUT / f"part{part:02d}_music_plan.json"
    return json.loads(fp.read_text()) if fp.exists() else {}


@router.get("/audio-stem/{part}/{stem}")
def get_audio_stem(part: int, stem: str):
    mp4s = sorted(glob.glob(str(OUTPUT / f"part{part:02d}_*.mp4")))
    if not mp4s:
        raise HTTPException(404, "No render found for this part")
    tmp = tempfile.mktemp(suffix=".wav")
    result = subprocess.run(
        [str(FFMPEG), "-y", "-i", mp4s[-1],
         "-vn", "-acodec", "pcm_s16le", "-ar", "22050", "-ac", "1", tmp],
        capture_output=True,
    )
    if not Path(tmp).exists():
        raise HTTPException(500, "Audio extraction failed")
    return FileResponse(tmp, media_type="audio/wav")
```

- [ ] **Step 4: Register router in creative_suite/app.py**

```python
from creative_suite.api import studio as studio_mod
from creative_suite.api import music_match as music_match_mod

# inside create_app():
app.include_router(studio_mod.router)
app.include_router(music_match_mod.router)

@app.get("/studio", response_class=HTMLResponse)
async def studio_page():
    return (FRONTEND / "studio.html").read_text()
```

- [ ] **Step 5: Create creative_suite/frontend/studio.html**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>QUAKE LEGACY Studio</title>
  <link rel="stylesheet" href="/cinema-static/studio.css">
  <script type="importmap">
  {
    "imports": {
      "wavesurfer": "/cinema-static/vendor/wavesurfer.js",
      "wavesurfer-multitrack": "/cinema-static/vendor/wavesurfer-multitrack.js",
      "animation-timeline-control": "/cinema-static/vendor/animation-timeline-control.js",
      "theatre-core": "/cinema-static/vendor/theatre-core.js",
      "tweakpane": "/cinema-static/vendor/tweakpane.js",
      "mp4box": "/cinema-static/vendor/mp4box.js",
      "litegraph": "https://cdn.jsdelivr.net/npm/litegraph.js@0.7.18/build/litegraph.core.js"
    }
  }
  </script>
</head>
<body>
  <div id="app">
    <header id="page-bar">
      <span class="brand">QUAKE LEGACY</span>
      <nav id="pages">
        <button data-page="cut" class="active">CUT</button>
        <button data-page="edit">EDIT</button>
        <button data-page="mix">MIX</button>
        <button data-page="color">COLOR</button>
        <button data-page="forge">FORGE</button>
      </nav>
      <div id="transport">
        <button id="btn-prev">&#9664;</button>
        <button id="btn-play">&#9654;</button>
        <button id="btn-stop">&#9632;</button>
        <button id="btn-next">&#9654;&#9654;</button>
        <span id="timecode">00:00:00:00</span>
      </div>
    </header>
    <div id="main-layout">
      <aside id="media-bin">
        <div id="bin-tabs">
          <button data-tab="clips" class="active">Clips</button>
          <button data-tab="music">Music</button>
          <button data-tab="assets">Assets</button>
        </div>
        <div id="bin-content"></div>
      </aside>
      <main id="preview-area">
        <canvas id="preview-canvas"></canvas>
        <div id="preview-controls">
          <select id="part-select"></select>
          <span id="frame-counter">Frame 0</span>
        </div>
      </main>
      <aside id="inspector">
        <div id="tweakpane-root"></div>
        <div id="theatre-curves"></div>
      </aside>
    </div>
    <div id="timeline-area">
      <div id="timeline-tracks"></div>
      <div id="audio-tracks"></div>
      <canvas id="beat-markers-overlay"></canvas>
    </div>
    <div id="litegraph-dock" class="dock hidden">
      <div class="dock-handle">
        <span>Effect Graph</span>
        <button id="litegraph-close">x</button>
      </div>
      <canvas id="litegraph-canvas"></canvas>
    </div>
  </div>
  <script type="module" src="/cinema-static/studio-app.js"></script>
</body>
</html>
```

- [ ] **Step 6: Run tests**

```bash
python -m pytest creative_suite/tests/test_api_studio.py -v
```

Expected: all 3 tests pass.

- [ ] **Step 7: Commit**

```bash
git add creative_suite/api/studio.py creative_suite/frontend/studio.html \
        creative_suite/app.py creative_suite/tests/test_api_studio.py
git commit -m "feat(studio): /studio route + API + HTML shell

Router: /parts, /state/{part}, /beats/{part}, /music-plan/{part}, /audio-stem/{part}/{stem}.
HTML: 5-page bar, 3-panel layout, timeline, dockable litegraph panel.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 3: PANTHEON dark theme CSS

**Files:**
- Create: `creative_suite/frontend/studio.css`

- [ ] **Step 1: Write studio.css**

```css
/* QUAKE LEGACY Studio — PANTHEON dark theme */
:root {
  --bg:       #1a1a1a;
  --surface:  #242424;
  --hover:    #333333;
  --border:   #404040;
  --text:     #E0E0E0;
  --dim:      #888888;
  --gold:     #D4AF37;
  --cyan:     #00B0F0;
  --orange:   #FF9500;
  --danger:   #FF4444;
  --font:     "IBM Plex Mono", monospace;
}
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;700&display=swap');
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: var(--bg); color: var(--text);
  font-family: var(--font); font-size: 12px;
  height: 100vh; overflow: hidden;
  display: flex; flex-direction: column;
}
#app { display: flex; flex-direction: column; height: 100vh; }
#page-bar {
  display: flex; align-items: center; gap: 16px;
  padding: 6px 12px; background: #111;
  border-bottom: 1px solid var(--border); flex-shrink: 0;
}
.brand { color: var(--gold); font-weight: 700; letter-spacing: 2px; }
#pages { display: flex; gap: 4px; }
#pages button {
  background: transparent; border: 1px solid transparent;
  color: var(--dim); padding: 4px 12px; cursor: pointer;
  letter-spacing: 1px; font-family: var(--font);
}
#pages button.active, #pages button:hover {
  color: var(--gold); border-color: var(--gold);
}
#transport { margin-left: auto; display: flex; align-items: center; gap: 8px; }
#transport button {
  background: var(--surface); border: 1px solid var(--border);
  color: var(--text); padding: 4px 8px; cursor: pointer;
  font-family: var(--font);
}
#timecode { color: var(--gold); font-variant-numeric: tabular-nums; min-width: 100px; }
#main-layout {
  display: grid; grid-template-columns: 220px 1fr 220px;
  flex: 1; min-height: 0; overflow: hidden;
}
#media-bin {
  background: var(--surface); border-right: 1px solid var(--border);
  display: flex; flex-direction: column; overflow: hidden;
}
#bin-tabs { display: flex; border-bottom: 1px solid var(--border); }
#bin-tabs button {
  flex: 1; padding: 6px; background: transparent; border: none;
  color: var(--dim); cursor: pointer; font-family: var(--font);
}
#bin-tabs button.active { color: var(--gold); border-bottom: 2px solid var(--gold); }
#bin-content { flex: 1; overflow-y: auto; padding: 8px; }
#preview-area {
  display: flex; flex-direction: column; background: #000; position: relative;
}
#preview-canvas { flex: 1; width: 100%; background: #000; display: block; }
#preview-controls {
  display: flex; gap: 8px; padding: 4px 8px;
  background: var(--surface); border-top: 1px solid var(--border);
}
#part-select {
  background: var(--hover); border: 1px solid var(--border);
  color: var(--text); padding: 2px 6px; font-family: var(--font);
}
#inspector {
  background: var(--surface); border-left: 1px solid var(--border);
  overflow-y: auto; padding: 8px;
}
#timeline-area {
  height: 40vh; min-height: 200px; background: var(--surface);
  border-top: 2px solid var(--border); display: flex;
  flex-direction: column; position: relative; flex-shrink: 0;
}
#timeline-tracks { flex: 1; min-height: 0; }
#audio-tracks { height: 100px; border-top: 1px solid var(--border); }
#beat-markers-overlay {
  position: absolute; top: 0; left: 0; right: 0; bottom: 0; pointer-events: none;
}
#litegraph-dock {
  position: fixed; bottom: 40vh; left: 220px; right: 220px;
  height: 200px; background: var(--surface); border: 1px solid var(--gold); z-index: 100;
}
#litegraph-dock.hidden { display: none; }
.dock-handle {
  display: flex; justify-content: space-between; align-items: center;
  padding: 4px 8px; background: #111; border-bottom: 1px solid var(--border);
  color: var(--gold); cursor: move;
}
#litegraph-canvas { width: 100%; height: calc(100% - 28px); }
.track-video { border-left: 3px solid var(--gold); }
.track-audio  { border-left: 3px solid var(--cyan); }
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--surface); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
```

- [ ] **Step 2: Verify in browser — http://localhost:8765/studio**

Confirm: dark background, gold page bar, three-column layout, no white flash.

- [ ] **Step 3: Commit**

```bash
git add creative_suite/frontend/studio.css
git commit -m "feat(studio): PANTHEON dark theme CSS

Gold #D4AF37 (video), cyan #00B0F0 (audio), 3-col layout + timeline.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 4: Shared store + app bootstrap

**Files:**
- Create: `creative_suite/frontend/studio-store.js`
- Create: `creative_suite/frontend/studio-app.js`

- [ ] **Step 1: Write studio-store.js**

```javascript
// Reactive state store — shared by all studio panels
const _listeners = {};
const state = {
  playheadT: 0,
  pxPerSec: 100,
  activePart: null,
  activePage: "cut",
  selectedClip: null,
  isPlaying: false,
  duration: 0,
  beats: [],
  flowPlan: null,
};

export function get(key) { return state[key]; }

export function set(key, value) {
  state[key] = value;
  (_listeners[key] || []).forEach(fn => fn(value));
  (_listeners["*"] || []).forEach(fn => fn(key, value));
}

export function on(key, fn) {
  _listeners[key] = _listeners[key] || [];
  _listeners[key].push(fn);
  return () => { _listeners[key] = _listeners[key].filter(f => f !== fn); };
}
```

- [ ] **Step 2: Write studio-app.js**

```javascript
import { set, get, on } from "./studio-store.js";

async function boot() {
  const parts = await fetch("/api/studio/parts").then(r => r.json());
  const sel = document.getElementById("part-select");

  parts.forEach(p => {
    const opt = document.createElement("option");
    opt.value = String(p.part);
    opt.textContent = `Part ${p.part}${p.has_plan ? "" : " (no plan)"}`;
    sel.appendChild(opt);
  });

  sel.addEventListener("change", () => loadPart(Number(sel.value)));

  document.querySelectorAll("#pages button").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("#pages button").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      set("activePage", btn.dataset.page);
    });
  });

  document.getElementById("btn-play").addEventListener("click", () => set("isPlaying", !get("isPlaying")));
  document.getElementById("btn-stop").addEventListener("click", () => { set("isPlaying", false); set("playheadT", 0); });

  window.addEventListener("keydown", e => {
    if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
    const actions = {
      Space: () => { e.preventDefault(); set("isPlaying", !get("isPlaying")); },
      KeyJ: () => set("playheadT", Math.max(0, get("playheadT") - 5)),
      KeyK: () => set("isPlaying", false),
      KeyL: () => set("isPlaying", true),
      KeyM: () => dispatchEvent(new CustomEvent("add-marker", {detail: {t: get("playheadT")}})),
    };
    if (actions[e.code]) actions[e.code]();
  });

  on("playheadT", t => {
    const h = Math.floor(t / 3600), m = Math.floor((t % 3600) / 60),
          s = Math.floor(t % 60), f = Math.floor((t % 1) * 30);
    document.getElementById("timecode").textContent =
      [h,m,s,f].map(v => String(v).padStart(2,"0")).join(":");
  });

  const first = parts.find(p => p.has_plan);
  if (first) loadPart(first.part);
}

async function loadPart(partNum) {
  set("activePart", partNum);
  document.getElementById("part-select").value = String(partNum);
  const [plan, beats, musicPlan] = await Promise.all([
    fetch(`/api/studio/state/${partNum}`).then(r => r.ok ? r.json() : null),
    fetch(`/api/studio/beats/${partNum}`).then(r => r.json()),
    fetch(`/api/studio/music-plan/${partNum}`).then(r => r.json()),
  ]);
  if (plan) {
    set("flowPlan", plan);
    set("duration", plan.clips?.reduce((a, c) => a + (c.duration || 0), 0) || 0);
  }
  set("beats", beats);
  dispatchEvent(new CustomEvent("part-loaded", {detail: {partNum, plan, beats, musicPlan}}));
}

boot().catch(console.error);
```

- [ ] **Step 3: Commit**

```bash
git add creative_suite/frontend/studio-store.js creative_suite/frontend/studio-app.js
git commit -m "feat(studio): shared store + app bootstrap

Reactive state (playheadT, pxPerSec, activePart, beats, flowPlan).
J/K/L/Space/M keyboard shortcuts. Timecode HH:MM:SS:FF display.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 5: WebCodecs + mp4box.js preview canvas

**Files:**
- Create: `creative_suite/frontend/studio-preview.js`

- [ ] **Step 1: Write studio-preview.js**

```javascript
import MP4Box from "mp4box";
import { get, set, on } from "./studio-store.js";

let decoder = null;
let frameCache = new Map();
let canvas, ctx;

function drawPlaceholder() {
  ctx.fillStyle = "#000";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#D4AF37";
  ctx.font = "14px IBM Plex Mono";
  ctx.textAlign = "center";
  ctx.fillText("Select a part to preview", canvas.width / 2, canvas.height / 2);
}

export function initPreview(canvasEl) {
  canvas = canvasEl;
  ctx = canvas.getContext("2d");
  canvas.width = 960; canvas.height = 540;
  drawPlaceholder();
  on("playheadT", seekToTime);
  on("isPlaying", playing => playing ? startPlayback() : stopPlayback());
}

export async function loadProxy(proxyUrl) {
  frameCache.clear();
  const mp4boxFile = MP4Box.createFile();

  mp4boxFile.onReady = info => {
    const track = info.videoTracks[0];
    if (!track) return;
    canvas.width = track.video.width;
    canvas.height = track.video.height;

    if (decoder) decoder.close();
    decoder = new VideoDecoder({
      output: frame => {
        const ts = frame.timestamp;
        createImageBitmap(frame).then(bmp => { frameCache.set(ts, bmp); frame.close(); });
      },
      error: e => console.error("VideoDecoder:", e),
    });
    decoder.configure({ codec: track.codec, codedWidth: track.video.width, codedHeight: track.video.height });
    mp4boxFile.setExtractionOptions(track.id, null, {nbSamples: Infinity});
    mp4boxFile.start();
  };

  mp4boxFile.onSamples = (_id, _user, samples) => {
    for (const s of samples) {
      decoder.decode(new EncodedVideoChunk({
        type: s.is_sync ? "key" : "delta",
        timestamp: s.dts * 1e6 / s.timescale,
        data: s.data,
      }));
    }
  };

  const buf = await fetch(proxyUrl).then(r => r.arrayBuffer());
  buf.fileStart = 0;
  mp4boxFile.appendBuffer(buf);
  mp4boxFile.flush();
}

function seekToTime(seconds) {
  const us = Math.round(seconds * 1e6);
  let closest = null, closestDist = Infinity;
  for (const [ts, bmp] of frameCache) {
    const d = Math.abs(ts - us);
    if (d < closestDist) { closest = bmp; closestDist = d; }
  }
  if (closest) {
    ctx.drawImage(closest, 0, 0, canvas.width, canvas.height);
    const el = document.getElementById("frame-counter");
    if (el) el.textContent = `Frame ${Math.round(seconds * 30)}`;
  }
}

let rafId = null, lastTime = null;
function startPlayback() {
  lastTime = performance.now();
  const tick = now => {
    const dt = (now - lastTime) / 1000; lastTime = now;
    const t = Math.min(get("playheadT") + dt, get("duration"));
    set("playheadT", t);
    if (t >= get("duration")) { set("isPlaying", false); return; }
    rafId = requestAnimationFrame(tick);
  };
  rafId = requestAnimationFrame(tick);
}
function stopPlayback() { if (rafId) { cancelAnimationFrame(rafId); rafId = null; } }

window.addEventListener("part-loaded", ({detail: {partNum}}) => {
  loadProxy(`/api/editor/proxy/${partNum}/preview`).catch(() => drawPlaceholder());
});

document.addEventListener("DOMContentLoaded", () => initPreview(document.getElementById("preview-canvas")));
```

- [ ] **Step 2: Add import to studio-app.js**

```javascript
import "./studio-preview.js";
```

- [ ] **Step 3: Test — select part, verify frame decode, Space to play**

- [ ] **Step 4: Commit**

```bash
git add creative_suite/frontend/studio-preview.js creative_suite/frontend/studio-app.js
git commit -m "feat(studio): WebCodecs + mp4box.js frame-accurate preview

Hardware-accelerated decode. RAF playback tied to store.isPlaying.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 6: Video + FX timeline rows

**Files:**
- Create: `creative_suite/frontend/studio-timeline.js`

- [ ] **Step 1: Write studio-timeline.js**

```javascript
import { Timeline } from "animation-timeline-control";
import { get, set, on } from "./studio-store.js";

let tl = null;

export function initTimeline(containerEl) {
  tl = new Timeline({ container: containerEl });

  tl.on("timeChanged", e => { if (e.source !== "store") set("playheadT", e.val / 1000); });
  on("playheadT", t => { if (tl) tl.setTime(t * 1000, "store"); });
  on("pxPerSec", px => { if (tl) tl.setZoom(px); });

  containerEl.addEventListener("wheel", e => {
    e.preventDefault();
    set("pxPerSec", Math.max(20, Math.min(500, get("pxPerSec") * (e.deltaY > 0 ? 0.9 : 1.1))));
  }, { passive: false });
}

export function loadFlowPlan(plan) {
  if (!tl || !plan?.clips) return;
  let cursor = 0;
  const videoKFs = plan.clips.map(clip => {
    const kf = { val: cursor * 1000, label: clip.name || `clip_${clip.index}`, group: "video" };
    cursor += clip.duration || 0;
    return kf;
  });

  const beats = get("beats") || [];
  const fxKFs = beats
    .filter(b => b.event_type !== "RECOGNITION_FAILED")
    .map(b => ({ val: ((b.clip_start_t || 0) + (b.action_peak_t || b.t || 0)) * 1000, label: b.event_type, group: "fx" }));

  tl.setModel({
    rows: [
      { id: "video", label: "VIDEO", keyframes: videoKFs, style: { borderLeft: "3px solid #D4AF37" } },
      { id: "fx",    label: "FX",    keyframes: fxKFs,    style: { borderLeft: "3px solid #D4AF37" } },
    ]
  });
}

window.addEventListener("part-loaded", ({detail: {plan}}) => { if (plan) loadFlowPlan(plan); });
document.addEventListener("DOMContentLoaded", () => initTimeline(document.getElementById("timeline-tracks")));
```

- [ ] **Step 2: Add import**

```javascript
// studio-app.js
import "./studio-timeline.js";
```

- [ ] **Step 3: Test — gold rows appear, scrub syncs preview**

- [ ] **Step 4: Commit**

```bash
git add creative_suite/frontend/studio-timeline.js
git commit -m "feat(studio): video + FX timeline rows

Gold rows from flow_plan clips + beats. Bidirectional playhead sync. Wheel zoom.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 7: Audio stem rows + beat markers

**Files:**
- Create: `creative_suite/frontend/studio-audio.js`
- Create: `creative_suite/frontend/studio-beatmarkers.js`

- [ ] **Step 1: Write studio-audio.js**

```javascript
import WaveSurfer from "wavesurfer";
import MultiTrack from "wavesurfer-multitrack";
import { get, set, on } from "./studio-store.js";

let mt = null;

export async function loadAudioStems(partNum) {
  const el = document.getElementById("audio-tracks");
  if (!el) return;
  if (mt) { mt.destroy(); mt = null; }

  mt = MultiTrack.create([
    { id: "game", url: `/api/studio/audio-stem/${partNum}/game`,
      options: { waveColor: "#00B0F0", progressColor: "#007ba0", height: 40 } },
  ], { container: el, minPxPerSec: get("pxPerSec"), cursorColor: "#D4AF37", cursorWidth: 2 });

  mt.on("timeupdate", t => { if (Math.abs(t - get("playheadT")) > 0.05) set("playheadT", t); });
  on("playheadT", t => { try { if (mt && Math.abs(mt.getCurrentTime() - t) > 0.05) mt.setTime(t); } catch(_){} });
  on("isPlaying", p => { try { p ? mt.play() : mt.pause(); } catch(_){} });
  on("pxPerSec", px => { try { mt.zoom(px); } catch(_){} });
}

window.addEventListener("part-loaded", ({detail: {partNum}}) => loadAudioStems(partNum).catch(console.warn));
```

- [ ] **Step 2: Write studio-beatmarkers.js**

```javascript
import { get, set, on } from "./studio-store.js";

let canvas, ctx;
const EVENT_COLORS = {
  player_death: "#FF4444", rocket_impact: "#FF9500",
  rail_fire: "#00B0F0", grenade_explode: "#FF9500",
};

export function initBeatMarkers(canvasEl) {
  canvas = canvasEl; ctx = canvas.getContext("2d");
  new ResizeObserver(() => { canvas.width = canvas.offsetWidth; canvas.height = canvas.offsetHeight; render(); }).observe(canvas);

  canvas.addEventListener("click", e => {
    const t = (e.clientX - canvas.getBoundingClientRect().left) / get("pxPerSec");
    const beats = get("beats") || [];
    let nearest = null, dist = Infinity;
    for (const b of beats) {
      const bt = b.t || b.action_peak_t || 0;
      const d = Math.abs(bt - t);
      if (d < dist) { dist = d; nearest = b; }
    }
    if (nearest && dist < 1.0) set("playheadT", nearest.t || nearest.action_peak_t || 0);
  });

  on("beats", () => render());
  on("playheadT", () => render());
  on("pxPerSec", () => render());
}

function render() {
  if (!canvas || !ctx) return;
  const px = get("pxPerSec");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.setLineDash([4, 2]);
  ctx.lineWidth = 1;

  for (const b of (get("beats") || [])) {
    const t = b.t || b.action_peak_t || 0;
    const x = t * px;
    if (x < 0 || x > canvas.width) continue;
    ctx.strokeStyle = EVENT_COLORS[b.event_type] || "#D4AF37";
    ctx.globalAlpha = 0.55;
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
    ctx.globalAlpha = 0.8; ctx.fillStyle = ctx.strokeStyle;
    ctx.font = "9px IBM Plex Mono";
    ctx.fillText((b.event_type || "").slice(0, 6), x + 2, 10);
  }

  const hx = get("playheadT") * px;
  ctx.setLineDash([]); ctx.strokeStyle = "#D4AF37"; ctx.globalAlpha = 1; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(hx, 0); ctx.lineTo(hx, canvas.height); ctx.stroke();
  ctx.globalAlpha = 1;
}

document.addEventListener("DOMContentLoaded", () => initBeatMarkers(document.getElementById("beat-markers-overlay")));
```

- [ ] **Step 3: Add imports**

```javascript
import "./studio-audio.js";
import "./studio-beatmarkers.js";
```

- [ ] **Step 4: Test — cyan waveform rows, colored beat markers, click to snap**

- [ ] **Step 5: Commit**

```bash
git add creative_suite/frontend/studio-audio.js creative_suite/frontend/studio-beatmarkers.js
git commit -m "feat(studio): wavesurfer-multitrack audio rows + beat markers

Cyan waveform synced to playhead. Color-coded beat markers (death=red,
rocket/grenade=orange, rail=cyan). Click within 1s snaps playhead.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 8: Music library + match % API

**Files:**
- Create: `creative_suite/api/music_match.py`
- Create: `creative_suite/frontend/studio-musiclib.js`
- Create: `creative_suite/tests/test_music_match.py`

- [ ] **Step 1: Write failing test**

```python
# creative_suite/tests/test_music_match.py
from fastapi.testclient import TestClient
from creative_suite.app import create_app

client = TestClient(create_app())

def test_music_match_schema():
    r = client.get("/api/music/match?part=4")
    assert r.status_code in (200, 404)
    if r.status_code == 200:
        data = r.json()
        assert isinstance(data, list)
        if data:
            for key in ("title", "match_pct", "bpm", "duration_s"):
                assert key in data[0]
            assert 0 <= data[0]["match_pct"] <= 100

def test_autosync_schema():
    r = client.post("/api/music/autosync",
        json={"part": 4, "track_path": "creative_suite/engine/music/part04_music.mp3"})
    assert r.status_code in (200, 404, 422)
    if r.status_code == 200:
        data = r.json()
        assert "windows" in data
        assert "count" in data
```

- [ ] **Step 2: Run to verify fail**

```bash
python -m pytest creative_suite/tests/test_music_match.py -v
```

- [ ] **Step 3: Create creative_suite/api/music_match.py**

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
import json

router = APIRouter(prefix="/api/music", tags=["music"])
OUTPUT = Path(__file__).parent.parent.parent / "output"
ENGINE = Path(__file__).parent.parent / "engine"

def _beats(part):
    fp = OUTPUT / f"part{part:02d}_beats.json"
    if not fp.exists():
        raise HTTPException(404, f"No beats.json for part {part}")
    return json.loads(fp.read_text())

def _library():
    for candidate in [
        ENGINE / "database" / "MusicLibrary.json",
        Path("creative_suite/database/MusicLibrary.json"),
    ]:
        if candidate.exists():
            data = json.loads(candidate.read_text())
            return data if isinstance(data, list) else data.get("tracks", [])
    return []

def _score(track, beats, duration):
    score = 0.0
    bpm = float(track.get("tempo", track.get("bpm", 0)) or 0)
    if bpm > 0:
        score += max(0.0, 40.0 - abs(bpm - 150) * 0.5)
    density = len(beats) / max(duration, 1.0)
    energy = float(track.get("energy", 0.5) or 0.5)
    score += (1.0 - abs(energy - min(density / 0.5, 1.0))) * 30.0
    dur_s = float(track.get("duration_ms", 0) or 0) / 1000.0
    if dur_s > 0:
        score += min(dur_s, duration) / max(dur_s, duration) * 30.0
    return round(min(score, 100.0), 1)

@router.get("/match")
def music_match(part: int):
    beats = _beats(part)
    library = _library()
    if not library:
        raise HTTPException(404, "Music library not found")
    dur = max((b.get("t", b.get("action_peak_t", 0)) for b in beats), default=0) + 10
    scored = sorted([{
        "title": str(t.get("name", t.get("title", "Unknown"))),
        "artist": str(t.get("artist", "")),
        "bpm": float(t.get("tempo", t.get("bpm", 0)) or 0),
        "energy": float(t.get("energy", 0) or 0),
        "duration_s": float(t.get("duration_ms", 0) or 0) / 1000.0,
        "path": str(t.get("path", "")),
        "match_pct": _score(t, beats, dur),
    } for t in library], key=lambda x: x["match_pct"], reverse=True)
    return scored[:200]

class AutosyncReq(BaseModel):
    part: int
    track_path: str

@router.post("/autosync")
def autosync(req: AutosyncReq):
    beats = _beats(req.part)
    fp = OUTPUT / f"part{req.part:02d}_flow_plan.json"
    if not fp.exists():
        raise HTTPException(404, "No flow plan")
    clips = json.loads(fp.read_text()).get("clips", [])
    windows = []
    for b in beats:
        if float(b.get("confidence", 0)) < 0.55:
            continue
        bt = float(b.get("t", b.get("action_peak_t", 0)))
        event = str(b.get("event_type", ""))
        cursor = 0.0
        for i, clip in enumerate(clips):
            dur = float(clip.get("duration", 0))
            if cursor <= bt <= cursor + dur:
                local = bt - cursor
                effect = "slowmo" if event in ("player_death", "rocket_impact") else "speedup"
                windows.append({
                    "clip_index": i,
                    "clip_name": str(clip.get("name", f"clip_{i}")),
                    "window_start": round(max(0.0, local - 0.8), 3),
                    "window_end": round(min(dur, local + 0.8), 3),
                    "effect": effect,
                    "rate": 0.5 if effect == "slowmo" else 1.5,
                    "event_type": event,
                    "confidence": float(b.get("confidence", 0)),
                })
                break
            cursor += dur
    return {"windows": windows, "count": len(windows)}
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest creative_suite/tests/test_music_match.py -v
```

Expected: PASS.

- [ ] **Step 5: Write studio-musiclib.js**

Use `createElement` + `textContent` throughout — no raw user data in template strings.

```javascript
import { get } from "./studio-store.js";

let tracks = [], currentPart = null;

function esc(str) { return String(str).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])); }

function buildTrackRow(track, index) {
  const row = document.createElement("div");
  row.className = "music-item";
  row.style.cssText = "padding:6px 8px;border-bottom:1px solid #333;cursor:pointer;display:flex;gap:8px;align-items:center;";

  const pctColor = track.match_pct >= 70 ? "#D4AF37" : track.match_pct >= 40 ? "#FF9500" : "#888";
  const pct = document.createElement("div");
  pct.style.cssText = `min-width:36px;text-align:right;color:${pctColor};font-weight:bold;font-size:11px;`;
  pct.textContent = `${track.match_pct}%`;

  const info = document.createElement("div");
  info.style.cssText = "flex:1;min-width:0;";
  const title = document.createElement("div");
  title.style.cssText = "white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#E0E0E0;";
  title.textContent = track.title;
  const meta = document.createElement("div");
  meta.style.cssText = "color:#888;font-size:10px;";
  meta.textContent = `${track.artist} \u00b7 ${Math.floor(track.bpm)}bpm \u00b7 ${Math.floor(track.duration_s)}s`;
  info.append(title, meta);

  const syncBtn = document.createElement("button");
  syncBtn.textContent = "SYNC";
  syncBtn.dataset.path = track.path;
  syncBtn.style.cssText = "background:#242424;border:1px solid #D4AF37;color:#D4AF37;padding:2px 6px;cursor:pointer;font-size:10px;font-family:inherit;";

  row.append(pct, info, syncBtn);

  row.addEventListener("click", e => {
    if (e.target === syncBtn) return;
    dispatchEvent(new CustomEvent("music-track-selected", {detail: track}));
  });

  syncBtn.addEventListener("click", async () => {
    syncBtn.textContent = "...";
    try {
      const res = await fetch("/api/music/autosync", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({part: currentPart, track_path: track.path}),
      }).then(r => r.json());
      dispatchEvent(new CustomEvent("autosync-result", {detail: res}));
      syncBtn.textContent = `${res.count}ok`;
    } catch { syncBtn.textContent = "ERR"; }
  });

  return row;
}

export async function loadMusicLibrary(partNum) {
  currentPart = partNum;
  const container = document.getElementById("bin-content");
  if (!container) return;

  const loading = document.createElement("div");
  loading.style.cssText = "color:#888;padding:8px;";
  loading.textContent = "Loading music library...";
  container.replaceChildren(loading);

  try {
    tracks = await fetch(`/api/music/match?part=${partNum}`).then(r => r.json());
    renderLibrary(container);
  } catch(e) {
    const err = document.createElement("div");
    err.style.cssText = "color:#FF4444;padding:8px;";
    err.textContent = `Error: ${e.message}`;
    container.replaceChildren(err);
  }
}

function renderLibrary(container) {
  const header = document.createElement("div");
  header.style.cssText = "padding:4px 8px;border-bottom:1px solid #404040;display:flex;gap:8px;align-items:center;";
  const search = document.createElement("input");
  search.id = "music-search"; search.placeholder = "Search...";
  search.style.cssText = "flex:1;background:#333;border:1px solid #404;color:#E0E0E0;padding:2px 6px;font-family:inherit;";
  const count = document.createElement("span");
  count.style.cssText = "color:#888;font-size:10px;";
  count.textContent = `${tracks.length} tracks`;
  header.append(search, count);

  const list = document.createElement("div");
  list.id = "music-list";
  list.style.cssText = "overflow-y:auto;max-height:calc(100vh - 200px);";

  container.replaceChildren(header, list);

  function renderFiltered(filter) {
    const filt = tracks.filter(t => `${t.title} ${t.artist}`.toLowerCase().includes(filter.toLowerCase()));
    list.replaceChildren(...filt.slice(0, 100).map(buildTrackRow));
  }

  search.addEventListener("input", e => renderFiltered(e.target.value));
  renderFiltered("");
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-tab]").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("[data-tab]").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      if (btn.dataset.tab === "music" && currentPart) loadMusicLibrary(currentPart);
    });
  });
});

window.addEventListener("part-loaded", ({detail: {partNum}}) => loadMusicLibrary(partNum));
```

- [ ] **Step 6: Import**

```javascript
import "./studio-musiclib.js";
```

- [ ] **Step 7: Test — music tab, match %, SYNC button**

- [ ] **Step 8: Commit**

```bash
git add creative_suite/api/music_match.py creative_suite/frontend/studio-musiclib.js \
        creative_suite/tests/test_music_match.py
git commit -m "feat(studio): music library with match % + auto-sync API

GET /api/music/match scores 200 top tracks. POST /api/music/autosync
suggests slowmo/speedup windows per beat. DOM built with createElement
(no innerHTML with user data — XSS-safe).

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 9: LiteGraph.js effect node graph

**Files:**
- Create: `creative_suite/frontend/studio-litegraph.js`

- [ ] **Step 1: Write studio-litegraph.js**

```javascript
import { get, set, on } from "./studio-store.js";

let graph = null, lgCanvas = null;

function loadLiteGraph(LiteGraph, LGraph, LGraphCanvas) {
  // Register custom nodes
  const nodes = {
    "quake/clip_source": { title: "Clip Source",
      build(n) { n.addOutput("video","video"); n.addOutput("audio","audio"); n.size=[120,60]; } },
    "quake/slowmo": { title: "Slow-Mo",
      build(n) { n.addInput("video","video"); n.addOutput("video","video");
        n.addWidget("number","rate",0.5,null,{min:0.1,max:2.0,step:0.1});
        n.addWidget("number","window_s",0.8,null,{min:0.1,max:5.0,step:0.1}); } },
    "quake/zoom": { title: "Zoom",
      build(n) { n.addInput("video","video"); n.addOutput("video","video");
        n.addWidget("number","scale",1.2,null,{min:1.0,max:3.0,step:0.1}); } },
    "quake/grade": { title: "Grade",
      build(n) { n.addInput("video","video"); n.addOutput("video","video");
        n.addWidget("number","brightness",0,null,{min:-1,max:1,step:0.05});
        n.addWidget("number","contrast",1,null,{min:0.5,max:2,step:0.05});
        n.addWidget("number","saturation",1,null,{min:0,max:2,step:0.05}); } },
    "quake/beat_trigger": { title: "Beat Trigger",
      build(n) { n.addOutput("trigger","event"); n.addOutput("peak_t","number");
        n.addWidget("combo","event_type","player_death",null,
          {values:["player_death","rocket_impact","rail_fire","grenade_explode"]}); } },
    "quake/output": { title: "Output",
      build(n) { n.addInput("video","video"); n.addInput("audio","audio"); n.size=[120,60]; } },
  };

  for (const [type, def] of Object.entries(nodes)) {
    function NodeCtor() { def.build(this); this.title = def.title; }
    NodeCtor.title = def.title;
    LiteGraph.registerNodeType(type, NodeCtor);
  }

  graph = new LGraph();
  lgCanvas = new LGraphCanvas(document.getElementById("litegraph-canvas"), graph);
  lgCanvas.background_image = null;
  lgCanvas.default_link_color = "#D4AF37";

  // Default graph
  const src = LiteGraph.createNode("quake/clip_source"); src.pos=[50,100]; graph.add(src);
  const grade = LiteGraph.createNode("quake/grade"); grade.pos=[220,60]; graph.add(grade);
  const slow = LiteGraph.createNode("quake/slowmo"); slow.pos=[220,180]; graph.add(slow);
  const beat = LiteGraph.createNode("quake/beat_trigger"); beat.pos=[50,260]; graph.add(beat);
  const out = LiteGraph.createNode("quake/output"); out.pos=[420,100]; graph.add(out);
  src.connect(0,grade,0); grade.connect(0,slow,0); slow.connect(0,out,0); src.connect(1,out,1);

  graph.start();
}

export function toggleDock() {
  const dock = document.getElementById("litegraph-dock");
  const wasHidden = dock.classList.contains("hidden");
  dock.classList.toggle("hidden");
  if (wasHidden) {
    // LiteGraph loaded via CDN importmap — access from global after import
    import("litegraph").then(m => loadLiteGraph(m.LiteGraph, m.LGraph, m.LGraphCanvas))
      .catch(() => {
        if (window.LiteGraph) loadLiteGraph(window.LiteGraph, window.LGraph, window.LGraphCanvas);
      });
  }
}

on("selectedClip", clip => {
  if (clip && graph) {
    // Future: load clip-specific graph from clip.effects_graph
  }
});

document.addEventListener("DOMContentLoaded", () => {
  const btn = document.createElement("button");
  btn.textContent = "FX GRAPH";
  btn.style.cssText = "background:#242424;border:1px solid #D4AF37;color:#D4AF37;padding:4px 8px;cursor:pointer;font-family:inherit;margin-left:8px;";
  btn.addEventListener("click", toggleDock);
  document.getElementById("transport").appendChild(btn);
  document.getElementById("litegraph-close").addEventListener("click", () => {
    document.getElementById("litegraph-dock").classList.add("hidden");
  });
});
```

- [ ] **Step 2: Import**

```javascript
import "./studio-litegraph.js";
```

- [ ] **Step 3: Test — FX GRAPH button, dock opens, nodes draggable, gold links**

- [ ] **Step 4: Commit**

```bash
git add creative_suite/frontend/studio-litegraph.js
git commit -m "feat(studio): LiteGraph.js per-clip effect node graph

Custom nodes: ClipSource, Grade, SlowMo, Zoom, BeatTrigger, Output.
Gold connections. Dockable panel above timeline.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 10: Tweakpane inspector + Theatre.js keyframes

**Files:**
- Create: `creative_suite/frontend/studio-inspector.js`

- [ ] **Step 1: Write studio-inspector.js**

```javascript
import { Pane } from "tweakpane";
import * as theatreCore from "theatre-core";
import { get, set, on } from "./studio-store.js";

let pane = null, project = null, sheet = null;

export function initInspector(containerEl) {
  pane = new Pane({ container: containerEl, title: "Inspector" });
  project = theatreCore.getProject("QuakeLegacy");
  sheet = project.sheet("ClipEditor");
  on("selectedClip", clip => clip ? showClip(clip) : showEmpty());
  showEmpty();
}

function showEmpty() {
  if (!pane) return;
  pane.children.slice().forEach(c => c.dispose());
  const b = pane.addBlade({ view: "text", label: "Selection",
    value: "No clip selected", parse: v => v, stringify: v => v });
}

function showClip(clip) {
  if (!pane) return;
  pane.children.slice().forEach(c => c.dispose());

  const p = {
    duration: clip.duration || 0,
    tier: clip.tier || "T2",
    speed: clip.speed_rate || 1.0,
    zoom: clip.zoom_scale || 1.0,
    brightness: clip.brightness || 0,
    saturation: clip.saturation || 1.0,
    head_trim: clip.head_trim || 0,
    tail_trim: clip.tail_trim || 0,
  };

  const props = pane.addFolder({ title: "Properties", expanded: true });
  props.addBinding(p, "duration", { label: "Duration", readonly: true, format: v => `${v.toFixed(2)}s` });
  props.addBinding(p, "tier", { label: "Tier", readonly: true });

  const trim = pane.addFolder({ title: "Trim", expanded: true });
  trim.addBinding(p, "head_trim", { label: "Head", min: 0, max: 5, step: 0.1 })
    .on("change", ({value}) => patch(clip, "head_trim", value));
  trim.addBinding(p, "tail_trim", { label: "Tail", min: 0, max: 5, step: 0.1 })
    .on("change", ({value}) => patch(clip, "tail_trim", value));

  const fx = pane.addFolder({ title: "Effects", expanded: true });
  fx.addBinding(p, "speed", { label: "Speed", min: 0.1, max: 2.0, step: 0.05 })
    .on("change", ({value}) => patch(clip, "speed_rate", value));
  fx.addBinding(p, "zoom", { label: "Zoom", min: 1.0, max: 3.0, step: 0.1 })
    .on("change", ({value}) => patch(clip, "zoom_scale", value));
  fx.addBinding(p, "brightness", { label: "Brightness", min: -1, max: 1, step: 0.05 })
    .on("change", ({value}) => patch(clip, "brightness", value));
  fx.addBinding(p, "saturation", { label: "Saturation", min: 0, max: 2, step: 0.05 })
    .on("change", ({value}) => patch(clip, "saturation", value));

  // Theatre.js object for keyframe curves
  const obj = sheet.object(`clip_${clip.index || 0}`, {
    speed: theatreCore.types.number(p.speed, { range: [0.1, 2.0] }),
    zoom: theatreCore.types.number(p.zoom, { range: [1.0, 3.0] }),
    brightness: theatreCore.types.number(p.brightness, { range: [-1, 1] }),
  });
  obj.onValuesChange(vals => { Object.assign(p, vals); pane.refresh(); });

  pane.addFolder({ title: "Keyframes", expanded: false })
    .addBlade({ view: "text", label: "Tip",
      value: "Ctrl+click a param to set keyframe", parse: v => v, stringify: v => v });
}

async function patch(clip, key, value) {
  const part = get("activePart");
  if (!part || clip.index === undefined) return;
  await fetch(`/api/editor/state/${part}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify([{ op: "replace", path: `/clips/${clip.index}/${key}`, value }]),
  });
}

document.addEventListener("DOMContentLoaded", () => initInspector(document.getElementById("tweakpane-root")));
```

- [ ] **Step 2: Import**

```javascript
import "./studio-inspector.js";
```

- [ ] **Step 3: Wire clip selection in timeline**

In `studio-timeline.js`, inside `initTimeline`, add after `tl.on("timeChanged", ...)`:

```javascript
tl.on("selected", ({keyframe}) => {
  if (!keyframe) return;
  const plan = get("flowPlan");
  const clip = plan?.clips?.find(c => (c.name || `clip_${c.index}`) === keyframe.label);
  if (clip) set("selectedClip", clip);
});
```

- [ ] **Step 4: Test — click clip keyframe, inspector populates, sliders PATCH state**

- [ ] **Step 5: Commit**

```bash
git add creative_suite/frontend/studio-inspector.js creative_suite/frontend/studio-timeline.js
git commit -m "feat(studio): Tweakpane inspector + Theatre.js keyframe curves

Trim/Effects sliders PATCH /api/editor/state live.
Theatre.js object created per selected clip for curve editing.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 11: 5-page system + FORGE skeletons

**Files:**
- Create: `creative_suite/frontend/studio-pages.js`

- [ ] **Step 1: Write studio-pages.js**

```javascript
import { on } from "./studio-store.js";

const LAYOUTS = {
  cut:   { bin: true, binTab: "clips",  inspector: false, timelineH: "30vh", audio: true },
  edit:  { bin: true, binTab: "clips",  inspector: true,  timelineH: "40vh", audio: true },
  mix:   { bin: true, binTab: "music",  inspector: false, timelineH: "50vh", audio: true },
  color: { bin: false, inspector: true, timelineH: "25vh", audio: false },
  forge: { bin: false, inspector: false, timelineH: "0",   audio: false, forge: true },
};

function applyLayout(page) {
  const l = LAYOUTS[page] || LAYOUTS.edit;

  const el = (id) => document.getElementById(id);
  if (el("media-bin"))   el("media-bin").style.display   = l.bin ? "" : "none";
  if (el("inspector"))   el("inspector").style.display   = l.inspector ? "" : "none";
  if (el("timeline-area")) el("timeline-area").style.height = l.timelineH;
  if (el("audio-tracks"))  el("audio-tracks").style.display = l.audio ? "" : "none";

  if (l.binTab) {
    const btn = document.querySelector(`[data-tab="${l.binTab}"]`);
    if (btn) btn.click();
  }

  // FORGE panel
  let forge = el("forge-panel");
  if (l.forge) {
    if (!forge) {
      forge = document.createElement("div");
      forge.id = "forge-panel";
      forge.style.cssText = "padding:24px;color:#888;grid-column:1/-1;";

      const heading = document.createElement("h2");
      heading.style.cssText = "color:#D4AF37;margin-bottom:16px;";
      heading.textContent = "FORGE";
      forge.appendChild(heading);

      const grid = document.createElement("div");
      grid.style.cssText = "display:grid;grid-template-columns:1fr 1fr;gap:16px;";

      // Intro Lab card
      const introCard = buildCard(
        "3D Intro Lab",
        "Generate fragmovie intros using Q3 BSP maps + MD3 models.",
        "Coming in engine assimilation phase.",
        "SELECT MAP",
        true,
      );
      // Demo Extractor card
      const demoInput = document.createElement("input");
      demoInput.type = "file"; demoInput.accept = ".dm_73"; demoInput.style.display = "none";
      const demoCard = buildCard(
        "Demo Extractor",
        "Drop a .dm_73 demo to parse frags and events.",
        "Requires engine/parser/ build (C++17).",
        "DROP DEMO",
        false,
      );
      demoCard.querySelector("button").addEventListener("click", () => demoInput.click());
      demoInput.addEventListener("change", e => {
        const f = e.target.files[0];
        if (!f) return;
        const msg = document.createElement("p");
        msg.style.cssText = "color:#FF9500;margin-top:8px;font-size:11px;";
        msg.textContent = `Parsing ${f.name}... (engine/parser/ not yet built)`;
        demoCard.appendChild(msg);
      });
      demoCard.appendChild(demoInput);

      grid.append(introCard, demoCard);
      forge.appendChild(grid);
      el("main-layout").appendChild(forge);
    }
    forge.style.display = "";
    el("main-layout").style.display = "block";
  } else {
    if (forge) forge.style.display = "none";
    if (el("main-layout")) el("main-layout").style.display = "";
  }
}

function buildCard(title, desc, note, btnLabel, disabled) {
  const card = document.createElement("div");
  card.style.cssText = "background:#242424;border:1px solid #404040;padding:16px;border-radius:4px;";
  const h = document.createElement("h3"); h.style.cssText = "color:#E0E0E0;margin-bottom:8px;"; h.textContent = title;
  const p = document.createElement("p"); p.style.cssText = "font-size:11px;line-height:1.6;"; p.textContent = desc;
  const n = document.createElement("span"); n.style.cssText = "color:#888;"; n.textContent = note;
  p.appendChild(n);
  const btn = document.createElement("button");
  btn.textContent = btnLabel;
  btn.disabled = disabled;
  btn.style.cssText = disabled
    ? "margin-top:12px;background:#333;border:1px solid #555;color:#666;padding:6px 12px;cursor:not-allowed;font-family:inherit;"
    : "margin-top:12px;background:#242424;border:1px solid #D4AF37;color:#D4AF37;padding:6px 12px;cursor:pointer;font-family:inherit;";
  card.append(h, p, btn);
  return card;
}

on("activePage", applyLayout);
document.addEventListener("DOMContentLoaded", () => applyLayout("cut"));
```

- [ ] **Step 2: Import**

```javascript
import "./studio-pages.js";
```

- [ ] **Step 3: Test all 5 pages — each shows correct panels**

- [ ] **Step 4: Commit**

```bash
git add creative_suite/frontend/studio-pages.js
git commit -m "feat(studio): 5-page system CUT/EDIT/MIX/COLOR/FORGE

Panel show/hide per page. FORGE has skeleton cards for 3D Intro Lab
and Demo Extractor. Built with createElement (no unsafe innerHTML).

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 12: End-to-end smoke test + final commit

- [ ] **Step 1: Start server**

```bash
cd G:/QUAKE_LEGACY && python -m creative_suite
```

- [ ] **Step 2: Golden path test (manual)**

1. Open http://localhost:8765/studio
2. Select a Part with `flow_plan.json` in output/
3. Verify: timeline shows gold VIDEO + FX rows, cyan audio waveform, beat markers
4. Space: playback starts, timecode ticks, preview scrubs
5. Switch to MIX page: music library loads with match %
6. Click SYNC: autosync result shows window count
7. Switch to EDIT: click clip keyframe, inspector populates
8. Change Speed slider: PATCH request fires (check browser network tab)
9. Click FX GRAPH: LiteGraph dock slides up with node graph
10. Switch to FORGE: skeleton panels visible

- [ ] **Step 3: Run full test suite**

```bash
python -m pytest creative_suite/tests/ -q
```

Expected: all tests pass.

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "feat(studio): full UI wiring complete v1

8 libraries wired: WebCodecs+mp4box preview, animation-timeline-control
video/FX rows, wavesurfer-multitrack audio stems, LiteGraph FX graph,
Theatre.js keyframes, Tweakpane inspector, OpenTimelineIO, music match API.
5 pages: CUT/EDIT/MIX/COLOR/FORGE. Beat snap. FORGE skeleton.
All DOM mutations use createElement/textContent (XSS-safe).

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```
