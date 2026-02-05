import cube_solver
import Cube
import sys

class main:
    def solve(self, cube_size, how_much_scramble, distance_type):
        print("Cube size:", cube_size, " Scramble moves:", how_much_scramble, " Distance type:", distance_type, "\n")
        cube_solver_instance = cube_solver.cube_solver_using_distance(distance_type)
        cube = Cube.Cube(cube_size)
        cube.scramble(how_much_scramble)
        actions = cube_solver_instance.solve(cube)
        print(actions)

if __name__ == "__main__":
    cube_size = int(sys.argv[1])
    scramble = int(sys.argv[2])
    distance = sys.argv[3]

    m = main()
    m.solve(cube_size, scramble, distance)