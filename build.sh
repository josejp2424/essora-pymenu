#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SRC_DIR="$ROOT/src"
TEMPLATE="$ROOT/package"
BUILD_DIR="$ROOT/build"
PACKAGE=$(awk '/^Package:/ {print $2; exit}' "$TEMPLATE/DEBIAN/control.in")
DEB_VERSION=$(awk '/^Version:/ {print $2; exit}' "$TEMPLATE/DEBIAN/control.in")
CC=${CC:-gcc}
CFLAGS=${CFLAGS:--O2 -pipe -Wall -Wextra -std=gnu11}

case "${ARCH:-}" in
    "")
        if command -v dpkg >/dev/null 2>&1; then
            ARCH=$(dpkg --print-architecture)
        else
            case "$(uname -m)" in
                x86_64) ARCH=amd64 ;;
                i?86) ARCH=i386 ;;
                aarch64) ARCH=arm64 ;;
                armv7*|armv6*) ARCH=armhf ;;
                *) ARCH=$(uname -m) ;;
            esac
        fi
        ;;
esac

STAGE="$BUILD_DIR/${PACKAGE}_${DEB_VERSION}_${ARCH}"
BIN="$BUILD_DIR/essora-pymenu"

rm -rf "$STAGE"
mkdir -p "$BUILD_DIR" "$STAGE"

compile_with_pkg_config() {
    command -v pkg-config >/dev/null 2>&1 || return 1
    pkg-config --exists gtk+-3.0 gio-2.0 gdk-pixbuf-2.0 pango || return 1

    # shellcheck disable=SC2046
    "$CC" $CFLAGS -DESSORA_USE_SYSTEM_GTK_HEADERS \
        "$SRC_DIR/essora-pymenu.c" -o "$BIN" \
        $(pkg-config --cflags --libs gtk+-3.0 gio-2.0 gdk-pixbuf-2.0 pango)
}

compile_with_runtime_abi() {
    find_lib() {
        ldconfig -p 2>/dev/null | awk -v name="$1" '$1 == name { print $NF; exit }'
    }

    LIBS=""
    for lib in \
        libgtk-3.so.0 \
        libgdk-3.so.0 \
        libgdk_pixbuf-2.0.so.0 \
        libgio-2.0.so.0 \
        libgobject-2.0.so.0 \
        libglib-2.0.so.0 \
        libpango-1.0.so.0
    do
        path=$(find_lib "$lib")
        if [ -z "$path" ]; then
            echo "Error: falta la biblioteca de ejecución $lib" >&2
            return 1
        fi
        LIBS="$LIBS $path"
    done

    # gtk3_abi.h permite compilar en Puppy livianos sin los headers -dev.
    # shellcheck disable=SC2086
    "$CC" $CFLAGS -I"$SRC_DIR" "$SRC_DIR/essora-pymenu.c" -o "$BIN" $LIBS
}

printf '%s\n' "Compilando Essora PyMenu..."
if ! compile_with_pkg_config; then
    printf '%s\n' "No se encontraron los headers GTK3; usando el ABI liviano incluido."
    compile_with_runtime_abi
fi

chmod 755 "$BIN"
if command -v strip >/dev/null 2>&1; then
    strip --strip-unneeded "$BIN" 2>/dev/null || true
fi

cp -a "$TEMPLATE/." "$STAGE/"
rm -f "$STAGE/DEBIAN/control.in"
install -D -m 755 "$BIN" "$STAGE/usr/local/pymenu/essora-pymenu"

find "$STAGE" -type d -exec chmod 755 {} +
chmod 755 "$STAGE/DEBIAN/postinst" \
          "$STAGE/usr/local/bin/pymenu" \
          "$STAGE/usr/local/pymenu/essora-pymenu" \
          "$STAGE/usr/local/pymenu/"*.py
find "$STAGE" -type f \
    ! -path "$STAGE/DEBIAN/postinst" \
    ! -path "$STAGE/usr/local/bin/pymenu" \
    ! -path "$STAGE/usr/local/pymenu/essora-pymenu" \
    ! -name '*.py' -exec chmod 644 {} +

INSTALLED_SIZE=$(du -sk "$STAGE" | awk '{print $1}')
sed \
    -e "s/@ARCH@/$ARCH/g" \
    -e "s/@INSTALLED_SIZE@/$INSTALLED_SIZE/g" \
    "$TEMPLATE/DEBIAN/control.in" > "$STAGE/DEBIAN/control"
chmod 644 "$STAGE/DEBIAN/control"

(
    cd "$STAGE"
    find . -type f ! -path './DEBIAN/*' -print0 \
        | sort -z \
        | xargs -0 md5sum \
        | sed 's#  \./#  #' > DEBIAN/md5sums
)
chmod 644 "$STAGE/DEBIAN/md5sums"

printf '\n%s\n' "Compilación terminada."
printf '%s\n' "Carpeta Debian preparada:"
printf '  %s\n' "$STAGE"
printf '\n%s\n' "Para crear el .deb:"
printf '  dpkg-deb --build --root-owner-group "%s"\n' "$STAGE"
