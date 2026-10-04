from argparse import Namespace
from pathlib import Path
import threading
import json
import time
import sys
import os


app_root = Path(__file__).resolve().parent
source_root = app_root / "source"

# Current auto-mcs uses both 'source.*' and top-level 'ui.*' imports
for path in (str(app_root), str(source_root)):
    if path not in sys.path:
        sys.path.insert(0, path)

import runtime

runtime.prepare_environment()
runtime.install_desktop_stubs()


def configure_constants():
    from source.core import constants, translator
    from source.core.constants import paths
    from os import path
    import json

    # 'constants.paths' must be constructed before this is flipped so it points
    # at the staged source/assets instead of the Android Python executable
    constants.app_compiled = True

    constants.is_android = True
    constants.is_docker = False
    constants.is_arm = True
    constants.is_rosetta = False

    constants.boot_arguments = Namespace()
    constants.debug = os.environ.get("AUTO_MCS_ANDROID_DEBUG", "1") != "0"
    constants.headless = False
    constants.bypass_admin_warning = True
    constants.bypass_disk_warning = True


    # Load 'build-data.json' into memory
    if path.exists(paths.build_data):
        with open(paths.build_data, 'r', encoding='utf-8', errors='ignore') as file:
            try:
                data = json.loads(file.read())
                if isinstance(data['version'], str) and data['version'].isnumeric(): data['version'] = int(data['version'])
                constants.build_data.update(data)

            except Exception as e:
                if constants.debug: runtime.log_exception(f"failed to load '{paths.build_data}'")

    # Apply helper variables from 'build-data.json'
    constants.is_official = str(constants.build_data['repo']) == constants.project_repo.split('/', 3)[-1]
    constants.dev_version = 'dev' in constants.build_data['type'] or not constants.is_official


    paths.launch_path = str(Path(__file__).resolve())

    constants.username = "remote"
    constants.hostname = runtime.hostname()
    constants.machine_id = runtime.machine_id()

    # Ensure the Android-private config exists before changing Android defaults.
    config_file = os.path.join(paths.config, "app-config.json")
    if not os.path.exists(config_file):
        constants.app_config.reset()

    # Android is a client build. Never self-update or try Discord IPC.
    if constants.app_config.auto_update:
        constants.app_config.auto_update = False
    if constants.app_config.discord_presence:
        constants.app_config.discord_presence = False

    constants.app_online = runtime.network_available()

    if not constants.app_config.locale:
        system_locale = runtime.locale_code()
        selected = "en"

        for data in translator.available_locales.values():
            if system_locale.startswith(data["code"]):
                selected = data["code"]
                break

        constants.app_config.locale = selected

    return constants


def init_runtime(constants):
    from source.core import audio, logger, telepath
    from source.core.tools import java, playit

    runtime.configure_audio(audio)

    # TelepathManager is needed for client-side requests
    constants.api_manager = telepath.TelepathManager()

    # These are compatibility objects for UI code that assumes these managers exist
    try: java.init_manager()
    except Exception: runtime.log_exception("Failed to initialize Java compatibility manager")

    try: playit.init_manager()
    except Exception: runtime.log_exception("Failed to initialize Playit compatibility manager")

    try: constants.search_manager = constants.SearchManager()
    except Exception: runtime.log_exception("Failed to initialize SearchManager")

    return logger


def background(constants):
    from source.core.server import foundry

    def background_launch(func, *args):
        try: func(*args)
        except Exception: runtime.log_exception(f"Failed to run Android background task '{func.__name__}'")

    def update_network():
        previous = constants.app_online
        try: current = runtime.network_available()
        except Exception: return
        if current == previous:
            return

        constants.app_online = current
        runtime.log(f'Android network changed: {previous} -> {current}')

        try:
            utility = sys.modules.get('source.ui.desktop.utility')
            if not utility: return
            from kivy.clock import Clock

            def refresh(*args):
                screen = utility.screen_manager.current_screen
                if screen and screen.__class__.__name__ == 'MainMenuScreen':
                    screen.reload_menu()
            Clock.schedule_once(refresh, 0)

        except Exception:
            runtime.log_exception('Failed to refresh Android network state')

    # Wait until ServerManager is initialized
    while not constants.server_manager:
        time.sleep(0.1)

    # Initialize background data
    background_launch(constants.get_public_ip)
    background_launch(foundry.find_latest_mc)
    background_launch(constants.server_manager.check_for_updates)
    background_launch(foundry.get_repo_templates)
    background_launch(foundry.check_data_cache)
    background_launch(constants.search_manager.cache_pages)

    # Update network state in the background
    while True:
        update_network()
        time.sleep(15)


def main():
    constants = configure_constants()
    logger = init_runtime(constants)

    threading.Thread(target=background, args=(constants,), name="android-network", daemon=True,).start()

    try:
        from source.ui.main import ui_loop
        ui_loop()

    except SystemExit:
        pass

    except Exception:
        runtime.log_exception("auto-mcs Android UI crashed")
        try: logger.log_manager.dump_to_disk()
        except Exception: pass
        raise

    finally:
        try:
            if constants.api_manager:
                constants.api_manager.stop()
                constants.api_manager.close_sessions()
        except Exception:
            pass

        try: logger.log_manager.dump_to_disk()
        except Exception: pass


if __name__ == "__main__":
    main()
