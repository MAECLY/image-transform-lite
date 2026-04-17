import json
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path


DEFAULT_ORDER = [
    "flip",
    "rotate",
    "crop",
    "resize",
    "brightness",
    "contrast",
    "sharpness",
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
            config_dir = (
                Path.home() / "Library" / "Application Support" / "ImageTransformLite"
            )
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
        return cls(**filtered)

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
            config_dir = (
                Path.home() / "Library" / "Application Support" / "ImageTransformLite"
            )
        else:
            config_dir = _app_base_dir()

        presets_dir = config_dir / "presets"
        presets_dir.mkdir(parents=True, exist_ok=True)
        return presets_dir


def _app_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent.parent.parent.parent
    return Path(__file__).resolve().parent.parent
