/**
 * PANTHEON STUDIO — Inspector Panel
 * studio-inspector.js  (v2 — plain DOM, no Tweakpane)
 *
 * Displays and edits clip properties for the currently selected clip.
 * Subscribes to StudioStore.selectedClip and repopulates on every change.
 *
 * Sections:
 *   CLIP INFO   — read-only: filename, tier, is_fl, duration
 *   OVERRIDES   — editable: head_trim, tail_trim, slow_rate
 *   EFFECTS     — editable: transition type
 *
 * "APPLY" button saves overrides back via PUT /api/studio/part/{n}/clips.
 *
 * Exposed on: window.StudioInspector
 * Rule UI-1: DOM via createElement/textContent only.
 * Rule UI-2: state from StudioStore, no local drift.
 */
(function (global) {
  'use strict';

  // ── Module state ─────────────────────────────────────────────────────────────

  var _container  = null;
  var _panelEl    = null;
  var _bodyEl     = null;
  var _unsubscribe = null;
  var _currentClip = null;

  var TRANSITIONS = ['none', 'xfade', 'fade', 'hard_cut'];

  var FX_CATALOGUE = [
    { type: 'slowmo',        label: 'Slow Motion',   params: { rate:      { min: 0.1,  max: 0.9,  step: 0.1,  def: 0.5  }, window_s: { min: 0.5, max: 4.0, step: 0.5, def: 1.6 } } },
    { type: 'speedup',       label: 'Speed Up',      params: { rate:      { min: 1.2,  max: 4.0,  step: 0.2,  def: 2.0  }, window_s: { min: 0.5, max: 4.0, step: 0.5, def: 1.6 } } },
    { type: 'zoom',          label: 'Zoom',          params: { scale:     { min: 1.05, max: 2.0,  step: 0.05, def: 1.3  } } },
    { type: 'vignette',      label: 'Vignette',      params: { strength:  { min: 0.0,  max: 1.0,  step: 0.05, def: 0.5  } } },
    { type: 'shine_on_kill', label: 'Shine On Kill', params: { intensity: { min: 0.1,  max: 2.0,  step: 0.1,  def: 1.0  } } },
    { type: 'bass_drop',     label: 'Bass Drop',     params: { depth_db:  { min: 1,    max: 12,   step: 1,    def: 6    } } },
    { type: 'reverb_tail',   label: 'Reverb Tail',   params: { decay_s:   { min: 0.1,  max: 2.0,  step: 0.1,  def: 0.6  } } },
  ];

  // ── DOM helpers ───────────────────────────────────────────────────────────────

  function _el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls)  n.className   = cls;
    if (text !== undefined && text !== null) n.textContent = text;
    return n;
  }

  function _fmt(val) {
    return (val === null || val === undefined) ? '—' : String(val);
  }

  function _fmtDur(s) {
    if (s === null || s === undefined) return '—';
    var n = Number(s);
    return isNaN(n) ? '—' : n.toFixed(1) + 's';
  }

  // ── Section builders ─────────────────────────────────────────────────────────

  function _infoRow(label, value) {
    var row = _el('div', 'insp-row');
    row.appendChild(_el('span', 'insp-lbl', label));
    var v = _el('span', 'insp-val', value);
    row.appendChild(v);
    return row;
  }

  function _rangeRow(label, min, max, step, initVal, onChange) {
    var row = _el('div', 'insp-row');
    row.appendChild(_el('span', 'insp-lbl', label));

    var wrap = _el('div', 'insp-range-wrap');

    var range = document.createElement('input');
    range.type  = 'range';
    range.className = 'insp-range';
    range.min   = String(min);
    range.max   = String(max);
    range.step  = String(step);
    range.value = String(initVal);

    var num = document.createElement('input');
    num.type  = 'number';
    num.className = 'insp-number';
    num.min   = String(min);
    num.max   = String(max);
    num.step  = String(step);
    num.value = String(initVal);

    range.addEventListener('input', function () {
      num.value = range.value;
      onChange(parseFloat(range.value));
    });
    num.addEventListener('change', function () {
      var v = Math.max(min, Math.min(max, parseFloat(num.value) || 0));
      num.value   = String(v);
      range.value = String(v);
      onChange(v);
    });

    wrap.appendChild(range);
    wrap.appendChild(num);
    row.appendChild(wrap);
    return row;
  }

  function _selectRow(label, options, initVal, onChange) {
    var row = _el('div', 'insp-row');
    row.appendChild(_el('span', 'insp-lbl', label));
    var sel = document.createElement('select');
    sel.className = 'insp-select';
    options.forEach(function (opt) {
      var o = document.createElement('option');
      o.value = opt;
      o.textContent = opt;
      if (opt === initVal) o.selected = true;
      sel.appendChild(o);
    });
    sel.addEventListener('change', function () { onChange(sel.value); });
    row.appendChild(sel);
    return row;
  }

  // ── FX Stack helpers ─────────────────────────────────────────────────────────

  function _buildFxCard(fx, arrangementId, part, onRemove) {
    var cat   = FX_CATALOGUE.find(function (c) { return c.type === fx.effect_type; });
    var label = cat ? cat.label : fx.effect_type;
    var pDef  = cat ? cat.params : {};

    var card = _el('div', 'fx-card' + (fx.enabled ? '' : ' fx-card--disabled'));
    var hdr  = _el('div', 'fx-card-hdr');

    // Toggle enable
    var tog = document.createElement('input');
    tog.type      = 'checkbox';
    tog.className = 'fx-toggle';
    tog.checked   = !!fx.enabled;
    tog.addEventListener('change', function () {
      card.classList.toggle('fx-card--disabled', !tog.checked);
      fetch('/api/studio/part/' + part + '/arrangement/' + arrangementId + '/fx/' + fx.id, {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: tog.checked ? 1 : 0 }),
        signal: AbortSignal.timeout(5000),
      }).catch(function (e) { console.error('[FX] toggle', e); });
    });
    hdr.appendChild(tog);

    // Label + collapse toggle
    var lbl = _el('span', 'fx-card-label', label);
    hdr.appendChild(lbl);

    var colBtn = _el('button', 'fx-collapse-btn', '▾');
    hdr.appendChild(colBtn);

    // Remove button
    var remBtn = _el('button', 'fx-remove-btn', '✕');
    remBtn.addEventListener('click', function () {
      fetch('/api/studio/part/' + part + '/arrangement/' + arrangementId + '/fx/' + fx.id, {
        method: 'DELETE', signal: AbortSignal.timeout(5000),
      })
        .then(function (r) { if (r.ok) onRemove(); })
        .catch(function (e) { console.error('[FX] delete', e); });
    });
    hdr.appendChild(remBtn);
    card.appendChild(hdr);

    // Param sliders (collapsible)
    var body   = _el('div', 'fx-card-body');
    var params = Object.assign({}, pDef ? Object.fromEntries(Object.entries(pDef).map(function (kv) { return [kv[0], kv[1].def]; })) : {});
    try { Object.assign(params, JSON.parse(fx.params || '{}')); } catch (e) {}

    Object.keys(pDef).forEach(function (k) {
      var spec = pDef[k];
      body.appendChild(_rangeRow(k, spec.min, spec.max, spec.step, params[k] !== undefined ? params[k] : spec.def, function (v) {
        params[k] = v;
        fetch('/api/studio/part/' + part + '/arrangement/' + arrangementId + '/fx/' + fx.id, {
          method: 'PUT', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ params: params }),
          signal: AbortSignal.timeout(5000),
        }).catch(function (e) { console.error('[FX] param', e); });
      }));
    });

    card.appendChild(body);

    colBtn.addEventListener('click', function () {
      var collapsed = body.style.display === 'none';
      body.style.display = collapsed ? '' : 'none';
      colBtn.textContent = collapsed ? '▾' : '▸';
    });

    return card;
  }

  function _buildAddFxRow(arrangementId, part, fxList, existingFx, onAdded) {
    var row = _el('div', 'fx-add-row');
    var sel = document.createElement('select');
    sel.className = 'fx-add-select';

    var used = (existingFx || []).map(function (f) { return f.effect_type; });
    FX_CATALOGUE.forEach(function (cat) {
      if (used.indexOf(cat.type) !== -1) return;
      var o = document.createElement('option');
      o.value = cat.type; o.textContent = cat.label;
      sel.appendChild(o);
    });
    row.appendChild(sel);

    var addBtn = _el('button', 'fx-add-btn', '+ ADD');
    addBtn.addEventListener('click', function () {
      var type = sel.value;
      if (!type) return;
      var cat = FX_CATALOGUE.find(function (c) { return c.type === type; });
      var defParams = cat ? Object.fromEntries(Object.entries(cat.params).map(function (kv) { return [kv[0], kv[1].def]; })) : {};
      fetch('/api/studio/part/' + part + '/arrangement/' + arrangementId + '/fx', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ effect_type: type, params: defParams }),
        signal: AbortSignal.timeout(5000),
      })
        .then(function (r) { return r.ok ? r.json() : Promise.reject('HTTP ' + r.status); })
        .then(function (d) { if (onAdded) onAdded(d); })
        .catch(function (e) { console.error('[FX] add', e); });
    });
    row.appendChild(addBtn);
    return row;
  }

  function _buildFxSection(clip, part) {
    var sec = _el('div', 'insp-section');
    sec.appendChild(_el('div', 'insp-section-title', 'FX STACK'));
    var loading = _el('div', 'insp-fx-loading', 'Loading…');
    sec.appendChild(loading);

    var clipPath = clip.path || clip.clip_path || '';

    fetch('/api/studio/part/' + part + '/arrangement', { signal: AbortSignal.timeout(6000) })
      .then(function (r) { return r.ok ? r.json() : { clips: [] }; })
      .then(function (d) {
        loading.remove();
        var arr = (d.clips || []).find(function (a) {
          return a.clip_path === clipPath ||
                 (clipPath && a.clip_path && (clipPath.endsWith(a.clip_path) || a.clip_path.endsWith(clipPath)));
        });
        if (!arr) {
          sec.appendChild(_el('div', 'insp-fx-empty', 'Add clip to arrangement first'));
          return;
        }

        var fxList = _el('div', 'insp-fx-list');

        function _refresh() {
          fetch('/api/studio/part/' + part + '/arrangement', { signal: AbortSignal.timeout(5000) })
            .then(function (r) { return r.ok ? r.json() : { clips: [] }; })
            .then(function (data) {
              while (fxList.firstChild) fxList.removeChild(fxList.firstChild);
              var fresh = (data.clips || []).find(function (a) { return a.id === arr.id; });
              var effects = fresh ? (fresh.effects || []) : [];
              arr.effects = effects;
              effects.forEach(function (fx) {
                fxList.appendChild(_buildFxCard(fx, arr.id, part, _refresh));
              });
              var addRow = sec.querySelector('.fx-add-row');
              if (addRow) addRow.remove();
              sec.appendChild(_buildAddFxRow(arr.id, part, fxList, effects, _refresh));
            })
            .catch(function (e) { console.error('[FX] refresh', e); });
        }

        (arr.effects || []).forEach(function (fx) {
          fxList.appendChild(_buildFxCard(fx, arr.id, part, _refresh));
        });
        sec.appendChild(fxList);
        sec.appendChild(_buildAddFxRow(arr.id, part, fxList, arr.effects || [], _refresh));
      })
      .catch(function (e) {
        loading.textContent = 'FX load error';
        console.error('[FX] section', e);
      });

    return sec;
  }

  // ── Panel population ─────────────────────────────────────────────────────────

  function _clearBody() {
    if (_bodyEl) {
      while (_bodyEl.firstChild) _bodyEl.removeChild(_bodyEl.firstChild);
    }
  }

  function _showEmpty() {
    _clearBody();
    if (!_bodyEl) return;
    _bodyEl.appendChild(_el('div', 'insp-empty', 'No clip selected'));
  }

  function _showClip(clip) {
    _clearBody();
    if (!_bodyEl) return;

    var values = {
      head_trim:  clip.head_trim  !== undefined ? clip.head_trim  : 0.0,
      tail_trim:  clip.tail_trim  !== undefined ? clip.tail_trim  : 0.0,
      slow_rate:  clip.slow_rate  !== undefined ? clip.slow_rate  : 1.0,
      transition: clip.transition || 'none',
    };

    // ── CLIP INFO ────────────────────────────────────────────────────────────
    var infoSec = _el('div', 'insp-section');
    infoSec.appendChild(_el('div', 'insp-section-title', 'CLIP INFO'));

    var rawName = clip.name || (clip.path ? clip.path.split(/[\\/]/).pop() : '(unnamed)');
    infoSec.appendChild(_infoRow('file', rawName));
    infoSec.appendChild(_infoRow('tier', clip.tier || '—'));
    infoSec.appendChild(_infoRow('fl', clip.is_fl ? 'yes' : 'no'));
    infoSec.appendChild(_infoRow('duration', _fmtDur(clip.duration_s)));
    if (clip.weapon)  infoSec.appendChild(_infoRow('weapon', _fmt(clip.weapon)));
    if (clip.map)     infoSec.appendChild(_infoRow('map',    _fmt(clip.map)));
    _bodyEl.appendChild(infoSec);

    // ── OVERRIDES ───────────────────────────────────────────────────────────
    var ovSec = _el('div', 'insp-section');
    ovSec.appendChild(_el('div', 'insp-section-title', 'OVERRIDES'));
    ovSec.appendChild(_rangeRow('head trim', 0, 10, 0.1, values.head_trim, function (v) { values.head_trim = v; }));
    ovSec.appendChild(_rangeRow('tail trim', 0, 10, 0.1, values.tail_trim, function (v) { values.tail_trim = v; }));
    ovSec.appendChild(_rangeRow('slow rate', 0.1, 2.0, 0.1, values.slow_rate, function (v) { values.slow_rate = v; }));
    _bodyEl.appendChild(ovSec);

    // ── EFFECTS ─────────────────────────────────────────────────────────────
    var fxSec = _el('div', 'insp-section');
    fxSec.appendChild(_el('div', 'insp-section-title', 'EFFECTS'));
    fxSec.appendChild(_selectRow('transition', TRANSITIONS, values.transition, function (v) { values.transition = v; }));
    _bodyEl.appendChild(fxSec);

    // ── FX STACK (async — fetches arrangement_id) ────────────────────────────
    var store2 = global.StudioStore;
    var part2  = store2 ? store2.getState().activePart : null;
    if (part2) {
      _bodyEl.appendChild(_buildFxSection(clip, part2));
    }

    // ── APPLY ────────────────────────────────────────────────────────────────
    var applyBtn = _el('button', 'insp-apply-btn', 'APPLY');
    applyBtn.addEventListener('click', function () {
      _applyValues(clip, values);
    });
    _bodyEl.appendChild(applyBtn);
  }

  function _applyValues(clip, values) {
    var store = global.StudioStore;
    if (!store) return;
    var state = store.getState();
    var part  = state.activePart;
    if (!part) return;

    var updated = state.clips.map(function (c) {
      if (c.path !== clip.path) return c;
      return Object.assign({}, c, {
        head_trim:  values.head_trim,
        tail_trim:  values.tail_trim,
        slow_rate:  values.slow_rate,
        transition: values.transition,
      });
    });

    fetch('/api/studio/part/' + part + '/clips', {
      method:  'PUT',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ clips: updated }),
      signal:  AbortSignal.timeout(6000),
    })
      .then(function (r) { return r.ok ? r.json() : Promise.reject('HTTP ' + r.status); })
      .then(function () {
        store.dispatch({ type: 'SET_STATUS_MSG', payload: 'Clip overrides saved.' });
        var btn = _bodyEl && _bodyEl.querySelector('.insp-apply-btn');
        if (btn) { btn.textContent = 'SAVED ✓'; setTimeout(function () { if (btn) btn.textContent = 'APPLY'; }, 1400); }
      })
      .catch(function (e) {
        store.dispatch({ type: 'SET_STATUS_MSG', payload: 'Save failed: ' + e });
      });
  }

  // ── Store subscription ────────────────────────────────────────────────────────

  function _subscribeStore() {
    var store = global.StudioStore;
    if (!store) return;

    var init = store.getState().selectedClip;
    if (init) { _currentClip = init; _showClip(init); }
    else      { _showEmpty(); }

    _unsubscribe = store.subscribe(function (state, prev) {
      if (state.selectedClip === prev.selectedClip) return;
      _currentClip = state.selectedClip;
      if (_currentClip) _showClip(_currentClip);
      else              _showEmpty();
    });
  }

  // ── DOM construction ──────────────────────────────────────────────────────────

  function _buildDom(containerEl) {
    var panel = _el('div', 'insp-panel');

    _bodyEl = _el('div', 'insp-body');
    panel.appendChild(_bodyEl);

    containerEl.appendChild(panel);
    _panelEl = panel;
  }

  // ── Public API ────────────────────────────────────────────────────────────────

  var StudioInspector = {

    mount: function (containerEl) {
      if (_panelEl) this.unmount();
      _container = containerEl;
      _buildDom(containerEl);
      _subscribeStore();
    },

    unmount: function () {
      if (_unsubscribe) { _unsubscribe(); _unsubscribe = null; }
      if (_panelEl && _panelEl.parentNode) _panelEl.parentNode.removeChild(_panelEl);
      _panelEl    = null;
      _bodyEl     = null;
      _container  = null;
      _currentClip = null;
    },

    inspectClip: function (clip) {
      if (!clip) { _showEmpty(); return; }
      _currentClip = clip;
      _showClip(clip);
    },

    getValues: function () {
      return _currentClip ? Object.assign({}, _currentClip) : null;
    },
  };

  global.StudioInspector = StudioInspector;

}(typeof window !== 'undefined' ? window : this));
