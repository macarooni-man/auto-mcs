from source.ui.headless.utility import *


# --------------------------------------------- Custom Command Behavior ------------------------------------------------

class Command:

    def exec(self, args=()):

        # Combine all arguments into one if one_arg
        if self.one_arg:
            args = ' '.join(args).strip()

        # If args is longer than self.params, concatenate the last args
        else:
            if len(args) > len(self.params):
                args = list(args[:len(self.params) - 1]) + [' '.join(args[len(self.params) - 1:])]
                args = tuple(args)


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
        if isinstance(cmd, (list, tuple)):
            root = cmd[0].strip()
            args = cmd[1:]

            # Dirty fix to failure parsing args
            if ' ' in root and not args:
                new_root = root.split(' ')
                root = new_root[0]
                args = new_root[1:]
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



# ----------------------------------------------- Command Definitions --------------------------------------------------

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
            'launch': {
                'help': 'launches a server by name',
                'one-arg': True,
                'params': {'server name': lambda name: manage_server(name, 'launch')}
            },
            'stop': {
                'help': 'stops a server by name',
                'one-arg': True,
                'params': {'server name': lambda name: manage_server(name, 'stop')}
            },
            'kill': {
                'help': 'terminates a server by name',
                'one-arg': True,
                'params': {'server name': lambda name: manage_server(name, 'kill')}
            },
            'restart': {
                'help': 'restarts a server by name',
                'one-arg': True,
                'params': {'server name': lambda name: manage_server(name, 'restart')}
            },
            'list': {
                'help': 'lists installed server names (* - active)',
                'exec': list_servers
            },
            'info': {
                'help': 'displays basic information about a server',
                'one-arg': True,
                'params': {'server name': lambda name: manage_server(name, 'info')}
            },
            'properties': {
                'help': "edit the 'server.properties' file",
                'one-arg': True,
                'params': {'server name': lambda name: edit_properties(name)}
            },
            'create': {
                'help': 'creates a server on a specified type/version',
                'params': {
                    'type:version': lambda data: init_create_server(data),
                    'server name': lambda data: init_create_server(data)
                }
            },
            'import': {
                'help': 'imports an existing server from a folder or auto-mcs back-up',
                'params': {
                    'path': lambda path: init_import_server(path)
                }
            },
            'delete': {
                'help': 'deletes a server by name',
                'one-arg': True,
                'params': {'server name': lambda name: manage_server(name, 'delete')}
            },
        }
    },
    'console': {
        'help': 'views a server console by name',
        'one-arg': True,
        'params': {'server name': lambda name: open_console(name)}
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
            'restrict': {
                'help': 'toggle access restriction from a user by ID',
                'one-arg': True,
                'params': {'#ID': lambda user_id: telepath_restrict(user_id)}
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
    'java': {
        'help': 'list and configure the Java runtime',
        'sub-commands': {
            'list': {
                'help': 'displays available runtime vendors, and versions',
                'exec': lambda: manage_java('list'),
            },
            'vendor': {
                'help': 'configure the default runtime vendor (will install automatically)',
                'one-arg': True,
                'params': {'vendor ID': lambda vendor_id: manage_java('vendor', vendor_id)}
            },
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
    'version': {
        'help': f'display {constants.app_title} build information',
        'exec': lambda *_: constants.format_version()
    }
}

# Only allow updates if the app is on the official release channel
if constants.is_official:
    command_data['update'] = {
        'help': f'view changelog and update {constants.app_title}',
        'sub-commands': {
            'info': {
                'help': 'show the changelog of a pending update',
                'exec': lambda *_: update_app(info=True)
            },
        }
    }

    if not constants.is_docker:
        command_data['update']['sub-commands']['install'] = {
            'help': 'install a pending update and restart',
            'exec': lambda *_: update_app()
        }

commands = {n: Command(n, d) if isinstance(d, dict) else d for n, d in command_data.items()}
