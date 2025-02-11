[app]
# (str) Title of your application
title = auto-mcs

# (str) Package name
package.name = automcs

# (str) Package domain (unique identifier)
package.domain = org.macarooniman

# (str) Source code directory (all your source files)
source.dir = ../source

# (str) The main .py file to use as the entry point for your application.
source.entrypoint = ../source/main.py

# (list) File extensions to include in the package
source.include_exts = py,kv,png,jpg,ico,ttf,otf,gif,webp,json,wav

# (str) Application version
version = 2.3

# (list) Application requirements (include all your dependencies)
requirements = python3==3.9.18,hostpython3==3.9.18,kivy,h11,click,wrapt,deprecated,limits,exceptiongroup,typing_extensions,starlette,anyio,sniffio,altgraph==0.17.3,asyncio-dgram==2.1.2,beautifulsoup4==4.11.1,bs4==0.0.1,certifi>=2024.07.04,charset-normalizer==2.1.1,cloudscraper>=1.2.71,dnspython==2.6.1,docutils==0.19,idna==3.7,ipaddress==1.0.23,Kivy==2.1.0,Kivy-Garden==0.1.5,munch==3.0.0,NBT==1.5.1,Pillow==8.4.0,plyer>=2.1.0,Pygments==2.16.1,pyparsing==3.0.9,requests==2.32.0,requests-toolbelt==0.10.1,six==1.16.0,soupsieve==2.3.2.post1,urllib3==1.26.19,PyYAML>=6.0.1,json_repair==0.10.1,fastapi>=0.111.1,fastapi-cli>=0.0.4,uvicorn>=0.30.1,pydantic==1.10.7,urwid==2.6.15,PyJWT>=2.9.0,bcrypt==3.2.2,python-multipart>=0.0.9,cryptography,py-machineid>=0.6.0,slowapi>=0.1.9,packaging>=24.1,pypresence>=4.3.0,python-dateutil>=1.16.0

# (str) Local path to python-for-android build recipes
# p4a.local_recipes = ./buildozer_recipes

# (str) Supported orientation (portrait, landscape, or all)
orientation = landscape

# (bool) Whether the application should be fullscreen
fullscreen = 1

# (list) Permissions required for your app on Android
android.permissions = INTERNET,ACCESS_NETWORK_STATE

# icon ;)
icon.filename = ../source/gui-assets/big-icon.png

# (str) Presplash of the application
presplash.filename = ../source/gui-assets/android-splash.png
android.presplash_color = #1D1D2E
