from source.core.server.svrmgr import ServerManager
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



# ----------------------------------------------------------------------------------------------
#                             _
#                  __ _ _   _| |_ ___                   < Module execution chain >
#   ▄▄██████▄▄    / _` | | | | __/ _ \          
#  ████████████  | (_| | |_| | || (_) |        -- Root: wrapper.py <─────────┐
# ████▀▀██▀▀████  \__,_|\__,_|\__\___/                   ┆      ┆            │
# ████▄▄▀▀▄▄████   _ __ ___   ___ ___            (bg thread)  (fg thread)    │
# █████    █████  | '_ ` _ \ / __/ __|                ┆            ┆         ├── constants.py
#  ████▄██▄████   | | | | | | (__\__ \          crash-handler    main.py <───┤
#   ▀▀██████▀▀    |_| |_| |_|\___|___/                             ┆         │
#                                                  headless.py / menu.py <───┘
#
#   < Functional Tests >
#   
#   - Windows 10 1909, 20H2, 21H2
#   - Windows 11 22H2
#   - macOS Monterey (Intel, 12.7.3)
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
