from source.ui.desktop.views.templates import *
from source.ui.desktop.widgets.base import *
from source.ui.desktop.utility import *
from source.core import constants



# ============================================= Telepath Utilities =====================================================
# <editor-fold desc="Telepath Utilities">

# Telepath instance screen (for a client to view servers it's connected to)
class InstanceButton(HoverButton):
    class NameInput(TextInput):

        def update_config(self, *a):
            def write(*a): constants.server_manager.rename_telepath_server(self.properties, self.text)

            if self.change_timeout: self.change_timeout.cancel()
            self.change_timeout = Clock.schedule_once(write, 0.7)

        def _on_focus(self, instance, value, *largs):
            super()._on_focus(instance, value, *largs)

            if not value and not self.text:
                self.text = constants.format_nickname(self.original_text)

        # Ignore popup text
        def insert_text(self, substring, from_undo=False):
            if utility.screen_manager.current_screen.popup_widget:
                return None

            # Input validation & formatting
            if len(substring) > 1 or (substring in [' ', '-', '.'] and (not self.text or self.text[self.cursor_col - 1] in ['-', '.'])):
                return

            if len(self.text) >= 20:
                return

            substring = substring.lower().replace(' ', '-')
            substring = re.sub('[^a-zA-Z0-9.-]', '', substring)

            self.update_config()

            super().insert_text(substring, from_undo)

        # Special keypress behaviors
        def keyboard_on_key_down(self, window, keycode, text, modifiers):

            if keycode[1] == "backspace" and control in modifiers:
                original_index = self.cursor_col
                new_text, index = constants.control_backspace(self.text, original_index)
                self.select_text(original_index - index, original_index)
                self.delete_selection()
            else:
                super().keyboard_on_key_down(window, keycode, text, modifiers)

        def __init__(self, instance_data, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.properties = instance_data
            self.__translate__ = False
            self.id = "title"
            self.halign = "left"
            self.foreground_color = constants.brighten_color((0.65, 0.65, 1, 1), 0.07)
            self.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
            self.background_color = (0, 0, 0, 0)
            self.size = (400, 50)
            self.font_size = sp(25)
            self.max_lines = 1
            self.multiline = False
            self.hint_text_color = (0.6, 0.6, 1, 0.4)
            self.cursor_color = (0.55, 0.55, 1, 1)
            self.cursor_width = dp(3)
            self.selection_color = (0.5, 0.5, 1, 0.4)
            self.hint_text = 'enter a nickname...'
            self.original_text = ''
            self.change_timeout = None

    def animate_button(self, image, color, hover_action, **kwargs):
        image_animate = Animation(duration=0.05)

        Animation(color=color, duration=0.06).start(self.title)
        Animation(color=(color if ((self.subtitle.text == self.original_subtitle) or self.hovered) else self.connect_color), duration=0.06).start(self.subtitle)
        Animation(color=color, duration=0.06).start(self.type_image.image)

        if self.type_image.version_label.__class__.__name__ == "AlignLabel":
            Animation(color=color, duration=0.06).start(self.type_image.version_label)
        Animation(color=color, duration=0.06).start(self.type_image.type_label)

        animate_background(self, image, hover_action)

        image_animate.start(self)

    def resize_self(self, *args):

        # Title and description
        padding = 2.17
        self.title.pos = (self.x + 53, self.y + 26)
        self.subtitle.pos = (self.x + (self.subtitle.text_size[0] / padding) - 78, self.y + 8)
        offset = 9.55

        self.type_image.image.x = self.width + self.x - (self.type_image.image.width) - 13
        self.type_image.image.y = self.y + ((self.height / 2) - (self.type_image.image.height / 2))

        self.type_image.type_label.x = self.width + self.x - (self.padding_x * offset) - self.type_image.width - 83
        self.type_image.type_label.y = self.y + (self.height * 0.05)

        # Edit button
        self.edit_layout.size_hint_max = (self.size_hint_max[0], self.size_hint_max[1])
        self.edit_layout.pos = (self.pos[0] - 6, self.pos[1] + 13)

        # Update label
        if self.type_image.version_label.__class__.__name__ == "AlignLabel":
            self.type_image.version_label.x = self.width + self.x - (self.padding_x * offset) - self.type_image.width - 83
            self.type_image.version_label.y = self.y - (self.height / 3.2)

        # Banner version object
        else:
            self.type_image.version_label.x = self.width + self.x - (self.padding_x * offset) - self.type_image.width - 130
            self.type_image.version_label.y = self.y - (self.height / 3.2) - 2

    def highlight(self):
        def next_frame(*args):
            Animation.stop_all(self.highlight_border)
            self.highlight_border.opacity = 1
            Animation(opacity=0, duration=0.7).start(self.highlight_border)

        Clock.schedule_once(next_frame, 0)

    def update_subtitle(self):

        def reset(*a):
            self.subtitle.copyable = False
            self.subtitle.color = self.color_id[1]
            self.subtitle.default_opacity = 0.56
            self.subtitle.font_name = self.original_font
            self.subtitle.text = self.original_subtitle
            self.enabled = False
            self.background_normal = os.path.join(paths.ui_assets, 'addon_button_disabled.png')

        try:
            if self.properties['host'] in constants.server_manager.online_telepath_servers:
                self.connect_color = (0.529, 1, 0.729, 1)
                self.subtitle.color = self.connect_color
                self.subtitle.default_opacity = 0.8
                self.subtitle.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
                self.subtitle.text = 'Connected'
                self.enabled = True
                self.background_normal = os.path.join(paths.ui_assets, 'telepath_button_enabled.png')

            else:
                self.connect_color = (1, 0.65, 0.65, 1)
                self.subtitle.color = self.connect_color
                self.subtitle.default_opacity = 0.8
                self.subtitle.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')

                if self.properties['telepath-version'] != constants.api_manager.version:
                    self.subtitle.text = 'API version mismatch'
                else:
                    self.subtitle.text = 'Authentication failure'

                self.enabled = False
                self.background_normal = os.path.join(paths.ui_assets, 'addon_button_disabled.png')

        except KeyError:
            reset()

        self.background_down = self.background_normal
        self.subtitle.opacity = self.subtitle.default_opacity
        self.color_id = [(0.05, 0.05, 0.1, 1), (0.65, 0.65, 1, 1)] if self.enabled else [(0.05, 0.1, 0.1, 1), (1, 0.6, 0.7, 1)]
        self.title.color = self.color_id[1]

    def generate_name(self):
        tld = self.properties['host']
        if self.properties['nickname']: tld = self.properties['nickname']
        return tld

    def __init__(self, instance_data, click_function=None, fade_in=0.0, highlight=None, update_banner="", **kwargs):
        super().__init__(**kwargs)

        self.properties = instance_data
        self.border = (-5, -5, -5, -5)
        self.color_id = [(0.05, 0.05, 0.1, 1), constants.brighten_color((0.65, 0.65, 1, 1), 0.07)]
        self.connect_color = (0.529, 1, 0.729, 1)
        self.pos_hint = {"center_x": 0.5, "center_y": 0.6}
        self.size_hint_max = (580, 80)
        self.id = "server_button"
        self.enabled = False

        self.background_normal = os.path.join(paths.ui_assets, 'server_button.png' if self.enabled else 'addon_button_disabled.png')
        self.background_down = self.background_normal

        self.icons = os.path.join(paths.ui_assets, 'fonts', constants.fonts['icons'])

        # Loading stuffs
        self.original_subtitle = 'Offline'
        self.original_font = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["regular"]}.ttf')

        # Title of Instance
        self.title = self.NameInput(instance_data)
        self.title.text = self.title.original_text = self.generate_name()
        self.add_widget(self.title)

        # Authentication status formatted
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
        self.subtitle.copyable = False
        self.subtitle.color = self.color_id[1]
        self.subtitle.default_opacity = 0.56
        self.subtitle.font_name = self.original_font
        self.subtitle.text = self.original_subtitle

        self.subtitle.opacity = self.subtitle.default_opacity

        self.add_widget(self.subtitle)
        self.update_subtitle()

        # Edit button
        self.edit_layout = RelativeLayout()
        self.edit_button = IconButton('', {}, (0, 0), (None, None), 'unpair.png', anchor='right', click_func=functools.partial(click_function, instance_data))
        self.edit_layout.add_widget(self.edit_button)
        self.add_widget(self.edit_layout)

        # Type icon and info
        self.type_image = RelativeLayout()
        self.type_image.width = 400

        instance_icon = os.path.join(paths.ui_assets, 'icons', 'big', f'{self.properties["os"]}.png')
        self.type_image.image = Image(source=instance_icon)

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

        if update_banner:
            self.type_image.version_label = RelativeLayout()
            self.type_image.version_label.add_widget(
                BannerObject(
                    pos_hint = {"center_x": 1, "center_y": 0.5},
                    size = (100, 30),
                    color = (0.647, 0.839, 0.969, 1),
                    text = update_banner,
                    icon = "arrow-up-circle.png",
                    icon_side = "left"
                )
            )

        else:
            self.type_image.version_label = TemplateLabel()
            self.type_image.version_label.color = self.color_id[1]
            self.type_image.version_label.text = f"auto-mcs v{self.properties['app-version']}"
            self.type_image.version_label.opacity = 0.6

        self.type_image.type_label = TemplateLabel()
        self.type_image.type_label.text = self.properties["os"].replace('macos', 'macOS')
        self.type_image.type_label.font_size = sp(23)
        self.type_image.add_widget(self.type_image.version_label)
        self.type_image.add_widget(self.type_image.type_label)
        self.add_widget(self.type_image)

        # Animate opacity
        if fade_in > 0:
            self.opacity = 0
            self.title.opacity = 0

            Animation(opacity=1, duration=fade_in).start(self)
            Animation(opacity=1, duration=fade_in).start(self.title)
            Animation(opacity=self.subtitle.default_opacity, duration=fade_in).start(self.subtitle)

        self.bind(pos=self.resize_self)

    def on_enter(self, *args):
        return
        # if not self.ignore_hover:
        #     self.animate_button(image=os.path.join(paths.ui_assets, 'server_button_hover.png'), color=self.color_id[0], hover_action=True)

    def on_leave(self, *args):
        return
        # if not self.ignore_hover:
        #     self.animate_button(image=os.path.join(paths.ui_assets, 'server_button.png' if self.enabled else 'addon_button_disabled.png'), color=self.color_id[1], hover_action=False)


class TelepathInstanceScreen(MenuBackground):

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
        default_scroll = 1

        # Update page counter
        self.last_results = results
        self.max_pages = (len(results) / self.page_size).__ceil__()
        self.current_page = 1 if self.current_page == 0 or new_search else self.current_page

        self.page_switcher.update_index(self.current_page, self.max_pages)
        page_list = []
        for k, v in constants.deepcopy(results).items():
            v['host'] = k
            page_list.append(v)
        page_list = page_list[(self.page_size * self.current_page) - self.page_size:self.page_size * self.current_page]

        self.scroll_layout.clear_widgets()

        # Generate header
        server_count = len(constants.server_manager.telepath_servers)
        header_content = "Select an instance to manage"

        for child in self.header.children:
            if child.id == "text":
                child.text = header_content
                break

        # Show servers if they exist
        if server_count != 0:

            # Clear and add all ServerButtons
            for x, instance in enumerate(page_list, 1):

                # Activated when server is clicked
                def view_server(data, *a):
                    if data['nickname']: display_name = f"{data['host']} ({data['nickname']})"
                    else:                display_name = data['nickname']

                    desc = f"Un-pairing this instance will prevent you from accessing it via $Telepath$ until it's paired again.\n\nAre you sure you want to un-pair from '${display_name}$'?"

                    def unpair(*a):
                        # Log out if possible
                        if data['host'] in constants.api_manager.jwt_tokens:
                            constants.api_manager.logout(data['host'], data['port'])

                        constants.server_manager.remove_telepath_server(data)
                        self.gen_search_results(constants.server_manager.telepath_servers)

                        telepath_banner(f"Un-paired from '${data['host']}$'", False)

                    Clock.schedule_once(
                        functools.partial(
                            utility.screen_manager.current_screen.show_popup,
                            "warning_query",
                            f'Un-pair Instance',
                            desc,
                            (None, unpair)
                        ),
                        0
                    )

                # Add-on button click function
                self.scroll_layout.add_widget(
                    ScrollItem(
                        widget = InstanceButton(
                            instance_data = instance,
                            fade_in = ((x if x <= 8 else 8) / self.anim_speed) if fade_in else 0,
                            click_function = view_server
                        )
                    )
                )

            self.resize_bind()

        # Go back to main menu if they don't
        else:
            utility.screen_manager.current = 'TelepathManagerScreen'
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
        self.background_color = constants.brighten_color(constants.background_color, -0.09)
        self.menu = 'init'
        self.header = None
        self.scroll_layout = None
        self.blank_label = None
        self.page_switcher = None
        self.load_layout = None

        self.last_results = []
        self.page_size = 10
        self.current_page = 0
        self.max_pages = 0
        self.anim_speed = 10

        with self.canvas.before:
            self.color = Color(*self.background_color, mode='rgba')
            self.rect = Rectangle(pos=self.pos, size=self.size)

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        super()._on_keyboard_down(keyboard, keycode, text, modifiers)

        # Press arrow keys to switch pages
        if keycode[1] in ['right', 'left'] and self.name == utility.screen_manager.current_screen.name:
            self.switch_page(keycode[1])

    def show_loading(self, show=True, *a):
        self.load_layout.text.x = (Window.width / 2) - 100
        self.load_layout.icon.x = (Window.width / 2) - 140
        Animation.stop_all(self.load_layout)
        Animation(opacity=1 if show else 0, duration=0.2).start(self.load_layout)

    def generate_menu(self, **kwargs):

        # Scroll list
        scroll_widget = ScrollViewWidget(position=(0.5, 0.52))
        scroll_anchor = AnchorLayout()
        self.scroll_layout = GridLayout(cols=1, spacing=15, size_hint_max_x=1250, size_hint_y=None, padding=[0, 30, 0, 30])

        # Bind / cleanup height on resize
        def resize_scroll(call_widget, grid_layout, anchor_layout, *args):
            call_widget.height = Window.height // 1.82
            grid_layout.cols = 2 if Window.width > grid_layout.size_hint_max_x else 1
            self.anim_speed = 13 if Window.width > grid_layout.size_hint_max_x else 10

            def update_grid(*args): anchor_layout.size_hint_min_y = grid_layout.height

            Clock.schedule_once(update_grid, 0)

        self.resize_bind = lambda *_: Clock.schedule_once(functools.partial(resize_scroll, scroll_widget, self.scroll_layout, scroll_anchor), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        self.scroll_layout.bind(minimum_height=self.scroll_layout.setter('height'))
        self.scroll_layout.id = 'scroll_content'

        # Scroll gradient
        scroll_top = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.795}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, 60), color=self.background_color)
        scroll_bottom = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.26}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, -60), color=self.background_color)

        # Generate buttons on page load
        header_content = "Select an instance to manage"
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

        menu_name = "Instance Manager"
        float_layout.add_widget(generate_title(menu_name))
        float_layout.add_widget(generate_footer(f'Telepath, {menu_name}', no_background=True))

        # Load layout
        self.load_layout = FloatLayout(opacity=0)

        # Loading icon to swap button
        self.load_layout.icon = AsyncImage()
        self.load_layout.icon.id = "load_icon"
        self.load_layout.icon.source = os.path.join(paths.ui_assets, 'animations', 'loading_pickaxe.gif')
        self.load_layout.icon.size_hint_max = (50, 50)
        self.load_layout.icon.color = (0.6, 0.6, 1, 1)
        self.load_layout.icon.pos_hint = {"center_y": 0.5}
        self.load_layout.icon.allow_stretch = True
        self.load_layout.icon.anim_delay = utility.anim_speed * 0.02
        self.load_layout.add_widget(self.load_layout.icon)

        # Load label
        self.load_layout.text = AlignLabel()
        self.load_layout.text.text = "loading instances..."
        self.load_layout.text.halign = "center"
        self.load_layout.text.valign = "center"
        self.load_layout.text.size_hint_max = (300, 50)
        self.load_layout.text.font_name = os.path.join(paths.ui_assets, 'fonts', constants.fonts['italic'])
        self.load_layout.text.pos_hint = {"center_y": 0.5}
        self.load_layout.text.font_size = sp(25)
        self.load_layout.text.color = (0.6, 0.6, 1, 0.5)
        self.load_layout.add_widget(self.load_layout.text)

        self.add_widget(float_layout)
        self.add_widget(self.load_layout)

        # Async reload Telepath servers
        def refresh_telepath_instances(*a):
            Clock.schedule_once(lambda *_: self.show_loading(True), 0)
            constants.server_manager.check_telepath_servers()
            Clock.schedule_once(lambda *_: self.show_loading(False), 0)
            Clock.schedule_once(lambda *_: self.gen_search_results(constants.server_manager.telepath_servers), 0.15)

        dTimer(0, refresh_telepath_instances).start()


# Telepath user screen (for a server to view connected clients)
class UserButton(HoverButton):
    def animate_button(self, image, color, hover_action, **kwargs):
        image_animate = Animation(duration=0.05)

        Animation(color=color, duration=0.06).start(self.title)
        Animation(color=(color if ((self.subtitle.text == self.original_subtitle) or self.hovered) else self.connect_color), duration=0.06).start(self.subtitle)
        Animation(color=color, duration=0.06).start(self.type_image.image)

        if self.type_image.version_label.__class__.__name__ == "AlignLabel":
            Animation(color=color, duration=0.06).start(self.type_image.version_label)
        Animation(color=color, duration=0.06).start(self.type_image.type_label)

        animate_background(self, image, hover_action)

        image_animate.start(self)

    def resize_self(self, *args):

        # Title and description
        padding = 2.17
        self.title.pos = (self.x + (self.title.text_size[0] / padding) - 8.3 + 30, self.y + 31)
        self.subtitle.pos = (self.x + (self.subtitle.text_size[0] / padding) - 78, self.y + 8)
        offset = 9.55

        self.type_image.image.x = self.width + self.x - (self.type_image.image.width) - 8
        self.type_image.image.y = self.y + ((self.height / 2) - (self.type_image.image.height / 2))

        self.type_image.type_label.x = self.width + self.x - (self.padding_x * offset) - self.type_image.width - 75
        self.type_image.type_label.y = self.y + (self.height * 0.15)

        self.disable_layout.pos = (self.x + self.width + 57, self.y - 23)

        # Edit button
        self.edit_layout.size_hint_max = (self.size_hint_max[0], self.size_hint_max[1])
        self.edit_layout.pos = (self.pos[0] - 6, self.pos[1] + 13)

    def highlight(self):
        def next_frame(*args):
            Animation.stop_all(self.highlight_border)
            self.highlight_border.opacity = 1
            Animation(opacity=0, duration=0.7).start(self.highlight_border)

        Clock.schedule_once(next_frame, 0)

    def update_status(self):

        def reset(*a):
            self.subtitle.copyable = False
            self.subtitle.color = self.color_id[1]
            self.subtitle.default_opacity = 0.56
            self.subtitle.font_name = self.original_font
            self.subtitle.text = self.original_subtitle
            self.enabled = False
            self.background_normal = os.path.join(paths.ui_assets, 'addon_button_disabled.png')

        try:

            # User is connected
            if self.connected:
                self.connect_color = (0.529, 1, 0.729, 1)
                self.type_image.image.color = self.type_image.type_label.color = self.connect_color
                self.type_image.type_label.text = 'connected'
                self.background_normal = os.path.join(paths.ui_assets, 'telepath_button_enabled.png')

            # User is offline
            elif not self.access_disabled:
                self.connect_color = (0.65, 0.65, 1, 1)
                self.type_image.image.color = self.type_image.type_label.color = self.connect_color
                self.type_image.type_label.text = 'offline'
                self.background_normal = os.path.join(paths.ui_assets, 'addon_button.png')

            # User is restricted
            else:
                self.connect_color = (1, 0.65, 0.65, 1)
                self.type_image.image.color = self.type_image.type_label.color = self.connect_color
                self.type_image.type_label.text = 'restricted'
                self.background_normal = os.path.join(paths.ui_assets, 'addon_button_disabled.png')

        except KeyError:
            reset()

        self.background_down = self.background_normal
        self.subtitle.opacity = self.subtitle.default_opacity
        self.color_id = [(0.05, 0.05, 0.1, 1), (0.65, 0.65, 1, 1)] if self.connected else [(0.05, 0.1, 0.1, 1), (1, 0.6, 0.7, 1)]

    def generate_name(self):
        return self.properties['user']

    def __init__(self, user_data, click_function=None, fade_in=0.0, connected=False, highlight=None, **kwargs):
        super().__init__(**kwargs)

        self.properties = user_data
        self.border = (-5, -5, -5, -5)
        self.color_id = [(0.05, 0.05, 0.1, 1), constants.brighten_color((0.65, 0.65, 1, 1), 0.07)]
        self.connect_color = (0.529, 1, 0.729, 1)
        self.pos_hint = {"center_x": 0.5, "center_y": 0.6}
        self.size_hint_max = (580, 80)
        self.id = "server_button"
        self.access_disabled = 'disabled' in self.properties and self.properties['disabled']
        self.connected = connected

        self.background_normal = os.path.join(paths.ui_assets, 'server_button.png' if self.connected else 'addon_button_disabled.png')
        self.background_down = self.background_normal

        self.icons = os.path.join(paths.ui_assets, 'fonts', constants.fonts['icons'])

        # Loading stuffs
        self.original_subtitle = self.properties["host"] if self.properties["host"] else self.properties["ip"]
        self.original_font = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["regular"]}.ttf')

        # Title of user
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

        # Hostname
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
        self.subtitle.copyable = False
        self.subtitle.color = self.color_id[1]
        self.subtitle.default_opacity = 0.65
        self.subtitle.font_name = self.original_font
        self.subtitle.text = self.original_subtitle

        self.subtitle.opacity = self.subtitle.default_opacity

        self.add_widget(self.subtitle)

        # Edit button
        self.edit_layout = RelativeLayout()
        self.edit_button = IconButton('', {}, (0, 0), (None, None), 'unpair.png', anchor='right', click_func=functools.partial(click_function, user_data))
        self.edit_layout.add_widget(self.edit_button)
        self.add_widget(self.edit_layout)

        # Type icon and info
        self.type_image = RelativeLayout()
        self.type_image.width = 400

        user_icon = os.path.join(paths.ui_assets, 'icons', 'big', 'telepath-user.png')
        self.type_image.image = Image(source=user_icon)

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
            template_label.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
            template_label.opacity = 0.8
            template_label.width = 150
            return template_label

        self.type_image.type_label = TemplateLabel()
        self.type_image.type_label.font_size = sp(23)
        self.type_image.add_widget(self.type_image.type_label)
        self.add_widget(self.type_image)
        self.update_status()

        # Temporary disable switch
        def disable_user(disable=True):
            constants.api_manager._disable_user(self.properties['id'], not disable)
            self.access_disabled = not disable
            self.update_status()

        # Make this check eventual variable
        self.disable_layout = RelativeLayout(size_hint_max=(10, 10))
        self.disable_user = toggle_button('telepath-disable', (0.5, 0.5), default_state=not self.access_disabled, x_offset=-395, custom_func=disable_user)
        self.disable_layout.size_hint_max = (10, 10)
        self.disable_layout.add_widget(self.disable_user)
        self.add_widget(self.disable_layout)

        # Animate opacity
        if fade_in > 0:
            self.opacity = 0
            self.title.opacity = 0

            Animation(opacity=1, duration=fade_in).start(self)
            Animation(opacity=1, duration=fade_in).start(self.title)
            Animation(opacity=self.subtitle.default_opacity, duration=fade_in).start(self.subtitle)

        self.bind(pos=self.resize_self)

    def on_enter(self, *args):
        return
        # if not self.ignore_hover:
        #     self.animate_button(image=os.path.join(paths.ui_assets, 'server_button_hover.png'), color=self.color_id[0], hover_action=True)

    def on_leave(self, *args):
        return
        # if not self.ignore_hover:
        #     self.animate_button(image=os.path.join(paths.ui_assets, 'server_button.png' if self.enabled else 'addon_button_disabled.png'), color=self.color_id[1], hover_action=False)


class TelepathUserScreen(MenuBackground):

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

    def gen_search_results(self, new_search=False, fade_in=True, highlight=None, animate_scroll=True, *args):

        # Generate list of online users
        online_list = []
        for user in constants.api_manager.current_users.values():
            user_str = f'{user["host"]}/{user["user"]}'
            if user_str not in online_list:
                online_list.append(user_str)

        # Sort users based on if they are online
        results = sorted(
            constants.api_manager.authenticated_sessions,
            key = lambda u: f'{u["host"]}/{u["user"]}' in online_list,
            reverse = True
        )

        default_scroll = 1

        # Update page counter
        self.last_results = results
        self.max_pages = (len(results) / self.page_size).__ceil__()
        self.current_page = 1 if self.current_page == 0 or new_search else self.current_page

        self.page_switcher.update_index(self.current_page, self.max_pages)
        page_list = results[(self.page_size * self.current_page) - self.page_size:self.page_size * self.current_page]

        self.scroll_layout.clear_widgets()

        # Generate header
        user_count = len(constants.api_manager.authenticated_sessions)
        header_content = "Select a user to manage"

        for child in self.header.children:
            if child.id == "text":
                child.text = header_content
                break

        # Show users if they exist
        if user_count != 0:

            # Clear and add all ServerButtons
            for x, user in enumerate(page_list, 1):

                # Activated when server is clicked
                def view_user(data, *a):
                    if data['host']: display_name = f"{data['host']}/{data['user']}"
                    else:            display_name = f"{data['ip']}/{data['user']}"

                    desc = f"Un-pairing this user will prevent them from accessing this instance via $Telepath$ until paired again.\n\nAre you sure you want to un-pair '${display_name}$'?"

                    def unpair(*a):
                        # Log out if possible
                        if data['ip'] in constants.api_manager.current_users:
                            constants.api_manager._force_logout(constants.api_manager.current_users[data['ip']]['session_id'])

                        constants.api_manager._revoke_session(data['id'])
                        self.gen_search_results()
                        telepath_banner(f"Un-paired '${display_name}$'", False)

                    Clock.schedule_once(
                        functools.partial(
                            utility.screen_manager.current_screen.show_popup,
                            "warning_query",
                            f'Un-pair Instance',
                            desc,
                            (None, unpair)
                        ),
                        0
                    )

                # Add-on button click function
                self.scroll_layout.add_widget(
                    ScrollItem(
                        widget = UserButton(
                            user_data = user,
                            fade_in = ((x if x <= 8 else 8) / self.anim_speed) if fade_in else 0,
                            click_function = view_user,
                            connected = f'{user["host"]}/{user["user"]}' in online_list,
                        )
                    )
                )

            self.resize_bind()

        # Go back to main menu if they don't
        else:
            utility.screen_manager.current = 'TelepathManagerScreen'
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
        self.background_color = constants.brighten_color(constants.background_color, -0.09)
        self.menu = 'init'
        self.header = None
        self.scroll_layout = None
        self.blank_label = None
        self.page_switcher = None
        self.load_layout = None

        self.last_results = []
        self.page_size = 10
        self.current_page = 0
        self.max_pages = 0
        self.anim_speed = 10

        with self.canvas.before:
            self.color = Color(*self.background_color, mode='rgba')
            self.rect = Rectangle(pos=self.pos, size=self.size)

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        super()._on_keyboard_down(keyboard, keycode, text, modifiers)

        # Press arrow keys to switch pages
        if keycode[1] in ['right', 'left'] and self.name == utility.screen_manager.current_screen.name:
            self.switch_page(keycode[1])

    def show_loading(self, show=True, *a):
        Animation.stop_all(self.load_layout)
        Animation(opacity=1 if show else 0, duration=0.2).start(self.load_layout)

    def generate_menu(self, **kwargs):

        # Scroll list
        scroll_widget = ScrollViewWidget(position=(0.5, 0.52))
        scroll_anchor = AnchorLayout()
        self.scroll_layout = GridLayout(cols=1, spacing=15, size_hint_max_x=1250, size_hint_y=None, padding=[0, 30, 0, 30])

        # Bind / cleanup height on resize
        def resize_scroll(call_widget, grid_layout, anchor_layout, *args):
            call_widget.height = Window.height // 1.82
            grid_layout.cols = 2 if Window.width > grid_layout.size_hint_max_x else 1
            self.anim_speed = 13 if Window.width > grid_layout.size_hint_max_x else 10

            def update_grid(*args): anchor_layout.size_hint_min_y = grid_layout.height

            Clock.schedule_once(update_grid, 0)

        self.resize_bind = lambda *_: Clock.schedule_once(functools.partial(resize_scroll, scroll_widget, self.scroll_layout, scroll_anchor), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        self.scroll_layout.bind(minimum_height=self.scroll_layout.setter('height'))
        self.scroll_layout.id = 'scroll_content'

        # Scroll gradient
        scroll_top = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.795}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, 60), color=self.background_color)
        scroll_bottom = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.26}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, -60), color=self.background_color)

        # Generate buttons on page load
        header_content = "Select a user to manage"
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

        for button in buttons: float_layout.add_widget(button)

        menu_name = "User Manager"
        float_layout.add_widget(generate_title(menu_name))
        float_layout.add_widget(generate_footer(f'Telepath, {menu_name}', no_background=True))

        self.add_widget(float_layout)

        self.gen_search_results()


class TelepathHostInput(CreateServerPortInput):
    def __init__(self, **kwargs):
        self.ip = ''
        self.port = ''
        super().__init__(**kwargs)
        self.checking = False
        self.hint_text = f"enter IPv4  (default port :{constants.api_manager.default_port})"
        self.bind(on_text_validate=self.check_connection)

    def check_connection(self, *a):

        def change_icon(show=True, *a):
            try:
                load_icon = utility.screen_manager.current_screen.load_icon
                Animation.stop_all(load_icon)
                Animation(opacity=1 if show else 0, duration=0.15).start(load_icon)
            except AttributeError:
                pass

        def background(*a):
            self.checking = True
            try:
                data = {'detail': 'Failed to connect'}
                Clock.schedule_once(functools.partial(change_icon, True), 0)
                if constants.check_port(self.ip, int(self.port), timeout=5):
                    data = constants.api_manager.request_pair(self.ip, self.port)
            except: pass

            Clock.schedule_once(functools.partial(change_icon, False), 0)
            self.checking = False

            try:
                if 'detail' in data:
                    self.stinky_text = ' Unable to connect'
                    self.valid(False)
                    return
            except: pass

            if data and utility.screen_manager.current_screen.name == 'TelepathManagerScreen':
                Clock.schedule_once(functools.partial(utility.screen_manager.current_screen.confirm_pair_input, self.ip, self.port), 0)

        if not self.checking: dTimer(0, background).start()
        change_timeout = None

    def update_config(self, *a):
        if self.change_timeout:  self.change_timeout.cancel()
        self.change_timeout = Clock.schedule_once(self.check_connection, 2)

    # Input validation
    def insert_text(self, substring, from_undo=False):

        if not self.text and substring == " ":
            substring = ""

        elif len(self.text) < 30:
            if '\n' in substring: substring = substring.splitlines()[0]
            s = re.sub('[^a-z0-9-:.]', '', substring)

            if ":" in self.text and ":" in s:
                s = ''

            if ("." in s and ((self.cursor_col > self.text.find(":")) and (self.text.find(":") > -1))) or ("." in s and self.text.count(".") >= 3):
                s = ''

            # Add name to current config
            def process(*a): self.process_text(text=(self.text))
            Clock.schedule_once(process, 0)

            return BaseInput.insert_text(self, s, from_undo=from_undo)

    def process_text(self, text=''):
        new_ip = ''
        default_port = constants.api_manager.default_port
        new_port = default_port

        typed_info = text if text else self.text

        # interpret typed information
        if ":" in typed_info: new_ip, new_port = typed_info.split(":")[-2:]
        else:
            if "." in typed_info or not new_port:
                new_ip = typed_info.replace(":", "")
                new_port = default_port
            else:
                new_port = typed_info.replace(":", "")

        if not str(self.port) or not new_port:
            new_port = default_port

        if not str(new_port).isnumeric():
            new_port = default_port

        # Input validation
        try: port_check = ((int(new_port) < 1024) or (int(new_port) > 65535))
        except: port_check = True
        ip_check = (constants.check_ip(new_ip) and '.' in typed_info) or new_ip.replace('-', '').replace('.',
                                                                                                         '').isalpha()
        self.stinky_text = ''
        fail = False

        if typed_info:

            if new_ip in constants.server_manager.telepath_servers:
                self.stinky_text = ' Host is already added'
                fail = True

            elif '.' not in typed_info and typed_info.isnumeric():
                self.stinky_text = ' Enter an IPv4 address'
                fail = True

            elif not ip_check and ("." in typed_info or ":" in typed_info):
                self.stinky_text = 'Invalid IPv4 address' if not port_check else 'Invalid IPv4 and port'
                fail = True

            elif port_check:
                self.stinky_text = ' Invalid port  (use 1024-65535)'
                fail = True

        else:
            new_ip = ''
            new_port = constants.api_manager.default_port

        if not fail:
            self.ip = new_ip

        if new_port and not fail:
            self.port = int(new_port)

        if fail:
            self.ip = ''
            self.port = default_port

        self.valid(not self.stinky_text)


class TelepathCodeInput(BigBaseInput):
    def __init__(self, ip: str, port: int, **kwargs):
        super().__init__(**kwargs)
        self.ip = ip
        self.port = port

        self.title_text = "pair code"
        self.hint_text = '000-000'
        self.is_valid = True
        self.stinky_text = ''

        self.valign = "center"
        self.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["mono-bold"]}.otf')
        self.font_size = sp(69)
        self.padding_y = (12, 9)
        self.cursor_width = dp(5)
        self.checking = False
        self.bind(on_text_validate=self.check_connection)
        self.fail_count = 0

    def check_connection(self, *a):
        code = self.text.replace('-', '').upper().strip()
        if len(code) != 6:
            self.stinky_text = 'Invalid code length'
            self.valid_text(False, True)
            self.valid(False)
            return
        else:
            self.valid(True)

        def change_icon(show=True, *a):
            try:
                load_icon = utility.screen_manager.current_screen.load_icon
                Animation.stop_all(load_icon)
                Animation(opacity=1 if show else 0, duration=0.15).start(load_icon)
            except AttributeError:
                pass

        def background(*a):
            self.checking = True
            data = None

            Clock.schedule_once(functools.partial(change_icon, True), 0)
            if constants.check_port(self.ip, int(self.port), timeout=5):
                data = constants.api_manager.submit_pair(self.ip, self.port, code)

            Clock.schedule_once(functools.partial(change_icon, False), 0)
            self.checking = False

            try:
                if not data or 'detail' in data:
                    self.stinky_text = '  Unable to connect or invalid code'
                    self.fail_count += 1
                    self.valid_text(False, True)
                    self.valid(False)
            except:
                pass

            if self.fail_count >= 3 and utility.screen_manager.current_screen.name == 'TelepathManagerScreen':
                Clock.schedule_once(functools.partial(utility.screen_manager.current_screen.show_pair_input, True), 0)
                return

            if data and utility.screen_manager.current_screen.name == 'TelepathManagerScreen':
                def back_to_menu(*a):
                    constants.server_manager.refresh_list()
                    utility.screen_manager.current = 'ServerManagerScreen'
                    utility.screen_manager.screen_tree = ['MainMenuScreen']
                    server_name = data['nickname'] if data['nickname'] else data['host']
                    telepath_banner(f"Successfully paired '${server_name}$'", True, play_sound='telepath/success')

                Clock.schedule_once(back_to_menu, 0)
                return

        if not self.checking: dTimer(0, background).start()

    # Ignore popup text
    def insert_text(self, substring, from_undo=False):
        substring = substring.upper()
        if len(substring) > 1:
            substring = ''

        if not self.text and substring == " ":
            substring = ""

        elif len(self.text) < 7:
            if '\n' in substring: substring = substring.splitlines()[0]
            s = re.sub('[^a-zA-Z0-9]', '', substring).upper().replace('O', '0')

            super().insert_text(s, from_undo)
            if len(self.text) == 3: super().insert_text('-')

    def valid_text(self, boolean_value, text):
        for child in self.parent.children:
            try:
                if child.id == "InputLabel":

                    # Valid input
                    if boolean_value:
                        child.clear_text()
                        child.disable_text(False)

                    # Invalid input
                    else:
                        child.update_text(self.stinky_text)
                        child.disable_text(True)
                    break

            except AttributeError:
                pass

    # Special keypress behaviors
    def keyboard_on_key_down(self, window, keycode, text, modifiers):

        def update_bar(*a):
            if (not self.text.endswith('-')) or keycode[1] == "backspace":
                self.text = self.text.replace('-', '')
            if len(self.text.replace('-', '')) > 3:
                self.text = self.text[:3] + '-' + self.text[3:]

        Clock.schedule_once(update_bar, 0)

        if keycode[1] == "backspace" and control in modifiers:
            original_index = self.cursor_col
            new_text, index = constants.control_backspace(self.text, original_index)
            self.select_text(original_index - index, original_index)
            self.delete_selection()

        else:
            super().keyboard_on_key_down(window, keycode, text, modifiers)


class ParticleMesh(Widget):
    points = ListProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.direction = []
        self._generated = False

        self.point_number = 50
        self.point_radius = 3
        self.line_width = 1
        self.speed = 0.05
        self.max_line_length = 200

        self.line_color = (0.55, 0.55, 0.8)
        self.point_color = (0.8, 0.8, 1)

        # Generate points and fade in
        self.opacity = 0
        self.bind(size=self.plot_points)

    def show(self, *a):
        Animation(opacity=1, duration=3, transition='out_sine').start(self)

    def plot_points(self, *a):
        if self.height > 200 and not self._generated:
            Clock.schedule_once(self.show, 0)
            self._generated = True
            for _ in range(self.point_number):
                x = random.randint(0, self.width)
                y = random.randint(0, self.height)
                self.points.extend([x, y])
                self.direction.append(random.randint(0, 300))
            Clock.schedule_interval(self.update_positions, self.speed)

    def draw_lines(self):
        self.canvas.after.clear()
        with self.canvas.after:
            for i in range(0, len(self.points), 2):
                for j in range(i + 2, len(self.points), 2):
                    d = self.distance_between_points(self.points[i], self.points[i + 1], self.points[j], self.points[j + 1])
                    if d > self.max_line_length: continue
                    opacity = 1 - (d / self.max_line_length)
                    Color(rgba=[*self.line_color, opacity])
                    Line(points=[self.points[i], self.points[i + 1], self.points[j], self.points[j + 1]], width=self.line_width)
                    Color(rgba=[*self.point_color, opacity])
                Ellipse(pos=(self.points[i] - self.point_radius, self.points[i + 1] - self.point_radius), size=(self.point_radius * 2, self.point_radius * 2))

    def update_positions(self, *args):
        step = 1
        for i, j in zip(range(0, len(self.points), 2), range(len(self.direction))):
            theta = self.direction[j]
            self.points[i] += step * math.cos(theta)
            self.points[i + 1] += step * math.sin(theta)

            if self.off_screen(self.points[i], self.points[i + 1]):
                self.direction[j] = 90 + self.direction[j]

        self.draw_lines()

    @staticmethod
    def distance_between_points(x1, y1, x2, y2):
        return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5

    def off_screen(self, x, y):
        return x < -5 or x > self.width + 5 or y < -5 or y > self.height + 5


class TelepathManagerScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'
        self.background_color = constants.brighten_color(constants.background_color, -0.09)
        self.back_button = None
        self.help_button = None
        self.instances_button = None
        self.users_button = None
        self.pair_button = None
        self.api_input = None
        self.api_toggle = None
        self.host_input = None
        self.confirm_input = None
        self.load_icon = None
        self.page_speed = 0.15

        with self.canvas.before:
            self.canvas.clear()

        with self.canvas.before:
            self.color = Color(*self.background_color, mode='rgba')
            self.rect = Rectangle(pos=self.pos, size=self.size)

        # Layouts
        self.main_layout = None
        self.pair_layout = None
        self.confirm_layout = None

    def on_pre_enter(self, *args):
        constants.api_manager.pair_listen = True
        return super().on_pre_enter(*args)

    def on_pre_leave(self, *args):
        constants.api_manager.pair_listen = False
        return super().on_pre_leave(*args)

    def show_pair_input(self, back=False, show=True):
        self.pair_button.disabled = True
        if show:
            self.back_button.custom_func = self.main_menu
            if self.pair_layout:
                self.pair_layout.clear_widgets()

            self.pair_layout = FloatLayout()
            self.pair_layout.opacity = 0
            self.pair_layout.add_widget(InputLabel(pos_hint={"center_x": 0.5, "center_y": 0.55}))
            self.pair_layout.add_widget(HeaderText("Enter the IPv4/port you wish to connect", 'make sure "share this instance" is enabled on the server', (0, 0.75)))
            self.host_input = TelepathHostInput(pos_hint={"center_x": 0.5, "center_y": 0.45}, text='')
            self.pair_layout.add_widget(self.host_input)

            # Spinning pickaxe
            load_icon = AsyncImage()
            load_icon.id = "load_icon"
            load_icon.source = os.path.join(paths.ui_assets, 'animations', 'loading_pickaxe.gif')
            load_icon.size_hint_max = (self.host_input.height / 2.5, self.host_input.height / 2.5)
            load_icon.color = (0.6, 0.6, 1, 1)
            load_icon.pos_hint = {"center_y": 0.45}
            load_icon.allow_stretch = True
            load_icon.anim_delay = utility.anim_speed * 0.02
            load_icon.opacity = 0
            if self.load_icon and self.confirm_layout:
                self.confirm_layout.remove_widget(self.load_icon)
            self.load_icon = load_icon
            self.pair_layout.add_widget(load_icon)

            def recenter(*a):
                def r(*a): load_icon.x = Window.center[0] - (self.host_input.width / 2) + 13
                Clock.schedule_once(r, 0)

            self.pair_layout.bind(pos=recenter, size=recenter)

            # Switch "screens"
            if back:
                def after(*a):
                    self.confirm_layout.opacity = 0
                    self.remove_widget(self.confirm_layout)
                    self.add_widget(self.pair_layout)
                    Animation(opacity=1, duration=self.page_speed).start(self.pair_layout)

                Animation.stop_all(self.confirm_layout)
                Animation(opacity=0, duration=self.page_speed).start(self.confirm_layout)
                Clock.schedule_once(after, self.page_speed + 0.05)

            else:
                def after(*a):
                    self.main_layout.opacity = 0
                    self.remove_widget(self.main_layout)
                    self.add_widget(self.pair_layout)
                    Animation(opacity=1, duration=self.page_speed).start(self.pair_layout)

                Animation.stop_all(self.main_layout)
                Animation(opacity=0, duration=self.page_speed).start(self.main_layout)
                Clock.schedule_once(after, self.page_speed + 0.05)

    def confirm_pair_input(self, ip: str, port: int, show=True):
        self.pair_button.disabled = True
        self.back_button.custom_func = functools.partial(self.show_pair_input, True)
        if show:
            if self.confirm_layout:
                self.confirm_layout.clear_widgets()

            self.confirm_layout = FloatLayout()
            self.confirm_layout.opacity = 0
            self.confirm_layout.add_widget(InputLabel(pos_hint={"center_x": 0.5, "center_y": 0.58}))
            self.confirm_layout.add_widget(HeaderText(f"Enter the pair code from:   $[color=#AAAAEE]{ip}[/color]$", 'if headless, use the "$telepath pair$" command', (0, 0.75)))
            self.confirm_input = TelepathCodeInput(ip, port, pos_hint={"center_x": 0.5, "center_y": 0.45}, text='')
            self.confirm_layout.add_widget(self.confirm_input)

            # Spinning pickaxe
            load_icon = AsyncImage()
            load_icon.id = "load_icon"
            load_icon.source = os.path.join(paths.ui_assets, 'animations', 'loading_pickaxe.gif')
            load_icon.size_hint_max = (self.host_input.height, self.host_input.height)
            load_icon.color = (0.6, 0.6, 1, 1)
            load_icon.pos_hint = {"center_y": 0.45}
            load_icon.allow_stretch = True
            load_icon.anim_delay = utility.anim_speed * 0.02
            load_icon.opacity = 0
            if self.load_icon and self.pair_layout: self.pair_layout.remove_widget(self.load_icon)
            self.load_icon = load_icon
            self.confirm_layout.add_widget(load_icon)

            def recenter(*a):
                def r(*a): load_icon.x = Window.center[0] - (self.host_input.width / 2) + 30
                Clock.schedule_once(r, 0)

            self.confirm_layout.bind(pos=recenter, size=recenter)

            # Switch "screens"
            def after(*a):
                self.pair_layout.opacity = 0
                self.remove_widget(self.pair_layout)
                self.add_widget(self.confirm_layout)
                Animation(opacity=1, duration=self.page_speed).start(self.confirm_layout)

            Animation.stop_all(self.pair_layout)
            Animation(opacity=0, duration=self.page_speed).start(self.pair_layout)
            self.confirm_input.grab_focus()
            Clock.schedule_once(after, self.page_speed + 0.05)

    def main_menu(self):
        # Switch "screens"
        def after(*a):
            self.back_button.custom_func = None
            self.pair_button.disabled = False
            self.pair_layout.opacity = 0
            self.remove_widget(self.pair_layout)
            self.add_widget(self.main_layout)
            Animation(opacity=1, duration=self.page_speed).start(self.main_layout)

        Animation.stop_all(self.pair_layout)
        Animation(opacity=0, duration=self.page_speed).start(self.pair_layout)
        Clock.schedule_once(after, self.page_speed + 0.05)

    def recalculate_buttons(self, *a):
        try: self.main_layout.remove_widget(self.users_button)
        except: pass

        try: self.main_layout.remove_widget(self.instances_button)
        except: pass

        if constants.api_manager.authenticated_sessions and constants.app_config.telepath_settings['enable-api']:
            self.main_layout.add_widget(self.users_button)

            pair_pos = (0.5, 0.42)
            enable_pos = (0.5, 0.29)
            back_pos = (0.5, 0.12)

        elif constants.server_manager.telepath_servers:
            self.main_layout.add_widget(self.instances_button)

            pair_pos = (0.5, 0.42)
            enable_pos = (0.5, 0.29)
            back_pos = (0.5, 0.12)

        else:
            pair_pos = (0.5, 0.5)
            enable_pos = (0.5, 0.35)
            back_pos = (0.5, 0.12)

        self.pair_button.pos_hint = {'center_x': pair_pos[0], 'center_y': pair_pos[1]}
        self.api_input.pos_hint = {'center_x': enable_pos[0], 'center_y': enable_pos[1]}
        self.api_toggle.button.pos_hint = {'center_x': enable_pos[0], 'center_y': enable_pos[1]}
        self.api_toggle.knob.pos_hint = {"center_y": enable_pos[1]}
        self.back_button.text.pos_hint = self.back_button.button.pos_hint = {'center_x': back_pos[0], 'center_y': back_pos[1]}
        self.back_button.icon.pos_hint = {'center_y': back_pos[1]}

    def generate_menu(self, **kwargs):
        self.main_layout = FloatLayout()
        self.main_layout.opacity = 0

        # Add particle background and gradient on top
        particles = ParticleMesh()
        self.add_widget(particles)

        # Menu shadow
        shadow = Image(source=os.path.join(paths.ui_assets, 'menu_shadow.png'))
        shadow.color = self.background_color
        shadow.opacity = 0.8
        shadow.size_hint_max = (600, 600)
        shadow.allow_stretch = True
        shadow.keep_ratio = False
        shadow.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        self.add_widget(shadow)

        gradient = Image(source=os.path.join(paths.ui_assets, 'telepath_gradient.png'))
        gradient.size_hint_max = (None, None)
        gradient.allow_stretch = True
        gradient.keep_ratio = False
        gradient.opacity = 0.6
        gradient.color = constants.brighten_color(self.background_color, 0.03)
        self.add_widget(gradient)

        # Help button
        def show_help():
            help_text = """$Telepath$ is an $auto-mcs$ protocol to control remote sessions seamlessly. For example, $Telepath$ can connect a local computer to an instance of $auto-mcs$ running on a different computer, or a VPS in the cloud.

To connect via $Telepath$, enable “share this instance” on the server you intend to connect. Then click “Pair a Server” on the client and follow the prompts.

Once paired, remote servers will appear in the Server Manager and can be interacted with like normal. You can also import or create a server on a $Telepath$ instance."""

            Clock.schedule_once(
                functools.partial(
                    self.show_popup,
                    "controls",
                    "About $Telepath$",
                    help_text,
                    (None)
                ),
                0
            )

        self.help_button = IconButton('help', {}, (70, 60), (None, None), 'question.png', clickable=True, anchor='right', click_func=show_help)
        self.add_widget(self.help_button)

        # Add telepath logo
        logo = Image(source=os.path.join(paths.ui_assets, 'telepath_logo.png'), allow_stretch=True, size_hint=(None, None), width=dp(400), pos_hint={"center_x": 0.5, "center_y": 0.77})
        logo.color = (0.8, 0.8, 1, 0.9)
        self.main_layout.add_widget(logo)

        session_splash = Label(pos_hint={"center_y": 0.7}, color=(0.7, 0.7, 1, 0.4), font_name=os.path.join(paths.ui_assets, 'fonts', constants.fonts['medium']), font_size=sp(25))
        session_splash.text = 'simplified remote access'
        self.main_layout.add_widget(session_splash)

        # Logic-driven button visibility
        def user_manager(*a): utility.screen_manager.current = "TelepathUserScreen"
        def instance_manager(*a): utility.screen_manager.current = "TelepathInstanceScreen"
        self.users_button = ColorButton("MANAGE USERS", position=(0.5, 0.55), icon_name='person-sharp.png', click_func=user_manager, color=(0.8, 0.8, 1, 1))
        self.instances_button = ColorButton("MANAGE INSTANCES", position=(0.5, 0.55), icon_name='settings-sharp.png', click_func=instance_manager, color=(0.8, 0.8, 1, 1))
        self.pair_button = ColorButton("PAIR A SERVER", position=(0.5, 0.5), icon_name='telepath.png', click_func=functools.partial(self.show_pair_input, False), color=(0.8, 0.8, 1, 1))
        self.main_layout.add_widget(self.pair_button)

        # Enable API toggle button
        def toggle_api(state, only_input=False, *a):
            if not only_input:
                constants.app_config.telepath_settings['enable-api'] = state
                constants.app_config.save_config()
                text = 'enabled' if state else 'disabled'
                constants.telepath_banner(f'$Telepath$ API is now {text}', state)

            # Update hint text
            if state:
                port = constants.api_manager.port
                ip = constants.api_manager.host

                if ip == '0.0.0.0':
                    ip = constants.get_private_ip()

                if constants.public_ip:
                    if constants.check_port(constants.public_ip, port, 0.05):
                        ip = constants.public_ip

                new_text = f">   {ip}:{port}"
                self.api_input.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
                self.api_input.hint_text_color = (0.6, 0.9, 1, 1)
                constants.api_manager.start()

            else:
                new_text = 'share this instance'
                self.api_input.hint_text_color = (0.6, 0.6, 1, 0.8)
                self.api_input.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
                constants.api_manager.stop()

            self.api_input.hint_text = new_text

        sub_layout = RelativeLayout()
        self.api_input = BlankInput(pos_hint={"center_x": 0.5, "center_y": 0.35}, hint_text="share this instance")
        self.api_toggle = toggle_button('api', (0.5, 0.35), default_state=constants.app_config.telepath_settings['enable-api'], custom_func=toggle_api)
        sub_layout.add_widget(self.api_input)
        sub_layout.add_widget(self.api_toggle)
        self.main_layout.add_widget(sub_layout)
        if constants.app_config.telepath_settings['enable-api']:
            toggle_api(True, True)

        Clock.schedule_once(self.recalculate_buttons, 0)

        # Static content on each page
        self.add_widget(generate_footer('$Telepath$', no_background=True))
        self.add_widget(self.main_layout)
        Animation(opacity=1, duration=1).start(self.main_layout)
        self.back_button = ExitButton('Back', (0.5, 0.12), cycle=True)
        self.add_widget(self.back_button)


# Telepath notifications and pairing
class TelepathPair():
    def __init__(self):
        self.is_open = False
        self.pair_data = {}

    def close(self):
        if not self.is_open:
            return

        # Normal operation
        try:
            current_user = constants.api_manager.current_users[self.pair_data['host']['ip']]
            if current_user and current_user['host'] == self.pair_data['host']['host'] and current_user['user'] == self.pair_data['host']['user']:
                message = f"Successfully paired with '${current_user['host']}/{current_user['user']}$'"
                color = (0.553, 0.902, 0.675, 1)
                sound = 'telepath/success'
            else:
                message = f'$Telepath$ pair request expired'
                color = (0.937, 0.831, 0.62, 1)
                sound = 'popup/warning'

        # Failed to pair
        except Exception as e:
            message = f'$Telepath$ pairing failed'
            color = (0.937, 0.831, 0.62, 1)
            sound = 'popup/warning'
            send_log(self.__class__.__name__, f'failed to pair: {constants.format_traceback(e)}', 'error')

        # Reset token if cancelled
        if constants.api_manager.pair_data:
            constants.api_manager.pair_data = {}

        Clock.schedule_once(
            functools.partial(
                utility.screen_manager.current_screen.show_banner,
                color,
                message,
                "telepath.png",
                2.5,
                {"center_x": 0.5, "center_y": 0.965},
                sound
            ), 0.1
        )

        self.is_open = False
        self.pair_data = {}

    def open(self, data: dict):
        if self.is_open:
            return

        self.pair_data = data

        # If the application is blocked, wait until it's not to show the pop-up
        def wait_thread(*a):
            self.is_open = True
            while constants.ignore_close or utility.screen_manager.current_screen.popup_widget:
                time.sleep(1)

            Clock.schedule_once(
                functools.partial(
                    utility.screen_manager.current_screen.show_popup,
                    "pair_request",
                    " ",
                    self.pair_data,
                    self.close
                ), 0
            )

        dTimer(0, wait_thread).start()


constants.telepath_pair = TelepathPair()

# </editor-fold> ///////////////////////////////////////////////////////////////////////////////////////////////////////
