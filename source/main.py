# Local imports
from svrmgr import ServerManager
import constants


# Run app, eventually in wrapper
def mainLoop():

    # Fixes display scaling on Windows - Eventually add this to the beginning of wrapper.py
    if constants.os_name == "windows" and not constants.headless:
        from ctypes import windll, c_int64

        # Calculate screen width and disable DPI scaling if bigger than a certain resolution
        try:
            width = windll.user32.GetSystemMetrics(0)
            scale = windll.shcore.GetScaleFactorForDevice(0) / 100
            if (width * scale) < 2000:
                windll.user32.SetProcessDpiAwarenessContext(c_int64(-4))
        except:
            print('Error: failed to set DPI context')


    # Cleanup temp files and generate splash text
    constants.cleanup_old_files()
    constants.generate_splash()
    constants.get_refresh_rate()

    # Instantiate Server Manager
    constants.server_manager = ServerManager()


    # Only start the GUI if not headless
    if not constants.headless:
        from menu import run_application
        run_application()


    # Otherwise, start a loop for a CLI interpreter with basic commands
    else:
        import urwid

        logo = ["                           _                                 ",
                "   ▄▄████▄▄     __ _ _   _| |_ ___       _ __ ___   ___ ___  ",
                "  ▄█  ██  █▄   / _` | | | | __/ _ \  __ | '_ ` _ \ / __/ __| ",
                "  ███▀  ▀███  | (_| | |_| | || (_) |(__)| | | | | | (__\__ \ ",
                "  ▀██ ▄▄ ██▀   \__,_|\__,_|\__\___/     |_| |_| |_|\___|___/ ",
                "   ▀▀████▀▀                                                  ",
                ""
        ]

        # Handle processing commands
        def handle_input(key):
            command = command_edit.text.strip(command_header)

            # On enter:
            if key == 'enter':
                process_command(command)

        def process_command(cmd):
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
            command_edit.set_edit_text('')

        def refresh_telepath_host(data=None):
            api = constants.api_manager
            header = f'Telepath API (v{constants.api_data["version"]})\n'

            if api.running:
                host = api.host
                if host == '0.0.0.0':
                    host = constants.get_private_ip()
                text = f'> {host}:{api.port}'

            else:
                text = ' < not running >'
            telepath_content.set_text(header + text)
            return data

        class Command:

            def exec(self, args=()):
                if self.sub_commands and args:
                    if args[0] in self.sub_commands:
                        return self.sub_commands[args[0]].exec(args[1:])
                    else:
                        return f"Sub-command '{args[0]}' not found"

                # Implement params here

                else:
                    return self.exec_func()



            def __init__(self, name: str, data: dict):
                # Note that self.params will be ignored if there are sub-commands

                self.name = name
                self.help = data['help']
                self.params = {} if 'params' not in data else data['params']
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
                return self.help

        class SubCommand(Command):
            def __init__(self, parent: Command, name: str, data: dict):
                super().__init__(name, data)
                self.parent = parent

        command_data = {
            'help': {
                'help': 'displays all commands',
                'params': {'command': None}
            },
            'exit': {
                'help': 'leaves the application',
                'exec': lambda: (_ for _ in ()).throw(urwid.ExitMainLoop())
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
                        'help': 'displays pairing data to connect remotely',
                        'exec': constants.api_manager.pair
                    }
                }
            }
        }
        commands = {n: Command(n, d) for n, d in command_data.items()}


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

        try:
            loop.run()
        except KeyboardInterrupt:
            pass



# ----------------------------------------------------------------------------------------------
#                             _
#                  __ _ _   _| |_ ___                   < Module execution chain >
#   ▄▄██████▄▄    / _` | | | | __/ _ \          
#  ████████████  | (_| | |_| | || (_) |        -- Root: wrapper.py <─────────┐
# ████▀▀██▀▀████  \__,_|\__,_|\__\___/                   ┆      ┆            │
# ████▄▄▀▀▄▄████   _ __ ___   ___ ___            (bg thread)  (fg thread)    │
# █████    █████  | '_ ` _ \ / __/ __|                ┆            ┆         ├── constants.py
#  ████▄██▄████   | | | | | | (__\__ \          crash-handler    main.py <───┤
#   ▀▀██████▀▀    |_| |_| |_|\___|___/                             ┆         │
#                                                                menu.py <───┘
#
#   < Functional Tests >
#   
#   - Windows 10 1909, 20H2, 21H2
#   - Windows 11 22H2
#   - macOS Monterey (Intel, 12.7.3)
#   - Manjaro KDE 2022 - 5.10, 5.16, 6.1, 6.3
#   - Manjaro XFCE 2022 - 5.15.8  //No file dialog, requires installation of Zenity
#   - Arch Linux (KDE) - 6.6.9
#   - Kali Linux 2022 - 5.15
#   - Ubuntu 23.10 Desktop (Wayland) - 6.5
#   - Ubuntu 22.04 Server (XFCE, LXDE) - 5.15
#   - Ubuntu 22.04.1 Desktop (Wayland, X11) - 5.15
#   - Fedora 33 Workstation - 5.8
#   - PopOS 22.04 - 5.19
#   - Linux Mint 21 MATE - 5.15
#   - Garuda KDE Lite - 5.19.7
#   - Garuda Wayfire - 5.19.7  //Issues with YAD not displaying file dialog
#   - Garuda i3 - 5.19.7       //Issues with YAD not displaying file dialog
#   - SteamOS Holo - 5.13
#
# ----------------------------------------------------------------------------------------------
