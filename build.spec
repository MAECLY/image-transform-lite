# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for Image Transform Lite (macOS / Windows / Linux).
#
#   macOS   -> dist/Image Transform Lite.app        (arch = host, or TARGET_ARCH)
#   Windows -> dist/Image Transform Lite/Image Transform Lite.exe   (onedir)
#   Linux   -> dist/image-transform-lite/image-transform-lite       (onedir)
#
# Build with: pyinstaller build.spec --clean --noconfirm

import os
import platform
import re
import sys

import certifi

ROOT = os.path.dirname(os.path.abspath(SPEC))

# Read version from app/version.py without importing the package
with open(os.path.join(ROOT, 'app', 'version.py')) as f:
    _version_match = re.search(r"^__version__\s*=\s*['\"]([^'\"]+)['\"]", f.read(), re.M)
_app_version = _version_match.group(1) if _version_match else '0.0.0'

_certifi_cacert = os.path.join(os.path.dirname(certifi.__file__), 'cacert.pem')

IS_MAC = sys.platform == 'darwin'
IS_WIN = sys.platform.startswith('win')
IS_LINUX = sys.platform.startswith('linux')

datas = [
    ('ui/', 'ui/'),
    (_certifi_cacert, 'certifi/'),
]

hiddenimports = [
    'webview',
    'PIL',
    'PIL.Image',
    'PIL.ImageOps',
    'PIL.ImageEnhance',
    'certifi',
]

excludes = []

if IS_MAC:
    icon = os.path.join(ROOT, 'assets', 'icon.icns')
    hiddenimports += ['webview.platforms.cocoa', 'objc']
    excludes += ['PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'qtpy', 'gi', 'clr', 'pythonnet']
    # Build for the host architecture unless TARGET_ARCH overrides it
    # (arm64 on Apple Silicon runners, x86_64 on Intel runners).
    _machine = platform.machine().lower()
    target_arch = os.environ.get('TARGET_ARCH') or ('arm64' if _machine in ('arm64', 'aarch64') else 'x86_64')
    exe_name = 'ImageTransformLite'
    coll_name = 'ImageTransformLite'
elif IS_WIN:
    icon = os.path.join(ROOT, 'assets', 'icon.ico')
    hiddenimports += [
        'webview.platforms.edgechromium',
        'webview.platforms.winforms',
        'clr',
        'clr_loader',
        'pythonnet',
    ]
    excludes += ['PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'qtpy', 'gi', 'objc', 'AppKit', 'Foundation', 'WebKit']
    target_arch = None
    exe_name = 'Image Transform Lite'
    coll_name = 'Image Transform Lite'
elif IS_LINUX:
    icon = None
    datas.append((os.path.join(ROOT, 'assets', 'icon.png'), 'assets/'))
    hiddenimports += [
        'webview.platforms.qt',
        'qtpy',
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtNetwork',
        'PyQt6.QtWebChannel',
        'PyQt6.QtWebEngineCore',
        'PyQt6.QtWebEngineWidgets',
        'PyQt6.sip',
    ]
    # Only the PyQt6 binding is shipped; keep qtpy from dragging in others.
    excludes += ['PyQt5', 'PySide2', 'PySide6', 'gi', 'objc', 'AppKit', 'Foundation', 'WebKit', 'clr', 'pythonnet']
    target_arch = None
    exe_name = 'image-transform-lite'
    coll_name = 'image-transform-lite'
else:
    raise SystemExit(f'build.spec: plataforma no soportada: {sys.platform}')

block_cipher = None

a = Analysis(
    ['app/main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=exe_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    target_arch=target_arch,
    icon=icon,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=coll_name,
)

if IS_MAC:
    app = BUNDLE(
        coll,
        name='Image Transform Lite.app',
        icon=icon,
        bundle_identifier='com.maecly.imagetransformlite',
        info_plist={
            'CFBundleShortVersionString': _app_version,
            'CFBundleVersion': _app_version,
            'CFBundleName': 'Image Transform Lite',
            'CFBundleDisplayName': 'Image Transform Lite',
            'NSHighResolutionCapable': True,
            'NSRequiresAquaSystemAppearance': False,
        },
    )
