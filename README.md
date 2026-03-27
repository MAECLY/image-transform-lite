# Image Transform Lite

Aplicacion de escritorio para Mac que permite procesar imagenes en lote con transformaciones configurables. Interfaz grafica donde puedes activar/desactivar transformaciones, ajustar parametros y cambiar el orden de ejecucion arrastrando las tarjetas.

![macOS](https://img.shields.io/badge/macOS-Apple%20Silicon-black) ![Python](https://img.shields.io/badge/Python-3.11-blue) ![License](https://img.shields.io/badge/license-private-red)

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

Todas las transformaciones se pueden reordenar con drag-and-drop en la UI.

## Input / Output

```
input_files/foto.jpg              →  output_files/foto.webp
input_files/rosas/foto.png        →  output_files/rosas/foto.webp
input_files/a/b/c/foto.bmp        →  output_files/a/b/c/foto.webp
```

- Busca imagenes recursivamente en la carpeta de input (`.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`, `.tiff`)
- Preserva la estructura de carpetas en el output
- Conserva el nombre del archivo, solo cambia la extension a `.webp`
- Formato de salida: WebP (calidad configurable, default 90)

## Instalacion rapida

### Opcion 1: Usar el .app directamente

1. Descargar `Image Transform Lite.zip`
2. Descomprimir
3. Doble click en `Image Transform Lite.app`
4. Si macOS lo bloquea: click derecho → Abrir

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

Incluye: transformaciones activas, parametros, orden de ejecucion, calidad WebP, y directorios de input/output.

## Tech Stack

- **Pillow** — procesamiento de imagenes
- **pywebview** — ventana nativa macOS (WebKit, sin navegador)
- **Sortable.js** — drag-and-drop en la UI
- **PyInstaller** — empaquetado como .app
