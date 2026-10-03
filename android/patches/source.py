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
        'runtime.bind_utility(utility)',
        'bind Android logical resolution to desktop UI utility',
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


    # ------------------------------------------ ui/desktop/widgets/base.py ---------------------------------------------
    base = SourcePatch(source / 'ui' / 'desktop' / 'widgets' / 'base.py')

    # Android touch scrolling should stop cleanly at list boundaries
    base.prepend(
        'ScrollBehavior.__init__',
        """if constants.is_android:
    kwargs.setdefault('effect_cls', ScrollEffect)""",
        'disable Android touch overscroll',
    )


    # ----------------------------------------- ui/desktop/widgets/menus.py --------------------------------------------
    menus = SourcePatch(source / 'ui' / 'desktop' / 'widgets' / 'menus.py')

    # FadeDrop bypasses ScrollBehavior, so disable its touch overscroll separately
    menus.prepend(
        'DropButton.FadeDrop.__init__',
        """if constants.is_android:
    kwargs.setdefault('effect_cls', ScrollEffect)""",
        'disable Android dropdown overscroll',
    )

    # Keep an expanded dropdown visually hovered until it closes
    menus.prepend(
        'DropButton.toggle_background',
        """if constants.is_android and boolean and not self.loading:
    self.button.ignore_hover = False
    self.button.on_enter()""",
        'preserve Android dropdown hover while expanded',
    )


    # ----------------------------------------- ui/desktop/widgets/buttons.py -------------------------------------------
    buttons = SourcePatch(source / 'ui' / 'desktop' / 'widgets' / 'buttons.py')

    # Android does not create the desktop keyboard listener
    buttons.remove_call(
        'HoverButton.force_click',
        'utility.screen_manager.current_screen._keyboard.release',
        'skip desktop keyboard release on Android',
    )


    # ----------------------------------------- ui/desktop/widgets/inputs.py --------------------------------------------
    inputs = SourcePatch(source / 'ui' / 'desktop' / 'widgets' / 'inputs.py')

    # Center focused inputs in the visible area above the Android keyboard
    inputs.prepend(
        'BaseInput._on_focus',
        """if constants.is_android:
    import runtime
    runtime.set_keyboard_target(self, value, constants.background_color)""",
        'position Android content around the focused input',
    )


    # --------------------------------------------- ui/desktop/utility.py -----------------------------------------------
    utility = SourcePatch(source / 'ui' / 'desktop' / 'utility.py')

    # Route file/directory selection through the native Android document picker
    utility.platform(
        'file_popup',
        'ask_type == "file"',
        """import runtime
final_path = runtime.file_popup('file', start_dir=start_dir, ext=ext, select_multiple=select_multiple, title=title)""",
        'route Android file selection through native document picker',
    )

    utility.platform(
        'file_popup',
        'ask_type == "dir"',
        """import runtime
final_path = runtime.file_popup('dir', start_dir=start_dir, ext=ext, select_multiple=False, title=title)""",
        'route Android directory selection through native document picker',
    )

    # Android has no desktop file-browser command equivalent
    utility.prepend(
        'open_folder',
        """if constants.is_android:
    send_log('open_folder', f"opening '{path}' in file browser")
    return False""",
        'prevent desktop file-browser commands on Android',
    )
