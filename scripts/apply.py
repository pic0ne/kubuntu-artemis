#!/usr/bin/env python3
"""Apply prepared Artemis assets and activate the Plasma layout."""
import argparse
import ctypes
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
META, SHIFT, CTRL, ALT = 0x10000000, 0x02000000, 0x04000000, 0x08000000
SCREENSAVER = 0x010000BA
# Krohnkite's defaults collide with Plasma's own shortcuts. Meta+T and Meta+L go to the tiler, and Lock
# Session moves to Ctrl+Alt+L. Krohnkite actions displaced by other Plasma keys move to free letters.
# An entry that frees a key comes before the entry that takes it.
SHORTCUTS = [
    ("kwin", "Edit Tiles", []),
    ("ksmserver", "Lock Session", [CTRL | ALT | ord("L"), SCREENSAVER]),
    ("kwin", "KrohnkiteTileLayout", [META | ord("T")]),
    ("kwin", "KrohnkiteFocusRight", [META | ord("L")]),
    ("kwin", "KrohnkiteIncrease", [META | ord("O")]),
    ("kwin", "KrohnkiteDecrease", [META | SHIFT | ord("O")]),
    ("kwin", "KrohnkiteRotate", [META | ord("Y")]),
    ("kwin", "KrohnkiteRotatePart", [META | SHIFT | ord("Y")]),
    ("kwin", "KrohnkiteFocusNext", [META | ord("N")]),
    ("kwin", "KrohnkiteFocusPrev", [META | SHIFT | ord("N")]),
]

DESKTOPS = 4


def shifted_digits():
    """Map 1-4 to the Qt keys of their shifted symbols on the active layout (Spanish: ! " · $)."""
    x11 = ctypes.cdll.LoadLibrary("libX11.so.6")
    x11.XOpenDisplay.restype = ctypes.c_void_p
    x11.XKeysymToKeycode.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    x11.XkbKeycodeToKeysym.argtypes = [ctypes.c_void_p, ctypes.c_ubyte, ctypes.c_int, ctypes.c_int]
    x11.XkbKeycodeToKeysym.restype = ctypes.c_ulong
    display = x11.XOpenDisplay(None)
    try:
        return {n: x11.XkbKeycodeToKeysym(display, x11.XKeysymToKeycode(display, ord(str(n))), 0, 1) for n in range(1, DESKTOPS + 1)}
    finally:
        x11.XCloseDisplay(ctypes.c_void_p(display))


def desktop_shortcuts():
    # kglobalaccel matches Alt+Shift+2 only when registered as the shifted symbol, Alt+" on a Spanish layout.
    # Latin-1 keysyms equal their Qt key codes; anything else falls back to the digit.
    return [("kwin", f"Window to Desktop {n}", [ALT | (symbol if symbol < 0x100 else SHIFT | ord(str(n)))])
            for n, symbol in shifted_digits().items()]


def add_desktops(bus, backup):
    import dbus
    path = bus.get_object("org.kde.KWin", "/VirtualDesktopManager")
    manager = dbus.Interface(path, "org.kde.KWin.VirtualDesktopManager")
    desktops = lambda: [str(desktop[1]) for desktop in path.Get("org.kde.KWin.VirtualDesktopManager", "desktops", dbus_interface="org.freedesktop.DBus.Properties")]
    existing = desktops()
    for position in range(len(existing), DESKTOPS):
        manager.createDesktop(position, f"Desktop {position + 1}")
    (backup / "desktops.json").write_text(json.dumps([desktop for desktop in desktops() if desktop not in existing], indent=2))


def bind_shortcuts(bus, backup):
    import dbus
    component = dbus.Interface(bus.get_object("org.kde.kglobalaccel", "/component/kwin"), "org.kde.kglobalaccel.Component")
    for _ in range(50):
        if "KrohnkiteTileLayout" in component.shortcutNames():
            break
        time.sleep(0.1)
    else:
        raise SystemExit("Krohnkite did not register its shortcuts.")
    accel = dbus.Interface(bus.get_object("org.kde.kglobalaccel", "/kglobalaccel"), "org.kde.KGlobalAccel")
    previous = []
    for owner, action, keys in SHORTCUTS + desktop_shortcuts():
        action_id = [owner, action, "", ""]
        previous.append([owner, action, [int(k) for k in accel.shortcut(action_id)]])
        accel.setForeignShortcut(action_id, dbus.Array(keys, signature="i"))
    # Replayed in reverse by restore.py so each key is freed before its original owner takes it back.
    (backup / "shortcuts.json").write_text(json.dumps(previous, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Run prerequisite checks without changing the desktop.")
    args = parser.parse_args()
    required = ["kwriteconfig6", "systemctl", "dpkg-deb", "fc-cache", "dbus-send"]
    missing = [name for name in required if shutil.which(name) is None]
    if missing:
        raise SystemExit("Missing desktop tools: " + ", ".join(missing))
    import dbus
    import gi  # Runtime dependency used by the Material You backend.
    subprocess.run([sys.executable, str(ROOT / "scripts/prepare.py"), "--check"], check=True)
    bus = dbus.SessionBus()
    if not bus.name_has_owner("org.kde.plasmashell"):
        raise SystemExit("Run this script from an active Plasma desktop session.")
    if args.check:
        print("Desktop prerequisites verified. No settings were changed.")
        return
    if (ROOT / "backups/latest").exists():
        raise SystemExit("A restore point already exists. Restore the previous setup before applying again.")
    subprocess.run([sys.executable, str(ROOT / "scripts/install.py")], check=True)
    plasma = dbus.Interface(bus.get_object("org.kde.plasmashell", "/PlasmaShell"), "org.kde.PlasmaShell")
    print(plasma.evaluateScript((ROOT / "scripts/layout.js").read_text()))
    home = Path.home()
    path = str(home / ".local/bin") + os.pathsep + os.environ.get("PATH", "")
    qml_path = str(home / ".local/share/artemis/runtime/usr/lib/x86_64-linux-gnu/qt6/qml")
    subprocess.run(["systemctl", "--user", "set-environment", "PATH=" + path, "QML_IMPORT_PATH=" + qml_path], check=True)
    subprocess.run(["systemctl", "--user", "restart", "plasma-plasmashell.service"], check=True)
    dbus.Interface(bus.get_object("org.kde.KWin", "/KWin"), "org.kde.KWin").reconfigure()
    backup = ROOT / "backups" / Path((ROOT / "backups/latest").read_text().strip()).name
    add_desktops(bus, backup)
    bind_shortcuts(bus, backup)
    subprocess.run(["systemd-run", "--user", "--unit=artemis-material-you", "--collect", str(home / ".local/bin/kde-material-you-colors")], check=True)
    print("Artemis is active. Restore with: python3 scripts/restore.py")


if __name__ == "__main__":
    main()
