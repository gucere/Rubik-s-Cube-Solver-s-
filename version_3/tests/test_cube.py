import os
import random
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from cube import Cube, FACES, layer_turns_to_permutation, state_from_colors, sticker_orbits
from cube_solver import CubeSolver

# our 3D moves have to do exactly what supercube does
def test_moves_match_supercube():
    from kociemba_solver import import_supercube
    supercube = import_supercube()
    for n in range(2, 8):
        for face in FACES:
            for layer in range(1, n + 1):
                c = supercube.NCube(n)
                getattr(c, face.lower())(clockwise=True, layer=layer)
                expected = np.array(c.get_state()).reshape(-1) - 1
                assert (layer_turns_to_permutation(n, face, [layer]) == expected).all(), (n, face, layer)

def test_24_orientations():
    for n in range(2, 9):
        cube = Cube(n)
        solutions = cube.all_solution_cubes()
        assert len(solutions) == 24
        for s in solutions:
            assert sorted(s) == list(range(6 * n * n))
            assert cube.is_solved(s)

def test_move_and_inverse():
    for n in range(2, 7):
        cube = Cube(n)
        for move in cube.all_moves():
            inverse = move[:-1] if move.endswith("'") else move if move.endswith("2") else move + "'"
            assert (cube.apply_move(cube.apply_move(cube.state, move), inverse) == cube.state).all()

# a 4x4 edge piece can't flip, so its 48 stickers split into 2 groups of 24
def test_orbits_4x4():
    sizes = sorted(np.bincount(sticker_orbits(4))[np.bincount(sticker_orbits(4)) > 0])
    assert sizes == [24, 24, 24, 24]

def test_colors_round_trip():
    random.seed(0)
    for n in range(2, 7):
        cube = Cube(n)
        cube.scramble(40)
        state = state_from_colors(n, cube.get_colors())
        assert (state // (n * n) == cube.get_colors()).all()

def test_bad_colors():
    cube = Cube(3)
    colors = cube.get_colors()
    # swap the white and green sticker of the up-front-right corner (mirrored corner)
    colors[8], colors[20] = colors[20], colors[8]
    for bad in (colors, [0] * 54, [-1] * 54):
        try:
            state_from_colors(3, bad)
            assert False, "should have failed"
        except ValueError:
            pass

def test_kociemba():
    random.seed(1)
    for n in (2, 3):
        for _ in range(3):
            cube = Cube(n)
            cube.scramble(30)
            moves = CubeSolver("manhattan", "kociemba").solve(cube)
            for m in moves:
                cube.perform_move(m)
            assert cube.is_solved()

def test_beam():
    random.seed(2)
    cube = Cube(3)
    cube.scramble(3)
    moves = CubeSolver("manhattan", "beam").solve(cube)
    for m in moves:
        cube.perform_move(m)
    assert cube.is_solved()

if __name__ == "__main__":
    for name, test in list(globals().items()):
        if name.startswith("test_"):
            test()
            print("ok", name)
