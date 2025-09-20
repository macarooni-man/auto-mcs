from concurrent.futures import ThreadPoolExecutor, as_completed
from configparser import ConfigParser, NoOptionError
from typing import Union, Optional, Any
from subprocess import Popen, PIPE, run
from shutil import copytree, copy, move
from datetime import datetime as dt
from threading import Timer
from copy import deepcopy
from glob import glob
from PIL import Image
import functools
import threading
import requests
import psutil
import ctypes
import time
import json
import math
import os
import re

from source.core.server.acl import AclManager, get_uuid, check_online
from source.core.server.backup import BackupManager
from source.core import constants, telepath
from source.core.server import backup
from source.core.constants import (

    # Directories
    serverDir, tempDir, cacheDir, downDir, applicationFolder, backupFolder, tmpsvr, gui_assets,
    uploadDir, telepathFile, telepathDir,

    # General methods
    folder_check, safe_delete, run_proc, download_url, fmt_date, check_free_space, java_check,
    format_traceback, get_cwd, version_check, gen_rstring, backup_lock, get_private_ip, check_port,
    telepath_download, telepath_upload, get_remote_var, clear_uploads, format_nickname, sync_attr,

    # Constants
    app_online, ams_version, os_name, server_ini, command_tmp, color_table,
    valid_config_formats, valid_image_formats, start_script_name,

    # Global manger objects
    api_manager, playit
)


# Auto-MCS Server Manager API
# ----------------------------------------------- Server Objects -------------------------------------------------------

# Log wrapper
def send_log(object_data, message, level=None):
    return constants.send_log(f'{__name__}.{object_data}', message, level, 'core')


# Instantiate class with "server_name" (case-sensitive)
# Big boy mega server object
class ServerObject():

    # Internal log wrapper
    def _send_log(self, message: str, level: str = None):
        return send_log(self.__class__.__name__, f"'{self.name}': {message}", level)

    def __init__(self, _manager: 'ServerManager', server_name: str):
        from source.core.server.amscript import ScriptManager, ServerScriptObject
        from source.core.server.addons import AddonManager

        # Manager / identity
        self._manager:           ServerManager  = _manager
        self._telepath_data:     Optional[dict] = None
        self._view_name:         str            = server_name
        self._hash:              str            = gen_rstring(8)

        # Status tracking
        self._loop_clock:        int            = 0
        self._last_telepath_log: dict           = {}
        self._disconnected:      bool           = False
        self.running:            bool           = False
        self.restart_flag:       bool           = False
        self.crash_log:          Optional[str]  = None

        # Dictionaries for config parsing
        self.gamemode_dict:      list[str]      = ['survival', 'creative', 'adventure', 'spectator']
        self.difficulty_dict:    list[str]      = ['peaceful', 'easy', 'normal', 'hard', 'hardcore']

        # Core server identity
        self.name:               str            = server_name
        self.server_path:        str            = server_path(server_name)
        self.server_icon:        str            = server_path(server_name, 'server-icon.png')
        self.server_properties:  dict[str, Any] = {}
        self.config_file:        ConfigParser   = None
        self.config_paths:       dict           = None

        # Properties loaded from config
        self.properties_hash:    str            = ""
        self.favorite:           bool           = False
        self.dedicated_ram:      str            = "auto"
        self.type:               str            = ""
        self.version:            str            = ""
        self.build:              str            = None
        self.custom_flags:       str            = ""
        self.is_modpack:         str            = ""
        self.proxy_enabled:      bool           = False
        self.geyser_enabled:     bool           = False
        self.auto_update:        str            = "false"
        self.update_string:      str            = ""
        self.world:              str            = None
        self.ip:                 str            = None
        self.port:               int            = None
        self.motd:               str            = None
        self.gamemode:           str            = None
        self.difficulty:         str            = None

        # Runtime state
        self.last_modified:      float          = None
        self.max_log_size:       int            = 2000
        self.run_data:           dict           = {}
        self.console_filter:     str            = "everything"
        self.viewed_notifs:      dict[str, str] = {}
        self.taskbar: 'ui.desktop.MenuTaskbar'  = None

        # Special sub-objects (loaded later)
        self.backup:         BackupManager      = None
        self.addon:          AddonManager       = None
        self.acl:            AclManager         = None
        self.script_manager: ScriptManager      = None
        self.script_object:  ServerScriptObject = None

        # Load configuration immediately
        self.reload_config(_from_init = True)
        self._manager._send_log(f"Server Manager: Loaded '{server_name}'", 'info')

    def __repr__(self):
        return f"<{__name__}.{self.__class__.__name__} '{self.name}' at '{self.server_path}'>"

    # Returns the value of the requested attribute (for remote)
    def _sync_attr(self, name):
        if name == 'run_data':
            return self._telepath_run_data()

        data = sync_attr(self, name)

        if name == '__all__':
            data['run_data'] = self._telepath_run_data()

        return data

    # Returns serialized version of self.run_data for telepath sessions
    def _telepath_run_data(self):
        blacklist = [
            'console-panel',
            'performance-panel',
            'close-hooks',
            'process-hooks',
            'thread',
            'process',
            'send-command',
            'playit-tunnel'
        ]
        new_data = {}
        for k, v in self.run_data.items():
            if k not in blacklist:
                new_data[k] = deepcopy(v)
        return new_data

    # Checks if server was initialized remotely
    def _is_telepath_session(self):
        try: return self in self._manager.remote_servers.values()
        except AttributeError: pass
        except RecursionError: pass
        return False

    # Returns last log and crash info
    def _sync_telepath_stop(self):
        if not self.running:
            crash_log = ''
            if self.crash_log:
                with open(self.crash_log, 'r') as f:
                    crash_log = f.read()

            return {'log': self._last_telepath_log, 'crash': crash_log}
        return {'log': None, 'crash': None}

    # Updates performance data on a clock until server stops
    def _start_performance_clock(self):
        self._loop_clock = 0
        def loop(*a):
            while self.running:
                if self._is_telepath_session():
                    self.performance_stats(1, (self._loop_clock == 3))
                    self._loop_clock += 1
                    if self._loop_clock > 6:
                        self._loop_clock = 1
                else:
                    time.sleep(0.5)

            # Reset on close
            self._loop_clock = 0

        # Don't run on telepath
        if not self._telepath_data:
            threading.Timer(0, loop).start()

    # Check status of loaded objects
    def _check_object_init(self):
        return {'addon': bool(self.addon), 'backup': bool(self.backup), 'acl': bool(self.acl), 'script_manager': bool(self.script_manager)}

    # Reloads server information from static files
    def reload_config(self, reload_objects=False, _logging=True, _from_init=False):
        from source.core.server.amscript import ScriptManager
        from source.core.server.addons import AddonManager
        from source.core.server.foundry import latestMC

        if _from_init: reload_objects = True; _logging = False
        if _logging: self._send_log(f"reloading configuration from disk...", 'info')

        # Server files
        self.server_icon       = server_path(self.name, 'server-icon.png')
        self.config_file       = server_config(self.name)
        self.server_properties = server_properties(self.name)

        # Repair 'server.properties' if empty or broken
        if len(self.server_properties) < 10:
            fix_empty_properties(self.name)
            self.server_properties = server_properties(self.name)

        self.properties_hash = self._get_properties_hash()


        # Server properties
        self.favorite = self.config_file.get("general", "isFavorite").lower() == 'true'
        self.dedicated_ram = str(self.config_file.get("general", "allocatedMemory").lower())
        self.type = self.config_file.get("general", "serverType").lower()
        self.version = self.config_file.get("general", "serverVersion").lower()
        self.build = None

        try: self.console_filter = self.config_file.get("general", "consoleFilter")
        except: pass

        try: self.viewed_notifs = json.loads(self.config_file.get("general", "viewedNotifs"))
        except: pass

        try:
            if self.config_file.get("general", "serverBuild"):
                self.build = self.config_file.get("general", "serverBuild").lower()
        except: pass

        try:
            if self.config_file.get("general", "customFlags"):
                self.custom_flags = self.config_file.get("general", "customFlags").strip()
        except:
            self.custom_flags = ''

        try:
            if self.config_file.get("general", "isModpack"):
                modpack = self.config_file.get("general", "isModpack").lower()
                if modpack: self.is_modpack = 'zip' if modpack != 'mrpack' else 'mrpack'
        except: self.is_modpack = ''

        try:
            if self.config_file.get("general", "enableProxy"):
                self.proxy_enabled = self.config_file.get("general", "enableProxy").lower() == 'true'
        except: self.proxy_enabled = False

        try:
            if self.config_file.get("general", "enableGeyser"):
                self.geyser_enabled = self.config_file.get("general", "enableGeyser").lower() == 'true'
        except: self.geyser_enabled = False


        # Check update properties for UI stuff
        self.update_string = ''
        if self.is_modpack:
            if self.update_list[self.name]['updateString'] and self.is_modpack == 'mrpack':
                self.update_string = self.update_list[self.name]['updateString']
        else:
            self.update_string = str(latestMC[self.type]) if version_check(latestMC[self.type], '>', self.version) else ''
            if not self.update_string and self.build:
                self.update_string = ('b-' + str(latestMC['builds'][self.type])) if (tuple(map(int, (str(latestMC['builds'][self.type]).split(".")))) > tuple(map(int, (str(self.build).split("."))))) else ""


        # Ensure automatic updates are disabled for non-mrpack modpacks
        if self.is_modpack and self.is_modpack != 'mrpack': self.auto_update = 'false'
        else: self.auto_update = str(self.config_file.get("general", "updateAuto").lower())


        if self.update_string: self._view_notif('settings', viewed='')
        else:                  self._view_notif('settings', False)

        try: self.world = self.server_properties['level-name']
        except KeyError: self.world = None

        try: self.ip = self.server_properties['server-ip']
        except KeyError: self.ip = None

        try: self.port = self.server_properties['server-port']
        except KeyError: self.port = None

        try: self.motd = self.server_properties['motd']
        except KeyError: self.motd = None


        try:
            self.gamemode = self.gamemode_dict[int(float(self.server_properties['gamemode']))] if not self.server_properties['hardcore'] else 'hardcore'
            self.difficulty = self.difficulty_dict[int(float(self.server_properties['difficulty']))]
        except ValueError:
            self.gamemode = self.server_properties['gamemode'] if not self.server_properties['hardcore'] else 'hardcore'
            self.difficulty = self.server_properties['difficulty']
        except KeyError:
            self.gamemode = None
            self.difficulty = None

        self.server_path = server_path(self.name)
        self.last_modified = os.path.getmtime(self.server_path)


        # Special sub-objects, and defer loading in the background
        # Make sure that menus wait until objects are fully loaded before opening
        if reload_objects:
            self.backup = None
            self.addon = None
            self.acl = None
            self.script_manager = None
            self.script_object = None

            def load_backup(*args):
                self.backup = BackupManager(self.name)
            Timer(0, load_backup).start()
            def load_addon(*args):
                self.addon = AddonManager(self.name)
                if 'add-ons' in self.viewed_notifs:
                    if self.viewed_notifs['add-ons'] == 'update' or not self.viewed_notifs['add-ons']:
                        self.addon.update_required = True
                self.addon.check_for_updates()
                if self.addon.update_required and len(self.addon.return_single_list()):
                    self._view_notif('add-ons', viewed='')
            Timer(0, load_addon).start()
            def load_acl(*args):
                self.acl = AclManager(self.name)
            Timer(0, load_acl).start()
            def load_scriptmgr(*args):
                self.script_manager = ScriptManager(self.name)
            Timer(0, load_scriptmgr).start()
            def load_config_paths(*args):
                self.reload_config_paths()
            Timer(0, load_config_paths).start()

        if _logging: self._send_log(f"successfully reloaded configuration from disk (internal objects may not be ready yet)", 'info')

    # Retrieve a data structure of all config files in the server
    def reload_config_paths(self):
        self.config_paths = gather_config_files(self.name)
        return self.config_paths

    # Returns a dict formatted like 'new_server_info'
    def properties_dict(self):
        properties = {
            "_hash": gen_rstring(8),

            "name": self.name,
            "type": self.type,
            "version": self.version,
            "build": self.build,
            "ip": self.ip,
            "port": self.port,
            "server_settings": {
                "world": self.world,
                "motd": self.motd,

                # If hardcore, set difficulty=hard, hardcore=true
                "difficulty": self.difficulty,
                "gamemode": self.gamemode,

                # Checks if geyser and floodgate are installed
                "geyser_support": self.geyser_enabled,
                "disable_chat_reporting": False

            },

            # # Dynamic content
            "addon_objects": [],
            # "backup_object": self.backup,
            # "acl_object": self.acl
        }

        # load addons into dict if they exist
        if self.addon:
            properties["addon_objects"] = self.addon.return_single_list()

        return properties


    # Checks if a user is online
    def user_online(self, user: str):
        return check_online(user)


    # Telepath-compatible methods for interacting with the proxy
    def proxy_installed(self):
        return playit._check_agent()
    def install_proxy(self):
        return playit.install_agent()
    def enable_proxy(self, enabled: bool):
        self.config_file.set("general", "enableProxy", str(enabled).lower())
        self.write_config()
        self.proxy_enabled = enabled
        action = 'enabled' if enabled else 'disabled'
        self._send_log(f"the playit proxy is now {action} enabled for this server", 'info')

    # Telepath-compatible method to retrieve the login URL for the playit web UI
    def get_playit_url(self):
        if not playit.initialized: playit.initialize()
        return playit.agent_web_url

    # Writes changes to 'server.properties' and 'auto-mcs.ini'
    def write_config(self, remote_data={}):
        if remote_data:
            self.config_file = reconstruct_config(remote_data['config_file'])
            self.server_properties = remote_data['server_properties']

        server_config(self.name, self.config_file)
        server_properties(self.name, self.server_properties)
        self._send_log(f"updated 'server.properties' and '{server_ini}'", 'info')

    # Converts stdout of self.run_data['process'] to fancy stuff
    def update_log(self, text: bytes, *args):

        text = text.replace(b'\xa7', b'\xc2\xa7').decode('utf-8', errors='ignore')

        # Ignore terminal warning
        if "Advanced terminal features are not available in this environment" in text:
            return

        # (date, type, log, color)
        def format_log(line, *args):

            def format_time(string):
                try:
                    date = dt.strptime(string, "%H:%M:%S").strftime(fmt_date("%#I:%M:%S %p")).rjust(11)
                except ValueError:
                    date = ''
                return date

            def format_color(code, *args):
                if 'r' not in code:
                    formatted_code = f'[color={color_table[code]}]'
                else:
                    formatted_code = '[/color]'
                return formatted_code

            date_label = ''
            type_label = ''
            main_label = ''
            type_color = ''
            event = None

            if line:

                message_date_obj = dt.now()

                # New log formatting (latest.log)
                if text.startswith('['):
                    message = line.split("]: ", 1)[-1].strip()
                    try:
                        date_str = line.split("]", 1)[0].strip().replace("[", "")
                        date_label = format_time(date_str)
                    except IndexError:
                        date_label = message_date_obj.strftime(fmt_date("%#I:%M:%S %p")).rjust(11)

                # Old log formatting (server.log)
                else:
                    message = line.split("] ", 1)[-1].strip()
                    try:
                        date_str = line.split(" ", 1)[1].split("[", 1)[0].strip()
                        date_label = format_time(date_str)
                    except IndexError:
                        date_label = message_date_obj.strftime(fmt_date("%#I:%M:%S %p")).rjust(11)

                # If date_label is missing, it may be formatted differently
                if not date_label:
                    date_label = message_date_obj.strftime(fmt_date("%#I:%M:%S %p")).rjust(11)

                # Format string as needed
                if message.endswith("[m"):
                    message = message.replace("[m", "").strip()

                # Format special color codes
                if '§' in message:
                    original_message = message

                    try:
                        message = escape_markup(message)
                        code_list = [message[x:x + 2] for x, y in enumerate(message, 0) if y == '§']

                        for code in code_list:
                            message = message.replace(code, '' if constants.headless else format_color(code))

                        if (len(code_list) % 2 == 1) and not constants.headless:
                            message = message + '[/color]'

                    except KeyError:
                        message = original_message


                # Remove escape codes
                try:
                    if message.strip().endswith('[0m'):
                        message = re.sub(r'(\[\S*\d+m)', '', message)
                except:
                    pass

                # Shorten coordinates, but don't pass this to amscript
                original_message = message.strip().replace('[Not Secure]', '').strip()
                addrs = re.findall(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', message)
                for float_str in re.findall(r"(?<=[ |\]|\(]|,)[-+]?(?:\d+\.\d+)", message):
                    if len(float_str) > 5 and "." in float_str:
                        for addr in addrs:
                            if float_str in addr:
                                break
                        else:
                            message = message.replace(float_str, str(round(float(float_str), 2)))


                main_label = message.strip()
                message = message.replace('[Not Secure]', '').strip()


                # Calculate color based on log type

                # Player auto-mcs command issued
                list_of_commands = []
                amscript_cmd = False
                if self.script_object:
                    if self.script_object.enabled:
                        if (message.startswith("<") and ">" in message) or "[Async Chat Thread" in line:
                            list_of_commands = list(self.script_object.aliases.keys())
                            possible_command = message.split('>', 1)[1].strip().split(" ")[0].strip()
                            amscript_cmd = possible_command in list_of_commands

                if amscript_cmd:
                    type_label = "EXEC"
                    type_color = (1, 0.298, 0.6, 1)
                    user = message.split('>', 1)[0].replace('<', '', 1).strip()
                    user = re.sub(r'\[(\/color|color=#?\w*).+?\]?', '', user)
                    content = original_message.split('>', 1)[1].strip()
                    main_label = f"{user} issued server command: {content}"
                    event = functools.partial(self.script_object.message_event, {'user': user, 'content': content})


                # Player message log
                elif (message.startswith("<") and ">" in message) or "[Async Chat Thread" in line:
                    type_label = "CHAT"
                    type_color = (0.439, 0.839, 1, 1)

                    if self.script_object.enabled:
                        user = message.split('>', 1)[0].replace('<', '', 1).strip()
                        user = re.sub(r'\[(\/color|color=#?\w*).+?\]?', '', user)
                        content = original_message.split('>', 1)[1].strip()
                        event = functools.partial(self.script_object.message_event, {'user': user, 'content': content})

                # Server message log
                elif message.strip().startswith("[Server]"):
                    type_label = "CHAT"
                    type_color = (0.439, 0.839, 1, 1)


                # Player command issued
                elif "issued server command: " in message:
                    type_label = "EXEC"
                    type_color = (1, 0.298, 0.6, 1)

                    user = message.split('issued server command: ')[0].strip()
                    user = re.sub(r'\[(\/color|color=#?\w*).+?\]?', '', user)
                    content = message.split('issued server command: ')[1].strip()

                    # If commands change ACL status, reload lists
                    if content.startswith('op ') or content.startswith('deop '):
                        self.acl.reload_list('ops')
                    if content.startswith('ban ') or content.startswith('pardon '):
                        self.acl.reload_list('bans')
                    if content.startswith('whitelist add ') or content.startswith('whitelist remove '):
                        self.acl.reload_list('wl')

                    # Process amscript event
                    if self.script_object.enabled:
                        event = functools.partial(self.script_object.message_event, {'user': user, 'content': content})



                # Server start log
                elif "Done" in line and "For help," in line:
                    type_label = "START"
                    type_color = (0.3, 1, 0.6, 1)
                    main_label += '. Type "!help" for auto-mcs commands'


                # Server stop log
                elif "Stopping server" in line:
                    type_label = "STOP"
                    type_color = (0.3, 1, 0.6, 1)
                    self.check_for_deadlock()


                # Server fail to start log
                elif "Failed to start the minecraft server" in line:
                    type_label = "FATAL"
                    type_color = (1, 0.5, 0.65, 1)
                    self.check_for_deadlock()


                # Player join log
                elif "logged in with entity id" in message:
                    uuid = None
                    user = message.split("[/", 1)[0].strip()
                    ip = message.split("[/", 1)[1].split("]")[0].strip()
                    main_label = f'{user} logged in from {ip} ' + message.split("]", 1)[1].replace('logged in', '').strip()
                    try:
                        for log_item in reversed(self.run_data['log'][-10:]):
                            if user in log_item['text'][2] and "UUID" in log_item['text'][2]:
                                uuid = log_item['text'][2].split(f"UUID of player {user} is ")[1]
                                break
                    except:
                        pass

                    if not uuid:
                        uuid = get_uuid(user)['uuid']


                    def add_to_list(username, user_uuid, ip_addr, msg_date_obj):
                        self.run_data['player-list'][username] = {
                            'user': username,
                            'uuid': user_uuid,
                            'ip': ip_addr,
                            'date': msg_date_obj,
                            'logged-in': True
                        }
                        self.acl._process_log(self.run_data['player-list'][username])

                        if self.script_object.enabled:
                            return functools.partial(self.script_object.join_event, self.run_data['player-list'][username])

                    try:
                        if self.run_data['player-list'][user]['date'] < message_date_obj:
                            event = add_to_list(user, uuid, ip, message_date_obj)
                    except KeyError:
                        try:
                            event = add_to_list(user, uuid, ip, message_date_obj)
                        except KeyError:
                            pass

                    # In case login isn't accurately reflected
                    try:
                        if not self.run_data['player-list'][user]['logged-in']:
                            self.run_data['player-list'][user]['logged-in'] = True
                    except KeyError:
                        pass

                    type_label = "PLAYER"
                    type_color = (0.953, 0.929, 0.38, 1)


                # Player leave log
                elif "lost connection: " in message:
                    user = message.split("lost connection: ", 1)[0].strip()

                    def add_to_list():
                        original_date = deepcopy(self.run_data['player-list'][user]['date'])
                        self.run_data['player-list'][user]['date'] = message_date_obj
                        self.run_data['player-list'][user]['logged-in'] = False
                        self.acl._process_log(self.run_data['player-list'][user])

                        if self.script_object.enabled:
                            data = deepcopy(self.run_data['player-list'][user])
                            data['playtime'] = message_date_obj - original_date
                            return functools.partial(self.script_object.leave_event, data)

                    try:
                        if self.run_data['player-list'][user]['date'] < message_date_obj:
                            event = add_to_list()
                    except KeyError:
                        try:
                            event = add_to_list()
                        except KeyError:
                            pass

                    # In case logout isn't accurately reflected
                    try:
                        if self.run_data['player-list'][user]['logged-in']:
                            self.run_data['player-list'][user]['logged-in'] = False
                    except KeyError:
                        pass

                    type_label = "PLAYER"
                    type_color = (0.953, 0.929, 0.38, 1)


                # Player achievement/advancement log
                elif " has made the advancement " in message or " has completed the challenge " in message or " has reached the goal " in message:
                    #  2:50:17 PM   [INFO] >   KChicken has made the advancement [Hot Stuff]
                    type_label = "CHAT"
                    type_color = (0.439, 0.839, 1, 1)
                    user = message.split(' ', 1)[0].strip()
                    advancement = message.split(' [')[1].strip(' ]')
                    event = functools.partial(self.script_object.achieve_event, {'user': user, 'advancement': advancement})


                # Other message events
                elif "WARN" in line:
                    type_label = "WARN"
                    type_color = (1, 0.804, 0.42, 1)
                elif "ERROR" in line:
                    type_label = "ERROR"
                    type_color = (1, 0.5, 0.65, 1)
                elif "CRITICAL" in line:
                    type_label = "CRIT"
                    type_color = (1, 0.5, 0.65, 1)
                elif "SEVERE" in line:
                    type_label = "SEVERE"
                    type_color = (1, 0.5, 0.65, 1)
                elif "FATAL" in line:
                    type_label = "FATAL"
                    type_color = (1, 0.5, 0.65, 1)
                elif (main_label.endswith(' left the game') or main_label.endswith(' joined the game')):
                    type_label = "CHAT"
                    type_color = (0.439, 0.839, 1, 1)
                else:
                    # Ignore NBT data updates
                    if " has the following entity data: {" in main_label or ((not line.startswith('[')) and (main_label.endswith('}'))) or main_label in ['Saved the world', 'Saving...']:
                        return None, None

                    type_label = "INFO"
                    type_color = (0.6, 0.6, 1, 1)

                    # Check for death events
                    exclude_list = ['joined', 'left', 'Killed', 'logged', 'disconnected', 'Made', 'UUID', 'achievement']
                    s_msg = main_label.split(" ")
                    for word in exclude_list:
                        if word in s_msg:
                            break
                    else:
                        include_list = [
                            'slain',
                            'went up in flames',
                            'fell out of the world',
                            'drowned',
                            'killed by',
                            'blown up by',
                            'suffocated in',
                            ' lava',
                            'hit the ground too hard',
                            'fell ',
                            'to fall',
                            'walked into the danger zone',
                            'struck by lightning',
                            ' froze',
                            'shot by',
                            'pummeled by',
                            'fireballed by',
                            'obliterated by',
                            'to death',
                            'squished too much',
                            'squished by',
                            'withered away',
                            ' died',
                            'impaled by',
                            'was killed',
                            'left the confines of this world',
                            'blew up'
                        ]
                        include = False

                        # Ignore false alarms from named entities
                        if not ('x=' in message and 'y=' in message and 'z=' in message):

                            for phrase in include_list:
                                if phrase in main_label.strip():
                                    include = True
                                    break

                            if include:
                                for word in s_msg:
                                    if word.strip() in self.run_data['player-list']:
                                        type_label = "CHAT"
                                        type_color = (0.439, 0.839, 1, 1)
                                        event = functools.partial(self.script_object.death_event, {'user': word.strip(), 'content': main_label.strip()})
                                        break

                if date_label and type_label and main_label and type_color:
                    return (date_label, type_label, main_label, type_color), event

        for log_line in text.splitlines():
            event = None
            if log_line:
                try: log_line, event = format_log(log_line)
                except Exception as e:
                    self._send_log(f"error processing 'log_line': {format_traceback(e)}\nlog_line: '{log_line}'", 'error')
                    continue
            if text and log_line:

                if not self.run_data:
                    return

                formatted_line = {'text': log_line}
                if formatted_line not in self.run_data['log'] and formatted_line['text']:
                    def update_headless():
                        if constants.headless:
                            for hook in self.run_data['process-hooks']:
                                hook(self.run_data['log'])

                    # Progress bars for preparing spawn area
                    def format_pct(line, *a):
                        num = int(re.search(r'\d+', line).group(0))
                        block = num // 4
                        if num < 100 and block >= 24:
                            block = 23
                        space = 24 - block
                        return f' [{"/" * block}{" " * space}] {num}%'
                    if log_line[2].startswith('Preparing spawn') and log_line[1] == 'INFO' and self.run_data['log'][-1]['text'][2].startswith('Preparing spawn'):
                        new = formatted_line['text']
                        self.run_data['log'][-1] = {'text': (new[0], new[1], f'Preparing spawn area: {format_pct(new[2])}', new[3])}
                        update_headless()
                    else:
                        if log_line[2].startswith('Time elapsed') and log_line[1] == 'INFO':
                            last = self.run_data['log'][-1]['text']
                            self.run_data['log'][-1] = {'text': (last[0], last[1], f'Preparing spawn area: {format_pct("100%")}', last[3])}
                            update_headless()

                        elif log_line[2].startswith('Preparing spawn') and log_line[1] == 'INFO':
                            last = formatted_line['text']
                            formatted_line = {'text': (last[0], last[1], f'Preparing spawn area: {format_pct(last[2])}', last[3])}

                        self.run_data['log'].append(formatted_line)

                    # Purge long ones
                    if len(self.run_data['log']) > self.max_log_size:
                        self.run_data['log'].pop(0)

                # Execute amscript event
                if event:
                    event()

    # Command handler to current server process
    def send_command(self, cmd, add_to_history=True, log_cmd=True, script=False):

        if self.running and self.run_data and len(cmd) > 0:

            # Format command with proper return
            cmd = cmd.replace('\n', '').replace('\r', '').strip()
            if cmd[0] == "/":
                cmd = cmd[1:]

            # Add to command history for input
            if add_to_history:
                if not self.run_data['command-history']:
                    self.run_data['command-history'].insert(0, cmd)
                else:
                    if cmd != self.run_data['command-history'][0]:
                        self.run_data['command-history'].insert(0, cmd)

                # Limit size of command history
                if len(self.run_data['command-history']) > 100:
                    self.run_data['command-history'].pop()

            # Send command to Popen stdin
            if self.run_data['process']:

                new_cmd = f"/{cmd}" if bool(re.match('^[a-zA-Z0-9]+$', cmd[:1])) else cmd

                # Show log
                if log_cmd:
                    self.run_data['log'].append({'text': (dt.now().strftime(fmt_date("%#I:%M:%S %p")).rjust(11), 'EXEC', f"Console issued server command: {new_cmd}", (1, 0.298, 0.6, 1))})

                # Send script event
                if self.script_object.enabled and not script:
                    # Check if command is in user command alias list, and if not don't send to server
                    self.script_object.message_event({'user': f'#{self._hash}', 'content': new_cmd})

                # Send to server if it doesn't start with !
                if not cmd.startswith("!"):
                    try:
                        # Format encoding per OS
                        if os_name == 'windows':
                            command = f"{cmd}\r\n".encode('utf-8', errors='ignore').replace(b'\xc2\xa7', b'\xa7')
                        else:
                            command = f"{cmd}\r\n".encode('utf-8', errors='ignore')

                        self.run_data['process'].stdin.write(command)
                        self.run_data['process'].stdin.flush()
                    except Exception as e:
                        if not self.running: self._send_log('command sent after process shutdown', 'warning')
                        else:                self._send_log(f"error sending command '{cmd.strip()}': {format_traceback(e)}")

    # Launch server, or reconnect to background server
    def launch(self, return_telepath=False):

        if not self.running:

            self.running = True
            self.crash_log = None
            java_check()

            # Attempt to update first
            if self.auto_update == 'true' and app_online:
                self.auto_update_func()

            script_path = generate_run_script(self.properties_dict(), custom_flags=self.custom_flags, no_flags=(not self.custom_flags and self.is_modpack))

            if not self.restart_flag:
                self.run_data['launch-time'] = None
                self.run_data['player-list'] = {}
                self.run_data['network'] = {}
                self.run_data['log'] = [{'text': (dt.now().strftime(fmt_date("%#I:%M:%S %p")).rjust(11), 'INIT', f"Launching '{self.name}', please wait...", (0.7,0.7,0.7,1))}]
                self.run_data['process-hooks'] = []
                self.run_data['close-hooks'] = [self.auto_backup_func]
                self.run_data['console-panel'] = None
                self.run_data['performance-panel'] = None
                self.run_data['command-history'] = []
                self.run_data['playit-tunnel'] = None
                self.run_data['entitydata-cache'] = {}
            else:
                self.run_data['log'].append({'text': (dt.now().strftime(fmt_date("%#I:%M:%S %p")).rjust(11), 'INIT', f"Restarting '{self.name}', please wait...", (0.7, 0.7, 0.7, 1))})
                if self.run_data['console-panel'] and not constants.headless:
                    self.run_data['console-panel'].toggle_deadlock(False)

            if self.custom_flags:
                self.run_data['log'].append({'text': (dt.now().strftime(fmt_date("%#I:%M:%S %p")).rjust(11), 'INIT', f"Using launch flags: '{self.custom_flags}'", (0.7, 0.7, 0.7, 1))})
                # Prevent bugs when closing immediately due to bad flags
                time.sleep(1)

            self.run_data['performance'] = {'ram': 0, 'cpu': 0, 'uptime': '00:00:00:00', 'current-players': []}
            self.run_data['deadlocked'] = False

            # Run data hashes to check for configuration changes post launch
            self.run_data['properties-hash'] = self._get_properties_hash()
            self.run_data['advanced-hash'] = self._get_advanced_hash()
            self.run_data['addon-hash'] = None
            if self.addon: self.run_data['addon-hash'] = deepcopy(self.addon._addon_hash)
            self.run_data['script-hash'] = deepcopy(self.script_manager._script_hash)

            # Write Geyser config if it doesn't exist
            if self.geyser_enabled: create_geyser_config(self)

            # Open server script and attempt to launch
            with open(script_path, 'r') as f:
                script_content = f.read()
                firewall_block = False

                # On Windows, prompt to allow Java rule with netsh & UAC
                if os_name == "windows":

                    # Check if Windows Firewall is enabled
                    if "OFF" not in str(run('netsh advfirewall show allprofiles | findstr State', shell=True, stdout=PIPE, stderr=PIPE).stdout):
                        exec_type = 'legacy' if constants.java_executable['legacy'] in script_content else 'modern' if constants.java_executable['modern'] in script_content else 'lts'
                        if run_proc(f'netsh advfirewall firewall show rule name="auto-mcs java {exec_type}"') == 1:
                            net_test = ctypes.windll.shell32.ShellExecuteW(None, "runas", 'netsh', f'advfirewall firewall add rule name="auto-mcs java {exec_type}" dir=in action=allow enable=yes program="{constants.java_executable[exec_type]}"', None, 0)
                            if net_test == 5:
                                self.run_data['log'].append({'text': (dt.now().strftime(fmt_date("%#I:%M:%S %p")).rjust(11), 'WARN', f"Java is blocked by Windows Firewall: can't accept external connections", (1, 0.659, 0.42, 1))})
                                firewall_block = True

                # Check for networking conflicts and current IP
                self.run_data['network'] = get_current_ip(self.name, proxy=self.proxy_enabled)

                # Launch playit if proxy is enabled
                if self.proxy_enabled and app_online and self.proxy_installed():

                    try:
                        self.run_data['playit-tunnel'] = playit.start_tunnel(self)
                        hostname = self.run_data['playit-tunnel'].hostname
                        self.run_data['network']['address']['ip'] = hostname
                        self.run_data['network']['public_ip'] = hostname
                        self.send_log(f"Initialized playit connection '{hostname}'", 'success')

                    except Exception as e:
                        playit._send_log(f'error starting playit service: {format_traceback(e)}', 'error')

                        # Temporary warning notice for Geyser
                        if self.geyser_enabled: self.send_log(f"The internal playit service doesn't currently support Geyser, playit will need to be set up manually", 'warning')
                        else:                   self.send_log(f"The internal playit service is currently unavailable", 'warning')
                        self.run_data['playit-tunnel'] = None

                # If port was changed, use that instead
                if self.run_data['network']['original_port']:
                    self.run_data['log'].append({'text': (dt.now().strftime(fmt_date("%#I:%M:%S %p")).rjust(11), 'WARN', f"Networking conflict detected: temporarily using '*:{self.run_data['network']['address']['port']}'", (1, 0.659, 0.42, 1))})

                # Run server
                self.run_data['process'] = Popen(script_content, stdout=PIPE, stdin=PIPE, stderr=PIPE, cwd=self.server_path, shell=True)
                self._send_log(f'launching the server process with PID {self.run_data["process"].pid}', 'info')

            self.run_data['pid'] = self.run_data['process'].pid
            self.run_data['send-command'] = self.send_command



            # ----------------------------------------------------------------------------------------------------------
            # Main server process loop, handles reading output, hooks, and crash detection
            def process_thread(*args):
                if version_check(self.version, '<', '1.7'):
                    lines_iterator = iter(self.run_data['process'].stderr.readline, "")
                    log_file = os.path.join(self.server_path, 'server.log')
                else:
                    lines_iterator = iter(self.run_data['process'].stdout.readline, "")
                    log_file = os.path.join(self.server_path, 'logs', 'latest.log')

                # Initialize variables
                fail_counter = 0
                close = False
                crash_info = None
                error_list = []

                accumulating = False
                accumulated_lines = []
                brace_count = 0

                def is_entity_data_start(string):
                    return ' has the following entity data: ' in string and not string.strip().endswith('}')

                def is_complete_entity_data(string):
                    string = string.decode(errors='ignore')
                    return ' has the following entity data: ' in string and string.strip().endswith('}')


                for line in lines_iterator:
                    decoded_line = line.decode(errors='ignore')

                    # Combine playerdata that spans multiple lines
                    if is_entity_data_start(decoded_line):
                        accumulating = True
                        accumulated_lines = [decoded_line]
                        brace_count = decoded_line.count('{') - decoded_line.count('}')
                        continue

                    # Append next line
                    elif accumulating:
                        accumulated_lines.append(decoded_line)
                        brace_count += decoded_line.count('{') - decoded_line.count('}')

                        # Completed data
                        if brace_count == 0:
                            line = ''.join(accumulated_lines).encode()
                            accumulating = False
                            accumulated_lines = []
                            brace_count = 0
                        else:
                            continue

                    # Add to list
                    if is_complete_entity_data(line):
                        data = line.decode().strip()
                        player = re.findall(r'(?<=\: )(.*)(?= has the following entity data)', data)[0]
                        self.run_data['entitydata-cache'][player] = data
                        self.run_data['entitydata-cache']['$newest'] = data
                        continue

                    try:
                        # Append legacy errors to error list
                        if version_check(self.version, '<', '1.7'):
                            if "[STDERR] ".encode() in line:
                                error_list.append(line.decode().split("[STDERR] ")[1])
                                continue

                        self.update_log(line)

                    except Exception as e:
                        self._send_log(f"error processing 'line': {format_traceback(e)}\nline: '{line}'", 'error')

                    fail_counter = 0 if line else (fail_counter + 1)

                    # Close wrapper if server is closed
                    if not self.running or self.run_data['process'].poll() is not None or fail_counter > 25:


                        # Initially check for crashes
                        def get_latest_crash():
                            crash_log = None

                            # First, check if a recent crash-reports file exists
                            if server_path(self.name, 'crash-reports'):
                                crash_log = sorted(glob(os.path.join(self.server_path, 'crash-reports', 'crash-*-server.*')), key=os.path.getmtime)
                                if crash_log:
                                    crash_log = crash_log[-1]
                                    if ((dt.now() - dt.fromtimestamp(os.path.getmtime(crash_log))).total_seconds() <= 30):
                                        crash_log = crash_log
                                    else:
                                        crash_log = None

                            # If crash report file does not exist, try to deduce what happened and make a new one
                            if not crash_log:

                                if version_check(self.version, '<', '1.7'):
                                    error = ''.join(error_list)
                                else:
                                    output, error = self.run_data['process'].communicate()
                                    error = error.decode().replace('\r', '')
                                file = None


                                # If the log was modified recently, try and scrape error from there
                                use_error = True
                                if os.path.exists(log_file) and ((dt.now() - dt.fromtimestamp(os.path.getmtime(log_file))).total_seconds() <= 30):

                                    with open(log_file, 'r') as f:
                                        file = f.read()

                                        # If older log, split to the newest session
                                        if os.path.basename(log_file) == 'server.log':
                                            identifier = "[INFO] Starting minecraft server version"
                                            file = identifier + file.split(identifier)[-1]
                                            date = file.splitlines()[1].split(' [')[0]
                                            file = f"{date} {file}"

                                        # Iterate through log to find errors
                                        file_lines = file.splitlines()
                                        for x, log_line in enumerate(file_lines):
                                            if (("crash report" in log_line.lower()) or
                                            ("a server is already running on that port" in log_line.lower()) or
                                            ("failed to start the minecraft server" in log_line.lower()) or
                                            ("you need to agree to the eula" in log_line.lower()) or
                                            ("incompatible mods found" in log_line.lower()) or
                                            ("FATAL]" in log_line or "encountered an unexpected exception" in log_line.lower())):
                                                file = '\n'.join(file_lines[x:])
                                                use_error = False
                                                break

                                        # If file wasn't split, don't use it
                                        else:
                                            if not (error and use_error):
                                                file = None
                                                error = False
                                                return None


                                # Use STDERR if no exception was found
                                if error and use_error:
                                    file = error.replace('\r', '').strip()


                                # If the crash was located, write it to the log file
                                folder_path = os.path.join(self.server_path, 'crash-reports')
                                crash_log = os.path.join(folder_path, dt.now().strftime("crash-%Y-%m-%d_%H.%M.%S-server.txt"))
                                folder_check(folder_path)

                                with open(crash_log, 'w+') as f:
                                    content = "---- Minecraft Crash Report ----\n"
                                    content += "// This report was generated by auto-mcs\n\n"
                                    content += f"Time: {dt.now().strftime(fmt_date('%#m/%#d/%y, %#I:%M %p'))}\n"

                                    if file:
                                        if "a server is already running on that port" in file.lower():
                                            content += "Description: Networking conflict\n\n"
                                            file = f"A connection is already active on *:{self.port}. Change the 'server-port' parameter in 'server.properties', or close the conflicting connection."
                                        elif "you need to agree to the eula" in file.lower():
                                            content += "Description: License error\n\n"
                                            file = "You need to agree to the EULA in order to run the server. Go to 'eula.txt' for more info."
                                        else:
                                            content += "Description: Exception in server tick loop\n\n"
                                        content += file

                                    # If error was not found, generate generic error
                                    else:
                                        content += "Description: Unknown exception\n\n"
                                        content += f"Something went wrong launching '{self.name}': an unspecified error has occurred. To troubleshoot, try the following:\n"
                                        content += f" - Verify that the server isn't already running in another process\n"
                                        content += f" - Verify that 'EULA.txt' is set to true\n"
                                        if self.type.lower() != 'vanilla':
                                            content += f" - Disable all {'mods' if self.type.lower() in ('fabric', 'forge') else 'plugins'} in the Add-on Manager\n"
                                        content += f" - Try using a different world file\n"
                                        content += f" - Try a different server file with the 'Change server.jar' option in the Settings tab\n"
                                        content += f"     - If this error was caused after using 'Change server.jar', there's an automatic back-up of the previous version in the Back-up Manager"

                                    f.write(content)

                            self.crash_log = crash_log
                            return crash_log


                        # Check for crash if exit code is not 0
                        if self.run_data['process'].returncode != 0:

                            # Check for false positives
                            false_positive = False
                            if error_list:
                                joined_errors = '\n'.join(error_list)

                                if 'java.net.SocketException: socket closed' in joined_errors:
                                    false_positive = True

                                if 'Server will start in ' in joined_errors:
                                    false_positive = True

                            if not false_positive:
                                crash_info = get_latest_crash()

                        # If server closes within 3 seconds, something probably went wrong
                        elif (dt.now() - self.run_data['launch-time']).total_seconds() <= 3:
                            crash_info = get_latest_crash()

                        # At last, check if there are problematic log events
                        else:
                            for log in reversed(self.run_data['log'][-50:]):
                                log = log['text']

                                if log[1] == "FATAL":
                                    crash_info = get_latest_crash()
                                    break

                                elif (log[1] in ('ERROR', 'CRITICAL', 'WARN', 'SEVERE')) and (("crash report" in log[2].lower()) or
                                                                                              ("a server is already running on that port" in log[2].lower()) or
                                                                                              ("you need to agree to the eula" in log[2].lower()) or
                                                                                              ("incompatible mods found" in log[2].lower()) or
                                                                                              ("failed to start the minecraft server" in log[2].lower()) or
                                                                                              ("encountered an unexpected exception" in log[2].lower())):
                                    crash_info = get_latest_crash()
                                    break


                        # Log shutdown data
                        if crash_info:
                            self.run_data['log'].append({'text': (dt.now().strftime(fmt_date("%#I:%M:%S %p")).rjust(11), 'INIT', f"'{self.name}' has stopped unexpectedly", (1,0.5,0.65,1))})
                        else:
                            self.run_data['log'].append({'text': (dt.now().strftime(fmt_date("%#I:%M:%S %p")).rjust(11), 'INIT', f"'{self.name}' has stopped successfully", (0.7,0.7,0.7,1))})

                        close = True


                    # Run process hooks
                    for hook in self.run_data['process-hooks']:
                        hook(self.run_data['log'])


                    # Do things when server closes
                    if close:

                        for hook in self.run_data['close-hooks']:
                            hook(crash_info)

                        break


                # Close server
                self.terminate()
                return

            # ----------------------------------------------------------------------------------------------------------



            self.run_data['thread'] = Timer(0, process_thread)
            self.run_data['thread'].daemon = True
            self.run_data['thread'].start()
            self.run_data['launch-time'] = dt.now()

            self._manager.running_servers[self.name] = self
            self._start_performance_clock()


            # Add and delete temp file to update last modified time of server directory
            with open(os.path.join(self.server_path, 'session.mcs'), 'w+') as f:
                f.write(self.name)
            os.remove(os.path.join(self.server_path, 'session.mcs'))
            self.last_modified = os.path.getmtime(self.server_path)


            # Initialize ScriptObject
            try:
                from source.core.server.amscript import ScriptObject
                self.script_object = ScriptObject(self)

                # Fire server start event
                if self.script_object.enabled:
                    loaded_count, total_count = self.script_object.construct()
                    self.script_object.start_event({'date': dt.now()})


                # If start-cmd.tmp exists, run every command in file (that is allowed by the command_whitelist)
                cmd_tmp = server_path(self.name, command_tmp)
                command_whitelist = ('gamerule')
                if cmd_tmp:
                    with open(cmd_tmp, 'r') as f:
                        for cmd in f.readlines():
                            if cmd.split(' ')[0] in command_whitelist:
                                self.send_command(cmd.strip(), add_to_history=False, log_cmd=False)
                    os.remove(cmd_tmp)

            # Server closed prematurely
            except AttributeError:
                pass

            self.restart_flag = False

        # Return stripped data if telepath session
        try:
            if self._is_telepath_session() and return_telepath:
                return self._sync_attr('run_data')
        except AttributeError:
            pass
        return self.run_data

    # Kill server and delete running configuration
    def terminate(self):
        if not self.restart_flag: self._send_log('terminating the server process...', 'info')

        # Kill server process
        try:
            if self.run_data['process'].poll() is None:
                self.run_data['process'].kill()

        # Ignore errors stopping the process
        except Exception as e:
            self._send_log(f'failed to terminate the server process: {format_traceback(e)}')
            return

        # Reset port back to normal if required
        if self.run_data['network']['original_port']:
            lines = []
            with open(server_path(self.name, "server.properties"), 'r') as f:
                lines = f.readlines()

            with open(server_path(self.name, "server.properties"), 'w+') as f:
                for line in lines:
                    if re.search(r'server-port=', line):
                        lines[lines.index(line)] = f"server-port={self.run_data['network']['original_port']}\n"
                        break
                f.writelines(lines)


        # Fire server stop event
        try:
            if self.script_object.enabled:
                crash_data = None
                if self.crash_log:
                    with open(self.crash_log, 'r') as f:
                        crash_data = f.read()
                self.script_object.deconstruct(crash_data=crash_data)
            del self.script_object
            self.script_object = None

        except AttributeError:
            pass


        # Add and delete temp file to update last modified time of server directory
        with open(os.path.join(self.server_path, 'session.mcs'), 'w+') as f:
            f.write(self.name)
        os.remove(os.path.join(self.server_path, 'session.mcs'))
        self.last_modified = os.path.getmtime(self.server_path)


        if not self.restart_flag:

            # First, copy log for telepath stop data if remote
            if self._is_telepath_session():
                self._last_telepath_log = deepcopy(self.run_data['log'])

            # Delete log from memory (hopefully)
            for item in self.run_data['log']:
                self.run_data['log'].remove(item)
                del item

            # Close proxy if running
            try:
                if self.run_data['playit-tunnel']:
                    playit.stop_tunnel(self)
            except KeyError:
                pass

            self.run_data.clear()
            self.running = False
            del self._manager.running_servers[self.name]
            self._send_log('successfully stopped the server process', 'info')

        # Reboot server if required
        else:
            self.running = False
            self.launch()

    # Restarts server, for amscript
    def restart(self):
        self.restart_flag = True
        try:
            for player in self.run_data['player-list'].keys():
                self.silent_command(f"kick {player} Server is restarting", log=False)
        except KeyError:
            pass
        self._send_log('restarting the server process...', 'info')
        self.stop()

    # Stops the server
    def stop(self):
        self.silent_command('stop')

    # Forcefully ends the server process
    def kill(self):

        # Iterate over self and children to find Java process
        try:
            parent = psutil.Process(self.run_data['process'].pid)
            self._send_log(f"attempting to kill the server process with PID {self.run_data['process'].pid}", 'info')
        except:
            return False
        sys_mem = round(psutil.virtual_memory().total / 1048576, 2)

        # Windows
        if os_name == "windows":
            children = parent.children(recursive=True)
            for proc in children:
                if proc.name() == "java.exe":
                    run_proc(f"taskkill /f /pid {proc.pid}")
                    break

        # macOS
        elif os_name == "macos":
            if parent.name() == "java":
                run_proc(f"kill -9 {parent.pid}")

        # Linux
        else:
            if parent.name() == "java":
                run_proc(f"kill -9 {parent.pid}")
            else:
                children = parent.children(recursive=True)
                for proc in children:
                    if proc.name() == "java":
                        run_proc(f"kill -9 {proc.pid}")
                        break


    # Checks if a server has closed, but hangs
    def check_for_deadlock(self):
        ip = self.run_data['network']['private_ip']
        port = int(self.run_data['network']['address']['port'])

        def check(*a):
            while self.running and check_port(ip, port):
                time.sleep(1)

            # If after a delay the server is still running, it is likely deadlocked
            time.sleep(1)
            if self.running and self.name not in backup_lock and not self.restart_flag:
                try:
                    # Delay if CPU usage is higher than expected
                    if self.run_data['performance']['cpu'] > 0.3:
                        time.sleep(15)
                    message = f"'{self.name}' is deadlocked, please kill it above to continue..."
                    self.run_data['deadlocked'] = True
                    if message != self.run_data['log'][-1]['text'][2]:
                        self.send_log(message, 'warning')
                        self._send_log(f"detected that the server process with PID {self.run_data['process'].pid} is deadlocked", 'warning')
                    self.run_data['console-panel'].toggle_deadlock(True)
                except:
                    pass

        t = threading.Timer(0, check)
        t.daemon = True
        t.start()


    # Retrieves performance information
    def performance_stats(self, interval=0.5, update_players=False):
        perc_cpu = 0
        perc_ram = 0

        # Get Java process
        try:
            parent = psutil.Process(self.run_data['process'].pid)
            sys_mem = round(psutil.virtual_memory().total / 1048576, 2)

            # Get performance stats of cmd > java.exe
            if os_name == "windows":
                children = parent.children(recursive=True)
                for proc in children:
                    if proc.name() == "java.exe":
                        perc_cpu = proc.cpu_percent(interval=interval)
                        perc_ram = round(proc.memory_info().private / 1048576, 2)
                        break

            # Get RSS of parent on macOS
            elif os_name == "macos":
                if parent.name() == "java":
                    perc_cpu = parent.cpu_percent(interval=interval)
                    perc_ram = round(parent.memory_info().rss / 1048576, 2)

            # Get performance stats of forked java process
            else:
                if parent.name() == "java":
                    perc_cpu = parent.cpu_percent(interval=interval)
                    perc_ram = round(parent.memory_info().vms / 1048576, 2)
                else:
                    children = parent.children(recursive=True)
                    for proc in children:
                        if proc.name() == "java":
                            perc_cpu = proc.cpu_percent(interval=interval)
                            perc_ram = round(proc.memory_info().vms / 1048576, 2)
                            break

            perc_cpu = round(perc_cpu / psutil.cpu_count(), 2)
            perc_ram = round(((perc_ram / sys_mem) * 100), 2)

        except:
            pass

        if not self.run_data:
            return

        # Format up-time
        try:
            delta = (dt.now() - self.run_data['launch-time'])
            time_str = str(delta).split(',')[-1]
            if '.' in time_str:
                time_str = time_str.split('.')[0]
            formatted_date = f"{str(delta.days)}:{time_str.strip().zfill(8)}".zfill(11)
        except KeyError:
            return False

        def limit_percent(pct):
            if pct < 0:
                return 0
            if pct > 100:
                return 100
            else:
                return pct

        self.run_data['performance']['cpu'] = limit_percent(perc_cpu)
        self.run_data['performance']['ram'] = limit_percent(perc_ram)
        self.run_data['performance']['uptime'] = formatted_date


        # Update players
        if update_players:
            self.acl.reload_list('ops')
            final_list = []
            try:
                player_list = self.run_data['player-list']
            except KeyError:
                return

            # Update player list
            for player, data in player_list.items():
                if data['logged-in']:
                    if self.acl.rule_in_acl(player, 'ops'):
                        final_list.insert(0, {'text': player, 'color': (0.5, 1, 1, 1)})
                    else:
                        final_list.append({'text': player, 'color': (0.6, 0.6, 0.88, 1)})

            self.run_data['performance']['current-players'] = final_list

    # Sets maximum allocated memory when launching
    def set_ram_limit(self, value='auto'):
        new_value = str(value).lower()
        self.config_file = server_config(self.name)
        self.config_file.set("general", "allocatedMemory", new_value)
        self.dedicated_ram = new_value
        server_config(self.name, self.config_file)

        log_value = new_value if new_value == 'auto' else f'{new_value} GB'
        self._send_log(f"changed memory allocation to: '{log_value}'")
        return new_value

    # Sets automatic update configuration
    def enable_auto_update(self, enabled=True):
        new_value = str(enabled).lower()
        self.config_file = server_config(self.name)
        self.config_file.set("general", "updateAuto", new_value)
        self.auto_update = new_value
        server_config(self.name, self.config_file)

        action = 'enabled' if enabled else 'disabled'
        self._send_log(f"{action} automatic updates", 'info')
        return enabled

    # Updates custom flags
    def update_flags(self, flags):
        self.config_file = server_config(self.name)
        self.config_file.set("general", "customFlags", flags.strip())
        self.custom_flags = flags.strip()
        server_config(self.name, self.config_file)
        self._send_log(f"changed launch flags to:\n{flags}", 'info')

    # Updates the server icon, deletes if "new_icon" is empty
    def update_icon(self, new_icon: str or False):
        data = update_server_icon(self.name, new_icon)
        self.server_icon = server_path(self.name, 'server-icon.png')
        self._send_log(f"changed icon to '{new_icon}'", 'info')
        return data

    # Updates console event filter in config
    # 'everything', 'errors', 'players', 'amscript'
    def change_filter(self, filter_type: str):
        self.config_file = server_config(self.name)
        self.config_file.set("general", "consoleFilter", filter_type)
        server_config(self.name, self.config_file)
        self._send_log(f"changed console filter to '{filter_type}'")

    # Renames server
    def rename(self, new_name: str):
        if not self.running:
            original_name = self.name
            new_name = new_name.strip()
            self._send_log(f"renaming myself: '{original_name}' -> '{new_name}'", 'info')


            # Change name in config
            self.config_file.set('general', 'serverName', new_name)
            self.write_config()

            # Rename persistent configuration for amscript
            # config_path = os.path.join(configDir, 'amscript', 'pstconf')
            # old_hash = int(hashlib.sha1(original_name.encode("utf-8")).hexdigest(), 16) % (10 ** 12)
            # old_path = os.path.join(config_path, f"{old_hash}.json")
            # if os.path.isfile(old_path):
            #     new_hash = int(hashlib.sha1(new_name.encode("utf-8")).hexdigest(), 16) % (10 ** 12)
            #     new_path = os.path.join(config_path, f"{new_hash}.json")
            #     try:
            #         os.rename(old_path, new_path)
            #     except:
            #         pass

            # Change folder name
            new_path = os.path.join(serverDir, new_name)
            os.rename(self.server_path, new_path)
            self.server_path = new_path
            self.name = new_name

            # Reset server object properties
            backup.rename_backups(original_name, new_name)

            # Reset constants properties
            constants.server_manager.create_server_list()
            self._manager.check_for_updates()

            # Reload properties
            if self.name == new_name: self._send_log(f"successfully renamed myself to '{new_name}'", 'info')
            else:                     self._send_log(f"something went wrong renaming myself to '{new_name}'", 'error')
            self.reload_config(reload_objects=True)

    # Deletes server
    def delete(self):
        if not self.running:
            self._send_log("I'm deleting myself, please wait :(", 'warning')

            # Save a back-up of current server state
            while not self.backup:
                time.sleep(0.1)

            if check_free_space():
                self.backup.save()

            # Delete server folder
            safe_delete(self.server_path)
            self._send_log("Mr. Stark, I don't feel so good...", 'warning')
            del self

    # Checks for modified 'server.properties'
    def _get_properties_hash(self):
        # return hash(frozenset(self.server_properties.items()))
        return ''.join(sorted([str(a).strip() for a in self.server_properties.values()]))

    # Checks modified advanced settings to check for a restart
    def _get_advanced_hash(self):
        return str(str(self.custom_flags) + str(self.properties_hash) + str(self.proxy_enabled).lower()[0] + str(self.geyser_enabled).lower()[0] + str(self.dedicated_ram)).strip()


    # Attempts to automatically update the server
    def auto_update_func(self, *args):
        if self.auto_update == 'prompt':
            return False

        elif self.auto_update == 'true' and app_online:
            return True

        else:
            return False

    # Attempts to automatically back up the server
    def auto_backup_func(self, crash_info, *args):
        auto_backup = self.backup._backup_stats['auto-backup']

        if auto_backup == 'prompt':
            return False

        elif auto_backup == 'true':
            if crash_info:
                self.send_log("Skipping back-up due to a crash", 'error')
                self._send_log("skipping back-up due to a crash", 'error')
            elif not check_free_space():
                self.send_log("Skipping back-up due to insufficient free space", 'error')
                self._send_log("skipping back-up due to insufficient free space", 'error')
            else:
                self.send_log(f"Saving a back-up of '{self.name}', please wait...", 'warning')
                self.backup.save(ignore_running=True)
                self.send_log("Back-up complete!", 'success')
            return True

        else:
            return False


    # Reloads all auto-mcs scripts
    def reload_scripts(self):
        if self.script_object:
            self._send_log(f"restarting the amscript engine...")

            # Delete ScriptObject
            self.script_object.deconstruct()
            del self.script_object

            # Initialize ScriptObject
            from source.core.server.amscript import ScriptObject
            self.script_object = ScriptObject(self)
            loaded_count, total_count = self.script_object.construct()
            self.script_object.start_event({'date': dt.now()})
            self.run_data['script-hash'] = deepcopy(self.script_manager._script_hash)

            return loaded_count, total_count
        else:
            return None, None

    # Returns data from amscript
    def get_ams_info(self):
        return {'version': ams_version, 'installed': self.script_manager.installed_scripts}

    # Methods strictly to send to amscript.ServerScriptObject
    # Castrated log function to prevent recursive events, sends only INFO, WARN, ERROR, and SUCC
    # log_type: 'info', 'warning', 'error', 'success'
    def send_log(self, text: str, log_type='info', *args):
        if not text:
            return

        text = str(text)

        log_type = log_type if log_type in ('info', 'warning', 'error', 'success') else 'info'
        text = text.encode().replace(b'\xa7', b'\xc2\xa7').decode('utf-8', errors='ignore')

        # (date, type, log, color)
        def format_log(message, *args):

            def format_color(code, *args):
                if 'r' not in code:
                    formatted_code = f'[color={color_table[code]}]'
                else:
                    formatted_code = '[/color]'
                return formatted_code

            date_label = ''
            type_label = ''
            main_label = ''
            type_color = ''

            if message:

                message_date_obj = dt.now()
                date_label = message_date_obj.strftime(fmt_date("%#I:%M:%S %p")).rjust(11)

                # Format string as needed

                # Shorten coordinates because FUCK they are long
                if "logged in with entity id" not in message:
                    for float_str in re.findall(r"[-+]?(?:\d*\.*\d+)", message):
                        if len(float_str) > 5 and float_str.count(".") == 1:
                            message = message.replace(float_str, str(round(float(float_str), 2)))

                if message.endswith("[m"):
                    message = message.replace("[m", "").rstrip()

                # Format special color codes
                if '§' in message:
                    original_message = message

                    try:
                        message = escape_markup(message)
                        code_list = [message[x:x + 2] for x, y in enumerate(message, 0) if y == '§']
                        for code in code_list:
                            message = message.replace(code, '' if constants.headless else format_color(code))

                        if (len(code_list) % 2 == 1) and not constants.headless:
                            message = message + '[/color]'

                    except KeyError:
                        message = original_message

                main_label = message.rstrip()

                if log_type == 'warning':
                    type_label = "WARN"
                    type_color = (1, 0.804, 0.42, 1)
                elif log_type == 'error':
                    type_label = "ERROR"
                    type_color = (1, 0.5, 0.65, 1)
                elif log_type == 'success':
                    type_label = "SUCCESS"
                    type_color = (0.3, 1, 0.6, 1)
                else:
                    type_label = "INFO"
                    type_color = (0.6, 0.6, 1, 1)

            if date_label and type_label and main_label and type_color:
                return (date_label, type_label, main_label, type_color)

        for log_line in text.splitlines():
            if text and log_line:
                formatted_line = {'text': format_log(log_line)}
                if formatted_line != self.run_data['log'][-1] and formatted_line['text']:
                    self.run_data['log'].append(formatted_line)

                    # Purge long ones
                    if len(self.run_data['log']) > self.max_log_size:
                        self.run_data['log'].pop(0)

        # Run process hooks
        for hook in self.run_data['process-hooks']:
            hook(self.run_data['log'])


    # Methods strictly to receive from amscript.ScriptObject
    # Castrated log function to prevent recursive events, sends only INFO, WARN, ERROR, and SUCC
    # log_type: 'print', 'info', 'warning', 'error', 'success'
    def amscript_log(self, text: str, log_type='info', *args):
        if not text or 'log' not in self.run_data:
            return

        log_type = log_type if log_type in ('print', 'info', 'warning', 'error', 'success') else 'info'
        text = text.encode().replace(b'\xa7', b'\xc2\xa7').decode('utf-8', errors='ignore')

        # (date, type, log, color)
        def format_log(message, *args):

            def format_color(code, *args):
                if 'r' not in code:
                    formatted_code = f'[color={color_table[code]}]'
                else:
                    formatted_code = '[/color]'
                return formatted_code

            date_label = ''
            type_label = ''
            main_label = ''
            type_color = ''

            if message:
                message_date_obj = dt.now()
                date_label = message_date_obj.strftime(fmt_date("%#I:%M:%S %p")).rjust(11)

                main_label = message.rstrip()
                type_label = "AMS"

                if log_type == 'print':
                    type_color = (0.9, 0.9, 0.9, 1)
                elif log_type == 'warning':
                    type_color = (1, 0.659, 0.42, 1)
                elif log_type == 'error':
                    type_color = (1, 0.5, 0.65, 1)
                elif log_type == 'success':
                    type_color = (0.3, 1, 0.6, 1)
                else:
                    type_color = (0.6, 0.6, 1, 1)

            if date_label and type_label and main_label and type_color:
                return (date_label, type_label, main_label, type_color)

        for log_line in text.splitlines():
            if text and log_line:
                formatted_line = {'text': format_log(log_line)}
                if formatted_line not in self.run_data['log'] and formatted_line['text']:
                    self.run_data['log'].append(formatted_line)

                    # Purge long ones
                    if len(self.run_data['log']) > self.max_log_size:
                        self.run_data['log'].pop(0)

        # Run process hooks
        for hook in self.run_data['process-hooks']:
            hook(self.run_data['log'])


    # Retrieves cached entity player data
    def get_entity_data(self, player, newest=False):
        original_data = None

        if player in self.run_data['entitydata-cache']:
            original_data = deepcopy(self.run_data['entitydata-cache'][player])

        # Format command to server based on version
        if version_check(self.version, '>=', '1.13'):
            command = f'data get entity {player}'
        else:
            return ""

        # If newest, use the newest tag
        if newest:
            player = '$newest'
            if '$newest' in self.run_data['entitydata-cache']:
                original_data = deepcopy(self.run_data['entitydata-cache'][player])

        self.silent_command(command)

        # Wait for data to get updated/sent from the server
        for timeout in range(50):
            if player in self.run_data['entitydata-cache'] and self.run_data['entitydata-cache'][player] != original_data:
                return self.run_data['entitydata-cache'][player]
            time.sleep(0.001)

        # If nothing, return the last tag
        if player in self.run_data['entitydata-cache']:
            return self.run_data['entitydata-cache'][player]
        return ""


    # Returns a username from a player selector
    def parse_tag(self, selector: str):
        data = self.get_entity_data(selector, True)
        player = re.findall(r'(?<=\: )(.*)(?= has the following entity data)', data)[0]
        return player


    # Sends a command that doesn't show up in the console
    def silent_command(self, cmd, log=False):
        self.send_command(cmd, False, log, True)


    # Retrieves updated player list from run_data
    def get_players(self):
        if self.run_data:
            return self.run_data['player-list']
        return {}


    # Retrieves IDE suggestions from internal objects
    def _retrieve_suggestions(self):
        script_obj = constants.script_obj

        # Gets list of functions and attributes
        def iter_attr(obj, a_start=''):
            final_list = []
            for attr in dir(obj):
                if not attr.startswith('_') and not attr[0].isupper():
                    if callable(getattr(obj, attr)):
                        final_list.append(a_start + attr + '()')
                    else:
                        final_list.append(a_start + attr)
            final_list = sorted(final_list, key=lambda x: x.endswith('()'), reverse=True)
            return final_list

        # Prevent race condition
        while not self.script_manager or not self.acl or not self.addon or not self.backup:
            time.sleep(0.1)

        from source.core.server.amscript import ServerScriptObject, PlayerScriptObject
        server_so = ServerScriptObject(self)
        player_so = PlayerScriptObject(server_so, server_so._server_id)
        suggestions = {
            '@': script_obj.valid_events,
            'server.': iter_attr(server_so),
            'acl.': iter_attr(self.acl),
            'addon.': iter_attr(self.addon),
            'backup.': iter_attr(self.backup),
            'amscript.': iter_attr(self.script_manager),
            'player.': iter_attr(player_so),
        }
        suggestions['enemy.'] = suggestions['player.']

        self._send_log(f"generated IDE auto-complete suggestions:\n{suggestions}")
        return suggestions

    # Shows taskbar notifications
    def _view_notif(self, name, add=True, viewed=''):
        self._send_log(f"set notification view state for '{name}':\nadd: '{add}'\nviewed: '{viewed}'")
        if name and add:
            show_notif = name not in self.viewed_notifs
            if name in self.viewed_notifs:
                show_notif = viewed != self.viewed_notifs[name]

            if self.taskbar and show_notif:
                try:
                    self.taskbar.show_notification(name)
                except AttributeError:
                    pass

            if name in self.viewed_notifs:
                if viewed: self.viewed_notifs[name] = viewed
            else:
                self.viewed_notifs[name] = viewed

        elif (not add) and (name in self.viewed_notifs):
            del self.viewed_notifs[name]

        self.config_file = server_config(self.name)
        self.config_file.set("general", "viewedNotifs", json.dumps(self.viewed_notifs))
        self.write_config()


# Low calorie version of ServerObject for a ViewClass in the Server Manager screen
class ViewObject():
    def __init__(self, _manager: 'ServerManager', server_name: str):
        from source.core.server.foundry import latestMC

        self._manager = _manager
        self._telepath_data = None
        self.name = server_name
        self._view_name = server_name
        self.running = self.name in self._manager.running_servers.keys()
        self.server_icon = server_path(self.name, 'server-icon.png')

        if self.running:
            server_obj = self._manager.running_servers[self.name]
            self.run_data = {'network': server_obj.run_data['network']}
            self.run_data['playit-tunnel'] = bool(server_obj.run_data['playit-tunnel'])
        else:
            self.run_data = {}


        # Server files
        self.config_file = server_config(server_name)

        # Server properties
        self.favorite = self.config_file.get("general", "isFavorite").lower() == 'true'
        self.auto_update = str(self.config_file.get("general", "updateAuto").lower())
        self.type = self.config_file.get("general", "serverType").lower()
        self.version = self.config_file.get("general", "serverVersion").lower()
        self.build = None
        try:
            if self.config_file.get("general", "serverBuild"):
                self.build = self.config_file.get("general", "serverBuild").lower()
        except:
            pass
        try:
            if self.config_file.get("general", "isModpack"):
                modpack = self.config_file.get("general", "isModpack").lower()
                if modpack:
                    self.is_modpack = 'zip' if modpack != 'mrpack' else 'mrpack'
        except:
            self.is_modpack = ''

        # Check update properties for UI stuff
        self.update_string = ''
        if self.is_modpack:
            if self.update_list[self.name]['updateString'] and self.is_modpack == 'mrpack':
                self.update_string = self.update_list[self.name]['updateString']
        else:
            self.update_string = str(latestMC[self.type]) if version_check(latestMC[self.type], '>', self.version) else ''
            if not self.update_string and self.build:
                self.update_string = ('b-' + str(latestMC['builds'][self.type])) if (tuple(map(int, (str(latestMC['builds'][self.type]).split(".")))) > tuple(map(int, (str(self.build).split("."))))) else ""


        self.server_path = server_path(server_name)
        self.last_modified = os.path.getmtime(self.server_path)

    def __getattribute__(self, name):

        # Remove illegal references when sending via the API
        if name == "__dict__":
            not_allowed = ['_manager']
            data = object.__getattribute__(self, "__dict__").copy()
            for attr in not_allowed: data.pop(attr, None)
            return data

        return object.__getattribute__(self, name)

    # Make dict(self) work too
    def __iter__(self):
        return iter(self.__dict__.items())

    def __repr__(self):
        return f"<{__name__}.{self.__class__.__name__} '{self.name}' at '{self.server_path}'>"


# Loads remote server data locally for a ViewClass in the Server Manager screen
class RemoteViewObject():

    def __init__(self, _manager: 'ServerManager', instance_data: dict, server_data: dict):
        self._manager = _manager

        for k, v in server_data.items(): setattr(self, k, v)

        self._telepath_data = instance_data

        # Set display name
        if self._telepath_data['nickname']: self._telepath_data['display-name'] = self._telepath_data['nickname']
        else: self._telepath_data['display-name'] = self._telepath_data['host']
        self._view_name = f"{self._telepath_data['display-name']}/{server_data['name']}"

        self.favorite = self._is_favorite()

    def _is_favorite(self):
        try:
            if self.name in self._telepath_data['added-servers']:
                return self._telepath_data['added-servers'][self.name]['favorite']
        except KeyError: pass
        return False

    def toggle_favorite(self):
        if self.name not in self._telepath_data['added-servers']: self._telepath_data['added-servers'][self.name] = {}
        self._telepath_data['added-servers'][self.name]['favorite'] = not self.favorite
        self.favorite = not self.favorite
        self._manager.write_telepath_servers(self._telepath_data)

    def __repr__(self):
        return f"<{__name__}.{self.__class__.__name__} '{self._view_name}' at '{self._telepath_data['host']}'>"


# Houses all server information
class ServerManager():

    # Internal log wrapper
    def _send_log(self, message: str, level: str = None):
        send_log(self.__class__.__name__, message, level)

    def __init__(self):

        # --------------------------- Local server data ----------------------------

        # Stores all local server names as strings
        self.server_list:       list[str] = []
        self.server_list_lower: list[str] = []

        # Stores a sorted dict of update information per server
        self.update_list:       dict[str, dict] = {}

        # The currently active server in the menu
        self.current_server:    ServerObject    = None

        # 'self.current_server' gets moved here when launched
        self.running_servers:   dict[str, ServerObject] = {}

        # Currently active servers from a remote Telepath client, mapped by host
        self.remote_servers:    dict[str, ServerObject] = {}

        # A sorted list of all ViewObjects (by date modified) for the menu
        self.menu_view_list:    list[Union[ViewObject, RemoteViewObject]] = []

        # Load local server info
        self.create_server_list()



        # -------------------------- Telepath client data --------------------------

        # An in-memory mirror of 'telepath-servers.json'
        self.telepath_servers        = {}

        # All currently connected remote Telepath servers
        self.online_telepath_servers = []

        # A map of 'self.update_list' for each remote Telepath server
        self.remote_update_list: dict[str, dict[str, dict]] = {}

        # Load Telepath servers
        self.load_telepath_servers()

        self._send_log('initialized Server Manager', 'info')



    #  -------------------------------------------- General Methods ----------------------------------------------------

    # Return a list of every valid server in 'applicationFolder'
    def create_server_list(self) -> list[str]:
        server_list       = []
        server_list_lower = []
        og_list           = self.server_list.copy()
        og_list_lower     = self.server_list_lower.copy()

        try:
            for file in glob(os.path.join(serverDir, "*")):
                if os.path.isfile(os.path.join(file, server_ini)):
                    server_list.append(os.path.basename(file))
                    server_list_lower.append(os.path.basename(file).lower())

            self.server_list       = server_list
            self.server_list_lower = server_list_lower

        except Exception as e:
            self.server_list       = og_list
            self.server_list_lower = og_list_lower
            self._send_log(f'error generating server list: {format_traceback(e)}', 'error')

        self._send_log(f"generated server list from valid servers in '{serverDir}':\n{server_list}")
        return server_list

    # Generates sorted list of ViewObject information for menu (includes all connected Telepath servers)
    def create_view_list(self, remote_data=None) -> list[Union[ViewObject, RemoteViewObject]]:
        final_list = []
        normal_list = []
        favorite_list = []

        # Create a ViewObject from a server name
        def grab_terse_props(server_name, *args):
            server_object = ViewObject(self, server_name)
            if server_object.favorite: favorite_list.append(server_object)
            else: normal_list.append(server_object)

        try:
            with ThreadPoolExecutor(max_workers=10) as pool:
                pool.map(grab_terse_props, self.create_server_list())

            # If remote servers are specified, grab them all with an API request
            if remote_data:
                for host, instance in remote_data.items():
                    instance['host'] = host
                    try:
                        remote_servers = api_manager.request(
                            endpoint = '/main/create_view_list',
                            host = instance['host'],
                            port = instance['port'],
                            timeout = 0.5
                        )

                        def process_remote_props(server_data):
                            remote_object = RemoteViewObject(self, instance, server_data)
                            if remote_object.favorite: favorite_list.append(remote_object)
                            else: normal_list.append(remote_object)

                        try:
                            with ThreadPoolExecutor(max_workers=10) as pool:
                                pool.map(process_remote_props, remote_servers)
                        except TypeError: continue

                    # Don't load server if the Telepath instance can't be found
                    except requests.exceptions.ConnectionError: pass
                    except requests.exceptions.ReadTimeout:     pass

        except Exception as e:
            self._send_log(f'error generating menu view list: {format_traceback(e)}', 'error')


        normal_list = sorted(normal_list, key=lambda x: x.last_modified, reverse=True)
        favorite_list = sorted(favorite_list, key=lambda x: x.last_modified, reverse=True)
        final_list.extend(favorite_list)
        final_list.extend(normal_list)

        return final_list

    # Return list of every valid server update property in 'applicationFolder'
    def check_for_updates(self) -> dict[str: dict]:
        from source.core.server.addons import get_modrinth_data
        from source.core.server.foundry import latestMC

        self.update_list = {}
        self._send_log("globally checking for server updates...", 'info')

        for name in glob(os.path.join(serverDir, "*")):
            name = os.path.basename(name)

            server_data = {
                name: {
                    "updateAuto":   False,
                    "needsUpdate":  False,
                    "updateString": None,
                    "updateUrl":    None
                }
            }

            config_path = os.path.abspath(os.path.join(serverDir, name, server_ini))
            if os.path.isfile(config_path) is True:

                config = ConfigParser(allow_no_value=True, comment_prefixes=';')
                config.optionxform = str
                config.read(config_path)

                updateAuto    = str(config.get("general", "updateAuto")) == 'true'
                serverVersion = str(config.get("general", "serverVersion"))
                serverType    = str(config.get("general", "serverType"))

                try: serverBuild = str(config.get("general", "serverBuild"))
                except NoOptionError: serverBuild = ""

                try: isModpack = str(config.get("general", "isModpack"))
                except NoOptionError: isModpack = ""

                # Check if modpack needs an update if detected (show only if auto-updates are enabled)
                if isModpack:
                    if isModpack == 'mrpack':
                        modpack_data = get_modrinth_data(name)
                        if (modpack_data['version'] != modpack_data['latest']) and not modpack_data['latest'].startswith("0.0.0"):
                            server_data[name]["needsUpdate"]  = True
                            server_data[name]["updateString"] = modpack_data['latest']
                            server_data[name]["updateUrl"]    = modpack_data['download_url']


                # Check if normal server needs an update (show only if auto-updates are enabled)
                else:
                    new_version     = latestMC[serverType.lower()]
                    current_version = serverVersion

                    if ((serverType.lower() in ["forge", "paper", "purpur"]) and (serverBuild != "")) and (new_version == current_version):
                        new_version += " b-" + str(latestMC["builds"][serverType.lower()])
                        current_version += " b-" + str(serverBuild)

                    if (new_version != current_version) and not current_version.startswith("0.0.0"):
                        server_data[name]["needsUpdate"] = True

                server_data[name]["updateAuto"] = updateAuto

            self.update_list.update(server_data)

        # Log update list
        if self.update_list: self._send_log(f"updates are available for:\n{str(list(self.update_list.keys()))}", 'info')
        else:                self._send_log('all servers are up to date', 'info')

        return self.update_list

    # Refreshes self.menu_view_list with current info
    def refresh_list(self):
        self.menu_view_list = self.create_view_list(self.online_telepath_servers)

    # This method is local only to open a server in the Servers directory
    # Sets self.current_server to selected ServerObject
    def open_server(self, name):
        try:
            if name in self.remote_servers:
                self.current_server = self.remote_servers[name]
                self._send_log(f"opened '{name}' with properties:\n{vars(self.current_server)}")
                return self.current_server
        except AttributeError:
            pass


        if self.current_server:
            crash_info = (self.current_server.name, self.current_server.crash_log)
        else:
            crash_info = (None, None)

        del self.current_server
        self.current_server = None

        # Check if server is running
        if name in self.running_servers.keys():
            self.current_server = self.running_servers[name]
        else:
            self.current_server = ServerObject(self, name)
            if crash_info[0] == name:
                self.current_server.crash_log = crash_info[1]

        self._send_log(f"opened '{name}' with properties:\n{vars(self.current_server)}")
        return self.current_server

    # This method is server-side for when a client opens a local server remotely
    # Sets self.remote_server to selected ServerObject
    def open_remote_server(self, host: str, name: str):
        try:
            if self.current_server.name == name:
                self.remote_servers[host] = self.current_server

                self._send_log(f"remote '{host}' opened '{name}' with properties:\n{vars(self.remote_servers[host])}")
                return host in self.remote_servers

        except AttributeError:
            pass

        if host in self.remote_servers:
            crash_info = (self.remote_servers[host].name, self.remote_servers[host].crash_log)
            del self.remote_servers[host]
        else:
            crash_info = (None, None)

        # Check if server is running
        if name in self.running_servers.keys():
            self.remote_servers[host] = self.running_servers[name]

        else:
            # Check if server is already open on another host
            for server_obj in self.remote_servers.values():
                if name == server_obj.name:
                    self.remote_servers[host] = server_obj
                    break

            # Initialize a new server object
            else:
                self.remote_servers[host] = ServerObject(self, name)
                if crash_info[0] == name:
                    self.remote_servers[host].crash_log = crash_info[1]

        self._send_log(f"remote '{host}' opened '{name}' with properties:\n{vars(self.remote_servers[host])}")
        return host in self.remote_servers

    # Reloads self.current_server
    def reload_server(self):
        if self.current_server:
            return self.open_server(self.current_server.name)



    #  ----------------------------------------- Telepath Management ---------------------------------------------------

    # From the perspective of a client, this opens a server on a remote Telepath host in 'self.remote_servers'
    def _init_telepathy(self, telepath_data: dict):

        # Make sure the server isn't already open
        if self.current_server and self.current_server._telepath_data:
            new = f"{telepath_data['host']}/{telepath_data['name']}"
            old = f"{self.current_server._telepath_data['host']}/{self.current_server._telepath_data['name']}"
            if new == old: return self.current_server

        self.current_server = telepath.RemoteServerObject(self, telepath_data)
        return self.current_server

    # Checks which remote servers are alive (if this instance is a Telepath client)
    def check_telepath_servers(self):
        if not self.telepath_servers:
            return

        new_server_list = {}
        self._send_log(f"attempting to connect to {len(self.telepath_servers)} Telepath server(s)...", 'info')

        def check_server(host, data):
            url = f'http://{host}:{data["port"]}/telepath/check_status'
            try:
                # Check if remote server is online
                if requests.get(url, timeout=0.5).json():
                    # Attempt to log in
                    login_data = api_manager.login(host, data["port"])
                    if login_data:
                        # Update values if host exists
                        if host in self.telepath_servers:
                            for k, v in login_data.items():
                                if v:
                                    self.telepath_servers[host][k] = v
                        else:
                            self.telepath_servers[host] = login_data

                        return host, deepcopy(data)
            except Exception:
                pass
            return None

        # Use ThreadPoolExecutor to check multiple servers concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_host = {executor.submit(check_server, host, data): host for host, data in self.telepath_servers.items()}

            for future in as_completed(future_to_host):
                result = future.result()
                if result:
                    host, data = result
                    new_server_list[host] = data

        # Update the online servers list
        self.online_telepath_servers = new_server_list
        self.write_telepath_servers(overwrite=True)
        self._send_log(f"successfully connected to {len(self.online_telepath_servers)} Telepath server(s)", 'info')
        return new_server_list

    # Retrieves remote update list
    def reload_telepath_updates(self, host_data=None):
        # Load remote update list
        if host_data:
            self.remote_update_list[host_data['host']] = get_remote_var('server_manager.update_list', host_data)

        else:
            for host, instance in self.telepath_servers.items():
                host_data = {'host': host, 'port': instance['port']}
                self.remote_update_list[host] = get_remote_var('server_manager.update_list', host_data)

    # Returns and updates remote update list
    def get_telepath_update(self, host_data: dict, server_name: str):
        self.reload_telepath_updates(host_data)
        if host_data['host'] not in self.remote_update_list:
            self.remote_update_list[host_data['host']] = {}
        if server_name in self.remote_update_list[host_data['host']]:
            return self.remote_update_list[host_data['host']][server_name]
        return {}

    # The below methods modify servers from 'telepath-servers.json'
    def load_telepath_servers(self):
        # Possibly run this function before auto-mcs boots, and wait for it to finish loading before showing the UI
        if os.path.exists(telepathFile):
            with open(telepathFile, 'r') as f:
                try:
                    self.telepath_servers = json.loads(f.read())
                except json.decoder.JSONDecodeError:
                    pass

        return self.telepath_servers
    def write_telepath_servers(self, instance=None, overwrite=False):
        if not overwrite:
            self.telepath_servers = self.load_telepath_servers()

        if instance:
            self.telepath_servers[instance['host']] = instance
            del instance['host']

        folder_check(telepathDir)
        with open(telepathFile, 'w+') as f:
            f.write(json.dumps(self.telepath_servers))
        return self.telepath_servers
    def add_telepath_server(self, instance: dict):
        if not instance['nickname']:
            instance['nickname'] = format_nickname(instance['hostname'])

        self._send_log(f'added a new Telepath server:\n{instance}')
        self.write_telepath_servers(instance)
        self.check_telepath_servers()
    def remove_telepath_server(self, instance: dict):
        if instance['host'] in self.telepath_servers:
            del self.telepath_servers[instance['host']]

        self._send_log(f'removed a Telepath server:\n{instance}')
        self.write_telepath_servers(overwrite=True)
        self.check_telepath_servers()
    def rename_telepath_server(self, instance: dict, new_name: str):
        new_name = format_nickname(new_name)
        instance['nickname'] = new_name
        self.telepath_servers[instance['host']]['nickname'] = new_name
        self.telepath_servers[instance['host']]['display-name'] = new_name

        self._send_log(f"renamed a Telepath server to '{new_name}':\n{instance}")
        self.write_telepath_servers(overwrite=True)



# --------------------------------------------- Utility Functions ------------------------------------------------------

# From kivy.utils (Kivy can't be imported in the backend)
def escape_markup(text):
    '''
    Escape markup characters found in the text. Intended to be used when markup
    text is activated on the Label::

        untrusted_text = escape_markup('Look at the example [1]')
        text = '[color=ff0000]' + untrusted_text + '[/color]'
        w = Label(text=text, markup=True)

    .. versionadded:: 1.3.0
    '''
    return text.replace('&', '&amp;').replace('[', '&bl;').replace(']', '&br;')


# Returns general server type from specific type
def server_type(specific_type: str):
    if specific_type.lower().strip() in ['craftbukkit', 'bukkit', 'spigot', 'paper', 'purpur']:
        return 'bukkit'
    else: return specific_type.lower().strip()


# Returns absolute file path of server directories
def server_path(server_name: str, *args):
    path_name = os.path.join(serverDir, server_name, *args)
    return path_name if os.path.exists(path_name) else None


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

                except NoOptionError:
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


# Returns active IP address of 'name'
# > assigned from UI to update IP text on screens
refresh_ips: callable = None
def get_current_ip(name: str, proxy=False):
    private_ip    = ""
    original_port = "25565"
    updated_port  = ""
    final_addr    = {}

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
        if constants.server_manager.running_servers:
            bad_ports = [int(server.run_data['network']['address']['port']) for server in constants.server_manager.running_servers.values() if server.name != name]

        new_port = int(original_port)
        conflict = False

        for port in bad_ports:
            if new_port == port:
                if new_port > 50000: new_port -= 1
                else:                new_port += 1
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

                    # If public IP isn't defined, retrieve it from API
                    if constants.public_ip: new_ip = constants.public_ip
                    else:
                        try: new_ip = requests.get('http://api.ipify.org', timeout=5).content.decode('utf-8', errors='ignore')
                        except: new_ip = ""

                    # Check if port is open
                    if new_ip and 'bad' not in new_ip.lower():
                        constants.public_ip = new_ip

                        # Assign public IP to current running server
                        if constants.server_manager.running_servers:
                            if updated_port: final_port = int(updated_port)
                            else:            final_port = int(original_port)

                            # Make a few attempts to verify WAN connection
                            port_check = False
                            for attempt in range(10):
                                port_check = check_port(constants.public_ip, final_port, timeout=5)
                                if port_check: break

                            if port_check:
                                try:
                                    constants.server_manager.running_servers[server_name].run_data['network']['address']['ip'] = constants.public_ip
                                    constants.server_manager.running_servers[server_name].run_data['network']['public_ip'] = constants.public_ip

                                    # Update screen info
                                    if refresh_ips: refresh_ips(name)

                                except KeyError: pass

                ip_timer = Timer(1, functools.partial(get_public_ip, name))
                ip_timer.daemon = True
                ip_timer.start()


    # Format network info
    if private_ip:       final_addr['ip'] = private_ip
    else:                final_addr['ip'] = '127.0.0.1'

    if updated_port:     final_addr['port'] = updated_port
    elif original_port:  final_addr['port'] = original_port
    else:                final_addr['port'] = "25565"


    network_dict = {
        'address': final_addr,
        'public_ip': constants.public_ip if constants.public_ip else None,
        'private_ip': private_ip if private_ip else '127.0.0.1',
        'original_port': original_port if updated_port else None
    }

    return network_dict



# ---------------------------------------------- Server Functions ------------------------------------------------------

# Toggles favorite status in ServerManager
def toggle_favorite(server_name: str):
    config_file = server_config(server_name)
    config_file.set('general', 'isFavorite', ('false' if config_file.get('general', 'isFavorite') == 'true' else 'true'))
    server_config(server_name, config_file)

    is_favorite = bool(config_file.get('general', 'isFavorite') == 'true')
    action = 'marked' if is_favorite else 'unmarked'
    send_log('toggle_favorite', f"'server_name' is now {action} as favorite", 'info')
    return is_favorite


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
                    java_override = constants.java_executable['modern']
                elif override == '<java17>':
                    java_override = constants.java_executable['lts']
                elif override == '<java8>':
                    java_override = constants.java_executable['legacy']

            # Build start flags
            start_flags = f' {custom_flags}'


        # Do some schennanies for NeoForge
        if properties['type'] == 'neoforge':
            if java_override:
                java = java_override
            else:
                java = constants.java_executable['modern']
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
                    java = constants.java_executable["lts"] if version_check(properties['version'], '<', '1.19.3') else constants.java_executable['modern']
                version_list = [os.path.basename(file) for file in glob(os.path.join("libraries", "net", "minecraftforge", "forge", f"1.{math.floor(float(properties['version'].replace('1.', '', 1)))}*")) if os.listdir(file)]
                arg_file = f"libraries/net/minecraftforge/forge/{version_list[-1]}/{'win_args.txt' if os_name == 'windows' else 'unix_args.txt'}"
                script = f'"{java}" -Xmx{ram}G -Xms{int(round(ram/2))}G {start_flags} -Dlog4j2.formatMsgNoLookups=true @{arg_file} nogui'

            # 1.6 to 1.16
            elif version_check(properties['version'], ">=", "1.6") and version_check(properties['version'], "<", "1.17"):
                if java_override:
                    java = java_override
                else:
                    java = constants.java_executable["legacy"]
                script = f'"{java}" -Xmx{ram}G -Xms{int(round(ram/2))}G {start_flags} -Dlog4j2.formatMsgNoLookups=true -jar server.jar nogui'


        # Everything else
        else:
            # Make sure this works non-spigot versions
            if java_override:
                java = java_override
            else:
                java = constants.java_executable["legacy"] if version_check(properties['version'], '<','1.17') else constants.java_executable['lts'] if version_check(properties['version'], '<', '1.19.3') else constants.java_executable['modern']

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


# Recursively gathers all config files with a specific depth (default 3)
# Returns {"dir1": ['match1', 'match2', 'match3', ...]}
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
    debug_only = f':\n{files}' if constants.debug else ''
    if files: send_log('gather_config_files', f"found {len(files)} config file(s) in '{name}'{debug_only}", 'info')
    else:     send_log('gather_config_files', f"no config files were found in '{name}'", 'info')

    return files


# auto-mcs.ini config file function
# write_object is the configparser object returned from this function
def server_config(server_name: str, write_object: ConfigParser = None, config_path: str = None):
    from source.core.server.foundry import latestMC

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
            config = ConfigParser(allow_no_value=True, comment_prefixes=';')
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
        config = ConfigParser(allow_no_value=True, comment_prefixes=';')
        config.optionxform = str

        config.add_section('general')
        config.set('general', "; DON'T MODIFY THE CONTENTS OF THIS FILE")
        config.set('general', 'serverName', properties['name'])
        config.set('general', 'serverVersion', properties['version'])
        if properties['build']:
            config.set('general', 'serverBuild', str(properties['build']))
        config.set('general', 'serverType', properties['type'])
        config.set('general', 'isFavorite', 'false')
        config.set('general', 'allocatedMemory', 'auto')
        try:    config.set('general', 'enableGeyser', str(properties['server_settings']['geyser_support']).lower())
        except: config.set('general', 'enableGeyser', 'false')
        try:    config.set('general', 'enableProxy', str(properties['server_settings']['enable_proxy']).lower())
        except: config.set('general', 'enableProxy', 'false')
        try:    config.set('general', 'customFlags', ' '.join(properties['launch_flags']))
        except: pass

        # Ensure non-mrpack modpacks aren't updated automatically
        if modpack:
            config.set('general', 'isModpack', str(modpack))
            value = 'prompt' if str(modpack) == 'mrpack' else 'false'
            config.set('general', 'updateAuto', value)

        else: config.set('general', 'updateAuto', 'prompt')


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


# Fixes empty 'server.properties' file, and updates EULA date check
def fix_empty_properties(name):
    from source.core.server.foundry import generate_eula

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


# Updates a world in a server
def update_world(path: str, new_type='default', new_seed='', telepath_data={}):
    if telepath_data:
        server_obj = constants.server_manager.remote_servers[telepath_data['host']]

        # Report to telepath logger
        api_manager.logger._report(f'main.update_world', extra_data=f'Changing world: {path}', server_name=server_obj.name)

    else: server_obj = constants.server_manager.current_server

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


# Updates the server icon with a new image
# Returns: [bool: success, str: reason]
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



# -------------------------------------------- Telepath Functions ------------------------------------------------------

# Clones a server with support for Telepath
def clone_server(server_obj: object or str, progress_func=None, host=None, *args):
    from source.core.server.foundry import (
        new_server_info, import_data, scan_import, finalize_import
    )

    if server_obj == '$remote':
        source_data = None
        destination_data = None
        server_obj = constants.server_manager.remote_servers[host]

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


# Reconstruct remote API config dict to a local configparser object
def reconstruct_config(remote_config: dict or ConfigParser, to_dict=False):
    if to_dict:
        if isinstance(remote_config, dict): return remote_config
        else: return {section: dict(remote_config.items(section)) for section in remote_config.sections()}

    else:
        config = ConfigParser(allow_no_value=True, comment_prefixes=';')
        config.optionxform = str
        for section, values in remote_config.items():
            if section == 'DEFAULT':
                continue

            config.add_section(section)
            for key, value in values.items():
                config.set(section, key, value)
    return config


# Compatibility to cache server icon with Telepath
def get_server_icon(server_name: str, telepath_data: dict, overwrite=False):
    if not (app_online and server_name):
        return None

    try:
        name = f"{telepath_data['host'].replace('/', '+')}+{server_name}"
        icon_cache = os.path.join(cacheDir, 'icons')
        final_path = os.path.join(icon_cache, name)

        if os.path.exists(final_path) and not overwrite:
            age = abs(dt.today().day - dt.fromtimestamp(os.stat(final_path).st_mtime).day)
            if age < 3: return final_path
            else: os.remove(final_path)

        elif not check_free_space():
            return None

        folder_check(icon_cache)
        if os.path.exists(final_path) and overwrite:
            os.remove(final_path)

        # Ensure that the server actually has an icon
        try:
            telepath_download(telepath_data, telepath_data['icon-path'], icon_cache, rename=name)
        except TypeError:
            send_log('update_server_icon', f"'{telepath_data['host']}/{server_name}' doesn't have a server icon")
            return None


        if os.path.exists(final_path): return final_path
        else: return None

    except Exception as e:
        send_log('update_server_icon', f"error retrieving icon for '{telepath_data['host']}/{server_name}': {format_traceback(e)}", 'error')
        return None



# ---------------------------------------------- Usage Examples --------------------------------------------------------

# sm = ServerManager()
# sm.open_server("booger squad")
# sm.reload_server()
