(function (global) {
  'use strict';
  var _slot = null;

  function mount(slot) {
    _slot = slot;
    var wrap = document.createElement('div'); wrap.className = 'list-panel';
    var bar = document.createElement('div'); bar.className = 'list-toolbar';
    var title = document.createElement('span'); title.className = 'panel-iframe-title'; title.textContent = 'PATTERNS';
    bar.appendChild(title);
    var note = document.createElement('div');
    note.style.cssText = 'padding:20px 14px;color:#555;font-size:11px';
    note.textContent = 'Requires demo parser output (event_diversity.json). Run extraction on demos first.';
    wrap.appendChild(bar); wrap.appendChild(note);
    slot.replaceChildren(wrap);
  }

  function unmount() { _slot = null; }

  global.LabPatterns = { mount: mount, unmount: unmount };
}(window));
