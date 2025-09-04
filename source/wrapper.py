from traceback import format_exc
import threading
import argparse
import requests
import ctypes
import glob
import time
import sys
import os
import gc


# Show a console in '--debug' mode on Windows if compiled
def setup_windows_debug_console(redirect_to_devnull: bool = True):

    app_title = "auto-mcs (console)"
    is_windows = (os.name == "nt")
    is_compiled = bool(getattr(sys, "frozen", False))  # PyInstaller/py2exe style
    args = sys.argv
    debug = any(a in ("-d", "--debug") for a in args)
    headless = any(a in ("-s", "--headless") for a in args)


    # Ignore on other operating systems as they have STDIO
    if not is_windows:
        return

    # Ignore if running as Python, since it has STDIO
    if not is_compiled:
        return

    # Ignore if headless
    if headless:
        return


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
        if redirect_to_devnull:
            sys.stdout = open(os.devnull, "w", encoding="utf-8", buffering=1)
            sys.stderr = open(os.devnull, "w", encoding="utf-8", buffering=1)



if __name__ == '__main__':

    # Modify garbage collector
    gc.collect(2)
    gc.freeze()


    import multiprocessing
    multiprocessing.set_start_method("spawn")
    multiprocessing.freeze_support()

    # If running in a spawned process, don't initialize anything
    if multiprocessing.parent_process():
        sys.exit()


    # Open debug console for Windows windowed builds (or silence stdio otherwise)
    setup_windows_debug_console()


    # Import constants and set variables
    import constants
    import telepath


    # Logging wrapper
    def send_log(object_data, message, level=None):
        return constants.send_log(f'wrapper.{object_data}', message, level)


    # Migrate old logs (<2.3.3) to new location

    # Move old error logs
    old_log_dir = os.path.join(constants.applicationFolder, "Logs")
    log_dir = os.path.join(constants.applicationFolder, "Logs", "errors")
    error_logs = glob.glob(os.path.join(old_log_dir, "ame-error*.log"))
    if error_logs:
        send_log('', f"migrating old error logs to '{log_dir}'", 'warning')
        constants.folder_check(log_dir)
        [constants.move(file, os.path.join(log_dir, os.path.basename(file))) for file in error_logs]

    # Move old crash logs
    old_log_dir = os.path.join(constants.applicationFolder, "Logs")
    log_dir = os.path.join(constants.applicationFolder, "Logs", "crashes")
    error_logs = glob.glob(os.path.join(old_log_dir, "ame-fatal*.log"))
    if error_logs:
        send_log('', f"migrating old crash logs to '{log_dir}'", 'warning')
        constants.folder_check(log_dir)
        [constants.move(file, os.path.join(log_dir, os.path.basename(file))) for file in error_logs]

    # Move old Telepath logs
    old_log_dir = os.path.join(constants.telepathDir, 'audit-logs')
    log_dir = os.path.join(constants.applicationFolder, 'Logs', 'telepath')
    audit_logs = glob.glob(os.path.join(old_log_dir, "session-audit_*.log"))
    if audit_logs:
        send_log('', f"migrating old Telepath audit-logs to '{log_dir}'", 'warning')
        constants.folder_check(log_dir)
        [constants.move(file, os.path.join(log_dir, os.path.basename(file))) for file in audit_logs]
        constants.safe_delete(old_log_dir)



    # Set launch path, username
    constants.launch_path = sys.executable if constants.app_compiled else __file__

    # Set username
    try: constants.username = constants.run_proc('whoami', True).split('\\')[-1].strip()
    except: pass

    # Set hostname
    try:
        if constants.is_docker: constants.hostname = constants.app_title
        else:                   constants.hostname = constants.run_proc('hostname', True).strip()
    except: pass


    # Check for update log
    update_log = None
    try:
        update_log = os.path.join(constants.tempDir, 'update-log')
        if os.path.exists(update_log):
            with open(update_log, 'r') as f:
                constants.update_data['reboot-msg'] = f.read().strip().split("@")
            send_log('', f"update complete: '{constants.update_data['reboot-msg']}'", 'info')
    except: pass



    # Check for additional arguments
    reset_config = False
    try:
        parser = argparse.ArgumentParser(description='CLI options for auto-mcs')
        parser.add_argument('-d', '--debug', default='', help='execute auto-mcs with verbose console logging', action='store_true')
        parser.add_argument('-l', '--launch', type=str, default='', help='specify a server name (or list of server names) to launch automatically', metavar='"Server 1, Server 2"')
        parser.add_argument('--reset', default='', help='reset global configuration file before launch', action='store_true')
        parser.add_argument('--bypass-admin-warning', default='', help='allow launch as admin/root (not recommended)', action='store_true')

        # For now, Windows doesn't support headless when compiled due to the GUI entrypoint from Pyinstaller
        if constants.os_name != 'windows' or not constants.app_compiled:
            parser.add_argument('-s', '--headless', default='', help='launch without initializing the UI and enable the Telepath API', action='store_true')



        # Assign parsed arguments to global variables
        args = constants.boot_arguments = parser.parse_args()
        constants.debug = args.debug
        reset_config = args.reset
        constants.bypass_admin_warning = args.bypass_admin_warning
        if constants.os_name != 'windows' or not constants.app_compiled:
            constants.headless = args.headless


        # Delete STDIO on Windows
        if constants.os_name == 'windows' and constants.app_compiled and not constants.debug:
            sys.stdout = open(os.devnull, 'w')
            sys.stderr = open(os.devnull, 'w')


        # Force headless if display is not set on Linux
        if (constants.os_name == 'linux' and 'DISPLAY' not in os.environ) or constants.is_docker:
            constants.headless = True

        # Close splash if headless & compiled
        if constants.app_compiled and constants.headless and constants.os_name == 'windows':
            import pyi_splash
            pyi_splash.close()


        # Check for auto-start
        if args.launch:
            constants.generate_server_list()
            server_list = [s.strip() for s in args.launch.split(',')]
            for server in server_list:
                if server.lower() in constants.server_list_lower:
                    server = constants.server_list[constants.server_list_lower.index(server.lower())]
                    constants.boot_launches.append(server)
                else:
                    send_log('', f"--launch: '{server}' does not exist", 'fatal')
                    sys.exit(-1)

    except AttributeError as e:
        send_log('', f"error processing CLI arguments: {constants.format_traceback(e)}", 'error')


    # Check if application is already open (Unless running in Docker)
    if not constants.is_docker:
        if constants.os_name == "windows":
            command = f'tasklist | findstr {os.path.basename(constants.launch_path)}'
            response = [line for line in constants.run_proc(command, True).strip().splitlines() if ((command not in line) and ('tasklist' not in line) and (line.endswith(' K')))]
            if len(response) > 2:
                user32 = ctypes.WinDLL('user32')
                if hwnd := user32.FindWindowW(None, constants.app_title):
                    if not user32.IsZoomed(hwnd):
                        user32.ShowWindow(hwnd, 1)
                    user32.SetForegroundWindow(hwnd)
                send_log('', f"closed: {constants.app_title} is already open, only a single instance can be open at the same time:\n{response}", 'fatal')
                sys.exit(10)

        elif constants.os_name == "macos":
            command = f'ps -e | grep .app/Contents/MacOS/{os.path.basename(constants.launch_path)}'
            response = [line for line in constants.run_proc(command, True).strip().splitlines() if command not in line and 'grep' not in line and line]
            if len(response) > 2:
                send_log('', f"closed: {constants.app_title} is already open, only a single instance can be open at the same time:\n{response}", 'fatal')
                sys.exit(10)

        # Linux
        else:
            command = f'ps -e | grep {os.path.basename(constants.launch_path)}'
            response = [line for line in constants.run_proc(command, True).strip().splitlines() if command not in line and 'grep' not in line and line]
            if len(response) > 2:
                send_log('', f"closed: {constants.app_title} is already open, only a single instance can be open at the same time:\n{response}", 'fatal')
                sys.exit(10)



    # Initialize Tk before Kivy due to a bug with SDL2
    if constants.os_name == 'macos' and not constants.headless:
        import tkinter as tk
        init_window = tk.Tk()
        init_window.withdraw()



    # Delete configuration/cache if flag is set
    if reset_config:
        constants.safe_delete(constants.cacheDir)
        constants.app_config.reset()



    # Get default system language
    try:
        if constants.os_name == 'macos': system_locale = constants.run_proc("osascript -e 'user locale of (get system info)'", True)

        else:
            from locale import getdefaultlocale
            system_locale = getdefaultlocale()[0]

        if '_' in system_locale:
            system_locale = system_locale.split('_')[0]

        for v in constants.available_locales.values():
            if system_locale.startswith(v['code']):
                if not constants.app_config.locale: constants.app_config.locale = v['code']
                break

    except Exception as e:
        if not constants.is_docker:
            send_log('', f'failed to determine locale: {e}', 'error')

    if not constants.app_config.locale:
        constants.app_config.locale = 'en'


    import main


    # Variables
    exitApp = False
    crash = None


    # Functions
    def cleanup_on_close():

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
        for img in glob.glob(os.path.join(constants.gui_assets, 'live', '*')):
            try: os.remove(img)
            except OSError: pass
        if not update_log or not os.path.exists(update_log):
            constants.safe_delete(constants.tempDir)

    def app_crash(traceback, exception):
        import crashmgr
        exc_code, log_path = crashmgr.generate_log(traceback)
        send_log('app_crash', f"{constants.app_title} has crashed with exception code:  {exc_code}\nFull crash log available in:  '{log_path}'", 'fatal')

        # Normal Python behavior when testing
        if not constants.app_compiled: raise exception

        # Otherwise, launch appropriate crash hook
        crashmgr.launch_window(exc_code, log_path)


    # Main wrapper
    def background():
        global exitApp, crash
        send_log('background', 'initializing the background thread', 'debug')

        # Check for updates
        constants.check_app_updates()
        constants.search_manager = constants.SearchManager()

        # Try to log into telepath servers automatically
        if os.path.exists(constants.telepathFile):
            while not constants.server_manager: time.sleep(0.1)
            if constants.server_list_lower:
                constants.server_manager.check_telepath_servers()

        def background_launch(func, *a):
            global exitApp, crash

            if exitApp or crash:
                return

            try: func()
            except Exception as e:
                send_log('background.background_launch', f"error running background task '{func}': {constants.format_traceback(e)}", 'error')

        # Find latest game versions and update data cache
        def get_public_ip(*a):
            constants.public_ip = requests.get('https://api.ipify.org').content.decode('utf-8')
        def get_versions(*a):
            constants.find_latest_mc()
            constants.make_update_list()
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
            if exitApp or crash: break
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


                if not (exitApp or crash): time.sleep(1)

        send_log('background', 'closed the background thread', 'debug')

    def foreground():
        global exitApp, crash

        # Main thread
        try:
            main.ui_loop()
            exitApp = True

        except SystemExit:
            exitApp = True

        # On crash
        except Exception as e:
            crash = format_exc()
            exitApp = True
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


    # Launch API before UI
    # Move this to the top, and grab the global config variable "enable_api" to launch here on boot if True
    constants.api_manager = telepath.TelepathManager()
    config = constants.app_config
    if ((config.telepath_settings['enable-api'] or constants.headless) and not constants.is_admin()) or constants.is_docker:
        constants.api_manager.update_config(config.telepath_settings['api-host'], config.telepath_settings['api-port'])
        constants.api_manager.start()


    # Launch/threading logic
    b = threading.Thread(name='background', target=background)
    b.setDaemon(True)

    b.start()
    foreground()
    b.join()

    # Exit with return code if there's a crash
    if crash: sys.exit(20)
