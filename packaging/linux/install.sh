#!/usr/bin/env bash
# Instala el acceso directo de Image Transform Lite en el menu de aplicaciones
# del usuario (~/.local/share). Se puede ejecutar varias veces sin problema.
# La app se ejecuta desde esta carpeta: si la mueves, vuelve a ejecutar ./install.sh
set -euo pipefail

APP_ID="image-transform-lite"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXE="$HERE/$APP_ID"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
APPS_DIR="$DATA_HOME/applications"
ICON_DIR="$DATA_HOME/icons/hicolor/512x512/apps"
DESKTOP_FILE="$APPS_DIR/$APP_ID.desktop"

if [ ! -f "$EXE" ]; then
    echo "Error: no se encuentra el ejecutable $EXE" >&2
    exit 1
fi
chmod +x "$EXE"

mkdir -p "$APPS_DIR" "$ICON_DIR"
install -m 644 "$HERE/$APP_ID.png" "$ICON_DIR/$APP_ID.png"

# Exec/Path absolutos (entre comillas por si la ruta tiene espacios).
sed -e "s|^Exec=.*|Exec=\"$EXE\"|" \
    -e "s|^Icon=.*|Icon=$APP_ID|" \
    "$HERE/$APP_ID.desktop" > "$DESKTOP_FILE.tmp"
grep -q '^Path=' "$DESKTOP_FILE.tmp" || echo "Path=$HERE" >> "$DESKTOP_FILE.tmp"
mv -f "$DESKTOP_FILE.tmp" "$DESKTOP_FILE"
chmod 644 "$DESKTOP_FILE"

command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database -q "$APPS_DIR" || true
command -v gtk-update-icon-cache >/dev/null 2>&1 && gtk-update-icon-cache -q -t "$DATA_HOME/icons/hicolor" || true

echo "Image Transform Lite instalado en el menu de aplicaciones."
echo "  Acceso directo: $DESKTOP_FILE"
echo "  Ejecutable:     $EXE"
echo "Para desinstalar: $HERE/uninstall.sh"
