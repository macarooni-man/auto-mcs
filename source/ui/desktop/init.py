from source.core.constants import paths
from source.core import constants
import logging
import os


# ----------------------------------------------- auto-mcs Desktop UI --------------------------------------------------

# Re-route all Kivy logs into the internal 'source.core.logger'
from source.core.logger import KivyToLoggerHandler
os.environ.setdefault("KIVY_LOG_MODE", "PYTHON")
os.environ.setdefault("KIVY_NO_FILELOG", "1")
os.environ.setdefault("KIVY_NO_CONSOLELOG", "1")

root = logging.getLogger()
root.setLevel(logging.DEBUG)
root.addHandler(KivyToLoggerHandler())



# Configure all Kivy properties for auto-mcs
kivy_folder = os.path.join(paths.os_temp, ".kivy")
constants.folder_check(kivy_folder)

os.environ['KIVY_HOME']            = kivy_folder
os.environ["KCFG_KIVY_LOG_LEVEL"]  = "debug" if constants.debug else "info"
os.environ["KIVY_IMAGE"]           = "pil,sdl2"
os.environ['KIVY_NO_ARGS']         = '1'
os.environ["KIVY_METRICS_DENSITY"] = "1"

from kivy.config import Config
Config.set('graphics', 'maxfps', '120')
Config.set('graphics', 'vsync', '-1')
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Config.set('graphics', 'window_state', 'hidden')
Config.set('kivy', 'exit_on_escape', '0')



# Import Kivy elements & helpers
from source.ui.desktop.utility import *
from source.ui.desktop import utility
from kivy.metrics import dp
from kivy.app import App
from kivy import __version__ as kivy_version
from packaging.version import Version

# Backport Kivy 2.3.2 fix for Windows DPI returning 0 (#9029)
if constants.os_name == 'windows' and Version(kivy_version) < Version('2.3.2'):
    def _update_density_and_dpi(self):
        from ctypes import windll

        self.dpi = 96.
        self._density = 1.

        try:
            hwnd = windll.user32.GetActiveWindow()
            dpi = float(windll.user32.GetDpiForWindow(hwnd))

            if dpi:
                self.dpi = dpi
                self._density = self.dpi / 96

        except AttributeError:
            pass

    Window.__class__._update_density_and_dpi = _update_density_and_dpi




# Screen overrides for testing
def test_hook():
    def _delay(*a):
        # s = constants.server_manager.open_server('Beds Rock')
        # while not all(s._check_object_init().values()):
        #     time.sleep(0.1)
        # utility.screen_manager.current - 'ServerBackupScreen'

        # from source.core.server import foundry
        # foundry.new_server_init()
        # utility.screen_manager.current = 'CreateServerNameScreen'

        pass

    Clock.schedule_once(_delay, 0)



# Global app instance (loaded into 'source.ui.desktop.utility')
class MainApp(App):

    # Flag to check size application from config
    window_preconfigured: bool = False

    # Flag to check if the first pass of the window size succeeded
    configured_window:    bool = False

    # For dropped file processing
    dropped_files:   list[str] = []
    processing_drops:     bool = False

    # Disable F1 menu when compiled
    if constants.app_compiled:
        def open_settings(self, *_): pass


    # Set up window size/position
    def _configure_window(self):
        if self.configured_window: return self.configured_window

        try:

            # Check if window pos is set in config
            if constants.app_config.geometry:
                pos = constants.app_config.geometry['pos']
                size = constants.app_config.geometry['size']

                # Only load cached window data if the position is valid (not zero, or off-screen)
                if all([i > 0 for i in pos]) and (pos[0] > -5000 and pos[1] > -5000):
                    utility.last_window = constants.app_config.geometry
                    if (size[0] >= utility.window_size[0] and size[1] >= utility.window_size[1] - 50):
                        Window.size = size
                        Window.left = pos[0]
                        Window.top  = pos[1]
                        self.window_preconfigured = True

            # Window size
            if not self.window_preconfigured:
                size = utility._default_size

                # Get pos and knowing the old size calculate the new one
                top  = dp((Window.top * Window.size[1] / size[1])) - dp(70)
                left = dp(Window.left * Window.size[0] / size[0])

                Window.size = (dp(size[0]), dp(size[1]))
                Window.top  = top
                Window.left = left

            self.configured_window = True


        # Failed to set window
        except Exception as e:
            send_log('MainApp', f'failed to configure window: {constants.format_traceback(e)}', 'error')
            self.configured_window = False

        return self.configured_window


    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # First, attempt to configure the window before shown
        self._configure_window()

        Window.on_request_close = self.exit_check
        Window.minimum_width = utility.window_size[0]
        Window.minimum_height = utility.window_size[1] - 50
        Window.clearcolor = constants.background_color

        Window.bind(
            on_maximize = utility.save_window_pos,
            on_minimize = utility.save_window_pos,
            on_restore  = utility.save_window_pos
        )

    # Prevent window from closing during certain situations
    def exit_check(self, force_close=False, *args):

        # Write window size to global config
        utility.save_window_pos()

        if force_close:
            Window.close()
            amseditor.quit_ipc = True
            return False

        if constants.ignore_close:
            return True

        elif constants.server_manager.running_servers:
            check_running(Window.close)
            return True

        else:
            Window.close()
            amseditor.quit_ipc = True
            return False

    def _close_window_wrapper(self):
        data = self.exit_check()
        if not data: self._exit()
        return data

    def attempt_to_close(self, force: bool = False):
        if force: self.exit_check(force_close=True)
        elif not self.exit_check(): self._exit()

    def _exit(self, *a, **kw):
        self.exit_check(force_close=True)
        sys.exit(0)


    # Run application and startup preferences
    def build(self):
        Window.bind(on_dropfile=self.file_drop)

        self.icon = os.path.join(paths.ui_assets, "big-icon.png")

        utility.screen_manager.initialize()

        # Close splash screen if compiled
        if constants.app_compiled and constants.os_name == 'windows':
            import pyi_splash
            pyi_splash.close()

        if constants.app_config.fullscreen: Window.maximize()
        Window.show()

        # Raise window, and configure again after if it failed
        def raise_window(*a):
            Window.raise_window()
            Window._update_density_and_dpi()
            self._configure_window()
        Clock.schedule_once(raise_window, 0)


        # Screen manager override for testing
        if not constants.app_compiled: test_hook()


        # Process --launch flag
        if constants.boot_launches:
            if not constants.is_admin() or constants.bypass_admin_warning:

                def callback(success: bool, message: str):
                    Clock.schedule_once(
                        functools.partial(
                            utility.screen_manager.current_screen.show_banner,
                            (0.553, 0.902, 0.675, 1) if success else (1, 0.5, 0.65, 1),
                            message,
                            "play-circle-sharp.png",
                            2.5,
                            {"center_x": 0.5, "center_y": 0.965}
                        ), 0
                    )

                constants.server_manager._gabage_handler(callback)

        return utility.screen_manager


    # Executes function on file drop
    def file_drop(self, w, path):
        def process_drops(*a):
            if not self.processing_drops and self.dropped_files:
                self.processing_drops = True

                utility.screen_manager.current_screen.file_drop(self.dropped_files)

                def enable(*a): self.processing_drops = False

                self.dropped_files = []
                Clock.schedule_once(enable, 1)

        self.dropped_files.append(path.decode())
        if not self.processing_drops and self.dropped_files:
            Clock.schedule_once(process_drops, 0.1)



# ---------------------------------------------------- Launch UI -------------------------------------------------------

def run_application():

    send_log('run_application', 'initializing graphical UI (Kivy)', 'info')
    utility.app = MainApp(title=constants.app_title)

    try:

        # Initialize UI dependencies
        audio.init_player()
        utility.get_refresh_rate()

        utility.app.run()

        if constants.os_name == 'macos':
            Window.close()

    except ArgumentError:
        pass

    except Exception as e:
        Window.close()
        raise e
