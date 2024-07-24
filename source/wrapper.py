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


    # Import constants and set variables
    import constants
    import telepath


    # Initialize Tk before Kivy due to a bug with SDL2
    if constants.os_name == 'macos':
        import tkinter as tk
        init_window = tk.Tk()
        init_window.withdraw()


    constants.launch_path = sys.executable if constants.app_compiled else __file__
    try:
        constants.username = constants.run_proc('whoami', True).split('\\')[-1].strip()
    except:
        pass

    if constants.app_compiled:
        os.environ["KIVY_NO_CONSOLELOG"] = "1"

    # Check for update log
    update_log = None
    try:
        update_log = os.path.join(constants.tempDir, 'update-log')
        if os.path.exists(update_log):
            with open(update_log, 'r') as f:
                constants.update_data['reboot-msg'] = f.read().strip().split("@")
            print('Update complete: ', constants.update_data['reboot-msg'])
    except:
        pass



    # Check for additional arguments
    try:
        parser = argparse.ArgumentParser(description='CLI options for auto-mcs')
        parser.add_argument('-d', '--debug', default='' ,help='execute auto-mcs with verbose console logging', action='store_true')
        parser.add_argument('-l', '--launch', type=str, default='', help='specify a server name (or list of server names) to launch automatically', metavar='"Server 1, Server 2"')
        parser.add_argument('-s', '--headless', default='', help='launch without initializing the UI and enable the Telepath API', action='store_true')
        args = parser.parse_args()

        # Check for debug mode
        constants.debug = args.debug
        constants.headless = args.headless

        # Check for auto-start
        if args.launch:
            constants.generate_server_list()
            server_list = [s.strip() for s in args.launch.split(',')]
            for server in server_list:
                if server.lower() in constants.server_list_lower:
                    server = constants.server_list[constants.server_list_lower.index(server.lower())]
                    constants.boot_launches.append(server)
                else:
                    print(f'--launch: server "{server}" does not exist')
                    sys.exit(-1)

    except AttributeError:
        if constants.debug:
            print("argparse error: failed to process commandline arguments")



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
                print('Closed: auto-mcs is already open')
                sys.exit(10)

        elif constants.os_name == "macos":
            command = f'ps -e | grep .app/Contents/MacOS/{os.path.basename(constants.launch_path)}'
            response = [line for line in constants.run_proc(command, True).strip().splitlines() if command not in line and line]
            if len(response) > 2:
                print('Closed: auto-mcs is already open')
                sys.exit(10)

        # Linux
        else:
            command = f'ps -e | grep {os.path.basename(constants.launch_path)}'
            response = [line for line in constants.run_proc(command, True).strip().splitlines() if command not in line and line]
            if len(response) > 2:
                print('Closed: auto-mcs is already open')
                sys.exit(10)


    # Get default system language
    try:
        if constants.os_name == 'macos':
            system_locale = constants.run_proc("osascript -e 'user locale of (get system info)'", True)
        else:
            from locale import getdefaultlocale
            system_locale = getdefaultlocale()[0]
        if '_' in system_locale:
            system_locale = system_locale.split('_')[0]
        for v in constants.available_locales.values():
            if system_locale.startswith(v['code']):
                constants.locale = v['code']
                break
    except Exception as e:
        print(f'Failed to determine locale: {e}')


    import main


    # Variables
    exitApp = False
    crash = None


    # Get global configuration
    if os.path.exists(constants.global_conf):
        try:
            with open(constants.global_conf, 'r') as f:
                file_contents = constants.json.loads(f.read())
                constants.geometry = file_contents['geometry']
                constants.fullscreen = file_contents['fullscreen']
                constants.locale = file_contents['locale']
                constants.auto_update = file_contents['auto-update']
        except:
            pass


    # Functions
    def app_crash(exception):
        import crashmgr
        log = crashmgr.generate_log(exception)
        crashmgr.launch_window(*log)


    # Main wrapper
    def background():
        global exitApp, crash

        # Check for updates
        constants.check_app_updates()
        constants.search_manager = constants.SearchManager()

        def background_launch(func, *a):
            global exitApp, crash

            if exitApp or crash:
                return

            try:
                func()
            except Exception as e:
                if constants.debug:
                    print(f'Error running {func}: {e}')

        # Find latest game versions and update data cache
        def get_public_ip(*a):
            constants.public_ip = requests.get('https://api.ipify.org').content.decode('utf-8')
        def get_versions(*a):
            constants.find_latest_mc()
            constants.make_update_list()
        background_launch(get_public_ip)
        background_launch(get_versions)
        background_launch(constants.load_addon_cache)
        background_launch(constants.check_data_cache)
        background_launch(constants.search_manager.cache_pages)


        # Update variables in the background
        connect_counter = 0
        while True:

            # Exit this thread if the main thread closes, or crashes
            if exitApp or crash:
                constants.api_manager.stop()
                constants.api_manager.close_sessions()
                break
            else:

                # Check for network changes in the background
                connect_counter += 1
                if (connect_counter == 10 and not constants.app_online) or (connect_counter == 60 and constants.app_online):
                    try:
                        constants.check_app_updates()
                    except Exception as e:
                        if constants.debug:
                            print(e)
                    connect_counter = 0

                time.sleep(1)


    def foreground():
        global exitApp, crash

        # Main thread
        try:
            main.mainLoop()
            exitApp = True

        except SystemExit:
            exitApp = True

        # On crash
        except Exception as e:
            crash = format_exc()
            exitApp = True

            # Use crash handler when app is compiled
            if crash and constants.app_compiled:

                # Destroy init window if macOS
                if constants.os_name == 'macos':
                    init_window.destroy()

                app_crash(crash)

            # Normal Python behavior when testing
            if not constants.app_compiled:
                raise e


    # Launch API before UI
    # Move this to the top, and grab the global config variable "enable_api" to launch here on boot if True
    if constants.api_data['enabled'] or constants.headless:
        constants.api_manager = telepath.WebAPI(constants.api_data['default-host'], constants.api_data['default-port'])
        constants.api_manager.start()


    # Launch/threading logic
    b = threading.Thread(name='background', target=background)
    b.setDaemon(True)

    b.start()
    foreground()
    b.join()


    # Delete live images/temp files on close
    for img in glob.glob(os.path.join(constants.gui_assets, 'live', '*')):
        try:
            os.remove(img)
        except OSError:
            pass
    if not update_log or not os.path.exists(update_log):
        constants.safe_delete(constants.tempDir)
