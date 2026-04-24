/**
 * PANTHEON STUDIO — NLE Editor
 * studio-edit.js  (v2 — permanent 4-panel layout, no tab-strip)
 *
 * Layout:
 *   ┌─ LIBRARY ──┬─ VIEWER ──────┬─ INSPECTOR ─┐
 *   │  clips     │  preview      │  props/fx   │
 *   ├────────────┴───────────────┴─────────────┤
 *   │  TIMELINE  (clips · audio · beats)       │
 *   └─────────────────────────────────────────┘
 *
 * Sub-panels delegated to existing modules:
 *   VIEWER   → StudioPreview.mount()
 *   INSPECTOR→ StudioInspector.mount()  + "EDIT GRAPH" button → FX modal
 *   TIMELINE → StudioTimeline + StudioAudio + StudioBeatMarkers stacked
 *   FX MODAL → StudioLiteGraph.mount() in a full-screen overlay
 *
 * Library is implemented inline here (tier filter + drag-drop reorder).
 *
 * Exposed on: window.StudioEdit
 * Rule UI-1: DOM via createElement/textContent only.
 * Rule UI-2: state from StudioStore, no local drift.
 */
(function (global) {
  'use strict';

  // ── Module state ────────────────────────────────────────────────────────────
  var _root       = null;
  var _fxModal    = null;
  var _libListEl  = null;
  var _libStatEl  = null;
  var _clips      = [];
  var _filter     = { tier: 'ALL', text: '' };
  var _dragIdx    = null;
  var _activeMods = [];
  var _playBtnUnsub = null;
  var _storeUnsub = null;
  var _saveTimer  = null;
  var _inspInner  = null;
  var _filterBtns = null;

  var TIER_COLOR = { T1: '#e8b923', T2: '#4a9eff', T3: '#7a7a9a' };
  var TIERS = ['ALL', 'T1', 'T2', 'T3'];

  // ── Library helpers ──────────────────────────────────────────────────────────

  function _loadClips(partNum) {
    if (!_libListEl) return;
    _clips = [];

    var ph = document.createElement('div');
    ph.className = 'nle-lib-empty';
    if (!partNum) {
      ph.textContent = '← Select a part';
      _libListEl.replaceChildren(ph);
      _updateLibStat();
      return;
    }
    ph.textContent = 'Loading clips…';
    _libListEl.replaceChildren(ph);

    fetch('/api/studio/part/' + partNum + '/clips', {
      signal: AbortSignal.timeout(10000),
    })
      .then(function (r) { return r.ok ? r.json() : { clips: [] }; })
      .then(function (d) {
        _clips = (d.clips || []).map(function (c, i) {
          return Object.assign({}, c, { _i: i });
        });
        _renderLibList();
        _updateLibStat();
      })
      .catch(function (e) {
        if (!_libListEl) return;
        var err = document.createElement('div');
        err.className = 'nle-lib-empty';
        err.textContent = 'Error: ' + e.message;
        _libListEl.replaceChildren(err);
      });
  }

  function _visibleClips() {
    var txt = (_filter.text || '').toLowerCase();
    return _clips.filter(function (c) {
      if (_filter.tier !== 'ALL' && c.tier !== _filter.tier) return false;
      if (txt) {
        var haystack = ((c.name || '') + ' ' + (c.weapon || '') + ' ' + (c.map || '')).toLowerCase();
        if (haystack.indexOf(txt) === -1) return false;
      }
      return true;
    });
  }

  function _updateLibStat() {
    if (!_libStatEl) return;
    var vis = _visibleClips();
    if (!_clips.length) {
      _libStatEl.textContent = '';
      return;
    }
    var t1 = _clips.filter(function (c) { return c.tier === 'T1'; }).length;
    var t2 = _clips.filter(function (c) { return c.tier === 'T2'; }).length;
    var t3 = _clips.filter(function (c) { return c.tier === 'T3'; }).length;
    _libStatEl.textContent =
      _clips.length + ' clips' +
      (t1 ? ' · ' + t1 + ' T1' : '') +
      (t2 ? ' · ' + t2 + ' T2' : '') +
      (t3 ? ' · ' + t3 + ' T3' : '') +
      (vis.length !== _clips.length ? ' (' + vis.length + ' shown)' : '');
  }

  function _renderLibList() {
    if (!_libListEl) return;
    var vis = _visibleClips();
    var store = global.StudioStore;
    var sel   = store ? store.getState().selectedClip : null;

    if (!vis.length) {
      var ph = document.createElement('div');
      ph.className = 'nle-lib-empty';
      ph.textContent = _clips.length ? 'No clips match filter.' : 'No clips.';
      _libListEl.replaceChildren(ph);
      return;
    }

    var frag = document.createDocumentFragment();
    vis.forEach(function (clip, vi) {
      var isActive = sel && sel._i === clip._i;

      var row = document.createElement('div');
      row.className = 'nle-clip-row' + (isActive ? ' active' : '');
      row.setAttribute('draggable', 'true');
      row.setAttribute('data-i', clip._i);

      // Tier badge
      var badge = document.createElement('span');
      badge.className = 'nle-tier-badge';
      badge.style.background = TIER_COLOR[clip.tier] || '#555';
      badge.textContent = clip.tier || '??';
      row.appendChild(badge);

      // Info block
      var info = document.createElement('div');
      info.className = 'nle-clip-info';

      var nameEl = document.createElement('div');
      nameEl.className = 'nle-clip-name';
      var rawName = clip.name || (clip.path ? clip.path.split(/[\\/]/).pop() : '(unnamed)');
      nameEl.textContent = rawName;
      info.appendChild(nameEl);

      var subParts = [];
      if (clip.weapon)     subParts.push(clip.weapon.toUpperCase());
      if (clip.map)        subParts.push(clip.map);
      if (clip.duration_s) subParts.push(Number(clip.duration_s).toFixed(1) + 's');
      if (clip.has_pair)   subParts.push('FL');
      var subEl = document.createElement('div');
      subEl.className = 'nle-clip-sub';
      subEl.textContent = subParts.join(' · ');
      info.appendChild(subEl);
      row.appendChild(info);

      // Drag handle
      var handle = document.createElement('span');
      handle.className = 'nle-drag-handle';
      handle.textContent = '⠿';
      row.appendChild(handle);

      // ── Drag events ────────────────────────────────────────────────────────
      row.addEventListener('dragstart', function (e) {
        _dragIdx = clip._i;
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', String(clip._i));
        // Also publish NLE clip payload so canvas timeline can accept drops
        var payload = JSON.stringify({
          clip_path:  clip.path || clip.clip_path || '',
          tier:       clip.tier       || 'T2',
          is_fl:      clip.is_fl      || false,
          pair_path:  clip.pair_path  || null,
          duration_s: clip.duration_s || null,
          role:       'body'
        });
        e.dataTransfer.setData('application/x-nle-clip', payload);
        row.classList.add('dragging');
      });
      row.addEventListener('dragend', function () {
        row.classList.remove('dragging');
        if (_libListEl) {
          _libListEl.querySelectorAll('.nle-clip-row.dragover')
            .forEach(function (el) { el.classList.remove('dragover'); });
        }
      });
      row.addEventListener('dragover', function (e) {
        if (_dragIdx === null) return;
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        row.classList.add('dragover');
      });
      row.addEventListener('dragleave', function () {
        row.classList.remove('dragover');
      });
      row.addEventListener('drop', function (e) {
        e.preventDefault();
        row.classList.remove('dragover');
        if (_dragIdx === null || _dragIdx === clip._i) { _dragIdx = null; return; }
        var fromI = _clips.findIndex(function (c) { return c._i === _dragIdx; });
        var toI   = _clips.findIndex(function (c) { return c._i === clip._i; });
        if (fromI === -1 || toI === -1) { _dragIdx = null; return; }
        var moved = _clips.splice(fromI, 1)[0];
        _clips.splice(toI, 0, moved);
        _clips.forEach(function (c, i) { c._i = i; });
        _dragIdx = null;
        _renderLibList();
        _updateLibStat();
        _scheduleSave();
      });

      // ── Click: select ──────────────────────────────────────────────────────
      row.addEventListener('click', function () {
        if (store) store.dispatch({ type: 'SET_SELECTED_CLIP', payload: clip });
        _renderLibList();
      });

      frag.appendChild(row);
    });

    _libListEl.replaceChildren(frag);
  }

  function _scheduleSave() {
    var store = global.StudioStore;
    if (!store) return;
    var part = store.getState().activePart;
    if (!part) return;
    if (_saveTimer) clearTimeout(_saveTimer);
    _saveTimer = setTimeout(function () {
      _saveTimer = null;
      fetch('/api/studio/part/' + part + '/clips', {
        method:  'PUT',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ clips: _clips }),
        signal:  AbortSignal.timeout(6000),
      }).catch(function (e) { console.warn('[NLE] clip save failed', e); });
    }, 600);
  }

  // ── Build: LIBRARY panel ────────────────────────────────────────────────────

  function _buildLibrary(container) {
    // Header
    var hdr = document.createElement('div');
    hdr.className = 'nle-panel-hdr';
    var title = document.createElement('span');
    title.className = 'nle-panel-title';
    title.textContent = 'LIBRARY';
    hdr.appendChild(title);
    _libStatEl = document.createElement('span');
    _libStatEl.className = 'nle-panel-stat';
    hdr.appendChild(_libStatEl);
    container.appendChild(hdr);

    // Tier filter row
    var filterRow = document.createElement('div');
    filterRow.className = 'nle-filter-row';
    _filterBtns = [];
    TIERS.forEach(function (tier) {
      var btn = document.createElement('button');
      btn.className = 'nle-filter-btn' + (tier === _filter.tier ? ' active' : '');
      btn.textContent = tier;
      btn.addEventListener('click', function () {
        _filter.tier = tier;
        _filterBtns.forEach(function (b, i) {
          b.classList.toggle('active', TIERS[i] === tier);
        });
        _renderLibList();
        _updateLibStat();
      });
      filterRow.appendChild(btn);
      _filterBtns.push(btn);
    });
    container.appendChild(filterRow);

    // Search
    var searchWrap = document.createElement('div');
    searchWrap.className = 'nle-lib-search-wrap';
    var searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.className = 'nle-lib-search';
    searchInput.placeholder = 'Filter clips…';
    searchInput.addEventListener('input', function () {
      _filter.text = searchInput.value;
      _renderLibList();
      _updateLibStat();
    });
    searchWrap.appendChild(searchInput);
    container.appendChild(searchWrap);

    // Clip scroll list
    _libListEl = document.createElement('div');
    _libListEl.className = 'nle-lib-list';
    container.appendChild(_libListEl);
  }

  // ── Build: INSPECTOR panel (DOM only — sub-module mounted after DOM insert) ──

  var _inspSlot   = null;
  var _viewerSlot = null;
  var _tlSlot     = null;
  var _audioSlot  = null;
  var _beatSlot   = null;

  function _buildInspector(container) {
    // "EDIT GRAPH" button row
    var fxRow = document.createElement('div');
    fxRow.className = 'nle-insp-fxrow';
    var fxBtn = document.createElement('button');
    fxBtn.className = 'nle-insp-fxbtn';
    fxBtn.textContent = '\u2B21  EDIT GRAPH';
    fxBtn.addEventListener('click', _openFxModal);
    fxRow.appendChild(fxBtn);
    container.appendChild(fxRow);

    _inspInner = document.createElement('div');
    _inspInner.className = 'nle-insp-inner';
    container.appendChild(_inspInner);
  }

  // ── Build: ACTION BAR (top strip — buttons + meta) ──────────────────────────

  function _buildActionBar(container) {
    var meta = document.createElement('span');
    meta.className = 'nle-action-meta';
    meta.id = 'nle-tl-meta';
    container.appendChild(meta);

    var sep0 = document.createElement('span');
    sep0.className = 'nle-action-sep';
    container.appendChild(sep0);

    // ── Transport: REW / PLAY / STOP ──────────────────────────────────────────
    var rewBtn = document.createElement('button');
    rewBtn.className = 'nle-tl-ctl-btn';
    rewBtn.title = 'Rewind';
    rewBtn.textContent = '\u23EE';
    rewBtn.addEventListener('click', function () {
      var s = global.StudioStore;
      if (s) { s.dispatch({ type: 'SET_PLAYING', payload: false }); s.dispatch({ type: 'SET_CURRENT_TIME', payload: 0 }); }
    });
    container.appendChild(rewBtn);

    var playBtn = document.createElement('button');
    playBtn.className = 'nle-tl-ctl-btn';
    playBtn.id = 'nle-play-btn';
    playBtn.textContent = '\u25B6';
    playBtn.style.cssText = 'min-width:28px;background:#1a2a1a;color:#6dbc6d;';
    playBtn.addEventListener('click', function () {
      var s = global.StudioStore;
      if (!s) return;
      var playing = !s.getState().isPlaying;
      s.dispatch({ type: 'SET_PLAYING', payload: playing });
      playBtn.textContent = playing ? '\u23F8' : '\u25B6';
      playBtn.style.background = playing ? '#0a1a0a' : '#1a2a1a';
    });
    container.appendChild(playBtn);

    // Keep play button in sync with store changes from outside
    (function () {
      var s = global.StudioStore;
      if (!s) return;
      _playBtnUnsub = s.subscribe(function (state) {
        playBtn.textContent = state.isPlaying ? '\u23F8' : '\u25B6';
        playBtn.style.background = state.isPlaying ? '#0a1a0a' : '#1a2a1a';
      });
    }());

    var sep1 = document.createElement('span');
    sep1.className = 'nle-action-sep';
    container.appendChild(sep1);

    var zoomLbl = document.createElement('span');
    zoomLbl.className = 'nle-tl-ctl-lbl';
    zoomLbl.textContent = 'ZOOM';
    container.appendChild(zoomLbl);

    var _zoom = 60;
    ['\u2212', '+'].forEach(function (sym, i) {
      var b = document.createElement('button');
      b.className = 'nle-tl-ctl-btn';
      b.textContent = sym;
      b.addEventListener('click', function () {
        _zoom = i === 0 ? Math.max(10, _zoom - 10) : Math.min(300, _zoom + 10);
        var nle = global.StudioTimelineNLE;
        if (nle && typeof nle.setZoom === 'function') nle.setZoom(_zoom);
      });
      container.appendChild(b);
    });

    var fitBtn = document.createElement('button');
    fitBtn.className = 'nle-tl-ctl-btn';
    fitBtn.textContent = 'FIT';
    fitBtn.style.cssText = 'font-size:9px;letter-spacing:0.1em;padding:1px 6px;';
    fitBtn.addEventListener('click', function () {
      var nle = global.StudioTimelineNLE;
      if (nle && typeof nle.fitZoom === 'function') {
        var z = nle.fitZoom();
        if (z) _zoom = z;
      }
    });
    container.appendChild(fitBtn);

    var sep2 = document.createElement('span');
    sep2.className = 'nle-action-sep';
    container.appendChild(sep2);

    var spacer = document.createElement('span');
    spacer.style.flex = '1';
    container.appendChild(spacer);

    var randBtn = document.createElement('button');
    randBtn.className = 'nle-gen-btn nle-randomize-btn';
    randBtn.textContent = '\u2684 RANDOMIZE';
    randBtn.addEventListener('click', _triggerRandomize);
    container.appendChild(randBtn);

    var musicBtn = document.createElement('button');
    musicBtn.className = 'nle-gen-btn nle-music-btn';
    musicBtn.textContent = '\u266B MUSIC';
    musicBtn.addEventListener('click', _triggerMusicGenerate);
    container.appendChild(musicBtn);

    var genBtn = document.createElement('button');
    genBtn.className = 'nle-gen-btn';
    genBtn.textContent = '\u25B6 RENDER';
    genBtn.addEventListener('click', _triggerGenerate);
    container.appendChild(genBtn);
  }

  // ── Build: TIMELINE panel (legacy stub — no longer used in v3 layout) ───────
  function _buildTimeline(_container) { /* slots set in mount() directly */ }

  // ── Mount sub-modules (called AFTER slot.replaceChildren so DOM is live) ────

  function _mountSubModules() {
    // Viewer / Preview
    if (_viewerSlot) {
      var preview = global.StudioPreview;
      if (preview && typeof preview.mount === 'function') {
        try { preview.mount(_viewerSlot); _activeMods.push(preview); }
        catch (e) { console.error('[NLE] Preview mount', e); }
      }
    }

    // Inspector
    if (_inspInner) {
      var insp = global.StudioInspector;
      if (insp && typeof insp.mount === 'function') {
        try { insp.mount(_inspInner); _activeMods.push(insp); }
        catch (e) {
          console.error('[NLE] Inspector mount', e);
          var phI = document.createElement('div');
          phI.className = 'nle-lib-empty';
          phI.textContent = 'Inspector unavailable.';
          _inspInner.appendChild(phI);
        }
      }
    }

    // NLE Timeline canvas (primary)
    if (_tlSlot) {
      var nle = global.StudioTimelineNLE;
      if (nle && typeof nle.mount === 'function') {
        try { nle.mount(_tlSlot); _activeMods.push(nle); }
        catch (e) { console.error('[NLE] TimelineNLE mount', e); }
      } else {
        // fallback to legacy timeline if NLE not loaded
        var tl = global.StudioTimeline;
        if (tl && typeof tl.mount === 'function') {
          try { tl.mount(_tlSlot); _activeMods.push(tl); }
          catch (e2) { console.error('[NLE] Timeline mount', e2); }
        }
      }
    }

    // Audio
    if (_audioSlot) {
      var audio = global.StudioAudio;
      if (audio && typeof audio.mount === 'function') {
        try { audio.mount(_audioSlot); _activeMods.push(audio); }
        catch (e) { console.error('[NLE] Audio mount', e); }
      }
    }

    // Beat markers
    if (_beatSlot) {
      var bm = global.StudioBeatMarkers;
      if (bm && typeof bm.mount === 'function') {
        try { bm.mount(_beatSlot); _activeMods.push(bm); }
        catch (e) { console.error('[NLE] BeatMarkers mount', e); }
      }
    }
  }

  // ── FX Graph modal ──────────────────────────────────────────────────────────

  function _openFxModal() {
    if (_fxModal) return;

    _fxModal = document.createElement('div');
    _fxModal.className = 'nle-fx-backdrop';
    _fxModal.addEventListener('click', function (e) {
      if (e.target === _fxModal) _closeFxModal();
    });

    var dlg = document.createElement('div');
    dlg.className = 'nle-fx-dlg';

    var hdr = document.createElement('div');
    hdr.className = 'nle-fx-hdr';
    var t = document.createElement('span');
    t.className = 'nle-fx-title';
    t.textContent = 'FX GRAPH';
    var closeBtn = document.createElement('button');
    closeBtn.className = 'nle-fx-close';
    closeBtn.textContent = '\u2715';
    closeBtn.addEventListener('click', _closeFxModal);
    hdr.appendChild(t);
    hdr.appendChild(closeBtn);
    dlg.appendChild(hdr);

    var body = document.createElement('div');
    body.className = 'nle-fx-body';
    dlg.appendChild(body);

    _fxModal.appendChild(dlg);
    document.body.appendChild(_fxModal);

    var lg = global.StudioLiteGraph;
    if (lg && typeof lg.mount === 'function') {
      try { lg.mount(body); }
      catch (e) {
        var ph = document.createElement('div');
        ph.style.padding = '20px';
        ph.style.color = '#888';
        ph.style.fontFamily = 'Consolas, monospace';
        ph.style.fontSize = '12px';
        ph.textContent = 'StudioLiteGraph not available: ' + e.message;
        body.appendChild(ph);
      }
    }
  }

  function _closeFxModal() {
    if (!_fxModal) return;
    var lg = global.StudioLiteGraph;
    if (lg && typeof lg.unmount === 'function') {
      try { lg.unmount(); } catch (e) {}
    }
    if (_fxModal.parentNode) _fxModal.parentNode.removeChild(_fxModal);
    _fxModal = null;
  }

  // ── Generate ────────────────────────────────────────────────────────────────

  function _triggerGenerate() {
    var store = global.StudioStore;
    if (!store) return;
    var part = store.getState().activePart;
    if (!part) {
      store.dispatch({ type: 'SET_STATUS_MSG', payload: 'Select a Part first.' });
      return;
    }
    store.dispatch({ type: 'SET_STATUS_MSG', payload: 'Generating Part ' + part + '\u2026' });
    fetch('/api/phase1/parts/' + part + '/rebuild', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({}),
      signal:  AbortSignal.timeout(10000),
    })
      .then(function (r) { return r.ok ? r.json() : Promise.reject('HTTP ' + r.status); })
      .then(function (d) {
        store.dispatch({
          type:    'SET_STATUS_MSG',
          payload: 'Part ' + part + ' queued \u2014 job ' + (d.job_id || '?'),
        });
      })
      .catch(function (e) {
        store.dispatch({ type: 'SET_STATUS_MSG', payload: 'Generate failed: ' + e });
      });
  }

  // ── Randomizer ──────────────────────────────────────────────────────────────

  var _randConfirmBar = null;

  function _triggerRandomize() {
    var store = global.StudioStore;
    if (!store) return;
    var part = store.getState().activePart;
    if (!part) {
      store.dispatch({ type: 'SET_STATUS_MSG', payload: 'Select a Part first.' });
      return;
    }
    fetch('/api/studio/part/' + part + '/randomize', { method: 'POST' })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var clips = data.body_clips || [];
        var nle = global.StudioTimelineNLE;
        if (nle) nle.showGhostPreview(clips);
        _showRandConfirmBar(clips.length);
      })
      .catch(function (err) {
        if (store) store.dispatch({ type: 'SET_STATUS_MSG', payload: 'Randomize failed: ' + err });
      });
  }

  function _showRandConfirmBar(count) {
    if (_randConfirmBar) _randConfirmBar.remove();
    _randConfirmBar = document.createElement('div');
    _randConfirmBar.className = 'nle-rand-bar';

    var msg = document.createElement('span');
    msg.className = 'nle-rand-msg';
    msg.textContent = 'Preview: ' + count + ' clips re-ordered';
    _randConfirmBar.appendChild(msg);

    function _makeBtn(label, cls, fn) {
      var b = document.createElement('button');
      b.className = 'nle-gen-btn ' + cls;
      b.textContent = label;
      b.addEventListener('click', fn);
      return b;
    }

    _randConfirmBar.appendChild(_makeBtn('ACCEPT', 'nle-accept-btn', function () {
      var nle = global.StudioTimelineNLE;
      if (nle) nle.acceptGhostPreview();
      _randConfirmBar.remove(); _randConfirmBar = null;
    }));
    _randConfirmBar.appendChild(_makeBtn('TRY AGAIN', '', function () {
      var nle = global.StudioTimelineNLE;
      if (nle) nle.clearGhostPreview();
      _randConfirmBar.remove(); _randConfirmBar = null;
      _triggerRandomize();
    }));
    _randConfirmBar.appendChild(_makeBtn('CANCEL', '', function () {
      var nle = global.StudioTimelineNLE;
      if (nle) nle.clearGhostPreview();
      _randConfirmBar.remove(); _randConfirmBar = null;
    }));

    // Insert above timeline row
    if (_root) _root.insertBefore(_randConfirmBar, _root.lastElementChild);
  }

  // ── Music Manager Panel (Sprint 2) ─────────────────────────────────────────
  //
  // Layout:
  //   MUSIC MANAGER header + close
  //   ┌─ INTRO slot   (assigned track or empty) ─ [CHANGE] [✕]
  //   ├─ MAIN 1 slot  ─ [CHANGE] [✕]
  //   ├─ MAIN 2 slot  ─ [CHANGE] [✕]    (optional extra main)
  //   └─ OUTRO slot   ─ [CHANGE] [✕]
  //   [+ ADD SLOT]  (adds main_2 if main_1 filled, etc.)
  //
  // Library Browser Modal:
  //   Overlay → search input → BPM filter → scrollable track list → SELECT
  //
  // Beat Recs Section (integrated, requires a music assignment for real BPM):
  //   Shows per-clip slowmo/speedup suggestions with APPLY + APPLY ALL

  var _musicPanel    = null;
  var _libraryModal  = null;
  var _libraryCache  = null;   // cached browse response

  // Role ordering used for position field
  var _ROLE_POSITION = { intro: 0, main_1: 1, main_2: 2, outro: 3 };
  var _ROLE_LABELS   = { intro: 'INTRO', main_1: 'MAIN', main_2: 'MAIN 2', outro: 'OUTRO' };

  function _fmtDur(s) {
    var n = Number(s);
    if (!n || isNaN(n)) return '';
    var m   = Math.floor(n / 60);
    var sec = Math.floor(n % 60);
    return m + ':' + (sec < 10 ? '0' : '') + sec;
  }

  // ── Entry point (MUSIC action-bar button) ────────────────────────────────────
  function _triggerMusicGenerate() {
    var store = global.StudioStore;
    if (!store) return;
    var part = store.getState().activePart;
    if (!part) {
      store.dispatch({ type: 'SET_STATUS_MSG', payload: 'Select a Part first.' });
      return;
    }
    if (_musicPanel) { _musicPanel.remove(); _musicPanel = null; return; }
    _openMusicManager(part);
  }

  // ── Music Manager Panel ──────────────────────────────────────────────────────
  function _openMusicManager(part) {
    if (_musicPanel) _musicPanel.remove();
    _musicPanel = document.createElement('div');
    _musicPanel.className = 'nle-music-panel';

    // Header
    var hdr = document.createElement('div');
    hdr.className = 'nle-music-panel-hdr';
    var title = document.createElement('span');
    title.className = 'nle-music-panel-title';
    title.textContent = 'MUSIC MANAGER \u2014 Part ' + part;
    var closeBtn = document.createElement('button');
    closeBtn.className = 'nle-music-panel-close';
    closeBtn.textContent = '\u2715';
    closeBtn.addEventListener('click', function () { _musicPanel.remove(); _musicPanel = null; });
    hdr.appendChild(title);
    hdr.appendChild(closeBtn);
    _musicPanel.appendChild(hdr);

    // Slots container (populated after fetch)
    var slotsEl = document.createElement('div');
    slotsEl.className = 'nle-music-slots';
    _musicPanel.appendChild(slotsEl);

    // Beat recs section (separated below slots)
    var beatSection = document.createElement('div');
    beatSection.className = 'nle-music-track-list';
    beatSection.style.borderTop = '1px solid #2a2a2a';
    beatSection.style.marginTop = '4px';
    beatSection.style.paddingTop = '4px';
    _musicPanel.appendChild(beatSection);

    if (_root) _root.insertBefore(_musicPanel, _root.lastElementChild);

    // Fetch current assignments and render slots
    _refreshSlots(part, slotsEl);
    _renderBeatRecs(beatSection, part);
  }

  function _refreshSlots(part, slotsEl) {
    slotsEl.replaceChildren();
    var loading = document.createElement('div');
    loading.className = 'nle-music-empty';
    loading.textContent = 'Loading\u2026';
    slotsEl.appendChild(loading);

    fetch('/api/studio/part/' + part + '/music_assignments')
      .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
      .then(function (data) {
        slotsEl.replaceChildren();
        var assignments = data.assignments || [];
        // Build a map role → assignment
        var byRole = {};
        assignments.forEach(function (a) { byRole[a.role] = a; });

        // Always show intro + main_1 + outro; show main_2 if assigned or main_1 filled
        var roles = ['intro', 'main_1'];
        if (byRole['main_1'] || byRole['main_2']) roles.push('main_2');
        roles.push('outro');

        roles.forEach(function (role) {
          slotsEl.appendChild(_buildSlotRow(part, role, byRole[role] || null, slotsEl));
        });
      })
      .catch(function () {
        slotsEl.replaceChildren();
        // Fallback: show empty slots
        ['intro', 'main_1', 'outro'].forEach(function (role) {
          slotsEl.appendChild(_buildSlotRow(part, role, null, slotsEl));
        });
      });
  }

  function _buildSlotRow(part, role, assignment, slotsEl) {
    var row = document.createElement('div');
    row.className = 'nle-music-row nle-music-slot-row';

    // Role badge
    var badge = document.createElement('span');
    badge.className = 'nle-music-pct';
    badge.textContent = _ROLE_LABELS[role] || role.toUpperCase();
    row.appendChild(badge);

    if (assignment && assignment.track_filename) {
      // Track info
      var info = document.createElement('span');
      info.className = 'nle-music-info';
      var label = assignment.title || assignment.track_filename;
      if (assignment.artist) label = assignment.artist + ' \u2014 ' + label;
      info.textContent = label;
      row.appendChild(info);

      var meta = document.createElement('span');
      meta.className = 'nle-music-meta';
      var metaParts = [];
      if (assignment.bpm)        metaParts.push(Math.round(assignment.bpm) + ' BPM');
      if (assignment.duration_s) metaParts.push(_fmtDur(assignment.duration_s));
      meta.textContent = metaParts.join('  ');
      row.appendChild(meta);

      // CHANGE button
      var changeBtn = document.createElement('button');
      changeBtn.className = 'nle-music-sel-btn';
      changeBtn.textContent = 'CHANGE';
      (function (r) {
        changeBtn.addEventListener('click', function () {
          _openLibraryBrowser(part, r, slotsEl);
        });
      }(role));
      row.appendChild(changeBtn);

      // DELETE button
      var delBtn = document.createElement('button');
      delBtn.className = 'nle-music-sel-btn';
      delBtn.style.color = '#c44';
      delBtn.textContent = '\u2715';
      (function (r) {
        delBtn.addEventListener('click', function () {
          _deleteAssignment(part, r, slotsEl);
        });
      }(role));
      row.appendChild(delBtn);

    } else {
      // Empty slot
      var emptyInfo = document.createElement('span');
      emptyInfo.className = 'nle-music-info';
      emptyInfo.style.opacity = '0.4';
      emptyInfo.textContent = 'empty';
      row.appendChild(emptyInfo);

      var addBtn = document.createElement('button');
      addBtn.className = 'nle-music-sel-btn';
      addBtn.textContent = '+ ASSIGN';
      (function (r) {
        addBtn.addEventListener('click', function () {
          _openLibraryBrowser(part, r, slotsEl);
        });
      }(role));
      row.appendChild(addBtn);
    }

    return row;
  }

  function _deleteAssignment(part, role, slotsEl) {
    fetch('/api/studio/part/' + part + '/music_assignment/' + role, { method: 'DELETE' })
      .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
      .then(function () { _refreshSlots(part, slotsEl); })
      .catch(function (err) { console.error('[NLE] delete assignment failed', err); });
  }

  // ── Library Browser Modal ────────────────────────────────────────────────────
  function _openLibraryBrowser(part, role, slotsEl) {
    if (_libraryModal) _libraryModal.remove();
    _libraryModal = document.createElement('div');
    _libraryModal.className = 'nle-library-modal-overlay';

    var box = document.createElement('div');
    box.className = 'nle-library-modal-box';

    // Header
    var mhdr = document.createElement('div');
    mhdr.className = 'nle-music-panel-hdr';
    var mtitle = document.createElement('span');
    mtitle.className = 'nle-music-panel-title';
    mtitle.textContent = 'LIBRARY \u2014 Assign to ' + (_ROLE_LABELS[role] || role);
    var mclose = document.createElement('button');
    mclose.className = 'nle-music-panel-close';
    mclose.textContent = '\u2715';
    mclose.addEventListener('click', function () { _libraryModal.remove(); _libraryModal = null; });
    mhdr.appendChild(mtitle);
    mhdr.appendChild(mclose);
    box.appendChild(mhdr);

    // Search + BPM filter bar
    var filterBar = document.createElement('div');
    filterBar.className = 'nle-library-filter-bar';

    var searchInput = document.createElement('input');
    searchInput.type        = 'text';
    searchInput.placeholder = 'Search title, artist\u2026';
    searchInput.className   = 'nle-library-search';

    var bpmLabel = document.createElement('span');
    bpmLabel.className   = 'nle-music-meta';
    bpmLabel.textContent = 'BPM:';

    var bpmMin = document.createElement('input');
    bpmMin.type        = 'number';
    bpmMin.placeholder = 'min';
    bpmMin.className   = 'nle-library-bpm-input';
    bpmMin.min         = '60';
    bpmMin.max         = '220';

    var bpmMax = document.createElement('input');
    bpmMax.type        = 'number';
    bpmMax.placeholder = 'max';
    bpmMax.className   = 'nle-library-bpm-input';
    bpmMax.min         = '60';
    bpmMax.max         = '220';

    filterBar.appendChild(searchInput);
    filterBar.appendChild(bpmLabel);
    filterBar.appendChild(bpmMin);
    filterBar.appendChild(bpmMax);
    box.appendChild(filterBar);

    // Track list
    var trackList = document.createElement('div');
    trackList.className = 'nle-library-track-list';
    box.appendChild(trackList);

    _libraryModal.appendChild(box);
    document.body.appendChild(_libraryModal);

    // Load library (use cache if available)
    var doRender = function (tracks) {
      _libraryCache = tracks;
      _renderLibraryTracks(trackList, tracks, part, role, slotsEl, searchInput, bpmMin, bpmMax);
    };

    var doFilter = function () {
      if (_libraryCache) {
        _renderLibraryTracks(trackList, _libraryCache, part, role, slotsEl, searchInput, bpmMin, bpmMax);
      }
    };

    searchInput.addEventListener('input',  doFilter);
    bpmMin.addEventListener('input',       doFilter);
    bpmMax.addEventListener('input',       doFilter);

    if (_libraryCache) {
      doRender(_libraryCache);
    } else {
      trackList.textContent = 'Loading library\u2026';
      fetch('/api/studio/music/browse')
        .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
        .then(doRender)
        .catch(function (err) {
          trackList.textContent = 'Library load failed: ' + err;
        });
    }
  }

  function _renderLibraryTracks(listEl, allTracks, part, role, slotsEl, searchInput, bpmMin, bpmMax) {
    var q    = (searchInput.value || '').toLowerCase().trim();
    var minB = bpmMin.value ? parseFloat(bpmMin.value) : 0;
    var maxB = bpmMax.value ? parseFloat(bpmMax.value) : Infinity;

    var filtered = allTracks.filter(function (t) {
      if (q) {
        var hay = ((t.title || '') + ' ' + (t.artist || '') + ' ' + (t.filename || '')).toLowerCase();
        if (hay.indexOf(q) === -1) return false;
      }
      if (t.bpm) {
        if (t.bpm < minB || t.bpm > maxB) return false;
      }
      return true;
    });

    listEl.replaceChildren();

    if (!filtered.length) {
      var empty = document.createElement('div');
      empty.className = 'nle-music-empty';
      empty.textContent = allTracks.length ? 'No tracks match filter.' : 'Library empty \u2014 add tracks to engine/music/library/';
      listEl.appendChild(empty);
      return;
    }

    filtered.forEach(function (t) {
      var row = document.createElement('div');
      row.className = 'nle-music-row';

      var info = document.createElement('span');
      info.className = 'nle-music-info';
      var label = t.title || t.filename || '';
      if (t.artist) label = t.artist + ' \u2014 ' + label;
      info.textContent = label;

      var meta = document.createElement('span');
      meta.className = 'nle-music-meta';
      var metaParts = [];
      if (t.bpm)        metaParts.push(Math.round(t.bpm) + ' BPM');
      if (t.duration_s) metaParts.push(_fmtDur(t.duration_s));
      meta.textContent = metaParts.join('  ');

      var selBtn = document.createElement('button');
      selBtn.className = 'nle-music-sel-btn';
      selBtn.textContent = 'SELECT';
      (function (track) {
        selBtn.addEventListener('click', function () {
          _assignTrack(part, role, track, slotsEl);
          if (_libraryModal) { _libraryModal.remove(); _libraryModal = null; }
        });
      }(t));

      row.appendChild(info);
      row.appendChild(meta);
      row.appendChild(selBtn);
      listEl.appendChild(row);
    });
  }

  function _assignTrack(part, role, track, slotsEl) {
    fetch('/api/studio/part/' + part + '/music_assignment', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        role:           role,
        track_filename: track.filename,
        artist:         track.artist  || null,
        title:          track.title   || null,
        bpm:            track.bpm     || null,
        duration_s:     track.duration_s || null,
        position:       _ROLE_POSITION[role] !== undefined ? _ROLE_POSITION[role] : 1,
      }),
    })
      .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
      .then(function () { _refreshSlots(part, slotsEl); })
      .catch(function (err) { console.error('[NLE] assign track failed', err); });
  }

  // ── Beat Recommendations Section ─────────────────────────────────────────────
  function _renderBeatRecs(container, partNum) {
    var sectionHdr = document.createElement('div');
    sectionHdr.className = 'nle-music-panel-hdr';
    sectionHdr.style.fontSize = '10px';
    sectionHdr.style.opacity = '0.7';
    var sectionTitle = document.createElement('span');
    sectionTitle.textContent = 'CLIP BEAT RECOMMENDATIONS';
    sectionHdr.appendChild(sectionTitle);
    container.appendChild(sectionHdr);

    var loading = document.createElement('div');
    loading.className = 'nle-music-empty';
    loading.textContent = 'Analyzing\u2026';
    container.appendChild(loading);

    fetch('/api/studio/part/' + partNum + '/clip_recommendations')
      .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
      .then(function (data) {
        loading.remove();

        // BPM info line
        var bpmInfo = document.createElement('div');
        bpmInfo.className = 'nle-music-empty';
        bpmInfo.style.opacity = '0.5';
        bpmInfo.style.fontSize = '10px';
        bpmInfo.textContent = 'BPM: ' + Math.round(data.bpm || 138) + '  beat: ' + ((data.beat_interval_s || 0.43) * 1000).toFixed(0) + 'ms';
        container.appendChild(bpmInfo);

        var recs = (data.recommendations || []).filter(function (r) { return r.suggestion !== 'none'; });
        if (!recs.length) {
          var none = document.createElement('div');
          none.className = 'nle-music-empty';
          none.textContent = 'All clips are beat-aligned \u2713';
          container.appendChild(none);
          return;
        }

        // APPLY ALL button
        var applyAllBtn = document.createElement('button');
        applyAllBtn.className = 'nle-music-sel-btn';
        applyAllBtn.style.margin = '4px 0';
        applyAllBtn.style.width = '100%';
        applyAllBtn.textContent = 'APPLY ALL (' + recs.length + ')';
        container.appendChild(applyAllBtn);

        var pending = { recs: recs };   // keep ref for apply-all

        applyAllBtn.addEventListener('click', function () {
          applyAllBtn.disabled = true;
          applyAllBtn.textContent = 'Applying\u2026';
          _applyAllBeatRecs(partNum, pending.recs, applyAllBtn, container);
        });

        recs.forEach(function (rec) {
          var row = document.createElement('div');
          row.className = 'nle-music-row';

          var badge = document.createElement('span');
          badge.className = 'nle-music-pct';
          badge.textContent = rec.tier;

          var info = document.createElement('span');
          info.className = 'nle-music-info';
          info.textContent = rec.clip_path.split(/[/\\]/).pop().replace(/\.avi$/i, '');

          var meta = document.createElement('span');
          meta.className = 'nle-music-meta';
          meta.textContent = rec.suggestion.toUpperCase() + ' ' + rec.recommended_rate + '\u00d7'
            + '  \u0394' + (rec.beat_offset_s * 1000).toFixed(0) + 'ms';

          var applyBtn = document.createElement('button');
          applyBtn.className = 'nle-music-sel-btn';
          applyBtn.textContent = 'APPLY';
          (function (r, btn) {
            btn.addEventListener('click', function () {
              _applySingleBeatRec(partNum, r, btn);
            });
          }(rec, applyBtn));

          row.appendChild(badge);
          row.appendChild(info);
          row.appendChild(meta);
          row.appendChild(applyBtn);
          container.appendChild(row);
        });
      })
      .catch(function (err) {
        loading.textContent = 'Beat analysis failed: ' + err;
      });
  }

  function _applySingleBeatRec(partNum, rec, btn) {
    fetch('/api/studio/part/' + partNum + '/arrangement/' + rec.clip_id + '/fx', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        effect_type: rec.suggestion,
        params:      { rate: rec.recommended_rate },
        enabled:     true,
        position:    0,
      }),
    })
      .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
      .then(function () {
        btn.textContent = '\u2713';
        btn.disabled = true;
      })
      .catch(function (err) { console.error('[NLE] apply beat rec failed', err); });
  }

  function _applyAllBeatRecs(partNum, recs, allBtn, container) {
    var promises = recs.map(function (rec) {
      return fetch('/api/studio/part/' + partNum + '/arrangement/' + rec.clip_id + '/fx', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          effect_type: rec.suggestion,
          params:      { rate: rec.recommended_rate },
          enabled:     true,
          position:    0,
        }),
      }).then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); });
    });
    Promise.all(promises)
      .then(function () {
        allBtn.textContent = '\u2713 ALL APPLIED (' + recs.length + ')';
        // Grey out all individual apply buttons
        container.querySelectorAll('.nle-music-sel-btn').forEach(function (b) {
          if (b !== allBtn) { b.disabled = true; b.textContent = '\u2713'; }
        });
      })
      .catch(function (err) {
        allBtn.textContent = 'APPLY ALL (some failed)';
        allBtn.disabled = false;
        console.error('[NLE] apply all beat recs failed', err);
      });
  }

  // ── Mount ───────────────────────────────────────────────────────────────────

  function mount(slot) {
    _activeMods  = [];
    _clips       = [];
    _filter      = { tier: 'ALL', text: '' };
    _dragIdx     = null;
    _libListEl   = null;
    _libStatEl   = null;
    _inspInner   = null;
    _filterBtns  = null;
    _viewerSlot  = null;
    _tlSlot      = null;
    _audioSlot   = null;
    _beatSlot    = null;

    // Root: action-bar / body
    _root = document.createElement('div');
    _root.className = 'nle-root';

    // ── Action bar ────────────────────────────────────────────────────────────
    var actionBar = document.createElement('div');
    actionBar.className = 'nle-action-bar';
    _buildActionBar(actionBar);
    _root.appendChild(actionBar);

    // ── Workspace: upper (3-col) + lower (timeline) ──────────────────────────
    var workspace = document.createElement('div');
    workspace.className = 'nle-workspace';

    // Upper zone: library | viewer/preview | inspector
    var upper = document.createElement('div');
    upper.className = 'nle-upper';

    var libPanel = document.createElement('div');
    libPanel.className = 'nle-panel nle-library';
    _buildLibrary(libPanel);
    upper.appendChild(libPanel);

    // Viewer (center-top): preview pane
    _viewerSlot = document.createElement('div');
    _viewerSlot.className = 'nle-panel nle-viewer';
    var vHdr = document.createElement('div');
    vHdr.className = 'nle-panel-hdr';
    var vTitle = document.createElement('span');
    vTitle.className = 'nle-panel-title';
    vTitle.textContent = 'PREVIEW';
    vHdr.appendChild(vTitle);
    _viewerSlot.appendChild(vHdr);
    // preview mounts directly into the viewer panel body (below the header)
    upper.appendChild(_viewerSlot);

    var inspPanel = document.createElement('div');
    inspPanel.className = 'nle-panel nle-inspector';
    _buildInspector(inspPanel);
    upper.appendChild(inspPanel);

    workspace.appendChild(upper);

    // Lower zone: timeline canvas + audio
    var lower = document.createElement('div');
    lower.className = 'nle-lower';

    _tlSlot = document.createElement('div');
    _tlSlot.className = 'nle-tl-main';
    lower.appendChild(_tlSlot);

    _audioSlot = document.createElement('div');
    _audioSlot.className = 'nle-tl-audio';
    lower.appendChild(_audioSlot);

    _beatSlot = document.createElement('div');
    _beatSlot.className = 'nle-tl-beat';
    _beatSlot.style.height = '32px';
    _beatSlot.style.flexShrink = '0';
    _beatSlot.style.overflow = 'hidden';
    lower.appendChild(_beatSlot);

    workspace.appendChild(lower);
    _root.appendChild(workspace);

    slot.replaceChildren(_root);

    // Mount sub-modules now that DOM is live in the document
    _mountSubModules();

    // ── Store subscription ────────────────────────────────────────────────────
    var store = global.StudioStore;
    if (store) {
      var initPart = store.getState().activePart;
      _loadClips(initPart);
      _updateTlMeta(store.getState());

      _storeUnsub = store.subscribe(function (s, prev) {
        if (s.activePart !== prev.activePart) {
          _loadClips(s.activePart);
        }
        if (s.selectedClip !== prev.selectedClip) {
          _renderLibList();
        }
        if (s.clips !== prev.clips) {
          _updateTlMeta(s);
        }
      });
    }
  }

  function _updateTlMeta(state) {
    var el = document.getElementById('nle-tl-meta');
    if (!el) return;
    var clips = state.clips || [];
    var part  = state.activePart;
    el.textContent = part
      ? 'PART ' + part + '  \u00B7  ' + clips.length + ' CLIPS'
      : '';
  }

  // ── Unmount ──────────────────────────────────────────────────────────────────

  function unmount() {
    _closeFxModal();

    _activeMods.forEach(function (mod) {
      if (mod && typeof mod.unmount === 'function') {
        try { mod.unmount(); } catch (e) {}
      }
    });
    _activeMods = [];

    if (_playBtnUnsub) { _playBtnUnsub(); _playBtnUnsub = null; }
    if (_storeUnsub) { _storeUnsub(); _storeUnsub = null; }
    if (_saveTimer)  { clearTimeout(_saveTimer); _saveTimer = null; }

    _root      = null;
    _libListEl = null;
    _libStatEl = null;
    _inspInner = null;
    _clips     = [];
    _fxModal   = null;
  }

  global.StudioEdit = { mount: mount, unmount: unmount };

}(window));
