/**
 * PANTHEON STUDIO — Clip Timeline Panel
 * studio-timeline.js
 *
 * Canvas-based clip timeline built on animation-timeline-js (timelineModule global).
 * Falls back to a simple Canvas 2D renderer when the library is unavailable.
 *
 * Exposed on: window.StudioTimeline
 *
 * Depends on: window.StudioStore (studio-store.js loaded first)
 *             window.timelineModule (vendor/animation-timeline.js loaded first)
 *
 * Rule UI-1: DOM built with createElement/textContent only (no raw injection).
 * Rule UI-2: all state from StudioStore — no local drift.
 */
(function (global) {
  'use strict';

  // ── Constants ──────────────────────────────────────────────────────────────

  /** Seconds between adjacent clip keyframes on the default view. */
  var DEFAULT_CLIP_SPACING_S = 2;

  /** Default clip duration when metadata is absent (seconds). */
  var DEFAULT_CLIP_DURATION_S = 3;

  /** Timeline time-unit: milliseconds (library uses val in ms). */
  var MS_PER_S = 1000;

  /**
   * One row label per tier.  Keyframes are placed on the row that matches the
   * clip's tier field (T1/T2/T3).  Unknown tier goes to the "OTHER" row.
   */
  var TIER_ROWS = ['T1', 'T2', 'T3', 'OTHER'];

  /** Unique DOM id prefix (avoids collisions when multiple instances exist). */
  var CANVAS_WRAP_ID = 'tl-canvas-wrap-inner';

  // ── Module-private state ───────────────────────────────────────────────────

  /** @type {Element|null} */
  var _container = null;

  /** @type {Element|null} */
  var _panelEl = null;

  /** @type {Element|null} */
  var _canvasWrap = null;

  /** @type {Element|null} */
  var _selectedLabel = null;

  /** @type {object|null} Currently selected clip object. */
  var _selectedClip = null;

  /** @type {function|null} StudioStore unsubscribe handle. */
  var _unsubscribe = null;

  /** @type {object|null} animation-timeline-js Timeline instance. */
  var _tl = null;

  /** @type {Array} Last loaded clips array. */
  var _clips = [];

  /** @type {number|null} Last loaded part number. */
  var _part = null;

  // ── Fallback Canvas renderer ───────────────────────────────────────────────
  // Used when timelineModule is unavailable at runtime.

  var _fbCanvas = null;
  var _fbCtx = null;
  var _fbPlayheadMs = 0;
  var _fbRows = [];   // [{label, clips:[{startMs, durationMs, clipObj}]}]
  var _fbTotalMs = 0;

  function _fbEnsureCanvas() {
    if (_fbCanvas) { return; }
    _fbCanvas = document.createElement('canvas');
    _fbCanvas.style.cssText = 'width:100%;height:100%;display:block;';
    _canvasWrap.appendChild(_fbCanvas);
    _fbCtx = _fbCanvas.getContext('2d');
    _fbCanvas.addEventListener('click', _fbOnClick);
    window.addEventListener('resize', _fbDraw);
  }

  function _fbOnClick(evt) {
    if (!_fbCtx || !_fbRows.length) { return; }
    var rect = _fbCanvas.getBoundingClientRect();
    var x = evt.clientX - rect.left;
    var y = evt.clientY - rect.top;
    var ROW_H = 28;
    var HEADER_H = 24;
    var LABEL_W = 40;
    var w = _fbCanvas.width - LABEL_W;
    var rowIdx = Math.floor((y - HEADER_H) / ROW_H);
    if (rowIdx < 0 || rowIdx >= _fbRows.length) { return; }
    var row = _fbRows[rowIdx];
    var msPerPx = _fbTotalMs / Math.max(1, w);
    var clickMs = (x - LABEL_W) * msPerPx;
    for (var i = 0; i < row.clips.length; i++) {
      var c = row.clips[i];
      if (clickMs >= c.startMs && clickMs <= c.startMs + c.durationMs) {
        _selectedClip = c.clipObj;
        _updateSelectedLabel();
        _fbDraw();
        return;
      }
    }
  }

  function _fbDraw() {
    if (!_fbCanvas || !_fbCtx) { return; }
    var rect = _canvasWrap.getBoundingClientRect();
    var W = Math.max(1, rect.width);
    var H = Math.max(1, rect.height);
    _fbCanvas.width = W;
    _fbCanvas.height = H;
    var ctx = _fbCtx;

    var HEADER_H = 24;
    var ROW_H = 28;
    var LABEL_W = 40;
    var totalMs = _fbTotalMs || 1;
    var timelineW = W - LABEL_W;

    // Background
    ctx.fillStyle = '#0D0D0D';
    ctx.fillRect(0, 0, W, H);

    // Header
    ctx.fillStyle = '#101011';
    ctx.fillRect(0, 0, W, HEADER_H);
    ctx.fillStyle = '#888';
    ctx.font = '10px monospace';
    var steps = 8;
    for (var s = 0; s <= steps; s++) {
      var tMs = Math.round((totalMs / steps) * s);
      var tX = LABEL_W + (tMs / totalMs) * timelineW;
      ctx.fillText((tMs / 1000).toFixed(1) + 's', tX + 2, 14);
      ctx.fillStyle = '#2A2A2A';
      ctx.fillRect(tX, 0, 1, H);
      ctx.fillStyle = '#888';
    }

    // Tier rows
    var TIER_COLORS = { T1: '#C9A84C', T2: '#4C8EC9', T3: '#4CC97A', OTHER: '#888' };
    for (var ri = 0; ri < _fbRows.length; ri++) {
      var row = _fbRows[ri];
      var ry = HEADER_H + ri * ROW_H;
      ctx.fillStyle = '#141414';
      ctx.fillRect(0, ry, W, ROW_H - 1);
      // Row label
      ctx.fillStyle = TIER_COLORS[row.label] || '#888';
      ctx.font = 'bold 10px monospace';
      ctx.fillText(row.label, 4, ry + ROW_H / 2 + 4);
      // Clips
      for (var ci = 0; ci < row.clips.length; ci++) {
        var clip = row.clips[ci];
        var cx = LABEL_W + (clip.startMs / totalMs) * timelineW;
        var cw = Math.max(4, (clip.durationMs / totalMs) * timelineW);
        var isSelected = _selectedClip && _selectedClip === clip.clipObj;
        ctx.fillStyle = isSelected ? '#fff' : (TIER_COLORS[row.label] || '#888');
        ctx.globalAlpha = isSelected ? 0.9 : 0.65;
        ctx.fillRect(cx, ry + 4, cw, ROW_H - 9);
        ctx.globalAlpha = 1;
        // Clip label
        ctx.fillStyle = '#000';
        ctx.font = '9px monospace';
        var lbl = clip.clipObj && clip.clipObj.name ? clip.clipObj.name.slice(-12) : '';
        if (cw > 20 && lbl) {
          ctx.fillText(lbl, cx + 2, ry + ROW_H / 2 + 3);
        }
      }
    }

    // Playhead
    if (_fbPlayheadMs >= 0 && totalMs > 0) {
      var px = LABEL_W + (_fbPlayheadMs / totalMs) * timelineW;
      ctx.fillStyle = '#FF4500';
      ctx.fillRect(px, 0, 2, H);
    }
  }

  // ── animation-timeline-js helpers ─────────────────────────────────────────

  /**
   * Build a timelineModule model from the flat clips array.
   * Rows = one per tier. Each clip becomes a keyframe at its start offset.
   * @param {Array} clips
   * @returns {{ rows: Array }}
   */
  function _buildModel(clips) {
    var rowMap = {};
    TIER_ROWS.forEach(function (label) {
      rowMap[label] = { name: label, keyframes: [] };
    });

    clips.forEach(function (clip, idx) {
      var tier = (clip.tier || '').toUpperCase();
      if (!rowMap[tier]) { tier = 'OTHER'; }
      var startMs = idx * DEFAULT_CLIP_SPACING_S * MS_PER_S;
      var durationMs = (clip.duration || DEFAULT_CLIP_DURATION_S) * MS_PER_S;
      rowMap[tier].keyframes.push({
        val:      startMs,
        _endVal:  startMs + durationMs,
        _clip:    clip,
      });
    });

    return {
      rows: TIER_ROWS.map(function (label) { return rowMap[label]; }),
    };
  }

  /**
   * Build the fallback renderer row data from clips.
   * @param {Array} clips
   */
  function _buildFbRows(clips) {
    var rowMap = {};
    TIER_ROWS.forEach(function (label) { rowMap[label] = { label: label, clips: [] }; });
    var totalMs = 0;
    clips.forEach(function (clip, idx) {
      var tier = (clip.tier || '').toUpperCase();
      if (!rowMap[tier]) { tier = 'OTHER'; }
      var startMs = idx * DEFAULT_CLIP_SPACING_S * MS_PER_S;
      var durationMs = (clip.duration || DEFAULT_CLIP_DURATION_S) * MS_PER_S;
      rowMap[tier].clips.push({ startMs: startMs, durationMs: durationMs, clipObj: clip });
      totalMs = Math.max(totalMs, startMs + durationMs);
    });
    _fbRows = TIER_ROWS.map(function (label) { return rowMap[label]; });
    _fbTotalMs = totalMs + DEFAULT_CLIP_SPACING_S * MS_PER_S;
  }

  // ── DOM helpers ────────────────────────────────────────────────────────────

  /**
   * Update the footer label after selection changes.
   */
  function _updateSelectedLabel() {
    if (!_selectedLabel) { return; }
    if (_selectedClip) {
      _selectedLabel.textContent = 'Selected: ' + (_selectedClip.name || _selectedClip.path || 'clip');
    } else {
      _selectedLabel.textContent = 'No clip selected';
    }
  }

  /**
   * Build a toolbar button element safely (no raw injection).
   * @param {string} id
   * @param {string} text
   * @returns {HTMLButtonElement}
   */
  function _makeBtn(id, text) {
    var btn = document.createElement('button');
    btn.className = 'tl-btn';
    btn.id = id;
    btn.textContent = text;
    return btn;
  }

  // ── StudioStore subscription ───────────────────────────────────────────────

  function _onStoreChange(state, prev) {
    if (state.clips !== prev.clips) {
      _StudioTimeline.loadClips(state.clips, state.activePart);
    }
    if (state.currentTime !== prev.currentTime) {
      _StudioTimeline.setPlayhead(state.currentTime);
    }
  }

  // ── Public API ─────────────────────────────────────────────────────────────

  var _StudioTimeline = {

    /**
     * Create the timeline panel DOM and mount it inside containerEl.
     * Initialises animation-timeline-js (or fallback renderer).
     * @param {Element} containerEl
     */
    mount: function (containerEl) {
      if (_panelEl) {
        console.warn('[StudioTimeline] already mounted — call unmount() first');
        return;
      }

      _container = containerEl;

      // ── Panel root ──────────────────────────────────────────────────────
      _panelEl = document.createElement('div');
      _panelEl.className = 'timeline-panel';

      // ── Toolbar ─────────────────────────────────────────────────────────
      var toolbar = document.createElement('div');
      toolbar.className = 'timeline-toolbar';

      var label = document.createElement('span');
      label.className = 'timeline-label';
      label.textContent = 'CLIP TIMELINE';

      var btnFit    = _makeBtn('tl-btn-fit',     'FIT');
      var btnZoomIn = _makeBtn('tl-btn-zoom-in',  '+');
      var btnZoomOut= _makeBtn('tl-btn-zoom-out', '-');

      toolbar.appendChild(label);
      toolbar.appendChild(btnFit);
      toolbar.appendChild(btnZoomIn);
      toolbar.appendChild(btnZoomOut);

      // ── Canvas wrap ──────────────────────────────────────────────────────
      _canvasWrap = document.createElement('div');
      _canvasWrap.className = 'timeline-canvas-wrap';
      // The animation-timeline lib requires a child element with a DOM id.
      var innerWrap = document.createElement('div');
      innerWrap.id = CANVAS_WRAP_ID;
      innerWrap.style.cssText = 'width:100%;height:100%;';
      _canvasWrap.appendChild(innerWrap);

      // ── Footer ───────────────────────────────────────────────────────────
      var footer = document.createElement('div');
      footer.className = 'timeline-footer';
      _selectedLabel = document.createElement('span');
      _selectedLabel.className = 'tl-selected-label';
      _selectedLabel.textContent = 'No clip selected';
      footer.appendChild(_selectedLabel);

      // ── Assemble ─────────────────────────────────────────────────────────
      _panelEl.appendChild(toolbar);
      _panelEl.appendChild(_canvasWrap);
      _panelEl.appendChild(footer);
      _container.appendChild(_panelEl);

      // ── Init library (or fallback) ───────────────────────────────────────
      var tm = global.timelineModule;
      if (tm && tm.Timeline) {
        try {
          _tl = new tm.Timeline(
            {
              id: CANVAS_WRAP_ID,
              headerFillColor: '#101011',
              fillColor:       '#101011',
              labelsColor:     '#D5D5D5',
              tickColor:       '#2A2A2A',
              zoom:            1,
              zoomSpeed:       0.1,
              zoomMin:         0.1,
              zoomMax:         8,
              stepPx:          120,
              stepVal:         1000,
            },
            { rows: [] }
          );

          // Wire selection event
          _tl.on(tm.TimelineEvents ? tm.TimelineEvents.Selected : 'selected', function (evt) {
            if (evt && evt.selected && evt.selected.length > 0) {
              var kf = evt.selected[0];
              _selectedClip = (kf && kf._clip) ? kf._clip : null;
            } else {
              _selectedClip = null;
            }
            _updateSelectedLabel();
          });

          // Wire time-changed event (scrubbing in library)
          _tl.on(tm.TimelineEvents ? tm.TimelineEvents.TimeChanged : 'timechanged', function (evt) {
            if (evt && typeof evt.val === 'number') {
              if (global.StudioStore) {
                global.StudioStore.dispatch({
                  type:    'SET_CURRENT_TIME',
                  payload: evt.val / MS_PER_S,
                });
              }
            }
          });
        } catch (e) {
          console.error('[StudioTimeline] animation-timeline init failed, using fallback:', e);
          _tl = null;
        }
      }

      // Fallback: simple canvas 2D renderer
      if (!_tl) {
        _fbEnsureCanvas();
      }

      // ── Toolbar button handlers ──────────────────────────────────────────
      btnFit.addEventListener('click', function () {
        if (_tl && typeof _tl.rescale === 'function') {
          _tl.rescale();
          _tl.redraw();
        } else {
          _fbDraw();
        }
      });

      btnZoomIn.addEventListener('click', function () {
        if (_tl && typeof _tl.zoomIn === 'function') {
          _tl.zoomIn();
        } else {
          _fbDraw();
        }
      });

      btnZoomOut.addEventListener('click', function () {
        if (_tl && typeof _tl.zoomOut === 'function') {
          _tl.zoomOut();
        } else {
          _fbDraw();
        }
      });

      // ── Subscribe to store ───────────────────────────────────────────────
      if (global.StudioStore) {
        _unsubscribe = global.StudioStore.subscribe(_onStoreChange);
        // Seed with current state
        var st = global.StudioStore.getState();
        if (st.clips && st.clips.length > 0) {
          _StudioTimeline.loadClips(st.clips, st.activePart);
        }
        if (typeof st.currentTime === 'number') {
          _StudioTimeline.setPlayhead(st.currentTime);
        }
      }
    },

    /**
     * Tear down the panel, destroy the timeline, unsubscribe from the store.
     */
    unmount: function () {
      if (_unsubscribe) {
        _unsubscribe();
        _unsubscribe = null;
      }

      if (_tl) {
        try {
          if (typeof _tl.offAll === 'function') { _tl.offAll(); }
        } catch (e) { /* ignore */ }
        _tl = null;
      }

      if (_fbCanvas) {
        _fbCanvas.removeEventListener('click', _fbOnClick);
        global.removeEventListener('resize', _fbDraw);
        _fbCanvas = null;
        _fbCtx = null;
      }

      if (_panelEl && _container) {
        _container.removeChild(_panelEl);
      }

      _panelEl      = null;
      _canvasWrap   = null;
      _selectedLabel= null;
      _selectedClip = null;
      _container    = null;
      _clips        = [];
      _part         = null;
      _fbRows       = [];
      _fbTotalMs    = 0;
      _fbPlayheadMs = 0;
    },

    /**
     * Load a clips array into the timeline.
     * One row per tier (T1/T2/T3/OTHER); each clip is one keyframe.
     * @param {Array}  clips
     * @param {number} part
     */
    loadClips: function (clips, part) {
      _clips = clips || [];
      _part  = part;
      _selectedClip = null;
      _updateSelectedLabel();

      if (_tl) {
        try {
          _tl.setModel(_buildModel(_clips));
        } catch (e) {
          console.error('[StudioTimeline] setModel failed:', e);
        }
        return;
      }

      // Fallback renderer
      _buildFbRows(_clips);
      _fbDraw();
    },

    /**
     * Return the currently-selected clip object, or null.
     * @returns {object|null}
     */
    getSelectedClip: function () {
      return _selectedClip;
    },

    /**
     * Move the playhead to a time position (in seconds).
     * @param {number} seconds
     */
    setPlayhead: function (seconds) {
      var ms = (seconds || 0) * MS_PER_S;

      if (_tl) {
        try {
          _tl.setTime(ms);
        } catch (e) { /* ignore if not yet initialised */ }
        return;
      }

      // Fallback renderer
      _fbPlayheadMs = ms;
      _fbDraw();
    },
  };

  global.StudioTimeline = _StudioTimeline;

}(typeof window !== 'undefined' ? window : this));
