from source.ui.desktop.views.templates import *
from source.ui.desktop.widgets.base import *



#  =============================================== Create Server =======================================================
# <editor-fold desc="Create Server">


# Create Server Menu Components ----------------------------------------------------------------------------------------

# Button for displaying an available '.ist' template in 'CreateServerTemplateScreen'
class TemplateButton(HoverButton):

    def animate_button(self, image, color, hover_action, **kwargs):
        image_animate = Animation(duration=0.05)

        Animation(color=color, duration=0.06).start(self.title)
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
        self.title.pos = (self.x + (self.title.text_size[0] / padding) - (8.3) + 30, self.y + 31)
        self.subtitle.pos = (self.x + (self.subtitle.text_size[0] / padding) - 78, self.y + 8)


        offset = 9.45 if self.type_image.type_label.text in ["vanilla", "paper", "purpur"]\
            else 9.6 if self.type_image.type_label.text == "forge"\
            else 9.35 if self.type_image.type_label.text == "craftbukkit"\
            else 9.55


        self.type_image.image.x = self.width + self.x - (self.type_image.image.width) - 13
        self.type_image.image.y = self.y + ((self.height / 2) - (self.type_image.image.height / 2))


        self.type_image.type_label.x = self.width + self.x - (self.padding_x * offset) - self.type_image.width - 83
        self.type_image.type_label.y = self.y + (self.height * 0.05)

        # Update label
        if self.type_image.version_label.__class__.__name__ == "AlignLabel":
            self.type_image.version_label.x = self.width + self.x - (self.padding_x * offset) - self.type_image.width - 83
            self.type_image.version_label.y = self.y - (self.height / 3.2)

        # Favorite button
        self.customize_layout.size_hint_max = (self.size_hint_max[0], self.size_hint_max[1])
        self.customize_layout.pos = (self.pos[0] - 6, self.pos[1] + 13)

    def __init__(self, template, fade_in=0.0, **kwargs):
        super().__init__(**kwargs)

        self.template = template
        self.border = (-5, -5, -5, -5)
        self.color_id = [(0.05, 0.05, 0.1, 1), constants.brighten_color((0.65, 0.65, 1, 1), 0.07)]
        self.pos_hint = {"center_x": 0.5, "center_y": 0.6}
        self.size_hint_max = (580, 80)
        self.id = "server_button"

        self.background_normal = os.path.join(paths.ui_assets, f'{self.id}.png')
        self.background_down = os.path.join(paths.ui_assets, f'{self.id}_click.png')


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
        self.title.text = template['template']['name']
        self.add_widget(self.title)


        # Server last modified date formatted
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
        self.subtitle.color = self.color_id[1]
        self.subtitle.default_opacity = 0.56
        self.subtitle.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["regular"]}.ttf')

        self.subtitle.text = template['template']['description']

        self.subtitle.opacity = self.subtitle.default_opacity

        self.add_widget(self.subtitle)


        # Type icon and info
        self.type_image = RelativeLayout()
        self.type_image.width = 400

        server_icon = os.path.join(paths.ui_assets, 'icons', 'big', f"{template['server']['type']}_small.png")
        self.type_image.image = Image(source=server_icon)

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
        self.type_image.version_label.text = template['server']['version']
        self.type_image.version_label.opacity = 0.6


        self.type_image.type_label = TemplateLabel()

        type_text = template['server']['type'].lower().replace("craft", "")
        self.type_image.type_label.text = type_text
        self.type_image.type_label.font_size = sp(23)
        self.type_image.add_widget(self.type_image.version_label)
        self.type_image.add_widget(self.type_image.type_label)
        self.add_widget(self.type_image)


        # Favorite button
        self.customize_layout = RelativeLayout()

        def customize_with_template(*a):
            foundry.apply_template(self.template)
            utility.screen_manager.current = 'CreateServerNameScreen'

        def create_with_template(*a):
            foundry.apply_template(self.template)
            utility.screen_manager.current = 'CreateServerProgressScreen'

        self.customize_button = IconButton('', {}, (0, 0), (None, None), 'settings-sharp.png', clickable=True, anchor='right', click_func=customize_with_template)

        self.customize_layout.add_widget(self.customize_button)
        self.add_widget(self.customize_layout)

        self.bind(pos=self.resize_self)
        self.bind(on_press=create_with_template)

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
            self.animate_button(image=os.path.join(paths.ui_assets, f'{self.id}.png'), color=self.color_id[1], hover_action=False)


# Create demo of how the server will appear in the Server Manager:
class ServerDemoInput(BaseInput):

    class TemplateLabel(AlignLabel):
        def __init__(self, _p, *a, **kw):
            super().__init__(*a, **kw)
            self.halign = "right"
            self.valign = "middle"
            self.text_size = self.size
            self.font_size = sp(18)
            self.color = _p.foreground_color
            self.font_name = _p.font_name
            self.width = 200

    def resize_self(self, *args):
        offset = 9.45 if self.type_image.type_label.text in ["vanilla", "paper", "purpur"]\
            else 9.6 if self.type_image.type_label.text == "forge"\
            else 9.35 if self.type_image.type_label.text == "craftbukkit"\
            else 9.55

        self.type_image.image.x = self.width+self.x-self.type_image.image.width-self.padding_x[0]+10
        self.type_image.image.y = self.y+(self.padding_y[0]/2.7)

        self.title_t.pos = (self.x + 185, self.y - 7)

        # Telepath icon
        if self.type_image.tp_shadow:
            self.type_image.tp_shadow.pos = (self.type_image.image.x - 2, self.type_image.image.y)
            self.type_image.tp_icon.pos = (self.type_image.image.x - 2, self.type_image.image.y)

        self.type_image.type_label.x = (self.width+self.x-(self.padding_x[0]*offset)) - 3
        self.type_image.type_label.y = self.y+(self.padding_y[0]/6.9)

        self.type_image.version_label.x = (self.width+self.x-(self.padding_x[0]*offset)) - 3
        self.type_image.version_label.y = self.y-(self.padding_y[0]*0.85)

    def __init__(self, properties: dict, pos_hint: dict, **kwargs):
        super().__init__(**kwargs)

        self.halign = "left"
        self.properties = properties  # {"type": "", "version": "", "name": ""}
        self.padding_x = 30
        self.padding_y = 24.5
        self.font_size = sp(25)
        self.size_hint_max = (580, 80)
        self.hint_text_color = (0.65, 0.65, 1, 1)
        self.background_normal = os.path.join(paths.ui_assets, 'server_preview.png')
        self.title_text = ""
        self.hint_text = ""
        self.markup = True


        # Type icon and info
        with self.canvas.after:
            self.type_image = RelativeLayout()
            self.type_image.image = Image(source=None)
            self.type_image.image.allow_stretch = True
            self.type_image.image.size = (62, 62)
            self.type_image.image.color = (0.65, 0.65, 1, 1)
            self.type_image.version_label = self.TemplateLabel(self)
            self.type_image.version_label.color = (0.6, 0.6, 1, 0.6)
            self.type_image.type_label = self.TemplateLabel(self)
            self.type_image.type_label.font_size = sp(22)
            self.type_image.tp_shadow = None

            self.bind(pos=self.resize_self)

            self.title_t = AlignLabel(halign='left', valign='center')
            self.title_t.font_size = sp(25)
            self.title_t.size_hint_max = (400, 80)
            self.title_t.text_size = self.title_t.size_hint_max
            self.title_t.color = (0.65, 0.65, 1, 1)
            self.title_t.markup = True
            self.title_t.font_name = self.font_name
            self.add_widget(self.title_t)


        # Initialize custom properties
        self.properties = properties
        self.pos_hint = pos_hint
        self.__translate__ = False
        self.title_t.text = properties['name']
        self.type_image.version_label.__translate__ = False
        self.type_image.version_label.text = properties['version']
        self.type_image.type_label.__translate__ = False
        self.type_image.type_label.text = properties['type'].lower().replace("craft", "")
        self.type_image.image.source = os.path.join(paths.ui_assets, 'icons', 'big', f'{properties["type"].lower()}_small.png')

        if utility.screen_manager.current.startswith('CreateServer'): send_log('CreateServer', f"menu progress:\n{properties}", 'info')
        if properties['_telepath_data']:
            if properties['_telepath_data']['nickname']: head = properties['_telepath_data']['nickname']
            else:                                        head = properties['_telepath_data']['host']

            self.title_t.text = f"[color=#7373A2]{head}/[/color]{properties['name']}"

            with self.canvas.after:
                self.type_image.tp_shadow = Image(source=icon_path('shadow.png'))
                self.type_image.tp_shadow.allow_stretch = True
                self.type_image.tp_shadow.size_hint_max = (33, 33)
                self.type_image.tp_shadow.color = constants.background_color
                self.type_image.add_widget(self.type_image.tp_shadow)

                self.type_image.tp_icon = Image(source=icon_path('telepath.png'))
                self.type_image.tp_icon.allow_stretch = True
                self.type_image.tp_icon.size_hint_max = (33, 33)
                self.type_image.tp_icon.color = self.type_image.image.color
                self.type_image.add_widget(self.type_image.tp_icon)

    # Make the text box non-interactive
    def on_enter(self, value):
        return

    def on_touch_down(self, touch):
        self.focus = False

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        return

    def insert_text(self, substring, from_undo=False):
        return



# Root Menus -----------------------------------------------------------------------------------------------------------

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
            if not foundry.ist_data: foundry.get_repo_templates()


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


            self.resize_bind = lambda*_: Clock.schedule_once(functools.partial(resize_scroll, scroll_widget, self.scroll_layout, scroll_anchor), 0)
            self.resize_bind()
            Window.bind(on_resize=self.resize_bind)
            self.scroll_layout.bind(minimum_height=self.scroll_layout.setter('height'))
            self.scroll_layout.id = 'scroll_content'


            # Scroll gradient
            scroll_top = ScrollBackground(pos_hint={"center_x": 0.5, "center_y": 0.795}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, 60))
            scroll_bottom = ScrollBackground(pos_hint={"center_x": 0.5, "center_y": 0.26}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, -60))

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


        for button in buttons: float_layout.add_widget(button)

        menu_name = "Instant Server"
        float_layout.add_widget(generate_title("Instant Server"))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)

        if constants.app_online: self.gen_search_results(list(foundry.ist_data.values()))



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
            self.next_button = NextButton('Next', (0.5, 0.24), not foundry.new_server_info['name'], next_screen='CreateServerTypeScreen')
            buttons.append(self.next_button)
            buttons.append(ExitButton('Back', (0.5, 0.14), cycle=True))
            float_layout.add_widget(PageCounter(1, 7, (0, 0.768)))

        for button in buttons: float_layout.add_widget(button)


        # Add telepath button if servers are connected
        if constants.server_manager.online_telepath_servers:
            float_layout.add_widget(TelepathDropButton('create', (0.5, 0.4)))


        float_layout.add_widget(generate_title('Create New Server'))
        float_layout.add_widget(generate_footer('Create new server'))

        self.add_widget(float_layout)


        if constants.app_online: self.name_input.grab_focus()



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
        buttons.append(NextButton('Next', (0.5, 0.21), False, next_screen='CreateServerVersionScreen'))
        buttons.append(ExitButton('Back', (0.5, 0.12), cycle=True))


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
        menu_name = f"Create '{foundry.new_server_info['name']}'"

        float_layout.add_widget(PageCounter(2, 7, (0, 0.868)))
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
            def validate(*a):
                self.next_button.loading(True)
                version_data = foundry.search_version(foundry.new_server_info)
                foundry.new_server_info['version']  = version_data[1]['version']
                foundry.new_server_info['build']    = version_data[1]['build']
                foundry.new_server_info['jar_link'] = version_data[3]
                success = version_data[0] and not version_data[2]
                if success: self.next_button.button.ignore_hover = True
                self.next_button.loading(False)

                # Continue to next screen if valid input, and back button not pressed
                if success and utility.screen_manager.current == 'CreateServerVersionScreen':
                    def _apply(*a):

                        # Reset geyser_selected if version is less than 1.13.2
                        if constants.version_check(self.version_input.text, "<", "1.13.2") or foundry.new_server_info['type'] not in ['spigot', 'paper', 'purpur', 'fabric', 'quilt', 'neoforge']:
                            foundry.new_server_info['server_settings']['geyser_support'] = False

                        # Reset gamerule settings if version is less than 1.4.2
                        if constants.version_check(self.version_input.text, "<", "1.4.2"):
                            foundry.new_server_info['server_settings']['keep_inventory'] = False
                            foundry.new_server_info['server_settings']['daylight_weather_cycle'] = True
                            foundry.new_server_info['server_settings']['command_blocks'] = False
                            foundry.new_server_info['server_settings']['random_tick_speed'] = "3"

                        # Reset level_type if level type not supported
                        if (
                            (constants.version_check(self.version_input.text, "<", "1.1")) or
                            (constants.version_check(self.version_input.text, "<", "1.3.1") and foundry.new_server_info['server_settings']['level_type'] not in ['default', 'flat']) or
                            (constants.version_check(self.version_input.text, "<", "1.7.2") and foundry.new_server_info['server_settings']['level_type'] not in ['default', 'flat', 'large_biomes'])
                        ):
                            foundry.new_server_info['server_settings']['level_type'] = "default"

                        # Disable chat reporting
                        disable_reporting = constants.version_check(self.version_input.text, "<", "1.19") or foundry.new_server_info['type'] == "vanilla"
                        foundry.new_server_info['server_settings']['disable_chat_reporting'] = disable_reporting

                        # Check for potential world incompatibilities
                        if foundry.new_server_info['server_settings']['world'] != "world":
                            check_world = constants.check_world_version(foundry.new_server_info['server_settings']['world'], foundry.new_server_info['version'])
                            if not check_world[0] and check_world[1]: foundry.new_server_info['server_settings']['world'] = "world"

                        self.version_input.valid_text(True, True)
                        utility.screen_manager.current = 'CreateServerWorldScreen'
                    Clock.schedule_once(_apply, 0)

                # Failed to apply
                else:
                    def _failed(*a):
                        self.version_input.focus = False
                        self.version_input.valid(version_data[0], version_data[2])
                        self.next_button.disable(not version_data[0])
                    Clock.schedule_once(_failed, 0)

            float_layout.add_widget(InputLabel(pos_hint={"center_x": 0.5, "center_y": 0.58}))
            float_layout.add_widget(PageCounter(3, 7, (0, 0.768)))
            float_layout.add_widget(HeaderText("What version of Minecraft do you wish to play?", '', (0, 0.76)))
            self.version_input = ServerVersionInput(pos_hint={"center_x": 0.5, "center_y": 0.5}, text=foundry.new_server_info['version'])
            float_layout.add_widget(self.version_input)
            self.next_button = NextButton('Next', (0.5, 0.24), False, click_func=validate, show_load_icon=True)
            buttons.append(self.next_button)
            buttons.append(ExitButton('Back', (0.5, 0.14), cycle=True))

        for button in buttons: float_layout.add_widget(button)

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
        buttons.append(InputButton('Browse...', (0.5, 0.55), ('dir', paths.minecraft_saves if os.path.isdir(paths.minecraft_saves) else paths.user_downloads), input_name='CreateServerWorldInput', title='Select a World File'))

        server_version = foundry.new_server_info['version']
        if constants.version_check(server_version, '>=', "1.1"):
            options = ['normal', 'superflat']
            if constants.version_check(server_version, '>=', "1.3.1"):
                options.append('large biomes')
            if constants.version_check(server_version, '>=', "1.7.2"):
                options.append('amplified')
            default_name = foundry.new_server_info['server_settings']['level_type'].replace("default", "normal").replace("flat", "superflat").replace("large_biomes", "large biomes")
            float_layout.add_widget(DropButton(default_name, (0.5, 0.442), options_list=options, input_name='ServerLevelTypeInput', x_offset=41))

        buttons.append(NextButton('Next', (0.5, 0.24), False, next_screen='CreateServerNetworkScreen'))
        buttons.append(ExitButton('Back', (0.5, 0.14), cycle=True))

        for button in buttons: float_layout.add_widget(button)

        menu_name = f"Create '{foundry.new_server_info['name']}'"
        float_layout.add_widget(PageCounter(4, 7, (0, 0.768)))
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

            except AttributeError: pass



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
                scroll_top.resize(); scroll_bottom.resize()

            Clock.schedule_once(update_grid, 0)


        self.resize_bind = lambda*_: Clock.schedule_once(functools.partial(resize_scroll, scroll_widget, scroll_layout, scroll_anchor), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        scroll_layout.bind(minimum_height=scroll_layout.setter('height'))
        scroll_layout.id = 'scroll_content'

        # Scroll gradient
        scroll_top = ScrollBackground(pos_hint={"center_x": 0.5, "center_y": 0.77}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, 60))
        scroll_bottom = ScrollBackground(pos_hint={"center_x": 0.5, "center_y": 0.272}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, -60))


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
        def toggle_proxy(boolean): foundry.new_server_info['server_settings']['enable_proxy'] = boolean
        sub_layout.add_widget(BlankInput(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text='enable proxy (playit)'))
        sub_layout.add_widget(SwitchButton('proxy', (0.5, 0.5), custom_func=toggle_proxy, default_state=foundry.new_server_info['server_settings']['enable_proxy']))
        scroll_layout.add_widget(sub_layout)


        # Append scroll view items
        scroll_anchor.add_widget(scroll_layout)
        scroll_widget.add_widget(scroll_anchor)
        float_layout.add_widget(scroll_widget)
        float_layout.add_widget(scroll_top)
        float_layout.add_widget(scroll_bottom)

        float_layout.add_widget(HeaderText("Do you wish to configure network information?", '', (0, 0.83)))

        self.next_button = NextButton('Next', (0.5, 0.24), False, next_screen='CreateServerOptionsScreen')
        buttons.append(self.next_button)
        buttons.append(ExitButton('Back', (0.5, 0.14), cycle=True))

        for button in buttons: float_layout.add_widget(button)

        menu_name = f"Create '{foundry.new_server_info['name']}'"
        float_layout.add_widget(PageCounter(5, 7, (0, 0.838)))
        float_layout.add_widget(generate_title(menu_name))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)



# Create Server Step 6:  Server Options --------------------------------------------------------------------------------

# Create ACL options, and Addon Options
class CreateServerOptionsScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'

    def generate_menu(self, **kwargs):

        # Blocking wait to prevent a crash if the AclObject isn't loaded yet
        if not foundry.new_server_info['acl_object']:
            while not foundry.new_server_info['acl_object']:
                time.sleep(0.2)

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
                scroll_top.resize(); scroll_bottom.resize()

            Clock.schedule_once(update_grid, 0)


        self.resize_bind = lambda*_: Clock.schedule_once(functools.partial(resize_scroll, scroll_widget, scroll_layout, scroll_anchor), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        scroll_layout.bind(minimum_height=scroll_layout.setter('height'))
        scroll_layout.id = 'scroll_content'

        # Scroll gradient
        scroll_top = ScrollBackground(pos_hint={"center_x": 0.5, "center_y": 0.77}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, 60))
        scroll_bottom = ScrollBackground(pos_hint={"center_x": 0.5, "center_y": 0.272}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, -60))

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
        sub_layout.add_widget(BlankInput(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="gamemode"))
        sub_layout.add_widget(DropButton(foundry.new_server_info['server_settings']['gamemode'], (0.5, 0.5), options_list=['survival', 'adventure', 'creative'], input_name='ServerModeInput'))
        scroll_layout.add_widget(sub_layout)

        # Difficulty dropdown
        sub_layout = ScrollItem()
        sub_layout.add_widget(BlankInput(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="difficulty"))
        sub_layout.add_widget(DropButton(foundry.new_server_info['server_settings']['difficulty'], (0.5, 0.5), options_list=['peaceful', 'easy', 'normal', 'hard', 'hardcore'], input_name='ServerDiffInput'))
        scroll_layout.add_widget(sub_layout)

        # Geyser switch for bedrock support
        if constants.version_check(foundry.new_server_info['version'], ">=", "1.13.2") \
        and foundry.new_server_info['type'].lower() in ['spigot', 'paper', 'purpur', 'fabric', 'quilt', 'neoforge']:
            sub_layout = ScrollItem()
            sub_layout.add_widget(BlankInput(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="bedrock support (geyser)"))
            sub_layout.add_widget(SwitchButton('geyser_support', (0.5, 0.5), default_state=foundry.new_server_info['server_settings']['geyser_support']))
            scroll_layout.add_widget(sub_layout)

        # Disable chat reporting by default
        if constants.version_check(foundry.new_server_info['version'], ">=", "1.19") \
        and foundry.new_server_info['type'].lower() != "vanilla":
            sub_layout = ScrollItem()
            sub_layout.add_widget(BlankInput(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="disable chat reporting"))
            sub_layout.add_widget(SwitchButton('chat_report', (0.5, 0.5), default_state=foundry.new_server_info['server_settings']['disable_chat_reporting']))
            scroll_layout.add_widget(sub_layout)

        # PVP switch button
        sub_layout = ScrollItem()
        sub_layout.add_widget(BlankInput(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="enable PVP"))
        sub_layout.add_widget(SwitchButton('pvp', (0.5, 0.5), default_state=foundry.new_server_info['server_settings']['pvp']))
        scroll_layout.add_widget(sub_layout)

        # Enable keep inventory
        if constants.version_check(foundry.new_server_info['version'], ">=", "1.4.2"):
            sub_layout = ScrollItem()
            sub_layout.add_widget(BlankInput(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="keep inventory"))
            sub_layout.add_widget(SwitchButton('keep_inventory', (0.5, 0.5), default_state=foundry.new_server_info['server_settings']['keep_inventory']))
            scroll_layout.add_widget(sub_layout)

        # Spawn protection switch button
        sub_layout = ScrollItem()
        sub_layout.add_widget(BlankInput(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="enable spawn protection"))
        sub_layout.add_widget(SwitchButton('spawn_protection', (0.5, 0.5), default_state=foundry.new_server_info['server_settings']['spawn_protection']))
        scroll_layout.add_widget(sub_layout)

        # Enable daylight cycle
        if constants.version_check(foundry.new_server_info['version'], ">=", "1.4.2"):
            label = "daylight & weather cycle" if constants.version_check(foundry.new_server_info['version'], ">=", "1.11") else "daylight cycle"
            sub_layout = ScrollItem()
            sub_layout.add_widget(BlankInput(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text=label))
            sub_layout.add_widget(SwitchButton('daylight_weather_cycle', (0.5, 0.5), default_state=foundry.new_server_info['server_settings']['daylight_weather_cycle']))
            scroll_layout.add_widget(sub_layout)

        # Spawn creatures switch button
        sub_layout = ScrollItem()
        sub_layout.add_widget(BlankInput(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="spawn creatures"))
        sub_layout.add_widget(SwitchButton('spawn_creatures', (0.5, 0.5), default_state=foundry.new_server_info['server_settings']['spawn_creatures']))
        scroll_layout.add_widget(sub_layout)

        # Enable command blocks switch button
        if constants.version_check(foundry.new_server_info['version'], ">=", "1.4.2"):
            sub_layout = ScrollItem()
            sub_layout.add_widget(BlankInput(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="enable command blocks"))
            sub_layout.add_widget(SwitchButton('command_blocks', (0.5, 0.5), default_state=foundry.new_server_info['server_settings']['command_blocks']))
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

        buttons.append(NextButton('Next', (0.5, 0.21), False, next_screen='CreateServerReviewScreen'))
        buttons.append(ExitButton('Back', (0.5, 0.12), cycle=True))

        for button in buttons: float_layout.add_widget(button)

        menu_name = f"Create '{foundry.new_server_info['name']}'"
        float_layout.add_widget(PageCounter(6, 7, (0, 0.868)))
        float_layout.add_widget(generate_title(menu_name))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)



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
                scroll_top.resize(); scroll_bottom.resize()

            Clock.schedule_once(update_grid, 0)


        self.resize_bind = lambda*_: Clock.schedule_once(functools.partial(resize_scroll, scroll_widget, scroll_layout, scroll_anchor), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        scroll_layout.bind(minimum_height=scroll_layout.setter('height'))
        scroll_layout.id = 'scroll_content'

        # Scroll gradient
        scroll_top = ScrollBackground(pos_hint={"center_x": 0.5, "center_y": 0.735}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, 60))
        scroll_bottom = ScrollBackground(pos_hint={"center_x": 0.5, "center_y": 0.272}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, -60))

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
                else: p.y = 0


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
            paragraph = ParagraphObject(size=(paragraph_width, content_height), name=name, content=text, font_size=content_size, font=pgh_font)
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
            if var: return '[/color]' + translate('Enabled')
            else:   return translate('Disabled') + '[/color]'
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
        float_layout.add_widget(ServerDemoInput(pos_hint={"center_x": 0.5, "center_y": 0.81}, properties=foundry.new_server_info))


        buttons.append(MainButton('Create Server', (0.5, 0.22), 'checkmark-circle-outline.png'))
        buttons.append(ExitButton('Back', (0.5, 0.12), cycle=True))

        for button in buttons: float_layout.add_widget(button)

        menu_name = f"Create '{foundry.new_server_info['name']}'"
        float_layout.add_widget(PageCounter(7, 7, (0, 0.815)))
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
            if final < 0: final = original
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
