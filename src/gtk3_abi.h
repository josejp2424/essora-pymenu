#ifndef ESSORA_GTK3_ABI_H
#define ESSORA_GTK3_ABI_H

/*
 * Minimal GTK3/GLib ABI declarations used only to make Essora PyMenu
 * buildable on lightweight Puppy/Essora systems that have GTK3 runtime
 * libraries but not the development headers. GTK3 and GLib keep ABI
 * compatibility across the 3.x/2.x series.
 *
 * When the normal development headers are present, define
 * ESSORA_USE_SYSTEM_GTK_HEADERS and the source will use them instead.
 */

#include <stddef.h>
#include <stdint.h>
#include <stdarg.h>

typedef int gboolean;
typedef int gint;
typedef unsigned int guint;
typedef unsigned long gulong;
typedef long glong;
typedef uint32_t guint32;
typedef int32_t gint32;
typedef int8_t gint8;
typedef size_t gsize;
typedef ptrdiff_t gssize;
typedef double gdouble;
typedef uint16_t guint16;
typedef uint8_t guint8;
typedef int16_t gint16;
typedef char gchar;
typedef unsigned char guchar;
typedef void *gpointer;
typedef const void *gconstpointer;
typedef guint GQuark;
typedef guint GType;
typedef guint GConnectFlags;
typedef guint GdkModifierType;
typedef guint GdkEventMask;
typedef guint GtkIconLookupFlags;
typedef guint GtkStateFlags;
typedef guint GFileMonitorFlags;
typedef gint GFileMonitorEvent;
typedef gint GMarkupParseFlags;
typedef gint GdkWindowTypeHint;
typedef gint GdkGrabStatus;
typedef gint GtkWindowType;
typedef gint GtkOrientation;
typedef gint GtkAlign;
typedef gint GtkPolicyType;
typedef gint GtkSelectionMode;
typedef gint GtkReliefStyle;
typedef gint GtkIconSize;
typedef gint GtkJustification;
typedef gint PangoEllipsizeMode;
typedef gint GtkMessageType;
typedef gint GtkButtonsType;
typedef gint GtkDialogFlags;
typedef gint GtkResponseType;

typedef struct _GObject GObject;
typedef struct _GError { GQuark domain; gint code; gchar *message; } GError;
typedef struct _GList { gpointer data; struct _GList *next; struct _GList *prev; } GList;
typedef struct _GSList { gpointer data; struct _GSList *next; } GSList;
typedef struct _GHashTable GHashTable;
typedef struct _GMarkupParseContext GMarkupParseContext;
typedef struct _GFile GFile;
typedef struct _GFileMonitor GFileMonitor;
typedef struct _GCancellable GCancellable;
typedef struct _GtkWidget GtkWidget;
typedef struct _GtkWindow GtkWindow;
typedef struct _GtkBox GtkBox;
typedef struct _GtkContainer GtkContainer;
typedef struct _GtkBin GtkBin;
typedef struct _GtkListBox GtkListBox;
typedef struct _GtkListBoxRow GtkListBoxRow;
typedef struct _GtkFlowBox GtkFlowBox;
typedef struct _GtkFlowBoxChild GtkFlowBoxChild;
typedef struct _GtkButton GtkButton;
typedef struct _GtkLabel GtkLabel;
typedef struct _GtkEntry GtkEntry;
typedef struct _GtkImage GtkImage;
typedef struct _GtkScrolledWindow GtkScrolledWindow;
typedef struct _GtkMenuShell GtkMenuShell;
typedef struct _GtkMenu GtkMenu;
typedef struct _GtkMenuItem GtkMenuItem;
typedef struct _GtkStyleContext GtkStyleContext;
typedef struct _GtkCssProvider GtkCssProvider;
typedef struct _GtkIconTheme GtkIconTheme;
typedef struct _GtkDialog GtkDialog;
typedef struct _GdkScreen GdkScreen;
typedef struct _GdkDisplay GdkDisplay;
typedef struct _GdkMonitor GdkMonitor;
typedef struct _GdkVisual GdkVisual;
typedef struct _GdkWindow GdkWindow;
typedef struct _GdkDevice GdkDevice;
typedef struct _GdkCursor GdkCursor;
typedef struct _GdkPixbuf GdkPixbuf;
typedef struct _PangoFontDescription PangoFontDescription;

typedef struct { gint x, y, width, height; } GdkRectangle;
typedef struct { gint x, y, width, height; } GtkAllocation;

typedef struct {
    gint type; GdkWindow *window; gint8 send_event; guint32 time;
    gdouble x, y; gdouble *axes; guint state; guint button;
    GdkDevice *device; gdouble x_root, y_root;
} GdkEventButton;

typedef struct {
    gint type; GdkWindow *window; gint8 send_event; guint32 time;
    guint state; guint keyval; gint length; gchar *string;
    guint16 hardware_keycode; guint8 group; guint is_modifier;
} GdkEventKey;

typedef struct {
    gint type; GdkWindow *window; gint8 send_event; gint16 in;
} GdkEventFocus;

typedef void (*GCallback)(void);
typedef void (*GClosureNotify)(gpointer data, gpointer closure);
typedef gboolean (*GSourceFunc)(gpointer data);
typedef void (*GDestroyNotify)(gpointer data);
typedef guint (*GHashFunc)(gconstpointer key);
typedef gboolean (*GEqualFunc)(gconstpointer a, gconstpointer b);

typedef struct {
    void (*start_element)(GMarkupParseContext*, const gchar*, const gchar**, const gchar**, gpointer, GError**);
    void (*end_element)(GMarkupParseContext*, const gchar*, gpointer, GError**);
    void (*text)(GMarkupParseContext*, const gchar*, gsize, gpointer, GError**);
    void (*passthrough)(GMarkupParseContext*, const gchar*, gsize, gpointer, GError**);
    void (*error)(GMarkupParseContext*, GError*, gpointer);
} GMarkupParser;

#ifndef TRUE
#define TRUE 1
#define FALSE 0
#endif
#define NULLPTR ((void*)0)
#define G_CALLBACK(f) ((GCallback)(f))
#define G_OBJECT(o) ((GObject*)(o))
#define GTK_WIDGET(o) ((GtkWidget*)(o))
#define GTK_WINDOW(o) ((GtkWindow*)(o))
#define GTK_BOX(o) ((GtkBox*)(o))
#define GTK_CONTAINER(o) ((GtkContainer*)(o))
#define GTK_BIN(o) ((GtkBin*)(o))
#define GTK_LIST_BOX(o) ((GtkListBox*)(o))
#define GTK_LIST_BOX_ROW(o) ((GtkListBoxRow*)(o))
#define GTK_FLOW_BOX(o) ((GtkFlowBox*)(o))
#define GTK_FLOW_BOX_CHILD(o) ((GtkFlowBoxChild*)(o))
#define GTK_BUTTON(o) ((GtkButton*)(o))
#define GTK_LABEL(o) ((GtkLabel*)(o))
#define GTK_ENTRY(o) ((GtkEntry*)(o))
#define GTK_IMAGE(o) ((GtkImage*)(o))
#define GTK_SCROLLED_WINDOW(o) ((GtkScrolledWindow*)(o))
#define GTK_MENU_SHELL(o) ((GtkMenuShell*)(o))
#define GTK_MENU(o) ((GtkMenu*)(o))
#define GTK_MENU_ITEM(o) ((GtkMenuItem*)(o))
#define GTK_STYLE_PROVIDER(o) ((gpointer)(o))
#define GTK_DIALOG(o) ((GtkDialog*)(o))

#define GTK_WINDOW_TOPLEVEL 0
#define GTK_ORIENTATION_HORIZONTAL 0
#define GTK_ORIENTATION_VERTICAL 1
#define GTK_ALIGN_FILL 0
#define GTK_ALIGN_START 1
#define GTK_ALIGN_END 2
#define GTK_ALIGN_CENTER 3
#define GTK_POLICY_ALWAYS 0
#define GTK_POLICY_AUTOMATIC 1
#define GTK_POLICY_NEVER 2
#define GTK_SELECTION_NONE 0
#define GTK_SELECTION_SINGLE 1
#define GTK_SELECTION_BROWSE 2
#define GTK_RELIEF_NORMAL 0
#define GTK_RELIEF_NONE 2
#define GTK_ICON_SIZE_INVALID 0
#define GTK_ICON_SIZE_MENU 1
#define GTK_ICON_SIZE_SMALL_TOOLBAR 2
#define GTK_ICON_SIZE_LARGE_TOOLBAR 3
#define GTK_ICON_SIZE_BUTTON 4
#define GTK_ICON_SIZE_DND 5
#define GTK_ICON_SIZE_DIALOG 6
#define GTK_JUSTIFY_LEFT 0
#define GTK_JUSTIFY_CENTER 2
#define PANGO_ELLIPSIZE_NONE 0
#define PANGO_ELLIPSIZE_END 3
#define GDK_WINDOW_TYPE_HINT_DIALOG 1
#define GTK_STYLE_PROVIDER_PRIORITY_APPLICATION 600
#define GTK_ICON_LOOKUP_FORCE_SIZE (1u << 4)
#define GDK_BUTTON_PRESS_MASK (1u << 8)
#define GDK_BUTTON_RELEASE_MASK (1u << 9)
#define GDK_ENTER_NOTIFY_MASK (1u << 12)
#define GDK_LEAVE_NOTIFY_MASK (1u << 13)
#define GDK_MOD1_MASK (1u << 3)
#define GDK_KEY_Escape 0xff1b
#define GDK_KEY_Return 0xff0d
#define GDK_KEY_KP_Enter 0xff8d
#define GDK_CURRENT_TIME 0
#define GDK_GRAB_SUCCESS 0
#define G_FILE_MONITOR_NONE 0
#define G_FILE_MONITOR_EVENT_CHANGED 0
#define G_FILE_MONITOR_EVENT_CHANGES_DONE_HINT 1
#define G_FILE_MONITOR_EVENT_DELETED 2
#define G_FILE_MONITOR_EVENT_CREATED 3
#define G_MARKUP_DEFAULT_FLAGS 0
#define GTK_DIALOG_MODAL (1u << 0)
#define GTK_MESSAGE_ERROR 3
#define GTK_MESSAGE_INFO 0
#define GTK_BUTTONS_CLOSE 2
#define GTK_RESPONSE_CLOSE -7

/* GLib/GObject */
void g_free(gpointer mem);
gchar *g_strdup(const gchar *str);
gchar *g_strdup_printf(const gchar *format, ...);
gchar *g_strstrip(gchar *string);
gchar *g_ascii_strdown(const gchar *str, glong len);
gint g_ascii_strcasecmp(const gchar *s1, const gchar *s2);
gint g_strcmp0(const gchar *str1, const gchar *str2);
gchar *g_markup_escape_text(const gchar *text, glong length);
const gchar *g_get_home_dir(void);
const gchar *g_get_user_name(void);
gint g_mkdir_with_parents(const gchar *pathname, gint mode);
guint g_timeout_add(guint interval, GSourceFunc function, gpointer data);
guint g_idle_add(GSourceFunc function, gpointer data);
gboolean g_source_remove(guint tag);
void g_error_free(GError *error);
GList *g_list_first(GList *list);
void g_list_free(GList *list);
GHashTable *g_hash_table_new_full(GHashFunc hash_func, GEqualFunc key_equal_func, GDestroyNotify key_destroy_func, GDestroyNotify value_destroy_func);
gboolean g_hash_table_insert(GHashTable *hash_table, gpointer key, gpointer value);
gpointer g_hash_table_lookup(GHashTable *hash_table, gconstpointer key);
void g_hash_table_remove_all(GHashTable *hash_table);
void g_hash_table_destroy(GHashTable *hash_table);
guint g_str_hash(gconstpointer v);
gboolean g_str_equal(gconstpointer v1, gconstpointer v2);
gulong g_signal_connect_data(gpointer instance, const gchar *detailed_signal, GCallback c_handler, gpointer data, GClosureNotify destroy_data, GConnectFlags connect_flags);
gpointer g_object_ref(gpointer object);
void g_object_unref(gpointer object);

GMarkupParseContext *g_markup_parse_context_new(const GMarkupParser *parser, GMarkupParseFlags flags, gpointer user_data, GDestroyNotify user_data_dnotify);
gboolean g_markup_parse_context_parse(GMarkupParseContext *context, const gchar *text, gssize text_len, GError **error);
gboolean g_markup_parse_context_end_parse(GMarkupParseContext *context, GError **error);
void g_markup_parse_context_free(GMarkupParseContext *context);

/* GTK/GDK */
void gtk_init(gint *argc, gchar ***argv);
void gtk_main(void);
void gtk_main_quit(void);
GtkWidget *gtk_window_new(GtkWindowType type);
void gtk_window_set_title(GtkWindow *window, const gchar *title);
void gtk_window_set_default_size(GtkWindow *window, gint width, gint height);
void gtk_window_set_resizable(GtkWindow *window, gboolean resizable);
void gtk_window_set_decorated(GtkWindow *window, gboolean setting);
void gtk_window_set_skip_taskbar_hint(GtkWindow *window, gboolean setting);
void gtk_window_set_skip_pager_hint(GtkWindow *window, gboolean setting);
void gtk_window_set_keep_above(GtkWindow *window, gboolean setting);
void gtk_window_set_type_hint(GtkWindow *window, GdkWindowTypeHint hint);
void gtk_window_move(GtkWindow *window, gint x, gint y);
void gtk_window_present(GtkWindow *window);
void gtk_window_set_icon_name(GtkWindow *window, const gchar *name);
void gtk_window_begin_move_drag(GtkWindow *window, gint button, gint root_x, gint root_y, guint32 timestamp);
void gtk_window_get_position(GtkWindow *window, gint *root_x, gint *root_y);
void gtk_window_get_size(GtkWindow *window, gint *width, gint *height);

GtkWidget *gtk_box_new(GtkOrientation orientation, gint spacing);
void gtk_box_pack_start(GtkBox *box, GtkWidget *child, gboolean expand, gboolean fill, guint padding);
void gtk_box_pack_end(GtkBox *box, GtkWidget *child, gboolean expand, gboolean fill, guint padding);
GtkWidget *gtk_separator_new(GtkOrientation orientation);
GtkWidget *gtk_scrolled_window_new(gpointer hadjustment, gpointer vadjustment);
void gtk_scrolled_window_set_policy(GtkScrolledWindow *scrolled_window, GtkPolicyType hscrollbar_policy, GtkPolicyType vscrollbar_policy);
GtkWidget *gtk_list_box_new(void);
void gtk_list_box_set_selection_mode(GtkListBox *box, GtkSelectionMode mode);
void gtk_list_box_select_row(GtkListBox *box, GtkListBoxRow *row);
GtkWidget *gtk_list_box_row_new(void);
GtkWidget *gtk_flow_box_new(void);
void gtk_flow_box_set_max_children_per_line(GtkFlowBox *box, guint n_children);
void gtk_flow_box_set_selection_mode(GtkFlowBox *box, GtkSelectionMode mode);
void gtk_flow_box_unselect_all(GtkFlowBox *box);
GList *gtk_flow_box_get_selected_children(GtkFlowBox *box);
GtkWidget *gtk_button_new(void);
void gtk_button_set_relief(GtkButton *button, GtkReliefStyle newstyle);
GtkWidget *gtk_label_new(const gchar *str);
void gtk_label_set_text(GtkLabel *label, const gchar *str);
void gtk_label_set_markup(GtkLabel *label, const gchar *str);
void gtk_label_set_xalign(GtkLabel *label, float xalign);
void gtk_label_set_yalign(GtkLabel *label, float yalign);
void gtk_label_set_line_wrap(GtkLabel *label, gboolean wrap);
void gtk_label_set_max_width_chars(GtkLabel *label, gint n_chars);
void gtk_label_set_lines(GtkLabel *label, gint lines);
void gtk_label_set_ellipsize(GtkLabel *label, PangoEllipsizeMode mode);
void gtk_label_set_justify(GtkLabel *label, GtkJustification jtype);
GtkWidget *gtk_search_entry_new(void);
const gchar *gtk_entry_get_text(GtkEntry *entry);
void gtk_entry_set_placeholder_text(GtkEntry *entry, const gchar *text);
GtkWidget *gtk_image_new(void);
GtkWidget *gtk_image_new_from_pixbuf(GdkPixbuf *pixbuf);
GtkWidget *gtk_image_new_from_icon_name(const gchar *icon_name, GtkIconSize size);
void gtk_image_set_from_pixbuf(GtkImage *image, GdkPixbuf *pixbuf);
void gtk_image_set_from_icon_name(GtkImage *image, const gchar *icon_name, GtkIconSize size);
void gtk_image_set_pixel_size(GtkImage *image, gint pixel_size);
GtkWidget *gtk_event_box_new(void);
void gtk_event_box_set_above_child(gpointer event_box, gboolean above_child);
GtkWidget *gtk_menu_new(void);
GtkWidget *gtk_menu_item_new_with_label(const gchar *label);
GtkWidget *gtk_separator_menu_item_new(void);
void gtk_menu_shell_append(GtkMenuShell *menu_shell, GtkWidget *child);
void gtk_menu_popup_at_pointer(GtkMenu *menu, gpointer trigger_event);
GtkWidget *gtk_message_dialog_new(GtkWindow *parent, GtkDialogFlags flags, GtkMessageType type, GtkButtonsType buttons, const gchar *message_format, ...);
gint gtk_dialog_run(GtkDialog *dialog);

void gtk_container_add(GtkContainer *container, GtkWidget *widget);
void gtk_container_remove(GtkContainer *container, GtkWidget *widget);
GList *gtk_container_get_children(GtkContainer *container);
GtkWidget *gtk_bin_get_child(GtkBin *bin);
void gtk_widget_destroy(GtkWidget *widget);
void gtk_widget_show(GtkWidget *widget);
void gtk_widget_hide(GtkWidget *widget);
void gtk_widget_show_all(GtkWidget *widget);
void gtk_widget_grab_focus(GtkWidget *widget);
void gtk_widget_set_can_focus(GtkWidget *widget, gboolean can_focus);
void gtk_widget_set_size_request(GtkWidget *widget, gint width, gint height);
void gtk_widget_set_halign(GtkWidget *widget, GtkAlign align);
void gtk_widget_set_valign(GtkWidget *widget, GtkAlign align);
void gtk_widget_set_hexpand(GtkWidget *widget, gboolean expand);
void gtk_widget_set_vexpand(GtkWidget *widget, gboolean expand);
void gtk_widget_set_margin_start(GtkWidget *widget, gint margin);
void gtk_widget_set_margin_end(GtkWidget *widget, gint margin);
void gtk_widget_set_margin_top(GtkWidget *widget, gint margin);
void gtk_widget_set_margin_bottom(GtkWidget *widget, gint margin);
void gtk_widget_set_tooltip_text(GtkWidget *widget, const gchar *text);
void gtk_widget_add_events(GtkWidget *widget, gint events);
void gtk_widget_set_app_paintable(GtkWidget *widget, gboolean app_paintable);
void gtk_widget_set_visual(GtkWidget *widget, GdkVisual *visual);
GtkStyleContext *gtk_widget_get_style_context(GtkWidget *widget);
void gtk_widget_override_font(GtkWidget *widget, const PangoFontDescription *font_desc);
void gtk_widget_get_allocation(GtkWidget *widget, GtkAllocation *allocation);
GdkWindow *gtk_widget_get_window(GtkWidget *widget);
void gtk_grab_add(GtkWidget *widget);
void gtk_grab_remove(GtkWidget *widget);

GtkCssProvider *gtk_css_provider_new(void);
gboolean gtk_css_provider_load_from_data(GtkCssProvider *css_provider, const gchar *data, gssize length, GError **error);
void gtk_style_context_add_class(GtkStyleContext *context, const gchar *class_name);
void gtk_style_context_remove_class(GtkStyleContext *context, const gchar *class_name);
void gtk_style_context_add_provider_for_screen(GdkScreen *screen, gpointer provider, guint priority);

GdkScreen *gdk_screen_get_default(void);
GdkVisual *gdk_screen_get_rgba_visual(GdkScreen *screen);
gboolean gdk_screen_is_composited(GdkScreen *screen);
gint gdk_screen_get_width(GdkScreen *screen);
gint gdk_screen_get_height(GdkScreen *screen);
GdkGrabStatus gdk_pointer_grab(GdkWindow *window, gboolean owner_events, GdkEventMask event_mask, GdkWindow *confine_to, GdkCursor *cursor, guint32 time_);
void gdk_pointer_ungrab(guint32 time_);

GtkIconTheme *gtk_icon_theme_get_default(void);
gboolean gtk_icon_theme_has_icon(GtkIconTheme *icon_theme, const gchar *icon_name);
GdkPixbuf *gtk_icon_theme_load_icon(GtkIconTheme *icon_theme, const gchar *icon_name, gint size, GtkIconLookupFlags flags, GError **error);
GdkPixbuf *gdk_pixbuf_new_from_file_at_scale(const gchar *filename, gint width, gint height, gboolean preserve_aspect_ratio, GError **error);
GdkPixbuf *gdk_pixbuf_new_from_file_at_size(const gchar *filename, gint width, gint height, GError **error);

PangoFontDescription *pango_font_description_from_string(const char *str);
void pango_font_description_set_size(PangoFontDescription *desc, gint size);
void pango_font_description_free(PangoFontDescription *desc);

GFile *g_file_new_for_path(const gchar *path);
GFileMonitor *g_file_monitor_file(GFile *file, GFileMonitorFlags flags, GCancellable *cancellable, GError **error);

#endif
