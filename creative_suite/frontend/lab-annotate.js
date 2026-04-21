(function (global) {
  'use strict';
  var _slot = null;

  function mount(slot) {
    _slot = slot;
    var wrap = document.createElement('div'); wrap.className = 'panel-iframe-wrap';
    var bar = document.createElement('div'); bar.className = 'panel-iframe-toolbar';
    var title = document.createElement('span'); title.className = 'panel-iframe-title'; title.textContent = 'ANNOTATE';
    var btnFull = document.createElement('button'); btnFull.className = 'panel-iframe-btn';
    btnFull.textContent = 'OPEN FULL';
    btnFull.addEventListener('click', function () { window.open('/annotate', '_blank'); });
    bar.appendChild(title); bar.appendChild(btnFull);
    var frame = document.createElement('iframe'); frame.className = 'panel-iframe-frame';
    frame.src = '/annotate';
    wrap.appendChild(bar); wrap.appendChild(frame);
    slot.replaceChildren(wrap);
  }

  function unmount() { _slot = null; }

  global.LabAnnotate = { mount: mount, unmount: unmount };
}(window));
