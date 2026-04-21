(function (global) {
  'use strict';

  function mount(slot) {
    var wrap = document.createElement('div'); wrap.className = 'panel-iframe-wrap';
    var bar = document.createElement('div'); bar.className = 'panel-iframe-toolbar';
    var title = document.createElement('span'); title.className = 'panel-iframe-title'; title.textContent = 'ENGINE GRAPH';
    var btnFull = document.createElement('button'); btnFull.className = 'panel-iframe-btn'; btnFull.textContent = 'OPEN FULL';
    btnFull.addEventListener('click', function () { window.open('/engine-graph/', '_blank'); });
    bar.appendChild(title); bar.appendChild(btnFull);
    var frame = document.createElement('iframe'); frame.className = 'panel-iframe-frame';
    frame.src = '/engine-graph/';
    frame.addEventListener('error', function () {
      var d = document.createElement('div');
      d.style.cssText = 'padding:24px;color:#555;font-family:monospace;font-size:11px';
      d.textContent = 'Engine graph not generated yet \u2014 run graphify on the engine source trees to populate engine/graphify-out/.';
      if (wrap.contains(frame)) wrap.replaceChild(d, frame);
    });
    wrap.appendChild(bar); wrap.appendChild(frame);
    slot.replaceChildren(wrap);
  }

  function unmount() {}

  global.LabEngine = { mount: mount, unmount: unmount };
}(window));
