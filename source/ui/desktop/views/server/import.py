from source.ui.desktop.views.templates import *
from source.ui.desktop.widgets.base import *



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

    # Callback for directory inputs
    def _update_server(self, path: str):
        if self.name_input:
            self.name_input.selected_server = os.path.abspath(path) if isinstance(path, str) else os.path.abspath(path[0])
            self.name_input.update_server()

    def load_input(self, input_type, *args):
        self.input_type = input_type
        self.button_layout.clear_widgets()
        self.page_counter.clear_widgets()
        self.layout.remove_widget(self.page_counter)

        # Change the input based on input_type
        self.page_counter = PageCounter(2, 2, (0, 0.818))
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
            start_path = paths.user_downloads if os.path.isdir(paths.user_downloads) else paths.user_home
            self.button_layout.add_widget(InputButton('Browse...', (0.5, 0.5 + offset), ('dir', start_path), input_callback=self._update_server, title='Select a Server Folder'))

        elif input_type == "backup":
            self.name_input = ServerImportBackupInput(pos_hint={"center_x": 0.5, "center_y": 0.5 + offset})
            self.button_layout.add_widget(self.name_input)
            start_path = paths.backups if os.path.isdir(paths.backups) else paths.user_downloads if os.path.isdir(paths.user_downloads) else paths.user_home
            self.button_layout.add_widget(InputButton('Browse...', (0.5, 0.5 + offset), ('file', start_path), input_callback=self._update_server, title='Select an auto-mcs back-up file', ext_list=['*.amb', '*.tgz']))

        # Auto-launch popup
        try:
            for item in self.button_layout.children[0].children:
                if item.id == "input_button" and not telepath_data:
                    Clock.schedule_once(item.force_click, 0)
                    Clock.schedule_once(item.on_leave, 0.01)
                    break
        except AttributeError: pass

        # def set_import_path(*args):
        #     for item in self.button_layout.children:
        #         if "ServerImport" in item.__class__.__name__:
        #             foundry.import_data['path'] = item.selected_server

        self.button_layout.add_widget(InputLabel(pos_hint={"center_x": 0.5, "center_y": 0.58 + offset}))
        self.next_button = NextButton('Next', (0.5, 0.24), True, next_screen='ServerImportProgressScreen')
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
            def go_to_modpack(*a): utility.screen_manager.current = 'ServerImportModpackScreen'
            self.layout.add_widget(HeaderText("What do you wish to import?", '', (0, 0.81)))
            buttons.append(MainButton('Import external server', (0.5, 0.55), 'folder-outline.png', click_func=functools.partial(self.load_input, 'external')))
            buttons.append(MainButton('Import Auto-MCS back-up', (0.5, 0.4), 'backup-icon.png', click_func=functools.partial(self.load_input, 'backup')))
            self.layout.add_widget(ExitButton('Back', (0.5, 0.14), cycle=True))
            self.page_counter = PageCounter(1, 2, (0, 0.818))
            self.add_widget(self.page_counter)

        self.button_layout = FloatLayout()
        for button in buttons: self.button_layout.add_widget(button)

        self.layout.add_widget(self.button_layout)
        self.layout.add_widget(generate_title('Import Server'))
        self.layout.add_widget(generate_footer('Import server'))

        self.add_widget(self.layout)


class ServerImportProgressScreen(ProgressScreen):

    # Only replace this function when making a child screen
    # Set fail message in child functions to trigger an error
    def contents(self):
        import_name = foundry.import_data['name']
        open_after = functools.partial(self.open_server, import_name, True, f"'${import_name}$' was imported successfully")

        def before_func(*args):

            if not constants.app_online:
                self.execute_error("An internet connection is required to continue\n\nVerify connectivity and try again")

            elif not constants.check_free_space(telepath_data=foundry.new_server_info['_telepath_data']):
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

        is_backup_file = ((foundry.import_data['path'].endswith(".tgz") or foundry.import_data['path'].endswith(".amb")) and os.path.isfile(foundry.import_data['path']))

        # Create function list
        java_text = 'Verifying Java Installation' if os.path.exists(paths.java) else 'Installing Java'
        function_list = [

            # Server import requires all Java builds because it generally has to run the server to find the version
            (java_text, functools.partial(constants.java_check, functools.partial(adjust_percentage, 30)), 0),
            ('Importing server', functools.partial(foundry.scan_import, is_backup_file, functools.partial(adjust_percentage, 30)), 0),
            ('Validating configuration', functools.partial(foundry.finalize_import, functools.partial(adjust_percentage, 20)), 0),
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

            def download_modpack(*a): utility.screen_manager.current = 'ServerImportModpackSearchScreen'
            buttons.append(MainButton('Download a Modpack', (0.5, 0.576 + offset), 'download-outline.png', width=528, click_func=download_modpack))

            start_path = paths.user_downloads if os.path.isdir(paths.user_downloads) else paths.user_home
            buttons.append(InputLabel(pos_hint={"center_x": 0.5, "center_y": 0.505 + offset}))
            server_input = ServerImportModpackInput(pos_hint={"center_x": 0.5, "center_y": 0.44 + offset})
            buttons.append(server_input)
            def _update_server(path: str): server_input.selected_server = os.path.abspath(path) if isinstance(path, str) else os.path.abspath(path[0]); server_input.update_server()
            buttons.append(InputButton('Browse...', (0.5, 0.44 + offset), ('file', start_path), input_callback=_update_server, title='Select a modpack', ext_list=['*.zip', '*.mrpack']))

            self.layout.add_widget(ExitButton('Back', (0.5, 0.14), cycle=True))

            def remove_page(*a):
                if 'ServerImportScreen' in utility.screen_manager.screen_tree:
                    utility.screen_manager.screen_tree.remove('ServerImportScreen')

            Clock.schedule_once(remove_page, 0.1)
            self.page_counter = PageCounter(2, 2, (0, 0.818))
            self.add_widget(self.page_counter)

        self.button_layout = FloatLayout()
        for button in buttons: self.button_layout.add_widget(button)

        self.layout.add_widget(self.button_layout)

        self.next_button = NextButton('Next', (0.5, 0.24), True, next_screen='ServerImportModpackProgressScreen')
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
                self.execute_error("An internet connection is required to continue\n\nVerify connectivity and try again")

            elif not constants.check_free_space(telepath_data=foundry.new_server_info['_telepath_data']):
                self.execute_error("Your primary disk is almost full\n\nFree up space and try again")

            else: foundry.pre_server_create()

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
            if final < 0: final = original
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

            # Server import requires all Java builds because it generally has to run the server to find the version
            (java_text, functools.partial(constants.java_check, functools.partial(adjust_percentage, 30)), 0),
            ('Validating modpack', functools.partial(foundry.scan_modpack, False, functools.partial(adjust_percentage, 20)), 0),
            ("Downloading 'server.jar'", functools.partial(foundry.download_jar, functools.partial(adjust_percentage, 15), True), 0),
            ('Installing modpack', functools.partial(foundry.install_server, None, True), 15),
            ('Validating configuration', functools.partial(foundry.finalize_modpack, False, functools.partial(adjust_percentage, 10)), 0),
            ('Creating initial back-up', functools.partial(foundry.create_backup, True), 10)
        ]

        self.page_contents['function_list'] = tuple(function_list)


class ServerImportModpackSearchScreen(ListSearchLayout, MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.provider = addons.ModrinthModpackProvider()

    def generate_list_button(self, modpack, index, fade_in, highlight):

        def load_modpack(*args):
            try:
                selected_button = self.get_list_button(index)
                if selected_button.properties:
                    if not selected_button.properties.description:
                        selected_button.properties = self.provider.get_modpack_info(modpack)

                Clock.schedule_once(functools.partial(selected_button.loading, False), 1)
                return (selected_button.properties, selected_button.installed)

            except:
                Clock.schedule_once(
                    functools.partial(
                        self.show_banner,
                        (1, 0.5, 0.65, 1),
                        "Failed to load modpack",
                        "close-circle-sharp.png",
                        2.5,
                        {"center_x": 0.5, "center_y": 0.965}
                    ),
                    0
                )

        def install_modpack(*args):

            def move_to_next_page(modpack_object, *args):
                modpack_object = self.provider.get_modpack_url(modpack_object)

                foundry.import_data = {
                    'name': modpack_object.name,
                    'url': modpack_object.download_url
                }

                def progress(*args):
                    utility.screen_manager.current = "ServerImportModpackProgressScreen"

                Clock.schedule_once(progress, 0.4)

            selected_button = self.get_list_button(index)
            dTimer(0, functools.partial(move_to_next_page, selected_button.properties)).start()

        def view_modpack(*args):
            selected_button = self.get_list_button(index)
            selected_button.loading(True)

            Clock.schedule_once(
                functools.partial(
                    self.show_popup,
                    "addon",
                    " ",
                    " ",
                    (None, functools.partial(install_modpack)),
                    functools.partial(load_modpack)
                ),
                0
            )

        return {
            'properties': modpack,
            'installed': False,
            'fade_in': fade_in,
            'click_function': view_modpack
        }

    def generate_menu(self, **kwargs):
        self.generate_list(
            translate("Modpack Search"),
            "search for modpacks above",
            self.provider.search_modpacks,
            empty_text = "there are no items to display"
        )

        buttons = []
        float_layout = self._layout

        buttons.append(ExitButton('Back', (0.5, 0.12), cycle=True))

        for button in buttons: float_layout.add_widget(button)

        menu_name = "Install a modpack, Download"
        float_layout.add_widget(generate_title("Download Modpack"))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)

        Clock.schedule_once(functools.partial(self.search_bar.execute_search, ""), 0)


# </editor-fold> ///////////////////////////////////////////////////////////////////////////////////////////////////////
