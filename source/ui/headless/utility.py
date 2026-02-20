from datetime import datetime as dt
from typing import TYPE_CHECKING
import traceback
import importlib
import functools
import inspect
import pkgutil
import urwid
import time
import sys
import re
import os

from source.core.server import foundry, acl, manager
from source.core.constants import paths, dTimer
from source.core import constants, telepath

from source.ui.headless.views.templates import *

if TYPE_CHECKING:
    from source.ui.headless.views.splash import MainMenuScreen


# -------------------------------------------- Global UI Variables -----------------------------------------------------

# Default headless UI settings
startup_screen:             str = 'MainMenuScreen'

# Feature flag to determine character/color rendering
advanced_term:             bool = os.environ.get('TERM', '').endswith('-256color')

# Lock for checking when the headless UI is fully loaded
ui_loaded:                 bool = False

# Global headless UI screen manager instance
screen_manager: 'AppScreenManager'

# Global reference to the main menu
main_menu:        'MainMenuScreen'

# Define the color palette
palette = [

    # Main menu palette
    ('caption_space',      'white', 'dark gray' if advanced_term else ''),
    ('caption_marker',     'dark gray', ''),
    ('input',              'light green', '', '', '#05e665', ''),
    ('hint',               'dark gray', ''),
    ('menu_line',          'white', '', '', '#444444', ''),
    ('telepath_enabled',   'light cyan', ''),
    ('telepath_disabled',  'dark gray', ''),
    ('telepath_host',      'dark cyan', ''),

    # Command response formatting
    ('success',            'light green', ''),
    ('fail',               'light red', '', '', '#ff2020', ''),
    ('warn',               'yellow', ''),
    ('info',               'dark gray', ''),
    ('normal',             'white', ''),
    ('command',            'light green', '', '', '#05e665', ''),
    ('sub_command',        'dark cyan', '', '', '#13e8cc', ''),
    ('parameter',          'yellow', '', '', '#F3ED61', ''),
    ('type_a',             'light magenta', '', '', '#FF00AA', ''),
    ('type_b',             'light cyan', ''),



    # ConsolePanel palette
    ('title',              'white', 'dark gray'),
    ('box_title',          'white', ''),
    ('stat',               'light gray', ''),
    ('input_header',       'light gray', ''),
    ('input',              'white', ''),
    ('linebox',            'dark gray', ''),
    ('bar_inactive',       'dark gray', '', '', 'h233', ''),
    ('bar_label',          'dark gray', '', '', 'h240', ''),
    ('ip',                 'light green', ''),

    # Performance panel colors
    ('perf_normal',        'light green', '', '', '#22FF66', ''),
    ('perf_warn',          'yellow', ''),
    ('perf_critical',      'light red', '', '', '#FF3333', ''),

    # Event colors
    ('console_gray',       'light gray', ''),
    ('console_gray_bg',    'black', 'light gray'),
    ('console_purple',     'dark blue', '', '', '#6666FF', ''),
    ('console_purple_bg',  'black', 'dark blue', '', 'black', '#6666FF'),
    ('console_green',      'light green', '', '', '#22FF66', ''),
    ('console_green_bg',   'black', 'light green', '', 'black', '#22FF66'),
    ('console_blue',       'light cyan', ''),
    ('console_blue_bg',    'black', 'light cyan'),
    ('console_pink',       'light magenta', '', '', '#FF00AA', ''),
    ('console_pink_bg',    'black', 'light magenta', '', 'black', '#FF00AA'),
    ('console_red',        'light red', '', '', '#FF3333', ''),
    ('console_red_bg',     'black', 'light red', '', 'black', '#FF3333'),
    ('console_orange',     'yellow', '', '', '#FF9525', ''),
    ('console_orange_bg',  'yellow', '', '', 'black', '#FF9525'),
    ('console_yellow',     'yellow', ''),
    ('console_yellow_bg',  'black', 'yellow'),



    # 'server.properties' palette
    ('key',                'dark blue', '', '', '#4455FF', ''),
    ('comment',            'dark gray', '', '', '#636363', ''),
    ('line',               'dark gray', '', '', 'h239', ''),
    ('eq',                 'dark gray', ''),
    ('selected_line',      'white', '', '', '#B2B2FF', ''),
    ('selected_eq',        'white', ''),
    ('search_highlight',   'black', 'light green', '', 'black', '#4DFF99'),
    ('search_bar',         'white', 'dark gray', '', 'white', '#333333'),

    ('boolean',            'light magenta', '', '', '#DD53DD', ''),
    ('integer',            'yellow', '', '', '#FF9525', ''),
    ('string',             'light cyan', '', '', '#68E3FF', ''),
    ('scrollbar_thumb',    'light gray', '')
]



# --------------------------------------------- General Functions ------------------------------------------------------

# UI log wrapper
def send_log(object_data, message, level=None):
    from source.core import logger
    return logger.send_log(f'{__name__}.{object_data}', message, level, 'ui')


# Overwrite STDOUT to not interfere with the UI
class NullWriter:
    encoding = None
    def write(self, *args, **kwargs): pass
    def flush(self): pass



# ---------------------------------------------- Command Handlers ------------------------------------------------------

# Lists/updates app to the latest version
def update_app(info=False):

    # Display update info
    if info:
        if not constants.is_docker:
            return [
                ("sub_command", f"(!) Update - v{constants.update_data['version']}\n\n"),
                ("info", constants.update_data['desc'].replace('\r','').strip() + '\n\n'),
                ("success", main_menu.response_header),
                ("normal", "To update to this version, run "),
                ("command", "update "),
                ("sub_command", "install ")
            ]
        else:
            return [
                ("sub_command", f"(!) Update - v{constants.update_data['version']}\n\n"),
                ("info", constants.update_data['desc'].replace('\r','').strip() + '\n\n'),
                ("success", main_menu.response_header),
                ("normal", "Update to this version from Docker Hub")
            ]

    else:
        main_menu.update_console([("info", main_menu.response_header), ('parameter', f'Downloading auto-mcs v{constants.update_data["version"].strip()}...')])
        if constants.download_update():
            main_menu.update_console([("success", main_menu.response_header), ('command', f'Successfully installed the update! Restarting...')])
            time.sleep(3)
            constants.restart_update_app()

        else: return [("info", "Something went wrong installing the update. Please try again later")], 'fail'

def set_debug(enable: bool | None):
    if isinstance(enable, bool): constants.debug = enable
    verb = 'enabled' if constants.debug else 'disabled'
    if enable is None: return [("info", f"Debug logging is currently {verb} for this session")], 'success'
    send_log('set_debug', f'{verb} debug logging for this session', 'info')
    return [("info", f"{verb.title()} debug logging for this session")], 'success'



# ---------------------- Change and list Java installation
def manage_java(mode: str, *args):
    from source.core.tools import java
    supported = java.manager.supported_vendors
    current   = java.manager.vendor


    # Show available/selected vendors
    if mode == 'list':
        if supported:
            return_text = [('normal', f'Available Java vendors'),  ('success', ' * - active'), ('info', f' ({len(supported)} total):\n\n')]
            line = ''
            for vendor in supported:
                active = vendor == current
                text = f'{"*" if active else ""}{vendor}    '
                line += text
                if len(line) > screen_manager.screen_size[0] - 20:
                    return_text.append(('info', '\n\n'))
                    line = ''
                return_text.append(('success' if active else 'info', text))
            return return_text
        else: return [('info', 'No Java vendors were found')], 'fail'


    # Actively configure the active vendor
    elif mode == 'vendor':
        new_vendor = args[0].strip().lower()

        if new_vendor not in supported:
            return [
                ('parameter', new_vendor),
                ('info', ' is not supported. Please run '),
                ("command", "java "),
                ("sub_command", "list "),
                ("info", "to list available vendors")
            ], 'fail'

        if new_vendor == current:
            return [('parameter', new_vendor), ('info', ' is already selected')]

        java.manager.set_vendor(new_vendor)
        return [('parameter', new_vendor), ('info', ' is now selected and will install automatically')]



# ---------------------- Enable/disable playit per server
def enable_playit(name: str, enabled=True):
    if name.lower() in constants.server_manager.server_list_lower:
        server_obj = constants.server_manager.open_server(name)
        main_menu.update_console('Retrieving server configuration...')
        while not all(list(server_obj._check_object_init().values())):
            time.sleep(0.1)
        time.sleep(0.1)

        if not server_obj.proxy_installed():
            main_menu.update_console('Installing playit agent...')
            server_obj.install_proxy()

        main_menu.update_console('Configuring playit agent...')
        server_obj.enable_proxy(enabled)

        return [("normal", f"{'En' if enabled else 'Dis'}abled tunneling for "), ("parameter", name)]

    # If server doesn't exist
    else:
        return [('parameter', name), ('info',  ' does not exist')], 'fail'



# ---------------------- Server management/creation
def manage_server(name: str, action: str):

    def _exception_wrapper(exception: Exception, error_info: str) -> tuple[str, str]:
        from source.core import logger
        send_log('manage_server', f"{error_info}: {constants.format_traceback(exception)}", 'error')
        return logger.create_error_log(traceback.format_exc(), error_info=error_info)

    def func_wrapper(func: list or tuple or callable):
        def run():
            if isinstance(func, list or tuple):
                [f() for f in func]
            else: func()

        dTimer(0, run).start()

    def return_log(log): return log
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
        if len(name) <= 25:
            if '\n' in name: name = name.splitlines()[0]
            name = re.sub('[^a-zA-Z0-9 _().-]', '', name)
        else:
            return [("parameter", name), ("info", " is too long, shorten it and try again (25 max)")], 'fail'

        if name.lower() in constants.server_manager.server_list_lower:
            return [("parameter", name), ("info", " already exists")], 'fail'


        # Create server here
        foundry.new_server_info['name'] = name
        foundry.new_server_info['acl_object'] = acl.AclManager(name)

        # Run things and stuff
        action_list = []
        download_addons = False
        needs_installed = False

        if foundry.new_server_info['type'] != 'vanilla':

            download_addons = (
                foundry.new_server_info['addon_objects']
                or foundry.new_server_info['server_settings']['disable_chat_reporting']
                or foundry.new_server_info['server_settings']['geyser_support']
                or (foundry.new_server_info['type'] in ['fabric', 'quilt'])
            )

            needs_installed = foundry.new_server_info['type'] in ['forge', 'neoforge', 'fabric', 'quilt']

        verb = 'Validating' if os.path.exists(paths.java) else 'Installing'
        action_list.append((
            f'{verb} Java',
            functools.partial(constants.java_check, None, foundry.new_server_info['version'], foundry.new_server_info['type'])
        ))

        action_list.append((
            "Downloading 'server.jar'",
            foundry.download_jar
        ))

        if needs_installed:
            action_list.append((
                f"Installing {foundry.new_server_info['type'].title().replace('forge','Forge')}",
                foundry.install_server
            ))

        if download_addons:
            action_list.append((
                'Add-oning add-ons',
                foundry.iter_addons
            ))

        action_list.append((
            f"Applying server configuration",
            foundry.generate_server_files,
        ))

        action_list.append((
            "Creating initial back-up",
            foundry.create_backup
        ))


        # Actually run things and stuff
        for x, (text, func) in enumerate(action_list, 1):
            main_menu.update_console(f"({x}/{len(action_list)}) {text}")

            try: func()
            except Exception as e:
                error_info = f"{action.title()} failed on step {x} / {len(action_list)} - '{text}'"
                crash_log, file_path = _exception_wrapper(e, error_info)
                return [
                    ("fail", error_info),
                    ("info", f"\n\nLog at: '{file_path}'"),
                ]

        constants.server_manager.create_server_list()

        return [
            ("normal", "Successfully created "),
            ("parameter", name),
            ("info", f" ({foundry.new_server_info['type'].replace('craft','').title()} {foundry.new_server_info['version']})\n\n"),
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
        foundry.pre_server_create()
        is_backup_file = ((foundry.import_data['path'].endswith(".tgz") or foundry.import_data['path'].endswith(".amb")) and os.path.isfile(foundry.import_data['path']))

        try:
            verb = 'Validating' if os.path.exists(paths.java) else 'Installing'
            main_menu.update_console(f'(1/4) {verb} Java')

            # Server import requires all Java builds because it generally has to run the server to find the version
            constants.java_check()

            main_menu.update_console(f"(2/4) Importing server")
            foundry.scan_import(is_backup_file)

            main_menu.update_console(f"(3/4) Validating configuration")
            foundry.finalize_import()

            main_menu.update_console(f"(4/4) Creating initial back-up")
            foundry.create_backup(True)

            constants.server_manager.create_server_list()

        except Exception as e:
            error_info = f"Error importing '{name}'", 'fail'
            crash_log, file_path = _exception_wrapper(e, error_info)
            return [
                ("fail", error_info),
                ("info", f"\n\nLog at: '{file_path}'"),
            ]

        return [
            ("normal", "Successfully imported "),
            ("parameter", name),
            ("info", f" ({foundry.new_server_info['type'].replace('craft', '').title()} {foundry.new_server_info['version']})\n\n"),
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
    elif name.lower() in constants.server_manager.server_list_lower:
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

            return screen_manager.screens['ServerViewScreen'].open_console(name, force_start=True)

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
                func_wrapper([server_obj.delete, constants.server_manager.create_server_list])
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
            main_menu.update_console([("info", "Saving a back-up of "), ("parameter", name), ("info", "...")])
            if not server_obj.backup:
                time.sleep(0.1)
            server_obj.backup.save()
            constants.server_manager.current_server.reload_config()
            return [("normal", "Saved a back-up of "), ("parameter", name)]

        elif action == 'restore':
            if not server_obj.running:
                if not server_obj.backup:
                    time.sleep(0.1)
                main_menu.update_console([("info", "Restoring the latest back-up of "), ("parameter", name), ("info", "...")])
                server_obj.backup.restore(server_obj.backup.latest)
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
    else: return [('parameter', name), ('info',  ' does not exist')], 'fail'

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
                template = foundry.ist_data[file]
                foundry.apply_template(template)

                return manage_server(name, 'create')

            except KeyError:
                pass

        return 'Invalid instant template specified', 'fail'

    # Manual version
    else:
        foundry.new_server_init()
        foundry.new_server_info['type'] = 'vanilla'
        name = data[1]
        data = data[0].replace('bukkit','craftbukkit').replace('builds','').lower()

        # Check if only a version was specified
        if data.replace('.', '').isdigit() or data == 'latest':
            foundry.new_server_info['version'] = data

        # Check if only a type was specified
        elif ':' not in data:
            foundry.new_server_info['type'] = data

        # Check if both a type and version was specified
        else:
            foundry.new_server_info['type'], foundry.new_server_info['version'] = data.split(':', 1)


        # Fail if type is invalid
        if foundry.new_server_info['type'] not in list(foundry.latestMC.keys()):
            return [('fail', foundry.new_server_info['type']), ('info', ' is not a supported server type')], 'fail'

        # Set to latest version if specified
        if foundry.new_server_info['version'] == 'latest':
            foundry.new_server_info['version'] = foundry.latestMC[foundry.new_server_info['type']]

        # Check if version is valid
        version_data = foundry.search_version(foundry.new_server_info)
        if not version_data[0]:
            return [('fail', foundry.new_server_info['version']), ('info', f' is not a supported {foundry.new_server_info["type"].replace("craft","").title()} version')], 'fail'

        foundry.new_server_info['version'] = version_data[1]['version']
        foundry.new_server_info['build'] = version_data[1]['build']
        foundry.new_server_info['jar_link'] = version_data[3]

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
        elif paths.servers in selected_server and os.path.basename(selected_server).lower() in constants.server_manager.server_list_lower:
            return 'This server already exists', 'fail'

        # If server is valid, do this
        else:
            foundry.import_data = {
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
        test_path = paths.temp
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
                    config_file = manager.server_config(server_name=None, config_path=new_path)
                    server_name = config_file.get('general', 'serverName')
                    foundry.new_server_info['type'] = config_file.get('general', 'serverType')
                    foundry.new_server_info['version'] = config_file.get('general', 'serverVersion')
                except:
                    pass
                file_failure = False

        os.chdir(cwd)
        constants.safe_delete(test_path)

        # Check if the selected server is invalid
        if file_failure:
            return 'Invalid back-up', 'fail'


        # Don't allow import of already imported servers
        elif server_name.lower() in constants.server_manager.server_list_lower:
            return 'This server already exists', 'fail'

        # If server is valid, do this
        else:
            foundry.import_data = {
                'name': re.sub('[^a-zA-Z0-9 _().-]', '', server_name.splitlines()[0])[:25],
                'path': selected_server
            }

    else:
        return 'Invalid server, or back-up', 'fail'

    # Valid server/back-up file
    return manage_server(foundry.import_data['name'], 'import')

def list_servers():
    constants.server_manager.create_server_list()
    if constants.server_manager.server_list:
        return_text = [('normal', f'Installed Servers'),  ('success', ' * - active'), ('info', f' ({len(constants.server_manager.server_list)} total):\n\n')]
        line = ''
        for server in constants.server_manager.server_list:
            running = server in constants.server_manager.running_servers
            text = f'{"*" if running else ""}{server}    '
            line += text
            if len(line) > screen_manager.screen_size[0] - 20:
                return_text.append(('info', '\n\n'))
                line = ''
            return_text.append(('success' if running else 'info', text))
        return return_text
    else: return [('info', 'No servers were found')], 'fail'



# ---------------------- Telepath interactions

# Refreshes Telepath display data at the top
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
    main_menu.telepath_content.set_text([header, text])
    return data

# Reset Telepath to default configuration
def reset_telepath(data=None):
    api = constants.api_manager
    api.stop()
    api._reset_session()
    time.sleep(0.1)  # for LUCK :)
    api.start()
    return f'Telepath data has {"not " if bool(api.authenticated_sessions) else ""}been cleared'

# Handles Telepath pair requests
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
            main_menu.update_console([
                ('success', main_menu.response_header),
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
    main_menu.update_console([
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

# Temporarily prevents a user from connecting
def telepath_restrict(user_id=None):

    # Input validate user ID
    if user_id:
        try:    user_id = int(user_id.strip('# ')) - 1
        except: user_id = None

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

# Revokes Telepath access from a user
def telepath_revoke(user_id=None):

    # Input validate user ID
    if user_id:
        try:    user_id = int(user_id.strip('# ')) - 1
        except: user_id = None


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



# ---------------------- Screen transitions
def open_console(name: str):
    console: MenuBackground = screen_manager.screens['ServerViewScreen']
    return console.open_console(name)

def edit_properties(name: str):
    editor: MenuBackground = screen_manager.screens['ServerPropertiesEditScreen']
    return editor.open_editor(name)

def open_log():
    log_view: MenuBackground = screen_manager.screens['LogViewScreen']
    return log_view.open_log()



# ---------------------------------------------- Helper Methods --------------------------------------------------------

# Retrieves a palette color
def get_color(key):
    for c in palette:
        if key == c[0]:
            return c


# Override print
if not constants.is_admin() and not constants.debug:
    def print(*args, **kwargs):
        main_menu.telepath_content.set_text(" ".join([str(a) for a in args]))


# Initialize Telepath menu overrides
class TelepathPair():
    def __init__(self):
        self.is_open = False
        self.pair_data = {}

    # Close "popup"
    def close(self):
        if not self.is_open:
            return

        try:
            current_user = constants.api_manager.current_users[self.pair_data['host']['ip']]
            if current_user and current_user['host'] == self.pair_data['host']['host'] and current_user['user'] == self.pair_data['host']['user']:
                message = f"Successfully paired with '${current_user['host']}/{current_user['user']}$'"
            else:
                message = f'$Telepath$ pair request expired'

        # Failed to pair
        except Exception as e:
            message = f'$Telepath$ pairing failed'
            if constants.debug:
                print(f'Telepath - failed to pair: {e}')

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
def telepath_banner(message: str, finished: bool, play_sound=None): return None
def telepath_disconnect(): return None
constants.telepath_pair = TelepathPair()
constants.telepath_banner = telepath_banner
constants.telepath_disconnect = telepath_disconnect
telepath.create_endpoint(constants.telepath_banner, 'main', True)



# ------------------------------------------- Global Screen Manager ----------------------------------------------------

class AppScreenManager():
    _initialized: bool = False
    _screen: 'urwid.Screen'
    screens: dict[str, MenuBackground]

    loop:            urwid.MainLoop | None = None
    current_screen:  MenuBackground | None = None
    screen_tree:                 list[str] = []


    def __init__(self):
        self._placeholder = urwid.WidgetPlaceholder(urwid.Text(""))

        # Initialize screen loop
        self._screen = urwid.raw_display.Screen()
        self._screen.set_terminal_properties(colors=256)
        self._screen.register_palette(palette)
        self._loop = urwid.MainLoop(self._placeholder, screen=self._screen)

        # Set screens in memory for hot swapping
        self.screens = {}
        self.initialize()

    @property
    def screen_size(self) -> tuple[int, int]:
        return self._loop.screen_size

    def initialize(self):
        if not self._initialized:
            self._initialized = True


            # Recurse & import all view *Screen classes to load into memory
            base_pkg = 'source.ui.headless.views'
            max_depth = 6

            pkg = importlib.import_module(base_pkg)
            base_depth = base_pkg.count('.')
            stack = [(base_pkg, list(getattr(pkg, '__path__', [])))]
            seen_mods = {base_pkg}
            seen_cls = set()


            # Collect child views once: {name: is_pkg}
            while stack:
                pkg_name, pkg_paths = stack.pop()

                children = {}
                for _, name, is_pkg in pkgutil.iter_modules(pkg_paths, pkg_name + '.'):
                    if (name.count('.') - base_depth) <= max_depth and name not in seen_mods: children[name] = is_pkg

                for root in pkg_paths:
                    try:
                        with os.scandir(root) as it:
                            for e in it:
                                if e.name.startswith(('.', '_')): continue
                                if e.is_dir():
                                    sub = f'{pkg_name}.{e.name}'
                                    if (
                                        (sub.count('.') - base_depth) <= max_depth and
                                        sub not in seen_mods and
                                        importlib.util.find_spec(sub) is not None
                                    ):
                                        children.setdefault(sub, True)

                                elif e.is_file() and e.name.endswith('.py'):
                                    mod = f'{pkg_name}.{e.name[:-3]}'
                                    if (mod.count('.') - base_depth) <= max_depth: children.setdefault(mod, False)

                    except FileNotFoundError: pass


                # Recurse into subpackages, import modules and retrieve classes
                for name, is_pkg in children.items():
                    seen_mods.add(name)
                    if is_pkg:
                        try:
                            sub = importlib.import_module(name)
                            paths = list(getattr(sub, '__path__', []))
                            if paths: stack.append((name, paths))
                        except: pass
                        continue

                    try: mod = importlib.import_module(name)
                    except: continue


                    # Add to screen list if it's not a duplicate, and definitely a Screen derivative
                    for _, cls in inspect.getmembers(mod, inspect.isclass):
                        if (
                            issubclass(cls, MenuBackground) and
                            cls is not MenuBackground and
                            cls.__name__.endswith('Screen') and
                            cls not in seen_cls
                        ):
                            seen_cls.add(cls)
                            try: self.screens[cls.__name__] = cls()
                            except Exception as e: send_log(f"error loading screen '{cls.__name__}': {constants.format_traceback(e)}", 'error')

            global ui_loaded; ui_loaded = True
            self.current = startup_screen

    @property
    def current(self) -> str:
        return self.current_screen.name

    @current.setter
    def current(self, screen_name: str):
        if screen_name not in self.screens: raise ValueError(f"screen with name '{screen_name}' does not exist")
        self.current_screen = self.screens[screen_name]
        self._placeholder.original_widget = self.current_screen.menu
        self._loop.unhandled_input = self.current_screen.handle_input

screen_manager = AppScreenManager()
main_menu = screen_manager.screens['MainMenuScreen']
refresh_telepath_host()
