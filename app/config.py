import json
import os
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

from app.platform_utils import normalize_os, user_config_dir


DEFAULT_ORDER = [
    "flip",
    "rotate",
    "crop",
    "resize",
    "brightness",
    "contrast",
    "sharpness",
    "watermark",
]


@dataclass
class AppConfig:
    # Flip
    flip_enabled: bool = True
    flip_direction: str = "horizontal"  # "horizontal" | "vertical"

    # Rotate
    rotate_enabled: bool = True
    rotate_degrees: int = 2

    # Safe square crop
    crop_enabled: bool = True

    # Resize
    resize_enabled: bool = False
    resize_mode: str = "percentage"  # "percentage" | "dimensions"
    resize_percentage: int = 100
    resize_width: int = 0
    resize_height: int = 0
    resize_keep_aspect: bool = True

    # Brightness
    brightness_enabled: bool = False
    brightness_factor: float = 1.0

    # Contrast
    contrast_enabled: bool = False
    contrast_factor: float = 1.0

    # Sharpness
    sharpness_enabled: bool = False
    sharpness_factor: float = 1.0

    # Watermark
    watermark_enabled: bool = False
    watermark_text: str = ""
    watermark_font_size: int = 32
    watermark_opacity: int = 128
    watermark_position: str = "bottom-right"

    # Transform execution order
    transform_order: list = field(default_factory=lambda: list(DEFAULT_ORDER))

    # Output
    output_format: str = "webp"  # "webp" | "jpeg" | "png" | "tiff"
    output_quality: int = 90

    # Directories
    input_dir: str = "input_files"
    output_dir: str = "output_files"

    # Update
    skip_version: str = ""

    @classmethod
    def _config_path(cls) -> Path:
        if getattr(sys, "frozen", False):
            config_dir = user_config_dir()
            config_dir.mkdir(parents=True, exist_ok=True)
            return config_dir / "config.json"
        return Path(__file__).resolve().parent.parent / "config.json"

    @classmethod
    def load(cls) -> "AppConfig":
        path = cls._config_path()
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                return cls.from_dict(data)
            except Exception:
                pass
        return cls()

    def save(self) -> None:
        path = self._config_path()
        path.write_text(
            json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "AppConfig":
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        cfg = cls(**filtered)
        existing = set(cfg.transform_order)
        for name in DEFAULT_ORDER:
            if name not in existing:
                cfg.transform_order.append(name)
        return cfg

    def resolve_input_dir(self) -> Path:
        p = Path(self.input_dir)
        if p.is_absolute():
            return p
        return _app_base_dir() / p

    def resolve_output_dir(self) -> Path:
        p = Path(self.output_dir)
        if p.is_absolute():
            return p
        return _app_base_dir() / p

    @classmethod
    def get_presets_dir(cls) -> Path:
        if getattr(sys, "frozen", False):
            config_dir = user_config_dir()
        else:
            config_dir = _app_base_dir()

        presets_dir = config_dir / "presets"
        presets_dir.mkdir(parents=True, exist_ok=True)
        return presets_dir


def _app_base_dir() -> Path:
    """Base dir for the relative default input_files/output_files folders."""
    if getattr(sys, "frozen", False):
        exe = Path(sys.executable).resolve()
        if normalize_os() == "macos":
            # .../X/Image Transform Lite.app/Contents/MacOS/<exe> -> X
            # (the folder containing the .app, unchanged since v1.0).
            return exe.parent.parent.parent.parent
        # Windows/Linux PyInstaller onedir: .../X/<app folder>/<exe>.
        # Use X (the folder containing the app folder) so the layout mirrors
        # macOS: input_files/output_files sit next to the app folder, where the
        # user extracted the zip/tar.gz, and are not wiped when the app folder
        # is replaced on update. If X is not writable (e.g. the app was moved
        # into C:\Program Files or /opt), fall back to the user's home, which
        # is always writable.
        base = exe.parent.parent
        if _is_writable_dir(base):
            return base
        return Path.home()
    return Path(__file__).resolve().parent.parent


def _is_writable_dir(path: Path) -> bool:
    try:
        return path.is_dir() and os.access(path, os.W_OK)
    except OSError:
        return False
