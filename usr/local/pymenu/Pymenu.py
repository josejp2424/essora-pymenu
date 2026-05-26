#!/usr/bin/env python3
# =============================================================================
# Pymenu
# Editado por: josejp2424
#
# Nota de edición:
# - Adaptado para leer essora-menu.xml
# - Desvinculado del uso directo de jwmrc para el menú principal
# - Ajustes de categorías, iconos y recarga del menú XML
#
# Si prefieres otra firma, también puede leerse como: "Agregado por josejp2424".
# =============================================================================
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, Gio, GLib
import xml.etree.ElementTree as ET
import os
import subprocess
import sys
import shlex
import json
import urllib.parse
import locale
import cairo

# === 🌍 Sistema de Traducción ===
try:
    sys.path.insert(0, '/usr/local/pymenu')
    from pymenupuplang import TranslationManager
except ModuleNotFoundError:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "pymenupuplang", 
        "/usr/local/pymenu/pymenupuplang.py"
    )
    if spec and spec.loader:
        pymenupuplang = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pymenupuplang)
        TranslationManager = pymenupuplang.TranslationManager
    else:
        print("ERROR: No se pudo cargar pymenupuplang.py")
        sys.exit(1)

TR = TranslationManager()
CATEGORY_MAP = TR.get_category_map()

# Import the pango module using GObject Introspection
gi.require_version('Pango', '1.0')
from gi.repository import Pango

# ============================================================================
# SISTEMA DE MAPEO DE CATEGORÍAS
# Editado por: josejp2424
# Motivo: El jwmrc usa nombres de categorías en el idioma configurado
#         (español, portugués, etc.) pero los iconos estaban hardcodeados
#         en inglés. Este sistema lee archivos .directory para mapear
#         correctamente iconos sin importar el idioma del jwmrc.
# ============================================================================

class DirectoryCategoryMapper:
    """
    Mapea nombres de categorías (en cualquier idioma) a sus iconos
    leyendo archivos .directory
    """
    
    def __init__(self):
        self.user_dir = os.path.expanduser('~/.local/share/desktop-directories')
        self.system_dir = '/usr/share/desktop-directories'
        self.category_map = {}
        self._load_all_directories()
    
    def _load_all_directories(self):
        """Carga todos los archivos .directory y crea los mapeos"""
        for base_dir in [self.user_dir, self.system_dir]:
            if not os.path.exists(base_dir):
                continue
            
            try:
                for filename in os.listdir(base_dir):
                    if not filename.endswith('.directory'):
                        continue
                    
                    filepath = os.path.join(base_dir, filename)
                    self._parse_directory_file(filepath)
            except Exception as e:
                pass  
    
    def _parse_directory_file(self, filepath):
        """Parsea un archivo .directory y extrae nombres e icono"""
        import re
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            icon = None
            names = []
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('Icon='):
                    icon = line.split('=', 1)[1].strip()
                elif line.startswith('Name=') and not line.startswith('Name['):
                    names.append(line.split('=', 1)[1].strip())
                elif line.startswith('Name['):
                    match = re.match(r'Name\[([^\]]+)\]=(.+)', line)
                    if match:
                        names.append(match.group(2).strip())
            

            if icon and names:
                for name in names:
                    self.category_map[name.lower()] = icon
                    self.category_map[name] = icon
        
        except Exception:
            pass  
    
    def get_icon_for_category(self, category_name, default='applications-other'):
        """
        Obtiene el icono para una categoría, sin importar el idioma
        """
        # Buscar con mayúsculas/minúsculas exactas
        if category_name in self.category_map:
            return self.category_map[category_name]
        
        # Buscar case-insensitive
        if category_name.lower() in self.category_map:
            return self.category_map[category_name.lower()]
        
        # Fallback: iconos hardcodeados
        fallback_icons = {
            'desktop': 'preferences-desktop',
            'escritorio': 'preferences-desktop',
            'system': 'applications-system',
            'sistema': 'applications-system',
            'utilities': 'applications-utilities',
            'utilidades': 'applications-utilities',
            'file': 'system-file-manager',
            'archivo': 'system-file-manager',
            'filesystem': 'folder',
            'graphics': 'applications-graphics',
            'gráficos': 'applications-graphics',
            'office': 'applications-office',
            'oficina': 'applications-office',
            'network': 'applications-internet',
            'internet': 'applications-internet',
            'red': 'applications-internet',
            'multimedia': 'applications-multimedia',
            'games': 'applications-games',
            'juegos': 'applications-games',
            'development': 'applications-development',
            'desarrollo': 'applications-development',
            'education': 'applications-science',
            'educación': 'applications-science',
            'help': 'help-browser',
            'ayuda': 'help-browser',
            'leave': 'system-shutdown',
            'salir': 'system-shutdown',
            'favorites': 'star',
            'favoritos': 'star',
            'flatpak': 'app_flatpak',
            'appimage': 'app_appimage',
            'wine': 'preferences-wine-essora',  # Editado por: josejp2424
        }
        
        return fallback_icons.get(category_name.lower(), default)

# --- Privilege handling ---
sudo_targets = {
    "logout_gui",
}
def _wrap_for_user(cmd_parts):
    """Ensure commands run as the invoking user (audio, browser) unless in sudo_targets."""
    import os, shlex, subprocess
    if not cmd_parts:
        return cmd_parts
    exe = cmd_parts[0]
    
    if exe in sudo_targets:
        return ["sudo"] + cmd_parts
    
    if os.geteuid() == 0 and os.environ.get("SUDO_USER"):
        return ["sudo", "-E", "-u", os.environ["SUDO_USER"]] + cmd_parts
    return cmd_parts

def open_directory(path):
    """
    Intenta expandir la ruta y abrirla con el administrador predeterminado del sistema.
    """
    expanded_path = os.path.expanduser(path)
    
    if not os.path.exists(expanded_path):
        try:
            os.makedirs(expanded_path, exist_ok=True)
            print(f"{TR['Folder created:']} {expanded_path}")
        except Exception as e:
            print(f"Error al crear la carpeta {expanded_path}: {e}")
            return 
    
    try:
        # Esto le pide al sistema que abrir la ruta con la APP PREDETERMINADA
        gio_file = Gio.File.new_for_path(expanded_path)
        Gio.AppInfo.launch_default_for_uri(gio_file.get_uri(), None)
    except Exception as e:
        # Si falla Gio, intentamos con xdg-open como respaldo
        try:
            subprocess.Popen(["xdg-open", expanded_path],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
        except Exception as ex:
            print(f"Error al abrir el directorio: {ex}")

gi.require_version('Pango', '1.0')
from gi.repository import Pango


HOME_DIR = os.path.expanduser("~")
CONFIG_DIR = os.path.expanduser("~/.config/essorawm")
PROFILE_PIC = os.path.join(CONFIG_DIR, "face")
PROFILE_MANAGER = "/usr/local/pymenu/ProfileManager.py"
SHUTDOWN_CMD = "/usr/local/bin/logout_gui"
CONFIG_FILE = os.path.join(CONFIG_DIR, "pymenu.json")
ESSORA_MENU_FILE = os.path.join(CONFIG_DIR, "essora-menu.xml")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG_FILE = os.path.join(SCRIPT_DIR, "defaults", "pymenu.json")


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

    # If the config directory exists but is not writable, move the whole dir aside.
    if os.path.exists(parent) and not os.access(parent, os.W_OK | os.X_OK):
        backup(parent)

    os.makedirs(parent, exist_ok=True)

    # If the target file exists but is not writable, move just that file aside.
    if os.path.exists(path) and not os.access(path, os.W_OK):
        backup(path)

    return path



class ConfigManager:
    """Manages reading and writing the application's JSON configuration."""
    def __init__(self, config_file=CONFIG_FILE):
        self.config_file = config_file
        self.config = self.load_config()

    def get_default_config(self):
        """Return the default configuration matching the current script's aesthetics."""
        return {
            "window": {
                "width": 547,
                "height": 567,
                "decorated_window": False,
                "hide_header": False,
                "hide_profile_pic": False,
                "halign": "center",
                "icon_size": 32,
                "profile_pic_size": 64,
                "hide_category_text": False,
                "category_icon_size": 16,
                "profile_pic_shape": "square",
                "header_layout": "left",
                "hide_os_name": False,
                "hide_kernel": False,
                "hide_hostname": False,
                "hide_places": False,           
                "hide_favorites": False,       
                "profile_in_places": False,
                "search_bar_position": "bottom",
                "search_bar_container": "window"    
            },
            "font": {
                "family": "Terminess Nerd Font Propo Bold 16",
                "size_categories": 14000,
                "size_names": 12000,
                "size_header": 12000
            },
            "colors": {
                "background_opacity": 0.7,
                "background": "rgba(0, 0, 0, 0.7)",
                "border": "rgba(255, 255, 255, 0.1)",
                "text_normal": "#D8DEE9",
                "text_header_os": "#D8DEE9",
                "text_header_kernel": "#D0883A",
                "text_header_hostname": "#88C0D0",
                "hover_background": "rgba(255, 255, 255, 0.1)",
                "selected_background": "rgba(255, 255, 255, 0.2)",
                "selected_text": "#ECEFF4",
                "button_normal_background": "rgba(0,0,0,0.6)",
                "button_text": "#ECEFF4",
                "categories_background": "rgba(0,0,0,0.4)"
            },
            "paths": {
                "profile_pic": PROFILE_PIC,
                "profile_manager": "/usr/local/pymenu/ProfileManager.py",
                "shutdown_cmd": "/usr/local/bin/logout_gui",
                "jwmrc_tray": "/usr/share/jwm/jwm/jwmrc-tray",          
                "tint2rc": "/usr/share/tint2/tint2/tint2rc"  
            },
                "tray": {
                "use_tint2": False
            },
            "categories": {
                "excluded": []
            },
        "favorites": []           
        }


    def load_default_config_from_file(self):
        """Load /usr/local/pymenu/defaults/pymenu.json if available, otherwise use internal defaults."""
        if os.path.exists(DEFAULT_CONFIG_FILE):
            try:
                with open(DEFAULT_CONFIG_FILE, 'r') as f:
                    default_config = json.load(f)
                # Ensure old package paths are not copied to the user's config.
                if isinstance(default_config.get("paths"), dict):
                    default_config["paths"]["profile_pic"] = os.path.join(CONFIG_DIR, "face")
                    default_config["paths"]["profile_manager"] = "/usr/local/pymenu/ProfileManager.py"
                return default_config
            except (IOError, json.JSONDecodeError) as e:
                print(f"Error loading default config file: {e}. Using internal defaults.")
        return self.get_default_config()

    def load_config(self):
        """Load configuration from the JSON file or create a default one."""
        if not os.path.exists(self.config_file):
            print(f"Config file not found. Creating user config at {self.config_file}")
            default_config = self.load_default_config_from_file()
            self.save_config(default_config)
            return default_config
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                # Merge with default config to ensure all keys exist
                default_config = self.get_default_config()
                for key in default_config:
                    if key not in config:
                        config[key] = default_config[key]
                    elif isinstance(config[key], dict) and isinstance(default_config[key], dict):
                        for sub_key in default_config[key]:
                            if sub_key not in config[key]:
                                config[key][sub_key] = default_config[key][sub_key]
                return config
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading config file: {e}. Using default settings.")
            return self.get_default_config()
    
    def save_config(self, config_data):
        """Save configuration to the JSON file without sudo."""
        ensure_user_writable_path(self.config_file)
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f, indent=4)

def apply_circular_mask(pixbuf):
    """Aplica una máscara circular a un GdkPixbuf, mostrando la imagen dentro del círculo."""
    try:
        width = pixbuf.get_width()
        height = pixbuf.get_height()
        
        # Determinar el tamaño del cuadrado más pequeño
        size = min(width, height)
        
        # 1. Asegurar que el pixbuf tiene canal alfa
        if not pixbuf.get_has_alpha():
            pixbuf = pixbuf.add_alpha(True, 0, 0, 0)
        
        # 2. Escalar a un cuadrado perfecto si no lo es
        if width != height or width != size:
            pixbuf = pixbuf.scale_simple(size, size, GdkPixbuf.InterpType.BILINEAR)
            width = height = size
        
        # 3. Crear una superficie temporal para la máscara
        mask_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
        mask_cr = cairo.Context(mask_surface)
        
        # Llenar de negro transparente
        mask_cr.set_source_rgba(0, 0, 0, 0)
        mask_cr.paint()
        
        # Dibujar un círculo blanco opaco en la máscara
        center_x = size / 2.0
        center_y = size / 2.0
        radius = size / 2.0
        
        mask_cr.arc(center_x, center_y, radius, 0, 2 * 3.141592653589793)
        mask_cr.set_source_rgba(1, 1, 1, 1)
        mask_cr.fill()
        
        # 4. Convertir el pixbuf a una superficie Cairo
        original_surface = Gdk.cairo_surface_create_from_pixbuf(pixbuf, 0, None)
        
        # 5. Crear la superficie final
        final_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
        final_cr = cairo.Context(final_surface)
        
        # Dibujar la imagen original
        final_cr.set_source_surface(original_surface, 0, 0)
        final_cr.paint()
        
        # Aplicar la máscara usando el operador IN
        final_cr.set_source_surface(mask_surface, 0, 0)
        final_cr.set_operator(cairo.OPERATOR_DEST_IN)
        final_cr.paint()
        
        # 6. Convertir la superficie final a GdkPixbuf
        new_pixbuf = Gdk.pixbuf_get_from_surface(final_surface, 0, 0, size, size)
        
        if new_pixbuf:
            return new_pixbuf
        else:
            print("⚠️ Advertencia: No se pudo crear pixbuf circular, devolviendo original")
            return pixbuf
        
    except Exception as e:
        print(f"❌ Error aplicando máscara circular: {e}")
        import traceback
        traceback.print_exc()
        return pixbuf


class EssoraMenuParser:
    """
    Lee essora-menu.xml y construye las categorías/aplicaciones para Pymenu.
    No depende de JWM.

    Editado por: josejp2424
    Motivo: usar essora-menu.xml como fuente principal del menú.
    """
    DEFAULT_ICON_PATHS = [
        "/usr/share/icons/Tela",
        "/usr/local/pymenu/icon-pymenu",
        "/usr/share/icons/Tela-black",
        "/usr/share/icons/TokyoNight-SE",
        "/usr/share/icons/Adwaita",
        "/usr/share/pixmaps/essora",
        "/usr/share/pixmaps/essora/tint2",
        "/usr/local/lib/X11/pixmaps",
        "/usr/share/pixmaps",
        "/usr/share/icons/hicolor/48x48/apps",
        "/usr/share/icons/hicolor/32x32/apps",
        "/usr/share/icons/hicolor/64x64/apps",
        "/usr/share/pixmaps/puppy",
    ]

    def __init__(self, menu_file=None):
        self.menu_file = self.resolve_menu_file(menu_file)
        self.applications = {}
        self.icon_paths = list(self.DEFAULT_ICON_PATHS)
        self.tray_config = None

    def resolve_menu_file(self, menu_file=None):
        """
        Usa ~/.config/essorawm/essora-menu.xml como fuente principal del usuario.
        Editado por: josejp2424
        """
        if menu_file:
            candidate = os.path.expanduser(menu_file)
            if candidate and os.path.exists(candidate):
                return candidate

        return ESSORA_MENU_FILE

    def parse_tray_config(self):
        """
        Lee la posición del panel desde tint2 si está activado.
        Si no, la toma desde <Tray> dentro de essora-menu.xml.
        """
        tray_info = {
            'height': 30,
            'width': 1300,
            'valign': 'bottom',
            'halign': 'center',
            'layer': 'above',
            'autohide': 'off',
            'source': 'default'
        }

        config_manager = ConfigManager()
        config = config_manager.config
        use_tint2 = config.get('tray', {}).get('use_tint2', False)

        if use_tint2:
            tint2_config = config.get('paths', {}).get('tint2rc', os.path.expanduser("/usr/share/tint2/tint2/tint2rc"))
            tint2_config = os.path.expanduser(tint2_config)

            if os.path.exists(tint2_config):
                try:
                    with open(tint2_config, 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith('panel_size'):
                                parts = line.split('=')
                                if len(parts) == 2:
                                    size_parts = parts[1].strip().split()
                                    if len(size_parts) >= 2:
                                        try:
                                            tray_info['height'] = int(size_parts[1])
                                        except ValueError:
                                            pass
                            elif line.startswith('panel_position'):
                                parts = line.split('=')
                                if len(parts) == 2:
                                    pos_parts = parts[1].strip().split()
                                    if len(pos_parts) >= 2:
                                        valign = pos_parts[0].lower()
                                        if valign in ['top', 'bottom']:
                                            tray_info['valign'] = valign
                                        halign = pos_parts[1].lower()
                                        if halign in ['left', 'center', 'right']:
                                            tray_info['halign'] = halign
                    tray_info['source'] = 'tint2'
                    self.tray_config = tray_info
                    print(f"Tray config detected from tint2rc: {tray_info}")
                    return tray_info
                except Exception as e:
                    print(f"Error parsing tint2 config: {e}")

        if os.path.exists(self.menu_file):
            try:
                tree = ET.parse(self.menu_file)
                root = tree.getroot()
                tray_element = root.find('.//Tray')
                if tray_element is not None:
                    tray_info['height'] = int(tray_element.get('height', '30'))
                    tray_info['width'] = int(tray_element.get('width', '1300'))
                    tray_info['valign'] = tray_element.get('valign', 'bottom').lower()
                    tray_info['halign'] = tray_element.get('halign', 'center').lower()
                    tray_info['layer'] = tray_element.get('layer', 'above').lower()
                    tray_info['autohide'] = tray_element.get('autohide', 'off').lower()
                    tray_info['source'] = 'essora-menu.xml'
                    print(f"Tray config detected from {self.menu_file}: {tray_info}")
            except Exception as e:
                print(f"Error parsing tray config from {self.menu_file}: {e}")
        else:
            print(f"Menu XML not found: {self.menu_file}")

        self.tray_config = tray_info
        return tray_info

    def parse_menu(self):
        """
        Lee essora-menu.xml generado por essora-menu-gen.py.
        """
        try:
            if not os.path.exists(self.menu_file):
                print(f"Menu XML not found: {self.menu_file}")
                try:
                    subprocess.run(["/usr/local/pymenu/essora-menu-gen.py"],
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL,
                                   check=False)
                except Exception as e:
                    print(f"Error auto-generating essora-menu.xml: {e}")
                if not os.path.exists(self.menu_file):
                    return self.get_fallback_applications()

            tree = ET.parse(self.menu_file)
            root = tree.getroot()

            self.icon_paths = self.extract_icon_paths(root)

            applications = {}
            for category in root.findall('./Category'):
                label = (category.get('label') or '').strip()
                if not label:
                    continue

                apps = []
                for app in category.findall('./App'):
                    app_label = (app.get('label') or '').strip()
                    exec_cmd = (app.get('exec') or '').strip()
                    icon = (app.get('icon') or '').strip()
                    comment = (app.get('comment') or app_label).strip()

                    if not app_label or not exec_cmd:
                        continue

                    apps.append({
                        'Name': app_label,
                        'Exec': exec_cmd,
                        'Icon': icon,
                        'Comment': comment or app_label,
                        'Terminal': 'terminal' in exec_cmd.lower() or 'urxvt' in exec_cmd.lower(),
                        'Categories': [label],
                    })

                if apps:
                    applications[label] = apps

            return applications if applications else self.get_fallback_applications()

        except Exception as e:
            print(f"Error parsing essora-menu.xml: {e}")
            return self.get_fallback_applications()

    def extract_icon_paths(self, root):
        paths = []
        for path_el in root.findall('.//IconPaths/Path'):
            if path_el.text:
                p = path_el.text.strip()
                if p and p not in paths:
                    paths.append(p)

        for path in self.DEFAULT_ICON_PATHS:
            if path not in paths:
                paths.append(path)

        return paths

    def get_fallback_applications(self):
        return {
            'System': [
                {'Name': 'Terminal', 'Exec': 'lxterminal', 'Icon': 'terminal', 'Comment': 'Terminal emulator', 'Terminal': False, 'Categories': []},
                {'Name': 'File Manager', 'Exec': 'rox', 'Icon': 'folder', 'Comment': 'File manager', 'Terminal': False, 'Categories': []},
            ],
            'Internet': [
                {'Name': 'Firefox', 'Exec': 'firefox', 'Icon': 'firefox', 'Comment': 'Web browser', 'Terminal': False, 'Categories': []},
            ]
        }

class ArcMenuLauncher(Gtk.Window):

    def __init__(self, icon_size=None, menu_file=None, x=None, y=None):
        super().__init__(title="Pymenu")
        
        self.config_manager = ConfigManager()
        self.config = self.config_manager.config
        self.is_resizing = False 
        # Use icon_size from config, or fallback to default
        self.icon_size = self.config['window'].get('icon_size', 32)
        
        # ========== INICIALIZAR MAPEADOR DE CATEGORÍAS ==========
        # Editado por: josejp2424
        self.category_mapper = DirectoryCategoryMapper()
        
        # Editado por: josejp2424
        # Pymenu toma el contenido directamente desde essora-menu.xml
        self.parser = EssoraMenuParser(menu_file)
        
        self.tray_config = self.parser.parse_tray_config()
        self.applications = self.parser.parse_menu()
        self.apps_flowbox = None
        self.categories_listbox = None
        self.search_entry = None
        self.profile_image = None
    
        self.icon_cache = {}
        self.current_category = "All"
        self.hover_timeout = None
        self.restore_timeout = None
        self.mouse_in_menu = False
    
        self.selected_category = None
        self.hovered_category = None
        self.selected_category_row = None
        
        self.pos_x = x
        self.pos_y = y
        
        self.context_menu_active = False   
        
        screen = Gdk.Screen.get_default()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.set_visual(visual)
            self.set_app_paintable(True)
        
        self.apply_css()
        self.setup_window()
        self.create_interface()
        
        self.menu_file_path = self.parser.menu_file
        if self.menu_file_path and os.path.exists(self.menu_file_path):
            self.menu_file = Gio.File.new_for_path(self.menu_file_path)
            self.file_monitor = self.menu_file.monitor_file(Gio.FileMonitorFlags.NONE, None)
            self.file_monitor.connect("changed", self.on_menu_file_changed)
            print(f"Now monitoring Essora menu XML for changes: {self.menu_file_path}")
        else:
            self.menu_file = None
            self.file_monitor = None
            print(f"Essora menu XML not found for monitoring: {self.menu_file_path}")

    def apply_css(self):
        """Loads and applies CSS from the configuration."""
        # Verificar si debe usar tema GTK
        use_gtk_theme = self.config['colors'].get('use_gtk_theme', False)
        
        if use_gtk_theme:
            # Si usa tema GTK, usar un fondo sólido compatible
            css = """
            GtkWindow, GtkEventBox {
                background-color: @theme_bg_color;
                border-radius: 0px;
                box-shadow: none;
                border: none;
            }
            .menu-window {
                background-color: @theme_bg_color;
                border-radius: 14px;
                box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.3);
                border: 1px solid @theme_unfocused_fg_color;
                padding: 5px 10px 10px 10px;
            }
            """
            print("Using GTK theme colors")
        else:
            # CSS personalizado original
            colors = self.config['colors']
            
            css = f"""
            GtkWindow, GtkEventBox {{
                background-color: {colors['background']};
                border-radius: 0px;
                box-shadow: none;
                border: none;
            }}
            .tooltip, tooltip, GtkTooltip {{
                background-color: {colors['background']};
                color: {colors['text_normal']};
                border-radius: 8px;
                padding: 10px 10px;
                border: 1px solid {colors['border']};
                box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.2);
            }}   
            .menu-window {{
                background-color: {colors['background']};
                border-radius: 2px;
                box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.3);
                border: 1px solid {colors['border']};
                padding: 5px 10px 10px 10px;
            }}
        
            listbox {{
                padding: 2px;
            }}
            
            listbox row {{
                background-color: {self.config['colors'].get('categories_background', 'rgba(0,0,0,0.4)')};
                color: {self.config['colors']['text_normal']};
                border-radius: 6px;
                padding: 2px;
                margin: 1px;
                min-height: 26px;
            }}
        
            listbox row:selected {{
                background-color: {colors['selected_background']};
                color: {colors['selected_text']};
            }}
        
            listbox row:hover {{
                background-color: {colors['hover_background']};
            }}
        
            button {{
                border-radius: 8px;
                padding: 2px 2px;
                background-color: {colors['button_normal_background']};
                color: {colors['button_text']};
                border: none;
            }}
            .action-button {{
                border-radius: 6px;
                background-color: {colors['button_normal_background']};
                color: {colors['text_normal']};
                border: 1px solid {colors['button_normal_background']};
            }}
            .action-button:hover {{
                background-color: {colors['hover_background']};
            }}
            
            listbox row.selected-category {{
                background-color: {colors['selected_background']};
                color: {colors['selected_text']};
            }}
        
            button:hover {{
                background-color: {colors['hover_background']};
            }}       
            .search-box:focus {{
            background-color: {colors['button_normal_background']};
            color: {colors['text_normal']};
            border: 1px solid {colors['border']} ;
            border-radius: 8px;
            }}
            .app-box {{
                min-width: {self.icon_size + 0}px;
            }}
            .category-list {{
                 background-color: {colors['categories_background']};
                 padding: 1px;
                 border-radius: 12px;
            }}
            menuitem {{
                background-color: {colors['background']};
                color: {colors['text_normal']};
                border-radius: 8px;
                padding: 10px 10px;
                border: 1px solid {colors['border']};
                box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.2);
            }}
            
            menuitem:hover {{
                background-color: {colors['hover_background']};
                color: {colors['text_normal']};
            }}
            
            menuitem:selected {{
                background-color: {colors['hover_background']};
                color: {colors['text_normal']};
            }}
            button.profile-circular-style {{
                border-radius: 50%;
                padding: 0; 
                border: none;
                min-width: 64px; 
                min-height: 64px;
            }}
            
            button.profile-circular-style:hover {{
                background-color: rgba(255, 255, 255, 0.1);
                box-shadow: none;
            }}            
            """
            print("Using custom colors")
        
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(css.encode('utf-8'))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def on_menu_file_changed(self, monitor, file, other_file, event_type):
        """Reload the menu when essora-menu.xml is modified"""
        if event_type == Gio.FileMonitorEvent.CHANGES_DONE_HINT:
            print("Essora menu XML changed, reloading menu...")
            self.applications = self.parser.parse_menu()
            for child in self.get_children():
                self.remove(child)
            self.create_interface()
            self.show_all()
            self.present()

    def get_hostname(self):
        """Get the system hostname from /etc/hostname"""
        try:
            with open("/etc/hostname", "r") as f:
                hostname = f.read().strip()
                if hostname:
                    return hostname
        except Exception as e:
            print(f"Error reading hostname: {e}")
        return "Unknown Host"

    def get_os_info(self):
        """Get OS name and kernel version"""
        try:
            os_name = "Unknown OS"
            for path in ['/etc/os-release', '/usr/lib/os-release']:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        for line in f:
                            if line.startswith('PRETTY_NAME='):
                                os_name = line.split('=', 1)[1].strip().strip('"')
                                break
                    break
            else:
                result = subprocess.run(['uname', '-sr'], capture_output=True, text=True)
                if result.returncode == 0:
                    os_name = result.stdout.strip()
            
            result = subprocess.run(['uname', '-r'], capture_output=True, text=True)
            kernel = result.stdout.strip() if result.returncode == 0 else "Unknown"
            
            return os_name, kernel
            
        except Exception as e:
            print(f"Error getting OS info: {e}")
            return "Unknown OS", "Unknown"
                
    def on_size_changed(self, widget, event):
            """Salva el nuevo tamaño de la ventana al archivo de configuración."""
            width, height = self.get_size()
            
            # Activa la bandera de redimensionamiento
            self.is_resizing = True
            
            # Desactiva la bandera después de un breve retraso
            GLib.timeout_add(150, self.reset_resizing_flag)
            
            # Verifica si el tamaño ha cambiado para evitar escrituras innecesarias
            if width != self.config['window']['width'] or height != self.config['window']['height']:
                print(f"Tamaño de ventana cambiado a {width}x{height}. Guardando...")
                self.config['window']['width'] = width
                self.config['window']['height'] = height
                self.config_manager.save_config(self.config)
                
    def reset_resizing_flag(self):
        """Reinicia la bandera de redimensionamiento."""
        self.is_resizing = False
        return False # No repetir el temporizador           
                
    def calculate_menu_position(self):
        """Calculate menu position based on config and screen size"""
        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor()
        geometry = monitor.get_geometry()
    
        screen_width = geometry.width
        screen_height = geometry.height
    
        menu_width = int(self.config['window'].get('width', 300))
        menu_height = int(self.config['window'].get('height', 200))
    
        # ---------- HORIZONTAL ----------
        menu_halign = self.config['window'].get('halign', 'center')
        if menu_halign == 'left':
            x = 10
        elif menu_halign == 'right':
            x = screen_width - menu_width - 10
        else:  # default = center
            x = (screen_width - menu_width) // 2
    
        # ---------- VERTICAL ----------
        tray_height = int(self.tray_config.get('height', 0))
        tray_valign = self.tray_config.get('valign', 'center')
    
        if tray_valign == 'top':
            y = tray_height
        elif tray_valign == 'bottom':
            y = screen_height - tray_height - menu_height
        else:
            y = (screen_height - menu_height) // 2
    
        # Clamp para evitar que quede fuera de pantalla
        x = max(0, min(x, screen_width - menu_width))
        y = max(0, min(y, screen_height - menu_height))
    
        return int(x), int(y)

    def setup_window(self):
        """Configure main window"""
        win_size = self.config['window']
        self.set_default_size(win_size['width'], win_size['height'])
        
        if self.pos_x is not None and self.pos_y is not None:
            self.move(int(self.pos_x), int(self.pos_y))
        else:
            x, y = self.calculate_menu_position()
            self.move(x, y)
   #         print(f"Positioning menu at ({x}, {y}) based on tray config: {self.tray_config}")
    
        self.set_resizable(True)
        self.set_decorated(self.config['window'].get('decorated_window', False))
        self.set_app_paintable(True)
        self.set_type_hint(Gdk.WindowTypeHint.DIALOG)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.connect("key-press-event", self.on_key_press)
        self.connect("focus-out-event", self.on_focus_out)
        self.connect("button-press-event", self.on_button_press)
        self.connect("configure-event", self.on_size_changed)
        self.show_all()
        self.present()
        self.grab_focus()
        self.set_keep_above(True)
        GLib.timeout_add(500, lambda: self.set_keep_above(False))
    
        try:
            self.set_icon_name("applications-system")
        except:
            pass      
            
    def on_button_press(self, widget, event):
        """Allows window to be dragged if ALT key is pressed and closes on right-click"""
        # Close the window on right-click (button 3)
        if event.button == 2:
            Gtk.main_quit()
            return True
        
        # Allows window to be dragged if ALT key is pressed
        if event.button == 1 and (event.state & Gdk.ModifierType.MOD1_MASK):
            self.begin_move_drag(event.button, int(event.x_root), int(event.y_root), event.time)
            return True
            
        return False
            
        return False
 
    def on_key_press(self, widget, event):
        """Close window with Escape key"""
        if event.keyval == Gdk.KEY_Escape:
            Gtk.main_quit()
            return True
        return False
    
    def on_focus_out(self, widget, event):
            """Cierra la ventana cuando pierde el foco, a menos que se esté redimensionando."""
            if not self.is_resizing and not self.context_menu_active:
                Gtk.main_quit()
            return False                    

    def create_interface(self):
        """Create the main interface"""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        main_box.get_style_context().add_class('menu-window')
        self.add(main_box)
        top_spacer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        top_spacer.set_size_request(-1, 2)
        main_box.pack_start(top_spacer, False, False, 0)
    
        if not self.config['window'].get('hide_header', False):
            header_box = self.create_header()
            main_box.pack_start(header_box, False, False, 0)
            main_box.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 0)
    
        content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        main_box.pack_start(content_box, True, True, 0)
    
        # Columna 1: Places
        places_sidebar = self.create_places_sidebar()
        content_box.pack_start(places_sidebar, False, False, 0)
        content_box.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL), False, False, 0)
        
        # Columna 2: Categorías
        content_box.pack_start(self.create_categories_sidebar(), False, False, 0)
        content_box.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL), False, False, 0)
        
        # Columna 3: Aplicaciones
        apps_area = self.create_applications_area()
        content_box.pack_start(apps_area, True, True, 0)
        
        # === NUEVA LÓGICA: Verificar CONTENEDOR de la barra de búsqueda ===
        search_container = self.config['window'].get('search_bar_container', 'window')
        
        if search_container == 'apps_column':
            # La barra ya está integrada en create_applications_area()
            pass
        else:
            # Comportamiento original: barra en la ventana principal
            search_position = self.config['window'].get('search_bar_position', 'bottom')
            search_and_buttons_box = self.create_search_and_buttons_box()
            
            if search_position == 'top':
                main_box_children = main_box.get_children()
                insert_position = 0
                
                for i, child in enumerate(main_box_children):
                    if child == content_box:
                        insert_position = i
                        break
                
                main_box.pack_start(search_and_buttons_box, False, False, 0)
                main_box.reorder_child(main_box.get_children()[-1], insert_position)
                
                separator_top = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
                main_box.pack_start(separator_top, False, False, 0)
                main_box.reorder_child(main_box.get_children()[-1], insert_position + 1)
            else:
                main_box.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 0)
                main_box.pack_end(search_and_buttons_box, False, False, 0)
        
        self.show_all()
        GLib.timeout_add(100, self.delayed_focus_grab)
        
    def create_search_and_buttons_box(self):
        """Crea la caja con barra de búsqueda y botones de acción"""
        bottom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        bottom_box.set_margin_top(4)
        bottom_box.set_margin_bottom(4)
        bottom_box.set_margin_start(4)
        bottom_box.set_margin_end(4)
    
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.get_style_context().add_class('search-box')
        self.search_entry.set_placeholder_text(TR['Search applications...'])
        self.search_entry.connect("search-changed", self.on_search_changed)
        self.search_entry.set_size_request(200, 10)
        self.search_entry.set_can_focus(True)
        self.search_entry.set_tooltip_text(TR['Search applications...'])
        bottom_box.pack_start(self.search_entry, True, True, 0)
        
        # ---- Botón de fixmenus (inmediatamente después de la barra de búsqueda) ----
        fixmenus_button = Gtk.Button()
        fixmenus_button.get_style_context().add_class('action-button')
        fixmenus_button.set_size_request(30, 5)
        
        icon_path = "/usr/local/pymenu/icon-pymenu/menu-update.png"
        if os.path.exists(icon_path):
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(icon_path, 20, 20)
            fixmenus_icon = Gtk.Image.new_from_pixbuf(pixbuf)
        else:
            fixmenus_icon = Gtk.Image.new_from_icon_name("view-refresh", Gtk.IconSize.SMALL_TOOLBAR)
        
        fixmenus_button.add(fixmenus_icon)
        fixmenus_button.set_tooltip_text(TR['Menu update'])
        fixmenus_button.connect("clicked", self.on_fixmenus_clicked)
        bottom_box.pack_start(fixmenus_button, False, False, 0)
        
        # ---- Botón de apagado ----
        shutdown_button = Gtk.Button()
        shutdown_button.get_style_context().add_class('action-button') 
        shutdown_button.set_size_request(30, 5)
        icon_path = self.find_icon_path("preferences-desktop-essora")
        if icon_path:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(icon_path, 20, 20)
            shutdown_icon = Gtk.Image.new_from_pixbuf(pixbuf)
        else:
            shutdown_icon = Gtk.Image.new_from_icon_name("preferences-desktop-essora", Gtk.IconSize.SMALL_TOOLBAR)        
        shutdown_button.add(shutdown_icon)
        shutdown_button.set_tooltip_text(TR['Shutdown'])
        shutdown_button.connect("clicked", self.on_shutdown_clicked)
        bottom_box.pack_end(shutdown_button, False, False, 0)
        
        # ---- Botón de navegador ----
        browser_button = Gtk.Button()
        browser_button.get_style_context().add_class('action-button') 
        browser_button.set_size_request(30, 5)
        icon_path = self.find_icon_path("preferences-system-search-essora")
        if icon_path:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(icon_path, 20, 20)
            browser_icon = Gtk.Image.new_from_pixbuf(pixbuf)
        else:
            browser_icon = Gtk.Image.new_from_icon_name("preferences-system-search-essora", Gtk.IconSize.SMALL_TOOLBAR)       
        browser_button.add(browser_icon)
        browser_button.set_tooltip_text(TR['Search in the web'])
        browser_button.connect("clicked", self.on_browser_search_clicked)
        bottom_box.pack_end(browser_button, False, False, 0)
        
        # ---- Botón de configuración ----
        config_button = Gtk.Button()
        config_button.get_style_context().add_class('action-button')
        config_button.set_size_request(30, 5)
        icon_path = self.find_icon_path("preferences-system-essora")
        if icon_path:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(icon_path, 20, 20)
            config_icon = Gtk.Image.new_from_pixbuf(pixbuf)
        else:
            config_icon = Gtk.Image.new_from_icon_name("preferences-system-essora", Gtk.IconSize.SMALL_TOOLBAR)
        
        config_button.add(config_icon)
        config_button.set_tooltip_text(TR['Pymenu config'])
        config_button.connect("clicked", self.on_config_clicked)
        bottom_box.pack_end(config_button, False, False, 0)
        
        return bottom_box  
        
    def on_fixmenus_clicked(self, button):
        """Regenera essora-menu.xml del sistema"""
        try:
            subprocess.Popen(
                ["/usr/local/pymenu/essora-menu-gen.py", "--debug"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as e:
            print(f"Error al actualizar essora-menu.xml: {e}")            
        
    def delayed_focus_grab(self):
        """Grab focus on search entry after a small delay to preserve placeholder visibility"""
        if self.search_entry:
            self.search_entry.grab_focus()
        return False  # Don't repeat the timeout        

    def create_header(self):
        """Create the top header with profile picture, OS, kernel, and hostname"""
        # Si el perfil está en Places, solo mostrar info del sistema
        if self.config['window'].get('profile_in_places', False):
            return self.create_system_info_only()
        
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        header_box.set_margin_top(1)
        header_box.set_margin_bottom(1)
        header_box.set_margin_start(5)
        header_box.set_margin_end(5)
        hide_profile = self.config['window'].get('hide_profile_pic', False)
    
        # === CREAR EL PERFIL ===
        profile_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        profile_box.set_valign(Gtk.Align.CENTER)
        
        profile_button = Gtk.Button()
        profile_button.set_relief(Gtk.ReliefStyle.NONE)
        profile_button.get_style_context().add_class('profile-button') 
        
        if self.config['window'].get('profile_pic_shape', 'square') == 'circular':
            profile_button.get_style_context().add_class('profile-circular-style')
        
        self.profile_image = Gtk.Image()
        profile_button.add(self.profile_image)
        self.profile_image.set_halign(Gtk.Align.CENTER)
        self.profile_image.set_valign(Gtk.Align.CENTER)
        
        def load_profile_image():
            profile_pic_path = self.config['paths']['profile_pic']
            profile_pic_size = self.config['window'].get('profile_pic_size', 128)
            profile_pic_shape = self.config['window'].get('profile_pic_shape', 'square')
            
            pixbuf = None
    
            # 1. Intentar cargar el .face del usuario
            if profile_pic_path and os.path.exists(profile_pic_path):
                try:
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                        profile_pic_path, profile_pic_size, profile_pic_size, True
                    )
                except Exception as e:
                    print(f"Error cargando .face: {e}")
    
            # 2. Si no hay .face, buscar el genérico en el sistema
            if pixbuf is None:
                icon_names = ["user-info", "avatar-default", "user-available", "system-users"]
                theme = Gtk.IconTheme.get_default()
                
                for name in icon_names:
                    if theme.has_icon(name):
                        try:
                            pixbuf = theme.load_icon(name, profile_pic_size, Gtk.IconLookupFlags.FORCE_SIZE)
                            break
                        except:
                            continue
    
            # 3. Aplicar forma y mostrar
            if pixbuf:
                if profile_pic_shape == 'circular':
                    pixbuf = apply_circular_mask(pixbuf)
                self.profile_image.set_from_pixbuf(pixbuf)
            else:
                self.profile_image.set_from_icon_name("image-missing", Gtk.IconSize.DIALOG)
        
        load_profile_image()
    
        def on_profile_clicked(button):
            profile_manager_path = self.config['paths'].get('profile_manager', "")
            if profile_manager_path:
                try:
                    GLib.timeout_add(100, lambda: Gtk.main_quit())
                    if os.access(profile_manager_path, os.X_OK):
                        subprocess.Popen([profile_manager_path])
                    else:
                        subprocess.Popen(["python3", profile_manager_path])
                except Exception as e:
                    print(f"Error: {e}")
            else:
                print("Profile Manager no configurado por el usuario.")
        
        profile_button.set_tooltip_text(TR["Select avatar"])
        profile_button.connect("clicked", on_profile_clicked)
        profile_box.pack_start(profile_button, False, False, 0)
        
        # === CREAR LA INFO DEL SISTEMA ===
        system_info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        system_info_box.set_valign(Gtk.Align.CENTER)
        
        os_name, kernel = self.get_os_info()
        hostname = self.get_hostname()
        
        header_font_string = self.config['font']['family']
        header_font_description = Pango.FontDescription.from_string(header_font_string)
        header_font_description.set_size(self.config['font']['size_header'])
        
        use_gtk_theme = self.config['colors'].get('use_gtk_theme', False)
        text_align = self.config['window'].get('header_text_align', 'left')
        
        # Convertir a constante de GTK
        if text_align == 'center':
            gtk_align = Gtk.Align.CENTER
        elif text_align == 'right':
            gtk_align = Gtk.Align.END
        else:  # left
            gtk_align = Gtk.Align.START
        
        # OS Label - solo mostrar si no está oculto
        if not self.config['window'].get('hide_os_name', False):
            os_label = Gtk.Label()
            if use_gtk_theme:
                os_label.set_markup(f'<b>{os_name}</b>')
            else:
                os_label.set_markup(f'<span color="{self.config["colors"]["text_header_os"]}"><b>{os_name}</b></span>')
            os_label.override_font(header_font_description)
            os_label.set_halign(gtk_align)
            os_label.set_ellipsize(3)
            os_label.set_max_width_chars(30)
            system_info_box.pack_start(os_label, False, False, 0)
        
        # Kernel Label - solo mostrar si no está oculto
        if not self.config['window'].get('hide_kernel', False):
            kernel_label = Gtk.Label()
            if use_gtk_theme:
                kernel_label.set_markup(f' {kernel}')
            else:
                kernel_label.set_markup(f'<span color="{self.config["colors"]["text_header_kernel"]}"> {kernel}</span>')
            kernel_label.override_font(header_font_description)
            kernel_label.set_halign(gtk_align)
            kernel_label.set_ellipsize(3)
            kernel_label.set_max_width_chars(30)
            system_info_box.pack_start(kernel_label, False, False, 0)
        
        # Hostname Label - solo mostrar si no está oculto Y si no está en Places
        if not self.config['window'].get('hide_hostname', False) and not self.config['window'].get('profile_in_places', False):
            hostname_label = Gtk.Label()
            if use_gtk_theme:
                hostname_label.set_markup(f' {hostname}')
            else:
                hostname_label.set_markup(f'<span color="{self.config["colors"]["text_header_hostname"]}"> {hostname}</span>')
            hostname_label.override_font(header_font_description)
            hostname_label.set_halign(gtk_align)
            hostname_label.set_ellipsize(3)
            hostname_label.set_max_width_chars(30)
            system_info_box.pack_start(hostname_label, False, False, 0)
        
        # === APLICAR EL LAYOUT SEGÚN CONFIGURACIÓN ===
        header_layout = self.config['window'].get('header_layout', 'left')
        
        if hide_profile:
            # Si el perfil está oculto, solo mostrar info del sistema
            header_box.pack_start(system_info_box, True, True, 0)
        elif header_layout == 'right':
            # Avatar a la derecha, info a la izquierda
            header_box.pack_start(system_info_box, True, True, 0)
            header_box.pack_start(profile_box, False, False, 0)
        elif header_layout == 'center':
            # Avatar centrado con info del sistema a ambos lados
            left_spacer = Gtk.Box()
            right_spacer = Gtk.Box()
            
            header_box.pack_start(left_spacer, True, True, 0)
            header_box.pack_start(profile_box, False, False, 0)
            header_box.pack_start(right_spacer, True, True, 0)
            
            system_info_box.set_halign(Gtk.Align.START)
            left_spacer.pack_start(system_info_box, False, False, 0)
        else:
            # Avatar a la izquierda, info a la derecha (layout original)
            header_box.pack_start(profile_box, False, False, 0)
            header_box.pack_start(system_info_box, True, True, 0)
        
        # Monitor de cambios en el archivo de perfil (solo si no está oculto)
        if not hide_profile:
            profile_pic_path = self.config['paths']['profile_pic']
            if profile_pic_path and os.path.exists(profile_pic_path):
                profile_file = Gio.File.new_for_path(profile_pic_path)
                monitor = profile_file.monitor_file(Gio.FileMonitorFlags.NONE, None)
                
                def on_file_changed(monitor, file, other_file, event_type):
                    if event_type in (Gio.FileMonitorEvent.CHANGED, Gio.FileMonitorEvent.CREATED):
                        GLib.idle_add(load_profile_image)
                
                monitor.connect("changed", on_file_changed)
        
        return header_box
        
    def create_system_info_only(self):
        """Create only system info without profile picture (for when profile is in Places)"""
        system_info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        system_info_box.set_valign(Gtk.Align.CENTER)
        
        os_name, kernel = self.get_os_info()
        hostname = self.get_hostname()
        
        header_font_string = self.config['font']['family']
        header_font_description = Pango.FontDescription.from_string(header_font_string)
        header_font_description.set_size(self.config['font']['size_header'])
        
        use_gtk_theme = self.config['colors'].get('use_gtk_theme', False)
        text_align = self.config['window'].get('header_text_align', 'left')
        
        # Convertir a constante de GTK
        if text_align == 'center':
            gtk_align = Gtk.Align.CENTER
        elif text_align == 'right':
            gtk_align = Gtk.Align.END
        else:  # left
            gtk_align = Gtk.Align.START
        
        # Contenedor principal
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        header_box.set_margin_top(1)
        header_box.set_margin_bottom(1)
        header_box.set_margin_start(5)
        header_box.set_margin_end(5)
        
        # OS Label
        if not self.config['window'].get('hide_os_name', False):
            os_label = Gtk.Label()
            if use_gtk_theme:
                os_label.set_markup(f'<b>{os_name}</b>')
            else:
                os_label.set_markup(f'<span color="{self.config["colors"]["text_header_os"]}"><b>{os_name}</b></span>')
            os_label.override_font(header_font_description)
            os_label.set_halign(gtk_align)
            os_label.set_ellipsize(3)
            os_label.set_max_width_chars(30)
            system_info_box.pack_start(os_label, False, False, 0)
        
        # Kernel Label
        if not self.config['window'].get('hide_kernel', False):
            kernel_label = Gtk.Label()
            if use_gtk_theme:
                kernel_label.set_markup(f' {kernel}')
            else:
                kernel_label.set_markup(f'<span color="{self.config["colors"]["text_header_kernel"]}"> {kernel}</span>')
            kernel_label.override_font(header_font_description)
            kernel_label.set_halign(gtk_align)
            kernel_label.set_ellipsize(3)
            kernel_label.set_max_width_chars(30)
            system_info_box.pack_start(kernel_label, False, False, 0)
        
        # Hostname Label - NO mostrar en header cuando profile_in_places=True
        # El hostname ya aparecerá en la columna de Places
        
        header_box.pack_start(system_info_box, True, True, 0)
        
        return header_box 

    def create_places_sidebar(self):
        """Crear columna de lugares completa: Perfil -> Hostname -> System Places -> Favoritos"""
        places_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        places_box.set_halign(Gtk.Align.CENTER)
        places_box.set_margin_top(1)
        places_box.set_margin_bottom(5)
        places_box.set_margin_start(5)
        places_box.set_margin_end(5)
        
        # 1. SECCIÓN DE PERFIL Y HOSTNAME - SOLO SI profile_in_places está ACTIVADO
        if self.config['window'].get('profile_in_places', False):
            profile_section = self.create_profile_section()
            places_box.pack_start(profile_section, False, False, 5)
            places_box.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 5)
        
        # 2. LUGARES DEL SISTEMA (Home, Downloads, etc.)
        system_places = [
            ('user-home', TR.get('Home', 'Home'), '~'),
            ('folder-download', TR.get('DownloadsDir', 'Downloads'), f"~/{TR.get('DownloadsDir', 'Downloads')}"),
            ('folder-music', TR.get('MusicDir', 'Music'), f"~/{TR.get('MusicDir', 'Music')}"),
            ('folder-documents', TR.get('DocumentsDir', 'Documents'), f"~/{TR.get('DocumentsDir', 'Documents')}"),
            ('folder-pictures', TR.get('PicturesDir', 'Pictures'), f"~/{TR.get('PicturesDir', 'Pictures')}"),
            ('folder-videos', TR.get('VideosDir', 'Videos'), f"~/{TR.get('VideosDir', 'Videos')}"),
        ]
        
        # Verificar si debemos mostrar los lugares del sistema
        hide_places = self.config['window'].get('hide_places', False)
        
        if not hide_places:
            # Fuente para los textos
            font_desc = Pango.FontDescription(self.config['font']['family'])
            font_desc.set_size(self.config['font'].get('size_categories', 12000))
            
            for icon_name, label, path in system_places:
                btn = Gtk.Button()
                btn.set_relief(Gtk.ReliefStyle.NONE)
                btn.get_style_context().add_class('social-button')
                btn.set_size_request(40, -1)
                
                hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                hbox.set_halign(Gtk.Align.START)
                hbox.set_margin_start(5)
                
                # Icono de sistema (24px)
                icon_image = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.DND)
                icon_image.set_pixel_size(24)
                
                # Texto
                text_label = Gtk.Label(label=label)
                text_label.set_halign(Gtk.Align.START)
                text_label.override_font(font_desc)
                
                hbox.pack_start(icon_image, False, False, 0)
                hbox.pack_start(text_label, True, True, 0)
                
                btn.add(hbox)
                btn.connect("clicked", lambda b, p=path: open_directory(p))
                places_box.pack_start(btn, False, False, 0)
        
        # 3. SEPARADOR Y FAVORITOS (solo si places no está oculto)
        hide_favorites = self.config['window'].get('hide_favorites', False)
        
        if not hide_places and not hide_favorites:
            places_box.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 5)
            
            # ===== AGREGAR FAVORITOS =====
            favorites = self.config.get('favorites', [])
            if favorites:
                # Título de favoritos
                fav_title_label = Gtk.Label(label="🌱 " + TR.get('Favorites', 'Favorites'))
                fav_title_label.set_halign(Gtk.Align.START)
                fav_title_label.set_margin_start(5)
                fav_title_label.override_font(font_desc)
                places_box.pack_start(fav_title_label, False, False, 2)
                
                # Agregar cada favorito
                for fav in favorites:
                    fav_name = fav.get('name', 'Unnamed')
                    fav_exec = fav.get('exec', '')
                    fav_icon = fav.get('icon', 'application-x-executable')
                    
                    # Crear botón para el favorito
                    fav_btn = Gtk.Button()
                    fav_btn.set_relief(Gtk.ReliefStyle.NONE)
                    fav_btn.get_style_context().add_class('social-button')
                    fav_btn.set_size_request(40, -1)
                    
                    hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                    hbox.set_halign(Gtk.Align.START)
                    hbox.set_margin_start(5)
                    
                    # Icono del favorito
                    try:
                        icon_path = self.find_icon_path(fav_icon)
                        if icon_path:
                            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(icon_path, 20, 20)
                            icon_image = Gtk.Image.new_from_pixbuf(pixbuf)
                        else:
                            icon_image = Gtk.Image.new_from_icon_name(fav_icon, Gtk.IconSize.DND)
                    except:
                        icon_image = Gtk.Image.new_from_icon_name("application-x-executable", Gtk.IconSize.DND)
                    
                    icon_image.set_pixel_size(20)
                    
                    # Texto del favorito
                    text_label = Gtk.Label(label=fav_name)
                    text_label.set_halign(Gtk.Align.START)
                    text_label.override_font(font_desc)
                    
                    hbox.pack_start(icon_image, False, False, 0)
                    hbox.pack_start(text_label, True, True, 0)
                    
                    fav_btn.add(hbox)
                    
                    # FUNCIÓN CORREGIDA para ejecutar favoritos
                    def launch_favorite(btn, cmd=fav_exec, name=fav_name):
                        try:
                            GLib.timeout_add(50, lambda: Gtk.main_quit())
                            
                            # Manejo especial para gtk-launch
                            cmd_clean = cmd.strip()
                            
                            if cmd_clean.startswith('gtk-launch'):
                                # Extraer nombre de la aplicación
                                parts = cmd_clean.split()
                                if len(parts) >= 2:
                                    app_name = parts[1]
                                    # Buscar archivo .desktop
                                    desktop_paths = [
                                        "/usr/share/applications/",
                                        "/usr/local/share/applications/",
                                        os.path.expanduser("~/.local/share/applications/")
                                    ]
                                    
                                    for path in desktop_paths:
                                        desktop_file = os.path.join(path, app_name + '.desktop')
                                        if os.path.exists(desktop_file):
                                            # Usar xdg-open
                                            subprocess.Popen(["xdg-open", desktop_file])
                                            return
                            
                            # Comando normal
                            import shlex
                            try:
                                cmd_parts = shlex.split(cmd_clean)
                            except:
                                cmd_parts = cmd_clean.split()
                            
                            subprocess.Popen(cmd_parts,
                                             stdout=subprocess.DEVNULL,
                                             stderr=subprocess.DEVNULL)
                        except Exception as e:
                            print(f"Error launching favorite {name}: {e}")
                    
                    fav_btn.connect("clicked", launch_favorite)
                    places_box.pack_start(fav_btn, False, False, 0)
            else:
                # Mostrar mensaje si no hay favoritos
                no_fav_label = Gtk.Label(label=TR.get('No favorites added', 'No favorites added'))
                no_fav_label.set_halign(Gtk.Align.CENTER)
                no_fav_label.set_margin_start(5)
                no_fav_label.override_font(font_desc)
                places_box.pack_start(no_fav_label, False, False, 2)
        
        # Si todo está oculto (places y favorites), mostrar mensaje
        elif hide_places:
            empty_label = Gtk.Label(label=TR.get('Places sidebar is hidden', 'Places sidebar is hidden'))
            empty_label.set_halign(Gtk.Align.CENTER)
            places_box.pack_start(empty_label, True, True, 0)
        
        # Scroll automático
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.add(places_box)
        
        return scrolled
        
    def create_profile_section(self):
        """Crear sección de perfil compacta para la columna de Places"""
        profile_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        profile_box.set_halign(Gtk.Align.CENTER)
        
        # Botón de perfil
        profile_button = Gtk.Button()
        profile_button.set_relief(Gtk.ReliefStyle.NONE)
        profile_button.get_style_context().add_class('profile-button')
        
        if self.config['window'].get('profile_pic_shape', 'square') == 'circular':
            profile_button.get_style_context().add_class('profile-circular-style')
        
        self.profile_image = Gtk.Image()
        profile_button.add(self.profile_image)
        self.profile_image.set_halign(Gtk.Align.CENTER)
        self.profile_image.set_valign(Gtk.Align.CENTER)
        
        def load_profile_image():
            profile_pic_path = self.config['paths']['profile_pic']
            profile_pic_size = self.config['window'].get('profile_pic_size', 64)
            profile_pic_shape = self.config['window'].get('profile_pic_shape', 'square')
            
            pixbuf = None
    
            if profile_pic_path and os.path.exists(profile_pic_path):
                try:
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                        profile_pic_path, profile_pic_size, profile_pic_size, True
                    )
                except Exception as e:
                    print(f"Error cargando .face: {e}")
    
            if pixbuf is None:
                icon_names = ["user-info", "avatar-default", "user-available", "system-users"]
                theme = Gtk.IconTheme.get_default()
                
                for name in icon_names:
                    if theme.has_icon(name):
                        try:
                            pixbuf = theme.load_icon(name, profile_pic_size, Gtk.IconLookupFlags.FORCE_SIZE)
                            break
                        except:
                            continue
    
            if pixbuf:
                if profile_pic_shape == 'circular':
                    pixbuf = apply_circular_mask(pixbuf)
                self.profile_image.set_from_pixbuf(pixbuf)
            else:
                self.profile_image.set_from_icon_name("image-missing", Gtk.IconSize.DIALOG)
        
        load_profile_image()
    
        def on_profile_clicked(button):
            profile_manager_path = self.config['paths'].get('profile_manager', "")
            if profile_manager_path:
                try:
                    GLib.timeout_add(100, lambda: Gtk.main_quit())
                    if os.access(profile_manager_path, os.X_OK):
                        subprocess.Popen([profile_manager_path])
                    else:
                        subprocess.Popen(["python3", profile_manager_path])
                except Exception as e:
                    print(f"Error: {e}")
            else:
                print("Profile Manager no configurado por el usuario.")
        
        profile_button.set_tooltip_text(TR["Select avatar"])
        profile_button.connect("clicked", on_profile_clicked)
        profile_box.pack_start(profile_button, False, False, 0)
        
        # === SOLO MOSTRAR HOSTNAME SI NO ESTÁ OCULTO ===
        if not self.config['window'].get('hide_hostname', False):
            hostname = self.get_hostname()
            username_label = Gtk.Label(label=hostname)
            username_label.set_halign(Gtk.Align.CENTER)
            
            font_description = Pango.FontDescription(self.config['font']['family'])
            font_description.set_size(self.config['font']['size_header'])
            username_label.override_font(font_description)
            
            use_gtk_theme = self.config['colors'].get('use_gtk_theme', False)
            if not use_gtk_theme:
                username_label.set_markup(f'<span color="{self.config["colors"]["text_header_os"]}"><b>{hostname}</b></span>')
            else:
                username_label.set_markup(f'<b>{hostname}</b>')
            
            profile_box.pack_start(username_label, False, False, 0)
        
        # Monitor de cambios en el archivo de perfil
        profile_pic_path = self.config['paths']['profile_pic']
        if profile_pic_path and os.path.exists(profile_pic_path):
            profile_file = Gio.File.new_for_path(profile_pic_path)
            monitor = profile_file.monitor_file(Gio.FileMonitorFlags.NONE, None)
            
            def on_file_changed(monitor, file, other_file, event_type):
                if event_type in (Gio.FileMonitorEvent.CHANGED, Gio.FileMonitorEvent.CREATED):
                    GLib.idle_add(load_profile_image)
            
            monitor.connect("changed", on_file_changed)
        
        return profile_box            
    
        def on_profile_clicked(button):
            try:
                GLib.timeout_add(100, lambda: Gtk.main_quit())
                profile_manager_path = self.config['paths']['profile_manager']
                if os.path.exists(profile_manager_path):
                    subprocess.Popen([profile_manager_path],
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL)
                else:
                    subprocess.Popen(["python3", profile_manager_path], 
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL)
                print(f"Launching Profile Manager: {profile_manager_path}")
            except Exception as e:
                print(f"Error opening Profile Manager: {e}")
        
        profile_button.set_tooltip_text(TR["Select avatar"])
        profile_button.connect("clicked", on_profile_clicked)
        profile_box.pack_start(profile_button, False, False, 0)
        
        # === CREAR LA INFO DEL SISTEMA ===
        system_info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        system_info_box.set_valign(Gtk.Align.CENTER)
        
        os_name, kernel = self.get_os_info()
        hostname = self.get_hostname()
        
        header_font_string = self.config['font']['family']
        header_font_description = Pango.FontDescription.from_string(header_font_string)
        
        use_gtk_theme = self.config['colors'].get('use_gtk_theme', False)
        
        # OS Label - solo mostrar si no está oculto
        if not self.config['window'].get('hide_os_name', False):
            os_label = Gtk.Label()
            if use_gtk_theme:
                os_label.set_markup(f'<b>{os_name}</b>')
            else:
                os_label.set_markup(f'<span color="{self.config["colors"]["text_header_os"]}"><b>{os_name}</b></span>')
            os_label.override_font(header_font_description)
            os_label.set_halign(Gtk.Align.START)
            os_label.set_ellipsize(3)
            os_label.set_max_width_chars(30)
            system_info_box.pack_start(os_label, False, False, 0)
        
        # Kernel Label - solo mostrar si no está oculto
        if not self.config['window'].get('hide_kernel', False):
            kernel_label = Gtk.Label()
            if use_gtk_theme:
                kernel_label.set_markup(f'🐧 {kernel}')
            else:
                kernel_label.set_markup(f'<span color="{self.config["colors"]["text_header_kernel"]}">🐧 {kernel}</span>')
            kernel_label.override_font(header_font_description)
            kernel_label.set_halign(Gtk.Align.START)
            kernel_label.set_ellipsize(3)
            kernel_label.set_max_width_chars(30)
            system_info_box.pack_start(kernel_label, False, False, 0)
        
        # Hostname Label - solo mostrar si no está oculto
        if not self.config['window'].get('hide_hostname', False):
            hostname_label = Gtk.Label()
            if use_gtk_theme:
                hostname_label.set_markup(f'💻 {hostname}')
            else:
                hostname_label.set_markup(f'<span color="{self.config["colors"]["text_header_hostname"]}">💻 {hostname}</span>')
            hostname_label.override_font(header_font_description)
            hostname_label.set_halign(Gtk.Align.START)
            hostname_label.set_ellipsize(3)
            hostname_label.set_max_width_chars(30)
            system_info_box.pack_start(hostname_label, False, False, 0)
        
        # === APLICAR EL LAYOUT SEGÚN CONFIGURACIÓN ===
        header_layout = self.config['window'].get('header_layout', 'left')
        
        if hide_profile:
            # Si el perfil está oculto, solo mostrar info del sistema
            header_box.pack_start(system_info_box, True, True, 0)
        elif header_layout == 'right':
            # Avatar a la derecha, info a la izquierda
            header_box.pack_start(system_info_box, True, True, 0)
            header_box.pack_start(profile_box, False, False, 0)
        elif header_layout == 'center':
            # Avatar centrado con info del sistema a ambos lados
            left_spacer = Gtk.Box()
            right_spacer = Gtk.Box()
            
            header_box.pack_start(left_spacer, True, True, 0)
            header_box.pack_start(profile_box, False, False, 0)
            header_box.pack_start(right_spacer, True, True, 0)
            
            system_info_box.set_halign(Gtk.Align.START)
            left_spacer.pack_start(system_info_box, False, False, 0)
        else:
            # Avatar a la izquierda, info a la derecha (layout original)
            header_box.pack_start(profile_box, False, False, 0)
            header_box.pack_start(system_info_box, True, True, 0)
        
        # Monitor de cambios en el archivo de perfil
        profile_file = Gio.File.new_for_path(self.config['paths']['profile_pic'])
        monitor = profile_file.monitor_file(Gio.FileMonitorFlags.NONE, None)
        
        def on_file_changed(monitor, file, other_file, event_type):
            if event_type in (Gio.FileMonitorEvent.CHANGED, Gio.FileMonitorEvent.CREATED):
                GLib.idle_add(load_profile_image)
        
        monitor.connect("changed", on_file_changed)
        
        return header_box

    def create_categories_sidebar(self):
        """Create categories sidebar with improved hover functionality"""
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        # La línea de abajo no es necesaria para la lista, pero si la quieres
        # para el contenedor ScrolledWindow, déjala aquí.
        scrolled.set_size_request(15, -1)
        
        # Aquí creas el ListBox una sola vez.
        self.categories_listbox = Gtk.ListBox()
        
        # Aquí aplicas todas las configuraciones a ese ListBox.
        self.categories_listbox.set_size_request(12, -1) # Puedes ajustar este valor ancho de columna
        self.categories_listbox.get_style_context().add_class('category-list')
        self.categories_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.categories_listbox.connect("row-activated", self.on_category_clicked)
    
        # ========== ORDEN FIJO DE CATEGORÍAS ==========
        # Editado por: josejp2424
        # Orden: Favoritos, Desktop, Sistema, Utilidades, Archivo, Gráficos, 
        #        Oficina, Internet, Multimedia, Juegos, Wine, Flatpak, AppImage
        preferred_order = [
            'Favoritos', 'Favorites',  # Español / Inglés
            'Desktop', 'Escritorio',    # Inglés / Español
            'Sistema', 'System',        # Español / Inglés
            'Utilidades', 'Utilities',  # Español / Inglés
            'Archivo', 'File', 'Filesystem',  # Español / Inglés / Alternativo
            'Gráficos', 'Graphics', 'Graphic',  # Español / Inglés
            'Oficina', 'Office',        # Español / Inglés
            'Internet', 'Network',      # Neutral / Inglés
            'Multimedia',               # Universal
            'Juegos', 'Games',          # Español / Inglés
            'Wine',                     # Nombre propio - Editado por: josejp2424
            'Flatpak',                  # Nombre propio
            'AppImage',                 # Nombre propio
        ]
        
        # Obtener categorías excluidas desde la configuración
        excluded_categories = self.config.get('categories', {}).get('excluded', [])
        
        added_categories = set()
        for category in preferred_order:
            if category in self.applications and self.applications[category] and category not in excluded_categories:
                # Usar mapper para obtener el icono
                icon = self.category_mapper.get_icon_for_category(category)
                self.add_category_row(category, icon)
                added_categories.add(category)
        
        for category in sorted(self.applications.keys()):
            if category not in added_categories and self.applications[category] and category not in excluded_categories:
                # Usar mapper para obtener el icono
                icon = self.category_mapper.get_icon_for_category(category)
                self.add_category_row(category, icon)
    
        scrolled.add(self.categories_listbox)
    
        first_row = self.categories_listbox.get_row_at_index(0)
        if first_row:
            self.categories_listbox.select_row(first_row)
            category = self.get_row_category(first_row)
            self.selected_category = category
            self.current_category = category
            first_row.get_style_context().add_class("selected-category")
            self.selected_category_row = first_row
            self.show_category_applications(category)
    
        return scrolled
    
    def add_category_row(self, category, icon_name):
        """Add a category row with hover events"""
        row = Gtk.ListBoxRow()
        event_box = Gtk.EventBox()
        event_box.set_above_child(True)
        
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        box.set_property("margin-left", 2)
        box.set_property("margin-right", 1)
        box.set_property("margin-top", 2)
        box.set_property("margin-bottom", 2)
        
        icon_path = self.find_icon_path(icon_name)
        if icon_path:
            category_icon_size = self.config['window'].get('category_icon_size', 24)
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(icon_path, category_icon_size, category_icon_size)
            icon = Gtk.Image.new_from_pixbuf(pixbuf)
        else:
            icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.MENU)
        
        # --- LÓGICA DE VISIBILIDAD DE ICONO Y TEXTO ---
        if self.config['window'].get('hide_category_text', False):
            # Crear un contenedor específico para centrar el icono
            center_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            center_box.set_homogeneous(False)
            
            # Tres secciones: vacía - icono - vacía
            left_spacer = Gtk.Box()
            right_spacer = Gtk.Box()
            
            center_box.pack_start(left_spacer, True, True, 0)
            center_box.pack_start(icon, False, False, 0)
            center_box.pack_start(right_spacer, True, True, 0)
            
            box.pack_start(center_box, True, True, 0)
            row.set_tooltip_text(TR[category] if category in TR.translations else category)
        else:
            # Si el texto es visible, usar el diseño normal sin center_box
            box.pack_start(icon, False, False, 0)
            
            label = Gtk.Label()
            font_description = Pango.FontDescription(self.config['font']['family'])
            font_description.set_size(self.config['font']['size_categories'])
            label.override_font(font_description)
            translated_category = TR[category] if category in TR.translations else category
            use_gtk_theme = self.config['colors'].get('use_gtk_theme', False)
            if use_gtk_theme:
                label.set_markup(f"{translated_category}")
            else:
                label.set_markup(f"<span foreground='{self.config['colors']['text_normal']}'>{translated_category}</span>")
            label.set_halign(Gtk.Align.START)
            box.pack_start(label, True, True, 5)
        
        event_box.add(box)
        row.add(event_box)
        row.category_name = category
        
        event_box.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
        event_box.connect("enter-notify-event", lambda w, e: self.on_category_hover_enter(row, e))
        event_box.connect("leave-notify-event", lambda w, e: self.on_category_hover_leave(row, e))
        
        self.categories_listbox.add(row)
        row.show_all()
    
    def get_row_category(self, row):
        """Get category name from row"""
        return getattr(row, "category_name", None)


    def on_category_hover_enter(self, row, event):
        """Handle mouse entering a category row"""
        category = self.get_row_category(row)
        if not category or category == self.current_category:
            return False
            
        if self.hover_timeout:
            GLib.source_remove(self.hover_timeout)
        if self.restore_timeout:
            GLib.source_remove(self.restore_timeout)
            self.restore_timeout = None
        
        self.hover_timeout = GLib.timeout_add(150, self._activate_hover_preview, category)
        self.hovered_category = category
        
        return False
        
    def on_category_hover_leave(self, row, event):
        """Handle mouse leaving a category row"""
        if self.hover_timeout:
            GLib.source_remove(self.hover_timeout)
            self.hover_timeout = None
            
        self.hovered_category = None
        return False

    def on_category_clicked(self, listbox, row):
        """Handle category selection by click or Enter key."""
        if not row:
            return
        
        category = self.get_row_category(row)
        if category:
            if self.hover_timeout:
                GLib.source_remove(self.hover_timeout)
                self.hover_timeout = None
        
            if self.selected_category_row:
                self.selected_category_row.get_style_context().remove_class("selected-category")
        
            row.get_style_context().add_class("selected-category")
        
            self.selected_category_row = row
            self.selected_category = category
            self.current_category = category
            
            self.show_category_applications(category)
        
    def restore_to_selected_category(self):
        """Revert to the permanently selected category"""
        self.restore_timeout = None
        if not self.mouse_in_menu:
            self.current_category = self.selected_category
            self.show_category_applications(self.selected_category)
        return False
        
    def _activate_hover_preview(self, category):
        """Activate the category preview on hover"""
        self.hover_timeout = None
        self.current_category = category
        self.show_category_applications(category)
        return False
    
    def _restore_selected_category(self):
        """Restore the selected category if no active hover"""
        if (not self.hover_timeout and 
            self.selected_category and 
            self.selected_category != self.current_category):
            
            self.hovered_category = None
            self.current_category = self.selected_category
            self.show_category_applications(self.selected_category)
        
        self.restore_timeout = None
        return False

    def create_applications_area(self):
        """Create applications display area with optional integrated search bar"""
        # Contenedor principal vertical para apps + búsqueda opcional
        main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Verificar si la búsqueda debe estar en esta columna
        search_container = self.config['window'].get('search_bar_container', 'window')
        search_position = self.config['window'].get('search_bar_position', 'bottom')
        
        # Si la búsqueda va arriba Y en esta columna, agregarla primero
        if search_container == 'apps_column' and search_position == 'top':
            search_and_buttons_box = self.create_search_and_buttons_box()
            main_container.pack_start(search_and_buttons_box, False, False, 0)
            main_container.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 0)
        
        # Área de aplicaciones con scroll
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        self.apps_flowbox = Gtk.FlowBox()
        self.apps_flowbox.set_valign(Gtk.Align.START)
        self.apps_flowbox.set_max_children_per_line(30)
        self.apps_flowbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.apps_flowbox.set_property("margin-left", 5)
        self.apps_flowbox.set_property("margin-right", 5)
        self.apps_flowbox.set_property("margin-top", 10)
        self.apps_flowbox.set_property("margin-bottom", 10)
        
        apps_eventbox = Gtk.EventBox()
        apps_eventbox.add(self.apps_flowbox)
        apps_eventbox.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK)
        apps_eventbox.connect("enter-notify-event", self.on_apps_area_enter)
        
        self.apps_flowbox.connect("key-press-event", self.on_apps_key_press)
        
        scrolled.add(apps_eventbox)
        main_container.pack_start(scrolled, True, True, 0)
        
        # Si la búsqueda va abajo Y en esta columna, agregarla al final
        if search_container == 'apps_column' and search_position == 'bottom':
            main_container.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 0)
            search_and_buttons_box = self.create_search_and_buttons_box()
            main_container.pack_start(search_and_buttons_box, False, False, 0)
        
        # Cargar primera categoría
        first_category = None
        preferred_order = ['Favorites', 'Desktop', 'System', 'Setup', 'Utility', 'Filesystem', 
                          'Graphic', 'Document', 'Business', 'Personal', 
                          'Network', 'Internet', 'Multimedia', 'Fun', 'Help', 'Leave']
        
        for cat in preferred_order:
            if cat in self.applications and self.applications[cat]:
                first_category = cat
                break
        
        if first_category:
            self.current_category = first_category
            GLib.idle_add(self.show_category_applications, first_category)
        
        return main_container
    
    def on_apps_area_enter(self, widget, event):
        """Handle mouse entering the applications area"""
        print("Mouse entered applications area")
        return False
    
    def create_statusbar(self):
        """Create status bar (kept for compatibility but not shown)"""
        statusbar = Gtk.Statusbar()
        context_id = statusbar.get_context_id("main")
        total_apps = sum(len(apps) for apps in self.applications.values())
        statusbar.push(context_id, f"Total applications: {total_apps}")
        return statusbar
    
    def create_app_button(self, app_info):
        """Create a button for an application"""
        button = Gtk.Button()
        button.set_can_focus(True)
        button.set_relief(Gtk.ReliefStyle.NONE)
        button.connect("clicked", self.on_app_clicked, app_info)
        
        # Contenedor vertical para ícono y nombre
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box.set_hexpand(False)
        box.set_property("margin-top", 4)
        box.set_property("margin-bottom", 4)
        
        # Ícono de la aplicación
        icon = self.load_app_icon(app_info.get('Icon', 'application-x-executable'))
        box.pack_start(icon, False, False, 0)
        
        # Nombre de la aplicación
        name_label = Gtk.Label(label=app_info['Name'])
        
        # Estilo de fuente
        font_description = Pango.FontDescription(self.config['font']['family'])
        font_description.set_size(self.config['font']['size_names'])
        name_label.override_font(font_description)
        
        # Solución definitiva para el salto de línea
        name_label.set_line_wrap(True)
        name_label.set_max_width_chars(10)  # Fija el ancho máximo en caracteres
        name_label.set_lines(2)
        name_label.set_ellipsize(Pango.EllipsizeMode.END)
        name_label.set_justify(Gtk.Justification.CENTER)
        name_label.set_halign(Gtk.Align.CENTER)
        
        box.pack_start(name_label, False, False, 0)
        
        button.add(box)
        button.set_tooltip_text(app_info.get('Comment', app_info['Name']))
        
        # Añade la información de la aplicación al botón para un acceso más fácil
        button.app_info = app_info
        
        # Habilitar eventos de mouse
        button.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        
        def on_right_click(widget, event):
            if event.button == 3:  # Clic derecho
                self.context_menu_active = True
                
                menu = Gtk.Menu()
                
                # Opción ejecutar
                item_run = Gtk.MenuItem(label=TR['Run'])
                item_run.connect("activate", lambda w: self.on_app_clicked(button, app_info))
                menu.append(item_run)
                
                # Separador
                separator = Gtk.SeparatorMenuItem()
                menu.append(separator)
                
                # Opción crear acceso directo
                item_shortcut = Gtk.MenuItem(label=TR['Create desktop shortcut'])
                item_shortcut.connect("activate", lambda w: self.create_desktop_shortcut(app_info))
                menu.append(item_shortcut)
                
                # Manejar cuando el menú se cierra
                def on_menu_deactivate(menu):
                    self.context_menu_active = False
                
                menu.connect("deactivate", on_menu_deactivate)
                menu.connect("cancel", on_menu_deactivate)
                
                # Mostrar menú
                menu.show_all()
                menu.popup_at_pointer(event)
                return True
            return False
        
        button.connect("button-press-event", on_right_click)
        
        return button

    
    def load_app_icon(self, icon_name):
        """
        Carga el ícono de la aplicación con caché y un sistema robusto de fallbacks.
        Almacena el pixbuf en caché para evitar que los íconos se "pierdan".
        """
        if not icon_name:
            icon_name = "application-x-executable"
    
        cache_key = f"{icon_name}_{self.icon_size}"
        pixbuf = self.icon_cache.get(cache_key)
    
        # 1. Si el pixbuf está en la caché, úsalo para crear un nuevo widget de imagen.
        if pixbuf:
            return Gtk.Image.new_from_pixbuf(pixbuf)
    
        # 2. Intentar cargar desde el tema de íconos.
        try:
            pixbuf = Gtk.IconTheme.get_default().load_icon(
                icon_name, self.icon_size, Gtk.IconLookupFlags.FORCE_SIZE
            )
        except Exception:
            pixbuf = None
    
        # 3. Si falla, intentar cargar desde una ruta de archivo.
        if pixbuf is None:
            icon_path = self.find_icon_path(icon_name)
            if icon_path and os.path.exists(icon_path):
                try:
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                        icon_path, self.icon_size, self.icon_size, True
                    )
                except Exception as e:
                    print(f"Failed to load image from path {icon_path}: {e}")
                    pixbuf = None
    
        # 4. Fallback final si todo lo demás falla.
        if pixbuf is None:
            try:
                pixbuf = Gtk.IconTheme.get_default().load_icon(
                    "application-x-executable", self.icon_size, Gtk.IconLookupFlags.FORCE_SIZE
                )
            except Exception:
                return Gtk.Image()
    
        # 5. Guardar el pixbuf en caché y devolver un nuevo widget de imagen.
        self.icon_cache[cache_key] = pixbuf
        return Gtk.Image.new_from_pixbuf(pixbuf)
    
    
    def find_icon_path(self, icon_name):
        """Encuentra el ícono en las rutas definidas, manejando extensiones comunes."""
        if os.path.isabs(icon_name) and os.path.exists(icon_name):
            return icon_name
    

        extensions = [
            '.png', '.svg', '.xpm', '.ico',
            '.jpg', '.jpeg', '.gif', '.tiff', '.bmp'
        ]
    
        for path in self.parser.icon_paths:
            if not os.path.exists(path):
                continue
    
            # Buscar el ícono con y sin extensiones
            base_name, ext = os.path.splitext(icon_name)
            if ext:  
                full_path = os.path.join(path, icon_name)
                if os.path.exists(full_path):
                    return full_path
            else:  
                for extension in extensions:
                    full_path = os.path.join(path, f"{base_name}{extension}")
                    if os.path.exists(full_path):
                        return full_path
    
        return None
    
    def is_valid_image_file(self, file_path):
        """Check if file is a valid image that GdkPixbuf can load"""
        if not os.path.isfile(file_path):
            return False
    
        _, ext = os.path.splitext(file_path.lower())
        valid_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.xpm', '.ico', '.tiff', '.tif'}
    
        if ext in valid_extensions:
            return True
    
        try:
            with open(file_path, 'rb') as f:
                header = f.read(16)
            if header.startswith(b'\x89PNG') or header.startswith(b'\xFF\xD8\xFF') or header.startswith(b'GIF87a') or header.startswith(b'GIF89a') or b'<svg' in header.lower() or header.startswith(b'<?xml') or b'XPM' in header or header.startswith(b'BM'):
                return True
        except (OSError, IOError):
            pass
    
        return False

        
        return None

    
    def show_category_applications(self, category):
        """Show applications from specific category with lazy loading"""
        if not self.apps_flowbox:
            return
        
        self.current_category = category
        
        for child in self.apps_flowbox.get_children():
            child.destroy()
        
        if category in self.applications:
            apps_data = [(category, self.applications[category])]
            GLib.idle_add(self.load_applications_batch, apps_data, 0)
        
        self.apps_flowbox.show_all()
    
    def load_applications_batch(self, apps_data, start_index, batch_size=10):
        """Load applications in batches to avoid UI freezing"""
        count = 0
        
        for category, apps in apps_data:
            for i, app in enumerate(apps[start_index:], start_index):
                if count >= batch_size:
                    GLib.idle_add(self.load_applications_batch, [(category, apps)], i)
                    return False
                
                button = self.create_app_button(app)
                self.apps_flowbox.add(button)
                count += 1
        
        self.apps_flowbox.show_all()
        return False
    
    def on_search_changed(self, search_entry):
        """Handle search text change"""
        if not self.apps_flowbox:
            return
            
        search_text = search_entry.get_text().lower()
        
        for child in self.apps_flowbox.get_children():
            child.destroy()
        
        if not search_text:
            if hasattr(self, 'current_category') and self.current_category:
                self.show_category_applications(self.current_category)
            else:
                preferred_order = ['Favorites', 'Desktop', 'System', 'Setup', 'Utility', 'Filesystem', 
                                  'Graphic', 'Document', 'Business', 'Personal', 
                                  'Network', 'Internet', 'Multimedia', 'Fun', 'Help', 'Leave']
                for cat in preferred_order:
                    if cat in self.applications and self.applications[cat]:
                        self.show_category_applications(cat)
                        break
            return
        
        for category, apps in self.applications.items():
            for app in apps:
                if (search_text in app['Name'].lower() or 
                    search_text in app.get('Comment', '').lower()):
                    button = self.create_app_button(app)
                    self.apps_flowbox.add(button)
        
        self.apps_flowbox.show_all()

    def on_apps_key_press(self, widget, event):
        """Handles key presses (arrows, Enter) on the apps flowbox."""
        keyval = event.keyval
        
        if keyval in [Gdk.KEY_Down, Gdk.KEY_Up, Gdk.KEY_Right, Gdk.KEY_Left]:
            self.navigate_apps(keyval)
            return True
        elif keyval == Gdk.KEY_Return:
            self.launch_selected_app()
            return True
        return False

    def navigate_apps(self, keyval):
        """Navigate through applications with arrow keys."""
        children = self.apps_flowbox.get_children()
        if not children:
            return

        selected_children = self.apps_flowbox.get_selected_children()
        if not selected_children:
            current_index = -1
        else:
            current_index = children.index(selected_children[0])

        new_index = -1
        
        # Determine the number of columns on the first row.
        # This is a more robust way to get the column count.
        cols = 1
        if len(children) > 1:
            y_pos_first_child = children[0].get_allocation().y
            for i in range(1, len(children)):
                if children[i].get_allocation().y == y_pos_first_child:
                    cols += 1
                else:
                    break

        if keyval == Gdk.KEY_Down:
            if current_index >= 0:
                new_index = current_index + cols
        elif keyval == Gdk.KEY_Up:
            if current_index >= 0:
                new_index = current_index - cols
        elif keyval == Gdk.KEY_Right:
            if current_index >= 0:
                new_index = current_index + 1
            else:
                new_index = 0
        elif keyval == Gdk.KEY_Left:
            if current_index > 0:
                new_index = current_index - 1
            else: 
                new_index = len(children) - 1

        if 0 <= new_index < len(children):
            self.apps_flowbox.unselect_all()
            self.apps_flowbox.select_child(children[new_index])
            children[new_index].grab_focus()

    def launch_selected_app(self):
        """Lanza la aplicación seleccionada con el teclado."""
        selected = self.apps_flowbox.get_selected_children()
        if selected:
            child = selected[0]
            button = child.get_child() 
            if button and hasattr(button, 'app_info'):
                self.on_app_clicked(button, button.app_info)


    def on_browser_search_clicked(self, button):
        """Launches a browser search with the text from the search box"""
        search_query = self.search_entry.get_text().strip()
        
        if not search_query:
            print("Search box is empty. Doing nothing.")
            return


        encoded_query = urllib.parse.quote_plus(search_query)
        search_url = f"https://www.google.com/search?q={encoded_query}"
        
        try:
            print(f"Launching browser search for: '{search_query}'")

            subprocess.Popen(["xdg-open", search_url], 
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)

            Gtk.main_quit()
        except FileNotFoundError:
            print("Error: 'xdg-open' not found. Please make sure you have a default browser configured.")
        except Exception as e:
            print(f"Failed to launch browser: {e}")

    def on_app_clicked(self, button, app_info):
        """Handle application launch"""
        try:
            GLib.timeout_add(50, lambda: Gtk.main_quit())
            
            command = app_info.get('Exec', '').strip()
            name = app_info.get('Name', 'Unknown')
            
            if not command:
                return
    

            if command.startswith('gtk-launch'):
                parts = command.split()
                if len(parts) >= 2:
                    app_name = parts[1]

                    desktop_paths = [
                        "/usr/share/applications/",
                        "/usr/local/share/applications/",
                        os.path.expanduser("~/.local/share/applications/")
                    ]
                    
                    for path in desktop_paths:
                        for ext in ['', '.desktop']:
                            desktop_file = os.path.join(path, app_name + ext)
                            if os.path.exists(desktop_file):
                                # Usar xdg-open
                                subprocess.Popen(["xdg-open", desktop_file],
                                               stdout=subprocess.DEVNULL,
                                               stderr=subprocess.DEVNULL)
                                return
                    
                    # Si no encuentra .desktop, buscar el ejecutable
                    print(f"⚠️ No se encontró .desktop para: {app_name}")
                    # Continuar con ejecución normal
            
            # 📁 DETECCIÓN DE CARPETAS
            import re
            path_match = re.search(r'(/[^\s\']+)', command)
            if path_match:
                potential_path = os.path.expanduser(path_match.group(1))
                if os.path.isdir(potential_path):
                    print(f"📂 Detectada carpeta: {potential_path}")
                    open_directory(potential_path)
                    return
            
            # 🚀 EJECUCIÓN NORMAL
            print(f"▶️ Ejecutando: {command}")
            subprocess.Popen(command, 
                            shell=True,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            start_new_session=True)
            
        except Exception as e:
            print(f"❌ Error lanzando {name}: {e}")   
                       

    def on_profile_clicked(self, button):
        """Open ProfileManager when profile thumbnail is clicked"""
        try:
            GLib.timeout_add(100, lambda: Gtk.main_quit())
            profile_manager_path = self.config['paths']['profile_manager']
            if os.path.exists(profile_manager_path):
                subprocess.Popen([profile_manager_path], 
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
            else:
                subprocess.Popen(["python3", profile_manager_path], 
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
            print(f"Launching Profile Manager: {profile_manager_path}")
        except Exception as e:
            print(f"Error opening Profile Manager: {e}")
            
    
    def on_config_clicked(self, button):
        """Lanza el script de configuración."""
        try:
            
            GLib.timeout_add(100, lambda: Gtk.main_quit())
            
            
            config_script = "/usr/local/pymenu/pymenu-config.py"
            subprocess.Popen([config_script],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
            print(f"Lanzando el configurador: {config_script}")
        except Exception as e:
            print(f"Error al lanzar el configurador: {e}")

    def on_shutdown_clicked(self, button):
        """Run shutdown command"""
        try:
            GLib.timeout_add(100, lambda: Gtk.main_quit())
            shutdown_cmd_path = self.config['paths']['shutdown_cmd']
            if os.path.exists(shutdown_cmd_path):
                subprocess.Popen(['sudo', shutdown_cmd_path],
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
            else:
                subprocess.Popen(['sudo', shutdown_cmd_path],
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
            print(f"Launching shutdown command: {shutdown_cmd_path}")
        except Exception as e:
            print(f"Failed to run shutdown command: {e}")
            
        
    def create_desktop_shortcut(self, app_info):
        """Crea un acceso directo .desktop usando URL= o fallback - SIN SUDO."""
        try:
            # 1. Obtener directorio de escritorio del usuario
            desktop_dir = os.path.expanduser('~/Desktop')
            if not os.path.isdir(desktop_dir):
                desktop_dir = os.path.expanduser('~/Escritorio')
            if not os.path.isdir(desktop_dir):
                desktop_dir = os.path.expanduser('~/Desktop')
                os.makedirs(desktop_dir, exist_ok=True)
            
            # 2. Buscar archivo .desktop original
            exec_cmd = app_info.get('Exec', '')
            if not exec_cmd:
                print("❌ No hay comando Exec")
                return
            
            try:
                parts = shlex.split(exec_cmd)
            except:
                parts = exec_cmd.split()
            
            if not parts:
                print("❌ No se pudo extraer comando")
                return
            
            app_name = os.path.basename(parts[0])
            desktop_id = self._find_desktop_file(exec_cmd)
            
            # 3. Crear archivo .desktop con URL= o como fallback
            shortcut_name = app_info.get('Name', 'Aplicación').replace('/', '_').replace(' ', '_')
            desktop_file_path = os.path.join(desktop_dir, f"{shortcut_name}.desktop")
            
            if desktop_id:
                # Usar URL= si encontramos el .desktop original
                desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Link
URL=/usr/share/applications/{desktop_id}
Icon={app_info.get('Icon', 'application-x-executable')}
Name={shortcut_name}
Comment=Acceso directo a {shortcut_name}
"""
                # 4. Escribir archivo y asignar permisos
                with open(desktop_file_path, 'w', encoding='utf-8') as f:
                    f.write(desktop_content)
                
                # Permisos para el enlace .desktop (solo lectura)
                os.chmod(desktop_file_path, 0o644)
                
            else:
                # Crear .desktop ejecutable directo como fallback
                desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name={shortcut_name}
Comment={app_info.get('Comment', shortcut_name)}
Exec={exec_cmd}
Icon={app_info.get('Icon', 'application-x-executable')}
Terminal=false
StartupNotify=true
Categories=Application;
"""
                # 4. Escribir archivo y asignar permisos
                with open(desktop_file_path, 'w', encoding='utf-8') as f:
                    f.write(desktop_content)
                
                # Permisos para el archivo .desktop ejecutable
                os.chmod(desktop_file_path, 0o755)
                
            print(f"✅ Acceso directo creado: {desktop_file_path}")
            
        except Exception as e:
            print(f"❌ Error creando acceso directo: {e}")
            
    def _find_desktop_file(self, exec_cmd):
        """Busca el archivo .desktop original (SOLO LECTURA)"""
        search_paths = [
            '/usr/share/applications',
            '/usr/local/share/applications',
            os.path.expanduser('~/.local/share/applications'),
        ]
        
        for search_path in search_paths:
            if not os.path.exists(search_path):
                continue
            
            try:
                for file_name in os.listdir(search_path):
                    if not file_name.endswith('.desktop'):
                        continue
                        
                    file_path = os.path.join(search_path, file_name)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            if exec_cmd.lower() in content.lower():
                                return file_name
                    except:
                        continue
                        
            except PermissionError:
                continue
        
        return None
            
def main():
    icon_size = None
    menu_file = None
    x = None
    y = None
    
    if len(sys.argv) >= 3:
        try:
            x = int(sys.argv[1])
            y = int(sys.argv[2])
        except ValueError:
            menu_file = sys.argv[1]
            try:
                icon_size = int(sys.argv[2])
                if icon_size not in [16, 24, 32, 40, 48]:
                    icon_size = None
            except ValueError:
                icon_size = None
    elif len(sys.argv) == 2:
        try:
            x = int(sys.argv[1])
            x = None
        except ValueError:
            menu_file = sys.argv[1]
    
    app = ArcMenuLauncher(icon_size, menu_file, x, y)
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    
    Gtk.main()

if __name__ == "__main__":
    main()
