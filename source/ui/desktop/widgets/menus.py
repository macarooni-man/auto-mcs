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

    def __init__(self, name, position, options_list, input_name=None, x_offset=0, facing='left', custom_func=None, change_text=True, **kwargs):
        super().__init__(**kwargs)

        self.text_padding = 5
        self.facing = facing
        self.options_list = options_list

        self.x += 133 + x_offset

        self.button = HoverButton(hover_scale=1)
        self.id = self.button.id = 'drop_button' if facing == 'center' else f'drop_button_{self.facing}'
        self.button.color_id = [(0.05, 0.05, 0.1, 1), (0.6, 0.6, 1, 1)]

        self.button.size_hint_max = (182, 58)
        self.button.pos_hint = {"center_x": position[0], "center_y": position[1]}
        self.button.border = (0, 0, 0, 0)
        self.button.background_normal = os.path.join(paths.ui_assets, f'{self.id}.png')
        self.button.background_down = os.path.join(paths.ui_assets, f'{self.id}_click.png')

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
            else:
                self.button.on_mouse_pos(None, Window.mouse_pos)
                if self.button.hovered: self.button.on_enter()
                else:                   self.button.on_leave()

        self.text = Label()
        self.text.id = 'text'
        self.text.size_hint = (None, None)
        self.text.pos_hint = {"center_x": position[0], "center_y": position[1]}
        self.text.text = name.upper() + (" " * self.text_padding)
        self.text.font_size = sp(17)
        self.text.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["bold"]}.ttf')
        self.text.color = (0.6, 0.6, 1, 1)


        # Dropdown list
        class FadeDrop(DropDown):
            def dismiss(self, *largs):
                Animation(opacity=0, duration=0.13).start(self)
                super().dismiss(self, *largs)
                Clock.schedule_once(functools.partial(self.deselect_buttons), 0.15)

            def deselect_buttons(self, *args):
                for child in self.children:
                    for child_item in child.children:
                        for child_button in child_item.children:
                            if "button" in child_button.id:
                                child_button.on_leave()

        self.dropdown = FadeDrop()
        self.dropdown.id = 'dropdown'
        self.dropdown.opacity = 0
        self.dropdown.min_state_time = 0.13

        for item in self.options_list:

            # Middle of the list
            if item != self.options_list[-1]:
                mid_btn = self.list_button(item, sub_id='list_mid_button')
                self.dropdown.add_widget(mid_btn)

            # Last button
            else:
                end_btn = self.list_button(item, sub_id='list_end_button')
                self.dropdown.add_widget(end_btn)

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
        self.icon.pos = (195 + x_offset, 200)

        self.add_widget(self.icon)

    @staticmethod
    def play_sound(): return audio.player.play('interaction/step', jitter=0.1, pitch=0.7, volume=0.75)

    def change_text(self, text, translate=True):
        self.text.__translate__ = translate
        self.text.text = text.upper() + (" " * self.text_padding)

    # Create button in drop-down list
    def list_button(self, sub_name, sub_id, translate=True):

        sub_final = AnchorLayout()
        sub_final.id = sub_name
        sub_final.size_hint_y = None
        sub_final.height = 42 if "mid" in sub_id else 46

        background = Image()
        background.id = 'background'
        background.allow_stretch = True
        background.keep_ratio = False
        background.source = os.path.join(paths.ui_assets, f'{sub_id}.png')

        sub_button = TransparentListButton()
        sub_button.id = sub_id
        sub_button.color_id = [(0.05, 0.05, 0.1, 1), (0.6, 0.6, 1, 1)]

        sub_button.border = (0, 0, 0, 0)
        sub_button.background_normal = os.path.join(paths.ui_assets, 'icon_button.png')
        sub_button.background_down = os.path.join(paths.ui_assets, f'{sub_id}_click.png')

        sub_text = Label()
        sub_text.__translate__ = translate
        sub_text.id = 'text'
        sub_text.text = sub_name
        sub_text.font_size = sp(19)
        sub_text.padding_y = 100
        sub_text.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
        sub_text.color = (0.6, 0.6, 1, 1)

        sub_button.bind(on_release=lambda btn: self.dropdown.select(sub_name))

        sub_final.add_widget(background)
        sub_final.add_widget(sub_button)
        sub_final.add_widget(sub_text)

        return sub_final

    # Update list options
    def change_options(self, options_list):
        self.options_list = options_list
        self.dropdown.clear_widgets()

        for item in self.options_list:

            # Middle of the list
            if item != self.options_list[-1]:
                mid_btn = self.list_button(item, sub_id='list_mid_button')
                self.dropdown.add_widget(mid_btn)

            # Last button
            else:
                end_btn = self.list_button(item, sub_id='list_end_button')
                self.dropdown.add_widget(end_btn)

# Figure out where self.change_text is called, and add telepath icon to label
class TelepathDropButton(DropButton):
    def __init__(self, type, position, x_offset=0, facing='center', *args, **kwargs):
        FloatLayout.__init__(self, *args, **kwargs)
        telepath_data = constants.server_manager.online_telepath_servers

        if type == 'create':     name = 'create a server on'
        elif type == 'install':  name = 'install server on'
        elif type == 'clone':    name = 'clone server to'
        else:                    name = 'import server to'

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

        self.text_padding = 5
        self.facing = facing

        self.options_list = {'this machine': None}
        self.options_list.update(constants.deepcopy(telepath_data))

        self.x += 152 + x_offset

        self.button = HoverButton(hover_scale=1)
        self.id = self.button.id = 'drop_button' if facing == 'center' else f'drop_button_{self.facing}'
        self.button.color_id = [(0.05, 0.05, 0.1, 1), (0.6, 0.6, 1, 1)]

        self.button.size_hint_max = (200, 65)
        self.button.pos_hint = {"center_x": position[0], "center_y": position[1]}
        self.button.border = (0, 0, 0, 0)
        self.button.background_normal = os.path.join(paths.ui_assets, f'{self.id}.png')
        self.button.background_down = os.path.join(paths.ui_assets, f'{self.id}_click.png')

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
            else:
                self.button.on_mouse_pos(None, Window.mouse_pos)
                if self.button.hovered: self.button.on_enter()
                else:                   self.button.on_leave()

        self.text = Label()
        self.text.id = 'text'
        self.text.size_hint = (None, None)
        self.text.pos_hint = {"center_x": position[0], "center_y": position[1]}
        self.text.text = 'THIS MACHINE' + (" " * self.text_padding)
        self.text.font_size = sp(17)
        self.text.shorten = True
        self.text.shorten_from = 'right'
        self.text.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["bold"]}.ttf')
        self.text.color = (0.6, 0.6, 1, 1)

        # Dropdown list
        class FadeDrop(DropDown):
            def dismiss(self, *largs):
                Animation(opacity=0, duration=0.13).start(self)
                super().dismiss(self, *largs)
                Clock.schedule_once(functools.partial(self.deselect_buttons), 0.15)

            def deselect_buttons(self, *args):
                for child in self.children:
                    for child_item in child.children:
                        for child_button in child_item.children:
                            if "button" in child_button.id:
                                child_button.on_leave()

        self.dropdown = FadeDrop()
        self.dropdown.id = 'dropdown'
        self.dropdown.opacity = 0
        self.dropdown.min_state_time = 0.13

        items = self.options_list.items()
        send_log(self.__class__.__name__, f"using list of connected Telepath servers:\n{items}")
        for item, telepath_data in items:
            original_item = item

            # Set display name
            if telepath_data:
                telepath_data['host'] = item
                if telepath_data['nickname']:
                    item = telepath_data['nickname']

            # Middle of the list
            if original_item != list(self.options_list.keys())[-1]:
                mid_btn = self.list_button(item, sub_id='list_mid_button', translate=(original_item=='this machine'))
                self.dropdown.add_widget(mid_btn)

            # Last button
            else:
                end_btn = self.list_button(item, sub_id='list_end_button')
                self.dropdown.add_widget(end_btn)

        # Button click behavior
        def set_var(parent, result):
            for k, v in self.options_list.items():
                if (k == 'this machine' == result) or (v and (('.' in result and result == k) or (result == v['nickname']))):
                    foundry.new_server_info['_telepath_data'] = v
                    if type in ['import', 'clone']:
                        foundry.import_data['_telepath_data'] = v

                    # Change icon color
                    Animation.stop_all(parent.label_icon)
                    Animation(color=parent.color_id[0 if result == 'this machine' else 1], duration=0.2).start(parent.label_icon)

                    # Update name list if creating a server
                    try: utility.screen_manager.current_screen.name_input.get_server_list()
                    except: pass
                    try: utility.screen_manager.current_screen.name_input.update_server()
                    except: pass

                    break

        self.button.on_release = functools.partial(lambda: self.dropdown.open(self.button))
        self.dropdown.bind(on_select=lambda instance, x: self.change_text(x, translate=(x=='this machine')))
        self.dropdown.bind(on_select=lambda instance, x: set_var(self, x))

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
        self.icon.pos = (225 + x_offset, 200)

        self.add_widget(self.icon)


        if '_telepath_data' in foundry.new_server_info and foundry.new_server_info['_telepath_data']:
            self.label_icon.color = self.color_id[1]
            if foundry.new_server_info['_telepath_data']['nickname']:
                name = foundry.new_server_info['_telepath_data']['nickname']
            else:
                name = foundry.new_server_info['_telepath_data']['host']
            self.text.text = name.upper() + (" " * self.text_padding)



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
