from source.ui.desktop.views.create import CreateServerAclScreen, CreateServerAclRuleScreen
from source.ui.desktop.widgets import _animate_background
from source.ui.desktop.views.templates import *
from source.ui.desktop.widgets import *
from source.ui.desktop.utility import *
from source.ui.desktop import utility


# =============================================== Server Manager =======================================================
# <editor-fold desc="Server Manager">

# Import Server --------------------------------------------------------------------------------------------------------

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


# Server Manager Overview ----------------------------------------------------------------------------------------------

class ServerButton(HoverButton):
    class ParagraphLabel(Label, HoverBehavior):

        def on_mouse_pos(self, *args):

            if "ServerViewScreen" in utility.screen_manager.current_screen.name and self.copyable:
                try:
                    super().on_mouse_pos(*args)
                except:
                    pass

        # Hover stuffies
        def on_enter(self, *args):

            if self.copyable:
                self.outline_width = 0
                self.outline_color = constants.brighten_color(self.color, 0.05)
                Animation(outline_width=1, duration=0.03).start(self)

        def on_leave(self, *args):

            if self.copyable:
                Animation.stop_all(self)
                self.outline_width = 0

        # Normal stuffies
        def on_ref_press(self, *args):
            if not self.disabled:
                def click(*a):
                    clipboard_text = re.sub(r"\[.*?\]", "", self.text.split(" ")[-1].strip())
                    if self.parent.button_pressed == "left":
                        banner_text = "Copied IP address  (right-click for LAN)"

                    else:
                        server_obj = self.parent.properties
                        if server_obj.running:
                            clipboard_text = server_obj.run_data['network']['private_ip'] + ':' + \
                                             server_obj.run_data['network']['address']['port']

                        banner_text = "Copied LAN IP address  (left-click for public)"

                    Clock.schedule_once(
                        functools.partial(
                            utility.screen_manager.current_screen.show_banner,
                            (0.85, 0.65, 1, 1),
                            banner_text,
                            "link-sharp.png",
                            2,
                            {"center_x": 0.5, "center_y": 0.965}
                        ), 0
                    )

                    Clipboard.copy(clipboard_text)

                Clock.schedule_once(click, 0)

        def ref_text(self, *args):

            if '[ref=' not in self.text and '[/ref]' not in self.text and self.copyable:
                self.text = f'[ref=none]{self.text.strip()}[/ref]'
            elif '[/ref]' in self.text:
                self.text = self.text.replace("[/ref]", "") + "[/ref]"

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.markup = True
            self.copyable = True
            self.bind(text=self.ref_text)

    class ChangeIconButton(Button, HoverBehavior):

        # Show menu to replace icon
        def on_click(self, *a):

            def apply_new_icon(path: str = None, *a):
                def do_change():
                    icon_path = False

                    # Upload to remote if Telepath
                    if path:
                        if self.server_obj._telepath_data:
                            icon_path = constants.telepath_upload(self.server_obj._telepath_data, path)['path']
                        else:
                            icon_path = path
                    success, message = self.server_obj.update_icon(icon_path)

                    # Reload page
                    if success:

                        # Override for Telepath
                        if self.server_obj._telepath_data:
                            manager.get_server_icon(self.server_obj.name, self.server_obj._telepath_data,
                                                    overwrite=True)

                        # Remove the cached image and texture
                        Cache.remove('kv.image')
                        Cache.remove('kv.texture')
                        for item in glob(os.path.join(paths.ui_assets, 'live', 'blur_icon_*.png')):
                            os.remove(item)

                    return success, message

                def loading_screen(*a):
                    utility.screen_manager.current = 'BlurredLoadingScreen'

                Clock.schedule_once(loading_screen, 0)

                # Actually rename the server files
                time.sleep(0.5)
                success, message = do_change()

                # Change header and footer text to reflect change
                def reload_page(*a):
                    def go_back(*a):
                        utility.screen_manager.current = 'ServerViewScreen'

                    Clock.schedule_once(go_back, 0)

                    # Display banner to show success
                    Clock.schedule_once(
                        functools.partial(
                            utility.screen_manager.current_screen.show_banner,
                            (0.553, 0.902, 0.675, 1) if success else (1, 0.5, 0.65, 1),
                            message,
                            "checkmark-circle-sharp.png" if success else "close-circle-sharp.png",
                            3,
                            {"center_x": 0.5, "center_y": 0.965}
                        ), 0.1
                    )

                Clock.schedule_once(reload_page, 0)

            # Add icon with left click
            if self.last_touch.button == 'left':
                title = "Select an image"
                selection = file_popup("file", start_dir=paths.user_downloads, ext=constants.valid_image_formats,
                                       input_name=None, select_multiple=False, title=title)
                if selection and selection[0]:
                    dTimer(0, functools.partial(apply_new_icon, selection[0])).start()

            # Delete icon with right click
            elif self.last_touch.button == 'right' and self.is_custom:

                Clock.schedule_once(
                    functools.partial(
                        utility.screen_manager.current_screen.show_popup,
                        "warning_query",
                        'Remove Icon',
                        "Do you want to remove this icon?\n\nYou'll need to re-import it again later",
                        (None, functools.partial(dTimer(0, apply_new_icon).start))
                    ),
                    0
                )

        def on_enter(self, *args):
            Animation.stop_all(self)
            Animation.stop_all(self.type_image)
            Animation(opacity=1, duration=self.anim_duration).start(self)
            Animation(opacity=0, duration=self.anim_duration).start(self.type_image.image)
            if self.server_obj._telepath_data:
                Animation(opacity=0, duration=self.anim_duration).start(self.type_image.tp_shadow)
                Animation(opacity=0, duration=self.anim_duration).start(self.type_image.tp_icon)

        def on_leave(self, *args):
            Animation.stop_all(self)
            Animation.stop_all(self.type_image)
            Animation(opacity=0, duration=self.anim_duration).start(self)
            Animation(opacity=1, duration=self.anim_duration).start(self.type_image.image)
            if self.server_obj._telepath_data:
                Animation(opacity=1, duration=self.anim_duration).start(self.type_image.tp_shadow)
                Animation(opacity=1, duration=self.anim_duration).start(self.type_image.tp_icon)

        def generate_blur_background(self, *args):
            def run_in_foreground(*a):
                self.blur_background.source = image_path
                self.canvas.ask_update()

            try:
                # Attempt to remove existing icon temp, who even cares lol
                for item in glob(os.path.join(paths.ui_assets, 'live', 'blur_icon_*.png')):
                    if self.server_obj.name in item:
                        image_path = item
                        return run_in_foreground()
                    os.remove(item)
            except:
                pass
            image_path = os.path.join(paths.ui_assets, 'live',
                                      f'blur_icon_{self.server_obj.name}_{constants.gen_rstring(4)}.png')
            constants.folder_check(os.path.join(paths.ui_assets, 'live'))

            self.type_image.image.export_to_png(image_path)

            # Convert the image in the background
            def convert(*a):
                im = PILImage.open(image_path)

                # Center and resize icon when custom
                if self.is_custom:
                    im = im.convert('RGBA')
                    left = 4
                    upper = (im.height - 65)
                    right = left + 65
                    lower = upper + 65
                    im = im.crop((left, upper, right, lower))

                # Blur and darken the icon
                im = ImageEnhance.Brightness(im)
                im = im.enhance(0.75)
                im1 = im.filter(GaussianBlur(3))

                im1.save(image_path)

                Clock.schedule_once(run_in_foreground, 0)

            dTimer(0, convert).start()

        def resize_self(self, *a):
            for child in self.children:
                child.pos = self.pos

            offset = (self.pos[0] + 17.5, self.pos[1] + 16.5)
            self.background_ellipse.pos = offset
            self.blur_background.pos = offset
            self.background_outline.ellipse = (*offset, 66, 66)

        def __init__(self, type_image, **kwargs):
            super().__init__(**kwargs)
            self.type_image = type_image
            self.size_hint_max = self.type_image.image.size
            self.is_custom = self.type_image.image.__class__.__name__ == 'CustomServerIcon'
            self.background_normal = os.path.join(paths.ui_assets, 'empty.png')
            self.background_down = os.path.join(paths.ui_assets, 'empty.png')
            self.anim_duration = 0.1
            self.fg = self.type_image.version_label.color
            self.bc = constants.brighten_color(constants.background_color, -0.1)
            self.server_obj = constants.server_manager.current_server

            with self.canvas.before:
                # Background ellipse (drawn first)
                Color(self.bc[0], self.bc[1], self.bc[2], 0.3)  # Adjust alpha as needed
                self.background_ellipse = Ellipse(
                    size=(66, 66),
                    angle_start=0,
                    angle_end=360
                )

            with self.canvas:
                # Blur background ellipse (drawn after background ellipse)
                Color(*self.fg)
                self.blur_background = Ellipse(
                    size=(66, 66),
                    angle_start=0,
                    angle_end=360
                )

                # Outline of the ellipse
                Color(*self.fg[:3], 0.0)
                self.background_outline = Line(
                    ellipse=(0, 0, 66, 66),
                    width=2
                )

            self.shadow = Image(source=icon_path('shadow.png'), color="#111122")
            self.shadow.opacity = 0.5
            self.icon = Image(source=icon_path('pencil-sharp.png'), color=constants.brighten_color(self.fg, 0.15))
            self.add_widget(self.shadow)
            self.add_widget(self.icon)

            # Bind and initialize
            self.bind(size=self.resize_self, pos=self.resize_self)
            self.bind(on_press=self.on_click)
            self.generate_blur_background()
            self.opacity = 0

    def toggle_favorite(self, favorite, *args):
        self.favorite = favorite
        self.color_id = [(0.05, 0.05, 0.1, 1),
                         constants.brighten_color((0.85, 0.6, 0.9, 1) if self.favorite else (0.65, 0.65, 1, 1), 0.07)]
        self.title.text_size = (self.size_hint_max[0] * (0.7 if favorite else 0.94), self.size_hint_max[1])
        self.background_normal = os.path.join(paths.ui_assets, f'{self.id}{"_favorite" if self.favorite else ""}.png')
        self.resize_self()
        return favorite

    def animate_button(self, image, color, hover_action, **kwargs):
        image_animate = Animation(duration=0.05)

        Animation(color=color, duration=0.06).start(self.title)
        Animation(color=self.run_color if (self.running and not self.hovered) else color, duration=0.06).start(
            self.subtitle)

        if not self.custom_icon:
            Animation(color=color, duration=0.06).start(self.type_image.image)

        if self.type_image.version_label.__class__.__name__ == "AlignLabel":
            Animation(color=color, duration=0.06).start(self.type_image.version_label)
        Animation(color=color, duration=0.06).start(self.type_image.type_label)

        _animate_background(self, image, hover_action)

        image_animate.start(self)

    def resize_self(self, *args):

        # Title and description
        padding = 2.17
        self.title.pos = (
        self.x + (self.title.text_size[0] / padding) - (5.3 if self.favorite else 8.3) + 30, self.y + 31)
        self.subtitle.pos = (self.x + (self.subtitle.text_size[0] / padding) - 78, self.y + 8)

        offset = 9.45 if self.type_image.type_label.text in ["vanilla", "paper", "purpur"] \
            else 9.6 if self.type_image.type_label.text == "forge" \
            else 9.35 if self.type_image.type_label.text == "craftbukkit" \
            else 9.55

        self.type_image.image.x = self.width + self.x - (self.type_image.image.width) - 13
        self.type_image.image.y = self.y + ((self.height / 2) - (self.type_image.image.height / 2))

        # Telepath icon
        if self.telepath_data:
            self.type_image.tp_shadow.pos = (self.type_image.image.x - 2, self.type_image.image.y)
            self.type_image.tp_icon.pos = (self.type_image.image.x - 2, self.type_image.image.y)

        self.type_image.type_label.x = self.width + self.x - (self.padding_x * offset) - self.type_image.width - 83
        self.type_image.type_label.y = self.y + (self.height * 0.05)

        # Update label
        if self.type_image.version_label.__class__.__name__ == "AlignLabel":
            self.type_image.version_label.x = self.width + self.x - (
                        self.padding_x * offset) - self.type_image.width - 83
            self.type_image.version_label.y = self.y - (self.height / 3.2)

        # Banner version object
        else:
            self.type_image.version_label.x = self.width + self.x - (
                        self.padding_x * offset) - self.type_image.width - 130
            self.type_image.version_label.y = self.y - (self.height / 3.2) - 2

        # Favorite button
        self.favorite_layout.size_hint_max = (self.size_hint_max[0], self.size_hint_max[1])
        self.favorite_layout.pos = (self.pos[0] - 6, self.pos[1] + 13)

        # Change Icon button pos
        if self.icon_button:
            half = self.type_image.image.size_hint_max[0] / 4
            offset = 2.5 if self.type_image.image.__class__.__name__ == 'CustomServerIcon' else -1
            self.icon_button.pos = (self.type_image.image.x - half + offset, self.type_image.image.y - half)

        # Highlight border
        self.highlight_border.pos = self.pos

    def highlight(self):
        def next_frame(*args):
            Animation.stop_all(self.highlight_border)
            self.highlight_border.opacity = 1
            Animation(opacity=0, duration=0.7).start(self.highlight_border)

        Clock.schedule_once(next_frame, 0)

    def update_subtitle(self, run_data=None, last_modified=None):

        def reset(*a):
            self.running = False
            self.subtitle.copyable = False
            if last_modified:
                self.original_subtitle = backup.convert_date(last_modified)
            self.subtitle.color = self.color_id[1]
            self.subtitle.default_opacity = 0.56
            self.subtitle.font_name = self.original_font
            self.subtitle.text = self.original_subtitle

        try:
            if run_data:
                self.running = True
                self.subtitle.copyable = True
                self.subtitle.color = self.run_color
                self.subtitle.default_opacity = 0.8
                self.subtitle.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
                if run_data.get('playit-tunnel', None) or 'ply.gg' in run_data['network']['address']['ip']:
                    text = run_data['network']['address']['ip']
                else:
                    text = ':'.join(run_data['network']['address'].values())
                self.subtitle.text = f"[font={self.icons}]N[/font]  {text.replace('127.0.0.1', 'localhost')}"
            else:
                reset()

        except KeyError:
            reset()

        self.subtitle.opacity = self.subtitle.default_opacity

    def generate_name(self, color='#7373A2'):
        if self.telepath_data:
            tld = self.telepath_data['host']
            if self.telepath_data['nickname']:
                tld = self.telepath_data['nickname']
            return f'[color={color}]{tld}/[/color]{self.properties.name}'
        else:
            return self.properties.name.strip()

    def __init__(self, server_object, click_function=None, fade_in=0.0, highlight=None, update_banner="",
                 view_only=False, **kwargs):
        super().__init__(**kwargs)

        # Check if server is remote
        self.telepath_data = server_object._telepath_data

        self.view_only = view_only

        if self.view_only:
            self.ignore_hover = True

        self.favorite = server_object.favorite
        self.properties = server_object
        self.border = (-5, -5, -5, -5)
        self.color_id = [(0.05, 0.05, 0.1, 1),
                         constants.brighten_color((0.85, 0.6, 0.9, 1) if self.favorite else (0.65, 0.65, 1, 1), 0.07)]
        self.run_color = (0.529, 1, 0.729, 1)
        self.running = server_object.running and server_object.run_data
        self.pos_hint = {"center_x": 0.5, "center_y": 0.6}
        self.size_hint_max = (580, 80)
        self.id = "server_button"

        if not self.view_only:
            self.background_normal = os.path.join(paths.ui_assets, f'{self.id}.png')
            self.background_down = os.path.join(paths.ui_assets,
                                                f'{self.id}{"_favorite" if self.favorite else ""}_click.png')
        else:
            self.background_normal = os.path.join(paths.ui_assets, f'{self.id}_ro.png')
            self.background_down = os.path.join(paths.ui_assets,
                                                f'{self.id}{"_favorite" if self.favorite else "_ro"}.png')

        self.icons = os.path.join(paths.ui_assets, 'fonts', constants.fonts['icons'])

        # Loading stuffs
        self.original_subtitle = backup.convert_date(server_object.last_modified)
        self.original_font = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["regular"]}.ttf')

        # Title of Server
        self.title = Label()
        self.title.__translate__ = False
        self.title.id = "title"
        self.title.halign = "left"
        self.title.color = self.color_id[1]
        self.title.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
        self.title.font_size = sp(25)
        self.title.text_size = (self.size_hint_max[0] * 0.58, self.size_hint_max[1])
        self.title.shorten = True
        self.title.markup = True
        self.title.shorten_from = "right"
        self.title.max_lines = 1
        self.title.text = self.generate_name()
        self.add_widget(self.title)

        # Server last modified date formatted
        if self.view_only:
            self.subtitle = self.ParagraphLabel()
        else:
            self.subtitle = Label()
        self.subtitle.__translate__ = False
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
        self.subtitle.text_size[0] = 350

        if self.running:
            self.subtitle.copyable = True
            self.subtitle.color = self.run_color
            self.subtitle.default_opacity = 0.8
            self.subtitle.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')

            if server_object.run_data.get('playit-tunnel', None) or 'ply.gg' in \
                    server_object.run_data['network']['address']['ip']:
                text = server_object.run_data['network']['address']['ip']
            else:
                text = ':'.join(server_object.run_data['network']['address'].values())
            self.subtitle.text = f"[font={self.icons}]N[/font]  {text.replace('127.0.0.1', 'localhost')}"
        else:
            self.subtitle.copyable = False
            self.subtitle.color = self.color_id[1]
            self.subtitle.default_opacity = 0.56
            self.subtitle.font_name = self.original_font
            self.subtitle.text = self.original_subtitle

        self.subtitle.opacity = self.subtitle.default_opacity

        self.add_widget(self.subtitle)

        # Type icon and info
        self.type_image = RelativeLayout()
        self.type_image.width = 400

        # Check for custom server icon
        if self.telepath_data:
            self.telepath_data['icon-path'] = server_object.server_icon
            self.server_icon = manager.get_server_icon(server_object.name, self.telepath_data)
        else:
            self.server_icon = server_object.server_icon

        if self.server_icon:
            self.custom_icon = True

            class CustomServerIcon(RelativeLayout):
                def __init__(self, server_icon, **kwargs):
                    super().__init__(**kwargs)
                    with self.canvas:
                        Color(1, 1, 1, 1)  # Set the color to white
                        self.shadow = Ellipse(pos=(-23.5, -27.5), size=(120, 120),
                                              source=os.path.join(paths.ui_assets, 'icon_shadow.png'), angle_start=0,
                                              angle_end=360)
                        self.ellipse = Ellipse(pos=(4, 0), size=(65, 65), source=server_icon, angle_start=0,
                                               angle_end=360)

            self.type_image.image = CustomServerIcon(self.server_icon)
        else:
            self.custom_icon = False
            self.server_icon = os.path.join(paths.ui_assets, 'icons', 'big', f'{server_object.type.lower()}_small.png')
            self.type_image.image = Image(source=self.server_icon)

        self.type_image.image.allow_stretch = True
        self.type_image.image.size_hint_max = (65, 65)
        self.type_image.image.color = self.color_id[1]
        self.type_image.add_widget(self.type_image.image)

        # Show icon on self.type_image to specify
        if self.telepath_data:
            self.type_image.tp_shadow = Image(source=icon_path('shadow.png'))
            self.type_image.tp_shadow.allow_stretch = True
            self.type_image.tp_shadow.size_hint_max = (33, 33)
            self.type_image.tp_shadow.color = self.color_id[0]
            self.type_image.add_widget(self.type_image.tp_shadow)

            self.type_image.tp_icon = Image(source=icon_path('telepath.png'))
            self.type_image.tp_icon.allow_stretch = True
            self.type_image.tp_icon.size_hint_max = (33, 33)
            self.type_image.tp_icon.color = self.color_id[1]
            self.type_image.add_widget(self.type_image.tp_icon)
        else:
            self.type_image.tp_shadow = None
            self.type_image.tp_icon = None

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

        if update_banner:
            self.type_image.version_label = RelativeLayout()
            self.type_image.version_label.add_widget(
                BannerObject(
                    pos_hint={"center_x": 1, "center_y": 0.5},
                    size=(100, 30),
                    color=(0.647, 0.839, 0.969, 1),
                    text=('   ' + update_banner + '  ') if update_banner.startswith('b-') else update_banner,
                    icon="arrow-up-circle.png",
                    icon_side="left"
                )
            )

        else:
            self.type_image.version_label = TemplateLabel()
            self.type_image.version_label.text = server_object.version.lower()
            self.type_image.version_label.opacity = 0.6

        self.type_image.version_label.color = self.color_id[1]
        self.type_image.type_label = TemplateLabel()

        # Say modpack if such
        if self.properties.is_modpack:
            type_text = 'modpack'
        else:
            type_text = server_object.type.lower().replace("craft", "")
        self.type_image.type_label.text = type_text
        self.type_image.type_label.font_size = sp(23)
        self.type_image.add_widget(self.type_image.version_label)
        self.type_image.add_widget(self.type_image.type_label)
        self.add_widget(self.type_image)

        # Favorite button
        self.favorite_layout = RelativeLayout()
        favorite = None
        if not view_only:
            self.icon_button = None
            try:
                favorite = functools.partial(utility.screen_manager.current_screen.favorite, server_object.name, server_object)
            except AttributeError:
                pass

        else:
            self.icon_button = self.ChangeIconButton(self.type_image)
            self.add_widget(self.icon_button)

        if self.favorite:
            self.favorite_button = IconButton('', {}, (0, 0), (None, None), 'heart-sharp.png',
                                              clickable=not self.view_only,
                                              force_color=[[(0.05, 0.05, 0.1, 1), (0.85, 0.6, 0.9, 1)], 'pink'],
                                              anchor='right', click_func=favorite)
        else:
            self.favorite_button = IconButton('', {}, (0, 0), (None, None), 'heart-outline.png',
                                              clickable=not self.view_only, anchor='right', click_func=favorite)

        self.favorite_layout.add_widget(self.favorite_button)
        self.add_widget(self.favorite_layout)

        # Highlight border
        self.highlight_layout = RelativeLayout()
        self.highlight_border = Image()
        self.highlight_border.keep_ratio = False
        self.highlight_border.allow_stretch = True
        self.highlight_border.color = constants.brighten_color(self.color_id[1], 0.1)
        self.highlight_border.opacity = 0
        self.highlight_border.source = os.path.join(paths.ui_assets, 'server_button_highlight.png')
        self.highlight_layout.add_widget(self.highlight_border)
        self.highlight_layout.width = self.size_hint_max[0]
        self.highlight_layout.height = self.size_hint_max[1]
        self.add_widget(self.highlight_layout)

        # Toggle favorite stuffies
        self.bind(pos=self.resize_self)
        if self.favorite:
            self.toggle_favorite(self.favorite)

        # If click_function
        if click_function and not view_only:
            self.bind(on_press=click_function)

        # Animate opacity
        if fade_in > 0:
            self.opacity = 0
            self.title.opacity = 0

            Animation(opacity=1, duration=fade_in).start(self)
            Animation(opacity=1, duration=fade_in).start(self.title)
            Animation(opacity=self.subtitle.default_opacity, duration=fade_in).start(self.subtitle)

        if highlight:
            self.highlight()

    def on_enter(self, *args):
        if not self.ignore_hover:
            self.animate_button(
                image=os.path.join(paths.ui_assets, f'{self.id}{"_favorite" if self.favorite else ""}_hover.png'),
                color=self.color_id[0], hover_action=True)

            self.title.text = self.generate_name('#2D2D4E')

            if self.telepath_data:
                new_color = constants.convert_color('#E865D4' if self.favorite else '#6769D9')['rgb']
                Animation(color=new_color, duration=0.1).start(self.type_image.tp_shadow)
                Animation(color=constants.brighten_color(self.color_id[0], -0.1), duration=0.1).start(
                    self.type_image.tp_icon)

    def on_leave(self, *args):
        if not self.ignore_hover:
            self.animate_button(
                image=os.path.join(paths.ui_assets, f'{self.id}{"_favorite" if self.favorite else ""}.png'),
                color=self.color_id[1], hover_action=False)

            self.title.text = self.generate_name()

            if self.telepath_data:
                Animation(color=self.color_id[0], duration=0.1).start(self.type_image.tp_shadow)
                Animation(color=self.color_id[1], duration=0.1).start(self.type_image.tp_icon)

    def update_context_options(self):
        def _open_server(name):
            if self.telepath_data:
                constants.api_manager.request(
                    endpoint=f'/main/open_remote_server?name={constants.quote(name)}',
                    host=self.telepath_data['host'],
                    port=self.telepath_data['port'],
                    args={'none': None}
                )
                new_data = constants.deepcopy(self.telepath_data)
                new_data['name'] = name
                return constants.server_manager._init_telepathy(new_data)
            else:
                return constants.server_manager.open_server(name)

        # Functions for context menu
        def launch(*a):
            if self.telepath_data:
                open_remote_server(self.telepath_data, self.properties.name, launch=True)
            else:
                open_server(self.properties.name, launch=True)

        def restart(*a):
            _open_server(self.properties.name).restart()

        def stop(*a):
            _open_server(self.properties.name).stop()

        def settings(*a):
            _open_server(self.properties.name)
            utility.screen_manager.current = 'ServerSettingsScreen'

        def update(*a):
            settings()
            utility.screen_manager.current_screen.update_button.button.trigger_action()

        def rename(*a):
            settings()
            rename_input = utility.screen_manager.current_screen.rename_input
            utility.screen_manager.current_screen.scroll_widget.scroll_to(rename_input)
            Clock.schedule_once(rename_input.grab_focus, 0.2)

        def delete(*a):
            settings()
            delete_button = utility.screen_manager.current_screen.delete_button
            utility.screen_manager.current_screen.scroll_widget.scroll_to(delete_button, animate=False)
            Clock.schedule_once(delete_button.button.trigger_action, 0.1)

        def copy_ip(local, *a):
            def click(*a):
                clipboard_text = re.sub(r"\[.*?\]", "", self.subtitle.text.split(" ")[-1].strip())
                if not local:
                    banner_text = "Copied IP address"

                else:
                    server_obj = self.properties
                    if server_obj.running:
                        clipboard_text = server_obj.run_data['network']['private_ip'] + ':' + \
                                         server_obj.run_data['network']['address']['port']
                    banner_text = "Copied LAN IP address"

                Clock.schedule_once(
                    functools.partial(
                        utility.screen_manager.current_screen.show_banner,
                        (0.85, 0.65, 1, 1),
                        banner_text,
                        "link-sharp.png",
                        2,
                        {"center_x": 0.5, "center_y": 0.965}
                    ), 0
                )

                Clipboard.copy(clipboard_text)

            Clock.schedule_once(click, 0)

        # Context menu buttons
        if self.view_only and self.properties.running:
            self.context_options = [
                {'name': 'Copy local IP', 'icon': 'ethernet.png', 'action': functools.partial(copy_ip, True)},
                {'name': 'Copy public IP', 'icon': 'wifi.png', 'action': functools.partial(copy_ip, False)}
            ]
        else:
            if self.properties.running:
                self.context_options = [
                    {'name': 'Restart', 'icon': 'restart-server.png', 'action': restart},
                    {'name': 'Stop', 'icon': 'stop-server.png', 'action': stop},
                    {'name': 'Copy IP', 'icon': 'wifi-sharp.png', 'action': functools.partial(copy_ip, False)},
                    {'name': 'Settings', 'icon': os.path.join('sm', 'advanced.png'), 'action': settings}
                ]
            else:
                if self.properties.is_modpack == 'zip':
                    u = None
                else:
                    u = self.properties.update_string
                self.context_options = [
                    {'name': 'Launch', 'icon': 'start-server.png',
                     'action': launch} if utility.screen_manager.current_screen.name != "ServerViewScreen" else None,
                    {'name': f'Update {"build" if u.startswith("b-") else f"{u}"}', 'icon': 'arrow-up.png',
                     'action': update} if u else None,
                    {'name': 'Rename', 'icon': 'rename.png', 'action': rename},
                    {'name': 'Settings', 'icon': os.path.join('sm', 'advanced.png'), 'action': settings},
                    {'name': 'Delete', 'icon': 'trash-sharp.png', 'action': delete, 'color': 'red'}
                ]


class ServerManagerScreen(MenuBackground):

    # Toggles favorite of item, and reload list
    def favorite(self, server_name, properties):
        if properties._telepath_data:
            properties.toggle_favorite()
            bool_favorite = properties.favorite

        else:
            bool_favorite = manager.toggle_favorite(server_name)

        # Show banner
        if server_name in constants.server_manager.running_servers:
            constants.server_manager.running_servers[server_name].favorite = bool_favorite

        if bool_favorite:
            banner_message = f"'${server_name}$' marked as favorite"
        else:
            banner_message = f"'${server_name}$' is no longer marked as favorite"

        Clock.schedule_once(
            functools.partial(
                utility.screen_manager.current_screen.show_banner,
                (0.85, 0.65, 1, 1) if bool_favorite else (0.68, 0.68, 1, 1),
                banner_message,
                "heart-sharp.png" if bool_favorite else "heart-dislike-outline.png",
                2,
                {"center_x": 0.5, "center_y": 0.965}
            ), 0
        )

        constants.server_manager.refresh_list()
        self.gen_search_results(constants.server_manager.menu_view_list, fade_in=False, highlight=properties._view_name)

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

    def gen_search_results(self, results, new_search=False, fade_in=True, highlight=None, animate_scroll=True, *args):

        # Set to proper page on favorite/un-favorite
        default_scroll = 1
        if highlight:
            def divide_chunks(l, n):
                final_list = []

                for i in range(0, len(l), n):
                    final_list.append(l[i:i + n])

                return final_list

            for x, l in enumerate(divide_chunks([x._view_name for x in results], self.page_size), 1):
                if highlight in l:
                    if self.current_page != x:
                        self.current_page = x

                    # Update scroll when page is bigger than list
                    if Window.height < self.scroll_layout.height:
                        default_scroll = 1 - round(l.index(highlight) / len(l), 2)
                        if default_scroll < 0.2:
                            default_scroll = 0
                        if default_scroll > 0.97:
                            default_scroll = 1
                    break

        # Update page counter
        self.last_results = results
        self.max_pages = (len(results) / self.page_size).__ceil__()
        self.current_page = 1 if self.current_page == 0 or new_search else self.current_page

        self.page_switcher.update_index(self.current_page, self.max_pages)
        page_list = results[(self.page_size * self.current_page) - self.page_size:self.page_size * self.current_page]

        self.scroll_layout.clear_widgets()

        # Generate header
        server_count = len(constants.server_manager.menu_view_list)
        header_content = "Select a server to manage"

        for child in self.header.children:
            if child.id == "text":
                child.text = header_content
                break

        # Show servers if they exist
        if server_count != 0:

            # Clear and add all ServerButtons
            for x, server_obj in enumerate(page_list, 1):

                # Activated when server is clicked
                def view_server(server, index, *args):
                    selected_button = \
                    [item for item in self.scroll_layout.walk() if item.__class__.__name__ == "ServerButton"][index - 1]

                    # View Server
                    if selected_button.last_touch.button == "left":
                        if not selected_button.telepath_data:
                            open_server(server.name, ignore_update=False)
                        else:
                            open_remote_server(selected_button.telepath_data, server.name, ignore_update=False)

                    # Favorite
                    elif selected_button.last_touch.button == "middle":
                        self.favorite(server.name)

                # Check if updates are available
                update_banner = ""
                if server_obj.auto_update == 'true':
                    update_banner = server_obj.update_string

                # Add-on button click function
                self.scroll_layout.add_widget(
                    ScrollItem(
                        widget=ServerButton(
                            server_object=server_obj,
                            fade_in=((x if x <= 8 else 8) / self.anim_speed) if fade_in else 0,
                            highlight=(highlight == server_obj._view_name),
                            update_banner=update_banner,
                            click_function=functools.partial(
                                view_server,
                                server_obj,
                                x
                            )
                        )
                    )
                )

            self.resize_bind()

        # Go back to main menu if they don't
        else:
            utility.screen_manager.current = 'MainMenuScreen'
            utility.screen_manager.screen_tree = []
            return

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

        # Scroll list
        scroll_widget = ScrollViewWidget(position=(0.5, 0.48))
        scroll_anchor = AnchorLayout()
        self.scroll_layout = GridLayout(cols=1, spacing=15, size_hint_max_x=1250, size_hint_y=None,
                                        padding=[0, 30, 0, 30])

        # Bind / cleanup height on resize
        def resize_scroll(call_widget, grid_layout, anchor_layout, *args):
            call_widget.height = Window.height // 1.82
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
        scroll_top = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.755}, pos=scroll_widget.pos,
                                       size=(scroll_widget.width // 1.5, 60))
        scroll_bottom = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.22}, pos=scroll_widget.pos,
                                          size=(scroll_widget.width // 1.5, -60))

        # Generate buttons on page load
        header_content = "Select a server in which to manage"
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

        buttons.append(ExitButton('Back', (0.5, 0.12), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)

        menu_name = "Server Manager"
        float_layout.add_widget(generate_title("Server Manager"))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)

        # Automatically generate results on page load
        constants.server_manager.refresh_list()
        highlight = False
        self.gen_search_results(constants.server_manager.menu_view_list)

        # Highlight the last server that was last selected
        def highlight_last_server(*args):
            server_obj = constants.server_manager.current_server
            if server_obj:
                highlight = server_obj._view_name
                self.gen_search_results(constants.server_manager.menu_view_list, highlight=highlight,
                                        animate_scroll=False)

        Clock.schedule_once(highlight_last_server, 0)


class MenuTaskbar(RelativeLayout):

    def resize(self, *args):

        # Resize background
        self.bg_left.x = 0
        self.bg_right.x = self.width
        self.bg_center.x = 0 + self.bg_left.width
        self.bg_center.size_hint_max_x = self.width - (self.bg_left.width * 2)

    def show_notification(self, tile_name, show=True):
        for tile in self.taskbar.children:
            if tile_name == tile.name:
                tile.show_notification(show=show)
                break

    def __init__(self, selected_item=None, animate=False, **kwargs):
        super().__init__(**kwargs)

        server_obj = constants.server_manager.current_server

        show_addons = (server_obj.type != 'vanilla')
        server_obj.taskbar = self
        self.pos_hint = {"center_x": 0.5}

        # Layout for icon object
        class TaskbarItem(RelativeLayout):

            def show_notification(self, show=True, animate=True):
                if animate:
                    Animation(opacity=(1 if show else 0), duration=0.25, transition='in_out_sine').start(
                        self.notification)

                    def fade_in(*a):
                        Animation(opacity=(0.5 if show else 0), duration=0.15, transition='in_out_sine').start(
                            self.notification_glow)

                    Clock.schedule_once(fade_in, 0.1)

                    def fade_out(*a):
                        Animation(opacity=0, duration=0.5, transition='in_out_sine').start(self.notification_glow)

                    Clock.schedule_once(fade_out, 0.35)
                else:
                    self.notification.opacity = (1 if show else 0)

            def __init__(self, item_info, selected=False, **kwargs):
                super().__init__(**kwargs)
                new_color = constants.convert_color(item_info[2])['rgb']
                self.name = item_info[0]

                # Icon and listed functions
                class Icon(AnchorLayout, HoverBehavior):

                    # Pretty animation if specified
                    def animate(self, *args):
                        def anim_in(*args):
                            Animation(size_hint_max=(self.default_size + 6, self.default_size + 6), duration=0.15,
                                      transition='in_out_sine').start(self.icon)
                            if self.selected:
                                Animation(opacity=1, duration=0.3, transition='in_out_sine').start(self.background)
                                Animation(color=constants.brighten_color(self.hover_color, -0.87), duration=0.2,
                                          transition='in_out_sine').start(self.icon)

                        def anim_out(*args):
                            Animation(size_hint_max=(self.default_size, self.default_size), duration=0.15,
                                      transition='in_out_sine').start(self.icon)

                        Clock.schedule_once(anim_in, 0.1)
                        Clock.schedule_once(anim_out, 0.25)

                    # Execute click function
                    def on_touch_down(self, touch):
                        if self.hovered and not self.selected and not utility.screen_manager.current_screen.popup_widget:

                            # Log for crash info
                            try:
                                interaction = f"TaskbarButton ({self.data[0].title()})"
                                constants.last_widget = interaction + f" @ {constants.format_now()}"
                                send_log('navigation', f"interaction: '{interaction}'")
                            except:
                                pass

                            # Animate button
                            self.icon.color = constants.brighten_color(self.hover_color, 0.2)
                            Animation(color=self.hover_color, duration=0.3).start(self.icon)

                            utility.back_clicked = True

                            # Play yummy sound
                            audio.player.play('interaction/click_*', jitter=(0, 0.15))

                            # Return if back is clicked
                            if self.data[0] == 'back':

                                utility.screen_manager.current = 'ServerManagerScreen'
                                utility.screen_manager.screen_tree = ['MainMenuScreen']


                            # If not back, proceed to next screen
                            else:
                                # Wait for data to exist on ServerAclScreen, ServerBackupScreen, And ServerAddonScreen
                                if self.data[-1] == 'ServerAclScreen':
                                    if not constants.server_manager.current_server.acl:
                                        while not constants.server_manager.current_server.acl:
                                            time.sleep(0.2)

                                if self.data[-1] == 'ServerBackupScreen':
                                    if not constants.server_manager.current_server.backup:
                                        while not constants.server_manager.current_server.backup:
                                            time.sleep(0.2)

                                if self.data[-1] == 'ServerAddonScreen':
                                    if not constants.server_manager.current_server.addon:
                                        while not constants.server_manager.current_server.addon:
                                            time.sleep(0.2)

                                if self.data[-1] == 'ServerAmscriptScreen':
                                    if not constants.server_manager.current_server.script_manager:
                                        while not constants.server_manager.current_server.script_manager:
                                            time.sleep(0.2)

                                utility.screen_manager.current = self.data[-1]

                            utility.back_clicked = False

                        # If no button is matched, return touch to super
                        else:
                            super().on_touch_down(touch)

                    # Change attributes when hovered
                    def on_enter(self):
                        if self.ignore_hover:
                            return

                        if not self.selected:
                            Animation(size_hint_max=(self.default_size + 6, self.default_size + 6), duration=0.15,
                                      transition='in_out_sine', color=self.hover_color).start(self.icon)
                        Animation(opacity=1, duration=0.25, transition='in_out_sine').start(self.parent.text)

                    def on_leave(self):
                        self.ignore_hover = False
                        if not self.selected:
                            Animation(size_hint_max=(self.default_size, self.default_size), duration=0.15,
                                      transition='in_out_sine', color=self.default_color).start(self.icon)
                        Animation(opacity=0, duration=0.25, transition='in_out_sine').start(self.parent.text)

                    def __init__(self, **kwargs):
                        super().__init__(**kwargs)

                        self.data = item_info
                        self.default_size = 40
                        self.default_color = (0.8, 0.8, 1, 1)
                        self.selected = selected
                        self.hover_color = new_color
                        self.size_hint_max = (self.default_size + 23, self.default_size + 23)
                        self.icon = Image()
                        self.icon.size_hint_max = (self.default_size, self.default_size)
                        self.icon.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
                        self.icon.source = item_info[1]
                        self.icon.color = self.default_color

                        # Add background and change color if selected
                        if self.selected:
                            self.background = Image(source=os.path.join(paths.ui_assets, 'icons', 'sm', 'selected.png'))
                            self.background.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
                            self.background.size_hint_max = self.size_hint_max
                            self.background.color = self.hover_color
                            self.add_widget(self.background)
                            if animate:
                                self.background.opacity = 0
                            else:
                                self.icon.color = constants.brighten_color(self.hover_color, -0.87)

                        self.add_widget(self.icon)

                        # Ignore on_hover when selected widget is already selected on page load
                        self.ignore_hover = False

                        def check_prehover(*args):
                            if self.collide_point(*self.to_widget(*Window.mouse_pos)) and self.selected:
                                self.ignore_hover = True

                        Clock.schedule_once(check_prehover, 0)

                self.icon = Icon()
                self.add_widget(self.icon)

                self.text = RelativeLayout(size_hint_min=(300, 50))
                self.text.add_widget(
                    BannerObject(pos_hint={'center_x': 0.5, 'center_y': 0.75}, text=item_info[0], size=(70, 30),
                                 color=new_color))
                self.text.pos_hint = {'center_x': 0.5, 'center_y': 1}
                self.text.opacity = 0
                self.add_widget(self.text)

                # Notification icon
                self.notification_glow = Image(
                    source=os.path.join(paths.ui_assets, 'icons', 'sm', 'notification-glow.png'))
                self.notification_glow.opacity = 0
                self.notification_glow.pos_hint = {'center_x': 0.7, 'center_y': 0.7}
                self.notification_glow.size_hint_max = (27, 27)
                self.notification_glow.color = constants.convert_color('#FFC175')['rgb']
                self.add_widget(self.notification_glow)

                self.notification = Image(source=os.path.join(paths.ui_assets, 'icons', 'sm', 'notification.png'))
                self.notification.opacity = 0
                self.notification.pos_hint = {'center_x': 0.7, 'center_y': 0.7}
                self.notification.size_hint_max = (20, 20)
                self.notification.color = constants.convert_color('#FFC175')['rgb']
                self.add_widget(self.notification)

        # Icon list  (name, path, color, next_screen)
        icon_path = os.path.join(paths.ui_assets, 'icons', 'sm')
        self.item_list = [
            ('back', os.path.join(icon_path, 'back-outline.png'), '#FF6FB4'),
            ('launch', os.path.join(icon_path, 'terminal.png'), '#817EFF', 'ServerViewScreen'),
            ('back-ups', os.path.join(icon_path, 'backup.png'), '#56E6FF', 'ServerBackupScreen'),
            ('access control', os.path.join(icon_path, 'acl.png'), '#00FFB2', 'ServerAclScreen'),
            ('add-ons', os.path.join(icon_path, 'addon.png'), '#42FF5E', 'ServerAddonScreen'),
            ('amscript', os.path.join(icon_path, 'amscript.png'), '#BFFF2B', 'ServerAmscriptScreen'),
            ('settings', os.path.join(icon_path, 'advanced.png'), '#FFFF44', 'ServerSettingsScreen')
        ]

        self.y = 65
        self.size_hint_max = (500 if show_addons else 430, 64)
        self.side_width = self.size_hint_max[1] * 0.55
        self.background_color = (0.063, 0.067, 0.141, 1)

        # Define resizable background
        self.bg_left = Image()
        self.bg_left.keep_ratio = False
        self.bg_left.allow_stretch = True
        self.bg_left.size_hint_max = (self.side_width, self.size_hint_max[1])
        self.bg_left.source = os.path.join(paths.ui_assets, 'taskbar_edge.png')
        self.bg_left.color = self.background_color
        self.add_widget(self.bg_left)

        self.bg_right = Image()
        self.bg_right.keep_ratio = False
        self.bg_right.allow_stretch = True
        self.bg_right.size_hint_max = (-self.side_width, self.size_hint_max[1])
        self.bg_right.source = os.path.join(paths.ui_assets, 'taskbar_edge.png')
        self.bg_right.color = self.background_color
        self.add_widget(self.bg_right)

        self.bg_center = Image()
        self.bg_center.keep_ratio = False
        self.bg_center.allow_stretch = True
        self.bg_center.source = os.path.join(paths.ui_assets, 'taskbar_center.png')
        self.bg_center.color = self.background_color
        self.add_widget(self.bg_center)

        # Taskbar layout
        self.taskbar = BoxLayout(orientation='horizontal', padding=[5, 0, 5, 0])
        for x, item in enumerate(self.item_list):

            name = item[0]

            if name == 'add-ons' and not show_addons:
                continue

            selected = (selected_item == name)
            item = TaskbarItem(item, selected=selected)
            self.taskbar.add_widget(item)
            if animate:
                Clock.schedule_once(item.icon.animate, x / 15)

            # Show notification if appropriate
            show = False

            if name == 'settings' and server_obj.update_string:
                if 'settings' not in server_obj.viewed_notifs:
                    show = True
                elif server_obj.update_string != server_obj.viewed_notifs['settings']:
                    show = True

            elif name in server_obj.viewed_notifs:
                if not server_obj.viewed_notifs[name]:
                    show = True

            if show:
                item.show_notification(True, animate)

        self.add_widget(self.taskbar)

        self.bind(pos=self.resize, size=self.resize)
        Clock.schedule_once(self.resize, 0)


# Server Manager Launch ------------------------------------------------------------------------------------------------

# Prompt for backups and updates on new server config
def prompt_new_server(server_obj, *args):
    # Step 3 - prompt for updates
    def set_update(boolean):
        server_obj.enable_auto_update(boolean)
        server_obj.reload_config()

    def prompt_updates(*args):
        utility.screen_manager.current_screen.show_popup(
            "query",
            "Automatic Updates",
            f"Would you like to enable automatic updates for '${server_obj.name}$'?\n\nIf an update is available, auto-mcs will update this server when opened",
            [functools.partial(set_update, False),
             functools.partial(set_update, True)]
        )

    # Step 2 - apply settings from backup popup and prompt for updates
    def set_bkup_and_prompt_update(boolean):
        server_obj.backup.enable_auto_backup(boolean)
        if boolean:
            dTimer(0, server_obj.backup.save).start()

        def wait_timer(*a):
            while utility.screen_manager.current_screen.popup_widget:
                time.sleep(0.1)
            if not constants.server_manager.current_server.is_modpack or constants.server_manager.current_server.is_modpack == 'mrpack':
                Clock.schedule_once(prompt_updates, 0)

        dTimer(0, wait_timer).start()

    # Step 1 - prompt for backups
    def prompt_backup(*args):
        utility.screen_manager.current_screen.show_popup(
            "query",
            "Automatic Back-ups",
            f"Would you like to enable automatic back-ups for '${server_obj.name}$'?\n\nauto-mcs will back up this server when closed",
            [functools.partial(set_bkup_and_prompt_update, False),
             functools.partial(set_bkup_and_prompt_update, True)]
        )

    prompt_backup()


class PerformancePanel(RelativeLayout):

    def update_rect(self, *args):
        texture_offset = 70

        # Resize panel
        console_panel = utility.screen_manager.current_screen.console_panel
        self.y = console_panel.default_y + (Window.height - console_panel.size_offset[1]) - 24
        self.width = Window.width - console_panel.size_offset[0] + texture_offset
        self.height = 240

        # Repos panel widgets
        overview_max = (Window.width * 0.2)
        self.overview_widget.size_hint_max_x = overview_max if overview_max >= self.overview_min else self.overview_min

        meter_max = (Window.width * 0.32)
        self.meter_layout.size_hint_max_x = meter_max if meter_max >= self.meter_min else self.meter_min
        self.meter_layout.x = self.width - self.meter_layout.width
        for child in self.meter_layout.children:
            Clock.schedule_once(child.recalculate_size, 0)

        self.player_widget.x = self.overview_widget.x + self.overview_widget.width - texture_offset + 12
        self.player_widget.size_hint_max_x = (self.width) - self.meter_layout.width - self.overview_widget.width + (
                    texture_offset * 2) - 24
        Clock.schedule_once(self.player_widget.recalculate_size, 0)

    # Updates data in panel while the server is running
    def refresh_data(self, interval=0.5, *args):

        # Get performance stats if running locally
        server_obj = constants.server_manager.current_server

        # Prevent a crash from doing something while in the menu of a server, and current_server is reset
        if not server_obj:
            return

        if server_obj and not server_obj._telepath_data:
            dTimer(0, functools.partial(server_obj.performance_stats, interval, (self.player_clock == 3))).start()

        # If the server is running remotely, update the console text as needed
        # This should probably be moved, though, it's the only client loop
        elif utility.screen_manager.current_screen.name == 'ServerViewScreen' and server_obj._telepath_data:
            console_panel = utility.screen_manager.current_screen.console_panel
            if server_obj.running and server_obj.run_data:
                server_obj.run_data = server_obj._telepath_run_data()

                # Check if remote server has disconnected when updating panel
                if not server_obj.run_data:
                    if check_telepath_disconnect():
                        return True

                try:
                    data_len = len(console_panel.scroll_layout.data)
                    run_len = len(server_obj.run_data['log'])
                    if data_len <= run_len:
                        console_panel.update_text(server_obj.run_data['log'], animate_last=(run_len > data_len))

                    if server_obj.run_data['deadlocked']:
                        console_panel.toggle_deadlock(True)

                # If log was removed from run_data
                except KeyError:
                    pass

                # Close the console if remotely launched, and no logs exist
                if not server_obj.running or not server_obj.run_data:
                    data = server_obj._sync_telepath_stop()

                    # Prevent closing if data does not exist (Telepath re-authentication issue)
                    if not data:
                        return True

                    server_obj.crash_log = data['crash']
                    console_panel.update_text(data['log'])
                    console_panel.reset_panel(data['crash'])

                    # Before closing, save contents to temp for view screen
                    constants.folder_check(paths.temp)
                    file_name = f"{server_obj._telepath_data['display-name']}, {server_obj.name}-latest.log"
                    with open(os.path.join(paths.temp, file_name), 'w+') as f:
                        f.write(json.dumps(data['log']))

        def update_data(*args):
            try:
                perf_data = constants.server_manager.current_server.run_data['performance']
            except KeyError:
                return
            except AttributeError:
                return

            # Update meter
            self.cpu_meter.set_percent(perf_data['cpu'])
            self.ram_meter.set_percent(perf_data['ram'])

            # Update up-time
            formatted_color = '[color=#737373]'
            found = False
            for x, item in enumerate(perf_data['uptime'].split(":")):
                if x == 0 and len(item) > 2:
                    formatted_color = f'{item}:'
                    found = True
                    continue
                if x == 0 and item != '00':
                    item = int(item)
                    formatted_color += '[/color]' if len(str(item)) >= 2 else '0[/color]'
                    found = True
                if item != "00" and not found:
                    found = True
                    item = int(item)
                    formatted_color += f'[/color]{item}:' if len(str(item)) == 2 else f'0[/color]{item}:'
                else:
                    formatted_color += f'{item}:'

            # Update player count every 5 cycles
            self.player_clock += 1
            if self.player_clock > 5:
                self.player_clock = 0

                total_count = int(self.overview_widget.max_players)
                percent = (len(perf_data['current-players']) / total_count)
                self.player_widget.update_data(perf_data['current-players'])

                # Update Discord rich presence
                constants.discord_presence.update_presence('Server Manager > Launch')

                # Colors
                if percent == 0:
                    color = (0.45, 0.45, 0.45, 1)
                elif percent < 50:
                    color = (0.92, 0.92, 0.92, 1)
                elif percent < 75:
                    color = (1, 0.9, 0.5, 1)
                else:
                    color = (1, 0.53, 0.58, 1)

                Animation(color=color, duration=0.4, transition='in_out_sine').start(
                    self.overview_widget.player_label.label)
                self.overview_widget.player_label.label.text = f'{len(perf_data["current-players"])}[color=#737373] / [/color]{total_count}'

            self.overview_widget.uptime_label.text = formatted_color[:-1]
            Animation(color=(0.92, 0.92, 0.92, 1), duration=0.4, transition='in_out_sine').start(
                self.overview_widget.uptime_label.label)

        if server_obj:
            Clock.schedule_once(update_data, (interval + 0.05))

    # Sets panel back to the default state
    def reset_panel(self):
        def reset(*args):
            self.cpu_meter.set_percent(0)
            self.ram_meter.set_percent(0)
            self.overview_widget.reset_panel()
            self.player_widget.update_data(None)

        Clock.schedule_once(reset, 1.5)

    def __init__(self, server_name, **kwargs):
        super().__init__(**kwargs)

        # Apply accent color if it's different
        screen_accent = utility.screen_manager.current_screen.accent_color
        if screen_accent:
            panel_background = constants.brighten_color(screen_accent, 0.025)
            normal_accent = constants.brighten_color(screen_accent, 0.32)
            dark_accent = constants.brighten_color(screen_accent, -0.035)
        else:
            panel_background = constants.convert_color("#232439")['rgb']
            normal_accent = constants.convert_color("#707CB7")['rgb']
            dark_accent = constants.convert_color("#151523")['rgb']

        yellow_accent = (1, 0.9, 0.5, 1)
        gray_accent = (0.45, 0.45, 0.45, 1)
        green_accent = (0.3, 1, 0.6, 1)
        red_accent = (1, 0.53, 0.58, 1)

        self.overview_min = 280
        self.meter_min = 350
        self.player_clock = 0

        # Label with shadow
        class ShadowLabel(RelativeLayout):

            def __setattr__(self, attr, value):
                if "text" in attr or "color" in attr:
                    try:
                        self.label.__setattr__(attr, value)
                        self.shadow.__setattr__(attr, value)
                        Clock.schedule_once(self.on_resize, 0)
                    except AttributeError:
                        super().__setattr__(attr, value)
                else:
                    super().__setattr__(attr, value)

            def on_resize(self, *args):
                max_x = 500
                self.label.texture_update()
                self.size_hint_max = self.label.texture_size
                self.size_hint_max[0] = max_x
                self.label.size_hint_max = self.label.texture_size
                self.label.size_hint_max[0] = max_x

                self.shadow.texture_update()
                self.shadow.size_hint_max = self.shadow.texture_size
                self.shadow.size_hint_max[0] = max_x
                self.shadow.pos = (self.label.x + self.offset, self.label.y - self.offset)

            def __init__(self, text, font, size, color, align='left', offset=2, shadow_color=dark_accent,
                         __translate__=True, **kwargs):
                super().__init__(**kwargs)

                self.offset = offset

                # Shadow
                self.shadow = AlignLabel()
                self.shadow.__translate__ = __translate__
                self.shadow.text = text
                self.shadow.font_name = font
                self.shadow.font_size = size
                self.shadow.color = shadow_color
                self.shadow.halign = align
                self.add_widget(self.shadow)

                # Main label
                self.label = AlignLabel()
                self.label.__translate__ = __translate__
                self.label.text = text
                self.label.font_name = font
                self.label.font_size = size
                self.label.color = color
                self.label.halign = align
                self.label.markup = True
                self.add_widget(self.label)

                self.bind(pos=self.on_resize)
                Clock.schedule_once(self.on_resize, 0)

        # Hacky background for panel objects
        class PanelFrame(Button):

            def on_press(self):
                self.state = 'normal'
                pass

            def on_touch_down(self, touch):
                return super().on_touch_down(touch)

            def on_touch_up(self, touch):
                return super().on_touch_up(touch)

            def __init__(self, **kwargs):
                super().__init__(**kwargs)

                self.background_normal = os.path.join(paths.ui_assets, 'performance_panel.png')
                self.background_down = os.path.join(paths.ui_assets, 'performance_panel.png')
                self.background_color = panel_background
                self.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
                self.border = (60, 60, 60, 60)

        class MeterWidget(RelativeLayout):

            def set_percent(self, percent: float or int, animate=True, *args):

                # Normalize value
                self.percent = round(percent, 1)
                if percent >= 100:
                    self.percent = 100
                if percent <= 0:
                    self.percent = 0

                # Colors
                if self.percent < 5:
                    color = gray_accent
                elif self.percent < 50:
                    color = green_accent
                elif self.percent < 75:
                    color = yellow_accent
                else:
                    color = red_accent

                # Update properties
                self.percentage_label.text = f'{self.percent} %'
                new_size = round(self.progress_bg.size_hint_max_x * (self.percent / 100)) if self.percent >= 1 else 0

                Animation.stop_all(self.progress_bar)
                Animation.stop_all(self.percentage_label.label)

                if animate:
                    Animation(color=color, duration=0.3, transition='in_out_sine').start(self.percentage_label.label)
                    Animation(color=color, duration=0.3, transition='in_out_sine').start(self.progress_bar)
                    if new_size == 0:
                        Animation.stop_all(self.progress_bar)
                        Animation(color=color, size_hint_max_x=new_size, duration=0.4, transition='in_out_sine').start(
                            self.progress_bar)
                    else:
                        Animation(size_hint_max_x=new_size, duration=0.99, transition='in_out_sine').start(
                            self.progress_bar)
                else:
                    self.percentage_label.label.color = self.progress_bar.color = color
                    self.progress_bar.size_hint_max_x = new_size

            def recalculate_size(self, *args):

                # Update bar size
                padding = (self.width - self.meter_min) * 0.03
                self.progress_bg.pos = (45 + padding, 52)
                self.progress_bg.size_hint_max = (self.width - 145 - (padding * 2), 7)
                self.progress_bar.pos = (
                self.progress_bg.x, self.progress_bg.y + self.progress_bar.size_hint_max[1] + 1)
                self.set_percent(self.percent, animate=False)

                # Set text position
                text_x = self.width - self.percentage_label.width - 45 - padding
                self.percentage_label.pos = (text_x, self.progress_bar.pos[1] + 12)
                self.name.pos = (text_x, self.progress_bg.pos[1] - (self.progress_bar.size_hint_max[1] / 2))

            def __init__(self, meter_name, meter_min=350, **kwargs):
                super().__init__(**kwargs)

                self.percent = 0
                self.meter_min = meter_min

                # Background
                self.background = PanelFrame()
                self.size_hint_max_y = 152
                self.add_widget(self.background)

                # Progress bar
                self.progress_bg = Image(color=dark_accent)
                self.add_widget(self.progress_bg)

                self.progress_bar = Image(color=gray_accent)
                self.progress_bar.size_hint_max = (0, 7)
                self.add_widget(self.progress_bar)

                # Label text
                self.name = ShadowLabel(
                    __translate__=False,
                    text=meter_name,
                    font=os.path.join(paths.ui_assets, 'fonts', constants.fonts["medium"]),
                    size=sp(22),
                    color=normal_accent,
                    align='right',
                    shadow_color=(0, 0, 0, 0)
                )
                self.add_widget(self.name)

                # Percent text
                self.percentage_label = ShadowLabel(
                    __translate__=False,
                    text=f'{self.percent} %',
                    font=os.path.join(paths.ui_assets, 'fonts', constants.fonts["bold"]),
                    size=sp(30),
                    color=gray_accent,
                    offset=3,
                    align='right',
                    shadow_color=(0, 0, 0, 0)
                )
                self.add_widget(self.percentage_label)

                Clock.schedule_once(self.recalculate_size, 0)

        class OverviewWidget(RelativeLayout):

            def reset_panel(self):
                def reset_text(*args):
                    self.uptime_label.text = f'00:00:00:00'
                    self.player_label.text = f'0 / {self.max_players}'

                Animation(color=gray_accent, duration=0.4, transition='in_out_sine').start(self.uptime_label.label)
                Animation(color=gray_accent, duration=0.4, transition='in_out_sine').start(self.player_label.label)
                Clock.schedule_once(reset_text, 0.4)

            def __init__(self, overview_min=270, **kwargs):
                super().__init__(**kwargs)

                try:
                    self.max_players = constants.server_manager.current_server.server_properties['max-players']
                except KeyError:
                    self.max_players = 20

                self.background = PanelFrame()
                self.size_hint_max_x = overview_min
                self.overview_min = overview_min
                self.add_widget(self.background)

                # Up-time title
                self.uptime_title = ShadowLabel(
                    text=f'up-time',
                    font=os.path.join(paths.ui_assets, 'fonts', constants.fonts["italic"]),
                    size=sp(23),
                    color=normal_accent,
                    offset=3,
                    align='center',
                    shadow_color=constants.brighten_color(dark_accent, 0.04)
                )
                self.uptime_title.pos_hint = {'center_x': 0.5}
                self.uptime_title.y = 170
                self.add_widget(self.uptime_title)

                # Up-time label
                self.uptime_label = ShadowLabel(
                    __translate__=False,
                    text=f'00:00:00:00',
                    font=os.path.join(paths.ui_assets, 'fonts', constants.fonts["mono-bold"]) + '.otf',
                    size=sp(30),
                    color=gray_accent,
                    offset=3,
                    align='center',
                    shadow_color=(0, 0, 0, 0)
                )
                self.uptime_label.pos_hint = {'center_x': 0.5}
                self.uptime_label.y = 135
                self.add_widget(self.uptime_label)

                # Player count title
                self.player_title = ShadowLabel(
                    text=f'capacity',
                    font=os.path.join(paths.ui_assets, 'fonts', constants.fonts["italic"]),
                    size=sp(23),
                    color=normal_accent,
                    offset=3,
                    align='center',
                    shadow_color=constants.brighten_color(dark_accent, 0.04)
                )
                self.player_title.pos_hint = {'center_x': 0.5}
                self.player_title.y = 80
                self.add_widget(self.player_title)

                # Player count label
                self.player_label = ShadowLabel(
                    __translate__=False,
                    text=f'0 / {self.max_players}',
                    font=os.path.join(paths.ui_assets, 'fonts', constants.fonts["bold"]),
                    size=sp(26),
                    color=gray_accent,
                    offset=3,
                    align='center',
                    shadow_color=(0, 0, 0, 0)
                )
                self.player_label.pos_hint = {'center_x': 0.5}
                self.player_label.y = 45
                self.add_widget(self.player_label)

        class PlayerWidget(RelativeLayout):

            # Add players
            def update_data(self, player_dict):
                if player_dict:
                    if self.player_list:
                        self.player_list.rows = None

                    if self.layout.opacity == 0:
                        Animation(opacity=0, duration=0.4, transition='in_out_sine').start(self.empty_label)

                        def after_anim(*args):
                            Animation(opacity=1, duration=0.4, transition='in_out_sine').start(self.layout)

                        Clock.schedule_once(after_anim, 0.4)

                    # if self.scroll_layout.data:
                    #     self.unq_hash['before'] = self.scroll_layout.data
                    # self.unq_hash['after'] = player_dict
                    self.scroll_layout.data = player_dict

                    if self.resize_list:
                        self.resize_list()

                else:
                    if self.layout.opacity == 1:
                        Animation(opacity=0, duration=0.4, transition='in_out_sine').start(self.layout)

                        def after_anim(*args):
                            Animation(opacity=1, duration=0.4, transition='in_out_sine').start(self.empty_label)

                        Clock.schedule_once(after_anim, 0.4)

            def resize_list(self, *args):
                blank_name = ''

                data_len = len(self.scroll_layout.data)

                try:
                    if self.player_list.rows <= 5:
                        for player in self.scroll_layout.data:
                            if player['text'] == blank_name:
                                self.scroll_layout.data.remove(player)
                        data_len = len([item for item in self.scroll_layout.data if item['text'] != blank_name])
                except TypeError:
                    pass

                text_width = 240
                if self.scroll_layout.width <= 50:
                    self.recalculate_size()
                    return

                # Dirty fix to circumvent RecycleView missing data: https://github.com/kivy/kivy/pull/7262
                try:
                    text_width = int(((self.scroll_layout.width // text_width) // 1))
                    self.player_list.cols = text_width
                    self.player_list.rows = round(data_len / text_width) + 3
                    # print(text_width, self.player_list.cols, self.player_list.rows, data_len)

                    if ((
                                data_len <= self.player_list.cols) and self.player_list.rows <= 5) or data_len + 1 == self.player_list.cols:
                        if self.scroll_layout.data[-1] is not {'text': blank_name}:
                            for x in range(self.player_list.cols):
                                self.scroll_layout.data.append({'text': blank_name})
                except ZeroDivisionError:
                    pass
                except IndexError:
                    pass

            def recalculate_size(self, *args):
                texture_offset = 70
                list_offset = 15

                self.layout.pos = ((texture_offset / 2), (texture_offset / 2) + list_offset)
                self.layout.size_hint_max = (
                self.width - texture_offset, self.height - texture_offset - (list_offset * 3.5))
                self.scroll_layout.size = self.layout.size

                Clock.schedule_once(self.resize_list, 0)

            def __init__(self, **kwargs):
                super().__init__(**kwargs)

                # self.unq_hash = {'before': None, 'after': None}

                class PlayerLabel(RelativeLayout):

                    class PlayerButton(HoverButton):
                        def update_context_options(self):
                            username = self.parent.label.text
                            if not self.ignore_hover and username:

                                # Functions for context menu
                                def permissions(*a):
                                    if constants.server_manager.current_server.acl:
                                        constants.server_manager.current_server.acl.get_rule(
                                            re.sub(r"\[.*?\]", "", username))
                                        utility.back_clicked = True
                                        utility.screen_manager.current = 'ServerAclScreen'
                                        utility.back_clicked = False

                                def copy(data_type: str, *a):
                                    try:
                                        player_info = constants.server_manager.current_server.run_data['player-list'][
                                            username]
                                        text = player_info[data_type]
                                        banner_text = f'Copied ${data_type.upper().replace("USER", "username")}$ to clipboard'

                                        Clock.schedule_once(
                                            functools.partial(
                                                utility.screen_manager.current_screen.show_banner,
                                                (0.85, 0.65, 1, 1),
                                                banner_text,
                                                "link-sharp.png",
                                                2,
                                                {"center_x": 0.5, "center_y": 0.965}
                                            ), 0
                                        )

                                        Clipboard.copy(text)

                                    except KeyError:
                                        pass

                                def kick(*a):
                                    constants.server_manager.current_server.acl.kick_player(username)

                                # Context menu buttons
                                self.context_options = [
                                    {'name': 'Copy username', 'icon': 'person.png',
                                     'action': functools.partial(copy, 'user')},
                                    {'name': 'Copy UUID', 'icon': 'id-card-sharp.png',
                                     'action': functools.partial(copy, 'uuid')},
                                    {'name': 'Copy IP', 'icon': 'wifi-sharp.png',
                                     'action': functools.partial(copy, 'ip')},
                                    {'name': 'Permissions', 'icon': 'shield-half-small.png', 'action': permissions},
                                    {'name': 'Kick player', 'icon': 'exit-sharp.png', 'action': kick, 'color': 'red'}
                                ]

                    def disable(self, boolean: bool, animate=False):
                        def disable(*a):
                            self.button.ignore_hover = boolean
                            utility.hide_widget(self, boolean)
                            utility.hide_widget(self.button, boolean)
                            self.button.disabled = boolean

                        if animate:
                            duration = 0.3

                            if not boolean:
                                disable()

                            self.opacity = (1 if boolean else 0)
                            Animation.stop_all(self)
                            Animation(opacity=(0 if boolean else 1), duration=duration).start(self)

                            if boolean:
                                Clock.schedule_once(disable, duration + 0.1)

                        else:
                            disable()

                    def check_anim(self, value):
                        animate = (self.name_value or value)
                        if self.parent:
                            panel = self.parent.parent.parent.parent
                            animate = animate and (panel.unq_hash['before'] != panel.unq_hash['after'])
                        self.disable(not bool(value), animate)

                    def __setattr__(self, attr, value):
                        super().__setattr__(attr, value)

                        # Change attributes dynamically based on rule
                        if attr == "text" and value:
                            # Update text
                            self.label.text = value.strip()

                            # Update font size
                            self.label.font_size = sp(
                                22 - (0 if len(self.label.text) < 11 else (len(self.label.text) // 3)))

                            # Update icon
                            def update_source(*a):
                                source = manager.get_player_head(value.strip())

                                def main_thread(*b):
                                    self.icon.source = source

                                Clock.schedule_once(main_thread, 0)

                            dTimer(0, update_source).start()

                        if attr == "text":
                            # self.check_anim(value)
                            self.disable(not bool(value), False)
                            self.name_value = value

                        if attr == "color" and value:
                            self.color_values = [(value[0], value[1], value[2], 0.75), value]
                            self.button.background_color = self.color_values[0]
                            label_color = Color(*self.color_values[1])
                            label_color.v -= 0.68
                            label_color.s += 0.05
                            self.label.color = label_color.rgba

                    def __init__(self, **kwargs):
                        super().__init__(**kwargs)

                        size = (215, 45)
                        name = 'player_label'
                        position = (0.5, 0.5)
                        self.name_value = None
                        self.color_values = [(0.8, 0.8, 0.8, 0), (1, 1, 1, 0)]

                        self.id = name
                        self.size_hint_max = size
                        self.size_hint_min = size

                        self.button = self.PlayerButton()
                        self.button.id = 'player_button'
                        self.button.border = (20, 20, 20, 20)
                        self.button.size_hint_max = size
                        self.button.size_hint_min = size
                        self.button.background_normal = os.path.join(paths.ui_assets, f'{self.button.id}.png')
                        self.button.background_down = os.path.join(paths.ui_assets, f'{self.button.id}.png')

                        self.label = AlignLabel()
                        self.label.__translate__ = False
                        self.label.halign = 'left'
                        self.label.valign = 'center'
                        self.label.id = 'label'
                        self.label.size_hint_max = size
                        self.label.pos_hint = {"center_x": position[0] + 0.18, "center_y": position[1] - 0.02}
                        self.label.text = name.upper()
                        self.label.font_size = sp(22)
                        self.label.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["bold"]}.ttf')
                        self.label.color = dark_accent

                        def on_touch_down(touch, *a):
                            super(Label, self.label).on_touch_down(touch)

                        self.label.on_touch_down = on_touch_down

                        # Button click behavior
                        def click_func(*a):
                            if not self.button.ignore_hover and self.label.text and self.button.last_touch.button == 'left':
                                if constants.server_manager.current_server.acl:
                                    constants.server_manager.current_server.acl.get_rule(
                                        re.sub(r"\[.*?\]", "", self.label.text))
                                    utility.back_clicked = True
                                    utility.screen_manager.current = 'ServerAclScreen'
                                    utility.back_clicked = False

                        def hover(enter=True, *a):
                            Animation.stop_all(self.button)
                            Animation.stop_all(self.hicon)
                            Animation(opacity=(0.25 if enter else 0), duration=0.12).start(self.hicon)
                            Animation(background_color=self.color_values[1 if enter else 0], duration=0.12).start(
                                self.button)

                        self.button.bind(on_press=click_func)
                        self.button.on_enter = functools.partial(hover, True)
                        self.button.on_leave = functools.partial(hover, False)
                        self.add_widget(self.button)

                        self.picon = Image()
                        self.picon.id = 'icon_placeholder'
                        self.picon.size_hint_max_y = size[1]
                        self.picon.pos_hint = {'center_x': 0.09}
                        self.picon.source = os.path.join(paths.ui_assets, 'steve.png')
                        self.add_widget(self.picon)

                        self.icon = AsyncImage()
                        self.icon.anim_delay = utility.anim_speed * 0.02
                        self.icon.id = 'icon'
                        self.icon.nocache = False
                        self.icon.size_hint_max_y = size[1]
                        self.icon.pos_hint = {'center_x': 0.09}
                        self.icon.source = os.path.join(paths.ui_assets, 'steve.png')
                        self.add_widget(self.icon)

                        self.hicon = Image()
                        self.hicon.id = 'icon_highlight'
                        self.hicon.size_hint_max_y = size[1]
                        self.hicon.pos_hint = {'center_x': 0.09}
                        self.hicon.source = os.path.join(paths.ui_assets, 'head_highlight.png')
                        self.hicon.opacity = 0
                        self.add_widget(self.hicon)

                        self.add_widget(self.label)

                self.background = PanelFrame()
                self.add_widget(self.background)

                self.current_players = None
                self.padding = 10

                # List layout
                self.layout = RelativeLayout()
                self.layout.opacity = 0
                self.layout_bg = Image(source=os.path.join(paths.ui_assets, 'performance_panel_background.png'))
                self.layout_bg.allow_stretch = True
                self.layout_bg.keep_ratio = False
                self.layout_bg.color = constants.brighten_color(panel_background, -0.015)
                self.layout.add_widget(self.layout_bg)

                # Player layout
                self.scroll_layout = RecycleViewWidget(position=None, view_class=PlayerLabel)
                self.scroll_layout.always_overscroll = False
                self.scroll_layout.scroll_wheel_distance = dp(50)
                self.player_list = RecycleGridLayout(size_hint_y=None, default_size=(240, 50),
                                                     padding=[self.padding, 3, self.padding, -20], spacing=[0, 8])
                self.player_list.bind(minimum_height=self.player_list.setter('height'))
                self.scroll_layout.add_widget(self.player_list)
                self.layout.add_widget(self.scroll_layout)
                self.add_widget(self.layout)

                # List shadow
                self.layout_shadow = Image(source=os.path.join(paths.ui_assets, 'performance_panel_shadow.png'))
                self.layout_shadow.allow_stretch = True
                self.layout_shadow.keep_ratio = False
                self.layout.add_widget(self.layout_shadow)

                # Player title
                self.title = ShadowLabel(
                    text=f'connected players',
                    font=os.path.join(paths.ui_assets, 'fonts', constants.fonts["italic"]),
                    size=sp(23),
                    color=normal_accent,
                    offset=3,
                    align='center',
                    shadow_color=constants.brighten_color(dark_accent, 0.04)
                )
                self.title.pos_hint = {'center_x': 0.5}
                self.title.y = 170
                self.add_widget(self.title)

                # Empty label
                self.empty_label = ShadowLabel(
                    text=f'*crickets*',
                    font=os.path.join(paths.ui_assets, 'fonts', constants.fonts["italic"]),
                    size=sp(24),
                    color=gray_accent,
                    offset=3,
                    align='center',
                    shadow_color=(0, 0, 0, 0)
                )
                self.empty_label.pos_hint = {'center_x': 0.5}
                self.empty_label.y = 95
                self.add_widget(self.empty_label)

                Clock.schedule_once(self.recalculate_size, 0)

        self.title_text = "Paragraph"
        self.size_hint = (None, None)
        self.size_hint_max = (None, None)
        self.pos_hint = {"center_x": 0.5}

        # Add widgets to layouts

        # Overview widget
        self.overview_widget = OverviewWidget(overview_min=self.overview_min)
        self.add_widget(self.overview_widget)

        # Player widget
        self.player_widget = PlayerWidget()
        self.add_widget(self.player_widget)

        # Meter widgets
        self.meter_layout = RelativeLayout(size_hint_max_x=self.meter_min)
        self.cpu_meter = MeterWidget(meter_name='CPU', pos_hint={'center_y': 0.684}, meter_min=self.meter_min)
        self.ram_meter = MeterWidget(meter_name='RAM', pos_hint={'center_y': 0.316}, meter_min=self.meter_min)
        self.meter_layout.add_widget(self.ram_meter)
        self.meter_layout.add_widget(self.cpu_meter)
        self.add_widget(self.meter_layout)

        self.bind(pos=self.update_rect)
        self.bind(size=self.update_rect)
        Clock.schedule_once(self.update_rect, 0)


class ConsolePanel(FloatLayout):

    # Update process to communicate with
    def update_process(self, run_data, *args):

        self.run_data = run_data

        # Close panel if telepath server closed immediately
        server_obj = constants.server_manager.current_server

        if server_obj._telepath_data:
            def check_for_crash(*a):
                data = server_obj._sync_telepath_stop(reset=False)
                if data['crash']:
                    server_obj.crash_log = data['crash']
                    self.update_text(data['log'])
                    self.reset_panel(data['crash'])

                    # Before closing, save contents to temp for view screen
                    constants.folder_check(paths.temp)
                    file_name = f"{server_obj._telepath_data['display-name']}, {server_obj.name}-latest.log"
                    with open(os.path.join(paths.temp, file_name), 'w+') as f:
                        f.write(json.dumps(data['log']))

            Clock.schedule_once(check_for_crash, 1)

        try:
            if self.update_text not in self.run_data['process-hooks']:
                self.run_data['process-hooks'].append(self.update_text)

            if self.reset_panel not in self.run_data['close-hooks']:
                self.run_data['close-hooks'].append(self.reset_panel)

            self.update_text(self.run_data['log'])

            def update_scroll(*args):
                if (self.console_text.height > self.scroll_layout.height - self.console_text.padding[-1]):
                    self.scroll_layout.scroll_y = 0

            Clock.schedule_once(update_scroll, 0)

        except KeyError:
            pass

    # Updates RecycleView text with console text
    def update_text(self, text, force_scroll=False, animate_last=True, *args):
        current_filter = self.filter_menu.current_filter
        self._unfiltered_text = text

        # Filterrrr oh yeah
        if current_filter != 'everything':
            event_whitelist = ['INIT', 'START', 'STOP', 'SUCCESS']

            if current_filter == 'errors':
                event_whitelist.extend(['WARN', 'ERROR', 'CRITICAL', 'SEVERE', 'FATAL'])

            elif current_filter == 'players':
                event_whitelist.extend(['CHAT', 'PLAYER'])

            elif current_filter == 'amscript':
                event_whitelist.extend(['AMS', 'EXEC'])

            text = [l for l in text if l['text'][1] in event_whitelist]

        original_scroll = self.scroll_layout.scroll_y
        original_len = len(self.scroll_layout.data)
        label_height = 41.8
        self.scroll_layout.data = text

        # Make the console sticky if scrolled to the bottom of the viewport
        viewport_size = self.scroll_layout.height - self.console_text.padding[-1] - self.console_text.padding[1]
        if (len(self.scroll_layout.data) * label_height > viewport_size) and (
                (original_scroll == 0 or not self.auto_scroll) or force_scroll):
            self.scroll_layout.scroll_y = 0
            self.auto_scroll = True


        # Temporary fix to prevent console text from moving when new data is added
        else:

            delta = self.scroll_layout.convert_distance_to_scroll(0, (
                        (len(self.scroll_layout.data) * label_height) * (1 - self.scroll_layout.scroll_y)) - (
                                                                              (original_len * label_height) * (
                                                                                  1 - original_scroll)))[1]
            if delta:
                final_scroll = self.scroll_layout.scroll_y + delta

                if final_scroll > 1:
                    final_scroll = 1
                elif final_scroll < 0:
                    final_scroll = 0

                self.scroll_layout.scroll_y = final_scroll

        def fade_animation(*args):
            for label in self.console_text.children:
                Animation.stop_all(label.anim_cover)
                Animation.stop_all(label.main_label)
                label.main_label.opacity = 1
                label.anim_cover.opacity = 0
                try:
                    if label.original_text == self.scroll_layout.data[-1]['text']:
                        label.main_label.opacity = 0
                        label.anim_cover.opacity = 1
                        Animation(opacity=1, duration=0.3).start(label.main_label)
                        Animation(opacity=0, duration=0.3).start(label.anim_cover)
                except:
                    pass

        if len(text) > original_len and animate_last:
            Clock.schedule_once(fade_animation, -1)

        # Update selection coordinates if they exist
        if self.last_self_touch:
            lst = self.last_self_touch
            self.last_self_touch = (lst[0], lst[1] + ((len(self.scroll_layout.data) - original_len) * label_height))

    # Fit background color across screen for transitions, and fix position
    def update_size(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

        self.scroll_layout.height = self.height - self.input.height
        self.scroll_layout.width = self.width
        self.scroll_layout.x = self.x
        self.scroll_layout.y = self.y + self.input.height

        self.console_text.width = self.width

        self.input.pos = (self.x, self.y)

        self.gradient.pos = (self.input.pos[0], self.pos[1] + (self.input.height * 1.2))
        self.gradient.width = self.scroll_layout.width - self.scroll_layout.bar_width
        self.gradient.height = 0 - (self.input.height * 0.5)

        self.input_background.pos = (self.pos[0] - 22, self.pos[1] + 8)

        # Corner resize
        offset = self.corner_size
        self.corner_mask.size_hint_max = (self.size[0] - offset, self.size[1] - offset)
        self.corner_mask.pos = (self.x + (offset / 2), self.y + (offset / 2))
        self.corner_mask.sl.size_hint_max_y = self.height - (self.corner_size * 2)
        self.corner_mask.sr.size_hint_max_y = self.height - (self.corner_size * 2)
        self.corner_mask.sb.size_hint_max_x = self.width - (self.corner_size * 2)
        self.corner_mask.st.size_hint_max_x = self.width - (self.corner_size * 2)

        # Console panel resize:
        texture = self.controls.background.texture_size
        self.controls.background.size_hint_max = (
        texture[0] + (self.height - texture[1]) + 200, texture[1] + (self.height - texture[1]))
        if self.full_screen == "animate":
            pass
        elif self.full_screen:
            self.size_hint_max = (Window.width, Window.height - self.full_screen_offset)
            self.y = 47
        else:
            self.size_hint_max = (Window.width - self.size_offset[0], Window.height - self.size_offset[1])
            self.y = self.default_y

        self.stop_click.size = self.size
        self.stop_click.pos = self.pos

        # Console controls resize
        self.controls.size = self.size
        self.controls.pos = self.pos

        shadow_size = self.controls.control_shadow.size
        self.controls.control_shadow.pos = (self.width - shadow_size[0], self.height - shadow_size[1])

        # Control buttons
        if self.controls.maximize_button and self.controls.stop_button and self.controls.restart_button and not self.full_screen:
            self.controls.view_button.pos = (self.width - 142, self.height - 80) if self.log_view else (
            self.width - 90, self.height - 80)
            self.controls.maximize_button.pos = (self.width - 90, self.height - 80)
            self.controls.stop_button.pos = (self.width - 142, self.height - 80)
            self.controls.restart_button.pos = (self.width - 194, self.height - 80)
            self.controls.filter_button.pos = (self.width - 246, self.height - 80)

        # Fullscreen shadow
        self.fullscreen_shadow.y = self.height + self.x - 3 + 25
        self.fullscreen_shadow.width = Window.width

        # Controls background
        def resize_background(*args):
            self.controls.background_ext.x = self.controls.background.width
            self.controls.background_ext.size_hint_max_x = self.width - self.controls.background.width

        Clock.schedule_once(resize_background, 0)

    # Launch server and update properties
    def launch_server(self, animate=True, wait_for_ip=True, *args):
        self.update_size()
        self.toggle_deadlock(False)
        self.selected_labels = []

        for k in self.parent._ignore_keys:
            if k == 'f':
                self.parent._ignore_keys.remove(k)

        anim_duration = 0.15 if animate else 0
        self.scroll_layout.scroll_y = 1
        self.auto_scroll = False

        # Animate panel
        self.controls.launch_button.disabled = True
        self.controls.log_button.disabled = True
        utility.hide_widget(self.controls.maximize_button, False)
        utility.hide_widget(self.controls.stop_button, False)
        utility.hide_widget(self.controls.restart_button, False)
        utility.hide_widget(self.controls.filter_button, False)
        self.controls.maximize_button.opacity = 0
        self.controls.stop_button.opacity = 0
        self.controls.restart_button.opacity = 0
        self.controls.filter_button.opacity = 0

        self.controls.crash_text.clear_text()

        if self.controls.view_button:
            Animation(opacity=0, duration=anim_duration).start(self.controls.view_button)
        Animation(opacity=0, duration=anim_duration).start(self.controls.button_shadow)
        Animation(opacity=0, duration=anim_duration).start(self.controls.background)
        Animation(opacity=0, duration=anim_duration).start(self.controls.background_ext)
        Animation(opacity=0, duration=(anim_duration * 1.5) if animate else 0).start(self.controls.launch_button)
        Animation(opacity=0, duration=(anim_duration * 1.5) if animate else 0).start(self.controls.log_button)

        def after_anim(*a):
            self.controls.maximize_button.disabled = False
            self.controls.stop_button.disabled = False
            self.controls.restart_button.disabled = False
            self.controls.filter_button.disabled = False
            self.controls.remove_widget(self.controls.launch_button)
            self.controls.remove_widget(self.controls.log_button)
            self.controls.remove_widget(self.controls.view_button)
            self.controls.launch_button.button.on_leave()
            self.controls.log_button.button.on_leave()
            self.controls.view_button.button.on_leave()

            def delay(function, obj, delay):
                def anim_delay(*a):
                    function.start(obj)

                Clock.schedule_once(anim_delay, delay)

            delay(Animation(opacity=1, duration=(anim_duration * 2.7) if animate else 0, transition='in_out_sine'),
                  self.controls.filter_button, 0.18)
            delay(Animation(opacity=1, duration=(anim_duration * 2.7) if animate else 0, transition='in_out_sine'),
                  self.controls.restart_button, 0.12)
            delay(Animation(opacity=1, duration=(anim_duration * 2.7) if animate else 0, transition='in_out_sine'),
                  self.controls.stop_button, 0.06)
            Animation(opacity=1, duration=(anim_duration * 2.7) if animate else 0, transition='in_out_sine').start(
                self.controls.maximize_button)

        # Update IP info at the top of the ServerViewScreen
        def update_launch_data(*args):
            if self.server_button: self.server_button.update_subtitle(self.run_data)

        Clock.schedule_once(update_launch_data, 3 if wait_for_ip else 1)
        if wait_for_ip:
            for x in range(6): Clock.schedule_once(update_launch_data, x * 5)

        # Show telepath banner when server is started remotely
        server_obj = constants.server_manager.current_server
        if wait_for_ip and server_obj._telepath_data:
            constants.api_manager.request(
                endpoint='/main/telepath_banner',
                host=server_obj._telepath_data['host'],
                port=server_obj._telepath_data['port'],
                args={'message': f"$Telepath$ action: Launched '${server_obj.name}$'", 'finished': True}
            )

        Clock.schedule_once(after_anim, (anim_duration * 1.51) if animate else 0)

        # Actually launch server
        def start_timer(*_):
            server_obj = utility.screen_manager.current_screen.server

            # Play sound
            if not server_obj.running: audio.player.play('interaction/launch_*', volume=0.85)

            if server_obj._telepath_data:
                boot_text = f"Connecting to '{server_obj._view_name}', please wait..."
            else:
                boot_text = f"Launching '{server_obj.name}', please wait..."

            text_list = [{'text': (
            dt.now().strftime(constants.fmt_date("%#I:%M:%S %p")).rjust(11), 'INIT', boot_text, (0.7, 0.7, 0.7, 1))}]

            if server_obj.proxy_enabled and server_obj.proxy_installed():
                text_list.append({'text': (
                dt.now().strftime(constants.fmt_date("%#I:%M:%S %p")).rjust(11), 'INFO', 'Initializing playit agent...',
                (0.6, 0.6, 1, 1))})

            self.update_text(text=text_list)
            while not all(server_obj._check_object_init().values()):
                time.sleep(0.05)

            self.update_process(utility.screen_manager.current_screen.server.launch())

            # Start performance counter
            try:
                utility.screen_manager.current_screen.set_timer(True)
            except AttributeError:
                pass

            self.input.disabled = False
            constants.server_manager.current_server.run_data['console-panel'] = self
            constants.server_manager.current_server.run_data['performance-panel'] = self.performance_panel

            # Update Discord rich presence
            constants.discord_presence.update_presence('Server Manager > Launch')

        dTimer(0, start_timer).start()

        # Show pop-up to ask user for initial user feedback
        try:
            if constants.app_config.prompt_feedback and constants.app_online:
                constants.app_config.prompt_feedback = False

                def open_feedback(*a):
                    url = "https://www.auto-mcs.com/feedback"
                    webbrowser.open_new_tab(url)

                Clock.schedule_once(
                    functools.partial(
                        utility.screen_manager.current_screen.show_popup,
                        "query",
                        "Share Your Feedback",
                        "Thanks for using $auto-mcs$!\n\nWhile your server is launching, please take a moment to leave us your feedback",
                        (None, dTimer(0, open_feedback).start)
                    ),
                    1
                )
        except:
            pass

    # Stop server
    def stop_server(self, *args):
        if self.run_data:
            utility.screen_manager.current_screen.server.stop()

        # Show deadlocked icon after stopping
        Clock.schedule_once(self.toggle_deadlock, 1)

    # Kills running process forcefully
    def kill_server(self, *args):
        if self.run_data:
            utility.screen_manager.current_screen.server.kill()

    # Restart server
    def restart_server(self, *args):
        if self.run_data and not self.deadlocked:
            utility.screen_manager.current_screen.server.restart()
            self.toggle_deadlock(False)

    # Called from ServerObject when process stops
    def reset_panel(self, crash=None):
        if self.server_obj.restart_flag:
            return

        def reset(*args):
            server_obj = constants.server_manager.current_server

            # Show crash banner if not on server screen
            def show_crash_banner(*args):
                if crash:
                    Clock.schedule_once(
                        functools.partial(
                            utility.screen_manager.current_screen.show_banner,
                            (1, 0.5, 0.65, 1),
                            f"'${self.server_name}$' has crashed",
                            "close-circle-sharp.png",
                            2.5,
                            {"center_x": 0.5, "center_y": 0.965}
                        ), 0
                    )

            # Ignore if screen isn't visible or a different server
            if not (utility.screen_manager.current_screen.name == 'ServerViewScreen'):
                show_crash_banner()

                # Update caption on list if user is staring at it for some reason
                if (utility.screen_manager.current_screen.name == 'ServerManagerScreen'):
                    for button in utility.screen_manager.current_screen.scroll_layout.children:
                        button = button.children[0]
                        if button.title.text.strip() == self.server_name:
                            button.update_subtitle(None, dt.now())
                            break
                return

            if utility.screen_manager.current_screen.server.name != self.server_name or not self.run_data:
                show_crash_banner()
                return

            # Do things when on server launch screen
            utility.screen_manager.current_screen.set_timer(False)
            utility.screen_manager.current_screen.performance_panel.reset_panel()
            try:
                if 'f' not in self.parent._ignore_keys:
                    self.parent._ignore_keys.append('f')

            # Return if parent is None-type (screen does not exist)
            except AttributeError:
                return

            # Before deleting run data, save log to a file
            if not server_obj._telepath_data:
                constants.folder_check(paths.temp)
                file_name = f"{server_obj.name}-latest.log"
                with open(os.path.join(paths.temp, file_name), 'w+') as f:
                    f.write(json.dumps(self.run_data['log']))

            self.run_data = None
            self.ignore_keypress = True

            if self.parent.server_button:
                self.parent.server_button.update_subtitle(self.run_data, dt.now())

            # Hide filter if it's visible
            if self.filter_menu.visible:
                self.filter_menu.hide()

            # Else, reset it back to normal
            def disable_buttons(*a):
                utility.hide_widget(self.controls.maximize_button, True)
                utility.hide_widget(self.controls.stop_button, True)
                utility.hide_widget(self.controls.restart_button, True)
                utility.hide_widget(self.controls.filter_button, True)
                self.controls.control_shadow.opacity = 0

            if self.full_screen:
                self.maximize(False)
                disable_buttons()

            def after_anim(*a):
                anim_speed = 0.15

                # Update crash widgets
                if crash:
                    self.controls.log_button.disabled = False
                    self.controls.log_button.opacity = 0
                    self.controls.add_widget(self.controls.log_button)
                    Animation(opacity=1, duration=anim_speed).start(self.controls.log_button)
                    self.controls.crash_text.update_text(f"Uh oh, '${self.server_name}$' has crashed", False)

                # Animate panel
                self.controls.launch_button.disabled = False
                self.input.disabled = True
                self.input.text = ''

                self.controls.launch_button.opacity = 0
                self.controls.add_widget(self.controls.launch_button)

                Animation(opacity=1, duration=anim_speed).start(self.controls.button_shadow)
                Animation(opacity=1, duration=anim_speed).start(self.controls.launch_button)
                Animation(opacity=1, duration=anim_speed).start(self.controls.background)
                Animation(opacity=1, duration=anim_speed).start(self.controls.background_ext)

                if self.controls.maximize_button.opacity > 0:
                    Animation(opacity=0, duration=anim_speed).start(self.controls.maximize_button)
                    Animation(opacity=0, duration=anim_speed).start(self.controls.stop_button)
                    Animation(opacity=0, duration=anim_speed).start(self.controls.restart_button)
                    Animation(opacity=0, duration=anim_speed).start(self.controls.filter_button)
                    Clock.schedule_once(disable_buttons, anim_speed * 1.1)

                def after_anim2(*a):
                    self.toggle_deadlock(False)
                    self.controls.maximize_button.disabled = False
                    self.controls.stop_button.disabled = False
                    self.controls.restart_button.disabled = False
                    self.controls.filter_button.disabled = False
                    self.scroll_layout.data = []
                    self.controls.control_shadow.opacity = 1

                    # View log button
                    self.add_log_button()

                    # Update Discord rich presence
                    constants.discord_presence.update_presence('Server Manager > Launch')

                Clock.schedule_once(after_anim2, (anim_speed * 1.51))

            Clock.schedule_once(after_anim, 1.5)

        Clock.schedule_once(reset, 0)

        # Prompt new server to enable automatic backups and updates
        if not crash and (self.server_obj.auto_update == 'prompt' or self.server_obj.backup._backup_stats[
            'auto-backup'] == 'prompt'):
            Clock.schedule_once(functools.partial(prompt_new_server, self.server_obj))

    # Toggles full screen on the console
    def maximize(self, maximize=True, *args):

        # Make sure the buttons exist
        if 'f' in self.parent._ignore_keys and maximize and not self.log_view or self.full_screen == 'animate':
            return

        try:
            test = self.controls.maximize_button.button.hovered
        except AttributeError:
            return

        anim_speed = 0.135
        self.full_screen = "animate"

        # Fix scrolling
        def fix_scroll(*a):
            if (self.console_text.height > self.scroll_layout.height):
                Animation(scroll_y=0, duration=anim_speed, transition='out_sine').start(self.scroll_layout)
            else:
                Animation(scroll_y=1, duration=anim_speed, transition='out_sine').start(self.scroll_layout)

        # Entering full screen
        if maximize:
            Animation(size_hint_max=(Window.width, Window.height - self.full_screen_offset), y=47, duration=anim_speed,
                      transition='out_sine').start(self)

            # If server is not running
            if self.log_view:

                # Hide log button
                self.controls.remove_widget(self.controls.view_button)
                del self.controls.view_button
                self.controls.view_button = IconButton('hide log', {}, (71, 150), (None, None), 'hide-log.png',
                                                       clickable=True, anchor='right',
                                                       force_color=self.button_colors['maximize'],
                                                       click_func=self.hide_log)
                self.controls.view_button.opacity = 0
                self.controls.add_widget(self.controls.view_button)

                # Filter button
                self.controls.remove_widget(self.controls.filter_button)
                del self.controls.filter_button
                self.controls.filter_button = IconButton('filter', {}, (123, 150), (None, None), 'filter-sharp.png',
                                                         clickable=True, anchor='right', text_offset=(9, 50),
                                                         force_color=self.button_colors['filter'],
                                                         click_func=self.filter_menu.show,
                                                         text_hover_color=(0.722, 0.722, 1, 1))
                self.controls.filter_button.opacity = 0
                self.controls.add_widget(self.controls.filter_button)

                def after_anim(*a):
                    self.full_screen = True
                    self.ignore_keypress = False
                    Animation(opacity=0, duration=(anim_speed * 0.1), transition='out_sine').start(self.corner_mask)
                    Animation(opacity=1, duration=(anim_speed * 0.1), transition='out_sine').start(
                        self.fullscreen_shadow)
                    Animation(opacity=1, duration=anim_speed, transition='out_sine').start(self.controls.view_button)
                    Animation(opacity=1, duration=anim_speed, transition='out_sine').start(self.controls.filter_button)

                Clock.schedule_once(after_anim, (anim_speed * 1.1))


            # If server is running
            else:

                # Full screen button
                self.controls.remove_widget(self.controls.maximize_button)
                del self.controls.maximize_button
                self.controls.maximize_button = IconButton('minimize', {}, (71, 150), (None, None), 'minimize.png',
                                                           clickable=True, anchor='right',
                                                           force_color=self.button_colors['maximize'],
                                                           click_func=functools.partial(self.maximize, False))
                self.controls.maximize_button.opacity = 0
                self.controls.add_widget(self.controls.maximize_button)

                # Stop server button
                self.controls.remove_widget(self.controls.stop_button)
                del self.controls.stop_button
                if not self.deadlocked:
                    self.controls.stop_button = IconButton('stop server', {}, (123, 150), (None, None),
                                                           'stop-server.png', clickable=True, anchor='right',
                                                           text_offset=(13, 50), force_color=self.button_colors['stop'],
                                                           click_func=self.stop_server,
                                                           text_hover_color=(0.85, 0.7, 1, 1))
                else:
                    self.controls.stop_button = IconButton('kill server', {}, (123, 150), (None, None),
                                                           'kill-server.png', clickable=True, anchor='right',
                                                           text_offset=(13, 50), force_color=self.button_colors['stop'],
                                                           click_func=self.kill_server,
                                                           text_hover_color=(0.85, 0.7, 1, 1))
                self.controls.stop_button.opacity = 0
                self.controls.add_widget(self.controls.stop_button)

                # Restart server button
                self.controls.remove_widget(self.controls.restart_button)
                del self.controls.restart_button
                self.controls.restart_button = IconButton('restart server', {}, (175, 150), (None, None),
                                                          'restart-server.png', clickable=True, anchor='right',
                                                          text_offset=(-25, 50), force_color=self.button_colors['stop'],
                                                          click_func=self.restart_server,
                                                          text_hover_color=(0.85, 0.7, 1, 1))
                self.controls.restart_button.opacity = 0
                self.controls.add_widget(self.controls.restart_button)

                # Filter button
                self.controls.remove_widget(self.controls.filter_button)
                del self.controls.filter_button
                self.controls.filter_button = IconButton('filter', {}, (227, 150), (None, None), 'filter-sharp.png',
                                                         clickable=True, anchor='right', text_offset=(9, 50),
                                                         force_color=self.button_colors['filter'],
                                                         click_func=self.filter_menu.show,
                                                         text_hover_color=(0.722, 0.722, 1, 1))
                self.controls.filter_button.opacity = 0
                self.controls.add_widget(self.controls.filter_button)

                def after_anim(*a):
                    self.full_screen = True
                    self.ignore_keypress = False
                    Animation(opacity=0, duration=(anim_speed * 0.1), transition='out_sine').start(self.corner_mask)
                    Animation(opacity=1, duration=(anim_speed * 0.1), transition='out_sine').start(
                        self.fullscreen_shadow)
                    Animation(opacity=1, duration=anim_speed, transition='out_sine').start(
                        self.controls.maximize_button)
                    Animation(opacity=1, duration=anim_speed, transition='out_sine').start(self.controls.stop_button)
                    Animation(opacity=1, duration=anim_speed, transition='out_sine').start(self.controls.restart_button)
                    Animation(opacity=1, duration=anim_speed, transition='out_sine').start(self.controls.filter_button)
                    fix_scroll()

                Clock.schedule_once(after_anim, (anim_speed * 1.1))


        # Exiting full screen
        else:
            Animation(size_hint_max=(Window.width - self.size_offset[0], Window.height - self.size_offset[1]),
                      y=self.default_y, duration=anim_speed, transition='out_sine').start(self)
            Animation(opacity=1, duration=(anim_speed * 0.1), transition='out_sine').start(self.corner_mask)
            Animation(opacity=0, duration=(anim_speed * 0.1), transition='out_sine').start(self.fullscreen_shadow)

            # Full screen button
            self.controls.remove_widget(self.controls.maximize_button)
            del self.controls.maximize_button
            self.controls.maximize_button = RelativeIconButton('maximize', {}, (20, 20), (None, None), 'maximize.png',
                                                               clickable=True, anchor='right', text_offset=(24, 80),
                                                               force_color=self.button_colors['maximize'],
                                                               click_func=functools.partial(self.maximize, True))
            self.controls.maximize_button.opacity = 0
            self.controls.add_widget(self.controls.maximize_button)

            # Stop server button
            self.controls.remove_widget(self.controls.stop_button)
            del self.controls.stop_button
            if not self.deadlocked:
                self.controls.stop_button = RelativeIconButton('stop server', {}, (20, 20), (None, None),
                                                               'stop-server.png', clickable=True, anchor='right',
                                                               text_offset=(8, 80),
                                                               force_color=self.button_colors['stop'],
                                                               click_func=self.stop_server,
                                                               text_hover_color=(0.85, 0.7, 1, 1))
            else:
                self.controls.stop_button = RelativeIconButton('kill server', {}, (20, 20), (None, None),
                                                               'kill-server.png', clickable=True, anchor='right',
                                                               text_offset=(8, 80),
                                                               force_color=self.button_colors['stop'],
                                                               click_func=self.kill_server,
                                                               text_hover_color=(0.85, 0.7, 1, 1))
            self.controls.stop_button.opacity = 0
            self.controls.add_widget(self.controls.stop_button)

            # Restart server button
            self.controls.remove_widget(self.controls.restart_button)
            del self.controls.restart_button
            self.controls.restart_button = RelativeIconButton('restart server', {}, (20, 20), (None, None),
                                                              'restart-server.png', clickable=True, anchor='right',
                                                              text_offset=(-30, 80),
                                                              force_color=self.button_colors['stop'],
                                                              click_func=self.restart_server,
                                                              text_hover_color=(0.85, 0.7, 1, 1))
            self.controls.restart_button.opacity = 0
            self.controls.add_widget(self.controls.restart_button)

            # Filter button
            self.controls.remove_widget(self.controls.filter_button)
            del self.controls.filter_button
            self.controls.filter_button = RelativeIconButton('filter', {}, (20, 20), (None, None), 'filter-sharp.png',
                                                             clickable=True, anchor='right', text_offset=(3, 80),
                                                             force_color=self.button_colors['filter'],
                                                             click_func=self.filter_menu.show,
                                                             text_hover_color=(0.722, 0.722, 1, 1))
            self.controls.filter_button.opacity = 0
            self.controls.add_widget(self.controls.filter_button)

            if not self.run_data:
                utility.hide_widget(self.controls.maximize_button, True)
                utility.hide_widget(self.controls.stop_button, True)
                utility.hide_widget(self.controls.restart_button, True)
                utility.hide_widget(self.controls.filter_button, True)

            def after_anim(*a):
                self.full_screen = False
                self.ignore_keypress = False
                if self.run_data:
                    self.update_size()
                    Animation(opacity=1, duration=anim_speed, transition='out_sine').start(
                        self.controls.maximize_button)
                    Animation(opacity=1, duration=anim_speed, transition='out_sine').start(self.controls.stop_button)
                    Animation(opacity=1, duration=anim_speed, transition='out_sine').start(self.controls.restart_button)
                    Animation(opacity=1, duration=anim_speed, transition='out_sine').start(self.controls.filter_button)
                fix_scroll()

            Clock.schedule_once(after_anim, (anim_speed * 1.1))

    # Toggles deadlock button visibility
    def toggle_deadlock(self, boolean=True):
        def main_thread(*a):
            self.deadlocked = boolean
            if boolean:
                self.controls.stop_button.change_data('kill-server.png', 'kill server', self.kill_server)
            else:
                self.controls.stop_button.change_data('stop-server.png', 'stop server', self.stop_server)

        Clock.schedule_once(main_thread, 0)

    # Opens crash log in auto-mcs logviewer
    def open_log(self, *args):
        server_obj = constants.server_manager.current_server
        title = None

        if server_obj._telepath_data:
            title = f'{server_obj._view_name}'

        view_file(server_obj.crash_log, title)
        self.controls.log_button.button.on_leave()
        self.controls.log_button.button.on_release()

    # Adds show/hide log button
    def add_log_button(self, *args):
        self.log_view = False
        self.input.hint_text = "enter command..."

        # Choose path based on server name
        server_obj = constants.server_manager.current_server
        if server_obj._telepath_data:
            log_name = f"{server_obj._telepath_data['display-name']}, {server_obj.name}-latest.log"
        else:
            log_name = f"{server_obj.name}-latest.log"

        # Before deleting run data, save log to a file
        constants.folder_check(paths.temp)
        file_path = os.path.join(paths.temp, log_name)
        if os.path.isfile(file_path):
            self.deselect_all()
            self.scroll_layout.data = []

            def change_later(*a):
                try:
                    with open(file_path, 'r') as f:
                        self._unfiltered_text = json.loads(f.read())
                        self.update_text(self._unfiltered_text)
                except Exception as e:
                    send_log(self.__class__.__name__, f"error loading 'latest.log': {constants.format_traceback(e)}",
                             'error')

            Clock.schedule_once(change_later, 0)

            self.controls.remove_widget(self.controls.view_button)
            del self.controls.view_button
            self.controls.view_button = RelativeIconButton('view log', {}, (20, 20), (None, None), 'view-log.png',
                                                           clickable=True, anchor='right', text_offset=(18, 80),
                                                           force_color=self.button_colors['maximize'],
                                                           click_func=self.show_log)
            self.controls.add_widget(self.controls.view_button)
            self.controls.view_button.opacity = 0
            Animation(opacity=1, duration=0.15).start(self.controls.view_button)
            self.update_size()

    # Shows previous console log in panel
    def show_log(self, *args):

        if self.run_data:
            return

        self.log_view = True

        self.controls.control_shadow.opacity = 0
        self.input.hint_text = "viewing last run..."
        self.controls.control_shadow.size_hint_max = (135, 120)
        self.selected_labels = []
        anim_speed = 0.15
        self.scroll_layout.scroll_y = 0
        self.auto_scroll = False

        Animation(opacity=0, duration=anim_speed).start(self.controls.view_button)
        Animation(opacity=0, duration=anim_speed).start(self.controls.crash_text)
        Animation(opacity=0, duration=anim_speed).start(self.controls.button_shadow)
        Animation(opacity=0, duration=anim_speed).start(self.controls.background)
        Animation(opacity=0, duration=anim_speed).start(self.controls.background_ext)
        Animation(opacity=0, duration=(anim_speed * 1.5)).start(self.controls.launch_button)
        Animation(opacity=0, duration=(anim_speed * 1.5)).start(self.controls.log_button)

        def after_anim(*a):
            self.controls.maximize_button.disabled = False
            self.controls.remove_widget(self.controls.launch_button)
            self.controls.remove_widget(self.controls.log_button)
            self.controls.launch_button.button.on_leave()
            self.controls.log_button.button.on_leave()
            Animation(opacity=1, duration=anim_speed).start(self.controls.control_shadow)

        Clock.schedule_once(after_anim, (anim_speed * 1.51))
        Clock.schedule_once(functools.partial(self.maximize, True), 0.2)

    # Hides previous console log in panel
    def hide_log(self, *args):

        self.selected_labels = []

        def after_anim(*a):
            anim_speed = 0.15

            # Update crash widgets
            if self.controls.crash_text.text.text.strip():
                self.controls.log_button.disabled = False
                self.controls.log_button.opacity = 0
                self.controls.add_widget(self.controls.log_button)
                Animation(opacity=1, duration=anim_speed).start(self.controls.log_button)
                Animation(opacity=1, duration=anim_speed).start(self.controls.crash_text)

            # Animate panel
            self.controls.launch_button.disabled = False
            self.input.disabled = True
            self.input.text = ''

            self.controls.launch_button.opacity = 0
            self.controls.add_widget(self.controls.launch_button)

            Animation(opacity=1, duration=anim_speed).start(self.controls.button_shadow)
            Animation(opacity=1, duration=anim_speed).start(self.controls.launch_button)
            Animation(opacity=1, duration=anim_speed).start(self.controls.background)
            Animation(opacity=1, duration=anim_speed).start(self.controls.background_ext)

            Clock.schedule_once(functools.partial(self.maximize, False), 0)

            if self.controls.view_button.opacity > 0:
                utility.hide_widget(self.controls.view_button, True)

            def after_anim2(*a):
                self.controls.view_button.disabled = False
                self.scroll_layout.data = []

                # View log button
                self.controls.control_shadow.size_hint_max = (255, 120)
                Clock.schedule_once(self.update_size, -1)
                self.add_log_button()

            Clock.schedule_once(after_anim2, (anim_speed * 1.51))

        Clock.schedule_once(after_anim, 0)

    # Select all ConsoleLabels
    def select_all(self):
        self.selected_labels = [x['text'] for x in self.scroll_layout.data]
        for label in self.console_text.children:
            Animation.stop_all(label.sel_cover)
            label.sel_cover.opacity = 0.2
        Clock.schedule_once(self.scroll_layout.refresh_from_layout, 0)

    # Deselect all selected ConsoleLabels
    def deselect_all(self):
        self.selected_labels = []
        for label in self.console_text.children:
            Animation.stop_all(label.sel_cover)
            Animation(opacity=0, duration=0.05).start(label.sel_cover)
        Clock.schedule_once(self.scroll_layout.refresh_from_layout, 0.1)

    # Format and copy all selected text to clipboard
    def copy_selection(self):
        if self.selected_labels:
            text = '\n'.join(
                [str(x[0].rjust(11) + ('[' + x[1] + ']').rjust(9) + ' >   ' + x[2]) for x in self.selected_labels])

            # Remove formatting from text
            if '[/color]' in text:
                text = re.sub(r'\[\/?color(=#\w+)?\]', '', text)
            if '§' in text:
                for code in constants.color_table.keys():
                    text = text.replace(code, '')
            Clipboard.copy(text)
            self.selected_labels = []

        # Animate to convey copying
        for label in self.console_text.children:
            if label.sel_cover.opacity > 0:
                Animation.stop_all(label.sel_cover)
                label.sel_cover.opacity = 0.4
                Animation(opacity=0, duration=0.2).start(label.sel_cover)
        Clock.schedule_once(self.scroll_layout.refresh_from_layout, 0.41)

    # Check for drag select
    def on_touch_down(self, touch):
        if touch.device == "wm_touch":
            touch.button = "left"

        # Copy when right-clicked
        if self.selected_labels and touch.button == "right":
            self.copy_selection()
            return True

        # Select code for a single ConsoleLabel is under "SelectCover.on_touch_down()"
        try:
            if touch.button == "left":
                self.last_self_touch = self.console_text.to_widget(*touch.pos)

        # Ignore invalid inputs from non-standard input devices
        except AttributeError:
            pass

        return super().on_touch_down(touch)

    # Check for drag select
    def on_touch_up(self, touch):
        self.last_self_touch = None
        return super().on_touch_up(touch)

    # Automatically scroll console_text when mouse is dragged on the top or bottom regions
    def scroll_region(self, top=True, last_touch=None):
        if not self.in_scroll_region:
            self.in_scroll_region = True
            scroll_padding = 50
            try:
                scroll_speed = (self.scroll_layout.height / len(self.scroll_layout.data)) / 1800
            except ZeroDivisionError:
                scroll_speed = 100
            last_touch.pos = self.to_widget(*Window.mouse_pos)

            if top:
                while (Window.mouse_pos[1] >= self.scroll_layout.y + (
                        self.scroll_layout.height - scroll_padding)) and self.last_self_touch:
                    def scroll_up(*a):
                        self.scroll_layout.scroll_y += scroll_speed

                    if self.scroll_layout.scroll_y < 1:
                        Clock.schedule_once(scroll_up, 0)
                        Clock.schedule_once(functools.partial(self.on_touch_move, last_touch), 0)
                    else:
                        self.scroll_layout.scroll_y = 1
                        break
                    time.sleep(0.01)

            else:
                while (self.scroll_layout.y + (scroll_padding * 2) >= Window.mouse_pos[
                    1] >= self.scroll_layout.y) and self.last_self_touch:
                    def scroll_down(*a):
                        self.scroll_layout.scroll_y -= scroll_speed

                    if self.scroll_layout.scroll_y > 0:
                        Clock.schedule_once(scroll_down, 0)
                        Clock.schedule_once(functools.partial(self.on_touch_move, last_touch), 0)
                    else:
                        self.scroll_layout.scroll_y = 0
                        break
                    time.sleep(0.01)

            self.in_scroll_region = False

    def on_touch_move(self, touch, *a):

        # Move the scrollbar when near the top or bottom to select more than the viewport
        scroll_padding = 50
        if (touch.dsy > 0) and (touch.pos[1] >= self.scroll_layout.y + (self.scroll_layout.height - scroll_padding)):
            dTimer(0, functools.partial(self.scroll_region, True, touch)).start()

        if (touch.dsy < 0) and (self.scroll_layout.y + (scroll_padding * 2) >= touch.pos[1] >= self.scroll_layout.y):
            dTimer(0, functools.partial(self.scroll_region, False, touch)).start()

        def is_between(y3):
            y1 = self.console_text.height - self.last_self_touch[1]
            y2 = self.console_text.height - self.console_text.to_widget(*touch.pos)[1]
            y3 = self.console_text.height - self.console_text.to_widget(*self.scroll_layout.to_parent(0, y3))[1] - 25
            return ((y1 <= y3 <= y2) or (y2 <= y3 <= y1)) and not (
                        touch.pos[0] > self.scroll_layout.x + (self.scroll_layout.width - self.scroll_layout.drag_pad))

        for widget in self.console_text.children:
            try:
                if is_between(widget.y) and widget.original_text not in self.selected_labels:

                    # Use Y delta to orient clipboard content
                    if touch.dsy > 0:
                        self.selected_labels.insert(0, widget.original_text)
                    else:
                        self.selected_labels.append(widget.original_text)
                    widget.sel_cover.opacity = 0.2

                elif (not is_between(widget.y)) and widget.original_text in self.selected_labels:
                    self.selected_labels.remove(widget.original_text)
                    widget.sel_cover.opacity = 0
            except:
                pass
        return super().on_touch_move(touch)

    def __init__(self, server_name, server_button=None, start_launched=False,
                 performance_panel: PerformancePanel = None, **kwargs):
        super().__init__(**kwargs)

        self.performance_panel = performance_panel

        self.server_name = server_name
        self.server_obj = None
        self.run_data = None
        self.server_button = server_button
        self.deadlocked = False
        self.log_view = False
        self.full_screen = False
        self.full_screen_offset = 95
        self.size_offset = (70, 550)
        self.ignore_keypress = False
        self.pos_hint = {"center_x": 0.5}
        self.default_y = 170
        self.y = self.default_y

        # Selection info
        self.selected_labels = []
        self.last_touch = None
        self.last_self_touch = None
        self.in_scroll_region = False

        self._unfiltered_text = []

        self.button_colors = {
            'maximize': [[(0.05, 0.08, 0.07, 1), (0.722, 0.722, 1, 1)], ''],
            'filter': [[(0.05, 0.08, 0.07, 1), (0.251, 0.251, 0.451, 1)], ''],
            'stop': [[(0.05, 0.08, 0.07, 1), (0.722, 0.722, 1, 1)], 'pink']
        }

        # Apply accent color if it's different
        screen_accent = utility.screen_manager.current_screen.accent_color

        # Stop clicks through the background
        class StopClick(FloatLayout):
            def on_touch_down(self, touch):
                if self.collide_point(*touch.pos):
                    return True
                else:
                    super().on_touch_down(touch)

        self.stop_click = StopClick()
        self.add_widget(self.stop_click)

        # Console line Viewclass for RecycleView
        class ConsoleLabel(RelativeLayout):

            def __setattr__(self, attr, value):
                # Change attributes dynamically based on rule
                if attr == "text" and value:
                    self.original_text = value
                    self.change_properties(value)

                super().__setattr__(attr, value)

            # Modifies rule attributes based on text content
            def change_properties(self, text):

                if not self.console_panel and constants.server_manager.current_server.run_data:
                    try:
                        self.console_panel = constants.server_manager.current_server.run_data['console-panel']
                    except KeyError:
                        pass

                if text and utility.screen_manager.current_screen.name == 'ServerViewScreen':

                    if not self.console_panel and not constants.server_manager.current_server.run_data:
                        try:
                            self.console_panel = utility.screen_manager.current_screen.console_panel
                        except:
                            pass

                    self.date_label.text = text[0]
                    self.type_label.text = text[1]
                    self.main_label.text = text[2]
                    type_color = text[3]

                    # Log text section formatting
                    width = utility.screen_manager.current_screen.console_panel.console_text.width
                    self.width = width
                    self.main_label.width = width - (self.section_size * 2) - 3
                    self.main_label.text_size = (width - (self.section_size * 2) - 3, None)
                    try:
                        self.main_label.texture_update()
                    except:
                        self.date_label.text = kivy.utils.escape_markup(text[0])
                        self.type_label.text = kivy.utils.escape_markup(text[1])
                        self.main_label.text = kivy.utils.escape_markup(text[2])
                        self.main_label.texture_update()
                    self.main_label.size = self.main_label.texture_size
                    self.main_label.size_hint_max_x = width - (self.section_size * 2) - 3
                    self.size_hint_max_x = width

                    # This is an extremely dirty and stinky fix for setting position and height
                    self.main_label.x = (width / 2) - 50 + (self.section_size) - 3

                    # def update_grid(*args):
                    #     self.main_label.texture_update()
                    #     self.size[1] = self.main_label.texture_size[1] + self.line_spacing
                    #
                    # Clock.schedule_once(update_grid, 0)

                    # Type & date label stuffies
                    self.date_label.x = 8
                    self.type_label.x = self.date_label.x + self.section_size - 6
                    self.type_banner.x = self.type_label.x - 7

                    if type_color:
                        self.main_label.color = type_color
                        self.date_label.color = self.type_label.color = constants.brighten_color(type_color, -0.65)
                        self.date_banner1.color = self.date_banner2.color = constants.brighten_color(type_color, -0.2)
                        self.type_banner.color = type_color

                        # Format selection color
                        if self.console_panel:
                            self.sel_cover.opacity = 0.2 if text in self.console_panel.selected_labels else 0
                        self.sel_cover.color = constants.brighten_color(type_color, 0.05)
                        self.sel_cover.width = self.width

            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.original_text = None
                self.console_panel = None
                self.line_spacing = 20
                self.font_size = sp(17)
                self.section_size = 110

                # Main text
                self.main_label = Label()
                self.main_label.__translate__ = False
                self.main_label.markup = True
                self.main_label.shorten = True
                self.main_label.shorten_from = 'right'
                self.main_label.font_size = sp(20)
                self.main_label.font_name = os.path.join(paths.ui_assets, 'fonts',
                                                         f'{constants.fonts["mono-bold"]}.otf')
                self.main_label.halign = 'left'
                self.add_widget(self.main_label)

                # Type label/banner
                self.type_banner = Image()
                self.type_banner.source = os.path.join(paths.ui_assets, 'console_banner.png')
                self.type_banner.allow_stretch = True
                self.type_banner.keep_ratio = False
                self.add_widget(self.type_banner)

                self.type_label = Label()
                self.type_label.__translate__ = False
                self.type_label.font_size = self.font_size
                self.type_label.font_name = os.path.join(paths.ui_assets, 'fonts',
                                                         f'{constants.fonts["mono-bold"]}.otf')
                self.add_widget(self.type_label)

                # Date label/banner
                self.date_banner1 = Image()
                self.date_banner1.source = os.path.join(paths.ui_assets, 'console_banner.png')
                self.date_banner1.allow_stretch = True
                self.date_banner1.keep_ratio = False
                self.add_widget(self.date_banner1)
                self.date_banner2 = Image()
                self.date_banner2.source = os.path.join(paths.ui_assets, 'console_banner.png')
                self.date_banner2.allow_stretch = True
                self.date_banner2.keep_ratio = False
                self.date_banner2.x = 27
                self.add_widget(self.date_banner2)

                self.date_label = Label()
                self.date_label.__translate__ = False
                self.date_label.font_size = self.font_size
                self.date_label.font_name = os.path.join(paths.ui_assets, 'fonts',
                                                         f'{constants.fonts["mono-medium"]}.otf')
                self.date_label.halign = 'left'
                self.add_widget(self.date_label)

                # Select cover for text selection
                class SelectCover(Image):

                    def on_touch_down(self, touch):
                        if self.collide_point(*touch.pos) and touch.button == 'left':
                            if self.parent:
                                for widget in self.parent.parent.children:
                                    widget.sel_cover.opacity = 0
                                try:
                                    if (self.parent.original_text in self.parent.console_panel.selected_labels) and (
                                            len(self.parent.console_panel.selected_labels) == 1):
                                        self.parent.console_panel.deselect_all()
                                    else:
                                        self.parent.console_panel.last_touch = touch.pos
                                        self.parent.console_panel.selected_labels = [self.parent.original_text]
                                        self.opacity = 0.2
                                        Clock.schedule_once(self.parent.console_panel.scroll_layout.refresh_from_layout,
                                                            0)
                                except:
                                    pass
                        else:
                            self.opacity = 0
                            return super().on_touch_down(touch)

                self.sel_cover = SelectCover()
                self.sel_cover.opacity = 0
                self.sel_cover.allow_stretch = True
                self.sel_cover.size_hint = (None, None)
                self.sel_cover.height = 42
                self.add_widget(self.sel_cover)

                # Cover for fade animation
                self.anim_cover = Image()
                self.anim_cover.opacity = 0
                self.anim_cover.allow_stretch = True
                self.anim_cover.size_hint = (None, None)
                self.anim_cover.width = self.section_size * 1.9
                self.anim_cover.height = self.section_size / 2.65
                self.anim_cover.color = background_color
                self.add_widget(self.anim_cover)

        # Command input at the bottom
        class ConsoleInput(TextInput):

            def _on_focus(self, instance, value, *largs):

                # Log for crash info
                if value:
                    try:
                        interaction = f"ConsoleInput (Sub-server {list(constants.server_manager.running_servers.keys()).index(self.parent.server_name) + 1})"
                        constants.last_widget = interaction + f" @ {constants.format_now()}"
                        send_log('navigation', f"interaction: '{interaction}'")
                    except:
                        pass

                # Update screen focus value on next frame
                def update_focus(*args):
                    utility.screen_manager.current_screen._input_focused = self.focus

                Clock.schedule_once(update_focus, 0)

                super(ConsoleInput, self)._on_focus(instance, value)
                Animation.stop_all(self.parent.input_background)
                Animation(opacity=0.9 if self.focus else 0.35, duration=0.2, step=0).start(self.parent.input_background)

            def __init__(self, **kwargs):
                super().__init__(**kwargs)

                self.original_text = ''
                self.history_index = 0

                self.multiline = False
                self.halign = "left"
                self.hint_text = "enter command..."

                self.hint_text_color = (0.6, 0.6, 1, 0.4)
                self.foreground_color = (0.6, 0.6, 1, 1)
                self.background_color = (0, 0, 0, 0)
                self.disabled_foreground_color = (0.6, 0.6, 1, 0.4)
                self.cursor_color = (0.55, 0.55, 1, 1)
                self.selection_color = (0.5, 0.5, 1, 0.4)

                self.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["mono-bold"]}.otf')
                self.font_size = sp(22)
                self.padding_y = (12, 12)
                self.padding_x = (70, 12)
                self.cursor_width = dp(3)

                self.bind(on_text_validate=self.on_enter)

            def tab_player(self, *a):
                player_list = [k for k, v in self.parent.server_obj.get_players().items() if v['logged-in']]

                if self.text.strip():
                    key = self.text.split(" ")[-1].lower()
                    if key not in player_list:
                        for player in player_list:
                            if self.text.endswith(" "):
                                self.text = self.text.strip() + " " + player
                                break

                            elif player.lower().startswith(key):
                                self.text = self.text[:-len(key)] + player
                                break

            def grab_focus(self, *a):
                def focus_later(*args):
                    self.focus = True

                Clock.schedule_once(focus_later, 0)

            def on_enter(self, value):

                # Move this to a proper send_command() function in svrmgr
                if self.parent.run_data:
                    self.parent.run_data['send-command'](self.text)
                    self.parent.update_text(self.parent.run_data['log'], force_scroll=True)

                self.original_text = ''
                self.history_index = 0

                self.text = ''
                self.grab_focus()

            # Input validation
            def insert_text(self, substring, from_undo=False):
                if utility.screen_manager.current_screen.popup_widget:
                    return None

                if not self.text and substring in [' ', '/']:
                    substring = ""

                if substring == "\t":
                    substring = ""

                else:
                    s = substring.replace("§", "[_color_]").encode("ascii", "ignore").decode().replace("\n",
                                                                                                       "").replace("\r",
                                                                                                                   "").replace(
                        "[_color_]", "§")
                    self.original_text = self.text + s
                    self.history_index = 0
                    return super().insert_text(s, from_undo=from_undo)

            # Manipulate command history
            def keyboard_on_key_down(self, window, keycode, text, modifiers):

                if self.parent.run_data:

                    if keycode[1] == "backspace" and control in modifiers:
                        original_index = self.cursor_col
                        new_text, index = constants.control_backspace(self.text, original_index)
                        self.select_text(original_index - index, original_index)
                        self.delete_selection()
                    else:
                        super().keyboard_on_key_down(window, keycode, text, modifiers)

                    if keycode[1] == "tab":
                        self.tab_player()

                    if keycode[1] == 'up' and self.parent.run_data['command-history']:
                        if self.text != self.original_text:
                            self.history_index += 1
                        if self.history_index > len(self.parent.run_data['command-history']) - 1:
                            self.history_index = len(self.parent.run_data['command-history']) - 1
                            if self.history_index < 0:
                                self.history_index = 0
                        self.text = self.parent.run_data['command-history'][self.history_index]


                    elif keycode[1] == 'down' and self.parent.run_data['command-history']:
                        self.history_index -= 1
                        if self.history_index < 0:
                            self.history_index = 0
                            self.text = self.original_text
                        else:
                            self.text = self.parent.run_data['command-history'][self.history_index]

        # Controls and background for console panel
        class ConsoleControls(RelativeLayout):
            def __init__(self, panel, **kwargs):
                super().__init__(**kwargs)
                self.panel = panel

                # Blurred background image
                self.background = Image()
                self.background.allow_stretch = True
                self.background.keep_ratio = False
                self.background.source = os.path.join(paths.ui_assets, f'console_preview_{randrange(3)}.png')
                self.background_ext = Image(size_hint_max=(None, None))
                self.add_widget(self.background_ext)
                self.add_widget(self.background)

                # Button shadow
                self.button_shadow = Image(pos_hint={'center_x': 0.5, 'center_y': 0.5})
                self.button_shadow.allow_stretch = True
                self.button_shadow.keep_ratio = False
                self.button_shadow.size_hint_max = (580, 250)
                self.button_shadow.source = os.path.join(paths.ui_assets, 'banner_shadow.png')
                self.add_widget(self.button_shadow)

                # Launch button
                self.launch_button = color_button("LAUNCH", position=(0.5, 0.5), icon_name='launch-server.png',
                                                  click_func=self.panel.launch_server,
                                                  hover_data={'color': (0.05, 0.05, 0.1, 1),
                                                              'image': os.path.join(paths.ui_assets,
                                                                                    'launch-button-hover.png')})
                self.launch_button.disabled = False
                self.add_widget(self.launch_button)

                # Open log button
                self.log_button = color_button("VIEW CRASH LOG", position=(0.5, 0.22),
                                               icon_name='document-text-outline-sharp.png',
                                               click_func=self.panel.open_log, color=(1, 0.65, 0.75, 1))
                self.log_button.disabled = False
                if constants.server_manager.current_server.crash_log:
                    self.add_widget(self.log_button)

                # Crash text
                self.crash_text = InputLabel(pos_hint={'center_y': 0.78})
                self.crash_text.text.text = ''
                self.add_widget(self.crash_text)
                if constants.server_manager.current_server.crash_log:
                    self.crash_text.update_text(f"Uh oh, '${self.panel.server_name}$' has crashed", False)

                # Button shadow in the top right
                self.control_shadow = Image()
                self.control_shadow.allow_stretch = True
                self.control_shadow.keep_ratio = False
                self.control_shadow.color = background_color
                self.control_shadow.source = os.path.join(paths.ui_assets, 'console_control_shadow.png')
                self.control_shadow.size_hint_max = (280, 120)
                self.add_widget(self.control_shadow)

                # Full screen button
                self.maximize_button = RelativeIconButton('maximize', {}, (20, 20), (None, None), 'maximize.png',
                                                          clickable=True, anchor='right', text_offset=(24, 80),
                                                          force_color=self.panel.button_colors['maximize'],
                                                          click_func=functools.partial(self.panel.maximize, True))
                utility.hide_widget(self.maximize_button)
                self.add_widget(self.maximize_button)

                # Stop server button
                self.stop_button = RelativeIconButton('stop server', {}, (20, 20), (None, None), 'stop-server.png',
                                                      clickable=True, anchor='right', text_offset=(8, 80),
                                                      force_color=self.panel.button_colors['stop'],
                                                      click_func=self.panel.stop_server,
                                                      text_hover_color=(0.85, 0.7, 1, 1))
                utility.hide_widget(self.stop_button)
                self.add_widget(self.stop_button)

                # Restart server button
                self.restart_button = RelativeIconButton('restart server', {}, (20, 20), (None, None),
                                                         'restart-server.png', clickable=True, anchor='right',
                                                         text_offset=(-30, 80),
                                                         force_color=self.panel.button_colors['stop'],
                                                         click_func=self.panel.restart_server,
                                                         text_hover_color=(0.85, 0.7, 1, 1))
                utility.hide_widget(self.restart_button)
                self.add_widget(self.restart_button)

                # Filter button
                self.filter_button = RelativeIconButton('filter', {}, (20, 20), (None, None), 'filter-sharp.png',
                                                        clickable=True, anchor='right', text_offset=(3, 80),
                                                        force_color=self.panel.button_colors['filter'],
                                                        click_func=self.panel.filter_menu.show,
                                                        text_hover_color=(0.722, 0.722, 1, 1))
                utility.hide_widget(self.filter_button)
                self.add_widget(self.filter_button)

                # View log button
                self.view_button = RelativeIconButton('view log', {}, (20, 20), (None, None), 'view-log.png',
                                                      clickable=True, anchor='right', text_offset=(18, 80),
                                                      force_color=self.panel.button_colors['maximize'],
                                                      click_func=functools.partial(self.panel.show_log, True))
                Clock.schedule_once(self.panel.add_log_button, 0)

        # Scrollable list for configuring console event filtering
        class FilterMenu(ContextMenu):

            def __init__(self, panel, **kwargs):
                super().__init__(**kwargs)
                self.panel = panel
                self.change_filter(constants.server_manager.current_server.console_filter)

            def change_filter(self, filter_type):
                if not filter_type:
                    filter_type = 'everything'

                self.current_filter = filter_type
                constants.server_manager.current_server.change_filter(filter_type)
                filter_button = None

                if self.panel.run_data or self.panel.log_view:
                    self.panel.update_text(self.panel._unfiltered_text)
                    filter_button = self.panel.controls.filter_button

                # Change filter icon colors
                filter_color = [[(0.05, 0.08, 0.07, 1), (0.6, 0.6, 1, 1)], '']
                default_color = [[(0.05, 0.08, 0.07, 1), (0.251, 0.251, 0.451, 1)], '']

                if filter_type == 'everything':
                    self.panel.button_colors['filter'] = default_color
                    if filter_button:
                        filter_button.button.color_id = default_color[0]
                        filter_button.button.on_leave()
                else:
                    self.panel.button_colors['filter'] = filter_color
                    if filter_button:
                        filter_button.button.color_id = filter_color[0]
                        filter_button.button.on_leave()

            def _change_options(self, options_list):
                self.options_list = options_list
                self._grid.clear_widgets()

                for item in self.options_list:
                    if not item: continue

                    selected = self.current_filter in item['name']

                    # Start of the list
                    if item == self.options_list[0]:
                        start_btn = self.ListButton(item, sub_id='list_start_button', selected=selected,
                                                    _menu_width=self.menu_width, _row_height=self.row_height)
                        self._grid.add_widget(start_btn)

                    # Middle of the list
                    elif item != self.options_list[-1]:
                        mid_btn = self.ListButton(item, sub_id='list_mid_button', selected=selected,
                                                  _menu_width=self.menu_width, _row_height=self.row_height)
                        self._grid.add_widget(mid_btn)

                    # Last button
                    else:
                        if 'color' in item:
                            sub_id = f'list_{item["color"]}_button'
                        else:
                            sub_id = 'list_end_button'
                        end_btn = self.ListButton(item, sub_id=sub_id, selected=selected, _menu_width=self.menu_width,
                                                  _row_height=self.row_height)
                        self._grid.add_widget(end_btn)

                # After rebuilding, ensure container height matches content and width tracks constraint
                self.height = self._grid.minimum_height

            def _update_pos(self):

                # Set initial position
                pos = (self.panel.x + self.panel.width - 220, self.panel.controls.y + self.panel.controls.height - 58)
                self._grid.x = pos[0]
                self._grid.y = pos[1] - self._grid.height
                Clock.schedule_once(self._round_top_left, 0)

                # Adjust auto-hide hitbox size/pos
                self._update_hitbox()

            def show(self):
                button_hidden = False
                try:
                    button_hidden = self.panel.controls.filter_button.opacity == 0
                except:
                    pass

                if self.visible or button_hidden:
                    self._hitbox.size_hint_max = (0, 0)
                    return self.hide()

                filters = [
                    {'name': 'everything', 'icon': 'reader.png', 'action': lambda *_: self.change_filter('everything')},
                    {'name': 'only errors', 'icon': 'warning.png', 'action': lambda *_: self.change_filter('errors')},
                    {'name': 'only players', 'icon': 'person.png', 'action': lambda *_: self.change_filter('players')},
                    {'name': 'amscript', 'icon': 'amscript.png', 'action': lambda *_: self.change_filter('amscript')}
                ]
                super().show(widget=self.panel.controls.filter_button.button, options_list=filters)

            def hide(self, animate=True, *args):
                Clock.schedule_once(self.widget.on_leave, 0.05)
                if self.visible: self.play_sound()

                if animate:
                    Animation(opacity=0, size_hint_max_x=150, duration=0.13, transition='in_out_sine').start(self)
                    for b in self._grid.children:
                        b.animate(False)
                    Clock.schedule_once(functools.partial(self._deselect_buttons), 0.14)
                    Clock.schedule_once(lambda *_: self._grid.clear_widgets(), 0.141)
                else:
                    self._grid.clear_widgets()

            def on_touch_down(self, touch):
                if self.visible:
                    if touch.button != 'right':
                        self.hide()
                        Clock.schedule_once(lambda *_: setattr(self, 'visible', False), 0.3)
                return FloatLayout.on_touch_down(self, touch)

        # Event filter
        self.filter_menu = FilterMenu(self)

        # Popen object reference
        self.scale = 1
        self.auto_scroll = False

        background_color = constants.brighten_color(constants.background_color, -0.1)

        # Background
        with self.canvas.before:
            self.color = Color(*background_color, mode='rgba')
            self.rect = Rectangle(pos=self.pos, size=self.size)

        with self.canvas.after:
            self.canvas.clear()

        # Text Layout
        self.scroll_layout = RecycleViewWidget(position=None, view_class=ConsoleLabel)
        self.scroll_layout.always_overscroll = False
        self.scroll_layout.scroll_wheel_distance = dp(50)
        self.console_text = RecycleGridLayout(size_hint_y=None, cols=1, default_size=(100, 42), padding=[0, 3, 0, 30])
        self.console_text.bind(minimum_height=self.console_text.setter('height'))
        self.scroll_layout.add_widget(self.console_text)
        self.scroll_layout.scroll_type = ['bars']
        self.add_widget(self.scroll_layout)

        # Log gradient
        self.gradient = Image()
        self.gradient.allow_stretch = True
        self.gradient.keep_ratio = False
        self.gradient.size_hint = (None, None)
        self.gradient.color = background_color
        self.gradient.opacity = 0.65
        self.gradient.source = os.path.join(paths.ui_assets, 'scroll_gradient.png')
        self.add_widget(self.gradient)

        # Command input
        self.input = ConsoleInput(size_hint_max_y=50)
        self.input.disabled = True
        self.add_widget(self.input)

        # Input icon
        self.input_background = Image()
        self.input_background.default_opacity = 0.35
        self.input_background.color = self.input.foreground_color
        self.input_background.opacity = self.input_background.default_opacity
        self.input_background.allow_stretch = True
        self.input_background.size_hint = (None, None)
        self.input_background.height = self.input.size_hint_max_y / 1.45
        self.input_background.source = os.path.join(paths.ui_assets, 'console_input_banner.png')
        self.add_widget(self.input_background)

        # Fullscreen shadow
        self.fullscreen_shadow = Image()
        self.fullscreen_shadow.allow_stretch = True
        self.fullscreen_shadow.keep_ratio = False
        self.fullscreen_shadow.size_hint_max = (None, 25)
        self.fullscreen_shadow.color = background_color
        self.fullscreen_shadow.opacity = 0
        self.fullscreen_shadow.source = os.path.join(paths.ui_assets, 'control_fullscreen_gradient.png')
        self.add_widget(self.fullscreen_shadow)

        # Start server/blurred background layout
        self.controls = ConsoleControls(self)
        self.add_widget(self.controls)
        self.controls.background_ext.color = background_color

        # Rounded corner mask
        self.corner_size = 30

        class Corner(Image):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.source = os.path.join(paths.ui_assets, 'console_border.png')
                self.color = screen_accent or constants.background_color
                self.allow_stretch = True
                self.keep_ratio = False

        class Side(Image):
            def __init__(self, vertical=True, **kwargs):
                super().__init__(**kwargs)
                self.source = os.path.join(paths.ui_assets,
                                           f'control_gradient_{"vertical" if vertical else "horizontal"}.png')
                self.allow_stretch = True
                self.keep_ratio = False

        self.corner_mask = RelativeLayout()
        self.corner_mask.tl = Corner(pos_hint={'center_x': 0, 'center_y': 1},
                                     size_hint_max=(self.corner_size, self.corner_size))
        self.corner_mask.tr = Corner(pos_hint={'center_x': 1, 'center_y': 1},
                                     size_hint_max=(-self.corner_size, self.corner_size))
        self.corner_mask.bl = Corner(pos_hint={'center_x': 0, 'center_y': 0},
                                     size_hint_max=(self.corner_size, -self.corner_size))
        self.corner_mask.br = Corner(pos_hint={'center_x': 1, 'center_y': 0},
                                     size_hint_max=(-self.corner_size, -self.corner_size))
        self.corner_mask.add_widget(self.corner_mask.tl)
        self.corner_mask.add_widget(self.corner_mask.tr)
        self.corner_mask.add_widget(self.corner_mask.bl)
        self.corner_mask.add_widget(self.corner_mask.br)

        self.corner_mask.sl = Side(pos_hint={'center_x': 0, 'center_y': 0.5}, size_hint_max=(self.corner_size, None),
                                   vertical=False)
        self.corner_mask.sr = Side(pos_hint={'center_x': 1, 'center_y': 0.5}, size_hint_max=(-self.corner_size, None),
                                   vertical=False)
        self.corner_mask.st = Side(pos_hint={'center_x': 0.5, 'center_y': 1}, size_hint_max=(None, self.corner_size))
        self.corner_mask.sb = Side(pos_hint={'center_x': 0.5, 'center_y': 0}, size_hint_max=(None, -self.corner_size))
        self.corner_mask.add_widget(self.corner_mask.sl)
        self.corner_mask.add_widget(self.corner_mask.sr)
        self.corner_mask.add_widget(self.corner_mask.st)
        self.corner_mask.add_widget(self.corner_mask.sb)

        self.add_widget(self.corner_mask)

        self.add_widget(self.filter_menu)

        self.bind(pos=self.update_size)
        self.bind(size=self.update_size)
        Clock.schedule_once(self.update_size, 0)

        if start_launched:
            Clock.schedule_once(functools.partial(self.launch_server, False, False), 0)


class ServerViewScreen(MenuBackground):

    # Fit background color across screen for transitions
    def update_rect(self, *args):

        # Hide context menu when screen is resized
        if self.context_menu:
            self.context_menu.hide(False)

        self.rect.pos = self.pos
        self.rect.size = self.size

        # Resize popup if it exists
        if self.popup_widget:
            self.popup_widget.resize()

        # Repos page switcher
        if self.page_switcher:
            self.page_switcher.resize_self()

        # Repos console panel and widgets
        if self.console_panel:
            Clock.schedule_once(self.console_panel.update_size, 0)
        if self.performance_panel:
            Clock.schedule_once(self.performance_panel.update_rect, 0)
        save_window_pos()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'
        self.server = None
        self.performance_panel = None
        self.console_panel = None
        self.menu_taskbar = None
        self.server_button = None
        self.server_button_layout = None
        self.perf_timer = None

        self.accent_color = None
        if self.accent_color:
            with self.canvas.before:
                self.color = Color(*self.accent_color, mode='rgba')
                self.rect = Rectangle(pos=self.pos, size=self.size)

    def set_timer(self, start=True):
        if start:
            try:
                if 'launch-time' in self.server.run_data:
                    self.performance_panel.player_clock = 6
                    Clock.schedule_once(self.performance_panel.refresh_data, 0.5)
                    self.perf_timer = Clock.schedule_interval(self.performance_panel.refresh_data, 1)
            except AttributeError:
                pass
        else:
            if self.perf_timer:
                self.perf_timer.cancel()
            self.perf_timer = None

    def on_pre_leave(self, **kwargs):
        self.set_timer(False)
        super().on_pre_leave(**kwargs)

    def on_pre_enter(self, **kwargs):
        super().on_pre_enter(**kwargs)
        self.set_timer(True)

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
                            Clock.schedule_once(
                                functools.partial(self.popup_widget.window_input.do_cursor_movement, 'cursor_right',
                                                  True), 0)

                    new_str = self.popup_widget.window_input.keyboard.keycode_to_string(keycode[0])
                    if 'shift' in modifiers:
                        new_str = new_str.upper()
                    if len(new_str) == 1:
                        insert_text(new_str)
                    elif keycode[1] == 'spacebar':
                        insert_text(' ')
                    self.popup_widget.resize_window()
                else:
                    self.popup_widget.resize_window()
                return True

            if keycode[1] in ['escape', 'n']:
                try:
                    self.popup_widget.click_event(self.popup_widget, self.popup_widget.no_button)
                except AttributeError:
                    self.popup_widget.click_event(self.popup_widget, self.popup_widget.ok_button)

            elif keycode[1] in ['enter', 'return', 'y']:
                try:
                    self.popup_widget.click_event(self.popup_widget, self.popup_widget.yes_button)
                except AttributeError:
                    self.popup_widget.click_event(self.popup_widget, self.popup_widget.ok_button)
            return


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

        # Ignore ESC commands while input focused
        if not self._input_focused and self.name == utility.screen_manager.current_screen.name:

            # Keycode is composed of an integer + a string
            # If we hit escape, release the keyboard
            # On ESC, click on back button if it exists
            if keycode[1] == 'escape' and 'escape' not in self._ignore_keys:

                if self.context_menu:
                    self.context_menu.hide()

                elif self.console_panel.log_view:
                    self.console_panel.hide_log()

                elif self.console_panel.full_screen:
                    self.console_panel.maximize(False)

                else:
                    for button in self.walk():
                        try:
                            if button.id == "exit_button":
                                button.force_click()
                                break
                        except AttributeError:
                            continue
                keyboard.release()

            # Start server when enter is pressed
            if (keycode[1] == 'enter' and 'enter' not in self._ignore_keys) and not self.server.run_data:
                if not self.console_panel.log_view:
                    self.console_panel.controls.launch_button.button.on_enter()
                    Clock.schedule_once(self.console_panel.launch_server, 0.1)

            # Use 'F' to toggle fullscreen
            if keycode[1] == 'f' and 'f' not in self._ignore_keys and self.server.run_data:
                if not self.console_panel.log_view:
                    self.console_panel.maximize(not self.console_panel.full_screen)
                    self.console_panel.ignore_keypress = True

            # Focus text input if server is started
            if (keycode[1] == 'tab' and 'tab' not in self._ignore_keys) and self.server.run_data:
                self.console_panel.input.grab_focus()

        # Capture keypress on current screen no matter what
        if self.name == utility.screen_manager.current_screen.name:

            # Copy selected console text
            if ((keycode[1] == 'c' and control in modifiers) and ('c' not in self._ignore_keys)) and (
                    self.server.run_data or self.console_panel.log_view):
                self.console_panel.copy_selection()

            # Select all console text
            if ((keycode[1] == 'a' and control in modifiers) and ('a' not in self._ignore_keys)) and (
                    self.server.run_data or self.console_panel.log_view):
                self.console_panel.select_all()

            # Deselect all console text
            if ((keycode[1] == 'd' and control in modifiers) and ('d' not in self._ignore_keys)) and (
                    self.server.run_data or self.console_panel.log_view):
                self.console_panel.deselect_all()

            # Stop the server if it's currently running
            if ((keycode[1] == 'q' and control in modifiers) and (
                    'q' not in self._ignore_keys)) and self.server.run_data:
                stop_button = self.console_panel.controls.stop_button
                if stop_button.opacity == 1:
                    stop_button.button.trigger_action(0.1)

            # Quit on macOS
            elif constants.os_name == 'macos' and (keycode[1] == 'q' and control in modifiers):
                utility.app.attempt_to_close()

            # Restart the server if it's currently running
            if ((keycode[1] == 'r' and (control in modifiers and 'shift' in modifiers)) and (
                    'r' not in self._ignore_keys)) and self.server.run_data:
                restart_button = self.console_panel.controls.restart_button
                if restart_button.opacity == 1:
                    restart_button.button.trigger_action(0.1)

        # Return True to accept the key. Otherwise, it will be used by the system.
        return True

    def generate_menu(self, **kwargs):

        # If a new server is selected, animate the taskbar
        animate_taskbar = False
        try:
            if not self.server:
                animate_taskbar = True
            elif self.server.name != constants.server_manager.current_server.name:
                animate_taskbar = True
        except AttributeError:
            pass

        self.server = constants.server_manager.current_server

        # Generate buttons on page load
        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'

        # Check if updates are available
        update_banner = ""
        if self.server.auto_update == 'true':
            update_banner = self.server.update_string

        self.server_button = ServerButton(self.server, update_banner=update_banner, fade_in=0.3, view_only=True)
        grid_layout = GridLayout(cols=1, size_hint_max_x=None, padding=(0, 80, 0, 0))
        self.server_button_layout = ScrollItem()
        self.server_button_layout.add_widget(self.server_button)
        grid_layout.add_widget(self.server_button_layout)
        float_layout.add_widget(grid_layout)

        # Only add this off-screen for 'ESC' behavior
        buttons.append(ExitButton('Back', (0.5, -1), cycle=True))
        for button in buttons:
            float_layout.add_widget(button)

        float_layout.add_widget(generate_title(f"Server Manager: '{self.server.name}'"))
        float_layout.add_widget(generate_footer(f"{self.server.name}, Launch"))

        self.add_widget(float_layout)

        # Add ManuTaskbar
        self.menu_taskbar = MenuTaskbar(selected_item='launch', animate=animate_taskbar)
        self.add_widget(self.menu_taskbar)

        # Add performance panel
        perf_layout = ScrollItem()
        if self.server.run_data and 'performance-panel' in self.server.run_data and self.server.run_data[
            'performance-panel']:
            self.performance_panel = self.server.run_data['performance-panel']
            try:
                if self.performance_panel.parent:
                    self.performance_panel.parent.remove_widget(self.performance_panel)
            except AttributeError:
                pass
        else:
            self.performance_panel = PerformancePanel(self.server.name)
        perf_layout.add_widget(self.performance_panel)
        self.add_widget(perf_layout)

        # Add ConsolePanel
        if self.server.run_data and 'console-panel' in self.server.run_data and 'log' in self.server.run_data and \
                self.server.run_data['console-panel']:
            self.console_panel = self.server.run_data['console-panel']
            self.console_panel.scroll_layout.data = []
            Clock.schedule_once(
                functools.partial(self.console_panel.update_text, self.server.run_data['log'], True, False), 0)
        else:
            self.console_panel = ConsolePanel(self.server.name, self.server_button, start_launched=self.server.running,
                                              performance_panel=self.performance_panel)

        self.add_widget(self.console_panel)
        self.console_panel.server_obj = self.server


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
                if self.download_button:
                    self.download_button.disable(True)
                continue

            if k == 'migrate' and server_obj._telepath_data:
                continue

            if k == button_name:
                v.loading(True) if loading else v.loading(False)
            else:
                v.disable(True) if loading else v.disable(False)

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

            Clock.schedule_once(update_grid, 0)

        self.resize_bind = lambda *_: Clock.schedule_once(
            functools.partial(resize_scroll, scroll_widget, scroll_layout, scroll_anchor), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        scroll_layout.bind(minimum_height=scroll_layout.setter('height'))
        scroll_layout.id = 'scroll_content'

        # Scroll gradient
        scroll_top = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.8}, pos=scroll_widget.pos,
                                       size=(scroll_widget.width // 1.5, 60))
        scroll_bottom = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.17}, pos=scroll_widget.pos,
                                          size=(scroll_widget.width // 1.5, -60))

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
                    header_content = f"{translate('Latest Back-up')}  [color=#494977]-[/color]  " + (
                        f'[color=#6A6ABA]{translate("Never")}[/color]' if not backup_stats[
                            'latest-backup'] else f'[font={very_bold_font}]{backup_stats["latest-backup"]}[/font]')
                    sub_header_content = f"{backup_count:,}  back-up" + ("" if backup_count == 1 else "s") + (
                        f"   ({backup_stats['total-size']})" if backup_count > 0 else "")
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
        self.restore_backup_button = WaitButton('Restore From Back-up', (0.5, 0.5), 'reload-sharp.png',
                                                disabled=server_obj.running)
        sub_layout.add_widget(self.restore_backup_button)
        scroll_layout.add_widget(sub_layout)

        # Auto-backup toggle
        start_value = False if str(backup_stats['auto-backup']) == 'prompt' else str(
            backup_stats['auto-backup']) == 'true'

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
        sub_layout.add_widget(blank_input(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="automatic back-ups"))
        sub_layout.add_widget(
            toggle_button('auto-backup', (0.5, 0.5), default_state=start_value, custom_func=toggle_auto))
        scroll_layout.add_widget(sub_layout)

        # Maximum back-up slider
        max_limit = 11
        start_value = max_limit if str(backup_stats['max-backup']) == 'unlimited' else int(backup_stats['max-backup'])

        def change_limit(val):
            server_obj.backup.set_amount('unlimited' if val == max_limit else val)

        sub_layout = ScrollItem()
        sub_layout.add_widget(blank_input(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="maximum back-ups"))
        sub_layout.add_widget(NumberSlider(start_value, (0.5, 0.5), input_name='BackupMaxInput', limits=(2, max_limit),
                                           max_icon='infinite-bold.png', function=change_limit))
        scroll_layout.add_widget(sub_layout)

        if server_obj._telepath_data:

            # Download a back-up
            def download_backup(*args):
                Clock.schedule_once(self.download_button.button.on_leave, 0.5)

            sub_layout = ScrollItem()
            self.download_button = WaitButton('Download a Back-up', (0.5, 0.5), 'cloud-download-sharp.png',
                                              click_func=download_backup)
            sub_layout.add_widget(self.download_button)
            scroll_layout.add_widget(sub_layout)


        # Only apply these buttons on a local server
        else:
            # Open back-up directory
            def open_backup_dir(*args):
                backup_stats = server_obj.backup._backup_stats
                constants.open_folder(backup_stats['backup-path'])
                Clock.schedule_once(self.open_path_button.button.on_leave, 0.5)

            self.open_path_button = IconButton('open directory', {}, (70, 110), (None, None), 'folder.png',
                                               anchor='right', click_func=open_backup_dir, text_offset=(10, 0))
            float_layout.add_widget(self.open_path_button)

            # Migrate back-up directory
            def change_backup_dir(*args):
                backup_stats = server_obj.backup._backup_stats
                current_path = backup_stats['backup-path']
                new_path = file_popup("dir",
                                      start_dir=(current_path if os.path.exists(current_path) else paths.backups),
                                      input_name='migrate_backup_button', select_multiple=False,
                                      title="Select a New Back-up Directory")
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
                if new_path:
                    dTimer(0, run_migrate).start()

            sub_layout = ScrollItem()
            self.migrate_path_button = WaitButton('Migrate Back-up Directory', (0.5, 0.5), 'migrate.png',
                                                  click_func=change_backup_dir)
            sub_layout.add_widget(self.migrate_path_button)
            scroll_layout.add_widget(sub_layout)

        # Clone server button
        def clone_server(*args):
            utility.screen_manager.current = 'ServerCloneScreen'

        sub_layout = ScrollItem()
        self.clone_button = WaitButton('Clone this server', (0.5, 0.5), 'duplicate-outline.png',
                                       click_func=clone_server)
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
        header_content = f"{translate('Latest Back-up')}  [color=#494977]-[/color]  " + (
            f'[color=#6A6ABA]{translate("Never")}[/color]' if not backup_stats[
                'latest-backup'] else f'[font={very_bold_font}]{backup_stats["latest-backup"]}[/font]')
        sub_header_content = f"{backup_count:,}  back-up" + ("" if backup_count == 1 else "s") + (
            f"   ({backup_stats['total-size']})" if backup_count > 0 else "")
        self.header = HeaderText(header_content, sub_header_content, (0, 0.89), __translate__=(False, True))
        float_layout.add_widget(self.header)

        buttons.append(ExitButton('Back', (0.5, -1), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)

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

        _animate_background(self, image, hover_action)

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
            self.type_image.version_label.x = self.width + self.x - (
                        self.padding_x * offset) - self.type_image.width - 83
            self.type_image.version_label.y = self.y - (self.height / 3.2)

        # Banner version object
        else:
            self.type_image.version_label.x = self.width + self.x - (
                        self.padding_x * offset) - self.type_image.width - 130
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
        self.type_image.image = Image(
            source=os.path.join(paths.ui_assets, 'icons', 'big', f'{backup_object.type.lower()}_small.png'))
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
        if backup_object.build:
            self.type_image.version_label.text = f'{backup_object.version.lower()} (b-{backup_object.build.lower()})'
        else:
            self.type_image.version_label.text = backup_object.version.lower()
        self.type_image.version_label.opacity = 0.6

        self.type_image.type_label = TemplateLabel()
        self.type_image.type_label.text = backup_object.type.lower().replace("craft", "")
        self.type_image.type_label.font_size = sp(23)
        self.type_image.add_widget(self.type_image.version_label)
        self.type_image.add_widget(self.type_image.type_label)
        self.add_widget(self.type_image)

        self.bind(pos=self.resize_self)

        # If click_function
        if click_function:
            self.bind(on_press=click_function)

        # Animate opacity
        if fade_in > 0:
            self.opacity = 0
            self.title.opacity = 0

            Animation(opacity=1, duration=fade_in).start(self)
            Animation(opacity=1, duration=fade_in).start(self.title)
            Animation(opacity=self.subtitle.default_opacity, duration=fade_in).start(self.subtitle)

    def on_enter(self, *args):
        if not self.ignore_hover:
            self.animate_button(image=os.path.join(paths.ui_assets, f'{self.id}_hover.png'), color=self.color_id[0],
                                hover_action=True)

    def on_leave(self, *args):
        if not self.ignore_hover:
            self.animate_button(image=os.path.join(paths.ui_assets, f'{self.id}{"_ro" if self.newest else ""}.png'),
                                color=self.color_id[1], hover_action=False)


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

                    selected_button = \
                    [item for item in self.scroll_layout.walk() if item.__class__.__name__ == "BackupButton"][index - 1]
                    if constants.server_manager.current_server.running:
                        utility.screen_manager.current_screen.show_popup(
                            "query",
                            "Stop & Restore Back-up",
                            f"Are you sure you want to stop and revert '{backup_obj.name}' to {backup_obj.date}?\n\nThis action can't be undone",
                            [None,
                             functools.partial(Clock.schedule_once, functools.partial(restore_screen, backup_obj, True),
                                               0.25)]
                        )
                    else:
                        utility.screen_manager.current_screen.show_popup(
                            "query",
                            "Restore Back-up",
                            f"Are you sure you want to revert '${backup_obj.name}$' to ${backup_obj.date}$?\n\nThis action can't be undone",
                            [None, functools.partial(Clock.schedule_once,
                                                     functools.partial(restore_screen, backup_obj, False), 0.25)]
                        )

                # Add-on button click function
                self.scroll_layout.add_widget(
                    ScrollItem(
                        widget=BackupButton(
                            backup_object=backup_object,
                            fade_in=((x if x <= 8 else 8) / self.anim_speed) if fade_in else 0,
                            index=x + ((self.current_page - 1) * self.page_size),
                            click_function=functools.partial(
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
        self.scroll_layout = GridLayout(cols=1, spacing=15, size_hint_max_x=1250, size_hint_y=None,
                                        padding=[0, 30, 0, 30])

        # Bind / cleanup height on resize
        def resize_scroll(call_widget, grid_layout, anchor_layout, *args):
            call_widget.height = Window.height // 1.82
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
        scroll_top = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.795}, pos=scroll_widget.pos,
                                       size=(scroll_widget.width // 1.5, 60))
        scroll_bottom = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.26}, pos=scroll_widget.pos,
                                          size=(scroll_widget.width // 1.5, -60))

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

        for button in buttons:
            float_layout.add_widget(button)

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
                            if download_button:
                                Clock.schedule_once(functools.partial(download_button.loading, True), 0)

                        location = constants.telepath_download(server_obj._telepath_data, backup_obj.path,
                                                               paths.user_downloads)
                        if os.path.exists(location):
                            constants.open_folder(location)
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
                            if download_button:
                                Clock.schedule_once(functools.partial(download_button.loading, False), 0)

                    dTimer(0, download_thread).start()

                # Add-on button click function
                self.scroll_layout.add_widget(
                    ScrollItem(
                        widget=BackupButton(
                            backup_object=backup_object,
                            fade_in=((x if x <= 8 else 8) / self.anim_speed) if fade_in else 0,
                            index=x + ((self.current_page - 1) * self.page_size),
                            click_function=functools.partial(
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
        self.scroll_layout = GridLayout(cols=1, spacing=15, size_hint_max_x=1250, size_hint_y=None,
                                        padding=[0, 30, 0, 30])

        # Bind / cleanup height on resize
        def resize_scroll(call_widget, grid_layout, anchor_layout, *args):
            call_widget.height = Window.height // 1.82
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
        scroll_top = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.795}, pos=scroll_widget.pos,
                                       size=(scroll_widget.width // 1.5, 60))
        scroll_bottom = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.26}, pos=scroll_widget.pos,
                                          size=(scroll_widget.width // 1.5, -60))

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

        for button in buttons:
            float_layout.add_widget(button)

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
            if final < 0:
                final = original
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
            ('Restoring back-up',
             functools.partial(foundry.restore_server, restore_file, functools.partial(adjust_percentage, 70)), 0),
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

        def start_clone(*a):
            utility.screen_manager.current = 'ServerCloneProgressScreen'

        buttons.append(next_button('Clone', (0.5, 0.24), False, click_func=start_clone))
        buttons.append(ExitButton('Back', (0.5, 0.14), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)

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
        open_after = functools.partial(self.open_server, server_name, True,
                                       f"'${server_name}$' was created successfully")

        def before_func(*args):

            if not constants.check_free_space(telepath_data=foundry.new_server_info['_telepath_data']):
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

            def restore_server():
                constants.server_manager.current_server = server_obj

            self._error_callback = restore_server

        function_list = [
            (java_text, functools.partial(constants.java_check, functools.partial(adjust_percentage, 30)), 0),
            ('Saving a back-up', server_obj.backup.save, 10),
            ('Cloning server',
             functools.partial(manager.clone_server, server_obj, functools.partial(adjust_percentage, 50)), 0),
            ('Creating initial back-up', functools.partial(foundry.create_backup, True), 10)
        ]

        self.page_contents['function_list'] = tuple(function_list)


# Server Access Control ------------------------------------------------------------------------------------------------

class ServerAclScreen(CreateServerAclScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.menu_taskbar = None

    def generate_menu(self, **kwargs):

        # If self._hash doesn't match, set list to ops by default
        if self._hash != constants.server_manager.current_server._hash:
            self.acl_object = constants.server_manager.current_server.acl
            self._hash = constants.server_manager.current_server._hash
            self.current_list = 'ops'

        self.show_panel = False

        self.filter_text = ""
        self.currently_filtering = False

        # Scroll list
        self.scroll_widget = RecycleViewWidget(position=(0.5, 0.455), view_class=RuleButton)
        self.scroll_layout = RecycleGridLayout(spacing=[110, -15], size_hint_y=None, padding=[60, 20, 0, 30])
        test_rule = RuleButton()

        # Bind / cleanup height on resize
        def resize_scroll(*args):
            self.scroll_widget.height = Window.height // 1.69
            rule_width = test_rule.width + self.scroll_layout.spacing[0] + 2
            rule_width = int(((Window.width // rule_width) // 1) - 2)

            self.scroll_layout.cols = rule_width
            self.scroll_layout.rows = 2 if len(self.scroll_widget.data) <= rule_width else None

            self.user_panel.x = Window.width - (self.user_panel.size_hint_max[0] * 0.93)

            # Reposition header
            for child in self.header.children:
                if child.id == "text":
                    child.halign = "left"
                    child.text_size[0] = 500
                    child.x = Window.width / 2 + 240
                    break

            self.search_label.pos_hint = {"center_x": (0.28 if Window.width < 1300 else 0.5), "center_y": 0.42}
            self.search_label.text_size = (Window.width / 3, 500)

        self.resize_bind = lambda *_: Clock.schedule_once(functools.partial(resize_scroll), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        self.scroll_layout.bind(minimum_height=self.scroll_layout.setter('height'))
        self.scroll_layout.id = 'scroll_content'

        # Scroll gradient
        scroll_top = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.735}, pos=self.scroll_widget.pos,
                                       size=(self.scroll_widget.width // 1.5, 60))
        scroll_bottom = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.175}, pos=self.scroll_widget.pos,
                                          size=(self.scroll_widget.width // 1.5, -60))

        # Generate buttons on page load
        selector_text = "operators" if self.current_list == "ops" else "bans" if self.current_list == "bans" else "whitelist"
        self.page_selector = DropButton(selector_text, (0.5, 0.89), options_list=['operators', 'bans', 'whitelist'],
                                        input_name='ServerAclTypeInput', x_offset=-210, facing='center',
                                        custom_func=self.update_list)
        header_content = ""
        self.header = HeaderText(header_content, '', (0, 0.89), fixed_x=True, no_line=True)

        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'
        float_layout.add_widget(self.header)

        # Search bar
        self.search_bar = AclInput(pos_hint={"center_x": 0.5, "center_y": 0.815})
        buttons.append(input_button('Add Rules...', (0.5, 0.815), input_name='AclInput'))

        # Whitelist toggle button
        def toggle_whitelist(boolean):
            self.acl_object.enable_whitelist(boolean)

            Clock.schedule_once(
                functools.partial(
                    self.show_banner,
                    (0.553, 0.902, 0.675, 1) if boolean else (0.937, 0.831, 0.62, 1),
                    f"Server whitelist {'en' if boolean else 'dis'}abled",
                    "shield-checkmark-outline.png" if boolean else "shield-disabled-outline.png",
                    2,
                    {"center_x": 0.5, "center_y": 0.965}
                ), 0
            )

            # Update list
            self.update_list('wl', reload_children=True, reload_panel=True)

        self.whitelist_toggle = toggle_button('whitelist', (0.5, 0.89),
                                              default_state=self.acl_object._server['whitelist'], x_offset=-395,
                                              custom_func=toggle_whitelist)

        # Legend for rule types
        self.list_header = BoxLayout(orientation="horizontal", pos_hint={"center_x": 0.5, "center_y": 0.749},
                                     size_hint_max=(400, 100))
        self.list_header.global_rule = RelativeLayout()
        self.list_header.global_rule.add_widget(
            BannerObject(size=(120, 32), color=test_rule.global_icon_color, text="global", icon="earth-sharp.png",
                         icon_side="left"))
        self.list_header.add_widget(self.list_header.global_rule)

        self.list_header.enabled_rule = RelativeLayout()
        self.list_header.enabled_rule.add_widget(
            BannerObject(size=(120, 32), color=(1, 1, 1, 1), text=" ", icon="add.png"))
        self.list_header.add_widget(self.list_header.enabled_rule)

        self.list_header.disabled_rule = RelativeLayout()
        self.list_header.disabled_rule.add_widget(
            BannerObject(size=(120, 32), color=(1, 1, 1, 1), text=" ", icon="add.png"))
        self.list_header.add_widget(self.list_header.disabled_rule)

        # Add blank label to the center, then load self.gen_search_results()
        self.blank_label = Label()
        self.blank_label.text = ""
        self.blank_label.font_name = os.path.join(paths.ui_assets, 'fonts', constants.fonts['italic'])
        self.blank_label.pos_hint = {"center_x": 0.5, "center_y": 0.48}
        self.blank_label.font_size = sp(23)
        self.blank_label.opacity = 0
        self.blank_label.color = (0.6, 0.6, 1, 0.35)
        float_layout.add_widget(self.blank_label)

        # Lol search label idek
        self.search_label = Label()
        self.search_label.text = ""
        self.search_label.halign = "center"
        self.search_label.valign = "center"
        self.search_label.font_name = os.path.join(paths.ui_assets, 'fonts', constants.fonts['italic'])
        self.search_label.pos_hint = {"center_x": 0.28, "center_y": 0.42}
        self.search_label.font_size = sp(25)
        self.search_label.color = (0.6, 0.6, 1, 0.35)
        float_layout.add_widget(self.search_label)

        # Controls button
        def show_controls():

            controls_text = """This menu shows enabled rules from files like 'ops.json', and disabled rules as others who have joined. Global rules are applied to every server. Rules can be modified in a few different ways:

• Right-click a rule to view, and see more options

• Left-click a rule to toggle permission

• Press middle-mouse to toggle globally

Rules can be filtered with the search bar, and can be added with the 'Add Rules' button or by pressing 'TAB'. The visible list can be switched between operators, bans, and the whitelist from the drop-down at the top."""

            Clock.schedule_once(
                functools.partial(
                    self.show_popup,
                    "controls",
                    "Controls",
                    controls_text,
                    (None)
                ),
                0
            )

        self.controls_button = IconButton('controls', {}, (70, 110), (None, None), 'question.png', clickable=True,
                                          anchor='right', click_func=show_controls)

        # User panel
        self.user_panel = AclRulePanel()
        self.user_panel.pos_hint = {"center_y": 0.44}

        # Append scroll view items
        self.scroll_widget.add_widget(self.scroll_layout)
        float_layout.add_widget(self.scroll_widget)
        float_layout.add_widget(scroll_top)
        float_layout.add_widget(scroll_bottom)
        float_layout.add_widget(self.page_selector)
        float_layout.add_widget(self.list_header)
        float_layout.add_widget(self.search_bar)
        float_layout.add_widget(self.whitelist_toggle)
        float_layout.add_widget(self.user_panel)

        buttons.append(ExitButton('Back', (0.5, -1), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)

        menu_name = f"{constants.server_manager.current_server.name}, Access Control"
        float_layout.add_widget(
            generate_title(f"Access Control Manager: '{constants.server_manager.current_server.name}'"))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)

        # Add ManuTaskbar
        self.menu_taskbar = MenuTaskbar(selected_item='access control')
        self.add_widget(self.menu_taskbar)

        # Add controls after taskbar because it's unclickable for some reason
        float_layout.add_widget(self.controls_button)

        # Generate page content
        self.update_list(self.current_list, reload_children=True)

        # Generate user panel info
        current_list = acl.deepcopy(self.acl_object.rules[self.current_list])
        if self.current_list == "bans":
            current_list.extend(acl.deepcopy(self.acl_object.rules['subnets']))

        if self.acl_object.displayed_rule and current_list:
            global_rules = acl.load_global_acl()
            self.acl_object.displayed_rule.acl_group = self.current_list
            rule_scope = acl.check_global_acl(global_rules, self.acl_object.displayed_rule).rule_scope
            self.update_user_panel(self.acl_object.displayed_rule.rule, rule_scope)
        else:
            self.update_user_panel(None, None)


class ServerAclRuleScreen(CreateServerAclRuleScreen):

    def generate_menu(self, **kwargs):
        # Generate buttons on page load

        class HintLabel(RelativeLayout):

            def icon_pos(self, *args):
                self.text.texture_update()
                self.icon.pos_hint = {"center_x": 0.57 - (0.005 * self.text.texture_size[0]), "center_y": 0.95}

            def __init__(self, pos, label, **kwargs):
                super().__init__(**kwargs)

                self.pos_hint = {"center_x": 0.5, "center_y": pos}
                self.size_hint_max = (100, 50)

                self.text = Label()
                self.text.id = 'text'
                self.text.size_hint = (None, None)
                self.text.markup = True
                self.text.halign = "center"
                self.text.valign = "center"
                self.text.text = "        " + label
                self.text.font_size = sp(22)
                self.text.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
                self.text.color = (0.6, 0.6, 1, 0.55)

                self.icon = Image()
                self.icon.id = 'icon'
                self.icon.source = os.path.join(paths.ui_assets, 'icons', 'information-circle-outline.png')
                self.icon.pos_hint = {"center_y": 0.95}
                self.icon.color = (0.6, 0.6, 1, 1)

                self.add_widget(self.text)
                self.add_widget(self.icon)

                self.bind(size=self.icon_pos)
                self.bind(pos=self.icon_pos)

        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'

        self.current_list = utility.screen_manager.get_screen("ServerAclScreen").current_list
        self.acl_object = utility.screen_manager.get_screen("ServerAclScreen").acl_object

        if self.current_list == "bans":
            header_message = "Enter usernames/IPs delimited, by, commas"
            float_layout.add_widget(
                HintLabel(0.464, "Use   [color=#FFFF33]!g <rule>[/color]   to apply globally on all servers"))
            float_layout.add_widget(HintLabel(0.374,
                                              "You can ban IP ranges/whitelist:   [color=#FF6666]192.168.0.0-150[/color], [color=#66FF88]!w 192.168.1.1[/color]"))
        else:
            header_message = "Enter usernames delimited, by, commas"
            float_layout.add_widget(
                HintLabel(0.425, "Use   [color=#FFFF33]!g <rule>[/color]   to apply globally on all servers"))

        float_layout.add_widget(InputLabel(pos_hint={"center_x": 0.5, "center_y": 0.72}))
        float_layout.add_widget(HeaderText(header_message, '', (0, 0.8)))
        self.acl_input = AclRuleInput(pos_hint={"center_x": 0.5, "center_y": 0.64}, text="")
        float_layout.add_widget(self.acl_input)

        buttons.append(next_button('Add Rules', (0.5, 0.24), True, next_screen='ServerAclScreen'))
        buttons.append(ExitButton('Back', (0.5, 0.14), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)

        menu_name = f"{constants.server_manager.current_server.name}, Access Control"
        list_name = "Operators" if self.current_list == "ops" else "Bans" if self.current_list == "bans" else "Whitelist"
        float_layout.add_widget(generate_title(f"Access Control Manager: Add {list_name}"))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)
        self.acl_input.grab_focus()


# Server Add-on Manager ------------------------------------------------------------------------------------------------

class AddonListButton(HoverButton):

    def toggle_enabled(self, *args):
        self.title.text_size = (self.size_hint_max[0] * (0.7), self.size_hint_max[1])
        self.background_normal = os.path.join(paths.ui_assets, f'{self.id}{"" if self.enabled else "_disabled"}.png')

        # If disabled, add banner as such
        if not self.enabled:
            self.disabled_banner = BannerObject(
                pos_hint={"center_x": 0.5, "center_y": 0.5},
                size=(125, 32),
                color=(1, 0.53, 0.58, 1),
                text="disabled",
                icon="close-circle.png",
                icon_side="right"
            )
            self.add_widget(self.disabled_banner)

        self.resize_self()

    def resize_self(self, *args):

        # Title and description
        padding = 2.17
        self.title.pos = (self.x + (self.title.text_size[0] / padding) - 6, self.y + 31)
        self.subtitle.pos = (self.x + (self.subtitle.text_size[0] / padding) - 1, self.y)
        self.hover_text.pos = (self.x + (self.size[0] / padding) - 30, self.y + 15)

        # Type Banner
        if self.disabled_banner:
            self.disabled_banner.pos_hint = {"center_x": None, "center_y": None}
            self.disabled_banner.pos = (self.width + self.x - self.disabled_banner.width - 18, self.y + 38.5)

        # Delete button
        self.delete_layout.size_hint_max = (self.size_hint_max[0], self.size_hint_max[1])
        self.delete_layout.pos = (self.pos[0] + self.width - (self.delete_button.width / 1.33), self.pos[1] + 13)

        # Reposition highlight border
        self.highlight_layout.pos = self.pos

    def highlight(self):
        def next_frame(*args):
            Animation.stop_all(self.highlight_border)
            self.highlight_border.opacity = 1
            Animation(opacity=0, duration=0.7).start(self.highlight_border)

        Clock.schedule_once(next_frame, 0)

    def __init__(self, properties, click_function=None, enabled=False, fade_in=0.0, highlight=False, **kwargs):
        super().__init__(**kwargs)

        self.anim_duration = 0.06
        self.enabled = enabled
        self.properties = properties
        self.border = (-5, -5, -5, -5)
        self.color_id = [(0.05, 0.05, 0.1, 1), (0.65, 0.65, 1, 1)] if self.enabled else [(0.05, 0.1, 0.1, 1),
                                                                                         (1, 0.6, 0.7, 1)]
        self.pos_hint = {"center_x": 0.5, "center_y": 0.6}
        self.size_hint_max = (580, 80)
        self.id = "addon_button"
        self.background_normal = os.path.join(paths.ui_assets, f'{self.id}.png')
        self.background_down = self.background_normal
        self.disabled_banner = None

        # Delete button
        def delete_hover(*args):
            def change_color(*args):
                if self.hovered:
                    self.hover_text.text = 'UNINSTALL ADD-ON'
                    self.background_normal = os.path.join(paths.ui_assets, "server_button_favorite_hover.png")

            Clock.schedule_once(change_color, 0.07)
            Animation.stop_all(self.delete_button)
            Animation(opacity=1, duration=0.25).start(self.delete_button)

        def delete_on_leave(*args):
            def change_color(*args):
                self.hover_text.text = ('DISABLE ADD-ON' if self.enabled else 'ENABLE ADD-ON')
                if self.hovered:
                    self.background_normal = os.path.join(paths.ui_assets,
                                                          f'{self.id}_hover_{"dis" if self.enabled else "en"}abled.png')
                    self.background_down = self.background_normal

            Clock.schedule_once(change_color, 0.07)
            Animation.stop_all(self.delete_button)
            Animation(opacity=0.65, duration=0.25).start(self.delete_button)

        def delete_click(*args):
            # Delete addon and reload list
            def reprocess_page(*args):
                addon_manager = constants.server_manager.current_server.addon
                addon_manager.delete_addon(self.properties)
                addon_screen = utility.screen_manager.current_screen
                new_list = [addon for addon in addon_manager.return_single_list() if not addons.is_geyser_addon(addon)]
                addon_screen.gen_search_results(new_list, fade_in=True)
                Clock.schedule_once(
                    functools.partial(addon_screen.search_bar.execute_search, addon_screen.search_bar.previous_search),
                    0)

                # Show banner if server is running
                if addon_manager._hash_changed():
                    Clock.schedule_once(
                        functools.partial(
                            utility.screen_manager.current_screen.show_banner,
                            (0.937, 0.831, 0.62, 1),
                            f"A server restart is required to apply changes",
                            "sync.png",
                            3,
                            {"center_x": 0.5, "center_y": 0.965}
                        ), 0
                    )

                else:
                    Clock.schedule_once(
                        functools.partial(
                            utility.screen_manager.current_screen.show_banner,
                            (1, 0.5, 0.65, 1),
                            f"'${self.properties.name}$' was uninstalled",
                            "trash-sharp.png",
                            2.5,
                            {"center_x": 0.5, "center_y": 0.965}
                        ), 0.25
                    )

                # Switch pages if page is empty
                if (len(addon_screen.scroll_layout.children) == 0) and (len(new_list) > 0):
                    addon_screen.switch_page("left")

            Clock.schedule_once(
                functools.partial(
                    utility.screen_manager.current_screen.show_popup,
                    "warning_query",
                    f'Uninstall ${self.properties.name}$',
                    "Do you want to permanently uninstall this add-on?\n\nYou'll need to re-import or download it again",
                    (None, functools.partial(reprocess_page))
                ),
                0
            )

        self.delete_layout = RelativeLayout(opacity=0)
        self.delete_button = IconButton('', {}, (0, 0), (None, None), 'trash-sharp.png', clickable=True,
                                        force_color=[[(0.05, 0.05, 0.1, 1), (0.01, 0.01, 0.01, 1)], 'pink'],
                                        anchor='right', click_func=delete_click)
        self.delete_button.opacity = 0.65
        self.delete_button.button.bind(on_enter=delete_hover)
        self.delete_button.button.bind(on_leave=delete_on_leave)
        self.delete_layout.add_widget(self.delete_button)
        self.add_widget(self.delete_layout)

        # Hover text
        self.hover_text = Label()
        self.hover_text.id = 'hover_text'
        self.hover_text.size_hint = (None, None)
        self.hover_text.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        self.hover_text.text = ('DISABLE ADD-ON' if self.enabled else 'ENABLE ADD-ON')
        self.hover_text.font_size = sp(23)
        self.hover_text.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["bold"]}.ttf')
        self.hover_text.color = (0.1, 0.1, 0.1, 1)
        self.hover_text.halign = "center"
        self.hover_text.text_size = (self.size_hint_max[0] * 0.94, self.size_hint_max[1])
        self.hover_text.opacity = 0
        self.add_widget(self.hover_text)

        # Loading stuffs
        self.original_subtitle = self.properties.subtitle if self.properties.subtitle else "Description unavailable"
        self.original_font = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["regular"]}.ttf')

        # Title of Addon
        self.title = Label()
        self.title.__translate__ = False
        self.title.id = "title"
        self.title.halign = "left"
        self.title.color = self.color_id[1]
        self.title.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
        self.title.font_size = sp(25)
        self.title.text_size = (self.size_hint_max[0] * (0.7), self.size_hint_max[1])
        self.title.shorten = True
        self.title.markup = True
        self.title.shorten_from = "right"
        self.title.max_lines = 1
        self.title.text = f"{self.properties.name}  [color=#434368]-[/color]  {self.properties.author if self.properties.author else 'Unknown'}"
        self.add_widget(self.title)
        Clock.schedule_once(self.toggle_enabled, 0)

        # Description of Addon
        self.subtitle = Label()
        self.subtitle.__translate__ = False
        self.subtitle.id = "subtitle"
        self.subtitle.halign = "left"
        self.subtitle.color = self.color_id[1]
        self.subtitle.font_name = self.original_font
        self.subtitle.font_size = sp(21)
        self.default_subtitle_opacity = 0.56
        self.subtitle.opacity = self.default_subtitle_opacity
        self.subtitle.text_size = (self.size_hint_max[0] * 0.91, self.size_hint_max[1])
        self.subtitle.shorten = True
        self.subtitle.shorten_from = "right"
        self.subtitle.max_lines = 1
        self.subtitle.text = self.original_subtitle
        self.add_widget(self.subtitle)

        # Highlight border
        self.highlight_layout = RelativeLayout()
        self.highlight_border = Image()
        self.highlight_border.keep_ratio = False
        self.highlight_border.allow_stretch = True
        self.highlight_border.color = constants.brighten_color(self.color_id[1], 0.1)
        self.highlight_border.opacity = 0
        self.highlight_border.source = os.path.join(paths.ui_assets, 'server_button_highlight.png')
        self.highlight_layout.add_widget(self.highlight_border)
        self.highlight_layout.width = self.size_hint_max[0]
        self.highlight_layout.height = self.size_hint_max[1]
        self.add_widget(self.highlight_layout)

        if highlight:
            self.highlight()

        # If self.enabled is false, and self.properties.version, display version where "enabled" logo is
        self.bind(pos=self.resize_self)
        self.resize_self()

        # If click_function
        if click_function:
            self.bind(on_press=click_function)

        # Animate opacity
        if fade_in > 0:
            self.opacity = 0
            self.title.opacity = 0

            Animation(opacity=1, duration=fade_in).start(self)
            Animation(opacity=1, duration=fade_in).start(self.title)
            Animation(opacity=0.56, duration=fade_in).start(self.subtitle)

    def on_enter(self, *args):
        if not self.ignore_hover:

            # Hide disabled banner if it exists
            if self.disabled_banner:
                Animation.stop_all(self.disabled_banner)
                Animation(opacity=0, duration=self.anim_duration).start(self.disabled_banner)

            # Fade button to hover state
            # if not self.delete_button.button.hovered:
            Animation(color=self.color_id[0], duration=(self.anim_duration * 0.5)).start(self.title)
            Animation(color=self.color_id[0], duration=(self.anim_duration * 0.5)).start(self.subtitle)
            animate_button(self, image=os.path.join(paths.ui_assets,
                                                    f'{self.id}_hover_{"dis" if self.enabled else "en"}abled.png'),
                           color=self.color_id[0], hover_action=True)

            # Show delete button
            Animation.stop_all(self.delete_layout)
            Animation(opacity=1, duration=self.anim_duration).start(self.delete_layout)

            # Hide text
            Animation(opacity=0, duration=self.anim_duration).start(self.title)
            Animation(opacity=0, duration=self.anim_duration).start(self.subtitle)
            Animation(opacity=1, duration=self.anim_duration).start(self.hover_text)

    def on_leave(self, *args):
        if not self.ignore_hover:

            # Hide disabled banner if it exists
            if self.disabled_banner:
                Animation.stop_all(self.disabled_banner)
                Animation(opacity=1, duration=self.anim_duration).start(self.disabled_banner)

            # Fade button to default state
            # if not self.delete_button.button.hovered:
            Animation(color=self.color_id[1], duration=(self.anim_duration * 0.5)).start(self.title)
            Animation(color=self.color_id[1], duration=(self.anim_duration * 0.5)).start(self.subtitle)
            animate_button(self,
                           image=os.path.join(paths.ui_assets, f'{self.id}{"" if self.enabled else "_disabled"}.png'),
                           color=self.color_id[1], hover_action=False)

            # Hide delete button
            Animation.stop_all(self.delete_layout)
            Animation(opacity=0, duration=self.anim_duration).start(self.delete_layout)

            # Show text
            Animation(opacity=1, duration=self.anim_duration).start(self.title)
            Animation(opacity=self.default_subtitle_opacity, duration=0.13).start(self.subtitle)
            Animation(opacity=0, duration=self.anim_duration).start(self.hover_text)

    def loading(self, load_state, *args):
        if load_state:
            self.subtitle.text = "Loading add-on info..."
            self.subtitle.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
        else:
            self.subtitle.text = self.original_subtitle
            self.subtitle.font_name = self.original_font


class ServerAddonUpdateScreen(ProgressScreen):

    # Only replace this function when making a child screen
    # Set fail message in child functions to trigger an error
    def contents(self):
        server_obj = constants.server_manager.current_server
        icons = os.path.join(paths.ui_assets, 'fonts', constants.fonts['icons'])
        desc_text = "Updating"
        final_text = "Updated"

        def before_func(*args):

            if not constants.app_online:
                self.execute_error(
                    "An internet connection is required to continue\n\nVerify connectivity and try again")

            elif not constants.check_free_space(telepath_data=server_obj._telepath_data):
                self.execute_error("Your primary disk is almost full\n\nFree up space and try again")

            else:
                foundry.pre_addon_update()

        def after_func(*args):
            self.steps.label_2.text = "Updates complete!" + f"   [font={icons}]å[/font]"

            foundry.post_addon_update()

            if server_obj.running:
                Clock.schedule_once(
                    functools.partial(
                        utility.screen_manager.current_screen.show_banner,
                        (0.937, 0.831, 0.62, 1),
                        f"A server restart is required to apply changes",
                        "sync.png",
                        3,
                        {"center_x": 0.5, "center_y": 0.965}
                    ), 1
                )

            else:
                Clock.schedule_once(
                    functools.partial(
                        utility.screen_manager.current_screen.show_banner,
                        (0.553, 0.902, 0.675, 1),
                        f"{final_text} add-ons successfully",
                        "checkmark-circle-sharp.png",
                        3,
                        {"center_x": 0.5, "center_y": 0.965}
                    ), 1
                )

            utility.screen_manager.screen_tree = ['MainMenuScreen', 'ServerManagerScreen']

        # Original is percentage before this function, adjusted is a percent of hooked value
        def adjust_percentage(*args):
            original = self.last_progress
            adjusted = args[0]
            total = args[1] * 0.01
            final = original + round(adjusted * total)
            if final < 0:
                final = original

            if self.telepath:
                completed_count = addon_count = len(server_obj.addon.return_single_list())
            else:
                addon_count = len(foundry.new_server_info['addon_objects'])
                completed_count = round(len(foundry.new_server_info['addon_objects']) * (final * 0.01))
            self.steps.label_2.text = "Updating Add-ons" + f"   ({completed_count}/{addon_count})"

            self.progress_bar.update_progress(final)

        self.page_contents = {

            # Page name
            'title': f"{desc_text} add-ons",

            # Header text
            'header': "Sit back and relax, it's automation time...",

            # Tuple of tuples for steps (label, function, percent)
            # Percent of all functions must total 100
            # Functions must return True, or default error will be executed
            'default_error': 'There was an issue, please try again later',

            'function_list': (
                (f'{desc_text} Add-ons...',
                 functools.partial(foundry.iter_addons, functools.partial(adjust_percentage, 100), True), 0),
            ),

            # Function to run before steps (like checking for an internet connection)
            'before_function': before_func,

            # Function to run after everything is complete (like cleaning up the screen tree) will only run if no error
            'after_function': after_func,

            # Screen to go to after complete
            'next_screen': 'ServerAddonScreen'
        }


class ServerAddonScreen(MenuBackground):

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

    def gen_search_results(self, results, new_search=False, fade_in=True, highlight=None, animate_scroll=True,
                           last_scroll=None, *args):

        # Update page counter
        # results = list(sorted(results, key=lambda d: d.name.lower()))
        # Set to proper page on toggle

        addon_manager = constants.server_manager.current_server.addon
        default_scroll = 1
        if highlight:
            def divide_chunks(l, n):
                final_list = []

                for i in range(0, len(l), n):
                    final_list.append(l[i:i + n])

                return final_list

            for x, l in enumerate(divide_chunks([x.hash for x in results], self.page_size), 1):
                if highlight in l:
                    if self.current_page != x:
                        self.current_page = x

                    # Update scroll when page is bigger than list
                    if Window.height < self.scroll_layout.height * 1.7:
                        default_scroll = 1 - round(l.index(highlight) / len(l), 2)
                        if default_scroll < 0.21:
                            default_scroll = 0
                        if default_scroll > 0.97:
                            default_scroll = 1
                    break

        self.last_results = results
        self.max_pages = (len(results) / self.page_size).__ceil__()
        self.current_page = 1 if self.current_page == 0 or new_search else self.current_page

        self.page_switcher.update_index(self.current_page, self.max_pages)
        page_list = results[(self.page_size * self.current_page) - self.page_size:self.page_size * self.current_page]

        self.scroll_layout.clear_widgets()

        # Animate scrolling
        def set_scroll(*args):
            Animation.stop_all(self.scroll_layout.parent.parent)
            if animate_scroll:
                Animation(scroll_y=default_scroll, duration=0.1).start(self.scroll_layout.parent.parent)
            else:
                self.scroll_layout.parent.parent.scroll_y = default_scroll

        Clock.schedule_once(set_scroll, 0)

        # Generate header
        addon_count = len(results)
        enabled_count = len(
            [addon for addon in addon_manager.installed_addons['enabled'] if not addons.is_geyser_addon(addon)])
        disabled_count = len(addon_manager.installed_addons['disabled'])
        very_bold_font = os.path.join(paths.ui_assets, 'fonts', constants.fonts["very-bold"])
        header_content = f"{translate('Installed Add-ons')}  [color=#494977]-[/color]  " + (
            f'[color=#6A6ABA]{translate("No items")}[/color]' if addon_count == 0 else f'[font={very_bold_font}]1[/font] {translate("item")}' if addon_count == 1 else f'[font={very_bold_font}]{enabled_count:,}{("/[color=#FF8793]" + str(disabled_count) + "[/color]") if disabled_count > 0 else ""}[/font] {translate("items")}')

        if addon_manager._hash_changed():
            icons = os.path.join(paths.ui_assets, 'fonts', constants.fonts['icons'])
            header_content = f"[color=#EFD49E][font={icons}]y[/font] " + header_content + "[/color]"

        for child in self.header.children:
            if child.id == "text":
                child.text = header_content
                break

        # If there are no addons, say as much with a label
        if addon_count == 0:
            self.blank_label.text = "Import or Download add-ons below"
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
                if addons.is_geyser_addon(addon_object):
                    continue

                # Activated when addon is clicked
                def toggle_addon(index, *args):
                    addon = index

                    if len(addon.name) < 26:
                        addon_name = addon.name
                    else:
                        addon_name = addon.name[:23] + "..."

                    # Toggle addon state
                    success = addon_manager.addon_state(addon, enabled=not addon.enabled)
                    if not success:
                        Clock.schedule_once(
                            functools.partial(
                                self.show_banner,
                                (0.937, 0.831, 0.62, 1),
                                f"can't disable while the server is running",
                                "alert-circle-sharp.png",
                                3,
                                {"center_x": 0.5, "center_y": 0.965}
                            ), 0
                        )
                        return False
                    addon_list = [addon for addon in addon_manager.return_single_list() if
                                  not addons.is_geyser_addon(addon)]
                    self.gen_search_results(addon_list, fade_in=False, highlight=addon.hash, animate_scroll=True)

                    # Show banner if server is running
                    if addon_manager._hash_changed():
                        Clock.schedule_once(
                            functools.partial(
                                self.show_banner,
                                (0.937, 0.831, 0.62, 1),
                                f"A server restart is required to apply changes",
                                "sync.png",
                                3,
                                {"center_x": 0.5, "center_y": 0.965}
                            ), 0
                        )

                    else:
                        if addon.enabled:
                            banner_text = f"'${addon_name}$' is now disabled"
                        else:
                            banner_text = f"'${addon_name}$' is now enabled"

                        Clock.schedule_once(
                            functools.partial(
                                self.show_banner,
                                (1, 0.5, 0.65, 1) if addon.enabled else (0.553, 0.902, 0.675, 1),
                                banner_text,
                                "close-circle-sharp.png" if addon.enabled else "checkmark-circle-sharp.png",
                                2.5,
                                {"center_x": 0.5, "center_y": 0.965}
                            ), 0
                        )

                # Add-on button click function
                self.scroll_layout.add_widget(
                    ScrollItem(
                        widget=AddonListButton(
                            properties=addon_object,
                            enabled=addon_object.enabled,
                            fade_in=((x if x <= 8 else 8) / self.anim_speed) if fade_in else 0,
                            highlight=(highlight == addon_object.hash),
                            click_function=functools.partial(
                                toggle_addon,
                                addon_object,
                                x
                            )
                        )
                    )
                )

            self.resize_bind()
            # self.scroll_layout.parent.parent.scroll_y = 1

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'
        self.header = None
        self.scroll_layout = None
        self.blank_label = None
        self.search_bar = None
        self.page_switcher = None
        self.menu_taskbar = None
        self.update_button = None

        self.last_results = []
        self.page_size = 20
        self.current_page = 0
        self.max_pages = 0
        self.anim_speed = 10

        self.server = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        super()._on_keyboard_down(keyboard, keycode, text, modifiers)

        # Press arrow keys to switch pages
        if keycode[1] in ['right', 'left'] and self.name == utility.screen_manager.current_screen.name:
            self.switch_page(keycode[1])

    def generate_menu(self, **kwargs):
        self.server = constants.server_manager.current_server

        # Return if no free space
        if disk_popup('ServerViewScreen', telepath_data=self.server._telepath_data):
            return

        # Scroll list
        scroll_widget = ScrollViewWidget(position=(0.5, 0.5))
        scroll_anchor = AnchorLayout()
        self.scroll_layout = GridLayout(cols=1, spacing=15, size_hint_max_x=1250, size_hint_y=None,
                                        padding=[0, 30, 0, 30])

        # Bind / cleanup height on resize
        def resize_scroll(call_widget, grid_layout, anchor_layout, *args):
            call_widget.height = Window.height // 1.85
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
        scroll_top = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.775}, pos=scroll_widget.pos,
                                       size=(scroll_widget.width // 1.5, 60))
        scroll_bottom = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.25}, pos=scroll_widget.pos,
                                          size=(scroll_widget.width // 1.5, -60))

        # Generate buttons on page load
        addon_count = len(self.server.addon.return_single_list())
        very_bold_font = os.path.join(paths.ui_assets, 'fonts', constants.fonts["very-bold"])
        header_content = f"{translate('Installed Add-ons')}  [color=#494977]-[/color]  " + (
            f'[color=#6A6ABA]{translate("No items")}[/color]' if addon_count == 0 else f'[font={very_bold_font}]1[/font] {translate("item")}' if addon_count == 1 else f'[font={very_bold_font}]{addon_count}[/font] {translate("items")}')
        self.header = HeaderText(header_content, '', (0, 0.9), __translate__=(False, True), no_line=True)

        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'
        float_layout.add_widget(self.header)

        # Add blank label to the center, then load self.gen_search_results()
        self.blank_label = Label()
        self.blank_label.text = "Import or Download add-ons below"
        self.blank_label.font_name = os.path.join(paths.ui_assets, 'fonts', constants.fonts['italic'])
        self.blank_label.pos_hint = {"center_x": 0.5, "center_y": 0.55}
        self.blank_label.font_size = sp(24)
        self.blank_label.color = (0.6, 0.6, 1, 0.35)
        float_layout.add_widget(self.blank_label)

        search_function = self.server.addon.filter_addons
        self.search_bar = search_input(return_function=search_function, server_info=None,
                                       pos_hint={"center_x": 0.5, "center_y": 0.845}, allow_empty=True)
        self.page_switcher = PageSwitcher(0, 0, (0.5, 0.86), self.switch_page)

        # Append scroll view items
        scroll_anchor.add_widget(self.scroll_layout)
        scroll_widget.add_widget(scroll_anchor)
        float_layout.add_widget(scroll_widget)
        float_layout.add_widget(scroll_top)
        float_layout.add_widget(scroll_bottom)
        float_layout.add_widget(self.search_bar)
        float_layout.add_widget(self.page_switcher)

        bottom_buttons = RelativeLayout()
        bottom_buttons.size_hint_max_x = 312
        bottom_buttons.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        bottom_buttons.add_widget(MainButton('Import', (0, 0.202), 'download-outline.png', width=300, icon_offset=-115,
                                             auto_adjust_icon=True))
        bottom_buttons.add_widget(
            MainButton('Download', (1, 0.202), 'cloud-download-outline.png', width=300, icon_offset=-115,
                       auto_adjust_icon=True))
        buttons.append(ExitButton('Back', (0.5, -1), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)
        float_layout.add_widget(bottom_buttons)

        menu_name = f"{self.server.name}, Add-ons"
        float_layout.add_widget(generate_title(f"Add-on Manager: '{self.server.name}'"))
        float_layout.add_widget(generate_footer(menu_name))

        # Buttons in the top right corner
        def update_addons(*a):
            utility.screen_manager.current = 'ServerAddonUpdateScreen'

        if addon_count > 0:
            position = (70 if self.server._telepath_data else 125, 110)
            vertical_offset = 0 if self.server._telepath_data else 50
            if not self.server.addon.update_required:
                self.server._view_notif('add-ons', False)
                float_layout.add_widget(
                    IconButton('up to date', {}, position, (None, None), 'checkmark-sharp.png', clickable=False,
                               anchor='right', click_func=update_addons, text_offset=(0, vertical_offset)))
            else:
                self.server._view_notif('add-ons', viewed='update')
                float_layout.add_widget(
                    IconButton('update add-ons', {}, position, (None, None), 'arrow-update.png', clickable=True,
                               anchor='right', click_func=update_addons,
                               force_color=[[(0.05, 0.08, 0.07, 1), (0.5, 0.9, 0.7, 1)], 'green'],
                               text_offset=(12, vertical_offset)))

        if not self.server._telepath_data:
            def open_dir(*a):
                constants.folder_check(self.server.addon.addon_path)
                constants.open_folder(self.server.addon.addon_path)

            float_layout.add_widget(
                IconButton('open directory', {}, (70, 110), (None, None), 'folder.png', anchor='right',
                           click_func=open_dir, text_offset=(10, 0)))

        self.add_widget(float_layout)

        # Add ManuTaskbar
        self.menu_taskbar = MenuTaskbar(selected_item='add-ons')
        self.add_widget(self.menu_taskbar)

        # Automatically generate results (installed add-ons) on page load
        addon_manager = constants.server_manager.current_server.addon
        addon_list = [addon for addon in addon_manager.return_single_list() if not addons.is_geyser_addon(addon)]

        self.gen_search_results(addon_list)

        # Show banner if server is running
        if addon_manager._hash_changed():
            Clock.schedule_once(
                functools.partial(
                    self.show_banner,
                    (0.937, 0.831, 0.62, 1),
                    f"A server restart is required to apply changes",
                    "sync.png",
                    3,
                    {"center_x": 0.5, "center_y": 0.965}
                ), 0
            )

        # Show banner if updates are available
        elif constants.server_manager.current_server.addon.update_required and not constants.server_manager.current_server.addon._update_notified:
            constants.server_manager.current_server.addon._update_notified = True
            Clock.schedule_once(
                functools.partial(
                    self.show_banner,
                    (0.553, 0.902, 0.675, 1),
                    f"Add-on updates are available",
                    "arrow-up-circle-sharp.png",
                    2.5,
                    {"center_x": 0.5, "center_y": 0.965},
                    'popup/notification'
                ), 0
            )


class ServerAddonSearchScreen(MenuBackground):

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
        addon_manager = constants.server_manager.current_server.addon

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

                # Create list of addon names
                installed_addon_names = [addon.name for addon in addon_manager.return_single_list()]

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
                                if not selected_button.properties.versions or not selected_button.properties.description:
                                    new_addon_info = addons.get_addon_info(addon,
                                                                           constants.server_manager.current_server.properties_dict())
                                    selected_button.properties = new_addon_info

                            Clock.schedule_once(functools.partial(selected_button.loading, False), 1)

                            return selected_button.properties, selected_button.installed

                        # Don't crash if add-on failed to load
                        except:
                            Clock.schedule_once(
                                functools.partial(
                                    utility.screen_manager.current_screen.show_banner,
                                    (1, 0.5, 0.65, 1),
                                    f"Failed to load add-on",
                                    "close-circle-sharp.png",
                                    2.5,
                                    {"center_x": 0.5, "center_y": 0.965}
                                ), 0
                            )

                    # Function to install addon
                    def install_addon(index):

                        selected_button = \
                        [item for item in self.scroll_layout.walk() if item.__class__.__name__ == "AddonButton"][
                            index - 1]
                        addon = selected_button.properties
                        selected_button.toggle_installed(not selected_button.installed)

                        if len(addon.name) < 26:
                            addon_name = addon.name
                        else:
                            addon_name = addon.name[:23] + "..."

                        # Install
                        if selected_button.installed:
                            dTimer(0, functools.partial(addon_manager.download_addon, addon)).start()

                            # Show banner if server is running
                            if addon_manager._hash_changed():
                                Clock.schedule_once(
                                    functools.partial(
                                        self.show_banner,
                                        (0.937, 0.831, 0.62, 1),
                                        f"A server restart is required to apply changes",
                                        "sync.png",
                                        3,
                                        {"center_x": 0.5, "center_y": 0.965}
                                    ), 0
                                )

                            else:
                                Clock.schedule_once(
                                    functools.partial(
                                        self.show_banner,
                                        (0.553, 0.902, 0.675, 1),
                                        f"Installed '${addon_name}$'",
                                        "checkmark-circle-sharp.png",
                                        2.5,
                                        {"center_x": 0.5, "center_y": 0.965}
                                    ), 0.25
                                )

                        # Uninstall
                        else:
                            for installed_addon in addon_manager.return_single_list():
                                if installed_addon.name == addon.name:
                                    addon_manager.delete_addon(installed_addon)

                                    # Show banner if server is running
                                    if addon_manager._hash_changed():
                                        Clock.schedule_once(
                                            functools.partial(
                                                self.show_banner,
                                                (0.937, 0.831, 0.62, 1),
                                                f"A server restart is required to apply changes",
                                                "sync.png",
                                                3,
                                                {"center_x": 0.5, "center_y": 0.965}
                                            ), 0
                                        )

                                    else:
                                        Clock.schedule_once(
                                            functools.partial(
                                                self.show_banner,
                                                (1, 0.5, 0.65, 1),
                                                f"'${addon_name}$' was uninstalled",
                                                "trash-sharp.png",
                                                2.5,
                                                {"center_x": 0.5, "center_y": 0.965}
                                            ), 0.25
                                        )

                                    break

                        return addon, selected_button.installed

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
                                installed=addon_object.name in installed_addon_names,
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
        header_content = translate("Add-on Search")
        self.header = HeaderText(header_content, '', (0, 0.89), __translate__=(False, True))

        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'
        float_layout.add_widget(self.header)

        # Add blank label to the center
        self.blank_label = Label()
        self.blank_label.text = "search for add-ons above"
        self.blank_label.font_name = os.path.join(paths.ui_assets, 'fonts', constants.fonts['italic'])
        self.blank_label.pos_hint = {"center_x": 0.5, "center_y": 0.48}
        self.blank_label.font_size = sp(24)
        self.blank_label.color = (0.6, 0.6, 1, 0.35)
        float_layout.add_widget(self.blank_label)

        server_obj = constants.server_manager.current_server
        search_function = server_obj.addon.search_addons
        self.search_bar = search_input(return_function=search_function, server_info=server_obj.properties_dict(),
                                       pos_hint={"center_x": 0.5, "center_y": 0.795})
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

        server_name = constants.server_manager.current_server.name
        menu_name = f"{server_name}, Add-ons, Download"
        float_layout.add_widget(generate_title(f"Add-on Manager: '{server_name}'"))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)

        # Autofocus search bar
        for widget in self.search_bar.children:
            try:
                if widget.id == "search_input":
                    widget.grab_focus()
                    break
            except AttributeError:
                pass


# amscript Manager ------------------------------------------------------------------------------------------------

constants.script_obj = amscript.ScriptObject()


def edit_script(edit_button, server_obj, script_path, download=True):
    "amscript-icon.png"

    # Override to download locally
    telepath_data = None
    telepath_script_dir = paths.telepath_script_temp
    if server_obj._telepath_data:
        telepath_data = constants.deepcopy(server_obj._telepath_data)
        telepath_data['headers'] = constants.api_manager._get_headers(telepath_data['host'], True)
        if download:
            script_path = constants.telepath_download(server_obj._telepath_data, script_path,
                                                      os.path.join(paths.telepath_script_temp,
                                                                   server_obj._telepath_data['host']))

    send_log('edit_script', f"opening in amscript IDE:\n'{script_path}'", 'info')

    # Update Discord rich presence
    constants.discord_presence.update_presence(f"amscript IDE > Editing '{os.path.basename(script_path)}'")

    constants.app_config.load_config()

    # Passed to child IDE window
    data_dict = {
        '_telepath_data': telepath_data,
        'app_title': constants.app_title,
        'ams_version': constants.ams_version,
        'gui_assets': paths.ui_assets,
        'cache_dir': paths.cache,
        'background_color': constants.background_color,
        'app_config': constants.app_config,
        'script_obj': {
            'syntax_func': constants.script_obj.is_valid,
            'protected': constants.script_obj.protected_variables,
            'events': constants.script_obj.valid_events
        },
        'suggestions': server_obj._retrieve_suggestions(),
        'os_name': constants.os_name,
        'translate': translate,
        'telepath_script_dir': telepath_script_dir,
    }

    # Passed to parent IPC receiver
    ipc_functions = {
        'api_manager': constants.api_manager,
        'telepath_upload': constants.telepath_upload,
        'format_traceback': constants.format_traceback,
        '_send_log': logger.send_log
    }

    Clock.schedule_once(functools.partial(amseditor.edit_script, script_path, data_dict, ipc_functions), 0.1)
    if edit_button:
        edit_button.on_leave()
        edit_button.on_release()


class ScriptButton(HoverButton):

    def toggle_installed(self, installed, *args):
        self.installed = installed
        self.install_image.opacity = 1 if installed and not self.show_type else 0
        self.install_label.opacity = 1 if installed and not self.show_type else 0
        self.title.text_size = (self.size_hint_max[0] * (0.7 if installed else 0.94), self.size_hint_max[1])
        self.background_normal = os.path.join(paths.ui_assets,
                                              f'{self.id}{"_installed" if self.installed and not self.show_type else ""}.png')
        self.resize_self()

    def resize_self(self, *args):

        # Title and description
        padding = 2.17
        self.title.pos = (self.x + (self.title.text_size[0] / padding) - (6 if self.installed else 0), self.y + 31)
        self.subtitle.pos = (self.x + (self.subtitle.text_size[0] / padding) - 1, self.y)

        # Install label
        self.install_image.pos = (self.width + self.x - self.install_label.width - 28, self.y + 38.5)
        self.install_label.pos = (self.width + self.x - self.install_label.width - 30, self.y + 5)

        # Type Banner
        if self.show_type:
            self.type_banner.pos_hint = {"center_x": None, "center_y": None}
            self.type_banner.pos = (self.width + self.x - self.type_banner.width - 18, self.y + 38.5)

        # self.version_label.x = self.width+self.x-(self.padding_x[0]*offset)
        # self.version_label.y = self.y-(self.padding_y[0]*0.85)

    def __init__(self, properties, click_function=None, installed=False, show_type=False, fade_in=0.0, **kwargs):
        properties.name = properties.title
        properties.subtitle = properties.description

        super().__init__(**kwargs)

        self.installed = False
        self.show_type = show_type
        self.properties = properties
        self.border = (-5, -5, -5, -5)
        self.color_id = [(0.05, 0.05, 0.1, 1), (0.65, 0.65, 1, 1)]
        self.pos_hint = {"center_x": 0.5, "center_y": 0.6}
        self.size_hint_max = (580, 80)
        self.id = "addon_button"
        self.background_normal = os.path.join(paths.ui_assets, f'{self.id}.png')
        self.background_down = os.path.join(paths.ui_assets, f'{self.id}_click.png')

        # Loading stuffs
        self.original_subtitle = self.properties.subtitle if self.properties.subtitle else "Description unavailable"
        if "\n" in self.original_subtitle:
            self.original_subtitle = self.original_subtitle.split("\n", 1)[0].strip()
        self.original_font = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["regular"]}.ttf')

        # Title of Script
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
        self.title.text = f"{self.properties.name}  [color=#434368]-[/color]  {self.properties.author if self.properties.author else 'Unknown'}"
        self.add_widget(self.title)

        # Description of Script
        self.subtitle = Label()
        self.subtitle.__translate__ = False
        self.subtitle.id = "subtitle"
        self.subtitle.halign = "left"
        self.subtitle.color = self.color_id[1]
        self.subtitle.font_name = self.original_font
        self.subtitle.font_size = sp(21)
        self.subtitle.opacity = 0.56
        self.subtitle.text_size = (self.size_hint_max[0] * 0.91, self.size_hint_max[1])
        self.subtitle.shorten = True
        self.subtitle.shorten_from = "right"
        self.subtitle.max_lines = 1
        self.subtitle.text = self.original_subtitle
        self.add_widget(self.subtitle)

        # Installed layout
        self.install_image = Image()
        self.install_image.size = (110, 30)
        self.install_image.keep_ratio = False
        self.install_image.allow_stretch = True
        self.install_image.source = os.path.join(paths.ui_assets, 'installed.png')
        self.install_image.opacity = 0
        self.add_widget(self.install_image)

        self.install_label = AlignLabel()
        self.install_label.halign = "right"
        self.install_label.valign = "middle"
        self.install_label.font_size = sp(18)
        self.install_label.color = self.color_id[1]
        self.install_label.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
        self.install_label.width = 100
        self.install_label.color = (0.05, 0.08, 0.07, 1)
        self.install_label.text = 'installed'
        self.install_label.opacity = 0
        self.add_widget(self.install_label)

        # Type Banner
        if show_type:
            self.type_banner = show_type
            self.add_widget(self.type_banner)

        # If self.installed is false, and self.properties.version, display version where "installed" logo is
        self.bind(pos=self.resize_self)
        if installed:
            self.toggle_installed(installed)

        # If click_function
        if click_function:
            self.bind(on_press=click_function)

        # Animate opacity
        if fade_in > 0:
            self.opacity = 0
            self.install_label.opacity = 0
            self.install_image.opacity = 0
            self.title.opacity = 0

            Animation(opacity=1, duration=fade_in).start(self)
            Animation(opacity=1, duration=fade_in).start(self.title)
            Animation(opacity=0.56, duration=fade_in).start(self.subtitle)

            if installed and not self.show_type:
                Animation(opacity=1, duration=fade_in).start(self.install_label)
                Animation(opacity=1, duration=fade_in).start(self.install_image)

    def on_enter(self, *args):
        if not self.ignore_hover:
            Animation(color=self.color_id[0], duration=0.06).start(self.title)
            Animation(color=self.color_id[0], duration=0.06).start(self.subtitle)
            animate_button(self, image=os.path.join(paths.ui_assets, f'{self.id}_hover.png'), color=self.color_id[0],
                           hover_action=True)

    def on_leave(self, *args):
        if not self.ignore_hover:
            Animation(color=self.color_id[1], duration=0.06).start(self.title)
            Animation(color=self.color_id[1], duration=0.06).start(self.subtitle)
            animate_button(self, image=os.path.join(paths.ui_assets,
                                                    f'{self.id}{"_installed" if self.installed and not self.show_type else ""}.png'),
                           color=self.color_id[1], hover_action=False)

    def loading(self, load_state, *args):
        if load_state:
            self.subtitle.text = "Loading script info..."
            self.subtitle.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
        else:
            self.subtitle.text = self.original_subtitle
            self.subtitle.font_name = self.original_font


class ScriptListButton(HoverButton):

    def toggle_enabled(self, *args):
        self.title.text_size = (self.size_hint_max[0] * (0.94 if self.enabled else 0.7), self.size_hint_max[1])
        self.background_normal = os.path.join(paths.ui_assets, f'{self.id}{"" if self.enabled else "_disabled"}.png')

        # If disabled, add banner as such
        if not self.enabled:
            self.disabled_banner = BannerObject(
                pos_hint={"center_x": 0.5, "center_y": 0.5},
                size=(125, 32),
                color=(1, 0.53, 0.58, 1),
                text="disabled",
                icon="close-circle.png",
                icon_side="right"
            )
            self.add_widget(self.disabled_banner)

        self.resize_self()

    def resize_self(self, *args):

        # Title and description
        padding = 2.17
        self.title.pos = (
        self.x + (self.title.text_size[0] / padding) - (6 if self.disabled_banner else 0), self.y + 31)
        self.subtitle.pos = (self.x + (self.subtitle.text_size[0] / padding) - 1, self.y)
        self.hover_text.pos = (self.x + (self.size[0] / padding) - 30, self.y + 15)

        # Type Banner
        if self.disabled_banner:
            self.disabled_banner.pos_hint = {"center_x": None, "center_y": None}
            self.disabled_banner.pos = (self.width + self.x - self.disabled_banner.width - 18, self.y + 38.5)

        # Delete button
        self.delete_layout.size_hint_max = (self.size_hint_max[0], self.size_hint_max[1])
        self.delete_layout.pos = (self.pos[0] + self.width - (self.delete_button.width / 1.33), self.pos[1] + 13)

        # Reposition highlight border
        self.highlight_layout.pos = self.pos

    def highlight(self):
        def next_frame(*args):
            Animation.stop_all(self.highlight_border)
            self.highlight_border.opacity = 1
            Animation(opacity=0, duration=0.7).start(self.highlight_border)

        Clock.schedule_once(next_frame, 0)

    def on_enter(self, *args):
        if not self.ignore_hover:

            # Hide disabled banner if it exists
            if self.disabled_banner:
                Animation.stop_all(self.disabled_banner)
                Animation(opacity=0, duration=self.anim_duration).start(self.disabled_banner)

            # Fade button to hover state
            # if not self.delete_button.button.hovered:
            Animation(color=self.color_id[0], duration=(self.anim_duration * 0.5)).start(self.title)
            Animation(color=self.color_id[0], duration=(self.anim_duration * 0.5)).start(self.subtitle)
            animate_button(self, image=os.path.join(paths.ui_assets,
                                                    f'{self.id}_hover_{"dis" if self.enabled else "en"}abled.png'),
                           color=self.color_id[0], hover_action=True)

            # Show delete button
            Animation.stop_all(self.delete_layout)
            Animation(opacity=1, duration=self.anim_duration).start(self.delete_layout)

            # Hide text
            Animation(opacity=0, duration=self.anim_duration).start(self.title)
            Animation(opacity=0, duration=self.anim_duration).start(self.subtitle)
            Animation(opacity=1, duration=self.anim_duration).start(self.hover_text)

    def on_leave(self, *args):
        if not self.ignore_hover:

            # Hide disabled banner if it exists
            if self.disabled_banner:
                Animation.stop_all(self.disabled_banner)
                Animation(opacity=1, duration=self.anim_duration).start(self.disabled_banner)

            # Fade button to default state
            # if not self.delete_button.button.hovered:
            Animation(color=self.color_id[1], duration=(self.anim_duration * 0.5)).start(self.title)
            Animation(color=self.color_id[1], duration=(self.anim_duration * 0.5)).start(self.subtitle)
            animate_button(self,
                           image=os.path.join(paths.ui_assets, f'{self.id}{"" if self.enabled else "_disabled"}.png'),
                           color=self.color_id[1], hover_action=False)

            # Hide delete button
            Animation.stop_all(self.delete_layout)
            Animation(opacity=0, duration=self.anim_duration).start(self.delete_layout)

            # Show text
            Animation(opacity=1, duration=self.anim_duration).start(self.title)
            Animation(opacity=self.default_subtitle_opacity, duration=0.13).start(self.subtitle)
            Animation(opacity=0, duration=self.anim_duration).start(self.hover_text)

    def loading(self, load_state, *args):
        if load_state:
            self.subtitle.text = "Loading script info..."
            self.subtitle.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
        else:
            self.subtitle.text = self.original_subtitle
            self.subtitle.font_name = self.original_font

    def __init__(self, properties, click_function=None, enabled=False, fade_in=0.0, highlight=False, **kwargs):

        properties.name = properties.title
        properties.subtitle = properties.description

        super().__init__(**kwargs)

        self.anim_duration = 0.06
        self.enabled = enabled
        self.properties = properties
        self.border = (-5, -5, -5, -5)
        self.color_id = [(0.05, 0.05, 0.1, 1), (0.65, 0.65, 1, 1)] if self.enabled else [(0.05, 0.1, 0.1, 1),
                                                                                         (1, 0.6, 0.7, 1)]
        self.pos_hint = {"center_x": 0.5, "center_y": 0.6}
        self.size_hint_max = (580, 80)
        self.id = "addon_button"
        self.background_normal = os.path.join(paths.ui_assets, f'{self.id}.png')
        self.background_down = self.background_normal
        self.disabled_banner = None

        if self.enabled:

            # Edit button
            def edit_hover(*args):
                def change_color(*args):
                    if self.hovered:
                        self.hover_text.text = 'EDIT SCRIPT'
                        self.background_normal = os.path.join(paths.ui_assets, "server_button_hover.png")

                Clock.schedule_once(change_color, 0.07)
                Animation.stop_all(self.delete_button)
                Animation(opacity=1, duration=0.25).start(self.delete_button)

            def edit_on_leave(*args):
                def change_color(*args):
                    self.hover_text.text = ('DISABLE SCRIPT' if self.enabled else 'ENABLE SCRIPT')
                    if self.hovered:
                        self.background_normal = os.path.join(paths.ui_assets,
                                                              f'{self.id}_hover_{"dis" if self.enabled else "en"}abled.png')
                        self.background_down = self.background_normal

                Clock.schedule_once(change_color, 0.07)
                Animation.stop_all(self.delete_button)
                Animation(opacity=0.65, duration=0.25).start(self.delete_button)

            def edit_click(*args):
                # Delete addon and reload list
                def reprocess_page(*args):
                    server_obj = constants.server_manager.current_server
                    script_manager = server_obj.script_manager
                    edit_script(self, server_obj, self.properties.path)

                    # Show banner if server is running
                    if script_manager._hash_changed():
                        Clock.schedule_once(
                            functools.partial(
                                utility.screen_manager.current_screen.show_banner,
                                (0.937, 0.831, 0.62, 1),
                                "An amscript reload is required to apply changes",
                                "sync.png",
                                3,
                                {"center_x": 0.5, "center_y": 0.965}
                            ), 0
                        )

                Clock.schedule_once(functools.partial(reprocess_page), 0)

            self.delete_layout = RelativeLayout(opacity=0)
            self.delete_button = IconButton('', {}, (0, 0), (None, None), 'edit-sharp.png', clickable=True,
                                            force_color=[[(0.05, 0.05, 0.1, 1), (0.01, 0.01, 0.01, 1)], ''],
                                            anchor='right', click_func=edit_click)
            self.delete_button.opacity = 0.65
            self.delete_button.button.bind(on_enter=edit_hover)
            self.delete_button.button.bind(on_leave=edit_on_leave)
            self.delete_layout.add_widget(self.delete_button)
            self.add_widget(self.delete_layout)

        else:

            # Delete button
            def delete_hover(*args):
                def change_color(*args):
                    if self.hovered:
                        self.hover_text.text = 'UNINSTALL SCRIPT'
                        self.background_normal = os.path.join(paths.ui_assets, "server_button_favorite_hover.png")

                Clock.schedule_once(change_color, 0.07)
                Animation.stop_all(self.delete_button)
                Animation(opacity=1, duration=0.25).start(self.delete_button)

            def delete_on_leave(*args):
                def change_color(*args):
                    self.hover_text.text = ('DISABLE SCRIPT' if self.enabled else 'ENABLE SCRIPT')
                    if self.hovered:
                        self.background_normal = os.path.join(paths.ui_assets,
                                                              f'{self.id}_hover_{"dis" if self.enabled else "en"}abled.png')
                        self.background_down = self.background_normal

                Clock.schedule_once(change_color, 0.07)
                Animation.stop_all(self.delete_button)
                Animation(opacity=0.65, duration=0.25).start(self.delete_button)

            def delete_click(*args):
                # Delete addon and reload list
                def reprocess_page(*args):
                    script_manager = constants.server_manager.current_server.script_manager
                    script_manager.delete_script(self.properties)
                    constants.clear_script_cache(self.properties.path)
                    script_screen = utility.screen_manager.current_screen
                    new_list = script_manager.return_single_list()
                    script_screen.gen_search_results(new_list, fade_in=True)
                    Clock.schedule_once(functools.partial(script_screen.search_bar.execute_search,
                                                          script_screen.search_bar.previous_search), 0)

                    # Show banner if server is running
                    if script_manager._hash_changed():
                        Clock.schedule_once(
                            functools.partial(
                                utility.screen_manager.current_screen.show_banner,
                                (0.937, 0.831, 0.62, 1),
                                "An amscript reload is required to apply changes",
                                "sync.png",
                                3,
                                {"center_x": 0.5, "center_y": 0.965}
                            ), 0
                        )

                    else:
                        Clock.schedule_once(
                            functools.partial(
                                utility.screen_manager.current_screen.show_banner,
                                (1, 0.5, 0.65, 1),
                                f"'${self.properties.name}$' was uninstalled",
                                "trash-sharp.png",
                                2.5,
                                {"center_x": 0.5, "center_y": 0.965}
                            ), 0
                        )

                    # Switch pages if page is empty
                    if (len(script_screen.scroll_layout.children) == 0) and (len(new_list) > 0):
                        script_screen.switch_page("left")

                Clock.schedule_once(
                    functools.partial(
                        utility.screen_manager.current_screen.show_popup,
                        "warning_query",
                        f'Uninstall ${self.properties.name}$',
                        "Uninstalling this script will render it unavailable for every server.\n\nDo you want to permanently uninstall this script?",
                        (None, functools.partial(reprocess_page))
                    ),
                    0
                )

            self.delete_layout = RelativeLayout(opacity=0)
            self.delete_button = IconButton('', {}, (0, 0), (None, None), 'trash-sharp.png', clickable=True,
                                            force_color=[[(0.05, 0.05, 0.1, 1), (0.01, 0.01, 0.01, 1)], 'pink'],
                                            anchor='right', click_func=delete_click)
            self.delete_button.opacity = 0.65
            self.delete_button.button.bind(on_enter=delete_hover)
            self.delete_button.button.bind(on_leave=delete_on_leave)
            self.delete_layout.add_widget(self.delete_button)
            self.add_widget(self.delete_layout)

        # Hover text
        self.hover_text = Label()
        self.hover_text.id = 'hover_text'
        self.hover_text.size_hint = (None, None)
        self.hover_text.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        self.hover_text.text = ('DISABLE SCRIPT' if self.enabled else 'ENABLE SCRIPT')
        self.hover_text.font_size = sp(23)
        self.hover_text.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["bold"]}.ttf')
        self.hover_text.color = (0.1, 0.1, 0.1, 1)
        self.hover_text.halign = "center"
        self.hover_text.text_size = (self.size_hint_max[0] * 0.94, self.size_hint_max[1])
        self.hover_text.opacity = 0
        self.add_widget(self.hover_text)

        # Loading stuffs
        self.original_subtitle = self.properties.subtitle if self.properties.subtitle else "Description unavailable"
        self.original_font = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["regular"]}.ttf')

        # Title of Script
        self.title = Label()
        self.title.__translate__ = False
        self.title.id = "title"
        self.title.halign = "left"
        self.title.color = self.color_id[1]
        self.title.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
        self.title.font_size = sp(25)
        self.title.text_size = (self.size_hint_max[0] * (0.94), self.size_hint_max[1])
        self.title.shorten = True
        self.title.markup = True
        self.title.shorten_from = "right"
        self.title.max_lines = 1
        self.title.text = f"{self.properties.name}{('  [color=#434368]-[/color]  ' + self.properties.author) if self.properties.author.lower().strip() != 'unknown' else ''}"
        self.add_widget(self.title)
        Clock.schedule_once(self.toggle_enabled, 0)

        # Description of Addon
        self.subtitle = Label()
        self.subtitle.__translate__ = False
        self.subtitle.id = "subtitle"
        self.subtitle.halign = "left"
        self.subtitle.color = self.color_id[1]
        self.subtitle.font_name = self.original_font
        self.subtitle.font_size = sp(21)
        self.default_subtitle_opacity = 0.56
        self.subtitle.opacity = self.default_subtitle_opacity
        self.subtitle.text_size = (self.size_hint_max[0] * 0.91, self.size_hint_max[1])
        self.subtitle.shorten = True
        self.subtitle.shorten_from = "right"
        self.subtitle.max_lines = 1
        self.subtitle.text = self.original_subtitle
        self.add_widget(self.subtitle)

        # Highlight border
        self.highlight_layout = RelativeLayout()
        self.highlight_border = Image()
        self.highlight_border.keep_ratio = False
        self.highlight_border.allow_stretch = True
        self.highlight_border.color = constants.brighten_color(self.color_id[1], 0.1)
        self.highlight_border.opacity = 0
        self.highlight_border.source = os.path.join(paths.ui_assets, 'server_button_highlight.png')
        self.highlight_layout.add_widget(self.highlight_border)
        self.highlight_layout.width = self.size_hint_max[0]
        self.highlight_layout.height = self.size_hint_max[1]
        self.add_widget(self.highlight_layout)

        if highlight:
            self.highlight()

        # If self.enabled is false, and self.properties.version, display version where "enabled" logo is
        self.bind(pos=self.resize_self)
        self.resize_self()

        # If click_function
        if click_function:
            self.bind(on_press=click_function)

        # Animate opacity
        if fade_in > 0:
            self.opacity = 0
            self.title.opacity = 0

            Animation(opacity=1, duration=fade_in).start(self)
            Animation(opacity=1, duration=fade_in).start(self.title)
            Animation(opacity=0.56, duration=fade_in).start(self.subtitle)


class CreateAmscriptScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'
        self.name_input = None
        self.create_button = None

    def generate_menu(self, **kwargs):
        # Generate buttons on page load
        server_obj = constants.server_manager.current_server

        def on_click(*a):
            script_name = self.name_input.convert_name(self.name_input.text)
            script_title = self.name_input.text.strip()

            if server_obj._telepath_data:
                script_path = os.path.join(paths.telepath_script_temp, script_name)
                constants.folder_check(paths.telepath_script_temp)
            else:
                script_path = os.path.join(paths.scripts, script_name)
                constants.folder_check(paths.scripts)

            contents = f"""#!
# title: {script_title}
# author: {constants.username.title()}
# version: 1.0
# description: 
#!



# {translate('Welcome to the amscript IDE!')}
# {translate('Right-click > Help to learn more about the capabilities of amscript')}

@player.on_join(player, message):
    if player not in server.usercache:
        player.log(f"{translate('Welcome to')} {{server}} {{player}}!")
"""

            with open(script_path, 'w+', encoding='utf-8', errors='ignore') as f:
                f.write(contents)

            # Upload and import if it's remote
            if server_obj._telepath_data:
                server_obj.script_manager.import_script(script_path)

            for s in server_obj.script_manager.return_single_list():
                if s.file_name == script_name:
                    server_obj.script_manager.script_state(s, enabled=True)
                    break

            def later(*_):
                edit_script(None, server_obj, script_path, download=False)

            dTimer(1, later).start()

            utility.screen_manager.previous_screen()
            del utility.screen_manager.screen_tree[-1]

            if server_obj.running:
                Clock.schedule_once(
                    functools.partial(
                        self.show_banner,
                        (0.937, 0.831, 0.62, 1),
                        "An amscript reload is required to apply changes",
                        "sync.png",
                        3,
                        {"center_x": 0.5, "center_y": 0.965}
                    ), 0
                )
            else:
                Clock.schedule_once(
                    functools.partial(
                        self.show_banner,
                        (0.553, 0.902, 0.675, 1),
                        f"'{script_name}' has been created",
                        "checkmark-circle-sharp.png",
                        2.5,
                        {"center_x": 0.5, "center_y": 0.965}
                    ), 0
                )

        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'

        float_layout.add_widget(InputLabel(pos_hint={"center_x": 0.5, "center_y": 0.58}))
        float_layout.add_widget(HeaderText("What would you like to name your script?", '', (0, 0.76)))
        self.name_input = ScriptNameInput(pos_hint={"center_x": 0.5, "center_y": 0.5})
        float_layout.add_widget(self.name_input)
        self.name_input.update_script_list(server_obj.script_manager.return_single_list())
        self.create_button = WaitButton('Create in IDE', (0.5, 0.24), 'amscript.png', width=370, icon_offset=-150,
                                        disabled=True, click_func=on_click)
        buttons.append(self.create_button)
        buttons.append(ExitButton('Back', (0.5, 0.14), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)

        menu_name = f"{server_obj.name}, amscript, Create script"
        float_layout.add_widget(generate_title(f"Script Manager: '{server_obj.name}'"))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)
        self.name_input.grab_focus()


class ServerAmscriptScreen(MenuBackground):

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

    def gen_search_results(self, results, new_search=False, fade_in=True, highlight=None, animate_scroll=True,
                           last_scroll=None, *args):

        # Update page counter
        # results = list(sorted(results, key=lambda d: d.name.lower()))
        # Set to proper page on toggle

        script_manager = constants.server_manager.current_server.script_manager
        default_scroll = 1
        if highlight:
            def divide_chunks(l, n):
                final_list = []

                for i in range(0, len(l), n):
                    final_list.append(l[i:i + n])

                return final_list

            for x, l in enumerate(divide_chunks([x.hash for x in results], self.page_size), 1):
                if highlight in l:
                    if self.current_page != x:
                        self.current_page = x

                    # Update scroll when page is bigger than list
                    if Window.height < self.scroll_layout.height * 1.7:
                        default_scroll = 1 - round(l.index(highlight) / len(l), 2)
                        if default_scroll < 0.21:
                            default_scroll = 0
                        if default_scroll > 0.97:
                            default_scroll = 1
                    break

        self.last_results = results
        self.max_pages = (len(results) / self.page_size).__ceil__()
        self.current_page = 1 if self.current_page == 0 or new_search else self.current_page

        self.page_switcher.update_index(self.current_page, self.max_pages)
        page_list = results[(self.page_size * self.current_page) - self.page_size:self.page_size * self.current_page]

        self.scroll_layout.clear_widgets()

        # Animate scrolling
        def set_scroll(*args):
            Animation.stop_all(self.scroll_layout.parent.parent)
            if animate_scroll:
                Animation(scroll_y=default_scroll, duration=0.1).start(self.scroll_layout.parent.parent)
            else:
                self.scroll_layout.parent.parent.scroll_y = default_scroll

        Clock.schedule_once(set_scroll, 0)

        # Generate header
        script_count = len(results)
        enabled_count = len(script_manager.installed_scripts['enabled'])
        disabled_count = len(script_manager.installed_scripts['disabled'])
        very_bold_font = os.path.join(paths.ui_assets, 'fonts', constants.fonts["very-bold"])
        header_content = f"{translate('Installed Scripts')}  [color=#494977]-[/color]  " + (
            f'[color=#6A6ABA]{translate("No items")}[/color]' if script_count == 0 else f'[font={very_bold_font}]1[/font] {translate("item")}' if script_count == 1 else f'[font={very_bold_font}]{enabled_count:,}{("/[color=#FF8793]" + str(disabled_count) + "[/color]") if disabled_count > 0 else ""}[/font] {translate("items")}')

        if script_manager._hash_changed():
            icons = os.path.join(paths.ui_assets, 'fonts', constants.fonts['icons'])
            header_content = f"[color=#EFD49E][font={icons}]y[/font] " + header_content + "[/color]"

        for child in self.header.children:
            if child.id == "text":
                child.text = header_content
                break

        # If there are no scripts, say as much with a label
        if script_count == 0:
            self.blank_label.text = "Import or Download Scripts Below"
            utility.hide_widget(self.blank_label, False)
            self.blank_label.opacity = 0
            Animation(opacity=1, duration=0.2).start(self.blank_label)
            self.max_pages = 0
            self.current_page = 0

        # If there are scripts, display them here
        else:
            utility.hide_widget(self.blank_label, True)

            # Clear and add all scripts
            for x, script_object in enumerate(page_list, 1):

                # Activated when script is clicked
                def toggle_script(index, *args):
                    script = index

                    if len(script.title) < 26:
                        script_name = script.title
                    else:
                        script_name = script.title[:23] + "..."

                    # Toggle script state
                    script_manager.script_state(script, enabled=not script.enabled)
                    self.gen_search_results(script_manager.return_single_list(), fade_in=False, highlight=script.hash,
                                            animate_scroll=True)

                    if constants.server_manager.current_server.script_manager._hash_changed():
                        Clock.schedule_once(
                            functools.partial(
                                self.show_banner,
                                (0.937, 0.831, 0.62, 1),
                                "An amscript reload is required to apply changes",
                                "sync.png",
                                3,
                                {"center_x": 0.5, "center_y": 0.965}
                            ), 0
                        )
                    else:
                        if script.enabled:
                            banner_text = f"'${script_name}$' is now disabled"
                        else:
                            banner_text = f"'${script_name}$' is now enabled"

                        Clock.schedule_once(
                            functools.partial(
                                self.show_banner,
                                (1, 0.5, 0.65, 1) if script.enabled else (0.553, 0.902, 0.675, 1),
                                banner_text,
                                "close-circle-sharp.png" if script.enabled else "checkmark-circle-sharp.png",
                                2.5,
                                {"center_x": 0.5, "center_y": 0.965}
                            ), 0
                        )

                # Script button click function
                self.scroll_layout.add_widget(
                    ScrollItem(
                        widget=ScriptListButton(
                            properties=script_object,
                            enabled=script_object.enabled,
                            fade_in=((x if x <= 8 else 8) / self.anim_speed) if fade_in else 0,
                            highlight=(highlight == script_object.hash),
                            click_function=functools.partial(
                                toggle_script,
                                script_object,
                                x
                            )
                        )
                    )
                )

            self.resize_bind()
            # self.scroll_layout.parent.parent.scroll_y = 1

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'
        self.header = None
        self.scroll_layout = None
        self.blank_label = None
        self.search_bar = None
        self.page_switcher = None
        self.menu_taskbar = None

        self.last_results = []
        self.page_size = 20
        self.current_page = 0
        self.max_pages = 0
        self.anim_speed = 10

        self.server = None
        self.reload_button = None
        self.directory_button = None
        self.path_button = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        super()._on_keyboard_down(keyboard, keycode, text, modifiers)

        # Press arrow keys to switch pages
        if keycode[1] in ['right', 'left'] and self.name == utility.screen_manager.current_screen.name:
            self.switch_page(keycode[1])

    def generate_menu(self, **kwargs):
        self.server = constants.server_manager.current_server

        # Return if no free space
        if disk_popup('ServerViewScreen', telepath_data=self.server._telepath_data):
            return

        # Scroll list
        scroll_widget = ScrollViewWidget(position=(0.5, 0.5))
        scroll_anchor = AnchorLayout()
        self.scroll_layout = GridLayout(cols=1, spacing=15, size_hint_max_x=1250, size_hint_y=None,
                                        padding=[0, 30, 0, 30])

        # Bind / cleanup height on resize
        def resize_scroll(call_widget, grid_layout, anchor_layout, *args):
            call_widget.height = Window.height // 1.85
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
        scroll_top = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.775}, pos=scroll_widget.pos,
                                       size=(scroll_widget.width // 1.5, 60))
        scroll_bottom = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.25}, pos=scroll_widget.pos,
                                          size=(scroll_widget.width // 1.5, -60))

        # Generate buttons on page load
        script_count = len(self.server.script_manager.return_single_list())
        very_bold_font = os.path.join(paths.ui_assets, 'fonts', constants.fonts["very-bold"])
        header_content = f"{translate('Installed Scripts')}  [color=#494977]-[/color]  " + (
            f'[color=#6A6ABA]{translate("No items")}[/color]' if script_count == 0 else f'[font={very_bold_font}]1[/font] {translate("item")}' if script_count == 1 else f'[font={very_bold_font}]{script_count}[/font] {translate("items")}')
        self.header = HeaderText(header_content, '', (0, 0.9), __translate__=(False, True), no_line=True)

        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'
        float_layout.add_widget(self.header)

        # Add blank label to the center, then load self.gen_search_results()
        self.blank_label = Label()
        self.blank_label.text = "Manage scripts below"
        self.blank_label.font_name = os.path.join(paths.ui_assets, 'fonts', constants.fonts['italic'])
        self.blank_label.pos_hint = {"center_x": 0.5, "center_y": 0.55}
        self.blank_label.font_size = sp(24)
        self.blank_label.color = (0.6, 0.6, 1, 0.35)
        float_layout.add_widget(self.blank_label)

        search_function = self.server.script_manager.filter_scripts
        self.search_bar = search_input(return_function=search_function, server_info=None,
                                       pos_hint={"center_x": 0.5, "center_y": 0.845}, allow_empty=True)
        self.page_switcher = PageSwitcher(0, 0, (0.5, 0.86), self.switch_page)

        # Append scroll view items
        scroll_anchor.add_widget(self.scroll_layout)
        scroll_widget.add_widget(scroll_anchor)
        float_layout.add_widget(scroll_widget)
        float_layout.add_widget(scroll_top)
        float_layout.add_widget(scroll_bottom)
        float_layout.add_widget(self.search_bar)
        float_layout.add_widget(self.page_switcher)

        bottom_buttons = RelativeLayout()
        bottom_buttons.size_hint_max_x = 512
        bottom_buttons.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        bottom_buttons.add_widget(MainButton('Import', (0, 0.202), 'download-outline.png', width=245, icon_offset=-115,
                                             auto_adjust_icon=True))
        bottom_buttons.add_widget(
            MainButton('Create New', (0.5, 0.202), '', width=245, icon_offset=-115, auto_adjust_icon=False))
        bottom_buttons.add_widget(
            MainButton('Download', (1, 0.202), 'cloud-download-outline.png', width=245, icon_offset=-115,
                       auto_adjust_icon=True))
        buttons.append(ExitButton('Back', (0.5, -1), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)
        float_layout.add_widget(bottom_buttons)

        menu_name = f"{self.server.name}, amscript"
        float_layout.add_widget(generate_title(f"Script Manager: '{self.server.name}'"))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)

        # Add ManuTaskbar
        self.menu_taskbar = MenuTaskbar(selected_item='amscript')
        self.add_widget(self.menu_taskbar)

        # Buttons in the top right corner
        def open_dir(*a):
            constants.folder_check(paths.scripts)
            constants.open_folder(paths.scripts)

        self.directory_button = IconButton('open directory', {}, (70, 110), (None, None), 'folder.png', anchor='right',
                                           click_func=open_dir, text_offset=(10, 0))
        float_layout.add_widget(self.directory_button)

        if self.server.running:
            def reload_scripts(*a):
                def timer():
                    self.server.reload_scripts()
                    Clock.schedule_once(
                        functools.partial(
                            self.show_banner,
                            (0.553, 0.902, 0.675, 1),
                            f"amscript engine was restarted successfully",
                            "checkmark-circle-sharp.png",
                            2.5,
                            {"center_x": 0.5, "center_y": 0.965}
                        ), 0
                    )
                    Clock.schedule_once(
                        functools.partial(self.gen_search_results, self.server.script_manager.return_single_list()), 0)

                dTimer(0, timer).start()

            self.reload_button = IconButton('reload scripts', {}, (125, 110), (None, None), 'reload-sharp.png',
                                            clickable=self.server.running, anchor='right', click_func=reload_scripts,
                                            text_offset=(10, 50))
            float_layout.add_widget(self.reload_button)

        # Automatically generate results (installed scripts) on page load
        self.gen_search_results(self.server.script_manager.return_single_list())

        # Show banner if server is running
        if constants.server_manager.current_server.script_manager._hash_changed():
            Clock.schedule_once(
                functools.partial(
                    self.show_banner,
                    (0.937, 0.831, 0.62, 1),
                    "An amscript reload is required to apply changes",
                    "sync.png",
                    3,
                    {"center_x": 0.5, "center_y": 0.965}
                ), 0
            )


class ServerAmscriptSearchScreen(MenuBackground):

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
        script_manager = constants.server_manager.current_server.script_manager

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
            script_count = len(results)
            very_bold_font = os.path.join(paths.ui_assets, 'fonts', constants.fonts["very-bold"])
            search_text = self.search_bar.previous_search if (
                        len(self.search_bar.previous_search) <= 25) else self.search_bar.previous_search[:22] + "..."
            if isinstance(search_text, str) and not search_text:
                header_content = f"{translate('Available Scripts')}  [color=#494977]-[/color]  " + (
                    f'[color=#6A6ABA]{translate("No results")}[/color]' if script_count == 0 else f'[font={very_bold_font}]1[/font] {translate("item")}' if script_count == 1 else f'[font={very_bold_font}]{script_count:,}[/font] {translate("items")}')
            else:
                header_content = f"{translate('Search for')} '{search_text}'  [color=#494977]-[/color]  " + (
                    f'[color=#6A6ABA]{translate("No results")}[/color]' if script_count == 0 else f'[font={very_bold_font}]1[/font] {translate("item")}' if script_count == 1 else f'[font={very_bold_font}]{script_count:,}[/font] {translate("items")}')

            for child in self.header.children:
                if child.id == "text":
                    child.text = header_content
                    break

            # If there are no scripts, say as much with a label
            if script_count == 0:
                self.blank_label.text = "there are no items to display"
                utility.hide_widget(self.blank_label, False)
                self.blank_label.opacity = 0
                Animation(opacity=1, duration=0.2).start(self.blank_label)
                self.max_pages = 0
                self.current_page = 0

            # If there are scripts, display them here
            else:
                utility.hide_widget(self.blank_label, True)

                # Clear and add all scripts
                for x, script_object in enumerate(page_list, 1):

                    # Function to install script
                    def install_script(index):

                        selected_button = \
                        [item for item in self.scroll_layout.walk() if item.__class__.__name__ == "ScriptButton"][
                            index - 1]
                        script = selected_button.properties
                        selected_button.toggle_installed(not selected_button.installed)

                        if len(script.name) < 26:
                            script_name = script.name
                        else:
                            script_name = script.name[:23] + "..."

                        # Install
                        if selected_button.installed:
                            dTimer(0, functools.partial(script_manager.download_script, script)).start()
                            # Show banner if server is running
                            if script_manager._hash_changed():
                                Clock.schedule_once(
                                    functools.partial(
                                        self.show_banner,
                                        (0.937, 0.831, 0.62, 1),
                                        "An amscript reload is required to apply changes",
                                        "sync.png",
                                        3,
                                        {"center_x": 0.5, "center_y": 0.965}
                                    ), 0
                                )

                            else:
                                Clock.schedule_once(
                                    functools.partial(
                                        self.show_banner,
                                        (0.553, 0.902, 0.675, 1),
                                        f"Installed '${script_name}$'",
                                        "checkmark-circle-sharp.png",
                                        2.5,
                                        {"center_x": 0.5, "center_y": 0.965}
                                    ), 0.25
                                )

                        # Uninstall
                        else:
                            for installed_script in script_manager.return_single_list():
                                if installed_script.title == script.title:
                                    script_manager.delete_script(installed_script)
                                    constants.clear_script_cache(installed_script.path)

                                    # Show banner if server is running
                                    if script_manager._hash_changed():
                                        Clock.schedule_once(
                                            functools.partial(
                                                self.show_banner,
                                                (0.937, 0.831, 0.62, 1),
                                                "An amscript reload is required to apply changes",
                                                "sync.png",
                                                3,
                                                {"center_x": 0.5, "center_y": 0.965}
                                            ), 0
                                        )

                                    else:
                                        Clock.schedule_once(
                                            functools.partial(
                                                self.show_banner,
                                                (1, 0.5, 0.65, 1),
                                                f"'${script_name}$' was uninstalled",
                                                "trash-sharp.png",
                                                2.5,
                                                {"center_x": 0.5, "center_y": 0.965}
                                            ), 0.25
                                        )

                                    break

                        return script, selected_button.installed

                    # Activated when script is clicked
                    def view_script(script, index, *args):
                        selected_button = \
                        [item for item in self.scroll_layout.walk() if item.__class__.__name__ == "ScriptButton"][
                            index - 1]
                        # selected_button.loading(True)

                        Clock.schedule_once(
                            functools.partial(
                                self.show_popup,
                                "script",
                                " ",
                                " ",
                                (None, functools.partial(install_script, index)),
                                (selected_button.installed, script)
                            ),
                            0
                        )

                    # Add-on button click function
                    self.scroll_layout.add_widget(
                        ScrollItem(
                            widget=ScriptButton(
                                properties=script_object,
                                installed=script_object.installed,
                                fade_in=((x if x <= 8 else 8) / self.anim_speed),
                                click_function=functools.partial(
                                    view_script,
                                    script_object,
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
        server_obj = constants.server_manager.current_server
        script_manager = server_obj.script_manager

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
        script_count = 0
        very_bold_font = os.path.join(paths.ui_assets, 'fonts', constants.fonts["very-bold"])
        header_content = translate("Script Search")
        self.header = HeaderText(header_content, '', (0, 0.89), __translate__=(False, True))

        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'
        float_layout.add_widget(self.header)

        # Add blank label to the center
        self.blank_label = Label()
        self.blank_label.text = "search for scripts above"
        self.blank_label.font_name = os.path.join(paths.ui_assets, 'fonts', constants.fonts['italic'])
        self.blank_label.pos_hint = {"center_x": 0.5, "center_y": 0.48}
        self.blank_label.font_size = sp(24)
        self.blank_label.color = (0.6, 0.6, 1, 0.35)
        float_layout.add_widget(self.blank_label)

        search_function = script_manager.search_scripts
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

        server_name = constants.server_manager.current_server.name
        menu_name = f"{server_name}, amscript, Download"
        float_layout.add_widget(generate_title(f"Script Manager: '{server_name}'"))
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


# Edit Config Screens ------------------------------------------------------------------------------------------------

# Determines the type of config file and open in the proper editor
def open_config_file(path: str, *a):
    config_data = {
        'path': path,
        'remote_path': None,
        '_telepath_data': None
    }

    try:
        server_obj = constants.server_manager.current_server
        ext = path.split('.')[-1]

        # First check if file is compatible
        if ext not in constants.valid_config_formats:
            return False
    except:
        return False

    # If this file is via Telepath, download it first prior to editing
    config_data['_telepath_data'] = server_obj._telepath_data
    if server_obj._telepath_data:
        config_data['remote_path'] = path
        config_data['path'] = constants.telepath_download(server_obj._telepath_data, path)

    # Check if file exits and pick the correct editor for the format
    if config_data['path'] and os.path.isfile(config_data['path']):
        editor_screen = None

        if ext in ['properties', 'ini']:
            editor_screen = 'ServerPropertiesEditScreen'

        elif ext in ['tml', 'toml']:
            editor_screen = 'ServerTomlEditScreen'

        elif ext in ['yml', 'yaml']:
            editor_screen = 'ServerYamlEditScreen'

        elif ext == 'json':
            editor_screen = 'ServerJsonEditScreen'

        elif ext == 'json5':
            editor_screen = 'ServerJson5EditScreen'

        else:
            editor_screen = 'ServerTextEditScreen'

        utility.screen_manager.get_screen(editor_screen).update_path(config_data)
        utility.screen_manager.current = editor_screen

    return False


def save_config_file(data: dict, content: str):
    # Write content to disk
    with open(data['path'], 'w', encoding='utf-8', errors='ignore') as f:
        f.write(content)

    # Upload via Telepath if remote
    if data['_telepath_data'] and data['remote_path']:
        telepath_data = data['_telepath_data']
        upload_path = constants.telepath_upload(telepath_data, data['path'])['path']

        test = constants.api_manager.request(
            endpoint='/main/update_config_file',
            host=telepath_data['host'],
            port=telepath_data['port'],
            args={
                'server_name': constants.server_manager.current_server.name,
                'upload_path': upload_path,
                'destination_path': data['remote_path']
            }
        )


# Controller for ConfigFiles containers
class ConfigFolder(RelativeLayout):

    def __init__(self, path: str, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Internal properties
        self.path = path
        self.files = None
        self.folded = True

        # Widget properties
        self.size_hint_max_y = 50
        self.pos_hint = {'center_y': 1}
        self.color = (0.6, 0.6, 1, 1)
        self.original_opacity = 0.7
        self.hover_delay = 0.1
        self.opacity = self.original_opacity

        # Click behavior
        self.button = HoverButton()
        self.button.opacity = 0
        self.button.y = -15
        self.button.on_enter = self.on_enter
        self.button.on_leave = self.on_leave
        self.button.on_press = self.on_click
        self.add_widget(self.button)

        # Folder icon
        self.icon = Image()
        self.icon.color = self.color
        self.icon.opacity = 1
        self.icon.allow_stretch = True
        self.icon.keep_ratio = False
        self.icon.size_hint_max = (35, 35)
        self.icon.y = 5
        self.icon.source = os.path.join(paths.ui_assets, 'icons', 'folder.png')
        self.add_widget(self.icon)

        # Folder text
        self.text = AlignLabel()
        self.text.__translate__ = False
        self.text.halign = "left"
        self.text.valign = "middle"
        self.text.color = self.color
        self.text.markup = True
        self.text.shorten = True
        self.text.shorten_from = 'left'
        self.text.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
        self.text.text = self.generate_name()
        depth = 1 if self.path.endswith(constants.server_manager.current_server.name) else 2
        text = constants.cross_platform_path(self.path, depth=depth)
        self.text.font_size = sp(25 - (0 if len(text) < 25 else (len(text) // 8)))
        self.text.max_lines = 1
        self.text.x = 55
        self.add_widget(self.text)

    def generate_name(self, color='#555599'):
        depth = 1 if self.path.endswith(constants.server_manager.current_server.name) else 2
        text = constants.cross_platform_path(self.path, depth=depth)
        if '/' in text:
            parent, child = text.rsplit('/', 1)
            return f'[color={color}]{parent}/[/color]{child}'
        elif '\\' in text:
            parent, child = text.rsplit('\\', 1)
            return fr'[color={color}]{parent}\[/color]{child}'
        else:
            return text.strip()

    def toggle_fold(self, fold=True, *a):
        self.folded = fold
        self.files.hide(fold)

        # Capture old scroll data
        screen = utility.screen_manager.current_screen
        old_scroll_ratio = screen.scroll_widget.scroll_y
        old_content_height = screen.scroll_layout.height
        viewport_height = screen.scroll_widget.height

        # Adjust folder height
        new_height = 0 if fold else len(self.files.file_list) * 50
        self.files.size_hint_min_y = new_height

        # Update icon and text
        self.icon.source = os.path.join(paths.ui_assets, 'icons', 'folder.png' if self.folded else 'folder-outline.png')
        Animation(opacity=0.7 if self.folded else 1, duration=0.1).start(self)

        # Force update so the scroll_layout adjusts its height and update scroll position
        def after_layout(*_):
            screen.scroll_anchor.do_layout()
            screen.scroll_layout.do_layout()
            screen.scroll_anchor.size_hint_min_y = screen.scroll_layout.height

            # Convert old pixel offset to the new scroll ratio
            new_content_height = screen.scroll_layout.height
            scrollable = new_content_height - viewport_height
            if scrollable > 0:
                # distance from top in pixels
                old_offset_from_top = (1 - old_scroll_ratio) * (old_content_height - viewport_height)
                new_ratio = 1 - (old_offset_from_top / scrollable)
                new_ratio = min(max(new_ratio, 0), 1)
                screen.scroll_widget.scroll_y = new_ratio

            # No scrolling needed if content < viewport
            else:
                screen.scroll_widget.scroll_y = 1

        Clock.schedule_once(after_layout, -1)

    def on_click(self, *a):

        # Open folder on right-click
        if not constants.server_manager.current_server._telepath_data:
            try:
                if self.button.last_touch.button == 'right':
                    return constants.open_folder(self.path)
            except:
                pass

        self.toggle_fold(not self.folded)

    def on_enter(self):
        Animation.stop_all(self)
        Animation(opacity=1, duration=self.hover_delay / 2).start(self)

    def on_leave(self):
        Animation.stop_all(self)
        Animation(opacity=self.original_opacity if self.folded else 1, duration=self.hover_delay).start(self)


# A container for ConfigFile objects that is controlled by ConfigFolder
class ConfigFiles(GridLayout):
    # A single file representation inside the parent
    class ConfigFile(RelativeLayout):

        def __init__(self, path: str, *args, **kwargs):
            super().__init__(*args, **kwargs)

            # Internal properties
            self.path = path

            # Widget properties
            self.size_hint_min_y = 50
            self.size_hint_max_y = 50
            self.pos_hint = {'center_y': 1}
            self.color = (0.6, 0.6, 1, 1)
            self.original_opacity = 0.5
            self.hover_delay = 0.15
            self.padding = 0

            # Background button
            self.button = HoverButton()
            self.button.opacity = 0
            self.button.y = -15
            self.button.on_enter = self.on_enter
            self.button.on_leave = self.on_leave
            self.button.on_press = self.on_click
            self.button.x = self.padding
            self.add_widget(self.button)

            # File icon
            self.icon = Image()
            self.icon.color = self.color
            self.icon.opacity = self.original_opacity
            self.icon.allow_stretch = True
            self.icon.keep_ratio = False
            self.icon.size_hint_max = (35, 35)
            self.icon.source = os.path.join(paths.ui_assets, 'icons', 'document-text-sharp.png')
            self.icon.y = -5
            self.icon.x = self.padding
            self.add_widget(self.icon)

            # File text
            self.text = AlignLabel()
            self.text.__translate__ = False
            self.text.halign = "left"
            self.text.valign = "bottom"
            self.text.color = self.color
            self.text.opacity = self.original_opacity
            self.text.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["regular"]}.ttf')
            self.text.text = constants.cross_platform_path(self.path)
            self.text.shorten = True
            self.text.shorten_from = 'left'
            self.text.font_size = sp(25 - (0 if len(self.text.text) < 20 else (len(self.text.text) // 8)))
            self.text.max_lines = 1
            self.text.x = 48 + self.padding
            self.add_widget(self.text)

        def resize(self, *a, folder=None):
            self.padding = (10 if Window.width < 900 else 60) - 5
            self.button.x = self.padding
            self.icon.x = self.padding
            self.text.x = 48 + self.padding
            if folder: self.text.size_hint_max_x = (folder.parent.background.size_hint_min_x - self.text.x) / 2.3

        def on_click(self):
            new_color = (0.75, 0.75, 1, 1)
            self.text.color = new_color
            self.icon.color = new_color
            Animation(color=self.color, duration=self.hover_delay).start(self.text)
            Animation(color=self.color, duration=self.hover_delay).start(self.icon)
            Clock.schedule_once(functools.partial(open_config_file, self.path), 0)

        def on_enter(self):
            Animation.stop_all(self.text)
            Animation.stop_all(self.icon)
            Animation(opacity=1, duration=self.hover_delay / 2).start(self.text)
            Animation(opacity=1, duration=self.hover_delay / 2).start(self.icon)

        def on_leave(self):
            Animation.stop_all(self.text)
            Animation.stop_all(self.icon)
            Animation(opacity=self.original_opacity, duration=self.hover_delay).start(self.text)
            Animation(opacity=self.original_opacity, duration=self.hover_delay).start(self.icon)

    def resize_files(self, *a):
        self.folder.parent.background.size_hint_min_x = utility.screen_manager.current_screen.max_width + (
            10 if Window.width < 900 else 60)

        for file in self.children:
            file.resize(folder=self.folder)

        Animation.stop_all(self.folder.parent.background)
        Animation(opacity=(0 if self.folder.folded else 1), duration=0.15).start(self.folder.parent.background)

    # Pretty animation :)
    def hide(self, hide: bool = True):
        utility.hide_widget(self, hide)
        if not hide:
            def animate(c, *a):
                Animation.stop_all(c)
                Animation(opacity=1, duration=0.15).start(c)

            for child in self.children:
                child.opacity = 0
            for x, child in enumerate(reversed(self.children), 1):
                if x > 10:
                    x = 10
                Clock.schedule_once(functools.partial(animate, child), x * 0.03)

    def __init__(self, folder: ConfigFolder, files: list, fold: bool = True, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Internal properties
        self.folder = folder
        self.file_list = files
        folder.files = self

        # Widget properties
        self.pos_hint = {'center_y': 1}
        self.cols = 1
        self.padding = [0, -35.5, 0, 0]

        # Add files to self
        for file in self.file_list:
            self.add_widget(self.ConfigFile(file))

        self.bind(size=self.resize_files, pos=self.resize_files)
        Clock.schedule_once(self.resize_files, 0)
        Clock.schedule_once(functools.partial(self.folder.toggle_fold, fold), 0)


# Abstracted file manager to display folders and config files
class ServerConfigScreen(MenuBackground):
    class Background(RelativeLayout):
        def resize(self, *args):
            self.rectangle1.pos = self.pos
            self.rectangle1.size = self.size
            self.rectangle2.pos = self.pos
            self.rectangle2.size = self.size

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            image = os.path.join(paths.ui_assets, 'head_highlight.png')
            radius = 25

            with self.canvas:
                Color(0, 0, 0.05, 0.12)
                self.rectangle1 = RoundedRectangle(source=image, radius=[radius] * 4)
                self.rectangle2 = RoundedRectangle(radius=[radius] * 4)

            self.bind(pos=self.resize, size=self.resize)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'

        self.filter_text: str = ''
        self.max_width: int = None
        self.server_obj = None
        self.scroll_widget = None
        self.scroll_anchor = None
        self.scroll_layout = None
        self.header = None
        self.search_bar = None
        self.search_label = None
        self.back_button = None
        self._cached = None

    def on_pre_enter(self, *args):
        if self.back_button:
            self.back_button.button.on_leave()
            self.back_button.button.background_normal = os.path.join(paths.ui_assets, 'exit_button.png')
        super().on_pre_enter(*args)

    def filter_files(self, query: str = None):
        self.filter_text = query

        if not query:
            return self.server_obj.config_paths

        # Filter by file name matches
        else:
            filtered = {}
            for folder, files in self.server_obj.config_paths.items():
                for file in files:
                    if query.lower() in constants.cross_platform_path(file).lower():
                        if folder not in filtered:
                            filtered[folder] = []
                        filtered[folder].append(file)

            return filtered

    def gen_search_results(self, results: dict = None, *a):
        if results is None:
            results = self.filter_files()
        else:
            self.scroll_layout.opacity = 0
            self.scroll_layout.clear_widgets()

        if results:

            # Hide "no results"
            if self.search_label.opacity > 0:
                Animation(opacity=0, duration=0.05).start(self.search_label)

            # Create two linked widgets for the folder and the items
            for folder, files in results.items():

                # Create expand filter
                expand_filter = False
                if self.server_obj.config_paths == results:
                    expand_filter = constants.cross_platform_path(folder) != self.server_obj.name

                folder_obj = ConfigFolder(folder)
                files_obj = ConfigFiles(folder_obj, files, expand_filter)

                folder_layout = RelativeLayout(size_hint_min_y=50)
                folder_layout.pos_hint = {'center_y': 1}

                padding = 10
                folder_layout.background = self.Background()
                folder_layout.background.size_hint_min_x = self.max_width + (padding * 2)
                folder_layout.background.pos = (-padding, 11)
                folder_layout.add_widget(folder_layout.background)

                folder_layout.add_widget(folder_obj)

                self.scroll_layout.add_widget(folder_layout)
                self.scroll_layout.add_widget(files_obj)


        # Show "no results"
        else:
            Animation.stop_all(self.search_label)
            self.search_label.text = f"No results for '{self.filter_text}'"
            Animation(opacity=1, duration=0.2).start(self.search_label)

        # Refresh screen
        if self.scroll_layout.opacity < 1:
            def reset_layout(*a):
                Animation.stop_all(self.scroll_layout)
                Animation(opacity=1, duration=0.3).start(self.scroll_layout)

            Clock.schedule_once(reset_layout, 0.1)

    def generate_menu(self, **kwargs):
        self.server_obj = constants.server_manager.current_server
        self.server_obj.reload_config_paths()
        if self.server_obj._telepath_data: self.server_obj._refresh_attr('config_paths')
        file_count = sum(len(files) for files in self.server_obj.config_paths.values())

        # Re-use previously generated widget if the server, file count, and language is the same
        if (self._cached and self._cached['server_obj'] == self.server_obj
                and self._cached['file_count'] == file_count
                and self._cached['locale'] == constants.app_config.locale):
            return self.add_widget(self._cached['layout'])

        # Ignore screen if there are no config paths in the current server
        if not self.server_obj.config_paths:
            if not self.server_obj.reload_config_paths():
                return utility.screen_manager.previous_screen()

        # Scroll list
        self.max_width = 750
        self.scroll_widget = ScrollViewWidget()
        self.scroll_widget.pos_hint = {'center_y': 0.485, 'center_x': 0.5}
        self.scroll_anchor = AnchorLayout()
        self.scroll_layout = GridLayout(
            cols=2,
            spacing=10,
            size_hint_max_x=self.max_width,
            size_hint_y=None,
            padding=[0, 80, 0, 60]
        )

        # Bind / cleanup height on resize
        def resize_scroll(call_widget, grid_layout, anchor_layout, *args):
            call_widget.height = Window.height // 1.5
            grid_layout.cols = 2

            def update_grid(*args):
                anchor_layout.size_hint_min_y = grid_layout.height

            Clock.schedule_once(update_grid, 0)

        self.resize_bind = lambda *_: Clock.schedule_once(
            functools.partial(resize_scroll, self.scroll_widget, self.scroll_layout, self.scroll_anchor), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        self.scroll_layout.bind(minimum_height=self.scroll_layout.setter('height'))
        self.scroll_layout.id = 'scroll_content'

        # Scroll gradient
        scroll_top = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.79}, pos=self.scroll_widget.pos,
                                       size=(self.scroll_widget.width // 1.5, 60))
        scroll_bottom = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.18}, pos=self.scroll_widget.pos,
                                          size=(self.scroll_widget.width // 1.5, -60))

        # Generate buttons on page load
        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'

        # Create header/search bar
        self.header = HeaderText("Select a configuration file to edit", '', (0, 0.9), no_line=True)
        self.search_bar = search_input(return_function=self.filter_files, server_info=None,
                                       pos_hint={"center_x": 0.5, "center_y": 0.84}, allow_empty=True)

        # Lol search label idek
        self.search_label = Label()
        self.search_label.__translate__ = False
        self.search_label.text = ""
        self.search_label.halign = "center"
        self.search_label.valign = "center"
        self.search_label.font_name = os.path.join(paths.ui_assets, 'fonts', constants.fonts['italic'])
        self.search_label.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        self.search_label.font_size = sp(25)
        self.search_label.color = (0.6, 0.6, 1, 0.35)
        float_layout.add_widget(self.search_label)

        # Append scroll view items
        self.scroll_anchor.add_widget(self.scroll_layout)
        self.scroll_widget.add_widget(self.scroll_anchor)
        float_layout.add_widget(self.scroll_widget)
        float_layout.add_widget(scroll_top)
        float_layout.add_widget(scroll_bottom)
        float_layout.add_widget(self.header)
        float_layout.add_widget(self.search_bar)

        self.back_button = ExitButton('Back', (0.5, 0.12), cycle=True)
        buttons.append(self.back_button)

        for button in buttons:
            float_layout.add_widget(button)

        float_layout.add_widget(generate_title(f"Server Settings: '{self.server_obj.name}'"))
        float_layout.add_widget(generate_footer(f"{self.server_obj.name}, Settings, Edit config"))

        self._cached = {
            'server_obj': self.server_obj,
            'locale': constants.app_config.locale,
            'file_count': file_count,
            'layout': float_layout
        }
        self.add_widget(float_layout)

        self.gen_search_results()


# Config file editor
class EditorRoot(MenuBackground):
    # Base functionality for EditorLines
    class EditorLine(RelativeLayout):
        class EditorInput(TextInput):

            class OverflowLabel(RelativeLayout):
                def show(self, show=True):
                    self.opacity = 1 if show else 0
                    self.background.opacity = 1 if show else 0
                    self.text.opacity = 1 if show else 0

                def __init__(self, side='left', *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.size_hint_max_x = 30
                    self.side = side

                    self.background = Image(source=os.path.join(paths.ui_assets, 'scroll_overflow.png'))
                    self.background.color = constants.brighten_color(constants.background_color, -0.1)
                    self.background.allow_stretch = True
                    self.background.keep_ratio = False
                    self.background.size_hint_max_x = (self.size_hint_max_x + 10) * (1 if self.side == 'left' else -1)
                    self.background.x = (0 if self.side == 'left' else self.size_hint_max_x - 5)

                    self.add_widget(self.background)

                    self.text = Label()
                    self.text.text = '…'
                    self.text.color = (0.6, 0.6, 1, 0.6)
                    self.text.markup = True
                    self.text.size_hint_max_x = self.size_hint_max_x
                    self.add_widget(self.text)

                    self.show(False)

            def _update_overflow(self):
                try:
                    if self.text:
                        text_width = self._get_text_width(str(self.text), self.tab_width, self._label_cached)
                        self.scrollable = text_width > self.width

                        if self.scrollable:
                            # Update text properties
                            self.ovf_left.text.font_name = self.ovf_right.text.font_name = os.path.join(paths.ui_assets,
                                                                                                        'fonts',
                                                                                                        f'{constants.fonts["mono-medium"]}.otf')
                            self.ovf_left.text.font_size = self.ovf_right.text.font_size = self.font_size + 6
                            self.ovf_left.height = self.ovf_right.height = self.height

                            # Update positions
                            y_pos = self.y + 7
                            self.ovf_left.pos = (self.x + 3, y_pos)
                            self.ovf_right.pos = (Window.width - self._line.input_padding - 16, y_pos)

                            # Update opacity
                            self.ovf_left.show(self.scroll_x > 0)
                            self.ovf_right.show(self.scroll_x + self.width <= text_width)

                            return

                except AttributeError:
                    pass

                self.scrollable = False
                self.ovf_left.show(False)
                self.ovf_right.show(False)

            def grab_focus(self, *a):
                def focus_later(*args):
                    try:
                        self.focus = True
                    except:
                        return

                Clock.schedule_once(focus_later, 0)

            def on_focus(self, *args):
                try:
                    if self._line.inactive:
                        self.focused = False
                        return
                except:
                    return

                Animation.stop_all(self._line.eq_label)
                Animation(opacity=(1 if self.focused else 0.5), duration=0.15).start(self._line.eq_label)
                try:
                    Animation(opacity=(1 if self.focused or self._line.line_matched else 0.35), duration=0.15).start(
                        self._line.line_number)
                except AttributeError:
                    pass

                if self.focused:
                    # Use 1-based line index
                    self._line._screen.current_line = self._line.line

                    # If there's a function to set the editor's index, pass our 1-based line
                    if self._line.index_func:
                        # The parent's 0-based index + 1 => 1-based
                        self._line.index_func(self._line.index + 1)

                    if self._get_text_width(str(self.text), self.tab_width, self._label_cached) > self.width:
                        self.cursor = (len(self.text), self.cursor[1])
                        self.scroll_x = self._get_text_width(str(self.text), self.tab_width,
                                                             self._label_cached) - self.width + 1
                        Clock.schedule_once(lambda *_: self.do_cursor_movement("cursor_end"), -1)

                        def select_error_handler(*a):
                            try:
                                self.select_text(0)
                            except:
                                pass

                        Clock.schedule_once(select_error_handler, 0.01)
                else:
                    self.do_cursor_movement("cursor_home")
                    self.scroll_x = 0

                self._update_overflow()

            # Type color and prediction
            @staticmethod
            def _input_validation(text: str):

                # Escape newlines and tabs from pasting
                if '\n' in text:
                    text = text.replace('\n', '\\n')
                if '\r' in text:
                    text = text.replace('\r', '\\r')
                if '\t' in text:
                    text = text.replace('\t', '    ')

                return text

            def on_text(self, *args):

                # Update text in memory
                if self._line._data:
                    self._line._data['value'] = self.text

                Animation.stop_all(self)
                Animation.stop_all(self.search)

                self.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["mono-medium"]}.otf')
                self.font_size = dp(25)
                self.foreground_color = (0.408, 0.889, 1, 1)
                self.cursor_color = (0.358, 0.839, 1, 1)
                self.selection_color = (0.308, 0.789, 1, 0.4)

                # Structured data detection
                if self.get_type(self.text) in (list, tuple, dict):
                    self.foreground_color = (0.2, 1, 0.5, 1)
                    self.cursor_color = (0.2, 1, 0.5, 1)
                    self.selection_color = (0.2, 1, 0.5, 0.4)

                # Boolean detection
                elif self.get_type(self.text.lower()) == bool:
                    self.text = self.text.lower()
                    self.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["mono-italic"]}')
                    self.foreground_color = (1, 0.451, 1, 1)
                    self.cursor_color = (1, 0.401, 1, 1)
                    self.selection_color = (0.955, 0.351, 1, 0.4)
                    self.font_size = dp(23.8)

                # Numeric detection (int or float)
                elif self.get_type(self.text) in (float, int):
                    self.foreground_color = (0.989, 0.591, 0.254, 1)
                    self.cursor_color = (0.939, 0.541, 0.254, 1)
                    self.selection_color = (0.889, 0.511, 0.254, 0.4)

                # Plain-text detection
                elif self.get_type(self.text) is None:
                    self.foreground_color = (0.7, 0.7, 1, 1)
                    self.cursor_color = (0.7, 0.7, 1, 1)
                    self.selection_color = (0.7, 0.7, 1, 0.4)

                self.last_color = self.foreground_color
                self.original_text = str(self.text)
                self.search.text = str(self.text)
                self.search.color = self.foreground_color
                self.search.font_size = self.font_size
                self.search.font_name = self.font_name
                self.search.text_size = self.search.size

                if self.search.opacity == 1:
                    self.foreground_color = (0, 0, 0, 0)

                def highlight(*args):
                    self._original_text = self.text
                    try:
                        self._line._screen.check_match(self._line._data, self._line._screen.search_bar.text)
                        self._line.highlight_text(self._line.last_search)
                    except AttributeError:
                        pass

                Clock.schedule_once(highlight, 0)

            def insert_text(self, substring, from_undo=False):

                # Ignore all key presses if search bar is highlighted or not selected line
                # Check 1-based line vs current_line
                if self._line._screen.search_bar.focused or self._line.line != self._line._screen.current_line:
                    self.focused = False
                    return None

                if self._line._screen.popup_widget:
                    return None

                substring = self._input_validation(substring)

                super().insert_text(substring, from_undo=from_undo)

            # Add in special key presses
            def keyboard_on_key_down(self, window, keycode, text, modifiers):
                if self._line._screen.popup_widget:
                    return None

                # Ignore all key presses if search bar is highlighted or not selected line
                if self._line._screen.search_bar.focused or self._line.line != self._line._screen.current_line:
                    self.focused = False
                    return None

                # Ignore undo and redo for global effect
                if (keycode[1] in ['r', 'z', 'y', 'c'] and control in modifiers) or keycode[1] == 'escape':
                    return None

                # Ignore pressing certain keys
                elif (keycode[1] == 'super' and control in modifiers) or (
                        control in modifiers and keycode[1] in ['s', 'f']):
                    pass

                # Undo functionality
                elif (((not modifiers or bool([m for m in modifiers if m not in keycode[1]])) and (
                        text or keycode[1] in ['backspace', 'delete', 'spacebar'])) or
                      (keycode[1] in ['v', 'x'] and control in modifiers) or
                      (keycode[1] == 'backspace' and control in modifiers)):
                    self.undo_func(save=True)

                # Toggle boolean values with space
                def replace_text(val, *args):
                    self.text = val

                if keycode[1] == "spacebar" and self.text == 'true':
                    Clock.schedule_once(functools.partial(replace_text, 'false'), 0)

                elif keycode[1] == "spacebar" and self.text == 'false':
                    Clock.schedule_once(functools.partial(replace_text, 'true'), 0)

                if keycode[1] == "backspace" and control in modifiers:
                    original_index = self.cursor_col
                    new_text, index = constants.control_backspace(self.text, original_index)
                    self.select_text(original_index - index, original_index)
                    self.delete_selection()
                else:
                    super().keyboard_on_key_down(window, keycode, text, modifiers)

                # Process override defined behavior
                override_result = self._line.keyboard_overrides(self, window, keycode, text, modifiers)

                # Fix scrolling issues with text input after text updates
                def fix_scroll(*a):
                    # Fix overscroll (cursor X pos is less than input position
                    if self.cursor_pos[0] < (self.x):
                        self.scroll_x = 0

                    # Fix underscroll (cursor X pos is greater than max width, and cursor is at the end of text)
                    if (self.cursor_pos[0] >= Window.width - self._line.input_padding) and len(self.text) == \
                            self.cursor[0]:
                        self.scroll_x = self._get_text_width(self.text, self.tab_width,
                                                             self._label_cached) - self.width + 12

                    # Update ellipses for content that's off-screen
                    self._update_overflow()

                Clock.schedule_once(fix_scroll, 0)

                if override_result:
                    return override_result

            def scroll_search(self, *a):
                offset = 12
                if self.cursor_offset() - self.width + offset > 0 and self.scroll_x > 0:
                    offset = self.cursor_offset() - self.width + offset
                else:
                    offset = 0

                self.search.x = (self.x + 5.3) - offset

                def highlight(*args):
                    try:
                        self._line.highlight_text(self._line.last_search)
                    except AttributeError:
                        pass

                Clock.schedule_once(highlight, 0)

            def on_touch_down(self, touch):
                if self._line._screen.popup_widget:
                    return
                else:
                    return super().on_touch_down(touch)

            def _update_data(self, data: dict):
                default_value = str(data['value'])
                self.index_func = self._line.index_func
                self.undo_func = self._line.undo_func
                self.get_type = self._line.get_type
                self.eq = self._line.eq_label

                self.text = self._input_validation(default_value)
                self.original_text = str(self.text)

                # This was formerly: self.line = self._line.line_number
                # Renamed to indicate it’s the label widget for the line number
                self.line_number = self._line.line_number

                # Instead of self.index, rely on self._line.index (0-based)
                # Instead of self.line, rely on self._line.line (1-based)

                if self._line.line == self._line._screen.current_line:
                    self.grab_focus()
                else:
                    def unfocus_later(*a):
                        self.focused = False
                        self.do_cursor_movement("cursor_home")
                        self.scroll_x = 0
                        # This seems to have problems with not actually updating when scrolling
                        self._update_overflow()

                    Clock.schedule_once(unfocus_later, 0)

            def __init__(self, line, **kwargs):
                super().__init__(**kwargs)
                self._line = line
                self._line._original_text = ''

                with self.canvas.after:
                    self.search = AlignLabel()
                    self.search.halign = "left"
                    self.search.color = (1, 1, 1, 1)
                    self.search.markup = True
                    self.search.font_name = self.font_name
                    self.search.font_size = self.font_size
                    self.search.text_size = self.search.size
                    self.search.width = 10000
                    self.search.font_kerning = False

                    self.ovf_left = self.OverflowLabel('left')
                    self.ovf_right = self.OverflowLabel('right')

                self.bind(scroll_x=self.scroll_search)
                self.__translate__ = False
                self.font_kerning = False
                self.index_func = None
                self.undo_func = None
                self.get_type = None
                self.text = ''
                self.original_text = ''
                self.multiline = False
                self.background_color = (0, 0, 0, 0)
                self.cursor_width = dp(3)
                self.eq = None
                self.scrollable = False

                # Holds the label widget for the line number, not the numeric index
                self.line_number = None

                self.last_color = (0, 0, 0, 0)
                self.valign = 'center'

                self.bind(text=self.on_text)
                self.bind(focused=self.on_focus)
                Clock.schedule_once(self.on_text, 0)

                self.size_hint_max = (None, None)
                self.size_hint_min_y = 40

        class CommentLabel(AlignLabel, HoverBehavior):
            # Hover stuffies
            def on_enter(self, *args):

                if self.copyable:
                    if '[u]' in self.text and '[/u]' in self.text and self.color_tag not in self.text:
                        self.text = self.text.replace('[u]', f'{self.color_tag}[u]')
                        self.text = self.text.replace('[/u]', '[/u][/color]')

            def on_leave(self, *args):

                if self.copyable:
                    if '[u]' in self.text and '[/u]' in self.text and self.color_tag in self.text:
                        self.text = self.text.replace(f'{self.color_tag}[u]', '[u]')
                        self.text = self.text.replace('[/u][/color]', '[/u]')

            # Normal stuffies
            def on_ref_press(self, *args):
                if not self.disabled:
                    def click(*a):
                        webbrowser.open_new_tab(self.url)

                    Clock.schedule_once(click, 0)

            def ref_text(self, *args):
                if 'http://' in self.text or 'https://' in self.text:
                    self.copyable = True

                    if '[ref=' not in self.text and '[/ref]' not in self.text and self.copyable:
                        self.original_text = self.text
                        url_pattern = r'(https?://[^\s]+)'

                        def replace_url(match):
                            url = match.group(1)
                            self.url = url
                            return f'[u]{url}[/u]'

                        # Use re.sub with the pattern
                        self.text = '[ref=none]' + re.sub(url_pattern, replace_url, self.text, count=1) + '[/ref]'

            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.markup = True
                self.copyable = False
                self.url = None
                self.original_text = ''
                self.color_tag = '[color=#8F8F8F]'
                self.bind(text=self.ref_text)

        def __setattr__(self, attr, value):
            if attr == "data" and value:
                return self._update_data(value)

            super().__setattr__(attr, value)

        def on_index_update(self):
            # Custom behavior when the index is updated
            # self.index is 0-based, so line_number text is index+1 for display
            self.line_number.text = str(self.index + 1)
            self.value_label._line.index = self.index  # Keep input's parent index in sync
            self.line_number.size_hint_max_x = (self.spacing * len(str(self.max_line_count)))

        def on_resize(self, *args):
            self.key_label.size_hint_max = self.key_label.texture_size
            self.eq_label.size_hint_max = self.eq_label.texture_size

            self.key_label.x = self.line_number.x + self.line_number.size_hint_max[0] + (
                        self.spacing * 1.4) + 10 + self.indent_space
            self.eq_label.x = self.key_label.x + self.key_label.size_hint_max[0] + (self.spacing * self.eq_spacing[0])
            self.value_label.x = self.eq_label.x + self.eq_label.size_hint_max[0] + (self.spacing * self.eq_spacing[1])
            self.value_label.y = -6

            # Properly position comments
            if self.is_comment:
                self.key_label.size_hint_max_y = self.eq_label.size_hint_max_y
                self.key_label.size_hint_max_x = Window.width


            # Properly position all other inputs to just before the edge of the screen
            else:
                self.value_label.size_hint_max_x = self.value_label.size_hint_min_x = Window.width - self.value_label.x - self.input_padding
                self.value_label._update_overflow()

            # Properly position search text
            vl = self.value_label
            vl.search.x = vl.x + 6
            vl.search.y = vl.y + (5 if 'italic' in vl.font_name.lower() else 7) + 10

            # Additional cover elements for ghosting or blocking touches
            try:
                self.ghost_cover_left.x = -10
                self.ghost_cover_left.size_hint_max_x = self.value_label.x + 14
                self.ghost_cover_right.x = Window.width - 33
                self.ghost_cover_right.size_hint_max_x = 33
            except AttributeError:
                pass

        def highlight_text(self, text, animate=True, *a):
            # Attempt to highlight text in both key and value for searching.
            self.last_search = text
            self.key_label.text = self.key_label.original_text
            self.line_matched = self._data['line_matched']

            if not animate:
                Animation.stop_all(self.line_number)

            def draw_highlight_box(label, *args):
                label.canvas.before.clear()
                if self.key_label.url:
                    return

                def get_x(lb, ref_x):
                    return lb.center_x - lb.texture_size[0] * 0.5 + ref_x

                def get_y(lb, ref_y):
                    return lb.center_y + lb.texture_size[1] * 0.5 - ref_y

                for name, boxes in label.refs.items():
                    for box in boxes:
                        with label.canvas.before:
                            Color(*self.select_color)
                            Rectangle(pos=(get_x(label, box[0]), get_y(label, box[1])),
                                      size=(box[2] - box[0], box[1] - box[3]))

            text = text.strip()

            if text and not self.key_label.url and self.line_matched:

                # Check if search matches in key label
                if self.line_matched['key']:
                    self.key_label.text = self.line_matched['key']
                else:
                    Clock.schedule_once(functools.partial(draw_highlight_box, self.key_label), 0)

                # Check if search matches in value input/ghost label
                if self.line_matched['value']:
                    self.value_label.search.text = self.line_matched['value']
                else:
                    self.value_label.search.text = self.value_label.text
                    Clock.schedule_once(functools.partial(draw_highlight_box, self.value_label.search), 0)

            # Highlight matches if line matched
            if self.line_matched and self._screen.search_bar.text:
                self.line_number.text = f'[color=#4CFF99]{self.line}[/color]'
                self.line_number.opacity = 1
                self.on_resize()

                Clock.schedule_once(functools.partial(draw_highlight_box, self.value_label.search), 0)
                Clock.schedule_once(functools.partial(draw_highlight_box, self.key_label), 0)

                self.value_label.foreground_color = (0, 0, 0, 0)
                self.value_label.search.opacity = 1

            else:
                # Reset visuals
                self.line_number.text = str(self.line)
                self.line_number.opacity = (1 if self.value_label.focused else 0.35)

                self.value_label.search.opacity = 0
                self.value_label.foreground_color = self.value_label.last_color

                Clock.schedule_once(functools.partial(draw_highlight_box, self.value_label.search), 0)
                Clock.schedule_once(functools.partial(draw_highlight_box, self.key_label), 0)

                self.value_label.search.text = self.value_label.text
                self.key_label.text = self.key_label.original_text

            return self.line_matched

        def _update_data(self, data: dict):

            # Remove all widgets to be added in 'self.render_line'
            self.clear_widgets()

            # First set self.index (0-based), then self.line (1-based)
            idx = self._screen.line_list.index({'data': data})
            self.index = idx
            self.line = idx + 1

            # Add global 'data' parsing here
            self._data = data

            # Render line as defined in override
            self.render_line(data)

            # Internally update the value label
            self.value_label._update_data(data)

            # Update widget sizes
            Clock.schedule_once(self.on_resize, -1)
            Clock.schedule_once(functools.partial(self.highlight_text, self._screen.search_bar.text), -1)

        def __init__(self, *args, **kwargs):
            super().__init__(**kwargs)
            background_color = constants.brighten_color(constants.background_color, -0.1)
            self._screen = utility.screen_manager.current_screen
            self.index_func = self._screen.set_index
            self.undo_func = self._screen.undo

            # Store the 1-based line here
            self.line = None
            # Store the 0-based index here
            self.index = None

            self.last_search = None
            self.font_size = dp(25)
            self.line_matched = False
            self._data = None

            # Overridable attributes
            self.eq_character = '='
            self.eq_spacing = (0.75, 0.75)
            self.indent_space = 0
            self.input_padding = 100

            # Line number
            self.line_number = AlignLabel()
            self.line_number.__translate__ = False
            self.line_number.text = ''
            self.line_number.halign = 'right'
            self.line_number.markup = True
            self.line_number.opacity = 0
            self.line_number.color = (0.7, 0.7, 1, 1)
            self.line_number.pos_hint = {'center_y': 0.7}
            self.line_number.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["mono-medium"]}.otf')
            self.line_number.font_size = self.font_size

            # Read-only key label
            self._key_labels = {'comment': self.CommentLabel(halign='left'), 'normal': Label()}
            self.key_label = self._key_labels['normal']

            # Equals label (for key/value pairs)
            self.eq_label = Label()
            self.eq_label.__translate__ = False
            self.eq_label.halign = 'left'
            self.eq_label.opacity = 0
            self.eq_label.pos_hint = {'center_y': 0.5}

            # Editable value label (EditorInput)
            self.value_label = self.EditorInput(self)

            # Ghost covers for left / right
            self.ghost_cover_left = Image(color=background_color)
            self.ghost_cover_right = Image(color=background_color)

        # Methods available to override
        def configure(self):

            # This method is meant to be overridden to specify configuration options

            self.eq_character = '='
            self.eq_spacing = (0.75, 0.75)

        def render_line(self, data: dict):
            self._data = data
            max_line_count = len(self._screen.line_list)

            # Determines if the line is skip-able when scrolling
            self.is_comment = data['is_comment']
            self.inactive = data['inactive']
            self.line_matched = data['line_matched']
            self._finished_rendering = False
            self._comment_padding = None

            # Defaults
            font_name = 'mono-medium'
            self.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts[font_name]}.otf')
            self.spacing = dp(16)
            self.size_hint_min_y = 50
            self.last_search = ''
            self.line_matched = False
            self.select_color = (0.3, 1, 0.6, 1)
            self.animate = False

            # Line number
            self.line_number.text = str(self.line)
            self.line_number.size_hint_max_x = (self.spacing * len(str(max_line_count)))
            self.line_number.opacity = 0.35

            # Key label
            self.key_label.url = None
            self.key_label.__translate__ = False
            self.key_label.max_lines = 1
            self.key_label.markup = True
            self.key_label.text = ''
            self.key_label.original_text = ''
            self.key_label.font_name = self.font_name
            self.key_label.font_size = self.font_size
            self.key_label.default_color = "#5E6BFF"
            self.key_label.color = self.key_label.default_color
            self.key_label.size_hint_max_y = 50
            self.key_label.pos_hint = {'center_y': 0.5}
            self.key_label.text_size[0] = 0
            self.key_label.opacity = 1

            # Show eq character
            self.eq_label.text = self.eq_character
            self.eq_label.font_name = self.font_name
            self.eq_label.font_size = self.font_size
            self.eq_label.color = (0, 0, 0, 0)
            self.eq_label.opacity = 0.5
            self.eq_label.pos_hint = {'center_y': 0.5}

            # Re-add all widgets in order of Z layer (bottom to top)
            self.add_widget(self.value_label)

            # Ghost covers for left / right
            self.add_widget(self.ghost_cover_left)
            self.add_widget(self.ghost_cover_right)

            # Add remaining widgets
            self.add_widget(self.eq_label)
            self.add_widget(self.line_number)
            self.add_widget(self.key_label)

        @staticmethod
        def get_type(value: str):
            data_type = str

            # Define custom behavior for determining data types

            # Structured data detection
            if ((value.strip().startswith('{') and value.strip().endswith('}'))
                    or (value.strip().startswith('[') and value.strip().endswith(']'))
                    or (value.strip().startswith('(') and value.strip().endswith(')'))):
                data_type = dict

            # Boolean detection
            elif value.lower() in ['true', 'false']:
                data_type = bool

            # Numeric detection (int or float)
            elif value.replace(".", "").replace("-", "").isdigit():
                data_type = float

            return data_type

        @staticmethod
        def keyboard_overrides(self, window, keycode, text, modifiers):

            # Define more keyboard processing behavior for input

            pass

    # Search bar for editor content
    class SearchInput(TextInput):

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self._screen = utility.screen_manager.current_screen

            self.original_text = ''
            self.history_index = 0

            self.size_hint_max_y = 50
            self.multiline = False
            self.halign = "left"
            self.hint_text = "search for text..."
            self.hint_text_color = (0.6, 0.6, 1, 0.4)
            self.foreground_color = (0.6, 0.6, 1, 1)
            self.background_color = (0, 0, 0, 0)
            self.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["mono-bold"]}.otf')
            self.font_size = sp(24)
            self.padding_y = (12, 12)
            self.padding_x = (70, 12)
            self.cursor_color = (0.55, 0.55, 1, 1)
            self.cursor_width = dp(3)
            self.selection_color = (0.5, 0.5, 1, 0.4)

            self.bind(on_text_validate=self.on_enter)

        def _on_focus(self, instance, value, *largs):
            def update_focus(*args):
                self._screen._input_focused = self.focus

            Clock.schedule_once(update_focus, 0)

            super(type(self), self)._on_focus(instance, value)
            Animation.stop_all(self.parent.input_background)
            Animation(opacity=0.9 if self.focus else 0.35, duration=0.2, step=0).start(self.parent.input_background)

        def grab_focus(self, *a):
            def focus_later(*args):
                self.focus = True

            Clock.schedule_once(focus_later, 0)

        def on_enter(self, value):
            self.grab_focus()

        def insert_text(self, substring, from_undo=False):
            if self._screen.popup_widget:
                return None
            substring = substring.replace("\n", "").replace("\r", "")
            return super().insert_text(substring, from_undo=from_undo)

        def keyboard_on_key_down(self, window, keycode, text, modifiers):
            if self.parent.popup_widget:
                return None

            if keycode[1] == 'escape' and self.focused:
                self.focused = False
                if self.parent:
                    self.parent.focus_input()
                return True

            if keycode[1] in ['r', 'z', 'y'] and control in modifiers:
                return None

            if keycode[1] == "backspace" and control in modifiers:
                original_index = self.cursor_col
                new_text, idx = constants.control_backspace(self.text, original_index)
                self.select_text(original_index - idx, original_index)
                self.delete_selection()
            else:
                super().keyboard_on_key_down(window, keycode, text, modifiers)

            # Fix overscroll
            if self.cursor_pos[0] > (self.x + self.width) - (self.width * 0.05):
                self.scroll_x += self.cursor_pos[0] - ((self.x + self.width) - (self.width * 0.05))

            if self.cursor_pos[0] < (self.x):
                self.scroll_x = 0

        def fix_overscroll(self, *args):
            if self.cursor_pos[0] < (self.x):
                self.scroll_x = 0

        def on_touch_down(self, touch):
            if self._screen.popup_widget:
                return
            else:
                return super().on_touch_down(touch)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'

        self._config_data = None
        self.path = None
        self.file_name = None

        self.server_obj = None
        self.header = None
        self.search_bar = None
        self.scroll_widget = None
        self.scroll_layout = None
        self.input_background = None
        self.fullscreen_shadow = None
        self.match_label = None
        self.controls_button = None

        self.undo_history = []
        self.redo_history = []
        self.last_search = ''
        self.match_list = []
        self.modified = False

        # EditorRoot.current_line is now consistently 1-based
        self.current_line = None

        self.line_list = []

        self.background_color = constants.brighten_color(constants.background_color, -0.1)

        # Background
        with self.canvas.before:
            self.color = Color(*self.background_color, mode='rgba')
            self.rect = Rectangle(pos=self.pos, size=self.size)

    # Update current file loaded in editor
    def update_path(self, data: dict):
        self._config_data = data
        self.path = self._config_data['path']
        self.file_name = os.path.basename(self.path)

    # Set current line as 1-based index
    def set_index(self, index, **kwargs):
        self.current_line = index

    # Highlight specific input
    def focus_input(self, new_input=None, highlight=False, force_end=True, grab_focus=False):
        if not new_input:
            if self.current_line:
                return self.scroll_to_line(self.current_line, highlight=highlight, grab_focus=grab_focus)
            else:
                return None

        if highlight:
            original_color = constants.convert_color(new_input.key_label.default_color)['rgb']
            new_input.key_label.color = constants.brighten_color(original_color, 0.2)
            Animation.stop_all(new_input.key_label)
            Animation(color=original_color, duration=0.5).start(new_input.key_label)

        if grab_focus:
            new_input.value_label.grab_focus()

        # Force cursor to the end of the line
        if force_end:
            Clock.schedule_once(lambda *_: new_input.value_label.do_cursor_movement('cursor_end', True), 0)

        self.set_index(new_input.line)

    # Scroll to any line in RecycleView
    def scroll_to_line(self, index: int, highlight=False, wrap_around=False, select=True, grab_focus=False):
        Animation.stop_all(self.scroll_widget, 'scroll_y')
        line_height = 50
        padding_lines = 5
        total_lines = len(self.line_list)
        content_height = total_lines * line_height
        viewport_height = self.scroll_widget.height - self.search_bar.height - self.header.height

        # If the content is smaller than or equal to the viewport, don't scroll.
        if content_height <= viewport_height:
            new_scroll_y = 1
        else:
            max_offset = content_height - viewport_height

            # Compute the top (in pixels) of the target line in the full content.
            target_line_top = (index - 1) * line_height

            # Set how many lines you want as padding.
            padding_pixels = padding_lines * line_height

            # Determine where in the viewport the target line should appear.
            # We choose a position opposite to the direction of travel:
            # - If scrolling downward (new index > current), position the target line
            #   near the bottom so that the extra padding appears above it.
            # - If scrolling upward (new index < current), position it near the top,
            #   leaving extra space (padding) below it.
            if self.current_line is not None:
                if index > self.current_line:
                    # Scrolling downward: target line should appear near the bottom.
                    desired_y = viewport_height - padding_pixels
                elif index < self.current_line:
                    # Scrolling upward: target line should appear near the top.
                    desired_y = padding_pixels
                else:
                    desired_y = viewport_height / 2
            else:
                desired_y = viewport_height / 2

            # Compute the new scroll offset (in pixels) so that the target line’s
            # position in the viewport becomes the desired_y value.
            target_offset = target_line_top - desired_y

            # Clamp to valid scroll range.
            target_offset = max(0, min(target_offset, max_offset))
            new_scroll_y = 1 - (target_offset / max_offset)

        def after_scroll(*a):
            [self.focus_input(line, highlight, True, grab_focus) for line in self.scroll_layout.children if
             line.line == index]

            # If a search term is active, update highlights.
            if self.search_bar.text:
                Clock.schedule_once(lambda *_: [line.highlight_text(self.search_bar.text, False) for line in
                                                self.scroll_layout.children], 0)

        # Only scroll when there is a scrollbar (i.e. not all lines are generated).
        if len(self.scroll_layout.children) < total_lines:
            if select:
                Animation(scroll_y=new_scroll_y, duration=0.1).start(self.scroll_widget)
                Clock.schedule_once(after_scroll, 0.4 if wrap_around else 0.11)
            else:
                self.scroll_widget.scroll_y = new_scroll_y
                self.set_index(index)
        else:
            if select:
                after_scroll()

    # Move between inputs with arrow keys
    def switch_input(self, position):
        if self.current_line is None:
            # Default to line 1 if current_line is unset
            self.set_index(1)

        found_input = False
        wrap_around = False

        # Keep the original increments to preserve user’s existing navigation behavior
        index = 0
        if position == 'up':
            index = self.current_line - 2
        elif position == 'down':
            index = self.current_line
        elif position in ['pagedown', 'end']:
            position = 'pagedown'
            index = len(self.line_list) - 1
        elif position in ['pageup', 'home']:
            position = 'pageup'
            index = 0

        # Loop until full circle or input is found
        attempts = 0
        while not found_input and attempts <= len(self.line_list):
            if index >= len(self.line_list):
                index = 0
                wrap_around = True
            elif index < 0:
                index = len(self.line_list) - 1
                wrap_around = True

            new_input = self.line_list[index]['data']
            ignore_input = False
            if not new_input['inactive']:

                if self.match_list and self.last_search:
                    if not new_input['line_matched']:
                        ignore_input = True

                if not ignore_input:
                    try:
                        # scroll_to_line expects a 1-based index
                        self.scroll_to_line(index + 1, wrap_around=wrap_around, grab_focus=True)
                        break
                    except AttributeError:
                        pass

            if 'up' in position:
                index = index - 1
            else:
                index = index + 1

            attempts += 1

    # Generate search in background
    @staticmethod
    def _check_match_logic(data: dict, search_text: str):
        # Override logic here to parse search matches with delimiters like ":" or "=" differently

        key_text = ''
        value_text = ''

        return key_text, value_text

    def check_match(self, data: dict, search_text: str):
        line_matched = False
        key_matched = False
        value_matched = False

        if search_text:
            search_text = kivy.utils.escape_markup(search_text.strip())

            # Detect different types of key/value pairs
            key_text, value_text = self._check_match_logic(data, search_text)

            key_data = kivy.utils.escape_markup(str(data['key']))
            value_data = kivy.utils.escape_markup(str(data['value']))

            # Check if search matches in key label
            if search_text in key_data:
                key_matched = f'[color=#000000][ref=0]{search_text}[/ref][/color]'.join(
                    [x for x in key_data.split(search_text)])
            elif key_text and key_data.endswith(key_text) and value_text.startswith(value_text):
                key_matched = f'[color=#000000][ref=0]{key_text}[/ref][/color]'.join(
                    [x for x in key_data.rsplit(key_text, 1)])

            # Check if search matches in value input/ghost label
            if search_text in value_data:
                value_matched = f'[color=#000000][ref=0]{search_text}[/ref][/color]'.join(
                    [x for x in value_data.split(search_text)])
            elif value_text and value_data.startswith(value_text) and key_data.endswith(key_text):
                value_matched = f'[color=#000000][ref=0]{value_text}[/ref][/color]'.join(
                    [x for x in value_data.split(value_text, 1)])

            if key_matched or value_matched:
                line_matched = {'key': key_matched, 'value': value_matched}

        data['line_matched'] = line_matched
        return line_matched

    def search_text(self, obj, text, *args):
        self.last_search = text
        self.match_list = []
        first_match = None

        # Update search data in background
        for x, line in enumerate(self.line_list):
            result = self.check_match(line['data'], text)
            if result:
                self.match_list.append(line)
            if result and not first_match:
                first_match = line

        # Update all visible widgets
        if not text:
            self.scroll_widget.refresh_from_data()

        for line in self.scroll_layout.children:
            Clock.schedule_once(functools.partial(line.highlight_text, text), -1)

        # Scroll to first match
        if first_match:
            index = self.line_list.index(first_match)
            # scroll_to_line expects 1-based
            self.scroll_to_line(index + 1, select=False, grab_focus=True)

        # Dirty hack to force focus to search bar
        for x in range(30):
            Clock.schedule_once(self.search_bar.grab_focus, 0.01 * x)

        # Show match count
        try:
            Animation.stop_all(self.match_label)
            Animation(opacity=(1 if text and self.match_list else 0.35 if text else 0), duration=0.1).start(
                self.match_label)
            matches = 0
            search_str = text.strip()
            if search_str:
                for x in self.match_list:
                    total_str = str(x['data']['key']) + str(x['data']['value'])
                    matches += total_str.count(search_str)
            self.match_label.text = f'{matches} match{"es" if matches != 1 else ""}'
        except AttributeError:
            pass

    # Undo/redo behavior
    def _apply_action(self, action, undo=True):
        """
        Called to undo or redo a structural action:
          - 'insert_line': remove or re-insert
          - 'remove_line': re-insert or remove
        """
        a_type = action['type']
        line_data = action['data']  # either the dict or the (key,value,...) tuple
        idx = action['index']

        if a_type == 'insert_line':
            if undo:
                # Undo an insert => remove it
                self.remove_line(idx, refresh=True)
                self.scroll_to_line(idx, grab_focus=True)
            else:
                # Redo an insert => put it back
                self.insert_line(line_data, idx, refresh=True)
                self.scroll_to_line(idx + 1, highlight=True, grab_focus=True)

        elif a_type == 'remove_line':
            if undo:
                # Undo a remove => re-insert it
                self.insert_line(line_data, idx, refresh=True)
                self.scroll_to_line(idx + 1, highlight=True, grab_focus=True)
            else:
                # Redo a remove => remove again
                self.remove_line(idx, refresh=True)
                self.scroll_to_line(idx, grab_focus=True)

    def undo(self, save=False, undo=False, action=None):
        """
        Handles both structural (insert/remove line) and text changes,
        with exactly the one-step-per-line logic you had before.

        - `save=True, action=...` => record a *structural* action
        - `save=True, action=None` => record a *text-change* action
        - `undo=True` => perform undo
        - `undo=False` => perform redo
        """

        # 1) Save a *structural* action
        if save and action is not None:
            self.redo_history.clear()
            self.undo_history.append(action)
            return

        # 2) Save a *text-change* action
        if save and action is None:
            self.redo_history.clear()
            if self.current_line is not None and 1 <= self.current_line <= len(self.line_list):

                # We already store EditorRoot.current_line as 1-based
                line_num = self.current_line

                # Grab the current line's "original_value" from the data
                old_text = self.line_list[line_num - 1]['data']['original_value']

                # If the last undo entry is text for the *same line*, update it
                if self.undo_history and not isinstance(self.undo_history[-1], dict):
                    last = self.undo_history[-1]  # e.g. (line_num, old_text)
                    if last[0] == line_num:
                        # "Update existing action"
                        self.undo_history[-1] = (line_num, old_text)
                        return

                # Otherwise, create a new text-based action
                self.undo_history.append((line_num, old_text))

            return

        # 3) Actually perform Undo or Redo
        if undo:
            # UNDO
            if not self.undo_history:
                return
            last_action = self.undo_history.pop()

            if isinstance(last_action, dict):
                # structural
                self._apply_action(last_action, undo=True)
                self.redo_history.append(last_action)
            else:
                # text-based => (line_num, old_text)
                line_num, old_text = last_action
                if 1 <= line_num <= len(self.line_list):
                    # Before reverting, store the current text for Redo
                    current_text = self.line_list[line_num - 1]['data']['value']
                    self.redo_history.append((line_num, current_text))

                    # Revert to old_text in the data
                    self.line_list[line_num - 1]['data']['value'] = old_text

                    # Also revert 'original_value' if you want it fully consistent:
                    self.line_list[line_num - 1]['data']['original_value'] = old_text

                    # Refresh the RecycleView so the UI sees the change
                    self.scroll_widget.data = self.line_list
                    self.scroll_widget.refresh_from_data()

                    # Optionally scroll/focus that line
                    self.scroll_to_line(line_num, highlight=True, grab_focus=True)

        else:
            # REDO
            if not self.redo_history:
                return
            last_action = self.redo_history.pop()

            if isinstance(last_action, dict):
                # structural
                self._apply_action(last_action, undo=False)
                self.undo_history.append(last_action)
            else:
                # text-based => (line_num, old_text)
                line_num, old_text = last_action
                if 1 <= line_num <= len(self.line_list):
                    # store the current text in Undo before overwriting
                    current_text = self.line_list[line_num - 1]['data']['value']
                    self.undo_history.append((line_num, current_text))

                    # revert data
                    self.line_list[line_num - 1]['data']['value'] = old_text
                    self.line_list[line_num - 1]['data']['original_value'] = old_text

                    # refresh
                    self.scroll_widget.data = self.line_list
                    self.scroll_widget.refresh_from_data()
                    self.scroll_to_line(line_num, highlight=True, grab_focus=True)

    def _refresh_viewport(self):
        # Force refresh of all data in the viewport
        self.scroll_widget.data = self.line_list
        self.scroll_widget.refresh_from_data()

        # If the content is smaller than or equal to the viewport, don't allow overscroll
        total_lines = len(self.line_list)
        content_height = total_lines * 50
        viewport_height = self.scroll_widget.height - self.search_bar.height
        self.scroll_widget.always_overscroll = content_height > viewport_height

    # Line behavior
    def insert_line(self, data: (tuple, list, dict), index: int = None, refresh=True):

        # Override data parsing in child editors for specific line formats
        if 'data' not in data:
            data = {'data': data}

        if index is not None:
            self.line_list.insert(index, data)

        else:
            self.line_list.append(data)

        # Update layout with new data
        if refresh:
            self.current_line = None

            for line in self.scroll_layout.children:
                line.value_label.focused = False

            self._refresh_viewport()

        return data

    def remove_line(self, index: int, refresh=True):
        if index in range(len(self.line_list)):
            self.current_line = None

            for line in self.scroll_layout.children:
                line.value_label.focused = False

            data = self.line_list.pop(index)

            # Update layout with new data
            if refresh:
                self._refresh_viewport()

            return data

    # Load/save behavior
    def load_file(self):

        # Overrides need to open and read 'self.path' and parse it into a data structure for 'self.lines'

        self.line_list = []

        for line in self.read_from_disk():
            line = line.rstrip()

            data = {
                'key': '',
                'value': line,
                'original_value': line,
                'is_comment': False,
                'inactive': False,
                'line_matched': False
            }

            self.insert_line(data, refresh=False)

        return self.line_list

    def save_file(self):

        # Overrides need to convert 'self.lines' back to a multi-line string, and pass it into 'self.write_to_disk()'

        final_content = ''

        for line in self.line_list:
            line = line['data']
            key_str = ''
            val_str = str(line['value']).strip()

            final_content += str(f"{key_str}{val_str}".rstrip() + '\n')

        self.write_to_disk(final_content)

    def read_from_disk(self) -> list:
        with open(self.path, 'r', encoding='utf-8') as f:
            content = f.read().strip('\r\n')
            content = content.replace(r'\n', '\\n').replace(r'\r', '\\r')
            return content.splitlines()

    def write_to_disk(self, content: str):
        try:
            save_config_file(self._config_data, content)
        except Exception as e:
            send_log(self.__class__.__name__, f"error saving '{self.path}': {constants.format_traceback(e)}", 'error')
            return False

        def set_banner(*a):
            self.set_banner_status(False)

        Clock.schedule_once(set_banner, 0)

        if self.server_obj.running:
            Clock.schedule_once(
                functools.partial(
                    utility.screen_manager.current_screen.show_banner,
                    (0.937, 0.831, 0.62, 1),
                    f"A server restart is required to apply changes",
                    "sync.png",
                    3,
                    {"center_x": 0.5, "center_y": 0.965}
                ), 0
            )
        else:
            Clock.schedule_once(
                functools.partial(
                    utility.screen_manager.current_screen.show_banner,
                    (0.553, 0.902, 0.675, 1),
                    f"'${self.file_name}$' was saved successfully",
                    "checkmark-circle-sharp.png",
                    2.5,
                    {"center_x": 0.5, "center_y": 0.965}
                ), 0
            )

    # Menu navigation
    def quit_to_menu(self, *a):
        for button in self.walk():
            try:
                if button.id == "exit_button":
                    button.force_click()
                    break
            except AttributeError:
                continue

    def save_and_quit(self, *a):
        self.save_file()
        self.quit_to_menu()

    def reset_data(self):
        self.load_file()
        self.set_banner_status(False)

    def check_data(self):
        return not self.undo_history

    def set_banner_status(self, changed=False):
        if changed != self.modified:
            self.remove_widget(self.header)
            del self.header

            if changed:
                self.header = BannerObject(
                    pos_hint={"center_x": 0.5, "center_y": 0.9},
                    size=(250, 40),
                    color="#F3ED61",
                    text=f"Editing '${self.file_name}$'",
                    icon="pencil-sharp.png",
                    animate=True
                )
                self.add_widget(self.header)
            else:
                self.header = BannerObject(
                    pos_hint={"center_x": 0.5, "center_y": 0.9},
                    size=(250, 40),
                    color=(0.4, 0.682, 1, 1),
                    text=f"Viewing '${self.file_name}$'",
                    icon="eye-outline.png",
                    animate=True
                )
                self.add_widget(self.header)

        self.modified = changed

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):

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
                            Clock.schedule_once(
                                functools.partial(self.popup_widget.window_input.do_cursor_movement, 'cursor_right',
                                                  True), 0)

                    new_str = self.popup_widget.window_input.keyboard.keycode_to_string(keycode[0])
                    if 'shift' in modifiers:
                        new_str = new_str.upper()
                    if len(new_str) == 1:
                        insert_text(new_str)
                    elif keycode[1] == 'spacebar':
                        insert_text(' ')
                    self.popup_widget.resize_window()
                else:
                    self.popup_widget.resize_window()
                return True

            if keycode[1] in ['escape', 'n']:
                try:
                    self.popup_widget.click_event(self.popup_widget, 'no')
                except AttributeError:
                    self.popup_widget.click_event(self.popup_widget, 'ok')

            elif keycode[1] in ['enter', 'return', 'y']:
                try:
                    self.popup_widget.click_event(self.popup_widget, 'yes')
                except AttributeError:
                    self.popup_widget.click_event(self.popup_widget, 'ok')
            return

        if (keycode[1] == 'q' and control in modifiers) or keycode[1] == 'escape':
            if self.modified:
                self.show_popup(
                    "query",
                    "Unsaved Changes",
                    f"There are unsaved changes in '${self.file_name}$'.\n\nWould you like to save before quitting?",
                    [functools.partial(Clock.schedule_once, self.quit_to_menu, 0.25),
                     functools.partial(Clock.schedule_once, self.save_and_quit, 0.25)]
                )
            else:
                self.quit_to_menu()
            return True

        if keycode[1] in ['down', 'up', 'pagedown', 'pageup']:
            return self.switch_input(keycode[1])

        if keycode[1] == 'f' and control in modifiers:
            if not self.search_bar.focused:
                self.search_bar.grab_focus()
            else:
                if self.current_line is not None:
                    self.focus_input()
            return True

        if keycode[1] == 's' and control in modifiers and self.modified:
            self.save_file()
            return None

        # Undo/Redo
        if keycode[1] == 'z' and control in modifiers and self.undo_history:
            self.undo(save=False, undo=True)
        elif keycode[1] == 'z' and control in modifiers and not self.undo_history:
            if not self.check_data():
                self.reset_data()

        if keycode[1] in ['r', 'y'] and control in modifiers and self.redo_history:
            self.undo(save=False, undo=False)

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

        def set_banner(*a):
            self.set_banner_status(not self.check_data())

        Clock.schedule_once(set_banner, 0)

        return True

    def generate_menu(self, **kwargs):
        self.server_obj = constants.server_manager.current_server

        # Editor UI
        self.scroll_widget = RecycleViewWidget(position=(0.5, 0.5), view_class=self.EditorLine)
        self.scroll_widget.always_overscroll = False
        self.scroll_layout = RecycleGridLayout(cols=1, size_hint_max_x=1250, size_hint_y=None, padding=[10, 30, 0, 30],
                                               default_size=(1250, 50))
        self.scroll_layout.bind(minimum_height=self.scroll_layout.setter('height'))
        self.scroll_layout.id = 'scroll_content'

        def resize_scroll(call_widget, grid_layout, *args):
            call_widget.height = Window.height // 1.23
            self.fullscreen_shadow.y = self.height + self.x - 3 + 25
            self.fullscreen_shadow.width = Window.width
            search_pos = 47
            self.search_bar.pos = (self.x, search_pos)
            self.input_background.pos = (self.search_bar.pos[0] - 15, self.search_bar.pos[1] + 8)
            self.search_bar.size_hint_max_x = Window.width - self.search_bar.x - 200

        self.resize_bind = lambda *_: Clock.schedule_once(
            functools.partial(resize_scroll, self.scroll_widget, self.scroll_layout), 0)
        Window.bind(on_resize=self.resize_bind)
        self.resize_bind()

        self.scroll_widget.data = self.load_file()

        float_layout = FloatLayout()
        float_layout.id = 'content'
        self.scroll_widget.add_widget(self.scroll_layout)
        float_layout.add_widget(self.scroll_widget)

        scroll_top = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.9}, pos=self.scroll_widget.pos,
                                       size=(self.scroll_widget.width // 1.5, 60))
        scroll_top.color = self.background_color
        scroll_bottom = scroll_background(pos_hint={"center_x": 0.5}, pos=self.scroll_widget.pos,
                                          size=(self.scroll_widget.width // 1.5, -60))
        scroll_bottom.color = self.background_color
        scroll_bottom.y = 115

        float_layout.add_widget(scroll_top)
        float_layout.add_widget(scroll_bottom)

        self.fullscreen_shadow = Image()
        self.fullscreen_shadow.allow_stretch = True
        self.fullscreen_shadow.keep_ratio = False
        self.fullscreen_shadow.size_hint_max = (None, 25)
        self.fullscreen_shadow.color = self.background_color
        self.fullscreen_shadow.opacity = 0
        self.fullscreen_shadow.source = os.path.join(paths.ui_assets, 'control_fullscreen_gradient.png')
        float_layout.add_widget(self.fullscreen_shadow)

        buttons = []
        buttons.append(ExitButton('Back', (0.5, -1), cycle=True))
        for b in buttons:
            float_layout.add_widget(b)

        float_layout.add_widget(generate_title(f"Server Settings: '{self.server_obj.name}'"))
        float_layout.add_widget(generate_footer(f"{self.server_obj.name}, Settings, Edit '${self.file_name}$'"))
        self.add_widget(float_layout)

        self.search_bar = self.SearchInput()
        self.search_bar.bind(text=self.search_text)
        self.add_widget(self.search_bar)

        self.match_label = AlignLabel()
        self.match_label.text = '0 matches'
        self.match_label.halign = "right"
        self.match_label.color = (0.6, 0.6, 1, 1)
        self.match_label.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["mono-bold"]}.otf')
        self.match_label.font_size = sp(24)
        self.match_label.y = 60
        self.match_label.padding_x = 10
        self.match_label.opacity = 0
        self.add_widget(self.match_label)

        self.input_background = Image()
        self.input_background.default_opacity = 0.35
        self.input_background.color = self.search_bar.foreground_color
        self.input_background.opacity = self.input_background.default_opacity
        self.input_background.allow_stretch = True
        self.input_background.size_hint = (None, None)
        self.input_background.height = self.search_bar.size_hint_max_y / 1.45
        self.input_background.source = os.path.join(paths.ui_assets, 'icons', 'search.png')
        self.add_widget(self.input_background)

        def show_controls():
            controls_text = """This editor allows you to modify additional server configuration options. Shortcuts are provided for ease of use:


• Press 'CTRL+Z' to undo, and 'CTRL+R'/'CTRL+Y' to redo

• Press 'CTRL+S' to save modifications

• Press 'CTRL+Q' to quit the editor

• Press 'CTRL+F' to search for data

• Press 'SPACE' to toggle boolean values (e.g. true, false)""" if constants.os_name != 'macos' else """This editor allows you to modify additional server configuration options. Shortcuts are provided for ease of use:


• Press 'CMD+Z' to undo, and 'CMD+R'/'CMD+Y' to redo

• Press 'CMD+S' to save modifications

• Press 'CMD+Q' to quit the editor

• Press 'CMD+F' to search for data

• Press 'SPACE' to toggle boolean values (e.g. true, false)"""

            Clock.schedule_once(
                functools.partial(
                    self.show_popup,
                    "controls",
                    "Controls",
                    controls_text,
                    (None)
                ),
                0
            )

        self.controls_button = IconButton(
            'controls', {}, (70, 110), (None, None), 'question.png',
            clickable=True, anchor='right', click_func=show_controls
        )
        float_layout.add_widget(self.controls_button)

        self.header = BannerObject(
            pos_hint={"center_x": 0.5, "center_y": 0.9},
            size=(250, 40),
            color=(0.4, 0.682, 1, 1),
            text=f"Viewing '${self.file_name}$'",
            icon="eye-outline.png"
        )
        self.add_widget(self.header)

        self.controls_button = IconButton(
            'save & quit', {}, (120, 110), (None, None), 'save-sharp.png',
            clickable=True, anchor='right',
            click_func=self.save_and_quit,
            text_offset=(-5, 50)
        )
        float_layout.add_widget(self.controls_button)


# Edit in plain-text mode for fallback
class ServerTextEditScreen(EditorRoot):
    class EditorLine(EditorRoot.EditorLine):
        def configure(self):
            self.eq_character = ':'
            self.eq_spacing = (1.05, 0.67)

        @staticmethod
        def get_type(value: str):
            # Define custom behavior for determining data types

            return None


# Edit all *.properties/INI files
class ServerPropertiesEditScreen(EditorRoot):
    class EditorLine(EditorRoot.EditorLine):
        def configure(self):
            self.eq_character = '='
            self.eq_spacing = (1.05, 0.67)

        def render_line(self, data: dict):
            self._data = data
            key = data['key']
            is_header = data['is_header']
            is_comment = data['is_comment']
            is_blank_line = data['is_blank_line']
            indent_level = data['indent']
            max_line_count = len(self._screen.line_list)

            # Determines if the line is skip-able when scrolling
            self.is_header = is_header
            self.is_comment = is_comment
            self.is_blank_line = is_blank_line
            self.inactive = data['inactive']
            self.line_matched = data['line_matched']
            self._finished_rendering = False
            self._comment_padding = None

            # Indentation space
            self.indent_level = indent_level
            self.indent_space = dp(25) * self.indent_level

            # Defaults
            font_name = 'mono-bold' if is_header else 'mono-medium'
            self.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts[font_name]}.otf')
            self.spacing = dp(16)
            self.size_hint_min_y = 50
            self.last_search = ''
            self.line_matched = False
            self.select_color = (0.3, 1, 0.6, 1)
            self.animate = False

            # Line number
            self.line_number.text = str(self.line)
            self.line_number.size_hint_max_x = (self.spacing * len(str(max_line_count)))
            self.line_number.opacity = 0.35

            # Key label
            self.key_label = self._key_labels['comment' if self.is_comment else 'normal']
            self.key_label.url = None
            self.key_label.__translate__ = False
            self.key_label.max_lines = 1
            self.key_label.markup = True
            self.key_label.text = key
            self.key_label.original_text = key
            self.key_label.font_name = self.font_name
            self.key_label.font_size = self.font_size
            self.key_label.default_color = "#636363" if is_comment else (0.5, 0.5, 1, 1) if is_header else "#5E6BFF"
            self.key_label.color = self.key_label.default_color
            self.key_label.size_hint_max_y = 50
            self.key_label.pos_hint = {'center_y': 0.5}
            self.key_label.text_size[0] = 1000 if is_comment or is_header else 260
            self.key_label.opacity = 1

            # Show "=" for *.properties/INI
            self.eq_label.text = self.eq_character
            self.eq_label.font_name = self.font_name
            self.eq_label.font_size = self.font_size
            self.eq_label.color = (0.6, 0.6, 1, 1) if is_header else (1, 1, 1, 1)
            self.eq_label.opacity = 0.5
            self.eq_label.pos_hint = {'center_y': 0.5}

            # Dynamically add widgets back
            if not (is_blank_line or is_comment):
                if not is_header:
                    self.add_widget(self.value_label)

            # Ghost covers for left / right
            self.add_widget(self.ghost_cover_left)
            self.add_widget(self.ghost_cover_right)

            # Add remaining widgets
            if not (is_blank_line or is_comment or is_header):
                self.add_widget(self.eq_label)
            self.add_widget(self.line_number)
            self.add_widget(self.key_label)

    # Override logic to parse search matches
    @staticmethod
    def _check_match_logic(data: dict, search_text: str):
        if "=" in search_text:
            key_text, value_text = [x.strip() for x in search_text.split("=", 1)]
        else:
            key_text = ''
            value_text = ''

        return key_text, value_text

    # *.properties/INI specific features
    def insert_line(self, line: (tuple, list, dict), index: int = None, refresh=True):
        if not isinstance(line, dict):

            key, value, is_blank_line, is_comment, is_header = line

            inactive = is_blank_line or is_header or is_comment

            data = {'data': {
                '__hash__': constants.gen_rstring(4),
                'key': key,
                'value': value,
                'original_value': value,
                'is_header': is_header,
                'is_comment': is_comment,
                'is_blank_line': is_blank_line,
                'inactive': inactive,
                'line_matched': False
            }}

        else:
            data = line

        return super().insert_line(data, index, refresh)

    def load_file(self):
        self.line_list = []

        for raw_line in self.read_from_disk():
            line = raw_line.rstrip('\r\n')

            # Extract leading indentation
            match = re.match(r'^(\s*)', line)
            indent_str = match.group(1) if match else ''

            # Strip the indentation and parse the rest
            stripped_line = line[len(indent_str):]

            is_comment = False
            is_blank_line = False
            is_header = False
            key = ''
            value = ''

            # Line has no content
            if not stripped_line.strip():
                is_blank_line = True

            # Is INI/TOML header
            elif stripped_line.startswith('[') and stripped_line.endswith(']') and '=' not in stripped_line:
                key = stripped_line
                is_header = True

            # Line is a comment
            elif stripped_line.startswith('#'):
                key = '# ' + stripped_line.lstrip('#').strip()
                is_comment = True

            # Normal key=value pair
            elif '=' in stripped_line:
                key, value = [x.strip() for x in stripped_line.split('=', 1)]

            # Build the data object
            data = {
                '__hash__': constants.gen_rstring(4),
                'key': key,
                'value': value,
                'original_value': value,
                'is_header': is_header,
                'is_comment': is_comment,
                'is_blank_line': is_blank_line,
                'indent': len(indent_str),
                'inactive': (is_blank_line or is_header or is_comment),
                'line_matched': False
            }

            # Insert data into editor
            self.insert_line({'data': data}, refresh=False)

        return self.line_list

    def save_file(self):
        final_content = ''

        for line in self.line_list:
            line = line['data']
            indent = "    " * line['indent']
            key_str = str(line['key']).strip()
            val_str = str(line['value']).strip()

            if line['is_comment'] or line['is_blank_line']:
                final_content += str(f"{indent}{key_str}".rstrip() + '\n')

            elif line['is_header'] or not val_str:
                final_content += str(f"{indent}{key_str}".rstrip() + '\n')

            elif key_str and val_str:
                final_content += str(f"{indent}{key_str}={val_str}".rstrip() + '\n')

            elif key_str:
                final_content += str(f"{indent}{key_str}=".rstrip() + '\n')

        self.write_to_disk(final_content)

        # If "server.properties", reload config
        if self.file_name == 'server.properties':
            self.server_obj.reload_config()


# Edit all TOML/TML files
class ServerTomlEditScreen(ServerPropertiesEditScreen):

    def save_file(self):
        final_content = ''

        for line in self.line_list:
            line = line['data']
            indent = "    " * line['indent']
            key_str = str(line['key']).strip()
            val_str = str(line['value']).strip()

            if line['is_comment'] or line['is_blank_line']:
                final_content += str(f"{indent}{key_str}".rstrip() + '\n')

            elif line['is_header'] or not val_str:
                final_content += str(f"{indent}{key_str}".rstrip() + '\n')

            elif key_str and val_str:
                final_content += str(f"{indent}{key_str} = {val_str}".rstrip() + '\n')

            elif key_str:
                final_content += str(f"{indent}{key_str} = ".rstrip() + '\n')

        # return print(final_content)
        self.write_to_disk(final_content)


# Edit all YAML/YML files
class ServerYamlEditScreen(EditorRoot):
    class EditorLine(EditorRoot.EditorLine):
        def configure(self):
            self.eq_character = ':'
            self.eq_spacing = (1.05, 0.67)

        def render_line(self, data: dict):
            self._data = data
            line_list = self._screen.line_list
            key = data['key']
            indent_level = data['indent']
            is_header = data['is_header']
            is_list_header = data['is_list_header']
            is_multiline_string = data['is_multiline_string']
            is_list_item = data['is_list_item']
            is_comment = data['is_comment']
            is_blank_line = data['is_blank_line']
            max_line_count = len(line_list)

            # Determines if the line is skip-able when scrolling
            self.is_header = is_header
            self.is_list_header = is_list_header
            self.is_list_item = is_list_item
            self.is_comment = is_comment
            self.is_blank_line = is_blank_line
            self.is_multiline_string = is_multiline_string
            self.inactive = data['inactive']
            self.line_matched = data['line_matched']
            self._finished_rendering = False
            self._comment_padding = None

            # Defaults
            font_name = 'mono-bold' if is_header or is_list_header else 'mono-medium'
            self.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts[font_name]}.otf')
            self.spacing = dp(16)
            self.size_hint_min_y = 50
            self.last_search = ''
            self.line_matched = False
            self.select_color = (0.3, 1, 0.6, 1)
            self.animate = False

            # Indentation space
            self.indent_level = indent_level
            self.indent_space = dp(25) * self.indent_level

            # Line number
            self.line_number.text = str(self.line)
            self.line_number.size_hint_max_x = (self.spacing * len(str(max_line_count)))
            self.line_number.opacity = 0.35

            # Key label
            self.key_label = self._key_labels['comment' if self.is_comment else 'normal']
            self.key_label.url = None
            self.key_label.__translate__ = False
            self.key_label.max_lines = 1
            self.key_label.shorten = True
            self.key_label.shorten_from = 'right'
            self.key_label.markup = True
            self.key_label.text = key
            self.key_label.original_text = key
            self.key_label.font_name = self.font_name
            self.key_label.font_size = self.font_size
            self.key_label.default_color = "#636363" if is_comment else (0.5, 0.5, 1, 1) if is_header else "#5E6BFF"
            self.key_label.color = self.key_label.default_color
            self.key_label.size_hint_max_y = 50
            self.key_label.pos_hint = {'center_y': 0.5}
            self.key_label.opacity = 0 if is_list_item else 1

            # Show ":" for YAML
            self.eq_label.text = '-' if is_list_item else ':'
            self.eq_label.font_name = self.font_name
            self.eq_label.font_size = self.font_size
            self.eq_label.color = (0.6, 0.6, 1, 1) if is_header else (1, 1, 1, 1)
            self.eq_label.opacity = 0.5
            self.eq_label.pos_hint = {'center_y': 0.5}

            if not (is_blank_line or is_comment):
                if not is_header and not is_list_header:
                    self.add_widget(self.value_label)

            # Ghost covers for left / right
            self.add_widget(self.ghost_cover_left)
            self.add_widget(self.ghost_cover_right)

            # Add remaining widgets
            if not (is_blank_line or is_comment or is_multiline_string):
                self.add_widget(self.eq_label)
            if is_multiline_string:
                self.key_label.opacity = 0
            self.add_widget(self.line_number)
            self.add_widget(self.key_label)

        @staticmethod
        def get_type(value: str):
            data_type = str

            # Define custom behavior for determining data types

            # Structured data detection
            if ((value.strip().startswith('{') and value.strip().endswith('}'))
                    or (value.strip().startswith('[') and value.strip().endswith(']'))
                    or (value.strip().startswith('(') and value.strip().endswith(')'))):
                data_type = dict

            # Boolean detection
            elif value.lower() in ['true', 'false', 'yes', 'no']:
                data_type = bool

            # Numeric detection (int or float)
            elif value.replace(".", "").replace("-", "").isdigit():
                data_type = float

            return data_type

        @staticmethod
        def keyboard_overrides(self, window, keycode, text, modifiers):

            # Toggle boolean values with space
            def replace_text(val, *args):
                self.text = val

            if keycode[1] == "spacebar":
                if self.text == 'yes':
                    Clock.schedule_once(functools.partial(replace_text, 'no'), 0)
                    return
                elif self.text == 'no':
                    Clock.schedule_once(functools.partial(replace_text, 'yes'), 0)
                    return

            # Add a new multi-line string on pressing "enter" in a current string
            if ((not self._line.is_list_item and self.text) or (self._line.is_multiline_string and self.text)) and \
                    keycode[1] in ['enter', 'return']:
                parent = self._line.parent
                if not parent:
                    return

                data = (
                    '__string__',
                    '',
                    self._line.indent_level + (2 if self._line.is_multiline_string else 1),
                    False,
                    False
                )

                self._line._screen.insert_line(data, self._line.line)

                def deselect(*a):
                    self._line._screen.current_line = None
                    self.focused = False

                Clock.schedule_once(deselect, 0)

                # Record the insertion action for undo
                if self._line.undo_func:
                    self._line.undo_func(
                        save=True,
                        action={
                            'type': 'insert_line',
                            'data': data,
                            'index': self._line.line
                        }
                    )

                self._line._screen.scroll_to_line(self._line.line + 1, grab_focus=True)

            # Remove line on backspace if it's empty
            elif self._line.is_multiline_string and keycode[1] in ['delete', 'backspace'] and not self._original_text:
                parent = self._line.parent
                if not parent:
                    return

                # Attempt to gather last line
                try:
                    next_line = self._line._screen.line_list[self._line.line - 1]['data']
                except:
                    next_line = {'is_list_item': False, 'eof': True}
                eof = 'eof' in next_line

                # Record the removal action for undo
                if self._line.undo_func:
                    self._line.undo_func(
                        save=True,
                        action={
                            'type': 'remove_line',
                            'data': self._line._data,
                            'index': self._line.line - 1
                        }
                    )

                self._line._screen.remove_line(self._line.line - 1)
                self._line._screen.scroll_to_line(self._line.line - 1, grab_focus=not eof)


            # Add a new list item on pressing "enter" in a current list
            elif (not self._line.is_multiline_string) and (
                    ((self._line.is_list_item and self.text) or (not self._line.is_list_item and not self.text)) and
                    keycode[1] in ['enter', 'return']):
                parent = self._line.parent
                if not parent:
                    return

                if not self.text and not self._line.is_list_item:
                    self._line._data['is_list_header'] = True
                    self._line._update_data(self._line._data)

                data = (
                    '__list__',
                    '',
                    self._line.indent_level,
                    False,
                    False
                )
                self._line._screen.insert_line(data, self._line.line)

                def deselect(*a):
                    self._line._screen.current_line = None
                    self.focused = False

                Clock.schedule_once(deselect, 0)

                # Record the insertion action for undo
                if self._line.undo_func:
                    self._line.undo_func(
                        save=True,
                        action={
                            'type': 'insert_line',
                            'data': data,
                            'index': self._line.line
                        }
                    )

                self._line._screen.scroll_to_line(self._line.line + 1, grab_focus=True)

            # Remove line on backspace if it's empty
            elif self._line.is_list_item and keycode[1] in ['delete', 'backspace'] and not self._original_text:
                parent = self._line.parent
                if not parent:
                    return

                # Record the removal action for undo
                if self._line.undo_func:
                    self._line.undo_func(
                        save=True,
                        action={
                            'type': 'remove_line',
                            'data': self._line._data,
                            'index': self._line.line - 1
                        }
                    )

                self._line._screen.remove_line(self._line.line - 1)

                # Existing focusing logic
                try:
                    previous_line = self._line._screen.line_list[self._line.line - 2]['data']
                    try:
                        next_line = self._line._screen.line_list[self._line.line - 1]['data']
                    except:
                        next_line = {'is_list_item': False, 'eof': True}
                    eof = 'eof' in next_line

                    if previous_line['is_list_item']:
                        self._line._screen.scroll_to_line(self._line.line - 1, grab_focus=True)

                    if not previous_line['is_list_item'] and previous_line['is_list_header'] and not next_line[
                        'is_list_item']:
                        previous_line['is_list_header'] = False
                        previous_line['inactive'] = False
                        self._line._screen.scroll_to_line(self._line.line - 1, grab_focus=not eof)
                        for line in self._line.scroll_layout.children:
                            line.value_label.focused = False
                        self._line.scroll_widget.data = self._line.line_list
                        self._line.scroll_widget.refresh_from_data()
                except:
                    pass

    # Override logic to parse search matches
    @staticmethod
    def _check_match_logic(data: dict, search_text: str):
        if "-" in search_text and data['is_list_item']:
            key_text, value_text = [x.strip() for x in search_text.split("-", 1)]
        elif ":" in search_text:
            key_text, value_text = [x.strip() for x in search_text.split(":", 1)]
        else:
            key_text = ''
            value_text = ''

        return key_text, value_text

    # YAML/YML specific features
    def insert_line(self, line: (tuple, list, dict), index: int = None, refresh=True):
        if not isinstance(line, dict):

            key, value, indent, is_header, is_list_header = line

            # Format empty values
            if value in ['""', "''", None]:
                value = ''

            # Format list_headers
            if is_list_header:
                is_header = False

            # Format list items
            is_list_item = key == '__list__'
            if is_list_item:
                key = '-'

            # Format multiline strings
            is_multiline_string = key == '__string__'
            if is_multiline_string:
                key = ''

            # Format multiline strings
            if is_multiline_string:
                indent = indent - 2
                key = '⁎'

            is_comment = key.strip().startswith('#')
            is_blank_line = not key.strip()
            inactive = is_header or is_list_header or is_comment or is_blank_line

            data = {'data': {
                '__hash__': constants.gen_rstring(4),
                'key': key,
                'value': value,
                'original_value': value,
                'indent': indent,
                'is_header': is_header,
                'is_list_header': is_list_header,
                'is_multiline_string': is_multiline_string,
                'is_comment': is_comment,
                'is_blank_line': is_blank_line,
                'is_list_item': is_list_item,
                'inactive': inactive,
                'line_matched': False
            }}

        else:
            data = line

        return super().insert_line(data, index, refresh)

    def load_file(self):

        def parse_yaml(lines: list):
            """
            Parses a YAML-like text line by line and returns a list of tuples in the form:
              (key, value, indent, is_header, is_list_header)

            Where:
              - Comments become (full_comment_text, '', indent, False, False)
              - Blank lines become ('', '', 0, False, False)
              - Multiline strings become ('__string__', full_line_text, indent, False, False)
              - List items become ('__list__', item_value, indent, False, False)
              - Normal key/value lines become (key, value, indent, is_header, is_list_header)
                * is_header = True if the line ends with a colon and no value,
                  and the next line is indented more deeply than this line.
                * is_list_header = True if the line ends with a colon and no value,
                  and the next non-comment, non-blank line is a list item.
            """

            # This list will hold dictionaries that we will later convert to tuples
            parsed_lines = []

            def get_indent(line):
                """
                Count leading spaces and convert to an integer "indent level".
                This example divides the number of leading spaces by 2, assuming 2 spaces = 1 indent level.
                Adjust if your YAML uses a different convention.
                """
                raw_leading_spaces = len(line) - len(line.lstrip(' '))
                return raw_leading_spaces // 2

            for line in lines:
                # 1) Identify indentation
                indent = get_indent(line)
                stripped = line.lstrip(' ')

                # 2) Check if blank line
                if not stripped.strip():
                    # Blank line (indent is forced to 0 in the final structure, per your example)
                    parsed_lines.append({
                        'key': '',
                        'value': '',
                        'indent': 0,
                        'is_header': False,
                        'is_list_header': False
                    })
                    continue

                # 3) Check if comment line
                if stripped.startswith('#'):
                    # Store the comment as key, no value
                    # Keep the "calculated" indent—your examples show comments sometimes having >0 indent
                    parsed_lines.append({
                        'key': stripped,
                        'value': '',
                        'indent': indent,
                        'is_header': False,
                        'is_list_header': False
                    })
                    continue

                # 4) Check if list item (starts with '-')
                if stripped.startswith('-'):
                    # Everything after the dash is the item value
                    item_value = stripped[1:].strip()
                    current_line = {
                        'key': '__list__',
                        'value': item_value,
                        'indent': indent,
                        'is_header': False,
                        'is_list_header': False
                    }
                    parsed_lines.append(current_line)

                    # Check if the previous meaningful line should be flagged as a "multiline list header"
                    # Condition: the previous line has no value, is not blank or comment or __string__
                    if len(parsed_lines) > 1:
                        prev_line = parsed_lines[-2]
                        # "Meaningful" means not blank line, not comment, not string placeholder
                        if (
                                prev_line['value'] == '' and
                                prev_line['key'] not in ('', '__string__') and
                                not prev_line['key'].startswith('#')
                        ):
                            prev_line['is_list_header'] = True

                    continue

                # 5) Check if we have a proper "key: value"
                # If there's a colon, split on the first colon + space
                if ': ' in stripped:
                    key_part, value_part = stripped.split(': ', 1)
                    key_part = key_part.strip()
                    value_part = value_part.strip()

                    current_line = {
                        'key': key_part,
                        'value': value_part,
                        'indent': indent,
                        'is_header': False,
                        'is_list_header': False
                    }
                    parsed_lines.append(current_line)

                # 6) Check if we have a proper "key:" line
                elif stripped.endswith(':'):
                    current_line = {
                        'key': stripped.rstrip(':'),
                        'value': '',
                        'indent': indent,
                        'is_header': False,
                        'is_list_header': False
                    }
                    parsed_lines.append(current_line)

                else:
                    # 6) Possibly a multiline string line or a weird line with no colon at all
                    #    We'll interpret this as a multiline string if it is more indented than the previous line
                    #    and the previous line is not comment/blank/string
                    if parsed_lines:
                        prev_line = parsed_lines[-1]
                        if (
                                indent > prev_line['indent'] and
                                prev_line['key'] not in ('', '__string__') and
                                not prev_line['key'].startswith('#')
                        ):
                            # It's a multiline string line
                            parsed_lines.append({
                                'key': '__string__',
                                'value': stripped,
                                'indent': indent,
                                'is_header': False,
                                'is_list_header': False
                            })
                        else:
                            # Fallback: treat as a "header" with no value
                            parsed_lines.append({
                                'key': stripped,
                                'value': '',
                                'indent': indent,
                                'is_header': False,
                                'is_list_header': False
                            })
                    else:
                        # If it's the first line in the file and has no colon, treat as a header
                        parsed_lines.append({
                            'key': stripped,
                            'value': '',
                            'indent': indent,
                            'is_header': False,
                            'is_list_header': False
                        })

            # ----------------------------------------------------------------
            # SECOND PASS:
            # Mark any line as a 'header' if it has an empty value and the NEXT line is more indented.
            #
            # Mark it as a 'header' if:
            #    - key != '' (not blank)
            #    - key != '#' (not comment)
            #    - value = ''
            #    - next line is more indented
            #
            # We already handle list headers in the single pass,
            # so we only do "is_header" fix-up here.
            # ----------------------------------------------------------------
            for i in range(len(parsed_lines) - 1):
                current_line = parsed_lines[i]
                next_line = parsed_lines[i + 1]

                # Skip if it's blank, comment, string marker, or has a value
                if (
                        current_line['key'] not in ('', '__string__') and
                        not current_line['key'].startswith('#') and
                        current_line['value'] == '' and
                        next_line['indent'] > current_line['indent']
                ):
                    current_line['is_header'] = True

            # Finally, convert parsed_lines (list of dicts) to the list of tuples
            result = [
                (
                    d['key'],
                    d['value'],
                    d['indent'],
                    d['is_header'],
                    d['is_list_header']
                )
                for d in parsed_lines
            ]

            return result

        self.undo_history = []
        self.redo_history = []
        self.last_search = ''
        self.match_list = []
        self.modified = False
        self.current_line = None

        # Flatten and insert into the editor
        self.line_list = []
        [self.insert_line(line, refresh=False) for line in parse_yaml(self.read_from_disk())]

        return self.line_list

    def save_file(self):
        final_content = ''

        for line in self.line_list:
            line = line['data']
            key_str = str(line['key']).strip()
            val_str = str(line['value']).strip()
            base_indent = " " * 2

            # Format empty values
            if val_str in ['""', "''", None]:
                val_str = ''

            # Ignore empty list items or multiline strings
            if (line['is_multiline_string'] or line['is_list_item']) and not val_str:
                continue

            if line['is_comment'] or line['is_blank_line']:
                indent = base_indent * line['indent']
                final_content += str(f"{indent}{key_str}".rstrip() + '\n')

            elif line['is_list_item'] and val_str:
                indent = base_indent * line['indent']
                final_content += str(f"{indent}- {val_str}".rstrip() + '\n')

            elif line['is_multiline_string'] and val_str:
                indent = base_indent * (line['indent'] + 2)
                final_content += str(f"{indent}{val_str}".rstrip() + '\n')

            elif line['is_header'] or line['is_list_header'] or not val_str:
                indent = base_indent * line['indent']
                final_content += str(f"{indent}{key_str}:".rstrip() + '\n')

            elif key_str and val_str:
                indent = base_indent * line['indent']
                final_content += str(f"{indent}{key_str}: {val_str}".rstrip() + '\n')

            elif key_str:
                indent = base_indent * line['indent']
                final_content += str(f"{indent}{key_str}:".rstrip() + '\n')

        # return print(final_content)
        self.write_to_disk(final_content)


# Edit all JSON files
class ServerJsonEditScreen(ServerYamlEditScreen):

    # Internally convert JSON to YAML for ease of editing
    def read_from_disk(self) -> list:
        with open(self.path, 'r', encoding='utf-8') as f:
            raw_content = f.read()
            raw_content = raw_content.replace('\\n', '\\\\n').replace('\\r', '\\\\r')

            # Determine format features prior to parsing to preserve when saving
            self.minified = len(raw_content.splitlines()) <= 1

            json_data = json.loads(raw_content)
            content = yaml.dump(json_data, sort_keys=False, allow_unicode=True, width=float("inf"))

            content = content.strip('\r\n')
            return content.splitlines()

    def save_file(self):
        final_content = ''

        for line in self.line_list:
            line = line['data']
            key_str = str(line['key']).strip()
            val_str = str(line['value']).strip()
            base_indent = " " * 2

            # Format empty values
            if val_str in ['""', "''", None]:
                val_str = ''

            # Ignore empty list items or multiline strings
            if (line['is_multiline_string'] or line['is_list_item']) and not val_str:
                continue

            if line['is_comment'] or line['is_blank_line']:
                indent = base_indent * line['indent']
                final_content += str(f"{indent}{key_str}".rstrip() + '\n')

            elif line['is_list_item'] and val_str:
                indent = base_indent * line['indent']
                final_content += str(f"{indent}- {val_str}".rstrip() + '\n')

            elif line['is_multiline_string'] and val_str:
                indent = base_indent * (line['indent'] + 2)
                final_content += str(f"{indent}{val_str}".rstrip() + '\n')

            elif line['is_header'] or line['is_list_header'] or not val_str:
                indent = base_indent * line['indent']
                final_content += str(f"{indent}{key_str}:".rstrip() + '\n')

            elif key_str and val_str:
                indent = base_indent * line['indent']
                final_content += str(f"{indent}{key_str}: {val_str}".rstrip() + '\n')

            elif key_str:
                indent = base_indent * line['indent']
                final_content += str(f"{indent}{key_str}:".rstrip() + '\n')

        # Internally convert YAML back to JSON to retain original file format
        try:
            yaml_data = yaml.safe_load(final_content.strip())

            if self.minified:
                final_content = json.dumps(yaml_data, indent=None, separators=(',', ':')).strip()

            else:
                final_content = json.dumps(yaml_data, indent=4)

        except Exception as e:
            send_log(self.__class__.__name__, f"error saving '{self.path}': {constants.format_traceback(e)}", 'error')
            return False

        # return print(final_content)
        self.write_to_disk(final_content)


# Edit all JSON5 files
class ServerJson5EditScreen(ServerYamlEditScreen):

    @staticmethod
    def json5_to_yaml(raw_content: str) -> str:
        """
        Convert JSON5 content to a YAML-like string preserving comments,
        blank lines, nesting, and indentation.

        The root scope is not indented—that is, one indent level is subtracted
        from every key compared to the raw JSON5. (When converting back to JSON5,
        that indent level is added back.)
        """
        lines = raw_content.splitlines()
        output_lines = []
        pending_comments = []
        base_indent = " " * 2  # two spaces per indent level
        indent_level = 0

        for line in lines:
            stripped = line.strip()

            # Check for opening or closing braces/brackets (ignoring trailing commas)
            if stripped.rstrip(",") in ("{", "["):
                indent_level += 1
                continue
            if stripped.rstrip(",") in ("}", "]"):
                indent_level = max(indent_level - 1, 0)
                continue

            # Preserve blank lines.
            if not stripped:
                output_lines.append("")
                continue

            # Process comments.
            if stripped.startswith("//"):
                comment_text = stripped[2:].strip()
                pending_comments.append(comment_text)
                continue
            if stripped.startswith("/*"):
                comment_text = stripped.lstrip("/*").rstrip("*/").strip()
                pending_comments.append(comment_text)
                continue

            # Process key/value lines.
            # (Assumes keys are quoted and each key/value is on its own line.)
            m = re.match(r'^\s*"([^"]+)"\s*:\s*(.+?)(,)?\s*$', line)
            if m:
                key = m.group(1)
                value = m.group(2).strip()
                # Remove surrounding quotes from a string value.
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                # Subtract one indent level for the YAML output.
                effective_indent = max(indent_level - 1, 0)
                current_indent = base_indent * effective_indent
                # Emit any pending comments.
                for comm in pending_comments:
                    output_lines.append(current_indent + "# " + comm)
                pending_comments.clear()
                # If the value indicates a nested object, output the key alone and increase indent.
                if value == "{" or value.startswith("{"):
                    output_lines.append(current_indent + f"{key}:")
                    indent_level += 1
                else:
                    output_lines.append(current_indent + f"{key}: {value}")
            else:
                current_indent = base_indent * max(indent_level - 1, 0)
                output_lines.append(current_indent + line.strip())
        while output_lines and output_lines[-1] == "":
            output_lines.pop()
        return "\n".join(output_lines)

    @staticmethod
    def yaml_to_json5(yaml_content: str) -> str:
        """
        Convert the YAML text (as produced above) back to JSON5, preserving comments,
        blank lines, nesting, and indentation.

        The YAML file is assumed to have no root indentation (i.e. one indent level was
        subtracted in the JSON5 → YAML conversion). The build step below adds one indent
        level back so that JSON5 keys inside the braces are indented appropriately.
        """
        lines = yaml_content.splitlines()

        def parse_yaml(lines, start_index=0, current_indent=0):
            entries = []
            index = start_index
            pending_comments = []
            while index < len(lines):
                line = lines[index]
                # Determine the indentation level.
                line_indent = len(line) - len(line.lstrip(" "))
                if line_indent < current_indent:
                    break
                stripped_line = line.lstrip(" ")
                if not stripped_line:
                    index += 1
                    continue
                if stripped_line.startswith("#"):
                    # Collect comment.
                    comment_text = stripped_line[1:].strip()
                    pending_comments.append(comment_text)
                    index += 1
                    continue
                # Expect a line in the format: key: [value]
                m = re.match(r'^([\w\-]+)\s*:(.*)$', stripped_line)
                if m:
                    key = m.group(1)
                    value_str = m.group(2).strip()
                    index += 1
                    if value_str == "":
                        # No immediate value; assume a nested block.
                        nested_entries, new_index = parse_yaml(lines, index, current_indent + 2)
                        entry = (pending_comments.copy(), key, nested_entries)
                        pending_comments.clear()
                        entries.append(entry)
                        index = new_index
                    else:
                        # A leaf value.
                        entry = (pending_comments.copy(), key, value_str)
                        pending_comments.clear()
                        entries.append(entry)
                else:
                    index += 1
            return entries, index

        parsed_entries, _ = parse_yaml(lines, 0, 0)

        # Build JSON5 text from the parsed structure.
        json5_lines = []
        json5_lines.append("{")

        def build_json5(entries, indent_level):
            result_lines = []
            json_indent = " " * 4  # 4 spaces per indent level in JSON5 output.
            for i, (comments, key, value) in enumerate(entries):
                for comm in comments:
                    result_lines.append(json_indent * (indent_level + 1) + "// " + comm)
                if isinstance(value, list):
                    result_lines.append(json_indent * (indent_level + 1) + f'"{key}": ' + "{")
                    nested_lines = build_json5(value, indent_level + 1)
                    result_lines.extend(nested_lines)
                    closing_line = json_indent * (indent_level + 1) + "}"
                    comma = "," if i < len(entries) - 1 else ""
                    result_lines.append(closing_line + comma)
                else:
                    # Quote the value if it is not a boolean or numeric.
                    if not (value in ["true", "false"] or re.match(r'^-?\d+(\.\d+)?$', value)):
                        if not ((value.startswith('"') and value.endswith('"')) or
                                (value.startswith("'") and value.endswith("'"))):
                            value = f'"{value}"'
                    comma = "," if i < len(entries) - 1 else ""
                    result_lines.append(json_indent * (indent_level + 1) + f'"{key}": {value}{comma}')
            return result_lines

        # Start with indent_level 0; build_json5 will add one indent level to root keys.
        json5_lines.extend(build_json5(parsed_entries, 0))
        json5_lines.append("}")
        return "\n".join(json5_lines)

    # Internally convert JSON5 to YAML for ease of editing.
    def read_from_disk(self) -> list:
        with open(self.path, 'r', encoding='utf-8') as f:
            raw_content = f.read()
            raw_content = raw_content.replace(r'\n', '\\n').replace(r'\r', '\\r')

            # Convert JSON5 to YAML using our custom parser.
            content = self.json5_to_yaml(raw_content)
            return content.splitlines()

    def save_file(self):
        final_content = ''

        for line in self.line_list:
            line = line['data']
            key_str = str(line['key']).strip()
            val_str = str(line['value']).strip()
            base_indent = " " * 2

            # Format empty values
            if val_str in ['""', "''", None]:
                val_str = ''

            # Ignore empty list items or multiline strings
            if (line['is_multiline_string'] or line['is_list_item']) and not val_str:
                continue

            if line['is_comment'] or line['is_blank_line']:
                indent = base_indent * line['indent']
                final_content += str(f"{indent}{key_str}".rstrip() + '\n')

            elif line['is_list_item'] and val_str:
                indent = base_indent * line['indent']
                final_content += str(f"{indent}- {val_str}".rstrip() + '\n')

            elif line['is_multiline_string'] and val_str:
                indent = base_indent * (line['indent'] + 2)
                final_content += str(f"{indent}{val_str}".rstrip() + '\n')

            elif line['is_header'] or line['is_list_header'] or not val_str:
                indent = base_indent * line['indent']
                final_content += str(f"{indent}{key_str}:".rstrip() + '\n')

            elif key_str and val_str:
                indent = base_indent * line['indent']
                final_content += str(f"{indent}{key_str}: {val_str}".rstrip() + '\n')

            elif key_str:
                indent = base_indent * line['indent']
                final_content += str(f"{indent}{key_str}:".rstrip() + '\n')

        try:
            # Convert the assembled YAML back into JSON5.
            json5_content = self.yaml_to_json5(final_content.strip())
        except Exception as e:
            send_log(self.__class__.__name__, f"error saving '{self.path}': {constants.format_traceback(e)}", 'error')
            return False

        # Write the JSON5 back to disk
        # return print(json5_content)
        return self.write_to_disk(json5_content)


# Server Settings Screen ---------------------------------------------------------------------------------------------

def toggle_proxy(boolean, *args):
    server_obj = constants.server_manager.current_server
    server_obj.enable_proxy(boolean)

    # If enabled, clear the server IP box and in "server.properties"
    if boolean:
        server_obj.server_properties['server-ip'] = ''
        server_obj.properties_hash = server_obj._get_properties_hash()
        server_obj.write_config()

        if utility.screen_manager.current == 'ServerSettingsScreen':
            utility.screen_manager.current_screen.ip_input._allow_ip = False
            utility.screen_manager.current_screen.ip_input.text = str(server_obj.port) if str(
                server_obj.port) != '25565' else ''

    elif utility.screen_manager.current == 'ServerSettingsScreen':
        utility.screen_manager.current_screen.ip_input._allow_ip = True
        utility.screen_manager.current_screen.ip_input.text = process_ip_text(server_obj=server_obj)

    # Show banner if server is running
    def default_message(*a):
        Clock.schedule_once(
            functools.partial(
                utility.screen_manager.current_screen.show_banner,
                (0.553, 0.902, 0.675, 1) if boolean else (0.937, 0.831, 0.62, 1),
                f"playit proxy is {'en' if boolean else 'dis'}abled",
                "checkmark-circle-outline.png" if boolean else "close-circle-outline.png",
                2.5,
                {"center_x": 0.5, "center_y": 0.965}
            ), 0
        )

    try:
        if utility.screen_manager.current_screen.check_changes(server_obj):
            Clock.schedule_once(
                functools.partial(
                    utility.screen_manager.current_screen.show_banner,
                    (0.937, 0.831, 0.62, 1),
                    f"A server restart is required to apply changes",
                    "sync.png",
                    3,
                    {"center_x": 0.5, "center_y": 0.965}
                ), 0
            )
        else:
            default_message()

    except AttributeError:
        default_message()


class ServerWorldScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'

        self.new_world = 'world'
        self.new_seed = ''
        self.new_type = 'default'

    def generate_menu(self, **kwargs):
        server_obj = constants.server_manager.current_server

        # Return if no free space
        if disk_popup('ServerSettingsScreen', telepath_data=server_obj._telepath_data):
            return

        self.new_world = 'world'
        self.new_seed = ''
        self.new_type = 'default'

        # Generate buttons on page load
        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'
        float_layout.add_widget(InputLabel(pos_hint={"center_x": 0.5, "center_y": 0.67}))
        float_layout.add_widget(
            HeaderText("What world would you like to use?", 'This action will automatically create a back-up',
                       (0, 0.83)))
        float_layout.add_widget(ServerWorldInput(pos_hint={"center_x": 0.5, "center_y": 0.58}))
        float_layout.add_widget(ServerSeedInput(pos_hint={"center_x": 0.5, "center_y": 0.462}))
        buttons.append(input_button('Browse...', (0.5, 0.58), (
        'dir', paths.minecraft_saves if os.path.isdir(paths.minecraft_saves) else paths.user_downloads),
                                    input_name='ServerWorldInput', title='Select a World File'))

        def change_type(type_name):
            self.new_type = type_name

        server_version = server_obj.version
        if constants.version_check(server_version, '>=', "1.1"):
            options = ['normal', 'superflat']
            if constants.version_check(server_version, '>=', "1.3.1"):
                options.append('large biomes')
            if constants.version_check(server_version, '>=', "1.7.2"):
                options.append('amplified')
            default_name = self.new_type.replace("default", "normal").replace("flat", "superflat").replace(
                "large_biomes", "large biomes")
            float_layout.add_widget(
                DropButton(default_name, (0.5, 0.462), options_list=options, input_name='ServerSettingsLevelTypeInput',
                           x_offset=41, custom_func=change_type))

        def change_world(*a):

            # Ignore world if it's the current server world
            if os.path.join(server_obj.server_path, server_obj.world) == self.new_world:
                Clock.schedule_once(
                    functools.partial(
                        utility.screen_manager.current_screen.show_banner,
                        (0.937, 0.831, 0.62, 1),
                        f"The destination world can't be the current world",
                        "close-circle-outline.png",
                        2.5,
                        {"center_x": 0.5, "center_y": 0.965}
                    ), 0
                )
                return

            def change_thread(*a):
                def update_button(*a):
                    try:
                        utility.screen_manager.current_screen.world_button.loading(True)
                    except:
                        pass

                Clock.schedule_once(update_button, 0)

                # If telepath, upload world here and return path
                if server_obj._telepath_data:
                    telepath_data = server_obj._telepath_data
                    if self.new_world != 'world':
                        new_path = constants.telepath_upload(telepath_data, self.new_world)['path']
                    else:
                        new_path = 'world'
                    constants.api_manager.request(
                        endpoint='/main/update_world',
                        host=telepath_data['host'],
                        port=telepath_data['port'],
                        args={
                            'path': new_path,
                            'new_type': self.new_type,
                            'new_seed': self.new_seed,
                            'telepath': True
                        }
                    )
                    constants.api_manager.request(endpoint='/main/clear_uploads', host=telepath_data['host'],
                                                  port=telepath_data['port'])

                # If local, update normally
                else:
                    manager.update_world(self.new_world, self.new_type, self.new_seed)

                def update_ui(*a):
                    try:
                        utility.screen_manager.current_screen.world_button.loading(False)
                    except:
                        pass
                    utility.screen_manager.current_screen.show_banner(
                        (0.553, 0.902, 0.675, 1),
                        f"The server world has been changed successfully",
                        "checkmark-circle-outline.png",
                        2.5,
                        {"center_x": 0.5, "center_y": 0.965}
                    )

                Clock.schedule_once(update_ui, 0)

            utility.screen_manager.previous_screen()
            utility.screen_manager.screen_tree.pop(-1)
            try:
                delete_button = utility.screen_manager.current_screen.delete_button
                utility.screen_manager.current_screen.scroll_widget.scroll_to(delete_button, animate=False)
            except:
                pass
            dTimer(0, change_thread).start()

        buttons.append(
            next_button('Next', (0.5, 0.24), False, next_screen='ServerSettingsScreen', click_func=change_world))
        buttons.append(ExitButton('Back', (0.5, 0.14), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)

        float_layout.add_widget(generate_title(f"Server Settings: '{server_obj.name}'"))
        float_layout.add_widget(generate_footer(f"{server_obj.name}, Settings, Change world"))

        self.add_widget(float_layout)

    def on_pre_enter(self, *args):
        super().on_pre_enter()
        self.toggle_new(True)

    # Call this when world loaded, and when the 'create new world instead' button is clicked. Fix overlapping when added/removed multiple times
    def toggle_new(self, boolean_value):
        server_obj = constants.server_manager.current_server

        current_input = ''
        server_version = server_obj.version

        for child in self.children:
            try:
                if child.id == 'content':
                    for item in child.children:
                        try:
                            if item.__class__.__name__ == 'ServerSeedInput':
                                current_input = 'input'
                                if self.new_world != 'world':
                                    child.remove_widget(item)

                                    try:
                                        if constants.version_check(server_version, '>=', "1.1"):
                                            child.remove_widget([relative for relative in child.children if
                                                                 relative.__class__.__name__ == 'DropButton'][0])
                                    except IndexError as e:
                                        send_log(f'{self.__class__.__name__}.toggle_new',
                                                 "'DropButton' does not exist, can't remove", 'error')

                            elif item.id == 'Create new world instead':
                                current_input = 'button'
                                if self.new_world == 'world':
                                    child.remove_widget(item)
                        except AttributeError:
                            continue

                    # Show button if true
                    if boolean_value and self.new_world != 'world' and current_input == 'input':
                        child.add_widget(
                            MainButton('Create new world instead', (0.5, 0.442), 'add-circle-outline.png', width=530))

                    # Show seed input, and clear world text
                    elif self.new_world == 'world' and current_input == 'button':
                        child.add_widget(ServerSeedInput(pos_hint={"center_x": 0.5, "center_y": 0.442}))

                        if constants.version_check(server_version, '>=', "1.1"):
                            options = ['normal', 'superflat']
                            if constants.version_check(server_version, '>=', "1.3.1"):
                                options.append('large biomes')
                            if constants.version_check(server_version, '>=', "1.7.2"):
                                options.append('amplified')
                            default_name = self.new_type.replace("default", "normal").replace("flat",
                                                                                              "superflat").replace(
                                "large_biomes", "large biomes")
                            child.add_widget(DropButton(default_name, (0.5, 0.442), options_list=options,
                                                        input_name='ServerSettingsLevelTypeInput', x_offset=41))
                    break

            except AttributeError:
                pass


class ServerSettingsScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'

        self.scroll_widget = None
        self.header = None
        self.title_widget = None
        self.footer_widget = None
        self.menu_taskbar = None

        self.config_button = None
        self.open_path_button = None
        self.update_button = None
        self.update_label = None
        self.proxy_button = None
        self.ip_input = None
        self.rename_input = None
        self.delete_button = None
        self.world_button = None

    def check_changes(self, server_obj, force_banner=False):
        if server_obj.running:
            # print(server_obj.run_data['advanced-hash'], server_obj._get_advanced_hash(), sep="\n")
            if server_obj.run_data and server_obj.run_data['advanced-hash'] != server_obj._get_advanced_hash():
                if "[font=" not in self.header.text.text:
                    icons = os.path.join(paths.ui_assets, 'fonts', constants.fonts['icons'])
                    self.header.text.text = f"[color=#EFD49E][font={icons}]y[/font] " + self.header.text.text + "[/color]"
                    if force_banner:
                        Clock.schedule_once(
                            functools.partial(
                                utility.screen_manager.current_screen.show_banner,
                                (0.937, 0.831, 0.62, 1),
                                f"A server restart is required to apply changes",
                                "sync.png",
                                3,
                                {"center_x": 0.5, "center_y": 0.965}
                            ), 0
                        )
                return True

            else:
                if "[font=" in self.header.text.text:
                    self.header.text.text = self.header.text.text.split("[/font] ")[1].split("[/color]")[0].strip()

        return False

    def generate_menu(self, **kwargs):
        server_obj = constants.server_manager.current_server
        server_obj.reload_config()

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

            def update_grid(*args):
                anchor_layout.size_hint_min_y = grid_layout.height

            Clock.schedule_once(update_grid, 0)

        self.resize_bind = lambda *_: Clock.schedule_once(
            functools.partial(resize_scroll, scroll_widget, scroll_layout, scroll_anchor), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        scroll_layout.bind(minimum_height=scroll_layout.setter('height'))
        scroll_layout.id = 'scroll_content'

        # Scroll gradient
        scroll_top = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.84}, pos=scroll_widget.pos,
                                       size=(scroll_widget.width // 1.5, 60))
        scroll_bottom = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.17}, pos=scroll_widget.pos,
                                          size=(scroll_widget.width // 1.5, -60))

        # Generate buttons on page load
        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'

        pgh_font = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["mono-medium"]}.otf')

        # Create and add paragraphs to GridLayout
        def create_paragraph(name, layout, cid, center_y):

            sub_layout = ScrollItem()
            content_size = sp(22)
            content_height = sum([(child.height + (layout.spacing[0] * 2)) for child in layout.children])
            paragraph = paragraph_object(size=(530, content_height), name=name, content=' ', font_size=content_size,
                                         font=pgh_font)
            sub_layout.height = paragraph.height + 80

            sub_layout.add_widget(paragraph)
            sub_layout.add_widget(layout)
            layout.pos_hint = {'center_x': 0.5, 'center_y': center_y}
            scroll_layout.add_widget(sub_layout)

        # ----------------------------------------------- General ------------------------------------------------------

        general_layout = GridLayout(cols=1, spacing=10, size_hint_max_x=1050, size_hint_y=None, padding=[0, 0, 0, 0])

        if server_obj.type == 'vanilla':
            # Edit properties button
            def edit_server_properties(*args):
                for directory, files in server_obj.config_paths.items():
                    if directory.endswith(server_obj.name):
                        for file in files:
                            if file.endswith('server.properties'):
                                return open_config_file(file)

            self.config_button = WaitButton("Edit 'server.properties'", (0.5, 0.5), 'document-text-outline.png',
                                            click_func=edit_server_properties)
        else:
            # Edit config button
            def open_config_menu(*args):
                utility.screen_manager.current = 'ServerConfigScreen'

            self.config_button = WaitButton("Edit Configuration Files", (0.5, 0.5), 'document-text-outline.png',
                                            click_func=open_config_menu)

        sub_layout = ScrollItem()
        sub_layout.add_widget(self.config_button)
        general_layout.add_widget(sub_layout)

        if server_obj._telepath_data:
            def download_server(*a):
                def download_thread():
                    if utility.screen_manager.current_screen.name == 'ServerSettingsScreen':
                        download_button = utility.screen_manager.current_screen.download_button
                        if download_button:
                            Clock.schedule_once(functools.partial(download_button.loading, True), 0)

                    path = os.path.join(server_obj.backup.directory, server_obj.backup.save()[0])
                    location = constants.telepath_download(server_obj._telepath_data, path, paths.user_downloads)
                    if os.path.exists(location):
                        constants.open_folder(location)
                        Clock.schedule_once(
                            functools.partial(
                                utility.screen_manager.current_screen.show_banner,
                                (0.553, 0.902, 0.675, 1),
                                f"Downloaded $'{server_obj._view_name}'$ successfully",
                                "cloud-download-sharp.png",
                                3,
                                {"center_x": 0.5, "center_y": 0.965}
                            ), 1
                        )

                    if utility.screen_manager.current_screen.name == 'ServerSettingsScreen':
                        download_button = utility.screen_manager.current_screen.download_button
                        if download_button:
                            Clock.schedule_once(functools.partial(download_button.loading, False), 0)

                dTimer(0, download_thread).start()

            sub_layout = ScrollItem()
            self.download_button = WaitButton('Download Server', (0.5, 0.5), 'cloud-download-sharp.png',
                                              click_func=download_server)
            sub_layout.add_widget(self.download_button)
            general_layout.add_widget(sub_layout)

        else:

            # Open server directory
            def open_server_dir(*args):
                constants.open_folder(server_obj.server_path)
                Clock.schedule_once(self.open_path_button.button.on_leave, 0.5)

            sub_layout = ScrollItem()
            self.open_path_button = WaitButton('Open Server Directory', (0.5, 0.5), 'folder-outline.png',
                                               click_func=open_server_dir)
            sub_layout.add_widget(self.open_path_button)
            general_layout.add_widget(sub_layout)

        # RAM allocation slider (Max limit = 75% of memory capacity)
        max_limit = constants.get_remote_var('max_memory', server_obj._telepath_data)
        min_limit = 0
        start_value = min_limit if str(server_obj.dedicated_ram) == 'auto' else int(server_obj.dedicated_ram)

        def change_limit(val):
            server_obj.set_ram_limit('auto' if val == min_limit else val)
            self.check_changes(server_obj, force_banner=True)

        sub_layout = ScrollItem()
        sub_layout.add_widget(blank_input(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="memory usage  (GB)"))
        sub_layout.add_widget(
            NumberSlider(start_value, (0.5, 0.5), input_name='RamInput', limits=(min_limit, max_limit),
                         min_icon='auto-icon.png', function=change_limit))
        general_layout.add_widget(sub_layout)

        # JVM flags
        sub_layout = ScrollItem()
        sub_layout.add_widget(InputLabel(pos_hint={"center_x": 0.5, "center_y": 1.1}))
        flag_input = ServerFlagInput(pos_hint={'center_x': 0.5, 'center_y': 0.5})
        flag_input.size_hint_max_x = 435
        sub_layout.add_widget(flag_input)
        general_layout.add_widget(sub_layout)

        create_paragraph('general', general_layout, 0, 0.65)

        # --------------------------------------------------------------------------------------------------------------

        # ----------------------------------------------- Network ------------------------------------------------------

        network_layout = GridLayout(cols=1, spacing=10, size_hint_max_x=1050, size_hint_y=None, padding=[0, 0, 0, 0])

        # MOTD Input
        sub_layout = ScrollItem()
        sub_layout.add_widget(InputLabel(pos_hint={"center_x": 0.5, "center_y": 1.2}))
        motd_input = ServerMOTDInput(pos_hint={'center_x': 0.5, 'center_y': 0.5})
        motd_input.size_hint_max_x = 435
        sub_layout.add_widget(motd_input)
        network_layout.add_widget(sub_layout)

        proxy_state = server_obj.proxy_enabled

        # Edit IP/Port input
        sub_layout = ScrollItem()
        sub_layout.add_widget(InputLabel(pos_hint={"center_x": 0.5, "center_y": 1.1}))
        self.ip_input = ServerPortInput(pos_hint={'center_x': 0.5, 'center_y': 0.5},
                                        text=process_ip_text(server_obj=server_obj))
        self.ip_input._allow_ip = not proxy_state
        self.ip_input.size_hint_max_x = 435
        sub_layout.add_widget(self.ip_input)
        network_layout.add_widget(sub_layout)

        # Playit toggle/install button
        def add_switch(index=0, fade=False, *a):
            sub_layout = ScrollItem()
            input_border = blank_input(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text='enable proxy (playit)',
                                       disabled=(not constants.app_online))
            sub_layout.add_widget(input_border)

            def open_login(*a):
                def _thread():
                    url = server_obj.get_playit_url()
                    if url: webbrowser.open_new_tab(url)

                Clock.schedule_once(
                    functools.partial(
                        self.show_popup,
                        "query",
                        "Open playit panel",
                        "This will redirect you to playit's web panel.\n\nClick 'continue as guest' to get started",
                        (None, dTimer(0, _thread).start)
                    ),
                    0
                )

            # Open playit web panel button
            open_panel_button = RelativeIconButton('open panel', {'center_x': 2.65, 'center_y': 0.5}, (0, 0),
                                                   (None, None), 'open.png', clickable=True, click_func=open_login,
                                                   text_offset=(20, 50), anchor='right')
            open_panel_button.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
            open_panel_button.size_hint_max = (50, 50)
            open_panel_button.opacity = 0.8
            open_panel_button.text.text = '\n\n\nopen panel'
            sub_layout.add_widget(open_panel_button)

            # Add toggle button to enable/disable widget
            sub_layout.add_widget(
                toggle_button('proxy', (0.5, 0.5), custom_func=toggle_proxy, default_state=proxy_state,
                              disabled=(not constants.app_online)))

            network_layout.add_widget(sub_layout, index)

            if fade:
                input_border.opacity = 0
                Animation(opacity=1, duration=0.5).start(input_border)

        if not server_obj.proxy_installed():
            def prompt_install(*args):
                def install_wrapper(*a):
                    Clock.schedule_once(functools.partial(self.proxy_button.loading, True), 0)
                    boolean = server_obj.install_proxy()

                    def add_widgets(*b):
                        self.proxy_button.loading(False)
                        network_layout.remove_widget(self.proxy_button.parent)
                        add_switch(1, True)
                        Clock.schedule_once(
                            functools.partial(
                                utility.screen_manager.current_screen.show_banner,
                                (0.553, 0.902, 0.675, 1) if boolean else (0.937, 0.831, 0.62, 1),
                                f"playit was {'installed successfully' if boolean else 'not installed'}",
                                "checkmark-circle-outline.png" if boolean else "close-circle-outline.png",
                                2.5,
                                {"center_x": 0.5, "center_y": 0.965}
                            ), 0
                        )

                    Clock.schedule_once(add_widgets, 0)

                if constants.app_online:
                    Clock.schedule_once(
                        functools.partial(
                            self.show_popup,
                            "query",
                            "Install playit",
                            "playit is a free proxy service that creates a tunnel to the internet. It can be used to bypass ISP port blocking or conflicts in which the client refuses to connect (e.g. strict NAT).\n\nWould you like to install playit?",
                            (None, dTimer(0, install_wrapper).start)
                        ),
                        0
                    )
                else:
                    self.show_popup('warning', 'Error',
                                    'An internet connection is required to install playit\n\nPlease check your connection and try again',
                                    (None))

            sub_layout = ScrollItem()
            self.proxy_button = WaitButton('Install playit', (0.5, 0.5), 'earth.png', click_func=prompt_install)
            sub_layout.add_widget(self.proxy_button)
            network_layout.add_widget(sub_layout)
        else:
            add_switch()

        # Enable Geyser toggle switch
        def toggle_geyser(boolean, install=True):
            if install:
                server_obj.addon._install_geyser(boolean)

                # Actually make changes
                server_obj.config_file.set("general", "enableGeyser", str(boolean).lower())
                server_obj.write_config()
                server_obj.geyser_enabled = boolean

                # Show banner if server is running
                if utility.screen_manager.current_screen.check_changes(server_obj):
                    Clock.schedule_once(
                        functools.partial(
                            utility.screen_manager.current_screen.show_banner,
                            (0.937, 0.831, 0.62, 1),
                            f"A server restart is required to apply changes",
                            "sync.png",
                            3,
                            {"center_x": 0.5, "center_y": 0.965}
                        ), 0
                    )

                else:
                    Clock.schedule_once(
                        functools.partial(
                            utility.screen_manager.current_screen.show_banner,
                            (0.553, 0.902, 0.675, 1) if boolean else (0.937, 0.831, 0.62, 1),
                            f"Bedrock support {'en' if boolean else 'dis'}abled",
                            "checkmark-circle-outline.png" if boolean else "close-circle-outline.png",
                            2.5,
                            {"center_x": 0.5, "center_y": 0.965}
                        ), 0
                    )

        # Geyser switch for bedrock support
        sub_layout = ScrollItem()
        disabled = not (constants.version_check(server_obj.version, ">=", "1.13.2") and server_obj.type.lower() in [
            'spigot', 'paper', 'purpur', 'fabric', 'quilt', 'neoforge'])
        hint_text = "geyser (unsupported server)" if disabled else "bedrock support (geyser)"
        if not constants.app_online:
            disabled = True
        sub_layout.add_widget(
            blank_input(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text=hint_text, disabled=disabled))
        sub_layout.add_widget(toggle_button('geyser', (0.5, 0.5), custom_func=toggle_geyser, disabled=disabled,
                                            default_state=(server_obj.geyser_enabled) and not disabled))
        network_layout.add_widget(sub_layout)

        create_paragraph('network', network_layout, 1, 0.65)

        # --------------------------------------------------------------------------------------------------------------

        # ------------------------------------------------ Updates -----------------------------------------------------

        update_layout = GridLayout(cols=1, spacing=10, size_hint_max_x=1050, size_hint_y=None, padding=[0, 0, 0, 0])

        # Automatic updates toggle
        def toggle_auto_update(boolean, *a):
            server_obj.enable_auto_update(boolean)
            Clock.schedule_once(
                functools.partial(
                    utility.screen_manager.current_screen.show_banner,
                    (0.553, 0.902, 0.675, 1) if boolean else (0.937, 0.831, 0.62, 1),
                    f"Automatic server updates {'en' if boolean else 'dis'}abled",
                    "checkmark-circle-outline.png" if boolean else "close-circle-outline.png",
                    2.5,
                    {"center_x": 0.5, "center_y": 0.965}
                ), 0
            )

        disabled = server_obj.is_modpack and server_obj.is_modpack != 'mrpack'
        sub_layout = ScrollItem()
        sub_layout.add_widget(
            blank_input(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text='automatic updates', disabled=disabled))
        sub_layout.add_widget(toggle_button('auto-update', (0.5, 0.5), custom_func=toggle_auto_update,
                                            default_state=server_obj.auto_update == 'true', disabled=disabled))
        update_layout.add_widget(sub_layout)

        disabled = server_obj.running or not constants.app_online

        # Updates server
        def update_server(*a):
            if server_obj.is_modpack == 'mrpack':
                update_url = ''
                if server_obj._telepath_data:
                    try:
                        update_url = \
                        constants.server_manager.get_telepath_update(server_obj._telepath_data, server_obj.name)[
                            'updateUrl']
                    except KeyError:
                        pass

                else:
                    update_url = constants.server_manager.update_list[server_obj.name]['updateUrl']

                if update_url:
                    foundry.import_data = {
                        'name': server_obj.name,
                        'url': update_url
                    }
                    os.chdir(constants.get_cwd())
                    constants.safe_delete(paths.temp)
                    utility.screen_manager.current = 'UpdateModpackProgressScreen'

            else:
                foundry.new_server_init()
                foundry.init_update()
                foundry.new_server_info['type'] = server_obj.type
                foundry.new_server_info['version'] = foundry.latestMC[server_obj.type]
                if server_obj.type in ['forge', 'paper']:
                    foundry.new_server_info['build'] = foundry.latestMC['builds'][server_obj.type]
                utility.screen_manager.current = 'MigrateServerProgressScreen'

        # Check for updates button
        sub_layout = ScrollItem()

        if server_obj._telepath_data:
            while not constants.server_manager.get_telepath_update(server_obj._telepath_data, server_obj.name):
                constants.server_manager.reload_telepath_updates(server_obj._telepath_data)
                time.sleep(0.5)
        else:
            while server_obj.name not in constants.server_manager.update_list:
                time.sleep(0.1)

        # First check if the server is a '.zip' format modpack
        needs_update = False
        if server_obj._telepath_data:
            try:
                needs_update = constants.server_manager.get_telepath_update(server_obj._telepath_data, server_obj.name)[
                    'needsUpdate']
            except KeyError:
                pass

        else:
            needs_update = constants.server_manager.update_list[server_obj.name]['needsUpdate']

        if server_obj.is_modpack == 'zip':
            def select_file(*a):
                zip_file = file_popup("file", start_dir=paths.user_downloads, ext=["*.zip", "*.mrpack"],
                                      input_name=None, select_multiple=True, title='Select a modpack update')
                if zip_file:
                    zip_file = zip_file[0]
                    if zip_file.endswith('.zip') or zip_file.endswith('.mrpack'):
                        foundry.import_data = {
                            'name': server_obj.name,
                            'path': os.path.abspath(zip_file)
                        }
                        os.chdir(constants.get_cwd())
                        constants.safe_delete(paths.temp)
                        utility.screen_manager.current = 'UpdateModpackProgressScreen'
                    else:
                        self.update_label.update_text('Invalid file type')

            self.update_label = InputLabel(pos_hint={"center_x": 0.5, "center_y": 1.05})
            disabled = (not constants.app_online) or server_obj.running
            self.update_button = WaitButton("Update from '.zip'", (0.5, 0.5), 'modpack.png', disabled=disabled,
                                            click_func=select_file)


        elif needs_update:
            if 'settings' in server_obj.viewed_notifs:
                if server_obj.viewed_notifs['settings'] != server_obj.update_string:
                    Clock.schedule_once(
                        functools.partial(
                            self.show_banner,
                            (0.553, 0.902, 0.675, 1),
                            f"A server update is available",
                            "arrow-up-circle-sharp.png",
                            2.5,
                            {"center_x": 0.5, "center_y": 0.965},
                            'popup/notification'
                        ), 0
                    )
            server_obj._view_notif('settings', viewed=server_obj.update_string)
            self.update_button = WaitButton(f"Update to ${server_obj.update_string}$", (0.5, 0.5),
                                            'arrow-up-circle-outline.png', disabled=disabled, click_func=update_server)

        # No updates are available
        else:
            self.update_button = WaitButton('Up to date', (0.5, 0.5), 'checkmark-circle.png', disabled=True)
            Animation.stop_all(self.update_button.icon)
            self.update_button.icon.opacity = 0.5

        sub_layout.add_widget(self.update_button)
        try:
            if self.update_label:
                sub_layout.add_widget(self.update_label)
        except:
            pass
        update_layout.add_widget(sub_layout)

        # Change 'server.jar' button
        def migrate_server(*a):
            foundry.new_server_init()
            foundry.new_server_info['type'] = server_obj.type
            foundry.new_server_info['version'] = server_obj.version
            utility.screen_manager.current = 'MigrateServerTypeScreen'

        sub_layout = ScrollItem()
        sub_layout.add_widget(WaitButton("Change 'server.jar'", (0.5, 0.5), 'swap-horizontal-outline.png',
                                         disabled=disabled or server_obj.is_modpack, click_func=migrate_server))
        update_layout.add_widget(sub_layout)

        create_paragraph('updates', update_layout, 0, 0.555)

        # --------------------------------------------------------------------------------------------------------------

        # ----------------------------------------------- Transilience -------------------------------------------------

        transilience_layout = GridLayout(cols=1, spacing=10, size_hint_max_x=1050, size_hint_y=None,
                                         padding=[0, 0, 0, 0])

        def rename_server(name, *args):
            def loading_screen(*a):
                utility.screen_manager.current = 'BlurredLoadingScreen'

            Clock.schedule_once(loading_screen, 0)

            # Actually rename the server files
            server_obj.rename(name)

            # Change header and footer text to reflect change
            def change_data(*a):
                def go_back(*a):
                    utility.screen_manager.current = 'ServerSettingsScreen'
                    effect_y = utility.screen_manager.current_screen.scroll_widget.effect_y
                    utility.screen_manager.current_screen.scroll_widget.effect_y = None
                    utility.screen_manager.current_screen.scroll_widget.scroll_y = 0

                    def reset_effect(*a):
                        utility.screen_manager.current_screen.scroll_widget.effect_y = effect_y

                    Clock.schedule_once(reset_effect, 0)

                Clock.schedule_once(go_back, 0)

                self.remove_widget(self.title_widget)
                self.remove_widget(self.footer_widget)
                del self.title_widget
                del self.footer_widget
                self.title_widget = generate_title(f"Server Settings: '{name}'")
                self.footer_widget = generate_footer(f"{name}, Settings", color='EFD49E')
                self.add_widget(self.title_widget)
                self.add_widget(self.footer_widget)

                # Display banner to show success
                Clock.schedule_once(
                    functools.partial(
                        utility.screen_manager.current_screen.show_banner,
                        (0.553, 0.902, 0.675, 1),
                        f"Server renamed to '${name}$' successfully!",
                        "rename.png",
                        2.5,
                        {"center_x": 0.5, "center_y": 0.965}
                    ), 0
                )

            Clock.schedule_once(change_data, 0)

        def rename_thread(name, *a):
            dTimer(0, functools.partial(rename_server, name)).start()

        # Rename server input
        sub_layout = ScrollItem()
        input_label = InputLabel(pos_hint={"center_x": 0.5, "center_y": 1.2})
        sub_layout.add_widget(input_label)
        self.rename_input = ServerRenameInput(pos_hint={'center_x': 0.5, 'center_y': 0.5}, text=server_obj.name,
                                              on_validate=rename_thread, disabled=server_obj.running)
        self.rename_input.size_hint_max_x = 435
        sub_layout.add_widget(self.rename_input)
        transilience_layout.add_widget(sub_layout)

        if server_obj.running:
            input_label.update_text("Server is running", True)

        # Change world file
        def change_world(*a):
            if constants.server_manager.current_server:
                utility.screen_manager.current = 'ServerWorldScreen'

        sub_layout = ScrollItem()
        self.world_button = WaitButton("Change world file", (0.5, 0.5), 'world.png', click_func=change_world,
                                       disabled=server_obj.running)
        sub_layout.add_widget(self.world_button)
        transilience_layout.add_widget(sub_layout)

        # Delete server button
        def delete_server(*args):
            def loading_screen(*a):
                utility.screen_manager.current = 'BlurredLoadingScreen'

            Clock.schedule_once(loading_screen, 0)

            server_name = server_obj.name
            server_obj.delete()
            constants.server_manager.current_server = None

            def switch_screens(*a):
                constants.server_manager.refresh_list()
                utility.screen_manager.current = "ServerManagerScreen"
                utility.screen_manager.screen_tree = ['MainMenuScreen']

                Clock.schedule_once(
                    functools.partial(
                        utility.screen_manager.current_screen.show_banner,
                        (1, 0.5, 0.65, 1),
                        f"'${server_name}$' was deleted successfully",
                        "trash-sharp.png",
                        3,
                        {"center_x": 0.5, "center_y": 0.965}
                    ), 0.1
                )

            Clock.schedule_once(switch_screens, 0.5)

        def timer_delete(*a):
            dTimer(0, delete_server).start()

        def prompt_delete(*args):
            Clock.schedule_once(
                functools.partial(
                    utility.screen_manager.current_screen.show_popup,
                    "warning_query",
                    f"Delete '${server_obj.name}$'",
                    "Do you want to permanently delete this server?\n\nThis action cannot be undone\n(Your server can be re-imported from a back-up later)",
                    (None, functools.partial(Clock.schedule_once, timer_delete, 0.5))
                ),
                0
            )

        sub_layout = ScrollItem()
        self.delete_button = color_button('Delete Server', (0.5, 0.5), 'trash-sharp.png', click_func=prompt_delete,
                                          color=(1, 0.5, 0.65, 1), disabled=server_obj.running)
        sub_layout.add_widget(self.delete_button)
        transilience_layout.add_widget(sub_layout)

        create_paragraph('transilience', transilience_layout, 0, 0.555)

        # --------------------------------------------------------------------------------------------------------------

        # Append scroll view items
        scroll_anchor.add_widget(scroll_layout)
        scroll_widget.add_widget(scroll_anchor)
        float_layout.add_widget(scroll_widget)
        float_layout.add_widget(scroll_top)
        float_layout.add_widget(scroll_bottom)

        # Server Preview Box
        # float_layout.add_widget(server_demo_input(pos_hint={"center_x": 0.5, "center_y": 0.81}, properties=foundry.new_server_info))

        # Configure header
        header_content = "Modify server configuration"
        self.header = HeaderText(header_content, '', (0, 0.89))
        self.check_changes(server_obj, force_banner=True)
        float_layout.add_widget(self.header)

        # if server_obj.advanced_hash_changed():
        #     icons = os.path.join(paths.gui_assets, 'fonts', constants.fonts['icons'])
        #     header_content = f"[color=#EFD49E][font={icons}]y[/font] " + header_content + "[/color]"

        buttons.append(ExitButton('Back', (0.5, -1), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)

        self.title_widget = generate_title(f"Server Settings: '{server_obj.name}'")
        self.footer_widget = generate_footer(f"{server_obj.name}, Settings", color='EFD49E')
        self.add_widget(self.title_widget)
        self.add_widget(self.footer_widget)

        self.add_widget(float_layout)

        # Add ManuTaskbar
        self.menu_taskbar = MenuTaskbar(selected_item='settings')
        self.add_widget(self.menu_taskbar)


# Update/Migrate server screens
class MigrateServerTypeScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'
        self.current_selection = 'vanilla'
        self.content_layout_1 = None
        self.content_layout_2 = None

    def generate_menu(self, **kwargs):
        server_obj = constants.server_manager.current_server

        # Return if no free space or telepath is busy
        if disk_popup('ServerSettingsScreen', telepath_data=server_obj._telepath_data):
            return
        if telepath_popup('ServerSettingsScreen'):
            return

        # Generate buttons on page load
        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'

        float_layout.add_widget(HeaderText("Which distribution would you like to switch to?",
                                           'This action will automatically create a back-up', (0, 0.89)))

        # Create UI buttons
        buttons.append(next_button('Next', (0.5, 0.21), False, next_screen='MigrateServerVersionScreen'))
        buttons.append(ExitButton('Back', (0.5, 0.12), cycle=True))

        self.current_selection = foundry.new_server_info['type']

        # Create type buttons (Page 1)
        self.content_layout_1 = FloatLayout()
        row_top = BoxLayout()
        row_bottom = BoxLayout()
        row_top.pos_hint = {"center_y": 0.66, "center_x": 0.5}
        row_bottom.pos_hint = {"center_y": 0.405, "center_x": 0.5}
        row_bottom.size_hint_max_x = row_top.size_hint_max_x = dp(1000)
        row_top.orientation = row_bottom.orientation = "horizontal"
        row_top.add_widget(
            big_icon_button('runs most plug-ins, optimized', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None),
                            'paper', clickable=True, selected=('paper' == foundry.new_server_info['type'])))
        row_top.add_widget(
            big_icon_button('default, stock experience', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None),
                            'vanilla', clickable=True, selected=('vanilla' == foundry.new_server_info['type'])))
        row_top.add_widget(
            big_icon_button('modded experience', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None), 'forge',
                            clickable=True, selected=('forge' == foundry.new_server_info['type'])))
        row_bottom.add_widget(
            big_icon_button('performant fork of paper', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None),
                            'purpur', clickable=True, selected=('purpur' == foundry.new_server_info['type'])))
        row_bottom.add_widget(
            big_icon_button('modern mod platform', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None), 'fabric',
                            clickable=True, selected=('fabric' == foundry.new_server_info['type'])))
        row_bottom.add_widget(
            big_icon_button('view more options', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None), 'more',
                            clickable=True, selected=False))
        self.content_layout_1.add_widget(row_top)
        self.content_layout_1.add_widget(row_bottom)

        # Create type buttons (Page 2)
        self.content_layout_2 = FloatLayout()
        utility.hide_widget(self.content_layout_2)
        row_top = BoxLayout()
        row_bottom = BoxLayout()
        row_top.pos_hint = {"center_y": 0.66, "center_x": 0.5}
        row_bottom.pos_hint = {"center_y": 0.405, "center_x": 0.5}
        row_top.size_hint_max_x = dp(1000)
        row_bottom.size_hint_max_x = dp(650)
        row_top.orientation = row_bottom.orientation = "horizontal"
        row_top.add_widget(
            big_icon_button('modern $Forge$ implementation', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None),
                            'neoforge', clickable=True, selected=('neoforge' == foundry.new_server_info['type'])))
        row_top.add_widget(
            big_icon_button('enhanced fork of $Fabric$', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None),
                            'quilt', clickable=True, selected=('quilt' == foundry.new_server_info['type'])))
        row_top.add_widget(
            big_icon_button('requires tuning, but efficient', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None),
                            'spigot', clickable=True, selected=('spigot' == foundry.new_server_info['type'])))
        row_bottom.add_widget(
            big_icon_button('legacy, supports plug-ins', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None),
                            'craftbukkit', clickable=True, selected=('craftbukkit' == foundry.new_server_info['type'])))
        row_bottom.add_widget(
            big_icon_button('view more options', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None), 'more',
                            clickable=True, selected=False))
        self.content_layout_2.add_widget(row_top)
        self.content_layout_2.add_widget(row_bottom)

        for button in buttons:
            float_layout.add_widget(button)

        float_layout.add_widget(self.content_layout_1)
        float_layout.add_widget(self.content_layout_2)
        float_layout.add_widget(page_counter(1, 2, (0, 0.86)))
        float_layout.add_widget(generate_title(f"Server Settings: '{server_obj.name}'"))
        float_layout.add_widget(generate_footer(f"{server_obj.name}, Settings, Change 'server.jar'"))

        self.add_widget(float_layout)


class MigrateServerVersionScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'

        self.final_button = None

    def generate_menu(self, **kwargs):
        server_obj = constants.server_manager.current_server

        # Generate buttons on page load
        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'

        # Prevent server creation if offline
        if not constants.app_online:
            float_layout.add_widget(
                HeaderText("Changing the 'server.jar' requires an internet connection", '', (0, 0.6)))
            buttons.append(ExitButton('Back', (0.5, 0.35)))

        # Regular menus
        else:
            def update_next(boolean_value, message, *a):

                if message:
                    for child in float_layout.children:
                        if "ServerVersionInput" in child.__class__.__name__:
                            child.focus = False
                            child.valid(boolean_value, message)

                self.final_button.disable(not boolean_value)

            def migrate_server(*a):

                def start_migration(*a):
                    def main_thread(*b):
                        utility.screen_manager.current = "MigrateServerProgressScreen"

                    Clock.schedule_once(functools.partial(self.final_button.loading, True), 0)
                    foundry.init_update()
                    Clock.schedule_once(main_thread, 0)

                def check_version(*args, **kwargs):
                    self.final_button.loading(True)
                    version_data = foundry.search_version(foundry.new_server_info)
                    foundry.new_server_info['version'] = version_data[1]['version']
                    foundry.new_server_info['build'] = version_data[1]['build']
                    foundry.new_server_info['jar_link'] = version_data[3]
                    self.final_button.loading(False)
                    Clock.schedule_once(functools.partial(update_next, version_data[0], version_data[2]), 0)

                    # Continue to next screen if valid input, and back button not pressed
                    if version_data[0] and not version_data[
                        2] and utility.screen_manager.current == 'MigrateServerVersionScreen':
                        if constants.version_check(foundry.new_server_info['version'], '<', server_obj.version):
                            Clock.schedule_once(
                                functools.partial(
                                    utility.screen_manager.current_screen.show_popup,
                                    "warning_query",
                                    f'Downgrade Warning',
                                    "Downgrading can corrupt the save file and crash until it's replaced.\n\nDo you really wish to downgrade?",
                                    (None, start_migration)
                                ),
                                0
                            )
                        else:
                            start_migration()

                timer = dTimer(0, function=check_version)
                timer.start()

            float_layout.add_widget(InputLabel(pos_hint={"center_x": 0.5, "center_y": 0.57}))
            float_layout.add_widget(page_counter(2, 2, (0, 0.77)))
            float_layout.add_widget(HeaderText("What version of Minecraft would you like to switch to?",
                                               f'Current version:  ${server_obj.version}$', (0, 0.8)))
            self.final_button = WaitButton("Change 'server.jar'", (0.5, 0.24), 'swap-horizontal-outline.png',
                                           click_func=migrate_server)
            float_layout.add_widget(ServerVersionInput(pos_hint={"center_x": 0.5, "center_y": 0.49},
                                                       text=foundry.new_server_info['version'],
                                                       enter_func=migrate_server))
            self.add_widget(self.final_button)
            buttons.append(ExitButton('Back', (0.5, 0.14), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)

        float_layout.add_widget(generate_title(f"Server Settings: '{server_obj.name}'"))
        float_layout.add_widget(generate_footer(f"{server_obj.name}, Settings, Change 'server.jar'"))

        self.add_widget(float_layout)


class MigrateServerProgressScreen(ProgressScreen):

    # Only replace this function when making a child screen
    # Set fail message in child functions to trigger an error
    def contents(self):
        server_obj = constants.server_manager.current_server
        if foundry.new_server_info['type'] != server_obj.type:
            desc_text = "Migrating"
            final_text = "Migrated"
            "migrating '$$'"
            "migrated '$$' successfully"
        elif constants.version_check(foundry.new_server_info['version'], '<', server_obj.version):
            desc_text = "Downgrading"
            final_text = "Downgraded"
            "downgrading '$$'"
            "downgraded '$$' successfully"
        elif constants.version_check(foundry.new_server_info['version'], '>',
                                     server_obj.version) or server_obj.update_string.startswith('b-'):
            desc_text = "Updating"
            final_text = "Updated"
            "updating '$$'"
            "updated '$$' successfully"
        else:
            desc_text = "Reinstalling"
            final_text = "Reinstalled"
            "reinstalling '$$'"
            "reinstalled '$$' successfully"

        def before_func(*args):

            if not constants.app_online:
                self.execute_error(
                    "An internet connection is required to continue\n\nVerify connectivity and try again")

            elif not constants.check_free_space(telepath_data=server_obj._telepath_data):
                self.execute_error("Your primary disk is almost full\n\nFree up space and try again")

            else:
                telepath_data = server_obj._telepath_data
                if telepath_data:
                    response = constants.api_manager.request(
                        endpoint='/create/push_new_server',
                        host=telepath_data['host'],
                        port=telepath_data['port'],
                        args={'server_info': foundry.new_server_info}
                    )
                foundry.pre_server_update()

        def after_func(*args):
            foundry.post_server_update()
            self.open_server(server_obj.name, True, f"{final_text} '${server_obj.name}$' successfully",
                             launch=self.page_contents['launch'])

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
            'launch': False,

            # Page name
            'title': f"{desc_text} '{server_obj.name}'",

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
        java_text = 'Verifying Java Installation' if os.path.exists(paths.java) else 'Installing Java'
        function_list = [
            (java_text, functools.partial(constants.java_check, functools.partial(adjust_percentage, 30)), 0),
            ("Downloading 'server.jar'",
             functools.partial(foundry.download_jar, functools.partial(adjust_percentage, 30)), 0)
        ]

        download_addons = False
        needs_installed = False

        if foundry.new_server_info['type'] != 'vanilla':
            download_addons = foundry.new_server_info['addon_objects'] or foundry.new_server_info['server_settings'][
                'disable_chat_reporting'] or foundry.new_server_info['server_settings']['geyser_support'] or (
                                          foundry.new_server_info['type'] in ['fabric', 'quilt'])
            needs_installed = foundry.new_server_info['type'] in ['forge', 'neoforge', 'fabric', 'quilt']

        if needs_installed:
            function_list.append((f'Installing ${foundry.new_server_info["type"].title().replace("forge", "Forge")}$',
                                  functools.partial(foundry.install_server), 10 if download_addons else 20))

        if download_addons:
            function_list.append((f'{desc_text} add-ons', functools.partial(foundry.iter_addons,
                                                                            functools.partial(adjust_percentage,
                                                                                              10 if needs_installed else 20),
                                                                            True), 0))

        function_list.append(('Creating pre-install back-up', functools.partial(foundry.create_backup),
                              5 if (download_addons or needs_installed) else 10))

        function_list.append(('Applying new configuration', functools.partial(foundry.update_server_files),
                              10 if (download_addons or needs_installed) else 20))

        function_list.append(('Creating post-install back-up', functools.partial(foundry.create_backup),
                              5 if (download_addons or needs_installed) else 10))

        self.page_contents['function_list'] = tuple(function_list)


class UpdateModpackProgressScreen(ProgressScreen):

    # Only replace this function when making a child screen
    # Set fail message in child functions to trigger an error
    def contents(self):
        server_obj = constants.server_manager.current_server

        def before_func(*args):

            # First, clean out any existing server in temp folder
            os.chdir(constants.get_cwd())
            constants.safe_delete(paths.temp)

            if not constants.app_online:
                self.execute_error(
                    "An internet connection is required to continue\n\nVerify connectivity and try again")

            elif not constants.check_free_space(telepath_data=server_obj._telepath_data):
                self.execute_error("Your primary disk is almost full\n\nFree up space and try again")

            else:
                telepath_data = server_obj._telepath_data
                if telepath_data:
                    response = constants.api_manager.request(
                        endpoint='/create/push_new_server',
                        host=telepath_data['host'],
                        port=telepath_data['port'],
                        args={'server_info': foundry.new_server_info, 'import_info': foundry.import_data}
                    )
                foundry.pre_server_update()

        def after_func(*args):
            import_data = foundry.post_server_create(modpack=True)

            if self.telepath and import_data['readme']:
                import_data['readme'] = constants.telepath_download(self.telepath, import_data['readme'])['path']

            self.open_server(
                import_data['name'],
                True,
                f"Updated '${import_data['name']}$' successfully",
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
            'title': f"Updating '${server_obj.name}$'",

            # Header text
            'header': "Sit back and relax, it's automation time...",

            # Tuple of tuples for steps (label, function, percent)
            # Percent of all functions must total 100
            # Functions must return True, or default error will be executed
            'default_error': "There was an issue updating this modpack.\n\nThe required resources were unobtainable and will require manual installation.",

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
             functools.partial(foundry.scan_modpack, True, functools.partial(adjust_percentage, 20)), 0),
            ("Downloading 'server.jar'",
             functools.partial(foundry.download_jar, functools.partial(adjust_percentage, 10), True), 0),
            ('Installing modpack', functools.partial(foundry.install_server, None, True), 15),
            ('Creating pre-install back-up', functools.partial(foundry.create_backup, True), 10),
            ('Validating configuration',
             functools.partial(foundry.finalize_modpack, True, functools.partial(adjust_percentage, 5)), 0),
            ('Creating post-install back-up', functools.partial(foundry.create_backup, True), 10)
        ]

        self.page_contents['function_list'] = tuple(function_list)

# </editor-fold> ///////////////////////////////////////////////////////////////////////////////////////////////////////
