/*
 * Essora PyMenu - native GTK3 menu for EssoraWM
 * Copyright (C) 2026 josejp2424
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <ctype.h>
#include <errno.h>
#include <limits.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/utsname.h>
#include <fcntl.h>

#ifdef ESSORA_USE_SYSTEM_GTK_HEADERS
#include <gtk/gtk.h>
#include <gio/gio.h>
#include <gdk-pixbuf/gdk-pixbuf.h>
#include <pango/pango.h>
#else
#include "gtk3_abi.h"
#endif

#define APP_NAME "Essora PyMenu"
#define APP_VERSION "1.0.1"
#define INSTALL_DIR "/usr/local/pymenu"
#define DEFAULT_CONFIG INSTALL_DIR "/defaults/pymenu.json"
#define CONFIG_REL ".config/essorawm/pymenu.json"
#define MENU_REL ".config/essorawm/essora-menu.xml"
#define FACE_REL ".config/essorawm/face"
#define MENU_GENERATOR INSTALL_DIR "/essora-menu-gen.py"
#define CONFIGURATOR INSTALL_DIR "/pymenu-config.py"
#define MAX_ICON_PATHS 64
#define MAX_EXCLUDED 64
#define LOAD_BATCH 10

#ifndef MIN
#define MIN(a,b) ((a)<(b)?(a):(b))
#endif
#ifndef MAX
#define MAX(a,b) ((a)>(b)?(a):(b))
#endif

typedef struct MenuState MenuState;

typedef struct {
    char *name;
    char *exec;
    char *icon;
    char *comment;
} AppInfo;

typedef struct {
    MenuState *state;
    char *label;
    char *icon;
    AppInfo **apps;
    size_t app_count;
    size_t app_capacity;
    GtkWidget *row;
} Category;

typedef struct {
    char *name;
    char *exec;
    char *icon;
} Favorite;

typedef struct {
    int width;
    int height;
    int icon_size;
    int category_icon_size;
    int profile_pic_size;
    int decorated_window;
    int hide_header;
    int hide_category_text;
    int hide_os_name;
    int hide_kernel;
    int hide_hostname;
    int hide_profile_pic;
    int hide_places;
    int hide_favorites;
    int profile_in_places;
    int use_gtk_theme;
    int use_tint2;
    char halign[16];
    char profile_pic_shape[16];
    char header_layout[16];
    char header_text_align[16];
    char search_bar_position[16];
    char search_bar_container[32];
    char font_family[128];
    int font_size_categories;
    int font_size_names;
    int font_size_header;
    char background[64];
    char border[64];
    char text_normal[64];
    char text_header_os[64];
    char text_header_kernel[64];
    char text_header_hostname[64];
    char hover_background[64];
    char selected_background[64];
    char selected_text[64];
    char button_normal_background[64];
    char button_text[64];
    char categories_background[64];
    char profile_pic[PATH_MAX];
    char profile_manager[PATH_MAX];
    char shutdown_cmd[PATH_MAX];
    char tint2rc[PATH_MAX];
    Favorite *favorites;
    size_t favorite_count;
    char *excluded[MAX_EXCLUDED];
    size_t excluded_count;
} Config;

typedef struct {
    int height;
    char valign[16];
    char halign[16];
} TrayConfig;

typedef struct {
    MenuState *state;
    Category *category;
    size_t index;
    unsigned generation;
    AppInfo **search_apps;
    size_t search_count;
    int owns_search_array;
} LoadContext;

typedef struct {
    MenuState *state;
    AppInfo *app;
    GtkWidget *button;
} AppSignalData;

typedef struct {
    MenuState *state;
    Category *category;
} CategorySignalData;

struct MenuState {
    Config config;
    TrayConfig tray;
    char menu_path[PATH_MAX];
    char config_path[PATH_MAX];
    char face_path[PATH_MAX];
    Category **categories;
    size_t category_count;
    size_t category_capacity;
    char *icon_paths[MAX_ICON_PATHS];
    size_t icon_path_count;
    GHashTable *translations;
    GHashTable *icon_cache;
    GtkWidget *window;
    GtkWidget *main_box;
    GtkWidget *categories_list;
    GtkWidget *apps_flow;
    GtkWidget *search_entry;
    Category *current_category;
    Category *selected_category;
    unsigned load_generation;
    guint hover_source;
    guint reload_source;
    guint grab_retry_source;
    int grab_attempts;
    int context_menu_active;
    int modal_dialog_active;
    int pointer_grabbed;
    int rebuilding;
    int explicit_x;
    int explicit_y;
    GFile *menu_file;
    GFileMonitor *menu_monitor;
};

static MenuState *global_state = NULL;

static char *xstrdup(const char *s) {
    if (!s) s = "";
    char *p = strdup(s);
    if (!p) { perror("strdup"); exit(1); }
    return p;
}

static void strcopy(char *dst, size_t cap, const char *src) {
    if (!cap) return;
    snprintf(dst, cap, "%s", src ? src : "");
}

static char *trim(char *s) {
    if (!s) return s;
    while (*s && isspace((unsigned char)*s)) s++;
    char *end = s + strlen(s);
    while (end > s && isspace((unsigned char)end[-1])) end--;
    *end = '\0';
    return s;
}

static int file_exists(const char *path) {
    struct stat st;
    return path && stat(path, &st) == 0;
}

static int is_directory(const char *path) {
    struct stat st;
    return path && stat(path, &st) == 0 && S_ISDIR(st.st_mode);
}

static char *read_file(const char *path, size_t *size_out) {
    FILE *f = fopen(path, "rb");
    if (!f) return NULL;
    if (fseek(f, 0, SEEK_END) != 0) { fclose(f); return NULL; }
    long n = ftell(f);
    if (n < 0 || fseek(f, 0, SEEK_SET) != 0) { fclose(f); return NULL; }
    char *buf = calloc((size_t)n + 1, 1);
    if (!buf) { fclose(f); return NULL; }
    size_t got = fread(buf, 1, (size_t)n, f);
    fclose(f);
    buf[got] = '\0';
    if (size_out) *size_out = got;
    return buf;
}

static int write_file(const char *path, const char *data, mode_t mode) {
    FILE *f = fopen(path, "wb");
    if (!f) return -1;
    size_t len = strlen(data);
    int ok = fwrite(data, 1, len, f) == len ? 0 : -1;
    if (fclose(f) != 0) ok = -1;
    if (ok == 0) chmod(path, mode);
    return ok;
}

static int copy_file_if_missing(const char *src, const char *dst) {
    if (file_exists(dst)) return 0;
    size_t n = 0;
    char *data = read_file(src, &n);
    if (!data) return -1;
    int rc = write_file(dst, data, 0644);
    free(data);
    return rc;
}

static void ensure_config_paths(MenuState *s) {
    const char *home = g_get_home_dir();
    if (!home || !*home) home = "/root";
    snprintf(s->config_path, sizeof(s->config_path), "%s/%s", home, CONFIG_REL);
    snprintf(s->menu_path, sizeof(s->menu_path), "%s/%s", home, MENU_REL);
    snprintf(s->face_path, sizeof(s->face_path), "%s/%s", home, FACE_REL);
    char dir[PATH_MAX];
    snprintf(dir, sizeof(dir), "%s/.config/essorawm", home);
    g_mkdir_with_parents(dir, 0755);
    copy_file_if_missing(DEFAULT_CONFIG, s->config_path);
    copy_file_if_missing(INSTALL_DIR "/essora-menu.xml", s->menu_path);
}

static const char *json_find_value(const char *json, const char *key) {
    if (!json || !key) return NULL;
    char pattern[256];
    snprintf(pattern, sizeof(pattern), "\"%s\"", key);
    const char *p = json;
    while ((p = strstr(p, pattern))) {
        p += strlen(pattern);
        while (*p && isspace((unsigned char)*p)) p++;
        if (*p != ':') continue;
        p++;
        while (*p && isspace((unsigned char)*p)) p++;
        return p;
    }
    return NULL;
}

static char *json_read_string_at(const char *p) {
    if (!p || *p != '"') return NULL;
    p++;
    size_t cap = strlen(p) + 1;
    char *out = malloc(cap);
    if (!out) return NULL;
    size_t j = 0;
    while (*p && *p != '"') {
        if (*p == '\\' && p[1]) {
            p++;
            switch (*p) {
                case 'n': out[j++] = '\n'; break;
                case 'r': out[j++] = '\r'; break;
                case 't': out[j++] = '\t'; break;
                case 'b': out[j++] = '\b'; break;
                case 'f': out[j++] = '\f'; break;
                default: out[j++] = *p; break;
            }
            p++;
        } else {
            out[j++] = *p++;
        }
    }
    out[j] = '\0';
    return out;
}

static int json_get_string(const char *json, const char *key, char *dst, size_t cap) {
    const char *p = json_find_value(json, key);
    char *v = json_read_string_at(p);
    if (!v) return 0;
    strcopy(dst, cap, v);
    free(v);
    return 1;
}

static int json_get_int(const char *json, const char *key, int *out) {
    const char *p = json_find_value(json, key);
    if (!p) return 0;
    char *end = NULL;
    long v = strtol(p, &end, 10);
    if (end == p) return 0;
    *out = (int)v;
    return 1;
}

static int json_get_bool(const char *json, const char *key, int *out) {
    const char *p = json_find_value(json, key);
    if (!p) return 0;
    if (!strncmp(p, "true", 4)) { *out = 1; return 1; }
    if (!strncmp(p, "false", 5)) { *out = 0; return 1; }
    return 0;
}

static void free_favorites(Config *c) {
    for (size_t i = 0; i < c->favorite_count; i++) {
        free(c->favorites[i].name);
        free(c->favorites[i].exec);
        free(c->favorites[i].icon);
    }
    free(c->favorites);
    c->favorites = NULL;
    c->favorite_count = 0;
}

static void parse_favorites(Config *c, const char *json) {
    free_favorites(c);
    const char *p = json_find_value(json, "favorites");
    if (!p || *p != '[') return;
    p++;
    while (*p && *p != ']') {
        while (*p && *p != '{' && *p != ']') p++;
        if (*p != '{') break;
        const char *start = p;
        int depth = 0;
        int in_string = 0;
        int escaped = 0;
        while (*p) {
            char ch = *p++;
            if (in_string) {
                if (escaped) escaped = 0;
                else if (ch == '\\') escaped = 1;
                else if (ch == '"') in_string = 0;
            } else {
                if (ch == '"') in_string = 1;
                else if (ch == '{') depth++;
                else if (ch == '}' && --depth == 0) break;
            }
        }
        size_t len = (size_t)(p - start);
        char *obj = strndup(start, len);
        if (!obj) break;
        char name[512] = "", exec[2048] = "", icon[PATH_MAX] = "application-x-executable";
        json_get_string(obj, "name", name, sizeof(name));
        json_get_string(obj, "exec", exec, sizeof(exec));
        json_get_string(obj, "icon", icon, sizeof(icon));
        free(obj);
        if (*name && *exec) {
            Favorite *nf = realloc(c->favorites, (c->favorite_count + 1) * sizeof(*nf));
            if (!nf) break;
            c->favorites = nf;
            Favorite *f = &c->favorites[c->favorite_count++];
            f->name = xstrdup(name);
            f->exec = xstrdup(exec);
            f->icon = xstrdup(icon);
        }
    }
}

static void free_excluded(Config *c) {
    for (size_t i = 0; i < c->excluded_count; i++) free(c->excluded[i]);
    c->excluded_count = 0;
}

static void parse_excluded(Config *c, const char *json) {
    free_excluded(c);
    const char *p = json_find_value(json, "excluded");
    if (!p || *p != '[') return;
    p++;
    while (*p && *p != ']' && c->excluded_count < MAX_EXCLUDED) {
        while (*p && *p != '"' && *p != ']') p++;
        if (*p != '"') break;
        p++;
        const char *start = p;
        int escaped = 0;
        while (*p) {
            if (!escaped && *p == '"') break;
            if (!escaped && *p == '\\') escaped = 1;
            else escaped = 0;
            p++;
        }
        if (*p != '"') break;
        char *v = strndup(start, (size_t)(p - start));
        if (v && *v) c->excluded[c->excluded_count++] = v;
        else free(v);
        p++;
    }
}

static void config_defaults(Config *c) {
    memset(c, 0, sizeof(*c));
    c->width = 682;
    c->height = 440;
    c->icon_size = 32;
    c->category_icon_size = 40;
    c->profile_pic_size = 64;
    c->decorated_window = 0;
    c->hide_header = 0;
    c->hide_category_text = 0;
    c->hide_os_name = 1;
    c->hide_kernel = 1;
    c->hide_hostname = 0;
    c->hide_profile_pic = 0;
    c->hide_places = 0;
    c->hide_favorites = 1;
    c->profile_in_places = 1;
    c->use_gtk_theme = 0;
    strcopy(c->halign, sizeof(c->halign), "center");
    strcopy(c->profile_pic_shape, sizeof(c->profile_pic_shape), "circular");
    strcopy(c->header_layout, sizeof(c->header_layout), "center");
    strcopy(c->header_text_align, sizeof(c->header_text_align), "left");
    strcopy(c->search_bar_position, sizeof(c->search_bar_position), "bottom");
    strcopy(c->search_bar_container, sizeof(c->search_bar_container), "apps_column");
    strcopy(c->font_family, sizeof(c->font_family), "Cantarell 12");
    c->font_size_categories = 15000;
    c->font_size_names = 14000;
    c->font_size_header = 14000;
    strcopy(c->background, sizeof(c->background), "rgba(25, 27, 32, 1.00)");
    strcopy(c->border, sizeof(c->border), "rgba(159, 192, 130, 1.00)");
    strcopy(c->text_normal, sizeof(c->text_normal), "#f6f5f4");
    strcopy(c->text_header_os, sizeof(c->text_header_os), "#769609");
    strcopy(c->text_header_kernel, sizeof(c->text_header_kernel), "#769609");
    strcopy(c->text_header_hostname, sizeof(c->text_header_hostname), "#769609");
    strcopy(c->hover_background, sizeof(c->hover_background), "rgba(255,255,255,0.1)");
    strcopy(c->selected_background, sizeof(c->selected_background), "rgba(255,255,255,0.2)");
    strcopy(c->selected_text, sizeof(c->selected_text), "#ECEFF4");
    strcopy(c->button_normal_background, sizeof(c->button_normal_background), "rgba(25,27,32,1.0)");
    strcopy(c->button_text, sizeof(c->button_text), "#ECEFF4");
    strcopy(c->categories_background, sizeof(c->categories_background), "rgba(18,20,21,1.0)");
    strcopy(c->profile_pic, sizeof(c->profile_pic), INSTALL_DIR "/icon-pymenu/preferences-desktop-essora.svg");
    strcopy(c->profile_manager, sizeof(c->profile_manager), INSTALL_DIR "/ProfileManager.py");
    strcopy(c->shutdown_cmd, sizeof(c->shutdown_cmd), "/usr/local/bin/logout_gui");
    strcopy(c->tint2rc, sizeof(c->tint2rc), "/usr/share/tint2/tint2/tint2rc");
}

static void config_apply_json(Config *c, const char *json) {
    if (!json) return;
    json_get_int(json, "width", &c->width);
    json_get_int(json, "height", &c->height);
    json_get_int(json, "icon_size", &c->icon_size);
    json_get_int(json, "category_icon_size", &c->category_icon_size);
    json_get_int(json, "profile_pic_size", &c->profile_pic_size);
    json_get_bool(json, "decorated_window", &c->decorated_window);
    json_get_bool(json, "hide_header", &c->hide_header);
    json_get_bool(json, "hide_category_text", &c->hide_category_text);
    json_get_bool(json, "hide_os_name", &c->hide_os_name);
    json_get_bool(json, "hide_kernel", &c->hide_kernel);
    json_get_bool(json, "hide_hostname", &c->hide_hostname);
    json_get_bool(json, "hide_profile_pic", &c->hide_profile_pic);
    json_get_bool(json, "hide_places", &c->hide_places);
    json_get_bool(json, "hide_favorites", &c->hide_favorites);
    json_get_bool(json, "profile_in_places", &c->profile_in_places);
    json_get_bool(json, "use_gtk_theme", &c->use_gtk_theme);
    json_get_bool(json, "use_tint2", &c->use_tint2);
    json_get_string(json, "halign", c->halign, sizeof(c->halign));
    json_get_string(json, "profile_pic_shape", c->profile_pic_shape, sizeof(c->profile_pic_shape));
    json_get_string(json, "header_layout", c->header_layout, sizeof(c->header_layout));
    json_get_string(json, "header_text_align", c->header_text_align, sizeof(c->header_text_align));
    json_get_string(json, "search_bar_position", c->search_bar_position, sizeof(c->search_bar_position));
    json_get_string(json, "search_bar_container", c->search_bar_container, sizeof(c->search_bar_container));
    json_get_string(json, "family", c->font_family, sizeof(c->font_family));
    json_get_int(json, "size_categories", &c->font_size_categories);
    json_get_int(json, "size_names", &c->font_size_names);
    json_get_int(json, "size_header", &c->font_size_header);
    json_get_string(json, "background", c->background, sizeof(c->background));
    json_get_string(json, "border", c->border, sizeof(c->border));
    json_get_string(json, "text_normal", c->text_normal, sizeof(c->text_normal));
    json_get_string(json, "text_header_os", c->text_header_os, sizeof(c->text_header_os));
    json_get_string(json, "text_header_kernel", c->text_header_kernel, sizeof(c->text_header_kernel));
    json_get_string(json, "text_header_hostname", c->text_header_hostname, sizeof(c->text_header_hostname));
    json_get_string(json, "hover_background", c->hover_background, sizeof(c->hover_background));
    json_get_string(json, "selected_background", c->selected_background, sizeof(c->selected_background));
    json_get_string(json, "selected_text", c->selected_text, sizeof(c->selected_text));
    json_get_string(json, "button_normal_background", c->button_normal_background, sizeof(c->button_normal_background));
    json_get_string(json, "button_text", c->button_text, sizeof(c->button_text));
    json_get_string(json, "categories_background", c->categories_background, sizeof(c->categories_background));
    json_get_string(json, "profile_pic", c->profile_pic, sizeof(c->profile_pic));
    json_get_string(json, "profile_manager", c->profile_manager, sizeof(c->profile_manager));
    json_get_string(json, "shutdown_cmd", c->shutdown_cmd, sizeof(c->shutdown_cmd));
    json_get_string(json, "tint2rc", c->tint2rc, sizeof(c->tint2rc));
    parse_favorites(c, json);
    parse_excluded(c, json);
    c->width = MAX(320, MIN(c->width, 2400));
    c->height = MAX(240, MIN(c->height, 1600));
    c->icon_size = MAX(16, MIN(c->icon_size, 128));
    c->category_icon_size = MAX(16, MIN(c->category_icon_size, 96));
    c->profile_pic_size = MAX(32, MIN(c->profile_pic_size, 192));
}

static void load_config(MenuState *s) {
    config_defaults(&s->config);
    char *defaults = read_file(DEFAULT_CONFIG, NULL);
    if (defaults) { config_apply_json(&s->config, defaults); free(defaults); }
    char *user = read_file(s->config_path, NULL);
    if (user) { config_apply_json(&s->config, user); free(user); }
}

static int category_is_excluded(MenuState *s, const char *label) {
    for (size_t i = 0; i < s->config.excluded_count; i++)
        if (!strcasecmp(label, s->config.excluded[i])) return 1;
    return 0;
}

static void translation_value_destroy(gpointer p) { g_free(p); }

static void load_lang_file(MenuState *s, const char *path) {
    char *data = read_file(path, NULL);
    if (!data) return;
    char *save = NULL;
    for (char *line = strtok_r(data, "\n", &save); line; line = strtok_r(NULL, "\n", &save)) {
        line = trim(line);
        if (!*line || *line == '#') continue;
        char *eq = strchr(line, '=');
        if (!eq) continue;
        *eq = '\0';
        char *k = trim(line);
        char *v = trim(eq + 1);
        if (*k) g_hash_table_insert(s->translations, g_strdup(k), g_strdup(v));
    }
    free(data);
}

static void detect_language(char *out, size_t cap) {
    const char *lang = getenv("LANG");
    char tmp[128] = "";
    if (lang && *lang) strcopy(tmp, sizeof(tmp), lang);
    if (!*tmp) {
        char *lc = read_file("/etc/locale.conf", NULL);
        if (lc) {
            char *p = strstr(lc, "LANG=");
            if (p) {
                p += 5;
                char *e = strpbrk(p, "\r\n");
                if (e) *e = '\0';
                p = trim(p);
                if (*p == '"') { p++; char *q = strchr(p, '"'); if (q) *q = '\0'; }
                strcopy(tmp, sizeof(tmp), p);
            }
            free(lc);
        }
    }
    char *dot = strchr(tmp, '.'); if (dot) *dot = '\0';
    char *at = strchr(tmp, '@'); if (at) *at = '\0';
    for (char *p = tmp; *p; p++) if (*p == '_') *p = '-';
    strcopy(out, cap, *tmp ? tmp : "en");
}

static void add_builtin_translations(MenuState *s) {
    static const struct { const char *key; const char *value; } defaults[] = {
        {"Search applications...", "Search applications..."},
        {"Shutdown", "Shutdown"}, {"Search in the web", "Search in the web"},
        {"Pymenu config", "Pymenu config"}, {"Menu update", "Menu update"},
        {"Select avatar", "Select avatar"}, {"Run", "Run"},
        {"Create desktop shortcut", "Create desktop shortcut"},
        {"Acceso directo creado:", "Desktop shortcut created:"},
        {"Home", "Home"}, {"DownloadsDir", "Downloads"}, {"MusicDir", "Music"},
        {"DocumentsDir", "Documents"}, {"PicturesDir", "Pictures"}, {"VideosDir", "Videos"},
        {"Favorites", "Favorites"}
    };
    for (size_t i = 0; i < sizeof(defaults)/sizeof(defaults[0]); i++)
        g_hash_table_insert(s->translations, g_strdup(defaults[i].key), g_strdup(defaults[i].value));
}

static void load_translations(MenuState *s) {
    s->translations = g_hash_table_new_full(g_str_hash, g_str_equal, g_free, translation_value_destroy);
    add_builtin_translations(s);
    char lang[128]; detect_language(lang, sizeof(lang));
    const char *home = g_get_home_dir();
    char candidates[8][PATH_MAX];
    size_t n = 0;
    snprintf(candidates[n++], PATH_MAX, "%s/.config/essorawm/locale/%s.lang", home, lang);
    snprintf(candidates[n++], PATH_MAX, INSTALL_DIR "/locale/%s.lang", lang);
    char base[32]; strcopy(base, sizeof(base), lang);
    char *dash = strchr(base, '-'); if (dash) *dash = '\0';
    if (strcmp(base, lang)) {
        snprintf(candidates[n++], PATH_MAX, "%s/.config/essorawm/locale/%s.lang", home, base);
        snprintf(candidates[n++], PATH_MAX, INSTALL_DIR "/locale/%s.lang", base);
    }
    if (!strcmp(base, "pt")) {
        snprintf(candidates[n++], PATH_MAX, INSTALL_DIR "/locale/pt-BR.lang");
        snprintf(candidates[n++], PATH_MAX, INSTALL_DIR "/locale/pt-PT.lang");
    }
    for (size_t i = 0; i < n; i++) {
        if (file_exists(candidates[i])) { load_lang_file(s, candidates[i]); break; }
    }
}

static const char *tr(MenuState *s, const char *key) {
    if (!key) return "";
    char *v = g_hash_table_lookup(s->translations, key);
    return v ? v : key;
}

static void free_app(AppInfo *a) {
    if (!a) return;
    free(a->name); free(a->exec); free(a->icon); free(a->comment); free(a);
}

static void free_category(Category *c) {
    if (!c) return;
    for (size_t i = 0; i < c->app_count; i++) free_app(c->apps[i]);
    free(c->apps); free(c->label); free(c->icon); free(c);
}

static void clear_menu_data(MenuState *s) {
    for (size_t i = 0; i < s->category_count; i++) free_category(s->categories[i]);
    free(s->categories); s->categories = NULL; s->category_count = s->category_capacity = 0;
    for (size_t i = 0; i < s->icon_path_count; i++) free(s->icon_paths[i]);
    s->icon_path_count = 0;
    s->current_category = s->selected_category = NULL;
}

static void add_icon_path(MenuState *s, const char *path) {
    if (!path || !*path || s->icon_path_count >= MAX_ICON_PATHS) return;
    for (size_t i = 0; i < s->icon_path_count; i++) if (!strcmp(s->icon_paths[i], path)) return;
    s->icon_paths[s->icon_path_count++] = xstrdup(path);
}

static Category *add_category(MenuState *s, const char *label, const char *icon) {
    if (!label || !*label) return NULL;
    if (s->category_count == s->category_capacity) {
        size_t nc = s->category_capacity ? s->category_capacity * 2 : 16;
        Category **np = realloc(s->categories, nc * sizeof(*np));
        if (!np) return NULL;
        s->categories = np; s->category_capacity = nc;
    }
    Category *c = calloc(1, sizeof(*c));
    if (!c) return NULL;
    c->state = s;
    c->label = xstrdup(label);
    c->icon = xstrdup(icon && *icon ? icon : "applications-other");
    s->categories[s->category_count++] = c;
    return c;
}

static void add_app(Category *c, const char *name, const char *exec, const char *icon, const char *comment) {
    if (!c || !name || !*name || !exec || !*exec) return;
    if (c->app_count == c->app_capacity) {
        size_t nc = c->app_capacity ? c->app_capacity * 2 : 16;
        AppInfo **np = realloc(c->apps, nc * sizeof(*np));
        if (!np) return;
        c->apps = np; c->app_capacity = nc;
    }
    AppInfo *a = calloc(1, sizeof(*a));
    if (!a) return;
    a->name = xstrdup(name);
    a->exec = xstrdup(exec);
    a->icon = xstrdup(icon && *icon ? icon : "application-x-executable");
    a->comment = xstrdup(comment && *comment ? comment : name);
    c->apps[c->app_count++] = a;
}

typedef struct {
    MenuState *state;
    Category *current;
    int in_path;
    char *path_text;
    size_t path_len;
} XmlCtx;

static const char *xml_attr(const gchar **names, const gchar **values, const char *wanted) {
    if (!names || !values) return NULL;
    for (size_t i = 0; names[i] && values[i]; i++) if (!strcmp(names[i], wanted)) return values[i];
    return NULL;
}

static void xml_start(GMarkupParseContext *context, const gchar *name, const gchar **an, const gchar **av, gpointer data, GError **error) {
    (void)context; (void)error;
    XmlCtx *x = data;
    if (!strcmp(name, "Category")) {
        const char *label = xml_attr(an, av, "label");
        const char *icon = xml_attr(an, av, "icon");
        x->current = add_category(x->state, label, icon);
    } else if (!strcmp(name, "App") && x->current) {
        add_app(x->current, xml_attr(an,av,"label"), xml_attr(an,av,"exec"), xml_attr(an,av,"icon"), xml_attr(an,av,"comment"));
    } else if (!strcmp(name, "Tray")) {
        const char *h = xml_attr(an,av,"height");
        const char *v = xml_attr(an,av,"valign");
        const char *a = xml_attr(an,av,"halign");
        if (h) x->state->tray.height = atoi(h);
        if (v) strcopy(x->state->tray.valign, sizeof(x->state->tray.valign), v);
        if (a) strcopy(x->state->tray.halign, sizeof(x->state->tray.halign), a);
    } else if (!strcmp(name, "Path")) {
        x->in_path = 1;
        free(x->path_text); x->path_text = NULL; x->path_len = 0;
    }
}

static void xml_text(GMarkupParseContext *context, const gchar *text, gsize len, gpointer data, GError **error) {
    (void)context; (void)error;
    XmlCtx *x = data;
    if (!x->in_path || !len) return;
    char *np = realloc(x->path_text, x->path_len + len + 1);
    if (!np) return;
    x->path_text = np;
    memcpy(x->path_text + x->path_len, text, len);
    x->path_len += len;
    x->path_text[x->path_len] = '\0';
}

static void xml_end(GMarkupParseContext *context, const gchar *name, gpointer data, GError **error) {
    (void)context; (void)error;
    XmlCtx *x = data;
    if (!strcmp(name, "Category")) x->current = NULL;
    else if (!strcmp(name, "Path")) {
        if (x->path_text) add_icon_path(x->state, trim(x->path_text));
        x->in_path = 0;
        free(x->path_text); x->path_text = NULL; x->path_len = 0;
    }
}

static int parse_menu_xml(MenuState *s, char **error_text) {
    clear_menu_data(s);
    s->tray.height = 30;
    strcopy(s->tray.valign, sizeof(s->tray.valign), "bottom");
    strcopy(s->tray.halign, sizeof(s->tray.halign), "center");
    char *xml = read_file(s->menu_path, NULL);
    if (!xml) {
        if (error_text) asprintf(error_text, "No se encontró:\n%s", s->menu_path);
        return 0;
    }
    XmlCtx xc = { .state = s };
    GMarkupParser parser = { xml_start, xml_end, xml_text, NULL, NULL };
    GError *err = NULL;
    GMarkupParseContext *ctx = g_markup_parse_context_new(&parser, G_MARKUP_DEFAULT_FLAGS, &xc, NULL);
    gboolean ok = g_markup_parse_context_parse(ctx, xml, (gssize)strlen(xml), &err);
    if (ok) ok = g_markup_parse_context_end_parse(ctx, &err);
    g_markup_parse_context_free(ctx);
    free(xc.path_text);
    free(xml);
    if (!ok) {
        if (error_text) asprintf(error_text, "XML inválido en %s:\n%s", s->menu_path, err && err->message ? err->message : "error desconocido");
        if (err) g_error_free(err);
        clear_menu_data(s);
        return 0;
    }
    if (err) g_error_free(err);
    add_icon_path(s, INSTALL_DIR "/icon-pymenu");
    add_icon_path(s, "/usr/share/pixmaps");
    add_icon_path(s, "/usr/share/icons/hicolor/48x48/apps");
    size_t write = 0;
    for (size_t i = 0; i < s->category_count; i++) {
        Category *c = s->categories[i];
        if (!c->app_count || category_is_excluded(s, c->label)) free_category(c);
        else s->categories[write++] = c;
    }
    s->category_count = write;
    if (!s->category_count) {
        if (error_text) asprintf(error_text, "El archivo no contiene categorías con aplicaciones:\n%s", s->menu_path);
        return 0;
    }
    return 1;
}

static void shell_launch(const char *command) {
    if (!command || !*command) return;
    pid_t pid = fork();
    if (pid == 0) {
        setsid();
        int devnull = open("/dev/null", O_RDWR);
        if (devnull >= 0) {
            dup2(devnull, STDIN_FILENO); dup2(devnull, STDOUT_FILENO); dup2(devnull, STDERR_FILENO);
            if (devnull > STDERR_FILENO) close(devnull);
        }
        execl("/bin/sh", "sh", "-c", command, (char*)NULL);
        _exit(127);
    }
}

static char *shell_quote(const char *s) {
    size_t n = 3;
    for (const char *p=s; p && *p; p++) n += (*p=='\'' ? 4 : 1);
    char *q = malloc(n); if (!q) return NULL;
    char *o=q; *o++='\'';
    for (const char *p=s; p && *p; p++) {
        if (*p=='\'') { memcpy(o,"'\\''",4); o+=4; } else *o++=*p;
    }
    *o++='\''; *o='\0'; return q;
}

static void open_directory_path(const char *path) {
    char expanded[PATH_MAX];
    const char *home = g_get_home_dir();
    if (!strcmp(path, "~")) strcopy(expanded, sizeof(expanded), home);
    else if (!strncmp(path, "~/", 2)) snprintf(expanded, sizeof(expanded), "%s/%s", home, path+2);
    else strcopy(expanded, sizeof(expanded), path);
    char *q = shell_quote(expanded);
    char cmd[PATH_MAX+256];
    if (file_exists("/usr/local/bin/defaultfilemanager") || file_exists("/usr/bin/defaultfilemanager"))
        snprintf(cmd, sizeof(cmd), "defaultfilemanager %s", q);
    else if (file_exists("/usr/local/apps/ROX-Filer/AppRun") || file_exists("/usr/bin/rox"))
        snprintf(cmd, sizeof(cmd), "rox %s", q);
    else snprintf(cmd, sizeof(cmd), "xdg-open %s", q);
    free(q); shell_launch(cmd);
}

static char *find_icon_file(MenuState *s, const char *name) {
    if (!name || !*name) return NULL;
    if (name[0] == '/' && file_exists(name)) return xstrdup(name);
    static const char *exts[] = {"", ".png", ".svg", ".xpm", ".ico", ".jpg", ".jpeg", NULL};
    for (size_t i = 0; i < s->icon_path_count; i++) {
        if (!is_directory(s->icon_paths[i])) continue;
        for (size_t j = 0; exts[j]; j++) {
            char path[PATH_MAX];
            if (*exts[j] || !strchr(name, '.')) snprintf(path, sizeof(path), "%s/%s%s", s->icon_paths[i], name, exts[j]);
            else snprintf(path, sizeof(path), "%s/%s", s->icon_paths[i], name);
            if (file_exists(path)) return xstrdup(path);
        }
    }
    return NULL;
}

static GdkPixbuf *load_pixbuf(MenuState *s, const char *icon, int size) {
    if (!icon || !*icon) icon = "application-x-executable";
    char key[PATH_MAX+64]; snprintf(key, sizeof(key), "%s@%d", icon, size);
    GdkPixbuf *cached = g_hash_table_lookup(s->icon_cache, key);
    if (cached) return g_object_ref(cached);
    GError *err = NULL;
    GdkPixbuf *pb = NULL;
    char *file = NULL;
    if (icon[0] == '/' || strchr(icon, '.')) file = find_icon_file(s, icon);
    if (file) {
        pb = gdk_pixbuf_new_from_file_at_scale(file, size, size, TRUE, &err);
        if (err) { g_error_free(err); err=NULL; }
        free(file);
    }
    if (!pb) {
        char theme_name[PATH_MAX]; strcopy(theme_name, sizeof(theme_name), icon);
        char *slash = strrchr(theme_name, '/'); if (slash) memmove(theme_name, slash+1, strlen(slash+1)+1);
        char *dot = strrchr(theme_name, '.'); if (dot && (!strcasecmp(dot,".png") || !strcasecmp(dot,".svg") || !strcasecmp(dot,".xpm"))) *dot='\0';
        pb = gtk_icon_theme_load_icon(gtk_icon_theme_get_default(), theme_name, size, GTK_ICON_LOOKUP_FORCE_SIZE, &err);
        if (err) { g_error_free(err); err=NULL; }
        if (!pb && !strstr(theme_name, "-symbolic")) {
            char symbolic[PATH_MAX + 16];
            snprintf(symbolic, sizeof(symbolic), "%s-symbolic", theme_name);
            pb = gtk_icon_theme_load_icon(gtk_icon_theme_get_default(), symbolic, size, GTK_ICON_LOOKUP_FORCE_SIZE, &err);
            if (err) { g_error_free(err); err=NULL; }
        }
    }
    if (!pb && icon[0] != '/') {
        file = find_icon_file(s, icon);
        if (file) {
            pb = gdk_pixbuf_new_from_file_at_scale(file, size, size, TRUE, &err);
            if (err) { g_error_free(err); err=NULL; }
            free(file);
        }
    }
    if (!pb && strcmp(icon, "application-x-executable")) {
        pb = gtk_icon_theme_load_icon(gtk_icon_theme_get_default(), "application-x-executable", size, GTK_ICON_LOOKUP_FORCE_SIZE, &err);
        if (err) { g_error_free(err); err=NULL; }
    }
    if (pb) g_hash_table_insert(s->icon_cache, g_strdup(key), g_object_ref(pb));
    return pb;
}

static GtkWidget *image_for_icon(MenuState *s, const char *icon, int size) {
    GdkPixbuf *pb = load_pixbuf(s, icon, size);
    GtkWidget *img;
    if (pb) { img = gtk_image_new_from_pixbuf(pb); g_object_unref(pb); }
    else { img = gtk_image_new_from_icon_name("application-x-executable", GTK_ICON_SIZE_DND); gtk_image_set_pixel_size(GTK_IMAGE(img), size); }
    return img;
}

static void set_font(GtkWidget *w, MenuState *s, int size) {
    PangoFontDescription *fd = pango_font_description_from_string(s->config.font_family);
    if (!fd) return;
    pango_font_description_set_size(fd, size);
    gtk_widget_override_font(w, fd);
    pango_font_description_free(fd);
}

static void apply_css(MenuState *s) {
    char *css = NULL;
    if (s->config.use_gtk_theme) {
        asprintf(&css,
            ".menu-window { border-radius: 5px; border: 1px solid @theme_unfocused_fg_color; padding: 5px; }\n"
            ".category-list { padding: 2px; }\n"
            ".app-button { padding: 2px; border-radius: 8px; }\n"
            ".action-button { padding: 2px; border-radius: 6px; }\n");
    } else {
        asprintf(&css,
            "window, eventbox { background-color: %s; }\n"
            "label { color: %s; }\n"
            ".menu-window { background-color: %s; border: 1px solid %s; padding: 5px 8px 8px 8px; }\n"
            ".category-list { background-color: %s; padding: 2px; border-radius: 8px; }\n"
            ".category-list row { background-color: %s; color: %s; border-radius: 6px; padding: 2px; margin: 1px; min-height: 26px; }\n"
            ".category-list row:hover { background-color: %s; }\n"
            ".category-list row:selected, .category-list row.selected-category { background-color: %s; color: %s; }\n"
            "button { background-image: none; background-color: %s; color: %s; border: none; border-radius: 8px; padding: 2px; }\n"
            "button:hover { background-image: none; background-color: %s; }\n"
            "button.action-button { background-image: none; background-color: %s; color: %s; border-radius: 6px; min-width: 28px; min-height: 24px; }\n"
            ".app-button { min-width: %dpx; }\n"
            "entry { background-color: %s; color: %s; border: 1px solid %s; border-radius: 8px; }\n"
            "menu, menuitem { background-color: %s; color: %s; }\n"
            "menuitem:hover { background-color: %s; }\n",
            s->config.background, s->config.text_normal, s->config.background, s->config.border,
            s->config.categories_background, s->config.categories_background, s->config.text_normal,
            s->config.hover_background, s->config.selected_background, s->config.selected_text,
            s->config.button_normal_background, s->config.button_text, s->config.hover_background,
            s->config.button_normal_background, s->config.button_text,
            s->config.icon_size + 18, s->config.button_normal_background, s->config.text_normal, s->config.border,
            s->config.background, s->config.text_normal, s->config.hover_background);
    }
    if (!css) return;
    GtkCssProvider *provider = gtk_css_provider_new();
    GError *err = NULL;
    gtk_css_provider_load_from_data(provider, css, -1, &err);
    if (err) { fprintf(stderr, "CSS: %s\n", err->message); g_error_free(err); }
    gtk_style_context_add_provider_for_screen(gdk_screen_get_default(), GTK_STYLE_PROVIDER(provider), GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);
    g_object_unref(provider);
    free(css);
}

/*
 * JWM/X11 does not always move keyboard focus when the user clicks the root
 * desktop.  A focus-out handler alone therefore cannot make a start menu
 * behave like a real popup menu.  While PyMenu is visible we grab pointer
 * button events.  Clicks outside the menu are delivered to this window and
 * can be used to close it reliably.
 */
static void release_pointer_grab(MenuState *s) {
    if (!s || !s->pointer_grabbed) return;
    gdk_pointer_ungrab(GDK_CURRENT_TIME);
    gtk_grab_remove(s->window);
    s->pointer_grabbed = 0;
}

static gboolean acquire_pointer_grab(gpointer data) {
    MenuState *s = data;
    if (s) s->grab_retry_source = 0;
    if (!s || !s->window || getenv("ESSORA_PYMENU_NO_AUTO_CLOSE")) return FALSE;

    GdkWindow *window = gtk_widget_get_window(s->window);
    if (!window) return FALSE;

    if (s->pointer_grabbed) release_pointer_grab(s);

    gtk_grab_add(s->window);
    GdkGrabStatus status = gdk_pointer_grab(
        window,
        TRUE,
        GDK_BUTTON_PRESS_MASK | GDK_BUTTON_RELEASE_MASK,
        NULL,
        NULL,
        GDK_CURRENT_TIME
    );

    if (status == GDK_GRAB_SUCCESS) {
        s->pointer_grabbed = 1;
        s->grab_attempts = 0;
    } else {
        gtk_grab_remove(s->window);
        /* The window may not yet be viewable during its first idle cycle. */
        if (s->grab_attempts++ < 10) {
            s->grab_retry_source = g_timeout_add(50, acquire_pointer_grab, s);
        } else {
            fprintf(stderr, "PyMenu: no se pudo capturar el puntero (%d)\n", (int)status);
        }
    }

    return FALSE;
}

static void reacquire_pointer_grab(MenuState *s) {
    if (!s || getenv("ESSORA_PYMENU_NO_AUTO_CLOSE")) return;
    if (s->grab_retry_source) g_source_remove(s->grab_retry_source);
    s->grab_retry_source = 0;
    s->grab_attempts = 0;
    g_idle_add(acquire_pointer_grab, s);
}

static void show_error_dialog(MenuState *s, const char *message) {
    int had_grab = s && s->pointer_grabbed;
    if (s) {
        s->modal_dialog_active = 1;
        release_pointer_grab(s);
    }
    GtkWidget *d = gtk_message_dialog_new(s && s->window ? GTK_WINDOW(s->window) : NULL, GTK_DIALOG_MODAL, GTK_MESSAGE_ERROR, GTK_BUTTONS_CLOSE, "%s", message ? message : "Error");
    gtk_dialog_run(GTK_DIALOG(d));
    gtk_widget_destroy(d);
    if (s) {
        s->modal_dialog_active = 0;
        if (had_grab) reacquire_pointer_grab(s);
    }
}

static void clear_container(GtkWidget *container) {
    GList *children = gtk_container_get_children(GTK_CONTAINER(container));
    for (GList *l = children; l; l = l->next) gtk_widget_destroy(GTK_WIDGET(l->data));
    g_list_free(children);
}

static gboolean quit_later(gpointer data) { (void)data; gtk_main_quit(); return FALSE; }

static void launch_command_and_close(MenuState *s, const char *cmd) {
    (void)s;
    shell_launch(cmd);
    g_timeout_add(40, quit_later, NULL);
}

static void on_app_clicked(GtkWidget *button, gpointer data) {
    (void)button;
    AppSignalData *d = data;
    launch_command_and_close(d->state, d->app->exec);
}

static void sanitize_filename(const char *name, char *out, size_t cap) {
    size_t j=0;
    for (const unsigned char *p=(const unsigned char*)name; *p && j+1<cap; p++) {
        if (isalnum(*p) || *p=='-' || *p=='_') out[j++]=(char)*p;
        else if (*p==' ' && j && out[j-1]!='-') out[j++]='-';
    }
    if (!j) strcopy(out, cap, "application"); else out[j]='\0';
}

static void create_desktop_shortcut(MenuState *s, AppInfo *a) {
    const char *home = g_get_home_dir();
    char desktop[PATH_MAX];
    snprintf(desktop, sizeof(desktop), "%s/Desktop", home);
    if (!is_directory(desktop)) snprintf(desktop, sizeof(desktop), "%s/Escritorio", home);
    if (!is_directory(desktop)) g_mkdir_with_parents(desktop, 0755);
    char safe[256]; sanitize_filename(a->name, safe, sizeof(safe));
    char *path = NULL;
    if (asprintf(&path, "%s/%s.desktop", desktop, safe) < 0) return;
    char *content = NULL;
    asprintf(&content,
        "[Desktop Entry]\nType=Application\nVersion=1.0\nName=%s\nComment=%s\nExec=%s\nIcon=%s\nTerminal=false\nCategories=Utility;\n",
        a->name, a->comment, a->exec, a->icon);
    if (content && write_file(path, content, 0755) == 0) {
        char *msg=NULL; asprintf(&msg, "%s\n%s", tr(s,"Acceso directo creado:"), path);
        int had_grab = s->pointer_grabbed;
        s->modal_dialog_active = 1;
        release_pointer_grab(s);
        GtkWidget *d=gtk_message_dialog_new(GTK_WINDOW(s->window),GTK_DIALOG_MODAL,GTK_MESSAGE_INFO,GTK_BUTTONS_CLOSE,"%s",msg);
        gtk_dialog_run(GTK_DIALOG(d)); gtk_widget_destroy(d); free(msg);
        s->modal_dialog_active = 0;
        if (had_grab) reacquire_pointer_grab(s);
    }
    free(content);
    free(path);
}

static void on_context_run(GtkWidget *item, gpointer data) { (void)item; AppSignalData *d=data; on_app_clicked(d->button,d); }
static void on_context_shortcut(GtkWidget *item, gpointer data) { (void)item; AppSignalData *d=data; create_desktop_shortcut(d->state,d->app); }
static void on_context_deactivate(GtkWidget *menu, gpointer data) {
    (void)menu;
    MenuState *s=data;
    s->context_menu_active=0;
    reacquire_pointer_grab(s);
}

static gboolean on_app_button_press(GtkWidget *button, GdkEventButton *event, gpointer data) {
    (void)button;
    AppSignalData *d = data;
    if (!event || event->button != 3) return FALSE;
    d->state->context_menu_active = 1;
    release_pointer_grab(d->state);
    GtkWidget *menu = gtk_menu_new();
    GtkWidget *run = gtk_menu_item_new_with_label(tr(d->state,"Run"));
    GtkWidget *sep = gtk_separator_menu_item_new();
    GtkWidget *shortcut = gtk_menu_item_new_with_label(tr(d->state,"Create desktop shortcut"));
    gtk_menu_shell_append(GTK_MENU_SHELL(menu), run);
    gtk_menu_shell_append(GTK_MENU_SHELL(menu), sep);
    gtk_menu_shell_append(GTK_MENU_SHELL(menu), shortcut);
    g_signal_connect_data(run,"activate",G_CALLBACK(on_context_run),d,NULL,0);
    g_signal_connect_data(shortcut,"activate",G_CALLBACK(on_context_shortcut),d,NULL,0);
    g_signal_connect_data(menu,"deactivate",G_CALLBACK(on_context_deactivate),d->state,NULL,0);
    gtk_widget_show_all(menu);
    gtk_menu_popup_at_pointer(GTK_MENU(menu), event);
    return TRUE;
}

static GtkWidget *create_app_button(MenuState *s, AppInfo *a) {
    GtkWidget *button = gtk_button_new();
    gtk_button_set_relief(GTK_BUTTON(button), GTK_RELIEF_NONE);
    gtk_widget_set_can_focus(button, TRUE);
    gtk_style_context_add_class(gtk_widget_get_style_context(button), "app-button");
    GtkWidget *box = gtk_box_new(GTK_ORIENTATION_VERTICAL, 2);
    gtk_widget_set_margin_top(box, 4); gtk_widget_set_margin_bottom(box, 4);
    GtkWidget *img = image_for_icon(s, a->icon, s->config.icon_size);
    gtk_box_pack_start(GTK_BOX(box), img, FALSE, FALSE, 0);
    GtkWidget *label = gtk_label_new(a->name);
    set_font(label, s, s->config.font_size_names);
    gtk_label_set_line_wrap(GTK_LABEL(label), TRUE);
    gtk_label_set_max_width_chars(GTK_LABEL(label), 11);
    gtk_label_set_lines(GTK_LABEL(label), 2);
    gtk_label_set_ellipsize(GTK_LABEL(label), PANGO_ELLIPSIZE_END);
    gtk_label_set_justify(GTK_LABEL(label), GTK_JUSTIFY_CENTER);
    gtk_widget_set_halign(label, GTK_ALIGN_CENTER);
    gtk_box_pack_start(GTK_BOX(box), label, FALSE, FALSE, 0);
    gtk_container_add(GTK_CONTAINER(button), box);
    gtk_widget_set_tooltip_text(button, a->comment);
    AppSignalData *d = calloc(1,sizeof(*d)); d->state=s; d->app=a; d->button=button;
    g_signal_connect_data(button,"clicked",G_CALLBACK(on_app_clicked),d,NULL,0);
    gtk_widget_add_events(button, GDK_BUTTON_PRESS_MASK);
    g_signal_connect_data(button,"button-press-event",G_CALLBACK(on_app_button_press),d,NULL,0);
    return button;
}

static gboolean load_batch(gpointer data) {
    LoadContext *lc = data;
    MenuState *s = lc->state;
    if (lc->generation != s->load_generation || !s->apps_flow) {
        if (lc->owns_search_array) free(lc->search_apps);
        free(lc); return FALSE;
    }
    size_t total = lc->search_apps ? lc->search_count : lc->category->app_count;
    size_t end = MIN(total, lc->index + LOAD_BATCH);
    for (; lc->index < end; lc->index++) {
        AppInfo *a = lc->search_apps ? lc->search_apps[lc->index] : lc->category->apps[lc->index];
        GtkWidget *b = create_app_button(s,a);
        gtk_container_add(GTK_CONTAINER(s->apps_flow),b);
    }
    gtk_widget_show_all(s->apps_flow);
    if (lc->index < total) return TRUE;
    if (lc->owns_search_array) free(lc->search_apps);
    free(lc);
    return FALSE;
}

static void show_category(MenuState *s, Category *c) {
    if (!s->apps_flow || !c) return;
    s->load_generation++;
    clear_container(s->apps_flow);
    s->current_category = c;
    LoadContext *lc = calloc(1,sizeof(*lc));
    lc->state=s; lc->category=c; lc->generation=s->load_generation;
    g_idle_add(load_batch,lc);
}

static void select_category(MenuState *s, Category *c) {
    if (!c) return;
    if (s->selected_category && s->selected_category->row)
        gtk_style_context_remove_class(gtk_widget_get_style_context(s->selected_category->row),"selected-category");
    s->selected_category=c;
    if (c->row) {
        gtk_style_context_add_class(gtk_widget_get_style_context(c->row),"selected-category");
        gtk_list_box_select_row(GTK_LIST_BOX(s->categories_list),GTK_LIST_BOX_ROW(c->row));
    }
    show_category(s,c);
}

static void on_category_row_activated(GtkListBox *box, GtkListBoxRow *row, gpointer data) {
    (void)box;
    MenuState *s=data;
    for(size_t i=0;i<s->category_count;i++) if(s->categories[i]->row==GTK_WIDGET(row)){ select_category(s,s->categories[i]); break; }
}

static gboolean hover_activate(gpointer data) {
    CategorySignalData *d=data;
    d->state->hover_source=0;
    show_category(d->state,d->category);
    free(d);
    return FALSE;
}

static gboolean on_category_enter(GtkWidget *w, gpointer event, gpointer data) {
    (void)w;(void)event;
    Category *c=data; MenuState *s=c->state;
    if (s->hover_source) g_source_remove(s->hover_source);
    CategorySignalData *d=calloc(1,sizeof(*d));d->state=s;d->category=c;
    s->hover_source=g_timeout_add(120,hover_activate,d);
    return FALSE;
}

static gboolean on_category_leave(GtkWidget *w, gpointer event, gpointer data) {
    (void)w;(void)event;
    Category *c=data; MenuState *s=c->state;
    if(s->hover_source){g_source_remove(s->hover_source);s->hover_source=0;}
    return FALSE;
}

static GtkWidget *create_categories_sidebar(MenuState *s) {
    GtkWidget *sc = gtk_scrolled_window_new(NULL,NULL);
    gtk_scrolled_window_set_policy(GTK_SCROLLED_WINDOW(sc),GTK_POLICY_NEVER,GTK_POLICY_AUTOMATIC);
    s->categories_list=gtk_list_box_new();
    gtk_list_box_set_selection_mode(GTK_LIST_BOX(s->categories_list),GTK_SELECTION_SINGLE);
    gtk_style_context_add_class(gtk_widget_get_style_context(s->categories_list),"category-list");
    g_signal_connect_data(s->categories_list,"row-activated",G_CALLBACK(on_category_row_activated),s,NULL,0);
    for(size_t i=0;i<s->category_count;i++){
        Category *c=s->categories[i];
        GtkWidget *row=gtk_list_box_row_new(); c->row=row;
        GtkWidget *ev=gtk_event_box_new(); gtk_event_box_set_above_child(ev,TRUE);
        GtkWidget *box=gtk_box_new(GTK_ORIENTATION_HORIZONTAL,5);
        gtk_widget_set_margin_start(box,3);gtk_widget_set_margin_end(box,3);gtk_widget_set_margin_top(box,2);gtk_widget_set_margin_bottom(box,2);
        const char *category_icon = c->icon;
        if (!strcasecmp(c->label, "Favorites") || !strcasecmp(c->label, "Favoritos"))
            category_icon = INSTALL_DIR "/icon-pymenu/favorites-leaf.svg";
        GtkWidget *img=image_for_icon(s,category_icon,s->config.category_icon_size);
        gtk_box_pack_start(GTK_BOX(box),img,FALSE,FALSE,0);
        if(!s->config.hide_category_text){
            GtkWidget *label=gtk_label_new(tr(s,c->label));set_font(label,s,s->config.font_size_categories);
            gtk_label_set_xalign(GTK_LABEL(label),0.0f);gtk_box_pack_start(GTK_BOX(box),label,TRUE,TRUE,3);
        } else gtk_widget_set_tooltip_text(row,tr(s,c->label));
        gtk_container_add(GTK_CONTAINER(ev),box);gtk_container_add(GTK_CONTAINER(row),ev);gtk_container_add(GTK_CONTAINER(s->categories_list),row);
        gtk_widget_add_events(ev,GDK_ENTER_NOTIFY_MASK|GDK_LEAVE_NOTIFY_MASK);
        g_signal_connect_data(ev,"enter-notify-event",G_CALLBACK(on_category_enter),c,NULL,0);
        g_signal_connect_data(ev,"leave-notify-event",G_CALLBACK(on_category_leave),c,NULL,0);
    }
    gtk_container_add(GTK_CONTAINER(sc),s->categories_list);
    return sc;
}

static void closure_free(gpointer data, gpointer closure) { (void)closure; free(data); }
static void on_place_clicked(GtkWidget *button, gpointer data) { (void)button; open_directory_path((const char*)data); g_timeout_add(50,quit_later,NULL); }

static GtkWidget *create_place_button(MenuState *s,const char *icon,const char *label,const char *path){
    GtkWidget *b=gtk_button_new();gtk_button_set_relief(GTK_BUTTON(b),GTK_RELIEF_NONE);
    GtkWidget *box=gtk_box_new(GTK_ORIENTATION_HORIZONTAL,8);gtk_widget_set_margin_start(box,5);
    GtkWidget *img=image_for_icon(s,icon,22);GtkWidget *l=gtk_label_new(label);set_font(l,s,s->config.font_size_categories);gtk_label_set_xalign(GTK_LABEL(l),0.0f);
    gtk_box_pack_start(GTK_BOX(box),img,FALSE,FALSE,0);gtk_box_pack_start(GTK_BOX(box),l,TRUE,TRUE,0);gtk_container_add(GTK_CONTAINER(b),box);
    g_signal_connect_data(b,"clicked",G_CALLBACK(on_place_clicked),xstrdup(path),closure_free,0);
    return b;
}

static void on_favorite_clicked(GtkWidget *button,gpointer data){(void)button;Favorite *f=data;shell_launch(f->exec);g_timeout_add(50,quit_later,NULL);}
static void on_profile_clicked(GtkWidget *button,gpointer data){(void)button;MenuState*s=data;launch_command_and_close(s,s->config.profile_manager);}

static GtkWidget *create_profile_widget(MenuState *s){
    GtkWidget *box=gtk_box_new(GTK_ORIENTATION_VERTICAL,3);gtk_widget_set_halign(box,GTK_ALIGN_CENTER);
    if(!s->config.hide_profile_pic){
        GtkWidget*b=gtk_button_new();gtk_button_set_relief(GTK_BUTTON(b),GTK_RELIEF_NONE);
        const char *pic=file_exists(s->face_path)?s->face_path:s->config.profile_pic;
        GtkWidget*img=image_for_icon(s,pic,s->config.profile_pic_size);gtk_container_add(GTK_CONTAINER(b),img);gtk_widget_set_tooltip_text(b,tr(s,"Select avatar"));
        g_signal_connect_data(b,"clicked",G_CALLBACK(on_profile_clicked),s,NULL,0);gtk_box_pack_start(GTK_BOX(box),b,FALSE,FALSE,0);
    }
    char host[256]="";FILE*f=fopen("/etc/hostname","r");if(f){fgets(host,sizeof(host),f);fclose(f);char*t=trim(host);memmove(host,t,strlen(t)+1);}if(!*host)strcopy(host,sizeof(host),g_get_user_name());
    GtkWidget*hbox=gtk_box_new(GTK_ORIENTATION_HORIZONTAL,5);GtkWidget*hi=image_for_icon(s,INSTALL_DIR "/icon-pymenu/computer.svg",18);GtkWidget*hl=gtk_label_new(host);set_font(hl,s,s->config.font_size_header);
    gtk_box_pack_start(GTK_BOX(hbox),hi,FALSE,FALSE,0);gtk_box_pack_start(GTK_BOX(hbox),hl,FALSE,FALSE,0);gtk_box_pack_start(GTK_BOX(box),hbox,FALSE,FALSE,0);
    return box;
}

static GtkWidget *create_places_sidebar(MenuState *s){
    GtkWidget*sc=gtk_scrolled_window_new(NULL,NULL);gtk_scrolled_window_set_policy(GTK_SCROLLED_WINDOW(sc),GTK_POLICY_NEVER,GTK_POLICY_AUTOMATIC);
    GtkWidget*box=gtk_box_new(GTK_ORIENTATION_VERTICAL,4);gtk_widget_set_margin_start(box,5);gtk_widget_set_margin_end(box,5);gtk_widget_set_margin_top(box,3);gtk_widget_set_margin_bottom(box,5);
    if(s->config.profile_in_places){gtk_box_pack_start(GTK_BOX(box),create_profile_widget(s),FALSE,FALSE,4);gtk_box_pack_start(GTK_BOX(box),gtk_separator_new(GTK_ORIENTATION_HORIZONTAL),FALSE,FALSE,3);}
    if(!s->config.hide_places){
        struct {const char*i,*l,*p;} places[]={
            {"user-home","Home","~"},{"folder-download","DownloadsDir","~/Downloads"},{"folder-music","MusicDir","~/Music"},
            {"folder-documents","DocumentsDir","~/Documents"},{"folder-pictures","PicturesDir","~/Pictures"},{"folder-videos","VideosDir","~/Videos"}
        };
        for(size_t i=0;i<sizeof(places)/sizeof(places[0]);i++)gtk_box_pack_start(GTK_BOX(box),create_place_button(s,places[i].i,tr(s,places[i].l),places[i].p),FALSE,FALSE,0);
    }
    if(!s->config.hide_places&&!s->config.hide_favorites&&s->config.favorite_count){
        gtk_box_pack_start(GTK_BOX(box),gtk_separator_new(GTK_ORIENTATION_HORIZONTAL),FALSE,FALSE,4);
        GtkWidget*title=gtk_box_new(GTK_ORIENTATION_HORIZONTAL,5);GtkWidget*ti=image_for_icon(s,INSTALL_DIR "/icon-pymenu/favorites-leaf.svg",18);GtkWidget*tl=gtk_label_new(tr(s,"Favorites"));set_font(tl,s,s->config.font_size_categories);
        gtk_box_pack_start(GTK_BOX(title),ti,FALSE,FALSE,0);gtk_box_pack_start(GTK_BOX(title),tl,FALSE,FALSE,0);gtk_box_pack_start(GTK_BOX(box),title,FALSE,FALSE,2);
        for(size_t i=0;i<s->config.favorite_count;i++){
            Favorite*fav=&s->config.favorites[i];GtkWidget*b=gtk_button_new();gtk_button_set_relief(GTK_BUTTON(b),GTK_RELIEF_NONE);GtkWidget*h=gtk_box_new(GTK_ORIENTATION_HORIZONTAL,8);gtk_widget_set_margin_start(h,5);
            gtk_box_pack_start(GTK_BOX(h),image_for_icon(s,fav->icon,20),FALSE,FALSE,0);GtkWidget*l=gtk_label_new(fav->name);set_font(l,s,s->config.font_size_categories);gtk_label_set_xalign(GTK_LABEL(l),0);gtk_box_pack_start(GTK_BOX(h),l,TRUE,TRUE,0);gtk_container_add(GTK_CONTAINER(b),h);
            g_signal_connect_data(b,"clicked",G_CALLBACK(on_favorite_clicked),fav,NULL,0);gtk_box_pack_start(GTK_BOX(box),b,FALSE,FALSE,0);
        }
    }
    gtk_container_add(GTK_CONTAINER(sc),box);return sc;
}

static void get_os_info(char *os_name,size_t oscap,char *kernel,size_t kcap){
    strcopy(os_name,oscap,"Linux");char*data=read_file("/etc/os-release",NULL);if(data){char*p=strstr(data,"PRETTY_NAME=");if(p){p+=12;char*e=strpbrk(p,"\r\n");if(e)*e='\0';p=trim(p);if(*p=='"'){p++;char*q=strrchr(p,'"');if(q)*q='\0';}strcopy(os_name,oscap,p);}free(data);}struct utsname u;if(uname(&u)==0)strcopy(kernel,kcap,u.release);else strcopy(kernel,kcap,"Unknown");}

static GtkWidget *system_info_line(MenuState*s,const char*icon,const char*text){GtkWidget*b=gtk_box_new(GTK_ORIENTATION_HORIZONTAL,6);gtk_box_pack_start(GTK_BOX(b),image_for_icon(s,icon,18),FALSE,FALSE,0);GtkWidget*l=gtk_label_new(text);set_font(l,s,s->config.font_size_header);gtk_label_set_xalign(GTK_LABEL(l),0);gtk_box_pack_start(GTK_BOX(b),l,TRUE,TRUE,0);return b;}

static GtkWidget *create_header(MenuState*s){
    GtkWidget*b=gtk_box_new(GTK_ORIENTATION_HORIZONTAL,20);gtk_widget_set_margin_start(b,5);gtk_widget_set_margin_end(b,5);gtk_widget_set_margin_top(b,2);gtk_widget_set_margin_bottom(b,2);
    if(!s->config.profile_in_places&&!s->config.hide_profile_pic)gtk_box_pack_start(GTK_BOX(b),create_profile_widget(s),FALSE,FALSE,0);
    GtkWidget*info=gtk_box_new(GTK_ORIENTATION_VERTICAL,3);char osn[256],ker[256],host[256]="";get_os_info(osn,sizeof(osn),ker,sizeof(ker));FILE*f=fopen("/etc/hostname","r");if(f){fgets(host,sizeof(host),f);fclose(f);char*t=trim(host);memmove(host,t,strlen(t)+1);}
    if(!s->config.hide_os_name)gtk_box_pack_start(GTK_BOX(info),system_info_line(s,"computer",osn),FALSE,FALSE,0);
    if(!s->config.hide_kernel)gtk_box_pack_start(GTK_BOX(info),system_info_line(s,INSTALL_DIR "/icon-pymenu/kernel.svg",ker),FALSE,FALSE,0);
    if(!s->config.hide_hostname)gtk_box_pack_start(GTK_BOX(info),system_info_line(s,INSTALL_DIR "/icon-pymenu/computer.svg",host),FALSE,FALSE,0);
    gtk_box_pack_start(GTK_BOX(b),info,TRUE,TRUE,0);return b;
}

static void on_search_changed(GtkEntry *entry,gpointer data){
    MenuState*s=data;const char*q=gtk_entry_get_text(entry);if(!q)q="";while(*q&&isspace((unsigned char)*q))q++;
    if(!*q){show_category(s,s->selected_category?s->selected_category:s->categories[0]);return;}
    char*low=g_ascii_strdown(q,-1);size_t cap=32,n=0;AppInfo**arr=malloc(cap*sizeof(*arr));
    for(size_t i=0;i<s->category_count;i++)for(size_t j=0;j<s->categories[i]->app_count;j++){
        AppInfo*a=s->categories[i]->apps[j];char*nn=g_ascii_strdown(a->name,-1);char*cc=g_ascii_strdown(a->comment,-1);
        if(strstr(nn,low)||strstr(cc,low)){if(n==cap){cap*=2;arr=realloc(arr,cap*sizeof(*arr));}arr[n++]=a;}g_free(nn);g_free(cc);
    }g_free(low);s->load_generation++;clear_container(s->apps_flow);LoadContext*lc=calloc(1,sizeof(*lc));lc->state=s;lc->generation=s->load_generation;lc->search_apps=arr;lc->search_count=n;lc->owns_search_array=1;g_idle_add(load_batch,lc);
}

static char *url_encode(const char*s){size_t n=1;for(const unsigned char*p=(const unsigned char*)s;*p;p++)n+=isalnum(*p)||strchr("-_.~",*p)?1:3;char*out=malloc(n),*o=out;static const char*h="0123456789ABCDEF";for(const unsigned char*p=(const unsigned char*)s;*p;p++){if(isalnum(*p)||strchr("-_.~",*p))*o++=*p;else if(*p==' ')*o++='+';else{*o++='%';*o++=h[*p>>4];*o++=h[*p&15];}}*o=0;return out;}
static void on_web_search(GtkWidget*b,gpointer data){(void)b;MenuState*s=data;const char*q=gtk_entry_get_text(GTK_ENTRY(s->search_entry));if(!q||!*q)return;char*e=url_encode(q);char*cmd=NULL;if(file_exists("/usr/local/bin/defaultbrowser")||file_exists("/usr/bin/defaultbrowser"))asprintf(&cmd,"defaultbrowser --new-tab 'https://www.google.com/search?q=%s'",e);else asprintf(&cmd,"xdg-open 'https://www.google.com/search?q=%s'",e);launch_command_and_close(s,cmd);free(cmd);free(e);}
static void on_config(GtkWidget*b,gpointer data){(void)b;MenuState*s=data;launch_command_and_close(s,CONFIGURATOR);}
static void on_shutdown(GtkWidget*b,gpointer data){(void)b;MenuState*s=data;launch_command_and_close(s,s->config.shutdown_cmd);}

static gboolean delayed_reload(gpointer data);
static void on_update(GtkWidget*b,gpointer data){(void)b;MenuState*s=data;char cmd[PATH_MAX+64];snprintf(cmd,sizeof(cmd),"%s --debug",MENU_GENERATOR);shell_launch(cmd);if(s->reload_source)g_source_remove(s->reload_source);s->reload_source=g_timeout_add(1200,delayed_reload,s);}

static GtkWidget *action_button(MenuState*s,const char*icon,const char*tip,GCallback cb){GtkWidget*b=gtk_button_new();gtk_style_context_add_class(gtk_widget_get_style_context(b),"action-button");gtk_container_add(GTK_CONTAINER(b),image_for_icon(s,icon,20));gtk_widget_set_tooltip_text(b,tr(s,tip));g_signal_connect_data(b,"clicked",cb,s,NULL,0);return b;}

static GtkWidget *create_search_bar(MenuState*s){GtkWidget*b=gtk_box_new(GTK_ORIENTATION_HORIZONTAL,8);gtk_widget_set_margin_start(b,4);gtk_widget_set_margin_end(b,4);gtk_widget_set_margin_top(b,4);gtk_widget_set_margin_bottom(b,4);s->search_entry=gtk_search_entry_new();gtk_entry_set_placeholder_text(GTK_ENTRY(s->search_entry),tr(s,"Search applications..."));gtk_widget_set_tooltip_text(s->search_entry,tr(s,"Search applications..."));gtk_widget_set_size_request(s->search_entry,180,28);g_signal_connect_data(s->search_entry,"search-changed",G_CALLBACK(on_search_changed),s,NULL,0);gtk_box_pack_start(GTK_BOX(b),s->search_entry,TRUE,TRUE,0);gtk_box_pack_start(GTK_BOX(b),action_button(s,INSTALL_DIR "/icon-pymenu/menu-update.png","Menu update",G_CALLBACK(on_update)),FALSE,FALSE,0);gtk_box_pack_end(GTK_BOX(b),action_button(s,"preferences-desktop-essora","Shutdown",G_CALLBACK(on_shutdown)),FALSE,FALSE,0);gtk_box_pack_end(GTK_BOX(b),action_button(s,"preferences-system-search-essora","Search in the web",G_CALLBACK(on_web_search)),FALSE,FALSE,0);gtk_box_pack_end(GTK_BOX(b),action_button(s,"preferences-system-essora","Pymenu config",G_CALLBACK(on_config)),FALSE,FALSE,0);return b;}

static GtkWidget *create_apps_area(MenuState*s){GtkWidget*main=gtk_box_new(GTK_ORIENTATION_VERTICAL,0);if(!strcmp(s->config.search_bar_container,"apps_column")&&!strcmp(s->config.search_bar_position,"top")){gtk_box_pack_start(GTK_BOX(main),create_search_bar(s),FALSE,FALSE,0);gtk_box_pack_start(GTK_BOX(main),gtk_separator_new(GTK_ORIENTATION_HORIZONTAL),FALSE,FALSE,0);}GtkWidget*sc=gtk_scrolled_window_new(NULL,NULL);gtk_scrolled_window_set_policy(GTK_SCROLLED_WINDOW(sc),GTK_POLICY_NEVER,GTK_POLICY_AUTOMATIC);s->apps_flow=gtk_flow_box_new();gtk_flow_box_set_max_children_per_line(GTK_FLOW_BOX(s->apps_flow),30);gtk_flow_box_set_selection_mode(GTK_FLOW_BOX(s->apps_flow),GTK_SELECTION_SINGLE);gtk_widget_set_valign(s->apps_flow,GTK_ALIGN_START);gtk_widget_set_margin_start(s->apps_flow,5);gtk_widget_set_margin_end(s->apps_flow,5);gtk_widget_set_margin_top(s->apps_flow,8);gtk_widget_set_margin_bottom(s->apps_flow,8);gtk_container_add(GTK_CONTAINER(sc),s->apps_flow);gtk_box_pack_start(GTK_BOX(main),sc,TRUE,TRUE,0);if(!strcmp(s->config.search_bar_container,"apps_column")&&strcmp(s->config.search_bar_position,"top")){gtk_box_pack_start(GTK_BOX(main),gtk_separator_new(GTK_ORIENTATION_HORIZONTAL),FALSE,FALSE,0);gtk_box_pack_start(GTK_BOX(main),create_search_bar(s),FALSE,FALSE,0);}return main;}

static void build_interface(MenuState*s){
    s->rebuilding=1;
    if(s->main_box){gtk_widget_destroy(s->main_box);s->main_box=NULL;}
    s->main_box=gtk_box_new(GTK_ORIENTATION_VERTICAL,0);gtk_style_context_add_class(gtk_widget_get_style_context(s->main_box),"menu-window");gtk_container_add(GTK_CONTAINER(s->window),s->main_box);
    if(!s->config.hide_header){gtk_box_pack_start(GTK_BOX(s->main_box),create_header(s),FALSE,FALSE,0);gtk_box_pack_start(GTK_BOX(s->main_box),gtk_separator_new(GTK_ORIENTATION_HORIZONTAL),FALSE,FALSE,0);}
    GtkWidget*content=gtk_box_new(GTK_ORIENTATION_HORIZONTAL,0);gtk_box_pack_start(GTK_BOX(s->main_box),content,TRUE,TRUE,0);
    int show_places=!s->config.hide_places||s->config.profile_in_places||(!s->config.hide_favorites&&s->config.favorite_count);
    if(show_places){gtk_box_pack_start(GTK_BOX(content),create_places_sidebar(s),FALSE,FALSE,0);gtk_box_pack_start(GTK_BOX(content),gtk_separator_new(GTK_ORIENTATION_VERTICAL),FALSE,FALSE,0);}
    gtk_box_pack_start(GTK_BOX(content),create_categories_sidebar(s),FALSE,FALSE,0);gtk_box_pack_start(GTK_BOX(content),gtk_separator_new(GTK_ORIENTATION_VERTICAL),FALSE,FALSE,0);gtk_box_pack_start(GTK_BOX(content),create_apps_area(s),TRUE,TRUE,0);
    if(strcmp(s->config.search_bar_container,"apps_column")){gtk_box_pack_start(GTK_BOX(s->main_box),gtk_separator_new(GTK_ORIENTATION_HORIZONTAL),FALSE,FALSE,0);gtk_box_pack_start(GTK_BOX(s->main_box),create_search_bar(s),FALSE,FALSE,0);}
    gtk_widget_show_all(s->main_box);select_category(s,s->categories[0]);if(s->search_entry)gtk_widget_grab_focus(s->search_entry);s->rebuilding=0;
}

static gboolean delayed_reload(gpointer data){MenuState*s=data;s->reload_source=0;char*err=NULL;if(!parse_menu_xml(s,&err)){if(err){show_error_dialog(s,err);free(err);}return FALSE;}build_interface(s);gtk_window_present(GTK_WINDOW(s->window));return FALSE;}

static void on_file_changed(GFileMonitor*m,GFile*f,GFile*other,GFileMonitorEvent event,gpointer data){(void)m;(void)f;(void)other;MenuState*s=data;if(event==G_FILE_MONITOR_EVENT_CHANGES_DONE_HINT||event==G_FILE_MONITOR_EVENT_CREATED||event==G_FILE_MONITOR_EVENT_CHANGED){if(s->reload_source)g_source_remove(s->reload_source);s->reload_source=g_timeout_add(250,delayed_reload,s);}}

static gboolean on_key(GtkWidget*w,GdkEventKey*e,gpointer data){(void)w;(void)data;if(e&&(e->keyval==GDK_KEY_Escape)){gtk_main_quit();return TRUE;}return FALSE;}
static gboolean on_focus_out(GtkWidget*w,GdkEventFocus*e,gpointer data){(void)w;(void)e;MenuState*s=data;if(getenv("ESSORA_PYMENU_NO_AUTO_CLOSE"))return FALSE;if(!s->context_menu_active&&!s->modal_dialog_active&&!s->rebuilding)gtk_main_quit();return FALSE;}

static gboolean click_is_outside(MenuState *s, GdkEventButton *e) {
    if (!s || !s->window || !e) return FALSE;
    gint x=0,y=0,width=0,height=0;
    gtk_window_get_position(GTK_WINDOW(s->window),&x,&y);
    gtk_window_get_size(GTK_WINDOW(s->window),&width,&height);
    return e->x_root < x || e->y_root < y ||
           e->x_root >= x + width || e->y_root >= y + height;
}

static gboolean on_window_button(GtkWidget*w,GdkEventButton*e,gpointer data){
    MenuState*s=data;
    if(!e)return FALSE;
    if(!getenv("ESSORA_PYMENU_NO_AUTO_CLOSE")&&s->pointer_grabbed&&!s->context_menu_active&&!s->modal_dialog_active&&!s->rebuilding&&click_is_outside(s,e)){
        gtk_main_quit();
        return TRUE;
    }
    if(e->button==2){gtk_main_quit();return TRUE;}
    if(e->button==1&&(e->state&GDK_MOD1_MASK)){gtk_window_begin_move_drag(GTK_WINDOW(w),e->button,(gint)e->x_root,(gint)e->y_root,e->time);return TRUE;}
    return FALSE;
}

static void on_destroy(GtkWidget*w,gpointer data){(void)w;MenuState*s=data;release_pointer_grab(s);gtk_main_quit();}
static gboolean disable_keep_above(gpointer data){gtk_window_set_keep_above(GTK_WINDOW(data),FALSE);return FALSE;}

static void setup_window(MenuState*s){
    s->window=gtk_window_new(GTK_WINDOW_TOPLEVEL);gtk_window_set_title(GTK_WINDOW(s->window),APP_NAME);gtk_window_set_default_size(GTK_WINDOW(s->window),s->config.width,s->config.height);gtk_window_set_resizable(GTK_WINDOW(s->window),TRUE);gtk_window_set_decorated(GTK_WINDOW(s->window),s->config.decorated_window);gtk_window_set_skip_taskbar_hint(GTK_WINDOW(s->window),TRUE);gtk_window_set_skip_pager_hint(GTK_WINDOW(s->window),TRUE);gtk_window_set_type_hint(GTK_WINDOW(s->window),GDK_WINDOW_TYPE_HINT_DIALOG);gtk_window_set_icon_name(GTK_WINDOW(s->window),"applications-system");
    GdkScreen*screen=gdk_screen_get_default();GdkVisual*v=gdk_screen_get_rgba_visual(screen);if(v&&gdk_screen_is_composited(screen)){gtk_widget_set_visual(s->window,v);gtk_widget_set_app_paintable(s->window,TRUE);}int sw=gdk_screen_get_width(screen),sh=gdk_screen_get_height(screen),x,y;if(s->explicit_x>=0&&s->explicit_y>=0){x=s->explicit_x;y=s->explicit_y;}else{x=!strcmp(s->config.halign,"left")?10:!strcmp(s->config.halign,"right")?sw-s->config.width-10:(sw-s->config.width)/2;y=!strcmp(s->tray.valign,"top")?s->tray.height:!strcmp(s->tray.valign,"bottom")?sh-s->tray.height-s->config.height:(sh-s->config.height)/2;}x=MAX(0,MIN(x,MAX(0,sw-s->config.width)));y=MAX(0,MIN(y,MAX(0,sh-s->config.height)));gtk_window_move(GTK_WINDOW(s->window),x,y);
    g_signal_connect_data(s->window,"destroy",G_CALLBACK(on_destroy),s,NULL,0);g_signal_connect_data(s->window,"key-press-event",G_CALLBACK(on_key),s,NULL,0);g_signal_connect_data(s->window,"focus-out-event",G_CALLBACK(on_focus_out),s,NULL,0);g_signal_connect_data(s->window,"button-press-event",G_CALLBACK(on_window_button),s,NULL,0);gtk_widget_add_events(s->window,GDK_BUTTON_PRESS_MASK);gtk_window_set_keep_above(GTK_WINDOW(s->window),TRUE);g_timeout_add(500,disable_keep_above,s->window);
}

static void setup_monitor(MenuState*s){GError*err=NULL;s->menu_file=g_file_new_for_path(s->menu_path);s->menu_monitor=g_file_monitor_file(s->menu_file,G_FILE_MONITOR_NONE,NULL,&err);if(s->menu_monitor)g_signal_connect_data(s->menu_monitor,"changed",G_CALLBACK(on_file_changed),s,NULL,0);if(err){fprintf(stderr,"Monitor: %s\n",err->message);g_error_free(err);}}

static void cleanup(MenuState*s){if(!s)return;release_pointer_grab(s);if(s->hover_source)g_source_remove(s->hover_source);if(s->reload_source)g_source_remove(s->reload_source);if(s->grab_retry_source)g_source_remove(s->grab_retry_source);if(s->menu_monitor)g_object_unref(s->menu_monitor);if(s->menu_file)g_object_unref(s->menu_file);clear_menu_data(s);free_favorites(&s->config);free_excluded(&s->config);if(s->translations)g_hash_table_destroy(s->translations);if(s->icon_cache)g_hash_table_destroy(s->icon_cache);free(s);}

int main(int argc,char**argv){
    MenuState*s=calloc(1,sizeof(*s));if(!s)return 1;global_state=s;s->explicit_x=s->explicit_y=-1;if(argc>=3){char*e1,*e2;long x=strtol(argv[1],&e1,10),y=strtol(argv[2],&e2,10);if(*e1=='\0'&&*e2=='\0'){s->explicit_x=(int)x;s->explicit_y=(int)y;}}
    gtk_init(&argc,&argv);ensure_config_paths(s);load_config(s);load_translations(s);s->icon_cache=g_hash_table_new_full(g_str_hash,g_str_equal,g_free,(GDestroyNotify)g_object_unref);char*err=NULL;if(!parse_menu_xml(s,&err)){setup_window(s);show_error_dialog(s,err?err:"No se pudo leer essora-menu.xml");free(err);cleanup(s);return 1;}apply_css(s);setup_window(s);build_interface(s);setup_monitor(s);gtk_widget_show_all(s->window);gtk_window_present(GTK_WINDOW(s->window));if(s->search_entry)gtk_widget_grab_focus(s->search_entry);reacquire_pointer_grab(s);gtk_main();cleanup(s);return 0;
}
