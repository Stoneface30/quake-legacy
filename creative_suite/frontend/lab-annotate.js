(function (global) {
  'use strict';
  var _frame = null;

  function mount(slot) {
    var wrap = document.createElement('div'); wrap.className = 'panel-iframe-wrap';
    var bar = document.createElement('div'); bar.className = 'panel-iframe-toolbar';
    var title = document.createElement('span'); title.className = 'panel-iframe-title'; title.textContent = 'ANNOTATE';
    var btnR = document.createElement('button'); btnR.className = 'panel-iframe-btn'; btnR.textContent = 'REFRESH';
    btnR.addEventListener('click', function () { if (_frame) { var s = _frame.src; _frame.src = ''; _frame.src = s; } });
    var btnO = document.createElement('button'); btnO.className = 'panel-iframe-btn'; btnO.textContent = 'OPEN FULL';
    btnO.addEventListener('click', function () { window.open('/annotate', '_blank'); });
    bar.appendChild(title); bar.appendChild(btnR); bar.appendChild(btnO);
    var frame = document.createElement('iframe'); frame.className = 'panel-iframe-frame';
    frame.src = '/web/annotate.html'; frame.title = 'Annotation Tool';
    _frame = frame;
    wrap.appendChild(bar); wrap.appendChild(frame);
    slot.replaceChildren(wrap);
  }

  function unmount() { _frame = null; }

  global.LabAnnotate = { mount: mount, unmount: unmount };
}(window));
