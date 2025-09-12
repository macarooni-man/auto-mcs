from shutil import rmtree, copytree, copy, ignore_patterns, move, disk_usage
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime as dt, date
from colorama import Fore, Back, Style
from random import randrange, choices
from difflib import SequenceMatcher
from urllib.parse import quote
from collections import deque
from bs4 import BeautifulSoup
from threading import Timer
from copy import deepcopy
from pathlib import Path
from munch import Munch
import multiprocessing
from glob import glob
from PIL import Image
from nbt import nbt
import configparser
import cloudscraper
import unicodedata
import subprocess
import functools
import threading
import traceback
import platform
import requests
import tempfile
import tarfile
import zipfile
import hashlib
import string
import psutil
import socket
import shlex
import queue
import stat
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

app_version = "2.3.3"
ams_version = "1.4.1"
telepath_version = "1.1.2"
app_title = "auto-mcs"

dev_version  = False
refresh_rate = 60
anim_speed   = 1
last_window  = {}
window_size  = (850, 850)
project_link = "https://github.com/macarooni-man/auto-mcs"
website      = "https://auto-mcs.com"
update_data  = {
    "version":    '',
    "urls":       {'windows': None, 'linux': None, 'linux-arm64': None, 'macos': None},
    "md5":        {'windows': None, 'linux': None, 'linux-arm64': None, 'macos': None},
    "desc":       '',
    "reboot-msg": [],
    "auto-show":  True
}
app_online      = False
app_latest      = True
app_loaded      = False
version_loading = False
screen_tree     = []
back_clicked    = False
session_splash  = ''
boot_launches   = []
restart_flag    = False
bypass_admin_warning = False
is_child_process = multiprocessing.current_process().name != "MainProcess"


# Global debug mode and app_compiled, set debug to false before release
debug          = False
enable_logging = True
app_compiled   = getattr(sys, 'frozen', False)

public_ip   = ""
footer_path = ""
last_widget = None

update_list = {}
addon_cache = {}

latestMC = {
    "vanilla":     "0.0.0",
    "forge":       "0.0.0",
    "neoforge":    "0.0.0",
    "paper":       "0.0.0",
    "purpur":      "0.0.0",
    "spigot":      "0.0.0",
    "craftbukkit": "0.0.0",
    "fabric":      "0.0.0",
    "quilt":       "0.0.0",

    "builds": {
        "forge":    "0",
        "paper":    "0",
        "purpur":   "0",
        "fabric":   "0",
        "neoforge": "0",
        "quilt":    "0"
    }
}

# Prevent running or importing servers while these are blank
java_executable = {
    "modern": None,
    "legacy": None,
    "lts":    None,
    "jar":    None
}

# Change this back when not testing
startup_screen = 'MainMenuScreen'

fonts = {
    'regular':      'Figtree-Regular',
    'medium':       'Figtree-Medium',
    'bold':         'Figtree-Bold',
    'very-bold':    'Figtree-ExtraBold',
    'italic':       'ProductSans-BoldItalic',
    'mono-regular': 'Inconsolata-Regular',
    'mono-medium':  'Mono-Medium',
    'mono-bold':    'Mono-Bold',
    'mono-italic':  'SometypeMono-RegularItalic',
    'icons':        'SosaRegular.ttf'
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

background_color  = (0.115, 0.115, 0.182, 1)
server_list       = []
server_list_lower = []
new_server_info   = {}
sub_processes     = []


# For '*.bat' or '*.sh' respectively
start_script_name = "Start"

# Oldest version that supports files like "ops.json" format
json_format_floor = "1.7.6"


# Paths
os_name = 'windows' if os.name == 'nt' else \
          'macos' if platform.system().lower() == 'darwin' else \
          'linux' if os.name == 'posix' else os.name

home    = os.path.expanduser('~')
appdata = os.getenv("APPDATA") if os_name == 'windows' else f'{home}/Library/Application Support' if os_name == 'macos' else home
applicationFolder = os.path.join(appdata, ('.auto-mcs' if os_name != 'macos' else 'auto-mcs'))

saveFolder    = os.path.join(appdata, '.minecraft', 'saves') if os_name != 'macos' else f"{home}/Library/Application Support/minecraft/saves"
downDir       = os.path.join(applicationFolder, 'Downloads')
uploadDir     = os.path.join(applicationFolder, 'Uploads')
backupFolder  = os.path.join(applicationFolder, 'Backups')
userDownloads = os.path.join(home, 'Downloads')
serverDir     = os.path.join(applicationFolder, 'Servers')
toolDir       = os.path.join(applicationFolder, 'Tools')
scriptDir     = os.path.join(toolDir, 'amscript')

tempDir     = os.path.join(applicationFolder, 'Temp')
tmpsvr      = os.path.join(tempDir, 'tmpsvr')
cacheDir    = os.path.join(applicationFolder, 'Cache')
templateDir = os.path.join(toolDir, 'templates')
configDir   = os.path.join(applicationFolder, 'Config')
javaDir     = os.path.join(toolDir, 'java')
os_temp     = os.getenv("TEMP") if os_name == "windows" else "/tmp"

max_log_count = 25

telepathDir       = os.path.join(toolDir, 'telepath')
telepathFile      = os.path.join(telepathDir, 'telepath-servers.json')
telepathSecrets   = os.path.join(telepathDir, 'telepath-secrets')
telepathScriptDir = os.path.join(scriptDir, 'telepath-temp')

username = ''
hostname = ''

server_ini  = 'auto-mcs.ini' if os_name == "windows" else '.auto-mcs.ini'
command_tmp = 'start-cmd.tmp' if os_name == "windows" else '.start-cmd.tmp'
script_obj  = None

text_logo = [
    "                           _                                 ",
    "   ▄▄████▄▄     __ _ _   _| |_ ___       _ __ ___   ___ ___  ",
    "  ▄█  ██  █▄   / _` | | | | __/ _ \  __ | '_ ` _ \ / __/ __| ",
    "  ███▀  ▀███  | (_| | |_| | || (_) |(__)| | | | | | (__\__ \ ",
    "  ▀██ ▄▄ ██▀   \__,_|\__,_|\__\___/     |_| |_| |_|\___|___/ ",
    "   ▀▀████▀▀                                                  ",
    ""
]


# Format OS as a string
def format_os() -> str:

    # System architecture (this app only supports 64-bit) ----------------------------
    arch_map = {
        "amd64": "64-bit", "x86_64": "64-bit",
        "aarch64": "ARM 64-bit", "arm64": "ARM 64-bit"
    }
    arch = arch_map.get(platform.machine().lower(), 'Unknown architecture')

    # Windows ------------------------------------------------------------------------
    def _windows_info() -> (str, str):
        data = platform.uname()
        product = data.system
        if 'server' in data.release.lower(): release = f'Server {data.release.lower().replace("server","").strip()}'
        else: release = data.release.strip()

        if '.' in data.version: build = data.version.rsplit('.')[-1]
        else: build = data.version.strip()

        return f'{product} {release}', build

    # macOS --------------------------------------------------------------------------
    def _mac_info() -> (str, str):
        version = None
        build = None
        for line in subprocess.check_output(["sw_vers"], text=True).strip().splitlines():
            if line.startswith('ProductVersion:'): version = line.split(':', 1)[-1].strip()
            if line.startswith('BuildVersion:'): build = line.split(':', 1)[-1].strip()

        if version: product = f'macOS {version}'
        else: product = 'macOS'

        return product, build

    # Linux --------------------------------------------------------------------------
    def _linux_info() -> (str, str):
        distro_name = None
        distro_id   = None
        try:
            with open("/etc/os-release", encoding="utf-8") as fp:
                for line in fp:
                    if line.startswith("NAME="): distro_name = line.split("=", 1)[-1].strip().strip('"')
                    if line.startswith("VERSION_ID="): distro_id = line.split("=", 1)[-1].strip().strip('"')
        except FileNotFoundError: pass

        if distro_name and distro_id: product = f'{distro_name} {distro_id}'
        else: product = 'Linux'

        kernel = platform.release()
        if '-' in kernel: kernel = kernel.split('-', 1)[0]
        if kernel.count('.') > 2: kernel = '.'.join(kernel.split('.')[:3])
        return product, kernel

    if os_name == "windows":
        name, version = _windows_info()
        return f"{name} (b-{version}, {arch})"

    elif os_name == "macos":
        name, version = _mac_info()
        return f"{name} (b-{version}, {arch})"

    elif os_name == "linux":
        distro, kernel = _linux_info()
        return f"{distro} (k-{kernel}, {arch})"

    else: return f'Unknown OS ({arch})'


# Format CPU as a string
def format_cpu() -> str:
    cpu_arch = platform.architecture()
    if len(cpu_arch) > 1: cpu_arch = cpu_arch[0]
    return f"{psutil.cpu_count(False)} ({psutil.cpu_count()}) C/T @ {round((psutil.cpu_freq().max) / 1000, 2)} GHz ({cpu_arch.replace('bit', '-bit')})"


# Format RAM as a string
def format_ram() -> str:
    return f"{round(psutil.virtual_memory().used / 1073741824, 2)} / {round(psutil.virtual_memory().total / 1073741824)} GB"


# Returns full error into a string for logging
def format_traceback(exception: Exception) -> str:
    last_trace = traceback.format_exc()
    return f'{exception}\nTraceback:\n{last_trace}'


# Creates a boot log for logger
boot_arguments = None
def send_boot_log(object_data: str):
    global boot_arguments, headless
    log_args = ' '.join([
        (f'--{k}' if isinstance(v, bool) else f'--{k} "{v}"')
        for k, v in vars(deepcopy(boot_arguments)).items() if v
    ])

    data_list = [
        f'Version:           {app_version} - {format_os()}',
        f'Launch flags:      {log_args if log_args else None}',
        f'Online:            {app_online}',
        f'Permissions:       {"Admin-level" if is_admin() else "User-level"}',
        f'UI Language:       {get_locale_string(True)}',
        f'Headless:          {"True" if headless else "False"}',
        f'Telepath server:   {"Active" if api_manager.running else "Inactive"}',
        f'Processor info:    {format_cpu()}',
        f'Used memory:       {format_ram()}'
    ]

    formatted_properties = "\n".join(data_list)
    send_log(object_data, f'initializing {app_title} with the following properties:\n{formatted_properties}', 'info')


# App/Assets folder
launch_path: str = None
try:
    if hasattr(sys, '_MEIPASS'):
        executable_folder = sys._MEIPASS
        gui_assets = os.path.join(executable_folder, 'gui-assets')
    else:
        executable_folder = os.path.abspath(".")
        gui_assets = os.path.join(executable_folder, 'gui-assets')

except FileNotFoundError:
    executable_folder = '.'
    gui_assets = os.path.join(executable_folder, 'gui-assets')


# API stuff
def get_private_ip():
    global is_docker

    # Try to get the host IP first if running in Docker
    if is_docker:
        try:
            host = socket.gethostbyname("host.docker.internal")
            if host and not host.startswith("127."): return host
        except Exception: pass

    # Otherwise, get the default static route
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(0)
        try:
            # doesn't even have to be reachable
            s.connect(('10.254.254.254', 1))
            return s.getsockname()[0]
        except Exception: pass

    return '127.0.0.1'


def sync_attr(self, name):
    if name != '__all__':
        return getattr(self, name)
    else:
        blacklist = ['addon', 'backup', 'acl', 'script_manager', 'script_object', 'run_data', 'taskbar']
        def allow(x):
            return ((not callable(getattr(self, x))) and (str(x) not in blacklist) and (not str(x).endswith('__')))
        return {a: getattr(self, a) for a in dir(self) if allow(a)}
api_manager: 'telepath.TelepathManager' = None
headless = False

# Prevent app from closing during critical operations
ignore_close        = False
telepath_banner     = None
telepath_pair       = None
telepath_disconnect = None
def allow_close(allow: bool, banner=''):
    global ignore_close
    ignore_close = not allow

    # Log that window was locked/unlocked
    verb        = 'locked' if ignore_close else 'unlocked'
    banner_verb = f'with banner: {banner}' if banner else 'with no banner'
    send_log('allow_close', f'{verb} GUI window {banner_verb}')

    if banner and telepath_banner and app_config.telepath_settings['show-banners']:
        telepath_banner(banner, allow)

discord_presence = None


# SSL crap when compiled
if os_name == 'linux' and app_compiled:
    os.environ['SSL_CERT_DIR'] = executable_folder
    os.environ['SSL_CERT_FILE'] = os.path.join(executable_folder, 'ca-bundle.crt')

elif os_name == 'macos' and app_compiled:
    os.environ['SSL_CERT_DIR'] = os.path.join(executable_folder, 'certifi')
    os.environ['SSL_CERT_FILE'] = os.path.join(executable_folder, 'certifi', 'cacert.pem')



# Bigboi server manager
server_manager: 'svrmgr.ServerManager' = None
search_manager: 'SearchManager' = None
import_data    = {'name': None, 'path': None}
backup_lock    = {}


# Maximum memory
total_ram  = round(psutil.virtual_memory().total / 1073741824)
max_memory = int(round(total_ram - (total_ram / 4)))

# Replacement for os.system to prevent CMD flashing, and also for debug logging
def run_proc(cmd: str, return_text=False) -> str or int:
    std_setting = subprocess.PIPE

    result = subprocess.run(
        cmd,
        shell  = True,
        stdout = std_setting,
        stderr = std_setting,
        text   = True,
        errors = 'ignore'
    )

    output = result.stdout or result.stderr or ''
    return_code = result.returncode
    run_content = f'\n{output.strip()}'
    log_content = f'with output:{run_content}' if run_content.strip() else 'with no output'
    send_log('run_proc', f"'{cmd}': returned exit code {result.returncode} {log_content}", None if return_code == 0 else 'error')

    return output if return_text else return_code


# Spawns a detached process with new process group
def run_detached(script_path: str):
    send_log('run_detached', f"executing '{script_path}'...")

    if os_name == 'windows':
        return subprocess.Popen(
            ['cmd', '/c', script_path],
            stdout = subprocess.DEVNULL,
            stderr = subprocess.DEVNULL,
            stdin = subprocess.DEVNULL,
            creationflags = 0x00000008
        )

    # macOS & Linux
    os.chmod(script_path, stat.S_IRWXU)
    args = ['bash', script_path]
    if os_name != 'macos': args.insert(0, 'setsid')
    subprocess.Popen(
        args,
        stdout = subprocess.DEVNULL,
        stderr = subprocess.DEVNULL,
        stdin = subprocess.DEVNULL,
        start_new_session = True,
        close_fds = True
    )


# Retrieves the best-guess TTY device path to the terminal that launched it
def get_parent_tty() -> str or None:
    # Windows doesn't have a terminal
    if os_name == 'windows': return None

    # If there's a TTY in STDIO, just use that
    for fd in (1, 0, 2):
        try:
            if os.isatty(fd): return shlex.quote(os.ttyname(fd))
        except Exception: pass

    # On Linux, try '/proc/self/fd' symlinks
    if os_name == 'linux' and os.path.exists('/proc/self/fd'):
        for fd in (1, 0, 2):
            try:
                p = os.readlink(f'/proc/self/fd/{fd}')
                if p.startswith('/dev/'): return shlex.quote(p)
            except Exception: pass

    # If that doesn't work, ask 'ps' for TTY of this PID and walk up the process tree
    def _ps_col(pid: int, col: str):
        try:
            out = subprocess.check_output(['ps', '-o', f'{col}=', '-p', str(pid)], stderr=subprocess.DEVNULL, text=True).strip()
            if out: return shlex.quote(out)
            return None
        except Exception: return None

    def _ps_tty(pid: int):
        t = _ps_col(pid, 'tty')
        if t and t != '?' and t.lower() != 'ttys??':
            # ps returns like 'pts/3' or 'ttys002'
            return shlex.quote(t) if t.startswith('/dev/') else f'/dev/{t}'
        return None

    # Try current process and then a few ancestors
    pid = os.getpid()
    tty = _ps_tty(pid)
    if tty: return shlex.quote(tty)
    ppid_seen = set()
    ppid = os.getppid()

    # Don't walk indefinitely
    for _ in range(5):
        if not ppid or ppid in ppid_seen: break
        ppid_seen.add(ppid)
        tty = _ps_tty(ppid)
        if tty: return shlex.quote(tty)

        p = _ps_col(ppid, 'ppid')
        try: ppid = int(p) if p else None
        except Exception: ppid = None

    return None


# Check if running in Docker
def check_docker() -> bool:
    if os_name == 'linux':
        if 'Alpine' in run_proc('uname -v', True).strip():
            return True
    cgroup = Path('/proc/self/cgroup')
    docker_check = Path('/.dockerenv').is_file() or cgroup.is_file() and 'docker' in cgroup.read_text()
    if docker_check: send_log('check_docker', f'{app_title} is running inside a Docker container')
    return docker_check
is_docker: bool

# Check if OS is ARM
def check_arm() -> bool:
    command = 'echo %PROCESSOR_ARCHITECTURE%' if os_name == 'windows' else 'uname -m'
    arch = run_proc(command, True).strip()
    return arch in ['aarch64', 'arm64']
is_arm: bool



# Global amscripts

# Grabs amscript files from GitHub repo for downloading internally
ams_web_list = []
def get_repo_scripts() -> list:
    global ams_web_list
    try:
        latest_commit = requests.get("https://api.github.com/repos/macarooni-man/auto-mcs/commits").json()[0]['sha']
        repo_data = requests.get(f"https://api.github.com/repos/macarooni-man/auto-mcs/git/trees/{latest_commit}?recursive=1").json()

        script_dict = {}
        ams_list = []
        root_url = "https://raw.githubusercontent.com/macarooni-man/auto-mcs/main/"

        # Organize all script files
        for file in repo_data['tree']:
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



# Global templates

# Parse template file into a Python object
def parse_template(path) -> dict:
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            data = yaml.safe_load(f.read())
            if latestMC[data['server']['type']] == '0.0.0':
                while latestMC[data['server']['type']] == '0.0.0':
                    time.sleep(0.1)
            if data['server']['version'] == 'latest':
                data['server']['version'] = latestMC[data['server']['type']]
            return data
    except:
        return {}


# Apply template to new_server_info
def apply_template(template: dict):
    global new_server_info

    # Get telepath data
    telepath_data = None
    name_list = server_list_lower
    if new_server_info:
        telepath_data = new_server_info['_telepath_data']

    new_server_init()

    if telepath_data:
        new_server_info['_telepath_data'] = telepath_data
        name_list = get_remote_var('server_list_lower', telepath_data)

    t = template['server']
    s = t['settings']

    new_server_info["name"] = new_server_name(template['template']['name'], name_list)
    new_server_info["type"] = t["type"]
    new_server_info["version"] = t["version"]
    new_server_info['server_settings']["world"] = "world" if not s["world"]["path"] else s["world"]["path"]
    new_server_info['server_settings']["seed"] = "" if not s["world"]["seed"] else s["world"]["seed"]
    new_server_info['server_settings']["level_type"] = s["world"]["level_type"]
    new_server_info['server_settings']["difficulty"] = s["difficulty"]
    new_server_info['server_settings']["gamemode"] = s["gamemode"]
    new_server_info['server_settings']["spawn_creatures"] = s["spawn_creatures"]
    new_server_info['server_settings']["spawn_protection"] = s["spawn_protection"]
    new_server_info['server_settings']["pvp"] = s["pvp"]
    new_server_info['server_settings']["max_players"] = str(s["max_players"])
    new_server_info['server_settings']["keep_inventory"] = s["keep_inventory"]
    new_server_info['server_settings']["daylight_weather_cycle"] = s["daylight_weather_cycle"]
    new_server_info['server_settings']["command_blocks"] = s["command_blocks"]
    new_server_info['server_settings']["random_tick_speed"] = str(s['random_tick_speed'])
    new_server_info['server_settings']["geyser_support"] = s['geyser_support']
    new_server_info['server_settings']["disable_chat_reporting"] = s['disable_chat_reporting']
    new_server_info['server_settings']["enable_proxy"] = s['playit']

    # Get add-ons
    if s['addons']:
        new_server_info['addon_objects'] = [a for a in [addons.find_addon(a, new_server_info) for a in s['addons']] if a]

    # Initialize AclManager
    from acl import AclManager
    new_server_info['acl_object'] = AclManager(new_server_info['name'])

    send_log('apply_template', f"applied '.ist' template '{template['template']['name']}': {template}")


# Grabs instant server template (.ist) files from GitHub repo
ist_data = {}
def get_repo_templates():
    global ist_data

    if ist_data:
        return

    if not os.path.exists(templateDir):

        try:
            latest_commit = requests.get("https://api.github.com/repos/macarooni-man/auto-mcs/commits").json()[0]['sha']
            repo_data = requests.get(f"https://api.github.com/repos/macarooni-man/auto-mcs/git/trees/{latest_commit}?recursive=1").json()

            # Organize all script files
            folder_check(templateDir)
            for file in repo_data['tree']:
                if file['path'].startswith('template-library'):
                    if "/" in file['path']:
                        file_name = file['path'].split("/")[1]
                        url = f'https://raw.githubusercontent.com/macarooni-man/auto-mcs/refs/heads/main/{quote(file["path"])}'
                        download_url(url, file_name, templateDir)
        except: ist_data = {}


    if os.path.exists(templateDir):
        for ist in glob(os.path.join(templateDir, '*.yml')):
            data = parse_template(ist)
            if ist not in ist_data:
                ist_data[os.path.basename(ist)] = data



# ---------------------------------------------- Global Functions ------------------------------------------------------

# Functions and data for translation
locale_file = os.path.join(executable_folder, 'locales.json')
locale_data = {}
if os.path.isfile(locale_file):
    with open(locale_file, 'r', encoding='utf-8', errors='ignore') as f:
        locale_data = json.load(f)
available_locales = {
    "English":    {"name": 'English', "code": 'en'},
    "Spanish":    {"name": 'Español', "code": 'es'},
    "French":     {"name": 'Français', "code": 'fr'},
    "Italian":    {"name": 'Italiano', "code": 'it'},
    "German":     {"name": 'Deutsch', "code": 'de'},
    "Dutch":      {"name": 'Nederlands', "code": 'nl'},
    "Portuguese": {"name": 'Português', "code": 'pt'},
    "Swedish":    {"name": 'Suédois', "code": 'sv'},
    "Finnish":    {"name": 'Suomi', "code": 'fi'},
    "English 2":  {"name": 'English 2', "code": 'e2'}

    # Requires special fonts:

    # "Chinese":  {"name": '中文', "code": 'zh-CN'},
    # "Japanese": {"name": '日本語', "code": 'ja'},
    # "Korean":   {"name": '한국어', "code": 'ko'},
    # "Arabic":   {"name": 'العربية', "code": 'ar'},
    # "Russian":  {"name": 'Русский', "code": 'ru'},
    # "Ukranian": {"name": 'Українська', "code": 'uk'},
    # "Serbian":  {"name": 'Cрпски', "code": 'sr'},
    # "Japanese": {"name": '日本語', "code": 'ja'}
}

# Return formatted locale string: 'Title (code)'
# 'english' = True, Title should display in English, native if False
def get_locale_string(english=False, *a) -> str:
    for k, v in available_locales.items():
        if app_config.locale in v.values():
            return f'{k if english else v["name"]} ({v["code"]})'


# Translate any string into relevant locale
def translate(text: str) -> str:
    global locale_data, app_config

    # Ignore if text is blank, or locale is set to english
    if not text.strip() or app_config.locale.startswith('en'):
        return text


    # Searches locale_data for string
    def search_data(s, *a):
        try: return locale_data[s.strip().lower()][app_config.locale]
        except KeyError: pass
        try: return locale_data[s.strip()][app_config.locale]
        except KeyError: pass


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
            try: return locale_data[s.group(0).strip().lower()][app_config.locale]
            except KeyError: pass
            return s.group(0)
        new_text = re.sub(r'\b\S+\b', match_data, text)


    # If a match was found, return text in its original case
    if new_text:

        # Escape proper nouns that ignore translation
        overrides = ('server.properties', 'server.jar', 'amscript', 'Geyser', 'Java', 'GB', '.zip', 'Telepath', 'telepath', 'ngrok', 'playit')
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
        if app_config.locale == 'es':
            new_text = re.sub('servidor\.properties', 'server.properties', new_text, re.IGNORECASE)
            new_text = re.sub('servidor\.jar', 'server.jar', new_text, re.IGNORECASE)
            new_text = re.sub('control S', 'Administrar', new_text, re.IGNORECASE)
        if app_config.locale == 'it':
            new_text = re.sub(r'ESENTATO', 'ESCI', new_text, re.IGNORECASE)
        if app_config.locale == 'fr':
            new_text = re.sub(r'moire \(Go\)', 'moire (GB)', new_text, re.IGNORECASE)
            new_text = re.sub(r'dos', 'retour', new_text, re.IGNORECASE)


        # Get the spacing in front and after the text
        if text.startswith(' ') or text.endswith(' '):
            try: before = re.search(r'(^\s+)', text).group(1)
            except: before = ''
            try: after = re.search(r'(?=.*)(\s+$)', text).group(1)
            except: after = ''
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
    else: return re.sub(r'\$(.*)\$', '\g<1>', text)


# Returns False if less than 15GB free
def check_free_space(telepath_data: dict = None, required_free_space: int = 15) -> bool:
    if telepath_data:
        try:
            return str(api_manager.request(
                endpoint = '/main/check_free_space',
                host = telepath_data['host'],
                port = telepath_data['port']
            )).lower() == 'true'
        except:
            return False

    free_space = round(disk_usage('/').free / 1048576)
    enough_space = free_space > 1024 * required_free_space
    action = 'has enough' if enough_space else 'does not have enough'
    send_log('check_free_space', f'primary disk {action} free space: {round(free_space/1024, 2)} GB / {required_free_space} GB', None if enough_space else 'error')
    return enough_space


# Returns to Telepath clients that this instance is set to 'ignore_close'
def telepath_busy() -> bool:
    return ignore_close and server_manager.remote_servers


# Retrieves the refresh rate of the display to calculate consistent animation speed
def get_refresh_rate() -> float or None:
    if headless: return
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
    except: pass


# Check for admin rights
admin_check_logged = False
def is_admin() -> bool:
    global admin_check_logged
    try:

        # Admin check on Windows
        if os_name == 'windows':
            import ctypes
            elevated = ctypes.windll.shell32.IsUserAnAdmin() == 1

        # Root user check on Unix-based systems
        else: elevated = os.getuid() == 0

    # If this check fails, it's not running as admin
    except:   elevated = False


    # Log startup permissions (this only needs to be logged once, but is checked multiple times)
    if not admin_check_logged:
        if elevated: send_log('is_admin', f'{app_title} is running with admin-level permissions', 'warning')
        else:        send_log('is_admin', f'{app_title} is running with user-level permissions')
        admin_check_logged = True

    return elevated


# Returns true if latest is greater than current
def check_app_version(current: str, latest: str, limit=None) -> bool:

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


# Restarts auto-mcs by dynamically generating a script
def restart_app(*a):
    global restart_flag

    if not app_compiled:
        return send_log('restart_app', "can't restart in script mode", 'warning')

    # Setup environment
    retry_wait = 30
    tty = get_parent_tty()
    executable = os.path.basename(launch_path)
    script_name = 'auto-mcs-reboot'
    script_path = None
    restart_flag = True
    flags = f"{' --debug' if debug else ''}{' --headless' if headless else ''}"
    folder_check(tempDir)
    send_log('restart_app', f'attempting to restart {app_title}...', 'warning')



    # Generate Windows script to restart
    if os_name == "windows":
        script_name = f'{script_name}.bat'
        script_path = os.path.join(tempDir, script_name)

        with open(script_path, 'w+') as script:
            script_content = (

f""":: Kill the process
taskkill /f /im \"{executable}\"

:: Wait for it to exit (max {retry_wait}s)
set /a count=0
:waitloop
tasklist /fi "imagename eq {executable}" | find /i \"{executable}\" >nul
if %errorlevel%==0 (
    timeout /t 1 /nobreak >nul
    set /a count+=1
    if %count% LSS {retry_wait} goto waitloop
)

:: Launch the original executable
start \"\" \"{launch_path}\"{flags}
del \"{script_path}\"""")

            script.write(script_content)
            send_log('restart_app', f"writing to '{script_path}':\n{script_content}")

        run_proc(f"\"{script_path}\" > nul 2>&1")
        sys.exit(0)



    # Generate Linux/macOS script to restart
    else:
        script_name = f'{script_name}.sh'
        script_path = os.path.join(tempDir, script_name)
        escaped_launch_path = shlex.quote(launch_path)

        with open(script_path, 'w+') as script:
            script_content = (

f"""#!/bin/bash
PID={os.getpid()}

# Kill the process
kill "$PID"

# Wait for it to exit (max {retry_wait}s)
for i in {{1..{retry_wait}}}; do
    if ! kill -0 "$PID" 2>/dev/null; then
        break
    fi
    sleep 1
done

# Force kill if it's still not closed
if kill -0 "$PID" 2>/dev/null; then
    kill -9 "$PID" 2>/dev/null
fi

# Launch the original executable
TTY={tty}
if [ -n "$TTY" ] && [ -e "$TTY" ] && [ -w "$TTY" ]; then
    # Reuse the original terminal for STDIO
    exec {escaped_launch_path}{flags} <"$TTY" >"$TTY" 2>&1 &
else
    # Original terminal wasn't found, background quietly
    exec {escaped_launch_path}{flags} >/dev/null 2>&1 &
fi
rm \"{script_path}\"""")

            script.write(script_content)
            send_log('restart_app', f"writing to '{script_path}':\n{script_content}")

    run_detached(script_path)
    sys.exit(0)


# Restarts and updates auto-mcs by dynamically generating a script
def restart_update_app(*a):
    global restart_flag

    if not app_compiled:
        return send_log('restart_update_app', "can't restart in script mode", 'warning')

    # Setup environment
    retry_wait = 30
    tty = get_parent_tty()
    executable = os.path.basename(launch_path)
    script_name = 'auto-mcs-update'
    script_path = None
    restart_flag = True
    flags = f"{' --debug' if debug else ''}{' --headless' if headless else ''}"
    folder_check(tempDir)

    new_version  = update_data['version']
    success_str  = f"auto-mcs was updated to v${new_version}$ successfully!"
    success_unix = f"auto-mcs was updated to v\${new_version}\$ successfully!"
    failure_str  = "Something went wrong with the update"
    script_name  = 'auto-mcs-update'
    update_log   = os.path.join(tempDir, 'update-log')
    send_log('restart_update_app', f'attempting to restart {app_title} and update to v{new_version}...', 'warning')


    # Delete guide cache for the next update
    guide_cache = os.path.join(cacheDir, 'guide-cache.json')
    if os.path.exists(guide_cache):
        try: os.remove(guide_cache)
        except: pass



    # Generate Windows script to restart
    if os_name == "windows":
        script_name = f'{script_name}.bat'
        script_path = os.path.join(tempDir, script_name)
        new_executable = os.path.join(downDir, 'auto-mcs.exe')

        with open(script_path, 'w+') as script:
            script_content = (

f""":: Kill the process
taskkill /f /im \"{executable}\"

:: Wait for it to exit (max {retry_wait}s)
set /a count=0
:waitloop
tasklist /fi "imagename eq {executable}" | find /i \"{executable}\" >nul
if %errorlevel%==0 (
    timeout /t 1 /nobreak >nul
    set /a count+=1
    if %count% LSS {retry_wait} goto waitloop
)

:: Copy new update file to original path
copy /b /v /y "{new_executable}" "{launch_path}"
if exist "{launch_path}" if %ERRORLEVEL% EQU 0 (
    echo banner-success@{success_str} > "{update_log}"
) else (
    echo banner-failure@{failure_str} > "{update_log}"
)

:: Launch the new executable
start \"\" \"{launch_path}\"{flags}
del \"{script_path}\"""")

            script.write(script_content)
            send_log('restart_update_app', f"writing to '{script_path}':\n{script_content}")

        run_proc(f"\"{script_path}\" > nul 2>&1")
        sys.exit(0)



    # Generate macOS script to restart
    elif os_name == 'macos':
        script_name = f'{script_name}.sh'
        script_path = os.path.join(tempDir, script_name)
        escaped_launch_path = shlex.quote(launch_path)
        dmg_path = os.path.join(downDir, 'auto-mcs.dmg')

        with open(script_path, 'w+') as script:
            script_content = (

f"""#!/bin/bash
PID={os.getpid()}

# Kill the process
kill "$PID"

# Wait for it to exit (max {retry_wait}s)
for i in {{1..{retry_wait}}}; do
    if ! kill -0 "$PID" 2>/dev/null; then
        break
    fi
    sleep 1
done

# Force kill if it's still not closed
if kill -0 "$PID" 2>/dev/null; then
    kill -9 "$PID" 2>/dev/null
fi

# Utilize rsync to update the old app contents in place
hdiutil mount "{dmg_path}"
rsync -a /Volumes/auto-mcs/auto-mcs.app/ "{os.path.join(os.path.dirname(launch_path), '../..')}"
errorlevel=$?
if [ -f "{launch_path}" ] && [ $errorlevel -eq 0 ]; then
    echo banner-success@{success_unix} > "{update_log}"
else
    echo banner-failure@{failure_str} > "{update_log}"
fi

# Remove the update disk
hdiutil unmount /Volumes/auto-mcs
rm -rf "{dmg_path}"

# Launch the new executable
chmod +x "{launch_path}"
TTY={tty}
if [ -n "$TTY" ] && [ -e "$TTY" ] && [ -w "$TTY" ]; then
    # Reuse the original terminal for STDIO
    exec {escaped_launch_path}{flags} <"$TTY" >"$TTY" 2>&1 &
else
    # Original terminal wasn't found, background quietly
    exec {escaped_launch_path}{flags} >/dev/null 2>&1 &
fi
rm \"{script_path}\"""")

            script.write(script_content)
            send_log('restart_update_app', f"writing to '{script_path}':\n{script_content}")

        run_proc(f"chmod +x \"{script_path}\" && bash \"{script_path}\" > /dev/null 2>&1")
        sys.exit(0)



    # Generate Linux script to restart
    else:
        script_name = f'{script_name}.sh'
        script_path = os.path.join(tempDir, script_name)
        escaped_launch_path = shlex.quote(launch_path)
        new_executable = os.path.join(downDir, 'auto-mcs')

        with open(script_path, 'w+') as script:
            script_content = (

f"""#!/bin/bash
PID={os.getpid()}

# Kill the process
kill "$PID"

# Wait for it to exit (max {retry_wait}s)
for i in {{1..{retry_wait}}}; do
    if ! kill -0 "$PID" 2>/dev/null; then
        break
    fi
    sleep 1
done

# Force kill if it's still not closed
if kill -0 "$PID" 2>/dev/null; then
    kill -9 "$PID" 2>/dev/null
fi

# Copy new update file to original path
/bin/cp -rf "{new_executable}" "{launch_path}"
errorlevel=$?
if [ -f "{launch_path}" ] && [ $errorlevel -eq 0 ]; then
    echo banner-success@{success_unix} > "{update_log}"
else
    echo banner-failure@{failure_str} > "{update_log}"
fi

# Launch the new executable
chmod +x "{launch_path}"
TTY={tty}
if [ -n "$TTY" ] && [ -e "$TTY" ] && [ -w "$TTY" ]; then
    # Reuse the original terminal for STDIO
    exec {escaped_launch_path}{flags} <"$TTY" >"$TTY" 2>&1 &
else
    # Original terminal wasn't found, background quietly
    exec {escaped_launch_path}{flags} >/dev/null 2>&1 &
fi
rm \"{script_path}\"""")

            script.write(script_content)
            send_log('restart_update_app', f"writing to '{script_path}':\n{script_content}")

    run_detached(script_path)
    sys.exit(0)


# Format date string to be cross-platform compatible
def fmt_date(date_string: str):
    if os_name == 'windows': return date_string
    else: return date_string.replace('%#','%-')


# Returns current formatted time
def format_now():
    return dt.now().strftime(fmt_date("%#I:%M:%S %p"))


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
def convert_color(color: str or tuple) -> dict:

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


# Returns modified color tuple or HEX string
def brighten_color(color: tuple or str, amount: float) -> tuple or str:

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
def similarity(a: str, b: str) -> float:
    return round(SequenceMatcher(None, a, b).ratio(), 2)


# Cloudscraper requests
global_scraper = None
def return_scraper(url_path: str, head=False, params=None) -> requests.Response:
    global global_scraper

    if not global_scraper:
        global_scraper = cloudscraper.create_scraper(
            browser = {'custom': f'{app_title}/{app_version}', 'platform': os_name, 'mobile': False},
            # ecdhCurve = 'secp384r1',
            # debug = debug
        )

    return global_scraper.head(url_path) if head else global_scraper.get(url_path, params=params)


# Return html content or status code
def get_url(url: str, return_code=False, only_head=False, return_response=False, params=None) -> requests.Response:
    global global_scraper
    max_retries = 10
    for retry in range(0, max_retries + 1):
        try:
            html = return_scraper(url, head=(return_code or only_head), params=params)
            send_log('get_url', f"request to '{url}': {html.status_code}")
            return html.status_code if return_code \
                else html if (only_head or return_response) \
                else BeautifulSoup(html.content, 'html.parser')

        except cloudscraper.exceptions.CloudflareChallengeError as e:
            global_scraper = None
            if retry >= max_retries:
                send_log('get_url', f"exceeded max retries to '{url}': {format_traceback(e)}", 'error')
                raise ConnectionRefusedError("The cloudscraper connection has failed")
            else: time.sleep((retry / 3))

        except requests.exceptions.MissingSchema:
            pass

        except Exception as e:
            send_log('get_url', f"error requesting '{url}': {format_traceback(e)}", 'error')
            raise e


# Download file and return if the downloaded file exists
def cs_download_url(url: str, file_name: str, destination_path: str) -> bool:
    global global_scraper
    max_retries = 10
    send_log('cs_download_url', f"requesting from '{url}' to download '{file_name}' to '{destination_path}'...")
    for retry in range(0, max_retries + 1):
        try:
            web_file = return_scraper(url)
            full_path = os.path.join(destination_path, file_name)
            folder_check(destination_path)
            with open(full_path, 'wb') as file:
                file.write(web_file.content)

            send_log('cs_download_url', f"download of '{file_name}' complete: '{full_path}'")
            return os.path.exists(full_path)

        except cloudscraper.exceptions.CloudflareChallengeError as e:
            global_scraper = None
            if retry >= max_retries:
                send_log('cs_download_url', f"exceeded max retries to '{url}': {format_traceback(e)}", 'error')
                raise ConnectionRefusedError("The cloudscraper connection has failed")
            else: time.sleep((retry / 3))

        except Exception as e:
            send_log('cs_download_url', f"error requesting '{url}': {format_traceback(e)}", 'error')
            raise e


# Uploads a file or directory to a telepath session of auto-mcs -> destination path
def telepath_upload(telepath_data: dict, path: str) -> any:
    if not api_manager:
        return False

    if os.path.exists(path):
        is_dir = False

        # If path is a directory, compress to tmp and use the archive instead
        if os.path.isdir(path):
            is_dir = True
            path = create_archive(path, tempDir, 'tar')

        host = telepath_data['host']
        port = telepath_data['port']
        url = f"http://{host}:{port}/main/upload_file?is_dir={is_dir}"

        send_log('telepath_upload', f"uploading '{path}' to '{url}'...")
        session = api_manager._get_session(host, port)
        request = lambda: session.post(url, headers=api_manager._get_headers(host, True), files={'file': open(path, 'rb')})
        data = api_manager._retry_wrapper(host, port, request)

        if data: return data.json()
        else: send_log('telepath_upload', f"failed to upload to '{url}'", 'error')


# Downloads a file to a telepath session --> destination path
# Whitelist is for restricting downloadable content
telepath_download_whitelist = {
    'paths': [serverDir, scriptDir, backupFolder],
    'names': ['.ams', '.amb', 'server-icon.png']
}
def telepath_download(telepath_data: dict, path: str, destination=downDir, rename='') -> str:
    if not api_manager:
        return False

    host = telepath_data['host']
    port = telepath_data['port']
    url = f"http://{host}:{port}/main/download_file?file={quote(path)}"

    send_log('telepath_download', f"downloading '{url}' to '{destination}'...")
    session = api_manager._get_session(host, port)
    request = lambda: session.post(url, headers=api_manager._get_headers(host), stream=True)
    data = api_manager._retry_wrapper(host, port, request)

    # Save if the request was successful
    if data and data.status_code == 200:

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

        send_log('telepath_download', f"downloaded '{url}' to '{final_path}'")
        return final_path

    else: send_log('telepath_download', f"failed to download '{url}'", 'error')


# Delete all files in Telepath uploads remotely (this is executed from a client)
def clear_uploads() -> bool:
    safe_delete(uploadDir)
    send_log('clear_uploads', f"cleared Telepath uploads in '{uploadDir}'")
    return not os.path.exists(uploadDir)


# Gets a variable from this module, remotely if telepath_data is specified
def get_remote_var(var: str, telepath_data: dict = {}) -> any:
    if telepath_data:
        return api_manager.request(
            endpoint = '/main/get_remote_var',
            host = telepath_data['host'],
            port = telepath_data['port'],
            args = {'var': var}
        )

    else:
        try: var = getattr(sys.modules[__name__], var)
        except: var = None
        return var


# Removes invalid characters from a filename
def sanitize_name(value, addon=False) -> str:

    if value == 'WorldEdit for Bukkit':
        return 'WorldEdit'

    value = '-'.join([v.strip() for v in value.split(":")])
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\'\w\s-]', '', value)
    return re.sub(r'[-\s]+', '-', value).strip('-_')


# Removes invalid characters for a telepath nickname
def format_nickname(nickname) -> str:
    formatted = re.sub('[^a-zA-Z0-9 _().-]', '', nickname.lower())
    formatted = re.sub(r'[\s-]+', '-', formatted)

    # Remove leading and trailing hyphens
    formatted = formatted.strip('-')

    # If the length of the string is greater than 20 characters
    if len(formatted) > 20 and '-' in formatted:
        formatted = formatted.split('-', 1)[0]

    return formatted


# Comparison tool for Minecraft version strings
def version_check(version_a: str, comparator: str, version_b: str) -> bool:
    def parse_version(version):
        version = version.lower()
        # Split the version into parts, including handling pre-release (-preX)
        if "-pre" in version:
            main_version, pre_release = version.split("-pre", 1)
            parts = main_version.split(".") + [f"-{pre_release}"]
        else:
            parts = version.split(".")

        parsed = []
        for part in parts:
            # Handle pre-release identifiers
            if part.startswith("-pre"):
                parsed.append(-1000)  # Pre-release marker, always less than normal versions
                part = part.replace("-pre", "")
                if part.isdigit():
                    parsed.append(int(part))
            elif "a" in part:
                parsed.append(-2)  # 'a' is less than 'b'
                part = part.replace("a", "")
            elif "b" in part:
                parsed.append(-1)  # 'b' is less than normal numbers
                part = part.replace("b", "")
            if part.isdigit():
                parsed.append(int(part))
        return tuple(parsed)

    try:
        # Parse both versions into comparable tuples
        parsed_a = parse_version(version_a)
        parsed_b = parse_version(version_b)

        # Perform the comparison
        if comparator == ">":
            return parsed_a > parsed_b
        elif comparator == ">=":
            return parsed_a >= parsed_b
        elif comparator == "<":
            return parsed_a < parsed_b
        elif comparator == "<=":
            return parsed_a <= parsed_b
        elif comparator == "==":
            return parsed_a == parsed_b
        else:
            raise ValueError(f"Invalid comparator: {comparator}")
    except Exception as e:
        return False


# Check if level is compatible with server version
# Returns (True, "") if world is compatible, else (False, "world_version"). (False, None) if world has an unknown version
def check_world_version(world_path: str, server_version: str) -> tuple[bool, str or None]:

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

                with open(cache_file, 'r', encoding='utf-8', errors='ignore') as f:
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
def check_ip(addr: str, restrict=True) -> bool:

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

def check_subnet(addr: str) -> bool:
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
            send_log('folder_check', f"Created '{directory}'")
        except FileExistsError:
            pass
    else:
        send_log('folder_check', f"'{directory}' already exists")


# Open folder in default file browser, and highlight if file is passed
def open_folder(directory: str):
    try:
        send_log('open_folder', f"opening '{directory}' in file browser")

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
        send_log('open_folder', f"error opening '{directory}': {e}", 'warning')
        return False


# Get current directory, and revert to exec path if it doesn't exist
def get_cwd() -> str:
    # try: new_dir = os.path.abspath(os.curdir)
    # except: pass
    return executable_folder


# Extract archive
def extract_archive(archive_file: str, export_path: str, skip_root=False):
    archive = None
    archive_type = None

    send_log('extract_archive', f"extracting '{archive_file}' to '{export_path}'...")

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
                    rc = subprocess.call(['tar', '--help'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    use_tar = rc == 0

                except Exception as e:
                    send_log('extract_archive', f"failed to acquire 'tar' provider: {e}", 'warning')
                    use_tar = False


            # Log provider usage
            provider = 'tar' if use_tar else 'python'
            send_log('extract_archive', f"using '{provider}' as a provider")


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

            send_log('extract_archive', f"extracted '{archive_file}' to '{export_path}'")

        else: send_log('extract_archive', f"archive '{archive_file}' was not found", 'error')

    except Exception as e:
        send_log('extract_archive', f"error extracting '{archive_file}': {format_traceback(e)}", 'error')

    if archive:
        archive.close()


# Create an archive
def create_archive(file_path: str, export_path: str, archive_type='tar') -> str or None:
    file_name = os.path.basename(file_path)
    archive_name = f'{file_name}.{archive_type}'
    final_path = os.path.join(export_path, archive_name)

    send_log('create_archive', f"compressing '{file_path}' to '{export_path}'...")

    folder_check(export_path)

    # Create a .tar archive
    if archive_type == 'tar':
        try:
            rc = subprocess.call(['tar', '--help'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            use_tar = rc == 0

        except Exception as e:
            send_log('create_archive', f"failed to acquire 'tar' provider: {e}", 'warning')
            use_tar = False


        # Log provider usage
        provider = 'tar' if use_tar else 'python'
        send_log('create_archive', f"using '{provider}' as a provider")


        # Use tar command if available
        if use_tar:
            run_proc(f'tar -C \"{os.path.dirname(file_path)}\" -cvf \"{final_path}\" \"{file_name}\"')

        # Otherwise, use the Python implementation
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
        send_log('create_archive', f"compressed '{file_path}' to '{export_path}'")
        return final_path

    else: send_log('create_archive', f"something went wrong compressing '{file_path}'", 'error')


# Check if root is a folder instead of files, and move sub-folders to destination
def move_files_root(source: str, destination: str = None):
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
def download_url(url: str, file_name: str, output_path: str, progress_func=None) -> str or None:
    send_log('download_url', f"requesting from '{url}' to download '{file_name}' to '{output_path}'...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers, stream=True)
    try: response.raise_for_status()
    except Exception as e:
        send_log('download_url', f"request to '{url}' error: {format_traceback(e)}", 'error')
        raise e

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
        send_log('download_url', f"download of '{file_name}' complete: '{file_path}'")
        return file_path


# Will attempt to delete a directory tree without error
def safe_delete(directory: str) -> bool:
    global restart_flag

    if not directory:
        return False

    # Guard restart scripts and update log from deletion until restart
    if directory == tempDir and restart_flag:
        return False

    try:
        if os.path.exists(directory):
            rmtree(directory)
            send_log('safe_delete', f"successfully deleted '{directory}'")

    except OSError as e:
        send_log('safe_delete', f"could not delete '{directory}': {e}", 'warning')

    return not os.path.exists(directory)


# Delete every '_MEIPASS' folder in case of leftover files, and delete '.auto-mcs\Downloads' and '.auto-mcs\Uploads'
def cleanup_old_files():
    os_temp_folder = os.path.normpath(executable_folder + os.sep + os.pardir)
    send_log('cleanup_old_files', f"cleaning up old {app_title} temporary files in '{os_temp_folder}'")
    for item in glob(os.path.join(os_temp_folder, "*")):
        if (item != executable_folder) and ("_MEI" in os.path.basename(item)):
            if os.path.exists(os.path.join(item, 'gui-assets', 'animations', 'loading_pickaxe.gif')):
                try:
                    safe_delete(item)
                    send_log('cleanup_old_files', f"successfully deleted remnants of '{item}'")
                except PermissionError:
                    pass
    safe_delete(os.path.join(os_temp, '.kivy'))

    # Delete temporary files
    os.chdir(get_cwd())
    safe_delete(downDir)
    safe_delete(uploadDir)
    safe_delete(tempDir)
    safe_delete(telepathScriptDir)


# Glob to find hidden folders as well
def hidden_glob(path: str) -> list:

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
def rotate_array(array: list, rotation: int) -> list:

    if rotation > 0:
        for x in range(0, rotation):
            array.insert(0, array.pop(-1))
    else:
        for x in range(rotation, 0):
            array.append(array.pop(0))

    return array


# Cross-platform function to copy a file or folder
# src_dir --> ../dst_dir/new_name
def copy_to(src_dir: str, dst_dir: str, new_name: str, overwrite=True) -> bool:
    final_path = os.path.join(dst_dir, new_name)
    item_type = "file" if os.path.isfile(src_dir) else "directory" if os.path.isdir(src_dir) else None
    success = False
    final_item = None

    # Check if src_dir is file or folder, and if dst_dir can be written to
    if os.path.exists(src_dir) and item_type:
        if (os.path.exists(final_path) and overwrite) or (not os.path.exists(final_path)):

            send_log('copy_to', f"copying '{os.path.basename(src_dir)}' to '{final_path}'...")
            folder_check(dst_dir)

            if item_type == "file":
                final_item = copy(src_dir, final_path)

            elif item_type == "directory":
                final_item = copytree(src_dir, final_path, dirs_exist_ok=True, ignore=ignore_patterns('*session.lock'))

            if final_item:
                success = True
                send_log('copy_to', f"successfully copied to '{new_name}'")

    if not success:
        send_log('copy_to', f"something went wrong copying to '{new_name}'", 'error')

    return success


# Create random string of characters
def gen_rstring(size: int) -> str:
    return ''.join(choices(string.ascii_uppercase + string.ascii_lowercase, k=size))



# --------------------------------------------- Startup Functions ------------------------------------------------------

# Check if client has an internet connection
def check_app_updates():
    global project_link, app_version, dev_version, app_latest, app_online, update_data

    # Check if updates are available
    try:
        # Grab release data
        latest_release = f"https://api.github.com/repos{project_link.split('.com')[1]}/releases/latest"
        req = requests.get(latest_release, timeout=5)
        status_code = req.status_code
        app_online = status_code in (200, 403)
        release_data = req.json()

        # Don't automatically update if specified in config
        if not app_config.auto_update:
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
        send_log('check_app_updates', f"error checking for updates: {format_traceback(e)}", 'error')


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
                with open(os.path.join(cacheDir, 'data-version-db.json'), 'r', encoding='utf-8', errors='ignore') as f:
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

            version_list = []

            # Get side panel versions
            li_list = soup.find_all('li', 'li-version-list')
            for li in li_list:
                for sub_li in li.find_all('li'):
                    version = sub_li.text.strip()
                    url = url.rsplit('/', 1)[0] + f'/index_{version}.html'
                    version_list.append((version, url))

            # Get the first entry from the side panel versions
            try:
                reqs = requests.get(version_list[0][-1], timeout=timeout)
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


        elif name == "neoforge":
            # Neoforge
            url = "https://maven.neoforged.net/api/maven/versions/releases/net/neoforged/neoforge"
            reqs = requests.get(url)
            for version in reversed(reqs.json()['versions']):
                if 'beta' not in version:
                    latestMC['neoforge'] = f'1.{version.rsplit(".", 1)[0]}'
                    latestMC['builds']['neoforge'] = version.rsplit(".", 1)[-1]
                    break


        elif name == "paper":
            # Paper
            reqs = requests.get(url, timeout=timeout)

            jsonObject = reqs.json()
            version = jsonObject['versions'][-1]
            latestMC["paper"] = version

            build_url = f"{url}/versions/{version}"
            reqs = requests.get(build_url)
            jsonObject = reqs.json()
            latestMC["builds"]["paper"] = jsonObject['builds'][-1]


        elif name == "purpur":
            # Purpur
            reqs = requests.get(url, timeout=timeout)

            jsonObject = reqs.json()
            version = jsonObject['versions'][-1]
            latestMC["purpur"] = version

            build_url = f"{url}/{version}"
            reqs = requests.get(build_url)
            jsonObject = reqs.json()
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
            jsonObject = reqs.json()

            for item in jsonObject:
                if item['stable']:
                    version = item['version']
                    break

            # Loader build
            reqs = requests.get(loader, timeout=timeout)
            jsonObject = reqs.json()

            for item in jsonObject:
                if item['stable']:
                    loader = item['version']
                    break

            # Installer build
            reqs = requests.get(installer, timeout=timeout)
            jsonObject = reqs.json()

            for item in jsonObject:
                if item['stable']:
                    installer = item['version']
                    break

            latestMC["fabric"] = version
            latestMC["builds"]["fabric"] = loader
            # URL: https://meta.fabricmc.net/v2/versions/loader/{version}/{build}/server/jar


        elif name == "quilt":
            # Quilt
            version = "https://meta.quiltmc.org/v3/versions/game"
            loader = "https://meta.quiltmc.org/v3/versions/loader"
            installer = "https://meta.quiltmc.org/v3/versions/installer"

            # Game version
            reqs = requests.get(version, timeout=timeout)
            jsonObject = reqs.json()

            for item in jsonObject:
                if item['stable']:
                    version = item['version']
                    break

            # Loader build
            reqs = requests.get(loader, timeout=timeout)
            jsonObject = reqs.json()

            for item in jsonObject:
                if 'beta' not in item['version']:
                    loader = item['version']
                    break

            # Installer build
            reqs = requests.get(installer, timeout=timeout)
            jsonObject = reqs.json()

            for item in jsonObject:
                if item:
                    installer = item['version']
                    break

            latestMC["quilt"] = version
            latestMC["builds"]["quilt"] = loader


    version_links = {
        "vanilla": "https://mcversions.net/index.html",
        "forge": "https://files.minecraftforge.net/net/minecraftforge/forge/",
        "neoforge": "https://fabricmc.net/use/server/",
        "paper": "https://api.papermc.io/v2/projects/paper",
        "purpur": "https://api.purpurmc.org/v2/purpur",
        "spigot": "https://getbukkit.org/download/spigot",
        "craftbukkit": "https://getbukkit.org/download/craftbukkit",
        "fabric": "https://fabricmc.net/use/server/",
        "quilt": "https://fabricmc.net/use/server/"
    }

    with ThreadPoolExecutor(max_workers=6) as pool:
        pool.map(latest_version, version_links.keys(), version_links.values())


# Grabs list of data versions from wiki page
def get_data_versions() -> dict or None:
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
        status_code = getattr(data, 'status_code', None)
        send_log('get_data_versions', f'failed to retrieve data versions: {status_code} ({url})', 'error')
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
        send_log('check_data_cache', 'latest Vanilla version could not be found, skipping check', 'error')
        return

    if not os.path.isfile(cache_file): renew_cache = True

    else:
        with open(cache_file, 'r', encoding='utf-8', errors='ignore') as f:
            try:
                if latestMC["vanilla"] not in json.load(f): renew_cache = True
            except: renew_cache = True

    # Update cache file
    if renew_cache:
        send_log('check_data_cache', 'renewing data version cache...')
        folder_check(os.path.join(applicationFolder, "Cache"))
        data_versions = get_data_versions()

        if data_versions:
            with open(cache_file, 'w+') as f:
                f.write(json.dumps(data_versions, indent=2))

    send_log('check_data_cache', f"successfully renewed data version cache to '{cache_file}'")


# Random splash message
def generate_splash(crash=False):
    global session_splash, headless

    splashes = [
        "Nothing is impossible, unless you can't do it.", "Every 60 seconds in Africa, a minute goes by.",
        "Did you know: you were born on your birthday.", "Okay, I'm here. What are your other two wishes?",
        "Sometimes when you close your eyes, you may not be able to see.",
        "Common sense is the most limited of all natural resources.", "Ah, yes. That will be $69,420.00",
        "Some mints can be very dangerous.", "Paper grows on trees.",
        "You forgot? No problem. It's USERNAME PASSWORD123.", "This is just like my Yamaha Motorcycle!",
        "n o t  c o o l  m a n!", "Existing is prohibited from the premises.", "no", "Oh no, the monster died!",
        "Black holes are essentially God divided by 0", "If you try and don't succeed, you probably shouldn't skydive",
        "On the other hand, you have different fingers.", "A day without sunshine is like night.",
        "?What are you doing here stranger¿", "Get outta my swamp!", "Whoever put the word fun in funeral?",
        "A new day is like a new day.", "Everywhere is within walking distance if you have the time.",
        "empty blank", "Money doesn’t buy happiness, but it does buy everything else.",
        "Congratulations! It's a pizza!", "Silence is golden, but duck tape is silver.", "Welcome to flavortown!",
        "I get enough exercise pushing my luck.", "Unicorns ARE real, they’re just fat, grey, and we call them rhinos.",
        "I’d like to help you out. Which way did you come in?", "There are too many dogs in your inventory.",
        "Careful man, there's a beverage present.", "Fool me once, fool me twice, fool me chicken soup with rice.",
        "60% of the time, it works EVERYTIME!", "Imagine how is touch the sky.",
        "I can't find my keyboard, it must be here somewhere...", "The quick brown fox jumped over the lazy dog.",
        "No, this is Patrick.", "My spirit animal will eat yours.", "Roses are red, violets are blue, lmao XD UWU!",
        "You can't run away from all your problems…\n            Not when they have ender pearls.",
        "[!] bite hazard [!]", "How are you doing today Bob/Steve/Kyle?", "Only uses 69% CPU!!!"
    ]

    if crash:
        exp = re.sub('\s+',' ',splashes[randrange(len(splashes))]).strip()
        return f'"{exp}"'

    if headless: session_splash = f"“{splashes[randrange(len(splashes))]}”"
    else:        session_splash = f"“ {splashes[randrange(len(splashes))]} ”"


# Downloads the latest version of auto-mcs if available
def download_update(progress_func=None):

    def hook(a, b, c):
        if progress_func:
            progress_func(round(100 * a * b / c))

    if os_name == 'linux' and is_arm: update_url = update_data['urls']['linux-arm64']
    else: update_url = update_data['urls'][os_name]

    if not update_url:
        return False

    # Attempt at most 3 times to download auto-mcs
    fail_count  = 0
    new_version = update_data['version']
    binary_file = None
    last_error  = None
    send_log('download_update', f'downloading {app_title} v{new_version} from: {update_url}', 'info')

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
            last_error = format_traceback(e)
            fail_count += 1

    if last_error: send_log('download_update', f'failed to download {app_title} v{new_version}: {last_error}', 'error')
    else:          send_log('download_update', f"successfully downloaded {app_title} v{new_version} to: '{binary_file}'", 'info')
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
                endpoint = '/addon/load_addon_cache',
                host = telepath_data['host'],
                port = telepath_data['port'],
                args = {'write': write, 'telepath': True}
            )
            return response


    global addon_cache
    file_name = "addon-db.json"
    file_path = os.path.join(cacheDir, file_name)

    # Loads data from dict
    if not write:
        try:
            if os.path.isfile(file_path):
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
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
def validate_version(server_info: dict) -> list[bool, dict[str, str], str, bool]:
    global version_loading

    version_loading = True

    foundServer = False
    modifiedVersion = 0
    originalRequest = mcVer = server_info['version']
    mcType = server_info['type']
    buildNum = server_info['build']
    final_info = [False, {'version': mcVer, 'build': buildNum}, '', None] # [if version acceptable, {version, build}, message]
    url = ""
    send_log('validate_version', f"attempting to find {mcType.title()} '{mcVer}'", 'info')

    # Remove below 1.6 versions for Forge
    try:

        while foundServer is False:
            # Ignore versions below supported
            if mcType.lower() == "forge":
                if version_check(mcVer, '<', '1.6'):
                    mcVer = ""
            if mcType.lower() == "neoforge":
                if version_check(mcVer, '<', '1.20.2'):
                    mcVer = ""


            # Actually retrieve versions
            if mcType.lower() == "vanilla":

                # Fix for "no main manifest attribute, in server.jar"
                if version_check(mcVer, '>=', '1.0') and version_check(mcVer, '<', '1.2'):
                    mcVer2 = '1.0.0' if mcVer == '1.0' else mcVer
                    url = f"http://files.betacraft.uk/server-archive/release/{mcVer}/{mcVer2}.jar"

                # Every other vanilla release
                else:
                    url = f"https://mcversions.net/download/{mcVer}"


            elif mcType.lower() == "craftbukkit":
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


            elif mcType.lower() == "spigot":
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


            elif mcType.lower() == "paper":

                # Workaround to prevent downloading Java 16 as well
                if mcVer != "1.17":

                    try:
                        paper_url = f"https://api.papermc.io/v2/projects/paper/versions/{mcVer}"
                        reqs = requests.get(paper_url)
                        jsonObject = reqs.json()
                        buildNum = jsonObject['builds'][-1]

                        url = f"https://api.papermc.io/v2/projects/paper/versions/{mcVer}/builds/{buildNum}/downloads/paper-{mcVer}-{buildNum}.jar"
                    except:
                        url = ""


            elif mcType.lower() == "purpur":

                # Workaround to prevent downloading Java 16 as well
                if mcVer != "1.17":

                    try:
                        paper_url = f"https://api.purpurmc.org/v2/purpur/{mcVer}"
                        reqs = requests.get(paper_url)
                        jsonObject = reqs.json()
                        buildNum = jsonObject['builds']['latest']

                        url = f"https://api.purpurmc.org/v2/purpur/{mcVer}/{buildNum}/download"
                    except:
                        url = ""


            elif mcType.lower() == "forge":

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


            elif mcType.lower() == "neoforge":
                neoforge_url = "https://maven.neoforged.net/api/maven/versions/releases/net/neoforged/neoforge"
                reqs = requests.get(neoforge_url)
                for version in reversed(reqs.json()['versions']):
                    if 'beta' not in version:
                        buildNum = version.rsplit(".", 1)[-1]
                        formatted_version = f'1.{version.rsplit(".", 1)[0]}'
                        if formatted_version == mcVer:
                            url = f"https://maven.neoforged.net/releases/net/neoforged/neoforge/{version}/neoforge-{version}-installer.jar"
                            break


            elif mcType.lower() == "fabric":
                version = "https://meta.fabricmc.net/v2/versions/game"
                loader = "https://meta.fabricmc.net/v2/versions/loader"
                installer = "https://meta.fabricmc.net/v2/versions/installer"

                # Game version
                reqs = requests.get(version)
                jsonObject = reqs.json()

                for item in jsonObject:
                    if mcVer == item['version']:
                        version = item['version']
                        break

                # Loader build
                reqs = requests.get(loader)
                jsonObject = reqs.json()

                for item in jsonObject:
                    if item['stable']:
                        loader = item['version']
                        break

                # Installer build
                reqs = requests.get(installer)
                jsonObject = reqs.json()

                for item in jsonObject:
                    if item['stable']:
                        installer = item['version']
                        break

                buildNum = loader
                url = f"https://meta.fabricmc.net/v2/versions/loader/{mcVer}/{loader}/{installer}/server/jar"


            elif mcType.lower() == "quilt":

                # Check if Vanilla version is valid first
                vanilla_validation = validate_version({'type': 'vanilla', 'version': server_info['version'], 'build': '0'})
                if vanilla_validation[0]:

                    version = "https://meta.quiltmc.org/v3/versions/game"
                    loader = "https://meta.quiltmc.org/v3/versions/loader"
                    installer = "https://meta.quiltmc.org/v3/versions/installer"

                    # Game version
                    reqs = requests.get(version)
                    jsonObject = reqs.json()

                    for item in jsonObject:
                        if mcVer == item['version']:
                            version = item['version']
                            break

                    # Loader build
                    reqs = requests.get(loader)
                    jsonObject = reqs.json()

                    for item in jsonObject:
                        if 'beta' not in item['version']:
                            loader = item['version']
                            break

                    # Installer build
                    reqs = requests.get(installer)
                    jsonObject = reqs.json()

                    for item in jsonObject:
                        if item:
                            installer = item['version']
                            break

                    url = f"https://maven.quiltmc.org/repository/release/org/quiltmc/quilt-installer/{installer}/quilt-installer-{installer}.jar"
                    vanilla_validation[-1] = url
                    vanilla_validation[1]['build'] = loader
                    send_log('validate_version', f"successfully found {mcType.title()} '{mcVer}': {url}", 'info')
                    return vanilla_validation


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

                            for a in soup.find_all('a'):
                                if a.get_text().strip().lower() == "download server jar":
                                    serverLink = a.get('href')


                    final_info = [True, {'version': mcVer, 'build': buildNum}, "", serverLink]

                    if modifiedVersion > 0:
                        final_info[2] = f"'${originalRequest}$' could not be found, using '${mcVer}$' instead"
                        send_log('validate_version', f"{mcType.title()} {final_info[2].replace('$','')}", 'info')
                    originalRequest = ""

                    version_loading = False
                    send_log('validate_version', f"successfully found {mcType.title()} '{mcVer}': {url}", 'info')
                    return final_info


                else:
                    foundServer = False

            except:
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
    send_log('validate_version', f"successfully found {mcType.title()} '{mcVer}': {url}", 'info')
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
    send_log('new_server_init', f"initializing '{__name__}.new_server_info'", 'info')
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
            "disable_chat_reporting": True,

            "enable_proxy": False,

        },

        # Dynamic content
        "addon_objects": [],
        "acl_object": None

    }

# Override remote new server configuration
def push_new_server(server_info: dict, import_info={}):
    global new_server_info, import_data, server_list_lower
    new_server_init()
    if import_info:
        import_data = import_info

    if server_info:
        server_info['_telepath_data'] = None
        new_server_info = server_info

        # Reconstruct ACL manager
        if 'acl_object' in server_info and server_info['acl_object']:
            from acl import AclManager
            acl_mgr = AclManager(server_info['name'])
            if server_info['acl_object']:
                for list_type, rules in server_info['acl_object']['rules'].items():
                    [acl_mgr.edit_list(r['rule'], list_type, not r['list_enabled']) for r in rules]
                new_server_info['acl_object'] = acl_mgr

            # Reconstruct add-ons
        if 'addon_objects' in server_info and server_info['addon_objects']:
            addon_dict = deepcopy(server_info['addon_objects'])
            new_server_info['addon_objects'] = []
            for addon in addon_dict:
                new_server_info['addon_objects'].append(addons.AddonWebObject(addon) if addon['__reconstruct__'] == 'AddonWebObject' else addons.get_addon_file(addon['path'], new_server_info))


# Generate new server name
def new_server_name(existing_server=None, s_list=None):
    pattern = r'\s\(\d+\)$'
    if s_list is None:
        generate_server_list()
        s_list = server_list_lower
    def iter_name(new_name):
        x = 1
        while new_name.lower() in s_list:
            new_name = f'{re.sub(pattern, "", new_name).strip()} ({x})'
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
            endpoint = '/main/java_check',
            host = telepath_data['host'],
            port = telepath_data['port'],
            args = {}
        )
        if progress_func and response:
            progress_func(100)
        return response


    global java_executable, modern_pct, lts_pct, legacy_pct
    max_retries = 3
    retries = 0
    modern_version = 21
    send_log('java_check', f"validating Java installations...", 'info')

    java_url = {
        'windows': {
            "modern": f"https://download.oracle.com/java/{modern_version}/latest/jdk-{modern_version}_windows-x64_bin.zip",
            "lts": f"https://download.oracle.com/java/17/archive/jdk-17.0.12_windows-x64_bin.zip",
            "legacy": "https://javadl.oracle.com/webapps/download/GetFile/1.8.0_331-b09/165374ff4ea84ef0bbd821706e29b123/windows-i586/jre-8u331-windows-x64.tar.gz"
        },
        'linux': {
            "modern": f"https://download.oracle.com/java/{modern_version}/latest/jdk-{modern_version}_linux-x64_bin.tar.gz",
            "lts": f"https://download.oracle.com/java/17/archive/jdk-17.0.12_linux-x64_bin.tar.gz",
            "legacy": "https://javadl.oracle.com/webapps/download/GetFile/1.8.0_331-b09/165374ff4ea84ef0bbd821706e29b123/linux-i586/jre-8u331-linux-x64.tar.gz"
        },
        'linux-arm64': {
            "modern": f"https://download.oracle.com/java/{modern_version}/latest/jdk-{modern_version}_linux-aarch64_bin.tar.gz",
            "lts": f"https://download.oracle.com/java/17/archive/jdk-17.0.12_linux-aarch64_bin.tar.gz",
            "legacy": "https://javadl.oracle.com/webapps/download/GetFile/1.8.0_281-b09/89d678f2be164786b292527658ca1605/linux-i586/jdk-8u281-linux-aarch64.tar.gz"
        },
        'macos': {
            "modern": f"https://download.oracle.com/java/{modern_version}/latest/jdk-{modern_version}_macos-x64_bin.tar.gz",
            "lts": f"https://download.oracle.com/java/17/archive/jdk-17.0.12_macos-x64_bin.tar.gz",
            "legacy": "https://javadl.oracle.com/webapps/download/GetFile/1.8.0_331-b09/165374ff4ea84ef0bbd821706e29b123/unix-i586/jre-8u331-macosx-x64.tar.gz"
        }
    }

    while not (java_executable['modern'] and java_executable['lts'] and java_executable['legacy']):

        # Delete downloads folder
        safe_delete(downDir)

        # If max_retries exceeded, give up
        if retries > max_retries:
            send_log('java_check', f"Java failed to download or install", 'error')
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
                if is_docker or run_proc(f'"{os.path.abspath(modern_path)}" --version', return_text=True).startswith(f'java {modern_version}.'):

                    java_executable = {
                        "modern": str(os.path.abspath(modern_path)),
                        "lts": str(os.path.abspath(lts_path)),
                        "legacy": str(os.path.abspath(legacy_path)),
                        "jar": str(os.path.abspath(jar_path))
                    }

                    send_log('java_check', f"valid Java installations detected", 'info')

                    if progress_func:
                        progress_func(100)

                    return True


        # If valid java installs are not detected, install them to '.auto-mcs\Tools'
        if not (java_executable['modern'] and java_executable['lts'] and java_executable['legacy']):

            send_log('java_check', f"Java is not detected, installing...", 'info')


            # On Docker, use apk to install Java instead
            if is_docker:
                run_proc('apk add openjdk21 openjdk17 openjdk8', True)
                folder_check(javaDir)
                try:
                    move('/usr/lib/jvm/java-21-openjdk', os.path.join(javaDir, 'modern'))
                    move('/usr/lib/jvm/java-17-openjdk', os.path.join(javaDir, 'lts'))
                    move('/usr/lib/jvm/java-1.8-openjdk', os.path.join(javaDir, 'legacy'))
                except: pass
                continue



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
            endpoint = '/create/download_jar',
            host = telepath_data['host'],
            port = telepath_data['port'],
            args = {'imported': imported}
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
    server_data = deepcopy(import_data if imported else new_server_info)
    fail_count  = 0
    final_path  = None
    last_error  = None
    log_title   = f"{str(server_data['type']).title()} '{server_data['version']}'"
    send_log('download_jar', f'downloading {log_title} from: {server_data["jar_link"]}', 'info')

    while fail_count < 5:

        safe_delete(downDir)
        folder_check(downDir)
        folder_check(tmpsvr)

        try:

            if progress_func and fail_count > 0:
                progress_func(0)

            jar_name = (server_data['type'] if server_data['type'] in ['forge', 'quilt', 'neoforge'] else 'server') + '.jar'
            download_url(server_data['jar_link'], jar_name, downDir, hook)
            jar_path = os.path.join(downDir, jar_name)

            # If successful, copy to tmpsvr
            if os.path.exists(jar_path):

                if progress_func:
                    progress_func(100)

                fail_count = 0
                final_path = os.path.join(tmpsvr, jar_name)
                copy(jar_path, final_path)
                os.remove(jar_path)
                break

        except Exception as e:
            last_error = format_traceback(e)
            fail_count += 1

    if last_error: send_log('download_jar', f'failed to download {log_title}: {last_error}', 'error')
    else:          send_log('download_jar', f"successfully downloaded {log_title} to: '{final_path}'", 'info')
    return fail_count < 5


# Iterates through new server addon objects and downloads/installs them to tmpsvr
hook_lock = False
def iter_addons(progress_func=None, update=False, telepath=False):
    global hook_lock

    # If telepath, update addons remotely
    if telepath:
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
                endpoint = '/addon/iter_addons',
                host = telepath_data['host'],
                port = telepath_data['port'],
                args = {'update': update, 'telepath': True}
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

    log_content = [addon.name for addon in all_addons]
    send_log('iter_addons', f"downloading all add-ons to '{tmpsvr}':\n{log_content}", 'info')

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
                        disabled_folder = "plugins" if server_type(new_server_info['type']) == 'bukkit' else 'mods'
                        copy(addon_object.path, os.path.join(tmpsvr, "disabled-" + disabled_folder, os.path.basename(addon_object.path)))

                    return True

                addons.import_addon(addon_object, new_server_info, tmpsvr=True)

        except Exception as e:
            send_log('iter_addons', f"failed to load '{addon_object.name}': {format_traceback(e)}")


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

    send_log('iter_addons', f"successfully downloaded all add-ons to '{tmpsvr}'", 'info')

    return True
def pre_addon_update(telepath=False, host=None):
    global new_server_info
    server_obj = server_manager.current_server

    if telepath:
        server_obj = server_manager.remote_servers[host]

    # If remote, do this through telepath
    else:
        telepath_data = server_obj._telepath_data
        if telepath_data:
            response = api_manager.request(
                endpoint = '/addon/pre_addon_update',
                host = telepath_data['host'],
                port = telepath_data['port'],
                args = {'telepath': True}
            )
            return response


    # Clear folders beforehand
    send_log('pre_addon_update', 'initializing environment for an add-on update...', 'info')
    os.chdir(get_cwd())
    safe_delete(tmpsvr)
    safe_delete(tempDir)
    safe_delete(downDir)

    # Generate server info for downloading proper add-on versions
    new_server_init()
    new_server_info = server_obj.properties_dict()
    init_update(telepath=telepath, host=host)
    new_server_info['addon_objects'] = server_obj.addon.return_single_list()
def post_addon_update(telepath=False, host=None):
    global new_server_info
    server_obj = server_manager.current_server

    if telepath:
        server_obj = server_manager.remote_servers[host]

    # If remote, do this through telepath
    else:
        telepath_data = server_obj._telepath_data
        if telepath_data:
            response = api_manager.request(
                endpoint = '/addon/post_addon_update',
                host = telepath_data['host'],
                port = telepath_data['port'],
                args = {'telepath': True}
            )

            # Clear stale cache
            if server_obj.__class__.__name__ == 'RemoteServerObject':
                server_obj._clear_all_cache()

            return response


    send_log('post_addon_update', 'cleaning up environment after add-on update...', 'info')
    server_obj.addon.update_required = False

    # Clear items from addon cache to re-cache
    for addon in server_obj.addon.installed_addons['enabled']:
        if addon.hash in addon_cache:
            del addon_cache[addon.hash]
    load_addon_cache(True)

    # Copy folder to server path and delete tmpsvr
    new_path = os.path.join(serverDir, new_server_info['name'])
    os.chdir(get_cwd())
    copytree(tmpsvr, new_path, dirs_exist_ok=True)
    safe_delete(tempDir)
    safe_delete(downDir)

    new_server_info = {}


# If Fabric or Forge, install server
def install_server(progress_func=None, imported=False):

    # If telepath, do this remotely
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
            endpoint = '/create/install_server',
            host = telepath_data['host'],
            port = telepath_data['port'],
            args = {'imported': imported}
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

    send_log('install_server', f"executing installer for {jar_type.title()} '{jar_version}' in '{tmpsvr}'...", 'info')


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


    # Install NeoForge server
    elif jar_type == 'neoforge':
        run_proc(f'"{java_executable["modern"]}" -jar neoforge.jar -installServer')

        for f in glob("user_jvm*"):
            os.remove(f)

        for f in glob("install*.log"):
            os.remove(f)

        for f in glob("neoforge.jar"):
            os.remove(f)


    # Install Fabric server
    elif jar_type == 'fabric':

        process = subprocess.Popen(f'"{java_executable["modern"]}" -jar server.jar nogui', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        while True:
            time.sleep(1)
            log = os.path.join(tmpsvr, 'logs', 'latest.log')
            if os.path.exists(log):
                with open(log, 'r', encoding='utf-8', errors='ignore') as f:
                    if "You need to agree to the EULA in order to run the server. Go to eula.txt for more info" in f.read():
                        break

        process.kill()

        for f in glob("eula.txt"):
            os.remove(f)

        for f in glob("server.properties"):
            os.remove(f)

        # Install Fabric server


    # Install Quilt server
    elif jar_type == 'quilt':
        run_proc(f'"{java_executable["modern"]}" -jar quilt.jar install server {jar_version} --download-server')

        # Move installed files to root
        if os.path.exists(os.path.join(tmpsvr, 'server')):
            os.remove(os.path.join(tmpsvr, 'quilt.jar'))
            move(os.path.join(tmpsvr, 'server', 'server.jar'), os.path.join(tmpsvr, 'server.jar'))
            move(os.path.join(tmpsvr, 'server', 'quilt-server-launch.jar'), os.path.join(tmpsvr, 'quilt.jar'))
            if os.path.exists(os.path.join(tmpsvr, 'libraries')):
                safe_delete(os.path.join(tmpsvr, 'libraries'))
            move(os.path.join(tmpsvr, 'server', 'libraries'), os.path.join(tmpsvr, 'libraries'))
            safe_delete(os.path.join(tmpsvr, 'server'))

            process = subprocess.Popen(f'"{java_executable["modern"]}" -jar quilt.jar nogui', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            while True:
                time.sleep(1)
                log = os.path.join(tmpsvr, 'logs', 'latest.log')
                if os.path.exists(log):
                    with open(log, 'r', encoding='utf-8', errors='ignore') as f:
                        if "You need to agree to the EULA in order to run the server. Go to eula.txt for more info" in f.read():
                            break

            process.kill()

            for f in glob("eula.txt"):
                os.remove(f)

            for f in glob("server.properties"):
                os.remove(f)


    # Change back to original directory
    os.chdir(cwd)

    send_log('install_server', f"successfully installed {jar_type.title()} '{jar_version}' in '{tmpsvr}'", 'info')

    return True


# Generate a new EULA content, and time stamp
def generate_eula() -> [str, str]:
    time_stamp = date.today().strftime(f"#%a %b %d ") + dt.now().strftime("%H:%M:%S ") + "MCS" + date.today().strftime(f" %Y")
    eula = f"#By changing the setting below to TRUE you are indicating your agreement to our EULA (https://account.mojang.com/documents/minecraft_eula).\n{time_stamp}\neula=true"
    return eula, time_stamp


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
            endpoint = '/create/generate_server_files',
            host = telepath_data['host'],
            port = telepath_data['port'],
            args = {}
        )
        if progress_func and response:
            progress_func(100)
        return response


    send_log('generate_server_files', f"generating pre-launch files in '{tmpsvr}'...", 'info')
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
        cmd_temp_path = os.path.join(tmpsvr, command_tmp)
        send_log('generate_server_files', f"generating '{cmd_temp_path}' for post-launch command execution...", 'info')
        with open(cmd_temp_path, 'w') as f:
            file = f"gamerule keepInventory {str(new_server_info['server_settings']['keep_inventory']).lower()}\n"
            if version_check(new_server_info['version'], '>=', '1.8'):
                file += f"gamerule randomTickSpeed {str(new_server_info['server_settings']['random_tick_speed']).lower()}\n"
                if version_check(new_server_info['version'], '<', '1.13'):
                    file += f"gamerule sendCommandFeedback false\n"
            if version_check(new_server_info['version'], '>=', '1.6.1'):
                file += f"gamerule doDaylightCycle {str(new_server_info['server_settings']['daylight_weather_cycle']).lower()}\n"
                if version_check(new_server_info['version'], '>=', '1.11'):
                    file += f"gamerule doWeatherCycle {str(new_server_info['server_settings']['daylight_weather_cycle']).lower()}\n"
            f.write(file.strip())
            send_log('generate_server_files', f"successfully created '{cmd_temp_path}' with the following commands:\n{file.splitlines()}", 'info')



    # Generate ACL rules to temp server
    if new_server_info['acl_object'].count_rules()['total'] > 0:
        new_server_info['acl_object'].write_rules()


    # Install playit if specified
    if new_server_info['server_settings']['enable_proxy'] and not playit._check_agent():
        playit._install_agent()


    # Generate EULA.txt
    send_log('generate_server_files', f"generating '{os.path.join(tmpsvr, 'eula.txt')}'...", 'info')
    eula, time_stamp = generate_eula()
    with open(os.path.join(tmpsvr, 'eula.txt'), 'w+') as f:
        f.write(eula)


    # Generate server.properties
    send_log('generate_server_files', f"generating minimal '{os.path.join(tmpsvr, 'server.properties')}'...", 'info')
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

    properties = f"""#Minecraft server properties
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
        properties += f"\nenforce_whitelist={bool_str(new_server_info['acl_object']._server['whitelist'])}"

    if version_check(new_server_info['version'], ">=", '1.19'):
        properties += "\nenforce-secure-profile=false"

    with open(os.path.join(tmpsvr, 'server.properties'), 'w+') as f:
        f.write(properties)


    # Create auto-mcs.ini
    create_server_config(new_server_info, temp_server=True)


    # Check if everything was created successfully
    if (os.path.exists(os.path.join(tmpsvr, 'server.properties')) and os.path.exists(os.path.join(tmpsvr, server_ini)) and os.path.exists(os.path.join(tmpsvr, 'eula.txt'))):

        # Copy folder to server path and delete tmpsvr
        new_path = os.path.join(serverDir, new_server_info['name'])
        os.chdir(get_cwd())
        copytree(tmpsvr, new_path, dirs_exist_ok=True)
        safe_delete(tempDir)
        safe_delete(downDir)

        if os_name == "windows":
            run_proc(f"attrib +H \"{os.path.join(new_path, server_ini)}\"")
            if os.path.exists(os.path.join(new_path, command_tmp)):
                run_proc(f"attrib +H \"{os.path.join(new_path, command_tmp)}\"")

        make_update_list()
        send_log('generate_server_files', "successfully generated all pre-launch files", 'info')
        return True

    else: send_log('generate_server_files', "something went wrong generating pre-launch files", 'error')


def pre_server_create(telepath=False):
    global new_server_info, import_data

    telepath_data = None
    try:
        if new_server_info['_telepath_data']:
            telepath_data = new_server_info['_telepath_data']
    except KeyError:
        pass


    if telepath_data and not telepath:
        send_log('pre_server_create', f"initializing environment for server creation...", 'info')

        # Convert ACL object for remote
        new_info = deepcopy(new_server_info)
        if new_info['acl_object']:
            new_info['acl_object'] = new_server_info['acl_object']._to_json()

        # Convert add-ons to remote
        for pos, addon in enumerate(new_server_info['addon_objects'], 0):
            a = addon._to_json()
            if 'AddonFileObject' == a['__reconstruct__']:
                a['path'] = telepath_upload(new_server_info['_telepath_data'], a['path'])['path']
            new_info['addon_objects'][pos] = a

        # Upload world if specified
        if new_server_info['server_settings']['world'] != 'world':
            new_path = telepath_upload(telepath_data, new_server_info['server_settings']['world'])['path']
            new_info['server_settings']['world'] = new_path

        # Copy import remotely if available
        try:
            if import_data['path']:
                import_data['path'] = telepath_upload(telepath_data, import_data['path'])['path']
        except KeyError:
            pass

        api_manager.request(
            endpoint = '/create/push_new_server',
            host = telepath_data['host'],
            port = telepath_data['port'],
            args = {'server_info': new_info, 'import_info': import_data}
        )
        response = api_manager.request(
            endpoint = '/create/pre_server_create',
            host = telepath_data['host'],
            port = telepath_data['port'],
            args = {'telepath': True}
        )
        return response


    # Input validate name to prevent overwriting
    if import_data['name']:
        if import_data['name'].lower() in server_list_lower:
            import_data['name'] = new_server_name(import_data['name'])
    elif new_server_info['name']:
        if new_server_info['name'].lower() in server_list_lower:
            new_server_info['name'] = new_server_name(new_server_info['name'])

    server_manager.current_server = None

    # First, clean out any existing server in temp folder
    safe_delete(tmpsvr)
    folder_check(tmpsvr)

    # Report to telepath logger
    if telepath:
        prefix = 'Importing: ' if bool('name' in import_data and import_data['name']) else 'Creating: '
        data = new_server_info if new_server_info['name'] else import_data
        api_manager.logger._report(f'create.pre_server_create', extra_data=f'{prefix}{data}')
def post_server_create(telepath=False, modpack=False):
    global new_server_info, import_data
    return_data = {'name': import_data['name'], 'readme': None}
    telepath_data = None
    try:
        if new_server_info['_telepath_data']:
            telepath_data = new_server_info['_telepath_data']
    except KeyError:
        pass

    if telepath_data and not telepath:
        response = api_manager.request(
            endpoint = '/create/post_server_create',
            host = telepath_data['host'],
            port = telepath_data['port'],
            args = {'telepath': True}
        )
        return response

    if modpack:
        server_path = os.path.join(serverDir, import_data['name'])
        read_me = [f for f in glob(os.path.join(server_path, '*.txt')) if 'read' in f.lower()]
        if read_me: return_data['readme'] = read_me[0]

    send_log('post_server_create', f"cleaning up environment after server creation...", 'info')

    clear_uploads()
    new_server_info = {}
    import_data = {'name': None, 'path': None}
    return return_data

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
            endpoint = '/create/update_server_files',
            host = telepath_data['host'],
            port = telepath_data['port'],
            args = {}
        )
        if progress_func and response:
            progress_func(100)
        return response


    new_path = os.path.join(serverDir, new_server_info['name'])
    new_config_path = os.path.join(tmpsvr, server_ini)
    send_log('update_server_files', f"preparing to patch '{new_path}' with update files from '{tmpsvr}'...", 'info')

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
        send_log('update_server_files', f"patching '{new_path}'...", 'info')
        safe_delete(new_path)
        os.chdir(get_cwd())
        copytree(tmpsvr, new_path, dirs_exist_ok=True)
        safe_delete(tempDir)
        safe_delete(downDir)

        if os_name == "windows":
            run_proc(f"attrib +H \"{os.path.join(new_path, server_ini)}\"")

        if os.path.isdir(new_path):
            send_log('update_server_files', f"successfully patched '{new_path}'", 'info')
            return True

    send_log('update_server_files', f"something went wrong moving update files from '{tmpsvr}' to '{new_path}'", 'error')


def pre_server_update(telepath=False, host=None):
    global new_server_info
    server_obj = server_manager.current_server

    if telepath:
        server_obj = server_manager.remote_servers[host]

    # If remote, do this through telepath
    else:
        telepath_data = server_obj._telepath_data
        if telepath_data:

            # Copy import remotely if available
            try:
                if import_data['path']:
                    import_data['path'] = telepath_upload(telepath_data, import_data['path'])['path']

                    api_manager.request(
                        endpoint = '/create/push_new_server',
                        host = telepath_data['host'],
                        port = telepath_data['port'],
                        args = {'server_info': new_server_info, 'import_info': import_data}
                    )
                    response = api_manager.request(
                        endpoint = '/create/pre_server_create',
                        host = telepath_data['host'],
                        port = telepath_data['port'],
                        args = {'telepath': True}
                    )
            except KeyError:
                pass

            response = api_manager.request(
                endpoint = '/create/pre_server_update',
                host = telepath_data['host'],
                port = telepath_data['port'],
                args = {'telepath': True}
            )
            return response

    send_log('pre_server_update', f"initializing environment for a server update...", 'info')

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

    # Report to telepath logger
    if telepath:
        data = f'Modifying server.jar: {server_obj.type} {server_obj.version} --> {new_server_info["type"]} {new_server_info["version"]}'
        api_manager.logger._report(f'create.pre_server_update', extra_data=data, server_name=server_obj.name)
def post_server_update(telepath=False, host=None):
    global new_server_info
    server_obj = server_manager.current_server

    if telepath:
        server_obj = server_manager.remote_servers[host]

    # If remote, do this through telepath
    else:
        telepath_data = server_obj._telepath_data
        if telepath_data:
            response = api_manager.request(
                endpoint = '/create/post_server_update',
                host = telepath_data['host'],
                port = telepath_data['port'],
                args = {'telepath': True}
            )

            # Clear stale cache
            if server_obj.__class__.__name__ == 'RemoteServerObject':
                server_obj._clear_all_cache()

            return response

    send_log('post_server_update', f"cleaning up environment after a server update...", 'info')
    make_update_list()
    server_obj._view_notif('add-ons', False)
    server_obj._view_notif('settings', viewed=new_server_info['version'])

    clear_uploads()
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
            endpoint = '/create/create_backup',
            host = telepath_data['host'],
            port = telepath_data['port'],
            args = {'import_server': import_server}
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

            if not proc_complete:
                percent = round((current_count/total_files) * 100)
                progress_func(percent)

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
    telepath_data = None
    try:
        if new_server_info['_telepath_data']:
            telepath_data = new_server_info['_telepath_data']
    except KeyError:
        pass

    if telepath_data:
        response = api_manager.request(
            endpoint = '/create/scan_import',
            host = telepath_data['host'],
            port = telepath_data['port'],
            args = {'bkup_file': bkup_file}
        )
        if progress_func and response:
            progress_func(100)
        return response


    name = import_data['name']
    path = import_data['path']
    send_log('scan_import', f"scanning '{path}' to detect metadata...", 'info')

    cwd = get_cwd()
    folder_check(tmpsvr)
    os.chdir(tmpsvr)

    import_data['config_file'] = None
    import_data['type'] = None
    import_data['version'] = None
    import_data['build'] = None

    file_name   = None
    script_list = None


    # If import is from a back-up
    if bkup_file:
        run_proc(f'tar -xvf "{path}"')

        if progress_func:
            progress_func(50)

        # Delete all startup scripts in directory
        for script in glob(os.path.join(tmpsvr, "*.bat"), recursive=False): os.remove(script)
        for script in glob(os.path.join(tmpsvr, "*.sh"), recursive=False): os.remove(script)

        # Extract info from auto-mcs.ini
        all_configs = glob(os.path.join(tmpsvr, "auto-mcs.ini*"))
        all_configs.extend(glob(os.path.join(tmpsvr, ".auto-mcs.ini*")))
        config_file = server_config(server_name=None, config_path=all_configs[0])
        import_data['version'] = config_file.get('general', 'serverVersion').lower()
        import_data['type'] = config_file.get('general', 'serverType').lower()
        try:    import_data['build'] = str(config_file.get('general', 'serverBuild'))
        except: pass
        try:    import_data['launch_flags'] = str(config_file.get('general', 'customFlags'))
        except: pass
        import_data['config_file'] = config_file

        # Then delete it for later
        for item in glob(os.path.join(tmpsvr, "*auto-mcs.ini"), recursive=False): os.remove(item)



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
                    script_name = os.path.join(tempDir, 'importtest', jar_name + '.bat')
                    with open(script_name, 'w+') as f:
                        f.write(f'java -jar {jar_name}')
                    script_list.append(script_name)


        # First, check for any run scripts to see if the .jar is contained within
        for file in script_list:

            # Find server jar name
            with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                output = f.read()
                raw_output = output
                f.close()
                start_script = False

                if "-jar" in output and ".jar" in output:
                    start_script = True
                    file_name = re.search(r'\S+(?=\.jar)', output).group(0)
                    file_path = os.path.join(str(path), f'{file_name}.jar')

                    # Ignore invalid file names
                    if not os.path.isfile(file_path):
                        continue

                    # copy jar file to test directory
                    copy(file_path, test_server)


                    # Check if server.jar is a valid server
                    run_proc(f'"{java_executable["jar"]}" -xf {file_name}.jar META-INF/MANIFEST.MF')
                    run_proc(f'"{java_executable["jar"]}" -xf {file_name}.jar META-INF/versions.list')

                    with open(os.path.join(test_server, 'META-INF', 'MANIFEST.MF'), 'r', encoding='utf-8', errors='ignore') as f:
                        output = f.read()

                        version_output = ""
                        if os.path.exists(os.path.join(test_server, 'META-INF', 'versions.list')):
                            with open(os.path.join(test_server, 'META-INF', 'versions.list'), 'r', encoding='utf-8', errors='ignore') as f:
                                version_output = f.read()

                        # Quilt keywords
                        if "quiltmc" in output.lower():
                            import_data['type'] = "quilt"

                        # NeoForge keywords
                        elif "neoforge" in output.lower():
                            import_data['type'] = "neoforge"

                        # Fabric keywords
                        elif "fabricinstaller" in output.lower() or "net.fabricmc" in output.lower():
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
                                    with open(os.path.join(str(path), 'version_history.json'), 'r', encoding='utf-8', errors='ignore') as f:
                                        import_data['build'] = str(json.load(f)['currentVersion'].lower().split('paper-')[1].split(' ')[0].strip())
                                except: pass

                        # Spigot keywords
                        elif "spigot" in output.lower() or "spigot" in version_output.lower():
                            import_data['type'] = "spigot"

                        # Spigot keywords
                        elif "craftbukkit" in output.lower():
                            import_data['type'] = "craftbukkit"

                        # Vanilla keywords
                        elif "net.minecraft.server.minecraftserver" in output.lower() or "net.minecraft.server.main" in output.lower() or "net.minecraft.bundler.main" in output.lower():
                            import_data['type'] = "vanilla"


                    # Before starting the server, check mods folder for most common version specified
                    if not import_data['version'] and import_data['type'] in ['forge', 'fabric']:

                        # Generate script list and iterate through each one
                        file_list = glob(os.path.join(path, "*.txt"))
                        if os.path.exists(os.path.join(path, 'scripts')):
                            file_list = glob(os.path.join(path, "scripts", "*.*"))
                        if os.path.exists(os.path.join(path, 'config')):
                            file_list.extend(glob(os.path.join(path, "config", "*.*")))

                        version_matches = []

                        def process_matches(content):
                            version_matches.extend(re.findall(r'(?<!\d.)1\.\d\d?\.\d\d?(?!\.\d+)\b', content))

                        # First, search through all the files to find the type, version, and launch flags
                        for file in file_list:
                            # Find server jar name
                            with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                                output = f.read()
                                f.close()
                                process_matches(output)
                                process_matches(os.path.basename(file))

                        # Second, search through all the mod names to more accurately determine the MC version
                        if os.path.exists(os.path.join(path, 'mods')):
                            for mod in glob(os.path.join(path, "mods", "*.jar")):
                                process_matches(os.path.basename(mod))

                        if version_matches:
                            import_data['version'] = max(set(version_matches), key=version_matches.count)


                    # Check for server version
                    if not import_data['version']:

                        if progress_func:
                            progress_func(50)

                        ram = calculate_ram(import_data)
                        send_log('scan_import', f"determined type '{import_data['type'].title()}':  validating version information...", 'info')

                        if import_data['type'] == "forge":
                            copy_to(os.path.join(str(path), 'libraries'), test_server, 'libraries', True)
                            for jar in glob(os.path.join(str(path), 'minecraft_server*.jar')):
                                copy(jar, test_server)

                        if import_data['type'] == 'fabric':
                            for properties in glob(os.path.join(str(path), '*.properties')):
                                copy(properties, test_server)
                            for folder in ['libraries', 'versions']:
                                if os.path.exists(os.path.join(str(path), folder)):
                                    copy_to(os.path.join(str(path), folder), test_server, folder)
                            for jar in glob(os.path.join(str(path), '*server*.jar')):
                                copy(jar, test_server)
                            if os.path.exists(os.path.join(test_server, 'fabric-server-launch.jar')):
                                file_name = 'fabric-server-launch.jar'

                        # EULA
                        eula, time_stamp = generate_eula()
                        with open(f"eula.txt", "w+") as f:
                            f.write(eula)

                        # Run legacy version of java
                        if not file_name.endswith('.jar'):
                            file_name = f'{file_name}.jar'

                        if import_data['type'] == "forge":
                            server = subprocess.Popen(f"\"{java_executable['legacy']}\" -Xmx{ram}G -Xms{int(round(ram/2))}G -jar {file_name} nogui", shell=True)

                        # Run latest version of java
                        else:
                            # If paper, copy pre-downloaded vanilla .jar files if they exist
                            if import_data['type'] in ["paper", "purpur"]:
                                copy_to(os.path.join(str(path), 'cache'), test_server, 'cache', True)

                            server = subprocess.Popen(f"\"{java_executable['modern']}\" -Xmx{ram}G -Xms{int(round(ram/2))}G -jar {file_name} nogui", shell=True)

                        found_version = False
                        timeout = 0

                        while found_version is False:
                            time.sleep(1)
                            timeout += 1
                            output = ""

                            # Read modern logs
                            if os.path.exists(os.path.join(test_server, 'logs', 'latest.log')):
                                with open(os.path.join(test_server, 'logs', 'latest.log'), 'r', encoding='utf-8', errors='ignore') as f:
                                    output = f.read()

                            # Read legacy logs
                            elif os.path.exists(os.path.join(test_server, 'server.log')):
                                with open(os.path.join(test_server, 'server.log'), 'r', encoding='utf-8', errors='ignore') as f:
                                    output = f.read()

                            if "starting minecraft server version" in output.lower():
                                found_version = True
                                if os_name == 'windows': run_proc(f"taskkill /F /T /PID {server.pid}")
                                else:                    run_proc(f"kill -9 {server.pid}")
                                server.kill()

                                for line in output.split("\n"):
                                    if "starting minecraft server version" in line.lower():
                                        import_data['version'] = line.split("version ")[1].replace("Beta ", "b").replace("Alpha ", "a")
                                break

                            if (timeout > 200) or (server.poll() is not None):
                                if os_name == 'windows': run_proc(f"taskkill /F /T /PID {server.pid}")
                                else:                    run_proc(f"kill -9 {server.pid}")
                                server.kill()
                                break

                # NeoForge
                elif "@libraries/net/neoforged/neoforge/" in output:
                    start_script = True
                    version_string = re.search(r'\d+.\d+.\d+', output.split("@libraries/net/neoforged/neoforge/")[1])[0]
                    version = '1.' + version_string.rsplit('.', 1)[0]
                    build = version_string.rsplit('.', 1)[-1]

                    import_data['type'] = "neoforge"
                    import_data['version'] = version
                    import_data['build'] = build
                    send_log('scan_import', f"determined type '{import_data['type'].title()}':  validating version information...", 'info')

                # New versions of forge
                elif "@libraries/net/minecraftforge/forge/" in output:
                    start_script = True
                    version_string = output.split("@libraries/net/minecraftforge/forge/")[1]
                    version = version_string.split("-")[0].lower()
                    build = version_string.split("-")[1]

                    import_data['type'] = "forge"
                    import_data['version'] = version
                    import_data['build'] = build
                    send_log('scan_import', f"determined type '{import_data['type'].title()}':  validating version information...", 'info')


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
                            if ("%" in flag or "${" in flag or '-Xmx' in flag or '-Xms' in flag or len(flag) < 5) and (not flag.strip().startswith('@')):
                                continue
                            for exclude in ['-install', '-server', '-jar', '--nogui', '-nogui', '-Command', '-fullversion', '-version', '-mcversion', '-loader', '-downloadminecraft', '-mirror']:
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
                try: os.rmdir(tmpsvr)
                except FileNotFoundError: pass
                except PermissionError: pass
                copy_to(str(path), tempDir, os.path.basename(tmpsvr))

                # Delete all startup scripts in directory
                for script in glob(os.path.join(tmpsvr, "*.bat"), recursive=False): os.remove(script)
                for script in glob(os.path.join(tmpsvr, "*.sh"), recursive=False): os.remove(script)

                # Delete all *.jar files in directory
                for jar in glob(os.path.join(tmpsvr, '*.jar'), recursive=False):
                    if not ((jar.startswith('minecraft_server') and import_data['type'] == 'forge') or (file_name and file_name in jar)):
                        os.remove(jar)

                    # Rename actual .jar file to server.jar to prevent crashes
                    if file_name and file_name in jar:
                        run_proc(f"{'move' if os_name == 'windows' else 'mv'} \"{os.path.join(tmpsvr, os.path.basename(jar))}\" \"{os.path.join(tmpsvr, 'server.jar')}\"")



    os.chdir(cwd)
    if import_data['type'] and import_data['version']:
        send_log('scan_import', f"determined version '{import_data['version']}': writing to '{tmpsvr}' for further processing...", 'info')

        # Regenerate auto-mcs.ini
        config_file = create_server_config(import_data, True)

        # Sanitize values from old versions of auto-mcs
        if import_data['config_file']:

            try: config_file.set('general', 'isFavorite', str(import_data['config_file'].get('general', 'isFavorite')).lower())
            except configparser.NoOptionError: pass

            try: config_file.set('general', 'updateAuto', str(import_data['config_file'].get('general', 'updateAuto')).lower())
            except configparser.NoOptionError: pass

            try: config_file.set('general', 'allocatedMemory', str(import_data['config_file'].get('general', 'allocatedMemory')).lower())
            except configparser.NoOptionError: pass

            try: config_file.set('general', 'customFlags', str(import_data['config_file'].get('general', 'customFlags')).lower())
            except configparser.NoOptionError: pass

            try: config_file.set('general', 'enableGeyser', str(import_data['config_file'].get('general', 'enableGeyser')).lower())
            except configparser.NoOptionError: pass

            try: config_file.set('general', 'enableProxy', str(import_data['config_file'].get('general', 'enableProxy')).lower())
            except configparser.NoOptionError: pass

            try: config_file.set('general', 'isModpack', str(import_data['config_file'].get('general', 'isModpack')).lower())
            except configparser.NoOptionError: pass

            try: config_file.set('general', 'consoleFilter', str(import_data['config_file'].get('general', 'consoleFilter')).lower())
            except configparser.NoOptionError: pass

            try: config_file.set('bkup', 'bkupAuto', str(import_data['config_file'].get('bkup', 'bkupAuto')).lower())
            except configparser.NoOptionError: pass

            try: config_file.set('bkup', 'bkupMax', str(import_data['config_file'].get('bkup', 'bkupMax')).lower())
            except configparser.NoOptionError: pass

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
            try: os.rename(item, os.path.join(tmpsvr, command_tmp))
            except FileExistsError: pass

        if os_name == "windows" and os.path.exists(os.path.join(tmpsvr, command_tmp)):
            run_proc(f"attrib +H \"{os.path.join(tmpsvr, command_tmp)}\"")

        # Generate startup script
        generate_run_script(import_data, temp_server=True)


        if os.path.exists(os.path.join(tmpsvr, server_ini)):
            if progress_func:
                progress_func(100)
            return True


    # Failed state due to one or more issues locating required data
    error_text = "type" if not import_data['version'] else "type and version"
    log_content = f"unable to determine the server's {error_text}:\n'import_data': {import_data}\n'bkup_file': {bkup_file}\n'script_list': {script_list}"
    send_log('scan_import', log_content, 'error')
    return False


# Moves tmpsvr to actual server and checks for ACL and other file validity
def finalize_import(progress_func=None, *args):
    global import_data

    telepath_data = None
    try:
        if new_server_info['_telepath_data']:
            telepath_data = new_server_info['_telepath_data']
    except KeyError:
        pass

    if telepath_data:
        response = api_manager.request(
            endpoint = '/create/finalize_import',
            host = telepath_data['host'],
            port = telepath_data['port'],
            args = {}
        )
        if progress_func and response:
            progress_func(100)
        return response


    if import_data['name']:
        new_path = os.path.join(serverDir, import_data['name'])
        send_log('finalize_import', f"installing '{tmpsvr}' to '{new_path}'...", 'info')

        # Copy folder to server path and delete tmpsvr
        os.chdir(get_cwd())
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
            send_log('finalize_import', f"generating '{new_server_name(import_data['name'], 'eula.txt')}'...", 'info')

            # Generate EULA
            eula, time_stamp = generate_eula()
            with open(os.path.join(server_path(import_data['name']), 'eula.txt'), 'w+') as f:
                f.write(eula)

            if server_path(import_data['name'], 'server.properties'):
                content = []
                with open(os.path.join(server_path(import_data['name']), 'server.properties'), 'r', encoding='utf-8', errors='ignore') as f:
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
            os.chdir(get_cwd())
            safe_delete(tempDir)
            safe_delete(downDir)
            make_update_list()
            if progress_func:
                progress_func(100)

            send_log('finalize_import', f"successfully imported to '{new_path}'", 'info')
            return True

        else: send_log('finalize_import', f"something went wrong importing to '{new_path}'", 'error')


# Imports a modpack from a .zip file
def scan_modpack(update=False, progress_func=None):
    global import_data

    telepath_data = None
    if server_manager.current_server and update:
        telepath_data = server_manager.current_server._telepath_data
    try:
        if not telepath_data and new_server_info['_telepath_data']:
            telepath_data = new_server_info['_telepath_data']
    except KeyError:
        pass

    if telepath_data:
        response = api_manager.request(
            endpoint = '/create/scan_modpack',
            host = telepath_data['host'],
            port = telepath_data['port'],
            args = {'update': update}
        )
        if progress_func and response:
            progress_func(100)
        return response


    # First, check if the modpack is a URL and needs to be downloaded
    try:
        url = import_data['url']

    # File is not a URL
    except KeyError:
        file_path = import_data['path']

    # Otherwise, download the modpack and use that as the import file
    else:
        send_log('scan_modpack', f"a URL was provided for '{import_data['name']}', downloading prior to scan from '{url}'...", 'info')
        file_path = import_data['path'] = download_url(url, f"{sanitize_name(import_data['name'])}.{url.rsplit('.',1)[-1]}", downDir)


    # Test archive first
    if not os.path.isfile(file_path) or file_path.split('.')[-1] not in ['zip', 'mrpack']:
        return False

    # Set up directory structures and extract the modpack
    cwd = get_cwd()
    folder_check(tmpsvr)
    os.chdir(tmpsvr)

    test_server = os.path.join(tempDir, 'importtest')
    send_log('scan_modpack', f"extracting '{file_path}' to '{test_server}'...", 'info')
    folder_check(test_server)
    os.chdir(test_server)

    extract_archive(file_path, test_server)
    move_files_root(test_server)

    if progress_func:
        progress_func(50)

    send_log('scan_modpack', f"scanning '{test_server}' to detect metadata...", 'info')


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
            if ("%" in flag or "${" in flag or '-Xmx' in flag or '-Xms' in flag or len(flag) < 5) and (not flag.strip().startswith('@')):
                continue
            for exclude in ['-install', '-server', '-jar', '--nogui', '-nogui', '-Command', '-fullversion', '-version', '-mcversion', '-loader', '-downloadminecraft', '-mirror']:
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
            with open(mr_index, 'r', encoding='utf-8', errors='ignore') as f:

                # Reorganize .json for ease of iteration
                metadata = [
                    {
                        'url': i['downloads'][0],
                        'file_name': os.path.basename(i['path']),
                        'destination': os.path.join(test_server, os.path.dirname(i['path']))
                    }
                    for i in json.loads(f.read())["files"]
                ]

                def get_mod_url(mod_data):
                    try: return cs_download_url(mod_data['url'], mod_data['file_name'], mod_data['destination'])
                    except Exception as e: return False

                # Iterate over additional content to see if it's available to be downloaded
                with ThreadPoolExecutor(max_workers=20) as pool:
                    for result in pool.map(get_mod_url, metadata):
                        if not result: return result

                send_log('scan_modpack', f"determined modpack type 'Modrinth'", 'info')


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

                matches = {'forge': 0, 'fabric': 0, 'neoforge': 0, 'quilt': 0}
                matches['forge'] += len(re.findall(r'\bforge\b', raw_content, re.IGNORECASE))
                matches['fabric'] += len(re.findall(r'\bfabric\b', raw_content, re.IGNORECASE))
                matches['neoforge'] += len(re.findall(r'\bneoforge\b', raw_content, re.IGNORECASE))
                matches['quilt'] += len(re.findall(r'\bquilt\b', raw_content, re.IGNORECASE))
                data['type'] = 'fabric' if matches['fabric'] > matches['forge'] else 'forge'
                if data['type'] == 'fabric' and matches['quilt'] > 1:
                    data['type'] = 'quilt'
                if data['type'] == 'forge' and matches['neoforge'] > 1:
                    data['type'] = 'neoforge'

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
                                with open(mod_dict, 'r', encoding='utf-8', errors='ignore') as f:
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

        send_log('scan_modpack', f"determined modpack type 'ServerStarter'", 'info')


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

        send_log('scan_modpack', f"found 'variables.txt'", 'info')


    # Approach #4: inspect launch scripts and 'server.jar'
    if not data['version'] or not data['type']:
        send_log('scan_modpack', f"no valid modpack format found, inspecting launch scripts & 'server.jar'", 'info')


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
                data['type'] = 'fabric'
                if len(split_match) >= 3:
                    if split_match[2] != 'installer.jar':
                        data['version'] = split_match[2].replace('mc.', '')
                        data['build'] = split_match[3].replace('loader.', '')
                        break


    # Approach #5: inspect server files
    if not data['version'] or not data['type']:
        send_log('scan_modpack', f"no valid scripts or 'server.jar', using a manual file scan", 'info')


        # Generate script list and iterate through each one
        file_list = glob(os.path.join(test_server, "*.txt"))
        if os.path.exists(os.path.join(test_server, 'scripts')):
            file_list = glob(os.path.join(test_server, "scripts", "*.*"))
        if os.path.exists(os.path.join(test_server, 'config')):
            file_list.extend(glob(os.path.join(test_server, "config", "*.*")))

        # Make sure they are actually files
        file_list = [file for file in file_list if os.path.isfile(file)]

        matches = {
            'forge': 0,
            'fabric': 0,
            'neoforge': 0,
            'quilt': 0,
            'versions': []
        }

        def process_matches(content):
            matches['forge'] += len(re.findall(r'\bforge\b', content, re.IGNORECASE))
            matches['fabric'] += len(re.findall(r'\bfabric\b', content, re.IGNORECASE))
            matches['neoforge'] += len(re.findall(r'\bneoforge\b', content, re.IGNORECASE))
            matches['quilt'] += len(re.findall(r'\bquilt\b', content, re.IGNORECASE))
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
        if data['type'] == 'fabric' and matches['quilt'] > 1:
            data['type'] = 'quilt'
        if data['type'] == 'forge' and matches['neoforge'] > 1:
            data['type'] = 'neoforge'
        if matches['versions']:
            data['version'] = max(set(matches['versions']), key=matches['versions'].count)


    # Get the modpack name
    if not data['name']:
        send_log('scan_modpack', f"no name was found, scraping from 'server.properties' and filename", 'info')


        # Get the name from "server.properties"
        for file in glob('*server.properties'):
            with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f.readlines():
                    if line.lower().startswith('motd='):
                        line = line.split('motd=', 1)[1]
                        process_name(line)
                        break
                else:
                    continue
                break

        # Get the name from the file if not declared in the "server.properties"
        if not data['name'] or data['name'].lower() == 'a minecraft server':
            name = os.path.basename(file_path).rsplit('.',1)[0]
            name = re.sub(r'(?<=\S)(-|_|\+)(?=\S)', ' ', name)
            if 'server' in name.lower():
                name = name[:len(name.lower().split('server')[0])].strip()
            process_name(name)

        # Add a default name case because it's not that important
        if not data['name']:
            process_name('Modpack Server')


    # Look in alternate locations for launch flags
    for file in glob(os.path.join(test_server, '*.*')):
        for key in ['jvm', 'args', 'arguments', 'param']:
            if key in os.path.basename(file):
                with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
                    for match in re.findall(r'(?<= |=|\n)--?\S+', text):
                        process_flags(match)
                    break


    # Success
    os.chdir(cwd)
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

        log_content = f"determined '{import_data['name']}' is {import_data['type'].title()} '{import_data['version']}'"
        send_log('scan_modpack', f"{log_content}: writing to '{tmpsvr}' for further processing...", 'info')
        return data


    # Failed state due to one or more issues locating required data
    else:
        log_content = f"unable to determine all the required metadata:\n'data': {data}"
        send_log('scan_modpack', log_content, 'error')
        return False


# Moves tmpsvr to actual server and checks for ACL and other file validity
def finalize_modpack(update=False, progress_func=None, *args):
    global import_data

    telepath_data = None
    if server_manager.current_server and update:
        telepath_data = server_manager.current_server._telepath_data
    try:
        if not telepath_data and new_server_info['_telepath_data']:
            telepath_data = new_server_info['_telepath_data']
    except KeyError:
        pass

    if telepath_data:
        response = api_manager.request(
            endpoint = '/create/finalize_modpack',
            host = telepath_data['host'],
            port = telepath_data['port'],
            args = {'update': update}
        )
        if progress_func and response:
            progress_func(100)
        return response



    test_server = os.path.join(tempDir, 'importtest')
    new_path = os.path.join(serverDir, str(import_data['name']))

    if import_data['name'] and os.path.exists(test_server):
        log_content = f"updating '{new_path}' from '{tmpsvr}'..." if update else f"installing '{tmpsvr}' to '{new_path}'..."
        send_log('finalize_modpack', log_content, 'info')


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
                    except IOError: send_log('finalize_modpack', "couldn't create thumbnail for server icon", 'error')
                    continue

                elif file_name == 'server-icon.png':
                    copy(item, tmpsvr)
                    continue

                elif file_name == 'modrinth.index.json':
                    copy(item, tmpsvr)
                    if os_name == 'windows': run_proc(f"attrib +H \"{os.path.join(tmpsvr, 'modrinth.index.json')}\"")
                    else: os.rename(os.path.join(tmpsvr, 'modrinth.index.json'), os.path.join(tmpsvr, '.modrinth.index.json'))
                    continue

                elif file_name.endswith('.png'): continue

                if file_name.lower() == 'eula.txt': continue

                # Recursively copy folders, and simply copy files if it already exists
                if os.path.isdir(item): copytree(item, os.path.join(tmpsvr, file_name), dirs_exist_ok=True)
                else: copy(item, tmpsvr)


        # Copy existing data from modpack if updating
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
            except: pass
            new_config.set('general', 'serverType', import_data['type'])
            server_config(import_data['name'], new_config, os.path.join(tmpsvr, server_ini))

            if progress_func:
                progress_func(33)

            # Erase server folder after copying
            safe_delete(new_path)

        else: create_server_config(import_data, True, import_data['pack_type'])


        # Copy folder to server path and delete tmpsvr
        folder_check(new_path)
        os.chdir(get_cwd())
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
            eula, time_stamp = generate_eula()
            with open(os.path.join(server_path(import_data['name']), 'eula.txt'), 'w+') as f:
                f.write(eula)

            if server_path(import_data['name'], 'server.properties'):
                content = []
                with open(os.path.join(server_path(import_data['name']), 'server.properties'), 'r', encoding='utf-8', errors='ignore') as f:
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
            os.chdir(get_cwd())
            safe_delete(tempDir)
            safe_delete(downDir)
            make_update_list()

            if progress_func:
                progress_func(100)

            action = 'updated' if update else 'imported to'
            send_log('finalize_modpack', f"successfully {action} '{new_path}'", 'info')
            return True

        else:
            action = 'updating' if update else 'importing to'
            send_log('finalize_import', f"something went wrong {action} '{new_path}'", 'error')


# Generates new information for a server update
def init_update(telepath=False, host=None):
    if telepath: server_obj = server_manager.remote_servers[host]
    else:        server_obj = server_manager.current_server
    new_server_info['name'] = server_obj.name

    send_log('init_update', f"initializing 'new_server_info' to update '{server_obj.name}'...", 'info')

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
        server_obj = server_manager.remote_servers[telepath_data['host']]

        # Report to telepath logger
        api_manager.logger._report(f'main.update_world', extra_data=f'Changing world: {path}', server_name=server_obj.name)

    else: server_obj = server_manager.current_server

    send_log('update_world', f"importing '{path}' to '{server_obj.name}'...", 'info')

    # First, save a backup
    server_obj.backup.save()

    # Delete current world
    world_path = server_path(server_obj.name, server_obj.world)
    if world_path:
        def delete_world(w: str):
            send_log('update_world', f"deleting old world '{w}'...", 'info')
            if os.path.exists(w):
                safe_delete(w)

        delete_world(world_path)
        delete_world(world_path + "_nether")
        delete_world(world_path + "_the_end")

    # Copy world to server if one is selected
    world_name = 'world'
    new_world = os.path.join(server_obj.server_path, world_name)
    if path.strip().lower() != "world":
        world_name = os.path.basename(path)
        copytree(path, new_world)

    # Fix level-type
    if version_check(server_obj.version, '>=', '1.19') and new_type == 'default':
        new_type = 'normal'

    # Change level-name in 'server.properties' and server_obj.world
    server_obj.server_properties['level-name'] = world_name
    server_obj.server_properties['level-type'] = new_type
    server_obj.server_properties['level-seed'] = new_seed

    server_obj.write_config()
    server_obj.reload_config()

    # Log final changes
    if os.path.isdir(new_world): send_log('update_world', f"successfully imported '{path}' to '{server_obj.name}'", 'info')
    else:                        send_log('update_world', f"something went wrong importing '{path}' to '{server_obj.name}'", 'info')


# Clones a server with support for Telepath
def clone_server(server_obj: object or str, progress_func=None, host=None, *args):

    if server_obj == '$remote':
        source_data = None
        destination_data = None
        server_obj = server_manager.remote_servers[host]

    else:
        source_data = server_obj._telepath_data
        destination_data = new_server_info['_telepath_data']

    success = False


    # Mode 4: remote a -> remote a
    if (source_data and destination_data) and (source_data['host'] == destination_data['host']):
        send_log('clone_server', f"<mode-4>  remotely cloning '{source_data['host']}/{server_obj.name}' on '{destination_data['host']}'", 'info')

        # Register clone_server function as an endpoint, and run this function remotely as local -> local
        response = api_manager.request(
            endpoint = '/create/clone_server',
            host = source_data['host'],
            port = source_data['port'],
            args = {'server_obj': '$remote'}
        )
        if progress_func and response:
            progress_func(100)
        success = response



    # Mode 3: remote a -> remote b
    elif source_data and destination_data:
        send_log('clone_server', f"<mode-3>  remotely cloning '{source_data['host']}/{server_obj.name}' to remote '{destination_data['host']}/{new_server_info['name']}'", 'info')

        # Download back-up from server_obj
        folder_check(downDir)
        file = telepath_download(source_data, server_obj.backup.latest['path'], downDir)
        if progress_func:
            progress_func(25)

        # Edit back-up to rename the server
        if new_server_info['name'] != server_obj.name:
            file = backup.rename_backup(file, new_server_info['name'])
        if progress_func:
            progress_func(50)

        # Upload back-up to new server
        import_data['name'] = new_server_info['name']
        import_data['path'] = telepath_upload(destination_data, file)['path']
        import_data['_telepath_data'] = None
        api_manager.request(
            endpoint = '/create/push_new_server',
            host = destination_data['host'],
            port = destination_data['port'],
            args = {'server_info': new_server_info, 'import_info': import_data}
        )
        import_data['_telepath_data'] = destination_data
        if progress_func:
            progress_func(75)

        # Import back-up to new server
        if scan_import(True) and finalize_import():
            if progress_func:
                progress_func(100)
            success = True



    # Mode 2: local -> remote
    elif not source_data and destination_data:
        send_log('clone_server', f"<mode-2>  cloning '{server_obj.name}' to remote '{destination_data['host']}/{new_server_info['name']}'", 'info')

        # Copy back-up to tempDir
        folder_check(tempDir)
        file = copy(server_obj.backup.latest.path, tempDir)
        if progress_func:
            progress_func(25)

        # Edit back-up to rename the server
        if new_server_info['name'] != server_obj.name:
            file = backup.rename_backup(file, new_server_info['name'])
        if progress_func:
            progress_func(50)

        # Upload back-up to new server
        import_data['name'] = new_server_info['name']
        import_data['path'] = telepath_upload(destination_data, file)['path']
        import_data['_telepath_data'] = None
        api_manager.request(
            endpoint = '/create/push_new_server',
            host = destination_data['host'],
            port = destination_data['port'],
            args = {'server_info': new_server_info, 'import_info': import_data}
        )
        import_data['_telepath_data'] = destination_data
        if progress_func:
            progress_func(75)

        # Import back-up to new server
        if scan_import(True) and finalize_import():
            if progress_func:
                progress_func(100)
            success = True



    # Mode 1: remote -> local
    elif source_data and not destination_data:
        send_log('clone_server', f"<mode-1>  cloning remote '{source_data['host']}/{server_obj.name}' to local '{new_server_info['name']}'", 'info')

        # Download back-up from server_obj
        folder_check(downDir)
        file = telepath_download(source_data, server_obj.backup.latest['path'], downDir)
        if progress_func:
            progress_func(33)

        # Edit back-up to rename the server
        if new_server_info['name'] != server_obj.name:
            file = backup.rename_backup(file, new_server_info['name'])
        import_data['name'] = new_server_info['name']
        import_data['path'] = file
        import_data['_telepath_data'] = None
        if progress_func:
            progress_func(66)

        # Import back-up
        if scan_import(True) and finalize_import():
            if progress_func:
                progress_func(100)
            success = True



    # Mode 0: local -> local
    else:
        send_log('clone_server', f"<mode-0>  cloning '{server_obj.name}' to '{new_server_info['name']}'", 'info')

        # Copy back-up to tempDir
        folder_check(tempDir)
        file = copy(server_obj.backup.latest.path, tempDir)
        if progress_func:
            progress_func(33)

        # Edit back-up to rename the server
        if new_server_info['name'] != server_obj.name:
            file = backup.rename_backup(file, new_server_info['name'])
        import_data['name'] = new_server_info['name']
        import_data['path'] = file
        import_data['_telepath_data'] = None
        if progress_func:
            progress_func(66)

        # Import back-up
        if scan_import(True) and finalize_import():
            if progress_func:
                progress_func(100)
            success = True

    # Log results
    if success: send_log('clone_server', f"successfully cloned '{server_obj.name}' to '{new_server_info['name']}'", 'info')
    else:       send_log('clone_server', f"something went wrong cloning '{server_obj.name}'", 'error')

    return success



# ------------------------------------------------ Server Functions ----------------------------------------------------

# Toggles favorite status in Server Manager
def toggle_favorite(server_name: str):
    config_file = server_config(server_name)
    config_file.set('general', 'isFavorite', ('false' if config_file.get('general', 'isFavorite') == 'true' else 'true'))
    server_config(server_name, config_file)

    is_favorite = bool(config_file.get('general', 'isFavorite') == 'true')
    action = 'marked' if is_favorite else 'unmarked'
    send_log('toggle_favorite', f"'server_name' is now {action} as favorite", 'info')
    return is_favorite


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
def server_config(server_name: str, write_object: configparser.ConfigParser = None, config_path: str = None):
    config_file = os.path.abspath(config_path) if config_path else server_path(server_name, server_ini)
    builds_available = list(latestMC['builds'].keys())

    # If write_object, write it to file path
    if write_object:
        send_log('server_config', f"updating configuration in '{config_file}'...")

        try:
            if write_object.get('general', 'serverType').lower() not in builds_available:
                write_object.remove_option('general', 'serverBuild')

            if os_name == "windows":
                run_proc(f"attrib -H \"{config_file}\"")

            with open(config_file, 'w') as f:
                write_object.write(f)

            if os_name == "windows":
                run_proc(f"attrib +H \"{config_file}\"")

        except Exception as e: send_log('server_config', f"error updating '{config_file}': {format_traceback(e)}", 'error')
        else:                  send_log('server_config', f"successfully updated '{config_file}'")

        return write_object


    # Read only if no config object provided
    else:
        try:
            config = configparser.ConfigParser(allow_no_value=True, comment_prefixes=';')
            config.optionxform = str
            config.read(config_file)
            send_log('server_config', f"read from '{config_file}'")
            def rename_option(old_name: str, new_name: str):
                try:
                    if config.get("general", old_name):
                        config.set("general", new_name, config.get("general", old_name))
                        config.remove_option("general", old_name)
                except: pass

            if config:
                if config.get('general', 'serverType').lower() not in builds_available:
                    config.remove_option('general', 'serverBuild')

                # Override legacy configuration options
                rename_option('enableNgrok', 'enableProxy')

            return config

        # Failed to read from config file
        except Exception as e:
            send_log('server_config', f"error reading from '{config_file}': {format_traceback(e)}", 'error')


# Creates new auto-mcs.ini config file
def create_server_config(properties: dict, temp_server=False, modpack=False):
    config = None
    config_path = os.path.join((tmpsvr if temp_server else server_path(properties['name'])), server_ini)
    send_log('create_server_config', f"generating '{config_path}'...", 'info')


    # Write default config
    try:
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
        try:    config.set('general', 'enableGeyser', str(properties['server_settings']['geyser_support']).lower())
        except: config.set('general', 'enableGeyser', 'false')
        try:    config.set('general', 'enableProxy', str(properties['server_settings']['enable_proxy']).lower())
        except: config.set('general', 'enableProxy', 'false')
        try:    config.set('general', 'customFlags', ' '.join(properties['launch_flags']))
        except: pass
        if modpack: config.set('general', 'isModpack', str(modpack))

        config.add_section('bkup')
        config.set('bkup', 'bkupAuto', 'prompt')
        config.set('bkup', 'bkupMax', '5')
        config.set('bkup', 'bkupDir', backupFolder)


        # Write file to path
        with open(config_path, 'w') as f:
            config.write(f)

        if os_name == "windows":
            run_proc(f"attrib +H \"{config_path}\"")

    except Exception as e: send_log('create_server_config', f"error creating '{config_path}': {format_traceback(e)}", 'error')
    else:                  send_log('create_server_config', f"successfully created '{config_path}'", 'info')

    return config


# Reconstruct remote API config dict to a local configparser object
def reconstruct_config(remote_config: dict or configparser.ConfigParser, to_dict=False):
    if to_dict:
        if isinstance(remote_config, dict): return remote_config
        else: return {section: dict(remote_config.items(section)) for section in remote_config.sections()}

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


# Fixes empty 'server.properties' file, and updates EULA date check
def fix_empty_properties(name):
    path = server_path(name)
    properties_file = os.path.join(path, 'server.properties')
    send_log('server_properties', f"generating new 'server.properties' for '{name}'...", 'info')

    try:
        eula, time_stamp = generate_eula()

        # EULA
        with open(os.path.join(path, 'eula.txt'), "w+") as f:
            f.write(eula)

        # server.properties
        properties = f"""#Minecraft server properties
{time_stamp}
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

        with open(properties_file, "w+") as f:
            f.write(properties)

    except Exception as e: send_log('server_properties', f"error generating '{properties_file}': {format_traceback(e)}", 'error')
    else:                  send_log('server_properties', f"successfully generated '{properties_file}'", 'info')


# server.properties function
# write_object is the dict object returned from this function
def server_properties(server_name: str, write_object=None):
    properties_file = server_path(server_name, 'server.properties')
    force_strings = ['level-seed', 'level-name', 'motd', 'resource-pack', 'resource-pack-prompt', 'resource-pack-sha1']


    # If write_object, write it to file path
    if write_object:
        send_log('server_properties', f"updating configuration in '{properties_file}'...")

        try:
            with open(properties_file, 'w', encoding='utf-8', errors='ignore') as f:
                file_contents = ""

                for key, value in write_object.items():

                    # Force boolean values
                    if str(value).lower().strip() in ['true', 'false'] and str(key) not in force_strings:
                        value = str(value).lower().strip()

                    # Force strings to be strings
                    elif str(key) in force_strings:
                        value = str(value).strip()

                    file_contents += f"{key}{'' if key.startswith('#') else ('=' + str(value))}\n"

                f.write(file_contents)

        except Exception as e: send_log('server_properties', f"error updating '{properties_file}': {format_traceback(e)}", 'error')
        else:                  send_log('server_properties', f"successfully updated '{properties_file}'")

        return write_object


    # Read only if no config object provided
    else:
        config = {}
        no_file = False

        try:
            with open(properties_file, 'r', encoding='utf-8', errors='ignore') as f:
                send_log('server_properties', f"read from '{properties_file}'")

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

                        # Force strings to be strings
                        elif line_object[0].strip() in force_strings:
                            config[line_object[0].strip()] = str(line_object[1].strip())

                        # Check for integers
                        else:
                            try:
                                config[line_object[0].strip()] = int(float(line_object[1].strip()))

                        # Normal strings
                            except ValueError:
                                config[line_object[0].strip()] = line_object[1].strip()


                    except IndexError: config[line_object[0].strip()] = ""


            # Override invalid values
            valid = False
            try:
                if int(config['max-players']) > 0: valid = True
            except: pass

            if not valid:
                config['max-players'] = 20
                config = server_properties(server_name, config)


        except Exception as e:
            send_log('server_properties', f"error reading from '{properties_file}': {format_traceback(e)}", 'error')
            no_file = True


        # Re-generate 'server.properties' if the file does not exist
        if no_file or not config:
            fix_empty_properties(server_name)
            config = server_properties(server_name)
            if config: send_log('server_properties', f"read from '{properties_file}'")
            else:      send_log('server_properties', f"something went wrong re-generating '{properties_file}'", 'error')

        return config


# Creates a new Geyser config with auto-mcs data
def create_geyser_config(server_obj: object, reset=False) -> bool:

    # Ascertain which path the config should be in
    config_name = 'config.yml'
    if server_obj.type in ['vanilla', 'forge']: return False
    if server_obj.type == 'fabric': config_path = os.path.join(server_obj.server_path, 'config', 'Geyser-Fabric')
    else:                           config_path = os.path.join(server_obj.server_path, 'plugins', 'Geyser-Spigot')
    final_path = os.path.join(config_path, config_name)
    send_log('create_geyser_config', f"writing Geyser config to '{final_path}'...", 'info')
    config_data = f"""# Setup: https://wiki.geysermc.org/geyser/setup/
bedrock:
  address: 0.0.0.0
  port: 19132
  clone-remote-port: true
  motd1: "{server_obj.name}"
  motd2: "{server_obj.server_properties['motd']}"
  server-name: "{server_obj.name}"
  compression-level: 6
  enable-proxy-protocol: false
remote:
  address: auto
  port: 25565
  auth-type: online
  allow-password-authentication: true
  use-proxy-protocol: false
  forward-hostname: true
floodgate-key-file: key.pem
pending-authentication-timeout: 120
command-suggestions: true
passthrough-motd: true
passthrough-player-counts: true
legacy-ping-passthrough: false
ping-passthrough-interval: 3
forward-player-ping: false
max-players: 100
debug-mode: false
show-cooldown: title
show-coordinates: true
disable-bedrock-scaffolding: false
emote-offhand-workaround: "disabled"
cache-images: 0
allow-custom-skulls: true
max-visible-custom-skulls: 128
custom-skull-render-distance: 32
add-non-bedrock-items: true
above-bedrock-nether-building: false
force-resource-packs: true
xbox-achievements-enabled: true
log-player-ip-addresses: true
notify-on-new-bedrock-update: true
unusable-space-block: minecraft:barrier
metrics:
  enabled: false
  uuid: 00000000-0000-0000-0000-000000000000
scoreboard-packet-threshold: 20
enable-proxy-connections: false
mtu: 1400
use-direct-connection: true
disable-compression: true
config-version: 4
"""


    # Write to disk
    try:
        if not os.path.exists(final_path) or reset:
            folder_check(config_path)
            with open(final_path, 'w+') as yml:
                yml.write(config_data)

    except Exception as e: send_log('create_geyser_config', f"error creating '{final_path}': {format_traceback(e)}", 'error')
    else:                  send_log('create_geyser_config', f"successfully created '{final_path}'", 'info')

    return os.path.exists(final_path)


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
            if ram >= 32:    ram = 6
            elif ram >= 16:  ram = 4
            else:            ram = 2
        except:              ram = 2

        if properties['type'].lower() in ["forge", "neoforge", "fabric", "quilt"]:
            ram = ram + 2

    else: ram = int(config_spec)

    return ram


# Generates server batch/shell script
def generate_run_script(properties, temp_server=False, custom_flags=None, no_flags=False):

    # Change directory to server path
    cwd = get_cwd()
    current_path = tmpsvr if temp_server else server_path(properties['name'])
    script_name  = f'{start_script_name}.{"bat" if os_name == "windows" else "sh"}'
    script_path = os.path.join(current_path, script_name)
    folder_check(current_path)
    os.chdir(current_path)


    script = ""
    ram = calculate_ram(properties)
    formatted_flags = '\n'.join(custom_flags.split(" ")) if custom_flags else ''
    log_flags = f' with custom flags:\n{formatted_flags}' if custom_flags else ''
    send_log('generate_run_script', f"generating run script for {properties['type'].title()} '{properties['version']}' as '{script_path}'{log_flags}...", 'info')


    # Use custom flags, or Aikar's flags if none are provided
    try:
        java_override = None

        if no_flags:
            start_flags = ''
        elif not custom_flags:
            start_flags = ' -XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200 -XX:+UnlockExperimentalVMOptions -XX:+DisableExplicitGC -XX:+AlwaysPreTouch -XX:G1HeapWastePercent=5 -XX:G1MixedGCCountTarget=4 -XX:G1MixedGCLiveThresholdPercent=90 -XX:G1RSetUpdatingPauseTimePercent=5 -XX:SurvivorRatio=32 -XX:+PerfDisableSharedMem -XX:MaxTenuringThreshold=1 -XX:G1NewSizePercent=30 -XX:G1MaxNewSizePercent=40 -XX:G1HeapRegionSize=8M -XX:G1ReservePercent=20 -XX:InitiatingHeapOccupancyPercent=15 -Dusing.aikars.flags=https://mcflags.emc.gs -Daikars.new.flags=true'
        else:

            # Override java version with custom flag
            check_override = re.search(r'^<java\d+>', custom_flags.strip())
            if check_override:
                override = check_override[0]
                custom_flags = custom_flags.replace(override, '').strip()
                if override == '<java21>':
                    java_override = java_executable['modern']
                elif override == '<java17>':
                    java_override = java_executable['lts']
                elif override == '<java8>':
                    java_override = java_executable['legacy']

            # Build start flags
            start_flags = f' {custom_flags}'


        # Do some schennanies for NeoForge
        if properties['type'] == 'neoforge':
            if java_override:
                java = java_override
            else:
                java = java_executable['modern']
            version_list = [os.path.basename(file) for file in glob(os.path.join("libraries", "net", "neoforged", "neoforge", f"{float(properties['version'][2:])}*")) if os.listdir(file)]
            arg_file = f"libraries/net/neoforged/neoforge/{version_list[-1]}/{'win_args.txt' if os_name == 'windows' else 'unix_args.txt'}"
            script = f'"{java}" -Xmx{ram}G -Xms{int(round(ram / 2))}G {start_flags} -Dlog4j2.formatMsgNoLookups=true @{arg_file} nogui'


        # Do some schennanies for Forge
        elif properties['type'] == 'forge':

            # Modern
            if version_check(properties['version'], ">=", "1.17"):
                if java_override:
                    java = java_override
                else:
                    java = java_executable["lts"] if version_check(properties['version'], '<', '1.19.3') else java_executable['modern']
                version_list = [os.path.basename(file) for file in glob(os.path.join("libraries", "net", "minecraftforge", "forge", f"1.{math.floor(float(properties['version'].replace('1.', '', 1)))}*")) if os.listdir(file)]
                arg_file = f"libraries/net/minecraftforge/forge/{version_list[-1]}/{'win_args.txt' if os_name == 'windows' else 'unix_args.txt'}"
                script = f'"{java}" -Xmx{ram}G -Xms{int(round(ram/2))}G {start_flags} -Dlog4j2.formatMsgNoLookups=true @{arg_file} nogui'

            # 1.6 to 1.16
            elif version_check(properties['version'], ">=", "1.6") and version_check(properties['version'], "<", "1.17"):
                if java_override:
                    java = java_override
                else:
                    java = java_executable["legacy"]
                script = f'"{java}" -Xmx{ram}G -Xms{int(round(ram/2))}G {start_flags} -Dlog4j2.formatMsgNoLookups=true -jar server.jar nogui'


        # Everything else
        else:
            # Make sure this works non-spigot versions
            if java_override:
                java = java_override
            else:
                java = java_executable["legacy"] if version_check(properties['version'], '<','1.17') else java_executable['lts'] if version_check(properties['version'], '<', '1.19.3') else java_executable['modern']

            # On bukkit derivatives, install geysermc, floodgate, and viaversion if version >= 1.13.2 (add -DPaper.ignoreJavaVersion=true if paper < 1.16.5)
            script = f'"{java}" -Xmx{ram}G -Xms{int(round(ram/2))}G{start_flags} -Dlog4j2.formatMsgNoLookups=true'

            if version_check(properties['version'], "<", "1.16.5") and properties['type'] in ['paper', 'purpur']:
                script += ' -DPaper.ignoreJavaVersion=true'

            # Improve performance on Purpur
            if properties['type'] == 'purpur':
                script += ' --add-modules=jdk.incubator.vector'

            jar_name = 'quilt.jar' if properties['type'] == 'quilt' else 'server.jar'

            script += f' -jar {jar_name} nogui'



        if script:
            with open(script_name, 'w+') as f: f.write(script)
            if os_name != 'windows': run_proc(f'chmod +x {script_name}')


    # Log and return from errors
    except Exception as e: send_log('generate_run_script', f"error writing to '{script_path}': {format_traceback(e)}", 'error')
    else:                  send_log('generate_run_script', f"successfully written to '{script_path}'", 'info')

    os.chdir(cwd)
    return script_path


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

    except Exception as e:
        send_log('generate_server_list', f'error generating server list: {format_traceback(e)}', 'error')

    send_log('generate_server_list', f"generated server list from valid servers in '{serverDir}':\n{server_list}")
    return server_list


# Retrieve modrinth config for updates
def get_modrinth_data(name: str):
    index = os.path.join(server_path(name), f'{"" if os_name == "windows" else "."}modrinth.index.json')
    index_data = {"name": None, "version": '0.0.0', "latest": '0.0.0'}
    send_log('get_modrinth_data', f"checking the Modrinth API for available updates to '{name}'...")


    # Check for 'modrinth.index.json' to get accurate server information
    if index:
        if os_name == 'windows': run_proc(f"attrib -H \"{index}\"")

        with open(index, 'r', encoding='utf-8', errors='ignore') as f:
            data = json.loads(f.read())

            try: index_data['name'] = data['name']
            except KeyError: pass
            try: index_data['version'] = data['versionId']
            except KeyError: pass

        if os_name == 'windows': run_proc(f"attrib +H \"{index}\"")


        # Check online for latest version
        try:
            online_modpack = addons.get_modpack_url(addons.search_modpacks(index_data['name'])[0])
            index_data['latest'] = online_modpack.download_version
            index_data['download_url'] = online_modpack.download_url
            send_log('get_modrinth_data', f"update found for '{name}': '{online_modpack.download_url}'")
        except IndexError:
            send_log('get_modrinth_data', f"'{name}' is up to date")


    return index_data


# Return list of every valid server update property in 'applicationFolder'
def make_update_list():
    global update_list
    update_list = {}
    send_log('make_update_list', f"globally checking for server updates...", 'info')

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

            try: jarBuild = str(config.get("general", "serverBuild"))
            except configparser.NoOptionError: jarBuild = ""

            try: isModpack = str(config.get("general", "isModpack"))
            except configparser.NoOptionError: isModpack = ""


            # Check if modpack needs an update if detected (show only if auto-updates are enabled)
            if isModpack:
                if isModpack == 'mrpack':
                    modpack_data = get_modrinth_data(name)
                    if (modpack_data['version'] != modpack_data['latest']) and not modpack_data['latest'].startswith("0.0.0"):
                        serverObject[name]["needsUpdate"] = "true"
                        serverObject[name]["updateString"] = modpack_data['latest']
                        serverObject[name]["updateUrl"] = modpack_data['download_url']


            # Check if normal server needs an update (show only if auto-updates are enabled)
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

    # Log update list
    if update_list: send_log('make_update_list', f"updates are available for:\n{str(list(update_list.keys()))}", 'info')
    else:           send_log('make_update_list', 'all servers are up to date', 'info')

    return update_list


# Check if port is open on host
def check_port(ip: str, port: int, timeout=120):

    # Check connectivity
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    result = sock.connect_ex((ip, port))

    # Log connectivity
    success = result == 0
    if success: send_log('check_port', f"successfully connected to '{ip}:{port}'")
    else:       send_log('check_port', f"could not connect to '{ip}:{port}': timed out", 'error')

    return success


# Assigned from 'menu.py' to update IP text on screens
refresh_ips = None

# Returns active IP address of 'name'
def get_current_ip(name: str, proxy=False):
    global public_ip

    private_ip = ""
    original_port = "25565"
    updated_port = ""
    final_addr = {}

    lines = []

    if server_path(name, "server.properties"):
        with open(server_path(name, "server.properties"), 'r', encoding='utf-8', errors='ignore') as f:
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
                        send_log('get_current_ip', f"temporarily changing port for '{name}' to '*:{updated_port}' due to conflict", 'warning')
                        break
                f.writelines(lines)


        # More ip info
        if not private_ip:
            private_ip = get_private_ip()

        if not proxy:
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

                            # Make a few attempts to verify WAN connection
                            port_check = False
                            for attempt in range(10):
                                port_check = check_port(public_ip, final_port, timeout=5)
                                if port_check:
                                    break

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


# Recursively gathers all config files with a specific depth (default 3)
# Returns {"dir1": ['match1', 'match2', 'match3', ...]}
valid_config_formats = ['properties', 'yml', 'yaml', 'tml', 'toml', 'json', 'json5', 'ini', 'txt', 'snbt']
[telepath_download_whitelist['names'].append(f'.{ext}') for ext in valid_config_formats]
def gather_config_files(name: str, max_depth: int = 3) -> dict[str, list[str]]:
    root = server_path(name)
    excludes = [
        'version_history.json', 'version_list.json', 'usercache.json', 'banned-players.json', 'banned-ips.json',
        'banned-subnets.json', 'whitelist.json', 'ops.json', 'ops.txt', 'whitelist.txt', 'banned-players.txt',
        'banned-ips.txt', 'eula.txt', 'bans.txt', 'modrinth.index.json', 'amscript', server_ini
    ]
    final_dict = {}
    send_log('gather_config_files', f"recursively retrieving all config files in '{name}'...")

    def process_dir(path: str, depth: int = 0):
        basename = os.path.basename(path)
        if depth > max_depth or basename.startswith('.') or basename in excludes:
            return

        match_list = []

        try:
            with os.scandir(path) as items:
                for item in items:

                    # Add to final_dict if it's a valid config file
                    if item.is_file() and os.path.splitext(item.name)[1].strip('.') in valid_config_formats and item.name not in excludes and not item.name.startswith('.'):
                        match_list.append(item.path)

                    # Continue recursion until max_depth is reached
                    elif item.is_dir():
                        process_dir(item.path, depth + 1)

        except (PermissionError, FileNotFoundError) as e:
            send_log('gather_config_files', f"error accessing '{path}': {format_traceback(e)}", 'error')

        if match_list:
            final_dict[path] = sorted(match_list, key=lambda x: (os.path.basename(x) != 'server.properties', os.path.basename(x)))

    process_dir(root)
    files = dict(sorted(final_dict.items(), key=lambda item: (os.path.basename(item[0]) != name, os.path.basename(item[0]))))
    debug_only = f':\n{files}' if debug else ''
    if files: send_log('gather_config_files', f"found {len(files)} config file(s) in '{name}'{debug_only}", 'info')
    else:     send_log('gather_config_files', f"no config files were found in '{name}'", 'info')

    return files

# Replace configuration files on this instance from a Telepath client
def update_config_file(server_name: str, upload_path: str, destination_path: str):

    # Don't allow move to itself
    if upload_path == destination_path:
        return False

    # Only allow files to get replaced in the current server
    if not destination_path.startswith(server_path(server_name)):
        return False

    # Only allow files which already exist
    if not os.path.isfile(destination_path):
        return False

    # Only allow files from uploadDir
    if not upload_path.startswith(uploadDir):
        return False

    # Only allow accepted file types
    for ext in valid_config_formats:
        if destination_path.endswith(f'.{ext}') or upload_path.endswith(f'.{ext}'):
            break
    else:
        return False

    # Move file to intended path
    send_log('update_config_file', f"replacing '{destination_path}' with '{upload_path}'")
    move(upload_path, destination_path)
    clear_uploads()

# Allows parsing of any OS path style
def cross_platform_path(path, depth=1):
    """
    Returns the last `depth` components of the given path.

    For Unix-style paths:
      - Only forward slashes ("/") are considered true directory separators.
      - Backslashes are used to escape characters (e.g. spaces) and are unescaped in the result.
      - If the original path is absolute (starts with '/'), the returned value will also be absolute.

    For Windows-style paths:
      - Both backslashes ("\") and forward slashes ("/") are treated as separators.
      - No unescaping is performed.

    If depth is greater than the available number of components,
    the original path is returned.

    Parameters:
      path (str): The file path.
      depth (int): The number of path components (from the right) to return (default is 1).

    Returns:
      str: The resulting subpath.
    """
    if depth < 1:
        raise ValueError("depth must be >= 1")

    def sanitize(text: str):
        return text.lstrip('/').lstrip('\\')

    # Remove any trailing separators to avoid an empty final component.
    path = re.sub(r'[\\/]+$', '', path)

    # Detect Windows-style paths:
    # - They often start with a drive letter (e.g., "C:\...")
    # - Or they contain backslashes and no forward slashes.
    if re.match(r'^[A-Za-z]:', path) or ('\\' in path and '/' not in path):
        # Split on one or more of either separator.
        parts = re.split(r'[\\/]+', path)
        # If the requested depth is more than available parts, return the original path.
        if depth >= len(parts):
            return sanitize(path)
        # Join the last `depth` parts with the Windows separator.
        return sanitize('\\'.join(parts[-depth:]))
    else:
        # Unix-style path.
        # In Unix, the only true separator is "/"; backslashes are escapes.
        is_absolute = path.startswith('/')
        # Split on "/" (ignoring empty strings which can occur if the path is absolute)
        parts = [p for p in path.split('/') if p]
        if depth > len(parts):
            # If depth is more than available, return the original path.
            return sanitize(path)
        # Grab the last `depth` components.
        selected_parts = parts[-depth:]
        # Unescape any escaped characters in each component (e.g. turn "\ " into " ").
        selected_parts = [re.sub(r'\\(.)', r'\1', comp) for comp in selected_parts]
        result = '/'.join(selected_parts)
        if is_absolute:
            result = '/' + result
        return sanitize(result)

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


# Updates the server icon with a new image
# Returns: [bool: success, str: reason]
valid_image_formats = ["*.png", "*.jpg", "*.jpeg", "*.gif", "*.jpe", "*.jfif", "*.tif", "*.tiff", "*.bmp", "*.icns", "*.ico", "*.webp"]
def update_server_icon(server_name: str, new_image: str = False) -> [bool, str]:
    icon_path = os.path.join(server_path(server_name), 'server-icon.png')

    # Delete if no image was provided
    if not new_image or new_image == 'False':
        if os.path.isfile(icon_path):
            try: os.remove(icon_path)
            except: pass

        send_log('update_server_icon', f"successfully cleared the server icon for '{server_name}'", 'info')
        return (True, 'icon removed successfully') if not os.path.exists(icon_path) else (False, 'something went wrong, please try again')


    # First, check if the image has a valid extension
    extension = new_image.rsplit('.')[-1].lower()
    if f'*.{extension}' not in valid_image_formats:
        send_log('update_server_icon', f"failed to change server icon for '{server_name}': '{new_image}' is not in valid extensions:\n{valid_image_formats}", 'error')
        return (False, f'".{extension}" is not a valid extension')

    # Next, try to convert the image
    try:
        img = Image.open(new_image)
        width, height = img.size

        # Handle images with an alpha channel
        mode = 'RGBA' if img.mode in ['RGBA', 'LA'] else 'RGB'
        size = 64

        # Calculate new dimensions while maintaining aspect ratio
        if width > height:
            # Landscape orientation
            new_width = size
            new_height = int(size * height / width)
        else:
            # Portrait orientation or square
            new_width = int(size * width / height)
            new_height = size

        # Resize the image while maintaining aspect ratio
        resized_img = img.resize((new_width, new_height), Image.LANCZOS)

        # Create new square image to re-center if needed
        new_img = Image.new(mode, (size, size))
        paste_x = (size - new_width) // 2
        paste_y = (size - new_height) // 2
        new_img.paste(resized_img, (paste_x, paste_y))

        # Save image to new path
        if os.path.isfile(icon_path):
            os.remove(icon_path)
        new_img.save(icon_path, 'PNG')

    except Exception as e:
        send_log('update_server_icon', f"error processing new server icon: {format_traceback(e)}", 'error')
        return (False, 'failed to convert the icon')

    send_log('update_server_icon', f"successfully processed and replaced the server icon for '{server_name}' with '{new_image}'", 'info')
    return (True, 'successfully updated the icon')


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
            age = abs(dt.today().day - dt.fromtimestamp(os.stat(final_path).st_mtime).day)
            if age < 3: return final_path
            else:       os.remove(final_path)

        elif not check_free_space():
            return default_image

        folder_check(head_cache)
        download_url(url, user, head_cache)

        if os.path.exists(final_path):
            return final_path
        else:
            return default_image

    except Exception as e:
        send_log('get_player_head', f"error retrieving player head icon for '{user}': {format_traceback(e)}", 'error')
        return default_image


# Compatibility to cache server icon with telepath
def get_server_icon(server_name: str, telepath_data: dict, overwrite=False):
    if not (app_online and server_name):
        return None

    try:
        name = f"{telepath_data['host'].replace('/', '+')}+{server_name}"
        icon_cache = os.path.join(cacheDir, 'icons')
        final_path = os.path.join(icon_cache, name)

        if os.path.exists(final_path) and not overwrite:
            age = abs(dt.today().day - dt.fromtimestamp(os.stat(final_path).st_mtime).day)
            if age < 3:
                return final_path
            else:
                os.remove(final_path)

        elif not check_free_space():
            return None

        folder_check(icon_cache)
        if os.path.exists(final_path) and overwrite:
            os.remove(final_path)

        # Ensure that the server actually has an icon
        try:
            telepath_download(telepath_data, telepath_data['icon-path'], icon_cache, rename=name)
        except TypeError:
            # send_log('update_server_icon', f"'{telepath_data['host']}/{server_name}' doesn't have a server icon")
            return None


        if os.path.exists(final_path):
            return final_path
        else:
            return None

    except Exception as e:
        send_log('update_server_icon', f"error retrieving icon for '{telepath_data['host']}/{server_name}': {format_traceback(e)}", 'error')
        return None


# Clean-up amscript IDE cache
def clear_script_cache(script_path):
    json_path = None

    # Ignore if the script isn't in the app directory
    if not script_path.startswith(applicationFolder):
        return

    # Attempt to delete the file
    try:
        file_name = os.path.basename(script_path).split('.')[0] + '.json'
        if script_path.startswith(telepathScriptDir):
            json_dir = os.path.join(cacheDir, 'ide', 'fold-regions', 'telepath')
        else:
            json_dir = os.path.join(cacheDir, 'ide', 'fold-regions', 'local')
        json_path = os.path.join(json_dir, file_name)
        if os.path.isfile(json_path):
            os.remove(json_path)

    # Log on failure
    except Exception as e:
        send_log('clear_script_cache', f"failed to remove IDE script cache '{json_path}': {format_traceback(e)}", 'error')



# --------------------------------------------- Global Logging Function ------------------------------------------------

class LoggingManager():

    # Internal log wrapper
    def _send_log(self, message: str, level: str = None, **kw):
        return self._dispatch(self.__class__.__name__, message, level, **kw)

    def __init__(self):
        self._line_header = '   >  '
        self._max_run_logs = 3
        self.path = os.path.join(applicationFolder, "Logs", "application")

        # Identify this launch (timestamp + pid -> short hash)
        self._launch_ts  = dt.now()
        self._launch_id  = hashlib.sha1(f"{self._launch_ts.isoformat()}-{os.getpid()}".encode("utf-8")).hexdigest()[:6]

        # Initialize db stuff
        self._log_db = deque(maxlen=2500)
        self._db_lock = threading.Lock()  # protect _log_db
        self._io_lock = threading.Lock()  # serialize stdout writes to avoid interweaving

        # Log since last UI action
        self._since_ui = deque(maxlen=1000)

        # Async pipeline
        self._q: 'queue.Queue[tuple[str, str, str, str, bool]]' = queue.Queue(maxsize=100)
        self._stop = threading.Event()
        self._writer = threading.Thread(target=self._worker, name="log-writer", daemon=True)
        self._writer.setDaemon(True)
        self._writer.start()

        # All stacks listed here are not logged unless "debug" is enabled
        self.debug_stacks = ('kivy', 'uvicorn')


        # Branding banner
        self._title = self._generate_title()
        self._send_log(f'{Style.BRIGHT}{self._title}{Style.RESET_ALL}', 'info', _raw=True)

    def _generate_title(self, box_drawing=True):
        self.header_len = 50
        box = ('┃', '━', '┏', '┓', '┗', '┛') if box_drawing else ('│', '—', '—', '—', '—', '—')
        header = f"{box[2]}{box[1] * round(self.header_len / 2)}  auto-mcs v{app_version}  {box[1]* round(self.header_len / 2)}{box[3]}"
        logo   = '\n'.join([f'{box[0]}   {i.ljust(len(header) - 5, " ")}{box[0]}' for i in text_logo])
        footer = f"{box[4]}{box[1] * (len(header) - 2)}{box[5]}"
        return f'{header}\n{logo}\n{footer}'

    # Receive from the rest of the app
    def _dispatch(self, object_data: str, message: str, level: str = None, stack: str = None, _raw=False):
        if '.' not in object_data and object_data not in ['wrapper', 'telepath']:
            object_data = f'{__name__}.{object_data}'
        object_data = object_data.strip('. \n')
        if not level: level = 'debug'
        if not stack: stack = 'core'


        # Reject debug log stacks
        if stack in self.debug_stacks and level == 'debug':
            return



        # Enqueue raw fields
        payload = (str(object_data), str(message), str(level), str(stack), _raw)

        # Enqueue line for background write
        try:
            # Prefer dropping general level data if the queue is full
            if self._q.full() and level in ('debug', 'info'):
                try: self._q.get_nowait(); self._q.task_done()
                except queue.Empty: pass
            self._q.put_nowait(payload)

        except queue.Full:

            # For warnings/errors/fatal, block briefly to avoid loss
            try: self._q.put(payload, timeout=0.25)

            # Last resort: block until there is space so critical logs still go through the worker
            except queue.Full: self._q.put(payload)

    def _add_entry(self, object_data: str, message: str, level: str, stack: str):
        data = {'time': dt.now(), 'object_data': object_data, 'level': level, 'stack': stack, 'message': message}
        with self._db_lock:
            self._log_db.append(data)

            # Reset the "since UI" window only on UI actions
            if stack == 'ui' and ('interaction:' in message or 'view:' in message):
                self._since_ui.clear()
            self._since_ui.append(data)

        return data

    def _worker(self):

        # Drain until stop is set and queue is empty
        while not self._stop.is_set() or not self._q.empty():
            try: object_data, message, level, stack, _raw = self._q.get(timeout=0.2)
            except queue.Empty: continue

            try:
                # Build the entry on the worker thread
                data = self._add_entry(object_data, message, level, stack)
                self._print(data, _raw)

            except Exception as e: sys.__stderr__.write(f"Logging worker error: {format_traceback(e)}")
            finally: self._q.task_done()

    def _prune_logs(self):
        files = sorted(
            (p for p in glob(os.path.join(self.path, "auto-mcs_*.log")) if os.path.isfile(p)),
            key = os.path.getmtime,
            reverse = True
        )
        for p in files[self._max_run_logs:]:
            try: os.remove(p)
            except OSError: pass

    def _get_file_name(self):
        time_stamp = self._launch_ts.strftime(fmt_date("%#H-%M-%S_%#m-%#d-%y"))
        file_name  = f"auto-mcs_{time_stamp}.log"
        return os.path.join(self.path, file_name)

    def _print(self, data: dict, _raw: bool = False):

        object_data = data['object_data']
        message = data['message']
        level = data['level']
        stack = data['stack']
        time_obj = data['time']


        # Only send messages if logging is enabled, and only log debug messages in debug mode
        if not (enable_logging and not (not debug and level == 'debug')):
            return

        # Treat low-priority stack logs as "debug"
        if stack in self.debug_stacks and (not debug and level in ('debug', 'info', 'warning')):
            return


        level_color = {
            'debug': Fore.MAGENTA,
            'info': Fore.GREEN,
            'warning': Fore.YELLOW,
            'error': Fore.RED,
            'critical': Fore.RED,
            'fatal': Fore.RED,
        }

        object_color = {
            'debug': Fore.CYAN,
            'info': Fore.CYAN,
            'warning': Fore.LIGHTYELLOW_EX,
            'error': Fore.LIGHTRED_EX,
            'critical': Fore.LIGHTRED_EX,
            'fatal': Fore.LIGHTRED_EX,
        }

        text_color = {
            'debug': Fore.RESET,
            'info': Fore.RESET,
            'warning': Fore.YELLOW,
            'error': Fore.RED,
            'critical': Fore.RED,
            'fatal': Fore.RED,
        }

        def fmt_block(text: str, color: Fore = Fore.CYAN):
            return f'{Style.BRIGHT}{Fore.LIGHTBLACK_EX}[{color}{text}{Fore.LIGHTBLACK_EX}]{Style.RESET_ALL}'

        with self._io_lock:

            # Make sure start logo displays correctly on Windows
            if _raw and (f' {app_title} v{app_version} ' in message) and (os_name == 'windows'):
                message = self._generate_title(False)

            for x, line in enumerate(message.splitlines(), 0):

                if not _raw:
                    object_width = 37 - len(level)
                    timestamp = time_obj.strftime('%I:%M:%S %p')
                    tc = text_color.get(level, Fore.CYAN)
                    content = f'{tc}{line.strip()}' if x == 0 else f'{Fore.LIGHTBLACK_EX}{self._line_header}{tc}{line.rstrip()}'
                    line = (
                        f"{fmt_block(timestamp, Fore.WHITE)} "
                        f"{fmt_block(level.upper(), level_color.get(level, Fore.CYAN))} "
                        f"{fmt_block(f'{stack}: {object_data}'.ljust(object_width), object_color.get(level, Fore.CYAN))} "
                        f"{content}"
                    ) if x == 0 else content

                else: line = line.strip()

                encoding = (sys.stdout and sys.stdout.encoding) or "utf-8"
                formatted = line.encode(encoding, errors="ignore").decode(encoding, errors="ignore")
                print(formatted)


    # Wait until all queued logs are written
    def flush(self, timeout: float = None):
        start = time.monotonic()
        self._q.join()
        if timeout is not None and (time.monotonic() - start) > timeout:
            return False
        return True

    # Stop the writer thread and flush
    def close(self, graceful: bool = True):
        if graceful:
            self._stop.set()
            self.flush()
        else:
            self._stop.set()

    # Flush the queue and write the entire in-memory log to a file, and clear the db
    def dump_to_disk(self) -> str:

        # Ensure background thread has printed/added everything it has
        self.flush()
        path = self._get_file_name()

        # Don’t write if logging is disabled or deque is empty, but still return the path for consistency
        if not enable_logging or not self._log_db:
            with self._db_lock: self._log_db.clear()
            return path


        self._send_log(f"flushing logger to '{path}'")

        # Snapshot and clear
        with self._db_lock:
            entries = list(self._log_db)
            self._log_db.clear()

        # Write plain text, no ANSI
        if not os.path.exists(path):
            folder_check(self.path)
            with open(path, "a+", encoding="utf-8", newline="\n") as f:
                launch_stamp = self._launch_ts.strftime(fmt_date("%#I:%M:%S %p %#m/%#d/%Y"))
                f.write(f"# {launch_stamp} (pid {os.getpid()}) id={self._launch_id}\n\n")

        with open(path, "a+", encoding="utf-8", newline="\n") as f:
            for e in entries:

                time_obj    = e["time"]
                object_data = e["object_data"]
                message     = e["message"]
                level       = e["level"]
                stack       = e["stack"]

                # Replace title log with formatting-free one
                if f' {app_title} v{app_version} ' in message and "█" in message:
                    f.write(self._title + '\n')
                    continue

                # Only log debug messages in debug mode
                if not debug and level == 'debug':
                    continue

                # Treat low-priority stack logs as "debug"
                if stack in self.debug_stacks and (not debug and level in ('debug', 'info', 'warning')):
                    continue


                # Format lines like print method
                object_width = 37 - len(level)
                timestamp = time_obj.strftime("%I:%M:%S %p")
                block = f"{stack}: {object_data}".ljust(object_width)

                lines = str(message).splitlines() or [""]
                for i, line in enumerate(lines):
                    if i == 0: f.write(f"[{timestamp}] [{level.upper()}] [{block}] {line.rstrip()}\n")
                    else: f.write(f"{self._line_header}{line.rstrip()}\n")

        self._prune_logs()
        api_manager.logger.dump_to_disk()
        return path

    # Get everything since the last UI action
    def since_last_interaction(self) -> list:

        # Ensure background thread has printed/added everything it has
        self.flush()

        # Snapshot and clear
        with self._db_lock:
            entries = list(self._since_ui)

        log_list = []
        for e in entries:

            time_obj    = e["time"]
            object_data = e["object_data"]
            message     = e["message"]
            level       = e["level"]
            stack       = e["stack"]

            # Skip title log with formatting-free one
            if self._title in message:
                continue


            # Format lines like print method
            object_width = 37 - len(level)
            timestamp = time_obj.strftime("%I:%M:%S %p")
            block = f"{stack}: {object_data}".ljust(object_width)

            lines = str(message).splitlines() or [""]
            for i, line in enumerate(lines):
                if i == 0: log_line = f"[{timestamp}] [{level.upper()}] [{block}] {line.strip()}\n"
                else:      log_line = f"{self._line_header}{line.strip()}\n"
                log_list.append(log_line)

        return log_list

# Global logger wrapper
# Levels: 'debug', 'info', 'warning', 'error', 'fatal'
# Stacks: 'core', 'ui', 'api', 'amscript'
if is_child_process:
    log_manager = None
    send_log = lambda *_: None
else:
    log_manager: LoggingManager = LoggingManager()
    send_log    = log_manager._dispatch


# Check for Docker/ARM architecture (required after logger is created)
is_docker = check_docker()
is_arm    = check_arm()



# ---------------------------------------------- Global Config Function ------------------------------------------------

# Handles all operations when writing/reading from global config. Adding attributes changes the config file
class ConfigManager():

    # Internal log wrapper
    def _send_log(self, message: str, level: str = None):
        return send_log(self.__class__.__name__, message, level)

    def __init__(self):
        self._path = os.path.join(configDir, 'app-config.json')
        self._defaults = self._init_defaults()
        self._data = Munch({})

        # Initialize default values
        if os.path.exists(applicationFolder):
            if self.load_config(): self._send_log(f"initialized ConfigManager successfully", 'info')
            else:                  self._send_log(f"failed to initialize ConfigManager", 'error')

    # Specify default values
    @staticmethod
    def _init_defaults():
        defaults = Munch({})
        defaults.fullscreen = False
        defaults.geometry = {}
        defaults.auto_update = True
        defaults.locale = None
        defaults.sponsor_reminder = None
        defaults.discord_presence = True
        defaults.prompt_feedback = True
        defaults.telepath_settings = {
            'enable-api': False,
            'api-host': "0.0.0.0",
            'api-port': 7001,
            'show-banners': True,
            'id_hash': None
        }
        defaults.ide_settings = {
            'fullscreen': False,
            'font-size': 15,
            'geometry': {}
        }
        return defaults

    def __setattr__(self, key, value):
        if key.startswith('_'):
            super().__setattr__(key, value)
        elif key not in self._defaults:
            raise AttributeError(f"'{self.__class__.__name__}' does not support '{key}'")
        else:
            self._data[key] = value
            self.save_config()

    def __getattr__(self, key):
        if key == '__setstate__':
            self._data = Munch({})
            self._path = os.path.join(configDir, 'app-config.json')
            self._defaults = self._init_defaults()
            self.load_config()

        if key in self._data:

            # First, fix empty dictionaries
            if isinstance(self._data[key], dict):
                for k, v in self._defaults[key].items():
                    if k not in self._data[key]:
                        self._data[key][k] = v

            # Then return the value
            return self._data[key]

        elif key in self._defaults:
            return self._defaults[key]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{key}'")


    def load_config(self):
        if os.path.exists(self._path):
            with open(self._path, 'r', encoding='utf-8', errors='ignore') as file:
                try:
                    self._data = json.loads(file.read().replace('ide-settings', 'ide_settings'))
                    self._send_log(f"successfully loaded global configuration from '{self._path}'")
                    return True
                except json.decoder.JSONDecodeError:
                    pass

        self._send_log('failed to read global configuration, resetting...', 'error')
        self.reset()

    def save_config(self):
        try:
            folder_check(os.path.dirname(self._path))
            with open(self._path, 'w') as file:
                json.dump(self._data, file, indent=2)

        except Exception as e: self._send_log(f"failed to save global configuration to '{self._path}': {format_traceback(e)}", 'error')
        else:                  self._send_log(f"successfully saved global configuration to '{self._path}'")

    def reset(self):
        if os.path.exists(self._path):
            os.remove(self._path)
        self._data = self._defaults.copy()
        self.save_config()

# Global config manager
app_config: ConfigManager = ConfigManager()



# ----------------------------------------------- playit.gg Integration ------------------------------------------------

# Handles all methods and data relating to playit.gg integration
class PlayitManager():

    # Raised when a tunnel has an issue being modified
    class TunnelException(BaseException):
        pass

    # Handles tunnel cache for retaining certain tunnel when the API is unreliable
    class TunnelCacheHelper():
        def __init__(self, root_path: str):
            self._path = os.path.join(root_path, 'tunnel-cache.json')
            self._data = {}
            self._read_data()

        def _read_data(self):
            if os.path.exists(self._path):
                with open(self._path, 'r', encoding='utf-8', errors='ignore') as f:
                    self._data = json.loads(f.read())

        def _write_data(self):
            with open(self._path, 'w+') as f:
                f.write(json.dumps(self._data))

        # Write a tunnel's data to the cache
        def add_tunnel(self, tunnel_id: str, data: dict) -> bool:
            self._data[tunnel_id] = data
            self._write_data()
            return tunnel_id in self._data

        # Remove a tunnel from the cache
        def remove_tunnel(self, tunnel_id: str) -> bool:
            if tunnel_id in self._data:
                del self._data[tunnel_id]
            self._write_data()
            return tunnel_id not in self._data

        # Retrieve the cache from a tunnel
        def get_tunnel(self, tunnel_id: str) -> dict:
            if tunnel_id in self._data:
                return self._data[tunnel_id]
            return {}

    # Houses all tunnel data
    class Tunnel():
        def __init__(self, _parent: 'PlayitManager', tunnel_data: dict):
            self._parent = _parent
            self._data_id = tunnel_data['alloc']['data']['id']
            self._cost = tunnel_data['port_count']

            # Format networking data
            self.region = tunnel_data['alloc']['data']['region']
            self.type = tunnel_data['tunnel_type'] if tunnel_data['tunnel_type'] else 'both'
            self.protocol = tunnel_data['port_type']

            # Mechanism to load data from cache if it's missing from the API
            try:
                self.port = tunnel_data['origin']['data']['local_port']
                self.host = tunnel_data['origin']['data']['local_ip']
            except:

                # If tunnel is not cached and port is unknown, delete itself
                try:
                    cached_data = self._parent.tunnel_cache.get_tunnel(self._data_id)
                    self.port = cached_data['local_port']
                    self.host = cached_data['local_ip']
                except:
                    self.delete()

            # Format playit tunnel data
            self.id = tunnel_data['id']
            self.domain = tunnel_data['alloc']['data']['assigned_domain']
            self.remote_port = tunnel_data['alloc']['data']['port_start']
            self.hostname = f'{self.domain}:{self.remote_port}' if self.type == 'both' else self.domain


            date_object = dt.fromisoformat(tunnel_data['created_at'].replace("Z", "+00:00"))
            timezone = dt.now().astimezone().tzinfo
            self.created = date_object.astimezone(timezone)

            # If tunnel is assigned to a server object
            self.in_use = False

        def delete(self):
            self._parent._delete_tunnel(self)

    # Internal log wrapper
    def _send_log(self, message: str, level: str = None):
        return send_log(self.__class__.__name__, message, level)

    def __init__(self):
        base_path = "https://github.com/playit-cloud/playit-agent/releases"
        self._download_url = {
            'windows': f'{base_path}/download/v0.15.26/playit-windows-x86_64-signed.exe',
            'linux': f'{base_path}/download/v0.15.26/playit-linux-{"aarch" if is_arm else "amd"}64',
            'macos': f'{base_path}/download/v0.15.13/playit-darwin-{"arm" if is_arm else "intel"}'
        }[os_name]
        self._filename = {
            'windows': 'playit.exe',
            'linux': 'playit',
            'macos': 'playit'
        }[os_name]


        # General stuff
        self.provider = 'playit'
        self.directory = os.path.join(toolDir, 'playit')
        self.exec_path = os.path.join(self.directory, self._filename)
        self.toml_path = os.path.join(self.directory, 'playit.toml')
        self.tunnel_cache = self.TunnelCacheHelper(self.directory)
        self.config = {}

        self.initialized = False
        self.session = requests.Session()
        self.service = None


        # Client info
        self.agent_web_url = None
        self.agent_id = None
        self.secret_key = None
        self.max_tunnels = 4
        self.tunnels = {'tcp': [], 'udp': [], 'both': []}



    # ----- OS/filesystem handling -----
    # Check if the agent is installed
    def _check_agent(self) -> bool:
        return os.path.exists(self.exec_path)

    # Load playit.toml into an attribute
    def _load_config(self) -> bool:
        if os.path.exists(self.toml_path):
            with open(self.toml_path, 'r', encoding='utf-8', errors='ignore') as toml:
                self._send_log(f"loading playit configuration from '{self.toml_path}'")
                strip_list = "'\" \n"
                self.config = {
                    k.strip(strip_list): v.strip(strip_list)
                    for k, v in (line.split('=', 1) for line in toml.readlines())
                }
        return bool(self.config)

    # Deletes config and starts over
    def _reset_config(self) -> bool:
        if os.path.exists(self.toml_path):
            os.remove(self.toml_path)

        self.config = {}
        return not os.path.exists(self.toml_path)

    # Download and install the agent
    def _install_agent(self, progress_func: callable = None) -> bool:
        if not app_online:
            raise ConnectionError('Downloading playit requires an internet connection')
        if self.service:
            raise RuntimeError("Can't re-install while playit is running")

        # If ngrok is present, delete it
        ngrok = os.path.join(applicationFolder, 'Tools', ('ngrok-v3.exe' if os_name == 'windows' else 'ngrok-v3'))
        if os.path.exists(ngrok):
            os.remove(ngrok)

        # Delete current version first
        final_path = os.path.join(self.directory, self._filename)
        self._send_log(f"installing playit agent from '{self._download_url}' to '{final_path}'...", 'info')
        if self._check_agent():
            os.remove(self.exec_path)

        # Install the new version
        folder_check(self.directory)
        download_url(self._download_url, self._filename, self.directory, progress_func)

        # chmod if UNIX-based
        if os_name != 'windows':
            run_proc(f'chmod +x "{self.exec_path}"')

        success = self._check_agent()
        if success: self._send_log(f"successfully installed playit agent to '{final_path}'", 'info')
        else:       self._send_log(f"something went wrong installing playit agent from '{self._download_url}'", 'error')

        return success

    # Removes the agent from the filesystem
    def _uninstall_agent(self) -> bool:
        if self.service:
            raise RuntimeError("Can't delete while playit is running")

        if os.path.exists(self.directory):
            self._send_log(f"deleting playit agent and configuration from '{self.directory}'", 'info')
            safe_delete(self.directory)

        return not self._check_agent()

    # Starts the agent and returns status
    def _start_agent(self) -> bool:
        if not self.service:
            self.service = subprocess.Popen(f'"{self.exec_path}" -s --secret_path "{self.toml_path}"', stdout=subprocess.PIPE, shell=True)
            self._send_log(f"launched playit agent with PID {self.service.pid}")
        return bool(self.service.poll())

    # Stops the agent and returns output
    def _stop_agent(self) -> str:
        if self.service and self.service.poll() is None:
            pid = self.service.pid

            # Iterate over self and children to find playit process
            try:             parent = psutil.Process(self.service.pid)
            except KeyError: parent = self.service

            # Windows
            if os_name == "windows":
                children = parent.children(recursive=True)
                for proc in children:
                    if proc.name() == "playit.exe":
                        run_proc(f"taskkill /f /pid {proc.pid}")
                        break

            # macOS
            elif os_name == "macos":
                if parent.name() == "playit":
                    run_proc(f"kill {parent.pid}")

            # Linux
            else:
                if parent.name() == "playit":
                    run_proc(f"kill {parent.pid}")
                else:
                    children = parent.children(recursive=True)
                    for proc in children:
                        if proc.name() == "playit":
                            run_proc(f"kill {proc.pid}")
                            break

            self.service.kill()
            self._send_log(f"stopped playit agent with PID {pid}")

        return_code = self.service.poll() if self.service else 0
        del self.service
        self.service = None

        return return_code



    # ----- API auth handling -----
    # Retrieves claim code from the console output
    def _get_claim_code(self) -> str:
        if self.service:

            # Loop over output for claim code
            url = 'https://playit.gg/claim/'
            code = None

            # Be careful with this, it could potentially wait for a new line forever
            for line in iter(self.service.stdout.readline, ""):
                if url in line.decode():
                    code = line.decode().split(url)[-1].strip()
                    break

            return code

    # Claim the agent as a guest user
    def _claim_agent(self) -> bool:
        self._start_agent()
        claim_code = self._get_claim_code()

        # First, retrieve guest auth cookie for agent
        url_claim = f"https://playit.gg/login/create?redirect=/claim/{claim_code}?type=self-managed&_data=routes/login.create"
        body = {'email': "", 'password': "", 'confirm-password': "", '_action': "guest"}
        response = self.session.post(url_claim, data=body)
        cookie = response.headers['set-cookie'].split(';')[0]
        response.headers['Cookie'] = cookie

        # Wait until agent is claimed
        url_claim_code = f"https://playit.gg/claim/{claim_code}?type=self-managed&_data=routes%2Fclaim%2F%24claimCode"
        while self.session.get(url_claim_code).json()['status'] == 'fail':
            time.sleep(1)

        # Accept claim and send to agent
        url_accept = f"https://playit.gg/claim/{claim_code}/accept?type=self-managed&_data=routes/claim/$claimCode/accept"
        self.session.post(
            url_accept,
            data = {
                "_action": "accept",
                "source": "",
                "agent_name": f"from-key-{claim_code[:4]}",
                "agent_type": "self-managed",
            },
        )

        # Retrieve secret key
        data = self.session.post("https://api.playit.gg/claim/exchange", json={"code": claim_code}).json()
        self.secret_key = data['data']['secret_key']

        # Successfully claimed agent
        self._send_log(f"successfully claimed playit agent to account")
        self._stop_agent()
        return bool(self.secret_key)



    # ----- API tunnel handling -----
    # Creates two lists of all tunnels, sorted by protocol
    def _retrieve_tunnels(self) -> dict:
        self.tunnels = {'tcp': [], 'udp': [], 'both': []}

        data = self.session.post("https://api.playit.gg/tunnels/list", json={"agent_id": self.agent_id}).json()
        if data['status'] == 'success':

            # Update maximum tunnels allowed by account (seems to be inaccurate)
            # self.max_tunnels = data['data']['tcp_alloc']['allowed']

            # Create tunnel objects from tunnels
            for tunnel_data in data['data']['tunnels']:
                tunnel = self.Tunnel(self, tunnel_data)
                self.tunnels[tunnel.protocol].append(tunnel)

        return self.tunnels

    # Returns consolidated list of every tunnel
    def _return_single_list(self) -> list:
        single_list = self.tunnels['tcp']
        single_list.extend(self.tunnels['udp'])
        single_list.extend(self.tunnels['both'])
        return single_list

    # Returns True if any tunnels are in use
    def _tunnels_in_use(self) -> bool:
        return any([t.in_use for t in self._return_single_list()])

    # Returns False if protocol type exceeds the max tunnel limit
    # protocol: 'tcp', 'udp', or 'both'
    def _check_tunnel_limit(self) -> bool:
        tunnel_count = sum(t._cost for t in self.tunnels['both'])
        tunnel_count += sum(t._cost for t in self.tunnels['tcp'])
        tunnel_count += sum(t._cost for t in self.tunnels['udp'])
        return not bool(tunnel_count >= self.max_tunnels)

    # Create a tunnel with
    # protocol: 'tcp', 'udp', or 'both'
    def _create_tunnel(self, port: int = 25565, protocol: str = 'tcp') -> Tunnel:
        if port not in range(1024, 65535):
            port = 25565

        # Can't exceed maximum tunnels specified
        if not self._check_tunnel_limit():
            raise self.TunnelException(f"Your account can't create more than {self.max_tunnels} tunnels")

        tunnel_type = {
            'tcp': 'minecraft-java',
            'udp': 'minecraft-bedrock',
            'both': None
        }[protocol]
        tunnel_data = {
            "type": "create-tunnel",
            "tunnel_type": tunnel_type,
            "port_type": protocol,
            "port_count": 2 if protocol == 'both' else 1,
            "local_ip": "127.0.0.1",
            "local_port": port,
            "agent_id": self.agent_id
        }


        # Send the request to create a tunnel
        try:
            tunnel_id = self.session.post("https://api.playit.cloud/account", json=tunnel_data).json()['id']
            if tunnel_id: self.tunnel_cache.add_tunnel(tunnel_id, tunnel_data)

            self._retrieve_tunnels()

            # Lookup method to reverse search the actual ID
            for tunnel in self.tunnels[protocol]:
                if tunnel_id == tunnel._data_id:
                    self._send_log(f"successfully created a tunnel with ID '{tunnel.id}' ({tunnel.hostname})")
                    return tunnel

        except KeyError:
            pass

    # Delete a tunnel with the object
    def _delete_tunnel(self, tunnel: Tunnel) -> bool:
        tunnel_status = self.session.post("https://api.playit.gg/tunnels/delete", json={'tunnel_id': tunnel.id}).json()
        if tunnel_status['status'] == 'success':
            self.tunnel_cache.remove_tunnel(tunnel._data_id)
            self.tunnels[tunnel.protocol].remove(tunnel)
            self._send_log(f"successfully deleted a tunnel with ID '{tunnel.id}' ({tunnel.hostname})")
            return tunnel not in self.tunnels[tunnel.protocol]
        else:
            return False

    # Deletes all tunnels
    def _clear_tunnels(self) -> dict:
        [tunnel.delete() for tunnel in self.tunnels['tcp']]
        [tunnel.delete() for tunnel in self.tunnels['udp']]
        [tunnel.delete() for tunnel in self.tunnels['both']]
        self.tunnels = {'tcp': [], 'udp': [], 'both': []}
        return self.tunnels



    # ----- General use -----
    # Configures the playit session and retrieves the agent key
    def initialize(self) -> bool:
        if not self._check_agent():
            return False

        # If a .toml isn't generated, the guest is unclaimed
        if not os.path.exists(self.toml_path):
            self._claim_agent()
            if not os.path.exists(self.toml_path):
                with open(self.toml_path, 'w+') as f:
                    f.write(f'secret_key = "{self.secret_key}"\n')

        # Otherwise, get the secret key from .toml
        else:
            try:
                self._load_config()
                self.secret_key = self.config['secret_key']

            # If the key couldn't be retrieved, delete .toml and try again
            except KeyError:
                self._reset_config()
                self._initialize()

        # Agent ID
        self.session.headers['Authorization'] = f'agent-key {self.secret_key}'
        data = self.session.post("https://api.playit.gg/agents/rundata").json()
        self.agent_id = data['data']['agent_id']
        self.agent_web_url = f'https://playit.gg/account/agents/{self.agent_id}/tunnels'

        # Get current tunnels
        self._retrieve_tunnels()

        self.initialized = True
        self._send_log(f"initialized playit agent with account URL: {self.agent_web_url}")
        return self.initialized

    # Get a tunnel by port and (optionally type)
    # Will recycle old tunnels if a new one needs to be made to not exceed the account limit
    # protocol: 'tcp', 'udp', or 'both'
    def get_tunnel(self, port: int, protocol: str = 'tcp', ensure: bool = False) -> Tunnel:
        self._retrieve_tunnels()

        for tunnel in self.tunnels[protocol]:
            if int(tunnel.port) == int(port) and not tunnel.in_use:
                return tunnel

        # If ensure is True, create the tunnel if it doesn't exist
        else:
            if ensure:

                # Remove the oldest tunnel before creating a new once if limit is exceeded
                if not self._check_tunnel_limit():
                    for tunnel in sorted(self._return_single_list(), key=lambda t: t.created):
                        tunnel.delete()
                        if self._check_tunnel_limit():
                            break

                return self._create_tunnel(port, protocol)

    # Initializes tunnel for a server object
    def start_tunnel(self, server_obj: object) -> Tunnel or False:
        if not self.initialized:
            if not self.initialize():
                return False

        port = int(server_obj.run_data['network']['address']['port'])
        protocol = 'both' if server_obj.geyser_enabled else 'tcp'

        tunnel = self.get_tunnel(port, protocol, ensure=True)
        if tunnel:
            tunnel.in_use = True

            # Add the tunnel to the server's run_data
            server_obj.run_data['playit-tunnel'] = tunnel
            # Ignore the tunnel with server_obj._telepath_run_data()
            self._start_agent()
            self._send_log(f"started a tunnel with ID '{tunnel.id}' ({tunnel.hostname})")
        return tunnel

    # Stops the current tunnel of the server object
    def stop_tunnel(self, server_obj: object) -> False:
        if not self.initialized:
            return False

        # Get tunnel from run_data
        tunnel = server_obj.run_data['playit-tunnel']
        tunnel.in_use = False

        # Stop agent only if no tunnels are in use
        if not self._tunnels_in_use() and self.service:
            self._send_log(f"stopped a tunnel with ID '{tunnel.id}' ({tunnel.hostname})")
            self._stop_agent()

# Global playit.gg manager
playit: PlayitManager = PlayitManager()



# ---------------------------------------------- Global Search Function ------------------------------------------------

# Generates content for all global searches
class SearchManager():

    # Internal log wrapper
    def _send_log(self, message: str, level: str = None):
        return send_log(self.__class__.__name__, message, level)

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
                ScreenObject('Home', 'MainMenuScreen', {'Update auto-mcs': None, 'View changelog': f'{project_link}/releases/latest', 'Create a new server': 'CreateServerModeScreen', 'Import a server': 'ServerImportScreen', 'Change language': 'ChangeLocaleScreen', 'Telepath': 'TelepathManagerScreen'}, ['addonpack', 'modpack', 'import modpack']),
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
                ScreenObject('Back-up Manager', 'ServerBackupScreen', {'Save a back-up now': None, 'Restore from a back-up': 'ServerBackupRestoreScreen', 'Enable automatic back-ups': None, 'Specify maximum back-ups': None, 'Open back-up directory': None, 'Migrate back-up directory': None, 'Clone this server': 'ServerCloneScreen'}, ['backup', 'revert', 'snapshot', 'restore', 'save', 'clone']),
                ScreenObject('Access Control', 'ServerAclScreen', {'Configure bans': None, 'Configure operators': None, 'Configure the whitelist': None}, ['player', 'user', 'ban', 'white', 'op', 'rule', 'ip', 'acl', 'access control']),
                ScreenObject('Add-on Manager', 'ServerAddonScreen', {'Download add-ons': 'ServerAddonSearchScreen', 'Import add-ons': None, 'Toggle add-on state': None, 'Update add-ons': None}, ['mod', 'plugin', 'addon', 'extension']),
                ScreenObject('Script Manager', 'ServerAmscriptScreen', {'Download scripts': 'ServerAmscriptSearchScreen', 'Import scripts': None, 'Create a new script': 'CreateAmscriptScreen', 'Edit a script': None, 'Open script directory': None}, ['amscript', 'script', 'ide', 'develop']),
                ScreenObject('Server Settings', 'ServerSettingsScreen', {"Edit configuration files": 'ServerConfigScreen', "Edit 'server.properties'": None, 'Open server directory': None, 'Specify memory usage': None, 'Change MOTD': None, 'Specify IP/port': None, 'Change launch flags': None, 'Enable proxy (playit)': None, 'Install proxy (playit)': None, 'Enable Bedrock support': None, 'Enable automatic updates': None, 'Update this server': None, "Change 'server.jar'": 'MigrateServerTypeScreen', 'Rename this server': None, 'Change world file': 'ServerWorldScreen', 'Delete this server': None}, ['ram', 'memory', 'server.properties', 'properties', 'rename', 'delete', 'bedrock', 'proxy', 'ngrok', 'playit', 'update', 'jvm', 'motd', 'yml', 'config'])
            ]
        }

    # Cache the guides to a .json file
    def cache_pages(self):
        if not app_online:
            self._send_log(f"failed to fully initialize SearchManager: {app_title} is offline", 'error')
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
            with open(cache_file, 'r', encoding='utf-8', errors='ignore') as f:
                self.guide_tree = json.loads(f.read())
                self._send_log(f"initialized SearchManager from cache in '{cache_file}'", 'info')
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
        self._send_log(f"initialized SearchManager from '{base_url}'", 'info')
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

                    # Change results for proxy installation
                    if setting.lower() == 'enable proxy (playit)' and not playit._check_agent():
                        continue
                    if setting.lower() == 'install proxy (playit)' and playit._check_agent():
                        continue

                    # If server is up-to-date, hide update prompt
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
        self._send_log(f"searching for '{query}'...")

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
        self._send_log(f"results for '{query}':\n{match_list}")

        return match_list

# Base search result
class SearchObject():
    def __init__(self):
        self.type = 'undefined'
        self.score = 0

    def __repr__(self):
        title = getattr(self, 'title', None)
        return f'<{self.__class__.__name__} "{title}">'

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
