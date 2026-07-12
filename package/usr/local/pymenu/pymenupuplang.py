#!/usr/bin/env python3
"""
Sistema de traducción simple para Essora PyMenu / PyMenuPup
Archivo: /usr/local/bin/pymenupuplang.py

Los archivos .lang se buscan en:
1. ~/.config/essorawm/locale/ (usuario)
2. /usr/local/pymenu/locale/ (instalación local)
3. /usr/share/locale/pymenu/ (sistema)
"""

import os
import locale

class TranslationManager:
    """Gestor de traducciones basado en archivos .lang simples"""
    
    # Rutas donde buscar archivos de traducción (en orden de prioridad)
    LOCALE_PATHS = [
        os.path.expanduser("~/.config/essorawm/locale"),  # Usuario local (mayor prioridad)
        "/usr/local/pymenu/locale",                     # Instalación de Essora
        "/usr/share/locale/pymenu",                     # Sistema (opcional)
    ]
        
# Traducciones por defecto en inglés (fallback)
    DEFAULT_TRANSLATIONS = {
        'PyMenuPup Configurator': 'PyMenuPup Configurator',
        'Window': 'Window',
        'Colors': 'Colors',
        'Font': 'Font',
        'Paths': 'Paths',
        'Save': 'Save',
        'Exit': 'Exit',
        'Config file not found. Creating default config.': 'Config file not found. Creating default config.',
        'Error loading config file:': 'Error loading config file:',
        'Using default config.': 'Using default config.',
        'Window width:': 'Window width:',
        'Window height:': 'Window height:',
        'Icon size:': 'Icon size:',
        'Category icon size:': 'Category icon size:',
        'Profile pic shape:': 'Profile pic shape:',
        'square': 'Square',
        'circular': 'Circular',
        'Profile pic size:': 'Profile pic size:',
        'Show window frame:': 'Show window frame:',
        '(No transparency)': '(No transparency)',
        'Hide header:': 'Hide header:',
        'Hide profile picture:': 'Hide profile picture:',
        'Hide quick access:': 'Hide quick access:',
        'Hide social networks:': 'Hide social networks:',
        'Hide categories text:': 'Hide categories text:',
        'Hide app names:': 'Hide app names:',
        'Horizontal alignment:': 'Horizontal alignment:',
        'Search bar position:': 'Search bar position:',
        'top': 'Top',
        'bottom': 'Bottom',
        'center': 'center',
        'left': 'left',
        'right': 'right',
        'Background color:': 'Background color:',
        'Border color:': 'Border color:',
        'Text normal:': 'Normal text:',
        'Header (OS):': 'Header (OS):',
        'Header (Kernel):': 'Header (Kernel):',
        'Header (Hostname):': 'Header (Hostname):',
        'Hover background:': 'Hover background:',
        'Button background:': 'Button background:',
        'Button text:': 'Button text:',
        'Font family:': 'Font family:',
        'Category font:': 'Category font:',
        'Category size:': 'Category size:',
        'App name size:': 'App name size:',
        'Header size:': 'Header size:',
        'Profile pic path:': 'Profile pic path:',
        'Profile manager:': 'Profile manager:',
        'Shutdown command:': 'Shutdown command:',
        'JWM Tray config:': 'JWM Tray config:',
        'Tint2 config:': 'Tint2 config:',
        'Use Tint2 (instead of JWM):': 'Use Tint2 (instead of JWM):',
        'Config saved (without closing).': 'Config saved (without closing).',
        'An error occurred:': 'An error occurred:',
        'Categories': 'Categories',
        'Excluded categories:': 'Excluded categories:',
        'Select categories to hide from menu': 'Select categories to hide from menu',
        'Header layout:': 'Header layout:',
        'Header text alignment:': 'Header text alignment:',
        'Avatar left': 'Avatar left',
        'Avatar right': 'Avatar right',
        'Avatar center': 'Avatar center',
        'Use system theme:': 'Use system theme:',
        'Hide OS name:': 'Hide OS name:',
        'Hide kernel:': 'Hide kernel:',
        'Hide hostname:': 'Hide hostname:',
        'Categories background:': 'Categories background:',
        'Desktop': 'Desktop',
        'System': 'System',
        'Setup': 'Setup',
        'Utility': 'Utility',
        'Filesystem': 'Filesystem',
        'Graphic': 'Graphic',
        'Document': 'Document',
        'Business': 'Business',
        'Personal': 'Personal',
        'Network': 'Network',
        'Internet': 'Internet',
        'Multimedia': 'Multimedia',
        'Fun': 'Fun',
        'Help': 'Help',
        'Rectify': 'Rectify',
        'Shutdown': 'Shutdown',
        'Leave': 'Leave',
        'Cancel': 'Cancel',
        'Select': 'Select',
        'Select profile picture': 'Select profile picture',
        'Select profile manager': 'Select profile manager',
        'Select shutdown command': 'Select shutdown command',
        'Select JWM config': 'Select JWM config',
        'Select Tint2 config': 'Select Tint2 config',
        'Search engine:': 'Search engine:',
        'Loading translations from:': 'Loading translations from:',
        'Category map built with': 'Category map built with',
        'entries': 'entries',
        'Window Manager detected:': 'Window Manager detected:',
        'Using user config': 'Using user config',
        'Automatically using Tint2 config': 'Automatically using Tint2 config',
        'Tray config detected from': 'Tray config detected from:',
        'Now monitoring JWM file for changes:': 'Now monitoring JWM file for changes:',
        'Folder created:': 'Folder created:',
        'Error creating folder': 'Error creating folder',
        'Mouse entered applications area': 'Mouse entered applications area',
        'Using GTK theme colors': 'Using GTK theme colors',
        'ERROR: Could not load pymenupuplang.py': 'ERROR: Could not load pymenupuplang.py',
        'Config file not found. Creating default config.': 'Config file not found. Creating default config.',
        'Error loading config file:': 'Error loading config file:',
        'Using default config.': 'Using default config.',
        'Config saved (without closing).': 'Config saved (without closing).',
        'An error occurred:': 'An error occurred:',
        'PyMenu Configurator': 'PyMenu Configurator',
        
        # AÑADIDAS LAS NUEVAS TRADUCCIONES:
        'Favorites': 'Favorites',
        'Add favorite': 'Add favorite',
        'No favorites yet. Click here to add one.': 'No favorites yet. Click here to add one.',
        'Add Favorite': 'Add Favorite',
        'Add': 'Add',
        'Select an application:': 'Select an application:',
        'Search applications...': 'Search applications...',
        'Application': 'Application',
        'Select a directory:': 'Select a directory:',
        'Path to directory': 'Path to directory',
        'Browse...': 'Browse...',
        'Directory': 'Directory',
        'Name:': 'Name:',
        'Favorite name': 'Favorite name',
        'Command:': 'Command:',
        'Command to execute': 'Command to execute',
        'Icon (optional):': 'Icon (optional):',
        'Icon name or path': 'Icon name or path',
        'Browse icon': 'Browse icon',
        'Open File Manager': 'Open File Manager',
        'Command': 'Command',
        'Select Directory': 'Select Directory',
        'Select Icon': 'Select Icon',
        'Image files': 'Image files',
        'All files': 'All files',
        
        # NUEVAS OPCIONES DEL MENÚ
        'Hide places sidebar:': 'Hide places sidebar:',
        '(Hides both places and favorites)': '(Hides both places and favorites)',
        'Hide favorites only:': 'Hide favorites only:',
        '(Show places but hide favorites)': '(Show places but hide favorites)',
        'Show profile in places sidebar:': 'Show profile in places sidebar:',
        '(Instead of header)': '(Instead of header)',
        
        # AGREGAR ESTAS NUEVAS CLAVES DE ESSORA:
        'Search applications...': 'Search applications...',
        'Shutdown': 'Shutdown',
        'Search in the web': 'Search in the web',
        'Pymenu config': 'Pymenu config',
        'Select avatar': 'Select avatar',
        'Run': 'Run',
        'Create desktop shortcut': 'Create desktop shortcut',
        
        # Categorías adicionales de Essora
        'Favorites': 'Favorites',
        'Accessories': 'Accessories',
        'Office': 'Office',
        'Applications': 'Applications',
        'Graphics': 'Graphics',        
    }
    
    def __init__(self):
        self.translations = self.DEFAULT_TRANSLATIONS.copy()
        self.current_lang = self._detect_system_language()
        self._load_translations()
        self.category_map = self._build_category_map()
    
    def _build_category_map(self):
        """
        Construye un mapa de categorías traducidas a sus nombres estándar en inglés.
        Esto permite que el sistema reconozca categorías del JWM en cualquier idioma.
        """
        # Categorías estándar que necesitan mapeo
        standard_categories = [
            'Desktop', 'System', 'Setup', 'Utility', 'Filesystem',
            'Graphic', 'Document', 'Business', 'Personal', 'Network',
            'Internet', 'Multimedia', 'Fun', 'Help', 'Rectify', 
            'Shutdown', 'Leave'
        ]
        
        category_map = {}
        
        # Agregar mapeo de inglés a inglés (identidad)
        for cat in standard_categories:
            category_map[cat] = cat
        
        # Buscar traducciones en todos los archivos .lang disponibles
        for locale_path in self.LOCALE_PATHS:
            if not os.path.exists(locale_path):
                continue
            
            try:
                for filename in os.listdir(locale_path):
                    if not filename.endswith('.lang'):
                        continue
                    
                    filepath = os.path.join(locale_path, filename)
                    file_translations = self._parse_lang_file(filepath)
                    
                    # Para cada categoría estándar, agregar su traducción al mapa
                    for standard_cat in standard_categories:
                        translated_cat = file_translations.get(standard_cat)
                        if translated_cat and translated_cat != standard_cat:
                            category_map[translated_cat] = standard_cat
            except Exception as e:
                print(f"⚠️  Error construyendo category_map desde {locale_path}: {e}")
        
        print(f"✓ Category map construido con {len(category_map)} entradas")
        return category_map
    
    def get_category_map(self):
        """Retorna el mapa de categorías traducidas"""
        return self.category_map
    
    def _detect_system_language(self):
        """Detecta el idioma del sistema"""
        try:
            sys_locale = locale.getlocale()
            if sys_locale[0]:
                # Obtiene código completo (ej: es_MX -> es-MX)
                lang_code = sys_locale[0].replace('_', '-')
                return lang_code
        except:
            pass
        return 'en'
    
    def _find_lang_file(self, lang_code):
        """Busca el archivo .lang en las rutas configuradas"""
        # Primero intenta con el código completo (ej: es-MX.lang)
        for base_path in self.LOCALE_PATHS:
            full_path = os.path.join(base_path, f"{lang_code}.lang")
            if os.path.exists(full_path):
                return full_path
        
        # Si no encuentra, intenta solo con el idioma base (ej: es.lang)
        if '-' in lang_code:
            base_lang = lang_code.split('-')[0]
            for base_path in self.LOCALE_PATHS:
                full_path = os.path.join(base_path, f"{base_lang}.lang")
                if os.path.exists(full_path):
                    return full_path
        
        return None
    
    def _parse_lang_file(self, filepath):
        """
        Lee un archivo .lang y retorna un diccionario
        Formato: clave = valor
        Soporta comentarios con # y líneas vacías
        """
        translations = {}
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Ignorar líneas vacías y comentarios
                    if not line or line.startswith('#'):
                        continue
                    
                    # Buscar el separador =
                    if '=' not in line:
                        print(f"⚠️  Línea {line_num} ignorada (sin '='): {line}")
                        continue
                    
                    # Separar clave y valor
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key and value:
                        translations[key] = value
                    
        except Exception as e:
            print(f"⚠️  Error leyendo archivo de traducción {filepath}: {e}")
        
        return translations
    
    def _load_translations(self):
        """Carga las traducciones para el idioma actual"""
        lang_file = self._find_lang_file(self.current_lang)
        
        if lang_file:
            print(f"✓ Cargando traducciones desde: {lang_file}")
            loaded_translations = self._parse_lang_file(lang_file)
            # Actualiza solo las claves que existen en el archivo
            self.translations.update(loaded_translations)
        else:
            # Si no encuentra archivo, intenta solo con el idioma base
            base_lang = self.current_lang.split('-')[0] if '-' in self.current_lang else self.current_lang
            if base_lang != 'en':
                print(f"⚠️  No se encontró archivo de traducción para '{self.current_lang}'")
                print(f"   Buscado en: {', '.join(self.LOCALE_PATHS)}")
                print(f"   Usando traducciones por defecto (inglés)")
    
    def get(self, key, default=None):
        """Obtiene una traducción por clave"""
        return self.translations.get(key, default or key)

    # Compatibilidad: permite usar TR.items(), TR.keys() y TR.values()
    # como si TranslationManager fuera un diccionario.
    def items(self):
        return self.translations.items()

    def keys(self):
        return self.translations.keys()

    def values(self):
        return self.translations.values()
    
    def __getitem__(self, key):
        """Permite usar TR['clave'] como antes"""
        return self.get(key)


# Para testing
if __name__ == "__main__":
    TR = TranslationManager()
    print(f"Idioma detectado: {TR.current_lang}")
    print(f"Ejemplo: {TR['PyMenuPup Configurator']}")
