#!/usr/bin/env bash
# Elimina el acceso directo y el icono instalados por install.sh.
# No borra esta carpeta ni tu configuracion (~/.config/ImageTransformLite).
set -euo pipefail

APP_ID="image-transform-lite"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"

rm -f "$DATA_HOME/applications/$APP_ID.desktop"
rm -f "$DATA_HOME/icons/hicolor/512x512/apps/$APP_ID.png"

command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database -q "$DATA_HOME/applications" || true
command -v gtk-update-icon-cache >/dev/null 2>&1 && gtk-update-icon-cache -q -t "$DATA_HOME/icons/hicolor" || true

echo "Acceso directo de Image Transform Lite eliminado."
echo "Puedes borrar la carpeta de la app manualmente si ya no la necesitas."
