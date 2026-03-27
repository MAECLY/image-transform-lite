# -*- mode: python ; coding: utf-8 -*-

import os

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
    bundle_identifier='com.fiftyflowers.imagetransformlite',
    info_plist={
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleName': 'Image Transform Lite',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
    },
)
