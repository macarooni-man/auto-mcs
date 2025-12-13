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
                server_obj.backup.save()

                # Update header
                def change_header(*args):
                    backup_stats = server_obj.backup._backup_stats
                    backup_count = len(backup_stats['backup-list'])
                    header_content = f"{translate('Latest Back-up')}  [color=#494977]-[/color]  " + (f'[color=#6A6ABA]{translate("Never")}[/color]' if not backup_stats['latest-backup'] else f'[font={very_bold_font}]{backup_stats["latest-backup"]}[/font]')
                    sub_header_content = f"{backup_count:,}  back-up" + ("" if backup_count == 1 else "s") + (f"   ({backup_stats['total-size']})" if backup_count > 0 else "")
                    self.header.text.text = header_content
                    self.header.lower_text.text = sub_header_content

                Clock.schedule_once(change_header, 0)

                # Show banner and update button
                Clock.schedule_once(functools.partial(self.solo_button, 'save', False), 0)

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
                new_path = file_popup("dir", start_dir=(current_path if os.path.exists(current_path) else paths.backups), input_name='migrate_backup_button', select_multiple=False, title="Select a New Back-up Directory")
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


class BackupButton(HoverButton):

    def animate_button(self, image, color, hover_action, **kwargs):
        image_animate = Animation(duration=0.05)

        Animation(color=color, duration=0.06).start(self.title)
        Animation(color=color, duration=0.06).start(self.index_icon)
        Animation(color=color, duration=0.06).start(self.index_label)
        Animation(color=color, duration=0.06).start(self.subtitle)
        Animation(color=color, duration=0.06).start(self.type_image.image)
        if self.type_image.version_label.__class__.__name__ == "AlignLabel":
            Animation(color=color, duration=0.06).start(self.type_image.version_label)
        Animation(color=color, duration=0.06).start(self.type_image.type_label)

        animate_background(self, image, hover_action)

        image_animate.start(self)

    def resize_self(self, *args):

        # Title and description
        padding = 2.17
        self.title.pos = (self.x + (self.title.text_size[0] / padding) - (0) + 30, self.y + 31)  # - (6)
        self.subtitle.pos = (self.x + (self.subtitle.text_size[0] / padding) - 1 + 30 - 100, self.y + 8)
        self.index_label.pos = (self.x - 19, self.y + 2.5)
        self.index_icon.pos = (self.x + 8, self.y + 18)

        offset = 9.45 if self.type_image.type_label.text in ["vanilla", "paper", "purpur"] \
            else 9.6 if self.type_image.type_label.text == "forge" \
            else 9.35 if self.type_image.type_label.text == "craftbukkit" \
            else 9.55

        self.type_image.image.x = self.width + self.x - (self.type_image.image.width) - 13
        self.type_image.image.y = self.y + ((self.height / 2) - (self.type_image.image.height / 2))

        self.type_image.type_label.x = self.width + self.x - (self.padding_x * offset) - self.type_image.width - 83
        self.type_image.type_label.y = self.y + (self.height * 0.05)

        # Update label
        if self.type_image.version_label.__class__.__name__ == "AlignLabel":
            self.type_image.version_label.x = self.width + self.x - (self.padding_x * offset) - self.type_image.width - 83
            self.type_image.version_label.y = self.y - (self.height / 3.2)

        # Banner version object
        else:
            self.type_image.version_label.x = self.width + self.x - (self.padding_x * offset) - self.type_image.width - 130
            self.type_image.version_label.y = self.y - (self.height / 3.2) - 2

    def __init__(self, backup_object, click_function=None, fade_in=0.0, index=0, **kwargs):
        super().__init__(**kwargs)

        self.properties = backup_object
        self.border = (-5, -5, -5, -5)
        self.color_id = [(0.05, 0.05, 0.1, 1), constants.brighten_color((0.65, 0.65, 1, 1), 0.07)]
        self.pos_hint = {"center_x": 0.5, "center_y": 0.6}
        self.size_hint_max = (580, 80)
        self.id = "server_button"
        self.index = index
        self.newest = (index == 1)

        self.background_normal = os.path.join(paths.ui_assets, f'{self.id}{"_ro" if self.newest else ""}.png')
        self.background_down = os.path.join(paths.ui_assets, f'{self.id}_click.png')

        # Loading stuffs
        self.original_subtitle = backup_object.date
        self.original_font = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["regular"]}.ttf')

        # Title of Server
        self.title = Label()
        self.title.__translate__ = False
        self.title.id = "title"
        self.title.halign = "left"
        self.title.color = self.color_id[1]
        self.title.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
        self.title.font_size = sp(25)
        self.title.text_size = (self.size_hint_max[0] * 0.94, self.size_hint_max[1])
        self.title.shorten = True
        self.title.markup = True
        self.title.shorten_from = "right"
        self.title.max_lines = 1
        self.title.text = backup_object.name
        self.add_widget(self.title)

        # Index Icon
        self.index_icon = Image()
        self.index_icon.id = "index_icon"
        self.index_icon.source = os.path.join(paths.ui_assets, 'icons', 'index-fade.png')
        self.index_icon.keep_ratio = False
        self.index_icon.allow_stretch = True
        self.index_icon.size = (44, 44)
        self.index_icon.color = self.color_id[1]
        self.index_icon.opacity = 0.4 if self.newest else 0.2
        self.add_widget(self.index_icon)

        # Index label
        self.index_label = Label()
        self.index_label.__translate__ = False
        self.index_label.id = "index_label"
        self.index_label.halign = "center"
        self.index_label.color = self.color_id[1]
        self.index_label.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
        self.index_label.font_size = sp(23)
        self.index_label.text_size = (50, 50)
        self.index_label.markup = True
        self.index_label.max_lines = 1
        self.index_label.text = str(self.index)
        self.index_label.opacity = 0.8 if self.newest else 0.5
        self.add_widget(self.index_label)

        # Server last modified date formatted
        self.subtitle = Label()
        self.subtitle.size = (300, 30)
        self.subtitle.id = "subtitle"
        self.subtitle.halign = "left"
        self.subtitle.valign = "center"
        self.subtitle.font_size = sp(21)
        self.subtitle.text_size = (self.size_hint_max[0] * 0.91, self.size_hint_max[1])
        self.subtitle.shorten = True
        self.subtitle.markup = True
        self.subtitle.shorten_from = "right"
        self.subtitle.max_lines = 1
        self.subtitle.color = self.color_id[1]
        self.subtitle.default_opacity = 0.56
        self.subtitle.font_name = self.original_font
        self.subtitle.text = self.original_subtitle
        self.subtitle.opacity = self.subtitle.default_opacity
        self.add_widget(self.subtitle)

        # Type icon and info
        "unknown_small.png"
        self.type_image = RelativeLayout()
        self.type_image.width = 400
        self.type_image.image = Image(source=os.path.join(paths.ui_assets, 'icons', 'big', f'{backup_object.type.lower()}_small.png'))
        self.type_image.image.allow_stretch = True
        self.type_image.image.size_hint_max = (65, 65)
        self.type_image.image.color = self.color_id[1]
        self.type_image.add_widget(self.type_image.image)

        def TemplateLabel():
            template_label = AlignLabel()
            template_label.__translate__ = False
            template_label.halign = "right"
            template_label.valign = "middle"
            template_label.text_size = template_label.size
            template_label.font_size = sp(19)
            template_label.color = self.color_id[1]
            template_label.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
            template_label.width = 150
            return template_label

        self.type_image.version_label = TemplateLabel()
        self.type_image.version_label.color = self.color_id[1]
        if backup_object.build: self.type_image.version_label.text = f'{backup_object.version.lower()} (b-{backup_object.build.lower()})'
        else:                   self.type_image.version_label.text = backup_object.version.lower()
        self.type_image.version_label.opacity = 0.6

        self.type_image.type_label = TemplateLabel()
        self.type_image.type_label.text = backup_object.type.lower().replace("craft", "")
        self.type_image.type_label.font_size = sp(23)
        self.type_image.add_widget(self.type_image.version_label)
        self.type_image.add_widget(self.type_image.type_label)
        self.add_widget(self.type_image)

        self.bind(pos=self.resize_self)

        # If click_function
        if click_function: self.bind(on_press=click_function)

        # Animate opacity
        if fade_in > 0:
            self.opacity = 0
            self.title.opacity = 0

            Animation(opacity=1, duration=fade_in).start(self)
            Animation(opacity=1, duration=fade_in).start(self.title)
            Animation(opacity=self.subtitle.default_opacity, duration=fade_in).start(self.subtitle)

    def on_enter(self, *args):
        if not self.ignore_hover:
            self.animate_button(image=os.path.join(paths.ui_assets, f'{self.id}_hover.png'), color=self.color_id[0], hover_action=True)

    def on_leave(self, *args):
        if not self.ignore_hover:
            self.animate_button(image=os.path.join(paths.ui_assets, f'{self.id}{"_ro" if self.newest else ""}.png'), color=self.color_id[1], hover_action=False)


class ServerBackupRestoreScreen(MenuBackground):

    def switch_page(self, direction):

        if self.max_pages == 1:
            return

        if direction == "right":
            if self.current_page == self.max_pages:
                self.current_page = 1
            else:
                self.current_page += 1

        else:
            if self.current_page == 1:
                self.current_page = self.max_pages
            else:
                self.current_page -= 1

        self.page_switcher.update_index(self.current_page, self.max_pages)
        self.gen_search_results(self.last_results)

    def gen_search_results(self, results, new_search=False, fade_in=True, animate_scroll=True, *args):

        # Set to proper page on favorite/unfavorite
        default_scroll = 1

        # Update page counter
        self.last_results = results
        self.max_pages = (len(results) / self.page_size).__ceil__()
        self.current_page = 1 if self.current_page == 0 or new_search else self.current_page

        self.page_switcher.update_index(self.current_page, self.max_pages)
        page_list = results[(self.page_size * self.current_page) - self.page_size:self.page_size * self.current_page]

        self.scroll_layout.clear_widgets()

        # Generate header
        backup_count = len(results)
        header_content = "Select a back-up to restore"

        for child in self.header.children:
            if child.id == "text":
                child.text = header_content
                break

        # Show back-ups if they exist
        if backup_count != 0:

            # Clear and add all ServerButtons
            for x, backup_object in enumerate(page_list, 1):

                # Activated when addon is clicked
                def restore_backup(backup_obj, index, *args):

                    def restore_screen(file, stop=False, *args):
                        server_obj = constants.server_manager.current_server
                        if stop:
                            server_obj.silent_command("stop")
                            while server_obj.running:
                                time.sleep(0.2)
                        constants.server_manager.current_server.backup._restore_file = file
                        utility.screen_manager.current = 'ServerBackupRestoreProgressScreen'

                    selected_button = [item for item in self.scroll_layout.walk() if item.__class__.__name__ == "BackupButton"][index - 1]
                    if constants.server_manager.current_server.running:
                        utility.screen_manager.current_screen.show_popup(
                            "query",
                            "Stop & Restore Back-up",
                            f"Are you sure you want to stop and revert '{backup_obj.name}' to {backup_obj.date}?\n\nThis action can't be undone",
                            [None, functools.partial(Clock.schedule_once, functools.partial(restore_screen, backup_obj, True), 0.25)]
                        )
                    else:
                        utility.screen_manager.current_screen.show_popup(
                            "query",
                            "Restore Back-up",
                            f"Are you sure you want to revert '${backup_obj.name}$' to ${backup_obj.date}$?\n\nThis action can't be undone",
                            [None, functools.partial(Clock.schedule_once, functools.partial(restore_screen, backup_obj, False), 0.25)]
                        )

                # Add-on button click function
                self.scroll_layout.add_widget(
                    ScrollItem(
                        widget = BackupButton(
                            backup_object = backup_object,
                            fade_in = ((x if x <= 8 else 8) / self.anim_speed) if fade_in else 0,
                            index = x + ((self.current_page - 1) * self.page_size),
                            click_function = functools.partial(
                                restore_backup,
                                backup_object,
                                x
                            )
                        )
                    )
                )

            self.resize_bind()

        # Animate scrolling
        def set_scroll(*args):
            Animation.stop_all(self.scroll_layout.parent.parent)
            if animate_scroll:
                Animation(scroll_y=default_scroll, duration=0.1).start(self.scroll_layout.parent.parent)
            else:
                self.scroll_layout.parent.parent.scroll_y = default_scroll

        Clock.schedule_once(set_scroll, 0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'
        self.header = None
        self.scroll_layout = None
        self.blank_label = None
        self.page_switcher = None

        self.last_results = []
        self.page_size = 10
        self.current_page = 0
        self.max_pages = 0
        self.anim_speed = 10

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        super()._on_keyboard_down(keyboard, keycode, text, modifiers)

        # Press arrow keys to switch pages
        if keycode[1] in ['right', 'left'] and self.name == utility.screen_manager.current_screen.name:
            self.switch_page(keycode[1])

    def generate_menu(self, **kwargs):
        server_obj = constants.server_manager.current_server
        backup_list = server_obj.backup.return_backup_list()

        # Scroll list
        scroll_widget = ScrollViewWidget(position=(0.5, 0.52))
        scroll_anchor = AnchorLayout()
        self.scroll_layout = GridLayout(cols=1, spacing=15, size_hint_max_x=1250, size_hint_y=None, padding=[0, 30, 0, 30])

        # Bind / cleanup height on resize
        def resize_scroll(call_widget, grid_layout, anchor_layout, *args):
            call_widget.height = Window.height // 1.82
            grid_layout.cols = 2 if Window.width > grid_layout.size_hint_max_x else 1
            self.anim_speed = 13 if Window.width > grid_layout.size_hint_max_x else 10

            def update_grid(*args):
                anchor_layout.size_hint_min_y = grid_layout.height
                scroll_top.resize(); scroll_bottom.resize()

            Clock.schedule_once(update_grid, 0)

        self.resize_bind = lambda *_: Clock.schedule_once(functools.partial(resize_scroll, scroll_widget, self.scroll_layout, scroll_anchor), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        self.scroll_layout.bind(minimum_height=self.scroll_layout.setter('height'))
        self.scroll_layout.id = 'scroll_content'

        # Scroll gradient
        scroll_top = ScrollBackground(pos_hint={"center_x": 0.5, "center_y": 0.795}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, 60))
        scroll_bottom = ScrollBackground(pos_hint={"center_x": 0.5, "center_y": 0.26}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, -60))

        # Generate buttons on page load
        header_content = "Select a back-up to restore"
        self.header = HeaderText(header_content, '', (0, 0.89))

        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'
        float_layout.add_widget(self.header)

        self.page_switcher = PageSwitcher(0, 0, (0.5, 0.887), self.switch_page)

        # Append scroll view items
        scroll_anchor.add_widget(self.scroll_layout)
        scroll_widget.add_widget(scroll_anchor)
        float_layout.add_widget(scroll_widget)
        float_layout.add_widget(scroll_top)
        float_layout.add_widget(scroll_bottom)
        float_layout.add_widget(self.page_switcher)

        buttons.append(ExitButton('Back', (0.5, 0.11), cycle=True))

        for button in buttons: float_layout.add_widget(button)

        float_layout.add_widget(generate_title(f"Back-up Manager: '{server_obj.name}'"))
        float_layout.add_widget(generate_footer(f"{server_obj.name}, Back-ups, Restore"))

        self.add_widget(float_layout)

        # Automatically generate results on page load
        constants.server_manager.refresh_list()
        self.gen_search_results(backup_list)


class ServerBackupDownloadScreen(MenuBackground):

    def switch_page(self, direction):

        if self.max_pages == 1:
            return

        if direction == "right":
            if self.current_page == self.max_pages:
                self.current_page = 1
            else:
                self.current_page += 1

        else:
            if self.current_page == 1:
                self.current_page = self.max_pages
            else:
                self.current_page -= 1

        self.page_switcher.update_index(self.current_page, self.max_pages)
        self.gen_search_results(self.last_results)

    def gen_search_results(self, results, new_search=False, fade_in=True, animate_scroll=True, *args):

        # Set to proper page on favorite/unfavorite
        default_scroll = 1

        # Update page counter
        self.last_results = results
        self.max_pages = (len(results) / self.page_size).__ceil__()
        self.current_page = 1 if self.current_page == 0 or new_search else self.current_page

        self.page_switcher.update_index(self.current_page, self.max_pages)
        page_list = results[(self.page_size * self.current_page) - self.page_size:self.page_size * self.current_page]

        self.scroll_layout.clear_widgets()

        # Generate header
        backup_count = len(results)
        header_content = "Select a back-up to download"

        for child in self.header.children:
            if child.id == "text":
                child.text = header_content
                break

        # Show back-ups if they exist
        if backup_count != 0:

            # Clear and add all ServerButtons
            for x, backup_object in enumerate(page_list, 1):

                # Activated when addon is clicked
                def download_backup(backup_obj, index, *args):
                    server_obj = constants.server_manager.current_server
                    if not server_obj._telepath_data:
                        return

                    utility.screen_manager.current = 'ServerBackupScreen'

                    def download_thread():
                        if utility.screen_manager.current_screen.name == 'ServerBackupScreen':
                            download_button = utility.screen_manager.current_screen.download_button
                            if download_button: Clock.schedule_once(functools.partial(download_button.loading, True), 0)

                        location = constants.telepath_download(server_obj._telepath_data, backup_obj.path, paths.user_downloads)
                        if os.path.exists(location):
                            open_folder(location)
                            Clock.schedule_once(
                                functools.partial(
                                    utility.screen_manager.current_screen.show_banner,
                                    (0.553, 0.902, 0.675, 1),
                                    f'Downloaded back-up successfully',
                                    "cloud-download-sharp.png",
                                    3,
                                    {"center_x": 0.5, "center_y": 0.965}
                                ), 1
                            )

                        if utility.screen_manager.current_screen.name == 'ServerBackupScreen':
                            download_button = utility.screen_manager.current_screen.download_button
                            if download_button: Clock.schedule_once(functools.partial(download_button.loading, False), 0)

                    dTimer(0, download_thread).start()

                # Add-on button click function
                self.scroll_layout.add_widget(
                    ScrollItem(
                        widget = BackupButton(
                            backup_object = backup_object,
                            fade_in = ((x if x <= 8 else 8) / self.anim_speed) if fade_in else 0,
                            index = x + ((self.current_page - 1) * self.page_size),
                            click_function = functools.partial(
                                download_backup,
                                backup_object,
                                x
                            )
                        )
                    )
                )

            self.resize_bind()

        # Animate scrolling
        def set_scroll(*args):
            Animation.stop_all(self.scroll_layout.parent.parent)
            if animate_scroll:
                Animation(scroll_y=default_scroll, duration=0.1).start(self.scroll_layout.parent.parent)
            else:
                self.scroll_layout.parent.parent.scroll_y = default_scroll

        Clock.schedule_once(set_scroll, 0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'
        self.header = None
        self.scroll_layout = None
        self.blank_label = None
        self.page_switcher = None

        self.last_results = []
        self.page_size = 10
        self.current_page = 0
        self.max_pages = 0
        self.anim_speed = 10

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        super()._on_keyboard_down(keyboard, keycode, text, modifiers)

        # Press arrow keys to switch pages
        if keycode[1] in ['right', 'left'] and self.name == utility.screen_manager.current_screen.name:
            self.switch_page(keycode[1])

    def generate_menu(self, **kwargs):
        server_obj = constants.server_manager.current_server
        backup_list = server_obj.backup.return_backup_list()

        # Scroll list
        scroll_widget = ScrollViewWidget(position=(0.5, 0.52))
        scroll_anchor = AnchorLayout()
        self.scroll_layout = GridLayout(cols=1, spacing=15, size_hint_max_x=1250, size_hint_y=None, padding=[0, 30, 0, 30])

        # Bind / cleanup height on resize
        def resize_scroll(call_widget, grid_layout, anchor_layout, *args):
            call_widget.height = Window.height // 1.82
            grid_layout.cols = 2 if Window.width > grid_layout.size_hint_max_x else 1
            self.anim_speed = 13 if Window.width > grid_layout.size_hint_max_x else 10

            def update_grid(*args):
                anchor_layout.size_hint_min_y = grid_layout.height
                scroll_top.resize(); scroll_bottom.resize()

            Clock.schedule_once(update_grid, 0)

        self.resize_bind = lambda *_: Clock.schedule_once(functools.partial(resize_scroll, scroll_widget, self.scroll_layout, scroll_anchor), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        self.scroll_layout.bind(minimum_height=self.scroll_layout.setter('height'))
        self.scroll_layout.id = 'scroll_content'

        # Scroll gradient
        scroll_top = ScrollBackground(pos_hint={"center_x": 0.5, "center_y": 0.795}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, 60))
        scroll_bottom = ScrollBackground(pos_hint={"center_x": 0.5, "center_y": 0.26}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, -60))

        # Generate buttons on page load
        header_content = "Select a back-up to download"
        self.header = HeaderText(header_content, '', (0, 0.89))

        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'
        float_layout.add_widget(self.header)

        self.page_switcher = PageSwitcher(0, 0, (0.5, 0.887), self.switch_page)

        # Append scroll view items
        scroll_anchor.add_widget(self.scroll_layout)
        scroll_widget.add_widget(scroll_anchor)
        float_layout.add_widget(scroll_widget)
        float_layout.add_widget(scroll_top)
        float_layout.add_widget(scroll_bottom)
        float_layout.add_widget(self.page_switcher)

        buttons.append(ExitButton('Back', (0.5, 0.11), cycle=True))

        for button in buttons: float_layout.add_widget(button)

        float_layout.add_widget(generate_title(f"Back-up Manager: '{server_obj.name}'"))
        float_layout.add_widget(generate_footer(f"{server_obj.name}, Back-ups, Download"))

        self.add_widget(float_layout)

        # Automatically generate results on page load
        constants.server_manager.refresh_list()
        self.gen_search_results(backup_list)


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
        java_text = 'Verifying Java Installation' if os.path.exists(paths.java) else 'Installing Java'
        function_list = [
            (java_text, functools.partial(constants.java_check, functools.partial(adjust_percentage, 30)), 0),
            ('Restoring back-up', functools.partial(foundry.restore_server, restore_file, functools.partial(adjust_percentage, 70)), 0),
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
            (java_text, functools.partial(constants.java_check, functools.partial(adjust_percentage, 30)), 0),
            ('Saving a back-up', server_obj.backup.save, 10),
            ('Cloning server', functools.partial(manager.clone_server, server_obj, functools.partial(adjust_percentage, 50)), 0),
            ('Creating initial back-up', functools.partial(foundry.create_backup, True), 10)
        ]

        self.page_contents['function_list'] = tuple(function_list)
