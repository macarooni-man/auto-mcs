# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules
from time import sleep
from re import findall
from os.path import basename
from os import environ
from glob import glob


block_cipher = None
hiddenimports = ['plyer.platforms.macosx.filechooser', 'PIL._tkinter_finder', 'dataclasses', 'nbt.world', 'pkg_resources.extern', 'menu.py']
hiddenimports.extend(collect_submodules('uvicorn'))


a = Analysis(['wrapper.py'],
             pathex=[],
             binaries=[],
             datas = [
                        ('./icon.ico', '.'),
                        ('./icon.icns', '.'),
                        ('./baselib.ams', '.'),
                        ('./locales.json', '.'),
                        ('./gui-assets/icons/sm/*', './gui-assets/icons/sm')
                    ],
             hiddenimports=hiddenimports,
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=['pandas', 'matplotlib'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)


# Import assets, and only use icons that are needed
png_list = []

with open("./menu.py", 'r') as f:
    script_contents = f.read()
    [png_list.append(x) for x in findall(r"'(.*?)'", script_contents) if '.png' in x and '{' not in x]
    [png_list.append(x) for x in findall(r'"(.*?)"', script_contents) if '.png' in x and '{' not in x]

exclude_list = [basename(file) for file in glob("./gui-assets/icons/*") if (basename(file) not in png_list) and ("big" not in file)]

data_list = list(a.datas)
for item in data_list:
    if "tzdata" in item[0]:
        data_list.remove(item)
a.datas = tuple(data_list)

# Convert modified list back to a tuple
a.datas += tuple(Tree('./gui-assets', prefix='gui-assets', excludes=exclude_list))
from constants import app_version

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
          [],
          exclude_binaries=True,
          name='auto-mcs',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
          disable_windowed_traceback=False,
          argv_emulation=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None,
          icon=['icon.icns']
)

coll = COLLECT(
          exe,
          a.binaries,
          a.zipfiles,
          a.datas,
          strip=False,
          upx=False,
          upx_exclude=[],
          name='auto-mcs',
)

app = BUNDLE(coll,
          name='auto-mcs.app',
          icon='icon.icns',
          bundle_identifier='com.auto-mcs',
          info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSAppleScriptEnabled': False,
            'NSHighResolutionCapable': False,
            'CFBundleShortVersionString': app_version,
            'CFBundleDocumentTypes': [
                    {
                        "CFBundleTypeExtensions": ["ams"],
                        "CFBundleTypeName": "Auto-MCS Script",
                        "CFBundleTypeRole": "Editor",
                        "CFBundleTypeOSTypes": ["TEXT"],
                    },
                    {
                        "CFBundleTypeExtensions": ["amb"],
                        "CFBundleTypeName": "Auto-MCS Back-up File",
                        "CFBundleTypeRole": "Editor",
                        "CFBundleTypeOSTypes": ["TEXT"],
                    },
                ]
            },
)
