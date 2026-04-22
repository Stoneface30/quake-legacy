/**
 * PANTHEON STUDIO — WebCodecs Preview Panel
 * studio-preview.js
 *
 * Browser-only video preview panel.  Uses mp4box.js for MP4 demuxing and the
 * WebCodecs API (VideoDecoder) for frame decoding onto a canvas.
 *
 * Gracefully degrades when VideoDecoder is not available — the canvas shows a
 * "no preview" state with a text message.
 *
 * Depends on:
 *   window.StudioStore  (studio-store.js, loaded first)
 *
 * Exposes:
 *   window.StudioPreview
 */
(function (global) {
  'use strict';

  // ── Frame-cache limits (Rule UI-3) ─────────────────────────────────────────

  var FRAME_CACHE_MAX = 500;

  // ── Internal state ─────────────────────────────────────────────────────────

  /** @type {HTMLDivElement|null} */
  var _container = null;

  /** @type {HTMLCanvasElement|null} */
  var _canvas = null;

  /** @type {HTMLVideoElement|null} */
  var _video = null;

  /** @type {CanvasRenderingContext2D|null} */
  var _ctx = null;

  /** @type {HTMLInputElement|null} */
  var _scrub = null;

  /** @type {HTMLSpanElement|null} */
  var _timecodeEl = null;

  /** @type {HTMLSpanElement|null} */
  var _clipNameEl = null;

  /** @type {HTMLSpanElement|null} */
  var _partLabelEl = null;

  /** @type {HTMLSpanElement|null} */
  var _clipCountEl = null;

  /** @type {HTMLSpanElement|null} */
  var _durationEl = null;

  /** @type {function(): void} unsubscribe from StudioStore */
  var _storeUnsub = null;

  /** @type {boolean} */
  var _isPlaying = false;

  /** @type {number} */
  var _currentTime = 0;

  /** @type {number} */
  var _duration = 0;

  /** @type {number|null} */
  var _activePart = null;

  /** @type {Array} */
  var _clips = [];

  /** @type {number|null} requestAnimationFrame handle */
  var _rafHandle = null;

  /** @type {number|null} timestamp of last rAF call */
  var _rafLastTs = null;

  /** @type {VideoDecoder|null} */
  var _decoder = null;

  /** @type {Map<number, ImageBitmap>} timestamp_us -> ImageBitmap frame cache */
  var _frameCache = new Map();

  /** @type {boolean} has VideoDecoder support */
  var _hasWebCodecs = (typeof VideoDecoder !== 'undefined');

  // ── Helpers ────────────────────────────────────────────────────────────────

  /**
   * Format seconds to HH:MM:SS.
   * @param {number} seconds
   * @returns {string}
   */
  function _formatTimecode(seconds) {
    var s = Math.max(0, Math.floor(seconds));
    var h = Math.floor(s / 3600);
    var m = Math.floor((s % 3600) / 60);
    var sec = s % 60;
    return (
      String(h).padStart(2, '0') + ':' +
      String(m).padStart(2, '0') + ':' +
      String(sec).padStart(2, '0')
    );
  }

  /**
   * Format seconds as M:SS (shorter display for duration labels).
   * @param {number} seconds
   * @returns {string}
   */
  function _formatDuration(seconds) {
    var s = Math.max(0, Math.floor(seconds));
    var m = Math.floor(s / 60);
    var sec = s % 60;
    return m + ':' + String(sec).padStart(2, '0');
  }

  /**
   * Draw a frame (ImageBitmap) to the canvas.
   * @param {ImageBitmap} imageBitmap
   */
  function _renderFrame(imageBitmap) {
    if (!_ctx || !_canvas) { return; }
    _ctx.drawImage(imageBitmap, 0, 0, _canvas.width, _canvas.height);
  }

  /**
   * Draw the "no preview" placeholder state to canvas.
   * @param {string} [message]
   */
  function _renderPlaceholder(message) {
    if (!_ctx || !_canvas) { return; }
    _ctx.fillStyle = '#111';
    _ctx.fillRect(0, 0, _canvas.width, _canvas.height);
    _ctx.fillStyle = 'rgba(255,255,255,0.25)';
    _ctx.font = '16px "Segoe UI", system-ui, sans-serif';
    _ctx.textAlign = 'center';
    _ctx.textBaseline = 'middle';
    _ctx.fillText(
      message || 'No preview available',
      _canvas.width / 2,
      _canvas.height / 2
    );
  }

  /**
   * Evict oldest entries from the frame cache when it exceeds FRAME_CACHE_MAX.
   */
  function _evictFrameCache() {
    if (_frameCache.size <= FRAME_CACHE_MAX) { return; }
    // Map iteration order is insertion order — delete oldest entries first.
    var excess = _frameCache.size - FRAME_CACHE_MAX;
    var iter = _frameCache.keys();
    for (var i = 0; i < excess; i++) {
      var key = iter.next().value;
      var bmp = _frameCache.get(key);
      if (bmp && typeof bmp.close === 'function') { bmp.close(); }
      _frameCache.delete(key);
    }
  }

  /**
   * Store an ImageBitmap in the frame cache.
   * @param {number} timestampUs
   * @param {ImageBitmap} bitmap
   */
  function _cacheFrame(timestampUs, bitmap) {
    _frameCache.set(timestampUs, bitmap);
    _evictFrameCache();
  }

  /**
   * Update all DOM labels to reflect current state.
   */
  function _syncUI() {
    if (_timecodeEl) {
      _timecodeEl.textContent = _formatTimecode(_currentTime);
    }
    if (_scrub) {
      var pct = _duration > 0 ? (_currentTime / _duration) * 100 : 0;
      _scrub.value = String(pct);
    }
    if (_durationEl) {
      _durationEl.textContent = _formatDuration(_duration);
    }
    if (_partLabelEl) {
      _partLabelEl.textContent = _activePart !== null
        ? 'Part ' + _activePart
        : 'Part \u2014';
    }
    if (_clipCountEl) {
      _clipCountEl.textContent = _clips.length + ' clip' + (_clips.length === 1 ? '' : 's');
    }
  }

  // ── WebCodecs / mp4box integration ─────────────────────────────────────────

  /**
   * Initialise the WebCodecs VideoDecoder pipeline.
   * Gracefully degrades: if VideoDecoder is unavailable the canvas stays in
   * placeholder state and logs a warning.
   */
  function _initDecoder() {
    // Graceful degradation — if VideoDecoder is not available in the browser,
    // show the canvas in a "no preview" state with a text message.
    if (!_hasWebCodecs) {
      console.warn('[StudioPreview] VideoDecoder not available — preview disabled.');
      _renderPlaceholder('VideoDecoder not supported in this browser');
      return;
    }

    if (_decoder) {
      try { _decoder.close(); } catch (_) {}
      _decoder = null;
    }

    _decoder = new VideoDecoder({
      output: function (videoFrame) {
        // Create an ImageBitmap from the decoded frame and cache it.
        var ts = videoFrame.timestamp;
        createImageBitmap(videoFrame)
          .then(function (bmp) {
            _cacheFrame(ts, bmp);
            // If this is the frame nearest to currentTime, render it.
            var targetUs = Math.round(_currentTime * 1e6);
            var nearest = _findNearestCachedFrame(targetUs);
            if (nearest !== null && Math.abs(nearest - targetUs) < 100000 /* 100ms */) {
              var frameBmp = _frameCache.get(nearest);
              if (frameBmp) { _renderFrame(frameBmp); }
            }
          })
          .catch(function (e) {
            console.error('[StudioPreview] createImageBitmap failed', e);
          })
          .finally(function () {
            videoFrame.close();
          });
      },
      error: function (e) {
        console.error('[StudioPreview] VideoDecoder error:', e);
        _renderPlaceholder('Decoder error — see console');
      },
    });
  }

  /**
   * Find the timestamp in the frame cache nearest to targetUs.
   * Returns null if cache is empty.
   * @param {number} targetUs
   * @returns {number|null}
   */
  function _findNearestCachedFrame(targetUs) {
    if (_frameCache.size === 0) { return null; }
    var best = null;
    var bestDelta = Infinity;
    _frameCache.forEach(function (_bmp, ts) {
      var delta = Math.abs(ts - targetUs);
      if (delta < bestDelta) {
        bestDelta = delta;
        best = ts;
      }
    });
    return best;
  }

  /**
   * Fetch and demux an MP4 clip via mp4box.js, feeding encoded chunks to
   * _decoder.  If MP4Box is not loaded, logs a warning and returns immediately.
   * @param {string} url  — URL to the clip MP4 file
   */
  function _loadClipUrl(url) {
    if (typeof MP4Box === 'undefined') {
      console.warn('[StudioPreview] MP4Box not loaded — cannot demux clip.');
      _renderPlaceholder('MP4Box not loaded');
      return;
    }
    if (!_decoder || _decoder.state === 'closed') {
      _initDecoder();
    }
    if (!_decoder) { return; }

    var mp4 = MP4Box.createFile();

    mp4.onReady = function (info) {
      var videoTrack = null;
      for (var i = 0; i < info.tracks.length; i++) {
        if (info.tracks[i].video) { videoTrack = info.tracks[i]; break; }
      }
      if (!videoTrack) {
        console.warn('[StudioPreview] No video track found in', url);
        return;
      }

      var codecStr = videoTrack.codec;
      _decoder.configure({
        codec:             codecStr,
        codedWidth:        videoTrack.video.width,
        codedHeight:       videoTrack.video.height,
        hardwareAcceleration: 'prefer-software',
      });

      mp4.setExtractionOptions(videoTrack.id, null, { nbSamples: 100 });
      mp4.start();
    };

    mp4.onSamples = function (_trackId, _ref, samples) {
      samples.forEach(function (sample) {
        var chunk = new EncodedVideoChunk({
          type:      sample.is_sync ? 'key' : 'delta',
          timestamp: (sample.cts * 1e6) / sample.timescale,
          duration:  (sample.duration * 1e6) / sample.timescale,
          data:      sample.data,
        });
        _decoder.decode(chunk);
      });
    };

    mp4.onError = function (e) {
      console.error('[StudioPreview] MP4Box error:', e);
      _renderPlaceholder('MP4 parse error');
    };

    // Fetch the clip in chunks and pipe into mp4box.
    var byteOffset = 0;
    fetch(url)
      .then(function (res) {
        if (!res.ok) {
          throw new Error('HTTP ' + res.status + ' fetching ' + url);
        }
        var reader = res.body.getReader();
        function pump() {
          return reader.read().then(function (result) {
            if (result.done) {
              mp4.flush();
              return;
            }
            var buf = result.value.buffer;
            buf.fileStart = byteOffset;
            byteOffset += buf.byteLength;
            mp4.appendBuffer(buf);
            return pump();
          });
        }
        return pump();
      })
      .catch(function (e) {
        console.error('[StudioPreview] Clip fetch failed:', e);
        _renderPlaceholder('Clip fetch failed');
      });
  }

  /**
   * Load a clip into the <video> element via the WebM stream endpoint.
   * @param {string} clipPath  — absolute filesystem path to the clip
   */
  function _loadClipStream(clipPath) {
    if (!_video) { return; }
    var url = '/api/studio/clip-stream?path=' + encodeURIComponent(clipPath);
    _video.pause();
    _video.src = url;
    _video.load();
    // Show video, hide canvas once video is ready
    _video.style.display = 'block';
    if (_canvas) { _canvas.style.display = 'none'; }
  }

  /**
   * Fetch a JPEG thumbnail from /api/studio/clip-thumb and draw it on the canvas.
   * Falls back gracefully if the endpoint is unavailable.
   * @param {string} clipPath  — absolute filesystem path to the clip
   * @param {number} tSec      — timestamp in seconds for the frame
   */
  function _loadClipThumb(clipPath, tSec) {
    if (!_ctx || !_canvas) { return; }
    var url = '/api/studio/clip-thumb?path=' + encodeURIComponent(clipPath) +
              '&t=' + (tSec || 1.0);
    var img = new Image();
    img.onload = function () {
      if (!_ctx || !_canvas) { return; }
      _ctx.clearRect(0, 0, _canvas.width, _canvas.height);
      // Letterbox the image into the canvas.
      var cw = _canvas.width, ch = _canvas.height;
      var scale = Math.min(cw / img.width, ch / img.height);
      var dw = img.width * scale, dh = img.height * scale;
      var dx = (cw - dw) / 2, dy = (ch - dh) / 2;
      _ctx.fillStyle = '#000';
      _ctx.fillRect(0, 0, cw, ch);
      _ctx.drawImage(img, dx, dy, dw, dh);
      // Subtle overlay label.
      _ctx.fillStyle = 'rgba(0,0,0,0.55)';
      _ctx.fillRect(0, ch - 22, cw, 22);
      _ctx.fillStyle = '#e8b923';
      _ctx.font = '10px Consolas, monospace';
      _ctx.fillText(clipPath.split('\\').pop() || clipPath.split('/').pop(), 6, ch - 6);
    };
    img.onerror = function () {
      console.warn('[StudioPreview] Thumbnail fetch failed for', clipPath);
      _renderPlaceholder('Thumbnail unavailable');
    };
    img.src = url;
  }

  // ── playback loop ──────────────────────────────────────────────────────────

  /**
   * requestAnimationFrame tick — advances _currentTime and syncs UI.
   * @param {number} ts  DOMHighResTimeStamp
   */
  function _rafTick(ts) {
    if (!_isPlaying) { return; }

    if (_rafLastTs !== null) {
      var delta = (ts - _rafLastTs) / 1000;
      _currentTime = Math.min(_currentTime + delta, _duration);
      _syncUI();

      // Render nearest cached frame.
      var targetUs = Math.round(_currentTime * 1e6);
      var nearest = _findNearestCachedFrame(targetUs);
      if (nearest !== null) {
        var bmp = _frameCache.get(nearest);
        if (bmp) { _renderFrame(bmp); }
      }

      // Notify store of updated playhead.
      if (global.StudioStore) {
        global.StudioStore.dispatch({ type: 'SET_CURRENT_TIME', payload: _currentTime });
      }

      // Stop at end.
      if (_currentTime >= _duration && _duration > 0) {
        _isPlaying = false;
        _rafLastTs = null;
        if (global.StudioStore) {
          global.StudioStore.dispatch({ type: 'SET_PLAYING', payload: false });
        }
        return;
      }
    }

    _rafLastTs = ts;
    _rafHandle = requestAnimationFrame(_rafTick);
  }

  // ── DOM builder ────────────────────────────────────────────────────────────

  /**
   * Build and return the panel root element.
   * @returns {HTMLDivElement}
   */
  function _buildDOM() {
    // Outer panel
    var panel = document.createElement('div');
    panel.className = 'preview-panel';

    // Viewport
    var viewport = document.createElement('div');
    viewport.className = 'preview-viewport';

    _canvas = document.createElement('canvas');
    _canvas.id     = 'preview-canvas';
    _canvas.width  = 1280;
    _canvas.height = 720;

    // Video element for WebM stream playback (shown instead of canvas when a clip is selected)
    _video = document.createElement('video');
    _video.id       = 'preview-video';
    _video.controls = true;
    _video.style.cssText = 'display:none;max-width:100%;max-height:100%;background:#000;';
    viewport.appendChild(_video);

    var overlay = document.createElement('div');
    overlay.className = 'preview-overlay';

    _clipNameEl = document.createElement('span');
    _clipNameEl.className = 'preview-clip-name';

    _timecodeEl = document.createElement('span');
    _timecodeEl.className = 'preview-timecode';
    _timecodeEl.textContent = '00:00:00';

    overlay.appendChild(_clipNameEl);
    overlay.appendChild(_timecodeEl);

    viewport.appendChild(_canvas);
    viewport.appendChild(overlay);

    // Controls
    var controls = document.createElement('div');
    controls.className = 'preview-controls';

    var scrubbar = document.createElement('div');
    scrubbar.className = 'preview-scrubbar';

    _scrub = document.createElement('input');
    _scrub.type  = 'range';
    _scrub.id    = 'preview-scrub';
    _scrub.min   = '0';
    _scrub.max   = '100';
    _scrub.value = '0';
    _scrub.step  = '0.1';

    _scrub.addEventListener('input', function () {
      var pct = parseFloat(_scrub.value) / 100;
      var t   = pct * _duration;
      _currentTime = t;
      _rafLastTs   = null;
      _syncUI();
      if (global.StudioStore) {
        global.StudioStore.dispatch({ type: 'SET_CURRENT_TIME', payload: t });
      }
    });

    scrubbar.appendChild(_scrub);

    var info = document.createElement('div');
    info.className = 'preview-info';

    _partLabelEl = document.createElement('span');
    _partLabelEl.className = 'preview-part-label';
    _partLabelEl.textContent = 'Part \u2014';

    _clipCountEl = document.createElement('span');
    _clipCountEl.className = 'preview-clip-count';
    _clipCountEl.textContent = '0 clips';

    _durationEl = document.createElement('span');
    _durationEl.className = 'preview-duration';
    _durationEl.textContent = '0:00';

    info.appendChild(_partLabelEl);
    info.appendChild(_clipCountEl);
    info.appendChild(_durationEl);

    controls.appendChild(scrubbar);
    controls.appendChild(info);

    panel.appendChild(viewport);
    panel.appendChild(controls);

    return panel;
  }

  // ── Store subscription ─────────────────────────────────────────────────────

  /**
   * Subscribe to StudioStore changes and react to activePart / isPlaying /
   * currentTime updates.
   */
  function _subscribeStore() {
    var store = global.StudioStore;
    if (!store) { return; }

    _storeUnsub = store.subscribe(function (state, prev) {
      // activePart changed — reload clips for the new part.
      if (state.activePart !== prev.activePart) {
        _activePart = state.activePart;
        _syncUI();
      }

      // clips list resolved — call loadPart internally.
      if (state.clips !== prev.clips && state.activePart !== null) {
        _loadPartInternal(state.activePart, state.clips);
      }

      // isPlaying toggled from outside (e.g. transport buttons).
      if (state.isPlaying !== prev.isPlaying) {
        if (state.isPlaying) {
          _startPlayback();
        } else {
          _stopPlayback();
        }
      }

      // currentTime driven from outside (e.g. rewind button → SET_CURRENT_TIME 0).
      if (state.currentTime !== prev.currentTime &&
          Math.abs(state.currentTime - _currentTime) > 0.05) {
        _currentTime = state.currentTime;
        _rafLastTs   = null;
        _syncUI();
      }

      // selectedClip changed — stream the newly selected clip via /api/studio/clip-stream.
      // Clips from /api/studio/part/{n}/clips carry an absolute .path field.
      if (state.selectedClip !== prev.selectedClip && state.selectedClip) {
        var cp = state.selectedClip.path || state.selectedClip.url;
        if (cp) { _loadClipStream(cp); }
      }
    });
  }

  /**
   * Internal: reset state for a newly loaded part.
   * @param {number} partNum
   * @param {Array}  clips
   */
  function _loadPartInternal(partNum, clips) {
    _activePart  = partNum;
    _clips       = clips || [];
    _currentTime = 0;
    _rafLastTs   = null;
    _isPlaying   = false;

    // Estimate total duration from clips (sum of clip.duration if present).
    var totalDuration = 0;
    _clips.forEach(function (clip) {
      if (typeof clip.duration === 'number') {
        totalDuration += clip.duration;
      }
    });
    _duration = totalDuration;

    // Clear frame cache.
    _frameCache.forEach(function (bmp) {
      if (bmp && typeof bmp.close === 'function') { bmp.close(); }
    });
    _frameCache.clear();

    _syncUI();

    // Show placeholder until a clip is actually decoded.
    if (_clips.length === 0) {
      _renderPlaceholder('No clips for Part ' + partNum);
      return;
    }

    _renderPlaceholder('Part ' + partNum + ' loaded — ' + _clips.length + ' clip(s)');

    // Kick off thumbnail for first clip.
    var firstClip = _clips[0];
    if (firstClip && (firstClip.path || firstClip.url)) {
      _loadClipThumb(firstClip.path || firstClip.url, 1.0);
    }
  }

  // ── Playback ───────────────────────────────────────────────────────────────

  function _startPlayback() {
    if (_isPlaying) { return; }
    _isPlaying  = true;
    _rafLastTs  = null;
    _rafHandle  = requestAnimationFrame(_rafTick);
  }

  function _stopPlayback() {
    _isPlaying = false;
    if (_rafHandle !== null) {
      cancelAnimationFrame(_rafHandle);
      _rafHandle = null;
    }
    _rafLastTs = null;
  }

  // ── Public API ─────────────────────────────────────────────────────────────

  /**
   * Mount the preview panel inside containerEl.
   * @param {Element} containerEl
   */
  function mount(containerEl) {
    if (_container) { unmount(); }

    _container = document.createElement('div');
    _container.style.cssText = 'width:100%;flex:1;min-height:0;display:flex;flex-direction:column;';

    var panel = _buildDOM();
    _container.appendChild(panel);
    containerEl.appendChild(_container);

    _ctx = _canvas.getContext('2d');

    // Initialise decoder pipeline (or show graceful degradation message).
    _initDecoder();
    _renderPlaceholder('Select a Part to preview');

    // Subscribe to store.
    _subscribeStore();
    _syncUI();
  }

  /**
   * Unmount the preview panel — removes DOM and cleans up resources.
   */
  function unmount() {
    _stopPlayback();

    if (_storeUnsub) { _storeUnsub(); _storeUnsub = null; }

    if (_decoder) {
      try { _decoder.close(); } catch (_) {}
      _decoder = null;
    }

    _frameCache.forEach(function (bmp) {
      if (bmp && typeof bmp.close === 'function') { bmp.close(); }
    });
    _frameCache.clear();

    if (_container && _container.parentNode) {
      _container.parentNode.removeChild(_container);
    }
    if (_video) { _video.pause(); _video.src = ''; _video = null; }
    _container    = null;
    _canvas       = null;
    _ctx          = null;
    _scrub        = null;
    _timecodeEl   = null;
    _clipNameEl   = null;
    _partLabelEl  = null;
    _clipCountEl  = null;
    _durationEl   = null;
  }

  /**
   * Load clips for a part number.
   * @param {number} partNum
   * @param {Array}  clips
   */
  function loadPart(partNum, clips) {
    _loadPartInternal(partNum, clips);
  }

  /**
   * Seek the playhead to timeSeconds.
   * @param {number} timeSeconds
   */
  function seek(timeSeconds) {
    _currentTime = Math.max(0, Math.min(timeSeconds, _duration));
    _rafLastTs   = null;
    _syncUI();
    if (global.StudioStore) {
      global.StudioStore.dispatch({ type: 'SET_CURRENT_TIME', payload: _currentTime });
    }
  }

  /**
   * Start playback.
   */
  function play() {
    _startPlayback();
    if (global.StudioStore) {
      global.StudioStore.dispatch({ type: 'SET_PLAYING', payload: true });
    }
  }

  /**
   * Pause playback.
   */
  function pause() {
    _stopPlayback();
    if (global.StudioStore) {
      global.StudioStore.dispatch({ type: 'SET_PLAYING', payload: false });
    }
  }

  /**
   * Return current preview state snapshot.
   * @returns {{ isPlaying: boolean, currentTime: number, duration: number, partNum: number|null }}
   */
  function getState() {
    return {
      isPlaying:   _isPlaying,
      currentTime: _currentTime,
      duration:    _duration,
      partNum:     _activePart,
    };
  }

  // ── Export ─────────────────────────────────────────────────────────────────

  global.StudioPreview = {
    mount:    mount,
    unmount:  unmount,
    loadPart: loadPart,
    seek:     seek,
    play:     play,
    pause:    pause,
    getState: getState,
    // Internal helpers exposed for testing (prefixed with underscore by convention).
    _formatTimecode: _formatTimecode,
  };

}(typeof window !== 'undefined' ? window : this));
