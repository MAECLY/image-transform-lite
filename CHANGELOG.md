# Changelog

Todos los cambios notables de este proyecto se documentan aqui.
Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

## [1.2.0] - 2026-03-27

### Added
- CHANGELOG.md con historial de todas las versiones
- Notas del changelog se incluyen automaticamente en los GitHub Releases
- `make release` valida que CHANGELOG.md tenga entrada para la version actual antes de crear el tag

## [1.1.0] - 2026-03-27

### Added
- Icono personalizado de la app (gradiente azul con marcos de imagen y flecha de transformacion)
- Menu dropdown en el header con opciones: "Buscar actualizaciones" y "Acerca de"
- Check for updates manual desde el menu
- Scripts de generacion de iconos en `scripts/` para futuras iteraciones

### Changed
- Icono embebido en el bundle `.app` (visible en Dock y Finder)

## [1.0.0] - 2026-03-27

### Added
- App de escritorio para macOS (Apple Silicon) con UI para procesamiento de imagenes en lote
- 7 transformaciones configurables: Flip, Rotate, Safe Square Crop, Resize, Brightness, Contrast, Sharpness
- Drag-and-drop para reordenar transformaciones
- Persistencia de configuracion (se guarda automaticamente)
- Preservacion de estructura de carpetas (input → output)
- Output en formato WebP con calidad configurable
- Check for updates automatico al iniciar (via GitHub Releases API)
- Banner de actualizacion con link de descarga directa
- Version visible en el header de la app
- GitHub Actions CI (tests en push/PR)
- GitHub Actions Release (build + publish `.pkg` y `.zip` al pushear tag)
- Instalador `.pkg` (instala en /Applications con doble click)
- Licencia MIT
- Makefile con targets: run, test, build, dist, pkg, version, release
