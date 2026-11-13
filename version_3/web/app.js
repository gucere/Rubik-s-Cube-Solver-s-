import * as THREE from 'three';
import { OrbitControls } from './vendor/OrbitControls.js';
import { CubeModel, FACES, FACE_AXES, OPPOSITE, dot, cross, inverse, parseMove } from './moves.js';

// colors in the same order as the faces in the state: U L F R B D
const COLORS = [0xf5f5f5, 0xff8a1f, 0x18a957, 0xe0322f, 0x2766e8, 0xffd21f];
const COLOR_NAMES = ['White', 'Orange', 'Green', 'Red', 'Blue', 'Yellow'];
const BLANK_COLOR = 0x50566a;
const METHOD_NAMES = { kociemba: 'Kociemba', beam: 'Beam search', greedy: 'Greedy search', fastest: 'Solve' };

const $ = (id) => document.getElementById(id);

// cube data
let n = 3;
let model = null;   // moves and geometry (moves.js)
let centers = [];   // 3D position of every sticker (times 2, so all integers)
let normals = [];   // outward direction of every sticker
let state = [];     // sticker id at every position, id / (n*n) is its color
let paint = null;   // color of every square while painting (-1 = blank)
let mode = 'play';
let history = [];   // moves the user made, for undo
let busy = false;

// solution being shown
let solution = null;
let startState = null;
let stepIndex = 0;
let playing = false;

// ---------- three.js scene ----------

const canvas = $('canvas');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
renderer.setPixelRatio(window.devicePixelRatio);
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(35, 1, 0.1, 1000);
const controls = new OrbitControls(camera, canvas);
controls.enablePan = false;
controls.enableDamping = true;
scene.add(new THREE.HemisphereLight(0xffffff, 0x8890a0, 2.2));
const light = new THREE.DirectionalLight(0xffffff, 1.2);
light.position.set(0.5, 1, 1);
camera.add(light);
scene.add(camera);

const cubeGroup = new THREE.Group();
scene.add(cubeGroup);
let cubies = [];
let stickers = [];

const bodyMaterial = new THREE.MeshStandardMaterial({ color: 0x101217, roughness: 0.7 });
const stickerMaterials = COLORS.map((c) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.45 }));
const blankMaterial = new THREE.MeshStandardMaterial({ color: BLANK_COLOR, roughness: 0.6 });
const bodyGeometry = new THREE.BoxGeometry(0.98, 0.98, 0.98);
const stickerGeometry = roundedSquare(0.84, 0.12);

function roundedSquare(size, radius) {
  const s = size / 2;
  const shape = new THREE.Shape();
  shape.moveTo(-s + radius, -s);
  shape.lineTo(s - radius, -s);
  shape.quadraticCurveTo(s, -s, s, -s + radius);
  shape.lineTo(s, s - radius);
  shape.quadraticCurveTo(s, s, s - radius, s);
  shape.lineTo(-s + radius, s);
  shape.quadraticCurveTo(-s, s, -s, s - radius);
  shape.lineTo(-s, -s + radius);
  shape.quadraticCurveTo(-s, -s, -s + radius, -s);
  return new THREE.ShapeGeometry(shape);
}

function buildScene() {
  cubeGroup.clear();
  cubies = [];
  stickers = [];
  const byKey = new Map();
  for (let p = 0; p < centers.length; p++) {
    const c = centers[p];
    const nr = normals[p];
    const piece = [c[0] - nr[0], c[1] - nr[1], c[2] - nr[2]];
    const key = piece.join(',');
    let group = byKey.get(key);
    if (!group) {
      group = new THREE.Group();
      group.userData.piece = piece;
      group.position.set(piece[0] / 2, piece[1] / 2, piece[2] / 2);
      group.add(new THREE.Mesh(bodyGeometry, bodyMaterial));
      cubeGroup.add(group);
      byKey.set(key, group);
      cubies.push(group);
    }
    const sticker = new THREE.Mesh(stickerGeometry, stickerMaterials[0]);
    sticker.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), new THREE.Vector3(...nr));
    sticker.position.set(nr[0] * 0.495, nr[1] * 0.495, nr[2] * 0.495);
    sticker.userData.p = p;
    group.add(sticker);
    stickers.push(sticker);
  }
  const distance = n * 3.1 + 2;
  camera.position.set(0.95, 0.8, 1.3).normalize().multiplyScalar(distance);
  controls.minDistance = n * 1.4;
  controls.maxDistance = n * 8;
  controls.update();
  recolor();
}

function recolor() {
  for (let p = 0; p < stickers.length; p++) {
    if (mode === 'paint') {
      stickers[p].material = paint[p] < 0 ? blankMaterial : stickerMaterials[paint[p]];
    } else {
      stickers[p].material = stickerMaterials[Math.floor(state[p] / (n * n))];
    }
  }
}

function resize() {
  const { clientWidth: w, clientHeight: h } = $('viewport');
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}
new ResizeObserver(resize).observe($('viewport'));

renderer.setAnimationLoop(() => {
  controls.update();
  renderer.render(scene, camera);
});

// ---------- moves ----------

const applyMove = (s, name) => model.apply(s, name);
const isSolved = (s) => model.isSolved(s);

// turn the layer on screen, then update the colors
function animateMove(name, ms) {
  if (ms <= 0) {
    state = applyMove(state, name);
    recolor();
    return Promise.resolve();
  }
  return new Promise((resolve) => {
    const { face, turns } = parseMove(name);
    const axis = FACE_AXES[face];
    const targets = model.layerDepths(name);
    const pivot = new THREE.Group();
    cubeGroup.add(pivot);
    for (const cubie of cubies) {
      if (targets.includes(dot(cubie.userData.piece, axis))) pivot.attach(cubie);
    }
    const axisVector = new THREE.Vector3(...axis);
    const angle = -Math.PI / 2 * turns;
    const duration = Math.abs(turns) === 2 ? ms * 1.4 : ms;
    const start = performance.now();

    function frame(now) {
      const t = Math.min(1, (now - start) / duration);
      const eased = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
      pivot.setRotationFromAxisAngle(axisVector, angle * eased);
      if (t < 1) {
        requestAnimationFrame(frame);
        return;
      }
      for (const cubie of [...pivot.children]) {
        cubeGroup.add(cubie);
        const piece = cubie.userData.piece;
        cubie.position.set(piece[0] / 2, piece[1] / 2, piece[2] / 2);
        cubie.quaternion.identity();
      }
      cubeGroup.remove(pivot);
      state = applyMove(state, name);
      recolor();
      resolve();
    }
    requestAnimationFrame(frame);
  });
}

function moveDuration() {
  return 760 - parseInt($('speed').value, 10) * 70;
}

// a move the user made by hand
async function userMove(name) {
  if (busy || mode !== 'play') return;
  clearSolution();
  history.push(name);
  busy = true;
  await animateMove(name, Math.min(moveDuration(), 260));
  busy = false;
  if (isSolved(state) && history.length) setStatus('Solved!', 'ok');
}

// ---------- loading a cube ----------

async function newCube(size) {
  if (busy) return;
  size = Math.max(2, Math.min(12, parseInt(size, 10) || 3));
  $('size').value = size;
  const data = await (await fetch(`/api/geometry?n=${size}`)).json();
  n = size;
  centers = data.centers;
  normals = data.normals;
  model = new CubeModel(n, centers, normals);
  state = model.solved();
  history = [];
  clearSolution();
  if (mode === 'paint') paint = state.map((id) => Math.floor(id / (n * n)));
  buildScene();
  updateSolveOptions();
  updatePalette();
  setStatus('');
}

// ---------- picking stickers with the mouse ----------

const raycaster = new THREE.Raycaster();
let drag = null;
let painting = false;

function pick(event) {
  const rect = canvas.getBoundingClientRect();
  const mouse = new THREE.Vector2(
    ((event.clientX - rect.left) / rect.width) * 2 - 1,
    -((event.clientY - rect.top) / rect.height) * 2 + 1,
  );
  raycaster.setFromCamera(mouse, camera);
  const hit = raycaster.intersectObjects(stickers, false)[0];
  return hit ? hit.object.userData.p : null;
}

function toScreen(v) {
  const projected = new THREE.Vector3(...v).project(camera);
  return [projected.x, -projected.y];
}

// which layer turn a drag on sticker p means
function moveFromDrag(p, dx, dy) {
  const nr = normals[p];
  const center = centers[p].map((x) => x / 2);
  const from = toScreen(center);
  const length = Math.hypot(dx, dy);
  let best = null;
  let bestScore = -Infinity;
  for (const axis of [[1, 0, 0], [0, 1, 0], [0, 0, 1]]) {
    if (dot(axis, nr) !== 0) continue;
    for (const sign of [1, -1]) {
      const t = axis.map((x) => x * sign);
      const to = toScreen(center.map((x, i) => x + t[i] * 0.5));
      const sx = to[0] - from[0];
      const sy = to[1] - from[1];
      const score = (sx * dx + sy * dy) / (Math.hypot(sx, sy) * length || 1);
      if (score > bestScore) { bestScore = score; best = t; }
    }
  }
  // moving toward t turns the layer +90 degrees around normal x t
  const turnAxis = cross(nr, best);
  const face = FACES.find((f) => dot(FACE_AXES[f], turnAxis) === 1);
  const layer = ((n - 1) - model.depth(p, FACE_AXES[face])) / 2 + 1;
  return model.layerMoveName(face, layer, false);
}

// capture, so we run before the camera controls and can stop them
$('viewport').addEventListener('pointerdown', (event) => {
  if (event.target !== canvas || event.button !== 0) return;
  const p = pick(event);
  if (p === null) return;
  controls.enabled = false;
  if (mode === 'paint') {
    painting = true;
    paintSquare(p);
  } else if (!busy) {
    drag = { p, x: event.clientX, y: event.clientY };
  }
}, { capture: true });

window.addEventListener('pointermove', (event) => {
  if (painting) {
    const p = pick(event);
    if (p !== null) paintSquare(p);
    return;
  }
  if (!drag) return;
  const rect = canvas.getBoundingClientRect();
  const dx = (event.clientX - drag.x) / rect.width * 2;
  const dy = (event.clientY - drag.y) / rect.height * 2;
  if (Math.hypot(event.clientX - drag.x, event.clientY - drag.y) < 12) return;
  const move = moveFromDrag(drag.p, dx, dy);
  drag = null;
  userMove(move);
});

window.addEventListener('pointerup', () => {
  drag = null;
  painting = false;
  controls.enabled = true;
});

window.addEventListener('keydown', (event) => {
  if (event.target.matches('input, select') || event.ctrlKey || event.metaKey || event.altKey) return;
  const face = event.key.toUpperCase();
  if (FACES.includes(face) && event.code === `Key${face}`) {
    userMove(face + (event.shiftKey ? "'" : ''));
    event.preventDefault();
  }
});

// ---------- play tools ----------

$('new-cube').addEventListener('click', () => newCube($('size').value));
$('size').addEventListener('change', () => newCube($('size').value));

$('scramble').addEventListener('click', async () => {
  if (busy || mode !== 'play') return;
  const count = Math.max(1, Math.min(300, parseInt($('scramble-count').value, 10) || 25));
  const moves = [];
  let last = null;
  while (moves.length < count) {
    const face = FACES[Math.floor(Math.random() * 6)];
    if (last && (face === last || face === OPPOSITE[last])) continue;
    const layer = 1 + Math.floor(Math.random() * Math.max(1, Math.floor(n / 2)));
    const suffix = ['', "'", '2'][Math.floor(Math.random() * 3)];
    moves.push((layer === 1 ? '' : layer) + face + suffix);
    last = face;
  }
  clearSolution();
  history.push(...moves);
  busy = true;
  const ms = count > 40 ? 0 : 90;
  for (const move of moves) await animateMove(move, ms);
  busy = false;
  setStatus(`Scrambled with ${count} moves`);
});

$('undo').addEventListener('click', async () => {
  if (busy || mode !== 'play' || !history.length) return;
  clearSolution();
  busy = true;
  await animateMove(inverse(history.pop()), 200);
  busy = false;
});

// ---------- paint mode ----------

let paintColor = 0;

function setMode(newMode) {
  mode = newMode;
  document.querySelectorAll('.tab').forEach((t) => t.classList.toggle('active', t.dataset.mode === mode));
  $('play-tools').hidden = mode !== 'play';
  $('paint-tools').hidden = mode !== 'paint';
  updateHint();
  recolor();
}

document.querySelectorAll('.tab').forEach((tab) => tab.addEventListener('click', async () => {
  if (busy || tab.dataset.mode === mode) return;
  if (tab.dataset.mode === 'paint') {
    clearSolution();
    paint = state.map((id) => Math.floor(id / (n * n)));
    setMode('paint');
    updatePalette();
    setStatus('');
  } else {
    await usePaintedCube();
  }
}));

function buildPalette() {
  const palette = $('palette');
  const entries = COLORS.map((c, i) => ({ i, css: '#' + c.toString(16).padStart(6, '0'), name: COLOR_NAMES[i] }));
  entries.push({ i: -1, css: '#' + BLANK_COLOR.toString(16), name: 'Erase' });
  for (const e of entries) {
    const button = document.createElement('button');
    button.className = 'swatch';
    button.style.background = e.css;
    button.title = e.name;
    button.dataset.color = e.i;
    button.appendChild(document.createElement('span'));
    button.addEventListener('click', () => { paintColor = e.i; updatePalette(); });
    palette.appendChild(button);
  }
}

function updatePalette() {
  document.querySelectorAll('.swatch').forEach((b) => {
    const color = parseInt(b.dataset.color, 10);
    b.classList.toggle('active', color === paintColor);
    const label = b.querySelector('span');
    if (!paint) return;
    const count = paint.filter((c) => c === color).length;
    label.textContent = color < 0 ? `${count} left` : `${count}/${n * n}`;
    label.classList.toggle('done', color >= 0 && count === n * n);
  });
}

function paintSquare(p) {
  if (paint[p] === paintColor) return;
  paint[p] = paintColor;
  stickers[p].material = paintColor < 0 ? blankMaterial : stickerMaterials[paintColor];
  updatePalette();
}

$('blank').addEventListener('click', () => { paint = paint.map(() => -1); recolor(); updatePalette(); });
$('solved-colors').addEventListener('click', () => {
  paint = paint.map((_, i) => Math.floor(i / (n * n)));
  recolor();
  updatePalette();
});
$('paint-done').addEventListener('click', usePaintedCube);

// check the painted colors with python and turn them into a cube we can play with
async function usePaintedCube() {
  const result = await post('/api/from_colors', { n, colors: paint });
  if (result.error) {
    setStatus("This isn't a valid cube: " + result.error, 'error');
    showToast("This isn't a valid cube: " + result.error);
    return false;
  }
  state = result.state;
  history = [];
  $('toast').hidden = true;
  setMode('play');
  setStatus('Painted cube is ready', 'ok');
  return true;
}

// ---------- solving ----------

function updateSolveOptions() {
  const kociemba = $('method').querySelector('option[value="kociemba"]');
  kociemba.disabled = n > 3;
  kociemba.textContent = n > 3 ? 'Kociemba (2x2 and 3x3 only)' : 'Kociemba';
  if (n > 3 && $('method').value === 'kociemba') $('method').value = 'beam';
  $('fast-note').textContent = n <= 3
    ? "Uses Kociemba's algorithm, solves any position in about a second."
    : 'Big cubes have no exact solver yet, so this uses beam search. It handles lightly scrambled cubes.';
  updateMethodFields();
}

function updateMethodFields() {
  const method = $('method').value;
  $('solve-with').textContent = 'Solve with ' + METHOD_NAMES[method];
  $('distance').disabled = method === 'kociemba';
  $('beam-width').disabled = method !== 'beam';
}
$('method').addEventListener('change', updateMethodFields);

$('solve-fast').addEventListener('click', () => solve('fastest'));
$('solve-with').addEventListener('click', () => solve($('method').value));
$('cancel').addEventListener('click', () => post('/api/cancel', {}));

async function solve(method) {
  if (busy) return;
  if (mode === 'paint' && !(await usePaintedCube())) return;
  if (isSolved(state)) {
    setStatus('The cube is already solved', 'ok');
    return;
  }
  clearSolution();
  busy = true;
  setSolving(true);
  setStatus(`Solving with ${METHOD_NAMES[method]}...`);
  const result = await post('/api/solve', {
    n,
    state,
    method,
    distance: $('distance').value,
    beam_width: parseInt($('beam-width').value, 10) || 100,
    time_limit: parseFloat($('time-limit').value) || 30,
  });
  busy = false;
  setSolving(false);
  const used = METHOD_NAMES[result.method] || METHOD_NAMES[method];
  if (result.error) {
    setStatus(`${used}: ${result.error}${result.seconds !== undefined ? ` (${result.seconds}s)` : ''}`, 'error');
    return;
  }
  solution = result.moves;
  startState = state.slice();
  stepIndex = 0;
  history = [];
  setStatus(`${used} found ${solution.length} moves in ${result.seconds}s`, 'ok');
  showSteps();
}

function setSolving(on) {
  $('cancel').hidden = !on;
  ['solve-fast', 'solve-with', 'scramble', 'undo', 'new-cube'].forEach((id) => { $(id).disabled = on; });
}

// ---------- steps ----------

function showSteps() {
  const list = $('moves');
  list.innerHTML = '';
  solution.forEach((move, i) => {
    const item = document.createElement('li');
    item.textContent = move;
    item.title = `Jump to after move ${i + 1}`;
    item.addEventListener('click', () => jumpTo(i + 1));
    list.appendChild(item);
  });
  $('steps-section').hidden = false;
  updateSteps();
}

function updateSteps() {
  if (!solution) return;
  $('step-count').textContent = `${stepIndex} / ${solution.length}`;
  [...$('moves').children].forEach((item, i) => {
    item.classList.toggle('done', i < stepIndex);
    item.classList.toggle('current', i === stepIndex);
  });
  $('play').textContent = playing ? '⏸ Pause' : stepIndex === solution.length ? '↺ Replay' : '▶ Play';
  $('first').disabled = $('prev').disabled = stepIndex === 0;
  $('next').disabled = $('last').disabled = stepIndex === solution.length;
}

function clearSolution() {
  solution = null;
  playing = false;
  $('steps-section').hidden = true;
}

async function stepForward() {
  if (busy || !solution || stepIndex >= solution.length) return false;
  busy = true;
  await animateMove(solution[stepIndex], moveDuration());
  stepIndex++;
  busy = false;
  updateSteps();
  return true;
}

async function stepBack() {
  if (busy || !solution || stepIndex <= 0) return;
  busy = true;
  stepIndex--;
  await animateMove(inverse(solution[stepIndex]), moveDuration());
  busy = false;
  updateSteps();
}

function jumpTo(index) {
  if (busy || !solution) return;
  playing = false;
  state = startState.slice();
  for (let i = 0; i < index; i++) state = applyMove(state, solution[i]);
  stepIndex = index;
  recolor();
  updateSteps();
}

async function play() {
  if (!solution) return;
  if (playing) { playing = false; updateSteps(); return; }
  if (stepIndex === solution.length) jumpTo(0);
  playing = true;
  updateSteps();
  while (playing && solution && stepIndex < solution.length) {
    if (!(await stepForward())) break;
  }
  playing = false;
  updateSteps();
}

$('next').addEventListener('click', () => { playing = false; stepForward(); });
$('prev').addEventListener('click', () => { playing = false; stepBack(); });
$('first').addEventListener('click', () => jumpTo(0));
$('last').addEventListener('click', () => jumpTo(solution.length));
$('play').addEventListener('click', play);

// ---------- small helpers ----------

async function post(url, body) {
  try {
    const response = await fetch(url, { method: 'POST', body: JSON.stringify(body) });
    return await response.json();
  } catch (e) {
    return { error: 'lost connection to the solver (' + e.message + ')' };
  }
}

function setStatus(text, kind = '') {
  $('status').textContent = text;
  $('status').className = 'status ' + kind;
}

let toastTimer = null;
function showToast(text) {
  $('toast').textContent = text;
  $('toast').hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { $('toast').hidden = true; }, 5000);
}

function updateHint() {
  $('hint').textContent = mode === 'paint'
    ? 'Paint mode: click or drag over squares to color them'
    : 'Drag stickers to turn layers, drag empty space to rotate the view';
}

buildPalette();
updateHint();
newCube(3);
