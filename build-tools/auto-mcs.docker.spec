# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules
from time import sleep
from re import findall
from os.path import basename
from os import environ
from glob import glob
import sys

block_cipher = None
hiddenimports = ['dataclasses', 'nbt.world', 'pkg_resources.extern']
hiddenimports.extend(collect_submodules('uvicorn'))

sys.modules['FixTk'] = None


a = Analysis(['wrapper.py'],
             pathex=[],
             binaries=[],
             datas = [
                        ('./baselib.ams', '.'),
                        ('../build-tools/ca-bundle.crt', '.'),
                        ('/usr/lib64/libcrypt.so.2', '.'),
                    ],
             hiddenimports=hiddenimports,
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=['simpleaudio', 'pandas', 'matplotlib', 'Kivy', 'menu', 'FixTk', 'tcl', 'tk', '_tkinter', 'tkinter', 'Tkinter'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

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


exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          # splash,
          # splash.binaries,
          # [('v', None, 'OPTION')],
          name='auto-mcs',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None
)
