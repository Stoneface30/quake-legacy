(function (global) {
  'use strict';
  var _logEl = null, _trafficEl = null, _btnBuild = null, _btnInstall = null;

  function _log(msg) {
    if (!_logEl) return;
    var line = document.createElement('div'); line.style.fontSize = '11px'; line.style.color = '#888';
    line.textContent = '[' + new Date().toLocaleTimeString() + '] ' + msg;
    _logEl.appendChild(line);
    while (_logEl.childNodes.length > 200) { _logEl.removeChild(_logEl.firstChild); }
    _logEl.scrollTop = _logEl.scrollHeight;
  }

  function _dot(ok) {
    var d = document.createElement('span');
    d.style.cssText = 'width:10px;height:10px;border-radius:50%;display:inline-block;margin-right:6px;background:' + (ok ? '#44bb44' : '#c41515');
    return d;
  }

  function _checkGate(d) {
    var variants = d.variants || [];
    var approved = variants.filter(function (v) { return v.status === 'approved'; }).length;
    var hasSurface = variants.some(function (v) { return v.status === 'approved' && v.category === 'surface'; });
    var hasSkin = variants.some(function (v) { return v.status === 'approved' && v.category === 'skin'; });
    if (_trafficEl) {
      _trafficEl.replaceChildren();
      var rows = [
        [approved >= 5, 'Approved variants: ' + approved + ' / 5'],
        [hasSurface, 'Surface category approved'],
        [hasSkin, 'Skin category approved']
      ];
      rows.forEach(function (r) {
        var row = document.createElement('div'); row.style.cssText = 'display:flex;align-items:center;padding:4px 14px;font-size:11px;color:#aaa';
        row.appendChild(_dot(r[0]));
        row.appendChild(document.createTextNode(r[1]));
        _trafficEl.appendChild(row);
      });
    }
    var allGreen = approved >= 5 && hasSurface && hasSkin;
    if (_btnBuild) _btnBuild.disabled = !allGreen;
    if (_btnInstall) _btnInstall.disabled = !allGreen;
  }

  function _refresh() {
    fetch('/api/comfy/status', { signal: AbortSignal.timeout(5000) })
      .then(function (r) { return r.ok ? r.json() : { variants: [] }; })
      .then(function (d) { _checkGate(d); })
      .catch(function () {});
  }

  function mount(slot) {
    var wrap = document.createElement('div'); wrap.className = 'list-panel';
    var bar = document.createElement('div'); bar.className = 'list-toolbar';
    var title = document.createElement('span'); title.className = 'panel-iframe-title'; title.textContent = 'PACKS';
    _btnBuild = document.createElement('button'); _btnBuild.className = 'panel-iframe-btn'; _btnBuild.textContent = 'BUILD'; _btnBuild.disabled = true;
    _btnInstall = document.createElement('button'); _btnInstall.className = 'panel-iframe-btn'; _btnInstall.textContent = 'INSTALL'; _btnInstall.disabled = true;
    var btnCheck = document.createElement('button'); btnCheck.className = 'panel-iframe-btn'; btnCheck.textContent = 'CHECK'; btnCheck.addEventListener('click', _refresh);
    bar.appendChild(title); bar.appendChild(_btnBuild); bar.appendChild(_btnInstall); bar.appendChild(btnCheck);
    _trafficEl = document.createElement('div'); _trafficEl.style.cssText = 'flex-shrink:0;padding:4px 0;border-bottom:1px solid #1a1a1a';
    _logEl = document.createElement('div'); _logEl.style.cssText = 'flex:1;overflow-y:auto;padding:10px 14px;font-family:Consolas,monospace';
    wrap.appendChild(bar); wrap.appendChild(_trafficEl); wrap.appendChild(_logEl);
    slot.replaceChildren(wrap);
    _btnBuild.addEventListener('click', function () {
      var btn = _btnBuild;
      if (btn) btn.disabled = true;
      fetch('/api/packs/build', { method: 'POST', signal: AbortSignal.timeout(60000) })
        .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
        .then(function (d) { _log('BUILD OK \u00b7 ' + (d.pk3_path || '') + ' \u00b7 ' + (d.sha256 || '')); if (btn) btn.disabled = false; })
        .catch(function (e) { _log('BUILD FAILED ' + e); if (btn) btn.disabled = false; });
    });
    _btnInstall.addEventListener('click', function () {
      var btn = _btnInstall;
      if (btn) btn.disabled = true;
      fetch('/api/packs/install', { method: 'POST', signal: AbortSignal.timeout(30000) })
        .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
        .then(function (d) { _log('INSTALL OK \u00b7 ' + (d.target_path || '')); if (btn) btn.disabled = false; })
        .catch(function (e) { _log('INSTALL FAILED ' + e); if (btn) btn.disabled = false; });
    });
    _refresh();
  }

  function unmount() { _logEl = null; _trafficEl = null; _btnBuild = null; _btnInstall = null; }

  global.CreativePacks = { mount: mount, unmount: unmount };
}(window));
