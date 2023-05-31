# Local imports
from svrmgr import ServerManager
import constants


# Run app, eventually in wrapper

def mainLoop():
    # Fixes display scaling on Windows - Eventually add this to the beginning of wrapper.py
    if constants.os_name == "windows":
        from ctypes import windll, c_int64
        windll.user32.SetProcessDpiAwarenessContext(c_int64(-4))

    # Cleanup temp files and generate splash text
    from menu import run_application
    constants.cleanup_old_files()
    constants.generate_splash()

    # Instantiate Server Manager
    constants.server_manager = ServerManager()
    print("Current server_list: ", constants.server_manager.server_list)

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
#                                                                menu.py <───┘
#
#   < Functional Tests >
#   
#   - Windows 10 1909, 20H2, 21H2
#   - Windows 11 22H2
#   - Manjaro KDE 2022 - 5.10, 5.16
#   - Manjaro XFCE 2019 - 5.4.6
#   - Manjaro XFCE 2022 - 5.15.8  //No file dialog, requires installation of Zenity
#   - Kali Linux 2022 - 5.15
#   - Ubuntu 22.04.1 Desktop (Wayland, X11) - 5.15
#   - Ubuntu 18.04 Desktop - 5.0
#   - Fedora 22 Workstation - 4.0
#   - PopOS 22.04 - 5.19
#   - Linux Mint 21 MATE - 5.15
#   - Garuda KDE Lite - 5.19.7
#   - Garuda Wayfire - 5.19.7  //Issues with YAD not displaying file dialog
#   - Garuda i3 - 5.19.7       //Issues with YAD not displaying file dialog
#   - SteamOS Holo - 5.13
#
# ----------------------------------------------------------------------------------------------
