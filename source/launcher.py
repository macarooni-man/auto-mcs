from traceback import format_exc
from os import path
import threading
import argparse
import requests
import ctypes
import glob
import time
import sys
import os
import gc



# ------------------------------------------------- Helper Methods -----------------------------------------------------

# Logging wrapper
def send_log(object_data, message, level=None):
    from source.core import constants
    return constants.send_log(f'main.{object_data}', message, level)

# Exits after a delay so that the logger has time to write on its own thread
def exit_with_log(*a, exit_code: int = 0, **kw):
    send_log(*a, **kw)
    time.sleep(0.1)
    sys.exit(exit_code)

# Setup garbage collector and multiprocessing settings
def setup_multiprocessing():

    # Modify garbage collector
    gc.collect(2)
    gc.freeze()

    # Configure multiprocessing
    import multiprocessing
    multiprocessing.set_start_method("spawn")
    multiprocessing.freeze_support()

    # If running in a spawned process, don't initialize anything
    if multiprocessing.parent_process():
        sys.exit()

# Show a console in '--debug' mode on Windows if compiled
def init_windows_console():

    app_title = "auto-mcs (console)"
    is_windows = (os.name == "nt")
    is_compiled = bool(getattr(sys, "frozen", False))  # PyInstaller/py2exe style
    args = sys.argv
    debug = any(a in ("-d", "--debug") for a in args)
    headless = any(a in ("-s", "--headless") for a in args)


    # Ignore on other operating systems as they have STDIO
    if not is_windows: return

    # Ignore if running as Python, since it has STDIO
    if not is_compiled: return

    # Ignore if headless
    if headless: return


    # Attach a console and wire stdio to it
    if debug:
        import ctypes
        k32 = ctypes.windll.kernel32
        ATTACH_PARENT_PROCESS = -1

        # Try to attach to parent console first, or allocate a new one
        attached = bool(k32.AttachConsole(ATTACH_PARENT_PROCESS))
        if not attached:
            allocated = bool(k32.AllocConsole())

            # If a console can't be acquired, don't redirect
            if not allocated: return

        # UTF-8 code page
        k32.SetConsoleCP(65001)
        k32.SetConsoleOutputCP(65001)

        # Enable ANSI escape sequences (VT) for colors
        STD_OUTPUT_HANDLE = -11
        ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
        hOut = k32.GetStdHandle(STD_OUTPUT_HANDLE)
        mode = ctypes.c_uint()
        if k32.GetConsoleMode(hOut, ctypes.byref(mode)):
            k32.SetConsoleMode(hOut, mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING)

        # Bind Python STDIO to the console
        sys.stdout = open("CONOUT$", "w", encoding="utf-8", buffering=1)
        sys.stderr = open("CONOUT$", "w", encoding="utf-8", buffering=1)
        sys.stdin  = open("CONIN$",  "r", encoding="utf-8", buffering=1)

        # OH YEAH BUSTER, IT'S COLOR TIME
        try: ctypes.windll.kernel32.SetConsoleTitleW(str(app_title))
        except Exception: pass
        try:
            import colorama
            colorama.just_fix_windows_console()
        except Exception: pass


    # Silence STDIO for non-debug runs so the UI app stays quiet
    else:
        sys.stdout = open(os.devnull, "w", encoding="utf-8", buffering=1)
        sys.stderr = open(os.devnull, "w", encoding="utf-8", buffering=1)

# Migrate old logs (<2.3.3) to new location
def migrate_legacy_logs():
    from source.core import constants

    # Move files matching 'pattern' under 'base_dir' into 'Logs/target_subdir'
    def _migrate(pattern: str, target_subdir: str, base_dir: str, delete_source_dir: bool = False):
        old_dir = path.join(base_dir)
        files = glob.glob(path.join(old_dir, pattern))
        if not files: return

        new_dir = path.join(constants.applicationFolder, "Logs", target_subdir)
        try:
            constants.send_log('migrate_legacy_logs',f"migrating {len(files)} '{pattern}' to '{new_dir}'", level='warning')
            constants.folder_check(new_dir)
            for src in files:
                dst = path.join(new_dir, path.basename(src))
                constants.move(src, dst)

        except Exception as e:
            constants.send_log(f"migrate_legacy_logs.{target_subdir}",f"error migrating '{pattern}': {constants.format_traceback(e)}", level='error')

        else:
            if delete_source_dir:
                try: constants.safe_delete(old_dir)
                except Exception as e: constants.send_log('migrate_legacy_logs',f"failed to delete source dir '{old_dir}': {constants.format_traceback(e)}", level='error')

    app_logs   = path.join(constants.applicationFolder, "Logs")
    audit_logs = path.join(constants.telepathDir, "audit-logs")
    _migrate("ame-error*.log", "errors", app_logs)
    _migrate("ame-fatal*.log", "crashes", app_logs)
    _migrate("session-audit_*.log", "telepath", audit_logs, delete_source_dir=True)

# Retrieve runtime variables from the system
def get_system_context():
    from source.core import constants

    # Set launch path
    constants.launch_path = sys.executable if constants.app_compiled else __file__


    # Set username
    try:    constants.username = constants.run_proc('whoami', True, log_only_in_debug=True).split('\\')[-1].strip()
    except: constants.username = 'user'


    # Set hostname
    if not constants.is_docker:
        try:
            hostname = constants.run_proc('hostname', True, log_only_in_debug=True).strip()
            if not 'hostname: command not found' in hostname: constants.hostname = hostname
        except: pass

    if not constants.hostname: constants.hostname = constants.app_title


    # Get default system language
    try:
        if constants.os_name == 'macos': system_locale = constants.run_proc("osascript -e 'user locale of (get system info)'", True, log_only_in_debug=True)

        else:
            from locale import getdefaultlocale
            system_locale = getdefaultlocale()[0]

        if '_' in system_locale: system_locale = system_locale.split('_')[0]

        for v in constants.available_locales.values():
            if system_locale.startswith(v['code']):
                if not constants.app_config.locale: constants.app_config.locale = v['code']
                break

    except Exception as e:
        if not constants.is_docker:
            send_log('get_system_context', f'failed to determine locale: {e}', 'error')

    if not constants.app_config.locale: constants.app_config.locale = 'en'

# Checks to see if an update log exists from a prior update
def check_if_updated() -> bool:
    from source.core import constants

    try:
        update_log = path.join(constants.tempDir, 'update-log')
        if path.exists(update_log):
            with open(update_log, 'r') as f:
                constants.update_data['reboot-msg'] = f.read().strip().split("@")
                send_log('', f"update complete: '{constants.update_data['reboot-msg']}'", 'info')
                return True

    except: pass
    return False

# Parse CLI args and apply boot-time side effects to 'constants'
def parse_boot_args():
    from source.core import constants
    reset_config = False

    try:
        parser = argparse.ArgumentParser(description='CLI options for auto-mcs')

        # Flags
        parser.add_argument(
            '-d', '--debug',
            help = 'execute auto-mcs with verbose console logging',
            action = 'store_true'
        )

        parser.add_argument(
            '-l', '--launch',
            type = str,
            default = '',
            metavar = '"Server 1, Server 2"',
            help = 'specify a server name (or list of server names) to launch automatically'
        )

        parser.add_argument(
            '--reset',
            help = 'reset global configuration file before launch',
            action = 'store_true'
        )

        parser.add_argument(
            '--bypass-admin-warning',
            help = 'allow launch as admin/root (not recommended)',
            action = 'store_true'
        )


        # Windows headless is unsupported when compiled (PyInstaller GUI entrypoint)
        if constants.os_name != 'windows' or not constants.app_compiled:
            parser.add_argument(
                '-s', '--headless',
                help = 'launch without initializing the UI and enable the Telepath API',
                action = 'store_true'
            )


        # Parse & assign to globals/constants
        args = parser.parse_args()
        constants.boot_arguments = args

        constants.debug = args.debug
        reset_config    = args.reset
        constants.bypass_admin_warning = args.bypass_admin_warning

        if constants.os_name != 'windows' or not constants.app_compiled:
            constants.headless = args.headless


        # Force headless if no display (Linux) or running in Docker
        if (constants.os_name == 'linux' and 'DISPLAY' not in os.environ) or constants.is_docker:
            constants.headless = True


        # Handle auto-start server list
        if args.launch:

            arg_server_list = [s.strip() for s in args.launch.split(',')]
            servers, servers_lower = zip(
                *[(f, f.lower()) for f in glob.glob(path.join(constants.serverDir, "*"))
                  if path.isfile(path.join(f, constants.server_ini))]
            )
            servers, servers_lower = list(servers), list(servers_lower)

            for server in arg_server_list:
                if server.lower() in servers_lower:
                    server = servers[servers_lower.index(server.lower())]
                    constants.boot_launches.append(server)

                else: exit_with_log('', f"--launch: '{server}' does not exist", 'fatal', exit_code=-1)


    except AttributeError as e:
        send_log('', f"error processing CLI arguments: {constants.format_traceback(e)}", 'error')


    # Delete configuration & cache if flag is set
    if reset_config:
        constants.safe_delete(constants.cacheDir)
        constants.app_config.reset()

# Ensure only a single instance of the app is running at the same time
def instance_check():
    from source.core import constants
    check_failed = False

    # Check if application is already open (Unless running in Docker)
    if not constants.is_docker:

        if constants.os_name == "windows":
            command = f'tasklist | findstr {path.basename(constants.launch_path)}'
            response = [line for line in constants.run_proc(command, True, log_only_in_debug=True).strip().splitlines() if ((command not in line) and ('tasklist' not in line) and (line.endswith(' K')))]
            if len(response) > 2:

                # Bring existing Window to the front of the screen
                user32 = ctypes.WinDLL('user32')
                if hwnd := user32.FindWindowW(None, constants.app_title):
                    if not user32.IsZoomed(hwnd): user32.ShowWindow(hwnd, 1)
                    user32.SetForegroundWindow(hwnd)
                check_failed = True


        elif constants.os_name == "macos":
            command = f'ps -e | grep .app/Contents/MacOS/{path.basename(constants.launch_path)}'
            response = [line for line in constants.run_proc(command, True, log_only_in_debug=True).strip().splitlines() if command not in line and 'grep' not in line and line]
            if len(response) > 2: check_failed = True


        else:  # Linux
            command = f'ps -e | grep {path.basename(constants.launch_path)}'
            response = [line for line in constants.run_proc(command, True, log_only_in_debug=True).strip().splitlines() if command not in line and 'grep' not in line and line]
            if len(response) > 2: check_failed = True


        if check_failed: exit_with_log('', f"closed: {constants.app_title} is already open, only a single instance can be open at the same time:\n{response}", 'fatal', exit_code=10)

# Runs OS-specific tweaks for standardizing the runtime context
init_window: 'tkinter.Tk' = None  # Only used on macOS
def os_context_tweaks():
    from source.core import constants
    global init_window


    # Windows specific tweaks
    # 'init_windows_console' must be initialized before 'constants' is imported
    # so, it's not in here because this method requires 'constants'
    if constants.os_name == 'windows':

        if constants.app_compiled and constants.headless:
            import pyi_splash
            pyi_splash.close()



    # macOS specific tweaks
    elif constants.os_name == 'macos':

        # Initialize Tk before Kivy due to a bug with SDL2
        if not constants.headless:
            import tkinter as tk
            init_window = tk.Tk()
            init_window.withdraw()



    # Linux specific tweaks
    else: pass

# Initialize Telepath if enabled
def init_telepath():
    from source.core import constants, telepath

    # Launch API before UI, grab the global config variable "enable_api" to launch here on boot if True
    constants.api_manager = telepath.TelepathManager()
    config = constants.app_config
    if ((config.telepath_settings['enable-api'] or constants.headless) and not constants.is_admin()) or constants.is_docker:
        constants.api_manager.update_config(config.telepath_settings['api-host'], config.telepath_settings['api-port'])
        constants.api_manager.start()



# ------------------------------------------------ Runtime Methods -----------------------------------------------------

# Flushes memory based data to disk, gracefully shuts down background threads, and cleans up temp files
def cleanup_on_close():
    from source.core import constants, telepath

    # Shut down Telepath API
    constants.api_manager.stop()
    constants.api_manager.close_sessions()

    # Cancel all token expiry timers to prevent hanging on close
    for timer in telepath.expire_timers:
        if timer.is_alive(): timer.cancel()

    # Close Discord rich presence
    try:
        if constants.discord_presence:
            if constants.discord_presence.presence: constants.discord_presence.presence.close()
    except: pass

    # Write logger to disk
    constants.log_manager.dump_to_disk()

    # Delete live images/temp files on close
    constants.safe_delete(path.join(constants.gui_assets, 'live'))
    constants.safe_delete(constants.tempDir)

# Handles switching execution context to a crash window that allows the app to be restarted
def app_crash(traceback, exception):
    from source.core import constants
    from source.ui import crashmgr

    exc_code, log_path = crashmgr.generate_log(traceback)
    send_log('app_crash', f"{constants.app_title} has crashed with exception code:  {exc_code}\n{constants.format_traceback(exception)}\nFull crash log available in:  '{log_path}'", 'fatal')

    # Normal Python behavior when testing
    if not constants.app_compiled: raise exception

    # Otherwise, launch appropriate crash hook
    crashmgr.launch_window(exc_code, log_path)



# This is the app entrypoint
if __name__ == '__main__':

    # ----------------------------------------------- Boot Pipeline ----------------------------------------------------

    # Setup proper multiprocessing context
    setup_multiprocessing()

    # Open debug console for Windows windowed builds (or silence stdio otherwise)
    init_windows_console()

    # Initialize user variables and launch path
    get_system_context()

    # Ensure only one instance of the app is running at a time
    instance_check()

    # Migrate old logs to >=2.3.3 format
    migrate_legacy_logs()

    # Check for update log
    was_updated = check_if_updated()

    # Initialize boot options from arguments
    parse_boot_args()

    # Run OS-specific context tweaks/fixes
    os_context_tweaks()

    # Initialize Telepath
    init_telepath()



    # ---------------------------------------------- Launch Pipeline ---------------------------------------------------

    exit_app = False
    crash    = None

    # Background thread
    def background():
        from source.core import constants
        global exit_app, crash, was_updated
        send_log('background', 'initializing the background thread')

        # Check for updates
        constants.check_app_updates()
        constants.search_manager = constants.SearchManager()

        # If app was just updated, re-install playit if it's installed
        if was_updated: constants.playit.update_agent()

        # Wait until ServerManager is initialized
        while not constants.server_manager: time.sleep(0.1)

        # Try to log into telepath servers automatically
        if path.exists(constants.telepathFile):
            if constants.server_list_lower: constants.server_manager.check_telepath_servers()

        def background_launch(func, *a):
            global exit_app, crash

            if exit_app or crash:
                return

            try: func()
            except Exception as e:
                send_log('background.background_launch', f"error running background task '{func}': {constants.format_traceback(e)}", 'error')

        # Find latest game versions and update data cache
        def get_public_ip(*a):
            constants.public_ip = requests.get('https://api.ipify.org').content.decode('utf-8')
        def get_versions(*a):
            constants.find_latest_mc()
            constants.server_manager.check_for_updates()
            constants.get_repo_templates()
        background_launch(get_public_ip)
        background_launch(get_versions)
        background_launch(constants.load_addon_cache)
        background_launch(constants.check_data_cache)
        background_launch(constants.search_manager.cache_pages)


        # Update variables in the background
        connect_counter = 0
        log_counter = 0
        while True:

            # Exit this thread if the main thread closes, or crashes
            if exit_app or crash: break
            else:

                # Check for network changes in the background
                connect_counter += 1
                if (connect_counter >= 10 and not constants.app_online) or (connect_counter >= 3600 and constants.app_online):
                    try: constants.check_app_updates()
                    except Exception as e: send_log('background', f"error checking for app updates: {constants.format_traceback(e)}", 'error')
                    connect_counter = 0


                # Write logs in memory to disk every 5 minutes
                log_counter += 1
                if log_counter >= 300:
                    try: constants.log_manager.dump_to_disk()
                    except Exception as e: send_log('background', f"error writing application log to disk: {constants.format_traceback(e)}", 'error')
                    log_counter = 0


                if not (exit_app or crash): time.sleep(1)

        send_log('background', 'closed the background thread', 'debug')

    # Foreground/UI thread
    def foreground():
        from source.ui.main import ui_loop
        from source.core import constants
        global exit_app, crash, init_window

        # Main thread
        try:
            ui_loop()
            exit_app = True

        except SystemExit:
            exit_app = True

        # On crash
        except Exception as e:
            crash = format_exc()
            exit_app = True
            send_log('foreground', 'UI has exited unexpectedly', 'error')

            # Use crash handler when app is compiled
            if crash:

                # Destroy init window if macOS
                if constants.os_name == 'macos':
                    init_window.destroy()

                app_crash(crash, e)

            cleanup_on_close()


        # Log if the UI closed properly
        if not crash: send_log('foreground', 'UI has exited gracefully', 'info')


        # Destroy init window if macOS
        cleanup_on_close()
        if constants.os_name == 'macos' and not constants.headless and not crash:
            init_window.destroy()
            raise SystemExit()


    # Launch & threading logic
    background_thread = threading.Thread(name='background', target=background)
    background_thread.setDaemon(True)

    background_thread.start()
    foreground()
    background_thread.join()

    # Exit with return code if there's a crash
    if crash: sys.exit(20)



# ----------------------------------------------------------------------------------------------
#                             _
#                  __ _ _   _| |_ ___                   < Module execution chain >
#   ▄▄██████▄▄    / _` | | | | __/ _ \
#  ████████████  | (_| | |_| | || (_) |        -- Root: main <───────────────┐
# ████▀▀██▀▀████  \__,_|\__,_|\__\___/                ┆            ┆         │
# ████▄▄▀▀▄▄████   _ __ ___   ___ ___            (bg thread)  (fg thread)    │
# █████    █████  | '_ ` _ \ / __/ __|                ┆            ┆         ├── core.constants
#  ████▄██▄████   | | | | | | (__\__ \          crash-handler  ui.launch <───┤
#   ▀▀██████▀▀    |_| |_| |_|\___|___/                             ┆         │
#                                                ui.headless / ui.desktop <──┘
#
#   < Functional Tests >
#
#   - Windows 10 1909, 20H2, 21H2
#   - Windows 11 22H2
#   - macOS Monterey (Intel, 12.7.3)
#   - macOS Sequoia (M3, 15.4.1)
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
