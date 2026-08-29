from source.ui.desktop.widgets.buttons import HoverButton, animate_button
from source.ui.desktop.widgets.base import *



# For DropDownMenu, and ContextMenu
class TransparentListButton(HoverButton):
    def on_enter(self, *args, _no_bg_change: bool = False):
        if not self.ignore_hover:
            animate_button(self, image=os.path.join(paths.ui_assets, f'{self.id}_hover.png'), color=self.color_id[0], hover_action=True, do_scale=1)

    def on_leave(self, *args, _no_bg_change: bool = False):
        if not self.ignore_hover:
            animate_button(self, image=os.path.join(paths.ui_assets, 'icon_button.png'), color=self.color_id[1], hover_action=False, do_scale=1)

# Facing: left, right, center
class DropButton(FloatLayout):
    button_size = (182, 58)
    button_offset = 133
    icon_offset = 195
    dropdown_height = 300


    # Scrollable/fading dropdown
    class FadeDrop(RecycleView, DropDown):
        def __init__(self, view_class, max_height=300, **kwargs):
            super().__init__(**kwargs)

            self.id = 'dropdown'
            self.opacity = 0
            self.min_state_time = 0.13
            self.max_height = max_height

            self.do_scroll_x = False
            self.scroll_type = ['bars', 'content']
            self.bar_width = 5
            self.bar_margin = 3
            self.bar_color = (0.6, 0.6, 1, 1)
            self.bar_inactive_color = (0.6, 0.6, 1, 0.25)
            self.scroll_wheel_distance = dp(55)

            self.scroll_layout = RecycleGridLayout(cols=1, size_hint_y=None, default_size=(None, 42), default_size_hint=(1, None))
            self.scroll_layout.bind(minimum_height=self.scroll_layout.setter('height'))
            self.always_overscroll = False

            self.add_widget(self.scroll_layout)
            self.viewclass = view_class

            # Round the bottom of the dropdown viewport
            self.clip_radius = dp(22)

            with self.canvas.before:
                self.clip_push = StencilPush()
                self.clip_mask = RoundedRectangle()
                self.clip_use = StencilUse()

            with self.canvas.after:
                self.clip_unuse = StencilUnUse()
                self.clip_mask_end = RoundedRectangle()
                self.clip_pop = StencilPop()

            self.bind(pos=self.resize_clip, size=self.resize_clip)
            self.resize_clip()

        def resize_clip(self, *args):
            radius = min(self.clip_radius, self.height / 2)
            radii = [(0, 0), (0, 0), (radius, radius), (radius, radius)]

            self.clip_mask.pos = self.clip_mask_end.pos = self.pos
            self.clip_mask.size = self.clip_mask_end.size = self.size
            self.clip_mask.radius = self.clip_mask_end.radius = radii

        def dismiss(self, *largs):
            Animation(opacity=0, duration=0.13).start(self)
            super().dismiss(*largs)
            Clock.schedule_once(self.deselect_buttons, 0.15)

        def deselect_buttons(self, *args):
            for child in self.scroll_layout.children:
                child.button.state = 'normal'
                child.button.hovered = False
                child.button.on_leave()


    # Recycled option displayed inside FadeDrop
    class DropOption(AnchorLayout):
        def __setattr__(self, attr, value):

            # Update attributes dynamically based on RV data
            if attr == 'option_data':
                super().__setattr__(attr, value)

                if value and hasattr(self, 'button'):
                    self.change_data(value)

                return

            super().__setattr__(attr, value)

        def __init__(self, **kwargs):
            super().__init__(**kwargs)

            self.option_data = None
            self.size_hint_y = None

            self.background = Image()
            self.background.id = 'background'
            self.background.allow_stretch = True
            self.background.keep_ratio = False

            self.button = TransparentListButton()
            self.button.color_id = [(0.05, 0.05, 0.1, 1), (0.6, 0.6, 1, 1)]
            self.button.border = (0, 0, 0, 0)
            self.button.background_normal = os.path.join(paths.ui_assets, 'icon_button.png')
            self.button.bind(on_release=self.select)

            self.text = Label()
            self.text.id = 'text'
            self.text.font_size = sp(19)
            self.text.padding_y = 100
            self.text.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
            self.text.color = (0.6, 0.6, 1, 1)

            self.add_widget(self.background)
            self.add_widget(self.button)
            self.add_widget(self.text)

        def change_data(self, data):
            Animation.stop_all(self.button)
            Animation.stop_all(self.text)

            self.id = data['name']
            self.background.source = os.path.join(paths.ui_assets, f'{data["sub_id"]}.png')

            self.button.id = data['sub_id']
            self.button.state = 'normal'
            self.button.hovered = False
            self.button.ignore_hover = False
            self.button.background_color = (1, 1, 1, 1)
            self.button.background_normal = os.path.join(paths.ui_assets, 'icon_button.png')
            self.button.background_down = os.path.join(paths.ui_assets, f'{data["sub_id"]}_click.png')

            self.text.__translate__ = data['translate']
            self.text.text = data['name']
            self.text.color = (0.6, 0.6, 1, 1)

        def select(self, *args):
            if self.option_data:
                self.option_data['dropdown'].select(self.option_data['name'])


    def __init__(self, name, position, options_list, input_name=None, x_offset=0, facing='left', custom_func=None, change_text=True, **kwargs):
        super().__init__(**kwargs)

        self.text_padding = 5
        self.facing = facing
        self.options_list = options_list

        self.x += self.button_offset + x_offset

        self.button = HoverButton(hover_scale=1)
        self.id = self.button.id = 'drop_button' if facing == 'center' else f'drop_button_{self.facing}'
        self.button.color_id = [(0.05, 0.05, 0.1, 1), (0.6, 0.6, 1, 1)]

        self.button.size_hint_max = self.button_size
        self.button.pos_hint = {"center_x": position[0], "center_y": position[1]}
        self.button.border = (0, 0, 0, 0)
        self.button.background_normal = os.path.join(paths.ui_assets, f'{self.id}.png')
        self.button.background_down = os.path.join(paths.ui_assets, f'{self.id}_click.png')
        self.button.background_disabled_normal = os.path.join(paths.ui_assets, f'{self.id}_disabled.png')
        self.button.background_disabled_down = os.path.join(paths.ui_assets, f'{self.id}_disabled.png')

        # Change background when expanded - A
        def toggle_background(boolean, *args):
            self.play_sound()

            self.button.ignore_hover = boolean

            for child in self.button.parent.children:
                if child.id == 'icon':
                    Animation(height=-abs(child.init_height) if boolean else abs(child.init_height), duration=0.15).start(child)

            if boolean:
                Animation(opacity=1, duration=0.13).start(self.dropdown)
                self.button.background_normal = os.path.join(paths.ui_assets, f'{self.id}_expand.png')
                utility.screen_manager.current_screen.context_menu = self
            else:
                def _reset_hover(*a):
                    self.button.on_mouse_pos(None, Window.mouse_pos)
                    if self.button.hovered: self.button.on_enter()
                    else:                   self.button.on_leave()
                utility.screen_manager.current_screen.context_menu = None
                Clock.schedule_once(_reset_hover, 0)


        self.text = Label()
        self.text.id = 'text'
        self.text.size_hint = (None, None)
        self.text.pos_hint = {"center_x": position[0], "center_y": position[1]}
        self.text.text = name.upper() + (" " * self.text_padding)
        self.text.font_size = sp(17)
        self.text.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["bold"]}.ttf')
        self.text.color = (0.6, 0.6, 1, 1)


        # Dropdown list
        self.dropdown = self.FadeDrop(self.DropOption, self.dropdown_height)
        self.change_options(options_list)


        # Button click behavior
        def set_var(var, result):

            # Gamemode drop-down
            if var == 'ServerModeInput':
                foundry.new_server_info['server_settings']['gamemode'] = result
            elif var == 'ServerDiffInput':
                foundry.new_server_info['server_settings']['difficulty'] = result
            elif var == 'ServerLevelTypeInput':
                result = result.replace("normal", "default").replace("superflat", "flat").replace("large biomes", "large_biomes")
                foundry.new_server_info['server_settings']['level_type'] = result


        self.button.on_release = functools.partial(lambda: self.dropdown.open(self.button))

        if change_text:
            self.dropdown.bind(on_select=lambda instance, x: setattr(self.text, 'text', x.upper() + (" " * self.text_padding)))

        if custom_func: self.dropdown.bind(on_select=lambda instance, x: custom_func(x))
        else:           self.dropdown.bind(on_select=lambda instance, x: set_var(input_name, x))

        # Change background when expanded - B
        self.button.bind(on_release=functools.partial(toggle_background, True))
        self.dropdown.bind(on_dismiss=functools.partial(toggle_background, False))


        self.add_widget(self.button)
        self.add_widget(self.text)

        # dropdown arrow
        self.icon = Image()
        self.icon.id = 'icon'
        self.icon.source = os.path.join(paths.ui_assets, 'drop_arrow.png')
        self.icon.init_height = 14
        self.icon.size = (14, self.icon.init_height)
        self.icon.allow_stretch = True
        self.icon.keep_ratio = True
        self.icon.size_hint_y = None
        self.icon.color = (0.6, 0.6, 1, 1)
        self.icon.pos_hint = {"center_y": position[1]}
        self.icon.pos = (self.icon_offset + x_offset, 200)

        self.add_widget(self.icon)


    @staticmethod
    def play_sound(): return audio.player.play('interaction/step', jitter=0.1, pitch=0.7, volume=0.75)

    def hide(self, animate=True, *args):
        self.dropdown.dismiss()

    def change_text(self, text, translate=True):
        self.text.__translate__ = translate
        self.text.text = text.upper() + (" " * self.text_padding)

    # Override to customize option display
    def format_option(self, item):
        return item, True

    # Update list options
    def change_options(self, options_list):
        self.options_list = options_list
        options = list(self.options_list)
        data = []

        for index, item in enumerate(options):
            name, translate = self.format_option(item)
            sub_id = 'list_end_button' if index == len(options) - 1 else 'list_mid_button'

            data.append({
                'height': 46 if 'end' in sub_id else 42,
                'option_data': {
                    'name': name,
                    'sub_id': sub_id,
                    'translate': translate,
                    'dropdown': self.dropdown
                }
            })

        self.dropdown.data = data

# Figure out where self.change_text is called, and add telepath icon to label
class TelepathDropButton(DropButton):
    button_size = (200, 65)
    button_offset = 152
    icon_offset = 225


    # Format Telepath entries for the inherited RecycleView
    def format_option(self, item):
        telepath_data = self.options_list[item]

        if telepath_data:
            nickname = telepath_data['nickname']
            if nickname:
                duplicates = sum(1 for data in self.options_list.values() if data and data['nickname'] == nickname)
                if duplicates == 1: return nickname, False

            return item, False

        return item, True


    def __init__(self, type, position, x_offset=0, facing='center', *args, **kwargs):
        telepath_data = constants.server_manager.online_telepath_servers

        if type == 'create':     name = 'create a server on'
        elif type == 'install':  name = 'install server on'
        elif type == 'clone':    name = 'clone server to'
        else:                    name = 'import server to'

        options_list = {'this machine': None}
        options_list.update(constants.deepcopy(telepath_data))


        # Button click behavior
        def set_var(result):
            for k, v in self.options_list.items():
                if (k == 'this machine' == result) or (v and (result == k or result == v['nickname'])):
                    foundry.new_server_info['_telepath_data'] = v
                    if type in ['import', 'clone']:
                        foundry.import_data['_telepath_data'] = v

                    # Change icon color
                    Animation.stop_all(self.label_icon)
                    Animation(color=self.color_id[0 if result == 'this machine' else 1], duration=0.2).start(self.label_icon)

                    # Update name list if creating a server
                    try: utility.screen_manager.current_screen.name_input.get_server_list()
                    except: pass
                    try: utility.screen_manager.current_screen.name_input.update_server()
                    except: pass

                    break


        super().__init__('this machine', position, options_list, x_offset=x_offset, facing=facing, custom_func=set_var, change_text=False, *args, **kwargs)

        self.text.shorten = True
        self.text.shorten_from = 'right'
        self.dropdown.bind(on_select=lambda instance, x: self.change_text(x, translate=(x == 'this machine')))

        items = self.options_list.items()
        send_log(self.__class__.__name__, f"using list of connected Telepath servers:\n{items}")


        # Side label
        self.label_layout = RelativeLayout(pos_hint={"center_x": 0.5, "center_y": position[1]})
        self.label_layout.size_hint_max = (400, 40)
        self.label_layout.id = 'relative_layout'

        self.label = AlignLabel()
        self.label.halign = 'right'
        self.label.valign = 'center'
        self.label.id = 'label'
        self.label.size_hint_max = (300, 50)
        self.label.text = name
        self.label.x -= 210
        self.label.y += 2
        self.label.font_size = sp(25)
        self.label.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
        self.label.color = (0.6, 0.6, 1, 1)
        self.label_layout.add_widget(self.label)

        self.label_icon = Image(source=icon_path('telepath.png'))
        self.label_icon.size_hint_max = (35, 35)
        self.label_icon.allow_stretch = True
        self.label_icon.keep_ratio = False
        self.label_icon.pos = (self.label.x + 20, self.label.y + 3)

        self.color_id = [(0.2, 0.2, 0.4, 1), (0.65, 0.65, 1, 1)]
        self.label_icon.color = self.color_id[0]

        self.label_layout.add_widget(self.label_icon)
        self.add_widget(self.label_layout)


        # Restore selected Telepath server
        if '_telepath_data' in foundry.new_server_info and foundry.new_server_info['_telepath_data']:
            self.label_icon.color = self.color_id[1]

            if foundry.new_server_info['_telepath_data']['nickname']:
                name = foundry.new_server_info['_telepath_data']['nickname']
            else:
                name = foundry.new_server_info['_telepath_data']['host']

            self.text.text = name.upper() + (" " * self.text_padding)

# Drop-down + contextual install/delete action
class DropActionButton(DropButton):
    button_offset = 0
    icon_offset = 0
    dropdown_height = 250

    def __init__(self, options, select_func, **kwargs):
        super().__init__(
            '',
            (0.5, 0.5),
            options,
            facing = 'right',
            custom_func = select_func,
            change_text = False,
            **kwargs
        )

        self.size_hint = (None, None)
        self.size = self.button_size

        self.button.size_hint = (None, None)
        self.button.size = self.button_size
        self.button.pos_hint = {}

        self.text.pos_hint = {}
        self.icon.pos_hint = {}

        self.bind(pos=self.resize_button, size=self.resize_button)
        self.icon.bind(height=self.resize_button)
        Clock.schedule_once(self.resize_button, 0)

    def resize_button(self, *args):
        self.button.size = self.button_size
        self.button.center = self.center

        self.text.size = (self.width - 35, self.height)
        self.text.center = (self.center_x + 6, self.center_y)
        self.icon.center = (self.right - 25, self.center_y)

    def format_option(self, item):
        return str(item), False

class DropActionBar(RelativeLayout):

    def __init__(self, action_func=None, select_func=None, **kwargs):
        super().__init__(**kwargs)

        self.size_hint = (None, None)
        self.size = (242, 58)

        self.action_func = action_func
        self.select_func = select_func
        self.option_map = {}
        self.selected = None
        self.installed_version = None
        self.allow_remove = True
        self.action_mode = 'download'
        self.action_icon_name = 'download-sharp.png'
        self._loading = False

        self.dropdown = DropActionButton([], self.select_option)
        self.dropdown.pos = (0, 0)
        self.add_widget(self.dropdown)

        self.action_button = HoverButton(hover_scale=1)
        self.action_button.id = 'drop_action_button'
        self.action_button.size_hint = (None, None)
        self.action_button.size = (60, 58)
        self.action_button.pos = (182, 0)
        self.action_button.border = (0, 0, 0, 0)
        self.action_button.color_id = [(0.05, 0.05, 0.1, 1), (0.6, 0.6, 1, 1)]
        self.action_button.background_normal = os.path.join(paths.ui_assets, f'{self.action_button.id}.png')
        self.action_button.background_down = os.path.join(paths.ui_assets, f'{self.action_button.id}_click.png')
        self.action_button.background_disabled_normal = os.path.join(paths.ui_assets, f'{self.action_button.id}_disabled.png')
        self.action_button.background_disabled_down = os.path.join(paths.ui_assets, f'{self.action_button.id}_disabled.png')

        def action_enter(*args, duration=None, **kwargs):
            if not self.action_button.ignore_hover:
                animate_button(
                    self.action_button,
                    os.path.join(paths.ui_assets, f'{self.action_button.id}_hover{self.action_button.alt_color}.png'),
                    self.action_button.color_id[0],
                    True,
                    do_scale = 1,
                    duration = 0.12 if duration is None else duration
                )

        self.action_button.on_enter = action_enter
        self.action_button.bind(on_release=self.run_action)
        self.add_widget(self.action_button)

        self.action_icon = Image(
            source = icon_path(self.action_icon_name),
            size_hint = (None, None),
            size = (25, 25),
            color = (0.6, 0.6, 1, 1)
        )
        self.action_icon.id = 'icon'
        self.add_widget(self.action_icon)

        self.load_icon = AsyncImage(
            source = os.path.join(paths.ui_assets, 'animations', 'loading_pickaxe.gif'),
            size_hint = (None, None),
            size = (32, 32),
            allow_stretch = True,
            color = (0.6, 0.6, 1, 1),
            opacity = 0
        )
        self.load_icon.id = 'load_icon'
        self.load_icon.anim_delay = utility.anim_speed * 0.02
        self.add_widget(self.load_icon)

        self.bind(pos=self.resize_bar, size=self.resize_bar)
        Clock.schedule_once(self.resize_bar, 0)

    @staticmethod
    def _version_key(version):
        version = str(version or '').strip().lower()
        return version[1:] if version.startswith('v') else version

    @staticmethod
    def _release_version(release, fallback=None, display=False):
        return str(
            (getattr(release, 'display_version', None) if display else None) or
            getattr(release, 'addon_version', None) or
            getattr(release, 'version', None) or
            fallback or ''
        ).strip()

    def resize_bar(self, *args):
        self.dropdown.pos = (0, 0)
        self.action_button.pos = (182, 0)
        self.action_icon.center = self.load_icon.center = (self.action_button.center_x - 2, self.action_button.center_y)

    def set_data(self, options, selected=None, installed_version=None, allow_remove=True, action_icon='download-sharp.png'):
        self.option_map = {str(label): release for label, release in options}
        self.installed_version = installed_version
        self.allow_remove = allow_remove
        self.action_icon_name = action_icon

        labels = list(self.option_map)
        self.dropdown.change_options(labels)

        if selected not in self.option_map:
            selected = labels[0] if labels else None

        self.selected = selected

        if selected: self.dropdown.change_text(self._release_version(self.option_map[selected], selected, display=True), False)
        else:        self.dropdown.change_text('unavailable', False)

        self.dropdown.button.disabled = not bool(labels)
        self.refresh_action()

    def select_option(self, option):
        if option not in self.option_map:
            return

        self.selected = option
        release = self.option_map[option]

        self.dropdown.change_text(self._release_version(release, option, display=True), False)
        self.refresh_action()

        if self.select_func:
            self.select_func(release)

    def refresh_action(self):
        release = self.option_map.get(self.selected)
        selected_version = self._release_version(release, self.selected)

        is_installed = (
            self.allow_remove and
            self.installed_version and
            selected_version and
            self._version_key(selected_version) == self._version_key(self.installed_version)
        )

        self.action_mode = 'delete' if is_installed else 'download'
        self.action_button.alt_color = '_pink' if is_installed else ''
        self.action_button.color_id = (
            [(0.1, 0.05, 0.05, 1), (0.6, 0.6, 1, 1)]
            if is_installed else
            [(0.05, 0.05, 0.1, 1), (0.6, 0.6, 1, 1)]
        )
        self.action_button.background_down = os.path.join(paths.ui_assets, f'{self.action_button.id}_click{self.action_button.alt_color}.png')
        self.action_icon.source = icon_path('trash-sharp.png' if is_installed else self.action_icon_name)

        enabled = bool(release) and not self._loading
        self.action_button.disabled = not enabled

        if self._loading:
            self.action_icon.opacity = 0
            self.load_icon.opacity = 1
        else:
            self.action_icon.opacity = 1 if enabled else 0.35
            self.load_icon.opacity = 0

        self.action_button.on_leave(duration=0)
        if self.action_button.hovered and enabled:
            self.action_button.on_enter(duration=0)

    def loading(self, value):
        if value:
            for button in (self.dropdown.button, self.action_button):
                button.on_leave(duration=0)
                button.hovered = False
                button.state = 'normal'

        self._loading = value
        self.dropdown.button.disabled = value or not bool(self.option_map)
        self.refresh_action()

    def run_action(self, *args):
        if self._loading or not self.action_func or self.selected not in self.option_map:
            return

        self.action_func(self.option_map[self.selected], self.action_mode)



# Similar to DropButton, but for a right-click context menu
# Options are assigned from children of the HoverButton class:
# self.context_options = [{'name': 'Test option', 'icon': 'test-icon.png', 'action': self.do_something}]
class ContextMenu(FloatLayout):
    menu_width: int = 200
    row_height: int = 42

    # To hide the menu when the mouse drifts too far away
    class HitBox(FloatLayout, HoverBehavior):
        scale_factor = 2
        def __init__(self, _parent, **kwargs):
            super().__init__(**kwargs)
            self._parent = _parent
            self.id = 'list_hitbox_button'

        def on_leave(self, *a):
            if self._parent.visible:
                self._parent.hide()
                self._parent.visible = False

    class MenuGrid(GridLayout):
        pass

    class ListButton(RelativeLayout):
        def animate(self, fade_in=True, delay=0):
            def delay_anim(*a):
                Animation.stop_all(self.text)
                Animation.stop_all(self.icon)
                self.text.x = self.text_x
                self.icon.x = self.icon_x

                if fade_in:
                    self.text.x -= 15
                    self.icon.x -= 15
                    self.text.opacity = 0
                    self.icon.opacity = 0
                    Animation(opacity=1, x=self.text_x, duration=0.3, transition='out_sine').start(self.text)
                    Animation(opacity=1, x=self.icon_x, duration=0.3, transition='out_sine').start(self.icon)
                else:
                    Animation(opacity=0, duration=0.15).start(self.text)
                    Animation(opacity=0, x=self.icon_x-40, duration=0.15).start(self.icon)
            Clock.schedule_once(delay_anim, delay)

        def __init__(self, sub_data, sub_id, selected=False, _menu_width=None, _row_height=None, **kw):
            super().__init__(**kw)

            self.id = sub_data['name']
            self.size_hint_y = None
            self.height = _row_height if "mid" in sub_id else (_row_height + 4)
            self.width = _menu_width
            self.text_x = 0
            self.icon_x = 0
            self.selected = selected

            self.background = Image()
            self.background.id = 'background'
            self.background.allow_stretch = True
            self.background.keep_ratio = False
            self.background.source = os.path.join(paths.ui_assets, f'{sub_id}.png')

            self.button = TransparentListButton()
            self.button.id = sub_id
            self.button.height = self.height

            if sub_id == 'list_red_button':
                self.button.color_id = [(0.1, 0.07, 0.07, 1), (1, 0.6, 0.7, 1)]
            elif self.selected:
                self.button.color_id = [(0.05, 0.05, 0.1, 1), (0.76, 0.76, 1, 1)]
                self.background.color = (0.67, 0.67, 0.67, 1)
            else:
                self.button.color_id = [(0.05, 0.05, 0.1, 1), (0.6, 0.6, 1, 1)]

            self.button.border = (0, 0, 0, 0)
            self.button.background_normal = os.path.join(paths.ui_assets, 'icon_button.png')
            self.button.background_down = os.path.join(paths.ui_assets, f'{sub_id}_click.png')

            self.text = Label()
            self.text.id = 'text'
            self.text.opacity = 0
            self.text.text = sub_data['name']
            self.text.font_size = sp(19)
            self.text.padding_y = 100
            self.text.halign = 'left'
            self.text.x = 15
            self.text_x = self.text.x
            self.text.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
            self.text.color = self.button.color_id[1]

            def adjust_text(*a):
                self.text.text_size = (200, None)
                self.text.texture_update()
            Clock.schedule_once(adjust_text, 0)

            self.add_widget(self.background)
            self.add_widget(self.button)
            self.add_widget(self.text)

            self.icon = Image()
            if sub_data['icon']:
                self.icon.id = 'icon'
                self.icon.opacity = 0
                self.icon.source = icon_path(sub_data['icon'])
                self.icon.size_hint_max = (25, 25)
                self.icon.pos_hint = {'center_y': 0.5}
                self.icon.x = self.width - (self.icon.size_hint_max[0] * 1.5)
                self.icon_x = self.icon.x
                self.icon.allow_stretch = True
                self.icon.keep_ratio = False
                self.icon.color = self.button.color_id[1]
                self.add_widget(self.icon)

            if sub_data['action']:
                self.button.bind(on_press=sub_data['action'])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Inner grid that actually holds the menu items
        self._hitbox = self.HitBox(self)
        self._grid = self.MenuGrid(cols=1, spacing=(0, 0.01), size_hint=(None, None))
        # The grid's width follows the container; height follows its content
        self.bind(width=lambda *_: setattr(self._grid, 'width', self.width))
        self._grid.bind(minimum_height=lambda *_: setattr(self, 'height', self._grid.minimum_height))

        # Place the grid at (0,0) within this FloatLayout
        self._grid.pos = (0, 0)
        super().add_widget(self._hitbox)
        super().add_widget(self._grid)

        # Preserve public fields
        self.id = 'context_menu'
        self.options_list = None
        self.size_hint_max_x = 138
        self.opacity = 0
        self.visible = False
        self.rounded = False
        self.widget = None

        # Initialize sizes
        self.width = max(self.width, self._grid.minimum_width)
        self.height = max(self.height, self._grid.minimum_height)
        self._grid.width = self.width

    # Proxy GridLayout parameters
    @property
    def cols(self): return self._grid.cols
    @cols.setter
    def cols(self, v): self._grid.cols = v
    @property
    def spacing(self): return self._grid.spacing
    @spacing.setter
    def spacing(self, v): self._grid.spacing = v
    @property
    def minimum_height(self): return self._grid.minimum_height
    @property
    def minimum_width(self): return self._grid.minimum_width

    # Route external additions to the grid, keep the real widget tree valid
    def add_widget(self, widget, *args, **kwargs):
        if widget is self._grid:
            return super().add_widget(widget, *args, **kwargs)
        return self._grid.add_widget(widget, *args, **kwargs)

    def remove_widget(self, widget, *args, **kwargs):
        if widget is self._grid:
            return super().remove_widget(widget, *args, **kwargs)
        return self._grid.remove_widget(widget, *args, **kwargs)

    @staticmethod
    def play_sound(): return audio.player.play('interaction/step', jitter=0.1, pitch=0.7, volume=0.75)

    # Internals now read from self._grid.children
    def show(self, widget, options_list=None):
        self.widget = widget
        if options_list: self._change_options(options_list)
        self.visible = True
        self.play_sound()

        def wait(*a):
            self._update_pos()
            Animation(opacity=1, size_hint_max_x=200, duration=0.13, transition='in_out_sine').start(self)
            for x, b in enumerate(reversed(self._grid.children), 0): b.animate(True, (math.log(x + 1) / math.log(1.17)) / 70)
        Clock.schedule_once(wait, 0)

    def hide(self, animate=True, *args):
        Clock.schedule_once(self.widget.on_leave, 0.05)
        if self.visible: self.play_sound()
        self._hitbox.hovered = False

        def delete(*a):
            try:
                for widget in self.parent.children:
                    if "ContextMenu" in widget.__class__.__name__:
                        self.parent.context_menu = None
                        self.parent.remove_widget(widget)
            except AttributeError as e:
                send_log(self.__class__.__name__, f"failed to delete menu as the parent window doesn't exist: {constants.format_traceback(e)}", 'error')

        if animate:
            Animation(opacity=0, size_hint_max_x=150, duration=0.13, transition='in_out_sine').start(self)
            for b in self._grid.children: b.animate(False)
            Clock.schedule_once(functools.partial(self._deselect_buttons), 0.14)
            Clock.schedule_once(delete, 0.141)
        else: delete()

    def _deselect_buttons(self, *args):
        for child in self._grid.children: child.button.on_leave()

    def _round_top_left(self, *a):
        try:
            b = self._grid.children[-1]
            b.button.id = 'list_start_flip_button'
            b.background.source = os.path.join(paths.ui_assets, f'{b.button.id}.png')
            b.button.background_down = os.path.join(paths.ui_assets, f'{b.button.id}_click.png')
            b.button.on_leave()
        except IndexError: pass

    def _update_hitbox(self):
        hitbox_size = (self.menu_width, self.row_height * len(self.options_list))
        hitbox_pos  = (self._grid.x, self._grid.y - (hitbox_size[1] * 0.5))

        self._hitbox.size_hint_max = self._hitbox.size_hint_min = \
            (hitbox_size[0] * self._hitbox.scale_factor, hitbox_size[1] * self._hitbox.scale_factor)

        self._hitbox.pos = \
            (hitbox_pos[0] - (hitbox_size[0] / 2), hitbox_pos[1] - (hitbox_size[1] / 2))

    def _update_pos(self):
        pos = Window.mouse_pos
        edge_padding = 10

        # position the whole container under the cursor
        self._grid.x = pos[0]
        self._grid.y = pos[1] - self._grid.height

        off_y = pos[1] - self._grid.minimum_height - edge_padding
        if off_y <= 0:
            self._grid.y -= off_y
            Clock.schedule_once(self._round_top_left, 0)

        off_x = pos[0] + self.menu_width + edge_padding
        if off_x >= Window.width:
            self._grid.x = (Window.width - self.menu_width - edge_padding)
            Clock.schedule_once(self._round_top_left, 0)

        # Adjust auto-hide hitbox size/pos
        self._update_hitbox()

    def _change_options(self, options_list):
        self.options_list = options_list
        self._grid.clear_widgets()

        for item in self.options_list:
            if not item: continue

            if item == self.options_list[0]:
                start_btn = self.ListButton(item, sub_id='list_start_button', _menu_width=self.menu_width, _row_height=self.row_height)
                self._grid.add_widget(start_btn)

            elif item != self.options_list[-1]:
                mid_btn = self.ListButton(item, sub_id='list_mid_button', _menu_width=self.menu_width, _row_height=self.row_height)
                self._grid.add_widget(mid_btn)

            else:
                sub_id = f'list_{item["color"]}_button' if 'color' in item else 'list_end_button'
                end_btn = self.ListButton(item, sub_id=sub_id, _menu_width=self.menu_width, _row_height=self.row_height)
                self._grid.add_widget(end_btn)

        # After rebuilding, ensure container height matches content and width tracks constraint
        self.height = self._grid.minimum_height

    def on_touch_down(self, touch):
        if self.visible:
            if touch.button != 'right':
                self.hide()
                self.visible = False
        return super().on_touch_down(touch)
