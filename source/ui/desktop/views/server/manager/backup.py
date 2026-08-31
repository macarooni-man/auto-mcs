from source.ui.desktop.views.server.manager.components import *



# Server Back-up Manager -----------------------------------------------------------------------------------------------

class ServerBackupScreen(ListHistoryLayout, MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.page_actions = None
        self.create_button = None
        self.settings_button = None
        self.create_load_icon = None

    def load_backup_metadata(self):

        def load():
            server_obj = constants.server_manager.current_server
            metadata = server_obj.backup.return_backup_list(True)

            def finish(*args):
                nonlocal metadata
                if utility.screen_manager.current != self.name:
                    return

                metadata = {
                    item.path: item
                    for item in metadata
                }

                for item in self.history_results:
                    loaded = metadata.get(item.path)

                    if loaded:
                        item.type = loaded.type
                        item.version = loaded.version
                        item.build = loaded.build
                        item.metadata_loaded = loaded.metadata_loaded

                self.refresh_history_items()

            Clock.schedule_once(finish, 0)

        dTimer(0, load).start()

    def generate_history_actions(self, item, index):
        server_obj = constants.server_manager.current_server

        actions = [('restore', 'reload-sharp.png', functools.partial(self.restore_backup, item))]
        if server_obj._telepath_data:
            actions.append(('download', 'cloud-download-sharp.png', functools.partial(self.download_backup, item)))
        actions.append(('delete', 'trash-sharp.png', functools.partial(self.delete_backup, item), {'force_color': [[(0.05, 0.05, 0.1, 1), (0.6, 0.6, 1, 1)], 'pink']}))
        return actions

    def generate_page_actions(self):
        server_obj = constants.server_manager.current_server
        button_width = 55
        button_spacing = 5

        self.settings_button = RelativeIconButton(
            '\n\n\nsettings', {'center_x': 0.5, 'center_y': 0.5}, None, (None, None), 'settings-sharp.png',
            click_func = lambda: setattr(utility.screen_manager, 'current', 'ServerBackupSettingsScreen')
        )

        self.create_button = RelativeIconButton(
            '\n\n\nsave', {'center_x': 0.5, 'center_y': 0.5}, None, (None, None), 'save-sharp.png',
            click_func = self.create_backup
        )
        self.create_button.button.background_disabled_normal = self.create_button.button.background_normal

        # Same loading animation used by WaitButton
        self.create_load_icon = AsyncImage(
            source = os.path.join(paths.ui_assets, 'animations', 'loading_pickaxe.gif'),
            color = (0.6, 0.6, 1, 1),
            size_hint = (None, None),
            size = (40, 40),
            pos_hint = {'center_x': 0.5, 'center_y': 0.5},
            opacity = 0
        )
        self.create_load_icon.anim_delay = utility.anim_speed * 0.02
        self.create_load_icon.id = 'create_load_icon'
        self.create_button.add_widget(self.create_load_icon)

        self.page_actions = BoxLayout(
            orientation = 'horizontal',
            spacing = button_spacing,
            size_hint = (None, None),
            size = ((button_width * 2) + button_spacing, 55)
        )

        for button in (self.settings_button, self.create_button):
            button.size_hint = (None, None)
            button.size = (button_width, 55)
            self.page_actions.add_widget(button)

        self.selection_layout.add_widget(self.page_actions)

        self.set_create_loading(server_obj.backup.is_backing_up())
        Clock.schedule_once(self.resize_history, 0)

    def set_create_loading(self, loading):
        if not self.create_button: return

        if loading:
            self.create_button.button.on_leave(duration=0)

        self.create_button.button.disabled = loading
        self.create_button.button.ignore_hover = loading
        self.create_button.icon.opacity = 0 if loading else 1
        self.create_load_icon.opacity = 1 if loading else 0

    def history_selection_center(self, action_top):
        return (Window.width / 2, Window.height * 0.89)

    def history_vertical_bounds(self):
        return self.selection_layout.y - dp(12), max(dp(72), Window.height * 0.11)

    def resize_history(self, *args):
        super().resize_history(*args)
        if not self.page_actions: return

        metadata_width = 260
        action_gap = -6

        group_width = metadata_width + action_gap + self.page_actions.width
        group_left = (self.selection_layout.width - group_width) / 2

        for label in (self.selection_date, self.selection_details):
            label.size_hint = (None, None)
            label.pos_hint = {}
            label.width = metadata_width
            label.halign = 'center'

        self.selection_date.height = 25
        self.selection_date.pos = (group_left, 22)

        self.selection_details.height = 20
        self.selection_details.pos = (group_left, 2)

        self.page_actions.pos = (group_left + metadata_width + action_gap, -4)

    def create_backup(self, *args):
        server_obj = constants.server_manager.current_server

        if server_obj.backup.is_backing_up():
            return

        if disk_popup('ServerBackupScreen', telepath_data=server_obj._telepath_data):
            return

        self.set_create_loading(True)

        def run_backup():
            backup_data = server_obj.backup.save()

            def finish(*args):
                self.set_create_loading(False)

                if utility.screen_manager.current != self.name:
                    return

                if backup_data:
                    self.gen_history_results(server_obj.backup.return_backup_list(False))

                    self.show_banner(
                        (0.553, 0.902, 0.675, 1),
                        f"Backed up '${server_obj.name}$' successfully",
                        'checkmark-circle-sharp.png',
                        2.5,
                        {'center_x': 0.5, 'center_y': 0.965}
                    )

                    self.load_backup_metadata()

                else:
                    self.show_banner(
                        (1, 0.5, 0.65, 1),
                        'Failed to save a back-up, check log for details',
                        'close-circle-outline.png',
                        2.5,
                        {'center_x': 0.5, 'center_y': 0.965}
                    )

            Clock.schedule_once(finish, 0)

        dTimer(0, run_backup).start()

    def restore_backup(self, backup_object, *args):
        server_obj = constants.server_manager.current_server

        def restore_screen(file, stop=False, *args):

            def run_restore():
                if stop:
                    server_obj.silent_command('stop')
                    while server_obj.running:
                        time.sleep(0.2)

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

    def download_backup(self, backup_object, *args):
        server_obj = constants.server_manager.current_server

        if not server_obj._telepath_data:
            return

        def download_thread():
            location = constants.telepath_download(server_obj._telepath_data, backup_object.path, paths.user_downloads)
            if os.path.exists(location):
                open_folder(location)

                Clock.schedule_once(
                    functools.partial(
                        self.show_banner,
                        (0.553, 0.902, 0.675, 1),
                        'Downloaded back-up successfully',
                        'cloud-download-sharp.png',
                        3,
                        {'center_x': 0.5, 'center_y': 0.965}
                    ),
                    0
                )

        dTimer(0, download_thread).start()

    def delete_backup(self, backup_object, *args):

        def delete(*args):
            server_obj = constants.server_manager.current_server
            old_index = self.selected_index

            def run_delete():
                success = server_obj.backup.delete(backup_object)

                def finish(*args):
                    if utility.screen_manager.current != self.name:
                        return

                    if success:
                        self.gen_history_results(server_obj.backup.return_backup_list(False))
                        if self.history_results:
                            self.select_history(min(old_index, len(self.history_results) - 1), False)

                        self.show_banner(
                            (0.553, 0.902, 0.675, 1),
                            'Deleted back-up successfully',
                            'checkmark-circle-sharp.png',
                            2.5,
                            {'center_x': 0.5, 'center_y': 0.965}
                        )

                    else:
                        self.show_banner(
                            (1, 0.5, 0.65, 1),
                            'Failed to delete back-up',
                            'close-circle-outline.png',
                            2.5,
                            {'center_x': 0.5, 'center_y': 0.965}
                        )

                Clock.schedule_once(finish, 0)

            dTimer(0, run_delete).start()

        self.show_popup(
            'warning_query',
            'Delete Back-up',
            f"Are you sure you want to permanently delete the back-up from ${backup_object.date}$?\n\nThis action can't be undone",
            [None, delete]
        )

    def generate_menu(self, **kwargs):
        server_obj = constants.server_manager.current_server

        # Shallow list appears immediately
        backup_list = server_obj.backup.return_backup_list(False)

        self.generate_history(backup_list, 'Back-up History')

        float_layout = self._layout
        float_layout.remove_widget(self.header)

        self.generate_page_actions()

        float_layout.add_widget(generate_title(f"Back-up Manager: '{server_obj.name}'"))
        float_layout.add_widget(generate_footer(f"{server_obj.name}, Back-ups"))

        self.add_widget(float_layout)

        self.menu_taskbar = MenuTaskbar(selected_item='back-ups')
        self.add_widget(self.menu_taskbar)

        # Fill in version/type/build asynchronously
        self.load_backup_metadata()


class ServerBackupSettingsScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.name = self.__class__.__name__
        self.menu = 'init'

        self.open_path_button = None
        self.migrate_path_button = None
        self.clone_button = None

        self.header = None
        self.menu_taskbar = None
        self.resize_bind = None

    def generate_menu(self, **kwargs):
        server_obj = constants.server_manager.current_server

        server_obj.backup._update_data()
        backup_stats = server_obj.backup._backup_stats
        very_bold_font = os.path.join(paths.ui_assets, 'fonts', constants.fonts["very-bold"])


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
                scroll_top.resize()
                scroll_bottom.resize()

            Clock.schedule_once(update_grid, 0)

        self.resize_bind = lambda *_: Clock.schedule_once(functools.partial(resize_scroll, scroll_widget, scroll_layout, scroll_anchor), 0)

        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)

        scroll_layout.bind(minimum_height=scroll_layout.setter('height'))
        scroll_layout.id = 'scroll_content'


        # Scroll gradient
        scroll_top = ScrollBackground(pos_hint={"center_x": 0.5, "center_y": 0.8}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, 60))
        scroll_bottom = ScrollBackground(pos_hint={"center_x": 0.5, "center_y": 0.17}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, -60))

        float_layout = FloatLayout()
        float_layout.id = 'content'


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

        def change_limit(val):
            server_obj.backup.set_amount('unlimited' if val == max_limit else val)

        sub_layout = ScrollItem()
        sub_layout.add_widget(BlankInput(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="maximum back-ups"))
        sub_layout.add_widget(NumberSlider(start_value, (0.5, 0.5), input_name='BackupMaxInput', limits=(2, max_limit), max_icon='infinite-bold.png', function=change_limit))
        scroll_layout.add_widget(sub_layout)


        # Log retention slider; top of the range disables cleanup
        log_max = 20
        start_value = log_max if str(backup_stats['log-size-limit']) == 'unlimited' else max(
            1,
            min(log_max - 1, int(backup_stats['log-size-limit']) // 100)
        )

        def change_log_limit(val):
            server_obj.backup.set_log_limit('unlimited' if val == log_max else val * 100)

        def format_log_limit(val):
            return f'{val / 10:g}'

        sub_layout = ScrollItem()
        sub_layout.add_widget(BlankInput(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="log retention (GB)"))
        sub_layout.add_widget(NumberSlider(start_value, (0.5, 0.5), input_name='BackupLogLimitInput', limits=(1, log_max), max_icon='infinite-bold.png', function=change_log_limit, display_func=format_log_limit))
        scroll_layout.add_widget(sub_layout)


        # Local back-up directory controls
        if not server_obj._telepath_data:

            def open_backup_dir(*args):
                backup_stats = server_obj.backup._backup_stats
                open_folder(backup_stats['backup-path'])
                Clock.schedule_once(self.open_path_button.button.on_leave, 0.5)

            self.open_path_button = IconButton('open directory', {}, (70, 110), (None, None), 'folder.png', anchor='right', click_func=open_backup_dir, text_offset=(10, 0))

            def change_backup_dir(*args):
                backup_stats = server_obj.backup._backup_stats
                current_path = backup_stats['backup-path']

                new_path = file_popup("dir", start_dir=(current_path if os.path.exists(current_path) else paths.backups), select_multiple=False, title="Select a New Back-up Directory")
                if not new_path:
                    return


                def run_migrate(*args):
                    Clock.schedule_once(
                        lambda *_: self.migrate_path_button.loading(True), 0
                    )

                    final_path = server_obj.backup.set_directory(new_path)

                    def finish(*args):
                        self.migrate_path_button.loading(False)

                        if final_path:
                            self.show_banner(
                                (0.553, 0.902, 0.675, 1),
                                "Migrated back-up directory successfully",
                                "checkmark-circle-sharp.png",
                                2.5,
                                {"center_x": 0.5, "center_y": 0.965}
                            )

                        else:
                            self.show_banner(
                                (1, 0.53, 0.58, 1),
                                "Failed to migrate back-up directory",
                                "close-circle.png",
                                2.5,
                                {"center_x": 0.5, "center_y": 0.965}
                            )

                    Clock.schedule_once(finish, 0)

                dTimer(0, run_migrate).start()


            sub_layout = ScrollItem()
            self.migrate_path_button = WaitButton('Migrate Back-up Directory', (0.5, 0.5), 'migrate.png', click_func=change_backup_dir)
            sub_layout.add_widget(self.migrate_path_button)
            scroll_layout.add_widget(sub_layout)


        # Clone server
        def clone_server(*args):
            utility.screen_manager.current = 'ServerCloneScreen'

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


        # Back-up summary
        backup_count = len(backup_stats['backup-list'])
        header_content = (
            f"{translate('Latest Back-up')}  [color=#494977]-[/color]  "
            + (
                f'[color=#6A6ABA]{translate("Never")}[/color]'
                if not backup_stats['latest-backup']
                else f'[font={very_bold_font}]{backup_stats["latest-backup"]}[/font]'
            )
        )

        sub_header_content = (
            f"{backup_count:,}  back-up"
            + ("" if backup_count == 1 else "s")
            + (f"   ({backup_stats['total-size']})" if backup_count > 0 else "")
        )

        self.header = HeaderText(header_content, sub_header_content, (0, 0.89), __translate__=(False, True))
        float_layout.add_widget(self.header)

        if not server_obj._telepath_data:
            float_layout.add_widget(self.open_path_button)

        # Back
        float_layout.add_widget(ExitButton('Back', (0.5, 0.11), cycle=True))


        # Title / footer
        float_layout.add_widget(generate_title(f"Back-up Settings: '{server_obj.name}'"))
        float_layout.add_widget(generate_footer(f"{server_obj.name}, Back-ups, Settings"))
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
