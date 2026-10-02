from pathlib import Path
import py_compile
import sys


baseline = "16c06e6a4e11f31c0dbf45a6c702cf98addc1cd5"


def fail(message):
    raise RuntimeError(f"[android patch] {message}")


def replace_once(path, old, new, description):
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    count = text.count(old)

    if count != 1:
        fail(f"{description}: expected exactly one source anchor in '{path}', found {count}. Current overlay baseline is {baseline}.")

    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"[android patch] {path}: {description}")


def patch_constants(source):
    path = source / "core" / "constants.py"

    replace_once(
        path,
        """os_name = 'windows' if os.name == 'nt' else \\
          'macos' if platform.system().lower() == 'darwin' else \\
          'linux' if os.name == 'posix' else \\
          os.name



# Global application paths
""",
        """os_name = 'windows' if os.name == 'nt' else \\
          'macos' if platform.system().lower() == 'darwin' else \\
          'linux' if os.name == 'posix' else \\
          os.name

# Android is injected only into the generated build tree.
is_android = os.environ.get("AUTO_MCS_ANDROID") == "1"



# Global application paths
""",
        "add Android runtime flag",
    )

    replace_once(
        path,
        """    user_home:            str = os.path.expanduser('~')
    user_downloads:       str = os.path.join(user_home, 'Downloads')
""",
        """    user_home:            str = os.environ.get("ANDROID_PRIVATE", os.path.expanduser('~')) if is_android else os.path.expanduser('~')
    user_downloads:       str = os.path.join(user_home, 'Downloads')
""",
        "use Android private storage as home",
    )

    replace_once(
        path,
        """    app_folder:           str = os.path.join(appdata, ('.auto-mcs' if os_name != 'macos' else 'auto-mcs'))
""",
        """    app_folder:           str = os.path.join(appdata, ('auto-mcs' if (os_name == 'macos' or is_android) else '.auto-mcs'))
""",
        "use non-hidden Android app data directory",
    )

    replace_once(
        path,
        """    os_temp:              str = os.getenv("TEMP") if os_name == "windows" else "/tmp"
""",
        """    os_temp:              str = os.path.join(user_home, 'tmp') if is_android else os.getenv("TEMP") if os_name == "windows" else "/tmp"
""",
        "keep Android temporary files in private storage",
    )

    replace_once(
        path,
        """    if os_name == "windows":
        name, version = _windows_info()
        return f"{name} (b-{version}, {arch})"

    elif os_name == "macos":
        name, version = _mac_info()
        rosetta_info = ', Rosetta' if is_rosetta else ''
        return f"{name} (b-{version}, {arch}{rosetta_info})"

    elif os_name == "linux":
        distro, kernel = _linux_info()
        docker_info = ', Docker' if is_docker else ''
        return f"{distro} (k-{kernel}, {arch}{docker_info})"

    else: return f'Unknown OS ({arch})'
""",
        """    if is_android:
        import runtime
        version, api = runtime.android_version()

        if version and api:
            return f"Android {version} (API {api}, {arch})"
        elif version:
            return f"Android {version} ({arch})"
        else:
            return f"Android ({arch})"

    elif os_name == "windows":
        name, version = _windows_info()
        return f"{name} (b-{version}, {arch})"

    elif os_name == "macos":
        name, version = _mac_info()
        rosetta_info = ', Rosetta' if is_rosetta else ''
        return f"{name} (b-{version}, {arch}{rosetta_info})"

    elif os_name == "linux":
        distro, kernel = _linux_info()
        docker_info = ', Docker' if is_docker else ''
        return f"{distro} (k-{kernel}, {arch}{docker_info})"

    else: return f'Unknown OS ({arch})'
""",
        "report Android platform information",
    )


def patch_telepath(source):
    path = source / "core" / "telepath.py"

    replace_once(
        path,
        """# Docker identity needs to persist with the app data, not the container
if constants.is_docker:
    UNIQUE_ID = ID_HASH

# First, try to get the machine ID using the module
else:
    try:
        import machineid
        UNIQUE_ID = machineid.hashed_id(f'{constants.app_title}::{constants.username}::{ID_HASH}')

    # If machine ID is busted, do it the good ol' fashioned way
    except:
        import uuid
        UNIQUE_ID = str(uuid.getnode()).ljust(64, '0')
""",
        """# Docker identity needs to persist with the app data, not the container
if constants.is_docker:
    UNIQUE_ID = ID_HASH

# Android identity needs to persist across application restarts
elif constants.is_android:
    UNIQUE_ID = hashlib.sha256(f"{constants.app_title}::{constants.username}::{ID_HASH}::{constants.machine_id}".encode()).hexdigest()

# First, try to get the machine ID using the module
else:
    try:
        import machineid
        UNIQUE_ID = machineid.hashed_id(f'{constants.app_title}::{constants.username}::{ID_HASH}')

    # If machine ID is busted, do it the good ol' fashioned way
    except:
        import uuid
        UNIQUE_ID = str(uuid.getnode()).ljust(64, '0')
""",
        "use persistent Android Telepath identity",
    )


def patch_desktop_init(source):
    path = source / "ui" / "desktop" / "init.py"

    replace_once(
        path,
        """Config.set('graphics', 'window_state', 'hidden')
Config.set('kivy', 'exit_on_escape', '0')



# Import Kivy elements & helpers
""",
        """Config.set('graphics', 'window_state', 'hidden')
Config.set('kivy', 'exit_on_escape', '0')

import runtime
runtime.configure_kivy(Config)



# Import Kivy elements & helpers
""",
        "install Android window and input configuration before Kivy Window import",
    )

    replace_once(
        path,
        """from source.ui.desktop import utility
from kivy.metrics import dp
""",
        """from source.ui.desktop import utility
runtime.bind_utility(utility)
from kivy.metrics import dp
""",
        "bind Android logical resolution to desktop UI utility",
    )

    replace_once(
        path,
        """    def _configure_window(self):
        if self.configured_window: return self.configured_window

        try:
""",
        """    def _configure_window(self):
        if constants.is_android:
            utility.window_size = runtime.window_size
            self.configured_window = True
            return True

        if self.configured_window: return self.configured_window

        try:
""",
        "skip desktop window positioning on Android",
    )

    replace_once(
        path,
        """        if constants.app_config.fullscreen: Window.maximize()
        Window.show()

        # Raise window, and configure again after if it failed
        def raise_window(*a):
            Window.raise_window()
            Window._update_density_and_dpi()
            self._configure_window()
        Clock.schedule_once(raise_window, 0)
""",
        """        if not constants.is_android:
            if constants.app_config.fullscreen: Window.maximize()
            Window.show()

            # Raise window, and configure again after if it failed
            def raise_window(*a):
                Window.raise_window()
                Window._update_density_and_dpi()
                self._configure_window()
            Clock.schedule_once(raise_window, 0)
""",
        "skip desktop show/maximize/raise operations on Android",
    )


def patch_buttons(source):
    path = source / "ui" / "desktop" / "widgets" / "buttons.py"

    replace_once(
        path,
        """    def onPressed(self, instance, touch):
        if touch.device == "wm_touch": touch.button = "left"

        self.button_pressed = touch.button
""",
        """    def onPressed(self, instance, touch):
        if touch.device == "wm_touch" or constants.is_android:
            touch.button = "left"

        self.button_pressed = touch.button
""",
        "normalize Android button presses to left click",
    )


def patch_templates(source):
    path = source / "ui" / "desktop" / "views" / "templates.py"

    replace_once(
        path,
        """        # Keyboard yumminess
        self._input_focused = False
        self._keyboard = Window.request_keyboard(None, self, 'text')
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        self._keyboard.bind(on_key_up=self._on_keyboard_up)
""",
        """        # Keyboard yumminess
        self._input_focused = False
        if not constants.is_android:
            self._keyboard = Window.request_keyboard(None, self, 'text')
            self._keyboard.bind(on_key_down=self._on_keyboard_down)
            self._keyboard.bind(on_key_up=self._on_keyboard_up)
""",
        "skip desktop keyboard capture on Android",
    )


def patch_utility(source):
    path = source / "ui" / "desktop" / "utility.py"

    replace_once(
        path,
        """            # filechooser.open_file() implements plyer's Win32FileChooser class for Windows
            if constants.os_name == 'windows':
                final_path = filechooser.open_file(title=title, filters=ext, path=iter_start_dir(start_dir), multiple=select_multiple, icon=file_icon)


            # Use the 'xdg-desktop-portal' spec helper for Linux
            elif constants.os_name == 'linux':
""",
        """            # Android uses Plyer's native file chooser rather than the Linux portal path.
            if constants.is_android:
                final_path = filechooser.open_file(title=title, filters=ext, path=start_dir, multiple=select_multiple)
                if isinstance(final_path, str) and final_path:
                    final_path = [final_path]

            # filechooser.open_file() implements plyer's Win32FileChooser class for Windows
            elif constants.os_name == 'windows':
                final_path = filechooser.open_file(title=title, filters=ext, path=iter_start_dir(start_dir), multiple=select_multiple, icon=file_icon)


            # Use the 'xdg-desktop-portal' spec helper for Linux
            elif constants.os_name == 'linux':
""",
        "route Android file selection through Plyer",
    )

    replace_once(
        path,
        """            # Use tkinter's filedialog only on Windows, it's a better UI than plyer's Win32FileChooser for directories
            if constants.os_name == "windows":
""",
        """            # Android uses Plyer's native directory chooser.
            if constants.is_android:
                selected = filechooser.choose_dir(title=title, path=start_dir)
                final_path = selected[0] if isinstance(selected, (list, tuple)) and selected else selected or ''

            # Use tkinter's filedialog only on Windows, it's a better UI than plyer's Win32FileChooser for directories
            elif constants.os_name == "windows":
""",
        "route Android directory selection through Plyer",
    )

    replace_once(
        path,
        """    try:
        send_log('open_folder', f"opening '{path}' in file browser")

        def q(p: str) -> str:
""",
        """    try:
        send_log('open_folder', f"opening '{path}' in file browser")

        if constants.is_android:
            return False

        def q(p: str) -> str:
""",
        "prevent desktop file-browser commands on Android",
    )


def validate(stage):
    source = stage / "source"

    targets = [
        source / "core" / "constants.py",
        source / "core" / "telepath.py",
        source / "ui" / "desktop" / "init.py",
        source / "ui" / "desktop" / "utility.py",
        source / "ui" / "desktop" / "widgets" / "buttons.py",
        source / "ui" / "desktop" / "views" / "templates.py",
        stage / "main.py",
        stage / "runtime.py",
        stage / "psutil.py",
    ]

    for path in targets:
        py_compile.compile(str(path), doraise=True)

    print("[android patch] Python syntax validation passed")


def main():
    if len(sys.argv) != 2:
        fail("Usage: apply.py <staged-app-root>")

    stage = Path(sys.argv[1]).resolve()
    source = stage / "source"

    if not source.is_dir():
        fail(f"Missing staged source directory: '{source}'")

    patch_constants(source)
    patch_telepath(source)
    patch_desktop_init(source)
    patch_buttons(source)
    patch_templates(source)
    patch_utility(source)
    validate(stage)

    print(f"[android patch] Done (baseline {baseline})")


if __name__ == "__main__":
    main()
