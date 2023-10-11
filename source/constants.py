from shutil import rmtree, copytree, copy, ignore_patterns
from concurrent.futures import ThreadPoolExecutor
from random import randrange, choices
from urllib.request import Request
from bs4 import BeautifulSoup
from platform import system
from threading import Timer
from copy import deepcopy
from glob import glob
from nbt import nbt
import configparser
import cloudscraper
import unicodedata
import subprocess
import functools
import threading
import ipaddress
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
import sys
import os
import re

import addons
import backup

# ---------------------------------------------- Global Variables ------------------------------------------------------

app_version = "1.0"
app_title = f"Auto-MCS v{app_version}"
project_link = "https://github.com/macarooni-man/auto-mcs"
update_urls = {'windows': None, 'linux': None}
update_md5 = {'windows': None, 'linux': None}
update_msg = ""

app_online = False
app_latest = True
app_loaded = False
version_loading = False
screen_tree = []
back_clicked = False
session_splash = ''
ignore_close = False

# Global debug mode and app_compiled, set debug to false before release
debug = False
app_compiled = getattr(sys, 'frozen', False)

public_ip = ""
ngrok_ip = {'name': None, 'ip': None}
footer_path = ""
last_widget = None

update_list = {}

latestMC = {
    "vanilla": "0.0.0",
    "forge": "0.0.0",
    "paper": "0.0.0",
    "spigot": "0.0.0",
    "craftbukkit": "0.0.0",
    "fabric": "0.0.0",

    "builds": {
        "forge": "0",
        "paper": "0",
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
appdata = os.getenv("APPDATA") if os_name == 'windows' else '~/Library/Application Support' if os_name == 'macos' else home
applicationFolder = os.path.join(appdata, ('.auto-mcs' if os_name != 'macos' else 'auto-mcs'))

saveFolder = os.path.join(appdata, '.minecraft', 'saves') if os_name != 'macos' else "~/Library/Application Support/minecraft/saves"
downDir = os.path.join(applicationFolder, 'Downloads')
backupFolder = os.path.join(applicationFolder, 'Backups')
userDownloads = os.path.join(home, 'Downloads')
serverDir = os.path.join(applicationFolder, 'Servers')

tempDir = os.path.join(applicationFolder, 'Temp')
tmpsvr = os.path.join(tempDir, 'tmpsvr')
cacheDir = os.path.join(applicationFolder, 'Cache')
configDir = os.path.join(applicationFolder, 'Config')
os_temp = os.getenv("TEMP") if os_name == "windows" else "/tmp"

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


# SSL crap on linux
if os_name == 'linux':
    os.environ['SSL_CERT_DIR'] = executable_folder
    os.environ['SSL_CERT_FILE'] = os.path.join(executable_folder, 'ca-bundle.crt')


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

import_data = {'name': None, 'path': None}

backup_lock = {}


# Maximum memory
total_ram = round(psutil.virtual_memory().total / 1073741824)
max_memory = int(round(total_ram - (total_ram / 4)))


# ---------------------------------------------- Global Functions ------------------------------------------------------

# Restarts auto-mcs by dynamically generating script
def restart_app():
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
exec {escaped_path} &
rm \"{os.path.join(tempDir, script_name)}\""""
            )

            shell_file.close()
            with open(shell_path, 'r') as f:
                print(f.read())
            run_proc(f"chmod +x \"{shell_path}\" && bash \"{shell_path}\"")
    sys.exit()

def restart_update_app():
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
exec {escaped_path} &
rm \"{os.path.join(tempDir, script_name)}\""""
            )

            shell_file.close()
            with open(shell_path, 'r') as f:
                print(f.read())
            run_proc(f"chmod +x \"{shell_path}\" && bash \"{shell_path}\"")
    sys.exit()



# Returns current formatted time
def format_now():
    return datetime.datetime.now().strftime("%#I:%M:%S %p" if os_name == "windows" else "%-I:%M:%S %p")


# Global banner
global_banner = None

# Replacement for run_proc to prevent CMD flashing
def run_proc(cmd):
    return_code = subprocess.call(cmd, shell=True)
    print(f'{cmd}: returned exit code {return_code}')
    return return_code


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

# Removes invalid characters from a filename
def sanitize_name(value, addon=False):
    value = value.split(":")[0]
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value)
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

                world_version = ([item for item in cache_file.items() if world_data_version == item[1]][0])
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
        os.makedirs(directory)
        if debug:
            print(f'Created "{directory}"')
    else:
        if debug:
            print(f'"{directory}" already exists')


# Open folder in default file browser
def open_folder(directory: str):
    if os_name == 'linux':
        subprocess.Popen(['xdg-open', directory])
    elif os_name == 'windows':
        subprocess.Popen(['explorer', directory])


# Extract archive
def extract_archive(archive_file: str, export_path: str, skip_root=False):
    archive = None
    archive_type = None

    if archive_file.endswith("tar.gz"):
        archive = tarfile.open(archive_file, "r:gz")
        archive_type = "tar"
    elif archive_file.endswith("tar"):
        archive = tarfile.open(archive_file, "r:")
        archive_type = "tar"
    elif archive_file.endswith("zip"):
        archive = zipfile.ZipFile(archive_file, 'r')
        archive_type = "zip"

    if archive and applicationFolder in os.path.split(export_path)[0]:
        folder_check(export_path)

        # Keep integrity of archive
        if not skip_root:
            archive.extractall(export_path)

        # Export from root folder instead
        else:
            if archive_type == "tar":
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

        print(f"Extracted '{archive_file}' to '{export_path}'")
    else:
        print(f"Archive '{archive_file}' was not found")


# Download file from URL to directory
def download_url(url: str, file_name: str, output_path: str, progress_func=None):

    # with DownloadProgressBar(unit='B', unit_scale=True, bar_format='{l_bar}{bar:40}\x1b[97m{r_bar}\x1b[97m{bar:-40b}', colour="GREEN", miniters=1, desc=file_name) as t:
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    urllib.request.install_opener(opener)
    urllib.request.urlretrieve(url, filename=os.path.join(output_path, file_name), reporthook=progress_func)


# Will attempt to delete dir tree without error
def safe_delete(directory: str):
    if not directory:
        return
    try:
        if os.path.exists(directory):
            rmtree(directory)
    except OSError:
        print(f"Could not delete '{directory}'")


# Delete every '_MEIPASS' folder in case of leftover files, and delete '.auto-mcs\Downloads'
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

    # Delete downloads folder
    safe_delete(downDir)
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
                final_item = copytree(src_dir, final_path, dirs_exist_ok=True)

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
    global project_link, app_version, app_latest, app_online, update_urls, update_md5

    # Check if updates are available
    try:
        # Grab release data
        latest_release = f"https://api.github.com/repos{project_link.split('.com')[1]}/releases/latest"
        req = requests.get(latest_release)
        status_code = req.status_code
        release_data = req.json()
        # print(release_data)


        # Get checksum data
        try:
            md5_str = release_data['body'].split("MD5 Checksums")[1]
            checksum = ""
            for line in md5_str.splitlines():
                if line == '`':
                    continue

                if checksum:
                    update_md5[checksum] = line.strip()
                    checksum = ""
                    continue

                if "Windows" in line:
                    checksum = "windows"
                    continue

                if "Linux" in line:
                    checksum = "linux"
                    continue
        except:
            pass


        # Format release data
        version = release_data['name']
        if "-" in version:
            latest_version = version[1:].split("-")[0].strip()
        elif " " in version:
            latest_version = version[1:].split("-")[0].strip()
        else:
            latest_version = app_version

        # Download links
        for file in release_data['assets']:
            if 'linux' in file['name']:
                update_urls['linux'] = file['browser_download_url']
                continue
            if 'windows' in file['name']:
                update_urls['windows'] = file['browser_download_url']
                continue

        # Check if app needs to be updated, and URL was successful
        if float(app_version) < float(latest_version):
            app_latest = False

        app_online = status_code == 200

    except Exception as e:
        if debug:
            print("Something went wrong checking for updates: ", e)


# Get latest game versions
def find_latest_mc():

    def latest_version(name, url):

        if name == "vanilla":
            # Vanilla
            try:
                reqs = requests.get(url)
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
            reqs = requests.get(url)
            soup = BeautifulSoup(reqs.text, 'html.parser')

            for div in soup.find_all('div', "title"):
                if "download latest" in div.text.lower():
                    latestMC["forge"] = div.small.text.split(" -")[0]
                    latestMC["builds"]["forge"] = div.small.text.split(" - ")[1]
                    break


        elif name == "paper":
            # Paper
            reqs = requests.get(url)
            soup = BeautifulSoup(reqs.text, 'html.parser')

            jsonObject = json.loads(reqs.text)
            version = jsonObject['versions'][-1]
            latestMC["paper"] = version

            build_url = f"https://papermc.io/api/v2/projects/paper/versions/{version}"
            reqs = requests.get(build_url)
            jsonObject = json.loads(reqs.text)
            latestMC["builds"]["paper"] = jsonObject['builds'][-1]


        elif name == "spigot":
            # Spigot
            reqs = requests.get(url)
            soup = BeautifulSoup(reqs.text, 'html.parser')

            latestMC["spigot"] = soup.find('div', "row vdivide").h2.text


        elif name == "craftbukkit":
            # Craftbukkit
            reqs = requests.get(url)
            soup = BeautifulSoup(reqs.text, 'html.parser')

            latestMC["craftbukkit"] = soup.find('div', "row vdivide").h2.text

        elif name == "fabric":
            # Fabric
            version = "https://meta.fabricmc.net/v2/versions/game"
            loader = "https://meta.fabricmc.net/v2/versions/loader"
            installer = "https://meta.fabricmc.net/v2/versions/installer"

            # Game version
            reqs = requests.get(version)
            jsonObject = json.loads(reqs.text)

            for item in jsonObject:
                if item['stable']:
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

            latestMC["fabric"] = version
            latestMC["builds"]["fabric"] = f"{loader}/{installer}"
            # URL: https://meta.fabricmc.net/v2/versions/loader/{version}/{build}/server/jar

    version_links = {
        "vanilla": "https://mcversions.net/index.html",
        "forge": "https://files.minecraftforge.net/net/minecraftforge/forge/index.html",
        "paper": "https://papermc.io/api/v2/projects/paper/",
        "spigot": "https://getbukkit.org/download/spigot",
        "craftbukkit": "https://getbukkit.org/download/craftbukkit",
        "fabric": "https://fabricmc.net/use/server/"
    }

    with ThreadPoolExecutor(max_workers=10) as pool:
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
        if "java" in item.a.get("title").lower():

            # Level ID = dict entry
            cols = item.find_all("td")

            try:
                data = cols[2].text
            except IndexError:
                data = None

            final_data[item.find("td").a.get("title").lower().replace("java edition ","")] = data

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
            "Congragulations! It's a pizza!",
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


# Downloads the latest version of Auto-MCS if available
def download_update(progress_func=None):

    def hook(a, b, c):
        if progress_func:
            progress_func(round(100 * a * b / c))

    update_url = update_urls['windows' if os_name == 'windows' else 'linux']
    if not update_url:
        return False

    # Attempt at most 5 times to download server.jar
    fail_count = 0
    while fail_count < 5:

        safe_delete(downDir)
        folder_check(downDir)

        try:

            if progress_func and fail_count > 0:
                progress_func(0)


            # Specify names
            binary_zip = 'auto-mcs.zip'
            binary_name = 'auto-mcs.exe' if os_name == 'windows' else 'auto-mcs'

            # Download binary zip, and extract the binary from the archive
            download_url(update_url, binary_zip, downDir, hook)
            update_path = os.path.join(downDir, binary_zip)
            extract_archive(update_path, downDir)
            binary_file = os.path.join(downDir, binary_name)
            os.remove(update_path)


            # If successful, copy to tmpsvr
            if os.path.isfile(binary_file):

                # If the hash matches, continue
                if get_checksum(binary_file) == update_md5['windows' if os_name == 'windows' else 'linux']:

                    if progress_func:
                        progress_func(100)

                    fail_count = 0
                    break

        except Exception as e:
            print(e)
            fail_count += 1


    return fail_count < 5


# Returns MD5 checksum of file
def get_checksum(file_path):
    return str(hashlib.md5(open(file_path, 'rb').read()).hexdigest())


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

    # Remove below 1.6 versions for Forge
    try:

        while foundServer is False:
            if str.lower(mcType) == "forge":
                versionCheck = float(mcVer.replace("1.", "", 1))
                if versionCheck < 6:
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
                        if div.h2.text == str(mcVer):

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


            elif str.lower(mcType) == "forge":
                forge_url = f"https://files.minecraftforge.net/net/minecraftforge/forge/index_{mcVer}.html"
                reqs = requests.get(forge_url)
                soup = BeautifulSoup(reqs.text, 'html.parser')
                div = soup.find('div', "link link-boosted")

                urls = div.a.get('href').split("&url=")

                for possible_url in urls:
                    if ".jar" in possible_url:
                        url = possible_url
                        break
                else:
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
                req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                urlTest = urllib.request.urlopen(req).getcode()

                if urlTest == 200:
                    urlValid = True

                    serverLink = url

                    # Upon valid URL
                    if mcType.lower() == "vanilla":

                        if version_check(mcVer, '>=', '1.0') and version_check(mcVer, '<', '1.2'):
                            pass

                        elif "b" in mcVer[:1]:
                            serverLink = f"https://archive.org/download/minecraft-beta-server-jars/Minecraft%20Beta%20Server%20Jars.zip/Minecraft%20Beta%20Server%20Jars%2FOffical%20Server%20Jars%2F{mcVer}.jar"

                        else:
                            reqs = requests.get(url)
                            soup = BeautifulSoup(reqs.text, 'html.parser')
                            urls = []

                            for link in soup.find_all('a'):
                                urls.append(link.get('href'))

                            serverLink = urls[3]


                    final_info = [True, {'version': mcVer, 'build': buildNum}, "", serverLink]

                    if modifiedVersion > 0:
                        final_info[2] = f"'{originalRequest}' could not be found, using '{mcVer}' instead"
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
        final_info = [False, {'version': originalRequest, 'build': buildNum}, f"'{originalRequest}' doesn't exist, or can't be retrieved", None]

    version_loading = False
    return final_info
def search_version(server_info: dict):

    if not server_info['version']:
        server_info['version'] = latestMC[server_info['type']]

        # Set build info
        if server_info['type'] in ["forge", "paper"]:
            server_info['build'] = latestMC['builds'][server_info['type']]

    return validate_version(server_info)


# Generate new server configuration
def new_server_init():
    global new_server_info
    new_server_info = {
        "_hash": gen_rstring(8),

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


# Verify portable java is available in '.auto-mcs\Tools', if not install it
modern_pct = 0
legacy_pct = 0
def java_check(progress_func=None):
    global java_executable, modern_pct, legacy_pct
    max_retries = 3
    retries = 0

    java_url = {
        'windows': {
            "modern": "https://download.oracle.com/java/17/latest/jdk-17_windows-x64_bin.zip",
            "legacy": "https://javadl.oracle.com/webapps/download/GetFile/1.8.0_331-b09/165374ff4ea84ef0bbd821706e29b123/windows-i586/jre-8u331-windows-x64.tar.gz"
        },
        'linux': {
            "modern": "https://download.oracle.com/java/17/latest/jdk-17_linux-x64_bin.tar.gz",
            "legacy": "https://javadl.oracle.com/webapps/download/GetFile/1.8.0_331-b09/165374ff4ea84ef0bbd821706e29b123/linux-i586/jre-8u331-linux-x64.tar.gz"
        },
        'macos': {
            "modern": "https://download.oracle.com/java/17/latest/jdk-17_macos-x64_bin.tar.gz",
            "legacy": "https://javadl.oracle.com/webapps/download/GetFile/1.8.0_331-b09/165374ff4ea84ef0bbd821706e29b123/unix-i586/jre-8u331-macosx-x64.tar.gz"
        }
    }

    while not java_executable['modern'] or not java_executable['legacy']:

        # Delete downloads folder
        safe_delete(downDir)

        # If max_retries exceeded, give up
        if retries > max_retries:
            if debug:
                print('\nJava failed to download or install\n')
            return False

        # Check if installations function before doing anything
        if os.path.exists(os.path.abspath(os.path.join(applicationFolder, 'Tools', 'java'))):

            modern_path = os.path.join(applicationFolder, 'Tools', 'java', 'modern', 'bin', 'java.exe' if os_name == "windows" else 'java')
            legacy_path = os.path.join(applicationFolder, 'Tools', 'java', 'legacy', 'bin', 'java.exe' if os_name == "windows" else 'java')
            jar_path = os.path.join(applicationFolder, 'Tools', 'java', 'modern', 'bin', 'jar.exe' if os_name == "windows" else 'jar')

            if (run_proc(f'"{os.path.abspath(modern_path)}" --version') == 0) and (run_proc(f'"{os.path.abspath(legacy_path)}" -version') == 0):

                java_executable = {
                    "modern": str(os.path.abspath(modern_path)),
                    "legacy": str(os.path.abspath(legacy_path)),
                    "jar": str(os.path.abspath(jar_path))
                }

                if debug:
                    print('\nValid Java installations detected\n')

                if progress_func:
                    progress_func(100)

                return True


        # If valid java installs are not detected, install them to '.auto-mcs\Tools'
        if not java_executable['modern'] or not java_executable['legacy']:

            if debug:
                print('\nJava is not detected, installing...\n')

            # Download java versions in threadpool:
            folder_check(downDir)

            modern_filename = f'modern-java.{os.path.basename(java_url[os_name]["modern"]).split(".", 1)[1]}'
            legacy_filename = f'legacy-java.{os.path.basename(java_url[os_name]["legacy"]).split(".", 1)[1]}'

            # Use timer and combined function to get total percentage of both installs
            modern_pct = 0
            legacy_pct = 0

            def avg_total(*args):
                global modern_pct, legacy_pct
                while True:
                    progress_func(round((modern_pct + legacy_pct) / 2))
                    time.sleep(0.2)
                    if (modern_pct >= 100 and legacy_pct >= 100):
                        break

            if progress_func:
                timer = Timer(0, function=avg_total)
                timer.start()  # Checks for potential crash

            with ThreadPoolExecutor(max_workers=2) as pool:

                def hook1(a, b, c):
                    global modern_pct, legacy_pct
                    modern_pct = round(100 * a * b / c)

                def hook2(a, b, c):
                    global modern_pct, legacy_pct
                    legacy_pct = round(100 * a * b / c)

                pool.map(
                    download_url,
                    [java_url[os_name]['modern'], java_url[os_name]['legacy']],
                    [modern_filename, legacy_filename],
                    [downDir, downDir],
                    [hook1 if progress_func else None, hook2 if progress_func else None]
                )

            if progress_func:
                timer.cancel()

            # Install java by extracting the files to their respective folder
            modern_path = os.path.join(applicationFolder, 'Tools', 'java', 'modern')
            legacy_path = os.path.join(applicationFolder, 'Tools', 'java', 'legacy')

            safe_delete(modern_path)
            safe_delete(legacy_path)

            with ThreadPoolExecutor(max_workers=2) as pool:
                pool.map(
                    extract_archive,
                    [os.path.join(downDir, modern_filename), os.path.join(downDir, legacy_filename)],
                    [modern_path, legacy_path],
                    [True, True]
                )

            retries += 1

    else:
        if progress_func:
            progress_func(100)

        return True



# Create New Server stuffies

# Downloads jar file from new_server_info, and generates link if it doesn't exist
def download_jar(progress_func=None):

    def hook(a, b, c):
        if progress_func:
            progress_func(round(100 * a * b / c))

    if not new_server_info['jar_link']:
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
def iter_addons(progress_func=None, update=False):
    global hook_lock

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
        if new_server_info['type'] in ['craftbukkit', 'spigot', 'paper']:
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

    addon_folder = "plugins" if new_server_info['type'] in ['spigot', 'craftbukkit', 'paper'] else 'mods'
    folder_check(os.path.join(tmpsvr, addon_folder))
    folder_check(os.path.join(tmpsvr, "disabled-" + addon_folder))

    def process_addon(addon_object):
        # Add exception handler at some point
        try:
            if addon_object.addon_object_type == "web":
                addons.download_addon(addon_object, new_server_info, tmpsvr=True)
            else:
                if update:
                    addon_web = addons.get_update_url(addon_object, new_server_info['version'], new_server_info['type'])
                    downloaded = addons.download_addon(addon_web, new_server_info, tmpsvr=True)
                    if not downloaded:
                        disabled_folder = "plugins" if server_manager.current_server.type in ['spigot', 'craftbukkit', 'paper'] else 'mods'
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
                timer.start()

    if progress_func:
        progress_func(100)

    return True


# If Fabric or Forge, install server
def install_server(progress_func=None):

    # Change directory to tmpsvr
    cwd = os.path.abspath(os.curdir)
    os.chdir(tmpsvr)


    # Install Forge server
    if new_server_info['type'] == 'forge':

        run_proc(f'"{java_executable["modern"]}" -jar forge.jar -installServer')

        # Modern
        if version_check(new_server_info['version'], ">=", "1.17"):
            for f in glob("run*"):
                os.remove(f)

            for f in glob("user_jvm*"):
                os.remove(f)

            for f in glob("install*.log"):
                os.remove(f)


        # 1.6 to 1.16
        elif version_check(new_server_info['version'], ">=", "1.6") and version_check(new_server_info['version'], "<", "1.17"):
            if os_name == "windows":
                run_proc("move *forge-*.jar server.jar")
            else:
                run_proc("mv *forge-*.jar server.jar")

        for f in glob("forge.jar"):
            os.remove(f)


    # Install Fabric server
    elif new_server_info['type'] == 'fabric':

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

    time_stamp = datetime.date.today().strftime(f"#%a %b %d ") + datetime.datetime.now().strftime("%H:%M:%S ") + "MCS" + datetime.date.today().strftime(f" %Y")
    world_name = 'world'


    # First, generate startup script
    generate_run_script(new_server_info, temp_server=True)


    # If custom world is selected, copy it to tmpsvr
    if new_server_info['server_settings']['world'] != 'world':
        world_name = os.path.basename(new_server_info['server_settings']['world'])
        copytree(new_server_info['server_settings']['world'], os.path.join(tmpsvr, world_name), dirs_exist_ok=True)


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
motd={new_server_info['server_settings']['motd']}
announce-player-achievements=true
force-gamemode=false
hardcore={bool_str(new_server_info['server_settings']['difficulty'] == 'hardcore')}
white-list={bool_str(new_server_info['acl_object'].server['whitelist'])}
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
allow-flight=false
resource-pack-hash=
max-world-size=29999984"""

    if version_check(new_server_info['version'], ">=", '1.13'):
        serverProperties += f"\nenforce_whitelist={bool_str(new_server_info['acl_object'].server['whitelist'])}"

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

        return True


# Configures server via server info in a variety of ways
def update_server_files(progress_func=None):
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


# Create initial backup of new server
# For existing servers, use server_manager.current_server.backup.save_backup()
def create_backup(import_server=False, *args):
    backup.BackupManager(new_server_info['name'] if not import_server else import_data['name']).save_backup()
    return True


# Restore backup and track progress for ServerBackupRestoreProgressScreen
def restore_server(file_path, progress_func=None):

    # Get file count of backup
    total_files = 0
    proc_complete = False
    server_name = server_manager.current_server.name
    file_name = os.path.basename(file_path)

    server_manager.current_server.backup.restore_file = None

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

    threading.Timer(0, thread_checker).start()

    server_manager.current_server.backup.restore_backup(file_name)
    proc_complete = True

    if progress_func:
        progress_func(100)

    return True



# Import Server stuffies

# Figures out type and version of server. Returns information to constants.import_data dict
# There will be issues importing 1.17.0 bukkit derivatives due to Java 16 requirement
def scan_import(bkup_file=False, progress_func=None, *args):
    name = import_data['name']
    path = import_data['path']

    cwd = os.path.abspath(os.curdir)
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

        for file in script_list:

            # Find server jar name
            with open(file, 'r') as f:
                output = f.read()
                f.close()

                if "-jar" in output and ".jar" in output:
                    file_name = output.split("-jar ")[1].split(".jar")[0]

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
                            server = subprocess.Popen(f"\"{java_executable['legacy']}\" -Xmx{ram}G -Xms{ram}G -jar server.jar nogui", stdout=subprocess.DEVNULL, shell=True)

                        # Run latest version of java
                        else:
                            # If paper, copy pre-downloaded vanilla .jar files if they exist
                            if import_data['type'] == "paper":
                                copy_to(os.path.join(str(path), 'cache'), test_server, 'cache', True)

                            server = subprocess.Popen(f"\"{java_executable['modern']}\" -Xmx{ram}G -Xms{ram}G -jar server.jar nogui", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)

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


            # Import files and such
            if import_data['type'] and import_data['version']:

                if progress_func:
                    progress_func(80)

                safe_delete(tmpsvr)
                try:
                    os.rmdir(tmpsvr)
                except FileNotFoundError:
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

    if import_data['name']:

        # Copy folder to server path and delete tmpsvr
        new_path = os.path.join(serverDir, import_data['name'])
        copytree(tmpsvr, new_path, dirs_exist_ok=True)
        safe_delete(tempDir)
        safe_delete(downDir)

        if progress_func:
            progress_func(33)


        # Add global rules to ACL
        from acl import AclObject
        AclObject(import_data['name']).write_rules()

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
                with open(os.path.join(server_path(import_data['name']), 'server.properties'), 'w+') as f:
                    content = f.readlines()
                    content[1] = f"#{time_stamp}"
                    f.writelines(content)


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


# Generates new information for a server update
def init_update():
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


# ------------------------------------------------ Server Functions ----------------------------------------------------

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

        if write_object.get('general', 'serverType').lower() not in ['forge', 'paper']:
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
def create_server_config(properties: dict, temp_server=False):

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


# server.properties function
# write_object is the dict object returned from this function
def server_properties(server_name: str, write_object=None):
    properties_file = server_path(server_name, 'server.properties')
    force_strings = ['level-seed', 'level-name', 'motd', 'resource-pack', 'resource-pack-prompt', 'resource-pack-sha1']

    # If write_object, write it to file path
    if write_object:

        with open(properties_file, 'w') as f:
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
            with open(properties_file, 'r') as f:
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
        ram = config_spec


    return ram


# Generates server batch/shell script
def generate_run_script(properties, temp_server=False):

    # Change directory to server path
    cwd = os.path.abspath(os.curdir)
    if temp_server:
        folder_check(tmpsvr)
        os.chdir(tmpsvr)
    else:
        folder_check(server_path(properties['name']))
        os.chdir(server_path(properties['name']))


    script = ""
    ram = calculate_ram(properties)
    start_flags = '-XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200 -XX:+UnlockExperimentalVMOptions -XX:+DisableExplicitGC -XX:+AlwaysPreTouch -XX:G1HeapWastePercent=5 -XX:G1MixedGCCountTarget=4 -XX:G1MixedGCLiveThresholdPercent=90 -XX:G1RSetUpdatingPauseTimePercent=5 -XX:SurvivorRatio=32 -XX:+PerfDisableSharedMem -XX:MaxTenuringThreshold=1 -XX:G1NewSizePercent=30 -XX:G1MaxNewSizePercent=40 -XX:G1HeapRegionSize=8M -XX:G1ReservePercent=20 -XX:InitiatingHeapOccupancyPercent=15 -Dusing.aikars.flags=https://mcflags.emc.gs -Daikars.new.flags=true -Dlog4j2.formatMsgNoLookups=true'


    # For every version except Forge
    if properties['type'] != 'forge':

        # Make sure this works non-spigot versions
        java = java_executable["legacy"] if version_check(properties['version'], '<','1.17') else java_executable['modern']

        # On bukkit derivatives, install geysermc, floodgate, and viaversion if version >= 1.13.2 (add -DPaper.ignoreJavaVersion=true if paper < 1.16.5)
        script = f'"{java}" -Xmx{ram}G -Xms{ram}G {start_flags} -Dlog4j2.formatMsgNoLookups=true'

        if version_check(properties['version'], "<", "1.16.5") and properties['type'] == 'paper':
            script += ' -DPaper.ignoreJavaVersion=true'

        script += ' -jar server.jar nogui'


    # Do some schennanies for Forge
    else:

        # Modern
        if version_check(properties['version'], ">=", "1.17"):
            version_list = [os.path.basename(file) for file in glob(os.path.join("libraries", "net", "minecraftforge", "forge", f"1.{math.floor(float(properties['version'].replace('1.', '', 1)))}*"))]
            arg_file = f"libraries/net/minecraftforge/forge/{version_list[-1]}/{'win_args.txt' if os_name == 'windows' else 'unix_args.txt'}"
            script = f'"{java_executable["modern"]}" -Xmx{ram}G -Xms{ram}G {start_flags} -Dlog4j2.formatMsgNoLookups=true @{arg_file} nogui'

        # 1.6 to 1.16
        elif version_check(properties['version'], ">=", "1.6") and version_check(properties['version'], "<", "1.17"):
            script = f'"{java_executable["legacy"]}" -Xmx{ram}G -Xms{ram}G {start_flags} -Dlog4j2.formatMsgNoLookups=true -jar server.jar nogui'


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


# Return list of every valid server update property in 'applicationFolder'
def make_update_list():
    global update_list

    update_list = {}

    for name in glob(os.path.join(applicationFolder, "Servers", "*")):

        name = os.path.basename(name)

        serverObject = {
                            name: {
                                    "updateAuto": "false",
                                    "needsUpdate": "false"
                                  }
                       }

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

            new_version = latestMC[jarType.lower()]
            current_version = jarVer

            if ((jarType.lower() in ["forge", "paper"]) and (jarBuild != "")) and (new_version == current_version):
                new_version += " ᴮ" + str(latestMC["builds"][jarType.lower()])
                current_version += " ᴮ" + str(jarBuild)

            if (new_version != current_version):
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

            if os_name == "linux" and "stable-linux-amd64" in dl_url:
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
        cwd = os.path.abspath(os.curdir)
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


# Returns active IP address of 'name'
def get_current_ip(name: str, get_ngrok=False):
    global public_ip

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
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0)
            try:
                # doesn't even have to be reachable
                s.connect(('10.254.254.254', 1))
                private_ip = s.getsockname()[0]
            finally:
                s.close()


        if not get_ngrok:
            if app_online and not public_ip:
                def get_public_ip(server_name, *args):
                    global public_ip
                    try:
                        new_ip = requests.get('http://api.ipify.org', timeout=5).content.decode('utf-8')
                    except:
                        new_ip = ""

                    if new_ip and 'bad' not in new_ip.lower():
                        public_ip = new_ip
                        # Assign public IP to current running server
                        if server_manager.running_servers:
                            try:
                                server_manager.running_servers[server_name].run_data['network']['address']['ip'] = public_ip
                                server_manager.running_servers[server_name].run_data['network']['public_ip'] = public_ip
                            except KeyError:
                                pass

                ip_timer = Timer(0, functools.partial(get_public_ip, name))
                ip_timer.start()


    # Format network info
    if get_ngrok:
        def get_ngk_ip(server_name, *args):
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
        ip_timer.start()

    if public_ip:
        final_addr['ip'] = public_ip
    elif private_ip:
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
allow-flight=false
resource-pack-hash=
max-world-size=29999984"""

    with open(os.path.join(path, 'server.properties'), "w+") as f:
        f.write(serverProperties)
