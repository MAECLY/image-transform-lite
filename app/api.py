import logging
import subprocess
import io
import base64
import json
import threading
from pathlib import Path

from app.config import AppConfig
from app.processor import BatchProcessor, discover_images
from app.updater import (
    check_for_updates as _check_updates,
    download_update as _download_update,
    extract_update as _extract_update,
    reveal_in_finder as _reveal_in_finder,
)
from app.version import __version__

log = logging.getLogger(__name__)


class Api:
    def __init__(self, config: AppConfig, window=None):
        self.config = config
        self.window = window
        self._processor: BatchProcessor | None = None
        self._update_check_result: dict | None = None
        self._update_check_done: threading.Event = threading.Event()
        self._update_download_result: dict | None = None
        self._update_download_progress: dict = {"downloaded": 0, "total": 0}
        self._update_download_done: threading.Event = threading.Event()
        self._downloaded_app_path: str | None = None

    def get_config(self) -> dict:
        return self.config.to_dict()

    def save_config(self, config_dict: dict) -> dict:
        self.config = AppConfig.from_dict(config_dict)
        self.config.save()
        return self.config.to_dict()

    def get_input_files(self) -> dict:
        input_dir = self.config.resolve_input_dir()
        files = discover_images(input_dir)
        items = []
        for f in files:
            rel = f.relative_to(input_dir)
            items.append(
                {
                    "name": f.name,
                    "relative_path": str(rel),
                    "size": f.stat().st_size,
                }
            )
        return {"count": len(items), "files": items}

    def process_images(self) -> dict:
        if self._processor and self._processor.running:
            return {"error": "Ya hay un proceso en ejecución"}
        self._processor = BatchProcessor(self.config)
        self._processor.start()
        return {"started": True}

    def get_progress(self) -> dict:
        if self._processor is None:
            return {
                "current": 0,
                "total": 0,
                "current_file": "",
                "done": True,
                "errors": [],
            }
        return self._processor.progress()

    def get_preview(
        self, config_dict: dict, image_path: str | None = None, index: int | None = None
    ) -> dict:
        try:
            # Use the provided config or current app config
            current_cfg = AppConfig.from_dict(config_dict)

            # If no image_path is provided, try to pick the image by index or first available
            input_dir = self.config.resolve_input_dir()
            files = discover_images(input_dir)

            if not files:
                return {"error": "No images found in input directory for preview"}

            if image_path:
                path = Path(image_path)
            elif index is not None:
                # Clamp index to available range
                safe_index = max(0, min(index, len(files) - 1))
                path = files[safe_index]
            else:
                path = files[0]

            if not path.exists():
                return {"error": "Preview image file not found"}

            from app.processor import get_preview_base64

            preview_b64 = get_preview_base64(path, current_cfg)

            # Also return the original image for a B&A comparison
            from app.processor import load_image

            img_orig = load_image(path)
            buf_orig = io.BytesIO()
            # Simple conversion for original preview
            if img_orig.mode not in ("RGB", "L"):
                img_orig = img_orig.convert("RGB")
            img_orig.save(buf_orig, format="WEBP", quality=80)
            orig_b64 = base64.b64encode(buf_orig.getvalue()).decode()

            return {
                "preview": preview_b64,
                "original": f"data:image/webp;base64,{orig_b64}",
                "filename": path.name,
                "index": files.index(path) if path in files else 0,
                "total": len(files),
            }
        except Exception as e:
            return {"error": str(e)}

    def select_input_directory(self) -> str | None:
        if self.window is None:
            return None
        result = self.window.create_file_dialog(
            dialog_type=20,  # FOLDER_DIALOG
        )
        if result and len(result) > 0:
            chosen = result[0]
            self.config.input_dir = chosen
            self.config.save()
            return chosen
        return None

    def select_output_directory(self) -> str | None:
        if self.window is None:
            return None
        result = self.window.create_file_dialog(
            dialog_type=20,  # FOLDER_DIALOG
        )
        if result and len(result) > 0:
            chosen = result[0]
            self.config.output_dir = chosen
            self.config.save()
            return chosen
        return None

    def select_preset_file(self) -> str | None:
        if self.window is None:
            return None
        result = self.window.create_file_dialog(
            dialog_type=10,
            file_types=("JSON Files (*.json)",),
        )
        if result and len(result) > 0:
            return result[0]
        return None

    def open_output_directory(self) -> None:
        out_dir = self.config.resolve_output_dir()
        out_dir.mkdir(parents=True, exist_ok=True)
        subprocess.Popen(["open", str(out_dir)])

    def get_version(self) -> str:
        return __version__

    def check_for_updates(self) -> dict:
        return _check_updates(__version__, skip_version=self.config.skip_version)

    def start_update_check(self) -> dict:
        self._update_check_done.clear()
        self._update_check_result = None

        def _run():
            try:
                self._update_check_result = _check_updates(
                    __version__, skip_version=self.config.skip_version
                )
            except Exception as e:
                log.error("Update check thread error: %s", e)
                self._update_check_result = {"update_available": False, "error": str(e)}
            finally:
                self._update_check_done.set()

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        return {"started": True}

    def get_update_check_result(self) -> dict:
        if not self._update_check_done.is_set():
            return {"done": False}
        result = self._update_check_result or {"update_available": False}
        return {"done": True, **result}

    def skip_update(self, version: str) -> dict:
        self.config.skip_version = version
        self.config.save()
        return {"success": True}

    def clear_skip_version(self) -> dict:
        self.config.skip_version = ""
        self.config.save()
        return {"success": True}

    def start_update_download(self, download_url: str) -> dict:
        self._update_download_done.clear()
        self._update_download_result = None
        self._update_download_progress = {"downloaded": 0, "total": 0}

        def _run():
            try:

                def on_progress(downloaded: int, total: int):
                    self._update_download_progress = {
                        "downloaded": downloaded,
                        "total": total,
                    }

                zip_path = _download_update(download_url, on_progress=on_progress)
                app_path = _extract_update(zip_path)
                self._downloaded_app_path = app_path
                self._update_download_result = {"success": True, "app_path": app_path}
            except Exception as e:
                log.error("Update download failed: %s", e)
                self._update_download_result = {"error": str(e)}
            finally:
                self._update_download_done.set()

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        return {"started": True}

    def get_download_progress(self) -> dict:
        prog = dict(self._update_download_progress)
        prog["done"] = self._update_download_done.is_set()
        if self._update_download_done.is_set() and self._update_download_result:
            prog["result"] = self._update_download_result
        return prog

    def reveal_update(self) -> dict:
        app_path = self._downloaded_app_path
        if not app_path:
            return {"error": "No update downloaded"}
        _reveal_in_finder(app_path)
        return {"success": True}

    def reset_config(self) -> dict:
        self.config = AppConfig()
        self.config.save()
        return self.config.to_dict()

    def list_presets(self) -> list[str]:
        try:
            presets_dir = AppConfig.get_presets_dir()
            return [f.stem for f in presets_dir.glob("*.json")]
        except Exception as e:
            log.error("Error listing presets: %s", e)
            return []

    def save_named_preset(self, name: str, config_dict: dict) -> dict:
        try:
            presets_dir = AppConfig.get_presets_dir()
            # Clean name to avoid filesystem issues
            safe_name = "".join(
                c for c in name if c.isalnum() or c in (" ", "_", "-")
            ).strip()
            if not safe_name:
                return {"error": "Nombre de preset inválido"}

            path = presets_dir / f"{safe_name}.json"

            # Save only transform settings, not directories
            save_data = {
                k: v
                for k, v in config_dict.items()
                if k not in ("input_dir", "output_dir")
            }

            path.write_text(json.dumps(save_data, indent=2), encoding="utf-8")
            return {"success": True, "name": safe_name}
        except Exception as e:
            return {"error": str(e)}

    def load_named_preset(self, name: str) -> dict:
        try:
            presets_dir = AppConfig.get_presets_dir()
            path = presets_dir / f"{name}.json"

            if not path.exists():
                return {"error": "Preset no encontrado"}

            data = json.loads(path.read_text(encoding="utf-8"))
            # Merge preset data into current config to keep directories
            current_data = self.config.to_dict()
            merged_data = {**current_data, **data}

            self.config = AppConfig.from_dict(merged_data)
            self.config.save()
            return self.config.to_dict()
        except Exception as e:
            return {"error": str(e)}

    def delete_preset(self, name: str) -> dict:
        try:
            presets_dir = AppConfig.get_presets_dir()
            path = presets_dir / f"{name}.json"
            if path.exists():
                path.unlink()
                return {"success": True}
            return {"error": "Preset no encontrado"}
        except Exception as e:
            return {"error": str(e)}

    def save_preset(self, config_dict: dict) -> dict:
        try:
            if self.window is None:
                return {"error": "Window not available"}

            result = self.window.create_file_dialog(
                dialog_type=30,  # SAVE_DIALOG
            )

            if not result or not result or len(result) == 0 or not result[0]:
                return {"canceled": True}

            path_str = result[0]
            chosen_path = Path(path_str)

            if chosen_path.name == "":
                return {"error": "Invalid file path selected"}

            if chosen_path.suffix.lower() != ".json":
                chosen_path = chosen_path.with_suffix(".json")

            save_data = {
                k: v
                for k, v in config_dict.items()
                if k not in ("input_dir", "output_dir")
            }

            chosen_path.write_text(json.dumps(save_data, indent=2), encoding="utf-8")
            return {
                "success": True,
                "path": str(chosen_path),
                "filename": chosen_path.name,
            }
        except Exception as e:
            return {"error": str(e)}

    def load_preset(self, path_str: str) -> dict:
        try:
            path = Path(path_str)
            if not path.exists():
                return {"error": "Preset file not found"}

            data = json.loads(path.read_text(encoding="utf-8"))
            # Merge preset data into current config
            # We preserve the directories so the user doesn't lose their paths
            current_cfg = AppConfig.from_dict(self.config.to_dict())
            updated_cfg = AppConfig.from_dict({**self.config.to_dict(), **data})

            self.config = updated_cfg
            self.config.save()
            return self.config.to_dict()
        except Exception as e:
            return {"error": str(e)}
