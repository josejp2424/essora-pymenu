#!/usr/bin/env python3
# autor original nilsonmorales
#configuraciones para essora por josejp2424
#traducciones por josejp2424.
import gi
import os
import subprocess
import shutil
import locale

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib

FACE_PATH = os.path.expanduser("~/.config/essorawm/face")
HOSTNAME_PATH = "/etc/hostname"
DEFAULT_ICON = "/usr/share/icons/essora.png"


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


active_notifications = []

# === 🌐 Diccionario de Traducción ===

LANG = {
    'en': {
        'Profile Manager': 'Profile Manager',
        'Error: ImageMagick not installed.': 'Error: ImageMagick not installed.',
        'Change Picture': 'Change Picture',
        'Change Name': 'Change Name',
        'Hostname': 'Hostname',
        'Select Image': 'Select Image',
        'Images': 'Images',
        'Profile picture updated': 'Profile picture updated',
        'Change Hostname': 'Change Hostname',
        'New name:': 'New name:',
        'Cancel': 'Cancel',
        'Apply': 'Apply',
        'Hostname changed to': 'Hostname changed to',
    },
    'es': {
        'Profile Manager': 'Gestor de Perfil',
        'Error: ImageMagick not installed.': 'Error: ImageMagick no está instalado.',
        'Change Picture': 'Cambiar Foto',
        'Change Name': 'Cambiar Nombre',
        'Hostname': 'Nombre de Host',
        'Select Image': 'Seleccionar Imagen',
        'Images': 'Imágenes',
        'Profile picture updated': 'Foto de perfil actualizada',
        'Change Hostname': 'Cambiar Nombre de Host',
        'New name:': 'Nuevo nombre:',
        'Cancel': 'Cancelar',
        'Apply': 'Aplicar',
        'Hostname changed to': 'Nombre de host cambiado a',
    },
    'ca': {
        'Profile Manager': 'Gestor de Perfil',
        'Error: ImageMagick not installed.': "Error: ImageMagick no està instal·lat.",
        'Change Picture': 'Canviar Foto',
        'Change Name': 'Canviar Nom',
        'Hostname': "Nom d'amfitrió",
        'Select Image': 'Seleccionar Imatge',
        'Images': 'Imatges',
        'Profile picture updated': 'Foto de perfil actualitzada',
        'Change Hostname': "Canviar nom d'amfitrió",
        'New name:': 'Nom nou:',
        'Cancel': 'Cancel·lar',
        'Apply': 'Aplicar',
        'Hostname changed to': "Nom d'amfitrió canviat a",
    },
    'fr': {
        'Profile Manager': 'Gestionnaire de Profil',
        'Error: ImageMagick not installed.': "Erreur : ImageMagick n'est pas installé.",
        'Change Picture': 'Changer la photo',
        'Change Name': 'Changer le nom',
        'Hostname': "Nom d’hôte",
        'Select Image': "Sélectionner l’image",
        'Images': 'Images',
        'Profile picture updated': 'Photo de profil mise à jour',
        'Change Hostname': "Changer le nom d’hôte",
        'New name:': 'Nouveau nom :',
        'Cancel': 'Annuler',
        'Apply': 'Appliquer',
        'Hostname changed to': "Nom d’hôte changé en",
    },
    'it': {
        'Profile Manager': 'Gestore Profilo',
        'Error: ImageMagick not installed.': 'Errore: ImageMagick non è installato.',
        'Change Picture': 'Cambia Foto',
        'Change Name': 'Cambia Nome',
        'Hostname': 'Nome host',
        'Select Image': 'Seleziona Immagine',
        'Images': 'Immagini',
        'Profile picture updated': 'Foto profilo aggiornata',
        'Change Hostname': 'Cambia nome host',
        'New name:': 'Nuovo nome:',
        'Cancel': 'Annulla',
        'Apply': 'Applica',
        'Hostname changed to': "Nome host cambiato in",
    },
    'pt': {
        'Profile Manager': 'Gerenciador de Perfil',
        'Error: ImageMagick not installed.': 'Erro: ImageMagick não está instalado.',
        'Change Picture': 'Alterar Foto',
        'Change Name': 'Alterar Nome',
        'Hostname': 'Nome do host',
        'Select Image': 'Selecionar Imagem',
        'Images': 'Imagens',
        'Profile picture updated': 'Foto de perfil atualizada',
        'Change Hostname': 'Alterar nome do host',
        'New name:': 'Novo nome:',
        'Cancel': 'Cancelar',
        'Apply': 'Aplicar',
        'Hostname changed to': 'Nome do host alterado para',
    },
    'hu': {
        'Profile Manager': 'Profilkezelő',
        'Error: ImageMagick not installed.': 'Hiba: az ImageMagick nincs telepítve.',
        'Change Picture': 'Kép cseréje',
        'Change Name': 'Név módosítása',
        'Hostname': 'Gépnév',
        'Select Image': 'Kép kiválasztása',
        'Images': 'Képek',
        'Profile picture updated': 'Profilkép frissítve',
        'Change Hostname': 'Gépnév módosítása',
        'New name:': 'Új név:',
        'Cancel': 'Mégse',
        'Apply': 'Alkalmaz',
        'Hostname changed to': 'Gépnév módosítva erre:',
    },
    'ru': {
        'Profile Manager': 'Менеджер профиля',
        'Error: ImageMagick not installed.': 'Ошибка: ImageMagick не установлен.',
        'Change Picture': 'Изменить фото',
        'Change Name': 'Изменить имя',
        'Hostname': 'Имя хоста',
        'Select Image': 'Выбрать изображение',
        'Images': 'Изображения',
        'Profile picture updated': 'Фото профиля обновлено',
        'Change Hostname': 'Изменить имя хоста',
        'New name:': 'Новое имя:',
        'Cancel': 'Отмена',
        'Apply': 'Применить',
        'Hostname changed to': 'Имя хоста изменено на',
    },
    'zh': {
        'Profile Manager': '个人资料管理器',
        'Error: ImageMagick not installed.': '错误：未安装 ImageMagick。',
        'Change Picture': '更改照片',
        'Change Name': '更改名称',
        'Hostname': '主机名',
        'Select Image': '选择图片',
        'Images': '图片',
        'Profile picture updated': '个人资料图片已更新',
        'Change Hostname': '更改主机名',
        'New name:': '新名称：',
        'Cancel': '取消',
        'Apply': '应用',
        'Hostname changed to': '主机名已更改为',
    },
    'ar': {
        'Profile Manager': 'مدير الملف الشخصي',
        'Error: ImageMagick not installed.': 'خطأ: ImageMagick غير مثبت.',
        'Change Picture': 'تغيير الصورة',
        'Change Name': 'تغيير الاسم',
        'Hostname': 'اسم المضيف',
        'Select Image': 'اختر صورة',
        'Images': 'صور',
        'Profile picture updated': 'تم تحديث صورة الملف الشخصي',
        'Change Hostname': 'تغيير اسم المضيف',
        'New name:': 'اسم جديد:',
        'Cancel': 'إلغاء',
        'Apply': 'تطبيق',
        'Hostname changed to': 'تم تغيير اسم المضيف إلى',
    },
}


# === 🌐 Detectar idioma del sistema ===

def get_translation_texts():
    
    try:
        import os, locale
        for var in ("LC_ALL", "LANGUAGE", "LANG"):
            val = os.environ.get(var, "")
            if val:
                code = val.split('.')[0].split('@')[0].split('_')[0].lower()
                if code in LANG:
                    return LANG[code]
        # Fallback to locale
        sys_locale = locale.getlocale()
        lang_code = sys_locale[0].split('_')[0] if sys_locale and sys_locale[0] else 'en'
        return LANG.get(lang_code, LANG['en'])
    except Exception:
        return LANG['en']

TR = get_translation_texts()


def safe_run(command):
    try:
        if shutil.which(command[0]):
            subprocess.run(command, check=False)
    except Exception as e:
        print(f"Warning: Failed to run {' '.join(command)}: {e}")

def notify(icon_path, title, message, duration=3):
    display = Gdk.Display.get_default()
    monitor = display.get_primary_monitor()
    geometry = monitor.get_geometry()

    window = Gtk.Window(type=Gtk.WindowType.POPUP)
    window.set_decorated(False)
    window.set_keep_above(True)
    window.set_type_hint(Gdk.WindowTypeHint.NOTIFICATION)
    window.set_border_width(8)
    window.set_resizable(False)

    vbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    window.add(vbox)

    if os.path.exists(icon_path):
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(icon_path, 48, 48, True)
            img = Gtk.Image.new_from_pixbuf(pixbuf)
            vbox.pack_start(img, False, False, 0)
        except:
            pass

    text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
    lbl_title = Gtk.Label()
    lbl_title.set_markup(f"<b>{title}</b>")
    lbl_message = Gtk.Label(label=message)
    lbl_message.set_line_wrap(True)
    text_box.pack_start(lbl_title, False, False, 0)
    text_box.pack_start(lbl_message, False, False, 0)
    vbox.pack_start(text_box, True, True, 0)

    window.show_all()

    w, h = window.get_size()
    base_x = geometry.width - w - 20
    base_y = 20 + len(active_notifications) * (h + 10)
    window.move(base_x, base_y)
    active_notifications.append(window)

    gdk_window = window.get_window()
    if gdk_window:
        gdk_window.set_opacity(0.0)

    window._opacity = 0.0
    y_offset = -30

    def animate_in():
        if gdk_window and window._opacity < 1.0:
            window._opacity += 0.05
            y_offset_local = int(y_offset + window._opacity * 30)
            gdk_window.set_opacity(window._opacity)
            window.move(base_x, base_y + y_offset_local)
            return True
        return False

    GLib.timeout_add(20, animate_in)

    def animate_out():
        if getattr(window, "_closed", False):
            return False
        window._closed = True

        if gdk_window and window._opacity > 0.0:
            window._opacity -= 0.05
            gdk_window.set_opacity(window._opacity)
            return True

        window.destroy()
        if window in active_notifications:
            active_notifications.remove(window)
        return False

    GLib.timeout_add_seconds(duration, lambda: GLib.timeout_add(50, animate_out))

    return window



def get_display_icon_path():
    """Determina la mejor ruta para la imagen del ícono principal."""
    
    current_icon_path = ""
    
    if os.path.exists(FACE_PATH):
        try:
           
            if FACE_PATH.lower().endswith('.svg'):
                
                real_path = os.path.realpath(FACE_PATH)
                pixbuf_test = GdkPixbuf.Pixbuf.new_from_file_at_scale(real_path, 1, 1, True)
            else:
                pixbuf_test = GdkPixbuf.Pixbuf.new_from_file_at_scale(FACE_PATH, 1, 1, True)
            
            
            current_icon_path = FACE_PATH
        except gi.repository.GLib.GError as e:
            
            print(f"Error al cargar el ícono, eliminando archivo corrupto: {e}")
            try:
                os.remove(FACE_PATH)
            except OSError as ex:
                print(f"No se pudo eliminar el archivo: {ex}")
            current_icon_path = DEFAULT_ICON
    else:
        current_icon_path = DEFAULT_ICON

    return current_icon_path

ICON_PATH = get_display_icon_path()


if shutil.which("magick") is None:
    print(TR['Error: ImageMagick not installed.'])
    exit(1)


class ProfileManager(Gtk.Window):
    def __init__(self):
        super().__init__(title=TR['Profile Manager'])
        self.set_border_width(10)
        
        
        self.set_icon_from_file(ICON_PATH)

        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
            button {
                font-family: 'FiraCode Nerd Font', 'Hack Nerd Font', 'Nerd Font';
                font-size: 12pt;
            }
        """)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(vbox)

        
        self.image_widget = Gtk.Image.new_from_file(ICON_PATH)
        vbox.pack_start(self.image_widget, True, True, 0)

        with open(HOSTNAME_PATH) as f:
            hostname = f.read().strip()
        btn_hostname = Gtk.Button(label=f"  {TR['Hostname']}:\n {hostname}")
        vbox.pack_start(btn_hostname, False, False, 0)

        button_box = Gtk.ButtonBox(orientation=Gtk.Orientation.HORIZONTAL)
        button_box.set_layout(Gtk.ButtonBoxStyle.CENTER)

        btn_change_pic = Gtk.Button(label=f"{TR['Change Picture']}")
        btn_change_pic.connect("clicked", self.change_picture)
        button_box.add(btn_change_pic)

        btn_change_name = Gtk.Button(label=f"{TR['Change Name']}")
        btn_change_name.connect("clicked", self.change_name)
        button_box.add(btn_change_name)

        vbox.pack_start(button_box, True, True, 0)

    def change_picture(self, widget):
        dialog = Gtk.FileChooserDialog(title=TR['Select Image'], parent=self)
        dialog.set_action(Gtk.FileChooserAction.OPEN)
        dialog.set_default_size(500, 350)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                           Gtk.STOCK_OPEN, Gtk.ResponseType.OK)

        filter_image = Gtk.FileFilter()
        filter_image.set_name(TR['Images'])
        for ext in ["png", "jpg", "jpeg", "bmp", "tiff", "ico", "svg"]:
            filter_image.add_pattern(f"*.{ext}")
        dialog.add_filter(filter_image)

        preview = Gtk.Image()
        preview.set_size_request(128, 128)
        dialog.set_preview_widget(preview)

        def update_preview(file_chooser):
            filename = file_chooser.get_preview_filename()
            if filename and os.path.isfile(filename):
                try:
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                        filename, 128, 128, preserve_aspect_ratio=True)
                    preview.set_from_pixbuf(pixbuf)
                    dialog.set_preview_widget_active(True)
                except:
                    dialog.set_preview_widget_active(False)
            else:
                dialog.set_preview_widget_active(False)

        dialog.connect("update-preview", update_preview)
        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.connect("response", self.on_picture_dialog_response)
        dialog.show_all()

    def on_picture_dialog_response(self, dialog, response_id):
        if response_id == Gtk.ResponseType.OK:
            selected_file = dialog.get_filename()
            
            
            safe_run([
                "magick", selected_file, "-resize", "512x512",
                "-background", "none", "-flatten", "png:" + FACE_PATH
            ])
            
            notify(FACE_PATH, TR['Profile Manager'], TR['Profile picture updated'], duration=3)
            
            
            self.image_widget.set_from_file(FACE_PATH)
            self.set_icon_from_file(FACE_PATH)

        dialog.destroy()

    def change_name(self, widget):
        dialog = Gtk.Dialog(title=TR['Change Hostname'], parent=self)
        dialog.set_default_size(300, 100)

        entry = Gtk.Entry()
        with open(HOSTNAME_PATH) as f:
            entry.set_text(f.read().strip())

        box = dialog.get_content_area()
        box.pack_start(Gtk.Label(label=TR['New name:']), False, False, 5)
        box.pack_start(entry, False, False, 5)

        dialog.add_buttons(TR['Cancel'], Gtk.ResponseType.CANCEL,
                           TR['Apply'], Gtk.ResponseType.OK)
        dialog.set_default_response(Gtk.ResponseType.OK)
        entry.connect("activate", lambda w: dialog.response(Gtk.ResponseType.OK))

        dialog.show_all()
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            new_name = entry.get_text().replace(" ", "-").strip()
            safe_run(["hostname", new_name])
            with open(HOSTNAME_PATH, "w") as f:
                f.write(new_name + "\n")
            safe_run(["sed", "-i", f"s/127.0.0.1.*/127.0.0.1\t{new_name}/", "/etc/hosts"])
            notify(FACE_PATH, TR['Profile Manager'], f"{TR['Hostname changed to']} {new_name}", duration=3)
        dialog.destroy()

if __name__ == "__main__":
    win = ProfileManager()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
