// cube moves for the page, same notation and same 3D math as cube.py
export const FACES = ['U', 'D', 'L', 'R', 'F', 'B'];
export const FACE_AXES = { U: [0, 1, 0], D: [0, -1, 0], L: [-1, 0, 0], R: [1, 0, 0], F: [0, 0, 1], B: [0, 0, -1] };
export const OPPOSITE = { U: 'D', D: 'U', L: 'R', R: 'L', F: 'B', B: 'F' };

export const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
export const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];

// "3Rw'" -> face R, layers 1-3, turns -1
export function parseMove(name) {
  const m = /^(\d*)([UDLRFB])(w?)(['2]?)$/.exec(name);
  if (!m) throw new Error('unknown move ' + name);
  const number = m[1] ? parseInt(m[1], 10) : null;
  const layers = [];
  if (m[3] === 'w') for (let k = 1; k <= (number || 2); k++) layers.push(k);
  else layers.push(number || 1);
  const turns = m[4] === "'" ? -1 : m[4] === '2' ? 2 : 1;
  return { face: m[2], layers, turns };
}

export function inverse(name) {
  if (name.endsWith("'")) return name.slice(0, -1);
  if (name.endsWith('2')) return name;
  return name + "'";
}

// clockwise (looking at the face) is -90 degrees around its axis
function rotate(v, axis, clockwise) {
  const d = dot(axis, v);
  const c = cross(axis, v);
  const s = clockwise ? -1 : 1;
  return [d * axis[0] + s * c[0], d * axis[1] + s * c[1], d * axis[2] + s * c[2]];
}

export class CubeModel {
  // centers and normals come from cube.py (sticker_geometry)
  constructor(n, centers, normals) {
    this.n = n;
    this.centers = centers;
    this.normals = normals;
    this.index = new Map(centers.map((c, i) => [c.join(','), i]));
    this.cache = new Map();
  }

  solved() {
    return this.centers.map((_, i) => i);
  }

  // where the sticker's piece is along an axis
  depth(p, axis) {
    const c = this.centers[p];
    const nr = this.normals[p];
    return (c[0] - nr[0]) * axis[0] + (c[1] - nr[1]) * axis[1] + (c[2] - nr[2]) * axis[2];
  }

  // depth of every layer the move turns
  layerDepths(name) {
    return parseMove(name).layers.map((k) => (this.n - 1) - 2 * (k - 1));
  }

  // new_state[q] = state[perm[q]], same as numpy's state[perm]
  permutation(name) {
    if (this.cache.has(name)) return this.cache.get(name);
    const { face, turns } = parseMove(name);
    const axis = FACE_AXES[face];
    const targets = this.layerDepths(name);
    const perm = this.solved();
    for (let p = 0; p < this.centers.length; p++) {
      if (!targets.includes(this.depth(p, axis))) continue;
      let v = this.centers[p];
      for (let t = 0; t < Math.abs(turns); t++) v = rotate(v, axis, turns > 0);
      perm[this.index.get(v.join(','))] = p;
    }
    this.cache.set(name, perm);
    return perm;
  }

  apply(state, name) {
    return this.permutation(name).map((p) => state[p]);
  }

  isSolved(state) {
    const size = this.n * this.n;
    for (let f = 0; f < 6; f++) {
      const color = Math.floor(state[f * size] / size);
      for (let k = 1; k < size; k++) if (Math.floor(state[f * size + k] / size) !== color) return false;
    }
    return true;
  }

  // name of the move that turns one layer, counted from a face (layer n is the opposite face)
  layerMoveName(face, layer, clockwise) {
    if (layer === this.n) {
      face = OPPOSITE[face];
      layer = 1;
      clockwise = !clockwise;
    }
    return (layer === 1 ? '' : layer) + face + (clockwise ? '' : "'");
  }
}
