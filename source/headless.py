from datetime import datetime as dt
import threading
import functools
import urwid
import time
import sys
import re
import os

import constants
import telepath
import amscript
import acl

import warnings
warnings.filterwarnings('ignore')
constants.script_obj = amscript.ScriptObject()


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

    # Create a new server
    if action == 'create':

        # Ignore if offline
        if not constants.app_online:
            return [("info", "Server creation requires an internet connection")], 'fail'

        # Ignore if disk is full
        if not constants.check_free_space():
            return [("info", "There isn't enough disk space to create a server")], 'fail'

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
        constants.new_server_info['name'] = name
        constants.new_server_info['acl_object'] = acl.AclManager(name)

        # Run things and stuff
        verb = 'Validating' if os.path.exists(constants.javaDir) else 'Installing'
        update_console(f'(1/5) {verb} Java')
        constants.java_check()

        update_console(f"(2/5) Downloading 'server.jar'")
        constants.download_jar()

        update_console(f"(3/5) Installing {constants.new_server_info['type'].title().replace('forge','Forge')}")
        constants.install_server()

        update_console(f"(4/5) Applying server configuration")
        constants.generate_server_files()

        update_console(f"(5/5) Creating initial back-up")
        constants.create_backup()

        constants.generate_server_list()

        return [
            ("normal", "Successfully created "),
            ("parameter", name),
            ("info", f" ({constants.new_server_info['type'].replace('craft','').title()} {constants.new_server_info['version']})\n\n"),
            ("info", " - to modify this server, run "),
            ("command", "telepath "),
            ("sub_command", "pair "),
            ("info", "to connect from a remote instance of auto-mcs"),
            ("info", "\n\n - to launch this server, run "),
            ("command", "server "),
            ("sub_command", "launch "),
            ("parameter", name),
        ]


    # Create a new server
    elif action == 'import':

        # Ignore if disk is full
        if not constants.check_free_space():
            return [("info", "There isn't enough disk space to import this server")], 'fail'

        # Run things and stuff
        constants.pre_server_create()
        is_backup_file = ((constants.import_data['path'].endswith(".tgz") or constants.import_data['path'].endswith(".amb")) and os.path.isfile(constants.import_data['path']))

        try:
            verb = 'Validating' if os.path.exists(constants.javaDir) else 'Installing'
            update_console(f'(1/4) {verb} Java')
            constants.java_check()

            update_console(f"(2/4) Importing server")
            constants.scan_import(is_backup_file)

            update_console(f"(3/4) Validating configuration")
            constants.finalize_import()

            update_console(f"(4/4) Creating initial back-up")
            constants.create_backup(True)

            constants.generate_server_list()
        except:
            return f"Failed to import '{name}'", 'fail'

        return [
            ("normal", "Successfully imported "),
            ("parameter", name),
            ("info", f" ({constants.new_server_info['type'].replace('craft', '').title()} {constants.new_server_info['version']})\n\n"),
            ("info", " - to modify this server, run "),
            ("command", "telepath "),
            ("sub_command", "pair "),
            ("info", "to connect from a remote instance of auto-mcs"),
            ("info", "\n\n - to launch this server, run "),
            ("command", "server "),
            ("sub_command", "launch "),
            ("parameter", name),
        ]


    # Manage existing servers
    elif name.lower() in constants.server_list_lower:
        server_obj = constants.server_manager.open_server(name)

        if action == 'info':
            return_text = [
                ("normal", "Server info - "), ("parameter", name),
                ("normal", '\n\n\n' + server_obj.server_properties['motd']),
                ("stat", f'\n{server_obj.type.title()} {server_obj.version}' + (f' (b{server_obj.build})\n' if server_obj.build else '\n'))
            ]
            if server_obj.running:
                try:
                    return_text.append(("success", f"\n> {server_obj.run_data['network']['address']['ip']}:{server_obj.run_data['network']['address']['port']}"))
                except:
                    return_text.append(("success", f"\nRunning, waiting to bind port..."))
            else:
                return_text.append(("info", "\n < not running >"))

            return return_log(return_text)

        elif action == 'launch':
            if server_obj.running:
                return [
                    ('parameter', name), ('info', ' is already running. '),
                    ("info", "Run "),
                    ("command", "console "),
                    ("parameter", name),
                    ("info", " to re-attach to the console")
                ], 'fail'

            return open_console(name, force_start=True)

        elif action == 'stop':
            if not server_obj.running:
                return [('parameter', name), ('info', ' is not running')], 'fail'

            func_wrapper(server_obj.stop)
            return return_log([("normal", "Stopped "), ("parameter", name)])

        elif action == 'kill':
            if not server_obj.running:
                return [('parameter', name), ('info', ' is not running')], 'fail'

            func_wrapper(server_obj.kill)
            return return_log([("normal", "Terminated "), ("parameter", name)])

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


def init_create_server(data):

    # Invalid info
    if len(data) < 2:
        return 'Server name is required', 'fail'

    # Instant template
    elif data[0].startswith('instant'):
        if ':' in data[0]:
            try:
                name = data[1]
                file = data[0].split(':')[1] + '.yml'
                template = constants.ist_data[file]
                constants.apply_template(template)

                return manage_server(name, 'create')

            except KeyError:
                pass

        return 'Invalid instant template specified', 'fail'

    # Manual version
    else:
        constants.new_server_init()
        constants.new_server_info['type'] = 'vanilla'
        name = data[1]
        data = data[0].replace('bukkit','craftbukkit').replace('builds','').lower()

        # Check if only a version was specified
        if data.replace('.', '').isdigit() or data == 'latest':
            constants.new_server_info['version'] = data

        # Check if only a type was specified
        elif ':' not in data:
            constants.new_server_info['type'] = data

        # Check if both a type and version was specified
        else:
            constants.new_server_info['type'], constants.new_server_info['version'] = data.split(':', 1)


        # Fail if type is invalid
        if constants.new_server_info['type'] not in list(constants.latestMC.keys()):
            return [('fail', constants.new_server_info['type']), ('info', ' is not a supported server type')], 'fail'

        # Set to latest version if specified
        if constants.new_server_info['version'] == 'latest':
            constants.new_server_info['version'] = constants.latestMC[constants.new_server_info['type']]

        # Check if version is valid
        version_data = constants.search_version(constants.new_server_info)
        if not version_data[0]:
            return [('fail', constants.new_server_info['version']), ('info', f' is not a supported {constants.new_server_info["type"].replace("craft","").title()} version')], 'fail'

        constants.new_server_info['version'] = version_data[1]['version']
        constants.new_server_info['build'] = version_data[1]['build']
        constants.new_server_info['jar_link'] = version_data[3]

        return manage_server(name, 'create')

def init_import_server(path):

    # Input validation
    if isinstance(path, tuple):
        path = ''.join(path).replace('\\ ', ' ')

    # If the path is a server directory
    if os.path.isdir(path):
        selected_server = os.path.abspath(path)

        # Check if the selected server is invalid
        if not (os.path.isfile(os.path.join(selected_server, 'server.properties'))):
            return 'Invalid server', 'fail'

        # Don't allow import of already imported servers
        elif os.path.join(constants.applicationFolder, 'Servers') in selected_server and os.path.basename(selected_server).lower() in constants.server_list_lower:
            return 'This server already exists', 'fail'

        # If server is valid, do this
        else:
            constants.import_data = {
                'name': re.sub('[^a-zA-Z0-9 _().-]', '', os.path.basename(selected_server).splitlines()[0])[:25],
                'path': selected_server
            }

    # If the path is an auto-mcs back-up
    elif os.path.isfile(path) and (path.endswith('.amb') or path.endswith(".tgz")):
        selected_server = os.path.abspath(path)

        # Extract auto-mcs.ini and server.properties
        file_failure = True
        server_name = None
        new_path = None
        test_path = constants.tempDir
        cwd = constants.get_cwd()

        constants.folder_check(test_path)
        os.chdir(test_path)
        constants.run_proc(f'tar -xf "{selected_server}" auto-mcs.ini')
        constants.run_proc(f'tar -xf "{selected_server}" .auto-mcs.ini')
        constants.run_proc(f'tar -xf "{selected_server}" server.properties')
        if (os.path.exists(os.path.join(test_path, "auto-mcs.ini")) or os.path.exists(os.path.join(test_path, ".auto-mcs.ini"))) and os.path.exists(os.path.join(test_path, "server.properties")):
            if os.path.exists(os.path.join(test_path, "auto-mcs.ini")):
                new_path = os.path.join(test_path, "auto-mcs.ini")
            elif os.path.exists(os.path.join(test_path, ".auto-mcs.ini")):
                new_path = os.path.join(test_path, ".auto-mcs.ini")
            if new_path:
                try:
                    config_file = constants.server_config(server_name=None, config_path=new_path)
                    server_name = config_file.get('general', 'serverName')
                    constants.new_server_info['type'] = config_file.get('general', 'serverType')
                    constants.new_server_info['version'] = config_file.get('general', 'serverVersion')
                except:
                    pass
                file_failure = False

        os.chdir(cwd)
        constants.safe_delete(test_path)

        # Check if the selected server is invalid
        if file_failure:
            return 'Invalid back-up', 'fail'


        # Don't allow import of already imported servers
        elif server_name.lower() in constants.server_list_lower:
            return 'This server already exists', 'fail'

        # If server is valid, do this
        else:
            constants.import_data = {
                'name': re.sub('[^a-zA-Z0-9 _().-]', '', server_name.splitlines()[0])[:25],
                'path': selected_server
            }

    else:
        return 'Invalid server, or back-up', 'fail'

    # Valid server/back-up file
    return manage_server(constants.import_data['name'], 'import')

def list_servers():
    constants.generate_server_list()
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
            time.sleep(0.1)
        time.sleep(0.1)

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

    user = constants.api_manager.current_users[data['host']['ip']]
    host = user["host"] if user["host"] else "Unknown"
    if user:
        final_text = [('normal', 'Successfully paired with '), ('telepath_host', f'{host}/{user["user"]} '), ('help', f'({user["ip"]})')]

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

        # Generate list of online users
        online_list = []
        for user in constants.api_manager.current_users.values():
            user_str = f'{user["host"]}/{user["user"]}'
            if user_str not in online_list:
                online_list.append(user_str)

        # Sort users based on if they are online
        results = sorted(
            constants.api_manager.authenticated_sessions,
            key = lambda u: f'{u["host"]}/{u["user"]}' in online_list,
            reverse = True
        )

        for x, user in enumerate(results):
            host = user["host"] if user["host"] else user["ip"]
            user_content = [('sub_command', f'ID #{constants.api_manager.authenticated_sessions.index(user)+1}   '), ('parameter', f'{host}/{user["user"]}')]

            # Check if user is online
            if constants.api_manager.current_users and f'{user["host"]}/{user["user"]}' in online_list:
                user_content.append(('command', ' (logged in)'))

            # Check if user is restricted
            elif 'disabled' in user and user["disabled"]:
                user_content.append(('fail', ' (restricted)'))

            if x+1 < len(constants.api_manager.authenticated_sessions):
                user_content.append(('info', '\n\n'))

            content.extend(user_content)

        return content

def telepath_restrict(user_id=None):

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
        host = user["host"] if user["host"] else user["ip"]
        disabled = 'disabled' in user and user["disabled"]
        constants.api_manager._disable_user(user['id'], not disabled)

        if user['ip'] not in constants.api_manager.current_users:
            verb = 'Unrestricted' if disabled else 'Restricted'
            return [('normal', f'{verb} Telepath access from '), ('sub_command', f'ID #{user_id+1} '), ('parameter', f'{host}/{user["user"]}')]

        else:
            return [('info', 'Something went wrong, please try again')], 'fail'


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
        host = user["host"] if user["host"] else user["ip"]

        # Force logout if they are logged in
        for session in constants.api_manager.current_users.values():
            if user['user'] == session['user'] and user['host'] == session['host']:
                constants.api_manager._force_logout(session['session_id'])
                break

        # Revoke from authenticated sessions
        constants.api_manager._revoke_session(user['id'])

        if user not in constants.api_manager.authenticated_sessions:
            return [('normal', 'Revoked Telepath access from '), ('sub_command', f'ID #{user_id+1} '), ('parameter', f'{host}/{user["user"]}')]

        else:
            return [('info', 'Something went wrong, please try again')], 'fail'


# Update app to the latest version
def update_app(info=False):

    # Display update info
    if info:
        if not constants.is_docker:
            return [
                ("sub_command", f"(!) Update - v{constants.update_data['version']}\n\n"),
                ("info", constants.update_data['desc'].replace('\r','')),
                ("success", response_header),
                ("normal", "To update to this version, run "),
                ("command", "update "),
                ("sub_command", "install ")
            ]
        else:
            return [
                ("sub_command", f"(!) Update - v{constants.update_data['version']}\n\n"),
                ("info", constants.update_data['desc'].replace('\r','')),
                ("success", response_header),
                ("normal", "Update to this version from Docker Hub")
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


class ScreenManager():
    def __init__(self):
        global loop
        self.placeholder = urwid.WidgetPlaceholder(urwid.Text(""))
        self.screens = {
            'MainMenuScreen': (main_menu, handle_input),
            'ServerPropertiesEditScreen': (None, None),
            'ServerViewScreen': (None, None)
        }

    def current_screen(self, screen_name: str):
        global loop
        self.placeholder.original_widget = self.screens[screen_name][0]
        loop.unhandled_input = self.screens[screen_name][1]




# -------------------------------------------------- Main Menu ---------------------------------------------------------

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
        }
    }
}
if not constants.is_docker:
    command_data['update']['sub-commands']['install'] = {
                'help': 'install a pending update and restart',
                'exec': lambda *_: update_app()
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
message_box = urwid.AttrMap(urwid.LineBox(console, title=title, title_attr=('normal' if constants.app_latest else 'parameter')), 'menu_line')

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

        # Insert version hints
        version_hints = [f'{t.replace("craft", "")}:latest' for t in constants.latestMC.keys() if t != 'builds']
        version_hints.insert(0, 'latest')

        # Insert instant template hints
        version_hints.extend([f"instant:{f[:-4]}" for f in constants.ist_data.keys()])


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

                        # Override "server name" parameter to display server names
                        elif command.name in input_text and list(command.params.items())[0][0] == 'server name':
                            partial_name = input_text.split(' ', 1)[-1].strip()
                            for server in constants.server_list:
                                if server.lower().startswith(partial_name.lower()):
                                    self.hint_text = f'{command.name} {server}'
                                    break

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
                                param_index = 0
                                args = ()


                                if len(sc.params) > 1:
                                    try:
                                        args = input_text.strip().split(' ', len(sc.params) + self.hint_params)[self.hint_params:]
                                    except:
                                        args = ()

                                    param_index = len(args)
                                    if param_index < 0:
                                        param_index = 0
                                    elif param_index > len(sc.params):
                                        param_index = len(sc.params)

                                    self._valid(True)

                                    if param_index >= len(sc.params):
                                        break

                                if input_text.endswith(sc.name + ' ') or (len(args) > 0 and input_text.endswith(' ')):
                                    self.hint_text = f'{input_text.strip()} <{list(sc.params.keys())[param_index]}>'

                                # Override "server name" parameter to display server names
                                elif sc.name in input_text and list(sc.params.items())[0][0] == 'server name':
                                    command_start = ' '.join(input_text.split(' ', 2)[:2])
                                    partial_name = input_text.split(' ', 2)[-1].strip()
                                    if command_start != 'server create':
                                        for server in constants.server_list:
                                            if server.lower().startswith(partial_name.lower()):
                                                self.hint_text = f'{command_start} {server}'
                                                break

                                # Override "type:version" parameter to display latest versions
                                elif sc.name in input_text and list(sc.params.items())[0][0] == 'type:version':
                                    command_start = ' '.join(input_text.split(' ', 2)[:2])
                                    partial_name = input_text.split(' ', 2)[-1].strip()
                                    for version in version_hints:
                                        if version.startswith(partial_name):
                                            self.hint_text = f'{command_start} {version} '
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

                if commands[command.strip()].sub_commands:

                    # Get index of param in command to check for special types
                    params = []
                    try:
                        params = commands[command.strip()].sub_commands[sub_command.strip()].params
                        args = param.split()
                        if len(args) > len(params):
                            args = list(args[:len(params) - 1]) + [' '.join(args[len(params) - 1:])]
                            args = tuple(args)
                    except:
                        args = ()


                    # Color different parameters differently
                    for x, arg in enumerate(args, 0):
                        found_type = False
                        try:
                            arg = re.findall(fr'{arg}\s*', param)[0]
                        except:
                            pass

                        # If the param patches the path of a matching data type
                        if params and args:
                            param_type = list(params.keys())[x]
                            if ':' in param_type:
                                found_type = True

                                if ':' in arg and not arg.endswith(':'):
                                    type_a, type_b = arg.split(':', 1)
                                    input_text.extend([
                                        ('type_a', type_a),
                                        ('hint', ':'),
                                        ('type_b', type_b)
                                    ])

                                elif ':' in arg:
                                    input_text.extend([
                                        ('type_a', arg.strip(':')),
                                        ('hint', ':')
                                    ])


                                else:
                                    s = arg.strip().lower()
                                    color = 'type_b' if s.replace('.', '').isdigit() or s == 'latest' else 'type_a'
                                    input_text.append((color, arg))


                        # Get index of parameter in question
                        if not found_type:
                            input_text.append(('parameter', arg))

                else:
                    input_text.append(('parameter', param))

        else:
            input_text = ('input', input_text)

        # Reformat original text for proper spacing
        if isinstance(input_text, list):
            final_space = ''
            if original_text.endswith(' '):
                final_space = (len(original_text) - len(original_text.rstrip())) * ' '
            original_text = re.sub(r'\s*\:\s*', ':', ' '.join([s[1].strip() for s in input_text])) + final_space

        hint_text = self._get_hint_text(original_text)
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
        if key == ' ' and self.get_edit_text().endswith(' '):
            return


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
                            self.set_edit_text(self.text + (' ' if not self.get_edit_text().endswith(' ') else ''))
                            self.set_edit_pos(len(self.get_edit_text()))
                            return None

                # Don't autofill params
                if '<' in self.hint_text and '>' in self.hint_text and ' ' in self.edit_text:
                    return None

                # Don't autofill one command params
                elif ('<' in self.hint_text and '>' in self.hint_text) or (self.hint_text in commands and commands[self.hint_text].params):
                    self.set_edit_text(self.hint_text.split(' ', 1)[0] + ' ')
                    self.set_edit_pos(len(self.get_edit_text()))
                    return None

                # Only autofill half of hybrid params
                if ':' in self.hint_text and ':' not in self.get_edit_text().rsplit(' ',1)[-1]:
                    self.hint_text = self.hint_text.rsplit(':')[0] + ':'

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
top_widget = urwid.Padding(pile)
main_menu = urwid.Frame(top_widget)

# Define the color palette
palette = [

    # Main menu palette
    ('caption_space', 'white', 'dark gray' if advanced_term else ''),
    ('caption_marker', 'dark gray', ''),
    ('input', 'light green', '', '', '#05e665', ''),
    ('hint', 'dark gray', ''),
    ('menu_line', 'white', '', '', '#444444', ''),
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
    ('parameter', 'yellow', '', '', '#F3ED61', ''),
    ('type_a', 'light magenta', '', '', '#FF00AA', ''),
    ('type_b', 'light cyan', ''),



    # ConsolePanel palette
    ('title', 'white', 'dark gray'),
    ('box_title', 'white', ''),
    ('stat', 'light gray', ''),
    ('input_header', 'light gray', ''),
    ('input', 'white', ''),
    ('linebox', 'dark gray', ''),
    ('bar_inactive', 'dark gray', '', '', 'h233', ''),
    ('bar_label', 'dark gray', '', '', 'h240', ''),
    ('ip', 'light green', ''),

    # Performance panel colors
    ('perf_normal', 'light green', '', '', '#22FF66', ''),
    ('perf_warn', 'yellow', ''),
    ('perf_critical', 'light red', '', '', '#FF3333', ''),

    # Event colors
    ('console_gray', 'light gray', ''),
    ('console_gray_bg', 'black', 'light gray'),
    ('console_purple', 'dark blue', '', '', '#6666FF', ''),
    ('console_purple_bg', 'black', 'dark blue', '', 'black', '#6666FF'),
    ('console_green', 'light green', '', '', '#22FF66', ''),
    ('console_green_bg', 'black', 'light green', '', 'black', '#22FF66'),
    ('console_blue', 'light cyan', ''),
    ('console_blue_bg', 'black', 'light cyan'),
    ('console_pink', 'light magenta', '', '', '#FF00AA', ''),
    ('console_pink_bg', 'black', 'light magenta', '', 'black', '#FF00AA'),
    ('console_red', 'light red', '', '', '#FF3333', ''),
    ('console_red_bg', 'black', 'light red', '', 'black', '#FF3333'),
    ('console_orange', 'yellow', '', '', '#FF9525', ''),
    ('console_orange_bg', 'yellow', '', '', 'black', '#FF9525'),
    ('console_yellow', 'yellow', ''),
    ('console_yellow_bg', 'black', 'yellow'),



    # 'server.properties' palette
    ('key', 'dark blue', '', '', '#4455FF', ''),
    ('comment',  'dark gray', '', '', '#636363', ''),
    ('line', 'dark gray', '', '', 'h239', ''),
    ('eq', 'dark gray', ''),
    ('selected_line', 'white', '', '', '#B2B2FF', ''),
    ('selected_eq', 'white', ''),
    ('search_highlight', 'black', 'light green', '', 'black', '#4DFF99'),
    ('search_bar', 'white', 'dark gray', '', 'white', '#333333'),

    ('boolean', 'light magenta', '', '', '#DD53DD', ''),
    ('integer', 'yellow', '', '', '#FF9525', ''),
    ('string', 'light cyan', '', '', '#68E3FF', ''),
    ('scrollbar_thumb', 'light gray', '')
]
def get_color(key):
    for c in palette:
        if key == c[0]:
            return c

screen_manager = ScreenManager()
screen = urwid.raw_display.Screen()
screen.set_terminal_properties(colors=256)
screen.register_palette(palette)
loop = urwid.MainLoop(screen_manager.placeholder, unhandled_input=handle_input, screen=screen)



# ------------------------------------------- 'server.properties' Editor -----------------------------------------------

class PropertiesEditor():

    # Custom ListBox to handle focus movement and wrapping
    class SearchListBox(urwid.ListBox):
        def __init__(self, body, editor):
            super().__init__(body)
            self.editor = editor

        def keypress(self, size, key):
            if key in ('up', 'down'):
                if self.editor.search_mode:
                    self.editor.handle_search_navigation(key)
                    return None  # Consume the key event
                else:
                    self.editor.handle_navigation(key)
                    return None  # Consume the key event
            return super().keypress(size, key)

        def mouse_event(self, size, event, button, col, row, focus):
            if event == 'mouse press' and button in (4, 5):  # Scroll up/down
                key = 'up' if button == 4 else 'down'
                if self.editor.search_mode:
                    self.editor.handle_search_navigation(key)
                    return True  # Consume the event
                else:
                    self.editor.handle_navigation(key)
                    return True  # Consume the event
            return super().mouse_event(size, event, button, col, row, focus)

    class Scrollbar(urwid.WidgetWrap):
        def __init__(self, listbox):
            self.listbox = listbox  # This is the ListBox
            self.scrollbar = urwid.WidgetPlaceholder(urwid.SolidFill(' '))  # Placeholder for the scrollbar
            self.thumb_char = '▐'
            # Combine the ListBox and the scrollbar
            self.widget = urwid.Columns([
                ('weight', 1, self.listbox),
                ('fixed', 1, self.scrollbar)
            ], focus_column=0)
            super().__init__(self.widget)

        def render(self, size, focus=False):
            # size is a tuple (maxcol, maxrow)
            maxcol, maxrow = size
            # Update the scrollbar with the current size
            self._update_scrollbar(size)
            # Render the widget
            return self.widget.render(size, focus=focus)

        def _update_scrollbar(self, size):
            maxcol, maxrow = size
            listbox = self.listbox

            total_lines = len(listbox.body)
            if total_lines == 0:
                thumb_size = maxrow
                thumb_position = 0
            else:
                # Calculate the visible portion
                focus_position = listbox.body.focus
                if focus_position is None:
                    focus_position = 0

                # Estimate the number of lines per screen
                lines_per_screen = maxrow
                thumb_size = max(1, round(int(lines_per_screen * maxrow / total_lines) / 2))
                thumb_position = int(
                    focus_position * (maxrow - thumb_size) / (max(1, total_lines - lines_per_screen) * 1.8))

                # Clamp thumb_position to ensure it stays within the scrollbar
                thumb_position = max(0, min(thumb_position, maxrow - thumb_size))

            # Create the scrollbar thumb using the "▐" character
            scrollbar_thumb = urwid.AttrMap(urwid.SolidFill(self.thumb_char), 'scrollbar_thumb')

            # Create spaces above and below the thumb
            scrollbar_top = urwid.SolidFill(' ')
            scrollbar_bottom = urwid.SolidFill(' ')

            # Build the scrollbar pile
            scrollbar_pile = urwid.Pile([
                ('fixed', thumb_position, scrollbar_top),
                ('fixed', thumb_size, scrollbar_thumb),
                ('weight', 1, scrollbar_bottom)
            ])

            self.scrollbar.original_widget = scrollbar_pile

        def keypress(self, size, key):
            return self.widget.keypress(size, key)

        def mouse_event(self, size, event, button, col, row, focus):
            return self.widget.mouse_event(size, event, button, col, row, focus)

    def __init__(self, server_name: str):
        self.server_name = server_name
        self.file_path = constants.server_path(server_name, 'server.properties')
        self.properties = self.load_properties()
        self.search_mode = False
        self.search_term = ""
        self.search_results = []
        self.focused_result = 0
        self.previous_focus = None
        self.current_index = 0

        self.widget_info = []  # Store references to widgets
        self.loop = None  # Will be set later

        self.list_walker = urwid.SimpleFocusListWalker(self.build_ui())
        self.listbox = self.SearchListBox(self.list_walker, self)
        self.search_edit = urwid.Edit(('search_bar', "Search: "))
        self.matches_display = urwid.Text("", align='right')
        search_columns = urwid.Columns([
            ('weight', 1, self.search_edit),
            ('pack', self.matches_display)
        ], dividechars=1)
        self.search_widget = urwid.AttrMap(search_columns, 'search_bar')

        # Help text to be displayed when search bar is hidden
        self.help_text = urwid.Text(('search_bar', " ESC - save & quit, CTRL+F - search "), align='center')

        # Wrap the ListBox with the Scrollbar
        self.scrollbar = self.Scrollbar(self.listbox)

        # Initially show the help text at the footer
        self.main_widget = urwid.Frame(
            body=self.scrollbar,
            footer=self.help_text  # Show help text by default
        )

    def connect_signals(self):
        urwid.connect_signal(self.list_walker, 'modified', self.render_focus)
        urwid.connect_signal(self.search_edit, 'change', self.on_search_edit_change)

    # Load server.properties file
    def load_properties(self):
        properties = []

        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as f:
                content = f.read()
                if content.strip():

                    for line in content.splitlines():

                        if line.startswith("#"):
                            properties.append(('comment', line.strip().replace('# ', '#'), None))

                        elif '=' in line:
                            key, value = line.strip().split('=', 1)
                            properties.append(('entry', key, value))

                        else:
                            properties.append(('raw', line.strip(), None))

        if not properties:
            constants.fix_empty_properties(self.server_name)
            return self.load_properties()

        return properties

    # Save properties back to the file
    def save_properties(self):
        final_text = []
        for i, widget in enumerate(self.list_walker):

            # Skip divider lines
            if isinstance(widget, urwid.Divider):
                continue

            # Normal line
            if isinstance(widget, urwid.Columns) and len(widget.contents) >= 4:
                key_widget = widget.contents[1][0]
                key = urwid.Text.get_text(key_widget)[0]
                value_placeholder = widget.contents[3][0]
                value_widget = value_placeholder.original_widget

                if isinstance(value_widget, urwid.AttrMap):
                    value_widget = value_widget.original_widget

                if isinstance(value_widget, urwid.Edit):
                    value = value_widget.get_edit_text()
                elif isinstance(value_widget, urwid.Text):
                    value = ''.join([t for attr, t in value_widget.text])
                else:
                    value = ''

                final_text.append(f'{key}={value}\n')

            # Comment
            elif isinstance(widget, urwid.Columns):
                comment = widget.contents[1][0].get_text()[0]
                final_text.append(f'{comment.replace("# ", "#")}\n')

        if final_text:
            with open(self.file_path, 'w') as f:
                f.writelines(final_text)

    def build_ui(self):
        widgets = []
        self.editable_indices = []  # Indices of editable lines
        for i, (entry_type, key, value) in enumerate(self.properties):

            # Comments
            if entry_type == 'comment':
                line_number_widget = urwid.Text(('line', f"{i + 1:3} "), align='right')
                comment_widget = urwid.Text(('comment', key.replace('#', '# ')))
                line_widget = urwid.Columns([
                    ('fixed', 4, line_number_widget),
                    comment_widget
                ], dividechars=1)
                widgets.append(line_widget)
                widgets.append(urwid.Divider())

            # Key and Value entries
            elif entry_type == 'entry':
                line_number_widget = urwid.Text(('line_number', f"{i + 1:3} "), align='right')
                key_widget = urwid.Text(('key', key))
                equal_sign_widget = urwid.Text(('line', '= '))

                # Define the value widget
                value_widget = urwid.Edit('', value)
                value_wrapper = urwid.AttrMap(value_widget, self.value_type(value))
                value_wrapper.edit = value_widget
                urwid.connect_signal(value_widget, 'change', functools.partial(self.on_edit, value_wrapper))

                # Wrap the value widget in a WidgetPlaceholder
                value_placeholder = urwid.WidgetPlaceholder(value_wrapper)

                # Assemble the columns
                columns = urwid.Columns([
                    ('fixed', 4, line_number_widget),
                    ('fixed', 20, key_widget),
                    ('fixed', 2, equal_sign_widget),
                    ('weight', 1, value_placeholder)
                ], dividechars=1)

                # Store the index before appending the widget
                widget_index = len(widgets)

                widgets.append(columns)
                widgets.append(urwid.Divider())

                self.editable_indices.append(widget_index)

                # Store references for later use
                self.widget_info.append({
                    'index': widget_index,
                    'entry_type': entry_type,
                    'key': key,
                    'value': value,
                    'key_widget': key_widget,
                    'value_widget': value_widget,
                    'value_placeholder': value_placeholder,
                    'value_wrapper': value_wrapper,
                    'line_widget': columns
                })

            else:
                widgets.append(urwid.Text(key))
                widgets.append(urwid.Divider())

        return widgets

    def toggle_search(self):
        if self.search_mode:
            self.search_mode = False
            self.main_widget.footer = self.help_text  # Show the help text again
            self.reset_highlighting()
            self.matches_display.set_text("")

            # Restore focus and explicitly set the cursor position after a short delay
            self.loop.set_alarm_in(0.01, self.restore_focus_and_cursor)
        else:
            self.search_mode = True
            self.previous_focus = self.listbox.get_focus()[1]  # Save current focus
            self.main_widget.footer = self.search_widget  # Show the search bar
            self.main_widget.set_focus('footer')
            if self.search_term:
                self.perform_search()

    def restore_focus_and_cursor(self, loop=None, user_data=None):
        focus_widget, focus_position = self.listbox.get_focus()

        # Explicitly set focus to the current line
        if focus_widget:
            self.listbox.set_focus(focus_position)

            # Ensure the cursor is placed at the end of the Edit widget if applicable
            self.set_cursor_to_end()

            # Force a screen redraw to ensure the cursor is visible
            self.loop.draw_screen()

    def set_cursor_to_end(self):
        focus_widget, focus_position = self.listbox.get_focus()

        # Ensure that we are focusing on an editable line
        if focus_position is not None and isinstance(self.list_walker[focus_position], urwid.Columns):
            value_placeholder = self.list_walker[focus_position].contents[3][0]
            value_widget = value_placeholder.original_widget

            if isinstance(value_widget, urwid.AttrMap):
                value_widget = value_widget.original_widget

            if isinstance(value_widget, urwid.Edit):
                # Explicitly move cursor to the end of the line
                value_widget.set_edit_pos(len(value_widget.get_edit_text()))

    def reset_highlighting(self):
        for info in self.widget_info:
            if info['entry_type'] == 'entry':
                key = info['key']
                key_widget = info['key_widget']
                value_placeholder = info['value_placeholder']
                value_wrapper = info['value_wrapper']

                # Reset key_widget text
                key_widget.set_text(('key', key))

                # Reset value_placeholder to original value_wrapper if needed
                if value_placeholder.original_widget != value_wrapper:
                    value_placeholder.original_widget = value_wrapper

    def on_search_edit_change(self, edit, new_edit_text):
        self.search_term = new_edit_text
        self.loop.set_alarm_in(0, lambda *_: self.perform_search())

    def perform_search(self):
        self.search_results = []
        self.search_term = self.search_edit.get_edit_text()
        if not self.search_term:
            self.reset_highlighting()
            self.matches_display.set_text("")
            return

        for info in self.widget_info:
            if info['entry_type'] == 'entry':
                key = info['key']
                value_widget = info['value_widget']
                value = value_widget.get_edit_text()
                key_widget = info['key_widget']
                value_placeholder = info['value_placeholder']
                value_wrapper = info['value_wrapper']

                # Reset key_widget text
                key_widget.set_text(('key', key))

                # Reset value_placeholder to original value_wrapper if needed
                if value_placeholder.original_widget != value_wrapper:
                    value_placeholder.original_widget = value_wrapper

                # Now, check for matches
                key_matches = self.search_term.lower() in key.lower()
                value_matches = self.search_term.lower() in value.lower()

                # For key
                if key_matches:
                    highlighted_key = self.highlight_text(key, self.search_term, default_attr='key')
                    key_widget.set_text(highlighted_key)
                else:
                    key_widget.set_text(('key', key))

                # For value
                if value_matches:
                    # Determine the value_type attribute
                    value_type_attr = self.value_type(value)
                    highlighted_value = self.highlight_text(value, self.search_term, default_attr=value_type_attr)
                    highlighted_value_widget = urwid.Text(highlighted_value)
                    value_placeholder.original_widget = highlighted_value_widget
                else:
                    # Restore the value_placeholder to the Edit widget if it was replaced
                    if value_placeholder.original_widget != value_wrapper:
                        value_placeholder.original_widget = value_wrapper

                # Add to search results if either key or value matches
                if key_matches or value_matches:
                    self.search_results.append(info['index'])

        if self.search_results:
            self.focused_result = 0
            self.focus_search_result(self.focused_result)
        else:
            # No results, update matches display
            self.matches_display.set_text("No Results")

    def highlight_text(self, text, term, default_attr=None):
        # Split the text into parts where the term occurs (case-insensitive)
        regex = re.compile('(' + re.escape(term) + ')', re.IGNORECASE)
        parts = regex.split(text)
        # Apply highlighting to the matched terms
        result = []
        for part in parts:
            if not part:
                continue  # Skip empty strings
            if regex.fullmatch(part):
                result.append(('search_highlight', part))
            else:
                if default_attr:
                    result.append((default_attr, part))
                else:
                    result.append(part)
        return result

    def focus_search_result(self, index):
        if self.search_results:
            self.focused_result = index % len(self.search_results)
            self.loop.set_alarm_in(0, lambda *_: self.listbox.set_focus(self.search_results[self.focused_result]))
            # Update matches display
            self.matches_display.set_text(f"{self.focused_result + 1} / {len(self.search_results)} Results")
        else:
            self.matches_display.set_text("No Results")

    @staticmethod
    def return_to_menu():
        screen_manager.current_screen('MainMenuScreen')

    def handle_input(self, key):
        # Ignore mouse events
        if isinstance(key, tuple):
            return

        # Close search or save & quit
        if key == 'esc':
            if self.search_mode:
                self.toggle_search()
            else:
                self.save_properties()
                self.return_to_menu()

        # Quit without saving
        elif key in ['ctrl c', 'ctrl q']:
            self.return_to_menu()

        # Toggle search
        elif key == 'ctrl f':
            self.toggle_search()
        elif self.search_mode:
            if key == 'esc':
                self.toggle_search()
            elif key in ('up', 'down', 'page up', 'page down', 'n', 'p'):
                # Handle navigation keys in search mode
                self.handle_search_navigation(key)
            else:
                # Allow the search_edit widget to handle the key
                maxcol = self.loop.screen_size[0]
                self.search_edit.keypress((maxcol,), key)
        else:
            # Handle navigation keys
            if key in ('up', 'down', 'page up', 'page down'):
                self.handle_navigation(key)
            else:
                # Let the ListBox handle other keys
                self.listbox.keypress(self.loop.screen_size, key)

    def handle_navigation(self, key):
        if isinstance(key, tuple):
            return

        if key in ('up', 'down'):
            self.move_focus_to_next_editable_line(key)
        elif key == 'page up':
            # Move up several lines
            for _ in range(5):  # Adjust as needed
                self.move_focus_to_next_editable_line('up')
        elif key == 'page down':
            for _ in range(5):
                self.move_focus_to_next_editable_line('down')

    def move_focus_to_next_editable_line(self, direction):
        current_focus = self.listbox.get_focus()[1]
        if current_focus is None:
            # No focus, start from 0 or max_index depending on direction
            current_focus = 0 if direction == 'down' else len(self.list_walker) - 1

        index = current_focus
        max_index = len(self.list_walker) - 1

        while True:
            if direction == 'up':
                index -= 1
                if index < 0:
                    index = max_index  # Wrap around to bottom
            elif direction == 'down':
                index += 1
                if index > max_index:
                    index = 0  # Wrap around to top

            if index == current_focus:
                # We've looped all the way around
                return

            if index in self.editable_indices:
                self.listbox.set_focus(index)
                break

    def handle_search_navigation(self, key):
        if not self.search_results:
            return  # No matches to navigate

        if key in ('down', 'n', 'page down'):
            self.focus_search_result(self.focused_result + 1)
        elif key in ('up', 'p', 'page up'):
            self.focus_search_result(self.focused_result - 1)
        else:
            pass  # Ignore other keys

    def on_edit(self, edit_widget, widget, value):
        def change(*a):
            value_type = self.value_type(value)

            # Toggle boolean values
            if value.endswith(' ') and value_type == 'boolean':
                edit_widget.edit.set_edit_text('false' if value.strip() == 'true' else 'true')
            else:
                edit_widget.attr_map = {None: value_type}
        self.loop.set_alarm_in(0, change)

    @staticmethod
    def value_type(value):
        value_type = 'string'
        if value.strip().lower() in ['true', 'false']:
            value_type = 'boolean'
        elif value.strip().isdigit():
            value_type = 'integer'
        return value_type

    def set_cursor_to_end(self):
        focus_widget, focus_position = self.listbox.get_focus()
        if focus_position is None or focus_position >= len(self.list_walker):
            return
        # Use focus_position instead of self.current_index
        if isinstance(self.list_walker[focus_position], urwid.Columns) and len(self.list_walker[focus_position].contents) >= 4:
            value_placeholder = self.list_walker[focus_position].contents[3][0]
            value_widget = value_placeholder.original_widget
            if isinstance(value_widget, urwid.AttrMap):
                value_widget = value_widget.original_widget
            if isinstance(value_widget, urwid.Edit):
                self.loop.set_alarm_in(0, lambda *_: value_widget.set_edit_pos(len(value_widget.get_edit_text())))

    def render_line(self):
        for i, widget in enumerate(self.list_walker):
            if isinstance(widget, urwid.Columns):
                if len(widget.contents) > 2:
                    line_number_widget = widget.contents[0][0]
                    equal_sign_widget = widget.contents[2][0]

                    # Highlight the selected line number and '=' sign
                    if i == self.current_index:
                        line_number_widget.set_text(('selected_line', line_number_widget.get_text()[0]))
                        equal_sign_widget.set_text(('selected_eq', equal_sign_widget.get_text()[0]))
                    else:
                        line_number_widget.set_text(('line', line_number_widget.get_text()[0]))
                        equal_sign_widget.set_text(('eq', equal_sign_widget.get_text()[0]))

    def render_focus(self):
        if getattr(self, '_adjusting_focus', False):
            return

        focused_widget, focus_position = self.listbox.get_focus()

        # Loop through the list_walker to find the index of the focused widget
        for i, widget in enumerate(self.list_walker):
            if widget == focused_widget:
                # Update the current index
                self.current_index = i
                self.render_line()
                self.set_cursor_to_end()

                # If in search mode, ensure focus is on a matching line
                if self.search_mode:
                    if self.current_index in self.search_results:
                        # Update the focused_result index
                        self.focused_result = self.search_results.index(self.current_index)
                        self.matches_display.set_text(f"{self.focused_result + 1} / {len(self.search_results)} Results")
                    else:
                        # Adjust focus to the nearest matching line
                        self.adjust_focus_to_match(self.current_index)
                break

    def adjust_focus_to_match(self, index):
        if getattr(self, '_adjusting_focus', False):
            return
        self._adjusting_focus = True

        if not self.search_results:
            self._adjusting_focus = False
            return

        # Find the matching index closest to 'index'
        distances = [(abs(i - index), i) for i in self.search_results]
        distances.sort()
        _, closest_index = distances[0]

        if closest_index != index:
            def set_focus(*args):
                self.listbox.set_focus(closest_index)
                self._adjusting_focus = False  # Reset after focus change
            self.loop.set_alarm_in(0, set_focus)
        else:
            self._adjusting_focus = False  # No need to adjust focus

editor = None
def edit_properties(server_name: str):
    global loop, editor

    if server_name.lower() in constants.server_list_lower:
        editor = PropertiesEditor(server_name)
        editor.loop = loop
        editor.connect_signals()
        screen_manager.screens['ServerPropertiesEditScreen'] = (editor.main_widget, editor.handle_input)
        screen_manager.current_screen('ServerPropertiesEditScreen')
        return [("normal", "Successfully saved 'server.properties'")]

    # If server doesn't exist
    else:
        return [('parameter', server_name), ('info', ' does not exist')], 'fail'



# -------------------------------------------------- Console Panel -----------------------------------------------------

player_counter = 0
class ConsolePanel():

    class Panels():

        class PerformancePanel:
            def __init__(self, parent, label, percent):
                self.parent = parent
                self.bar_width = 20

                # Percentage bar
                bar_active_length = int((percent / 100) * self.bar_width)
                bar_inactive_length = self.bar_width - bar_active_length
                self.bar = urwid.Text([
                    ('bar_inactive', '▄' * bar_active_length),
                    ('bar_inactive', ' ' * bar_inactive_length),
                    ('bar_inactive', '\n'),
                    ('bar_inactive', '▀' * self.bar_width)
                ])
                bar_pile = urwid.Pile([self.bar])

                # Performance label
                self.label = urwid.Text(('bar_label', f"{percent}%"), align='right')
                progress_label = urwid.Text(('bar_label', f"{label}"), align='right')
                label_pile = urwid.Pile([self.label, progress_label])

                # Create columns with bar and labels
                self.widgets = urwid.Columns([
                    bar_pile,
                    ('fixed', 6, label_pile)
                ], dividechars=0)

            def set_percent(self, percent):
                color = self.parent.get_percent_color(percent, 5)
                fraction = (percent / 100) * self.bar_width
                full_steps = int(fraction)
                fractional = fraction - full_steps

                active_bars = ''
                bar_inactive_length = 0

                # If no full steps and percent > 0.5, display a half-step
                if full_steps == 0 and percent > 0.5:
                    active_bars = '▖'
                    bar_inactive_length = self.bar_width - 1

                # If fractional part > 0.5, add a half-step
                elif fractional > 0.5:
                    active_bars = '▄' * full_steps + '▖'
                    bar_inactive_length = self.bar_width - full_steps - 1

                # Otherwise, only full steps
                else:
                    active_bars = '▄' * full_steps
                    bar_inactive_length = self.bar_width - full_steps

                # Update the progress bar, and text
                self.bar.set_text([
                    (color, active_bars),
                    ('bar_inactive', ' ' * bar_inactive_length),
                    ('bar_inactive', '\n'),
                    ('bar_inactive', '▀' * self.bar_width)
                ])
                number = '0' if float(percent) == 0 else round(float(percent), 1)
                self.label.set_text((color, f"{number}%"))

        @staticmethod
        def get_percent_color(percent, min_limit=0):
            if percent <= min_limit:
                color = 'bar_label'
            elif percent < 50:
                color = 'perf_normal'
            elif percent < 75:
                color = 'perf_warn'
            else:
                color = 'perf_critical'

            return color

        def __init__(self, parent):
            self.parent = parent
            self.uptime = "00:00:00:00"
            self.player_count = "0 / 20"
            self.cpu_percent = 0
            self.ram_percent = 0

            # Stats panel
            self.stats = urwid.Text([
                ('stat', "up-time:\n"),
                ('bar_label', f"{self.uptime}\n\n"),
                ('stat', "players:\n"),
                ('bar_label', self.player_count)
            ], align='center')
            left_box = urwid.AttrMap(urwid.LineBox(urwid.Padding(self.stats, left=2, right=2)), 'linebox')

            # Center overview panel
            self.overview = urwid.Text([('bar_label', '\n\n< not running >\n\n')], align='center')
            middle_panel = urwid.Padding(self.overview, left=2, right=2)
            middle_box = urwid.AttrMap(
                urwid.LineBox(middle_panel, title=self.parent.server_name, title_attr='box_title'), 'linebox')
            middle_box_filled = urwid.Filler(middle_box, valign='top')

            # Performance panel
            self.cpu_panel = self.PerformancePanel(self, "CPU", self.cpu_percent)
            self.ram_panel = self.PerformancePanel(self, "RAM", self.ram_percent)

            right_panel = urwid.Pile([
                urwid.Padding(self.cpu_panel.widgets, left=2, right=2),
                urwid.Text(''),
                urwid.Padding(self.ram_panel.widgets, left=2, right=2)
            ])
            right_box = urwid.AttrMap(urwid.LineBox(urwid.Padding(right_panel, min_width=30)), 'linebox')

            # Compile the panels
            self.widgets = urwid.Columns([
                ('pack', urwid.Padding(left_box, left=1, right=1)),  # Left side: Uptime and Player Count
                ('weight', 1, urwid.Padding(middle_box_filled, left=1, right=1)),
                ('pack', urwid.Padding(right_box, left=1, right=1))  # Right side: CPU and RAM with 40% width
            ])

        def refresh_data(self, refresh_players=False, *a):
            server_obj = self.parent.server
            server_obj.performance_stats(0.005, update_players=refresh_players)

            try:
                perf_data = constants.server_manager.current_server.run_data['performance']
            except KeyError:
                return
            except AttributeError:
                return

            if not perf_data:
                return

            try:

                # Update up-time
                formatted_color = ''
                found = False
                for x, item in enumerate(perf_data['uptime'].split(":")):
                    if x == 0 and len(item) > 2:
                        formatted_color = f'{item}:'
                        found = True
                        continue
                    if x == 0 and item != '00':
                        item = int(item)
                        formatted_color += '|' if len(str(item)) >= 2 else '0|'
                        found = True
                    if item != "00" and not found:
                        found = True
                        item = int(item)
                        formatted_color += f'|{item}:' if len(str(item)) == 2 else f'0|{item}:'
                    else:
                        formatted_color += f'{item}:'

                formatted_color = formatted_color.strip(':')
                if '|' in formatted_color:
                    empty, full = formatted_color.split('|')
                else:
                    empty = ''
                    full = formatted_color

                # Update player count
                total_count = int(server_obj.server_properties['max-players'])
                count = len(perf_data['current-players'])
                percent = (count / total_count)
                color = self.get_percent_color(percent).replace('perf_normal', 'box_title')
                end_color = 'bar_label' if full == self.uptime else 'white'

                self.stats.set_text([
                    ('stat', "up-time:\n"),
                    ('bar_label', f"{empty}"), (end_color, f"{full}\n\n"),
                    ('stat', "players:\n"),
                    (color, str(count)), ('bar_label', ' / '), (color, str(total_count)),
                ])

                # Update server overview
                self.parent.ip_address = f"{server_obj.run_data['network']['address']['ip']}:{server_obj.run_data['network']['address']['port']}"
                self.overview.set_text([
                    ("white", f"\n{self.parent.motd}"),
                    ("stat", f"\n{self.parent.server_version}"),
                    ("ip", f"\n\n> {self.parent.ip_address}")
                ])

                # Update CPU/RAM stats
                self.cpu_panel.set_percent(perf_data['cpu'])
                self.ram_panel.set_percent(perf_data['ram'])

            except KeyError:
                return

    class Log():

        class ScrollBar(urwid.WidgetWrap):
            def __init__(self, parent, listbox):
                self.parent = parent
                self.listbox = listbox
                self.scrollbar = urwid.Text('')
                self.thumb_char = '▐'

                # Create a Columns widget with ListBox and ScrollBar
                columns = urwid.Columns([
                    ('weight', 1, listbox),
                    ('fixed', 2, self.scrollbar)
                ], dividechars=1)
                super().__init__(columns)

            def render(self, size, focus=False):

                # Calculate scrollbar based on size
                maxcol, maxrow = size
                total_items = len(self.listbox.body)
                if total_items <= 0:
                    bar = ' ' * maxrow
                else:

                    # Calculate thumb size, make it at least 2 rows and proportional to the content
                    thumb_size = max(2, int((maxrow / total_items) * maxrow * 0.6))
                    thumb_size = min(thumb_size, maxrow)

                    # Calculate thumb position based on focus
                    thumb_pos = int(
                        (self.listbox.focus_position / max(max(total_items - 1, 1), 1)) * (maxrow - thumb_size))
                    thumb_pos = max(0, min(thumb_pos, maxrow - thumb_size))
                    thumb_size = max(2, thumb_size)

                    # Build scrollbar lines
                    bar_lines = [' ' for _ in range(maxrow)]
                    for i in range(thumb_pos, thumb_pos + thumb_size):
                        if i < maxrow:
                            bar_lines[i] = self.thumb_char
                    bar = '\n'.join(bar_lines)

                    if bar.count(self.thumb_char) == maxrow:
                        bar = ' ' * maxrow

                self.scrollbar.set_text(('scrollbar_thumb', bar))
                return super().render(size, focus)

        @staticmethod
        def console_event(date, log_type, color, message):
            def get_log_color(c, background=False):
                new_color = 'console_purple'
                if c == (0.7, 0.7, 0.7, 1):
                    new_color = 'console_gray'
                elif c == (0.3, 1, 0.6, 1):
                    new_color = 'console_green'
                elif c == (1, 0.5, 0.65, 1):
                    new_color = 'console_red'
                elif c == (1, 0.804, 0.42, 1):
                    new_color = 'console_orange'
                elif c == (0.953, 0.929, 0.38, 1):
                    new_color = 'console_yellow'
                elif c == (0.439, 0.839, 1, 1):
                    new_color = 'console_blue'
                elif c == (1, 0.298, 0.6, 1):
                    new_color = 'console_pink'

                if background:
                    new_color += '_bg'

                return new_color

            # Make it fancy if the terminal supports it
            if advanced_term:
                line = urwid.Columns([
                    ('fixed', 13,
                     urwid.AttrMap(urwid.Text(f"{date} ", align='right'), get_log_color(color, True))),
                    ('fixed', 7, urwid.AttrMap(urwid.Text(log_type, align='center'), get_log_color(color, True))),
                    urwid.Text(f"{'█' if advanced_term else ''}  {message}\n", wrap='ellipsis')
                ])
                return urwid.AttrMap(line, get_log_color(color, False))

            # Basic view
            else:
                line = urwid.Columns([
                    ('fixed', 12, urwid.Text(f" {date}", align='right')),
                    ('fixed', 10, urwid.Text(log_type, align='center')),
                    urwid.Text(f"{message}\n", wrap='ellipsis')
                ])
                return urwid.AttrMap(line, get_log_color(color, False))

        def __init__(self, parent):
            self.parent = parent
            self.log = []

            self.data = urwid.SimpleFocusListWalker(self.log)
            list_box = urwid.ListBox(self.data)

            # Store a reference to list_box for scrolling
            self.list_box = list_box

            # Wrap the ListBox with ScrollBar
            self.scroll_bar = self.ScrollBar(self, list_box)

            # Wrap everything in a LineBox
            log_box = urwid.LineBox(self.scroll_bar)
            self.widget = urwid.AttrMap(urwid.Padding(log_box, left=1, right=1), 'linebox')  # Padding on the outside only

        def update_text(self, text, refresh=False, force_scroll=False):

            # Check if the scrollbar is at the bottom before adding new text
            at_bottom = False
            if force_scroll or (len(self.list_box.body) == 0 or self.list_box.focus_position == len(self.list_box.body) - 1):
                at_bottom = True


            # Update existing log
            if (len(text) == len(self.log)) and not refresh:
                last_entry = text[-1]['text']
                time_stamp, log_type, message, color = last_entry
                new_widget = self.console_event(time_stamp, log_type, color, message)
                self.log[-1] = new_widget
                self.data[-1] = new_widget

            # Add entries to the log
            else:
                if refresh:
                    self.log.clear()
                    self.data.clear()

                for line in text[len(self.log):]:
                    time_stamp, log_type, message, color = line["text"]
                    new_widget = self.console_event(time_stamp, log_type, color, message)
                    self.log.append(new_widget)
                    self.data.append(new_widget)


            # If it was at the bottom before, scroll to the bottom again
            if at_bottom:
                self.list_box.set_focus(len(self.list_box.body) - 1)

    class Input():

        class ValidatedEdit(urwid.Edit):
            def __init__(self, exec_func, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.command_history = []
                self.history_index = 0
                self.exec_func = exec_func
                self.hint_text = "enter command, or 'ESC' to detach..."

            def render(self, size, focus=False):
                if not self.get_edit_text():
                    # Display the hint text in dark gray when input is empty
                    hint = urwid.Text(('bar_label', self.hint_text))
                    return hint.render(size, focus)
                else:
                    # Display the regular input when there is text
                    return super().render(size, focus)

            def keypress(self, size, key):
                if not self.get_edit_text() and key == '/':
                    urwid.emit_signal(self, 'invalid_key', key)
                    return None

                elif key == 'enter':
                    command = self.get_edit_text().strip()

                    if command not in self.command_history[:1]:
                        self.command_history.insert(0, command)

                        # Limit size of command history
                        if len(self.command_history) > 100:
                            self.command_history.pop()

                    self.exec_func(command)

                    self.set_edit_text('')

                # Modulate command history with arrow keys
                elif key in ['up', 'down'] and self.command_history:

                    if key == 'down':
                        if self.history_index > 0:
                            self.history_index -= 1
                        else:
                            self.set_edit_text('')
                            return

                    # Constrain history_index to valid range
                    self.history_index = max(0, min(self.history_index, len(self.command_history) - 1))

                    # Set the command text based on the updated index
                    new_text = self.command_history[self.history_index]
                    self.set_edit_text(new_text)
                    self.set_edit_pos(len(new_text))

                    if key == 'up':
                        if self.history_index < len(self.command_history) - 1:
                            self.history_index += 1

                return super().keypress(size, key)

        def send_command(self, command):
            if self.parent.server.run_data:
                self.parent.server.run_data['send-command'](command)
                self.parent.log.update_text(self.parent.server.run_data['log'], force_scroll=True)

        def __init__(self, parent):
            self.parent = parent
            self.command_header = ' ❯❯  ' if advanced_term else ' >>  '
            prompt = urwid.Text(('input_header', self.command_header), align='left')
            edit = urwid.AttrMap(self.ValidatedEdit(self.send_command), 'input')

            self.widgets = urwid.Columns([('fixed', 5, prompt), edit])

    def __init__(self, server_name: str):
        # Initialize server
        self.is_visible = True

        self.server = constants.server_manager.open_server(server_name)
        while not all(list(self.server._check_object_init().values())):
            time.sleep(0.1)
        time.sleep(0.1)

        # Initialize IP address and server info for the middle box
        self.server_name = server_name
        self.motd = self.server.motd
        self.server_version = f'{self.server.type.title()} {self.server.version}'
        self.ip_address = '0.0.0.0:0'

        # Performance panel
        self.panels = self.Panels(self)

        # Log panel
        self.log = self.Log(self)

        # Create the input field
        self.input = self.Input(self)

        # Widget layout
        self.widgets = self.build_layout()

        # Launch the actual server
        self.launch_server()

    def handle_input(self, key):
        if key == 'esc':
            self.reset_panel(show_attach=True)

    def start_update_loop(self, *a):
        global player_counter, loop
        player_counter += 1

        loop.set_alarm_in(0, functools.partial(self.panels.refresh_data, player_counter == 3))
        if self.server.running and self.is_visible:
            loop.set_alarm_in(1, self.start_update_loop)

        if player_counter > 3:
            player_counter = 0

    def reset_panel(self, show_attach=False, *a):
        if self.server.restart_flag:
            return

        self.is_visible = False
        screen_manager.current_screen('MainMenuScreen')

        if not show_attach:
            update_console([('info', response_header), ('normal', "Type a command, ?, or "), ('command', 'help')])

    def launch_server(self):

        # Update log with initial message
        boot_text = f"Launching '{self.server_name}', please wait..."
        text_list = [{'text': (dt.now().strftime(constants.fmt_date("%#I:%M:%S %p")).rjust(11), 'INIT', boot_text, (0.7, 0.7, 0.7, 1))}]

        if self.server.proxy_enabled and self.server.proxy_installed() and not constants.playit.initialized:
            text_list.append({'text': (dt.now().strftime(constants.fmt_date("%#I:%M:%S %p")).rjust(11), 'INFO', 'Initializing playit agent...', (0.6, 0.6, 1, 1))})

        self.log.update_text(text_list)

        while not self.server.addon or not self.server.backup or not self.server.script_manager or not self.server.acl:
            time.sleep(0.05)


        # Launch the server
        self.server.launch()
        self.log.update_text(self.server.run_data['log'], refresh=True)


        # Map update functions to run_data hooks
        if self.log.update_text not in self.server.run_data.get('process-hooks', []):
            self.server.run_data.setdefault('process-hooks', []).append(self.log.update_text)

        if self.reset_panel not in self.server.run_data.get('close-hooks', []):
            self.server.run_data.setdefault('close-hooks', []).append(self.reset_panel)

        self.server.run_data['console-panel'] = self


        # Start timer to update performance stats
        self.start_update_loop()

    def open_panel(self):
        self.is_visible = True
        self.start_update_loop()
        return self

    def build_layout(self):
        title_text = urwid.Text(('title', f"auto-mcs v{constants.app_version} (headless)"), align='center')
        top_content = urwid.Pile([
            urwid.AttrMap(urwid.Filler(urwid.Padding(title_text, left=0, right=0), valign='top'), 'title'),
            urwid.AttrMap(urwid.Filler(urwid.Padding(urwid.Text(''), left=0, right=0), valign='top'), '')
        ])

        layout = urwid.Frame(
            self.log.widget,
            footer=self.input.widgets,
            header=urwid.Pile([top_content, self.panels.widgets]),
            focus_part='footer'
        )
        return layout

console = None
def open_console(server_name: str, force_start=False):
    global console, player_counter
    console = None
    if not force_start:

        # First, check if the server exists
        if server_name.lower() not in constants.server_list_lower:
            return [('parameter', server_name), ('info', ' does not exist')], 'fail'

        # Check if the server is running
        elif server_name not in constants.server_manager.running_servers:
            return [
                ("info", "Run "),
                ("command", "server "),
                ("sub_command", "launch "),
                ("parameter", server_name),
                ("info", " to start the server")
            ], 'fail'


    # Attempt to re-attach to the console if it's already available
    try:
        if server_name in constants.server_manager.running_servers:
            console = constants.server_manager.running_servers[server_name].run_data['console-panel'].open_panel()
    except:
        pass

    if not console:
        console = ConsolePanel(server_name)

    screen_manager.screens['ServerViewScreen'] = (console.widgets, console.handle_input)
    screen_manager.current_screen('ServerViewScreen')

    return [
        ("info", "Run "),
        ("command", "console "),
        ("parameter", server_name),
        ("info", " to re-attach to the console")
    ]



# --------------------------------------------------- Launch Menu ------------------------------------------------------

def run_application():
    # Give an error if elevated
    # Give an error if elevated
    if (constants.is_admin() and not constants.is_docker) and constants.bypass_admin_warning:
        print(f"\n\033[31m> Privilege Warning:  Running auto-mcs as {'administrator' if constants.os_name == 'windows' else 'root'} can expose your system to security vulnerabilities\n\nProceed with caution, this configuration is unsupported\033[0m\n\n< press 'ENTER' to continue >")
        null = input()

    elif (constants.is_admin() and not constants.is_docker) and not constants.bypass_admin_warning:
        print(f"\n\033[31m> Privilege Error:  Running auto-mcs as {'administrator' if constants.os_name == 'windows' else 'root'} can expose your system to security vulnerabilities\n\nPlease restart with standard user privileges to continue\033[0m")
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

            current_user = constants.api_manager.current_users[self.pair_data['host']['ip']]
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
        screen_manager.current_screen('MainMenuScreen')
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
