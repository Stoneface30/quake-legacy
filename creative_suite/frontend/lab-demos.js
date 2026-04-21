(function (global) {
  'use strict';
  var _list = null, _poll = null;

  function _renderList(rows) {
    if (!_list) return;
    _list.replaceChildren();
    rows.forEach(function (r) {
      var row = document.createElement('div');
      row.className = 'list-row';
      row.setAttribute('data-demo', r.name);
      var icn = document.createElement('span');
      icn.textContent = '\u25c6'; icn.style.color = '#c9a84c';
      var body = document.createElement('div');
      var p = document.createElement('div'); p.className = 'r-primary'; p.textContent = r.name;
      var s = document.createElement('div'); s.className = 'r-sub'; s.textContent = r.map + ' \u00b7 ' + r.size_mb + ' MB';
      body.appendChild(p); body.appendChild(s);
      var meta = document.createElement('span'); meta.className = 'r-meta'; meta.textContent = r.state || 'fresh';
      row.appendChild(icn); row.appendChild(body); row.appendChild(meta);
      row.addEventListener('click', function () {
        global.StudioStore.dispatch({ type: 'SET_SELECTED_DEMO', demo: r.name });
        global.StudioStore.dispatch({ type: 'SET_ACTIVE_PAGE', page: 'extraction' });
      });
      _list.appendChild(row);
    });
  }

  function _fetchDemos() {
    fetch('/api/forge/demos', { signal: AbortSignal.timeout(5000) })
      .then(function (r) { return r.ok ? r.json() : { demos: [] }; })
      .then(function (d) { _renderList(d.demos || []); })
      .catch(function () {});
  }

  function mount(slot) {
    var wrap = document.createElement('div'); wrap.className = 'list-panel';
    var bar = document.createElement('div'); bar.className = 'list-toolbar';
    var title = document.createElement('span'); title.className = 'panel-iframe-title'; title.textContent = 'DEMOS';
    var filter = document.createElement('input'); filter.className = 'list-filter';
    filter.placeholder = 'filter by map or date\u2026';
    filter.addEventListener('input', function () {
      var q = filter.value.toLowerCase();
      _list.querySelectorAll('.list-row').forEach(function (row) {
        row.style.display = row.textContent.toLowerCase().indexOf(q) !== -1 ? '' : 'none';
      });
    });
    var btnRefresh = document.createElement('button'); btnRefresh.className = 'panel-iframe-btn';
    btnRefresh.textContent = 'REFRESH'; btnRefresh.addEventListener('click', _fetchDemos);
    bar.appendChild(title); bar.appendChild(filter); bar.appendChild(btnRefresh);
    var scroll = document.createElement('div'); scroll.className = 'list-scroll';
    _list = scroll;
    wrap.appendChild(bar); wrap.appendChild(scroll);
    slot.replaceChildren(wrap);
    _fetchDemos();
    _poll = setInterval(_fetchDemos, 15000);
  }

  function unmount() {
    if (_poll !== null) { clearInterval(_poll); _poll = null; }
    _list = null;
  }

  global.LabDemos = { mount: mount, unmount: unmount };
}(window));
