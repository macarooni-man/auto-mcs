from source.ui.desktop.widgets.base import *



# ToggleButton override to ignore clicks when there's a popup
class ToggleButton(ToggleButton):
    def on_touch_down(self, touch):
        if not utility.screen_manager.current_screen.popup_widget: return super().on_touch_down(touch)


# Custom mobile-like UI switch for binary settings
class SwitchButton(FloatLayout):
    def __init__(self, name, position, default_state=True, x_offset=0, custom_func=None, disabled=False, **kwargs):
        super().__init__(**kwargs)

        # (Left, Right) (156.7 on left, 191 on right with border)
        self.knob_limits = (156.4 + x_offset, 193 + x_offset)
        bgc = constants.background_color
        self.color_id = [(bgc[0] - 0.021, bgc[1] - 0.021, bgc[2] - 0.021, bgc[3]), (0.6, 0.6, 1, 1)]
        self.name = name
        self.custom_func = custom_func

        self.x += 174 + x_offset

        self.button = button = ToggleButton(state='down' if default_state else 'normal')
        self.button.disabled = disabled
        self.button.id = 'toggle_button'
        self.button.pos_hint = {"center_x": position[0], "center_y": position[1]}
        self.button.size_hint_max = (82, 42)
        self.button.border = (0, 0, 0, 0)
        self.button.background_normal = os.path.join(paths.ui_assets, 'toggle_button.png')
        self.button.background_down   = os.path.join(paths.ui_assets, 'toggle_button_enabled.png')
        self.button.background_disabled_normal = self.button.background_normal
        self.button.bind(on_press=self.on_toggle)

        self.knob = knob = Image()
        self.knob.id = 'knob'
        self.knob.source = os.path.join(paths.ui_assets, f'toggle_button_knob{"_enabled" if default_state else ""}.png')
        self.knob.size = (30, 30)
        self.knob.pos_hint = {"center_y": position[1]}
        self.knob.x = self.knob_limits[1] if default_state else self.knob_limits[0]
        self.knob.color = self.color_id[0] if default_state else self.color_id[1]

        if disabled: self.opacity = 0.4

        self.add_widget(button)
        self.add_widget(knob)


    # When switch is toggled
    def on_toggle(self, *args):
        if self.disabled or utility.screen_manager.current_screen.popup_widget:
            return

        # Log for crash info
        try:
            interaction = "ToggleButton"
            if self.name: interaction += f" ({self.name})"
            constants.last_widget = interaction + f" @ {constants.format_now()}"
            send_log('navigation', f"interaction: '{interaction}'")
        except:
            pass

        state = args[0].state == "down"

        if self.custom_func: self.custom_func(state)


        # Change settings of ID
        elif self.name == "geyser_support":
            foundry.new_server_info['server_settings']['geyser_support'] = state

        elif self.name == 'chat_report':
            foundry.new_server_info['server_settings']['disable_chat_reporting'] = state

        elif self.name == "pvp":
            foundry.new_server_info['server_settings']['pvp'] = state

        elif self.name == "spawn_protection":
            foundry.new_server_info['server_settings']['spawn_protection'] = state

        elif self.name == "keep_inventory":
            foundry.new_server_info['server_settings']['keep_inventory'] = state

        elif self.name == "daylight_weather_cycle":
            foundry.new_server_info['server_settings']['daylight_weather_cycle'] = state

        elif self.name == "spawn_creatures":
            foundry.new_server_info['server_settings']['spawn_creatures'] = state

        elif self.name == "command_blocks":
            foundry.new_server_info['server_settings']['command_blocks'] = state



        # Play sassy sounds
        file_name = f'toggle_{"on" if state else "off"}'
        audio.player.play(f'interaction/{file_name}', jitter=(0, 0.125))

        # Animate sassy animations
        for child in args[0].parent.children:
            if child.id == "knob":
                Animation(x=self.knob_limits[1] if state else self.knob_limits[0], color=self.color_id[0] if state else self.color_id[1], duration=0.12).start(child)
                child.source = os.path.join(paths.ui_assets, f'toggle_button_knob{"_enabled" if state else ""}.png')
