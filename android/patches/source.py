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

    # Stage user-facing Telepath downloads privately before publishing through Android
    constants.prepend(
        'telepath_download',
        """android_export = is_android and os.path.normpath(destination) == os.path.normpath(paths.user_downloads)
if android_export: destination = paths.downloads""",
        'stage user-facing Telepath downloads privately on Android',
    )

    constants.before_return(
        'telepath_download',
        'final_path',
        """if android_export:
    import runtime
    exported_path = runtime.export_download(final_path)
    if not exported_path: raise RuntimeError(f"Failed to export Android download '{final_path}'")
    safe_delete(final_path)
    final_path = exported_path""",
        'publish user-facing Telepath downloads through Android Downloads',
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

    # Override back/'ESC' handling and configure runtime display rotation
    # init.prepend(
    #     'MainApp.on_start',
    #     """if constants.is_android:
    # runtime.bind_escape(Window, utility)
    # runtime.bind_rotation(utility)""",
    #     'install Android runtime navigation and rotation handlers',
    # )
    # Portrait support - runtime.bind_rotation(utility)
    # Look at 232efba0c71328f2d97d487a4a37de86d66a905e to restore portrait
    init.prepend(
        'MainApp.on_start',
        """if constants.is_android:
        runtime.bind_escape(Window, utility)""",
        'route Android escape through normal UI navigation',
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

    # Android dimensions change dynamically with device orientation
    init.guard_object(
        'MainApp.__init__',
        'Window.minimum_width',
        'not constants.is_android',
        'skip desktop minimum width on Android',
    )

    init.guard_object(
        'MainApp.__init__',
        'Window.minimum_height',
        'not constants.is_android',
        'skip desktop minimum height on Android',
    )

    # Skip native desktop window operations
    init.guard_call('MainApp.build', 'Window.maximize', 'not constants.is_android', 'skip desktop maximize operation on Android')
    init.guard_call('MainApp.build', 'Window.show', 'not constants.is_android', 'skip desktop show operation on Android')
    init.guard_call('MainApp.build', 'Clock.schedule_once', 'not constants.is_android', 'skip desktop raise operation on Android', args=['raise_window'])


    # ------------------------------------------ ui/desktop/widgets/pages.py --------------------------------------------
    pages = SourcePatch(source / 'ui' / 'desktop' / 'widgets' / 'pages.py')

    # Extend the page header behind Android's status bar
    pages.set(
        'HeaderBackground.y_offset',
        'dp(70)',
        'extend Android page header behind status bar',
    )

    # Center and constrain titles within the taller Android header
    pages.prepend(
        'generate_title',
        """center_header = True
font_size = sp(30)
y_offset = dp(3)
if width_ratio is None:
    width_ratio = 0.48""",
        'configure Android page title layout',
    )


    # ----------------------------------------- ui/desktop/views/templates.py ------------------------------------------
    templates = SourcePatch(source / 'ui' / 'desktop' / 'views' / 'templates.py')

    # Match Android system-bar foreground to the rendered page header
    templates.prepend(
        'MenuBackground.on_pre_enter',
        """if constants.is_android:
    import runtime
    Clock.schedule_once(lambda *_: runtime.configure_system_bars(), 0)""",
        'match Android system bars to current page',
    )

    # Android uses the native soft keyboard instead of desktop keyboard capture
    templates.guard_object(
        'MenuBackground.on_pre_enter',
        'self._keyboard',
        'not constants.is_android',
        'skip desktop keyboard capture on Android',
    )

    # Shift banners down in portrait mode to not interfere with the system nav
    templates.prepend(
        'MenuBackground.show_banner',
        """if constants.is_android and Window.height > Window.width:
        pos_hint = dict(pos_hint)
        max_center_y = 1 - ((HeaderBackground.y_offset + 23.5) / Window.height)
        pos_hint['center_y'] = min(pos_hint.get('center_y', 0.895), max_center_y)""",
        'keep portrait banners below Android header',
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

    # Hide unsupported Android directory buttons
    buttons.prepend(
        'IconButton.__init__',
        """if constants.is_android and name.strip().lower() == 'open directory':
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (0, 0)
        self.opacity = 0
        self.disabled = True
        return""",
        'hide unsupported Android directory buttons',
    )


    # ----------------------------------------- ui/desktop/widgets/inputs.py --------------------------------------------
    inputs = SourcePatch(source / 'ui' / 'desktop' / 'widgets' / 'inputs.py')

    # Center focused inputs in the visible area above the Android keyboard
    inputs.prepend(
        'BaseInput._on_focus',
        """if constants.is_android:
        popup = getattr(utility.screen_manager.current_screen, 'popup_widget', None)
        if not (popup and getattr(popup, 'window_input', None) is self):
            import runtime
            runtime.set_keyboard_target(self, value, utility.screen_manager.current_screen.background_color)""",
        'position Android content around the focused input',
    )

    # Hack for canvas input
    inputs.prepend(
        'BaseInput.insert_text',
        """if constants.is_android:
        popup = getattr(utility.screen_manager.current_screen, 'popup_widget', None)
        if popup and getattr(popup, 'window_input', None) is self:
            return super().insert_text(substring, from_undo)""",
        'allow Android global search input typing',
    )


    # ----------------------------------------- ui/desktop/widgets/popups.py --------------------------------------------
    popups = SourcePatch(source / 'ui' / 'desktop' / 'widgets' / 'popups.py')

    # PopupSearch is intentionally rendered through a detached canvas hierarchy
    # Keep its search field near the top on Android instead
    popups.prepend(
        'PopupSearch.resize',
        """if constants.is_android:
        self.window.size = self.window_background.size
        input_margin = 200
        input_center_y = Window.height - input_margin - (self.window_input.height / 2)
        self.window.pos = (
            Window.width / 2 - self.window_background.width / 2,
            input_center_y - self.window.height / 2
        )
        if self.shown:
            Clock.schedule_once(self.generate_blur_background, 0.1)
        return""",
        'anchor Android global search near the top of the screen',
    )


    # -------------------------------- ui/desktop/views/server/manager/console.py --------------------------------------
    console = SourcePatch(source / 'ui' / 'desktop' / 'views' / 'server' / 'manager' / 'console.py')

    # ConsoleInput bypasses BaseInput, so route it through Android IME tracking separately
    console.prepend(
        'ConsolePanel.ConsoleInput._on_focus',
        """if constants.is_android:
    import runtime
    runtime.set_keyboard_target(self, value, utility.screen_manager.current_screen.background_color)""",
        'track Android console input keyboard position',
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
