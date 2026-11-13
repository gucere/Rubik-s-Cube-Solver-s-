import Cube

class distanceChecker:
    def __init__(self, distance_type):
         self.distance_type = distance_type
    
    # distance calculation based on the selected distance type
    def calculate_distance(self, cube):
        if self.distance_type == "manhattan":
            return self.manhattanDistance(cube)
        elif self.distance_type == "tiles_out_of_place":
            return self.tilesOutOfPlace(cube)
        else:
            raise ValueError("Invalid distance type")
    
    # manhattan distance
    def manhattanDistance(self, cube):
        state = cube.get_state()
        n = cube.n

        solved_states = cube.all_solution_cubes().values()
        best_total = float("inf")

        # optional: precompute the set of tile values appearing in the current state
        state_vals = set()
        for f in range(6):
            for i in range(n):
                for j in range(n):
                    state_vals.add(state[f][i][j])

        for goal in solved_states:
            # build tile/color -> list of goal positions
            goal_pos = {}
            goal_vals = set()

            for f in range(6):
                for i in range(n):
                    for j in range(n):
                        c = goal[f][i][j]
                        goal_vals.add(c)
                        goal_pos.setdefault(c, []).append((f, i, j))

            # if this goal orientation doesn't contain all values in the current state, skip it
            if not state_vals.issubset(goal_vals):
                continue

            total = 0
            invalid = False

            for f in range(6):
                for i in range(n):
                    for j in range(n):
                        c = state[f][i][j]
                        positions = goal_pos.get(c)
                        if positions is None:
                            # Shouldn't happen after the subset check, but keep it safe
                            invalid = True
                            break

                        # find closest goal position for this same tile/color
                        best = float("inf")
                        for gf, gi, gj in positions:
                            face_penalty = 0 if f == gf else n
                            d = abs(i - gi) + abs(j - gj) + face_penalty
                            if d < best:
                                best = d

                        total += best
                if invalid:
                    break

            if not invalid and total < best_total:
                best_total = total

        # If every goal was skipped (shouldn't usually happen), fall back to something safe
        if best_total == float("inf"):
            return 0  # or return a large number like 10**9

        return best_total


    # tiles out of place
    def tilesOutOfPlace(self, cube):
        state = cube.get_state()
        n = cube.n

        # get all solved orientations
        solved_dict = cube.all_solution_cubes()
        solved_states = solved_dict.values()

        best = float("inf")

        for goal in solved_states:
            out = 0

            for f in range(6):
                for i in range(n):
                    for j in range(n):
                        if state[f][i][j] != goal[f][i][j]:
                            out += 1

            if out < best:
                best = out

        return best