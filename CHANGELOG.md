# Changelog

Todos los cambios notables de este proyecto se documentan aqui.
Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

## [1.5.0] - 2026-04-27

### Added

- **Watermark transform**: nueva transformacion para anadir texto como marca de agua. Configurable: texto, tamano de fuente, opacidad y posicion (4 esquinas + centro).
- **Tests para `processor.py`**: 29 tests nuevos cubriendo `discover_images()`, `load_image()`, `apply_transforms()`, `save_image()` y `BatchProcessor`.
- **Tests mejorados para transforms**: anadidos tests de contraste (valor real cambia) y 5 tests de watermark.

### Changed

- `DEFAULT_ORDER` ahora incluye `"watermark"` como ultima transformacion en la cadena.
- `transforms.py` importa `ImageDraw` e `ImageFont` para soporte de watermark.
- Total de tests: de 42 a 77 (+35 tests).

## [1.4.0] - 2026-04-27

### Added

- **Sidebar colapsable**: la sidebar se puede colapsar/expandir con un boton toggle. El estado se persiste en `localStorage` y se mantiene entre sesiones.
- **Tooltips en sidebar colapsada**: al colapsar la sidebar, los iconos muestran un tooltip con su funcion al hacer hover. Los presets tambien muestran su nombre.
- **Iconos Lucide**: migracion de todos los SVGs inline a [Lucide Icons](https://lucide.dev/) via bundle UMD local (`ui/lib/lucide.min.js`). Reemplaza ~120 lineas de SVGs hardcodeados por etiquetas `<i data-lucide="...">`.
- **Avatar de preset**: cuando la sidebar esta colapsada, los presets muestran la primera letra del nombre en un circulo (estilo avatar) en vez de un circulo vacio.

### Changed

- Sidebar: de 240px fijo a 240px expandible con animacion de transicion (0.25s ease).
- Sidebar colapsada muestra solo iconos a 48px de ancho con tooltips contextuales.
- Botones de Configuracion (Restablecer, Actualizaciones, Acerca de) ahora tienen iconos SVG dedicados (rotate-ccw, refresh-cw, info).
- Boton eliminar preset cambia de `×` texto a icono Lucide `x`.
- Modal de actualizacion: icono SVG inline reemplazado por `<i data-lucide="download">`.
- Icono "Restablecer Todo" actualizado a `rotate-ccw` (icono de reset estandar) a 16x16, consistente con los demas iconos de la seccion.

## [1.3.4] - 2026-04-20

### Fixed

- La verificacion automatica de actualizaciones al iniciar fallaba silenciosamente: ahora muestra un toast con el error especifico (HTTP, red, etc.)
- Error en el check de actualizaciones al inicio ya no se ignora: el usuario recibe feedback claro de que algo fallo

## [1.3.3] - 2026-04-17

### Fixed

- Error "Error de red. Verifica tu conexion a internet" al verificar actualizaciones desde la app empaquetada
- Certificados SSL CA no estaban incluidos en el bundle de PyInstaller, impidiendo conexiones HTTPS
- `updater.py` ahora usa `certifi` como fuente de certificados CA con fallback al sistema
- `build.spec` actualizado para incluir `certifi` en hiddenimports y `cacert.pem` como data file

## [1.3.2] - 2026-04-17

### Fixed

- Crash al presionar "Buscar Actualizaciones" multiples veces: la llamada API bloqueaba el hilo principal de la UI
- El contenedor de toasts faltaba en el HTML, causando errores JS silenciosos que colgaban la app
- `check_for_updates` ahora se ejecuta en un thread separado via `start_update_check` + `get_update_check_result` (polling)
- `download_and_prepare_update` renombrado a `start_update_download` — se ejecuta en thread con polling de progreso
- Boton "Buscar Actualizaciones" se deshabilita durante la verificacion para evitar multiples clics
- Mejor manejo de errores de red: mensajes diferenciados para HTTP errors, errores de conexion, etc.

## [1.3.1] - 2026-04-17

### Added

- Sistema de actualizaciones mejorado: modal con release notes, boton "Saltar esta version" y "Ver en GitHub"
- Auto-descarga de actualizaciones: descarga el .zip, extrae y abre Finder para reemplazar la app
- Filtro de asset arm64 en el updater (prioriza .zip con arm64 en el nombre)
- Skip version persistente: si el usuario salta una version, no se le notifica de nuevo hasta la siguiente
- Manejo de errores de red en el updater: muestra mensajes claros (HTTP error, sin conexion)
- Dialogo "Acerca de" con credito del autor (MigelAngelEC)
- Repo hecho publico para que el updater funcione sin autenticacion

### Changed

- Updater: `check_for_updates()` ahora acepta `skip_version` y devuelve `release_notes`
- Updater: manejo de errores diferenciado (HTTPError, URLError, Exception generica)
- API: nuevos metodos `skip_update()`, `clear_skip_version()`, `download_and_prepare_update()`, `get_download_progress()`, `reveal_update()`

## [1.3.0] - 2026-04-17

### Added

- Presets (Recetas) como chips horizontales con wrap en la sidebar — mejor aprovechamiento del espacio
- Botones de Importar/Exportar JSON directamente en la sidebar junto a "Nueva Receta"
- Navegacion de preview con botones prev/next y wrap-around (primera ↔ ultima imagen)
- Tooltip CSS custom en el nombre de imagen del preview (hover muestra nombre completo)
- Nombre de archivo del preview es "pressable" — click expande el texto completo

### Changed

- Sidebar reorganizada: Import/Export movidos del dropdown del header a la sidebar
- Eliminado el dropdown menu del header (ya no es necesario)
- Layout del preview mejorado: imagenes ya no se desbordan del marco al redimensionar la ventana
- Sidebar y contenido principal con scroll independiente

### Fixed

- Botones de navegacion del preview (prev/next) no tenian event listeners asignados
- Preview se salia del marco del contenedor al mostrar imagenes grandes
- Tests: `webp_quality` renombrado a `output_quality` en test_config.py (bug pre-existente)

## [1.2.1] - 2026-03-27

### Fixed

- Dropdown menu: clicks en "Buscar actualizaciones" y "Acerca de" no ejecutaban la accion (evento burbuja cerraba el menu antes del handler)
- Resultados de "Buscar actualizaciones" y "Acerca de" ahora se muestran en un modal dialog centrado en pantalla (antes solo aparecian en la barra de estado al fondo, dificil de ver)

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
