from ui.desktop.views.server.manager.editor import open_config_file
from source.ui.desktop.views.server.manager.components import *
from source.core.server import playit


# ---------------------------------------------- Server Settings Screen ------------------------------------------------

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
            utility.screen_manager.current_screen.ip_input.text = str(server_obj.port) if str(server_obj.port) != '25565' else ''

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

        # Generate buttons on page load
        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'
        float_layout.add_widget(InputLabel(pos_hint={"center_x": 0.5, "center_y": 0.67}))
        float_layout.add_widget(HeaderText("What world would you like to use?", 'This action will automatically create a back-up',(0, 0.83)))
        float_layout.add_widget(ServerWorldInput(pos_hint={"center_x": 0.5, "center_y": 0.58}))
        float_layout.add_widget(ServerSeedInput(pos_hint={"center_x": 0.5, "center_y": 0.462}))
        buttons.append(InputButton('Browse...', (0.5, 0.58), ('dir', paths.minecraft_saves if os.path.isdir(paths.minecraft_saves) else paths.user_downloads), input_name='ServerWorldInput', title='Select a World File'))

        def change_type(type_name): self.new_type = type_name

        server_version = server_obj.version
        original_type = self.new_type = server_obj.server_properties.get('level-type', 'default').replace(r'\:', ':').lower().strip()

        if constants.version_check(server_version, '>=', "1.1"):
            options = ['normal', 'superflat']

            if constants.version_check(server_version, '>=', "1.3.1"):
                options.append('large biomes')

            if constants.version_check(server_version, '>=', "1.7.2"):
                options.append('amplified')

            if not self.new_type.startswith('minecraft:') and self.new_type not in options:
                options.insert(0, self.new_type)

            default_name = self.new_type.replace("default", "normal").replace("flat", "superflat").replace("large_biomes", "large biomes").replace('minecraft:', '').strip().lower()
            float_layout.add_widget(DropButton(default_name, (0.5, 0.462), options_list=options, input_name='ServerSettingsLevelTypeInput', x_offset=41, custom_func=change_type))

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
                    try: utility.screen_manager.current_screen.world_button.loading(True)
                    except: pass
                Clock.schedule_once(update_button, 0)


                # If telepath, upload world here and return path
                error: bool = False
                new_type = self.new_type if original_type != self.new_type else None,
                if server_obj._telepath_data:
                    telepath_data = server_obj._telepath_data
                    if self.new_world != 'world': new_path = constants.telepath_upload(telepath_data, self.new_world)['path']
                    else:                         new_path = 'world'

                    constants.api_manager.request(
                        endpoint = '/main/update_world',
                        host = telepath_data['host'],
                        port = telepath_data['port'],
                        args = {
                            'path': new_path,
                            'new_type': new_type,
                            'new_seed': self.new_seed,
                            'telepath': True
                        }
                    )
                    constants.api_manager.request(endpoint='/main/clear_uploads', host=telepath_data['host'], port=telepath_data['port'])

                # If local, update normally
                else:
                    try: manager.update_world(self.new_world, new_type, self.new_seed)
                    except Exception as e:
                        send_log(f"error updating world with '{self.new_world}'", 'error')
                        error = True

                def update_ui(*a):
                    try: utility.screen_manager.current_screen.world_button.loading(False)
                    except: pass

                    if not error:
                        utility.screen_manager.current_screen.show_banner(
                            (0.553, 0.902, 0.675, 1),
                            f"The server world has been changed successfully",
                            "checkmark-circle-outline.png",
                            2.5,
                            {"center_x": 0.5, "center_y": 0.965}
                        )

                    else:
                        utility.screen_manager.current_screen.show_banner(
                            (1, 0.5, 0.65, 1),
                            f"The server world failed to update",
                            "close-circle-outline.png",
                            2.5,
                            {"center_x": 0.5, "center_y": 0.965}
                        )

                Clock.schedule_once(update_ui, 0)

            def _update_screen(*a):
                utility.screen_manager.previous_screen()
                utility.screen_manager.screen_tree.pop(-1)
                try:
                    delete_button = utility.screen_manager.current_screen.delete_button
                    utility.screen_manager.current_screen.scroll_widget.scroll_to(delete_button, animate=False)
                except: pass
            Clock.schedule_once(_update_screen, 0)
            dTimer(0, change_thread).start()

        self.next_button = NextButton('Next', (0.5, 0.24), False, next_screen='ServerSettingsScreen', click_func=change_world)
        buttons.append(self.next_button)
        buttons.append(ExitButton('Back', (0.5, 0.14), cycle=True))

        for button in buttons: float_layout.add_widget(button)

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
                                            child.remove_widget([relative for relative in child.children if relative.__class__.__name__ == 'DropButton'][0])
                                    except IndexError as e:
                                        send_log(f'{self.__class__.__name__}.toggle_new', "'DropButton' does not exist, can't remove", 'error')

                            elif item.id == 'Create new world instead':
                                current_input = 'button'
                                if self.new_world == 'world': child.remove_widget(item)
                        except AttributeError: continue

                    # Show button if true
                    if boolean_value and self.new_world != 'world' and current_input == 'input':
                        child.add_widget(MainButton('Create new world instead', (0.5, 0.442), 'add-circle-outline.png', width=530))

                    # Show seed input, and clear world text
                    elif self.new_world == 'world' and current_input == 'button':
                        child.add_widget(ServerSeedInput(pos_hint={"center_x": 0.5, "center_y": 0.442}))

                        if constants.version_check(server_version, '>=', "1.1"):
                            options = ['normal', 'superflat']
                            if constants.version_check(server_version, '>=', "1.3.1"):
                                options.append('large biomes')
                            if constants.version_check(server_version, '>=', "1.7.2"):
                                options.append('amplified')
                            default_name = self.new_type.replace("default", "normal").replace("flat", "superflat").replace("large_biomes", "large biomes")
                            child.add_widget(DropButton(default_name, (0.5, 0.442), options_list=options, input_name='ServerSettingsLevelTypeInput', x_offset=41))
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
                scroll_top.resize(); scroll_bottom.resize()

            Clock.schedule_once(update_grid, 0)

        self.resize_bind = lambda *_: Clock.schedule_once(functools.partial(resize_scroll, scroll_widget, scroll_layout, scroll_anchor), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        scroll_layout.bind(minimum_height=scroll_layout.setter('height'))
        scroll_layout.id = 'scroll_content'

        # Scroll gradient
        scroll_top = ScrollBackground(pos_hint={"center_x": 0.5, "center_y": 0.84}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, 60))
        scroll_bottom = ScrollBackground(pos_hint={"center_x": 0.5, "center_y": 0.17}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, -60))

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
            paragraph = ParagraphObject(size=(530, content_height), name=name, content=' ', font_size=content_size, font=pgh_font)
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

            self.config_button = WaitButton("Edit 'server.properties'", (0.5, 0.5), 'document-text-outline.png', click_func=edit_server_properties)
        else:
            # Edit config button
            def open_config_menu(*args): utility.screen_manager.current = 'ServerConfigScreen'

            self.config_button = WaitButton("Edit Configuration Files", (0.5, 0.5), 'document-text-outline.png', click_func=open_config_menu)

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
                        open_folder(location)
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
            self.download_button = WaitButton('Download Server', (0.5, 0.5), 'cloud-download-sharp.png', click_func=download_server)
            sub_layout.add_widget(self.download_button)
            general_layout.add_widget(sub_layout)

        else:

            # Open server directory
            def open_server_dir(*args):
                open_folder(server_obj.server_path)
                Clock.schedule_once(self.open_path_button.button.on_leave, 0.5)

            sub_layout = ScrollItem()
            self.open_path_button = WaitButton('Open Server Directory', (0.5, 0.5), 'folder-outline.png', click_func=open_server_dir)
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
        sub_layout.add_widget(BlankInput(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="memory usage  (GB)"))
        sub_layout.add_widget(NumberSlider(start_value, (0.5, 0.5), input_name='RamInput', limits=(min_limit, max_limit), min_icon='auto-icon.png', function=change_limit))
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
        self.ip_input = ServerPortInput(pos_hint={'center_x': 0.5, 'center_y': 0.5}, text=process_ip_text(server_obj=server_obj))
        self.ip_input._allow_ip = not proxy_state
        self.ip_input.size_hint_max_x = 435
        sub_layout.add_widget(self.ip_input)
        network_layout.add_widget(sub_layout)

        # Playit toggle/install button
        def add_switch(index=0, fade=False, *a):
            sub_layout = ScrollItem()
            input_border = BlankInput(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text='enable proxy (playit)', disabled=(not constants.app_online))
            sub_layout.add_widget(input_border)

            # Only show 'open panel' button if a guest account exists
            if os.path.exists(playit.manager.toml_path):

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
                open_panel_button = RelativeIconButton('open panel', {'center_x': 2.65, 'center_y': 0.5}, (0, 0), (None, None), 'open.png', clickable=True, click_func=open_login, text_offset=(20, 50), anchor='right')
                open_panel_button.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
                open_panel_button.size_hint_max = (50, 50)
                open_panel_button.opacity = 0.8
                open_panel_button.text.text = '\n\n\nopen panel'
                sub_layout.add_widget(open_panel_button)

            # Add toggle button to enable/disable widget
            sub_layout.add_widget(SwitchButton('proxy', (0.5, 0.5), custom_func=toggle_proxy, default_state=proxy_state, disabled=(not constants.app_online)))

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
                    self.show_popup('warning', 'Error', 'An internet connection is required to install playit\n\nPlease check your connection and try again', (None))

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
        supported  = (constants.version_check(server_obj.version, ">=", "1.13.2")
                     and server_obj.type.lower() in ['spigot', 'paper', 'purpur', 'fabric', 'quilt', 'neoforge'])
        hint_text  = "bedrock support (geyser)" if supported else "geyser (unsupported server)"
        disabled   = not (constants.app_online and supported)
        sub_layout.add_widget(BlankInput(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text=hint_text, disabled=disabled))
        sub_layout.add_widget(SwitchButton('geyser', (0.5, 0.5), custom_func=toggle_geyser, disabled=disabled, default_state=(server_obj.geyser_enabled) and not disabled))
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
        sub_layout.add_widget(BlankInput(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text='automatic updates', disabled=disabled))
        sub_layout.add_widget(SwitchButton('auto-update', (0.5, 0.5), custom_func=toggle_auto_update, default_state=server_obj.auto_update == 'true', disabled=disabled))
        update_layout.add_widget(sub_layout)

        disabled = server_obj.running or not constants.app_online

        # Updates server
        def update_server(*a):
            if server_obj.is_modpack == 'mrpack':
                update_url = ''
                if server_obj._telepath_data:
                    try:
                        update_url = constants.server_manager.get_telepath_update(server_obj._telepath_data, server_obj.name)['updateUrl']
                    except KeyError: pass

                else:
                    update_url = constants.server_manager.update_list[server_obj.name]['updateUrl']

                if update_url:
                    foundry.import_data = {'name': server_obj.name, 'url': update_url}
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
                needs_update = constants.server_manager.get_telepath_update(server_obj._telepath_data, server_obj.name)['needsUpdate']
            except KeyError: pass

        else:
            needs_update = constants.server_manager.update_list[server_obj.name]['needsUpdate']

        if server_obj.is_modpack == 'zip':
            def select_file(*a):
                zip_file = file_popup("file", start_dir=paths.user_downloads, ext=["*.zip", "*.mrpack"], input_name=None, select_multiple=True, title='Select a modpack update')
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
            self.update_button = WaitButton("Update from '.zip'", (0.5, 0.5), 'modpack.png', disabled=disabled, click_func=select_file)


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
            self.update_button = WaitButton(f"Update to ${server_obj.update_string}$", (0.5, 0.5), 'arrow-up-circle-outline.png', disabled=disabled, click_func=update_server)

        # No updates are available
        else:
            self.update_button = WaitButton('Up to date', (0.5, 0.5), 'checkmark-circle.png', disabled=True)
            Animation.stop_all(self.update_button.icon)
            self.update_button.icon.opacity = 0.5

        sub_layout.add_widget(self.update_button)
        try:
            if self.update_label: sub_layout.add_widget(self.update_label)
        except: pass
        update_layout.add_widget(sub_layout)

        # Change 'server.jar' button
        def migrate_server(*a):
            foundry.new_server_init()
            foundry.new_server_info['type'] = server_obj.type
            foundry.new_server_info['version'] = server_obj.version
            utility.screen_manager.current = 'MigrateServerTypeScreen'

        sub_layout = ScrollItem()
        sub_layout.add_widget(WaitButton("Change 'server.jar'", (0.5, 0.5), 'swap-horizontal-outline.png', disabled=disabled or server_obj.is_modpack, click_func=migrate_server))
        update_layout.add_widget(sub_layout)

        create_paragraph('updates', update_layout, 0, 0.555)

        # --------------------------------------------------------------------------------------------------------------



        # ----------------------------------------------- Transilience -------------------------------------------------

        transilience_layout = GridLayout(cols=1, spacing=10, size_hint_max_x=1050, size_hint_y=None, padding=[0, 0, 0, 0])

        def rename_server(name, *args):
            def loading_screen(*a): utility.screen_manager.current = 'BlurredLoadingScreen'

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
        self.rename_input = ServerRenameInput(pos_hint={'center_x': 0.5, 'center_y': 0.5}, text=server_obj.name, on_validate=rename_thread, disabled=server_obj.running)
        self.rename_input.size_hint_max_x = 435
        sub_layout.add_widget(self.rename_input)
        transilience_layout.add_widget(sub_layout)

        if server_obj.running: input_label.update_text("Server is running", True)

        # Change world file
        def change_world(*a):
            if constants.server_manager.current_server:
                utility.screen_manager.current = 'ServerWorldScreen'

        sub_layout = ScrollItem()
        self.world_button = WaitButton("Change world file", (0.5, 0.5), 'world.png', click_func=change_world, disabled=server_obj.running)
        sub_layout.add_widget(self.world_button)
        transilience_layout.add_widget(sub_layout)

        # Delete server button
        def delete_server(*args):
            def loading_screen(*a): utility.screen_manager.current = 'BlurredLoadingScreen'

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
        self.delete_button = ColorButton('Delete Server', (0.5, 0.5), 'trash-sharp.png', click_func=prompt_delete, color=(1, 0.5, 0.65, 1), disabled=server_obj.running)
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

        for button in buttons: float_layout.add_widget(button)

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

        float_layout.add_widget(HeaderText("Which distribution would you like to switch to?", 'This action will automatically create a back-up', (0, 0.89)))

        # Create UI buttons
        self.next_button = NextButton('Next', (0.5, 0.21), False, next_screen='MigrateServerVersionScreen')
        buttons.append(self.next_button)
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
        row_top.add_widget(BigIconButton('runs most plug-ins, optimized', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None), 'paper', clickable=True, selected=('paper' == foundry.new_server_info['type'])))
        row_top.add_widget(BigIconButton('default, stock experience', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None), 'vanilla', clickable=True, selected=('vanilla' == foundry.new_server_info['type'])))
        row_top.add_widget(BigIconButton('modded experience', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None), 'forge', clickable=True, selected=('forge' == foundry.new_server_info['type'])))
        row_bottom.add_widget(BigIconButton('performant fork of paper', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None), 'purpur', clickable=True, selected=('purpur' == foundry.new_server_info['type'])))
        row_bottom.add_widget(BigIconButton('modern mod platform', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None), 'fabric', clickable=True, selected=('fabric' == foundry.new_server_info['type'])))
        row_bottom.add_widget(BigIconButton('view more options', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None), 'more', clickable=True, selected=False))
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
        row_top.add_widget(BigIconButton('modern $Forge$ implementation', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None), 'neoforge', clickable=True, selected=('neoforge' == foundry.new_server_info['type'])))
        row_top.add_widget(BigIconButton('enhanced fork of $Fabric$', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None), 'quilt', clickable=True, selected=('quilt' == foundry.new_server_info['type'])))
        row_top.add_widget(BigIconButton('requires tuning, but efficient', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None), 'spigot', clickable=True, selected=('spigot' == foundry.new_server_info['type'])))
        row_bottom.add_widget(BigIconButton('legacy, supports plug-ins', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None), 'craftbukkit', clickable=True, selected=('craftbukkit' == foundry.new_server_info['type'])))
        row_bottom.add_widget(BigIconButton('view more options', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None), 'more', clickable=True, selected=False))
        self.content_layout_2.add_widget(row_top)
        self.content_layout_2.add_widget(row_bottom)

        for button in buttons: float_layout.add_widget(button)

        float_layout.add_widget(self.content_layout_1)
        float_layout.add_widget(self.content_layout_2)
        float_layout.add_widget(PageCounter(1, 2, (0, 0.86)))
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
            float_layout.add_widget(HeaderText("Changing the 'server.jar' requires an internet connection", '', (0, 0.6)))
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
                    def main_thread(*b): utility.screen_manager.current = "MigrateServerProgressScreen"
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
                    if version_data[0] and not version_data[2] and utility.screen_manager.current == 'MigrateServerVersionScreen':
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
            float_layout.add_widget(PageCounter(2, 2, (0, 0.77)))
            float_layout.add_widget(HeaderText("What version of Minecraft would you like to switch to?", f'Current version:  ${server_obj.version}$', (0, 0.8)))
            self.final_button = WaitButton("Change 'server.jar'", (0.5, 0.24), 'swap-horizontal-outline.png', click_func=migrate_server)
            float_layout.add_widget(ServerVersionInput(pos_hint={"center_x": 0.5, "center_y": 0.49}, text=foundry.new_server_info['version'], enter_func=migrate_server))
            self.add_widget(self.final_button)
            buttons.append(ExitButton('Back', (0.5, 0.14), cycle=True))

        for button in buttons: float_layout.add_widget(button)

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

        elif constants.version_check(foundry.new_server_info['version'], '>', server_obj.version) or server_obj.update_string.startswith('b-'):
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
                self.execute_error("An internet connection is required to continue\n\nVerify connectivity and try again")

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
            self.open_server(server_obj.name, True, f"{final_text} '${server_obj.name}$' successfully", launch=self.page_contents['launch'])

        # Original is percentage before this function, adjusted is a percent of hooked value
        def adjust_percentage(*args):
            original = self.last_progress
            adjusted = args[0]
            total = args[1] * 0.01
            final = original + round(adjusted * total)
            if final < 0: final = original
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
            download_addons = foundry.new_server_info['addon_objects'] or \
                              foundry.new_server_info['server_settings']['disable_chat_reporting'] or \
                              foundry.new_server_info['server_settings']['geyser_support'] or \
                              (foundry.new_server_info['type'] in ['fabric', 'quilt'])

            needs_installed = foundry.new_server_info['type'] in ['forge', 'neoforge', 'fabric', 'quilt']

        if needs_installed:
            function_list.append((f'Installing ${foundry.new_server_info["type"].title().replace("forge", "Forge")}$', functools.partial(foundry.install_server), 10 if download_addons else 20))

        if download_addons:
            function_list.append((f'{desc_text} add-ons', functools.partial(foundry.iter_addons, functools.partial(adjust_percentage, 10 if needs_installed else 20), True), 0))

        function_list.append(('Creating pre-install back-up', functools.partial(foundry.create_backup), 5 if (download_addons or needs_installed) else 10))

        function_list.append(('Applying new configuration', functools.partial(foundry.update_server_files), 10 if (download_addons or needs_installed) else 20))

        function_list.append(('Creating post-install back-up', functools.partial(foundry.create_backup), 5 if (download_addons or needs_installed) else 10))

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
                self.execute_error("An internet connection is required to continue\n\nVerify connectivity and try again")

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
            if final < 0: final = original
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
            ('Validating modpack', functools.partial(foundry.scan_modpack, True, functools.partial(adjust_percentage, 20)), 0),
            ("Downloading 'server.jar'", functools.partial(foundry.download_jar, functools.partial(adjust_percentage, 10), True), 0),
            ('Installing modpack', functools.partial(foundry.install_server, None, True), 15),
            ('Creating pre-install back-up', functools.partial(foundry.create_backup, True), 10),
            ('Validating configuration', functools.partial(foundry.finalize_modpack, True, functools.partial(adjust_percentage, 5)), 0),
            ('Creating post-install back-up', functools.partial(foundry.create_backup, True), 10)
        ]

        self.page_contents['function_list'] = tuple(function_list)
