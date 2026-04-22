/**
 * PANTHEON STUDIO — App Bootstrap
 * studio-app.js
 *
 * Runs on DOMContentLoaded. Wires up the UI to StudioStore.
 * Depends on studio-store.js being loaded first (window.StudioStore).
 */
(function () {
  'use strict';

  // ── Constants ──────────────────────────────────────────────────────────────

  var GLYPH_PLAY  = '\u25B6';     // ▶ BLACK RIGHT-POINTING TRIANGLE
  var GLYPH_PAUSE = '\u258C\u258C'; // two left half-blocks used as pause bars

  // ── Helpers ────────────────────────────────────────────────────────────────

  /**
   * Safe querySelector — returns null without throwing if id is missing.
   * @param {string} selector
   * @returns {Element|null}
   */
  function $(selector) {
    return document.querySelector(selector);
  }

  // ── Bootstrap ──────────────────────────────────────────────────────────────

  document.addEventListener('DOMContentLoaded', function () {
    var store = window.StudioStore;

    if (!store) {
      console.error('[studio-app] StudioStore not found — store script must load first.');
      return;
    }

    // ── 1. Fetch parts list and populate #part-select ────────────────────────
    fetch('/api/studio/parts')
      .then(function (res) {
        if (!res.ok) {
          throw new Error('HTTP ' + res.status);
        }
        return res.json();
      })
      .then(function (parts) {
        store.dispatch({ type: 'SET_PARTS', payload: parts });
        _populatePartSelect(parts);

        if (parts.length > 0) {
          store.dispatch({ type: 'SET_ACTIVE_PART', payload: parts[0].part });
          var sel = $('#part-select');
          if (sel) {
            sel.value = String(parts[0].part);
          }
        }
      })
      .catch(function (err) {
        console.error('[studio-app] Failed to load parts:', err);
        store.dispatch({ type: 'SET_STATUS_MSG', payload: 'Failed to load parts: ' + err.message });
      });

    // ── 2. Sidebar nav wiring ────────────────────────────────────────────────
    var navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(function (item) {
      item.addEventListener('click', function () {
        var page = item.getAttribute('data-page');
        if (!page) { return; }

        // Toggle .active class
        navItems.forEach(function (n) { n.classList.remove('active'); });
        item.classList.add('active');

        store.dispatch({ type: 'SET_ACTIVE_PAGE', page: page });
      });
    });

    // ── 3. Transport buttons ─────────────────────────────────────────────────
    var btnPlay = $('#btn-play');
    if (btnPlay) {
      btnPlay.addEventListener('click', function () {
        var isPlaying = store.getState().isPlaying;
        store.dispatch({ type: 'SET_PLAYING', payload: !isPlaying });
      });
    }

    var btnRew = $('#btn-rew');
    if (btnRew) {
      btnRew.addEventListener('click', function () {
        store.dispatch({ type: 'SET_CURRENT_TIME', payload: 0 });
      });
    }

    var btnFwd = $('#btn-fwd');
    if (btnFwd) {
      btnFwd.addEventListener('click', function (e) {
        e.preventDefault();
        // no-op for now
      });
    }

    // ── 4. Part selector ─────────────────────────────────────────────────────
    var partSelect = $('#part-select');
    if (partSelect) {
      partSelect.addEventListener('change', function () {
        var val = parseInt(partSelect.value, 10);
        if (!isNaN(val)) {
          store.dispatch({ type: 'SET_ACTIVE_PART', payload: val });
        }
      });
    }

    // ── 5. Rebuild button ────────────────────────────────────────────────────
    var btnRebuild = $('#btn-rebuild');
    if (btnRebuild) {
      btnRebuild.addEventListener('click', function () {
        var activePart = store.getState().activePart;
        store.dispatch({ type: 'SET_BUILD_STATUS', payload: 'building' });
        store.dispatch({ type: 'SET_STATUS_MSG',   payload: 'Building...' });

        fetch('/api/phase1/parts/' + activePart + '/rebuild', {
          method:  'POST',
          headers: { 'Content-Type': 'application/json' },
          body:    JSON.stringify({}),
        })
          .then(function (res) {
            if (!res.ok) {
              throw new Error('HTTP ' + res.status);
            }
            return res.json();
          })
          .then(function (data) {
            store.dispatch({ type: 'SET_BUILD_STATUS', payload: 'done' });
            store.dispatch({
              type:    'SET_STATUS_MSG',
              payload: data.message || 'Build complete.',
            });
          })
          .catch(function (err) {
            console.error('[studio-app] Rebuild failed:', err);
            store.dispatch({ type: 'SET_BUILD_STATUS', payload: 'error' });
            store.dispatch({ type: 'SET_STATUS_MSG',   payload: 'Build failed: ' + err.message });
          });
      });
    }

    // ── 6. Subscribe to store — keep statusbar and transport in sync ─────────
    store.subscribe(function (state) {
      var statusText = $('#status-text');
      if (statusText) {
        statusText.textContent = state.statusMessage;
      }

      // Sync play button label (textContent only — no untrusted data)
      if (btnPlay) {
        btnPlay.textContent = state.isPlaying ? GLYPH_PAUSE : GLYPH_PLAY;
        btnPlay.title       = state.isPlaying ? 'Pause' : 'Play';
      }
    });
  });

  // ── Private helpers ────────────────────────────────────────────────────────

  /**
   * Populate #part-select with options built from a parts array.
   * Clears existing options first. Uses createElement/replaceChildren — no
   * untrusted inner-HTML injection (Rule UI-1).
   * @param {Array<{part: number}>} parts
   */
  function _populatePartSelect(parts) {
    var sel = document.querySelector('#part-select');
    if (!sel) { return; }

    var fragment = document.createDocumentFragment();
    parts.forEach(function (p) {
      var opt         = document.createElement('option');
      opt.value       = String(p.part);
      opt.textContent = 'Part ' + p.part;
      fragment.appendChild(opt);
    });

    sel.replaceChildren(fragment);
  }

}());
