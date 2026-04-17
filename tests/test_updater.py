import json
from unittest.mock import patch, MagicMock

from app.updater import compare_versions, check_for_updates, _find_zip_asset


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


class TestFindZipAsset:
    def test_prefers_arm64_zip(self):
        assets = [
            {"name": "app-1.0.0.zip", "browser_download_url": "https://dl/app.zip"},
            {
                "name": "app-1.0.0-arm64.zip",
                "browser_download_url": "https://dl/app-arm64.zip",
            },
        ]
        assert _find_zip_asset(assets) == "https://dl/app-arm64.zip"

    def test_falls_back_to_any_zip(self):
        assets = [
            {"name": "app-1.0.0.zip", "browser_download_url": "https://dl/app.zip"},
        ]
        assert _find_zip_asset(assets) == "https://dl/app.zip"

    def test_empty_assets(self):
        assert _find_zip_asset([]) == ""


class TestCheckForUpdates:
    @patch("app.updater.urllib.request.urlopen")
    def test_update_available_with_release_notes(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(
            {
                "tag_name": "v2.0.0",
                "html_url": "https://github.com/r",
                "body": "## What's New\n- Feature A\n- Fix B",
                "assets": [
                    {
                        "name": "Image-Transform-Lite-2.0.0-arm64.zip",
                        "browser_download_url": "https://dl/app.zip",
                    },
                    {
                        "name": "Image-Transform-Lite-2.0.0-arm64.pkg",
                        "browser_download_url": "https://dl/app.pkg",
                    },
                ],
            }
        ).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = check_for_updates("1.0.0")
        assert result["update_available"] is True
        assert result["latest_version"] == "2.0.0"
        assert result["download_url"] == "https://dl/app.zip"
        assert "What's New" in result["release_notes"]

    @patch("app.updater.urllib.request.urlopen")
    def test_skip_version(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(
            {
                "tag_name": "v2.0.0",
                "html_url": "https://github.com/r",
                "body": "",
                "assets": [
                    {
                        "name": "app-arm64.zip",
                        "browser_download_url": "https://dl/app.zip",
                    }
                ],
            }
        ).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = check_for_updates("1.0.0", skip_version="2.0.0")
        assert result["update_available"] is False
        assert result["skipped"] is True

    @patch("app.updater.urllib.request.urlopen")
    def test_no_update(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(
            {
                "tag_name": "v1.0.0",
                "html_url": "",
                "body": "",
                "assets": [],
            }
        ).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = check_for_updates("1.0.0")
        assert result["update_available"] is False

    @patch("app.updater.urllib.request.urlopen", side_effect=Exception("network error"))
    def test_network_failure(self, mock_urlopen):
        result = check_for_updates("1.0.0")
        assert result["update_available"] is False
