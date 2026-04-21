(function (global) {
  'use strict';
  var CATEGORY = 'skin';
  var GLOBAL   = 'CreativeSkins';
  var TITLE    = 'SKINS';
  var _grid = null;
  var _overlay = null;

  function _openPrompt(asset) {
    var overlay = document.createElement('div');
    overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.75);z-index:9999;display:flex;align-items:center;justify-content:center';
    var modal = document.createElement('div');
    modal.style.cssText = 'background:#1a1a1a;border:1px solid #333;padding:20px;width:400px;max-width:90vw;display:flex;flex-direction:column;gap:10px';
    var heading = document.createElement('div'); heading.style.cssText = 'color:#c9a84c;font-size:13px;font-family:Consolas,monospace'; heading.textContent = asset.name || asset.id;
    var textarea = document.createElement('textarea'); textarea.rows = 3;
    textarea.style.cssText = 'resize:vertical;background:#111;color:#ddd;border:1px solid #333;padding:6px;font-family:Consolas,monospace;font-size:11px;width:100%;box-sizing:border-box';
    textarea.placeholder = 'Positive prompt suffix...';
    var sliderRow = document.createElement('div'); sliderRow.style.cssText = 'display:flex;align-items:center;gap:8px';
    var sliderLabel = document.createElement('span'); sliderLabel.textContent = 'Denoise'; sliderLabel.style.cssText = 'font-size:11px;color:#888;width:60px';
    var slider = document.createElement('input'); slider.type = 'range'; slider.min = '0.1'; slider.max = '0.8'; slider.step = '0.05'; slider.value = '0.35';
    slider.style.cssText = 'flex:1';
    var sliderVal = document.createElement('span'); sliderVal.textContent = '0.35'; sliderVal.style.cssText = 'font-size:11px;color:#888;width:32px;text-align:right';
    slider.addEventListener('input', function () { sliderVal.textContent = slider.value; });
    sliderRow.appendChild(sliderLabel); sliderRow.appendChild(slider); sliderRow.appendChild(sliderVal);
    var btnRow = document.createElement('div'); btnRow.style.cssText = 'display:flex;gap:8px;justify-content:flex-end';
    var btnCancel = document.createElement('button'); btnCancel.className = 'panel-iframe-btn'; btnCancel.textContent = 'CANCEL';
    var btnQueue = document.createElement('button'); btnQueue.className = 'panel-iframe-btn'; btnQueue.textContent = 'QUEUE';
    btnRow.appendChild(btnCancel); btnRow.appendChild(btnQueue);
    modal.appendChild(heading); modal.appendChild(textarea); modal.appendChild(sliderRow); modal.appendChild(btnRow);
    overlay.appendChild(modal);
    _overlay = overlay;
    document.body.appendChild(overlay);
    function close() { if (overlay.parentNode) overlay.parentNode.removeChild(overlay); _overlay = null; }
    btnCancel.addEventListener('click', close);
    overlay.addEventListener('click', function (e) { if (e.target === overlay) close(); });
    btnQueue.addEventListener('click', function () {
      btnQueue.disabled = true;
      fetch('/api/comfy/queue', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ asset_id: asset.id, user_prompt: textarea.value, denoise: parseFloat(slider.value) }),
        signal: AbortSignal.timeout(10000)
      })
        .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
        .then(function () { close(); })
        .catch(function (e) { btnQueue.textContent = 'ERR ' + e; btnQueue.disabled = false; });
    });
  }

  function _renderGrid(assets) {
    if (!_grid) return;
    _grid.replaceChildren();
    if (!assets.length) {
      var empty = document.createElement('div');
      empty.style.cssText = 'padding:20px 14px;color:#555;font-size:11px';
      empty.textContent = 'No ' + TITLE.toLowerCase() + ' assets found.';
      _grid.appendChild(empty);
      return;
    }
    assets.forEach(function (asset) {
      var cell = document.createElement('div');
      cell.style.cssText = 'display:flex;flex-direction:column;gap:4px;cursor:pointer';
      cell.setAttribute('tabindex', '0');
      var img = document.createElement('img');
      img.src = asset.thumbnail_url || '';
      img.style.cssText = 'width:100%;aspect-ratio:1;object-fit:cover;background:#111';
      img.alt = asset.name || '';
      var label = document.createElement('div');
      label.textContent = asset.name || asset.id;
      label.style.cssText = 'font-size:10px;color:#888;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-family:Consolas,monospace';
      cell.appendChild(img); cell.appendChild(label);
      cell.addEventListener('click', function () { _openPrompt(asset); });
      _grid.appendChild(cell);
    });
  }

  function mount(slot) {
    var wrap = document.createElement('div'); wrap.className = 'list-panel';
    var bar = document.createElement('div'); bar.className = 'list-toolbar';
    var title = document.createElement('span'); title.className = 'panel-iframe-title'; title.textContent = TITLE;
    bar.appendChild(title);
    var grid = document.createElement('div');
    grid.style.cssText = 'flex:1;overflow-y:auto;padding:10px;display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:8px';
    _grid = grid;
    wrap.appendChild(bar); wrap.appendChild(grid);
    slot.replaceChildren(wrap);
    fetch('/api/assets?category=' + CATEGORY, { signal: AbortSignal.timeout(8000) })
      .then(function (r) { return r.ok ? r.json() : { assets: [] }; })
      .then(function (d) { _renderGrid(d.assets || []); })
      .catch(function () { _renderGrid([]); });
  }

  function unmount() {
    if (_overlay && _overlay.parentNode) { _overlay.parentNode.removeChild(_overlay); }
    _overlay = null;
    _grid = null;
  }

  global[GLOBAL] = { mount: mount, unmount: unmount };
}(window));
