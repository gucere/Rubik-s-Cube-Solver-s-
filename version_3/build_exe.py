# builds RubiksCubeSolver.exe in the top folder of the project (run: python build_exe.py)
import os
import shutil
import tempfile

import PyInstaller.__main__

import kociemba_solver

HERE = os.path.dirname(os.path.abspath(__file__))
TOP_FOLDER = os.path.dirname(HERE)

# make sure the 2x2 solver's tables exist, so the exe doesn't have to build them (about 30 seconds) on first solve
kociemba_solver.load()
tables = kociemba_solver.table_folder()

# pyinstaller's work files go to a temporary folder, so only the exe is left behind
# (it also runs from there, because importing supercube writes table files in the current folder)
work = tempfile.mkdtemp()
old = os.getcwd()
os.chdir(work)
try:
    PyInstaller.__main__.run([
        os.path.join(HERE, "app.py"),
        "--name", "RubiksCubeSolver",
        "--onefile",
        "--windowed",
        "--noconfirm",
        "--distpath", TOP_FOLDER,
        "--workpath", os.path.join(work, "build"),
        "--specpath", work,
        "--icon", os.path.join(HERE, "web", "icon.ico"),
        "--add-data", f"{os.path.join(HERE, 'web')}{os.pathsep}web",
        "--add-data", f"{tables}{os.pathsep}kociemba_2x2_tables",
        # the 3x3 kociemba tables
        "--collect-data", "supercube",
        # only needed for supercube's own 3D window, which the app doesn't use
        "--exclude-module", "pyvista",
        "--exclude-module", "vtk",
        "--exclude-module", "vtkmodules",
        "--exclude-module", "matplotlib",
        "--exclude-module", "scipy",
        "--exclude-module", "IPython",
        "--exclude-module", "PIL",
    ])
finally:
    os.chdir(old)
    shutil.rmtree(work, ignore_errors=True)
