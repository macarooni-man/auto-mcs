from source.ui.desktop.widgets.buttons import button_action
from source.ui.desktop.widgets.inputs import SearchBar
from source.ui.desktop.widgets.pages import *
from source.ui.desktop.widgets.base import *



# ================================================ List Manager =========================================================

class ListSearchLayout:

    scroll_position = (0.5, 0.437)
    scroll_divisor = 1.79
    scroll_top = 0.715
    scroll_bottom = 0.17

    header_position = (0, 0.89)
    blank_position = 0.48
    search_position = 0.795
    page_position = (0.5, 0.805)

    no_line = False
    search_hotkey = True
    available_header = None
    animate_results = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.name = self.__class__.__name__
        self.menu = 'init'

        self._layout = None
        self.header = None
        self.scroll_layout = None
        self.blank_label = None
        self.search_bar = None
        self.action_layout = None
        self.page_switcher = None
        self.scroll_widget = None
        self.search_layout = None
        self.resize_bind = None
        self._scroll_top = None
        self._scroll_bottom = None

        self.last_results = []
        self.page_size = 20
        self.current_page = 0
        self.max_pages = 0
        self.anim_speed = 10

        self.header_text = ''
        self.empty_text = ''


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

    def prepare_list_results(self, results):
        return list(results)

    def before_list_render(self, results):
        pass

    def generate_list_header(self, results):
        count = len(results)
        very_bold_font = os.path.join(paths.ui_assets, 'fonts', constants.fonts["very-bold"])

        search_text = self.search_bar.previous_search
        if len(search_text) > 25:
            search_text = search_text[:22] + "..."

        if not search_text and self.available_header:
            prefix = translate(self.available_header)
        else:
            prefix = f"{translate('Search for')} '{search_text}'"

        count_text = (
            f'[color=#6A6ABA]{translate("No results")}[/color]'
            if count == 0

            else
            f'[font={very_bold_font}]1[/font] {translate("item")}'
            if count == 1

            else
            f'[font={very_bold_font}]{count:,}[/font] {translate("items")}'
        )

        return f"{prefix}  [color=#494977]-[/color]  {count_text}"

    def generate_list_button(self, item, index, fade_in, highlight):
        return None

    def update_list_header(self, text):
        for child in self.header.children:
            if child.id == "text":
                child.text = text
                break

    def get_list_button(self, index):
        if not self.scroll_layout:
            return None

        for button in self.scroll_layout.children:
            if button.view_index == index:
                return button

        return None

    def get_list_data(self, index):
        if not self.scroll_widget:
            return None

        for data in self.scroll_widget.data:
            if data['list_data']['index'] == index:
                return data['list_data']

        return None


    def resize_list(self, *args):
        self.scroll_widget.height = Window.height // self.scroll_divisor

        wide_layout = Window.width > 1250
        self.scroll_layout.cols = 2 if wide_layout else 1
        self.anim_speed = 13 if wide_layout else 10

        # Preserve the centered 1250px GridLayout
        horizontal_padding = max((Window.width - 1250) / 2, 0)

        # Vertically center short lists
        item_count = len(self.scroll_widget.data)

        if item_count:
            row_count = ((item_count - 1) // self.scroll_layout.cols) + 1

            content_height = (
                (row_count * self.scroll_layout.default_size[1]) +
                (max(0, row_count - 1) * self.scroll_layout.spacing[1])
            )

            vertical_padding = max((self.scroll_widget.height - content_height) / 2, 30)

        else:
            vertical_padding = 30

        self.scroll_layout.padding = [
            horizontal_padding,
            vertical_padding,
            horizontal_padding,
            vertical_padding
        ]

        if self._scroll_top:
            self._scroll_top.resize()
            self._scroll_bottom.resize()

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        super()._on_keyboard_down(keyboard, keycode, text, modifiers)

        # Press arrow keys to switch pages
        if keycode[1] in ['right', 'left'] and self.name == utility.screen_manager.current_screen.name:
            self.switch_page(keycode[1])

        elif self.search_hotkey and keycode[1] == "tab" and self.name == utility.screen_manager.current_screen.name:
            for widget in self.search_bar.children:
                try:
                    if widget.id == "search_input":
                        widget.grab_focus()
                        break
                except AttributeError:
                    pass

    def generate_list(self, header_text, blank_text, search_function, server_info=None, allow_empty=False, empty_text=None, actions=None):
        actions = actions or []

        # Reset list state
        self.last_results = []
        self.current_page = 0
        self.max_pages = 0


        # Recycled scroll list
        self.scroll_widget = RecycleViewWidget(position=self.scroll_position, view_class=ListButton)
        self.scroll_layout = RecycleGridLayout(
            cols = 1,
            spacing = 15,
            size_hint_y = None,
            default_size = (580, 85),
            default_size_hint = (1, None),
            padding = [0, 30, 0, 30]
        )

        self.scroll_layout.bind(minimum_height = self.scroll_layout.setter('height'))
        self.scroll_layout.id = 'scroll_content'
        self.resize_bind = lambda *_: Clock.schedule_once(self.resize_list, 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)


        # Scroll gradient
        self._scroll_top = ScrollBackground(
            pos_hint = {"center_x": 0.5, "center_y": self.scroll_top},
            pos = self.scroll_widget.pos,
            size = (self.scroll_widget.width // 1.5, 60)
        )

        self._scroll_bottom = ScrollBackground(
            pos_hint = {"center_x": 0.5, "center_y": self.scroll_bottom},
            pos = self.scroll_widget.pos,
            size = (self.scroll_widget.width // 1.5, -60)
        )


        # Generate layout
        self._layout = FloatLayout()
        self._layout.id = 'content'

        self.header_text = header_text
        self.empty_text = empty_text if empty_text is not None else blank_text
        self.header = HeaderText(header_text, '', self.header_position, __translate__=(False, True), no_line=self.no_line)
        self._layout.add_widget(self.header)


        # Add blank label to the center
        self.blank_label = Label()
        self.blank_label.text = blank_text
        self.blank_label.font_name = os.path.join(paths.ui_assets, 'fonts', constants.fonts['italic'])
        self.blank_label.pos_hint = {"center_x": 0.5, "center_y": self.blank_position}
        self.blank_label.font_size = sp(24)
        self.blank_label.color = (0.6, 0.6, 1, 0.35)
        self._layout.add_widget(self.blank_label)


        # Search / pagination / actions
        search_width = 500
        button_width = 55
        button_spacing = 5
        action_gap = 10

        action_width = (len(actions) * button_width) + (max(0, len(actions) - 1) * button_spacing)
        layout_width = search_width + (action_gap + action_width if actions else 0)
        self.search_layout = RelativeLayout(size_hint=(None, None), size=(layout_width, 80), pos_hint={"center_x": 0.5, "center_y": self.search_position})

        self.search_bar = SearchBar(
            return_function = search_function,
            server_info = server_info,
            pos_hint = {"center_x": 0.5, "center_y": 0.5},
            allow_empty = allow_empty,
            size_hint = (None, None),
            size = (search_width, 80)
        )
        self.search_bar.pos = (0, 0)
        self.search_layout.add_widget(self.search_bar)

        if actions:
            self.action_layout = BoxLayout(orientation="horizontal", spacing=button_spacing, size_hint=(None, None), size=(action_width, 80), pos=(search_width + action_gap, 0))
            for button in actions:
                button.size_hint = (None, None)
                button.size = (button_width, 80)
                self.action_layout.add_widget(button)

            self.search_layout.add_widget(self.action_layout)

        self.page_switcher = PageSwitcher(0, 0, self.page_position, self.switch_page)


        # Append Recycler layout
        self.scroll_widget.add_widget(self.scroll_layout)

        self._layout.add_widget(self.scroll_widget)
        self._layout.add_widget(self._scroll_top)
        self._layout.add_widget(self._scroll_bottom)
        self._layout.add_widget(self.search_layout)
        self._layout.add_widget(self.page_switcher)

        return self._layout

    def gen_search_results(self, results, new_search=False, fade_in=True, highlight=None, animate_scroll=None, last_scroll=None, *args):
        highlight_index = None

        # Error on remote/search failure
        if not results and isinstance(results, bool):
            self.show_popup(
                "warning",
                "Server Error",
                "There was an issue reaching the add-on repository\n\nPlease try again later",
                None
            )
            self.max_pages = 0
            self.current_page = 0
            return

        # Normalize result list
        results = self.prepare_list_results(results)

        self.last_results = results
        self.max_pages = (len(results) / self.page_size).__ceil__()
        self.current_page = 1 if (self.current_page == 0 or self.current_page > self.max_pages or new_search) else self.current_page

        # Default scroll position
        default_scroll = 1 if last_scroll is None else last_scroll

        # Move to the page containing a highlighted item
        if highlight:
            for start in range(0, len(results), self.page_size):
                page = results[start:start + self.page_size]

                for index, item in enumerate(page):
                    if getattr(item, "hash", None) == highlight:
                        self.current_page = (start // self.page_size) + 1
                        highlight_index = index + 1
                        break

                if highlight_index:
                    break

        # Update page counter
        self.page_switcher.update_index(self.current_page, self.max_pages)

        page_list = results[
            (self.page_size * self.current_page) - self.page_size:
            self.page_size * self.current_page
        ]

        # Predict highlighted item scroll position based on RV data
        if highlight_index:
            cols = self.scroll_layout.cols
            row = (highlight_index - 1) // cols
            rows = ((len(page_list) - 1) // cols) + 1

            item_height = self.scroll_layout.default_size[1]
            spacing = self.scroll_layout.spacing[1]
            viewport = self.scroll_widget.height

            content_height = (rows * item_height) + (max(0, rows - 1) * spacing) + 60

            if content_height > viewport:
                max_offset = content_height - viewport
                target_top = 30 + (row * (item_height + spacing))
                target_offset = target_top - ((viewport - item_height) / 2)
                target_offset = max(0, min(target_offset, max_offset))

                default_scroll = 1 - (target_offset / max_offset)

            else:
                default_scroll = 1

        # Let screen prepare any render state
        self.before_list_render(results)

        # Update header
        self.update_list_header(self.generate_list_header(results))

        # Empty state
        if not results:
            self.scroll_widget.data = []
            self.blank_label.text = self.empty_text
            utility.hide_widget(self.blank_label, False)
            self.blank_label.opacity = 0

            Animation(opacity=1, duration=0.2).start(self.blank_label)
            self.max_pages = 0
            self.current_page = 0
            return

        utility.hide_widget(self.blank_label, True)

        # Generate logical Recycler data
        list_data = []
        for index, item in enumerate(page_list, 1):
            list_data.append({
                'list_data': {
                    'item': item,
                    'index': index,
                    'generator': self.generate_list_button,
                    'fade_in': (index if index <= 8 else 8) / self.anim_speed if fade_in else 0,
                    'fade_until': Clock.get_time() + ((index if index <= 8 else 8) / self.anim_speed if fade_in else 0),
                    'highlight': False,
                    'state': {}
                }
            })

        # Reset the viewport before loading a normal page
        if not highlight_index:
            self.scroll_widget.scroll_y = default_scroll

        self.scroll_widget.data = list_data
        self.resize_list()

        # Restore / animate scroll
        if animate_scroll is None:
            animate_scroll = self.animate_results

        Animation.stop_all(self.scroll_widget)
        if animate_scroll: Animation(scroll_y=default_scroll, duration=0.1).start(self.scroll_widget)
        else: self.scroll_widget.scroll_y = default_scroll

        if highlight_index:
            def _highlight_button(*args):
                if utility.screen_manager.current != self.name:
                    return

                button = self.get_list_button(highlight_index)
                if button: button.highlight()
                else: Clock.schedule_once(_highlight_button, 0)

            Clock.schedule_once(_highlight_button, 0.11 if animate_scroll else 0)



class ListDiscoverLayout(ListSearchLayout):

    discover_breakpoint = 1400
    discover_list_width = 630
    discover_panel_width = 580
    discover_small_width = 650
    discover_gap = 45
    discover_panel_trim = 15

    discover_fallback_icon = 'extension-puzzle.png'
    refresh_after_action = True
    loading_after_action = False


    # Inline details panel
    class DiscoverPanel(RelativeLayout):
        collapsed_scale = 0.983
        collapsed_opacity = 0.7

        class ProjectIcon(Widget):
            load_timeout = 8
            cache_limit = 48
            texture_cache = {}
            cache_order = []

            def __init__(self, fallback, **kwargs):
                super().__init__(**kwargs)

                self.size_hint = (None, None)
                self.size = (46, 46)

                self.fallback = fallback
                self._source = None
                self._state = 'fallback'
                self._timeout_event = None

                background_color = constants.background_color

                # Circular backing & remote icon
                with self.canvas:
                    Color(*background_color[:3], 1)
                    self.background = Ellipse()

                    self.image_color = Color(1, 1, 1, 0)
                    self.project_image = Ellipse()

                # Local fallback icon
                self.fallback_image = Image(
                    source = fallback,
                    size_hint = (None, None),
                    size = (40, 40),
                    allow_stretch = True,
                    keep_ratio = True,
                    color = (0.6, 0.6, 1, 1)
                )
                self.add_widget(self.fallback_image)

                # Hidden AsyncImage only fetches the remote icon
                self.image = AsyncImage(size_hint=(None, None), opacity=0)
                self.image.bind(on_load=self.image_loaded, on_error=self.image_error)
                self.add_widget(self.image)

                # Loading animation
                self.loader = AsyncImage(
                    source = os.path.join(paths.ui_assets, 'animations', 'loading_pickaxe.gif'),
                    size_hint = (None, None),
                    size = (36, 36),
                    allow_stretch = True,
                    color = (0.6, 0.6, 1, 1),
                    opacity = 0
                )
                self.loader.anim_delay = utility.anim_speed * 0.02
                self.add_widget(self.loader)

                self.bind(pos=self.resize_icon, size=self.resize_icon)
                self.resize_icon()

            @classmethod
            def cache_texture(cls, source, texture):
                if not source or not texture:
                    return

                cls.texture_cache[source] = texture

                try: cls.cache_order.remove(source)
                except ValueError: pass

                cls.cache_order.append(source)

                while len(cls.cache_order) > cls.cache_limit:
                    cls.texture_cache.pop(cls.cache_order.pop(0), None)

            def resize_icon(self, *args):
                self.background.pos = self.project_image.pos = self.pos
                self.background.size = self.project_image.size = self.size

                self.fallback_image.size = (40, 40)
                self.fallback_image.center = self.center

                self.loader.center = self.center

                self.image.pos = self.pos
                self.image.size = self.size

            def cancel_timeout(self):
                if self._timeout_event:
                    self._timeout_event.cancel()
                    self._timeout_event = None

            def show_fallback(self, *args):
                self.cancel_timeout()

                self._state = 'fallback'
                self.image_color.a = 0
                self.loader.opacity = 0
                self.fallback_image.opacity = 1

            def reset(self):
                self.cancel_timeout()

                self._source = None
                self._state = 'fallback'

                self.project_image.texture = None
                self.image_color.a = 0
                self.loader.opacity = 0
                self.fallback_image.opacity = 1

            def load(self, source=None, fallback=None):
                if fallback and fallback != self.fallback:
                    self.fallback = fallback
                    self.fallback_image.source = fallback

                if not source:
                    self.reset()
                    return

                # preview() -> set_data() shouldn't restart the same request
                if source == self._source and self._state in ('loading', 'loaded'):
                    return

                cached = self.texture_cache.get(source)
                if cached:
                    self.cancel_timeout()
                    self.cache_texture(source, cached)

                    self._source = source
                    self._state = 'loaded'

                    self.project_image.texture = cached
                    self.image_color.a = 1
                    self.loader.opacity = 0
                    self.fallback_image.opacity = 0
                    return

                self.cancel_timeout()

                self._source = source
                self._state = 'loading'

                self.image_color.a = 0
                self.fallback_image.opacity = 0
                self.loader.opacity = 1

                if self.image.source == source:
                    self.image.reload()
                else:
                    self.image.source = source

                self._timeout_event = Clock.schedule_once(functools.partial(self.image_timeout, source), self.load_timeout)

            def image_loaded(self, instance, *args):
                if instance.source != self._source or self._state != 'loading':
                    return

                # AsyncImage's actual source texture is now available
                if not instance.texture:
                    return Clock.schedule_once(functools.partial(self.image_loaded, instance), 0)

                self.cancel_timeout()
                self.cache_texture(instance.source, instance.texture)

                self._state = 'loaded'
                self.project_image.texture = instance.texture
                self.image_color.a = 1

                self.loader.opacity = 0
                self.fallback_image.opacity = 0

            def image_error(self, instance, *args):
                if instance.source == self._source:
                    self.show_fallback()

            def image_timeout(self, source, *args):
                if source == self._source and self._state == 'loading':
                    self.show_fallback()

        class ProjectButton(RelativeLayout):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)

                self.size_hint = (None, None)
                self.size = (135 if constants.app_config.locale == 'en' else 155, 30)

                self.button = HoverButton()
                self.button.id = 'project_button'
                self.button.hover_scale = 1.025
                self.button.size_hint = (None, None)
                self.button.size = self.size
                self.button.pos = (0, 0)
                self.button.border = (0, 0, 0, 0)
                self.button.background_color = (0.6, 0.6, 1, 0.45)
                self.button.background_normal = os.path.join(paths.ui_assets, 'addon_view_button.png')
                self.button.background_down = self.button.background_normal
                self.button.background_disabled_normal = self.button.background_normal
                self.button.background_disabled_down = self.button.background_normal
                self.button.text = 'view project'
                self.button.color = constants.brighten_color(constants.background_color, -0.01)
                self.button.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
                self.button.font_size = sp(16)

                def on_enter(*args):
                    if not self.button.ignore_hover:
                        animate_background(self.button, self.button.background_normal, True, 1.025, _no_bg_change=True)
                        Animation(background_color=(0.65, 0.65, 1, 0.65), duration=0.1).start(self.button)

                def on_leave(*args):
                    if not self.button.ignore_hover:
                        animate_background(self.button, self.button.background_normal, False, 1.025, _no_bg_change=True)
                        Animation(background_color=(0.6, 0.6, 1, 0.45), duration=0.1).start(self.button)

                self.button.on_enter = on_enter
                self.button.on_leave = on_leave
                self.add_widget(self.button)

        def __init__(self, close_func=None, action_func=None, select_func=None, **kwargs):
            super().__init__(**kwargs)

            self.size_hint = (None, None)
            self.close_func = close_func
            self.data = None
            self._active = False
            self._transitioning = False
            self.banners = []
            self.project_url = None

            with self.canvas.before:
                self.anim_push = PushMatrix()
                self.anim_scale = Scale(0.96, 0.96, 1, origin=(self.width / 2, self.height / 2))

            with self.canvas.after:
                self.anim_pop = PopMatrix()


            # Background
            self.panel_background = ParagraphBackground()
            self.add_widget(self.panel_background)


            # Scrollable description
            self.scroll = ScrollView(size_hint=(None, None))
            self.scroll.do_scroll_x = False
            self.scroll.bar_width = 5
            self.scroll.bar_color = (0.6, 0.6, 1, 1)
            self.scroll.bar_inactive_color = (0.6, 0.6, 1, 0.25)
            self.scroll.scroll_wheel_distance = dp(55)

            self.description = Label(
                size_hint = (None, None),
                font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["regular"]}.ttf'),
                font_size = sp(18),
                color = (0.65, 0.65, 1, 0.85),
                halign = 'left',
                valign = 'top'
            )
            self.description.__translate__ = False
            self.description.line_height = 1.2

            self.scroll.add_widget(self.description)
            self.add_widget(self.scroll)


            self.scroll_top = Image(source=os.path.join(paths.ui_assets, 'scroll_gradient.png'), size_hint=(None, None), allow_stretch=True, keep_ratio=False, color=constants.background_color, opacity=0)
            self.scroll_bottom = Image(source=os.path.join(paths.ui_assets, 'scroll_gradient.png'), size_hint=(None, None), allow_stretch=True, keep_ratio=False, color=constants.background_color, opacity=0)
            self.add_widget(self.scroll_top)
            self.add_widget(self.scroll_bottom)


            # Empty state/loading icon
            self.placeholder = Label(
                text = translate('select an item to view details'),
                size_hint = (None, None),
                font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf'),
                font_size = sp(21),
                color = (0.6, 0.6, 1, 0.35),
                halign = 'center',
                valign = 'middle'
            )
            self.add_widget(self.placeholder)

            self.loading_icon = AsyncImage(
                source = os.path.join(paths.ui_assets, 'animations', 'loading_pickaxe.gif'),
                size_hint = (None, None),
                size = (42, 42),
                allow_stretch = True,
                color = (0.6, 0.6, 1, 1),
                opacity = 0
            )
            self.loading_icon.anim_delay = utility.anim_speed * 0.02
            self.loading_label = Label(
                text = translate('loading details'),
                size_hint = (None, None),
                size = (180, 24),
                font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf'),
                font_size = sp(20),
                color = (0.6, 0.6, 1, 0.7),
                halign = 'center',
                opacity = 0
            )
            self.add_widget(self.loading_label)
            self.add_widget(self.loading_icon)


            # Project image
            self.icon = self.ProjectIcon(icon_path('extension-puzzle.png'))
            self.add_widget(self.icon)


            # Project title / author
            self.title = Label(
                size_hint = (None, None),
                font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf'),
                font_size = sp(24),
                color = (0.65, 0.65, 1, 1),
                halign = 'left',
                valign = 'middle',
                shorten = True,
                shorten_from = 'right',
                max_lines = 1
            )
            self.title.__translate__ = False
            self.add_widget(self.title)

            self.author = Label(
                size_hint = (None, None),
                font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf'),
                font_size = sp(19),
                color = (0.65, 0.65, 1, 0.56),
                halign = 'left',
                valign = 'middle',
                shorten = True,
                shorten_from = 'right',
                max_lines = 1
            )
            self.author.__translate__ = False
            self.add_widget(self.author)


            # Close button
            self.close_button = RelativeIconButton(
                '',
                {"center_x": 0.5, "center_y": 0.5},
                None,
                (None, None),
                'close-sharp.png',
                click_func = lambda *_: self.close_func() if self.close_func else None
            )
            self.close_button.size_hint = (None, None)
            self.close_button.size = (40, 40)
            self.close_button.button.size = (40, 40)
            self.close_button.icon.size = (20, 20)
            self.close_button.button.background_disabled_normal = self.close_button.button.background_normal
            self.close_button.button.background_disabled_down = self.close_button.button.background_normal
            self.add_widget(self.close_button)


            # Version + contextual install/delete action
            self.action_bar = DropActionBar(action_func=action_func, select_func=select_func)
            self.add_widget(self.action_bar)


            # Project button
            self.project_button = self.ProjectButton()
            self.project_button.opacity = 0
            self.project_button.disabled = True
            self.project_button.button.bind(on_release=self.open_project)
            self.add_widget(self.project_button)


            self.bind(pos=self.resize_animation, size=self.resize_animation)
            self.bind(size=self.resize_panel)
            self.clear()

        def resize_animation(self, *args):
            self.anim_scale.origin = (self.width / 2, self.height / 2)

        def animate_panel(self):
            Animation.stop_all(self)
            try: Animation.cancel_all(self.anim_scale)
            except: pass

            self.opacity = self.collapsed_opacity
            self.anim_scale.x = self.anim_scale.y = self.collapsed_scale

            Animation(opacity=1, duration=0.13, t='out_cubic').start(self)
            Animation(x=1, y=1, duration=0.13, t='out_cubic').start(self.anim_scale)

        def hide_panel(self, callback=None):
            if self._transitioning:
                return

            self._transitioning = True

            Animation.stop_all(self)
            try: Animation.cancel_all(self.anim_scale)
            except: pass

            duration = 0.13
            fade = Animation(opacity=self.collapsed_opacity, duration=duration, t='out_cubic')
            scale = Animation(x=self.collapsed_scale, y=self.collapsed_scale, duration=duration, t='out_cubic')

            def _finish(*args):
                self._transitioning = False
                if callback: callback()

            scale.bind(on_complete=_finish)

            fade.start(self)
            scale.start(self.anim_scale)

        def resize_text(self, *args):
            self.description.text_size = (max(self.description.width - 12, 0), None)
            self.description.texture_update()
            self.description.height = self.description.texture_size[1] + 45

        def resize_panel(self, *args):

            # Background
            self.panel_background.pos = (0, 0)
            self.panel_background.size = self.size

            # Compact 58px header
            padding = 15
            header_y = self.height - self.action_bar.height - padding

            self.icon.pos = (
                padding,
                header_y + ((self.action_bar.height - self.icon.height) / 2)
            )

            action_x = self.width - self.action_bar.width - 58
            self.action_bar.pos = (action_x, header_y)

            self.close_button.pos = (self.width - 52, self.height - 52)

            title_x = self.icon.right + 12
            title_width = max(action_x - title_x - 12, 100)

            self.title.pos = (title_x, header_y + 29)
            self.title.size = (title_width, 26)
            self.title.text_size = self.title.size

            self.author.pos = (title_x, header_y + 4)
            self.author.size = (title_width, 23)
            self.author.text_size = self.author.size


            # Banners
            if self.banners:
                banner_y = header_y - 40
                banner_gap = 10
                banner_width = sum(banner.width for banner in self.banners) + ((len(self.banners) - 1) * banner_gap)
                banner_x = (self.width - banner_width) / 2

                for banner in self.banners:
                    banner.pos = (banner_x, banner_y)
                    banner_x += banner.width + banner_gap

                content_top = banner_y - 2

            else:
                content_top = header_y - 4

            # Project link
            self.project_button.pos = ((self.width - self.project_button.width) / 2, 15)
            content_bottom = self.project_button.top if self.project_url else padding

            # Description
            self.scroll.pos = (padding, content_bottom)
            self.scroll.size = (max(self.width - (padding * 2), 0), max(content_top - content_bottom, 0))

            self.description.width = self.scroll.width
            self.resize_text()

            # Description fade edges
            fade_height = 30
            scrollbar_width = 5
            self.scroll_top.pos = (self.scroll.x, self.scroll.top - (fade_height / 1.5))
            self.scroll_top.size = (self.scroll.width - scrollbar_width, fade_height)
            self.scroll_bottom.pos = (self.scroll.x, self.scroll.y + (fade_height / 1.5))
            self.scroll_bottom.size = (self.scroll.width - scrollbar_width, -fade_height)

            self.placeholder.pos = (0, 0)
            self.placeholder.size = self.size
            self.placeholder.text_size = (max(self.width - 80, 0), self.height)

            self.loading_icon.center = (self.width / 2, (self.height / 2) + 14)
            self.loading_label.center = (self.width / 2, (self.height / 2) - 24)

        def reset_close_button(self):
            button = self.close_button.button
            button.on_leave(duration=0)
            button.hovered = False
            button.state = 'normal'

        def _fallback_icon(self, name=None):
            path = icon_path(name or 'extension-puzzle.png')
            return path if os.path.isfile(path) else icon_path('extension-puzzle.png')

        def _set_active(self, active):
            self._active = active

            if not active:
                self.reset_close_button()

            opacity = 1 if active else 0

            for widget in [self.icon, self.title, self.author, self.close_button, self.action_bar, self.scroll]:
                widget.opacity = opacity

            for banner in self.banners:
                banner.opacity = opacity

            self.project_button.opacity = opacity if self.project_url else 0
            self.close_button.button.disabled = not active
            self.scroll.do_scroll_y = active
            self.project_button.disabled = not active or not bool(self.project_url)

            self.placeholder.opacity = 0 if active else 1
            self.panel_background.set_opacity(1 if active else 0.48)
            self.scroll_top.opacity = self.scroll_bottom.opacity = opacity

        def reset_scroll(self, *args):
            Animation.stop_all(self.scroll)
            self.scroll.scroll_y = 1

        def clear(self):
            Animation.stop_all(self)
            try: Animation.cancel_all(self.anim_scale)
            except: pass

            self.data = None
            self.set_banners([])
            self.set_project_url(None)
            self._set_active(False)

            self.icon.reset()
            self.title.text = ''
            self.author.text = ''
            self.description.text = ''
            self.loading_icon.opacity = 0
            self.loading_label.opacity = 0

            self.action_bar.set_data([])
            self.action_bar.opacity = 0

            self.opacity = self.collapsed_opacity
            self.anim_scale.x = self.anim_scale.y = self.collapsed_scale
            self._transitioning = False

        def preview(self, data):
            Animation.stop_all(self)
            try: Animation.cancel_all(self.anim_scale)
            except: pass

            self.data = None
            self.set_banners([])
            self.set_project_url(None)
            self.reset_close_button()
            self.reset_scroll()
            self._set_active(False)

            self.icon.reset()
            self.title.text = ''
            self.author.text = ''
            self.description.text = ''

            self.placeholder.opacity = 0
            self.close_button.opacity = 1
            self.close_button.button.disabled = False
            self.action_bar.opacity = 0

            self.loading_icon.opacity = 0
            self.loading_label.opacity = 0

            self.opacity = self.collapsed_opacity
            self.anim_scale.x = self.anim_scale.y = self.collapsed_scale
            self.resize_panel()

        def set_data(self, data, reset_scroll=True):
            last_scroll = self.scroll.scroll_y
            self.loading_icon.opacity = 0
            self.loading_label.opacity = 0

            self.data = data
            self.set_banners(data.get('banners'))
            self.set_project_url(data.get('project_url'))
            self._set_active(True)

            self.icon.load(data.get('icon_url'), self._fallback_icon(data.get('fallback_icon')))
            self.title.text = data.get('title') or ''
            self.author.text = data.get('author') or 'Unknown'
            self.description.text = (data.get('description') or '').strip() or translate('description unavailable')

            options = data.get('versions') or []
            self.action_bar.opacity = 1 if options else 0
            self.action_bar.set_data(
                options,
                selected = data.get('selected'),
                installed_version = data.get('installed_version'),
                allow_remove = data.get('allow_remove', True),
                action_icon = data.get('action_icon', 'arrow-down.png')
            )

            self.resize_panel()

            if reset_scroll:
                self.reset_scroll()
                Clock.schedule_once(self.reset_scroll, 0)
            else:
                self.scroll.scroll_y = last_scroll
                Clock.schedule_once(lambda *_: setattr(self.scroll, 'scroll_y', last_scroll), 0)

            self.loading(False)

            if reset_scroll:
                self.animate_panel()

        def loading(self, value, *args):
            self.action_bar.loading(value)

            show_loader = value and self.data is None
            self.loading_icon.opacity = 1 if show_loader else 0
            self.loading_label.opacity = 1 if show_loader else 0

        def set_banners(self, banners):
            for banner in self.banners:
                if banner.parent is self: self.remove_widget(banner)

            self.banners = []

            for data in banners or []:
                banner = BannerObject(pos_hint={}, **data)
                banner.opacity = 1 if self._active else 0
                self.banners.append(banner)
                self.add_widget(banner)

            if hasattr(self, 'scroll'):
                self.resize_panel()

        def set_project_url(self, url):
            self.project_url = url
            self.project_button.opacity = 1 if self._active and url else 0
            self.project_button.disabled = not bool(url)

            if hasattr(self, 'scroll'):
                self.resize_panel()

        def open_project(self, *args):
            if self.project_url:
                webbrowser.open_new_tab(self.project_url)


    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.detail_panel = None
        self.selected_item = None
        self.pending_search = None
        self.pending_select_first = False
        self.detail_request = 0


    def is_discover_wide(self):
        return Window.width >= self.discover_breakpoint

    @staticmethod
    def _discover_name(item):
        return str(getattr(item, 'name', None) or getattr(item, 'title', None) or '').strip()

    @staticmethod
    def _discover_version(item, index=0):
        return str(
            getattr(item, 'display_version', None) or
            getattr(item, 'addon_version', None) or
            getattr(item, 'download_version', None) or
            getattr(item, 'version', None) or
            f'release {index + 1}'
        ).strip()

    # Queues a search to be executed the next time this Discovery screen loads
    def queue_discover_search(self, query, select_first=None):
        if select_first is None: select_first = self.is_discover_wide()
        self.pending_search = str(query or '').strip()
        self.pending_select_first = bool(select_first)

    # Executes the queued search, or a fallback query when loaded normally
    def load_discover_search(self, default='', *args):
        if self.pending_search is not None:
            query = self.pending_search
            self.pending_search = None

        else:
            query = default
            self.pending_select_first = False

        if self.search_bar:
            self.search_bar.search_input.text = query
            self.search_bar.execute_search(query)

    def find_discover_match(self, item, item_list):
        def normalize(value):
            return ''.join(c for c in str(value or '').lower() if c.isalnum())

        item_id = normalize(getattr(item, 'id', None))
        item_name = normalize(self._discover_name(item))

        for candidate in item_list:
            candidate_id = normalize(getattr(candidate, 'id', None))
            candidate_name = normalize(self._discover_name(candidate))

            if item_id and candidate_id:
                if item_id == candidate_id:
                    return candidate
                continue

            if item_name and candidate_name and item_name == candidate_name:
                return candidate

        return None

    def build_discover_versions(self, releases, installed=None):
        releases = list(releases or [])
        installed_version = str(getattr(installed, 'addon_version', None) or getattr(installed, 'version', None) or '').strip()
        installed_key = self._discover_version_key(installed_version)

        # Always expose the installed version if the provider no longer returns it
        if installed_key and not any(self._discover_version_key(self._discover_version(release)) == installed_key for release in releases):
            releases.append(installed)

        # Preserve provider releases sharing the same human version
        options = []
        labels = {}

        for index, release in enumerate(releases):
            version = self._discover_version(release, index)
            labels[version] = labels.get(version, 0) + 1
            options.append((version if labels[version] == 1 else f'{version} ({labels[version]})', release))

        return options

    def get_discover_preview(self, item):
        return {
            'title': self._discover_name(item),
            'author': getattr(item, 'author', None) or 'Unknown',
            'icon_url': getattr(item, 'icon_url', None),
            'fallback_icon': self.discover_fallback_icon
        }

    def load_discover_item(self, item):
        return None

    def perform_discover_action(self, item, release, mode):
        return False

    def discover_back_button(self, position=(0.5, 0.12), **kwargs):
        button = ExitButton('Back', position, **kwargs)

        def _back():
            if not self.is_discover_wide() and self.selected_item:
                return self.clear_discover_item()
            button_action('Back', button.button)

        button.custom_func = _back
        return button


    def generate_list(self, *args, **kwargs):
        self.detail_request += 1
        self.selected_item = None
        self.detail_panel = None

        layout = super().generate_list(*args, **kwargs)

        self.detail_panel = self.DiscoverPanel(
            close_func = self.clear_discover_item,
            action_func = self.run_discover_action,
            select_func = self.select_discover_release
        )

        layout.add_widget(self.detail_panel)
        self.sync_discover_visibility()

        Clock.schedule_once(self.resize_list, 0.01)
        return layout

    def _show_result_list(self, visible):
        widgets = (
            self.scroll_widget,
            self._scroll_top,
            self._scroll_bottom
        )

        if visible:
            index = len(self._layout.children)

            for widget in widgets:
                if widget and not widget.parent:
                    self._layout.add_widget(widget, index=index)

        else:
            for widget in widgets:
                if widget and widget.parent is self._layout:
                    self._layout.remove_widget(widget)

    def _show_detail_panel(self, visible):
        if not self.detail_panel:
            return

        if visible:
            if not self.detail_panel.parent:
                self._layout.add_widget(self.detail_panel)

        elif self.detail_panel.parent is self._layout:
            self._layout.remove_widget(self.detail_panel)

    def sync_discover_visibility(self, *args):
        if not self.detail_panel:
            return

        # Initial page / no results: hide list & pane
        if not self.last_results:
            self._show_result_list(False)
            self._show_detail_panel(False)
            return

        wide_layout = self.is_discover_wide()
        selected = self.selected_item is not None

        if wide_layout:
            self._show_result_list(True)
            self._show_detail_panel(True)

        elif selected:
            self._show_result_list(False)
            self._show_detail_panel(True)

        else:
            self._show_detail_panel(False)
            self._show_result_list(True)

    @staticmethod
    def _discover_version_key(version):
        version = str(version or '').strip().lower()
        return version[1:] if version.startswith('v') else version

    @staticmethod
    def get_discover_release(versions, selected):
        return next((release for label, release in versions if label == selected), None)

    def get_discover_banners(self, item, release):
        return []

    def select_discover_release(self, release):
        if self.detail_panel and self.selected_item:
            self.detail_panel.set_banners(self.get_discover_banners(self.selected_item, release))

    def get_discover_selected(self, versions, installed=None, server_version=None):
        if installed:
            installed_version = getattr(installed, 'addon_version', None) or getattr(installed, 'version', None)
            installed_key = self._discover_version_key(installed_version)

            if installed_key:
                for label, release in versions:
                    release_version = getattr(release, 'addon_version', None) or getattr(release, 'version',
                                                                                         None) or label
                    if self._discover_version_key(release_version) == installed_key:
                        return label

        if server_version:
            for label, release in versions:
                if str(server_version) in [str(version) for version in (getattr(release, 'versions', None) or [])]:
                    return label

        return versions[0][0] if versions else None


    def resize_list(self, *args):
        if not self.scroll_widget:
            return

        self.scroll_widget.size_hint = (None, None)
        self.scroll_widget.height = Window.height // self.scroll_divisor
        self.scroll_layout.cols = 1
        self.anim_speed = 10

        wide_layout = self.is_discover_wide()
        list_width = self.discover_list_width if wide_layout else min(self.discover_list_width, Window.width - 60)
        panel_width = self.discover_panel_width if wide_layout else min(self.discover_small_width, Window.width * 0.75)

        if wide_layout:
            total_width = list_width + self.discover_gap + panel_width
            list_x = Window.center[0] - (total_width / 2)
            panel_x = list_x + list_width + self.discover_gap

        else:
            list_x = Window.center[0] - (list_width / 2)
            panel_x = Window.center[0] - (panel_width / 2)

        scroll_y = (Window.height * self.scroll_position[1]) - (self.scroll_widget.height / 2)

        self.scroll_widget.pos_hint = {}
        self.scroll_widget.pos = (list_x, scroll_y)
        self.scroll_widget.width = list_width

        item_width = self.scroll_layout.default_size[0]
        available_padding = max(list_width - item_width, 0)
        left_padding = min(25, available_padding)
        right_padding = max(available_padding - left_padding, 0)

        # Vertically center short lists
        item_count = len(self.scroll_widget.data)

        if item_count:
            content_height = (
                (item_count * self.scroll_layout.default_size[1]) +
                (max(0, item_count - 1) * self.scroll_layout.spacing[1])
            )
            vertical_padding = max((self.scroll_widget.height - content_height) / 2, 30)

        else:
            vertical_padding = 30

        self.scroll_layout.padding = [
            left_padding,
            vertical_padding,
            right_padding,
            vertical_padding
        ]

        # Gradients follow the entire padded list viewport
        if self._scroll_top:
            self._scroll_top.pos_hint = {}
            self._scroll_top.pos = (list_x, self.scroll_widget.top - 30)
            self._scroll_top.size = (list_width, 60)

            self._scroll_bottom.pos_hint = {}
            self._scroll_bottom.pos = (list_x, self.scroll_widget.y + 30)
            self._scroll_bottom.size = (list_width, -60)

        # Detail pane & list vertical positioning
        if self.detail_panel:
            panel_height = max(self.scroll_widget.height - self.discover_panel_trim, 300)
            panel_height = min(panel_height, self.scroll_widget.height)

            self.detail_panel.size_hint = (None, None)
            self.detail_panel.pos_hint = {}
            self.detail_panel.pos = (panel_x, self.scroll_widget.top - panel_height - 6)
            self.detail_panel.size = (panel_width, panel_height)
            self.detail_panel.resize_panel()

        self.sync_discover_visibility()

    def _load_discover_item(self, item, request, reset_scroll=True):
        def _load():
            try:
                data = self.load_discover_item(item)
                error = None

            except Exception as e:
                data = None
                error = e

            def _finish(*args):
                if request != self.detail_request or utility.screen_manager.current != self.name:
                    return

                if not data:
                    self.detail_panel.loading(False)
                    self.show_banner(
                        (1, 0.5, 0.65, 1),
                        "Failed to load item details",
                        "close-circle-sharp.png",
                        2.5,
                        {"center_x": 0.5, "center_y": 0.965}
                    )

                    if error and constants.debug:
                        constants.send_log('ui.widgets.layouts.ListDiscoverLayout', f'failed to load "{item}": {constants.format_traceback(error)}', 'error')

                    return

                self.selected_item = data.get('item', item)
                self.detail_panel.set_data(data, reset_scroll)

            Clock.schedule_once(_finish, 0)

        dTimer(0, _load).start()

    def clear_discover_item(self, *args):
        if not self.selected_item:
            return

        self.detail_request += 1

        def _finish(*args):
            self.selected_item = None
            self.detail_panel.clear()

            if self.is_discover_wide(): self.sync_discover_visibility()
            else: Clock.schedule_once(self.sync_discover_visibility, 0)

        if self.detail_panel: self.detail_panel.hide_panel(_finish)
        else: _finish()

    def select_discover_item(self, item, *args):
        if self.selected_item and self.find_discover_match(item, [self.selected_item]):
            return

        self.detail_request += 1
        request = self.detail_request
        self.selected_item = item

        self.detail_panel.preview(self.get_discover_preview(item))
        self.detail_panel.loading(True)

        if self.is_discover_wide():
            self.sync_discover_visibility()
        else:
            Clock.schedule_once(self.sync_discover_visibility, 0)

        self._load_discover_item(item, request)

    def refresh_discover_results(self):
        if not self.last_results:
            return

        last_scroll = self.scroll_widget.scroll_y
        self.gen_search_results(
            self.last_results,
            fade_in = False,
            animate_scroll = False,
            last_scroll = last_scroll
        )

    def run_discover_action(self, release, mode):
        if not release or not self.selected_item:
            return

        item = self.selected_item
        self.detail_request += 1
        request = self.detail_request
        self.detail_panel.loading(True)

        def _run():
            try:
                success = self.perform_discover_action(item, release, mode)
                error = None

            except Exception as e:
                success = False
                error = e

            def _finish(*args):
                if utility.screen_manager.current != self.name:
                    return

                if success is False:
                    self.detail_panel.loading(False)
                    self.show_banner(
                        (1, 0.5, 0.65, 1),
                        "Failed to apply changes",
                        "close-circle-sharp.png",
                        2.5,
                        {"center_x": 0.5, "center_y": 0.965}
                    )

                    if error and constants.debug:
                        constants.send_log('ui.widgets.layouts.ListDiscoverLayout', f'failed to run action "{mode}": {constants.format_traceback(error)}', 'error')

                    return

                if not self.refresh_after_action:
                    if not self.loading_after_action:
                        self.detail_panel.loading(False)
                    return

                self.refresh_discover_results()
                if request == self.detail_request and self.selected_item:
                    self._load_discover_item(item, request, False)

            Clock.schedule_once(_finish, 0)

        dTimer(0, _run).start()

    def gen_search_results(self, results, new_search=False, fade_in=True, highlight=None, animate_scroll=None, last_scroll=None, *args):
        if new_search:
            self.clear_discover_item()

        response = super().gen_search_results(results, new_search, fade_in, highlight, animate_scroll, last_scroll, *args)

        # Consume queued selection state for this search
        select_first = self.pending_select_first
        self.pending_select_first = False

        if isinstance(results, bool):
            return response

        # Never retain a selection through empty results
        if not self.last_results:
            self.selected_item = None
            if self.detail_panel:
                self.detail_panel.clear()

        self.sync_discover_visibility()
        Clock.schedule_once(self.resize_list, 0)

        # Automatically open the first result when requested
        if select_first and self.last_results:
            Clock.schedule_once(functools.partial(self.select_discover_item, self.last_results[0]), 0)

        return response



class ListManageLayout(ListSearchLayout):

    scroll_position = (0.5, 0.5)
    scroll_divisor = 1.85
    scroll_top = 0.775
    scroll_bottom = 0.25

    header_position = (0, 0.9)
    blank_position = 0.55
    search_position = 0.845
    page_position = (0.5, 0.86)

    no_line = True
    search_hotkey = False
    animate_results = True

    def generate_list_header(self, results):
        return self.header_text



# =============================================== History List ==========================================================

class ListHistoryLayout:

    history_header_position = (0, 0.89)

    class Timeline(RelativeLayout):

        max_labels = 6
        max_ticks = 80

        def __init__(self, group_func=None, select_func=None, drag_func=None, **kwargs):
            super().__init__(**kwargs)

            self.size_hint = (None, None)

            self.group_func = group_func
            self.select_func = select_func
            self.drag_func = drag_func

            self.history_list = []
            self.selected_index = 0
            self.display_position = 0

            self.dragging = False
            self.drag_moved = False
            self.drag_origin = None

            self.ticks = []
            self.labels = []
            self.major_indices = set()

            self.rail_bottom = 58
            self.rail_top = 58

            self.bold_font = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["bold"]}.ttf')

            self.line_color = (0.3, 0.3, 0.5, 1)
            self.line_width = dp(2)

            self.minor_tick_length = dp(9)
            self.major_tick_length = dp(16)
            self.selector_length = dp(22)

            with self.canvas.before:
                self.rail_color = Color(*self.line_color)
                self.rail = Rectangle(pos=(0, 0), size=(self.line_width, 1))

                self.now_color = Color(*self.line_color)
                self.now_line = Rectangle(pos=(0, 0), size=(self.major_tick_length, self.line_width))

                self.selector_color = Color(0.72, 0.72, 1, 0)
                self.selector = Rectangle(pos=(0, 0), size=(self.selector_length, self.line_width))
                self.selector_dot = Ellipse(size=(dp(10), dp(10)))

            self.now_label = Label(
                text = translate('now'),
                size_hint = (None, None),
                size = (110, 24),
                halign = 'right',
                valign = 'middle',
                font_size = sp(15),
                font_name = self.bold_font,
                color = (0.6, 0.6, 1, 0.7)
            )
            self.now_label.__translate__ = False
            self.now_label.text_size = self.now_label.size
            self.add_widget(self.now_label)

            self.calendar_icon = Image(
                source = icon_path('calendar-outline.png'),
                size_hint = (None, None),
                size = (24, 24),
                color = (0.6, 0.6, 1, 0.72)
            )
            self.add_widget(self.calendar_icon)

            self.history_label = Label(
                text = 'history',
                size_hint = (None, None),
                size = (120, 28),
                halign = 'right',
                valign = 'middle',
                font_size = sp(17),
                font_name = self.bold_font,
                color = (0.6, 0.6, 1, 0.78)
            )
            self.history_label.__translate__ = False
            self.history_label.text_size = self.history_label.size
            self.add_widget(self.history_label)

            self.bind(pos=self.resize_self, size=self.resize_self)

        def _clear_timeline(self):
            for label in self.labels:
                try: self.remove_widget(label)
                except: pass

            for index, tick, color, major in self.ticks:
                try: self.canvas.before.remove(tick)
                except: pass

                try: self.canvas.before.remove(color)
                except: pass

            self.labels = []
            self.ticks = []
            self.major_indices = set()

        def _raise_selector(self):
            for instruction in (self.selector_color, self.selector, self.selector_dot):
                try: self.canvas.before.remove(instruction)
                except: pass

            for instruction in (self.selector_color, self.selector, self.selector_dot):
                self.canvas.before.add(instruction)

        def build_timeline(self):
            self._clear_timeline()

            if not self.history_list:
                self.resize_self()
                return

            groups = []
            last_group = None

            for index, item in enumerate(self.history_list):
                group = self.group_func(item)

                if group != last_group:
                    groups.append((index, group))
                    last_group = group

            if len(groups) > self.max_labels:
                reduced = []

                for x in range(self.max_labels):
                    item = groups[round((len(groups) - 1) * (x / (self.max_labels - 1)))]
                    if item not in reduced: reduced.append(item)

                groups = reduced

            self.major_indices = {index for index, text in groups}

            step = max(1, (len(self.history_list) + self.max_ticks - 1) // self.max_ticks)
            indices = list(range(0, len(self.history_list), step))

            if indices and indices[-1] != len(self.history_list) - 1:
                indices.append(len(self.history_list) - 1)

            with self.canvas.before:
                for index in indices:
                    endpoint = index in (0, len(self.history_list) - 1)
                    major = index in self.major_indices or endpoint

                    color = Color(*self.line_color)
                    tick = Rectangle(pos=(0, 0), size=(1, self.line_width))

                    self.ticks.append((index, tick, color, major))

            self._raise_selector()

            for index, text in groups:
                label = Label(
                    text = text,
                    size_hint = (None, None),
                    size = (120, 24),
                    halign = 'right',
                    valign = 'middle',
                    font_size = sp(15),
                    font_name = self.bold_font,
                    color = (0.6, 0.6, 1, 0.42)
                )

                label.__translate__ = False
                label.text_size = label.size
                label.timeline_index = index

                self.labels.append(label)
                self.add_widget(label)

            self.resize_self()

        def set_history(self, history_list):
            self.history_list = list(history_list)
            self.selected_index = 0
            self.display_position = 0

            self.build_timeline()

            if self.history_list:
                self.set_index(0)
                self.set_position(0)

        def get_y(self, position):
            if len(self.history_list) <= 1: return self.rail_bottom

            ratio = position / (len(self.history_list) - 1)
            return self.rail_bottom + (ratio * (self.rail_top - self.rail_bottom))

        def get_tick_y(self, index):
            y = self.get_y(index)

            if index == 0:
                y += self.line_width / 2

            elif index == len(self.history_list) - 1:
                y -= self.line_width / 2

            return y

        def get_position(self, y):
            if not self.history_list: return None
            if len(self.history_list) == 1: return 0

            ratio = (y - self.rail_bottom) / max(self.rail_top - self.rail_bottom, 1)
            ratio = max(0, min(1, ratio))

            return ratio * (len(self.history_list) - 1)

        def _update_selector(self):
            rail_x = self.width - 20

            if not self.history_list:
                self.selector_color.a = 0
                return

            selected_y = self.get_y(self.display_position)

            selector_bottom = selected_y - (self.line_width / 2)
            selector_top = selected_y + (self.line_width / 2)

            for index, tick, color, major in self.ticks:
                tick_y = self.get_tick_y(index)
                tick_bottom = tick_y - (self.line_width / 2)
                tick_top = tick_y + (self.line_width / 2)

                overlaps = tick_bottom < selector_top and tick_top > selector_bottom
                color.a = 0 if overlaps else 1

            self.selector.pos = (rail_x - self.selector_length, selected_y - (self.line_width / 2))
            self.selector.size = (self.selector_length, self.line_width)
            self.selector_dot.pos = (rail_x - dp(4), selected_y - dp(5))
            self.selector_color.a = 1

        def set_position(self, position):
            if not self.history_list: return

            self.display_position = max(0, min(position, len(self.history_list) - 1))
            self._update_selector()

        def set_index(self, index):
            if not self.history_list: return

            self.selected_index = max(0, min(index, len(self.history_list) - 1))

            if self.labels:
                selected_label = self.labels[0]

                for label in self.labels:
                    if label.timeline_index <= self.selected_index:
                        selected_label = label
                    else:
                        break

                for label in self.labels:
                    label.color = (0.74, 0.74, 1, 1) if label == selected_label else (0.6, 0.6, 1, 0.42)

        def resize_self(self, *args):
            self.rail_bottom = 58
            self.rail_top = max(self.height - 62, self.rail_bottom)

            rail_x = self.width - 20

            # Base rail
            self.rail.pos = (rail_x, self.rail_bottom)
            self.rail.size = (self.line_width, self.rail_top - self.rail_bottom)

            # Header
            self.calendar_icon.center = (rail_x - 10, self.height - 28)
            self.history_label.pos = (rail_x - self.history_label.width - 34, self.height - 40)

            # Minor / major ticks
            for index, tick, color, major in self.ticks:
                y = self.get_tick_y(index)
                length = self.major_tick_length if major else self.minor_tick_length

                tick.pos = (rail_x - length, y - (self.line_width / 2))
                tick.size = (length, self.line_width)

            # Date labels
            for label in self.labels:
                y = self.get_y(label.timeline_index)
                label.pos = (rail_x - label.width - 24, y - (label.height / 2))

            # Now
            self.now_label.pos = (rail_x - self.now_label.width - 24, self.rail_bottom - 43)
            self.now_line.pos = (rail_x - self.major_tick_length, self.rail_bottom - 29 - (self.line_width / 2))
            self.now_line.size = (self.major_tick_length, self.line_width)

            self._update_selector()

        def on_touch_down(self, touch):
            if not self.collide_point(*touch.pos):
                return super().on_touch_down(touch)

            if getattr(touch, 'button', 'left') == 'left':
                self.dragging = True
                self.drag_moved = False
                self.drag_origin = touch.pos

                touch.grab(self)
                return True

            return super().on_touch_down(touch)

        def on_touch_move(self, touch):
            if self.dragging:
                if not self.drag_moved and abs(touch.y - self.drag_origin[1]) >= dp(4):
                    self.drag_moved = True

                if self.drag_moved:
                    local_x, local_y = self.to_local(*touch.pos)
                    self.drag_func(self.get_position(local_y))

                return True

            return super().on_touch_move(touch)

        def on_touch_up(self, touch):
            if self.dragging:
                self.dragging = False

                try: touch.ungrab(self)
                except: pass

                local_x, local_y = self.to_local(*touch.pos)
                position = self.get_position(local_y)

                if position is not None:
                    if self.drag_moved:
                        self.drag_func(position)

                    self.select_func(round(position), True)

                self.drag_moved = False
                self.drag_origin = None

                return True

            return super().on_touch_up(touch)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.name = self.__class__.__name__
        self.menu = 'init'

        self._layout = None
        self.header = None

        self.selection_layout = None
        self.selection_date = None
        self.selection_details = None

        self.scroll_widget = None
        self.scroll_layout = None
        self._scroll_top = None
        self._scroll_bottom = None

        self.timeline = None

        self.action_layout = None
        self.back_button = None
        self.history_action_button = None
        self._history_selection_lock = False

        self.history_results = []
        self.selected_item = None
        self.selected_index = 0

        self.history_position = 0.0
        self._history_target = 0.0

        self._history_clock = None
        self._history_settle = None
        self._hover_release = None

        self._programmatic_scroll = False
        self._history_scrolling = False
        self._wheel_active = False

        self.resize_bind = None


    # History presentation hooks
    def generate_history_group(self, item):
        date = str(item.date)

        today = translate('today')
        yesterday = translate('yesterday')

        if date.casefold().startswith(today.casefold()): return today
        if date.casefold().startswith(yesterday.casefold()): return yesterday

        try:
            date_obj = backup.convert_date_str(os.path.basename(item.path))
            return date_obj.strftime('%b %d, %Y').replace(' 0', ' ')
        except:
            return date.split(' ', 1)[0]


    def generate_history_details(self, item):
        build = f' (b-{item.build})' if item.build else ''

        return (
            item.date,
            f'{item.type.lower()} {item.version}{build}   [color=#494977]-[/color]   {item.size}'
        )


    def history_selection_changed(self, item, index, final):
        pass


    # Helpers
    def _max_history_index(self):
        return max(len(self.history_results) - 1, 0)


    def get_history_button(self, index):
        if not self.scroll_layout: return None

        for button in self.scroll_layout.children:
            if isinstance(button, ListHistoryButton) and button.view_index == index:
                return button

        return None


    def set_history_action_enabled(self, enabled):
        if not self.history_action_button: return

        self.history_action_button.button.disabled = not enabled
        self.history_action_button.button.ignore_hover = not enabled

        color = (0.6, 0.6, 1, 1 if enabled else 0.4)

        self.history_action_button.text.color = color
        self.history_action_button.icon.color = color


    # Hover / recycled row state
    def _reset_history_buttons(self, suppress_hover=False):
        if not self.scroll_layout: return

        for item in self.scroll_layout.children:
            if isinstance(item, ListHistoryButton):
                item._reset_visuals(suppress_hover)


    def _release_history_hover(self, *args):
        self._hover_release = None
        if self._history_scrolling: return

        for item in self.scroll_layout.children:
            if isinstance(item, ListHistoryButton):
                item._reset_visuals(False)


    def _schedule_history_hover(self):
        if self._hover_release: self._hover_release.cancel()
        self._hover_release = Clock.schedule_once(self._release_history_hover, 0.06)


    def _set_history_scrolling(self, active):
        if self._history_scrolling == active: return

        self._history_scrolling = active

        if active:
            if self._hover_release:
                self._hover_release.cancel()
                self._hover_release = None

            self._reset_history_buttons(True)

        else:
            self._reset_history_buttons(True)
            self._schedule_history_hover()


    # Selection
    def update_history_selection(self, index, final=True):
        if not self.history_results:
            self.selected_item = None
            self.selected_index = 0
            self.set_history_action_enabled(False)
            return

        index = max(0, min(index, len(self.history_results) - 1))
        if index == self.selected_index and not final: return

        self.selected_index = index
        self.selected_item = self.history_results[index]


        # Persist logical RV state
        if self.scroll_widget:
            for data in self.scroll_widget.data:
                history_data = data.get('history_data', {})
                history_data['selected'] = history_data.get('index') == index


        # Update visible rows
        if self.scroll_layout:
            animate_radio = final and not self._history_scrolling
            for item in self.scroll_layout.children:
                if isinstance(item, ListHistoryButton):
                    item.set_selected(item.view_index == index, animate_radio)


        if self.timeline:
            self.timeline.set_index(index)


        date, details = self.generate_history_details(self.selected_item)

        self.selection_date.text = date
        self.selection_details.text = details

        self.set_history_action_enabled(True)
        self.history_selection_changed(self.selected_item, index, final)


        if final:
            self._reset_history_buttons(True)

            if not self._history_scrolling:
                self._schedule_history_hover()


    # Smooth scrolling
    def _cancel_history_clock(self):
        if self._history_clock:
            self._history_clock.cancel()
            self._history_clock = None


    def _cancel_history_settle(self):
        if self._history_settle:
            self._history_settle.cancel()
            self._history_settle = None


    def _start_history_clock(self):
        if not self._history_clock:
            self._history_clock = Clock.schedule_interval(self._smooth_history_scroll, 0)


    def _apply_history_position(self, position):
        if not self.scroll_widget: return

        maximum = self._max_history_index()
        position = max(0, min(position, maximum))

        self.history_position = position
        scroll_y = position / maximum if maximum else 0

        self._programmatic_scroll = True

        try: self.scroll_widget.scroll_y = scroll_y
        finally: self._programmatic_scroll = False

        self.update_history_position(position=position)


    def _smooth_history_scroll(self, dt):
        error = self._history_target - self.history_position
        dt = max(0, min(dt, 0.05))

        blend = 1 - pow(0.000001, dt)

        if abs(error) > 0.001:
            self._apply_history_position(self.history_position + (error * blend))
            return True

        self._apply_history_position(self._history_target)

        if abs(self._history_target - round(self._history_target)) > 0.001:
            return True

        self.update_history_selection(round(self._history_target))

        self._history_selection_lock = False
        self._history_clock = None
        self._set_history_scrolling(False)

        return False


    def update_history_position(self, *args, position=None):
        if not self.scroll_widget or not self.history_results: return

        if position is None:
            position = self.scroll_widget.scroll_y * self._max_history_index()

        position = max(0, min(position, self._max_history_index()))
        self.history_position = position


        # Select the row currently crossing the visual center
        if not self._history_selection_lock:
            nearest = round(position)
            if nearest != self.selected_index:
                self.update_history_selection(nearest, False)


        for item in self.scroll_layout.children:
            if isinstance(item, ListHistoryButton):
                item.set_depth(item.view_index - position)


        if self.timeline:
            self.timeline.set_position(position)

    def on_history_wheel(self, button):
        if not self.history_results: return

        self._history_selection_lock = False
        self._cancel_history_settle()

        if not self._wheel_active:
            self._wheel_active = True
            self._history_target = self.history_position

        # History indices run newest -> oldest; invert native Kivy wheel direction
        direction = -1 if button == 'scrollup' else 1

        self._history_target += direction * 0.72
        self._history_target = max(0, min(self._history_target, self._max_history_index()))

        self._set_history_scrolling(True)
        self._start_history_clock()

        self._history_settle = Clock.schedule_once(self._finish_history_wheel, 0.11)


    def _finish_history_wheel(self, *args):
        self._history_settle = None
        self._wheel_active = False

        self._history_target = float(round(self._history_target))
        self._history_target = max(0, min(self._history_target, self._max_history_index()))

        self._start_history_clock()


    def on_history_scroll(self, *args):
        if utility.screen_manager.current != self.name or self._programmatic_scroll: return

        self._history_selection_lock = False
        self._cancel_history_clock()
        self._cancel_history_settle()

        self._wheel_active = False

        self.update_history_position()

        self._history_target = self.history_position
        self._set_history_scrolling(True)
        self._history_settle = Clock.schedule_once(self._finish_history_drag, 0.13)


    def _finish_history_drag(self, *args):
        self._history_settle = None

        try: self.scroll_widget.effect_y.velocity = 0
        except: pass

        self._history_target = float(round(self.history_position))
        self._start_history_clock()


    def drag_history(self, position):
        if position is None or not self.history_results: return

        self._history_selection_lock = False
        self._cancel_history_clock()
        self._cancel_history_settle()

        self._wheel_active = False

        position = max(0, min(position, self._max_history_index()))
        self._history_target = position

        self._set_history_scrolling(True)
        self._apply_history_position(position)

    def select_history(self, index, animate=True):
        if not self.history_results: return

        index = max(0, min(round(index), len(self.history_results) - 1))

        self._cancel_history_settle()
        self._wheel_active = False

        self._history_selection_lock = True
        self._history_target = float(index)

        # Explicit selection should update immediately
        self.update_history_selection(index, False)

        if not animate:
            self._cancel_history_clock()
            self._apply_history_position(self._history_target)
            self.update_history_selection(index)

            self._history_selection_lock = False
            self._set_history_scrolling(False)
            return

        self._set_history_scrolling(True)
        self._start_history_clock()


    # Mouse / keyboard
    def on_touch_down(self, touch):
        button = getattr(touch, 'button', None)

        if button in ('scrollup', 'scrolldown') and not self.popup_widget:
            over_history = self.scroll_widget and self.scroll_widget.collide_point(*touch.pos)
            over_timeline = self.timeline and self.timeline.collide_point(*touch.pos)

            if over_history or over_timeline:
                self.on_history_wheel(button)
                return True

        return super().on_touch_down(touch)


    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        super()._on_keyboard_down(keyboard, keycode, text, modifiers)

        if self.name != utility.screen_manager.current_screen.name or self.popup_widget or not self.history_results:
            return

        key = keycode[1]

        if key in ('up', 'right'):    self.select_history(self.selected_index + 1)
        elif key in ('down', 'left'): self.select_history(self.selected_index - 1)
        elif key == 'home':           self.select_history(0)
        elif key == 'end':            self.select_history(len(self.history_results) - 1)


    # Layout
    def attach_history_actions(self, back_button, action_button):
        self.back_button = back_button
        self.history_action_button = action_button

        self.action_layout = RelativeLayout(size_hint=(None, None), size=(455, 67))
        self.action_layout.add_widget(self.back_button)
        self.action_layout.add_widget(self.history_action_button)

        self._layout.add_widget(self.action_layout)

        self.set_history_action_enabled(bool(self.history_results))
        Clock.schedule_once(self.resize_history, 0)


    def resize_history(self, *args):
        if not self.scroll_widget: return

        timeline_width = 185 if Window.width > 1100 else 165
        gap = 8

        scroll_width = min(880, max(620, Window.width - timeline_width - 48))


        # Bottom controls
        action_y = max(dp(95), Window.height * 0.12)

        if self.action_layout:
            self.action_layout.center = (Window.width / 2, action_y)

        action_top = action_y + (self.action_layout.height / 2 if self.action_layout else 33.5)
        self.selection_layout.center = (Window.width / 2, action_top + dp(40))


        # Action icons
        if self.back_button:
            self.back_button.icon.center = (
                self.back_button.button.x + 38,
                self.back_button.button.center_y
            )

        if self.history_action_button:
            self.history_action_button.icon.center = (
                self.history_action_button.button.x + 40,
                self.history_action_button.button.center_y
            )


        # Fill available vertical space between header and selection
        scroll_top_y = Window.height * 0.855
        scroll_bottom_y = self.selection_layout.top - dp(20)
        scroll_height = max(scroll_top_y - scroll_bottom_y, dp(300))


        # Preserve current wide/small history positioning
        list_offset = dp(0 if Window.width > 1100 else 50)
        left = max(((Window.width - scroll_width) / 2) - list_offset, dp(10))


        # History
        self.scroll_widget.pos_hint = {}
        self.scroll_widget.size_hint = (None, None)
        self.scroll_widget.size = (scroll_width, scroll_height)
        self.scroll_widget.pos = (left, scroll_bottom_y)


        # First/last items can reach visual center
        row_height = self.scroll_layout.default_size[1]
        vertical_padding = max((scroll_height - row_height) / 2, 0)
        self.scroll_layout.padding = [0, vertical_padding, 0, vertical_padding]


        # Scroll gradients
        gradient_height = 60
        gradient_center_x = self.scroll_widget.center_x / Window.width

        self._scroll_top.size = (scroll_width, gradient_height)
        self._scroll_bottom.size = (scroll_width, -gradient_height)

        self._scroll_top.pos_hint = {
            'center_x': gradient_center_x,
            'center_y': (self.scroll_widget.top - (gradient_height / 2)) / Window.height
        }

        self._scroll_bottom.pos_hint = {
            'center_x': gradient_center_x,
            'center_y': (self.scroll_widget.y + (gradient_height / 2)) / Window.height
        }

        self._scroll_top.resize()
        self._scroll_bottom.resize()


        # Timeline
        timeline_x = min(left + scroll_width + gap, Window.width - timeline_width - dp(10))

        self.timeline.size = (timeline_width, scroll_height)
        self.timeline.pos = (timeline_x, scroll_bottom_y)
        self.timeline.resize_self()

        Clock.schedule_once(self.update_history_position, 0)


    # Data
    def gen_history_results(self, results):
        self.history_results = list(results)

        self.selected_item = None
        self.selected_index = 0
        self.history_position = 0
        self._history_target = 0

        self.timeline.opacity = 1 if self.history_results else 0.25
        self.timeline.set_history(self.history_results)

        position_func = lambda: self.history_position
        scrolling_func = lambda: self._history_scrolling

        self.scroll_widget.data = [
            {
                'history_data': {
                    'item': item,
                    'index': index,
                    'selected': index == 0,
                    'depth': index,
                    'click_function': self.select_history,
                    'position': position_func,
                    'is_scrolling': scrolling_func
                }
            }
            for index, item in reversed(list(enumerate(self.history_results)))
        ]

        if self.history_results:
            self.scroll_widget.scroll_y = 0
            self.update_history_selection(0)

        else:
            self.selection_date.text = translate('No back-ups available')
            self.selection_details.text = ''
            self.set_history_action_enabled(False)

        self.resize_history()
        Clock.schedule_once(self.update_history_position, 0.05)


    def generate_history(self, results, header_text, empty_text='No back-ups available'):
        self.history_results = list(results)


        # Main layout
        self._layout = FloatLayout()
        self._layout.id = 'content'


        # Header
        self.header = HeaderText(header_text, '', self.history_header_position)
        self._layout.add_widget(self.header)


        # Recycled history
        self.scroll_widget = RecycleViewWidget(position=(0.5, 0.515), view_class=ListHistoryButton, effect_cls=ScrollEffect)
        self.scroll_widget.size_hint = (None, None)
        self.scroll_widget.pos_hint = {}
        self.scroll_widget.bar_width = 0
        self.scroll_widget.drag_pad = 0
        self.scroll_widget.always_overscroll = False

        self.scroll_layout = RecycleGridLayout(
            cols = 1,
            spacing = (0, 8),
            size_hint_y = None,
            default_size = (620, 100),
            default_size_hint = (1, None),
            padding = [0, 0, 0, 0]
        )

        self.scroll_layout.bind(minimum_height=self.scroll_layout.setter('height'))
        self.scroll_layout.id = 'scroll_content'

        self.scroll_widget.add_widget(self.scroll_layout)
        self._layout.add_widget(self.scroll_widget)


        # Scroll fade
        self._scroll_top = ScrollBackground(
            pos_hint = {'center_x': 0.5, 'center_y': 0.77},
            pos = self.scroll_widget.pos,
            size = (620, 60)
        )

        self._scroll_bottom = ScrollBackground(
            pos_hint = {'center_x': 0.5, 'center_y': 0.26},
            pos = self.scroll_widget.pos,
            size = (620, -60)
        )

        self._layout.add_widget(self._scroll_top)
        self._layout.add_widget(self._scroll_bottom)


        # Timeline
        self.timeline = self.Timeline(
            group_func = self.generate_history_group,
            select_func = self.select_history,
            drag_func = self.drag_history
        )

        self._layout.add_widget(self.timeline)


        # Selected item info
        self.selection_layout = RelativeLayout(size_hint=(None, None), size=(560, 48))

        self.selection_date = Label(
            text = '',
            size_hint = (1, None),
            height = 25,
            pos_hint = {'center_x': 0.5, 'center_y': 0.72},
            halign = 'center',
            valign = 'middle',
            font_size = sp(20),
            font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["bold"]}.ttf'),
            color = (0.65, 0.65, 1, 1)
        )
        self.selection_date.__translate__ = False
        self.selection_date.bind(size=lambda *_: setattr(self.selection_date, 'text_size', self.selection_date.size))

        self.selection_details = Label(
            text = '',
            size_hint = (1, None),
            height = 20,
            pos_hint = {'center_x': 0.5, 'center_y': 0.25},
            halign = 'center',
            valign = 'middle',
            markup = True,
            font_size = sp(15),
            font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf'),
            color = (0.6, 0.6, 1, 0.72)
        )
        self.selection_details.__translate__ = False
        self.selection_details.bind(size=lambda *_: setattr(self.selection_details, 'text_size', self.selection_details.size))

        self.selection_layout.add_widget(self.selection_date)
        self.selection_layout.add_widget(self.selection_details)
        self._layout.add_widget(self.selection_layout)


        # Scroll events
        self.scroll_widget.bind(scroll_y=self.on_history_scroll)


        # Responsive layout
        self.resize_bind = lambda *_: Clock.schedule_once(self.resize_history, 0)
        Window.bind(on_resize=self.resize_bind)

        self.gen_history_results(results)

        return self._layout

    def on_leave(self, *args):
        self._cancel_history_clock()
        self._cancel_history_settle()

        if self._hover_release:
            self._hover_release.cancel()
            self._hover_release = None

        if self.resize_bind:
            try: Window.unbind(on_resize=self.resize_bind)
            except: pass
            self.resize_bind = None

        return super().on_leave(*args)
