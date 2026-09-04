import os
import subprocess
import sys
import time
import threading
import webbrowser

# Handle PyInstaller paths
if getattr(sys, 'frozen', False):
    RESOURCE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    BASE_DIR = os.path.dirname(sys.executable)
else:
    RESOURCE_DIR = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if RESOURCE_DIR not in sys.path:
    sys.path.insert(0, RESOURCE_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Mark process as dedicated desktop application
os.environ["AIRADB_DESKTOP"] = "1"

from server import DualStackThreadingHTTPServer, AirADBRequestHandler

PORT = 8765
TARGET_URL = f"http://127.0.0.1:{PORT}/?view=app"


def start_server(port: int = PORT):
    """Start local AirADB backend server in daemon thread."""
    try:
        server_address = ("0.0.0.0", port)
        DualStackThreadingHTTPServer.allow_reuse_address = True
        httpd = DualStackThreadingHTTPServer(server_address, AirADBRequestHandler)
        t = threading.Thread(target=httpd.serve_forever, daemon=True)
        t.start()
        return httpd
    except Exception:
        # If port 8765 is already listening, existing daemon is reused
        return None


def launch_app():
    # 1. Start background AirADB server daemon
    httpd = start_server(PORT)
    time.sleep(0.5)

    # 2. Paths to Microsoft Edge Chromium on Windows
    edge_paths = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe"),
    ]

    edge_exe = next((p for p in edge_paths if os.path.exists(p)), None)

    # 3. Launch Edge in dedicated standalone app-window mode (frameless app window)
    if edge_exe:
        try:
            proc = subprocess.Popen([
                edge_exe,
                f"--app={TARGET_URL}",
                "--window-size=1280,820",
                "--app-id=AirADBStudio"
            ])
            # Wait for Edge window process to exit
            proc.wait()
            return
        except Exception:
            pass

    # Fallback to default browser if Edge is missing or fails
    webbrowser.open(TARGET_URL)

    # Keep server process alive while running in fallback
    if httpd:
        try:
            while True:
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            pass


if __name__ == "__main__":
    launch_app()
