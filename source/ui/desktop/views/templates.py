from source.ui.desktop.widgets.switches import *
from source.ui.desktop.widgets.banners import *
from source.ui.desktop.widgets.buttons import *
from source.ui.desktop.widgets.sliders import *
from source.ui.desktop.widgets.inputs import *
from source.ui.desktop.widgets.popups import *
from source.ui.desktop.widgets.menus import *
from source.ui.desktop.widgets.pages import *
from source.ui.desktop.widgets.base import *

from source.ui.desktop.utility import *
from source.ui.desktop import utility



# =============================================== Screen Templates =====================================================
# <editor-fold desc="Screen Templates">

class MenuBackground(Screen):

    reload_page = True

    def on_pre_leave(self, *args):
        super().on_pre_leave()
        if not utility.back_clicked and not self._ignore_tree:
            utility.screen_manager.screen_tree.append(self.__class__.__name__)

        # Close keyboard listener on current screen
        if self._keyboard: self._keyboard_closed()

    # Reset page on screen load
    def on_pre_enter(self, *args):

        # Ignore loading anything if server is remote and unavailable
        screen_name = self.__class__.__name__
        if screen_name.startswith('Server') and screen_name not in ['ServerManagerScreen', 'ServerImportScreen']:
            if check_telepath_disconnect(): return True


        if self.reload_page and utility.ui_loaded:
            self.reload_menu()

            # Remove popup
            if self.popup_widget:
                self.popup_widget.self_destruct(self, False)
                self.popup_widget = None
                self.canvas.after.clear()

            # Add global banner object if one exists
            def revive_banner(*args):
                if utility.global_banner:
                    if utility.global_banner.parent:
                        utility.global_banner.parent.remove_widget(utility.global_banner)
                self.banner_widget = utility.global_banner if utility.global_banner else BannerLayout()
                self.add_widget(self.banner_widget)

            Clock.schedule_once(revive_banner, 0.12)

        # Keyboard yumminess
        self._input_focused = False
        self._keyboard = Window.request_keyboard(None, self, 'text')
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        self._keyboard.bind(on_key_up=self._on_keyboard_up)


    def on_leave(self, *args):
        # Remove popup
        if self.popup_widget:
            self.popup_widget.self_destruct(self, False)
            self.popup_widget = None
            self.canvas.after.clear()

            with self.canvas.after:
                self.canvas.clear()

        if self.resize_bind:
            Window.unbind(on_resize=self.resize_bind)

        # Remove context menu
        if self.context_menu:
            self.context_menu.hide(animate=False)
            self.context_menu = None

        # Causes bug with resizing
        # for widget in self.walk():
        #     self.remove_widget(widget)
        #     del widget

        with self.canvas.after:
            self.canvas.clear()

        with self.canvas.before:
            self.canvas.clear()

        self.canvas.clear()
        self.clear_widgets()



    def reload_menu(self, *args):
        self.clear_widgets()
        self.generate_menu()


    def generate_menu(self, *args):
        pass

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

        save_window_pos()

    # Ignore touch events when popup is present
    def on_touch_down(self, touch):
        if self.popup_widget:
            if self.popup_widget.window.collide_point(*touch.pos): return super().on_touch_down(touch)
            else: return
        else: return super().on_touch_down(touch)

    # Show popup; popup_type can be "info", "warning", "query"
    def show_popup(self, popup_type, title, content, callback=None, *args):

        # Ignore if a pop-up is already on-screen
        if self.popup_widget:
            return


        # If not, process pop-up
        popup_types = (
            "info", "warning", "query", "warning_query", "controls", "addon",
            "script", "file", "error_log"
        )
        telepath_types = ("pair_request", "pair_result")
        if self.context_menu:
            self.context_menu.hide()

        if ((popup_type == "update") or (title and content and (popup_type in popup_types or popup_type in telepath_types))) and (self == utility.screen_manager.current_screen):

            # self.show_popup("info", "Title", "This is an info popup!", functools.partial(callback_func))
            # self.show_popup("warning", "Title", "This is a warning popup!", functools.partial(callback_func))
            # self.show_popup("query", "Title", "Yes or no?", (functools.partial(callback_func_no), functools.partial(callback_func_yes)))
            # self.show_popup("warning_query", "Title", "Yes or no?", (functools.partial(callback_func_no), functools.partial(callback_func_yes)))
            # self.show_popup("controls", "Title", "Press X to do Y", functools.partial(callback_func))
            # self.show_popup("addon", "Title", "Description", (functools.partial(callback_func_web), functools.partial(callback_func_install)), addon_object)
            # self.show_popup("script", "Title", "Description", (functools.partial(callback_func_web), functools.partial(callback_func_install)), script_object)
            # self.show_popup("update", (None, functools.partial(callback_func_install)))
            # self.show_popup("file", "Title", file_path)


            # Log for crash info
            try:
                interaction = f"PopupWidget ({popup_type}: {title})"
                constants.last_widget = interaction + f" @ {constants.format_now()}"
                send_log('navigation', f"interaction: '{interaction}'")
            except: pass


            with self.canvas.after:
                if popup_type == "info":
                    self.popup_widget = PopupInfo()
                elif popup_type == "warning":
                    self.popup_widget = PopupWarning()
                elif popup_type == "query":
                    self.popup_widget = PopupQuery()
                elif popup_type == "warning_query":
                    self.popup_widget = PopupWarningQuery()
                elif popup_type == "controls":
                    self.popup_widget = PopupControls()
                elif popup_type == "addon":
                    self.popup_widget = PopupAddon(addon_object=args[0])
                    try: self.popup_widget.window_content
                    except AttributeError:
                        title = args[0].args[0].name[0:30]
                        content = "There is no data available for this add-on"
                        callback = None
                        self.popup_widget = PopupWarning()
                elif popup_type == "script":
                    self.popup_widget = PopupScript(script_object=args[0])
                    try: self.popup_widget.window_content
                    except AttributeError:
                        title = args[0].args[0].name[0:30]
                        content = "There is no data available for this script"
                        callback = None
                        self.popup_widget = PopupWarning()
                elif popup_type == "update":
                    self.popup_widget = PopupUpdate()
                    title = ""
                    content = ""
                elif popup_type == "file":
                    self.popup_widget = PopupFile()
                    Clock.schedule_once(functools.partial(self.popup_widget.set_text, content), 0)
                elif popup_type == "error_log":
                    self.popup_widget = PopupErrorLog()

                # Telepath pop-ups
                elif popup_type == "pair_request":
                    self.popup_widget = PopupTelepathPair(prompt=True)
                elif popup_type == "pair_result":
                    self.popup_widget = PopupTelepathPair()

            self.popup_widget.generate_blur_background()

            if popup_type not in telepath_types:
                if title.strip():   self.popup_widget.window_title.text = title
                if content.strip(): self.popup_widget.window_content.text = content

            self.popup_widget.callback = callback

            def show(*argies):
                self.add_widget(self.popup_widget)
                self.popup_widget.resize()
                self.popup_widget.animate(True)

            if self.popup_widget.window_sound:
                # Fix popping sound when sounds are played
                try: self.popup_widget.window_sound.play()
                except: pass
            Clock.schedule_once(show, 0.3)

    # Show global search bar
    def show_search(self):

        if "ProgressScreen" in self.__class__.__name__:
            return

        if "BlurredLoadingScreen" in self.__class__.__name__:
            return

        if self.context_menu:
            self.context_menu.hide()

        # Log for crash info
        try:
            interaction = f"PopupWidget (GlobalSearch)"
            constants.last_widget = interaction + f" @ {constants.format_now()}"
            send_log('navigation', f"interaction: '{interaction}'")
        except: pass

        with self.canvas.after:
            self.popup_widget = PopupSearch()

        self.popup_widget.generate_blur_background()

        def show(*argies):
            self.add_widget(self.popup_widget)
            self.popup_widget.resize()
            self.popup_widget.animate(True)

        Clock.schedule_once(show, 0)

    # Show a context menu when clicking on certain elements
    def show_context_menu(self, widget, options_list):
        if not self.popup_widget:

            def show(*a):
                if not self.context_menu:
                    self.context_menu = ContextMenu()
                    self.add_widget(self.context_menu)
                self.context_menu.show(widget, options_list)

            if self.context_menu:
                if self.context_menu.widget != widget:
                    self.context_menu.hide()
                    widget.on_enter()
                    Clock.schedule_once(show, 0.15)
                    return None

            show()




    # Show banner; pass in color, text, icon name, and duration
    @staticmethod
    def show_banner(color, text, icon, duration=5, pos_hint={"center_x": 0.5, "center_y": 0.895}, play_sound=None, *args):

        # Base banner layout
        banner_layout = BannerLayout()
        banner_size = (800, 47)

        # Banner
        banner_object = BannerObject(
            pos_hint = pos_hint,
            size = banner_size,
            color = color,
            text = text,
            icon = icon,
            animate = True
        )

        # Banner drop shadow
        banner_shadow = Image()
        banner_shadow.source = os.path.join(paths.ui_assets, 'banner_shadow.png')
        banner_shadow.keep_ratio = False
        banner_shadow.allow_stretch = True
        banner_shadow.size_hint_max = (banner_size[0] + 150, banner_size[1] * 2)
        banner_shadow.pos_hint = pos_hint
        banner_shadow.opacity = 0
        Animation(opacity=1, duration=0.5).start(banner_shadow)

        # Banner progress bar
        banner_progress_bar = Image()
        banner_progress_bar.source = os.path.join(paths.ui_assets, 'banner_progress_bar.png')
        banner_progress_bar.keep_ratio = False
        banner_progress_bar.allow_stretch = True
        banner_progress_bar.size_hint_max = (banner_size[0] - (banner_object.left_side.width * 2), banner_size[1])
        banner_progress_bar.color = (0, 0, 0, 1)
        banner_progress_bar.pos_hint = pos_hint
        banner_progress_bar.opacity = 0
        Animation(opacity=0.25, duration=0.5).start(banner_progress_bar)
        Animation(size_hint_max=(0, banner_size[1]), duration=duration).start(banner_progress_bar)

        banner_layout.add_widget(banner_shadow)
        banner_layout.add_widget(banner_object)
        banner_layout.add_widget(banner_progress_bar)

        # Remove banner if it already exists
        if utility.global_banner:
            if utility.global_banner.parent:
                utility.hide_widget(utility.global_banner)
                utility.global_banner.parent.remove_widget(utility.global_banner)

        utility.screen_manager.current_screen.banner_widget = banner_layout
        utility.global_banner = banner_layout

        utility.screen_manager.current_screen.add_widget(utility.screen_manager.current_screen.banner_widget)

        # Deletes banner object after duration
        def hide_banner(widget, *args):
            try:
                if utility.global_banner.id == widget.id:

                    if utility.global_banner:
                        if utility.global_banner.parent:
                            utility.global_banner.parent.remove_widget(utility.global_banner)

                    utility.global_banner = None
                    for screen in utility.screen_manager.children:
                        screen.banner_widget = None

            # Ignore crash if screen was rapidly changed
            except AttributeError:
                pass

        def hide_widgets(shadow, progress_bar, *args):
            Animation(opacity=0, duration=0.5).start(shadow)
            Animation(opacity=0, duration=0.1).start(progress_bar)


        Clock.schedule_once(functools.partial(banner_object.show_animation, False), duration)
        Clock.schedule_once(functools.partial(hide_widgets, banner_shadow, banner_progress_bar), duration)
        Clock.schedule_once(functools.partial(hide_banner, banner_layout), duration + 0.32)

        if play_sound:
            try: audio.player.play(play_sound)
            except: pass


    # Keyboard listeners
    def _keyboard_closed(self):
        # print('Keyboard has been closed')
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _reset_shift_counter(self, *args):
        self._shift_press_count = 0
        self._shift_timer = None

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
                            Clock.schedule_once(functools.partial(self.popup_widget.window_input.do_cursor_movement, 'cursor_right', True), 0)

                    new_str = self.popup_widget.window_input.keyboard.keycode_to_string(keycode[0])
                    if 'shift' in modifiers:       new_str = new_str.upper()
                    if len(new_str) == 1:          insert_text(new_str)
                    elif keycode[1] == 'spacebar': insert_text(' ')
                    self.popup_widget.resize_window()

                else: self.popup_widget.resize_window()
                return True

            if keycode[1] in ['escape', 'n']:
                try: self.popup_widget.click_event(self.popup_widget, 'no')
                except AttributeError:
                    self.popup_widget.click_event(self.popup_widget, 'ok')

            elif keycode[1] in ['enter', 'return', 'y']:
                try: self.popup_widget.click_event(self.popup_widget, 'yes')
                except AttributeError:
                    self.popup_widget.click_event(self.popup_widget, 'ok')
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
                else: self._shift_timer = Clock.schedule_once(self._reset_shift_counter, 0.25)  # Adjust time as needed
            return True


        # Quit on macOS
        elif constants.os_name == 'macos' and (keycode[1] == 'q' and control in modifiers):
            utility.app.attempt_to_close()


        # Ignore ESC commands while input focused
        if not self._input_focused and self.name == utility.screen_manager.current_screen.name:

            # Keycode is composed of an integer + a string
            # If we hit escape, release the keyboard
            # On ESC, click on back button if it exists
            if keycode[1] == 'escape' and 'escape' not in self._ignore_keys:

                if self.context_menu:
                    self.context_menu.hide()

                else:
                    for button in self.walk():
                        try:
                            if button.id == "exit_button":
                                button.force_click()
                                break
                        except AttributeError:
                            continue
                keyboard.release()


            # Click next button if it's not disabled
            if keycode[1] == 'enter' and 'enter' not in self._ignore_keys:
                for button in self.walk():
                    try:
                        if button.id == "next_button" and button.disabled is False:
                            button.force_click()
                            break
                    except AttributeError:
                        continue
                keyboard.release()


        # # On TAB/Shift+TAB, cycle through elements
        # if keycode[1] == 'tab' and 'tab' not in self._ignore_keys:
        #     pass
        #     # for widget in self.walk():
        #     #     try:
        #     #         if "button" in widget.id or "input" in widget.id:
        #     #             print(widget)
        #     #             break
        #     #     except AttributeError:
        #     #         continue


        # Crash test
        # if keycode[1] == 'z' and control in modifiers:
        #     crash = float("crash")


        # Return True to accept the key. Otherwise, it will be used by the system.
        return True

    def _on_keyboard_up(self, window, keycode):
        if keycode[1] == 'shift':
            self._shift_held = False  # Mark Shift as released

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Screen won't get added to screen tree on leave
        self._ignore_tree = False

        self.banner_widget = None
        self.popup_widget = None
        self.page_switcher = None
        self.context_menu = None

        self._input_focused = False
        self._keyboard = None
        self._shift_press_count = 0
        self._shift_timer = None
        self._shift_held = False
        self.background_color = constants.background_color

        # Add keys to override in child windows
        self._ignore_keys = []

        with self.canvas.before:
            self.color = Color(*constants.background_color, mode='rgba')
            self.rect = Rectangle(pos=self.pos, size=self.size)

        with self.canvas.after:
            self.canvas.clear()

        self.bind(pos=self.update_rect)
        self.bind(size=self.update_rect)

        self.resize_bind = None
        self.popup_bind = None


# Template for loading/busy screens
class ProgressWidget(RelativeLayout):

    # Value: 0-100
    def update_progress(self, value, *args):

        # Throttle gate to prevent animation glitches, caches trailing value
        if not getattr(self, "_bypass_throttle", False):
            now = time.time()
            elapsed = now - getattr(self, "_last_update_ts", 0)
            if elapsed < getattr(self, "_throttle_interval", 0):
                self._pending_value = value
                if self._throttle_ev is None:
                    delay = max(0, self._throttle_interval - elapsed)
                    self._throttle_ev = Clock.schedule_once(self._flush_throttle, delay)
                return

            self._last_update_ts = now


        value = 0 if value < 0 else 100 if value > 100 else int(round(value))

        if self.value == value:
            return

        self.value = value

        anim_duration = 0.7
        adjusted_value = (self.value*0.01) if self.value != 99 else 0.98

        new_width = (self.size_hint_max[0] * (1 - adjusted_value))
        new_x = (self.size_hint_max[0] - new_width)
        Animation.stop_all(self.cover)
        Animation.stop_all(self.percentage)

        # Funny text animation
        diff = self.value - int(self.percentage.text.replace("%", ""))
        def update_text(*args):
            yummy = int(round(anim_duration*10))
            if diff > 5:
                new_value = int(self.percentage.text.replace("%", "")) + round((diff // yummy))
                for num in range(1, yummy):
                    if new_value > self.value:
                        break
                    new_value = new_value + round((diff // yummy))
                    self.percentage.text = str(new_value) + "%"
                    time.sleep(0.1)
            self.percentage.text = str(self.value) + "%"

        original_text = self.percentage.text
        self.percentage.text = str(self.value) + "%"
        if diff > 5: Clock.schedule_once(self.percentage.texture_update, -1)
        self.percentage.size_hint_max = self.percentage.texture_size
        self.percentage.text = original_text

        # Actually animate schennanies LOL fuck kivy holy shit
        def anim(*args):

            thread = dTimer(0, update_text)
            thread.start()

            text_x = new_x if self.value == 0 else (new_x - self.percentage.width / 2)
            if text_x < self.rail.x: text_x = self.rail.x
            overshoot = (new_x + (self.percentage.width / 1.5)) - self.size_hint_max[0]
            if overshoot > 0: text_x -= overshoot

            # print(text_x, self.percentage.text, self.percentage.texture_size)

            Animation(x=text_x, duration=anim_duration, transition='out_sine').start(self.percentage)
            Animation(size_hint_max_x=new_width, x=new_x, duration=anim_duration, transition='out_sine').start(self.cover)

            if value == 100:
                def make_green(*args):
                    green = (0.3, 1, 0.6, 1)
                    new_dur = 0.2
                    for widget in [self.bar, self.rail, self.cover]:
                        Animation(opacity=0, duration=new_dur).start(widget)
                    Animation(opacity=1, duration=new_dur, color=green).start(self.static_bar)
                    Animation(color=green, duration=new_dur).start(self.percentage)
                Clock.schedule_once(make_green, 0 if diff < 3 else anim_duration-0.1)

        Clock.schedule_once(anim, 0)

    def _flush_throttle(self, *args):
        self._throttle_ev = None
        if self._pending_value is not None:
            pv = self._pending_value
            self._pending_value = None
            self._bypass_throttle = True
            try: self.update_progress(pv)
            finally: self._bypass_throttle = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._updates_per_sec = 10
        self._throttle_interval = 1 / self._updates_per_sec
        self._last_update_ts = 0
        self._pending_value = None
        self._throttle_ev = None
        self._bypass_throttle = False

        self.size_hint_max = (540, 28)
        self.value = 0

        # Frame of progress bar
        self.rail = Image()
        self.rail.allow_stretch = True
        self.rail.keep_ratio = False
        self.rail.source = os.path.join(paths.ui_assets, 'progress_bar_empty.png')

        # Cover of progress bar (to simulate horizontal movement)
        self.cover = Image()
        self.cover.allow_stretch = True
        self.cover.keep_ratio = False
        self.cover.size_hint_max_x = self.size_hint_max_x
        self.cover.color = constants.background_color
        self.cover.pos_hint = {'center_y': 0.5}

        # Fake shading to change the depth
        self.shadow = Image()
        self.shadow.allow_stretch = True
        self.shadow.keep_ratio = False
        self.shadow.size_hint_max_x = self.size_hint_max_x
        self.shadow.color = constants.background_color
        self.shadow.opacity = 0.1
        self.shadow.size_hint_max_y = self.size_hint_max_y / 2
        self.shadow.y = self.y

        # Progress bar animation
        self.bar = Image()
        self.bar.allow_stretch = True
        self.bar.keep_ratio = False
        self.bar.source = os.path.join(paths.ui_assets, 'animations', 'bar_full.gif')
        self.bar.anim_delay = 0.025

        # Progress bar Static
        self.static_bar = Image()
        self.static_bar.allow_stretch = True
        self.static_bar.keep_ratio = False
        self.static_bar.source = os.path.join(paths.ui_assets, 'progress_bar_full.png')
        self.static_bar.color = (0.58, 0.6, 1, 1)
        self.static_bar.opacity = 0

        # Percentage text
        self.percentage = Label()
        self.percentage.__translate__ = False
        self.percentage.text = "0%"
        self.percentage.font_name = os.path.join(paths.ui_assets, 'fonts', constants.fonts['medium'])
        self.percentage.font_size = sp(19)
        self.percentage.color = (0.58, 0.6, 1, 1)
        self.percentage.opacity = 1
        def align_label(*args):
            self.percentage.texture_update()
            self.percentage.size_hint_max = self.percentage.texture_size
            self.percentage.y = self.rail.y + 31
            self.percentage.texture_update()
        Clock.schedule_once(align_label, -1)


        self.add_widget(self.bar)
        self.add_widget(self.static_bar)
        self.add_widget(self.cover)
        self.add_widget(self.rail)
        self.add_widget(self.percentage)
        self.add_widget(self.shadow)

        self.update_progress(self.value)

class ProgressScreen(MenuBackground):

    # Returns current progress bar value
    def get_progress(self):
        return self.progress_bar.value

    # Only replace this function when making a child screen
    # Set fail message in child functions to trigger an error
    def contents(self):
        def sleep(delay: float or int):
            time.sleep(delay)
            return True

        self.page_contents = {

            # Page name
            'title': "Progress Screen",

            # Header text
            'header': "Sit back and relax, it's automation time",

            # Tuple of tuples for steps (label, function, percent)
            # Percent of all functions must total 100
            # Functions must return True, or default error will be executed
            'default_error': 'There was an issue, please try again later',

            'function_list': (
                ('Step 1', functools.partial(sleep, 3), 30),
                ('Step 2', functools.partial(sleep, 3), 30),
                ('Step 3', functools.partial(sleep, 0.1), 30),
                ('Step 4', functools.partial(sleep, 0.1), 10)
            ),

            # Function to run before steps (like checking for an internet connection)
            'before_function': functools.partial(sleep, 0),

            # Function to run after everything is complete (like cleaning up the screen tree) will only run if no error
            'after_function': functools.partial(sleep, 0),

            # Screen to go to after complete
            'next_screen': 'MainMenuScreen'
        }


    # Check if there's a telepath client or server, and if it's using a blocking action
    def _check_telepath(self):
        server_obj = constants.server_manager.current_server

        try:
            if constants.telepath_busy():
                self.execute_error('A critical operation is currently running through a $Telepath$ session.\n\nPlease try again later', reset_close=False)
                return True

            elif self._telepath_override == '$local':
                self.telepath = None
            elif self._telepath_override:
                self.telepath = self._telepath_override

            elif server_obj and server_obj._telepath_data:
                self.telepath = server_obj._telepath_data

            elif '_telepath_data' in foundry.new_server_info and foundry.new_server_info['_telepath_data']:
                self.telepath = constants.deepcopy(foundry.new_server_info['_telepath_data'])

            if self.telepath:
                self.telepath['server-name'] = server_obj.name
                host = self.telepath['nickname'] if self.telepath['nickname'] else self.telepath['host']
                if not server_obj.progress_available():
                    self.execute_error(f"A critical operation is currently running locally on '${host}$'.\n\nPlease try again later", reset_close=False)
                    return True

        except AttributeError:
            return False

        return False

    def allow_close(self, allow: bool):
        if self.telepath:
            banner = f'$Telepath$ action {"finished" if allow else "started"}: {self.page_contents["title"]}'
            constants.api_manager.request(
                endpoint = '/main/allow_close',
                host = self.telepath['host'],
                port = self.telepath['port'],
                args = {'allow': allow, 'banner': banner}
            )
        else: constants.allow_close(allow)

    def open_server(self, *args, **kwargs):
        if self.telepath: open_remote_server(self.telepath, *args, **kwargs)
        else:             open_server(*args, **kwargs)


    def execute_steps(self):

        # Before doing anything, check telepath data to prevent issues with concurrency
        if self._check_telepath():
            return

        icons = os.path.join(paths.ui_assets, 'fonts', constants.fonts['icons'])

        self.allow_close(False)
        send_log(self.__class__.__name__, f"initializing '{utility.screen_manager.current_screen.name}': {self.page_contents['title'].replace('$','')}...", 'info')

        # Execute before function
        if self.page_contents['before_function']:
            self.steps.label_2.text = "Initializing, please wait..."
            self.page_contents['before_function']()
            if self.error:
                return

        # Go over every step in function_list
        for x, step in enumerate(self.page_contents['function_list']):

            # Close thread if error occurred
            if self.error:
                return

            step_info = f"'{utility.screen_manager.current_screen.name}' executing step {x + 1} / {len(self.page_contents['function_list'])} - '{step[0]}'"
            send_log(self.__class__.__name__, step_info, 'info')

            if x != 0:
                if "[font=" not in self.steps.label_2.text:
                    self.steps.label_2.text = self.steps.label_2.text.split('(')[0].strip() + f"   [font={icons}]å[/font]"
                time.sleep(0.4)
            self.update_steps(step[0], x)

            # Execute function and check for completion
            self.last_progress = self.progress_bar.value
            exception = None
            crash_log = None
            file_path = None
            try:
                test = step[1]()

            # On error, log it and prompt user to open it
            except Exception as e:
                exception = e
                error_info = f"'{utility.screen_manager.current_screen.name}' failed on step {x+1} / {len(self.page_contents['function_list'])} - '{step[0]}'"

                crash_log, file_path = logger.create_error_log(traceback.format_exc(), error_info=error_info)
                test = False

                send_log(self.__class__.__name__, f"{error_info}: {constants.format_traceback(e)}", 'error')

            time.sleep(0.2)

            # If it failed, execute default error
            if not test:
                self.execute_error(self.page_contents['default_error'], exception=exception, log_data=(crash_log, file_path) if crash_log else None)
                return

            completed = x + 1 == len(self.page_contents['function_list'])
            if completed: audio.player.play('interaction/click_*', after=0.42, jitter=(0, 0.15))
            else:         audio.player.play('interaction/step', after=0.42, jitter=0.1, pitch=0.7, volume=0.75)

            self.progress_bar.update_progress(self.progress_bar.value + step[2])

        # Execute after_function
        time.sleep(0.5)
        def test(*a):
            if "[font=" not in self.steps.label_2.text:
                self.steps.label_2.text = self.steps.label_2.text.split('(')[0].strip() + f"   [font={icons}]å[/font]"
        Clock.schedule_once(test, 0)
        # time.sleep(0.19)
        Animation(color=(0.3, 1, 0.6, 1), duration=0.2, transition='out_sine').start(self.steps.label_2)

        # Execute after function on if there was no error
        if self.page_contents['after_function'] and not self.error:
            self.page_contents['after_function']()

        # Switch to next_page after it's done
        self.allow_close(True)

        # Migrate to the next screen
        if not self.error:
            send_log(self.__class__.__name__, f"successfully executed '{utility.screen_manager.current_screen.name}': {self.page_contents['title'].replace('$','')}", 'info')

            # Play yummy sound (if not restarting for an update)
            if not constants.restart_flag: audio.player.play('popup/success', after=1)

            if self.page_contents['next_screen']:
                def next_screen(*args):
                    utility.back_clicked = True
                    utility.screen_manager.current = self.page_contents['next_screen']
                    utility.back_clicked = False
                Clock.schedule_once(next_screen, 0.8)


    def execute_error(self, msg, reset_close=True, exception=None, log_data=None, *args):
        if reset_close: self.allow_close(True)
        self.error = True

        if exception: msg = f'{msg}\n\n{exception}'

        def close(*args):
            Clock.schedule_once(utility.screen_manager.previous_screen, 0.25)
            self.error = False
            self.timer = None

        def function(*args):
            self.timer.cancel()

            if self._error_callback:
                self._error_callback()

            if log_data:
                log_path = log_data[1]
                send_log(self.__class__.__name__, f"'{utility.screen_manager.current_screen.name}' exited with exception code:  {log_data[0]}\nFull error log available in:  '{log_path}'", 'error')
                title = f'Error: {log_data[0]}'
                def open_log():
                    view_file(log_path, title)
                    close()
                self.show_popup('error_log', 'Error', msg, (close, open_log))

            # This eventually also needs to be type 'error_log' with the following functionality:
            #   - ability to view everything in the log since the first event when this page was loaded
            else:
                send_log(self.__class__.__name__, f"'{utility.screen_manager.current_screen.name}' exited with error:\n{msg}", 'error')
                self.show_popup('warning', 'Error', msg, (close))

        Clock.schedule_once(function, 0)


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'

        self._ignore_tree = True
        self._error_callback = None
        self._telepath_override = None
        self.telepath = None

        self.title = None
        self.footer = None
        self.progress_bar = None
        self.steps = None
        self.timer = None
        self.error = False
        self.start = False
        self.last_progress = 0

        self.page_contents = None


    def update_steps(self, current, num):
        icons = os.path.join(paths.ui_assets, 'fonts', constants.fonts['icons'])
        yummy_label = f"   ({num+1}/{len(self.page_contents['function_list'])})"
        end_label = f"{len(self.page_contents['function_list'])})"

        Animation.stop_all(self.steps.label_1)
        Animation.stop_all(self.steps.label_2)
        Animation.stop_all(self.steps.label_3)
        Animation.stop_all(self.steps.label_4)
        self.steps.label_1.y = self.steps.label_1.original_y
        self.steps.label_2.y = self.steps.label_2.original_y
        self.steps.label_3.y = self.steps.label_3.original_y
        self.steps.label_4.y = self.steps.label_4.original_y

        if len(self.page_contents['function_list']) == 1:
            self.steps.label_2.text = current
        else:
            anim_duration = 0.5 if self.start else 0

            if "[font=" not in self.steps.label_2.text and self.steps.label_2.text:
                self.steps.label_2.text = translate(self.steps.label_2.text.split('(')[0].strip()) + f"   [font={icons}]å[/font]"
            Animation(opacity=0.3, duration=0.2 if self.start else 0, transition='out_sine').start(self.steps.label_1)
            Animation(opacity=0.3, duration=0.2 if self.start else 0, transition='out_sine').start(self.steps.label_2)
            Animation(opacity=0.3, duration=0.2 if self.start else 0, transition='out_sine').start(self.steps.label_3)
            Animation(opacity=0.3, duration=0.2 if self.start else 0, transition='out_sine').start(self.steps.label_4)

            if num != 0:
                if not self.steps.label_3.text.endswith(end_label) and self.steps.label_3.text:
                    self.steps.label_3.text += yummy_label
                Animation(y=self.steps.label_1.y + (self.steps.size_hint_max[1] / 2), duration=anim_duration, transition='out_sine').start(self.steps.label_1)
                Animation(y=self.steps.label_2.y + (self.steps.size_hint_max[1] / 2), duration=anim_duration, transition='out_sine').start(self.steps.label_2)
                Animation(y=self.steps.label_3.y + (self.steps.size_hint_max[1] / 2), opacity=1, duration=anim_duration, transition='out_sine').start(self.steps.label_3)
                Animation(y=self.steps.label_4.y + (self.steps.size_hint_max[1] / 2), duration=anim_duration, transition='out_sine').start(self.steps.label_4)
            else:
                Animation.stop_all(self.steps.label_2)
                self.steps.label_2.opacity = 1

            def delayed_func(*args):
                if num != 0:
                    # Label 1
                    try:
                        self.steps.label_1.text = self.page_contents['function_list'][num-1][0]
                        if "[font=" not in self.steps.label_1.text and self.steps.label_1.text:
                            self.steps.label_1.text += f"   [font={icons}]å[/font]"
                        self.steps.label_1.opacity = 0.3
                    except IndexError: pass
                    self.steps.label_1.y = self.steps.label_1.original_y


                # Label 2
                try:
                    self.steps.label_2.text = translate(current) + yummy_label
                    self.steps.label_2.opacity = 1
                except IndexError: pass
                self.steps.label_2.y = self.steps.label_2.original_y


                # Label 3
                try:
                    self.steps.label_3.text = self.page_contents['function_list'][num+1][0]
                    self.steps.label_3.opacity = 0.3
                except IndexError: self.steps.label_3.text = ""
                self.steps.label_3.y = self.steps.label_3.original_y


                # Label 4
                try:
                    self.steps.label_4.text = self.page_contents['function_list'][num+2][0]
                    self.steps.label_4.opacity = 0.3
                except IndexError: self.steps.label_4.text = ""
                self.steps.label_4.y = self.steps.label_4.original_y

            Clock.schedule_once(delayed_func, anim_duration+0.2 if self.start else 0)
            self.start = True


    def generate_menu(self, **kwargs):
        # Generate buttons on page load
        self.contents()
        self.start = False
        self.error = False
        self.telepath = None
        self.last_progress = 0

        float_layout = FloatLayout()
        float_layout.id = 'content'

        float_layout.add_widget(HeaderText(self.page_contents['header'], '', (0, 0.8)))

        self.progress_bar = ProgressWidget(pos_hint={'center_x': 0.5, 'center_y': 0.6})

        self.title = generate_title(self.page_contents['title'])


        # Yummy animated steps text
        class StepLabel(Label):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.text = ""
                self.font_name = os.path.join(paths.ui_assets, 'fonts', constants.fonts['medium'])
                self.font_size = sp(25)
                self.markup = True
                self.color = (0.6, 0.6, 1, 1)
                self.opacity = 1
                self.original_y = 0
        self.steps = RelativeLayout()
        self.steps.size_hint_max = (150, 150)
        self.steps.pos_hint = {'center_x': 0.5, 'center_y': 0.25}
        self.steps.label_1 = StepLabel()
        self.steps.label_1.original_y = self.steps.label_1.y = self.steps.size_hint_max[1]
        self.steps.label_2 = StepLabel()
        self.steps.label_2.original_y = self.steps.label_2.y = self.steps.size_hint_max[1] / 2
        self.steps.label_3 = StepLabel()
        self.steps.label_3.original_y = self.steps.label_3.y = 0
        self.steps.label_4 = StepLabel()
        self.steps.label_4.original_y = self.steps.label_4.y = 0 - (self.steps.size_hint_max[1] / 2)
        self.steps.scroll_top = ScrollBackground(pos_hint={'center_x': 0.5}, pos=(0, self.steps.size_hint_max[1] * 1.7), size=(Window.width // 1.5, 60))
        self.steps.scroll_bottom = ScrollBackground(pos_hint={'center_x': 0.5}, pos=(0, (self.steps.size_hint_max[1] / 3.5)), size=(Window.width // 1.5, -60))
        self.steps.add_widget(self.steps.label_1)
        self.steps.add_widget(self.steps.label_2)
        self.steps.add_widget(self.steps.label_3)
        self.steps.add_widget(self.steps.label_4)
        self.steps.add_widget(self.steps.scroll_top)
        self.steps.add_widget(self.steps.scroll_bottom)


        # Change footer icon to loading pickaxe, remove home button
        # Also prevent window from being closed during operations
        self.footer = generate_footer(self.page_contents['title'] + '...', progress_screen=True)

        float_layout.add_widget(self.title)
        float_layout.add_widget(self.footer)
        float_layout.add_widget(self.steps)
        float_layout.add_widget(self.progress_bar)

        self.add_widget(float_layout)

        self.timer = dTimer(0, self.execute_steps)
        self.timer.start()

# Blurred loading screen for blocking operations
class BlurredLoadingScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'
        self._ignore_tree = True

        self.generating_background = False
        self.blur_background = None
        self.load_icon = None
        self.load_label = None

    def generate_blur_background(self, *args):
        image_path = os.path.join(paths.ui_assets, 'live', 'blur_background.png')
        constants.folder_check(os.path.join(paths.ui_assets, 'live'))

        if not self.generating_background:
            self.generating_background = True
            self.blur_background.opacity = 0

            utility.screen_manager.get_screen(utility.screen_manager.screen_tree[-1]).export_to_png(image_path)
            im = PILImage.open(image_path)
            im = ImageEnhance.Brightness(im)
            im = im.enhance(popup_blur_darkness)
            im1 = im.filter(GaussianBlur(popup_blur_amount))
            im1.save(image_path)
            self.blur_background.reload()

            self.blur_background.opacity = 1

    def on_pre_enter(self, *args):
        super().on_pre_enter()
        if utility.ui_loaded: constants.ignore_close = True

    def on_leave(self, *args):
        super().on_leave()
        if utility.ui_loaded: constants.ignore_close = False

    def resize_self(self, *args):
        self.load_label.x = (Window.width / 2) - 75
        self.load_icon.x = (Window.width / 2) - 160


    def generate_menu(self, **kwargs):
        # Generate buttons on page load

        float_layout = FloatLayout()
        float_layout.id = 'content'

        # Blurred background
        self.blur_background = Image()
        self.blur_background.opacity = 0
        self.blur_background.id = "blur_background"
        self.blur_background.source = os.path.join(paths.ui_assets, 'live', 'blur_background.png')
        self.blur_background.allow_stretch = True
        self.blur_background.keep_ratio = False
        self.generating_background = False
        float_layout.add_widget(self.blur_background)
        Clock.schedule_once(self.generate_blur_background, -1)


        # Loading icon to swap button
        self.load_icon = AsyncImage()
        self.load_icon.id = "load_icon"
        self.load_icon.source = os.path.join(paths.ui_assets, 'animations', 'loading_pickaxe.gif')
        self.load_icon.size_hint_max = (65, 65)
        self.load_icon.color = (0.8, 0.8, 1, 1)
        self.load_icon.pos_hint = {"center_y": 0.5}
        self.load_icon.allow_stretch = True
        self.load_icon.anim_delay = utility.anim_speed * 0.02
        float_layout.add_widget(self.load_icon)


        # Loading label
        self.load_label = AlignLabel()
        self.load_label.halign = 'left'
        self.load_label.valign = 'center'
        self.load_label.id = 'label'
        self.load_label.size_hint_max = (300, 50)
        self.load_label.pos_hint = {"center_y": 0.5}
        self.load_label.text = 'please wait...'
        self.load_label.font_size = sp(35)
        self.load_label.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["bold"]}.ttf')
        self.load_label.color = (0.8, 0.8, 1, 1)
        float_layout.add_widget(self.load_label)


        self.blur_background.size_hint_min = Window.size
        float_layout.bind(pos=self.resize_self, size=self.resize_self)

        self.add_widget(float_layout)


# </editor-fold> ///////////////////////////////////////////////////////////////////////////////////////////////////////
