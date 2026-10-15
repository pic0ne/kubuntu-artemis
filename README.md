# Artemis for Kubuntu

A basic monochrome lunar preset for KDE Plasma 6, built around NASA's Artemis II photography. Based on [KDE Artemis on r/unixporn](https://www.reddit.com/r/unixporn/comments/1shnpz9/kde_artemis/).

![Desktop with the Artemis II eclipse wallpaper, floating top panel, audio visualizer, and centered dock](docs/images/desktop.jpg)

![Lock screen with the Artemis II Earthset photograph](docs/images/lock-screen.jpg)

## What it sets up

| Component | Configuration |
| --- | --- |
| Colors | Breeze with dark Material You colors generated from the wallpaper |
| Icons | YAMIS, outlined variants |
| Window decoration | Graphite-dark-round with subdued outlines |
| Fonts | Source Sans 3 for the interface, Source Code Pro for terminals and the panel clock |
| Panels | Floating top bar with a centered clock, media controls, and the system tray, plus a floating dock |
| Visualizer | Kurve with thin monochrome CAVA bars, hidden when no audio plays |
| Terminal | Konsole profile and an `artemis-fetch` Fastfetch preset |

## Requirements

- Kubuntu 26.04 on x86_64 with Plasma 6.6 and Python 3.14.
- An active Plasma session, X11 or Wayland.
- Internet access for the first `prepare.py` run.

Nothing is installed system-wide and `sudo` is never used. Assets go under `~/.local`, and startup configuration goes under `~/.config`.

## Install

```sh
python3 scripts/prepare.py        # download pinned themes, fonts, wallpapers, and runtime packages
python3 scripts/apply.py --check  # verify prerequisites without changing anything
python3 scripts/apply.py          # back up the current look, install, and activate
```

`apply.py` replaces the panel layout and restarts Plasma. Open windows stay open. It refuses to run a second time while a restore point exists.

## Customize

- Edit `scripts/layout.js` to change panel geometry or the pinned dock apps before you install.
- Change color generation in the **KDE Material You Colors** widget or in `~/.config/kde-material-you-colors/config.conf`.
- Adjust font sizes in **System Settings > Colors & Themes > Fonts**.

## Restore

```sh
python3 scripts/restore.py
```

This stops the color service, restores every file the installer changed, and restarts Plasma. The restore point lives in `backups/` inside your checkout, so keep the checkout until you no longer need it.

## Credits

| Asset | Source |
| --- | --- |
| Original rice | [KDE Artemis on r/unixporn](https://www.reddit.com/r/unixporn/comments/1shnpz9/kde_artemis/) |
| Color generation | [KDE Material You Colors](https://github.com/luisbocanegra/kde-material-you-colors) |
| Icons | [Yet Another Monochrome Icon Set](https://bitbucket.org/dirn-typo/yet-another-monochrome-icon-set) by Dirn |
| Window decoration | [Graphite KDE theme](https://github.com/vinceliuice/Graphite-kde-theme) by vinceliuice |
| Audio visualizer | [Kurve](https://github.com/luisbocanegra/kurve) and [CAVA](https://github.com/karlstav/cava) |
| Fonts | [Source Sans 3](https://github.com/adobe-fonts/source-sans) and [Source Code Pro](https://github.com/adobe-fonts/source-code-pro) by Adobe |
| Desktop wallpaper | NASA, [Artemis II in Eclipse (art002e009301)](https://images.nasa.gov/details/art002e009301) |
| Lock screen wallpaper | NASA, [A New View of the Moon (art002e009287)](https://images.nasa.gov/details/art002e009287) |

Third-party assets keep their upstream licenses. They are downloaded at pinned revisions by `scripts/prepare.py`, not stored in this repository.
