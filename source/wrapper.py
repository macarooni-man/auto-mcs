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

    # allocs, gen1, gen2 = gc.get_threshold()
    # allocs = 50_000
    # gen1 = gen1 * 2
    # gen2 = gen2 * 2
    # gc.set_threshold(allocs, gen1, gen2)


    import multiprocessing
    multiprocessing.set_start_method("spawn")
    multiprocessing.freeze_support()


    # Import constants and set variables
    import constants
    constants.launch_path = sys.executable if constants.app_compiled else __file__
    try:
        constants.username = constants.run_proc('whoami', True).split('\\')[-1].strip()
    except:
        pass

    if constants.app_compiled:
        os.environ["KIVY_NO_CONSOLELOG"] = "1"

    # Check for update log
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
        parser.add_argument('-d', '--debug', default='',help='execute auto-mcs with verbose console logging', action='store_true')
        parser.add_argument('-l', '--launch', type=str, default='', help='specify a server name (or list of server names) to launch automatically', metavar='"Server 1, Server 2"')
        args = parser.parse_args()

        # Check for debug mode
        constants.debug = args.debug

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



    # Check if application is already open
    if constants.os_name == "windows":
        command = f'tasklist | findstr {os.path.basename(constants.launch_path)}'
        response = [line for line in constants.run_proc(command, True).strip().splitlines() if ((command not in line) and ('tasklist' not in line) and (line.endswith(' K')))]
        print(response)
        if len(response) > 2:
            user32 = ctypes.WinDLL('user32')
            if hwnd := user32.FindWindowW(None, constants.app_title):
                if not user32.IsZoomed(hwnd):
                    user32.ShowWindow(hwnd, 1)
                user32.SetForegroundWindow(hwnd)
            sys.exit()
    # Linux
    else:
        command = f'ps -e | grep {os.path.basename(constants.launch_path)}'
        response = [line for line in constants.run_proc(command, True).strip().splitlines() if command not in line and line]
        if len(response) > 2:
            sys.exit()

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


        # Find latest game versions and update data cache
        try:
            constants.load_addon_cache()
        except Exception as e:
            if constants.debug:
                print(e)

        try:
            constants.find_latest_mc()
        except Exception as e:
            if constants.debug:
                print(e)

        try:
            constants.check_data_cache()
        except Exception as e:
            if constants.debug:
                print(e)

        try:
            constants.make_update_list()
        except Exception as e:
            if constants.debug:
                print(e)

        try:
            constants.public_ip = requests.get('https://api.ipify.org').content.decode('utf-8')
        except Exception as e:
            if constants.debug:
                print(e)

        # Background loop if needed
        connect_counter = 0
        while True:
            # Put things here to update variables in the background
            # constants.variable = x
            if exitApp or crash:
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
            f.exception = e
            crash = format_exc()
            exitApp = True

            # Use crash handler when app is compiled
            if crash and constants.app_compiled:
                app_crash(crash)

            # Normal Python behavior when testing
            if not constants.app_compiled:
                raise e


    b = threading.Thread(name='background', target=background)
    f = threading.Thread(name='foreground', target=foreground)
    f.setDaemon(False)
    b.setDaemon(True)

    b.start()
    f.start()

    try:
        b.join()
        f.join()
    except KeyboardInterrupt:
        sys.exit()

    # Delete live images/temp files on close
    for img in glob.glob(os.path.join(constants.gui_assets, 'live', '*')):
        try:
            os.remove(img)
        except OSError:
            pass
    if not os.path.exists(update_log):
        constants.safe_delete(constants.tempDir)
