from source.ui.desktop.views.templates import *
from source.ui.desktop.widgets import *



#  =============================================== Import Server =======================================================
# <editor-fold desc="Import Server">


# Import existing servers ----------------------------------------------------------------------------------------------

class ServerImportScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'

        self.layout = None
        self.button_layout = None
        self.page_counter = None
        self.input_type = None
        self.input = None
        self.next_button = None
        self.name_input = None

    def load_input(self, input_type, *args):
        self.input_type = input_type
        self.button_layout.clear_widgets()
        self.page_counter.clear_widgets()
        self.layout.remove_widget(self.page_counter)

        # Change the input based on input_type
        self.page_counter = page_counter(2, 2, (0, 0.818))
        self.button_layout.opacity = 0
        self.add_widget(self.page_counter)

        # Add telepath button if servers are connected
        offset = 0
        telepath_data = constants.server_manager.online_telepath_servers
        if telepath_data:
            offset = 0.05
            self.add_widget(TelepathDropButton('import', (0.5, 0.45)))

        if input_type == "external":
            self.name_input = ServerImportPathInput(pos_hint={"center_x": 0.5, "center_y": 0.5 + offset})
            self.button_layout.add_widget(self.name_input)
            self.button_layout.add_widget(input_button('Browse...', (0.5, 0.5 + offset), (
            'dir', paths.user_downloads if os.path.isdir(paths.user_downloads) else paths.user_home),
                                                       input_name='ServerImportPathInput',
                                                       title='Select a Server Folder'))

        elif input_type == "backup":
            self.name_input = ServerImportBackupInput(pos_hint={"center_x": 0.5, "center_y": 0.5 + offset})
            self.button_layout.add_widget(self.name_input)
            start_path = paths.backups if os.path.isdir(paths.backups) else paths.user_downloads if os.path.isdir(
                paths.user_downloads) else paths.user_home
            self.button_layout.add_widget(input_button('Browse...', (0.5, 0.5 + offset), ('file', start_path),
                                                       input_name='ServerImportBackupInput',
                                                       title='Select an auto-mcs back-up file',
                                                       ext_list=['*.amb', '*.tgz']))

        # Auto-launch popup
        try:
            for item in self.button_layout.children[0].children:
                if item.id == "input_button" and not telepath_data:
                    Clock.schedule_once(item.force_click, 0)
                    Clock.schedule_once(item.on_leave, 0.01)
                    break
        except AttributeError:
            pass

        # def set_import_path(*args):
        #     for item in self.button_layout.children:
        #         if "ServerImport" in item.__class__.__name__:
        #             foundry.import_data['path'] = item.selected_server

        self.button_layout.add_widget(InputLabel(pos_hint={"center_x": 0.5, "center_y": 0.58 + offset}))
        self.next_button = next_button('Next', (0.5, 0.24), True, next_screen='ServerImportProgressScreen')
        # self.next_button.children[2].bind(on_press=set_import_path)
        self.button_layout.add_widget(self.next_button)
        Animation(opacity=1, duration=0.5).start(self.button_layout)

    def generate_menu(self, **kwargs):

        # Return if no free space or telepath is busy
        if disk_popup():
            return
        if telepath_popup():
            return

        # Reset import path
        foundry.import_data = {'name': None, 'path': None}
        os.chdir(constants.get_cwd())
        constants.safe_delete(paths.temp)

        # Generate buttons on page load
        buttons = []
        self.layout = FloatLayout()
        self.layout.id = 'content'

        # Prevent server creation if offline
        if not constants.app_online:
            self.layout.add_widget(HeaderText("Importing a server requires an internet connection", '', (0, 0.6)))
            buttons.append(ExitButton('Back', (0.5, 0.35)))

        # Regular menus
        else:
            def go_to_modpack(*a):
                utility.screen_manager.current = 'ServerImportModpackScreen'

            self.layout.add_widget(HeaderText("What do you wish to import?", '', (0, 0.81)))
            buttons.append(MainButton('Import external server', (0.5, 0.55), 'folder-outline.png',
                                      click_func=functools.partial(self.load_input, 'external')))
            buttons.append(MainButton('Import Auto-MCS back-up', (0.5, 0.4), 'backup-icon.png',
                                      click_func=functools.partial(self.load_input, 'backup')))
            self.layout.add_widget(ExitButton('Back', (0.5, 0.14), cycle=True))
            self.page_counter = page_counter(1, 2, (0, 0.818))
            self.add_widget(self.page_counter)

        self.button_layout = FloatLayout()
        for button in buttons:
            self.button_layout.add_widget(button)

        self.layout.add_widget(self.button_layout)
        self.layout.add_widget(generate_title('Import Server'))
        self.layout.add_widget(generate_footer('Import server'))

        self.add_widget(self.layout)


class ServerImportProgressScreen(ProgressScreen):

    # Only replace this function when making a child screen
    # Set fail message in child functions to trigger an error
    def contents(self):
        import_name = foundry.import_data['name']
        open_after = functools.partial(self.open_server, import_name, True,
                                       f"'${import_name}$' was imported successfully")

        def before_func(*args):

            if not constants.app_online:
                self.execute_error(
                    "An internet connection is required to continue\n\nVerify connectivity and try again")

            elif not constants.check_free_space(telepath_data=foundry.new_server_info['_telepath_data']):
                self.execute_error("Your primary disk is almost full\n\nFree up space and try again")

            else:
                foundry.pre_server_create()

        def after_func(*args):
            foundry.post_server_create()
            open_after()

        # Original is percentage before this function, adjusted is a percent of hooked value
        def adjust_percentage(*args):
            original = self.last_progress
            adjusted = args[0]
            total = args[1] * 0.01
            final = original + round(adjusted * total)
            if final < 0:
                final = original
            self.progress_bar.update_progress(final)

        self.page_contents = {

            # Page name
            'title': f"Importing '{import_name}'",

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

        is_backup_file = ((foundry.import_data['path'].endswith(".tgz") or foundry.import_data['path'].endswith(
            ".amb")) and os.path.isfile(foundry.import_data['path']))

        # Create function list
        java_text = 'Verifying Java Installation' if os.path.exists(paths.java) else 'Installing Java'
        function_list = [
            (java_text, functools.partial(constants.java_check, functools.partial(adjust_percentage, 30)), 0),
            ('Importing server',
             functools.partial(foundry.scan_import, is_backup_file, functools.partial(adjust_percentage, 30)), 0),
            ('Validating configuration',
             functools.partial(foundry.finalize_import, functools.partial(adjust_percentage, 20)), 0),
            ('Creating initial back-up', functools.partial(foundry.create_backup, True), 20)
        ]

        self.page_contents['function_list'] = tuple(function_list)



# Import modpack files -------------------------------------------------------------------------------------------------

class ServerImportModpackScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'

        self.layout = None
        self.button_layout = None
        self.page_counter = None
        self.input_type = None
        self.input = None
        self.next_button = None

    def generate_menu(self, **kwargs):

        # Reset import path
        foundry.import_data = {'name': None, 'path': None}
        os.chdir(constants.get_cwd())
        constants.safe_delete(paths.temp)

        # Generate buttons on page load
        buttons = []
        self.layout = FloatLayout()
        self.layout.id = 'content'

        # Prevent server creation if offline
        if not constants.app_online:
            self.layout.add_widget(HeaderText("Server creation requires an internet connection", '', (0, 0.6)))
            buttons.append(ExitButton('Back', (0.5, 0.35)))


        # Regular menus
        else:

            # Add Telepath button if servers are connected
            offset = 0
            if constants.server_manager.online_telepath_servers:
                offset = 0.05
                self.add_widget(TelepathDropButton('install', (0.5, 0.37)))

            # Regular menus
            self.layout.add_widget(HeaderText("Which modpack do you wish to install?", '', (0, 0.81)))

            def download_modpack(*a):
                utility.screen_manager.current = 'ServerImportModpackSearchScreen'

            buttons.append(MainButton('Download a Modpack', (0.5, 0.576 + offset), 'download-outline.png', width=528,
                                      click_func=download_modpack))

            start_path = paths.user_downloads if os.path.isdir(paths.user_downloads) else paths.user_home
            buttons.append(InputLabel(pos_hint={"center_x": 0.5, "center_y": 0.505 + offset}))
            buttons.append(ServerImportModpackInput(pos_hint={"center_x": 0.5, "center_y": 0.44 + offset}))
            buttons.append(input_button('Browse...', (0.5, 0.44 + offset), ('file', start_path),
                                        input_name='ServerImportModpackInput', title='Select a modpack',
                                        ext_list=['*.zip', '*.mrpack']))

            self.layout.add_widget(ExitButton('Back', (0.5, 0.14), cycle=True))

            def remove_page(*a):
                if 'ServerImportScreen' in utility.screen_manager.screen_tree:
                    utility.screen_manager.screen_tree.remove('ServerImportScreen')

            Clock.schedule_once(remove_page, 0.1)
            self.page_counter = page_counter(2, 2, (0, 0.818))
            self.add_widget(self.page_counter)

        self.button_layout = FloatLayout()
        for button in buttons:
            self.button_layout.add_widget(button)

        self.layout.add_widget(self.button_layout)

        self.next_button = next_button('Next', (0.5, 0.24), True, next_screen='ServerImportModpackProgressScreen')
        if constants.app_online: self.button_layout.add_widget(self.next_button)

        self.layout.add_widget(generate_title('Install a Modpack'))
        self.layout.add_widget(generate_footer('Install a modpack'))

        self.add_widget(self.layout)


class ServerImportModpackProgressScreen(ProgressScreen):

    # Only replace this function when making a child screen
    # Set fail message in child functions to trigger an error
    def contents(self):
        import_name = foundry.import_data['name']

        def before_func(*args):
            if not constants.app_online:
                self.execute_error(
                    "An internet connection is required to continue\n\nVerify connectivity and try again")

            elif not constants.check_free_space(telepath_data=foundry.new_server_info['_telepath_data']):
                self.execute_error("Your primary disk is almost full\n\nFree up space and try again")

            else:
                foundry.pre_server_create()

        def after_func(*args):
            import_data = foundry.post_server_create(modpack=True)

            if self.telepath and import_data['readme']:
                import_data['readme'] = constants.telepath_download(self.telepath, import_data['readme'])['path']

            self.open_server(
                import_data['name'],
                True,
                f"'${import_data['name']}$' was imported successfully",
                show_readme=import_data['readme']
            )

        # Original is percentage before this function, adjusted is a percent of hooked value
        def adjust_percentage(*args):
            original = self.last_progress
            adjusted = args[0]
            total = args[1] * 0.01
            final = original + round(adjusted * total)
            if final < 0:
                final = original
            self.progress_bar.update_progress(final)

        self.page_contents = {

            # Page name
            'title': f"Installing Modpack",

            # Header text
            'header': "Sit back and relax, it's automation time...",

            # Tuple of tuples for steps (label, function, percent)
            # Percent of all functions must total 100
            # Functions must return True, or default error will be executed
            'default_error': "There was an issue importing this modpack.\n\nThe required resources were unobtainable and will require manual installation.",

            'function_list': (),

            # Function to run before steps (like checking for an internet connection)
            'before_function': before_func,

            # Function to run after everything is complete (like cleaning up the screen tree) will only run if no error
            'after_function': after_func,

            # Screen to go to after complete
            'next_screen': None
        }

        # Create function list
        java_text = 'Verifying Java Installation' if os.path.exists(paths.java) else 'Installing Java'
        function_list = [
            (java_text, functools.partial(constants.java_check, functools.partial(adjust_percentage, 30)), 0),
            ('Validating modpack',
             functools.partial(foundry.scan_modpack, False, functools.partial(adjust_percentage, 20)), 0),
            ("Downloading 'server.jar'",
             functools.partial(foundry.download_jar, functools.partial(adjust_percentage, 15), True), 0),
            ('Installing modpack', functools.partial(foundry.install_server, None, True), 15),
            ('Validating configuration',
             functools.partial(foundry.finalize_modpack, False, functools.partial(adjust_percentage, 10)), 0),
            ('Creating initial back-up', functools.partial(foundry.create_backup, True), 10)
        ]

        self.page_contents['function_list'] = tuple(function_list)


class ServerImportModpackSearchScreen(MenuBackground):

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

    def gen_search_results(self, results, new_search=False, *args):

        # Error on failure
        if not results and isinstance(results, bool):
            self.show_popup(
                "warning",
                "Server Error",
                "There was an issue reaching the add-on repository\n\nPlease try again later",
                None
            )
            self.max_pages = 0
            self.current_page = 0

        # On success, rebuild results
        else:

            # Update page counter
            self.last_results = results
            self.max_pages = (len(results) / self.page_size).__ceil__()
            self.current_page = 1 if self.current_page == 0 or new_search else self.current_page

            self.page_switcher.update_index(self.current_page, self.max_pages)
            page_list = results[
                        (self.page_size * self.current_page) - self.page_size:self.page_size * self.current_page]

            self.scroll_layout.clear_widgets()

            # Generate header
            addon_count = len(results)
            very_bold_font = os.path.join(paths.ui_assets, 'fonts', constants.fonts["very-bold"])
            search_text = self.search_bar.previous_search if (
                        len(self.search_bar.previous_search) <= 25) else self.search_bar.previous_search[:22] + "..."
            header_content = f"{translate('Search for')} '{search_text}'  [color=#494977]-[/color]  " + (
                f'[color=#6A6ABA]{translate("No results")}[/color]' if addon_count == 0 else f'[font={very_bold_font}]1[/font] {translate("item")}' if addon_count == 1 else f'[font={very_bold_font}]{addon_count:,}[/font] {translate("items")}')

            for child in self.header.children:
                if child.id == "text":
                    child.text = header_content
                    break

            # If there are no addons, say as much with a label
            if addon_count == 0:
                self.blank_label.text = "there are no items to display"
                utility.hide_widget(self.blank_label, False)
                self.blank_label.opacity = 0
                Animation(opacity=1, duration=0.2).start(self.blank_label)
                self.max_pages = 0
                self.current_page = 0

            # If there are addons, display them here
            else:
                utility.hide_widget(self.blank_label, True)

                # Clear and add all addons
                for x, addon_object in enumerate(page_list, 1):

                    # Function to download addon info
                    def load_addon(addon, index):
                        try:
                            selected_button = \
                            [item for item in self.scroll_layout.walk() if item.__class__.__name__ == "AddonButton"][
                                index - 1]

                            # Cache updated addon info into button, or skip if it's already cached
                            if selected_button.properties:
                                if not selected_button.properties.description:
                                    new_addon_info = addons.get_modpack_info(addon)
                                    selected_button.properties = new_addon_info

                            Clock.schedule_once(functools.partial(selected_button.loading, False), 1)

                            return selected_button.properties, selected_button.installed

                        # Don't crash if add-on failed to load
                        except:
                            Clock.schedule_once(
                                functools.partial(
                                    utility.screen_manager.current_screen.show_banner,
                                    (1, 0.5, 0.65, 1),
                                    f"Failed to load modpack",
                                    "close-circle-sharp.png",
                                    2.5,
                                    {"center_x": 0.5, "center_y": 0.965}
                                ), 0
                            )

                    # Function to install addon
                    def install_addon(index):

                        def move_to_next_page(addon, *a):
                            addon = addons.get_modpack_url(addon)
                            foundry.import_data = {
                                'name': addon.name,
                                'url': addon.download_url
                            }

                            def progress(*a):
                                utility.screen_manager.current = "ServerImportModpackProgressScreen"

                            Clock.schedule_once(progress, 0.4)

                        selected_button = \
                        [item for item in self.scroll_layout.walk() if item.__class__.__name__ == "AddonButton"][
                            index - 1]
                        dTimer(0, functools.partial(move_to_next_page, selected_button.properties)).start()

                    # Activated when addon is clicked
                    def view_addon(addon, index, *args):
                        selected_button = \
                        [item for item in self.scroll_layout.walk() if item.__class__.__name__ == "AddonButton"][
                            index - 1]

                        selected_button.loading(True)

                        Clock.schedule_once(
                            functools.partial(
                                self.show_popup,
                                "addon",
                                " ",
                                " ",
                                (None, functools.partial(install_addon, index)),
                                functools.partial(load_addon, addon, index)
                            ),
                            0
                        )

                    # Add-on button click function
                    self.scroll_layout.add_widget(
                        ScrollItem(
                            widget=AddonButton(
                                properties=addon_object,
                                installed=False,
                                fade_in=((x if x <= 8 else 8) / self.anim_speed),
                                click_function=functools.partial(
                                    view_addon,
                                    addon_object,
                                    x
                                )
                            )
                        )
                    )

                self.resize_bind()
                self.scroll_layout.parent.parent.scroll_y = 1

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'
        self.header = None
        self.scroll_layout = None
        self.blank_label = None
        self.search_bar = None
        self.page_switcher = None

        self.last_results = []
        self.page_size = 20
        self.current_page = 0
        self.max_pages = 0
        self.anim_speed = 10

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        super()._on_keyboard_down(keyboard, keycode, text, modifiers)

        # Press arrow keys to switch pages
        if keycode[1] in ['right', 'left'] and self.name == utility.screen_manager.current_screen.name:
            self.switch_page(keycode[1])
        elif keycode[1] == "tab" and self.name == utility.screen_manager.current_screen.name:
            for widget in self.search_bar.children:
                try:
                    if widget.id == "search_input":
                        widget.grab_focus()
                        break
                except AttributeError:
                    pass

    def generate_menu(self, **kwargs):

        # Scroll list
        scroll_widget = ScrollViewWidget(position=(0.5, 0.437))
        scroll_anchor = AnchorLayout()
        self.scroll_layout = GridLayout(cols=1, spacing=15, size_hint_max_x=1250, size_hint_y=None,
                                        padding=[0, 30, 0, 30])

        # Bind / cleanup height on resize
        def resize_scroll(call_widget, grid_layout, anchor_layout, *args):
            call_widget.height = Window.height // 1.79
            grid_layout.cols = 2 if Window.width > grid_layout.size_hint_max_x else 1
            self.anim_speed = 13 if Window.width > grid_layout.size_hint_max_x else 10

            def update_grid(*args):
                anchor_layout.size_hint_min_y = grid_layout.height

            Clock.schedule_once(update_grid, 0)

        self.resize_bind = lambda *_: Clock.schedule_once(
            functools.partial(resize_scroll, scroll_widget, self.scroll_layout, scroll_anchor), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        self.scroll_layout.bind(minimum_height=self.scroll_layout.setter('height'))
        self.scroll_layout.id = 'scroll_content'

        # Scroll gradient
        scroll_top = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.715}, pos=scroll_widget.pos,
                                       size=(scroll_widget.width // 1.5, 60))
        scroll_bottom = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.17}, pos=scroll_widget.pos,
                                          size=(scroll_widget.width // 1.5, -60))

        # Generate buttons on page load
        addon_count = 0
        very_bold_font = os.path.join(paths.ui_assets, 'fonts', constants.fonts["very-bold"])
        header_content = translate("Modpack Search")
        self.header = HeaderText(header_content, '', (0, 0.89), __translate__=(False, True))

        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'
        float_layout.add_widget(self.header)

        # Add blank label to the center
        self.blank_label = Label()
        self.blank_label.text = "search for modpacks above"
        self.blank_label.font_name = os.path.join(paths.ui_assets, 'fonts', constants.fonts['italic'])
        self.blank_label.pos_hint = {"center_x": 0.5, "center_y": 0.48}
        self.blank_label.font_size = sp(24)
        self.blank_label.color = (0.6, 0.6, 1, 0.35)
        float_layout.add_widget(self.blank_label)

        search_function = addons.search_modpacks
        self.search_bar = search_input(return_function=search_function, pos_hint={"center_x": 0.5, "center_y": 0.795})
        self.page_switcher = PageSwitcher(0, 0, (0.5, 0.805), self.switch_page)

        # Append scroll view items
        scroll_anchor.add_widget(self.scroll_layout)
        scroll_widget.add_widget(scroll_anchor)
        float_layout.add_widget(scroll_widget)
        float_layout.add_widget(scroll_top)
        float_layout.add_widget(scroll_bottom)
        float_layout.add_widget(self.search_bar)
        float_layout.add_widget(self.page_switcher)

        buttons.append(ExitButton('Back', (0.5, 0.12), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)

        menu_name = "Install a modpack, Download"
        float_layout.add_widget(generate_title("Download Modpack"))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)

        # # Autofocus search bar
        # for widget in self.search_bar.children:
        #     try:
        #         if widget.id == "search_input":
        #             widget.grab_focus()
        #             break
        #     except AttributeError:
        #         pass

        Clock.schedule_once(functools.partial(self.search_bar.execute_search, ""), 0)


# </editor-fold> ///////////////////////////////////////////////////////////////////////////////////////////////////////
