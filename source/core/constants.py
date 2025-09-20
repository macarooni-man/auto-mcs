from shutil import rmtree, copytree, copy, ignore_patterns, move, disk_usage
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime as dt, date
from random import randrange, choices
from difflib import SequenceMatcher
from typing import TYPE_CHECKING
from colorama import Fore, Style
from urllib.parse import quote
from collections import deque
from bs4 import BeautifulSoup
from copy import deepcopy
from pathlib import Path
from munch import Munch
import multiprocessing
from glob import glob
from nbt import nbt
import cloudscraper
import unicodedata
import subprocess
import threading
import traceback
import platform
import requests
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
import sys
import os
import re


# ---------------------------------------------- Global Variables ------------------------------------------------------

app_version = "2.3.4"
ams_version = "1.5"
telepath_version = "1.2"
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

valid_image_formats = [
    "*.png", "*.jpg", "*.jpeg", "*.gif", "*.jpe", "*.jfif",
    "*.tif", "*.tiff", "*.bmp", "*.icns", "*.ico", "*.webp"
]

valid_config_formats = [
    'properties', 'yml', 'yaml', 'tml', 'toml', 'json',
    'json5', 'ini', 'txt', 'snbt'
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
        docker_info = ', Docker' if is_docker else ''
        return f"{distro} (k-{kernel}, {arch}{docker_info})"

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
    send_log(object_data, f'initializing {app_title} with the following properties:\n{formatted_properties}', 'info', 'ui')


# App/Assets folder
launch_path: str = None
try:
    if hasattr(sys, '_MEIPASS'):
        executable_folder = sys._MEIPASS
        gui_assets = os.path.join(executable_folder, 'ui', 'assets')
    else:
        executable_folder = os.path.abspath(".")
        gui_assets = os.path.join(executable_folder, 'ui', 'assets')

except FileNotFoundError:
    executable_folder = '.'
    gui_assets = os.path.join(executable_folder, 'ui', 'assets')


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
if TYPE_CHECKING: import core
server_manager: 'core.server.manager.ServerManager' = None
search_manager: 'SearchManager' = None
backup_lock    = {}


# Maximum memory
total_ram  = round(psutil.virtual_memory().total / 1073741824)
max_memory = int(round(total_ram - (total_ram / 4)))

# Replacement for os.system to prevent CMD flashing, and also for debug logging
def run_proc(cmd: str, return_text=False, log_only_in_debug=False) -> str or int:
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

    if return_code != 0 and (debug or not log_only_in_debug):
        send_log('run_proc', f"'{cmd}': returned exit code {result.returncode} {log_content}", 'error')
    else:
        send_log('run_proc', f"'{cmd}': returned exit code {result.returncode} {log_content}")

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
        if 'Alpine' in run_proc('uname -v', True, log_only_in_debug=True).strip():
            return True
    cgroup = Path('/proc/self/cgroup')
    docker_check = Path('/.dockerenv').is_file() or cgroup.is_file() and 'docker' in cgroup.read_text()
    if docker_check: send_log('check_docker', f'{app_title} is running inside a Docker container')
    return docker_check
is_docker: bool

# Check if OS is ARM
def check_arm() -> bool:
    command = 'echo %PROCESSOR_ARCHITECTURE%' if os_name == 'windows' else 'uname -m'
    arch = run_proc(command, True, log_only_in_debug=True).strip()
    return arch in ['aarch64', 'arm64']
is_arm: bool



# Global amscripts

# Grabs amscript files from GitHub repo for downloading internally
ams_web_list = []
def get_repo_scripts() -> list:
    from source.core.server import amscript
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



# ---------------------------------------------- Global Functions ------------------------------------------------------

# Functions and data for translation
locale_file = os.path.join(gui_assets, 'locales.json')
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


# Retrieves the refresh rate of the display to calculate consistent animation speed
def get_refresh_rate() -> float or None:
    if headless: return
    global refresh_rate, anim_speed

    try:
        if os_name == "windows":
            rate = run_proc('powershell Get-WmiObject win32_videocontroller | findstr "CurrentRefreshRate"', True, log_only_in_debug=True)
            if "CurrentRefreshRate" in rate:
                refresh_rate = round(float(rate.splitlines()[0].split(":")[1].strip()))

        elif os_name == 'macos':
            rate = run_proc('system_profiler SPDisplaysDataType | grep Hz', True, log_only_in_debug=True)
            if "@ " in rate and "Hz" in rate:
                refresh_rate = round(float(re.search(r'(?<=@ ).*(?=Hz)', rate.strip())[0]))

        # Linux
        else:
            rate = run_proc('xrandr | grep "*"', True, log_only_in_debug=True)
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


# Hide Kivy widgets
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


# Removes invalid characters from a filename
def sanitize_name(value, addon=False) -> str:

    if value == 'WorldEdit for Bukkit':
        return 'WorldEdit'

    value = '-'.join([v.strip() for v in value.split(":")])
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\'\w\s-]', '', value)
    return re.sub(r'[-\s]+', '-', value).strip('-_')


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



# ------------------------------------------------ Server Functions ----------------------------------------------------

# Verify portable java is available in '.auto-mcs\Tools', if not install it
modern_pct = 0
lts_pct    = 0
legacy_pct = 0
def java_check(progress_func=None):
    from source.core.server.foundry import new_server_info

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
            lts_filename    = f'lts-java.{os.path.basename(java_url[os_name]["lts"]).split(".", 1)[1]}'
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
                timer = threading.Timer(0, function=avg_total)
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


# Check if port is open on host
def check_port(ip: str, port: int, timeout=120):

    # Check connectivity
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    result = sock.connect_ex((ip, port))

    # Log connectivity
    success = result == 0
    if success: send_log('check_port', f"successfully connected to '{ip}:{port}'")
    elif debug: send_log('check_port', f"could not connect to '{ip}:{port}': timed out", 'error')

    return success


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



# ----------------------------------------------- Telepath Functions ---------------------------------------------------

# Downloads a file to a telepath session --> destination path
# Whitelist is for restricting downloadable content
telepath_download_whitelist = {
    'paths': [serverDir, scriptDir, backupFolder],
    'names': ['.ams', '.amb', 'server-icon.png', *[f'.{ext}' for ext in valid_config_formats]]
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

        # If it's a sub-attribute
        if '.' in var: root, attr = [i.strip() for i in var.split('.', 1)]
        else: root = var; attr = None

        # Get root value
        try: value = getattr(sys.modules[__name__], root)
        except Exception as e: value = None; print(format_traceback(e))

        if attr:
            try: value = getattr(value, attr)
            except: value = None

        return value


# Returns to Telepath clients that this instance is set to 'ignore_close'
def telepath_busy() -> bool:
    return ignore_close and server_manager.remote_servers


# Removes invalid characters for a Telepath nickname
def format_nickname(nickname) -> str:
    formatted = re.sub('[^a-zA-Z0-9 _().-]', '', nickname.lower())
    formatted = re.sub(r'[\s-]+', '-', formatted)

    # Remove leading and trailing hyphens
    formatted = formatted.strip('-')

    # If the length of the string is greater than 20 characters
    if len(formatted) > 20 and '-' in formatted:
        formatted = formatted.split('-', 1)[0]

    return formatted


# Helper method for sorting and retrieving data via the API
def sync_attr(self, name):
    if name != '__all__':
        return getattr(self, name)
    else:
        blacklist = ['addon', 'backup', 'acl', 'script_manager', 'script_object', 'run_data', 'taskbar', '_manager']
        def allow(x):
            return ((not callable(getattr(self, x))) and (str(x) not in blacklist) and (not str(x).endswith('__')))
        return {a: getattr(self, a) for a in dir(self) if allow(a)}



# -------------------------------------------- Global Logging Functions ------------------------------------------------

class LoggingManager():

    # Internal log wrapper
    def _send_log(self, message: str, level: str = None, **kw):
        return self._dispatch(self.__class__.__name__, message, level, **kw)

    def __init__(self):
        self._line_header = '   >  '
        self._max_run_logs = 3
        self._object_width = 40
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
        if '.' not in object_data and object_data not in ['main', 'telepath']:
            object_data = f'{__name__}.{object_data}'
        if any([object_data.startswith(i) for i in ('source.core.', 'source.ui.')]):
            object_data = object_data.split('.', 2)[-1]
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
                    object_width = self._object_width - len(level)
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
                object_width = self._object_width - len(level)
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



# --------------------------------------------- Global Config Functions ------------------------------------------------

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
        if os.path.exists(self._path): os.remove(self._path)
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


        # Delete the cache file and reset
        def clear_cache(self):
            if os.path.exists(self._path): os.remove(self._path)
            self._data = {}

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
        _parent:     'PlayitManager' = None
        _cost:       str  = None

        id:          str  = None
        status:      str  = None
        in_use:      bool = None
        region:      str  = None
        type:        str  = None
        protocol:    str  = None
        port:        int  = None
        host:        str  = None
        domain:      str  = None
        remote_port: int  = None
        hostname:    str  = None
        created:     dt   = None

        def __init__(self, _parent: 'PlayitManager', tunnel_data: dict):
            self._parent = _parent
            self._cost = tunnel_data['port_count']
            self.id = tunnel_data['id']
            self.type = tunnel_data['tunnel_type'] if tunnel_data['tunnel_type'] else 'both'
            self.protocol = tunnel_data['port_type']

            # if Tunnel is not ready
            self.status = tunnel_data['alloc']['status']
            if self.status == 'pending': return

            # Format networking data
            self.region = tunnel_data['alloc']['data']['region']

            # Mechanism to load data from cache if it's missing from the API
            try:
                self.port = int(tunnel_data['origin']['data']['local_port'])
                self.host = tunnel_data['origin']['data']['local_ip']
            except:

                # If tunnel is not cached and port is unknown, delete itself
                try:
                    cached_data = self._parent.tunnel_cache.get_tunnel(self.id)
                    self.port = int(cached_data['local_port'])
                    self.host = cached_data['local_ip']
                except:
                    self.delete()

            # Format playit tunnel data
            self.domain = tunnel_data['alloc']['data']['assigned_domain']
            self.remote_port = int(tunnel_data['alloc']['data']['port_start'])
            self.hostname = f'{self.domain}:{self.remote_port}' if self.type == 'both' else self.domain


            date_object = dt.fromisoformat(tunnel_data['created_at'].replace("Z", "+00:00"))
            timezone = dt.now().astimezone().tzinfo
            self.created = date_object.astimezone(timezone)

            # If this tunnel is currently assigned to a ServerObject
            self.in_use = False

        def __repr__(self):
            return f"<PlayitManager.{self.__class__.__name__} '{self.hostname}'>"

        def delete(self):
            self._parent._delete_tunnel(self)

    # Internal log wrapper
    def _send_log(self, message: str, level: str = None):
        return send_log(self.__class__.__name__, message, level)

    def __init__(self):
        self._git_base = "https://github.com/playit-cloud/playit-agent/releases"
        self._api_base = "https://api.playit.gg"
        self._web_base = "https://playit.gg"

        self._exec_version = {
            'windows': '0.16.2',
            'linux':   '0.16.2',
            'macos':   '0.15.13'
        }[os_name]

        self._download_url = {
            'windows': f'{self._git_base}/download/v{self._exec_version}/playit-windows-x86_64-signed.exe',
            'linux':   f'{self._git_base}/download/v{self._exec_version}/playit-linux-{"aarch" if is_arm else "amd"}64',
            'macos':   f'{self._git_base}/download/v{self._exec_version}/playit-darwin-{"arm" if is_arm else "intel"}'
        }[os_name]

        self._filename = {
            'windows': 'playit.exe',
            'linux':   'playit',
            'macos':   'playit'
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
        self.max_tunnels = 4
        self.tunnels = {'tcp': [], 'udp': [], 'both': []}

        self._agent_id    = None   # Installed agent ID (executable)
        self._proto_key   = None   # Protocol registry key
        self._session_key = None   # For login URL to guest account
        self._secret_key  = None   # For authentication to guest account



    # ----- OS/filesystem handling -----
    # Check if the agent is installed
    def _check_agent(self) -> bool:
        return os.path.isfile(self.exec_path)

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

        reset = not os.path.exists(self.toml_path)

        if reset:
            self.config = {}
            self._send_log('successfully reset playit configuration')
        else: self._send_log('failed to reset playit configuration', 'error')

        return reset

    # Download and install the agent
    def install_agent(self, progress_func: callable = None) -> bool:

        if not app_online:
            log_content = "Downloading playit requires an internet connection"
            self._send_log(log_content, 'error')
            raise ConnectionError(log_content)

        if self.service:
            log_content = "Can't re-install while playit is running"
            self._send_log(log_content, 'error')
            raise RuntimeError(log_content)


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
    def uninstall_agent(self, keep_config=True) -> bool:

        if not self._check_agent():
            self._send_log("can't uninstall as playit isn't installed")
            return True

        if self.service:
            log_content = "Can't delete while playit is running"
            self._send_log(log_content, 'error')
            raise RuntimeError(log_content)

        if os.path.exists(self.directory):
            self._send_log(f"deleting playit agent and configuration from '{self.directory}'", 'info')
            os.remove(self.exec_path) if keep_config else safe_delete(self.directory)

        return not self._check_agent()

    # Updates the agent to the latest version
    def update_agent(self) -> bool:
        success = False

        if self._check_agent():
            try:
                uninstalled = self.uninstall_agent()
                self.tunnel_cache.clear_cache()
                installed   = self.install_agent()
                success = uninstalled and installed

            except Exception as e:
                self._send_log(f'failed to update the playit client: {format_traceback(e)}', 'error')

            if success: self._send_log('successfully updated the playit client ', 'info')

        return success

    # Starts the agent and returns status
    def _start_agent(self) -> bool:

        if not self.service:
            self.service = subprocess.Popen(f'"{self.exec_path}" -s --secret_path "{self.toml_path}"', stdout=subprocess.PIPE, shell=True)
            self._send_log(f"launched playit agent with PID {self.service.pid}")

        return self.service is not None and self.service.poll() is None

    # Stops the agent and returns output
    def _stop_agent(self) -> str:

        # Kill service if it's currently running
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
            url = f'{self._web_base}/claim/'
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
        url_claim = f"{self._web_base}/login/create?redirect=/claim/{claim_code}?type=self-managed&_data=routes/login.create"
        body = {'email': "", 'password': "", 'confirm-password': "", '_action': "guest"}
        response = self.session.post(url_claim, data=body)
        cookie = response.headers['set-cookie'].split(';')[0]
        response.headers['Cookie'] = cookie

        # Wait until agent is claimed
        url_claim_code = f"{self._web_base}/claim/{claim_code}?type=self-managed&_data=routes%2Fclaim%2F%24claimCode"
        while self.session.get(url_claim_code).json()['status'] == 'fail':
            time.sleep(1)

        # Accept claim and send to agent
        url_accept = f"{self._web_base}/claim/{claim_code}/accept?type=self-managed&_data=routes/claim/$claimCode/accept"
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
        data = self._request('claim/exchange', json={"code": claim_code})
        self._secret_key = data['data']['secret_key']

        # Successfully claimed agent
        self._send_log(f"successfully claimed playit agent to account")
        self._stop_agent()
        return bool(self._secret_key)

    # Register client protocol version with the server
    def _proto_register(self) -> bool:
        proto_data = {
            'agent_version': {
                'official': True,
                'details_website': None,
                'version': {
                    'platform': os_name,
                    'version': self._exec_version
                }
            },
            'client_addr': '0.0.0.0:0',
            'tunnel_addr': '0.0.0.0:0'
        }

        response = self._request('proto/register', json=proto_data)
        if 'status' in response and response['status'] == 'success':
            self._proto_key = response['data']['key']

        return bool(self._proto_key)


    # ----- API tunnel handling -----
    def _request(self, endpoint: str, *args, **kwargs):
        return self.session.post(f"{self._api_base}/{endpoint.strip('/')}", *args, **kwargs).json()

    # Creates two lists of all tunnels, sorted by protocol
    def _retrieve_tunnels(self) -> dict:
        self.tunnels = {'tcp': [], 'udp': [], 'both': []}

        data = self._request('tunnels/list', json={"agent_id": self._agent_id})
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
            raise self.TunnelException(f"This account can't create more than {self.max_tunnels} tunnel(s)")

        tunnel_type = {
            'tcp': 'minecraft-java',
            'udp': 'minecraft-bedrock',
            'both': None
        }[protocol]

        tunnel_data = {
            "name": f'{tunnel_type}_{gen_rstring(4).lower()}',
            "tunnel_type": tunnel_type,
            "port_type": protocol,
            "port_count": 2 if protocol == 'both' else 1,
            "enabled": True,
            "origin": {
                "type": "agent",
                "data": {
                    "agent_id": self._agent_id,
                    "local_ip": '127.0.0.1',
                    "local_port": port,
                },
            },
        }


        # Send the request to create a tunnel
        try:
            data = self._request('tunnels/create', json=tunnel_data)
            tunnel_id = data['data']['id']

            # Success
            if tunnel_id:
                self.tunnel_cache.add_tunnel(tunnel_id, tunnel_data)

                # Wait until tunnel is live (up to 15s)
                for _ in range(15):
                    self._retrieve_tunnels()

                    # Lookup method to reverse search the actual ID
                    for tunnel in self.tunnels[protocol]:
                        if tunnel.status != 'pending' and tunnel_id == tunnel.id:
                            self._send_log(f"successfully created a tunnel with ID '{tunnel.id}' ({tunnel.hostname})")
                            return tunnel

                    time.sleep(1)

        except Exception as e:
            self._send_log(f"failed to create a tunnel for '{protocol}:{port}': {format_traceback(e)}")

    # Delete a tunnel with the object
    def _delete_tunnel(self, tunnel: Tunnel) -> bool:
        tunnel_status = self._request('tunnels/delete', json={'tunnel_id': tunnel.id})

        if tunnel_status['status'] == 'success':
            self.tunnel_cache.remove_tunnel(tunnel.id)
            self.tunnels[tunnel.protocol].remove(tunnel)
            self._send_log(f"successfully deleted a tunnel with ID '{tunnel.id}' ({tunnel.hostname})")
            return tunnel not in self.tunnels[tunnel.protocol]

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
                    f.write(f'secret_key = "{self._secret_key}"\n')

        # Otherwise, get the secret key from .toml
        else:
            try:
                self._load_config()
                self._secret_key = self.config['secret_key']

            # If the key couldn't be retrieved, delete .toml and try again
            except KeyError:
                self._reset_config()
                self._initialize()

        # Agent ID
        self.session.headers['Authorization'] = f'agent-key {self._secret_key}'
        agent_data = self._request('agents/rundata')
        self._agent_id = agent_data['data']['agent_id']

        # Get login URL
        guest_data = self._request('login/guest')
        self._session_key = guest_data['data']['session_key']
        self.agent_web_url = f'{self._web_base}/login/guest-account/{self._session_key}'

        # Register client protocol
        self._proto_register()

        # Get current tunnels
        self._retrieve_tunnels()

        self.initialized = True
        self._send_log(f"initialized playit agent, login from this url (select 'continue as guest'):\n{self.agent_web_url}", 'info')
        return self.initialized

    # Get a tunnel by port and (optionally type)
    # Will recycle old tunnels if a new one needs to be made to not exceed the account limit
    # protocol: 'tcp', 'udp', or 'both'
    def get_tunnel(self, port: int, protocol: str = 'tcp', ensure: bool = False) -> Tunnel:
        self._retrieve_tunnels()

        for tunnel in self.tunnels[protocol]:
            if tunnel.port == int(port) and not tunnel.in_use:
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



# ---------------------------------------------- Global Search Functions -----------------------------------------------

# Generates content for all global searches
class SearchManager():

    # Internal log wrapper
    def _send_log(self, message: str, level: str = None):
        return send_log(self.__class__.__name__, message, level)

    def get_server_list(self):
        if server_manager.menu_view_list:
            return {s._view_name: s._telepath_data for s in server_manager.menu_view_list}
        else:
            return {s: None for s in server_manager.create_server_list()}

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
        from source.core.server.foundry import new_server_info
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
