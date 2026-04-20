#!/usr/bin/env node
// build.js — copy vendor libs into creative_suite/frontend/vendor/
// Run: node build.js
// Each package is copied as a single minified ESM file.

const fs = require("fs");
const path = require("path");

const VENDOR = path.join(__dirname, "creative_suite", "frontend", "vendor");
fs.mkdirSync(VENDOR, { recursive: true });

// Map: vendor filename -> source in node_modules
const copies = [
  // animation-timeline-js (MIT) — canvas-based keyframe timeline
  {
    src: "node_modules/animation-timeline-js/lib/animation-timeline.min.js",
    dst: "animation-timeline.js",
  },
  // wavesurfer.js ESM bundle (BSD-3-Clause)
  {
    src: "node_modules/wavesurfer.js/dist/wavesurfer.esm.js",
    dst: "wavesurfer.js",
  },
  // wavesurfer-multitrack plugin (BSD-3-Clause) — separate package from v7+
  {
    src: "node_modules/wavesurfer-multitrack/dist/multitrack.min.js",
    dst: "wavesurfer-multitrack.js",
  },
  // tweakpane ESM (MIT)
  {
    src: "node_modules/tweakpane/dist/tweakpane.js",
    dst: "tweakpane.js",
  },
  // mp4box (BSD-3-Clause)
  {
    src: "node_modules/mp4box/dist/mp4box.all.min.js",
    dst: "mp4box.js",
  },
  // Theatre.js core + studio bundle (Apache-2.0 / AGPL-3.0 — local personal use only)
  {
    src: "node_modules/@theatre/browser-bundles/dist/core-and-studio.js",
    dst: "theatre-core-studio.js",
  },
];

let ok = 0, fail = 0;
for (const { src, dst } of copies) {
  const srcPath = path.join(__dirname, src);
  const dstPath = path.join(VENDOR, dst);
  if (fs.existsSync(srcPath)) {
    fs.copyFileSync(srcPath, dstPath);
    console.log("OK  " + dst);
    ok++;
  } else {
    console.warn("MISSING  " + dst + " -- source not found: " + src);
    fail++;
  }
}
console.log("\nBuild: " + ok + " copied, " + fail + " missing");
if (fail > 0) process.exit(1);
