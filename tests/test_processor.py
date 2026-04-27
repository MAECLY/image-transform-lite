import pytest
from PIL import Image
from pathlib import Path

from app.config import AppConfig
from app.processor import (
    discover_images,
    load_image,
    apply_transforms,
    save_image,
    BatchProcessor,
    IMAGE_EXTENSIONS,
)


def _make_rgb(w=100, h=100, color=(255, 0, 0)):
    return Image.new("RGB", (w, h), color)


def _write_img(path: Path, fmt: str = "PNG", size=(100, 100), color=(255, 0, 0)):
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", size, color)
    img.save(str(path), format=fmt)


class TestDiscoverImages:
    def test_empty_dir(self, tmp_path):
        assert discover_images(tmp_path) == []

    def test_nonexistent_dir(self):
        assert discover_images(Path("/nonexistent/path")) == []

    def test_finds_valid_extensions(self, tmp_path):
        for ext in IMAGE_EXTENSIONS:
            _write_img(tmp_path / f"img{ext}")
        result = discover_images(tmp_path)
        assert len(result) == len(IMAGE_EXTENSIONS)

    def test_ignores_invalid_extensions(self, tmp_path):
        (tmp_path / "doc.txt").write_text("hello")
        (tmp_path / "data.csv").write_text("1,2")
        _write_img(tmp_path / "img.jpg")
        result = discover_images(tmp_path)
        assert len(result) == 1

    def test_recursive_discovery(self, tmp_path):
        _write_img(tmp_path / "top.jpg")
        sub = tmp_path / "subdir"
        _write_img(sub / "nested.png")
        result = discover_images(tmp_path)
        assert len(result) == 2

    def test_ignores_directories(self, tmp_path):
        (tmp_path / "images").mkdir()
        _write_img(tmp_path / "images" / "photo.jpg")
        _write_img(tmp_path / "real.webp")
        result = discover_images(tmp_path)
        assert len(result) == 2

    def test_case_insensitive_extension(self, tmp_path):
        _write_img(tmp_path / "upper.JPG")
        _write_img(tmp_path / "lower.jpg")
        result = discover_images(tmp_path)
        assert len(result) == 2


class TestLoadImage:
    def test_rgb_image(self, tmp_path):
        path = tmp_path / "rgb.png"
        _make_rgb().save(str(path), format="PNG")
        img = load_image(path)
        assert img.mode in ("RGB", "RGBA")

    def test_palette_mode_converted(self, tmp_path):
        path = tmp_path / "pal.png"
        Image.new("P", (10, 10)).save(str(path), format="PNG")
        img = load_image(path)
        assert img.mode == "RGBA"

    def test_cmyk_converted(self, tmp_path):
        path = tmp_path / "cmyk.jpg"
        Image.new("CMYK", (10, 10)).save(str(path), format="JPEG")
        img = load_image(path)
        assert img.mode == "RGB"

    def test_rgba_preserved(self, tmp_path):
        path = tmp_path / "rgba.png"
        Image.new("RGBA", (10, 10), (255, 0, 0, 128)).save(str(path), format="PNG")
        img = load_image(path)
        assert img.mode == "RGBA"

    def test_nonexistent_raises(self):
        with pytest.raises(Exception):
            load_image(Path("/nonexistent/image.png"))


class TestApplyTransforms:
    def test_all_disabled(self):
        cfg = AppConfig()
        cfg.flip_enabled = False
        cfg.rotate_enabled = False
        cfg.crop_enabled = False
        cfg.resize_enabled = False
        cfg.brightness_enabled = False
        cfg.contrast_enabled = False
        cfg.sharpness_enabled = False
        cfg.watermark_enabled = False
        img = _make_rgb(100, 100)
        result = apply_transforms(img, cfg)
        assert result.size == (100, 100)

    def test_flip_applied(self):
        cfg = AppConfig()
        cfg.flip_enabled = True
        cfg.flip_direction = "horizontal"
        cfg.rotate_enabled = False
        cfg.crop_enabled = False
        cfg.resize_enabled = False
        cfg.brightness_enabled = False
        cfg.contrast_enabled = False
        cfg.sharpness_enabled = False
        cfg.watermark_enabled = False
        img = _make_rgb(100, 100)
        img.putpixel((0, 0), (0, 255, 0))
        result = apply_transforms(img, cfg)
        assert result.getpixel((99, 0)) == (0, 255, 0)

    def test_resize_applied(self):
        cfg = AppConfig()
        cfg.flip_enabled = False
        cfg.rotate_enabled = False
        cfg.crop_enabled = False
        cfg.resize_enabled = True
        cfg.resize_mode = "percentage"
        cfg.resize_percentage = 50
        cfg.brightness_enabled = False
        cfg.contrast_enabled = False
        cfg.sharpness_enabled = False
        cfg.watermark_enabled = False
        img = _make_rgb(200, 100)
        result = apply_transforms(img, cfg)
        assert result.size == (100, 50)

    def test_custom_order(self):
        cfg = AppConfig()
        cfg.flip_enabled = False
        cfg.rotate_enabled = False
        cfg.crop_enabled = False
        cfg.resize_enabled = True
        cfg.resize_mode = "percentage"
        cfg.resize_percentage = 50
        cfg.brightness_enabled = False
        cfg.contrast_enabled = False
        cfg.sharpness_enabled = False
        cfg.watermark_enabled = False
        cfg.transform_order = ["resize"]
        img = _make_rgb(200, 100)
        result = apply_transforms(img, cfg)
        assert result.size == (100, 50)

    def test_pipeline_multiple(self):
        cfg = AppConfig()
        cfg.flip_enabled = True
        cfg.flip_direction = "horizontal"
        cfg.rotate_enabled = False
        cfg.crop_enabled = False
        cfg.resize_enabled = True
        cfg.resize_mode = "percentage"
        cfg.resize_percentage = 50
        cfg.brightness_enabled = False
        cfg.contrast_enabled = False
        cfg.sharpness_enabled = False
        cfg.watermark_enabled = False
        img = _make_rgb(200, 100)
        result = apply_transforms(img, cfg)
        assert result.size == (100, 50)


class TestSaveImage:
    def test_save_webp(self, tmp_path):
        out = tmp_path / "out.webp"
        img = _make_rgb()
        save_image(img, out, "webp", quality=80)
        assert out.exists()

    def test_save_jpeg(self, tmp_path):
        out = tmp_path / "out.jpg"
        img = _make_rgb()
        save_image(img, out, "jpeg", quality=80)
        assert out.exists()

    def test_save_png(self, tmp_path):
        out = tmp_path / "out.png"
        img = _make_rgb()
        save_image(img, out, "png")
        assert out.exists()

    def test_save_tiff(self, tmp_path):
        out = tmp_path / "out.tiff"
        img = _make_rgb()
        save_image(img, out, "tiff")
        assert out.exists()

    def test_save_rgba_as_webp(self, tmp_path):
        out = tmp_path / "out.webp"
        img = Image.new("RGBA", (10, 10), (255, 0, 0, 128))
        save_image(img, out, "webp", quality=80)
        assert out.exists()

    def test_save_rgba_as_jpeg(self, tmp_path):
        out = tmp_path / "out.jpg"
        img = Image.new("RGBA", (10, 10), (255, 0, 0, 128))
        save_image(img, out, "jpeg", quality=80)
        assert out.exists()

    def test_creates_subdirectories(self, tmp_path):
        out = tmp_path / "sub" / "dir" / "out.png"
        img = _make_rgb()
        save_image(img, out, "png")
        assert out.exists()


class TestBatchProcessor:
    def test_zero_images(self, tmp_path):
        cfg = AppConfig()
        cfg.input_dir = str(tmp_path)
        cfg.output_dir = str(tmp_path / "out")
        bp = BatchProcessor(cfg)
        bp._run()
        assert bp.done is True
        assert bp.total == 0

    def test_progress_format(self, tmp_path):
        cfg = AppConfig()
        cfg.input_dir = str(tmp_path)
        cfg.output_dir = str(tmp_path / "out")
        bp = BatchProcessor(cfg)
        p = bp.progress()
        assert "current" in p
        assert "total" in p
        assert "current_file" in p
        assert "done" in p
        assert "errors" in p

    def test_error_does_not_stop_batch(self, tmp_path):
        _write_img(tmp_path / "good.jpg")
        (tmp_path / "bad.jpg").write_text("not an image")
        _write_img(tmp_path / "also_good.png")
        cfg = AppConfig()
        cfg.input_dir = str(tmp_path)
        cfg.output_dir = str(tmp_path / "out")
        cfg.flip_enabled = False
        cfg.rotate_enabled = False
        cfg.crop_enabled = False
        cfg.resize_enabled = False
        cfg.brightness_enabled = False
        cfg.contrast_enabled = False
        cfg.sharpness_enabled = False
        cfg.watermark_enabled = False
        bp = BatchProcessor(cfg)
        bp._run()
        assert bp.done is True
        assert len(bp.errors) == 1
        assert bp.current == 3

    def test_running_property(self):
        cfg = AppConfig()
        bp = BatchProcessor(cfg)
        assert bp.running is False

    def test_start_guard(self):
        cfg = AppConfig()
        bp = BatchProcessor(cfg)
        bp.start()
        assert bp.running is True
        bp.start()
        bp._thread.join(timeout=5)