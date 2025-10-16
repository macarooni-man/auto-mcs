from source.ui.desktop.views.templates import *
from source.ui.desktop.widgets.base import *



# ================================================== Main Menu =========================================================
# <editor-fold desc="Main Menu">

shown_disk_error = False

class MainMenuScreen(MenuBackground):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.loaded = False
        self.settings_bar = None

    # Prompt update/show banner when starting up
    def on_enter(self, *args):
        global shown_disk_error


        # Show warning if running with elevated permissions, and flag is used
        if constants.is_admin() and constants.bypass_admin_warning:
            def admin_error(*_):
                self.show_popup(
                    "warning",
                    "Privilege Warning",
                    f"Running auto-mcs as ${'administrator' if constants.os_name == 'windows' else 'root'}$ can expose your system to security vulnerabilities.\n\nProceed with caution, this configuration is unsupported",
                    None
                )
            Clock.schedule_once(admin_error, 0.5)
            return


        # Close if running with elevated permissions, and flag is not used
        elif constants.is_admin():
            def admin_error(*_):
                self.show_popup(
                    "warning",
                    "Privilege Error",
                    f"Running auto-mcs as ${'administrator' if constants.os_name == 'windows' else 'root'}$ can expose your system to security vulnerabilities.\n\nPlease restart with standard user privileges to continue",
                    Window.close
                )
            Clock.schedule_once(admin_error, 0.5)
            return


        # Close on macOS when it's running in DMG
        elif constants.os_name == 'macos' and (paths.launch_path.startswith('/Volumes/') and constants.app_title in paths.launch_path):
            def dmg_error(*_):
                self.show_popup(
                    "warning",
                    "Permission Error",
                    f"Please move $auto-mcs$ to the Applications folder to continue",
                    Window.close
                )
            Clock.schedule_once(dmg_error, 0.5)
            return


        # Show warning when disk is full
        elif not constants.check_free_space() and not shown_disk_error:
            shown_disk_error = True
            def disk_error(*_):
                self.show_popup(
                    "warning",
                    "Storage Error",
                    "auto-mcs has limited functionality from low disk space. Further changes can lead to corruption in your servers.\n\nPlease free up space on your disk to minimize issues",
                    None
                )
            Clock.schedule_once(disk_error, 0.5)


        if constants.update_data['reboot-msg']:
            message = constants.update_data['reboot-msg']
            fail = message[0] == "banner-failure"
            Clock.schedule_once(
                functools.partial(
                    self.show_banner,
                    (1, 0.5, 0.65, 1) if fail else (0.553, 0.902, 0.675, 1),
                    message[1],
                    "close-circle-sharp.png" if fail else "checkmark-circle-sharp.png",
                    3,
                    {"center_x": 0.5, "center_y": 0.965}
                ), 0.1
            )
            constants.update_data['reboot-msg'] = []
            constants.update_data['auto-show'] = False
        else:
            Clock.schedule_once(functools.partial(self.prompt_update, False), 0.5)

    def prompt_update(self, force=False, *args):

        # Only allow the popup to show if it's on the official release channel
        if not constants.is_official: return

        if (not constants.app_latest) and (constants.update_data['auto-show']) or force:

            # Installs update and restarts
            def install_update(*a):
                def change_screen(*b): utility.screen_manager.current = 'UpdateAppProgressScreen'
                check_running(change_screen)

            if constants.app_online:
                self.show_popup("update", title=None, content=None, callback=(None, install_update))
            constants.update_data['auto-show'] = False

    def open_donate(self, *a):
        if constants.app_online:
            url = "https://www.auto-mcs.com/about-us"
            webbrowser.open_new_tab(url)

    def generate_menu(self, **kwargs):
        # Generate buttons on page load
        buttons = []
        float_layout = FloatLayout()

        utility.screen_manager.screen_tree = []
        constants.server_manager.create_server_list()

        splash = FloatLayout()

        logo = Image(source=os.path.join(paths.ui_assets, 'title.png'), allow_stretch=True, size_hint=(None, None), width=dp(550), pos_hint={"center_x": 0.5, "center_y": 0.77})
        splash.add_widget(logo)

        anim_logo = Image(
            source = os.path.join(paths.ui_assets, 'animations', 'animated_logo.gif'),
            allow_stretch = True,
            size_hint = (None, None),
            width = dp(550),
            pos_hint = {"center_x": 0.5, "center_y": 0.77},
            anim_loop = 1,
            anim_delay = utility.anim_speed * 0.02
        )
        splash.add_widget(anim_logo)


        color = "#FF8793" if constants.is_admin() else (0.6, 0.6, 1, 0.5)
        version = Label(pos=(330, 200), pos_hint={"center_y": 0.77}, color=color, font_name=os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf'), font_size=sp(23))
        version.__translate__ = False
        if not constants.dev_version:
            version_text = constants.app_version
            version.text = f"v{version_text}{(7 - len(version_text)) * '  '}"
        splash.add_widget(version)

        separator = Label(pos_hint={"center_y": 0.7}, color=(0.6, 0.6, 1, 0.1), font_name=os.path.join(paths.ui_assets, 'fonts', 'LLBI.otf'), font_size=sp(25))
        separator.__translate__ = False
        separator.text = "_" * 50
        splash.add_widget(separator)

        session_splash = Label(pos_hint={"center_y": 0.65}, color=(0.6, 0.6, 1, 0.5), font_size=sp(25))
        session_splash.__translate__ = False

        # Display full build data if 'dev_version' instead of splash
        if constants.dev_version:
            session_splash.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
            session_splash.text      = constants.format_version()
        else:
            session_splash.font_name = os.path.join(paths.ui_assets, 'fonts', 'LLBI.otf')
            session_splash.text      = constants.session_splash

        splash.add_widget(session_splash)

        float_layout.add_widget(splash)

        if not constants.server_manager.server_list and not constants.server_manager.online_telepath_servers:
            top_button = MainButton('Create a new server', (0.5, 0.42), 'create-server.png')
            def open_telepath_menu(*a): utility.screen_manager.current = 'TelepathManagerScreen'
            bottom_button = MainButton('Connect Via $Telepath$', (0.5, 0.32), 'telepath.png', click_func=open_telepath_menu)
        else:
            top_button = MainButton('Manage Auto-MCS servers', (0.5, 0.42), 'manage-servers.png')
            bottom_button = MainButton('Create a new server', (0.5, 0.32), 'create-server.png')
        quit_button = ExitButton('Quit', (0.5, 0.17))

        buttons.append(top_button)
        buttons.append(bottom_button)
        buttons.append(quit_button)

        for button in buttons: float_layout.add_widget(button)

        footer = generate_footer('splash', func_dict={'update': functools.partial(self.prompt_update, True), 'donate': self.open_donate})
        float_layout.add_widget(footer)

        self.add_widget(float_layout)

        # Animate for startup yumminess
        def animate_screen(*a):
            if not self.loaded:
                self.loaded = True

                anim_logo.opacity = logo.opacity = 0
                logo_width = logo.width
                anim_logo.width = logo.width = logo.width * 0.97

                version.opacity = 0
                version_x = version.x
                version.x = version.x - 10

                top_button.opacity = 0
                bottom_button.opacity = 0
                quit_button.opacity = 0

                Animation(opacity=1, duration=0.8, width=logo_width, transition='out_quad').start(logo)
                Animation(opacity=1, duration=0.8, width=logo_width, transition='out_quad').start(anim_logo)
                Animation(opacity=1, duration=1, x=version_x, transition='out_sine').start(version)

                def button_1(*b): Animation(opacity=1, duration=0.8, transition='in_out_sine').start(top_button)
                def button_2(*b): Animation(opacity=1, duration=1.1, transition='in_out_sine').start(bottom_button)
                def button_3(*b): Animation(opacity=1, duration=1.4, transition='in_out_sine').start(quit_button)
                Clock.schedule_once(button_1, 0)
                Clock.schedule_once(button_2, 0.1)
                Clock.schedule_once(button_3, 0.2)

                # Animate footer items
                def wait_anim(c, c_y, *b): Animation(duration=0.65, y=c_y, transition='out_circ').start(c)
                def wait_anim_2(w, *b):    Animation(opacity=1, duration=1, transition='out_circ').start(w)
                for x, w in enumerate(reversed(footer.children), 0):
                    w.opacity = 0
                    delay = (x * 0.1) + 0.35
                    for c in w.children:
                        c_y = c.y
                        c.y = c_y - 50
                        Clock.schedule_once(functools.partial(wait_anim, c, c_y), delay)
                    Clock.schedule_once(functools.partial(wait_anim_2, w), delay)


                # Animate sponsor button
                if constants.app_online:

                    # Only show a reminder once per month
                    show_anim = True
                    try:
                        if constants.app_config.sponsor_reminder:
                            if int(dt.now().strftime('%y%m')) == constants.app_config.sponsor_reminder:
                                show_anim = False
                    except: pass

                    if show_anim:
                        constants.app_config.sponsor_reminder = int(dt.now().strftime('%y%m'))
                        def anim(*a):
                            anim_background = Image(
                                source = os.path.join(paths.ui_assets, 'menu_shadow.png'),
                                allow_stretch = True,
                                size_hint = (None, None),
                                width = dp(100),
                                height = dp(100),
                                color = (0.9, 0.65, 1, 0.08)
                            )
                            footer.add_widget(anim_background)
                            anim_background.pos = (88, -18)
                            anim_background.opacity = 0
                            Animation(opacity=1, duration=0.1).start(anim_background)

                            sponsor_anim = Image(
                                source = os.path.join(paths.ui_assets, 'animations', 'sponsor.webp'),
                                allow_stretch = True,
                                size_hint = (None, None),
                                width = dp(50),
                                height = dp(50),
                                anim_loop = 1,
                                anim_delay = utility.anim_speed * 0.02,
                                color = (1, 0.85, 1, 1)
                            )
                            footer.add_widget(sponsor_anim)
                            sponsor_anim.pos = (113, 5)
                            def a(*a):
                                Animation(opacity=0, duration=0.5).start(anim_background)
                                Animation(opacity=0, duration=0.5).start(sponsor_anim)
                            Clock.schedule_once(a, 0.6)
                        Clock.schedule_once(anim, 1.2)

        Clock.schedule_once(animate_screen, 0)

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        # print('The key', keycode, 'have been pressed')
        # print(' - text is %r' % text)
        # print(' - modifiers are %r' % modifiers)

        # Ignore key presses when popup is visible
        if self.popup_widget:

            # Override for PopupSearch
            if self.popup_widget.__class__.__name__ == 'PopupSearch':
                if keycode[1] == 'escape':
                    self.popup_widget.self_destruct(True)
                elif keycode[1] == 'backspace' or ('shift' in modifiers and text and not text.isalnum()):
                    self.popup_widget.resize_window()
                elif control not in modifiers and text and self.popup_widget.window_input.keyboard:

                    def insert_text(content):
                        col = self.popup_widget.window_input.cursor_col
                        start = self.popup_widget.window_input.text[:col]
                        end = self.popup_widget.window_input.text[col:]
                        self.popup_widget.window_input.text = start + content + end
                        for x in range(len(content)):
                            Clock.schedule_once(functools.partial(self.popup_widget.window_input.do_cursor_movement, 'cursor_right', True), 0)

                    new_str = self.popup_widget.window_input.keyboard.keycode_to_string(keycode[0])
                    if 'shift' in modifiers:       new_str = new_str.upper()
                    if len(new_str) == 1:          insert_text(new_str)
                    elif keycode[1] == 'spacebar': insert_text(' ')
                    self.popup_widget.resize_window()

                else: self.popup_widget.resize_window()
                return True

            if keycode[1] in ['escape', 'n']:
                try: self.popup_widget.click_event(self.popup_widget, 'no')
                except AttributeError:
                    self.popup_widget.click_event(self.popup_widget, 'ok')

            elif keycode[1] in ['enter', 'return', 'y']:
                try: self.popup_widget.click_event(self.popup_widget, 'yes')
                except AttributeError:
                    self.popup_widget.click_event(self.popup_widget, 'ok')

            elif keycode[1] == 'spacebar':
                try: self.popup_widget.click_event(self.popup_widget, 'body')
                except AttributeError:
                    pass
            return


        # Force a crash for debugging
        if 'c' in keycode[1] and 'ctrl' in modifiers and 'shift' in modifiers and constants.debug:
            raise Exception('Forced a crash for testing (CTRL-SHIFT-C)')


        # Trigger for showing search bar
        elif keycode[1] == 'shift':
            if not self._shift_held:
                self._shift_held = True
                self._shift_press_count += 1

                if self._shift_timer:
                    self._shift_timer.cancel()

                # Check for double tap
                if self._shift_press_count == 2:
                    self.show_search()
                    self._shift_press_count = 0

                # Otherwise, reset the timer
                else:
                    self._shift_timer = Clock.schedule_once(self._reset_shift_counter, 0.25)  # Adjust time as needed
            return True


        # Quit on macOS
        elif constants.os_name == 'macos' and (keycode[1] == 'q' and control in modifiers):
            utility.app.attempt_to_close()


        # Ignore ESC commands while input focused
        if not self._input_focused and self.name == utility.screen_manager.current_screen.name:

            # Force prompt an update/reinstall on main menu
            if keycode[1] == 'u' and 'shift' in modifiers and 'alt' in modifiers and control in modifiers and not self.popup_widget:
                self.prompt_update(force=True)

            # Keycode is composed of an integer + a string
            # If we hit escape, release the keyboard
            # On ESC, click on back button if it exists
            if keycode[1] == 'escape' and 'escape' not in self._ignore_keys:

                if self.context_menu:
                    self.context_menu.hide()

                else:
                    for button in self.walk():
                        try:
                            if button.id == "exit_button":
                                button.force_click()
                                break
                        except AttributeError:
                            continue
                keyboard.release()

            # Click next button if it's not disabled
            if keycode[1] == 'enter' and 'enter' not in self._ignore_keys:
                for button in self.walk():
                    try:
                        if button.id == "next_button" and button.disabled is False:
                            button.force_click()
                            break
                    except AttributeError:
                        continue
                keyboard.release()

        # # On TAB/Shift+TAB, cycle through elements
        # if keycode[1] == 'tab' and 'tab' not in self._ignore_keys:
        #     pass
        #     # for widget in self.walk():
        #     #     try:
        #     #         if "button" in widget.id or "input" in widget.id:
        #     #             print(widget)
        #     #             break
        #     #     except AttributeError:
        #     #         continue

        # Crash test
        # if keycode[1] == 'z' and control in modifiers:
        #     crash = float("crash")

        # Return True to accept the key. Otherwise, it will be used by the system.
        return True


class CreateServerModeScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'

    def generate_menu(self, **kwargs):
        # Generate buttons on page load
        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'

        float_layout.add_widget(HeaderText("What type of server do you wish to create?", '', (0, 0.86)))

        # Create UI buttons
        buttons.append(ExitButton('Back', (0.5, 0.14), cycle=True))

        # Create type buttons (Page 1)
        row_top = BoxLayout()
        row_bottom = BoxLayout()
        row_top.pos_hint = {"center_y": 0.64, "center_x": 0.5}
        row_bottom.pos_hint = {"center_y": 0.38, "center_x": 0.5}
        row_bottom.size_hint_max_x = row_top.size_hint_max_x = dp(600)
        row_top.orientation = row_bottom.orientation = "horizontal"

        def screen(name, *a):
            foundry.new_server_init()
            utility.screen_manager.current = name

        row_top.add_widget(big_mode_button('create a pre-configured server', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None), 'instant', clickable=True, click_func=functools.partial(screen, 'CreateServerTemplateScreen')))
        row_top.add_widget(big_mode_button('install a modpack', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None), 'modpack', clickable=True, click_func=functools.partial(screen, 'ServerImportModpackScreen')))

        row_bottom.add_widget(big_mode_button('import an existing server', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None), 'import', clickable=True, click_func=functools.partial(screen, 'ServerImportScreen')))
        row_bottom.add_widget(big_mode_button('create a server manually', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None), 'custom', clickable=True, click_func=functools.partial(screen, 'CreateServerNameScreen')))

        float_layout.add_widget(row_top)
        float_layout.add_widget(row_bottom)

        for button in buttons: float_layout.add_widget(button)

        float_layout.add_widget(generate_title('Create New Server'))
        float_layout.add_widget(generate_footer('Create new server'))

        # Async reload Telepath servers
        dTimer(0, constants.server_manager.check_telepath_servers).start()

        self.add_widget(float_layout)


class UpdateAppProgressScreen(ProgressScreen):

    # Only replace this function when making a child screen
    # Set fail message in child functions to trigger an error
    def contents(self):

        def before_func(*args):

            # First, clean out any existing files in temp or downloads
            os.chdir(constants.get_cwd())
            constants.safe_delete(paths.temp)
            constants.safe_delete(paths.downloads)

            if not constants.app_online:
                self.execute_error("An internet connection is required to continue\n\nVerify connectivity and try again")

            elif not constants.check_free_space():
                self.execute_error("Your primary disk is almost full\n\nFree up space and try again")


        def after_func(*args):
            icons = os.path.join(paths.ui_assets, 'fonts', constants.fonts['icons'])
            self.steps.label_2.text = "Update complete! Restarting..." + f"   [font={icons}]å[/font]"

            def process_update_and_close(*a):
                constants.restart_update_app()
                utility.app.attempt_to_close(True)

            Clock.schedule_once(process_update_and_close, 1)

        # Original is percentage before this function, adjusted is a percent of hooked value
        def adjust_percentage(*args):
            original = self.last_progress
            adjusted = args[0]
            total = args[1] * 0.01
            final = original + round(adjusted * total)
            if final < 0: final = original
            self.progress_bar.update_progress(final)

        self.page_contents = {

            # Page name
            'title': f"Updating auto-mcs",

            # Header text
            'header': "Sit back and relax, it's automation time...",

            # Tuple of tuples for steps (label, function, percent)
            # Percent of all functions must total 100
            # Functions must return True, or default error will be executed
            'default_error': 'There was an issue, please try again later',

            'function_list': (),

            # Function to run before steps (like checking for an internet connection)
            'before_function': before_func,

            # Function to run after everything is complete (like cleaning up the screen tree) will only run if no error
            'after_function': after_func,

            # Screen to go to after complete
            'next_screen': None
        }

        # Create function list
        function_list = [
            (f'Downloading auto-mcs v{constants.update_data["version"].strip()}...', functools.partial(constants.download_update, functools.partial(adjust_percentage, 100)), 0)
        ]

        self.page_contents['function_list'] = tuple(function_list)



# App Settings Menu ----------------------------------------------------------------------------------------------------

class AppSettingsScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'

        self.scroll_widget = None
        self.header = None
        self.title_widget = None
        self.footer_widget = None

    def generate_menu(self, **kwargs):

        # Scroll list
        scroll_widget = ScrollViewWidget()
        self.scroll_widget = scroll_widget
        scroll_anchor = AnchorLayout()
        scroll_layout = GridLayout(cols=1, spacing=10, size_hint_max_x=1175, size_hint_y=None, padding=[0, -50, 0, 60])


        # Bind / cleanup height on resize
        def resize_scroll(call_widget, grid_layout, anchor_layout, *args):
            call_widget.height = Window.height // 1.5
            call_widget.pos_hint = {"center_y": 0.5}
            grid_layout.cols = 2 if Window.width > grid_layout.size_hint_max_x else 1

            def update_grid(*args): anchor_layout.size_hint_min_y = grid_layout.height

            Clock.schedule_once(update_grid, 0)


        self.resize_bind = lambda*_: Clock.schedule_once(functools.partial(resize_scroll, scroll_widget, scroll_layout, scroll_anchor), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        scroll_layout.bind(minimum_height=scroll_layout.setter('height'))
        scroll_layout.id = 'scroll_content'

        # Scroll gradient
        scroll_top = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.84}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, 60))
        scroll_bottom = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.17}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, -60))

        # Generate buttons on page load
        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'

        pgh_font = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["mono-medium"]}.otf')

        # Create and add paragraphs to GridLayout
        def create_paragraph(name, layout, cid, center_y):

            sub_layout = ScrollItem()
            content_size = sp(22)
            content_height = sum([(child.height + (layout.spacing[0]*2)) for child in layout.children])
            paragraph = paragraph_object(size=(530, content_height), name=name, content=' ', font_size=content_size, font=pgh_font)
            sub_layout.height = paragraph.height + 80

            sub_layout.add_widget(paragraph)
            sub_layout.add_widget(layout)
            layout.pos_hint = {'center_x': 0.5, 'center_y': center_y}
            scroll_layout.add_widget(sub_layout)


        # ----------------------------------------------- General ------------------------------------------------------

        general_layout = GridLayout(cols=1, spacing=10, size_hint_max_x=1050, size_hint_y=None, padding=[0, 0, 0, 0])


        # Change locale button
        sub_layout = ScrollItem()
        def change_locale_screen(*a): utility.screen_manager.current = 'ChangeLocaleScreen'
        button = WaitButton(get_locale_string(), (0.5, 0.5), 'language.png', click_func=change_locale_screen)
        sub_layout.add_widget(button)
        general_layout.add_widget(sub_layout)


        # Open changelog
        sub_layout = ScrollItem()
        def open_changelog(*a):
            if constants.app_online:
                url = f'{constants.project_repo}/releases/latest'
                webbrowser.open_new_tab(url)
        button = WaitButton('View Changelog', (0.5, 0.5), 'document-text-sharp.png', click_func=open_changelog)
        sub_layout.add_widget(button)
        general_layout.add_widget(sub_layout)


        # Sound mixer
        max_limit = 100
        start_value = max(0, min(100, constants.app_config.master_volume))

        def change_volume(val):
            normalized = max(0, min(100, val))
            constants.app_config.master_volume = normalized

        sub_layout = ScrollItem()
        sub_layout.add_widget(blank_input(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="app volume"))
        sub_layout.add_widget(NumberSlider(start_value, (0.5, 0.5), input_name='SoundMixerInput', limits=(0, max_limit), min_icon='volume-mute.png', max_icon='volume-high.png', function=change_volume, sound={'file': 'popup/normal'}))
        general_layout.add_widget(sub_layout)


        # Enable Discord rich presence toggle switch
        sub_layout = ScrollItem()
        disabled = not constants.app_online
        hint_text = "enable $discord$ presence"
        sub_layout.add_widget(blank_input(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text=hint_text, disabled=disabled))
        sub_layout.add_widget(toggle_button('discord', (0.5, 0.5), custom_func=constants.discord_presence.toggle_presence, disabled=disabled, default_state=constants.app_config.discord_presence))
        general_layout.add_widget(sub_layout)


        create_paragraph('general', general_layout, 0, 0.65)

        # --------------------------------------------------------------------------------------------------------------



        # --------------------------------------------- Management -----------------------------------------------------

        management_layout = GridLayout(cols=1, spacing=10, size_hint_max_x=1050, size_hint_y=None, padding=[0, 0, 0, 0])


        # Open Telepath button
        sub_layout = ScrollItem()
        def telepath_screen(*a): utility.screen_manager.current = 'TelepathManagerScreen'
        open_telepath_button = WaitButton("Manage $Telepath$", (0.5, 0.5), 'telepath.png', click_func=telepath_screen)
        sub_layout.add_widget(open_telepath_button)
        management_layout.add_widget(sub_layout)


        # Open Global amscript manager button
        sub_layout = ScrollItem()
        def amscript_screen(*a): utility.screen_manager.current = 'AmscriptManagerScreen'
        open_telepath_button = WaitButton("Manage $amscript$", (0.5, 0.5), 'amscript.png', click_func=amscript_screen, disabled=True)
        sub_layout.add_widget(open_telepath_button)
        management_layout.add_widget(sub_layout)


        # Change App Path
        # Reset configuration button
        # Delete server button
        def move_app_dir(new_path: str):
            def loading_screen(*a): utility.screen_manager.current = 'BlurredLoadingScreen'
            Clock.schedule_once(loading_screen, 0)

            if not constants.restart_move_app(new_path=new_path):
                def switch_screens(*a):
                    last_error = None
                    for l in logger.log_manager._since_ui:
                        if l['level'] in ['warning', 'error']: last_error = str(l['message'][0].upper() + l['message'][1:])
                    log_data = last_error
                    message_content = f': \n\n{log_data}' if log_data else ''

                    utility.screen_manager.current = "AppSettingsScreen"
                    utility.screen_manager.screen_tree = ['MainMenuScreen']

                    Clock.schedule_once(
                        functools.partial(
                            self.show_popup,
                            "warning",
                            "Move App Directory",
                            f"Unable to move app directory to '{new_path}'{message_content}",
                            (None)
                        ), 0
                    )
                Clock.schedule_once(switch_screens, 0.5)
        def timer_move(new_path: str): dTimer(0, lambda *_: move_app_dir(new_path)).start()
        def select_folder(*a):
            new_path = file_popup("dir", start_dir=(paths.appdata), input_name='migrate_app_dir', select_multiple=False, title="Select where to move the app directory")
            if not new_path: return

            Clock.schedule_once(
                functools.partial(
                    utility.screen_manager.current_screen.show_popup,
                    "warning_query",
                    f"Move App Directory",
                    f"This operation can take a very long time in the background. Don't open auto-mcs again or shut off your computer until it re-opens.\n\nAre you sure you want to continue?",
                    (None, functools.partial(Clock.schedule_once, lambda *_: timer_move(new_path), 0.5))
                ),
                0
            )

        def prompt_move(*args):
            if constants.server_manager.server_list or os.path.isdir(paths.backups):
                Clock.schedule_once(
                    functools.partial(
                        utility.screen_manager.current_screen.show_popup,
                        "warning_query",
                        f"Move App Directory",
                        f"Proceed with caution: this action has the potential to cause data loss.\n\nEnsure back-ups are copied outside of the current app folder if needed.",
                        (None, functools.partial(Clock.schedule_once, select_folder, 0.5))
                    ),
                    0
                )

            else: select_folder()

        sub_layout = ScrollItem()
        move_app_button = WaitButton('Migrate App Directory', (0.5, 0.5), 'migrate.png', click_func=prompt_move)
        sub_layout.add_widget(move_app_button)
        management_layout.add_widget(sub_layout)


        # Reset configuration button
        def reset_config(*args):
            if not constants.app_compiled:
                return Clock.schedule_once(
                    functools.partial(
                        self.show_banner,
                        (0.937, 0.831, 0.62, 1),
                        f"can't restart in script mode",
                        "remove-circle-sharp.png",
                        2.5,
                        {"center_x": 0.5, "center_y": 0.965}
                    ), 0
                )


            # App is compiled
            else:
                def loading_screen(*a): utility.screen_manager.current = 'BlurredLoadingScreen'
                Clock.schedule_once(loading_screen, 0)

                def restart_and_reset(*a): constants.restart_app(['--reset'])
                Clock.schedule_once(restart_and_reset, 0.2)
        def timer_reset(*a): dTimer(0, reset_config).start()
        def prompt_reset(*args):
            Clock.schedule_once(
                functools.partial(
                    utility.screen_manager.current_screen.show_popup,
                    "warning_query",
                    f"Reset Configuration",
                    f"Do you want to restart & reset the ${constants.app_title}$ configuration?\n\nThis will not touch servers, scripts, back-ups, or Telepath",
                    (None, functools.partial(Clock.schedule_once, timer_reset, 0.5))
                ),
                0
            )
        sub_layout = ScrollItem()
        reset_button = ColorButton('Reset Configuration', (0.5, 0.5), 'reload-sharp.png', click_func=prompt_reset, color=(1, 0.5, 0.65, 1), disabled=False)
        sub_layout.add_widget(reset_button)
        management_layout.add_widget(sub_layout)


        create_paragraph('   management   ', management_layout, 1, 0.65)

        # --------------------------------------------------------------------------------------------------------------



        # Append scroll view items
        scroll_anchor.add_widget(scroll_layout)
        scroll_widget.add_widget(scroll_anchor)
        float_layout.add_widget(scroll_widget)
        float_layout.add_widget(scroll_top)
        float_layout.add_widget(scroll_bottom)


        # Configure header
        header_content = f"Modify {constants.app_title} configuration"
        self.header = HeaderText(header_content, '', (0, 0.89))
        float_layout.add_widget(self.header)


        buttons.append(ExitButton('Back', (0.5, 0.12), cycle=True))

        for button in buttons: float_layout.add_widget(button)


        # Button to open app directory
        def open_app_dir(*args):
            open_folder(paths.app_folder)
            Clock.schedule_once(self.open_path_button.button.on_leave, 0.5)

        self.open_path_button = IconButton('open directory', {}, (70, 110), (None, None), 'folder.png', anchor='right', click_func=open_app_dir, text_offset=(10, 0))
        float_layout.add_widget(self.open_path_button)


        self.title_widget = generate_title(f"Settings")
        self.footer_widget = generate_footer(f"Settings", full_version=True)
        self.add_widget(self.title_widget)
        self.add_widget(self.footer_widget)

        self.add_widget(float_layout)


class ChangeLocaleScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'

    def generate_menu(self, **kwargs):

        # Scroll list
        scroll_widget = ScrollViewWidget()
        scroll_widget.pos_hint = {'center_y': 0.485}
        scroll_anchor = AnchorLayout()
        scroll_layout = GridLayout(cols=1, spacing=10, size_hint_max_x=1050, size_hint_y=None, padding=[0, 10, 0, 100])


        # Bind / cleanup height on resize
        def resize_scroll(call_widget, grid_layout, anchor_layout, *args):
            call_widget.height = Window.height // 1.7
            grid_layout.cols = 2 if Window.width > grid_layout.size_hint_max_x else 1

            def update_grid(*args): anchor_layout.size_hint_min_y = grid_layout.height

            Clock.schedule_once(update_grid, 0)


        self.resize_bind = lambda*_: Clock.schedule_once(functools.partial(resize_scroll, scroll_widget, scroll_layout, scroll_anchor), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        scroll_layout.bind(minimum_height=scroll_layout.setter('height'))
        scroll_layout.id = 'scroll_content'

        # Scroll gradient
        scroll_top = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.77}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, 60))
        scroll_bottom = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.21}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, -60))

        # Generate buttons on page load
        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'
        float_layout.add_widget(HeaderText("Select a language", '', (0, 0.86)))

        class LocaleButton(MainButton):

            def on_press(self, *a):
                constants.app_config.locale = self.code
                size_list()
                utility.back_clicked = True
                utility.screen_manager.previous_screen()
                utility.back_clicked = False
                Clock.schedule_once(
                    functools.partial(
                        utility.screen_manager.current_screen.show_banner,
                        (0.85, 0.65, 1, 1),
                        f"Switched language to ${re.sub(r' +', ' ', self.text.text)}$",
                        "language-sharp.png",
                        2,
                        {"center_x": 0.5, "center_y": 0.965}
                    ), 0
                )

            def on_leave(self, *a):
                def change_background(*a): self.button.background_normal = os.path.join(paths.ui_assets, 'addon_button_installed.png')
                Clock.schedule_once(change_background, 0.08)

            def __init__(self, name, code='en', **args):

                self.code = code
                in_use = self.code == constants.app_config.locale

                icon = 'checkmark-sharp.png' if in_use else 'arrow-forward.png'

                super().__init__(name, position=(0, 0), icon_name=icon, **args)
                self.text.__translate__ = False
                self.text.text = name

                self.button.on_press = self.on_press

                if in_use:
                    self.button.color_id[1] = (0.6, 1, 0.8, 1)
                    self.button.bind(on_leave=self.on_leave)
                    self.text.color = self.icon.color = self.button.color_id[1]
                    self.on_leave()


        # Create a button for each available language
        for k, v in available_locales.items():

            sub_layout = ScrollItem()
            locale_title = f'{v["name"].title()}   ({v["code"].upper()})'
            sub_layout.add_widget(LocaleButton(name=locale_title, pos_hint={"center_x": 1, "center_y": 0.5}, code=v["code"]))
            scroll_layout.add_widget(sub_layout)


        # Append scroll view items
        scroll_anchor.add_widget(scroll_layout)
        scroll_widget.add_widget(scroll_anchor)
        float_layout.add_widget(scroll_widget)
        float_layout.add_widget(scroll_top)
        float_layout.add_widget(scroll_bottom)


        buttons.append(ExitButton('Back', (0.5, 0.12), cycle=True))

        for button in buttons: float_layout.add_widget(button)

        menu_name = "Language"
        float_layout.add_widget(generate_title(menu_name))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)


# </editor-fold> ///////////////////////////////////////////////////////////////////////////////////////////////////////
