# Android-only source transformations
# Application & validation live in 'apply.py'

def register(source, SourcePatch):

    # ----------------------------------------------- core/constants.py -------------------------------------------------
    constants = SourcePatch(source / 'core' / 'constants.py')

    # Expose an Android runtime flag only inside the generated source tree.
    constants.replace(
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
        'add Android runtime flag',
    )

    # Keep the generated application state in Android-private storage.
    constants.replace(
        """    user_home:            str = os.path.expanduser('~')
    user_downloads:       str = os.path.join(user_home, 'Downloads')
""",
        """    user_home:            str = os.environ.get("ANDROID_PRIVATE", os.path.expanduser('~')) if is_android else os.path.expanduser('~')
    user_downloads:       str = os.path.join(user_home, 'Downloads')
""",
        'use Android private storage as home',
    )

    # Do not create the normal hidden Linux-style application directory on Android.
    constants.replace(
        """    app_folder:           str = os.path.join(appdata, ('.auto-mcs' if os_name != 'macos' else 'auto-mcs'))
""",
        """    app_folder:           str = os.path.join(appdata, ('auto-mcs' if (os_name == 'macos' or is_android) else '.auto-mcs'))
""",
        'use non-hidden Android app data directory',
    )

    # /tmp is not a suitable writable application temp directory on Android.
    constants.replace(
        """    os_temp:              str = os.getenv("TEMP") if os_name == "windows" else "/tmp"
""",
        """    os_temp:              str = os.path.join(user_home, 'tmp') if is_android else os.getenv("TEMP") if os_name == "windows" else "/tmp"
""",
        'keep Android temporary files in private storage',
    )

    # Report Android release/API data instead of presenting the runtime as Linux.
    constants.replace(
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
        version, api = runtime.os_version()

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
        'report Android platform information',
    )


    # ----------------------------------------------- core/telepath.py --------------------------------------------------
    telepath = SourcePatch(source / 'core' / 'telepath.py')

    # Build Telepath identity from the persistent Settings.Secure.ANDROID_ID.
    telepath.replace(
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
        'use persistent Android Telepath identity',
    )


    # --------------------------------------------- ui/desktop/init.py --------------------------------------------------
    init = SourcePatch(source / 'ui' / 'desktop' / 'init.py')

    # Configure the logical Android window before Kivy imports Window.
    init.replace(
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
        'install Android window and input configuration before Kivy Window import',
    )

    # Bind desktop utility sizing to the logical Android surface size.
    init.replace(
        """from source.ui.desktop import utility
from kivy.metrics import dp
""",
        """from source.ui.desktop import utility
runtime.bind_utility(utility)
from kivy.metrics import dp
""",
        'bind Android logical resolution to desktop UI utility',
    )

    # Skip desktop monitor positioning and use the already-configured Android surface.
    init.replace(
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
        'skip desktop window positioning on Android',
    )

    # Android owns the native window; do not show/maximize/raise it through desktop Kivy paths.
    init.replace(
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
        'skip desktop show/maximize/raise operations on Android',
    )


    # ----------------------------------------- ui/desktop/widgets/buttons.py -------------------------------------------
    buttons = SourcePatch(source / 'ui' / 'desktop' / 'widgets' / 'buttons.py')

    # SDL touch events need to behave as normal left-clicks for the desktop widgets.
    buttons.replace(
        """    def onPressed(self, instance, touch):
        if touch.device == "wm_touch": touch.button = "left"

        self.button_pressed = touch.button
""",
        """    def onPressed(self, instance, touch):
        if touch.device == "wm_touch" or constants.is_android:
            touch.button = "left"

        self.button_pressed = touch.button
""",
        'normalize Android button presses to left click',
    )


    # ----------------------------------------- ui/desktop/views/templates.py ------------------------------------------
    templates = SourcePatch(source / 'ui' / 'desktop' / 'views' / 'templates.py')

    # Android should use the native soft keyboard rather than Kivy desktop keyboard capture.
    templates.replace(
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
        'skip desktop keyboard capture on Android',
    )


    # --------------------------------------------- ui/desktop/utility.py -----------------------------------------------
    utility = SourcePatch(source / 'ui' / 'desktop' / 'utility.py')

    # Route file selection through Plyer's Android-native picker before desktop OS handling.
    utility.replace(
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
        'route Android file selection through Plyer',
    )

    # Route directory selection through Plyer's Android-native picker.
    utility.replace(
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
        'route Android directory selection through Plyer',
    )

    # Android has no desktop file browser command equivalent for this helper.
    utility.replace(
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
        'prevent desktop file-browser commands on Android',
    )
