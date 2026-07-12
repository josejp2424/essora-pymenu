#!/usr/bin/env python3
# Essora Store
# Copyright (C) 2025 nilsonmorales
# editadopor josejp2424 para essora
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib
import subprocess
import json
import os
import sys
import locale
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# === DEFINIR HOME_DIR ===
HOME_DIR = os.path.expanduser("~")

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

CONFIG_DIR = os.path.expanduser("~/.config/essorawm")
CONFIG_FILE = os.path.join(CONFIG_DIR, "pymenu.json")
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
    """Clase para cargar y guardar la configuración."""
    def __init__(self, config_file=CONFIG_FILE):
        self.config_file = config_file
        self.config = self.load_config()

    def get_default_config(self):
        """Devuelve una configuración predeterminada."""
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
                "profile_pic": os.path.join(CONFIG_DIR, "face"),
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
        if not os.path.exists(self.config_file):
            print(TR['Config file not found. Creating default config.'])
            default_config = self.load_default_config_from_file()
            self.save_config(default_config)
            return default_config
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
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
            print(f"{TR['Error loading config file:']} {e}. {TR['Using default config.']}")
            return self.get_default_config()

    def save_config(self, config_data):
        ensure_user_writable_path(self.config_file)
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f, indent=4)

class ConfigWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title=TR['PyMenu Configurator'])
        self.set_default_size(500, 600)
        self.set_resizable(True)
        self.connect("destroy", Gtk.main_quit)
        
        self.config_manager = ConfigManager()
        self.config = self.config_manager.config
        
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_vbox.set_border_width(10)
        self.add(main_vbox)
        
        notebook = Gtk.Notebook()
        main_vbox.pack_start(notebook, True, True, 0)
        
        notebook.append_page(self.create_window_tab(), Gtk.Label(label=TR['Window']))
        notebook.append_page(self.create_colors_tab(), Gtk.Label(label=TR['Colors']))
        notebook.append_page(self.create_font_tab(), Gtk.Label(label=TR['Font']))
        notebook.append_page(self.create_paths_tab(), Gtk.Label(label=TR['Paths']))
        notebook.append_page(self.create_categories_tab(), Gtk.Label(label=TR['Categories']))
        
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_halign(Gtk.Align.CENTER)
        
        save_button = Gtk.Button(label=TR['Save'])
        save_button.set_size_request(100, 30)
        save_button.connect("clicked", self.on_save_only_clicked)
        button_box.pack_start(save_button, False, False, 0)
        
        exit_button = Gtk.Button(label=TR['Exit'])
        exit_button.set_size_request(100, 30)
        exit_button.connect("clicked", self.on_exit_clicked)
        button_box.pack_start(exit_button, False, False, 0)
        
        main_vbox.pack_end(button_box, False, False, 0)
        
    def on_gtk_theme_toggled(self, check_button):
        """Manejar el toggle del checkbox de tema GTK"""
        self.config['colors']['use_gtk_theme'] = check_button.get_active()
        self.config_manager.save_config(self.config)
        self.update_color_widgets_sensitivity()
    
    def update_color_widgets_sensitivity(self):
        """Habilitar/deshabilitar widgets de color según el estado del tema GTK"""
        use_gtk_theme = self.config['colors'].get('use_gtk_theme', False)
        
        if hasattr(self, 'color_widgets'):
            for widget in self.color_widgets:
                widget.set_sensitive(not use_gtk_theme)         

    def create_window_tab(self):
        grid = Gtk.Grid(row_spacing=10, column_spacing=10)
        grid.set_border_width(10)
    
        grid.attach(Gtk.Label(label=TR['Window width:']), 0, 0, 1, 1)
        width_spin = Gtk.SpinButton.new_with_range(100, 1500, 10)
        width_spin.set_value(self.config['window']['width'])
        width_spin.connect("value-changed", self.on_spin_button_changed, "window", "width")
        grid.attach(width_spin, 1, 0, 1, 1)
    
        grid.attach(Gtk.Label(label=TR['Window height:']), 0, 1, 1, 1)
        height_spin = Gtk.SpinButton.new_with_range(100, 1500, 10)
        height_spin.set_value(self.config['window']['height'])
        height_spin.connect("value-changed", self.on_spin_button_changed, "window", "height")
        grid.attach(height_spin, 1, 1, 1, 1)
    
        # Show window frame
        frame_label_text = TR['Show window frame:'] + '\n' + TR['(No transparency)']
        frame_label = Gtk.Label(label=frame_label_text)
        frame_label.set_halign(Gtk.Align.START)
        frame_label.set_line_wrap(True)
        grid.attach(frame_label, 0, 2, 1, 1)
    
        decorated_check = Gtk.CheckButton()
        decorated_check.set_active(self.config['window'].get('decorated_window', True))
        decorated_check.connect("toggled", self.on_check_toggled, "window", "decorated_window")
        grid.attach(decorated_check, 1, 2, 1, 1)
    
        # Hide header
        grid.attach(Gtk.Label(label=TR['Hide header:']), 0, 3, 1, 1)
        hide_header_check = Gtk.CheckButton()
        hide_header_check.set_active(self.config['window'].get('hide_header', False))
        hide_header_check.connect("toggled", self.on_check_toggled, "window", "hide_header")
        grid.attach(hide_header_check, 1, 3, 1, 1)
        
        grid.attach(Gtk.Label(label=TR['Hide profile pic:']), 0, 4, 1, 1)
        hide_profile_check = Gtk.CheckButton()
        hide_profile_check.set_active(self.config['window'].get('hide_profile_pic', False))
        hide_profile_check.connect("toggled", self.on_check_toggled, "window", "hide_profile_pic")
        grid.attach(hide_profile_check, 1, 4, 1, 1)
        
        # Header layout
        grid.attach(Gtk.Label(label=TR['Header layout:']), 0, 5, 1, 1)
        header_layout_combo = Gtk.ComboBoxText()
        header_layout_combo.append("left", TR['Avatar left'])
        header_layout_combo.append("center", TR['Avatar center'])
        header_layout_combo.append("right", TR['Avatar right'])
        current_layout = self.config['window'].get('header_layout', 'left')
        header_layout_combo.set_active_id(current_layout)
        header_layout_combo.connect("changed", self.on_combobox_changed, 'window', 'header_layout')
        grid.attach(header_layout_combo, 1, 5, 1, 1)
        
        # Header text alignment
        grid.attach(Gtk.Label(label=TR['Header text alignment:']), 0, 6, 1, 1)
        header_text_align_combo = Gtk.ComboBoxText()
        header_text_align_combo.append("left", TR['left'])
        header_text_align_combo.append("center", TR['center'])
        header_text_align_combo.append("right", TR['right'])
        current_text_align = self.config['window'].get('header_text_align', 'left')
        header_text_align_combo.set_active_id(current_text_align)
        header_text_align_combo.connect("changed", self.on_combobox_changed, 'window', 'header_text_align')
        grid.attach(header_text_align_combo, 1, 6, 1, 1)
        
        # Hide OS name
        grid.attach(Gtk.Label(label=TR['Hide OS name:']), 0, 7, 1, 1)
        hide_os_check = Gtk.CheckButton()
        hide_os_check.set_active(self.config['window'].get('hide_os_name', False))
        hide_os_check.connect("toggled", self.on_check_toggled, "window", "hide_os_name")
        grid.attach(hide_os_check, 1, 7, 1, 1)
        
        # Hide kernel
        grid.attach(Gtk.Label(label=TR['Hide kernel:']), 0, 8, 1, 1)
        hide_kernel_check = Gtk.CheckButton()
        hide_kernel_check.set_active(self.config['window'].get('hide_kernel', False))
        hide_kernel_check.connect("toggled", self.on_check_toggled, "window", "hide_kernel")
        grid.attach(hide_kernel_check, 1, 8, 1, 1)
        
        # Hide hostname
        grid.attach(Gtk.Label(label=TR['Hide hostname:']), 0, 9, 1, 1)
        hide_hostname_check = Gtk.CheckButton()
        hide_hostname_check.set_active(self.config['window'].get('hide_hostname', False))
        hide_hostname_check.connect("toggled", self.on_check_toggled, "window", "hide_hostname")
        grid.attach(hide_hostname_check, 1, 9, 1, 1)
        
        # Hide categories text
        grid.attach(Gtk.Label(label=TR['Hide categories text:']), 0, 10, 1, 1)
        hide_cat_text_check = Gtk.CheckButton()
        hide_cat_text_check.set_active(self.config['window'].get('hide_category_text', False))
        hide_cat_text_check.connect("toggled", self.on_check_toggled, 'window', 'hide_category_text')
        grid.attach(hide_cat_text_check, 1, 10, 1, 1)
    
        # ===== NUEVAS OPCIONES =====
        
        # Hide places sidebar
        places_label_text = TR['Hide places sidebar:'] + '\n' + TR['(Hides both places and favorites)']
        places_label = Gtk.Label(label=places_label_text)
        places_label.set_halign(Gtk.Align.START)
        places_label.set_line_wrap(True)
        grid.attach(places_label, 0, 11, 1, 1)
        
        hide_places_check = Gtk.CheckButton()
        hide_places_check.set_active(self.config['window'].get('hide_places', False))
        hide_places_check.connect("toggled", self.on_check_toggled, "window", "hide_places")
        grid.attach(hide_places_check, 1, 11, 1, 1)
        
        # Hide favorites only (solo si places está visible)
        favorites_label_text = TR['Hide favorites only:'] + '\n' + TR['(Show places but hide favorites)']
        favorites_label = Gtk.Label(label=favorites_label_text)
        favorites_label.set_halign(Gtk.Align.START)
        favorites_label.set_line_wrap(True)
        grid.attach(favorites_label, 0, 12, 1, 1)
        
        hide_favorites_check = Gtk.CheckButton()
        hide_favorites_check.set_active(self.config['window'].get('hide_favorites', False))
        hide_favorites_check.connect("toggled", self.on_check_toggled, "window", "hide_favorites")
        grid.attach(hide_favorites_check, 1, 12, 1, 1)
        
        # Profile in places (mover perfil a la columna Places)
        profile_places_label_text = TR['Show profile in places sidebar:'] + '\n' + TR['(Instead of header)']
        profile_places_label = Gtk.Label(label=profile_places_label_text)
        profile_places_label.set_halign(Gtk.Align.START)
        profile_places_label.set_line_wrap(True)
        grid.attach(profile_places_label, 0, 13, 1, 1)
        
        # En la línea donde se crea el checkbox de profile_in_places:
        profile_in_places_check = Gtk.CheckButton()
        profile_in_places_check.set_active(self.config['window'].get('profile_in_places', False))  # ← False por defecto
        profile_in_places_check.connect("toggled", self.on_check_toggled, "window", "profile_in_places")
        grid.attach(profile_in_places_check, 1, 13, 1, 1)
    
        # Icon size
        grid.attach(Gtk.Label(label=TR['Icon size:']), 0, 14, 1, 1)
        icon_size_spin = Gtk.SpinButton.new_with_range(16, 64, 8)
        icon_size_spin.set_value(self.config['window'].get('icon_size', 32))
        icon_size_spin.connect("value-changed", self.on_spin_button_changed, "window", "icon_size")
        grid.attach(icon_size_spin, 1, 14, 1, 1)
    
        # Category icon size
        grid.attach(Gtk.Label(label=TR['Category icon size:']), 0, 15, 1, 1)
        category_icon_size_spin = Gtk.SpinButton.new_with_range(16, 64, 8)
        category_icon_size_spin.set_value(self.config['window'].get('category_icon_size', 24))
        category_icon_size_spin.connect("value-changed", self.on_spin_button_changed, "window", "category_icon_size")
        grid.attach(category_icon_size_spin, 1, 15, 1, 1)
    
        # Profile pic size
        grid.attach(Gtk.Label(label=TR['Profile pic size:']), 0, 16, 1, 1)
        profile_pic_size_spin = Gtk.SpinButton.new_with_range(64, 256, 8)
        profile_pic_size_spin.set_value(self.config['window'].get('profile_pic_size', 128))
        profile_pic_size_spin.connect("value-changed", self.on_spin_button_changed, "window", "profile_pic_size")
        grid.attach(profile_pic_size_spin, 1, 16, 1, 1)
    
        # Profile pic shape
        grid.attach(Gtk.Label(label=TR['Profile pic shape:']), 0, 17, 1, 1)
        shape_combo = Gtk.ComboBoxText()
        shape_combo.append("square", TR['square'])
        shape_combo.append("circular", TR['circular'])
        current_shape = self.config['window'].get('profile_pic_shape', 'square')
        shape_combo.set_active_id(current_shape)
        shape_combo.connect("changed", self.on_combobox_changed, 'window', 'profile_pic_shape')
        grid.attach(shape_combo, 1, 17, 1, 1)
    
        # Horizontal alignment
        grid.attach(Gtk.Label(label=TR['Horizontal alignment:']), 0, 18, 1, 1)
        halign_combo = Gtk.ComboBoxText()
        halign_combo.append("center", TR['center'])
        halign_combo.append("left", TR['left'])
        halign_combo.append("right", TR['right'])
        current_halign = self.config['window'].get('halign', 'center')
        halign_combo.set_active_id(current_halign)
        halign_combo.connect("changed", self.on_combobox_changed, "window", "halign")
        grid.attach(halign_combo, 1, 18, 1, 1)
        
        # Search bar position
        grid.attach(Gtk.Label(label=TR['Search bar position:']), 0, 19, 1, 1)
        searchbar_combo = Gtk.ComboBoxText()
        searchbar_combo.append("top", TR['top'])
        searchbar_combo.append("bottom", TR['bottom'])
        current_searchbar = self.config['window'].get('search_bar_position', 'bottom')
        searchbar_combo.set_active_id(current_searchbar)
        searchbar_combo.connect("changed", self.on_combobox_changed, 'window', 'search_bar_position')
        grid.attach(searchbar_combo, 1, 19, 1, 1)
        
        # Control para search_bar_container (añadir después de la posición)
        grid.attach(Gtk.Label(label=TR['Search bar container:']), 0, 20, 1, 1)
        container_combo = Gtk.ComboBoxText()
        container_combo.append("window", TR['In window'])
        container_combo.append("apps_column", TR['In applications column'])
        current_container = self.config['window'].get('search_bar_container', 'window')
        container_combo.set_active_id(current_container)
        container_combo.connect("changed", self.on_combobox_changed, 'window', 'search_bar_container')
        grid.attach(container_combo, 1, 20, 1, 1)        
    
        # Envolver el grid en un ScrolledWindow
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.add(grid)
        return scrolled_window
    
        
    def on_check_toggled(self, check_button, category, key):
        """Handle Gtk.CheckButton toggle events and save the state."""
        self.config[category][key] = check_button.get_active()
        
        if key == "profile_in_places" and check_button.get_active():
            self.config['window']['hide_profile_pic'] = False
            
            if hasattr(self, 'hide_profile_check'):
                self.hide_profile_check.set_active(False)
        
        elif key == "hide_places" and check_button.get_active():
            self.config['window']['profile_in_places'] = False
            
            # Actualizar el checkbox si existe
            if hasattr(self, 'profile_in_places_check'):
                self.profile_in_places_check.set_active(False)
        
        self.config_manager.save_config(self.config)
        
    def on_combobox_changed(self, combobox, category, key):
        """Manejar el cambio en un Gtk.ComboBoxText y guarda la nueva configuración,
           usando el ID activo."""
        selected_id = combobox.get_active_id()
        if selected_id is not None:
            self.config[category][key] = selected_id
            self.config_manager.save_config(self.config)               

    def create_colors_tab(self):
        grid = Gtk.Grid(row_spacing=10, column_spacing=10)
        grid.set_border_width(10)
        
        grid.attach(Gtk.Label(label=TR['Use system theme:']), 0, 0, 1, 1)
        gtk_theme_check = Gtk.CheckButton()
        gtk_theme_check.set_active(self.config['colors'].get('use_gtk_theme', False))
        gtk_theme_check.connect("toggled", self.on_gtk_theme_toggled)
        grid.attach(gtk_theme_check, 1, 0, 1, 1)
        
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        grid.attach(separator, 0, 1, 2, 1)
        
        colors_to_config = {
            "text_header_os": TR['Header (OS):'],
            "text_header_kernel": TR['Header (Kernel):'],
            "text_header_hostname": TR['Header (Hostname):'],
            "background": TR['Background color:'],
            "border": TR['Border color:'],
            "categories_background": TR['Categories background:'],
            "text_normal": TR['Text normal:'],
            "button_normal_background": TR['Button background:'],
            "button_text": TR['Button text:'],
            "hover_background": TR['Hover background:'],            
        }        
        
        self.color_widgets = []
        
        keys_for_hex_only = ["text_header_os", "text_header_kernel", "text_header_hostname", "text_normal", "button_text"]
        
        for i, (key, label) in enumerate(colors_to_config.items()):
            row = i + 2  
            color_label = Gtk.Label(label=label)
            grid.attach(color_label, 0, row, 1, 1)
            
            color_button = Gtk.ColorButton()
            
            if key in keys_for_hex_only:
                color_button.set_use_alpha(False)
            else:
                color_button.set_use_alpha(True)
    
            rgba = self.hex_to_rgba(self.config['colors'][key])
            if rgba:
                color_button.set_rgba(rgba)
            color_button.connect("color-set", self.on_color_set, "colors", key)
            grid.attach(color_button, 1, row, 1, 1)
            
            self.color_widgets.extend([color_label, color_button])
        
        self.update_color_widgets_sensitivity()
        
        return grid
        
    def create_font_tab(self):
        grid = Gtk.Grid(row_spacing=10, column_spacing=10)
        grid.set_border_width(10)
        
        grid.attach(Gtk.Label(label=TR['Font family:']), 0, 0, 1, 1)
        font_button = Gtk.FontButton()
        font_button.set_font(self.config['font']['family'])
        font_button.connect("font-set", self.on_font_set, "font", "family")
        grid.attach(font_button, 1, 0, 1, 1)
        
        sizes_to_config = {
            "size_categories": TR['Category size:'],
            "size_names": TR['App name size:'],
            "size_header": TR['Header size:']
        }
        
        for i, (key, label) in enumerate(sizes_to_config.items(), start=1):
            grid.attach(Gtk.Label(label=label), 0, i, 1, 1)
            size_spin = Gtk.SpinButton.new_with_range(5000, 50000, 1000)
            size_spin.set_value(self.config['font'][key])
            size_spin.connect("value-changed", self.on_spin_button_changed, "font", key)
            grid.attach(size_spin, 1, i, 1, 1)
            
        return grid

    def create_paths_tab(self):
        grid = Gtk.Grid(row_spacing=10, column_spacing=10)
        grid.set_border_width(10)
        
        paths_to_config = {
            "profile_pic": TR['Profile pic path:'],
            "profile_manager": TR['Profile manager:'],
            "shutdown_cmd": TR['Shutdown command:'],
            "jwmrc_tray": TR['JWM Tray config:'],
            "tint2rc": TR['Tint2 config:']
        }

        grid.attach(Gtk.Label(label=paths_to_config["profile_pic"]), 0, 0, 1, 1)
        entry_profile_pic = Gtk.Entry()
        entry_profile_pic.set_text(self.config['paths']["profile_pic"])
        entry_profile_pic.connect("changed", self.on_path_changed, "paths", "profile_pic")
        grid.attach(entry_profile_pic, 1, 0, 1, 1)
        browse_profile_pic = Gtk.Button(label="...")
        browse_profile_pic.connect("clicked", self.on_browse_file, entry_profile_pic, TR['Select profile picture'])
        grid.attach(browse_profile_pic, 2, 0, 1, 1)
        
        # Fila 1: Profile manager
        grid.attach(Gtk.Label(label=paths_to_config["profile_manager"]), 0, 1, 1, 1)
        entry_profile_manager = Gtk.Entry()
        entry_profile_manager.set_text(self.config['paths']["profile_manager"])
        entry_profile_manager.connect("changed", self.on_path_changed, "paths", "profile_manager")
        grid.attach(entry_profile_manager, 1, 1, 1, 1)
        browse_profile_manager = Gtk.Button(label="...")
        browse_profile_manager.connect("clicked", self.on_browse_file, entry_profile_manager, TR['Select profile manager'])
        grid.attach(browse_profile_manager, 2, 1, 1, 1)
        
        # Fila 2: Shutdown command
        grid.attach(Gtk.Label(label=paths_to_config["shutdown_cmd"]), 0, 2, 1, 1)
        entry_shutdown_cmd = Gtk.Entry()
        entry_shutdown_cmd.set_text(self.config['paths']["shutdown_cmd"])
        entry_shutdown_cmd.connect("changed", self.on_path_changed, "paths", "shutdown_cmd")
        grid.attach(entry_shutdown_cmd, 1, 2, 1, 1)
        browse_shutdown_cmd = Gtk.Button(label="...")
        browse_shutdown_cmd.connect("clicked", self.on_browse_file, entry_shutdown_cmd, TR['Select shutdown command'])
        grid.attach(browse_shutdown_cmd, 2, 2, 1, 1)
        
        # Separador 1
        separator1 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        grid.attach(separator1, 0, 3, 3, 1)
        

        grid.attach(Gtk.Label(label=TR['Use Tint2 (instead of JWM):']), 0, 4, 1, 1)
        self.tint2_checkbox = Gtk.CheckButton()
        self.tint2_checkbox.set_active(self.config.get('tray', {}).get('use_tint2', False))
        self.tint2_checkbox.connect("toggled", self.on_tint2_toggled)
        grid.attach(self.tint2_checkbox, 1, 4, 1, 1)
        
        # Fila 5: JWM config
        self.jwm_label = Gtk.Label(label=paths_to_config["jwmrc_tray"])
        grid.attach(self.jwm_label, 0, 5, 1, 1)
        self.entry_jwmrc_tray = Gtk.Entry()
        self.entry_jwmrc_tray.set_text(self.config['paths'].get("jwmrc_tray", "/usr/share/jwm/jwm/jwmrc-tray"))
        self.entry_jwmrc_tray.connect("changed", self.on_path_changed, "paths", "jwmrc_tray")
        grid.attach(self.entry_jwmrc_tray, 1, 5, 1, 1)
        browse_jwm = Gtk.Button(label="...")
        browse_jwm.connect("clicked", self.on_browse_file, self.entry_jwmrc_tray, TR['Select JWM config'])
        grid.attach(browse_jwm, 2, 5, 1, 1)
        
        # Fila 6: Tint2 config
        self.tint2_label = Gtk.Label(label=paths_to_config["tint2rc"])
        grid.attach(self.tint2_label, 0, 6, 1, 1)
        self.entry_tint2rc = Gtk.Entry()
        self.entry_tint2rc.set_text(self.config['paths'].get("tint2rc", "/usr/share/tint2/tint2/tint2rc"))
        self.entry_tint2rc.connect("changed", self.on_path_changed, "paths", "tint2rc")
        grid.attach(self.entry_tint2rc, 1, 6, 1, 1)
        browse_tint2 = Gtk.Button(label="...")
        browse_tint2.connect("clicked", self.on_browse_file, self.entry_tint2rc, TR['Select Tint2 config'])
        grid.attach(browse_tint2, 2, 6, 1, 1)
        
        # Separador 2
        separator2 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        grid.attach(separator2, 0, 7, 3, 1)

        grid.attach(Gtk.Label(label=TR['Search engine:']), 0, 8, 1, 1)
        search_engine_combo = Gtk.ComboBoxText()
        search_engine_combo.append("google", "Google")
        search_engine_combo.append("duckduckgo", "DuckDuckGo")
        search_engine_combo.append("brave", "Brave Search")
        search_engine_combo.append("searxng", "SearXNG")
        search_engine_combo.append("librex", "LibreX")
        search_engine_combo.set_active_id(self.config.get('search_engine', {}).get('engine', 'google'))
        search_engine_combo.connect("changed", self.on_search_engine_changed)
        grid.attach(search_engine_combo, 1, 8, 2, 1)
        
        # Separador 3
        separator3 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        grid.attach(separator3, 0, 9, 3, 1)

        fav_title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        favorites_label = Gtk.Label(label=f"<b>{TR['Favorites']}</b>")
        favorites_label.set_use_markup(True)
        fav_title_box.pack_start(favorites_label, False, False, 0)
        
        btn_always_add = Gtk.Button(label=TR.get('Add favorite', 'Add favorite'))
        btn_always_add.connect("clicked", self.on_add_favorite_clicked)
        fav_title_box.pack_end(btn_always_add, False, False, 0)
        
        grid.attach(fav_title_box, 0, 10, 3, 1)
        
        self.favorites_listbox = Gtk.ListBox()
        self.favorites_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        
        fav_scroll = Gtk.ScrolledWindow()
        fav_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        fav_scroll.set_size_request(-1, 200)
        fav_scroll.add(self.favorites_listbox)
        
        grid.attach(fav_scroll, 0, 11, 3, 1)
        

        self.update_tray_widgets_sensitivity()
        

        def load_favorites_idle():
            self.load_favorites_list()
            return False
        GLib.idle_add(load_favorites_idle)
        
        # Envolver todo en un ScrolledWindow principal para Puppy Linux
        main_scrolled = Gtk.ScrolledWindow()
        main_scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        main_scrolled.add(grid)
        
        return main_scrolled
        
# ===== FUNCIONES PARA FAVORITOS =====

    def load_favorites_list(self):
        """Cargar y mostrar la lista de favoritos actual"""
        # Limpiar lista actual
        for child in self.favorites_listbox.get_children():
            self.favorites_listbox.remove(child)
        
        favorites = self.config.get('favorites', [])
        
        if not favorites:
            row = Gtk.ListBoxRow()
            
            btn_empty = Gtk.Button(label=TR.get('No favorites yet. Click here to add one.', 'No favorites yet. Click here to add one.'))
            btn_empty.set_relief(Gtk.ReliefStyle.NONE)
            
            btn_empty.connect("clicked", self.on_add_favorite_clicked)
            
            row.add(btn_empty)
            self.favorites_listbox.add(row)
        else:
            for fav in favorites:
                row = self.create_favorite_row(fav)
                self.favorites_listbox.add(row)
        
        self.favorites_listbox.show_all()
    
    def create_favorite_row(self, fav):
        """Crear una fila para mostrar un favorito con botones de acción"""
        row = Gtk.ListBoxRow()
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        hbox.set_margin_top(5)
        hbox.set_margin_bottom(5)
        hbox.set_margin_start(10)
        hbox.set_margin_end(10)
        
        # Usar el nombre directamente del JSON
        name = fav.get('name', 'Unnamed')
        exec_cmd = fav.get('exec', '')
        icon_name = fav.get('icon', 'application-x-executable')
        
        # Determinar ícono basado en el tipo de comando
        if 'gtk-launch' in exec_cmd:
            icon_text = "📱"
        elif any(x in exec_cmd for x in ['pcmanfm', 'rox', 'thunar', 'nautilus']):
            icon_text = "📁"
        else:
            icon_text = "⚙️"
        
        # Ícono
        icon_label = Gtk.Label(label=icon_text)
        hbox.pack_start(icon_label, False, False, 0)
        
        # Nombre del favorito
        name_label = Gtk.Label(label=name)
        name_label.set_halign(Gtk.Align.START)
        hbox.pack_start(name_label, True, True, 0)
        
        # Comando (truncado)
        cmd_preview = exec_cmd[:30] + "..." if len(exec_cmd) > 30 else exec_cmd
        cmd_label = Gtk.Label()
        cmd_label.set_markup(f"<small><i>{cmd_preview}</i></small>")
        hbox.pack_start(cmd_label, False, False, 0)
        
        # Botón eliminar
        delete_button = Gtk.Button(label="🗑️")
        delete_button.set_relief(Gtk.ReliefStyle.NONE)
        delete_button.connect("clicked", self.on_delete_favorite_clicked, fav)
        hbox.pack_start(delete_button, False, False, 0)
        
        row.add(hbox)
        return row
    
    def on_add_favorite_clicked(self, button):
        """Mostrar diálogo para agregar un nuevo favorito"""
        dialog = Gtk.Dialog(
            title=TR.get('Add Favorite', 'Add Favorite'),
            parent=self,
            flags=0
        )
        dialog.add_buttons(
            TR['Cancel'], Gtk.ResponseType.CANCEL,
            TR.get('Add', 'Add'), Gtk.ResponseType.OK
        )
        dialog.set_default_size(500, 400)
        
        content = dialog.get_content_area()
        content.set_spacing(10)
        content.set_border_width(10)
        
        # Notebook con pestañas para cada tipo
        notebook = Gtk.Notebook()
        content.pack_start(notebook, True, True, 0)
        
        # === PESTAÑA 1: APLICACIÓN ===
        app_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        app_box.set_border_width(10)
        
        app_label = Gtk.Label(label=TR.get('Select an application:', 'Select an application:'))
        app_label.set_halign(Gtk.Align.START)
        app_box.pack_start(app_label, False, False, 0)
        
        # Caja de búsqueda
        search_entry = Gtk.SearchEntry()
        search_entry.set_placeholder_text(TR.get('Search applications...', 'Search applications...'))
        app_box.pack_start(search_entry, False, False, 0)
        
        app_scrolled = Gtk.ScrolledWindow()
        app_scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        app_listbox = Gtk.ListBox()
        app_listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        
        desktop_files = self.get_desktop_files()
        all_rows = [] 
        
        for desktop_file in sorted(desktop_files):
            display_name = os.path.basename(desktop_file).replace('.desktop', '')
            row = Gtk.ListBoxRow()
            label = Gtk.Label(label=display_name)
            label.set_halign(Gtk.Align.START)
            label.set_margin_start(10)
            label.set_margin_top(5)
            label.set_margin_bottom(5)
            row.add(label)
            row.desktop_path = desktop_file
            row.display_name = display_name
            app_listbox.add(row)
            all_rows.append(row)
        
        def on_search_changed(entry):
            search_text = entry.get_text().lower()
            for row in all_rows:
                if search_text in row.display_name.lower():
                    row.show()
                else:
                    row.hide()
        
        search_entry.connect("search-changed", on_search_changed)
        
        app_scrolled.add(app_listbox)
        app_box.pack_start(app_scrolled, True, True, 0)
        notebook.append_page(app_box, Gtk.Label(label=TR.get('Application', 'Application')))
        
        # === PESTAÑA 2: DIRECTORIO ===
        dir_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        dir_box.set_border_width(10)
        dir_label = Gtk.Label(label=TR.get('Select a directory:', 'Select a directory:'))
        dir_label.set_halign(Gtk.Align.START)
        dir_box.pack_start(dir_label, False, False, 0)
        
        dir_entry = Gtk.Entry()
        dir_entry.set_placeholder_text(TR.get('Path to directory', 'Path to directory'))
        dir_box.pack_start(dir_entry, False, False, 0)
        
        dir_browse = Gtk.Button(label=TR.get('Browse...', 'Browse...'))
        dir_browse.connect("clicked", self.on_browse_directory, dir_entry)
        dir_box.pack_start(dir_browse, False, False, 0)
        
        notebook.append_page(dir_box, Gtk.Label(label=TR.get('Directory', 'Directory')))
        
        # === PESTAÑA 3: COMANDO PERSONALIZADO ===
        cmd_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        cmd_box.set_border_width(10)
        
        # Nombre
        cmd_box.pack_start(Gtk.Label(label=TR.get('Name:', 'Name:'), halign=Gtk.Align.START), False, False, 0)
        cmd_name_entry = Gtk.Entry()
        cmd_name_entry.set_placeholder_text(TR.get('Favorite name', 'Favorite name'))
        cmd_box.pack_start(cmd_name_entry, False, False, 0)
        
        # Comando
        cmd_box.pack_start(Gtk.Label(label=TR.get('Command:', 'Command:'), halign=Gtk.Align.START), False, False, 0)
        cmd_exec_entry = Gtk.Entry()
        cmd_exec_entry.set_placeholder_text(TR.get('Command to execute', 'Command to execute'))
        cmd_box.pack_start(cmd_exec_entry, False, False, 0)
        
        # Ícono con botón de explorar
        cmd_box.pack_start(Gtk.Label(label=TR.get('Icon (optional):', 'Icon (optional):'), halign=Gtk.Align.START), False, False, 0)
        
        # Caja horizontal para entrada + botón
        icon_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        cmd_icon_entry = Gtk.Entry()
        cmd_icon_entry.set_placeholder_text(TR.get('Icon name or path', 'Icon name or path'))
        icon_hbox.pack_start(cmd_icon_entry, True, True, 0)
        
        # Botón explorar ícono
        icon_browse_button = Gtk.Button(label="📂")
        icon_browse_button.set_tooltip_text(TR.get('Browse icon', 'Browse icon'))
        icon_browse_button.connect("clicked", self.on_browse_icon_clicked, cmd_icon_entry)
        icon_hbox.pack_start(icon_browse_button, False, False, 0)
        
        cmd_box.pack_start(icon_hbox, False, False, 0)
        
        notebook.append_page(cmd_box, Gtk.Label(label=TR.get('Command', 'Command')))
        
        dialog.show_all()
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            current_page = notebook.get_current_page()
            fav = None
            
            if current_page == 0:  
                selected = app_listbox.get_selected_row()
                if selected:
                    
                    icon_name = "application-x-desktop"
                    try:
                        with open(selected.desktop_path, 'r') as f:
                            for line in f:
                                if line.startswith("Icon="):
                                    icon_name = line.split("=")[1].strip()
                                    break
                    except: 
                        pass
                    
                    fav = {
                        'name': selected.display_name,
                        'exec': f"gtk-launch {os.path.basename(selected.desktop_path)}",
                        'icon': icon_name
                    }
            
            elif current_page == 1: 
                path = dir_entry.get_text().strip()
                if path:
                    fav = {
                        'name': os.path.basename(path) or path,
                        'exec': f"pcmanfm '{path}'",  
                        'icon': 'folder'
                    }
            
            elif current_page == 2:  
                name = cmd_name_entry.get_text().strip()
                exec_cmd = cmd_exec_entry.get_text().strip()
                icon = cmd_icon_entry.get_text().strip()
                if name and exec_cmd:
                    fav = {
                        'name': name,
                        'exec': exec_cmd,
                        'icon': icon if icon else 'application-x-executable'
                    }
            
            # Guardar si se creó un objeto favorito válido
            if fav:
                if 'favorites' not in self.config:
                    self.config['favorites'] = []
                self.config['favorites'].append(fav)
                self.config_manager.save_config(self.config)
                self.load_favorites_list()  
        
        dialog.destroy()
        
    def on_delete_favorite_clicked(self, button, fav):
        """Eliminar un favorito de la lista"""
        if 'favorites' in self.config:
            for i, existing_fav in enumerate(self.config['favorites']):
                if (existing_fav.get('name') == fav.get('name') and 
                    existing_fav.get('exec') == fav.get('exec')):
                    del self.config['favorites'][i]
                    self.config_manager.save_config(self.config)
                    self.load_favorites_list()
                    break        
    
    def get_desktop_files(self):
        """Obtener lista de archivos .desktop del sistema"""
        desktop_files = []
        search_paths = [
            '/usr/share/applications',
            '/usr/local/share/applications',
            os.path.expanduser('~/.local/share/applications')
        ]
        
        for path in search_paths:
            if os.path.exists(path):
                for file in os.listdir(path):
                    if file.endswith('.desktop'):
                        desktop_files.append(os.path.join(path, file))
        
        return desktop_files
        
    def on_search_engine_changed(self, combobox):
        """Manejar el cambio de motor de búsqueda"""
        if 'search_engine' not in self.config:
            self.config['search_engine'] = {}
        self.config['search_engine']['engine'] = combobox.get_active_id()
        self.config_manager.save_config(self.config)
    
    def on_browse_file(self, button, entry, dialog_title):
        """Abrir diálogo para seleccionar archivo con gestor de archivos"""
        dialog = Gtk.FileChooserDialog(
            title=dialog_title,
            parent=self,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            TR['Cancel'], Gtk.ResponseType.CANCEL,
            TR['Select'], Gtk.ResponseType.OK
        )
        
        file_manager_button = Gtk.Button(label="📂 " + TR.get('Open File Manager', 'Open File Manager'))
        file_manager_button.connect("clicked", self.on_open_file_manager_clicked)
        dialog.get_action_area().pack_start(file_manager_button, False, False, 0)
        dialog.get_action_area().reorder_child(file_manager_button, 0)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            selected_file = dialog.get_filename()
            entry.set_text(selected_file)
        
        dialog.destroy()
    
    def on_browse_directory(self, button, entry):
        """Abrir selector de directorio"""
        dialog = Gtk.FileChooserDialog(
            title=TR.get('Select Directory', 'Select Directory'),
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            TR['Cancel'], Gtk.ResponseType.CANCEL,
            TR['Select'], Gtk.ResponseType.OK
        )
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            entry.set_text(dialog.get_filename())
        
        dialog.destroy()
    
    def on_browse_icon_clicked(self, button, entry):
        """Abrir diálogo para seleccionar un ícono"""
        dialog = Gtk.FileChooserDialog(
            title=TR.get('Select Icon', 'Select Icon'),
            parent=self,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            TR['Cancel'], Gtk.ResponseType.CANCEL,
            TR['Select'], Gtk.ResponseType.OK
        )
        
        # Filtrar archivos de imagen
        filter_images = Gtk.FileFilter()
        filter_images.set_name(TR.get('Image files', 'Image files'))
        filter_images.add_mime_type('image/png')
        filter_images.add_mime_type('image/svg+xml')
        filter_images.add_mime_type('image/x-icon')
        filter_images.add_pattern('*.png')
        filter_images.add_pattern('*.svg')
        filter_images.add_pattern('*.ico')
        filter_images.add_pattern('*.xpm')
        dialog.add_filter(filter_images)
        
        # Filtrar todos los archivos
        filter_all = Gtk.FileFilter()
        filter_all.set_name(TR.get('All files', 'All files'))
        filter_all.add_pattern('*')
        dialog.add_filter(filter_all)
        
        # Directorio inicial
        if os.path.exists('/usr/share/pixmaps'):
            dialog.set_current_folder('/usr/share/pixmaps')
        elif os.path.exists('/usr/share/icons'):
            dialog.set_current_folder('/usr/share/icons')
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            selected_file = dialog.get_filename()
            entry.set_text(selected_file)
        
        dialog.destroy()
    
    def on_open_file_manager_clicked(self, button):
        """Abrir el gestor de archivos del sistema"""
        # Detectar gestor de archivos disponible
        file_managers = ['rox', 'pcmanfm', 'thunar', 'nautilus', 'dolphin', 'nemo']
        
        for fm in file_managers:
            try:
                subprocess.Popen([fm], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"✅ Opening {fm}")
                return
            except FileNotFoundError:
                continue
        
        # Si ninguno funciona, intentar con xdg-open
        try:
            subprocess.Popen(['xdg-open', os.path.expanduser('~')], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"❌ Could not open file manager: {e}")       
    
    def on_browse_directory(self, button, entry):
        """Abrir selector de directorio"""
        dialog = Gtk.FileChooserDialog(
            title=TR.get('Select Directory', 'Select Directory'),
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            TR['Cancel'], Gtk.ResponseType.CANCEL,
            TR['Select'], Gtk.ResponseType.OK
        )
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            entry.set_text(dialog.get_filename())
        
        dialog.destroy()
        
    def on_tint2_toggled(self, checkbox):
        """Manejar el toggle del checkbox de Tint2"""
        if 'tray' not in self.config:
            self.config['tray'] = {}
        self.config['tray']['use_tint2'] = checkbox.get_active()
        self.config_manager.save_config(self.config)
        self.update_tray_widgets_sensitivity()
    
    def update_tray_widgets_sensitivity(self):
        """Actualizar la sensibilidad de los widgets según el checkbox de Tint2"""
        use_tint2 = self.config.get('tray', {}).get('use_tint2', False)
        
        # Si usa Tint2, deshabilitar JWM y viceversa
        self.jwm_label.set_sensitive(not use_tint2)
        self.entry_jwmrc_tray.set_sensitive(not use_tint2)
        self.tint2_label.set_sensitive(use_tint2)
        self.entry_tint2rc.set_sensitive(use_tint2)   
        
    def create_categories_tab(self):
        """Crear tab para excluir categorías"""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_border_width(10)
    
        # Título descriptivo
        label = Gtk.Label(label=TR['Select categories to hide from menu'])
        label.set_halign(Gtk.Align.START)
        main_box.pack_start(label, False, False, 0)
    
        # Contenedor con scroll para los checkboxes
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_size_request(-1, 300)
    
        # con un espacio entre columnas de 10 píxeles.
        checkbox_grid = Gtk.Grid(row_spacing=6, column_spacing=100)
        checkbox_grid.set_border_width(10)
    
        # Lista de todas las categorías disponibles
        available_categories = [
            'Desktop', 'System', 'Setup', 'Utility', 'Filesystem', 
            'Graphic', 'Document', 'Business', 'Personal', 
            'Network', 'Internet', 'Multimedia', 'Fun', 'Help', 'Rectify', 'Shutdown',
             'Leave'
        ]

        self.category_checkboxes = {}
        excluded_list = self.config.get('categories', {}).get('excluded', [])
            
        for i, category in enumerate(available_categories):
            translated_name = TR.get(category, category)
                       
            # Create the label widget
            cat_label = Gtk.Label(label=translated_name)
            cat_label.set_halign(Gtk.Align.START) 
            
            # Create the checkbox
            checkbox = Gtk.CheckButton()
            checkbox.set_active(category in excluded_list)
            checkbox.connect("toggled", self.on_category_checkbox_toggled, category)
            
            checkbox_grid.attach(cat_label, 0, i, 1, 1)
            checkbox_grid.attach(checkbox, 1, i, 1, 1)
        
            self.category_checkboxes[category] = checkbox
    
        scrolled.add(checkbox_grid)
        main_box.pack_start(scrolled, True, True, 0)
    
        return main_box
    
    def on_category_checkbox_toggled(self, checkbox, category):
        """Manejar cambios en checkboxes de categorías"""
        if 'categories' not in self.config:
            self.config['categories'] = {'excluded': []}
        
        excluded_list = self.config['categories']['excluded']
        
        if checkbox.get_active():

            if category not in excluded_list:
                excluded_list.append(category)
        else:

            if category in excluded_list:
                excluded_list.remove(category)
        

        self.config_manager.save_config(self.config)       
            
    def on_spin_button_changed(self, spin_button, category, key):
        self.config[category][key] = int(spin_button.get_value())
        self.config_manager.save_config(self.config)
        
    def on_combo_changed(self, combo, category, key):
        selected_text = combo.get_active_text()

        # TranslationManager no es un dict y no tiene .items().
        # Usamos el diccionario interno de traducciones para evitar que
        # pymenu-config.py falle al cambiar opciones de ComboBox.
        translations = getattr(TR, "translations", {})
        for k, v in translations.items():
            if v == selected_text:
                self.config[category][key] = k
                break
        else:
            self.config[category][key] = selected_text

        self.config_manager.save_config(self.config)        

    def on_path_changed(self, entry, category, key):
        self.config[category][key] = entry.get_text()
        self.config_manager.save_config(self.config)

    def on_color_set(self, color_button, category, key):
        # --- INICIO DEL CAMBIO 2 ---
        rgba = color_button.get_rgba()
        keys_for_hex_only = ["text_header_os", "text_header_kernel", "text_header_hostname", "text_normal"]


        if key in keys_for_hex_only:
            self.config[category][key] = self.rgba_to_hex(rgba)

        else:
            self.config[category][key] = self.rgba_to_string(rgba)
        # --- FIN DEL CAMBIO 2 ---
        self.config_manager.save_config(self.config)

    def on_font_set(self, font_button, category, key):
        self.config[category][key] = font_button.get_font()
        self.config_manager.save_config(self.config)
        
    def on_checkbox_toggled(self, button, category, key):
        self.config[category][key] = button.get_active()    
        self.config_manager.save_config(self.config)
        
    def on_save_only_clicked(self, button):
        self.config_manager.save_config(self.config)
        print(TR['Config saved (without closing).'])
    
    def on_exit_clicked(self, button):
        Gtk.main_quit()

    def hex_to_rgba(self, hex_or_rgba_string):
        rgba = Gdk.RGBA()
        try:
            rgba.parse(hex_or_rgba_string)
            return rgba
        except ValueError:
            return None
    
    def rgba_to_string(self, rgba):
        r = int(rgba.red * 255)
        g = int(rgba.green * 255)
        b = int(rgba.blue * 255)
        return f"rgba({r}, {g}, {b}, {rgba.alpha:.2f})"


    def rgba_to_hex(self, rgba):
        r = int(rgba.red * 255)
        g = int(rgba.green * 255)
        b = int(rgba.blue * 255)
        return f"#{r:02x}{g:02x}{b:02x}"
    # --- FIN DEL CAMBIO 3 ---

def main():
    try:
        win = ConfigWindow()
        win.show_all()
        Gtk.main()
    except Exception as e:
        print(f"{TR['An error occurred:']} {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
