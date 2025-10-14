from source.ui.desktop.widgets.base import *



# ToggleButton override to ignore clicks when there's a popup
class ToggleButton(ToggleButton):
    def on_touch_down(self, touch):
        if not utility.screen_manager.current_screen.popup_widget: return super().on_touch_down(touch)

def toggle_button(name, position, default_state=True, x_offset=0, custom_func=None, disabled=False):

    knob_limits = (156.4 + x_offset, 193 + x_offset) # (Left, Right) (156.7 on left, 191 on right with border)
    bgc = constants.background_color
    color_id = [(bgc[0] - 0.021, bgc[1] - 0.021, bgc[2] - 0.021, bgc[3]), (0.6, 0.6, 1, 1)]

    # When switch is toggled
    def on_active(button_name, *args):
        if disabled or utility.screen_manager.current_screen.popup_widget:
            return

        # Log for crash info
        try:
            interaction = "ToggleButton"
            if name: interaction += f" ({name})"
            constants.last_widget = interaction + f" @ {constants.format_now()}"
            send_log('navigation', f"interaction: '{interaction}'")
        except: pass

        state = args[0].state == "down"

        if custom_func: custom_func(state)

        # Change settings of ID
        elif button_name == "geyser_support":
            foundry.new_server_info['server_settings']['geyser_support'] = state
        elif button_name == 'chat_report':
            foundry.new_server_info['server_settings']['disable_chat_reporting'] = state
        elif button_name == "pvp":
            foundry.new_server_info['server_settings']['pvp'] = state
        elif button_name == "spawn_protection":
            foundry.new_server_info['server_settings']['spawn_protection'] = state
        elif button_name == "keep_inventory":
            foundry.new_server_info['server_settings']['keep_inventory'] = state
        elif button_name == "daylight_weather_cycle":
            foundry.new_server_info['server_settings']['daylight_weather_cycle'] = state
        elif button_name == "spawn_creatures":
            foundry.new_server_info['server_settings']['spawn_creatures'] = state
        elif button_name == "command_blocks":
            foundry.new_server_info['server_settings']['command_blocks'] = state


        # Play sassy sounds
        file_name = f'toggle_{"on" if state else "off"}'
        audio.player.play(f'interaction/{file_name}', jitter=(0, 0.125))

        # Animate sassy animations
        for child in args[0].parent.children:
            if child.id == "knob":
                Animation(x=knob_limits[1] if state else knob_limits[0], color=color_id[0] if state else color_id[1], duration=0.12).start(child)
                child.source = os.path.join(paths.ui_assets, f'toggle_button_knob{"_enabled" if state else ""}.png')

    final = FloatLayout()
    final.x += 174 + x_offset

    final.button = button = ToggleButton(state='down' if default_state else 'normal')
    button.id = 'toggle_button'
    button.pos_hint = {"center_x": position[0], "center_y": position[1]}
    button.size_hint_max = (82, 42)
    button.border = (0, 0, 0, 0)
    button.background_normal = os.path.join(paths.ui_assets, 'toggle_button.png')
    button.background_down = button.background_normal if disabled else os.path.join(paths.ui_assets, 'toggle_button_enabled.png')
    button.bind(on_press=functools.partial(on_active, name))

    final.knob = knob = Image()
    knob.id = 'knob'
    knob.source = os.path.join(paths.ui_assets, f'toggle_button_knob{"_enabled" if default_state else ""}.png')
    knob.size = (30, 30)
    knob.pos_hint = {"center_y": position[1]}
    knob.x = knob_limits[1] if default_state else knob_limits[0]
    knob.color = color_id[0] if default_state else color_id[1]

    if disabled: final.opacity = 0.4

    final.add_widget(button)
    final.add_widget(knob)
    return final
