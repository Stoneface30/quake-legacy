/**
 * PANTHEON STUDIO — NLE Timeline (Canvas)
 * studio-timeline-nle.js
 *
 * Custom <canvas> Non-Linear Editor timeline. No external dependencies.
 * Replaces animation-timeline-js.
 *
 * State sources:
 *   StudioStore: clips[], selectedClip, activePart, currentTime
 *
 * Public API (window.StudioTimelineNLE):
 *   mount(container)         — attach to a DOM element
 *   unmount()                — detach, clean up listeners
 *   setZoom(pixPerSec)       — change horizontal zoom (10–200)
 *   showGhostPreview(clips)  — show randomizer preview at 60% opacity
 *   clearGhostPreview()      — cancel ghost, restore real clips
 *   acceptGhostPreview()     — commit ghost clips as new arrangement
 *
 * Rules: UI-1 (no innerHTML with untrusted data), UI-2 (store is source of truth)
 */
(function (global) {
  'use strict';

  // ── Constants ──────────────────────────────────────────────────────────────

  var TIER_COLORS = { T1: '#e8b923', T2: '#4a9eff', T3: '#7a7a9a' };
  var RULER_H   = 24;
  var AUDIO_H   = 28;
  var MIN_CLIP_W = 8;

  // Dynamic clip row height — fills canvas minus ruler and audio row.
  function _clipH() {
    if (!_canvas) return 80;
    var h = (_canvas.clientHeight || (_canvas.height / (_dpr || 1))) - RULER_H - AUDIO_H;
    return Math.max(60, h);
  }
  var FONT_CLIP  = '11px "Bebas Neue", monospace';
  var FONT_RULER = '10px monospace';

  // ── Module state ───────────────────────────────────────────────────────────

  var _container   = null;
  var _canvas      = null;
  var _ctx         = null;
  var _dpr         = 1;
  var _clips       = [];
  var _ghostClips  = null;
  var _selected    = [];
  var _dragging    = null;
  var _playheadT   = 0;
  var _pixPerSec   = 60;
  var _scrollLeft  = 0;
  var _clipboard   = [];
  var _unsubscribe = null;
  var _resizeObserver = null;
  var _activePart  = null;
  var _raf         = null;
  var _dirty       = true;

  // ── Helpers ────────────────────────────────────────────────────────────────

  function _clipDur(clip) {
    return (clip.duration_s && clip.duration_s > 0) ? clip.duration_s : 5.0;
  }

  function _clipX(idx) {
    var x = 0;
    for (var i = 0; i < idx; i++) {
      x += _clipDur(_clips[i]) * _pixPerSec;
    }
    return x - _scrollLeft;
  }

  function _clipW(clip) {
    return Math.max(MIN_CLIP_W, _clipDur(clip) * _pixPerSec);
  }

  function _totalDur() {
    return _clips.reduce(function (s, c) { return s + _clipDur(c); }, 0);
  }

  function _hitTestClip(px, py) {
    if (py < RULER_H || py > RULER_H + _clipH()) return -1;
    var x = 0;
    var list = _ghostClips || _clips;
    for (var i = 0; i < list.length; i++) {
      var w  = _clipW(list[i]);
      var cx = x - _scrollLeft;
      if (px >= cx && px < cx + w) return i;
      x += w;
    }
    return -1;
  }

  // ── Render ─────────────────────────────────────────────────────────────────

  function _render() {
    if (!_canvas || !_ctx) return;
    var dpr = _dpr || 1;
    var W   = _canvas.width  / dpr;
    var H   = _canvas.height / dpr;
    var ctx = _ctx;

    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, W, H);

    // Background
    ctx.fillStyle = '#0a0a0a';
    ctx.fillRect(0, 0, W, H);

    // Ruler background
    ctx.fillStyle = '#111';
    ctx.fillRect(0, 0, W, RULER_H);
    ctx.fillStyle = '#222';
    ctx.fillRect(0, RULER_H - 1, W, 1);

    // Ruler ticks
    var visStart = Math.floor(_scrollLeft / _pixPerSec);
    var visEnd   = Math.ceil((_scrollLeft + W) / _pixPerSec) + 2;
    ctx.font = FONT_RULER;
    ctx.textAlign = 'left';
    for (var s = visStart; s <= visEnd; s++) {
      var tx = s * _pixPerSec - _scrollLeft;
      if (s % 5 === 0) {
        ctx.fillStyle = '#444';
        ctx.fillRect(tx, RULER_H - 14, 1, 14);
        ctx.fillStyle = '#777';
        ctx.fillText(s + 's', tx + 2, RULER_H - 4);
      } else {
        ctx.fillStyle = '#2a2a2a';
        ctx.fillRect(tx, RULER_H - 6, 1, 6);
      }
    }

    // Clip row background
    ctx.fillStyle = '#0e0e0e';
    ctx.fillRect(0, RULER_H, W, _clipH());

    // Draw clips
    var drawList = _ghostClips || _clips;
    var x = 0;
    for (var i = 0; i < drawList.length; i++) {
      var clip = drawList[i];
      var cx   = x - _scrollLeft;
      var cw   = _clipW(clip);
      var isSelected = !_ghostClips && _selected.indexOf(i) >= 0;
      var isPinned   = clip.role === 'intro' || clip.role === 'outro';

      ctx.globalAlpha = _ghostClips ? 0.55 : 1.0;

      var color = TIER_COLORS[clip.tier] || '#4a9eff';

      if (isPinned) {
        ctx.fillStyle = '#1a1a1a';
        ctx.fillRect(cx, RULER_H + 2, cw - 1, _clipH() - 4);
        ctx.strokeStyle = '#444';
        ctx.lineWidth = 1;
        ctx.strokeRect(cx + 0.5, RULER_H + 2.5, cw - 2, _clipH() - 5);
        ctx.fillStyle = color;
        ctx.fillRect(cx, RULER_H + 2, 3, _clipH() - 4);
      } else {
        ctx.fillStyle = color;
        ctx.fillRect(cx, RULER_H + 2, cw - 1, _clipH() - 4);
        // Dark inner background for readability
        if (cw > 8) {
          ctx.fillStyle = 'rgba(0,0,0,0.35)';
          ctx.fillRect(cx + 1, RULER_H + 3, cw - 3, _clipH() - 6);
          ctx.fillStyle = color;
          ctx.fillRect(cx, RULER_H + 2, 3, _clipH() - 4);
        }
      }

      // Selection ring
      if (isSelected) {
        ctx.globalAlpha = 1.0;
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2;
        ctx.strokeRect(cx + 1, RULER_H + 3, cw - 3, _clipH() - 6);
      }

      // Clip label
      ctx.globalAlpha = _ghostClips ? 0.55 : 1.0;
      if (cw > 24) {
        ctx.fillStyle = '#ffffff';
        ctx.font = FONT_CLIP;
        ctx.textAlign = 'left';
        var name = clip.name || (clip.clip_path ? clip.clip_path.split(/[/\\]/).pop() : '');
        var label = (clip.tier || 'T2');
        if (name) label += ' ' + name.replace(/\.avi$/i, '').slice(0, 18);
        ctx.fillText(label, cx + 5, RULER_H + _clipH() - 10);
      }

      x += cw;
    }

    ctx.globalAlpha = 1.0;

    // Playhead
    var phX = _playheadT * _pixPerSec - _scrollLeft;
    if (phX >= 0 && phX <= W) {
      ctx.fillStyle = '#ff3333';
      ctx.fillRect(phX, 0, 2, RULER_H + _clipH());
    }

    // Audio row
    var audioY = RULER_H + _clipH();
    ctx.fillStyle = '#0c0c0c';
    ctx.fillRect(0, audioY, W, AUDIO_H);
    ctx.fillStyle = '#1e1e1e';
    ctx.fillRect(0, audioY + 1, W, AUDIO_H - 2);
    ctx.font = '10px monospace';
    ctx.textAlign = 'left';
    ctx.fillStyle = '#2a5a2a';
    ctx.fillText('AUDIO — assign via GENERATE', 8, audioY + 18);

    _dirty = false;
  }

  function _scheduleRender() {
    _dirty = true;
    if (_raf) return;
    _raf = requestAnimationFrame(function () {
      _raf = null;
      if (_dirty) _render();
    });
  }

  // ── Canvas sizing ──────────────────────────────────────────────────────────

  function _resize() {
    if (!_canvas || !_container) return;
    _dpr = window.devicePixelRatio || 1;
    var rect = _container.getBoundingClientRect();
    var cssW = Math.max(rect.width  || 800, 400);
    var cssH = Math.max(rect.height || 120, RULER_H + 60 + AUDIO_H);
    _canvas.width        = Math.round(cssW * _dpr);
    _canvas.height       = Math.round(cssH * _dpr);
    _canvas.style.width  = cssW + 'px';
    _canvas.style.height = cssH + 'px';
    _scheduleRender();
  }

  // ── Interaction ────────────────────────────────────────────────────────────

  function _onMouseDown(e) {
    var rect = _canvas.getBoundingClientRect();
    var px   = e.clientX - rect.left;
    var py   = e.clientY - rect.top;
    var idx  = _hitTestClip(px, py);

    if (idx < 0) {
      _selected = [];
      _dispatchStore('SET_SELECTED_CLIP', null);
      _scheduleRender();
      return;
    }

    if (e.shiftKey) {
      var pos = _selected.indexOf(idx);
      if (pos >= 0) _selected.splice(pos, 1);
      else _selected.push(idx);
    } else if (_selected.indexOf(idx) < 0) {
      _selected = [idx];
    }

    _dispatchStore('SET_SELECTED_CLIP', _clips[_selected[0]] || null);
    _scheduleRender();

    _dragging = { clipIdx: idx, startX: px, origIdx: idx };
    window.addEventListener('mousemove', _onMouseMove);
    window.addEventListener('mouseup', _onMouseUp);
  }

  function _onMouseMove(e) {
    if (!_dragging || _ghostClips) return;
    var rect = _canvas.getBoundingClientRect();
    var px   = e.clientX - rect.left;
    var dx   = px - _dragging.startX;

    // Map pixel delta to approximate clip-slot delta
    var avgW = _clips.length > 0
      ? (_totalDur() * _pixPerSec) / _clips.length
      : _pixPerSec * 5;
    var slotDelta = Math.round(dx / avgW);
    var newIdx = Math.max(0, Math.min(_clips.length - 1,
                          _dragging.origIdx + slotDelta));

    if (newIdx !== _dragging.clipIdx) {
      _moveClip(_dragging.clipIdx, newIdx);
      _dragging.clipIdx = newIdx;
      _scheduleRender();
    }
  }

  function _onMouseUp() {
    window.removeEventListener('mousemove', _onMouseMove);
    window.removeEventListener('mouseup', _onMouseUp);
    if (_dragging) {
      _saveArrangement();
      _dragging = null;
    }
  }

  function _onContextMenu(e) {
    e.preventDefault();
    var rect = _canvas.getBoundingClientRect();
    var px   = e.clientX - rect.left;
    var py   = e.clientY - rect.top;
    var idx  = _hitTestClip(px, py);
    if (idx < 0) return;
    _showContextMenu(e.clientX, e.clientY, idx);
  }

  function _onWheel(e) {
    e.preventDefault();
    _scrollLeft = Math.max(0, _scrollLeft + e.deltaY * 2);
    _scheduleRender();
  }

  function _onKeyDown(e) {
    if (!_canvas) return;
    var active = document.activeElement;
    var inInput = active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA' || active.tagName === 'SELECT');
    if (inInput) return;
    var ctrl = e.ctrlKey || e.metaKey;
    if (ctrl && e.key === 'x')  { e.preventDefault(); _cutSelected(); }
    else if (ctrl && e.key === 'c')  { e.preventDefault(); _copySelected(); }
    else if (ctrl && e.key === 'v')  { e.preventDefault(); _pasteAtPlayhead(); }
    else if (ctrl && e.key === 'd')  { e.preventDefault(); _duplicateSelected(); }
    else if (e.key === 'Delete' || e.key === 'Backspace') {
      if (_selected.length > 0) { e.preventDefault(); _deleteSelected(); }
    }
  }

  // ── Clip operations ────────────────────────────────────────────────────────

  function _moveClip(fromIdx, toIdx) {
    if (fromIdx === toIdx) return;
    var clip = _clips.splice(fromIdx, 1)[0];
    _clips.splice(toIdx, 0, clip);
    _selected = _selected.map(function (i) {
      if (i === fromIdx) return toIdx;
      if (fromIdx < toIdx && i > fromIdx && i <= toIdx) return i - 1;
      if (fromIdx > toIdx && i >= toIdx && i < fromIdx) return i + 1;
      return i;
    });
  }

  function _deleteSelected() {
    if (_selected.length === 0) return;
    var sorted = _selected.slice().sort(function (a, b) { return b - a; });
    for (var i = 0; i < sorted.length; i++) {
      var clip = _clips[sorted[i]];
      if (clip && (clip.role === 'intro' || clip.role === 'outro')) continue;
      _clips.splice(sorted[i], 1);
    }
    _selected = [];
    _dispatchStore('SET_SELECTED_CLIP', null);
    _saveArrangement();
    _scheduleRender();
  }

  function _copySelected() {
    _clipboard = _selected.map(function (i) {
      return Object.assign({}, _clips[i]);
    });
  }

  function _cutSelected() {
    _copySelected();
    _deleteSelected();
  }

  function _pasteAtPlayhead() {
    if (_clipboard.length === 0) return;
    var t = 0;
    var insertAt = _clips.length;
    for (var i = 0; i < _clips.length; i++) {
      t += _clipDur(_clips[i]);
      if (t >= _playheadT) { insertAt = i + 1; break; }
    }
    var newClips = _clipboard.map(function (c) {
      return Object.assign({}, c, { role: 'body', id: undefined });
    });
    Array.prototype.splice.apply(_clips, [insertAt, 0].concat(newClips));
    _saveArrangement();
    _scheduleRender();
  }

  function _duplicateSelected() {
    _copySelected();
    _pasteAtPlayhead();
  }

  // ── Context menu ───────────────────────────────────────────────────────────

  function _showContextMenu(clientX, clientY, clipIdx) {
    var existing = document.getElementById('nle-ctx-menu');
    if (existing) existing.remove();

    var menu = document.createElement('div');
    menu.id = 'nle-ctx-menu';
    menu.className = 'nle-ctx-menu';
    menu.style.left = clientX + 'px';
    menu.style.top  = clientY + 'px';

    function _item(label, fn) {
      var li = document.createElement('div');
      li.className = 'nle-ctx-item';
      li.textContent = label;
      li.addEventListener('click', function () { menu.remove(); fn(); });
      menu.appendChild(li);
    }

    _item('Cut',       function () { _selected = [clipIdx]; _cutSelected(); });
    _item('Copy',      function () { _selected = [clipIdx]; _copySelected(); });
    _item('Duplicate', function () { _selected = [clipIdx]; _duplicateSelected(); });
    _item('Delete',    function () { _selected = [clipIdx]; _deleteSelected(); });
    _item('── Set Role ──', function () {});
    _item('Set as Intro', function () {
      if (_clips[clipIdx]) {
        _clips[clipIdx].role = 'intro';
        _saveArrangement(); _scheduleRender();
      }
    });
    _item('Set as Outro', function () {
      if (_clips[clipIdx]) {
        _clips[clipIdx].role = 'outro';
        _saveArrangement(); _scheduleRender();
      }
    });
    _item('Reset to Body', function () {
      if (_clips[clipIdx]) {
        _clips[clipIdx].role = 'body';
        _saveArrangement(); _scheduleRender();
      }
    });

    document.body.appendChild(menu);

    function _rmMenu(ev) {
      if (!menu.contains(ev.target)) {
        menu.remove();
        document.removeEventListener('mousedown', _rmMenu);
      }
    }
    document.addEventListener('mousedown', _rmMenu);
  }

  // ── Ghost preview (randomizer) ─────────────────────────────────────────────

  function showGhostPreview(clips) {
    _ghostClips = clips.slice();
    _scheduleRender();
  }

  function clearGhostPreview() {
    _ghostClips = null;
    _scheduleRender();
  }

  function acceptGhostPreview() {
    if (!_ghostClips) return;
    _clips = _ghostClips.slice();
    _ghostClips = null;
    _selected = [];
    _saveArrangement();
    _scheduleRender();
    // Update store so library panel etc. reflect new order
    _dispatchStore('SET_CLIPS', _clips.slice());
  }

  // ── API persistence ────────────────────────────────────────────────────────

  function _saveArrangement() {
    var part = _activePart;
    if (!part) return;
    fetch('/api/studio/part/' + part + '/arrangement', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        clips: _clips.map(function (c) {
          return {
            clip_path:  c.clip_path || c.path || '',
            role:       c.role      || 'body',
            tier:       c.tier      || 'T2',
            is_fl:      !!c.is_fl,
            pair_path:  c.pair_path  || null,
            duration_s: c.duration_s || null,
          };
        }),
      }),
    }).catch(function (err) {
      console.error('[NLETimeline] save failed', err);
    });
  }

  function _dispatchStore(type, payload) {
    if (global.StudioStore) {
      global.StudioStore.dispatch({ type: type, payload: payload });
    }
  }

  // ── Store subscription ─────────────────────────────────────────────────────

  function _subscribeStore() {
    if (!global.StudioStore) return;
    _unsubscribe = global.StudioStore.subscribe(function (state, prev) {
      if (state.activePart !== prev.activePart) {
        _activePart = state.activePart;
      }
      if (state.clips !== prev.clips) {
        _clips = (state.clips || []).map(function (c) {
          return Object.assign({ role: 'body', duration_s: null }, c, {
            clip_path: c.path || c.clip_path || '',
          });
        });
        _selected = [];
        _ghostClips = null;
        // Auto-fit zoom when a new clip list loads
        if (_clips.length > 0) {
          var dur = _totalDur();
          if (dur > 0 && _container) {
            var cssW = (_container.getBoundingClientRect().width || 800) - 20;
            _pixPerSec = Math.max(10, Math.min(200, cssW / dur));
            _scrollLeft = 0;
          }
        }
        _scheduleRender();
      }
      if (state.currentTime !== prev.currentTime) {
        _playheadT = state.currentTime || 0;
        _scheduleRender();
      }
    });
    // Seed from current state
    var s = global.StudioStore.getState();
    _activePart = s.activePart;
    _clips = (s.clips || []).map(function (c) {
      return Object.assign({ role: 'body', duration_s: null }, c, {
        clip_path: c.path || c.clip_path || '',
      });
    });
  }

  // ── Mount / unmount ────────────────────────────────────────────────────────

  function mount(container) {
    _container = container;

    _canvas = document.createElement('canvas');
    _canvas.tabIndex = 0;
    _canvas.className = 'nle-canvas';
    _canvas.style.width = '100%';
    _canvas.style.display = 'block';
    _canvas.style.cursor = 'pointer';
    _canvas.setAttribute('aria-label', 'NLE Timeline');

    container.replaceChildren(_canvas);
    _ctx = _canvas.getContext('2d');

    _canvas.addEventListener('mousedown', _onMouseDown);
    _canvas.addEventListener('contextmenu', _onContextMenu);
    _canvas.addEventListener('wheel', _onWheel, { passive: false });
    document.addEventListener('keydown', _onKeyDown);

    _subscribeStore();

    _resizeObserver = new ResizeObserver(_resize);
    _resizeObserver.observe(container);
    _resize();
    // Auto-fit if clips already loaded in store when mounting
    if (_clips.length > 0) {
      requestAnimationFrame(function () { fitZoom(); });
    }
  }

  function unmount() {
    if (_unsubscribe) { _unsubscribe(); _unsubscribe = null; }
    if (_resizeObserver) { _resizeObserver.disconnect(); _resizeObserver = null; }
    if (_canvas) {
      _canvas.removeEventListener('mousedown', _onMouseDown);
      _canvas.removeEventListener('contextmenu', _onContextMenu);
      _canvas.removeEventListener('wheel', _onWheel);
    }
    document.removeEventListener('keydown', _onKeyDown);
    if (_raf) { cancelAnimationFrame(_raf); _raf = null; }
    _container = null;
    _canvas    = null;
    _ctx       = null;
  }

  function setZoom(pixPerSec) {
    _pixPerSec = Math.max(10, Math.min(200, pixPerSec));
    _scheduleRender();
  }

  function fitZoom() {
    if (!_container) return _pixPerSec;
    var dur = _totalDur();
    if (dur <= 0) return _pixPerSec;
    var cssW = (_container.getBoundingClientRect().width || 800) - 20;
    var newZoom = Math.max(10, Math.min(200, cssW / dur));
    _pixPerSec  = newZoom;
    _scrollLeft = 0;
    _scheduleRender();
    return newZoom;
  }

  // ── Public API ─────────────────────────────────────────────────────────────

  global.StudioTimelineNLE = {
    mount:              mount,
    unmount:            unmount,
    setZoom:            setZoom,
    fitZoom:            fitZoom,
    showGhostPreview:   showGhostPreview,
    clearGhostPreview:  clearGhostPreview,
    acceptGhostPreview: acceptGhostPreview,
  };

}(typeof window !== 'undefined' ? window : this));
