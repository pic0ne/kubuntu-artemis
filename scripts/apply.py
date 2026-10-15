#!/usr/bin/env python3
"""Apply prepared Artemis assets and activate the Plasma layout."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


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
    subprocess.run(["systemd-run", "--user", "--unit=artemis-material-you", "--collect", str(home / ".local/bin/kde-material-you-colors")], check=True)
    print("Artemis is active. Restore with: python3 scripts/restore.py")


if __name__ == "__main__":
    main()
