/**
 * PANTHEON STUDIO — Music Library Browser Panel
 * studio-musiclib.js
 *
 * Displays music tracks for the active part with match % colour coding.
 * Subscribes to StudioStore.activePart changes and fetches /api/studio/part/{n}/music.
 *
 * Exposed on: window.StudioMusicLib
 *
 * Depends on:
 *   window.StudioStore  (studio-store.js loaded first)
 *
 * Rule UI-1: DOM built with createElement/textContent only — no raw innerHTML with
 *            untrusted data.
 * Rule UI-2: all state flows from StudioStore — no local state drift.
 */
(function (global) {
  'use strict';

  // ── Private state ────────────────────────────────────────────────────────────

  /** @type {Element|null} */
  var _containerEl = null;

  /** @type {Element|null} */
  var _panelEl = null;

  /** @type {Element|null} */
  var _listEl = null;

  /** @type {Element|null} */
  var _countEl = null;

  /** @type {function(): void|null} unsubscribe from StudioStore */
  var _unsubscribe = null;

  /** @type {object|null} Currently selected track object */
  var _selectedTrack = null;

  // ── Helpers ──────────────────────────────────────────────────────────────────

  /**
   * Format seconds as M:SS.
   * @param {number|null} totalSeconds
   * @returns {string}
   */
  function _formatDuration(totalSeconds) {
    if (totalSeconds === null || totalSeconds === undefined) {
      return '--:--';
    }
    var s = Math.round(totalSeconds);
    var m = Math.floor(s / 60);
    var sec = s % 60;
    return m + ':' + (sec < 10 ? '0' : '') + sec;
  }

  /**
   * Return CSS color for a match percentage value.
   * >=90 → gold, 70-89 → yellow, <70 → muted grey, null → grey.
   * @param {number|null} pct
   * @returns {string}
   */
  function _matchColor(pct) {
    if (pct === null || pct === undefined) {
      return 'var(--text-secondary)';
    }
    if (pct >= 90) {
      return 'var(--gold)';
    }
    if (pct >= 70) {
      return '#FFD700';
    }
    return '#555555';
  }

  /**
   * Return role CSS class suffix for a role string.
   * @param {string} role
   * @returns {string}
   */
  function _roleClass(role) {
    if (role === 'intro') return 'ml-role-intro';
    if (role === 'outro') return 'ml-role-outro';
    return 'ml-role-main';
  }

  // ── DOM builders ─────────────────────────────────────────────────────────────

  /**
   * Build the root panel DOM and return it.  Called once during mount().
   * @returns {{ panelEl: Element, listEl: Element, countEl: Element }}
   */
  function _buildPanel() {
    var panel = document.createElement('div');
    panel.className = 'musiclib-panel';

    // Toolbar
    var toolbar = document.createElement('div');
    toolbar.className = 'ml-toolbar';

    var label = document.createElement('span');
    label.className = 'ml-label';
    label.textContent = 'MUSIC LIBRARY';

    var count = document.createElement('span');
    count.className = 'ml-track-count';
    count.textContent = '0 tracks';

    toolbar.appendChild(label);
    toolbar.appendChild(count);

    // Track list
    var list = document.createElement('div');
    list.className = 'ml-list';

    panel.appendChild(toolbar);
    panel.appendChild(list);

    return { panelEl: panel, listEl: list, countEl: count };
  }

  /**
   * Build a single track row element.
   * @param {object} track  track object from API
   * @returns {Element}
   */
  function _buildTrackRow(track) {
    var row = document.createElement('div');
    row.className = 'ml-track';
    row.setAttribute('data-filename', track.filename);

    // Role badge
    var role = document.createElement('span');
    role.className = 'ml-track-role ' + _roleClass(track.role);
    role.textContent = track.role.toUpperCase();

    // Track name
    var name = document.createElement('span');
    name.className = 'ml-track-name';
    name.textContent = track.filename;

    // Duration
    var dur = document.createElement('span');
    dur.className = 'ml-track-duration';
    dur.textContent = _formatDuration(track.duration_s);

    // Match %
    var match = document.createElement('span');
    match.className = 'ml-track-match';
    if (track.match_pct !== null && track.match_pct !== undefined) {
      match.textContent = Math.round(track.match_pct) + '%';
    } else {
      match.textContent = '--';
    }
    match.style.color = _matchColor(track.match_pct);

    row.appendChild(role);
    row.appendChild(name);
    row.appendChild(dur);
    row.appendChild(match);

    // Click → select
    row.addEventListener('click', function () {
      _selectTrack(row, track);
    });

    return row;
  }

  // ── Selection ─────────────────────────────────────────────────────────────────

  /**
   * Mark a row as selected and update _selectedTrack.
   * @param {Element} rowEl
   * @param {object} track
   */
  function _selectTrack(rowEl, track) {
    // Deselect previous
    if (_listEl) {
      var prev = _listEl.querySelector('[data-selected]');
      if (prev) {
        prev.removeAttribute('data-selected');
      }
    }
    rowEl.setAttribute('data-selected', '');
    _selectedTrack = track;
  }

  // ── Core API ─────────────────────────────────────────────────────────────────

  /**
   * Mount the music library panel into containerEl.
   * @param {Element} containerEl
   */
  function mount(containerEl) {
    if (_panelEl) {
      unmount();
    }

    _containerEl = containerEl;
    _selectedTrack = null;

    var els = _buildPanel();
    _panelEl = els.panelEl;
    _listEl = els.listEl;
    _countEl = els.countEl;

    _containerEl.appendChild(_panelEl);

    // Subscribe to store — react to activePart changes
    _unsubscribe = global.StudioStore.subscribe(function (state, prev) {
      if (state.activePart !== prev.activePart) {
        _onPartChange(state.activePart);
      }
    });

    // Load current part if already set
    var currentPart = global.StudioStore.getState().activePart;
    if (currentPart !== null && currentPart !== undefined) {
      _onPartChange(currentPart);
    }
  }

  /**
   * Unmount the panel and clean up listeners.
   */
  function unmount() {
    if (_unsubscribe) {
      _unsubscribe();
      _unsubscribe = null;
    }
    if (_panelEl && _panelEl.parentNode) {
      _panelEl.parentNode.removeChild(_panelEl);
    }
    _panelEl = null;
    _listEl = null;
    _countEl = null;
    _containerEl = null;
    _selectedTrack = null;
  }

  /**
   * Render a list of track objects into the panel.
   * @param {Array<object>} tracks
   */
  function loadTracks(tracks) {
    if (!_listEl) return;

    // Clear existing rows
    while (_listEl.firstChild) {
      _listEl.removeChild(_listEl.firstChild);
    }
    _selectedTrack = null;

    for (var i = 0; i < tracks.length; i++) {
      _listEl.appendChild(_buildTrackRow(tracks[i]));
    }

    if (_countEl) {
      _countEl.textContent = tracks.length + (tracks.length === 1 ? ' track' : ' tracks');
    }
  }

  /**
   * Return the currently selected track object, or null.
   * @returns {object|null}
   */
  function getSelectedTrack() {
    return _selectedTrack;
  }

  // ── Internal: react to part change ──────────────────────────────────────────

  /**
   * Fetch music tracks for a part number and render them.
   * @param {number} partNum
   */
  function _onPartChange(partNum) {
    if (!_listEl) return;

    fetch('/api/studio/part/' + partNum + '/music')
      .then(function (res) {
        if (!res.ok) {
          throw new Error('HTTP ' + res.status);
        }
        return res.json();
      })
      .then(function (data) {
        loadTracks(data.tracks || []);
      })
      .catch(function (err) {
        console.error('[StudioMusicLib] fetch failed', err);
        loadTracks([]);
        if (global.StudioStore) {
          global.StudioStore.dispatch({
            type: 'SET_STATUS_MSG',
            payload: 'Music library load failed: ' + err.message,
          });
        }
      });
  }

  // ── Expose public API ────────────────────────────────────────────────────────

  global.StudioMusicLib = {
    mount: mount,
    unmount: unmount,
    loadTracks: loadTracks,
    getSelectedTrack: getSelectedTrack,
  };

}(typeof window !== 'undefined' ? window : this));
