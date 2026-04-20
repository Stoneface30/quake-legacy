/**
 * PANTHEON STUDIO — LiteGraph Effect Node Graph Panel
 * studio-litegraph.js
 *
 * Builds a visual FFmpeg effect-chain editor using LiteGraph.js.
 * Lets the user wire input_clip → effect nodes → output_render,
 * then read back a flat array of effect descriptors to pass to the
 * render pipeline.
 *
 * Exposed on: window.StudioEffects
 *
 * Depends on:
 *   window.LiteGraph   (vendor/litegraph.js loaded first)
 *   window.LGraph      (same vendor file)
 *   window.LGraphCanvas (same vendor file)
 *   window.StudioStore (studio-store.js loaded first)
 *   window.StudioTimeline (studio-timeline.js — optional, for selected clip)
 *
 * Rule UI-1: DOM built with createElement/textContent only — no unsafe injection.
 * Rule UI-2: all state from StudioStore — no local drift.
 */
(function (global) {
  'use strict';

  // ── Module-private state ───────────────────────────────────────────────────

  /** @type {Element|null} */
  var _container = null;

  /** @type {Element|null} */
  var _panelEl = null;

  /** @type {Element|null} */
  var _statusText = null;

  /** @type {object|null} LGraph instance */
  var _graph = null;

  /** @type {object|null} LGraphCanvas instance */
  var _canvas = null;

  /** @type {function|null} StudioStore unsubscribe handle */
  var _unsubscribe = null;

  /** @type {boolean} True once node types have been registered */
  var _typesRegistered = false;

  // ── LiteGraph node type registration ──────────────────────────────────────

  /**
   * Register all custom Quake effect node types with LiteGraph.
   * Called once before any graph is created.
   */
  function _registerNodeTypes() {
    if (_typesRegistered) { return; }
    if (typeof LiteGraph === 'undefined') { return; }

    // 1. INPUT CLIP ─────────────────────────────────────────────────────────
    function InputClipNode() {
      this.addOutput('clip', 'string');
      this.properties = { clip_path: '' };
      this.title = 'INPUT CLIP';
      this.size = [180, 50];
    }
    InputClipNode.title = 'INPUT CLIP';
    LiteGraph.registerNodeType('quake/input_clip', InputClipNode);

    // 2. SLOW MOTION ────────────────────────────────────────────────────────
    function SlowMotionNode() {
      this.addInput('clip', 'string');
      this.addOutput('clip', 'string');
      this.properties = { rate: 0.5, window_s: 0.8 };
      this.title = 'SLOW MOTION';
      this.color = '#3a1a1a';
      this.bgcolor = '#2a1010';
      this.size = [180, 70];
    }
    SlowMotionNode.title = 'SLOW MOTION';
    LiteGraph.registerNodeType('quake/slow_motion', SlowMotionNode);

    // 3. SPEED UP ───────────────────────────────────────────────────────────
    function SpeedUpNode() {
      this.addInput('clip', 'string');
      this.addOutput('clip', 'string');
      this.properties = { rate: 2.0, window_s: 0.8 };
      this.title = 'SPEED UP';
      this.color = '#1a3a1a';
      this.bgcolor = '#102810';
      this.size = [180, 70];
    }
    SpeedUpNode.title = 'SPEED UP';
    LiteGraph.registerNodeType('quake/speed_up', SpeedUpNode);

    // 4. ZOOM ───────────────────────────────────────────────────────────────
    function ZoomNode() {
      this.addInput('clip', 'string');
      this.addOutput('clip', 'string');
      this.properties = { scale: 1.3, cx: 0.5, cy: 0.5 };
      this.title = 'ZOOM';
      this.color = '#1a1a3a';
      this.bgcolor = '#101028';
      this.size = [180, 70];
    }
    ZoomNode.title = 'ZOOM';
    LiteGraph.registerNodeType('quake/zoom', ZoomNode);

    // 5. OUTPUT RENDER ──────────────────────────────────────────────────────
    function OutputRenderNode() {
      this.addInput('clip', 'string');
      this.properties = { format: 'mp4' };
      this.title = 'OUTPUT';
      this.size = [180, 50];
    }
    OutputRenderNode.title = 'OUTPUT';
    LiteGraph.registerNodeType('quake/output_render', OutputRenderNode);

    _typesRegistered = true;
  }

  // ── Default graph factory ─────────────────────────────────────────────────

  /**
   * Populate graph with the default two-node starter layout:
   *   INPUT CLIP → OUTPUT RENDER
   */
  function _loadDefaultGraph() {
    if (!_graph) { return; }
    _graph.clear();

    var inputNode = LiteGraph.createNode('quake/input_clip');
    inputNode.pos = [80, 120];
    _graph.add(inputNode);

    var outputNode = LiteGraph.createNode('quake/output_render');
    outputNode.pos = [340, 120];
    _graph.add(outputNode);

    // Connect output slot 0 of inputNode → input slot 0 of outputNode
    inputNode.connect(0, outputNode, 0);

    if (_graph.setDirtyCanvas) {
      _graph.setDirtyCanvas(true, true);
    }
  }

  // ── Graph traversal (getEffectChain) ──────────────────────────────────────

  /**
   * Walk the graph from input_clip through connected outputs until
   * output_render (or dead end), collecting effect descriptors.
   *
   * @returns {Array<Object>} Ordered array of effect descriptor objects.
   */
  function _getEffectChain() {
    if (!_graph) { return []; }

    var nodes = _graph._nodes || [];
    var chain = [];

    // Find the input node
    var inputNode = null;
    for (var i = 0; i < nodes.length; i++) {
      if (nodes[i].type === 'quake/input_clip') {
        inputNode = nodes[i];
        break;
      }
    }
    if (!inputNode) { return []; }

    // Walk the chain
    var current = inputNode;
    var visited = {};
    var MAX_WALK = 64;
    var steps = 0;

    while (current && steps < MAX_WALK) {
      steps++;
      visited[current.id] = true;

      // Collect effect descriptor for non-input/non-output nodes
      if (current.type === 'quake/slow_motion') {
        chain.push({
          type: 'slow_motion',
          rate: current.properties.rate,
          window_s: current.properties.window_s,
        });
      } else if (current.type === 'quake/speed_up') {
        chain.push({
          type: 'speed_up',
          rate: current.properties.rate,
          window_s: current.properties.window_s,
        });
      } else if (current.type === 'quake/zoom') {
        chain.push({
          type: 'zoom',
          scale: current.properties.scale,
          cx: current.properties.cx,
          cy: current.properties.cy,
        });
      }

      // Stop at output node
      if (current.type === 'quake/output_render') { break; }

      // Advance: follow the first connected output link
      var nextNode = null;
      if (current.outputs && current.outputs.length > 0) {
        var outputSlot = current.outputs[0];
        if (outputSlot && outputSlot.links && outputSlot.links.length > 0) {
          var linkId = outputSlot.links[0];
          var link = _graph.links[linkId];
          if (link) {
            var candidate = _graph.getNodeById(link.target_id);
            if (candidate && !visited[candidate.id]) {
              nextNode = candidate;
            }
          }
        }
      }
      current = nextNode;
    }

    return chain;
  }

  // ── Store subscription ─────────────────────────────────────────────────────

  /**
   * Called whenever StudioStore state changes.
   * Updates the input_clip node's clip_path when a clip is selected.
   */
  function _onStoreChange(state) {
    if (!_graph) { return; }
    var clips = state.clips || [];
    if (!clips.length) { return; }

    // Try to get the selected clip from StudioTimeline if available
    var selectedClip = null;
    if (global.StudioTimeline && typeof global.StudioTimeline.getSelectedClip === 'function') {
      selectedClip = global.StudioTimeline.getSelectedClip();
    }
    if (!selectedClip) { return; }

    var clipPath = selectedClip.path || selectedClip.clip_path || selectedClip.name || '';
    if (!clipPath) { return; }

    // Update all input_clip nodes in the graph
    var nodes = _graph._nodes || [];
    for (var i = 0; i < nodes.length; i++) {
      if (nodes[i].type === 'quake/input_clip') {
        nodes[i].properties.clip_path = clipPath;
        if (_graph.setDirtyCanvas) {
          _graph.setDirtyCanvas(true, false);
        }
      }
    }
  }

  // ── DOM construction ───────────────────────────────────────────────────────

  /**
   * Build the effects panel DOM tree using only createElement/textContent.
   * @returns {Element} The root .effects-panel div.
   */
  function _buildPanelDOM() {
    // Root panel
    var panel = document.createElement('div');
    panel.className = 'effects-panel';

    // Toolbar
    var toolbar = document.createElement('div');
    toolbar.className = 'effects-toolbar';

    var label = document.createElement('span');
    label.className = 'effects-label';
    label.textContent = 'EFFECT GRAPH';
    toolbar.appendChild(label);

    var clearBtn = document.createElement('button');
    clearBtn.className = 'ef-btn';
    clearBtn.id = 'ef-btn-clear';
    clearBtn.textContent = 'CLEAR';
    toolbar.appendChild(clearBtn);

    var applyBtn = document.createElement('button');
    applyBtn.className = 'ef-btn';
    applyBtn.id = 'ef-btn-run';
    applyBtn.textContent = 'APPLY';
    toolbar.appendChild(applyBtn);

    panel.appendChild(toolbar);

    // Canvas wrap
    var canvasWrap = document.createElement('div');
    canvasWrap.className = 'effects-canvas-wrap';
    panel.appendChild(canvasWrap);

    // Status bar
    var statusBar = document.createElement('div');
    statusBar.className = 'effects-status';

    var statusSpan = document.createElement('span');
    statusSpan.className = 'ef-status-text';
    statusSpan.textContent = 'No effects';
    statusBar.appendChild(statusSpan);

    panel.appendChild(statusBar);

    return { panel: panel, canvasWrap: canvasWrap, statusSpan: statusSpan };
  }

  // ── Canvas resize helper ───────────────────────────────────────────────────

  function _resizeCanvas() {
    if (!_canvas || !_canvas.canvas) { return; }
    var wrap = _canvas.canvas.parentElement;
    if (!wrap) { return; }
    var rect = wrap.getBoundingClientRect();
    if (rect.width > 0 && rect.height > 0) {
      _canvas.canvas.width = rect.width;
      _canvas.canvas.height = rect.height;
      if (_canvas.setDirty) {
        _canvas.setDirty(true, true);
      }
    }
  }

  // ── Public API ─────────────────────────────────────────────────────────────

  /**
   * mount(containerEl)
   * Creates the effects panel DOM, initialises LGraph + LGraphCanvas,
   * loads the default starter graph, and subscribes to StudioStore.
   *
   * @param {Element} containerEl — element to inject the panel into.
   */
  function mount(containerEl) {
    if (_panelEl) { return; }  // already mounted
    _container = containerEl;

    var domResult = _buildPanelDOM();
    _panelEl    = domResult.panel;
    _statusText = domResult.statusSpan;
    var canvasWrap = domResult.canvasWrap;

    _container.appendChild(_panelEl);

    // LiteGraph unavailable — show placeholder, bail out
    if (typeof LiteGraph === 'undefined') {
      var placeholder = document.createElement('p');
      placeholder.textContent = 'LiteGraph not loaded';
      placeholder.style.cssText = 'color:#888;padding:16px;margin:0;';
      canvasWrap.appendChild(placeholder);
      return;
    }

    // Register custom node types (idempotent)
    _registerNodeTypes();

    // Create canvas element
    var canvasEl = document.createElement('canvas');
    canvasEl.id = 'effects-canvas';
    canvasEl.style.cssText = 'display:block;width:100%;height:100%;';
    canvasWrap.appendChild(canvasEl);

    // Size the canvas backing store to match its CSS box
    var rect = canvasWrap.getBoundingClientRect();
    canvasEl.width  = Math.max(rect.width,  400);
    canvasEl.height = Math.max(rect.height, 300);

    // Create graph + canvas
    _graph  = new LGraph();
    _canvas = new LGraphCanvas(canvasEl, _graph);

    // Load default two-node graph
    _loadDefaultGraph();

    // Wire up toolbar buttons
    var clearBtn = _panelEl.querySelector('#ef-btn-clear');
    if (clearBtn) {
      clearBtn.addEventListener('click', function () { clearGraph(); });
    }

    var applyBtn = _panelEl.querySelector('#ef-btn-run');
    if (applyBtn) {
      applyBtn.addEventListener('click', function () {
        var chain = getEffectChain();
        var msg = chain.length > 0
          ? chain.length + ' effect' + (chain.length !== 1 ? 's' : '') + ' queued'
          : 'No effects';
        if (_statusText) { _statusText.textContent = msg; }
        if (global.StudioStore) {
          global.StudioStore.dispatch({ type: 'SET_STATUS_MSG', payload: msg });
        }
      });
    }

    // Subscribe to store
    if (global.StudioStore) {
      _unsubscribe = global.StudioStore.subscribe(_onStoreChange);
    }

    // Handle window resize
    window.addEventListener('resize', _resizeCanvas);
  }

  /**
   * unmount()
   * Destroys the graph, removes the DOM, and cleans up listeners.
   */
  function unmount() {
    if (_unsubscribe) {
      _unsubscribe();
      _unsubscribe = null;
    }

    window.removeEventListener('resize', _resizeCanvas);

    if (_canvas) {
      if (typeof _canvas.stopRendering === 'function') {
        _canvas.stopRendering();
      }
      _canvas = null;
    }

    if (_graph) {
      if (typeof _graph.stop === 'function') {
        _graph.stop();
      }
      _graph = null;
    }

    if (_panelEl && _panelEl.parentNode) {
      _panelEl.parentNode.removeChild(_panelEl);
    }

    _panelEl    = null;
    _statusText = null;
    _container  = null;
  }

  /**
   * loadGraph(graphJson)
   * Loads a previously-serialised graph from a JSON object.
   *
   * @param {Object} graphJson — output of a prior saveGraph() call.
   */
  function loadGraph(graphJson) {
    if (!_graph) { return; }
    if (!graphJson || typeof graphJson !== 'object') { return; }
    _graph.configure(graphJson);
    if (_graph.setDirtyCanvas) {
      _graph.setDirtyCanvas(true, true);
    }
  }

  /**
   * saveGraph()
   * Serialises the current graph state.
   *
   * @returns {Object|null} Serialised graph JSON, or null if not mounted.
   */
  function saveGraph() {
    if (!_graph) { return null; }
    return _graph.serialize();
  }

  /**
   * clearGraph()
   * Removes all nodes and reloads the default two-node starter graph.
   */
  function clearGraph() {
    if (!_graph) { return; }
    _loadDefaultGraph();
    if (_statusText) { _statusText.textContent = 'No effects'; }
  }

  /**
   * getEffectChain()
   * Returns an ordered array of effect descriptor objects by walking
   * the graph from input_clip to output_render.
   *
   * @returns {Array<Object>}
   */
  function getEffectChain() {
    return _getEffectChain();
  }

  // ── Export ─────────────────────────────────────────────────────────────────

  global.StudioEffects = {
    mount:          mount,
    unmount:        unmount,
    loadGraph:      loadGraph,
    saveGraph:      saveGraph,
    clearGraph:     clearGraph,
    getEffectChain: getEffectChain,
  };

}(typeof window !== 'undefined' ? window : this));
