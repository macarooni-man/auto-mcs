# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules
from os.path import basename
from time import sleep
from re import findall
from os import environ
from glob import glob
import sys, os


build_tools = os.path.abspath(os.path.join('..', 'build-tools'))
sys.path.extend(['..', build_tools])
from source.core.constants import app_title, app_version
from compile_helper import *

block_cipher = None
hiddenimports = ['dataclasses', 'nbt.world', 'pkg_resources.extern']
hiddenimports.extend(collect_submodules('uvicorn'))
hiddenimports.extend(collect_internal_modules())

sys.modules['FixTk'] = None
excluded_imports = [

    # Local modules
    'source.ui.desktop',
    'source.ui.amseditor',
    'source.ui.logviewer',

    # External modules
    'simpleaudio',
    'pandas',
    'matplotlib',
    'Kivy',
    'FixTk',
    'tcl',
    'tk',
    '_tkinter',
    'tkinter',
    'Tkinter',
    'pygments'
]


a = Analysis(['launcher.py'],

    hiddenimports = hiddenimports,
    excludes = excluded_imports,
    datas = [
        ('./core/server/baselib.ams', './core/server'),
        ('../build-tools/ca-bundle.crt', '.'),
    ],

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

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)


# Remove binaries
final_list = []
excluded_binaries = [
	'libstdc++.so.6',
	'libgcc_s.so.1',
    'libfreetype.so.6',
    'libfontconfig.so.1',
    'libreadline',
    'libncursesw',
    'libasound',
    'libharfbuzz',
    'libfreetype',
    'libSDL2',
    'libX11',
    'libgstreamer',
    'libgraphite2',
    'libglapi'
]

for binary in a.binaries:
    remove = False
    for exclude in excluded_binaries:
        if exclude in binary[0]:
            remove = True
            break

    if not remove:
        final_list.append(binary)

a.binaries = TOC(final_list)


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
