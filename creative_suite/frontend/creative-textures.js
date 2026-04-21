(function (global) {
  'use strict';

  var _iframe = null;
  var _toolbar = null;
  var _pollTimer = null;

  function _fetchStatus() {
    fetch('/api/comfy/status', { signal: AbortSignal.timeout(3000) })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) {
        var dot   = document.getElementById('tex-status-dot');
        var label = document.getElementById('tex-status-label');
        if (!dot || !label) { return; }
        if (!d) {
          dot.style.background = '#444';
          label.textContent    = 'ComfyUI offline';
          return;
        }
        var queue = (d.queue_remaining !== undefined) ? d.queue_remaining : -1;
        if (queue > 0) {
          dot.style.background = '#c9a84c';
          label.textContent    = queue + ' job' + (queue !== 1 ? 's' : '') + ' queued';
        } else {
          dot.style.background = '#44bb44';
          label.textContent    = 'idle';
        }
      })
      .catch(function () {
        var dot = document.getElementById('tex-status-dot');
        if (dot) { dot.style.background = '#444'; }
      });
  }

  function _pollStatus() {
    _fetchStatus();
    _pollTimer = setInterval(_fetchStatus, 8000);
  }

  function _stopPoll() {
    if (_pollTimer !== null) { clearInterval(_pollTimer); _pollTimer = null; }
  }

  function mount(slot) {
    var wrap = document.createElement('div');
    wrap.style.cssText = 'display:flex;flex-direction:column;height:100%;overflow:hidden;background:#0d0d0d';
    var bar = document.createElement('div');
    bar.style.cssText = 'display:flex;align-items:center;gap:12px;padding:6px 14px;background:#161616;border-bottom:1px solid #2a2a2a;flex-shrink:0';
    var title = document.createElement('span');
    title.textContent = 'PHOTOREAL GALLERY';
    title.style.cssText = 'color:#c9a84c;font-size:11px;letter-spacing:2px;font-family:Consolas,monospace';
    var spacer = document.createElement('span'); spacer.style.flex = '1';
    var btnStyle = 'font-size:10px;letter-spacing:1px;padding:3px 10px;background:#1a1200;color:#c9a84c;border:1px solid #3a2800;border-radius:3px;cursor:pointer;font-family:Consolas,monospace';
    var btnRefresh = document.createElement('button'); btnRefresh.textContent = 'REFRESH'; btnRefresh.style.cssText = btnStyle;
    btnRefresh.addEventListener('click', function () { if (_iframe) { _iframe.src = _iframe.src; } });
    var btnOpen = document.createElement('button'); btnOpen.textContent = 'OPEN FULL'; btnOpen.style.cssText = btnStyle;
    btnOpen.addEventListener('click', function () { window.open('/gallery', '_blank'); });
    var statusDot = document.createElement('span');
    statusDot.id = 'tex-status-dot';
    statusDot.style.cssText = 'width:8px;height:8px;border-radius:50%;background:#444;display:inline-block';
    var statusLabel = document.createElement('span');
    statusLabel.id = 'tex-status-label';
    statusLabel.textContent = 'checking\u2026';
    statusLabel.style.cssText = 'font-size:10px;color:#666;font-family:Consolas,monospace';
    bar.appendChild(title); bar.appendChild(spacer); bar.appendChild(statusLabel); bar.appendChild(statusDot);
    bar.appendChild(btnRefresh); bar.appendChild(btnOpen);
    _toolbar = bar;
    var iframe = document.createElement('iframe');
    iframe.src = '/gallery';
    iframe.style.cssText = 'flex:1;border:none;width:100%;background:#0d0d0d';
    iframe.title = 'Photoreal Gallery';
    _iframe = iframe;
    wrap.appendChild(bar); wrap.appendChild(iframe);
    slot.replaceChildren(wrap);
    _pollStatus();
  }

  function unmount() {
    _stopPoll();
    _iframe = null;
    _toolbar = null;
  }

  global.CreativeTextures = { mount: mount, unmount: unmount };
  global.StudioTextures = global.CreativeTextures; // compat shim
}(window));
