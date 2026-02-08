from source.ui.headless.utility import *
from source.ui.headless import utility


# Suppress warnings from interfering with the UI
import warnings
warnings.filterwarnings('ignore')



# ---------------------------------------------------- Launch UI -------------------------------------------------------

def run_application():
    from source.core import logger

    send_log('run_application', 'initializing headless UI (urwid)', 'info')

    # Raise an interactive warning if elevated, but bypassed
    if (constants.is_admin() and not constants.is_docker) and constants.bypass_admin_warning:
        print(f"\n\033[31m> Privilege Warning:  Running auto-mcs as {'administrator' if constants.os_name == 'windows' else 'root'} can expose your system to security vulnerabilities\n\nProceed with caution, this configuration is unsupported\033[0m\n\n< press 'ENTER' to continue >")
        null = input()

    # Raise an error if elevated
    elif (constants.is_admin() and not constants.is_docker) and not constants.bypass_admin_warning:
        print(f"\n\033[31m> Privilege Error:  Running auto-mcs as {'administrator' if constants.os_name == 'windows' else 'root'} can expose your system to security vulnerabilities\n\nPlease restart with standard user privileges to continue\033[0m")
        return False


    # Launch servers if requested with the flag
    for server in constants.boot_launches:
        print(f"\n> Launching '{server}', please wait...")

        def callback(success: bool, message: str): print(message)
        constants.server_manager._gabage_handler(callback)

        print('+ Done!')


    try:
        # Disable STDOUT
        logger.enable_printing = False
        if constants.os_name == 'windows':
            old_std_err = sys.stderr
            sys.stderr = NullWriter()
        else:
            old_std_out = sys.stdout
            sys.stdout = NullWriter()


        # Run UI (and store potential exception for later)
        runtime_error: Exception | None = None
        try: screen_manager._loop.run()
        except Exception as e: runtime_error = e


        # Enable STDOUT
        logger.enable_printing = True
        if constants.os_name == 'windows': sys.stderr = old_std_err
        else:                              sys.stdout = old_std_out

        # Stop all running servers
        for server in [s for s in constants.server_manager.running_servers.values()]:
            if server.running:
                print(f"\n> Stopping '{server.name}', please wait...")
                server.stop()
                while server.running:
                    time.sleep(0.5)
                print('+ Done!')


        # Only raise error after normal STDIO is restored
        if runtime_error: raise runtime_error

    # Close gracefully on CTRL-C
    except KeyboardInterrupt:
        pass
