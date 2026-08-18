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
        self.resize_list = None
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


        # Bind / cleanup height on resize
        def resize_scroll(*args):
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

            self._scroll_top.resize()
            self._scroll_bottom.resize()

        self.resize_list = resize_scroll
        self.resize_bind = lambda *_: Clock.schedule_once(resize_scroll, 0)
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
            cols = 2 if Window.width > 1250 else 1
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
