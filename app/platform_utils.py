"""Cross-platform helpers (OS/arch detection, config dir, opening paths)."""

import os
import platform
import subprocess
import sys
from pathlib import Path

APP_DIR_NAME = "ImageTransformLite"

_OS_MAP = {"darwin": "macos", "windows": "windows", "linux": "linux"}
_ARCH_MAP = {
    "x86_64": "x64",
    "amd64": "x64",
    "x64": "x64",
    "arm64": "arm64",
    "aarch64": "arm64",
    "armv8": "arm64",
    "armv8l": "arm64",
}

_LABELS = {
    ("macos", "arm64"): "macOS Apple Silicon",
    ("macos", "x64"): "macOS Intel",
    ("windows", "x64"): "Windows x64",
    ("windows", "arm64"): "Windows ARM64",
    ("linux", "x64"): "Linux x64",
    ("linux", "arm64"): "Linux ARM64",
}

_FILE_MANAGERS = {
    "macos": "Finder",
    "windows": "Explorador de archivos",
    "linux": "gestor de archivos",
}


def normalize_os(system: str | None = None) -> str:
    system = (system if system is not None else platform.system()).lower()
    return _OS_MAP.get(system, system)


def normalize_arch(machine: str | None = None) -> str:
    machine = (machine if machine is not None else platform.machine()).lower()
    return _ARCH_MAP.get(machine, machine)


def current_platform() -> tuple[str, str]:
    """Return (os, arch) tokens, e.g. ("macos", "arm64"), ("windows", "x64")."""
    return normalize_os(), normalize_arch()


def platform_label(os_name: str | None = None, arch: str | None = None) -> str:
    cur_os, cur_arch = current_platform()
    os_name = os_name or cur_os
    arch = arch or cur_arch
    return _LABELS.get((os_name, arch), f"{os_name} {arch}")


def file_manager_name(os_name: str | None = None) -> str:
    os_name = os_name or normalize_os()
    return _FILE_MANAGERS.get(os_name, "gestor de archivos")


def platform_info() -> dict:
    os_name, arch = current_platform()
    return {
        "os": os_name,
        "arch": arch,
        "label": platform_label(os_name, arch),
        "file_manager": file_manager_name(os_name),
    }


def user_config_dir(os_name: str | None = None) -> Path:
    """Per-user config directory for the bundled app (not created here)."""
    os_name = os_name or normalize_os()
    home = Path.home()
    if os_name == "macos":
        return home / "Library" / "Application Support" / APP_DIR_NAME
    if os_name == "windows":
        appdata = os.environ.get("APPDATA")
        base = Path(appdata) if appdata else home / "AppData" / "Roaming"
        return base / APP_DIR_NAME
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg and os.path.isabs(xdg) else home / ".config"
    return base / APP_DIR_NAME


def open_path(path: str | os.PathLike) -> None:
    """Open a file or folder with the OS default handler."""
    path = str(path)
    os_name = normalize_os()
    if os_name == "macos":
        subprocess.Popen(["open", path])
    elif os_name == "windows":
        os.startfile(path)  # type: ignore[attr-defined]
    else:
        subprocess.Popen(["xdg-open", path])


def reveal_path(path: str | os.PathLike) -> None:
    """Show a file/folder selected in the OS file manager."""
    path = str(path)
    os_name = normalize_os()
    if os_name == "macos":
        subprocess.Popen(["open", "-R", path])
    elif os_name == "windows":
        subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])
    else:
        parent = os.path.dirname(os.path.abspath(path)) or path
        subprocess.Popen(["xdg-open", parent])


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))
