import os
import sys
import json
import socket
import mimetypes
import tempfile
import threading
import webbrowser
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from adb_manager import ADBManager

# Ensure UTF-8 output in Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

PORT = 8765
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")

adb = ADBManager()


class DualStackThreadingHTTPServer(ThreadingHTTPServer):
    """Multi-threaded HTTP Server supporting both IPv4 and IPv6 (localhost and LAN IPs)."""
    daemon_threads = True

    def server_bind(self):
        try:
            # Enable dual-stack IPv4 and IPv6 on Windows
            if hasattr(socket, 'AF_INET6') and self.address_family == socket.AF_INET6:
                self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        except Exception:
            pass
        super().server_bind()


def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


class AirADBRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress routine log messages for a clean console, log errors only
        if args and str(args[1]) in ["404", "500"]:
            super().log_message(format, *args)

    def handle(self):
        try:
            super().handle()
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass

    def _send_json(self, data: dict, status: int = 200):
        try:
            body = json.dumps(data).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.end_headers()
            self.wfile.write(body)
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass
        except Exception as e:
            pass

    def _read_json_body(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length > 0:
                raw = self.rfile.read(length).decode("utf-8", errors="replace")
                return json.loads(raw)
        except Exception:
            pass
        return {}

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        # API Routes
        if path == "/api/status":
            installed = adb.is_installed()
            self._send_json({
                "installed": installed,
                "version": adb.get_version() if installed else None,
                "adb_path": adb.adb_path,
                "local_ip": get_local_ip()
            })
            return

        elif path == "/api/devices":
            devices = adb.get_devices()
            self._send_json({"devices": devices})
            return

        elif path == "/api/history":
            self._send_json({"history": adb.history})
            return

        elif path == "/api/scan":
            mdns = adb.scan_mdns_services()
            subnet_devices = adb.scan_local_subnet_adb()
            self._send_json({
                "mdns": mdns,
                "subnet": subnet_devices
            })
            return

        elif path == "/api/screenshot":
            serial = params.get("serial", [None])[0]
            if not serial:
                self._send_json({"error": "Serial parameter required"}, 400)
                return

            success, img_bytes, err = adb.capture_screenshot(serial)
            if success and img_bytes:
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Content-Length", str(len(img_bytes)))
                self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                self.end_headers()
                self.wfile.write(img_bytes)
            else:
                self._send_json({"error": f"Failed to capture screenshot: {err}"}, 500)
            return

        elif path == "/api/logcat":
            serial = params.get("serial", [None])[0]
            lines = int(params.get("lines", [150])[0])
            filter_str = params.get("filter", [None])[0]

            if not serial:
                self._send_json({"error": "Serial parameter required"}, 400)
                return

            res = adb.get_logcat(serial, lines, filter_str)
            self._send_json(res)
            return

        # Static File Serving
        self._serve_static(path)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/install-adb":
            # Start download in background or sync
            res = adb.download_and_install_platform_tools()
            self._send_json(res)
            return

        elif path == "/api/pair":
            body = self._read_json_body()
            ip_port = body.get("ip_port", "")
            code = body.get("code", "")
            nickname = body.get("nickname", "")
            res = adb.pair_device(ip_port, code, nickname)
            self._send_json(res)
            return

        elif path == "/api/connect":
            body = self._read_json_body()
            ip_port = body.get("ip_port", "")
            nickname = body.get("nickname", "")
            res = adb.connect_device(ip_port, nickname)
            self._send_json(res)
            return

        elif path == "/api/disconnect":
            body = self._read_json_body()
            ip_port = body.get("ip_port", None)
            res = adb.disconnect_device(ip_port)
            self._send_json(res)
            return

        elif path == "/api/usb-to-wifi":
            body = self._read_json_body()
            serial = body.get("serial", None)
            port = int(body.get("port", 5555))
            res = adb.switch_usb_to_wireless(serial, port)
            self._send_json(res)
            return

        elif path == "/api/history/delete":
            body = self._read_json_body()
            ip = body.get("ip", "")
            adb.remove_from_history(ip)
            self._send_json({"success": True, "history": adb.history})
            return

        elif path == "/api/shell":
            body = self._read_json_body()
            serial = body.get("serial", "")
            cmd = body.get("command", "")
            if not serial or not cmd:
                self._send_json({"success": False, "message": "Serial and command required"}, 400)
                return
            res = adb.execute_shell(serial, cmd)
            self._send_json(res)
            return

        elif path == "/api/mobile/open-settings":
            body = self._read_json_body()
            target = body.get("target", "dev_options")
            serial = body.get("serial", "")
            
            action_map = {
                "dev_options": "android.settings.APPLICATION_DEVELOPMENT_SETTINGS",
                "wireless": "android.settings.WIRELESS_SETTINGS",
                "settings": "android.settings.SETTINGS"
            }
            act = action_map.get(target, "android.settings.APPLICATION_DEVELOPMENT_SETTINGS")
            
            if not serial:
                devices = adb.get_devices()
                if devices:
                    serial = devices[0]["serial"]
                    
            if serial:
                res = adb.execute_shell(serial, f"am start -a {act}")
                self._send_json({"success": True, "target": target, "action": act, "output": res.get("output", "")})
            else:
                self._send_json({"success": False, "message": "No active ADB device connected to launch settings remotely."}, 200)
            return

        elif path == "/api/restart-adb":
            res = adb.restart_adb_server()
            self._send_json(res)
            return

        elif path == "/api/upload-apk":
            # Handle multipart/form-data APK upload
            content_type = self.headers.get("Content-Type", "")
            if "multipart/form-data" not in content_type:
                self._send_json({"success": False, "message": "Expected multipart/form-data"}, 400)
                return

            try:
                import cgi
                form = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': content_type}
                )
                serial = form.getvalue("serial")
                fileitem = form["file"] if "file" in form else None

                if not serial or not fileitem or not fileitem.filename:
                    self._send_json({"success": False, "message": "Device serial and APK file are required"}, 400)
                    return

                with tempfile.NamedTemporaryFile(delete=False, suffix=".apk") as tmp:
                    tmp.write(fileitem.file.read())
                    tmp_path = tmp.name

                res = adb.install_apk(serial, tmp_path)
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

                self._send_json(res)
            except Exception as e:
                self._send_json({"success": False, "message": f"Error handling APK upload: {str(e)}"}, 500)
            return

        self._send_json({"error": "Route not found"}, 404)

    def _serve_static(self, path: str):
        if path == "/" or not path:
            path = "/index.html"

        # Sanitize path
        rel_path = path.lstrip("/").replace("/", os.sep)
        full_path = os.path.join(PUBLIC_DIR, rel_path)

        if not os.path.exists(full_path) or os.path.isdir(full_path):
            full_path = os.path.join(PUBLIC_DIR, "index.html")

        if not os.path.exists(full_path):
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")
            return

        mime_type, _ = mimetypes.guess_type(full_path)
        if not mime_type:
            mime_type = "application/octet-stream"

        try:
            with open(full_path, "rb") as f:
                content = f.read()

            self.send_response(200)
            self.send_header("Content-Type", f"{mime_type}; charset=utf-8" if "text" in mime_type or "javascript" in mime_type else mime_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content)
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass
        except Exception as e:
            try:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f"500 Internal Server Error: {e}".encode("utf-8"))
            except Exception:
                pass


def run_server(port=PORT, open_browser=True):
    os.makedirs(PUBLIC_DIR, exist_ok=True)
    server_address = ("0.0.0.0", port)
    DualStackThreadingHTTPServer.allow_reuse_address = True
    httpd = DualStackThreadingHTTPServer(server_address, AirADBRequestHandler)

    url = f"http://localhost:{port}"
    lan_url = f"http://{get_local_ip()}:{port}"
    print("=" * 60)
    print("  🚀 AirADB Studio - Android Wireless Debugging Hub")
    print(f"  📡 Laptop URL:  {url}")
    print(f"  📱 Mobile URL:  {lan_url}")
    print("=" * 60)

    if open_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping AirADB server...")
        httpd.server_close()


if __name__ == "__main__":
    should_open = "--no-browser" not in sys.argv
    run_server(PORT, open_browser=should_open)
