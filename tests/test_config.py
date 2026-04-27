import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from app.config import AppConfig, DEFAULT_ORDER


class TestAppConfig:
    def test_defaults(self):
        cfg = AppConfig()
        assert cfg.flip_enabled is True
        assert cfg.flip_direction == "horizontal"
        assert cfg.rotate_degrees == 2
        assert cfg.crop_enabled is True
        assert cfg.resize_enabled is False
        assert cfg.brightness_factor == 1.0
        assert cfg.contrast_factor == 1.0
        assert cfg.sharpness_factor == 1.0
        assert cfg.transform_order == list(DEFAULT_ORDER)
        assert cfg.output_quality == 90

    def test_to_dict_and_from_dict(self):
        cfg = AppConfig(flip_direction="vertical", rotate_degrees=5)
        d = cfg.to_dict()
        assert d["flip_direction"] == "vertical"
        assert d["rotate_degrees"] == 5

        cfg2 = AppConfig.from_dict(d)
        assert cfg2.flip_direction == "vertical"
        assert cfg2.rotate_degrees == 5

    def test_from_dict_ignores_unknown(self):
        cfg = AppConfig.from_dict({"flip_enabled": False, "unknown_field": 42})
        assert cfg.flip_enabled is False

    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            with patch.object(AppConfig, "_config_path", return_value=path):
                cfg = AppConfig(rotate_degrees=15, output_quality=80)
                cfg.save()

                assert path.exists()
                data = json.loads(path.read_text())
                assert data["rotate_degrees"] == 15

                loaded = AppConfig.load()
                assert loaded.rotate_degrees == 15
                assert loaded.output_quality == 80

    def test_load_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nonexistent.json"
            with patch.object(AppConfig, "_config_path", return_value=path):
                cfg = AppConfig.load()
                assert cfg.flip_enabled is True  # default

    def test_transform_order_preserved(self):
        order = [
            "sharpness",
            "flip",
            "rotate",
            "crop",
            "resize",
            "brightness",
            "contrast",
            "watermark",
        ]
        cfg = AppConfig(transform_order=order)
        d = cfg.to_dict()
        cfg2 = AppConfig.from_dict(d)
        assert cfg2.transform_order == order

    def test_transform_order_auto_adds_new(self):
        old_order = ["flip", "rotate", "crop", "resize", "brightness", "contrast", "sharpness"]
        cfg = AppConfig.from_dict({"transform_order": old_order})
        assert "watermark" in cfg.transform_order
        for name in old_order:
            assert name in cfg.transform_order
