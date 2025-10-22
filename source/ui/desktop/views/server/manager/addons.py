from source.ui.desktop.views.server.manager.components import *



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

                    if len(addon.name) < 26: addon_name = addon.name
                    else:                    addon_name = addon.name[:23] + "..."

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
                scroll_top.resize(); scroll_bottom.resize()

            Clock.schedule_once(update_grid, 0)


        self.resize_bind = lambda*_: Clock.schedule_once(functools.partial(resize_scroll, scroll_widget, self.scroll_layout, scroll_anchor), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        self.scroll_layout.bind(minimum_height=self.scroll_layout.setter('height'))
        self.scroll_layout.id = 'scroll_content'


        # Scroll gradient
        scroll_top = ScrollBackground(pos_hint={"center_x": 0.5, "center_y": 0.795}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, 60))
        scroll_bottom = ScrollBackground(pos_hint={"center_x": 0.5, "center_y": 0.27}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, -60))

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

        for button in buttons: float_layout.add_widget(button)
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

                        if len(addon.name) < 26: addon_name = addon.name
                        else:                    addon_name = addon.name[:23] + "..."

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
                scroll_top.resize(); scroll_bottom.resize()

            Clock.schedule_once(update_grid, 0)


        self.resize_bind = lambda*_: Clock.schedule_once(functools.partial(resize_scroll, scroll_widget, self.scroll_layout, scroll_anchor), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        self.scroll_layout.bind(minimum_height=self.scroll_layout.setter('height'))
        self.scroll_layout.id = 'scroll_content'

        # Scroll gradient
        scroll_top = ScrollBackground(pos_hint={"center_x": 0.5, "center_y": 0.715}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, 60))
        scroll_bottom = ScrollBackground(pos_hint={"center_x": 0.5, "center_y": 0.17}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, -60))

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
        self.search_bar = SearchBar(return_function=search_function, server_info=foundry.new_server_info, pos_hint={"center_x": 0.5, "center_y": 0.795})
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

        for button in buttons: float_layout.add_widget(button)

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



# Server Add-on Manager ------------------------------------------------------------------------------------------------

class AddonListButton(HoverButton):

    def toggle_enabled(self, *args):
        self.title.text_size = (self.size_hint_max[0] * (0.7), self.size_hint_max[1])
        self.background_normal = os.path.join(paths.ui_assets, f'{self.id}{"" if self.enabled else "_disabled"}.png')

        # If disabled, add banner as such
        if not self.enabled:
            self.disabled_banner = BannerObject(
                pos_hint={"center_x": 0.5, "center_y": 0.5},
                size=(125, 32),
                color=(1, 0.53, 0.58, 1),
                text="disabled",
                icon="close-circle.png",
                icon_side="right"
            )
            self.add_widget(self.disabled_banner)

        self.resize_self()

    def resize_self(self, *args):

        # Title and description
        padding = 2.17
        self.title.pos = (self.x + (self.title.text_size[0] / padding) - 6, self.y + 31)
        self.subtitle.pos = (self.x + (self.subtitle.text_size[0] / padding) - 1, self.y)
        self.hover_text.pos = (self.x + (self.size[0] / padding) - 30, self.y + 15)

        # Type Banner
        if self.disabled_banner:
            self.disabled_banner.pos_hint = {"center_x": None, "center_y": None}
            self.disabled_banner.pos = (self.width + self.x - self.disabled_banner.width - 18, self.y + 38.5)

        # Delete button
        self.delete_layout.size_hint_max = (self.size_hint_max[0], self.size_hint_max[1])
        self.delete_layout.pos = (self.pos[0] + self.width - (self.delete_button.width / 1.33), self.pos[1] + 13)

        # Reposition highlight border
        self.highlight_layout.pos = self.pos

    def highlight(self):
        def next_frame(*args):
            Animation.stop_all(self.highlight_border)
            self.highlight_border.opacity = 1
            Animation(opacity=0, duration=0.7).start(self.highlight_border)

        Clock.schedule_once(next_frame, 0)

    def __init__(self, properties, click_function=None, enabled=False, fade_in=0.0, highlight=False, **kwargs):
        super().__init__(**kwargs)

        self.anim_duration = 0.06
        self.enabled = enabled
        self.properties = properties
        self.border = (-5, -5, -5, -5)
        self.color_id = [(0.05, 0.05, 0.1, 1), (0.65, 0.65, 1, 1)] if self.enabled else [(0.05, 0.1, 0.1, 1), (1, 0.6, 0.7, 1)]
        self.pos_hint = {"center_x": 0.5, "center_y": 0.6}
        self.size_hint_max = (580, 80)
        self.id = "addon_button"
        self.background_normal = os.path.join(paths.ui_assets, f'{self.id}.png')
        self.background_down = self.background_normal
        self.disabled_banner = None

        # Delete button
        def delete_hover(*args):
            def change_color(*args):
                if self.hovered:
                    self.hover_text.text = 'UNINSTALL ADD-ON'
                    self.background_normal = os.path.join(paths.ui_assets, "server_button_favorite_hover.png")

            Clock.schedule_once(change_color, 0.07)
            Animation.stop_all(self.delete_button)
            Animation(opacity=1, duration=0.25).start(self.delete_button)

        def delete_on_leave(*args):
            def change_color(*args):
                self.hover_text.text = ('DISABLE ADD-ON' if self.enabled else 'ENABLE ADD-ON')
                if self.hovered:
                    self.background_normal = os.path.join(paths.ui_assets, f'{self.id}_hover_{"dis" if self.enabled else "en"}abled.png')
                    self.background_down = self.background_normal

            Clock.schedule_once(change_color, 0.07)
            Animation.stop_all(self.delete_button)
            Animation(opacity=0.65, duration=0.25).start(self.delete_button)

        def delete_click(*args):
            # Delete addon and reload list
            def reprocess_page(*args):
                addon_manager = constants.server_manager.current_server.addon
                addon_manager.delete_addon(self.properties)
                addon_screen = utility.screen_manager.current_screen
                new_list = [addon for addon in addon_manager.return_single_list() if not addons.is_geyser_addon(addon)]
                addon_screen.gen_search_results(new_list, fade_in=True)
                Clock.schedule_once(functools.partial(addon_screen.search_bar.execute_search, addon_screen.search_bar.previous_search), 0)

                # Show banner if server is running
                if addon_manager._hash_changed():
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
                            (1, 0.5, 0.65, 1),
                            f"'${self.properties.name}$' was uninstalled",
                            "trash-sharp.png",
                            2.5,
                            {"center_x": 0.5, "center_y": 0.965}
                        ), 0.25
                    )

                # Switch pages if page is empty
                if (len(addon_screen.scroll_layout.children) == 0) and (len(new_list) > 0):
                    addon_screen.switch_page("left")

            Clock.schedule_once(
                functools.partial(
                    utility.screen_manager.current_screen.show_popup,
                    "warning_query",
                    f'Uninstall ${self.properties.name}$',
                    "Do you want to permanently uninstall this add-on?\n\nYou'll need to re-import or download it again",
                    (None, functools.partial(reprocess_page))
                ),
                0
            )

        self.delete_layout = RelativeLayout(opacity=0)
        self.delete_button = IconButton('', {}, (0, 0), (None, None), 'trash-sharp.png', clickable=True, force_color=[[(0.05, 0.05, 0.1, 1), (0.01, 0.01, 0.01, 1)], 'pink'], anchor='right', click_func=delete_click)
        self.delete_button.opacity = 0.65
        self.delete_button.button.bind(on_enter=delete_hover)
        self.delete_button.button.bind(on_leave=delete_on_leave)
        self.delete_layout.add_widget(self.delete_button)
        self.add_widget(self.delete_layout)

        # Hover text
        self.hover_text = Label()
        self.hover_text.id = 'hover_text'
        self.hover_text.size_hint = (None, None)
        self.hover_text.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        self.hover_text.text = ('DISABLE ADD-ON' if self.enabled else 'ENABLE ADD-ON')
        self.hover_text.font_size = sp(23)
        self.hover_text.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["bold"]}.ttf')
        self.hover_text.color = (0.1, 0.1, 0.1, 1)
        self.hover_text.halign = "center"
        self.hover_text.text_size = (self.size_hint_max[0] * 0.94, self.size_hint_max[1])
        self.hover_text.opacity = 0
        self.add_widget(self.hover_text)

        # Loading stuffs
        self.original_subtitle = self.properties.subtitle if self.properties.subtitle else "Description unavailable"
        self.original_font = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["regular"]}.ttf')

        # Title of Addon
        self.title = Label()
        self.title.__translate__ = False
        self.title.id = "title"
        self.title.halign = "left"
        self.title.color = self.color_id[1]
        self.title.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
        self.title.font_size = sp(25)
        self.title.text_size = (self.size_hint_max[0] * (0.7), self.size_hint_max[1])
        self.title.shorten = True
        self.title.markup = True
        self.title.shorten_from = "right"
        self.title.max_lines = 1
        self.title.text = f"{self.properties.name}  [color=#434368]-[/color]  {self.properties.author if self.properties.author else 'Unknown'}"
        self.add_widget(self.title)
        Clock.schedule_once(self.toggle_enabled, 0)

        # Description of Addon
        self.subtitle = Label()
        self.subtitle.__translate__ = False
        self.subtitle.id = "subtitle"
        self.subtitle.halign = "left"
        self.subtitle.color = self.color_id[1]
        self.subtitle.font_name = self.original_font
        self.subtitle.font_size = sp(21)
        self.default_subtitle_opacity = 0.56
        self.subtitle.opacity = self.default_subtitle_opacity
        self.subtitle.text_size = (self.size_hint_max[0] * 0.91, self.size_hint_max[1])
        self.subtitle.shorten = True
        self.subtitle.shorten_from = "right"
        self.subtitle.max_lines = 1
        self.subtitle.text = self.original_subtitle
        self.add_widget(self.subtitle)

        # Highlight border
        self.highlight_layout = RelativeLayout()
        self.highlight_border = Image()
        self.highlight_border.keep_ratio = False
        self.highlight_border.allow_stretch = True
        self.highlight_border.color = constants.brighten_color(self.color_id[1], 0.1)
        self.highlight_border.opacity = 0
        self.highlight_border.source = os.path.join(paths.ui_assets, 'server_button_highlight.png')
        self.highlight_layout.add_widget(self.highlight_border)
        self.highlight_layout.width = self.size_hint_max[0]
        self.highlight_layout.height = self.size_hint_max[1]
        self.add_widget(self.highlight_layout)

        if highlight:
            self.highlight()

        # If self.enabled is false, and self.properties.version, display version where "enabled" logo is
        self.bind(pos=self.resize_self)
        self.resize_self()

        # If click_function
        if click_function:
            self.bind(on_press=click_function)

        # Animate opacity
        if fade_in > 0:
            self.opacity = 0
            self.title.opacity = 0

            Animation(opacity=1, duration=fade_in).start(self)
            Animation(opacity=1, duration=fade_in).start(self.title)
            Animation(opacity=0.56, duration=fade_in).start(self.subtitle)

    def on_enter(self, *args):
        if not self.ignore_hover:

            # Hide disabled banner if it exists
            if self.disabled_banner:
                Animation.stop_all(self.disabled_banner)
                Animation(opacity=0, duration=self.anim_duration).start(self.disabled_banner)

            # Fade button to hover state
            # if not self.delete_button.button.hovered:
            Animation(color=self.color_id[0], duration=(self.anim_duration * 0.5)).start(self.title)
            Animation(color=self.color_id[0], duration=(self.anim_duration * 0.5)).start(self.subtitle)
            animate_button(self, image=os.path.join(paths.ui_assets, f'{self.id}_hover_{"dis" if self.enabled else "en"}abled.png'), color=self.color_id[0], hover_action=True)

            # Show delete button
            Animation.stop_all(self.delete_layout)
            Animation(opacity=1, duration=self.anim_duration).start(self.delete_layout)

            # Hide text
            Animation(opacity=0, duration=self.anim_duration).start(self.title)
            Animation(opacity=0, duration=self.anim_duration).start(self.subtitle)
            Animation(opacity=1, duration=self.anim_duration).start(self.hover_text)

    def on_leave(self, *args):
        if not self.ignore_hover:

            # Hide disabled banner if it exists
            if self.disabled_banner:
                Animation.stop_all(self.disabled_banner)
                Animation(opacity=1, duration=self.anim_duration).start(self.disabled_banner)

            # Fade button to default state
            # if not self.delete_button.button.hovered:
            Animation(color=self.color_id[1], duration=(self.anim_duration * 0.5)).start(self.title)
            Animation(color=self.color_id[1], duration=(self.anim_duration * 0.5)).start(self.subtitle)
            animate_button(self, image=os.path.join(paths.ui_assets, f'{self.id}{"" if self.enabled else "_disabled"}.png'), color=self.color_id[1], hover_action=False)

            # Hide delete button
            Animation.stop_all(self.delete_layout)
            Animation(opacity=0, duration=self.anim_duration).start(self.delete_layout)

            # Show text
            Animation(opacity=1, duration=self.anim_duration).start(self.title)
            Animation(opacity=self.default_subtitle_opacity, duration=0.13).start(self.subtitle)
            Animation(opacity=0, duration=self.anim_duration).start(self.hover_text)

    def loading(self, load_state, *args):
        if load_state:
            self.subtitle.text = "Loading add-on info..."
            self.subtitle.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
        else:
            self.subtitle.text = self.original_subtitle
            self.subtitle.font_name = self.original_font


class ServerAddonUpdateScreen(ProgressScreen):

    # Only replace this function when making a child screen
    # Set fail message in child functions to trigger an error
    def contents(self):
        server_obj = constants.server_manager.current_server
        icons = os.path.join(paths.ui_assets, 'fonts', constants.fonts['icons'])
        desc_text = "Updating"
        final_text = "Updated"

        def before_func(*args):

            if not constants.app_online:
                self.execute_error("An internet connection is required to continue\n\nVerify connectivity and try again")

            elif not constants.check_free_space(telepath_data=server_obj._telepath_data):
                self.execute_error("Your primary disk is almost full\n\nFree up space and try again")

            else: foundry.pre_addon_update()

        def after_func(*args):
            self.steps.label_2.text = "Updates complete!" + f"   [font={icons}]å[/font]"

            foundry.post_addon_update()

            if server_obj.running:
                Clock.schedule_once(
                    functools.partial(
                        utility.screen_manager.current_screen.show_banner,
                        (0.937, 0.831, 0.62, 1),
                        f"A server restart is required to apply changes",
                        "sync.png",
                        3,
                        {"center_x": 0.5, "center_y": 0.965}
                    ), 1
                )

            else:
                Clock.schedule_once(
                    functools.partial(
                        utility.screen_manager.current_screen.show_banner,
                        (0.553, 0.902, 0.675, 1),
                        f"{final_text} add-ons successfully",
                        "checkmark-circle-sharp.png",
                        3,
                        {"center_x": 0.5, "center_y": 0.965}
                    ), 1
                )

            utility.screen_manager.screen_tree = ['MainMenuScreen', 'ServerManagerScreen']

        # Original is percentage before this function, adjusted is a percent of hooked value
        def adjust_percentage(*args):
            original = self.last_progress
            adjusted = args[0]
            total = args[1] * 0.01
            final = original + round(adjusted * total)
            if final < 0: final = original

            if self.telepath:
                completed_count = addon_count = len(server_obj.addon.return_single_list())
            else:
                addon_count = len(foundry.new_server_info['addon_objects'])
                completed_count = round(len(foundry.new_server_info['addon_objects']) * (final * 0.01))
            self.steps.label_2.text = "Updating Add-ons" + f"   ({completed_count}/{addon_count})"

            self.progress_bar.update_progress(final)

        self.page_contents = {

            # Page name
            'title': f"{desc_text} add-ons",

            # Header text
            'header': "Sit back and relax, it's automation time...",

            # Tuple of tuples for steps (label, function, percent)
            # Percent of all functions must total 100
            # Functions must return True, or default error will be executed
            'default_error': 'There was an issue, please try again later',

            'function_list': (
                (f'{desc_text} Add-ons...',
                 functools.partial(foundry.iter_addons, functools.partial(adjust_percentage, 100), True), 0),
            ),

            # Function to run before steps (like checking for an internet connection)
            'before_function': before_func,

            # Function to run after everything is complete (like cleaning up the screen tree) will only run if no error
            'after_function': after_func,

            # Screen to go to after complete
            'next_screen': 'ServerAddonScreen'
        }


class ServerAddonScreen(MenuBackground):

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

    def gen_search_results(self, results, new_search=False, fade_in=True, highlight=None, animate_scroll=True, last_scroll=None, *args):

        # Update page counter
        # results = list(sorted(results, key=lambda d: d.name.lower()))
        # Set to proper page on toggle

        addon_manager = constants.server_manager.current_server.addon
        default_scroll = 1
        if highlight:
            def divide_chunks(l, n):
                final_list = []

                for i in range(0, len(l), n):
                    final_list.append(l[i:i + n])

                return final_list

            for x, l in enumerate(divide_chunks([x.hash for x in results], self.page_size), 1):
                if highlight in l:
                    if self.current_page != x:
                        self.current_page = x

                    # Update scroll when page is bigger than list
                    if Window.height < self.scroll_layout.height * 1.7:
                        default_scroll = 1 - round(l.index(highlight) / len(l), 2)
                        if default_scroll < 0.21: default_scroll = 0
                        if default_scroll > 0.97: default_scroll = 1
                    break

        self.last_results = results
        self.max_pages = (len(results) / self.page_size).__ceil__()
        self.current_page = 1 if self.current_page == 0 or new_search else self.current_page

        self.page_switcher.update_index(self.current_page, self.max_pages)
        page_list = results[(self.page_size * self.current_page) - self.page_size:self.page_size * self.current_page]

        self.scroll_layout.clear_widgets()

        # Animate scrolling
        def set_scroll(*args):
            Animation.stop_all(self.scroll_layout.parent.parent)
            if animate_scroll:
                Animation(scroll_y=default_scroll, duration=0.1).start(self.scroll_layout.parent.parent)
            else:
                self.scroll_layout.parent.parent.scroll_y = default_scroll

        Clock.schedule_once(set_scroll, 0)

        # Generate header
        addon_count = len(results)
        enabled_count = len([addon for addon in addon_manager.installed_addons['enabled'] if not addons.is_geyser_addon(addon)])
        disabled_count = len(addon_manager.installed_addons['disabled'])
        very_bold_font = os.path.join(paths.ui_assets, 'fonts', constants.fonts["very-bold"])
        header_content = f"{translate('Installed Add-ons')}  [color=#494977]-[/color]  " + (f'[color=#6A6ABA]{translate("No items")}[/color]' if addon_count == 0 else f'[font={very_bold_font}]1[/font] {translate("item")}' if addon_count == 1 else f'[font={very_bold_font}]{enabled_count:,}{("/[color=#FF8793]" + str(disabled_count) + "[/color]") if disabled_count > 0 else ""}[/font] {translate("items")}')

        if addon_manager._hash_changed():
            icons = os.path.join(paths.ui_assets, 'fonts', constants.fonts['icons'])
            header_content = f"[color=#EFD49E][font={icons}]y[/font] " + header_content + "[/color]"

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
                if addons.is_geyser_addon(addon_object):
                    continue

                # Activated when addon is clicked
                def toggle_addon(index, *args):
                    addon = index

                    if len(addon.name) < 26: addon_name = addon.name
                    else:                    addon_name = addon.name[:23] + "..."

                    # Toggle addon state
                    success = addon_manager.addon_state(addon, enabled=not addon.enabled)
                    if not success:
                        Clock.schedule_once(
                            functools.partial(
                                self.show_banner,
                                (0.937, 0.831, 0.62, 1),
                                f"can't disable while the server is running",
                                "alert-circle-sharp.png",
                                3,
                                {"center_x": 0.5, "center_y": 0.965}
                            ), 0
                        )
                        return False
                    addon_list = [addon for addon in addon_manager.return_single_list() if not addons.is_geyser_addon(addon)]
                    self.gen_search_results(addon_list, fade_in=False, highlight=addon.hash, animate_scroll=True)

                    # Show banner if server is running
                    if addon_manager._hash_changed():
                        Clock.schedule_once(
                            functools.partial(
                                self.show_banner,
                                (0.937, 0.831, 0.62, 1),
                                f"A server restart is required to apply changes",
                                "sync.png",
                                3,
                                {"center_x": 0.5, "center_y": 0.965}
                            ), 0
                        )

                    else:
                        if addon.enabled: banner_text = f"'${addon_name}$' is now disabled"
                        else:             banner_text = f"'${addon_name}$' is now enabled"

                        Clock.schedule_once(
                            functools.partial(
                                self.show_banner,
                                (1, 0.5, 0.65, 1) if addon.enabled else (0.553, 0.902, 0.675, 1),
                                banner_text,
                                "close-circle-sharp.png" if addon.enabled else "checkmark-circle-sharp.png",
                                2.5,
                                {"center_x": 0.5, "center_y": 0.965}
                            ), 0
                        )

                # Add-on button click function
                self.scroll_layout.add_widget(
                    ScrollItem(
                        widget = AddonListButton(
                            properties = addon_object,
                            enabled = addon_object.enabled,
                            fade_in = ((x if x <= 8 else 8) / self.anim_speed) if fade_in else 0,
                            highlight = (highlight == addon_object.hash),
                            click_function = functools.partial(
                                toggle_addon,
                                addon_object,
                                x
                            )
                        )
                    )
                )

            self.resize_bind()
            # self.scroll_layout.parent.parent.scroll_y = 1

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'
        self.header = None
        self.scroll_layout = None
        self.blank_label = None
        self.search_bar = None
        self.page_switcher = None
        self.menu_taskbar = None
        self.update_button = None

        self.last_results = []
        self.page_size = 20
        self.current_page = 0
        self.max_pages = 0
        self.anim_speed = 10

        self.server = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        super()._on_keyboard_down(keyboard, keycode, text, modifiers)

        # Press arrow keys to switch pages
        if keycode[1] in ['right', 'left'] and self.name == utility.screen_manager.current_screen.name:
            self.switch_page(keycode[1])

    def generate_menu(self, **kwargs):
        self.server = constants.server_manager.current_server

        # Return if no free space
        if disk_popup('ServerViewScreen', telepath_data=self.server._telepath_data):
            return

        # Scroll list
        scroll_widget = ScrollViewWidget(position=(0.5, 0.5))
        scroll_anchor = AnchorLayout()
        self.scroll_layout = GridLayout(cols=1, spacing=15, size_hint_max_x=1250, size_hint_y=None, padding=[0, 30, 0, 30])

        # Bind / cleanup height on resize
        def resize_scroll(call_widget, grid_layout, anchor_layout, *args):
            call_widget.height = Window.height // 1.85
            grid_layout.cols = 2 if Window.width > grid_layout.size_hint_max_x else 1
            self.anim_speed = 13 if Window.width > grid_layout.size_hint_max_x else 10

            def update_grid(*args):
                anchor_layout.size_hint_min_y = grid_layout.height
                scroll_top.resize(); scroll_bottom.resize()

            Clock.schedule_once(update_grid, 0)

        self.resize_bind = lambda *_: Clock.schedule_once(functools.partial(resize_scroll, scroll_widget, self.scroll_layout, scroll_anchor), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        self.scroll_layout.bind(minimum_height=self.scroll_layout.setter('height'))
        self.scroll_layout.id = 'scroll_content'

        # Scroll gradient
        scroll_top = ScrollBackground(pos_hint={"center_x": 0.5, "center_y": 0.775}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, 60))
        scroll_bottom = ScrollBackground(pos_hint={"center_x": 0.5, "center_y": 0.25}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, -60))

        # Generate buttons on page load
        addon_count = len(self.server.addon.return_single_list())
        very_bold_font = os.path.join(paths.ui_assets, 'fonts', constants.fonts["very-bold"])
        header_content = f"{translate('Installed Add-ons')}  [color=#494977]-[/color]  " + (f'[color=#6A6ABA]{translate("No items")}[/color]' if addon_count == 0 else f'[font={very_bold_font}]1[/font] {translate("item")}' if addon_count == 1 else f'[font={very_bold_font}]{addon_count}[/font] {translate("items")}')
        self.header = HeaderText(header_content, '', (0, 0.9), __translate__=(False, True), no_line=True)

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

        search_function = self.server.addon.filter_addons
        self.search_bar = SearchBar(return_function=search_function, server_info=None, pos_hint={"center_x": 0.5, "center_y": 0.845}, allow_empty=True)
        self.page_switcher = PageSwitcher(0, 0, (0.5, 0.86), self.switch_page)

        # Append scroll view items
        scroll_anchor.add_widget(self.scroll_layout)
        scroll_widget.add_widget(scroll_anchor)
        float_layout.add_widget(scroll_widget)
        float_layout.add_widget(scroll_top)
        float_layout.add_widget(scroll_bottom)
        float_layout.add_widget(self.search_bar)
        float_layout.add_widget(self.page_switcher)

        bottom_buttons = RelativeLayout()
        bottom_buttons.size_hint_max_x = 312
        bottom_buttons.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        bottom_buttons.add_widget(MainButton('Import', (0, 0.202), 'download-outline.png', width=300, icon_offset=-115, auto_adjust_icon=True))
        bottom_buttons.add_widget(MainButton('Download', (1, 0.202), 'cloud-download-outline.png', width=300, icon_offset=-115, auto_adjust_icon=True))
        buttons.append(ExitButton('Back', (0.5, -1), cycle=True))

        for button in buttons: float_layout.add_widget(button)
        float_layout.add_widget(bottom_buttons)

        menu_name = f"{self.server.name}, Add-ons"
        float_layout.add_widget(generate_title(f"Add-on Manager: '{self.server.name}'"))
        float_layout.add_widget(generate_footer(menu_name))

        # Buttons in the top right corner
        def update_addons(*a): utility.screen_manager.current = 'ServerAddonUpdateScreen'

        if addon_count > 0:
            position = (70 if self.server._telepath_data else 125, 110)
            vertical_offset = 0 if self.server._telepath_data else 50
            if not self.server.addon.update_required:
                self.server._view_notif('add-ons', False)
                float_layout.add_widget(IconButton('up to date', {}, position, (None, None), 'checkmark-sharp.png', clickable=False, anchor='right', click_func=update_addons, text_offset=(0, vertical_offset)))
            else:
                self.server._view_notif('add-ons', viewed='update')
                float_layout.add_widget(IconButton('update add-ons', {}, position, (None, None), 'arrow-update.png', clickable=True, anchor='right', click_func=update_addons, force_color=[[(0.05, 0.08, 0.07, 1), (0.5, 0.9, 0.7, 1)], 'green'], text_offset=(12, vertical_offset)))

        if not self.server._telepath_data:
            def open_dir(*a):
                constants.folder_check(self.server.addon.addon_path)
                open_folder(self.server.addon.addon_path)

            float_layout.add_widget(IconButton('open directory', {}, (70, 110), (None, None), 'folder.png', anchor='right', click_func=open_dir, text_offset=(10, 0)))

        self.add_widget(float_layout)

        # Add ManuTaskbar
        self.menu_taskbar = MenuTaskbar(selected_item='add-ons')
        self.add_widget(self.menu_taskbar)

        # Automatically generate results (installed add-ons) on page load
        addon_manager = constants.server_manager.current_server.addon
        addon_list = [addon for addon in addon_manager.return_single_list() if not addons.is_geyser_addon(addon)]

        self.gen_search_results(addon_list)

        # Show banner if server is running
        if addon_manager._hash_changed():
            Clock.schedule_once(
                functools.partial(
                    self.show_banner,
                    (0.937, 0.831, 0.62, 1),
                    f"A server restart is required to apply changes",
                    "sync.png",
                    3,
                    {"center_x": 0.5, "center_y": 0.965}
                ), 0
            )

        # Show banner if updates are available
        elif constants.server_manager.current_server.addon.update_required and not constants.server_manager.current_server.addon._update_notified:
            constants.server_manager.current_server.addon._update_notified = True
            Clock.schedule_once(
                functools.partial(
                    self.show_banner,
                    (0.553, 0.902, 0.675, 1),
                    f"Add-on updates are available",
                    "arrow-up-circle-sharp.png",
                    2.5,
                    {"center_x": 0.5, "center_y": 0.965},
                    'popup/notification'
                ), 0
            )


class ServerAddonSearchScreen(MenuBackground):

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
        addon_manager = constants.server_manager.current_server.addon

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
                installed_addon_names = [addon.name for addon in addon_manager.return_single_list()]

                # Clear and add all addons
                for x, addon_object in enumerate(page_list, 1):

                    # Function to download addon info
                    def load_addon(addon, index):
                        try:
                            selected_button = [item for item in self.scroll_layout.walk() if item.__class__.__name__ == "AddonButton"][index - 1]

                            # Cache updated addon info into button, or skip if it's already cached
                            if selected_button.properties:
                                if not selected_button.properties.versions or not selected_button.properties.description:
                                    new_addon_info = addons.get_addon_info(addon, constants.server_manager.current_server.properties_dict())
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

                        selected_button = [item for item in self.scroll_layout.walk() if item.__class__.__name__ == "AddonButton"][index - 1]
                        addon = selected_button.properties
                        selected_button.toggle_installed(not selected_button.installed)

                        if len(addon.name) < 26: addon_name = addon.name
                        else:                    addon_name = addon.name[:23] + "..."

                        # Install
                        if selected_button.installed:
                            dTimer(0, functools.partial(addon_manager.download_addon, addon)).start()

                            # Show banner if server is running
                            if addon_manager._hash_changed():
                                Clock.schedule_once(
                                    functools.partial(
                                        self.show_banner,
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
                                        self.show_banner,
                                        (0.553, 0.902, 0.675, 1),
                                        f"Installed '${addon_name}$'",
                                        "checkmark-circle-sharp.png",
                                        2.5,
                                        {"center_x": 0.5, "center_y": 0.965}
                                    ), 0.25
                                )

                        # Uninstall
                        else:
                            for installed_addon in addon_manager.return_single_list():
                                if installed_addon.name == addon.name:
                                    addon_manager.delete_addon(installed_addon)

                                    # Show banner if server is running
                                    if addon_manager._hash_changed():
                                        Clock.schedule_once(
                                            functools.partial(
                                                self.show_banner,
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
                                                self.show_banner,
                                                (1, 0.5, 0.65, 1),
                                                f"'${addon_name}$' was uninstalled",
                                                "trash-sharp.png",
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
                scroll_top.resize(); scroll_bottom.resize()

            Clock.schedule_once(update_grid, 0)

        self.resize_bind = lambda *_: Clock.schedule_once(functools.partial(resize_scroll, scroll_widget, self.scroll_layout, scroll_anchor), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        self.scroll_layout.bind(minimum_height=self.scroll_layout.setter('height'))
        self.scroll_layout.id = 'scroll_content'

        # Scroll gradient
        scroll_top = ScrollBackground(pos_hint={"center_x": 0.5, "center_y": 0.715}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, 60))
        scroll_bottom = ScrollBackground(pos_hint={"center_x": 0.5, "center_y": 0.17}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, -60))

        # Generate buttons on page load
        addon_count = 0
        very_bold_font = os.path.join(paths.ui_assets, 'fonts', constants.fonts["very-bold"])
        header_content = translate("Add-on Search")
        self.header = HeaderText(header_content, '', (0, 0.89), __translate__=(False, True))

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

        server_obj = constants.server_manager.current_server
        search_function = server_obj.addon.search_addons
        self.search_bar = SearchBar(return_function=search_function, server_info=server_obj.properties_dict(), pos_hint={"center_x": 0.5, "center_y": 0.795})
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

        for button in buttons: float_layout.add_widget(button)

        server_name = constants.server_manager.current_server.name
        menu_name = f"{server_name}, Add-ons, Download"
        float_layout.add_widget(generate_title(f"Add-on Manager: '{server_name}'"))
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
