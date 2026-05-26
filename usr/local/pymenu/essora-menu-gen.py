#!/usr/bin/env python3
"""
essora-menu-gen.py — Generador de menú para Pymenu
Usa el menú XDG real (/etc/xdg/menus/essora-applications.menu)
para generar categorías como lo hace lxpanel, sin mostrar el root
"Applications /" en las etiquetas finales.

Editado para Essora por: josejp2424
"""

import os
import sys
import shlex
from xml.sax.saxutils import escape as xe

try:
    from xdg.Menu import parse, Menu, MenuEntry, Separator
except Exception:
    print("✗ Falta python3-xdg. Instalalo con: sudo apt install python3-xdg", file=sys.stderr)
    sys.exit(1)

MENU_FILE = "/etc/xdg/menus/essora-applications.menu"
CONFIG_DIR = os.path.expanduser("~/.config/essorawm")
OUTPUT_SYSTEM = os.path.join(CONFIG_DIR, "essora-menu.xml")

ICON_PATHS = [
    "/usr/local/pymenu/icon-pymenu",
    "/usr/share/icons/Tela",
    "/usr/share/icons/Tela-black",
    "/usr/share/icons/TokyoNight-SE",
    "/usr/share/icons/Adwaita",
    "/usr/share/pixmaps/essora",
    "/usr/share/pixmaps",
    "/usr/share/icons/hicolor/48x48/apps",
    "/usr/share/icons/hicolor/32x32/apps",
    "/usr/share/icons/hicolor/64x64/apps",
]

APP_DIRS = [
    "/usr/share/applications",
    "/usr/local/share/applications",
    os.path.expanduser("~/.local/share/applications"),
]

FLATPAK_APP_DIRS = [
    "/var/lib/flatpak/exports/share/applications",
    os.path.expanduser("~/.local/share/flatpak/exports/share/applications"),
]

APPIMAGE_ICON = "/usr/share/pixmaps/app_appimage.png"
FLATPAK_ICON = "/usr/share/pixmaps/app_flatpak.png"


def ensure_user_writable_path(path):
    """Ensure a user-owned/writable path under ~/.config can be written without sudo.
    If an old sudo-created file/dir blocks writing, move it aside as .root-backup.*.
    """
    import time
    path = os.path.expanduser(path)
    parent = os.path.dirname(path) or "."
    parent = os.path.expanduser(parent)

    def backup(p):
        if not os.path.exists(p):
            return
        stamp = time.strftime("%Y%m%d-%H%M%S")
        newp = f"{p}.root-backup.{stamp}"
        try:
            os.rename(p, newp)
            print(f"Old non-writable path moved to: {newp}")
        except Exception as e:
            raise PermissionError(f"No se puede escribir ni mover {p}: {e}")


    if os.path.exists(parent) and not os.access(parent, os.W_OK | os.X_OK):
        backup(parent)

    os.makedirs(parent, exist_ok=True)


    if os.path.exists(path) and not os.access(path, os.W_OK):
        backup(path)

    return path



def clean_exec(exec_line: str) -> str:
    if not exec_line:
        return ""
    try:
        parts = shlex.split(exec_line)
    except Exception:
        parts = exec_line.split()

    cleaned = []
    for p in parts:
        if p.startswith("%") and len(p) <= 2:
            continue
        cleaned.append(p)
    return " ".join(cleaned).strip()


def get_menu_label(menu_obj) -> str:
    try:
        if menu_obj.Directory and menu_obj.Directory.DesktopEntry:
            name = menu_obj.Directory.DesktopEntry.getName()
            if name:
                return name.strip()
    except Exception:
        pass

    try:
        name = menu_obj.getName()
        if name:
            return name.strip()
    except Exception:
        pass

    return "Sin nombre"


def get_menu_icon(menu_obj) -> str:
    try:
        if menu_obj.Directory and menu_obj.Directory.DesktopEntry:
            icon = menu_obj.Directory.DesktopEntry.getIcon()
            if icon:
                return icon.strip()
    except Exception:
        pass
    return "applications-other"


def entry_to_app(menu_entry):
    try:
        de = menu_entry.DesktopEntry
    except Exception:
        return None

    try:
        no_display = bool(de.getNoDisplay())
    except Exception:
        no_display = False
    if no_display:
        return None

    try:
        app_type = de.getType()
    except Exception:
        app_type = "Application"
    if app_type != "Application":
        return None

    try:
        name = (de.getName() or "").strip()
    except Exception:
        name = ""

    try:
        comment = (de.getComment() or name).strip()
    except Exception:
        comment = name

    try:
        icon = (de.getIcon() or "application-x-executable").strip()
    except Exception:
        icon = "application-x-executable"

    try:
        exec_cmd = clean_exec(de.getExec() or "")
    except Exception:
        exec_cmd = ""

    if not name or not exec_cmd:
        return None

    return {
        "Name": name,
        "Comment": comment,
        "Icon": icon,
        "Exec": exec_cmd,
    }


def walk_menu(menu_obj, parent_path="", debug=False):
    label = get_menu_label(menu_obj)
    icon = get_menu_icon(menu_obj)
    full_label = f"{parent_path} / {label}" if parent_path else label

    apps = []
    submenus = []
    seen_exec = set()

    for entry in getattr(menu_obj, "Entries", []):
        if isinstance(entry, Menu):
            child = walk_menu(entry, full_label, debug=debug)
            if child["apps"] or child["submenus"]:
                submenus.append(child)

        elif isinstance(entry, MenuEntry):
            app = entry_to_app(entry)
            if not app:
                continue

            key = (app["Name"].lower(), app["Exec"])
            if key in seen_exec:
                continue
            seen_exec.add(key)
            apps.append(app)

        elif isinstance(entry, Separator):
            continue

    apps.sort(key=lambda a: a["Name"].lower())

    if debug:
        print(f"  [debug] {full_label:30s} — apps={len(apps)} submenus={len(submenus)}")

    return {
        "label": label,
        "full_label": full_label,
        "icon": icon,
        "apps": apps,
        "submenus": submenus,
    }


def flatten_nodes(nodes):
    out = []

    def rec(node):
        if node["apps"]:
            out.append({
                "loc_name": node["full_label"],
                "icon": node["icon"],
                "apps": node["apps"],
            })
        for child in node["submenus"]:
            rec(child)

    for n in nodes:
        rec(n)

    return out


def read_basic_desktop(path):
    data = {
        "Name": None,
        "Exec": None,
        "Icon": None,
        "Comment": "",
        "Categories": [],
        "NoDisplay": False,
        "Type": "Application",
    }

    try:
        in_entry = False
        with open(path, encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line == "[Desktop Entry]":
                    in_entry = True
                    continue
                if line.startswith("[") and line != "[Desktop Entry]":
                    in_entry = False
                    continue
                if not in_entry or not line or line.startswith("#") or "=" not in line:
                    continue

                k, _, v = line.partition("=")
                k = k.strip()
                v = v.strip()

                if k == "Name" and not data["Name"]:
                    data["Name"] = v
                elif k == "Exec" and not data["Exec"]:
                    data["Exec"] = clean_exec(v)
                elif k == "Icon" and data["Icon"] is None:
                    data["Icon"] = v or "application-x-executable"
                elif k == "Comment" and not data["Comment"]:
                    data["Comment"] = v
                elif k == "Categories":
                    data["Categories"] = [c.strip() for c in v.split(";") if c.strip()]
                elif k == "NoDisplay":
                    data["NoDisplay"] = v.lower() == "true"
                elif k == "Type":
                    data["Type"] = v
    except Exception:
        return None

    if data["NoDisplay"] or data["Type"] != "Application" or not data["Name"] or not data["Exec"]:
        return None
    if not data["Comment"]:
        data["Comment"] = data["Name"]
    if not data["Icon"]:
        data["Icon"] = "application-x-executable"
    return data


def append_special_categories(categories, debug=False):
    existing = {c["loc_name"].lower() for c in categories}
    special = {
        "AppImage": {"icon": APPIMAGE_ICON, "apps": []},
        "Wine": {"icon": "preferences-wine-essora", "apps": []},
        "Flatpak": {"icon": FLATPAK_ICON, "apps": []},
    }

    seen_special_apps = {
        "AppImage": set(),
        "Wine": set(),
        "Flatpak": set(),
    }

    seen_files = set()
    for d in APP_DIRS:
        if not os.path.isdir(d):
            continue
        try:
            names = sorted(os.listdir(d))
        except Exception:
            continue

        for fname in names:
            if not fname.endswith(".desktop") or fname in seen_files:
                continue
            seen_files.add(fname)
            path = os.path.join(d, fname)
            info = read_basic_desktop(path)
            if not info:
                continue

            cats = info.get("Categories", [])
            exec_cmd = (info.get("Exec") or "").lower()

            app = {
                "Name": info["Name"],
                "Exec": info["Exec"],
                "Icon": info["Icon"],
                "Comment": info["Comment"],
            }
            app_key = (app["Name"].lower(), app["Exec"])

            if "AppImage" in cats or ".appimage" in exec_cmd:
                if app_key not in seen_special_apps["AppImage"]:
                    seen_special_apps["AppImage"].add(app_key)
                    app["Icon"] = APPIMAGE_ICON
                    special["AppImage"]["apps"].append(app)
            elif "Wine" in cats or "wine" in cats or "wine" in exec_cmd:
                if app_key not in seen_special_apps["Wine"]:
                    seen_special_apps["Wine"].add(app_key)
                    special["Wine"]["apps"].append(app)

    seen_flatpak_files = set()
    for d in FLATPAK_APP_DIRS:
        if not os.path.isdir(d):
            continue
        try:
            names = sorted(os.listdir(d))
        except Exception:
            continue

        for fname in names:
            if not fname.endswith(".desktop") or fname in seen_flatpak_files:
                continue
            seen_flatpak_files.add(fname)
            path = os.path.join(d, fname)
            info = read_basic_desktop(path)
            if not info:
                continue

            app = {
                "Name": info["Name"],
                "Exec": info["Exec"],
                "Icon": FLATPAK_ICON,
                "Comment": info["Comment"],
            }
            app_key = (app["Name"].lower(), app["Exec"])
            if app_key in seen_special_apps["Flatpak"]:
                continue
            seen_special_apps["Flatpak"].add(app_key)
            special["Flatpak"]["apps"].append(app)

    for name, info in special.items():
        if not info["apps"]:
            continue
        if name.lower() in existing:
            continue
        info["apps"].sort(key=lambda a: a["Name"].lower())
        categories.append({
            "loc_name": name,
            "icon": info["icon"],
            "apps": info["apps"],
        })
        if debug:
            print(f"  [debug] categoría especial añadida: {name} ({len(info['apps'])} apps)")

    return categories


def build_menu(debug=False):
    if not os.path.exists(MENU_FILE):
        print(f"✗ No existe: {MENU_FILE}", file=sys.stderr)
        sys.exit(1)

    try:
        root_menu = parse(MENU_FILE)
    except Exception as e:
        print(f"✗ Error al parsear {MENU_FILE}: {e}", file=sys.stderr)
        sys.exit(1)


    top_nodes = []
    for entry in getattr(root_menu, "Entries", []):
        if isinstance(entry, Menu):
            child = walk_menu(entry, "", debug=debug)
            if child["apps"] or child["submenus"]:
                top_nodes.append(child)

    categories = flatten_nodes(top_nodes)
    categories = append_special_categories(categories, debug=debug)
    categories = [c for c in categories if c.get("apps")]

    if debug:
        for c in categories:
            print(f"  [result] {c['loc_name']:30s} — {len(c['apps'])} apps")

    total = sum(len(c["apps"]) for c in categories)
    print(f"✓ {len(categories)} categories, {total} apps")
    return categories


def write_xml(categories, output_path):
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<!-- essora-menu.xml — Generado por essora-menu-gen.py -->',
        '<!-- Para regenerar: /usr/local/pymenu/essora-menu-gen.py -->',
        '',
        '<EssoraMenu>',
        '',
        '  <IconPaths>',
    ]

    for p in ICON_PATHS:
        lines.append(f'    <Path>{xe(p)}</Path>')

    lines += [
        '  </IconPaths>',
        '',
        '  <Tray height="30" valign="bottom" halign="center"/>',
        '',
    ]

    for cat in categories:
        lines.append(f'  <Category label="{xe(cat["loc_name"])}" icon="{xe(cat["icon"])}">')
        for app in cat["apps"]:
            lines.append(
                f'    <App label="{xe(app["Name"])}" '
                f'icon="{xe(app["Icon"])}" '
                f'exec="{xe(app["Exec"])}" '
                f'comment="{xe(app["Comment"])}"/>'
            )
        lines.append('  </Category>')
        lines.append('')

    lines += ['</EssoraMenu>', '']

    try:
        ensure_user_writable_path(output_path)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        os.chmod(output_path, 0o644)
        print(f"✓ Written: {output_path}")
        return True
    except PermissionError:
        print(f"✗ Permission denied: {output_path}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"✗ {output_path}: {e}", file=sys.stderr)
        return False


def main():
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    debug = "--debug" in args

    print("=" * 55)
    print("essora-menu-gen — Generador de menú para Pymenu")
    print("=" * 55)

    categories = build_menu(debug=debug)
    if not categories:
        print("✗ No se encontraron aplicaciones.", file=sys.stderr)
        sys.exit(1)

    if dry_run:
        print("\n[dry-run] No se escribieron archivos.")
        for c in categories:
            print(f"  {c['loc_name']:30s} — {len(c['apps'])} apps")
        return

    ok = write_xml(categories, OUTPUT_SYSTEM)
    if not ok:
        sys.exit(1)

    print("=" * 55)
    print("Done. Restart Pymenu to see the updated menu.")
    print("=" * 55)


if __name__ == "__main__":
    main()
