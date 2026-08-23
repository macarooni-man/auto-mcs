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
    discover_panel_trim = 30

    discover_fallback_icon = 'extension-puzzle.png'
    refresh_after_action = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.detail_panel = None
        self.selected_item = None
        self.detail_request = 0


    def is_discover_wide(self):
        return Window.width >= self.discover_breakpoint

    @staticmethod
    def _discover_name(item):
        return str(getattr(item, 'name', None) or getattr(item, 'title', None) or '').strip()

    @staticmethod
    def _discover_version(item, index=0):
        return str(
            getattr(item, 'addon_version', None) or
            getattr(item, 'download_version', None) or
            getattr(item, 'version', None) or
            f'release {index + 1}'
        ).strip()

    def find_discover_match(self, item, item_list):
        def normalize(value):
            return ''.join(c for c in str(value or '').lower() if c.isalnum())

        item_id = normalize(getattr(item, 'id', None))
        item_name = normalize(self._discover_name(item))

        for candidate in item_list:
            candidate_id = normalize(getattr(candidate, 'id', None))
            candidate_name = normalize(self._discover_name(candidate))

            if item_id and candidate_id and item_id == candidate_id:
                return candidate

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

        self.detail_panel = DiscoverPanel(
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

        if isinstance(results, bool):
            return response

        # Never retain a selection through empty results
        if not self.last_results:
            self.selected_item = None
            if self.detail_panel:
                self.detail_panel.clear()

        self.sync_discover_visibility()
        Clock.schedule_once(self.resize_list, 0)

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
