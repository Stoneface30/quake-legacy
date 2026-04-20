/**
 * PANTHEON STUDIO — Shared Reactive Store
 * studio-store.js
 *
 * Lightweight observable store. No framework. Plain ES5-compatible global
 * so it can be loaded as a classic <script> before any app code.
 *
 * Exposed on: window.StudioStore
 */
(function (global) {
  'use strict';

  /** @type {StudioState} */
  var INITIAL_STATE = {
    activePage:    'preview',
    activePart:    null,
    parts:         [],
    clips:         [],
    isPlaying:     false,
    currentTime:   0,
    buildStatus:   null,
    statusMessage: 'Ready',
  };

  // ── Private state ──────────────────────────────────────────────────────────

  var _state     = Object.assign({}, INITIAL_STATE);
  var _listeners = [];

  // ── Core helpers ───────────────────────────────────────────────────────────

  /**
   * Shallow-merge patch into state and notify all listeners.
   * @param {Partial<StudioState>} patch
   */
  function setState(patch) {
    var prev = Object.assign({}, _state);
    _state   = Object.assign({}, _state, patch);
    for (var i = 0; i < _listeners.length; i++) {
      try {
        _listeners[i](_state, prev);
      } catch (e) {
        console.error('[StudioStore] listener error', e);
      }
    }
  }

  /**
   * Return a shallow copy of current state (callers cannot mutate the store).
   * @returns {StudioState}
   */
  function getState() {
    return Object.assign({}, _state);
  }

  /**
   * Register a change listener.
   * @param {function(StudioState, StudioState): void} listener
   * @returns {function(): void} unsubscribe
   */
  function subscribe(listener) {
    _listeners.push(listener);
    return function unsubscribe() {
      _listeners = _listeners.filter(function (l) { return l !== listener; });
    };
  }

  // ── Async helpers ──────────────────────────────────────────────────────────

  /**
   * Fetch clips for a given part number and dispatch SET_CLIPS.
   * On failure, dispatches SET_STATUS_MSG with an error string.
   * @param {number} partNum
   */
  function _fetchClips(partNum) {
    fetch('/api/studio/part/' + partNum + '/clips')
      .then(function (res) {
        if (!res.ok) {
          throw new Error('HTTP ' + res.status);
        }
        return res.json();
      })
      .then(function (data) {
        dispatch({ type: 'SET_CLIPS', payload: data.clips || [] });
      })
      .catch(function (err) {
        console.error('[StudioStore] fetchClips failed', err);
        dispatch({ type: 'SET_STATUS_MSG', payload: 'Failed to load clips: ' + err.message });
      });
  }

  // ── Action dispatcher ──────────────────────────────────────────────────────

  /**
   * Dispatch a named action. Synchronous state mutations are applied immediately.
   * SET_ACTIVE_PART also kicks off an async clip fetch.
   * @param {{ type: string, payload?: any }} action
   */
  function dispatch(action) {
    switch (action.type) {
      case 'SET_ACTIVE_PAGE':
        setState({ activePage: action.payload });
        break;

      case 'SET_ACTIVE_PART':
        setState({ activePart: action.payload, clips: [] });
        if (action.payload !== null && action.payload !== undefined) {
          _fetchClips(action.payload);
        }
        break;

      case 'SET_PARTS':
        setState({ parts: action.payload });
        break;

      case 'SET_CLIPS':
        setState({ clips: action.payload });
        break;

      case 'SET_PLAYING':
        setState({ isPlaying: action.payload });
        break;

      case 'SET_CURRENT_TIME':
        setState({ currentTime: action.payload });
        break;

      case 'SET_BUILD_STATUS':
        setState({ buildStatus: action.payload });
        break;

      case 'SET_STATUS_MSG':
        setState({ statusMessage: action.payload });
        break;

      default:
        console.warn('[StudioStore] Unknown action type:', action.type);
    }
  }

  // ── Public API ─────────────────────────────────────────────────────────────

  global.StudioStore = {
    getState:  getState,
    setState:  setState,
    subscribe: subscribe,
    dispatch:  dispatch,
  };

}(typeof window !== 'undefined' ? window : this));
