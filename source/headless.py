import threading
import urwid
import time
import sys
import re

import constants
import telepath
import acl


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

    command_content.set_text([('success' if success else 'fail', '❯ '), *response])


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
            ("info", f"(Vanilla {constants.latestMC['vanilla']})\n"),
            ("info", " - to modify this server, run "),
            ("command", "telepath "),
            ("sub_command", "pair "),
            ("info", "to connect from a remote instance of auto-mcs")
        ]


    # Manage existing servers
    elif name.lower() in constants.server_list_lower:
        server_obj = constants.server_manager.open_server(name)

        if action == 'start':
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

def show_servers():
    if constants.server_list:
        return_text = [('normal', f'Installed Servers'),  ('success', ' * - active'), ('info', f' ({len(constants.server_list)} total):\n\n')]
        for server in constants.server_list:
            running = server in constants.server_manager.running_servers
            return_text.append(('success' if running else 'info', f'{"*" if running else ""}{server}    '))
        return return_text
    else:
        return [('info', 'No servers were found')], 'fail'


# Refreshes telepath display data at the top
def refresh_telepath_host(data=None):
    api = constants.api_manager
    header = ('telepath_header', f'Telepath API (v{constants.api_manager.version})\n')

    if api.running:
        host = api.host
        if host == '0.0.0.0':
            host = constants.get_private_ip()
        text = ('telepath_enabled', f'> {host}:{api.port}')

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
    final_text = f'Failed to pair, please run \'telepath pair\' again.'

    update_console([('success', '❯ '), ('normal', 'Listening to pair requests for 3 minutes'), ('parameter', '\n\nEnter the IP above into another instance of auto-mcs to continue')])
    constants.api_manager.pair_listen = True
    timeout = 0

    try:
        while 'code' not in constants.api_manager.pair_data:
            time.sleep(1)
            timeout += 1
            if timeout >= 180:
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


# Override print
def print(*args, **kwargs):
    telepath_content.set_text(" ".join([str(a) for a in args]))


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


command_data = {
    'exit': {
        'help': 'leaves the application',
        'exec': lambda: (_ for _ in ()).throw(urwid.ExitMainLoop())
    },
    'server': {
        'help': 'manage local servers',
        'sub-commands': {
            'list': {
                'help': 'lists installed server names (* - active)',
                'exec': show_servers
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
                'exec': lambda *_: 'implement a function to return all users here'
            },
            'reset': {
                'help': 'removes all paired sessions and users',
                'exec': reset_telepath
            }
        }
    }
}
commands = {n: Command(n, d) for n, d in command_data.items()}
commands['help'] = HelpCommand()


# Display messages
logo_widget = urwid.Text([('command', '\n'.join(logo))], align='center')
splash_widget = urwid.Text([('info', f"{constants.session_splash}\n")], align='center')
telepath_content = urwid.Text([('info', 'Initializing...')])
command_content = urwid.Text([('info', '❯ '), ('normal', f"Type a command, ?, or "), ('command', 'help')])

# Contains updating text in box
console = urwid.Pile([
    ('flow', telepath_content),
    urwid.Filler(command_content, valign='bottom')
])

message_box = urwid.LineBox(console, title=f"auto-mcs v{constants.app_version} (headless)")
refresh_telepath_host()

# Create an Edit widget for command input
command_header = '   '
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
                command_content.set_text([('info', '❯ '), *help_content])
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
    ('caption_space', 'white', 'dark gray'),
    ('caption_marker', 'dark gray', ''),
    ('input', 'light green', '', '', '#05e665', ''),
    ('hint', 'dark gray', ''),
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



def run_application():

    # Give an error if elevated
    if constants.is_admin():
        print(f"\n> Error:  Running auto-mcs as {'administrator' if constants.os_name == 'windows' else 'root'} can expose your system to security vulnerabilities.\n\nPlease restart with standard user privileges to continue")
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
