# Image Transform Lite

Aplicacion de escritorio para Mac que permite procesar imagenes en lote con transformaciones configurables, vista previa en tiempo real y actualizaciones automaticas.

![macOS](https://img.shields.io/badge/macOS-Apple%20Silicon-black) ![Python](https://img.shields.io/badge/Python-3.11-blue) ![License](https://img.shields.io/badge/license-MIT-green) ![Version](https://img.shields.io/badge/version-1.3.3-blue)

## Caracteristicas

- **Live Preview** — vista antes/despues en tiempo real con navegacion entre imagenes
- **7 transformaciones** — flip, rotate, safe square crop, resize, brightness, contrast, sharpness
- **Drag-and-drop** — reordena transformaciones arrastrando las tarjetas
- **Recetas (presets)** — guarda, carga, importa y exporta combinaciones de transformaciones
- **Multi-formato** — salida en WebP, JPEG, PNG o TIFF
- **Actualizaciones automaticas** — verifica al iniciar, descarga e instala desde la app
- **Procesamiento en lote** — convierte carpetas completas preservando estructura

## Transformaciones disponibles

| Transformacion | Parametros | Default |
|---|---|---|
| **Flip** | Horizontal / Vertical | Horizontal, activado |
| **Rotate** | Grados (-360 a 360) | 2 grados, activado |
| **Safe Square Crop** | Automatico | Activado |
| **Resize** | Porcentaje (10-500%) o dimensiones (px) con aspect ratio | Desactivado, 100% |
| **Brightness** | Factor 0.5 - 2.0 | Desactivado, 1.0 |
| **Contrast** | Factor 0.5 - 2.0 | Desactivado, 1.0 |
| **Sharpness** | Factor 0.0 - 3.0 | Desactivado, 1.0 |

## Live Preview

La app muestra una vista antes/despues que se actualiza automaticamente (con debounce de 150ms) cada vez que cambias un parametro. Navega entre imagenes con los botones anterior/siguiente.

## Input / Output

```
input_files/foto.jpg       →  output_files/foto.webp
input_files/rosas/foto.png →  output_files/rosas/foto.webp
input_files/a/b/foto.bmp   →  output_files/a/b/foto.webp
```

- Busca imagenes recursivamente (`.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`, `.tiff`, `.tif`)
- Preserva la estructura de carpetas en el output
- Conserva el nombre del archivo, cambia la extension segun el formato de salida
- Formato de salida configurable: WebP, JPEG, PNG o TIFF

## Recetas (Presets)

Guarda combinaciones de transformaciones como recetas en la sidebar:

- **Nueva** — guarda la configuracion actual como receta con nombre
- **Importar** — carga un preset desde archivo JSON
- **Exportar** — exporta la configuracion actual como archivo JSON
- **Aplicar** — un click para cargar cualquier receta
- **Eliminar** — borra recetas con el boton X
- Las recetas se almacenan en `<config_dir>/presets/`

## Actualizaciones

La app verifica actualizaciones automaticamente al iniciar:

- **Notificacion** — banner + modal con notas de la version
- **Saltar version** — ignora una version especifica hasta la siguiente
- **Descarga automatica** — descarga el .zip desde GitHub con barra de progreso
- **Instalar** — extrae y abre Finder para reemplazar la app
- **Verificacion manual** — boton "Buscar Actualizaciones" en la sidebar

## Instalacion rapida

### Opcion 1: Usar el .app directamente

1. Descargar `Image Transform Lite.zip` desde [Releases](https://github.com/miguel50flowers/fe-image-transform-lite/releases)
2. Descomprimir
3. Mover `Image Transform Lite.app` a `/Applications`
4. Doble click en `Image Transform Lite.app`
5. Si macOS lo bloquea: click derecho → Abrir

> **Gatekeeper:** Como la app no esta firmada con un certificado de Apple Developer, macOS Gatekeeper puede bloquearla la primera vez. Para bypassar de forma segura, abre Terminal y ejecuta:
>
> ```bash
> xattr -rd com.apple.quarantine /Applications/Image\ Transform\ Lite.app
> ```
>
> Despues de esto, podras abrir la app normalmente.

### Opcion 2: Ejecutar desde el codigo

**Requisitos:** Python 3.11 (`brew install python@3.11`)

```bash
git clone https://github.com/miguel50flowers/fe-image-transform-lite.git
cd fe-image-transform-lite
make run
```

## Comandos (Makefile)

```bash
make help         # Ver todos los comandos disponibles
make install      # Crear venv + instalar dependencias
make run          # Ejecutar la app en modo desarrollo
make run-debug    # Ejecutar con consola de debug
make test         # Correr tests
make build        # Construir dist/Image Transform Lite.app
make dist         # Construir + generar .zip para distribuir
make pkg          # Construir .pkg instalador
make release      # Crear tag de version y push (trigger CI)
make clean        # Limpiar archivos de build
make clean-all    # Limpiar todo incluyendo venv
```

## Construir el .app

```bash
make dist
```

Genera:
- `dist/Image Transform Lite.app` — aplicacion lista para usar
- `dist/Image Transform Lite.zip` — listo para compartir

Target: macOS Apple Silicon (arm64). Bundle de ~32MB.

## Configuracion

La configuracion se guarda automaticamente con cada cambio en la UI:

- **Modo desarrollo:** `./config.json`
- **App bundleada:** `~/Library/Application Support/ImageTransformLite/config.json`

Incluye: transformaciones activas, parametros, orden de ejecucion, formato y calidad de salida, directorios de input/output, y version saltada de actualizaciones.

## Arquitectura

- **Backend (`app/`)** — Python 3.11 con Pillow para procesamiento de imagenes, pywebview para ventana nativa
- **Frontend (`ui/`)** — HTML/CSS/JS single-page con Sortable.js para drag-and-drop
- **API bridge** — `Api` class expuesta a JS via `pywebview.api.*`
- **Procesamiento** — `BatchProcessor` corre en daemon thread, JS polling cada 200ms
- **Actualizaciones** — GitHub Releases API con descarga en background y extraccion automatica

### Flujo de datos

```
UI change → save_config(dict) → AppConfig.save() → config.json
Process click → process_images() → BatchProcessor thread
  discovers input_files/**/*.{jpg,png,...}
  for each: load → apply transforms in order → save as output format
  JS polls get_progress() → updates progress bar
Preview change → get_preview(config, path) → base64 before/after
Update check → GitHub API → modal with release notes → download → reveal in Finder
```

## Tech Stack

- **Pillow** — procesamiento de imagenes
- **pywebview** — ventana nativa macOS (WebKit, sin navegador)
- **Sortable.js** — drag-and-drop en la UI
- **PyInstaller** — empaquetado como .app
- **certifi** — certificados SSL para verificacion de actualizaciones

## Licencia

MIT