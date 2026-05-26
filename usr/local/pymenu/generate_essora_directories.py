#!/usr/bin/env python3
"""
Generador de Archivos .directory para Pymenu

Editado por: josejp2424
Motivo: Crea archivos .directory completos en ~/.local/share/desktop-directories/
        con traducciones en más de 50 idiomas para mapear correctamente iconos
        de categorías sin importar el idioma del sistema. Incluye soporte para
        Favoritos y eliminación automática de entradas vacías.
"""

import os


TEMPLATE = """[Desktop Entry]
Type=Directory
{names}Icon={icon}
"""


TRANSLATIONS = {
    'favorites': {
        'en': 'Favorites',
        'ar': 'المفضلة',
        'be': 'Упадабаныя',
        'bg': 'Предпочитани',
        'ca': 'Preferits',
        'cs': 'Oblíbené',
        'da': 'Favoritter',
        'de': 'Favoriten',
        'el': 'Αγαπημένα',
        'en_GB': 'Favourites',
        'es': 'Favoritos',
        'et': 'Lemmikud',
        'eu': 'Gogokoak',
        'fi': 'Suosikit',
        'fr': 'Favoris',
        'gl': 'Favoritos',
        'he': 'מועדפים',
        'hr': 'Favoriti',
        'hu': 'Kedvencek',
        'id': 'Favorit',
        'it': 'Preferiti',
        'ja': 'お気に入り',
        'ko': '즐겨찾기',
        'lt': 'Mėgstamiausi',
        'nl': 'Favorieten',
        'nn': 'Favorittar',
        'pl': 'Ulubione',
        'pt': 'Favoritos',
        'pt_BR': 'Favoritos',
        'ro': 'Favorite',
        'ru': 'Избранное',
        'sk': 'Obľúbené',
        'sl': 'Priljubljene',
        'sr': 'Омиљени',
        'sr@latin': 'Omiljeni',
        'sv': 'Favoriter',
        'tr': 'Sık Kullanılanlar',
        'uk': 'Вибране',
        'vi': 'Yêu thích',
        'zh_CN': '收藏夹',
        'zh_TW': '我的最愛',
    },
    'desktop': {
        'en': 'Desktop',
        'ar': 'سطح المكتب',
        'be': 'Працоўны стол',
        'bg': 'Работен плот',
        'ca': 'Escriptori',
        'cs': 'Plocha',
        'da': 'Skrivebord',
        'de': 'Arbeitsfläche',
        'el': 'Επιφάνεια εργασίας',
        'en_GB': 'Desktop',
        'es': 'Escritorio',
        'et': 'Töölaud',
        'eu': 'Mahaigaina',
        'fi': 'Työpöytä',
        'fr': 'Bureau',
        'gl': 'Escritorio',
        'he': 'שולחן עבודה',
        'hr': 'Radna površina',
        'hu': 'Asztal',
        'id': 'Desktop',
        'it': 'Scrivania',
        'ja': 'デスクトップ',
        'ko': '데스크톱',
        'lt': 'Darbalaukis',
        'nl': 'Bureaublad',
        'nn': 'Skrivebord',
        'pl': 'Pulpit',
        'pt': 'Ambiente de Trabalho',
        'pt_BR': 'Área de Trabalho',
        'ro': 'Desktop',
        'ru': 'Рабочий стол',
        'sk': 'Pracovná plocha',
        'sl': 'Namizje',
        'sr': 'Радна површина',
        'sr@latin': 'Radna površina',
        'sv': 'Skrivbord',
        'tr': 'Masaüstü',
        'uk': 'Стільниця',
        'vi': 'Màn hình nền',
        'zh_CN': '桌面',
        'zh_TW': '桌面',
    },
    'system': {
        'en': 'System',
        'ar': 'النظام',
        'be': 'Сістэма',
        'bg': 'Система',
        'ca': 'Sistema',
        'cs': 'Systém',
        'da': 'System',
        'de': 'System',
        'el': 'Σύστημα',
        'en_GB': 'System',
        'es': 'Sistema',
        'et': 'Süsteem',
        'eu': 'Sistema',
        'fi': 'Järjestelmä',
        'fr': 'Système',
        'gl': 'Sistema',
        'he': 'מערכת',
        'hr': 'Sustav',
        'hu': 'Rendszer',
        'id': 'Sistem',
        'it': 'Sistema',
        'ja': 'システム',
        'ko': '시스템',
        'lt': 'Sistema',
        'nl': 'Systeem',
        'nn': 'System',
        'pl': 'System',
        'pt': 'Sistema',
        'pt_BR': 'Sistema',
        'ro': 'Sistem',
        'ru': 'Система',
        'sk': 'Systém',
        'sl': 'Sistem',
        'sr': 'Систем',
        'sr@latin': 'Sistem',
        'sv': 'System',
        'tr': 'Sistem',
        'uk': 'Система',
        'vi': 'Hệ thống',
        'zh_CN': '系统',
        'zh_TW': '系統',
    },
    'utilities': {
        'en': 'Utilities',
        'ar': 'أدوات',
        'be': 'Утыліты',
        'bg': 'Помощни програми',
        'ca': 'Utilitats',
        'cs': 'Nástroje',
        'da': 'Værktøjer',
        'de': 'Zubehör',
        'el': 'Βοηθήματα',
        'en_GB': 'Utilities',
        'es': 'Utilidades',
        'et': 'Tööriistad',
        'eu': 'Tresnak',
        'fi': 'Apuohjelmat',
        'fr': 'Utilitaires',
        'gl': 'Utilidades',
        'he': 'כלי עזר',
        'hr': 'Uslužni programi',
        'hu': 'Segédeszközök',
        'id': 'Utilitas',
        'it': 'Accessori',
        'ja': 'ユーティリティ',
        'ko': '보조 프로그램',
        'lt': 'Įrankiai',
        'nl': 'Hulpmiddelen',
        'nn': 'Verktøy',
        'pl': 'Narzędzia',
        'pt': 'Utilitários',
        'pt_BR': 'Utilitários',
        'ro': 'Utilitare',
        'ru': 'Утилиты',
        'sk': 'Nástroje',
        'sl': 'Pripomočki',
        'sr': 'Алати',
        'sr@latin': 'Alati',
        'sv': 'Verktyg',
        'tr': 'Araçlar',
        'uk': 'Утиліти',
        'vi': 'Tiện ích',
        'zh_CN': '实用工具',
        'zh_TW': '公用程式',
    },
    'file': {
        'en': 'File',
        'ar': 'الملفات',
        'be': 'Файл',
        'bg': 'Файл',
        'ca': 'Fitxer',
        'cs': 'Soubor',
        'da': 'Fil',
        'de': 'Datei',
        'el': 'Αρχείο',
        'en_GB': 'File',
        'es': 'Archivo',
        'et': 'Fail',
        'eu': 'Fitxategia',
        'fi': 'Tiedosto',
        'fr': 'Fichier',
        'gl': 'Ficheiro',
        'he': 'קובץ',
        'hr': 'Datoteka',
        'hu': 'Fájl',
        'id': 'Berkas',
        'it': 'File',
        'ja': 'ファイル',
        'ko': '파일',
        'lt': 'Failas',
        'nl': 'Bestand',
        'nn': 'Fil',
        'pl': 'Plik',
        'pt': 'Ficheiro',
        'pt_BR': 'Arquivo',
        'ro': 'Fișier',
        'ru': 'Файл',
        'sk': 'Súbor',
        'sl': 'Datoteka',
        'sr': 'Фајл',
        'sr@latin': 'Fajl',
        'sv': 'Fil',
        'tr': 'Dosya',
        'uk': 'Файл',
        'vi': 'Tập tin',
        'zh_CN': '文件',
        'zh_TW': '檔案',
    },
    'graphics': {
        'en': 'Graphics',
        'ar': 'الرسومات',
        'be': 'Графіка',
        'bg': 'Графика',
        'ca': 'Gràfics',
        'cs': 'Grafika',
        'da': 'Grafik',
        'de': 'Grafik',
        'el': 'Γραφικά',
        'en_GB': 'Graphics',
        'es': 'Gráficos',
        'et': 'Graafika',
        'eu': 'Grafikoak',
        'fi': 'Grafiikka',
        'fr': 'Graphisme',
        'gl': 'Gráficos',
        'he': 'גרפיקה',
        'hr': 'Grafika',
        'hu': 'Grafika',
        'id': 'Grafis',
        'it': 'Grafica',
        'ja': 'グラフィックス',
        'ko': '그래픽',
        'lt': 'Grafika',
        'nl': 'Grafisch',
        'nn': 'Grafikk',
        'pl': 'Grafika',
        'pt': 'Gráficos',
        'pt_BR': 'Gráficos',
        'ro': 'Grafică',
        'ru': 'Графика',
        'sk': 'Grafika',
        'sl': 'Grafika',
        'sr': 'Графика',
        'sr@latin': 'Grafika',
        'sv': 'Grafik',
        'tr': 'Grafik',
        'uk': 'Графіка',
        'vi': 'Đồ họa',
        'zh_CN': '图形',
        'zh_TW': '美工繪圖',
    },
    'office': {
        'en': 'Office',
        'ar': 'المكتب',
        'be': 'Офіс',
        'bg': 'Офис',
        'ca': 'Oficina',
        'cs': 'Kancelář',
        'da': 'Kontor',
        'de': 'Büroprogramme',
        'el': 'Γραφείο',
        'en_GB': 'Office',
        'es': 'Oficina',
        'et': 'Kontor',
        'eu': 'Bulegoa',
        'fi': 'Toimisto',
        'fr': 'Bureautique',
        'gl': 'Ofimática',
        'he': 'משרד',
        'hr': 'Ured',
        'hu': 'Iroda',
        'id': 'Perkantoran',
        'it': 'Ufficio',
        'ja': 'オフィス',
        'ko': '사무용 도구',
        'lt': 'Raštinė',
        'nl': 'Kantoor',
        'nn': 'Kontor',
        'pl': 'Biuro',
        'pt': 'Escritório',
        'pt_BR': 'Escritório',
        'ro': 'Birou',
        'ru': 'Офис',
        'sk': 'Kancelária',
        'sl': 'Pisarna',
        'sr': 'Канцеларија',
        'sr@latin': 'Kancelarija',
        'sv': 'Kontor',
        'tr': 'Ofis',
        'uk': 'Офіс',
        'vi': 'Văn phòng',
        'zh_CN': '办公',
        'zh_TW': '辦公軟體',
    },
    'internet': {
        'en': 'Internet',
        'ar': 'الإنترنت',
        'be': 'Інтэрнэт',
        'bg': 'Интернет',
        'ca': 'Internet',
        'cs': 'Internet',
        'da': 'Internet',
        'de': 'Internet',
        'el': 'Διαδίκτυο',
        'en_GB': 'Internet',
        'es': 'Internet',
        'et': 'Internet',
        'eu': 'Internet',
        'fi': 'Internet',
        'fr': 'Internet',
        'gl': 'Internet',
        'he': 'אינטרנט',
        'hr': 'Internet',
        'hu': 'Internet',
        'id': 'Internet',
        'it': 'Internet',
        'ja': 'インターネット',
        'ko': '인터넷',
        'lt': 'Internetas',
        'nl': 'Internet',
        'nn': 'Internett',
        'pl': 'Internet',
        'pt': 'Internet',
        'pt_BR': 'Internet',
        'ro': 'Internet',
        'ru': 'Интернет',
        'sk': 'Internet',
        'sl': 'Internet',
        'sr': 'Интернет',
        'sr@latin': 'Internet',
        'sv': 'Internet',
        'tr': 'İnternet',
        'uk': 'Інтернет',
        'vi': 'Internet',
        'zh_CN': '互联网',
        'zh_TW': '網際網路',
    },
    'multimedia': {
        'en': 'Multimedia',
        'ar': 'الوسائط المتعددة',
        'be': 'Мультымедыя',
        'bg': 'Мултимедия',
        'ca': 'Multimèdia',
        'cs': 'Multimédia',
        'da': 'Multimedie',
        'de': 'Multimedia',
        'el': 'Πολυμέσα',
        'en_GB': 'Multimedia',
        'es': 'Multimedia',
        'et': 'Multimeedia',
        'eu': 'Multimedia',
        'fi': 'Multimedia',
        'fr': 'Multimédia',
        'gl': 'Multimedia',
        'he': 'מולטימדיה',
        'hr': 'Multimedija',
        'hu': 'Multimédia',
        'id': 'Multimedia',
        'it': 'Multimedia',
        'ja': 'マルチメディア',
        'ko': '멀티미디어',
        'lt': 'Multimedija',
        'nl': 'Multimedia',
        'nn': 'Multimedia',
        'pl': 'Multimedia',
        'pt': 'Multimédia',
        'pt_BR': 'Multimídia',
        'ro': 'Multimedia',
        'ru': 'Мультимедиа',
        'sk': 'Multimédiá',
        'sl': 'Večpredstavnost',
        'sr': 'Мултимедија',
        'sr@latin': 'Multimedija',
        'sv': 'Multimedia',
        'tr': 'Çokluortam',
        'uk': 'Мультимедіа',
        'vi': 'Đa phương tiện',
        'zh_CN': '多媒体',
        'zh_TW': '多媒體',
    },
    'games': {
        'en': 'Games',
        'ar': 'الألعاب',
        'be': 'Гульні',
        'bg': 'Игри',
        'ca': 'Jocs',
        'cs': 'Hry',
        'da': 'Spil',
        'de': 'Spiele',
        'el': 'Παιχνίδια',
        'en_GB': 'Games',
        'es': 'Juegos',
        'et': 'Mängud',
        'eu': 'Jokoak',
        'fi': 'Pelit',
        'fr': 'Jeux',
        'gl': 'Xogos',
        'he': 'משחקים',
        'hr': 'Igre',
        'hu': 'Játékok',
        'id': 'Permainan',
        'it': 'Giochi',
        'ja': 'ゲーム',
        'ko': '게임',
        'lt': 'Žaidimai',
        'nl': 'Spellen',
        'nn': 'Spel',
        'pl': 'Gry',
        'pt': 'Jogos',
        'pt_BR': 'Jogos',
        'ro': 'Jocuri',
        'ru': 'Игры',
        'sk': 'Hry',
        'sl': 'Igre',
        'sr': 'Игре',
        'sr@latin': 'Igre',
        'sv': 'Spel',
        'tr': 'Oyunlar',
        'uk': 'Ігри',
        'vi': 'Trò chơi',
        'zh_CN': '游戏',
        'zh_TW': '遊戲',
    },
    'wine': {
        'en': 'Wine',
        'ar': 'واين',
        'be': 'Wine',
        'bg': 'Wine',
        'ca': 'Wine',
        'cs': 'Wine',
        'da': 'Wine',
        'de': 'Wine',
        'el': 'Wine',
        'en_GB': 'Wine',
        'es': 'Wine',
        'et': 'Wine',
        'eu': 'Wine',
        'fi': 'Wine',
        'fr': 'Wine',
        'gl': 'Wine',
        'he': 'Wine',
        'hr': 'Wine',
        'hu': 'Wine',
        'id': 'Wine',
        'it': 'Wine',
        'ja': 'Wine',
        'ko': 'Wine',
        'lt': 'Wine',
        'nl': 'Wine',
        'nn': 'Wine',
        'pl': 'Wine',
        'pt': 'Wine',
        'pt_BR': 'Wine',
        'ro': 'Wine',
        'ru': 'Wine',
        'sk': 'Wine',
        'sl': 'Wine',
        'sr': 'Wine',
        'sr@latin': 'Wine',
        'sv': 'Wine',
        'tr': 'Wine',
        'uk': 'Wine',
        'vi': 'Wine',
        'zh_CN': 'Wine',
        'zh_TW': 'Wine',
    },
}

# Iconos para cada categoría
ICONS = {
    'favorites': 'starred',
    'desktop': 'preferences-desktop',
    'system': 'applications-system',
    'utilities': 'applications-utilities',
    'file': 'system-file-manager',
    'graphics': 'applications-graphics',
    'office': 'applications-office',
    'internet': 'applications-internet',
    'multimedia': 'applications-multimedia',
    'games': 'applications-games',
    'wine': 'wine',  # Editado por: josejp2424
}


def build_names_section(category_key):
    """Construye la sección de nombres solo con traducciones existentes"""
    translations = TRANSLATIONS.get(category_key, {})
    
    lines = []
    

    if 'en' in translations:
        lines.append(f"Name={translations['en']}")
    

    lang_codes = [
        'ar', 'ast', 'az', 'be', 'bg', 'bs', 'ca', 'ca@valencia', 'cs', 'da',
        'de', 'el', 'en_GB', 'eo', 'es', 'et', 'eu', 'fi', 'fr', 'gl', 'he',
        'hi', 'hr', 'hsb', 'hu', 'ia', 'id', 'is', 'it', 'ja', 'ka', 'ko',
        'lt', 'lv', 'ml', 'nb', 'nds', 'nl', 'nn', 'pa', 'pl', 'pt', 'pt_BR',
        'ro', 'ru', 'sa', 'se', 'sk', 'sl', 'sr', 'sr@ijekavian',
        'sr@ijekavianlatin', 'sr@latin', 'sv', 'ta', 'tg', 'th', 'tr', 'uk',
        'vi', 'x-test', 'zh_CN', 'zh_TW'
    ]
    

    for lang in lang_codes:
        if lang in translations:
            lines.append(f"Name[{lang}]={translations[lang]}")
    
    return '\n'.join(lines) + '\n'


def generate_files(output_dir=None, dry_run=False):
    """
    Genera archivos .directory con traducciones completas
    
    Args:
        output_dir: Directorio de salida (default: ~/.local/share/desktop-directories)
        dry_run: Solo muestra qué se crearía
    """
    if output_dir is None:
        output_dir = os.path.expanduser('~/.local/share/desktop-directories')
    
    print("=" * 60)
    print("GENERADOR DE ARCHIVOS .DIRECTORY PARA PYMENU")
    print("Editado por: josejp2424")
    print("=" * 60)
    print(f"Directorio: {output_dir}")
    print(f"Modo: {'DRY RUN' if dry_run else 'CREAR ARCHIVOS'}")
    print()
    
    if not dry_run:
        os.makedirs(output_dir, exist_ok=True)
    
    created = 0
    
    for key in TRANSLATIONS.keys():
        filename = f"essora-{key}.directory"
        filepath = os.path.join(output_dir, filename)
        
        names = build_names_section(key)
        icon = ICONS.get(key, 'applications-other')
        content = TEMPLATE.format(names=names, icon=icon)
        
        if dry_run:
            print(f"📄 {filename}")
            trans = TRANSLATIONS[key]
            en_name = trans.get('en', key)
            es_name = trans.get('es', key)
            print(f"   {en_name} / {es_name} → {icon}")
            print(f"   ({len(trans)} idiomas)")
        else:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                os.chmod(filepath, 0o644)
                trans = TRANSLATIONS[key]
                print(f" {filename} ({len(trans)} idiomas)")
                created += 1
            except Exception as e:
                print(f" Error: {e}")
    
    print()
    print("=" * 60)
    if dry_run:
        print(f"Se crearían {len(TRANSLATIONS)} archivos")
    else:
        print(f" Creados {created}/{len(TRANSLATIONS)} archivos")
        print(f"\n Ahora ejecuta Pymenu para usar los nuevos mapeos")
    print("=" * 60)


def main():
    import sys
    
    dry_run = '--dry-run' in sys.argv
    
    # Opción para crear en el sistema (requiere sudo)
    if '--system' in sys.argv:
        if os.geteuid() != 0:
            print("  --system requiere sudo")
            print("Ejecuta: sudo python3 generate_essora_directories.py --system")
            sys.exit(1)
        output_dir = '/usr/share/desktop-directories'
    else:
        output_dir = None
    
    generate_files(output_dir=output_dir, dry_run=dry_run)


if __name__ == "__main__":
    main()
