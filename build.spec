# -*- mode: python ; coding: utf-8 -*-

import os
import re

# Read version from app/version.py without importing the package
_version_file = os.path.join(os.path.dirname(os.path.abspath('build.spec')), 'app', 'version.py')
with open(_version_file) as f:
    _version_match = re.search(r"^__version__\s*=\s*['\"]([^'\"]+)['\"]", f.read(), re.M)
_app_version = _version_match.group(1) if _version_match else '0.0.0'

block_cipher = None

a = Analysis(
    ['app/main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('ui/', 'ui/'),
    ],
    hiddenimports=[
        'webview',
        'webview.platforms.cocoa',
        'PIL',
        'PIL.Image',
        'PIL.ImageOps',
        'PIL.ImageEnhance',
        'objc',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='ImageTransformLite',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    target_arch='arm64',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='ImageTransformLite',
)

app = BUNDLE(
    coll,
    name='Image Transform Lite.app',
    icon='assets/icon.icns',
    bundle_identifier='com.fiftyflowers.imagetransformlite',
    info_plist={
        'CFBundleShortVersionString': _app_version,
        'CFBundleName': 'Image Transform Lite',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
    },
)
