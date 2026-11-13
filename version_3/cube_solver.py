import time

import kociemba_solver
from distance_checker import DistanceChecker

METHODS = ("greedy", "beam", "kociemba", "fastest")

class CubeSolver:

    def __init__(self, distance_type, method="greedy", beam_width=100, max_depth=50, time_limit=None, stop_event=None):
        if method not in METHODS:
            raise ValueError("Invalid search method")
        self.distance_type = distance_type
        self.method = method
        self.beam_width = beam_width
        self.max_depth = max_depth
        self.time_limit = time_limit
        self.stop_event = stop_event
        self.used_method = method

    # returns the list of moves that solves the cube, or None if no solution was found
    def solve(self, cube, state=None):
        if state is None:
            state = cube.get_state()
        self.deadline = time.time() + self.time_limit if self.time_limit else None

        method = self.method
        if method == "fastest":
            # kociemba is instant for 2x2 and 3x3, bigger cubes fall back to beam search
            method = "kociemba" if cube.n in (2, 3) else "beam"
        self.used_method = method

        if method == "kociemba":
            return kociemba_solver.solve(cube, state)
        self.distance_checker = DistanceChecker(cube, self.distance_type)
        if method == "beam":
            return self.beam_search(cube, state)
        return self.greedy_search(cube, state)

    # true when we ran out of time or someone pressed cancel
    def should_stop(self):
        if self.stop_event is not None and self.stop_event.is_set():
            return True
        return self.deadline is not None and time.time() > self.deadline

    # always take the move that gets closest, but never go back to a state we already visited
    def greedy_search(self, cube, state):
        visited = {state.tobytes()}
        needed_moves = []

        for _ in range(self.max_depth):
            if cube.is_solved(state):
                return needed_moves
            if self.should_stop():
                return None

            best_move = None
            best_state = None
            best_distance = float("inf")

            for move in cube.all_moves():
                new_state = cube.apply_move(state, move)
                if new_state.tobytes() in visited:
                    continue
                new_distance = self.distance_checker.calculate_distance(new_state)
                if new_distance < best_distance:
                    best_distance = new_distance
                    best_move = move
                    best_state = new_state

            # every neighbor was visited before, we are stuck
            if best_move is None:
                return None

            needed_moves.append(best_move)
            visited.add(best_state.tobytes())
            state = best_state

        return needed_moves if cube.is_solved(state) else None

    # keep the best beam_width states at every depth
    def beam_search(self, cube, state):
        if cube.is_solved(state):
            return []

        beam = [(state, [])]
        visited = {state.tobytes()}

        for _ in range(self.max_depth):
            candidates = []
            for state, moves in beam:
                if self.should_stop():
                    return None
                for move in cube.all_moves():
                    new_state = cube.apply_move(state, move)
                    key = new_state.tobytes()
                    if key in visited:
                        continue
                    visited.add(key)
                    if cube.is_solved(new_state):
                        return moves + [move]
                    distance = self.distance_checker.calculate_distance(new_state)
                    candidates.append((distance, len(candidates), new_state, moves + [move]))

            if not candidates:
                return None

            candidates.sort()
            beam = [(state, moves) for _, _, state, moves in candidates[:self.beam_width]]

        return None
