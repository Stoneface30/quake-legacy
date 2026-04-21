(function (global) {
  'use strict';

  var NAV = {
    studio: {
      label: 'Edit',
      groups: [
        { label: 'Edit flow', items: [
          { page: 'preview',   label: 'Preview',   icon: 'play',      module: 'StudioPreview'   },
          { page: 'timeline',  label: 'Timeline',  icon: 'timeline',  module: 'StudioTimeline'  },
          { page: 'audio',     label: 'Audio',     icon: 'wave',      module: 'StudioAudio'     },
          { page: 'effects',   label: 'Effects',   icon: 'bolt',      module: 'StudioEffects'   },
          { page: 'inspector', label: 'Inspector', icon: 'crosshair', module: 'StudioInspector' },
        ]},
      ],
    },
    lab: {
      groups: [
        { label: 'Intake', items: [
          { page: 'demos',      label: 'Demos',      icon: 'reel',  module: 'LabDemos'      },
          { page: 'extraction', label: 'Extraction', icon: 'clock', module: 'LabExtraction' },
        ]},
        { label: 'Discover', items: [
          { page: 'patterns',   label: 'Patterns',   icon: 'nodes', module: 'LabPatterns'   },
          { page: 'annotate',   label: 'Annotate',   icon: 'page',  module: 'LabAnnotate'   },
          { page: 'flags',      label: 'Flags',      icon: 'flag',  module: 'LabFlags'      },
        ]},
        { label: 'Engine', items: [
          { page: 'forge',      label: 'Forge',      icon: 'hex',   module: 'LabForge'      },
          { page: 'engine',     label: 'Graph',      icon: 'graph', module: 'LabEngine'     },
        ]},
      ],
    },
    creative: {
      groups: [
        { label: 'Generate', items: [
          { page: 'textures',   label: 'Textures',   icon: 'tile4',  module: 'CreativeTextures'  },
          { page: 'sprites',    label: 'Sprites',    icon: 'spark',  module: 'CreativeSprites'   },
          { page: 'skins',      label: 'Skins',      icon: 'figure', module: 'CreativeSkins'     },
          { page: 'maps',       label: 'Maps',       icon: 'map',    module: 'CreativeMaps'      },
        ]},
        { label: 'Inspect', items: [
          { page: 'md3',        label: 'MD3 Viewer', icon: 'cube',  module: 'CreativeMd3Viewer' },
          { page: 'prompts',    label: 'Prompts',    icon: 'quote', module: 'CreativePrompts'   },
        ]},
        { label: 'Build', items: [
          { page: 'queue',      label: 'Queue',      icon: 'queue', module: 'CreativeQueue'     },
          { page: 'packs',      label: 'Packs',      icon: 'box',   module: 'CreativePacks'     },
        ]},
      ],
    },
  };

  var ICONS = {
    play: '<polygon points="7 5 19 12 7 19"/>',
    timeline: '<rect x="3" y="8" width="18" height="8"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="9" y1="8" x2="9" y2="16"/><line x1="15" y1="8" x2="15" y2="16"/>',
    wave: '<path d="M3 12h3l3-7 3 14 3-7h6"/>',
    bolt: '<polyline points="13 3 5 14 12 14 11 21 19 10 12 10 13 3"/>',
    crosshair: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="3"/><line x1="12" y1="3" x2="12" y2="7"/><line x1="12" y1="17" x2="12" y2="21"/><line x1="3" y1="12" x2="7" y2="12"/><line x1="17" y1="12" x2="21" y2="12"/>',
    reel: '<path d="M3 7h18v10H3z"/><path d="M3 11h18"/><circle cx="7" cy="14" r="1"/>',
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 3v9l6 3"/>',
    nodes: '<circle cx="7" cy="7" r="3"/><circle cx="17" cy="7" r="3"/><circle cx="7" cy="17" r="3"/><circle cx="17" cy="17" r="3"/><line x1="10" y1="7" x2="14" y2="7"/><line x1="7" y1="10" x2="7" y2="14"/><line x1="10" y1="17" x2="14" y2="17"/><line x1="17" y1="10" x2="17" y2="14"/>',
    page: '<path d="M4 4h12l4 4v12H4z"/><line x1="8" y1="13" x2="16" y2="13"/><line x1="8" y1="17" x2="14" y2="17"/>',
    flag: '<path d="M5 3v18l7-5 7 5V3z"/>',
    hex: '<path d="M12 3l9 5v8l-9 5-9-5V8z"/><path d="M3 8l9 5 9-5"/><line x1="12" y1="13" x2="12" y2="21"/>',
    graph: '<circle cx="6" cy="6" r="2"/><circle cx="18" cy="6" r="2"/><circle cx="6" cy="18" r="2"/><circle cx="18" cy="18" r="2"/><circle cx="12" cy="12" r="2"/><line x1="7.5" y1="7.5" x2="10.5" y2="10.5"/><line x1="16.5" y1="7.5" x2="13.5" y2="10.5"/><line x1="7.5" y1="16.5" x2="10.5" y2="13.5"/><line x1="16.5" y1="16.5" x2="13.5" y2="13.5"/>',
    tile4: '<rect x="3" y="3" width="8" height="8"/><rect x="13" y="3" width="8" height="8"/><rect x="3" y="13" width="8" height="8"/><rect x="13" y="13" width="8" height="8"/>',
    spark: '<path d="M12 3v5M12 16v5M3 12h5M16 12h5M5.6 5.6l3.5 3.5M14.9 14.9l3.5 3.5M5.6 18.4l3.5-3.5M14.9 9.1l3.5-3.5"/>',
    figure: '<circle cx="12" cy="5" r="2.5"/><path d="M7 21v-7l-2-3M17 21v-7l2-3M10 13h4l-1 8h-2z"/>',
    map: '<polygon points="3 5 9 3 15 5 21 3 21 19 15 21 9 19 3 21 3 5"/><line x1="9" y1="3" x2="9" y2="19"/><line x1="15" y1="5" x2="15" y2="21"/>',
    cube: '<path d="M12 3l9 5v8l-9 5-9-5V8z"/><path d="M12 12l9-4M12 12l-9-4M12 12v9"/>',
    quote: '<path d="M7 7h4v4H7zM7 11c0 4 2 6 4 6M15 7h4v4h-4zM15 11c0 4 2 6 4 6"/>',
    queue: '<rect x="3" y="5" width="18" height="3"/><rect x="3" y="11" width="14" height="3"/><rect x="3" y="17" width="10" height="3"/>',
    box: '<path d="M3 7l9-4 9 4v10l-9 4-9-4V7z"/><path d="M3 7l9 4 9-4M12 11v10"/>',
  };

  var _currentPanel = null;
  var _currentKey   = null;

  function _renderSidebar(mode, activePage) {
    var container = document.getElementById('nav-list');
    if (!container) return;
    container.setAttribute('data-active-mode', mode);
    container.replaceChildren();
    var groups = (NAV[mode] || {}).groups || [];
    if (!groups.length) return;
    for (var i = 0; i < groups.length; i++) {
      var g = groups[i];
      var gEl = document.createElement('div');
      gEl.className = 'nav-group';
      var lbl = document.createElement('div');
      lbl.className = 'nav-group-label';
      lbl.textContent = g.label;
      gEl.appendChild(lbl);
      for (var j = 0; j < g.items.length; j++) {
        var it = g.items[j];
        var row = document.createElement('div');
        row.className = 'nav-item' + (it.page === activePage ? ' active' : '');
        row.setAttribute('data-page', it.page);
        row.setAttribute('data-mode', mode);
        row.setAttribute('role', 'button');
        row.setAttribute('tabindex', '0');
        var icn = document.createElement('span');
        icn.className = 'nav-icon';
        icn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7">' + (ICONS[it.icon] || '') + '</svg>';
        var lab = document.createElement('span');
        lab.className = 'nav-label';
        lab.textContent = it.label;
        row.appendChild(icn); row.appendChild(lab);
        gEl.appendChild(row);
      }
      container.appendChild(gEl);
    }
  }

  function _switch(mode, page) {
    var key = mode + ':' + page;
    if (key === _currentKey) return;
    var slot = document.getElementById('panel-slot');
    if (!slot) return;

    if (_currentPanel && typeof _currentPanel.unmount === 'function') {
      try { _currentPanel.unmount(); } catch (e) { console.error('[Pages] unmount', e); }
    }
    _currentPanel = null;
    slot.replaceChildren();

    var cfg = _lookup(mode, page);
    if (!cfg) { _placeholder(slot, page); _currentKey = key; return; }
    var mod = global[cfg.module];
    if (!mod || typeof mod.mount !== 'function') { _placeholder(slot, page); _currentKey = key; return; }

    try { mod.mount(slot); _currentPanel = mod; }
    catch (e) { console.error('[Pages] mount', e); _placeholder(slot, page); }

    _currentKey = key;
    _syncStatusChip(mode);
  }

  function _lookup(mode, page) {
    var groups = (NAV[mode] || {}).groups || [];
    for (var i = 0; i < groups.length; i++)
      for (var j = 0; j < groups[i].items.length; j++)
        if (groups[i].items[j].page === page) return groups[i].items[j];
    return null;
  }

  function _placeholder(slot, page) {
    var d = document.createElement('div');
    d.className = 'panel-not-loaded';
    d.textContent = 'Panel not loaded: ' + page;
    slot.replaceChildren(d);
  }

  function _syncStatusChip(mode) {
    var el = document.getElementById('status-mode-chip');
    if (!el) return;
    el.className = 'status-mode ' + mode;
    el.textContent = mode.toUpperCase();
  }

  function _syncUrl(mode, page) {
    var u = new URL(window.location.href);
    u.searchParams.set('mode', mode);
    u.searchParams.set('page', page);
    window.history.replaceState(null, '', u.toString());
  }

  function _readUrl() {
    var u = new URL(window.location.href);
    return { mode: u.searchParams.get('mode'), page: u.searchParams.get('page') };
  }

  function _wire() {
    document.querySelectorAll('#mode-switch .mode-btn').forEach(function (b) {
      b.addEventListener('click', function () {
        var m = b.getAttribute('data-mode');
        global.StudioStore.dispatch({ type: 'SET_ACTIVE_MODE', mode: m });
        document.querySelectorAll('#mode-switch .mode-btn').forEach(function (x) {
          x.classList.toggle('active', x === b);
          x.setAttribute('aria-selected', x === b ? 'true' : 'false');
        });
      });
    });

    var sidebar = document.getElementById('sidebar');
    if (sidebar) {
      sidebar.addEventListener('click', function (e) {
        var item = e.target.closest('.nav-item'); if (!item) return;
        var page = item.getAttribute('data-page');
        global.StudioStore.dispatch({ type: 'SET_ACTIVE_PAGE', page: page });
      });
      sidebar.addEventListener('keydown', function (e) {
        if (e.key !== 'Enter' && e.key !== ' ') return;
        var item = e.target.closest('.nav-item'); if (!item) return;
        e.preventDefault();
        var page = item.getAttribute('data-page');
        global.StudioStore.dispatch({ type: 'SET_ACTIVE_PAGE', page: page });
      });
    }
  }

  function init() {
    var store = global.StudioStore;
    if (!store) { console.error('[Pages] no StudioStore'); return; }

    var st = store.getState();
    var q = _readUrl();
    if (q.mode && NAV[q.mode]) store.dispatch({ type: 'SET_ACTIVE_MODE', mode: q.mode });
    if (q.page && _lookup(q.mode && NAV[q.mode] ? q.mode : st.activeMode, q.page)) {
      store.dispatch({ type: 'SET_ACTIVE_PAGE', page: q.page });
    }

    _wire();

    store.subscribe(function (s, p) {
      if (s.activeMode !== p.activeMode) {
        _renderSidebar(s.activeMode, s.activePage);
        document.querySelectorAll('#mode-switch .mode-btn').forEach(function (b) {
          b.classList.toggle('active', b.getAttribute('data-mode') === s.activeMode);
        });
      }
      if (s.activePage !== p.activePage || s.activeMode !== p.activeMode) {
        _syncActive(s.activePage);
        _switch(s.activeMode, s.activePage);
        _syncUrl(s.activeMode, s.activePage);
      }
    });

    _renderSidebar(st.activeMode, st.activePage);
    _switch(st.activeMode, st.activePage);
    _syncUrl(st.activeMode, st.activePage);
  }

  function _syncActive(page) {
    document.querySelectorAll('#nav-list .nav-item').forEach(function (it) {
      it.classList.toggle('active', it.getAttribute('data-page') === page);
    });
  }

  global.StudioPages = { init: init };

  if (document.readyState === 'loading')
    document.addEventListener('DOMContentLoaded', init);
  else
    init();

}(window));