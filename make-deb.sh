#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

"$ROOT/build.sh"

STAGE=$(find "$ROOT/build" -mindepth 1 -maxdepth 1 -type d -name 'essora-pymenu_*' | sort | tail -n 1)
if [ -z "$STAGE" ]; then
    echo "Error: no se encontró la carpeta Debian preparada." >&2
    exit 1
fi

OUTPUT="${STAGE}.deb"
dpkg-deb --build --root-owner-group "$STAGE" "$OUTPUT"
printf '%s\n' "DEB creado: $OUTPUT"
