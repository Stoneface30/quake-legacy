/**
 * PANTHEON STUDIO — Inspector Panel
 * studio-inspector.js
 *
 * Properties inspector for the currently selected clip.  Renders editable
 * clip metadata + override parameters via Tweakpane 4.x, with an optional
 * Theatre.js Core animation timeline when available.
 *
 * Exposed on: window.StudioInspector
 *
 * Depends on:
 *   window.StudioStore        (studio-store.js loaded first)
 *   window.Pane               (vendor/tweakpane.js — ES-module export; may be
 *                              undefined when loaded as a classic <script>)
 *   window.Theatre            (vendor/theatre-core-studio.js)
 *                              The bundle sets window.Theatre = { core, studio }
 *                              We use Theatre.core only (Apache-2.0).
 *
 * Vendor API notes (discovered by reading vendor files):
 *   Tweakpane 4.0.5 — ES-module file, exports { Pane, FolderApi, … } via
 *     `export {}` at EOF.  When loaded as a classic <script> tag the named
 *     exports are NOT placed on window.  Check window.Pane as the canonical
 *     guard; fall back to a placeholder div when unavailable.
 *
 *   Theatre.js — IIFE bundle; sets:
 *     window.Theatre = { core: <@theatre/core API>, studio: <@theatre/studio> }
 *     @theatre/core API: getProject(name) → Project
 *       project.sheet(name)  → Sheet
 *       sheet.object(key, { props }) → SheetObject (animatable)
 *     ONLY core is used here; studio UI is never initialised (AGPL concern).
 *
 * Rule UI-1: DOM built with createElement / textContent only (no raw injection).
 * Rule UI-2: all state from StudioStore — no local drift.
 */
(function (global) {
  'use strict';

  // ── Tweakpane availability guard ────────────────────────────────────────────
  //
  // tweakpane.js is a pure ES-module bundle (ends with `export { Pane, … }`).
  // When included via <script src> in a classic HTML page the export statement
  // is silently ignored — no global is set.  We therefore check for Pane on
  // window (some bundlers do assign it) and, if missing, degrade gracefully.

  function getTweakpanePane() {
    // Primary: explicit window.Tweakpane namespace (some CDN builds)
    if (typeof global.Tweakpane !== 'undefined' && global.Tweakpane.Pane) {
      return global.Tweakpane.Pane;
    }
    // Secondary: Pane placed directly on window (some bundler outputs)
    if (typeof global.Pane !== 'undefined') {
      return global.Pane;
    }
    return null;
  }

  // ── Theatre.js Core availability guard ─────────────────────────────────────
  //
  // The vendor bundle (theatre-core-studio.js) is an IIFE that ends with:
  //   window.Theatre = { core: src_exports, studio: src_default }
  // We only use `core` to avoid AGPL surface of the studio package.

  function getTheatreCore() {
    if (
      typeof global.Theatre !== 'undefined' &&
      global.Theatre !== null &&
      typeof global.Theatre.core !== 'undefined'
    ) {
      return global.Theatre.core;
    }
    return null;
  }

  // ── Module-private state ────────────────────────────────────────────────────

  /** @type {Element|null} Outer container passed to mount(). */
  var _container = null;

  /** @type {Element|null} Root panel element. */
  var _panelEl = null;

  /** @type {Element|null} Toolbar clip-name label. */
  var _clipNameEl = null;

  /** @type {Element|null} Tweakpane wrapper div. */
  var _paneWrapEl = null;

  /** @type {Element|null} Theatre.js wrapper div. */
  var _animWrapEl = null;

  /** @type {object|null} Tweakpane Pane instance. */
  var _pane = null;

  /** @type {object|null} Current clip being inspected. */
  var _currentClip = null;

  /** @type {object} Editable values object (Tweakpane binds to this). */
  var _values = {
    path:      '',
    tier:      '',
    is_fl:     false,
    head_trim: 0.0,
    tail_trim: 0.0,
    slow_rate: 1.0,
  };

  /** @type {function|null} StudioStore unsubscribe handle. */
  var _unsubscribe = null;

  /** @type {object|null} Theatre.js Project instance. */
  var _theatreProject = null;

  /** @type {object|null} Theatre.js Sheet instance. */
  var _theatreSheet = null;

  /** @type {object|null} Theatre.js SheetObject for current clip. */
  var _theatreObj = null;

  // ── Tweakpane helpers ───────────────────────────────────────────────────────

  /**
   * Destroy the current Tweakpane pane if one exists.
   */
  function _destroyPane() {
    if (_pane) {
      try { _pane.dispose(); } catch (e) { /* already disposed */ }
      _pane = null;
    }
  }

  /**
   * Build (or rebuild) the Tweakpane pane inside _paneWrapEl.
   * Caller is responsible for ensuring _paneWrapEl is non-null.
   */
  function _buildPane() {
    _destroyPane();

    var PaneClass = getTweakpanePane();

    if (!PaneClass) {
      // Tweakpane not available — show a plain text placeholder
      var notice = document.createElement('p');
      notice.textContent = 'Tweakpane not available (vendor not loaded as module)';
      notice.style.cssText = 'color:#888;font-size:11px;padding:8px;margin:0;';
      // Clear previous children safely
      while (_paneWrapEl.firstChild) {
        _paneWrapEl.removeChild(_paneWrapEl.firstChild);
      }
      _paneWrapEl.appendChild(notice);
      return;
    }

    // Clear previous children
    while (_paneWrapEl.firstChild) {
      _paneWrapEl.removeChild(_paneWrapEl.firstChild);
    }

    // Create Tweakpane pane bound to our wrapper element
    _pane = new PaneClass({ container: _paneWrapEl });

    // ── Folder: CLIP INFO (read-only monitors) ──────────────────────────────
    var infoFolder = _pane.addFolder({ title: 'CLIP INFO', expanded: true });

    infoFolder.addBinding(_values, 'path', {
      label: 'path',
      readonly: true,
    });

    infoFolder.addBinding(_values, 'tier', {
      label: 'tier',
      readonly: true,
    });

    infoFolder.addBinding(_values, 'is_fl', {
      label: 'is_fl',
      readonly: true,
    });

    // ── Folder: OVERRIDES (editable) ────────────────────────────────────────
    var overrideFolder = _pane.addFolder({ title: 'OVERRIDES', expanded: true });

    overrideFolder.addBinding(_values, 'head_trim', {
      label: 'head_trim',
      min: 0,
      max: 10,
      step: 0.1,
    });

    overrideFolder.addBinding(_values, 'tail_trim', {
      label: 'tail_trim',
      min: 0,
      max: 10,
      step: 0.1,
    });

    overrideFolder.addBinding(_values, 'slow_rate', {
      label: 'slow_rate',
      min: 0.1,
      max: 2.0,
      step: 0.1,
    });
  }

  // ── Theatre.js helpers ──────────────────────────────────────────────────────

  /**
   * Initialise a Theatre.js sheet object for the given clip.
   * No-ops silently when Theatre.core is unavailable.
   * Uses @theatre/core only — studio UI is never initialised.
   *
   * @param {object} clip
   */
  function _initTheatreObject(clip) {
    if (_theatreObj) {
      try { _theatreObj.detachFromParent && _theatreObj.detachFromParent(); } catch (e) { /* ignore */ }
      _theatreObj = null;
    }

    var TheatreCore = getTheatreCore();
    if (!TheatreCore) { return; }

    try {
      if (!_theatreProject) {
        _theatreProject = TheatreCore.getProject('PantheonStudio');
      }
      if (!_theatreSheet) {
        _theatreSheet = _theatreProject.sheet('ClipInspector');
      }

      // Create a sheet object whose props mirror the editable overrides.
      // The key is per-clip so each clip gets its own animation track.
      var clipKey = 'clip_' + (clip.path || 'unknown').replace(/[^a-zA-Z0-9_]/g, '_');

      _theatreObj = _theatreSheet.object(clipKey, {
        head_trim: _values.head_trim,
        tail_trim: _values.tail_trim,
        slow_rate: _values.slow_rate,
      });

      // Show the animation wrapper
      if (_animWrapEl) {
        var label = document.createElement('p');
        label.textContent = 'Theatre.js: ' + clipKey;
        label.style.cssText = 'color:#C9A84C;font-size:10px;padding:6px 8px;margin:0;';
        while (_animWrapEl.firstChild) {
          _animWrapEl.removeChild(_animWrapEl.firstChild);
        }
        _animWrapEl.appendChild(label);
      }
    } catch (e) {
      console.warn('[StudioInspector] Theatre.js init error:', e);
    }
  }

  // ── DOM construction ────────────────────────────────────────────────────────

  /**
   * Build the inspector panel DOM tree and append to container.
   * All nodes created with createElement; no raw string injection.
   */
  function _buildDom(containerEl) {
    // Outer panel
    var panel = document.createElement('div');
    panel.className = 'inspector-panel';

    // ── Toolbar ──────────────────────────────────────────────────────────────
    var toolbar = document.createElement('div');
    toolbar.className = 'inspector-toolbar';

    var labelSpan = document.createElement('span');
    labelSpan.className = 'inspector-label';
    labelSpan.textContent = 'INSPECTOR';

    var clipNameSpan = document.createElement('span');
    clipNameSpan.className = 'inspector-clip-name';
    clipNameSpan.textContent = 'No clip selected';

    toolbar.appendChild(labelSpan);
    toolbar.appendChild(clipNameSpan);
    panel.appendChild(toolbar);

    // ── Pane wrapper ──────────────────────────────────────────────────────────
    var paneWrap = document.createElement('div');
    paneWrap.className = 'inspector-pane-wrap';
    panel.appendChild(paneWrap);

    // ── Animation wrapper ─────────────────────────────────────────────────────
    var animWrap = document.createElement('div');
    animWrap.className = 'inspector-anim-wrap';
    panel.appendChild(animWrap);

    containerEl.appendChild(panel);

    _panelEl    = panel;
    _clipNameEl = clipNameSpan;
    _paneWrapEl = paneWrap;
    _animWrapEl = animWrap;
  }

  // ── Store subscription ──────────────────────────────────────────────────────

  /**
   * Subscribe to StudioStore.  When clips array changes and we have a currently
   * inspected clip, refresh its display (covers metadata updates from API).
   */
  function _subscribeStore() {
    if (!global.StudioStore) { return; }

    _unsubscribe = global.StudioStore.subscribe(function (state, prev) {
      if (_currentClip === null) { return; }
      if (state.clips === prev.clips) { return; }

      // Find updated clip by path
      var updatedClip = null;
      for (var i = 0; i < state.clips.length; i++) {
        if (state.clips[i].path === _currentClip.path) {
          updatedClip = state.clips[i];
          break;
        }
      }
      if (updatedClip) {
        StudioInspector.inspectClip(updatedClip);
      }
    });
  }

  // ── Public API ──────────────────────────────────────────────────────────────

  var StudioInspector = {

    /**
     * Create the inspector panel inside containerEl and initialise Tweakpane.
     * @param {Element} containerEl
     */
    mount: function (containerEl) {
      if (_panelEl) { this.unmount(); }
      _container = containerEl;

      _buildDom(containerEl);
      _buildPane();
      _subscribeStore();
    },

    /**
     * Destroy the pane, remove the panel DOM, and unsubscribe from the store.
     */
    unmount: function () {
      _destroyPane();

      if (_unsubscribe) {
        _unsubscribe();
        _unsubscribe = null;
      }

      if (_panelEl && _panelEl.parentNode) {
        _panelEl.parentNode.removeChild(_panelEl);
      }

      _panelEl    = null;
      _clipNameEl = null;
      _paneWrapEl = null;
      _animWrapEl = null;
      _container  = null;
      _currentClip = null;
      if (_theatreObj) {
        try { _theatreObj.detachFromParent && _theatreObj.detachFromParent(); } catch (e) {}
        _theatreObj = null;
      }
    },

    /**
     * Populate the inspector with properties from the given clip object.
     * @param {object} clip  — { path, tier, is_fl, … }
     */
    inspectClip: function (clip) {
      if (!clip) { return; }
      _currentClip = clip;

      // Update toolbar label
      if (_clipNameEl) {
        var name = clip.path ? clip.path.split('/').pop() : 'unnamed';
        _clipNameEl.textContent = name;
      }

      // Sync _values from clip
      _values.path    = clip.path  || '';
      _values.tier    = clip.tier  || '';
      _values.is_fl   = clip.is_fl || false;

      // Preserve user-edited override values on re-inspect of same clip;
      // reset to clip overrides if provided, otherwise keep current values.
      _values.head_trim = (clip.head_trim !== undefined) ? clip.head_trim : _values.head_trim;
      _values.tail_trim = (clip.tail_trim !== undefined) ? clip.tail_trim : _values.tail_trim;
      _values.slow_rate = (clip.slow_rate !== undefined) ? clip.slow_rate : _values.slow_rate;

      // Rebuild pane so monitors reflect new values
      if (_paneWrapEl) { _buildPane(); }

      // Theatre.js sheet object for animation
      _initTheatreObject(clip);
    },

    /**
     * Add one Tweakpane folder per effect in the chain.
     * @param {Array<{name: string, [prop: string]: any}>} effectChain
     */
    inspectEffects: function (effectChain) {
      if (!_pane || !effectChain || !effectChain.length) { return; }

      for (var i = 0; i < effectChain.length; i++) {
        var effect = effectChain[i];
        if (!effect || typeof effect !== 'object') { continue; }

        var title = effect.name || ('Effect ' + (i + 1));
        var folder = _pane.addFolder({ title: title, expanded: false });

        // Add each numeric/boolean/string prop as a binding
        var effectValues = {};
        var keys = Object.keys(effect);
        for (var k = 0; k < keys.length; k++) {
          var key = keys[k];
          if (key === 'name') { continue; }
          effectValues[key] = effect[key];
          try {
            folder.addBinding(effectValues, key, { label: key });
          } catch (e) {
            // addBinding may reject unsupported types — skip silently
          }
        }
      }
    },

    /**
     * Return a plain-object snapshot of the current pane values.
     * @returns {object}
     */
    getValues: function () {
      return {
        path:      _values.path,
        tier:      _values.tier,
        is_fl:     _values.is_fl,
        head_trim: _values.head_trim,
        tail_trim: _values.tail_trim,
        slow_rate: _values.slow_rate,
      };
    },
  };

  // Expose globally
  global.StudioInspector = StudioInspector;

}(typeof window !== 'undefined' ? window : this));
