/**
 * PANTHEON STUDIO — Clips Browser + Music Assignment
 * studio-clips.js  (v3 — all tiers, drag-and-drop, interactive music)
 *
 * Left column  — expandable parts 1-12.  Expanded view lists ALL clips from
 *   T1 (FP primary, from manifest), T2 (FL scanned), T3 (cinematic scanned).
 *   Clips are draggable; drop reorders the list and auto-saves via
 *   PUT /api/studio/part/{n}/clips.
 *
 * Right column — when a part is selected: music assignment panel.
 *   Shows available tracks with BPM badges, highlights the best BPM match,
 *   lets user assign roles (INTRO / MAIN / OUTRO), then fire RUN BEATMATCH.
 *
 * Exposed on: window.StudioClips
 * Rule UI-1: DOM via createElement/textContent only.
 * Rule UI-2: state mutations via StudioStore.
 */
(function (global) {
  'use strict';

  // ── Constants ─────────────────────────────────────────────────────────────
  var TIER_COLOR = { T1: '#e8b923', T2: '#4a9eff', T3: '#7a7a9a' };
  var TIER_LABEL = { T1: 'FP', T2: 'FL', T3: 'CIN' };
  var SAVE_DEBOUNCE_MS = 600;

  // ── Module state ──────────────────────────────────────────────────────────
  var _slot       = null;
  var _unsub      = null;
  var _partsData  = [];
  var _tracksData = [];
  var _clipsCache = {};   // partN -> clip array (mutable, reflects current order)
  var _expanded   = {};
  var _selPart    = null;
  var _assign     = {};   // partN -> {intro, main[], outro}
  var _inflight   = {};
  var _saveTimer  = {};   // partN -> setTimeout id
  var _musicWrap  = null;
  var _logEl      = null;
  var _listEl     = null; // the left scroll container

  // drag state
  var _dragIdx    = null;
  var _dragPart   = null;

  // ── Logging ───────────────────────────────────────────────────────────────
  function _log(msg, kind) {
    if (!_logEl) return;
    var line = document.createElement('div');
    line.textContent = '[' + new Date().toLocaleTimeString() + '] ' + msg;
    line.style.color = kind === 'err' ? '#ff6666' : kind === 'ok' ? '#9beab1' : '#888';
    line.style.fontSize = '11px';
    _logEl.appendChild(line);
    while (_logEl.childNodes.length > 120) _logEl.removeChild(_logEl.firstChild);
    _logEl.scrollTop = _logEl.scrollHeight;
  }

  // ── Music helpers ─────────────────────────────────────────────────────────
  function _tracksForPart(n) {
    var prefix = 'part' + (n < 10 ? '0' : '') + n + '_music_';
    return _tracksData.filter(function (t) { return t.name.indexOf(prefix) === 0; });
  }

  function _bestBpmMatch(tracks, targetBpm) {
    if (!targetBpm || !tracks.length) return null;
    var best = null, bestDiff = Infinity;
    tracks.forEach(function (t) {
      if (!t.bpm) return;
      var diff = Math.abs(t.bpm - targetBpm);
      if (diff < bestDiff) { bestDiff = diff; best = t.name; }
    });
    return best;
  }

  function _partTargetBpm(n) {
    // Look for a beats.json with tempo data for this part
    var prefix = 'part' + (n < 10 ? '0' : '') + n + '_music';
    var found = _tracksData.find(function (t) { return t.name.indexOf(prefix) === 0 && t.bpm; });
    return found ? found.bpm : null;
  }

  // ── Music assignment persistence ──────────────────────────────────────────
  function _loadAssign(n) {
    if (_assign[n]) return;
    _assign[n] = { intro: null, main: [], outro: null };
    fetch('/api/phase1/parts/' + n + '/music-override', { signal: AbortSignal.timeout(4000) })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) {
        if (!d || !_assign[n]) return;
        _assign[n] = { intro: d.intro || null, main: d.main || [], outro: d.outro || null };
        if (_selPart === n) _renderMusicPanel(n);
      }).catch(function () {});
  }

  function _saveAssign(n) {
    var body = _assign[n] || { intro: null, main: [], outro: null };
    fetch('/api/phase1/parts/' + n + '/music-override', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(5000),
    }).then(function (r) {
      _log(r.ok ? 'Saved music for Part ' + n : 'Save failed ' + r.status, r.ok ? 'ok' : 'err');
    }).catch(function (e) { _log('Save error: ' + e.message, 'err'); });
  }

  // ── Clip order persistence (debounced) ───────────────────────────────────
  function _scheduleClipSave(n) {
    if (_saveTimer[n]) clearTimeout(_saveTimer[n]);
    _saveTimer[n] = setTimeout(function () {
      _saveTimer[n] = null;
      var clips = _clipsCache[n];
      if (!clips) return;
      fetch('/api/studio/part/' + n + '/clips', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ clips: clips }),
        signal: AbortSignal.timeout(6000),
      }).then(function (r) {
        _log(r.ok ? 'Saved order for Part ' + n : 'Order save failed ' + r.status,
             r.ok ? 'ok' : 'err');
      }).catch(function (e) { _log('Order save error: ' + e.message, 'err'); });
    }, SAVE_DEBOUNCE_MS);
  }

  // ── Drag and drop ─────────────────────────────────────────────────────────
  function _onDragStart(e, idx, n) {
    _dragIdx  = idx;
    _dragPart = n;
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', String(idx));
    e.currentTarget.classList.add('sc-clip-dragging');
  }

  function _onDragEnd(e) {
    e.currentTarget.classList.remove('sc-clip-dragging');
    // Remove all drag-over highlights
    if (_listEl) {
      var overs = _listEl.querySelectorAll('.sc-clip-dragover');
      for (var i = 0; i < overs.length; i++) overs[i].classList.remove('sc-clip-dragover');
    }
  }

  function _onDragOver(e, idx) {
    if (_dragPart !== _selPart) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    e.currentTarget.classList.add('sc-clip-dragover');
  }

  function _onDragLeave(e) {
    e.currentTarget.classList.remove('sc-clip-dragover');
  }

  function _onDrop(e, targetIdx, n, rerender) {
    e.preventDefault();
    e.currentTarget.classList.remove('sc-clip-dragover');
    if (_dragPart !== n || _dragIdx === null || _dragIdx === targetIdx) return;

    var clips = _clipsCache[n];
    if (!clips) return;

    // Reorder in-place
    var moved = clips.splice(_dragIdx, 1)[0];
    var insertAt = _dragIdx < targetIdx ? targetIdx - 1 : targetIdx;
    clips.splice(insertAt, 0, moved);
    // Renumber
    clips.forEach(function (c, i) { c.idx = i; });
    _dragIdx  = null;
    _dragPart = null;

    rerender();
    _scheduleClipSave(n);
  }

  // ── Clip list rendering ──────────────────────────────────────────────────
  function _renderClips(container, n) {
    container.replaceChildren();
    var clips = _clipsCache[n] || [];
    if (!clips.length) {
      var empty = document.createElement('div');
      empty.className = 'sc-clip-loading';
      empty.textContent = 'No clips found.';
      container.appendChild(empty);
      return;
    }

    // Group header counts
    var counts = { T1: 0, T2: 0, T3: 0 };
    clips.forEach(function (c) { counts[c.tier] = (counts[c.tier] || 0) + 1; });

    // Tier group headers
    var lastTier = null;

    clips.forEach(function (clip, i) {
      // Tier divider
      if (clip.tier !== lastTier) {
        lastTier = clip.tier;
        var div = document.createElement('div');
        div.className = 'sc-tier-divider';
        div.style.borderLeftColor = TIER_COLOR[clip.tier] || '#555';
        var tl = document.createElement('span');
        tl.style.color = TIER_COLOR[clip.tier] || '#555';
        tl.textContent = clip.tier + ' — ' + TIER_LABEL[clip.tier];
        var tc = document.createElement('span');
        tc.className = 'sc-tier-count';
        tc.textContent = counts[clip.tier] + ' clips';
        div.appendChild(tl);
        div.appendChild(tc);
        container.appendChild(div);
      }

      var row = document.createElement('div');
      row.className = 'sc-clip-row';
      row.setAttribute('draggable', 'true');
      row.setAttribute('data-idx', i);

      // Drag handle
      var handle = document.createElement('span');
      handle.className = 'sc-drag-handle';
      handle.textContent = '\u2B0C'; // ⬌ indicator
      handle.title = 'Drag to reorder';
      row.appendChild(handle);

      // Tier dot
      var dot = document.createElement('span');
      dot.className = 'sc-tier-dot';
      dot.style.background = TIER_COLOR[clip.tier] || '#555';
      row.appendChild(dot);

      // Name
      var nameEl = document.createElement('span');
      nameEl.className = 'sc-clip-name';
      nameEl.textContent = clip.name || clip.path || '(unnamed)';
      row.appendChild(nameEl);

      // Tags
      if (clip.weapon) {
        var wt = document.createElement('span');
        wt.className = 'sc-tag';
        wt.textContent = clip.weapon;
        row.appendChild(wt);
      }
      if (clip.map) {
        var mt = document.createElement('span');
        mt.className = 'sc-tag sc-tag-map';
        mt.textContent = clip.map;
        row.appendChild(mt);
      }
      if (clip.duration_s) {
        var dt = document.createElement('span');
        dt.className = 'sc-clip-dur';
        dt.textContent = Number(clip.duration_s).toFixed(1) + 's';
        row.appendChild(dt);
      }

      // Drag events
      row.addEventListener('dragstart', function (e) { _onDragStart(e, i, n); });
      row.addEventListener('dragend', _onDragEnd);
      row.addEventListener('dragover', function (e) { _onDragOver(e, i); });
      row.addEventListener('dragleave', _onDragLeave);
      row.addEventListener('drop', function (e) {
        _onDrop(e, i, n, function () { _renderClips(container, n); });
      });

      // Click: select part + show music
      row.addEventListener('click', function () {
        var allRows = container.querySelectorAll('.sc-clip-row');
        for (var j = 0; j < allRows.length; j++) allRows[j].classList.remove('active');
        row.classList.add('active');
        if (global.StudioStore) {
          var st = global.StudioStore.getState();
          if (st.activePart !== n) global.StudioStore.dispatch({ type: 'SET_ACTIVE_PART', payload: n });
        }
        _renderMusicPanel(n);
      });

      container.appendChild(row);
    });
  }

  // ── Music panel ───────────────────────────────────────────────────────────
  function _renderMusicPanel(n) {
    if (!_musicWrap) return;
    _musicWrap.replaceChildren();
    _logEl = null;

    var hdr = document.createElement('div');
    hdr.className = 'sc-music-hdr';
    hdr.textContent = 'PART ' + (n < 10 ? '0' : '') + n + ' — MUSIC';
    _musicWrap.appendChild(hdr);

    var tracks = _tracksForPart(n);
    if (!tracks.length) {
      var empty = document.createElement('div');
      empty.className = 'sc-music-empty';
      empty.textContent = 'No music files for Part ' + n + '.\nAdd part' +
        (n < 10 ? '0' : '') + n + '_music_01.mp3 … to creative_suite/engine/music/.';
      _musicWrap.appendChild(empty);
      return;
    }

    var assign   = _assign[n] || { intro: null, main: [], outro: null };
    var targetBpm = _partTargetBpm(n);
    var bestMatch = _bestBpmMatch(tracks, targetBpm);

    // BPM context line
    if (targetBpm) {
      var bpmCtx = document.createElement('div');
      bpmCtx.className = 'sc-music-bpm-ctx';
      bpmCtx.textContent = 'Part target: ' + Math.round(targetBpm) + ' BPM';
      _musicWrap.appendChild(bpmCtx);
    }

    // Track cards
    tracks.forEach(function (track) {
      var isMatch = track.name === bestMatch;

      var card = document.createElement('div');
      card.className = 'sc-track-card' + (isMatch ? ' sc-track-best' : '');

      // Best-match badge
      if (isMatch) {
        var badge = document.createElement('span');
        badge.className = 'sc-match-badge';
        badge.textContent = '\u2605 BEST MATCH';
        card.appendChild(badge);
      }

      var trackTop = document.createElement('div');
      trackTop.className = 'sc-track-top';

      var shortName = track.name
        .replace(/^part\d+_music_0?/, '')
        .replace(/\.(mp3|ogg|wav|m4a)$/i, '');
      var nameEl = document.createElement('span');
      nameEl.className = 'sc-music-name';
      nameEl.textContent = shortName;
      trackTop.appendChild(nameEl);

      if (track.bpm) {
        var bpmBadge = document.createElement('span');
        bpmBadge.className = 'sc-music-bpm';
        bpmBadge.textContent = Math.round(track.bpm) + ' BPM';
        trackTop.appendChild(bpmBadge);
      }
      card.appendChild(trackTop);

      // Role selector
      var roleRow = document.createElement('div');
      roleRow.className = 'sc-role-row';

      var curRole = 'off';
      if (assign.intro === track.name) curRole = 'intro';
      else if (assign.outro === track.name) curRole = 'outro';
      else if (assign.main.indexOf(track.name) !== -1) curRole = 'main';

      ['off', 'intro', 'main', 'outro'].forEach(function (role) {
        var btn = document.createElement('button');
        btn.className = 'sc-role-btn' + (curRole === role ? ' active' : '');
        btn.textContent = role === 'off' ? '—' : role.toUpperCase();
        btn.addEventListener('click', function () {
          var a = _assign[n];
          if (a.intro === track.name) a.intro = null;
          if (a.outro === track.name) a.outro = null;
          a.main = a.main.filter(function (x) { return x !== track.name; });
          if (role === 'intro') a.intro = track.name;
          else if (role === 'outro') a.outro = track.name;
          else if (role === 'main') a.main.push(track.name);
          _saveAssign(n);
          _renderMusicPanel(n); // re-render to reflect new state
        });
        roleRow.appendChild(btn);
      });
      card.appendChild(roleRow);
      _musicWrap.appendChild(card);
    });

    // RUN BEATMATCH
    var btnRow = document.createElement('div');
    btnRow.className = 'sc-beatmatch-row';
    var runBtn = document.createElement('button');
    runBtn.className = 'sc-beatmatch-btn';
    runBtn.textContent = '\u25B6 RUN BEATMATCH';
    runBtn.addEventListener('click', function () {
      runBtn.disabled = true;
      runBtn.textContent = 'QUEUING\u2026';
      _log('Queuing Part ' + n + ' rebuild\u2026', 'info');
      fetch('/api/phase1/parts/' + n + '/rebuild', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
        signal: AbortSignal.timeout(10000),
      }).then(function (r) { return r.ok ? r.json() : Promise.reject('HTTP ' + r.status); })
        .then(function (d) {
          _log('Part ' + n + ' queued — job_id=' + (d.job_id || '?'), 'ok');
          runBtn.disabled = false;
          runBtn.textContent = '\u25B6 RUN BEATMATCH';
        }).catch(function (e) {
          _log('Failed: ' + e, 'err');
          runBtn.disabled = false;
          runBtn.textContent = '\u25B6 RUN BEATMATCH';
        });
    });
    btnRow.appendChild(runBtn);
    _musicWrap.appendChild(btnRow);

    // Log
    _logEl = document.createElement('div');
    _logEl.className = 'sc-log';
    _musicWrap.appendChild(_logEl);
  }

  // ── Part rows ─────────────────────────────────────────────────────────────
  function _renderPartRow(listEl, p) {
    var n = p.part;
    var wrap = document.createElement('div');
    wrap.className = 'sc-part-wrap';
    wrap.setAttribute('data-part', n);

    var hdr = document.createElement('div');
    hdr.className = 'sc-part-hdr' + (_selPart === n ? ' active' : '');
    hdr.setAttribute('role', 'button');
    hdr.setAttribute('tabindex', '0');

    var arrow = document.createElement('span');
    arrow.className = 'sc-part-arrow';
    arrow.textContent = _expanded[n] ? '\u25BC' : '\u25B6';
    hdr.appendChild(arrow);

    var label = document.createElement('span');
    label.className = 'sc-part-label';
    label.textContent = 'PART ' + (n < 10 ? '0' : '') + n;
    hdr.appendChild(label);

    // Tier count chips
    var chips = document.createElement('span');
    chips.className = 'sc-part-chips';
    if (p.t1_count > 0) {
      var c1 = document.createElement('span');
      c1.className = 'sc-chip sc-chip-t1';
      c1.textContent = p.t1_count + ' T1';
      chips.appendChild(c1);
    }
    if (p.t2_count > 0) {
      var c2 = document.createElement('span');
      c2.className = 'sc-chip sc-chip-t2';
      c2.textContent = p.t2_count + ' T2';
      chips.appendChild(c2);
    }
    if (p.t3_count > 0) {
      var c3 = document.createElement('span');
      c3.className = 'sc-chip sc-chip-t3';
      c3.textContent = p.t3_count + ' T3';
      chips.appendChild(c3);
    }
    if (p.has_music) {
      var cm = document.createElement('span');
      cm.className = 'sc-chip sc-chip-music';
      cm.textContent = 'MUSIC';
      chips.appendChild(cm);
    }
    if (p.has_flow_plan) {
      var cf = document.createElement('span');
      cf.className = 'sc-chip sc-chip-ok';
      cf.textContent = 'PLAN';
      chips.appendChild(cf);
    }
    hdr.appendChild(chips);
    wrap.appendChild(hdr);

    var clipsEl = document.createElement('div');
    clipsEl.className = 'sc-clips-list';
    if (!_expanded[n]) clipsEl.style.display = 'none';
    wrap.appendChild(clipsEl);

    function _toggle() {
      // Activate this part
      _selPart = n;
      _loadAssign(n);

      // Update header active state across all parts
      var allHdrs = listEl.querySelectorAll('.sc-part-hdr');
      for (var i = 0; i < allHdrs.length; i++) allHdrs[i].classList.remove('active');
      hdr.classList.add('active');

      _expanded[n] = !_expanded[n];
      arrow.textContent = _expanded[n] ? '\u25BC' : '\u25B6';
      clipsEl.style.display = _expanded[n] ? '' : 'none';

      // Show music panel for this part immediately
      if (_clipsCache[n]) {
        _renderMusicPanel(n);
      }

      if (_expanded[n] && !_clipsCache[n] && !_inflight[n]) {
        _inflight[n] = true;
        clipsEl.replaceChildren();
        var loading = document.createElement('div');
        loading.className = 'sc-clip-loading';
        loading.textContent = 'Loading clips\u2026';
        clipsEl.appendChild(loading);

        fetch('/api/studio/part/' + n + '/clips', { signal: AbortSignal.timeout(10000) })
          .then(function (r) { return r.ok ? r.json() : { clips: [] }; })
          .then(function (d) {
            _clipsCache[n] = d.clips || [];
            _inflight[n] = false;
            _renderClips(clipsEl, n);
            _renderMusicPanel(n);
          }).catch(function () {
            _inflight[n] = false;
            clipsEl.replaceChildren();
            var errEl = document.createElement('div');
            errEl.className = 'sc-clip-loading';
            errEl.textContent = 'Failed to load clips.';
            clipsEl.appendChild(errEl);
          });
      } else if (_expanded[n] && _clipsCache[n]) {
        _renderClips(clipsEl, n);
      }
    }

    hdr.addEventListener('click', _toggle);
    hdr.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); _toggle(); }
    });

    listEl.appendChild(wrap);
  }

  // ── Mount / Unmount ────────────────────────────────────────────────────────
  function mount(slot) {
    _slot       = slot;
    _logEl      = null;
    _musicWrap  = null;
    _listEl     = null;
    _partsData  = [];
    _tracksData = [];
    _clipsCache = {};
    _expanded   = {};
    _selPart    = null;
    _assign     = {};
    _inflight   = {};
    _saveTimer  = {};
    _dragIdx    = null;
    _dragPart   = null;

    var root = document.createElement('div');
    root.className = 'sc-root';

    // Left column
    var leftCol = document.createElement('div');
    leftCol.className = 'sc-left';
    var leftHdr = document.createElement('div');
    leftHdr.className = 'sc-col-hdr';
    leftHdr.textContent = 'PARTS & CLIPS';
    leftCol.appendChild(leftHdr);
    _listEl = document.createElement('div');
    _listEl.className = 'sc-parts-list';
    leftCol.appendChild(_listEl);

    // Right column
    var rightCol = document.createElement('div');
    rightCol.className = 'sc-right';
    _musicWrap = document.createElement('div');
    _musicWrap.className = 'sc-music-wrap';
    var placeholder = document.createElement('div');
    placeholder.className = 'sc-music-empty';
    placeholder.textContent = 'Select a part to assign music and run beatmatch.';
    _musicWrap.appendChild(placeholder);
    rightCol.appendChild(_musicWrap);

    root.appendChild(leftCol);
    root.appendChild(rightCol);
    slot.replaceChildren(root);

    // Load parts and tracks
    Promise.all([
      fetch('/api/studio/parts', { signal: AbortSignal.timeout(6000) }).then(function (r) { return r.ok ? r.json() : []; }),
      fetch('/api/phase1/music/tracks', { signal: AbortSignal.timeout(6000) }).then(function (r) { return r.ok ? r.json() : []; }),
    ]).then(function (res) {
      _partsData  = res[0];
      _tracksData = res[1];
      _listEl.replaceChildren();
      if (!_partsData.length) {
        var e = document.createElement('div');
        e.className = 'sc-music-empty';
        e.textContent = 'No parts found.';
        _listEl.appendChild(e);
        return;
      }
      _partsData.forEach(function (p) { _renderPartRow(_listEl, p); });

      // Auto-select first part with clips
      var first = _partsData.find(function (p) { return (p.clip_count || 0) > 0; }) || _partsData[0];
      if (first) {
        var hdrEl = _listEl.querySelector('[data-part="' + first.part + '"] .sc-part-hdr');
        if (hdrEl) hdrEl.click();
      }
    }).catch(function (e) {
      _listEl.replaceChildren();
      var errEl = document.createElement('div');
      errEl.className = 'sc-music-empty';
      errEl.textContent = 'Error: ' + e.message;
      _listEl.appendChild(errEl);
    });

    // Store subscription: sync when another panel changes activePart
    if (global.StudioStore) {
      _unsub = global.StudioStore.subscribe(function (s, p) {
        if (s.activePart !== p.activePart && s.activePart) {
          var n = s.activePart;
          if (!_expanded[n]) {
            var hdrEl = _listEl && _listEl.querySelector('[data-part="' + n + '"] .sc-part-hdr');
            if (hdrEl) hdrEl.click();
          } else {
            _selPart = n;
            _loadAssign(n);
            _renderMusicPanel(n);
          }
        }
      });
    }
  }

  function unmount() {
    if (_unsub) { _unsub(); _unsub = null; }
    // Clear any pending save timers
    Object.keys(_saveTimer).forEach(function (k) {
      if (_saveTimer[k]) clearTimeout(_saveTimer[k]);
    });
    _slot      = null;
    _logEl     = null;
    _musicWrap = null;
    _listEl    = null;
  }

  global.StudioClips = { mount: mount, unmount: unmount };
}(window));
