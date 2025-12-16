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

            elif "import" in button_name.lower():
                title = "Select Add-on Files (.jar)"
                selection = file_popup("file", start_dir=paths.user_downloads, ext=["*.jar"], input_name=None, select_multiple=True, title=title)

                if selection:
                    banner_text = ''
                    for addon in selection:
                        if addon.endswith(".jar") and os.path.isfile(addon):
                            addon = addons.get_addon_file(addon, foundry.new_server_info)
                            foundry.new_server_info['addon_objects'].append(addon)
                            utility.screen_manager.current_screen.gen_search_results(foundry.new_server_info['addon_objects'])

                            # Switch pages if page is full
                            if (len(utility.screen_manager.current_screen.scroll_layout.children) == 0) and (len(foundry.new_server_info['addon_objects']) > 0):
                                utility.screen_manager.current_screen.switch_page("right")

                            # Show banner
                            if len(selection) == 1:
                                if len(addon.name) < 26: addon_name = addon.name
                                else:                    addon_name = addon.name[:23] + "..."
                                banner_text = f"Added '${addon_name}$' to the queue"
                            else: banner_text = f"Added ${len(selection)}$ add-ons to the queue"

                    if banner_text:
                        Clock.schedule_once(
                            functools.partial(
                                utility.screen_manager.current_screen.show_banner,
                                (0.553, 0.902, 0.675, 1),
                                banner_text,
                                "add-circle-sharp.png",
                                2.5,
                                {"center_x": 0.5, "center_y": 0.965}
                            ), 0
                        )


        elif "ServerAddonScreen" in str(utility.screen_manager.current_screen):
            addon_manager = constants.server_manager.current_server.addon

            if "download" in button_name.lower():
                utility.screen_manager.current = 'ServerAddonSearchScreen'

            elif "import" in button_name.lower():
                title = "Select Add-on Files (.jar)"
                selection = file_popup("file", start_dir=paths.user_downloads, ext=["*.jar"], input_name=None, select_multiple=True, title=title)

                if selection:
                    banner_text = ''
                    for addon in selection:
                        if addon.endswith(".jar") and os.path.isfile(addon):
                            addon = addon_manager.import_addon(addon)
                            addon_list = addon_manager.return_single_list()
                            utility.screen_manager.current_screen.gen_search_results(addon_manager.return_single_list(), fade_in=False, highlight=addon.hash, animate_scroll=True)

                            # Switch pages if page is full
                            if (len(utility.screen_manager.current_screen.scroll_layout.children) == 0) and (len(addon_list) > 0):
                                utility.screen_manager.current_screen.switch_page("right")

                            # Show banner
                            if len(selection) == 1:
                                if len(addon.name) < 26: addon_name = addon.name
                                else:                    addon_name = addon.name[:23] + "..."
                                banner_text = f"Imported '${addon_name}$'"
                            else: banner_text = f"Imported ${len(selection)}$ add-ons"

                    if banner_text:

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
                                    (0.553, 0.902, 0.675, 1),
                                    banner_text,
                                    "add-circle-sharp.png",
                                    2.5,
                                    {"center_x": 0.5, "center_y": 0.965}
                                ), 0
                            )


        elif "ServerAmscriptScreen" in str(utility.screen_manager.current_screen):
            script_manager = constants.server_manager.current_server.script_manager

            if "download" in button_name.lower():
                utility.screen_manager.current = 'ServerAmscriptSearchScreen'

            elif "create new" in button_name.lower():
                utility.screen_manager.current = 'CreateAmscriptScreen'

            elif "import" in button_name.lower():
                title = "Select amscripts (.ams)"
                selection = file_popup("file", start_dir=paths.user_downloads, ext=["*.ams"], input_name=None, select_multiple=True, title=title)

                if selection:
                    banner_text = ''
                    for script in selection:
                        if script.endswith(".ams") and os.path.isfile(script):
                            script = script_manager.import_script(script)
                            if not script:
                                continue

                            script_list = script_manager.return_single_list()
                            utility.screen_manager.current_screen.gen_search_results(script_manager.return_single_list(), fade_in=False, highlight=script.hash, animate_scroll=True)

                            # Switch pages if page is full
                            if (len(utility.screen_manager.current_screen.scroll_layout.children) == 0) and (len(script_list) > 0):
                                utility.screen_manager.current_screen.switch_page("right")

                            # Show banner
                            if len(selection) == 1:
                                if len(script.title) < 26: script_name = script.title
                                else:                      script_name = script.title[:23] + "..."
                                banner_text = f"Imported '${script_name}$'"
                            else: banner_text = f"Imported ${len(selection)}$ scripts"

                    if banner_text:

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
                                    (0.553, 0.902, 0.675, 1),
                                    banner_text,
                                    "add-circle-sharp.png",
                                    2.5,
                                    {"center_x": 0.5, "center_y": 0.965}
                                ), 0
                            )


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

    def repos_icon(self, *args):

        def resize(*args):
            pos_calc = ((self.button.width/2 - 35) if self.button.center[0] > 0 else (-self.button.width/2 + 35))
            self.icon.center[0] = self.button.center[0] + pos_calc
            self.load_icon.center[0] = self.button.center[0] + pos_calc

        Clock.schedule_once(resize, 0)

    def loading(self, boolean_value, *args):
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


# Similar to 'MainButton', but with a right-aligned icon button for a secondary action
class AddonButton(HoverButton):

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
        self.original_font = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["regular"]}.ttf')


        # Title of Addon
        self.title = Label()
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
        self.title.__translate__ = False
        self.title.text = f"{self.properties.name}  [color=#434368]-[/color]  {self.properties.author if self.properties.author else 'Unknown'}"
        self.add_widget(self.title)


        # Description of Addon
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
        if installed: self.toggle_installed(installed)

        # If click_function
        if click_function: self.bind(on_press=click_function)

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
            self.subtitle.text = "Loading add-on info..."
            self.subtitle.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
        else:
            self.subtitle.text = self.original_subtitle
            self.subtitle.font_name = self.original_font


# Right-side button for BaseInput-derived TextInputs
class InputButton(FloatLayout):
    def __init__(self, name, position, file=(), input_name=None, title=None, ext_list=[], offset=0, **kwargs):
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
        if file: self.button.on_release = functools.partial(file_popup, file[0], file[1], ext_list, input_name, title=title)
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
