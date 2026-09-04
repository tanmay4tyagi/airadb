import os
import sys
import threading
import time

# Handle PyInstaller frozen application paths
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


def start_backend_server(port: int = PORT):
    """Start local AirADB backend daemon in a background thread."""
    try:
        server_address = ("0.0.0.0", port)
        DualStackThreadingHTTPServer.allow_reuse_address = True
        httpd = DualStackThreadingHTTPServer(server_address, AirADBRequestHandler)
        t = threading.Thread(target=httpd.serve_forever, daemon=True)
        t.start()
        return httpd
    except Exception:
        # Port already open / existing daemon running
        return None


def run_pyqt_window():
    """Launch native PyQt6 standalone desktop application window with QWebEngineView."""
    from PyQt6.QtCore import QUrl, QSize
    from PyQt6.QtGui import QIcon, QColor
    from PyQt6.QtWidgets import QApplication, QMainWindow
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage

    app = QApplication(sys.argv)
    app.setApplicationName("AirADB Studio")
    app.setOrganizationName("AirADB")

    # Set application icon if available
    icon_path = os.path.join(RESOURCE_DIR, "public", "icon.jpg")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = QMainWindow()
    window.setWindowTitle("AirADB Studio — Android Wireless Debugging Manager")
    window.resize(1280, 840)
    window.setMinimumSize(QSize(980, 640))

    # Dark background styling
    window.setStyleSheet("QMainWindow { background-color: #07090e; }")

    # Standalone WebEngine Browser View
    view = QWebEngineView(window)
    view.setStyleSheet("background-color: #07090e;")
    
    # Load dashboard directly
    view.setUrl(QUrl(TARGET_URL))
    window.setCentralWidget(view)

    window.show()
    return app.exec()


def fallback_launch():
    """Fallback if QtWebEngine is not available on bare environments."""
    import subprocess
    import webbrowser

    edge_paths = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe"),
    ]
    edge_exe = next((p for p in edge_paths if os.path.exists(p)), None)

    if edge_exe:
        try:
            proc = subprocess.Popen([
                edge_exe,
                f"--app={TARGET_URL}",
                "--window-size=1280,820",
                "--app-id=AirADBStudio"
            ])
            proc.wait()
            return
        except Exception:
            pass

    webbrowser.open(TARGET_URL)
    while True:
        time.sleep(1)


def main():
    # 1. Start local ADB backend server daemon
    start_backend_server(PORT)
    time.sleep(0.4)

    # 2. Launch native desktop GUI
    try:
        sys.exit(run_pyqt_window())
    except Exception as e:
        print(f"[Desktop Launcher] PyQt6 launcher fallback triggered: {e}")
        fallback_launch()


if __name__ == "__main__":
    main()
