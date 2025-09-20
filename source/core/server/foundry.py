from shutil import copytree, copy, ignore_patterns, move, disk_usage
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime as dt, date
from configparser import NoOptionError
from urllib.parse import quote
from bs4 import BeautifulSoup
from copy import deepcopy
from glob import glob
from PIL import Image
import subprocess
import threading
import requests
import tarfile
import time
import json
import yaml
import os
import re

from source.core.server import addons, backup
from source.core import constants
from source.core.constants import (

    # Directories
    serverDir, tempDir, cacheDir, downDir, applicationFolder, templateDir, backupFolder, tmpsvr,

    # General methods
    translate, folder_check, safe_delete, copy_to, run_proc, get_url, download_url, cs_download_url,
    format_traceback, get_cwd, version_check, gen_rstring, sanitize_name, extract_archive, move_files_root,
    telepath_upload, get_remote_var, clear_uploads,

    # Constants
    os_name, java_executable, server_ini, command_tmp,

    # Global manger objects
    server_manager, api_manager, playit
)

from source.core.server.manager import (
    server_type, server_path, create_server_config, server_config,
    calculate_ram, generate_run_script, fix_empty_properties
)


# ---------------------------------------------- Global Functions ------------------------------------------------------

new_server_info = {}
import_data     = {'name': None, 'path': None}

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

# Log wrapper
def send_log(object_data, message, level=None):
    return constants.send_log(f'{__name__}.{object_data}', message, level, 'core')



# --------------------------------------- Server Template Functions (.ist) ---------------------------------------------

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
    name_list = server_manager.server_list_lower
    if new_server_info:
        telepath_data = new_server_info['_telepath_data']

    new_server_init()

    if telepath_data:
        new_server_info['_telepath_data'] = telepath_data
        name_list = get_remote_var('server_manager.server_list_lower', telepath_data)

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
    from source.core.server.acl import AclManager
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



# ----------------------------------------------- Utility Functions ----------------------------------------------------

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



# ------------------------------------ Server Creation/Import/Update Functions -----------------------------------------

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
    global new_server_info, import_data
    new_server_init()
    if import_info:
        import_data = import_info

    if server_info:
        server_info['_telepath_data'] = None
        new_server_info = server_info

        # Reconstruct ACL manager
        if 'acl_object' in server_info and server_info['acl_object']:
            from source.core.server.acl import AclManager
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
        server_manager.create_server_list()
        s_list = server_manager.server_list_lower
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

    # If Telepath, update addons remotely
    # 'telepath_data' is filled only when this is a client that is connected to a remote server
    # 'telepath' is only True when this is the server, and a client requested this method via the API
    if not telepath:
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
        if addon.hash in addons.addon_cache:
            del addons.addon_cache[addon.hash]
    addons.load_addon_cache(True)

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
        playit.install_agent()


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

        server_manager.check_for_updates()
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
        if import_data['name'].lower() in server_manager.server_list_lower:
            import_data['name'] = new_server_name(import_data['name'])
    elif new_server_info['name']:
        if new_server_info['name'].lower() in server_manager.server_list_lower:
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
    server_manager.check_for_updates()
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
            except NoOptionError: pass

            try: config_file.set('general', 'updateAuto', str(import_data['config_file'].get('general', 'updateAuto')).lower())
            except NoOptionError: pass

            try: config_file.set('general', 'allocatedMemory', str(import_data['config_file'].get('general', 'allocatedMemory')).lower())
            except NoOptionError: pass

            try: config_file.set('general', 'customFlags', str(import_data['config_file'].get('general', 'customFlags')).lower())
            except NoOptionError: pass

            try: config_file.set('general', 'enableGeyser', str(import_data['config_file'].get('general', 'enableGeyser')).lower())
            except NoOptionError: pass

            try: config_file.set('general', 'enableProxy', str(import_data['config_file'].get('general', 'enableProxy')).lower())
            except NoOptionError: pass

            try: config_file.set('general', 'isModpack', str(import_data['config_file'].get('general', 'isModpack')).lower())
            except NoOptionError: pass

            try: config_file.set('general', 'consoleFilter', str(import_data['config_file'].get('general', 'consoleFilter')).lower())
            except NoOptionError: pass

            try: config_file.set('bkup', 'bkupAuto', str(import_data['config_file'].get('bkup', 'bkupAuto')).lower())
            except NoOptionError: pass

            try: config_file.set('bkup', 'bkupMax', str(import_data['config_file'].get('bkup', 'bkupMax')).lower())
            except NoOptionError: pass

            backup_dir = backupFolder
            try:
                if os.path.isdir(str(import_data['config_file'].get('bkup', 'bkupMax'))):
                    backup_dir = str(import_data['config_file'].get('bkup', 'bkupMax'))
            except NoOptionError:
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
        from source.core.server.acl import AclManager
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
            server_manager.check_for_updates()
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

        # If the server isn't being updated, make sure it creates a new server
        if data['name'] and not update:
            data['name'] = new_server_name(process_name(data['name']))

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
            from source.core.server.acl import AclManager
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
            server_manager.check_for_updates()

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
