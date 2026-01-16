from urllib.parse import urlparse, unquote
from PIL.ImageFilter import GaussianBlur
from datetime import datetime as dt
from PIL import Image as PILImage
from ctypes import ArgumentError
from typing import TYPE_CHECKING
from pypresence import Presence
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
import queue
import shlex
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
from source.core.constants import paths, dTimer
from source.ui import amseditor, logviewer
from source.core.constants import paths
from source.core.translator import *

if TYPE_CHECKING:
    from source.ui.desktop.widgets import banners
    from source.ui.desktop import init


# -------------------------------------------- Global UI Variables -----------------------------------------------------

# Default desktop UI settings
startup_screen:             str = 'MainMenuScreen'
_default_size:  tuple[int, int] = (850, 850)
window_size:    tuple[int, int] = _default_size

# State tracking with back button, previous screens, and previous window size
back_clicked:              bool = False
last_window:    dict[str, list] = {}

# Lock for checking when the desktop UI is fully loaded
ui_loaded:                 bool = False

# Animation speed based on refresh rate & multiplier for consistency
refresh_rate:               int = 60
anim_speed:                 int = 1

# Cross-platform "Control" modifier key for keyboard shortcuts
control:  str = 'meta' if constants.os_name == "macos" else 'ctrl'

# Global UI banner object, used for persistence when switching pages
global_banner:  'banners.BannerLayout' = None

# Global desktop UI application instance
app:            'init.MainApp'

# Global desktop UI screen manager instance
screen_manager: 'AppScreenManager'



# --------------------------------------------- General Functions ------------------------------------------------------

# UI log wrapper
def send_log(object_data, message, level=None):
    return logger.send_log(f'{__name__}.{object_data}', message, level, 'ui')



# ------------------------------------------- Global Screen Manager ----------------------------------------------------

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


            # Recurse & import all view *Screen classes to load into memory
            base_pkg = 'source.ui.desktop.views'
            max_depth = 6

            pkg = importlib.import_module(base_pkg)
            base_depth = base_pkg.count('.')
            stack = [(base_pkg, list(getattr(pkg, '__path__', [])))]
            seen_mods = {base_pkg}
            seen_cls = set()


            # Collect child views once: {name: is_pkg}
            while stack:
                pkg_name, pkg_paths = stack.pop()

                children = {}
                for _, name, is_pkg in pkgutil.iter_modules(pkg_paths, pkg_name + '.'):
                    if (name.count('.') - base_depth) <= max_depth and name not in seen_mods: children[name] = is_pkg

                for root in pkg_paths:
                    try:
                        with os.scandir(root) as it:
                            for e in it:
                                if e.name.startswith(('.', '_')): continue
                                if e.is_dir():
                                    sub = f'{pkg_name}.{e.name}'
                                    if (
                                        (sub.count('.') - base_depth) <= max_depth and
                                        sub not in seen_mods and
                                        importlib.util.find_spec(sub) is not None
                                    ):
                                        children.setdefault(sub, True)

                                elif e.is_file() and e.name.endswith('.py'):
                                    mod = f'{pkg_name}.{e.name[:-3]}'
                                    if (mod.count('.') - base_depth) <= max_depth: children.setdefault(mod, False)

                    except FileNotFoundError: pass


                # Recurse into subpackages, import modules and retrieve classes
                for name, is_pkg in children.items():
                    seen_mods.add(name)
                    if is_pkg:
                        try:
                            sub = importlib.import_module(name)
                            paths = list(getattr(sub, '__path__', []))
                            if paths: stack.append((name, paths))
                        except: pass
                        continue

                    try: mod = importlib.import_module(name)
                    except: continue


                    # Add to screen list if it's not a duplicate, and definitely a Screen derivative
                    for _, cls in inspect.getmembers(mod, inspect.isclass):
                        if (
                            issubclass(cls, Screen) and
                            cls is not Screen and
                            cls.__name__.endswith('Screen') and
                            cls not in seen_cls
                        ):
                            seen_cls.add(cls)
                            try: self.add_widget(cls(name=cls.__name__))
                            except Exception as e: send_log(f"error loading screen '{cls.__name__}': {constants.format_traceback(e)}", 'error')

            global ui_loaded; ui_loaded = True
            screen_manager.current = startup_screen

screen_manager = AppScreenManager()



# ------------------------------------- Discord Rich Presence functionality --------------------------------------------

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
        self.start_time = int(time.time())

        # Queue logic to prevent frequent updates
        # - Discord's API rate limit is '1/15'
        self._last_update:        dict = None
        self._update_interval:     int = 15
        self._pending_worker:   dTimer = None
        self._last_update_time: dt.now = None

        if self.enabled: self.start()

    # Retrieves the current running server image
    def _get_image(self, file_path: str):
        server_obj = constants.server_manager.current_server
        try:
            if 'rich-presence-icon' in server_obj.run_data: return server_obj.run_data['rich-presence-icon']
        except: pass

        with open(file_path, 'rb') as fb:
            url = 'https://0x0.st'
            files = {'file': fb}
            response = constants.requests.post(url, files=files, headers={'User-Agent': f'{constants.app_title}/{constants.app_version}'})
            if response.status_code == 200:
                url = response.text.strip()

                # Cache icon for later retrieval
                server_obj.run_data['rich-presence-icon'] = url
                return url

            # Something went wrong
            else:
                self._send_log(f"icon upload to '{url}' failed:\n{response.text}")
                return None

    # Publishes the data to the client through a buffer using 'self._worker'
    def _send_update(self, **kwargs):
        if self.connected:

            # Throttle updates if they are too frequent
            try:
                self._last_update = kwargs

                # The worker will pull the latest 'self._last_update' anyway
                if self._pending_worker: return

                if self._last_update_time: elapsed = abs((dt.now() - self._last_update_time).total_seconds())
                else:                      elapsed = self._update_interval

                if elapsed >= self._update_interval:
                    return self._worker()

                self._pending_worker = dTimer(
                    round(max(min(self._update_interval - elapsed, self._update_interval), 0)),
                    self._worker
                )
                self._pending_worker.start()

            except Exception as e:
                if constants.debug: self._send_log(f'error updating Discord presence: {constants.format_traceback(e)}', 'error')

    # Run the update actual update
    def _worker(self):
        if not self._last_update or not self.enabled: return

        # Safely snapshot presence and connection state
        presence_ref = self.presence
        if not (self.connected and presence_ref):
            for x in range(50):
                if self.connected and self.presence:
                    presence_ref = self.presence
                    break
                time.sleep(0.2)
            else: return False

        if self.connected and presence_ref:

            # Ensure timer cleanup even if update raises
            pw = self._pending_worker
            self._pending_worker = None

            try:
                presence_ref.update(**self._last_update)
                self._last_update_time = dt.now()

            except Exception as e:
                if constants.debug: self._send_log(f'error updating Discord presence: {constants.format_traceback(e)}','error')

            if pw:
                try: pw.cancel()
                except: pass



    # Starts the connection to Discord's servers
    def start(self):
        if not self.connected:
            if self.presence: self.stop()

            self.presence = Presence(self.id)
            def presence_thread(*a):
                try:
                    self.presence.connect()
                    self.connected = True
                    self._send_log("initialized Discord Presence: successfully connected", 'info')
                except Exception as e:
                    self.presence = None
                    if constants.debug: self._send_log(f"failed to initialize Discord Presence: {constants.format_traceback(e)}", 'error')
            dTimer(0, presence_thread).start()

    # Stops the connection to Discord's servers
    def stop(self):
        try:
            if self.connected:
                self.presence.close()
                self.presence = None
                self.connected = False

                # Cancel pending worker if scheduled
                pw = self._pending_worker
                self._pending_worker = None
                if pw:
                    try: pw.cancel()
                    except: pass

                self._send_log("stopped Discord Presence: successfully disconnected", 'info')

        except Exception as e:
            if constants.debug: self._send_log(f"failed to stop Discord Presence: {constants.format_traceback(e)}", 'error')

    # Updates the client status message
    def update_presence(self, footer_data: str = None):
        if not self.enabled or not self.presence:
            return False

        def do_update(*a):
            def _update(*a):
                assets_url = f'https://github.com/macarooni-man/auto-mcs/blob/main/source/ui/assets'

                if footer_data:
                    footer_path = footer_data.replace('$','')

                    # Content overrides (display this content instead in Discord per page)
                    overrides = {
                        'splash': ('Main Menu', self.splash)
                    }

                    details = None
                    state = None
                    large = f'{assets_url}/big-icon.png'

                    # Override for running server
                    if constants.server_manager.current_server and constants.server_manager.current_server.running and screen_manager.current == 'ServerViewScreen':
                        server_obj = constants.server_manager.current_server
                        details = f"Running '{server_obj.name}'"
                        if server_obj._telepath_data: details = f"Telepath - running '{server_obj.name}'"
                        state = f'{server_obj.type.replace("craft", "").title()} {server_obj.version}'

                        # Custom arguments for customization
                        if 'player-list' in server_obj.run_data: current = len([p for p in server_obj.run_data['player-list'].values() if p['logged-in']])
                        else:                                    current = 0

                        if current: args = {'party_size': [int(current), int(server_obj.server_properties['max-players'])]}
                        else:       args = {}

                        # Get server icon
                        if server_obj.server_icon:
                            if server_obj._telepath_data: icon_path = manager.get_server_icon(server_obj.name, server_obj._telepath_data)
                            else:                         icon_path = server_obj.server_icon
                            args['small_image'] = self._get_image(icon_path)
                        else: args['small_image'] = f'{assets_url}/icons/big/{server_obj.type}_small.png?raw=true'

                        args['small_text'] = f"{server_obj.name} - {state}"

                        # Safe update (presence may have been cleared by stop())
                        self._send_update(state=state, details=details, start=self.start_time, large_image=large, **args)
                        return True


                    elif footer_path in overrides:
                        details = overrides[footer_path][0]
                        state = overrides[footer_path][1]


                    elif 'amscript IDE' in footer_path:
                        details, state = footer_path.split(' > ', 1)
                        image = f'{assets_url}/amscript-icon.png?raw=true'
                        self._send_update(state=state, details=details, start=self.start_time, small_image=image, small_text='amscript IDE', large_image=large)
                        return True


                    elif 'Telepath' in footer_path:
                        if ' > ' in footer_path: details, state = footer_path.split(' > ', 1)
                        else:                    details, state = 'Telepath', self.splash
                        image = f'{assets_url}/icons/telepath.png?raw=true'
                        self._send_update(state=state, details=details, start=self.start_time, small_image=image, small_text='Telepath', large_image=large)
                        return True


                    elif ' > ' in footer_path:
                        details, state = footer_path.split(' > ', 1)
                        if constants.server_manager.current_server and details == 'Server Manager':
                            server_obj = constants.server_manager.current_server
                            if server_obj._telepath_data: details = f"Telepath - '{server_obj.name}'"
                            else:                         details = f"Server Manager - '{server_obj.name}'"

                    else:
                        details = footer_path
                        state = self.splash


                    if details and state:
                        self._send_update(state=state, details=details, start=self.start_time, large_image=large)

                else: pass

            try: _update()
            except Exception as e:
                if constants.debug: self._send_log(f'error updating Discord presence: {constants.format_traceback(e)}', 'error')

            # Always reset even if an exception occurred
            finally: self.updating_presence = False

        # Thread-safe check to prevent overlap
        if not self.updating_presence:
            self.updating_presence = True
            dTimer(0, do_update).start()

    # Automates the start/stop process with config persistence
    def toggle_presence(self, *a):

        # Stop presence if it's enabled
        if self.connected or constants.app_config.discord_presence:
            self.stop()
            banner_text = f"$Discord$ rich presence is now disabled"
            banner_color = (0.937, 0.831, 0.62, 1)
            banner_icon = "discord-strike.png"
            constants.app_config.discord_presence = False

        # Start presence if it's disabled
        else:
            self.start()
            self.update_presence(constants.footer_path)
            banner_text = f"$Discord$ rich presence is now enabled"
            banner_color = (0.553, 0.902, 0.675, 1)
            banner_icon = "discord.png"
            constants.app_config.discord_presence = True

        # Show banner in the UI
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

constants.discord_presence = DiscordPresenceManager()



# ----------------------------------------- Translation Kivy Overrides -------------------------------------------------

# Override Kivy widgets for translations
size_dict: dict[str, list] = {'down': [], 'up': []}

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
    if isinstance(string, str) and "$" in string: return re.sub(r'\$([^\$]+)\$', r'\g<1>', string)
    else: return string

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
        else: super().__setattr__(key, value)



# ------------------------------------------- Telepath UI Callbacks ----------------------------------------------------

# Endpoint for receiving & displaying remote client action notifications as a banner
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


# Handle UI logic when Telepath session gets disconnected
def telepath_disconnect():
    try:
        # This is handled in MenuBackground.on_pre_enter()
        if constants.server_manager.current_server:
            constants.server_manager.current_server._disconnected = True
    except AttributeError: pass
constants.telepath_disconnect = telepath_disconnect


# Check if this Telepath client has disconnected from a currently loaded remote server
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


# Displays a UI warning/block if the remote server is currently busy with a critical operation
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



# ----------------------------------------------- Helper Methods -------------------------------------------------------

# Saves the current Kivy window position & size to config
def save_window_pos(*args):
    global last_window

    # Only save position in windowed mode
    if Window.left > 0 and Window.top > 0:
        last_window.update({'pos': [Window.left, Window.top], 'size': Window.system_size})

    constants.app_config.fullscreen = (Window.system_size[0] > (_default_size[0] + 400))
    constants.app_config.geometry   = last_window


# Helper to hide Kivy widgets
def hide_widget(wid, dohide=True, *argies):
    if hasattr(wid, 'saved_attrs'):
        if not dohide:
            wid.height, wid.size_hint_y, wid.opacity, wid.disabled = wid.saved_attrs
            del wid.saved_attrs
    elif dohide:
        wid.saved_attrs = wid.height, wid.size_hint_y, wid.opacity, wid.disabled
        wid.height, wid.size_hint_y, wid.opacity, wid.disabled = 0, None, 0, True


# Check if any servers are running, and display a popup if there are to prevent an action
# This is meant to be displayed before sensitive operations that could affect servers in runtime
def check_running(final_func):
    running = constants.server_manager.running_servers

    # Issue stop command to all running servers to quit gracefully
    def close_servers(*args):
        for server in running.values():
            dTimer(0, functools.partial(server.silent_command, "stop")).start()
        if final_func: final_func()

    # If there are running servers, prompt user before exiting
    if running:
        server_count = len(list(running.keys()))

        if server_count == 1: desc = "There is currently 1 server running. To continue, it will be closed.\n\nAre you sure you want to continue?"
        else:                 desc = f"There are currently ${server_count}$ servers running. To continue, they will be closed.\n\nAre you sure you want to continue?"

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
    elif final_func: final_func()


# Helper for input validation in IP TextInputs
def process_ip_text(server_obj=None):

    if server_obj:
        start_text = ''
        if not str(server_obj.port) == '25565' or server_obj.ip:
            if server_obj.ip: start_text = server_obj.ip
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


# Shorthand for retrieving an icon asset location
def icon_path(name):
    return os.path.join(paths.ui_assets, 'icons', name)



# --------------------------------------------------  File chooser  ----------------------------------------------------

# Synchronous 'xdg-desktop-portal' FileChooser using dbus-next
# https://wiki.archlinux.org/title/XDG_Desktop_Portal
def linux_portal_picker(ask_type: str, start_dir: str = "", title: str = "", patterns: list[str] | None = None, multiple: bool = False, timeout_s: float = 120.0) -> str | list[str]:
    patterns = patterns or []

    def _cancel():
        return [] if (ask_type == "file" and multiple) else ""

    def _uri_to_path(uri: str) -> str:
        p = urlparse(uri)
        return unquote(p.path) if p.scheme == "file" else uri

    def _folder_to_ay(folder: str) -> bytes:
        b = os.fsencode(folder)
        return b if b.endswith(b"\x00") else b + b"\x00"

    if constants.os_name != 'linux': return _cancel()
    q: "queue.Queue[object]" = queue.Queue(maxsize=1)

    def worker():
        try:
            from dbus_next import Variant, Message, MessageType
            from dbus_next.aio import MessageBus
            import secrets
            import asyncio

            async def _run():
                bus = await MessageBus().connect()
                token: str = f"auto_mcs_{secrets.token_hex(8)}"
                options: dict[str, Variant] = {
                    "modal": Variant("b", True),
                    "handle_token": Variant("s", token),
                }

                if ask_type == "dir": options["directory"] = Variant("b", True)
                elif multiple:        options["multiple"]  = Variant("b", True)
                if start_dir:
                    folder = str(Path(start_dir).expanduser().resolve())
                    options["current_folder"] = Variant("ay", _folder_to_ay(folder))


                # Portal expects a(sa(us)) where each entry is:
                #   (name, [ (type, pattern), ... ])
                # type 0 = glob pattern
                if ask_type == "file" and patterns:
                    string = ', '.join(patterns)
                    filters = [[string, [[0, p] for p in patterns]]]
                    options["filters"] = Variant("a(sa(us))", filters)


                # Signature: OpenFile(s parent_window, s title, a{sv} options) -> o (request_handle)
                msg = Message(
                    destination = "org.freedesktop.portal.Desktop",
                    path = "/org/freedesktop/portal/desktop",
                    interface = "org.freedesktop.portal.FileChooser",
                    member = "OpenFile",
                    signature = "ssa{sv}",
                    body = ["", title or "", options],
                )

                reply = await bus.call(msg)
                if reply.message_type == MessageType.ERROR:
                    raise RuntimeError(f"Portal OpenFile error: {reply.error_name} {reply.body}")

                request_path = reply.body[0]

                # Wait for Request::Response from handle
                loop = asyncio.get_running_loop()
                fut = loop.create_future()


                # Interface: org.freedesktop.portal.Request
                # Member: Response
                # Signature: ua{sv} (u response, a{sv} results)
                def handler(message: Message):
                    if (
                        message.message_type == MessageType.SIGNAL
                        and message.path == request_path
                        and message.interface == "org.freedesktop.portal.Request"
                        and message.member == "Response"
                    ):
                        if not fut.done(): fut.set_result(message.body)

                bus.add_message_handler(handler)

                # Always remove handler to prevent buildup
                try: body = await asyncio.wait_for(fut, timeout=timeout_s)
                finally: bus.remove_message_handler(handler)

                response_code = int(body[0])
                results = body[1] or {}

                # 0: success
                # 1: cancelled
                # 2: dismissed/other
                if response_code != 0: return _cancel()

                uris_var = results.get("uris")
                uris = uris_var.value if uris_var is not None else []
                paths = [_uri_to_path(u) for u in uris]

                if ask_type == "file" and multiple: return paths
                return paths[0] if paths else _cancel()

            q.put(asyncio.run(_run()))

        except BaseException as e: q.put(e)

    dTimer(0, worker).start()

    output = q.get()
    if isinstance(output, BaseException):
        if constants.debug: send_log("linux_portal_picker", f"portal picker failed:\n{constants.format_traceback(output)}", "error")
        return _cancel()

    return output


# Opens a popup for the user to select a folder or file, and returns their selection
def file_popup(ask_type, start_dir=paths.user_home, ext=[], input_callback=None, select_multiple=False, title=None) -> str | list[str]:
    final_path: str | list[str] = ''
    file_icon:              str = os.path.join(paths.ui_assets, "small-icon.ico")
    title:                  str = translate(title)
    error:     Exception | None = None
    send_log('file_popup', f"requesting {ask_type} popup '{title}'", 'info')

    # Will find the first file start_dir to auto select
    def iter_start_dir(directory):
        end_dir = directory

        for dir_item in glob(os.path.join(start_dir, "*")):
            end_dir = dir_item
            break

        return end_dir


    # Prompt the user to select a file/files
    # ext = [("Comma-separated Values", "*.csv")]
    try:
        if ask_type == "file":

            # filechooser.open_file() implements plyer's Win32FileChooser class for Windows
            if constants.os_name == 'windows':
                final_path = filechooser.open_file(title=title, filters=ext, path=iter_start_dir(start_dir), multiple=select_multiple, icon=file_icon)


            # Use the 'xdg-desktop-portal' spec helper for Linux
            elif constants.os_name == 'linux':
                final_path = [linux_portal_picker(
                    ask_type = "file",
                    start_dir = start_dir,
                    title = title,
                    patterns = ext,
                    multiple = select_multiple,
                )]

            # Use AppleScript solution for macOS
            elif constants.os_name == 'macos':
                ext_list = '", "'.join(ext)
                ext_command = f'of type {{"{ext_list}"}}'.replace('*.','') if ext else ''
                start_path_command = f'with prompt "{title}"' + (f' default location POSIX file "{start_dir}"' if start_dir else '')

                # AppleScript with f-string formatting for dynamically setting parameters
                script = f"osascript -e 'set myFile to choose file {start_path_command} {ext_command}\nPOSIX path of myFile'"
                final_path = [constants.run_proc(script, return_text=True).strip()]


        # Prompt the user to select a directory
        elif ask_type == "dir":

            # Use tkinter's filedialog only on Windows, it's a better UI than plyer's Win32FileChooser for directories
            if constants.os_name == "windows":
                import tkinter as tk
                from tkinter import filedialog

                root = tk.Tk()
                root.withdraw()
                root.iconbitmap(file_icon)
                final_path = filedialog.askdirectory(initialdir=start_dir, title=title)
                Window.raise_window()


            # Use the 'xdg-desktop-portal' spec helper for Linux
            elif constants.os_name == 'linux':
                final_path = linux_portal_picker(
                    ask_type = "dir",
                    start_dir = start_dir,
                    title = title,
                    patterns = [],
                    multiple = False,
                )


            # Use AppleScript solution for macOS
            elif constants.os_name == 'macos':
                start_path_command = f'with prompt "{title}"' + (f' default location POSIX file "{start_dir}"' if start_dir else '')

                # AppleScript with f-string formatting for dynamically setting parameters
                script = f"    osascript -e 'set myFolder to choose folder {start_path_command}\nPOSIX path of myFolder'"
                final_path = constants.run_proc(script, return_text=True).strip()
                if final_path.endswith('User canceled. (-128)'): final_path = []

    except Exception as e: error = e


    # Update callback method with the final path
    if input_callback and final_path: input_callback(final_path)

    if error:       send_log('file_popup', f"error opening {ask_type} popup '{title}': {constants.format_traceback(error)}", 'error')
    if final_path:  send_log('file_popup', f"retrieved user selection from {ask_type} popup '{title}':\n'{final_path}'", 'info')
    elif not error: send_log('file_popup', f"user cancelled {ask_type} popup '{title}'")

    return final_path


# Open folder in default file browser, and automatically select a file if one is passed
def open_folder(path: str):
    try:
        send_log('open_folder', f"opening '{path}' in file browser")

        def q(p: str) -> str:
            return shlex.quote(p) if constants.os_name in ('linux', 'macos') else f'"{p}"'

        # Open directory, and highlight a file
        if os.path.isfile(path):
            if constants.os_name == 'linux':
                uri = Path(path).resolve().as_uri()
                cmd = (
                    'dbus-send --session --print-reply '
                    '--dest=org.freedesktop.FileManager1 --type=method_call '
                    '/org/freedesktop/FileManager1 org.freedesktop.FileManager1.ShowItems '
                    f'array:string:"{uri}" string:""'
                )
                constants.run_proc(cmd)

            elif constants.os_name == 'macos':
                constants.run_proc(f'open -R {q(path)}')

            elif constants.os_name == 'windows':
                constants.run_proc(f'explorer /select,{q(path)}', success_code=1)

        # Otherwise, just open a directory
        else:
            if constants.os_name == 'linux':
                constants.run_proc(f'xdg-open {q(path)}')

            elif constants.os_name == 'macos':
                constants.run_proc(f'open {q(path)}')

            elif constants.os_name == 'windows':
                constants.run_proc(f'explorer {q(path)}', success_code=1)

    except Exception as e:
        send_log('open_folder', f"error opening '{path}': {e}", 'warning')
        return False


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



# ----------------------------------------------- Server Manager Helpers -----------------------------------------------

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
                functools.partial(screen_manager.current_screen.show_popup, "file", "Author's Notes", show_readme, (None)),
                1
            )

    constants.server_manager.open_server(server_name)
    server_obj = constants.server_manager.current_server

    needs_update = False
    try:
        if constants.server_manager.update_list:
            needs_update = constants.server_manager.update_list[server_obj.name]['needsUpdate']
    except: pass

    # Automatically update if available
    if server_obj.running: ignore_update = True
    if server_obj.auto_update == "true" and needs_update and constants.app_online and not ignore_update and constants.check_free_space(telepath_data=server_obj._telepath_data):
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

    else: Clock.schedule_once(next_screen, 0.8 if wait_page_load else 0)


# Opens a remote server in panel, and updates Server Manager current_server
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
                functools.partial(screen_manager.current_screen.show_popup, "file", "Author's Notes", show_readme, (None)),
                1
            )

    remote_obj = constants.api_manager.request(
        endpoint = f'/main/open_remote_server?name={constants.quote(server_name)}',
        host = instance['host'],
        port = instance['port'],
        args = {'none': None}
    )

    if remote_obj:
        telepath_data = {'name': server_name, 'host': instance['host'], 'port': instance['port'], 'nickname': instance['nickname']}
        constants.server_manager._init_telepathy(telepath_data)
        server_obj = constants.server_manager.current_server
        update_list = constants.get_remote_var('server_manager.update_list', telepath_data)

        needs_update = False
        try:
            if update_list: needs_update = update_list[server_obj.name]['needsUpdate'] == 'true'
        except: pass

        # Automatically update if available
        if server_obj.running: ignore_update = True
        if server_obj.auto_update == "true" and needs_update and constants.app_online and not ignore_update and constants.check_free_space(telepath_data=server_obj._telepath_data):
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
            telepath_data = {'name': server_name, 'host': instance['host'], 'port': instance['port'], 'nickname': instance['nickname']}
            constants.server_manager._init_telepathy(telepath_data)
            Clock.schedule_once(next_screen, 0.8 if wait_page_load else 0)

    return remote_obj


# Displays a UI warning/block if the auto-mcs storage location is full (see 'constants.check_free_space()')
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


# Initializes the UI callback for updating the displayed IP in the console panel from the backend
def refresh_ips(server_name):
    def _schedule(*a):
        screen = screen_manager.current_screen
        if "ServerViewScreen" in screen.name:
            if screen.server.name == server_name:
                screen.server_button.update_subtitle(screen.server.run_data)
    Clock.schedule_once(_schedule, 0)
manager.refresh_ips = refresh_ips
