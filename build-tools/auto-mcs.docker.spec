# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules, collect_data_files
from os.path import basename, exists
from time import sleep
import sys, os


build_tools = os.path.abspath(os.path.join('..', 'build-tools'))
sys.path.extend(['..', build_tools])
from source.core.constants import app_title, app_version
from compile_helper import *

block_cipher = None
hiddenimports = ['dataclasses', 'nbt.world']
hiddenimports.extend(collect_submodules('uvicorn'))
hiddenimports.extend(collect_internal_modules())

sys.modules['FixTk'] = None
excluded_imports = list(set([

    # Local modules
    'source.ui.desktop',
    'source.ui.amseditor',
    'source.ui.logviewer',

    # External modules
    'pandas', 'matplotlib',
    'Kivy', 'FixTk', 'tcl',
    'tk', '_tkinter', 'tkinter',
    'Tkinter', 'pygments',
    'numpy', 'scipy',
    'pkg_resources',

    *excluded_imports
]))


# Included data files
included_files = [
    ('./core/server/baselib.ams', './core/server'),
    ('../build-tools/ca-bundle.crt', '.'),
    ('./build-data.json', '.') if exists('build-data.json') else None,

    # Library data files
    *collect_data_files("mojangson")
]

a = Analysis(['launcher.py'],

    hiddenimports = hiddenimports,
    excludes = excluded_imports,
    datas = [d for d in included_files if d],
    pathex = [],
    binaries = [],
    hookspath = [],
    hooksconfig = {},
    runtime_hooks = [],
    win_no_prefer_redirects = False,
    win_private_assemblies = False,
    cipher=block_cipher,
    noarchive=False
)


# Filter out and clean up compiled data/binaries
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
a.datas    = filter_datas(a.datas)
a.binaries = filter_binaries(a.binaries,
    excludes = [
        'libstdc++.so.6', 'libgcc_s.so.1', 'libfreetype.so.6', 'libfontconfig.so.1',
        'libreadline', 'libncursesw', 'libasound', 'libharfbuzz', 'libfreetype',
        'libSDL2', 'libX11', 'libgstreamer', 'libgraphite2', 'libglapi', 'libcrypto',
        'libssl', 'libglib', 'libobject', 'libgio', 'libgmodule', 'libgthread',
        'libgtk', 'libgtk', 'libgdk', 'libatk', 'libpango', 'liblzma.so',
        'liblzma.so.5', 'libz.so', 'libz.so.1', 'libzstd.so', 'libzstd.so.1'
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
    upx = False,
    upx_exclude = [],
    runtime_tmpdir = None,
    console = True,
    disable_windowed_traceback = False,
    target_arch = None,
    codesign_identity = None,
    entitlements_file = None
)
