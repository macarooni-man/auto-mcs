import pyperclip
import threading
import datetime
import curses
import urwid
import time
import math
import sys
import re
import os

import constants
import telepath
import acl


# ----------------------------------------------- Global Functions -----------------------------------------------------

# Check if advanced terminal features are supported
advanced_term = False
try:
    if os.environ['TERM'].endswith('-256color'):
        advanced_term = True
except:
    pass


# Overwrite STDOUT to not interfere with the UI
class NullWriter:
    def write(self, *args, **kwargs):
        pass
    def flush(self):
        pass

logo = ["                           _                                 ",
        "   ▄▄████▄▄     __ _ _   _| |_ ___       _ __ ___   ___ ___  ",
        "  ▄█  ██  █▄   / _` | | | | __/ _ \  __ | '_ ` _ \ / __/ __| ",
        "  ███▀  ▀███  | (_| | |_| | || (_) |(__)| | | | | | (__\__ \ ",
        "  ▀██ ▄▄ ██▀   \__,_|\__,_|\__\___/     |_| |_| |_|\___|___/ ",
        "   ▀▀████▀▀                                                  ",
        ""
        ]


# Handle keyboard inputs from console
def handle_input(key):
    global history_index
    command = command_edit.get_edit_text().replace(command_header, '')

    # Submit/process command on ENTER
    if key == 'enter' and not disable_commands:
        process_command(command)

    # Modulate command history with arrow keys
    elif key in ['up', 'down'] and command_history:

        if key == 'down':
            if history_index > 0:
                history_index -= 1
            else:
                command_edit.set_edit_text('')
                return

        # Constrain history_index to valid range
        history_index = max(0, min(history_index, len(command_history) - 1))

        # Set the command text based on the updated index
        new_text = command_history[history_index]
        command_edit.set_edit_text(new_text)
        command_edit.set_edit_pos(len(new_text))

        if key == 'up':
            if history_index < len(command_history) - 1:
                history_index += 1


# Handle commands entered in console
def process_command(cmd: str):
    global history_index, command_history
    history_index = 0
    success = True

    if cmd not in command_history[:1]:
        command_history.insert(0, cmd)

        # Limit size of command history
        if len(command_history) > 100:
            command_history.pop()

    command_edit.set_edit_text('')
    response = [('normal', "Type a command, ?, or "), ('command', 'help')]
    if cmd.strip():
        try:
            # Format raw data into command, and args
            raw = [a.strip() for a in cmd.split(' ') if a.strip()]
            cmd = raw[0]
            args = () if len(raw) < 2 else raw[1:]

            # Process command and return output
            command = commands[cmd]
            output = command.exec(args)
            if isinstance(output, tuple):
                success = 'fail' != output[1]
                output = output[0]
            response = output

        except KeyError:
            response = [("info", "Unknown command "), ("fail", cmd), ("normal", '\n'), *response]

    command_content.set_text([('success' if success else 'fail', response_header), *response])


def update_console(text: str or tuple):
    command_content.set_text(text)
    loop.draw_screen()


# Manage servers from the 'server' command
def manage_server(name: str, action: str):
    def func_wrapper(func: list or tuple or callable):
        global disable_commands
        disable_commands = True
        def run():
            if isinstance(func, list or tuple):
                [f() for f in func]
            else:
                func()
        disable_commands = False

        threading.Timer(0, run).start()

    def return_log(log):
        return log

    name = name.strip()

    # Create a new stock Vanilla server
    if action == 'create':

        # Ignore if offline
        if not constants.app_online:
            return [("info", "Server creation requires an internet connection")], 'fail'

        # Name input validation
        if len(name) < 25:
            if '\n' in name:
                name = name.splitlines()[0]
            name = re.sub('[^a-zA-Z0-9 _().-]', '', name)
        else:
            return [("parameter", name), ("info", " is too long, shorten it and try again (25 max)")], 'fail'

        if name.lower() in constants.server_list_lower:
            return [("parameter", name), ("info", " already exists")], 'fail'


        # Create server here
        constants.new_server_init()
        constants.new_server_info['name'] = name
        constants.new_server_info['type'] = 'vanilla'
        constants.new_server_info['version'] = constants.latestMC['vanilla']
        constants.new_server_info['acl_object'] = acl.AclManager(name)

        # Run things and stuff
        update_console('(1/5) Validating Java')
        constants.java_check()

        update_console(f"(2/5) Downloading 'server.jar'")
        constants.download_jar()

        update_console(f"(3/5) Installing '{name}'")
        constants.install_server()

        update_console(f"(4/5) Applying server configuration")
        constants.generate_server_files()

        update_console(f"(5/5) Creating initial back-up")
        constants.create_backup()

        constants.generate_server_list()

        return [
            ("normal", "Successfully created "),
            ("parameter", name),
            ("info", f" (Vanilla {constants.latestMC['vanilla']})\n\n"),
            ("info", " - to modify this server, run "),
            ("command", "telepath "),
            ("sub_command", "pair "),
            ("info", "to connect from a remote instance of auto-mcs")
        ]


    # Manage existing servers
    elif name.lower() in constants.server_list_lower:
        server_obj = constants.server_manager.open_server(name)

        if action == 'info':
            return_text = [
                ("normal", "Server info - "), ("parameter", name),
                ("normal", f'\n\n{server_obj.type.title()} {server_obj.version}' + (f' (b{server_obj.build})\n' if server_obj.build else '\n')),
                ("sub_command", server_obj.server_properties['motd'])
            ]
            if server_obj.running:
                try:
                    return_text.append(("success", f"\n\n> {server_obj.run_data['network']['address']['ip']}:{server_obj.run_data['network']['address']['port']}"))
                except:
                    return_text.append(("success", f"\n\nRunning, waiting to bind port..."))
            else:
                return_text.append(("info", "\n\nNot running"))

            return return_log(return_text)

        elif action == 'start':
            if server_obj.running:
                return [('parameter', name), ('info', ' is already running')], 'fail'

            func_wrapper(server_obj.launch)
            return return_log([("normal", "Launched "), ("parameter", name)])

        elif action == 'stop':
            if not server_obj.running:
                return [('parameter', name), ('info', ' is not running')], 'fail'

            func_wrapper(server_obj.stop)
            return return_log([("normal", "Stopped "), ("parameter", name)])

        elif action == 'restart':
            if server_obj.running:
                func_wrapper(server_obj.restart)
                return return_log([("normal", "Restarted "), ("parameter", name)])
            else:
                return [("parameter", name), ("info", " is not running")], 'fail'

        elif action == 'delete':
            if not server_obj.running:
                func_wrapper([server_obj.delete, constants.generate_server_list])
                return [("normal", "Deleted "), ("parameter", name), ("normal", " and saved a back-up")]

            else:
                return [
                    ("parameter", name),
                    ("info", " is running. Please run "),
                    ("command", "server "),
                    ("sub_command", "stop "),
                    ("parameter", name),
                    ("info", " first")
                ], 'fail'

        elif action == 'save':
            update_console([("info", "Saving a back-up of "), ("parameter", name), ("info", "...")])
            if not server_obj.backup:
                time.sleep(0.1)
            server_obj.backup.save()
            constants.server_manager.current_server.reload_config()
            return [("normal", "Saved a back-up of "), ("parameter", name)]

        elif action == 'restore':
            if not server_obj.running:
                if not server_obj.backup:
                    time.sleep(0.1)
                update_console([("info", "Restoring the latest back-up of "), ("parameter", name), ("info", "...")])
                server_obj.backup.restore(server_obj.backup.list[0])
                constants.server_manager.current_server.reload_config()
                return return_log([("normal", "Restored "), ("parameter", name), ("normal", " to the latest back-up")])
            else:
                return [
                    ("parameter", name),
                    ("info", " is running. Please run "),
                    ("command", "server "),
                    ("sub_command", "stop "),
                    ("parameter", name),
                    ("info", " first")
                ], 'fail'

    # If server doesn't exist
    else:
        return [('parameter', name), ('info',  ' does not exist')], 'fail'

def list_servers():
    if constants.server_list:
        return_text = [('normal', f'Installed Servers'),  ('success', ' * - active'), ('info', f' ({len(constants.server_list)} total):\n\n')]
        line = ''
        for server in constants.server_list:
            running = server in constants.server_manager.running_servers
            text = f'{"*" if running else ""}{server}    '
            line += text
            if len(line) > loop.screen_size[0] - 20:
                return_text.append(('info', '\n\n'))
                line = ''
            return_text.append(('success' if running else 'info', text))
        return return_text
    else:
        return [('info', 'No servers were found')], 'fail'

def enable_playit(name: str, enabled=True):
    if name.lower() in constants.server_list_lower:
        server_obj = constants.server_manager.open_server(name)
        update_console('Retrieving server configuration...')
        while not all(list(server_obj._check_object_init().values())):
            time.sleep(0.5)

        if not server_obj.proxy_installed():
            update_console('Installing playit agent...')
            server_obj.install_proxy()

        update_console('Configuring playit agent...')
        server_obj.enable_proxy(enabled)

        return [("normal", f"{'En' if enabled else 'Dis'}abled tunneling for "), ("parameter", name)]

    # If server doesn't exist
    else:
        return [('parameter', name), ('info',  ' does not exist')], 'fail'


# Refreshes telepath display data at the top
def refresh_telepath_host(data=None):
    api = constants.api_manager
    header = ('telepath_header', f'Telepath API (v{constants.api_manager.version})\n')

    if api.running:
        ip = api.host
        if ip == '0.0.0.0':
            ip = constants.get_private_ip()
        port = api.port
        if constants.public_ip:
            if constants.check_port(constants.public_ip, port, 0.05):
                ip = constants.public_ip


        text = ('telepath_enabled', f'> {ip}:{api.port}')

    else:
        text = ('telepath_disabled', ' < not running >')
    telepath_content.set_text([header, text])
    return data


# Reset telepath to default configuration
def reset_telepath(data=None):
    api = constants.api_manager
    api.stop()
    api._reset_session()
    return f'Telepath data has {"not " if bool(api.authenticated_sessions) else ""}been cleared'


# Handles telepath pair requests
def telepath_pair(data=None):
    final_text = [
        ("info", "Failed to pair. Please run "),
        ("command", "telepath "),
        ("sub_command", "pair "),
        ("info", "to try again")
    ], 'fail'

    constants.api_manager.pair_listen = True
    timeout = 0
    total = 180

    try:
        while 'code' not in constants.api_manager.pair_data:
            update_console([
                ('success', response_header),
                ('normal', f'Listening to pair requests for {total - timeout}s'),
                ('info', ' (CTRL-C to cancel)'),
                ('parameter', '\n\nEnter the IP above into another instance of auto-mcs to continue')
            ])
            time.sleep(1)
            timeout += 1
            if timeout >= total:
                return final_text
    except KeyboardInterrupt:
        constants.api_manager.pair_listen = False
        return [('info', 'Pairing was cancelled')], 'fail'

    data = constants.api_manager.pair_data
    code = f'{data["code"][:3]}-{data["code"][3:]}'
    update_console([
        ('normal', '< '),
        ('telepath_host', f'{data["host"]["host"]}/{data["host"]["user"]}'),
        ('normal', ' >\n\n'),
        ('info', 'Code (expires 1m):   '),
        ('command', code)
    ])

    timeout = 0
    while constants.api_manager.pair_data:
        time.sleep(1)
        timeout += 1
        if timeout >= 60:
            return final_text

    if constants.api_manager.current_user:
        user = constants.api_manager.current_user
        final_text = [('normal', 'Successfully paired with '), ('telepath_host', f'{user["host"]}/{user["user"]}:{user["ip"]}')]

    constants.api_manager.pair_listen = False

    return final_text


# Displays Telepath users
def telepath_users(data=None):
    if not constants.api_manager.running:
        return 'Telepath API is not running', 'fail'

    elif not constants.api_manager.authenticated_sessions:
        return [
            ("info", "There are no authenticated Telepath users. Please run "),
            ("command", "telepath "),
            ("sub_command", "pair "),
            ("info", "first to pair a client")
        ], 'fail'

    else:
        content = [('normal', f'Authenticated Telepath users'), ('info', f' ({len(constants.api_manager.authenticated_sessions)} total):\n\n')]
        for x, user in enumerate(constants.api_manager.authenticated_sessions):
            user_content = [('sub_command', f'ID #{x+1}   '), ('parameter', f'{user["host"]}/{user["user"]}')]
            if constants.api_manager.current_user and (user["user"] == constants.api_manager.current_user["user"]):
                user_content.append(('command', ' (logged in)'))
            if x+1 < len(constants.api_manager.authenticated_sessions):
                user_content.append(('info', '\n\n'))
            content.extend(user_content)

        return content
def telepath_revoke(user_id=None):

    # Input validate user ID
    if user_id:
        try:
            user_id = int(user_id.strip('# ')) - 1
        except:
            user_id = None


    if not constants.api_manager.running:
        return 'Telepath API is not running', 'fail'

    elif not constants.api_manager.authenticated_sessions:
        return [
            ("info", "There are no authenticated Telepath users. Please run "),
            ("command", "telepath "),
            ("sub_command", "pair "),
            ("info", "first to pair a client")
        ], 'fail'

    elif user_id is None or user_id > len(constants.api_manager.authenticated_sessions) - 1 or user_id < 0:
        return [
            ("info", "A valid user ID was not specified. Please run "),
            ("command", "telepath "),
            ("sub_command", "users "),
            ("info", "first to locate the ID")
        ], 'fail'

    else:
        user = constants.api_manager.authenticated_sessions[user_id]

        # Force logout if they are logged in
        if constants.api_manager.current_user and (user["user"] == constants.api_manager.current_user["user"]):
            constants.api_manager._force_logout(constants.api_manager.current_user['session_id'])

        # Revoke from authenticated sessions
        constants.api_manager._revoke_session(user['id'])

        if user not in constants.api_manager.authenticated_sessions:
            return [('normal', 'Revoked Telepath access from '), ('sub_command', f'ID #{user_id+1} '), ('parameter', f'{user["host"]}/{user["user"]}')]

        else:
            return [('info', 'Something went wrong, please try again')], 'fail'


# Update app to the latest version
def update_app(info=False):

    # Display update info
    if info:
        return [
            ("sub_command", f"(!) Update - v{constants.update_data['version']}\n\n"),
            ("info", constants.update_data['desc'].replace('\r','')),
            ("success", response_header),
            ("normal", "To update to this version, run "),
            ("command", "update "),
            ("sub_command", "install ")
        ]

    else:
        update_console([("info", response_header), ('parameter', f'Downloading auto-mcs v{constants.update_data["version"].strip()}...')])
        if constants.download_update():
            update_console([("success", response_header), ('command', f'Successfully installed the update! Restarting...')])
            time.sleep(3)
            constants.restart_update_app()

        else:
            return [("info", "Something went wrong installing the update. Please try again later")], 'fail'


# Override print
if not constants.is_admin() and not constants.debug:
    def print(*args, **kwargs):
        telepath_content.set_text(" ".join([str(a) for a in args]))



# -------------------------------------------------- Main Menu ---------------------------------------------------------

class Command:

    def exec(self, args=()):
        if self.one_arg:
            args = ' '.join(args).strip()

        # Execute subcommands if specified
        if self.sub_commands and args:
            if args[0] in self.sub_commands:
                return self.sub_commands[args[0]].exec(args[1:])
            else:
                return [
                    ("info", f"Sub-command "),
                    ("fail", args[0]),
                    ("info", ' not found\n'), *self.display_help()
                ], 'fail'


        # Execute with params here
        elif self.params and args:
            for p in self.params:
                return self.params[p](args)

        else:
            return self.exec_func()

    def __init__(self, name: str, data: dict):
        # Note that self.params will be ignored if there are sub-commands
        self.parent = None
        self.name = name
        self.help = data['help']
        self.params = {} if 'params' not in data else data['params']
        self.one_arg = False if 'one-arg' not in data else data['one-arg']
        self.sub_commands = {} if 'sub-commands' not in data else \
            {n: SubCommand(self, n, d) for n, d in data['sub-commands'].items()}

        # Wrap function for execution
        self.exec_func = self.display_help
        if 'exec' in data:
            if isinstance(data['exec'], tuple):
                def recurse_exec(d: list or tuple, v=None):
                    return v if not d else recurse_exec(d[1:], d[0](v) if v else d[0]())

                self.exec_func = lambda *_: recurse_exec(data['exec'])
            elif data['exec']:
                self.exec_func = data['exec']

    def display_help(self):

        command_color = 'command' if self.__class__.__name__ == 'Command' else 'sub_command'
        display = [
            (command_color, self.name),
            ('normal', ' usage:\n'),
            ('info', f' - {self.help}'),
            ('normal', '\n\n'),
            ('info', '>>  '),
            ('command', '' if not self.parent else self.parent.name + ' '),
            (command_color, self.name)
        ]

        if self.sub_commands:
            sub_commands = [('normal', ' ')]
            separator = ('info', '|')
            for command in self.sub_commands:
                sub_commands.append(('sub_command', command))
                sub_commands.append(('info', '|'))
            display.extend(sub_commands[:-1])

        elif self.params:
            display.append(('info', f' {" ".join(["<" + p + ">" for p in self.params])}'))

        return display

    def get_hints(self, args=(), params=False):
        if self.one_arg:
            args = ' '.join(args).strip()

        if self.sub_commands and args:
            for sub_command in self.sub_commands.values():
                if sub_command.name.startswith(args[0]):
                    return sub_command.name
            else:
                return None


class HelpCommand(Command):
    def __init__(self):
        data = {
            'help': 'displays all commands',
            'exec': self.display_help,
            'params': {'command': self.show_command_help}
        }
        super().__init__('help', data)

    def display_help(self):
        return [
            ('normal', 'Available commands:\n'),
            ('info', ' - Type '),
            ('command', 'help'),
            ('info', ' <command> for syntax\n\n'),
            ('command', '   '.join(commands))
        ]

    def show_command_help(self, cmd: list or tuple or str):
        if isinstance(cmd, list or tuple):
            root = cmd[0].strip()
            args = cmd[1:]
        else:
            root = cmd.strip()
            args = []

        if root in commands:
            for a in args:
                if a in commands[root].sub_commands:
                    return commands[root].sub_commands[a].display_help()
            return commands[root].display_help()

        else:
            return self.display_help()


class SubCommand(Command):
    def __init__(self, parent: Command, name: str, data: dict):
        super().__init__(name, data)
        self.parent = parent


# Define command behaviors and syntax trees
command_data = {
    'help': HelpCommand(),
    'exit': {
        'help': 'leaves the application',
        'exec': lambda: (_ for _ in ()).throw(urwid.ExitMainLoop())
    },
    'server': {
        'help': 'manage local servers',
        'sub-commands': {
            'list': {
                'help': 'lists installed server names (* - active)',
                'exec': list_servers
            },
            'info': {
                'help': 'displays basic information about a server',
                'one-arg': True,
                'params': {'server name': lambda name: manage_server(name, 'info')}
            },
            'start': {
                'help': 'launches a server by name',
                'one-arg': True,
                'params': {'server name': lambda name: manage_server(name, 'start')}
            },
            'stop': {
                'help': 'stops a server by name',
                'one-arg': True,
                'params': {'server name': lambda name: manage_server(name, 'stop')}
            },
            'restart': {
                'help': 'restarts a server by name',
                'one-arg': True,
                'params': {'server name': lambda name: manage_server(name, 'restart')}
            },
            'create': {
                'help': 'creates a Vanilla server on the latest version',
                'one-arg': True,
                'params': {'server name': lambda name: manage_server(name, 'create')}
            },
            'properties': {
                'help': "edit the 'server.properties' file",
                'one-arg': True,
                'params': {'server name': lambda name: edit_properties(name)}
            },
            'delete': {
                'help': 'deletes a server by name',
                'one-arg': True,
                'params': {'server name': lambda name: manage_server(name, 'delete')}
            },
        }
    },
    'backup': {
        'help': 'save or restore a server by name',
        'sub-commands': {
            'save': {
                'help': 'saves a back-up of a server by name',
                'one-arg': True,
                'params': {'server name': lambda name: manage_server(name, 'save')}
            },
            'restore': {
                'help': 'restores a server from the latest back-up by name',
                'one-arg': True,
                'params': {'server name': lambda name: manage_server(name, 'restore')}
            },
        }
    },
    'telepath': {
        'help': 'manage the Telepath API',
        'sub-commands': {
            'start': {
                'help': 'starts the Telepath API',
                'exec': (constants.api_manager.start, refresh_telepath_host)
            },
            'stop': {
                'help': 'stops the Telepath API',
                'exec': (constants.api_manager.stop, refresh_telepath_host)
            },
            'pair': {
                'help': 'listens for and displays pairing data to connect remotely',
                'exec': telepath_pair
            },
            'users': {
                'help': 'lists all paired and connected users',
                'exec': telepath_users,
            },
            'revoke': {
                'help': 'revoke access from a user by ID (they will need to re-pair)',
                'one-arg': True,
                'params': {'#ID': lambda user_id: telepath_revoke(user_id)}
            },
            'reset': {
                'help': 'removes all paired sessions and users',
                'exec': reset_telepath
            }
        }
    },
    'playit': {
        'help': 'tunnel a server through playit.gg',
        'sub-commands': {
            'enable': {
                'help': 'enable tunneling for a server by name',
                'one-arg': True,
                'params': {'server name': lambda name: enable_playit(name, enabled=True)}
            },
            'disable': {
                'help': 'disable tunneling for a server by name',
                'one-arg': True,
                'params': {'server name': lambda name: enable_playit(name, enabled=False)}
            },
        }
    },
    'update': {
        'help': 'manage local servers',
        'sub-commands': {
            'info': {
                'help': 'show the changelog of a pending update',
                'exec': lambda *_: update_app(info=True)
            },
            'install': {
                'help': 'install a pending update and restart',
                'exec': lambda *_: update_app()
            }
        }
    }
}
commands = {n: Command(n, d) if isinstance(d, dict) else d for n, d in command_data.items()}

# Display messages
command_header = '   ' if advanced_term else ' >>  '
response_header = '❯ ' if advanced_term else '> '
logo_widget = urwid.Text([('command', '\n'.join(logo))], align='center')
splash_widget = urwid.Text([('info', f"{constants.session_splash}\n")], align='center')
telepath_content = urwid.Text([('info', 'Initializing...')])

# Home screen status
content = []
if not constants.app_latest:
    content.extend([
        ("parameter", response_header),
        ("parameter", "(!) An update for auto-mcs is available. Run "),
        ("command", "update "),
        ("sub_command", "info "),
        ("parameter", "to learn more\n\n")
    ])
content.extend([('info', response_header), ('normal', f"Type a command, ?, or "), ('command', 'help')])
command_content = urwid.Text(content)

# Contains updating text in box
console = urwid.Pile([
    ('flow', telepath_content),
    urwid.Filler(command_content, valign='bottom')
    # urwid.ScrollBar(urwid.Scrollable(urwid.Filler(command_content, valign='bottom')))
])

title = f"auto-mcs v{constants.app_version} (headless)" if constants.app_latest else f"auto-mcs v{constants.app_version} (!)"
message_box = urwid.AttrMap(urwid.LineBox(console, title=title, title_attr=('normal' if constants.app_latest else 'parameter')), 'line')

refresh_telepath_host()

# Create an Edit widget for command input
disable_commands = False
command_history = []
history_index = 0

class CommandInput(urwid.Edit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hint_text = ''
        self.is_valid = False
        self.hint_params = 0

    def _valid(self, valid=True):
        self.is_valid = valid
        color = get_color('command') if valid else get_color('fail')
        loop.screen.register_palette_entry('input', *color[1:])

    def _get_hint_text(self, input_text):
        if input_text:
            command_name = input_text.split(' ')[0]
            self.hint_text = ''

            # Get root command object
            for command in commands.values():
                if command.name.startswith(command_name):
                    self._valid(True)

                    # Attempt to find sub-commands for a hint
                    if input_text.startswith(command.name) and command.sub_commands and input_text not in commands:
                        args = input_text.replace(command.name, '').strip().split(' ')
                        sub_hint = command.get_hints(args)
                        if not sub_hint:
                            self._valid(False)
                            return ""
                        else:
                            self.hint_text = f'{command.name} {sub_hint}'


                    # Check if there are parameters for root command instead
                    self.hint_params = 0
                    if not self.hint_text and command.params:
                        self.hint_params = 1
                        self._valid(True)
                        if input_text.strip().endswith(command.name) and ' ' not in input_text.strip():
                            self.hint_text = f'{command.name} {" ".join(["<" + p + ">" for p in command.params])}'

                        # Override "command" parameter to display commands
                        elif command.name in input_text and list(command.params.items())[0][0] == 'command':
                            command_start = ' '.join(input_text.split(' ', 1)[:1])
                            partial_name = input_text.split(' ', 1)[-1].strip()
                            for c in commands:
                                if c.lower().startswith(partial_name.lower()):
                                    self.hint_text = f'{command_start} {c}'
                                    break


                    if input_text.startswith(command.name) and command.sub_commands:
                        for sc in command.sub_commands.values():
                            if sc.params:
                                self.hint_params = 2
                                self._valid(True)
                                if input_text.strip().endswith(sc.name):
                                    self.hint_text = f'{input_text.strip()} {" ".join(["<" + p + ">" for p in sc.params])}'

                                # Override "server name" parameter to display server names
                                elif sc.name in input_text and list(sc.params.items())[0][0] == 'server name':
                                    command_start = ' '.join(input_text.split(' ', 2)[:2])
                                    partial_name = input_text.split(' ', 2)[-1].strip()
                                    for server in constants.server_list:
                                        if server.lower().startswith(partial_name.lower()):
                                            self.hint_text = f'{command_start} {server}'
                                            break

                    if not self.hint_text:
                        self.hint_text = command.name


                    # Return the rest of the command as the hint
                    return self.hint_text[len(input_text):]

        self._valid(False)
        return ""

    def get_text(self):
        input_text = super().get_edit_text()
        hint_text = self._get_hint_text(input_text)
        if hint_text:
            return self.hint_text, len(input_text)
        return input_text, len(input_text)

    def render(self, size, focus=False):
        original_text = input_text = super().get_edit_text()
        hint_text = self._get_hint_text(input_text)

        # Combine input text with hint text
        caption_space = ('caption_space', re.search(r'^\s+', self.caption)[0])
        caption_marker = ('caption_marker', self.caption.lstrip())

        if ' ' in input_text and self.is_valid:
            command = f"{original_text.split(' ', 1)[0]} "

            sub_command = ''
            if self.hint_params != 1:
                sub_command = original_text.split(' ')[1]
                try:
                    sub_command = sub_command + re.search(r'\s+', original_text[len(command + sub_command):])[0]
                except:
                    pass

            param = ''
            if 0 < self.hint_params <= original_text.strip().count(' '):
                param = original_text.split(' ', self.hint_params)[-1].replace(sub_command.strip(), '')


            # Add the text to a list
            input_text = []
            if command:
                input_text.append(('command', command))
            if sub_command:
                input_text.append(('sub_command', sub_command))
            if param:
                input_text.append(('parameter', param))

        else:
            input_text = ('input', input_text)

        combined_text = [caption_space, caption_marker, input_text, ('hint', hint_text)]

        # Create the canvas using urwid.Text
        text_widget = urwid.Text(combined_text)
        canvas = text_widget.render(size)

        # Ensure cursor shows at the correct position
        if focus:
            canvas = urwid.CompositeCanvas(canvas)
            cursor_position = len(self.caption) + self.edit_pos
            canvas.cursor = (cursor_position, 0)

        return canvas

    def cursor_x(self, size):
        return self.get_cursor_coords(size)[0] - len(self.caption)

    def keypress(self, size, key):
        actual_text = self.edit_text
        actual_index = self.get_cursor_coords(size)[0]

        if (key == 'backspace') and (actual_index - len(self.caption) == len(actual_text)):
            text, index = constants.control_backspace(actual_text, self.cursor_x(size))
            new_index = self.cursor_x(size) - index + len(self.caption)
            self.set_edit_text(text.strip())

            if text.endswith(' '):
                self.keypress(size, ' ')

            self.set_edit_pos(new_index)
            return None


        # Ignore excess spaces
        if key == ' ' and not self.text:
            return
        try:
            if key == ' ' and self.text[self.cursor_x(size)] != ' ':
                return
        except IndexError:
            pass


        # Show help content with "?"
        if key == '?':
            help_content = commands['help'].show_command_help(self.get_edit_text().split(' '))
            if help_content:
                command_content.set_text([('info', response_header), *help_content])
            return


        # Auto-complete
        if key in ('tab', 'right') and self.cursor_x(size) >= len(actual_text):
            if self.hint_text:

                # Add a space if there are sub-commands
                if self.hint_text in commands.keys():
                    if commands[self.hint_text].sub_commands:
                        self.hint_text += ' '

                # Format for params
                if ' ' in self.hint_text.strip():
                    command = self.hint_text.split(' ', 1)[0].strip()
                    sub_command = self.hint_text.split(' ', 1)[-1].strip()
                    if sub_command in commands[command].sub_commands.keys():
                        if commands[command].sub_commands[sub_command].params:
                            self.set_edit_text(self.text + ' ')
                            self.set_edit_pos(len(self.get_edit_text()))
                            return None

                # Don't autofill params
                if '<' in self.hint_text and '>' in self.hint_text and ' ' in self.edit_text:
                    return None

                # Don't auto-fill one command params
                elif ('<' in self.hint_text and '>' in self.hint_text) or (self.hint_text in commands and commands[self.hint_text].params):
                    self.set_edit_text(self.hint_text.split(' ', 1)[0] + ' ')
                    self.set_edit_pos(len(self.get_edit_text()))
                    return None


                # Complete text with the hint
                self.set_edit_text(self.hint_text)
                self.set_edit_pos(len(self.get_edit_text()))
                return None

        # Handle other keys normally
        result = super().keypress(size, key)

        # Update cursor position after handling keypress
        self.set_edit_pos(self.edit_pos)
        loop.draw_screen()

        return result

    def get_cursor_coords(self, size):
        return (len(self.caption) + self.edit_pos, 0)
command_edit = CommandInput(caption=command_header)


# Create a Pile for stacking widgets vertically
pile = urwid.Pile([
    ('flow', logo_widget),
    ('flow', splash_widget),
    ('weight', 0.5, urwid.Padding(message_box, left=1, right=1)),
    ('flow', command_edit)
])

# Wrap the pile in a padding widget to ensure it resizes with the terminal
top_widget = urwid.Padding(pile)

# Create a Frame to add a border around the top_widget
frame = urwid.Frame(top_widget)

# Define the color palette
palette = [
    ('caption_space', 'white', 'dark gray' if advanced_term else ''),
    ('caption_marker', 'dark gray', ''),
    ('input', 'light green', '', '', '#05e665', ''),
    ('hint', 'dark gray', ''),
    ('line', 'white', '', '', '#444444', ''),
    ('telepath_enabled', 'light cyan', ''),
    ('telepath_disabled', 'dark gray', ''),
    ('telepath_host', 'dark cyan', ''),

    # Command response formatting
    ('success', 'light green', ''),
    ('fail', 'light red', '', '', '#ff2020', ''),
    ('warn', 'yellow', ''),
    ('info', 'dark gray', ''),
    ('normal', 'white', ''),
    ('command', 'light green', '', '', '#05e665', ''),
    ('sub_command', 'dark cyan', '', '', '#13e8cc', ''),
    ('parameter', 'yellow', '', '', '#F3ED61', '')
]
def get_color(key):
    for c in palette:
        if key == c[0]:
            return c


# Create a Loop and run the UI
screen = urwid.raw_display.Screen()
screen.set_terminal_properties(colors=256)
screen.register_palette(palette)
loop = urwid.MainLoop(frame, unhandled_input=handle_input, screen=screen)



# ------------------------------------------- 'server.properties' Editor -----------------------------------------------

leftMargin = 4
status = "Viewing"
saveColor = 9

con_line = 0
con_col = 0

search_mode = False
search_text = ""
search_view = ""
search_banner = ""
search_list = []
current_match = 0
total_matches = 0
horizontal_control = ""
horizontal_scroll = 0
start_char = 0
end_char = 0
long_text = False
long_selected = False

class EditorWindow:

    def __init__(self, n_rows, n_cols, row=0, col=0):
        self.n_rows = n_rows
        self.n_cols = n_cols
        self.row = row
        self.col = col

    @property
    def bottom(self):
        return self.row + self.n_rows - 1

    def up(self, cursor):
        if cursor.row == self.row - 1 and self.row > 0:
            self.row -= 1

    def down(self, buffer, cursor):
        if cursor.row == self.bottom + 1 and self.bottom < buffer.bottom:
            self.row += 1

    def translate(self, cursor):
        return cursor.row - self.row, cursor.col - self.col

    def horizontal_scroll(self, cursor, buffer, left_margin=5, right_margin=2):
        global horizontal_scroll
        global horizontal_control
        global start_char
        global end_char
        global long_text

        try:
            line = buffer.__getitem__(cursor.row)

            try:
                line_key = line.split("=")[0] + " = "
                line_value = line.split("=")[1]

            except IndexError:
                line_key = line
                line_value = 0



            if (len(line) - 2 > self.n_cols - 10):

                if (self.col == 0) and (long_text is False) and (horizontal_scroll > 0):
                    weird_calc = len(buffer.__getitem__(cursor.row)) - self.n_cols + 10 if len(buffer.__getitem__(cursor.row)) - self.n_cols + 8 > 0 else 0
                    horizontal_scroll = weird_calc
                    start_char = weird_calc + 1
                    end_char = 0

                    cursor.col = len(line_key) + leftMargin + len(line_value[start_char:len(line_value) - end_char]) + 3 + 2

            horizontal_control = ""

        except IndexError:
            pass


    def undo(self, cursor, buffer, window, save=False):
        global undoHistory
        global status
        global saveColor
        global long_selected
        global horizontal_scroll
        global start_char
        global end_char


        if save is True:
            if not any(cursor.row in x for x in undoHistory):
                try:
                    undoHistory.append([cursor.row, buffer.__getitem__(cursor.row), window.row])
                except:
                    undoHistory.append([cursor.row, "", window.row])

        else:
            if undoHistory:
                cursor.row = undoHistory[-1][0]
                window.row = undoHistory[-1][2]
                buffer.lines.pop(cursor.row)
                new = undoHistory[-1][1]
                buffer.lines.insert(cursor.row, new)
                if cursor.col < len(buffer.__getitem__(cursor.row)) + leftMargin + 2:
                    cursor.col = len(buffer.__getitem__(cursor.row)) + leftMargin + 2
                else:
                    try:
                        if cursor.col > len(buffer.__getitem__(cursor.row)) + leftMargin + 2:
                            cursor.col = len(buffer.__getitem__(cursor.row)) + leftMargin + 2
                    except IndexError:
                        cursor.col = len(buffer.__getitem__(cursor.row).split("=")[0]) + 2 + leftMargin + 1
                undoHistory.pop(-1)

                if (len(new) - 2 > self.n_cols - 10) and (long_selected is True):
                    line_key = new.split("=")[0] + " = "
                    line_value = new.split("=")[1]

                    extra_space = 0 if horizontal_scroll > 1 else 1

                    weird_calc = len(new) - self.n_cols + 10 if len(new) - self.n_cols + 8 > 0 else 0
                    horizontal_scroll = weird_calc
                    start_char = weird_calc + 1
                    end_char = 0

                    cursor.col = len(line_key) + leftMargin + len(line_value[start_char:len(line_value) - end_char]) + 3 + extra_space


            if not undoHistory:
                status = "Viewing"
                saveColor = 9


class EditorCursor:
    def __init__(self, row=0, col=0, col_hint=None):
        self.row = row
        self._col = col
        self._col_hint = col if col_hint is None else col_hint

    @property
    def col(self):
        return self._col

    @col.setter
    def col(self, col):
        self._col = col
        self._col_hint = col


    def center(self, buffer):
        if self.row > len(buffer.lines) - 1:
            self.row = len(buffer.lines) - 1

        self._clamp_col(buffer)
        if self.col < len(buffer.__getitem__(self.row).split("=")[0]) + 2 + leftMargin + 1:
            self.col = len(buffer.__getitem__(self.row).split("=")[0]) + 2 + leftMargin + 1


    def up(self, buffer):
        if self.row > 0:
            self.row -= 1
            self._clamp_col(buffer)
            if self.col < len(buffer.__getitem__(self.row).split("=")[0]) + 2 + leftMargin + 1:
                self.col = len(buffer.__getitem__(self.row).split("=")[0]) + 2 + leftMargin + 1

    def down(self, buffer):
        if self.row < buffer.bottom:
            self.row += 1
            self._clamp_col(buffer)
            if self.col < len(buffer.__getitem__(self.row).split("=")[0]) + 2 + leftMargin + 1:
                self.col = len(buffer.__getitem__(self.row).split("=")[0]) + 2 + leftMargin + 1


    def _clamp_col(self, buffer):
        self._col = min(self._col_hint, len(buffer[self.row]))
        try:
            len(buffer.__getitem__(self.row).split("=")[1])
            self.col = len(buffer.__getitem__(self.row).split("=")[0]) + 2 + leftMargin + 1 + len(buffer.__getitem__(self.row).split("=")[1])

        except IndexError:
            self.col -= 1
            pass


    def left(self, buffer):
        global long_selected

        if self.col > len(buffer.__getitem__(self.row).split("=")[0]) + 2 + leftMargin + 1:
            self.col -= 1
        elif self.row > 0 and long_selected is False:
            self.row -= 1
            self.col = int(len(buffer[self.row]) + int(leftMargin)) + 2

    def right(self, buffer):
        if self.col < int(len(buffer[self.row]) + int(leftMargin)) + 2:
            if self.col < len(buffer.__getitem__(self.row).split("=")[0]) + 2 + leftMargin + 1:
                self.col = len(buffer.__getitem__(self.row).split("=")[0]) + 2 + leftMargin + 1
                self.row += 1
            else:
                self.col += 1
        elif self.row < buffer.bottom:
            self.row += 1
            self.col = len(buffer.__getitem__(self.row).split("=")[0]) + 2 + leftMargin + 1


def right(window, buffer, cursor):
    global long_selected

    cursor.right(buffer)
    window.down(buffer, cursor)

    if long_selected is False and len(buffer.__getitem__(cursor.row)) - 2 > window.n_cols - 10:
        window.horizontal_scroll(cursor, buffer)
        cursor.col = window.n_cols - 2


def left(window, buffer, cursor):
    global long_selected

    cursor.left(buffer)
    window.up(cursor)

    if long_selected is False and len(buffer.__getitem__(cursor.row)) - 2 > window.n_cols - 10:
        window.horizontal_scroll(cursor, buffer)
        cursor.col = window.n_cols - 2


class Buffer:
    def __init__(self, lines):
        self.lines = lines

    def __len__(self):
        return len(self.lines)

    def __getitem__(self, index):
        return self.lines[index]

    @property
    def bottom(self):
        return len(self) - 1

    def insert(self, cursor, string, window, buffer):
        global horizontal_scroll

        window.undo(cursor, buffer, window, save=True)

        horizontal_scroll = horizontal_scroll - 2 if horizontal_scroll > 0 else 0

        row, col = cursor.row, cursor.col - 4 + horizontal_scroll - 2
        current = self.lines.pop(row)
        new = current[:col] + string + current[col:]
        self.lines.insert(row, new)


    def split(self, cursor):
        row, col = cursor.row, cursor.col
        current = self.lines.pop(row)
        self.lines.insert(row, current[:col])
        self.lines.insert(row + 1, current[col:])


    def delete(self, cursor, window, buffer):
        global horizontal_scroll
        global horizontal_control
        global long_text
        global end_char
        global start_char
        global long_selected

        window.undo(cursor, buffer, window, save=True)

        horizontal_scroll = horizontal_scroll - 3 if horizontal_scroll > 0 else 0

        if (long_text is True) and (cursor.col + 2 >= window.n_cols - 5) and (horizontal_control == "backspace"):
            row, col = cursor.row, cursor.col - leftMargin + horizontal_scroll - 2
            if (row, col) < (self.bottom, len(self[row])):
                current = self.lines.pop(row)
                new = current[:col] + current[col + 1:]
                self.lines.insert(row, new)

            long_text = False
            return

        elif (long_selected is True) and (horizontal_scroll < 2) and (cursor.col + 2 >= window.n_cols - 5) and (horizontal_control == "backspace"):
            if end_char > 0:
                cursor.left(buffer)

        if long_text is True and horizontal_control == "delete" and (cursor.col + 2 <= window.n_cols - 1):

            if (end_char > 0) and (cursor.col + 2 <= window.n_cols - 4):

                end_char -= 1
                start_char += 1
                horizontal_scroll += 1

                row, col = cursor.row, cursor.col - leftMargin + horizontal_scroll - 2
                if (row, col) < (self.bottom, len(self[row])):
                    current = self.lines.pop(row)
                    new = current[:col] + current[col + 1:]
                    self.lines.insert(row, new)

                return

            else:
                cursor.right(buffer)

        elif long_text is True and horizontal_control == "delete" and (cursor.col + 2 >= window.n_cols - 5):
            return

        row, col = cursor.row, cursor.col - leftMargin + horizontal_scroll - 2
        if (row, col) < (self.bottom, len(self[row])):

            current = self.lines.pop(row)
            new = current[:col] + current[col + 1:]
            self.lines.insert(row, new)


def edit_properties(server_name: str):
    def editMain(stdscr):
        global undoHistory
        global status
        global saveColor
        global search_mode
        global search_text
        global search_view
        global search_banner
        global search_list
        global current_match
        global total_matches

        global horizontal_control
        global horizontal_scroll
        global start_char
        global end_char
        global long_text
        global long_selected

        global con_line
        global con_col

        buffer = None
        window = None

        last_key = ""
        long_selected = False
        long_text = False
        line_key = ""
        line_value = ""
        start_char = 0
        end_char = 0
        horizontal_scroll = 0
        horizontal_control = ""
        total_matches = 0
        current_match = 0
        search_list = []
        status = "Viewing"
        saveColor = 9
        undoHistory = []
        search_text = ""
        search_mode = False
        reset_cursor = False
        long_text = False
        right_lock = False

        filename = os.path.join(constants.serverDir, server_name, 'server.properties')
        if not os.path.exists(filename):
            constants.fix_empty_properties(server_name)

        with open(filename) as f:
            buffer = Buffer(f.read().splitlines())

        window = EditorWindow(curses.LINES - 1, curses.COLS - 1)

        index = 0
        for row, line in enumerate(buffer[window.row:window.row + window.n_rows]):
            if index == 2:
                cursor = EditorCursor(col=len(line) + leftMargin + 2, row=index)
                break
            index += 1

        # Custom colors
        curses.init_color(99, 950, 450, 150)   # Orange
        curses.init_color(98, 950, 250, 1000)  # Purple
        curses.init_color(100, 300, 850, 1000)    # Aqua

        curses.init_color(101, 300, 300, 1000)  # text blue
        curses.init_color(104, 300, 300, 1000)  # line-num color

        curses.init_color(102, 0, 800, 450)      # Saved
        curses.init_color(103, 800, 800, 600)    # Unsaved
        curses.init_color(105, 400, 400, 400)    # Gray
        curses.init_color(106, 120, 120, 120)    # Dark Gray
        curses.init_color(107, 600, 1000, 600)   # Select green
        curses.init_color(108, 1000, 1000, 1000) # White
        curses.start_color()

        curses.init_pair(9, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(10, curses.COLOR_BLACK, 103)
        curses.init_pair(11, curses.COLOR_BLACK, 102)
        curses.init_pair(3, 101, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_BLACK, 104)
        curses.init_pair(5, 105, curses.COLOR_BLACK)

        curses.init_pair(20, curses.COLOR_WHITE, 106)  # Search stuff
        curses.init_pair(21, 105, curses.COLOR_BLACK)
        curses.init_pair(22, curses.COLOR_BLACK, 107)

        curses.init_pair(30, 100, curses.COLOR_BLACK)  # String
        curses.init_pair(31, 99, curses.COLOR_BLACK)   # Int
        curses.init_pair(32, 98, curses.COLOR_BLACK)   # Bool

        curses.init_pair(40, 108, curses.COLOR_BLACK)  # Scrollbar bar
        curses.init_pair(41, 105, curses.COLOR_BLACK)  # Scrollbar line


        def generate_search():
            global search_text
            global search_view
            global search_banner
            global current_match
            global total_matches

            max_search_size = 20

            multiplier = (max_search_size - len(search_text))
            if multiplier < 1:
                multiplier = 1

            search_view = search_text
            if len(search_view) >= max_search_size:
                search_view = "..." + search_view[len(search_view) - max_search_size + 4:]

            total_matches = 0

            if search_text:
                for item in buffer:
                    if search_text in item:
                        total_matches += 1

            else:
                total_matches = 0

            current_match = total_matches if current_match > total_matches else current_match

            num_fix = 1
            if total_matches == 0:
                num_fix = 0


            # matches = '\n'.join(buffer).count(search_text) if len(search_text) > 0 else 0

            search_banner = " Ϙ ⁞  " + search_view + (" " * multiplier) + "  "
            search_banner = search_banner + f"│ {current_match + num_fix} / {total_matches} matches - 'ESC' " if len(search_text) > 0 else search_banner + f"│ 'ESC' to exit search "

            # if (cursor.row != (window.n_rows + window.row)) and (search_mode is True) and (len(search_text) > 0):
            #     search_banner += "- 'ESC' "


        def find_search(direction):
            global search_list
            global current_match

            foundItem = None

            if search_list:

                if direction == "down":

                    search_list = sorted(search_list)

                    for item in search_list:

                        if item[0] > cursor.row:

                            foundItem = item
                            break

                    foundItem = search_list[0] if foundItem is None else foundItem

                elif direction == "up":

                    search_list = sorted(search_list, reverse=True)

                    for item in search_list:

                        if item[0] < cursor.row:
                            foundItem = item
                            break

                    foundItem = search_list[0] if foundItem is None else foundItem

                elif direction == "first":

                    search_list = sorted(search_list)
                    foundItem = search_list[0]

                window.horizontal_scroll(cursor, buffer)
                cursor.row = foundItem[0]
                window.row = foundItem[1]
                current_match = foundItem[2]
                cursor.center(buffer)
                return foundItem



        while True:

            # Prevent stinky lil crash
            if cursor.col > window.n_cols:
                cursor.col = window.n_cols - 2

            stdscr.erase()
            x, y = stdscr.getmaxyx()
            con_line = y
            con_col = x

            statusText = f" {status} 'server.properties' (CTL+Q quit/+S save/+Z undo/+F search)"


            # Show scrollbar
            if (len(buffer.lines) > window.n_rows):

                height = round(window.n_rows / 1.2)
                offset = round((window.n_rows * 0.2) / 4)
                item = window.row / window.n_rows
                total = len(buffer) / window.n_rows

                # print(window.n_rows, x)

                bar_pos = math.ceil((item / total) * height)
                bar_len = math.ceil(height / total)

                handle_range = range(bar_pos, bar_pos + bar_len)

                try:
                    stdscr.addstr(offset, window.n_cols - 1, "↑", curses.color_pair(41))

                    for x in range(1, height + 1):

                        if x in handle_range:
                            stdscr.addstr(offset + x, window.n_cols - 1, "█", curses.color_pair(40))

                        else:
                            stdscr.addstr(offset + x, window.n_cols - 1, "│", curses.color_pair(41))

                    stdscr.addstr(offset + height + 1, window.n_cols - 1, "↓", curses.color_pair(41))
                except:
                    pass



            # Search mode
            try:

                if not search_mode:

                    stdscr.addstr(window.n_rows, curses.COLS // 2 - len(statusText) // 2, statusText, curses.color_pair(saveColor))

                else:

                    generate_search()

                    stdscr.addstr(window.n_rows, curses.COLS // 2 - len(search_banner) // 2, search_banner, curses.color_pair(20))


                # Find location of search matches
                search_list = []
                line_num = 0
                match_num = 0
                if search_text:
                    for row, line in enumerate(buffer):
                        if search_text in line:

                            scroll = len(buffer) - window.n_rows if len(buffer) - window.n_rows > 0 else 0

                            search_list.append([line_num, scroll, match_num])

                            match_num += 1

                        line_num += 1


                for row, line in enumerate(buffer[window.row:window.row + window.n_rows]):

                    # Check if line exceeds screen space
                    try:
                        horizontal_scroll = len(buffer.__getitem__(cursor.row)) - window.n_cols + 10 - end_char if len(buffer.__getitem__(cursor.row)) - window.n_cols + 8 > 0 else 0
                        weird_calc = len(buffer.__getitem__(cursor.row)) - window.n_cols + 10 if len(buffer.__getitem__(cursor.row)) - window.n_cols + 8 > 0 else 0

                        if (row == (cursor.row - window.row)) and (horizontal_control == "right") and (end_char < weird_calc + 1) and (long_text is False) and (cursor.col - 2 >= window.n_cols - 7):
                            horizontal_scroll += 2
                            start_char += 2
                            end_char -= 2


                        if horizontal_scroll < 2:
                            long_text = False
                            start_char = 0
                            end_char = weird_calc


                        if len(buffer.__getitem__(cursor.row)) - 2 > (window.n_cols - 10):
                            pass

                        else:
                            long_selected = False


                        if (row == (cursor.row - window.row)) and (len(line) - 2 > window.n_cols - 10):

                            line_key = line.split("=", 1)[0] + "="
                            line_value = line.split("=", 1)[1]

                            if long_text is False:
                                if (cursor.col - 2 >= window.n_cols - 5) and end_char > 0:
                                    left(window, buffer, cursor)
                                long_text = True
                                long_selected = True

                            # start_char = 0 if len(line) - window.n_cols + 10 < 0 else len(line) - window.n_cols + 11
                            start_char = horizontal_scroll + 1


                            if (start_char < 4 and (cursor.col + 2 <= window.n_cols - 8)) or horizontal_scroll < 0:
                                horizontal_scroll = 0
                                start_char = 0
                                end_char = weird_calc

                            if start_char > 0:

                                if horizontal_control in ["right", "insert"]:

                                    if end_char == 0:

                                        if horizontal_control in ["right", "insert"] and (cursor.col - 2 >= window.n_cols - 5):
                                            end_char = end_char - 1 if end_char > 0 else 0

                                        if horizontal_control in ["right", "insert"] and (cursor.col - start_char + 2 == window.n_cols - 4):
                                            start_char = start_char + 1 if start_char > 0 else start_char
                                            cursor.col = window.n_rows - 5 + 2


                                    elif end_char > 0:

                                        if horizontal_control == "right" and (cursor.col - 2 >= window.n_cols - 7):
                                            end_char = end_char - 1 if end_char > 2 else 0

                                        if horizontal_control == "right" and (cursor.col - start_char - 2 >= window.n_cols - 7):
                                            start_char = start_char + 1 if start_char > 0 else start_char
                                            cursor.col = window.n_rows - 8 + 2



                                elif horizontal_control == "backspace" and (cursor.col - start_char - 2 == window.n_cols - 4):
                                    start_char = start_char - 1 if start_char > 0 else start_char


                                elif horizontal_control == "left" and cursor.col - 2 <= len(line_key) + 7:
                                    end_char = end_char + 1 # if cursor.col - len(line_key) - 4 > 3 else 0
                                    start_char = start_char - 1 if start_char > 0 else start_char
                                    cursor.col = len(line_key) + 7 + 2


                            if horizontal_scroll < 2:
                                start_char = 0
                                horizontal_scroll = 0
                                end_char = weird_calc



                            line = line_value[start_char:len(line_value) - end_char]
                            line = line_key + "..." + line if horizontal_scroll > 0 else line_key + line + "..."


                            end = -3
                            if ((horizontal_control == "right") and (end_char > 0) and (cursor.col - 2 >= window.n_cols - 7)) or (end_char == weird_calc):
                                end = -4


                            line = line[:end] + "..." if end_char > 0 else line


                            horizontal_control = ""


                        elif (len(line) - 2 > window.n_cols - 10):
                            line = line[:window.n_cols - 11] + "..."


                        right_lock = False
                        if end_char > 0:
                            right_lock = True


                        # debug use
                        # stdscr.addstr(0, window.n_cols - len(f"{long_selected}, {long_text}, {weird_calc}, {horizontal_scroll}, {start_char}, {end_char}"), f"{long_selected}, {long_text}, {weird_calc}, {horizontal_scroll}, {start_char}, {end_char}")
                        # stdscr.addstr(0, window.n_cols - len(last_key) - 1, last_key)

                    except IndexError:
                        cursor.row = 0 if cursor.row < 0 or cursor.row > window.n_rows + window.row else cursor.row



                    if window.row < buffer.bottom - window.n_rows + 1:
                        stdscr.addstr(window.n_rows, 0, " ▼ more ▼", curses.color_pair(5))

            # Line counter
                    rowNumber = str(window.row + row + 1) + " "
                    if len(rowNumber) == 2:
                        rowNumber = " " + rowNumber

                    if len(rowNumber) > 3:
                        rowNumber = str(window.row + row + 1)

                    stdscr.addstr(row, 0, rowNumber, curses.color_pair(4))


            # Highlight matches in search
                    sassy_line = buffer.__getitem__(row + window.row).replace("=", " = ", 1)

                    if (len(search_text) > 0) and (search_text in sassy_line) and (search_mode is True):
                        line = line.replace("=", " = ", 1)
                        lines = line.split(search_text)

                        length = 0
                        line_key = sassy_line.split('=')[0] + ' = '
                        match_pos = len(line_key) + leftMargin + sassy_line.find(search_text)
                        start_text = horizontal_scroll if cursor.row != row + window.row else match_pos - len(search_text) - 3 - len(line_key) - leftMargin

                        # Long string
                        if ((((len(sassy_line) - 2 > window.n_cols - 10) and len(sassy_line.split('=')[0] + ' = ') + leftMargin + sassy_line.find(search_text) > window.n_cols - 10) or (horizontal_scroll > start_text)) and (search_text not in line_key)):

                            if cursor.row != row + window.row:
                                stdscr.addstr(row, leftMargin, line.split("...")[0], curses.color_pair(21))
                                stdscr.addstr(row, leftMargin + len(line.split("...")[0]), "...", curses.color_pair(22))

                            else:
                                start = start_char + leftMargin + len(line_key) + 5
                                end = len(sassy_line.split(' = ')[1] + ' = ') - end_char + leftMargin + len(line_key) - len(search_text) + 2

                                # stdscr.addstr(window.n_rows, window.n_cols - len(f"{start}, {end}, {match_pos}, {horizontal_scroll}"), f"{start}, {end}, {match_pos}, {horizontal_scroll}")

                                if (match_pos not in range(start, end) and (search_text not in line_key)) or (horizontal_scroll > start_text):
                                    if (match_pos < start and horizontal_scroll > 0) or (horizontal_scroll > start_text) and (long_selected is True):
                                        stdscr.addstr(row, leftMargin, line_key, curses.color_pair(21))
                                        stdscr.addstr(row, leftMargin + len(line_key) + 3, line.split("...", 1)[1], curses.color_pair(21))
                                        stdscr.addstr(row, leftMargin + len(line_key), "...", curses.color_pair(22))

                                    elif end_char > 0:
                                        stdscr.addstr(row, leftMargin, line_key, curses.color_pair(21))
                                        stdscr.addstr(row, leftMargin + len(line_key), line.split(" = ", 1)[1], curses.color_pair(21))
                                        stdscr.addstr(row, leftMargin + len(line_key) + len(line.split(" = ", 1)[1]) - 3, "...", curses.color_pair(22))

                                    else:

                                        for item in lines:
                                            stdscr.addstr(row, leftMargin + length, item, curses.color_pair(21))
                                            length += len(item)

                                            if lines.index(item) != len(lines) - 1:
                                                # Highlight
                                                stdscr.addstr(row, leftMargin + length, search_text, curses.color_pair(22))
                                                length += len(search_text)

                                else:

                                    for item in lines:
                                        stdscr.addstr(row, leftMargin + length, item, curses.color_pair(21))
                                        length += len(item)

                                        if lines.index(item) != len(lines) - 1:

                                            # Highlight
                                            stdscr.addstr(row, leftMargin + length, search_text, curses.color_pair(22))
                                            length += len(search_text)

                        # Normal string
                        else:

                            for item in lines:
                                stdscr.addstr(row, leftMargin + length, item, curses.color_pair(21))
                                length += len(item)

                                if lines.index(item) != len(lines) - 1:

                                    # Highlight
                                    stdscr.addstr(row, leftMargin + length, search_text, curses.color_pair(22))
                                    length += len(search_text)


                    elif "=" in line:

                        try:
                            line = line.split("=", 1)
                            stdscr.addstr(row, leftMargin, line[0], curses.color_pair(3))

                            if cursor.row == window.row + row:
                                stdscr.addstr(row, len(line[0]) + leftMargin, " = ")

                            else:
                                stdscr.addstr(row, len(line[0]) + leftMargin, " = ", curses.color_pair(5))


                            # Register colors for different data types

                            # Int
                            try:
                                test = float(line[1])
                                is_int = True
                            except ValueError:
                                is_int = False

                            if is_int is True:
                                stdscr.addstr(row, len(line[0]) + leftMargin + 3, line[1], curses.color_pair(31))

                            # Bool
                            elif line[1] in ["true", "false"]:
                                stdscr.addstr(row, len(line[0]) + leftMargin + 3, line[1], curses.color_pair(32))

                            # String
                            else:
                                stdscr.addstr(row, len(line[0]) + leftMargin + 3, line[1], curses.color_pair(30))

                        except:
                            left(window, buffer, cursor)
                            buffer.delete(cursor, window, buffer)
                    else:
                        stdscr.addstr(row, leftMargin, line, curses.color_pair(5))

                try:
                    stdscr.move(*window.translate(cursor))
                except curses.error:
                    window.row = cursor.row
                    # continue

                if (cursor.row == (window.n_rows + window.row)) and (search_mode is True):
                    charTest = ["", 0]

                else:
                    charTest = buffer.__getitem__(cursor.row).split("=")

            except curses.error:
                try:
                    if curses.KEY_RESIZE == last_key:
                        print(True)
                        stdscr.refresh()
                        time.sleep(0.5)
                        # continue
                except:
                    time.sleep(0.5)

                print('fail')


            if reset_cursor is True:
                cursor.row = window.n_rows + window.row
                generate_search()

                cursor.col = round(con_col / 2) - round(len(search_banner) / 2) + 6 + len(search_view)

            reset_cursor = False


    # user input
            k = stdscr.getch()
            if k >= 0:
                last_key = str(k)


            # Detect key input
            print(k)
            if k > 0:

                if k == 17: # CTRL+Q
                    stdscr.erase()
                    return

                elif k == 26: # CTRL+Z
                    window.undo(cursor, buffer, window, save=False)

                elif k == 19: # CTRL+S
                    status = "Saved"
                    saveColor = 11


                # Save file
                    outFile = ""
                    for row, line in enumerate(buffer[:buffer.bottom + 1]):
                        outFile += line + "\n"

                    with open(filename, 'w') as f:
                        f.write(outFile)


                # Toggle search mode
                elif k == 6: # CTRL+F
                    search_mode = True

                    generate_search()

                    cursor.row = window.n_rows + window.row
                    cursor.col = round(con_col / 2) - round(len(search_banner) / 2) + 5 + len(search_view) + 1 # + (4 if (len(search_text) > 0) else 0)



                # Paste content
                elif k == 22: # CTRL+V

                    if "=" in buffer.__getitem__(cursor.row):
                        data = pyperclip.paste().replace("\n", "    ").replace("\r", "")

                        buffer.insert(cursor, data, window, buffer)
                        cursor.col += len(data)



                elif k == 27: # ESC

                    if cursor.row > (window.n_rows + window.row) - 1:

                        if total_matches == 0:
                            cursor.row = 0
                            window.row = 0
                        else:
                            cursor.row = search_list[current_match][0]
                            window.row = search_list[current_match][1]

                    search_mode = False
                    total_matches = 0
                    cursor.center(buffer)


                elif k == 259: # up arrow

                    if (search_mode is False) or (total_matches == 0):
                        cursor.up(buffer)
                        window.up(cursor)
                        window.horizontal_scroll(cursor, buffer)

                    else:
                        find_search("up")



                elif k == 258: # down arrow

                    if (search_mode is False) or (total_matches == 0):
                        cursor.down(buffer)
                        window.down(buffer, cursor)
                        window.horizontal_scroll(cursor, buffer)

                    else:
                        find_search("down")


                elif k == 260: # left arrow
                    if (cursor.row != (window.n_rows + window.row)):
                        horizontal_control = "left"
                        cursor.left(buffer)
                        window.up(cursor)
                        # window.horizontal_scroll(cursor, buffer)

                elif k == 261: # right arrow
                    if (cursor.row != (window.n_rows + window.row)):
                        horizontal_control = "right"

                        if (horizontal_scroll == 0) or ((horizontal_scroll > 0) and (cursor.col - 2 <= window.n_cols - 5)):

                            if ((cursor.col - 2 >= window.n_cols - 7) and (right_lock is True)):
                                pass

                            else:
                                right(window, buffer, cursor)


                elif k == 9: # TAB
                    if search_mode:

                        if cursor.row == window.n_rows + window.row:

                            if cursor.row > (window.n_rows + window.row) - 1:
                                cursor.row = (window.n_rows + window.row) - 1

                            cursor.center(buffer)

                        else:
                            generate_search()

                            cursor.row = window.n_rows + window.row
                            cursor.col = round(con_col / 2) - round(len(search_banner) / 2) + 5 + len(search_view) + 3 # + (4 if (len(search_text) > 0) else 0)


                elif k == 330: # DELETE

                    if (cursor.row != (window.n_rows + window.row)):
                        if cursor.col - 2 > int(len(charTest[0]) + leftMargin):
                            horizontal_control = "delete"
                            buffer.delete(cursor, window, buffer)
                            if status != "Editing":
                                status = "Editing"
                                saveColor = 10

                elif k == 8: # backspace

                    if search_mode:

                        find_search("first")
                        reset_cursor = True

                        search_text = "" if len(search_text) == 1 else search_text[:-1]

                        generate_search()

                        cursor.col = round(con_col / 2) - round(len(search_banner) / 2) + 5 + len(search_view) + 1

                    elif (cursor.row, cursor.col) > (0, 0):
                        if cursor.col - 2 > int(len(charTest[0]) + leftMargin + 1):
                            horizontal_control = "backspace"

                            if (horizontal_scroll == 0) and (cursor.col > len(buffer.__getitem__(cursor.row).split("=")[0]) + 2 + leftMargin + 1):

                                left(window, buffer, cursor)

                            buffer.delete(cursor, window, buffer)
                            if status != "Editing":
                                status = "Editing"
                                saveColor = 10


                elif k in [262, 358] and long_selected is True: # HOME/END keys

                    try:
                        line = buffer.__getitem__(cursor.row)
                        weird_calc = len(buffer.__getitem__(cursor.row)) - window.n_cols + 10 if len(buffer.__getitem__(cursor.row)) - window.n_cols + 8 > 0 else 0

                        try:
                            line_key = line.split("=")[0] + " = "
                            line_value = line.split("=")[1]

                        except IndexError:
                            line_key = line
                            line_value = 0

                        if k == 358:
                            if (len(line) - 2 > window.n_cols - 10):
                                random_char = 1 if horizontal_scroll == 0 else 0

                                horizontal_scroll = weird_calc
                                start_char = weird_calc + 1
                                end_char = 0

                                cursor.col = len(line_key) + leftMargin + len(line_value[start_char:len(line_value) - end_char]) + 3 + random_char

                        else:
                            if (len(line) - 2 > window.n_cols - 10):
                                horizontal_scroll = 0
                                start_char = 0
                                end_char = weird_calc

                                cursor.col = len(line_key) + leftMargin

                        horizontal_control = ""

                    except IndexError:
                        pass


                elif k == 10: # ENTER
                    "do nothing"

                elif k >= 0:
                    k = chr(k)
                    if len(k) == 1:

                        if search_mode:

                            search_text += k

                            find_search("first")
                            reset_cursor = True

                            generate_search()

                            cursor.col = round(con_col / 2) - round(len(search_banner) / 2) + 6 + len(search_view)

                        elif (cursor.col - 2 > int(len(charTest[0]) + leftMargin)):
                            try:
                                str(charTest[1])

                                horizontal_control = "insert"

                                buffer.insert(cursor, k, window, buffer)
                                for _ in k:

                                    if horizontal_scroll == 0:

                                        if ((cursor.col - 1 >= window.n_cols - 7) and (right_lock is True)):
                                            if long_text is False:
                                                right(window, buffer, cursor)
                                                horizontal_scroll += 1
                                                end_char -= 1
                                                start_char += 1
                                            pass

                                        else:
                                            right(window, buffer, cursor)

                                if status != "Editing":
                                    status = "Editing"
                                    saveColor = 10
                            except IndexError:
                                pass

    curses.wrapper(editMain)



# ------------------------------------------------ Launch Menu ---------------------------------------------------------


    # Give an error if elevated
    if constants.is_admin() and not constants.is_docker:
        print(f"\n> Error:  Running auto-mcs as {'administrator' if constants.os_name == 'windows' else 'root'} can expose your system to security vulnerabilities\n\nPlease restart with standard user privileges to continue")
        return False


    # Launch servers if requested with the flag
    for server in constants.boot_launches:
        print(f"\n> Launching '{server}', please wait...")
        constants.server_manager.open_server(server)
        threading.Timer(0, constants.server_manager.current_server.launch).start()

        if len(constants.boot_launches) > 1:
            while server not in constants.server_manager.running_servers:
                time.sleep(0.5)
            time.sleep(2)
        print('+ Done!')


    # Initialize telepath menu overrides
    class TelepathPair():
        def __init__(self):
            self.is_open = False
            self.pair_data = {}

        # Close "popup"
        def close(self):
            if not self.is_open:
                return

            current_user = constants.api_manager.current_user
            if current_user and current_user['host'] == self.pair_data['host']['host'] and current_user['user'] == self.pair_data['host']['user']:
                message = f"Successfully paired with '${current_user['host']}/{current_user['user']}$'"
            else:
                message = f'$Telepath$ pair request expired'

            # Reset token if cancelled
            if constants.api_manager.pair_data:
                constants.api_manager.pair_data = {}

            self.is_open = False
            self.pair_data = {}

        # Displays "popup"
        def open(self, data: dict):
            if self.is_open:
                return

            self.pair_data = data
    def telepath_banner(message: str, finished: bool, play_sound=None):
        return None
    def telepath_disconnect():
        return None
    constants.telepath_pair = TelepathPair()
    constants.telepath_banner = telepath_banner
    constants.telepath_disconnect = telepath_disconnect
    telepath.create_endpoint(constants.telepath_banner, 'main', True)


    try:
        # Disable STDOUT
        if constants.os_name == 'windows':
            old_std_err = sys.stderr
            sys.stderr = NullWriter()
        else:
            old_std_out = sys.stdout
            sys.stdout = NullWriter()


        # Run UI
        loop.run()


        # Enable STDOUT
        if constants.os_name == 'windows':
            sys.stderr = old_std_err
        else:
            sys.stdout = old_std_out

        # Stop all running servers
        for server in [s for s in constants.server_manager.running_servers.values()]:
            if server.running:
                print(f"\n> Stopping '{server.name}', please wait...")
                server.stop()
                while server.running:
                    time.sleep(0.5)
                print('+ Done!')

    # Close gracefully on CTRL-C
    except KeyboardInterrupt:
        pass
