# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules, collect_data_files
from os.path import basename, exists
from time import sleep
import sys, os


build_tools = os.path.abspath(os.path.join('..', 'build-tools'))
sys.path.extend(['..', build_tools])
from source.core.constants import app_title, app_version, check_arm
from compile_helper import *
architecture = "arm64" if check_arm() else "x64"

block_cipher = None
hiddenimports = ['plyer.platforms.linux.filechooser', 'PIL._tkinter_finder', 'dataclasses', 'nbt.world']
hiddenimports.extend(collect_submodules('uvicorn'))
hiddenimports.extend(collect_internal_modules())


# Included data files
included_files = [
    ('./core/server/baselib.ams', './core/server'),
    ('./ui/assets/icon.ico', './ui/assets'),
    ('./ui/assets/locales.json', './ui/assets'),
    ('./ui/assets/icons/sm/*', './ui/assets/icons/sm'),
    ('../build-tools/ca-bundle.crt', '.'),
    ('/usr/lib64/libcrypt.so.2', '.'),
    ('./build-data.json', '.') if exists('build-data.json') else None,

    # Bundled utilities
    (f'../build-tools/utils/sox/linux/{architecture}', f'./utils/sox/linux/{architecture}'),

    # Library data files
    *collect_data_files("mojangson")
]

a = Analysis(['launcher.py'],

    hiddenimports = hiddenimports,
    excludes = ['pandas', 'matplotlib', 'numpy', 'scipy', 'pkg_resources'],
    datas = [d for d in included_files if d],
    pathex = [],
    binaries = [],
    hookspath = [],
    hooksconfig = {},
    runtime_hooks = [],
    win_no_prefer_redirects = False,
    win_private_assemblies = False,
    cipher = block_cipher,
    noarchive = False
)


# Filter out and clean up compiled data/binaries
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
a.datas    = filter_datas(a.datas)
a.binaries = filter_binaries(a.binaries,
    excludes = [
    	'libstdc++.so.6', 'libgcc_s.so.1', 'libfreetype.so.6', 'libfontconfig.so.1',
        'libreadline', 'libncursesw', 'libasound', 'libcrypto', 'libssl', 'libglib',
        'libobject', 'libgio', 'libgmodule', 'libgthread', 'libgtk', 'libgtk',
        'libgdk', 'libatk', 'libpango', 'libharfbuzz', 'liblzma.so', 'liblzma.so.5',
        'libz.so', 'libz.so.1', 'libzstd.so', 'libzstd.so.1',
    ]
)


exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,

    name = app_title,
    debug = False,
    
    bootloader_ignore_signals = False,
    strip = False,
    upx = True,
    upx_exclude = [],
    runtime_tmpdir = None,
    console = True,
    disable_windowed_traceback = False,
    target_arch = None,
    codesign_identity = None,
    entitlements_file = None
)
