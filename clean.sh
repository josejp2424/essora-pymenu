#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
rm -rf "$ROOT/build"
printf '%s\n' "Limpieza terminada."
