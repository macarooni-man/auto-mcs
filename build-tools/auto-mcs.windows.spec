# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules, collect_data_files
from os.path import basename, exists
from kivy_deps import sdl2, glew
from time import sleep
import sys, os


build_tools = os.path.abspath(os.path.join('..', 'build-tools'))
sys.path.extend(['..', build_tools])
from source.core.constants import app_title, app_version
from compile_helper import *

block_cipher = None
hidden_imports = ['plyer.platforms.win.filechooser', 'PIL._tkinter_finder', 'dataclasses', 'nbt.world']
hidden_imports.extend(collect_submodules('uvicorn'))
hidden_imports.extend(collect_internal_modules())


# Included data files
included_files = [
    ('.\\core\\server\\baselib.ams', '.\\core\\server'),
    ('.\\ui\\assets\\icon.ico', '.\\ui\\assets'),
    ('..\\locales\\*.json', 'locales'),
    ('.\\ui\\assets\\icons\\sm\\*', '.\\ui\\assets\\icons\\sm'),
    ('.\\build-data.json', '.') if exists('build-data.json') else None,

    # Bundled utilities
    ('..\\build-tools\\utils\\mpg\\windows', '.\\utils\\mpg\\windows'),

    # Library data files
    *collect_data_files("mojangson")
]

a = Analysis(['launcher.py'],

    hiddenimports = hidden_imports,
    excludes = excluded_imports,
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
    excludes = []
)


# Dynamically generate version file
version_file  = "version.rc"
version_tuple = [int(num) for num in app_version.split(".")]
while len(version_tuple) < 4:
    version_tuple.append(0)
version_tuple = tuple(version_tuple)

with open(version_file, 'w+') as f:
    f.write(f"""# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
filevers={version_tuple},
prodvers={version_tuple},
mask=0x3f,
flags=0x0,
OS=0x4,
fileType=0x1,
subtype=0x0,
date=(0, 0)
),
  kids=[
StringFileInfo(
  [
  StringTable(
    u'040904B0',
    [StringStruct(u'CompanyName', u'Kaleb Efflandt'),
    StringStruct(u'FileDescription', u'{app_title}'),
    StringStruct(u'FileVersion', u'{app_version}'),
    StringStruct(u'InternalName', u'{app_title}'),
    StringStruct(u'LegalCopyright', u'Copyright (c) Kaleb Efflandt'),
    StringStruct(u'OriginalFilename', u'{app_title}.exe'),
    StringStruct(u'ProductName', u'{app_title}'),
    StringStruct(u'ProductVersion', u'{app_version}')])
  ]), 
VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)""")



splash = Splash(

    '.\\ui\\assets\\splash.png',

    binaries = a.binaries,
    datas = a.datas,
    text_pos = None,
    text_size = 12,
    minify_script = True,
    always_on_top = False,
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    splash,
    splash.binaries,
    *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],

    name = f'{app_title}.exe',
    icon = '.\\ui\\assets\\icon.ico',
    debug = False,

    bootloader_ignore_signals = False,
    strip = False,
    upx = False,
    runtime_tmpdir = None,
    console = False,
    disable_windowed_traceback = False,
    target_arch = None,
    codesign_identity = None,
    entitlements_file = None,
    version = version_file
)
