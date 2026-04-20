/**
 * PANTHEON STUDIO — Page Router
 * studio-pages.js
 *
 * Mounts / unmounts panel modules in #panel-slot based on the active page in
 * StudioStore. Wires the timeline→inspector clip-selection callback.
 *
 * Exposed on: window.StudioPages
 *
 * Depends on (must be loaded before this file):
 *   window.StudioStore     (studio-store.js)
 *   window.StudioPreview   (studio-preview.js)
 *   window.StudioTimeline  (studio-timeline.js)
 *   window.StudioAudio     (studio-audio.js)
 *   window.StudioEffects   (studio-litegraph.js)
 *   window.StudioInspector (studio-inspector.js)
 */
(function (global) {
  'use strict';

  // ── Page → panel module map ──────────────────────────────────────────────────
  // Lazy getters: panel globals are resolved at switch-time, not at parse-time,
  // so load order issues cannot bite us even if modules arrive later.

  var PAGE_MAP = {
    preview:   function () { return global.StudioPreview;   },
    timeline:  function () { return global.StudioTimeline;  },
    audio:     function () { return global.StudioAudio;     },
    effects:   function () { return global.StudioEffects;   },
    inspector: function () { return global.StudioInspector; },
  };

  // ── Private state ────────────────────────────────────────────────────────────

  /** @type {string|null} */
  var _currentPage  = null;

  /** @type {Object|null} The panel module that is currently mounted. */
  var _currentPanel = null;

  // ── Internal helpers ─────────────────────────────────────────────────────────

  /**
   * Unmount the active panel (if any) and clear #panel-slot.
   * Uses replaceChildren() — never innerHTML — per Rule UI-1.
   * @param {Element} slot
   */
  function _clearSlot(slot) {
    if (_currentPanel && typeof _currentPanel.unmount === 'function') {
      try {
        _currentPanel.unmount();
      } catch (e) {
        console.error('[StudioPages] unmount error for page', _currentPage, e);
      }
    }
    _currentPanel = null;
    slot.replaceChildren();
  }

  /**
   * Update the .active class on sidebar nav items to match newPage.
   * @param {string} newPage
   */
  function _syncNavActive(newPage) {
    var items = document.querySelectorAll('.nav-item');
    items.forEach(function (item) {
      if (item.getAttribute('data-page') === newPage) {
        item.classList.add('active');
      } else {
        item.classList.remove('active');
      }
    });
  }

  /**
   * Render a "panel not loaded" placeholder.
   * Uses createElement — no innerHTML per Rule UI-1.
   * @param {Element} slot
   * @param {string} page
   */
  function _showNotLoaded(slot, page) {
    var div = document.createElement('div');
    div.className = 'panel-not-loaded';
    div.textContent = 'Panel not loaded: ' + page;
    slot.replaceChildren(div);
  }

  /**
   * Switch to a new page: unmount current, mount new panel.
   * @param {string} page
   */
  function _switchPage(page) {
    if (page === _currentPage) { return; }

    var slot = document.getElementById('panel-slot');
    if (!slot) {
      console.error('[StudioPages] #panel-slot not found');
      return;
    }

    // 1. Tear down old panel
    _clearSlot(slot);
    _currentPage = page;

    // 2. Resolve the panel module for the requested page
    var getter = PAGE_MAP[page];
    if (!getter) {
      _showNotLoaded(slot, page);
      _syncNavActive(page);
      return;
    }

    var panel = getter();
    if (!panel || typeof panel.mount !== 'function') {
      _showNotLoaded(slot, page);
      _syncNavActive(page);
      return;
    }

    // 3. Mount the new panel
    try {
      panel.mount(slot);
      _currentPanel = panel;
    } catch (e) {
      console.error('[StudioPages] mount error for page', page, e);
      _showNotLoaded(slot, page);
    }

    // 4. Sync nav highlight
    _syncNavActive(page);
  }

  // ── Timeline → Inspector callback ────────────────────────────────────────────

  /**
   * Wire a store subscription so that whenever the timeline's selected clip
   * changes, StudioInspector.inspectClip() is called automatically.
   * This wiring is established once in init() and stays active for the session.
   */
  function _wireTimelineToInspector() {
    var store = global.StudioStore;
    if (!store) { return; }

    store.subscribe(function () {
      var timeline  = global.StudioTimeline;
      var inspector = global.StudioInspector;
      if (!timeline || !inspector) { return; }
      if (typeof timeline.getSelectedClip !== 'function') { return; }
      if (typeof inspector.inspectClip    !== 'function') { return; }

      var clip = timeline.getSelectedClip();
      if (clip) {
        try {
          inspector.inspectClip(clip);
        } catch (e) {
          console.error('[StudioPages] inspectClip error', e);
        }
      }
    });
  }

  // ── Public API ───────────────────────────────────────────────────────────────

  /**
   * Initialise the page router.
   * - Subscribes to StudioStore for activePage changes.
   * - Renders the current activePage immediately.
   * - Wires the timeline→inspector callback.
   */
  function init() {
    var store = global.StudioStore;
    if (!store) {
      console.error('[StudioPages] StudioStore not found — store script must load first.');
      return;
    }

    // Subscribe: respond to every future SET_ACTIVE_PAGE dispatch
    store.subscribe(function (state, prev) {
      if (state.activePage !== prev.activePage) {
        _switchPage(state.activePage);
      }
    });

    // Render the current page immediately (do not wait for the first change)
    var initialPage = store.getState().activePage || 'preview';
    _switchPage(initialPage);

    // Wire timeline selection → inspector
    _wireTimelineToInspector();
  }

  /**
   * Return the page string that is currently displayed.
   * @returns {string}
   */
  function getActivePage() {
    return (global.StudioStore && global.StudioStore.getState().activePage) || _currentPage || 'preview';
  }

  // ── Expose ───────────────────────────────────────────────────────────────────

  global.StudioPages = {
    init:          init,
    getActivePage: getActivePage,
  };

  // ── Auto-init ────────────────────────────────────────────────────────────────
  // Called once the DOM is ready so all other scripts have had a chance to run.

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      global.StudioPages.init();
    });
  } else {
    global.StudioPages.init();
  }

}(typeof window !== 'undefined' ? window : this));
