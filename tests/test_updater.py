from unittest.mock import patch, MagicMock

from app.updater import compare_versions, check_for_updates


class TestCompareVersions:
    def test_newer_patch(self):
        assert compare_versions("1.0.0", "1.0.1") is True

    def test_newer_minor(self):
        assert compare_versions("1.0.0", "1.1.0") is True

    def test_newer_major(self):
        assert compare_versions("1.0.0", "2.0.0") is True

    def test_same_version(self):
        assert compare_versions("1.0.0", "1.0.0") is False

    def test_older_version(self):
        assert compare_versions("1.1.0", "1.0.0") is False

    def test_with_v_prefix(self):
        assert compare_versions("1.0.0", "v1.1.0") is True

    def test_invalid_input(self):
        assert compare_versions("1.0.0", "invalid") is False
        assert compare_versions("", "1.0.0") is False


class TestCheckForUpdates:
    @patch("app.updater.urllib.request.urlopen")
    def test_update_available(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"tag_name":"v2.0.0","html_url":"https://github.com/r","body":"notes","assets":[{"name":"Image-Transform-Lite-2.0.0-arm64.zip","browser_download_url":"https://dl/app.zip"}]}'
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = check_for_updates("1.0.0")
        assert result["update_available"] is True
        assert result["latest_version"] == "2.0.0"
        assert result["download_url"] == "https://dl/app.zip"

    @patch("app.updater.urllib.request.urlopen")
    def test_no_update(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"tag_name":"v1.0.0","html_url":"","body":"","assets":[]}'
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = check_for_updates("1.0.0")
        assert result["update_available"] is False

    @patch("app.updater.urllib.request.urlopen", side_effect=Exception("network error"))
    def test_network_failure(self, mock_urlopen):
        result = check_for_updates("1.0.0")
        assert result["update_available"] is False
