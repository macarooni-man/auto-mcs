from source.ui.desktop.widgets.banners import *
from source.ui.desktop.widgets.base import *



# -------------------------------------------------  Helper Methods  ---------------------------------------------------

# Call function when any button is pressed
def button_action(button_name, button, specific_screen=''):

    # print(button_name)
    # print(button.button_pressed)

    if button.button_pressed == "left":

        if button_name.lower() == "quit":
            utility.app.attempt_to_close()

        elif button_name.lower() == "back":
            utility.back_clicked = True
            utility.screen_manager.previous_screen()
            utility.back_clicked = False

        elif button_name.lower() == "import":
            utility.screen_manager.current_screen.import_files()

        elif "manage" in button_name.lower() and "servers" in button_name.lower():
            utility.screen_manager.current = "ServerManagerScreen"

        # Return to main menu, prompt user if inside of progressive function
        elif "main menu" in button_name.lower():
            def return_to_main(*argies):
                utility.screen_manager.current = 'MainMenuScreen'

            # Warn user if creating server, or updating server etc...
            if ("CreateServer" in str(utility.screen_manager.current_screen) or "ServerImport" in str(utility.screen_manager.current_screen)) and 'Mode' not in str(utility.screen_manager.current_screen):
                utility.screen_manager.current_screen.show_popup(
                    "query",
                    "Main Menu",
                    "Would you like to return to the main menu?\n\nYour progress will not be saved",
                    [None, functools.partial(Clock.schedule_once, return_to_main, 0.25)])

            else: return_to_main()

        elif "create a new server" in button_name.lower():
            foundry.new_server_init()
            utility.screen_manager.current = 'CreateServerModeScreen'

        elif "import a server" in button_name.lower():
            foundry.new_server_init()
            utility.screen_manager.current = 'ServerImportScreen'

        elif "create new world instead" in button_name.lower():
            break_loop = False
            for item in utility.screen_manager.current_screen.children:
                if item.id == 'content':
                    for child_item in item.children:
                        if break_loop:
                            break
                        if child_item.__class__.__name__ == 'CreateServerWorldInput':
                            child_item.selected_world = foundry.new_server_info['server_settings']['world'] = 'world'
                            child_item.update_world(force_ignore=True)
                        elif child_item.__class__.__name__ == 'ServerWorldInput':
                            child_item.selected_world = utility.screen_manager.current_screen.new_world = 'world'
                            child_item.update_world(force_ignore=True)


        # Main menu reconnect button
        elif "no connection" in button_name.lower():
            try:
                constants.check_app_updates()
                foundry.find_latest_mc()
            except: pass
            utility.screen_manager.current_screen.reload_menu()


        elif "CreateServerNetwork" in str(utility.screen_manager.current_screen):
            if "access control" in button_name.lower():
                if not foundry.new_server_info['acl_object']:
                    while not foundry.new_server_info['acl_object']:
                        time.sleep(0.2)
                utility.screen_manager.current = 'CreateServerAclScreen'


        elif "add rules" in button_name.lower() and "CreateServerAclScreen" in str(utility.screen_manager.current_screen):
            utility.screen_manager.current = 'CreateServerAclRuleScreen'

        elif "add rules" in button_name.lower() and "ServerAclScreen" in str(utility.screen_manager.current_screen):
            utility.screen_manager.current = 'ServerAclRuleScreen'

        elif "add rules" in button_name.lower() and "ServerAclRuleScreen" in str(utility.screen_manager.current_screen):
            utility.screen_manager.current_screen.apply_rules()


        elif "CreateServerOptions" in str(utility.screen_manager.current_screen) or "CreateServerAddon" in str(utility.screen_manager.current_screen):

            # If creating a new server, use CreateServerAddonScreen
            if "add-on manager" in button_name.lower():
                utility.screen_manager.current = 'CreateServerAddonScreen'

            elif "download" in button_name.lower():
                utility.screen_manager.current = 'CreateServerAddonSearchScreen'


        elif "ServerAddonScreen" in str(utility.screen_manager.current_screen):
            if "download" in button_name.lower():
                utility.screen_manager.current = 'ServerAddonSearchScreen'


        elif "ServerAmscriptScreen" in str(utility.screen_manager.current_screen):
            script_manager = constants.server_manager.current_server.script_manager

            if "download" in button_name.lower():
                utility.screen_manager.current = 'ServerAmscriptSearchScreen'

            elif "create new" in button_name.lower():
                utility.screen_manager.current = 'CreateAmscriptScreen'


        elif "ServerBackupScreen" in str(utility.screen_manager.current_screen) and "restore" in button_name.lower():
            utility.screen_manager.current = "ServerBackupRestoreScreen"

        elif "ServerBackupScreen" in str(utility.screen_manager.current_screen) and "download" in button_name.lower():
            utility.screen_manager.current = "ServerBackupDownloadScreen"


        elif "CreateServerReview" in str(utility.screen_manager.current_screen) and "create server" in button_name.lower():
            utility.screen_manager.current = "CreateServerProgressScreen"



# --------------------------------------------  Base Button Functionality  ---------------------------------------------

def animate_background(self, image, hover_action, do_scale=default_scale, _new_color: tuple = None, _no_bg_change: bool = False):
    if getattr(self, '_anim', False): self._anim.stop(self)

    scale = do_scale
    scale_widget = self.parent

    if do_scale:
        if hover_action and not getattr(scale_widget, '_hover_scale', None):

            # Store instructions on the widget to remove them later
            with scale_widget.canvas.before:
                scale_widget._hover_push = PushMatrix()
                scale_widget._hover_scale = Scale(1.0, 1.0, 1.0, origin=self.center)
            with scale_widget.canvas.after:
                scale_widget._hover_pop = PopMatrix()

            # Keep the origin centered
            def _upd(*_):
                if getattr(scale_widget, "_hover_scale", None): scale_widget._hover_scale.origin = self.center
            scale_widget.bind(pos=_upd, size=_upd)
            scale_widget._hover_upd = _upd

            try: Animation.cancel_all(scale_widget._hover_scale)
            except Exception: pass
            scale_widget._anim = Animation(x=scale, y=scale, d=0.12, t="out_cubic")
            scale_widget._anim.start(scale_widget._hover_scale)

        elif not hover_action:
            # Safely animate back and remove when complete
            if hasattr(scale_widget, "_hover_push"):
                try: Animation.cancel_all(scale_widget._hover_scale)
                except: pass
                scale_widget._anim = Animation(x=1.0, y=1.0, d=0.12, t="out_cubic")

                def _cleanup(*_):
                    if hasattr(scale_widget, "_hover_upd"):
                        try: scale_widget.unbind(pos=scale_widget._hover_upd, size=scale_widget._hover_upd)
                        except: pass
                        try: del scale_widget._hover_upd
                        except: pass
                    try:
                        scale_widget.canvas.before.remove(scale_widget._hover_push)
                        scale_widget.canvas.before.remove(scale_widget._hover_scale)
                        scale_widget.canvas.after.remove(scale_widget._hover_pop)
                    except: pass
                    try: del scale_widget._hover_push, scale_widget._hover_scale, scale_widget._hover_pop
                    except: pass

                scale_widget._anim.bind(on_complete=_cleanup)
                scale_widget._anim.start(scale_widget._hover_scale)


    # Change the actual button background
    def f(w): w.background_normal = image
    if _no_bg_change: return f(self)

    # Save the original color, and split it up to adjust it
    original_color = getattr(self, 'background_color', (1, 1, 1, 1))
    background_time, color, opacity = 0.1, original_color[:-1], original_color[-1]
    floor, ceil = 0.22, 1
    start, end = [(*color, floor), (*color, ceil)] if hover_action else [(*color, ceil), (*color, floor)]

    # Execute the animation
    if hover_action: f(self)
    self.background_color = start
    self._anim = Animation(background_color=end, duration=background_time)

    # If not hovering, make sure that the opacity gets reset
    new_color = _new_color or (*color, ceil)
    if not hover_action: self._anim.on_complete = lambda *_: (setattr(self, 'background_color', new_color), f(self))
    self._anim.start(self)

def animate_button(self, image, color, hover_action=False, do_scale=1.03, duration=0.12, _new_color=None, _no_bg_change=False, **kwargs):
    image_animate = Animation(**kwargs, duration=max((duration * 0.5) - 0.1, 0))

    for child in self.parent.children:
        if child.id == 'text': Animation(color=color, duration=(duration * 0.5)).start(child)
        if child.id == 'icon': Animation(color=color, duration=(duration * 0.5)).start(child)

    animate_background(self, image, hover_action, do_scale, _new_color, (_no_bg_change or duration == 0))

    image_animate.start(self)

def animate_icon(self, image, colors, hover_action, do_scale=1.1, duration=0.12, _new_color=None, _no_bg_change=False, **kwargs):
    image_animate = Animation(**kwargs, duration=max((duration * 0.5) - 0.1, 0))

    for child in self.parent.children:
        if child.id == 'text':
            if hover_action:
                try:    color = child.hover_color
                except: child.hover_color = None

                if child.hover_color: Animation(color=child.hover_color, duration=duration).start(child)
                else:                 Animation(color=colors[1] if not self.selected else (0.6, 0.6, 1, 1), duration=duration).start(child)

            else: Animation(color=(0, 0, 0, 0), duration=duration).start(child)

        if child.id == 'icon':
            if hover_action: Animation(color=colors[0], duration=(duration * 0.5)).start(child)
            else:            Animation(color=colors[1], duration=(duration * 0.5)).start(child)

    animate_background(self, image, hover_action, do_scale, _new_color, (_no_bg_change or duration == 0))

    image_animate.start(self)

class HoverButton(Button, HoverBehavior):

    # self.id references image patterns
    # self.color_id references text/image color [hovered, un-hovered]

    color_id = [(0, 0, 0, 0), (0, 0, 0, 0)]
    alt_color = ''
    ignore_hover = False

    # Ignore touch events when popup is present
    def on_touch_down(self, touch):
        popup_widget = utility.screen_manager.current_screen.popup_widget
        if popup_widget: return
        return super().on_touch_down(touch)

    def __init__(self, hover_scale: float = None, **kwargs):
        super().__init__(**kwargs)
        self.bind(on_touch_down=self.onPressed)
        self.hover_scale = hover_scale
        self.button_pressed = None
        self.selected = False
        self.context_options = []
        self.id = ''

    def onPressed(self, instance, touch):
        if touch.device == "wm_touch": touch.button = "left"

        self.button_pressed = touch.button

        # Show context menu if available
        if touch.button == 'right' and self.collide_point(*touch.pos):
            self.update_context_options()
            if self.context_options: utility.screen_manager.current_screen.show_context_menu(self, self.context_options)

    def on_enter(self, *args, duration: float = None, _no_bg_change: bool = False):
        if not self.ignore_hover:
            kwargs = {'do_scale': self.hover_scale} if self.hover_scale else {}
            kwargs.update({'duration': duration} if duration else {})
            kwargs.update({'_no_bg_change': _no_bg_change} if _no_bg_change else {})

            if 'icon_button' in self.id:
                if self.selected: animate_icon(self, image=os.path.join(paths.ui_assets, f'{self.id}_selected.png'), colors=[(0.05, 0.05, 0.1, 1), (0.05, 0.05, 0.1, 1)], hover_action=True, **kwargs)
                else:             animate_icon(self, image=os.path.join(paths.ui_assets, f'{self.id}_hover{self.alt_color}.png'), colors=self.color_id, hover_action=True, **kwargs)

            else: animate_button(self, image=os.path.join(paths.ui_assets, f'{self.id}_hover.png'), color=self.color_id[0], hover_action=True, **kwargs)

    def on_leave(self, *args, duration: float = None, _no_bg_change: bool = False):
        if not self.ignore_hover:
            kwargs = {'do_scale': self.hover_scale} if self.hover_scale else {}
            kwargs.update({'duration': duration} if duration is not None else {})
            kwargs.update({'_no_bg_change': _no_bg_change} if _no_bg_change else {})

            if 'icon_button' in self.id:
                if self.selected: animate_icon(self, image=os.path.join(paths.ui_assets, f'{self.id}_selected.png'), colors=[(0.05, 0.05, 0.1, 1), (0.05, 0.05, 0.1, 1)], hover_action=False, **kwargs)
                else:             animate_icon(self, image=os.path.join(paths.ui_assets, f'{self.id}.png'), colors=self.color_id, hover_action=False, **kwargs)

            else: animate_button(self, image=os.path.join(paths.ui_assets, f'{self.id}.png'), color=self.color_id[1], hover_action=False, **kwargs)

    def on_press(self):
        self.on_mouse_pos(self, Window.mouse_pos)

        # Log for crash info
        try:
            widget_text = None
            for widget in self.parent.children:
                if "Label" in widget.__class__.__name__:
                    widget_text = widget.text
                    break

            if "_" in str(self.id): interaction = str(''.join([x.title() for x in self.id.split("_")]))
            else:                   interaction = str(self.id)
            if widget_text:         interaction += f" ({widget_text.title().replace('Mcs', 'MCS').strip()})"
            constants.last_widget = interaction + f" @ {constants.format_now()}"
            send_log('navigation', f"interaction: '{interaction}'")

            no_sound = [self.disabled, self.parent.disabled, self.opacity == 0, self.parent.opacity == 0]
            if not any(no_sound): audio.player.play('interaction/click_*', jitter=(0, 0.15))
        except: pass

    def force_click(self, *args):
        touch = MouseMotionEvent("mouse", "mouse", Window.center)
        touch.button = 'left'
        touch.pos = Window.center
        self.dispatch('on_touch_down', touch)

        utility.screen_manager.current_screen._keyboard.release()
        self.on_enter()
        self.trigger_action(0.1)

    # Optional hook to override for updating context options dynamically
    def update_context_options(self):
        pass



# -------------------------------------------------  Main Buttons  -----------------------------------------------------

# Default wide button in most menus, accepts an icon and text
class MainButton(FloatLayout):

    def repos_icon(self, *args):

        def resize(*args):
            pos_calc = ((self.button.width/2 - 35) if self.button.center[0] > 0 else (-self.button.width/2 + 35))
            self.icon.center[0] = self.button.center[0] + pos_calc

        Clock.schedule_once(resize, 0)

    def __init__(self, name, position, icon_name=None, width=None, icon_offset=None, auto_adjust_icon=False, click_func=None, **args):
        super().__init__(**args)

        self.id = name

        self.button = HoverButton()
        self.button.id = 'main_button'
        self.button.color_id = [(0.05, 0.05, 0.1, 1), (0.6, 0.6, 1, 1)]
        self.button.size_hint = (None, None)
        self.button.size = (dp(450 if not width else width), dp(72))
        self.button.pos_hint = {"center_x": position[0], "center_y": position[1]}
        self.button.border = (30, 30, 30, 30)
        self.button.background_normal = os.path.join(paths.ui_assets, 'main_button.png')
        self.button.background_down = os.path.join(paths.ui_assets, 'main_button_click.png')

        self.text = Label()
        self.text.id = 'text'
        self.text.size_hint = (None, None)
        self.text.pos_hint = {"center_x": position[0], "center_y": position[1]}

        # Justify text spacing for other languages
        translated = translate(name)
        if auto_adjust_icon:
            if position[0] >= 0.5: text = name.upper() + (int(round(len(translated)*.7))*' ')
            else:                  text = (int(round(len(translated)*.7))*' ') + name.upper()
        elif len(translated) > 28: text = (int(round(len(translated)*.2))*' ') + name.upper()
        else:                      text = name.upper()
        self.text.text = text

        self.text.font_size = sp(19)
        self.text.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["bold"]}.ttf')
        self.text.color = (0.6, 0.6, 1, 1)


        # Button click behavior
        self.button.on_release = functools.partial(button_action, name, self.button)
        self.add_widget(self.button)

        if icon_name:
            self.icon = Image()
            self.icon.id = 'icon'
            self.icon.source = icon_path(icon_name)
            self.icon.size = (dp(1), dp(1))
            self.icon.color = (0.6, 0.6, 1, 1)
            self.icon.pos_hint = {"center_y": position[1]}
            self.icon.pos = (icon_offset if icon_offset else -190 if not width else (-190 - (width / 13)), 200)
            self.add_widget(self.icon)

        self.add_widget(self.text)

        if auto_adjust_icon and icon_name: Clock.schedule_once(self.repos_icon, 0)

        if click_func: self.button.bind(on_press=click_func)


# Similar to 'MainButton', but is a solid color with an optional hover image
class ColorButton(FloatLayout):

    def repos_icon(self, *args):
        def resize(*args):
            pos_calc = ((self.button.width / 2 - 35) if self.button.center[0] > 0 else (-self.button.width / 2 + 35))
            self.icon.center[0] = self.button.center[0] + pos_calc
        Clock.schedule_once(resize, 0)

    def __init__(self, name, position, icon_name=None, width=None, icon_offset=None, auto_adjust_icon=False, click_func=None, color=(1, 1, 1, 1), disabled=False, hover_data={'color': None, 'image': None}, **kw):
        super().__init__(**kw)
        self.id = name

        def on_enter(*a):
            if not self.button.ignore_hover:
                if self._hover_data['color'] or self._hover_data['image']:
                    animate_button(self.button, image=self._hover_data['image'], color=self._hover_data['color'], hover_action=True)
                    return True
            return self.button._on_enter()

        self._hover_data = hover_data
        self.button = HoverButton()
        self.button._on_enter = self.button.on_enter
        self.button.on_enter = on_enter
        self.button.id = 'color_button'
        self.button.color_id = [constants.brighten_color(color, -0.9), color]

        self.button.size_hint = (None, None)
        self.button.size = (dp(450 if not width else width), dp(72))
        self.button.pos_hint = {"center_x": position[0], "center_y": position[1]}
        self.button.border = (30, 30, 30, 30)
        self.button.background_normal = os.path.join(paths.ui_assets, 'color_button.png')
        self.button.background_down = os.path.join(paths.ui_assets, 'color_button_click.png') if not disabled else self.button.background_normal
        self.button.background_disabled_normal = os.path.join(paths.ui_assets, 'color_button.png')
        self.button.background_disabled_down = os.path.join(paths.ui_assets, 'color_button_click.png')
        self.button.background_color = self.button.color_id[1]

        self.text = Label()
        self.text.id = 'text'
        self.text.size_hint = (None, None)
        self.text.pos_hint = {"center_x": position[0], "center_y": position[1]}
        self.text.text = name.upper()
        self.text.font_size = sp(19)
        self.text.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["bold"]}.ttf')
        self.text.color = self.button.color_id[1]


        # Button click behavior
        self.button.on_release = functools.partial(button_action, name, self.button)
        self.add_widget(self.button)

        if icon_name:
            self.icon = Image()
            self.icon.id = 'icon'
            self.icon.source = icon_path(icon_name)
            self.icon.size = (dp(1), dp(1))
            self.icon.color = self.button.color_id[1]
            self.icon.pos_hint = {"center_y": position[1]}
            self.icon.pos = (icon_offset if icon_offset else -190 if not width else (-190 - (width / 13)), 200)
            if disabled: self.icon.opacity = 0
            self.add_widget(self.icon)

        self.add_widget(self.text)

        if auto_adjust_icon and icon_name: Clock.schedule_once(self.repos_icon, 0)

        if click_func and not disabled: self.button.bind(on_press=click_func)

        self.button.ignore_hover = disabled
        if disabled:
            self.opacity = 0.4
            self.button.opacity = 0.5


# Similar to 'MainButton', but has an async loading feature
class WaitButton(FloatLayout):

    @property
    def is_disabled(self) -> bool:
        return self.button.disabled

    def repos_icon(self, *args):

        def resize(*args):
            pos_calc = ((self.button.width/2 - 35) if self.button.center[0] > 0 else (-self.button.width/2 + 35))
            self.icon.center[0] = self.button.center[0] + pos_calc
            self.load_icon.center[0] = self.button.center[0] + pos_calc

        Clock.schedule_once(resize, 0)

    def loading(self, boolean_value, *args):
        self.is_loading = boolean_value
        def _animate(*_):
            if boolean_value: self.button.on_leave()
            self.disable(boolean_value)
            self.load_icon.color = (0.6, 0.6, 1, 1) if boolean_value else (0.6, 0.6, 1, 0)
        Clock.schedule_once(_animate, -1)

    def disable(self, disable=False, animate=True):
        if self.button.disabled == disable: return

        previously_disabled  = self.button.disabled
        self.button.disabled = disable
        duration = (0.12 if animate else 0)

        def _animate(*_):
            if (disable) or (not disable and not self.button.hovered):
                Animation(color=(0.6, 0.6, 1, 0.4) if self.button.disabled else (0.6, 0.6, 1, 1), duration=duration).start(self.text)
                Animation(color=(0.6, 0.6, 1, 0) if self.button.disabled else (0.6, 0.6, 1, 1), duration=duration).start(self.icon)

            elif not self.button.ignore_hover and previously_disabled and (not disable and self.button.hovered):
                self.button.on_enter()
        Clock.schedule_once(_animate, -1)

    def force_click(self, *a):
        if self.button.disabled: return
        self.button.force_click(*a)

    def __init__(self, name, position, icon_name=None, width=None, icon_offset=None, auto_adjust_icon=False, click_func=None, disabled=False, start_loading=False, **kwargs):
        super().__init__(**kwargs)

        self.id = name
        self.is_loading = False

        self.button = HoverButton()
        self.button.id = 'main_button'
        self.button.color_id = [(0.05, 0.05, 0.1, 1), (0.6, 0.6, 1, 1)]

        self.button.size_hint = (None, None)
        self.button.size = (dp(450 if not width else width), dp(72))
        self.button.pos_hint = {"center_x": position[0], "center_y": position[1]}
        self.button.border = (30, 30, 30, 30)
        self.button.background_normal = os.path.join(paths.ui_assets, 'main_button.png')
        self.button.background_down = os.path.join(paths.ui_assets, 'main_button_click.png')
        self.button.background_disabled_normal = os.path.join(paths.ui_assets, 'main_button_disabled.png')
        self.button.background_disabled_down = os.path.join(paths.ui_assets, 'main_button_disabled.png')

        self.text = Label()
        self.text.id = 'text'
        self.text.size_hint = (None, None)
        self.text.pos_hint = {"center_x": position[0], "center_y": position[1]}
        self.text.text = name.upper()
        self.text.font_size = sp(19)
        self.text.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["bold"]}.ttf')
        self.text.color = (0.6, 0.6, 1, 1)


        # Button click behavior
        self.button.on_release = functools.partial(button_action, name, self.button)
        self.add_widget(self.button)

        if icon_name:
            self.icon = Image()
            self.icon.id = 'icon'
            self.icon.source = icon_path(icon_name)
            self.icon.size = (dp(1), dp(1))
            self.icon.color = (0.6, 0.6, 1, 1)
            self.icon.pos_hint = {"center_y": position[1]}
            self.icon.pos = (icon_offset if icon_offset else -190 if not width else (-190 - (width / 13)), 200)
            self.add_widget(self.icon)


        # Loading icon
        self.load_icon = AsyncImage()
        self.load_icon.id = 'load_icon'
        self.load_icon.source = os.path.join(paths.ui_assets, 'animations', 'loading_pickaxe.gif')
        self.load_icon.size_hint_max_y = 40
        self.load_icon.color = (0.6, 0.6, 1, 0)
        self.load_icon.pos_hint = {"center_y": position[1]}
        self.load_icon.pos = (icon_offset if icon_offset else -190 if not width else (-190 - (width / 13)), 200)
        self.load_icon.allow_stretch = True
        self.load_icon.anim_delay = utility.anim_speed * 0.02
        self.add_widget(self.load_icon)


        self.add_widget(self.text)

        if auto_adjust_icon and icon_name: Clock.schedule_once(self.repos_icon, 0)

        if click_func: self.button.bind(on_press=click_func)

        if disabled: self.disable(True, False)

        if start_loading: self.loading(True)


# Similar to 'WaitButton', but way smaller
class NextButton(WaitButton):

    def __init__(self, name, position, disabled=False, next_screen=None, show_load_icon=False, click_func=None, **kwargs):
        FloatLayout.__init__(self, **kwargs)

        self.next_screen = next_screen
        self.click_func = click_func
        self._name = name
        self.is_loading = False

        self.button = HoverButton(disabled=disabled)
        self.button.id = 'next_button'
        self.button.color_id = [(0.05, 0.05, 0.1, 1), (0.6, 0.6, 1, 1)]
        self.button.size_hint = (None, None)
        self.button.size = (dp(240), dp(67))
        self.button.pos_hint = {"center_x": position[0], "center_y": position[1]}
        self.button.border = (-25, -25, -25, -25)
        self.button.background_normal = os.path.join(paths.ui_assets, 'next_button.png')
        self.button.background_down = os.path.join(paths.ui_assets, 'next_button_click.png')
        self.button.background_disabled_normal = os.path.join(paths.ui_assets, 'next_button_disabled.png')
        self.button.background_disabled_down = os.path.join(paths.ui_assets, 'next_button_disabled.png')

        self.text = Label()
        self.text.id = 'text'
        self.text.size_hint = (None, None)
        self.text.pos_hint = {"center_x": position[0], "center_y": position[1]}
        self.text.text = name.upper()
        self.text.font_size = sp(19)
        self.text.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["bold"]}.ttf')
        self.text.color = (0.6, 0.6, 1, 0.4) if disabled else (0.6, 0.6, 1, 1)

        # Button click behavior
        self.button.on_release = self.on_press

        self.icon = Image()
        self.icon.id = 'icon'
        self.icon.source = icon_path('next-stylized.png')
        self.icon.size = (dp(1), dp(1))
        self.icon.color = (0.6, 0.6, 1, 0) if disabled else (0.6, 0.6, 1, 1)
        self.icon.pos_hint = {"center_y": position[1]}
        self.icon.pos = (-90, 200)

        if show_load_icon:
            self.load_icon = AsyncImage()
            self.load_icon.id = 'load_icon'
            self.load_icon.source = os.path.join(paths.ui_assets, 'animations', 'loading_pickaxe.gif')
            self.load_icon.size_hint_max_y = 40
            self.load_icon.color = (0.6, 0.6, 1, 0)
            self.load_icon.pos_hint = {"center_y": position[1]}
            self.load_icon.pos = (-87, 200)
            self.load_icon.allow_stretch = True
            self.load_icon.anim_delay = utility.anim_speed * 0.02
            self.add_widget(self.load_icon)

        self.add_widget(self.button)
        self.add_widget(self.icon)
        self.add_widget(self.text)

    def on_press(self, *a):
        if self.button.disabled: return

        def _exec(*a):
            if self.click_func: self.click_func()
            else:               button_action(self._name, self.button)

            if self.next_screen: Clock.schedule_once(lambda *_: setattr(utility.screen_manager, 'current', self.next_screen), 0)

            # Unfocus all inputs if the page doesn't continue
            else:
                for child in self.parent.children:
                    if "Input" in child.__class__.__name__:
                        child.focus = False

        dTimer(0, _exec).start()


# Similar to 'MainButton', but way smaller and has a pink gradient tint
class ExitButton(RelativeLayout):

    def __init__(self, name, position, cycle=False, custom_func=None, **args):
        super().__init__(**args)

        self.button = HoverButton()
        self.button.id = 'exit_button'
        self.button.color_id = [(0.1, 0.05, 0.05, 1), (0.6, 0.6, 1, 1)]
        self.button.size_hint = (None, None)
        self.button.size = (dp(195), dp(55))
        self.button.pos_hint = {"center_x": position[0], "center_y": position[1]}
        self.button.border = (-10, -10, -10, -10)
        self.button.background_normal = os.path.join(paths.ui_assets, 'exit_button.png')
        self.button.background_down = os.path.join(paths.ui_assets, 'exit_button_click.png')
        self.custom_func = custom_func

        self.text = Label()
        self.text.id = 'text'
        self.text.size_hint = (None, None)
        self.text.pos_hint = {"center_x": position[0], "center_y": position[1]}

        # Justify text spacing for other languages
        translated = translate(name)
        if len(translated) == len(name): text = name.upper()
        else: text = (int(round(len(translated)*.7))*' ') + name.upper()
        self.text.text = text

        self.text.font_size = sp(19)
        self.text.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["bold"]}.ttf')
        self.text.color = (0.6, 0.6, 1, 1)

        self.icon = Image()
        self.icon.id = 'icon'
        self.icon.source = icon_path('close-stylized.png' if name.lower() == "quit" else 'back-stylized.png')
        self.icon.size = (dp(1), dp(1))
        self.icon.color = (0.6, 0.6, 1, 1)
        self.icon.pos_hint = {"center_y": position[1]}
        self.icon.pos = (-70, 200)


        # Button click behavior
        def execute(*a):
            if self.custom_func: self.custom_func()
            else:                button_action(name, self.button)

        self.button.on_release = execute


        self.add_widget(self.button)
        self.add_widget(self.icon)
        self.add_widget(self.text)


class ListActionBehavior:

    def _init_actions(self):
        self.actions = []
        self._action_cache = []
        self.action_buttons = []

        self.action_layout = RelativeLayout(size_hint=(None, None), opacity=0)
        self.action_row = BoxLayout(orientation='horizontal', spacing=5, size_hint=(None, None), height=80)

        self.action_text = Label()
        self.action_text.__translate__ = False
        self.action_text.id = 'action_text'
        self.action_text.size_hint = (None, None)
        self.action_text.text = ''
        self.action_text.font_size = sp(19)
        self.action_text.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
        self.action_text.color = (0.6, 0.6, 1, 1)
        self.action_text.halign = 'right'
        self.action_text.valign = 'middle'
        self.action_text.opacity = 0

        self.action_layout.add_widget(self.action_text)
        self.action_layout.add_widget(self.action_row)

    def _action_enter(self, button, *args):
        def change_action(*args):
            if not self.button.hovered or not button.list_action:
                return

            self.action_text.text = button.list_action[0].lower()
            self.action_text.color = button.button.color_id[1]

            Animation.stop_all(self.action_text)
            Animation.stop_all(button)

            Animation(opacity=1, duration=0.15).start(self.action_text)
            Animation(opacity=1, duration=0.15).start(button)

        Clock.schedule_once(change_action, 0)

    def _action_leave(self, button, *args):
        def restore(*args):
            if self.button.hovered and not any(item.button.hovered for item in self.action_buttons):
                Animation.stop_all(self.action_text)
                Animation(opacity=0, duration=0.15).start(self.action_text)

        Animation.stop_all(button)
        Animation(opacity=0.65, duration=0.15).start(button)

        Clock.schedule_once(restore, 0)

    def _configure_action(self, button, action):
        icon, click_func = action[1:3]
        options = action[3].copy() if len(action) > 3 else {}
        options.pop('hover_image', None)

        force_color = options.get('force_color')

        button.list_action = action
        button.change_data(icon=icon)

        button.button.color_id = force_color[0] if force_color else [(0.05, 0.05, 0.1, 1), (0.6, 0.6, 1, 1)]
        button.button.alt_color = "_" + force_color[1] if force_color and force_color[1] else ''

        button.button.background_normal = os.path.join(paths.ui_assets, f'{button.button.id}.png')
        button.button.background_down = os.path.join(paths.ui_assets,
            (
                f'{button.button.id}_click{button.button.alt_color}.png'
                if click_func else
                f'{button.button.id}_hover{button.button.alt_color}.png'
            )
        )

        button.icon.color = button.button.color_id[1]
        button.disabled = False
        button.button.disabled = not self.button.hovered or self.is_loading
        button.button.state = 'normal'
        button.button.hovered = False
        button.text.color = (0, 0, 0, 0)
        button.opacity = 0.65


        if click_func:
            def execute(*args):
                if not button.disabled and not button.button.disabled:
                    click_func()

            button.button.on_release = execute

        else: button.button.on_release = lambda *_: None

    def _set_actions(self, actions):
        self.actions = actions or []

        # Cache physical IconButtons instead of regenerating them while scrolling
        while len(self._action_cache) < len(self.actions):
            button = IconButton('', {"center_x": 0.5, "center_y": 0.5}, None, (None, None), 'checkmark-sharp.png', clickable=False)

            button.button.background_disabled_normal = button.button.background_normal
            button.button.background_disabled_down = button.button.background_normal

            button.list_action = None
            button.size_hint = (None, None)
            button.size = (50, 80)
            button.opacity = 0.65

            button.button.bind(on_enter=functools.partial(self._action_enter, button))
            button.button.bind(on_leave=functools.partial(self._action_leave, button))

            self._action_cache.append(button)


        # Re-use the cached action widgets
        self.action_row.clear_widgets()
        self.action_buttons = self._action_cache[:len(self.actions)]

        for button, action in zip(self.action_buttons, self.actions):
            self._configure_action(button, action)
            self.action_row.add_widget(button)

        self.action_row.width = (len(self.actions) * 50) + (max(0, len(self.actions) - 1) * self.action_row.spacing)

    def _show_actions(self):
        if not self.actions or self.is_loading:
            return

        self.action_text.opacity = 0

        for button in self.action_buttons:
            button.button.disabled = False

        Animation.stop_all(self.action_layout)
        Animation(opacity=1, duration=0.06).start(self.action_layout)

    def _hide_actions(self, animate=True):
        Animation.stop_all(self.action_layout)
        Animation.stop_all(self.action_text)

        if animate: Animation(opacity=0, duration=0.06).start(self.action_layout)
        else: self.action_layout.opacity = 0
        self.action_text.opacity = 0

        for button in self.action_buttons:
            Animation.stop_all(button)
            Animation.stop_all(button.button)
            Animation.stop_all(button.icon)
            Animation.stop_all(button.text)

            button.button.hovered = False
            button.button.state = 'normal'
            button.button.on_leave(duration=0)

            button.icon.color = button.button.color_id[1]
            button.text.color = (0, 0, 0, 0)

            button.button.disabled = True
            button.opacity = 0.65


# Similar to 'MainButton', but optimized for RecycleView list layouts
class ListButton(ListActionBehavior, FloatLayout):
    def __setattr__(self, attr, value):

        # Update attributes dynamically based on RV data
        if attr == "list_data":
            super().__setattr__(attr, value)

            if value and hasattr(self, 'button'):
                self.change_data(value)

            return

        # Preserve properties if the current row updates them
        elif attr == "properties":
            super().__setattr__(attr, value)

            if value and getattr(self, 'list_data', None) and not getattr(self, '_changing_data', False):
                self.list_data['item'] = value

            return

        super().__setattr__(attr, value)

    def _hide_status(self):
        for item in (self.banner, self.disabled_banner):
            if item:
                Animation.stop_all(item)
                item.opacity = 0

        if self._status_visible():
            for item in (self.install_image, self.install_label):
                Animation.stop_all(item)
                item.opacity = 0

    def _show_status(self):
        for item in (self.banner, self.disabled_banner):
            if item:
                Animation.stop_all(item)
                item.opacity = 1

        if self._status_visible():
            for item in (self.install_image, self.install_label):
                Animation.stop_all(item)
                item.opacity = 1

    def _status_visible(self):
        return self.installed and not self.banner and self.enabled is None

    def _primary_click(self, *args):
        if self.is_loading:
            return

        if self.action_layout and any(item.button.hovered for item in self.action_buttons):
            return

        if self.click_function:
            self.click_function(*args)

    def _normal_image(self):
        if self.enabled is False:
            return os.path.join(paths.ui_assets, f'{self.button.id}_disabled.png')

        elif self.installed and not self.banner and self.enabled is None:
            return os.path.join(paths.ui_assets, f'{self.button.id}_installed.png')

        return os.path.join(paths.ui_assets, f'{self.button.id}.png')

    def _hover_image(self):
        if self.actions:
            return os.path.join(paths.ui_assets, 'server_button.png')

        return os.path.join(paths.ui_assets, f'{self.button.id}_hover.png')

    def _reset_visuals(self):
        def _reset_scale(widget):
            if hasattr(widget, '_hover_scale'):
                try: Animation.cancel_all(widget._hover_scale)
                except: pass
                if hasattr(widget, '_hover_upd'):
                    try: widget.unbind(pos=widget._hover_upd, size=widget._hover_upd)
                    except: pass
                try:
                    widget.canvas.before.remove(widget._hover_push)
                    widget.canvas.before.remove(widget._hover_scale)
                    widget.canvas.after.remove(widget._hover_pop)
                except: pass
                try: del widget._hover_push, widget._hover_scale, widget._hover_pop, widget._hover_upd
                except: pass

        _reset_scale(self)
        Animation.stop_all(self.button)
        Animation.stop_all(self.title)
        Animation.stop_all(self.subtitle)
        Animation.stop_all(self.install_image)
        Animation.stop_all(self.install_label)
        Animation.stop_all(self.load_icon)
        Animation.stop_all(self.hover_text)
        Animation.stop_all(self.action_layout)
        Animation.stop_all(self.action_text)
        Animation.stop_all(self.highlight_border)

        self.opacity = 1
        self.title.opacity = 1
        self.subtitle.opacity = 0.56
        self.hover_text.opacity = 0
        self.action_layout.opacity = 0
        self.action_text.opacity = 0
        self.action_text.text = ''
        self.load_icon.opacity = 0
        self.highlight_border.opacity = 0

        self.button.state = 'normal'
        self.button.disabled = False
        self.button.hovered = False
        self.button.ignore_hover = False
        self.button.background_color = (1, 1, 1, 1)

        for button in self.action_buttons:
            Animation.stop_all(button)
            Animation.stop_all(button.button)
            Animation.stop_all(button.icon)
            Animation.stop_all(button.text)

            _reset_scale(button)

            button.button.hovered = False
            button.button.state = 'normal'
            button.button.background_color = (1, 1, 1, 1)

            button.icon.color = button.button.color_id[1]
            button.text.color = (0, 0, 0, 0)

            button.button.disabled = True
            button.opacity = 0.65

    def _set_banner(self, banner):
        if self.banner:
            Animation.stop_all(self.banner)
            try: self.remove_widget(self.banner)
            except: pass

        if isinstance(banner, dict):
            banner = BannerObject(**banner)

        self.banner = banner
        if self.banner:
            self.banner.size_hint = (None, None)
            self.banner.pos_hint = {}
            self.add_widget(self.banner)

    def _set_disabled_banner(self):
        if self.disabled_banner:
            Animation.stop_all(self.disabled_banner)
            try: self.remove_widget(self.disabled_banner)
            except: pass

        self.disabled_banner = None
        if self.enabled is False and not self.banner:
            self.disabled_banner = BannerObject(size=(125, 32), color=(1, 0.53, 0.58, 1), text="disabled", icon="close-circle.png", icon_side="right")
            self.disabled_banner.size_hint = (None, None)
            self.disabled_banner.pos_hint = {}
            self.add_widget(self.disabled_banner)

    def change_data(self, data):
        self._reset_visuals()
        self._changing_data = True
        self.view_index = data['index']


        # Generate display state from the current live item every time
        fade_in = max(data['fade_until'] - Clock.get_time(), 0) if not data.get('rendered') else 0
        button_data = data['generator'](data['item'], data['index'], fade_in, False)

        if not button_data:
            self.opacity = 0
            self.button.disabled = True
            self._changing_data = False
            return

        button_data = button_data.copy()
        button_data.update(data.setdefault('state', {}))


        # Generic state
        self.properties = button_data.get('properties', data['item'])
        self.installed = button_data.get('installed', False)
        self.install_label.text = button_data.get('status_text', 'installed')
        self.enabled = button_data.get('enabled')
        self.click_function = button_data.get('click_function')
        self.is_loading = False

        banner = button_data.get('banner')
        actions = button_data.get('actions') or []
        loading = button_data.get('loading', False)


        # Generic object presentation
        self.display_name = (
            getattr(self.properties, "name", None) or
            getattr(self.properties, "title", "Unknown")
        )

        self.display_subtitle = (
            getattr(self.properties, "subtitle", None) or
            getattr(self.properties, "description", None)
        )

        self.display_author = getattr(self.properties, "author", None) or "Unknown"

        if not self.display_subtitle:
            self.display_subtitle = "Description unavailable"

        if "\n" in self.display_subtitle:
            self.display_subtitle = self.display_subtitle.split("\n", 1)[0].strip()


        # State colors
        if self.enabled is False:
            self.color_id = [(0.05, 0.1, 0.1, 1), (1, 0.6, 0.7, 1)]
        else:
            self.color_id = [(0.05, 0.05, 0.1, 1), (0.65, 0.65, 1, 1)]

        self.button.color_id = self.color_id
        self.title.color = self.color_id[1]
        self.subtitle.color = self.color_id[1]
        self.highlight_border.color = constants.brighten_color(self.color_id[1], 0.1)


        # Title
        self.title.text = f"{self.display_name}  [color=#434368]-[/color]  {self.display_author}"
        self.title.text_size = (self.button.width * (0.7 if self.installed or banner or actions else 0.94), self.button.height)


        # Description
        self.subtitle.text = self.display_subtitle
        self.subtitle.font_name = self.original_font


        # Optional state
        self._set_banner(banner)
        self._set_disabled_banner()
        self._set_actions(actions)


        # Installed indicator
        self.install_image.opacity = 1 if self._status_visible() else 0
        self.install_label.opacity = 1 if self._status_visible() else 0


        # Button images
        self.button.background_normal = self._normal_image()

        if self.actions:
            self.button.background_down = os.path.join(paths.ui_assets, f'{self.button.id}_click_alt.png')

        else:
            self.button.background_down = (
                os.path.join(paths.ui_assets, f'{self.button.id}_click.png')
                if self.click_function
                else self.button.background_normal
            )


        self.hover_text.text = self.display_name
        self.hover_text.color = self.color_id[1]

        self.resize_self()


        # Loading
        self.loading(loading, False, _sync=False)


        # Fade-in only the first time this logical item is rendered
        if fade_in > 0:
            Animation.stop_all(self)
            Animation.stop_all(self.title)
            Animation.stop_all(self.subtitle)

            self.opacity = 0
            self.title.opacity = 0
            self.subtitle.opacity = 0

            Animation(opacity=1, duration=fade_in).start(self)
            Animation(opacity=1, duration=fade_in).start(self.title)
            Animation(opacity=0.56, duration=fade_in).start(self.subtitle)


        data['rendered'] = True
        self._changing_data = False

    def toggle_installed(self, installed, *args):
        self.installed = installed

        if self.list_data:
            self.list_data.setdefault('state', {})['installed'] = installed

        self.install_image.opacity = 1 if self._status_visible() else 0
        self.install_label.opacity = 1 if self._status_visible() else 0

        self.title.text_size = (self.button.width * (0.7 if self.installed or self.banner or self.actions else 0.94), self.button.height)
        self.button.background_normal = self._normal_image()
        self.resize_self()

    def resize_self(self, *args):

        # Title and description
        padding = 2.17
        offset = 5 if self.actions else 0

        self.title.pos = (
            self.button.x + (self.title.text_size[0] / padding) - offset,
            self.button.y + 31
        )

        self.subtitle.pos = (
            self.button.x + (self.subtitle.text_size[0] / padding) - 1,
            self.button.y
        )

        # Installed label
        self.install_image.pos = (
            self.button.x + self.button.width - self.install_label.width - 28,
            self.button.y + 38.5
        )

        self.install_label.pos = (
            self.button.x + self.button.width - self.install_label.width - 30,
            self.button.y + 5
        )

        # Optional banner
        if self.banner:
            self.banner.pos = (
                self.button.x + self.button.width - self.banner.width - 18,
                self.button.y + 38.5
            )

        # Disabled banner
        if self.disabled_banner:
            self.disabled_banner.pos = (
                self.button.x + self.button.width - self.disabled_banner.width - 18,
                self.button.y + 38.5
            )

        # Action row
        self.action_layout.pos = self.button.pos
        self.action_layout.size = self.button.size

        self.action_row.pos = (
            self.button.width - self.action_row.width - 12,
            0
        )

        self.action_text.pos = (
            self.action_row.x - 155,
            0
        )

        self.action_text.size = (
            145,
            self.button.height
        )

        self.action_text.text_size = self.action_text.size

        self.hover_text.pos = (
            self.button.x + 18,
            self.button.y
        )

        self.hover_text.size = (
            self.action_text.x - 30,
            self.button.height
        )

        self.hover_text.text_size = self.hover_text.size

        # Loading icon
        self.load_icon.pos = (
            self.button.x + self.button.width - 62,
            self.button.y + 15
        )

        # Highlight border
        self.highlight_layout.pos = self.button.pos
        self.highlight_layout.size = self.button.size

        self.highlight_border.pos = (0, 0)
        self.highlight_border.size = self.button.size

    def highlight(self):
        def next_frame(*args):
            Animation.stop_all(self.highlight_border)
            self.highlight_border.opacity = 1
            Animation(opacity=0, duration=0.7).start(self.highlight_border)

        Clock.schedule_once(next_frame, 0)

    def on_enter(self, *args):
        if self.button.ignore_hover or self.is_loading:
            return

        Animation(color=self.color_id[0], duration=self.anim_duration).start(self.title)
        Animation(color=self.color_id[0], duration=self.anim_duration).start(self.subtitle)
        animate_background(self.button, self._hover_image(), True, _no_bg_change=bool(self.actions))

        if self.actions:
            self._hide_status()

            for button in self.action_buttons:
                button.button.disabled = False

            self.hover_text.text = self.display_name
            self.hover_text.color = self.color_id[1]

            Animation.stop_all(self.title)
            Animation.stop_all(self.subtitle)
            Animation.stop_all(self.hover_text)
            Animation.stop_all(self.action_layout)
            Animation.stop_all(self.action_text)

            self.action_text.opacity = 0
            Animation(opacity=0, duration=self.anim_duration).start(self.title)
            Animation(opacity=0, duration=self.anim_duration).start(self.subtitle)
            Animation(opacity=1, duration=self.anim_duration).start(self.hover_text)
            Animation(opacity=1, duration=self.anim_duration).start(self.action_layout)

    def on_leave(self, *args):
        if self.button.ignore_hover or self.is_loading:
            return

        Animation(color=self.color_id[1], duration=self.anim_duration).start(self.title)
        Animation(color=self.color_id[1], duration=self.anim_duration).start(self.subtitle)
        animate_background(self.button, self._normal_image(), False, _no_bg_change=bool(self.actions))

        if self.actions:
            self.hover_text.text = self.display_name

            Animation.stop_all(self.title)
            Animation.stop_all(self.subtitle)
            Animation.stop_all(self.hover_text)
            Animation.stop_all(self.action_layout)
            Animation.stop_all(self.action_text)

            self.action_text.opacity = 0
            Animation(opacity=1, duration=self.anim_duration).start(self.title)
            Animation(opacity=0.56, duration=self.anim_duration).start(self.subtitle)
            Animation(opacity=0, duration=self.anim_duration).start(self.hover_text)
            Animation(opacity=0, duration=self.anim_duration).start(self.action_layout)

            for button in self.action_buttons:
                Animation.stop_all(button)
                Animation.stop_all(button.button)
                Animation.stop_all(button.icon)
                Animation.stop_all(button.text)

                button.button.hovered = False
                button.button.on_leave(duration=0)
                button.button.state = 'normal'

                button.icon.color = button.button.color_id[1]
                button.text.color = (0, 0, 0, 0)

                button.button.disabled = True
                button.opacity = 0.65

            self._show_status()

    def loading(self, load_state, show_text=True, *args, _sync=True):

        if _sync and self.list_data:
            self.list_data.setdefault('state', {})['loading'] = load_state

        if load_state and not self.is_loading and self.button.hovered:
            self.on_leave()

        self.is_loading = load_state
        self.load_icon.opacity = 1 if load_state else 0

        if self.actions:
            self.action_layout.opacity = 0 if load_state else 1 if self.button.hovered else 0

            for button in self.action_buttons:
                button.button.disabled = load_state or not self.button.hovered

            if load_state:
                self.hover_text.opacity = 0
                self.action_text.opacity = 0


        if load_state:
            self._hide_status()

        elif not self.button.hovered:
            self._show_status()


        if show_text:
            if load_state:
                self.subtitle.text = "Loading info..."
                self.subtitle.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')

            else:
                self.subtitle.text = self.display_subtitle
                self.subtitle.font_name = self.original_font

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.id = 'list_item'
        self.height = 85
        self.size_hint_y = None

        self.list_data = None
        self.view_index = 0
        self.properties = None

        self.installed = False
        self.enabled = None
        self.banner = None
        self.disabled_banner = None
        self.click_function = None
        self.is_loading = False

        self.display_name = "Unknown"
        self.display_subtitle = "Description unavailable"
        self.display_author = "Unknown"

        self.color_id = [(0.05, 0.05, 0.1, 1), (0.65, 0.65, 1, 1)]
        self.anim_duration = 0.06
        self._changing_data = False
        self._init_actions()

        self.original_font = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["regular"]}.ttf')


        # Main button
        self.button = HoverButton()
        self.button.id = "list_button"
        self.button.color_id = self.color_id
        self.button.border = (-5, -5, -5, -5)
        self.button.size_hint = (None, None)
        self.button.size = (580, 80)
        self.button.pos_hint = {"center_x": 0.5, "center_y": 0.6}

        self.button.background_normal = self._normal_image()
        self.button.background_down = self.button.background_normal

        self.button.on_enter = self.on_enter
        self.button.on_leave = self.on_leave
        self.button.bind(on_press=self._primary_click)

        self.add_widget(self.button)


        # Title
        self.title = Label()
        self.title.size_hint = (None, None)
        self.title.__translate__ = False
        self.title.id = "title"
        self.title.halign = "left"
        self.title.color = self.color_id[1]
        self.title.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
        self.title.font_size = sp(25)
        self.title.text_size = (self.button.width * 0.94, self.button.height)
        self.title.shorten = True
        self.title.markup = True
        self.title.shorten_from = "right"
        self.title.max_lines = 1
        self.title.text = ""
        self.add_widget(self.title)


        # Description
        self.subtitle = Label()
        self.subtitle.size_hint = (None, None)
        self.subtitle.__translate__ = False
        self.subtitle.id = "subtitle"
        self.subtitle.halign = "left"
        self.subtitle.color = self.color_id[1]
        self.subtitle.font_name = self.original_font
        self.subtitle.font_size = sp(21)
        self.subtitle.opacity = 0.56
        self.subtitle.text_size = (self.button.width * 0.91, self.button.height)
        self.subtitle.shorten = True
        self.subtitle.shorten_from = "right"
        self.subtitle.max_lines = 1
        self.subtitle.text = ""

        self.add_widget(self.subtitle)


        # Installed indicator
        self.install_image = Image()
        self.install_image.size_hint = (None, None)
        self.install_image.size = (110, 30)
        self.install_image.keep_ratio = False
        self.install_image.allow_stretch = True
        self.install_image.source = os.path.join(paths.ui_assets, 'installed.png')
        self.install_image.opacity = 0

        self.add_widget(self.install_image)

        self.install_label = AlignLabel()
        self.install_label.size_hint = (None, None)
        self.install_label.halign = "right"
        self.install_label.valign = "middle"
        self.install_label.font_size = sp(18)
        self.install_label.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
        self.install_label.width = 100
        self.install_label.color = (0.05, 0.08, 0.07, 1)
        self.install_label.text = 'installed'
        self.install_label.opacity = 0

        self.add_widget(self.install_label)


        # Loading icon
        self.load_icon = AsyncImage()
        self.load_icon.id = 'load_icon'
        self.load_icon.source = os.path.join(paths.ui_assets, 'animations', 'loading_pickaxe.gif')
        self.load_icon.size_hint = (None, None)
        self.load_icon.size = (50, 50)
        self.load_icon.color = (0.6, 0.6, 1, 1)
        self.load_icon.opacity = 0
        self.load_icon.allow_stretch = True
        self.load_icon.anim_delay = utility.anim_speed * 0.02
        self.add_widget(self.load_icon)


        # Hover title
        self.hover_text = Label()
        self.hover_text.__translate__ = False
        self.hover_text.id = 'hover_text'
        self.hover_text.size_hint = (None, None)
        self.hover_text.text = ''
        self.hover_text.font_size = sp(23)
        self.hover_text.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["bold"]}.ttf')
        self.hover_text.color = (0.1, 0.1, 0.1, 1)
        self.hover_text.halign = "left"
        self.hover_text.valign = "middle"
        self.hover_text.shorten = True
        self.hover_text.shorten_from = "right"
        self.hover_text.max_lines = 1
        self.hover_text.opacity = 0
        self.hover_text.padding_x = 15
        self.add_widget(self.hover_text)


        # Action layout
        self.add_widget(self.action_layout)


        # Highlight border
        self.highlight_layout = RelativeLayout(size_hint=(None, None))
        self.highlight_border = Image()
        self.highlight_border.keep_ratio = False
        self.highlight_border.allow_stretch = True
        self.highlight_border.color = constants.brighten_color(self.color_id[1], 0.1)
        self.highlight_border.opacity = 0
        self.highlight_border.source = os.path.join(paths.ui_assets, 'server_button_highlight.png')
        self.highlight_layout.add_widget(self.highlight_border)
        self.add_widget(self.highlight_layout)

        self.bind(pos=self.resize_self, size=self.resize_self)
        self.button.bind(pos=self.resize_self, size=self.resize_self)
        Clock.schedule_once(self.resize_self, 0)

        if self.list_data:
            self.change_data(self.list_data)


# Similar to 'ListButton', but optimized for historical snapshot layouts
class ListHistoryButton(ListActionBehavior, RelativeLayout):

    radio_rgba = ListProperty([0, 0, 0, 1])

    def __setattr__(self, attr, value):

        # Update attributes dynamically based on RV data
        if attr == 'history_data':
            super().__setattr__(attr, value)

            if value and hasattr(self, 'button'):
                self.change_data(value)

            return

        super().__setattr__(attr, value)

    def _clear_hover_scale(self):
        if not hasattr(self.card, '_hover_scale'):
            return

        try: Animation.cancel_all(self.card._hover_scale)
        except: pass

        if hasattr(self.card, '_hover_upd'):
            try: self.card.unbind(pos=self.card._hover_upd, size=self.card._hover_upd)
            except: pass

        try:
            self.card.canvas.before.remove(self.card._hover_push)
            self.card.canvas.before.remove(self.card._hover_scale)
            self.card.canvas.after.remove(self.card._hover_pop)
        except: pass

        for attr in ('_hover_push', '_hover_scale', '_hover_pop', '_hover_upd', '_anim'):
            try: delattr(self.card, attr)
            except: pass

    def _normal_image(self):
        return os.path.join(paths.ui_assets, f'server_button{"_ro" if self.selected else ""}.png')

    def _set_radio(self, hovered=False, animate=True):
        hovered = bool(hovered and not self.button.ignore_hover)
        if hovered:         color = self.color_id[0]
        elif self.selected: color = self.color_id[1]
        else:               color = (0.28, 0.28, 0.42, 1)

        rgba = [*color[:3], 1]
        dot_opacity = 1 if self.selected else 0

        Animation.cancel_all(self, 'radio_rgba')
        Animation.cancel_all(self.radio_dot_widget, 'opacity')

        if animate:
            Animation(radio_rgba=rgba, duration=0.08, t='out_quad').start(self)
            Animation(opacity=dot_opacity, duration=0.08, t='out_quad').start(self.radio_dot_widget)

        else:
            self.radio_rgba = rgba
            self.radio_dot_widget.opacity = dot_opacity

    def _reset_visuals(self, suppress_hover=False):
        self._clear_hover_scale()
        self._hide_actions(False)

        Animation.stop_all(self.button)
        Animation.cancel_all(self, 'radio_rgba')
        Animation.cancel_all(self.radio_dot_widget, 'opacity')

        for widget in (
            self.title, self.subtitle, self.hover_text,
            self.type_image.image, self.loading_text,
            self.type_image.type_label,
            self.type_image.version_label
        ):
            Animation.stop_all(widget)

        self.button.state = 'normal'
        self.button.hovered = False
        self.button.ignore_hover = suppress_hover
        self.button.button_pressed = None
        self.button.background_color = (1, 1, 1, 1)
        self.button.background_normal = self._normal_image()

        self.title.color = self.color_id[1]
        self.subtitle.color = self.color_id[1]
        self.type_image.image.color = self.color_id[1]
        self.type_image.type_label.color = self.color_id[1]
        self.type_image.version_label.color = self.color_id[1]

        self.title.opacity = 1
        self.subtitle.opacity = self.subtitle.default_opacity
        self.hover_text.opacity = 0
        self.hover_text.text = getattr(self.properties, 'name', '') if self.properties else ''
        self.type_image.image.opacity = 1 if self.metadata_loaded else 0
        self.type_image.type_label.opacity = 1 if self.metadata_loaded else 0
        self.type_image.version_label.opacity = 0.6 if self.metadata_loaded else 0
        self.loading_text.opacity = 0 if self.metadata_loaded else 0.6

        self._set_radio(False, False)

    def animate_button(self, image, color, hover_action, radio_hover=None, **kwargs):
        duration = 0.06

        Animation(color=color, duration=duration).start(self.title)
        Animation(color=color, duration=duration).start(self.subtitle)
        Animation(color=color, duration=duration).start(self.type_image.image)
        Animation(color=color, duration=duration).start(self.type_image.version_label)
        Animation(color=color, duration=duration).start(self.type_image.type_label)

        self._set_radio(hover_action if radio_hover is None else radio_hover)
        animate_background(self.button, image, hover_action, **kwargs)

    def on_enter(self, *args):
        if self.button.ignore_hover: return

        for widget in (
            self.title, self.subtitle, self.hover_text,
            self.type_image.image, self.type_image.type_label,
            self.type_image.version_label
        ):
            Animation.stop_all(widget)

        # Keep normal appearance; hover only scales the card
        self.animate_button(self._normal_image(), self.color_id[1], True, radio_hover=False, _no_bg_change=True)

        if self.selected and self.actions:
            self._show_actions()

            Animation(opacity=0, duration=0.06).start(self.title)
            Animation(opacity=0, duration=0.06).start(self.subtitle)
            Animation(opacity=1, duration=0.06).start(self.hover_text)

            Animation(opacity=0, duration=0.06).start(self.type_image.image)
            Animation(opacity=0, duration=0.06).start(self.type_image.type_label)
            Animation(opacity=0, duration=0.06).start(self.type_image.version_label)
            Animation(opacity=0, duration=0.06).start(self.loading_text)

    def on_leave(self, *args):
        if self.button.ignore_hover: return

        for widget in (
            self.title, self.subtitle, self.hover_text,
            self.type_image.image, self.type_image.type_label,
            self.type_image.version_label
        ):
            Animation.stop_all(widget)

        self._hide_actions()
        self.animate_button(self._normal_image(), self.color_id[1], False, radio_hover=False, _no_bg_change=True)

        Animation(opacity=1, duration=0.06).start(self.title)
        Animation(opacity=self.subtitle.default_opacity, duration=0.06).start(self.subtitle)
        Animation(opacity=0, duration=0.06).start(self.hover_text)

        Animation(opacity=1 if self.metadata_loaded else 0, duration=0.06).start(self.type_image.image)
        Animation(opacity=1 if self.metadata_loaded else 0, duration=0.06).start(self.type_image.type_label)
        Animation(opacity=0.6 if self.metadata_loaded else 0, duration=0.06).start(self.type_image.version_label)
        Animation(opacity=0 if self.metadata_loaded else 0.6, duration=0.06).start(self.loading_text)

    def _primary_click(self, *args):
        if any(button.button.hovered for button in self.action_buttons):
            return

        self._reset_visuals(True)

        if self.click_function:
            self.click_function(self.view_index, True)

    def set_selected(self, selected, animate=False):
        self.selected = selected
        self.button.background_normal = self._normal_image()
        self._set_radio(False, animate)

        if self.button.hovered:
            if selected and self.actions: self._show_actions()
            else:                         self._hide_actions()

    def set_depth(self, depth):
        distance = min(abs(depth), 5)
        scale = max(0.84, 1 - (distance * 0.035))

        self.depth = depth
        self.depth_scale.x = scale
        self.depth_scale.y = scale
        self.opacity = 1 if self.selected else max(0.18, 1 - (distance * 0.16))

    def change_data(self, data):
        self._reset_visuals(True)

        self.view_index = data['index']
        self.properties = data['item']
        self.click_function = data.get('click_function')
        self.selected = data.get('selected', False)
        self._set_actions(data.get('actions') or [])

        backup_object = self.properties
        self.metadata_loaded = getattr(backup_object, 'metadata_loaded', True)

        self.title.text = backup_object.name
        self.subtitle.text = backup_object.date
        self.hover_text.text = backup_object.name

        if self.metadata_loaded:
            icon = os.path.join(paths.ui_assets, 'icons', 'big', f'{backup_object.type.lower()}_small.png')
            if not os.path.exists(icon):
                icon = os.path.join(paths.ui_assets, 'icons', 'big', 'unknown_small.png')

            self.type_image.image.source = icon
            self.type_image.type_label.text = backup_object.type.lower().replace('craft', '')

            if backup_object.build:
                self.type_image.version_label.text = f'{backup_object.version.lower()} (b-{backup_object.build.lower()})'
            else:
                self.type_image.version_label.text = backup_object.version.lower()

            self.loading_text.text = ''

        else:
            self.type_image.type_label.text = ''
            self.type_image.version_label.text = ''
            self.loading_text.text = 'loading...'

        scrolling = data.get('is_scrolling')
        if callable(scrolling): scrolling = scrolling()

        self.button.ignore_hover = bool(scrolling)

        self.resize_self()
        self.set_selected(self.selected)
        self._reset_visuals(bool(scrolling))

        position = data.get('position')
        depth = self.view_index - position() if callable(position) else data.get('depth', 0)
        self.set_depth(depth)

    def resize_button(self, *args):
        button = self.button

        # Title / subtitle - copied directly from BackupButton
        padding = 2.17

        self.title.pos = (
            button.x + (self.title.text_size[0] / padding) + 30,
            button.y + 31
        )

        self.subtitle.pos = (
            button.x + (self.subtitle.text_size[0] / padding) - 1 + 30 - 100,
            button.y + 8
        )

        # Radio replaces the old 44x44 index icon
        radio_pos = (button.x + 8, button.y + 18)

        self.radio_ring_widget.pos = radio_pos
        self.radio_dot_widget.pos = radio_pos

        radio_x = button.x + 30
        radio_y = button.y + 40

        self.radio_ring.circle = (radio_x, radio_y, dp(11))
        self.radio_dot.pos = (radio_x - dp(5), radio_y - dp(5))


        # Type / version - copied directly from BackupButton
        offset = 9.45 if self.type_image.type_label.text in ['vanilla', 'paper', 'purpur'] \
            else 9.6 if self.type_image.type_label.text == 'forge' \
            else 9.35 if self.type_image.type_label.text == 'craftbukkit' \
            else 9.55

        self.type_image.image.x = button.width + button.x - self.type_image.image.width - 13
        self.type_image.image.y = button.y + ((button.height / 2) - (self.type_image.image.height / 2))

        self.type_image.type_label.x = button.width + button.x - (button.padding_x * offset) - self.type_image.width - 83
        self.type_image.type_label.y = button.y + (button.height * 0.05)

        self.type_image.version_label.x = button.width + button.x - (button.padding_x * offset) - self.type_image.width - 83
        self.type_image.version_label.y = button.y - (button.height / 3.2)

        self.loading_text.pos = (
            button.x + button.width - self.loading_text.width + 20,
            button.y
        )


        # Actions
        self.action_layout.pos = button.pos
        self.action_layout.size = button.size

        self.action_row.pos = (button.width - self.action_row.width - 12, 0)
        self.action_text.pos = (self.action_row.x - 155, 0)
        self.action_text.size = (145, button.height)
        self.action_text.text_size = self.action_text.size

        # Shortened title while actions are visible
        self.hover_text.pos = (button.x + 55, button.y)
        self.hover_text.size = (self.action_text.x - 75, button.height)
        self.hover_text.text_size = self.hover_text.size

    def resize_self(self, *args):
        self.card.size = (620, 88)
        self.card.center = (self.width / 2, self.height / 2)

        self.button.size = (580, 80)
        self.button.pos = (
            (self.card.width - self.button.width) / 2,
            (self.card.height - self.button.height) / 2
        )

        self.depth_scale.origin = self.card.center
        self.resize_button()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.id = 'history_item'
        self.height = 100
        self.size_hint_y = None

        self.history_data = None
        self.view_index = 0
        self.properties = None

        self.depth = 0
        self.selected = False
        self.click_function = None
        self.metadata_loaded = True

        self.is_loading = False
        self._init_actions()

        self.color_id = [
            (0.05, 0.05, 0.1, 1),
            constants.brighten_color((0.65, 0.65, 1, 1), 0.07)
        ]

        self.original_font = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["regular"]}.ttf')


        # Depth transform
        with self.canvas.before:
            self.depth_push = PushMatrix()
            self.depth_scale = Scale(1, 1, 1, origin=self.center)

        with self.canvas.after:
            self.depth_pop = PopMatrix()


        # Inner card isolates hover scale from depth scale
        self.card = RelativeLayout(size_hint=(None, None))
        self.add_widget(self.card)


        # Main button
        self.button = HoverButton()
        self.button.id = 'server_button'
        self.button.color_id = self.color_id
        self.button.border = (-5, -5, -5, -5)
        self.button.size_hint = (None, None)
        self.button.background_normal = self._normal_image()
        self.button.background_down = os.path.join(paths.ui_assets, 'server_button_click.png')

        self.button.on_enter = self.on_enter
        self.button.on_leave = self.on_leave
        self.button.bind(on_press=self._primary_click)

        self.card.add_widget(self.button)

        # Title
        self.title = Label()
        self.title.__translate__ = False
        self.title.id = 'title'
        self.title.halign = 'left'
        self.title.color = self.color_id[1]
        self.title.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
        self.title.font_size = sp(25)
        self.title.text_size = (580 * 0.94, 80)
        self.title.shorten = True
        self.title.markup = True
        self.title.shorten_from = 'right'
        self.title.max_lines = 1
        self.button.add_widget(self.title)

        # Date
        self.subtitle = Label()
        self.subtitle.__translate__ = False
        self.subtitle.size = (300, 30)
        self.subtitle.id = 'subtitle'
        self.subtitle.halign = 'left'
        self.subtitle.valign = 'center'
        self.subtitle.font_size = sp(21)
        self.subtitle.text_size = (580 * 0.91, 80)
        self.subtitle.shorten = True
        self.subtitle.markup = True
        self.subtitle.shorten_from = 'right'
        self.subtitle.max_lines = 1
        self.subtitle.color = self.color_id[1]
        self.subtitle.default_opacity = 0.56
        self.subtitle.font_name = self.original_font
        self.subtitle.opacity = self.subtitle.default_opacity
        self.button.add_widget(self.subtitle)

        # Hover title
        self.hover_text = Label()
        self.hover_text.__translate__ = False
        self.hover_text.id = 'hover_text'
        self.hover_text.size_hint = (None, None)
        self.hover_text.halign = 'left'
        self.hover_text.valign = 'middle'
        self.hover_text.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
        self.hover_text.font_size = sp(25)
        self.hover_text.color = self.color_id[1]
        self.hover_text.opacity = 0
        self.hover_text.shorten = True
        self.hover_text.shorten_from = 'right'
        self.hover_text.max_lines = 1
        self.button.add_widget(self.hover_text)

        # Type icon / version
        self.type_image = RelativeLayout()
        self.type_image.width = 400

        self.type_image.image = Image()
        self.type_image.image.allow_stretch = True
        self.type_image.image.size_hint_max = (65, 65)
        self.type_image.image.color = self.color_id[1]
        self.type_image.add_widget(self.type_image.image)

        def TemplateLabel():
            template_label = AlignLabel()
            template_label.__translate__ = False
            template_label.halign = 'right'
            template_label.valign = 'middle'
            template_label.text_size = template_label.size
            template_label.font_size = sp(19)
            template_label.color = self.color_id[1]
            template_label.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
            template_label.width = 150
            return template_label

        self.type_image.version_label = TemplateLabel()
        self.type_image.version_label.opacity = 0.6

        self.type_image.type_label = TemplateLabel()
        self.type_image.type_label.font_size = sp(23)

        self.type_image.add_widget(self.type_image.version_label)
        self.type_image.add_widget(self.type_image.type_label)
        self.button.add_widget(self.type_image)


        # Lazy metadata loading
        self.loading_text = Label()
        self.loading_text.__translate__ = False
        self.loading_text.size_hint = (None, None)
        self.loading_text.size = (180, 80)
        self.loading_text.text_size = self.loading_text.size
        self.loading_text.halign = 'center'
        self.loading_text.valign = 'middle'
        self.loading_text.font_size = sp(20)
        self.loading_text.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
        self.loading_text.color = self.color_id[1]
        self.loading_text.opacity = 0
        self.button.add_widget(self.loading_text)


        # Action bar layout
        self.card.add_widget(self.action_layout)


        # Selection radio
        base_color = self.color_id[1]
        self.radio_rgba = [*base_color[:3], 1]

        self.radio_ring_widget = Widget(size_hint=(None, None), size=(44, 44), opacity=1)
        with self.radio_ring_widget.canvas:
            self.radio_ring_color = Color(*self.radio_rgba)
            self.radio_ring = Line(circle=(0, 0, dp(11)), width=dp(1.4))

        self.button.add_widget(self.radio_ring_widget)

        self.radio_dot_widget = Widget(size_hint=(None, None), size=(44, 44), opacity=0)
        with self.radio_dot_widget.canvas:
            self.radio_dot_color = Color(*self.radio_rgba)
            self.radio_dot = Ellipse(size=(dp(10), dp(10)))

        self.button.add_widget(self.radio_dot_widget)

        self.bind(
            radio_rgba=lambda _, value: (
                setattr(self.radio_ring_color, 'rgba', value),
                setattr(self.radio_dot_color, 'rgba', value)
            )
        )

        self.bind(pos=self.resize_self, size=self.resize_self)
        Clock.schedule_once(self.resize_self, 0)

        if self.history_data:
            self.change_data(self.history_data)


# Right-side button for BaseInput-derived TextInputs
class InputButton(FloatLayout):
    def __init__(self, name, position, file=(), input_callback=None, title=None, ext_list=[], offset=0, **kwargs):
        super().__init__(**kwargs)
        self.x += (190 + offset)

        self.button = HoverButton()
        self.button.id = 'input_button'
        self.button.color_id = [(0.05, 0.05, 0.1, 1), (0.6, 0.6, 1, 1)]

        self.button.size_hint_max = (151, 58)
        self.button.pos_hint = {"center_x": position[0], "center_y": position[1]}
        self.button.border = (0, 0, 0, 0)
        self.button.background_normal = os.path.join(paths.ui_assets, 'input_button.png')
        self.button.background_down = os.path.join(paths.ui_assets, 'input_button_click.png')

        self.text = Label()
        self.text.id = 'text'
        self.text.size_hint = (None, None)
        self.text.pos_hint = {"center_x": position[0], "center_y": position[1]}
        self.text.text = name.upper()
        self.text.font_size = sp(17)
        self.text.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["bold"]}.ttf')
        self.text.color = (0.6, 0.6, 1, 1)

        # Button click behavior
        if file: self.button.on_release = functools.partial(file_popup, file[0], file[1], ext_list, input_callback, title=title)
        else:    self.button.on_release = functools.partial(button_action, name, self.button)

        self.add_widget(self.button)
        self.add_widget(self.text)



# -------------------------------------------------  Icon Buttons  -----------------------------------------------------

# Small circular button that shows an icon and tooltip
class IconButton(FloatLayout):

    def change_data(self, icon=None, text=None, click_func=None):
        if icon: self.icon.source = icon_path(icon)

        if text: self.text.text = text.lower()

        if click_func:
            def _check_disabled():
                if not self.disabled and not self.button.disabled: click_func()
            self.button.on_release = functools.partial(_check_disabled)

    def resize(self, *args):
        self.x = Window.width - self.default_pos[0]
        self.y = Window.height - self.default_pos[1]

        if self.default_pos:
            self.button.pos = (self.x + 11, self.y)
            self.icon.pos = (self.x, self.y - 11)

            if self.anchor == "left":
                self.text.pos = (self.x - 10, self.y + 17)
                if self.text.pos[0] <= 0:
                    self.text.pos[0] += sp(len(self.text.text) * 3)

            elif self.anchor == "right":
                self.text.pos = (self.x - 4, self.y - 17)
                if self.text.pos[0] >= Window.width - self.button.width * 2:
                    self.text.pos[0] -= sp(len(self.text.text) * 3)
                    self.text.pos[1] -= self.button.height

        if self.text.offset[0] != 0 or self.text.offset[1] != 0:
            self.text.pos[0] = self.text.pos[0] - self.text.offset[0]
            self.text.pos[1] = self.text.pos[1] - self.text.offset[1]

    def __init__(self, name, pos_hint, position, size_hint, icon_name=None, clickable=True, force_color=None, anchor='left', click_func=None, text_offset=(0, 0), text_hover_color=None, **kwargs):
        super().__init__(**kwargs)

        self.default_pos = position
        self.anchor = anchor

        self.button = HoverButton()
        self.button.id = 'icon_button'
        self.button.color_id = [(0.05, 0.05, 0.1, 1), (0.6, 0.6, 1, 1)] if not force_color else force_color[0]

        if force_color and force_color[1]: self.button.alt_color = "_" + force_color[1]

        self.button.size_hint = size_hint
        self.button.size = (dp(50), dp(50))
        self.button.pos_hint = pos_hint

        if position: self.button.pos = (position[0] + 11, position[1])

        self.button.border = (0, 0, 0, 0)
        self.button.background_normal = os.path.join(paths.ui_assets, f'{self.button.id}.png')

        if not force_color or not force_color[1]:
            self.button.background_down = os.path.join(paths.ui_assets, f'{self.button.id}_click.png' if clickable else f'{self.button.id}_hover.png')
        else:
            self.button.background_down = os.path.join(paths.ui_assets, f'{self.button.id}_click_{force_color[1]}.png' if clickable else f'{self.button.id}_hover_{force_color[1]}.png')

        self.text = Label()
        self.text.id = 'text'
        self.text.size_hint = size_hint
        self.text.pos_hint = pos_hint
        self.text.text = name.lower()
        self.text.hover_color = text_hover_color if text_hover_color else None
        self.text.font_size = sp(19)
        self.text.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
        self.text.color = (0, 0, 0, 0)
        self.text.offset = text_offset

        if position: self.text.pos = (position[0] - 10, position[1] + 17)

        if self.text.pos[0] <= 0: self.text.pos[0] += sp(len(self.text.text) * 3)

        if self.text.offset[0] != 0 or self.text.offset[1] != 0:
            self.text.pos[0] = self.text.pos[0] - self.text.offset[0]
            self.text.pos[1] = self.text.pos[1] - self.text.offset[1]

        # Button click behavior
        if clickable:
            def _check_disabled():
                if not self.disabled and not self.button.disabled:
                    if click_func: click_func()
                    else: button_action(name, self.button)
            self.button.on_release = functools.partial(_check_disabled)


        self.add_widget(self.button)

        if icon_name:
            self.icon = Image()
            self.icon.id = 'icon'
            self.icon.size_hint = size_hint
            self.icon.source = icon_path(icon_name)
            self.icon.size = (dp(72), dp(72))
            self.icon.color = self.button.color_id[1]
            self.icon.pos_hint = pos_hint

            if position: self.icon.pos = (position[0], position[1] - 11)

            self.add_widget(self.icon)

        self.add_widget(self.text)

        # Check for right float
        if anchor == "right":
            self.bind(size=self.resize)
            self.bind(pos=self.resize)


# Similar to 'IconButton', but has a more flexible positioning style
class RelativeIconButton(RelativeLayout):

    def change_data(self, icon=None, text=None, click_func=None):
        if icon: self.icon.source = icon_path(icon)

        if text: self.text.text = text.lower()

        if click_func:
            def _check_disabled():
                if not self.disabled and not self.button.disabled: click_func()
            self.button.on_release = functools.partial(_check_disabled)

    def resize(self, *args):
        self.text.x = Window.width - self.text.texture_size[0] + 25
        if self.text_offset: self.text.x += self.text_offset[0]

    def on_hover(self, hovered=False, *a):
        pass

    def __init__(self, name, pos_hint, position, size_hint, icon_name=None, clickable=True, force_color=None, anchor='left', click_func=None, text_offset=(0, 0), text_hover_color=None, anchor_text=None, **kwargs):
        super().__init__(**kwargs)

        self.default_pos = position
        self.anchor = anchor

        self.button = HoverButton()
        self.button.id = 'icon_button'
        self.button.color_id = [(0.05, 0.05, 0.1, 1), (0.6, 0.6, 1, 1)] if not force_color else force_color[0]
        self.text_offset = text_offset

        if force_color and force_color[1]: self.button.alt_color = "_" + force_color[1]

        self.button.size_hint = size_hint
        self.button.size = (dp(50), dp(50))
        self.button.pos_hint = pos_hint

        if position: self.button.pos = (position[0] + 11, position[1])

        self.button.border = (0, 0, 0, 0)
        self.button.background_normal = os.path.join(paths.ui_assets, f'{self.button.id}.png')

        if not force_color or not force_color[1]:
            self.button.background_down = os.path.join(paths.ui_assets, f'{self.button.id}_click.png' if clickable else f'{self.button.id}_hover.png')
        else:
            self.button.background_down = os.path.join(paths.ui_assets, f'{self.button.id}_click_{force_color[1]}.png' if clickable else f'{self.button.id}_hover_{force_color[1]}.png')


        if anchor_text:
            self.text = AlignLabel()
            self.text.halign = anchor_text
        else:
            self.text = Label()

        self.text.id = 'text'
        self.text.size_hint = size_hint
        if pos_hint and not anchor_text: self.text.pos_hint = pos_hint
        self.text.text = name.lower()
        self.text.hover_color = text_hover_color if text_hover_color else None
        self.text.font_size = sp(19)
        self.text.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
        self.text.color = (0, 0, 0, 0)
        self.text.offset = text_offset

        if position: self.text.pos = (position[0] - 10, position[1] + 17)

        if self.text.pos[0] <= 0: self.text.pos[0] += sp(len(self.text.text) * 3)

        self.text.original_pos = self.text.pos

        if self.text.offset[0] != 0 or self.text.offset[1] != 0:
            self.text.pos[0] = self.text.original_pos[0] - self.text.offset[0]
            self.text.pos[1] = self.text.original_pos[1] - self.text.offset[1]


        if clickable:
            # Button click behavior
            if click_func: self.button.on_release = functools.partial(click_func)
            else:          self.button.on_release = functools.partial(button_action, name, self.button)


        self.add_widget(self.button)

        if icon_name:
            self.icon = Image()
            self.icon.id = 'icon'
            self.icon.size_hint = size_hint
            self.icon.source = icon_path(icon_name)
            self.icon.size = (dp(72), dp(72))
            self.icon.color = self.button.color_id[1]
            if pos_hint: self.icon.pos_hint = pos_hint

            if position: self.icon.pos = (position[0], position[1] - 11)

            self.add_widget(self.icon)

        self.add_widget(self.text)

        if anchor_text == "right":
            self.bind(size=self.resize)
            self.bind(pos=self.resize)

        if utility.screen_manager.current_screen.name == 'MainMenuScreen':
            Clock.schedule_once(self.text.texture_update, 0)
            Clock.schedule_once(self.resize, 0)

        # Hover hook
        self.button.bind(on_enter=lambda *_: self.on_hover(True))
        self.button.bind(on_leave=lambda *_: self.on_hover(False))


# Similar to 'IconButton', but supported an animated icon instead
class AnimButton(FloatLayout):

    def resize(self, *args):
        self.x = Window.width - self.default_pos[0]
        self.y = Window.height - self.default_pos[1]

        if self.default_pos:
            self.button.pos = (self.x + 11, self.y)
            self.icon.pos = (self.x, self.y - 11)

            if self.anchor == "left":
                self.text.pos = (self.x - 10, self.y + 17)
                if self.text.pos[0] <= 0: self.text.pos[0] += sp(len(self.text.text) * 3)

            elif self.anchor == "right":
                self.text.pos = (self.x - 4, self.y - 17)
                if self.text.pos[0] >= Window.width - self.button.width * 2:
                    self.text.pos[0] -= sp(len(self.text.text) * 3)
                    self.text.pos[1] -= self.button.height

    def __init__(self, name, pos_hint, position, size_hint, icon_name=None, clickable=True, force_color=None, anchor='left', click_func=None, text_hover_color=None, **kwargs):
        super().__init__(**kwargs)

        self.default_pos = position
        self.anchor = anchor

        self.button = HoverButton()
        self.button.id = 'icon_button'
        self.button.color_id = [(0.05, 0.05, 0.1, 1), (0.6, 0.6, 1, 1)] if not force_color else force_color[0]

        if force_color: self.button.alt_color = "_" + force_color[1]

        self.button.size_hint = size_hint
        self.button.size = (dp(50), dp(50))
        self.button.pos_hint = pos_hint

        if position: self.button.pos = (position[0] + 11, position[1])

        self.button.border = (0, 0, 0, 0)
        self.button.background_normal = os.path.join(paths.ui_assets, f'{self.button.id}.png')

        if not force_color:
            self.button.background_down = os.path.join(paths.ui_assets, f'{self.button.id}_click.png' if clickable else f'{self.button.id}_hover.png')
        else:
            self.button.background_down = os.path.join(paths.ui_assets, f'{self.button.id}_click_{force_color[1]}.png' if clickable else f'{self.button.id}_hover_{force_color[1]}.png')

        self.text = Label()
        self.text.id = 'text'
        self.text.size_hint = size_hint
        self.text.pos_hint = pos_hint
        self.text.text = name.lower()
        self.text.hover_color = text_hover_color if text_hover_color else None
        self.text.font_size = sp(19)
        self.text.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
        self.text.color = (0, 0, 0, 0)

        if position: self.text.pos = (position[0] - 10, position[1] + 17)

        if self.text.pos[0] <= 0: self.text.pos[0] += sp(len(self.text.text) * 3)

        # Button click behavior
        if clickable:
            def _check_disabled():
                if not self.disabled and not self.button.disabled:
                    if click_func: click_func()
                    else: button_action(name, self.button)
            self.button.on_release = functools.partial(_check_disabled)

        self.add_widget(self.button)

        if icon_name:
            self.icon = AsyncImage()
            self.icon.id = 'icon'
            self.icon.source = os.path.join(paths.ui_assets, 'animations', icon_name)
            self.icon.size_hint_max = (dp(45), dp(45))
            self.icon.color = self.button.color_id[1]
            self.icon.pos_hint = pos_hint
            self.icon.allow_stretch = True
            self.icon.anim_delay = utility.anim_speed * 0.02

            if position:
                self.icon.texture_update()
                self.icon.pos = (self.button.pos[0] + 2.2, self.button.pos[1] + 2.2)

            self.add_widget(self.icon)

        self.add_widget(self.text)

        # Check for right float
        if anchor == "right":
            self.bind(size=self.resize)
            self.bind(pos=self.resize)



# ------------------------------------------------ Big Icon Buttons  ---------------------------------------------------

# Paired multi-layout big buttons with a large icon, border, and tooltip
class BigIcon(HoverButton):
    def __init__(self):
        super().__init__(hover_scale = 1.06)

    def on_enter(self, *a, **kw):
        if self.selected: kw['_no_bg_change'] = True
        return super().on_enter(*a, **kw)

    def on_leave(self, *a, **kw):
        if self.selected: kw['_no_bg_change'] = True
        return super().on_leave(*a, **kw)

    def deselect(self):
        self.selected = False
        for child in [x for x in self.parent.children if x.id == "icon"]:
            if child.type == self.type: self.on_leave(duration=0)
        self.background_normal = os.path.join(paths.ui_assets, f'{self.id}.png')
        self.background_down   = os.path.join(paths.ui_assets, f'{self.id}_click.png')
        self.background_hover  = os.path.join(paths.ui_assets, f'{self.id}_hover.png')

    def on_click(self):
        cl1 = utility.screen_manager.current_screen.content_layout_1
        cl2 = utility.screen_manager.current_screen.content_layout_2

        if self.type == 'more':
            self.on_leave(duration=0)
            self.hovered = False
            def _swap(*a):
                if cl2.opacity == 0:
                    utility.hide_widget(cl2, False)
                    utility.hide_widget(cl1)
                else:
                    utility.hide_widget(cl1, False)
                    utility.hide_widget(cl2)
            return Clock.schedule_once(_swap, -1)


        def iterator(layout, *a):
            for item in layout.children:
                for child_item in item.children:
                    for child_button in child_item.children:
                        if child_button.id == 'big_icon_button':

                            if child_button.type == 'more':
                                child_button.deselect()
                                continue

                            if child_button.hovered:
                                child_button.selected = True
                                child_button.on_enter()
                                child_button.background_down = os.path.join(paths.ui_assets, f'{child_button.id}_selected.png')
                                foundry.new_server_info['type'] = child_button.type

                            else: child_button.deselect()
                            break

        iterator(cl1)
        iterator(cl2)


# BigIcon specifically for the CreateServerModeScreen
class BigModeButton(RelativeLayout):
    def __init__(self, name, pos_hint, position, size_hint, icon_name=None, clickable=True, force_color=None, text_hover_color=None, click_func=None, **kw):
        super().__init__(**kw)
        self.size_hint_max_y = dp(150)
        self.pos_hint = {'center_y': 0.5, 'center_x': 0.5}
        self.anchor_x = 'center'

        self.button = BigIcon()
        self.button.id = 'big_icon_button'
        self.button.color_id = [(0.47, 0.52, 1, 1), (0.6, 0.6, 1, 1)] if not force_color else force_color[0]
        self.button.type = icon_name

        if force_color: self.button.alt_color = "_" + force_color[1]

        self.button.size_hint = size_hint
        self.button.size = (dp(150), dp(150))
        self.button.pos_hint = pos_hint

        if position: self.button.pos = (position[0] + 11, position[1])

        self.button.border = (0, 0, 0, 0)
        self.button.background_normal = os.path.join(paths.ui_assets, f'{self.button.id}.png')

        if not force_color:
            if self.button.selected: self.button.background_down = os.path.join(paths.ui_assets, f'{self.button.id}_selected.png')
            else:                    self.button.background_down = os.path.join(paths.ui_assets, f'{self.button.id}_click.png' if clickable else f'{self.button.id}_hover.png')

        else: self.button.background_down = os.path.join(paths.ui_assets, f'{self.button.id}_click_{force_color[1]}.png' if clickable else f'{self.button.id}_hover_{force_color[1]}.png')

        self.text = Label()
        self.text.id = 'text'
        self.text.size_hint = size_hint
        self.text.pos_hint = {'center_x': pos_hint['center_x'], 'center_y': pos_hint['center_y'] - 0.11}
        self.text.text = name.lower()
        self.text.hover_color = text_hover_color if text_hover_color else None
        self.text.font_size = sp(19)
        self.text.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
        self.text.color = (0, 0, 0, 0)

        if position: self.text.pos = (position[0] - 10, position[1] - 17)

        if self.text.pos[0] <= 0: self.text.pos[0] += sp(len(self.text.text) * 3)


        # Button click behavior
        if clickable and click_func: self.button.on_release = functools.partial(click_func)


        self.add_widget(self.button)

        if icon_name:
            self.icon = Image()
            self.icon.id = 'icon'
            self.icon.type = self.button.type
            self.icon.size_hint = size_hint
            self.icon.source = icon_path(os.path.join('big', 'modes', f'{icon_name}.png'))
            self.icon.size = (dp(125), dp(125))
            self.icon.color = self.button.color_id[1]
            self.icon.pos_hint = {'center_x': pos_hint['center_x'], 'center_y': pos_hint['center_y'] + 0.005}

            if position: self.icon.pos = (position[0], position[1] - 11)

            self.add_widget(self.icon)


            self.icon_text = Label()
            self.icon_text.id = 'icon'
            self.icon_text.size_hint_max = (130, 120)
            self.icon_text.text_size = (130, 120)
            self.icon_text.halign = 'center'
            self.icon_text.pos_hint = {"center_x": 0.5, "center_y": 0.5}
            self.icon_text.text = icon_name.lower()
            self.icon_text.font_size = sp(23)
            self.icon_text.font_name = os.path.join(paths.ui_assets, 'fonts', 'CenturyGothic.ttf')
            self.icon_text.color = (0.6, 0.6, 1, 1)

            self.add_widget(self.icon_text)

        self.add_widget(self.text)


# BigIcon specifically for the CreateServerTypeScreen, MigrateServerTypeScreen
class BigIconButton(FloatLayout):

    def __init__(self, name, pos_hint, position, size_hint, icon_name=None, clickable=True, force_color=None, selected=False, text_hover_color=None, **kwargs):
        super().__init__(**kwargs)

        self.button = BigIcon()
        self.button.selected = selected
        self.button.id = 'big_icon_button'
        self.button.color_id = [(0.47, 0.52, 1, 1), (0.6, 0.6, 1, 1)] if not force_color else force_color[0]
        self.button.type = icon_name

        if force_color: self.button.alt_color = "_" + force_color[1]

        self.button.size_hint = size_hint
        self.button.size = (dp(150), dp(150))
        self.button.pos_hint = pos_hint

        if position: self.button.pos = (position[0] + 11, position[1])

        self.button.border = (0, 0, 0, 0)
        self.button.background_normal = os.path.join(paths.ui_assets, f'{self.button.id}{"_selected" if selected else ""}.png')

        if not force_color:
            if self.button.selected: self.button.background_down = os.path.join(paths.ui_assets, f'{self.button.id}_selected.png')
            else:                    self.button.background_down = os.path.join(paths.ui_assets, f'{self.button.id}_click.png' if clickable else f'{self.button.id}_hover.png')
        else:                        self.button.background_down = os.path.join(paths.ui_assets, f'{self.button.id}_click_{force_color[1]}.png' if clickable else f'{self.button.id}_hover_{force_color[1]}.png')

        self.text = Label()
        self.text.id = 'text'
        self.text.size_hint = size_hint
        self.text.pos_hint = {'center_x': pos_hint['center_x'], 'center_y': pos_hint['center_y'] - 0.11}
        self.text.text = name.lower()
        self.text.hover_color = text_hover_color if text_hover_color else None
        self.text.font_size = sp(19)
        self.text.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
        self.text.color = (0, 0, 0, 0)

        if position: self.text.pos = (position[0] - 10, position[1] - 17)

        if self.text.pos[0] <= 0: self.text.pos[0] += sp(len(self.text.text) * 3)

        # Button click behavior
        if clickable: self.button.on_release = functools.partial(self.button.on_click)

        self.add_widget(self.button)

        if icon_name:
            self.icon = Image()
            self.icon.id = 'icon'
            self.icon.type = self.button.type
            self.icon.size_hint = size_hint
            self.icon.source = icon_path(os.path.join('big', f'{icon_name}.png'))
            self.icon.size = (dp(125), dp(125))
            self.icon.color = self.button.color_id[1] if not selected else (0.05, 0.05, 0.1, 1)
            self.icon.pos_hint = pos_hint

            if position: self.icon.pos = (position[0], position[1] - 11)

            self.add_widget(self.icon)

        self.add_widget(self.text)
