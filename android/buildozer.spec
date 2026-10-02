[app]

title = auto-mcs
package.name = automcs
package.domain = com.macarooniman
version = 2.4

source.dir = build/app
source.include_exts = py,kv,ams,png,jpg,jpeg,ico,svg,ttf,otf,gif,webp,json,yaml,yml,wav,txt,ini,properties,conf,toml,hocon,crt,zip
source.exclude_dirs = __pycache__,tests,test

# The Android build deliberately has its own dependency set.
# psutil and py-machineid are supplied/replaced by the Android overlay.
# dbus-next and PyInstaller are desktop-only and are intentionally omitted.
requirements = python3==3.12.8,hostpython3==3.12.8,kivy==2.3.1,pyjnius,Kivy-Garden>=0.1.5,asyncio-dgram>=2.1.2,beautifulsoup4==4.11.1,bs4==0.0.1,colorama>=0.4.6,certifi>=2024.7.4,charset-normalizer==2.1.1,cloudscraper>=1.2.71,dnspython==2.6.1,idna==3.7,munch==3.0.0,NBT==1.5.1,mojangson>=0.2.1,Pillow==11.3.0,plyer>=2.1.0,Pygments>=2.16.1,pyparsing==3.0.9,requests==2.32.4,requests-toolbelt==0.10.1,six==1.16.0,soupsieve>=2.9.0,urllib3==1.26.20,PyYAML>=6.0.1,json_repair==0.10.1,fastapi>=0.111.1,uvicorn>=0.30.1,pydantic==2.11.3,pydantic-core==2.33.1,urwid==2.6.15,PyJWT>=2.9.0,python-multipart>=0.0.9,cryptography==46.0.3,slowapi>=0.1.9,packaging>=24.1,pypresence>=4.3.0,python-dateutil>=1.16.0,pyhocon==0.3.61,markdown-it-py>=4.0.0

orientation = landscape,landscape-reverse
fullscreen = 1

icon.filename = %(source.dir)s/source/ui/assets/big-icon.png
presplash.filename = source/gui-assets/android-splash.png
android.presplash_color = #1D1D2E

android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.api = 36
android.minapi = 24
android.ndk = 28c
android.archs = arm64-v8a
android.accept_sdk_license = True
android.enable_androidx = True
android.display_cutout = shortEdges

p4a.bootstrap = sdl2
p4a.source_dir = build/python-for-android


[buildozer]

log_level = 2
warn_on_root = 1
build_dir = build/.buildozer
bin_dir = build/bin
