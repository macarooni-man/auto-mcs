import distutils.sysconfig as sysconfig
from difflib import SequenceMatcher
from threading import Timer
from textwrap import indent
from copy import deepcopy
from munch import Munch
from glob import glob
from nbt import nbt
import constants
import traceback
import functools
import requests
import base64
import json
import time
import ast
import sys
import os
import re
import gc


# Auto-MCS Scripting API
# ------------------------------------------------- Script Object ------------------------------------------------------

# House an .ams file and relevant details
class AmsFileObject():
    def __init__(self, path, enabled=False):
        self.script_object_type = 'file'
        self.path = path
        self.file_name = os.path.basename(path)
        self.title = self.file_name.replace(".ams","")
        self.author = None
        self.version = None
        self.description = None
        self.enabled = enabled


        # Try and grab header information from .ams file
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                header_data = [line.replace("#","").strip() for line in f.read().split("#!")[1].splitlines() if line]
                for line in header_data:

                    # Get title of script
                    if line.lower().startswith("title:"):
                        self.title = line.split("title:", 1)[1].strip()
                        continue

                    # Get author of script
                    elif line.lower().startswith("author:") and not self.author:
                        self.author = line.split("author:", 1)[1].strip()
                        continue

                    # Get version of script
                    elif line.lower().startswith("version:") and not self.version:
                        self.version = line.split("version:", 1)[1].strip()
                        continue

                    # Get description of script
                    elif line.lower().startswith("description:") and not self.description:
                        self.description = line.split("description:", 1)[1].strip()
                        continue

        except:
            pass

        if not self.author:
            self.author = "Unknown"
        if not self.version:
            self.version = "Unknown"
        if not self.description:
            self.description = "No description"

        self.hash = base64.b64encode(f'{self.title}/{self.author}/{self.version}'.encode())

# House an .ams file in the online repository
class AmsWebObject():
    def __init__(self, data: tuple or list):
        self.script_object_type = 'web'

        meta = None
        self.title = data[0]
        data = data[1]

        self.url = data['url']
        self.download_url = None
        self.file_name = None
        self.author = None
        self.version = None
        self.description = None
        self.installed = False
        self.libs = None

        # Retrieve metadata
        for name, url in data.items():
            if name == 'meta':
                meta = requests.get(url).content.decode()
                for line in meta.splitlines():

                    # Get title of script
                    if line.lower().startswith("title:") and not self.title:
                        self.title = line.split("title:", 1)[1].strip()
                        continue

                    # Get author of script
                    elif line.lower().startswith("author:") and not self.author:
                        self.author = line.split("author:", 1)[1].strip()
                        continue

                    # Get version of script
                    elif line.lower().startswith("version:") and not self.version:
                        self.version = line.split("version:", 1)[1].strip()
                        continue

                self.description = meta.split('description:')[1].strip()

            elif name.endswith(".ams"):
                self.file_name = name
                self.download_url = url

            elif name == 'libs.zip':
                self.libs = url

        if not self.author:
            self.author = "Unknown"
        if not self.version:
            self.version = "Unknown"
        if not self.description:
            self.description = "No description"

# For managing .ams files and toggling them in the menu
class ScriptManager():

    def __init__(self, server_name):
        self._server_name = server_name
        self._server_path = constants.server_path(server_name)
        self.script_path = constants.scriptDir
        self.json_path = os.path.join(self._server_path, 'amscript', json_name)
        self.installed_scripts = {'enabled': [], 'disabled': []}
        self._online_scripts = constants.ams_web_list
        self._script_hash = None
        self._enumerate_scripts()

    # Sets script hash to determine changes
    def _set_hash(self):
        script_hash = ""

        for script in sorted(self.installed_scripts['enabled'], key=lambda x: x.title):
            script_hash += script.hash.decode()

        return script_hash

    # Checks script hash in running config to see if it's changed
    def _hash_changed(self):
        hash_changed = False

        if self._server_name in constants.server_manager.running_servers:
            hash_changed = constants.server_manager.running_servers[self._server_name].run_data['script-hash'] != self._script_hash

        return hash_changed

    # Checks for enabled scrips and adds them to the list
    def _enumerate_scripts(self, single_list=False):
        all_scripts = glob(os.path.join(self.script_path, '*.ams'))
        ams_dict = {'enabled': [], 'disabled': []}

        # Cross-reference enabled scripts in json_path
        if os.path.isfile(self.json_path):
            try:
                with open(self.json_path, 'r') as f:
                    enabled_list = json.load(f)['enabled']
                    for path in all_scripts:
                        for enabled in enabled_list:
                            if os.path.basename(path.lower()) == enabled.strip().lower():
                                ams_dict['enabled'].append(AmsFileObject(path, enabled=True))
                                break
                        else:
                            ams_dict['disabled'].append(AmsFileObject(path, enabled=False))
            except:
                os.remove(self.json_path)


        # If no scripts are explicitly allowed in the .json file, disable all scripts
        if not os.path.isfile(self.json_path):
            ams_dict['disabled'] = [AmsFileObject(script, enabled=False) for script in all_scripts]

        self.installed_scripts = ams_dict
        self._script_hash = self._set_hash()

        # If single list, concatenate enabled and disabled lists
        if single_list:
            final_list = deepcopy(ams_dict['enabled'])
            final_list.extend(ams_dict['disabled'])
            return final_list
        else:
            return ams_dict

    # If scripts aren't obtained, gather web list
    def _refresh_online_scripts(self):
        if not self._online_scripts:
            constants.get_repo_scripts()
            self._online_scripts = constants.ams_web_list

    # Imports list of scripts into script folder
    def import_script(self, script: str):
        if not script:
            return False

        success = False
        source_dir = os.path.dirname(script)
        source_name = os.path.basename(script)

        # Make sure the addon_path and destination_path are not the same
        if source_dir != constants.scriptDir and source_name.endswith(".ams"):

            # Copy script to proper folder if it exists
            try:
                constants.copy_to(script, constants.scriptDir, source_name)
                success = AmsFileObject(os.path.join(constants.scriptDir, source_name))
                self.script_state(success, enabled=True)
            except OSError:
                pass

        self._enumerate_scripts()
        return success

    # Checks online to view scripts from GitHub
    def search_scripts(self, query: str, *args):
        constants.folder_check(constants.scriptDir)
        self._refresh_online_scripts()

        final_list = []
        installed_list = [script.title.lower().strip() for script in self.return_single_list()]

        # Filter available scripts with query
        for script in self._online_scripts:
            if query.lower().strip() in script.title.lower().strip() or query.lower() in script.description.lower().strip() or not query:
                if script not in final_list:
                    script.installed = script.title.lower().strip() in installed_list
                    final_list.append(script)

        return final_list

    # Downloads script and enables it
    def download_script(self, script: str or AmsWebObject):

        # If string was provided
        if isinstance(script, str):
            script = self.get_script(script, online=True)

        constants.folder_check(constants.scriptDir)
        constants.download_url(script.download_url, script.file_name, constants.scriptDir)
        new_script = AmsFileObject(os.path.join(constants.scriptDir, script.file_name))
        self.script_state(new_script, enabled=True)

        if script.libs:
            lib_dir = os.path.join(constants.scriptDir, 'libs')
            constants.folder_check(constants.downDir)
            constants.folder_check(lib_dir)
            constants.download_url(script.libs, 'libs.zip', constants.downDir)
            constants.extract_archive(os.path.join(constants.downDir, 'libs.zip'), lib_dir)

    # Enables/Disables scripts
    def script_state(self, script: AmsFileObject, enabled=True):
        script_state(self._server_name, script, enabled)

        # Reload script data
        self._enumerate_scripts()

    # Deletes script
    def delete_script(self, script: AmsFileObject):

        # Remove script from every server in which it's enabled
        for server in glob(os.path.join(constants.applicationFolder, 'Servers', '*')):
            server_name = os.path.basename(server)
            json_path = constants.server_path(server_name, 'amscript', json_name)
            if json_path:
                script_state(server_name, script, enabled=False)

        # Delete script from .ams path
        try:
            os.remove(script.path)
            removed = True
        except OSError:
            removed = False

        self._enumerate_scripts()
        return removed

    # Retrieves AmsFileObject or AmsWebObject by name
    def get_script(self, script_name: str, online=False):
        name = script_name.strip().lower()
        match_list = []

        # Get list of available scripts
        if online:
            self._refresh_online_scripts()
            script_list = self._online_scripts
        else:
            script_list = self.return_single_list()

        for script in script_list:

            if name in [script.title.lower(), script.file_name.lower()]:
                return script

            score = round(SequenceMatcher(None, script.title.lower(), name).ratio(), 2)
            score += round(SequenceMatcher(None, script.file_name.lower(), name).ratio(), 2)
            if script.description:
                score += (round(SequenceMatcher(None, script.description.lower(), name).ratio(), 2) * 5)

            match_list.append((script, score))

        if match_list:
            return sorted(match_list, key=lambda x: x[1], reverse=True)[0][0]

    # Returns single list of all scripts
    def return_single_list(self):
        return self._enumerate_scripts(single_list=True)


# For processing .ams files and running them in the wrapper
# Pass in svrmgr.ServerObject
class ScriptObject():

    # ------------------------- Management -------------------------

    def __init__(self, server_obj=None):
        # Server stuffs
        self.enabled = True

        if server_obj:
            self.server = server_obj
            self.server_script_obj = ServerScriptObject(server_obj)
            self.server_id = ("#" + server_obj._hash)

        # File stuffs
        self.script_path = constants.scriptDir
        self.scripts = None

        # Yummy stuffs
        self.protected_variables = ["server", "acl", "backup", "addon", "amscript"]
        self.valid_events = ["@player.on_join", "@player.on_leave", "@player.on_death", "@player.on_message", "@player.on_alias", "@server.on_start", "@server.on_stop", "@server.on_loop"]
        self.delay_events = ["@player.on_join", "@player.on_leave", "@player.on_death", "@player.on_message", "@server.on_start", "@server.on_stop"]
        self.valid_imports = std_libs
        for library in ['dataclasses', 'itertools', 'requests', 'bs4', 'nbt', 'tkinter', 'simpleaudio', 'webbrowser', 'cloudscraper', 'json', 'difflib', 'shutil', 'concurrent', 'concurrent.futures', 'random', 'platform', 'threading', 'copy', 'glob', 'configparser', 'unicodedata', 'subprocess', 'functools', 'threading', 'requests', 'datetime', 'tarfile', 'zipfile', 'hashlib', 'urllib', 'string', 'psutil', 'socket', 'time', 'json', 'math', 'sys', 'os', 're', 'pathlib', 'ctypes', 'inspect', 'functools', 'PIL', 'base64', 'ast', 'traceback', 'munch', 'textwrap', 'urllib']:
            if library not in self.valid_imports:
                self.valid_imports.append(library)


        # Import external libraries
        self.lib_path = os.path.join(constants.scriptDir, 'libs')
        constants.folder_check(self.lib_path)
        if self.lib_path not in sys.path:
            sys.path.append(self.lib_path)
        for library in [os.path.basename(x).rsplit(".", 1)[0] for x in glob(os.path.join(self.lib_path, '*.py'))]:
            if library not in self.valid_imports:
                self.valid_imports.append(library)
        for library in [os.path.basename(x) for x in glob(os.path.join(self.lib_path, '*')) if os.path.isdir(x) and not x.endswith('pstconf')]:
            if library not in self.valid_imports:
                self.valid_imports.append(library)


        self.aliases = {}
        self.src_dict = {}
        self.function_dict = {}


    def __del__(self):
        self.enabled = False


    # If script returns None it's valid, else will return error message
    # 1. Iterate over every line and check for valid events, and protect global variables and functions
    # 2. Check for general Python syntax errors
    def is_valid(self, script_path: list or str):

        def iterate_lines(iterator, file_name):

            parse_error = {}
            script_text = ""
            id_hash = constants.gen_rstring(10)
            max_lines = 0

            for x, line in iterator:
                max_lines = x
                line.replace("\r","")
                if not line.endswith("\n"):
                    line = line + "\n"

                # Throw error if server variable is reassigned
                for var in self.protected_variables:
                    stripped = line.strip().replace(' ', '')
                    if stripped.startswith(f"{var}=") or\
                    ("def" in line and f" {var}(" in line) or\
                    (line.strip().startswith("import ") and line.strip().endswith(f"as {var}")) or \
                    ((stripped.startswith(f"{var},") or f",{var}," in stripped or f",{var}=" in stripped) and "=" in line):
                        parse_error['file'] = file_name
                        parse_error['code'] = line.rstrip()
                        parse_error['line'] = f'{x}:{line.find(f"{var}") + 1}'
                        parse_error['message'] = f"(AssertionError) '{var}' attribute is read-only and cannot be re-assigned"
                        parse_error['object'] = AssertionError(parse_error['message'].split(") ")[1])
                        return parse_error

                # Format valid event tags as functions
                for event in self.valid_events:

                    # Invalid indentation
                    if event in line and not line.startswith(event) and not line.startswith("#"):
                        parsed_event = line.strip().split('(')[0]
                        parse_error['file'] = file_name
                        parse_error['code'] = line.split(event)[0]
                        parse_error['line'] = f'{x}:1'
                        parse_error['message'] = f"(IndentationError) '{parsed_event}' cannot be indented"
                        parse_error['object'] = IndentationError(parse_error['message'].split(") ")[1])
                        return parse_error


                    elif line.startswith(event):
                        if event == '@player.on_alias':
                            line = line.replace(event, f'{event.split(".")[1]}').replace(":\n", f'\ndef __on_alias__(): #{id_hash}\n')
                        elif event == '@server.on_loop':
                            line = line.replace(event, f'{event.split(".")[1]}').replace(":\n", f'\ndef __on_loop__(): #{id_hash}\n')
                        else:
                            line = line.replace(event, f'def {event.split(".")[1]}')


                    # Check for invalid events
                    elif (line.startswith("@server.") or line.startswith("@player.")) and (("(") in line and ("):") in line):
                        parsed_event = line.strip().split('(')[0]
                        if parsed_event not in self.valid_events:
                            parse_error['file'] = file_name
                            parse_error['code'] = line.rstrip()
                            parse_error['line'] = f'{x}:1'
                            parse_error['message'] = f"(EventError) '{parsed_event}' event does not exist"
                            parse_error['object'] = NameError(parse_error['message'].split(") ")[1])
                            return parse_error

                script_text = script_text + f'{line}'

            # print(script_text)

            try:
                ast.parse(script_text)
            except Exception as e:
                try:
                    line_num = e.args[1][1] - script_text.count(f'#{id_hash}', 0, script_text.find(e.args[1][-1].strip()))
                    parse_error['file'] = file_name
                    parse_error['code'] = e.args[1][-1].strip()
                    parse_error['line'] = f"{line_num}:{e.args[1][2]}"
                    parse_error['message'] = f"({e.__class__.__name__}) {e.args[0]}"
                    parse_error['object'] = e
                except IndexError:
                    try:
                        line_num = str(e).rsplit("line ", 1)[1].replace(")", "")
                        parse_error['file'] = file_name
                        parse_error['line'] = f"{line_num}:0"
                        parse_error['code'] = script_text.splitlines()[int(line_num)-1].strip()
                        parse_error['message'] = f"({e.__class__.__name__}) {e.args[0]}"
                        parse_error['object'] = e
                        parse_error['object'].args = (e.args[0], ('<unknown>', int(line_num), 0, parse_error['code']))
                    except IndexError:
                        parse_error['file'] = file_name
                        parse_error['code'] = "Unknown"
                        parse_error['line'] = "0:0"
                        parse_error['message'] = f"({e.__class__.__name__}) {e.args[0]}"
                        parse_error['object'] = e

                # Reformat if it starts with an event
                error = parse_error['code']
                try:
                    if error.startswith('def') or error.startswith('on_'):
                        for event in self.valid_events:
                            if event.endswith(error.replace('def ','',1).split('(')[0].strip()):
                                old, same = error.split('(', 1)
                                pattern = event + '(' + same
                                if ':' in parse_error['line']:
                                    line, char = parse_error['line'].split(':')
                                    if parse_error['message'] == '(IndentationError) expected an indented block':
                                        char = 1
                                    else:
                                        char = str(int(char) - len(old) + len(event))
                                    parse_error['line'] = f'{line}:{char}'
                                parse_error['code'] = pattern
                                args = list(parse_error['object'].args)
                                args1 = list(args[1])
                                args1[-1] = pattern
                                args[1] = tuple(args1)
                                parse_error['object'].args = tuple(args)
                                break
                except ValueError:
                    pass

                if ':' in parse_error['line']:
                    line, char = parse_error['line'].split(":")
                    if int(line) > max_lines:
                        parse_error['line'] = f"{max_lines}:{char}"

                return parse_error

        if isinstance(script_path, str):
            with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:
                return iterate_lines(enumerate(f.readlines(), 1), file_name=os.path.basename(script_path))
        else:
            return iterate_lines(enumerate(script_path[0].splitlines(), 1), file_name=os.path.basename(script_path[1]))

    # Converts amscripts into memory to be accessed by events
    # 1. Remove all comments and sort global functions and variables into 'gbl' string, and source into 'src' string
    # 2. Run 'gbl' string in exec() to check for functional errors, and send final memory space to 'variables' dict
    # 3. Pull out every @event and send them to the src_dict and function_dict for further processing
    # 4. Wrap @server.on_loop and @player.on_alias events with special code to ensure proper functionality
    def convert_script(self, script_path):

        def enum_error(e, find=None):
            s = os.path.basename(script_path)
            ex_type, ex_value, ex_traceback = sys.exc_info()
            parse_error = {}

            # First, grab relative line number from modified code
            tb = [item for item in traceback.format_exception(ex_type, ex_value, ex_traceback) if 'File "<string>"' in item][-1].strip()

            if find:
                line_num = 0
                original_code = find

            else:
                line_num = int(re.search(r'(?<=,\sline\s)(.*)(?=,\sin)', tb).group(0))

                # Locate original code from source
                original_code = self.src_dict[s]['gbl'].splitlines()[line_num - 1]

            # Use the line to find the original line number from the source
            event_count = 0
            func_name = f'def {tb.split("in ")[1].strip()}('
            for n, line in enumerate(self.src_dict[s]['src'].splitlines(), 1):
                # print(n, line, event_count, i)

                if (original_code.strip() in line) and (event_count > 0):
                    line_num = f'{n}:{len(line) - len(line.lstrip()) + 1}'
                    break

                if line.startswith(func_name):
                    event_count += 1

            # Likely global code that's not wrapped in a function
            else:
                for n, line in enumerate(self.src_dict[s]['src'].splitlines(), 1):
                    # print(n, line, event_count, i)

                    if original_code.strip() in line:
                        line_num = f'{n}:{len(line) - len(line.lstrip()) + 1}'
                        break

                    if line.startswith(func_name):
                        event_count += 1

            # Generate error dict
            parse_error['file'] = s
            parse_error['code'] = original_code.strip()
            parse_error['line'] = line_num
            parse_error['message'] = f"({ex_type.__name__}) {ex_value}"
            parse_error['object'] = e

            del self.function_dict[s]['values']
            del self.src_dict[s]['gbl']
            del self.src_dict[s]['src']

            return parse_error

        with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:

            # Initialize self.function_dict
            self.function_dict[os.path.basename(script_path)] = {event: [] for event in self.valid_events}
            self.src_dict[os.path.basename(script_path)] = {event: [] for event in self.valid_events}
            self.src_dict[os.path.basename(script_path)]['other_funcs'] = []
            self.src_dict[os.path.basename(script_path)]['src'] = ''
            self.src_dict[os.path.basename(script_path)]['gbl'] = ''

            # Get list of all variables
            variables = {
                'server': self.server_script_obj,
                'acl': self.server.acl,
                'backup': self.server.backup,
                'addon': self.server.addon,
                'amscript': self.server.script_manager
            }

            try:
                test = self.function_dict[os.path.basename(script_path)]['values']
            except KeyError:
                self.function_dict[os.path.basename(script_path)]['values'] = variables

            alias_functions = {}
            loop_functions = []
            func_calls = []

            # Ignore all comments and grab imports/global variables
            script_data = ""
            global_variables = f"from itertools import zip_longest\nimport importlib\nimport time\nimport sys\nimport os\nsys.path.insert(0, r'{self.script_path}')\n"

            for line in f.readlines():
                line = line.replace('\t', '    ')
                self.src_dict[os.path.basename(script_path)]['src'] += line

                # Possible function call
                try:
                    func_call = re.search(r'\w+[^\s+(def|async)\s+.+]+\.?\w+\(*.*\)[^\:]*', line).group(0).strip()
                except AttributeError:
                    func_call = None

                # Find and remove comments
                if line.strip().startswith('#'):
                    line = line.split("#")[0] + "\n"

                # Grab import statements
                elif line.startswith("from ") or line.startswith("import "):
                    for i in self.valid_imports:
                        if re.search(r'\b' + i + r'\b', line):
                            if line not in global_variables:
                                global_variables = global_variables + line.strip() + "\n"
                            if f"import {i} as " in line and "from " not in line:
                                i = line.split(f"import {i} as ", 1)[1].strip()
                            if f"from {i}" in line and " import" in line:
                                break
                            if f"importlib.reload({i})" not in global_variables:
                                global_variables = global_variables + f"importlib.reload({i})\n"
                        else:
                            try:
                                exec(line.strip(), {}, {})
                            except Exception as e:
                                return enum_error(e, find=line.strip())


                # Tag global functions
                elif line.startswith("def "):
                    line = "%" + line

                # Find global variables
                elif not ((line.startswith(' ') or line.startswith('\t'))):
                    # Find function calls and decorators
                    if (line.startswith("@")) and line.strip()[-1] != ":": # func_call == line.strip() or
                        func_calls.append(f'{line.strip()}\n')

                    elif not (line.strip().startswith('@') and line.strip().endswith(':')): # elif re.match(r"[A-Za-z0-9]+.*=.*", line.strip(), re.IGNORECASE)
                        global_variables = global_variables + line.strip() + "\n"

                script_data = script_data + line
            script_data += "\n "

            # Redefine print function to redirect to server console instead of Python console
            print_func = "def print(*args, sep=' ', end=''):\n    for line in sep.join(str(arg) for arg in args).replace('\\r','').splitlines():\n        server._ams_log(line, 'print')"
            global_variables = global_variables + "\n" + print_func + "\n"

            # Search through script to find global functions
            last_index = 0
            for num in range(0, script_data.count("%def ")):

                text = script_data[script_data.find("%def ", last_index):]
                last_index = script_data.find("%def ", last_index) + 1

                function = ''

                # Find where function ends by locating indents
                for x, line in enumerate(text.splitlines()):
                    if (line[0:1] not in ['', ' '] and x > 1) or (x + 1 == len(text.splitlines())):

                        # Format string and use exec to return function object
                        for new_line in text.splitlines()[:x]:
                            if new_line.startswith("%"):
                                new_line = new_line.replace("%def ", f'def ')
                            function = function + new_line + "\n"
                        global_variables = global_variables + "\n\n" + function.strip()
                        self.src_dict[os.path.basename(script_path)]['other_funcs'].append(function.strip())
                        break

            # Load global function calls at the very end
            global_variables += "\n\n"
            for line in func_calls:
                global_variables = global_variables + line

            # Change to server directory
            global_variables += f"\nos.chdir(r'{self.server.server_path}')"

            # Load Imports, and global variables/functions into memory
            # print(global_variables)
            self.src_dict[os.path.basename(script_path)]['gbl'] = global_variables

            # Attempt to process imports, global variables, and functions
            try:
                exec(global_variables, self.function_dict[os.path.basename(script_path)]['values'], self.function_dict[os.path.basename(script_path)]['values'])

            # Handle global variable exceptions
            except Exception as e:
                return enum_error(e)

            # Search through script for events
            for event in self.valid_events:

                if event in script_data:

                    last_index = 0
                    for num in range(0, script_data.count(event)):

                        text = script_data[script_data.find(event, last_index):]
                        last_index = script_data.find(event, last_index) + 1

                        function = ''

                        # Find where function ends by locating indents
                        for x, line in enumerate(text.splitlines()):
                            if (line[0:1] not in ['', ' '] and x > 1) or (x + 1 == len(text.splitlines())):

                                # Format string and use exec to return function object
                                func_name = f'__{event.split(".")[1]}__'
                                for new_line in text.splitlines()[:x]:

                                    # Replace event decorators with function assignments
                                    if new_line.startswith("@"):
                                        new_line = new_line.replace(event, f'def {func_name}')

                                    # Attempt to prevent while loops from looping forever
                                    if new_line.strip().startswith("while "):
                                        new_line = ' and server._running:'.join(new_line.rsplit(':', 1))

                                    function = function + new_line + "\n"
                                function = function.strip()
                                src_function_call = f"{event}({function.splitlines()[0].split('(', 1)[1]}"
                                # print(function)

                                # Check if delay is specified for events that support it, and modify the function accordingly
                                if event in self.delay_events:
                                    try:
                                        func_head = function.splitlines()[0]
                                        search = re.search(r",\s*?delay=[0-9]*\.?[0-9]*", func_head).group(0)
                                        delay = float(re.sub(r"[^0-9.]", '', search))
                                    except AttributeError:
                                        search = ''
                                        delay = 0

                                    if search and delay > 0:
                                        call, body = function.replace(search, '').split("\n", 1)
                                        function = call + f"\n    time.sleep({delay})\n" + body

                                # Register alias and reformat code
                                if event == '@player.on_alias':
                                    alias_values = {
                                        'cmd': '',
                                        'args': {},
                                        'perm': 'anyone',
                                        'desc': '',
                                        'plr': '',
                                        'hide': False
                                    }

                                    args = function.splitlines()[0].split('(', 1)[1].rsplit(')', 1)[0]
                                    if "command=" not in args and "player=" not in args:
                                        player, args = args.split(",", 1)
                                        args = f"'{player.strip()}', {args.strip()}"
                                    elif ('=' in args.split(",")[0]) and "player=" not in args:
                                        args = "player='player', " + args
                                    else:
                                        player, args = args.split(",", 1)
                                        args = f"'{player.strip()}', {args.strip()}"
                                    # print(args)

                                    proc_func = "def process(player='player', command='', arguments={}, permission='anyone', description='', hidden=False):\n    global cmd, args, perm, desc, plr, hide\n    cmd=command\n    args=arguments\n    perm=permission\n    desc=description\n    plr=player\n    hide=hidden\n"
                                    proc_func += f"process({args})"
                                    try:
                                        exec(proc_func, alias_values, alias_values)
                                    except Exception as e:
                                        return enum_error(e, find=src_function_call)

                                    # Only allow last argument to be optional, hence retarded dict comprehension
                                    alias_keys = alias_values['args'].keys()
                                    alias_dict = {
                                        'command': f"!{alias_values['cmd']}" if bool(re.match('^[a-zA-Z0-9]+$', alias_values['cmd'][:1])) else f"!{alias_values['cmd'][1:]}",
                                        'arguments': {k: (True if (k != list(alias_keys)[-1]) else v) for (k, v) in alias_values['args'].items()},
                                        'syntax': '',
                                        'permission': alias_values['perm'],
                                        'description': alias_values['desc'] if alias_values['desc'] else f"Provided by '{os.path.basename(script_path)}'",
                                        'player': alias_values['plr'],
                                        'hidden': alias_values['hide']
                                    }

                                    syntax = f"!{alias_values['cmd']}"
                                    for z, y in alias_dict['arguments'].items():
                                        syntax += f" <{z + ':optional' if not y else z}>"

                                    alias_dict['syntax'] = syntax

                                    self.aliases[alias_dict['command']] = alias_dict
                                    if not alias_dict['hidden']:
                                        self.server_script_obj.aliases[alias_dict['command']] = {
                                            'command': alias_dict['command'],
                                            'syntax': syntax,
                                            'permission': alias_dict['permission'],
                                            'description': alias_dict['description'],
                                            'file': os.path.basename(script_path)
                                        }
                                    alias_functions[alias_dict['command']] = function


                                # Register loop event and reformat code
                                elif event == '@server.on_loop':
                                    loop_values = {
                                        'itvl': 0,
                                        'unt': 'second'
                                    }

                                    args = function.splitlines()[0].split('(', 1)[1].rsplit(')', 1)[0].lower()
                                    proc_func = "def process(interval=1, unit='second'):\n    global itvl, unt\n    itvl=interval\n    unt=unit\n"
                                    proc_func += f"process({args})"
                                    try:
                                        exec(proc_func, loop_values, loop_values)
                                    except Exception as e:
                                        return enum_error(e, find=src_function_call)

                                    loop_dict = {
                                        'interval': loop_values['itvl'],
                                        'unit': loop_values['unt'],
                                        'function': function
                                    }

                                    # Input validation
                                    loop_dict['unit'] = loop_dict['unit'] if loop_dict['unit'] in ('second', 'minute', 'hour', 'tick') else 'second'

                                    # Seconds conversion, round to nearest 0.05 step
                                    try:
                                        if loop_dict['unit'] in ('second', 'minute', 'hour'):
                                            test = float(loop_dict['interval'])
                                            test = test if loop_dict['unit'] == 'second' else (test * 60) if loop_dict['unit'] == 'minute' else (test * 3600)
                                            loop_dict['interval'] = round(((test // 0.05) * 0.05) + 0.05, 2)

                                        # Tick conversion to seconds
                                        else:
                                            test = float(loop_dict['interval'])
                                            loop_dict['interval'] = round((test * 0.05), 2) if test > 1 else 0.05
                                    except:
                                        loop_dict['interval'] = 1

                                    loop_functions.append(loop_dict)
                                    # print(loop_dict)


                                else:
                                    try:
                                        exec(function, self.function_dict[os.path.basename(script_path)]['values'], self.function_dict[os.path.basename(script_path)]['values'])
                                        self.function_dict[os.path.basename(script_path)][event].append(self.function_dict[os.path.basename(script_path)]['values'][func_name])
                                        self.src_dict[os.path.basename(script_path)][event].append(function.strip())
                                    except Exception as e:
                                        return enum_error(e, find=src_function_call)
                                break

            # Concatenate all aliases into one function
            if alias_functions:
                first = True

                func_header = "def __on_alias__(player, command, permission='anyone'):\n"
                func_header += "    perm_dict = {'anyone': 0, 'op': 1, 'server': 2}\n\n"
                new_func = ""

                for k, v in alias_functions.items():

                    syntax = self.aliases[k]['syntax']
                    hidden = self.aliases[k]['hidden']
                    argument_list = list(self.aliases[k]['arguments'].keys())
                    req_args_list = list([x for x in self.aliases[k]['arguments'].keys() if self.aliases[k]['arguments'][x]])
                    arguments = {}

                    new_func += f"    {'if' if first else 'elif'} command.strip().split(' ',1)[0].strip() == '{k}': #__{self.server_id}__\n"
                    if self.aliases[k]['permission'] in ['anyone', 'op', 'server']:
                        new_func += f"        if perm_dict[permission] < perm_dict['{self.aliases[k]['permission']}']:\n"
                    else:
                        new_func += f"        if not player.check_permission('{self.aliases[k]['permission']}'):\n"

                    # Permission thingy
                    new_func += (f"            player.log_error(\"You do not have permission to use this command\")\n" if not hidden else "            pass\n")
                    new_func += f"        else:\n"
                    new_func += f"            if len(command.split(' ', len({argument_list}))[1:]) < len({req_args_list}):\n"

                    # Syntax thingy
                    new_func += (f"                player.log_error(\"Invalid syntax: {syntax}\")\n" if not hidden else "                pass\n")
                    new_func += f"            else:\n"
                    new_func += f"                arguments = dict(zip_longest({argument_list}, command.split(' ', len({argument_list}))[1:]))\n"
                    new_func += f"                command = command.split(' ', 1)[0].strip()\n"

                    # Allow 'player' variable to be reassigned if needed
                    if self.aliases[k]['player'] != 'player':
                        new_func += f"                {self.aliases[k]['player']} = player\n"

                    # Iterate over function to pull out global calls, and put them at the top
                    actual_code = ''
                    for line in v.split("\n", 1)[1].splitlines():
                        if line.strip().startswith("global"):
                            if line.strip() not in func_header:
                                func_header += ("    " + line.strip() + "\n")
                        else:
                            actual_code += (line + "\n")
                    func_header += "\n"

                    new_func += "\n"
                    new_func += indent(actual_code, "            ")
                    new_func += "\n\n"
                    first = False

                new_func = func_header + new_func

                # print(new_func)
                exec(new_func, self.function_dict[os.path.basename(script_path)]['values'], self.function_dict[os.path.basename(script_path)]['values'])
                self.function_dict[os.path.basename(script_path)]['@player.on_alias'].append(self.function_dict[os.path.basename(script_path)]['values']['__on_alias__'])
                self.src_dict[os.path.basename(script_path)]['@player.on_alias'].append(new_func.strip())

            # Convert all loops to actual loops
            if loop_functions:
                for loop in loop_functions:

                    div_int = 5
                    new = divmod(loop['interval'], div_int)

                    # Initialize wrapper and split timer into chunks for polling if the server has closed
                    new_func = "def __on_loop__():\n"
                    new_func += f"    while server._running:\n"
                    if new[0] > 0:
                        new_func += f"        for s in range({int(new[0])}):\n"
                        new_func += f"            if not server._running:\n"
                        new_func += f"                return\n"
                        new_func += f"            time.sleep({div_int})\n"

                    if new[1]:
                        new_func += f"        time.sleep({new[1]})\n"

                    new_func += f"        if not server._running:\n"
                    new_func += f"            return\n"

                    new_func += "\n"

                    # Put code in loop
                    new_func += indent(loop['function'].split("\n", 1)[1], "    ")
                    new_func += "\n\n"

                    # print(new_func)
                    exec(new_func, self.function_dict[os.path.basename(script_path)]['values'], self.function_dict[os.path.basename(script_path)]['values'])
                    self.function_dict[os.path.basename(script_path)]['@server.on_loop'].append(self.function_dict[os.path.basename(script_path)]['values']['__on_loop__'])
                    self.src_dict[os.path.basename(script_path)]['@server.on_loop'].append(new_func.strip())

            # Remove references to function calls in the script context
            for event in self.valid_events:
                func_name = f'__{event.split(".")[1]}__'
                if func_name in self.function_dict[os.path.basename(script_path)]['values'].keys():
                    del self.function_dict[os.path.basename(script_path)]['values'][func_name]

            del variables
            # print(function)
        # print(self.function_dict)


    # Generate script thread and code from .ams files
    def construct(self):

        # First, gather all script files
        constants.folder_check(self.script_path)
        self.server.script_manager._enumerate_scripts()
        self.scripts = [os.path.join(constants.executable_folder, 'baselib.ams')]
        self.scripts.extend([script.path for script in self.server.script_manager.installed_scripts['enabled']])


        # Reload external libraries
        constants.folder_check(self.lib_path)
        if self.lib_path not in sys.path:
            sys.path.append(self.lib_path)
        for library in [os.path.basename(x).rsplit(".", 1)[0] for x in glob(os.path.join(self.lib_path, '*.py'))]:
            if library not in self.valid_imports:
                self.valid_imports.append(library)
        for library in [os.path.basename(x) for x in glob(os.path.join(self.lib_path, '*')) if os.path.isdir(x) and not x.endswith('pstconf')]:
            if library not in self.valid_imports:
                self.valid_imports.append(library)


        # Parse script file
        def process_file(script_file):
            parse_error = self.is_valid(script_file)

            if parse_error is None:
                parse_error = self.convert_script(script_file)

            if parse_error:
                self.log_error(parse_error)
                return False
            else:
                return True


        # Process all script files
        total_count = loaded_count = len(self.scripts) - 1

        if total_count > 0:
            self.server.amscript_log(f'[amscript v{constants.ams_version}] amscript is compiling, please wait...', 'info')

        for script in self.scripts:
            success = process_file(script)
            if not success:
                loaded_count -= 1

        # Report stats to console
        if total_count > 0:
            if loaded_count < total_count:
                self.server.amscript_log(f'Loaded ({loaded_count}/{total_count}) script(s): check errors above for more info', 'warning')

            elif loaded_count == 0:
                self.server.amscript_log(f'No scripts were loaded: check errors above for more info', 'error')

            else:
                self.server.amscript_log(f'Loaded ({loaded_count}/{total_count}) script(s) successfully!', 'success')

        return loaded_count, total_count


    # Deconstruct loaded .ams files
    def deconstruct(self):

        # Write persistent data before doing anything
        self.server_script_obj._persistent_config.write_config()

        self.enabled = False
        self.server_script_obj._running = False

        # Wait for tick time*2 for loops to stop
        time.sleep(0.1)
        del self.server_script_obj

        # Reset dicts in memory
        for key, item in self.function_dict.items():
            self.function_dict[key].clear()
            del item

        for key, item in self.src_dict.items():
            self.function_dict[key].clear()
            del item

        self.function_dict.clear()
        del self.function_dict
        self.function_dict = {}
        self.src_dict = {}
        self.aliases = {}
        gc.collect()


    # Runs specified event with parameters
    def call_event(self, event: str, args: tuple, delay=0):

        if self.function_dict and event in self.valid_events:
            for script in tuple(self.function_dict.items()):
                try:
                    for x, func in enumerate(script[1][event]):
                        if not self.enabled:
                            return

                        # s = script name, i = function index
                        def error_handler(s, i, *func_args):

                            # First, try and execute function
                            try:
                                func(*func_args)

                            # On failure, locate original code in file
                            except Exception as e:
                                ex_type, ex_value, ex_traceback = sys.exc_info()
                                parse_error = {}
                                original_code = ""
                                nested_func = False

                                # First, grab relative line number from modified code
                                tb = [item for item in traceback.format_exception(ex_type, ex_value, ex_traceback) if 'File "<string>"' in item][-1].strip()
                                try:
                                    line_num = int(re.search(r'(?<=,\sline\s)(.*)(?=,\sin)', tb).group(0))
                                except AttributeError:
                                    line_num = 0
                                    original_code = "Unknown"
                                else:

                                    # Try to locate event first
                                    try:
                                        # Locate original code from the source
                                        original_code = self.src_dict[s][event][i].splitlines()[line_num - 1]
                                        new_i = i

                                        # If alias, count if statements beforehand instead because it's one function
                                        if event == "@player.on_alias":
                                            new_i = ("\n".join(self.src_dict[s]['@player.on_alias'][i].splitlines()[:line_num]).count(f": #__{self.server_id}__")) - 1

                                        # Use the line to find the original line number from the source
                                        event_count = 0
                                        for n, line in enumerate(self.src_dict[s]['src'].splitlines(), 1):
                                            # print((original_code.strip(), line), (i+1, event_count))
                                            # print(n, line, event_count, i)

                                            if (original_code.strip() in line) and ((new_i + 1) == event_count):
                                                line_num = f'{n}:{len(line) - len(line.lstrip()) + 1}'
                                                break

                                            if line.startswith(event):
                                                event_count += 1
                                        else:
                                            nested_func = True

                                    # When error is not in an event, but in a nested function or library
                                    except IndexError:
                                        nested_func = True


                                    if nested_func:

                                        # Locate original code from source
                                        original_code = self.src_dict[s]['gbl'].splitlines()[line_num - 1]

                                        # Use the line to find the original line number from the source
                                        event_count = 0
                                        func_name = f'def {tb.split("in ")[1].strip()}('
                                        for n, line in enumerate(self.src_dict[s]['src'].splitlines(), 1):
                                            # print(n, line, event_count, i)

                                            if (original_code.strip() in line) and (event_count > 0):
                                                line_num = f'{n}:{len(line) - len(line.lstrip()) + 1}'
                                                break

                                            if line.startswith(func_name):
                                                event_count += 1


                                # Generate error dict
                                parse_error['file'] = s
                                parse_error['code'] = original_code.strip()
                                parse_error['line'] = line_num
                                parse_error['message'] = f"({ex_type.__name__}) {ex_value}"
                                parse_error['object'] = e
                                self.log_error(parse_error)

                        event_timer = Timer(delay, functools.partial(error_handler, script[0], x, *args))
                        event_timer.daemon = True
                        event_timer.start()


                except KeyError:
                    return


    # Logs error to console from generated error dict
    def log_error(self, error_dict: dict):
        # print(error_dict)
        self.server.amscript_log(f"Exception in '{error_dict['file']}': {error_dict['message']}", 'error')
        if error_dict['code'].startswith("from itertools import zip_longest") and error_dict['line'] == 1:
            return
        if error_dict['code'].startswith("Unknown") and error_dict['line'] == 0:
            return
        self.server.amscript_log(f"[Line {error_dict['line']}]  {error_dict['code']}", 'error')


    # ----------------------- Server Events ------------------------

    # Fires when server starts
    # {'date': date}
    def start_event(self, data):
        self.call_event('@server.on_start', (data))
        self.call_event('@server.on_loop', ())
        if constants.debug:
            print('server.on_start')
            print(data)

    # Fires when server starts
    # Eventually add return code to see if it crashed
    # {'date': date}
    def shutdown_event(self, data):
        self.server_script_obj._running = False
        self.call_event('@server.on_stop', (data))
        if constants.debug:
            print('server.on_stop')
            print(data)


    # ----------------------- Player Events ------------------------

    # Fires event when player joins the game
    # {'user': user, 'uuid': uuid, 'ip': ip_addr, 'date': date, 'logged-in': True}
    def join_event(self, player_obj):
        if player_obj['user'] not in self.server_script_obj.player_list:
            self.server_script_obj.player_list[player_obj['user']] = player_obj
            # print(self.server_script_obj.player_list)
            # print(self.server.run_data['player-list'])

        self.call_event('@player.on_join', (PlayerScriptObject(self.server_script_obj, player_obj['user'], _send_command=False), player_obj))

        if player_obj['user'] not in self.server_script_obj.usercache:
            try:
                self.server_script_obj.usercache[player_obj['user']] = player_obj['uuid']
            except KeyError:
                self.server_script_obj.usercache[player_obj['user']] = None

        if constants.debug:
            print('player.on_join')
            print(player_obj)

    # Fires when player leaves the game
    # {'user': user, 'uuid': uuid, 'ip': ip_addr, 'date': date, 'logged-in': False}
    def leave_event(self, player_obj):

        # Wait to process event to receive updated playerdata
        time.sleep(0.05)

        self.call_event('@player.on_leave', (PlayerScriptObject(self.server_script_obj, player_obj['user'], _send_command=False), player_obj))

        if player_obj['user'] in self.server_script_obj.player_list:
            del self.server_script_obj.player_list[player_obj['user']]
            # print(self.server_script_obj.player_list)
            # print(self.server.run_data['player-list'])

        if constants.debug:
            print('player.on_leave')
            print(player_obj)

    # Fires event when message/cmd is sent
    # {'user': player, 'content': message}
    def message_event(self, msg_obj):
        msg_obj['content'] = msg_obj['content'].replace("&bl;", "[").replace("&br;", "]")
        if msg_obj['content'].strip().split(" ",1)[0].strip() in self.aliases.keys():
            self.alias_event(msg_obj)
        elif msg_obj['content'].startswith('!'):
            player = PlayerScriptObject(self.server_script_obj, msg_obj['user'])
            message = 'Unknown command. Type "!help" for a list of commands.'
            if player.is_server:
                self.server_script_obj.log(message)
            else:
                player.log_error(message)
        elif msg_obj['user'] != self.server_id:
            self.call_event('@player.on_message', (PlayerScriptObject(self.server_script_obj, msg_obj['user']), msg_obj['content']))

            if constants.debug:
                print('player.on_message')
                print(msg_obj)

    # Fires event when a player dies
    # {'user': player, 'content': message}
    def death_event(self, msg_obj):
        if msg_obj['user'] != self.server_id:
            enemy = None

            # Attempt to find attacker if player was killed by another player
            for word in reversed(msg_obj['content'].split(' ')):
                if word.strip() != msg_obj['user'] and word.strip() in self.server.run_data['player-list']:
                    enemy = PlayerScriptObject(self.server_script_obj, word.strip())
                    break

            self.call_event('@player.on_death', (PlayerScriptObject(self.server_script_obj, msg_obj['user']), enemy, msg_obj['content']))

            print('player.on_death')
            print(msg_obj)

    # Fires event when player sends a command alias
    # {'user': player, 'content': message}
    def alias_event(self, player_obj):
        self.server.acl.reload_list('ops')
        # print([rule.rule for rule in self.server.acl.rules['ops']])
        if player_obj['user'] == self.server_id:
            permission = 'server'
        elif self.server.acl.rule_in_acl(player_obj['user'], 'ops'):
            permission = 'op'
        else:
            permission = 'anyone'

        self.call_event('@player.on_alias', (PlayerScriptObject(self.server_script_obj, player_obj['user']), player_obj['content'], permission))

        print('player.on_alias')
        print(player_obj)


# Reconfigured ServerObject to be passed in as 'server' variable to amscripts
class ServerScriptObject():
    def __init__(self, server_obj):
        self._running = True

        # Data to be used internally, don't use these in user scripts
        self._server_id = ("#" + server_obj._hash)
        self._ams_log = server_obj.amscript_log
        self._reload_scripts = server_obj.reload_scripts
        self._ams_info = server_obj.get_ams_info()
        self._persistent_config = PersistenceManager(server_obj.name)
        self._app_version = constants.app_version
        self._script_state = server_obj.script_manager.script_state

        # Assign callable functions from main server object
        self.execute = server_obj.silent_command
        self.restart = server_obj.restart
        self.stop = server_obj.stop
        self.log = server_obj.send_log
        self.aliases = {}
        self.ams_version = constants.ams_version

        # Properties
        self.name = server_obj.name
        self.version = server_obj.version
        self.build = server_obj.build
        self.type = server_obj.type
        self.world = server_obj.world if server_obj.world else 'world'
        self.directory = server_obj.server_path
        self.properties = server_obj.server_properties
        self.persistent = self._persistent_config._data.server

        if server_obj.run_data:
            self._performance = server_obj.run_data['performance']
            self.player_list = deepcopy(server_obj.run_data['player-list'])
            self.network = server_obj.run_data['network']['address']
        else:
            self._performance = {}
            self.player_list = {}
            self.network = {'ip': None, 'port': None}

        # Load usercache
        try:
            self.usercache = {}
            with open(os.path.join(self.directory, 'usercache.json'), 'r') as f:
                file = json.load(f)
                for item in file:
                    try:
                        self.usercache[item['name']] = item['uuid']
                    except KeyError:
                        self.usercache[item['name']] = None
        except:
            pass

    def __del__(self):
        self._running = False

    # If self is printed, show string of server name instead
    def __str__(self):
        return self.name

    # Overrides comparison to return string instead
    def __eq__(self, comp):
        return self.name == comp

    # Logging functions
    def log_warning(self, msg):
        self.log(msg, log_type='warning')
    def log_error(self, msg):
        self.log(msg, log_type='error')
    def log_success(self, msg):
        self.log(msg, log_type='success')

    # Version check
    def version_check(self, operand, version):
        return constants.version_check(self.version, operand, version)

    # Returns PlayerScriptObject that matches selector
    def get_player(self, tag):

        # First check if there's a user selector
        if tag.startswith("@p") or tag.startswith("@r"):
            user = None

            if self.version_check(">", "1.13"):
                try:
                    log_data = self.execute(f'data get entity {tag}', log=False, _capture=f" has the following entity data: ", _send_twice=True)
                    user = log_data.split(" has the following entity data: ")[0].rsplit(":",1)[1].strip()
                except:
                    user = None

            elif self.version_check(">=", "1.8") and self.version_check("<", "1.13"):
                try:
                    log_data = self.execute(f'execute {tag} ~ ~ ~ tp @p ~ ~ ~', log=False, _capture=f"Teleported ", _send_twice=True)
                    user = log_data.split("Teleported ")[1].split(" to")[0].strip()
                except:
                    user = None

            if user:
                tag = user
            else:
                return None

        # Then check if username is in player list
        if tag in self.player_list:
            obj = PlayerScriptObject(self, tag, _get_player=True)

        else:
            obj = None

        return obj


# Reconfigured ServerObject to be passed in as 'player' variable to amscript events
class PlayerScriptObject():
    def __init__(self, server_script_obj: ServerScriptObject, player_name: str, _get_player=False, _send_command=True):
        self._get_player = _get_player
        self._send_command = _send_command
        self._server = server_script_obj
        self._server_id = server_script_obj._server_id
        self._execute = server_script_obj.execute
        self._version_check = server_script_obj.version_check
        self._world_path = os.path.join(server_script_obj.directory, server_script_obj.world)


        # If this object is the console
        self.is_server = (player_name == self._server_id)

        if not self.is_server:
            player_info = server_script_obj.player_list[player_name]
            self.uuid = player_info['uuid']
            self.ip_address = player_info['ip'].split(":")[0]
        else:
            self.uuid = ''
            self.ip_address = server_script_obj.network['ip']

        # Properties
        self.name = player_name

        # NBT data
        self.position = CoordinateObject({'x': None, 'y': None, 'z': None})
        self.rotation = CoordinateObject({'x': None, 'y': None})
        self.motion = CoordinateObject({'x': None, 'y': None, 'z': None})
        self.spawn_position = CoordinateObject({'x': None, 'y': None, 'z': None})
        self.health = 0
        self.hunger_level = 0
        self.gamemode = "None"
        self.xp = 0
        self.on_fire = False
        self.is_flying = False
        self.is_sleeping = False
        self.is_drowning = False
        self.hurt_time = 0
        self.death_time = 0
        self.dimension = "None"
        self.active_effects = {}
        self.inventory = InventoryObject(None, None)

        # Persistent config
        if self.is_server:
            self.persistent = server_script_obj._persistent_config._data.server
        elif self.uuid:
            try:
                self.persistent = server_script_obj._persistent_config._data.player[self.uuid]
            except KeyError:
                server_script_obj._persistent_config._data.player[self.uuid] = {}
                self.persistent = server_script_obj._persistent_config._data.player[self.uuid]
        else:
            try:
                self.persistent = server_script_obj._persistent_config._data.player[self.name]
            except KeyError:
                server_script_obj._persistent_config._data.player[self.name] = {}
                self.persistent = server_script_obj._persistent_config._data.player[self.name]

        if not self.is_server:
            self._get_nbt()

    def __hash__(self):
        return hash(self.name)

    # If self is printed, show string of username instead
    def __str__(self):
        return self.name

    # Overrides comparison to return string instead
    def __eq__(self, comp):
        return self.name == comp

    # Overrides comparison to return string instead
    def __neq__(self, comp):
        return self.name != comp

    # Grabs latest player NBT data
    def _get_nbt(self):
        log_data = None
        new_nbt = None

        # If newer version, use "/data get" to gather updated playerdata
        if self._version_check(">", "1.13"):

            # Attempt to intercept player's entity data
            try:
                if not self._send_command:
                    try:
                        new_nbt = nbt.NBTFile(os.path.join(self._world_path, 'playerdata', f'{self.uuid}.dat'), 'rb')
                    except FileNotFoundError:
                        return None
                    except PermissionError:
                        return None
                    try:
                        self.position = CoordinateObject({'x': fmt(new_nbt['Pos'][0]), 'y': fmt(new_nbt['Pos'][1]), 'z': fmt(new_nbt['Pos'][2])})
                    except:
                        pass

                    try:
                        self.rotation = CoordinateObject(
                            {'x': fmt(new_nbt['Rotation'][0]), 'y': fmt(new_nbt['Rotation'][1])})
                    except:
                        pass

                    try:
                        self.motion = CoordinateObject({'x': fmt(new_nbt['Motion'][0]), 'y': fmt(new_nbt['Motion'][1]), 'z': fmt(new_nbt['Motion'][2])})
                    except:
                        pass

                    try:
                        self.spawn_position = CoordinateObject(
                            {'x': fmt(new_nbt['SpawnX']), 'y': fmt(new_nbt['SpawnY']), 'z': fmt(new_nbt['SpawnZ'])})
                    except:
                        pass

                    try:
                        self.health = int(new_nbt['Health'].value)
                    except:
                        pass

                    try:
                        self.hunger_level = int(new_nbt['foodLevel'].value)
                    except:
                        pass

                    try:
                        self.gamemode = ['survival', 'creative', 'adventure', 'spectator'][
                            int(new_nbt['playerGameType'].value)]
                    except:
                        pass

                    try:
                        self.xp = round(float(new_nbt['XpLevel'].value) + float(new_nbt['XpP'].value), 3)
                    except:
                        pass

                    try:
                        self.hurt_time = int(new_nbt['HurtTime'].value)
                    except:
                        pass

                    try:
                        self.death_time = int(new_nbt['DeathTime'].value)
                    except:
                        pass

                    try:
                        self.on_fire = (int(new_nbt['Fire'].value) > 0)
                    except:
                        pass

                    try:
                        self.is_flying = (int(new_nbt['abilities']['flying'].value) == 1)
                    except:
                        pass

                    try:
                        self.is_sleeping = (int(new_nbt['Sleeping'].value) == 1)
                    except:
                        pass

                    try:
                        self.is_drowning = (int(new_nbt['Air'].value) < 1)
                    except:
                        pass

                    try:
                        self.dimension = {0: 'overworld', -1: 'the_nether', 1: 'the_end'}.get(int(new_nbt['Dimension'].value), int(new_nbt['Dimension'].value)).replace('minecraft:', '')
                    except:
                        pass

                    try:
                        self.active_effects = {
                            id_dict['effect'].get(item[3].value, item[3].value).replace('minecraft:', ''): EffectObject({'id': item[3].value, 'amplitude': int(item[4].value), 'duration': int(item[2].value), 'show_particles': (item[1].value == 1)}, name=id_dict['effect'].get(item[3].value, item[3].value).replace('minecraft:', '')) for item in new_nbt['ActiveEffects'].tags}
                    except:
                        pass

                    try:
                        try:
                            selected_item = (new_nbt['SelectedItem'], int(new_nbt['SelectedItemSlot'].value))
                        except KeyError:
                            selected_item = None
                        self.inventory = InventoryObject(new_nbt['Inventory'], selected_item)
                    except:
                        pass
                else:
                    log_data = self._execute(f'data get entity {self.name}', log=False, _capture=f"{self.name} has the following entity data: ", _send_twice=self._get_player)
                    nbt_data = log_data.split("following entity data: ")[1].strip()
                    # print(log_data)

                    # Make sure that strings are escaped with quotes, and json quotes are escaped with \"
                    try:
                        new_nbt = re.sub(r'(:?"[^"]*")|([A-Za-z_\-\d.?\d]\w*\.*\d*\w*)', lambda x: json_regex(x), nbt_data).replace(";",",").replace("'{", '"{').replace("}'", '}"')
                        new_nbt = json.loads(re.sub(r'(?<="{)(.*?)(?=}")', lambda x: x.group(1).replace('"', '\\"'), new_nbt))
                    except json.decoder.JSONDecodeError:
                        if constants.debug:
                            print('Failed to process NBT data')
                        pass

            # If log doesn't contain entity content, revert NBT
            except IndexError:
                pass

            # Process NBT if there's no error
            else:
                try:
                    self.position = CoordinateObject({'x': new_nbt['pos'][0], 'y': new_nbt['pos'][1], 'z': new_nbt['pos'][2]})
                except:
                    pass

                try:
                    self.rotation = CoordinateObject({'x': new_nbt['rotation'][0], 'y': new_nbt['rotation'][1]})
                except:
                    pass

                try:
                    self.motion = CoordinateObject({'x': new_nbt['motion'][0], 'y': new_nbt['motion'][1], 'z': new_nbt['motion'][2]})
                except:
                    pass

                try:
                    self.spawn_position = CoordinateObject({'x': new_nbt['spawnx'], 'y': new_nbt['spawny'], 'z': new_nbt['spawnz']})
                except:
                    pass

                try:
                    self.health = int(new_nbt['health'])
                except:
                    pass

                try:
                    self.hunger_level = int(new_nbt['foodlevel'])
                except:
                    pass

                try:
                    self.gamemode = ['survival', 'creative', 'adventure', 'spectator'][int(new_nbt['playergametype'])]
                except:
                    pass

                try:
                    self.xp = round(float(new_nbt['xplevel']) + float(new_nbt['xpp']), 3)
                except:
                    pass

                try:
                    self.on_fire = (int(new_nbt['fire']) > 0)
                except:
                    pass

                try:
                    self.is_flying = (int(new_nbt['abilities']['flying']) == 1)
                except:
                    pass

                try:
                    self.is_sleeping = (int(new_nbt['sleeptimer']) > 0)
                except:
                    pass

                try:
                    self.is_drowning = (int(new_nbt['air']) < 1)
                except:
                    pass

                try:
                    self.hurt_time = int(new_nbt['hurttime'])
                except:
                    pass

                try:
                    self.death_time = int(new_nbt['deathtime'])
                except:
                    pass

                try:
                    self.dimension = str(new_nbt['dimension']).replace('minecraft:','')
                except:
                    pass

                try:
                    self.active_effects = {id_dict['effect'].get(item['id'], item['id']).replace('minecraft:',''): EffectObject(item, name=id_dict['effect'].get(item['id'], item['id']).replace('minecraft:','')) for item in new_nbt['activeeffects']}
                except:
                    pass

                try:
                    try:
                        selected_item = (new_nbt['selecteditem'], int(new_nbt['selecteditemslot']))
                    except KeyError:
                        selected_item = None
                    self.inventory = InventoryObject(new_nbt['inventory'], selected_item)
                except:
                    pass


        # If pre-1.12, get outdated playerdata from the user's .dat file but updated pos
        else:
            try:
                if self._version_check(">=", "1.8") and self._version_check("<", "1.13"):
                    if self._send_command:
                        log_data = self._execute(f'execute {self.name} ~ ~ ~ tp {self.name} ~ ~ ~', log=False, _capture=f"Teleported {self.name} to ", _send_twice=self._get_player)
                    try:
                        new_nbt = nbt.NBTFile(os.path.join(self._world_path, 'playerdata', f'{self.uuid}.dat'), 'rb')
                    except FileNotFoundError:
                        return None

                # Pre-1.8, get outdated playerdata from the user's .dat file
                else:
                    new_nbt = nbt.NBTFile(os.path.join(self._world_path, 'players', f'{self.name}.dat'), 'rb')

            except OSError:
                pass

            # Process NBT if there's no error
            else:
                try:
                    if log_data:
                        coords = [round(float(pos.strip()), 4) for pos in log_data.split(f"Teleported {self.name} to ")[1].split(",")]
                        self.position = CoordinateObject({'x': coords[0], 'y': coords[1], 'z': coords[2]})
                    else:
                        self.position = CoordinateObject({'x': fmt(new_nbt['Pos'][0]), 'y': fmt(new_nbt['Pos'][1]), 'z': fmt(new_nbt['Pos'][2])})
                except:
                    pass

                try:
                    self.rotation = CoordinateObject({'x': fmt(new_nbt['Rotation'][0]), 'y': fmt(new_nbt['Rotation'][1])})
                except:
                    pass

                try:
                    self.motion = CoordinateObject({'x': fmt(new_nbt['Motion'][0]), 'y': fmt(new_nbt['Motion'][1]), 'z': fmt(new_nbt['Motion'][2])})
                except:
                    pass

                try:
                    self.spawn_position = CoordinateObject({'x': fmt(new_nbt['SpawnX']), 'y': fmt(new_nbt['SpawnY']), 'z': fmt(new_nbt['SpawnZ'])})
                except:
                    pass

                try:
                    self.health = int(new_nbt['Health'].value)
                except:
                    pass

                try:
                    self.hunger_level = int(new_nbt['foodLevel'].value)
                except:
                    pass

                try:
                    self.gamemode = ['survival', 'creative', 'adventure', 'spectator'][int(new_nbt['playerGameType'].value)]
                except:
                    pass

                try:
                    self.xp = round(float(new_nbt['XpLevel'].value) + float(new_nbt['XpP'].value), 3)
                except:
                    pass

                try:
                    self.hurt_time = int(new_nbt['HurtTime'].value)
                except:
                    pass

                try:
                    self.death_time = int(new_nbt['DeathTime'].value)
                except:
                    pass

                try:
                    self.on_fire = (int(new_nbt['Fire'].value) > 0)
                except:
                    pass

                try:
                    self.is_flying = (int(new_nbt['abilities']['flying'].value) == 1)
                except:
                    pass

                try:
                    self.is_sleeping = (int(new_nbt['Sleeping'].value) == 1)
                except:
                    pass

                try:
                    self.is_drowning = (int(new_nbt['Air'].value) < 1)
                except:
                    pass

                try:
                    self.dimension = {0: 'overworld', -1: 'the_nether', 1: 'the_end'}.get(int(new_nbt['Dimension'].value), int(new_nbt['Dimension'].value)).replace('minecraft:','')
                except:
                    pass

                try:
                    self.active_effects = {id_dict['effect'].get(item[3].value, item[3].value).replace('minecraft:',''): EffectObject({'id': item[3].value, 'amplitude': int(item[4].value), 'duration': int(item[2].value), 'show_particles': (item[1].value == 1)}, name=id_dict['effect'].get(item[3].value, item[3].value).replace('minecraft:','')) for item in new_nbt['ActiveEffects'].tags}
                except:
                    pass

                try:
                    try:
                        selected_item = (new_nbt['SelectedItem'], int(new_nbt['SelectedItemSlot'].value))
                    except KeyError:
                        selected_item = None
                    self.inventory = InventoryObject(new_nbt['Inventory'], selected_item)
                except:
                    pass


        # Eventually process this to object data
        # print(new_nbt)

    # Set custom player permissions
    def set_permission(self, permission, enable=True):
        try:
            permissions = self.persistent['__permissions__']
        except KeyError:
            self.persistent['__permissions__'] = {}

        self.persistent['__permissions__'][permission] = enable

    # Check custom player permissions
    def check_permission(self, permission):
        if self.is_server:
            return True
        else:
            try:
                return self.persistent['__permissions__'][permission]
            except KeyError:
                return False

    # Logging functions
    # Version compatible message system for local player object
    def log(self, msg, color="gray", style='italic', tag=False):
        if not msg:
            return

        msg = str(msg)
        if tag and not self.is_server:
            msg = f'[auto-mcs] {msg}'

        style = 'normal' if style not in ('normal', 'italic', 'bold', 'strikethrough', 'obfuscated', 'underlined') else style

        # Use /tellraw if it's supported, else /tell
        if constants.version_check(str(self._server.version), '>=', '1.7.2') and not self.is_server:
            msg = f'/tellraw {self.name} {{"text": {json.dumps(msg)}, "color": "{color}"}}'
            if style != 'normal':
                msg = msg[:-1] + f', "{style}": true}}'
            self._server.execute(msg, log=False)

        # Pre 1.7.2
        else:
            color_table = {
                'dark_red': '§4',
                'red': '§c',
                'gold': '§6',
                'yellow': '§e',
                'dark_green': '§2',
                'green': '§a',
                'aqua': '§b',
                'dark_aqua': '§3',
                'dark_blue': '§1',
                'blue': '§9',
                'light_purple': '§d',
                'dark_purple': '§5',
                'white': '§f',
                'gray': '§7',
                'dark_gray': '§8',
                'black': '§0'
            }
            style_table = {
                'obfuscated': '§k',
                'bold': '§l',
                'underlined': '§n',
                'strikethrough': '§m',
                'italic': '§o'
            }
            final_code = ''

            if color in list(color_table.keys()):
                final_code += color_table[color]

            # If user is server, send to server instead
            if self.is_server:
                msg = f'{final_code}{("§r " + final_code).join(msg.rstrip().split(" "))}§r'
                self._server.log(msg)
            else:
                if style != 'normal':
                    final_code += style_table[style]
                msg = f'/tell {self.name} {final_code}{("§r "+final_code).join(msg.rstrip().split(" "))}§r'
                self._server.execute(msg, log=False)
    def log_warning(self, msg, tag=False):
        self.log(msg, "gold", "normal", tag=tag)
    def log_error(self, msg, tag=False):
        self.log(msg, "red", "normal", tag=tag)
    def log_success(self, msg, tag=False):
        self.log(msg, "green", "normal", tag=tag)



# --------------------------------------------- General Functions ------------------------------------------------------

# Conversion dict for effect IDs
json_name = "ams-conf.json"
id_dict = {
    'effect': {
        1:  'speed',
        2:  'slowness',
        3:  'haste',
        4:  'mining_fatigue',
        5:  'strength',
        6:  'instant_health',
        7:  'instant_damage',
        8:  'jump_boost',
        9:  'nausea',
        10: 'regeneration',
        11: 'resistance',
        12: 'fire_resistance',
        13: 'water_breathing',
        14: 'invisibility',
        15: 'blindness',
        16: 'night_vision',
        17: 'hunger',
        18: 'weakness',
        19: 'poison',
        20: 'wither',
        21: 'health_boost',
        22: 'absorption',
        23: 'saturation',
        24: 'glowing',
        25: 'levitation',
        26: 'luck',
        27: 'unluck',
        28: 'slow_falling',
        29: 'conduit_power',
        30: 'dolphins_grace',
        31: 'bad_omen',
        32: 'hero_of_the_village',
        33: 'darkness',
        34: 'big',
        35: 'small'
    },
    'enchant': {
        0:  'protection',
        1:  'fire_protection',
        2:  'feather_falling',
        3:  'blast_protection',
        4:  'projectile_protection',
        5:  'respiration',
        6:  'aqua_affinity',
        7:  'thorns',
        8:  'depth_strider',
        10: 'binding_curse',
        16: 'sharpness',
        17: 'smite',
        18: 'bane_of_arthropods',
        19: 'knockback',
        20: 'fire_aspect',
        21: 'looting',
        22: 'sweeping',
        32: 'efficiency',
        33: 'silk_touch',
        34: 'unbreaking',
        35: 'fortune',
        48: 'power',
        49: 'punch',
        50: 'flame',
        51: 'infinity',
        61: 'luck_of_the_sea',
        62: 'lure',
        65: 'loyalty',
        66: 'impaling',
        67: 'riptide',
        68: 'channeling',
        70: 'mending',
        71: 'vanishing_curse'
    },
    'items': {
        0:    'minecraft:air',
        1:    'minecraft:stone',
        2:    'minecraft:grass',
        3:    'minecraft:dirt',
        4:    'minecraft:cobblestone',
        5:    'minecraft:planks',
        6:    'minecraft:sapling',
        7:    'minecraft:bedrock',
        8:    'minecraft:flowing_water',
        9:    'minecraft:water',
        10:   'minecraft:flowing_lava',
        11:   'minecraft:lava',
        12:   'minecraft:sand',
        13:   'minecraft:gravel',
        14:   'minecraft:gold_ore',
        15:   'minecraft:iron_ore',
        16:   'minecraft:coal_ore',
        17:   'minecraft:log',
        18:   'minecraft:leaves',
        19:   'minecraft:sponge',
        20:   'minecraft:glass',
        21:   'minecraft:lapis_ore',
        22:   'minecraft:lapis_block',
        23:   'minecraft:dispenser',
        24:   'minecraft:sandstone',
        25:   'minecraft:noteblock',
        26:   'minecraft:bed',
        27:   'minecraft:golden_rail',
        28:   'minecraft:detector_rail',
        29:   'minecraft:sticky_piston',
        30:   'minecraft:web',
        31:   'minecraft:tallgrass',
        32:   'minecraft:deadbush',
        33:   'minecraft:piston',
        34:   'minecraft:piston_head',
        35:   'minecraft:wool',
        37:   'minecraft:yellow_flower',
        38:   'minecraft:red_flower',
        39:   'minecraft:brown_mushroom',
        40:   'minecraft:red_mushroom',
        41:   'minecraft:gold_block',
        42:   'minecraft:iron_block',
        43:   'minecraft:double_stone_slab',
        44:   'minecraft:stone_slab',
        45:   'minecraft:brick_block',
        46:   'minecraft:tnt',
        47:   'minecraft:bookshelf',
        48:   'minecraft:mossy_cobblestone',
        49:   'minecraft:obsidian',
        50:   'minecraft:torch',
        51:   'minecraft:fire',
        52:   'minecraft:mob_spawner',
        53:   'minecraft:oak_stairs',
        54:   'minecraft:chest',
        55:   'minecraft:redstone_wire',
        56:   'minecraft:diamond_ore',
        57:   'minecraft:diamond_block',
        58:   'minecraft:crafting_table',
        59:   'minecraft:wheat',
        60:   'minecraft:farmland',
        61:   'minecraft:furnace',
        62:   'minecraft:lit_furnace',
        63:   'minecraft:standing_sign',
        64:   'minecraft:wooden_door',
        65:   'minecraft:ladder',
        66:   'minecraft:rail',
        67:   'minecraft:stone_stairs',
        68:   'minecraft:wall_sign',
        69:   'minecraft:lever',
        70:   'minecraft:stone_pressure_plate',
        71:   'minecraft:iron_door',
        72:   'minecraft:wooden_pressure_plate',
        73:   'minecraft:redstone_ore',
        74:   'minecraft:lit_redstone_ore',
        75:   'minecraft:unlit_redstone_torch',
        76:   'minecraft:redstone_torch',
        77:   'minecraft:stone_button',
        78:   'minecraft:snow_layer',
        79:   'minecraft:ice',
        80:   'minecraft:snow',
        81:   'minecraft:cactus',
        82:   'minecraft:clay',
        83:   'minecraft:reeds',
        84:   'minecraft:jukebox',
        85:   'minecraft:fence',
        86:   'minecraft:pumpkin',
        87:   'minecraft:netherrack',
        88:   'minecraft:soul_sand',
        89:   'minecraft:glowstone',
        90:   'minecraft:portal',
        91:   'minecraft:lit_pumpkin',
        92:   'minecraft:cake',
        93:   'minecraft:unpowered_repeater',
        94:   'minecraft:powered_repeater',
        95:   'minecraft:stained_glass',
        96:   'minecraft:trapdoor',
        97:   'minecraft:monster_egg',
        98:   'minecraft:stonebrick',
        99:   'minecraft:brown_mushroom_block',
        100:  'minecraft:red_mushroom_block',
        101:  'minecraft:iron_bars',
        102:  'minecraft:glass_pane',
        103:  'minecraft:melon_block',
        104:  'minecraft:pumpkin_stem',
        105:  'minecraft:melon_stem',
        106:  'minecraft:vine',
        107:  'minecraft:fence_gate',
        108:  'minecraft:brick_stairs',
        109:  'minecraft:stone_brick_stairs',
        110:  'minecraft:mycelium',
        111:  'minecraft:waterlily',
        112:  'minecraft:nether_brick',
        113:  'minecraft:nether_brick_fence',
        114:  'minecraft:nether_brick_stairs',
        115:  'minecraft:nether_wart',
        116:  'minecraft:enchanting_table',
        117:  'minecraft:brewing_stand',
        118:  'minecraft:cauldron',
        119:  'minecraft:end_portal',
        120:  'minecraft:end_portal_frame',
        121:  'minecraft:end_stone',
        122:  'minecraft:dragon_egg',
        123:  'minecraft:redstone_lamp',
        124:  'minecraft:lit_redstone_lamp',
        125:  'minecraft:double_wooden_slab',
        126:  'minecraft:wooden_slab',
        127:  'minecraft:cocoa',
        128:  'minecraft:sandstone_stairs',
        129:  'minecraft:emerald_ore',
        130:  'minecraft:ender_chest',
        131:  'minecraft:tripwire_hook',
        132:  'minecraft:tripwire_hook',
        133:  'minecraft:emerald_block',
        134:  'minecraft:spruce_stairs',
        135:  'minecraft:birch_stairs',
        136:  'minecraft:jungle_stairs',
        137:  'minecraft:command_block',
        138:  'minecraft:beacon',
        139:  'minecraft:cobblestone_wall',
        140:  'minecraft:flower_pot',
        141:  'minecraft:carrots',
        142:  'minecraft:potatoes',
        143:  'minecraft:wooden_button',
        144:  'minecraft:skull',
        145:  'minecraft:anvil',
        146:  'minecraft:trapped_chest',
        147:  'minecraft:light_weighted_pressure_plate',
        148:  'minecraft:heavy_weighted_pressure_plate',
        149:  'minecraft:unpowered_comparator',
        150:  'minecraft:powered_comparator',
        151:  'minecraft:daylight_detector',
        152:  'minecraft:redstone_block',
        153:  'minecraft:quartz_ore',
        154:  'minecraft:hopper',
        155:  'minecraft:quartz_block',
        156:  'minecraft:quartz_stairs',
        157:  'minecraft:activator_rail',
        158:  'minecraft:dropper',
        159:  'minecraft:stained_hardened_clay',
        160:  'minecraft:stained_glass_pane',
        161:  'minecraft:leaves2',
        162:  'minecraft:log2',
        163:  'minecraft:acacia_stairs',
        164:  'minecraft:dark_oak_stairs',
        165:  'minecraft:slime',
        166:  'minecraft:barrier',
        167:  'minecraft:iron_trapdoor',
        168:  'minecraft:prismarine',
        169:  'minecraft:sea_lantern',
        170:  'minecraft:hay_block',
        171:  'minecraft:carpet',
        172:  'minecraft:hardened_clay',
        173:  'minecraft:coal_block',
        174:  'minecraft:packed_ice',
        175:  'minecraft:double_plant',
        176:  'minecraft:standing_banner',
        177:  'minecraft:wall_banner',
        178:  'minecraft:daylight_detector_inverted',
        179:  'minecraft:red_sandstone',
        180:  'minecraft:red_sandstone_stairs',
        181:  'minecraft:double_stone_slab2',
        182:  'minecraft:stone_slab2',
        183:  'minecraft:spruce_fence_gate',
        184:  'minecraft:birch_fence_gate',
        185:  'minecraft:jungle_fence_gate',
        186:  'minecraft:dark_oak_fence_gate',
        187:  'minecraft:acacia_fence_gate',
        188:  'minecraft:spruce_fence',
        189:  'minecraft:birch_fence',
        190:  'minecraft:jungle_fence',
        191:  'minecraft:dark_oak_fence',
        192:  'minecraft:acacia_fence',
        193:  'minecraft:spruce_door',
        194:  'minecraft:birch_door',
        195:  'minecraft:jungle_door',
        196:  'minecraft:acacia_door',
        197:  'minecraft:dark_oak_door',
        198:  'minecraft:end_rod',
        199:  'minecraft:chorus_plant',
        200:  'minecraft:chorus_flower',
        201:  'minecraft:purpur_block',
        202:  'minecraft:purpur_pillar',
        203:  'minecraft:purpur_stairs',
        204:  'minecraft:purpur_double_slab',
        205:  'minecraft:purpur_slab',
        206:  'minecraft:end_bricks',
        207:  'minecraft:beetroots',
        208:  'minecraft:grass_path',
        209:  'minecraft:end_gateway',
        210:  'minecraft:repeating_command_block',
        211:  'minecraft:chain_command_block',
        212:  'minecraft:frosted_ice',
        213:  'minecraft:magma',
        214:  'minecraft:nether_wart_block',
        215:  'minecraft:red_nether_brick',
        216:  'minecraft:bone_block',
        217:  'minecraft:structure_void',
        218:  'minecraft:observer',
        219:  'minecraft:white_shulker_box',
        220:  'minecraft:orange_shulker_box',
        221:  'minecraft:magenta_shulker_box',
        222:  'minecraft:light_blue_shulker_box',
        223:  'minecraft:yellow_shulker_box',
        224:  'minecraft:lime_shulker_box',
        225:  'minecraft:pink_shulker_box',
        226:  'minecraft:gray_shulker_box',
        227:  'minecraft:silver_shulker_box',
        228:  'minecraft:cyan_shulker_box',
        229:  'minecraft:purple_shulker_box',
        230:  'minecraft:blue_shulker_box',
        231:  'minecraft:brown_shulker_box',
        232:  'minecraft:green_shulker_box',
        233:  'minecraft:red_shulker_box',
        234:  'minecraft:black_shulker_box',
        235:  'minecraft:white_glazed_terracotta',
        236:  'minecraft:orange_glazed_terracotta',
        237:  'minecraft:magenta_glazed_terracotta',
        238:  'minecraft:light_blue_glazed_terracotta',
        239:  'minecraft:yellow_glazed_terracotta',
        240:  'minecraft:lime_glazed_terracotta',
        241:  'minecraft:pink_glazed_terracotta',
        242:  'minecraft:gray_glazed_terracotta',
        243:  'minecraft:light_gray_glazed_terracotta',
        244:  'minecraft:cyan_glazed_terracotta',
        245:  'minecraft:purple_glazed_terracotta',
        246:  'minecraft:blue_glazed_terracotta',
        247:  'minecraft:brown_glazed_terracotta',
        248:  'minecraft:green_glazed_terracotta',
        249:  'minecraft:red_glazed_terracotta',
        250:  'minecraft:black_glazed_terracotta',
        251:  'minecraft:concrete',
        252:  'minecraft:concrete_powder',
        255:  'minecraft:structure_block',
        256:  'minecraft:iron_shovel',
        257:  'minecraft:iron_pickaxe',
        258:  'minecraft:iron_axe',
        259:  'minecraft:flint_and_steel',
        260:  'minecraft:apple',
        261:  'minecraft:bow',
        262:  'minecraft:arrow',
        263:  'minecraft:coal',
        264:  'minecraft:diamond',
        265:  'minecraft:iron_ingot',
        266:  'minecraft:gold_ingot',
        267:  'minecraft:iron_sword',
        268:  'minecraft:wooden_sword',
        269:  'minecraft:wooden_shovel',
        270:  'minecraft:wooden_pickaxe',
        271:  'minecraft:wooden_axe',
        272:  'minecraft:stone_sword',
        273:  'minecraft:stone_shovel',
        274:  'minecraft:stone_pickaxe',
        275:  'minecraft:stone_axe',
        276:  'minecraft:diamond_sword',
        277:  'minecraft:diamond_shovel',
        278:  'minecraft:diamond_pickaxe',
        279:  'minecraft:diamond_axe',
        280:  'minecraft:stick',
        281:  'minecraft:bowl',
        282:  'minecraft:mushroom_stew',
        283:  'minecraft:golden_sword',
        284:  'minecraft:golden_shovel',
        285:  'minecraft:golden_pickaxe',
        286:  'minecraft:golden_axe',
        287:  'minecraft:string',
        288:  'minecraft:feather',
        289:  'minecraft:gunpowder',
        290:  'minecraft:wooden_hoe',
        291:  'minecraft:stone_hoe',
        292:  'minecraft:iron_hoe',
        293:  'minecraft:diamond_hoe',
        294:  'minecraft:golden_hoe',
        295:  'minecraft:wheat_seeds',
        296:  'minecraft:wheat',
        297:  'minecraft:bread',
        298:  'minecraft:leather_helmet',
        299:  'minecraft:leather_chestplate',
        300:  'minecraft:leather_leggings',
        301:  'minecraft:leather_boots',
        302:  'minecraft:chainmail_helmet',
        303:  'minecraft:chainmail_chestplate',
        304:  'minecraft:chainmail_leggings',
        305:  'minecraft:chainmail_boots',
        306:  'minecraft:iron_helmet',
        307:  'minecraft:iron_chestplate',
        308:  'minecraft:iron_leggings',
        309:  'minecraft:iron_boots',
        310:  'minecraft:diamond_helmet',
        311:  'minecraft:diamond_chestplate',
        312:  'minecraft:diamond_leggings',
        313:  'minecraft:diamond_boots',
        314:  'minecraft:golden_helmet',
        315:  'minecraft:golden_chestplate',
        316:  'minecraft:golden_leggings',
        317:  'minecraft:golden_boots',
        318:  'minecraft:flint',
        319:  'minecraft:porkchop',
        320:  'minecraft:cooked_porkchop',
        321:  'minecraft:painting',
        322:  'minecraft:golden_apple',
        323:  'minecraft:sign',
        324:  'minecraft:wooden_door',
        325:  'minecraft:bucket',
        326:  'minecraft:water_bucket',
        327:  'minecraft:lava_bucket',
        328:  'minecraft:minecart',
        329:  'minecraft:saddle',
        330:  'minecraft:iron_door',
        331:  'minecraft:redstone',
        332:  'minecraft:snowball',
        333:  'minecraft:boat',
        334:  'minecraft:leather',
        335:  'minecraft:milk_bucket',
        336:  'minecraft:brick',
        337:  'minecraft:clay_ball',
        338:  'minecraft:reeds',
        339:  'minecraft:paper',
        340:  'minecraft:book',
        341:  'minecraft:slime_ball',
        342:  'minecraft:chest_minecart',
        343:  'minecraft:furnace_minecart',
        344:  'minecraft:egg',
        345:  'minecraft:compass',
        346:  'minecraft:fishing_rod',
        347:  'minecraft:clock',
        348:  'minecraft:glowstone_dust',
        349:  'minecraft:fish',
        350:  'minecraft:cooked_fish',
        351:  'minecraft:dye',
        352:  'minecraft:bone',
        353:  'minecraft:sugar',
        354:  'minecraft:cake',
        355:  'minecraft:bed',
        356:  'minecraft:repeater',
        357:  'minecraft:cookie',
        358:  'minecraft:filled_map',
        359:  'minecraft:shears',
        360:  'minecraft:melon',
        361:  'minecraft:pumpkin_seeds',
        362:  'minecraft:melon_seeds',
        363:  'minecraft:beef',
        364:  'minecraft:cooked_beef',
        365:  'minecraft:chicken',
        366:  'minecraft:cooked_chicken',
        367:  'minecraft:rotten_flesh',
        368:  'minecraft:ender_pearl',
        369:  'minecraft:blaze_rod',
        370:  'minecraft:ghast_tear',
        371:  'minecraft:gold_nugget',
        372:  'minecraft:nether_wart',
        373:  'minecraft:potion',
        374:  'minecraft:glass_bottle',
        375:  'minecraft:spider_eye',
        376:  'minecraft:fermented_spider_eye',
        377:  'minecraft:blaze_powder',
        378:  'minecraft:magma_cream',
        379:  'minecraft:brewing_stand',
        380:  'minecraft:cauldron',
        381:  'minecraft:ender_eye',
        382:  'minecraft:speckled_melon',
        383:  'minecraft:spawn_egg',
        384:  'minecraft:experience_bottle',
        385:  'minecraft:fire_charge',
        386:  'minecraft:writable_book',
        387:  'minecraft:written_book',
        388:  'minecraft:emerald',
        389:  'minecraft:item_frame',
        390:  'minecraft:flower_pot',
        391:  'minecraft:carrot',
        392:  'minecraft:potato',
        393:  'minecraft:baked_potato',
        394:  'minecraft:poisonous_potato',
        395:  'minecraft:map',
        396:  'minecraft:golden_carrot',
        397:  'minecraft:skull',
        398:  'minecraft:carrot_on_a_stick',
        399:  'minecraft:nether_star',
        400:  'minecraft:pumpkin_pie',
        401:  'minecraft:fireworks',
        402:  'minecraft:firework_charge',
        403:  'minecraft:enchanted_book',
        404:  'minecraft:comparator',
        405:  'minecraft:netherbrick',
        406:  'minecraft:quartz',
        407:  'minecraft:tnt_minecart',
        408:  'minecraft:hopper_minecart',
        409:  'minecraft:prismarine_shard',
        410:  'minecraft:prismarine_crystals',
        411:  'minecraft:rabbit',
        412:  'minecraft:cooked_rabbit',
        413:  'minecraft:rabbit_stew',
        414:  'minecraft:rabbit_foot',
        415:  'minecraft:rabbit_hide',
        416:  'minecraft:armor_stand',
        417:  'minecraft:iron_horse_armor',
        418:  'minecraft:golden_horse_armor',
        419:  'minecraft:diamond_horse_armor',
        420:  'minecraft:lead',
        421:  'minecraft:name_tag',
        422:  'minecraft:command_block_minecart',
        423:  'minecraft:mutton',
        424:  'minecraft:cooked_mutton',
        425:  'minecraft:banner',
        426:  'minecraft:end_crystal',
        427:  'minecraft:spruce_door',
        428:  'minecraft:birch_door',
        429:  'minecraft:jungle_door',
        430:  'minecraft:acacia_door',
        431:  'minecraft:dark_oak_door',
        432:  'minecraft:chorus_fruit',
        433:  'minecraft:popped_chorus_fruit',
        434:  'minecraft:beetroot',
        435:  'minecraft:beetroot_seeds',
        436:  'minecraft:beetroot_soup',
        437:  'minecraft:dragon_breath',
        438:  'minecraft:splash_potion',
        439:  'minecraft:spectral_arrow',
        440:  'minecraft:tipped_arrow',
        441:  'minecraft:lingering_potion',
        442:  'minecraft:shield',
        443:  'minecraft:elytra',
        444:  'minecraft:spruce_boat',
        445:  'minecraft:birch_boat',
        446:  'minecraft:jungle_boat',
        447:  'minecraft:acacia_boat',
        448:  'minecraft:dark_oak_boat',
        449:  'minecraft:totem_of_undying',
        450:  'minecraft:shulker_shell',
        452:  'minecraft:iron_nugget',
        453:  'minecraft:knowledge_book',
        2256: 'minecraft:record_13',
        2257: 'minecraft:record_cat',
        2258: 'minecraft:record_blocks',
        2259: 'minecraft:record_chirp',
        2260: 'minecraft:record_far',
        2261: 'minecraft:record_mall',
        2262: 'minecraft:record_mellohi',
        2263: 'minecraft:record_stal',
        2264: 'minecraft:record_strad',
        2265: 'minecraft:record_ward',
        2266: 'minecraft:record_11',
        2267: 'minecraft:record_wait'
    }
}


# Retrieve Python standard libraries for module whitelist
std_lib = sysconfig.get_python_lib(standard_lib=True)
libs = []
for top, dirs, files in os.walk(std_lib):
    for nm in files:
        prefix = top[len(std_lib)+1:]
        if prefix[:13] == 'site-packages':
            continue
        if nm == '__init__.py':
            libs.append(top[len(std_lib)+1:].replace(os.path.sep,'.'))
        elif nm[-3:] == '.py':
            libs.append(os.path.join(prefix, nm)[:-3].replace(os.path.sep,'.'))
        elif nm[-3:] == '.so' and top[-11:] == 'lib-dynload':
            libs.append(nm[0:-3])

for builtin in sys.builtin_module_names:
    libs.append(builtin)

# Filter out libraries
std_libs = []
for lib in list(set(libs)):
    if lib.startswith("test") or "test." in lib:
        continue
    if lib.startswith("_"):
        continue
    std_libs.append(lib)
del libs


# Gives strings quotes that don't have any, and formats numbers
def json_regex(match):
    if match.group(2):
        # print(match.group(2), re.match(r'^-?\d+.?\d*(f|L|b|d)?$', match.group(2)))

        if re.match(r'^-?\d+.?\d*(f|L|b|d)?$', match.group(2)):
            if "." in match.group(2):
                final_str = str(round(float(re.sub(r'[^0-9.-]', '', match.group(2))), 4))
            else:
                final_str = re.sub(r'[^0-9-]', '', match.group(2))
        else:
            final_str = f'"{match.group(2).lower()}"'

    else:
        final_str = match.group(1).replace('minecraft:', '')

    return final_str

# Enables or disables script for a specific server
def script_state(server_name: str, script: AmsFileObject, enabled=True):
    json_path = os.path.join(constants.server_path(server_name), 'amscript', json_name)

    # Get script whitelist data if it exists
    json_data = {'enabled': []}
    constants.folder_check(os.path.join(constants.server_path(server_name), 'amscript'))
    if os.path.isfile(json_path):
        with open(json_path, 'r') as f:
            json_data = json.loads(f.read())

    # print(script.file_name, json_data)

    # Add file to json list
    if enabled:
        if script.file_name not in json_data['enabled']:
            json_data['enabled'].append(script.file_name)

    # Remove file from json list
    else:
        if script.file_name in json_data['enabled']:
            json_data['enabled'].remove(script.file_name)

        # Delete file if it's empty
        if not json_data['enabled']:
            if os.path.isfile(json_path):
                os.remove(json_path)

    # Write to json file if there are scripts
    if json_data['enabled']:
        with open(json_path, 'w+') as f:
            f.write(json.dumps(json_data, indent=2))

# Gets and formats value for old NBT values
def fmt(obj):
    return round(float(obj.value), 4)

# Inventory classes for PlayerScriptObject
class ItemObject(Munch):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self['$_amsclass'] = self.__class__.__name__

    def __str__(self):
        try:
            item_id = str(self['id'])
        except KeyError:
            item_id = None
        return item_id

class EffectObject(Munch):
    def __init__(self, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self['$_amsclass'] = self.__class__.__name__
        self.effect_name = name

    def __str__(self):
        return str(self.effect_name)

class CoordinateObject(Munch):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self['$_amsclass'] = self.__class__.__name__

    def __do_operation__(self, operand, operator, reversed=False):
        if isinstance(operand, CoordinateObject):
            if len(self.keys()) != len(operand.keys()):
                raise AttributeError("Invalid arithmetic with Vec2 and Vec3")

            final_dict = {}
            for k in list(self.keys())[:3]:
                eval_str = f'y {operator} x' if reversed else f'x {operator} y'
                final_dict[k] = eval(eval_str, None, {'x': self[k], 'y': operand[k]})
            return CoordinateObject(final_dict)

        elif isinstance(operand, (int, float)):
            final_dict = {}
            for k in list(self.keys())[:3]:
                eval_str = f'y {operator} x' if reversed else f'x {operator} y'
                final_dict[k] = eval(eval_str, None, {'x': self[k], 'y': operand})
            return CoordinateObject(final_dict)

        else:
            raise TypeError('Operand must be <int> or <float>')


    def __str__(self):
        return " ".join([str(i) for k, i in self.items() if k != '$_amsclass'])

    def __add__(self, other):
        return self.__do_operation__(other, '+')

    def __radd__(self, other):
        return self.__do_operation__(other, '+', True)

    def __iadd__(self, other):
        for k, v in self.__do_operation__(other, '+').items():
            self[k] = v

    def __sub__(self, other):
        return self.__do_operation__(other, '-')

    def __mul__(self, other):
        return self.__do_operation__(other, '*')

    def __matmul__(self, other):
        return self.__do_operation__(other, '@')

    def __truediv__(self, other):
        return self.__do_operation__(other, '/')

    def __floordiv__(self, other):
        return self.__do_operation__(other, '//')

    def __mod__(self, other):
        return self.__do_operation__(other, '%')

    def __neg__(self):
        final_dict = {}
        for k in list(self.keys())[:3]:
            final_dict[k] = self[k] * -1
        return final_dict

    def __pos__(self):
        return self

    def __abs__(self):
        final_dict = {}
        for k in list(self.keys())[:3]:
            final_dict[k] = abs(self[k])
        return final_dict

    def __pow__(self, power, modulo=None):
        return self.__do_operation__(power, '**')

class InventoryObject():

    def __init__(self, item_list, selected_item):

        self._item_list = []

        self.selected_item = ItemObject({})
        self.offhand = ItemObject({})
        self.hotbar = ItemObject({x: ItemObject({}) for x in range(0, 9)})
        self.inventory = ItemObject({x: ItemObject({}) for x in range(0, 27)})
        self.armor = ItemObject({'head': ItemObject({}), 'chest': ItemObject({}), 'legs': ItemObject({}), 'feet': ItemObject({})})

        if item_list:
            self._process_items(item_list, selected_item)

    def __iter__(self):
        for item in self._item_list:
            yield item

    def _process_items(self, i, s):

        # Old items, parsing from playerdata
        if i.__class__.__name__ == "TAG_List":

            # Converts block/item/enchantment IDs to names
            def proc_nbt(item):

                # Add all root tags to formatted
                formatted = {}
                for x in item:

                    # Add all tag attributes to root.tag
                    if item[x].name == 'tag':
                        formatted[item[x].name] = {}
                        for tag in item[x]:
                            value = item[x][tag].value
                            formatted[item[x].name.lower()][item[x][tag].name.lower() if item[x][tag].name != "ench" else "enchantments"] = value if value else {}

                            # Format all enchantments
                            if item[x][tag].name.lower() in ["ench", "storedenchantments"]:
                                for e in item[x][tag]:
                                    formatted[item[x].name.lower()]['enchantments'][id_dict['enchant'].get(e['id'].value, e['id'].value)] = {'id': e['id'].value, 'lvl': e['lvl'].value}

                            # Format all display items
                            elif item[x][tag].name.lower() == "display":
                                for d in item[x][tag]:
                                    if d == "Lore":
                                        value = '\n'.join([line.value for line in item[x][tag][d]])
                                    else:
                                        value = item[x][tag][d].value

                                        if d == "Name":
                                            # Add to item list for __iter__ function
                                            if value not in self._item_list:
                                                self._item_list.append(value)

                                    formatted[item[x].name.lower()][item[x][tag].name][item[x][tag][d].name.lower()] = value

                            # Attributes
                            elif item[x][tag].name.lower() == "attributemodifiers":
                                formatted[item[x].name.lower()]['attributemodifiers'] = []
                                for y in item[x][tag].tags:
                                    attr_dict = {y[a].name.lower(): y[a].value for a in y}
                                    formatted[item[x].name.lower()]['attributemodifiers'].append(attr_dict)

                            # Format all book pages
                            elif item[x][tag].name.lower() == "pages":
                                formatted[item[x].name.lower()]['pages'] = [y for y in item[x][tag].tags]


                    elif item[x].name == 'id':
                        try:
                            value = item[x].value.replace('minecraft:','')
                        except AttributeError:
                            value = id_dict['items'][item[x].value].replace('minecraft:','')

                        # Add to item list for __iter__ function
                        if value not in self._item_list:
                            self._item_list.append(value)

                        formatted[item[x].name.lower()] = value


                    elif item[x].name != 'Slot':
                        formatted[item[x].name.lower()] = item[x].value


                return ItemObject(formatted)

            # Iterates over every item in inventory
            def sort_item(item):
                slot = fmt(item['Slot'])

                # Hotbar
                if slot in range(0, 9):
                    self.hotbar[slot] = proc_nbt(item)

                # Offhand
                elif slot == -106:
                    self.offhand = proc_nbt(item)

                # Feet
                elif slot == 100:
                    self.armor.feet = proc_nbt(item)

                # Legs
                elif slot == 101:
                    self.armor.legs = proc_nbt(item)

                # Chest
                elif slot == 102:
                    self.armor.chest = proc_nbt(item)

                # Head
                elif slot == 103:
                    self.armor.head = proc_nbt(item)

                # Inventory
                else:
                    self.inventory[slot-9] = proc_nbt(item)

            for item in i.tags:
                sort_item(item)

            if s:
                self.selected_item = proc_nbt(s[0])
                self.selected_item['slot'] = s[1]

        # /data get formatting
        else:

            # Converts block/item/enchantment IDs to names
            def proc_nbt(item):
                new_item = deepcopy(item)

                # Delete slot attribute, because it already exists in parent
                try:
                    del new_item['slot']
                except KeyError:
                    pass

                # Add ID's and names to persistent cache
                if new_item['id'] not in self._item_list:
                    self._item_list.append(new_item['id'])

                try:
                    custom_name = ''.join([name for name in re.findall(r'"text":\s*?"([^"]*)"', new_item['tag']['display']['name'])])
                    if custom_name not in self._item_list:
                        self._item_list.append(custom_name)
                except KeyError:
                    pass

                return ItemObject(new_item)

            # Iterates over every item in inventory
            def sort_item(item):
                slot = int(item['slot'])

                # Hotbar
                if slot in range(0, 9):
                    self.hotbar[slot] = proc_nbt(item)

                # Offhand
                elif slot == -106:
                    self.offhand = proc_nbt(item)

                # Feet
                elif slot == 100:
                    self.armor.feet = proc_nbt(item)

                # Legs
                elif slot == 101:
                    self.armor.legs = proc_nbt(item)

                # Chest
                elif slot == 102:
                    self.armor.chest = proc_nbt(item)

                # Head
                elif slot == 103:
                    self.armor.head = proc_nbt(item)

                # Inventory
                else:
                    self.inventory[slot-9] = proc_nbt(item)

            for item in i:
                sort_item(item)

            if s:
                self.selected_item = proc_nbt(s[0])
                self.selected_item['slot'] = s[1]


# Stores persistent player and server configurations
class PersistenceManager():

    class ObjectDecoder(json.JSONDecoder):
        def __init__(self, *args, **kwargs):
            json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

        def object_hook(self, dct):
            if '$_amsclass' in dct:
                if dct['$_amsclass'] == 'ItemObject':
                    return ItemObject(dct)
                elif dct['$_amsclass'] == 'EffectObject':
                    return EffectObject(dct)
                elif dct['$_amsclass'] == 'CoordinateObject':
                    return CoordinateObject(dct)
            return dct

    class PersistenceObject(Munch):

        # Prevent deletion of root keys
        def __delitem__(self, key):
            if key in ['server', 'player']:
                self[key] = {}
            return super().__delitem__(key)

        # Prevent assignment to root keys
        def __setitem__(self, key, value):
            if not isinstance(value, dict):
                raise AttributeError(f"Root attribute '{key}' must be a dictionary, assign '{value}' to a key instead")
            return super().__setitem__(key, value)

    def __init__(self, server_name):
        # The server's persistent configuration will reside in the 'server' key
        # Individual players will have their own dictionary in the 'player' key

        self._name = server_name
        self._config_path = os.path.join(constants.server_path(self._name), 'amscript')
        self._path = os.path.join(self._config_path, "pst-conf.json")
        self._data = None

        # Retrieve data if it exists
        # print(self._path)
        if os.path.exists(self._path):
            with open(self._path, 'r+') as f:
                try:
                    self._data = self.PersistenceObject(json.load(f, cls=self.ObjectDecoder))
                    # print(self._data)
                except json.JSONDecodeError:
                    pass

        # Else instantiate new object
        if not self._data:
            self._data = self.PersistenceObject({"server": {}, "player": {}})

        self.clean_keys()


    # Fixes deleted keys
    def clean_keys(self):
        try:
            if not self._data['server']:
                self._data.update({'server': {}})
        except KeyError:
            self._data.update({'server': {}})

        try:
            if not self._data['player']:
                self._data.update({'player': {}})
        except KeyError:
            self._data.update({'player': {}})


    # Writes persistent config to disk
    def write_config(self):
        self.clean_keys()

        # If data is empty, delete persistent config if it exists in file
        if not self._data['server'] and not self._data['player']:
            if os.path.exists(self._path):
                os.remove(self._path)

        # If they do exist, write to file
        else:
            constants.folder_check(self._config_path)
            with open(self._path, 'w+') as f:
                json.dump(self._data, f, indent=4)


    # Resets data, and deletes file on disk
    def purge_config(self):
        self._data = self.PersistenceObject({"server": {}, "player": {}})
        self.write_config()
