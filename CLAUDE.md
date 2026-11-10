# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
make install      # Create venv (Python 3.11) + install deps
make test         # Run all tests
make run          # Run app in dev mode
make run-debug    # Run with pywebview dev console
make build        # Build the app for the current OS/arch (PyInstaller)
make dist         # Build + archive for distribution
make clean-all    # Remove build artifacts + venv
```

## Architecture

Cross-platform desktop app (macOS, Windows, Linux; arm64 + x64) for batch image transforms. Python 3.11 backend + HTML/CSS/JS frontend connected via **pywebview** (native webview window, no browser needed). Webview backend per OS: macOS Cocoa/WebKit, Windows EdgeChromium/WebView2 (pythonnet), Linux Qt (PyQt6 + PyQt6-WebEngine + qtpy, installed via `sys_platform == "linux"` markers in requirements.txt).

### Backend (`app/`)

- **main.py** — Entry point. Creates pywebview window pointing at `ui/index.html`, exposes `Api` to JS via `js_api`. Handles frozen (PyInstaller) vs dev path resolution.
- **config.py** — `AppConfig` dataclass with all transform parameters + execution order. Persists to JSON: `./config.json` in dev; in the frozen app `<config_dir>/config.json` where config_dir is `~/Library/Application Support/ImageTransformLite` (macOS), `%APPDATA%/ImageTransformLite` (Windows), `$XDG_CONFIG_HOME/ImageTransformLite` or `~/.config/ImageTransformLite` (Linux). Auto-saves on every UI change.
- **transforms.py** — 8 independent transform functions (flip, rotate, safe_square_crop, resize, brightness, contrast, sharpness, watermark) using Pillow. Each takes an `Image` and returns an `Image`.
- **processor.py** — `BatchProcessor` runs in a daemon thread. Discovers images recursively in input dir, applies transforms in `config.transform_order` (skipping disabled ones), saves as WebP. Frontend polls `progress()` for status.
- **api.py** — Methods exposed to JS: `get_config`, `save_config`, `process_images`, `get_progress`, `select_input_directory`, `select_output_directory`, `open_output_directory`, `get_platform_info`, `reset_config`, plus preview (`get_preview`, `get_input_files`), update (`get_version`, `start_update_check`, `start_update_download`, `reveal_update`, ...) and preset (`list_presets`, `save_named_preset`, `load_named_preset`, `delete_preset`, ...) methods.

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

- Python 3.11 + PyInstaller (`build.spec`). No cross-compilation: each target is built on its native GitHub Actions runner on tag push `v*`.
- Targets / runners: macOS arm64 `macos-15`, macOS x64 `macos-15-intel`, Windows x64 `windows-latest`, Windows arm64 `windows-11-arm` (x64 Python under emulation: pythonnet has no arm64 ClrLoader.dll), Linux x64 `ubuntu-22.04`, Linux arm64 `ubuntu-22.04-arm`. Tests run in CI on all 3 OSes.
- Release assets: `Image-Transform-Lite-<VERSION>-<os>-<arch>.<ext>` with os in {macos, windows, linux}, arch in {arm64, x64}:
  - macOS: `.pkg` + `.zip` (contains `Image Transform Lite.app`)
  - Windows: `.zip` (folder `Image Transform Lite/` with `Image Transform Lite.exe`)
  - Linux: `.tar.gz` (folder `image-transform-lite/` with executable, `.desktop`, icon png, `install.sh` -> `~/.local/share/applications`)
  - LEGACY `Image-Transform-Lite-<VERSION>-arm64.zip` = copy of the macos-arm64 zip, for v<=1.6 updaters (they pick the first `.zip` containing `arm64`). The release job creates the release with it uploaded FIRST, then uploads the rest. Do not remove.
- Updater picks the asset containing `-<os>-<arch>.` (AMD64/x86_64 -> x64, arm64/aarch64 -> arm64); prefers `.zip` on macOS, `.tar.gz` on Linux; never the legacy asset off macOS.
- Icons: `assets/icon.icns` (macOS), `assets/icon.ico` (Windows), `assets/icon.png` 512px (Linux).
- Bundle ID (macOS): `com.maecly.imagetransformlite`
- Builds are unsigned: macOS Gatekeeper (right-click -> Open), Windows SmartScreen ("Run anyway").
