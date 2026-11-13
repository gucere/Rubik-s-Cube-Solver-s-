import argparse
import json
import os
import sys
import threading
import time
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import numpy as np

import kociemba_solver
from cube import Cube, sticker_geometry, state_from_colors
from cube_solver import CubeSolver

MAX_SIZE = 12
# when built as an exe, the web files are unpacked next to the code
BASE = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
WEB_FOLDER = os.path.join(BASE, "web")
cancel_event = threading.Event()

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_FOLDER, **kwargs)

    # don't print every request
    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path.startswith("/api/geometry"):
            n = int(self.path.split("n=")[1])
            centers, normals = sticker_geometry(check_size(n))
            return self.send_json({"centers": centers.tolist(), "normals": normals.tolist()})
        return super().do_GET()

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])) or b"{}")
        try:
            if self.path == "/api/solve":
                return self.send_json(solve(body))
            if self.path == "/api/from_colors":
                n = check_size(body["n"])
                return self.send_json({"state": state_from_colors(n, body["colors"]).tolist()})
            if self.path == "/api/cancel":
                cancel_event.set()
                return self.send_json({})
        except ValueError as e:
            return self.send_json({"error": str(e)})
        self.send_error(404)

    def send_json(self, data):
        raw = json.dumps(data).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

def check_size(n):
    if not 2 <= int(n) <= MAX_SIZE:
        raise ValueError(f"cube size must be between 2 and {MAX_SIZE}")
    return int(n)

# solve the state the page sent with the method the user picked
def solve(body):
    cube = Cube(check_size(body["n"]))
    state = np.array(body["state"], dtype=int)
    cancel_event.clear()
    solver = CubeSolver(body.get("distance", "manhattan"), body.get("method", "fastest"),
                        beam_width=int(body.get("beam_width", 100)), max_depth=int(body.get("max_depth", 50)),
                        time_limit=float(body.get("time_limit", 30)), stop_event=cancel_event)
    start = time.time()
    moves = solver.solve(cube, state)
    seconds = round(time.time() - start, 2)
    if moves is None:
        reason = "cancelled" if cancel_event.is_set() else "no solution found within the limits"
        return {"error": reason, "method": solver.used_method, "seconds": seconds}
    return {"moves": moves, "method": solver.used_method, "seconds": seconds}

def main():
    parser = argparse.ArgumentParser(description="3D Rubik's cube solver app")
    parser.add_argument("--browser", action="store_true", help="open in your web browser instead of an app window")
    parser.add_argument("--serve", action="store_true", help="only run the local server, don't open anything")
    parser.add_argument("--port", type=int, default=0, help="port for the local server (default: any free port)")
    args = parser.parse_args()

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    threading.Thread(target=server.serve_forever, daemon=True).start()
    # kociemba takes a few seconds to load, do it before anyone presses solve
    threading.Thread(target=kociemba_solver.load, daemon=True).start()

    if not args.browser and not args.serve:
        try:
            import webview
            webview.create_window("Rubik's Cube Solver", url, width=1280, height=820, min_size=(900, 600))
            webview.start()
            return
        except Exception as e:
            print("Couldn't open the app window, opening the browser instead:", e)

    print("Running at", url, "(press Ctrl+C to stop)", flush=True)
    if not args.serve:
        webbrowser.open(url)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
