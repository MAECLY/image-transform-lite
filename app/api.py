import subprocess

from app.config import AppConfig
from app.processor import BatchProcessor, discover_images
from app.updater import check_for_updates as _check_updates
from app.version import __version__


class Api:
    def __init__(self, config: AppConfig, window=None):
        self.config = config
        self.window = window
        self._processor: BatchProcessor | None = None

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
            items.append({
                "name": f.name,
                "relative_path": str(rel),
                "size": f.stat().st_size,
            })
        return {"count": len(items), "files": items}

    def process_images(self) -> dict:
        if self._processor and self._processor.running:
            return {"error": "Ya hay un proceso en ejecución"}
        self._processor = BatchProcessor(self.config)
        self._processor.start()
        return {"started": True}

    def get_progress(self) -> dict:
        if self._processor is None:
            return {"current": 0, "total": 0, "current_file": "", "done": True, "errors": []}
        return self._processor.progress()

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

    def open_output_directory(self) -> None:
        out_dir = self.config.resolve_output_dir()
        out_dir.mkdir(parents=True, exist_ok=True)
        subprocess.Popen(["open", str(out_dir)])

    def get_version(self) -> str:
        return __version__

    def check_for_updates(self) -> dict:
        return _check_updates(__version__)

    def reset_config(self) -> dict:
        self.config = AppConfig()
        self.config.save()
        return self.config.to_dict()
