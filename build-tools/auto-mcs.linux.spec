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
hiddenimports = ['plyer.platforms.linux.filechooser', 'PIL._tkinter_finder', 'dataclasses', 'nbt.world', 'pkg_resources.extern']
hiddenimports.extend(collect_submodules('uvicorn'))
hiddenimports.extend(collect_internal_modules())


a = Analysis(['launcher.py'],

    hiddenimports = hiddenimports,
    excludes = ['pandas', 'matplotlib'],
    datas = [
        ('./core/server/baselib.ams', './core/server'),
        ('./ui/assets/icon.ico', './ui/assets'),
        ('./ui/assets/locales.json', './ui/assets'),
        ('./ui/assets/icons/sm/*', './ui/assets/icons/sm'),
        ('../build-tools/ca-bundle.crt', '.'),
        ('/usr/lib64/libcrypt.so.2', '.')
    ],

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

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)


# Import assets, and only use icons that are needed
png_list = []

with open("./ui/desktop.py", 'r') as f:
    script_contents = f.read()
    [png_list.append(x) for x in findall(r"'(.*?)'", script_contents) if '.png' in x and '{' not in x]
    [png_list.append(x) for x in findall(r'"(.*?)"', script_contents) if '.png' in x and '{' not in x]

exclude_list = [basename(file) for file in glob("./ui/assets/icons/*") if (basename(file) not in png_list) and ("big" not in file)]

data_list = list(a.datas)
for item in data_list:
    if "tzdata" in item[0]: data_list.remove(item)
a.datas = tuple(data_list)

# Convert modified list back to a tuple
a.datas += tuple(Tree('./ui/assets', prefix='ui/assets', excludes=exclude_list))


# Remove binaries
final_list = []
excluded_binaries = [
	'libstdc++.so.6',
	'libgcc_s.so.1',
    'libfreetype.so.6',
    'libfontconfig.so.1',
    'libreadline',
    'libncursesw',
    'libasound'
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
    upx = True,
    upx_exclude = [],
    runtime_tmpdir = None,
    console = True,
    disable_windowed_traceback = False,
    target_arch = None,
    codesign_identity = None,
    entitlements_file = None
)
