# Cockpit UI Closeout Stabilization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stabilize the current `/studio` cockpit so the live UI, automated tests, documentation, and visual records all agree on the same shell contract before the user-led test pass.

**Architecture:** Treat the current product direction as `STUDIO = { CLIPS, EDIT }`, with `EDIT` remaining the integrated NLE workspace already shipped in [`creative_suite/frontend/studio-edit.js`](/mnt/g/QUAKE_LEGACY/creative_suite/frontend/studio-edit.js). Fix the broken API contracts in LAB and CREATIVE, then refresh the repo docs/tests so they verify the current shell instead of the retired five-page router.

**Tech Stack:** FastAPI, vanilla browser JS, sqlite, existing TestClient-based pytest suite, Playwright/manual browser screenshots in `docs/visual-record/`.

---

## File Map

### Modify
- `creative_suite/frontend/creative-maps.js`
- `creative_suite/frontend/creative-skins.js`
- `creative_suite/frontend/creative-sprites.js`
- `creative_suite/frontend/creative-queue.js`
- `creative_suite/frontend/creative-packs.js`
- `creative_suite/frontend/lab-forge.js`
- `creative_suite/frontend/lab-extraction.js`
- `creative_suite/frontend/studio-edit.js`
- `creative_suite/frontend/studio-timeline-nle.js`
- `creative_suite/frontend/studio-pages.js`
- `creative_suite/api/assets.py`
- `creative_suite/api/variants.py`
- `creative_suite/tests/test_studio_html.py`
- `creative_suite/tests/test_studio_pages.py`
- `creative_suite/tests/test_api_packs.py`
- `creative_suite/tests/test_api_variants.py`
- `docs/claude_designer/Unified Nav Shell Design v2.html`
- `docs/superpowers/plans/EXECUTION_STATUS.md`

### Create
- `creative_suite/tests/test_api_assets.py`
- `docs/reference/cockpit-v2-contract.md`
- `docs/visual-record/README.md`

### Verification Artifacts
- `docs/visual-record/2026-04-21/studio_clips_page.png`
- `docs/visual-record/2026-04-21/studio_edit_page.png`
- `docs/visual-record/2026-04-21/cockpit-v2-lab-mode-stubs.png`
- `docs/visual-record/2026-04-21/cockpit-v2-creative-mode.png`

---

### Task 1: Lock The Real Shell Contract In Tests

**Files:**
- Modify: `creative_suite/tests/test_studio_html.py`
- Modify: `creative_suite/tests/test_studio_pages.py`
- Test: `creative_suite/tests/test_studio_store.py`

- [ ] **Step 1: Replace the stale five-page assertions with the current CLIPS/EDIT contract**

```python
def test_studio_html_contains_mode_buttons(client: TestClient) -> None:
    r = client.get("/studio")
    assert r.status_code == 200
    for mode in ("studio", "lab", "creative"):
        assert f'data-mode="{mode}"' in r.text


def test_studio_html_contains_dynamic_sidebar_shell(client: TestClient) -> None:
    r = client.get("/studio")
    assert r.status_code == 200
    assert 'id="nav-list"' in r.text
    assert 'data-active-mode="studio"' in r.text


def test_pages_source_has_current_studio_rows() -> None:
    src = PAGES_JS.read_text(encoding="utf-8")
    assert "{ page: 'clips'" in src
    assert "{ page: 'edit'" in src
    assert "StudioClips" in src
    assert "StudioEdit" in src
```

- [ ] **Step 2: Run the focused shell tests and confirm the old expectations fail before the update**

Run:

```bash
/mnt/e/PersonalAI/venv/Scripts/python.exe -m pytest \
  creative_suite/tests/test_studio_html.py \
  creative_suite/tests/test_studio_pages.py -q
```

Expected: FAIL on `preview/timeline/audio/effects/inspector` expectations.

- [ ] **Step 3: Add coverage for the current mode/page contract**

```python
def test_pages_source_syncs_url_to_mode_and_page() -> None:
    src = PAGES_JS.read_text(encoding="utf-8")
    assert "searchParams.set('mode'" in src
    assert "searchParams.set('page'" in src


def test_studio_html_loads_mode_panels(client: TestClient) -> None:
    r = client.get("/studio")
    assert r.status_code == 200
    for script in (
        "studio-clips.js",
        "studio-edit.js",
        "lab-demos.js",
        "lab-forge.js",
        "creative-textures.js",
        "creative-packs.js",
    ):
        assert script in r.text
```

- [ ] **Step 4: Re-run the focused shell tests**

Run:

```bash
/mnt/e/PersonalAI/venv/Scripts/python.exe -m pytest \
  creative_suite/tests/test_studio_html.py \
  creative_suite/tests/test_studio_pages.py \
  creative_suite/tests/test_studio_store.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add \
  creative_suite/tests/test_studio_html.py \
  creative_suite/tests/test_studio_pages.py \
  creative_suite/tests/test_studio_store.py
git commit -m "test(cockpit): align shell tests with clips-edit contract"
```

---

### Task 2: Make CREATIVE Asset Panels Load Real Assets

**Files:**
- Modify: `creative_suite/api/assets.py`
- Modify: `creative_suite/frontend/creative-maps.js`
- Modify: `creative_suite/frontend/creative-skins.js`
- Modify: `creative_suite/frontend/creative-sprites.js`
- Create: `creative_suite/tests/test_api_assets.py`

- [ ] **Step 1: Write the failing API test for filtered asset browsing**

```python
def test_assets_kind_filter_returns_flat_assets(client: TestClient) -> None:
    r = client.get("/api/assets?kind=skins")
    assert r.status_code == 200
    body = r.json()
    assert body["kind"] == "skins"
    assert isinstance(body["assets"], list)
```

- [ ] **Step 2: Run the new test and confirm it fails**

Run:

```bash
/mnt/e/PersonalAI/venv/Scripts/python.exe -m pytest \
  creative_suite/tests/test_api_assets.py::test_assets_kind_filter_returns_flat_assets -q
```

Expected: FAIL because `/api/assets` only returns `categories`.

- [ ] **Step 3: Extend `assets.py` with a stable `kind` filter used by the shell**

```python
_KIND_MAP = {
    "maps": ("textures", "mapobjects"),
    "skins": ("players",),
    "sprites": ("sprites", "powerups", "weaphits"),
}


@router.get("")
def list_tree(
    request: Request,
    kind: str | None = None,
) -> dict[str, Any]:
    ...
    if kind:
        wanted = _KIND_MAP[kind]
        flat_assets = [
            {
                "id": r["id"],
                "category": r["category"],
                "internal_path": r["internal_path"],
                "thumbnail_url": (
                    f"/api/assets/{r['id']}/thumbnail" if r["thumbnail_path"] else None
                ),
            }
            for r in rows
            if r["category"] in wanted
        ]
        return {"kind": kind, "assets": flat_assets, "total": len(flat_assets)}
```

- [ ] **Step 4: Point the three Creative panels at the real shell kinds**

```js
// creative-maps.js
var KIND = 'maps';
...
fetch('/api/assets?kind=' + KIND, { signal: AbortSignal.timeout(8000) })
  .then(function (r) { return r.ok ? r.json() : { assets: [] }; })
  .then(function (d) { _renderGrid(d.assets || []); });

// creative-skins.js
var KIND = 'skins';

// creative-sprites.js
var KIND = 'sprites';
```

- [ ] **Step 5: Add one real shape assertion for the filtered response**

```python
def test_assets_kind_filter_uses_expected_categories(client: TestClient) -> None:
    r = client.get("/api/assets?kind=sprites")
    assert r.status_code == 200
    allowed = {"sprites", "powerups", "weaphits"}
    for asset in r.json()["assets"][:25]:
        assert asset["category"] in allowed
```

- [ ] **Step 6: Run the asset tests**

Run:

```bash
/mnt/e/PersonalAI/venv/Scripts/python.exe -m pytest \
  creative_suite/tests/test_api_assets.py \
  creative_suite/tests/test_api_variants.py \
  creative_suite/tests/test_api_packs.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add \
  creative_suite/api/assets.py \
  creative_suite/frontend/creative-maps.js \
  creative_suite/frontend/creative-skins.js \
  creative_suite/frontend/creative-sprites.js \
  creative_suite/tests/test_api_assets.py
git commit -m "fix(cockpit): wire creative asset panels to real asset kinds"
```

---

### Task 3: Repair Variant Queue And Pack Gating

**Files:**
- Modify: `creative_suite/api/variants.py`
- Modify: `creative_suite/frontend/creative-queue.js`
- Modify: `creative_suite/frontend/creative-packs.js`
- Test: `creative_suite/tests/test_api_variants.py`
- Test: `creative_suite/tests/test_api_packs.py`

- [ ] **Step 1: Add a failing variants feed test**

```python
def test_variants_feed_returns_recent_items(client: TestClient) -> None:
    r = client.get("/api/variants/feed")
    assert r.status_code == 200
    body = r.json()
    assert "variants" in body
    assert isinstance(body["variants"], list)
```

- [ ] **Step 2: Run the feed test and confirm it fails**

Run:

```bash
/mnt/e/PersonalAI/venv/Scripts/python.exe -m pytest \
  creative_suite/tests/test_api_variants.py::test_variants_feed_returns_recent_items -q
```

Expected: FAIL with 404.

- [ ] **Step 3: Add a shell-oriented variants feed endpoint**

```python
@router.get("/feed")
def variant_feed(request: Request, limit: int = Query(default=60, le=200)) -> dict[str, Any]:
    cfg = request.app.state.cfg
    with connect(cfg) as con:
        rows = con.execute(
            "SELECT v.id, v.status, v.png_path, a.category "
            "FROM variants v JOIN assets a ON a.id = v.asset_id "
            "ORDER BY v.id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return {
        "variants": [
            {
                **dict(r),
                "png_url": f"/api/variants/{r['id']}/png" if r["png_path"] else None,
            }
            for r in rows
        ]
    }
```

- [ ] **Step 4: Point `creative-queue.js` at the right read/write endpoints**

```js
fetch('/api/variants/feed', { signal: AbortSignal.timeout(5000) })
  .then(function (r) { return r.ok ? r.json() : { variants: [] }; })
...
fetch('/api/variants/' + vid + '/approve', { method: 'POST', signal: AbortSignal.timeout(5000) })
fetch('/api/variants/' + vid + '/reject', { method: 'POST', signal: AbortSignal.timeout(5000) })
```

- [ ] **Step 5: Point `creative-packs.js` at the dedicated gate endpoint**

```js
function _refresh() {
  fetch('/api/packs/status', { signal: AbortSignal.timeout(5000) })
    .then(function (r) { return r.ok ? r.json() : { gate_cs1: { ok: false, approved: 0, per_category: {} } }; })
    .then(function (d) {
      var gate = d.gate_cs1 || { ok: false, approved: 0, per_category: {} };
      var approved = gate.approved || 0;
      var perCat = gate.per_category || {};
      var hasTexture = (perCat.textures || 0) > 0 || (perCat.mapobjects || 0) > 0;
      var hasPlayer = (perCat.players || 0) > 0;
      ...
    });
}
```

- [ ] **Step 6: Run the queue/pack tests**

Run:

```bash
/mnt/e/PersonalAI/venv/Scripts/python.exe -m pytest \
  creative_suite/tests/test_api_variants.py \
  creative_suite/tests/test_api_packs.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add \
  creative_suite/api/variants.py \
  creative_suite/frontend/creative-queue.js \
  creative_suite/frontend/creative-packs.js \
  creative_suite/tests/test_api_variants.py \
  creative_suite/tests/test_api_packs.py
git commit -m "fix(cockpit): repair creative queue and pack gate wiring"
```

---

### Task 4: Align LAB Payloads And Clean Up UI Lifecycle Leaks

**Files:**
- Modify: `creative_suite/frontend/lab-forge.js`
- Modify: `creative_suite/frontend/lab-extraction.js`
- Modify: `creative_suite/frontend/studio-edit.js`
- Modify: `creative_suite/frontend/studio-timeline-nle.js`

- [ ] **Step 1: Write a focused static contract test for the FORGE panel copy**

```python
def test_lab_forge_uses_queue_copy_not_fragment_count() -> None:
    src = Path("G:/QUAKE_LEGACY/creative_suite/frontend/lab-forge.js").read_text(encoding="utf-8")
    assert "job_id" in src
    assert "frags" not in src
```

- [ ] **Step 2: Run the static test and confirm the current copy fails**

Run:

```bash
/mnt/e/PersonalAI/venv/Scripts/python.exe -m pytest \
  creative_suite/tests/test_forge_router.py -q
```

Expected: FAIL after the new static assertion is added because the panel logs fake fragment counts.

- [ ] **Step 3: Change the two LAB panels to display the stub contract honestly**

```js
// lab-forge.js
var st = d.ready ? 'ready' : 'blocked';
_statusEl.textContent = st.toUpperCase();
...
.then(function (d) { _log('QUEUED job_id=' + (d.job_id || '?'), 'ok'); })

// lab-extraction.js
.then(function (d) {
  if (_statusEl) { _statusEl.textContent = '\u25cf QUEUED'; _statusEl.style.color = '#44bb44'; }
  _log('Queued extraction job ' + (d.job_id || '?') + ' for ' + demo, 'ok');
})
```

- [ ] **Step 4: Remove the leaking anonymous store subscription from `studio-edit.js`**

```js
var _actionBarUnsubs = [];
...
var syncPlay = s.subscribe(function (state) {
  playBtn.textContent = state.isPlaying ? '\u23F8' : '\u25B6';
  playBtn.style.background = state.isPlaying ? '#0a1a0a' : '#1a2a1a';
});
_actionBarUnsubs.push(syncPlay);
...
_actionBarUnsubs.forEach(function (unsub) { unsub(); });
_actionBarUnsubs = [];
```

- [ ] **Step 5: Store and disconnect the `ResizeObserver` in `studio-timeline-nle.js`**

```js
var _resizeObserver = null;
...
_resizeObserver = new ResizeObserver(_resize);
_resizeObserver.observe(container);
...
if (_resizeObserver) {
  _resizeObserver.disconnect();
  _resizeObserver = null;
}
```

- [ ] **Step 6: Run the targeted tests**

Run:

```bash
/mnt/e/PersonalAI/venv/Scripts/python.exe -m pytest \
  creative_suite/tests/test_forge_router.py \
  creative_suite/tests/test_studio_preview.py \
  creative_suite/tests/test_studio_timeline.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add \
  creative_suite/frontend/lab-forge.js \
  creative_suite/frontend/lab-extraction.js \
  creative_suite/frontend/studio-edit.js \
  creative_suite/frontend/studio-timeline-nle.js \
  creative_suite/tests/test_forge_router.py
git commit -m "fix(cockpit): align lab payload copy and clean mount teardown"
```

---

### Task 5: Reconcile Docs, Status, And Visual Records

**Files:**
- Create: `docs/reference/cockpit-v2-contract.md`
- Modify: `docs/claude_designer/Unified Nav Shell Design v2.html`
- Modify: `docs/superpowers/plans/EXECUTION_STATUS.md`
- Create: `docs/visual-record/README.md`

- [ ] **Step 1: Create a short canonical contract doc for the current shell**

```md
# Cockpit v2 Contract

- `/studio` is a 3-mode shell: `studio`, `lab`, `creative`
- `studio` exposes exactly two rows: `clips`, `edit`
- `edit` mounts the integrated NLE workspace from `studio-edit.js`
- `lab` exposes: `demos`, `extraction`, `patterns`, `annotate`, `flags`, `forge`, `engine`
- `creative` exposes: `textures`, `sprites`, `skins`, `maps`, `md3`, `prompts`, `queue`, `packs`
```

- [ ] **Step 2: Update the old plan/status docs that still describe the retired five-page shell**

```md
## Plan 2 — Cockpit UI Wiring ✅ COMPLETE

- `/studio` no longer uses the five-page STUDIO sidebar
- Current contract is `STUDIO = { CLIPS, EDIT }`
- `EDIT` is the composite NLE workspace, not the old route-per-panel shell
```

- [ ] **Step 3: Add a visual-record index so screenshots are navigable**

```md
# Visual Record Index

- `2026-04-21/studio_clips_page.png` — current STUDIO CLIPS browser
- `2026-04-21/studio_edit_page.png` — current STUDIO EDIT NLE workspace
- `2026-04-21/cockpit-v2-lab-mode-stubs.png` — LAB shell groups
- `2026-04-21/cockpit-v2-creative-mode.png` — CREATIVE shell after asset fixes
```

- [ ] **Step 4: Capture the current shell states after Tasks 1-4 land**

Run:

```bash
# Use the existing screenshot flow already used in this repo.
# Save outputs into docs/visual-record/2026-04-21/
```

Expected artifacts:
- `studio_clips_page.png`
- `studio_edit_page.png`
- `cockpit-v2-lab-mode-stubs.png`
- `cockpit-v2-creative-mode.png`

- [ ] **Step 5: Re-run the full targeted UI/backend suite**

Run:

```bash
/mnt/e/PersonalAI/venv/Scripts/python.exe -m pytest \
  creative_suite/tests/test_studio_html.py \
  creative_suite/tests/test_studio_pages.py \
  creative_suite/tests/test_studio_store.py \
  creative_suite/tests/test_api_assets.py \
  creative_suite/tests/test_api_variants.py \
  creative_suite/tests/test_api_packs.py \
  creative_suite/tests/test_api_forge_demos.py \
  creative_suite/tests/test_forge_router.py \
  creative_suite/tests/test_app_root_redirect.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add \
  docs/reference/cockpit-v2-contract.md \
  docs/claude_designer/Unified\ Nav\ Shell\ Design\ v2.html \
  docs/superpowers/plans/EXECUTION_STATUS.md \
  docs/visual-record/README.md \
  docs/visual-record/2026-04-21/
git commit -m "docs(cockpit): reconcile shell contract and visual record"
```

---

## Self-Review

### Spec coverage
- Current shell contract: covered by Task 1 and Task 5.
- Broken CREATIVE asset/queue/pack flows: covered by Task 2 and Task 3.
- Broken LAB payload copy: covered by Task 4.
- Lifecycle/mount cleanup gaps: covered by Task 4.
- Documentation and visual-record drift: covered by Task 5.

### Placeholder scan
- No `TODO`, `TBD`, or “handle appropriately” placeholders were used.
- Every task contains exact file paths, concrete code snippets, and run commands.

### Type consistency
- Current canonical mode/page names are `studio|lab|creative` and `clips|edit|demos|extraction|patterns|annotate|flags|forge|engine|textures|sprites|skins|maps|md3|prompts|queue|packs`.
- Asset browser filter uses `kind`, not `category`, so the backend and frontend stay aligned on one shell-specific contract.

---

Plan complete and saved to `docs/superpowers/plans/2026-04-21-cockpit-ui-closeout-stabilization.md`. Two execution options:

1. Subagent-Driven (recommended) - I dispatch a fresh subagent per task, review between tasks, fast iteration

2. Inline Execution - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
