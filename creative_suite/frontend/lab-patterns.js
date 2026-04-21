(function (global) {
  'use strict';
  var _list = null, _unsub = null;

  function _renderList(patterns) {
    if (!_list) return;
    _list.replaceChildren();
    if (!patterns.length) {
      var empty = document.createElement('div');
      empty.style.cssText = 'padding:20px 14px;color:#555;font-size:11px';
      empty.textContent = 'No patterns found for this part.';
      _list.appendChild(empty);
      return;
    }
    patterns.forEach(function (p) {
      var row = document.createElement('div'); row.className = 'list-row';
      var icn = document.createElement('span'); icn.textContent = '\u25c6'; icn.style.color = '#3a66b8';
      var body = document.createElement('div');
      var prim = document.createElement('div'); prim.className = 'r-primary';
      prim.textContent = (p.name || p.pattern_id || '').replace(/_/g, ' ');
      var sub = document.createElement('div'); sub.className = 'r-sub';
      sub.textContent = (p.count || 0) + ' events \u00b7 ' + (p.maps || []).join(', ');
      body.appendChild(prim); body.appendChild(sub);
      var meta = document.createElement('span'); meta.className = 'r-meta'; meta.textContent = p.weapon || '';
      row.appendChild(icn); row.appendChild(body); row.appendChild(meta);
      row.addEventListener('click', function () {
        global.StudioStore.dispatch({ type: 'SET_ACTIVE_MODE', mode: 'studio' });
        global.StudioStore.dispatch({ type: 'SET_ACTIVE_PAGE', page: 'inspector' });
      });
      _list.appendChild(row);
    });
  }

  function _fetch() {
    if (!global.StudioStore) return;
    var part = global.StudioStore.getState().activePart;
    if (!part) {
      if (_list) {
        _list.replaceChildren();
        var note = document.createElement('div');
        note.style.cssText = 'padding:20px 14px;color:#555;font-size:11px';
        note.textContent = 'No part selected. Pick a part in STUDIO first.';
        _list.appendChild(note);
      }
      return;
    }
    fetch('/api/phase1/parts/' + part + '/artifacts', { signal: AbortSignal.timeout(5000) })
      .then(function (r) { return r.ok ? r.json() : { event_diversity: {} }; })
      .then(function (d) {
        var div = d.event_diversity || {};
        var patterns = Object.keys(div).map(function (id) {
          return Object.assign({ pattern_id: id, name: id }, div[id]);
        });
        _renderList(patterns);
      })
      .catch(function () { _renderList([]); });
  }

  function mount(slot) {
    var wrap = document.createElement('div'); wrap.className = 'list-panel';
    var bar = document.createElement('div'); bar.className = 'list-toolbar';
    var title = document.createElement('span'); title.className = 'panel-iframe-title'; title.textContent = 'PATTERNS';
    var filter = document.createElement('input'); filter.className = 'list-filter'; filter.placeholder = 'filter\u2026';
    filter.addEventListener('input', function () {
      var q = filter.value.toLowerCase();
      if (!_list) return;
      _list.querySelectorAll('.list-row').forEach(function (row) {
        row.style.display = row.textContent.toLowerCase().indexOf(q) !== -1 ? '' : 'none';
      });
    });
    bar.appendChild(title); bar.appendChild(filter);
    var scroll = document.createElement('div'); scroll.className = 'list-scroll';
    _list = scroll;
    wrap.appendChild(bar); wrap.appendChild(scroll);
    slot.replaceChildren(wrap);
    _fetch();
    if (global.StudioStore) {
      _unsub = global.StudioStore.subscribe(function () { _fetch(); });
    }
  }

  function unmount() {
    if (_unsub) { _unsub(); _unsub = null; }
    _list = null;
  }

  global.LabPatterns = { mount: mount, unmount: unmount };
}(window));
