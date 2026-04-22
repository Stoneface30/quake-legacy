# PANTHEON Cockpit v2 — Unified Nav Shell

> **For agentic workers:** Use `superpowers:subagent-driven-development` or `superpowers:executing-plans` to implement task-by-task. Steps use `- [ ]` syntax for tracking.

**Goal:** Replace the flat 6-item STUDIO sidebar with a 3-mode shell (STUDIO / LAB / CREATIVE) at `/studio`, wiring all 20 panels to 14 existing API routers.

**Architecture:** Mode switch in the header drives sidebar re-render and panel mount/unmount via nested NAV config in `studio-pages.js`. `StudioStore` gains `activeMode` + `modePage` (last page per mode). 15 new panel JS files follow `{ mount(slot), unmount() }` contract. Only one new backend endpoint: `GET /api/forge/demos`.

**Tech Stack:** Vanilla ES5 JS, FastAPI/Python. No new npm. Full panel source code in `docs/Unified Nav Shell Design v2.html` sections 05–13.

**Pre-implementation questions (answer before Phase 3):**
- Q1: Does an in-browser MD3 viewer module exist? If not, ship download-link placeholder.
- Q2: Does `/api/engine/graphify` exist? If not, no-op the REBUILD button in LAB-Graph.

---

## File Map

### Modified
| File | Change |
|---|---|
| `creative_suite/app.py` | Root `GET /` to 307 `/studio`; add engine-graph static mount |
| `creative_suite/frontend/studio-store.js` | Add `activeMode`, `modePage`, `SET_ACTIVE_MODE`, update `SET_ACTIVE_PAGE` |
| `creative_suite/frontend/studio.html` | Full replacement — mode switch + dynamic nav-list + 21 script tags |
| `creative_suite/frontend/studio-pages.js` | Full replacement — nested NAV, sidebar render, URL sync, mode wiring |
| `creative_suite/frontend/studio.css` | Append ~80 lines (mode switch, groups, chips, iframe/list shells) |
| `creative_suite/api/forge.py` | Add `GET /api/forge/demos` |

### Renamed
| Old | New | Global rename |
|---|---|---|
| `creative_suite/frontend/studio-textures.js` | `creative_suite/frontend/creative-textures.js` | `StudioTextures` to `CreativeTextures` + compat shim |

### Created — LAB panels (7)
`lab-demos.js` · `lab-extraction.js` · `lab-patterns.js` · `lab-annotate.js` · `lab-flags.js` · `lab-forge.js` · `lab-engine.js`

### Created — CREATIVE panels (8)
`creative-sprites.js` · `creative-skins.js` · `creative-maps.js` · `creative-md3.js` · `creative-prompts.js` · `creative-queue.js` · `creative-packs.js`

### Created — Tests
`creative_suite/tests/test_api_forge_demos.py` · `creative_suite/tests/test_app_root_redirect.py`

---

## PHASE 1 — Skeleton (targets A1–A6)

### Task 1: app.py — root redirect + engine-graph mount

**Files:** `creative_suite/app.py` · `creative_suite/tests/test_app_root_redirect.py`

- [ ] **Write failing test** (`creative_suite/tests/test_app_root_redirect.py`):

```python
from fastapi.testclient import TestClient
from creative_suite.app import create_app

def test_root_redirects_to_studio():
    client = TestClient(create_app(), follow_redirects=False)
    r = client.get("/")
    assert r.status_code == 307
    assert r.headers["location"] == "/studio"
```

- [ ] **Run — confirm FAIL**: `E:\PersonalAI\venv\Scripts\pytest.exe creative_suite/tests/test_app_root_redirect.py -v`
  Expected: FAIL (root currently returns 200 annotate.html)

- [ ] **Edit app.py** — `GET /` handler body: change `return FileResponse(WEB_ROOT / "annotate.html")` to:
```python
return RedirectResponse(url="/studio", status_code=307)
```
Add `RedirectResponse` to existing `from fastapi.responses import FileResponse` import if not already there.

- [ ] **Add engine-graph static mount** after existing `/static` mount block:
```python
_ENGINE_GRAPH_DIR = Path(__file__).parent.parent / "engine" / "graphify-out"
if _ENGINE_GRAPH_DIR.exists():
    app.mount("/engine-graph",
              StaticFiles(directory=str(_ENGINE_GRAPH_DIR), html=True),
              name="engine-graph")
```
`StaticFiles` and `Path` are already imported.

- [ ] **Run — confirm PASS** then commit:
```
git add creative_suite/app.py creative_suite/tests/test_app_root_redirect.py
git commit -m "feat(shell-v2): root GET / 307 to /studio; engine-graph static mount"
```

---

### Task 2: studio-store.js — activeMode + modePage + SET_ACTIVE_MODE

**Files:** `creative_suite/frontend/studio-store.js`

- [ ] **Add to INITIAL_STATE** (after opening brace, before `activePage`):
```js
activeMode: 'studio',
modePage: { studio: 'preview', lab: 'demos', creative: 'textures' },
selectedDemo: null,
```

- [ ] **Add after INITIAL_STATE closing brace**:
```js
var _DEFAULTS = { studio: 'preview', lab: 'demos', creative: 'textures' };
```

- [ ] **Add SET_ACTIVE_MODE case** in dispatch() switch, BEFORE the existing SET_ACTIVE_PAGE case:
```js
case 'SET_ACTIVE_MODE': {
  var nextMode = action.payload;
  var nextPage = _state.modePage[nextMode] || _DEFAULTS[nextMode];
  setState({ activeMode: nextMode, activePage: nextPage });
  break;
}
```

- [ ] **Replace SET_ACTIVE_PAGE body** (currently just `setState({ activePage: action.payload })`):
```js
case 'SET_ACTIVE_PAGE': {
  var page = action.payload;
  var mp = Object.assign({}, _state.modePage);
  mp[_state.activeMode] = page;
  setState({ activePage: page, modePage: mp });
  break;
}
```

- [ ] **Add SET_SELECTED_DEMO case** (after SET_ACTIVE_PAGE):
```js
case 'SET_SELECTED_DEMO':
  setState({ selectedDemo: action.payload });
  break;
```

- [ ] **Commit**: `git commit -m "feat(shell-v2): store — activeMode, modePage, SET_ACTIVE_MODE, per-mode page memory"`

---

### Task 3: studio.html — wholesale replacement

**Files:** `creative_suite/frontend/studio.html` (replace all 95 lines)

- [ ] **Replace entire file** with source from spec section 06. Structural changes from current v1:
  - Logo text changes from "PANTHEON STUDIO" to "PANTHEON"
  - New `<div id="mode-switch" role="tablist">` with 3 `<button class="mode-btn">` elements: STUDIO (active), LAB, CREATIVE
  - Replace hardcoded `<ul id="nav-list">` with `<div id="nav-list" data-active-mode="studio">` (studio-pages.js populates it)
  - Status footer adds: `<span id="status-mode-chip" class="status-mode studio">STUDIO</span>`
  - Script tag list expands from 13 to 21: vendor(7) + core(2) + studio panels(5) + lab panels(7) + creative panels(8) + router(1)
  - `studio-textures.js` becomes `creative-textures.js` in the script list

- [ ] **Commit**: `git commit -m "feat(shell-v2): studio.html — mode switch, dynamic nav-list, 21 script tags"`

---

### Task 4: studio-pages.js — full rewrite

**Files:** `creative_suite/frontend/studio-pages.js` (replace entire file)

- [ ] **Replace entire file** with source from spec section 08. Full source is copy-pasteable from there. Summary of what the new file does:

  **NAV object** — three top-level keys `studio` / `lab` / `creative`, each with `groups[]` of `{ label, items[] }`. Items have `{ page, label, icon, module }` where `module` is the window global name (e.g. `'LabDemos'`).

  **ICONS object** — 20 keys mapping icon names to SVG path strings (static data, never user input).

  **`_renderSidebar(mode, activePage)`** — clears `#nav-list`, rebuilds from NAV[mode].groups. Each nav item is a `<div role="button" tabindex="0" data-page="...">`. SVG icon injection via `.innerHTML` is the ONLY allowed use of innerHTML (static ICONS dict — Rule UI-1).

  **`_switch(mode, page)`** — unmounts current panel, resolves `global[cfg.module]`, calls `.mount(slot)`. Falls back to placeholder div if module not loaded.

  **`_syncUrl(mode, page)`** — `history.replaceState` with `?mode=&page=` querystring.

  **`_wire()`** — mode-switch button clicks dispatch `SET_ACTIVE_MODE`; sidebar clicks/Enter/Space dispatch `SET_ACTIVE_PAGE`.

  **`init()`** — reads URL params, dispatches, wires, subscribes to store, does initial `_renderSidebar` + `_switch` + `_syncUrl`.

- [ ] **Commit**: `git commit -m "feat(shell-v2): studio-pages.js — nested NAV, sidebar render, URL sync, mode wiring"`

---

### Task 5: studio.css — append mode + panel-shell CSS

**Files:** `creative_suite/frontend/studio.css` (append only — do NOT edit existing rules)

- [ ] **Append** the ~80 lines from spec section 07 to end of file. Sections to append (copy verbatim from spec):
  - `:root` additions: `--mode-studio: #C9A84C`, `--mode-lab: #3a66b8`, `--mode-creative: #a03fbc`
  - `#mode-switch` container + `.mode-btn` base + `.mode-btn:hover` + three `.mode-btn.active[data-mode=X]` rules
  - Mode-aware sidebar active state: `#nav-list[data-active-mode=lab] .nav-item.active` and creative variant
  - `.nav-group + .nav-group` separator + `.nav-group-label` + `.nav-group-label::after` gradient line
  - `.nav-item .nav-chip` + `.nav-chip.new` + `.nav-chip.count` + `.nav-icon svg`
  - `.status-mode` chip + three `.status-mode.studio/lab/creative` variants
  - `.panel-iframe-wrap/toolbar/title/btn/frame` — shared iframe panel shell
  - `.list-panel/toolbar/filter/scroll/row` + `.list-row:hover/active/.r-primary/.r-sub/.r-meta` — shared list panel shell

- [ ] **Commit**: `git commit -m "feat(shell-v2): studio.css — mode switch, nav groups, iframe/list panel shells"`

---

### Phase 1 Smoke Test — verify A1–A6 before proceeding

Restart FastAPI server (`uvicorn creative_suite.app:create_app --factory --host 0.0.0.0 --port 8765 --reload`), then:

- [ ] **A1** — `curl -I http://localhost:8765/` returns `307` with `location: /studio`
- [ ] **A2** — Visit `/studio`: 3 mode buttons in header, STUDIO active (gold), sidebar shows 5 items under "Edit flow", panel-slot shows placeholder
- [ ] **A3** — Click LAB: sidebar re-renders with 7 items in 3 groups, status chip turns blue "LAB", URL becomes `?mode=lab&page=demos`
- [ ] **A4** — Click CREATIVE: 8 items in 3 groups, status chip violet
- [ ] **A5** — Click STUDIO, navigate to Timeline, click LAB, click STUDIO again: lands on Timeline (modePage preserved)
- [ ] **A6** — Hard-navigate to `/studio?mode=lab&page=patterns`: Patterns placeholder loads cold with Patterns nav item active

**Stop if any A1–A6 fail. Common issues:** wrong script load order in studio.html; store subscribe not called before initial render in init().

---

## PHASE 2 — Move + stub (targets A11, zero console errors)

### Task 6: Rename studio-textures.js to creative-textures.js

**Files:** `creative_suite/frontend/studio-textures.js` → `creative_suite/frontend/creative-textures.js`

- [ ] Copy and rename:
```
cp creative_suite/frontend/studio-textures.js creative_suite/frontend/creative-textures.js
```

- [ ] Edit `creative-textures.js` — find the bottom assignment (e.g. `global.StudioTextures = { mount: mount, unmount: unmount }`). Replace with:
```js
global.CreativeTextures = { mount: mount, unmount: unmount };
window.StudioTextures = window.CreativeTextures; // compat shim — remove next release
```

- [ ] Delete original: `git rm creative_suite/frontend/studio-textures.js`

- [ ] Commit:
```
git add creative_suite/frontend/creative-textures.js
git commit -m "feat(shell-v2): studio-textures to creative-textures; CreativeTextures global; compat shim"
```

---

### Task 7: Create 14 panel stubs

**Files:** All 14 new `lab-*.js` and `creative-*.js` files except `creative-textures.js`.

- [ ] Create each file using this template (substitute LABEL and GLOBAL per table):
```js
(function (global) { 'use strict';
  function mount(slot) {
    var d = document.createElement('div');
    d.style.cssText = 'padding:24px;color:#555;font-family:monospace;font-size:12px';
    d.textContent = 'LABEL';
    slot.replaceChildren(d);
  }
  global.GLOBAL = { mount: mount, unmount: function () {} };
}(window));
```

| File | GLOBAL | LABEL |
|---|---|---|
| `lab-demos.js` | `LabDemos` | `LAB · DEMOS — loading` |
| `lab-extraction.js` | `LabExtraction` | `LAB · EXTRACTION — loading` |
| `lab-patterns.js` | `LabPatterns` | `LAB · PATTERNS — loading` |
| `lab-annotate.js` | `LabAnnotate` | `LAB · ANNOTATE — loading` |
| `lab-flags.js` | `LabFlags` | `LAB · FLAGS — loading` |
| `lab-forge.js` | `LabForge` | `LAB · FORGE — loading` |
| `lab-engine.js` | `LabEngine` | `LAB · ENGINE GRAPH — loading` |
| `creative-sprites.js` | `CreativeSprites` | `CREATIVE · SPRITES — loading` |
| `creative-skins.js` | `CreativeSkins` | `CREATIVE · SKINS — loading` |
| `creative-maps.js` | `CreativeMaps` | `CREATIVE · MAPS — loading` |
| `creative-md3.js` | `CreativeMd3Viewer` | `CREATIVE · MD3 VIEWER — loading` |
| `creative-prompts.js` | `CreativePrompts` | `CREATIVE · PROMPTS — loading` |
| `creative-queue.js` | `CreativeQueue` | `CREATIVE · QUEUE — loading` |
| `creative-packs.js` | `CreativePacks` | `CREATIVE · PACKS — loading` |

- [ ] Commit: `git commit -m "feat(shell-v2): 14 panel stubs — every nav item mounts a placeholder"`

- [ ] **Smoke test** — click every nav item across all 3 modes. Verify: each shows placeholder text, zero JS console errors, A11 (CREATIVE·Textures unchanged behavior).

---

## PHASE 3 — forge API + LAB panels (targets A7–A10)

### Task 8: forge.py — GET /api/forge/demos

**Files:** `creative_suite/api/forge.py` · `creative_suite/tests/test_api_forge_demos.py`

- [ ] **Write failing tests**:
```python
# creative_suite/tests/test_api_forge_demos.py
from __future__ import annotations
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from creative_suite.app import create_app

@pytest.fixture
def client_with_demos(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    demos_dir = tmp_path / "demos"
    demos_dir.mkdir()
    (demos_dir / "game01.dm_73").write_bytes(b"x")
    (demos_dir / "game02.dm_73").write_bytes(b"x")
    (demos_dir / "sub").mkdir()
    (demos_dir / "sub" / "game03.dm_73").write_bytes(b"x")
    import creative_suite.api.forge as forge_mod
    monkeypatch.setattr(forge_mod, "_DEMOS_DIR", demos_dir)
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    return TestClient(create_app())

def test_demos_returns_list(client_with_demos: TestClient) -> None:
    r = client_with_demos.get("/api/forge/demos")
    assert r.status_code == 200
    assert len(r.json()["demos"]) == 3

def test_demos_entry_shape(client_with_demos: TestClient) -> None:
    demo = client_with_demos.get("/api/forge/demos").json()["demos"][0]
    for key in ("path", "name", "size_mb", "state"):
        assert key in demo
    assert demo["state"] == "fresh"

def test_demos_empty_when_no_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import creative_suite.api.forge as forge_mod
    monkeypatch.setattr(forge_mod, "_DEMOS_DIR", tmp_path / "nonexistent")
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    r = TestClient(create_app()).get("/api/forge/demos")
    assert r.status_code == 200
    assert r.json()["demos"] == []
```

- [ ] **Run — confirm FAIL** (404): `E:\PersonalAI\venv\Scripts\pytest.exe creative_suite/tests/test_api_forge_demos.py -v`

- [ ] **Add endpoint to forge.py** (after `_count_demos` function, around line 56):
```python
@router.get("/demos")
def get_demos() -> dict[str, Any]:
    """List all .dm_73 files in the demo corpus."""
    if not _DEMOS_DIR.exists():
        return {"demos": []}
    demos = []
    for p in sorted(_DEMOS_DIR.rglob("*.dm_73")):
        try:
            size_mb = round(p.stat().st_size / (1024 * 1024), 2)
        except OSError:
            size_mb = 0.0
        demos.append({
            "path": str(p),
            "name": p.name,
            "map": p.parent.name if p.parent != _DEMOS_DIR else "",
            "size_mb": size_mb,
            "state": "fresh",
        })
    return {"demos": demos}
```

- [ ] **Run — confirm PASS** then commit:
```
git add creative_suite/api/forge.py creative_suite/tests/test_api_forge_demos.py
git commit -m "feat(shell-v2): GET /api/forge/demos — list dm_73 corpus with path/name/map/size_mb"
```

---

### Task 9: lab-demos.js — demo list panel

**Files:** `creative_suite/frontend/lab-demos.js` (replace stub)

Full source is in spec section 10 "lab-demos.js · list of .dm_73 files". Copy verbatim from there.

Key contract:
- `mount(slot)`: `.list-panel` with toolbar (title + filter input + REFRESH button) + `.list-scroll`
- `_fetchDemos()`: `GET /api/forge/demos` with `AbortSignal.timeout(5000)` → `_renderList(d.demos)`
- `_renderList(rows)`: each `.list-row` = diamond icon + name/map·size + state chip. All via createElement/textContent.
- Row click: `StudioStore.dispatch({ type: 'SET_SELECTED_DEMO', payload: r.path })` then `dispatch({ type: 'SET_ACTIVE_PAGE', payload: 'extraction' })`
- `unmount()`: clears `setInterval` (15s poll)

- [ ] **Verify (A7)**: navigate to `?mode=lab&page=demos`, list populates, click row → navigates to Extraction and stores demo path
- [ ] **Commit**: `git commit -m "feat(shell-v2): lab-demos.js — dm73 list from /api/forge/demos, click to extraction"`

---

### Task 10: lab-forge.js — native forge panel

**Files:** `creative_suite/frontend/lab-forge.js` (replace stub)

- [ ] **Build the panel** — `.list-panel` with toolbar + log div:
  - Toolbar: title "FORGE" + status span + "GENERATE INTRO" button + "EXTRACT DEMO" button
  - `_pollStatus()` every 5s: `GET /api/forge/status` → status span text/color (IDLE=green, BUSY=amber, OFFLINE=grey). Use `AbortSignal.timeout(4000)`.
  - GENERATE INTRO: `POST /api/forge/intro` body `{ part: StudioStore.getState().activePart || 1, style: 'default', duration_s: 8 }` with `AbortSignal.timeout(10000)` → `_log('OK job_id=...', 'ok')` or `_log('FAILED ...', 'err')`
  - EXTRACT DEMO: reads `StudioStore.getState().selectedDemo`; if null → `_log('No demo selected', 'err')`; else `POST /api/forge/demo/extract` body `{ demo_path, extract_frags: true }` with `AbortSignal.timeout(30000)`
  - `_log(msg, kind)`: appends timestamped div to log element, color-coded (err=red, ok=green, info=grey)
  - `unmount()`: clears poll interval

- [ ] **Verify (A8)**: network tab shows `/api/forge/status` every 5s; both buttons POST and append to log
- [ ] **Commit**: `git commit -m "feat(shell-v2): lab-forge.js — status poll, GENERATE INTRO, EXTRACT DEMO log panel"`

---

### Task 11: lab-annotate.js — iframe wrapper

**Files:** `creative_suite/frontend/lab-annotate.js` (replace stub)

- [ ] **Implement**:
```js
(function (global) { 'use strict';
  var _frame = null;
  function mount(slot) {
    var wrap = document.createElement('div'); wrap.className = 'panel-iframe-wrap';
    var bar = document.createElement('div'); bar.className = 'panel-iframe-toolbar';
    var title = document.createElement('span'); title.className = 'panel-iframe-title'; title.textContent = 'ANNOTATE';
    var btnR = document.createElement('button'); btnR.className = 'panel-iframe-btn'; btnR.textContent = 'REFRESH';
    btnR.addEventListener('click', function () { if (_frame) _frame.src = _frame.src; });
    var btnO = document.createElement('button'); btnO.className = 'panel-iframe-btn'; btnO.textContent = 'OPEN FULL';
    btnO.addEventListener('click', function () { window.open('/annotate', '_blank'); });
    bar.appendChild(title); bar.appendChild(btnR); bar.appendChild(btnO);
    var frame = document.createElement('iframe'); frame.className = 'panel-iframe-frame';
    frame.src = '/web/annotate.html'; frame.title = 'Annotation Tool'; _frame = frame;
    wrap.appendChild(bar); wrap.appendChild(frame); slot.replaceChildren(wrap);
  }
  function unmount() { _frame = null; }
  global.LabAnnotate = { mount: mount, unmount: unmount };
}(window));
```

- [ ] **Verify (A9)**: iframe loads `/web/annotate.html`, REFRESH reloads it, zero console errors
- [ ] **Commit**: `git commit -m "feat(shell-v2): lab-annotate.js — iframe for /web/annotate.html"`

---

### Task 12: lab-engine.js — knowledge graph iframe

**Files:** `creative_suite/frontend/lab-engine.js` (replace stub)

- [ ] **Implement** — same `.panel-iframe-wrap` shape, `frame.src = '/engine-graph/index.html'`, OPEN FULL button. Add error handler:
```js
frame.addEventListener('error', function () {
  var d = document.createElement('div');
  d.style.cssText = 'padding:24px;color:#555;font-family:monospace;font-size:11px';
  d.textContent = 'Engine graph not generated yet — run graphify on the engine source trees to populate engine/graphify-out/.';
  if (wrap.contains(frame)) wrap.replaceChild(d, frame);
});
```
No REBUILD button (endpoint not wired yet — per Q2).

- [ ] **Verify (A10)**: if `engine/graphify-out/index.html` exists, it renders; else shows placeholder text. Check `engine/graphify-out/cache` exists — verify if `index.html` is there.
- [ ] **Commit**: `git commit -m "feat(shell-v2): lab-engine.js — engine graph iframe, graceful empty state"`

---

### Task 13: lab-extraction.js

**Files:** `creative_suite/frontend/lab-extraction.js` (replace stub)

- [ ] **Implement** — `.list-panel` with toolbar + info row + log:
  - Info row shows `StudioStore.getState().selectedDemo` filename (basename only). Subscribe to store on mount: `_unsub = StudioStore.subscribe(fn)`. Call `_unsub()` in unmount.
  - Status span: IDLE (grey) → RUNNING (amber) → DONE (green) / FAILED (red)
  - EXTRACT button: if `selectedDemo` null → `_log('No demo selected — go to LAB · Demos first', 'err')` and return. Else `POST /api/forge/demo/extract` body `{ demo_path: selectedDemo, extract_frags: true }` with `AbortSignal.timeout(60000)` → log fragments + duration_s
  - `_log(msg, kind)`: same pattern as lab-forge.js

- [ ] **Commit**: `git commit -m "feat(shell-v2): lab-extraction.js — store-synced demo path, extract with log"`

---

### Task 14: lab-patterns.js

**Files:** `creative_suite/frontend/lab-patterns.js` (replace stub)

- [ ] **Implement** — filterable list over phase1 artifacts:
  - `_fetch()`: get `activePart` from store; if null show empty state. Call `GET /api/phase1/parts/:activePart/artifacts` with `AbortSignal.timeout(5000)`. Parse `d.event_diversity` (object keyed by pattern_id) into array `[{ pattern_id, name, count, weapon, maps }]` where `name = pattern_id.replace(/_/g, ' ')`.
  - `_renderList(patterns)`: each `.list-row` = blue diamond + name/count·maps + weapon tag
  - Row click: `dispatch SET_ACTIVE_MODE='studio'` then `dispatch SET_ACTIVE_PAGE='inspector'`
  - Filter input: text search on row textContent
  - Empty state message when no patterns found

- [ ] **Commit**: `git commit -m "feat(shell-v2): lab-patterns.js — event diversity list, click to STUDIO Inspector"`

---

### Task 15: lab-flags.js

**Files:** `creative_suite/frontend/lab-flags.js` (replace stub)

- [ ] **Implement** — AI-assisted tagging:
  - `_fetch()`: `GET /api/phase1/parts` → collect clip entries into list (simplified: map parts array to stub clip objects)
  - Each row: clip ID + current tag text + SUGGEST button
  - SUGGEST click: `POST /api/ollama/suggest` body `{ clip_id }` with `AbortSignal.timeout(15000)` → update tag display
  - On 503: set `_ollamaAvail = false`; immediately disable ALL SUGGEST buttons with `disabled = true`; show notice "(Ollama unavailable)" in toolbar
  - On other errors: log in button text, re-enable button

- [ ] **Phase 3 Smoke Test (A7–A10)**:
  - A7: LAB·Demos list populates; click row → navigates to Extraction showing demo filename
  - A8: LAB·Forge polls status every 5s; buttons POST and append to log
  - A9: LAB·Annotate iframe loads `/web/annotate.html`
  - A10: LAB·Graph loads engine graph or shows graceful placeholder

- [ ] **Commit**: `git commit -m "feat(shell-v2): lab-flags.js — Ollama suggest, 503 graceful disable"`

---

## PHASE 4 — CREATIVE panels (targets A12–A14)

### Task 16: creative-sprites.js, creative-skins.js, creative-maps.js — asset thumbnail grids

**Files:** Replace 3 stubs. All three have identical structure — only title, category, and global name differ.

- [ ] **Implement each** as a `.list-panel` with thumbnail grid:
  - Toolbar: title only
  - Grid div: `grid-template-columns: repeat(auto-fill, minmax(140px, 1fr))`, `overflow-y: auto`
  - On mount: `GET /api/assets?category=CATEGORY` with `AbortSignal.timeout(8000)` → render grid cells
  - Each cell: `<img src=thumbnail_url>` + name label via textContent. Empty state: "No CATEGORY assets found."
  - Cell click: call `_openPrompt(asset)` — opens an inline overlay modal

- [ ] **`_openPrompt(asset)` modal** (append to `document.body`, remove on close):
  - Fixed overlay div (rgba 0,0,0,0.75)
  - Modal: asset name heading + textarea (positive prompt, 3 rows) + denoise range slider (min=0.1 max=0.8 step=0.05 default=0.35) + denoise value display + CANCEL + QUEUE buttons
  - QUEUE click: `POST /api/comfy/queue` body `{ asset_id: asset.id, user_prompt: textarea.value, denoise: parseFloat(slider.value) }` with `AbortSignal.timeout(10000)` → close modal on success; show error in button text on fail
  - CANCEL + click-outside-overlay both close (remove overlay from body)
  - All content via createElement/textContent — no innerHTML

- [ ] **Category routing per file**:
  - `creative-sprites.js` → `category=sprite` → `global.CreativeSprites`
  - `creative-skins.js` → `category=skin` → `global.CreativeSkins`
  - `creative-maps.js` → `category=surface` → `global.CreativeMaps`

- [ ] **Commit**:
```
git add creative_suite/frontend/creative-sprites.js creative_suite/frontend/creative-skins.js creative_suite/frontend/creative-maps.js
git commit -m "feat(shell-v2): creative-sprites/skins/maps — asset thumbnail grids with queue prompt modal"
```

---

### Task 17: creative-queue.js — ComfyUI job queue

**Files:** `creative_suite/frontend/creative-queue.js` (replace stub)

Full source is in spec section 11 "creative-queue.js · ComfyUI job queue". Copy verbatim.

Key contract:
- Grid: `grid-template-columns: repeat(auto-fill, minmax(180px, 1fr))`
- `_fetchPending()`: `GET /api/comfy/status` → for each variant render: img + status dot (approved=`#44bb44`, rejected=`#c41515`, running=`#e68a00`, else `#888`) + approve (checkmark) + reject (cross) buttons. Empty state message.
- Approve button: `PATCH /api/variants/:id` body `{ status: 'approved' }` with `AbortSignal.timeout(5000)` → re-fetch
- Reject button: `PATCH /api/variants/:id` body `{ status: 'rejected' }` → re-fetch
- Poll every 4s; clear in `unmount()`
- All event listeners via closure (IIFE) to capture correct `v.id` per iteration

- [ ] **Verify (A13)**: navigate to `?mode=creative&page=queue`; poll fires every 4s in network tab; approve/reject buttons round-trip
- [ ] **Commit**: `git commit -m "feat(shell-v2): creative-queue.js — variant thumbnails, approve/reject, 4s poll"`

---

### Task 18: creative-packs.js — pk3 gate + build/install

**Files:** `creative_suite/frontend/creative-packs.js` (replace stub)

- [ ] **Implement** — `.list-panel` with toolbar + traffic-light section + log div:

  **Toolbar**: title "PACKS" + BUILD button (disabled initially) + INSTALL button (disabled) + CHECK button

  **Traffic light section** (3 rows built with createElement only — no innerHTML):
  - Row 1: colored dot + "Approved variants: N / 5"
  - Row 2: colored dot + "Surface category approved"
  - Row 3: colored dot + "Skin category approved"
  - Dot color: green (`#44bb44`) if condition met, red (`#c41515`) if not
  - Pattern for each row:
    ```js
    var dot = document.createElement('span');
    dot.style.cssText = 'width:10px;height:10px;border-radius:50%;display:inline-block;margin-right:6px;background:' + (ok ? '#44bb44' : '#c41515');
    row.appendChild(dot);
    row.appendChild(document.createTextNode(labelText));
    ```

  **`_refresh()`**: `GET /api/comfy/status` → count approved, get categories → `_checkGate(d)`. Rebuild traffic light rows. Enable BUILD + INSTALL only when all 3 conditions green (approved>=5, has surface, has skin).

  **BUILD**: `POST /api/packs/build` with `AbortSignal.timeout(60000)` → log `pk3_path + sha256`
  **INSTALL**: `POST /api/packs/install` with `AbortSignal.timeout(30000)` → log `target_path`

- [ ] **Verify (A14)**: navigate to `?mode=creative&page=packs`; gate shows 3 traffic lights; with <5 approved BUILD is disabled
- [ ] **Commit**: `git commit -m "feat(shell-v2): creative-packs.js — Gate CS-1 traffic lights, BUILD/INSTALL buttons"`

---

### Task 19: creative-md3.js + creative-prompts.js

**Files:** Replace 2 stubs.

- [ ] **creative-md3.js** — placeholder + download button (per spec Q1, no in-browser viewer yet):
  - Body centered: explanation text + asset_id input + DOWNLOAD MD3 button
  - Button click: `window.open('/api/md3/' + encodeURIComponent(input.value.trim()), '_blank')` if input non-empty

- [ ] **creative-prompts.js** — read-only preset library:
  - Hardcode 6 prompt presets matching `build_final_prompt` style names from `creative_suite/comfy/prompts.py`
  - Preset names (check prompts.py for exact names): Photoreal Surface, Neon Cel-Shade, Dark Gothic, Weapon Metal, Player Skin, Pickup Icon
  - Each row: name (gold color) + positive prompt text (green, prefix "+") + negative (red, prefix "−") + COPY+ button
  - COPY+ button: `navigator.clipboard.writeText(preset.positive)` → flash button text "COPIED" for 1.2s then restore

- [ ] **Phase 4 Smoke Test (A12–A14)**:
  - A12: CREATIVE·Sprites/Skins/Maps render thumbnail grids from `/api/assets?category=...`; clicking a cell opens the prompt modal
  - A13: CREATIVE·Queue polls `/api/comfy/status` every 4s; approve/reject buttons PATCH `/api/variants/:id`
  - A14: CREATIVE·Packs shows 3 traffic lights; BUILD disabled when <5 approved

- [ ] **Commit**: `git commit -m "feat(shell-v2): creative-md3 placeholder + download; creative-prompts read-only library"`

---

## PHASE 5 — Polish + audit (A15–A17)

### Task 20: innerHTML audit + keyboard nav + console sweep

**No new files.**

- [ ] **A16 innerHTML audit** — run:
```
grep -rn "innerHTML" creative_suite/frontend/ --include="*.js"
```
Expected: **exactly 1 hit** — the ICONS injection in `studio-pages.js`. Any other hit must be converted to `createElement`/`textContent`. Fix all offenders before continuing.

- [ ] **A15 Keyboard nav** — use Tab key only, no mouse:
  - Header: logo → STUDIO → LAB → CREATIVE mode buttons → part-select → rew → play → fwd → REBUILD
  - Sidebar: every nav item reachable via Tab; Enter or Space activates each item
  - Verify `studio-pages.js` `_renderSidebar()` sets `tabindex="0"` and `role="button"` on each nav item div (it does per Task 4 spec)

- [ ] **A17 Browser console sweep** — open DevTools console, navigate to every panel in order:
  - STUDIO: Preview → Timeline → Audio → Effects → Inspector
  - LAB: Demos → Extraction → Patterns → Annotate → Flags → Forge → Graph
  - CREATIVE: Textures → Sprites → Skins → Maps → MD3 Viewer → Prompts → Queue → Packs
  - Expected: **zero app-code errors**. Vendor lib warnings from wavesurfer/litegraph/theatre are acceptable.

- [ ] **Run full test suite**:
```
E:\PersonalAI\venv\Scripts\pytest.exe creative_suite/tests/ -v --tb=short 2>&1 | tail -20
```
Expected: all tests pass (565 pre-existing + 4 new from this plan = 569+).

- [ ] **Final commit**: `git commit -m "feat(shell-v2): Phase 5 polish — innerHTML clean, keyboard nav, console sweep"`

---

## Acceptance Checklist

| # | Gate | How to verify |
|---|---|---|
| A1 | `GET /` returns 307 `Location: /studio` | `curl -I http://localhost:8765/` |
| A2 | 3 mode buttons in header; STUDIO sidebar 5 items | Screenshot |
| A3 | LAB click: 7-item sidebar, blue chip, URL `?mode=lab&page=demos` | Browser |
| A4 | CREATIVE click: 8-item sidebar, violet chip | Browser |
| A5 | Mode flip preserves last-visited page per mode | Manual |
| A6 | Hard-refresh `?mode=lab&page=patterns` loads cold | Browser |
| A7 | LAB·Demos list populates; row click to Extraction | Network + Browser |
| A8 | LAB·Forge polls `/api/forge/status` every 5s; buttons POST | Network tab |
| A9 | LAB·Annotate iframe loads `/web/annotate.html` | Browser |
| A10 | LAB·Graph loads or graceful placeholder | Browser |
| A11 | CREATIVE·Textures identical behavior to before | Visual compare |
| A12 | CREATIVE·Sprites/Skins/Maps render asset grids | Browser |
| A13 | CREATIVE·Queue 4s poll; approve/reject round-trip | Network tab |
| A14 | CREATIVE·Packs gate traffic lights; BUILD gated | Browser |
| A15 | Keyboard Tab covers all nav + mode buttons; Enter/Space activates | Manual |
| A16 | `grep innerHTML` returns exactly 1 hit (ICONS in studio-pages.js) | Grep |
| A17 | Browser console: zero app-code errors across all 20 panels | DevTools |
