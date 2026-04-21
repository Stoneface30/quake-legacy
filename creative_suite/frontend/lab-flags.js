(function (global) {
  'use strict';
  var _slot = null;

  function mount(slot) {
    _slot = slot;
    var wrap = document.createElement('div'); wrap.className = 'list-panel';
    var bar = document.createElement('div'); bar.className = 'list-toolbar';
    var title = document.createElement('span'); title.className = 'panel-iframe-title'; title.textContent = 'FLAGS';
    bar.appendChild(title);
    var note = document.createElement('div');
    note.style.cssText = 'padding:20px 14px;color:#555;font-size:11px';
    note.textContent = 'AI event tagging via /api/ollama/suggest. Requires Ollama running locally.';
    wrap.appendChild(bar); wrap.appendChild(note);
    slot.replaceChildren(wrap);
  }

  function unmount() { _slot = null; }

  global.LabFlags = { mount: mount, unmount: unmount };
}(window));
