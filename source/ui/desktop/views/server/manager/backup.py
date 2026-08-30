from source.ui.desktop.views.server.manager.components import *



# Server Back-up Manager -----------------------------------------------------------------------------------------------

class ServerBackupScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'

        self.save_backup_button = None
        self.restore_backup_button = None
        self.open_path_button = None
        self.migrate_path_button = None
        self.download_button = None
        self.clone_button = None

        self.header = None
        self.menu_taskbar = None

    def solo_button(self, button_name, loading=True, *args):
        server_obj = constants.server_manager.current_server

        button_dict = {
            'save': self.save_backup_button,
            'restore': self.restore_backup_button,
            'migrate': self.migrate_path_button
        }

        for k, v in button_dict.items():
            # print(server_obj.backup._backup_stats['backup-list'])
            if k == 'restore' and not server_obj.backup._backup_stats['backup-list']:
                v.disable(True)
                if self.download_button: self.download_button.disable(True)
                continue

            if k == 'migrate' and server_obj._telepath_data:
                continue

            if k == button_name: v.loading(True) if loading else v.loading(False)
            else:                v.disable(True) if loading else v.disable(False)

    def generate_menu(self, **kwargs):
        server_obj = constants.server_manager.current_server

        # Return if no free space
        if disk_popup('ServerViewScreen', telepath_data=server_obj._telepath_data):
            return

        server_obj.backup._update_data()
        backup_stats = server_obj.backup._backup_stats
        very_bold_font = os.path.join(paths.ui_assets, 'fonts', constants.fonts["very-bold"])

        # Retain button persistence when disabled
        if server_obj.name in backup.backup_lock:
            Clock.schedule_once(functools.partial(self.solo_button, backup.backup_lock[server_obj.name], True), 0)
        else:
            Clock.schedule_once(functools.partial(self.solo_button, None, False), 0)

        # Scroll list
        scroll_widget = ScrollViewWidget(position=(0.5, 0.485))
        scroll_anchor = AnchorLayout()
        scroll_layout = GridLayout(cols=1, spacing=10, size_hint_max_x=1050, size_hint_y=None, padding=[0, 16, 0, 30])

        # Bind / cleanup height on resize
        def resize_scroll(call_widget, grid_layout, anchor_layout, *args):
            call_widget.height = Window.height // 1.6
            grid_layout.cols = 2 if Window.width > grid_layout.size_hint_max_x else 1
            scroll_layout.spacing = 30 if grid_layout.cols == 2 else 10

            def update_grid(*args):
                anchor_layout.size_hint_min_y = grid_layout.height
                scroll_top.resize(); scroll_bottom.resize()

            Clock.schedule_once(update_grid, 0)

        self.resize_bind = lambda *_: Clock.schedule_once(functools.partial(resize_scroll, scroll_widget, scroll_layout, scroll_anchor), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        scroll_layout.bind(minimum_height=scroll_layout.setter('height'))
        scroll_layout.id = 'scroll_content'

        # Scroll gradient
        scroll_top = ScrollBackground(pos_hint={"center_x": 0.5, "center_y": 0.8}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, 60))
        scroll_bottom = ScrollBackground(pos_hint={"center_x": 0.5, "center_y": 0.17}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, -60))

        # Generate buttons on page load
        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'

        # Save back-up button
        def save_backup(*args):

            def run_backup(*args):

                # Run back-up
                Clock.schedule_once(functools.partial(self.solo_button, 'save', True), 0)
                backup_data = server_obj.backup.save()

                # Failed to save backup
                if not backup_data:
                    Clock.schedule_once(
                        functools.partial(
                            self.show_banner,
                            (1, 0.5, 0.65, 1),
                            f"Failed to save a back-up, check log for details",
                            "close-circle-outline.png",
                            2.5,
                            {"center_x": 0.5, "center_y": 0.965}
                        ), 0
                    )

                # Successfully saved backup
                else:

                    # Update header
                    def change_header(*args):
                        backup_stats = server_obj.backup._backup_stats
                        backup_count = len(backup_stats['backup-list'])
                        header_content = f"{translate('Latest Back-up')}  [color=#494977]-[/color]  " + (f'[color=#6A6ABA]{translate("Never")}[/color]' if not backup_stats['latest-backup'] else f'[font={very_bold_font}]{backup_stats["latest-backup"]}[/font]')
                        sub_header_content = f"{backup_count:,}  back-up" + ("" if backup_count == 1 else "s") + (f"   ({backup_stats['total-size']})" if backup_count > 0 else "")
                        self.header.text.text = header_content
                        self.header.lower_text.text = sub_header_content
                    Clock.schedule_once(change_header, 0)

                    Clock.schedule_once(
                        functools.partial(
                            self.show_banner,
                            (0.553, 0.902, 0.675, 1),
                            f"Backed up '${server_obj.name}$' successfully",
                            "checkmark-circle-sharp.png",
                            2.5,
                            {"center_x": 0.5, "center_y": 0.965}
                        ), 0
                    )

                # Update buttons
                Clock.schedule_once(functools.partial(self.solo_button, 'save', False), 0)

            dTimer(0, run_backup).start()

        sub_layout = ScrollItem()
        self.save_backup_button = WaitButton('Save Back-up Now', (0.5, 0.5), 'save-sharp.png', click_func=save_backup)
        sub_layout.add_widget(self.save_backup_button)
        scroll_layout.add_widget(sub_layout)

        # Restore back-up button
        sub_layout = ScrollItem()
        self.restore_backup_button = WaitButton('Restore From Back-up', (0.5, 0.5), 'reload-sharp.png', disabled=server_obj.running)
        sub_layout.add_widget(self.restore_backup_button)
        scroll_layout.add_widget(sub_layout)

        # Auto-backup toggle
        start_value = False if str(backup_stats['auto-backup']) == 'prompt' else str(backup_stats['auto-backup']) == 'true'

        def toggle_auto(var):
            server_obj.backup.enable_auto_backup(var)

            Clock.schedule_once(
                functools.partial(
                    self.show_banner,
                    (0.553, 0.902, 0.675, 1) if var else (0.937, 0.831, 0.62, 1),
                    f"Automatic back-ups {'en' if var else 'dis'}abled",
                    "checkmark-circle-sharp.png" if var else "close-circle-sharp.png",
                    2,
                    {"center_x": 0.5, "center_y": 0.965}
                ), 0
            )

        sub_layout = ScrollItem()
        sub_layout.add_widget(BlankInput(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="automatic back-ups"))
        sub_layout.add_widget(SwitchButton('auto-backup', (0.5, 0.5), default_state=start_value, custom_func=toggle_auto))
        scroll_layout.add_widget(sub_layout)

        # Maximum back-up slider
        max_limit = 11
        start_value = max_limit if str(backup_stats['max-backup']) == 'unlimited' else int(backup_stats['max-backup'])

        def change_limit(val): server_obj.backup.set_amount('unlimited' if val == max_limit else val)
        sub_layout = ScrollItem()
        sub_layout.add_widget(BlankInput(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="maximum back-ups"))
        sub_layout.add_widget(NumberSlider(start_value, (0.5, 0.5), input_name='BackupMaxInput', limits=(2, max_limit), max_icon='infinite-bold.png', function=change_limit))
        scroll_layout.add_widget(sub_layout)

        # Maximum log size slider (MB); top of the range disables purging
        log_max = 2000
        start_log = log_max if str(backup_stats['max-log-size']) == 'unlimited' else int(backup_stats['max-log-size'])

        def change_log_limit(val): server_obj.backup.set_log_amount('unlimited' if val == log_max else val)
        sub_layout = ScrollItem()
        sub_layout.add_widget(BlankInput(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="maximum log size (MB)"))
        sub_layout.add_widget(NumberSlider(start_log, (0.5, 0.5), input_name='BackupLogMaxInput', limits=(50, log_max), step=50, max_icon='infinite-bold.png', function=change_log_limit))
        scroll_layout.add_widget(sub_layout)

        if server_obj._telepath_data:

            # Download a back-up
            def download_backup(*args): Clock.schedule_once(self.download_button.button.on_leave, 0.5)
            sub_layout = ScrollItem()
            self.download_button = WaitButton('Download a Back-up', (0.5, 0.5), 'cloud-download-sharp.png', click_func=download_backup)
            sub_layout.add_widget(self.download_button)
            scroll_layout.add_widget(sub_layout)


        # Only apply these buttons on a local server
        else:
            # Open back-up directory
            def open_backup_dir(*args):
                backup_stats = server_obj.backup._backup_stats
                open_folder(backup_stats['backup-path'])
                Clock.schedule_once(self.open_path_button.button.on_leave, 0.5)

            self.open_path_button = IconButton('open directory', {}, (70, 110), (None, None), 'folder.png', anchor='right', click_func=open_backup_dir, text_offset=(10, 0))
            float_layout.add_widget(self.open_path_button)

            # Migrate back-up directory
            def change_backup_dir(*args):
                backup_stats = server_obj.backup._backup_stats
                current_path = backup_stats['backup-path']
                new_path = file_popup("dir", start_dir=(current_path if os.path.exists(current_path) else paths.backups), select_multiple=False, title="Select a New Back-up Directory")
                Clock.schedule_once(self.open_path_button.button.on_leave, 0.5)

                def run_migrate(*args):
                    Clock.schedule_once(functools.partial(self.solo_button, 'migrate', True), 0)
                    final_path = server_obj.backup.set_directory(new_path)

                    # Show banner and update button
                    Clock.schedule_once(functools.partial(self.solo_button, 'migrate', False), 0)

                    if final_path:
                        Clock.schedule_once(
                            functools.partial(
                                self.show_banner,
                                (0.553, 0.902, 0.675, 1),
                                "Migrated back-up directory successfully",
                                "checkmark-circle-sharp.png",
                                2.5,
                                {"center_x": 0.5, "center_y": 0.965}
                            ), 0
                        )
                    else:
                        Clock.schedule_once(
                            functools.partial(
                                self.show_banner,
                                (1, 0.53, 0.58, 1),
                                "Failed to migrate back-up directory",
                                "close-circle.png",
                                2.5,
                                {"center_x": 0.5, "center_y": 0.965}
                            ), 0
                        )

                # If path was selected, migrate folder
                if new_path: dTimer(0, run_migrate).start()

            sub_layout = ScrollItem()
            self.migrate_path_button = WaitButton('Migrate Back-up Directory', (0.5, 0.5), 'migrate.png', click_func=change_backup_dir)
            sub_layout.add_widget(self.migrate_path_button)
            scroll_layout.add_widget(sub_layout)

        # Clone server button
        def clone_server(*args): utility.screen_manager.current = 'ServerCloneScreen'
        sub_layout = ScrollItem()
        self.clone_button = WaitButton('Clone this server', (0.5, 0.5), 'duplicate-outline.png', click_func=clone_server)
        sub_layout.add_widget(self.clone_button)
        scroll_layout.add_widget(sub_layout)

        # Append scroll view items
        scroll_anchor.add_widget(scroll_layout)
        scroll_widget.add_widget(scroll_anchor)
        float_layout.add_widget(scroll_widget)
        float_layout.add_widget(scroll_top)
        float_layout.add_widget(scroll_bottom)

        # Configure header
        # print(backup_stats)
        backup_count = len(backup_stats['backup-list'])
        header_content = f"{translate('Latest Back-up')}  [color=#494977]-[/color]  " + (f'[color=#6A6ABA]{translate("Never")}[/color]' if not backup_stats['latest-backup'] else f'[font={very_bold_font}]{backup_stats["latest-backup"]}[/font]')
        sub_header_content = f"{backup_count:,}  back-up" + ("" if backup_count == 1 else "s") + (f"   ({backup_stats['total-size']})" if backup_count > 0 else "")
        self.header = HeaderText(header_content, sub_header_content, (0, 0.89), __translate__=(False, True))
        float_layout.add_widget(self.header)

        buttons.append(ExitButton('Back', (0.5, -1), cycle=True))

        for button in buttons: float_layout.add_widget(button)

        float_layout.add_widget(generate_title(f"Back-up Manager: '{server_obj.name}'"))
        float_layout.add_widget(generate_footer(f"{server_obj.name}, Back-ups"))

        self.add_widget(float_layout)

        # Add ManuTaskbar
        self.menu_taskbar = MenuTaskbar(selected_item='back-ups')
        self.add_widget(self.menu_taskbar)


class ServerBackupRestoreScreen(ListHistoryLayout, MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.restore_button = None


    def restore_backup(self, *args):
        if not self.selected_item: return

        server_obj = constants.server_manager.current_server
        backup_object = self.selected_item


        def restore_screen(file, stop=False, *args):

            def run_restore():
                if stop:
                    server_obj.silent_command('stop')
                    while server_obj.running: time.sleep(0.2)

                server_obj.backup._restore_file = file
                Clock.schedule_once(lambda *_: setattr(utility.screen_manager, 'current', 'ServerBackupRestoreProgressScreen'), 0)

            dTimer(0, run_restore).start()


        if server_obj.running:
            self.show_popup(
                'query',
                'Stop & Restore Back-up',
                f"Are you sure you want to stop and revert '{backup_object.name}' to {backup_object.date}?\n\nThis action can't be undone",
                [None, functools.partial(restore_screen, backup_object, True)]
            )

        else:
            self.show_popup(
                'query',
                'Restore Back-up',
                f"Are you sure you want to revert '${backup_object.name}$' to ${backup_object.date}$?\n\nThis action can't be undone",
                [None, functools.partial(restore_screen, backup_object, False)]
            )


    def generate_menu(self, **kwargs):
        server_obj = constants.server_manager.current_server
        backup_list = server_obj.backup.return_backup_list()

        self.generate_history(backup_list, 'Select a back-up to restore')

        float_layout = self._layout


        # Back
        back_button = ExitButton('Back', (0.215, 0.5), cycle=True)
        back_button.icon.size_hint = (None, None)
        back_button.icon.size = (dp(26), dp(26))
        back_button.icon.pos_hint = {}


        # Restore
        self.restore_button = NextButton(
            '    Restore',
            (0.736, 0.5),
            disabled = not bool(backup_list),
            click_func = lambda: Clock.schedule_once(self.restore_backup, 0)
        )

        self.restore_button.icon.source = icon_path('reload-sharp.png')
        self.restore_button.icon.size_hint = (None, None)
        self.restore_button.icon.size = (dp(28), dp(28))
        self.restore_button.icon.pos_hint = {}
        self.restore_button.icon.opacity = 1

        self.attach_history_actions(back_button, self.restore_button)


        # Title / footer
        float_layout.add_widget(generate_title(f"Back-up Manager: '{server_obj.name}'"))
        float_layout.add_widget(generate_footer(f"{server_obj.name}, Back-ups, Restore"))

        self.add_widget(float_layout)


class ServerBackupDownloadScreen(ListHistoryLayout, MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.download_action_button = None


    def download_backup(self, *args):
        if not self.selected_item: return

        server_obj = constants.server_manager.current_server
        backup_object = self.selected_item

        if not server_obj._telepath_data:
            return


        # Return to Back-up Manager while downloading
        utility.screen_manager.current = 'ServerBackupScreen'


        def download_thread():
            if utility.screen_manager.current_screen.name == 'ServerBackupScreen':
                download_button = utility.screen_manager.current_screen.download_button
                if download_button:
                    Clock.schedule_once(functools.partial(download_button.loading, True), 0)

            location = constants.telepath_download(
                server_obj._telepath_data,
                backup_object.path,
                paths.user_downloads
            )

            if os.path.exists(location):
                open_folder(location)

                Clock.schedule_once(
                    functools.partial(
                        utility.screen_manager.current_screen.show_banner,
                        (0.553, 0.902, 0.675, 1),
                        'Downloaded back-up successfully',
                        'cloud-download-sharp.png',
                        3,
                        {'center_x': 0.5, 'center_y': 0.965}
                    ),
                    1
                )

            if utility.screen_manager.current_screen.name == 'ServerBackupScreen':
                download_button = utility.screen_manager.current_screen.download_button
                if download_button:
                    Clock.schedule_once(functools.partial(download_button.loading, False), 0)

        dTimer(0, download_thread).start()


    def generate_menu(self, **kwargs):
        server_obj = constants.server_manager.current_server
        backup_list = server_obj.backup.return_backup_list()

        self.generate_history(backup_list, 'Select a back-up to download')

        float_layout = self._layout


        # Back
        back_button = ExitButton('Back', (0.215, 0.5), cycle=True)
        back_button.icon.size_hint = (None, None)
        back_button.icon.size = (dp(26), dp(26))
        back_button.icon.pos_hint = {}


        # Download
        self.download_action_button = NextButton(
            '    Download',
            (0.736, 0.5),
            disabled = not bool(backup_list),
            click_func = lambda: Clock.schedule_once(self.download_backup, 0)
        )

        self.download_action_button.icon.source = icon_path('cloud-download-sharp.png')
        self.download_action_button.icon.size_hint = (None, None)
        self.download_action_button.icon.size = (dp(28), dp(28))
        self.download_action_button.icon.pos_hint = {}
        self.download_action_button.icon.opacity = 1

        self.attach_history_actions(back_button, self.download_action_button)


        # Title / footer
        float_layout.add_widget(generate_title(f"Back-up Manager: '{server_obj.name}'"))
        float_layout.add_widget(generate_footer(f"{server_obj.name}, Back-ups, Download"))

        self.add_widget(float_layout)


class ServerBackupRestoreProgressScreen(ProgressScreen):

    # Only replace this function when making a child screen
    # Set fail message in child functions to trigger an error
    def contents(self):
        def before_func(*args):
            # First, clean out any existing server in temp folder
            os.chdir(constants.get_cwd())
            constants.safe_delete(paths.temp)
            constants.folder_check(paths.tmpsvr)

        def after_func(server_obj, restore_date):
            message = f"'${server_obj.name}$' was restored to ${restore_date}$"
            self.open_server(server_obj.name, True, message)

        # Original is percentage before this function, adjusted is a percent of hooked value
        def adjust_percentage(*args):
            original = self.last_progress
            adjusted = args[0]
            total = args[1] * 0.01
            final = original + round(adjusted * total)
            if final < 0: final = original
            self.progress_bar.update_progress(final)

        server_obj = constants.server_manager.current_server
        restore_file = server_obj.backup._restore_file
        restore_date = server_obj.backup._restore_file.date
        self.page_contents = {

            # Page name
            'title': f"Restoring '${server_obj.name}$'",

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
            'after_function': functools.partial(after_func, server_obj, restore_date),

            # Screen to go to after complete
            'next_screen': None
        }

        # Create function list
        function_list = [
            ('Restoring back-up', functools.partial(foundry.restore_server, restore_file, functools.partial(adjust_percentage, 100)), 0),
        ]

        self.page_contents['function_list'] = tuple(function_list)


class ServerCloneScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'
        self.name_input = None

    def generate_menu(self, **kwargs):

        # Return if no free space or telepath is busy
        if disk_popup():
            return
        if telepath_popup():
            return

        # Generate buttons on page load
        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'
        foundry.new_server_init()
        foundry.import_data = {'name': None, 'path': None}
        server_obj = constants.server_manager.current_server

        # Regular menu
        float_layout.add_widget(InputLabel(pos_hint={"center_x": 0.5, "center_y": 0.58}))
        float_layout.add_widget(HeaderText("What would you like to name the copy?", '', (0, 0.76)))
        self.name_input = ServerNameInput(pos_hint={"center_x": 0.5, "center_y": 0.5}, text=server_obj.name)
        float_layout.add_widget(self.name_input)

        def start_clone(*a): Clock.schedule_once(lambda *_: setattr(utility.screen_manager, 'current', 'ServerCloneProgressScreen'), 0)
        self.next_button = NextButton('Clone', (0.5, 0.24), False, click_func=start_clone)
        buttons.append(self.next_button)
        buttons.append(ExitButton('Back', (0.5, 0.14), cycle=True))

        for button in buttons: float_layout.add_widget(button)

        # Add telepath button if servers are connected
        if constants.server_manager.online_telepath_servers:
            float_layout.add_widget(TelepathDropButton('clone', (0.5, 0.4)))

        float_layout.add_widget(generate_title(f"Back-up Manager: '{server_obj.name}'"))
        float_layout.add_widget(generate_footer(f"{server_obj.name}, Back-ups, Clone"))

        self.add_widget(float_layout)
        self.name_input.grab_focus()
        Clock.schedule_once(functools.partial(self.name_input.on_enter, self.name_input.text, False), 0)


class ServerCloneProgressScreen(ProgressScreen):

    # Only replace this function when making a child screen
    # Set fail message in child functions to trigger an error
    def contents(self):
        server_name = foundry.new_server_info['name']
        open_after = functools.partial(self.open_server, server_name, True, f"'${server_name}$' was created successfully")

        def before_func(*args):

            if not constants.check_free_space(telepath_data=foundry.new_server_info['_telepath_data']):
                self.execute_error("Your primary disk is almost full\n\nFree up space and try again")

            else: foundry.pre_server_create()

        def after_func(*args):
            foundry.post_server_create()
            open_after()

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
            'title': f"Creating '{server_name}'",

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
        server_obj = constants.server_manager.current_server
        java_text = 'Verifying Java Installation' if os.path.exists(paths.java) else 'Installing Java'

        # If remote data, open remote server after
        # print(foundry.new_server_info)
        if foundry.new_server_info['_telepath_data']:
            self._telepath_override = foundry.new_server_info['_telepath_data']

        # If not remote data, restore server manager open server on error
        else:
            self._telepath_override = '$local'

            def restore_server(): constants.server_manager.current_server = server_obj
            self._error_callback = restore_server

        function_list = [
            ('Saving a back-up', server_obj.backup.save, 20),
            ('Cloning server', functools.partial(manager.clone_server, server_obj, functools.partial(adjust_percentage, 60)), 0),
            ('Creating initial back-up', functools.partial(foundry.create_backup, True), 20)
        ]

        self.page_contents['function_list'] = tuple(function_list)
