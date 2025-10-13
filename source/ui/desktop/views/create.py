from source.ui.desktop.views.templates import *
from source.ui.desktop.widgets import *


#  =============================================== Create Server =======================================================
# <editor-fold desc="Create Server">

class CreateServerTemplateScreen(MenuBackground):
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
        default_scroll = 1

        # Update page counter
        self.last_results = results
        self.max_pages = (len(results) / self.page_size).__ceil__()
        self.current_page = 1 if self.current_page == 0 or new_search else self.current_page


        self.page_switcher.update_index(self.current_page, self.max_pages)
        page_list = results[(self.page_size * self.current_page) - self.page_size:self.page_size * self.current_page]

        self.scroll_layout.clear_widgets()


        # Generate header
        header_content = "Select a template to use"

        for child in self.header.children:
            if child.id == "text":
                child.text = header_content
                break


        # Show servers if they exist
        if foundry.ist_data:

            # Clear and add all TemplateButtons
            for x, template in enumerate(page_list, 1):

                # Template button click function
                self.scroll_layout.add_widget(
                    ScrollItem(
                        widget = TemplateButton(
                            template = template,
                            fade_in = ((x if x <= 8 else 8) / self.anim_speed) if fade_in else 0,
                        )
                    )
                )

            self.resize_bind()

        # Go back to main menu if they don't
        else:
            utility.screen_manager.current = 'CreateServerModeScreen'
            utility.screen_manager.screen_tree = ['MainMenuScreen']
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

        # Return if no free space or telepath is busy
        if disk_popup():
            return
        if telepath_popup():
            return

        # Generate buttons on page load
        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'

        # Prevent server creation if offline
        if not constants.app_online:
            float_layout.add_widget(HeaderText("Server creation requires an internet connection", '', (0, 0.6)))
            buttons.append(ExitButton('Back', (0.5, 0.35)))

        # Regular menus
        else:

            # Reload templates
            if not foundry.ist_data:
                foundry.get_repo_templates()


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

                Clock.schedule_once(update_grid, 0)


            self.resize_bind = lambda*_: Clock.schedule_once(functools.partial(resize_scroll, scroll_widget, self.scroll_layout, scroll_anchor), 0)
            self.resize_bind()
            Window.bind(on_resize=self.resize_bind)
            self.scroll_layout.bind(minimum_height=self.scroll_layout.setter('height'))
            self.scroll_layout.id = 'scroll_content'


            # Scroll gradient
            scroll_top = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.795}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, 60))
            scroll_bottom = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.26}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, -60))

            # Generate buttons on page load
            header_content = "Select a template to use"
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

            telepath_data = constants.server_manager.online_telepath_servers
            buttons.append(ExitButton('Back', (0.5, 0.11 if telepath_data else 0.14), cycle=True))

            # Add Telepath button if servers are connected
            if telepath_data and constants.app_online:
                float_layout.add_widget(TelepathDropButton('create', (0.5, 0.202)))


        for button in buttons:
            float_layout.add_widget(button)

        menu_name = "Instant Server"
        float_layout.add_widget(generate_title("Instant Server"))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)

        if constants.app_online:
            self.gen_search_results(list(foundry.ist_data.values()))

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

        row_top.add_widget(
            big_mode_button('create a pre-configured server', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None),
                            'instant', clickable=True, click_func=functools.partial(screen, 'CreateServerTemplateScreen'))
        )
        row_top.add_widget(
            big_mode_button('install a modpack', {"center_y": 0.5, "center_x": 0.5}, (0, 0),(None, None),
                            'modpack', clickable=True, click_func=functools.partial(screen, 'ServerImportModpackScreen'))
        )

        row_bottom.add_widget(
            big_mode_button('import an existing server', {"center_y": 0.5, "center_x": 0.5}, (0, 0),(None, None),
                            'import', clickable=True, click_func=functools.partial(screen, 'ServerImportScreen'))
        )
        row_bottom.add_widget(
            big_mode_button('create a server manually', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None),
                            'custom', clickable=True, click_func=functools.partial(screen, 'CreateServerNameScreen'))
        )

        float_layout.add_widget(row_top)
        float_layout.add_widget(row_bottom)


        for button in buttons:
            float_layout.add_widget(button)

        float_layout.add_widget(generate_title('Create New Server'))
        float_layout.add_widget(generate_footer('Create new server'))

        # Async reload Telepath servers
        dTimer(0, constants.server_manager.check_telepath_servers).start()

        self.add_widget(float_layout)


# Create Server Step 1:  Server Name -----------------------------------------------------------------------------------

class CreateServerNameScreen(MenuBackground):

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

        # Prevent server creation if offline
        if not constants.app_online:
            float_layout.add_widget(HeaderText("Server creation requires an internet connection", '', (0, 0.6)))
            buttons.append(ExitButton('Back', (0.5, 0.35)))

        # Regular menus
        else:
            float_layout.add_widget(InputLabel(pos_hint={"center_x": 0.5, "center_y": 0.58}))
            float_layout.add_widget(HeaderText("What would you like to name your server?", '', (0, 0.76)))
            self.name_input = ServerNameInput(pos_hint={"center_x": 0.5, "center_y": 0.5}, text=foundry.new_server_info['name'])
            float_layout.add_widget(self.name_input)
            buttons.append(next_button('Next', (0.5, 0.24), not foundry.new_server_info['name'], next_screen='CreateServerTypeScreen'))
            buttons.append(ExitButton('Back', (0.5, 0.14), cycle=True))
            float_layout.add_widget(page_counter(1, 7, (0, 0.768)))

        for button in buttons:
            float_layout.add_widget(button)


        # Add telepath button if servers are connected
        if constants.server_manager.online_telepath_servers:
            float_layout.add_widget(TelepathDropButton('create', (0.5, 0.4)))


        float_layout.add_widget(generate_title('Create New Server'))
        float_layout.add_widget(generate_footer('Create new server'))

        self.add_widget(float_layout)


        if constants.app_online:
            self.name_input.grab_focus()



# Create Server Step 2:  Server Type -----------------------------------------------------------------------------------

class CreateServerTypeScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'
        self.current_selection = 'vanilla'
        self.content_layout_1 = None
        self.content_layout_2 = None

    def generate_menu(self, **kwargs):
        # Generate buttons on page load
        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'

        float_layout.add_widget(HeaderText("What type of server do you wish to create?", '', (0, 0.86)))
        self.current_selection = foundry.new_server_info['type']

        # Create UI buttons
        buttons.append(next_button('Next', (0.5, 0.21), False, next_screen='CreateServerVersionScreen'))
        buttons.append(ExitButton('Back', (0.5, 0.12), cycle=True))


        # Create type buttons (Page 1)
        self.content_layout_1 = FloatLayout()
        row_top = BoxLayout()
        row_bottom = BoxLayout()
        row_top.pos_hint = {"center_y": 0.66, "center_x": 0.5}
        row_bottom.pos_hint = {"center_y": 0.405, "center_x": 0.5}
        row_bottom.size_hint_max_x = row_top.size_hint_max_x = dp(1000)
        row_top.orientation = row_bottom.orientation = "horizontal"
        row_top.add_widget(big_icon_button('runs most plug-ins, optimized', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None), 'paper', clickable=True, selected=('paper' == foundry.new_server_info['type'])))
        row_top.add_widget(big_icon_button('default, stock experience', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None), 'vanilla', clickable=True, selected=('vanilla' == foundry.new_server_info['type'])))
        row_top.add_widget(big_icon_button('modded experience', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None), 'forge', clickable=True, selected=('forge' == foundry.new_server_info['type'])))
        row_bottom.add_widget(big_icon_button('performant fork of paper', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None), 'purpur', clickable=True, selected=('purpur' == foundry.new_server_info['type'])))
        row_bottom.add_widget(big_icon_button('modern mod platform', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None), 'fabric', clickable=True, selected=('fabric' == foundry.new_server_info['type'])))
        row_bottom.add_widget(big_icon_button('view more options', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None), 'more', clickable=True, selected=False))
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
        row_top.add_widget(big_icon_button('modern $Forge$ implementation', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None), 'neoforge', clickable=True, selected=('neoforge' == foundry.new_server_info['type'])))
        row_top.add_widget(big_icon_button('enhanced fork of $Fabric$', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None), 'quilt', clickable=True, selected=('quilt' == foundry.new_server_info['type'])))
        row_top.add_widget(big_icon_button('requires tuning, but efficient', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None), 'spigot', clickable=True, selected=('spigot' == foundry.new_server_info['type'])))
        row_bottom.add_widget(big_icon_button('legacy, supports plug-ins', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None), 'craftbukkit', clickable=True, selected=('craftbukkit' == foundry.new_server_info['type'])))
        row_bottom.add_widget(big_icon_button('view more options', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None), 'more', clickable=True, selected=False))
        self.content_layout_2.add_widget(row_top)
        self.content_layout_2.add_widget(row_bottom)


        for button in buttons:
            float_layout.add_widget(button)

        float_layout.add_widget(self.content_layout_1)
        float_layout.add_widget(self.content_layout_2)
        menu_name = f"Create '{foundry.new_server_info['name']}'"

        float_layout.add_widget(page_counter(2, 7, (0, 0.868)))
        float_layout.add_widget(generate_title(menu_name))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)



# Create Server Step 3:  Server Version --------------------------------------------------------------------------------

class CreateServerVersionScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'

    def generate_menu(self, **kwargs):

        # Generate buttons on page load
        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'

        # Prevent server creation if offline
        if not constants.app_online:
            float_layout.add_widget(HeaderText("Server creation requires an internet connection", '', (0, 0.6)))
            buttons.append(ExitButton('Back', (0.5, 0.35)))

        # Regular menus
        else:
            float_layout.add_widget(InputLabel(pos_hint={"center_x": 0.5, "center_y": 0.58}))
            float_layout.add_widget(page_counter(3, 7, (0, 0.768)))
            float_layout.add_widget(HeaderText("What version of Minecraft do you wish to play?", '', (0, 0.76)))
            float_layout.add_widget(ServerVersionInput(pos_hint={"center_x": 0.5, "center_y": 0.5}, text=foundry.new_server_info['version']))
            buttons.append(next_button('Next', (0.5, 0.24), False, next_screen='CreateServerWorldScreen', show_load_icon=True))
            buttons.append(ExitButton('Back', (0.5, 0.14), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)

        menu_name = f"Create '{foundry.new_server_info['name']}'"
        float_layout.add_widget(generate_title(menu_name))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)



# Create Server Step 4:  Server Name -----------------------------------------------------------------------------------
# Note:  Also generates ACL object after name/version are decided
class CreateServerWorldScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'

    def generate_menu(self, **kwargs):

        # Generate ACL in new_server_info
        def create_acl():
            if not foundry.new_server_info['acl_object']:
                foundry.new_server_info['acl_object'] = acl.AclManager(foundry.new_server_info['name'])
            else:
                foundry.new_server_info['acl_object'].server = acl.dump_config(foundry.new_server_info['name'], True)

            # acl.print_acl(foundry.new_server_info['acl_object'])

        thread = dTimer(0, create_acl)
        thread.start()


        # Generate buttons on page load
        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'
        float_layout.add_widget(InputLabel(pos_hint={"center_x": 0.5, "center_y": 0.62}))
        float_layout.add_widget(HeaderText("What world would you like to use?", '', (0, 0.76)))
        float_layout.add_widget(CreateServerWorldInput(pos_hint={"center_x": 0.5, "center_y": 0.55}))
        float_layout.add_widget(CreateServerSeedInput(pos_hint={"center_x": 0.5, "center_y": 0.442}))
        buttons.append(input_button('Browse...', (0.5, 0.55), ('dir', paths.minecraft_saves if os.path.isdir(paths.minecraft_saves) else paths.user_downloads), input_name='CreateServerWorldInput', title='Select a World File'))

        server_version = foundry.new_server_info['version']
        if constants.version_check(server_version, '>=', "1.1"):
            options = ['normal', 'superflat']
            if constants.version_check(server_version, '>=', "1.3.1"):
                options.append('large biomes')
            if constants.version_check(server_version, '>=', "1.7.2"):
                options.append('amplified')
            default_name = foundry.new_server_info['server_settings']['level_type'].replace("default", "normal").replace("flat", "superflat").replace("large_biomes", "large biomes")
            float_layout.add_widget(DropButton(default_name, (0.5, 0.442), options_list=options, input_name='ServerLevelTypeInput', x_offset=41))

        buttons.append(next_button('Next', (0.5, 0.24), False, next_screen='CreateServerNetworkScreen'))
        buttons.append(ExitButton('Back', (0.5, 0.14), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)

        menu_name = f"Create '{foundry.new_server_info['name']}'"
        float_layout.add_widget(page_counter(4, 7, (0, 0.768)))
        float_layout.add_widget(generate_title(menu_name))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)

    def on_pre_enter(self, *args):
        super().on_pre_enter()
        self.toggle_new(foundry.new_server_info['server_settings']['world'] != 'world')

    # Call this when world loaded, and when the 'create new world instead' button is clicked. Fix overlapping when added/removed multiple times
    def toggle_new(self, boolean_value):

        current_input = ''
        server_version = foundry.new_server_info['version']

        for child in self.children:
            try:
                if child.id == 'content':
                    for item in child.children:
                        try:
                            if item.__class__.__name__ == 'CreateServerSeedInput':
                                current_input = 'input'
                                if foundry.new_server_info['server_settings']['world'] != 'world':
                                    child.remove_widget(item)

                                    try:
                                        if constants.version_check(server_version, '>=', "1.1"):
                                            child.remove_widget([relative for relative in child.children if relative.__class__.__name__ == 'DropButton'][0])
                                    except IndexError as e:
                                        send_log(f'{self.__class__.__name__}.toggle_new', "'DropButton' does not exist, can't remove", 'error')

                            elif item.id == 'Create new world instead':
                                current_input = 'button'
                                if foundry.new_server_info['server_settings']['world'] == 'world':
                                    child.remove_widget(item)
                        except AttributeError:
                            continue

                    # Show button if true
                    if boolean_value and foundry.new_server_info['server_settings']['world'] != 'world' and current_input == 'input':
                        child.add_widget(MainButton('Create new world instead', (0.5, 0.442), 'add-circle-outline.png', width=530))

                    # Show seed input, and clear world text
                    elif foundry.new_server_info['server_settings']['world'] == 'world' and current_input == 'button':
                        child.add_widget(CreateServerSeedInput(pos_hint={"center_x": 0.5, "center_y": 0.442}))

                        if constants.version_check(server_version, '>=', "1.1"):
                            options = ['normal', 'superflat']
                            if constants.version_check(server_version, '>=', "1.3.1"):
                                options.append('large biomes')
                            if constants.version_check(server_version, '>=', "1.7.2"):
                                options.append('amplified')
                            default_name = foundry.new_server_info['server_settings']['level_type'].replace("default", "normal").replace("flat", "superflat").replace("large_biomes", "large biomes")
                            child.add_widget(DropButton(default_name, (0.5, 0.442), options_list=options, input_name='ServerLevelTypeInput', x_offset=41))
                    break

            except AttributeError:
                pass



# Create Server Step 5:  Server Network --------------------------------------------------------------------------------
class CreateServerNetworkScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'

    def generate_menu(self, **kwargs):

        # Scroll list
        scroll_widget = ScrollViewWidget()
        scroll_anchor = AnchorLayout()
        scroll_layout = GridLayout(cols=1, spacing=30, size_hint_max_x=1050, size_hint_y=None, padding=[0, 50, 0, 30])


        # Bind / cleanup height on resize
        def resize_scroll(call_widget, grid_layout, anchor_layout, *args):
            call_widget.height = Window.height // 2
            grid_layout.cols = 2 if Window.width > grid_layout.size_hint_max_x else 1

            def update_grid(*args):
                anchor_layout.size_hint_min_y = grid_layout.height

            Clock.schedule_once(update_grid, 0)


        self.resize_bind = lambda*_: Clock.schedule_once(functools.partial(resize_scroll, scroll_widget, scroll_layout, scroll_anchor), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        scroll_layout.bind(minimum_height=scroll_layout.setter('height'))
        scroll_layout.id = 'scroll_content'

        # Scroll gradient
        scroll_top = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.77}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, 60))
        scroll_bottom = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.272}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, -60))


        # Generate buttons on page load
        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'

        sub_layout = ScrollItem()
        sub_layout.add_widget(InputLabel(pos_hint={"center_x": 0.5, "center_y": 1.1}))
        sub_layout.add_widget(CreateServerPortInput(pos_hint={"center_x": 0.5, "center_y": 0.5}, text=process_ip_text()))
        scroll_layout.add_widget(sub_layout)

        sub_layout = ScrollItem()
        sub_layout.add_widget(CreateServerMOTDInput(pos_hint={"center_x": 0.5, "center_y": 0.5}))
        scroll_layout.add_widget(sub_layout)

        sub_layout = ScrollItem()
        sub_layout.add_widget(MainButton('Access Control', (0.5, 0.5), 'shield-half-small.png', width=450, icon_offset=-185))
        scroll_layout.add_widget(sub_layout)

        sub_layout = ScrollItem()
        def toggle_proxy(boolean):
            foundry.new_server_info['server_settings']['enable_proxy'] = boolean
        sub_layout.add_widget(blank_input(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text='enable proxy (playit)'))
        sub_layout.add_widget(toggle_button('proxy', (0.5, 0.5), custom_func=toggle_proxy, default_state=foundry.new_server_info['server_settings']['enable_proxy']))
        scroll_layout.add_widget(sub_layout)


        # Append scroll view items
        scroll_anchor.add_widget(scroll_layout)
        scroll_widget.add_widget(scroll_anchor)
        float_layout.add_widget(scroll_widget)
        float_layout.add_widget(scroll_top)
        float_layout.add_widget(scroll_bottom)

        float_layout.add_widget(HeaderText("Do you wish to configure network information?", '', (0, 0.83)))


        buttons.append(next_button('Next', (0.5, 0.24), False, next_screen='CreateServerOptionsScreen'))
        buttons.append(ExitButton('Back', (0.5, 0.14), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)

        menu_name = f"Create '{foundry.new_server_info['name']}'"
        float_layout.add_widget(page_counter(5, 7, (0, 0.838)))
        float_layout.add_widget(generate_title(menu_name))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)



# Create Server Step 5:  ACL Options -----------------------------------------------------------------------------------

class CreateServerAclScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'
        self._ignore_keys = ['tab']
        self.header = None
        self.search_bar = None
        self.whitelist_toggle = None
        self.scroll_widget = None
        self.scroll_layout = None
        self.blank_label = None
        self.search_label = None
        self.list_header = None
        self.controls_button = None
        self.user_panel = None
        self.show_panel = False

        self.acl_object = None
        self._hash = None
        self.current_list = None

        self.filter_text = ""
        self.currently_filtering = False


    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        super()._on_keyboard_down(keyboard, keycode, text, modifiers)

        if ((keycode[1] == 'h' and control in modifiers and constants.os_name != 'macos') or (keycode[1] == 'h' and control in modifiers and 'shift' in modifiers and constants.os_name == 'macos')) and not self.popup_widget:
            self.controls_button.button.trigger_action()

        # Press
        if keycode[1] == 'tab' and not self._input_focused and self.name == utility.screen_manager.current_screen.name:
            for button in self.walk():
                try:
                    if button.id == "input_button":
                        button.force_click()
                        break
                except AttributeError:
                    continue


    def update_user_panel(self, rule_name: str, rule_scope: str):

        # Generate rule list count
        rule_count = len(self.scroll_widget.data)
        panel_check = rule_count > 0


        # Hide user panel if there are no items
        if panel_check != self.show_panel:

            for child in self.user_panel.children:

                # Figure out how to make this not bug out when transitioning between rules, specifically with blank_text
                if child.__class__.__name__ == "Label":
                    child.opacity = (1 if panel_check else 0)
                else:
                    Animation(opacity=(1 if panel_check else 0), duration=0.3).start(child)

                # Make sure self.options shows and hides properly
                for widget in self.user_panel.options.children:
                    utility.hide_widget(widget, panel_check)

            self.show_panel = panel_check


        # Update displayed data on user panel
        if rule_name:
            self.acl_object.get_rule(rule_name)
            self.user_panel.update_panel(self.acl_object.displayed_rule, rule_scope)


        # If rule is displayed
        if self.acl_object.displayed_rule:

            if self.user_panel.blank_label.opacity > 0:
                Animation.stop_all(self.user_panel.blank_label)
                utility.hide_widget(self.user_panel.blank_label, True)
                for child in self.user_panel.options.children:
                    utility.hide_widget(child, False)

        # If rule is not displayed
        else:

            if self.user_panel.blank_label.opacity == 0:
                utility.hide_widget(self.user_panel.blank_label, False)
                for child in self.user_panel.options.children:
                    utility.hide_widget(child, True)


        if not panel_check:
            for widget in self.user_panel.options.children:
                utility.hide_widget(widget, True)


        if self.acl_object.displayed_rule:
            Animation.stop_all(self.user_panel.blank_label)
            utility.hide_widget(self.user_panel.blank_label, True)
            self.user_panel.blank_label.opacity = 0


    # Filter data from search bar
    def search_filter(self, query):

        def lock(*args):
            self.currently_filtering = False
            if self.filter_text != self.search_bar.text:
                self.search_filter(self.search_bar.text)

        # Prevent refreshes shorter than 0.5s
        if not self.currently_filtering:
            self.currently_filtering = True
            self.filter_text = query

            # Filter data

            # Reset scroll
            self.scroll_widget.scroll_y = 1

            total_list = [{'rule': rule} for rule in self.acl_object.list_items[self.current_list]['enabled']]
            total_list.extend([{'rule': rule} for rule in self.acl_object.list_items[self.current_list]['disabled']])

            original_len = len(total_list)

            if query:
                filtered_list = []
                for rule in total_list:
                    rule_obj = rule['rule']

                    # Name matches query
                    if query.lower().replace("!w", "").replace("!g", "") in rule_obj.rule.lower():
                        filtered_list.append(rule)

                    # Scope matches query
                    elif query.lower() == rule_obj.rule_scope:
                        filtered_list.append(rule)

                    # Rule type matches query
                    elif query.lower() == rule_obj.rule_type:
                        filtered_list.append(rule)

                    # Location matches query
                    else:
                        try:
                            location = acl.get_uuid(rule_obj.rule)['ip-geo']
                            if query.lower() in location.lower().replace(" - ", " ") and location != "Unknown":
                                filtered_list.append(rule)
                        except KeyError:
                            pass


                total_list = filtered_list
                del filtered_list

            # Show hint text if there are no rules

            self.set_data(total_list)


            # Show search label if it exists
            Animation.stop_all(self.search_label)
            if self.filter_text and len(self.scroll_widget.data) == 0 and original_len > 0:
                self.search_label.text = f"No results for '{self.filter_text}'"
                Animation(opacity=1, duration=0.2).start(self.search_label)
            else:
                Animation(opacity=0, duration=0.05).start(self.search_label)


            # Unlock the lock
            timer = dTimer(0.5, function=lock)
            timer.start()


    # ops, bans, wl
    def update_list(self, list_type: str, reload_children=True, reload_panel=False):

        if "op" in list_type:
            list_type = "ops"
        elif "ban" in list_type:
            list_type = "bans"
        else:
            list_type = "wl"

        # Reset scroll
        list_changed = False
        if self.current_list != list_type:
            list_changed = True
            self.scroll_widget.scroll_y = 1

        # Create list data with list type
        self.current_list = list_type

        # Check if there's an active filter
        if self.filter_text:
            self.search_filter(self.filter_text)
        else:
            total_list = [{'rule': rule} for rule in self.acl_object.list_items[list_type]['enabled']]
            total_list.extend([{'rule': rule} for rule in self.acl_object.list_items[list_type]['disabled']])

            self.set_data(total_list)

        rule_count = len(self.acl_object.rules[list_type])
        if list_type == "bans":
            rule_count += len(self.acl_object.rules['subnets'])


        # Modify header content
        very_bold_font = os.path.join(paths.ui_assets, 'fonts', constants.fonts["very-bold"])
        header_content = (f'[color=#6A6ABA]{translate("No rules")}[/color]' if rule_count == 0 else f'[font={very_bold_font}]1[/font] {translate("rule")}' if rule_count == 1 else f'[font={very_bold_font}]{rule_count:,}[/font] {translate("rules")}')
        if list_type == "wl" and not self.acl_object._server['whitelist']:
            header_content += f" ({translate('inactive')})"

        # header_content = (" "*(len(header_content) - (55 if 'inactive' not in header_content else 50))) + header_content

        for child in self.header.children:
            if child.id == "text":
                child.text = header_content
                child.halign = "left"
                child.text_size[0] = 500
                child.x = Window.width / 2 + 240
                break


        display_count = len(self.acl_object.list_items[list_type]['enabled']) + len(self.acl_object.list_items[list_type]['disabled'])

        # If there are no rules, say as much with a label
        utility.hide_widget(self.list_header.global_rule, display_count == 0)
        utility.hide_widget(self.list_header.enabled_rule, display_count == 0)
        utility.hide_widget(self.list_header.disabled_rule, display_count == 0)


        if display_count == 0:
            if self.blank_label.opacity < 1:
                self.blank_label.text = "No rules available, add them above"
                utility.hide_widget(self.blank_label, False)
                self.blank_label.opacity = 0
                Animation(opacity=1, duration=0.2).start(self.blank_label)
                Animation(opacity=0, duration=0.2).start(self.search_label)

        # If there are rules, display them here
        else:
            # Show search label if it exists
            Animation.stop_all(self.search_label)
            # print(len(self.scroll_widget.data))
            if self.filter_text and len(self.scroll_widget.data) == 0:
                self.search_label.text = f"{translate('No results for')} '{self.filter_text}'"
                Animation(opacity=1, duration=0.2).start(self.search_label)
            else:
                Animation(opacity=0, duration=0.2).start(self.search_label)

            self.list_header.remove_widget(self.list_header.enabled_rule)
            self.list_header.enabled_rule = RelativeLayout()
            self.list_header.enabled_rule.add_widget(
                BannerObject(
                    size=(120, 32),
                    color=(0.439, 0.839, 1, 1) if list_type == 'ops'
                    else (1, 0.5, 0.65, 1) if list_type == 'bans'
                    else (0.3, 1, 0.6, 1),

                    text="operator" if list_type == 'ops'
                    else "banned" if list_type == 'bans'
                    else "allowed",

                    icon="settings-sharp.png" if list_type == 'ops'
                    else "close-circle-sharp.png" if list_type == 'bans'
                    else "checkmark-circle-sharp.png"
                )
            )
            self.list_header.add_widget(self.list_header.enabled_rule)


            self.list_header.remove_widget(self.list_header.disabled_rule)
            self.list_header.disabled_rule = RelativeLayout()
            self.list_header.disabled_rule.add_widget(
                BannerObject(
                    size=(125, 32),
                    color=(0.6, 0.5, 1, 1) if list_type == 'ops'
                    else (0.3, 1, 0.6, 1) if list_type == 'bans'
                    else (1, 0.5, 0.65, 1) if self.acl_object._server['whitelist'] else(0.7, 0.7, 0.7, 1),

                    text="standard" if list_type == 'ops'
                    else "allowed" if list_type == 'bans'
                    else "restricted",

                    icon="person-circle-sharp.png" if list_type == 'ops'
                    else "checkmark-circle-sharp.png" if list_type == 'bans'
                    else "close-circle-sharp.png"
                )
            )
            self.list_header.add_widget(self.list_header.disabled_rule)

            utility.hide_widget(self.blank_label, True)

        # Change whitelist toggle visibility based on list_type
        utility.hide_widget(self.whitelist_toggle, list_type != 'wl')

        # Refresh all buttons
        if reload_children:
            for rule_button in self.scroll_layout.children:
                rule_button.change_properties(rule_button.rule)


            # Dirty fix to hide grid resize that fixes RuleButton text.pos_hint x
            if list_changed:
                self.scroll_widget.opacity = 0
                self.scroll_layout.cols = 1
                self.resize_bind()
                def animate_grid(*args):
                    Animation.stop_all(self.scroll_widget)
                    Animation(opacity=1, duration=0.3).start(self.scroll_widget)
                Clock.schedule_once(animate_grid, 0)


        # Update displayed rule options
        if (self.acl_object.displayed_rule and list_changed) or (reload_panel and self.acl_object.displayed_rule):
            global_rules = acl.load_global_acl()
            self.acl_object.displayed_rule.acl_group = list_type
            rule_scope = acl.check_global_acl(global_rules, self.acl_object.displayed_rule).rule_scope
            self.update_user_panel(self.acl_object.displayed_rule.rule, rule_scope)


    def set_data(self, data):

        if self.scroll_layout:
            self.scroll_layout.rows = None

        self.scroll_widget.data = data

        if self.resize_bind:
            self.resize_bind()


    def generate_menu(self, **kwargs):

        if not foundry.new_server_info['acl_object']:
            foundry.new_server_name()
            foundry.new_server_info['acl_object'] = acl.AclManager(foundry.new_server_info['name'])
            self.acl_object = foundry.new_server_info['acl_object']

        # If self._hash doesn't match, set list to ops by default
        if self._hash != foundry.new_server_info['_hash']:
            self.acl_object = foundry.new_server_info['acl_object']
            self._hash = foundry.new_server_info['_hash']
            self.current_list = 'ops'

        self.show_panel = False

        self.filter_text = ""
        self.currently_filtering = False


        # Scroll list
        self.scroll_widget = RecycleViewWidget(position=(0.5, 0.43), view_class=RuleButton)
        self.scroll_layout = RecycleGridLayout(spacing=[110, -15], size_hint_y=None, padding=[60, 20, 0, 30])
        test_rule = RuleButton()

        # Bind / cleanup height on resize
        def resize_scroll(*args):
            self.scroll_widget.height = Window.height // 1.65
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


        self.resize_bind = lambda*_: Clock.schedule_once(functools.partial(resize_scroll), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        self.scroll_layout.bind(minimum_height=self.scroll_layout.setter('height'))
        self.scroll_layout.id = 'scroll_content'


        # Scroll gradient
        scroll_top = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.735}, pos=self.scroll_widget.pos, size=(self.scroll_widget.width // 1.5, 60))
        scroll_bottom = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.14}, pos=self.scroll_widget.pos, size=(self.scroll_widget.width // 1.5, -60))

        # Generate buttons on page load
        very_bold_font = os.path.join(paths.ui_assets, 'fonts', constants.fonts["very-bold"])
        selector_text = "operators" if self.current_list == "ops" else "bans" if self.current_list == "bans" else "whitelist"
        self.page_selector = DropButton(selector_text, (0.5, 0.89), options_list=['operators', 'bans', 'whitelist'], input_name='ServerAclTypeInput', x_offset=-210, facing='center', custom_func=self.update_list)
        header_content = ""
        self.header = HeaderText(header_content, '', (0, 0.89), fixed_x=True, no_line=True, __translate__ = (False, True))


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

        self.whitelist_toggle = toggle_button('whitelist', (0.5, 0.89), default_state=self.acl_object._server['whitelist'], x_offset=-395, custom_func=toggle_whitelist)


        # Legend for rule types
        self.list_header = BoxLayout(orientation="horizontal", pos_hint={"center_x": 0.5, "center_y": 0.749}, size_hint_max=(400, 100))
        self.list_header.global_rule = RelativeLayout()
        self.list_header.global_rule.add_widget(BannerObject(size=(120, 32), color=test_rule.global_icon_color, text="global", icon="earth-sharp.png", icon_side="left"))
        self.list_header.add_widget(self.list_header.global_rule)

        self.list_header.enabled_rule = RelativeLayout()
        self.list_header.enabled_rule.add_widget(BannerObject(size=(120, 32), color=(1,1,1,1), text=" ", icon="add.png"))
        self.list_header.add_widget(self.list_header.enabled_rule)

        self.list_header.disabled_rule = RelativeLayout()
        self.list_header.disabled_rule.add_widget(BannerObject(size=(120, 32), color=(1,1,1,1), text=" ", icon="add.png"))
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
        self.search_label.__translate__ = False
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
        self.controls_button = IconButton('controls', {}, (70, 110), (None, None), 'question.png', clickable=True, anchor='right', click_func=show_controls)
        float_layout.add_widget(self.controls_button)


        # User panel
        self.user_panel = AclRulePanel()


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

        buttons.append(ExitButton('Back', (0.5, 0.099), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)

        menu_name = f"Create '{foundry.new_server_info['name']}', Access Control"
        float_layout.add_widget(generate_title(f"Access Control Manager: '{foundry.new_server_info['name']}'"))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)

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

class CreateServerAclRuleScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'

        self._ignore_tree = True

        self.acl_input = None
        self.current_list = None
        self.acl_object = None


    def apply_rules(self):

        # Actually apply rules
        original_list = self.acl_object._process_query(self.acl_input.text, self.current_list)

        applied_list = []
        applied_list.extend(original_list['global'])
        applied_list.extend(original_list['local'])


        # Generate banner
        banner_text = "Added "
        "Added '$$'"

        if len(applied_list) == 1:
            banner_text += f"'${acl.get_uuid(applied_list[0])['name'] if applied_list[0].count('.') < 3 else applied_list[0]}$'"
        elif len(applied_list) < 3:
            banner_text += f"'${', '.join([(acl.get_uuid(x)['name'] if x.count('.') < 3 else x) for x in applied_list[0:2]])}$'"
        else:
            banner_text += f"'${acl.get_uuid(applied_list[0])['name'] if applied_list[0].count('.') < 3 else applied_list[0]}$' and {len(applied_list) - 1:,} more"


        Clock.schedule_once(
            functools.partial(
                utility.screen_manager.current_screen.show_banner,
                (0.553, 0.902, 0.675, 1),
                banner_text,
                "add-circle-sharp.png",
                2.5,
                {"center_x": 0.5, "center_y": 0.965}
            ), 0
        )

        # Return to previous screen
        self.acl_object.get_rule(applied_list[0])
        utility.screen_manager.previous_screen()

        def update_panel(*args):
            utility.screen_manager.current_screen.update_user_panel(applied_list[0], applied_list[0] in original_list['global'])

        Clock.schedule_once(update_panel, 0)

        # Prevent back button from going back to this screen
        for screen in utility.screen_manager.screen_tree:
            if screen == self.name:
                utility.screen_manager.screen_tree.remove(self.name)


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

        self.current_list = utility.screen_manager.get_screen("CreateServerAclScreen").current_list
        self.acl_object = utility.screen_manager.get_screen("CreateServerAclScreen").acl_object

        if self.current_list == "bans":
            header_message = "Enter usernames/IPs delimited, by, commas"
            float_layout.add_widget(HintLabel(0.464, "Use   [color=#FFFF33]!g <rule>[/color]   to apply globally on all servers"))
            float_layout.add_widget(HintLabel(0.374, "You can ban IP ranges/whitelist:   [color=#FF6666]192.168.0.0-150[/color], [color=#66FF88]!w 192.168.1.1[/color]"))
        else:
            header_message = "Enter usernames delimited, by, commas"
            float_layout.add_widget(HintLabel(0.425, "Use   [color=#FFFF33]!g <rule>[/color]   to apply globally on all servers"))

        float_layout.add_widget(InputLabel(pos_hint={"center_x": 0.5, "center_y": 0.72}))
        float_layout.add_widget(HeaderText(header_message, '', (0, 0.8)))
        self.acl_input = AclRuleInput(pos_hint={"center_x": 0.5, "center_y": 0.64}, text="")
        float_layout.add_widget(self.acl_input)

        buttons.append(next_button('Add Rules', (0.5, 0.24), True, next_screen='CreateServerAclScreen'))
        buttons.append(ExitButton('Back', (0.5, 0.14), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)

        menu_name = f"Create '{foundry.new_server_info['name']}', Access Control"
        list_name = "Operators" if self.current_list == "ops" else "Bans" if self.current_list == "bans" else "Whitelist"
        float_layout.add_widget(generate_title(f"Access Control Manager: Add {list_name}"))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)
        self.acl_input.grab_focus()



# Create Server Step 6:  Server Options --------------------------------------------------------------------------------

# Create ACL options, and Addon Options
class CreateServerOptionsScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'

    def generate_menu(self, **kwargs):

        # Scroll list
        scroll_widget = ScrollViewWidget()
        scroll_anchor = AnchorLayout()
        scroll_layout = GridLayout(cols=1, spacing=10, size_hint_max_x=1050, size_hint_y=None, padding=[0, 16, 0, 30])


        # Bind / cleanup height on resize
        def resize_scroll(call_widget, grid_layout, anchor_layout, *args):
            call_widget.height = Window.height // 2
            grid_layout.cols = 2 if Window.width > grid_layout.size_hint_max_x else 1

            def update_grid(*args):
                anchor_layout.size_hint_min_y = grid_layout.height

            Clock.schedule_once(update_grid, 0)


        self.resize_bind = lambda*_: Clock.schedule_once(functools.partial(resize_scroll, scroll_widget, scroll_layout, scroll_anchor), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        scroll_layout.bind(minimum_height=scroll_layout.setter('height'))
        scroll_layout.id = 'scroll_content'

        # Scroll gradient
        scroll_top = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.77}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, 60))
        scroll_bottom = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.272}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, -60))

        # Generate buttons on page load
        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'
        float_layout.add_widget(HeaderText(f"Optionally, configure additional properties", '', (0, 0.86)))

        # If server type != vanilla, append addon manger button and extend float_layout widget
        if foundry.new_server_info['type'] != 'vanilla':
            sub_layout = ScrollItem()
            sub_layout.add_widget(MainButton('Add-on Manager', (0.5, 0.5), 'extension-puzzle-sharp.png'))
            scroll_layout.add_widget(sub_layout)

        # Gamemode dropdown
        sub_layout = ScrollItem()
        sub_layout.add_widget(blank_input(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="gamemode"))
        sub_layout.add_widget(DropButton(foundry.new_server_info['server_settings']['gamemode'], (0.5, 0.5), options_list=['survival', 'adventure', 'creative'], input_name='ServerModeInput'))
        scroll_layout.add_widget(sub_layout)

        # Difficulty dropdown
        sub_layout = ScrollItem()
        sub_layout.add_widget(blank_input(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="difficulty"))
        sub_layout.add_widget(DropButton(foundry.new_server_info['server_settings']['difficulty'], (0.5, 0.5), options_list=['peaceful', 'easy', 'normal', 'hard', 'hardcore'], input_name='ServerDiffInput'))
        scroll_layout.add_widget(sub_layout)

        # Geyser switch for bedrock support
        if constants.version_check(foundry.new_server_info['version'], ">=", "1.13.2")\
        and foundry.new_server_info['type'].lower() in ['spigot', 'paper', 'purpur', 'fabric', 'quilt', 'neoforge']:
            sub_layout = ScrollItem()
            sub_layout.add_widget(blank_input(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="bedrock support (geyser)"))
            sub_layout.add_widget(toggle_button('geyser_support', (0.5, 0.5), default_state=foundry.new_server_info['server_settings']['geyser_support']))
            scroll_layout.add_widget(sub_layout)

        # Disable chat reporting by default
        if constants.version_check(foundry.new_server_info['version'], ">=", "1.19")\
        and foundry.new_server_info['type'].lower() != "vanilla":
            sub_layout = ScrollItem()
            sub_layout.add_widget(blank_input(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="disable chat reporting"))
            sub_layout.add_widget(toggle_button('chat_report', (0.5, 0.5), default_state=foundry.new_server_info['server_settings']['disable_chat_reporting']))
            scroll_layout.add_widget(sub_layout)

        # PVP switch button
        sub_layout = ScrollItem()
        sub_layout.add_widget(blank_input(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="enable PVP"))
        sub_layout.add_widget(toggle_button('pvp', (0.5, 0.5), default_state=foundry.new_server_info['server_settings']['pvp']))
        scroll_layout.add_widget(sub_layout)

        # Enable keep inventory
        if constants.version_check(foundry.new_server_info['version'], ">=", "1.4.2"):
            sub_layout = ScrollItem()
            sub_layout.add_widget(blank_input(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="keep inventory"))
            sub_layout.add_widget(toggle_button('keep_inventory', (0.5, 0.5), default_state=foundry.new_server_info['server_settings']['keep_inventory']))
            scroll_layout.add_widget(sub_layout)

        # Spawn protection switch button
        sub_layout = ScrollItem()
        sub_layout.add_widget(blank_input(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="enable spawn protection"))
        sub_layout.add_widget(toggle_button('spawn_protection', (0.5, 0.5), default_state=foundry.new_server_info['server_settings']['spawn_protection']))
        scroll_layout.add_widget(sub_layout)

        # Enable daylight cycle
        if constants.version_check(foundry.new_server_info['version'], ">=", "1.4.2"):
            label = "daylight & weather cycle" if constants.version_check(foundry.new_server_info['version'], ">=", "1.11") else "daylight cycle"
            sub_layout = ScrollItem()
            sub_layout.add_widget(blank_input(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text=label))
            sub_layout.add_widget(toggle_button('daylight_weather_cycle', (0.5, 0.5), default_state=foundry.new_server_info['server_settings']['daylight_weather_cycle']))
            scroll_layout.add_widget(sub_layout)

        # Spawn creatures switch button
        sub_layout = ScrollItem()
        sub_layout.add_widget(blank_input(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="spawn creatures"))
        sub_layout.add_widget(toggle_button('spawn_creatures', (0.5, 0.5), default_state=foundry.new_server_info['server_settings']['spawn_creatures']))
        scroll_layout.add_widget(sub_layout)

        # Enable command blocks switch button
        if constants.version_check(foundry.new_server_info['version'], ">=", "1.4.2"):
            sub_layout = ScrollItem()
            sub_layout.add_widget(blank_input(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="enable command blocks"))
            sub_layout.add_widget(toggle_button('command_blocks', (0.5, 0.5), default_state=foundry.new_server_info['server_settings']['command_blocks']))
            scroll_layout.add_widget(sub_layout)

        # Random tick speed input
        if constants.version_check(foundry.new_server_info['version'], ">=", "1.4.2"):
            sub_layout = ScrollItem()
            sub_layout.add_widget(ServerTickSpeedInput(pos_hint={"center_x": 0.5, "center_y": 0.5}, text=foundry.new_server_info['server_settings']['random_tick_speed']))
            scroll_layout.add_widget(sub_layout)

        # Max player input
        sub_layout = ScrollItem()
        sub_layout.add_widget(ServerPlayerInput(pos_hint={"center_x": 0.5, "center_y": 0.5}, text=foundry.new_server_info['server_settings']['max_players']))
        scroll_layout.add_widget(sub_layout)

        # Append scroll view items
        scroll_anchor.add_widget(scroll_layout)
        scroll_widget.add_widget(scroll_anchor)
        float_layout.add_widget(scroll_widget)
        float_layout.add_widget(scroll_top)
        float_layout.add_widget(scroll_bottom)

        buttons.append(next_button('Next', (0.5, 0.21), False, next_screen='CreateServerReviewScreen'))
        buttons.append(ExitButton('Back', (0.5, 0.12), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)

        menu_name = f"Create '{foundry.new_server_info['name']}'"
        float_layout.add_widget(page_counter(6, 7, (0, 0.868)))
        float_layout.add_widget(generate_title(menu_name))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)



# Create Server Step 6:  Add-on Options --------------------------------------------------------------------------------

class CreateServerAddonScreen(MenuBackground):

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

        # Update page counter
        results = list(sorted(results, key=lambda d: d.name.lower()))
        self.last_results = results
        self.max_pages = (len(results) / self.page_size).__ceil__()
        self.current_page = 1 if self.current_page == 0 or new_search else self.current_page

        self.page_switcher.update_index(self.current_page, self.max_pages)
        page_list = results[(self.page_size * self.current_page) - self.page_size:self.page_size * self.current_page]

        self.scroll_layout.clear_widgets()

        # Generate header
        addon_count = len(results)
        very_bold_font = os.path.join(paths.ui_assets, 'fonts', constants.fonts["very-bold"])
        header_content = f"{translate('Add-on Queue')}  [color=#494977]-[/color]  " + (f'[color=#6A6ABA]{translate("No items")}[/color]' if addon_count == 0 else f'[font={very_bold_font}]1[/font] {translate("item")}' if addon_count == 1 else f'[font={very_bold_font}]{addon_count:,}[/font] {translate("items")}')

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

                # Function to remove addon
                def remove_addon(index):
                    selected_button = [item for item in self.scroll_layout.walk() if item.__class__.__name__ == "AddonButton"][index-1]
                    addon = selected_button.properties

                    if len(addon.name) < 26:
                        addon_name = addon.name
                    else:
                        addon_name = addon.name[:23] + "..."

                    Clock.schedule_once(
                        functools.partial(
                            self.show_banner,
                            (0.937, 0.831, 0.62, 1),
                            f"Removed '${addon_name}$' from the queue",
                            "remove-circle-sharp.png",
                            2.5,
                            {"center_x": 0.5, "center_y": 0.965}
                        ), 0.25
                    )

                    if addon in foundry.new_server_info['addon_objects']:
                        foundry.new_server_info['addon_objects'].remove(addon)
                        self.gen_search_results(foundry.new_server_info['addon_objects'])

                        # Switch pages if page is empty
                        if (len(self.scroll_layout.children) == 0) and (len(foundry.new_server_info['addon_objects']) > 0):
                            self.switch_page("left")

                    return addon, selected_button.installed


                # Activated when addon is clicked
                def view_addon(addon, index, *args):
                    selected_button = [item for item in self.scroll_layout.walk() if item.__class__.__name__ == "AddonButton"][index - 1]

                    # Possibly make custom popup that shows differently for Web and File addons
                    Clock.schedule_once(
                        functools.partial(
                            self.show_popup,
                            "query",
                            addon.name,
                            "Do you want to remove this add-on from the queue?",
                            (None, functools.partial(remove_addon, index))
                        ),
                        0
                    )


                # Add-on button click function
                self.scroll_layout.add_widget(
                    ScrollItem(
                        widget = AddonButton(
                            properties = addon_object,
                            installed = True,
                            fade_in = ((x if x <= 8 else 8) / self.anim_speed),

                            show_type = BannerObject(
                                pos_hint = {"center_x": 0.5, "center_y": 0.5},
                                size = (125 if addon_object.addon_object_type == "web" else 100, 32),
                                color = (0.647, 0.839, 0.969, 1) if addon_object.addon_object_type == "web" else (0.6, 0.6, 1, 1),
                                text = "download" if addon_object.addon_object_type == "web" else "import",
                                icon = "cloud-download-sharp.png" if addon_object.addon_object_type == "web" else "download.png",
                                icon_side = "right"
                            ),

                            click_function = functools.partial(
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

    def generate_menu(self, **kwargs):

        # Scroll list
        scroll_widget = ScrollViewWidget(position=(0.5, 0.52))
        scroll_anchor = AnchorLayout()
        self.scroll_layout = GridLayout(cols=1, spacing=15, size_hint_max_x=1250, size_hint_y=None, padding=[0, 30, 0, 30])


        # Bind / cleanup height on resize
        def resize_scroll(call_widget, grid_layout, anchor_layout, *args):
            call_widget.height = Window.height // 1.85
            grid_layout.cols = 2 if Window.width > grid_layout.size_hint_max_x else 1
            self.anim_speed = 13 if Window.width > grid_layout.size_hint_max_x else 10

            def update_grid(*args):
                anchor_layout.size_hint_min_y = grid_layout.height

            Clock.schedule_once(update_grid, 0)


        self.resize_bind = lambda*_: Clock.schedule_once(functools.partial(resize_scroll, scroll_widget, self.scroll_layout, scroll_anchor), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        self.scroll_layout.bind(minimum_height=self.scroll_layout.setter('height'))
        self.scroll_layout.id = 'scroll_content'


        # Scroll gradient
        scroll_top = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.795}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, 60))
        scroll_bottom = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.27}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, -60))

        # Generate buttons on page load
        addon_count = len(foundry.new_server_info['addon_objects'])
        very_bold_font = os.path.join(paths.ui_assets, 'fonts', constants.fonts["very-bold"])
        header_content = f"{translate('Add-on Queue')}  [color=#494977]-[/color]  " + (f'[color=#6A6ABA]{translate("No items")}[/color]' if addon_count == 0 else f'[font={very_bold_font}]1[/font] {translate("item")}' if addon_count == 1 else f'[font={very_bold_font}]{addon_count}[/font] {translate("items")}')
        self.header = HeaderText(header_content, '', (0, 0.89), __translate__ = (False, True))

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

        self.page_switcher = PageSwitcher(0, 0, (0.5, 0.887), self.switch_page)


        # Append scroll view items
        scroll_anchor.add_widget(self.scroll_layout)
        scroll_widget.add_widget(scroll_anchor)
        float_layout.add_widget(scroll_widget)
        float_layout.add_widget(scroll_top)
        float_layout.add_widget(scroll_bottom)
        float_layout.add_widget(self.page_switcher)

        bottom_buttons = RelativeLayout()
        bottom_buttons.size_hint_max_x = 312
        bottom_buttons.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        bottom_buttons.add_widget(MainButton('Import', (0, 0.202), 'download-outline.png', width=300, icon_offset=-115, auto_adjust_icon=True))
        bottom_buttons.add_widget(MainButton('Download', (1, 0.202), 'cloud-download-outline.png', width=300, icon_offset=-115, auto_adjust_icon=True))
        buttons.append(ExitButton('Back', (0.5, 0.11), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)
        float_layout.add_widget(bottom_buttons)

        menu_name = f"Create '{foundry.new_server_info['name']}', Add-ons"
        float_layout.add_widget(generate_title(f"Add-on Manager: '{foundry.new_server_info['name']}'"))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)

        # Automatically generate results (installed add-ons) on page load
        self.gen_search_results(foundry.new_server_info['addon_objects'])

class CreateServerAddonSearchScreen(MenuBackground):

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
            page_list = results[(self.page_size * self.current_page) - self.page_size:self.page_size * self.current_page]

            self.scroll_layout.clear_widgets()


            # Generate header
            addon_count = len(results)
            very_bold_font = os.path.join(paths.ui_assets, 'fonts', constants.fonts["very-bold"])
            search_text = self.search_bar.previous_search if (len(self.search_bar.previous_search) <= 25) else self.search_bar.previous_search[:22] + "..."
            header_content = f"{translate('Search for')} '{search_text}'  [color=#494977]-[/color]  " + (f'[color=#6A6ABA]{translate("No results")}[/color]' if addon_count == 0 else f'[font={very_bold_font}]1[/font] {translate("item")}' if addon_count == 1 else f'[font={very_bold_font}]{addon_count:,}[/font] {translate("items")}')

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
                installed_addon_names = [addon.name for addon in foundry.new_server_info["addon_objects"]]

                # Clear and add all addons
                for x, addon_object in enumerate(page_list, 1):


                    # Function to download addon info
                    def load_addon(addon, index):
                        try:
                            selected_button = [item for item in self.scroll_layout.walk() if item.__class__.__name__ == "AddonButton"][index-1]

                            # Cache updated addon info into button, or skip if it's already cached
                            if selected_button.properties:
                                if not selected_button.properties.versions or not selected_button.properties.description:
                                    new_addon_info = addons.get_addon_info(addon, foundry.new_server_info)
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
                        selected_button = [item for item in self.scroll_layout.walk() if item.__class__.__name__ == "AddonButton"][index-1]
                        addon = selected_button.properties
                        selected_button.toggle_installed(not selected_button.installed)

                        if len(addon.name) < 26:
                            addon_name = addon.name
                        else:
                            addon_name = addon.name[:23] + "..."

                        # Install
                        if selected_button.installed:
                            foundry.new_server_info["addon_objects"].append(addons.get_addon_url(addon, foundry.new_server_info))

                            Clock.schedule_once(
                                functools.partial(
                                    self.show_banner,
                                    (0.553, 0.902, 0.675, 1),
                                    f"Added '${addon_name}$' to the queue",
                                    "add-circle-sharp.png",
                                    2.5,
                                    {"center_x": 0.5, "center_y": 0.965}
                                ), 0.25
                            )

                        # Uninstall
                        else:
                            for installed_addon_object in foundry.new_server_info["addon_objects"]:
                                if installed_addon_object.name == addon.name:
                                    foundry.new_server_info["addon_objects"].remove(installed_addon_object)

                                    Clock.schedule_once(
                                        functools.partial(
                                            self.show_banner,
                                            (0.937, 0.831, 0.62, 1),
                                            f"Removed '${addon_name}$' from the queue",
                                            "remove-circle-sharp.png",
                                            2.5,
                                            {"center_x": 0.5, "center_y": 0.965}
                                        ), 0.25
                                    )

                                    break

                        return addon, selected_button.installed


                    # Activated when addon is clicked
                    def view_addon(addon, index, *args):
                        selected_button = [item for item in self.scroll_layout.walk() if item.__class__.__name__ == "AddonButton"][index - 1]

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
                            widget = AddonButton(
                                properties = addon_object,
                                installed = addon_object.name in installed_addon_names,
                                fade_in = ((x if x <= 8 else 8) / self.anim_speed),
                                click_function = functools.partial(
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
        self.scroll_layout = GridLayout(cols=1, spacing=15, size_hint_max_x=1250, size_hint_y=None, padding=[0, 30, 0, 30])


        # Bind / cleanup height on resize
        def resize_scroll(call_widget, grid_layout, anchor_layout, *args):
            call_widget.height = Window.height // 1.79
            grid_layout.cols = 2 if Window.width > grid_layout.size_hint_max_x else 1
            self.anim_speed = 13 if Window.width > grid_layout.size_hint_max_x else 10

            def update_grid(*args):
                anchor_layout.size_hint_min_y = grid_layout.height

            Clock.schedule_once(update_grid, 0)


        self.resize_bind = lambda*_: Clock.schedule_once(functools.partial(resize_scroll, scroll_widget, self.scroll_layout, scroll_anchor), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        self.scroll_layout.bind(minimum_height=self.scroll_layout.setter('height'))
        self.scroll_layout.id = 'scroll_content'

        # Scroll gradient
        scroll_top = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.715}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, 60))
        scroll_bottom = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.17}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, -60))

        # Generate buttons on page load
        addon_count = 0
        very_bold_font = os.path.join(paths.ui_assets, 'fonts', constants.fonts["very-bold"])
        header_content = translate("Add-on Search")
        self.header = HeaderText(header_content, '', (0, 0.89), __translate__ = (False, True))

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


        search_function = addons.search_addons
        self.search_bar = search_input(return_function=search_function, server_info=foundry.new_server_info, pos_hint={"center_x": 0.5, "center_y": 0.795})
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

        menu_name = f"Create '{foundry.new_server_info['name']}', Add-ons, Download"
        float_layout.add_widget(generate_title(f"Add-on Manager: '{foundry.new_server_info['name']}'"))
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



# Create Server Step 7 (end):  Server Review ---------------------------------------------------------------------------

class CreateServerReviewScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'

    def generate_menu(self, **kwargs):

        # Fulfill prerequisites if skipped somehow
        foundry.new_server_name()

        if not foundry.new_server_info['version']:
            server_type = foundry.new_server_info['type']
            foundry.new_server_info['version'] = foundry.latestMC[server_type]
            if server_type in ['forge', 'paper']:
                foundry.new_server_info['build'] = foundry.latestMC['builds'][server_type]

        if not foundry.new_server_info['acl_object']:
            foundry.new_server_info['acl_object'] = acl.AclManager(foundry.new_server_info['name'])


        # Scroll list
        scroll_widget = ScrollViewWidget()
        scroll_anchor = AnchorLayout()
        scroll_layout = GridLayout(cols=1, spacing=10, size_hint_max_x=(1050 if constants.app_config.locale == 'en' else 1130), size_hint_y=None, padding=[0, -10, 0, 60])


        # Bind / cleanup height on resize
        def resize_scroll(call_widget, grid_layout, anchor_layout, *args):
            call_widget.height = Window.height // 2.05
            call_widget.pos_hint = {"center_y": 0.51}
            grid_layout.cols = 2 if Window.width > grid_layout.size_hint_max_x else 1

            def update_grid(*args):
                anchor_layout.size_hint_min_y = grid_layout.height

            Clock.schedule_once(update_grid, 0)


        self.resize_bind = lambda*_: Clock.schedule_once(functools.partial(resize_scroll, scroll_widget, scroll_layout, scroll_anchor), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        scroll_layout.bind(minimum_height=scroll_layout.setter('height'))
        scroll_layout.id = 'scroll_content'

        # Scroll gradient
        scroll_top = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.735}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, 60))
        scroll_bottom = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.272}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, -60))

        # Generate buttons on page load
        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'
        float_layout.add_widget(HeaderText(f"Please verify your configuration", '', (0, 0.89), no_line=True))

        pgh_font = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["mono-medium"]}.otf')


        # Create and add paragraphs to GridLayout
        def create_paragraph(name, text, cid):

            # Dirty fix to anchor paragraphs to the top
            def repos(p, s, *args):
                if scroll_layout.cols == 2:
                    if s.height != scroll_layout._rows[cid]:
                        p.y = scroll_layout._rows[cid] - s.height

                    if cid == 0:
                        for child in scroll_layout.children:
                            if child != s and child.x == s.x:
                                p2 = child.children[0]
                                p2.y = p.y
                                break
                else:
                    p.y = 0


            # Format spacing appropriately for content
            if constants.app_config.locale == 'en':
                paragraph_width = 485
                for line in text.splitlines():
                    if '||' in line:
                        new_line = line.replace(' ||', ' ', 1)
                        text = text.replace(line, new_line)

            else:
                # Find the longest key in a paragraph to dynamically generate spacing
                paragraph_width = 530
                longest = 0
                for line in text.splitlines():
                    if '||' in line:
                        key = line.split('||', 1)[0].strip()
                        if len(key) > longest:
                            longest = len(key)

                longest += 3

                # Replace text with proper spacing
                for line in text.splitlines():
                    if '||' in line:
                        key, value = line.split('||', 1)
                        text = text.replace(line, f'{key.strip()}{(longest - len(key.strip())) * " "}{value}')

            sub_layout = ScrollItem()
            content_size = sp(22)
            content_height = len(text.splitlines()) * (content_size + sp(9))
            paragraph = paragraph_object(size=(paragraph_width, content_height), name=name, content=text, font_size=content_size, font=pgh_font)
            sub_layout.height = paragraph.height + 60

            sub_layout.bind(pos=functools.partial(repos, paragraph, sub_layout, cid))
            sub_layout.bind(size=functools.partial(repos, paragraph, sub_layout, cid))

            sub_layout.add_widget(paragraph)
            scroll_layout.add_widget(sub_layout)



        # ----------------------------------------------- General ------------------------------------------------------
        content = ""
        content += f"[color=6666AA]{translate('Name')}:      ||[/color]{foundry.new_server_info['name']}\n"
        content += f"[color=6666AA]{translate('Type')}:      ||[/color]{foundry.new_server_info['type'].title()}\n"
        content += f"[color=6666AA]{translate('Version')}:   ||[/color]{foundry.new_server_info['version']}"
        if foundry.new_server_info['build']:
            content += f" ({foundry.new_server_info['build']})"
        content += "\n\n"
        if foundry.new_server_info['server_settings']['world'] == "world":
            content += f"[color=6666AA]{translate('World')}:     ||[/color]{translate('Create a new world')}\n"
            if foundry.new_server_info['server_settings']['level_type']:
                content += f"[color=6666AA]{translate('Type')}:      ||[/color]{translate(foundry.new_server_info['server_settings']['level_type'].title())}\n"
            if foundry.new_server_info['server_settings']['seed']:
                content += f"[color=6666AA]{translate('Seed')}:      ||[/color]{foundry.new_server_info['server_settings']['seed']}\n"
        else:
            box_text = os.path.join(*Path(os.path.abspath(foundry.new_server_info['server_settings']['world'])).parts[-2:])
            box_text = box_text[:27] + "..." if len(box_text) > 27 else box_text
            content += f"[color=6666AA]{translate('World')}:     [/color]{box_text}\n"

        def check_enabled(var):
            if var:
                return '[/color]' + translate('Enabled')
            else:
                return translate('Disabled') + '[/color]'
        create_paragraph('general', content, 0)
        # --------------------------------------------------------------------------------------------------------------



        # ----------------------------------------------- Options ------------------------------------------------------
        content = ""
        content += f"[color=6666AA]{translate('Gamemode')}:             ||[/color]{translate(foundry.new_server_info['server_settings']['gamemode'].title())}\n"
        content += f"[color=6666AA]{translate('Difficulty')}:           ||[/color]{translate(foundry.new_server_info['server_settings']['difficulty'].title())}\n"
        content += f"[color=6666AA]PVP:                  ||{check_enabled(foundry.new_server_info['server_settings']['pvp'])}\n"
        content += f"[color=6666AA]{translate('Spawn protection')}:     ||{check_enabled(foundry.new_server_info['server_settings']['spawn_protection'])}"

        content += "\n\n"

        if constants.version_check(foundry.new_server_info['version'], ">=", "1.4.2"):
            content += f"[color=6666AA]{translate('Keep inventory')}:       ||{check_enabled(foundry.new_server_info['server_settings']['keep_inventory'])}\n"

        content += f"[color=6666AA]{translate('Spawn creatures')}:      ||{check_enabled(foundry.new_server_info['server_settings']['spawn_creatures'])}\n"

        if constants.version_check(foundry.new_server_info['version'], ">=", "1.4.2"):
            if constants.version_check(foundry.new_server_info['version'], ">=", "1.11"):
                content += f"[color=6666AA]{translate('Daylight/weather')}:     ||{check_enabled(foundry.new_server_info['server_settings']['daylight_weather_cycle'])}\n"
            else:
                content += f"[color=6666AA]{translate('Daylight cycle')}:       ||{check_enabled(foundry.new_server_info['server_settings']['daylight_weather_cycle'] )}\n"

        content += f"[color=6666AA]{translate('Command blocks')}:       ||{check_enabled(foundry.new_server_info['server_settings']['command_blocks'])}\n"

        if constants.version_check(foundry.new_server_info['version'], ">=", "1.19") and foundry.new_server_info['type'].lower() != "vanilla":
            content += f"[color=6666AA]{translate('Chat reporting')}:       ||{check_enabled(not foundry.new_server_info['server_settings']['disable_chat_reporting'])}\n"

        if constants.version_check(foundry.new_server_info['version'], ">=", "1.4.2"):
            content += f"[color=6666AA]{translate('Random tick speed')}:    ||[/color]{foundry.new_server_info['server_settings']['random_tick_speed']} {translate('ticks')}"

        create_paragraph('options', content, 0)
        # --------------------------------------------------------------------------------------------------------------



        # ----------------------------------------------- Network ------------------------------------------------------
        formatted_ip = ("localhost" if not foundry.new_server_info['ip'] else foundry.new_server_info['ip']) + f":{foundry.new_server_info['port']}"
        max_plr = foundry.new_server_info['server_settings']['max_players']
        formatted_players = (max_plr + translate(' players' if int(max_plr) != 1 else ' player'))
        content = ""
        content += f"[color=6666AA]{translate('Server IP')}:      ||[/color]{formatted_ip}\n"
        content += f"[color=6666AA]{translate('Max players')}:    ||[/color]{formatted_players}\n"
        if foundry.new_server_info['server_settings']['geyser_support']:
            content += f"[color=6666AA]Geyser:         ||[/color]{translate('Enabled')}"

        content += "\n\n"

        if foundry.new_server_info['server_settings']['motd'].lower() == 'a minecraft server':
            content += f"[color=6666AA]MOTD:\n[/color]{translate('A Minecraft Server')}"
        else:
            content += f"[color=6666AA]MOTD:\n[/color]{foundry.new_server_info['server_settings']['motd']}"

        content += "\n\n\n"

        rule_count = foundry.new_server_info['acl_object'].count_rules()
        if rule_count['total'] > 0:
            content += f"[color=6666AA]          {translate('Access Control Rules')}[/color]"

            if rule_count['ops'] > 0:
                content += "\n\n"
                content += f"[color=6666AA]{translate('Operators')} ({rule_count['ops']:,}):[/color]\n"
                content += '    ' + '\n    '.join([rule.rule for rule in foundry.new_server_info['acl_object'].rules['ops']])

            if rule_count['bans'] > 0:
                content += "\n\n"
                content += f"[color=6666AA]{translate('Bans')} ({rule_count['bans']:,}):[/color]\n"
                bans = acl.deepcopy(foundry.new_server_info['acl_object'].rules['bans'])
                bans.extend(acl.deepcopy(foundry.new_server_info['acl_object'].rules['subnets']))
                content += '    ' + '\n    '.join([rule.rule if '!w' not in rule.rule else rule.rule.replace('!w','').strip()+f' ({translate("whitelist")})' for rule in bans])

            if rule_count['wl'] > 0:
                content += "\n\n"
                content += f"[color=6666AA]{translate('Whitelist')} ({rule_count['wl']:,}):[/color]\n"
                content += '    ' + '\n    '.join([rule.rule for rule in foundry.new_server_info['acl_object'].rules['wl']])

        create_paragraph('network', content, 1)
        # --------------------------------------------------------------------------------------------------------------



        # ------------------------------------------------ Addons ------------------------------------------------------
        if len(foundry.new_server_info['addon_objects']) > 0:
            content = ""
            addons_sorted = {'import': [], 'download': []}
            [addons_sorted['import' if addon.addon_object_type == 'file' else 'download'].append(addon.name) for addon in foundry.new_server_info['addon_objects']]

            if len(addons_sorted['download']) > 0:
                content += f"[color=6666AA]{translate('Add-ons to download')} ({len(addons_sorted['download']):,}):[/color]\n"
                content += '    ' + '\n    '.join([(item[:32]+'...' if len(item) > 35 else item) for item in addons_sorted['download']])

                if len(addons_sorted['import']) > 0:
                    content += "\n\n"

            if len(addons_sorted['import']) > 0:
                content += f"[color=6666AA]{translate('Add-ons to import')} ({len(addons_sorted['import']):,}):[/color]\n"
                content += '    ' + '\n    '.join([(item[:32]+'...' if len(item) > 35 else item) for item in addons_sorted['import']])

            create_paragraph('add-ons', content, 1)
        # --------------------------------------------------------------------------------------------------------------



        # Append scroll view items
        scroll_anchor.add_widget(scroll_layout)
        scroll_widget.add_widget(scroll_anchor)
        float_layout.add_widget(scroll_widget)
        float_layout.add_widget(scroll_top)
        float_layout.add_widget(scroll_bottom)


        # Server Preview Box
        float_layout.add_widget(server_demo_input(pos_hint={"center_x": 0.5, "center_y": 0.81}, properties=foundry.new_server_info))


        buttons.append(MainButton('Create Server', (0.5, 0.22), 'checkmark-circle-outline.png'))
        buttons.append(ExitButton('Back', (0.5, 0.12), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)

        menu_name = f"Create '{foundry.new_server_info['name']}'"
        float_layout.add_widget(page_counter(7, 7, (0, 0.815)))
        float_layout.add_widget(generate_title(menu_name))
        float_layout.add_widget(generate_footer(f"{menu_name}, Verify"))

        self.add_widget(float_layout)


# Create Server Progress Screen ----------------------------------------------------------------------------------------
class CreateServerProgressScreen(ProgressScreen):

    # Only replace this function when making a child screen
    # Set fail message in child functions to trigger an error
    def contents(self):
        open_after = functools.partial(self.open_server, foundry.new_server_info['name'], True, f"'${foundry.new_server_info['name']}$' was created successfully")

        def before_func(*args):

            if not constants.app_online:
                self.execute_error("An internet connection is required to continue\n\nVerify connectivity and try again")

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
            'title': f"Creating '${foundry.new_server_info['name']}$'",

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
            ("Downloading 'server.jar'", functools.partial(foundry.download_jar, functools.partial(adjust_percentage, 30)), 0)
        ]

        download_addons = False
        needs_installed = False

        if foundry.new_server_info['type'] != 'vanilla':
            download_addons = foundry.new_server_info['addon_objects'] or foundry.new_server_info['server_settings']['disable_chat_reporting'] or foundry.new_server_info['server_settings']['geyser_support'] or (foundry.new_server_info['type'] in ['fabric', 'quilt'])
            needs_installed = foundry.new_server_info['type'] in ['forge', 'neoforge', 'fabric', 'quilt']

        if needs_installed:
            function_list.append((f'Installing ${foundry.new_server_info["type"].title().replace("forge","Forge")}$', functools.partial(foundry.install_server), 10 if download_addons else 20))

        if download_addons:
            function_list.append(('Add-oning add-ons', functools.partial(foundry.iter_addons, functools.partial(adjust_percentage, 10 if needs_installed else 20)), 0))

        function_list.append(('Applying server configuration', functools.partial(foundry.generate_server_files), 10 if (download_addons or needs_installed) else 20))


        function_list.append(('Creating initial back-up', functools.partial(foundry.create_backup), 10 if (download_addons or needs_installed) else 20))


        self.page_contents['function_list'] = tuple(function_list)

# </editor-fold> ///////////////////////////////////////////////////////////////////////////////////////////////////////
