from source.core.constants import paths
from source.core import constants
import logging
import os


# Disable Kivy logging from their way
from source.core.logger import KivyToLoggerHandler
kivy_folder = os.path.join(paths.os_temp, ".kivy")
constants.folder_check(kivy_folder)
os.environ['KIVY_HOME'] = kivy_folder
os.environ.setdefault("KIVY_LOG_MODE", "PYTHON")
os.environ.setdefault("KIVY_NO_FILELOG", "1")
os.environ.setdefault("KIVY_NO_CONSOLELOG", "1")
root = logging.getLogger()
root.setLevel(logging.DEBUG)
root.addHandler(KivyToLoggerHandler())


os.environ["KCFG_KIVY_LOG_LEVEL"] = "debug" if constants.debug else "info"
os.environ["KIVY_IMAGE"] = "pil,sdl2"
os.environ['KIVY_NO_ARGS'] = '1'
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




# Run application and startup preferences
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

        popup = utility.screen_manager.current_screen.popup_widget
        if popup:
            popup.self_destruct(utility.screen_manager.current_screen, False)
            utility.screen_manager.current_screen.canvas.after.clear()

        Clock.schedule_once(
            functools.partial(
                utility.screen_manager.current_screen.show_popup,
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

def exit_app(*a, **kw):
    app.exit_check(force_close=True)
    sys.exit(0)

class MainApp(App):

    # Disable F1 menu when compiled
    if constants.app_compiled:
        def open_settings(self, *largs):
            pass

    # Check if window pos is set in config
    preconfigured = False
    if constants.app_config.geometry:
        pos = constants.app_config.geometry['pos']
        size = constants.app_config.geometry['size']

        # Only load cached window data if the position is valid (not zero, or off-screen)
        if all([i > 0 for i in pos]) and (pos[0] > -5000 and pos[1] > -5000):
            constants.last_window = constants.app_config.geometry
            if (size[0] >= constants.window_size[0] and size[1] >= constants.window_size[1] - 50):
                Window.size   = size
                Window.left   = pos[0]
                Window.top    = pos[1]
                preconfigured = True

    # Window size
    if not preconfigured:
        size = constants._default_size

        # Get pos and knowing the old size calculate the new one
        top  = dp((Window.top * Window.size[1] / size[1])) - dp(70)
        left = dp(Window.left * Window.size[0] / size[0])

        Window.size = (dp(size[0]), dp(size[1]))
        Window.top  = top
        Window.left = left
    Window.on_request_close = exit_app

    Window.minimum_width  = constants.window_size[0]
    Window.minimum_height = constants.window_size[1] - 50
    Window.clearcolor     = constants.background_color

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
        data = app.exit_check()
        if not data: exit_app()
        return data
    Window.bind(on_request_close=_close_window_wrapper)
    Window.bind(
        on_maximize     = utility.save_window_pos,
        on_minimize     = utility.save_window_pos,
        on_restore      = utility.save_window_pos
    )
    dropped_files = []
    processing_drops = False

    def build(self):
        Window.bind(on_dropfile=self.file_drop)

        self.icon = os.path.join(paths.ui_assets, "big-icon.png")

        utility.screen_manager.initialize()

        # Close splash screen if compiled
        if constants.app_compiled and constants.os_name == 'windows':
            import pyi_splash
            pyi_splash.close()

        if constants.app_config.fullscreen:
            Window.maximize()
        Window.show()
        Window._update_density_and_dpi()

        # Raise window
        def raise_window(*a):
            Window.raise_window()
        Clock.schedule_once(raise_window, 0)


        # Screen manager override for testing
        # if not constants.app_compiled:
        #     def _delay(*a):
        #         s = constants.server_manager.open_server('Beds Rock')
        #         while not all(s._check_object_init().values()):
        #             time.sleep(0.1)
        #         foundry.new_server_init()
        #         utility.screen_manager.current = 'ServerBackupScreen'
        #     Clock.schedule_once(_delay, 0)



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


                if utility.screen_manager.current == 'CreateServerAddonScreen':
                    banner_text = ''
                    for addon in self.dropped_files:
                        if addon.endswith(".jar") and os.path.isfile(addon):
                            addon = addons.get_addon_file(addon, foundry.new_server_info)
                            foundry.new_server_info['addon_objects'].append(addon)
                            utility.screen_manager.current_screen.gen_search_results(
                                foundry.new_server_info['addon_objects'])

                            # Switch pages if page is full
                            if (len(utility.screen_manager.current_screen.scroll_layout.children) == 0) and (len(foundry.new_server_info['addon_objects']) > 0):
                                utility.screen_manager.current_screen.switch_page("right")

                            # Show banner
                            if len(self.dropped_files) == 1:
                                if len(addon.name) < 26:
                                    addon_name = addon.name
                                else:
                                    addon_name = addon.name[:23] + "..."

                                banner_text = f"Added '${addon_name}$' to the queue"
                            else:
                                banner_text = f"Added ${len(self.dropped_files)}$ add-ons to the queue"

                    if banner_text:
                        Clock.schedule_once(
                            functools.partial(
                                utility.screen_manager.current_screen.show_banner,
                                (0.553, 0.902, 0.675, 1),
                                banner_text,
                                "add-circle-sharp.png",
                                2.5,
                                {"center_x": 0.5, "center_y": 0.965}
                            ), 0
                        )

                if utility.screen_manager.current == 'ServerAddonScreen':
                    addon_manager = constants.server_manager.current_server.addon
                    banner_text = ''
                    for addon in self.dropped_files:
                        if addon.endswith(".jar") and os.path.isfile(addon):
                            addon = addon_manager.import_addon(addon)
                            addon_list = addon_manager.return_single_list()
                            utility.screen_manager.current_screen.gen_search_results(addon_manager.return_single_list(), fade_in=False, highlight=addon.hash, animate_scroll=True)

                            # Switch pages if page is full
                            if (len(utility.screen_manager.current_screen.scroll_layout.children) == 0) and (len(addon_list) > 0):
                                utility.screen_manager.current_screen.switch_page("right")

                            # Show banner
                            if len(self.dropped_files) == 1:
                                if len(addon.name) < 26:
                                    addon_name = addon.name
                                else:
                                    addon_name = addon.name[:23] + "..."

                                banner_text = f"Imported '${addon_name}$'"
                            else:
                                banner_text = f"Imported ${len(self.dropped_files)}$ add-ons"

                    if banner_text:

                        # Show banner if server is running
                        if addon_manager._hash_changed():
                            Clock.schedule_once(
                                functools.partial(
                                    utility.screen_manager.current_screen.show_banner,
                                    (0.937, 0.831, 0.62, 1),
                                    f"A server restart is required to apply changes",
                                    "sync.png",
                                    3,
                                    {"center_x": 0.5, "center_y": 0.965}
                                ), 0
                            )

                        else:
                            Clock.schedule_once(
                                functools.partial(
                                    utility.screen_manager.current_screen.show_banner,
                                    (0.553, 0.902, 0.675, 1),
                                    banner_text,
                                    "add-circle-sharp.png",
                                    2.5,
                                    {"center_x": 0.5, "center_y": 0.965}
                                ), 0
                            )

                if utility.screen_manager.current == 'ServerAmscriptScreen':
                    script_manager = constants.server_manager.current_server.script_manager
                    if self.dropped_files:
                        banner_text = ''
                        for script in self.dropped_files:
                            if script.endswith(".ams") and os.path.isfile(script):
                                script = script_manager.import_script(script)
                                if not script:
                                    continue

                                script_list = script_manager.return_single_list()
                                utility.screen_manager.current_screen.gen_search_results(script_manager.return_single_list(), fade_in=False, highlight=script.hash, animate_scroll=True)

                                # Switch pages if page is full
                                if (len(utility.screen_manager.current_screen.scroll_layout.children) == 0) and (len(script_list) > 0):
                                    utility.screen_manager.current_screen.switch_page("right")

                                # Show banner
                                if len(self.dropped_files) == 1:
                                    if len(script.title) < 26:
                                        script_name = script.title
                                    else:
                                        script_name = script.title[:23] + "..."

                                    banner_text = f"Imported '${script_name}$'"
                                else:
                                    banner_text = f"Imported ${len(self.dropped_files)}$ scripts"

                        if banner_text:

                            # Show banner if server is running
                            if script_manager._hash_changed():
                                Clock.schedule_once(
                                    functools.partial(
                                        utility.screen_manager.current_screen.show_banner,
                                        (0.937, 0.831, 0.62, 1),
                                        "An amscript reload is required to apply changes",
                                        "sync.png",
                                        3,
                                        {"center_x": 0.5, "center_y": 0.965}
                                    ), 0
                                )

                            else:
                                Clock.schedule_once(
                                    functools.partial(
                                        utility.screen_manager.current_screen.show_banner,
                                        (0.553, 0.902, 0.675, 1),
                                        banner_text,
                                        "add-circle-sharp.png",
                                        2.5,
                                        {"center_x": 0.5, "center_y": 0.965}
                                    ), 0
                                )


                def enable(*a):
                    self.processing_drops = False
                self.dropped_files = []
                Clock.schedule_once(enable, 1)


        self.dropped_files.append(path.decode())
        if not self.processing_drops and self.dropped_files:
            Clock.schedule_once(process_drops, 0.1)


app: MainApp = None
def run_application():
    global app

    send_log('run_application', 'initializing graphical UI (Kivy)', 'info')
    app = MainApp(title=constants.app_title)

    try:
        audio.init_player()
        app.run()
        if constants.os_name == 'macos':
            Window.close()
    except ArgumentError:
        pass

    except Exception as e:
        Window.close()
        raise e
