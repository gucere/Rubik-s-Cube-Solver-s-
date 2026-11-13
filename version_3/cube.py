import random
from functools import lru_cache
import numpy as np

FACES = ['U', 'D', 'L', 'R', 'F', 'B']
# outward direction of every face
FACE_AXES = {'U': (0, 1, 0), 'D': (0, -1, 0), 'L': (-1, 0, 0), 'R': (1, 0, 0), 'F': (0, 0, 1), 'B': (0, 0, -1)}
# colors are numbered in the same order as the faces in the state: U L F R B D
COLOR_NAMES = ['white', 'orange', 'green', 'red', 'blue', 'yellow']
OPPOSITE_COLOR = {0: 5, 5: 0, 1: 3, 3: 1, 2: 4, 4: 2}

class Cube:
    # initialize a cube with NxNxN
    def __init__(self, n):
        if n < 2:
            raise ValueError("cube size must be at least 2")
        self.n = n
        # state is a flat array of sticker ids, sticker id // (n*n) is its color
        self.state = np.arange(6 * n * n)
        self.moves, self.search_moves = build_moves(n)
        self.solution_cubes = build_solution_cubes(n)

    # get current state of the cube
    def get_state(self):
        return self.state.copy()

    # define a specific state
    def define_state(self, state):
        self.state = np.array(state)

    # define the cube from the color of every square (0-5, see COLOR_NAMES)
    def define_colors(self, colors):
        self.state = state_from_colors(self.n, colors)

    # color of every square
    def get_colors(self):
        return self.state // (self.n * self.n)

    # scramble the cube randomly for a specific number of moves
    def scramble(self, moves=30):
        scramble_moves = [random.choice(self.all_moves()) for _ in range(moves)]
        for move in scramble_moves:
            self.perform_move(move)
        return scramble_moves

    # all possible move set
    def all_moves(self):
        return list(self.search_moves)

    # all possible solutions (the solved cube in all 24 orientations)
    def all_solution_cubes(self):
        return self.solution_cubes

    # state you get after doing a move, without changing the cube
    def apply_move(self, state, move):
        return state[self.moves[move]]

    # perform a move (or a space separated list of moves) on the cube
    def perform_move(self, move):
        for m in move.split():
            self.state = self.apply_move(self.state, m)

    # solved means every face has a single color
    def is_solved(self, state=None):
        if state is None:
            state = self.state
        colors = (state // (self.n * self.n)).reshape(6, -1)
        return bool((colors == colors[:, :1]).all())

    # print current state
    def show(self):
        c = self.to_supercube()
        c.show()
        c.show(colors=True)

    # 3D current state
    def show_3d(self):
        self.to_supercube().show_3d()

    # supercube object with the same state (only used for drawing in the terminal)
    def to_supercube(self):
        from kociemba_solver import import_supercube
        c = import_supercube().NCube(self.n)
        c.set_state((self.state + 1).reshape(6, self.n, self.n).tolist())
        return c


# 3D position (times 2, so everything is an integer) and outward direction of every sticker,
# in the same order as supercube's state: faces U L F R B D, each row by row like the usual cube net
@lru_cache(maxsize=None)
def sticker_geometry(n):
    centers = []
    normals = []
    for face in range(6):
        for i in range(n):
            for j in range(n):
                a, b = 2 * i - (n - 1), 2 * j - (n - 1)
                centers.append([(b, n, a), (-n, -a, b), (b, -a, n), (n, -a, -b), (-b, -a, -n), (b, -n, -a)][face])
                normals.append([(0, 1, 0), (-1, 0, 0), (0, 0, 1), (1, 0, 0), (0, 0, -1), (0, -1, 0)][face])
    return np.array(centers), np.array(normals)

# turn one or more layers of a face a quarter turn, as a permutation of the state
def layer_turns_to_permutation(n, face, layers, clockwise=True):
    centers, normals = sticker_geometry(n)
    axis = np.array(FACE_AXES[face])
    depth = (centers - normals) @ axis  # where the sticker's piece is along the axis
    in_layer = np.isin(depth, [(n - 1) - 2 * (layer - 1) for layer in layers])

    # clockwise (looking at the face) is -90 degrees around the face's axis
    sign = 1 if clockwise else -1
    moved = centers.copy()
    moved[in_layer] = (centers[in_layer] @ axis)[:, None] * axis - sign * np.cross(axis, centers[in_layer])

    keys = position_keys(n, centers)
    order = np.argsort(keys)
    perm = np.empty(len(centers), dtype=int)
    perm[order[np.searchsorted(keys[order], position_keys(n, moved))]] = np.arange(len(centers))
    return perm

# one number for every 3D position, so positions can be looked up fast
def position_keys(n, points):
    size = 2 * n + 1
    p = points + n
    return (p[:, 0] * size + p[:, 1]) * size + p[:, 2]

# every move as a permutation (same move set as before), plus the list the solvers search with
# where duplicates are removed (for example 2U and 2D' on a 3x3 are the same slice)
@lru_cache(maxsize=None)
def build_moves(n):
    groups = [(face, [1]) for face in FACES]
    groups += [(f"{layer}{face}", [layer]) for layer in range(2, n) for face in FACES]
    groups += [(f"{width}{face}w", list(range(1, width + 1))) for width in range(2, n) for face in FACES]

    moves = {}
    search_moves = []
    seen = set()
    for name, layers in groups:
        if name.startswith("2") and name.endswith("w"):
            name = name[1:]  # 2Uw is just written as Uw
        quarter = layer_turns_to_permutation(n, name.strip("0123456789w"), layers)
        for suffix, perm in (("", quarter), ("'", np.argsort(quarter)), ("2", quarter[quarter])):
            moves[name + suffix] = perm
            if name.endswith("w") and len(name) == 2:
                moves["2" + name + suffix] = perm
            if perm.tobytes() not in seen:
                seen.add(perm.tobytes())
                search_moves.append(name + suffix)
    return moves, tuple(search_moves)

# rotate the solved cube with whole cube turns until we find all 24 orientations
@lru_cache(maxsize=None)
def build_solution_cubes(n):
    x = layer_turns_to_permutation(n, 'R', range(1, n + 1))
    y = layer_turns_to_permutation(n, 'U', range(1, n + 1))

    solved = np.arange(6 * n * n)
    found = {solved.tobytes(): solved}
    queue = [solved]
    while queue:
        state = queue.pop()
        for rotation in (x, y):
            new_state = state[rotation]
            if new_state.tobytes() not in found:
                found[new_state.tobytes()] = new_state
                queue.append(new_state)
    return np.array(list(found.values()))

# group of sticker positions that a sticker can ever reach with moves
# (for example on a 4x4 an edge piece can never be flipped, so its two stickers are in different groups)
@lru_cache(maxsize=None)
def sticker_orbits(n):
    moves, search_moves = build_moves(n)
    orbit = np.arange(6 * n * n)
    while True:
        new_orbit = orbit.copy()
        for move in search_moves:
            new_orbit = np.minimum(new_orbit, new_orbit[moves[move]])
        if (new_orbit == orbit).all():
            return orbit
        orbit = new_orbit

# turn the color of every square into a state (sticker ids) the solvers can use
def state_from_colors(n, colors):
    colors = np.asarray(colors, dtype=int)
    if len(colors) != 6 * n * n:
        raise ValueError(f"expected {6 * n * n} squares, got {len(colors)}")
    if (colors < 0).any() or (colors > 5).any():
        raise ValueError(f"{int(((colors < 0) | (colors > 5)).sum())} squares don't have a color yet")
    counts = np.bincount(colors, minlength=6)
    wrong = [f"{COLOR_NAMES[c]} ({counts[c]})" for c in range(6) if counts[c] != n * n]
    if wrong:
        raise ValueError(f"every color needs exactly {n * n} squares, but these don't: " + ", ".join(wrong))

    centers, normals = sticker_geometry(n)
    orbit = sticker_orbits(n)
    solved_colors = np.arange(6 * n * n) // (n * n)

    # stickers that belong to the same piece
    pieces = {}
    for p, key in enumerate(position_keys(n, centers - normals)):
        pieces.setdefault(key, []).append(p)

    # solved pieces we can still hand out, by what they look like
    pool = {}
    for stickers in pieces.values():
        pool.setdefault(tuple(sorted((orbit[q], solved_colors[q]) for q in stickers)), []).append(stickers)

    state = np.empty(6 * n * n, dtype=int)
    for stickers in pieces.values():
        key = tuple(sorted((orbit[p], colors[p]) for p in stickers))
        names = "-".join(COLOR_NAMES[colors[p]] for p in stickers)
        if not pool.get(key):
            raise ValueError(f"the {names} piece doesn't exist on a real cube (or there are too many of it)")
        match = {(orbit[q], solved_colors[q]): q for q in pool[key].pop()}
        for p in stickers:
            state[p] = match[(orbit[p], colors[p])]
        # a corner can't be a mirror image of the real one
        if len(stickers) == 3 and np.linalg.det(normals[stickers]) * np.linalg.det(normals[state[stickers]]) < 0:
            raise ValueError(f"the {names} corner is mirrored, two of its colors are swapped")
    return state
