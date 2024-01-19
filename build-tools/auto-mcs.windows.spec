# -*- mode: python ; coding: utf-8 -*-

from kivy_deps import sdl2, glew
from time import sleep
from re import findall
from os.path import basename
from glob import glob


block_cipher = None


a = Analysis(['wrapper.py'],
             pathex=[],
             binaries=[],
             datas = [
                        ('.\\icon.ico', '.'),
                        ('.\\baselib.ams', '.'),
                        ('.\\gui-assets\\icons\\sm\\*', '.\\gui-assets\\icons\\sm')
                    ],
             hiddenimports=['plyer.platforms.win.filechooser', 'PIL._tkinter_finder', 'dataclasses', 'nbt.world'],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=['pandas', 'matplotlib', 'packaging'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)


# Import assets, and only use icons that are needed
png_list = []

with open(".\\menu.py", 'r') as f:
    script_contents = f.read()
    [png_list.append(x) for x in findall(r"'(.*?)'", script_contents) if '.png' in x and '{' not in x]
    [png_list.append(x) for x in findall(r'"(.*?)"', script_contents) if '.png' in x and '{' not in x]

exclude_list = [basename(file) for file in glob(".\\gui-assets\\icons\\*") if (basename(file) not in png_list) and ("big" not in file)]

data_list = list(a.datas)
for item in data_list:
    if "tzdata" in item[0]:
        data_list.remove(item)
a.datas = data_list

# Convert modified list back to a tuple
a.datas += Tree('.\\gui-assets', prefix='gui-assets', excludes=exclude_list)


# Dynamically generate version file
from constants import app_version
version_file = "version.rc"
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
    StringStruct(u'FileDescription', u'auto-mcs'),
    StringStruct(u'FileVersion', u'{app_version}'),
    StringStruct(u'InternalName', u'auto-mcs'),
    StringStruct(u'LegalCopyright', u'Copyright (c) Kaleb Efflandt'),
    StringStruct(u'OriginalFilename', u'auto-mcs.exe'),
    StringStruct(u'ProductName', u'Auto-MCS'),
    StringStruct(u'ProductVersion', u'{app_version}')])
  ]), 
VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)""")



splash = Splash(
    '.\\gui-assets\\splash.png',
    binaries=a.binaries,
    datas=a.datas,
    text_pos=None,
    text_size=12,
    minify_script=True,
    always_on_top=True,
)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          splash,
          splash.binaries,
          *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
          name='auto-mcs.exe',
          debug=True,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=['tcl86t.dll', 'tk86t.dll'],
          runtime_tmpdir=None,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None,
          icon='icon.ico',
          version=version_file
)
