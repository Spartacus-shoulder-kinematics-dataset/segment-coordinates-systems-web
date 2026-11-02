// Shared Three.js viewer. Scene units are millimetres and scene axes are the ISB global axes
// (X anterior, Y superior, Z right), so data is drawn without any conversion.
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { CSS2DObject, CSS2DRenderer } from "three/addons/renderers/CSS2DRenderer.js";

const UP = new THREE.Vector3(0, 1, 0);
const UNIT_SPHERE = new THREE.SphereGeometry(1, 20, 14);
const UNIT_CYLINDER = new THREE.CylinderGeometry(1, 1, 1, 14, 1).translate(0, 0.5, 0);
const UNIT_CONE = new THREE.ConeGeometry(1, 1, 18).translate(0, 0.5, 0);

export const v3 = (a) => new THREE.Vector3(a[0], a[1], a[2]);
const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
const scale = (a, s) => [a[0] * s, a[1] * s, a[2] * s];
const norm = (a) => Math.hypot(a[0], a[1], a[2]);

/** Colours come from CSS custom properties so the scene follows the page theme. */
export function palette() {
  const css = getComputedStyle(document.documentElement);
  const get = (name) => css.getPropertyValue(name).trim();
  return {
    bg: get("--scene-bg"),
    grid: get("--scene-grid"),
    bone: get("--bone"),
    boneMesh: get("--bone-mesh"),
    landmark: get("--landmark"),
    highlight: get("--highlight"),
    derived: get("--derived"),
    vector: get("--vector"),
    plane: get("--plane"),
    X: get("--ax-x"),
    Y: get("--ax-y"),
    Z: get("--ax-z"),
    e2: get("--ax-e2"),
    muted: get("--muted"),
  };
}

const materialCache = new Map();
function material(color, opacity = 1) {
  const key = `${color}|${opacity}`;
  if (!materialCache.has(key)) {
    materialCache.set(
      key,
      new THREE.MeshStandardMaterial({
        color: new THREE.Color(color),
        roughness: 0.55,
        metalness: 0.05,
        transparent: opacity < 1,
        opacity,
        depthWrite: opacity >= 1,
      }),
    );
  }
  return materialCache.get(key);
}

export class Viewer {
  constructor(container, { view = [1, 0.35, 0.8] } = {}) {
    this.container = container;
    this.view = view;
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.domElement.className = "viewer-canvas";
    container.appendChild(this.renderer.domElement);
    this.labels = new CSS2DRenderer();
    this.labels.domElement.className = "viewer-labels";
    container.appendChild(this.labels.domElement);

    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(35, 1, 1, 20000);
    this.scene.add(new THREE.HemisphereLight(0xffffff, 0x8a8a8a, 2.2));
    const sun = new THREE.DirectionalLight(0xffffff, 1.6);
    sun.position.set(600, 1000, 500);
    this.scene.add(sun);
    this.content = new THREE.Group();
    this.scene.add(this.content);

    this.controls = new OrbitControls(this.camera, this.labels.domElement);
    this.controls.enableDamping = false;
    this.controls.addEventListener("change", () => this.render());
    this.fitted = false;
    this.size = 150;
    this.showLabels = true;

    this.resizeObserver = new ResizeObserver(() => this.resize());
    this.resizeObserver.observe(container);
    this.resize();
  }

  /** Stroke thickness scales with the size of what is displayed (hand vs. whole shoulder). */
  get k() {
    return Math.min(2.2, Math.max(0.28, this.size / 170));
  }

  resize() {
    const w = this.container.clientWidth, h = this.container.clientHeight;
    if (!w || !h) return;
    this.renderer.setSize(w, h, false);
    this.labels.setSize(w, h);
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.render();
  }

  clear() {
    for (const obj of [...this.content.children]) {
      obj.traverse((o) => {
        if (o.geometry && ![UNIT_SPHERE, UNIT_CYLINDER, UNIT_CONE].includes(o.geometry)) o.geometry.dispose();
      });
      this.content.remove(obj);
    }
    const p = palette();
    this.palette = p;
    this.scene.background = new THREE.Color(p.bg);
  }

  /** Frame the camera on points the first time (or when forced), keeping the user's view afterwards. */
  fit(points, force = false) {
    const box = new THREE.Box3();
    points.forEach((p) => box.expandByPoint(v3(p)));
    const sphere = box.getBoundingSphere(new THREE.Sphere());
    this.size = Math.max(sphere.radius * 2, 40);
    if (this.fitted && !force) return;
    const dist = (sphere.radius * 1.25) / Math.sin(THREE.MathUtils.degToRad(this.camera.fov / 2));
    const dir = v3(this.view).normalize();
    this.controls.target.copy(sphere.center);
    this.camera.position.copy(sphere.center).addScaledVector(dir, dist);
    this.camera.near = dist / 100;
    this.camera.far = dist * 20;
    this.camera.updateProjectionMatrix();
    this.controls.update();
    this.fitted = true;
  }

  label(pos, text, cls = "") {
    if (!this.showLabels && !cls.includes("keep")) return;
    const div = document.createElement("div");
    div.className = `lbl ${cls}`;
    div.innerHTML = text;
    const obj = new CSS2DObject(div);
    obj.position.copy(v3(pos));
    this.content.add(obj);
    return obj;
  }

  point(pos, { color, radius = 4, opacity = 1, label, labelClass = "" } = {}) {
    const mesh = new THREE.Mesh(UNIT_SPHERE, material(color ?? this.palette.landmark, opacity));
    mesh.scale.setScalar(radius * this.k);
    mesh.position.copy(v3(pos));
    this.content.add(mesh);
    if (label) this.label(add(pos, [0, radius * this.k * 2.2, 0]), label, labelClass);
    return mesh;
  }

  cylinder(a, b, { color, radius = 1.3, opacity = 1 } = {}) {
    const dir = v3(b).sub(v3(a));
    const len = dir.length();
    if (len < 1e-6) return;
    const mesh = new THREE.Mesh(UNIT_CYLINDER, material(color ?? this.palette.bone, opacity));
    mesh.scale.set(radius * this.k, len, radius * this.k);
    mesh.quaternion.setFromUnitVectors(UP, dir.normalize());
    mesh.position.copy(v3(a));
    this.content.add(mesh);
    return mesh;
  }

  /** Arrow from `origin` along `vec` (its true length). */
  arrow(origin, vec, { color, radius = 1.6, opacity = 1, dashed = false, label, labelClass = "" } = {}) {
    const len = norm(vec);
    if (len < 1e-6) return;
    const dir = scale(vec, 1 / len);
    const head = Math.min(len * 0.35, 11 * this.k);
    const shaftEnd = add(origin, scale(dir, len - head));
    if (dashed) {
      const n = Math.max(3, Math.round((len - head) / (7 * this.k)));
      for (let i = 0; i < n; i += 2) {
        const a = add(origin, scale(dir, ((len - head) * i) / n));
        const b = add(origin, scale(dir, ((len - head) * Math.min(i + 1, n)) / n));
        this.cylinder(a, b, { color, radius, opacity });
      }
    } else {
      this.cylinder(origin, shaftEnd, { color, radius, opacity });
    }
    const cone = new THREE.Mesh(UNIT_CONE, material(color, opacity));
    cone.scale.set(radius * 2.6 * this.k, head, radius * 2.6 * this.k);
    cone.quaternion.setFromUnitVectors(UP, v3(dir));
    cone.position.copy(v3(shaftEnd));
    this.content.add(cone);
    if (label) this.label(add(origin, scale(dir, len + 7 * this.k)), label, labelClass);
  }

  /** Coordinate frame: axes = {X, Y, Z} unit vectors. */
  frame(origin, axes, { length = 60, opacity = 1, radius = 1.8, dashed = false, suffix = "", names = ["X", "Y", "Z"] } = {}) {
    ["X", "Y", "Z"].forEach((a, i) =>
      this.arrow(origin, scale(axes[a], length), {
        color: this.palette[a],
        radius,
        opacity,
        dashed,
        label: `${names[i]}${suffix}`,
        labelClass: `ax-${a.toLowerCase()}`,
      }),
    );
    this.point(origin, { color: this.palette.muted, radius: 2.4, opacity });
  }

  /** Translucent triangle through three points. */
  plane(a, b, c, { color, opacity = 0.18 } = {}) {
    const geom = new THREE.BufferGeometry();
    geom.setAttribute("position", new THREE.Float32BufferAttribute([...a, ...b, ...c], 3));
    geom.computeVertexNormals();
    const mat = new THREE.MeshBasicMaterial({
      color: new THREE.Color(color ?? this.palette.plane),
      transparent: true,
      opacity,
      side: THREE.DoubleSide,
      depthWrite: false,
    });
    this.content.add(new THREE.Mesh(geom, mat));
  }

  /** Arc of `angle` radians about unit `axis`, starting along unit `from`, centred at `center`. */
  arc(center, axis, from, angle, radius, { color, label, labelClass = "" } = {}) {
    if (Math.abs(angle) < 1e-4) return;
    const ax = v3(axis).normalize();
    const start = v3(from);
    const n = Math.max(8, Math.ceil(Math.abs(angle) / 0.08));
    const pts = [];
    for (let i = 0; i <= n; i++) {
      const q = new THREE.Quaternion().setFromAxisAngle(ax, (angle * i) / n);
      pts.push(start.clone().applyQuaternion(q).multiplyScalar(radius).add(v3(center)));
    }
    const curve = new THREE.CatmullRomCurve3(pts);
    const tube = new THREE.TubeGeometry(curve, n * 2, 0.9 * this.k, 8, false);
    this.content.add(new THREE.Mesh(tube, material(color)));
    const end = pts[pts.length - 1];
    const tangent = curve.getTangent(1);
    const cone = new THREE.Mesh(UNIT_CONE, material(color));
    cone.scale.set(2.6 * this.k, 6 * this.k, 2.6 * this.k);
    cone.quaternion.setFromUnitVectors(UP, tangent);
    cone.position.copy(end);
    this.content.add(cone);
    if (label) this.label(pts[Math.floor(n / 2)].toArray(), label, labelClass);
  }

  render() {
    this.renderer.render(this.scene, this.camera);
    this.labels.render(this.scene, this.camera);
  }

  dispose() {
    this.resizeObserver.disconnect();
    this.controls.dispose();
    this.clear();
    this.renderer.dispose();
    this.renderer.forceContextLoss();
    this.container.innerHTML = "";
  }
}

// --- bone meshes -----------------------------------------------------------------------------------------
const meshCache = new Map(); // url -> { geometry, waiters }

/**
 * Geometry of a bone mesh group (float32 xyz then uint32 triangle indices), or null while it loads;
 * `onReady` is called once it is available.
 */
export function boneGeometry(entry, onReady) {
  let item = meshCache.get(entry.file);
  if (!item) {
    item = { geometry: null, waiters: new Set() };
    meshCache.set(entry.file, item);
    fetch(entry.file)
      .then((r) => r.arrayBuffer())
      .then((buf) => {
        const g = new THREE.BufferGeometry();
        g.setAttribute("position", new THREE.BufferAttribute(new Float32Array(buf, 0, entry.vertices * 3), 3));
        g.setIndex(new THREE.BufferAttribute(new Uint32Array(buf, entry.vertices * 12, entry.triangles * 3), 1));
        g.computeVertexNormals();
        item.geometry = g;
        item.waiters.forEach((fn) => fn());
        item.waiters.clear();
      })
      .catch((e) => console.warn(`could not load ${entry.file}`, e));
  }
  if (!item.geometry) item.waiters.add(onReady);
  return item.geometry;
}

/** Bounding-box corners of mesh groups, mirrored for the left side. */
export function meshCorners(entries, side) {
  const s = side === "L" ? -1 : 1;
  return entries.flatMap((e) => [
    [e.min[0], e.min[1], e.min[2] * s],
    [e.max[0], e.max[1], e.max[2] * s],
  ]);
}

const boneMaterials = new Map();
function boneMaterial(color, opacity) {
  const key = `${color}|${opacity}`;
  if (!boneMaterials.has(key)) {
    boneMaterials.set(
      key,
      new THREE.MeshStandardMaterial({
        color: new THREE.Color(color),
        roughness: 0.75,
        metalness: 0,
        transparent: opacity < 1,
        opacity,
        depthWrite: opacity >= 1,
      }),
    );
  }
  return boneMaterials.get(key);
}

Viewer.prototype.bone = function (geometry, { opacity = 1, rotation = null, translation = [0, 0, 0], mirror = false } = {}) {
  const mesh = new THREE.Mesh(geometry, boneMaterial(this.palette.boneMesh, opacity));
  mesh.matrixAutoUpdate = false;
  const R = rotation ?? [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
  const m = new THREE.Matrix4().set(
    R[0][0], R[0][1], R[0][2], translation[0],
    R[1][0], R[1][1], R[1][2], translation[1],
    R[2][0], R[2][1], R[2][2], translation[2],
    0, 0, 0, 1,
  );
  if (mirror) m.multiply(new THREE.Matrix4().makeScale(1, 1, -1));
  mesh.matrix.copy(m);
  mesh.renderOrder = -1;
  this.content.add(mesh);
  return mesh;
};

export const BONE_MODES = [
  { value: "solid", label: "Solid" },
  { value: "ghost", label: "Ghost" },
  { value: "off", label: "Off" },
];
export const boneOpacity = (mode) => (mode === "solid" ? 1 : mode === "ghost" ? 0.5 : 0);

// --- lazy mounting: WebGL contexts only exist for viewers near the viewport -----------------------
const MAX_ACTIVE = 8;
const active = [];

/**
 * Mount a viewer lazily. `draw(viewer)` must redraw everything from the caller's state.
 * Returns a handle whose redraw() is a no-op while the viewer is off screen.
 */
export function lazyViewer(container, draw, options = {}) {
  const handle = {
    viewer: null,
    redraw() {
      if (!this.viewer) return;
      this.viewer.clear();
      draw(this.viewer);
      this.viewer.render();
    },
    refit() {
      if (this.viewer) {
        this.viewer.fitted = false;
        this.redraw();
      }
    },
  };
  const mount = () => {
    if (handle.viewer) return;
    while (active.length >= MAX_ACTIVE) unmount(active.shift());
    handle.viewer = new Viewer(container, options);
    active.push(handle);
    handle.redraw();
  };
  const unmount = (h) => {
    if (!h.viewer) return;
    h.viewer.dispose();
    h.viewer = null;
    const i = active.indexOf(h);
    if (i >= 0) active.splice(i, 1);
  };
  new IntersectionObserver(
    (entries) => entries.forEach((e) => (e.isIntersecting ? mount() : unmount(handle))),
    { rootMargin: "300px 0px" },
  ).observe(container);
  window.addEventListener("themechange", () => handle.redraw());
  return handle;
}
