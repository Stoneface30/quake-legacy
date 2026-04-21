(function (global) {
  'use strict';
  var _slot = null;

  function mount(slot) {
    _slot = slot;
    var wrap = document.createElement('div'); wrap.className = 'panel-iframe-wrap';
    var bar = document.createElement('div'); bar.className = 'panel-iframe-toolbar';
    var title = document.createElement('span'); title.className = 'panel-iframe-title'; title.textContent = 'ENGINE GRAPH';
    var btnRebuild = document.createElement('button'); btnRebuild.className = 'panel-iframe-btn';
    btnRebuild.textContent = 'REBUILD';
    btnRebuild.addEventListener('click', function () {
      fetch('/api/engine/graphify', { method: 'POST', signal: AbortSignal.timeout(5000) })
        .then(function () { frame.src = frame.src; })
        .catch(function () {});
    });
    var btnFull = document.createElement('button'); btnFull.className = 'panel-iframe-btn';
    btnFull.textContent = 'OPEN FULL';
    btnFull.addEventListener('click', function () { window.open('/engine-graph/', '_blank'); });
    bar.appendChild(title); bar.appendChild(btnRebuild); bar.appendChild(btnFull);
    var frame = document.createElement('iframe'); frame.className = 'panel-iframe-frame';
    frame.src = '/engine-graph/';
    wrap.appendChild(bar); wrap.appendChild(frame);
    slot.replaceChildren(wrap);
  }

  function unmount() { _slot = null; }

  global.LabEngine = { mount: mount, unmount: unmount };
}(window));
