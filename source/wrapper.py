from traceback import format_exc
import urllib.error
import threading
import requests
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

    # Import constants and check for debug mode
    import constants
    constants.launch_path = sys.executable if constants.app_compiled else __file__


    if "--debug" in sys.argv:
        constants.debug = True
    import main


    # Variables
    exitApp = False
    crash = None


    # Functions
    def app_crash(exception):
        import crashmgr
        log = crashmgr.generate_log(exception)
        crashmgr.launch_window(*log)


    # Main wrapper
    def background():
        global exitApp

        constants.check_app_updates()
        # Before background loop starts

        try:

            # Find latest game versions and update data cache
            constants.find_latest_mc()

            constants.check_data_cache()

            constants.make_update_list()

            main.publicIP = requests.get('https://api.ipify.org').content.decode('utf-8')

        except requests.HTTPError or TimeoutError or urllib.error.URLError as e:
            if constants.debug:
                print(e)

        # Background loop if needed
        while True:

            # Put things here to update variables in the background
            # constants.variable = x
            if crash:
                app_crash(crash)

            if exitApp is True or crash:
                break
            else:
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
    constants.safe_delete(constants.tempDir)
