from source.ui.desktop.views.server.manager.components import *



# Create Server Step 6:  Add-on Options --------------------------------------------------------------------------------

class CreateServerAddonScreen(ListManageLayout, MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.animate_results = False

    def prepare_list_results(self, results):
        return list(sorted(results, key=lambda item: item.name.lower()))

    def generate_list_header(self, results):
        count = len(results)
        very_bold_font = os.path.join(paths.ui_assets, 'fonts', constants.fonts["very-bold"])

        count_text = (
            f'[color=#6A6ABA]{translate("No items")}[/color]'
            if count == 0

            else
            f'[font={very_bold_font}]1[/font] {translate("item")}'
            if count == 1

            else
            f'[font={very_bold_font}]{count:,}[/font] {translate("items")}'
        )

        return f"{translate('Add-on Queue')}  [color=#494977]-[/color]  {count_text}"

    def remove_addon(self, addon, *args):
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
            ),
            0.25
        )

        addon_manager = foundry.new_server_info['addon_object']

        if addon_manager.delete_addon(addon):
            addon_list = addon_manager.return_single_list()
            self.gen_search_results(addon_list)

            if len(self.scroll_layout.children) == 0 and len(addon_list) > 0:
                self.switch_page("left")

        return addon, True

    def import_files(self, files=None, *args):
        if files is None:
            title = "Select Add-on Files (.jar)"
            files = file_popup("file", start_dir=paths.user_downloads, ext=["*.jar"], select_multiple=True, title=title)

        if not files:
            return

        banner_text = ''
        addon_manager = foundry.new_server_info['addon_object']

        for addon in files:
            if addon.endswith(".jar") and os.path.isfile(addon):
                addon = addons.get_addon_file(addon, foundry.new_server_info)
                addon_manager.add_addon(addon)
                addon_list = addon_manager.return_single_list()
                self.gen_search_results(addon_list)

                # Switch pages if page is full
                if (len(self.scroll_layout.children) == 0) and (len(addon_list) > 0):
                    self.switch_page("right")

                # Show banner
                if len(files) == 1:
                    if len(addon.name) < 26:
                        addon_name = addon.name
                    else:
                        addon_name = addon.name[:23] + "..."
                    banner_text = f"Added '${addon_name}$' to the queue"

                else:
                    banner_text = f"Added ${len(files)}$ add-ons to the queue"

        if banner_text:
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

    def generate_list_button(self, addon, index, fade_in, highlight):

        def primary_action(*args):
            pass

        def remove_action(*args):
            Clock.schedule_once(
                functools.partial(
                    self.show_popup,
                    "query",
                    addon.name,
                    "Do you want to remove this add-on from the queue?",
                    (None, functools.partial(self.remove_addon, addon))
                ),
                0
            )

        actions = [
            (
                "remove",
                "remove-circle-sharp.png",
                remove_action,
                {"force_color": [[(0.05, 0.05, 0.1, 1), (0.6, 0.6, 1, 1)], "pink"]}
            )
        ]

        banner = BannerObject(
            pos_hint = {"center_x": 0.5, "center_y": 0.5},
            size = (
                125
                if addon.addon_object_type == "web"
                else 100,
                32
            ),
            color = (
                (0.647, 0.839, 0.969, 1)
                if addon.addon_object_type == "web"
                else (0.6, 0.6, 1, 1)
            ),
            text = (
                "download"
                if addon.addon_object_type == "web"
                else "import"
            ),
            icon = (
                "cloud-download-sharp.png"
                if addon.addon_object_type == "web"
                else "download.png"
            ),
            icon_side = "right"
        )

        return ListButton(
            properties = addon,
            installed = True,
            banner = banner,
            actions = actions,
            fade_in = fade_in,
            click_function = primary_action
        )

    def generate_menu(self, **kwargs):
        addon_manager = foundry.new_server_info['addon_object']

        # Generate buttons on page load
        addon_count = len(addon_manager.return_single_list())
        very_bold_font = os.path.join(paths.ui_assets, 'fonts', constants.fonts["very-bold"])
        header_content = f"{translate('Add-on Queue')}  [color=#494977]-[/color]  " + (f'[color=#6A6ABA]{translate("No items")}[/color]' if addon_count == 0 else f'[font={very_bold_font}]1[/font] {translate("item")}' if addon_count == 1 else f'[font={very_bold_font}]{addon_count:,}[/font] {translate("items")}')
        self.generate_list(header_content, "Import or Download add-ons below", addon_manager.filter_addons, allow_empty=True)

        buttons = []
        float_layout = self._layout

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

        # Automatically generate results on page load
        self.gen_search_results(addon_manager.return_single_list())


class CreateServerAddonSearchScreen(ListSearchLayout, MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.installed_names = []

    def before_list_render(self, results):
        addon_manager = foundry.new_server_info['addon_object']
        self.installed_names = [addon.name for addon in addon_manager.return_single_list()]

    def generate_list_button(self, addon, index, fade_in, highlight):
        addon_manager = foundry.new_server_info['addon_object']

        def load_addon(*args):
            try:
                selected_button = self.get_list_button(index)
                if selected_button.properties:
                    if not selected_button.properties.versions or not selected_button.properties.description:
                        selected_button.properties = (addon_manager.get_addon_info(addon))

                Clock.schedule_once(functools.partial(selected_button.loading, False), 1)
                return (selected_button.properties, selected_button.installed)

            except:
                Clock.schedule_once(
                    functools.partial(
                        self.show_banner,
                        (1, 0.5, 0.65, 1),
                        "Failed to load add-on",
                        "close-circle-sharp.png",
                        2.5,
                        {"center_x": 0.5, "center_y": 0.965}
                    ),
                    0
                )

        def install_addon(*args):
            selected_button = self.get_list_button(index)
            addon_object = selected_button.properties

            selected_button.toggle_installed(not selected_button.installed)

            if len(addon_object.name) < 26: addon_name = addon_object.name
            else:                           addon_name = addon_object.name[:23] + "..."

            if selected_button.installed:
                addon_manager.add_addon(addon_manager.get_addon_url(addon_object))

                Clock.schedule_once(
                    functools.partial(
                        self.show_banner,
                        (0.553, 0.902, 0.675, 1),
                        f"Added '${addon_name}$' to the queue",
                        "add-circle-sharp.png",
                        2.5,
                        {"center_x": 0.5, "center_y": 0.965}
                    ),
                    0.25
                )

            else:
                for installed_addon in addon_manager.return_single_list():
                    if installed_addon.name == addon_object.name:
                        addon_manager.delete_addon(installed_addon)

                        Clock.schedule_once(
                            functools.partial(
                                self.show_banner,
                                (0.937, 0.831, 0.62, 1),
                                f"Removed '${addon_name}$' from the queue",
                                "remove-circle-sharp.png",
                                2.5,
                                {"center_x": 0.5, "center_y": 0.965}
                            ),
                            0.25
                        )
                        break

            return addon_object, selected_button.installed

        def view_addon(*args):
            selected_button = self.get_list_button(index)
            selected_button.loading(True)

            Clock.schedule_once(
                functools.partial(
                    self.show_popup,
                    "addon",
                    " ",
                    " ",
                    (None, functools.partial(install_addon)),
                    functools.partial(load_addon)
                ),
                0
            )

        return ListButton(
            properties = addon,
            installed = addon.name in self.installed_names,
            fade_in = fade_in,
            click_function = view_addon
        )

    def generate_menu(self, **kwargs):
        addon_manager = foundry.new_server_info['addon_object']
        self.generate_list(
            translate("Add-on Search"),
            "search for add-ons above",
            addon_manager.search_addons,
            empty_text = "there are no items to display"
        )

        buttons = []
        float_layout = self._layout

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
                addon_list = foundry.new_server_info['addon_object'].addon_queue
                addon_count = len(addon_list)
                completed_count = round(len(addon_list) * (final * 0.01))
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
                 functools.partial(foundry.write_addons, functools.partial(adjust_percentage, 100), True), 0),
            ),

            # Function to run before steps (like checking for an internet connection)
            'before_function': before_func,

            # Function to run after everything is complete (like cleaning up the screen tree) will only run if no error
            'after_function': after_func,

            # Screen to go to after complete
            'next_screen': 'ServerAddonScreen'
        }


class ServerAddonScreen(ListManageLayout, MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.menu_taskbar = None
        self.update_button = None
        self.server = None

    def import_files(self, files=None, *args):
        if files is None:
            title = "Select Add-on Files (.jar)"
            files = file_popup("file", start_dir=paths.user_downloads, ext=["*.jar"], select_multiple=True, title=title)

        if not files:
            return

        addon_manager = constants.server_manager.current_server.addon
        banner_text = ''

        for addon in files:
            if addon.endswith(".jar") and os.path.isfile(addon):
                addon = addon_manager.import_addon(addon)
                if not addon:
                    continue

                addon_list = addon_manager.return_single_list()
                self.gen_search_results(addon_list, fade_in=False, highlight=addon.hash, animate_scroll=True)

                # Switch pages if page is full
                if (len(self.scroll_layout.children) == 0) and (len(addon_list) > 0):
                    self.switch_page("right")

                # Show banner
                if len(files) == 1:
                    if len(addon.name) < 26:
                        addon_name = addon.name
                    else:
                        addon_name = addon.name[:23] + "..."
                    banner_text = f"Imported '${addon_name}$'"

                else:
                    banner_text = f"Imported ${len(files)}$ add-ons"

        if banner_text:

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
                        banner_text,
                        "add-circle-sharp.png",
                        2.5,
                        {"center_x": 0.5, "center_y": 0.965}
                    ), 0
                )

    def generate_list_header(self, results):
        addon_manager = self.server.addon
        addon_count = len(results)

        enabled_count = len([
            addon for addon in addon_manager.installed_addons['enabled']
            if not addons.is_geyser_addon(addon)
        ])
        disabled_count = len(addon_manager.installed_addons['disabled'])
        very_bold_font = os.path.join(paths.ui_assets, 'fonts', constants.fonts["very-bold"])

        header_content = f"{translate('Installed Add-ons')}  [color=#494977]-[/color]  "
        if addon_count == 0:
            header_content += f'[color=#6A6ABA]{translate("No items")}[/color]'

        elif addon_count == 1:
            header_content += f'[font={very_bold_font}]1[/font] {translate("item")}'

        else:
            disabled_text = (
                f'/[color=#FF8793]{disabled_count}[/color]'
                if disabled_count > 0
                else ''
            )
            header_content += f'[font={very_bold_font}]{enabled_count:,}{disabled_text}[/font] {translate("items")}'

        if addon_manager._hash_changed():
            icons = os.path.join(paths.ui_assets, 'fonts', constants.fonts['icons'])
            header_content = f"[color=#EFD49E][font={icons}]y[/font] {header_content}[/color]"

        return header_content

    def toggle_addon(self, addon, *args):
        addon_manager = self.server.addon

        if len(addon.name) < 26: addon_name = addon.name
        else:                    addon_name = addon.name[:23] + "..."

        success = addon_manager.addon_state(addon, enabled=not addon.enabled)

        if not success:
            Clock.schedule_once(
                functools.partial(
                    self.show_banner,
                    (0.937, 0.831, 0.62, 1),
                    "can't disable while the server is running",
                    "alert-circle-sharp.png",
                    3,
                    {"center_x": 0.5, "center_y": 0.965}
                ),
                0
            )
            return False

        addon_list = [
            item for item in addon_manager.return_single_list()
            if not addons.is_geyser_addon(item)
        ]

        self.gen_search_results(addon_list, fade_in=False, highlight=addon.hash, animate_scroll=True)

        if addon_manager._hash_changed():
            Clock.schedule_once(
                functools.partial(
                    self.show_banner,
                    (0.937, 0.831, 0.62, 1),
                    "A server restart is required to apply changes",
                    "sync.png",
                    3,
                    {"center_x": 0.5, "center_y": 0.965}
                ),
                0
            )

        else:
            if addon.enabled: banner_text = f"'${addon_name}$' is now disabled"
            else:             banner_text = f"'${addon_name}$' is now enabled"

            Clock.schedule_once(
                functools.partial(
                    self.show_banner,
                    (1, 0.5, 0.65, 1)
                    if addon.enabled
                    else (0.553, 0.902, 0.675, 1),

                    banner_text,

                    "close-circle-sharp.png"
                    if addon.enabled
                    else "checkmark-circle-sharp.png",

                    2.5,
                    {"center_x": 0.5, "center_y": 0.965}
                ),
                0
            )

    def delete_addon(self, addon, *args):

        def reprocess_page(*args):
            addon_manager = self.server.addon
            addon_manager.delete_addon(addon)

            new_list = [
                item for item in addon_manager.return_single_list()
                if not addons.is_geyser_addon(item)
            ]

            self.gen_search_results(new_list, fade_in=True)
            Clock.schedule_once(functools.partial(self.search_bar.execute_search, self.search_bar.previous_search), 0)

            if addon_manager._hash_changed():
                Clock.schedule_once(
                    functools.partial(
                        self.show_banner,
                        (0.937, 0.831, 0.62, 1),
                        "A server restart is required to apply changes",
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
                        f"'${addon.name}$' was uninstalled",
                        "trash-sharp.png",
                        2.5,
                        {"center_x": 0.5, "center_y": 0.965}
                    ),
                    0.25
                )

            if len(self.scroll_layout.children) == 0 and len(new_list) > 0:
                self.switch_page("left")

        Clock.schedule_once(
            functools.partial(
                self.show_popup,
                "warning_query",
                f'Uninstall ${addon.name}$',
                "Do you want to permanently uninstall this add-on?\n\nYou'll need to re-import or download it again",
                (None, functools.partial(reprocess_page))
            ),
            0
        )

    def prepare_list_results(self, results):
        return list(sorted(results, key=lambda addon: (not addon.enabled, addon.name.lower())))

    def update_addon_item(self, addon, *args):
        addon_manager = self.server.addon

        def update():
            updated = addon_manager.update_addon(addon)

            def finish(*args):
                if not updated:
                    self.show_banner(
                        (0.937, 0.831, 0.62, 1),
                        f"No compatible update was found for '${addon.name}$'",
                        "alert-circle-sharp.png",
                        2.5,
                        {"center_x": 0.5, "center_y": 0.965}
                    )
                    return

                addon_list = [
                    item for item in addon_manager.return_single_list()
                    if not addons.is_geyser_addon(item)
                ]

                self.gen_search_results(addon_list, fade_in=False, highlight=updated.hash,animate_scroll=True)

                if addon_manager._hash_changed():
                    self.show_banner(
                        (0.937, 0.831, 0.62, 1),
                        "A server restart is required to apply changes",
                        "sync.png",
                        3,
                        {"center_x": 0.5, "center_y": 0.965}
                    )
                else:
                    self.show_banner(
                        (0.553, 0.902, 0.675, 1),
                        f"Updated '${addon.name}$'",
                        "checkmark-circle-sharp.png",
                        2.5,
                        {"center_x": 0.5, "center_y": 0.965}
                    )

            Clock.schedule_once(finish, 0)

        dTimer(0, update).start()

    def generate_list_button(self, addon, index, fade_in, highlight):

        def primary_action(*args):
            pass

        toggle_options = (
            {"force_color": [[(0.05, 0.05, 0.1, 1), (0.6, 0.6, 1, 1)], "pink"]}
            if addon.enabled else
            {"force_color": [[(0.05, 0.08, 0.07, 1), (0.6, 0.6, 1, 1)], "green"]}
        )

        actions = [
            (
                "disable" if addon.enabled else "enable",
                "close-circle-sharp.png" if addon.enabled else "checkmark-circle-sharp.png",
                functools.partial(self.toggle_addon, addon),
                toggle_options
            ),
            (
                "update",
                "sync.png",
                functools.partial(self.update_addon_item, addon)
            ),
            (
                "delete",
                "trash-sharp.png",
                functools.partial(self.delete_addon, addon),
                {"force_color": [[(0.05, 0.05, 0.1, 1), (0.6, 0.6, 1, 1)], "pink"]}
            )
        ]

        return ListButton(
            properties = addon,
            enabled = addon.enabled,
            actions = actions,
            fade_in = fade_in,
            highlight = highlight,
            click_function = primary_action
        )

    def generate_menu(self, **kwargs):
        self.server = constants.server_manager.current_server

        # Return if no free space
        if disk_popup('ServerViewScreen', telepath_data=self.server._telepath_data):
            return

        # Generate buttons on page load
        addon_count = len(self.server.addon.return_single_list())
        very_bold_font = os.path.join(paths.ui_assets, 'fonts', constants.fonts["very-bold"])
        header_content = f"{translate('Installed Add-ons')}  [color=#494977]-[/color]  " + (f'[color=#6A6ABA]{translate("No items")}[/color]' if addon_count == 0 else f'[font={very_bold_font}]1[/font] {translate("item")}' if addon_count == 1 else f'[font={very_bold_font}]{addon_count}[/font] {translate("items")}')
        self.generate_list(header_content, "Import or Download add-ons below", self.server.addon.filter_addons, allow_empty=True)

        buttons = []
        float_layout = self._layout

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


class ServerAddonSearchScreen(ListSearchLayout, MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.installed_names = []

    def before_list_render(self, results):
        addon_manager = constants.server_manager.current_server.addon
        self.installed_names = [addon.name for addon in addon_manager.return_single_list()]

    def generate_list_button(self, addon, index, fade_in, highlight):
        addon_manager = constants.server_manager.current_server.addon

        def load_addon(*args):
            try:
                selected_button = self.get_list_button(index)
                if selected_button.properties:
                    if not selected_button.properties.versions or not selected_button.properties.description:
                        selected_button.properties = addon_manager.get_addon_info(addon)

                Clock.schedule_once(functools.partial(selected_button.loading, False), 1)
                return (selected_button.properties, selected_button.installed)

            except:
                Clock.schedule_once(
                    functools.partial(
                        self.show_banner,
                        (1, 0.5, 0.65, 1),
                        "Failed to load add-on",
                        "close-circle-sharp.png",
                        2.5,
                        {"center_x": 0.5, "center_y": 0.965}
                    ),
                    0
                )

        def install_addon(*args):
            selected_button = self.get_list_button(index)
            addon_object = selected_button.properties
            selected_button.toggle_installed(not selected_button.installed)

            if len(addon_object.name) < 26: addon_name = addon_object.name
            else:                           addon_name = addon_object.name[:23] + "..."

            if selected_button.installed:
                dTimer(0, functools.partial(addon_manager.download_addon, addon_object)).start()

                if addon_manager._hash_changed():
                    Clock.schedule_once(
                        functools.partial(
                            self.show_banner,
                            (0.937, 0.831, 0.62, 1),
                            "A server restart is required to apply changes",
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
                            (0.553, 0.902, 0.675, 1),
                            f"Installed '${addon_name}$'",
                            "checkmark-circle-sharp.png",
                            2.5,
                            {"center_x": 0.5, "center_y": 0.965}
                        ),
                        0.25
                    )

            else:
                for installed_addon in addon_manager.return_single_list():
                    if installed_addon.name == addon_object.name:
                        addon_manager.delete_addon(installed_addon)

                        if addon_manager._hash_changed():
                            Clock.schedule_once(
                                functools.partial(
                                    self.show_banner,
                                    (0.937, 0.831, 0.62, 1),
                                    "A server restart is required to apply changes",
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
                                    f"'${addon_name}$' was uninstalled",
                                    "trash-sharp.png",
                                    2.5,
                                    {"center_x": 0.5, "center_y": 0.965}
                                ),
                                0.25
                            )
                        break

            return addon_object, selected_button.installed

        def view_addon(*args):
            selected_button = self.get_list_button(index)
            selected_button.loading(True)

            Clock.schedule_once(
                functools.partial(
                    self.show_popup,
                    "addon",
                    " ",
                    " ",
                    (None, functools.partial(install_addon)),
                    functools.partial(load_addon)
                ),
                0
            )

        return ListButton(
            properties = addon,
            installed = addon.name in self.installed_names,
            fade_in = fade_in,
            click_function = view_addon
        )

    def generate_menu(self, **kwargs):
        server_obj = constants.server_manager.current_server
        self.generate_list(
            translate("Add-on Search"),
            "search for add-ons above",
            server_obj.addon.search_addons,
            server_info = server_obj.properties_dict(),
            empty_text = "there are no items to display"
        )

        buttons = []
        float_layout = self._layout

        buttons.append(ExitButton('Back', (0.5, 0.12), cycle=True))

        for button in buttons: float_layout.add_widget(button)

        server_name = server_obj.name
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
