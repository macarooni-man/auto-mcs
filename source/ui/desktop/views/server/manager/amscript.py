from source.ui.desktop.views.server.manager.components import *



# amscript Manager ------------------------------------------------------------------------------------------------

def edit_script(edit_button, server_obj, script_path, download=True):
    "amscript-icon.png"

    # Override to download locally
    telepath_data = None
    telepath_script_dir = paths.telepath_script_temp
    if server_obj._telepath_data:
        telepath_data = constants.deepcopy(server_obj._telepath_data)
        telepath_data['headers'] = constants.api_manager._get_headers(telepath_data['host'], telepath_data['port'], True)
        if download:
            temp_folder = os.path.join(paths.telepath_script_temp, server_obj._telepath_data['host'], str(server_obj._telepath_data['port']))
            script_path = constants.telepath_download(server_obj._telepath_data, script_path, temp_folder)

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
            'syntax_func': constants.server_manager._script_object.is_valid,
            'protected': constants.server_manager._script_object.protected_variables,
            'events': constants.server_manager._script_object.valid_events
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

            def later(*_): edit_script(None, server_obj, script_path, download=False)
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
        self.create_button = WaitButton('Create in IDE', (0.5, 0.24), 'amscript.png', width=370, icon_offset=-150, disabled=True, click_func=on_click)
        buttons.append(self.create_button)
        buttons.append(ExitButton('Back', (0.5, 0.14), cycle=True))

        for button in buttons: float_layout.add_widget(button)

        menu_name = f"{server_obj.name}, amscript, Create script"
        float_layout.add_widget(generate_title(f"Script Manager: '{server_obj.name}'"))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)
        self.name_input.grab_focus()


class ServerAmscriptScreen(ListManageLayout, MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.menu_taskbar = None
        self.server = None
        self.reload_button = None
        self.directory_button = None
        self.path_button = None
        self.update_button = None

    def import_files(self, files=None, *args):
        if files is None:
            title = "Select amscripts (.ams)"
            files = file_popup("file", start_dir=paths.user_downloads, ext=["*.ams"], select_multiple=True, title=title)

        if not files:
            return

        script_manager = constants.server_manager.current_server.script_manager
        banner_text = ''

        for script in files:
            if script.endswith(".ams") and os.path.isfile(script):
                script = script_manager.import_script(script)
                if not script:
                    continue

                script_list = script_manager.return_single_list()
                self.gen_search_results(script_list, fade_in=False, highlight=script.hash, animate_scroll=True)

                # Switch pages if page is full
                if (not self.scroll_widget.data) and (len(script_list) > 0):
                    self.switch_page("right")

                # Show banner
                if len(files) == 1:
                    if len(script.title) < 26:
                        script_name = script.title
                    else:
                        script_name = script.title[:23] + "..."
                    banner_text = f"Imported '${script_name}$'"

                else:
                    banner_text = f"Imported ${len(files)}$ scripts"

        if banner_text:

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
                        banner_text,
                        "add-circle-sharp.png",
                        2.5,
                        {"center_x": 0.5, "center_y": 0.965}
                    ), 0
                )

    def generate_list_header(self, results):
        script_manager = self.server.script_manager

        script_count = len(results)
        enabled_count = len([script for script in results if script.enabled])
        disabled_count = len([script for script in results if not script.enabled])

        very_bold_font = os.path.join(paths.ui_assets, 'fonts', constants.fonts["very-bold"])
        header_content = f"{translate('Installed Scripts')}  [color=#494977]-[/color]  "

        if script_count == 0:
            header_content += f'[color=#6A6ABA]{translate("No items")}[/color]'

        elif script_count == 1:
            header_content += f'[font={very_bold_font}]1[/font] {translate("item")}'

        else:
            disabled_text = (
                f'/[color=#FF8793]{disabled_count}[/color]'
                if disabled_count > 0
                else ''
            )
            header_content += f'[font={very_bold_font}]{enabled_count:,}{disabled_text}[/font] {translate("items")}'

        if script_manager._hash_changed():
            icons = os.path.join(paths.ui_assets, 'fonts', constants.fonts['icons'])
            header_content = f"[color=#EFD49E][font={icons}]y[/font] {header_content}[/color]"

        return header_content

    def toggle_script(self, script, *args):
        script_manager = self.server.script_manager

        if len(script.title) < 26: script_name = script.title
        else:                      script_name = script.title[:23] + "..."

        script_manager.script_state(script, enabled=not script.enabled)

        self.gen_search_results(script_manager.return_single_list(), fade_in=False, highlight=script.hash, animate_scroll=True)

        if script_manager._hash_changed():
            Clock.schedule_once(
                functools.partial(
                    self.show_banner,
                    (0.937, 0.831, 0.62, 1),
                    "An amscript reload is required to apply changes",
                    "sync.png",
                    3,
                    {"center_x": 0.5, "center_y": 0.965}
                ),
                0
            )

        else:
            if script.enabled: banner_text = f"'${script_name}$' is now disabled"
            else:              banner_text = f"'${script_name}$' is now enabled"

            Clock.schedule_once(
                functools.partial(
                    self.show_banner,
                    (1, 0.5, 0.65, 1)
                    if script.enabled
                    else (0.553, 0.902, 0.675, 1),

                    banner_text,

                    "close-circle-sharp.png"
                    if script.enabled
                    else "checkmark-circle-sharp.png",

                    2.5,
                    {"center_x": 0.5, "center_y": 0.965}
                ),
                0
            )

    def toggle_all(self, enabled, *args):
        script_manager = self.server.script_manager

        for script in script_manager.return_single_list():
            if script.enabled != enabled:
                script_manager.script_state(script, enabled=enabled)

        self.gen_search_results(script_manager.return_single_list(), fade_in=False)

    def edit_script_item(self, script, *args):
        edit_script(None, self.server, script.path)

        if self.server.script_manager._hash_changed():
            Clock.schedule_once(
                functools.partial(
                    self.show_banner,
                    (0.937, 0.831, 0.62, 1),
                    "An amscript reload is required to apply changes",
                    "sync.png",
                    3,
                    {"center_x": 0.5, "center_y": 0.965}
                ),
                0
            )

    def delete_script(self, script, *args):

        def reprocess_page(*args):
            script_manager = self.server.script_manager
            script_manager.delete_script(script)
            constants.clear_script_cache(script.path)

            new_list = script_manager.return_single_list()
            self.gen_search_results(new_list, fade_in=True)

            Clock.schedule_once(functools.partial(self.search_bar.execute_search, self.search_bar.previous_search), 0)

            if script_manager._hash_changed():
                Clock.schedule_once(
                    functools.partial(
                        self.show_banner,
                        (0.937, 0.831, 0.62, 1),
                        "An amscript reload is required to apply changes",
                        "sync.png",
                        3,
                        {"center_x": 0.5, "center_y": 0.965}
                    ),
                    0
                )

            else:
                Clock.schedule_once(
                    functools.partial(
                        self.show_banner,
                        (1, 0.5, 0.65, 1),
                        f"'${script.title}$' was uninstalled",
                        "trash-sharp.png",
                        2.5,
                        {"center_x": 0.5, "center_y": 0.965}
                    ),
                    0
                )

            if not self.scroll_widget.data and len(new_list) > 0:
                self.switch_page("left")

        Clock.schedule_once(
            functools.partial(
                self.show_popup,
                "warning_query",
                f'Uninstall ${script.title}$',
                "Uninstalling this script will render it unavailable for every server.\n\nDo you want to permanently uninstall this script?",
                (None, functools.partial(reprocess_page))
            ),
            0
        )

    def update_script_item(self, script, *args):
        pass

    def prepare_list_results(self, results):
        return list(sorted(results, key=lambda script: (not script.enabled, script.title.lower())))

    def generate_list_button(self, script, index, fade_in, highlight):

        def primary_action(*args):
            Clock.schedule_once(
                functools.partial(
                    self.show_popup,
                    "info",
                    f'{script.title} - Details',
                    f"Version:  {script.version}\n"
                    f"Filename:  {script.file_name}\n"
                    f"Author:  {script.author}",
                    None,
                    None,
                    silent = True,
                ), 0
            )

        toggle_options = (
            {"force_color": [[(0.05, 0.05, 0.1, 1), (0.6, 0.6, 1, 1)], "pink"]}
            if script.enabled else
            {"force_color": [[(0.05, 0.08, 0.07, 1), (0.6, 0.6, 1, 1)], "green"]}
        )

        update_action = (
            (
                "update",
                "arrow-update.png",
                functools.partial(self.update_script_item, script),
                {"force_color": [[(0.05, 0.08, 0.07, 1), (0.5, 0.9, 0.7, 1)], "green"]}
            )
            if script.update.get('url') else
            (
                "up to date",
                "checkmark-sharp.png",
                None
            )
        )

        actions = [
            (
                "edit",
                "edit-sharp.png",
                functools.partial(self.edit_script_item, script)
            ),

            # update_action,

            (
                "disable" if script.enabled else "enable",
                "close-circle-sharp.png" if script.enabled else "checkmark-circle-sharp.png",
                functools.partial(self.toggle_script, script),
                toggle_options
            ),
            (
                "delete",
                "trash-sharp.png",
                functools.partial(self.delete_script, script),
                {"force_color": [[(0.05, 0.05, 0.1, 1), (0.6, 0.6, 1, 1)], "pink"]}
            )
        ]

        banner = (
            BannerObject(
                pos_hint = {"center_x": 0.5, "center_y": 0.5},
                size = (100, 30),
                color = (0.647, 0.839, 0.969, 1),
                text = script.update['version'],
                icon = "arrow-up-circle.png",
                icon_side = "left"
            )
            if script.update.get('version')
            else None
        )

        return {
            'properties': script,
            'enabled': script.enabled,
            'banner': banner,
            'actions': actions,
            'fade_in': fade_in,
            'highlight': highlight,
            'click_function': primary_action
        }

    def generate_menu(self, **kwargs):
        self.server = constants.server_manager.current_server

        # Return if no free space
        if disk_popup('ServerViewScreen', telepath_data=self.server._telepath_data):
            return

        # Generate buttons on page load
        script_count = len(self.server.script_manager.return_single_list())
        very_bold_font = os.path.join(paths.ui_assets, 'fonts', constants.fonts["very-bold"])
        header_content = f"{translate('Installed Scripts')}  [color=#494977]-[/color]  " + (f'[color=#6A6ABA]{translate("No items")}[/color]' if script_count == 0 else f'[font={very_bold_font}]1[/font] {translate("item")}' if script_count == 1 else f'[font={very_bold_font}]{script_count}[/font] {translate("items")}')
        updates_available = bool(self.server.script_manager.get_update_list())

        self.update_button = (
            RelativeIconButton(
                '\n\n\nupdate all', {"center_x": 0.5, "center_y": 0.5}, None, (None, None), 'arrow-update.png',
                # click_func = self.update_all_scripts,
                force_color = [[(0.05, 0.08, 0.07, 1), (0.5, 0.9, 0.7, 1)], 'green']
            )
            if updates_available else
            RelativeIconButton(
                '\n\n\nup to date', {"center_x": 0.5, "center_y": 0.5}, None, (None, None), 'checkmark-sharp.png',
                clickable = False
            )
        )
        actions = [
            RelativeIconButton(
                '\n\n\nenable all', {"center_x": 0.5, "center_y": 0.5}, None, (None, None),
                'checkmark-circle-sharp.png',
                click_func = functools.partial(self.toggle_all, True),
                force_color = [[(0.05, 0.08, 0.07, 1), (0.6, 0.6, 1, 1)], 'green']
            ),
            RelativeIconButton(
                '\n\n\ndisable all', {"center_x": 0.5, "center_y": 0.5}, None, (None, None), 'close-circle-sharp.png',
                click_func = functools.partial(self.toggle_all, False),
                force_color = [[(0.05, 0.05, 0.1, 1), (0.6, 0.6, 1, 1)], 'pink']
            ),

            # self.update_button
        ]

        self.generate_list(header_content, "Manage scripts below", self.server.script_manager.filter_scripts, allow_empty=True, actions=actions)

        buttons = []
        float_layout = self._layout

        bottom_buttons = RelativeLayout()
        bottom_buttons.size_hint_max_x = 512
        bottom_buttons.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        bottom_buttons.add_widget(MainButton('Import', (0, 0.202), 'download-outline.png', width=245, icon_offset=-115, auto_adjust_icon=True))
        bottom_buttons.add_widget(MainButton('Create New', (0.5, 0.202), '', width=245, icon_offset=-115, auto_adjust_icon=False))
        bottom_buttons.add_widget(MainButton('Download', (1, 0.202), 'cloud-download-outline.png', width=245, icon_offset=-115, auto_adjust_icon=True))
        buttons.append(ExitButton('Back', (0.5, -1), cycle=True))

        for button in buttons: float_layout.add_widget(button)
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
            open_folder(paths.scripts)

        self.directory_button = IconButton('open directory', {}, (70, 110), (None, None), 'folder.png', anchor='right', click_func=open_dir, text_offset=(10, 0))
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
                    Clock.schedule_once(functools.partial(self.gen_search_results, self.server.script_manager.return_single_list()), 0)

                dTimer(0, timer).start()

            self.reload_button = IconButton('reload scripts', {}, (125, 110), (None, None), 'reload-sharp.png', clickable=self.server.running, anchor='right', click_func=reload_scripts, text_offset=(10, 50))
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


class ServerAmscriptSearchScreen(ListDiscoverLayout, MenuBackground):
    discover_fallback_icon = 'amscript.png'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.available_header = "Available Scripts"

    def before_list_render(self, results):
        script_manager = constants.server_manager.current_server.script_manager
        installed = {
            str(script.title or '').strip().lower()
            for script in script_manager.return_single_list()
        }

        for script in results:
            script.installed = str(script.title or '').strip().lower() in installed

    def get_discover_banners(self, script, release):
        script_manager = constants.server_manager.current_server.script_manager
        installed = self.find_discover_match(script, script_manager.return_single_list())

        return [{
            'size': (125, 32),
            'color': (0.553, 0.902, 0.675, 1),
            'text': 'installed',
            'icon': 'checkmark-circle.png',
            'icon_side': 'right'
        }] if installed else []

    def generate_list_button(self, script, index, fade_in, highlight):
        return {
            'properties': script,
            'installed': script.installed,
            'fade_in': fade_in,
            'click_function': functools.partial(self.select_discover_item, script)
        }

    def load_discover_item(self, script):
        script_manager = constants.server_manager.current_server.script_manager
        installed = self.find_discover_match(script, script_manager.return_single_list())

        version = str(script.version or 'Unknown')
        versions = [(version, script)]

        selected = self.get_discover_selected(versions, installed)
        release = self.get_discover_release(versions, selected)

        return {
            'item': script,
            'title': script.title,
            'author': script.author or 'Unknown',
            'description': script.description,
            'icon_url': None,
            'fallback_icon': 'amscript.png',
            'project_url': getattr(script, 'url', None),
            'banners': self.get_discover_banners(script, release),
            'versions': versions,
            'selected': selected,
            'installed': installed,
            'installed_version': getattr(installed, 'version', None) if installed else None,
            'allow_remove': True
        }

    def perform_discover_action(self, script, release, mode):
        script_manager = constants.server_manager.current_server.script_manager
        installed = self.find_discover_match(script, script_manager.return_single_list())

        if len(script.title) < 26: script_name = script.title
        else:                      script_name = script.title[:23] + '...'

        if mode == 'delete':
            if not installed:
                return False

            path = installed.path
            success = script_manager.delete_script(installed)

            if success:
                constants.clear_script_cache(path)

        else:
            script_manager.download_script(release)
            success = bool(self.find_discover_match(script, script_manager.return_single_list()))

        if not success:
            return False

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

        elif mode == 'delete':
            Clock.schedule_once(
                functools.partial(
                    self.show_banner,
                    (1, 0.5, 0.65, 1),
                    f"'${script_name}$' was uninstalled",
                    "trash-sharp.png",
                    2.5,
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
                ), 0
            )

        return True

    def generate_menu(self, **kwargs):
        server_obj = constants.server_manager.current_server
        script_manager = server_obj.script_manager

        self.generate_list(
            translate("Script Search"),
            "search for scripts above",
            script_manager.search_scripts,
            empty_text = "there are no items to display"
        )

        buttons = []
        float_layout = self._layout

        buttons.append(self.discover_back_button(cycle=True))

        for button in buttons: float_layout.add_widget(button)

        server_name = server_obj.name
        menu_name = f"{server_name}, amscript, Download"
        float_layout.add_widget(generate_title(f"Script Manager: '{server_name}'"))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)

        Clock.schedule_once(functools.partial(self.search_bar.execute_search, ""), 0)
