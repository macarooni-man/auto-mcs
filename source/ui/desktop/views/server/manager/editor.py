from source.ui.desktop.views.server.manager.components import *



# Config Folder Screens ------------------------------------------------------------------------------------------------

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

        if ext in ['properties', 'ini']:  editor_screen = 'ServerPropertiesEditScreen'
        elif ext in ['tml', 'toml']:      editor_screen = 'ServerTomlEditScreen'
        elif ext in ['yml', 'yaml']:      editor_screen = 'ServerYamlEditScreen'
        elif ext == 'json':               editor_screen = 'ServerJsonEditScreen'
        elif ext == 'json5':              editor_screen = 'ServerJson5EditScreen'
        else:                             editor_screen = 'ServerTextEditScreen'

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
            endpoint = '/main/update_config_file',
            host = telepath_data['host'],
            port = telepath_data['port'],
            args = {
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
            else: screen.scroll_widget.scroll_y = 1

        Clock.schedule_once(after_layout, -1)

    def on_click(self, *a):

        # Open folder on right-click
        if not constants.server_manager.current_server._telepath_data:
            try:
                if self.button.last_touch.button == 'right':
                    return open_folder(self.path)
            except: pass

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
        self.folder.parent.background.size_hint_min_x = utility.screen_manager.current_screen.max_width + (10 if Window.width < 900 else 60)

        for file in self.children: file.resize(folder=self.folder)

        Animation.stop_all(self.folder.parent.background)
        Animation(opacity=(0 if self.folder.folded else 1), duration=0.15).start(self.folder.parent.background)

    # Pretty animation :)
    def hide(self, hide: bool = True):
        utility.hide_widget(self, hide)
        if not hide:
            def animate(c, *a):
                Animation.stop_all(c)
                Animation(opacity=1, duration=0.15).start(c)

            for child in self.children: child.opacity = 0
            for x, child in enumerate(reversed(self.children), 1):
                if x > 10: x = 10
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
        for file in self.file_list: self.add_widget(self.ConfigFile(file))

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

        if not query: return self.server_obj.config_paths

        # Filter by file name matches
        else:
            filtered = {}
            for folder, files in self.server_obj.config_paths.items():
                for file in files:
                    if query.lower() in constants.cross_platform_path(file).lower():
                        if folder not in filtered: filtered[folder] = []
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
        if (
            self._cached and
            self._cached['server_obj'] == self.server_obj and
            self._cached['file_count'] == file_count and
            self._cached['locale'] == constants.app_config.locale
        ):
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
            cols = 2,
            spacing = 10,
            size_hint_max_x = self.max_width,
            size_hint_y = None,
            padding = [0, 80, 0, 60]
        )

        # Bind / cleanup height on resize
        def resize_scroll(call_widget, grid_layout, anchor_layout, *args):
            call_widget.height = Window.height // 1.5
            grid_layout.cols = 2

            def update_grid(*args):
                anchor_layout.size_hint_min_y = grid_layout.height
                scroll_top.resize(); scroll_bottom.resize()

            Clock.schedule_once(update_grid, 0)

        self.resize_bind = lambda *_: Clock.schedule_once(functools.partial(resize_scroll, self.scroll_widget, self.scroll_layout, self.scroll_anchor), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        self.scroll_layout.bind(minimum_height=self.scroll_layout.setter('height'))
        self.scroll_layout.id = 'scroll_content'

        # Scroll gradient
        scroll_top = ScrollBackground(pos_hint={"center_x": 0.5, "center_y": 0.79}, pos=self.scroll_widget.pos, size=(self.scroll_widget.width // 1.5, 60))
        scroll_bottom = ScrollBackground(pos_hint={"center_x": 0.5, "center_y": 0.18}, pos=self.scroll_widget.pos, size=(self.scroll_widget.width // 1.5, -60))

        # Generate buttons on page load
        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'

        # Create header/search bar
        self.header = HeaderText("Select a configuration file to edit", '', (0, 0.9), no_line=True)
        self.search_bar = SearchBar(return_function=self.filter_files, server_info=None, pos_hint={"center_x": 0.5, "center_y": 0.84}, allow_empty=True)

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

        for button in buttons: float_layout.add_widget(button)

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




# Edit Config Screens ------------------------------------------------------------------------------------------------

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

                except AttributeError: pass

                self.scrollable = False
                self.ovf_left.show(False)
                self.ovf_right.show(False)

            def grab_focus(self, *a):
                def focus_later(*args):
                    try: self.focus = True
                    except: return

                Clock.schedule_once(focus_later, 0)

            def on_focus(self, *args):
                try:
                    if self._line.inactive:
                        self.focused = False
                        return
                except: return

                Animation.stop_all(self._line.eq_label)
                Animation(opacity=(1 if self.focused else 0.5), duration=0.15).start(self._line.eq_label)
                try: Animation(opacity=(1 if self.focused or self._line.line_matched else 0.35), duration=0.15).start(self._line.line_number)
                except AttributeError: pass

                if self.focused:
                    # Use 1-based line index
                    self._line._screen.current_line = self._line.line

                    # If there's a function to set the editor's index, pass our 1-based line
                    if self._line.index_func:
                        # The parent's 0-based index + 1 => 1-based
                        self._line.index_func(self._line.index + 1)

                    if self._get_text_width(str(self.text), self.tab_width, self._label_cached) > self.width:
                        self.cursor = (len(self.text), self.cursor[1])
                        self.scroll_x = self._get_text_width(str(self.text), self.tab_width, self._label_cached) - self.width + 1
                        Clock.schedule_once(lambda *_: self.do_cursor_movement("cursor_end"), -1)

                        def select_error_handler(*a):
                            try: self.select_text(0)
                            except: pass

                        Clock.schedule_once(select_error_handler, 0.01)
                else:
                    self.do_cursor_movement("cursor_home")
                    self.scroll_x = 0

                self._update_overflow()

            # Type color and prediction
            @staticmethod
            def _input_validation(text: str):

                # Escape newlines and tabs from pasting
                if '\n' in text: text = text.replace('\n', '\\n')
                if '\r' in text: text = text.replace('\r', '\\r')
                if '\t' in text: text = text.replace('\t', '    ')

                return text

            def on_text(self, *args):

                # Update text in memory
                if self._line._data: self._line._data['value'] = self.text

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

                if self.search.opacity == 1: self.foreground_color = (0, 0, 0, 0)

                def highlight(*args):
                    self._original_text = self.text
                    try:
                        self._line._screen.check_match(self._line._data, self._line._screen.search_bar.text)
                        self._line.highlight_text(self._line.last_search)
                    except AttributeError: pass

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
                elif (keycode[1] == 'super' and control in modifiers) or (control in modifiers and keycode[1] in ['s', 'f']):
                    pass

                # Undo functionality
                elif (((not modifiers or bool([m for m in modifiers if m not in keycode[1]])) and (text or keycode[1] in ['backspace', 'delete', 'spacebar'])) or (keycode[1] in ['v', 'x'] and control in modifiers) or (keycode[1] == 'backspace' and control in modifiers)):
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

                else: super().keyboard_on_key_down(window, keycode, text, modifiers)

                # Process override defined behavior
                override_result = self._line.keyboard_overrides(self, window, keycode, text, modifiers)

                # Fix scrolling issues with text input after text updates
                def fix_scroll(*a):
                    # Fix overscroll (cursor X pos is less than input position
                    if self.cursor_pos[0] < (self.x):
                        self.scroll_x = 0

                    # Fix underscroll (cursor X pos is greater than max width, and cursor is at the end of text)
                    if (self.cursor_pos[0] >= Window.width - self._line.input_padding) and len(self.text) == self.cursor[0]:
                        self.scroll_x = self._get_text_width(self.text, self.tab_width, self._label_cached) - self.width + 12

                    # Update ellipses for content that's off-screen
                    self._update_overflow()

                Clock.schedule_once(fix_scroll, 0)

                if override_result: return override_result

            def scroll_search(self, *a):
                offset = 12
                if self.cursor_offset() - self.width + offset > 0 and self.scroll_x > 0:
                    offset = self.cursor_offset() - self.width + offset
                else:
                    offset = 0

                self.search.x = (self.x + 5.3) - offset

                def highlight(*args):
                    try: self._line.highlight_text(self._line.last_search)
                    except AttributeError: pass

                Clock.schedule_once(highlight, 0)

            def on_touch_down(self, touch):
                if self._line._screen.popup_widget: return
                else: return super().on_touch_down(touch)

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

                if self._line.line == self._line._screen.current_line: self.grab_focus()
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
                    def click(*a): webbrowser.open_new_tab(self.url)
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

            self.key_label.x = self.line_number.x + self.line_number.size_hint_max[0] + (self.spacing * 1.4) + 10 + self.indent_space
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
            except AttributeError: pass

        def highlight_text(self, text, animate=True, *a):
            # Attempt to highlight text in both key and value for searching.
            self.last_search = text
            self.key_label.text = self.key_label.original_text
            self.line_matched = self._data['line_matched']

            if not animate: Animation.stop_all(self.line_number)

            def draw_highlight_box(label, *args):
                label.canvas.before.clear()
                if self.key_label.url:
                    return

                def get_x(lb, ref_x): return lb.center_x - lb.texture_size[0] * 0.5 + ref_x
                def get_y(lb, ref_y): return lb.center_y + lb.texture_size[1] * 0.5 - ref_y

                for name, boxes in label.refs.items():
                    for box in boxes:
                        with label.canvas.before:
                            Color(*self.select_color)
                            Rectangle(pos=(get_x(label, box[0]), get_y(label, box[1])), size=(box[2] - box[0], box[1] - box[3]))

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
            if ((value.strip().startswith('{') and value.strip().endswith('}')) or (value.strip().startswith('[') and value.strip().endswith(']')) or (value.strip().startswith('(') and value.strip().endswith(')'))):
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
            def update_focus(*args): self._screen._input_focused = self.focus
            Clock.schedule_once(update_focus, 0)

            super(type(self), self)._on_focus(instance, value)
            Animation.stop_all(self.parent.input_background)
            Animation(opacity=0.9 if self.focus else 0.35, duration=0.2, step=0).start(self.parent.input_background)

        def grab_focus(self, *a):
            def focus_later(*args): self.focus = True
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
                if self.parent: self.parent.focus_input()
                return True

            if keycode[1] in ['r', 'z', 'y'] and control in modifiers:
                return None

            if keycode[1] == "backspace" and control in modifiers:
                original_index = self.cursor_col
                new_text, idx = constants.control_backspace(self.text, original_index)
                self.select_text(original_index - idx, original_index)
                self.delete_selection()

            else: super().keyboard_on_key_down(window, keycode, text, modifiers)

            # Fix overscroll
            if self.cursor_pos[0] > (self.x + self.width) - (self.width * 0.05):
                self.scroll_x += self.cursor_pos[0] - ((self.x + self.width) - (self.width * 0.05))

            if self.cursor_pos[0] < (self.x):
                self.scroll_x = 0

        def fix_overscroll(self, *args):
            if self.cursor_pos[0] < (self.x):
                self.scroll_x = 0

        def on_touch_down(self, touch):
            if self._screen.popup_widget: return
            else: return super().on_touch_down(touch)

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
            if self.current_line: return self.scroll_to_line(self.current_line, highlight=highlight, grab_focus=grab_focus)
            else: return None

        if highlight:
            original_color = constants.convert_color(new_input.key_label.default_color)['rgb']
            new_input.key_label.color = constants.brighten_color(original_color, 0.2)
            Animation.stop_all(new_input.key_label)
            Animation(color=original_color, duration=0.5).start(new_input.key_label)

        if grab_focus: new_input.value_label.grab_focus()

        # Force cursor to the end of the line
        if force_end: Clock.schedule_once(lambda *_: new_input.value_label.do_cursor_movement('cursor_end', True), 0)

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
        if content_height <= viewport_height: new_scroll_y = 1
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
                Clock.schedule_once(lambda *_: [line.highlight_text(self.search_bar.text, False) for line in self.scroll_layout.children], 0)

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
                    except AttributeError: pass

            if 'up' in position: index = index - 1
            else:                index = index + 1

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
                key_matched = f'[color=#000000][ref=0]{search_text}[/ref][/color]'.join([x for x in key_data.split(search_text)])
            elif key_text and key_data.endswith(key_text) and value_text.startswith(value_text):
                key_matched = f'[color=#000000][ref=0]{key_text}[/ref][/color]'.join([x for x in key_data.rsplit(key_text, 1)])

            # Check if search matches in value input/ghost label
            if search_text in value_data:
                value_matched = f'[color=#000000][ref=0]{search_text}[/ref][/color]'.join([x for x in value_data.split(search_text)])
            elif value_text and value_data.startswith(value_text) and key_data.endswith(key_text):
                value_matched = f'[color=#000000][ref=0]{value_text}[/ref][/color]'.join([x for x in value_data.split(value_text, 1)])

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
            if result: self.match_list.append(line)
            if result and not first_match: first_match = line

        # Update all visible widgets
        if not text: self.scroll_widget.refresh_from_data()

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
            Animation(opacity=(1 if text and self.match_list else 0.35 if text else 0), duration=0.1).start(self.match_label)
            matches = 0
            search_str = text.strip()
            if search_str:
                for x in self.match_list:
                    total_str = str(x['data']['key']) + str(x['data']['value'])
                    matches += total_str.count(search_str)
            self.match_label.text = f'{matches} match{"es" if matches != 1 else ""}'
        except AttributeError: pass

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
        try: save_config_file(self._config_data, content)
        except Exception as e:
            send_log(self.__class__.__name__, f"error saving '{self.path}': {constants.format_traceback(e)}", 'error')
            return False

        def set_banner(*a): self.set_banner_status(False)
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
            except AttributeError: continue

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
                    pos_hint = {"center_x": 0.5, "center_y": 0.9},
                    size = (250, 40),
                    color = "#F3ED61",
                    text = f"Editing '${self.file_name}$'",
                    icon = "pencil-sharp.png",
                    animate = True
                )
                self.add_widget(self.header)
            else:
                self.header = BannerObject(
                    pos_hint = {"center_x": 0.5, "center_y": 0.9},
                    size = (250, 40),
                    color = (0.4, 0.682, 1, 1),
                    text = f"Viewing '${self.file_name}$'",
                    icon = "eye-outline.png",
                    animate = True
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
                            Clock.schedule_once(functools.partial(self.popup_widget.window_input.do_cursor_movement, 'cursor_right', True), 0)

                    new_str = self.popup_widget.window_input.keyboard.keycode_to_string(keycode[0])
                    if 'shift' in modifiers:       new_str = new_str.upper()
                    if len(new_str) == 1:          insert_text(new_str)
                    elif keycode[1] == 'spacebar': insert_text(' ')
                    self.popup_widget.resize_window()

                else: self.popup_widget.resize_window()
                return True

            if keycode[1] in ['escape', 'n']:
                try: self.popup_widget.click_event(self.popup_widget, 'no')
                except AttributeError:
                    self.popup_widget.click_event(self.popup_widget, 'ok')

            elif keycode[1] in ['enter', 'return', 'y']:
                try: self.popup_widget.click_event(self.popup_widget, 'yes')
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
            else: self.quit_to_menu()
            return True

        if keycode[1] in ['down', 'up', 'pagedown', 'pageup']:
            return self.switch_input(keycode[1])

        if keycode[1] == 'f' and control in modifiers:
            if not self.search_bar.focused: self.search_bar.grab_focus()
            else:
                if self.current_line is not None: self.focus_input()
            return True

        if keycode[1] == 's' and control in modifiers and self.modified:
            self.save_file()
            return None

        # Undo/Redo
        if keycode[1] == 'z' and control in modifiers and self.undo_history:
            self.undo(save=False, undo=True)
        elif keycode[1] == 'z' and control in modifiers and not self.undo_history:
            if not self.check_data(): self.reset_data()

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
                else: self._shift_timer = Clock.schedule_once(self._reset_shift_counter, 0.25)  # Adjust time as needed
            return True

        def set_banner(*a): self.set_banner_status(not self.check_data())
        Clock.schedule_once(set_banner, 0)

        return True

    def generate_menu(self, **kwargs):
        self.server_obj = constants.server_manager.current_server

        # Editor UI
        self.scroll_widget = RecycleViewWidget(position=(0.5, 0.5), view_class=self.EditorLine)
        self.scroll_widget.always_overscroll = False
        self.scroll_layout = RecycleGridLayout(cols=1, size_hint_max_x=1250, size_hint_y=None, padding=[10, 30, 0, 30], default_size=(1250, 50))
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

            def update_background(*a): scroll_top.resize(); scroll_bottom.resize()
            Clock.schedule_once(update_background, 0)

        self.resize_bind = lambda *_: Clock.schedule_once(functools.partial(resize_scroll, self.scroll_widget, self.scroll_layout), 0)
        Window.bind(on_resize=self.resize_bind)
        self.resize_bind()

        self.scroll_widget.data = self.load_file()

        float_layout = FloatLayout()
        float_layout.id = 'content'
        self.scroll_widget.add_widget(self.scroll_layout)
        float_layout.add_widget(self.scroll_widget)

        scroll_top = ScrollBackground(pos_hint={"center_x": 0.5, "center_y": 0.9}, pos=self.scroll_widget.pos, size=(self.scroll_widget.width // 1.5, 60))
        scroll_top.color = self.background_color
        scroll_bottom = ScrollBackground(pos_hint={"center_x": 0.5}, pos=self.scroll_widget.pos, size=(self.scroll_widget.width // 1.5, -60))
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
        for b in buttons: float_layout.add_widget(b)

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
            clickable = True, anchor = 'right', click_func = show_controls
        )
        float_layout.add_widget(self.controls_button)

        self.header = BannerObject(
            pos_hint = {"center_x": 0.5, "center_y": 0.9},
            size = (250, 40),
            color = (0.4, 0.682, 1, 1),
            text = f"Viewing '${self.file_name}$'",
            icon = "eye-outline.png"
        )
        self.add_widget(self.header)

        self.controls_button = IconButton(
            'save & quit', {}, (120, 110), (None, None), 'save-sharp.png',
            clickable = True, anchor='right',
            click_func = self.save_and_quit,
            text_offset = (-5, 50)
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
                if not is_header: self.add_widget(self.value_label)

            # Ghost covers for left / right
            self.add_widget(self.ghost_cover_left)
            self.add_widget(self.ghost_cover_right)

            # Add remaining widgets
            if not (is_blank_line or is_comment or is_header): self.add_widget(self.eq_label)
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

        else: data = line

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
                if not is_header and not is_list_header: self.add_widget(self.value_label)

            # Ghost covers for left / right
            self.add_widget(self.ghost_cover_left)
            self.add_widget(self.ghost_cover_right)

            # Add remaining widgets
            if not (is_blank_line or is_comment or is_multiline_string): self.add_widget(self.eq_label)
            if is_multiline_string: self.key_label.opacity = 0
            self.add_widget(self.line_number)
            self.add_widget(self.key_label)

        @staticmethod
        def get_type(value: str):
            data_type = str

            # Define custom behavior for determining data types

            # Structured data detection
            if ((value.strip().startswith('{') and value.strip().endswith('}')) or (value.strip().startswith('[') and value.strip().endswith(']')) or (value.strip().startswith('(') and value.strip().endswith(')'))):
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
            def replace_text(val, *args): self.text = val

            if keycode[1] == "spacebar":
                if self.text == 'yes':
                    Clock.schedule_once(functools.partial(replace_text, 'no'), 0)
                    return
                elif self.text == 'no':
                    Clock.schedule_once(functools.partial(replace_text, 'yes'), 0)
                    return

            # Add a new multi-line string on pressing "enter" in a current string
            if ((not self._line.is_list_item and self.text) or (self._line.is_multiline_string and self.text)) and keycode[1] in ['enter', 'return']:
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
                        save = True,
                        action = {
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
                try:    next_line = self._line._screen.line_list[self._line.line - 1]['data']
                except: next_line = {'is_list_item': False, 'eof': True}
                eof = 'eof' in next_line

                # Record the removal action for undo
                if self._line.undo_func:
                    self._line.undo_func(
                        save = True,
                        action = {
                            'type': 'remove_line',
                            'data': self._line._data,
                            'index': self._line.line - 1
                        }
                    )

                self._line._screen.remove_line(self._line.line - 1)
                self._line._screen.scroll_to_line(self._line.line - 1, grab_focus=not eof)


            # Add a new list item on pressing "enter" in a current list
            elif (not self._line.is_multiline_string) and (((self._line.is_list_item and self.text) or (not self._line.is_list_item and not self.text)) and keycode[1] in ['enter', 'return']):
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
                        save = True,
                        action = {
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
                        save = True,
                        action = {
                            'type': 'remove_line',
                            'data': self._line._data,
                            'index': self._line.line - 1
                        }
                    )

                self._line._screen.remove_line(self._line.line - 1)

                # Existing focusing logic
                try:
                    previous_line = self._line._screen.line_list[self._line.line - 2]['data']
                    try:    next_line = self._line._screen.line_list[self._line.line - 1]['data']
                    except: next_line = {'is_list_item': False, 'eof': True}
                    eof = 'eof' in next_line

                    if previous_line['is_list_item']:
                        self._line._screen.scroll_to_line(self._line.line - 1, grab_focus=True)

                    if not previous_line['is_list_item'] and previous_line['is_list_header'] and not next_line[
                        'is_list_item']:
                        previous_line['is_list_header'] = False
                        previous_line['inactive'] = False
                        self._line._screen.scroll_to_line(self._line.line - 1, grab_focus=not eof)
                        for line in self._line.scroll_layout.children: line.value_label.focused = False
                        self._line.scroll_widget.data = self._line.line_list
                        self._line.scroll_widget.refresh_from_data()
                except: pass

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

        else: data = line

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

            if self.minified: final_content = json.dumps(yaml_data, indent=None, separators=(',', ':')).strip()
            else:             final_content = json.dumps(yaml_data, indent=4)

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
