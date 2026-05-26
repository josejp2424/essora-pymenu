# essora-pymenu
<p align="center">
<img src="assets/essorawm-pymenu.png">
</p>

# Essora PyMenu

Modern application menu for Essora Desktop with profiles, favorites, categories and desktop integration.

</div>

---

## About

Essora PyMenu is a fork based on the original PyMenuPup project:

Original project: [Woofshahenzup](https://github.com/Woofshahenzup/PyMenuPup)

This version has been adapted specifically for the Essora ecosystem, with modifications focused on desktop integration, user configuration, menu generation and Essora visual consistency.

Unlike a generic implementation, Essora PyMenu integrates directly with the Essora Desktop environment and its tools while maintaining a lightweight and customizable design.

---

## Features

### Desktop integration

* Full integration with Essora Desktop
* Integration with EssoraWM
* Integration with JWM and Tint2
* User profile support
* Profile image management
* Favorites support
* Search support
* Category filtering
* Multi-language support
* Theme support
* Dynamic icon loading
* Customizable layout
* Header customization
* System actions integration

---

### User configuration

Configuration is stored per-user:

```bash
~/.config/essorawm/
```

Generated files:

```bash
~/.config/essorawm/pymenu.json
~/.config/essorawm/essora-menu.xml
```

Advantages:

* No sudo required
* Per-user configuration
* Multiple user support
* Easy backup
* Independent desktop customization

---

### Built-in menu generator

Essora PyMenu includes its own integrated menu generation system.

The menu generator automatically reads:

```bash
/etc/xdg/menus/essora-applications.menu
```

and generates:

```bash
~/.config/essorawm/essora-menu.xml
```

Features:

* Automatic application detection
* XDG category parsing
* Dynamic icon detection
* Flatpak support
* Custom categories
* User generated menus
* Automatic updates

---

### Essora integration

Essora PyMenu was adapted to work with:

* Essora Desktop
* EssoraFM
* Essora Store
* Essora System tools
* Essora profile manager
* Essora themes
* Essora menu generation system

---

### Visual customization

Configurable:

* Window dimensions
* Header visibility
* Profile image shape
* Category icon size
* Search position
* Colors
* Fonts
* Favorites
* Transparency
* GTK theme usage

---

## Directory layout

```text
/usr/local/pymenu/
├── Pymenu.py
├── pymenu-config.py
├── pymenupuplang.py
├── ProfileManager.py
├── essora-menu-gen.py
├── locale/
├── defaults/
└── icon-pymenu/

/home/user/.config/essorawm/
├── pymenu.json
└── essora-menu.xml
```

---

## Credits

Essora PyMenu is based on PyMenuPup.

Original project:
https://github.com/Woofshahenzup/PyMenuPup

Adapted for Essora Linux by:

josejp2424

Changes include:

* Essora Desktop integration
* User configuration system
* Removed sudo dependency
* Essora visual adaptation
* Integrated menu generator
* Dynamic menu generation
* Improved desktop integration

---

## License

This project keeps the original upstream license and credits while adding modifications for the Essora ecosystem.
