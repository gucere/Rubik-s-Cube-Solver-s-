import argparse
import random
import sys
import time

from cube import Cube
from cube_solver import CubeSolver, METHODS

def main():
    parser = argparse.ArgumentParser(description="Solve a scrambled NxNxN Rubik's cube with greedy search, beam search or kociemba.")
    parser.add_argument("size", type=int, help="cube size N (2 or more)")
    parser.add_argument("scramble", type=int, help="number of random scramble moves")
    parser.add_argument("distance", choices=["manhattan", "tiles_out_of_place"], help="distance (heuristic) type")
    parser.add_argument("--method", choices=METHODS, default="greedy",
                        help="search method, kociemba only works for 2x2 and 3x3 (default: greedy)")
    parser.add_argument("--beam-width", type=int, default=100, help="states kept per depth in beam search (default: 100)")
    parser.add_argument("--max-depth", type=int, default=50, help="give up after this many moves (default: 50)")
    parser.add_argument("--seed", type=int, help="random seed, to get the same scramble again")
    parser.add_argument("--show", action="store_true", help="print the cube before and after solving")
    args = parser.parse_args()
    if args.size < 2:
        parser.error("size must be at least 2")

    if args.seed is not None:
        random.seed(args.seed)

    print("Cube size:", args.size, " Scramble moves:", args.scramble, " Distance type:", args.distance, "\n")
    cube = Cube(args.size)
    scramble = cube.scramble(args.scramble)
    print("Scramble:", " ".join(scramble), "\n")
    if args.show:
        cube.show()

    solver = CubeSolver(args.distance, args.method, args.beam_width, args.max_depth)
    print("Solving the cube with", args.method, "search...\n")
    start = time.time()
    try:
        actions = solver.solve(cube)
    except ValueError as e:
        print("Can't solve:", e)
        sys.exit(1)
    elapsed = time.time() - start

    if actions is None:
        print(f"No solution found ({elapsed:.2f}s)")
        sys.exit(1)

    for move in actions:
        cube.perform_move(move)
    print(f"Solution ({len(actions)} moves, {elapsed:.2f}s):", " ".join(actions))
    print("Cube is solved!" if cube.is_solved() else "Something went wrong, cube is not solved")
    if args.show:
        cube.show()

if __name__ == "__main__":
    # so the colored output works on windows terminals too
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
