#!/usr/bin/env python3
"""Restore the saved pre-Artemis appearance. Does not close application windows."""
from pathlib import Path
import json, shutil, subprocess

root = Path(__file__).resolve().parents[1]
backup = root / 'backups' / Path((root / 'backups/latest').read_text().strip()).name
home = Path.home()
subprocess.run(['systemctl', '--user', 'stop', 'artemis-material-you.service'])
backend = home / '.local/bin/kde-material-you-colors'
if backend.exists():
    subprocess.run([str(backend), '--stop'])
subprocess.run(['systemctl', '--user', 'stop', 'plasma-plasmashell.service'], check=True)
for item in json.loads((backup / 'manifest.json').read_text()):
    path = home / item['path']
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    elif path.exists() or path.is_symlink():
        path.unlink()
    if item['existed']:
        src = backup / item['path']
        path.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, path, symlinks=True)
        else:
            shutil.copy2(src, path, follow_symlinks=False)
subprocess.run(['systemctl', '--user', 'unset-environment', 'QML_IMPORT_PATH'])
import dbus
bus = dbus.SessionBus()
bus.get_object('org.kde.KWin', '/KWin').reconfigure(dbus_interface='org.kde.KWin')
subprocess.run(['dbus-send', '--session', '--type=signal', '/KDEPlatformTheme', 'org.kde.KDEPlatformTheme.refreshFonts'])
subprocess.run(['dbus-send', '--session', '--type=signal', '/KGlobalSettings', 'org.kde.KGlobalSettings.notifyChange', 'int32:0', 'int32:0'])
subprocess.run(['systemctl', '--user', 'start', 'plasma-plasmashell.service'], check=True)
print('Restored appearance from', backup)
