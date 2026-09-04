import os
import sys
import threading
import time
import socket

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

import webview
from server import DualStackThreadingHTTPServer, AirADBRequestHandler


def start_server(port: int = 8765):
    """Start local AirADB backend server in daemon thread."""
    try:
        server_address = ("0.0.0.0", port)
        DualStackThreadingHTTPServer.allow_reuse_address = True
        httpd = DualStackThreadingHTTPServer(server_address, AirADBRequestHandler)
        t = threading.Thread(target=httpd.serve_forever, daemon=True)
        t.start()
        return httpd
    except Exception as e:
        # If port 8765 is already listening, server is already running
        return None


def main():
    port = 8765
    start_server(port)
    time.sleep(0.4)

    # Launch native desktop app window using Microsoft Edge Chromium (WebView2)
    window = webview.create_window(
        title="AirADB Studio - Android Wireless Debugging",
        url=f"http://127.0.0.1:{port}/?view=app",
        width=1280,
        height=820,
        min_size=(960, 640),
        background_color="#080b11",
        text_select=True,
        zoomable=True
    )
    # Explicitly enforce Edge Chromium (WebView2) engine to prevent WinForms/pythonnet crash
    webview.start(gui="edgechromium", private_mode=False)


if __name__ == "__main__":
    main()
