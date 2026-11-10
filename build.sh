#!/usr/bin/env bash
# Build local de Image Transform Lite para el sistema actual
# (macOS .app, Windows carpeta con .exe via Git Bash, Linux carpeta + .tar.gz).
set -e

cd "$(dirname "$0")"

# Python 3.11 recomendado; se puede forzar con PYTHON=/ruta/python ./build.sh
if [ -z "$PYTHON" ]; then
    for candidate in python3.11 /opt/homebrew/opt/python@3.11/bin/python3.11 python3 python; do
        if command -v "$candidate" >/dev/null 2>&1; then
            PYTHON="$(command -v "$candidate")"
            break
        fi
    done
fi
if [ -z "$PYTHON" ]; then
    echo "Error: Python 3 no encontrado (macOS: brew install python@3.11)"
    exit 1
fi

VENV_DIR="build_venv"

echo "=== Image Transform Lite - Build ==="
"$PYTHON" --version

# Create venv
if [ ! -d "$VENV_DIR" ]; then
    echo "Creando virtual environment..."
    "$PYTHON" -m venv "$VENV_DIR"
fi

# Activate and install
if [ -f "$VENV_DIR/Scripts/activate" ]; then
    source "$VENV_DIR/Scripts/activate"
else
    source "$VENV_DIR/bin/activate"
fi
echo "Instalando dependencias..."
python -m pip install --upgrade pip -q
python -m pip install -r requirements.txt pyinstaller -q

# Build
echo "Construyendo..."
pyinstaller build.spec --clean --noconfirm

# Smoke check + release assets for this platform
python scripts/package_release.py

echo ""
echo "=== Build completado ==="
echo "Assets en dist/"
