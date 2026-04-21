(function (global) {
  'use strict';

  var _slot = null;

  function mount(slot) {
    _slot = slot;
    var wrap = document.createElement('div');
    wrap.className = 'panel-stub';
    var h = document.createElement('h2');
    h.textContent = 'Preview';
    wrap.appendChild(h);
    var p = document.createElement('p');
    p.textContent = 'Coming soon';
    wrap.appendChild(p);
    slot.replaceChildren(wrap);
  }

  function unmount() {
    if (_slot) { _slot.replaceChildren(); _slot = null; }
  }

  global.StudioPreview = { mount: mount, unmount: unmount };
}(window));
