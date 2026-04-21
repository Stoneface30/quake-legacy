/**
 * PANTHEON STUDIO — EDIT Tab Wrapper
 * studio-edit.js
 *
 * Consolidates the five authoring panels into a single EDIT surface with a
 * horizontal secondary tab strip at the top:
 *   PREVIEW | TIMELINE | AUDIO | EFFECTS | INSPECTOR
 *
 * Each sub-panel is the existing window.Studio* module, mounted into an inner
 * slot.  Only one is alive at a time; switching unmounts the old and mounts
 * the new.
 *
 * Exposed on: window.StudioEdit
 * Depends on: window.StudioStore, window.StudioPreview, window.StudioTimeline,
 *             window.StudioAudio, window.StudioLiteGraph, window.StudioInspector
 *
 * Rule UI-1: DOM via createElement/textContent only.
 * Rule UI-2: state from StudioStore, no local drift.
 */
(function (global) {
  'use strict';

  var TABS = [
    { key: 'preview',   label: 'PREVIEW',   module: 'StudioPreview'   },
    { key: 'timeline',  label: 'TIMELINE',  module: 'StudioTimeline'  },
    { key: 'audio',     label: 'AUDIO',     module: 'StudioAudio'     },
    { key: 'effects',   label: 'FX GRAPH',  module: 'StudioLiteGraph' },
    { key: 'inspector', label: 'INSPECTOR', module: 'StudioInspector' },
  ];

  var _container    = null;
  var _innerSlot    = null;
  var _activeKey    = 'preview';
  var _currentPanel = null;

  function _mountTab(key) {
    if (!_innerSlot) return;

    // Unmount previous
    if (_currentPanel && typeof _currentPanel.unmount === 'function') {
      try { _currentPanel.unmount(); } catch (e) { console.error('[Edit] unmount', e); }
      _currentPanel = null;
    }

    _activeKey = key;

    // Update tab button styles
    if (_container) {
      var btns = _container.querySelectorAll('.se-tab-btn');
      for (var i = 0; i < btns.length; i++) {
        btns[i].classList.toggle('active', btns[i].getAttribute('data-key') === key);
      }
    }

    // Mount new panel
    var cfg = TABS.find(function (t) { return t.key === key; });
    if (!cfg) return;
    var mod = global[cfg.module];
    if (!mod || typeof mod.mount !== 'function') {
      _innerSlot.replaceChildren();
      var ph = document.createElement('div');
      ph.className = 'panel-not-loaded';
      ph.textContent = cfg.label + ' — module not loaded (' + cfg.module + ')';
      _innerSlot.appendChild(ph);
      return;
    }
    try {
      mod.mount(_innerSlot);
      _currentPanel = mod;
    } catch (e) {
      console.error('[Edit] mount error for ' + cfg.module, e);
      _innerSlot.replaceChildren();
      var errEl = document.createElement('div');
      errEl.className = 'panel-not-loaded';
      errEl.textContent = cfg.label + ' — mount error: ' + e.message;
      _innerSlot.appendChild(errEl);
    }
  }

  function mount(slot) {
    _container = document.createElement('div');
    _container.className = 'se-root';

    // Secondary tab strip
    var strip = document.createElement('div');
    strip.className = 'se-tab-strip';
    TABS.forEach(function (tab) {
      var btn = document.createElement('button');
      btn.className = 'se-tab-btn' + (tab.key === _activeKey ? ' active' : '');
      btn.setAttribute('data-key', tab.key);
      btn.textContent = tab.label;
      btn.addEventListener('click', function () { _mountTab(tab.key); });
      strip.appendChild(btn);
    });
    _container.appendChild(strip);

    // Inner panel slot
    _innerSlot = document.createElement('div');
    _innerSlot.className = 'se-inner-slot';
    _container.appendChild(_innerSlot);

    slot.replaceChildren(_container);

    // Mount active tab
    _mountTab(_activeKey);
  }

  function unmount() {
    if (_currentPanel && typeof _currentPanel.unmount === 'function') {
      try { _currentPanel.unmount(); } catch (e) { console.error('[Edit] unmount', e); }
      _currentPanel = null;
    }
    _container = null;
    _innerSlot = null;
  }

  global.StudioEdit = { mount: mount, unmount: unmount };
}(window));
