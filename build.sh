#!/bin/bash
set -e

PYTHON="/opt/homebrew/opt/python@3.11/bin/python3.11"
VENV_DIR="build_venv"

echo "=== Image Transform Lite - Build ==="

# Check Python 3.11
if [ ! -f "$PYTHON" ]; then
    echo "Error: Python 3.11 no encontrado en $PYTHON"
    echo "Instalar con: brew install python@3.11"
    exit 1
fi

# Create venv
if [ ! -d "$VENV_DIR" ]; then
    echo "Creando virtual environment..."
    "$PYTHON" -m venv "$VENV_DIR"
fi

# Activate and install
source "$VENV_DIR/bin/activate"
echo "Instalando dependencias..."
pip install --upgrade pip -q
pip install -r requirements.txt pyinstaller -q

# Build
echo "Construyendo .app..."
pyinstaller build.spec --clean --noconfirm

echo ""
echo "=== Build completado ==="
echo "App: dist/Image Transform Lite.app"
echo ""
echo "Para distribuir: zip -r 'Image Transform Lite.zip' 'dist/Image Transform Lite.app'"
