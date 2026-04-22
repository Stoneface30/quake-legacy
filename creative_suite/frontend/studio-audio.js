/**
 * PANTHEON STUDIO — Audio Waveform Panel
 * studio-audio.js
 *
 * WaveSurfer v7 multitrack audio timeline for PANTHEON Studio.
 * Shows game audio + music track(s) for the active part.
 *
 * Exposed on: window.StudioAudio
 *
 * Depends on:
 *   window.StudioStore        (studio-store.js loaded first)
 *   window.Multitrack         (vendor/wavesurfer-multitrack.js loaded first)
 *
 * Vendor API notes (read from wavesurfer-multitrack.js):
 *   - globalThis.Multitrack is the class exposed by the multitrack vendor bundle.
 *   - Multitrack.create(tracks, options) is the factory method.
 *   - Tracks: [{ id, url, peaks, startPosition, options: {waveColor, height} }]
 *   - Options: { container, minPxPerSec, cursorColor, cursorWidth, trackBorderColor }
 *   - Instance methods: play(), pause(), seekTo(ratio), setTime(seconds),
 *                       zoom(pxPerSec), destroy(), isPlaying(), getCurrentTime()
 *
 * Rule UI-1: DOM built with createElement/textContent only (no raw injection).
 * Rule UI-2: all state from StudioStore — no local drift.
 */
(function (global) {
  'use strict';

  // ── Constants ────────────────────────────────────────────────────────────────

  /** PANTHEON gold — matches brand palette. */
  var CURSOR_COLOR = '#C9A84C';

  /** Accent orange — game audio track waveform. */
  var GAME_TRACK_COLOR = '#FF4500';

  /** Gold — music track waveform. */
  var MUSIC_TRACK_COLOR = '#C9A84C';

  /** Progress-bar colors (dimmed variants). */
  var GAME_PROGRESS_COLOR = 'rgba(255, 69, 0, 0.45)';
  var MUSIC_PROGRESS_COLOR = 'rgba(201, 168, 76, 0.45)';

  /** Default pixels-per-second zoom level. */
  var DEFAULT_ZOOM_PX = 50;

  /** Height (px) for each waveform track. */
  var TRACK_HEIGHT = 60;

  // ── Module-private state ─────────────────────────────────────────────────────

  /** @type {Element|null} Host container provided by caller. */
  var _container = null;

  /** @type {Element|null} Root panel element. */
  var _panelEl = null;

  /** @type {Element|null} .audio-tracks-wrap element. */
  var _tracksWrap = null;

  /** @type {Element|null} Track-count span. */
  var _trackCountEl = null;

  /** @type {object|null} Multitrack instance. */
  var _multitrack = null;

  /** @type {number} Current zoom level in pixels-per-second. */
  var _zoomPx = DEFAULT_ZOOM_PX;

  /** @type {Array} Loaded track descriptors [{url, label}]. */
  var _loadedUrls = [];

  /** @type {function|null} StudioStore unsubscribe handle. */
  var _unsubscribe = null;

  /** @type {Element|null} Browse modal backdrop. */
  var _browseModal = null;

  /** @type {Array} Full browse results cache. */
  var _browseCache = [];

  // ── DOM helpers ──────────────────────────────────────────────────────────────

  /**
   * Create an element, optionally set its textContent and class.
   * @param {string} tag
   * @param {string|null} [cls]
   * @param {string|null} [text]
   * @returns {Element}
   */
  function _el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls)  { node.className = cls; }
    if (text) { node.textContent = text; }
    return node;
  }

  // ── Panel construction ───────────────────────────────────────────────────────

  /**
   * Build the full panel DOM. Does NOT attach to the DOM yet.
   * @returns {Element} .audio-panel root
   */
  function _buildPanel() {
    var panel = _el('div', 'audio-panel');

    // ── Toolbar
    var toolbar = _el('div', 'audio-toolbar');

    var label = _el('span', 'audio-label', 'AUDIO TIMELINE');

    var btnZoomIn = _el('button', 'audio-btn');
    btnZoomIn.id = 'audio-btn-zoom-in';
    btnZoomIn.textContent = '+';
    btnZoomIn.addEventListener('click', function () {
      setZoom(_zoomPx * 1.5);
    });

    var btnZoomOut = _el('button', 'audio-btn');
    btnZoomOut.id = 'audio-btn-zoom-out';
    btnZoomOut.textContent = '-';
    btnZoomOut.addEventListener('click', function () {
      setZoom(_zoomPx / 1.5);
    });

    _trackCountEl = _el('span', 'audio-track-count', '0 tracks');

    var btnBrowse = _el('button', 'audio-btn audio-browse-btn');
    btnBrowse.textContent = 'BROWSE MUSIC';
    btnBrowse.addEventListener('click', _openBrowseModal);

    toolbar.appendChild(label);
    toolbar.appendChild(btnZoomIn);
    toolbar.appendChild(btnZoomOut);
    toolbar.appendChild(btnBrowse);
    toolbar.appendChild(_trackCountEl);

    // ── Tracks area
    _tracksWrap = _el('div', 'audio-tracks-wrap');

    panel.appendChild(toolbar);
    panel.appendChild(_tracksWrap);

    return panel;
  }

  // ── Multitrack helpers ────────────────────────────────────────────────────────

  /**
   * Destroy the existing Multitrack instance and clear the wrap element.
   */
  function _destroyMultitrack() {
    if (_multitrack) {
      try { _multitrack.destroy(); } catch (e) { /* ignore */ }
      _multitrack = null;
    }
    if (_tracksWrap) {
      // Remove all child nodes safely, one at a time
      while (_tracksWrap.firstChild) {
        _tracksWrap.removeChild(_tracksWrap.firstChild);
      }
    }
  }

  /**
   * Map a { url, label } descriptor to the Multitrack track format.
   * Track index 0 = game audio (orange), 1+ = music (gold).
   * @param {{ url: string, label: string }} descriptor
   * @param {number} index
   * @returns {object}
   */
  function _descriptorToTrack(descriptor, index) {
    var isGame = (index === 0);
    return {
      id: 'track-' + index,
      url: descriptor.url,
      startPosition: 0,
      options: {
        height: TRACK_HEIGHT,
        waveColor:     isGame ? GAME_TRACK_COLOR    : MUSIC_TRACK_COLOR,
        progressColor: isGame ? GAME_PROGRESS_COLOR : MUSIC_PROGRESS_COLOR,
      },
    };
  }

  /**
   * Show a graceful placeholder inside the tracks wrap.
   * @param {string} message
   */
  function _showPlaceholder(message) {
    _destroyMultitrack();
    var p = _el('p', 'audio-no-support', message);
    _tracksWrap.appendChild(p);
  }

  /**
   * Update the track-count label.
   * @param {number} count
   */
  function _updateTrackCount(count) {
    if (_trackCountEl) {
      _trackCountEl.textContent = count + ' track' + (count === 1 ? '' : 's');
    }
  }

  // ── Store subscription ────────────────────────────────────────────────────────

  /**
   * React to StudioStore state changes.
   * @param {object} state  Current state
   * @param {object} prev   Previous state
   */
  function _onStoreChange(state, prev) {
    // Play / pause synchronization
    if (state.isPlaying !== prev.isPlaying) {
      if (_multitrack) {
        if (state.isPlaying) {
          try { _multitrack.play(); } catch (e) { /* ignore if no audio loaded */ }
        } else {
          try { _multitrack.pause(); } catch (e) { /* ignore */ }
        }
      }
    }

    // Seek synchronization
    if (state.currentTime !== prev.currentTime && !state.isPlaying) {
      setPlayhead(state.currentTime);
    }
  }

  // ── Music browse modal ───────────────────────────────────────────────────────

  function _openBrowseModal() {
    if (_browseModal) return;

    _browseModal = _el('div', 'music-modal-backdrop');
    _browseModal.addEventListener('click', function (e) {
      if (e.target === _browseModal) _closeBrowseModal();
    });

    var dlg = _el('div', 'music-modal');

    // header
    var hdr = _el('div', 'music-modal-hdr');
    hdr.appendChild(_el('span', 'music-modal-title', 'MUSIC LIBRARY'));
    var closeBtn = _el('button', 'music-modal-close', '\u2715');
    closeBtn.addEventListener('click', _closeBrowseModal);
    hdr.appendChild(closeBtn);
    dlg.appendChild(hdr);

    // search
    var searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.className = 'music-modal-search';
    searchInput.placeholder = 'Filter artist / title…';
    dlg.appendChild(searchInput);

    // list
    var list = _el('div', 'music-modal-list');
    list.appendChild(_el('div', 'music-modal-loading', 'Loading…'));
    dlg.appendChild(list);

    _browseModal.appendChild(dlg);
    document.body.appendChild(_browseModal);

    searchInput.addEventListener('input', function () {
      _renderBrowseList(list, searchInput.value);
    });

    if (_browseCache.length) {
      _renderBrowseList(list, '');
    } else {
      fetch('/api/studio/music/browse', { signal: AbortSignal.timeout(8000) })
        .then(function (r) { return r.ok ? r.json() : []; })
        .then(function (tracks) {
          _browseCache = tracks || [];
          _renderBrowseList(list, searchInput.value);
        })
        .catch(function (e) {
          while (list.firstChild) list.removeChild(list.firstChild);
          list.appendChild(_el('div', 'music-modal-loading', 'Error: ' + e.message));
        });
    }
  }

  function _closeBrowseModal() {
    if (_browseModal && _browseModal.parentNode) {
      _browseModal.parentNode.removeChild(_browseModal);
    }
    _browseModal = null;
  }

  function _fmtDur(s) {
    if (s === null || s === undefined) return '';
    var n = Math.round(Number(s));
    var m = Math.floor(n / 60);
    var sec = n % 60;
    return m + ':' + (sec < 10 ? '0' : '') + sec;
  }

  function _renderBrowseList(listEl, query) {
    while (listEl.firstChild) listEl.removeChild(listEl.firstChild);

    var q = (query || '').toLowerCase();
    var filtered = _browseCache.filter(function (t) {
      if (!q) return true;
      return ((t.artist || '') + ' ' + (t.title || '')).toLowerCase().indexOf(q) !== -1;
    });

    if (!filtered.length) {
      listEl.appendChild(_el('div', 'music-modal-loading', filtered.length === 0 && _browseCache.length === 0 ? 'No tracks in library.' : 'No matches.'));
      return;
    }

    filtered.forEach(function (track) {
      var row = _el('div', 'music-track-row');

      var info = _el('div', 'music-track-info');
      var titleEl = _el('div', 'music-track-title', track.title || track.filename);
      var metaEl  = _el('div', 'music-track-meta',
        (track.artist ? track.artist + '  ·  ' : '') + _fmtDur(track.duration_s));
      info.appendChild(titleEl);
      info.appendChild(metaEl);
      row.appendChild(info);

      var addBtn = _el('button', 'music-add-btn', '+ ADD');
      addBtn.addEventListener('click', function () {
        var url = '/api/studio/music/file/' + encodeURIComponent(track.filename);
        _loadedUrls.push({ url: url, label: track.title || track.filename });
        loadAudio(_loadedUrls);
        addBtn.textContent = '✓';
        addBtn.disabled = true;
      });
      row.appendChild(addBtn);

      listEl.appendChild(row);
    });
  }

  // ── Public API ───────────────────────────────────────────────────────────────

  /**
   * Mount the audio panel into a container element.
   * Creates panel DOM and initialises the multitrack instance.
   * @param {Element} containerEl
   */
  function mount(containerEl) {
    if (_panelEl) {
      unmount();
    }

    _container = containerEl;
    _panelEl   = _buildPanel();
    _container.appendChild(_panelEl);

    // Subscribe to store (Rule UI-2)
    _unsubscribe = global.StudioStore.subscribe(_onStoreChange);

    // Check WaveSurfer / Multitrack availability
    if (typeof global.Multitrack === 'undefined') {
      _showPlaceholder('WaveSurfer not loaded');
      return;
    }

    // No URLs loaded yet — show waiting placeholder
    _showPlaceholder('No audio tracks loaded. Call loadAudio(urls) to populate.');
  }

  /**
   * Unmount: destroy the multitrack instance, remove DOM, unsubscribe from store.
   */
  function unmount() {
    _closeBrowseModal();
    _destroyMultitrack();

    if (_unsubscribe) {
      _unsubscribe();
      _unsubscribe = null;
    }

    if (_panelEl && _panelEl.parentNode) {
      _panelEl.parentNode.removeChild(_panelEl);
    }

    _panelEl       = null;
    _container     = null;
    _tracksWrap    = null;
    _trackCountEl  = null;
    _loadedUrls    = [];
  }

  /**
   * Load an array of { url, label } objects as separate waveform tracks.
   * An empty array or undefined shows a graceful placeholder.
   * @param {Array<{url: string, label: string}>} urls
   */
  function loadAudio(urls) {
    _destroyMultitrack();
    _loadedUrls = urls || [];

    if (!_tracksWrap) {
      return; // not mounted yet
    }

    // Graceful degradation: no Multitrack library
    if (typeof global.Multitrack === 'undefined') {
      _showPlaceholder('WaveSurfer not loaded');
      _updateTrackCount(0);
      return;
    }

    // Empty array — placeholder
    if (!_loadedUrls.length) {
      _showPlaceholder('No audio tracks loaded.');
      _updateTrackCount(0);
      return;
    }

    // Build Multitrack tracks array
    var tracks = _loadedUrls.map(function (desc, i) {
      return _descriptorToTrack(desc, i);
    });

    try {
      _multitrack = global.Multitrack.create(tracks, {
        container:       _tracksWrap,
        minPxPerSec:     _zoomPx,
        cursorColor:     CURSOR_COLOR,
        cursorWidth:     2,
        trackBorderColor: '#2A2A2A',
        trackBackground: '#141414',
      });

      _updateTrackCount(_loadedUrls.length);

      // Sync initial play state
      var state = global.StudioStore.getState();
      if (state.isPlaying) {
        try { _multitrack.play(); } catch (e) { /* ignore */ }
      }
    } catch (e) {
      console.error('[StudioAudio] Multitrack.create failed', e);
      _showPlaceholder('Audio timeline failed to initialise. See console.');
      _updateTrackCount(0);
    }
  }

  /**
   * Seek all tracks to a given position in seconds.
   * @param {number} seconds
   */
  function setPlayhead(seconds) {
    if (!_multitrack) { return; }
    try {
      _multitrack.setTime(seconds);
    } catch (e) { /* ignore: no audio loaded */ }
  }

  /**
   * Return the current zoom level in pixels-per-second.
   * @returns {number}
   */
  function getZoom() {
    return _zoomPx;
  }

  /**
   * Set the zoom level (pixels per second).
   * Clamped to [10, 500] to prevent runaway canvas allocation.
   * @param {number} pxPerSec
   */
  function setZoom(pxPerSec) {
    _zoomPx = Math.max(10, Math.min(500, pxPerSec));
    if (_multitrack) {
      try {
        _multitrack.zoom(_zoomPx);
      } catch (e) { /* ignore: no audio loaded */ }
    }
  }

  // ── Global export ─────────────────────────────────────────────────────────────

  global.StudioAudio = {
    mount:        mount,
    unmount:      unmount,
    loadAudio:    loadAudio,
    setPlayhead:  setPlayhead,
    getZoom:      getZoom,
    setZoom:      setZoom,
  };

}(typeof window !== 'undefined' ? window : this));
