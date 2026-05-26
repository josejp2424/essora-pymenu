#!/usr/bin/env python3
"""
Wine Desktop Creator - Generador de archivos .desktop para aplicaciones Wine

Editado por: josejp2424
Motivo: Automatizar la creación de archivos .desktop para aplicaciones Windows
        instaladas en Wine. Busca en todas las carpetas .wine* de los usuarios,
        detecta ejecutables .exe, prioriza versiones 64-bit, y crea los .desktop
        con el icono correcto y la categoría Wine.

Uso:
    # Como usuario normal (crea en ~/.local/share/applications)
    python3 wine-desktop-creator.py
    
    # Como root (crea en /usr/share/applications y busca en todos los usuarios)
    sudo python3 wine-desktop-creator.py
"""

import os
import sys
import re
from pathlib import Path

# Configuración
WINE_ICON = "/usr/local/pymenu/icon-pymenu/preferences-wine-essora.svg"
EXCLUDED_DIRS = ["Common Files", "Internet Explorer", "Windows NT", "WindowsApps"]


class WineDesktopCreator:
    """
    Crea archivos .desktop para aplicaciones Wine
    Editado por: josejp2424
    """
    
    def __init__(self):
        self.is_root = os.geteuid() == 0
        self.desktop_dir = self._get_desktop_directory()
        self.created_count = 0
        self.skipped_count = 0
        self.error_count = 0
        
        print("=" * 70)
        print("WINE DESKTOP CREATOR")
        print("Editado por: josejp2424")
        print("=" * 70)
        print(f"Ejecutando como: {'ROOT' if self.is_root else 'USUARIO'}")
        print(f"Directorio destino: {self.desktop_dir}")
        print()
    
    def _get_desktop_directory(self):
        """Determina dónde crear los archivos .desktop"""
        if self.is_root:

            return "/usr/share/applications"
        else:

            return os.path.expanduser("~/.local/share/applications")
    
    def _get_users_home_dirs(self):
        """Obtiene lista de directorios home de usuarios"""
        if self.is_root:

            home_dirs = []
            try:
                for entry in os.listdir("/home"):
                    user_home = os.path.join("/home", entry)
                    if os.path.isdir(user_home):
                        home_dirs.append(user_home)
            except Exception as e:
                print(f" Error listando /home: {e}")
            
            if not home_dirs:
                print(" No se encontraron usuarios en /home")
            
            return home_dirs
        else:

            return [os.path.expanduser("~")]
    
    def _find_wine_directories(self, home_dir):
        """Encuentra carpetas .wine* en el directorio home"""
        wine_dirs = []
        
        try:
            for entry in os.listdir(home_dir):
                if entry.startswith('.wine'):
                    wine_path = os.path.join(home_dir, entry)
                    if os.path.isdir(wine_path):
                        wine_dirs.append(wine_path)
        except Exception as e:
            print(f"Error buscando en {home_dir}: {e}")
        
        return wine_dirs
    
    def _find_program_files(self, wine_dir):
        """Encuentra el directorio Program Files en una carpeta Wine"""
        possible_paths = [
            os.path.join(wine_dir, "drive_c", "Program Files"),
            os.path.join(wine_dir, "drive_c", "Program Files (x86)"),
        ]
        
        program_dirs = []
        for path in possible_paths:
            if os.path.exists(path) and os.path.isdir(path):
                program_dirs.append(path)
        
        return program_dirs
    
    def _should_skip_directory(self, dir_name):
        """Verifica si un directorio debe ser omitido"""
        return dir_name in EXCLUDED_DIRS
    
    def _find_exe_files(self, directory):
        """Encuentra archivos .exe en un directorio, priorizando 64-bit"""
        exe_files = {}
        
        try:
            for entry in os.listdir(directory):
                if entry.lower().endswith('.exe'):
                    exe_path = os.path.join(directory, entry)
                    

                    base_name = entry[:-4]  
                    

                    is_64bit = '64' in base_name.lower()
                    

                    normalized_name = re.sub(r'64$', '', base_name, flags=re.IGNORECASE)
                    
               
                    if normalized_name in exe_files:
                        existing = exe_files[normalized_name]
                      
                        if is_64bit and not existing['is_64bit']:
                            exe_files[normalized_name] = {
                                'path': exe_path,
                                'name': entry,
                                'is_64bit': is_64bit,
                                'base_name': base_name
                            }
                    else:
                        exe_files[normalized_name] = {
                            'path': exe_path,
                            'name': entry,
                            'is_64bit': is_64bit,
                            'base_name': base_name
                        }
        
        except Exception as e:
            print(f"Error listando {directory}: {e}")
        
        return list(exe_files.values())
    
    def _sanitize_desktop_filename(self, name):
        """Convierte un nombre de exe en un nombre válido para .desktop"""
  
        name = re.sub(r'\.exe$', '', name, flags=re.IGNORECASE)
        
        name = re.sub(r'[^\w\-]', '_', name)
        
        return f"wine-{name}.desktop"
    
    def _desktop_exists(self, desktop_filename):
        """Verifica si un archivo .desktop ya existe"""
        desktop_path = os.path.join(self.desktop_dir, desktop_filename)
        return os.path.exists(desktop_path)
    
    def _get_wine_command(self, wine_dir):
        """Determina el comando Wine correcto según el directorio"""
        wine_dir_name = os.path.basename(wine_dir)
        
        if 'appimage' in wine_dir_name.lower():
   
            return "wine"  
        elif 'stable' in wine_dir_name.lower():
            return "wine-stable"
        elif 'staging' in wine_dir_name.lower():
            return "wine-staging"
        else:
            return "wine"
    
    def _create_desktop_file(self, exe_info, wine_dir, program_folder):
        """Crea un archivo .desktop para una aplicación Wine"""
        

        desktop_filename = self._sanitize_desktop_filename(exe_info['base_name'])
        
        if self._desktop_exists(desktop_filename):
            print(f"OMITIDO: {exe_info['base_name']} (ya existe)")
            self.skipped_count += 1
            return False
        
       
        app_name = exe_info['base_name']
        exe_path = exe_info['path']
        wine_cmd = self._get_wine_command(wine_dir)
        

        exec_command = f'env WINEPREFIX="{wine_dir}" {wine_cmd} "{exe_path}"'
        

        desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name={app_name}
Comment=Windows application via Wine
Exec={exec_command}
Icon={WINE_ICON}
Categories=Wine;
Terminal=false
StartupNotify=true
"""
        

        os.makedirs(self.desktop_dir, exist_ok=True)
        
        
        desktop_path = os.path.join(self.desktop_dir, desktop_filename)
        
        try:
            with open(desktop_path, 'w', encoding='utf-8') as f:
                f.write(desktop_content)
            
   
            os.chmod(desktop_path, 0o755)
            
            bit_info = "64-bit" if exe_info['is_64bit'] else "32-bit"
            print(f"CREADO: {app_name} ({bit_info})")
            print(f"   Wine: {os.path.basename(wine_dir)}")
            print(f"   Folder: {os.path.basename(program_folder)}")
            print(f"   File: {desktop_filename}")
            print()
            
            self.created_count += 1
            return True
            
        except Exception as e:
            print(f"ERROR creando {desktop_filename}: {e}")
            self.error_count += 1
            return False
    
    def scan_and_create(self):
        """Proceso principal: escanear y crear archivos .desktop"""
        
  
        home_dirs = self._get_users_home_dirs()
        
        if not home_dirs:
            print(" No se encontraron directorios de usuario para escanear")
            return
        
        print(f"🔍 Escaneando {len(home_dirs)} directorio(s) de usuario...")
        print()
        
        for home_dir in home_dirs:
            username = os.path.basename(home_dir)
            print(f"Usuario: {username}")
            print(f"Home: {home_dir}")
            
            # Buscar carpetas .wine*
            wine_dirs = self._find_wine_directories(home_dir)
            
            if not wine_dirs:
                print(f" No se encontraron carpetas Wine")
                print()
                continue
            
            print(f"   🍷 Encontradas {len(wine_dirs)} carpeta(s) Wine:")
            for wine_dir in wine_dirs:
                print(f"      • {os.path.basename(wine_dir)}")
            print()
            
            # Procesar cada carpeta Wine
            for wine_dir in wine_dirs:
                wine_name = os.path.basename(wine_dir)
                print(f"   🔍 Explorando: {wine_name}")
                

                program_dirs = self._find_program_files(wine_dir)
                
                if not program_dirs:
                    print(f"       No se encontró 'Program Files'")
                    continue
                

                for program_files_dir in program_dirs:
                    program_files_name = os.path.basename(program_files_dir)
                    print(f"      {program_files_name}")
                    
                    try:
             
                        for folder in os.listdir(program_files_dir):
                            folder_path = os.path.join(program_files_dir, folder)
                            
                     
                            if not os.path.isdir(folder_path):
                                continue
                            
                     
                            if self._should_skip_directory(folder):
                                continue
                            
                            # Buscar archivos .exe
                            exe_files = self._find_exe_files(folder_path)
                            
                            if exe_files:
                                print(f"         {folder} ({len(exe_files)} exe)")
                                
                                for exe_info in exe_files:
                                    self._create_desktop_file(exe_info, wine_dir, folder)
                    
                    except Exception as e:
                        print(f"       Error: {e}")
                
                print()
    
    def print_summary(self):
        """Muestra resumen de la operación"""
        print("=" * 70)
        print("RESUMEN")
        print("=" * 70)
        print(f" Archivos creados: {self.created_count}")
        print(f"  Archivos omitidos (ya existen): {self.skipped_count}")
        
        if self.error_count > 0:
            print(f" Errores: {self.error_count}")
        
        print()
        
        if self.created_count > 0:
            print(f" Los archivos .desktop se crearon en:")
            print(f"   {self.desktop_dir}")
            print()
            print("   Para ver las aplicaciones en Pymenu:")
            print("   1. Cierra Pymenu si está abierto")
            print("   2. Abre Pymenu nuevamente")
            print("   3. Busca la categoría 'Wine'")
        
        print("=" * 70)


def main():
    """Función principal"""
    
  
    if not os.path.exists(WINE_ICON):
        print("  ADVERTENCIA: No se encuentra el icono de Wine:")
        print(f"   {WINE_ICON}")
        print()
        print("   Los archivos .desktop se crearán de todas formas,")
        print("   pero mostrarán un icono genérico.")
        print()
        response = input("¿Continuar? (s/n): ").lower()
        if response != 's':
            print("Operación cancelada.")
            sys.exit(0)
        print()
    
    # Crear instancia y ejecutar
    creator = WineDesktopCreator()
    
    try:
        creator.scan_and_create()
    except KeyboardInterrupt:
        print()
        print(" Operación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print()
        print(f"Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Mostrar resumen
    creator.print_summary()


if __name__ == "__main__":
    main()
