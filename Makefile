# Python 3.11 preferido (python3.11 del PATH, Homebrew en macOS, o python3).
# Se puede forzar: make PYTHON=/ruta/a/python3.11 build
PYTHON     ?= $(shell command -v python3.11 2>/dev/null || command -v /opt/homebrew/opt/python@3.11/bin/python3.11 2>/dev/null || command -v python3 2>/dev/null || command -v python 2>/dev/null)
VENV       := venv
UNAME_S    := $(shell uname -s 2>/dev/null || echo Windows)
ifneq (,$(or $(findstring MINGW,$(UNAME_S)),$(findstring MSYS,$(UNAME_S)),$(findstring CYGWIN,$(UNAME_S)),$(findstring Windows,$(UNAME_S))))
  VENV_BIN := $(VENV)/Scripts
else
  VENV_BIN := $(VENV)/bin
endif
SHELL      := bash
ACTIVATE   := source $(VENV_BIN)/activate
APP_NAME   := Image Transform Lite
DIST_APP   := dist/$(APP_NAME).app

.PHONY: help venv install test run run-debug build dist pkg icons version release clean clean-all

help: ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

venv: ## Crea el virtual environment (Python 3.11 recomendado)
	@test -n "$(PYTHON)" || (echo "Error: Python 3 no encontrado. macOS: brew install python@3.11" && exit 1)
	@"$(PYTHON)" -c "import sys; v=sys.version_info[:2]; print('Python %d.%d' % v); sys.exit(0 if v >= (3, 10) else 1)" || (echo "Error: se necesita Python >= 3.10 (3.11 recomendado)" && exit 1)
	@test -d $(VENV) || "$(PYTHON)" -m venv $(VENV)
	@echo "venv listo en $(VENV)/"

install: venv ## Instala todas las dependencias
	@$(ACTIVATE) && python -m pip install --upgrade pip -q && python -m pip install -r requirements.txt pytest pyinstaller -q
	@echo "Dependencias instaladas"

test: install ## Ejecuta los tests
	@$(ACTIVATE) && python -m pytest tests/ -v

run: install ## Ejecuta la app en modo desarrollo
	@$(ACTIVATE) && python -m app.main

run-debug: install ## Ejecuta la app en modo desarrollo con debug
	@$(ACTIVATE) && python -m app.main --debug

build: install ## Construye la app para este sistema (.app / carpeta con .exe / carpeta Linux)
	@$(ACTIVATE) && pyinstaller build.spec --clean --noconfirm
	@$(ACTIVATE) && python scripts/package_release.py --check
	@echo ""
	@echo "Build listo en dist/"

dist: build ## Construye y empaqueta los assets de release de este sistema en dist/
	@$(ACTIVATE) && python scripts/package_release.py

icons: ## Regenera assets/icon.ico y assets/icon.png desde assets/icon.icns
	@$(ACTIVATE) && python scripts/generate_platform_icons.py

pkg: build ## Construye el instalador .pkg (solo macOS)
	@test "$(UNAME_S)" = "Darwin" || (echo "Error: make pkg solo funciona en macOS" && exit 1)
	@$(ACTIVATE) && VERSION=$$(python -c "from app.version import __version__; print(__version__)") && \
	ARCH=$$(uname -m | sed 's/x86_64/x64/') && \
	rm -rf pkg-root && \
	mkdir -p pkg-root/Applications && \
	ditto "$(DIST_APP)" "pkg-root/Applications/$(APP_NAME).app" && \
	pkgbuild \
		--root pkg-root \
		--identifier com.maecly.imagetransformlite \
		--version "$$VERSION" \
		--install-location / \
		"dist/Image-Transform-Lite-$$VERSION-macos-$$ARCH.pkg" && \
	rm -rf pkg-root && \
	echo "Pkg listo: dist/Image-Transform-Lite-$$VERSION-macos-$$ARCH.pkg"

version: ## Muestra la version actual de la app
	@$(ACTIVATE) && python -c "from app.version import __version__; print(__version__)"

release: dist ## Crea tag y push para triggear release en GitHub Actions (6 plataformas)
	@$(ACTIVATE) && VERSION=$$(python -c "from app.version import __version__; print(__version__)") && \
	grep -q "## \[$$VERSION\]" CHANGELOG.md || (echo "ERROR: CHANGELOG.md no tiene entrada para v$$VERSION" && exit 1) && \
	echo "Creando release v$$VERSION..." && \
	git tag -a "v$$VERSION" -m "Release v$$VERSION" && \
	git push origin "v$$VERSION" && \
	echo "Tag v$$VERSION pushed. GitHub Actions compilara macOS/Windows/Linux y creara el release."

clean: ## Limpia archivos de build
	@chmod -R u+w dist/ 2>/dev/null || true
	rm -rf build/ dist/ pkg-root/ *.spec.bak __pycache__ .pytest_cache 2>/dev/null || true
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

clean-all: clean ## Limpia todo incluyendo el venv
	rm -rf $(VENV)
