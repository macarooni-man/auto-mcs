from concurrent.futures import ThreadPoolExecutor, as_completed
from subprocess import Popen, PIPE, run
from datetime import datetime as dt
from threading import Timer
from copy import deepcopy
from glob import glob
import functools
import threading
import requests
import psutil
import ctypes
import time
import json
import os
import re

from acl import AclManager, get_uuid, check_online
from backup import BackupManager
from addons import AddonManager
import constants
import telepath
import amscript
import backup


# Auto-MCS Server Manager API
# ----------------------------------------------- Server Objects -------------------------------------------------------

# Instantiate class with "server_name" (case-sensitive)
# Big boy mega server object
class ServerObject():

    def __init__(self, server_name: str):
        self._telepath_data = None
        self._view_name = server_name
        self._loop_clock = 0
        self._last_telepath_log = {}
        self._disconnected = False

        self.gamemode_dict = ['survival', 'creative', 'adventure', 'spectator']
        self.difficulty_dict = ['peaceful', 'easy', 'normal', 'hard', 'hardcore']


        self.name = server_name
        self.server_path = constants.server_path(server_name)
        self.last_modified = os.path.getmtime(self.server_path)
        self.server_icon = constants.server_path(self.name, 'server-icon.png')
        self.running = False
        self.restart_flag = False
        self.custom_flags = ''
        self.is_modpack = ''
        self.crash_log = None
        self.max_log_size = 2000
        self.run_data = {}
        self.console_filter = 'everything'
        self.viewed_notifs = {}
        self.taskbar = None
        self._hash = constants.gen_rstring(8)


        # Server files
        generate_properties = False
        if not os.path.join(self.server_path, 'server.properties'):
            generate_properties = True

        self.server_properties = constants.server_properties(server_name)
        if len(self.server_properties) < 10:
            generate_properties = True

        # Repair properties if empty or broken
        if generate_properties:
            constants.fix_empty_properties(self.name)
            self.server_properties = constants.server_properties(server_name)

        self.config_file = constants.server_config(server_name)
        self.config_paths = None
        self.properties_hash = self._get_properties_hash()


        # Server properties
        self.favorite = self.config_file.get("general", "isFavorite").lower() == 'true'
        self.auto_update = str(self.config_file.get("general", "updateAuto").lower())
        self.dedicated_ram = str(self.config_file.get("general", "allocatedMemory").lower())
        self.type = self.config_file.get("general", "serverType").lower()
        self.version = self.config_file.get("general", "serverVersion").lower()
        self.build = None
        try:
            self.console_filter = self.config_file.get("general", "consoleFilter")
        except:
            pass
        try:
            self.viewed_notifs = json.loads(self.config_file.get("general", "viewedNotifs"))
        except:
            pass
        try:
            if self.config_file.get("general", "serverBuild"):
                self.build = self.config_file.get("general", "serverBuild").lower()
        except:
            pass
        try:
            if self.config_file.get("general", "customFlags"):
                self.custom_flags = self.config_file.get("general", "customFlags").strip()
        except:
            self.custom_flags = ''
        try:
            if self.config_file.get("general", "isModpack"):
                modpack = self.config_file.get("general", "isModpack").lower()
                if modpack:
                    self.is_modpack = 'zip' if modpack != 'mrpack' else 'mrpack'
        except:
            self.is_modpack = ''
        try:
            if self.config_file.get("general", "enableProxy"):
                self.proxy_enabled = self.config_file.get("general", "enableProxy").lower() == 'true'
        except:
            self.proxy_enabled = False
        try:
            if self.config_file.get("general", "enableGeyser"):
                self.geyser_enabled = self.config_file.get("general", "enableGeyser").lower() == 'true'
        except:
            self.geyser_enabled = False
            # Check if Geyser actually exists
            def thread(*a):
                geyser = 0
                if constants.version_check(self.version, ">=", "1.13.2") and self.type.lower() in ['spigot', 'paper', 'purpur', 'fabric']:
                    while not self.addon:
                        time.sleep(0.2)
                    addon_list = self.addon.return_single_list()
                    for addon in addon_list:
                        if (addon.name.startswith('Geyser') or addon.name == 'floodgate') and addon.author == 'GeyserMC':
                            geyser += 1
                            if geyser == 2:
                                break

                self.config_file.set("general", "enableGeyser", str(geyser >= 2).lower())
                constants.server_config(self.name, self.config_file)
            geyser_timer = threading.Timer(0.1, thread)
            geyser_timer.daemon = True
            geyser_timer.start()


        # Check update properties for UI stuff
        self.update_string = ''
        if self.is_modpack:
            if constants.update_list[self.name]['updateString'] and self.is_modpack == 'mrpack':
                self.update_string = constants.update_list[self.name]['updateString']
        else:
            self.update_string = str(constants.latestMC[self.type]) if constants.version_check(constants.latestMC[self.type], '>', self.version) else ''
            if not self.update_string and self.build:
                self.update_string = ('b-' + str(constants.latestMC['builds'][self.type])) if (tuple(map(int, (str(constants.latestMC['builds'][self.type]).split(".")))) > tuple(map(int, (str(self.build).split("."))))) else ""


        if self.update_string:
            self._view_notif('settings', viewed='')
        else:
            self._view_notif('settings', False)

        try:
            self.world = self.server_properties['level-name']
        except KeyError:
            self.world = None
        try:
            self.ip = self.server_properties['server-ip']
        except KeyError:
            self.ip = None
        try:
            self.port = self.server_properties['server-port']
        except KeyError:
            self.port = None
        try:
            self.motd = self.server_properties['motd']
        except KeyError:
            self.motd = None


        try:
            self.gamemode = self.gamemode_dict[int(float(self.server_properties['gamemode']))] if not self.server_properties['hardcore'] else 'hardcore'
            self.difficulty = self.difficulty_dict[int(float(self.server_properties['difficulty']))]
        except ValueError:
            self.gamemode = self.server_properties['gamemode'] if not self.server_properties['hardcore'] else 'hardcore'
            self.difficulty = self.server_properties['difficulty']
        except KeyError:
            self.gamemode = None
            self.difficulty = None


        # Special sub-objects, and defer loading in the background
        # Make sure that menus wait until objects are fully loaded before opening
        self.backup = None
        self.addon = None
        self.acl = None
        self.script_manager = None
        self.script_object = None

        def load_backup(*args):
            self.backup = BackupManager(server_name)
        Timer(0, load_backup).start()
        def load_addon(*args):
            self.addon = AddonManager(server_name)
            if 'add-ons' in self.viewed_notifs:
                if self.viewed_notifs['add-ons'] == 'update':
                    self.addon.update_required = True
            self.addon.check_for_updates()
            if self.addon.update_required and len(self.addon.return_single_list()):
                self._view_notif('add-ons', viewed='')
        Timer(0, load_addon).start()
        def load_acl(*args):
            self.acl = AclManager(server_name)
        Timer(0, load_acl).start()
        def load_scriptmgr(*args):
            self.script_manager = amscript.ScriptManager(self.name)
        Timer(0, load_scriptmgr).start()
        def load_config_paths(*args):
            self.reload_config_paths()
        Timer(0, load_config_paths).start()

        if not constants.headless:
            print(f"[INFO] [auto-mcs] Server Manager: Loaded '{server_name}'")

    # Returns the value of the requested attribute (for remote)
    def _sync_attr(self, name):
        if name == 'run_data':
            return self._telepath_run_data()

        data = constants.sync_attr(self, name)

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
        try:
            return self in constants.server_manager.remote_servers.values()
        except AttributeError:
            pass
        except RecursionError:
            pass
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
        return {'addon': bool(self.addon), 'backup': bool(self.backup), 'acl': bool(self.backup), 'script_manager': bool(self.script_manager)}

    # Checks if a user is online
    def user_online(self, user: str):
        return check_online(user)


    # Telepath-compatible methods for interacting with the proxy
    def proxy_installed(self):
        return constants.playit._check_agent()
    def install_proxy(self):
        return constants.playit._install_agent()
    def enable_proxy(self, enabled: bool):
        self.config_file.set("general", "enableProxy", str(enabled).lower())
        self.write_config()
        self.proxy_enabled = enabled

    # Retrieve a data structure of all config files in the server
    def reload_config_paths(self):
        self.config_paths = constants.gather_config_files(self.name)
        return self.config_paths

    # Reloads server information from static files
    def reload_config(self, reload_objects=False):

        # Server files
        self.server_icon = constants.server_path(self.name, 'server-icon.png')
        self.config_file = constants.server_config(self.name)
        self.server_properties = constants.server_properties(self.name)
        self.properties_hash = self._get_properties_hash()

        # Server properties
        self.favorite = self.config_file.get("general", "isFavorite").lower() == 'true'
        self.auto_update = str(self.config_file.get("general", "updateAuto").lower())
        self.dedicated_ram = str(self.config_file.get("general", "allocatedMemory").lower())
        self.type = self.config_file.get("general", "serverType").lower()
        self.version = self.config_file.get("general", "serverVersion").lower()
        self.build = None
        try:
            self.console_filter = self.config_file.get("general", "consoleFilter")
        except:
            pass
        try:
            self.viewed_notifs = json.loads(self.config_file.get("general", "viewedNotifs"))
        except:
            pass
        try:
            if self.config_file.get("general", "serverBuild"):
                self.build = self.config_file.get("general", "serverBuild").lower()
        except:
            pass
        try:
            if self.config_file.get("general", "customFlags"):
                self.custom_flags = self.config_file.get("general", "customFlags").strip()
        except:
            self.custom_flags = ''
        try:
            if self.config_file.get("general", "isModpack"):
                modpack = self.config_file.get("general", "isModpack").lower()
                if modpack:
                    self.is_modpack = 'zip' if modpack != 'mrpack' else 'mrpack'
        except:
            self.is_modpack = ''
        try:
            if self.config_file.get("general", "enableProxy"):
                self.proxy_enabled = self.config_file.get("general", "enableProxy").lower() == 'true'
        except:
            self.proxy_enabled = False
        try:
            if self.config_file.get("general", "enableGeyser"):
                self.geyser_enabled = self.config_file.get("general", "enableGeyser").lower() == 'true'
        except:
            self.geyser_enabled = False


        # Check update properties for UI stuff
        self.update_string = ''
        if self.is_modpack:
            if constants.update_list[self.name]['updateString'] and self.is_modpack == 'mrpack':
                self.update_string = constants.update_list[self.name]['updateString']
        else:
            self.update_string = str(constants.latestMC[self.type]) if constants.version_check(constants.latestMC[self.type], '>', self.version) else ''
            if not self.update_string and self.build:
                self.update_string = ('b-' + str(constants.latestMC['builds'][self.type])) if (tuple(map(int, (str(constants.latestMC['builds'][self.type]).split(".")))) > tuple(map(int, (str(self.build).split("."))))) else ""


        if self.update_string:
            self._view_notif('settings', viewed='')
        else:
            self._view_notif('settings', False)

        try:
            self.world = self.server_properties['level-name']
        except KeyError:
            self.world = None
        try:
            self.ip = self.server_properties['server-ip']
        except KeyError:
            self.ip = None
        try:
            self.port = self.server_properties['server-port']
        except KeyError:
            self.port = None
        try:
            self.motd = self.server_properties['motd']
        except KeyError:
            self.motd = None


        try:
            self.gamemode = self.gamemode_dict[int(float(self.server_properties['gamemode']))] if not self.server_properties['hardcore'] else 'hardcore'
            self.difficulty = self.difficulty_dict[int(float(self.server_properties['difficulty']))]
        except ValueError:
            self.gamemode = self.server_properties['gamemode'] if not self.server_properties['hardcore'] else 'hardcore'
            self.difficulty = self.server_properties['difficulty']
        except KeyError:
            self.gamemode = None
            self.difficulty = None

        self.server_path = constants.server_path(self.name)
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
                self.script_manager = amscript.ScriptManager(self.name)
            Timer(0, load_scriptmgr).start()
            def load_config_paths(*args):
                self.reload_config_paths()
            Timer(0, load_config_paths).start()

    # Returns a dict formatted like 'new_server_info'
    def properties_dict(self):
        properties = {
            "_hash": constants.gen_rstring(8),

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

    # Writes changes to 'server.properties' and 'auto-mcs.ini'
    def write_config(self, remote_data={}):
        if remote_data:
            self.config_file = constants.reconstruct_config(remote_data['config_file'])
            self.server_properties = remote_data['server_properties']

        constants.server_config(self.name, self.config_file)
        constants.server_properties(self.name, self.server_properties)

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
                    date = dt.strptime(string, "%H:%M:%S").strftime(constants.fmt_date("%#I:%M:%S %p")).rjust(11)
                except ValueError:
                    date = ''
                return date

            def format_color(code, *args):
                if 'r' not in code:
                    formatted_code = f'[color={constants.color_table[code]}]'
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
                        date_label = message_date_obj.strftime(constants.fmt_date("%#I:%M:%S %p")).rjust(11)

                # Old log formatting (server.log)
                else:
                    message = line.split("] ", 1)[-1].strip()
                    try:
                        date_str = line.split(" ", 1)[1].split("[", 1)[0].strip()
                        date_label = format_time(date_str)
                    except IndexError:
                        date_label = message_date_obj.strftime(constants.fmt_date("%#I:%M:%S %p")).rjust(11)

                # If date_label is missing, it may be formatted differently
                if not date_label:
                    date_label = message_date_obj.strftime(constants.fmt_date("%#I:%M:%S %p")).rjust(11)

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
                        self.run_data['player-list'][user]['date'] = message_date_obj
                        self.run_data['player-list'][user]['logged-in'] = False
                        self.acl._process_log(self.run_data['player-list'][user])

                        if self.script_object.enabled:
                            return functools.partial(self.script_object.leave_event, self.run_data['player-list'][user])

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
                try:
                    log_line, event = format_log(log_line)
                except Exception as e:
                    if constants.debug:
                        print(e)
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
                    self.run_data['log'].append({'text': (dt.now().strftime(constants.fmt_date("%#I:%M:%S %p")).rjust(11), 'EXEC', f"Console issued server command: {new_cmd}", (1, 0.298, 0.6, 1))})

                # Send script event
                if self.script_object.enabled and not script:
                    # Check if command is in user command alias list, and if not don't send to server
                    self.script_object.message_event({'user': f'#{self._hash}', 'content': new_cmd})

                # Send to server if it doesn't start with !
                if not cmd.startswith("!"):
                    try:
                        # Format encoding per OS
                        if constants.os_name == 'windows':
                            command = f"{cmd}\r\n".encode('utf-8', errors='ignore').replace(b'\xc2\xa7', b'\xa7')
                        else:
                            command = f"{cmd}\r\n".encode('utf-8', errors='ignore')

                        self.run_data['process'].stdin.write(command)
                        self.run_data['process'].stdin.flush()
                    except:
                        if constants.debug:
                            print("Error: Command sent after process shutdown")

    # Launch server, or reconnect to background server
    def launch(self, return_telepath=False):

        if not self.running:

            self.running = True
            self.crash_log = None
            constants.java_check()

            # Attempt to update first
            if self.auto_update == 'true' and constants.app_online:
                self.auto_update_func()

            script_path = constants.generate_run_script(self.properties_dict(), custom_flags=self.custom_flags, no_flags=(not self.custom_flags and self.is_modpack))

            if not self.restart_flag:
                self.run_data['launch-time'] = None
                self.run_data['player-list'] = {}
                self.run_data['network'] = {}
                self.run_data['log'] = [{'text': (dt.now().strftime(constants.fmt_date("%#I:%M:%S %p")).rjust(11), 'INIT', f"Launching '{self.name}', please wait...", (0.7,0.7,0.7,1))}]
                self.run_data['process-hooks'] = []
                self.run_data['close-hooks'] = [self.auto_backup_func]
                self.run_data['console-panel'] = None
                self.run_data['performance-panel'] = None
                self.run_data['command-history'] = []
                self.run_data['playit-tunnel'] = None
                self.run_data['entitydata-cache'] = {}
            else:
                self.run_data['log'].append({'text': (dt.now().strftime(constants.fmt_date("%#I:%M:%S %p")).rjust(11), 'INIT', f"Restarting '{self.name}', please wait...", (0.7, 0.7, 0.7, 1))})
                if self.run_data['console-panel'] and not constants.headless:
                    self.run_data['console-panel'].toggle_deadlock(False)

            if self.custom_flags:
                self.run_data['log'].append({'text': (dt.now().strftime(constants.fmt_date("%#I:%M:%S %p")).rjust(11), 'INIT', f"Using launch flags: '{self.custom_flags}'", (0.7, 0.7, 0.7, 1))})
                # Prevent bugs when closing immediately due to bad flags
                time.sleep(1)

            self.run_data['performance'] = {'ram': 0, 'cpu': 0, 'uptime': '00:00:00:00', 'current-players': []}
            self.run_data['deadlocked'] = False

            # Run data hashes to check for configuration changes post launch
            self.run_data['properties-hash'] = self._get_properties_hash()
            self.run_data['advanced-hash'] = self._get_advanced_hash()
            self.run_data['addon-hash'] = None
            if self.addon:
                self.run_data['addon-hash'] = deepcopy(self.addon._addon_hash)
            self.run_data['script-hash'] = deepcopy(self.script_manager._script_hash)

            # Write Geyser config if it doesn't exist
            if self.geyser_enabled:
                constants.write_geyser_config(self)

            # Open server script and attempt to launch
            with open(script_path, 'r') as f:
                script_content = f.read()
                firewall_block = False

                # On Windows, prompt to allow Java rule with netsh & UAC
                if constants.os_name == "windows":

                    # Check if Windows Firewall is enabled
                    if "OFF" not in str(run('netsh advfirewall show allprofiles | findstr State', shell=True, stdout=PIPE, stderr=PIPE).stdout):
                        exec_type = 'legacy' if constants.java_executable['legacy'] in script_content else 'modern' if constants.java_executable['modern'] in script_content else 'lts'
                        if constants.run_proc(f'netsh advfirewall firewall show rule name="auto-mcs java {exec_type}"') == 1:
                            net_test = ctypes.windll.shell32.ShellExecuteW(None, "runas", 'netsh', f'advfirewall firewall add rule name="auto-mcs java {exec_type}" dir=in action=allow enable=yes program="{constants.java_executable[exec_type]}"', None, 0)
                            if net_test == 5:
                                self.run_data['log'].append({'text': (dt.now().strftime(constants.fmt_date("%#I:%M:%S %p")).rjust(11), 'WARN', f"Java is blocked by Windows Firewall: can't accept external connections", (1, 0.659, 0.42, 1))})
                                firewall_block = True

                # Check for networking conflicts and current IP
                self.run_data['network'] = constants.get_current_ip(self.name, proxy=self.proxy_enabled)

                # Launch playit if proxy is enabled
                if self.proxy_enabled and constants.app_online and self.proxy_installed():
                    try:
                        self.run_data['playit-tunnel'] = constants.playit.start_tunnel(self)
                        hostname = self.run_data['playit-tunnel'].hostname
                        self.run_data['network']['address']['ip'] = hostname
                        self.run_data['network']['public_ip'] = hostname
                        self.send_log(f"Initialized playit connection '{hostname}'", 'success')
                    except:
                        self.send_log(f"The playit service is currently unavailable", 'warning')
                        self.run_data['playit-tunnel'] = None

                # If port was changed, use that instead
                if self.run_data['network']['original_port']:
                    self.run_data['log'].append({'text': (dt.now().strftime(constants.fmt_date("%#I:%M:%S %p")).rjust(11), 'WARN', f"Networking conflict detected: temporarily using '*:{self.run_data['network']['address']['port']}'", (1, 0.659, 0.42, 1))})

                # Run server
                self.run_data['process'] = Popen(script_content, stdout=PIPE, stdin=PIPE, stderr=PIPE, cwd=self.server_path, shell=True)

            self.run_data['pid'] = self.run_data['process'].pid
            self.run_data['send-command'] = self.send_command



            # ----------------------------------------------------------------------------------------------------------
            # Main server process loop, handles reading output, hooks, and crash detection
            def process_thread(*args):
                if constants.version_check(self.version, '<', '1.7'):
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
                        if constants.version_check(self.version, '<', '1.7'):
                            if "[STDERR] ".encode() in line:
                                error_list.append(line.decode().split("[STDERR] ")[1])
                                continue

                        self.update_log(line)

                    except Exception as e:
                        if constants.debug:
                            print(f'Failed to process line: {e}')

                    fail_counter = 0 if line else (fail_counter + 1)

                    # Close wrapper if server is closed
                    if not self.running or self.run_data['process'].poll() is not None or fail_counter > 25:


                        # Initially check for crashes
                        def get_latest_crash():
                            crash_log = None

                            # First, check if a recent crash-reports file exists
                            if constants.server_path(self.name, 'crash-reports'):
                                crash_log = sorted(glob(os.path.join(self.server_path, 'crash-reports', 'crash-*-server.*')), key=os.path.getmtime)
                                if crash_log:
                                    crash_log = crash_log[-1]
                                    if ((dt.now() - dt.fromtimestamp(os.path.getmtime(crash_log))).total_seconds() <= 30):
                                        crash_log = crash_log
                                    else:
                                        crash_log = None

                            # If crash report file does not exist, try to deduce what happened and make a new one
                            if not crash_log:

                                if constants.version_check(self.version, '<', '1.7'):
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
                                constants.folder_check(folder_path)

                                with open(crash_log, 'w+') as f:
                                    content = "---- Minecraft Crash Report ----\n"
                                    content += "// This report was generated by auto-mcs\n\n"
                                    content += f"Time: {dt.now().strftime(constants.fmt_date('%#m/%#d/%y, %#I:%M %p'))}\n"

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
                            self.run_data['log'].append({'text': (dt.now().strftime(constants.fmt_date("%#I:%M:%S %p")).rjust(11), 'INIT', f"'{self.name}' has stopped unexpectedly", (1,0.5,0.65,1))})
                        else:
                            self.run_data['log'].append({'text': (dt.now().strftime(constants.fmt_date("%#I:%M:%S %p")).rjust(11), 'INIT', f"'{self.name}' has stopped successfully", (0.7,0.7,0.7,1))})

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
                if constants.debug:
                    print(f'Terminating "{self.name}"')
                self.terminate()
                return

            # ----------------------------------------------------------------------------------------------------------



            self.run_data['thread'] = Timer(0, process_thread)
            self.run_data['thread'].daemon = True
            self.run_data['thread'].start()
            self.run_data['launch-time'] = dt.now()

            constants.server_manager.running_servers[self.name] = self
            self._start_performance_clock()


            # Add and delete temp file to update last modified time of server directory
            with open(os.path.join(self.server_path, 'session.mcs'), 'w+') as f:
                f.write(self.name)
            os.remove(os.path.join(self.server_path, 'session.mcs'))
            self.last_modified = os.path.getmtime(self.server_path)


            # Initialize ScriptObject
            try:
                self.script_object = amscript.ScriptObject(self)

                # Fire server start event
                if self.script_object.enabled:
                    self.script_object.construct()
                    self.script_object.start_event({'date': dt.now()})


                # If start-cmd.tmp exists, run every command in file (that is allowed by the command_whitelist)
                cmd_tmp = constants.server_path(self.name, constants.command_tmp)
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

        # Kill server process
        try:
            if self.run_data['process'].poll() is None:
                self.run_data['process'].kill()

        # Ignore errors stopping the process
        except:
            return

        # Reset port back to normal if required
        if self.run_data['network']['original_port']:
            lines = []
            with open(constants.server_path(self.name, "server.properties"), 'r') as f:
                lines = f.readlines()

            with open(constants.server_path(self.name, "server.properties"), 'w+') as f:
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
                    constants.playit.stop_tunnel(self)
            except KeyError:
                pass

            self.run_data.clear()
            self.running = False
            del constants.server_manager.running_servers[self.name]
            # print(constants.server_manager.running_servers)

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
        self.stop()

    # Stops the server
    def stop(self):
        self.silent_command('stop')

    # Forcefully ends the server process
    def kill(self):

        # Iterate over self and children to find Java process
        try:
            parent = psutil.Process(self.run_data['process'].pid)
        except:
            return False
        sys_mem = round(psutil.virtual_memory().total / 1048576, 2)

        # Windows
        if constants.os_name == "windows":
            children = parent.children(recursive=True)
            for proc in children:
                if proc.name() == "java.exe":
                    constants.run_proc(f"taskkill /f /pid {proc.pid}")
                    break

        # macOS
        elif constants.os_name == "macos":
            if parent.name() == "java":
                constants.run_proc(f"kill {parent.pid}")

        # Linux
        else:
            if parent.name() == "java":
                constants.run_proc(f"kill {parent.pid}")
            else:
                children = parent.children(recursive=True)
                for proc in children:
                    if proc.name() == "java":
                        constants.run_proc(f"kill {proc.pid}")
                        break


    # Checks if a server has closed, but hangs
    def check_for_deadlock(self):
        ip = self.run_data['network']['private_ip']
        port = int(self.run_data['network']['address']['port'])

        def check(*a):
            while self.running and constants.check_port(ip, port):
                time.sleep(1)

            # If after a delay the server is still running, it is likely deadlocked
            time.sleep(1)
            if self.running and self.name not in constants.backup_lock and not self.restart_flag:
                try:
                    # Delay if CPU usage is higher than expected
                    if self.run_data['performance']['cpu'] > 0.5:
                        time.sleep(15)
                    message = f"'{self.name}' is deadlocked, please kill it above to continue..."
                    self.run_data['deadlocked'] = True
                    if message != self.run_data['log'][-1]['text'][2]:
                        self.send_log(message, 'warning')
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
            if constants.os_name == "windows":
                children = parent.children(recursive=True)
                for proc in children:
                    if proc.name() == "java.exe":
                        perc_cpu = proc.cpu_percent(interval=interval)
                        perc_ram = round(proc.memory_info().private / 1048576, 2)
                        break

            # Get RSS of parent on macOS
            elif constants.os_name == "macos":
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
        self.config_file = constants.server_config(self.name)
        self.config_file.set("general", "allocatedMemory", new_value)
        self.dedicated_ram = new_value
        constants.server_config(self.name, self.config_file)

        return new_value

    # Sets automatic update configuration
    def enable_auto_update(self, enabled=True):
        new_value = str(enabled).lower()
        self.config_file = constants.server_config(self.name)
        self.config_file.set("general", "updateAuto", new_value)
        self.auto_update = new_value
        constants.server_config(self.name, self.config_file)

        return enabled

    # Updates custom flags
    def update_flags(self, flags):
        self.config_file = constants.server_config(self.name)
        self.config_file.set("general", "customFlags", flags.strip())
        self.custom_flags = flags.strip()
        constants.server_config(self.name, self.config_file)

    # Updates the server icon, deletes if "new_icon" is empty
    def update_icon(self, new_icon: str or False):
        data = constants.update_server_icon(self.name, new_icon)
        self.server_icon = constants.server_path(self.name, 'server-icon.png')
        return data

    # Updates console event filter in config
    # 'everything', 'errors', 'players', 'amscript'
    def change_filter(self, filter_type: str):
        self.config_file = constants.server_config(self.name)
        self.config_file.set("general", "consoleFilter", filter_type)
        constants.server_config(self.name, self.config_file)

    # Renames server
    def rename(self, new_name: str):
        if not self.running:
            original_name = self.name
            new_name = new_name.strip()

            # Change name in config
            self.config_file.set('general', 'serverName', new_name)
            self.write_config()

            # Rename persistent configuration for amscript
            # config_path = os.path.join(constants.configDir, 'amscript', 'pstconf')
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
            new_path = os.path.join(constants.applicationFolder, 'Servers', new_name)
            os.rename(self.server_path, new_path)
            self.server_path = new_path
            self.name = new_name

            # Reset server object properties
            backup.rename_backups(original_name, new_name)

            # Reset constants properties
            constants.generate_server_list()
            constants.make_update_list()

            # Reload properties
            self.reload_config(reload_objects=True)

    # Deletes server
    def delete(self):
        if not self.running:

            # Save a back-up of current server state
            while not self.backup:
                time.sleep(0.1)

            if constants.check_free_space():
                self.backup.save()

            # Delete server folder
            constants.safe_delete(self.server_path)
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

        elif self.auto_update == 'true' and constants.app_online:
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
            elif not constants.check_free_space():
                self.send_log("Skipping back-up due to insufficient free space", 'error')
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
            # Delete ScriptObject
            self.script_object.deconstruct()
            del self.script_object

            # Initialize ScriptObject
            self.script_object = amscript.ScriptObject(self)
            loaded_count, total_count = self.script_object.construct()
            self.script_object.start_event({'date': dt.now()})
            self.run_data['script-hash'] = deepcopy(self.script_manager._script_hash)

            return loaded_count, total_count
        else:
            return None, None

    # Returns data from amscript
    def get_ams_info(self):
        return {'version': constants.ams_version, 'installed': self.script_manager.installed_scripts}

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
                    formatted_code = f'[color={constants.color_table[code]}]'
                else:
                    formatted_code = '[/color]'
                return formatted_code

            date_label = ''
            type_label = ''
            main_label = ''
            type_color = ''

            if message:

                message_date_obj = dt.now()
                date_label = message_date_obj.strftime(constants.fmt_date("%#I:%M:%S %p")).rjust(11)

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
        if not text:
            return

        log_type = log_type if log_type in ('print', 'info', 'warning', 'error', 'success') else 'info'
        text = text.encode().replace(b'\xa7', b'\xc2\xa7').decode('utf-8', errors='ignore')

        # (date, type, log, color)
        def format_log(message, *args):

            def format_color(code, *args):
                if 'r' not in code:
                    formatted_code = f'[color={constants.color_table[code]}]'
                else:
                    formatted_code = '[/color]'
                return formatted_code

            date_label = ''
            type_label = ''
            main_label = ''
            type_color = ''

            if message:
                message_date_obj = dt.now()
                date_label = message_date_obj.strftime(constants.fmt_date("%#I:%M:%S %p")).rjust(11)

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
        if constants.version_check(self.version, '>=', '1.13'):
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

        server_so = amscript.ServerScriptObject(self)
        player_so = amscript.PlayerScriptObject(server_so, server_so._server_id)
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

        return suggestions

    # Shows taskbar notifications
    def _view_notif(self, name, add=True, viewed=''):
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
                if viewed:
                    self.viewed_notifs[name] = viewed
            else:
                self.viewed_notifs[name] = viewed

        elif (not add) and (name in self.viewed_notifs):
            del self.viewed_notifs[name]

        self.config_file = constants.server_config(self.name)
        self.config_file.set("general", "viewedNotifs", json.dumps(self.viewed_notifs))
        self.write_config()


# Low calorie version of ServerObject for a ViewClass in the Server Manager screen
class ViewObject():

    def __init__(self, server_name: str):

        self._telepath_data = None
        self.name = server_name
        self._view_name = server_name
        self.running = self.name in constants.server_manager.running_servers.keys()
        self.server_icon = constants.server_path(self.name, 'server-icon.png')

        if self.running:
            server_obj = constants.server_manager.running_servers[self.name]
            self.run_data = {'network': server_obj.run_data['network']}
            self.run_data['playit-tunnel'] = bool(server_obj.run_data['playit-tunnel'])
        else:
            self.run_data = {}


        # Server files
        self.config_file = constants.server_config(server_name)

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
            if constants.update_list[self.name]['updateString'] and self.is_modpack == 'mrpack':
                self.update_string = constants.update_list[self.name]['updateString']
        else:
            self.update_string = str(constants.latestMC[self.type]) if constants.version_check(constants.latestMC[self.type], '>', self.version) else ''
            if not self.update_string and self.build:
                self.update_string = ('b-' + str(constants.latestMC['builds'][self.type])) if (tuple(map(int, (str(constants.latestMC['builds'][self.type]).split(".")))) > tuple(map(int, (str(self.build).split("."))))) else ""


        self.server_path = constants.server_path(server_name)
        self.last_modified = os.path.getmtime(self.server_path)


# Loads remote server data locally for a ViewClass in the Server Manager screen
class RemoteViewObject():
    def _is_favorite(self):
        try:
            if self.name in self._telepath_data['added-servers']:
                return self._telepath_data['added-servers'][self.name]['favorite']
        except KeyError:
            pass
        return False

    def toggle_favorite(self):
        if self.name not in self._telepath_data['added-servers']:
            self._telepath_data['added-servers'][self.name] = {}
        self._telepath_data['added-servers'][self.name]['favorite'] = not self.favorite
        self.favorite = not self.favorite
        constants.server_manager.write_telepath_servers(self._telepath_data)

    def __init__(self, instance_data: dict, server_data: dict):
        for k, v in server_data.items():
            setattr(self, k, v)

        self._telepath_data = instance_data

        # Set display name
        if self._telepath_data['nickname']:
            self._telepath_data['display-name'] = self._telepath_data['nickname']
        else:
            self._telepath_data['display-name'] = self._telepath_data['host']
        self._view_name = f"{self._telepath_data['display-name']}/{server_data['name']}"

        self.favorite = self._is_favorite()


# Houses all server information
class ServerManager():

    def __init__(self):
        self.telepath_servers = {}
        self.telepath_updates = {}
        self.online_telepath_servers = []

        self.server_list = create_server_list()
        self.current_server = None
        self.remote_servers = {}
        self.running_servers = {}

        # Load telepath servers
        self.load_telepath_servers()

        if not constants.is_docker:
            print("[INFO] [auto-mcs] Server Manager initialized")

    def _init_telepathy(self, telepath_data: dict):
        self.current_server = telepath.RemoteServerObject(telepath_data)
        return self.current_server

    # Refreshes self.server_list with current info
    def refresh_list(self):

        self.server_list = create_server_list(self.online_telepath_servers)

    # Sets self.current_server to selected ServerObject
    def open_server(self, name):
        try:
            if self.remote_server.name == name:
                self.current_server = self.remote_server
                if constants.debug:
                    print(vars(self.current_server))
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
            self.current_server = ServerObject(name)
            if crash_info[0] == name:
                self.current_server.crash_log = crash_info[1]

        if constants.debug:
            print(vars(self.current_server))

        return self.current_server

    # Sets self.remote_server to selected ServerObject
    def open_remote_server(self, host: str, name: str):
        try:
            if self.current_server.name == name:
                self.remote_servers[host] = self.current_server

                if constants.debug:
                    print(vars(self.remote_servers[host]))

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
                self.remote_servers[host] = ServerObject(name)
                if crash_info[0] == name:
                    self.remote_servers[host].crash_log = crash_info[1]

        if constants.debug:
            print(vars(self.remote_servers[host]))

        return host in self.remote_servers

    # Reloads self.current_server
    def reload_server(self):
        if self.current_server:
            return self.open_server(self.current_server.name)

    # Loads servers from "telepath.json" in Servers directory
    def load_telepath_servers(self):
        # Possibly run this function before auto-mcs boots, and wait for it to finish loading before showing the UI
        if os.path.exists(constants.telepathFile):
            with open(constants.telepathFile, 'r') as f:
                try:
                    self.telepath_servers = json.loads(f.read())
                except json.decoder.JSONDecodeError:
                    pass

        return self.telepath_servers

    # Checks which servers are alive
    def check_telepath_servers(self):
        new_server_list = {}

        def check_server(host, data):
            url = f'http://{host}:{data["port"]}/telepath/check_status'
            try:
                # Check if remote server is online
                if requests.get(url, timeout=0.5).json():
                    # Attempt to log in
                    login_data = constants.api_manager.login(host, data["port"])
                    if login_data:
                        # Update values if host exists
                        if host in self.telepath_servers:
                            for k, v in login_data.items():
                                if v:
                                    self.telepath_servers[host][k] = v
                        else:
                            self.telepath_servers[host] = login_data

                        return host, constants.deepcopy(data)
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
        return new_server_list

    def write_telepath_servers(self, instance=None, overwrite=False):
        if not overwrite:
            self.telepath_servers = self.load_telepath_servers()

        if instance:
            self.telepath_servers[instance['host']] = instance
            del instance['host']

        constants.folder_check(constants.telepathDir)
        with open(constants.telepathFile, 'w+') as f:
            f.write(json.dumps(self.telepath_servers))
        return self.telepath_servers

    def add_telepath_server(self, instance: dict):
        if not instance['nickname']:
            instance['nickname'] = constants.format_nickname(instance['hostname'])

        self.write_telepath_servers(instance)
        self.check_telepath_servers()

    def remove_telepath_server(self, instance: dict):
        if instance['host'] in self.telepath_servers:
            del self.telepath_servers[instance['host']]

        self.write_telepath_servers(overwrite=True)
        self.check_telepath_servers()

    def rename_telepath_server(self, instance: dict, new_name: str):
        new_name = constants.format_nickname(new_name)
        instance['nickname'] = new_name
        self.telepath_servers[instance['host']]['nickname'] = new_name
        self.telepath_servers[instance['host']]['display-name'] = new_name

        self.write_telepath_servers(overwrite=True)

    # Retrieves remote update list
    def reload_telepath_updates(self, host_data=None):
        # Load remote update list
        if host_data:
            self.telepath_updates[host_data['host']] = constants.get_remote_var('update_list', host_data)

        else:
            for host, instance in self.telepath_servers.items():
                host_data = {'host': host, 'port': instance['port']}
                self.telepath_updates[host] = constants.get_remote_var('update_list', host_data)

    # Returns and updates remote update list
    def get_telepath_update(self, host_data: dict, server_name: str):
        self.reload_telepath_updates(host_data)
        if host_data['host'] not in self.telepath_updates:
            self.telepath_updates[host_data['host']] = {}
        if server_name in self.telepath_updates[host_data['host']]:
            return self.telepath_updates[host_data['host']][server_name]
        return {}

# --------------------------------------------- General Functions ------------------------------------------------------

# Generates sorted dict of server information for menu
def create_server_list(remote_data=None):

    final_list = []
    normal_list = []
    favorite_list = []

    def grab_terse_props(server_name, *args):
        server_object = ViewObject(server_name)

        if server_object.favorite:
            favorite_list.append(server_object)
        else:
            normal_list.append(server_object)

    with ThreadPoolExecutor(max_workers=10) as pool:
        pool.map(grab_terse_props, constants.generate_server_list())


    # If remote servers are specified, grab them all with an API request
    if remote_data:
        for host, instance in remote_data.items():
            instance['host'] = host
            try:
                remote_servers = constants.api_manager.request(
                    endpoint='/main/create_server_list',
                    host=instance['host'],
                    port=instance['port'],
                    timeout=0.5
                )

                def process_remote_props(server_data):
                    remote_object = RemoteViewObject(instance, server_data)
                    if remote_object.favorite:
                        favorite_list.append(remote_object)
                    else:
                        normal_list.append(remote_object)

                try:
                    # for s in remote_servers:
                    #     process_remote_props(s)
                    with ThreadPoolExecutor(max_workers=10) as pool:
                        pool.map(process_remote_props, remote_servers)
                except TypeError:
                    continue

            # Don't load server if it can't be found
            except requests.exceptions.ConnectionError:
                pass
            except requests.exceptions.ReadTimeout:
                pass


    normal_list = sorted(normal_list, key=lambda x: x.last_modified, reverse=True)
    favorite_list = sorted(favorite_list, key=lambda x: x.last_modified, reverse=True)
    final_list.extend(favorite_list)
    final_list.extend(normal_list)

    return final_list

# From kivy.utils
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


# ---------------------------------------------- Usage Examples --------------------------------------------------------

# sm = ServerManager()
# sm.open_server("booger squad")
# sm.reload_server()
