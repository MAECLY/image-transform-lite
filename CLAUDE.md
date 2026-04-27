# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
make install      # Create venv (Python 3.11) + install deps
make test         # Run all tests
make run          # Run app in dev mode
make run-debug    # Run with pywebview dev console
make build        # Build dist/Image Transform Lite.app (arm64)
make dist         # Build + zip for distribution
make clean-all    # Remove build artifacts + venv
```

## Architecture

macOS desktop app for batch image transforms. Python 3.11 backend + HTML/CSS/JS frontend connected via **pywebview** (native WebKit window, no browser needed).

### Backend (`app/`)

- **main.py** — Entry point. Creates pywebview window pointing at `ui/index.html`, exposes `Api` to JS via `js_api`. Handles frozen (PyInstaller) vs dev path resolution.
- **config.py** — `AppConfig` dataclass with all transform parameters + execution order. Persists to JSON: `./config.json` in dev, `~/Library/Application Support/ImageTransformLite/config.json` in bundled app. Auto-saves on every UI change.
- **transforms.py** — 8 independent transform functions (flip, rotate, safe_square_crop, resize, brightness, contrast, sharpness, watermark) using Pillow. Each takes an `Image` and returns an `Image`.
- **processor.py** — `BatchProcessor` runs in a daemon thread. Discovers images recursively in input dir, applies transforms in `config.transform_order` (skipping disabled ones), saves as WebP. Frontend polls `progress()` for status.
- **api.py** — Methods exposed to JS: `get_config`, `save_config`, `process_images`, `get_progress`, `select_input_directory`, `select_output_directory`, `open_output_directory`, `reset_config`.

### Frontend (`ui/`)

- Single-page app. `app.js` waits for `pywebviewready` event, then calls `pywebview.api.*` methods.
- Transform cards rendered dynamically from `TRANSFORMS` object in `app.js`. Each card has enable checkbox + parameters + drag handle.
- **Sortable.js** handles drag-and-drop reordering of transforms. `onEnd` callback saves new order to config.
- Progress polling: after `process_images()` starts, JS polls `get_progress()` every 200ms.

### Data Flow

```
UI change → save_config(dict) → AppConfig.save() → config.json
Process click → process_images() → BatchProcessor thread
  discovers input_files/**/*.{jpg,png,...}
  for each: load → apply transforms in order → save as output_files/**/name.webp
  JS polls get_progress() → updates progress bar
```

Input/output directory structure is mirrored: `input_files/subfolder/img.jpg` → `output_files/subfolder/img.webp`.

## Key Patterns

- **Image mode handling**: P→RGBA, CMYK/YCbCr→RGB on load. EXIF orientation auto-corrected. Output always RGB for WebP.
- **safe_square_crop**: After rotation (which adds transparent corners), iteratively shrinks a center square until all 4 corners have alpha > 0. Falls back to simple center crop for non-RGBA images.
- **Error resilience**: Per-image errors are caught and collected, batch continues. Errors shown in UI after completion.
- **Frozen detection**: `sys.frozen` and `sys._MEIPASS` for PyInstaller bundle paths.

## Adding a New Transform

1. Add function in `app/transforms.py`
2. Add config fields (`*_enabled`, params) + update `DEFAULT_ORDER` in `app/config.py`
3. Add case in `apply_transforms()` in `app/processor.py`
4. Add entry in `TRANSFORMS` object in `ui/app.js` with `enabledKey` and `params` generator
5. Add tests in `tests/test_transforms.py`

## Build & Distribution

- Uses Python 3.11 (`/opt/homebrew/opt/python@3.11/bin/python3.11`) for PyInstaller compatibility
- Target: arm64 macOS only
- Bundle ID: `com.fiftyflowers.imagetransformlite`
- Recipients bypass Gatekeeper with right-click → Open on first launch
