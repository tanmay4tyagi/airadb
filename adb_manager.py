import os
import sys
import subprocess
import socket
import json
import re
import urllib.request
import zipfile
import shutil
import time
from typing import Dict, List, Optional, Any, Tuple

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BIN_DIR = os.path.join(BASE_DIR, "bin")
PLATFORM_TOOLS_DIR = os.path.join(BIN_DIR, "platform-tools")
HISTORY_FILE = os.path.join(BASE_DIR, "history.json")

GOOGLE_PLATFORM_TOOLS_URL = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"


class ADBManager:
    def __init__(self):
        self._adb_path: Optional[str] = self._find_adb()
        self.history: List[Dict[str, Any]] = self._load_history()

    def _find_adb(self) -> Optional[str]:
        """Find ADB executable on system or in local bundled directory."""
        # 1. Local bin folder
        local_adb = os.path.join(PLATFORM_TOOLS_DIR, "adb.exe" if sys.platform == "win32" else "adb")
        if os.path.exists(local_adb):
            return local_adb

        # 2. In PATH
        adb_in_path = shutil.which("adb")
        if adb_in_path:
            return adb_in_path

        # 3. Standard Android SDK locations on Windows
        if sys.platform == "win32":
            local_appdata = os.environ.get("LOCALAPPDATA", "")
            if local_appdata:
                sdk_adb = os.path.join(local_appdata, "Android", "Sdk", "platform-tools", "adb.exe")
                if os.path.exists(sdk_adb):
                    return sdk_adb

            program_files = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
            sdk_adb_pf = os.path.join(program_files, "Android", "android-sdk", "platform-tools", "adb.exe")
            if os.path.exists(sdk_adb_pf):
                return sdk_adb_pf

            alt_c = "C:\\Android\\platform-tools\\adb.exe"
            if os.path.exists(alt_c):
                return alt_c

        return None

    @property
    def adb_path(self) -> Optional[str]:
        if not self._adb_path or not os.path.exists(self._adb_path):
            self._adb_path = self._find_adb()
        return self._adb_path

    def is_installed(self) -> bool:
        return self.adb_path is not None

    def get_version(self) -> Optional[str]:
        if not self.adb_path:
            return None
        res = self._run_adb(["version"])
        if res["success"]:
            lines = res["output"].strip().splitlines()
            return lines[0] if lines else "Installed"
        return None

    def download_and_install_platform_tools(self, progress_callback=None) -> Dict[str, Any]:
        """Download official Google platform-tools for Windows and extract to bin/platform-tools."""
        os.makedirs(BIN_DIR, exist_ok=True)
        zip_path = os.path.join(BIN_DIR, "platform-tools.zip")

        try:
            if progress_callback:
                progress_callback("Downloading Android Platform-Tools from Google...")

            def _reporthook(count, block_size, total_size):
                if progress_callback and total_size > 0:
                    percent = int(count * block_size * 100 / total_size)
                    percent = min(100, percent)
                    progress_callback(f"Downloading: {percent}%")

            urllib.request.urlretrieve(GOOGLE_PLATFORM_TOOLS_URL, zip_path, _reporthook)

            if progress_callback:
                progress_callback("Extracting platform-tools...")

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(BIN_DIR)

            if os.path.exists(zip_path):
                os.remove(zip_path)

            self._adb_path = self._find_adb()
            if self._adb_path:
                # Test execution and start server
                self._run_adb(["start-server"])
                return {
                    "success": True,
                    "message": "ADB installed successfully!",
                    "adb_path": self._adb_path,
                    "version": self.get_version()
                }
            else:
                return {
                    "success": False,
                    "message": "Extracted platform-tools, but adb executable was not found."
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to download/install platform-tools: {str(e)}"
            }

    def _run_adb(self, args: List[str], timeout: int = 15) -> Dict[str, Any]:
        """Run an ADB command with timeout."""
        adb = self.adb_path
        if not adb:
            return {
                "success": False,
                "output": "",
                "error": "ADB is not installed or configured. Please install platform-tools."
            }

        cmd = [adb] + args
        try:
            # Hide console window on Windows if spawned from GUI
            creationflags = 0
            if sys.platform == "win32":
                creationflags = subprocess.CREATE_NO_WINDOW

            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                creationflags=creationflags,
                encoding="utf-8",
                errors="replace"
            )
            stdout = proc.stdout.strip()
            stderr = proc.stderr.strip()
            combined = (stdout + "\n" + stderr).strip() if stderr else stdout

            return {
                "success": proc.returncode == 0,
                "output": combined,
                "stdout": stdout,
                "stderr": stderr,
                "returncode": proc.returncode
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "output": "", "error": f"Command timed out after {timeout}s"}
        except Exception as e:
            return {"success": False, "output": "", "error": str(e)}

    def _run_adb_bytes(self, args: List[str], timeout: int = 15) -> Tuple[bool, bytes, str]:
        """Run an ADB command and return raw bytes (used for screencap)."""
        adb = self.adb_path
        if not adb:
            return False, b"", "ADB is not installed."

        cmd = [adb] + args
        try:
            creationflags = 0
            if sys.platform == "win32":
                creationflags = subprocess.CREATE_NO_WINDOW

            proc = subprocess.run(
                cmd,
                capture_output=True,
                timeout=timeout,
                creationflags=creationflags
            )
            if proc.returncode == 0:
                return True, proc.stdout, ""
            return False, b"", proc.stderr.decode("utf-8", errors="replace")
        except Exception as e:
            return False, b"", str(e)

    def pair_device(self, ip_port: str, code: str, nickname: Optional[str] = None) -> Dict[str, Any]:
        """Pair with an Android 11+ device using pairing port and 6-digit code."""
        ip_port = ip_port.strip()
        code = code.strip()

        if not ip_port:
            return {"success": False, "message": "IP and pairing port cannot be empty (e.g. 192.168.1.5:37123)"}
        if not code:
            return {"success": False, "message": "6-digit Pairing code cannot be empty"}

        # Format validation
        if ":" not in ip_port:
            return {"success": False, "message": "Port missing. Format must be IP:PORT (e.g. 192.168.1.5:37123)"}

        ip = ip_port.split(":")[0]

        # Cloud container safeguard: Cloud servers (Render/AWS/etc.) cannot route to private RFC1918 IPs
        if os.environ.get("RENDER") and (ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("172.")):
            return {
                "success": False,
                "message": f"Cloud limitation: Render runs in a remote cloud datacenter and cannot reach your private home Wi-Fi IP ({ip}). Run AirADB locally on your PC (http://localhost:8765) or use WebUSB in Chrome to connect!",
                "raw": "Private network IP not reachable from cloud container"
            }

        res = self._run_adb(["pair", ip_port, code], timeout=20)
        output = res.get("output", "")

        # Check for success indicators
        if "Successfully paired to" in output or "already paired" in output.lower():
            self._save_to_history(ip, ip_port.split(":")[1], nickname or f"Phone ({ip})", "paired")
            return {
                "success": True,
                "message": f"Successfully paired to {ip_port}!",
                "raw": output,
                "ip": ip
            }
        else:
            err_msg = output or res.get("error", "Pairing failed. Make sure the pairing popup is currently open on your phone.")
            return {
                "success": False,
                "message": f"Pairing failed: {err_msg}",
                "raw": output
            }

    def connect_device(self, ip_port: str, nickname: Optional[str] = None) -> Dict[str, Any]:
        """Connect to an Android device over Wi-Fi (IP:PORT)."""
        ip_port = ip_port.strip()
        if not ip_port:
            return {"success": False, "message": "IP and Port required (e.g. 192.168.1.5:5555 or 192.168.1.5:41235)"}

        if ":" not in ip_port:
            ip_port = f"{ip_port}:5555"

        ip, port = ip_port.split(":", 1)

        # Cloud container safeguard: Cloud servers (Render/AWS/etc.) cannot route to private RFC1918 IPs
        if os.environ.get("RENDER") and (ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("172.")):
            return {
                "success": False,
                "message": f"Cloud limitation: Render runs in a remote cloud datacenter and cannot reach your private home Wi-Fi IP ({ip}). Run AirADB locally on your PC (http://localhost:8765) or use WebUSB in Chrome to connect!",
                "raw": "Private network IP not reachable from cloud container",
                "hint": "Private home Wi-Fi IPs (192.168.x.x) are not reachable from cloud servers over the public internet."
            }

        res = self._run_adb(["connect", ip_port], timeout=15)
        output = res.get("output", "")

        if "connected to" in output.lower() and "cannot connect" not in output.lower() and "failed" not in output.lower():
            self._save_to_history(ip, port, nickname or f"Phone ({ip})", "connected")
            # Auto setup reverse port proxy so phone can open http://localhost:8765
            self._run_adb(["-s", ip_port, "reverse", "tcp:8765", "tcp:8765"], timeout=3)
            return {
                "success": True,
                "message": f"Connected successfully to {ip_port}!",
                "raw": output,
                "ip_port": ip_port
            }
        elif "already connected" in output.lower():
            self._save_to_history(ip, port, nickname or f"Phone ({ip})", "connected")
            self._run_adb(["-s", ip_port, "reverse", "tcp:8765", "tcp:8765"], timeout=3)
            return {
                "success": True,
                "message": f"Already connected to {ip_port}",
                "raw": output,
                "ip_port": ip_port
            }
        else:
            msg = f"Could not connect to {ip_port}. {output}".strip()
            hint = "Check that Wireless Debugging is toggled ON on your phone and both devices are on the same Wi-Fi network."
            if "failed to connect" in output.lower():
                msg = f"Could not connect to {ip_port}. Device is not paired yet!"
                hint = "In Android 11+, you must complete Step 1 (Pair Device) with your phone's 6-digit pairing code before connecting."
            return {
                "success": False,
                "message": msg,
                "raw": output,
                "hint": hint
            }

    def disconnect_device(self, ip_port: Optional[str] = None) -> Dict[str, Any]:
        """Disconnect wireless device or all wireless devices."""
        args = ["disconnect"]
        if ip_port:
            args.append(ip_port.strip())

        res = self._run_adb(args)
        return {
            "success": res["success"],
            "message": res["output"] or ("Disconnected device" if ip_port else "Disconnected all wireless devices")
        }

    def get_devices(self) -> List[Dict[str, Any]]:
        """Get list of connected devices with detailed metadata."""
        if not self.adb_path:
            return []

        res = self._run_adb(["devices", "-l"])
        if not res["success"]:
            return []

        lines = res["output"].strip().splitlines()
        devices = []

        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue

            parts = line.split()
            if len(parts) < 2:
                continue

            serial = parts[0]
            state = parts[1]

            is_wireless = ":" in serial or "._adb" in serial or "._tcp" in serial
            model = "Android Device"
            product = ""
            device_name = ""

            for part in parts[2:]:
                if part.startswith("model:"):
                    model = part.split(":", 1)[1].replace("_", " ")
                elif part.startswith("product:"):
                    product = part.split(":", 1)[1]
                elif part.startswith("device:"):
                    device_name = part.split(":", 1)[1]

            # Detailed queries if device is authorized
            battery_level = None
            android_version = None
            ip_address = None

            if state == "device":
                # Get Android Version
                v_res = self._run_adb(["-s", serial, "shell", "getprop", "ro.build.version.release"], timeout=3)
                if v_res["success"] and v_res["output"]:
                    android_version = v_res["output"].strip()

                # Get Battery
                b_res = self._run_adb(["-s", serial, "shell", "dumpsys", "battery"], timeout=3)
                if b_res["success"]:
                    match = re.search(r"level:\s*(\d+)", b_res["output"])
                    if match:
                        battery_level = int(match.group(1))

                # Get Wi-Fi IP if USB
                if not is_wireless:
                    ip_address = self._get_device_wifi_ip(serial)
                else:
                    ip_address = serial.split(":")[0]

            devices.append({
                "serial": serial,
                "state": state,
                "is_wireless": is_wireless,
                "model": model,
                "product": product,
                "device_name": device_name,
                "android_version": android_version,
                "battery_level": battery_level,
                "ip_address": ip_address
            })

        return devices

    def _get_device_wifi_ip(self, serial: str) -> Optional[str]:
        """Detect the Wi-Fi IP address of a device connected via USB."""
        # Method 1: ip route
        res = self._run_adb(["-s", serial, "shell", "ip", "route"], timeout=3)
        if res["success"]:
            for line in res["output"].splitlines():
                if "wlan0" in line and "src" in line:
                    parts = line.split()
                    if "src" in parts:
                        idx = parts.index("src")
                        if idx + 1 < len(parts):
                            return parts[idx + 1]

        # Method 2: ip addr show wlan0
        res = self._run_adb(["-s", serial, "shell", "ip", "-f", "inet", "addr", "show", "wlan0"], timeout=3)
        if res["success"]:
            match = re.search(r"inet\s+(\d+\.\d+\.\d+\.\d+)", res["output"])
            if match:
                return match.group(1)

        # Method 3: getprop dhcp.wlan0.ipaddress
        res = self._run_adb(["-s", serial, "shell", "getprop", "dhcp.wlan0.ipaddress"], timeout=3)
        if res["success"] and res["output"].strip():
            return res["output"].strip()

        return None

    def switch_usb_to_wireless(self, serial: Optional[str] = None, port: int = 5555) -> Dict[str, Any]:
        """Convert a USB-connected phone to Wireless TCP/IP mode and connect automatically."""
        devices = self.get_devices()
        usb_devices = [d for d in devices if not d["is_wireless"] and d["state"] == "device"]

        if not usb_devices:
            return {
                "success": False,
                "message": "No USB-connected Android devices found. Please connect your phone with a USB cable first and allow USB debugging."
            }

        target = None
        if serial:
            target = next((d for d in usb_devices if d["serial"] == serial), None)
        if not target:
            target = usb_devices[0]

        target_serial = target["serial"]
        ip = target.get("ip_address") or self._get_device_wifi_ip(target_serial)

        if not ip:
            return {
                "success": False,
                "message": "Could not detect Wi-Fi IP address for the phone. Ensure phone is connected to Wi-Fi."
            }

        # Step 1: Enable TCP/IP on device
        tcpip_res = self._run_adb(["-s", target_serial, "tcpip", str(port)], timeout=8)
        if not tcpip_res["success"]:
            return {
                "success": False,
                "message": f"Failed to enable TCP/IP port {port}: {tcpip_res.get('output', '')}"
            }

        time.sleep(1.5)

        # Step 2: Connect via IP
        target_ip_port = f"{ip}:{port}"
        conn_res = self.connect_device(target_ip_port, nickname=target["model"])

        if conn_res["success"]:
            return {
                "success": True,
                "message": f"Successfully switched {target['model']} to Wireless Debugging at {target_ip_port}! You can now safely unplug the USB cable.",
                "ip_port": target_ip_port,
                "device": target["model"]
            }
        else:
            return {
                "success": True,  # Port opened, connect might just need phone to acknowledge
                "message": f"TCP/IP mode enabled on {port}. If auto-connect didn't finish, tap Connect for {target_ip_port}.",
                "ip_port": target_ip_port,
                "connect_result": conn_res
            }

    def capture_screenshot(self, serial: str) -> Tuple[bool, bytes, str]:
        """Capture screen as PNG bytes."""
        return self._run_adb_bytes(["-s", serial, "exec-out", "screencap", "-p"], timeout=10)

    def get_logcat(self, serial: str, lines: int = 150, filter_str: Optional[str] = None) -> Dict[str, Any]:
        """Fetch recent logcat entries."""
        args = ["-s", serial, "logcat", "-d", "-v", "time", "-t", str(min(lines, 500))]
        res = self._run_adb(args, timeout=8)
        if not res["success"]:
            return {"success": False, "logs": [], "error": res.get("error", "")}

        raw_lines = res["output"].splitlines()
        if filter_str:
            f_lower = filter_str.lower()
            raw_lines = [l for l in raw_lines if f_lower in l.lower()]

        return {"success": True, "logs": raw_lines}

    def install_apk(self, serial: str, apk_path: str) -> Dict[str, Any]:
        """Install APK to wireless device."""
        if not os.path.exists(apk_path):
            return {"success": False, "message": f"APK file not found: {apk_path}"}

        res = self._run_adb(["-s", serial, "install", "-r", apk_path], timeout=60)
        if "success" in res.get("output", "").lower():
            return {"success": True, "message": "APK installed successfully!"}
        return {"success": False, "message": f"APK installation failed: {res.get('output', '')}"}

    def execute_shell(self, serial: str, command: str) -> Dict[str, Any]:
        """Run custom shell command on device."""
        res = self._run_adb(["-s", serial, "shell", command], timeout=10)
        return {
            "success": res["success"],
            "output": res["output"]
        }

    def restart_adb_server(self) -> Dict[str, Any]:
        """Kill and restart ADB server."""
        self._run_adb(["kill-server"], timeout=5)
        time.sleep(0.5)
        res = self._run_adb(["start-server"], timeout=8)
        return {
            "success": res["success"],
            "message": "ADB server restarted" if res["success"] else f"Failed to restart: {res.get('error', '')}"
        }

    def scan_mdns_services(self) -> List[Dict[str, Any]]:
        """Discover broadcasting Android devices via Zeroconf and ADB mDNS."""
        services = []
        seen_addresses = set()

        # 1. Native Python Zeroconf listener for Android Wireless Debugging
        try:
            from zeroconf import Zeroconf, ServiceBrowser

            class ADBListener:
                def __init__(self):
                    self.found = []

                def remove_service(self, zc, type_, name):
                    pass

                def update_service(self, zc, type_, name):
                    pass

                def add_service(self, zc, type_, name):
                    info = zc.get_service_info(type_, name)
                    if info and info.addresses:
                        ip = socket.inet_ntoa(info.addresses[0])
                        port = info.port
                        addr_str = f"{ip}:{port}"
                        if addr_str not in seen_addresses:
                            seen_addresses.add(addr_str)
                            self.found.append({
                                "name": name.split(".")[0],
                                "type": type_.strip("."),
                                "address": addr_str,
                                "source": "zeroconf"
                            })

            zc = Zeroconf()
            listener = ADBListener()
            browser_connect = ServiceBrowser(zc, "_adb-tls-connect._tcp.local.", listener)
            browser_pairing = ServiceBrowser(zc, "_adb-tls-pairing._tcp.local.", listener)
            time.sleep(0.8)
            zc.close()

            services.extend(listener.found)
        except Exception:
            pass

        # 2. Fallback to adb mdns services
        try:
            res = self._run_adb(["mdns", "services"], timeout=5)
            if res["success"]:
                for line in res["output"].splitlines():
                    line = line.strip()
                    if not line or "List of discovered" in line:
                        continue
                    parts = line.split()
                    if len(parts) >= 3:
                        addr = parts[2]
                        if addr not in seen_addresses:
                            seen_addresses.add(addr)
                            services.append({
                                "name": parts[0],
                                "type": parts[1],
                                "address": addr,
                                "source": "adb_mdns"
                            })
        except Exception:
            pass

        return services

    def scan_local_subnet_adb(self, subnet_prefix: Optional[str] = None, timeout_sec: float = 0.3) -> List[str]:
        """Scan local subnet for devices with open port 5555."""
        if not subnet_prefix:
            # Find local IP
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                s.close()
                parts = local_ip.split(".")
                subnet_prefix = f"{parts[0]}.{parts[1]}.{parts[2]}"
            except Exception:
                subnet_prefix = "192.168.1"

        discovered = []
        import concurrent.futures

        def _check_host(host_ip):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout_sec)
                result = sock.connect_ex((host_ip, 5555))
                sock.close()
                if result == 0:
                    return host_ip
            except Exception:
                pass
            return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(_check_host, f"{subnet_prefix}.{i}") for i in range(1, 255)]
            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                if res:
                    discovered.append(f"{res}:5555")

        return discovered

    def _load_history(self) -> List[Dict[str, Any]]:
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_to_history(self, ip: str, port: str, nickname: str, last_action: str):
        existing = next((h for h in self.history if h["ip"] == ip), None)
        entry = {
            "ip": ip,
            "port": port,
            "nickname": nickname,
            "last_action": last_action,
            "last_connected": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        if existing:
            self.history.remove(existing)
        self.history.insert(0, entry)
        self.history = self.history[:15]  # Keep last 15

        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2)
        except Exception:
            pass

    def remove_from_history(self, ip: str):
        self.history = [h for h in self.history if h.get("ip") != ip]
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2)
        except Exception:
            pass

    def get_battery_info(self, serial: str) -> Dict[str, Any]:
        """Query and parse battery telemetry from dumpsys battery."""
        if not serial:
            return {"success": False, "message": "Device serial is required."}
        res = self._run_adb(["-s", serial, "shell", "dumpsys", "battery"], timeout=6)
        if not res["success"] or not res.get("output"):
            err = res.get("error") or res.get("output") or "Device not responding"
            return {"success": False, "message": f"Failed to query battery: {err}"}

        data = {
            "success": True,
            "serial": serial,
            "level": 0,
            "temperature_c": 0.0,
            "temperature_f": 0.0,
            "voltage_v": 0.0,
            "status": "Unknown",
            "health": "Good",
            "power_source": "Battery",
            "technology": "Li-ion",
            "present": True
        }

        status_map = {
            1: "Unknown",
            2: "Charging",
            3: "Discharging",
            4: "Not Charging",
            5: "Full"
        }
        health_map = {
            1: "Unknown",
            2: "Good",
            3: "Overheat",
            4: "Dead",
            5: "Over Voltage",
            6: "Unspecified Failure",
            7: "Cold"
        }

        lines = res["output"].splitlines()
        ac = False
        usb = False
        wireless = False

        for line in lines:
            line = line.strip()
            if ":" not in line:
                continue
            k, v = [x.strip() for x in line.split(":", 1)]
            k_lower = k.lower()

            if k_lower == "level":
                try: data["level"] = int(v)
                except ValueError: pass
            elif k_lower == "temperature":
                try:
                    temp_raw = int(v)
                    c = temp_raw / 10.0
                    f = (c * 9.0 / 5.0) + 32.0
                    data["temperature_c"] = round(c, 1)
                    data["temperature_f"] = round(f, 1)
                except ValueError: pass
            elif k_lower == "voltage":
                try:
                    mv = int(v)
                    data["voltage_v"] = round(mv / 1000.0, 2)
                except ValueError: pass
            elif k_lower == "status":
                try:
                    st = int(v)
                    data["status"] = status_map.get(st, f"Status {st}")
                except ValueError:
                    data["status"] = v
            elif k_lower == "health":
                try:
                    hl = int(v)
                    data["health"] = health_map.get(hl, f"Health {hl}")
                except ValueError:
                    data["health"] = v
            elif k_lower == "technology":
                data["technology"] = v
            elif k_lower == "ac powered":
                ac = (v.lower() == "true")
            elif k_lower == "usb powered":
                usb = (v.lower() == "true")
            elif k_lower == "wireless powered":
                wireless = (v.lower() == "true")
            elif k_lower == "present":
                data["present"] = (v.lower() == "true")

        if ac:
            data["power_source"] = "AC Fast Charger"
        elif usb:
            data["power_source"] = "USB Powered"
        elif wireless:
            data["power_source"] = "Wireless Charging"
        elif data["status"] == "Charging":
            data["power_source"] = "Charging"
        else:
            data["power_source"] = "Discharging (Battery)"

        return data

    def send_text(self, serial: str, text: str) -> Dict[str, Any]:
        """Type text into focused input on phone using sanitized adb shell input text."""
        if not serial:
            return {"success": False, "message": "Device serial is required."}
        if not text:
            return {"success": False, "message": "Text cannot be empty."}

        lines = text.splitlines()
        for idx, line in enumerate(lines):
            escaped = ""
            for ch in line:
                if ch == " ":
                    escaped += "%s"
                elif ch in '\\"\'&<>;()|$`!*?[]{}':
                    escaped += f"\\{ch}"
                else:
                    escaped += ch

            if escaped:
                res = self._run_adb(["-s", serial, "shell", "input", "text", escaped], timeout=8)
                if not res["success"]:
                    return {"success": False, "message": res.get("output") or "Failed to send text"}

            if idx < len(lines) - 1:
                self._run_adb(["-s", serial, "shell", "input", "keyevent", "66"], timeout=5)

        return {"success": True, "message": "Text sent to phone successfully!"}

    def send_keyevent(self, serial: str, keycode: int) -> Dict[str, Any]:
        """Send Android keycode event (Media, Volume, Navigation)."""
        if not serial:
            return {"success": False, "message": "Device serial is required."}
        try:
            kc = int(keycode)
        except (ValueError, TypeError):
            return {"success": False, "message": "Invalid keycode."}

        res = self._run_adb(["-s", serial, "shell", "input", "keyevent", str(kc)], timeout=5)
        return {
            "success": res["success"],
            "keycode": kc,
            "message": f"Keyevent {kc} sent" if res["success"] else res.get("output")
        }

    def set_screen_timeout(self, serial: str, timeout_ms: int, keep_awake: bool = False) -> Dict[str, Any]:
        """Configure screen timeout and stay-awake state."""
        if not serial:
            return {"success": False, "message": "Device serial is required."}

        stay_arg = "true" if keep_awake else "false"
        self._run_adb(["-s", serial, "shell", "svc", "power", "stayon", stay_arg], timeout=5)

        if timeout_ms > 0:
            res = self._run_adb([
                "-s", serial, "shell", "settings", "put", "system", "screen_off_timeout", str(int(timeout_ms))
            ], timeout=5)
            if not res["success"]:
                return {"success": False, "message": res.get("output") or "Failed to set screen timeout"}

        desc = "Keep Awake" if keep_awake else f"{int(timeout_ms) // 1000}s"
        return {"success": True, "message": f"Screen timeout updated: {desc}"}

    def set_dark_mode(self, serial: str, enable: bool) -> Dict[str, Any]:
        """Toggle system Dark Mode (night mode) via cmd uimode."""
        if not serial:
            return {"success": False, "message": "Device serial is required."}
        mode = "yes" if enable else "no"
        res = self._run_adb(["-s", serial, "shell", "cmd", "uimode", "night", mode], timeout=5)
        return {
            "success": res["success"],
            "dark_mode": enable,
            "message": f"Dark mode turned {'ON' if enable else 'OFF'}" if res["success"] else res.get("output")
        }
