import supercube
from collections import deque

class Cube:
    # initialize a cube with NxNxN
    def __init__(self, n):
        self.n = n
        self.cube = supercube.NCube(n)

    # get current state of the cube    
    def get_state(self):
        return self.cube.get_state()
    
    # define a specific state
    def define_state(self, state):
        self.cube.define_state(state)

    # scramble the cube randomly
    def scramble(self):
        self.cube.scramble()
    
    # scramble the cube for a specific number of moves
    def scramble(self, moves):
        self.cube.scramble(number_of_moves = moves)
    
    # all possible move set
    def all_moves(self):
        n = self.n
        moves = set()

        faces = ['U', 'D', 'L', 'R', 'F', 'B']

        for face in faces:
            moves.add(face)
            moves.add(f"{face}'")
            moves.add(f"{face}2")

        if n > 2:
            for face in faces:
                moves.add(f"{face}w")
                moves.add(f"{face}w'")
                moves.add(f"{face}w2")

            for width in range(2, n):
                for face in faces:
                    moves.add(f"{width}{face}w")
                    moves.add(f"{width}{face}w'")
                    moves.add(f"{width}{face}w2")

            for layer in range(2, n):
                for face in faces:
                    moves.add(f"{layer}{face}")
                    moves.add(f"{layer}{face}'")
                    moves.add(f"{layer}{face}2")

        return moves
    
    # all possible solutions
    def all_solution_cubes(self):
        n = self.n
        U, L, F, R, B, D = 0, 1, 2, 3, 4, 5

        def face_rc_to_xyz(face, i, j):
            if face == U:
                x = j
                y = n - 1
                z = n - 1 - i
            elif face == D:
                x = j
                y = 0
                z = i
            elif face == F:
                x = j
                y = n - 1 - i
                z = n - 1
            elif face == B:
                x = n - 1 - j
                y = n - 1 - i
                z = 0
            elif face == L:
                x = 0
                y = n - 1 - i
                z = j
            elif face == R:
                x = n - 1
                y = n - 1 - i
                z = n - 1 - j
            else:
                raise ValueError("bad face")
            return x, y, z

        def xyz_to_face_rc(x, y, z):
            if y == n - 1:
                face = U
                i = n - 1 - z
                j = x
            elif y == 0:
                face = D
                i = z
                j = x
            elif z == n - 1:
                face = F
                i = n - 1 - y
                j = x
            elif z == 0:
                face = B
                i = n - 1 - y
                j = n - 1 - x
            elif x == 0:
                face = L
                i = n - 1 - y
                j = z
            elif x == n - 1:
                face = R
                i = n - 1 - y
                j = n - 1 - z
            else:
                raise ValueError("coordinate not on surface")
            return face, i, j

        def rot_x_90(x, y, z):
            return x, z, (n - 1 - y)

        def rot_y_90(x, y, z):
            return (n - 1 - z), y, x

        def rot_z_90(x, y, z):
            return y, (n - 1 - x), z

        def rotate_state(state, axis, turns=1):
            turns %= 4
            if turns == 0:
                return state

            rot = {"x": rot_x_90, "y": rot_y_90, "z": rot_z_90}[axis]

            cur = state
            for _ in range(turns):
                nxt = [[[None for _ in range(n)] for _ in range(n)] for _ in range(6)]
                for face in range(6):
                    for i in range(n):
                        for j in range(n):
                            x, y, z = face_rc_to_xyz(face, i, j)
                            x2, y2, z2 = rot(x, y, z)
                            f2, i2, j2 = xyz_to_face_rc(x2, y2, z2)
                            nxt[f2][i2][j2] = cur[face][i][j]
                cur = nxt
            return cur

        def freeze_state(state):
            return tuple(tuple(tuple(row) for row in face) for face in state)

        base_cube = supercube.NCube(n)
        base_state = base_cube.get_state()

        solutions = {}
        seen = set()

        q = deque()
        q.append(("", base_state))

        while q:
            name, st = q.popleft()
            key = freeze_state(st)
            if key in seen:
                continue
            seen.add(key)

            label = name if name else "identity"
            solutions[label] = st

            for axis in ("x", "y", "z"):
                st2 = rotate_state(st, axis, 1)
                name2 = (name + " " + axis).strip()
                q.append((name2, st2))

        return solutions
    
    # get current state
    def get_state(self):
        return self.cube.get_state()
    
    # print current state
    def show(self):
        self.cube.show()
        self.cube.show(colors=True)

    # 3D current state
    def show_3d(self):
        self.cube.show_3d()
    
    # perform a move on the cube
    def perform_move(self, move):
        self.cube.move(move)