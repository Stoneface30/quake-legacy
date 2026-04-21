/**
 * PANTHEON STUDIO — Clips Browser + Music Assignment Panel
 * studio-clips.js
 *
 * Two-column layout:
 *   Left  — expandable parts list (parts 4-12), each listing clips from the
 *            clip-list manifests via /api/studio/part/{n}/clips
 *   Right — music assignment panel for the selected part: 5 tracks per part,
 *            role selector (INTRO / MAIN / OUTRO), BPM badge, RUN BEATMATCH
 *
 * Exposed on: window.StudioClips
 * Depends on: window.StudioStore (studio-store.js loaded first)
 *
 * Rule UI-1: DOM via createElement/textContent only.
 * Rule UI-2: state mutations go through StudioStore.
 */
(function (global) {
  'use strict';

  // ── Module state ──────────────────────────────────────────────────────────
  var _slot       = null;
  var _unsub      = null;
  var _partsData  = [];   // [{part, clip_count, has_music, …}]
  var _tracksData = [];   // [{name, path, bpm?}]
  var _clipsCache = {};   // partN → [{name, tier, weapon, map, …}]
  var _expanded   = {};   // partN → bool
  var _selPart    = null; // currently selected part number
  var _selClip    = null; // currently selected clip name
  var _assign     = {};   // partN → {intro:str|null, main:[str], outro:str|null}
  var _logEl      = null;
  var _musicWrap  = null;
  var _inflight   = {};   // partN → bool (clip fetch in-flight guard)

  // ── Helpers ───────────────────────────────────────────────────────────────
  function _log(msg, kind) {
    if (!_logEl) return;
    var line = document.createElement('div');
    line.textContent = '[' + new Date().toLocaleTimeString() + '] ' + msg;
    line.style.color = kind === 'err' ? '#ff6666' : kind === 'ok' ? '#9beab1' : '#888';
    line.style.fontSize = '11px';
    _logEl.appendChild(line);
    while (_logEl.childNodes.length > 120) { _logEl.removeChild(_logEl.firstChild); }
    _logEl.scrollTop = _logEl.scrollHeight;
  }

  function _tracksForPart(n) {
    var prefix = 'part' + (n < 10 ? '0' + n : '' + n) + '_music_';
    return _tracksData.filter(function (t) { return t.name.indexOf(prefix) === 0; });
  }

  function _roleName(role) {
    if (role === 'intro') return 'INTRO';
    if (role === 'outro') return 'OUTRO';
    return 'MAIN';
  }

  function _tierColor(tier) {
    if (!tier) return '#555';
    var t = tier.toUpperCase();
    if (t === 'T1') return '#e8b923';
    if (t === 'T2') return '#4a9eff';
    if (t === 'T3') return '#7a7a9a';
    return '#555';
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
        if (_selPart === n) _renderMusic(n);
      })
      .catch(function () {});
  }

  function _saveAssign(n) {
    var body = _assign[n] || { intro: null, main: [], outro: null };
    fetch('/api/phase1/parts/' + n + '/music-override', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(5000)
    }).then(function (r) {
      _log(r.ok ? 'Saved music assignment for Part ' + n : 'Save failed: HTTP ' + r.status,
           r.ok ? 'ok' : 'err');
    }).catch(function (e) { _log('Save error: ' + e.message, 'err'); });
  }

  // ── Right panel: music assignment ─────────────────────────────────────────
  function _renderMusic(n) {
    if (!_musicWrap) return;
    _musicWrap.replaceChildren();

    var hdr = document.createElement('div');
    hdr.className = 'sc-music-hdr';
    var hdrTitle = document.createElement('span');
    hdrTitle.textContent = 'PART ' + (n < 10 ? '0' + n : n) + ' — MUSIC';
    hdr.appendChild(hdrTitle);
    _musicWrap.appendChild(hdr);

    var tracks = _tracksForPart(n);
    if (!tracks.length) {
      var empty = document.createElement('div');
      empty.className = 'sc-music-empty';
      empty.textContent = 'No music files found for Part ' + n + '.';
      _musicWrap.appendChild(empty);
      return;
    }

    var assign = _assign[n] || { intro: null, main: [], outro: null };

    tracks.forEach(function (track) {
      var row = document.createElement('div');
      row.className = 'sc-music-row';

      var nameEl = document.createElement('div');
      nameEl.className = 'sc-music-name';
      // Show short name: strip "partNN_music_" prefix
      var shortName = track.name.replace(/^part\d+_music_0?/, '').replace(/\.(mp3|ogg|wav|m4a)$/i, '');
      nameEl.textContent = shortName;
      row.appendChild(nameEl);

      if (track.bpm) {
        var bpmEl = document.createElement('span');
        bpmEl.className = 'sc-music-bpm';
        bpmEl.textContent = Math.round(track.bpm) + ' BPM';
        row.appendChild(bpmEl);
      }

      // Determine current assigned role
      var curRole = 'off';
      if (assign.intro === track.name) curRole = 'intro';
      else if (assign.outro === track.name) curRole = 'outro';
      else if (assign.main.indexOf(track.name) !== -1) curRole = 'main';

      var sel = document.createElement('select');
      sel.className = 'sc-music-sel';
      ['off', 'intro', 'main', 'outro'].forEach(function (r) {
        var opt = document.createElement('option');
        opt.value = r;
        opt.textContent = r === 'off' ? '—' : _roleName(r);
        if (r === curRole) opt.selected = true;
        sel.appendChild(opt);
      });

      sel.addEventListener('change', function () {
        var a = _assign[n];
        // Remove this track from all roles first
        if (a.intro === track.name) a.intro = null;
        if (a.outro === track.name) a.outro = null;
        a.main = a.main.filter(function (x) { return x !== track.name; });
        // Assign new role
        var newRole = sel.value;
        if (newRole === 'intro') a.intro = track.name;
        else if (newRole === 'outro') a.outro = track.name;
        else if (newRole === 'main') a.main.push(track.name);
        _saveAssign(n);
      });

      row.appendChild(sel);
      _musicWrap.appendChild(row);
    });

    // RUN BEATMATCH button
    var btnRow = document.createElement('div');
    btnRow.className = 'sc-beatmatch-row';
    var btn = document.createElement('button');
    btn.className = 'sc-beatmatch-btn';
    btn.textContent = '\u25B6 RUN BEATMATCH';
    btn.addEventListener('click', function () {
      btn.disabled = true;
      btn.textContent = 'QUEUING\u2026';
      _log('Queuing Part ' + n + ' rebuild\u2026', 'info');
      fetch('/api/phase1/parts/' + n + '/rebuild', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
        signal: AbortSignal.timeout(10000)
      })
        .then(function (r) { return r.ok ? r.json() : Promise.reject('HTTP ' + r.status); })
        .then(function (d) {
          _log('Part ' + n + ' queued — job_id=' + (d.job_id || '?'), 'ok');
          btn.disabled = false;
          btn.textContent = '\u25B6 RUN BEATMATCH';
        })
        .catch(function (e) {
          _log('Part ' + n + ' queue failed: ' + e, 'err');
          btn.disabled = false;
          btn.textContent = '\u25B6 RUN BEATMATCH';
        });
    });
    btnRow.appendChild(btn);
    _musicWrap.appendChild(btnRow);

    // Log area
    _logEl = document.createElement('div');
    _logEl.className = 'sc-log';
    _musicWrap.appendChild(_logEl);
  }

  // ── Left panel: parts list ─────────────────────────────────────────────────
  function _renderPartRow(listEl, p) {
    var n = p.part;
    var rowWrap = document.createElement('div');
    rowWrap.className = 'sc-part-wrap';
    rowWrap.setAttribute('data-part', n);

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
    label.textContent = 'PART ' + (n < 10 ? '0' + n : n);
    hdr.appendChild(label);

    var chips = document.createElement('span');
    chips.className = 'sc-part-chips';

    var countChip = document.createElement('span');
    countChip.className = 'sc-chip';
    countChip.textContent = p.clip_count + ' clips';
    chips.appendChild(countChip);

    if (p.has_music) {
      var musicChip = document.createElement('span');
      musicChip.className = 'sc-chip sc-chip-music';
      musicChip.textContent = 'MUSIC';
      chips.appendChild(musicChip);
    }
    if (p.has_flow_plan) {
      var fpChip = document.createElement('span');
      fpChip.className = 'sc-chip sc-chip-ok';
      fpChip.textContent = 'PLAN';
      chips.appendChild(fpChip);
    }
    hdr.appendChild(chips);
    rowWrap.appendChild(hdr);

    // Clips container (collapsed by default)
    var clipsEl = document.createElement('div');
    clipsEl.className = 'sc-clips-list';
    if (!_expanded[n]) clipsEl.style.display = 'none';
    rowWrap.appendChild(clipsEl);

    function _toggle() {
      _selPart = n;
      _loadAssign(n);
      _renderMusic(n);

      // Update active state on all part headers
      var allHdrs = listEl.querySelectorAll('.sc-part-hdr');
      for (var i = 0; i < allHdrs.length; i++) {
        allHdrs[i].classList.remove('active');
      }
      hdr.classList.add('active');

      _expanded[n] = !_expanded[n];
      arrow.textContent = _expanded[n] ? '\u25BC' : '\u25B6';
      clipsEl.style.display = _expanded[n] ? '' : 'none';

      if (_expanded[n] && !_clipsCache[n] && !_inflight[n]) {
        _inflight[n] = true;
        clipsEl.replaceChildren();
        var loading = document.createElement('div');
        loading.className = 'sc-clip-loading';
        loading.textContent = 'Loading clips\u2026';
        clipsEl.appendChild(loading);

        fetch('/api/studio/part/' + n + '/clips', { signal: AbortSignal.timeout(8000) })
          .then(function (r) { return r.ok ? r.json() : { clips: [] }; })
          .then(function (d) {
            _clipsCache[n] = d.clips || [];
            _inflight[n] = false;
            _renderClips(clipsEl, n);
          })
          .catch(function () {
            _inflight[n] = false;
            clipsEl.replaceChildren();
            var err = document.createElement('div');
            err.className = 'sc-clip-loading';
            err.textContent = 'Failed to load clips.';
            clipsEl.appendChild(err);
          });
      } else if (_expanded[n] && _clipsCache[n]) {
        _renderClips(clipsEl, n);
      }
    }

    hdr.addEventListener('click', _toggle);
    hdr.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); _toggle(); }
    });

    listEl.appendChild(rowWrap);
  }

  function _renderClips(container, n) {
    container.replaceChildren();
    var clips = _clipsCache[n] || [];
    if (!clips.length) {
      var empty = document.createElement('div');
      empty.className = 'sc-clip-loading';
      empty.textContent = 'No clips in manifest.';
      container.appendChild(empty);
      return;
    }
    clips.forEach(function (clip) {
      var row = document.createElement('div');
      row.className = 'sc-clip-row' + (_selClip === clip.name ? ' active' : '');
      row.setAttribute('data-clip', clip.name || '');

      var tierDot = document.createElement('span');
      tierDot.className = 'sc-tier-dot';
      tierDot.style.background = _tierColor(clip.tier);
      row.appendChild(tierDot);

      var nameEl = document.createElement('span');
      nameEl.className = 'sc-clip-name';
      nameEl.textContent = clip.name || '(unnamed)';
      row.appendChild(nameEl);

      if (clip.weapon) {
        var wep = document.createElement('span');
        wep.className = 'sc-tag';
        wep.textContent = clip.weapon;
        row.appendChild(wep);
      }
      if (clip.map) {
        var map = document.createElement('span');
        map.className = 'sc-tag sc-tag-map';
        map.textContent = clip.map;
        row.appendChild(map);
      }
      if (clip.duration_s) {
        var dur = document.createElement('span');
        dur.className = 'sc-clip-dur';
        dur.textContent = clip.duration_s.toFixed(1) + 's';
        row.appendChild(dur);
      }

      row.addEventListener('click', function () {
        _selClip = clip.name;
        // Update active state
        var allRows = container.querySelectorAll('.sc-clip-row');
        for (var i = 0; i < allRows.length; i++) allRows[i].classList.remove('active');
        row.classList.add('active');
        // Dispatch part change if needed
        if (global.StudioStore) {
          var st = global.StudioStore.getState();
          if (st.activePart !== n) {
            global.StudioStore.dispatch({ type: 'SET_ACTIVE_PART', payload: n });
          }
        }
      });

      container.appendChild(row);
    });
  }

  // ── Mount / Unmount ────────────────────────────────────────────────────────
  function mount(slot) {
    _slot = slot;
    _logEl = null;
    _musicWrap = null;
    _partsData = [];
    _tracksData = [];
    _clipsCache = {};
    _expanded = {};
    _selPart = null;
    _selClip = null;
    _assign = {};
    _inflight = {};

    // Root layout
    var root = document.createElement('div');
    root.className = 'sc-root';

    // Left column: parts list
    var leftCol = document.createElement('div');
    leftCol.className = 'sc-left';
    var listHdr = document.createElement('div');
    listHdr.className = 'sc-col-hdr';
    listHdr.textContent = 'PARTS & CLIPS';
    leftCol.appendChild(listHdr);
    var listEl = document.createElement('div');
    listEl.className = 'sc-parts-list';
    leftCol.appendChild(listEl);

    // Right column: music + log
    var rightCol = document.createElement('div');
    rightCol.className = 'sc-right';
    _musicWrap = document.createElement('div');
    _musicWrap.className = 'sc-music-wrap';
    var placeholder = document.createElement('div');
    placeholder.className = 'sc-music-empty';
    placeholder.textContent = 'Select a part to assign music.';
    _musicWrap.appendChild(placeholder);
    rightCol.appendChild(_musicWrap);

    root.appendChild(leftCol);
    root.appendChild(rightCol);
    slot.replaceChildren(root);

    // Fetch parts and tracks in parallel
    Promise.all([
      fetch('/api/studio/parts', { signal: AbortSignal.timeout(6000) }).then(function (r) { return r.ok ? r.json() : []; }),
      fetch('/api/phase1/music/tracks', { signal: AbortSignal.timeout(6000) }).then(function (r) { return r.ok ? r.json() : []; }),
    ]).then(function (results) {
      _partsData = results[0];
      _tracksData = results[1];
      listEl.replaceChildren();
      if (!_partsData.length) {
        var empty = document.createElement('div');
        empty.className = 'sc-music-empty';
        empty.textContent = 'No parts found. Add clip lists to creative_suite/engine/clip_lists/.';
        listEl.appendChild(empty);
        return;
      }
      _partsData.forEach(function (p) { _renderPartRow(listEl, p); });

      // Auto-select first part that has clips
      var firstWithClips = _partsData.find(function (p) { return p.clip_count > 0; }) || _partsData[0];
      if (firstWithClips) {
        var firstWrap = listEl.querySelector('[data-part="' + firstWithClips.part + '"] .sc-part-hdr');
        if (firstWrap) firstWrap.click();
      }
    }).catch(function (e) {
      listEl.replaceChildren();
      var err = document.createElement('div');
      err.className = 'sc-music-empty';
      err.textContent = 'Error loading data: ' + e.message;
      listEl.appendChild(err);
    });

    // Subscribe to store for part changes from other panels
    if (global.StudioStore) {
      _unsub = global.StudioStore.subscribe(function (s, p) {
        if (s.activePart !== p.activePart) {
          var n = s.activePart;
          // Expand that part if not already
          if (!_expanded[n]) {
            var wrap = listEl && listEl.querySelector('[data-part="' + n + '"] .sc-part-hdr');
            if (wrap) wrap.click();
          } else {
            _selPart = n;
            _loadAssign(n);
            _renderMusic(n);
          }
        }
      });
    }
  }

  function unmount() {
    if (_unsub) { _unsub(); _unsub = null; }
    _slot = null;
    _logEl = null;
    _musicWrap = null;
  }

  global.StudioClips = { mount: mount, unmount: unmount };
}(window));
