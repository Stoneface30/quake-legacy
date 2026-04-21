(function (global) {
  'use strict';
  var _logEl = null, _statusEl = null, _demoLabel = null;

  function _log(msg, kind) {
    if (!_logEl) return;
    var line = document.createElement('div');
    line.textContent = '[' + new Date().toLocaleTimeString() + '] ' + msg;
    line.style.color = kind === 'err' ? '#ff6666' : kind === 'ok' ? '#9beab1' : '#888';
    line.style.fontSize = '11px';
    _logEl.appendChild(line); _logEl.scrollTop = _logEl.scrollHeight;
  }

  function _getDemo() {
    var st = global.StudioStore && global.StudioStore.getState();
    return st ? st.selectedDemo : null;
  }

  function _extract() {
    var demo = _getDemo();
    if (!demo) { _log('No demo selected — pick one in LAB \u00b7 Demos', 'err'); return; }
    if (_statusEl) { _statusEl.textContent = '\u25cf RUNNING'; _statusEl.style.color = '#e68a00'; }
    _log('Extracting: ' + demo, 'info');
    fetch('/api/forge/demo/extract', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ demo_path: demo, extract_frags: true }),
      signal: AbortSignal.timeout(30000),
    })
      .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
      .then(function (d) {
        if (_statusEl) { _statusEl.textContent = '\u25cf DONE'; _statusEl.style.color = '#44bb44'; }
        _log('OK \u00b7 ' + (d.fragments || 0) + ' fragments \u00b7 ' + (d.duration_s || 0) + 's', 'ok');
      })
      .catch(function (e) {
        if (_statusEl) { _statusEl.textContent = '\u25cf FAILED'; _statusEl.style.color = '#ff6666'; }
        _log('Failed: ' + e, 'err');
      });
  }

  function _syncDemo() {
    var demo = _getDemo();
    if (_demoLabel) _demoLabel.textContent = demo ? demo : '(none selected)';
  }

  function mount(slot) {
    var wrap = document.createElement('div'); wrap.className = 'list-panel';
    var bar = document.createElement('div'); bar.className = 'list-toolbar';
    var title = document.createElement('span'); title.className = 'panel-iframe-title'; title.textContent = 'EXTRACTION';
    _statusEl = document.createElement('span');
    _statusEl.textContent = '\u25cf IDLE'; _statusEl.style.color = '#888'; _statusEl.style.fontSize = '10px';
    var btnExtract = document.createElement('button'); btnExtract.className = 'panel-iframe-btn';
    btnExtract.textContent = 'EXTRACT'; btnExtract.addEventListener('click', _extract);
    bar.appendChild(title); bar.appendChild(_statusEl); bar.appendChild(btnExtract);

    var info = document.createElement('div');
    info.style.cssText = 'padding:8px 14px;font-size:11px;color:#888;border-bottom:1px solid #1a1a1a;flex-shrink:0';
    _demoLabel = document.createElement('span'); _demoLabel.style.color = '#c9a84c';
    var prefix = document.createElement('span'); prefix.textContent = 'Demo: ';
    info.appendChild(prefix); info.appendChild(_demoLabel);

    _logEl = document.createElement('div');
    _logEl.style.cssText = 'flex:1;overflow-y:auto;padding:10px 14px;font-family:Consolas,monospace';

    wrap.appendChild(bar); wrap.appendChild(info); wrap.appendChild(_logEl);
    slot.replaceChildren(wrap);
    _syncDemo();
    _log('Ready. Select a demo in LAB \u00b7 Demos then click EXTRACT.', 'info');
    if (global.StudioStore) {
      global.StudioStore.subscribe(function () { _syncDemo(); });
    }
  }

  function unmount() { _logEl = null; _statusEl = null; _demoLabel = null; }

  global.LabExtraction = { mount: mount, unmount: unmount };
}(window));
