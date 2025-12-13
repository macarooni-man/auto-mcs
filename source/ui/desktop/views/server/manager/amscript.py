from source.ui.desktop.views.server.manager.components import *



# amscript Manager ------------------------------------------------------------------------------------------------

def edit_script(edit_button, server_obj, script_path, download=True):
    "amscript-icon.png"

    # Override to download locally
    telepath_data = None
    telepath_script_dir = paths.telepath_script_temp
    if server_obj._telepath_data:
        telepath_data = constants.deepcopy(server_obj._telepath_data)
        telepath_data['headers'] = constants.api_manager._get_headers(telepath_data['host'], True)
        if download: script_path = constants.telepath_download(server_obj._telepath_data, script_path, os.path.join(paths.telepath_script_temp, server_obj._telepath_data['host']))

    send_log('edit_script', f"opening in amscript IDE:\n'{script_path}'", 'info')

    # Update Discord rich presence
    constants.discord_presence.update_presence(f"amscript IDE > Editing '{os.path.basename(script_path)}'")

    constants.app_config.load_config()

    # Passed to child IDE window
    data_dict = {
        '_telepath_data': telepath_data,
        'app_title': constants.app_title,
        'ams_version': constants.ams_version,
        'gui_assets': paths.ui_assets,
        'cache_dir': paths.cache,
        'background_color': constants.background_color,
        'app_config': constants.app_config,
        'script_obj': {
            'syntax_func': constants.server_manager._script_object.is_valid,
            'protected': constants.server_manager._script_object.protected_variables,
            'events': constants.server_manager._script_object.valid_events
        },
        'suggestions': server_obj._retrieve_suggestions(),
        'os_name': constants.os_name,
        'translate': translate,
        'telepath_script_dir': telepath_script_dir,
    }

    # Passed to parent IPC receiver
    ipc_functions = {
        'api_manager': constants.api_manager,
        'telepath_upload': constants.telepath_upload,
        'format_traceback': constants.format_traceback,
        '_send_log': logger.send_log
    }

    Clock.schedule_once(functools.partial(amseditor.edit_script, script_path, data_dict, ipc_functions), 0.1)
    if edit_button:
        edit_button.on_leave()
        edit_button.on_release()


class ScriptButton(HoverButton):

    def toggle_installed(self, installed, *args):
        self.installed = installed
        self.install_image.opacity = 1 if installed and not self.show_type else 0
        self.install_label.opacity = 1 if installed and not self.show_type else 0
        self.title.text_size = (self.size_hint_max[0] * (0.7 if installed else 0.94), self.size_hint_max[1])
        self.background_normal = os.path.join(paths.ui_assets, f'{self.id}{"_installed" if self.installed and not self.show_type else ""}.png')
        self.resize_self()

    def resize_self(self, *args):

        # Title and description
        padding = 2.17
        self.title.pos = (self.x + (self.title.text_size[0] / padding) - (6 if self.installed else 0), self.y + 31)
        self.subtitle.pos = (self.x + (self.subtitle.text_size[0] / padding) - 1, self.y)

        # Install label
        self.install_image.pos = (self.width + self.x - self.install_label.width - 28, self.y + 38.5)
        self.install_label.pos = (self.width + self.x - self.install_label.width - 30, self.y + 5)

        # Type Banner
        if self.show_type:
            self.type_banner.pos_hint = {"center_x": None, "center_y": None}
            self.type_banner.pos = (self.width + self.x - self.type_banner.width - 18, self.y + 38.5)

        # self.version_label.x = self.width+self.x-(self.padding_x[0]*offset)
        # self.version_label.y = self.y-(self.padding_y[0]*0.85)

    def __init__(self, properties, click_function=None, installed=False, show_type=False, fade_in=0.0, **kwargs):
        properties.name = properties.title
        properties.subtitle = properties.description

        super().__init__(**kwargs)

        self.installed = False
        self.show_type = show_type
        self.properties = properties
        self.border = (-5, -5, -5, -5)
        self.color_id = [(0.05, 0.05, 0.1, 1), (0.65, 0.65, 1, 1)]
        self.pos_hint = {"center_x": 0.5, "center_y": 0.6}
        self.size_hint_max = (580, 80)
        self.id = "addon_button"
        self.background_normal = os.path.join(paths.ui_assets, f'{self.id}.png')
        self.background_down = os.path.join(paths.ui_assets, f'{self.id}_click.png')

        # Loading stuffs
        self.original_subtitle = self.properties.subtitle if self.properties.subtitle else "Description unavailable"
        if "\n" in self.original_subtitle: self.original_subtitle = self.original_subtitle.split("\n", 1)[0].strip()
        self.original_font = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["regular"]}.ttf')

        # Title of Script
        self.title = Label()
        self.title.__translate__ = False
        self.title.id = "title"
        self.title.halign = "left"
        self.title.color = self.color_id[1]
        self.title.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
        self.title.font_size = sp(25)
        self.title.text_size = (self.size_hint_max[0] * 0.94, self.size_hint_max[1])
        self.title.shorten = True
        self.title.markup = True
        self.title.shorten_from = "right"
        self.title.max_lines = 1
        self.title.text = f"{self.properties.name}  [color=#434368]-[/color]  {self.properties.author if self.properties.author else 'Unknown'}"
        self.add_widget(self.title)

        # Description of Script
        self.subtitle = Label()
        self.subtitle.__translate__ = False
        self.subtitle.id = "subtitle"
        self.subtitle.halign = "left"
        self.subtitle.color = self.color_id[1]
        self.subtitle.font_name = self.original_font
        self.subtitle.font_size = sp(21)
        self.subtitle.opacity = 0.56
        self.subtitle.text_size = (self.size_hint_max[0] * 0.91, self.size_hint_max[1])
        self.subtitle.shorten = True
        self.subtitle.shorten_from = "right"
        self.subtitle.max_lines = 1
        self.subtitle.text = self.original_subtitle
        self.add_widget(self.subtitle)

        # Installed layout
        self.install_image = Image()
        self.install_image.size = (110, 30)
        self.install_image.keep_ratio = False
        self.install_image.allow_stretch = True
        self.install_image.source = os.path.join(paths.ui_assets, 'installed.png')
        self.install_image.opacity = 0
        self.add_widget(self.install_image)

        self.install_label = AlignLabel()
        self.install_label.halign = "right"
        self.install_label.valign = "middle"
        self.install_label.font_size = sp(18)
        self.install_label.color = self.color_id[1]
        self.install_label.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
        self.install_label.width = 100
        self.install_label.color = (0.05, 0.08, 0.07, 1)
        self.install_label.text = 'installed'
        self.install_label.opacity = 0
        self.add_widget(self.install_label)

        # Type Banner
        if show_type:
            self.type_banner = show_type
            self.add_widget(self.type_banner)

        # If self.installed is false, and self.properties.version, display version where "installed" logo is
        self.bind(pos=self.resize_self)
        if installed:
            self.toggle_installed(installed)

        # If click_function
        if click_function:
            self.bind(on_press=click_function)

        # Animate opacity
        if fade_in > 0:
            self.opacity = 0
            self.install_label.opacity = 0
            self.install_image.opacity = 0
            self.title.opacity = 0

            Animation(opacity=1, duration=fade_in).start(self)
            Animation(opacity=1, duration=fade_in).start(self.title)
            Animation(opacity=0.56, duration=fade_in).start(self.subtitle)

            if installed and not self.show_type:
                Animation(opacity=1, duration=fade_in).start(self.install_label)
                Animation(opacity=1, duration=fade_in).start(self.install_image)

    def on_enter(self, *args):
        if not self.ignore_hover:
            Animation(color=self.color_id[0], duration=0.06).start(self.title)
            Animation(color=self.color_id[0], duration=0.06).start(self.subtitle)
            animate_button(self, image=os.path.join(paths.ui_assets, f'{self.id}_hover.png'), color=self.color_id[0], hover_action=True)

    def on_leave(self, *args):
        if not self.ignore_hover:
            Animation(color=self.color_id[1], duration=0.06).start(self.title)
            Animation(color=self.color_id[1], duration=0.06).start(self.subtitle)
            animate_button(self, image=os.path.join(paths.ui_assets, f'{self.id}{"_installed" if self.installed and not self.show_type else ""}.png'), color=self.color_id[1], hover_action=False)

    def loading(self, load_state, *args):
        if load_state:
            self.subtitle.text = "Loading script info..."
            self.subtitle.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
        else:
            self.subtitle.text = self.original_subtitle
            self.subtitle.font_name = self.original_font


class ScriptListButton(HoverButton):

    def toggle_enabled(self, *args):
        self.title.text_size = (self.size_hint_max[0] * (0.94 if self.enabled else 0.7), self.size_hint_max[1])
        self.background_normal = os.path.join(paths.ui_assets, f'{self.id}{"" if self.enabled else "_disabled"}.png')

        # If disabled, add banner as such
        if not self.enabled:
            self.disabled_banner = BannerObject(
                pos_hint = {"center_x": 0.5, "center_y": 0.5},
                size = (125, 32),
                color = (1, 0.53, 0.58, 1),
                text = "disabled",
                icon = "close-circle.png",
                icon_side = "right"
            )
            self.add_widget(self.disabled_banner)

        self.resize_self()

    def resize_self(self, *args):

        # Title and description
        padding = 2.17
        self.title.pos = (
        self.x + (self.title.text_size[0] / padding) - (6 if self.disabled_banner else 0), self.y + 31)
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
            self.subtitle.text = "Loading script info..."
            self.subtitle.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
        else:
            self.subtitle.text = self.original_subtitle
            self.subtitle.font_name = self.original_font

    def __init__(self, properties, click_function=None, enabled=False, fade_in=0.0, highlight=False, **kwargs):

        properties.name = properties.title
        properties.subtitle = properties.description

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

        if self.enabled:

            # Edit button
            def edit_hover(*args):
                def change_color(*args):
                    if self.hovered:
                        self.hover_text.text = 'EDIT SCRIPT'
                        self.background_normal = os.path.join(paths.ui_assets, "server_button_hover.png")

                Clock.schedule_once(change_color, 0.07)
                Animation.stop_all(self.delete_button)
                Animation(opacity=1, duration=0.25).start(self.delete_button)

            def edit_on_leave(*args):
                def change_color(*args):
                    self.hover_text.text = ('DISABLE SCRIPT' if self.enabled else 'ENABLE SCRIPT')
                    if self.hovered:
                        self.background_normal = os.path.join(paths.ui_assets, f'{self.id}_hover_{"dis" if self.enabled else "en"}abled.png')
                        self.background_down = self.background_normal

                Clock.schedule_once(change_color, 0.07)
                Animation.stop_all(self.delete_button)
                Animation(opacity=0.65, duration=0.25).start(self.delete_button)

            def edit_click(*args):
                # Delete addon and reload list
                def reprocess_page(*args):
                    server_obj = constants.server_manager.current_server
                    script_manager = server_obj.script_manager
                    edit_script(self, server_obj, self.properties.path)

                    # Show banner if server is running
                    if script_manager._hash_changed():
                        Clock.schedule_once(
                            functools.partial(
                                utility.screen_manager.current_screen.show_banner,
                                (0.937, 0.831, 0.62, 1),
                                "An amscript reload is required to apply changes",
                                "sync.png",
                                3,
                                {"center_x": 0.5, "center_y": 0.965}
                            ), 0
                        )

                Clock.schedule_once(functools.partial(reprocess_page), 0)

            self.delete_layout = RelativeLayout(opacity=0)
            self.delete_button = IconButton('', {}, (0, 0), (None, None), 'edit-sharp.png', clickable=True, force_color=[[(0.05, 0.05, 0.1, 1), (0.01, 0.01, 0.01, 1)], ''], anchor='right', click_func=edit_click)
            self.delete_button.opacity = 0.65
            self.delete_button.button.bind(on_enter=edit_hover)
            self.delete_button.button.bind(on_leave=edit_on_leave)
            self.delete_layout.add_widget(self.delete_button)
            self.add_widget(self.delete_layout)

        else:

            # Delete button
            def delete_hover(*args):
                def change_color(*args):
                    if self.hovered:
                        self.hover_text.text = 'UNINSTALL SCRIPT'
                        self.background_normal = os.path.join(paths.ui_assets, "server_button_favorite_hover.png")

                Clock.schedule_once(change_color, 0.07)
                Animation.stop_all(self.delete_button)
                Animation(opacity=1, duration=0.25).start(self.delete_button)

            def delete_on_leave(*args):
                def change_color(*args):
                    self.hover_text.text = ('DISABLE SCRIPT' if self.enabled else 'ENABLE SCRIPT')
                    if self.hovered:
                        self.background_normal = os.path.join(paths.ui_assets, f'{self.id}_hover_{"dis" if self.enabled else "en"}abled.png')
                        self.background_down = self.background_normal

                Clock.schedule_once(change_color, 0.07)
                Animation.stop_all(self.delete_button)
                Animation(opacity=0.65, duration=0.25).start(self.delete_button)

            def delete_click(*args):
                # Delete addon and reload list
                def reprocess_page(*args):
                    script_manager = constants.server_manager.current_server.script_manager
                    script_manager.delete_script(self.properties)
                    constants.clear_script_cache(self.properties.path)
                    script_screen = utility.screen_manager.current_screen
                    new_list = script_manager.return_single_list()
                    script_screen.gen_search_results(new_list, fade_in=True)
                    Clock.schedule_once(functools.partial(script_screen.search_bar.execute_search, script_screen.search_bar.previous_search), 0)

                    # Show banner if server is running
                    if script_manager._hash_changed():
                        Clock.schedule_once(
                            functools.partial(
                                utility.screen_manager.current_screen.show_banner,
                                (0.937, 0.831, 0.62, 1),
                                "An amscript reload is required to apply changes",
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
                            ), 0
                        )

                    # Switch pages if page is empty
                    if (len(script_screen.scroll_layout.children) == 0) and (len(new_list) > 0):
                        script_screen.switch_page("left")

                Clock.schedule_once(
                    functools.partial(
                        utility.screen_manager.current_screen.show_popup,
                        "warning_query",
                        f'Uninstall ${self.properties.name}$',
                        "Uninstalling this script will render it unavailable for every server.\n\nDo you want to permanently uninstall this script?",
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
        self.hover_text.text = ('DISABLE SCRIPT' if self.enabled else 'ENABLE SCRIPT')
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

        # Title of Script
        self.title = Label()
        self.title.__translate__ = False
        self.title.id = "title"
        self.title.halign = "left"
        self.title.color = self.color_id[1]
        self.title.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
        self.title.font_size = sp(25)
        self.title.text_size = (self.size_hint_max[0] * (0.94), self.size_hint_max[1])
        self.title.shorten = True
        self.title.markup = True
        self.title.shorten_from = "right"
        self.title.max_lines = 1
        self.title.text = f"{self.properties.name}{('  [color=#434368]-[/color]  ' + self.properties.author) if self.properties.author.lower().strip() != 'unknown' else ''}"
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

        if highlight: self.highlight()

        # If self.enabled is false, and self.properties.version, display version where "enabled" logo is
        self.bind(pos=self.resize_self)
        self.resize_self()

        # If click_function
        if click_function: self.bind(on_press=click_function)

        # Animate opacity
        if fade_in > 0:
            self.opacity = 0
            self.title.opacity = 0

            Animation(opacity=1, duration=fade_in).start(self)
            Animation(opacity=1, duration=fade_in).start(self.title)
            Animation(opacity=0.56, duration=fade_in).start(self.subtitle)


class CreateAmscriptScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'
        self.name_input = None
        self.create_button = None

    def generate_menu(self, **kwargs):
        # Generate buttons on page load
        server_obj = constants.server_manager.current_server

        def on_click(*a):
            script_name = self.name_input.convert_name(self.name_input.text)
            script_title = self.name_input.text.strip()

            if server_obj._telepath_data:
                script_path = os.path.join(paths.telepath_script_temp, script_name)
                constants.folder_check(paths.telepath_script_temp)
            else:
                script_path = os.path.join(paths.scripts, script_name)
                constants.folder_check(paths.scripts)

            contents = f"""#!
# title: {script_title}
# author: {constants.username.title()}
# version: 1.0
# description: 
#!



# {translate('Welcome to the amscript IDE!')}
# {translate('Right-click > Help to learn more about the capabilities of amscript')}

@player.on_join(player, message):
    if player not in server.usercache:
        player.log(f"{translate('Welcome to')} {{server}} {{player}}!")
"""

            with open(script_path, 'w+', encoding='utf-8', errors='ignore') as f:
                f.write(contents)

            # Upload and import if it's remote
            if server_obj._telepath_data:
                server_obj.script_manager.import_script(script_path)

            for s in server_obj.script_manager.return_single_list():
                if s.file_name == script_name:
                    server_obj.script_manager.script_state(s, enabled=True)
                    break

            def later(*_): edit_script(None, server_obj, script_path, download=False)
            dTimer(1, later).start()

            utility.screen_manager.previous_screen()
            del utility.screen_manager.screen_tree[-1]

            if server_obj.running:
                Clock.schedule_once(
                    functools.partial(
                        self.show_banner,
                        (0.937, 0.831, 0.62, 1),
                        "An amscript reload is required to apply changes",
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
                        f"'{script_name}' has been created",
                        "checkmark-circle-sharp.png",
                        2.5,
                        {"center_x": 0.5, "center_y": 0.965}
                    ), 0
                )

        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'

        float_layout.add_widget(InputLabel(pos_hint={"center_x": 0.5, "center_y": 0.58}))
        float_layout.add_widget(HeaderText("What would you like to name your script?", '', (0, 0.76)))
        self.name_input = ScriptNameInput(pos_hint={"center_x": 0.5, "center_y": 0.5})
        float_layout.add_widget(self.name_input)
        self.name_input.update_script_list(server_obj.script_manager.return_single_list())
        self.create_button = WaitButton('Create in IDE', (0.5, 0.24), 'amscript.png', width=370, icon_offset=-150, disabled=True, click_func=on_click)
        buttons.append(self.create_button)
        buttons.append(ExitButton('Back', (0.5, 0.14), cycle=True))

        for button in buttons: float_layout.add_widget(button)

        menu_name = f"{server_obj.name}, amscript, Create script"
        float_layout.add_widget(generate_title(f"Script Manager: '{server_obj.name}'"))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)
        self.name_input.grab_focus()


class ServerAmscriptScreen(MenuBackground):

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

        script_manager = constants.server_manager.current_server.script_manager
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
        script_count = len(results)
        enabled_count = len(script_manager.installed_scripts['enabled'])
        disabled_count = len(script_manager.installed_scripts['disabled'])
        very_bold_font = os.path.join(paths.ui_assets, 'fonts', constants.fonts["very-bold"])
        header_content = f"{translate('Installed Scripts')}  [color=#494977]-[/color]  " + (f'[color=#6A6ABA]{translate("No items")}[/color]' if script_count == 0 else f'[font={very_bold_font}]1[/font] {translate("item")}' if script_count == 1 else f'[font={very_bold_font}]{enabled_count:,}{("/[color=#FF8793]" + str(disabled_count) + "[/color]") if disabled_count > 0 else ""}[/font] {translate("items")}')

        if script_manager._hash_changed():
            icons = os.path.join(paths.ui_assets, 'fonts', constants.fonts['icons'])
            header_content = f"[color=#EFD49E][font={icons}]y[/font] " + header_content + "[/color]"

        for child in self.header.children:
            if child.id == "text":
                child.text = header_content
                break

        # If there are no scripts, say as much with a label
        if script_count == 0:
            self.blank_label.text = "Import or Download Scripts Below"
            utility.hide_widget(self.blank_label, False)
            self.blank_label.opacity = 0
            Animation(opacity=1, duration=0.2).start(self.blank_label)
            self.max_pages = 0
            self.current_page = 0

        # If there are scripts, display them here
        else:
            utility.hide_widget(self.blank_label, True)

            # Clear and add all scripts
            for x, script_object in enumerate(page_list, 1):

                # Activated when script is clicked
                def toggle_script(index, *args):
                    script = index

                    if len(script.title) < 26: script_name = script.title
                    else:                      script_name = script.title[:23] + "..."

                    # Toggle script state
                    script_manager.script_state(script, enabled=not script.enabled)
                    self.gen_search_results(script_manager.return_single_list(), fade_in=False, highlight=script.hash, animate_scroll=True)

                    if constants.server_manager.current_server.script_manager._hash_changed():
                        Clock.schedule_once(
                            functools.partial(
                                self.show_banner,
                                (0.937, 0.831, 0.62, 1),
                                "An amscript reload is required to apply changes",
                                "sync.png",
                                3,
                                {"center_x": 0.5, "center_y": 0.965}
                            ), 0
                        )
                    else:
                        if script.enabled: banner_text = f"'${script_name}$' is now disabled"
                        else:              banner_text = f"'${script_name}$' is now enabled"

                        Clock.schedule_once(
                            functools.partial(
                                self.show_banner,
                                (1, 0.5, 0.65, 1) if script.enabled else (0.553, 0.902, 0.675, 1),
                                banner_text,
                                "close-circle-sharp.png" if script.enabled else "checkmark-circle-sharp.png",
                                2.5,
                                {"center_x": 0.5, "center_y": 0.965}
                            ), 0
                        )

                # Script button click function
                self.scroll_layout.add_widget(
                    ScrollItem(
                        widget = ScriptListButton(
                            properties = script_object,
                            enabled = script_object.enabled,
                            fade_in = ((x if x <= 8 else 8) / self.anim_speed) if fade_in else 0,
                            highlight = (highlight == script_object.hash),
                            click_function = functools.partial(
                                toggle_script,
                                script_object,
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

        self.last_results = []
        self.page_size = 20
        self.current_page = 0
        self.max_pages = 0
        self.anim_speed = 10

        self.server = None
        self.reload_button = None
        self.directory_button = None
        self.path_button = None

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
        script_count = len(self.server.script_manager.return_single_list())
        very_bold_font = os.path.join(paths.ui_assets, 'fonts', constants.fonts["very-bold"])
        header_content = f"{translate('Installed Scripts')}  [color=#494977]-[/color]  " + (f'[color=#6A6ABA]{translate("No items")}[/color]' if script_count == 0 else f'[font={very_bold_font}]1[/font] {translate("item")}' if script_count == 1 else f'[font={very_bold_font}]{script_count}[/font] {translate("items")}')
        self.header = HeaderText(header_content, '', (0, 0.9), __translate__=(False, True), no_line=True)

        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'
        float_layout.add_widget(self.header)

        # Add blank label to the center, then load self.gen_search_results()
        self.blank_label = Label()
        self.blank_label.text = "Manage scripts below"
        self.blank_label.font_name = os.path.join(paths.ui_assets, 'fonts', constants.fonts['italic'])
        self.blank_label.pos_hint = {"center_x": 0.5, "center_y": 0.55}
        self.blank_label.font_size = sp(24)
        self.blank_label.color = (0.6, 0.6, 1, 0.35)
        float_layout.add_widget(self.blank_label)

        search_function = self.server.script_manager.filter_scripts
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
        bottom_buttons.size_hint_max_x = 512
        bottom_buttons.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        bottom_buttons.add_widget(MainButton('Import', (0, 0.202), 'download-outline.png', width=245, icon_offset=-115, auto_adjust_icon=True))
        bottom_buttons.add_widget(MainButton('Create New', (0.5, 0.202), '', width=245, icon_offset=-115, auto_adjust_icon=False))
        bottom_buttons.add_widget(MainButton('Download', (1, 0.202), 'cloud-download-outline.png', width=245, icon_offset=-115, auto_adjust_icon=True))
        buttons.append(ExitButton('Back', (0.5, -1), cycle=True))

        for button in buttons: float_layout.add_widget(button)
        float_layout.add_widget(bottom_buttons)

        menu_name = f"{self.server.name}, amscript"
        float_layout.add_widget(generate_title(f"Script Manager: '{self.server.name}'"))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)

        # Add ManuTaskbar
        self.menu_taskbar = MenuTaskbar(selected_item='amscript')
        self.add_widget(self.menu_taskbar)

        # Buttons in the top right corner
        def open_dir(*a):
            constants.folder_check(paths.scripts)
            open_folder(paths.scripts)

        self.directory_button = IconButton('open directory', {}, (70, 110), (None, None), 'folder.png', anchor='right', click_func=open_dir, text_offset=(10, 0))
        float_layout.add_widget(self.directory_button)

        if self.server.running:
            def reload_scripts(*a):
                def timer():
                    self.server.reload_scripts()
                    Clock.schedule_once(
                        functools.partial(
                            self.show_banner,
                            (0.553, 0.902, 0.675, 1),
                            f"amscript engine was restarted successfully",
                            "checkmark-circle-sharp.png",
                            2.5,
                            {"center_x": 0.5, "center_y": 0.965}
                        ), 0
                    )
                    Clock.schedule_once(functools.partial(self.gen_search_results, self.server.script_manager.return_single_list()), 0)

                dTimer(0, timer).start()

            self.reload_button = IconButton('reload scripts', {}, (125, 110), (None, None), 'reload-sharp.png', clickable=self.server.running, anchor='right', click_func=reload_scripts, text_offset=(10, 50))
            float_layout.add_widget(self.reload_button)

        # Automatically generate results (installed scripts) on page load
        self.gen_search_results(self.server.script_manager.return_single_list())

        # Show banner if server is running
        if constants.server_manager.current_server.script_manager._hash_changed():
            Clock.schedule_once(
                functools.partial(
                    self.show_banner,
                    (0.937, 0.831, 0.62, 1),
                    "An amscript reload is required to apply changes",
                    "sync.png",
                    3,
                    {"center_x": 0.5, "center_y": 0.965}
                ), 0
            )


class ServerAmscriptSearchScreen(MenuBackground):

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
        script_manager = constants.server_manager.current_server.script_manager

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
            script_count = len(results)
            very_bold_font = os.path.join(paths.ui_assets, 'fonts', constants.fonts["very-bold"])
            search_text = self.search_bar.previous_search if (len(self.search_bar.previous_search) <= 25) else self.search_bar.previous_search[:22] + "..."
            if isinstance(search_text, str) and not search_text:
                header_content = f"{translate('Available Scripts')}  [color=#494977]-[/color]  " + (f'[color=#6A6ABA]{translate("No results")}[/color]' if script_count == 0 else f'[font={very_bold_font}]1[/font] {translate("item")}' if script_count == 1 else f'[font={very_bold_font}]{script_count:,}[/font] {translate("items")}')
            else:
                header_content = f"{translate('Search for')} '{search_text}'  [color=#494977]-[/color]  " + (f'[color=#6A6ABA]{translate("No results")}[/color]' if script_count == 0 else f'[font={very_bold_font}]1[/font] {translate("item")}' if script_count == 1 else f'[font={very_bold_font}]{script_count:,}[/font] {translate("items")}')

            for child in self.header.children:
                if child.id == "text":
                    child.text = header_content
                    break

            # If there are no scripts, say as much with a label
            if script_count == 0:
                self.blank_label.text = "there are no items to display"
                utility.hide_widget(self.blank_label, False)
                self.blank_label.opacity = 0
                Animation(opacity=1, duration=0.2).start(self.blank_label)
                self.max_pages = 0
                self.current_page = 0

            # If there are scripts, display them here
            else:
                utility.hide_widget(self.blank_label, True)

                # Clear and add all scripts
                for x, script_object in enumerate(page_list, 1):

                    # Function to install script
                    def install_script(index):

                        selected_button = [item for item in self.scroll_layout.walk() if item.__class__.__name__ == "ScriptButton"][index - 1]
                        script = selected_button.properties
                        selected_button.toggle_installed(not selected_button.installed)

                        if len(script.name) < 26: script_name = script.name
                        else:                     script_name = script.name[:23] + "..."

                        # Install
                        if selected_button.installed:
                            dTimer(0, functools.partial(script_manager.download_script, script)).start()
                            # Show banner if server is running
                            if script_manager._hash_changed():
                                Clock.schedule_once(
                                    functools.partial(
                                        self.show_banner,
                                        (0.937, 0.831, 0.62, 1),
                                        "An amscript reload is required to apply changes",
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
                                        f"Installed '${script_name}$'",
                                        "checkmark-circle-sharp.png",
                                        2.5,
                                        {"center_x": 0.5, "center_y": 0.965}
                                    ), 0.25
                                )

                        # Uninstall
                        else:
                            for installed_script in script_manager.return_single_list():
                                if installed_script.title == script.title:
                                    script_manager.delete_script(installed_script)
                                    constants.clear_script_cache(installed_script.path)

                                    # Show banner if server is running
                                    if script_manager._hash_changed():
                                        Clock.schedule_once(
                                            functools.partial(
                                                self.show_banner,
                                                (0.937, 0.831, 0.62, 1),
                                                "An amscript reload is required to apply changes",
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
                                                f"'${script_name}$' was uninstalled",
                                                "trash-sharp.png",
                                                2.5,
                                                {"center_x": 0.5, "center_y": 0.965}
                                            ), 0.25
                                        )

                                    break

                        return script, selected_button.installed

                    # Activated when script is clicked
                    def view_script(script, index, *args):
                        selected_button = [item for item in self.scroll_layout.walk() if item.__class__.__name__ == "ScriptButton"][index - 1]
                        # selected_button.loading(True)

                        Clock.schedule_once(
                            functools.partial(
                                self.show_popup,
                                "script",
                                " ",
                                " ",
                                (None, functools.partial(install_script, index)),
                                (selected_button.installed, script)
                            ),
                            0
                        )

                    # Add-on button click function
                    self.scroll_layout.add_widget(
                        ScrollItem(
                            widget = ScriptButton(
                                properties = script_object,
                                installed = script_object.installed,
                                fade_in = ((x if x <= 8 else 8) / self.anim_speed),
                                click_function = functools.partial(
                                    view_script,
                                    script_object,
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
        server_obj = constants.server_manager.current_server
        script_manager = server_obj.script_manager

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
        script_count = 0
        very_bold_font = os.path.join(paths.ui_assets, 'fonts', constants.fonts["very-bold"])
        header_content = translate("Script Search")
        self.header = HeaderText(header_content, '', (0, 0.89), __translate__=(False, True))

        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'
        float_layout.add_widget(self.header)

        # Add blank label to the center
        self.blank_label = Label()
        self.blank_label.text = "search for scripts above"
        self.blank_label.font_name = os.path.join(paths.ui_assets, 'fonts', constants.fonts['italic'])
        self.blank_label.pos_hint = {"center_x": 0.5, "center_y": 0.48}
        self.blank_label.font_size = sp(24)
        self.blank_label.color = (0.6, 0.6, 1, 0.35)
        float_layout.add_widget(self.blank_label)

        search_function = script_manager.search_scripts
        self.search_bar = SearchBar(return_function=search_function, pos_hint={"center_x": 0.5, "center_y": 0.795})
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
        menu_name = f"{server_name}, amscript, Download"
        float_layout.add_widget(generate_title(f"Script Manager: '{server_name}'"))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)

        # # Autofocus search bar
        # for widget in self.search_bar.children:
        #     try:
        #         if widget.id == "search_input":
        #             widget.grab_focus()
        #             break
        #     except AttributeError:
        #         pass
        Clock.schedule_once(functools.partial(self.search_bar.execute_search, ""), 0)
