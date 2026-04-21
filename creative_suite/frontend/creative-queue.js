(function (global) {
  'use strict';
  var _grid = null, _poll = null, _inflight = false;

  function _fetchPending() {
    if (!_grid) return;
    if (_inflight) return;
    _inflight = true;
    fetch('/api/comfy/status', { signal: AbortSignal.timeout(5000) })
      .then(function (r) { return r.ok ? r.json() : { variants: [] }; })
      .then(function (d) {
        if (!_grid) return;
        var variants = d.variants || [];
        _grid.replaceChildren();
        if (!variants.length) {
          var empty = document.createElement('div');
          empty.style.cssText = 'padding:20px 14px;color:#555;font-size:11px';
          empty.textContent = 'No variants in queue.';
          _grid.appendChild(empty);
          return;
        }
        variants.forEach(function (v) {
          (function (vid, vstatus) {
            var cell = document.createElement('div');
            cell.style.cssText = 'display:flex;flex-direction:column;gap:6px;background:#111;padding:8px';
            var img = document.createElement('img');
            img.src = v.thumbnail_url || '';
            img.style.cssText = 'width:100%;aspect-ratio:1;object-fit:cover;background:#0a0a0a';
            img.alt = '';
            var statusDot = document.createElement('span');
            var dotColor = vstatus === 'approved' ? '#44bb44' : vstatus === 'rejected' ? '#c41515' : vstatus === 'running' ? '#e68a00' : '#888';
            statusDot.style.cssText = 'width:8px;height:8px;border-radius:50%;display:inline-block;background:' + dotColor;
            var btnRow = document.createElement('div'); btnRow.style.cssText = 'display:flex;gap:4px';
            var btnApprove = document.createElement('button'); btnApprove.className = 'panel-iframe-btn'; btnApprove.textContent = '\u2713';
            var btnReject = document.createElement('button'); btnReject.className = 'panel-iframe-btn'; btnReject.textContent = '\u2717';
            btnApprove.addEventListener('click', function () {
              fetch('/api/variants/' + vid, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: 'approved' }),
                signal: AbortSignal.timeout(5000)
              }).then(function () { _fetchPending(); }).catch(function () {});
            });
            btnReject.addEventListener('click', function () {
              fetch('/api/variants/' + vid, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: 'rejected' }),
                signal: AbortSignal.timeout(5000)
              }).then(function () { _fetchPending(); }).catch(function () {});
            });
            btnRow.appendChild(statusDot); btnRow.appendChild(btnApprove); btnRow.appendChild(btnReject);
            cell.appendChild(img); cell.appendChild(btnRow);
            _grid.appendChild(cell);
          }(v.id, v.status));
        });
      })
      .catch(function () {})
      .then(function () { _inflight = false; });
  }

  function mount(slot) {
    var wrap = document.createElement('div'); wrap.className = 'list-panel';
    var bar = document.createElement('div'); bar.className = 'list-toolbar';
    var title = document.createElement('span'); title.className = 'panel-iframe-title'; title.textContent = 'QUEUE';
    bar.appendChild(title);
    var grid = document.createElement('div');
    grid.style.cssText = 'flex:1;overflow-y:auto;padding:10px;display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:8px';
    _grid = grid;
    wrap.appendChild(bar); wrap.appendChild(grid);
    slot.replaceChildren(wrap);
    _fetchPending();
    _poll = setInterval(_fetchPending, 4000);
  }

  function unmount() {
    if (_poll !== null) { clearInterval(_poll); _poll = null; }
    _grid = null;
    _inflight = false;
  }

  global.CreativeQueue = { mount: mount, unmount: unmount };
}(window));
