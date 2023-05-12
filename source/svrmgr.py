from concurrent.futures import ThreadPoolExecutor
from kivy.utils import escape_markup
from datetime import datetime as dt
from subprocess import Popen, PIPE, run
from threading import Timer
from glob import glob
import ctypes
import time
import os
import re

from backup import BackupObject
from addons import AddonManager
from acl import AclObject
import constants
import amscript


# Auto-MCS Server Manager API
# ----------------------------------------------- Server Objects -------------------------------------------------------

# Instantiate class with "server_name" (case-sensitive)
# Big boy mega server object
class ServerObject():

    def __init__(self, server_name: str):

        gamemode_dict = ['survival', 'creative', 'adventure', 'spectator']
        difficulty_dict = ['peaceful', 'easy', 'normal', 'hard', 'hardcore']


        self.name = server_name
        self.running = False
        self.max_log_size = 800
        self.run_data = {}
        self._hash = constants.gen_rstring(8)


        # Server files
        self.config_file = constants.server_config(server_name)
        self.server_properties = constants.server_properties(server_name)


        # Server properties
        self.favorite = self.config_file.get("general", "isFavorite").lower() == 'true'
        self.auto_update = str(self.config_file.get("general", "updateAuto").lower())
        self.dedicated_ram = str(self.config_file.get("general", "allocatedMemory").lower())
        self.type = self.config_file.get("general", "serverType").lower()
        self.version = self.config_file.get("general", "serverVersion").lower()
        self.build = None
        try:
            if self.config_file.get("general", "serverBuild"):
                self.build = self.config_file.get("general", "serverBuild").lower()
        except:
            pass

        # Check update properties for UI stuff
        self.update_string = ''
        self.update_string = str(constants.latestMC[self.type]) if constants.version_check(constants.latestMC[self.type], '>', self.version) else ''
        if not self.update_string and self.build:
            self.update_string = ('b-' + str(constants.latestMC['builds'][self.type])) if (tuple(map(int, (str(constants.latestMC['builds'][self.type]).split(".")))) > tuple(map(int, (str(self.build).split("."))))) else ""


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
            self.gamemode = gamemode_dict[int(float(self.server_properties['gamemode']))] if not self.server_properties['hardcore'] else 'hardcore'
            self.difficulty = difficulty_dict[int(float(self.server_properties['difficulty']))]
        except ValueError:
            self.gamemode = self.server_properties['gamemode'] if not self.server_properties['hardcore'] else 'hardcore'
            self.difficulty = self.server_properties['difficulty']
        except KeyError:
            self.gamemode = None
            self.difficulty = None

        self.server_path = constants.server_path(server_name)


        # Special sub-objects, and defer loading in the background
        # Make sure that menus wait until objects are fully loaded before opening
        self.backup = None
        self.addon = None
        self.acl = None
        self.script_object = None

        def load_subs(*args):
            self.backup = BackupObject(server_name)
            self.addon = AddonManager(server_name)
            self.acl = AclObject(server_name)
        Timer(0, load_subs).start()

        print(f"[INFO] [auto-mcs] Server Manager: Loaded '{server_name}'")

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
                "geyser_support": False

            },

            # # Dynamic content
            # "addon_objects": self.addon.installed_addons,
            # "backup_object": self.backup,
            # "acl_object": self.acl
        }
        return properties

    # Writes changes to 'server.properties' and 'auto-mcs.ini'
    def write_config(self):
        constants.server_config(self.name, self.config_file)
        constants.server_properties(self.name, self.server_properties)

    # Converts stdout of self.run_data['process'] to fancy stuff
    def update_log(self, text, *args):

        # print(text)
        text = text.decode()

        # (date, type, log, color)
        def format_log(line, *args):

            def format_time(string):
                try:
                    date = dt.strptime(string, "%H:%M:%S").strftime("%#I:%M:%S %p").rjust(11)
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

            if line:

                message_date_obj = dt.now()

                # New log formatting (latest.log)
                if text.startswith('['):
                    message = line.split("]: ", 1)[-1].strip()
                    date_str = line.split("]", 1)[0].strip().replace("[", "")
                    date_label = format_time(date_str)

                # Old log formatting (server.log)
                else:
                    message = line.split("] ", 1)[-1].strip()
                    date_str = line.split(" ", 1)[1].split("[", 1)[0].strip()
                    date_label = format_time(date_str)

                # Format string as needed

                # Shorten coordinates because FUCK they are long
                if "logged in with entity id" not in message:
                    for float_str in re.findall(r"[-+]?(?:\d*\.*\d+)", message):
                        if len(float_str) > 5 and "." in float_str:
                            message = message.replace(float_str, str(round(float(float_str), 2)))

                if message.endswith("[m"):
                    message = message.replace("[m", "").strip()

                # Format special color codes
                if '§' in message:
                    message = escape_markup(message)
                    code_list = [message[x:x + 2] for x, y in enumerate(message, 0) if y == '§']
                    for code in code_list:
                        message = message.replace(code, format_color(code))

                    if len(code_list) % 2 == 1:
                        message = message + '[/color]'

                main_label = message.strip()


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
                    content = message.split('>', 1)[1].strip()
                    main_label = f"{user} issued server command: {content}"
                    self.script_object.message_event({'user': user, 'content': content})


                # Player message log
                elif (message.startswith("<") and ">" in message) or "[Async Chat Thread" in line:
                    type_label = "CHAT"
                    type_color = (0.439, 0.839, 1, 1)

                    if self.script_object.enabled:
                        user = message.split('>', 1)[0].replace('<', '', 1).strip()
                        content = message.split('>', 1)[1].strip()
                        self.script_object.message_event({'user': user, 'content': content})


                # Server message log
                elif message.replace('[Not Secure]', '').strip().startswith("[Server]"):
                    type_label = "CHAT"
                    type_color = (0.439, 0.839, 1, 1)


                # Player command issued
                elif "issued server command: " in message:
                    type_label = "EXEC"
                    type_color = (1, 0.298, 0.6, 1)

                    if self.script_object.enabled:
                        user = message.split('issued server command: ')[0].strip()
                        content = message.split('issued server command: ')[1].strip()
                        self.script_object.message_event({'user': user, 'content': content})


                # Server start log
                elif "Done" in line and "For help," in line:
                    type_label = "START"
                    type_color = (0.3, 1, 0.6, 1)


                # Server stop log
                elif "Stopping server" in line:
                    type_label = "STOP"
                    type_color = (0.3, 1, 0.6, 1)


                # Player join log
                elif "logged in with entity id" in message:
                    user = message.split("[/", 1)[0].strip()
                    ip = message.split("[/", 1)[1].split("]")[0].strip()
                    main_label = f'{user} logged in from {ip} ' + message.split("]")[1].replace('logged in', '').strip()

                    def add_to_list():
                        self.run_data['player-list'][user] = {
                            'user': user,
                            'ip': ip,
                            'date': message_date_obj,
                            'logged-in': True
                        }
                        self.acl.process_log(self.run_data['player-list'][user])

                        if self.script_object.enabled:
                            self.script_object.join_event(self.run_data['player-list'][user])

                    try:
                        if self.run_data['player-list'][user]['date'] < message_date_obj:
                            add_to_list()
                    except KeyError:
                        try:
                            add_to_list()
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
                        self.acl.process_log(self.run_data['player-list'][user])

                        if self.script_object.enabled:
                            self.script_object.leave_event(self.run_data['player-list'][user])

                    try:
                        if self.run_data['player-list'][user]['date'] < message_date_obj:
                            add_to_list()
                    except KeyError:
                        try:
                            add_to_list()
                        except KeyError:
                            pass

                    type_label = "PLAYER"
                    type_color = (0.953, 0.929, 0.38, 1)


                # Other message events
                elif "WARN" in line:
                    type_label = "WARN"
                    type_color = (1, 0.659, 0.42, 1)
                elif "ERROR" in line:
                    type_label = "ERROR"
                    type_color = (1, 0.5, 0.65, 1)
                elif "FATAL" in line:
                    type_label = "FATAL"
                    type_color = (1, 0.5, 0.65, 1)
                else:
                    type_label = "INFO"
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

    # Command handler to current server process
    def send_command(self, cmd, add_to_history=True, log_cmd=True, script=False):

        if self.running and self.run_data:

            # Format command with proper return
            cmd = cmd.replace('\n', '').replace('\r', '').strip()
            if cmd[0] == "/":
                cmd = cmd[1:]

            # Add to command history for input
            if add_to_history:
                if not self.run_data['command-history']:
                    self.run_data['command-history'].insert(0, cmd)
                else:
                    if cmd != self.run_data['command-history'][-1]:
                        self.run_data['command-history'].insert(0, cmd)

            # Send command to Popen stdin
            if self.run_data['process']:

                new_cmd = f"/{cmd}" if bool(re.match('^[a-zA-Z0-9]+$', cmd[:1])) else cmd

                # Send script event
                if self.script_object.enabled and not script:
                    # Check if command is in user command alias list, and if not don't send to server
                    self.script_object.message_event({'user': f'#{self._hash}', 'content': new_cmd})

                # Show log
                if log_cmd:
                    self.run_data['log'].append({'text': (dt.now().strftime("%#I:%M:%S %p").rjust(11), 'EXEC', f"Console issued server command: {new_cmd}", (1, 0.298, 0.6, 1))})

                # Send to server
                self.run_data['process'].stdin.write(f"{cmd}\r\n".encode())
                self.run_data['process'].stdin.flush()
    def silent_command(self, cmd, log=True):
        self.send_command(cmd, False, log, True)

    # Launch server, or reconnect to background server
    def launch(self):

        if not self.running:

            self.running = True
            constants.java_check()

            script_path = constants.generate_run_script(self.properties_dict())
            self.run_data['launch-time'] = dt.now()
            self.run_data['player-list'] = {}
            self.run_data['network'] = {}
            self.run_data['log'] = [{'text': (dt.now().strftime("%#I:%M:%S %p").rjust(11), 'INIT', f"Launching '{self.name}', please wait...", (0.7,0.7,0.7,1))}]
            self.run_data['process-hooks'] = []

            with open(script_path, 'r') as f:
                script_content = f.read()
                firewall_block = False

                # On Windows, prompt to allow Java rule with netsh & UAC
                if constants.os_name == "windows":

                    # Check if Windows Firewall is enabled
                    if "OFF" not in str(run('netsh advfirewall show allprofiles | findstr State', shell=True, stdout=PIPE, stderr=PIPE).stdout):
                        exec_type = 'legacy' if constants.java_executable['legacy'] in script_content else 'modern'
                        if constants.run_proc(f'netsh advfirewall firewall show rule name="auto-mcs java {exec_type}"') == 1:
                            net_test = ctypes.windll.shell32.ShellExecuteW(None, "runas", 'netsh', f'advfirewall firewall add rule name="auto-mcs java {exec_type}" dir=in action=allow enable=yes program="{constants.java_executable[exec_type]}"', None, 0)
                            if net_test == 5:
                                self.run_data['log'].append({'text': (dt.now().strftime("%#I:%M:%S %p").rjust(11), 'WARN', f"Java is blocked by Windows Firewall: can't accept external connections", (1, 0.659, 0.42, 1))})
                                firewall_block = True

                # Check for networking conflicts and current IP
                self.run_data['network'] = constants.get_current_ip(self.name)
                if self.run_data['network']['original_port']:
                    self.run_data['log'].append({'text': (dt.now().strftime("%#I:%M:%S %p").rjust(11), 'WARN', f"Networking conflict detected: temporarily using '*:{self.run_data['network']['address']['port']}'", (1, 0.659, 0.42, 1))})

                # Run server
                self.run_data['process'] = Popen(script_content, stdout=PIPE, stdin=PIPE, stderr=PIPE, cwd=self.server_path, shell=True)

            self.run_data['pid'] = self.run_data['process'].pid
            self.run_data['send-command'] = self.send_command
            self.run_data['command-history'] = []


            # Main server process loop, handles reading output, hooks, and crash detection
            def process_thread(*args):
                if constants.version_check(self.version, '<', '1.7'):
                    lines_iterator = iter(self.run_data['process'].stderr.readline, "")
                else:
                    lines_iterator = iter(self.run_data['process'].stdout.readline, "")
                fail_counter = 0
                close = False
                for line in lines_iterator:
                    self.update_log(line)

                    fail_counter = 0 if line else (fail_counter + 1)

                    # Close wrapper if server is closed
                    # Likely put crash detector here
                    if not self.running or self.run_data['process'].poll() is not None or fail_counter > 100:
                        self.run_data['log'].append({'text': (dt.now().strftime("%#I:%M:%S %p").rjust(11), 'INIT', f"'{self.name}' has stopped successfully", (0.7,0.7,0.7,1))})
                        close = True

                    # Run process hooks
                    for hook in self.run_data['process-hooks']:
                        hook(self.run_data['log'])

                    if close:
                        break


                # Close server
                self.terminate()
                return

            self.run_data['thread'] = Timer(0, process_thread)
            self.run_data['thread'].start()

            constants.server_manager.running_servers[self.name] = self


            # Initialize ScriptObject
            self.script_object = amscript.ScriptObject(self)

            # Fire server start event
            if self.script_object.enabled:
                self.script_object.construct()
                self.script_object.start_event({'date': dt.now()})

            # If start-cmd.tmp exists, run every command in file
            cmd_tmp = constants.server_path(self.name, constants.command_tmp)
            if cmd_tmp:
                with open(cmd_tmp, 'r') as f:
                    for cmd in f.readlines():
                        self.send_command(cmd.strip(), add_to_history=False, log_cmd=False)
                os.remove(cmd_tmp)

        return self.run_data

    # Kill server and delete running configuration
    def terminate(self):

        # Kill server process
        if self.run_data['process'].poll() is None:
            self.run_data['process'].kill()

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
        if self.script_object.enabled:
            self.script_object.shutdown_event({'date': dt.now()})
            self.script_object.deconstruct()
        del self.script_object
        self.script_object = None

        # Delete log from memory (hopefully)
        for item in self.run_data['log']:
            self.run_data['log'].remove(item)
            del item

        self.run_data.clear()
        self.running = False
        del constants.server_manager.running_servers[self.name]
        # print(constants.server_manager.running_servers)

    # Reloads all auto-mcs scripts
    def reload_scripts(self):
        if self.script_object:

            # Delete ScriptObject
            self.script_object.deconstruct()
            del self.script_object

            # Initialize ScriptObject
            self.script_object = amscript.ScriptObject(self)
            self.script_object.construct()

# Low calorie version of ServerObject for a ViewClass in the Server Manager screen
class ViewObject():

    def __init__(self, server_name: str):

        self.name = server_name
        self.running = self.name in constants.server_manager.running_servers.keys()

        if self.running:
            self.run_data = {'network': constants.server_manager.running_servers[self.name].run_data['network']}
        else:
            self.run_data = []


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

        # Check update properties for UI stuff
        self.update_string = ''
        self.update_string = str(constants.latestMC[self.type]) if constants.version_check(constants.latestMC[self.type], '>', self.version) else ''
        if not self.update_string and self.build:
            self.update_string = ('b-' + str(constants.latestMC['builds'][self.type])) if (tuple(map(int, (str(constants.latestMC['builds'][self.type]).split(".")))) > tuple(map(int, (str(self.build).split("."))))) else ""


        self.server_path = constants.server_path(server_name)
        self.last_modified = os.path.getmtime(self.server_path)


# Houses all server information
class ServerManager():

    def __init__(self):
        self.server_list = create_server_list()
        self.current_server = None
        self.running_servers = {}
        print("[INFO] [auto-mcs] Server Manager initialized")

    # Refreshes self.server_list with current info
    def refresh_list(self):
        self.server_list = create_server_list()

    # Sets self.current_server to selected ServerObject
    def open_server(self, name):
        del self.current_server
        self.current_server = None

        # Check if server is running
        if name in self.running_servers.keys():
            self.current_server = self.running_servers[name]
        else:
            self.current_server = ServerObject(name)

    # Reloads self.current_server
    def reload_server(self):
        if self.current_server:
            self.open_server(self.current_server.name)

# --------------------------------------------- General Functions ------------------------------------------------------

# Generates sorted dict of server information for menu
def create_server_list():

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


    normal_list = sorted(normal_list, key=lambda x: x.last_modified, reverse=True)
    favorite_list = sorted(favorite_list, key=lambda x: x.last_modified, reverse=True)
    final_list.extend(favorite_list)
    final_list.extend(normal_list)

    return final_list



# ---------------------------------------------- Usage Examples --------------------------------------------------------

# sm = ServerManager()
# sm.open_server("booger squad")
# sm.reload_server()
