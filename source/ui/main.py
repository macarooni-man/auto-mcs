from source.core.server.manager import ServerManager
from source.core import constants


# Logging wrapper
def send_log(object_data, message, level=None):
    return constants.send_log(f'{__name__}.{object_data}', message, level, 'ui')


# Run app, eventually in wrapper
def ui_loop():

    # Fixes display scaling on Windows - Eventually add this to the beginning of wrapper.py
    if constants.os_name == "windows" and not constants.headless:
        from ctypes import windll, c_int64
        send_log('ui_loop', f'setting DPI context before launching GUI')

        # Calculate screen width and disable DPI scaling if bigger than a certain resolution
        try:
            width = windll.user32.GetSystemMetrics(0)
            scale = windll.shcore.GetScaleFactorForDevice(0) / 100
            if (width * scale) < 2000: windll.user32.SetProcessDpiAwarenessContext(c_int64(-4))
        except Exception as e:
            send_log('ui_loop', f'error setting DPI context:\n{constants.format_traceback(e)}')


    # Cleanup temp files and generate splash text
    constants.cleanup_old_files()
    constants.generate_splash()
    constants.get_refresh_rate()

    # Instantiate Server Manager
    constants.server_manager = ServerManager()

    # If no local servers and Telepath connections, attempt to check those first
    if not constants.server_list_lower and constants.server_manager.telepath_servers:
        constants.server_manager.check_telepath_servers()

    # Initialize boot log
    constants.send_boot_log(f'{__name__}.ui_loop')


    # Only start the GUI if not headless
    if not constants.headless:
        from source.ui.desktop import run_application

    # Otherwise, start a loop for a CLI interpreter with basic commands
    else:
        from source.ui.headless import run_application

    run_application()
