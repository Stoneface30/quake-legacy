/**
 * PANTHEON STUDIO — Beat Markers Overlay
 * studio-beatmarkers.js
 *
 * Renders a horizontal canvas strip above the clip timeline showing beat
 * positions and music section boundaries for the active part.
 *
 * Beat data comes from GET /api/studio/part/{n}/beats (P1-Z rule).
 *
 * Exposed on: window.StudioBeatMarkers
 *
 * Rules enforced:
 *   UI-1: DOM built with createElement/textContent only — no unsafe string injection
 *   UI-2: shared store is single source of truth — subscribes to StudioStore
 *   UI-3: no unbounded memory — canvas redrawn on each update, no frame cache
 */
(function (global) {
  'use strict';

  // ── Section colour palette (muted, dark-theme friendly) ───────────────────

  var SECTION_COLORS = {
    intro:  '#1a2a3a',
    build:  '#1a3a1a',
    drop:   '#3a1a1a',
    break:  '#2a2a1a',
    outro:  '#1a1a2a',
  };

  var SECTION_COLOR_DEFAULT = '#1e1e2a';

  // ── Module state ───────────────────────────────────────────────────────────

  var _container   = null;   // host element passed to mount()
  var _panel       = null;   // .beatmarkers-panel root
  var _canvas      = null;   // <canvas>
  var _ctx         = null;   // CanvasRenderingContext2D
  var _countLabel  = null;   // .bm-count span
  var _unsubscribe = null;   // StudioStore unsubscribe fn

  var _beats       = [];
  var _sections    = [];
  var _totalDur    = 0;
  var _playheadT   = 0;
  var _canvasW     = 0;
  var _canvasH     = 0;

  // ── DOM helpers ────────────────────────────────────────────────────────────

  function _buildPanel() {
    var panel = document.createElement('div');
    panel.className = 'beatmarkers-panel';

    // Header row
    var header = document.createElement('div');
    header.className = 'bm-header';

    var label = document.createElement('span');
    label.className = 'bm-label';
    label.textContent = 'BEAT MARKERS';

    var count = document.createElement('span');
    count.className = 'bm-count';
    count.textContent = '0 beats';

    header.appendChild(label);
    header.appendChild(count);

    // Canvas wrapper
    var wrap = document.createElement('div');
    wrap.className = 'bm-canvas-wrap';

    var canvas = document.createElement('canvas');
    canvas.className = 'bm-canvas';

    wrap.appendChild(canvas);
    panel.appendChild(header);
    panel.appendChild(wrap);

    return { panel: panel, canvas: canvas, countLabel: count };
  }

  // ── Canvas rendering ───────────────────────────────────────────────────────

  function _syncCanvasSize() {
    if (!_canvas) { return; }
    var rect = _canvas.parentElement.getBoundingClientRect();
    var w = Math.max(1, Math.round(rect.width  || _canvas.parentElement.offsetWidth  || 600));
    var h = Math.max(1, Math.round(rect.height || _canvas.parentElement.offsetHeight || 48));
    if (_canvas.width !== w || _canvas.height !== h) {
      _canvas.width  = w;
      _canvas.height = h;
    }
    _canvasW = _canvas.width;
    _canvasH = _canvas.height;
  }

  function _tToX(t) {
    if (_totalDur <= 0) { return 0; }
    return (t / _totalDur) * _canvasW;
  }

  function _draw() {
    if (!_ctx) { return; }
    _syncCanvasSize();

    var ctx = _ctx;
    var w   = _canvasW;
    var h   = _canvasH;

    // Background
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = '#0D0D0D';
    ctx.fillRect(0, 0, w, h);

    if (_totalDur <= 0) { return; }

    // ── Sections ──────────────────────────────────────────────────────────
    for (var s = 0; s < _sections.length; s++) {
      var sec  = _sections[s];
      var sx   = _tToX(sec.start || 0);
      var ex   = _tToX(sec.end   || _totalDur);
      var sw   = Math.max(1, ex - sx);

      var color = SECTION_COLORS[String(sec.label || '').toLowerCase()] || SECTION_COLOR_DEFAULT;
      ctx.fillStyle = color;
      ctx.fillRect(sx, 0, sw, h);

      // Section label (centered in band, clipped)
      if (sw > 28) {
        ctx.save();
        ctx.beginPath();
        ctx.rect(sx, 0, sw, h);
        ctx.clip();
        ctx.fillStyle = 'rgba(200, 200, 200, 0.35)';
        ctx.font = '9px "Segoe UI", system-ui, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(String(sec.label || ''), sx + sw / 2, h / 2);
        ctx.restore();
      }
    }

    // ── Beat lines ────────────────────────────────────────────────────────
    for (var b = 0; b < _beats.length; b++) {
      var beat = _beats[b];
      var bx   = _tToX(beat.t || 0);

      // Beat 1 of each bar = gold; others = subtle grey
      var isBarOne = (beat.beat === 1) || (beat.bar !== undefined && beat.beat === 1);
      ctx.strokeStyle = isBarOne ? '#C9A84C' : '#444444';
      ctx.lineWidth   = isBarOne ? 1.5 : 0.75;
      ctx.globalAlpha = isBarOne ? 0.9 : 0.55;

      ctx.beginPath();
      ctx.moveTo(bx, 0);
      ctx.lineTo(bx, h);
      ctx.stroke();
    }

    ctx.globalAlpha = 1;

    // ── Playhead ──────────────────────────────────────────────────────────
    if (_playheadT >= 0 && _totalDur > 0) {
      var px = _tToX(_playheadT);
      ctx.strokeStyle = '#C9A84C';
      ctx.lineWidth   = 1.5;
      ctx.globalAlpha = 1;
      ctx.beginPath();
      ctx.moveTo(px, 0);
      ctx.lineTo(px, h);
      ctx.stroke();
    }
  }

  // ── Data loading ───────────────────────────────────────────────────────────

  function _computeTotalDuration(beats, sections) {
    var maxT = 0;
    for (var i = 0; i < beats.length; i++) {
      if ((beats[i].t || 0) > maxT) { maxT = beats[i].t; }
    }
    for (var j = 0; j < sections.length; j++) {
      if ((sections[j].end || 0) > maxT) { maxT = sections[j].end; }
    }
    return maxT > 0 ? maxT + 2 : 0;
  }

  function loadBeats(beats, sections) {
    _beats    = Array.isArray(beats)    ? beats    : [];
    _sections = Array.isArray(sections) ? sections : [];
    _totalDur = _computeTotalDuration(_beats, _sections);

    if (_countLabel) {
      _countLabel.textContent = _beats.length + ' beat' + (_beats.length !== 1 ? 's' : '');
    }

    _draw();
  }

  function _fetchBeats(partNum) {
    if (!partNum && partNum !== 0) { return; }
    fetch('/api/studio/part/' + partNum + '/beats')
      .then(function (res) {
        if (!res.ok) { throw new Error('HTTP ' + res.status); }
        return res.json();
      })
      .then(function (data) {
        loadBeats(data.beats || [], data.sections || []);
      })
      .catch(function (err) {
        console.warn('[StudioBeatMarkers] fetchBeats failed', err);
        loadBeats([], []);
      });
  }

  // ── Store subscription ─────────────────────────────────────────────────────

  function _onStoreChange(state, prev) {
    if (state.activePart !== prev.activePart) {
      _beats    = [];
      _sections = [];
      _totalDur = 0;
      _playheadT = 0;
      if (_countLabel) { _countLabel.textContent = '0 beats'; }
      if (state.activePart !== null && state.activePart !== undefined) {
        _fetchBeats(state.activePart);
      } else {
        _draw();
      }
    }

    if (state.currentTime !== prev.currentTime) {
      _playheadT = state.currentTime || 0;
      _draw();
    }
  }

  // ── Public API ─────────────────────────────────────────────────────────────

  function mount(containerEl) {
    if (_panel) { return; }   // already mounted

    var built = _buildPanel();
    _panel      = built.panel;
    _canvas     = built.canvas;
    _countLabel = built.countLabel;
    _ctx        = _canvas.getContext('2d');
    _container  = containerEl;

    containerEl.appendChild(_panel);

    // Subscribe to store changes (UI-2)
    if (global.StudioStore) {
      _unsubscribe = global.StudioStore.subscribe(_onStoreChange);

      // Prime from current state
      var state = global.StudioStore.getState();
      if (state.activePart !== null && state.activePart !== undefined) {
        _fetchBeats(state.activePart);
      }
      _playheadT = state.currentTime || 0;
    }

    _syncCanvasSize();
    _draw();
  }

  function unmount() {
    if (_unsubscribe) {
      _unsubscribe();
      _unsubscribe = null;
    }
    if (_panel && _panel.parentElement) {
      _panel.parentElement.removeChild(_panel);
    }
    _panel      = null;
    _canvas     = null;
    _ctx        = null;
    _countLabel = null;
    _container  = null;
    _beats      = [];
    _sections   = [];
    _totalDur   = 0;
    _playheadT  = 0;
  }

  function setPlayhead(seconds) {
    _playheadT = seconds || 0;
    _draw();
  }

  function syncWidth(widthPx) {
    if (_canvas && _canvas.parentElement) {
      _canvas.parentElement.style.width = widthPx + 'px';
    }
    _syncCanvasSize();
    _draw();
  }

  // ── Export ─────────────────────────────────────────────────────────────────

  global.StudioBeatMarkers = {
    mount:      mount,
    unmount:    unmount,
    loadBeats:  loadBeats,
    setPlayhead: setPlayhead,
    syncWidth:  syncWidth,
  };

}(typeof window !== 'undefined' ? window : this));
