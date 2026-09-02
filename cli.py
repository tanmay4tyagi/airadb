import os
import sys
import time
from adb_manager import ADBManager

# Ensure UTF-8 output in Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

adb = ADBManager()


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_banner():
    print("""
================================================================
       🚀 AirADB CLI — Android Wireless Debugging Assistant
================================================================
""")
    if adb.is_installed():
        ver = adb.get_version()
        print(f"  [✓] ADB Status: Active ({ver})")
        print(f"  [✓] Path: {adb.adb_path}")
    else:
        print("  [!] ADB Status: NOT FOUND. Option 8 will auto-install it.")
    print("=" * 64)


def menu():
    while True:
        clear_screen()
        print_banner()
        print("""
  [1] 📱 Pair Device with Pairing Code (Android 11+)
  [2] 🔌 Connect to Wireless Device (IP:PORT)
  [3] ⚡ 1-Click USB-to-Wireless Switch (Auto-detect IP)
  [4] 📋 List Connected Devices
  [5] ❌ Disconnect Wireless Device(s)
  [6] 🔍 Scan Local Wi-Fi Subnet for Devices
  [7] 📸 Capture Screenshot to Disk
  [8] ⬇️  Auto-Download & Install Official ADB Platform-Tools
  [9] 🌐 Launch AirADB Web Studio Dashboard (GUI)
  [0] 🚪 Exit
""")
        choice = input(" Select an option [0-9]: ").strip()

        if choice == "1":
            option_pair()
        elif choice == "2":
            option_connect()
        elif choice == "3":
            option_usb_switch()
        elif choice == "4":
            option_list_devices()
        elif choice == "5":
            option_disconnect()
        elif choice == "6":
            option_scan()
        elif choice == "7":
            option_screenshot()
        elif choice == "8":
            option_install_adb()
        elif choice == "9":
            option_launch_web()
        elif choice == "0":
            print("\nGoodbye!")
            break
        else:
            print("\nInvalid choice. Press Enter to continue...")
            input()


def option_pair():
    print("\n--- Pair Device (Android 11+) ---")
    print("Go to Developer Options > Wireless Debugging > Pair device with pairing code.")
    ip_port = input("Enter Phone IP:Port (e.g. 192.168.1.5:37123): ").strip()
    code = input("Enter 6-digit Pairing Code: ").strip()
    nickname = input("Device Nickname (optional): ").strip()

    if not ip_port or not code:
        print("Error: IP:Port and Code are required.")
        input("\nPress Enter to continue...")
        return

    print("\nPairing...")
    res = adb.pair_device(ip_port, code, nickname or None)
    if res["success"]:
        print(f"\n✅ {res['message']}")
        # Ask to connect now
        conn = input("Do you want to connect now? [Y/n]: ").strip().lower()
        if conn != "n":
            conn_port = input("Enter Connection Port from phone screen (or press enter if same): ").strip()
            target = f"{res['ip']}:{conn_port}" if conn_port else ip_port
            c_res = adb.connect_device(target, nickname)
            print(f"Connection result: {c_res['message']}")
    else:
        print(f"\n❌ {res['message']}")

    input("\nPress Enter to return to menu...")


def option_connect():
    print("\n--- Connect to Device ---")
    ip_port = input("Enter IP:Port (e.g. 192.168.1.5:41235 or 192.168.1.5:5555): ").strip()
    nickname = input("Device Nickname (optional): ").strip()

    if not ip_port:
        print("Error: IP:Port is required.")
        input("\nPress Enter to continue...")
        return

    print("\nConnecting...")
    res = adb.connect_device(ip_port, nickname or None)
    if res["success"]:
        print(f"\n✅ {res['message']}")
    else:
        print(f"\n❌ {res['message']}")
        if "hint" in res:
            print(f"💡 Hint: {res['hint']}")

    input("\nPress Enter to return to menu...")


def option_usb_switch():
    print("\n--- 1-Click USB to Wireless Switch ---")
    print("Plug your phone via USB cable and ensure USB Debugging is allowed.")
    input("Press Enter when ready...")

    print("Switching...")
    res = adb.switch_usb_to_wireless()
    if res["success"]:
        print(f"\n✅ {res['message']}")
    else:
        print(f"\n❌ {res['message']}")

    input("\nPress Enter to return to menu...")


def option_list_devices():
    print("\n--- Connected Devices ---")
    devices = adb.get_devices()
    if not devices:
        print("No devices connected.")
    else:
        for idx, d in enumerate(devices, 1):
            dtype = "📶 Wi-Fi" if d["is_wireless"] else "🔌 USB"
            battery = f"{d['battery_level']}%" if d['battery_level'] is not None else "N/A"
            os_ver = f"Android {d['android_version']}" if d['android_version'] else ""
            print(f"  [{idx}] {d['model']} ({dtype})")
            print(f"      Serial/IP : {d['serial']}")
            print(f"      Status    : {d['state']}")
            print(f"      OS / Batt : {os_ver} | Battery: {battery}")
            if d.get("ip_address"):
                print(f"      Wi-Fi IP  : {d['ip_address']}")
            print()

    input("Press Enter to return to menu...")


def option_disconnect():
    print("\n--- Disconnect Devices ---")
    print("  [1] Disconnect all wireless devices")
    print("  [2] Disconnect specific IP:Port")
    sub = input("Select [1/2]: ").strip()

    if sub == "1":
        res = adb.disconnect_device()
        print(f"\n{res['message']}")
    elif sub == "2":
        target = input("Enter IP:Port to disconnect: ").strip()
        if target:
            res = adb.disconnect_device(target)
            print(f"\n{res['message']}")
    input("\nPress Enter to return to menu...")


def option_scan():
    print("\n--- Scanning Local Wi-Fi Subnet for Android ADB devices... ---")
    print("Please wait a moment...")
    devices = adb.scan_local_subnet_adb()
    mdns = adb.scan_mdns_services()

    if not devices and not mdns:
        print("\nNo devices discovered on port 5555 or mDNS.")
    else:
        print(f"\nFound {len(devices) + len(mdns)} device(s):")
        for dev in devices:
            print(f"  • {dev} (TCP/IP 5555)")
        for m in mdns:
            print(f"  • {m['address']} ({m['name']} / {m['type']})")

    input("\nPress Enter to return to menu...")


def option_screenshot():
    devices = [d for d in adb.get_devices() if d["state"] == "device"]
    if not devices:
        print("\nNo active devices connected.")
        input("Press Enter to return...")
        return

    target = devices[0]["serial"]
    if len(devices) > 1:
        print("\nMultiple devices found:")
        for idx, d in enumerate(devices, 1):
            print(f"  [{idx}] {d['model']} ({d['serial']})")
        sel = input("Select device number: ").strip()
        try:
            target = devices[int(sel) - 1]["serial"]
        except Exception:
            pass

    filename = f"screenshot_{int(time.time())}.png"
    filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

    print(f"\nCapturing screen from {target}...")
    success, img_bytes, err = adb.capture_screenshot(target)
    if success and img_bytes:
        with open(filepath, "wb") as f:
            f.write(img_bytes)
        print(f"✅ Screenshot saved to: {filepath}")
    else:
        print(f"❌ Failed to capture screenshot: {err}")

    input("\nPress Enter to return to menu...")


def option_install_adb():
    print("\n--- Download & Install Google Android Platform-Tools ---")
    print("This will download the official platform-tools zip from Google and extract to ./bin/platform-tools")
    confirm = input("Proceed? [Y/n]: ").strip().lower()
    if confirm == "n":
        return

    res = adb.download_and_install_platform_tools(lambda msg: print(f"  {msg}"))
    if res["success"]:
        print(f"\n✅ {res['message']}")
        print(f"  ADB Path: {res['adb_path']}")
        print(f"  Version:  {res['version']}")
    else:
        print(f"\n❌ {res['message']}")

    input("\nPress Enter to return to menu...")


def option_launch_web():
    import webbrowser
    print("\nStarting AirADB Web Studio...")
    os.system(f'start "" "{sys.executable}" server.py')
    print("Web dashboard launched in background! Open http://localhost:8765 in your browser.")
    input("\nPress Enter to return to menu...")


if __name__ == "__main__":
    menu()
