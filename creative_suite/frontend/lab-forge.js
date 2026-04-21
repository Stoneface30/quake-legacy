(function (global) {
  'use strict';
  var _logEl = null, _statusEl = null, _poll = null;

  function _log(msg, kind) {
    if (!_logEl) return;
    var line = document.createElement('div');
    line.textContent = '[' + new Date().toLocaleTimeString() + '] ' + msg;
    line.style.color = kind === 'err' ? '#ff6666' : kind === 'ok' ? '#9beab1' : '#888';
    line.style.fontSize = '11px';
    _logEl.appendChild(line);
    while (_logEl.childNodes.length > 200) { _logEl.removeChild(_logEl.firstChild); }
    _logEl.scrollTop = _logEl.scrollHeight;
  }

  function _pollStatus() {
    fetch('/api/forge/status', { signal: AbortSignal.timeout(4000) })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) {
        if (!d || !_statusEl) return;
        var st = d.status || 'idle';
        _statusEl.textContent = st.toUpperCase();
        _statusEl.style.color = st === 'idle' ? '#44bb44' : st === 'busy' ? '#e68a00' : '#888';
      })
      .catch(function () {
        if (_statusEl) { _statusEl.textContent = 'OFFLINE'; _statusEl.style.color = '#888'; }
      });
  }

  function mount(slot) {
    var wrap = document.createElement('div'); wrap.className = 'list-panel';
    var bar = document.createElement('div'); bar.className = 'list-toolbar';
    var title = document.createElement('span'); title.className = 'panel-iframe-title'; title.textContent = 'FORGE';
    _statusEl = document.createElement('span');
    _statusEl.style.cssText = 'font-size:10px;color:#888;margin-left:8px';
    _statusEl.textContent = '...';
    var btnIntro = document.createElement('button'); btnIntro.className = 'panel-iframe-btn'; btnIntro.textContent = 'GENERATE INTRO';
    btnIntro.addEventListener('click', function () {
      var st = global.StudioStore && global.StudioStore.getState();
      var part = st ? st.activePart || 1 : 1;
      fetch('/api/forge/intro', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ part: part, style: 'default', duration_s: 8 }),
        signal: AbortSignal.timeout(10000)
      })
        .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
        .then(function (d) { _log('OK job_id=' + (d.job_id || '?'), 'ok'); })
        .catch(function (e) { _log('FAILED ' + e, 'err'); });
    });
    var btnExtract = document.createElement('button'); btnExtract.className = 'panel-iframe-btn'; btnExtract.textContent = 'EXTRACT DEMO';
    btnExtract.addEventListener('click', function () {
      var st = global.StudioStore && global.StudioStore.getState();
      var demo = st ? st.selectedDemo : null;
      if (!demo) { _log('No demo selected', 'err'); return; }
      fetch('/api/forge/demo/extract', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ demo_path: demo, extract_frags: true }),
        signal: AbortSignal.timeout(30000)
      })
        .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
        .then(function (d) { _log('OK ' + (d.fragments || 0) + ' frags', 'ok'); })
        .catch(function (e) { _log('FAILED ' + e, 'err'); });
    });
    bar.appendChild(title); bar.appendChild(_statusEl); bar.appendChild(btnIntro); bar.appendChild(btnExtract);
    _logEl = document.createElement('div');
    _logEl.style.cssText = 'flex:1;overflow-y:auto;padding:10px 14px;font-family:Consolas,monospace';
    wrap.appendChild(bar); wrap.appendChild(_logEl);
    slot.replaceChildren(wrap);
    _pollStatus();
    _poll = setInterval(_pollStatus, 5000);
    _log('Forge ready.', 'info');
  }

  function unmount() {
    if (_poll !== null) { clearInterval(_poll); _poll = null; }
    _logEl = null; _statusEl = null;
  }

  global.LabForge = { mount: mount, unmount: unmount };
}(window));
