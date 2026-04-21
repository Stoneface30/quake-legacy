// md3viewer.js — minimal Quake 3 MD3 model viewer using Three.js.
//
// Task 4 / Creative Suite v2. Mounts on a host <div>, loads raw MD3 bytes
// over fetch, parses the format, builds a Three.js mesh, and spins it on a
// turntable. Three lights with slider-controllable intensities — ambient,
// key, and RIM (back-of-model, per L85 rim-light fix learning).
//
// Usage:
//   import { MD3Viewer } from '/web/js/md3viewer.js';
//   const v = new MD3Viewer(document.getElementById('md3-host'));
//   v.loadUrl('/api/md3/123');
//
// MD3 format reference: https://icculus.org/~phaethon/q3a/formats/md3format.html
//
// We parse the first frame only (static pose). Quake md3s are cm-scale;
// we auto-fit to a unit sphere so any model fills the viewport.

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const MD3_XYZ_SCALE = 1.0 / 64.0; // per format spec

function readHeader(dv) {
  const ident = String.fromCharCode(
    dv.getUint8(0), dv.getUint8(1), dv.getUint8(2), dv.getUint8(3),
  );
  if (ident !== 'IDP3') throw new Error(`bad md3 magic: ${ident}`);
  return {
    ident,
    version: dv.getInt32(4, true),
    numFrames: dv.getInt32(76, true),
    numTags: dv.getInt32(80, true),
    numSurfaces: dv.getInt32(84, true),
    ofsFrames: dv.getInt32(92, true),
    ofsTags: dv.getInt32(96, true),
    ofsSurfaces: dv.getInt32(100, true),
    ofsEof: dv.getInt32(104, true),
  };
}

function readSurface(dv, base) {
  // Surface header is 108 bytes; ident at base + 0 is "IDP3"
  const numFrames = dv.getInt32(base + 72, true);
  const numShaders = dv.getInt32(base + 76, true);
  const numVerts = dv.getInt32(base + 80, true);
  const numTris = dv.getInt32(base + 84, true);
  const ofsTris = dv.getInt32(base + 88, true);
  const ofsShaders = dv.getInt32(base + 92, true);
  const ofsSt = dv.getInt32(base + 96, true);
  const ofsXyzNormal = dv.getInt32(base + 100, true);
  const ofsEnd = dv.getInt32(base + 104, true);
  return {
    numFrames, numShaders, numVerts, numTris,
    ofsTris, ofsShaders, ofsSt, ofsXyzNormal, ofsEnd,
  };
}

export function parseMD3(buffer) {
  const dv = new DataView(buffer);
  const hdr = readHeader(dv);
  const surfaces = [];

  let surfBase = hdr.ofsSurfaces;
  for (let s = 0; s < hdr.numSurfaces; s++) {
    const surf = readSurface(dv, surfBase);

    // First-frame vertices: 8 bytes each (x,y,z int16 + normal uint16)
    const positions = new Float32Array(surf.numVerts * 3);
    const normals = new Float32Array(surf.numVerts * 3);
    const vertBase = surfBase + surf.ofsXyzNormal;
    for (let v = 0; v < surf.numVerts; v++) {
      const vo = vertBase + v * 8;
      positions[v * 3 + 0] = dv.getInt16(vo + 0, true) * MD3_XYZ_SCALE;
      positions[v * 3 + 1] = dv.getInt16(vo + 2, true) * MD3_XYZ_SCALE;
      positions[v * 3 + 2] = dv.getInt16(vo + 4, true) * MD3_XYZ_SCALE;
      // md3 packed normal: byte0 = lat, byte1 = lng, each 0..255 mapping 0..2pi
      const lat = dv.getUint8(vo + 6) * (2 * Math.PI / 255);
      const lng = dv.getUint8(vo + 7) * (2 * Math.PI / 255);
      normals[v * 3 + 0] = Math.cos(lat) * Math.sin(lng);
      normals[v * 3 + 1] = Math.sin(lat) * Math.sin(lng);
      normals[v * 3 + 2] = Math.cos(lng);
    }

    // UVs
    const uvs = new Float32Array(surf.numVerts * 2);
    const stBase = surfBase + surf.ofsSt;
    for (let v = 0; v < surf.numVerts; v++) {
      uvs[v * 2 + 0] = dv.getFloat32(stBase + v * 8 + 0, true);
      uvs[v * 2 + 1] = 1.0 - dv.getFloat32(stBase + v * 8 + 4, true);
    }

    // Indices
    const indices = new Uint32Array(surf.numTris * 3);
    const triBase = surfBase + surf.ofsTris;
    for (let t = 0; t < surf.numTris; t++) {
      indices[t * 3 + 0] = dv.getInt32(triBase + t * 12 + 0, true);
      indices[t * 3 + 1] = dv.getInt32(triBase + t * 12 + 4, true);
      indices[t * 3 + 2] = dv.getInt32(triBase + t * 12 + 8, true);
    }

    surfaces.push({ positions, normals, uvs, indices });
    surfBase += surf.ofsEnd;
  }

  return { header: hdr, surfaces };
}

export class MD3Viewer {
  constructor(host) {
    this.host = host;
    this.turntable = true;
    this.clock = new THREE.Clock();

    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x111316);

    const w = host.clientWidth || 640;
    const h = host.clientHeight || 480;
    this.camera = new THREE.PerspectiveCamera(45, w / h, 0.01, 100);
    this.camera.position.set(2.4, 1.6, 2.4);

    this.renderer = new THREE.WebGLRenderer({ antialias: true });
    this.renderer.setPixelRatio(window.devicePixelRatio);
    this.renderer.setSize(w, h);
    host.appendChild(this.renderer.domElement);

    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;

    // Lights — ambient + key + rim (L85 rim-light preserved)
    this.ambient = new THREE.AmbientLight(0xffffff, 0.35);
    this.scene.add(this.ambient);

    this.key = new THREE.DirectionalLight(0xffffff, 1.0);
    this.key.position.set(3, 4, 2);
    this.scene.add(this.key);

    this.rim = new THREE.DirectionalLight(0x6ab6ff, 0.4);
    this.rim.position.set(-3, 2, -2); // behind-and-above for rim highlight
    this.scene.add(this.rim);

    // Pivot group (we rotate this for turntable)
    this.pivot = new THREE.Group();
    this.scene.add(this.pivot);

    this._animate = this._animate.bind(this);
    this._onResize = this._onResize.bind(this);
    window.addEventListener('resize', this._onResize);
    this._animate();
  }

  _onResize() {
    if (!this.renderer) return;
    const w = this.host.clientWidth || 640;
    const h = this.host.clientHeight || 480;
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h);
  }

  _animate() {
    this._raf = requestAnimationFrame(this._animate);
    const dt = this.clock.getDelta();
    if (this.turntable && this.pivot) {
      this.pivot.rotation.z += dt * 0.6; // md3 is z-up
    }
    this.controls.update();
    this.renderer.render(this.scene, this.camera);
  }

  setAmbient(v) { this.ambient.intensity = v; }
  setKey(v)     { this.key.intensity = v; }
  setRim(v)     { this.rim.intensity = v; }
  setTurntable(on) { this.turntable = !!on; }

  clearModel() {
    if (!this.pivot) return;
    for (const child of [...this.pivot.children]) {
      this.pivot.remove(child);
      if (child.geometry) child.geometry.dispose();
      if (child.material) child.material.dispose();
    }
  }

  async loadUrl(url) {
    const r = await fetch(url);
    if (!r.ok) throw new Error(`fetch ${url}: ${r.status}`);
    const buf = await r.arrayBuffer();
    this.loadBytes(buf);
  }

  loadBytes(buffer) {
    const parsed = parseMD3(buffer);
    this.clearModel();

    const group = new THREE.Group();
    // MD3 is z-up; rotate pivot so +y is up in world.
    group.rotation.x = -Math.PI / 2;

    for (const surf of parsed.surfaces) {
      const geom = new THREE.BufferGeometry();
      geom.setAttribute('position', new THREE.BufferAttribute(surf.positions, 3));
      geom.setAttribute('normal', new THREE.BufferAttribute(surf.normals, 3));
      geom.setAttribute('uv', new THREE.BufferAttribute(surf.uvs, 2));
      geom.setIndex(new THREE.BufferAttribute(surf.indices, 1));
      geom.computeBoundingSphere();
      geom.computeBoundingBox();

      const mat = new THREE.MeshStandardMaterial({
        color: 0xc8c8c8,
        roughness: 0.55,
        metalness: 0.1,
      });
      const mesh = new THREE.Mesh(geom, mat);
      group.add(mesh);
    }

    this.pivot.add(group);

    // Auto-fit to unit sphere
    const box = new THREE.Box3().setFromObject(group);
    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());
    group.position.sub(center);
    const radius = Math.max(size.x, size.y, size.z) * 0.5 || 1.0;
    const fit = 1.2 / radius;
    group.scale.setScalar(fit);

    this.camera.position.set(2.4, 1.6, 2.4);
    this.controls.target.set(0, 0, 0);
    this.controls.update();
  }

  dispose() {
    cancelAnimationFrame(this._raf);
    window.removeEventListener('resize', this._onResize);
    this.clearModel();
    this.renderer.dispose();
    if (this.renderer.domElement.parentNode === this.host) {
      this.host.removeChild(this.renderer.domElement);
    }
  }
}
