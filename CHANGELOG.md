# Changelog

## 1.0.1

- The menu now closes when clicking outside it, including when JWM does not change the focused window after clicking the desktop.
- Added a temporary pointer grab while the menu is visible.
- The pointer grab is released correctly when opening context menus or dialogs and restored after they close.
- `ESSORA_PYMENU_NO_AUTO_CLOSE=1` continues to disable automatic closing.

## 1.0.0

- Rewrote the main application menu in C and GTK3.
- Categories and applications are loaded only from `essora-menu.xml`.
- Preserved support for regular applications, Flatpak, AppImage, and Wine.
- Replaced visible emoji characters with dedicated SVG icons.
- Retained auxiliary generators and configuration tools in Python.
- Added a build system that generates a Debian package directory ready for packaging.

## Credits

- **Original Python 3 version:** nilsonmorales
- **C and GTK3 rewrite:** josejp2424
