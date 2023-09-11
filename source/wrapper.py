from platform import platform, architecture
from traceback import format_exc
from operator import itemgetter
from bs4 import BeautifulSoup
import urllib.error
import threading
import requests
import datetime
import textwrap
import hashlib
import psutil
import signal
import glob
import json
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
    multiprocessing.freeze_support()

    # Import constants and check for debug mode
    import constants

    if "--debug" in sys.argv:
        constants.debug = True
    import main


    # Variables
    exitApp = False
    currentDir = os.path.abspath(os.curdir)


    # Functions
    def app_crash(exception):
        # Remove file paths from exception
        trimmed_exception = []
        skip = False
        exception_lines = exception.splitlines()
        for item in exception_lines:

            if skip is True or "Traceback" in item:
                skip = False
                continue

            if "File \"C:\\" in item:
                indent = item.split("File \"", 1)[0]
                eol = "," + item.split(",", 1)[1]
                lib_path = ""

                if "Python\\Python" in item:
                    file = item.split("File \"", 1)[1].split("\"")[0]
                    file = os.path.basename("C:\\" + file)
                    lib_path = item.split("lib\\", 1)[1].split(file)[0]

                else:
                    file = item.split("File \"", 1)[1].split("\"")[0]
                    file = os.path.basename("C:\\" + file)

                line = indent + f"File \"{lib_path}{file}\""
                skip = True

            else:
                line = item.split(",")[0]

            if "File" in line:
                line += "," + item.split(",")[2]

            trimmed_exception.append(line)

        trimmed_exception = "\n".join(trimmed_exception[-2:])

        # Create AME code
        path = " > ".join(constants.footer_path) if isinstance(constants.footer_path, list) else constants.footer_path
        ame = (hashlib.shake_128(path.encode()).hexdigest(1) if path else "00") + "-" + hashlib.shake_128(trimmed_exception.encode()).hexdigest(3)

        # Check for 'Logs' folder in application directory
        # If it doesn't exist, create a new folder called 'Logs'
        log_dir = os.path.join(constants.applicationFolder, "Logs")

        # Timestamp
        time_stamp = datetime.datetime.now().strftime("%#H-%M-%S_%#m-%#d-%y")
        time_formatted = datetime.datetime.now().strftime("%#I:%M:%S %p  %#m/%#d/%Y")

        # Header
        header = f'Auto-MCS Exception:    {ame}  '

        if not os.path.isdir(log_dir):
            os.makedirs(log_dir)

        cpu_arch = architecture()
        if len(cpu_arch) > 1:
            cpu_arch = cpu_arch[0]

        log = f"""{'=' * (42 * 3)}
    {"||" + (' ' * round((42 * 1.5) - (len(header) / 2) - 1)) + header + (' ' * round((42 * 1.5) - (len(header)) + 14)) + "||"}
    {'=' * (42 * 3)}
    
    
    General Info:
    
        Version:           {constants.app_version} - {constants.os_name.title()} ({platform()})
        Online:            {constants.app_online}
        Sub-servers:       {len(constants.sub_servers) if constants.sub_servers else "None"}
        ngrok:             {"Inactive" if constants.ngrok_ip == "" else "Active"}
    
        Processor info:    {psutil.cpu_count(False)} ({psutil.cpu_count()}) C/T @ {round((psutil.cpu_freq().max) / 1000, 2)} GHz ({cpu_arch})
        System memory:     {round(psutil.virtual_memory().total / 1073741824)} GB
    
    
    
    Time of AME:
    
    {textwrap.indent(time_formatted, "    ")}
    
    
    
    Application path at time of AME:
    
    {textwrap.indent(path, "    ")}
    
    
    
    AME traceback:
    
    {textwrap.indent(exception, "    ")}"""

        with open(os.path.abspath(os.path.join(log_dir, f"ame-fatal_{time_stamp}.log")), "w") as log_file:
            log_file.write(log)

        # Remove old logs
        keep = 50

        fileData = {}
        for file in glob.glob(os.path.join(log_dir, "ame-fatal*.log")):
            fileData[file] = os.stat(file).st_mtime

        sortedFiles = sorted(fileData.items(), key=itemgetter(1))

        delete = len(sortedFiles) - keep
        for x in range(0, delete):
            os.remove(sortedFiles[x][0])


        # f"Uh oh, it appears that Auto-MCS has crashed."
        # f"   Auto-MCS: Crash"
        # f" AME code:  {ame}\n\n\n"
        # buttons.append("Restart Auto-MCS")
        # buttons.append("Open crash log")
        # buttons.append("Quit...")
        # main.footer_text = ['Auto-MCS Crash']

    #     if "Open crash log":
    #         latest_file = max(glob.glob(log_dir + "\\*"), key=os.path.getctime)
    #         Popen(f"notepad.exe \"{os.path.abspath(latest_file)}\"")
    #
    #     elif "Restart":
    #         exeName = os.path.basename(sys.executable)  # if this breaks, change exeName back to fileName
    #
    #         myBat = open(f'{log_dir}\\auto-mcs-reboot.bat', 'w+')
    #
    #         if getattr(sys, 'frozen', False):  # Running as compiled
    #             myBat.write(f"""taskkill /f /im \"{exeName}\"
    #
    # cd \"{currentDir}\"
    # start \"\" \"{exeName}\"
    #
    # del \"{log_dir}\\auto-mcs-reboot.bat\"""")
    #
    #             else:
    #                 myBat.write(f"""taskkill /f /im \"{exeName}\"
    #
    # cd \"{currentDir}\"
    # start \"\" cmd /c \"Launch.bat\"
    #
    # del \"{log_dir}\\auto-mcs-reboot.bat\"""")
    #
    #             myBat.close()
    #             os.chdir(log_dir)
    #             os.system("start /b cmd \"\" /C auto-mcs-reboot.bat > nul 2>&1")
    #             b.join()
    #             f.join()
    #             sys.exit()
    #
    #         elif "Quit..." in buttonClicked:
    #             break


    # Main wrapper
    def background():
        global exitApp

        constants.check_app_updates()
        # Before background loop starts

        try:

            # Find latest game versions and update data cache
            constants.check_data_cache()

            constants.find_latest_mc()

            constants.make_update_list()

            main.publicIP = requests.get('https://api.ipify.org').content.decode('utf-8')

        except requests.HTTPError or TimeoutError or urllib.error.URLError as e:
            if constants.debug:
                print(e)

        # Background loop if needed
        while True:

            # Put things here to update variables in the background
            # constants.variable = x

            if exitApp is True:
                break
            else:
                time.sleep(1)


    def foreground():
        global exitApp

        # Main thread
        while exitApp is False:

            try:
                main.mainLoop()

            except SystemExit:
                if constants.sub_processes:
                    for pid in constants.sub_processes:
                        try:
                            if constants.os_name == "windows":
                                os.kill(pid, signal.SIGTERM)
                            else:
                                os.kill(pid, signal.SIGKILL)
                        except PermissionError:
                            continue

                exitApp = True


            # On crash
            # except Exception as e:
            #     f.exception = e
            #     app_crash(format_exc())


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
