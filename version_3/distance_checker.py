import numpy as np

class DistanceChecker:
    def __init__(self, cube, distance_type):
        if distance_type not in ("manhattan", "tiles_out_of_place"):
            raise ValueError("Invalid distance type")
        self.distance_type = distance_type
        self.n = cube.n
        self.solved_states = cube.all_solution_cubes()

        # face, row and column of every sticker position
        positions = np.arange(6 * self.n * self.n)
        self.face, rest = np.divmod(positions, self.n * self.n)
        self.row, self.col = np.divmod(rest, self.n)

        # for every solved orientation, the goal position of every sticker
        self.goal_positions = np.argsort(self.solved_states, axis=1)

    # distance calculation based on the selected distance type
    def calculate_distance(self, state):
        if self.distance_type == "manhattan":
            return self.manhattan_distance(state)
        return self.tiles_out_of_place(state)

    # manhattan distance (closest solved orientation)
    def manhattan_distance(self, state):
        goal = self.goal_positions[:, state]
        face_penalty = self.n * (self.face != self.face[goal])
        d = np.abs(self.row - self.row[goal]) + np.abs(self.col - self.col[goal]) + face_penalty
        return int(d.sum(axis=1).min())

    # tiles out of place (closest solved orientation)
    def tiles_out_of_place(self, state):
        return int((self.solved_states != state).sum(axis=1).min())
