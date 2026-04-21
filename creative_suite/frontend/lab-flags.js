(function (global) {
  'use strict';
  var _slot = null, _ollamaAvail = true;

  function _log(btn, msg) {
    var orig = btn.textContent;
    btn.textContent = msg;
    setTimeout(function () { btn.textContent = orig; }, 2000);
  }

  function _buildRow(clip) {
    var row = document.createElement('div'); row.className = 'list-row';
    var icn = document.createElement('span'); icn.textContent = '\u25c6'; icn.style.color = '#c9a84c';
    var body = document.createElement('div');
    var prim = document.createElement('div'); prim.className = 'r-primary'; prim.textContent = clip.id || clip.name || 'clip';
    var tag = document.createElement('div'); tag.className = 'r-sub'; tag.textContent = clip.tag || '(untagged)';
    body.appendChild(prim); body.appendChild(tag);
    var btn = document.createElement('button'); btn.className = 'panel-iframe-btn'; btn.textContent = 'SUGGEST';
    if (!_ollamaAvail) btn.disabled = true;
    btn.addEventListener('click', function () {
      if (!_ollamaAvail) return;
      btn.disabled = true;
      fetch('/api/ollama/suggest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ clip_id: clip.id }),
        signal: AbortSignal.timeout(15000)
      })
        .then(function (r) {
          if (r.status === 503) {
            _ollamaAvail = false;
            if (_slot) {
              _slot.querySelectorAll('.panel-iframe-btn').forEach(function (b) { b.disabled = true; });
              var notice = _slot.querySelector('[data-ollama-notice]');
              if (!notice) {
                notice = document.createElement('div');
                notice.setAttribute('data-ollama-notice', '1');
                notice.style.cssText = 'padding:6px 14px;font-size:11px;color:#888';
                notice.textContent = '(Ollama unavailable)';
                var bar = _slot.querySelector('.list-toolbar');
                if (bar && bar.parentNode) bar.parentNode.insertBefore(notice, bar.nextSibling);
              }
            }
            return Promise.reject('503');
          }
          return r.ok ? r.json() : Promise.reject(r.status);
        })
        .then(function (d) {
          tag.textContent = d.tag || d.suggestion || '(no tag)';
          btn.disabled = false;
        })
        .catch(function (e) {
          if (e !== '503') { _log(btn, 'ERR'); btn.disabled = false; }
        });
    });
    row.appendChild(icn); row.appendChild(body); row.appendChild(btn);
    return row;
  }

  function mount(slot) {
    _slot = slot;
    var wrap = document.createElement('div'); wrap.className = 'list-panel';
    var bar = document.createElement('div'); bar.className = 'list-toolbar';
    var title = document.createElement('span'); title.className = 'panel-iframe-title'; title.textContent = 'FLAGS';
    bar.appendChild(title);
    var scroll = document.createElement('div'); scroll.className = 'list-scroll';
    wrap.appendChild(bar); wrap.appendChild(scroll);
    slot.replaceChildren(wrap);
    fetch('/api/phase1/parts', { signal: AbortSignal.timeout(5000) })
      .then(function (r) { return r.ok ? r.json() : { parts: [] }; })
      .then(function (d) {
        var parts = d.parts || [];
        var clips = [];
        parts.forEach(function (p) {
          (p.clips || []).forEach(function (c) {
            clips.push({ id: c.id || (p.part + '_' + c.name), name: c.name || c.id, tag: c.tag || '' });
          });
        });
        if (!clips.length) {
          var empty = document.createElement('div');
          empty.style.cssText = 'padding:20px 14px;color:#555;font-size:11px';
          empty.textContent = 'No clips found. Run extraction first.';
          scroll.appendChild(empty);
          return;
        }
        clips.forEach(function (clip) { scroll.appendChild(_buildRow(clip)); });
      })
      .catch(function () {
        var err = document.createElement('div');
        err.style.cssText = 'padding:20px 14px;color:#555;font-size:11px';
        err.textContent = 'Could not load parts \u2014 run extraction first.';
        scroll.appendChild(err);
      });
  }

  function unmount() { _slot = null; }

  global.LabFlags = { mount: mount, unmount: unmount };
}(window));
