import json
import logging
import os
import re
import shutil
import ssl
import stat
import tarfile
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

from app.platform_utils import current_platform, reveal_path

GITHUB_API_URL = "https://api.github.com/repos/MAECLY/image-transform-lite/releases/latest"
TIMEOUT_SECONDS = 5

log = logging.getLogger(__name__)


def compare_versions(current: str, latest: str) -> bool:
    def parse(v: str) -> tuple[int, ...]:
        return tuple(int(x) for x in v.lstrip("v").split("."))

    try:
        return parse(latest) > parse(current)
    except (ValueError, AttributeError):
        return False


# Archive formats the in-app updater knows how to extract, per OS (in order
# of preference). macOS .pkg installers are intentionally not auto-selected.
_EXTRACTABLE = {
    "macos": (".zip",),
    "windows": (".zip",),
    "linux": (".tar.gz", ".zip"),
}

# Pre-1.7 macOS Apple Silicon asset, e.g. "Image-Transform-Lite-1.7.0-arm64.zip"
# (no OS token). Kept only so arm64 Macs can still update from it.
_LEGACY_MAC_ARM64 = re.compile(r"-arm64\.zip$", re.IGNORECASE)
_OS_TOKEN = re.compile(r"-(macos|windows|linux)-", re.IGNORECASE)


def select_asset(assets: list, os_name: str, arch: str) -> dict | None:
    """Pick the release asset for (os_name, arch) per the release naming contract.

    Names look like "Image-Transform-Lite-<ver>-<os>-<arch>.<ext>". The legacy
    "...-arm64.zip" asset is only ever chosen on macOS arm64.
    """
    exts = _EXTRACTABLE.get(os_name, (".zip", ".tar.gz"))
    token = f"-{os_name}-{arch}.".lower()

    for ext in exts:
        for asset in assets:
            name = asset.get("name", "").lower()
            if token in name and name.endswith(ext) and asset.get(
                "browser_download_url"
            ):
                return asset

    if os_name == "macos" and arch == "arm64":
        for asset in assets:
            name = asset.get("name", "")
            if (
                _LEGACY_MAC_ARM64.search(name)
                and not _OS_TOKEN.search(name)
                and asset.get("browser_download_url")
            ):
                return asset

    return None


def find_download_url(assets: list, os_name: str | None = None, arch: str | None = None) -> str:
    cur_os, cur_arch = current_platform()
    asset = select_asset(assets, os_name or cur_os, arch or cur_arch)
    return asset["browser_download_url"] if asset else ""


def _find_zip_asset(assets: list) -> str:
    """Backward-compatible alias: URL of the asset for the running platform."""
    return find_download_url(assets)


def _get_ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    try:
        import certifi

        cafile = certifi.where()
        if os.path.isfile(cafile):
            ctx.load_verify_locations(cafile)
            return ctx
    except Exception:
        pass
    default_ca = ssl.get_default_verify_paths().cafile
    if default_ca and os.path.isfile(default_ca):
        return ctx
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    log.warning("No CA certificates found; SSL verification disabled")
    return ctx


def check_for_updates(current_version: str, skip_version: str = "") -> dict:
    try:
        req = urllib.request.Request(
            GITHUB_API_URL,
            headers={
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "ImageTransformLite",
            },
        )
        with urllib.request.urlopen(
            req, timeout=TIMEOUT_SECONDS, context=_get_ssl_context()
        ) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        tag = data.get("tag_name", "")
        latest = tag.lstrip("v")

        if not compare_versions(current_version, latest):
            return {"update_available": False}

        if skip_version and skip_version == latest:
            return {"update_available": False, "skipped": True}

        os_name, arch = current_platform()
        asset = select_asset(data.get("assets", []), os_name, arch)
        download_url = asset["browser_download_url"] if asset else ""

        release_notes = data.get("body", "")
        if release_notes is None:
            release_notes = ""

        return {
            "update_available": True,
            "latest_version": latest,
            "current_version": current_version,
            "download_url": download_url,
            "asset_name": asset.get("name", "") if asset else "",
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


def _archive_suffix(name: str) -> str:
    lower = name.lower()
    for ext in (".tar.gz", ".tgz", ".zip"):
        if lower.endswith(ext):
            return ext
    return ".zip"


def download_update(download_url: str, on_progress=None) -> str:
    if not download_url:
        raise ValueError("No download URL provided")

    tmp_dir = tempfile.mkdtemp(prefix="ImageTransformLite-update-")
    url_name = urllib.parse.unquote(urllib.parse.urlparse(download_url).path)
    archive_path = os.path.join(tmp_dir, "update" + _archive_suffix(url_name))

    req = urllib.request.Request(
        download_url,
        headers={"User-Agent": "ImageTransformLite"},
    )

    with urllib.request.urlopen(req, timeout=30, context=_get_ssl_context()) as resp:
        total = resp.headers.get("Content-Length")
        total = int(total) if total else None
        downloaded = 0
        chunk_size = 8192

        with open(archive_path, "wb") as f:
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if on_progress and total:
                    on_progress(downloaded, total)

    return archive_path


def _is_within(base: str, target: str) -> bool:
    base = os.path.realpath(base)
    target = os.path.realpath(target)
    return os.path.commonpath([base, target]) == base


def _safe_extract_zip(zip_path: str, dest: str) -> None:
    """Extract a zip, rejecting path traversal and restoring unix modes/symlinks."""
    with zipfile.ZipFile(zip_path, "r") as zf:
        for info in zf.infolist():
            name = info.filename
            if not name or os.path.isabs(name) or name.startswith(("/", "\\")):
                raise ValueError(f"Unsafe path in archive: {name}")
            target = os.path.join(dest, *re.split(r"[\\/]", name))
            if not _is_within(dest, target):
                raise ValueError(f"Unsafe path in archive: {name}")

            mode = (info.external_attr >> 16) & 0xFFFF
            if info.is_dir():
                os.makedirs(target, exist_ok=True)
                continue

            os.makedirs(os.path.dirname(target), exist_ok=True)
            if stat.S_ISLNK(mode) and os.name != "nt":
                link = zf.read(info).decode("utf-8")
                link_target = os.path.join(os.path.dirname(target), link)
                if os.path.isabs(link) or not _is_within(dest, link_target):
                    raise ValueError(f"Unsafe symlink in archive: {name}")
                if os.path.lexists(target):
                    os.unlink(target)
                os.symlink(link, target)
                continue

            with zf.open(info) as src, open(target, "wb") as out:
                shutil.copyfileobj(src, out)
            perms = mode & 0o777
            if perms and os.name != "nt":
                os.chmod(target, perms)


def _safe_extract_tar(tar_path: str, dest: str) -> None:
    with tarfile.open(tar_path, "r:*") as tf:
        if hasattr(tarfile, "data_filter"):
            tf.extractall(dest, filter="data")
            return
        # Older Pythons without extraction filters: validate manually.
        for member in tf.getmembers():
            target = os.path.join(dest, member.name)
            if os.path.isabs(member.name) or not _is_within(dest, target):
                raise ValueError(f"Unsafe path in archive: {member.name}")
            if member.issym() or member.islnk():
                link_target = os.path.join(os.path.dirname(target), member.linkname)
                if os.path.isabs(member.linkname) or not _is_within(dest, link_target):
                    raise ValueError(f"Unsafe link in archive: {member.name}")
            if member.isdev():
                raise ValueError(f"Device file in archive: {member.name}")
        tf.extractall(dest)


def _locate_app(extract_dir: str, os_name: str) -> str:
    root = Path(extract_dir)
    if os_name == "macos":
        app_paths = list(root.glob("*.app")) or list(root.rglob("*.app"))
        return str(app_paths[0]) if app_paths else extract_dir

    # Windows/Linux: the archive contains a single app folder
    # ("Image Transform Lite/" or "image-transform-lite/").
    dirs = [p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")]
    if len(dirs) == 1:
        return str(dirs[0])
    for d in dirs:
        if (d / "Image Transform Lite.exe").exists() or (d / "image-transform-lite").exists():
            return str(d)
    return extract_dir


def extract_update(archive_path: str, os_name: str | None = None) -> str:
    """Extract a downloaded .zip/.tar.gz update.

    Returns the .app bundle on macOS, the extracted app folder on
    Windows/Linux, or the extraction directory if neither is found.
    """
    os_name = os_name or current_platform()[0]
    extract_dir = os.path.join(os.path.dirname(os.path.abspath(archive_path)), "extracted")
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)
    os.makedirs(extract_dir)

    lower = archive_path.lower()
    if lower.endswith((".tar.gz", ".tgz")) or (
        not lower.endswith(".zip") and tarfile.is_tarfile(archive_path)
    ):
        _safe_extract_tar(archive_path, extract_dir)
    else:
        _safe_extract_zip(archive_path, extract_dir)

    return _locate_app(extract_dir, os_name)


def reveal_in_file_manager(path: str) -> None:
    reveal_path(path)


# Backward-compatible alias (pre-1.7 name)
reveal_in_finder = reveal_in_file_manager
