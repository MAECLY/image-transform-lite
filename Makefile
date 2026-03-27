PYTHON     := /opt/homebrew/opt/python@3.11/bin/python3.11
VENV       := venv
ACTIVATE   := source $(VENV)/bin/activate
APP_NAME   := Image Transform Lite
DIST_APP   := dist/$(APP_NAME).app

.PHONY: help venv install test run build dist version release clean clean-all

help: ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

venv: ## Crea el virtual environment con Python 3.11
	@test -f $(PYTHON) || (echo "Error: Python 3.11 no encontrado. Instalar con: brew install python@3.11" && exit 1)
	@test -d $(VENV) || $(PYTHON) -m venv $(VENV)
	@echo "venv listo en $(VENV)/"

install: venv ## Instala todas las dependencias
	@$(ACTIVATE) && pip install --upgrade pip -q && pip install -r requirements.txt pytest pyinstaller -q
	@echo "Dependencias instaladas"

test: install ## Ejecuta los tests
	@$(ACTIVATE) && python -m pytest tests/ -v

run: install ## Ejecuta la app en modo desarrollo
	@$(ACTIVATE) && python -m app.main

run-debug: install ## Ejecuta la app en modo desarrollo con debug
	@$(ACTIVATE) && python -m app.main --debug

build: install ## Construye el .app bundle
	@$(ACTIVATE) && pyinstaller build.spec --clean --noconfirm
	@echo ""
	@echo "Build listo: $(DIST_APP)"

dist: build ## Construye y genera el .zip para distribuir
	@cd dist && zip -r "$(APP_NAME).zip" "$(APP_NAME).app" -q
	@echo "Zip listo: dist/$(APP_NAME).zip"

version: ## Muestra la version actual de la app
	@$(ACTIVATE) && python -c "from app.version import __version__; print(__version__)"

release: dist ## Crea tag y push para triggear release en GitHub Actions
	@$(ACTIVATE) && VERSION=$$(python -c "from app.version import __version__; print(__version__)") && \
	echo "Creando release v$$VERSION..." && \
	git tag -a "v$$VERSION" -m "Release v$$VERSION" && \
	git push origin "v$$VERSION" && \
	echo "Tag v$$VERSION pushed. GitHub Actions creara el release automaticamente."

clean: ## Limpia archivos de build
	rm -rf build/ dist/ *.spec.bak __pycache__ .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

clean-all: clean ## Limpia todo incluyendo el venv
	rm -rf $(VENV)
