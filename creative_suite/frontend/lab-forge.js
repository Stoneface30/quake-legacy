(function (global) {
  'use strict';
  var _logEl = null, _countEl = null;

  function _log(msg) {
    if (!_logEl) return;
    var line = document.createElement('div'); line.style.fontSize = '11px'; line.style.color = '#888';
    line.textContent = '[' + new Date().toLocaleTimeString() + '] ' + msg;
    _logEl.appendChild(line); _logEl.scrollTop = _logEl.scrollHeight;
  }

  function _fetchStatus() {
    fetch('/api/forge/status', { signal: AbortSignal.timeout(4000) })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) {
        if (!d || !_countEl) return;
        _countEl.textContent = (d.demo_count || 0) + ' demos · ' + (d.fragment_count || 0) + ' fragments';
      })
      .catch(function () {});
  }

  function mount(slot) {
    var wrap = document.createElement('div'); wrap.className = 'list-panel';
    var bar = document.createElement('div'); bar.className = 'list-toolbar';
    var title = document.createElement('span'); title.className = 'panel-iframe-title'; title.textContent = 'FORGE';
    _countEl = document.createElement('span'); _countEl.style.cssText = 'font-size:10px;color:#888;margin-left:auto';
    var btnRefresh = document.createElement('button'); btnRefresh.className = 'panel-iframe-btn';
    btnRefresh.textContent = 'REFRESH'; btnRefresh.addEventListener('click', _fetchStatus);
    bar.appendChild(title); bar.appendChild(_countEl); bar.appendChild(btnRefresh);
    _logEl = document.createElement('div');
    _logEl.style.cssText = 'flex:1;overflow-y:auto;padding:10px 14px;font-family:Consolas,monospace';
    wrap.appendChild(bar); wrap.appendChild(_logEl);
    slot.replaceChildren(wrap);
    _fetchStatus();
    _log('Forge ready. Use LAB \u00b7 Demos to pick a demo and LAB \u00b7 Extraction to process.');
  }

  function unmount() { _logEl = null; _countEl = null; }

  global.LabForge = { mount: mount, unmount: unmount };
}(window));
