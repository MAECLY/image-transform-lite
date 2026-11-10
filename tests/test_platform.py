import io
import os
import sys
import tarfile
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from app import config as config_mod
from app import platform_utils
from app.api import Api
from app.config import AppConfig
from app.transforms import load_watermark_font, watermark_image
from app.updater import download_update, extract_update, select_asset

VER = "1.7.0"
PLATFORMS = [
    ("macos", "arm64"),
    ("macos", "x64"),
    ("windows", "x64"),
    ("windows", "arm64"),
    ("linux", "x64"),
    ("linux", "arm64"),
]


def _asset(name):
    return {"name": name, "browser_download_url": f"https://dl/{name}"}


def full_release_assets():
    # Legacy asset first (lowest id), as the release job uploads it.
    names = [f"Image-Transform-Lite-{VER}-arm64.zip"]
    for os_name, arch in PLATFORMS:
        base = f"Image-Transform-Lite-{VER}-{os_name}-{arch}"
        if os_name == "macos":
            names += [f"{base}.pkg", f"{base}.zip"]
        elif os_name == "windows":
            names.append(f"{base}.zip")
        else:
            names.append(f"{base}.tar.gz")
    return [_asset(n) for n in names]


# ---------------------------------------------------------------- platform


class TestPlatformTokens:
    @pytest.mark.parametrize(
        "system,expected",
        [("Darwin", "macos"), ("Windows", "windows"), ("Linux", "linux")],
    )
    def test_normalize_os(self, system, expected):
        assert platform_utils.normalize_os(system) == expected

    @pytest.mark.parametrize(
        "machine,expected",
        [
            ("x86_64", "x64"),
            ("AMD64", "x64"),
            ("arm64", "arm64"),
            ("aarch64", "arm64"),
            ("ARM64", "arm64"),
        ],
    )
    def test_normalize_arch(self, machine, expected):
        assert platform_utils.normalize_arch(machine) == expected

    @pytest.mark.parametrize(
        "plat,label",
        [
            (("macos", "arm64"), "macOS Apple Silicon"),
            (("macos", "x64"), "macOS Intel"),
            (("windows", "x64"), "Windows x64"),
            (("windows", "arm64"), "Windows ARM64"),
            (("linux", "x64"), "Linux x64"),
            (("linux", "arm64"), "Linux ARM64"),
        ],
    )
    def test_platform_info(self, plat, label):
        with patch.object(platform_utils, "current_platform", return_value=plat):
            info = platform_utils.platform_info()
        assert info["os"] == plat[0]
        assert info["arch"] == plat[1]
        assert info["label"] == label
        assert info["file_manager"]

    def test_api_get_platform_info(self):
        info = Api(AppConfig()).get_platform_info()
        assert set(info) == {"os", "arch", "label", "file_manager"}

    def test_file_manager_names(self):
        assert platform_utils.file_manager_name("macos") == "Finder"
        assert platform_utils.file_manager_name("windows") == "Explorador de archivos"
        assert platform_utils.file_manager_name("linux") == "gestor de archivos"


class TestOpenAndReveal:
    @patch("app.platform_utils.subprocess.Popen")
    def test_open_macos(self, popen):
        with patch.object(platform_utils, "normalize_os", return_value="macos"):
            platform_utils.open_path("/x/out")
        popen.assert_called_once_with(["open", "/x/out"])

    @patch("app.platform_utils.subprocess.Popen")
    def test_open_linux(self, popen):
        with patch.object(platform_utils, "normalize_os", return_value="linux"):
            platform_utils.open_path("/x/out")
        popen.assert_called_once_with(["xdg-open", "/x/out"])

    def test_open_windows(self):
        startfile = MagicMock()
        with patch.object(platform_utils, "normalize_os", return_value="windows"), \
                patch.object(platform_utils.os, "startfile", startfile, create=True):
            platform_utils.open_path("C:/x/out")
        startfile.assert_called_once_with("C:/x/out")

    @patch("app.platform_utils.subprocess.Popen")
    def test_reveal_windows(self, popen):
        with patch.object(platform_utils, "normalize_os", return_value="windows"):
            platform_utils.reveal_path("/x/app")
        args = popen.call_args[0][0]
        assert args[:2] == ["explorer", "/select,"]

    @patch("app.platform_utils.subprocess.Popen")
    def test_reveal_linux_opens_parent(self, popen):
        with patch.object(platform_utils, "normalize_os", return_value="linux"):
            platform_utils.reveal_path("/x/y/app")
        expected = os.path.dirname(os.path.abspath("/x/y/app"))
        popen.assert_called_once_with(["xdg-open", expected])

    def test_api_open_output_directory(self, tmp_path):
        cfg = AppConfig(output_dir=str(tmp_path / "out"))
        with patch("app.api.open_path") as op:
            Api(cfg).open_output_directory()
        op.assert_called_once_with(tmp_path / "out")
        assert (tmp_path / "out").is_dir()


# ---------------------------------------------------------------- config dir


class TestConfigDir:
    def test_macos(self, monkeypatch, tmp_path):
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        assert platform_utils.user_config_dir("macos") == (
            tmp_path / "Library" / "Application Support" / "ImageTransformLite"
        )

    def test_windows_appdata(self, monkeypatch, tmp_path):
        monkeypatch.setenv("APPDATA", str(tmp_path / "Roaming"))
        assert platform_utils.user_config_dir("windows") == (
            tmp_path / "Roaming" / "ImageTransformLite"
        )

    def test_windows_no_appdata(self, monkeypatch, tmp_path):
        monkeypatch.delenv("APPDATA", raising=False)
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        assert platform_utils.user_config_dir("windows") == (
            tmp_path / "AppData" / "Roaming" / "ImageTransformLite"
        )

    def test_linux_xdg(self, monkeypatch, tmp_path):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
        assert platform_utils.user_config_dir("linux") == (
            tmp_path / "xdg" / "ImageTransformLite"
        )

    def test_linux_default(self, monkeypatch, tmp_path):
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        assert platform_utils.user_config_dir("linux") == (
            tmp_path / ".config" / "ImageTransformLite"
        )

    @pytest.mark.parametrize("os_name", ["macos", "windows", "linux"])
    def test_frozen_config_and_presets_use_user_dir(self, monkeypatch, tmp_path, os_name):
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.setenv("APPDATA", str(tmp_path / "Roaming"))
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
        monkeypatch.setattr(platform_utils, "normalize_os", lambda s=None: os_name)
        expected = platform_utils.user_config_dir(os_name)
        assert AppConfig._config_path() == expected / "config.json"
        assert AppConfig.get_presets_dir() == expected / "presets"
        assert (expected / "presets").is_dir()

    def test_dev_mode_config_in_repo(self):
        repo = Path(config_mod.__file__).resolve().parent.parent
        assert AppConfig._config_path() == repo / "config.json"


class TestAppBaseDir:
    def test_macos_folder_containing_app(self, monkeypatch, tmp_path):
        exe = tmp_path / "Apps" / "Image Transform Lite.app" / "Contents" / "MacOS" / "itl"
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "executable", str(exe))
        monkeypatch.setattr(config_mod, "normalize_os", lambda: "macos")
        assert config_mod._app_base_dir() == (tmp_path / "Apps").resolve()

    @pytest.mark.parametrize("os_name", ["windows", "linux"])
    def test_onedir_folder_containing_app_folder(self, monkeypatch, tmp_path, os_name):
        app_dir = tmp_path / "Downloads" / "Image Transform Lite"
        app_dir.mkdir(parents=True)
        exe = app_dir / "Image Transform Lite.exe"
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "executable", str(exe))
        monkeypatch.setattr(config_mod, "normalize_os", lambda: os_name)
        assert config_mod._app_base_dir() == (tmp_path / "Downloads").resolve()

    def test_onedir_unwritable_falls_back_to_home(self, monkeypatch, tmp_path):
        exe = tmp_path / "nonexistent" / "app" / "image-transform-lite"
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "executable", str(exe))
        monkeypatch.setattr(config_mod, "normalize_os", lambda: "linux")
        monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")
        assert config_mod._app_base_dir() == tmp_path / "home"


# ---------------------------------------------------------------- assets


class TestSelectAsset:
    @pytest.mark.parametrize("os_name,arch", PLATFORMS)
    def test_each_platform_gets_its_asset(self, os_name, arch):
        asset = select_asset(full_release_assets(), os_name, arch)
        assert asset is not None
        name = asset["name"]
        assert f"-{os_name}-{arch}." in name
        if os_name == "linux":
            assert name.endswith(".tar.gz")
        else:
            assert name.endswith(".zip")

    def test_macos_prefers_zip_over_pkg(self):
        base = f"Image-Transform-Lite-{VER}-macos-x64"
        assets = [_asset(f"{base}.pkg"), _asset(f"{base}.zip")]
        assert select_asset(assets, "macos", "x64")["name"] == f"{base}.zip"

    def test_macos_pkg_only_not_selected(self):
        assets = [_asset(f"Image-Transform-Lite-{VER}-macos-x64.pkg")]
        assert select_asset(assets, "macos", "x64") is None

    def test_legacy_not_chosen_on_windows_arm64(self):
        assets = [_asset(f"Image-Transform-Lite-{VER}-arm64.zip")]
        assert select_asset(assets, "windows", "arm64") is None

    def test_legacy_not_chosen_on_linux_arm64_or_mac_x64(self):
        assets = [_asset(f"Image-Transform-Lite-{VER}-arm64.zip")]
        assert select_asset(assets, "linux", "arm64") is None
        assert select_asset(assets, "macos", "x64") is None

    def test_windows_arm64_with_legacy_present(self):
        asset = select_asset(full_release_assets(), "windows", "arm64")
        assert asset["name"] == f"Image-Transform-Lite-{VER}-windows-arm64.zip"

    def test_legacy_fallback_only_mac_arm64(self):
        assets = [
            _asset(f"Image-Transform-Lite-1.6.0-arm64.zip"),
            _asset(f"Image-Transform-Lite-1.6.0-arm64.pkg"),
        ]
        assert select_asset(assets, "macos", "arm64")["name"].endswith("-arm64.zip")

    def test_x64_does_not_match_other_arch(self):
        assets = [_asset(f"Image-Transform-Lite-{VER}-linux-arm64.tar.gz")]
        assert select_asset(assets, "linux", "x64") is None

    def test_empty(self):
        assert select_asset([], "linux", "x64") is None


# ---------------------------------------------------------------- extraction


def _make_tar(tmp_path, folder="image-transform-lite"):
    src = tmp_path / "src" / folder
    src.mkdir(parents=True)
    exe = src / "image-transform-lite"
    exe.write_text("#!/bin/sh\necho hi\n")
    exe.chmod(0o755)
    (src / "install.sh").write_text("#!/bin/sh\n")
    dl = tmp_path / "dl"
    dl.mkdir()
    tar_path = dl / "update.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tf:
        tf.add(src, arcname=folder)
    return tar_path


class TestExtractArchives:
    def test_tar_gz_linux_returns_app_folder(self, tmp_path):
        tar_path = _make_tar(tmp_path)
        result = extract_update(str(tar_path), os_name="linux")
        assert Path(result).name == "image-transform-lite"
        exe = Path(result) / "image-transform-lite"
        assert exe.is_file()
        if os.name != "nt":
            assert os.access(exe, os.X_OK)

    def test_zip_windows_returns_app_folder(self, tmp_path):
        zip_path = tmp_path / "update.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("Image Transform Lite/Image Transform Lite.exe", b"MZ")
            zf.writestr("Image Transform Lite/_internal/base.dll", b"x")
        result = extract_update(str(zip_path), os_name="windows")
        assert Path(result).name == "Image Transform Lite"
        assert (Path(result) / "Image Transform Lite.exe").is_file()

    def test_zip_preserves_exec_bit(self, tmp_path):
        zip_path = tmp_path / "update.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            info = zipfile.ZipInfo("Image Transform Lite.app/Contents/MacOS/itl")
            info.external_attr = (0o100755) << 16
            zf.writestr(info, b"bin")
        result = extract_update(str(zip_path), os_name="macos")
        exe = Path(result) / "Contents" / "MacOS" / "itl"
        assert exe.is_file()
        if os.name != "nt":
            assert os.access(exe, os.X_OK)

    def test_zip_path_traversal_rejected(self, tmp_path):
        zip_path = tmp_path / "dl" / "update.zip"
        zip_path.parent.mkdir()
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("../../evil.txt", b"x")
        with pytest.raises(ValueError):
            extract_update(str(zip_path), os_name="linux")
        assert not (tmp_path / "evil.txt").exists()

    def test_tar_path_traversal_rejected(self, tmp_path):
        dl = tmp_path / "dl"
        dl.mkdir()
        tar_path = dl / "update.tar.gz"
        with tarfile.open(tar_path, "w:gz") as tf:
            data = b"x"
            info = tarfile.TarInfo("../../evil.txt")
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
        with pytest.raises(Exception):
            extract_update(str(tar_path), os_name="linux")
        assert not (tmp_path / "evil.txt").exists()

    @patch("app.updater.urllib.request.urlopen")
    def test_download_keeps_tar_gz_extension(self, mock_urlopen):
        resp = MagicMock()
        resp.headers = {"Content-Length": "3"}
        resp.read.side_effect = [b"abc", b""]
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = resp
        path = download_update(
            f"https://dl/Image-Transform-Lite-{VER}-linux-x64.tar.gz"
        )
        assert path.endswith(".tar.gz")


# ---------------------------------------------------------------- fonts


class TestWatermarkFont:
    @pytest.mark.parametrize("system", ["Darwin", "Windows", "Linux", "FreeBSD"])
    def test_font_loads_for_any_platform(self, system):
        assert load_watermark_font(24, system=system) is not None

    def test_fallback_when_no_truetype_available(self):
        with patch("app.transforms._font_candidates", return_value=["/nope/x.ttf"]):
            font = load_watermark_font(20)
        assert font is not None
        img = Image.new("RGB", (200, 100), (0, 0, 0))
        with patch("app.transforms._font_candidates", return_value=[]):
            out = watermark_image(img, text="Hola", font_size=20)
        assert out.size == (200, 100)

    def test_fallback_when_load_default_size_unsupported(self):
        from PIL import ImageFont

        real = ImageFont.load_default

        def fake(*args, **kwargs):
            if "size" in kwargs:
                raise TypeError("no size")
            return real()

        with patch("app.transforms._font_candidates", return_value=[]), \
                patch("app.transforms.ImageFont.load_default", side_effect=fake):
            assert load_watermark_font(20) is not None
