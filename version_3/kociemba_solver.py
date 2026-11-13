import os
import sys
import threading
import types

from cube import OPPOSITE_COLOR

# supercube loads pyvista for its 3D window, we only need its kociemba solvers
# (the exe is built without pyvista so it stays small)
try:
    import pyvista  # noqa: F401
except ImportError:
    sys.modules["pyvista"] = types.ModuleType("pyvista")

# kociemba wants the faces in U R F D L B order, our state is U L F R B D
KOCIEMBA_FACE_ORDER = [0, 3, 2, 5, 1, 4]
FACE_LETTERS = "ULFRBD"
_lock = threading.RLock()

# folder for the 2x2 solver's tables (it builds them the first time, takes about 30 seconds)
def table_folder():
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, "kociemba_2x2_tables")
    folder = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "RubiksCubeSolver", "kociemba_2x2_tables")
    os.makedirs(folder, exist_ok=True)
    return folder

# import supercube, always use this instead of "import supercube"
# (importing it loads the 2x2 solver, which reads and writes its tables in the current folder)
def import_supercube():
    with _lock:
        if "supercube" not in sys.modules:
            old = os.getcwd()
            os.chdir(table_folder())
            try:
                import supercube  # noqa: F401
            finally:
                os.chdir(old)
    return sys.modules["supercube"]

# load both solvers (slow the first time, so the app does it in the background at start)
def load():
    with _lock:
        import_supercube()
        from supercube import kociemba  # noqa: F401

# kociemba's string for the cube, every square is the letter of the face its color belongs to
def facelets(n, colors):
    if n == 3:
        # the center of every face tells which color the face has
        letter = {colors[f * 9 + 4]: FACE_LETTERS[f] for f in range(6)}
    else:
        # the 2x2 solver keeps the down-left-back corner in place, so name the faces after that corner
        d, l, b = colors[5 * 4 + 2], colors[1 * 4 + 2], colors[4 * 4 + 3]
        letter = {d: 'D', OPPOSITE_COLOR[d]: 'U', l: 'L', OPPOSITE_COLOR[l]: 'R', b: 'B', OPPOSITE_COLOR[b]: 'F'}
    if len(letter) != 6:
        raise ValueError("the cube's colors are not valid")
    return "".join(letter[colors[f * n * n + k]] for f in KOCIEMBA_FACE_ORDER for k in range(n * n))

# solve a 2x2 or 3x3 with kociemba's two phase algorithm (2x2 gives the shortest solution)
def solve(cube, state):
    if cube.n not in (2, 3):
        raise ValueError("kociemba only works for 2x2 and 3x3")
    if cube.is_solved(state):
        return []
    load()
    cubestring = facelets(cube.n, [int(c) for c in state // (cube.n * cube.n)])
    with _lock:
        if cube.n == 3:
            from supercube import kociemba
            result = kociemba.solve(cubestring)
        else:
            from supercube.kociemba_2x2 import solver
            result = solver.solve(cubestring)
    if result.startswith("Error"):
        raise ValueError(result)
    return result.split()
