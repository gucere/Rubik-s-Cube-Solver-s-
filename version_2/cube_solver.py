import distanceChecker
import Cube
import copy

class cube_solver_using_distance:

    def __init__(self, distance_type):
        self.distance_checker = distanceChecker.distanceChecker(distance_type)

    def solve(self, cube):
        print("Solving the cube...\n")
        print("Initial state:")
        print(cube.get_state())
        print("\n")
        needed_moves = []

        while True:
            distance = self.distance_checker.calculate_distance(cube)
            if distance == 0:
                print("Cube is solved!")
                print("Final state:")
                print(cube.get_state())
                print("\n")
                return needed_moves

            best_move = None
            best_distance = float("inf")

            for move in cube.all_moves():
                # clone the whole cube, then try the move on the clone
                new_cube = copy.deepcopy(cube)
                new_cube.cube.move(move)

                new_distance = self.distance_checker.calculate_distance(new_cube)
                if new_distance < best_distance:
                    best_distance = new_distance
                    best_move = move

            needed_moves.append(best_move)
            cube.cube.move(best_move)