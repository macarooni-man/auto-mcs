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

    def remove_all(self, *args):

        def _remove(*args):
            addon_manager = foundry.new_server_info['addon_object']

            for addon in addon_manager.return_single_list():
                addon_manager.delete_addon(addon)

            self.gen_search_results(addon_manager.return_single_list())

        if foundry.new_server_info['addon_object'].return_single_list():
            Clock.schedule_once(
                functools.partial(
                    self.show_popup,
                    "warning_query",
                    "Remove All Add-ons",
                    "Do you want to remove every add-on from the queue?",
                    (None, functools.partial(_remove))
                ),
                0
            )

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
            version = addon.addon_version or "Unknown"
            details = (
                (
                    f"Version:  {version}\n"
                    f"Filename:  {os.path.basename(addon.path) if addon.path else 'Unknown'}\n"
                    f"Author:  {addon.author or 'Unknown'}\n"
                    f"Project ID:  {addon.id or 'Unknown'}\n"
                    f"Type:  {addon.type or 'Unknown'}"
                )
                if addon.addon_object_type == "file" else
                (
                    f"Version:  {version}\n"
                    f"Provider:  {addon.provider or 'Unknown'}\n"
                    f"Author:  {addon.author or 'Unknown'}\n"
                    f"Project ID:  {addon.id or 'Unknown'}\n"
                    f"Type:  {addon.type or 'Unknown'}"
                )
            )

            Clock.schedule_once(
                functools.partial(
                    self.show_popup,
                    "info",
                    f'{addon.name} - Details',
                    details,
                    None,
                    None,
                    silent = True,
                ), 0
            )

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
        actions = [RelativeIconButton('\n\n\nremove all', {"center_x": 0.5, "center_y": 0.5}, None, (None, None), 'trash-sharp.png', click_func=self.remove_all, force_color=[[(0.05, 0.05, 0.1, 1), (0.6, 0.6, 1, 1)], 'pink'])]
        self.generate_list(header_content, "Import or Download add-ons below", addon_manager.filter_addons, allow_empty=True, actions=actions)

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

class ServerAddonScreen(ListManageLayout, MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.menu_taskbar = None
        self.update_button = None
        self.server = None

        self.active_updates = set()
        self._watching_updates = None

    def refresh_list(self, *args):
        last_scroll = self.scroll_layout.parent.parent.scroll_y
        search = self.search_bar.previous_search

        if search: addon_list = self.server.addon.filter_addons(search)
        else:      addon_list = self.server.addon.return_single_list()

        self.gen_search_results(addon_list, fade_in=False, animate_scroll=False, last_scroll=last_scroll)
        self.refresh_update_button()

    def before_list_render(self, results):
        try:    self.active_updates = set(self.server.addon._sync_attr('active_updates'))
        except: self.active_updates = set()

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

        enabled_count = len([addon for addon in results if addon.enabled])
        disabled_count = len([addon for addon in results if not addon.enabled])
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

        addon_list = addon_manager.return_single_list()
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

    def toggle_all(self, enabled, *args):
        addon_manager = self.server.addon

        for addon in addon_manager.return_single_list():
            if addon.enabled != enabled:
                addon_manager.addon_state(addon, enabled=enabled)

        self.refresh_list()

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

    def delete_addon(self, addon, *args):

        def reprocess_page(*args):
            addon_manager = self.server.addon
            addon_manager.delete_addon(addon)

            new_list = addon_manager.return_single_list()
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

    def update_all_addons(self, *args):
        addon_manager = self.server.addon

        for button in self.list_buttons:
            if button.properties.update.get('url'):
                button.loading(True, False)

        def _update():
            addon_manager.update_all()
            addon_manager.check_for_updates()

            def _finish(*args):
                try:
                    if utility.screen_manager.current == self.name:
                        self.refresh_list()
                except: pass

            Clock.schedule_once(_finish, 0)

        dTimer(0, _update).start()

    def prepare_list_results(self, results):
        return list(sorted(results, key=lambda addon: (not addon.enabled, addon.name.lower())))

    def update_addon_item(self, addon, index, *args):
        addon_manager = self.server.addon

        try: self.get_list_button(index).loading(True, False)
        except: pass

        def _update():
            updated = addon_manager.update_addon(addon)

            # Refresh update metadata after the filesystem refresh
            addon_manager.check_for_updates()

            def _finish(*args):
                try:
                    if utility.screen_manager.current != self.name:
                        return

                    self.refresh_list()

                    if not updated:
                        self.show_banner(
                            (0.937, 0.831, 0.62, 1),
                            f"No compatible update was found for '${addon.name}$'",
                            "alert-circle-sharp.png",
                            2.5,
                            {"center_x": 0.5, "center_y": 0.965}
                        )
                        return

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

                except:
                    pass

            Clock.schedule_once(_finish, 0)

        dTimer(0, _update).start()

    def refresh_update_button(self, *args):
        if self.server.addon._server['is_modpack']:
            return

        if not self.update_button or not self.action_layout:
            return

        updates_available = bool(self.server.addon.get_update_list())
        self.action_layout.remove_widget(self.update_button)

        if updates_available:
            self.update_button = RelativeIconButton(
                '\n\n\nupdate all',
                {"center_x": 0.5, "center_y": 0.5},
                None,
                (None, None),
                'arrow-update.png',
                click_func = self.update_all_addons,
                force_color = [[(0.05, 0.08, 0.07, 1), (0.5, 0.9, 0.7, 1)], 'green']
            )

        else:
            self.update_button = RelativeIconButton(
                '\n\n\nup to date',
                {"center_x": 0.5, "center_y": 0.5},
                None,
                (None, None),
                'checkmark-sharp.png',
                clickable = False
            )

        self.update_button.size_hint = (None, None)
        self.update_button.size = (55, 80)
        self.action_layout.add_widget(self.update_button)

    def generate_list_button(self, addon, index, fade_in, highlight):
        is_modpack = self.server.addon._server['is_modpack']

        def primary_action(*args):
            version = addon.addon_version or "Unknown"
            file_name = os.path.basename(addon.path) if addon.path else "Unknown"

            Clock.schedule_once(
                functools.partial(
                    self.show_popup,
                    "info",
                    f'{addon.name} - Details',
                    f"Version:  {version}\n"
                    f"Filename:  {file_name}\n"
                    f"Author:  {addon.author or 'Unknown'}\n"
                    f"Project ID:  {addon.id or 'Unknown'}\n"
                    f"Type:  {addon.type or 'Unknown'}",
                    None,
                    None,
                    silent = True,
                ), 0
            )

        toggle_options = (
            {"force_color": [[(0.05, 0.05, 0.1, 1), (0.6, 0.6, 1, 1)], "pink"]}
            if addon.enabled else
            {"force_color": [[(0.05, 0.08, 0.07, 1), (0.6, 0.6, 1, 1)], "green"]}
        )

        update_action = (
            (
                "update",
                "arrow-update.png",
                functools.partial(self.update_addon_item, addon, index),
                {"force_color": [[(0.05, 0.08, 0.07, 1), (0.5, 0.9, 0.7, 1)], "green"]}
            )
            if addon.update.get('url') else
            (
                "up to date",
                "checkmark-sharp.png",
                None
            )
        )

        actions = [
            (
                "disable" if addon.enabled else "enable",
                "close-circle-sharp.png" if addon.enabled else "checkmark-circle-sharp.png",
                functools.partial(self.toggle_addon, addon),
                toggle_options
            ),
            (
                "delete",
                "trash-sharp.png",
                functools.partial(self.delete_addon, addon),
                {"force_color": [[(0.05, 0.05, 0.1, 1), (0.6, 0.6, 1, 1)], "pink"]}
            )
        ]

        if not is_modpack: actions.insert(0, update_action)

        banner = (
            BannerObject(
                pos_hint = {"center_x": 0.5, "center_y": 0.5},
                size = (100, 30),
                color = (0.647, 0.839, 0.969, 1),
                text = addon.update['version'],
                icon = "arrow-up-circle.png",
                icon_side = "left"
            )
            if addon.update.get('version')
            else None
        )

        return ListButton(
            properties = addon,
            enabled = addon.enabled,
            banner = banner,
            actions = actions,
            fade_in = fade_in,
            highlight = highlight,
            click_function = primary_action,
            loading = str(addon.id or addon.name).lower() in self.active_updates,
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
        updates_available = bool(self.server.addon.get_update_list())
        is_modpack = self.server.addon._server['is_modpack']

        self.update_button = (
            RelativeIconButton(
                '\n\n\nupdate all', {"center_x": 0.5, "center_y": 0.5}, None, (None, None), 'arrow-update.png',
                click_func = self.update_all_addons,
                force_color = [[(0.05, 0.08, 0.07, 1), (0.5, 0.9, 0.7, 1)], 'green']
            )
            if updates_available else
            RelativeIconButton(
                '\n\n\nup to date', {"center_x": 0.5, "center_y": 0.5}, None, (None, None), 'checkmark-sharp.png',
                clickable = False
            )
        )
        actions = [
            RelativeIconButton(
                '\n\n\nenable all', {"center_x": 0.5, "center_y": 0.5}, None, (None, None),
                'checkmark-circle-sharp.png',
                click_func = functools.partial(self.toggle_all, True),
                force_color = [[(0.05, 0.08, 0.07, 1), (0.6, 0.6, 1, 1)], 'green']
            ),
            RelativeIconButton(
                '\n\n\ndisable all', {"center_x": 0.5, "center_y": 0.5}, None, (None, None), 'close-circle-sharp.png',
                click_func = functools.partial(self.toggle_all, False),
                force_color = [[(0.05, 0.05, 0.1, 1), (0.6, 0.6, 1, 1)], 'pink']
            )
        ]
        if not is_modpack: actions.append(self.update_button)
        self.generate_list(header_content, "Import or Download add-ons below", self.server.addon.filter_addons, allow_empty=True, actions=actions)

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
        self.server._view_notif('add-ons', False)
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
        addon_list = addon_manager.return_single_list()
        self.gen_search_results(addon_list)

        if self.active_updates and self._watching_updates is not addon_manager:
            self._watching_updates = addon_manager
            server_name = self.server.name

            def _wait():
                try:
                    while addon_manager._sync_attr('active_updates'):
                        time.sleep(0.5)
                except: pass

                def _finish(*args):
                    if self._watching_updates is addon_manager:
                        self._watching_updates = None
                    try:
                        if utility.screen_manager.current == self.name and self.server.name == server_name:
                            self.refresh_list()
                    except: pass
                Clock.schedule_once(_finish, 0)
            dTimer(0, _wait).start()

        # Kick off checking for updates
        def _check_updates():
            addon_manager.check_for_updates()
            try:
                if utility.screen_manager.current == self.name:
                    Clock.schedule_once(self.refresh_update_button, 0)
                    Clock.schedule_once(functools.partial(self.server._view_notif, 'add-ons', False), 0)
            except: pass
        dTimer(0, _check_updates).start()

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
