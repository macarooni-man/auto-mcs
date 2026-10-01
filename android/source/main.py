from pathlib import Path
import threading
import time
import sys
import os


APP_ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = APP_ROOT / "source"

# Current auto-mcs uses both `source.*` and top-level `ui.*` imports.
for path in (str(APP_ROOT), str(SOURCE_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

import android_runtime

android_runtime.prepare_environment()
android_runtime.install_desktop_stubs()


def configure_constants():
    from source.core import constants, translator
    from source.core.constants import paths

    # `constants.paths` must be constructed before this is flipped so it points
    # at the staged source/assets instead of the Android Python executable.
    constants.app_compiled = True

    constants.is_android = True
    constants.is_docker = False
    constants.is_arm = True
    constants.is_rosetta = False

    constants.debug = os.environ.get("AUTO_MCS_ANDROID_DEBUG", "1") != "0"
    constants.headless = False
    constants.bypass_admin_warning = True
    constants.bypass_disk_warning = True

    paths.launch_path = str(Path(__file__).resolve())

    constants.username = "remote"
    constants.hostname = android_runtime.hostname()

    # Ensure the Android-private config exists before changing Android defaults.
    config_file = os.path.join(paths.config, "app-config.json")
    if not os.path.exists(config_file):
        constants.app_config.reset()

    # Android is a client build. Never self-update or try Discord IPC.
    if constants.app_config.auto_update:
        constants.app_config.auto_update = False
    if constants.app_config.discord_presence:
        constants.app_config.discord_presence = False

    constants.app_online = android_runtime.network_available()

    if not constants.app_config.locale:
        system_locale = android_runtime.locale_code()
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

    android_runtime.install_null_audio(audio)

    # TelepathManager is needed for client-side requests even though the
    # Android client never starts the local API listener.
    constants.api_manager = telepath.TelepathManager()

    # These are compatibility objects for UI code that assumes managers exist.
    # No Android background task installs or launches either service.
    try:
        java.init_manager()
    except Exception:
        android_runtime.log_exception("Failed to initialize Java compatibility manager")

    try:
        playit.init_manager()
    except Exception:
        android_runtime.log_exception("Failed to initialize Playit compatibility manager")

    try:
        constants.search_manager = constants.SearchManager()
    except Exception:
        android_runtime.log_exception("Failed to initialize SearchManager")

    return logger


def network_loop(constants):
    while True:
        try:
            constants.app_online = android_runtime.network_available()
        except Exception:
            pass
        time.sleep(10)


def main():
    constants = configure_constants()
    logger = init_runtime(constants)

    threading.Thread(
        target=network_loop,
        args=(constants,),
        name="android-network",
        daemon=True,
    ).start()

    try:
        from source.ui.main import ui_loop
        ui_loop()

    except SystemExit:
        pass

    except Exception:
        android_runtime.log_exception("auto-mcs Android UI crashed")
        try:
            logger.log_manager.dump_to_disk()
        except Exception:
            pass
        raise

    finally:
        try:
            if constants.api_manager:
                constants.api_manager.stop()
                constants.api_manager.close_sessions()
        except Exception:
            pass

        try:
            logger.log_manager.dump_to_disk()
        except Exception:
            pass


if __name__ == "__main__":
    main()
