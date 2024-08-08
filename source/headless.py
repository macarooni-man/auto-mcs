import threading
import urwid
import time
import sys
import re

import constants
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
    command = command_edit.text.strip(command_header)

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
    if cmd not in command_history[:1]:
        command_history.insert(0, cmd)

    command_edit.set_edit_text('')
    response = f"Type a command, or 'help'"
    if cmd.strip():
        try:
            # Format raw data into command, and args
            raw = [a.strip() for a in cmd.split(' ') if a.strip()]
            cmd = raw[0]
            args = () if len(raw) < 2 else raw[1:]

            # Process command and return output
            command = commands[cmd]
            output = command.exec(args)
            response = output

        except KeyError:
            response = f"Unknown command '{cmd}'.\n{response}"

    # Capitalize response
    response = f'{response[0].upper()}{response[1:]}'
    command_content.set_text(response)


def update_console(text: str):
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
            return "Server creation requires an internet connection"

        # Name input validation
        if len(name) < 25:
            if '\n' in name:
                name = name.splitlines()[0]
            name = re.sub('[^a-zA-Z0-9 _().-]', '', name)
        else:
            return f"'{name}' is too long, shorten it and try again (25 max)"

        if name.lower() in constants.server_list_lower:
            return f"'{name}' already exists"


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
        return f"Successfully created '{name}' (Vanilla {constants.latestMC['vanilla']})\nTo modify this server, run 'telepath pair' to connect from a remote instance of auto-mcs"

    # Manage existing servers
    elif name.lower() in constants.server_list_lower:
        server_obj = constants.server_manager.open_server(name)

        if action == 'start':
            func_wrapper(server_obj.launch)
            return return_log(f"Launched '{name}'")

        elif action == 'stop':
            func_wrapper(server_obj.stop)
            return return_log(f"Stopped '{name}'")

        elif action == 'restart':
            if server_obj.running:
                func_wrapper(server_obj.restart)
                return return_log(f"Restarted '{name}'")
            else:
                return return_log(f"'{name}' is not launched")

        elif action == 'delete':
            if not server_obj.running:
                func_wrapper([server_obj.delete, constants.generate_server_list])
                return return_log(f"Deleted '{name}' and saved a back-up")
            else:
                return return_log(f"'{name}' is running, please run 'server stop {name}' first")

        elif action == 'save':
            update_console(f"Saving a back-up of '{name}'...")
            if not server_obj.backup:
                time.sleep(0.1)
            server_obj.backup.save()
            constants.server_manager.current_server.reload_config()
            return return_log(f"Saved a back-up of '{name}'")

        elif action == 'restore':
            if not server_obj.running:
                if not server_obj.backup:
                    time.sleep(0.1)
                update_console(f"Restoring latest back-up of '{name}'...")
                server_obj.backup.restore(server_obj.backup.list[0])
                constants.server_manager.current_server.reload_config()
                return return_log(f"Restored '{name}' to the latest back-up")
            else:
                return return_log(f"'{name}' is running, please run 'server stop {name}' first")

    # If server doesn't exist
    else:
        return f"'{name}' does not exist"


# Refreshes telepath display data at the top
def refresh_telepath_host(data=None):
    api = constants.api_manager
    header = f'Telepath API (v{constants.api_manager.version})\n'

    if api.running:
        host = api.host
        if host == '0.0.0.0':
            host = constants.get_private_ip()
        text = f'> {host}:{api.port}'

    else:
        text = ' < not running >'
    telepath_content.set_text(header + text)
    return data


def telepath_pair(data=None):
    final_text = f'Failed to pair, please run \'telepath pair\' again.'

    update_console('Listening to pair requests for 3 minutes. Enter the IP above into another instance of auto-mcs to continue.')
    constants.api_manager.pair_listen = True
    timeout = 0
    while 'code' not in constants.api_manager.pair_data:
        time.sleep(1)
        timeout += 1
        if timeout >= 180:
            return final_text

    data = constants.api_manager.pair_data
    update_console(f'< {data["host"]["host"]}/{data["host"]["user"]} >\nCode (expires 1m):  {data["code"]}')

    timeout = 0
    while constants.api_manager.pair_data:
        time.sleep(1)
        timeout += 1
        if timeout >= 60:
            return final_text

    if constants.api_manager.current_user:
        user = constants.api_manager.current_user
        final_text = f'Successfully paired with "{user["host"]}/{user["user"]}:{user["ip"]}"'

    constants.api_manager.pair_listen = False

    return final_text


class Command:

    def exec(self, args=()):
        if self.one_arg:
            args = ' '.join(args).strip()

        # Execute subcommands if specified
        if self.sub_commands and args:
            if args[0] in self.sub_commands:
                return self.sub_commands[args[0]].exec(args[1:])
            else:
                return f"Sub-command '{args[0]}' not found\n{self.display_help()}"

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
        parent = '' if not self.parent else self.parent.name + ' '

        display = f"{self.name} usage:\n - {self.help}\n>>  {parent}{self.name}"
        if self.sub_commands:
            display += f' {"|".join(self.sub_commands)}'

        elif self.params:
            display += f' {" ".join(["<" + p + ">" for p in self.params])}'

        return display


class HelpCommand(Command):
    def __init__(self):
        data = {
            'help': 'displays all commands',
            'exec': self.display_help,
            'params': {'command': self.show_command_help}
        }
        super().__init__('help', data)

    def display_help(self):
        return f"Available commands:\n - Type 'help <command>' for syntax\n{', '.join(commands)}"

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
                'exec': lambda *_: f'Installed Servers, * - active ({len(constants.server_list)} total):\n{", ".join("*"+s if s in constants.server_manager.running_servers else s for s in constants.server_list)}'
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
                'help': 'creates a new server',
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
            }
        }
    }
}
commands = {n: Command(n, d) for n, d in command_data.items()}
commands['help'] = HelpCommand()


# Display messages
logo_widget = urwid.Text('\n'.join(logo), align='center')
splash_widget = urwid.Text(f"{constants.session_splash}\n", align='center')
telepath_content = urwid.Text('Initializing...')
command_content = urwid.Text("Type a command, or 'help'")

# Contains updating text in box
console = urwid.Pile([
    ('flow', telepath_content),
    urwid.Filler(command_content, valign='bottom')
])

message_box = urwid.LineBox(console, title=f"auto-mcs v{constants.app_version} (headless)")
refresh_telepath_host()

# Create an Edit widget for command input
command_header = '>>  '
disable_commands = False
command_history = []
history_index = 0
command_edit = urwid.Edit(command_header)

# Create a Pile for stacking widgets vertically
pile = urwid.Pile([
    ('flow', logo_widget),
    ('flow', splash_widget),
    ('weight', 0.5, message_box),
    ('flow', command_edit)
])

# Wrap the pile in a padding widget to ensure it resizes with the terminal
top_widget = urwid.Padding(pile, left=1, right=1)

# Create a Frame to add a border around the top_widget
frame = urwid.Frame(top_widget)

# Create a Loop and run the UI
loop = urwid.MainLoop(frame, unhandled_input=handle_input)



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
    constants.telepath_pair = TelepathPair()
    constants.telepath_banner = lambda *_: None
    constants.telepath_disconnect = lambda *_: None


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
