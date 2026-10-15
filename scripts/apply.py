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
SHIFT, ALT = 0x02000000, 0x08000000
DESKTOPS = 5
# The Alt layer of the komorebi rice on Windows, so both desktops share one set of keys. Komorebi's
# stacking keys have no Krohnkite counterpart, and kglobalaccel cannot grab Enter on X11, so
# Alt+Shift+Enter (set master) stays unbound. Alt+X and Alt+Y rotate instead of mirroring.
TILING = {
    "KrohnkiteFocusLeft": ALT | ord("H"),
    "KrohnkiteFocusDown": ALT | ord("J"),
    "KrohnkiteFocusUp": ALT | ord("K"),
    "KrohnkiteFocusRight": ALT | ord("L"),
    "KrohnkiteShiftLeft": ALT | SHIFT | ord("H"),
    "KrohnkiteShiftDown": ALT | SHIFT | ord("J"),
    "KrohnkiteShiftUp": ALT | SHIFT | ord("K"),
    "KrohnkiteShiftRight": ALT | SHIFT | ord("L"),
    "KrohnkiteToggleFloat": ALT | ord("T"),
    "KrohnkiteMonocleLayout": ALT | SHIFT | ord("F"),
    "KrohnkiteRotate": ALT | ord("X"),
    "KrohnkiteRotatePart": ALT | ord("Y"),
    "KrohnkiteTileLayout": ALT | SHIFT | ord("R"),
    "KrohnkiteFloatAll": ALT | ord("P"),
}
# KWin actions that keep their Plasma keys and gain the komorebi one.
EXTRA = {"Window Close": ALT | ord("Q"), "Window Minimize": ALT | ord("M")} | {
    f"Switch to Desktop {n}": ALT | ord(str(n)) for n in range(1, DESKTOPS + 1)}


def key_levels(keysym):
    """Qt keys for the plain and shifted symbols of the physical key that types `keysym`."""
    x11 = ctypes.cdll.LoadLibrary("libX11.so.6")
    x11.XOpenDisplay.restype = ctypes.c_void_p
    x11.XKeysymToKeycode.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    x11.XkbKeycodeToKeysym.argtypes = [ctypes.c_void_p, ctypes.c_ubyte, ctypes.c_int, ctypes.c_int]
    x11.XkbKeycodeToKeysym.restype = ctypes.c_ulong
    display = x11.XOpenDisplay(None)
    try:
        keycode = x11.XKeysymToKeycode(display, keysym)
        plain, shifted = (x11.XkbKeycodeToKeysym(display, keycode, 0, level) for level in (0, 1))
    finally:
        x11.XCloseDisplay(ctypes.c_void_p(display))
    # Latin-1 keysyms equal their Qt key codes; anything else falls back to Shift plus the plain key.
    return plain, shifted if shifted < 0x100 else SHIFT | plain


def layout_shortcuts():
    # kglobalaccel matches Alt+Shift on a symbol key only when registered as the shifted symbol, for example
    # Alt+" for Alt+Shift+2 on a Spanish layout, so these keys come from the active keyboard layout.
    plus, plus_shifted = key_levels(ord("+"))
    minus, minus_shifted = key_levels(ord("-"))
    return {
        "KrohnkitegrowWidth": ALT | plus,
        "KrohnkiteShrinkWidth": ALT | minus,
        "KrohnkiteGrowHeight": ALT | plus_shifted,
        "KrohnkiteShrinkHeight": ALT | minus_shifted,
    } | {f"Window to Desktop {n}": ALT | key_levels(ord(str(n)))[1] for n in range(1, DESKTOPS + 1)}


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
    current = lambda action: [int(k) for k in accel.shortcut(["kwin", action, "", ""]) if int(k)]
    assigned = TILING | layout_shortcuts()
    # Krohnkite's own Meta defaults are cleared so Meta stays with Plasma.
    plan = {str(action): [] for action in component.shortcutNames() if str(action).startswith("Krohnkite")}
    plan |= {action: [key] for action, key in assigned.items()}
    plan |= {action: current(action) + [key] for action, key in EXTRA.items()}
    previous = []
    for action, keys in plan.items():
        previous.append(["kwin", action, current(action)])
        accel.setForeignShortcut(["kwin", action, "", ""], dbus.Array(keys, signature="i"))
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
