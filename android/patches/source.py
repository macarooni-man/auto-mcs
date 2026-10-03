# Android-only source transformations
# Application & validation live in 'apply.py'

def register(source, SourcePatch):

    # ----------------------------------------------- core/constants.py -------------------------------------------------
    constants = SourcePatch(source / 'core' / 'constants.py')

    # Expose Android before paths are evaluated
    constants.before(
        'paths',
        """# Android is injected only into the generated build tree.
is_android = os.environ.get("AUTO_MCS_ANDROID") == "1" """,
        'add Android runtime flag',
    )

    # Store application data in Android-private storage
    constants.set(
        'paths.user_home',
        "os.environ.get('ANDROID_PRIVATE', os.path.expanduser('~')) if is_android else os.path.expanduser('~')",
        'use Android private storage as home',
    )
    constants.set(
        'paths.app_folder',
        "os.path.join(appdata, ('auto-mcs' if (os_name == 'macos' or is_android) else '.auto-mcs'))",
        'use non-hidden Android app data directory',
    )
    constants.set(
        'paths.os_temp',
        "os.path.join(user_home, 'tmp') if is_android else os.getenv('TEMP') if os_name == 'windows' else '/tmp'",
        'keep Android temporary files in private storage',
    )

    # Report Android release/API data instead of presenting the runtime as Linux
    constants.after_assignment(
        'format_os',
        'arch',
        """if is_android:
    import runtime
    version, api = runtime.os_version()

    if version and api:
        return f"Android {version} (API {api}, {arch})"
    elif version:
        return f"Android {version} ({arch})"
    else:
        return f"Android ({arch})" """,
        'report Android platform information',
    )


    # ----------------------------------------------- core/telepath.py --------------------------------------------------
    telepath = SourcePatch(source / 'core' / 'telepath.py')

    # Persist the final Telepath identity independently of application updates
    telepath.elif_(
        'constants.is_docker',
        'constants.is_android',
        """import runtime
UNIQUE_ID = runtime.telepath_id(constants.app_title, constants.username, ID_HASH)""",
        'use persistent Android Telepath identity',
    )


    # --------------------------------------------- ui/desktop/init.py --------------------------------------------------
    init = SourcePatch(source / 'ui' / 'desktop' / 'init.py')

    # Configure the Android surface before desktop utility initializes Kivy Window
    init.before_import(
        'source.ui.desktop.utility',
        """import runtime
runtime.configure_kivy(Config)""",
        'install Android window and input configuration before Kivy Window import',
    )

    # Bind desktop utility sizing to the Android logical resolution
    init.after_import(
        'source.ui.desktop',
        """runtime.bind_utility(utility)
Window.softinput_mode = 'below_target'""",
        'bind Android logical resolution and soft keyboard behavior',
        name = 'utility',
    )

    # Android owns native window sizing/positioning
    init.prepend(
        'MainApp._configure_window',
        """if constants.is_android:
    utility.window_size = runtime.window_size
    self.configured_window = True
    return True""",
        'skip desktop window positioning on Android',
    )

    # Skip native desktop window operations
    init.guard_call('MainApp.build', 'Window.maximize', 'not constants.is_android', 'skip desktop maximize operation on Android')
    init.guard_call('MainApp.build', 'Window.show', 'not constants.is_android', 'skip desktop show operation on Android')
    init.guard_call('MainApp.build', 'Clock.schedule_once', 'not constants.is_android', 'skip desktop raise operation on Android', args=['raise_window'])


    # ----------------------------------------- ui/desktop/views/templates.py ------------------------------------------
    templates = SourcePatch(source / 'ui' / 'desktop' / 'views' / 'templates.py')

    # Android uses the native soft keyboard instead of desktop keyboard capture
    templates.guard_object(
        'MenuBackground.on_pre_enter',
        'self._keyboard',
        'not constants.is_android',
        'skip desktop keyboard capture on Android',
    )


    # ----------------------------------------- ui/desktop/widgets/inputs.py --------------------------------------------
    inputs = SourcePatch(source / 'ui' / 'desktop' / 'widgets' / 'inputs.py')

    # Match the exposed keyboard-pan area to the footer background
    inputs.prepend(
        'BaseInput._on_focus',
        """if constants.is_android:
    Window.clearcolor = constants.brighten_color(constants.background_color, -0.02) if value else constants.background_color""",
        'match Android keyboard background to footer',
    )


    # --------------------------------------------- ui/desktop/utility.py -----------------------------------------------
    utility = SourcePatch(source / 'ui' / 'desktop' / 'utility.py')

    # Route file/directory selection through Plyer before desktop platform handling
    utility.platform(
        'file_popup',
        'ask_type == "file"',
        """final_path = filechooser.open_file(title=title, filters=ext, path=start_dir, multiple=select_multiple)
if isinstance(final_path, str) and final_path:
    final_path = [final_path]""",
        'route Android file selection through Plyer',
    )

    utility.platform(
        'file_popup',
        'ask_type == "dir"',
        """selected = filechooser.choose_dir(title=title, path=start_dir)
final_path = selected[0] if isinstance(selected, (list, tuple)) and selected else selected or ''""",
        'route Android directory selection through Plyer',
    )

    # Android has no desktop file-browser command equivalent
    utility.prepend(
        'open_folder',
        """if constants.is_android:
    send_log('open_folder', f"opening '{path}' in file browser")
    return False""",
        'prevent desktop file-browser commands on Android',
    )
