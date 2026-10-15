// Native Plasma 6 scripting API, dimensions in logical pixels.
// Original panels are preserved in backups before this script is evaluated.
function configure(widget, group, values) {
    widget.currentConfigGroup = group;
    Object.keys(values).forEach(function(key) { widget.writeConfig(key, values[key]); });
    widget.reloadConfig();
}

panels().forEach(function(panel) { panel.remove(); });
var screen = screenGeometry(0);
var home = userDataPath();
var desktopsList = desktops();
desktopsList.forEach(function(desktop) {
    desktop.wallpaperPlugin = 'org.kde.image';
    configure(desktop, ['Wallpaper', 'org.kde.image', 'General'], {
        Image: 'file://' + home + '/.local/share/wallpapers/Artemis-II/eclipse.jpg',
        FillMode: 2,
        DynamicMode: 0
    });
    // Filter desktop launchers out of view without moving or deleting their files.
    configure(desktop, ['General'], {filter: '*', filterMode: 2});
});

var top = new Panel;
top.location = 'top';
top.height = 40;
top.lengthMode = 'fill';
top.alignment = 'center';
top.hiding = 'none';
configure(top, ['General'], {floating: true, opacityMode: 1});
var menu = top.addWidget('org.kde.plasma.kickoff');
configure(menu, ['General'], {icon: 'start-here-kde'});
var left = top.addWidget('org.kde.plasma.panelspacer');
configure(left, ['General'], {expanding: true});
var clock = top.addWidget('org.kde.plasma.digitalclock');
configure(clock, ['Appearance'], {
    showDate: true, showSeconds: 0, use24hFormat: 2,
    dateFormat: 'custom', customDateFormat: 'dd/MM/yyyy',
    fontFamily: 'Source Code Pro', fontSize: 14, autoFontAndSize: false, dateDisplayFormat: 2,
    fontWeight: 400
});
var right = top.addWidget('org.kde.plasma.panelspacer');
configure(right, ['General'], {expanding: true});
var media = top.addWidget('org.kde.plasma.mediacontroller');
var tray = top.addWidget('org.kde.plasma.systemtray');
configure(tray, ['General'], {scaleIconsToFit: false, iconSize: 1});

var dock = new Panel;
dock.location = 'bottom';
dock.height = 64;
dock.alignment = 'center';
dock.lengthMode = 'fit';
dock.hiding = 'none';
configure(dock, ['General'], {floating: true, opacityMode: 1});
var tasks = dock.addWidget('org.kde.plasma.icontasks');
configure(tasks, ['General'], {
    launchers: ['applications:org.kde.dolphin.desktop', 'preferred://browser', 'applications:org.kde.konsole.desktop'],
    showOnlyCurrentDesktop: true, showOnlyCurrentActivity: true,
    groupingStrategy: 1, iconSpacing: 0, maxStripes: 1, showToolTips: true
});

var desktop = desktopForScreen(0);
desktop.widgets('luisbocanegra.audio.visualizer').forEach(function(widget) { widget.remove(); });
// Desktop widget positions are relative to the area below the top panel, and Plasma
// ignores geometry changes after a widget is added, so place it once with the gap built in.
var visualHeight = 144;
var visual = desktop.addWidget('luisbocanegra.audio.visualizer', 0,
    screen.height - top.height - dock.height - visualHeight - 40, screen.width, visualHeight);
configure(visual, ['General'], {
    visualizerStyle: 0, barCount: 240, barWidth: 2, barGap: 7,
    framerate: 30, desktopWidgetBg: 0, orientation: 1,
    hideWhenIdle: true, pauseOnFullScreenWindow: false,
    disableLeftClick: true, hideToolTip: true,
    noiseReduction: 77, inputMethod: 'pulse', inputSource: 'auto',
    minimumLength: screen.width, length: screen.width
});
configure(visual, ['General'], {barColors: JSON.stringify({enabled:true, sourceType:0, custom:'#b4b6c5', alpha:0.85})});
print('Artemis layout applied. Top panel: ' + top.id + ', dock: ' + dock.id + ', visualizer: ' + visual.id);
