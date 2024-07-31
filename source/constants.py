from shutil import rmtree, copytree, copy, ignore_patterns, move, disk_usage
from concurrent.futures import ThreadPoolExecutor
from random import randrange, choices
from difflib import SequenceMatcher
from urllib.parse import quote
from bs4 import BeautifulSoup
from platform import system
from threading import Timer
from copy import deepcopy
from pathlib import Path
from glob import glob
from PIL import Image
from nbt import nbt
import configparser
import cloudscraper
import unicodedata
import subprocess
import functools
import threading
import requests
import datetime
import tarfile
import zipfile
import hashlib
import urllib
import string
import psutil
import socket
import time
import json
import math
import yaml
import sys
import os
import re

import addons
import backup
import amscript

# ---------------------------------------------- Global Variables ------------------------------------------------------

app_version = "2.2"
ams_version = "1.2.1"
app_title = "auto-mcs"
dev_version = False
window_size = (850, 850)
refresh_rate = 60
anim_speed = 1
fullscreen = False
last_window = {}
geometry = {}
project_link = "https://github.com/macarooni-man/auto-mcs"
website = "https://auto-mcs.com"
update_data = {
    "version": '',
    "urls": {'windows': None, 'linux': None, 'linux-arm64': None, 'macos': None},
    "md5": {'windows': None, 'linux': None, 'linux-arm64': None, 'macos': None},
    "desc": '',
    "reboot-msg": [],
    "auto-show": True
}
auto_update = True
app_online = False
app_latest = True
app_loaded = False
version_loading = False
screen_tree = []
back_clicked = False
session_splash = ''
boot_launches = []


# Global debug mode and app_compiled, set debug to false before release
debug = False
app_compiled = getattr(sys, 'frozen', False)

public_ip = ""
ngrok_ip = {'name': None, 'ip': None}
footer_path = ""
last_widget = None

update_list = {}
addon_cache = {}

latestMC = {
    "vanilla": "0.0.0",
    "forge": "0.0.0",
    "paper": "0.0.0",
    "purpur": "0.0.0",
    "spigot": "0.0.0",
    "craftbukkit": "0.0.0",
    "fabric": "0.0.0",

    "builds": {
        "forge": "0",
        "paper": "0",
        "purpur": "0"
    }
}

# Prevent running or importing servers while these are blank
java_executable = {
    "modern": None,
    "legacy": None,
    "jar": None
}

# Change this back when not testing
startup_screen = 'MainMenuScreen'

fonts = {
    'regular': 'Figtree-Regular',
    'medium': 'Figtree-Medium',
    'bold': 'Figtree-Bold',
    'very-bold': 'Figtree-ExtraBold',
    'italic': 'ProductSans-BoldItalic',
    'mono-regular': 'Inconsolata-Regular',
    'mono-medium': 'Mono-Medium',
    'mono-bold': 'Mono-Bold',
    'mono-italic': 'SometypeMono-RegularItalic',
    'icons': 'SosaRegular.ttf'
}

color_table = {
    '§0': '#000000',
    '§1': '#0000AA',
    '§2': '#00AA00',
    '§3': '#00AAAA',
    '§4': '#AA0000',
    '§5': '#AA00AA',
    '§6': '#FFAA00',
    '§7': '#AAAAAA',
    '§8': '#555555',
    '§9': '#5555FF',
    '§a': '#55FF55',
    '§b': '#55FFFF',
    '§c': '#FF5555',
    '§d': '#FF55FF',
    '§e': '#FFFF55',
    '§f': '#FFFFFF'
}

background_color = (0.115, 0.115, 0.182, 1)
server_list = []
server_list_lower = []
new_server_info = {}
sub_processes = []


# For '*.bat' or '*.sh' respectively
start_script_name = "Start"


# Paths
os_name = 'windows' if os.name == 'nt' else 'macos' if system().lower() == 'darwin' else 'linux' if os.name == 'posix' else os.name
home = os.path.expanduser('~')
appdata = os.getenv("APPDATA") if os_name == 'windows' else f'{home}/Library/Application Support' if os_name == 'macos' else home
applicationFolder = os.path.join(appdata, ('.auto-mcs' if os_name != 'macos' else 'auto-mcs'))

saveFolder = os.path.join(appdata, '.minecraft', 'saves') if os_name != 'macos' else f"{home}/Library/Application Support/minecraft/saves"
downDir = os.path.join(applicationFolder, 'Downloads')
uploadDir = os.path.join(applicationFolder, 'Uploads')
backupFolder = os.path.join(applicationFolder, 'Backups')
userDownloads = os.path.join(home, 'Downloads')
serverDir = os.path.join(applicationFolder, 'Servers')
telepathFile = os.path.join(serverDir, 'telepath-servers.json')

tempDir = os.path.join(applicationFolder, 'Temp')
tmpsvr = os.path.join(tempDir, 'tmpsvr')
cacheDir = os.path.join(applicationFolder, 'Cache')
configDir = os.path.join(applicationFolder, 'Config')
scriptDir = os.path.join(applicationFolder, 'Tools', 'amscript')
javaDir = os.path.join(applicationFolder, 'Tools', 'java')
os_temp = os.getenv("TEMP") if os_name == "windows" else "/tmp"
global_conf = os.path.join(configDir, 'app-config.json')
username = ''

server_ini = 'auto-mcs.ini' if os_name == "windows" else '.auto-mcs.ini'
command_tmp = 'start-cmd.tmp' if os_name == "windows" else '.start-cmd.tmp'


# App/Assets folder
launch_path = None
if hasattr(sys, '_MEIPASS'):
    executable_folder = sys._MEIPASS
    gui_assets = os.path.join(executable_folder, 'gui-assets')
else:
    executable_folder = os.path.abspath(".")
    gui_assets = os.path.join(executable_folder, 'gui-assets')


# API stuff
def get_private_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(('10.254.254.254', 1))
        return s.getsockname()[0]
    finally:
        s.close()
def sync_attr(self, name):
    if name != '__all__':
        return getattr(self, name)
    else:
        blacklist = ['addon', 'backup', 'acl', 'script_manager', 'script_object', 'run_data', 'taskbar']
        def allow(x):
            return ((not callable(getattr(self, x))) and (str(x) not in blacklist) and (not str(x).endswith('__')))
        return {a: getattr(self, a) for a in dir(self) if allow(a)}
api_manager = None
headless = False
api_data = {
    "enabled": True,
    "version": "0.6.0",
    "show-banners": True,
    "default-host": "0.0.0.0",
    "default-port": 7001,
    "logo": "https://github.com/macarooni-man/auto-mcs/blob/main/source/gui-assets/logo.png?raw=true"
}

# Prevent app from closing during critical operations
ignore_close = False
telepath_banner = None
def allow_close(allow: bool, banner=''):
    global ignore_close
    ignore_close = not allow

    if banner and telepath_banner and api_data['show-banners']:
        telepath_banner(banner, allow)




# SSL crap
if os_name == 'linux':
    os.environ['SSL_CERT_DIR'] = executable_folder
    os.environ['SSL_CERT_FILE'] = os.path.join(executable_folder, 'ca-bundle.crt')

elif os_name == 'macos':
    os.environ['SSL_CERT_DIR'] = os.path.join(executable_folder, 'certifi')
    os.environ['SSL_CERT_FILE'] = os.path.join(executable_folder, 'certifi', 'cacert.pem')


# Ngrok info
ngrok_installed = False
ngrok_exec = 'ngrok-v3.exe' if os_name == 'windows' else 'ngrok-v3'

# Checks if ngrok is installed (returns bool)
def check_ngrok():
    global ngrok_installed
    ngrok_installed = os.path.exists(os.path.join(applicationFolder, 'Tools', ngrok_exec))
    return ngrok_installed
check_ngrok()


# Bigboi server manager
server_manager = None
search_manager = None
import_data = {'_telepath_data': None, 'name': None, 'path': None}
backup_lock = {}


# Maximum memory
total_ram = round(psutil.virtual_memory().total / 1073741824)
max_memory = int(round(total_ram - (total_ram / 4)))

# Replacement for os.system to prevent CMD flashing
def run_proc(cmd, return_text=False):
    if return_text:
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        if debug:
            print(f'{cmd}: returned exit code {result.returncode}')
        return result.stdout.decode('utf-8', errors='ignore')
    else:
        kwargs = {'stdout': subprocess.DEVNULL, 'stderr': subprocess.DEVNULL} if headless else {}
        return_code = subprocess.call(cmd, shell=True, **kwargs)
        if debug:
            print(f'{cmd}: returned exit code {return_code}')
        return return_code



# Check if running in Docker
def check_docker():
    cgroup = Path('/proc/self/cgroup')
    return Path('/.dockerenv').is_file() or cgroup.is_file() and 'docker' in cgroup.read_text()
is_docker = check_docker()

# Check if OS is ARM
def check_arm():
    if os_name != 'windows':
        return run_proc('uname -m', True).strip() == 'aarch64'
    else:
        return run_proc('echo %PROCESSOR_ARCHITECTURE%', True).strip() == 'ARM64'
is_arm = check_arm()



# Global amscripts

# Grabs amscript files from GitHub repo for downloading internally
ams_web_list = []
def get_repo_scripts():
    global ams_web_list
    try:
        latest_commit = requests.get("https://api.github.com/repos/macarooni-man/auto-mcs/commits").json()[0]['sha']
        ams_data = requests.get(f"https://api.github.com/repos/macarooni-man/auto-mcs/git/trees/{latest_commit}?recursive=1").json()

        script_dict = {}
        ams_list = []
        root_url = "https://raw.githubusercontent.com/macarooni-man/auto-mcs/main/"

        # Organize all script files
        for file in ams_data['tree']:
            if file['path'].startswith('amscript-library'):
                if "/" in file['path']:
                    root_name = file['path'].split("/")[1]
                    if root_name not in script_dict:
                        script_dict[root_name] = {'url': f'https://github.com/macarooni-man/auto-mcs/tree/main/{quote(file["path"])}'}
                    if root_name + "/" in file['path']:
                        script_dict[root_name][os.path.basename(file['path'])] = f"{root_url}{quote(file['path'])}"

        # Concurrently add scripts to ams_list
        def add_to_list(script, *args):
            ams_list.append(amscript.AmsWebObject(script))

        with ThreadPoolExecutor(max_workers=10) as pool:
            pool.map(add_to_list, script_dict.items())

        # Sort list by title
        ams_list = sorted(ams_list, key=lambda x: x.title, reverse=True)
    except:
        ams_list = []

    ams_web_list = ams_list
    return ams_list



# ---------------------------------------------- Global Functions ------------------------------------------------------

# Functions and data for translation
locale = 'en'
locale_file = os.path.join(executable_folder, 'locales.json')
locale_data = {}
if os.path.isfile(locale_file):
    with open(locale_file, 'r') as f:
        locale_data = json.loads(f.read())
available_locales = {
    "English": {"name": 'English', "code": 'en'},
    "Spanish": {"name": 'Español', "code": 'es'},
    "French": {"name": 'Français', "code": 'fr'},
    "Italian": {"name": 'Italiano', "code": 'it'},
    "German": {"name": 'Deutsch', "code": 'de'},
    "Dutch": {"name": 'Nederlands', "code": 'nl'},
    "Portuguese": {"name": 'Português', "code": 'pt'},
    "Swedish": {"name": 'Suédois', "code": 'sv'},
    "Finnish": {"name": 'Suomi', "code": 'fi'},

    # Requires special fonts:

    # "Chinese": {"name": '中文', "code": 'zh-CN'},
    # "Japanese": {"name": '日本語', "code": 'ja'},
    # "Korean": {"name": '한국어', "code": 'ko'},
    # "Arabic": {"name": 'العربية', "code": 'ar'},
    # "Russian": {"name": 'Русский', "code": 'ru'},
    # "Ukranian": {"name": 'Українська', "code": 'uk'},
    # "Serbian": {"name": 'Cрпски', "code": 'sr'},
    # "Japanese": {"name": '日本語', "code": 'ja'}
}
def get_locale_string(english=False, *a):
    for k, v in available_locales.items():
        if locale in v.values():
            return f'{k if english else v["name"]} ({v["code"]})'

def translate(text: str):
    global locale_data, locale

    # Ignore if text is blank, or locale is set to english
    if not text.strip() or locale.startswith('en'):
        return text

    # Create translator object
    # if not translator:
    #     translator = Translator()
    # return translator.translate(text, src='en', dest=locale).text


    # Searches locale_data for string
    def search_data(s, *a):
        try:
            return locale_data[s.strip().lower()][locale]
        except KeyError:
            pass


    # Extract proper noun if present with flag
    conserve = []
    if text.count('$') >= 2:
        dollar_pattern = re.compile(r'\$([^\$]+)\$')
        conserve = [i for i in re.findall(dollar_pattern, text)]
        text = re.sub(dollar_pattern, '$$', text)


    # First, attempt to get translation through locale_data directly
    new_text = search_data(text, False)

    # Second, attempt to translate matched words with regex
    if not new_text:
        def match_data(s, *a):
            try:
                return locale_data[s.group(0).strip().lower()][locale]
            except KeyError:
                pass
            return s.group(0)
        new_text = re.sub(r'\b\S+\b', match_data, text)


    # If a match was found, return text in its original case
    if new_text:

        # Escape proper nouns that ignore translation
        overrides = ('server.properties', 'server.jar', 'amscript', 'Geyser', 'Java', 'GB', '.zip')
        for o in overrides:
            new_key = search_data(o)
            if not new_key:
                continue

            if new_key in new_text:
                new_text = new_text.replace(new_key, o)
            elif new_key.upper() in new_text:
                new_text = new_text.replace(new_key.upper(), o.upper())
            elif new_key.lower() in new_text:
                new_text = new_text.replace(new_key.lower(), o.lower())


        # Manual overrides
        if locale == 'es':
            new_text = re.sub('servidor\.properties', 'server.properties', new_text, re.IGNORECASE)
            new_text = re.sub('servidor\.jar', 'server.jar', new_text, re.IGNORECASE)
            new_text = re.sub('control S', 'Administrar', new_text, re.IGNORECASE)
        if locale == 'it':
            new_text = re.sub(r'ESENTATO', 'ESCI', new_text, re.IGNORECASE)
        if locale == 'fr':
            new_text = re.sub(r'moire \(Go\)', 'moire (GB)', new_text, re.IGNORECASE)


        # Get the spacing in front and after the text
        if text.startswith(' ') or text.endswith(' '):
            try:
                before = re.search(r'(^\s+)', text).group(1)
            except:
                before = ''
            try:
                after = re.search(r'(?=.*)(\s+$)', text).group(1)
            except:
                after = ''
            new_text = f'{before}{new_text}{after}'


        # Keep case from original text
        if text == text.title():
            new_text = new_text.title()
        elif text == text.upper():
            new_text = new_text.upper()
        elif text == text.lower():
            new_text = new_text.lower()
        elif text.strip() == text[0].strip().upper() + text[1:].strip().lower():
            new_text = new_text[0].upper() + new_text[1:].lower()


        # Replace proper noun (rework this to iterate over each match, in case there are multiple
        for match in conserve:
            new_text = new_text.replace('$$', match, 1)

        # Remove dollar signs if they are still present for some reason
        new_text = re.sub(r'\$([^\$]+)\$', '\g<1>', new_text)

        return new_text

    # If not, return original text
    else:
        return re.sub(r'\$(.*)\$', '\g<1>', text)


# Returns False if less than 500MB free
def check_free_space():
    free_space = round(disk_usage('/').free / 1048576)
    return free_space > 500

def telepath_busy():
    return ignore_close and server_manager.remote_server


# Retrieves the refresh rate of the display to calculate consistent animation speed
def get_refresh_rate():
    global refresh_rate, anim_speed

    try:
        if os_name == "windows":
            rate = run_proc('powershell Get-WmiObject win32_videocontroller | findstr "CurrentRefreshRate"', True)
            if "CurrentRefreshRate" in rate:
                refresh_rate = round(float(rate.splitlines()[0].split(":")[1].strip()))

        elif os_name == 'macos':
            rate = run_proc('system_profiler SPDisplaysDataType | grep Hz', True)
            if "@ " in rate and "Hz" in rate:
                refresh_rate = round(float(re.search(r'(?<=@ ).*(?=Hz)', rate.strip())[0]))

        # Linux
        else:
            rate = run_proc('xrandr | grep "*"', True)
            if rate.strip().endswith("*"):
                refresh_rate = round(float(rate.splitlines()[0].strip().split(" ", 1)[1].strip().replace("*","")))

        # Modify animation speed based on refresh rate
        anim_speed = 0.78 + round(refresh_rate * 0.002, 2)
    except:
        pass


# Check for admin rights
def is_admin():
    try:
        if os_name == 'windows':
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() == 1
        else:
            return os.getuid() == 0
    except:
        return False


# Returns true if latest is greater than current
def check_app_version(current, latest, limit=None):

    # Makes list the size of the greatest list
    def normalize(l, s):
        if len(l) < s:
            for x in range(s - len(l)):
                l.append(0)
        return l

    c_list = [int(x) for x in current.split(".")]
    l_list = [int(x) for x in latest.split(".")]
    max_size = max(len(c_list), len(l_list))
    normalize(c_list, max_size)
    normalize(l_list, max_size)

    for x in range(max_size):

        if limit:
            if x >= limit:
                return False

        if l_list[x] > c_list[x]:
            return True

        elif c_list[x] > l_list[x]:
            return False
    else:
        return False


# Restarts auto-mcs by dynamically generating script
def restart_app(*a):
    executable = os.path.basename(launch_path)
    script_name = 'auto-mcs-reboot'

    # Generate Windows script to restart
    if os_name == "windows":
        script_name = f'{script_name}.bat'
        folder_check(tempDir)
        batch_path = os.path.join(tempDir, script_name)
        batch_file = open(batch_path, 'w+')

        if app_compiled:  # Running as compiled
            batch_file.write(
f"""taskkill /f /im \"{executable}\"
start \"\" \"{launch_path}\"
del \"{os.path.join(tempDir, script_name)}\""""
            )

            batch_file.close()
            run_proc(f"\"{batch_path}\" > nul 2>&1")


    # Generate Linux/macOS script to restart
    else:
        script_name = f'{script_name}.sh'
        folder_check(tempDir)
        shell_path = os.path.join(tempDir, script_name)
        shell_file = open(shell_path, 'w+')
        escaped_path = launch_path.replace(" ", "\ ")

        if app_compiled:  # Running as compiled
            shell_file.write(
f"""#!/bin/bash
kill {os.getpid()}
exec {escaped_path} &
rm \"{os.path.join(tempDir, script_name)}\""""
            )

            shell_file.close()
            with open(shell_path, 'r') as f:
                print(f.read())
            run_proc(f"chmod +x \"{shell_path}\" && bash \"{shell_path}\"")
    sys.exit()


# Restarts and updates auto-mcs by dynamically generating script
def restart_update_app(*a):
    executable = os.path.basename(launch_path)
    new_version = update_data['version']
    success_str = f"auto-mcs was updated to v${new_version}$ successfully!"
    success_unix = f"auto-mcs was updated to v\${new_version}\$ successfully!"
    failure_str = "Something went wrong with the update"
    script_name = 'auto-mcs-update'
    update_log = os.path.join(tempDir, 'update-log')
    folder_check(tempDir)

    # Delete guide cache in case of update
    guide_cache = os.path.join(cacheDir, 'guide-cache.json')
    if os.path.exists(guide_cache):
        try:
            os.remove(guide_cache)
        except:
            pass

    # Generate Windows script to restart
    if os_name == "windows":
        script_name = f'{script_name}.bat'
        folder_check(tempDir)
        batch_path = os.path.join(tempDir, script_name)
        batch_file = open(batch_path, 'w+')

        if app_compiled:  # Running as compiled
            batch_file.write(
f"""taskkill /f /im \"{executable}\"
timeout /t 3 /nobreak

copy /b /v /y "{os.path.join(downDir, 'auto-mcs.exe')}" "{launch_path}"
if exist "{launch_path}" if %ERRORLEVEL% EQU 0 (
    echo banner-success@{success_str} > "{update_log}"
) else (
    echo banner-failure@{failure_str} > "{update_log}"
)

start \"\" \"{launch_path}\"
del \"{os.path.join(tempDir, script_name)}\""""
            )

            batch_file.close()
            run_proc(f"\"{batch_path}\" > nul 2>&1")


    # Generate macOS script to restart
    elif os_name == 'macos':
        script_name = f'{script_name}.sh'
        folder_check(tempDir)
        shell_path = os.path.join(tempDir, script_name)
        shell_file = open(shell_path, 'w+')
        escaped_path = launch_path.replace(" ", "\ ")
        dmg_path = os.path.join(downDir, 'auto-mcs.dmg')

        if app_compiled:  # Running as compiled
            shell_file.write(
                f"""#!/bin/bash
kill {os.getpid()}
sleep 2

hdiutil mount "{dmg_path}"
rsync -a /Volumes/auto-mcs/auto-mcs.app/ "{os.path.join(os.path.dirname(launch_path), '../..')}"
errorlevel=$?
if [ -f "{launch_path}" ] && [ $errorlevel -eq 0 ]; then
    echo banner-success@{success_unix} > "{update_log}"
else
    echo banner-failure@{failure_str} > "{update_log}"
fi

hdiutil unmount /Volumes/auto-mcs
rm -rf "{dmg_path}"
chmod +x "{launch_path}"
exec {escaped_path} &
rm \"{os.path.join(tempDir, script_name)}\""""
            )

            shell_file.close()
            with open(shell_path, 'r') as f:
                print(f.read())
            run_proc(f"chmod +x \"{shell_path}\" && bash \"{shell_path}\"")


    # Generate Linux script to restart
    else:
        script_name = f'{script_name}.sh'
        folder_check(tempDir)
        shell_path = os.path.join(tempDir, script_name)
        shell_file = open(shell_path, 'w+')
        escaped_path = launch_path.replace(" ", "\ ")

        if app_compiled:  # Running as compiled
            shell_file.write(
f"""#!/bin/bash
kill {os.getpid()}
sleep 2

/bin/cp -rf "{os.path.join(downDir, 'auto-mcs')}" "{launch_path}"
errorlevel=$?
if [ -f "{launch_path}" ] && [ $errorlevel -eq 0 ]; then
    echo banner-success@{success_unix} > "{update_log}"
else
    echo banner-failure@{failure_str} > "{update_log}"
fi

chmod +x "{launch_path}"
exec {escaped_path} &
rm \"{os.path.join(tempDir, script_name)}\""""
            )

            shell_file.close()
            with open(shell_path, 'r') as f:
                print(f.read())
            run_proc(f"chmod +x \"{shell_path}\" && bash \"{shell_path}\"")
    sys.exit()



# Format date string to be cross-platform compatible
def fmt_date(date_string: str):
    if os_name == 'windows':
        return date_string
    else:
        return date_string.replace('%#','%-')

# Returns current formatted time
def format_now():
    return datetime.datetime.now().strftime(fmt_date("%#I:%M:%S %p"))


# Global banner
global_banner = None


# Hide kivy widgets
def hide_widget(wid, dohide=True, *argies):
    if hasattr(wid, 'saved_attrs'):
        if not dohide:
            wid.height, wid.size_hint_y, wid.opacity, wid.disabled = wid.saved_attrs
            del wid.saved_attrs
    elif dohide:
        wid.saved_attrs = wid.height, wid.size_hint_y, wid.opacity, wid.disabled
        wid.height, wid.size_hint_y, wid.opacity, wid.disabled = 0, None, 0, True


# Converts between HEX and RGB decimal colors
def convert_color(color: str or tuple):

    # HEX
    if isinstance(color, str):
        color = color.replace("#", "")
        if len(color) == 6:
            split_color = (color[0:2], color[2:4], color[4:6])
        else:
            split_color = (color[0]*2, color[1]*2, color[2]*2)

        new_color = [0, 0, 0]

        for x, item in enumerate(split_color):
            item = round(int(item, 16) / 255, 3)
            new_color[x] = int(item) if item in [0, 1] else item

        new_color.append(1)

        return {'hex': '#'+''.join(split_color).upper(), 'rgb': tuple(new_color)}


    # RGB decimal
    else:

        new_color = "#"

        for item in color[0:3]:
            x = str(hex(round(item * 255)).split("0x")[1]).upper()
            x = f"0{x}" if len(x) == 1 else "FF" if len(x) > 2 else x
            new_color += x

        rgb_color = list(color[0:3])
        rgb_color.append(1)

        return {'hex': new_color, 'rgb': tuple(rgb_color)}


# Returns modified color tuple
def brighten_color(color: tuple or str, amount: float):

    # If HEX, convert to decimal RGB
    hex_input = False
    if isinstance(color, str):
        color = convert_color(color)['rgb']
        hex_input = True


    color = list(color)

    for x, y in enumerate(color):
        if x < 3:
            new_amount = y + amount
            new_amount = 1 if new_amount > 1 else 0 if new_amount < 0 else new_amount
            color[x] = new_amount

    return convert_color(color)['hex'] if hex_input else tuple(color)


# Returns similarity of strings with a metric of 0-1
def similarity(a, b):
    return round(SequenceMatcher(None, a, b).ratio(), 2)


# Cloudscraper requests
global_scraper = None
def return_scraper(url_path: str, head=False):
    global global_scraper

    if not global_scraper:
        global_scraper = cloudscraper.create_scraper(
            browser={'custom': f'Auto-MCS/{app_version}', 'platform': os_name, 'mobile': False},
            ecdhCurve='secp384r1',
            debug=debug
        )

    return global_scraper.head(url_path) if head else global_scraper.get(url_path)

# Return html content or status code
def get_url(url: str, return_code=False, only_head=False, return_response=False):
    global global_scraper
    max_retries = 10
    for retry in range(0, max_retries + 1):
        try:
            html = return_scraper(url, head=(return_code or only_head))
            return html.status_code if return_code \
                else html if (only_head or return_response) \
                else BeautifulSoup(html.content, 'html.parser')

        except cloudscraper.exceptions.CloudflareChallengeError:
            global_scraper = None
            if retry >= max_retries:
                raise ConnectionRefusedError("The cloudscraper connection has failed")
            else:
                time.sleep((retry / 3))

        except Exception as e:
            raise e

# Download file and return existence
def cs_download_url(url: str, file_name: str, destination_path: str):
    global global_scraper
    max_retries = 10
    print(f"Downloading '{file_name}' to '{destination_path}'...")
    for retry in range(0, max_retries + 1):
        try:
            web_file = return_scraper(url)
            full_path = os.path.join(destination_path, file_name)
            folder_check(destination_path)
            with open(full_path, 'wb') as file:
                file.write(web_file.content)

            print(f"Download of '{file_name}' complete!")
            return os.path.exists(full_path)

        except cloudscraper.exceptions.CloudflareChallengeError:
            global_scraper = None
            if retry >= max_retries:
                raise ConnectionRefusedError("The cloudscraper connection has failed")
            else:
                time.sleep((retry / 3))

        except Exception as e:
            raise e

# Uploads a file or directory to a telepath session of auto-mcs --> destination path
def telepath_upload(telepath_data: dict, path: str):
    if os.path.exists(path):
        is_dir = False

        # If path is a directory, compress to tmp and use the archive instead
        if os.path.isdir(path):
            is_dir = True
            path = create_archive(path, tempDir, 'tar')

        url = f"http://{telepath_data['host']}:{telepath_data['port']}/main/upload_file?is_dir={is_dir}"
        data = requests.post(url, files={'file': open(path, 'rb')})
        return data.json()

# Downloads a file to a telepath session --> destination path
# Whitelist is for restricting downloadable content
telepath_download_whitelist = {
    'paths': [serverDir, scriptDir, backupFolder],
    'names': ['.ams', '.amb', 'server.properties', 'server-icon.png']
}
def telepath_download(telepath_data: dict, path: str, destination=downDir, rename=''):
    url = f"http://{telepath_data['host']}:{telepath_data['port']}/main/download_file?file={quote(path)}"
    data = requests.post(url, stream=True)

    # Save if the request was successful
    if data.status_code == 200:

        # File name input validation
        file_name = os.path.basename(rename if rename else path)
        if '/' in file_name:
            file_name = file_name.rsplit('/', 1)[-1]
        elif '\\' in file_name:
            file_name = file_name.rsplit('\\', 1)[-1]

        final_path = os.path.join(destination, file_name)
        folder_check(destination)

        with open(final_path, 'wb') as file:
            for chunk in data.iter_content(chunk_size=8192):
                file.write(chunk)

        return final_path

# Delete all files in telepath uploads remotely
def clear_uploads():
    safe_delete(uploadDir)
    return not os.path.exists(uploadDir)

# Gets a variable from this module, remotely if telepath_data is specified
def get_remote_var(var: str, telepath_data={}):
    if telepath_data:
        return api_manager.request(
            endpoint='/main/get_remote_var',
            host=telepath_data['host'],
            port=telepath_data['port'],
            args={'var': var}
        )

    else:
        try:
            var = getattr(sys.modules[__name__], var)
        except:
            var = None
        return var


# Removes invalid characters from a filename
def sanitize_name(value, addon=False):

    if value == 'WorldEdit for Bukkit':
        return 'WorldEdit'

    value = value.split(":")[0]
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\'\w\s-]', '', value)
    return re.sub(r'[-\s]+', '-', value).strip('-_')

# Comparison tool for Minecraft version strings
def version_check(version_a: str, comparator: str, version_b: str): # Comparator can be '>', '>=', '<', '<=', '=='
    try:

        # A greater than B
        if ">" in comparator:

            if "b" in version_a and "a" in version_b:
                return True

            elif "a" in version_a:
                if "a" in version_b:
                    version_a = float(version_a.replace("a1.", "", 1))
                    version_b = float(version_b.replace("a1.", "", 1))
                    if "=" in comparator:
                        return version_a >= version_b
                    else:
                        return version_a > version_b
                else:
                    return False

            elif "b" in version_a:
                if "b" in version_b:
                    version_a = float(version_a.replace("b1.", "", 1))
                    version_b = float(version_b.replace("b1.", "", 1))
                    if "=" in comparator:
                        return version_a >= version_b
                    else:
                        return version_a > version_b
                else:
                    return False

            else:
                if ("a" not in version_a and "a" in version_b) or ("b" not in version_a and "b" in version_b):
                    return True

                version_a = float(version_a.replace("1.", "", 1))
                version_b = float(version_b.replace("1.", "", 1))
                if "=" in comparator:
                    return version_a >= version_b
                else:
                    return version_a > version_b

        # A less than B
        elif "<" in comparator:

            if "b" in version_b and "a" in version_a:
                return True

            elif "a" in version_b:
                if "a" in version_a:
                    version_a = float(version_a.replace("a1.", "", 1))
                    version_b = float(version_b.replace("a1.", "", 1))
                    if "=" in comparator:
                        return version_a <= version_b
                    else:
                        return version_a < version_b
                else:
                    return False

            elif "b" in version_b:
                if "b" in version_a:
                    version_a = float(version_a.replace("b1.", "", 1))
                    version_b = float(version_b.replace("b1.", "", 1))
                    if "=" in comparator:
                        return version_a <= version_b
                    else:
                        return version_a < version_b
                else:
                    return False

            else:
                if ("a" not in version_b and "a" in version_a) or ("b" not in version_b and "b" in version_a):
                    return True

                version_a = float(version_a.replace("1.", "", 1))
                version_b = float(version_b.replace("1.", "", 1))
                if "=" in comparator:
                    return version_a <= version_b
                else:
                    return version_a < version_b

        # A equal to B
        elif comparator == "==":
            return version_a == version_b

    except ValueError:
        return False


# Check if level is compatible with server version
def check_world_version(world_path: str, server_version: str):  # Returns (True, "") if world is compatible, else (False, "world_version"). (False, None) if world has an unknown version

    world_path = os.path.abspath(world_path)
    level_dat = os.path.join(world_path, "level.dat")
    cache_file = os.path.join(applicationFolder, "Cache", "data-version-db.json")

    # Only check data version if world and cache file exist
    if os.path.isdir(world_path) and os.path.isfile(cache_file):
        if os.path.isfile(level_dat):
            try:
                nbt_file = nbt.NBTFile(level_dat, 'rb')
                world_data_version = str(nbt_file["Data"]["DataVersion"].value)

            # Return if old version with unknown type
            except KeyError or IndexError:
                return (False, None)

            # If world has data version
            else:

                with open(cache_file, 'r') as f:
                    cache_file = json.load(f)

                try:
                    world_version = ([item for item in cache_file.items() if world_data_version == item[1]][0])
                # Accept as valid if world could not be found, it's probably too new
                except IndexError:
                    return (True, None)
                try:
                    server_version = (server_version, cache_file[server_version])
                except:
                    server_version = (server_version, None)

                # If world newer than intended server, prompt user with error
                if version_check(world_version[0], ">", server_version[0]) and ('w' not in server_version[0]):
                    return (False, world_version[0])

                elif server_version[1]:
                    if int(world_version[1]) > int(server_version[1]):
                        return (False, world_version[0])

    # World is compatible, or otherwise can't check
    return (True, "")


# Verify a properly formatted IPv4 address/subnet prefix
def check_ip(addr: str, restrict=True):

    if isinstance(addr, dict):
        return False

    validIP = False

    if addr.count(".") == 3:

        octets = addr.split(".")
        if len(octets) == 4:

            try:
                x = 1
                for octet in octets:
                    float(octet)
                    octet = int(octet)

                    if octet in range(0, 255) or (x < 4 and octet == 255):
                        validIP = True

                        if (x == 4 and octet == 0) and restrict is True:
                            validIP = False
                            break

                    else:
                        validIP = False
                        break

                    x += 1

            except ValueError:
                validIP = False

    return validIP

def check_subnet(addr: str):
    if addr.count(".") == 3 and "/" in addr:
        return (int(addr.split("/")[1]) in range(16, 31)) and check_ip(addr.split("/")[0], False)

    elif addr.count(".") == 3 and "!w" in addr:
        return check_ip(addr.replace("!w", "").strip(), False)

    else:
        return False


# Create folder if it doesn't exist
def folder_check(directory: str):
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except FileExistsError:
            pass
        if debug:
            print(f'Created "{directory}"')
    else:
        if debug:
            print(f'"{directory}" already exists')


# Open folder in default file browser, and highlight if file is passed
def open_folder(directory: str):
    try:

        # Open directory, and highlight a file
        if os.path.isfile(directory):
            if os_name == 'linux':
                subprocess.Popen([
                    'dbus-send', '--session', '--print-reply', '--dest=org.freedesktop.FileManager1', '--type=method_call',
                    f'/org/freedesktop/FileManager1 org.freedesktop.FileManager1.ShowItems array:string:"file://{directory}"', 'string:""'
                ])
            elif os_name == 'macos':
                subprocess.Popen(['open', '-R', directory])
            elif os_name == 'windows':
                subprocess.Popen(['explorer', '/select,', directory])

        # Otherwise, just open a directory
        else:
                if os_name == 'linux':
                    subprocess.Popen(['xdg-open', directory])
                elif os_name == 'macos':
                    subprocess.Popen(['open', directory])
                elif os_name == 'windows':
                    subprocess.Popen(['explorer', directory])

    except Exception as e:
        if debug:
            print(f"Error opening '{directory}': {e}")
        return False


# Get current directory, and revert to exec path if it doesn't exist
def get_cwd():
    try:
        return os.path.abspath(os.curdir)
    except:
        return executable_folder


# Extract archive
def extract_archive(archive_file: str, export_path: str, skip_root=False):
    archive = None
    archive_type = None

    if debug:
        print(f"Extracting '{archive_file}' to '{export_path}'...")

    try:
        if archive_file.endswith("tar.gz"):
            archive = tarfile.open(archive_file, "r:gz")
            archive_type = "tar"
        elif archive_file.endswith("tar"):
            archive = tarfile.open(archive_file, "r:")
            archive_type = "tar"
        elif archive_file.endswith("zip") or archive_file.endswith("mrpack"):
            archive = zipfile.ZipFile(archive_file, 'r')
            archive_type = "zip"

        if archive and applicationFolder in os.path.split(export_path)[0]:
            folder_check(export_path)

            # Use tar if available, for speed
            use_tar = False
            if archive_type == 'tar':
                try:
                    rc = subprocess.call(['tar', '--help'], stdout=subprocess.DEVNULL)
                    use_tar = rc == 0

                except Exception as e:
                    if debug:
                        print(e)
                    use_tar = False

            if debug and use_tar:
                print('Extract: Using "tar" as a provider')


            # Keep integrity of archive
            if not skip_root:

                if use_tar:
                    archive_file = os.path.abspath(archive_file)
                    run_proc(f"tar -xf \"{archive_file}\" -C \"{export_path}\"")
                else:
                    archive.extractall(export_path)

            # Export from root folder instead
            else:
                if use_tar:
                    run_proc(f"tar -x{'z' if archive_file.endswith('.tar.gz') else ''}f \"{archive_file}\" -C \"{export_path}\"")

                    # Find sub-folders
                    folders = [f for f in glob(os.path.join(export_path, '*')) if os.path.isdir(f)]
                    target = os.path.join(export_path, folders[0])

                    # Move data to root, and delete the sub-folder
                    for f in glob(os.path.join(target, '*')):
                        move(f, os.path.join(export_path, os.path.basename(f)))

                    safe_delete(target)

                elif archive_type == "tar":
                    def remove_root(file):
                        root_path = file.getmembers()[0].path
                        if "/" in root_path:
                            root_path = root_path.split("/", 1)[0]
                        root_path += "/"
                        l = len(root_path)

                        for member in file.getmembers():
                            if member.path.startswith(root_path):
                                member.path = member.path[l:]
                                yield member
                    archive.extractall(export_path, members=remove_root(archive))

                elif archive_type == "zip":
                    root_path = archive.namelist()[0]
                    for zip_info in archive.infolist():
                        if zip_info.filename[-1] == '/':
                            continue
                        zip_info.filename = zip_info.filename[len(root_path):]
                        archive.extract(zip_info, export_path)

            if debug:
                print(f"Extracted '{archive_file}' to '{export_path}'")
        elif debug:
            print(f"Archive '{archive_file}' was not found")

    except Exception as e:
        print(f"Something went wrong extracting '{archive_file}': {e}")

    if archive:
        archive.close()


# Create an archive
def create_archive(file_path: str, export_path: str, archive_type='tar'):
    file_name = os.path.basename(file_path)
    archive_name = f'{file_name}.{archive_type}'
    final_path = os.path.join(export_path, archive_name)

    if debug:
        print(f"Compressing '{file_path}' to '{export_path}'...")

    folder_check(export_path)

    # Create a .tar archive
    if archive_type == 'tar':
        try:
            rc = subprocess.call(['tar', '--help'], stdout=subprocess.DEVNULL)
            use_tar = rc == 0

        except Exception as e:
            if debug:
                print(e)
            use_tar = False

        # Use tar command if available
        if use_tar:
            run_proc(f'tar -C \"{os.path.dirname(file_path)}\" -cvf \"{final_path}\" \"{file_name}\"')

        # Oherwise, use the Python implementation
        else:
            with tarfile.open(final_path, "w", compresslevel=6) as tar_file:
                # Use glob for when an asterisk is used
                for file in glob(file_path):
                    tar_file.add(file, os.path.basename(file))

    # Create a .zip archive
    elif archive_type == 'zip':
        with zipfile.ZipFile(final_path, "w", compresslevel=6) as zip_file:
            # Use glob for when an asterisk is used
            for file in glob(file_path):
                zip_file.write(file, os.path.basename(file))

    # Return file path if it exists
    if os.path.exists(final_path):

        if debug:
            print(f"Compressed '{file_path}' to '{export_path}'")

        return final_path

    else:
        print(f"Something went wrong compressing '{file_path}'")



# Check if root is a folder instead of files, and move sub-folders to destination
def move_files_root(source, destination=None):
    destination = source if not destination else destination
    folder_list = [d for d in glob(os.path.join(source, '*')) if os.path.isdir(d)]
    file_list = [f for f in glob(os.path.join(source, '*')) if os.path.isdir(f)]
    if len(folder_list) == 1 and len(file_list) <= 1:

        # Move data to root, and delete the sub-folder
        for f in glob(os.path.join(folder_list[0], '*')):
            move(f, os.path.join(destination, os.path.basename(f)))
        safe_delete(folder_list[0])

    # If destination is a different path and there is no root folder, move anyway
    elif source != destination:
        for f in glob(os.path.join(source, '*')):
            move(f, os.path.join(destination, os.path.basename(f)))


# Download file from URL to directory
def download_url(url: str, file_name: str, output_path: str, progress_func=None):
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers, stream=True)
    response.raise_for_status()

    file_path = os.path.join(output_path, file_name)
    folder_check(output_path)

    with open(file_path, 'wb') as file:
        total_length = response.headers.get('content-length')
        if total_length is None:  # no content length header
            file.write(response.content)
            if progress_func:
                progress_func(1, 1, 1)
        else:
            total_length = int(total_length)
            chunk_size = 8192
            for chunk, data in enumerate(response.iter_content(chunk_size=chunk_size), 0):
                file.write(data)
                if progress_func:
                    progress_func(chunk, chunk_size, total_length)

    if os.path.isfile(file_path):
        return file_path


# Will attempt to delete dir tree without error
def safe_delete(directory: str):
    if not directory:
        return
    try:
        if os.path.exists(directory):
            rmtree(directory)
    except OSError as e:
        print(e)
        print(f"Could not delete '{directory}'")


# Delete every '_MEIPASS' folder in case of leftover files, and delete '.auto-mcs\Downloads' and '.auto-mcs\Uploads'
def cleanup_old_files():
    os_temp_folder = os.path.normpath(executable_folder + os.sep + os.pardir)
    for item in glob(os.path.join(os_temp_folder, "*")):
        if (item != executable_folder) and ("_MEI" in os.path.basename(item)):
            if os.path.exists(os.path.join(item, 'gui-assets', 'animations', 'loading_pickaxe.gif')):
                try:
                    safe_delete(item)
                    print(f"Deleted remnants of '{item}'")
                except PermissionError:
                    pass
    safe_delete(os.path.join(os_temp, '.kivy'))

    # Delete temporary files
    safe_delete(downDir)
    safe_delete(uploadDir)
    safe_delete(tempDir)


# Glob to find hidden folders as well
def hidden_glob(path: str):

    home_shortcut = False
    if "~" in path:
        home_shortcut = True
        path = path.replace("~", home)

    final_list = [item for item in glob(path + "*")]
    relative_dir = os.path.split(path)[0]
    try:
        final_list += [os.path.join(relative_dir, item) for item in os.listdir(relative_dir)
                       if item.startswith(".") and item.startswith(os.path.split(path)[0])]
    except OSError:
        pass

    if home_shortcut:
        final_list = [item.replace(home, "~") for item in final_list]

    if executable_folder in final_list:
        final_list.remove(executable_folder)

    final_list = [item for item in final_list if item.startswith(path.replace(home, "~") if home_shortcut else path)]

    final_list = sorted(final_list)
    return final_list


# Rotate an array
# (int) rotation: 'x' is forwards, '-x' is backwards
def rotate_array(array: list, rotation: int):

    if rotation > 0:
        for x in range(0, rotation):
            array.insert(0, array.pop(-1))
    else:
        for x in range(rotation, 0):
            array.append(array.pop(0))

    return array


# Cross-platform function to copy a file or folder
# src_dir --> ../dst_dir/new_name
def copy_to(src_dir: str, dst_dir: str, new_name: str, overwrite=True):
    final_path = os.path.join(dst_dir, new_name)
    item_type = "file" if os.path.isfile(src_dir) else "directory" if os.path.isdir(src_dir) else None
    success = False
    final_item = None

    # Check if src_dir is file or folder, and if dst_dir can be written to
    if os.path.exists(src_dir) and item_type:
        if (os.path.exists(final_path) and overwrite) or (not os.path.exists(final_path)):

            # if debug:
            print(f"Copying '{os.path.basename(src_dir)}' to '{final_path}'...")
            folder_check(dst_dir)

            if item_type == "file":
                final_item = copy(src_dir, final_path)

            elif item_type == "directory":
                final_item = copytree(src_dir, final_path, dirs_exist_ok=True, ignore=ignore_patterns('*session.lock'))

            if final_item:
                success = True
                # if debug:
                print(f"Copied to '{new_name}' successfully!")

    if not success:
        # if debug:
        print(f"Something went wrong copying to '{new_name}'")

    return success


# Create random string of characters
def gen_rstring(size: int):
    return ''.join(choices(string.ascii_uppercase + string.ascii_lowercase, k=size))



# --------------------------------------------- Startup Functions ------------------------------------------------------

# Check if client has an internet connection
def check_app_updates():
    global project_link, app_version, dev_version, app_latest, app_online, update_data, auto_update

    # Check if updates are available
    try:
        # Grab release data
        latest_release = f"https://api.github.com/repos{project_link.split('.com')[1]}/releases/latest"
        req = requests.get(latest_release, timeout=5)
        status_code = req.status_code
        app_online = status_code in (200, 403)
        release_data = req.json()

        # Don't automatically update if specified in config
        if not auto_update:
            app_latest = True
            return None

        # Get checksum data
        try:
            description, md5_str = release_data['body'].split("MD5 Checksums", 1)
            update_data['desc'] = description.replace("- ", "• ").strip().replace('<br>', '\n').replace("`", "")

            checksum = ""
            for line in md5_str.splitlines():
                if line == '`':
                    continue

                if checksum:
                    update_data['md5'][checksum] = line.strip()
                    checksum = ""
                    continue

                if "Windows" in line:
                    checksum = "windows"
                    continue

                if "macOS" in line:
                    checksum = "macos"
                    continue

                if "arm64" in line.lower():
                    checksum = "linux-arm64"
                    continue

                if "Linux" in line:
                    checksum = "linux"
                    continue
        except:
            pass


        # Format release data
        version = release_data['name']
        if "-" in version:
            update_data['version'] = version[1:].split("-")[0].strip()
        elif " " in version:
            update_data['version'] = version[1:].split(" ")[0].strip()
        elif "v" in version:
            update_data['version'] = version[1:].strip()
        else:
            update_data['version'] = app_version


        # Download links
        for file in release_data['assets']:
            if 'windows' in file['name']:
                update_data['urls']['windows'] = file['browser_download_url']
                continue
            if 'macos' in file['name']:
                update_data['urls']['macos'] = file['browser_download_url']
                continue
            if 'arm64' in file['name']:
                update_data['urls']['linux-arm64'] = file['browser_download_url']
                continue
            if 'linux' in file['name']:
                update_data['urls']['linux'] = file['browser_download_url']
                continue

        # Check if app needs to be updated, and URL was successful
        if check_app_version(str(app_version), str(update_data['version'])):
            app_latest = False

        # Check if dev version
        elif (str(app_version) != str(update_data['version'])) and check_app_version(str(update_data['version']), str(app_version)):
            dev_version = True

    except Exception as e:
        if debug:
            print("Something went wrong checking for updates: ", e)


# Get latest game versions
def find_latest_mc():
    timeout = 15

    def latest_version(name, url):

        if name == "vanilla":
            # Vanilla
            try:
                reqs = requests.get(url, timeout=timeout)
                soup = BeautifulSoup(reqs.text, 'html.parser')

                for div in soup.find_all('div', "item flex items-center p-3 border-b border-gray-700 snap-start ncItem"):
                    if "latest release" in div.div.span.text.lower():
                        latestMC["vanilla"] = div.get('data-version')
                        break
            except:
                with open(os.path.join(cacheDir, 'data-version-db.json'), 'r') as f:
                    for key in json.loads(f.read()).keys():
                        for char in key:
                            if char.isalpha():
                                break
                        else:
                            latestMC["vanilla"] = key
                            break


        elif name == "forge":
            # Forge
            reqs = requests.get(url, timeout=timeout)
            soup = BeautifulSoup(reqs.text, 'html.parser')

            # Get side panel latest version
            li = soup.find('li', 'li-version-list')

            try:
                new_url = url.rsplit('/', 1)[0] + '/' + li.find_all('a')[-1].get('href')
                reqs = requests.get(new_url, timeout=timeout)
                soup = BeautifulSoup(reqs.text, 'html.parser')
            except:
                pass

            title_list = soup.find_all('div', "title")

            for div in title_list:
                if "download recommended" in div.text.lower():
                    latestMC["forge"] = div.small.text.split(" -")[0]
                    latestMC["builds"]["forge"] = div.small.text.split(" - ")[1]
                    break
            else:
                for div in title_list:
                    if "download latest" in div.text.lower():
                        latestMC["forge"] = div.small.text.split(" -")[0]
                        latestMC["builds"]["forge"] = div.small.text.split(" - ")[1]
                        break


        elif name == "paper":
            # Paper
            reqs = requests.get(url, timeout=timeout)

            jsonObject = json.loads(reqs.text)
            version = jsonObject['versions'][-1]
            latestMC["paper"] = version

            build_url = f"{url}/versions/{version}"
            reqs = requests.get(build_url)
            jsonObject = json.loads(reqs.text)
            latestMC["builds"]["paper"] = jsonObject['builds'][-1]


        elif name == "purpur":
            # Purpur
            reqs = requests.get(url, timeout=timeout)

            jsonObject = json.loads(reqs.text)
            version = jsonObject['versions'][-1]
            latestMC["purpur"] = version

            build_url = f"{url}/{version}"
            reqs = requests.get(build_url)
            jsonObject = json.loads(reqs.text)
            latestMC["builds"]["purpur"] = jsonObject['builds']['latest']


        elif name == "spigot":
            # Spigot
            reqs = requests.get(url, timeout=timeout)
            soup = BeautifulSoup(reqs.text, 'html.parser')

            latestMC["spigot"] = soup.find('div', "row vdivide").h2.text


        elif name == "craftbukkit":
            # Craftbukkit
            reqs = requests.get(url, timeout=timeout)
            soup = BeautifulSoup(reqs.text, 'html.parser')

            latestMC["craftbukkit"] = soup.find('div', "row vdivide").h2.text


        elif name == "fabric":
            # Fabric
            version = "https://meta.fabricmc.net/v2/versions/game"
            loader = "https://meta.fabricmc.net/v2/versions/loader"
            installer = "https://meta.fabricmc.net/v2/versions/installer"

            # Game version
            reqs = requests.get(version, timeout=timeout)
            jsonObject = json.loads(reqs.text)

            for item in jsonObject:
                if item['stable']:
                    version = item['version']
                    break

            # Loader build
            reqs = requests.get(loader, timeout=timeout)
            jsonObject = json.loads(reqs.text)

            for item in jsonObject:
                if item['stable']:
                    loader = item['version']
                    break

            # Installer build
            reqs = requests.get(installer, timeout=timeout)
            jsonObject = json.loads(reqs.text)

            for item in jsonObject:
                if item['stable']:
                    installer = item['version']
                    break

            latestMC["fabric"] = version
            latestMC["builds"]["fabric"] = f"{loader}/{installer}"
            # URL: https://meta.fabricmc.net/v2/versions/loader/{version}/{build}/server/jar

    version_links = {
        "vanilla": "https://mcversions.net/index.html",
        "forge": "https://files.minecraftforge.net/net/minecraftforge/forge/",
        "paper": "https://papermc.io/api/v2/projects/paper",
        "purpur": "https://api.purpurmc.org/v2/purpur",
        "spigot": "https://getbukkit.org/download/spigot",
        "craftbukkit": "https://getbukkit.org/download/craftbukkit",
        "fabric": "https://fabricmc.net/use/server/"
    }

    with ThreadPoolExecutor(max_workers=6) as pool:
        pool.map(latest_version, version_links.keys(), version_links.values())


# Grabs list of data versions from wiki page
def get_data_versions():
    # Parse data
    final_data = {}
    page_exists = True

    # Request data and see if page exists
    url = f"https://minecraft.fandom.com/wiki/Data_version#List_of_data_versions"
    data = None
    try:
        data = requests.get(url, timeout=2)
    except requests.exceptions.ReadTimeout:
        page_exists = False

    if data.status_code != 200:
        page_exists = False

    if not data or not page_exists:
        if debug:
            print("get_data_versions() error: Failed to retrieve data versions")
        return None

    soup = BeautifulSoup(data.text, 'html.parser')

    # Assign data versions to dictionary
    table = soup.find("table", {"class": "wikitable sortable jquery-tablesorter"})

    for item in table.find_all("tr"):
        title = None
        try:
            title = item.a.get("title").lower()
        except AttributeError:
            pass

        if not title:
            continue

        if "java" in title:

            # Level ID = dict entry
            cols = item.find_all("td")

            try:
                data = cols[2].text
            except IndexError:
                data = None

            final_data[title.replace("java edition ","")] = data

    # All data returned as dict
    return final_data


# Checks data versions cache
def check_data_cache():
    renew_cache = False
    cache_file = os.path.join(applicationFolder, "Cache", "data-version-db.json")

    # Error out if latest version could not be located
    if latestMC["vanilla"] == "0.0.0":
        if debug:
            print("check_data_cache() error: Latest Vanilla version could not be found, skipping")
        return

    if not os.path.isfile(cache_file):
        renew_cache = True

    else:
        with open(cache_file, 'r') as f:
            if latestMC["vanilla"] not in json.load(f):
                renew_cache = True

    # Update cache file
    if renew_cache:
        folder_check(os.path.join(applicationFolder, "Cache"))
        data_versions = get_data_versions()

        if data_versions:
            with open(cache_file, 'w+') as f:
                f.write(json.dumps(data_versions, indent=2))


# Random splash message
def generate_splash(crash=False):
    global session_splash

    splashes = ["Nothing is impossible, unless you can't do it.", "Every 60 seconds in Africa, a minute goes by.",
            "Did you know: you were born on your birthday.", "Okay, I'm here. What are your other two wishes?",
            "Sometimes when you close your eyes, you may not be able to see.",
            "Common sense is the most limited of all natural resources.", "Ah, yes. That will be $69,420.00",
            "Some mints can be very dangerous.", "Paper grows on trees.",
            "You forgot? No problem. It's USERNAME PASSWORD123.", "This is just like my Yamaha Motorcycle!",
            "n o t  c o o l  m a n!", "Existing is prohibited from the premises.", "no", "Oh no, the monster died!",
            "Black holes are essentially God divided by 0",
            "If you try and don't succeed, you probably shouldn't skydive",
            "On the other hand, you have different fingers.", "A day without sunshine is like night.",
            "?What are you doing here stranger¿", "Get outta my swamp!", "Whoever put the word fun in funeral?",
            "A new day is like a new day.", "Everywhere is within walking distance if you have the time.",
            "empty blank", "Money doesn’t buy happiness, but it does buy everything else.",
            "Congratulations! It's a pizza!",
            "Silence is golden, but duck tape is silver.", "Welcome to flavortown!",
            "I get enough exercise pushing my luck.",
            "Unicorns ARE real, they’re just fat, grey, and we call them rhinos.",
            "I’d like to help you out. Which way did you come in?", "There are too many dogs in your inventory.",
            "Careful man, there's a beverage present.", "Fool me once, fool me twice, fool me chicken soup with rice.",
            "60% of the time, it works EVERYTIME!", "Imagine how is touch the sky.",
            "I can't find my keyboard, it must be here somewhere...", "The quick brown fox jumped over the lazy dog.",
            "No, this is Patrick.", "My spirit animal will eat yours.", "Roses are red, violets are blue, lmao XD UWU!",
            "You can't run away from all your problems…\n            Not when they have ender pearls."]

    if crash:
        exp = re.sub('\s+',' ',splashes[randrange(len(splashes))]).strip()
        return f'"{exp}"'

    session_splash = f"“ {splashes[randrange(len(splashes))]} ”"


# Downloads the latest version of auto-mcs if available
def download_update(progress_func=None):

    def hook(a, b, c):
        if progress_func:
            progress_func(round(100 * a * b / c))

    if os_name == 'linux' and is_arm:
        update_url = update_data['urls']['linux-arm64']
    else:
        update_url = update_data['urls'][os_name]

    if not update_url:
        return False

    # Attempt at most 3 times to download auto-mcs
    fail_count = 0
    while fail_count < 3:

        safe_delete(downDir)
        folder_check(downDir)

        try:

            if progress_func and fail_count > 0:
                progress_func(0)


            # Specify names
            if os_name == 'macos':
                binary_zip = 'auto-mcs.dmg'
                binary_name = 'auto-mcs.app'
            else:
                binary_zip = 'auto-mcs.zip'
                binary_name = 'auto-mcs.exe' if os_name == 'windows' else 'auto-mcs'

            # Download binary zip, and extract the binary from the archive
            download_url(update_url, binary_zip, downDir, hook)
            update_path = os.path.join(downDir, binary_zip)

            if os_name == 'macos':
                binary_file = update_path
            else:
                extract_archive(update_path, downDir)
                os.remove(update_path)
                binary_file = os.path.join(downDir, binary_name)


            # If successful, copy to tmpsvr
            if os.path.isfile(binary_file):

                # If the hash matches, continue
                if get_checksum(binary_file) == update_data['md5'][os_name]:

                    if progress_func:
                        progress_func(100)

                    fail_count = 0
                    break

                else:
                    fail_count += 1

        except Exception as e:
            print(e)
            fail_count += 1


    return fail_count < 5


# Returns MD5 checksum of file
def get_checksum(file_path):
    return str(hashlib.md5(open(file_path, 'rb').read()).hexdigest())


# Grabs addon_cache if it exists
def load_addon_cache(write=False, telepath=False):
    if not telepath and server_manager.current_server:
        telepath_data = server_manager.current_server._telepath_data
        if telepath_data:
            response = api_manager.request(
                endpoint='/addon/load_addon_cache',
                host=telepath_data['host'],
                port=telepath_data['port'],
                args={'write': write, 'telepath': True}
            )
            return response


    global addon_cache
    file_name = "addon-db.json"
    file_path = os.path.join(cacheDir, file_name)

    # Loads data from dict
    if not write:
        try:
            if os.path.isfile(file_path):
                with open(file_path, 'r') as f:
                    addon_cache = json.load(f)
        except:
            return
    else:
        try:
            folder_check(cacheDir)
            with open(file_path, 'w+') as f:
                f.write(json.dumps(addon_cache, indent=2))
        except:
            return



# ------------------------------------ Server Creation/Import/Update Functions -----------------------------------------

# For validation of server version during server creation/modification
def validate_version(server_info: dict):
    global version_loading

    version_loading = True

    foundServer = False
    modifiedVersion = 0
    originalRequest = mcVer = server_info['version']
    mcType = server_info['type']
    buildNum = server_info['build']
    final_info = [False, {'version': mcVer, 'build': buildNum}, '', None] # [if version acceptable, {version, build}, message]
    url = ""

    # Remove below 1.6 versions for Forge
    try:

        while foundServer is False:
            if str.lower(mcType) == "forge":
                if version_check(mcVer, '<', '1.6'):
                    mcVer = ""


            if str.lower(mcType) == "vanilla":

                # Fix for "no main manifest attribute, in server.jar"
                if version_check(mcVer, '>=', '1.0') and version_check(mcVer, '<', '1.2'):
                    mcVer2 = '1.0.0' if mcVer == '1.0' else mcVer
                    url = f"http://files.betacraft.uk/server-archive/release/{mcVer}/{mcVer2}.jar"

                # Every other vanilla release
                else:
                    url = f"https://mcversions.net/download/{mcVer}"


            elif str.lower(mcType) == "craftbukkit":
                cb_url = "https://getbukkit.org/download/craftbukkit"

                # Workaround to prevent downloading Java 16 as well
                if mcVer != "1.17":

                    reqs = requests.get(cb_url)
                    soup = BeautifulSoup(reqs.text, 'html.parser')

                    for div in soup.find_all('div', "row vdivide"):
                        if div.h2.text == str(mcVer):

                            reqs = requests.get(div.a.get('href'))
                            soup = BeautifulSoup(reqs.text, 'html.parser')

                            for div in soup.find_all('div', "well"):
                                url = div.h2.a.get('href')
                                break

                            break


            elif str.lower(mcType) == "spigot":
                cb_url = "https://getbukkit.org/download/spigot"

                # Workaround to prevent downloading Java 16 as well
                if mcVer != "1.17":

                    reqs = requests.get(cb_url)
                    soup = BeautifulSoup(reqs.text, 'html.parser')

                    for div in soup.find_all('div', "row vdivide"):
                        if div.h2.text.strip() == str(mcVer):

                            reqs = requests.get(div.a.get('href'))
                            soup = BeautifulSoup(reqs.text, 'html.parser')

                            for div in soup.find_all('div', "well"):
                                url = div.h2.a.get('href')
                                break

                            break


            elif str.lower(mcType) == "paper":

                # Workaround to prevent downloading Java 16 as well
                if mcVer != "1.17":

                    try:
                        paper_url = f"https://papermc.io/api/v2/projects/paper/versions/{mcVer}"
                        reqs = requests.get(paper_url)
                        jsonObject = json.loads(reqs.text)
                        buildNum = jsonObject['builds'][-1]

                        url = f"https://papermc.io/api/v2/projects/paper/versions/{mcVer}/builds/{buildNum}/downloads/paper-{mcVer}-{buildNum}.jar"
                    except:
                        url = ""


            elif str.lower(mcType) == "purpur":

                # Workaround to prevent downloading Java 16 as well
                if mcVer != "1.17":

                    try:
                        paper_url = f"https://api.purpurmc.org/v2/purpur/{mcVer}"
                        reqs = requests.get(paper_url)
                        jsonObject = json.loads(reqs.text)
                        buildNum = jsonObject['builds']['latest']

                        url = f"https://api.purpurmc.org/v2/purpur/{mcVer}/{buildNum}/download"
                    except:
                        url = ""


            elif str.lower(mcType) == "forge":

                # 1.16.3 is unavailable due to issues with Java
                # https://www.reddit.com/r/Minecraft/comments/s7ce50/serverhosting_forge_minecraft_keeps_crashing_on/
                if mcVer != "1.16.3":

                    try:
                        forge_url = f"https://files.minecraftforge.net/net/minecraftforge/forge/index_{mcVer}.html"
                        reqs = requests.get(forge_url)
                        soup = BeautifulSoup(reqs.text, 'html.parser')

                        download_divs = soup.find_all('div', "download")
                        dl = None
                        for div in download_divs:
                            if "download recommended" in div.find('div', "title").text.lower() and version_check(mcVer, '<=', '1.15.2'):
                                dl = div.find('div', "link link-boosted")
                                break
                        else:
                            for div in download_divs:
                                if "download latest" in div.find('div', "title").text.lower():
                                    dl = div.find('div', "link link-boosted")
                                    break

                        urls = dl.a.get('href').split("&url=")

                        for possible_url in urls:
                            if ".jar" in possible_url:
                                url = possible_url
                                break
                        else:
                            url = ''
                    except:
                        url = ''


            elif str.lower(mcType) == "fabric":
                version = "https://meta.fabricmc.net/v2/versions/game"
                loader = "https://meta.fabricmc.net/v2/versions/loader"
                installer = "https://meta.fabricmc.net/v2/versions/installer"

                # Game version
                reqs = requests.get(version)
                jsonObject = json.loads(reqs.text)

                for item in jsonObject:
                    if mcType == item['version']:
                        version = item['version']
                        break

                # Loader build
                reqs = requests.get(loader)
                jsonObject = json.loads(reqs.text)

                for item in jsonObject:
                    if item['stable']:
                        loader = item['version']
                        break

                # Installer build
                reqs = requests.get(installer)
                jsonObject = json.loads(reqs.text)

                for item in jsonObject:
                    if item['stable']:
                        installer = item['version']
                        break

                url = f"https://meta.fabricmc.net/v2/versions/loader/{mcVer}/{loader}/{installer}/server/jar"


            try:
                if get_url(url, return_code=True) == 200:
                    serverLink = url

                    # Upon valid URL
                    if mcType.lower() == "vanilla":

                        if version_check(mcVer, '>=', '1.0') and version_check(mcVer, '<', '1.2'):
                            pass

                        elif "b" in mcVer[:1]:
                            serverLink = f"https://archive.org/download/minecraft-beta-server-jars/Minecraft%20Beta%20Server%20Jars.zip/Minecraft%20Beta%20Server%20Jars%2FOffical%20Server%20Jars%2F{mcVer}.jar"

                        else:
                            soup = get_url(url)
                            urls = []

                            for link in soup.find_all('a'):
                                urls.append(link.get('href'))

                            serverLink = urls[3]


                    final_info = [True, {'version': mcVer, 'build': buildNum}, "", serverLink]

                    if modifiedVersion > 0:
                        final_info[2] = f"'${originalRequest}$' could not be found, using '${mcVer}$' instead"
                    originalRequest = ""

                    version_loading = False
                    return final_info


                else:
                    foundServer = False

            except Exception as e:
                print(e)
                foundServer = False

            if foundServer is False:

                # If failed
                if modifiedVersion == 1:
                    modifiedVersion = 0
                    mcVer = ""
                    break

                if modifiedVersion == 0:
                    modifiedVersion = 12
                else:
                    modifiedVersion -= 1

                versionCheck = int(mcVer.replace("1.", "", 1).split(".")[0])

                mcVer = f"1.{versionCheck}.{modifiedVersion}"

    except:
        mcVer = ''
        pass

    if not mcVer:
        final_info = [False, {'version': originalRequest, 'build': buildNum}, f"'${originalRequest}$' doesn't exist, or can't be retrieved", None]

    version_loading = False
    return final_info
def search_version(server_info: dict):

    if not server_info['version']:
        server_info['version'] = latestMC[server_info['type']]

        # Set build info
        if server_info['type'] in ["forge", "paper", "purpur"]:
            server_info['build'] = latestMC['builds'][server_info['type']]

    return validate_version(server_info)


# Generate new server configuration
def new_server_init():
    global new_server_info
    new_server_info = {
        "_hash": gen_rstring(8),
        '_telepath_data': None,

        "name": "",
        "type": "vanilla",
        "version": "",
        "build": "",
        "jar_link": "",
        "ip": "",
        "port": "25565",
        "server_settings": {
            "world": "world",
            "seed": "",
            "level_type": "default",
            "motd": "A Minecraft Server",

            # If hardcore, set difficulty=hard, hardcore=true
            "difficulty": "normal",
            "gamemode": "survival",

            # Modifies both peaceful and hostile mobs
            "spawn_creatures": True,
            "spawn_protection": False,
            "pvp": False,
            "max_players": "20",

            # Gamerules
            "keep_inventory": False,
            "daylight_weather_cycle": True,
            "command_blocks": False,
            "random_tick_speed": "3",

            # On bukkit derivatives, install geysermc, floodgate, and viaversion if version >= 1.13.2 (add -DPaper.ignoreJavaVersion=true if paper < 1.16.5)
            "geyser_support": False,
            "disable_chat_reporting": True

        },

        # Dynamic content
        "addon_objects": [],
        "acl_object": None

    }

# Override remote new server configuration
def push_new_server(server_info: dict):
    global new_server_info
    server_info['_telepath_data'] = None
    new_server_info = server_info

# Generate new server name
def new_server_name(existing_server=None):
    def iter_name(new_name):
        x = 1
        while new_name.lower() in server_list_lower:
            new_name = f'{new_name} ({x})'
            x += 1
        return new_name

    if existing_server:
        return iter_name(existing_server)

    elif not new_server_info['name']:
        new_server_info['name'] = iter_name('New Server')


# Verify portable java is available in '.auto-mcs\Tools', if not install it
modern_pct = 0
lts_pct = 0
legacy_pct = 0
def java_check(progress_func=None):

    # If telepath, check if Java is installed remotely
    telepath_data = None
    if server_manager.current_server:
        telepath_data = server_manager.current_server._telepath_data

    try:
        if not telepath_data and new_server_info['_telepath_data']:
            telepath_data = new_server_info['_telepath_data']
    except KeyError:
        pass

    if telepath_data:
        response = api_manager.request(
            endpoint='/main/java_check',
            host=telepath_data['host'],
            port=telepath_data['port'],
            args={}
        )
        if progress_func and response:
            progress_func(100)
        return response


    global java_executable, modern_pct, lts_pct, legacy_pct
    max_retries = 3
    retries = 0
    modern_version = 21

    java_url = {
        'windows': {
            "modern": f"https://download.oracle.com/java/{modern_version}/latest/jdk-{modern_version}_windows-x64_bin.zip",
            "lts": f"https://download.oracle.com/java/17/latest/jdk-17_windows-x64_bin.zip",
            "legacy": "https://javadl.oracle.com/webapps/download/GetFile/1.8.0_331-b09/165374ff4ea84ef0bbd821706e29b123/windows-i586/jre-8u331-windows-x64.tar.gz"
        },
        'linux': {
            "modern": f"https://download.oracle.com/java/{modern_version}/latest/jdk-{modern_version}_linux-x64_bin.tar.gz",
            "lts": f"https://download.oracle.com/java/17/latest/jdk-17_linux-x64_bin.tar.gz",
            "legacy": "https://javadl.oracle.com/webapps/download/GetFile/1.8.0_331-b09/165374ff4ea84ef0bbd821706e29b123/linux-i586/jre-8u331-linux-x64.tar.gz"
        },
        'linux-arm64': {
            "modern": f"https://download.oracle.com/java/{modern_version}/latest/jdk-{modern_version}_linux-aarch64_bin.tar.gz",
            "lts": f"https://download.oracle.com/java/17/latest/jdk-17_linux-aarch64_bin.tar.gz",
            "legacy": "https://javadl.oracle.com/webapps/download/GetFile/1.8.0_281-b09/89d678f2be164786b292527658ca1605/linux-i586/jdk-8u281-linux-aarch64.tar.gz"
        },
        'macos': {
            "modern": f"https://download.oracle.com/java/{modern_version}/latest/jdk-{modern_version}_macos-x64_bin.tar.gz",
            "lts": f"https://download.oracle.com/java/17/latest/jdk-17_macos-x64_bin.tar.gz",
            "legacy": "https://javadl.oracle.com/webapps/download/GetFile/1.8.0_331-b09/165374ff4ea84ef0bbd821706e29b123/unix-i586/jre-8u331-macosx-x64.tar.gz"
        }
    }

    while not (java_executable['modern'] and java_executable['lts'] and java_executable['legacy']):

        # Delete downloads folder
        safe_delete(downDir)

        # If max_retries exceeded, give up
        if retries > max_retries:
            if debug:
                print('\nJava failed to download or install\n')
            return False

        # Check if installations function before doing anything
        if os.path.exists(os.path.abspath(javaDir)):

            # Gather paths to Java installed internally
            if os_name == 'macos':
                modern_path = os.path.join(applicationFolder, 'Tools', 'java', 'modern', 'Contents', 'Home', 'bin', 'java')
                lts_path = os.path.join(applicationFolder, 'Tools', 'java', 'lts', 'Contents', 'Home', 'bin', 'java')
                legacy_path = os.path.join(applicationFolder, 'Tools', 'java', 'legacy', 'Contents', 'Home', 'bin', 'java')
                jar_path = os.path.join(applicationFolder, 'Tools', 'java', 'modern', 'Contents', 'Home', 'bin', 'jar')

            else:
                modern_path = os.path.join(applicationFolder, 'Tools', 'java', 'modern', 'bin', 'java.exe' if os_name == "windows" else 'java')
                lts_path = os.path.join(applicationFolder, 'Tools', 'java', 'lts', 'bin', 'java.exe' if os_name == "windows" else 'java')
                legacy_path = os.path.join(applicationFolder, 'Tools', 'java', 'legacy', 'bin', 'java.exe' if os_name == "windows" else 'java')
                jar_path = os.path.join(applicationFolder, 'Tools', 'java', 'modern', 'bin', 'jar.exe' if os_name == "windows" else 'jar')


            if (run_proc(f'"{os.path.abspath(modern_path)}" --version') == 0) and (run_proc(f'"{os.path.abspath(lts_path)}" --version') == 0) and (run_proc(f'"{os.path.abspath(legacy_path)}" -version') == 0):

                # Check for appropriate modern version
                if run_proc(f'"{os.path.abspath(modern_path)}" --version', return_text=True).startswith(f'java {modern_version}.'):

                    java_executable = {
                        "modern": str(os.path.abspath(modern_path)),
                        "lts": str(os.path.abspath(lts_path)),
                        "legacy": str(os.path.abspath(legacy_path)),
                        "jar": str(os.path.abspath(jar_path))
                    }

                    if debug:
                        print('\nValid Java installations detected\n')

                    if progress_func:
                        progress_func(100)

                    return True


        # If valid java installs are not detected, install them to '.auto-mcs\Tools'
        if not (java_executable['modern'] and java_executable['lts'] and java_executable['legacy']):

            if debug:
                print('\nJava is not detected, installing...\n')

            # Download java versions in threadpool:
            folder_check(downDir)

            modern_filename = f'modern-java.{os.path.basename(java_url[os_name]["modern"]).split(".", 1)[1]}'
            lts_filename = f'lts-java.{os.path.basename(java_url[os_name]["lts"]).split(".", 1)[1]}'
            legacy_filename = f'legacy-java.{os.path.basename(java_url[os_name]["legacy"]).split(".", 1)[1]}'

            # Use timer and combined function to get total percentage of both installs
            modern_pct = 0
            lts_pct = 0
            legacy_pct = 0

            def avg_total(*args):
                global modern_pct, legacy_pct
                while True:
                    progress_func(round((modern_pct + lts_pct + legacy_pct) / 3))
                    time.sleep(0.2)
                    if (modern_pct >= 100 and lts_pct >= 100 and legacy_pct >= 100):
                        break

            if progress_func:
                timer = Timer(0, function=avg_total)
                timer.daemon = True
                timer.start()  # Checks for potential crash


            # Detect if running on ARM
            if os_name == 'linux' and is_arm:
                os_download = 'linux-arm64'
            else:
                os_download = os_name


            with ThreadPoolExecutor(max_workers=2) as pool:

                def hook1(a, b, c):
                    global modern_pct
                    modern_pct = round(100 * a * b / c)

                def hook2(a, b, c):
                    global lts_pct
                    lts_pct = round(100 * a * b / c)

                def hook3(a, b, c):
                    global legacy_pct
                    legacy_pct = round(100 * a * b / c)

                pool.map(
                    download_url,
                    [java_url[os_download]['modern'], java_url[os_download]['lts'], java_url[os_download]['legacy']],
                    [modern_filename, lts_filename, legacy_filename],
                    [downDir, downDir, downDir],
                    [hook1 if progress_func else None, hook2 if progress_func else None, hook3 if progress_func else None]
                )

            if progress_func:
                timer.cancel()

            # Install java by extracting the files to their respective folder
            modern_path = os.path.join(javaDir, 'modern')
            lts_path = os.path.join(javaDir, 'lts')
            legacy_path = os.path.join(javaDir, 'legacy')

            safe_delete(modern_path)
            safe_delete(lts_path)
            safe_delete(legacy_path)

            with ThreadPoolExecutor(max_workers=2) as pool:
                pool.map(
                    extract_archive,
                    [os.path.join(downDir, modern_filename), os.path.join(downDir, lts_filename), os.path.join(downDir, legacy_filename)],
                    [modern_path, lts_path, legacy_path],
                    [True, True, True]
                )

            retries += 1

    else:
        if progress_func:
            progress_func(100)

        return True



# Create New Server stuffies

# Downloads jar file from new_server_info, and generates link if it doesn't exist
def download_jar(progress_func=None, imported=False):

    # If telepath, check if Java is installed remotely
    telepath_data = None
    if server_manager.current_server:
        telepath_data = server_manager.current_server._telepath_data

    try:
        if not telepath_data and new_server_info['_telepath_data']:
            telepath_data = new_server_info['_telepath_data']
    except KeyError:
        pass

    if telepath_data:
        response = api_manager.request(
            endpoint='/create/download_jar',
            host=telepath_data['host'],
            port=telepath_data['port'],
            args={'imported': imported}
        )
        if progress_func:
            progress_func(100)
        return response


    def hook(a, b, c):
        if progress_func:
            progress_func(round(100 * a * b / c))

    if imported:
        import_data['jar_link'] = search_version(import_data)[3]

    elif not new_server_info['jar_link']:
        new_server_info['jar_link'] = search_version(new_server_info)[3]

    # Attempt at most 5 times to download server.jar
    fail_count = 0
    while fail_count < 5:

        safe_delete(downDir)
        folder_check(downDir)
        folder_check(tmpsvr)

        try:

            if progress_func and fail_count > 0:
                progress_func(0)

            if imported:
                jar_name = ('forge' if import_data['type'] == 'forge' else 'server') + '.jar'
                download_url(import_data['jar_link'], jar_name, downDir, hook)

            else:
                jar_name = ('forge' if new_server_info['type'] == 'forge' else 'server') + '.jar'
                download_url(new_server_info['jar_link'], jar_name, downDir, hook)

            jar_path = os.path.join(downDir, jar_name)

            # If successful, copy to tmpsvr
            if os.path.exists(jar_path):

                if progress_func:
                    progress_func(100)

                fail_count = 0
                copy(jar_path, os.path.join(tmpsvr, jar_name))
                os.remove(jar_path)
                break

        except Exception as e:
            print(e)
            fail_count += 1


    return fail_count < 5


# Iterates through new server addon objects and downloads/installs them to tmpsvr
hook_lock = False
def iter_addons(progress_func=None, update=False, telepath=False):
    global hook_lock

    # If telepath, update addons remotely
    if telepath:
        server_obj = server_manager.remote_server

    else:
        if server_manager.current_server:
            telepath_data = server_manager.current_server._telepath_data
            if telepath_data:
                response = api_manager.request(
                    endpoint='/addon/iter_addons',
                    host=telepath_data['host'],
                    port=telepath_data['port'],
                    args={'update': update, 'telepath': True}
                )
                if progress_func and response:
                    progress_func(100)
                return response


    all_addons = deepcopy(new_server_info['addon_objects'])

    # Add additional addons based on server config

    # If chat reporting is enabled, add chat reporting addon as an addon object
    if new_server_info['server_settings']['disable_chat_reporting']:
        disable_addon = addons.disable_report_addon(new_server_info)
        if disable_addon:
            all_addons.append(disable_addon)

    # If geyser is enabled, add proper addons to list
    if new_server_info['server_settings']['geyser_support']:

        # Add vault for permissions
        if server_type(new_server_info['type']) == 'bukkit':
            vault = addons.find_addon('vault', new_server_info)
            if vault:
                if vault not in all_addons:
                    all_addons.append(vault)

        # Add Geyser, Floodgate, and ViaVersion
        for addon in addons.geyser_addons(new_server_info):
            all_addons.append(addon)

    # Install Fabric API alongside Fabric
    if new_server_info['type'] == 'fabric':
        fabric_api = addons.find_addon('Fabric API', new_server_info)
        if fabric_api:
            all_addons.append(fabric_api)


    addon_count = len(all_addons)


    # Skip step if there are no addons for some reason
    if addon_count == 0:
        return True

    addon_folder = "plugins" if server_type(new_server_info['type']) == 'bukkit' else 'mods'
    folder_check(os.path.join(tmpsvr, addon_folder))
    folder_check(os.path.join(tmpsvr, "disabled-" + addon_folder))

    def process_addon(addon_object):
        # Add exception handler at some point
        try:
            if addon_object.addon_object_type == "web":
                addons.download_addon(addon_object, new_server_info, tmpsvr=True)
            else:
                if update:

                    # Ignore updates for Geyser and Floodgate because they are already added
                    if addons.is_geyser_addon(addon_object):
                        return True

                    addon_web = addons.get_update_url(addon_object, new_server_info['version'], new_server_info['type'])
                    downloaded = addons.download_addon(addon_web, new_server_info, tmpsvr=True)
                    if not downloaded:
                        disabled_folder = "plugins" if server_type(server_obj.type) == 'bukkit' else 'mods'
                        copy(addon_object.path, os.path.join(tmpsvr, "disabled-" + disabled_folder, os.path.basename(addon_object.path)))

                    return True

                addons.import_addon(addon_object, new_server_info, tmpsvr=True)

        except Exception as e:
            if debug:
                print(e)


    # Iterate over all addon_objects in ThreadPool
    max_pct = 0
    hook_lock = False
    with ThreadPoolExecutor(max_workers=10) as pool:
        for x, result in enumerate(pool.map(process_addon, all_addons)):

            if x > max_pct:
                max_pct = x

            if progress_func and x >= max_pct and not hook_lock:
                hook_lock = True

                def hook():
                    global hook_lock
                    progress_func(round(100 * ((x + 1) / addon_count)))
                    time.sleep(0.2)
                    hook_lock = False

                timer = threading.Timer(0, hook)
                timer.daemon = True
                timer.start()

    if progress_func:
        progress_func(100)

    return True
def pre_addon_update(telepath=False):
    global new_server_info
    server_obj = server_manager.current_server

    if telepath:
        server_obj = server_manager.remote_server

    # If remote, do this through telepath
    else:
        telepath_data = server_obj._telepath_data
        if telepath_data:
            response = api_manager.request(
                endpoint='/addon/pre_addon_update',
                host=telepath_data['host'],
                port=telepath_data['port'],
                args={'telepath': True}
            )
            return response


    # Clear folders beforehand
    safe_delete(tmpsvr)
    safe_delete(tempDir)
    safe_delete(downDir)

    # Generate server info for downloading proper add-on versions
    new_server_init()
    new_server_info = server_obj.properties_dict()
    init_update(telepath=True)
    new_server_info['addon_objects'] = server_obj.addon.return_single_list()
def post_addon_update(telepath=False):
    global new_server_info
    server_obj = server_manager.current_server

    if telepath:
        server_obj = server_manager.remote_server

    # If remote, do this through telepath
    else:
        telepath_data = server_obj._telepath_data
        if telepath_data:
            response = api_manager.request(
                endpoint='/addon/post_addon_update',
                host=telepath_data['host'],
                port=telepath_data['port'],
                args={'telepath': True}
            )
            return response


    server_obj.addon.update_required = False

    # Clear items from addon cache to re-cache
    for addon in server_obj.addon.installed_addons['enabled']:
        if addon.hash in addon_cache:
            del addon_cache[addon.hash]
    load_addon_cache(True)

    # Copy folder to server path and delete tmpsvr
    new_path = os.path.join(serverDir, new_server_info['name'])
    copytree(tmpsvr, new_path, dirs_exist_ok=True)
    safe_delete(tempDir)
    safe_delete(downDir)

    new_server_info = {}


# If Fabric or Forge, install server
def install_server(progress_func=None, imported=False):

    # If telepath, check if Java is installed remotely
    telepath_data = None
    if server_manager.current_server:
        telepath_data = server_manager.current_server._telepath_data

    try:
        if not telepath_data and new_server_info['_telepath_data']:
            telepath_data = new_server_info['_telepath_data']
    except KeyError:
        pass

    if telepath_data:
        response = api_manager.request(
            endpoint='/create/install_server',
            host=telepath_data['host'],
            port=telepath_data['port'],
            args={'imported': imported}
        )
        if progress_func and response:
            progress_func(100)
        return response



    # Change directory to tmpsvr
    cwd = get_cwd()
    os.chdir(tmpsvr)

    if imported:
        jar_version = import_data['version']
        jar_type = import_data['type']
    else:
        jar_version = new_server_info['version']
        jar_type = new_server_info['type']


    # Install Forge server
    if jar_type == 'forge':

        run_proc(f'"{java_executable["modern"]}" -jar forge.jar -installServer')

        # Modern
        if version_check(jar_version, ">=", "1.17"):
            for f in glob("run*"):
                os.remove(f)

            for f in glob("user_jvm*"):
                os.remove(f)

            for f in glob("install*.log"):
                os.remove(f)


        # 1.6 to 1.16
        elif version_check(jar_version, ">=", "1.6") and version_check(jar_version, "<", "1.17"):
            if os_name == "windows":
                run_proc("move *forge-*.jar server.jar")
            else:
                run_proc("mv *forge-*.jar server.jar")

        for f in glob("forge.jar"):
            os.remove(f)


    # Install Fabric server
    elif jar_type == 'fabric':

        print("test", f'"{java_executable["modern"]}" -jar server.jar nogui')

        process = subprocess.Popen(f'"{java_executable["modern"]}" -jar server.jar nogui', shell=True)

        while True:
            time.sleep(1)
            log = os.path.join(tmpsvr, 'logs', 'latest.log')
            if os.path.exists(log):
                with open(log, 'r') as f:
                    if "You need to agree to the EULA in order to run the server. Go to eula.txt for more info" in f.read():
                        break

        process.kill()

        for f in glob("eula.txt"):
            os.remove(f)

        for f in glob("server.properties"):
            os.remove(f)


    # Change back to original directory
    os.chdir(cwd)

    return True


# Configures server via server info in a variety of ways
def generate_server_files(progress_func=None):

    # If telepath, do all of this remotely
    telepath_data = None
    if server_manager.current_server:
        telepath_data = server_manager.current_server._telepath_data

    try:
        if not telepath_data and new_server_info['_telepath_data']:
            telepath_data = new_server_info['_telepath_data']
    except KeyError:
        pass

    if telepath_data:
        response = api_manager.request(
            endpoint='/create/generate_server_files',
            host=telepath_data['host'],
            port=telepath_data['port'],
            args={}
        )
        if progress_func and response:
            progress_func(100)
        return response


    time_stamp = datetime.date.today().strftime(f"#%a %b %d ") + datetime.datetime.now().strftime("%H:%M:%S ") + "MCS" + datetime.date.today().strftime(f" %Y")
    world_name = 'world'


    # First, generate startup script
    generate_run_script(new_server_info, temp_server=True)


    # If custom world is selected, copy it to tmpsvr
    if new_server_info['server_settings']['world'] != 'world':
        world_name = os.path.basename(new_server_info['server_settings']['world'])
        copytree(new_server_info['server_settings']['world'], os.path.join(tmpsvr, world_name), dirs_exist_ok=True)


    # Fix level-type
    if version_check(new_server_info['version'], '>=', '1.19') and new_server_info['server_settings']['level_type'] == 'default':
        new_server_info['server_settings']['level_type'] = 'normal'


    # Create start-cmd.tmp for changing gamerules after the server starts
    if new_server_info['server_settings']['keep_inventory'] or new_server_info['server_settings']['daylight_weather_cycle'] or new_server_info['server_settings']['random_tick_speed'] and version_check(new_server_info['version'], '>=', '1.4.2'):
        with open(os.path.join(tmpsvr, command_tmp), 'w') as f:
            file = f"gamerule keepInventory {str(new_server_info['server_settings']['keep_inventory']).lower()}\n"
            if version_check(new_server_info['version'], '>=', '1.8'):
                file += f"gamerule randomTickSpeed {str(new_server_info['server_settings']['random_tick_speed']).lower()}\n"
            if version_check(new_server_info['version'], '>=', '1.6.1'):
                file += f"gamerule doDaylightCycle {str(new_server_info['server_settings']['daylight_weather_cycle']).lower()}\n"
                if version_check(new_server_info['version'], '>=', '1.11'):
                    file += f"gamerule doWeatherCycle {str(new_server_info['server_settings']['daylight_weather_cycle']).lower()}\n"
            f.write(file.strip())


    # Generate ACL rules to temp server
    if new_server_info['acl_object'].count_rules()['total'] > 0:
        new_server_info['acl_object'].write_rules()


    # Generate EULA.txt
    eula = f"""#By changing the setting below to TRUE you are indicating your agreement to our EULA (https://account.mojang.com/documents/minecraft_eula).
{time_stamp}
eula=true"""

    with open(os.path.join(tmpsvr, 'eula.txt'), 'w+') as f:
        f.write(eula)


    # Generate server.properties
    gamemode_dict = {
        'survival': 0,
        'creative': 1,
        'adventure': 2
    }

    difficulty_dict = {
        'peaceful': 0,
        'easy': 1,
        'normal': 2,
        'hard': 3,
        'hardcore': 3
    }

    if new_server_info['server_settings']['motd'].lower() == 'a minecraft server':
        motd = translate('A Minecraft Server')
    else:
        motd = new_server_info['server_settings']['motd']

    def bool_str(value):
        return 'true' if value else 'false'

    serverProperties = f"""#Minecraft server properties
{time_stamp}
view-distance=10
max-build-height=256
server-ip={new_server_info['ip']}
level-seed={new_server_info['server_settings']['seed']}
gamemode={gamemode_dict[new_server_info['server_settings']['gamemode']]}
server-port={new_server_info['port']}
enable-command-block={bool_str(new_server_info['server_settings']['command_blocks'])}
allow-nether=true
enable-rcon=false
op-permission-level=4
enable-query=false
generator-settings=
resource-pack=
player-idle-timeout=0
level-name={world_name}
motd={motd}
announce-player-achievements=true
force-gamemode=false
hardcore={bool_str(new_server_info['server_settings']['difficulty'] == 'hardcore')}
white-list={bool_str(new_server_info['acl_object']._server['whitelist'])}
pvp={bool_str(new_server_info['server_settings']['pvp'])}
spawn-npcs={bool_str(new_server_info['server_settings']['spawn_creatures'])}
generate-structures=true
spawn-animals={bool_str(new_server_info['server_settings']['spawn_creatures'])}
snooper-enabled=true
difficulty={difficulty_dict[new_server_info['server_settings']['difficulty']]}
network-compression-threshold=256
level-type={new_server_info['server_settings']['level_type']}
spawn-monsters={bool_str(new_server_info['server_settings']['spawn_creatures'])}
max-tick-time=60000
max-players={new_server_info['server_settings']['max_players']}
spawn-protection={20 if new_server_info['server_settings']['spawn_protection'] else 0}
online-mode={bool_str(not ("b" in new_server_info['version'][:1] or "a" in new_server_info['version'][:1]))}
allow-flight=true
resource-pack-hash=
max-world-size=29999984"""

    if version_check(new_server_info['version'], ">=", '1.13'):
        serverProperties += f"\nenforce_whitelist={bool_str(new_server_info['acl_object']._server['whitelist'])}"

    if version_check(new_server_info['version'], ">=", '1.19'):
        serverProperties += "\nenforce-secure-profile=false"

    with open(os.path.join(tmpsvr, 'server.properties'), 'w+') as f:
        f.write(serverProperties)


    # Create auto-mcs.ini
    create_server_config(new_server_info, temp_server=True)


    # Check if everything was created successfully
    if (os.path.exists(os.path.join(tmpsvr, 'server.properties')) and os.path.exists(os.path.join(tmpsvr, server_ini)) and os.path.exists(os.path.join(tmpsvr, 'eula.txt'))):

        # Copy folder to server path and delete tmpsvr
        new_path = os.path.join(serverDir, new_server_info['name'])
        copytree(tmpsvr, new_path, dirs_exist_ok=True)
        safe_delete(tempDir)
        safe_delete(downDir)

        if os_name == "windows":
            run_proc(f"attrib +H \"{os.path.join(new_path, server_ini)}\"")
            if os.path.exists(os.path.join(new_path, command_tmp)):
                run_proc(f"attrib +H \"{os.path.join(new_path, command_tmp)}\"")

        make_update_list()
        return True
def pre_server_create(telepath=False):
    telepath_data = None
    try:
        if new_server_info['_telepath_data']:
            telepath_data = new_server_info['_telepath_data']
    except KeyError:
        pass

    if telepath_data and not telepath:
        new_info = deepcopy(new_server_info)
        new_info['acl_object'] = new_server_info['acl_object']._to_json()

        api_manager.request(
            endpoint='/create/push_new_server',
            host=telepath_data['host'],
            port=telepath_data['port'],
            args={'server_info': new_info}
        )
        response = api_manager.request(
            endpoint='/create/pre_server_create',
            host=telepath_data['host'],
            port=telepath_data['port'],
            args={'telepath': True}
        )
        return response

    server_manager.current_server = None

    # First, clean out any existing server in temp folder
    safe_delete(tmpsvr)
    folder_check(tmpsvr)
def post_server_create(telepath=False):
    telepath_data = None
    try:
        if new_server_info['_telepath_data']:
            telepath_data = new_server_info['_telepath_data']
    except KeyError:
        pass

    if telepath_data and not telepath:
        new_server_init()
        api_manager.request(
            endpoint='/create/push_new_server',
            host=telepath_data['host'],
            port=telepath_data['port'],
            args={'server_info': new_server_info}
        )
        response = api_manager.request(
            endpoint='/create/post_server_create',
            host=telepath_data['host'],
            port=telepath_data['port'],
            args={'telepath': True}
        )
        return response


# Configures server via server info in a variety of ways (for updates)
def update_server_files(progress_func=None):

    # If telepath, do all of this remotely
    telepath_data = None
    if server_manager.current_server:
        telepath_data = server_manager.current_server._telepath_data

    try:
        if not telepath_data and new_server_info['_telepath_data']:
            telepath_data = new_server_info['_telepath_data']
    except KeyError:
        pass

    if telepath_data:
        response = api_manager.request(
            endpoint='/create/update_server_files',
            host=telepath_data['host'],
            port=telepath_data['port'],
            args={}
        )
        if progress_func and response:
            progress_func(100)
        return response


    print(glob(os.path.join(tmpsvr, '*')))
    new_config_path = os.path.join(tmpsvr, server_ini)

    # First, generate startup script
    generate_run_script(new_server_info, temp_server=True)
    path = server_path(new_server_info['name'])


    # Edit auto-mcs.ini
    config_file = server_config(new_server_info['name'])
    config_file.set("general", "serverType", new_server_info['type'])
    config_file.set("general", "serverVersion", new_server_info['version'])
    if new_server_info['build']:
        config_file.set("general", "serverBuild", str(new_server_info['build']))
    server_config(new_server_info['name'], config_file, new_config_path)


    # Copy over EULA.txt
    def copy_eula(eula_path):
        if os.path.exists(eula_path):
            copy(eula_path, os.path.join(tmpsvr, 'eula.txt'))
            return True
    if not copy_eula(os.path.join(path, 'eula.txt')):
        if not copy_eula(os.path.join(path, 'EULA.txt')):
            copy_eula(os.path.join(path, 'EULA.txt'))

    # Copy server.properties back after it gets DELETED
    if not os.path.exists(os.path.join(tmpsvr, 'server.properties')) and os.path.exists(os.path.join(path, 'server.properties')):
        copy(os.path.join(path, 'server.properties'), os.path.join(tmpsvr, 'server.properties'))


    # Check if everything was created successfully
    if (os.path.exists(os.path.join(tmpsvr, 'server.properties')) and os.path.exists(new_config_path) and os.path.exists(os.path.join(tmpsvr, 'eula.txt'))):

        # Replace server path with tmpsvr
        new_path = os.path.join(serverDir, new_server_info['name'])
        safe_delete(new_path)
        copytree(tmpsvr, new_path, dirs_exist_ok=True)
        safe_delete(tempDir)
        safe_delete(downDir)

        if os_name == "windows":
            run_proc(f"attrib +H \"{os.path.join(new_path, server_ini)}\"")

        return True
def pre_server_update(telepath=False):
    global new_server_info
    server_obj = server_manager.current_server

    if telepath:
        server_obj = server_manager.remote_server

    # If remote, do this through telepath
    else:
        telepath_data = server_obj._telepath_data
        if telepath_data:
            response = api_manager.request(
                endpoint='/create/pre_server_update',
                host=telepath_data['host'],
                port=telepath_data['port'],
                args={'telepath': True}
            )
            return response


    # First, clean out any existing server in temp folder
    safe_delete(tmpsvr)

    # Copy over existing server and remove the files which will be replaced
    copytree(server_obj.server_path, tmpsvr)
    for jar in glob(os.path.join(tmpsvr, '*.jar')):
        os.remove(jar)

    safe_delete(os.path.join(tmpsvr, 'addons'))
    safe_delete(os.path.join(tmpsvr, 'disabled-addons'))
    safe_delete(os.path.join(tmpsvr, 'mods'))
    safe_delete(os.path.join(tmpsvr, 'disabled-mods'))

    # Delete EULA.txt
    def delete_eula(eula_path):
        if os.path.exists(eula_path):
            os.remove(eula_path)

    delete_eula(os.path.join(tmpsvr, 'eula.txt'))
    delete_eula(os.path.join(tmpsvr, 'EULA.txt'))
    delete_eula(os.path.join(tmpsvr, 'EULA.TXT'))
def post_server_update(telepath=False):
    global new_server_info
    server_obj = server_manager.current_server

    if telepath:
        server_obj = server_manager.remote_server

    # If remote, do this through telepath
    else:
        telepath_data = server_obj._telepath_data
        if telepath_data:
            response = api_manager.request(
                endpoint='/create/post_server_update',
                host=telepath_data['host'],
                port=telepath_data['port'],
                args={'telepath': True}
            )
            return response

    make_update_list()
    server_obj._view_notif('add-ons', False)
    server_obj._view_notif('settings', viewed=new_server_info['version'])

    new_server_info = {}


# Create initial backup of new server
# For existing servers, use server_manager.current_server.backup.save()
def create_backup(import_server=False, *args):

    # If telepath, check if Java is installed remotely
    telepath_data = None
    if server_manager.current_server:
        telepath_data = server_manager.current_server._telepath_data

    try:
        if not telepath_data and new_server_info['_telepath_data']:
            telepath_data = new_server_info['_telepath_data']
    except KeyError:
        pass

    if telepath_data:
        response = api_manager.request(
            endpoint='/create/create_backup',
            host=telepath_data['host'],
            port=telepath_data['port'],
            args={'import_server': import_server}
        )
        return response


    backup.BackupManager(new_server_info['name'] if not import_server else import_data['name']).save()
    return True


# Restore backup and track progress for ServerBackupRestoreProgressScreen
def restore_server(backup_obj: backup.BackupObject, progress_func=None):

    # Restore a remote backup
    if 'RemoteBackupObject' in backup_obj.__class__.__name__:
        success = server_manager.current_server.backup.restore(backup_obj)
        if progress_func:
            progress_func(100)
        return success


    # Get file count of backup
    total_files = 0
    proc_complete = False
    file_path = backup_obj.path
    server_name = server_manager.current_server.name
    file_name = os.path.basename(file_path)

    server_manager.current_server.backup._restore_file = None

    with tarfile.open(file_path) as archive:
        total_files = sum(1 for member in archive if member.isreg())

    def thread_checker():
        while not proc_complete:
            time.sleep(0.5)
            current_count = 0
            for path, dir_count, file_count in os.walk(server_path(server_name)):
                current_count += len(file_count)

            percent = round((current_count/total_files) * 100)
            progress_func(percent)

        print("Done!")

    thread_check = threading.Timer(0, thread_checker)
    thread_check.daemon = True
    thread_check.start()

    server_manager.current_server.backup.restore(backup_obj)
    proc_complete = True

    if progress_func:
        progress_func(100)

    return True



# Import Server stuffies

# Figures out type and version of server. Returns information to import_data dict
# There will be issues importing 1.17.0 bukkit derivatives due to Java 16 requirement
def scan_import(bkup_file=False, progress_func=None, *args):
    name = import_data['name']
    path = import_data['path']

    cwd = get_cwd()
    folder_check(tmpsvr)
    os.chdir(tmpsvr)

    import_data['config_file'] = None
    import_data['type'] = None
    import_data['version'] = None
    import_data['build'] = None

    file_name = None


    # If import is from a back-up
    if bkup_file:
        run_proc(f'tar -xvf "{path}"')

        if progress_func:
            progress_func(50)

        # Delete all startup scripts in directory
        for script in glob(os.path.join(tmpsvr, "*.bat"), recursive=False):
            os.remove(script)
        for script in glob(os.path.join(tmpsvr, "*.sh"), recursive=False):
            os.remove(script)

        # Extract info from auto-mcs.ini
        config_file = server_config(server_name=None, config_path=glob(os.path.join(tmpsvr, "*auto-mcs.ini"))[0])
        import_data['version'] = config_file.get('general', 'serverVersion').lower()
        import_data['type'] = config_file.get('general', 'serverType').lower()
        try:
            import_data['build'] = str(config_file.get('general', 'serverBuild'))
        except:
            pass
        try:
            import_data['launch_flags'] = str(config_file.get('general', 'customFlags'))
        except:
            pass
        import_data['config_file'] = config_file

        # Then delete it for later
        for item in glob(os.path.join(tmpsvr, "*auto-mcs.ini"), recursive=False):
            os.remove(item)



    # Try to determine arbitrary server type and version
    else:
        test_server = os.path.join(tempDir, 'importtest')
        folder_check(test_server)
        os.chdir(test_server)


        # Generate script list and iterate through each one
        script_list = glob(os.path.join(str(path), "*.bat"))
        script_list.extend(glob(os.path.join(str(path), "*.sh")))


        # If no startup scripts were found, generate a temp script for each .jar file
        if not script_list:
            jar_list = glob(os.path.join(str(path), '*.jar'))
            if jar_list:
                for jar in sorted(jar_list, key=lambda x: os.path.getsize(x)):
                    folder_check(tempDir)
                    jar_name = os.path.basename(jar)
                    script_name = os.path.join(tempDir, jar_name + '.bat')
                    with open(script_name, 'w+') as f:
                        f.write(f'java -jar {jar_name}')
                    script_list.append(script_name)


        # First, check for any run scripts to see if the .jar is contained within
        for file in script_list:

            # Find server jar name
            with open(file, 'r') as f:
                output = f.read()
                raw_output = output
                f.close()
                start_script = False

                if "-jar" in output and ".jar" in output:
                    start_script = True
                    file_name = re.search(r'\S+(?=\.jar)', output).group(0)

                    # copy jar file to test directory
                    copy(os.path.join(str(path), f'{file_name}.jar'), test_server)


                    # Check if server.jar is a valid server
                    run_proc(f'"{java_executable["jar"]}" -xf {file_name}.jar META-INF/MANIFEST.MF')
                    run_proc(f'"{java_executable["jar"]}" -xf {file_name}.jar META-INF/versions.list')

                    with open(os.path.join(test_server, 'META-INF', 'MANIFEST.MF'), 'r') as f:
                        output = f.read()

                        version_output = ""
                        if os.path.exists(os.path.join(test_server, 'META-INF', 'versions.list')):
                            with open(os.path.join(test_server, 'META-INF', 'versions.list'), 'r') as f:
                                version_output = f.read()


                        # Fabric keywords
                        if "fabricinstaller" in output.lower() or "net.fabricmc" in output.lower():
                            import_data['type'] = "fabric"

                        # Forge keywords
                        elif "modloader" in output.lower() or "forge" in output.lower() or "fml" in output.lower():
                            import_data['type'] = "forge"

                        # Purpur keywords
                        elif "purpur" in version_output.lower():
                            import_data['type'] = "purpur"

                        # Paper keywords
                        elif "paperclip" in output.lower():
                            import_data['type'] = "paper"

                            # Grab build info
                            if os.path.exists(os.path.join(str(path), 'version_history.json')):
                                try:
                                    with open(os.path.join(str(path), 'version_history.json'), 'r') as f:
                                        import_data['build'] = str(json.load(f)['currentVersion'].lower().split('paper-')[1].split(' ')[0].strip())
                                except:
                                    pass

                        # Spigot keywords
                        elif "spigot" in output.lower() or "spigot" in version_output.lower():
                            import_data['type'] = "spigot"

                        # Spigot keywords
                        elif "craftbukkit" in output.lower():
                            import_data['type'] = "craftbukkit"

                        # Vanilla keywords
                        elif "net.minecraft.server.minecraftserver" in output.lower() or "net.minecraft.server.main" in output.lower() or "net.minecraft.bundler.main" in output.lower():
                            import_data['type'] = "vanilla"

                    # Check for server version
                    if not import_data['version']:

                        if progress_func:
                            progress_func(50)

                        ram = calculate_ram(import_data)
                        print(f"Determined type '{import_data['type']}':  validating version information...")

                        if import_data['type'] == "forge":
                            copy_to(os.path.join(str(path), 'libraries'), test_server, 'libraries', True)
                            for jar in glob(os.path.join(str(path), 'minecraft_server*.jar')):
                                copy(jar, test_server)

                        if file_name != "server":
                            if os.path.exists("server.jar"):
                                os.remove("server.jar")
                            run_proc(f"{'move' if os_name == 'windows' else 'mv'} {file_name}.jar server.jar")

                        time_stamp = datetime.date.today().strftime(f"#%a %b %d ") + datetime.datetime.now().strftime("%H:%M:%S ") + "MCS" + datetime.date.today().strftime(f" %Y")

                        eula = f"""#By changing the setting below to TRUE you are indicating your agreement to our EULA (https://account.mojang.com/documents/minecraft_eula).
{time_stamp}
eula=true"""

                        # EULA
                        with open(f"eula.txt", "w+") as f:
                            f.write(eula)

                        # Run legacy version of java
                        if import_data['type'] == "forge":
                            server = subprocess.Popen(f"\"{java_executable['legacy']}\" -Xmx{ram}G -Xms{int(round(ram/2))}G -jar server.jar nogui", stdout=subprocess.DEVNULL, shell=True)

                        # Run latest version of java
                        else:
                            # If paper, copy pre-downloaded vanilla .jar files if they exist
                            if import_data['type'] in ["paper", "purpur"]:
                                copy_to(os.path.join(str(path), 'cache'), test_server, 'cache', True)

                            server = subprocess.Popen(f"\"{java_executable['modern']}\" -Xmx{ram}G -Xms{int(round(ram/2))}G -jar server.jar nogui", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)

                        found_version = False
                        timeout = 0

                        while found_version is False:
                            time.sleep(1)
                            timeout += 1
                            output = ""

                            # Read modern logs
                            if os.path.exists(os.path.join(test_server, 'logs', 'latest.log')):
                                with open(os.path.join(test_server, 'logs', 'latest.log'), 'r') as f:
                                    output = f.read()

                            # Read legacy logs
                            elif os.path.exists(os.path.join(test_server, 'server.log')):
                                with open(os.path.join(test_server, 'server.log'), 'r') as f:
                                    output = f.read()

                            if "starting minecraft server version" in output.lower():
                                found_version = True
                                if os_name == 'windows':
                                    run_proc(f"taskkill /F /T /PID {server.pid}")
                                else:
                                    run_proc(f"kill -9 {server.pid}")
                                server.kill()

                                for line in output.split("\n"):
                                    if "starting minecraft server version" in line.lower():
                                        import_data['version'] = line.split("version ")[1].replace("Beta ", "b").replace("Alpha ", "a")
                                break

                            if (timeout > 200) or (server.poll() is not None):
                                if os_name == 'windows':
                                    run_proc(f"taskkill /F /T /PID {server.pid}")
                                else:
                                    run_proc(f"kill -9 {server.pid}")
                                server.kill()
                                break

                # New versions of forge
                elif "@libraries/net/minecraftforge/forge/" in output:
                    start_script = True

                    version = output.split("@libraries/net/minecraftforge/forge/")[1].split("-")[0]

                    version_list = []

                    for forge_file in glob(os.path.join(str(path), 'libraries', 'net', 'minecraftforge', 'forge', f'{version}*')):
                        version_list.append(os.path.basename(forge_file))

                        if version_list != 0:
                            print(f"Determined type '{import_data['type']}':  validating version information...")

                            import_data['type'] = "forge"
                            import_data['version'] = version_list[0].split("-")[0].lower()
                            import_data['build'] = str(version_list[0].split("-")[1])
                            break


                # Gather launch flags
                if start_script:
                    if 'launch_flags' not in import_data.keys():
                        import_data['launch_flags'] = []
                    def process_flags(flags):
                        if (flags.startswith('"') and flags.endswith('"')) or (flags.startswith("'") and flags.endswith("'")):
                            flags = flags[1:-1]

                        for flag in flags.split(' '):

                            # Clean up flags
                            for qt in ['"', "'"]:
                                if flag.startswith(qt):
                                    flag = flag[1:]
                                if flag.endswith(qt):
                                    flag = flag[:-1]

                            # Ignore flags with invalid data
                            if "%" in flag or "${" in flag or '-Xmx' in flag or '-Xms' in flag or len(flag) < 5:
                                continue
                            for exclude in ['-install', '-server', '-jar', '--nogui', '-nogui', '-Command', '-fullversion', '-version']:
                                if exclude in flag:
                                    break

                            else:
                                # Add flag to final data
                                if flag.strip() not in import_data['launch_flags'] and flag.strip():
                                    import_data['launch_flags'].append(flag.strip())
                    for match in re.findall(r'(?<= |=)--?\S+', raw_output):
                        process_flags(match)


            # Import files and such
            if import_data['type'] and import_data['version']:

                if progress_func:
                    progress_func(80)

                safe_delete(tmpsvr)
                try:
                    os.rmdir(tmpsvr)
                except FileNotFoundError:
                    pass
                except PermissionError:
                    pass
                copy_to(str(path), tempDir, os.path.basename(tmpsvr))

                # Delete all startup scripts in directory
                for script in glob(os.path.join(tmpsvr, "*.bat"), recursive=False):
                    os.remove(script)
                for script in glob(os.path.join(tmpsvr, "*.sh"), recursive=False):
                    os.remove(script)

                # Delete all *.jar files in directory
                for jar in glob(os.path.join(str(path), '*.jar'), recursive=False):
                    if not ((jar.startswith('minecraft_server') and import_data['type'] == 'forge') or (file_name in jar)):
                        os.remove(jar)

                    # Rename actual .jar file to server.jar to prevent crashes
                    if file_name in jar:
                        run_proc(f"{'move' if os_name == 'windows' else 'mv'} \"{os.path.join(tmpsvr, os.path.basename(jar))}\" \"{os.path.join(tmpsvr, 'server.jar')}\"")


    # print(import_data)
    os.chdir(cwd)
    if import_data['type'] and import_data['version']:

        # Regenerate auto-mcs.ini
        # print(import_data)
        config_file = create_server_config(import_data, True)

        # Sanitize values from old versions of auto-mcs
        if import_data['config_file']:

            try:
                config_file.set('general', 'isFavorite', str(import_data['config_file'].get('general', 'isFavorite')).lower())
            except configparser.NoOptionError:
                pass

            try:
                config_file.set('general', 'updateAuto', str(import_data['config_file'].get('general', 'updateAuto')).lower())
            except configparser.NoOptionError:
                pass

            try:
                config_file.set('general', 'allocatedMemory', str(import_data['config_file'].get('general', 'allocatedMemory')).lower())
            except configparser.NoOptionError:
                pass

            try:
                config_file.set('general', 'customFlags', str(import_data['config_file'].get('general', 'customFlags')).lower())
            except configparser.NoOptionError:
                pass

            try:
                config_file.set('bkup', 'bkupAuto', str(import_data['config_file'].get('bkup', 'bkupAuto')).lower())
            except configparser.NoOptionError:
                pass

            try:
                config_file.set('bkup', 'bkupMax', str(import_data['config_file'].get('bkup', 'bkupMax')).lower())
            except configparser.NoOptionError:
                pass

            backup_dir = backupFolder
            try:
                if os.path.isdir(str(import_data['config_file'].get('bkup', 'bkupMax'))):
                    backup_dir = str(import_data['config_file'].get('bkup', 'bkupMax'))
            except configparser.NoOptionError:
                pass

            config_file.set('bkup', 'bkupDir', backup_dir)

            # Delete auto-mcs.ini again
            for item in glob(os.path.join(tmpsvr, "*auto-mcs.ini"), recursive=False):
                os.remove(item)

            # Write file to path
            config_path = os.path.join(tmpsvr, server_ini)

            with open(config_path, 'w') as f:
                config_file.write(f)

            if os_name == "windows":
                run_proc(f"attrib +H \"{config_path}\"")

        # Find command temp if it exists
        for item in glob(os.path.join(tmpsvr, "*start-cmd.tmp")):
            try:
                os.rename(item, command_tmp)
            except FileExistsError:
                pass

        if os_name == "windows" and os.path.exists(os.path.join(tmpsvr, command_tmp)):
            run_proc(f"attrib +H \"{os.path.join(tmpsvr, command_tmp)}\"")

        # Generate startup script
        generate_run_script(import_data, temp_server=True)


        if os.path.exists(os.path.join(tmpsvr, server_ini)):
            if progress_func:
                progress_func(100)
            return True


# Moves tmpsvr to actual server and checks for ACL and other file validity
def finalize_import(progress_func=None, *args):
    global import_data

    if import_data['name']:

        # Copy folder to server path and delete tmpsvr
        new_path = os.path.join(serverDir, import_data['name'])
        copytree(tmpsvr, new_path, dirs_exist_ok=True)
        safe_delete(tempDir)
        safe_delete(downDir)

        if progress_func:
            progress_func(33)


        # Add global rules to ACL
        from acl import AclManager
        AclManager(import_data['name']).write_rules()

        if progress_func:
            progress_func(66)


        # Check for EULA
        if not (server_path(import_data['name'], 'eula.txt') or server_path(import_data['name'], 'EULA.txt')):
            time_stamp = datetime.date.today().strftime(f"#%a %b %d ") + datetime.datetime.now().strftime("%H:%M:%S ") + "MCS" + datetime.date.today().strftime(f" %Y")

            # Generate EULA.txt
            eula = f"""#By changing the setting below to TRUE you are indicating your agreement to our EULA (https://account.mojang.com/documents/minecraft_eula).
{time_stamp}
eula=true"""

            with open(os.path.join(server_path(import_data['name']), 'eula.txt'), 'w+') as f:
                f.write(eula)

            if server_path(import_data['name'], 'server.properties'):
                content = []
                with open(os.path.join(server_path(import_data['name']), 'server.properties'), 'r') as f:
                    content = f.readlines()
                    edited = False
                    if len(content) >= 1:
                        if content[1].startswith('#'):
                            content[1] = f"#{time_stamp}\n"
                            edited = True
                    if not edited:
                        content.insert(0, f"#{time_stamp}\n")
                        content.insert(0, "#Minecraft server properties\n")

                with open(os.path.join(server_path(import_data['name']), 'server.properties'), 'w+') as f:
                    f.writelines(content)
            else:
                fix_empty_properties(import_data['name'])


        if os_name == "windows":

            if server_path(import_data['name'], '.auto-mcs.ini'):
                os.remove(server_path(import_data['name'], '.auto-mcs.ini'))

            if server_path(import_data['name'], '.start-cmd.tmp'):
                os.rename(server_path(import_data['name'], '.start-cmd.tmp'), os.path.join(server_path(import_data['name']), command_tmp))

            run_proc(f"attrib +H \"{server_path(import_data['name'], server_ini)}\"")
            if server_path(import_data['name'], command_tmp):
                run_proc(f"attrib +H \"{server_path(import_data['name'], command_tmp)}\"")

        else:
            if server_path(import_data['name'], 'auto-mcs.ini'):
                os.remove(server_path(import_data['name'], 'auto-mcs.ini'))

            if server_path(import_data['name'], 'start-cmd.tmp'):
                os.rename(server_path(import_data['name'], 'start-cmd.tmp'), os.path.join(server_path(import_data['name']), command_tmp))


        if server_path(import_data['name'], server_ini):
            safe_delete(tempDir)
            safe_delete(downDir)
            make_update_list()
            if progress_func:
                progress_func(100)
            return True


# Imports a modpack from a .zip file
def scan_modpack(update=False, progress_func=None):
    global import_data

    # First, download modpack if it's a URL
    try:
        url = import_data['url']
    except KeyError:
        file_path = import_data['path']
    else:
        file_path = import_data['path'] = download_url(url, f"{sanitize_name(import_data['name'])}.{url.rsplit('.',1)[-1]}", downDir)


    # Test archive first
    if not os.path.isfile(file_path) or file_path.split('.')[-1] not in ['zip', 'mrpack']:
        return False

    # Set up directory structures and extract the modpack
    cwd = get_cwd()
    folder_check(tmpsvr)
    os.chdir(tmpsvr)

    test_server = os.path.join(tempDir, 'importtest')
    folder_check(test_server)
    os.chdir(test_server)

    extract_archive(file_path, test_server)
    move_files_root(test_server)

    if progress_func:
        progress_func(50)


    # Clean-up name
    def process_name(name):

        # First, sanitize the name of encoded data and irrelevant characters
        name = name.encode('ascii').decode('unicode_escape')
        name = re.sub(r'§\S', '', name).replace('\\', '')
        name = re.sub(r'v?\d+(\.?\d+)+\w?', '', name)
        name = re.sub(r'fabric|forge|modpack', '', name, flags=re.IGNORECASE)
        name = re.sub('[^a-zA-Z0-9 .\']', '', name).strip()
        name = re.sub(r'\s+',' ', name)

        if name:

            # Filter words in the title
            articles = ('a', 'an', 'the', 'and', 'of', 'with', 'in', 'for')
            name = ' '.join([w for w in name.split(' ') if (w[0].isupper() or w[0].isdigit() or w in articles)]).strip()

            data['name'] = name

        return name

    # Clean-up launch flags
    def process_flags(flags):
        if (flags.startswith('"') and flags.endswith('"')) or (flags.startswith("'") and flags.endswith("'")):
            flags = flags[1:-1]

        for flag in flags.split(' '):

            # Clean up flags
            for qt in ['"', "'"]:
                if flag.startswith(qt):
                    flag = flag[1:]
                if flag.endswith(qt):
                    flag = flag[:-1]

            # Ignore flags with invalid data
            if "%" in flag or "${" in flag or '-Xmx' in flag or '-Xms' in flag or len(flag) < 5:
                continue
            for exclude in ['-install', '-server', '-jar', '--nogui', '-nogui', '-Command', '-fullversion', '-version']:
                if exclude in flag:
                    break

            else:
                # Add flag to final data
                if flag.strip() not in data['launch_flags'] and flag.strip():
                    data['launch_flags'].append(flag.strip())


    data = {
        'name': None,
        'type': None,
        'version': None,
        'build': None,
        'launch_flags': [],
        'pack_type': 'zip'
    }

    if import_data['name'] and not update:
        data['name'] = new_server_name(process_name(import_data['name']))


    # Approach #1: Look for "modrinth.index.json"
    if file_path.endswith('.mrpack'):
        data['pack_type'] = 'mrpack'
        mr_index = os.path.join(test_server, 'modrinth.index.json')
        if os.path.isfile(mr_index):
            with open(mr_index, 'r') as f:

                # Reorganize .json for ease of iteration
                metadata = [
                    {
                        'url':i['downloads'][0],
                        'file_name':os.path.basename(i['path']),
                        'destination':os.path.join(test_server, os.path.dirname(i['path']))
                    }
                    for i in json.loads(f.read())["files"]
                ]

                def get_mod_url(mod_data):
                    try:
                        return cs_download_url(mod_data['url'], mod_data['file_name'], mod_data['destination'])
                    except Exception as e:
                        return False

                # Iterate over additional content to see if it's available to be downloaded
                with ThreadPoolExecutor(max_workers=20) as pool:
                    for result in pool.map(get_mod_url, metadata):
                        if not result:
                            return result


    # Approach #2: look for "ServerStarter"
    server_starter = False
    yaml_list = []
    for file in glob(os.path.join(test_server, '*.*')):
        with open(file, 'r', encoding='utf-8', errors='ignore') as f:
            text_content = f.read()
            file_name = os.path.basename(file)
            if 'serverstarter' in text_content.lower() or 'serverstarter' in file_name.lower():
                server_starter = True
            if file_name.rsplit('.', 1)[1] in ['yml', 'yaml']:
                try:
                    yaml_list.append(text_content)
                except:
                    pass
    if server_starter and yaml_list:
        for raw_content in yaml_list:
            content = yaml.safe_load(raw_content)
            if 'modpack' in content.keys() and '_specver' in content.keys():
                data['name'] = content['modpack']['name']
                data['version'] = content['install']['mcVersion']
                data['build'] = content['install']['loaderVersion']
                data['launch_flags'] = content['launch']['javaArgs']

                matches = {'forge': 0, 'fabric': 0}
                matches['forge'] += len(re.findall(r'\bforge\b', raw_content, re.IGNORECASE))
                matches['fabric'] += len(re.findall(r'\bfabric\b', raw_content, re.IGNORECASE))
                data['type'] = 'fabric' if matches['fabric'] > matches['forge'] else 'forge'

                # Install additional content if required
                try:
                    if content['install']['modpackUrl']:
                        url = content['install']['modpackUrl']
                        additional_extract = os.path.join(tempDir, 'additional_extract')
                        additional = os.path.join(test_server, 'modpack_additional.zip')

                        # Download additional content defined in the .yaml
                        if cs_download_url(url, os.path.basename(additional), test_server):
                            folder_check(additional_extract)
                            extract_archive(additional, additional_extract)
                            move_files_root(additional_extract, test_server)

                            # Download mods from "manifest.json"
                            mod_dict = os.path.join(additional_extract, 'manifest.json')

                            if os.path.isfile(mod_dict):
                                with open(mod_dict, 'r') as f:
                                    metadata = json.loads(f.read())

                                    def get_mod_url(mod_data):
                                        destination = os.path.join(test_server, 'mods')
                                        mod_name = None
                                        mod_url = None

                                        # If URL is provided
                                        try:
                                            if mod_data['downloadUrl']:
                                                if mod_data['downloadUrl'].endswith('.jar'):
                                                    mod_name = sanitize_name(
                                                        mod_data['downloadUrl'].rsplit('/', 1)[-1])[:-3] + '.jar'
                                                else:
                                                    mod_name = mod_data['downloadUrl'].rsplit('/', 1)[-1]
                                                mod_url = mod_data['downloadUrl']
                                        except KeyError:
                                            pass

                                        if mod_name and mod_url:
                                            return cs_download_url(mod_url, mod_name, destination)
                                        else:
                                            return False

                                    # Iterate over additional content to see if it's available to be downloaded
                                    with ThreadPoolExecutor(max_workers=20) as pool:
                                        for result in pool.map(get_mod_url, metadata['files']):
                                            if not result:
                                                return result

                except KeyError:
                    pass

    # Approach #3: inspect "variables.txt"
    if os.path.exists('variables.txt'):
        with open('variables.txt', 'r', encoding='utf-8', errors='ignore') as f:
            variables = {}
            for line in f.readlines():
                if '=' in line:
                    key, value = line.split('=', 1)
                    variables[key.lower()] = value.replace('\n','')
            data['version'] = variables['minecraft_version'].strip()
            data['build'] = variables['modloader_version'].strip()
            data['type'] = variables['modloader'].lower().strip()
            process_flags(variables['java_args'])

    # Approach #4: inspect launch scripts and server.jar
    if not data['version'] or not data['type']:

        # Generate script list and iterate through each one
        file_list = glob(os.path.join(str(test_server), "*.bat"))
        file_list.extend(glob(os.path.join(str(test_server), "*.sh")))
        jar_exists_name_fail = False

        # First, search through all the scripts to find the type, version, and launch flags
        for file in file_list:

            # Find server jar name
            with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                output = f.read()
                f.close()

                # Reformat variables set in config files (Forge)
                for match in re.findall(r'forge.*\.jar', output):
                    if '$' in match or '%' in match:
                        jar_exists_name_fail = True
                        continue

                    split_match = match.split('-')
                    if len(split_match) >= 3:
                        jar_exists_name_fail = False
                        data['version'] = split_match[1]
                        data['type'] = 'forge'
                        data['build'] = split_match[2].replace('.jar','')
                        break

                # Reformat variables set in config files (Fabric)
                for match in re.findall(r'fabric.*\.jar', output):
                    if '$' in match or '%' in match:
                        jar_exists_name_fail = True
                        continue

                    split_match = match.split('-')
                    if len(split_match) >= 3:
                        jar_exists_name_fail = False
                        data['version'] = split_match[2].replace('mc.','')
                        data['type'] = 'fabric'
                        data['build'] = split_match[3].replace('loader.','')
                        break

                # Gather launch flags
                for match in re.findall(r'(?<= |=)--?\S+', output):
                    process_flags(match)


        # If a file exists but the name could not be determined, look for it manually
        if jar_exists_name_fail:

            # Reformat variables set in config files (Forge)
            for match in glob(os.path.join(test_server, 'forge-*.jar')):
                split_match = os.path.basename(match).split('-')
                if len(split_match) >= 3:
                    data['version'] = split_match[1]
                    data['type'] = 'forge'
                    data['build'] = split_match[2].replace('.jar', '')
                    break

            # Reformat variables set in config files (Fabric)
            for match in glob(os.path.join(test_server, 'fabric-*.jar')):
                split_match = os.path.basename(match).split('-')
                if len(split_match) >= 3:
                    data['version'] = split_match[2].replace('mc.', '')
                    data['type'] = 'fabric'
                    data['build'] = split_match[3].replace('loader.', '')
                    break

    # Approach #3: inspect server files
    if not data['version'] or not data['type']:

        # Generate script list and iterate through each one
        file_list = glob(os.path.join(test_server, "*.txt"))
        if os.path.exists(os.path.join(test_server, 'scripts')):
            file_list = glob(os.path.join(test_server, "scripts", "*.*"))
        if os.path.exists(os.path.join(test_server, 'config')):
            file_list.extend(glob(os.path.join(test_server, "config", "*.*")))

        matches = {
            'forge': 0,
            'fabric': 0,
            'versions': []
        }

        def process_matches(content):
            matches['forge'] += len(re.findall(r'\bforge\b', content, re.IGNORECASE))
            matches['fabric'] += len(re.findall(r'\bfabric\b', content, re.IGNORECASE))
            matches['versions'].extend(re.findall(r'(?<!\d.)1\.\d\d?\.\d\d?(?!\.\d+)\b', content))

        # First, search through all the files to find the type, version, and launch flags
        for file in file_list:

            # Find server jar name
            with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                output = f.read()
                f.close()
                process_matches(output)
                process_matches(os.path.basename(file))

        process_matches(os.path.basename(file_path))

        # Second, search through all the mod names to more accurately determine the MC version
        if os.path.exists(os.path.join(test_server, 'mods')):
            for mod in glob(os.path.join(test_server, "mods", "*.jar")):
                process_matches(os.path.basename(mod))

        data['type'] = 'fabric' if matches['fabric'] > matches['forge'] else 'forge'
        if matches['versions']:
            data['version'] = max(set(matches['versions']), key=matches['versions'].count)


    # Get the modpack name
    if not data['name']:

        # Get the name from "server.properties"
        if os.path.isfile('server.properties'):
            with open('server.properties', 'r', encoding='utf-8', errors='ignore') as f:
                for line in f.readlines():
                    if line.lower().startswith('motd='):
                        line = line.split('motd=', 1)[1]
                        process_name(line)
                        break

        # Get the name from the file if not declared in the "server.properties"
        if not data['name'] or data['name'].lower() == 'a minecraft server':
            name = os.path.basename(file_path).rsplit('.',1)[0]
            name = re.sub(r'(?<=\S)(-|_|\+)(?=\S)', ' ', name)
            if 'server' in name.lower():
                name = name[:len(name.lower().split('server')[0])].strip()
            process_name(name)

    # Look in alternate locations for launch flags
    for file in glob(os.path.join(test_server, '*.*')):
        for key in ['jvm', 'args', 'arguments', 'param']:
            if key in os.path.basename(file):
                with open(file, 'r') as f:
                    text = f.read()
                    for match in re.findall(r'(?<= |=|\n)--?\S+', text):
                        process_flags(match)
                    break


    if data['type'] and data['version'] and data['name']:
        import_data = {
            'name': data['name'],
            'path': import_data['path'],
            'type': data['type'],
            'version': data['version'],
            'build': data['build'],
            'launch_flags': data['launch_flags'],
            'pack_type': data['pack_type']
        }

        if progress_func:
            progress_func(100)

        return data
    else:
        return False


# Moves tmpsvr to actual server and checks for ACL and other file validity
def finalize_modpack(update=False, progress_func=None, *args):
    global import_data

    test_server = os.path.join(tempDir, 'importtest')

    if import_data['name'] and os.path.exists(test_server):

        # Finish migrating data to tmpsvr
        for item in glob(os.path.join(test_server, '*')):
            file_name = os.path.basename(item)
            if os.path.isdir(item) or (os.path.isfile(item) and (file_name.endswith('.txt') or file_name.endswith('.png') or file_name.endswith('.yml') or file_name.endswith('.json') or file_name in ['server.properties'])):

                # Scale and migrate image for "server-icon.png", if one is not provided
                if file_name.lower() == 'icon.png' and not os.path.exists(os.path.join(tmpsvr, 'server-icon.png')):
                    try:
                        im = Image.open(file_name)
                        im.thumbnail((64, 64), Image.LANCZOS)
                        im.save(os.path.join(tmpsvr, 'server-icon.png'), 'png')
                    except IOError:
                        print("Error: can't create thumbnail for server icon")
                    continue

                elif file_name == 'server-icon.png':
                    copy(item, tmpsvr)
                    continue

                elif file_name == 'modrinth.index.json':
                    copy(item, tmpsvr)
                    if os_name == 'windows':
                        run_proc(f"attrib +H \"{os.path.join(tmpsvr, 'modrinth.index.json')}\"")
                    else:
                        os.rename(os.path.join(tmpsvr, 'modrinth.index.json'), os.path.join(tmpsvr, '.modrinth.index.json'))
                    continue

                elif file_name.endswith('.png'):
                    continue

                if file_name.lower() == 'eula.txt':
                    continue

                # Recursively copy folders, and simply copy files
                if os.path.isdir(item):
                    copytree(item, os.path.join(tmpsvr, file_name), dirs_exist_ok=True)
                else:
                    copy(item, tmpsvr)


        # Copy existing data from modpack if updating
        new_path = os.path.join(serverDir, import_data['name'])
        if update and os.path.isdir(new_path):
            valid_files = ['server.properties', 'eula.txt', 'auto-mcs.ini', '.auto-mcs.ini', 'start-cmd.tmp']
            for item in glob(os.path.join(new_path, '*')):
                file_name = os.path.basename(item)
                if os.path.isdir(item) or (os.path.isfile(item) and (file_name.endswith('.txt') or file_name.endswith('.yml') or file_name.endswith('.json') or file_name in valid_files)):
                    if file_name == 'modrinth.index.json':
                        continue

                    elif os.path.isdir(item) and file_name in ['mods', 'config', 'versions', 'libraries', 'resources', '.fabric']:
                        continue

                    # Recursively copy folders, and simply copy files
                    if os.path.isdir(item):
                        copytree(item, os.path.join(tmpsvr, file_name), dirs_exist_ok=True)
                    else:
                        copy(item, tmpsvr)


        # Create auto-mcs.ini
        if update and os.path.isfile(os.path.join(new_path, server_ini)):
            new_config = server_config(import_data['name'])
            new_config.set('general', 'serverVersion', import_data['version'])
            if import_data['build']:
                new_config.set('general', 'serverBuild', str(import_data['build']))
            try:
                new_config.set('general', 'customFlags', ' '.join(import_data['launch_flags']))
            except:
                pass
            new_config.set('general', 'serverType', import_data['type'])
            server_config(import_data['name'], new_config, os.path.join(tmpsvr, server_ini))

            if progress_func:
                progress_func(33)

            # Erase server folder after copying
            safe_delete(new_path)

        else:
            create_server_config(import_data, True, import_data['pack_type'])


        # Copy folder to server path and delete tmpsvr
        folder_check(new_path)
        copytree(tmpsvr, new_path, dirs_exist_ok=True)
        safe_delete(tempDir)
        safe_delete(downDir)

        if progress_func:
            progress_func(33 if not update else 66)


        # Generate ACL, 'EULA.txt', and 'server.properties' if importing a new modpack
        if not update:

            # Add global rules to ACL
            from acl import AclManager
            AclManager(import_data['name']).write_rules()

            if progress_func:
                progress_func(66)


            # Write EULA and "server.properties"
            time_stamp = datetime.date.today().strftime(f"#%a %b %d ") + datetime.datetime.now().strftime("%H:%M:%S ") + "MCS" + datetime.date.today().strftime(f" %Y")

            # Generate EULA.txt
            eula = f"""#By changing the setting below to TRUE you are indicating your agreement to our EULA (https://account.mojang.com/documents/minecraft_eula).
{time_stamp}
eula=true"""

            with open(os.path.join(server_path(import_data['name']), 'eula.txt'), 'w+') as f:
                f.write(eula)

            if server_path(import_data['name'], 'server.properties'):
                content = []
                with open(os.path.join(server_path(import_data['name']), 'server.properties'), 'r') as f:
                    content = f.readlines()
                    edited = False
                    if len(content) >= 1:
                        if content[1].startswith('#'):
                            content[1] = f"#{time_stamp}\n"
                            edited = True
                    if not edited:
                        content.insert(0, f"#{time_stamp}\n")
                        content.insert(0, "#Minecraft server properties\n")

                with open(os.path.join(server_path(import_data['name']), 'server.properties'), 'w+') as f:
                    f.writelines(content)
            else:
                fix_empty_properties(import_data['name'])


        if server_path(import_data['name'], server_ini):
            safe_delete(tempDir)
            safe_delete(downDir)
            make_update_list()
            if progress_func:
                progress_func(100)
            return True


# Generates new information for a server update
def init_update(telepath=False):
    if telepath:
        server_obj = server_manager.remote_server
    else:
        server_obj = server_manager.current_server
    new_server_info['name'] = server_obj.name

    # Check for Geyser and chat reporting, and prep addon objects
    chat_reporting = False
    new_server_info['addon_objects'] = server_obj.addon.return_single_list()
    for addon in new_server_info['addon_objects']:
        try:
            if addon.name.lower() == "freedomchat":
                chat_reporting = True
                new_server_info['addon_objects'].remove(addon)
            if addon.name.lower() == "no-chat-reports":
                chat_reporting = True
                new_server_info['addon_objects'].remove(addon)
            if addon.name.lower() == "viaversion":
                new_server_info['addon_objects'].remove(addon)
            if addon.author.lower() == "geysermc":
                new_server_info['addon_objects'].remove(addon)
        except AttributeError:
            continue

    new_server_info['server_settings']['disable_chat_reporting'] = chat_reporting
    new_server_info['server_settings']['geyser_support'] = server_obj.geyser_enabled


# Updates a world in a server
def update_world(path: str, new_type='default', new_seed='', telepath_data={}):
    if telepath_data:
        server_obj = server_manager.remote_server
    else:
        server_obj = server_manager.current_server

    # First, save backup
    server_obj.backup.save()

    # Delete current world
    world_path = server_path(server_obj.name, server_obj.world)
    if world_path:
        def delete_world(w: str):
            if os.path.exists(w):
                safe_delete(w)

        delete_world(world_path)
        delete_world(world_path + "_nether")
        delete_world(world_path + "_the_end")

    # Copy world to server if one is selected
    world_name = 'world'
    if path.strip().lower() != "world":
        world_name = os.path.basename(path)
        copytree(path, os.path.join(server_obj.server_path, world_name))

    # Fix level-type
    if version_check(server_obj.version, '>=', '1.19') and new_type == 'default':
        new_type = 'normal'

    # Change level-name in 'server.properties' and server_obj.world
    server_obj.server_properties['level-name'] = world_name
    server_obj.server_properties['level-type'] = new_type
    server_obj.server_properties['level-seed'] = new_seed

    server_obj.write_config()
    server_obj.reload_config()



# ------------------------------------------------ Server Functions ----------------------------------------------------


# Toggles favorite status in Server Manager
def toggle_favorite(server_name: str):
    config_file = server_config(server_name)
    config_file.set('general', 'isFavorite', ('false' if config_file.get('general', 'isFavorite') == 'true' else 'true'))
    server_config(server_name, config_file)

    return bool(config_file.get('general', 'isFavorite') == 'true')


# Returns general server type from specific type
def server_type(specific_type: str):
    if specific_type.lower().strip() in ['craftbukkit', 'bukkit', 'spigot', 'paper', 'purpur']:
        return 'bukkit'
    else:
        return specific_type.lower().strip()


# Returns absolute file path of server directories
def server_path(server_name: str, *args):
    path_name = os.path.join(applicationFolder, 'Servers', server_name, *args)
    return path_name if os.path.exists(path_name) else None


# auto-mcs.ini config file function
# write_object is the configparser object returned from this function
def server_config(server_name: str, write_object=None, config_path=None):
    if config_path:
        config_file = os.path.abspath(config_path)
    else:
        config_file = server_path(server_name, server_ini)


    # If write_object, write it to file path
    if write_object:

        if write_object.get('general', 'serverType').lower() not in ['forge', 'paper', 'purpur']:
            write_object.remove_option('general', 'serverBuild')

        if os_name == "windows":
            run_proc(f"attrib -H \"{config_file}\"")

        with open(config_file, 'w') as f:
            write_object.write(f)

        if os_name == "windows":
            run_proc(f"attrib +H \"{config_file}\"")

        return write_object

    # Read only if no config object provided
    else:
        config = configparser.ConfigParser(allow_no_value=True, comment_prefixes=';')
        config.optionxform = str
        config.read(config_file)
        if config:
            if config.get('general', 'serverType').lower() not in ['forge', 'paper']:
                config.remove_option('general', 'serverBuild')

        return config


# Creates new auto-mcs.ini config file
def create_server_config(properties: dict, temp_server=False, modpack=False):

    # Write default config
    config = configparser.ConfigParser(allow_no_value=True, comment_prefixes=';')
    config.optionxform = str

    config.add_section('general')
    config.set('general', "; DON'T MODIFY THE CONTENTS OF THIS FILE")
    config.set('general', 'serverName', properties['name'])
    config.set('general', 'serverVersion', properties['version'])
    if properties['build']:
        config.set('general', 'serverBuild', str(properties['build']))
    config.set('general', 'serverType', properties['type'])
    config.set('general', 'isFavorite', 'false')
    config.set('general', 'updateAuto', 'prompt')
    config.set('general', 'allocatedMemory', 'auto')
    try:
        config.set('general', 'enableGeyser', str(properties['server_settings']['geyser_support']).lower())
    except:
        config.set('general', 'enableGeyser', 'false')
    config.set('general', 'enableNgrok', 'false')
    try:
        config.set('general', 'customFlags', ' '.join(properties['launch_flags']))
    except:
        pass
    if modpack:
        config.set('general', 'isModpack', str(modpack))

    config.add_section('bkup')
    config.set('bkup', 'bkupAuto', 'prompt')
    config.set('bkup', 'bkupMax', '5')
    config.set('bkup', 'bkupDir', backupFolder)


    # Write file to path
    config_path = os.path.join((tmpsvr if temp_server else server_path(properties['name'])), server_ini)

    with open(config_path, 'w') as f:
        config.write(f)

    if os_name == "windows":
        run_proc(f"attrib +H \"{config_path}\"")

    return config


# Reconstruct API dict to a configparser object
def reconstruct_config(remote_config: dict or configparser.ConfigParser, to_dict=False):
    if to_dict:
        if isinstance(remote_config, dict):
            return remote_config
        else:
            return {section: dict(remote_config.items(section)) for section in remote_config.sections()}

    else:
        config = configparser.ConfigParser(allow_no_value=True, comment_prefixes=';')
        config.optionxform = str
        for section, values in remote_config.items():
            if section == 'DEFAULT':
                continue

            config.add_section(section)
            for key, value in values.items():
                config.set(section, key, value)
    return config

# server.properties function
# write_object is the dict object returned from this function
def server_properties(server_name: str, write_object=None):
    properties_file = server_path(server_name, 'server.properties')
    force_strings = ['level-seed', 'level-name', 'motd', 'resource-pack', 'resource-pack-prompt', 'resource-pack-sha1']

    # If write_object, write it to file path
    if write_object:

        with open(properties_file, 'w', encoding='utf-8', errors='ignore') as f:
            file_contents = ""

            for key, value in write_object.items():
                if str(value).lower().strip() in ['true', 'false'] and str(key) not in force_strings:
                    value = str(value).lower().strip()

                file_contents += f"{key}{'' if key.startswith('#') else ('=' + str(value))}\n"

            f.write(file_contents)

        return write_object

    # Read only if no config object provided
    else:
        config = {}
        no_file = False

        try:
            with open(properties_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f.readlines():
                    if not line.strip():
                        continue

                    line_object = line.split("=")

                    # Convert content to a typed dictionary
                    try:
                        # Check for boolean value
                        if (line_object[1].strip().lower() == 'true') and (line_object[0].strip() not in force_strings):
                            config[line_object[0].strip()] = True
                        elif (line_object[1].strip().lower() == 'false') and (line_object[0].strip() not in force_strings):
                            config[line_object[0].strip()] = False

                        # Check for integers
                        else:
                            try:
                                config[line_object[0].strip()] = int(float(line_object[1].strip()))

                        # Normal strings
                            except ValueError:
                                config[line_object[0].strip()] = line_object[1].strip()


                    except IndexError:
                        config[line_object[0].strip()] = ""

        except OSError:
            no_file = True
        except TypeError:
            no_file = True

        # Re-generate 'server.properties' if the file does not exist
        if no_file or not config:
            fix_empty_properties(server_name)
            config = server_properties(server_name)

        return config


# Calculate system memory for server
def calculate_ram(properties):
    config_spec = "auto"
    ram = 0

    # Attempt to retrieve auto-mcs.ini spec first
    if server_path(properties['name']):

        config_file = server_config(properties['name'])
        if config_file:

            # Only pickup server as valid with good config
            if properties['name'] == config_file.get("general", "serverName"):

                try:
                    config_spec = config_file.get("general", "allocatedMemory")

                except configparser.NoOptionError:
                    config_file.set("general", "allocatedMemory", "auto")
                    server_config(properties['name'], config_file)


    # If it doesn't exist, set to auto
    if config_spec == "auto":

        try:
            ram = round(psutil.virtual_memory().total / 1073741824)

            if ram >= 32:
                ram = 6
            elif ram >= 16:
                ram = 4
            else:
                ram = 2
        except:
            ram = 2
            pass

        if properties['type'].lower() == "forge":
            ram = ram + 2

    else:
        ram = int(config_spec)

    return ram


# Generates server batch/shell script
def generate_run_script(properties, temp_server=False, custom_flags=None, no_flags=False):

    # Change directory to server path
    cwd = get_cwd()
    if temp_server:
        folder_check(tmpsvr)
        os.chdir(tmpsvr)
    else:
        folder_check(server_path(properties['name']))
        os.chdir(server_path(properties['name']))


    script = ""
    ram = calculate_ram(properties)

    # Use custom flags, or Aikar's flags if none are provided
    if no_flags:
        start_flags = ''
    elif not custom_flags:
        start_flags = ' -XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200 -XX:+UnlockExperimentalVMOptions -XX:+DisableExplicitGC -XX:+AlwaysPreTouch -XX:G1HeapWastePercent=5 -XX:G1MixedGCCountTarget=4 -XX:G1MixedGCLiveThresholdPercent=90 -XX:G1RSetUpdatingPauseTimePercent=5 -XX:SurvivorRatio=32 -XX:+PerfDisableSharedMem -XX:MaxTenuringThreshold=1 -XX:G1NewSizePercent=30 -XX:G1MaxNewSizePercent=40 -XX:G1HeapRegionSize=8M -XX:G1ReservePercent=20 -XX:InitiatingHeapOccupancyPercent=15 -Dusing.aikars.flags=https://mcflags.emc.gs -Daikars.new.flags=true'
    else:
        start_flags = f' {custom_flags}'


    # For every version except Forge
    if properties['type'] != 'forge':

        # Make sure this works non-spigot versions
        java = java_executable["legacy"] if version_check(properties['version'], '<','1.17') else java_executable['lts'] if version_check(properties['version'], '<','1.20.5') else java_executable['modern']

        # On bukkit derivatives, install geysermc, floodgate, and viaversion if version >= 1.13.2 (add -DPaper.ignoreJavaVersion=true if paper < 1.16.5)
        script = f'"{java}" -Xmx{ram}G -Xms{int(round(ram/2))}G{start_flags} -Dlog4j2.formatMsgNoLookups=true'

        if version_check(properties['version'], "<", "1.16.5") and properties['type'] in ['paper', 'purpur']:
            script += ' -DPaper.ignoreJavaVersion=true'

        # Improve performance on Purpur
        if properties['type'] == 'purpur':
            script += ' --add-modules=jdk.incubator.vector'

        script += ' -jar server.jar nogui'


    # Do some schennanies for Forge
    else:

        # Modern
        if version_check(properties['version'], ">=", "1.17"):
            java = java_executable["lts"] if version_check(properties['version'], '<', '1.20.5') else java_executable['modern']
            version_list = [os.path.basename(file) for file in glob(os.path.join("libraries", "net", "minecraftforge", "forge", f"1.{math.floor(float(properties['version'].replace('1.', '', 1)))}*")) if os.listdir(file)]
            arg_file = f"libraries/net/minecraftforge/forge/{version_list[-1]}/{'win_args.txt' if os_name == 'windows' else 'unix_args.txt'}"
            script = f'"{java}" -Xmx{ram}G -Xms{int(round(ram/2))}G {start_flags} -Dlog4j2.formatMsgNoLookups=true @{arg_file} nogui'

        # 1.6 to 1.16
        elif version_check(properties['version'], ">=", "1.6") and version_check(properties['version'], "<", "1.17"):
            script = f'"{java_executable["legacy"]}" -Xmx{ram}G -Xms{int(round(ram/2))}G {start_flags} -Dlog4j2.formatMsgNoLookups=true -jar server.jar nogui'


    script_check = ""
    if script:
        if os_name == "windows":
            with open(f"{start_script_name}.bat", "w+") as f:
                f.write(script)
            script_check = os.path.abspath(f"{start_script_name}.bat")
        else:
            with open(f"{start_script_name}.sh", "w+") as f:
                f.write(script)
            run_proc(f"chmod +x {start_script_name}.sh")
            script_check = os.path.abspath(f"{start_script_name}.sh")


    os.chdir(cwd)

    return script_check


# Return list of every valid server in 'applicationFolder'
def generate_server_list():
    global server_list
    global server_list_lower
    server_list = []
    server_list_lower = []

    try:
        for file in glob(os.path.join(serverDir, "*")):
            if os.path.isfile(os.path.join(file, server_ini)):
                server_list.append(os.path.basename(file))
                server_list_lower.append(os.path.basename(file).lower())

    except FileNotFoundError:
        pass

    return server_list


# Retrieve modrinth config for updates
def get_modrinth_data(name: str):
    index = os.path.join(server_path(name), f'{"" if os_name == "windows" else "."}modrinth.index.json')
    index_data = {"name": None, "version": '0.0.0', "latest": '0.0.0'}

    if index:
        if os_name == 'windows':
            run_proc(f"attrib -H \"{index}\"")

        with open(index, 'r') as f:
            data = json.loads(f.read())

            try:
                index_data['name'] = data['name']
            except KeyError:
                pass
            try:
                index_data['version'] = data['versionId']
            except KeyError:
                pass

        if os_name == 'windows':
            run_proc(f"attrib +H \"{index}\"")


        # Check online for latest version
        try:
            online_modpack = addons.get_modpack_url(addons.search_modpacks(index_data['name'])[0])
            index_data['latest'] = online_modpack.download_version
            index_data['download_url'] = online_modpack.download_url
        except IndexError:
            pass


    return index_data


# Return list of every valid server update property in 'applicationFolder'
def make_update_list():
    global update_list

    update_list = {}

    for name in glob(os.path.join(applicationFolder, "Servers", "*")):

        name = os.path.basename(name)

        serverObject = {name: {"updateAuto": "false", "needsUpdate": "false", "updateString": None, "updateUrl": None}}

        configFile = os.path.abspath(os.path.join(applicationFolder, 'Servers', name, server_ini))

        if os.path.isfile(configFile) is True:
            config = configparser.ConfigParser(allow_no_value=True, comment_prefixes=';')
            config.optionxform = str
            config.read(configFile)

            updateAuto = str(config.get("general", "updateAuto"))
            jarVer = str(config.get("general", "serverVersion"))
            jarType = str(config.get("general", "serverType"))

            try:
                jarBuild = str(config.get("general", "serverBuild"))
            except configparser.NoOptionError:
                jarBuild = ""

            try:
                isModpack = str(config.get("general", "isModpack"))
            except configparser.NoOptionError:
                isModpack = ""


            if isModpack:
                if isModpack == 'mrpack':
                    modpack_data = get_modrinth_data(name)
                    if (modpack_data['version'] != modpack_data['latest']) and not modpack_data['latest'].startswith("0.0.0"):
                        serverObject[name]["needsUpdate"] = "true"
                        serverObject[name]["updateString"] = modpack_data['latest']
                        serverObject[name]["updateUrl"] = modpack_data['download_url']


            else:
                new_version = latestMC[jarType.lower()]
                current_version = jarVer

                if ((jarType.lower() in ["forge", "paper", "purpur"]) and (jarBuild != "")) and (new_version == current_version):
                    new_version += " b-" + str(latestMC["builds"][jarType.lower()])
                    current_version += " b-" + str(jarBuild)

                if (new_version != current_version) and not current_version.startswith("0.0.0"):
                    serverObject[name]["needsUpdate"] = "true"

            serverObject[name]["updateAuto"] = updateAuto

        update_list.update(serverObject)

    return update_list


# Installs ngrok in tools directory
def install_ngrok():

    # Attempt to find download URL
    ngrok_url = "https://dl.equinox.io/ngrok/ngrok-v3/stable"
    final_url = None
    file_name = None

    soup = BeautifulSoup(requests.get(ngrok_url).content, features="html.parser")
    for a in soup.find_all('a', "btn"):
        try:
            dl_url = a.get('href')
            if os_name == "windows" and "stable-windows-amd64" in dl_url:
                final_url = dl_url
                file_name = "ngrok.zip"
                break

            if os_name == "macos" and "stable-darwin-amd64" in dl_url:
                final_url = dl_url
                file_name = "ngrok.zip"
                break

            if os_name == "linux" and is_arm and "stable-linux-arm64" in dl_url:
                final_url = dl_url
                file_name = "ngrok.tgz"
                break

            if os_name == "linux" and not is_arm and "stable-linux-amd64" in dl_url:
                final_url = dl_url
                file_name = "ngrok.tgz"
                break

        except AttributeError:
            continue

    # If URL not found, error out operation
    if not final_url:
        return False

    try:
        # If URL found, download ngrok archive
        tool_path = os.path.join(applicationFolder, 'Tools')
        folder_check(downDir)
        download_url(final_url, file_name, downDir)

        # Extract executable from archive
        folder_check(tool_path)
        cwd = get_cwd()
        os.chdir(tool_path)
        archive_file = ('ngrok.exe' if os_name == 'windows' else 'ngrok')
        run_proc(f"tar -xf \"{os.path.join(downDir, file_name)}\" \"{archive_file}\"")
        os.rename(archive_file, ngrok_exec)
        os.chdir(cwd)
        safe_delete(downDir)

    except Exception as e:
        print(e)
        return False

    return os.path.exists(os.path.join(tool_path, ngrok_exec))


# Checks for a valid ngrok config file
def check_ngrok_creds():
    identifier = 'authtoken:'

    if os_name == 'windows':
        config_path = os.path.join(home, 'AppData', 'Local', 'ngrok', 'ngrok.yml')
        old_path = os.path.join(home, '.ngrok2', 'ngrok.yml')
    elif os_name == 'macos':
        config_path = os.path.join(appdata, 'ngrok', 'ngrok.yml')
        old_path = os.path.join(home, '.config', 'ngrok', 'ngrok.yml')
    else:
        config_path = os.path.join(home, '.config', 'ngrok', 'ngrok.yml')
        old_path = os.path.join(home, '.ngrok2', 'ngrok.yml')

    if os.path.isfile(old_path):
        run_proc(f'"{os.path.join(applicationFolder, "Tools", ngrok_exec)}" config upgrade')
        with open(config_path, 'r') as f:
            for line in f.readlines():
                if line.startswith(identifier) and line.strip() != identifier:
                    return True

    if os.path.isfile(config_path):
        with open(config_path, 'r') as f:
            for line in f.readlines():
                if line.startswith(identifier) and line.strip() != identifier:
                    return True

    return False


# Gets current ngrok IP
def get_ngrok_ip(server_name: str):
    global ngrok_ip
    retries = 0

    while retries < 10:
        try:
            url = "http://localhost:4040/api/tunnels"
            reqs = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            json_obj = json.loads(reqs.text)
            ip = json_obj["tunnels"][0]["public_url"]
            ngrok_ip = {'name': server_name, 'ip': ip.split("tcp://")[1].strip()}
            break
        except:
            time.sleep(1)
            retries += 1


# Check if port is open on host
def check_port(ip: str, port: int):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(120)
    result = sock.connect_ex((ip, port))
    return result == 0


# Assigned from 'menu.py' to update IP text on screens
refresh_ips = None

# Returns active IP address of 'name'
def get_current_ip(name: str, get_ngrok=False):
    global public_ip, ngrok_ip

    private_ip = ""
    original_port = "25565"
    updated_port = ""
    final_addr = {}

    lines = []

    if server_path(name, "server.properties"):
        with open(server_path(name, "server.properties"), 'r') as f:
            lines = f.readlines()
            for line in lines:
                if re.search(r'server-port=', line):
                    original_port = line.replace("server-port=", "").replace("\n", "")
                elif re.search(r'server-ip=', line):
                    private_ip = line.replace("server-ip=", "").replace("\n", "")


        # Check for server port conflicts
        bad_ports = []
        if server_manager.running_servers:
            bad_ports = [int(server.run_data['network']['address']['port']) for server in server_manager.running_servers.values() if server.name != name]

        new_port = int(original_port)
        conflict = False

        for port in bad_ports:
            if new_port == port:
                if new_port > 50000:
                    new_port -= 1
                else:
                    new_port += 1
                conflict = True


        # If there is a conflicting port, change it temporarily
        if conflict:
            updated_port = str(new_port)
            with open(server_path(name, "server.properties"), 'w+') as f:
                for line in lines:
                    if re.search(r'server-port=', line):
                        lines[lines.index(line)] = f"server-port={updated_port}\n"
                        print(updated_port)
                        break
                f.writelines(lines)


        # More ip info
        if not private_ip:
            private_ip = get_private_ip()


        if not get_ngrok:
            if app_online:
                def get_public_ip(server_name, *args):
                    global public_ip

                    # If public IP isn't defined, retrieve it from API
                    if public_ip:
                        new_ip = public_ip
                    else:
                        try:
                            new_ip = requests.get('http://api.ipify.org', timeout=5).content.decode('utf-8', errors='ignore')
                        except:
                            new_ip = ""

                    # Check if port is open
                    if new_ip and 'bad' not in new_ip.lower():
                        public_ip = new_ip

                        # Assign public IP to current running server
                        if server_manager.running_servers:
                            if updated_port:
                                final_port = int(updated_port)
                            else:
                                final_port = int(original_port)

                            port_check = check_port(public_ip, final_port)
                            if port_check:
                                try:
                                    server_manager.running_servers[server_name].run_data['network']['address']['ip'] = public_ip
                                    server_manager.running_servers[server_name].run_data['network']['public_ip'] = public_ip

                                    # Update screen info
                                    if refresh_ips:
                                        refresh_ips(name)

                                except KeyError:
                                    pass

                ip_timer = Timer(1, functools.partial(get_public_ip, name))
                ip_timer.daemon = True
                ip_timer.start()


    # Format network info
    if get_ngrok:
        def get_ngk_ip(server_name, *args):
            global ngrok_ip
            get_ngrok_ip(server_name)

            if ngrok_ip['ip']:
                # Assign ngrok IP to current running server
                if server_manager.running_servers:
                    try:
                        server_obj = server_manager.running_servers[server_name]
                        server_obj.run_data['network']['address']['ip'] = ngrok_ip['ip']
                        server_obj.run_data['network']['public_ip'] = ngrok_ip['ip']
                        server_obj.send_log(f"Initialized ngrok connection '{ngrok_ip['ip']}'", 'success')
                    except KeyError:
                        pass

        ip_timer = Timer(0, functools.partial(get_ngk_ip, name))
        ip_timer.daemon = True
        ip_timer.start()

    # if public_ip:
    #     final_addr['ip'] = public_ip
    if private_ip:
        final_addr['ip'] = private_ip
    else:
        final_addr['ip'] = '127.0.0.1'

    if updated_port:
        final_addr['port'] = updated_port
    elif original_port:
        final_addr['port'] = original_port
    else:
        final_addr['port'] = "25565"


    network_dict = {
        'address': final_addr,
        'public_ip': public_ip if public_ip else None,
        'private_ip': private_ip if private_ip else '127.0.0.1',
        'original_port': original_port if updated_port else None
    }

    return network_dict


# Fixes empty 'server.properties' file
def fix_empty_properties(name):
    path = server_path(name)

    timeStamp = datetime.date.today().strftime(f"#%a %b %d ") + datetime.datetime.now().strftime("%H:%M:%S ") + "MCS" + datetime.date.today().strftime(f" %Y")

    eula = f"""#By changing the setting below to TRUE you are indicating your agreement to our EULA (https://account.mojang.com/documents/minecraft_eula).
{timeStamp}
eula=true"""

    # EULA
    with open(os.path.join(path, 'eula.txt'), "w+") as f:
        f.write(eula)

    # server.properties
    serverProperties = f"""#Minecraft server properties
{timeStamp}
view-distance=10
max-build-height=256
server-ip=
level-seed=
gamemode=0
server-port=25565
enable-command-block=false
allow-nether=true
enable-rcon=false
op-permission-level=4
enable-query=false
generator-settings=
resource-pack=
player-idle-timeout=0
level-name=world
motd=A Minecraft Server
announce-player-achievements=true
force-gamemode=false
hardcore=false
white-list=false
pvp=true
spawn-npcs=true
generate-structures=true
spawn-animals=true
snooper-enabled=true
difficulty=1
network-compression-threshold=256
level-type=default
spawn-monsters=true
max-tick-time=60000
max-players=20
spawn-protection=20
online-mode=true
allow-flight=true
resource-pack-hash=
max-world-size=29999984"""

    with open(os.path.join(path, 'server.properties'), "w+") as f:
        f.write(serverProperties)


# CTRL + Backspace function
def control_backspace(text, index):

    # Split up text into parts
    start = text[:index].strip()
    end = text[index:]

    if " " not in start:
        new_text = ""
    else:
        new_text = start.rsplit(" ", 1)[0]

    # Add space between concatenated blocks if one does not exist
    try:
        if new_text[-1] != " " and not end:
            new_text += " "

        elif new_text[-1] != " " and end[0] != " ":
            new_text += " "

    except IndexError:
        pass

    # Return edited text
    final_text = new_text + end
    new_index = len(text) - len(final_text)
    return final_text, new_index


# Get player head to .png: pass player object
def get_player_head(user: str):

    # Set default image in case of failure
    default_image = os.path.join(gui_assets, 'steve.png')
    if not (app_online and user):
        return default_image

    try:
        head_cache = os.path.join(cacheDir, 'heads')
        final_path = os.path.join(head_cache, user)
        url = f"https://mc-heads.net/avatar/{user}"

        if os.path.exists(final_path):
            age = abs(datetime.datetime.today().day - datetime.datetime.fromtimestamp(os.stat(final_path).st_mtime).day)
            if age < 3:
                return final_path
            else:
                os.remove(final_path)

        elif not check_free_space():
            return default_image

        folder_check(head_cache)
        download_url(url, user, head_cache)

        if os.path.exists(final_path):
            return final_path
        else:
            return default_image

    except Exception as e:
        if debug:
            print(f"Error retrieving head for '{user}': {e}")
        return default_image


# Compatibility to cache server icon with telepath
def get_server_icon(server_name: str, telepath_data: dict):
    if not (app_online and server_name):
        return None

    try:
        name = f"{telepath_data['host'].replace('/', '+')}+{server_name}"
        icon_cache = os.path.join(cacheDir, 'icons')
        final_path = os.path.join(icon_cache, name)

        if os.path.exists(final_path):
            age = abs(datetime.datetime.today().day - datetime.datetime.fromtimestamp(os.stat(final_path).st_mtime).day)
            if age < 3:
                return final_path
            else:
                os.remove(final_path)

        elif not check_free_space():
            return None

        folder_check(icon_cache)
        telepath_download(telepath_data, telepath_data['icon-path'], icon_cache, rename=name)

        if os.path.exists(final_path):
            return final_path
        else:
            return None

    except Exception as e:
        if debug:
            print(f"Error retrieving icon for '{server_name}': {e}")
        return None



# ---------------------------------------------- Global Search Function ------------------------------------------------

# Generates content for all global searches
class SearchManager():

    def get_server_list(self):
        if server_manager.server_list:
            return {s._view_name: s._telepath_data for s in server_manager.server_list}
        else:
            return {s: None for s in generate_server_list()}

    def __init__(self):

        # Used to contain attributes of pages
        class ScreenObject():
            def __init__(self, name: str, screen_id: str, options: list or staticmethod, helper_keywords=[]):
                self.id = screen_id
                self.name = name
                self.options = options
                self.helper_keywords = helper_keywords
                self.score = 0

        self.guide_tree = {}
        self.options_tree = {

            'MainMenu': [
                ScreenObject('Home', 'MainMenuScreen', {'Update auto-mcs': None, 'View changelog': f'{project_link}/releases/latest', 'Create a new server': 'CreateServerNameScreen', 'Import a server': 'ServerImportScreen', 'Change language': 'ChangeLocaleScreen'}, ['addonpack', 'modpack', 'import modpack']),
                ScreenObject('Server Manager', 'ServerManagerScreen', self.get_server_list),
            ],

            'CreateServer': [
                ScreenObject('Create Server (Step 1)', 'CreateServerNameScreen', {'Server Name': None}),
                ScreenObject('Create Server (Step 2)', 'CreateServerTypeScreen', {'Select Vanilla': None, 'Select Paper': None, 'Select Purpur': None, 'Select Fabric': None, 'Select CraftBukkit': None, 'Select Forge': None, 'Select Spigot': None}),
                ScreenObject('Create Server (Step 3)', 'CreateServerVersionScreen', {'Type in version': None}),
                ScreenObject('Create Server (Step 4)', 'CreateServerWorldScreen', {'Browse for a world': None, 'Type in seed': None, 'Select world type': None}),
                ScreenObject('Create Server (Step 5)', 'CreateServerNetworkScreen', {'Specify IP/port': None, 'Type in Message Of The Day': None, 'Configure Access Control': 'CreateServerAclScreen'}),
                ScreenObject('Create Server (Access Control)', 'CreateServerAclScreen', {'Configure bans': None, 'Configure operators': None, 'Configure the whitelist': None}, ['player', 'user', 'ban', 'white', 'op', 'rule', 'ip', 'acl', 'access control']),
                ScreenObject('Create Server (Add-on Manager)', 'CreateServerAddonScreen', {'Download add-ons': 'CreateServerAddonSearchScreen', 'Import add-ons': None, 'Toggle add-on state': None}, ['mod', 'plugin', 'addon', 'extension']),
                ScreenObject('Create Server (Step 6)', 'CreateServerOptionsScreen', {'Change gamemode': None, 'Change difficulty': None, 'Specify maximum players': None, 'Enable spawn protection': None, 'Configure gamerules': None, 'Specify randomTickSpeed': None, 'Enable Bedrock support': None}),
                ScreenObject('Create Server (Step 7)', 'CreateServerReviewScreen', {'Review & create server': None})
            ],

            'ServerImport': [
                ScreenObject('Import Server', 'ServerImportScreen', {'Import a server folder': None, 'Import an auto-mcs back-up': None, 'Import a Modpack': None, 'Download a Modpack': None}),
            ],

            'Server': [
                ScreenObject('Server Manager', 'ServerViewScreen', {'Launch server': None, 'Stop server': None, 'Restart server': None, 'Enter console commands': None}),
                ScreenObject('Back-up Manager', 'ServerBackupScreen', {'Save a back-up now': None, 'Restore from a back-up': 'ServerBackupRestoreScreen', 'Enable automatic back-ups': None, 'Specify maximum back-ups': None, 'Open back-up directory': None, 'Migrate back-up directory': None}, ['backup', 'revert', 'snapshot', 'restore', 'save']),
                ScreenObject('Access Control', 'ServerAclScreen', {'Configure bans': None, 'Configure operators': None, 'Configure the whitelist': None}, ['player', 'user', 'ban', 'white', 'op', 'rule', 'ip', 'acl', 'access control']),
                ScreenObject('Add-on Manager', 'ServerAddonScreen', {'Download add-ons': 'ServerAddonSearchScreen', 'Import add-ons': None, 'Toggle add-on state': None, 'Update add-ons': None}, ['mod', 'plugin', 'addon', 'extension']),
                ScreenObject('Script Manager', 'ServerAmscriptScreen', {'Download scripts': 'ServerAmscriptSearchScreen', 'Import scripts': None, 'Create a new script': 'CreateAmscriptScreen', 'Edit a script': None, 'Open script directory': None}, ['amscript', 'script', 'ide', 'develop']),
                ScreenObject('Server Settings', 'ServerSettingsScreen', {"Edit 'server.properties'": 'ServerPropertiesEditScreen', 'Open server directory': None, 'Specify memory usage': None, 'Change MOTD': None, 'Specify IP/port': None, 'Change launch flags': None, 'Enable proxy (ngrok)': None, 'Install proxy (ngrok)': None, 'Enable Bedrock support': None, 'Enable automatic updates': None, 'Update this server': None, "Change 'server.jar'": 'MigrateServerTypeScreen', 'Rename this server': None, 'Change world file': 'ServerWorldScreen', 'Delete this server': None}, ['ram', 'memory', 'server.properties', 'rename', 'delete', 'bedrock', 'proxy', 'ngrok', 'update', 'jvm', 'motd'])
            ]
        }

    # Cache the guides to a .json file
    def cache_pages(self):
        if not app_online:
            return False

        def get_html_contents(url: str):
            while True:
                req = requests.get(url)
                if req.status_code == 200:
                    break
                else:
                    time.sleep(3)

            return BeautifulSoup(req.content, features='html.parser')

        cache_file = os.path.join(cacheDir, 'guide-cache.json')
        cache_data = {}

        # If cache file exists, load data from there instead
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                self.guide_tree = json.loads(f.read())
                return True

        # If not, scrape the website
        base_url = "https://www.auto-mcs.com/guides"
        content = get_html_contents(base_url)

        for a in content.find_all('a', class_="portfolio-hover-item"):

            sub_url = base_url + a.get('href').replace('guides/', '')
            title = a.get_text().strip()

            guide = get_html_contents(sub_url)
            time.sleep(1)

            # Clean-up guide by removing unnecessary elements
            for tag in guide("div", id='toc'):
                tag.decompose()
            for tag in guide("section", id='itemPagination'):
                tag.decompose()
            for tag in guide("section", class_='page-section'):
                if '<  guides' in tag.get_text() or 'help@auto-mcs.com' in tag.get_text():
                    tag.decompose()

            # Format specific tags in a custom way
            for tag in guide("code"):
                add_space = tag.text[-1] == ' '
                tag.replace_with(f'`{tag.text.strip()}`{" " if add_space else ""}')

            for tag in guide("a"):
                try:
                    href = tag.get('href')
                    if href:
                        if href.startswith('/'):
                            href = f'https://auto-mcs.com{href}'

                        if href.endswith('.png') or href.endswith('.jpg'):
                            new_href = requests.get(href, allow_redirects=True).history[-1].headers['location']
                            time.sleep(1)
                            tag.replace_with(BeautifulSoup(f'<img src="{new_href}">', 'html.parser').img)
                            continue

                        tag.replace_with(f'[{tag.text}](<{href}>)')
                except:
                    pass

            # Organize page contents into a dictionary of headers and paragraphs
            page_content = {}
            images = {}
            last = None
            last_header = ''
            header_list = ['h1', 'h2', 'h3']
            for element in guide.find_all():
                text = element.text.strip()

                accordion_header = 'accordion-item__title' in element.get('class', []) and element.name == 'span'

                if element.name in ['p', 'ul', 'img'] or element.name in header_list or accordion_header:
                    if len(element.text) > 10000:
                        continue

                    if last:
                        if last.name in header_list and element.name in header_list:
                            continue

                    # Format lists
                    if element.name == 'ul':
                        text = '\n'.join([f'- {l.text.strip()}' for l in element.find_all('li') if l.text.strip()])
                    elif element.name == 'li' or element.parent.name == 'li':
                        continue

                    # Format images
                    if element.name == 'img':
                        try:
                            text = f"[⠀]({element.get('src')})"
                            images[last_header].append(text)
                        except:
                            pass
                        continue

                    last = element

                    # Ignore certain headers
                    if ('controls' == text.lower() or 'some notable features include' in text.lower()):
                        text = f"## {text}"

                    # Add header
                    elif element.name in header_list or accordion_header:
                        last_header = text.lower()
                        page_content[last_header] = ''
                        images[last_header] = []
                        continue

                    page_content[last_header] += re.sub(r'\n\n+', '\n\n', text) + '\n'

            # Format text to read better
            for header, content in page_content.items():
                content = re.sub(r'\.(?=[A-Z])', '.\n\n', content)
                content = re.sub(r'(\n+Note:  )(.*)(\n+)', lambda x: f'\n\n> *Note:*  **{x.group(2)}**\n\n', f'\n{content}\n').strip()
                content = re.sub(r'(?<=(\w|\d|\.|\?|\!))(\n)(?=(\w|\d|\.|\?|\!))', '\n\n', content).strip()
                content = content.replace('permissions**\n\n!`auto-mcs --launch "Server 1, Server 2"`', 'permissions! `auto-mcs --launch "Server 1, Server 2"`**')
                content = content.replace('`java.lang.**\n\nOutOfMemoryError: Java heap space`', '`java.lang.OutOfMemoryError: Java heap space`**')
                if header in images:
                    content += ' '.join(list(set(images[header])))

                # Remove empty data
                if not content.strip():
                    del page_content[header]

                page_content[header] = content

            cache_data[title] = {'url': sub_url, 'content': page_content}

        with open(cache_file, 'w+') as f:
            f.write(json.dumps(cache_data))
        self.guide_tree = cache_data
        return True

    # Generates a list of available options based on the current screen
    def filter_options(self, current_screen):
        screen_list = self.options_tree['MainMenu']
        final_list = []

        if current_screen.startswith('ServerImport'):
            screen_list.extend(self.options_tree['ServerImport'])

        if current_screen.startswith('CreateServer'):
            for screen in self.options_tree['CreateServer']:
                if not (new_server_info['type'] == 'vanilla' and screen.id == 'ServerAddonScreen'):
                    if screen not in screen_list:
                        screen_list.append(screen)

        if server_manager.current_server:
            for screen in self.options_tree['Server']:
                if not (server_manager.current_server.type == 'vanilla' and screen.id == 'ServerAddonScreen'):
                    if screen not in screen_list:
                        screen_list.append(screen)


        # Iterate through available screens to create search objects
        for screen in screen_list:
            if screen.id == 'ServerManagerScreen':
                final_list.append(ScreenResult(screen.name, 'Configuration page', screen.id, screen.helper_keywords))
                for server, telepath_data in screen.options().items():
                    if telepath_data:
                        telepath = deepcopy(telepath_data)
                        telepath['name'] = server.rsplit('/', 1)[-1]
                        keywords = [telepath['host'], telepath['nickname'], 'telepath', 'remote', telepath['name']]
                        final_list.append(ServerResult(server, 'Telepath server', None, keywords, telepath=telepath))
                    else:
                        final_list.append(ServerResult(server, 'Installed server', None))

            elif (screen.id.startswith('Server') and 'Import' not in screen.id) and server_manager.current_server:
                keywords = list(screen.options.keys())
                keywords.extend(screen.helper_keywords)
                if current_screen != screen.id:
                    final_list.append(ScreenResult(screen.name, f'Configuration page ({server_manager.current_server.name})', screen.id, keywords))
                for setting, value in screen.options.items():

                    # Ignore results for running server
                    if server_manager.current_server.running and setting.lower() in ('launch server', 'update this server', "change 'server.jar'", 'rename this server', 'change world file', 'delete this server'):
                        continue
                    elif not server_manager.current_server.running and setting.lower() in ('restart server', 'stop server'):
                        continue

                    # Change results for ngrok installation
                    if setting.lower() == 'enable proxy (ngrok)' and not ngrok_installed:
                        continue
                    if setting.lower() == 'install proxy (ngrok)' and ngrok_installed:
                        continue

                    # If server is up to date, hide update prompt
                    if setting.lower() == 'update this server' and not server_manager.current_server.update_string:
                        continue

                    final_list.append(SettingResult(setting, f'Action in {screen.name} ({server_manager.current_server.name})', value if value else screen.id, keywords))

            else:
                keywords = list(screen.options.keys())
                keywords.extend(screen.helper_keywords)
                final_list.append(ScreenResult(screen.name, 'Configuration page', screen.id, keywords))
                for setting, value in screen.options.items():

                    if setting.lower() == 'update auto-mcs' and app_latest:
                        continue

                    final_list.append(SettingResult(setting, f'Action in {screen.name}', value if value else screen.id, keywords))


        # Return a list of all created screens, settings, and guides
        return final_list

    # Generate a list of weighted results from a search
    def execute_search(self, current_screen, query):
        
        match_list = {
            'guide': SearchObject(),
            'setting': [],
            'screen': [],
            'server': []
        }

        # Cleanup strings
        def clean_str(string):
            return string.strip().lower().replace('-', '')

        # Removes common words to improve search results
        def remove_common_words(string):
            common_words = ['the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'I', 'it', 'for', 'not',
                            'on', 'with', 'he', 'as', 'you', 'do', 'at', 'this', 'but', 'his', 'by', 'from', 'they',
                            'we', 'say', 'her', 'she', 'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there',
                            'their', 'what', 'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me',
                            'when', 'make', 'can', 'like', 'time', 'no', 'just', 'him', 'know', 'take', 'people',
                            'into', 'year', 'your', 'good', 'some', 'could', 'them', 'see', 'other', 'than', 'then',
                            'now', 'look', 'only', 'come', 'its', 'over', 'think', 'also', 'back', 'after', 'two',
                            'how', 'our', 'work', 'first', 'well', 'way', 'even', 'new', 'want', 'because', 'any',
                            'these', 'give', 'day', 'most', 'us', 'is']

            final_words = []

            for w in string.split(' '):
                if w.lower().strip() not in common_words:
                    final_words.append(w)

            return ' '.join(final_words)

        # Manual query overrides for improved results
        def check_overrides(string):
            def check_word(w):
                return len(re.findall(fr'\b{w}\b', string)) > 0

            if (check_word('automcs') or check_word('this')) and 'what' in query.lower():
                return 'getting started'

            elif (check_word('automcs') or check_word(
                'this')) and 'addon' not in query.lower() and 'script' not in query.lower() and (
                check_word('download') or check_word('use') or check_word('install') or check_word('get')):
                return 'installation'

            elif (check_word('level') or check_word('world')) and (
                'back' not in query.lower() and 'up' not in query.lower()):
                return 'change the world'

            elif check_word('ram') or check_word('memory'):
                return 'allocate memory'

            elif check_word('ide'):
                return 'amscript ide'

            elif 'modding' in query.lower():
                return 'installing addons'

            elif check_word('distribution'):
                return 'server type'

            elif (check_word('use') or check_word('controls') or check_word('help') or check_word('manager')) and (
                check_word('acl') or 'access control' in query.lower()):
                return 'what are rules'

            elif (check_word('make') or check_word('create')) and check_word('server'):
                return 'create a server'

            elif check_word('amscript') and 'what is' in query.lower():
                return 'amscript'

            elif 'port forward' in query.lower() or check_word(
                'nat') or 'address translation' in query.lower() or check_word('tcp') or check_word(
                'udp') or 'port trigger' in query.lower():
                return 'wan config'

            elif check_word('port') or check_word('ip'):
                return 'lan config'

            elif check_word('amscript') and (
                check_word('download') or check_word('use') or check_word('install') or check_word('get')):
                return 'amscript getting started'

            else:
                return string


        # Find matching objects
        options_list = self.filter_options(current_screen)
        if options_list:
            o_query = query

            # First check for a title match
            query = clean_str(query).replace('?', '').replace(',', '').replace('help','').replace('guide','')
            query = query.replace('mod', 'addon').replace('plugin', 'addon').replace('folder', 'directory').replace('path', 'directory').replace('addonpack', 'modpack')
            query = check_overrides(query)

            for obj in options_list:
                title = obj.title
                simple_query = remove_common_words(query)
                if simple_query in clean_str(obj.title):
                    obj.score = 100
                    if obj not in match_list[obj.type]:
                        match_list[obj.type].append(obj)

            # If no match was found, search every content header
            else:
                for obj in options_list:
                    title = clean_str(obj.title)
                    obj.score = 0

                    if query == title:
                        obj.score = 100

                    else:
                        # Initial score based on title match
                        obj.score = similarity(query, title) * 10

                        # Increase score comparing word by word
                        for w1 in title.split(' '):
                            for w2 in query.split(' '):
                                obj.score += ((similarity(w1, w2) * len(w2)) * 2)

                        # Finally, increase score by pre-existing keyword matches
                        for keyword in obj.keywords:
                            if clean_str(keyword) in query:
                                obj.score += 20

                        # Modify values based on object type
                        if obj.type in ['server'] and current_screen == 'ServerManagerScreen':
                            obj.score *= 2
                        elif obj.type in ['server'] and (current_screen.startswith('Server') or current_screen.startswith('CreateServer')):
                            obj.score /= 1.5

                    list_type = obj.type
                    if obj not in match_list[list_type]:
                        match_list[list_type].append(obj)


        # Search through every guide to return relevant information from a query
        if app_online and self.guide_tree:
            o_query = query

            # First check for a title match
            query = clean_str(query).replace('?', '').replace(',', '').replace('help','').replace('guide','')
            query = query.replace('mod', 'addon').replace('plugin', 'addon').replace('folder', 'directory').replace('path', 'directory')
            query = check_overrides(query)

            for title in self.guide_tree.keys():
                simple_query = remove_common_words(query)
                if simple_query in clean_str(title):
                    match_list['guide'] = GuideResult(
                        f'{title} - Overview',
                        'View guide from auto-mcs.com',
                        self.guide_tree[title]['url'],
                        score = 100
                    )

            # If no match was found, search every content header
            else:
                for page_title, data in self.guide_tree.items():
                    url = data['url']
                    content = data['content']

                    o_page_title = page_title
                    page_title = clean_str(page_title)

                    # Ignore pages based on query
                    def check_word_in_title(w1, w2=None, invert=False):
                        if not w2:
                            w2 = w1
                        if invert:
                            return w1 in query and w2 not in page_title
                        else:
                            return w1 not in query and w2 in page_title

                    if check_word_in_title('addon') or check_word_in_title('backup') or check_word_in_title('amscript'):
                        continue

                    if check_word_in_title('addon', invert=True) or check_word_in_title('backup', invert=True) or check_word_in_title('amscript', invert=True):
                        continue

                    for title, paragraph in content.items():
                        o_paragraph = paragraph
                        o_title = title
                        title = clean_str(title)
                        paragraph = clean_str(paragraph)

                        # If title matches query, give it a high score
                        if query == title:
                            similarity_score = 100
                        else:
                            # Calculate the similarity score
                            similarity_score = round(similarity(paragraph, query)) + similarity(title, query)

                            # If words from search are in the paragraph, increase score
                            for word in remove_common_words(query).split():
                                if len(word) > 2:
                                    similarity_score += (len(re.findall(fr'\b{word}\b', paragraph)) / 10)
                                    similarity_score += (len(re.findall(fr'\b{word}\b', title)) / 10)

                        # print(similarity_score)
                        if similarity_score > match_list['guide'].score:
                            if 'https://' in o_title.lower():
                                continue
                            match_list['guide'] = GuideResult(
                                f'{o_page_title} - {o_title.title()}',
                                'View guide from auto-mcs.com',
                                url + '#' + o_title.lower().replace(' ', '-'),
                                score = similarity_score
                            )

            if 'guide' in o_query.lower() or 'help' in o_query.lower():
                match_list['guide'].score = 1000

        match_list['setting'] = tuple(sorted(match_list['setting'], key=lambda x: x.score, reverse=True))
        match_list['screen'] = tuple(sorted(match_list['screen'], key=lambda x: x.score, reverse=True))
        match_list['server'] = tuple(sorted(match_list['server'], key=lambda x: x.score, reverse=True))
        return match_list

# Base search result
class SearchObject():
    def __init__(self):
        self.type = 'undefined'
        self.score = 0

# Search result that matches a setting
class SettingResult(SearchObject):
    def __init__(self, title, subtitle, target, keywords=[], score=0):
        super().__init__()
        self.type = 'setting'
        self.icon = os.path.join(gui_assets, 'icons', 'play-circle-sharp.png')
        self.color = (0.7, 0.7, 1, 1)
        self.title = title
        self.subtitle = subtitle
        self.target = target
        self.keywords = keywords
        self.score = score

# Search result that matches an online guide
class GuideResult(SearchObject):
    def __init__(self, title, subtitle, target, keywords=[], score=0):
        super().__init__()
        self.type = 'guide'
        self.icon = os.path.join(gui_assets, 'icons', 'newspaper.png')
        self.color = (0.6, 1, 0.75, 1)
        self.title = title
        self.subtitle = subtitle
        self.target = target
        self.keywords = keywords
        self.score = score

# Search result that matches an installed server
class ServerResult(SearchObject):
    def __init__(self, title, subtitle, target, keywords=[], score=0, telepath=None):
        super().__init__()
        self._telepath_data = telepath
        self.type = 'server'
        self.icon = os.path.join(gui_assets, 'icons', 'sm', 'terminal.png')
        self.color = (1, 0.598, 0.9, 1)

        if self._telepath_data:
            self.title = f'[color=#9383A2]{self._telepath_data["display-name"]}/[/color]{self._telepath_data["name"]}'
        else:
            self.title = title
        self.subtitle = subtitle
        self.target = target
        self.keywords = keywords
        self.score = score

# Search result that matches a configuration page
class ScreenResult(SearchObject):
    def __init__(self, title, subtitle, target, keywords=[], score=0):
        super().__init__()
        self.type = 'screen'
        self.icon = os.path.join(gui_assets, 'icons', 'exit-sharp.png')
        self.color = (0.639, 1, 1, 1)
        self.title = title
        self.subtitle = subtitle
        self.target = target
        self.keywords = keywords
        self.score = score
