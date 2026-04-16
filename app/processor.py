import logging
import threading
import base64
import io
from pathlib import Path

from PIL import Image, ImageOps

from app.config import AppConfig
from app.transforms import (
    flip_image,
    rotate_image,
    safe_square_crop,
    resize_image,
    adjust_brightness,
    adjust_contrast,
    adjust_sharpness,
)

log = logging.getLogger("processor")

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"}


def discover_images(input_dir: Path) -> list[Path]:
    if not input_dir.exists():
        return []
    files = []
    for p in sorted(input_dir.rglob("*")):
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS:
            files.append(p)
    return files


def load_image(path: Path) -> Image.Image:
    img = Image.open(path)
    try:
        exif = img.getexif()
        if exif:
            img = ImageOps.exif_transpose(img)
    except Exception:
        pass
    if img.mode == "P":
        img = img.convert("RGBA")
    elif img.mode in ("CMYK", "YCbCr"):
        img = img.convert("RGB")
    return img


def apply_transforms(img: Image.Image, config: AppConfig) -> Image.Image:
    for name in config.transform_order:
        if name == "flip" and config.flip_enabled:
            img = flip_image(img, config.flip_direction)
        elif name == "rotate" and config.rotate_enabled:
            img = rotate_image(img, config.rotate_degrees)
        elif name == "crop" and config.crop_enabled:
            img = safe_square_crop(img)
        elif name == "resize" and config.resize_enabled:
            img = resize_image(
                img,
                mode=config.resize_mode,
                percentage=config.resize_percentage,
                width=config.resize_width,
                height=config.resize_height,
                keep_aspect=config.resize_keep_aspect,
            )
        elif name == "brightness" and config.brightness_enabled:
            img = adjust_brightness(img, config.brightness_factor)
        elif name == "contrast" and config.contrast_enabled:
            img = adjust_contrast(img, config.contrast_factor)
        elif name == "sharpness" and config.sharpness_enabled:
            img = adjust_sharpness(img, config.sharpness_factor)
    return img


def get_preview_base64(image_path: Path, config: AppConfig) -> str:
    """Processes a single image and returns it as a base64 encoded string."""
    img = load_image(image_path)
    img = apply_transforms(img, config)
    
    # Convert to RGB for consistent base64 WebP output
    if img.mode == "RGBA":
        img = img.convert("RGB")
    elif img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
        
    buffered = io.BytesIO()
    img.save(buffered, format="WEBP", quality=80) # Lower quality for faster preview
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/webp;base64,{img_str}"


def save_image(img: Image.Image, path: Path, fmt: str, quality: int = 90) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Map format to Pillow format names
    format_map = {
        "webp": "WEBP",
        "jpeg": "JPEG",
        "png": "PNG",
        "tiff": "TIFF"
    }
    pillow_fmt = format_map.get(fmt.lower(), "WEBP")
    
    if pillow_fmt == "JPEG":
        if img.mode != "RGB":
            img = img.convert("RGB")
    elif pillow_fmt == "WEBP":
        if img.mode == "RGBA":
            img = img.convert("RGB")
        elif img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
    elif pillow_fmt not in ("PNG", "TIFF"):
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

    # Save using the determined format
    img.save(str(path), format=pillow_fmt, quality=quality, method=6 if pillow_fmt == "WEBP" else None)


# Removed save_webp as it's replaced by save_image
    path.parent.mkdir(parents=True, exist_ok=True)
    if img.mode == "RGBA":
        img = img.convert("RGB")
    elif img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    img.save(str(path), format="WEBP", quality=quality, method=6)


class BatchProcessor:
    def __init__(self, config: AppConfig):
        self.config = config
        self.current = 0
        self.total = 0
        self.current_file = ""
        self.done = False
        self.errors: list[dict] = []
        self._thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.running:
            return
        self.current = 0
        self.total = 0
        self.current_file = ""
        self.done = False
        self.errors = []
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        input_dir = self.config.resolve_input_dir()
        output_dir = self.config.resolve_output_dir()

        files = discover_images(input_dir)
        self.total = len(files)

        if self.total == 0:
            self.done = True
            return

        for i, file_path in enumerate(files):
            rel = file_path.relative_to(input_dir)
            
            # Determine output filename based on chosen format
            fmt = self.config.output_format.lower()
            ext = {
                "webp": ".webp",
                "jpeg": ".jpg",
                "png": ".png",
                "tiff": ".tiff"
            }.get(fmt, ".webp")
            
            out_path = output_dir / rel.with_suffix(ext)
            self.current = i + 1
            self.current_file = str(rel)

            try:
                img = load_image(file_path)
                img = apply_transforms(img, self.config)
                save_image(img, out_path, self.config.output_format, self.config.output_quality)
            except Exception as e:
                log.error("Error processing %s: %s", rel, e)
                self.errors.append({"file": str(rel), "error": str(e)})

        self.done = True

    def progress(self) -> dict:
        return {
            "current": self.current,
            "total": self.total,
            "current_file": self.current_file,
            "done": self.done,
            "errors": self.errors,
        }
