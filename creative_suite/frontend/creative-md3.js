(function (global) {
  'use strict';
  function mount(slot) {
    var wrap = document.createElement('div'); wrap.className = 'list-panel';
    var bar = document.createElement('div'); bar.className = 'list-toolbar';
    var title = document.createElement('span'); title.className = 'panel-iframe-title'; title.textContent = 'MD3 VIEWER';
    bar.appendChild(title);
    var body = document.createElement('div');
    body.style.cssText = 'flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px;padding:24px';
    var note = document.createElement('div');
    note.style.cssText = 'color:#555;font-size:11px;font-family:Consolas,monospace;text-align:center;max-width:320px';
    note.textContent = 'No in-browser MD3 viewer available yet. Enter an asset ID to download the raw model file.';
    var inputRow = document.createElement('div'); inputRow.style.cssText = 'display:flex;gap:8px';
    var input = document.createElement('input');
    input.style.cssText = 'background:#111;color:#ddd;border:1px solid #333;padding:6px 8px;font-family:Consolas,monospace;font-size:11px;width:220px';
    input.placeholder = 'asset_id e.g. models/players/visor/head';
    var btnDl = document.createElement('button'); btnDl.className = 'panel-iframe-btn'; btnDl.textContent = 'DOWNLOAD MD3';
    btnDl.addEventListener('click', function () {
      var id = input.value.trim();
      if (id) window.open('/api/md3/' + encodeURIComponent(id), '_blank');
    });
    inputRow.appendChild(input); inputRow.appendChild(btnDl);
    body.appendChild(note); body.appendChild(inputRow);
    wrap.appendChild(bar); wrap.appendChild(body);
    slot.replaceChildren(wrap);
  }
  function unmount() {}
  global.CreativeMd3Viewer = { mount: mount, unmount: unmount };
}(window));
