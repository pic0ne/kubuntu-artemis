#!/usr/bin/env python3
"""Install Artemis assets locally, with a manifest-backed restore point."""
from pathlib import Path
import configparser, datetime, json, re, shutil, subprocess, zipfile

ROOT = Path(__file__).resolve().parents[1]
HOME = Path.home()
if (ROOT / 'backups/latest').exists():
    raise SystemExit('An original restore point already exists. Assets are installed; use layout.js for layout changes.')
subprocess.run(['python3', str(ROOT / 'scripts/prepare.py'), '--check'], check=True)
BACKUP = ROOT / 'backups' / ('original-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
BACKUP.mkdir(parents=True)
manifest = []

def save(rel):
    path = HOME / rel
    if any(item['path'] == rel for item in manifest):
        return path
    exists = path.exists() or path.is_symlink()
    manifest.append({'path': rel, 'existed': exists})
    if exists:
        out = BACKUP / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        if path.is_dir():
            shutil.copytree(path, out, symlinks=True)
        else:
            shutil.copy2(path, out, follow_symlinks=False)
    (BACKUP / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    return path

def copy(source, rel):
    dest = save(rel)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, dest, dirs_exist_ok=True, symlinks=True, ignore=shutil.ignore_patterns('.git', '__pycache__'))
    else:
        shutil.copy2(source, dest)
    return dest

def write(rel, content, executable=False):
    dest = save(rel)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content)
    if executable:
        dest.chmod(0o755)

for rel in ['.config/kdeglobals', '.config/kwinrc', '.config/plasmarc',
            '.config/plasmashellrc', '.config/plasma-org.kde.plasma.desktop-appletsrc',
            '.config/kscreenlockerrc', '.config/kcminputrc', '.config/konsolerc',
            '.config/dolphinrc', '.config/gtk-3.0/settings.ini', '.config/gtk-4.0/settings.ini',
            '.config/gtkrc', '.config/gtkrc-2.0', '.local/share/konsole',
            '.local/share/color-schemes', '.config/kde-material-you-colors',
            '.local/share/kxmlgui5/konsole', '.local/share/kxmlgui6/konsole']:
    save(rel)

local = HOME / '.local/share/artemis'
save('.local/share/artemis')
copy(ROOT / 'assets/python', '.local/share/artemis/python')
runtime = ROOT / 'assets/runtime'
for deb in (ROOT / 'assets/debs').glob('*.deb'):
    subprocess.run(['dpkg-deb', '-x', str(deb), str(runtime)], check=True)
copy(runtime, '.local/share/artemis/runtime')
copy(ROOT / 'assets/YAMIS', '.local/share/icons/yet-another-monochrome-icon-set')
index = HOME / '.local/share/icons/yet-another-monochrome-icon-set/index.theme'
index.write_text(index.read_text().replace('places/scalable', 'places/scalable-outlined').replace('mimetypes/scalable', 'mimetypes/scalable-outlined'))
decoration = copy(ROOT / 'assets/Graphite-kde-theme/aurorae/Graphite-dark-round', '.local/share/aurorae/themes/Graphite-dark-round') / 'decoration.svg'
def subdued_outline(match):
    return match.group(0).replace('class="ColorScheme-ButtonFocus"', '').replace('fill="currentColor"', 'fill="#4a4c54"')
decoration.write_text(re.sub(r'<(?:path|rect)\b[^>]*class="ColorScheme-ButtonFocus"[^>]*>', subdued_outline, decoration.read_text(), flags=re.S))
copy(ROOT / 'assets/kurve/package', '.local/share/plasma/plasmoids/luisbocanegra.audio.visualizer')
copy(ROOT / 'assets/kde-material-you-colors/src/plasmoid/package', '.local/share/plasma/plasmoids/luisbocanegra.kdematerialyou.colors')
for weight in ['Regular', 'Bold']:
    copy(ROOT / f'assets/SourceCodePro-{weight}.ttf', f'.local/share/fonts/SourceCodePro/SourceCodePro-{weight}.ttf')
for weight in ['Regular', 'Semibold', 'Bold']:
    copy(ROOT / f'assets/SourceSans3-{weight}.ttf', f'.local/share/fonts/SourceSans3/SourceSans3-{weight}.ttf')
with zipfile.ZipFile(ROOT / 'assets/krohnkite.kwinscript') as package:
    package.extractall(save('.local/share/kwin/scripts/krohnkite'))
copy(ROOT / 'assets/artemis-eclipse.jpg', '.local/share/wallpapers/Artemis-II/eclipse.jpg')
copy(ROOT / 'assets/artemis-earthset.jpg', '.local/share/wallpapers/Artemis-II/earthset.jpg')

write('.local/bin/cava', '#!/bin/sh\nexport LD_LIBRARY_PATH="' + str(local / 'runtime/usr/lib/x86_64-linux-gnu') + '${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"\nexec "' + str(local / 'runtime/usr/bin/cava') + '" "$@"\n', True)
write('.local/bin/kde-material-you-colors', '#!/usr/bin/python3\nimport sys\nsys.path.insert(0, ' + repr(str(local / 'python')) + ')\nfrom kde_material_you_colors.main import main\nmain()\n', True)
write('.local/bin/fastfetch', '#!/bin/sh\nexport LD_LIBRARY_PATH="' + str(local / 'runtime/usr/lib/x86_64-linux-gnu') + '${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"\nexec "' + str(local / 'runtime/usr/bin/fastfetch') + '" "$@"\n', True)
write('.local/bin/artemis-fetch', '#!/bin/sh\nexec "$HOME/.local/bin/fastfetch" --config "$HOME/.local/share/artemis/fastfetch.jsonc" "$@"\n', True)
ink = '38;2;180;182;197'
write('.local/share/artemis/fastfetch.jsonc', json.dumps({
    'logo': {'type': 'small', 'color': {'1': ink, '2': ink, '3': ink}},
    'display': {'separator': ': ', 'color': {'keys': ink, 'title': ink}},
    'modules': ['title', 'separator', 'os', 'host', 'kernel', 'uptime', 'packages', 'shell', 'display', 'de', 'wm', 'wmtheme', 'theme', 'icons', 'font', 'cursor', 'terminal', 'cpu', 'gpu', 'memory', 'disk', 'break', 'colors']
}, indent=2))
write('.local/bin/plasma-changeicons', '#!/bin/sh\nexec /usr/lib/x86_64-linux-gnu/libexec/plasma-changeicons "$@"\n', True)
write('.config/plasma-workspace/env/artemis.sh', '#!/bin/sh\nexport PATH="$HOME/.local/bin:$PATH"\nexport QML_IMPORT_PATH="$HOME/.local/share/artemis/runtime/usr/lib/x86_64-linux-gnu/qt6/qml${QML_IMPORT_PATH:+:$QML_IMPORT_PATH}"\n', True)
write('.config/kde-material-you-colors/config.conf', '''[CUSTOM]
light = False
ncolor = 0
iconsdark = yet-another-monochrome-icon-set
iconslight = yet-another-monochrome-icon-set
pywal = False
scheme_variant = 5
chroma_multiplier = 0.7
tone_multiplier = 1.0
frame_contrast = 0.2
contrast_level = 0
spec_version = 2021
konsole_opacity = 100
konsole_opacity_dark = 100
konsole_blur = False
main_loop_delay = 2
''')
write('.config/autostart/artemis-material-you.desktop', '[Desktop Entry]\nType=Application\nName=Artemis Material You Colors\nExec=' + str(HOME / '.local/bin/kde-material-you-colors') + '\nIcon=preferences-desktop-color\nX-KDE-autostart-after=panel\n')

def config(file, group, key, value):
    subprocess.run(['kwriteconfig6', '--file', file, '--group', group, '--key', key, str(value)], check=True)

font = 'Source Sans 3,11,-1,5,400,0,0,0,0,0,0,0,0,0,0,1'
mono = 'Source Code Pro,11,-1,5,400,0,0,0,0,0,0,0,0,0,0,1'
for key in ['font', 'menuFont', 'toolBarFont']:
    config('kdeglobals', 'General', key, font)
config('kdeglobals', 'General', 'smallestReadableFont', font.replace(',11,', ',9,'))
config('kdeglobals', 'General', 'fixed', mono)
config('kdeglobals', 'WM', 'activeFont', font.replace(',400,', ',600,'))
config('kwinrc', 'WM', 'activeFont', font.replace(',400,', ',600,'))
config('kdeglobals', 'KDE', 'widgetStyle', 'Breeze')
config('kdeglobals', 'Icons', 'Theme', 'yet-another-monochrome-icon-set')
config('plasmarc', 'Theme', 'name', 'default')
config('kcminputrc', 'Mouse', 'cursorTheme', 'breeze_cursors')
config('kcminputrc', 'Mouse', 'cursorSize', '24')
for key, value in {'library':'org.kde.kwin.aurorae', '__aurorae__svg__':'Graphite-dark-round', 'theme':'__aurorae__svg__Graphite-dark-round', 'BorderSize':'None', 'ButtonsOnLeft':'M', 'ButtonsOnRight':'IAX'}.items():
    config('kwinrc', 'org.kde.kdecoration2', key, value)
config('kwinrc', 'Plugins', 'blurEnabled', 'true')
config('kwinrc', 'Plugins', 'contrastEnabled', 'true')
config('kwinrc', 'Plugins', 'krohnkiteEnabled', 'true')
# Floating panels overhang the work area by 8 px, so 24 px above and below leaves the same 16 px
# gutter as between windows. The 8 px side margins line windows up with the panel edges.
for key, value in {'screenGapTop': 24, 'screenGapBottom': 24, 'screenGapLeft': 8, 'screenGapRight': 8, 'screenGapBetween': 16}.items():
    config('kwinrc', 'Script-krohnkite', key, value)
# Like komorebi, focusing or moving past the edge may cross to another monitor but never to another desktop.
config('kwinrc', 'Script-krohnkite', 'focusMoveVDesktopsNormal', 'false')
config('kscreenlockerrc', 'Greeter', 'Theme', 'org.kde.breeze.desktop')
subprocess.run(['kwriteconfig6', '--file', 'kscreenlockerrc', '--group', 'Greeter', '--group', 'Wallpaper', '--group', 'org.kde.image', '--group', 'General', '--key', 'Image', str(HOME / '.local/share/wallpapers/Artemis-II/earthset.jpg')], check=True)
config('konsolerc', 'Desktop Entry', 'DefaultProfile', 'Artemis.profile')
config('konsolerc', 'MainWindow', 'MenuBar', 'Disabled')
config('dolphinrc', 'General', 'ShowFullPath', 'false')
config('dolphinrc', 'IconsMode', 'IconSize', '128')
for gtk in ['gtk-3.0', 'gtk-4.0']:
    path = HOME / '.config' / gtk / 'settings.ini'
    cp = configparser.ConfigParser(interpolation=None)
    cp.optionxform = str
    cp.read(path)
    if not cp.has_section('Settings'):
        cp.add_section('Settings')
    cp['Settings'].update({'gtk-theme-name':'Breeze-Dark', 'gtk-icon-theme-name':'yet-another-monochrome-icon-set', 'gtk-font-name':'Source Sans 3 11', 'gtk-monospace-font-name':'Source Code Pro 11', 'gtk-application-prefer-dark-theme':'true'})
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w') as out:
        cp.write(out)
konsole = HOME / '.local/share/konsole'
konsole.mkdir(parents=True, exist_ok=True)
(konsole / 'Artemis.profile').write_text('[General]\nName=Artemis\nParent=FALLBACK/\n[Appearance]\nFont=' + mono + '\nColorScheme=MaterialYou\n[Scrolling]\nScrollBarPosition=2\n')
subprocess.run(['fc-cache', '-f', str(HOME / '.local/share/fonts')], check=True)
subprocess.run([str(HOME / '.local/bin/plasma-changeicons'), 'yet-another-monochrome-icon-set'], check=True)
subprocess.run(['dbus-send', '--session', '--type=signal', '/KGlobalSettings', 'org.kde.KGlobalSettings.notifyChange', 'int32:0', 'int32:0'])
subprocess.run(['dbus-send', '--session', '--type=signal', '/KGlobalSettings', 'org.kde.KGlobalSettings.notifyChange', 'int32:1', 'int32:0'])
subprocess.run(['dbus-send', '--session', '--type=signal', '/KDEPlatformTheme', 'org.kde.KDEPlatformTheme.refreshFonts'])
# Reloading gtkconfig regenerates xsettingsd, which GTK and Chromium apps on X11 read fonts from.
for method in ['unloadModule', 'loadModule']:
    subprocess.run(['dbus-send', '--session', '--type=method_call', '--dest=org.kde.kded6', '/kded', 'org.kde.kded6.' + method, 'string:gtkconfig'])
(ROOT / 'backups/latest').write_text(BACKUP.name + '\n')
print('Restore point:', BACKUP)
print('Installed assets. Apply the layout and restart Plasma to activate local QML modules.')
