# Rubik-s-Cube-Solver-s-

Solves NxNxN Rubik's cubes (any N from 2 up) with greedy search, beam search or Kociemba's algorithm.
Comes with a 3D app where you can play with a cube, paint your own real cube's colors in, and watch it get solved step by step.

## Folders

- `RubiksCubeSolver.exe`: the app (Windows), just double-click it
- `version_1/`: the original 2x2 beam search notebook from college
- `version_2/`: greedy NxN solver, before the rewrite
- `version_3/`: current code (solver, app, tests)

## The app

Double-click `RubiksCubeSolver.exe`, or run it from source:

```
cd version_3
pip install -r requirements.txt
python app.py
```

- **Play**: drag a sticker to turn its layer, drag empty space to look around. Keys `U D L R F B`, hold `Shift` for counter-clockwise. Scramble, undo, any size from 2x2 to 12x12.
- **Paint**: start from a blank cube, pick a color and click (or drag over) squares to copy your real cube. The app checks that every piece exists on a real cube before solving.
- **Solve**: the big button uses the fastest method (Kociemba for 2x2 and 3x3, beam search for bigger cubes). Or pick any algorithm and heuristic yourself with "Solve with ...".
- **Steps**: play the solution, step forward and back, or click a move to jump to it.

`python app.py --browser` opens it in your web browser instead of its own window.

### Building the exe

```
cd version_3
python build_exe.py
```

The exe ends up in the top folder. It needs Microsoft Edge WebView2, which comes with Windows 10 and 11.

## Command line

From `version_3/`:

```
python main.py <size> <scramble moves> <distance> [--method greedy|beam|kociemba|fastest] [--beam-width 100] [--max-depth 50] [--seed S] [--show]
```

Examples:

```
python main.py 3 1 manhattan
python main.py 3 5 manhattan --method beam --seed 1
python main.py 3 30 manhattan --method kociemba
python main.py 6 3 tiles_out_of_place --method beam --show
```

- `distance`: `manhattan` or `tiles_out_of_place`, both measured against the closest of the 24 solved orientations
- `--method greedy`: always takes the move that gets closest, never revisits a state
- `--method beam`: keeps the best `--beam-width` states at every depth
- `--method kociemba`: two phase algorithm, solves any 2x2 (shortest solution) or 3x3 in about a second
- `--method fastest`: kociemba for 2x2 and 3x3, beam search for bigger cubes
- `--seed`: gives the same scramble again
- `--show`: prints the cube before and after

## How it works

- The cube is a flat array of sticker ids. Every sticker has a 3D position, and every move is a quarter turn of some layers in 3D, precomputed once as a permutation of the array.
- The move set is face turns, inner slice turns (`2U`, `3R`, ...) and wide turns (`Uw`, `3Fw`, ...), with duplicates removed. The notation is the same as [super-rubik-cube](https://pypi.org/project/super-rubik-cube/) (tests check every move against it).
- The cube counts as solved when every face has one color, no matter which way the cube is facing.
- Kociemba comes from super-rubik-cube.
- The app is a small local web server (`app.py`) with a three.js page (`web/`), shown in its own window with pywebview. `web/moves.js` does the same moves as `cube.py` so the page can animate them.

## Results

10 random scrambles each, beam width 100:

| Cube | Scramble | Heuristic | Greedy solved | Beam solved |
|------|----------|-----------|---------------|-------------|
| 2x2 | 4 | manhattan | 5/10 | 10/10 |
| 2x2 | 8 | manhattan | 0/10 | 6/10 |
| 3x3 | 4 | manhattan | 2/10 | 9/10 |
| 3x3 | 6 | manhattan | 0/10 | 6/10 |
| 4x4 | 4 | manhattan | 2/10 | 8/10 |
| 5x5 | 3 | manhattan | 5/10 | 10/10 |
| 6x6 | 3 | manhattan | 2/10 | 10/10 |

Greedy and beam search are heuristic, so they work well on short scrambles but don't solve fully scrambled cubes. Kociemba solves any 2x2 or 3x3.

## Tests

```
cd version_3
python tests/test_cube.py
```
