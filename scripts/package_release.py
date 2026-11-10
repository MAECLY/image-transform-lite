"""Package the PyInstaller output in dist/ into the release assets for this host.

Run after `pyinstaller build.spec --clean --noconfirm`, from the repo root:

    python scripts/package_release.py            # version from app/version.py
    python scripts/package_release.py --check    # only verify the build output

Produces in dist/ (VERSION e.g. 1.7.0, arch in {arm64, x64}):
  macOS   Image-Transform-Lite-<VERSION>-macos-<arch>.zip  (ditto, keeps symlinks)
          Image-Transform-Lite-<VERSION>-macos-<arch>.pkg  (pkgbuild -> /Applications)
          + on arm64: Image-Transform-Lite-<VERSION>-arm64.zip (legacy byte copy
            for pre-1.7 auto-updaters)
  Windows Image-Transform-Lite-<VERSION>-windows-<arch>.zip
          (folder "Image Transform Lite/" with "Image Transform Lite.exe")
  Linux   Image-Transform-Lite-<VERSION>-linux-<arch>.tar.gz
          (folder "image-transform-lite/" with executable, .desktop, icon,
           install.sh and uninstall.sh)
"""

import argparse
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
PREFIX = "Image-Transform-Lite"
BUNDLE_ID = "com.maecly.imagetransformlite"

MAC_APP = DIST / "Image Transform Lite.app"
WIN_DIR = DIST / "Image Transform Lite"
WIN_EXE = WIN_DIR / "Image Transform Lite.exe"
LINUX_ID = "image-transform-lite"
LINUX_DIR = DIST / LINUX_ID
LINUX_EXE = LINUX_DIR / LINUX_ID


def read_version() -> str:
    text = (ROOT / "app" / "version.py").read_text()
    m = re.search(r"^__version__\s*=\s*['\"]([^'\"]+)['\"]", text, re.M)
    if not m:
        sys.exit("No se pudo leer __version__ de app/version.py")
    return m.group(1)


def host_os() -> str:
    if sys.platform == "darwin":
        return "macos"
    if sys.platform.startswith("win"):
        return "windows"
    if sys.platform.startswith("linux"):
        return "linux"
    sys.exit(f"Plataforma no soportada: {sys.platform}")


def host_arch() -> str:
    machine = platform.machine().lower()
    if machine in ("arm64", "aarch64"):
        return "arm64"
    if machine in ("x86_64", "amd64", "x64"):
        return "x64"
    sys.exit(f"Arquitectura no soportada: {platform.machine()}")


def run(cmd: list) -> None:
    print("+", " ".join(str(c) for c in cmd), flush=True)
    subprocess.run([str(c) for c in cmd], check=True)


def check_build(os_name: str, arch: str) -> None:
    """Cheap, non-flaky smoke checks on the PyInstaller output."""
    if os_name == "macos":
        exe = MAC_APP / "Contents" / "MacOS" / "ImageTransformLite"
        must = [exe, MAC_APP / "Contents" / "Info.plist"]
    elif os_name == "windows":
        exe = WIN_EXE
        must = [exe]
    else:
        exe = LINUX_EXE
        must = [exe]
    for p in must:
        if not p.is_file():
            sys.exit(f"SMOKE FAIL: falta {p}")
    if os_name != "windows" and not os.access(exe, os.X_OK):
        sys.exit(f"SMOKE FAIL: {exe} no es ejecutable")
    # The UI must be bundled next to the executable.
    found_ui = list(DIST.rglob("ui/index.html"))
    if not found_ui:
        sys.exit("SMOKE FAIL: ui/index.html no esta en el bundle")
    if os_name == "macos":
        out = subprocess.run(["lipo", "-archs", str(exe)], capture_output=True, text=True).stdout
        want = "arm64" if arch == "arm64" else "x86_64"
        print(f"lipo -archs: {out.strip()}")
        if want not in out.split():
            sys.exit(f"SMOKE FAIL: el ejecutable no es {want}")
    elif os_name == "linux":
        if not list(LINUX_DIR.rglob("QtWebEngineProcess")):
            sys.exit("SMOKE FAIL: QtWebEngineProcess no esta en el bundle")
    print(f"Smoke OK: {exe} ({exe.stat().st_size} bytes)")


def package_macos(version: str, arch: str) -> list:
    base = f"{PREFIX}-{version}-macos-{arch}"
    zip_path = DIST / f"{base}.zip"
    pkg_path = DIST / f"{base}.pkg"
    for p in (zip_path, pkg_path):
        p.unlink(missing_ok=True)

    run(["ditto", "-c", "-k", "--sequesterRsrc", "--keepParent", MAC_APP, zip_path])

    pkg_root = ROOT / "pkg-root"
    shutil.rmtree(pkg_root, ignore_errors=True)
    (pkg_root / "Applications").mkdir(parents=True)
    run(["ditto", MAC_APP, pkg_root / "Applications" / MAC_APP.name])
    run([
        "pkgbuild",
        "--root", pkg_root,
        "--identifier", BUNDLE_ID,
        "--version", version,
        "--install-location", "/",
        pkg_path,
    ])
    shutil.rmtree(pkg_root, ignore_errors=True)

    produced = [zip_path, pkg_path]
    if arch == "arm64":
        legacy = DIST / f"{PREFIX}-{version}-arm64.zip"
        shutil.copyfile(zip_path, legacy)
        produced.append(legacy)
    return produced


def package_windows(version: str, arch: str) -> list:
    base = DIST / f"{PREFIX}-{version}-windows-{arch}"
    Path(f"{base}.zip").unlink(missing_ok=True)
    out = shutil.make_archive(str(base), "zip", root_dir=DIST, base_dir=WIN_DIR.name)
    return [Path(out)]


def package_linux(version: str, arch: str) -> list:
    pkg = ROOT / "packaging" / "linux"
    shutil.copyfile(pkg / f"{LINUX_ID}.desktop", LINUX_DIR / f"{LINUX_ID}.desktop")
    shutil.copyfile(ROOT / "assets" / "icon.png", LINUX_DIR / f"{LINUX_ID}.png")
    for script in ("install.sh", "uninstall.sh"):
        dst = LINUX_DIR / script
        shutil.copyfile(pkg / script, dst)
        dst.chmod(0o755)
    LINUX_EXE.chmod(LINUX_EXE.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    tar_path = DIST / f"{PREFIX}-{version}-linux-{arch}.tar.gz"
    tar_path.unlink(missing_ok=True)
    with tarfile.open(tar_path, "w:gz") as tf:
        tf.add(LINUX_DIR, arcname=LINUX_ID)
    return [tar_path]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--version", default=None, help="Version (default: app/version.py)")
    parser.add_argument("--check", action="store_true", help="Only run the smoke checks")
    parser.add_argument("--arch", choices=("arm64", "x64"), default=None,
                        help="Asset arch label (default: host arch). Used for windows-arm64, built with x64 Python under emulation")
    args = parser.parse_args()

    version = args.version or read_version()
    os_name, arch = host_os(), args.arch or host_arch()
    print(f"Plataforma: {os_name}-{arch}  Version: {version}")

    check_build(os_name, arch)
    if args.check:
        return

    produced = {"macos": package_macos, "windows": package_windows, "linux": package_linux}[os_name](version, arch)
    for p in produced:
        print(f"Asset: {p.relative_to(ROOT)} ({p.stat().st_size / 1_048_576:.1f} MB)")


if __name__ == "__main__":
    main()
