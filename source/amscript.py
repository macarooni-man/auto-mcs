from concurrent.futures import ThreadPoolExecutor
from functools import partial
from threading import Timer
from textwrap import indent
from glob import glob
import constants
import time
import acl
import ast
import os
import re
import gc


# Auto-MCS Scripting API
# ------------------------------------------------- Script Object ------------------------------------------------------


# For processing .ams files and running them in the wrapper
# Pass in svrmgr.ServerObject
class ScriptObject():

    # ------------------------- Management -------------------------

    def __init__(self, server_obj):
        # Server stuffs
        self.enabled = True
        self.server = server_obj
        self.server_script_obj = ServerScriptObject(server_obj)
        self.server_id = ("#" + server_obj._hash)

        # File stuffs
        self.script_path = os.path.join(constants.configDir, 'amscript')
        constants.folder_check(self.script_path)
        self.scripts = glob(os.path.join(self.script_path, '*.ams'))

        # Yummy stuffs
        self.protected_variables = ["server", "acl", "backup", "addon"]
        self.valid_events = ["@player.on_join", "@player.on_leave", "@player.on_message", "@server.alias", "@server.on_start", "@server.on_shutdown", "@server.on_loop"]
        self.delay_events = ["@player.on_join", "@player.on_leave", "@player.on_message", "@server.on_start", "@server.on_shutdown"]
        self.valid_imports = ['requests', 'time', 'os', 'requests', 'glob', 'datetime', 'concurrent.futures']
        self.valid_imports.extend([os.path.basename(x).rsplit(".", 1)[0] for x in glob(os.path.join(self.script_path, '*.py'))])
        self.aliases = {}
        self.function_dict = {}


    def __del__(self):
        self.enabled = False


    # Generate script thread and code from .ams files
    def construct(self):

        # If script returns None it's valid, else will return error message
        def is_valid(script_path):

            parse_error = {}
            script_text = ""

            with open(script_path, 'r') as f:

                for x, line in enumerate(f.readlines(), 1):

                    # Throw error if server variable is reassigned
                    for var in self.protected_variables:
                        if line.strip().replace(' ', '').startswith(f"{var}=") or ("def" in line and f" {var}(" in line):
                            parse_error['file'] = os.path.basename(script_path)
                            parse_error['code'] = line.strip()
                            parse_error['line'] = f'{x}:{line.find(f"{var}")+1}'
                            parse_error['message'] = f"AssertionError: '{var}' attribute is read-only and cannot be re-assigned"
                            parse_error['object'] = AssertionError(parse_error['message'])
                            return parse_error

                    # Format valid event tags as functions
                    for event in self.valid_events:
                        if line.startswith(event):
                            if event == '@server.alias':
                                line = line.replace(event, f'{event.split(".")[1]}').replace(":\n", f'\ndef alias():\n')
                            elif event == '@server.on_loop':
                                line = line.replace(event, f'{event.split(".")[1]}').replace(":\n", f'\ndef on_loop():\n')
                            else:
                                line = line.replace(event, f'def {event.split(".")[1]}')

                    script_text = script_text + f'{line}'

            # print(script_text)


            try:
                ast.parse(script_text)
            except Exception as e:
                parse_error['file'] = os.path.basename(script_path)
                parse_error['code'] = e.args[1][-1].strip()
                parse_error['line'] = f"{e.args[1][1]}:{e.args[1][2]}"
                parse_error['message'] = f"{e.__class__.__name__}: {e.args[0]}"
                parse_error['object'] = e
                return parse_error

        # Converts amscripts into memory to be accessed by events
        def convert_script(script_path):
            with open(script_path, 'r') as f:

                # Initialize self.function_dict
                self.function_dict[os.path.basename(script_path)] = {event: [] for event in self.valid_events}

                # Get list of all variables
                variables = {
                    'server': self.server_script_obj,
                    'acl': self.server.acl,
                    'backup': self.server.backup,
                    'addon': self.server.addon
                }

                try:
                    test = self.function_dict[os.path.basename(script_path)]['values']
                except KeyError:
                    self.function_dict[os.path.basename(script_path)]['values'] = variables

                alias_functions = {}
                loop_functions = []


                # Ignore all comments and grab imports/global variables
                script_data = ""
                global_variables = f"from itertools import zip_longest\nimport importlib\nimport time\nimport sys\nimport os\nsys.path.insert(0, r'{self.script_path}')\n"

                for line in f.readlines():
                    line = line.replace('\t', '    ')

                    # Find and remove comments
                    if "#" in line.strip():
                        line = line.split("#")[0] + "\n"

                    # Grab import statements
                    elif line.startswith("from ") or line.startswith("import "):
                        for i in self.valid_imports:
                            if i in line:
                                alias = i
                                if line not in global_variables:
                                    global_variables = global_variables + line.strip() + "\n"
                                if f"import {i} as " in line and "from " not in line:
                                    i = line.split(f"import {i} as ", 1)[1].strip()
                                if f"from {i}" in line and " import" in line:
                                    break
                                if f"importlib.reload({i})" not in global_variables:
                                    global_variables = global_variables + f"importlib.reload({i})\n"

                    # Tag global functions
                    elif line.startswith("def "):
                        line = "%" + line

                    # Find global variables
                    elif not (line.startswith(' ') or line.startswith('\t')):
                        if re.match(r"[A-Za-z0-9]+.*=.*", line.strip(), re.IGNORECASE):
                            global_variables = global_variables + line.strip() + "\n"

                    script_data = script_data + line
                script_data += "\n "


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
                            break

                # Load Imports, and global variables/functions into memory
                # print(global_variables)
                global_variables += f"\nos.chdir(r'{self.server.server_path}')"
                exec(global_variables, self.function_dict[os.path.basename(script_path)]['values'], self.function_dict[os.path.basename(script_path)]['values'])


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
                                    if event == '@server.alias':
                                        alias_values = {
                                            'cmd': '',
                                            'args': {},
                                            'perm': 'anyone',
                                            'desc': '',
                                            'plr': '',
                                            'hide': False
                                        }

                                        args = function.splitlines()[0].split('(',1)[1].rsplit(')',1)[0]
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
                                        exec(proc_func, alias_values, alias_values)

                                        # Only allow last argument to be optional, hence retarded dict comprehension
                                        alias_keys = alias_values['args'].keys()
                                        alias_dict = {
                                            'command': f"!{alias_values['cmd']}" if bool(re.match('^[a-zA-Z0-9]+$', alias_values['cmd'][:1])) else f"!{alias_values['cmd'][1:]}",
                                            'arguments': {k:(True if (k != list(alias_keys)[-1]) else v) for (k,v) in alias_values['args'].items()},
                                            'syntax': '',
                                            'permission': alias_values['perm'],
                                            'description': alias_values['desc'] if alias_values['desc'] else 'An Auto-MCS provided command',
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
                                                'description': alias_dict['description']
                                            }
                                        alias_functions[alias_dict['command']] = function


                                    # Register loop event and reformat code
                                    elif event == '@server.on_loop':
                                        loop_values = {
                                            'itvl': 0,
                                            'unt': 'second'
                                        }

                                        args = function.splitlines()[0].split('(',1)[1].rsplit(')',1)[0].lower()
                                        proc_func = "def process(interval=1, unit='second'):\n    global itvl, unt\n    itvl=interval\n    unt=unit\n"
                                        proc_func += f"process({args})"
                                        exec(proc_func, loop_values, loop_values)

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
                                                test = test if loop_dict['unit'] == 'second' else (test*60) if loop_dict['unit'] == 'minute' else (test*3600)
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
                                        exec(function, self.function_dict[os.path.basename(script_path)]['values'], self.function_dict[os.path.basename(script_path)]['values'])
                                        self.function_dict[os.path.basename(script_path)][event].append(self.function_dict[os.path.basename(script_path)]['values'][func_name])
                                    break


                # Concatenate all aliases into one function
                if alias_functions:
                    first = True

                    new_func = "def __alias__(player, command, permission='anyone'):\n"
                    new_func += "    perm_dict = {'anyone': 0, 'op': 1, 'server': 2}\n\n"

                    for k, v in alias_functions.items():

                        syntax = self.aliases[k]['syntax']
                        hidden = self.aliases[k]['hidden']
                        argument_list = list(self.aliases[k]['arguments'].keys())
                        req_args_list = list([x for x in self.aliases[k]['arguments'].keys() if self.aliases[k]['arguments'][x]])
                        arguments = {}

                        new_func += f"    {'if' if first else 'elif'} command.strip().split(' ',1)[0].strip() == '{k}':\n"
                        new_func += f"        if perm_dict[permission] < perm_dict['{self.aliases[k]['permission']}']:\n"

                        # Permission thingy
                        new_func += (f"            player.log_error(\"You do not have permission to use this command\")\n" if not hidden else "            pass\n")
                        new_func += f"        else:\n"
                        new_func += f"            if len(command.split(' ', len({argument_list}))[1:]) < len({req_args_list}):\n"

                        # Syntax thingy
                        new_func += (f"                player.log_error(\"Invalid syntax: {syntax}\")\n" if not hidden else "                pass\n")
                        new_func += f"            else:\n"
                        new_func += f"                arguments = dict(zip_longest(reversed({argument_list}), reversed(command.split(' ', len({argument_list}))[1:])))\n"
                        new_func += f"                command = command.split(' ', 1)[0].strip()\n"

                        # Allow 'player' variable to be reassigned if needed
                        if self.aliases[k]['player'] != 'player':
                            new_func += f"                {self.aliases[k]['player']} = player\n"
                        new_func += "\n"
                        new_func += indent(v.split("\n", 1)[1], "            ")
                        new_func += "\n\n"
                        first = False

                    # print(new_func)
                    exec(new_func, self.function_dict[os.path.basename(script_path)]['values'], self.function_dict[os.path.basename(script_path)]['values'])
                    self.function_dict[os.path.basename(script_path)]['@server.alias'].append(self.function_dict[os.path.basename(script_path)]['values']['__alias__'])


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


                # Remove references to function calls in the script context
                for event in self.valid_events:
                    func_name = f'__{event.split(".")[1]}__'
                    if func_name in self.function_dict[os.path.basename(script_path)]['values'].keys():
                        del self.function_dict[os.path.basename(script_path)]['values'][func_name]

                del variables
                # print(function)
            # print(self.function_dict)


        # Parse script file
        def process_file(script_file):
            valid = is_valid(script_file)
            print(valid)

            if valid is None:
                convert_script(script_file)


        # with ThreadPoolExecutor(max_workers=10) as pool:
        #     pool.map(process_file, self.scripts)
        for script in self.scripts:
            process_file(script)


    # Deconstruct loaded .ams files
    def deconstruct(self):
        self.enabled = False
        self.server_script_obj._running = False

        # Wait for tick time*2 for loops to stop
        time.sleep(0.1)
        del self.server_script_obj

        # Reset dict in memory
        for key, item in self.function_dict.items():
            for v in self.function_dict[key]['values'].values():
                del v
            self.function_dict[key].clear()
            del item

        self.function_dict.clear()
        del self.function_dict
        self.function_dict = {}
        self.aliases = {}
        gc.collect()


    # Runs specified event with parameters
    def call_event(self, event: str, args: tuple, delay=0):
        if self.function_dict and event in self.valid_events:
            for script in tuple(self.function_dict.values()):
                try:
                    for func in script[event]:
                        if not self.enabled:
                            return
                        Timer(delay, partial(func, *args)).start()
                except KeyError:
                    return


    # ----------------------- Server Events ------------------------

    # Fires when server starts
    # {'date': date}
    def start_event(self, data):
        self.call_event('@server.on_start', (data))
        self.call_event('@server.on_loop', ())
        print('server.on_start')
        print(data)

    # Fires when server starts
    # Eventually add return code to see if it crashed
    # {'date': date}
    def shutdown_event(self, data):
        self.server_script_obj._running = False
        self.call_event('@server.on_stop', (data))
        print('server.on_shutdown')
        print(data)


    # ----------------------- Player Events ------------------------

    # Fires event when player joins the game
    # {'user': user, 'ip': ip_addr, 'date': date, 'logged-in': True}
    def join_event(self, player_obj):
        self.call_event('@player.on_join', (PlayerScriptObject(self.server_script_obj, player_obj['user']), player_obj))
        print('player.on_join')
        print(player_obj)

    # Fires when player leaves the game
    # {'user': user, 'ip': ip_addr, 'date': date, 'logged-in': False}
    def leave_event(self, player_obj):
        self.call_event('@player.on_leave', (PlayerScriptObject(self.server_script_obj, player_obj['user']), player_obj))
        print('player.on_leave')
        print(player_obj)

    # Fires event when message/cmd is sent
    # {'user': player, 'content': message}
    def message_event(self, msg_obj):
        if msg_obj['content'].strip().split(" ",1)[0].strip() in self.aliases.keys():
            self.alias_event(msg_obj)
        elif msg_obj['user'] != self.server_id:
            self.call_event('@player.on_message', (PlayerScriptObject(self.server_script_obj, msg_obj['user']), msg_obj['content']))

            print('player.on_message')
            print(msg_obj)

    # Fires event when player sends a command alias
    # {'user': player, 'content': message}
    def alias_event(self, player_obj):
        self.server.acl.reload_list('ops')
        print([rule.rule for rule in self.server.acl.rules['ops']])
        if player_obj['user'] == self.server_id:
            permission = 'server'
        elif self.server.acl.rule_in_acl('ops', player_obj['user']):
            permission = 'op'
        else:
            permission = 'anyone'

        self.call_event('@server.alias', (PlayerScriptObject(self.server_script_obj, player_obj['user']), player_obj['content'], permission))

        print('server.alias')
        print(player_obj)



# Reconfigured ServerObject to be passed in as 'server' variable to amscripts
class ServerScriptObject():
    def __init__(self, server_obj):
        self._running = True
        self._server_id = ("#" + server_obj._hash)
        self._reload_scripts = server_obj.reload_scripts

        # Assign functions from main server object
        self.execute = server_obj.silent_command
        self.log = server_obj.send_log
        self.aliases = {}

        # Properties
        self.name = server_obj.name
        self.version = server_obj.version
        self.build = server_obj.build
        self.type = server_obj.type
        self.network = server_obj.run_data['network']['address']


    def __del__(self):
        self._running = False

    # Logging functions
    def log_error(self, msg):
        self.log(msg, 'error')
    def log_success(self, msg):
        self.log(msg, 'success')


# Reconfigured ServerObject to be passed in as 'player' variable to amscript events
class PlayerScriptObject():
    def __init__(self, server_script_obj: ServerScriptObject, player_name: str):
        self._server = server_script_obj
        self._server_id = server_script_obj._server_id

        # Properties
        self.name = player_name


    # Simple boolean check to see if user is the server
    def is_server(self):
        return self.name == self._server_id

    # Logging functions
    # Version compatible message system for local player object
    def log(self, msg, color="gray", style='italic'):
        style = 'normal' if style not in ('normal', 'italic', 'bold', 'strikethrough', 'obfuscated', 'underlined') else style

        # Use /tellraw if it's supported, else /tell
        if constants.version_check(str(self._server.version), '>=', '1.7.2') and not self.is_server():
            msg = f'/tellraw {self.name} {{"text": "{msg}", "color": "{color}"}}'
            if style != 'normal':
                msg = msg[:-1] + f', "{style}": "true"}}'
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
            if self.is_server():
                msg = f'{final_code}{("§r " + final_code).join(msg.strip().split(" "))}§r'
                self._server.log(msg)
            else:
                if style != 'normal':
                    final_code += style_table[style]
                msg = f'/tell {self.name} {final_code}{("§r "+final_code).join(msg.strip().split(" "))}§r'
                self._server.execute(msg, log=False)

    def log_error(self, msg):
        self.log(msg, "red", "normal")
    def log_success(self, msg):
        self.log(msg, "green", "normal")
