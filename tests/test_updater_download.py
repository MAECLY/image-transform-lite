import os
import zipfile
import tempfile
from unittest.mock import patch, MagicMock

from app.updater import download_update, extract_update, reveal_in_finder


class TestExtractUpdate:
    def test_extracts_app_from_zip(self, tmp_path):
        app_dir = tmp_path / "Image Transform Lite.app"
        app_dir.mkdir()
        (app_dir / "Contents").mkdir()
        (app_dir / "Contents" / "Info.plist").write_text("test")

        zip_path = str(tmp_path / "update.zip")
        with zipfile.ZipFile(zip_path, "w") as zf:
            for root, dirs, files in os.walk(str(app_dir)):
                for f in files:
                    full = os.path.join(root, f)
                    arcname = os.path.relpath(full, str(tmp_path))
                    zf.write(full, arcname)

        result = extract_update(zip_path)
        assert "Image Transform Lite.app" in result

    def test_returns_extract_dir_if_no_app(self, tmp_path):
        zip_path = str(tmp_path / "update.zip")
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("readme.txt", "hello")

        result = extract_update(zip_path)
        assert os.path.isdir(result)


class TestRevealInFinder:
    @patch("app.updater.subprocess.Popen")
    def test_calls_open_r(self, mock_popen):
        reveal_in_finder("/some/path.app")
        mock_popen.assert_called_once_with(["open", "-R", "/some/path.app"])


class TestDownloadUpdate:
    @patch("app.updater.urllib.request.urlopen")
    def test_downloads_file(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.headers = {"Content-Length": "12"}
        mock_resp.read.side_effect = [b"test content", b""]
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        progress_calls = []

        def on_progress(downloaded, total):
            progress_calls.append((downloaded, total))

        result = download_update("https://example.com/app.zip", on_progress=on_progress)
        assert os.path.exists(result)
        with open(result, "rb") as f:
            assert f.read() == b"test content"

    @patch("app.updater.urllib.request.urlopen")
    def test_raises_on_empty_url(self, mock_urlopen):
        try:
            download_update("")
            assert False, "Should have raised"
        except ValueError:
            pass
