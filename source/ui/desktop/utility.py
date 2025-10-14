from PIL.ImageFilter import GaussianBlur
from datetime import datetime as dt
from PIL import Image as PILImage
from ctypes import ArgumentError
from typing import TYPE_CHECKING
from plyer import filechooser
from random import randrange
from PIL import ImageEnhance
from pathlib import Path
from glob import glob
import webbrowser
import traceback
import functools
import importlib
import pkgutil
import logging
import inspect
import random
import json
import yaml
import time
import math
import sys
import os
import re


# Kivy imports
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition, FadeTransition


# Local imports
from source.core.server import foundry, manager, amscript, addons, backup, acl
from source.core import constants, telepath, logger, audio
if TYPE_CHECKING: from source.ui.desktop import init
from source.core.constants import paths, dTimer
from source.ui import amseditor, logviewer
from source.core.constants import paths







# UI log wrapper
def send_log(object_data, message, level=None):
    return logger.send_log(f'{__name__}.{object_data}', message, level, 'ui')


# Main application instance
app: 'init.MainApp' = None


# ======================================================================================================================
class AppScreenManager(ScreenManager):
    _initialized:      bool = False
    screen_tree:  list[str] = []

    def previous_screen(self, *args):
        try: self.current = self.screen_tree.pop(-1)
        except IndexError: pass
        # print(screen_manager.screen_tree)

    def initialize(self):
        if not self._initialized:
            self._initialized = True


            # Setup transitions
            self.transition = NoTransition()
            self.transition = FadeTransition(duration=0.115)


            # Recurse and import all files
            base_pkg  = 'source.ui.desktop.views'
            max_depth = 4
            seen      = set()

            for name, is_pkg in constants.walk_namespace(base_pkg, depth=0, max_depth=max_depth):
                if is_pkg: continue
                try: mod = importlib.import_module(name)
                except: continue

                for _, cls in inspect.getmembers(mod, inspect.isclass):
                    if (
                        issubclass(cls, Screen) and
                        cls is not Screen and
                        cls.__name__.endswith('Screen')
                    ):
                        if cls in seen: continue
                        seen.add(cls)

                        try: self.add_widget(cls(name=cls.__name__))
                        except Exception as e: send_log(f"error loading screen '{cls.__name__}': {constants.format_traceback(e)}")

            global ui_loaded; ui_loaded = True
            screen_manager.current = startup_screen

screen_manager = AppScreenManager()


# ======================================================================================================================








# ------------------------------------------------ UI Functions --------------------------------------------------------
# <editor-fold desc="UI Functions">

# Default desktop UI settings
startup_screen:             str = 'MainMenuScreen'
_default_size:  tuple[int, int] = (850, 850)
window_size:    tuple[int, int] = _default_size

# State tracking with back button, previous screens, and previous window size
back_clicked:              bool = False
last_window:    dict[str: list] = {}

# Lock for checking when the desktop UI is fully loaded
ui_loaded:        bool = False

# Animation speed based on refresh rate & multiplier for consistency
refresh_rate:      int = 60
anim_speed:        int = 1

# Global UI banner object, used for persistence when switching pages
global_banner: 'ui.desktop.BannerLayout' = None

# Hide Kivy widgets
def hide_widget(wid, dohide=True, *argies):
    if hasattr(wid, 'saved_attrs'):
        if not dohide:
            wid.height, wid.size_hint_y, wid.opacity, wid.disabled = wid.saved_attrs
            del wid.saved_attrs
    elif dohide:
        wid.saved_attrs = wid.height, wid.size_hint_y, wid.opacity, wid.disabled
        wid.height, wid.size_hint_y, wid.opacity, wid.disabled = 0, None, 0, True

# Retrieves the refresh rate of the display to calculate consistent animation speed
def get_refresh_rate() -> float or None:
    if constants.headless: return
    global refresh_rate, anim_speed

    try:
        if constants.os_name == "windows":
            rate = constants.run_proc('powershell Get-WmiObject win32_videocontroller | findstr "CurrentRefreshRate"', True, log_only_in_debug=True)
            if "CurrentRefreshRate" in rate:
                refresh_rate = round(float(rate.splitlines()[0].split(":")[1].strip()))

        elif constants.os_name == 'macos':
            rate = constants.run_proc('system_profiler SPDisplaysDataType | grep Hz', True, log_only_in_debug=True)
            if "@ " in rate and "Hz" in rate:
                refresh_rate = round(float(re.search(r'(?<=@ ).*(?=Hz)', rate.strip())[0]))

        # Linux
        else:
            rate = constants.run_proc('xrandr | grep "*"', True, log_only_in_debug=True)
            if rate.strip().endswith("*"):
                refresh_rate = round(float(rate.splitlines()[0].strip().split(" ", 1)[1].strip().replace("*","")))

        # Modify animation speed based on refresh rate
        anim_speed = 0.78 + round(refresh_rate * 0.002, 2)
    except: pass

# </editor-fold>


# Control modifier for keyboard shortcuts
control = 'meta' if constants.os_name == "macos" else 'ctrl'


# Check if any servers are running
def check_running(final_func):
    running = constants.server_manager.running_servers

    # Issue stop command to all running servers to quit gracefully
    def close_servers(*args):
        for server in running.values():
            dTimer(0, functools.partial(server.silent_command, "stop")).start()

        if final_func:
            final_func()

    # If there are running servers, prompt user before exiting
    if running:
        server_count = len(list(running.keys()))

        if server_count == 1:
            desc = "There is currently 1 server running. To continue, it will be closed.\n\nAre you sure you want to continue?"
        else:
            desc = f"There are currently ${server_count}$ servers running. To continue, they will be closed.\n\nAre you sure you want to continue?"

        popup = screen_manager.current_screen.popup_widget
        if popup:
            popup.self_destruct(screen_manager.current_screen, False)
            screen_manager.current_screen.canvas.after.clear()

        Clock.schedule_once(
            functools.partial(
                screen_manager.current_screen.show_popup,
                "warning_query",
                f'Server Warning',
                desc,
                (None, close_servers)
            ),
            1 if popup else 0
        )

    # If there aren't running server, execute function normally
    elif final_func:
        final_func()

# Template for any screen
def save_window_pos(*args):
    global last_window

    # Only save position in windowed mode
    if Window.left > 0 and Window.top > 0:
        last_window.update({'pos': [Window.left, Window.top], 'size': Window.system_size})

    constants.app_config.fullscreen = (Window.system_size[0] > (_default_size[0] + 400))
    constants.app_config.geometry   = last_window


def process_ip_text(server_obj=None):

    if server_obj:
        start_text = ''
        if not str(server_obj.port) == '25565' or server_obj.ip:
            if server_obj.ip:
                start_text = server_obj.ip
            if str(server_obj.port) != '25565':
                start_text = start_text + ':' + str(server_obj.port) if start_text else str(server_obj.port)

    else:
        start_text = ''
        if not str(foundry.new_server_info['port']) == '25565' or foundry.new_server_info['ip']:
            if foundry.new_server_info['ip']:
                start_text = foundry.new_server_info['ip']
            if str(foundry.new_server_info['port']) != '25565':
                start_text = start_text + ':' + foundry.new_server_info['port'] if start_text else foundry.new_server_info['port']

    return start_text









# Telepath banner endpoint for sending remote notifications
def telepath_banner(message: str, finished: bool, play_sound=None):
    screen = screen_manager.current_screen

    if screen.show_banner:
        Clock.schedule_once(
            functools.partial(
                screen.show_banner,
                (0.553, 0.902, 0.675, 1) if finished else (0.937, 0.831, 0.62, 1),
                message,
                "checkmark-circle-sharp.png" if finished else "telepath.png",
                3,
                {"center_x": 0.5, "center_y": 0.965},
                play_sound
            ), 0.1
        )

    # Refresh Telepath home screen
    if screen.name == 'TelepathManagerScreen':
        Clock.schedule_once(screen.recalculate_buttons, 0)

    # Refresh user list if visible
    if screen.name == 'TelepathUserScreen' and not screen.popup_widget:
        Clock.schedule_once(lambda *_: screen.gen_search_results(fade_in=False), 0)
constants.telepath_banner = telepath_banner
telepath.create_endpoint(constants.telepath_banner, 'main', True)


# Handle UI logic when telepath session gets disconnected
def telepath_disconnect():
    try:
        # This is handled in MenuBackground.on_pre_enter()
        if constants.server_manager.current_server:
            constants.server_manager.current_server._disconnected = True
    except AttributeError:
        pass
constants.telepath_disconnect = telepath_disconnect

def check_telepath_disconnect():
    sm = constants.server_manager
    server_obj = sm.current_server

    if server_obj:
        telepath_data = server_obj._telepath_data
        if telepath_data:

            # Make a better health check at some point, this is really expensive with latency
            server_obj._check_object_init()
            if server_obj._disconnected:
                sm.current_server = None

                if telepath_data and screen_manager.current_screen.name not in ['MainMenuScreen', 'ServerManagerScreen']:
                    constants.server_manager.refresh_list()
                    screen_manager.current = 'ServerManagerScreen'
                    screen_manager.screen_tree = ['MainMenuScreen']

                server_name = telepath_data['nickname'] if telepath_data['nickname'] else telepath_data['host']
                telepath_banner(f"Lost connection to $'{server_name}'$", False)
                return True

    return False












# Override Kivy widgets for translations
from source.core.translator import *
size_dict = {'down': [], 'up': []}

# Generates manual overrides for string resizing. Run this function with locale changes, and on startup
def size_list(*a):
    scale_up = ['back-ups', 'launch']
    scale_down = ['ADD RULES...', 'QUIT']
    size_dict['up'] = [translate(i).lower() for i in scale_up]
    size_dict['down'] = [translate(i).lower() for i in scale_down]
size_list()

def scale_size(obj, o, n, *a):
    if o and n and obj.__o_size__:
        diff = len(n) - len(o)
        parent_class = obj.parent.__class__.__name__
        new_size = None

        # Ignore on certain screens
        if screen_manager.current.endswith('ProgressScreen') or r'[ref=none]' in obj.text:
            return None

        # Ignore header resizing
        if parent_class not in ('HeaderText'):
            new_size = round(diff * 0.4)

        if new_size:

            # Make text bigger
            if obj.text.strip().lower() in size_dict['up'] or parent_class in ('IconButton'):
                new_size = round(new_size / 2)

            # Make text smaller
            if obj.text.strip().lower() in size_dict['down']:
                new_size = new_size * 2

            # Change popup sizes
            if (screen_manager.current_screen.popup_widget and parent_class == 'RelativeLayout'):
                if screen_manager.current_screen.popup_widget.window_background.width > 500:
                    new_size = round(new_size / 32)
                else:
                    new_size = round(new_size / 5)

            # Set a floor for resize
            if obj.__o_size__ - new_size < obj.__o_size__ - 4:
                new_size = 4

            # Change y-center of Input
            if obj.__class__.__name__.endswith('Input'):
                obj.padding_y = (11 + new_size, 11 + new_size)

            obj.font_size = obj.__o_size__ - new_size
def filter_text(string):
    if isinstance(string, str) and "$" in string:
        return re.sub(r'\$([^\$]+)\$', r'\g<1>', string)
    else:
        return string
class Label(Label):
    def __init__(self, *args, **kwargs):
        self.__translate__ = True
        self.__o_size__ = None
        super().__init__(*args, **kwargs)

    def __setattr__(self, key, value):
        if constants.app_config.locale != 'en':
            if key == 'font_size' and not self.__o_size__:
                self.__o_size__ = value
            if key in ['text'] and isinstance(value, str) and not value.isnumeric() and value.strip() and self.__translate__:
                o = value
                value = translate(value)
                Clock.schedule_once(functools.partial(scale_size, self, o, value), 0)
        elif constants.app_config.locale == 'en' and key in ['text']:
            value = filter_text(value)
        super().__setattr__(key, value)
class Button(Button):
    def __init__(self, *args, **kwargs):
        self.__translate__ = True
        self.__o_size__ = None
        super().__init__(*args, **kwargs)

    def __setattr__(self, key, value):
        if constants.app_config.locale != 'en':
            if key == 'font_size' and not self.__o_size__:
                self.__o_size__ = value
            if key in ['text'] and isinstance(value, str) and not value.isnumeric() and value.strip() and self.__translate__:
                o = value
                value = translate(value)
                Clock.schedule_once(functools.partial(scale_size, self, o, value), 0)
        elif constants.app_config.locale == 'en' and key in ['text']:
            value = filter_text(value)
        super().__setattr__(key, value)
class TextInput(TextInput):
    def __init__(self, *args, **kwargs):
        self.__translate__ = True
        self.__o_size__ = None
        super().__init__(*args, **kwargs)

    def __setattr__(self, key, value):
        if constants.app_config.locale != 'en':
            if key == 'font_size' and not self.__o_size__:
                self.__o_size__ = value
            if key in ['hint_text'] and isinstance(value, str) and not value.isnumeric() and value.strip() and self.__translate__:
                o = value
                value = translate(value)
                Clock.schedule_once(functools.partial(scale_size, self, o, value), 0)
        elif constants.app_config.locale == 'en' and key in ['hint_text']:
            value = filter_text(value)

        if key in ['focus', 'focused']:
            try: super().__setattr__(key, value)
            except: pass
        else:
            super().__setattr__(key, value)








from pypresence import Presence
# Discord rich presence
class DiscordPresenceManager():

    # Internal log wrapper
    def _send_log(self, message: str, level: str = None):
        return send_log(self.__class__.__name__, message, level)

    def __init__(self):
        self.enabled = constants.app_config.discord_presence
        self.presence = None
        self.connected = False
        self.updating_presence = False
        self.splash = constants.session_splash.replace(' ', '')
        self.id = "1293773204552421429"
        self.start_time = 0
        if self.enabled:
            self.start()

    def start(self):
        if not self.connected:
            self.presence = Presence(self.id)
            self.start_time = int(time.time())
            def presence_thread(*a):
                try:
                    self.presence.connect()
                    self.connected = True
                    self._send_log("initialized Discord Presence: successfully connected", 'info')
                except Exception as e:
                    self.presence = None
                    if constants.debug: self._send_log(f"failed to initialize Discord Presence: {constants.format_traceback(e)}", 'error')
            dTimer(0, presence_thread).start()

    def stop(self):
        try:
            if self.connected:
                self.presence.close()
                self.start_time = None
                self.presence = None
                self.connected = False
                self._send_log("stopped Discord Presence: successfully disconnected", 'info')

        except Exception as e:
            if constants.debug: self._send_log(f"failed to stop Discord Presence: {constants.format_traceback(e)}", 'error')

    def get_image(self, file_path: str):
        server_obj = constants.server_manager.current_server
        try:
            if 'rich-presence-icon' in server_obj.run_data:
                return server_obj.run_data['rich-presence-icon']
        except:
            pass

        url = 'https://0x0.st'
        files = {'file': open(file_path, 'rb')}
        response = constants.requests.post(url, files=files, headers={'User-Agent': f'{constants.app_title}/{constants.app_version}'})
        if response.status_code == 200:
            url = response.text.strip()

            # Cache icon for later retrieval
            server_obj.run_data['rich-presence-icon'] = url
            return url
        else:
            self._send_log(f"icon upload to '{url}' failed:\n{response.text}")
            return None

    def update_presence(self, footer_data: str = None):
        if not self.enabled or not self.presence:
            return False

        def do_update(*a):
            self.updating_presence = True
            def update(*a):
                if not self.connected:
                    for x in range(50):
                        if self.connected:
                            break
                        time.sleep(0.2)
                    else:
                        return False

                if footer_data:
                    footer_path = footer_data.replace('$','')
                    overrides = {
                        'splash': ('Main Menu', self.splash)
                    }

                    details = None
                    state = None
                    large = 'https://raw.githubusercontent.com/macarooni-man/auto-mcs/refs/heads/main/source/gui-assets/big-icon.png'

                    # Override for running server
                    if constants.server_manager.current_server and constants.server_manager.current_server.running and screen_manager.current == 'ServerViewScreen':
                        server_obj = constants.server_manager.current_server
                        details = f"Running '{server_obj.name}'"
                        if server_obj._telepath_data:
                            details = f"Telepath - running '{server_obj.name}'"
                        state = f'{server_obj.type.replace("craft", "").title()} {server_obj.version}'

                        # Custom arguments for customization
                        if 'player-list' in server_obj.run_data:
                            current = len([p for p in server_obj.run_data['player-list'].values() if p['logged-in']])
                        else:
                            current = 0

                        if current:
                            args = {'party_size': [int(current), int(server_obj.server_properties['max-players'])]}
                        else:
                            args = {}

                        # Get server icon
                        if server_obj.server_icon:
                            if server_obj._telepath_data:
                                icon_path = manager.get_server_icon(server_obj.name, server_obj._telepath_data)
                            else:
                                icon_path = server_obj.server_icon
                            args['small_image'] = self.get_image(icon_path)
                        else:
                            args['small_image'] = f'https://github.com/macarooni-man/auto-mcs/blob/main/source/gui-assets/icons/big/{server_obj.type}_small.png?raw=true'

                        args['small_text'] = f"{server_obj.name} - {state}"
                        self.presence.update(state=state, details=details, start=self.start_time, large_image=large, **args)

                        return True


                    elif footer_path in overrides:
                        details = overrides[footer_path][0]
                        state = overrides[footer_path][1]


                    elif 'amscript IDE' in footer_path:
                        details, state = footer_path.split(' > ', 1)
                        image = 'https://github.com/macarooni-man/auto-mcs/blob/main/source/gui-assets/amscript-icon.png?raw=true'
                        self.presence.update(state=state, details=details, start=self.start_time, small_image=image, small_text='amscript IDE', large_image=large)

                        return True


                    elif 'Telepath' in footer_path:
                        if ' > ' in footer_path:
                            details, state = footer_path.split(' > ', 1)
                        else:
                            details, state = 'Telepath', self.splash
                        image = 'https://github.com/macarooni-man/auto-mcs/blob/main/source/gui-assets/icons/telepath.png?raw=true'
                        self.presence.update(state=state, details=details, start=self.start_time, small_image=image, small_text='Telepath', large_image=large)

                        return True


                    elif ' > ' in footer_path:
                        details, state = footer_path.split(' > ', 1)
                        if constants.server_manager.current_server and details == 'Server Manager':
                            server_obj = constants.server_manager.current_server
                            if server_obj._telepath_data:
                                details = f"Telepath - '{server_obj.name}'"
                            else:
                                details = f"Server Manager - '{server_obj.name}'"

                    else:
                        details = footer_path
                        state = self.splash


                    if details and state:
                        self.presence.update(state=state, details=details, start=self.start_time, large_image=large)

                else:
                    pass
            update()
            self.updating_presence = False
        if not self.updating_presence:
            dTimer(0, do_update).start()

constants.discord_presence = DiscordPresenceManager()
def toggle_discord_presence(*a):
    if constants.discord_presence.connected or constants.app_config.discord_presence:
        constants.discord_presence.stop()
        banner_text = f"$Discord$ rich presence is now disabled"
        banner_color = (0.937, 0.831, 0.62, 1)
        banner_icon = "discord-strike.png"
        constants.app_config.discord_presence = False

    else:
        constants.discord_presence.start()
        constants.discord_presence.update_presence(constants.footer_path)
        banner_text = f"$Discord$ rich presence is now enabled"
        banner_color = (0.553, 0.902, 0.675, 1)
        banner_icon = "discord.png"
        constants.app_config.discord_presence = True

    Clock.schedule_once(
        functools.partial(
            screen_manager.current_screen.show_banner,
             banner_color,
            banner_text,
            banner_icon,
            2.5,
            {"center_x": 0.5, "center_y": 0.965}
        ), 0
    )








# Helper methods

def icon_path(name):
    return os.path.join(paths.ui_assets, 'icons', name)



# --------------------------------------------------  File chooser  ----------------------------------------------------

# Import tkinter filedialog here for Windows only
if constants.os_name == "windows":
    import tkinter as tk
    from tkinter import filedialog

def file_popup(ask_type, start_dir=paths.user_home, ext=[], input_name=None, select_multiple=False, title=None):
    if not constants.check_free_space():
        return []

    final_path = ""
    file_icon = os.path.join(paths.ui_assets, "small-icon.ico")
    title = translate(title)
    send_log('file_popup', f"requesting {ask_type} popup '{title}'", 'info')

    # Will find the first file start_dir to auto select
    def iter_start_dir(directory):
        end_dir = directory

        for dir_item in glob(os.path.join(start_dir, "*")):
            end_dir = dir_item
            break

        return end_dir

    def linux_warning():
        screen_manager.current_screen.show_popup(
            "warning",
            "No File Provider",
            "auto-mcs was unable to open a file pop-up.\n\nPlease install the package 'zenity' and try again, or input a path to the input manually.",
            None
        )

    # Make sure that ask_type file can dynamically choose between a list and a single file
    if ask_type == "file":
        try:
            final_path = filechooser.open_file(title=title, filters=ext, path=iter_start_dir(start_dir), multiple=select_multiple, icon=file_icon)
            # Ext = [("Comma-separated Values", "*.csv")]
        except:
            if constants.os_name == 'linux':
                linux_warning()

            # Attempt to use a back-up AppleScript solution for macOS
            elif constants.os_name == 'macos':
                ext_list = '", "'.join(ext)
                ext_command = f'of type {{"{ext_list}"}}'.replace('*.','') if ext else ''
                start_path_command = f'with prompt "{title}"' + (f' default location POSIX file "{start_dir}"' if start_dir else '')

                # AppleScript with f-string formatting for dynamically setting parameters
                script = f"osascript -e 'set myFile to choose file {start_path_command} {ext_command}\nPOSIX path of myFile'"
                final_path = [constants.run_proc(script, return_text=True).strip()]

    elif ask_type == "dir":
        if constants.os_name == "windows":
            root = tk.Tk()
            root.withdraw()
            root.iconbitmap(file_icon)
            final_path = filedialog.askdirectory(initialdir=start_dir, title=title)
            Window.raise_window()
        else:
            try:
                final_path = filechooser.choose_dir(path=iter_start_dir(start_dir), title=title, icon=file_icon, multiple=False)
                final_path = final_path[0] if final_path else None

            except:
                if constants.os_name == 'linux':
                    linux_warning()

                # Attempt to use a back-up AppleScript solution for macOS
                elif constants.os_name == 'macos':
                    start_path_command = f'with prompt "{title}"' + (f' default location POSIX file "{start_dir}"' if start_dir else '')

                    # AppleScript with f-string formatting for dynamically setting parameters
                    script = f"    osascript -e 'set myFolder to choose folder {start_path_command}\nPOSIX path of myFolder'"
                    final_path = constants.run_proc(script, return_text=True).strip()
                    if final_path.endswith('User canceled. (-128)'): final_path = []

    # World screen
    if input_name:
        break_loop = False
        for item in screen_manager.current_screen.children:
            if break_loop:
                break
            for child in item.children:
                if break_loop:
                    break
                if child.__class__.__name__ == input_name:
                    if "ServerWorldInput" in input_name:
                        if final_path:
                            child.selected_world = os.path.abspath(final_path)
                            child.update_world()
                    break_loop = True
                    break

    # Import screen
    if input_name:
        break_loop = False
        for child in screen_manager.current_screen.walk():
            if break_loop:
                break
            if child.__class__.__name__ == input_name:
                if input_name.startswith("ServerImport"):
                    if final_path:
                        child.selected_server = os.path.abspath(final_path) if isinstance(final_path, str) else os.path.abspath(final_path[0])
                        child.update_server()
                break_loop = True
                break

    if final_path: send_log('file_popup', f"retrieved user selection from {ask_type} popup '{title}':\n'{final_path}'", 'info')
    else:          send_log('file_popup', f"user cancelled {ask_type} popup '{title}':")

    return final_path

# ----------------------------------------------------------------------------------------------------------------------


# Opens text file with logviewer
def view_file(path: str, title=None):
    data_dict = {
        'app_title': constants.app_title,
        'gui_assets': paths.ui_assets,
        'background_color': constants.background_color,
        'sub_processes': constants.sub_processes,
        'os_name': constants.os_name,
        'translate': translate
    }

    if not title and constants.server_manager.current_server:
        title = constants.server_manager.current_server.name

    send_log('view_file', f"opening in log viewer:\n'{path}'", 'info')

    Clock.schedule_once(
        functools.partial(
            logviewer.open_log,
            title,
            path,
            data_dict
        ), 0.1
    )







# Server Manager Overview ----------------------------------------------------------------------------------------------

# Opens server in panel, and updates Server Manager current_server
def open_server(server_name, wait_page_load=False, show_banner='', ignore_update=True, launch=False, show_readme=None, *args):
    def next_screen(*args):
        different_server = constants.server_manager.current_server.name != server_name
        if different_server:
            while constants.server_manager.current_server.name != server_name:
                time.sleep(0.005)

        if screen_manager.current == 'ServerViewScreen' and different_server:
            screen_manager.current = 'ServerManagerScreen'

        if show_banner: screen_manager.get_screen('ServerViewScreen').server = None
        screen_manager.current = 'ServerViewScreen'

        if launch:
            Clock.schedule_once(screen_manager.current_screen.console_panel.launch_server, 0)

        if show_banner:
            Clock.schedule_once(
                functools.partial(
                    screen_manager.current_screen.show_banner,
                    (0.553, 0.902, 0.675, 1),
                    show_banner,
                    "checkmark-circle-sharp.png",
                    2.5,
                    {"center_x": 0.5, "center_y": 0.965}
                ), 0
            )

        screen_manager.screen_tree = ['MainMenuScreen', 'ServerManagerScreen']

        # If showing readme
        if show_readme:
            Clock.schedule_once(
                functools.partial(screen_manager.current_screen.show_popup, "file", "Author's Notes", show_readme,
                                  (None)),
                1
            )

    constants.server_manager.open_server(server_name)
    server_obj = constants.server_manager.current_server

    needs_update = False
    try:
        if constants.server_manager.update_list:
            needs_update = constants.server_manager.update_list[server_obj.name]['needsUpdate']
    except:
        pass

    # Automatically update if available
    if server_obj.running:
        ignore_update = True
    if server_obj.auto_update == "true" and needs_update and constants.app_online and not ignore_update and constants.check_free_space(
            telepath_data=server_obj._telepath_data):
        while not server_obj.addon:
            time.sleep(0.05)

        if server_obj.is_modpack == 'mrpack':
            if constants.server_manager.update_list[server_obj.name]['updateUrl']:
                foundry.import_data = {
                    'name': server_obj.name,
                    'url': constants.server_manager.update_list[server_obj.name]['updateUrl']
                }
                os.chdir(constants.get_cwd())
                constants.safe_delete(paths.temp)
                screen_manager.current = 'UpdateModpackProgressScreen'
                screen_manager.current_screen.page_contents['launch'] = launch

        else:
            foundry.new_server_init()
            foundry.init_update()
            foundry.new_server_info['type'] = server_obj.type
            foundry.new_server_info['version'] = foundry.latestMC[server_obj.type]
            if server_obj.type in ['forge', 'paper', 'purpur', 'quilt', 'neoforge']:
                foundry.new_server_info['build'] = foundry.latestMC['builds'][server_obj.type]
            screen_manager.current = 'MigrateServerProgressScreen'
            screen_manager.current_screen.page_contents['launch'] = launch

    else:
        Clock.schedule_once(next_screen, 0.8 if wait_page_load else 0)


def open_remote_server(instance, server_name, wait_page_load=False, show_banner='', ignore_update=True, launch=False, show_readme=None, *args):
    def next_screen(*args):
        different_server = constants.server_manager.current_server.name != server_name
        if different_server:
            while constants.server_manager.current_server.name != server_name:
                time.sleep(0.005)

        elif constants.server_manager.current_server:
            constants.server_manager.current_server.reload_config()

        if screen_manager.current == 'ServerViewScreen' and different_server:
            screen_manager.current = 'ServerManagerScreen'

        screen_manager.current = 'ServerViewScreen'

        if launch:
            Clock.schedule_once(screen_manager.current_screen.console_panel.launch_server, 0)

        if show_banner:
            Clock.schedule_once(
                functools.partial(
                    screen_manager.current_screen.show_banner,
                    (0.553, 0.902, 0.675, 1),
                    show_banner,
                    "checkmark-circle-sharp.png",
                    2.5,
                    {"center_x": 0.5, "center_y": 0.965}
                ), 0
            )

        screen_manager.screen_tree = ['MainMenuScreen', 'ServerManagerScreen']

        # If showing readme
        if show_readme:
            Clock.schedule_once(
                functools.partial(screen_manager.current_screen.show_popup, "file", "Author's Notes", show_readme,
                                  (None)),
                1
            )

    remote_obj = constants.api_manager.request(
        endpoint=f'/main/open_remote_server?name={constants.quote(server_name)}',
        host=instance['host'],
        port=instance['port'],
        args={'none': None}
    )

    if remote_obj:
        telepath_data = {'name': server_name, 'host': instance['host'], 'port': instance['port'],
                         'nickname': instance['nickname']}
        constants.server_manager._init_telepathy(telepath_data)
        server_obj = constants.server_manager.current_server
        update_list = constants.get_remote_var('server_manager.update_list', telepath_data)

        needs_update = False
        try:
            if update_list:
                needs_update = update_list[server_obj.name]['needsUpdate'] == 'true'
        except:
            pass

        # Automatically update if available
        if server_obj.running:
            ignore_update = True
        if server_obj.auto_update == "true" and needs_update and constants.app_online and not ignore_update and constants.check_free_space(
                telepath_data=server_obj._telepath_data):
            while not server_obj.addon:
                time.sleep(0.05)

            if server_obj.is_modpack == 'mrpack':
                if update_list[server_obj.name]['updateUrl']:
                    foundry.import_data = {
                        'name': server_obj.name,
                        'url': update_list[server_obj.name]['updateUrl']
                    }
                    os.chdir(constants.get_cwd())
                    constants.safe_delete(paths.temp)
                    screen_manager.current = 'UpdateModpackProgressScreen'
                    screen_manager.current_screen.page_contents['launch'] = launch

            else:
                foundry.new_server_init()
                foundry.init_update()
                foundry.new_server_info['type'] = server_obj.type
                foundry.new_server_info['version'] = foundry.latestMC[server_obj.type]
                if server_obj.type in ['forge', 'paper', 'purpur', 'quilt', 'neoforge']:
                    foundry.new_server_info['build'] = foundry.latestMC['builds'][server_obj.type]
                screen_manager.current = 'MigrateServerProgressScreen'
                screen_manager.current_screen.page_contents['launch'] = launch

        else:
            telepath_data = {'name': server_name, 'host': instance['host'], 'port': instance['port'],
                             'nickname': instance['nickname']}
            constants.server_manager._init_telepathy(telepath_data)
            Clock.schedule_once(next_screen, 0.8 if wait_page_load else 0)

    return remote_obj


def disk_popup(go_to='back', telepath_data=None):
    if not constants.check_free_space(telepath_data=telepath_data):
        def go_back(*a):
            global back_clicked
            back_clicked = True
            if go_to == 'back': screen_manager.previous_screen()
            else:               screen_manager.current = go_to
            back_clicked = False

        def disk_error(*_):
            screen_manager.current_screen.show_popup(
                "warning",
                "Storage Error",
                f"auto-mcs has limited functionality from low disk space. Further changes can lead to corruption in your servers.\n\nPlease free up space on {'this $Telepath$ instance' if telepath_data else 'your disk'} to continue",
                go_back
            )

        Clock.schedule_once(disk_error, 0)
        return True


def telepath_popup(go_to='back'):
    if constants.telepath_busy():
        def go_back(*a):
            global back_clicked
            back_clicked = True
            if go_to == 'back': screen_manager.previous_screen()
            else:               screen_manager.current = go_to
            back_clicked = False

        def telepath_error(*_):
            screen_manager.current_screen.show_popup(
                "warning",
                "Telepath Error",
                "A critical operation is currently running through a $Telepath$ session.\n\nPlease try again later",
                go_back
            )

        Clock.schedule_once(telepath_error, 0)
        return True


def refresh_ips(server_name):
    def _schedule(*a):
        screen = screen_manager.current_screen
        if "ServerViewScreen" in screen.name:
            if screen.server.name == server_name:
                screen.server_button.update_subtitle(screen.server.run_data)
    Clock.schedule_once(_schedule, 0)


manager.refresh_ips = refresh_ips
