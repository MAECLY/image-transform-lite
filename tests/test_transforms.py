import pytest
from PIL import Image

from app.transforms import (
    flip_image,
    rotate_image,
    safe_square_crop,
    resize_image,
    adjust_brightness,
    adjust_contrast,
    adjust_sharpness,
    watermark_image,
)


def _make_rgb(w=100, h=100, color=(255, 0, 0)):
    return Image.new("RGB", (w, h), color)


def _make_rgba(w=100, h=100, color=(255, 0, 0, 255)):
    return Image.new("RGBA", (w, h), color)


class TestFlip:
    def test_horizontal(self):
        img = _make_rgb()
        img.putpixel((0, 0), (0, 255, 0))
        flipped = flip_image(img, "horizontal")
        assert flipped.getpixel((99, 0)) == (0, 255, 0)

    def test_vertical(self):
        img = _make_rgb()
        img.putpixel((0, 0), (0, 255, 0))
        flipped = flip_image(img, "vertical")
        assert flipped.getpixel((0, 99)) == (0, 255, 0)

    def test_invalid_direction(self):
        with pytest.raises(ValueError):
            flip_image(_make_rgb(), "diagonal")


class TestRotate:
    def test_returns_rgba(self):
        result = rotate_image(_make_rgb(), 45)
        assert result.mode == "RGBA"

    def test_expand(self):
        img = _make_rgb(100, 100)
        result = rotate_image(img, 45)
        assert result.width > 100 or result.height > 100

    def test_zero_degrees(self):
        img = _make_rgb(50, 50)
        result = rotate_image(img, 0)
        assert result.size == (50, 50)


class TestSafeSquareCrop:
    def test_rgb_center_crop(self):
        img = _make_rgb(200, 100)
        result = safe_square_crop(img)
        assert result.width == result.height == 100

    def test_rgba_opaque(self):
        img = _make_rgba(100, 100)
        result = safe_square_crop(img)
        assert result.width == result.height

    def test_after_rotation(self):
        img = _make_rgb(100, 100)
        rotated = rotate_image(img, 10)
        cropped = safe_square_crop(rotated)
        assert cropped.width == cropped.height
        assert cropped.width > 10


class TestResize:
    def test_percentage_100_noop(self):
        img = _make_rgb(100, 100)
        result = resize_image(img, "percentage", percentage=100)
        assert result.size == (100, 100)

    def test_percentage_50(self):
        img = _make_rgb(100, 100)
        result = resize_image(img, "percentage", percentage=50)
        assert result.size == (50, 50)

    def test_dimensions_keep_aspect(self):
        img = _make_rgb(200, 100)
        result = resize_image(img, "dimensions", width=100, height=100, keep_aspect=True)
        assert result.width == 100
        assert result.height == 50

    def test_dimensions_no_aspect(self):
        img = _make_rgb(200, 100)
        result = resize_image(img, "dimensions", width=50, height=50, keep_aspect=False)
        assert result.size == (50, 50)


class TestEnhancements:
    def test_brightness_noop(self):
        img = _make_rgb()
        result = adjust_brightness(img, 1.0)
        assert result.size == img.size

    def test_brightness_brighter(self):
        img = _make_rgb(10, 10, (100, 100, 100))
        result = adjust_brightness(img, 1.5)
        r, g, b = result.getpixel((5, 5))
        assert r > 100

    def test_contrast_noop(self):
        img = _make_rgb()
        result = adjust_contrast(img, 1.0)
        assert result.size == img.size

    def test_contrast_higher(self):
        img = _make_rgb(10, 10, (80, 150, 200))
        result = adjust_contrast(img, 2.0)
        r, g, b = result.getpixel((5, 5))
        assert r != 80 or g != 150 or b != 200

    def test_sharpness_noop(self):
        img = _make_rgb()
        result = adjust_sharpness(img, 1.0)
        assert result.size == img.size


class TestWatermark:
    def test_empty_text_noop(self):
        img = _make_rgb()
        result = watermark_image(img, text="")
        assert result.size == img.size

    def test_adds_text_returns_rgba(self):
        img = _make_rgb()
        result = watermark_image(img, text="TEST", font_size=16, opacity=128)
        assert result.mode == "RGBA"
        assert result.size == img.size

    def test_different_opacity(self):
        img = _make_rgb(200, 200)
        low = watermark_image(img, text="HI", font_size=16, opacity=50)
        high = watermark_image(img, text="HI", font_size=16, opacity=200)
        assert low.tobytes() != high.tobytes()

    def test_all_positions(self):
        img = _make_rgb(200, 200)
        for pos in ("top-left", "top-right", "bottom-left", "bottom-right", "center"):
            result = watermark_image(img, text="X", font_size=16, position=pos)
            assert result.size == img.size

    def test_rgba_input(self):
        img = _make_rgba(100, 100)
        result = watermark_image(img, text="WM", font_size=16)
        assert result.mode == "RGBA"
