from source.ui.desktop.views.server.manager.components import *



# Server Manager Launch ------------------------------------------------------------------------------------------------

# Prompt for backups and updates on new server config
def prompt_new_server(server_obj, *args):
    # Step 3 - prompt for updates
    def set_update(boolean):
        server_obj.enable_auto_update(boolean)
        server_obj.reload_config()

    def prompt_updates(*args):
        utility.screen_manager.current_screen.show_popup(
            "query",
            "Automatic Updates",
            f"Would you like to enable automatic updates for '${server_obj.name}$'?\n\nIf an update is available, auto-mcs will update this server when opened",
            [functools.partial(set_update, False),
             functools.partial(set_update, True)]
        )

    # Step 2 - apply settings from backup popup and prompt for updates
    def set_bkup_and_prompt_update(boolean):
        server_obj.backup.enable_auto_backup(boolean)
        if boolean:
            dTimer(0, server_obj.backup.save).start()

        def wait_timer(*a):
            while utility.screen_manager.current_screen.popup_widget:
                time.sleep(0.1)
            if not constants.server_manager.current_server.is_modpack or constants.server_manager.current_server.is_modpack == 'mrpack':
                Clock.schedule_once(prompt_updates, 0)

        dTimer(0, wait_timer).start()

    # Step 1 - prompt for backups
    def prompt_backup(*args):
        utility.screen_manager.current_screen.show_popup(
            "query",
            "Automatic Back-ups",
            f"Would you like to enable automatic back-ups for '${server_obj.name}$'?\n\nauto-mcs will back up this server when closed",
            [functools.partial(set_bkup_and_prompt_update, False),
             functools.partial(set_bkup_and_prompt_update, True)]
        )

    prompt_backup()


class PerformancePanel(RelativeLayout):

    def update_rect(self, *args):
        texture_offset = 70

        # Resize panel
        console_panel = utility.screen_manager.current_screen.console_panel
        self.y = console_panel.default_y + (Window.height - console_panel.size_offset[1]) - 24
        self.width = Window.width - console_panel.size_offset[0] + texture_offset
        self.height = 240

        # Repos panel widgets
        overview_max = (Window.width * 0.2)
        self.overview_widget.size_hint_max_x = overview_max if overview_max >= self.overview_min else self.overview_min

        meter_max = (Window.width * 0.32)
        self.meter_layout.size_hint_max_x = meter_max if meter_max >= self.meter_min else self.meter_min
        self.meter_layout.x = self.width - self.meter_layout.width
        for child in self.meter_layout.children:
            Clock.schedule_once(child.recalculate_size, 0)

        self.player_widget.x = self.overview_widget.x + self.overview_widget.width - texture_offset + 12
        self.player_widget.size_hint_max_x = (self.width) - self.meter_layout.width - self.overview_widget.width + (
                    texture_offset * 2) - 24
        Clock.schedule_once(self.player_widget.recalculate_size, 0)

    # Updates data in panel while the server is running
    def refresh_data(self, interval=0.5, *args):

        # Get performance stats if running locally
        server_obj = constants.server_manager.current_server

        # Prevent a crash from doing something while in the menu of a server, and current_server is reset
        if not server_obj:
            return

        if server_obj and not server_obj._telepath_data:
            dTimer(0, functools.partial(server_obj.performance_stats, interval, (self.player_clock == 3))).start()

        # If the server is running remotely, update the console text as needed
        # This should probably be moved, though, it's the only client loop
        elif utility.screen_manager.current_screen.name == 'ServerViewScreen' and server_obj._telepath_data:
            console_panel = utility.screen_manager.current_screen.console_panel
            if server_obj.running and server_obj.run_data:
                server_obj.run_data = server_obj._telepath_run_data()

                # Check if remote server has disconnected when updating panel
                if not server_obj.run_data:
                    if check_telepath_disconnect():
                        return True

                try:
                    data_len = len(console_panel.scroll_layout.data)
                    run_len = len(server_obj.run_data['log'])
                    if data_len <= run_len:
                        console_panel.update_text(server_obj.run_data['log'], animate_last=(run_len > data_len))

                    if server_obj.run_data['deadlocked']:
                        console_panel.toggle_deadlock(True)

                # If log was removed from run_data
                except KeyError:
                    pass

                # Close the console if remotely launched, and no logs exist
                if not server_obj.running or not server_obj.run_data:
                    data = server_obj._sync_telepath_stop()

                    # Prevent closing if data does not exist (Telepath re-authentication issue)
                    if not data:
                        return True

                    server_obj.crash_log = data['crash']
                    console_panel.update_text(data['log'])
                    console_panel.reset_panel(data['crash'])

                    # Before closing, save contents to temp for view screen
                    constants.folder_check(paths.temp)
                    file_name = f"{server_obj._telepath_data['display-name']}, {server_obj.name}-latest.log"
                    with open(os.path.join(paths.temp, file_name), 'w+') as f:
                        f.write(json.dumps(data['log']))

        def update_data(*args):
            try:
                perf_data = constants.server_manager.current_server.run_data['performance']
            except KeyError:
                return
            except AttributeError:
                return

            # Update meter
            self.cpu_meter.set_percent(perf_data['cpu'])
            self.ram_meter.set_percent(perf_data['ram'])

            # Update up-time
            formatted_color = '[color=#737373]'
            found = False
            for x, item in enumerate(perf_data['uptime'].split(":")):
                if x == 0 and len(item) > 2:
                    formatted_color = f'{item}:'
                    found = True
                    continue
                if x == 0 and item != '00':
                    item = int(item)
                    formatted_color += '[/color]' if len(str(item)) >= 2 else '0[/color]'
                    found = True
                if item != "00" and not found:
                    found = True
                    item = int(item)
                    formatted_color += f'[/color]{item}:' if len(str(item)) == 2 else f'0[/color]{item}:'
                else:
                    formatted_color += f'{item}:'

            # Update player count every 5 cycles
            self.player_clock += 1
            if self.player_clock > 5:
                self.player_clock = 0

                total_count = int(self.overview_widget.max_players)
                percent = (len(perf_data['current-players']) / total_count)
                self.player_widget.update_data(perf_data['current-players'])

                # Update Discord rich presence
                constants.discord_presence.update_presence('Server Manager > Launch')

                # Colors
                if percent == 0:
                    color = (0.45, 0.45, 0.45, 1)
                elif percent < 50:
                    color = (0.92, 0.92, 0.92, 1)
                elif percent < 75:
                    color = (1, 0.9, 0.5, 1)
                else:
                    color = (1, 0.53, 0.58, 1)

                Animation(color=color, duration=0.4, transition='in_out_sine').start(
                    self.overview_widget.player_label.label)
                self.overview_widget.player_label.label.text = f'{len(perf_data["current-players"])}[color=#737373] / [/color]{total_count}'

            self.overview_widget.uptime_label.text = formatted_color[:-1]
            Animation(color=(0.92, 0.92, 0.92, 1), duration=0.4, transition='in_out_sine').start(
                self.overview_widget.uptime_label.label)

        if server_obj:
            Clock.schedule_once(update_data, (interval + 0.05))

    # Sets panel back to the default state
    def reset_panel(self):
        def reset(*args):
            self.cpu_meter.set_percent(0)
            self.ram_meter.set_percent(0)
            self.overview_widget.reset_panel()
            self.player_widget.update_data(None)

        Clock.schedule_once(reset, 1.5)

    def __init__(self, server_name, **kwargs):
        super().__init__(**kwargs)

        # Apply accent color if it's different
        screen_accent = utility.screen_manager.current_screen.accent_color
        if screen_accent:
            panel_background = constants.brighten_color(screen_accent, 0.025)
            normal_accent = constants.brighten_color(screen_accent, 0.32)
            dark_accent = constants.brighten_color(screen_accent, -0.035)
        else:
            panel_background = constants.convert_color("#232439")['rgb']
            normal_accent = constants.convert_color("#707CB7")['rgb']
            dark_accent = constants.convert_color("#151523")['rgb']

        yellow_accent = (1, 0.9, 0.5, 1)
        gray_accent = (0.45, 0.45, 0.45, 1)
        green_accent = (0.3, 1, 0.6, 1)
        red_accent = (1, 0.53, 0.58, 1)

        self.overview_min = 280
        self.meter_min = 350
        self.player_clock = 0

        # Label with shadow
        class ShadowLabel(RelativeLayout):

            def __setattr__(self, attr, value):
                if "text" in attr or "color" in attr:
                    try:
                        self.label.__setattr__(attr, value)
                        self.shadow.__setattr__(attr, value)
                        Clock.schedule_once(self.on_resize, 0)
                    except AttributeError:
                        super().__setattr__(attr, value)
                else:
                    super().__setattr__(attr, value)

            def on_resize(self, *args):
                max_x = 500
                self.label.texture_update()
                self.size_hint_max = self.label.texture_size
                self.size_hint_max[0] = max_x
                self.label.size_hint_max = self.label.texture_size
                self.label.size_hint_max[0] = max_x

                self.shadow.texture_update()
                self.shadow.size_hint_max = self.shadow.texture_size
                self.shadow.size_hint_max[0] = max_x
                self.shadow.pos = (self.label.x + self.offset, self.label.y - self.offset)

            def __init__(self, text, font, size, color, align='left', offset=2, shadow_color=dark_accent,
                         __translate__=True, **kwargs):
                super().__init__(**kwargs)

                self.offset = offset

                # Shadow
                self.shadow = AlignLabel()
                self.shadow.__translate__ = __translate__
                self.shadow.text = text
                self.shadow.font_name = font
                self.shadow.font_size = size
                self.shadow.color = shadow_color
                self.shadow.halign = align
                self.add_widget(self.shadow)

                # Main label
                self.label = AlignLabel()
                self.label.__translate__ = __translate__
                self.label.text = text
                self.label.font_name = font
                self.label.font_size = size
                self.label.color = color
                self.label.halign = align
                self.label.markup = True
                self.add_widget(self.label)

                self.bind(pos=self.on_resize)
                Clock.schedule_once(self.on_resize, 0)

        # Hacky background for panel objects
        class PanelFrame(Button):

            def on_press(self):
                self.state = 'normal'
                pass

            def on_touch_down(self, touch):
                return super().on_touch_down(touch)

            def on_touch_up(self, touch):
                return super().on_touch_up(touch)

            def __init__(self, **kwargs):
                super().__init__(**kwargs)

                self.background_normal = os.path.join(paths.ui_assets, 'performance_panel.png')
                self.background_down = os.path.join(paths.ui_assets, 'performance_panel.png')
                self.background_color = panel_background
                self.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
                self.border = (60, 60, 60, 60)

        class MeterWidget(RelativeLayout):

            def set_percent(self, percent: float or int, animate=True, *args):

                # Normalize value
                self.percent = round(percent, 1)
                if percent >= 100:
                    self.percent = 100
                if percent <= 0:
                    self.percent = 0

                # Colors
                if self.percent < 5:
                    color = gray_accent
                elif self.percent < 50:
                    color = green_accent
                elif self.percent < 75:
                    color = yellow_accent
                else:
                    color = red_accent

                # Update properties
                self.percentage_label.text = f'{self.percent} %'
                new_size = round(self.progress_bg.size_hint_max_x * (self.percent / 100)) if self.percent >= 1 else 0

                Animation.stop_all(self.progress_bar)
                Animation.stop_all(self.percentage_label.label)

                if animate:
                    Animation(color=color, duration=0.3, transition='in_out_sine').start(self.percentage_label.label)
                    Animation(color=color, duration=0.3, transition='in_out_sine').start(self.progress_bar)
                    if new_size == 0:
                        Animation.stop_all(self.progress_bar)
                        Animation(color=color, size_hint_max_x=new_size, duration=0.4, transition='in_out_sine').start(
                            self.progress_bar)
                    else:
                        Animation(size_hint_max_x=new_size, duration=0.99, transition='in_out_sine').start(
                            self.progress_bar)
                else:
                    self.percentage_label.label.color = self.progress_bar.color = color
                    self.progress_bar.size_hint_max_x = new_size

            def recalculate_size(self, *args):

                # Update bar size
                padding = (self.width - self.meter_min) * 0.03
                self.progress_bg.pos = (45 + padding, 52)
                self.progress_bg.size_hint_max = (self.width - 145 - (padding * 2), 7)
                self.progress_bar.pos = (
                self.progress_bg.x, self.progress_bg.y + self.progress_bar.size_hint_max[1] + 1)
                self.set_percent(self.percent, animate=False)

                # Set text position
                text_x = self.width - self.percentage_label.width - 45 - padding
                self.percentage_label.pos = (text_x, self.progress_bar.pos[1] + 12)
                self.name.pos = (text_x, self.progress_bg.pos[1] - (self.progress_bar.size_hint_max[1] / 2))

            def __init__(self, meter_name, meter_min=350, **kwargs):
                super().__init__(**kwargs)

                self.percent = 0
                self.meter_min = meter_min

                # Background
                self.background = PanelFrame()
                self.size_hint_max_y = 152
                self.add_widget(self.background)

                # Progress bar
                self.progress_bg = Image(color=dark_accent)
                self.add_widget(self.progress_bg)

                self.progress_bar = Image(color=gray_accent)
                self.progress_bar.size_hint_max = (0, 7)
                self.add_widget(self.progress_bar)

                # Label text
                self.name = ShadowLabel(
                    __translate__=False,
                    text=meter_name,
                    font=os.path.join(paths.ui_assets, 'fonts', constants.fonts["medium"]),
                    size=sp(22),
                    color=normal_accent,
                    align='right',
                    shadow_color=(0, 0, 0, 0)
                )
                self.add_widget(self.name)

                # Percent text
                self.percentage_label = ShadowLabel(
                    __translate__=False,
                    text=f'{self.percent} %',
                    font=os.path.join(paths.ui_assets, 'fonts', constants.fonts["bold"]),
                    size=sp(30),
                    color=gray_accent,
                    offset=3,
                    align='right',
                    shadow_color=(0, 0, 0, 0)
                )
                self.add_widget(self.percentage_label)

                Clock.schedule_once(self.recalculate_size, 0)

        class OverviewWidget(RelativeLayout):

            def reset_panel(self):
                def reset_text(*args):
                    self.uptime_label.text = f'00:00:00:00'
                    self.player_label.text = f'0 / {self.max_players}'

                Animation(color=gray_accent, duration=0.4, transition='in_out_sine').start(self.uptime_label.label)
                Animation(color=gray_accent, duration=0.4, transition='in_out_sine').start(self.player_label.label)
                Clock.schedule_once(reset_text, 0.4)

            def __init__(self, overview_min=270, **kwargs):
                super().__init__(**kwargs)

                try:
                    self.max_players = constants.server_manager.current_server.server_properties['max-players']
                except KeyError:
                    self.max_players = 20

                self.background = PanelFrame()
                self.size_hint_max_x = overview_min
                self.overview_min = overview_min
                self.add_widget(self.background)

                # Up-time title
                self.uptime_title = ShadowLabel(
                    text=f'up-time',
                    font=os.path.join(paths.ui_assets, 'fonts', constants.fonts["italic"]),
                    size=sp(23),
                    color=normal_accent,
                    offset=3,
                    align='center',
                    shadow_color=constants.brighten_color(dark_accent, 0.04)
                )
                self.uptime_title.pos_hint = {'center_x': 0.5}
                self.uptime_title.y = 170
                self.add_widget(self.uptime_title)

                # Up-time label
                self.uptime_label = ShadowLabel(
                    __translate__=False,
                    text=f'00:00:00:00',
                    font=os.path.join(paths.ui_assets, 'fonts', constants.fonts["mono-bold"]) + '.otf',
                    size=sp(30),
                    color=gray_accent,
                    offset=3,
                    align='center',
                    shadow_color=(0, 0, 0, 0)
                )
                self.uptime_label.pos_hint = {'center_x': 0.5}
                self.uptime_label.y = 135
                self.add_widget(self.uptime_label)

                # Player count title
                self.player_title = ShadowLabel(
                    text=f'capacity',
                    font=os.path.join(paths.ui_assets, 'fonts', constants.fonts["italic"]),
                    size=sp(23),
                    color=normal_accent,
                    offset=3,
                    align='center',
                    shadow_color=constants.brighten_color(dark_accent, 0.04)
                )
                self.player_title.pos_hint = {'center_x': 0.5}
                self.player_title.y = 80
                self.add_widget(self.player_title)

                # Player count label
                self.player_label = ShadowLabel(
                    __translate__=False,
                    text=f'0 / {self.max_players}',
                    font=os.path.join(paths.ui_assets, 'fonts', constants.fonts["bold"]),
                    size=sp(26),
                    color=gray_accent,
                    offset=3,
                    align='center',
                    shadow_color=(0, 0, 0, 0)
                )
                self.player_label.pos_hint = {'center_x': 0.5}
                self.player_label.y = 45
                self.add_widget(self.player_label)

        class PlayerWidget(RelativeLayout):

            # Add players
            def update_data(self, player_dict):
                if player_dict:
                    if self.player_list:
                        self.player_list.rows = None

                    if self.layout.opacity == 0:
                        Animation(opacity=0, duration=0.4, transition='in_out_sine').start(self.empty_label)

                        def after_anim(*args):
                            Animation(opacity=1, duration=0.4, transition='in_out_sine').start(self.layout)

                        Clock.schedule_once(after_anim, 0.4)

                    # if self.scroll_layout.data:
                    #     self.unq_hash['before'] = self.scroll_layout.data
                    # self.unq_hash['after'] = player_dict
                    self.scroll_layout.data = player_dict

                    if self.resize_list:
                        self.resize_list()

                else:
                    if self.layout.opacity == 1:
                        Animation(opacity=0, duration=0.4, transition='in_out_sine').start(self.layout)

                        def after_anim(*args):
                            Animation(opacity=1, duration=0.4, transition='in_out_sine').start(self.empty_label)

                        Clock.schedule_once(after_anim, 0.4)

            def resize_list(self, *args):
                blank_name = ''

                data_len = len(self.scroll_layout.data)

                try:
                    if self.player_list.rows <= 5:
                        for player in self.scroll_layout.data:
                            if player['text'] == blank_name:
                                self.scroll_layout.data.remove(player)
                        data_len = len([item for item in self.scroll_layout.data if item['text'] != blank_name])
                except TypeError:
                    pass

                text_width = 240
                if self.scroll_layout.width <= 50:
                    self.recalculate_size()
                    return

                # Dirty fix to circumvent RecycleView missing data: https://github.com/kivy/kivy/pull/7262
                try:
                    text_width = int(((self.scroll_layout.width // text_width) // 1))
                    self.player_list.cols = text_width
                    self.player_list.rows = round(data_len / text_width) + 3
                    # print(text_width, self.player_list.cols, self.player_list.rows, data_len)

                    if ((
                                data_len <= self.player_list.cols) and self.player_list.rows <= 5) or data_len + 1 == self.player_list.cols:
                        if self.scroll_layout.data[-1] is not {'text': blank_name}:
                            for x in range(self.player_list.cols):
                                self.scroll_layout.data.append({'text': blank_name})
                except ZeroDivisionError:
                    pass
                except IndexError:
                    pass

            def recalculate_size(self, *args):
                texture_offset = 70
                list_offset = 15

                self.layout.pos = ((texture_offset / 2), (texture_offset / 2) + list_offset)
                self.layout.size_hint_max = (
                self.width - texture_offset, self.height - texture_offset - (list_offset * 3.5))
                self.scroll_layout.size = self.layout.size

                Clock.schedule_once(self.resize_list, 0)

            def __init__(self, **kwargs):
                super().__init__(**kwargs)

                # self.unq_hash = {'before': None, 'after': None}

                class PlayerLabel(RelativeLayout):

                    class PlayerButton(HoverButton):
                        def update_context_options(self):
                            username = self.parent.label.text
                            if not self.ignore_hover and username:

                                # Functions for context menu
                                def permissions(*a):
                                    if constants.server_manager.current_server.acl:
                                        constants.server_manager.current_server.acl.get_rule(
                                            re.sub(r"\[.*?\]", "", username))
                                        utility.back_clicked = True
                                        utility.screen_manager.current = 'ServerAclScreen'
                                        utility.back_clicked = False

                                def copy(data_type: str, *a):
                                    try:
                                        player_info = constants.server_manager.current_server.run_data['player-list'][
                                            username]
                                        text = player_info[data_type]
                                        banner_text = f'Copied ${data_type.upper().replace("USER", "username")}$ to clipboard'

                                        Clock.schedule_once(
                                            functools.partial(
                                                utility.screen_manager.current_screen.show_banner,
                                                (0.85, 0.65, 1, 1),
                                                banner_text,
                                                "link-sharp.png",
                                                2,
                                                {"center_x": 0.5, "center_y": 0.965}
                                            ), 0
                                        )

                                        Clipboard.copy(text)

                                    except KeyError:
                                        pass

                                def kick(*a):
                                    constants.server_manager.current_server.acl.kick_player(username)

                                # Context menu buttons
                                self.context_options = [
                                    {'name': 'Copy username', 'icon': 'person.png',
                                     'action': functools.partial(copy, 'user')},
                                    {'name': 'Copy UUID', 'icon': 'id-card-sharp.png',
                                     'action': functools.partial(copy, 'uuid')},
                                    {'name': 'Copy IP', 'icon': 'wifi-sharp.png',
                                     'action': functools.partial(copy, 'ip')},
                                    {'name': 'Permissions', 'icon': 'shield-half-small.png', 'action': permissions},
                                    {'name': 'Kick player', 'icon': 'exit-sharp.png', 'action': kick, 'color': 'red'}
                                ]

                    def disable(self, boolean: bool, animate=False):
                        def disable(*a):
                            self.button.ignore_hover = boolean
                            utility.hide_widget(self, boolean)
                            utility.hide_widget(self.button, boolean)
                            self.button.disabled = boolean

                        if animate:
                            duration = 0.3

                            if not boolean:
                                disable()

                            self.opacity = (1 if boolean else 0)
                            Animation.stop_all(self)
                            Animation(opacity=(0 if boolean else 1), duration=duration).start(self)

                            if boolean:
                                Clock.schedule_once(disable, duration + 0.1)

                        else:
                            disable()

                    def check_anim(self, value):
                        animate = (self.name_value or value)
                        if self.parent:
                            panel = self.parent.parent.parent.parent
                            animate = animate and (panel.unq_hash['before'] != panel.unq_hash['after'])
                        self.disable(not bool(value), animate)

                    def __setattr__(self, attr, value):
                        super().__setattr__(attr, value)

                        # Change attributes dynamically based on rule
                        if attr == "text" and value:
                            # Update text
                            self.label.text = value.strip()

                            # Update font size
                            self.label.font_size = sp(
                                22 - (0 if len(self.label.text) < 11 else (len(self.label.text) // 3)))

                            # Update icon
                            def update_source(*a):
                                source = manager.get_player_head(value.strip())

                                def main_thread(*b):
                                    self.icon.source = source

                                Clock.schedule_once(main_thread, 0)

                            dTimer(0, update_source).start()

                        if attr == "text":
                            # self.check_anim(value)
                            self.disable(not bool(value), False)
                            self.name_value = value

                        if attr == "color" and value:
                            self.color_values = [(value[0], value[1], value[2], 0.75), value]
                            self.button.background_color = self.color_values[0]
                            label_color = Color(*self.color_values[1])
                            label_color.v -= 0.68
                            label_color.s += 0.05
                            self.label.color = label_color.rgba

                    def __init__(self, **kwargs):
                        super().__init__(**kwargs)

                        size = (215, 45)
                        name = 'player_label'
                        position = (0.5, 0.5)
                        self.name_value = None
                        self.color_values = [(0.8, 0.8, 0.8, 0), (1, 1, 1, 0)]

                        self.id = name
                        self.size_hint_max = size
                        self.size_hint_min = size

                        self.button = self.PlayerButton()
                        self.button.id = 'player_button'
                        self.button.border = (20, 20, 20, 20)
                        self.button.size_hint_max = size
                        self.button.size_hint_min = size
                        self.button.background_normal = os.path.join(paths.ui_assets, f'{self.button.id}.png')
                        self.button.background_down = os.path.join(paths.ui_assets, f'{self.button.id}.png')

                        self.label = AlignLabel()
                        self.label.__translate__ = False
                        self.label.halign = 'left'
                        self.label.valign = 'center'
                        self.label.id = 'label'
                        self.label.size_hint_max = size
                        self.label.pos_hint = {"center_x": position[0] + 0.18, "center_y": position[1] - 0.02}
                        self.label.text = name.upper()
                        self.label.font_size = sp(22)
                        self.label.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["bold"]}.ttf')
                        self.label.color = dark_accent

                        def on_touch_down(touch, *a):
                            super(Label, self.label).on_touch_down(touch)

                        self.label.on_touch_down = on_touch_down

                        # Button click behavior
                        def click_func(*a):
                            if not self.button.ignore_hover and self.label.text and self.button.last_touch.button == 'left':
                                if constants.server_manager.current_server.acl:
                                    constants.server_manager.current_server.acl.get_rule(
                                        re.sub(r"\[.*?\]", "", self.label.text))
                                    utility.back_clicked = True
                                    utility.screen_manager.current = 'ServerAclScreen'
                                    utility.back_clicked = False

                        def hover(enter=True, *a):
                            Animation.stop_all(self.button)
                            Animation.stop_all(self.hicon)
                            Animation(opacity=(0.25 if enter else 0), duration=0.12).start(self.hicon)
                            Animation(background_color=self.color_values[1 if enter else 0], duration=0.12).start(
                                self.button)

                        self.button.bind(on_press=click_func)
                        self.button.on_enter = functools.partial(hover, True)
                        self.button.on_leave = functools.partial(hover, False)
                        self.add_widget(self.button)

                        self.picon = Image()
                        self.picon.id = 'icon_placeholder'
                        self.picon.size_hint_max_y = size[1]
                        self.picon.pos_hint = {'center_x': 0.09}
                        self.picon.source = os.path.join(paths.ui_assets, 'steve.png')
                        self.add_widget(self.picon)

                        self.icon = AsyncImage()
                        self.icon.anim_delay = utility.anim_speed * 0.02
                        self.icon.id = 'icon'
                        self.icon.nocache = False
                        self.icon.size_hint_max_y = size[1]
                        self.icon.pos_hint = {'center_x': 0.09}
                        self.icon.source = os.path.join(paths.ui_assets, 'steve.png')
                        self.add_widget(self.icon)

                        self.hicon = Image()
                        self.hicon.id = 'icon_highlight'
                        self.hicon.size_hint_max_y = size[1]
                        self.hicon.pos_hint = {'center_x': 0.09}
                        self.hicon.source = os.path.join(paths.ui_assets, 'head_highlight.png')
                        self.hicon.opacity = 0
                        self.add_widget(self.hicon)

                        self.add_widget(self.label)

                self.background = PanelFrame()
                self.add_widget(self.background)

                self.current_players = None
                self.padding = 10

                # List layout
                self.layout = RelativeLayout()
                self.layout.opacity = 0
                self.layout_bg = Image(source=os.path.join(paths.ui_assets, 'performance_panel_background.png'))
                self.layout_bg.allow_stretch = True
                self.layout_bg.keep_ratio = False
                self.layout_bg.color = constants.brighten_color(panel_background, -0.015)
                self.layout.add_widget(self.layout_bg)

                # Player layout
                self.scroll_layout = RecycleViewWidget(position=None, view_class=PlayerLabel)
                self.scroll_layout.always_overscroll = False
                self.scroll_layout.scroll_wheel_distance = dp(50)
                self.player_list = RecycleGridLayout(size_hint_y=None, default_size=(240, 50),
                                                     padding=[self.padding, 3, self.padding, -20], spacing=[0, 8])
                self.player_list.bind(minimum_height=self.player_list.setter('height'))
                self.scroll_layout.add_widget(self.player_list)
                self.layout.add_widget(self.scroll_layout)
                self.add_widget(self.layout)

                # List shadow
                self.layout_shadow = Image(source=os.path.join(paths.ui_assets, 'performance_panel_shadow.png'))
                self.layout_shadow.allow_stretch = True
                self.layout_shadow.keep_ratio = False
                self.layout.add_widget(self.layout_shadow)

                # Player title
                self.title = ShadowLabel(
                    text=f'connected players',
                    font=os.path.join(paths.ui_assets, 'fonts', constants.fonts["italic"]),
                    size=sp(23),
                    color=normal_accent,
                    offset=3,
                    align='center',
                    shadow_color=constants.brighten_color(dark_accent, 0.04)
                )
                self.title.pos_hint = {'center_x': 0.5}
                self.title.y = 170
                self.add_widget(self.title)

                # Empty label
                self.empty_label = ShadowLabel(
                    text=f'*crickets*',
                    font=os.path.join(paths.ui_assets, 'fonts', constants.fonts["italic"]),
                    size=sp(24),
                    color=gray_accent,
                    offset=3,
                    align='center',
                    shadow_color=(0, 0, 0, 0)
                )
                self.empty_label.pos_hint = {'center_x': 0.5}
                self.empty_label.y = 95
                self.add_widget(self.empty_label)

                Clock.schedule_once(self.recalculate_size, 0)

        self.title_text = "Paragraph"
        self.size_hint = (None, None)
        self.size_hint_max = (None, None)
        self.pos_hint = {"center_x": 0.5}

        # Add widgets to layouts

        # Overview widget
        self.overview_widget = OverviewWidget(overview_min=self.overview_min)
        self.add_widget(self.overview_widget)

        # Player widget
        self.player_widget = PlayerWidget()
        self.add_widget(self.player_widget)

        # Meter widgets
        self.meter_layout = RelativeLayout(size_hint_max_x=self.meter_min)
        self.cpu_meter = MeterWidget(meter_name='CPU', pos_hint={'center_y': 0.684}, meter_min=self.meter_min)
        self.ram_meter = MeterWidget(meter_name='RAM', pos_hint={'center_y': 0.316}, meter_min=self.meter_min)
        self.meter_layout.add_widget(self.ram_meter)
        self.meter_layout.add_widget(self.cpu_meter)
        self.add_widget(self.meter_layout)

        self.bind(pos=self.update_rect)
        self.bind(size=self.update_rect)
        Clock.schedule_once(self.update_rect, 0)


class ConsolePanel(FloatLayout):

    # Update process to communicate with
    def update_process(self, run_data, *args):

        self.run_data = run_data

        # Close panel if telepath server closed immediately
        server_obj = constants.server_manager.current_server

        if server_obj._telepath_data:
            def check_for_crash(*a):
                data = server_obj._sync_telepath_stop(reset=False)
                if data['crash']:
                    server_obj.crash_log = data['crash']
                    self.update_text(data['log'])
                    self.reset_panel(data['crash'])

                    # Before closing, save contents to temp for view screen
                    constants.folder_check(paths.temp)
                    file_name = f"{server_obj._telepath_data['display-name']}, {server_obj.name}-latest.log"
                    with open(os.path.join(paths.temp, file_name), 'w+') as f:
                        f.write(json.dumps(data['log']))

            Clock.schedule_once(check_for_crash, 1)

        try:
            if self.update_text not in self.run_data['process-hooks']:
                self.run_data['process-hooks'].append(self.update_text)

            if self.reset_panel not in self.run_data['close-hooks']:
                self.run_data['close-hooks'].append(self.reset_panel)

            self.update_text(self.run_data['log'])

            def update_scroll(*args):
                if (self.console_text.height > self.scroll_layout.height - self.console_text.padding[-1]):
                    self.scroll_layout.scroll_y = 0

            Clock.schedule_once(update_scroll, 0)

        except KeyError:
            pass

    # Updates RecycleView text with console text
    def update_text(self, text, force_scroll=False, animate_last=True, *args):
        current_filter = self.filter_menu.current_filter
        self._unfiltered_text = text

        # Filterrrr oh yeah
        if current_filter != 'everything':
            event_whitelist = ['INIT', 'START', 'STOP', 'SUCCESS']

            if current_filter == 'errors':
                event_whitelist.extend(['WARN', 'ERROR', 'CRITICAL', 'SEVERE', 'FATAL'])

            elif current_filter == 'players':
                event_whitelist.extend(['CHAT', 'PLAYER'])

            elif current_filter == 'amscript':
                event_whitelist.extend(['AMS', 'EXEC'])

            text = [l for l in text if l['text'][1] in event_whitelist]

        original_scroll = self.scroll_layout.scroll_y
        original_len = len(self.scroll_layout.data)
        label_height = 41.8
        self.scroll_layout.data = text

        # Make the console sticky if scrolled to the bottom of the viewport
        viewport_size = self.scroll_layout.height - self.console_text.padding[-1] - self.console_text.padding[1]
        if (len(self.scroll_layout.data) * label_height > viewport_size) and (
                (original_scroll == 0 or not self.auto_scroll) or force_scroll):
            self.scroll_layout.scroll_y = 0
            self.auto_scroll = True


        # Temporary fix to prevent console text from moving when new data is added
        else:

            delta = self.scroll_layout.convert_distance_to_scroll(0, (
                        (len(self.scroll_layout.data) * label_height) * (1 - self.scroll_layout.scroll_y)) - (
                                                                              (original_len * label_height) * (
                                                                                  1 - original_scroll)))[1]
            if delta:
                final_scroll = self.scroll_layout.scroll_y + delta

                if final_scroll > 1:
                    final_scroll = 1
                elif final_scroll < 0:
                    final_scroll = 0

                self.scroll_layout.scroll_y = final_scroll

        def fade_animation(*args):
            for label in self.console_text.children:
                Animation.stop_all(label.anim_cover)
                Animation.stop_all(label.main_label)
                label.main_label.opacity = 1
                label.anim_cover.opacity = 0
                try:
                    if label.original_text == self.scroll_layout.data[-1]['text']:
                        label.main_label.opacity = 0
                        label.anim_cover.opacity = 1
                        Animation(opacity=1, duration=0.3).start(label.main_label)
                        Animation(opacity=0, duration=0.3).start(label.anim_cover)
                except:
                    pass

        if len(text) > original_len and animate_last:
            Clock.schedule_once(fade_animation, -1)

        # Update selection coordinates if they exist
        if self.last_self_touch:
            lst = self.last_self_touch
            self.last_self_touch = (lst[0], lst[1] + ((len(self.scroll_layout.data) - original_len) * label_height))

    # Fit background color across screen for transitions, and fix position
    def update_size(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

        self.scroll_layout.height = self.height - self.input.height
        self.scroll_layout.width = self.width
        self.scroll_layout.x = self.x
        self.scroll_layout.y = self.y + self.input.height

        self.console_text.width = self.width

        self.input.pos = (self.x, self.y)

        self.gradient.pos = (self.input.pos[0], self.pos[1] + (self.input.height * 1.2))
        self.gradient.width = self.scroll_layout.width - self.scroll_layout.bar_width
        self.gradient.height = 0 - (self.input.height * 0.5)

        self.input_background.pos = (self.pos[0] - 22, self.pos[1] + 8)

        # Corner resize
        offset = self.corner_size
        self.corner_mask.size_hint_max = (self.size[0] - offset, self.size[1] - offset)
        self.corner_mask.pos = (self.x + (offset / 2), self.y + (offset / 2))
        self.corner_mask.sl.size_hint_max_y = self.height - (self.corner_size * 2)
        self.corner_mask.sr.size_hint_max_y = self.height - (self.corner_size * 2)
        self.corner_mask.sb.size_hint_max_x = self.width - (self.corner_size * 2)
        self.corner_mask.st.size_hint_max_x = self.width - (self.corner_size * 2)

        # Console panel resize:
        texture = self.controls.background.texture_size
        self.controls.background.size_hint_max = (
        texture[0] + (self.height - texture[1]) + 200, texture[1] + (self.height - texture[1]))
        if self.full_screen == "animate":
            pass
        elif self.full_screen:
            self.size_hint_max = (Window.width, Window.height - self.full_screen_offset)
            self.y = 47
        else:
            self.size_hint_max = (Window.width - self.size_offset[0], Window.height - self.size_offset[1])
            self.y = self.default_y

        self.stop_click.size = self.size
        self.stop_click.pos = self.pos

        # Console controls resize
        self.controls.size = self.size
        self.controls.pos = self.pos

        shadow_size = self.controls.control_shadow.size
        self.controls.control_shadow.pos = (self.width - shadow_size[0], self.height - shadow_size[1])

        # Control buttons
        if self.controls.maximize_button and self.controls.stop_button and self.controls.restart_button and not self.full_screen:
            self.controls.view_button.pos = (self.width - 142, self.height - 80) if self.log_view else (
            self.width - 90, self.height - 80)
            self.controls.maximize_button.pos = (self.width - 90, self.height - 80)
            self.controls.stop_button.pos = (self.width - 142, self.height - 80)
            self.controls.restart_button.pos = (self.width - 194, self.height - 80)
            self.controls.filter_button.pos = (self.width - 246, self.height - 80)

        # Fullscreen shadow
        self.fullscreen_shadow.y = self.height + self.x - 3 + 25
        self.fullscreen_shadow.width = Window.width

        # Controls background
        def resize_background(*args):
            self.controls.background_ext.x = self.controls.background.width
            self.controls.background_ext.size_hint_max_x = self.width - self.controls.background.width

        Clock.schedule_once(resize_background, 0)

    # Launch server and update properties
    def launch_server(self, animate=True, wait_for_ip=True, *args):
        self.update_size()
        self.toggle_deadlock(False)
        self.selected_labels = []

        for k in self.parent._ignore_keys:
            if k == 'f':
                self.parent._ignore_keys.remove(k)

        anim_duration = 0.15 if animate else 0
        self.scroll_layout.scroll_y = 1
        self.auto_scroll = False

        # Animate panel
        self.controls.launch_button.disabled = True
        self.controls.log_button.disabled = True
        utility.hide_widget(self.controls.maximize_button, False)
        utility.hide_widget(self.controls.stop_button, False)
        utility.hide_widget(self.controls.restart_button, False)
        utility.hide_widget(self.controls.filter_button, False)
        self.controls.maximize_button.opacity = 0
        self.controls.stop_button.opacity = 0
        self.controls.restart_button.opacity = 0
        self.controls.filter_button.opacity = 0

        self.controls.crash_text.clear_text()

        if self.controls.view_button:
            Animation(opacity=0, duration=anim_duration).start(self.controls.view_button)
        Animation(opacity=0, duration=anim_duration).start(self.controls.button_shadow)
        Animation(opacity=0, duration=anim_duration).start(self.controls.background)
        Animation(opacity=0, duration=anim_duration).start(self.controls.background_ext)
        Animation(opacity=0, duration=(anim_duration * 1.5) if animate else 0).start(self.controls.launch_button)
        Animation(opacity=0, duration=(anim_duration * 1.5) if animate else 0).start(self.controls.log_button)

        def after_anim(*a):
            self.controls.maximize_button.disabled = False
            self.controls.stop_button.disabled = False
            self.controls.restart_button.disabled = False
            self.controls.filter_button.disabled = False
            self.controls.remove_widget(self.controls.launch_button)
            self.controls.remove_widget(self.controls.log_button)
            self.controls.remove_widget(self.controls.view_button)
            self.controls.launch_button.button.on_leave()
            self.controls.log_button.button.on_leave()
            self.controls.view_button.button.on_leave()

            def delay(function, obj, delay):
                def anim_delay(*a):
                    function.start(obj)

                Clock.schedule_once(anim_delay, delay)

            delay(Animation(opacity=1, duration=(anim_duration * 2.7) if animate else 0, transition='in_out_sine'),
                  self.controls.filter_button, 0.18)
            delay(Animation(opacity=1, duration=(anim_duration * 2.7) if animate else 0, transition='in_out_sine'),
                  self.controls.restart_button, 0.12)
            delay(Animation(opacity=1, duration=(anim_duration * 2.7) if animate else 0, transition='in_out_sine'),
                  self.controls.stop_button, 0.06)
            Animation(opacity=1, duration=(anim_duration * 2.7) if animate else 0, transition='in_out_sine').start(
                self.controls.maximize_button)

        # Update IP info at the top of the ServerViewScreen
        def update_launch_data(*args):
            if self.server_button: self.server_button.update_subtitle(self.run_data)

        Clock.schedule_once(update_launch_data, 3 if wait_for_ip else 1)
        if wait_for_ip:
            for x in range(6): Clock.schedule_once(update_launch_data, x * 5)

        # Show telepath banner when server is started remotely
        server_obj = constants.server_manager.current_server
        if wait_for_ip and server_obj._telepath_data:
            constants.api_manager.request(
                endpoint='/main/telepath_banner',
                host=server_obj._telepath_data['host'],
                port=server_obj._telepath_data['port'],
                args={'message': f"$Telepath$ action: Launched '${server_obj.name}$'", 'finished': True}
            )

        Clock.schedule_once(after_anim, (anim_duration * 1.51) if animate else 0)

        # Actually launch server
        def start_timer(*_):
            server_obj = utility.screen_manager.current_screen.server

            # Play sound
            if not server_obj.running: audio.player.play('interaction/launch_*', volume=0.85)

            if server_obj._telepath_data:
                boot_text = f"Connecting to '{server_obj._view_name}', please wait..."
            else:
                boot_text = f"Launching '{server_obj.name}', please wait..."

            text_list = [{'text': (
            dt.now().strftime(constants.fmt_date("%#I:%M:%S %p")).rjust(11), 'INIT', boot_text, (0.7, 0.7, 0.7, 1))}]

            if server_obj.proxy_enabled and server_obj.proxy_installed():
                text_list.append({'text': (
                dt.now().strftime(constants.fmt_date("%#I:%M:%S %p")).rjust(11), 'INFO', 'Initializing playit agent...',
                (0.6, 0.6, 1, 1))})

            self.update_text(text=text_list)
            while not all(server_obj._check_object_init().values()):
                time.sleep(0.05)

            self.update_process(utility.screen_manager.current_screen.server.launch())

            # Start performance counter
            try:
                utility.screen_manager.current_screen.set_timer(True)
            except AttributeError:
                pass

            self.input.disabled = False
            constants.server_manager.current_server.run_data['console-panel'] = self
            constants.server_manager.current_server.run_data['performance-panel'] = self.performance_panel

            # Update Discord rich presence
            constants.discord_presence.update_presence('Server Manager > Launch')

        dTimer(0, start_timer).start()

        # Show pop-up to ask user for initial user feedback
        try:
            if constants.app_config.prompt_feedback and constants.app_online:
                constants.app_config.prompt_feedback = False

                def open_feedback(*a):
                    url = "https://www.auto-mcs.com/feedback"
                    webbrowser.open_new_tab(url)

                Clock.schedule_once(
                    functools.partial(
                        utility.screen_manager.current_screen.show_popup,
                        "query",
                        "Share Your Feedback",
                        "Thanks for using $auto-mcs$!\n\nWhile your server is launching, please take a moment to leave us your feedback",
                        (None, dTimer(0, open_feedback).start)
                    ),
                    1
                )
        except:
            pass

    # Stop server
    def stop_server(self, *args):
        if self.run_data:
            utility.screen_manager.current_screen.server.stop()

        # Show deadlocked icon after stopping
        Clock.schedule_once(self.toggle_deadlock, 1)

    # Kills running process forcefully
    def kill_server(self, *args):
        if self.run_data:
            utility.screen_manager.current_screen.server.kill()

    # Restart server
    def restart_server(self, *args):
        if self.run_data and not self.deadlocked:
            utility.screen_manager.current_screen.server.restart()
            self.toggle_deadlock(False)

    # Called from ServerObject when process stops
    def reset_panel(self, crash=None):
        if self.server_obj.restart_flag:
            return

        def reset(*args):
            server_obj = constants.server_manager.current_server

            # Show crash banner if not on server screen
            def show_crash_banner(*args):
                if crash:
                    Clock.schedule_once(
                        functools.partial(
                            utility.screen_manager.current_screen.show_banner,
                            (1, 0.5, 0.65, 1),
                            f"'${self.server_name}$' has crashed",
                            "close-circle-sharp.png",
                            2.5,
                            {"center_x": 0.5, "center_y": 0.965}
                        ), 0
                    )

            # Ignore if screen isn't visible or a different server
            if not (utility.screen_manager.current_screen.name == 'ServerViewScreen'):
                show_crash_banner()

                # Update caption on list if user is staring at it for some reason
                if (utility.screen_manager.current_screen.name == 'ServerManagerScreen'):
                    for button in utility.screen_manager.current_screen.scroll_layout.children:
                        button = button.children[0]
                        if button.title.text.strip() == self.server_name:
                            button.update_subtitle(None, dt.now())
                            break
                return

            if utility.screen_manager.current_screen.server.name != self.server_name or not self.run_data:
                show_crash_banner()
                return

            # Do things when on server launch screen
            utility.screen_manager.current_screen.set_timer(False)
            utility.screen_manager.current_screen.performance_panel.reset_panel()
            try:
                if 'f' not in self.parent._ignore_keys:
                    self.parent._ignore_keys.append('f')

            # Return if parent is None-type (screen does not exist)
            except AttributeError:
                return

            # Before deleting run data, save log to a file
            if not server_obj._telepath_data:
                constants.folder_check(paths.temp)
                file_name = f"{server_obj.name}-latest.log"
                with open(os.path.join(paths.temp, file_name), 'w+') as f:
                    f.write(json.dumps(self.run_data['log']))

            self.run_data = None
            self.ignore_keypress = True

            if self.parent.server_button:
                self.parent.server_button.update_subtitle(self.run_data, dt.now())

            # Hide filter if it's visible
            if self.filter_menu.visible:
                self.filter_menu.hide()

            # Else, reset it back to normal
            def disable_buttons(*a):
                utility.hide_widget(self.controls.maximize_button, True)
                utility.hide_widget(self.controls.stop_button, True)
                utility.hide_widget(self.controls.restart_button, True)
                utility.hide_widget(self.controls.filter_button, True)
                self.controls.control_shadow.opacity = 0

            if self.full_screen:
                self.maximize(False)
                disable_buttons()

            def after_anim(*a):
                anim_speed = 0.15

                # Update crash widgets
                if crash:
                    self.controls.log_button.disabled = False
                    self.controls.log_button.opacity = 0
                    self.controls.add_widget(self.controls.log_button)
                    Animation(opacity=1, duration=anim_speed).start(self.controls.log_button)
                    self.controls.crash_text.update_text(f"Uh oh, '${self.server_name}$' has crashed", False)

                # Animate panel
                self.controls.launch_button.disabled = False
                self.input.disabled = True
                self.input.text = ''

                self.controls.launch_button.opacity = 0
                self.controls.add_widget(self.controls.launch_button)

                Animation(opacity=1, duration=anim_speed).start(self.controls.button_shadow)
                Animation(opacity=1, duration=anim_speed).start(self.controls.launch_button)
                Animation(opacity=1, duration=anim_speed).start(self.controls.background)
                Animation(opacity=1, duration=anim_speed).start(self.controls.background_ext)

                if self.controls.maximize_button.opacity > 0:
                    Animation(opacity=0, duration=anim_speed).start(self.controls.maximize_button)
                    Animation(opacity=0, duration=anim_speed).start(self.controls.stop_button)
                    Animation(opacity=0, duration=anim_speed).start(self.controls.restart_button)
                    Animation(opacity=0, duration=anim_speed).start(self.controls.filter_button)
                    Clock.schedule_once(disable_buttons, anim_speed * 1.1)

                def after_anim2(*a):
                    self.toggle_deadlock(False)
                    self.controls.maximize_button.disabled = False
                    self.controls.stop_button.disabled = False
                    self.controls.restart_button.disabled = False
                    self.controls.filter_button.disabled = False
                    self.scroll_layout.data = []
                    self.controls.control_shadow.opacity = 1

                    # View log button
                    self.add_log_button()

                    # Update Discord rich presence
                    constants.discord_presence.update_presence('Server Manager > Launch')

                Clock.schedule_once(after_anim2, (anim_speed * 1.51))

            Clock.schedule_once(after_anim, 1.5)

        Clock.schedule_once(reset, 0)

        # Prompt new server to enable automatic backups and updates
        if not crash and (self.server_obj.auto_update == 'prompt' or self.server_obj.backup._backup_stats[
            'auto-backup'] == 'prompt'):
            Clock.schedule_once(functools.partial(prompt_new_server, self.server_obj))

    # Toggles full screen on the console
    def maximize(self, maximize=True, *args):

        # Make sure the buttons exist
        if 'f' in self.parent._ignore_keys and maximize and not self.log_view or self.full_screen == 'animate':
            return

        try:
            test = self.controls.maximize_button.button.hovered
        except AttributeError:
            return

        anim_speed = 0.135
        self.full_screen = "animate"

        # Fix scrolling
        def fix_scroll(*a):
            if (self.console_text.height > self.scroll_layout.height):
                Animation(scroll_y=0, duration=anim_speed, transition='out_sine').start(self.scroll_layout)
            else:
                Animation(scroll_y=1, duration=anim_speed, transition='out_sine').start(self.scroll_layout)

        # Entering full screen
        if maximize:
            Animation(size_hint_max=(Window.width, Window.height - self.full_screen_offset), y=47, duration=anim_speed,
                      transition='out_sine').start(self)

            # If server is not running
            if self.log_view:

                # Hide log button
                self.controls.remove_widget(self.controls.view_button)
                del self.controls.view_button
                self.controls.view_button = IconButton('hide log', {}, (71, 150), (None, None), 'hide-log.png',
                                                       clickable=True, anchor='right',
                                                       force_color=self.button_colors['maximize'],
                                                       click_func=self.hide_log)
                self.controls.view_button.opacity = 0
                self.controls.add_widget(self.controls.view_button)

                # Filter button
                self.controls.remove_widget(self.controls.filter_button)
                del self.controls.filter_button
                self.controls.filter_button = IconButton('filter', {}, (123, 150), (None, None), 'filter-sharp.png',
                                                         clickable=True, anchor='right', text_offset=(9, 50),
                                                         force_color=self.button_colors['filter'],
                                                         click_func=self.filter_menu.show,
                                                         text_hover_color=(0.722, 0.722, 1, 1))
                self.controls.filter_button.opacity = 0
                self.controls.add_widget(self.controls.filter_button)

                def after_anim(*a):
                    self.full_screen = True
                    self.ignore_keypress = False
                    Animation(opacity=0, duration=(anim_speed * 0.1), transition='out_sine').start(self.corner_mask)
                    Animation(opacity=1, duration=(anim_speed * 0.1), transition='out_sine').start(
                        self.fullscreen_shadow)
                    Animation(opacity=1, duration=anim_speed, transition='out_sine').start(self.controls.view_button)
                    Animation(opacity=1, duration=anim_speed, transition='out_sine').start(self.controls.filter_button)

                Clock.schedule_once(after_anim, (anim_speed * 1.1))


            # If server is running
            else:

                # Full screen button
                self.controls.remove_widget(self.controls.maximize_button)
                del self.controls.maximize_button
                self.controls.maximize_button = IconButton('minimize', {}, (71, 150), (None, None), 'minimize.png',
                                                           clickable=True, anchor='right',
                                                           force_color=self.button_colors['maximize'],
                                                           click_func=functools.partial(self.maximize, False))
                self.controls.maximize_button.opacity = 0
                self.controls.add_widget(self.controls.maximize_button)

                # Stop server button
                self.controls.remove_widget(self.controls.stop_button)
                del self.controls.stop_button
                if not self.deadlocked:
                    self.controls.stop_button = IconButton('stop server', {}, (123, 150), (None, None),
                                                           'stop-server.png', clickable=True, anchor='right',
                                                           text_offset=(13, 50), force_color=self.button_colors['stop'],
                                                           click_func=self.stop_server,
                                                           text_hover_color=(0.85, 0.7, 1, 1))
                else:
                    self.controls.stop_button = IconButton('kill server', {}, (123, 150), (None, None),
                                                           'kill-server.png', clickable=True, anchor='right',
                                                           text_offset=(13, 50), force_color=self.button_colors['stop'],
                                                           click_func=self.kill_server,
                                                           text_hover_color=(0.85, 0.7, 1, 1))
                self.controls.stop_button.opacity = 0
                self.controls.add_widget(self.controls.stop_button)

                # Restart server button
                self.controls.remove_widget(self.controls.restart_button)
                del self.controls.restart_button
                self.controls.restart_button = IconButton('restart server', {}, (175, 150), (None, None),
                                                          'restart-server.png', clickable=True, anchor='right',
                                                          text_offset=(-25, 50), force_color=self.button_colors['stop'],
                                                          click_func=self.restart_server,
                                                          text_hover_color=(0.85, 0.7, 1, 1))
                self.controls.restart_button.opacity = 0
                self.controls.add_widget(self.controls.restart_button)

                # Filter button
                self.controls.remove_widget(self.controls.filter_button)
                del self.controls.filter_button
                self.controls.filter_button = IconButton('filter', {}, (227, 150), (None, None), 'filter-sharp.png',
                                                         clickable=True, anchor='right', text_offset=(9, 50),
                                                         force_color=self.button_colors['filter'],
                                                         click_func=self.filter_menu.show,
                                                         text_hover_color=(0.722, 0.722, 1, 1))
                self.controls.filter_button.opacity = 0
                self.controls.add_widget(self.controls.filter_button)

                def after_anim(*a):
                    self.full_screen = True
                    self.ignore_keypress = False
                    Animation(opacity=0, duration=(anim_speed * 0.1), transition='out_sine').start(self.corner_mask)
                    Animation(opacity=1, duration=(anim_speed * 0.1), transition='out_sine').start(
                        self.fullscreen_shadow)
                    Animation(opacity=1, duration=anim_speed, transition='out_sine').start(
                        self.controls.maximize_button)
                    Animation(opacity=1, duration=anim_speed, transition='out_sine').start(self.controls.stop_button)
                    Animation(opacity=1, duration=anim_speed, transition='out_sine').start(self.controls.restart_button)
                    Animation(opacity=1, duration=anim_speed, transition='out_sine').start(self.controls.filter_button)
                    fix_scroll()

                Clock.schedule_once(after_anim, (anim_speed * 1.1))


        # Exiting full screen
        else:
            Animation(size_hint_max=(Window.width - self.size_offset[0], Window.height - self.size_offset[1]),
                      y=self.default_y, duration=anim_speed, transition='out_sine').start(self)
            Animation(opacity=1, duration=(anim_speed * 0.1), transition='out_sine').start(self.corner_mask)
            Animation(opacity=0, duration=(anim_speed * 0.1), transition='out_sine').start(self.fullscreen_shadow)

            # Full screen button
            self.controls.remove_widget(self.controls.maximize_button)
            del self.controls.maximize_button
            self.controls.maximize_button = RelativeIconButton('maximize', {}, (20, 20), (None, None), 'maximize.png',
                                                               clickable=True, anchor='right', text_offset=(24, 80),
                                                               force_color=self.button_colors['maximize'],
                                                               click_func=functools.partial(self.maximize, True))
            self.controls.maximize_button.opacity = 0
            self.controls.add_widget(self.controls.maximize_button)

            # Stop server button
            self.controls.remove_widget(self.controls.stop_button)
            del self.controls.stop_button
            if not self.deadlocked:
                self.controls.stop_button = RelativeIconButton('stop server', {}, (20, 20), (None, None),
                                                               'stop-server.png', clickable=True, anchor='right',
                                                               text_offset=(8, 80),
                                                               force_color=self.button_colors['stop'],
                                                               click_func=self.stop_server,
                                                               text_hover_color=(0.85, 0.7, 1, 1))
            else:
                self.controls.stop_button = RelativeIconButton('kill server', {}, (20, 20), (None, None),
                                                               'kill-server.png', clickable=True, anchor='right',
                                                               text_offset=(8, 80),
                                                               force_color=self.button_colors['stop'],
                                                               click_func=self.kill_server,
                                                               text_hover_color=(0.85, 0.7, 1, 1))
            self.controls.stop_button.opacity = 0
            self.controls.add_widget(self.controls.stop_button)

            # Restart server button
            self.controls.remove_widget(self.controls.restart_button)
            del self.controls.restart_button
            self.controls.restart_button = RelativeIconButton('restart server', {}, (20, 20), (None, None),
                                                              'restart-server.png', clickable=True, anchor='right',
                                                              text_offset=(-30, 80),
                                                              force_color=self.button_colors['stop'],
                                                              click_func=self.restart_server,
                                                              text_hover_color=(0.85, 0.7, 1, 1))
            self.controls.restart_button.opacity = 0
            self.controls.add_widget(self.controls.restart_button)

            # Filter button
            self.controls.remove_widget(self.controls.filter_button)
            del self.controls.filter_button
            self.controls.filter_button = RelativeIconButton('filter', {}, (20, 20), (None, None), 'filter-sharp.png',
                                                             clickable=True, anchor='right', text_offset=(3, 80),
                                                             force_color=self.button_colors['filter'],
                                                             click_func=self.filter_menu.show,
                                                             text_hover_color=(0.722, 0.722, 1, 1))
            self.controls.filter_button.opacity = 0
            self.controls.add_widget(self.controls.filter_button)

            if not self.run_data:
                utility.hide_widget(self.controls.maximize_button, True)
                utility.hide_widget(self.controls.stop_button, True)
                utility.hide_widget(self.controls.restart_button, True)
                utility.hide_widget(self.controls.filter_button, True)

            def after_anim(*a):
                self.full_screen = False
                self.ignore_keypress = False
                if self.run_data:
                    self.update_size()
                    Animation(opacity=1, duration=anim_speed, transition='out_sine').start(
                        self.controls.maximize_button)
                    Animation(opacity=1, duration=anim_speed, transition='out_sine').start(self.controls.stop_button)
                    Animation(opacity=1, duration=anim_speed, transition='out_sine').start(self.controls.restart_button)
                    Animation(opacity=1, duration=anim_speed, transition='out_sine').start(self.controls.filter_button)
                fix_scroll()

            Clock.schedule_once(after_anim, (anim_speed * 1.1))

    # Toggles deadlock button visibility
    def toggle_deadlock(self, boolean=True):
        def main_thread(*a):
            self.deadlocked = boolean
            if boolean:
                self.controls.stop_button.change_data('kill-server.png', 'kill server', self.kill_server)
            else:
                self.controls.stop_button.change_data('stop-server.png', 'stop server', self.stop_server)

        Clock.schedule_once(main_thread, 0)

    # Opens crash log in auto-mcs logviewer
    def open_log(self, *args):
        server_obj = constants.server_manager.current_server
        title = None

        if server_obj._telepath_data:
            title = f'{server_obj._view_name}'

        view_file(server_obj.crash_log, title)
        self.controls.log_button.button.on_leave()
        self.controls.log_button.button.on_release()

    # Adds show/hide log button
    def add_log_button(self, *args):
        self.log_view = False
        self.input.hint_text = "enter command..."

        # Choose path based on server name
        server_obj = constants.server_manager.current_server
        if server_obj._telepath_data:
            log_name = f"{server_obj._telepath_data['display-name']}, {server_obj.name}-latest.log"
        else:
            log_name = f"{server_obj.name}-latest.log"

        # Before deleting run data, save log to a file
        constants.folder_check(paths.temp)
        file_path = os.path.join(paths.temp, log_name)
        if os.path.isfile(file_path):
            self.deselect_all()
            self.scroll_layout.data = []

            def change_later(*a):
                try:
                    with open(file_path, 'r') as f:
                        self._unfiltered_text = json.loads(f.read())
                        self.update_text(self._unfiltered_text)
                except Exception as e:
                    send_log(self.__class__.__name__, f"error loading 'latest.log': {constants.format_traceback(e)}",
                             'error')

            Clock.schedule_once(change_later, 0)

            self.controls.remove_widget(self.controls.view_button)
            del self.controls.view_button
            self.controls.view_button = RelativeIconButton('view log', {}, (20, 20), (None, None), 'view-log.png',
                                                           clickable=True, anchor='right', text_offset=(18, 80),
                                                           force_color=self.button_colors['maximize'],
                                                           click_func=self.show_log)
            self.controls.add_widget(self.controls.view_button)
            self.controls.view_button.opacity = 0
            Animation(opacity=1, duration=0.15).start(self.controls.view_button)
            self.update_size()

    # Shows previous console log in panel
    def show_log(self, *args):

        if self.run_data:
            return

        self.log_view = True

        self.controls.control_shadow.opacity = 0
        self.input.hint_text = "viewing last run..."
        self.controls.control_shadow.size_hint_max = (135, 120)
        self.selected_labels = []
        anim_speed = 0.15
        self.scroll_layout.scroll_y = 0
        self.auto_scroll = False

        Animation(opacity=0, duration=anim_speed).start(self.controls.view_button)
        Animation(opacity=0, duration=anim_speed).start(self.controls.crash_text)
        Animation(opacity=0, duration=anim_speed).start(self.controls.button_shadow)
        Animation(opacity=0, duration=anim_speed).start(self.controls.background)
        Animation(opacity=0, duration=anim_speed).start(self.controls.background_ext)
        Animation(opacity=0, duration=(anim_speed * 1.5)).start(self.controls.launch_button)
        Animation(opacity=0, duration=(anim_speed * 1.5)).start(self.controls.log_button)

        def after_anim(*a):
            self.controls.maximize_button.disabled = False
            self.controls.remove_widget(self.controls.launch_button)
            self.controls.remove_widget(self.controls.log_button)
            self.controls.launch_button.button.on_leave()
            self.controls.log_button.button.on_leave()
            Animation(opacity=1, duration=anim_speed).start(self.controls.control_shadow)

        Clock.schedule_once(after_anim, (anim_speed * 1.51))
        Clock.schedule_once(functools.partial(self.maximize, True), 0.2)

    # Hides previous console log in panel
    def hide_log(self, *args):

        self.selected_labels = []

        def after_anim(*a):
            anim_speed = 0.15

            # Update crash widgets
            if self.controls.crash_text.text.text.strip():
                self.controls.log_button.disabled = False
                self.controls.log_button.opacity = 0
                self.controls.add_widget(self.controls.log_button)
                Animation(opacity=1, duration=anim_speed).start(self.controls.log_button)
                Animation(opacity=1, duration=anim_speed).start(self.controls.crash_text)

            # Animate panel
            self.controls.launch_button.disabled = False
            self.input.disabled = True
            self.input.text = ''

            self.controls.launch_button.opacity = 0
            self.controls.add_widget(self.controls.launch_button)

            Animation(opacity=1, duration=anim_speed).start(self.controls.button_shadow)
            Animation(opacity=1, duration=anim_speed).start(self.controls.launch_button)
            Animation(opacity=1, duration=anim_speed).start(self.controls.background)
            Animation(opacity=1, duration=anim_speed).start(self.controls.background_ext)

            Clock.schedule_once(functools.partial(self.maximize, False), 0)

            if self.controls.view_button.opacity > 0:
                utility.hide_widget(self.controls.view_button, True)

            def after_anim2(*a):
                self.controls.view_button.disabled = False
                self.scroll_layout.data = []

                # View log button
                self.controls.control_shadow.size_hint_max = (255, 120)
                Clock.schedule_once(self.update_size, -1)
                self.add_log_button()

            Clock.schedule_once(after_anim2, (anim_speed * 1.51))

        Clock.schedule_once(after_anim, 0)

    # Select all ConsoleLabels
    def select_all(self):
        self.selected_labels = [x['text'] for x in self.scroll_layout.data]
        for label in self.console_text.children:
            Animation.stop_all(label.sel_cover)
            label.sel_cover.opacity = 0.2
        Clock.schedule_once(self.scroll_layout.refresh_from_layout, 0)

    # Deselect all selected ConsoleLabels
    def deselect_all(self):
        self.selected_labels = []
        for label in self.console_text.children:
            Animation.stop_all(label.sel_cover)
            Animation(opacity=0, duration=0.05).start(label.sel_cover)
        Clock.schedule_once(self.scroll_layout.refresh_from_layout, 0.1)

    # Format and copy all selected text to clipboard
    def copy_selection(self):
        if self.selected_labels:
            text = '\n'.join(
                [str(x[0].rjust(11) + ('[' + x[1] + ']').rjust(9) + ' >   ' + x[2]) for x in self.selected_labels])

            # Remove formatting from text
            if '[/color]' in text:
                text = re.sub(r'\[\/?color(=#\w+)?\]', '', text)
            if '§' in text:
                for code in constants.color_table.keys():
                    text = text.replace(code, '')
            Clipboard.copy(text)
            self.selected_labels = []

        # Animate to convey copying
        for label in self.console_text.children:
            if label.sel_cover.opacity > 0:
                Animation.stop_all(label.sel_cover)
                label.sel_cover.opacity = 0.4
                Animation(opacity=0, duration=0.2).start(label.sel_cover)
        Clock.schedule_once(self.scroll_layout.refresh_from_layout, 0.41)

    # Check for drag select
    def on_touch_down(self, touch):
        if touch.device == "wm_touch":
            touch.button = "left"

        # Copy when right-clicked
        if self.selected_labels and touch.button == "right":
            self.copy_selection()
            return True

        # Select code for a single ConsoleLabel is under "SelectCover.on_touch_down()"
        try:
            if touch.button == "left":
                self.last_self_touch = self.console_text.to_widget(*touch.pos)

        # Ignore invalid inputs from non-standard input devices
        except AttributeError:
            pass

        return super().on_touch_down(touch)

    # Check for drag select
    def on_touch_up(self, touch):
        self.last_self_touch = None
        return super().on_touch_up(touch)

    # Automatically scroll console_text when mouse is dragged on the top or bottom regions
    def scroll_region(self, top=True, last_touch=None):
        if not self.in_scroll_region:
            self.in_scroll_region = True
            scroll_padding = 50
            try:
                scroll_speed = (self.scroll_layout.height / len(self.scroll_layout.data)) / 1800
            except ZeroDivisionError:
                scroll_speed = 100
            last_touch.pos = self.to_widget(*Window.mouse_pos)

            if top:
                while (Window.mouse_pos[1] >= self.scroll_layout.y + (
                        self.scroll_layout.height - scroll_padding)) and self.last_self_touch:
                    def scroll_up(*a):
                        self.scroll_layout.scroll_y += scroll_speed

                    if self.scroll_layout.scroll_y < 1:
                        Clock.schedule_once(scroll_up, 0)
                        Clock.schedule_once(functools.partial(self.on_touch_move, last_touch), 0)
                    else:
                        self.scroll_layout.scroll_y = 1
                        break
                    time.sleep(0.01)

            else:
                while (self.scroll_layout.y + (scroll_padding * 2) >= Window.mouse_pos[
                    1] >= self.scroll_layout.y) and self.last_self_touch:
                    def scroll_down(*a):
                        self.scroll_layout.scroll_y -= scroll_speed

                    if self.scroll_layout.scroll_y > 0:
                        Clock.schedule_once(scroll_down, 0)
                        Clock.schedule_once(functools.partial(self.on_touch_move, last_touch), 0)
                    else:
                        self.scroll_layout.scroll_y = 0
                        break
                    time.sleep(0.01)

            self.in_scroll_region = False

    def on_touch_move(self, touch, *a):

        # Move the scrollbar when near the top or bottom to select more than the viewport
        scroll_padding = 50
        if (touch.dsy > 0) and (touch.pos[1] >= self.scroll_layout.y + (self.scroll_layout.height - scroll_padding)):
            dTimer(0, functools.partial(self.scroll_region, True, touch)).start()

        if (touch.dsy < 0) and (self.scroll_layout.y + (scroll_padding * 2) >= touch.pos[1] >= self.scroll_layout.y):
            dTimer(0, functools.partial(self.scroll_region, False, touch)).start()

        def is_between(y3):
            y1 = self.console_text.height - self.last_self_touch[1]
            y2 = self.console_text.height - self.console_text.to_widget(*touch.pos)[1]
            y3 = self.console_text.height - self.console_text.to_widget(*self.scroll_layout.to_parent(0, y3))[1] - 25
            return ((y1 <= y3 <= y2) or (y2 <= y3 <= y1)) and not (
                        touch.pos[0] > self.scroll_layout.x + (self.scroll_layout.width - self.scroll_layout.drag_pad))

        for widget in self.console_text.children:
            try:
                if is_between(widget.y) and widget.original_text not in self.selected_labels:

                    # Use Y delta to orient clipboard content
                    if touch.dsy > 0:
                        self.selected_labels.insert(0, widget.original_text)
                    else:
                        self.selected_labels.append(widget.original_text)
                    widget.sel_cover.opacity = 0.2

                elif (not is_between(widget.y)) and widget.original_text in self.selected_labels:
                    self.selected_labels.remove(widget.original_text)
                    widget.sel_cover.opacity = 0
            except:
                pass
        return super().on_touch_move(touch)

    def __init__(self, server_name, server_button=None, start_launched=False,
                 performance_panel: PerformancePanel = None, **kwargs):
        super().__init__(**kwargs)

        self.performance_panel = performance_panel

        self.server_name = server_name
        self.server_obj = None
        self.run_data = None
        self.server_button = server_button
        self.deadlocked = False
        self.log_view = False
        self.full_screen = False
        self.full_screen_offset = 95
        self.size_offset = (70, 550)
        self.ignore_keypress = False
        self.pos_hint = {"center_x": 0.5}
        self.default_y = 170
        self.y = self.default_y

        # Selection info
        self.selected_labels = []
        self.last_touch = None
        self.last_self_touch = None
        self.in_scroll_region = False

        self._unfiltered_text = []

        self.button_colors = {
            'maximize': [[(0.05, 0.08, 0.07, 1), (0.722, 0.722, 1, 1)], ''],
            'filter': [[(0.05, 0.08, 0.07, 1), (0.251, 0.251, 0.451, 1)], ''],
            'stop': [[(0.05, 0.08, 0.07, 1), (0.722, 0.722, 1, 1)], 'pink']
        }

        # Apply accent color if it's different
        screen_accent = utility.screen_manager.current_screen.accent_color

        # Stop clicks through the background
        class StopClick(FloatLayout):
            def on_touch_down(self, touch):
                if self.collide_point(*touch.pos):
                    return True
                else:
                    super().on_touch_down(touch)

        self.stop_click = StopClick()
        self.add_widget(self.stop_click)

        # Console line Viewclass for RecycleView
        class ConsoleLabel(RelativeLayout):

            def __setattr__(self, attr, value):
                # Change attributes dynamically based on rule
                if attr == "text" and value:
                    self.original_text = value
                    self.change_properties(value)

                super().__setattr__(attr, value)

            # Modifies rule attributes based on text content
            def change_properties(self, text):

                if not self.console_panel and constants.server_manager.current_server.run_data:
                    try:
                        self.console_panel = constants.server_manager.current_server.run_data['console-panel']
                    except KeyError:
                        pass

                if text and utility.screen_manager.current_screen.name == 'ServerViewScreen':

                    if not self.console_panel and not constants.server_manager.current_server.run_data:
                        try:
                            self.console_panel = utility.screen_manager.current_screen.console_panel
                        except:
                            pass

                    self.date_label.text = text[0]
                    self.type_label.text = text[1]
                    self.main_label.text = text[2]
                    type_color = text[3]

                    # Log text section formatting
                    width = utility.screen_manager.current_screen.console_panel.console_text.width
                    self.width = width
                    self.main_label.width = width - (self.section_size * 2) - 3
                    self.main_label.text_size = (width - (self.section_size * 2) - 3, None)
                    try:
                        self.main_label.texture_update()
                    except:
                        self.date_label.text = kivy.utils.escape_markup(text[0])
                        self.type_label.text = kivy.utils.escape_markup(text[1])
                        self.main_label.text = kivy.utils.escape_markup(text[2])
                        self.main_label.texture_update()
                    self.main_label.size = self.main_label.texture_size
                    self.main_label.size_hint_max_x = width - (self.section_size * 2) - 3
                    self.size_hint_max_x = width

                    # This is an extremely dirty and stinky fix for setting position and height
                    self.main_label.x = (width / 2) - 50 + (self.section_size) - 3

                    # def update_grid(*args):
                    #     self.main_label.texture_update()
                    #     self.size[1] = self.main_label.texture_size[1] + self.line_spacing
                    #
                    # Clock.schedule_once(update_grid, 0)

                    # Type & date label stuffies
                    self.date_label.x = 8
                    self.type_label.x = self.date_label.x + self.section_size - 6
                    self.type_banner.x = self.type_label.x - 7

                    if type_color:
                        self.main_label.color = type_color
                        self.date_label.color = self.type_label.color = constants.brighten_color(type_color, -0.65)
                        self.date_banner1.color = self.date_banner2.color = constants.brighten_color(type_color, -0.2)
                        self.type_banner.color = type_color

                        # Format selection color
                        if self.console_panel:
                            self.sel_cover.opacity = 0.2 if text in self.console_panel.selected_labels else 0
                        self.sel_cover.color = constants.brighten_color(type_color, 0.05)
                        self.sel_cover.width = self.width

            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.original_text = None
                self.console_panel = None
                self.line_spacing = 20
                self.font_size = sp(17)
                self.section_size = 110

                # Main text
                self.main_label = Label()
                self.main_label.__translate__ = False
                self.main_label.markup = True
                self.main_label.shorten = True
                self.main_label.shorten_from = 'right'
                self.main_label.font_size = sp(20)
                self.main_label.font_name = os.path.join(paths.ui_assets, 'fonts',
                                                         f'{constants.fonts["mono-bold"]}.otf')
                self.main_label.halign = 'left'
                self.add_widget(self.main_label)

                # Type label/banner
                self.type_banner = Image()
                self.type_banner.source = os.path.join(paths.ui_assets, 'console_banner.png')
                self.type_banner.allow_stretch = True
                self.type_banner.keep_ratio = False
                self.add_widget(self.type_banner)

                self.type_label = Label()
                self.type_label.__translate__ = False
                self.type_label.font_size = self.font_size
                self.type_label.font_name = os.path.join(paths.ui_assets, 'fonts',
                                                         f'{constants.fonts["mono-bold"]}.otf')
                self.add_widget(self.type_label)

                # Date label/banner
                self.date_banner1 = Image()
                self.date_banner1.source = os.path.join(paths.ui_assets, 'console_banner.png')
                self.date_banner1.allow_stretch = True
                self.date_banner1.keep_ratio = False
                self.add_widget(self.date_banner1)
                self.date_banner2 = Image()
                self.date_banner2.source = os.path.join(paths.ui_assets, 'console_banner.png')
                self.date_banner2.allow_stretch = True
                self.date_banner2.keep_ratio = False
                self.date_banner2.x = 27
                self.add_widget(self.date_banner2)

                self.date_label = Label()
                self.date_label.__translate__ = False
                self.date_label.font_size = self.font_size
                self.date_label.font_name = os.path.join(paths.ui_assets, 'fonts',
                                                         f'{constants.fonts["mono-medium"]}.otf')
                self.date_label.halign = 'left'
                self.add_widget(self.date_label)

                # Select cover for text selection
                class SelectCover(Image):

                    def on_touch_down(self, touch):
                        if self.collide_point(*touch.pos) and touch.button == 'left':
                            if self.parent:
                                for widget in self.parent.parent.children:
                                    widget.sel_cover.opacity = 0
                                try:
                                    if (self.parent.original_text in self.parent.console_panel.selected_labels) and (
                                            len(self.parent.console_panel.selected_labels) == 1):
                                        self.parent.console_panel.deselect_all()
                                    else:
                                        self.parent.console_panel.last_touch = touch.pos
                                        self.parent.console_panel.selected_labels = [self.parent.original_text]
                                        self.opacity = 0.2
                                        Clock.schedule_once(self.parent.console_panel.scroll_layout.refresh_from_layout,
                                                            0)
                                except:
                                    pass
                        else:
                            self.opacity = 0
                            return super().on_touch_down(touch)

                self.sel_cover = SelectCover()
                self.sel_cover.opacity = 0
                self.sel_cover.allow_stretch = True
                self.sel_cover.size_hint = (None, None)
                self.sel_cover.height = 42
                self.add_widget(self.sel_cover)

                # Cover for fade animation
                self.anim_cover = Image()
                self.anim_cover.opacity = 0
                self.anim_cover.allow_stretch = True
                self.anim_cover.size_hint = (None, None)
                self.anim_cover.width = self.section_size * 1.9
                self.anim_cover.height = self.section_size / 2.65
                self.anim_cover.color = background_color
                self.add_widget(self.anim_cover)

        # Command input at the bottom
        class ConsoleInput(TextInput):

            def _on_focus(self, instance, value, *largs):

                # Log for crash info
                if value:
                    try:
                        interaction = f"ConsoleInput (Sub-server {list(constants.server_manager.running_servers.keys()).index(self.parent.server_name) + 1})"
                        constants.last_widget = interaction + f" @ {constants.format_now()}"
                        send_log('navigation', f"interaction: '{interaction}'")
                    except:
                        pass

                # Update screen focus value on next frame
                def update_focus(*args):
                    utility.screen_manager.current_screen._input_focused = self.focus

                Clock.schedule_once(update_focus, 0)

                super(ConsoleInput, self)._on_focus(instance, value)
                Animation.stop_all(self.parent.input_background)
                Animation(opacity=0.9 if self.focus else 0.35, duration=0.2, step=0).start(self.parent.input_background)

            def __init__(self, **kwargs):
                super().__init__(**kwargs)

                self.original_text = ''
                self.history_index = 0

                self.multiline = False
                self.halign = "left"
                self.hint_text = "enter command..."

                self.hint_text_color = (0.6, 0.6, 1, 0.4)
                self.foreground_color = (0.6, 0.6, 1, 1)
                self.background_color = (0, 0, 0, 0)
                self.disabled_foreground_color = (0.6, 0.6, 1, 0.4)
                self.cursor_color = (0.55, 0.55, 1, 1)
                self.selection_color = (0.5, 0.5, 1, 0.4)

                self.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["mono-bold"]}.otf')
                self.font_size = sp(22)
                self.padding_y = (12, 12)
                self.padding_x = (70, 12)
                self.cursor_width = dp(3)

                self.bind(on_text_validate=self.on_enter)

            def tab_player(self, *a):
                player_list = [k for k, v in self.parent.server_obj.get_players().items() if v['logged-in']]

                if self.text.strip():
                    key = self.text.split(" ")[-1].lower()
                    if key not in player_list:
                        for player in player_list:
                            if self.text.endswith(" "):
                                self.text = self.text.strip() + " " + player
                                break

                            elif player.lower().startswith(key):
                                self.text = self.text[:-len(key)] + player
                                break

            def grab_focus(self, *a):
                def focus_later(*args):
                    self.focus = True

                Clock.schedule_once(focus_later, 0)

            def on_enter(self, value):

                # Move this to a proper send_command() function in svrmgr
                if self.parent.run_data:
                    self.parent.run_data['send-command'](self.text)
                    self.parent.update_text(self.parent.run_data['log'], force_scroll=True)

                self.original_text = ''
                self.history_index = 0

                self.text = ''
                self.grab_focus()

            # Input validation
            def insert_text(self, substring, from_undo=False):
                if utility.screen_manager.current_screen.popup_widget:
                    return None

                if not self.text and substring in [' ', '/']:
                    substring = ""

                if substring == "\t":
                    substring = ""

                else:
                    s = substring.replace("§", "[_color_]").encode("ascii", "ignore").decode().replace("\n",
                                                                                                       "").replace("\r",
                                                                                                                   "").replace(
                        "[_color_]", "§")
                    self.original_text = self.text + s
                    self.history_index = 0
                    return super().insert_text(s, from_undo=from_undo)

            # Manipulate command history
            def keyboard_on_key_down(self, window, keycode, text, modifiers):

                if self.parent.run_data:

                    if keycode[1] == "backspace" and control in modifiers:
                        original_index = self.cursor_col
                        new_text, index = constants.control_backspace(self.text, original_index)
                        self.select_text(original_index - index, original_index)
                        self.delete_selection()
                    else:
                        super().keyboard_on_key_down(window, keycode, text, modifiers)

                    if keycode[1] == "tab":
                        self.tab_player()

                    if keycode[1] == 'up' and self.parent.run_data['command-history']:
                        if self.text != self.original_text:
                            self.history_index += 1
                        if self.history_index > len(self.parent.run_data['command-history']) - 1:
                            self.history_index = len(self.parent.run_data['command-history']) - 1
                            if self.history_index < 0:
                                self.history_index = 0
                        self.text = self.parent.run_data['command-history'][self.history_index]


                    elif keycode[1] == 'down' and self.parent.run_data['command-history']:
                        self.history_index -= 1
                        if self.history_index < 0:
                            self.history_index = 0
                            self.text = self.original_text
                        else:
                            self.text = self.parent.run_data['command-history'][self.history_index]

        # Controls and background for console panel
        class ConsoleControls(RelativeLayout):
            def __init__(self, panel, **kwargs):
                super().__init__(**kwargs)
                self.panel = panel

                # Blurred background image
                self.background = Image()
                self.background.allow_stretch = True
                self.background.keep_ratio = False
                self.background.source = os.path.join(paths.ui_assets, f'console_preview_{randrange(3)}.png')
                self.background_ext = Image(size_hint_max=(None, None))
                self.add_widget(self.background_ext)
                self.add_widget(self.background)

                # Button shadow
                self.button_shadow = Image(pos_hint={'center_x': 0.5, 'center_y': 0.5})
                self.button_shadow.allow_stretch = True
                self.button_shadow.keep_ratio = False
                self.button_shadow.size_hint_max = (580, 250)
                self.button_shadow.source = os.path.join(paths.ui_assets, 'banner_shadow.png')
                self.add_widget(self.button_shadow)

                # Launch button
                self.launch_button = color_button("LAUNCH", position=(0.5, 0.5), icon_name='launch-server.png',
                                                  click_func=self.panel.launch_server,
                                                  hover_data={'color': (0.05, 0.05, 0.1, 1),
                                                              'image': os.path.join(paths.ui_assets,
                                                                                    'launch-button-hover.png')})
                self.launch_button.disabled = False
                self.add_widget(self.launch_button)

                # Open log button
                self.log_button = color_button("VIEW CRASH LOG", position=(0.5, 0.22),
                                               icon_name='document-text-outline-sharp.png',
                                               click_func=self.panel.open_log, color=(1, 0.65, 0.75, 1))
                self.log_button.disabled = False
                if constants.server_manager.current_server.crash_log:
                    self.add_widget(self.log_button)

                # Crash text
                self.crash_text = InputLabel(pos_hint={'center_y': 0.78})
                self.crash_text.text.text = ''
                self.add_widget(self.crash_text)
                if constants.server_manager.current_server.crash_log:
                    self.crash_text.update_text(f"Uh oh, '${self.panel.server_name}$' has crashed", False)

                # Button shadow in the top right
                self.control_shadow = Image()
                self.control_shadow.allow_stretch = True
                self.control_shadow.keep_ratio = False
                self.control_shadow.color = background_color
                self.control_shadow.source = os.path.join(paths.ui_assets, 'console_control_shadow.png')
                self.control_shadow.size_hint_max = (280, 120)
                self.add_widget(self.control_shadow)

                # Full screen button
                self.maximize_button = RelativeIconButton('maximize', {}, (20, 20), (None, None), 'maximize.png',
                                                          clickable=True, anchor='right', text_offset=(24, 80),
                                                          force_color=self.panel.button_colors['maximize'],
                                                          click_func=functools.partial(self.panel.maximize, True))
                utility.hide_widget(self.maximize_button)
                self.add_widget(self.maximize_button)

                # Stop server button
                self.stop_button = RelativeIconButton('stop server', {}, (20, 20), (None, None), 'stop-server.png',
                                                      clickable=True, anchor='right', text_offset=(8, 80),
                                                      force_color=self.panel.button_colors['stop'],
                                                      click_func=self.panel.stop_server,
                                                      text_hover_color=(0.85, 0.7, 1, 1))
                utility.hide_widget(self.stop_button)
                self.add_widget(self.stop_button)

                # Restart server button
                self.restart_button = RelativeIconButton('restart server', {}, (20, 20), (None, None),
                                                         'restart-server.png', clickable=True, anchor='right',
                                                         text_offset=(-30, 80),
                                                         force_color=self.panel.button_colors['stop'],
                                                         click_func=self.panel.restart_server,
                                                         text_hover_color=(0.85, 0.7, 1, 1))
                utility.hide_widget(self.restart_button)
                self.add_widget(self.restart_button)

                # Filter button
                self.filter_button = RelativeIconButton('filter', {}, (20, 20), (None, None), 'filter-sharp.png',
                                                        clickable=True, anchor='right', text_offset=(3, 80),
                                                        force_color=self.panel.button_colors['filter'],
                                                        click_func=self.panel.filter_menu.show,
                                                        text_hover_color=(0.722, 0.722, 1, 1))
                utility.hide_widget(self.filter_button)
                self.add_widget(self.filter_button)

                # View log button
                self.view_button = RelativeIconButton('view log', {}, (20, 20), (None, None), 'view-log.png',
                                                      clickable=True, anchor='right', text_offset=(18, 80),
                                                      force_color=self.panel.button_colors['maximize'],
                                                      click_func=functools.partial(self.panel.show_log, True))
                Clock.schedule_once(self.panel.add_log_button, 0)

        # Scrollable list for configuring console event filtering
        class FilterMenu(ContextMenu):

            def __init__(self, panel, **kwargs):
                super().__init__(**kwargs)
                self.panel = panel
                self.change_filter(constants.server_manager.current_server.console_filter)

            def change_filter(self, filter_type):
                if not filter_type:
                    filter_type = 'everything'

                self.current_filter = filter_type
                constants.server_manager.current_server.change_filter(filter_type)
                filter_button = None

                if self.panel.run_data or self.panel.log_view:
                    self.panel.update_text(self.panel._unfiltered_text)
                    filter_button = self.panel.controls.filter_button

                # Change filter icon colors
                filter_color = [[(0.05, 0.08, 0.07, 1), (0.6, 0.6, 1, 1)], '']
                default_color = [[(0.05, 0.08, 0.07, 1), (0.251, 0.251, 0.451, 1)], '']

                if filter_type == 'everything':
                    self.panel.button_colors['filter'] = default_color
                    if filter_button:
                        filter_button.button.color_id = default_color[0]
                        filter_button.button.on_leave()
                else:
                    self.panel.button_colors['filter'] = filter_color
                    if filter_button:
                        filter_button.button.color_id = filter_color[0]
                        filter_button.button.on_leave()

            def _change_options(self, options_list):
                self.options_list = options_list
                self._grid.clear_widgets()

                for item in self.options_list:
                    if not item: continue

                    selected = self.current_filter in item['name']

                    # Start of the list
                    if item == self.options_list[0]:
                        start_btn = self.ListButton(item, sub_id='list_start_button', selected=selected,
                                                    _menu_width=self.menu_width, _row_height=self.row_height)
                        self._grid.add_widget(start_btn)

                    # Middle of the list
                    elif item != self.options_list[-1]:
                        mid_btn = self.ListButton(item, sub_id='list_mid_button', selected=selected,
                                                  _menu_width=self.menu_width, _row_height=self.row_height)
                        self._grid.add_widget(mid_btn)

                    # Last button
                    else:
                        if 'color' in item:
                            sub_id = f'list_{item["color"]}_button'
                        else:
                            sub_id = 'list_end_button'
                        end_btn = self.ListButton(item, sub_id=sub_id, selected=selected, _menu_width=self.menu_width,
                                                  _row_height=self.row_height)
                        self._grid.add_widget(end_btn)

                # After rebuilding, ensure container height matches content and width tracks constraint
                self.height = self._grid.minimum_height

            def _update_pos(self):

                # Set initial position
                pos = (self.panel.x + self.panel.width - 220, self.panel.controls.y + self.panel.controls.height - 58)
                self._grid.x = pos[0]
                self._grid.y = pos[1] - self._grid.height
                Clock.schedule_once(self._round_top_left, 0)

                # Adjust auto-hide hitbox size/pos
                self._update_hitbox()

            def show(self):
                button_hidden = False
                try:
                    button_hidden = self.panel.controls.filter_button.opacity == 0
                except:
                    pass

                if self.visible or button_hidden:
                    self._hitbox.size_hint_max = (0, 0)
                    return self.hide()

                filters = [
                    {'name': 'everything', 'icon': 'reader.png', 'action': lambda *_: self.change_filter('everything')},
                    {'name': 'only errors', 'icon': 'warning.png', 'action': lambda *_: self.change_filter('errors')},
                    {'name': 'only players', 'icon': 'person.png', 'action': lambda *_: self.change_filter('players')},
                    {'name': 'amscript', 'icon': 'amscript.png', 'action': lambda *_: self.change_filter('amscript')}
                ]
                super().show(widget=self.panel.controls.filter_button.button, options_list=filters)

            def hide(self, animate=True, *args):
                Clock.schedule_once(self.widget.on_leave, 0.05)
                if self.visible: self.play_sound()

                if animate:
                    Animation(opacity=0, size_hint_max_x=150, duration=0.13, transition='in_out_sine').start(self)
                    for b in self._grid.children:
                        b.animate(False)
                    Clock.schedule_once(functools.partial(self._deselect_buttons), 0.14)
                    Clock.schedule_once(lambda *_: self._grid.clear_widgets(), 0.141)
                else:
                    self._grid.clear_widgets()

            def on_touch_down(self, touch):
                if self.visible:
                    if touch.button != 'right':
                        self.hide()
                        Clock.schedule_once(lambda *_: setattr(self, 'visible', False), 0.3)
                return FloatLayout.on_touch_down(self, touch)

        # Event filter
        self.filter_menu = FilterMenu(self)

        # Popen object reference
        self.scale = 1
        self.auto_scroll = False

        background_color = constants.brighten_color(constants.background_color, -0.1)

        # Background
        with self.canvas.before:
            self.color = Color(*background_color, mode='rgba')
            self.rect = Rectangle(pos=self.pos, size=self.size)

        with self.canvas.after:
            self.canvas.clear()

        # Text Layout
        self.scroll_layout = RecycleViewWidget(position=None, view_class=ConsoleLabel)
        self.scroll_layout.always_overscroll = False
        self.scroll_layout.scroll_wheel_distance = dp(50)
        self.console_text = RecycleGridLayout(size_hint_y=None, cols=1, default_size=(100, 42), padding=[0, 3, 0, 30])
        self.console_text.bind(minimum_height=self.console_text.setter('height'))
        self.scroll_layout.add_widget(self.console_text)
        self.scroll_layout.scroll_type = ['bars']
        self.add_widget(self.scroll_layout)

        # Log gradient
        self.gradient = Image()
        self.gradient.allow_stretch = True
        self.gradient.keep_ratio = False
        self.gradient.size_hint = (None, None)
        self.gradient.color = background_color
        self.gradient.opacity = 0.65
        self.gradient.source = os.path.join(paths.ui_assets, 'scroll_gradient.png')
        self.add_widget(self.gradient)

        # Command input
        self.input = ConsoleInput(size_hint_max_y=50)
        self.input.disabled = True
        self.add_widget(self.input)

        # Input icon
        self.input_background = Image()
        self.input_background.default_opacity = 0.35
        self.input_background.color = self.input.foreground_color
        self.input_background.opacity = self.input_background.default_opacity
        self.input_background.allow_stretch = True
        self.input_background.size_hint = (None, None)
        self.input_background.height = self.input.size_hint_max_y / 1.45
        self.input_background.source = os.path.join(paths.ui_assets, 'console_input_banner.png')
        self.add_widget(self.input_background)

        # Fullscreen shadow
        self.fullscreen_shadow = Image()
        self.fullscreen_shadow.allow_stretch = True
        self.fullscreen_shadow.keep_ratio = False
        self.fullscreen_shadow.size_hint_max = (None, 25)
        self.fullscreen_shadow.color = background_color
        self.fullscreen_shadow.opacity = 0
        self.fullscreen_shadow.source = os.path.join(paths.ui_assets, 'control_fullscreen_gradient.png')
        self.add_widget(self.fullscreen_shadow)

        # Start server/blurred background layout
        self.controls = ConsoleControls(self)
        self.add_widget(self.controls)
        self.controls.background_ext.color = background_color

        # Rounded corner mask
        self.corner_size = 30

        class Corner(Image):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.source = os.path.join(paths.ui_assets, 'console_border.png')
                self.color = screen_accent or constants.background_color
                self.allow_stretch = True
                self.keep_ratio = False

        class Side(Image):
            def __init__(self, vertical=True, **kwargs):
                super().__init__(**kwargs)
                self.source = os.path.join(paths.ui_assets,
                                           f'control_gradient_{"vertical" if vertical else "horizontal"}.png')
                self.allow_stretch = True
                self.keep_ratio = False

        self.corner_mask = RelativeLayout()
        self.corner_mask.tl = Corner(pos_hint={'center_x': 0, 'center_y': 1},
                                     size_hint_max=(self.corner_size, self.corner_size))
        self.corner_mask.tr = Corner(pos_hint={'center_x': 1, 'center_y': 1},
                                     size_hint_max=(-self.corner_size, self.corner_size))
        self.corner_mask.bl = Corner(pos_hint={'center_x': 0, 'center_y': 0},
                                     size_hint_max=(self.corner_size, -self.corner_size))
        self.corner_mask.br = Corner(pos_hint={'center_x': 1, 'center_y': 0},
                                     size_hint_max=(-self.corner_size, -self.corner_size))
        self.corner_mask.add_widget(self.corner_mask.tl)
        self.corner_mask.add_widget(self.corner_mask.tr)
        self.corner_mask.add_widget(self.corner_mask.bl)
        self.corner_mask.add_widget(self.corner_mask.br)

        self.corner_mask.sl = Side(pos_hint={'center_x': 0, 'center_y': 0.5}, size_hint_max=(self.corner_size, None),
                                   vertical=False)
        self.corner_mask.sr = Side(pos_hint={'center_x': 1, 'center_y': 0.5}, size_hint_max=(-self.corner_size, None),
                                   vertical=False)
        self.corner_mask.st = Side(pos_hint={'center_x': 0.5, 'center_y': 1}, size_hint_max=(None, self.corner_size))
        self.corner_mask.sb = Side(pos_hint={'center_x': 0.5, 'center_y': 0}, size_hint_max=(None, -self.corner_size))
        self.corner_mask.add_widget(self.corner_mask.sl)
        self.corner_mask.add_widget(self.corner_mask.sr)
        self.corner_mask.add_widget(self.corner_mask.st)
        self.corner_mask.add_widget(self.corner_mask.sb)

        self.add_widget(self.corner_mask)

        self.add_widget(self.filter_menu)

        self.bind(pos=self.update_size)
        self.bind(size=self.update_size)
        Clock.schedule_once(self.update_size, 0)

        if start_launched:
            Clock.schedule_once(functools.partial(self.launch_server, False, False), 0)


class ServerViewScreen(MenuBackground):

    # Fit background color across screen for transitions
    def update_rect(self, *args):

        # Hide context menu when screen is resized
        if self.context_menu:
            self.context_menu.hide(False)

        self.rect.pos = self.pos
        self.rect.size = self.size

        # Resize popup if it exists
        if self.popup_widget:
            self.popup_widget.resize()

        # Repos page switcher
        if self.page_switcher:
            self.page_switcher.resize_self()

        # Repos console panel and widgets
        if self.console_panel:
            Clock.schedule_once(self.console_panel.update_size, 0)
        if self.performance_panel:
            Clock.schedule_once(self.performance_panel.update_rect, 0)
        save_window_pos()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'
        self.server = None
        self.performance_panel = None
        self.console_panel = None
        self.menu_taskbar = None
        self.server_button = None
        self.server_button_layout = None
        self.perf_timer = None

        self.accent_color = None
        if self.accent_color:
            with self.canvas.before:
                self.color = Color(*self.accent_color, mode='rgba')
                self.rect = Rectangle(pos=self.pos, size=self.size)

    def set_timer(self, start=True):
        if start:
            try:
                if 'launch-time' in self.server.run_data:
                    self.performance_panel.player_clock = 6
                    Clock.schedule_once(self.performance_panel.refresh_data, 0.5)
                    self.perf_timer = Clock.schedule_interval(self.performance_panel.refresh_data, 1)
            except AttributeError:
                pass
        else:
            if self.perf_timer:
                self.perf_timer.cancel()
            self.perf_timer = None

    def on_pre_leave(self, **kwargs):
        self.set_timer(False)
        super().on_pre_leave(**kwargs)

    def on_pre_enter(self, **kwargs):
        super().on_pre_enter(**kwargs)
        self.set_timer(True)

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        # print('The key', keycode, 'have been pressed')
        # print(' - text is %r' % text)
        # print(' - modifiers are %r' % modifiers)

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
                            Clock.schedule_once(
                                functools.partial(self.popup_widget.window_input.do_cursor_movement, 'cursor_right',
                                                  True), 0)

                    new_str = self.popup_widget.window_input.keyboard.keycode_to_string(keycode[0])
                    if 'shift' in modifiers:
                        new_str = new_str.upper()
                    if len(new_str) == 1:
                        insert_text(new_str)
                    elif keycode[1] == 'spacebar':
                        insert_text(' ')
                    self.popup_widget.resize_window()
                else:
                    self.popup_widget.resize_window()
                return True

            if keycode[1] in ['escape', 'n']:
                try:
                    self.popup_widget.click_event(self.popup_widget, self.popup_widget.no_button)
                except AttributeError:
                    self.popup_widget.click_event(self.popup_widget, self.popup_widget.ok_button)

            elif keycode[1] in ['enter', 'return', 'y']:
                try:
                    self.popup_widget.click_event(self.popup_widget, self.popup_widget.yes_button)
                except AttributeError:
                    self.popup_widget.click_event(self.popup_widget, self.popup_widget.ok_button)
            return


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
                else:
                    self._shift_timer = Clock.schedule_once(self._reset_shift_counter, 0.25)  # Adjust time as needed
            return True

        # Ignore ESC commands while input focused
        if not self._input_focused and self.name == utility.screen_manager.current_screen.name:

            # Keycode is composed of an integer + a string
            # If we hit escape, release the keyboard
            # On ESC, click on back button if it exists
            if keycode[1] == 'escape' and 'escape' not in self._ignore_keys:

                if self.context_menu:
                    self.context_menu.hide()

                elif self.console_panel.log_view:
                    self.console_panel.hide_log()

                elif self.console_panel.full_screen:
                    self.console_panel.maximize(False)

                else:
                    for button in self.walk():
                        try:
                            if button.id == "exit_button":
                                button.force_click()
                                break
                        except AttributeError:
                            continue
                keyboard.release()

            # Start server when enter is pressed
            if (keycode[1] == 'enter' and 'enter' not in self._ignore_keys) and not self.server.run_data:
                if not self.console_panel.log_view:
                    self.console_panel.controls.launch_button.button.on_enter()
                    Clock.schedule_once(self.console_panel.launch_server, 0.1)

            # Use 'F' to toggle fullscreen
            if keycode[1] == 'f' and 'f' not in self._ignore_keys and self.server.run_data:
                if not self.console_panel.log_view:
                    self.console_panel.maximize(not self.console_panel.full_screen)
                    self.console_panel.ignore_keypress = True

            # Focus text input if server is started
            if (keycode[1] == 'tab' and 'tab' not in self._ignore_keys) and self.server.run_data:
                self.console_panel.input.grab_focus()

        # Capture keypress on current screen no matter what
        if self.name == utility.screen_manager.current_screen.name:

            # Copy selected console text
            if ((keycode[1] == 'c' and control in modifiers) and ('c' not in self._ignore_keys)) and (
                    self.server.run_data or self.console_panel.log_view):
                self.console_panel.copy_selection()

            # Select all console text
            if ((keycode[1] == 'a' and control in modifiers) and ('a' not in self._ignore_keys)) and (
                    self.server.run_data or self.console_panel.log_view):
                self.console_panel.select_all()

            # Deselect all console text
            if ((keycode[1] == 'd' and control in modifiers) and ('d' not in self._ignore_keys)) and (
                    self.server.run_data or self.console_panel.log_view):
                self.console_panel.deselect_all()

            # Stop the server if it's currently running
            if ((keycode[1] == 'q' and control in modifiers) and (
                    'q' not in self._ignore_keys)) and self.server.run_data:
                stop_button = self.console_panel.controls.stop_button
                if stop_button.opacity == 1:
                    stop_button.button.trigger_action(0.1)

            # Quit on macOS
            elif constants.os_name == 'macos' and (keycode[1] == 'q' and control in modifiers):
                utility.app.attempt_to_close()

            # Restart the server if it's currently running
            if ((keycode[1] == 'r' and (control in modifiers and 'shift' in modifiers)) and (
                    'r' not in self._ignore_keys)) and self.server.run_data:
                restart_button = self.console_panel.controls.restart_button
                if restart_button.opacity == 1:
                    restart_button.button.trigger_action(0.1)

        # Return True to accept the key. Otherwise, it will be used by the system.
        return True

    def generate_menu(self, **kwargs):

        # If a new server is selected, animate the taskbar
        animate_taskbar = False
        try:
            if not self.server:
                animate_taskbar = True
            elif self.server.name != constants.server_manager.current_server.name:
                animate_taskbar = True
        except AttributeError:
            pass

        self.server = constants.server_manager.current_server

        # Generate buttons on page load
        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'

        # Check if updates are available
        update_banner = ""
        if self.server.auto_update == 'true':
            update_banner = self.server.update_string

        self.server_button = ServerButton(self.server, update_banner=update_banner, fade_in=0.3, view_only=True)
        grid_layout = GridLayout(cols=1, size_hint_max_x=None, padding=(0, 80, 0, 0))
        self.server_button_layout = ScrollItem()
        self.server_button_layout.add_widget(self.server_button)
        grid_layout.add_widget(self.server_button_layout)
        float_layout.add_widget(grid_layout)

        # Only add this off-screen for 'ESC' behavior
        buttons.append(ExitButton('Back', (0.5, -1), cycle=True))
        for button in buttons:
            float_layout.add_widget(button)

        float_layout.add_widget(generate_title(f"Server Manager: '{self.server.name}'"))
        float_layout.add_widget(generate_footer(f"{self.server.name}, Launch"))

        self.add_widget(float_layout)

        # Add ManuTaskbar
        self.menu_taskbar = MenuTaskbar(selected_item='launch', animate=animate_taskbar)
        self.add_widget(self.menu_taskbar)

        # Add performance panel
        perf_layout = ScrollItem()
        if self.server.run_data and 'performance-panel' in self.server.run_data and self.server.run_data[
            'performance-panel']:
            self.performance_panel = self.server.run_data['performance-panel']
            try:
                if self.performance_panel.parent:
                    self.performance_panel.parent.remove_widget(self.performance_panel)
            except AttributeError:
                pass
        else:
            self.performance_panel = PerformancePanel(self.server.name)
        perf_layout.add_widget(self.performance_panel)
        self.add_widget(perf_layout)

        # Add ConsolePanel
        if self.server.run_data and 'console-panel' in self.server.run_data and 'log' in self.server.run_data and \
                self.server.run_data['console-panel']:
            self.console_panel = self.server.run_data['console-panel']
            self.console_panel.scroll_layout.data = []
            Clock.schedule_once(
                functools.partial(self.console_panel.update_text, self.server.run_data['log'], True, False), 0)
        else:
            self.console_panel = ConsolePanel(self.server.name, self.server_button, start_launched=self.server.running,
                                              performance_panel=self.performance_panel)

        self.add_widget(self.console_panel)
        self.console_panel.server_obj = self.server
