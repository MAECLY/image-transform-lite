import json
import logging
import os
import subprocess
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

GITHUB_API_URL = "https://api.github.com/repos/miguel50flowers/fe-image-transform-lite/releases/latest"
TIMEOUT_SECONDS = 5

log = logging.getLogger(__name__)


def compare_versions(current: str, latest: str) -> bool:
    def parse(v: str) -> tuple[int, ...]:
        return tuple(int(x) for x in v.lstrip("v").split("."))

    try:
        return parse(latest) > parse(current)
    except (ValueError, AttributeError):
        return False


def _find_zip_asset(assets: list) -> str:
    for asset in assets:
        name = asset.get("name", "")
        if name.endswith(".zip") and "arm64" in name:
            return asset["browser_download_url"]
    for asset in assets:
        if asset.get("name", "").endswith(".zip"):
            return asset["browser_download_url"]
    return ""


def check_for_updates(current_version: str, skip_version: str = "") -> dict:
    try:
        req = urllib.request.Request(
            GITHUB_API_URL,
            headers={
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "ImageTransformLite",
            },
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        tag = data.get("tag_name", "")
        latest = tag.lstrip("v")

        if not compare_versions(current_version, latest):
            return {"update_available": False}

        if skip_version and skip_version == latest:
            return {"update_available": False, "skipped": True}

        download_url = _find_zip_asset(data.get("assets", []))

        release_notes = data.get("body", "")
        if release_notes is None:
            release_notes = ""

        return {
            "update_available": True,
            "latest_version": latest,
            "current_version": current_version,
            "download_url": download_url,
            "release_url": data.get("html_url", ""),
            "release_notes": release_notes,
        }
    except urllib.error.HTTPError as e:
        log.error("Update check HTTP error: %s %s", e.code, e.reason)
        return {"update_available": False, "error": f"HTTP {e.code}: {e.reason}"}
    except urllib.error.URLError as e:
        log.error("Update check network error: %s", e.reason)
        return {
            "update_available": False,
            "error": "Error de red. Verifica tu conexion a internet.",
        }
    except Exception as e:
        log.error("Update check error: %s", e)
        return {"update_available": False, "error": str(e)}


def download_update(download_url: str, on_progress=None) -> str:
    if not download_url:
        raise ValueError("No download URL provided")

    tmp_dir = tempfile.mkdtemp(prefix="ImageTransformLite-update-")
    zip_path = os.path.join(tmp_dir, "update.zip")

    req = urllib.request.Request(
        download_url,
        headers={"User-Agent": "ImageTransformLite"},
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        total = resp.headers.get("Content-Length")
        total = int(total) if total else None
        downloaded = 0
        chunk_size = 8192

        with open(zip_path, "wb") as f:
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if on_progress and total:
                    on_progress(downloaded, total)

    return zip_path


def extract_update(zip_path: str) -> str:
    extract_dir = os.path.dirname(zip_path)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)

    app_paths = list(Path(extract_dir).glob("*.app"))
    if not app_paths:
        app_paths = list(Path(extract_dir).rglob("*.app"))

    if app_paths:
        return str(app_paths[0])

    return extract_dir


def reveal_in_finder(path: str) -> None:
    subprocess.Popen(["open", "-R", path])
