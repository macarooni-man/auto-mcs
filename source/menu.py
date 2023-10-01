from concurrent.futures import ThreadPoolExecutor
from PIL.ImageFilter import GaussianBlur
from datetime import datetime as dt
from PIL import Image as PILImage
from ctypes import ArgumentError
from plyer import filechooser
from random import randrange
import simpleaudio as sa
from pathlib import Path
from glob import glob
import webbrowser
import functools
import threading
import inspect
import time
import sys
import os
import re
# import gc


# Local imports
import logviewer
import constants
import addons
import backup
import acl


if constants.os_name == "windows":
    import tkinter as tk
    from tkinter import filedialog

# Disable Kivy logging if debug is off and app is compiled
if constants.app_compiled and constants.debug is False:
    os.environ["KIVY_NO_CONSOLELOG"] = "1"
    os.environ['KIVY_HOME'] = os.path.join(constants.executable_folder, ".kivy")


os.environ["KCFG_KIVY_LOG_LEVEL"] = "info"
os.environ["KIVY_IMAGE"] = "pil,sdl2"

from kivy.config import Config
Config.set('graphics', 'maxfps', '240')
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Config.set('graphics', 'window_state', 'hidden')
Config.set('kivy', 'exit_on_escape', '0')

# Import kivy elements
from kivy.clock import Clock
from kivy.loader import Loader
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.utils import escape_markup
from kivy.animation import Animation
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.recycleview import RecycleView
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.togglebutton import ToggleButton
from kivy.graphics import Canvas, Color, Rectangle
from kivy.uix.relativelayout import RelativeLayout
from kivy.input.providers.mouse import MouseMotionEvent
from kivy.uix.recyclegridlayout import RecycleGridLayout
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition, FadeTransition


import kivy
kivy.require('2.0.0')
from kivy.app import App
from kivy.metrics import sp, dp
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.core.window import Window
from kivy.uix.dropdown import DropDown
from kivy.core.clipboard import Clipboard
from kivy.uix.image import Image, AsyncImage
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import BooleanProperty, ObjectProperty, NumericProperty, ListProperty


def icon_path(name):
    return os.path.join(constants.gui_assets, 'icons', name)


# Custom widget attributes
class HoverBehavior(object):
    """Hover behavior.
    :Events:
        `on_enter`
            Fired when mouse enter the bbox of the widget.
        `on_leave`
            Fired when the mouse exit the widget
    """

    hovered = BooleanProperty(False)
    border_point = ObjectProperty(None)
    '''Contains the last relevant point received by the Hoverable. This can
    be used in `on_enter` or `on_leave` in order to know where was dispatched the event.
    '''

    def __init__(self, *args, **kwargs):
        self.register_event_type('on_enter')
        self.register_event_type('on_leave')
        Window.bind(mouse_pos=self.on_mouse_pos)
        super(HoverBehavior, self).__init__(**kwargs)

    def on_mouse_pos(self, *args):
        if not self.get_root_window() or self.disabled:
            return # do proceed if I'm not displayed <=> If there's no parent
        pos = args[1]
        #Next line to_widget allow to compensate for relative layout
        inside = self.collide_point(*self.to_widget(*pos))

        if self.hovered == inside:
            #We have already done what was needed
            return
        self.border_point = pos
        self.hovered = inside
        if inside:
            self.dispatch('on_enter')
        else:
            self.dispatch('on_leave')

    def on_enter(self):
        pass

    def on_leave(self):
        pass

from kivy.lang import Builder
from kivy.factory import Factory
Factory.register('HoverBehavior', HoverBehavior)


def animate_button(self, image, color, **kwargs):
    image_animate = Animation(**kwargs, duration=0.05)

    def f(w):
        w.background_normal = image

    for child in self.parent.children:
        if child.id == 'text':
            Animation(color=color, duration=0.06).start(child)
        if child.id == 'icon':
            Animation(color=color, duration=0.06).start(child)

    a = Animation(duration=0.0)
    a.on_complete = functools.partial(f)

    image_animate += a

    image_animate.start(self)



def animate_icon(self, image, colors, hover_action, **kwargs):
    image_animate = Animation(**kwargs, duration=0.05)

    def f(w):
        w.background_normal = image

    for child in self.parent.children:
        if child.id == 'text':
            if hover_action:
                Animation(color=colors[1] if not self.selected else (0.6, 0.6, 1, 1), duration=0.12).start(child)
            else:
                Animation(color=(0, 0, 0, 0), duration=0.12).start(child)

        if child.id == 'icon':
            if hover_action:
                Animation(color=colors[0], duration=0.06).start(child)
            else:
                Animation(color=colors[1], duration=0.06).start(child)

    a = Animation(duration=0.0)
    a.on_complete = functools.partial(f)

    image_animate += a

    image_animate.start(self)



class HoverButton(Button, HoverBehavior):

    # self.id references image patterns
    # self.color_id references text/image color [hovered, un-hovered]

    color_id = [(0, 0, 0, 0), (0, 0, 0, 0)]
    alt_color = ''
    ignore_hover = False

    # Ignore touch events when popup is present
    def on_touch_down(self, touch):
        popup_widget = screen_manager.current_screen.popup_widget
        if popup_widget:
            return
        else:
            return super().on_touch_down(touch)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(on_touch_down=self.onPressed)
        self.button_pressed = None
        self.selected = False

    def onPressed(self, instance, touch):
        if touch.device == "wm_touch":
            touch.button = "left"

        self.button_pressed = touch.button

    def on_enter(self, *args):
        if not self.ignore_hover:

            if 'icon_button' in self.id:
                if self.selected:
                    animate_icon(self, image=os.path.join(constants.gui_assets, f'{self.id}_selected.png'), colors=[(0.05, 0.05, 0.1, 1), (0.05, 0.05, 0.1, 1)], hover_action=True)
                else:
                    animate_icon(self, image=os.path.join(constants.gui_assets, f'{self.id}_hover{self.alt_color}.png'), colors=self.color_id, hover_action=True)
            else:
                animate_button(self, image=os.path.join(constants.gui_assets, f'{self.id}_hover.png'), color=self.color_id[0])

    def on_leave(self, *args):
        if not self.ignore_hover:

            if 'icon_button' in self.id:
                if self.selected:
                    animate_icon(self, image=os.path.join(constants.gui_assets, f'{self.id}_selected.png'), colors=[(0.05, 0.05, 0.1, 1), (0.05, 0.05, 0.1, 1)], hover_action=False)
                else:
                    animate_icon(self, image=os.path.join(constants.gui_assets, f'{self.id}.png'), colors=self.color_id, hover_action=False)
            else:
                animate_button(self, image=os.path.join(constants.gui_assets, f'{self.id}.png'), color=self.color_id[1])

    def on_press(self):
        self.on_mouse_pos(self, Window.mouse_pos)

    def force_click(self, *args):
        touch = MouseMotionEvent("mouse", "mouse", Window.center)
        touch.button = 'left'
        touch.pos = Window.center
        self.dispatch('on_touch_down', touch)

        screen_manager.current_screen._keyboard.release()
        self.on_enter()
        self.trigger_action(0.1)


# -----------------------------------------------------  Labels  -------------------------------------------------------
class InputLabel(RelativeLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.id = 'InputLabel'
        self.text_size = sp(21)

        text = Label()
        text.id = 'text'
        text.text = "Invalid input"
        text.font_size = self.text_size
        self.text_x = text.x
        text.x += dp(15)
        text.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
        text.color = (1, 0.53, 0.58, 0)

        icon = Image()
        icon.id = 'icon'
        icon.source = os.path.join(constants.gui_assets, 'icons', 'alert-circle-outline.png')
        icon.color = (1, 0.53, 0.58, 0) # make alpha 0 eventually
        self.icon_x = icon.x
        icon.x -= dp((len(text.text) * (self.text_size - 8)) / 3) - dp(20)

        self.add_widget(text)
        self.add_widget(icon)


    def disable_text(self, disable):

        break_loop = False
        for child in self.parent.children:
            if break_loop:
                break

            elif child.__class__.__name__ == 'FloatLayout':
                for item in child.children:
                    try:
                        if item.id == 'next_button':
                            item.disable(disable)
                            break_loop = True
                            break

                    except AttributeError:
                        pass


    def update_text(self, text, warning=False):

        chosen_color = (0.3, 0.75, 1, 1) if warning else (1, 0.53, 0.58, 1)
        start_color = (0.3, 0.75, 1, 0) if warning else (1, 0.53, 0.58, 0)

        def change_color(item):
            item.color = start_color
            Animation(color=chosen_color, duration=0.12).start(item)

        for child in self.children:
            if child.id == 'text':
                child.text = text
                child.x = self.text_x + dp(15)

                if [round(x, 2) for x in child.color] != [round(x, 2) for x in chosen_color]:
                    change_color(child)
            else:
                child.source = os.path.join(constants.gui_assets, 'icons', 'alert-circle-outline.png')
                child.x = self.icon_x - dp((len(text) * (self.text_size - 8)) / 3) - dp(20)

                if [round(x, 2) for x in child.color] != [round(x, 2) for x in chosen_color]:
                    change_color(child)


    def clear_text(self):
        for child in self.children:
            new_color = (child.color[0], child.color[1], child.color[2], 0)
            Animation(color=new_color, duration=0.12).start(child)

            def reset_color(item, *args):
                item.color = (1, 0.53, 0.58, 0)

            Clock.schedule_once(functools.partial(reset_color, child), 0.2)


class BaseInput(TextInput):

    def _on_focus(self, instance, value, *largs):
        super()._on_focus(instance, value, *largs)

        # Update screen focus value on next frame
        def update_focus(*args):
            screen_manager.current_screen._input_focused = self.focus
        Clock.schedule_once(update_focus, 0)


    def grab_focus(self):
        def focus_later(*args):
            self.focus = True
        Clock.schedule_once(focus_later, 0)


    def fix_overscroll(self, *args):

        if self.cursor_pos[0] < (self.x):
            self.scroll_x = 0


    def update_rect(self, *args):
        self.rect.source = os.path.join(constants.gui_assets, f'text_input_cover{"" if self.focused else "_fade"}.png')

        self.title.text = self.title_text
        self.rect.width = (len(self.title.text) * 16) + 116 if self.title.text else 0
        if self.width > 500:
            self.rect.width += (self.width - 500)
        self.rect.pos = self.pos[0] + (self.size[0] / 2) - (self.rect.size[0] / 2) - 1, self.pos[1] + 45
        self.title.pos = self.pos[0] + (self.size[0] / 2) - (self.title.size[0] / 2), self.pos[1] + 4
        Animation(opacity=(0.85 if self.text and self.title_text else 0), color=self.foreground_color, duration=0.06).start(self.title)
        Animation(opacity=(1 if self.text and self.title_text else 0), duration=0.08).start(self.rect)

        # Auto position cursor at end if typing
        if self.cursor_index() == len(self.text) - 1:
            self.do_cursor_movement('cursor_end', True)
            Clock.schedule_once(functools.partial(self.do_cursor_movement, 'cursor_end', True), 0.01)


    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.title_text = "InputTitle"

        self.multiline = False
        self.size_hint_max = (500, 54)
        self.border = (-15, -15, -15, -15)
        self.background_normal = os.path.join(constants.gui_assets, f'text_input.png')
        self.background_active = os.path.join(constants.gui_assets, f'text_input_selected.png')

        self.halign = "center"
        self.hint_text_color = (0.6, 0.6, 1, 0.4)
        self.foreground_color = (0.6, 0.6, 1, 1)
        self.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
        self.font_size = sp(22)
        self.padding_y = (12, 12)
        self.cursor_color = (0.55, 0.55, 1, 1)
        self.cursor_width = dp(3)
        self.selection_color = (0.5, 0.5, 1, 0.4)

        with self.canvas.after:
            self.rect = Image(size=(100, 15), color=constants.background_color, opacity=0, allow_stretch=True, keep_ratio=False)
            self.title = AlignLabel(halign="center", text=self.title_text, color=self.foreground_color, opacity=0, font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["regular"]}.ttf'))
            self.bind(pos=self.update_rect)
            self.bind(size=self.update_rect)
            self.bind(text=self.update_rect)
            self.bind(foreground_color=self.update_rect)
            self.bind(focused=self.update_rect)

        self.bind(cursor_pos=self.fix_overscroll)


    # Ignore popup text
    def insert_text(self, substring, from_undo=False):
        if screen_manager.current_screen.popup_widget:
            return None

        super().insert_text(substring, from_undo)


    def valid_text(self, boolean_value, text):
        pass

    #               if error       visible text
    def valid(self, boolean_value, text=True):

        if boolean_value:

            # Hide text
            self.valid_text(boolean_value, text)

            self.background_normal = os.path.join(constants.gui_assets, f'text_input.png')
            self.background_active = os.path.join(constants.gui_assets, f'text_input_selected.png')
            self.hint_text_color = (0.6, 0.6, 1, 0.4)
            self.foreground_color = (0.6, 0.6, 1, 1)
            self.cursor_color = (0.55, 0.55, 1, 1)
            self.selection_color = (0.5, 0.5, 1, 0.4)

        else:

            # Show error
            self.valid_text(boolean_value, text)

            self.background_normal = os.path.join(constants.gui_assets, f'text_input_invalid.png')
            self.background_active = os.path.join(constants.gui_assets, f'text_input_invalid_selected.png')
            self.hint_text_color = (1, 0.6, 0.6, 0.4)
            self.foreground_color = (1, 0.56, 0.6, 1)
            self.cursor_color = (1, 0.52, 0.55, 1)
            self.selection_color = (1, 0.5, 0.5, 0.4)

    # Ignore touch events when popup is present
    def on_touch_down(self, touch):
        popup_widget = screen_manager.current_screen.popup_widget
        if popup_widget:
            return
        else:
            return super().on_touch_down(touch)

    # Special keypress behaviors
    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        super().keyboard_on_key_down(window, keycode, text, modifiers)

        if keycode[1] == "backspace" and "ctrl" in modifiers:
            if " " not in self.text:
                self.text = ""
            else:
                self.text = self.text.rsplit(" ", 1)[0]



class SearchButton(HoverButton):

    # Execute search on click
    def on_touch_down(self, touch):
        if self.collide_point(touch.x, touch.y):
            for child in self.parent.children:
                if child.id == "search_input":
                    child.focus = False
                    if child.text and self.parent.previous_search != child.text:
                        self.parent.execute_search(child.text)
                    return True

        return super().on_touch_down(touch)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.icon = os.path.join(constants.gui_assets, 'icons', 'search-sharp.png')
        self.id = "search_button"
        self.border = (0, 0, 0, 0)
        self.background_normal = self.icon
        self.background_down = self.icon
        self.color_id = [(0.341, 0.353, 0.596, 1), (0.542, 0.577, 0.918, 1)]
        self.background_color = self.color_id[0]

    def on_enter(self, *args):
        if not self.ignore_hover:
            Animation(background_color=self.color_id[1], duration=0.12).start(self)

    def on_leave(self, *args):
        if not self.ignore_hover:
            Animation(background_color=self.color_id[0], duration=0.12).start(self)

class SearchInput(BaseInput):

    def __init__(self, return_function, **kwargs):
        super().__init__(**kwargs)
        self.id = "search_input"
        self.title_text = ""
        self.hint_text = "enter a query..."
        self.halign = "left"
        self.padding_x = 24
        self.background_normal = os.path.join(constants.gui_assets, f'search_input.png')
        self.background_active = os.path.join(constants.gui_assets, f'search_input_selected.png')
        self.bind(on_text_validate=self.on_enter)


    def on_enter(self, value):
        if self.text and self.parent.previous_search != self.text:
            self.parent.execute_search(self.text)


    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        super().keyboard_on_key_down(window, keycode, text, modifiers)

        if not self.text or str.isspace(self.text):
            self.valid(True, False)

        if self.cursor_pos[0] > (self.x + self.width) - (self.width * 0.175):
            self.scroll_x += self.cursor_pos[0] - ((self.x + self.width) - (self.width * 0.175))


    # Input validation
    def insert_text(self, substring, from_undo=False):

        if not self.text and substring == " ":
            substring = ""

        elif len(self.text) < 50:
            s = re.sub('[^a-zA-Z0-9 _().-]', '', substring.splitlines()[0])

            return super().insert_text(s, from_undo=from_undo)


    def valid(self, boolean_value, text=True):

        self.valid_text(boolean_value, text)

        self.background_normal = os.path.join(constants.gui_assets, f'search_input.png')
        self.background_active = os.path.join(constants.gui_assets, f'search_input_selected.png')
        self.hint_text_color = (0.6, 0.6, 1, 0.4)
        self.foreground_color = (0.6, 0.6, 1, 1)
        self.cursor_color = (0.55, 0.55, 1, 1)
        self.selection_color = (0.5, 0.5, 1, 0.4)

def search_input(return_function=None, server_info=None, pos_hint={"center_x": 0.5, "center_y": 0.5}):
    class SearchLayout(FloatLayout):

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.previous_search = ""

        # Gather search results from passed in function
        def execute_search(self, query):
            self.previous_search = query

            def execute():
                current_screen = screen_manager.current_screen.name
                self.loading(True)
                results = False

                try:
                    results = return_function(query, server_info)

                except ConnectionRefusedError:
                    pass

                if not results and isinstance(results, bool):
                    self.previous_search = ""

                if screen_manager.current_screen.name == current_screen:
                    update_screen = functools.partial(screen_manager.current_screen.gen_search_results, results, True)
                    Clock.schedule_once(update_screen, 0)

                    self.loading(False)

            timer = threading.Timer(0, function=execute)
            timer.start()  # Checks for potential crash


        def loading(self, boolean_value):

            for child in self.children:
                if child.id == "load_icon":
                    if boolean_value:
                        Animation(color=(0.6, 0.6, 1, 1), duration=0.05).start(child)
                    else:
                        Animation(color=(0.6, 0.6, 1, 0), duration=0.2).start(child)

                if child.id == "search_button":
                    constants.hide_widget(child, boolean_value)

    def repos_button(bar, button, load, *args):
        def after_window(*args):
            button.x = bar.x + bar.width - button.width - 18
            load.x = bar.x + bar.width - load.width - 14

        Clock.schedule_once(after_window, 0)

    final_layout = SearchLayout()

    # Input box
    search_bar = SearchInput(return_function)
    search_bar.pos_hint = pos_hint

    # Search icon on the right of box
    search_button = SearchButton()
    search_button.pos_hint = {"center_y": pos_hint['center_y']}
    search_button.size_hint_max = (search_bar.height / 3.6, search_bar.height / 3.6)

    # Loading icon to swap button
    load_icon = AsyncImage()
    load_icon.id = "load_icon"
    load_icon.source = os.path.join(constants.gui_assets, 'animations', 'loading_pickaxe.gif')
    load_icon.size_hint_max = (search_bar.height / 3, search_bar.height / 3)
    load_icon.color = (0.6, 0.6, 1, 0)
    load_icon.pos_hint = {"center_y": pos_hint['center_y']}
    load_icon.allow_stretch = True
    load_icon.anim_delay = 0.02

    # Assemble layout
    final_layout.bind(pos=functools.partial(repos_button, search_bar, search_button, load_icon))
    final_layout.bind(size=functools.partial(repos_button, search_bar, search_button, load_icon))
    final_layout.add_widget(search_bar)
    final_layout.add_widget(search_button)
    final_layout.add_widget(load_icon)

    return final_layout



class ServerNameInput(BaseInput):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.title_text = "name"
        self.hint_text = "enter a name..."
        self.bind(on_text_validate=self.on_enter)


    def on_enter(self, value):

        constants.new_server_info['name'] = (self.text).strip()

    # Invalid input
        if not self.text or str.isspace(self.text):
            self.valid(True, False)

        elif self.text.lower() in constants.server_list_lower:
            self.valid(False)

    # Valid input
        else:
            break_loop = False
            for child in self.parent.children:
                if break_loop:
                    break
                for item in child.children:
                    try:
                        if item.id == "next_button":
                            item.force_click()
                            break_loop = True
                            break
                    except AttributeError:
                        pass


    def valid_text(self, boolean_value, text):
        for child in self.parent.children:
            try:
                if child.id == "InputLabel":

                # Empty input
                    if not text:
                        child.clear_text()
                        child.disable_text(True)

                # Valid input
                    elif boolean_value:
                        child.clear_text()
                        child.disable_text(False)

                # Invalid input
                    else:
                        child.update_text("This server already exists")
                        child.disable_text(True)
                    break

            except AttributeError:
                pass


    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        super().keyboard_on_key_down(window, keycode, text, modifiers)

        if keycode[1] == "backspace" and len(self.text) >= 1:
            # Add name to current config
            constants.new_server_info['name'] = (self.text).strip()

            self.valid((self.text).lower().strip() not in constants.server_list_lower)

        def check_validity(*a):
            if not self.text or str.isspace(self.text):
                self.valid(True, False)
        Clock.schedule_once(check_validity, 0)


    # Input validation
    def insert_text(self, substring, from_undo=False):

        if not self.text and substring == " ":
            substring = ""

        elif len(self.text) < 25:
            s = re.sub('[^a-zA-Z0-9 _().-]', '', substring.splitlines()[0])

            self.valid((self.text + s).lower().strip() not in constants.server_list_lower, ((len(self.text + s) > 0) and not (str.isspace(self.text))))

            # Add name to current config
            constants.new_server_info['name'] = (self.text + s).strip()

            return super().insert_text(s, from_undo=from_undo)



class ServerVersionInput(BaseInput):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.title_text = "version"
        self.hint_text = f"click 'next' for latest  ({constants.latestMC[constants.new_server_info['type']]})"
        self.bind(on_text_validate=self.on_enter)


    def on_touch_down(self, touch):
        if not constants.version_loading:
            super().on_touch_down(touch)

        else:
            self.focus = False


    def on_enter(self, value):

        if not constants.version_loading:

            if self.text:
                constants.new_server_info['version'] = (self.text).strip()
            else:
                constants.new_server_info['version'] = constants.latestMC[constants.new_server_info['type']]

            break_loop = False
            for child in self.parent.children:
                if break_loop:
                    break
                for item in child.children:
                    try:
                        if item.id == "next_button":
                            item.force_click()
                            break
                    except AttributeError:
                        pass


    def valid_text(self, boolean_value, text):
        if not constants.version_loading:

            if isinstance(text, bool):
                text = ''

            for child in self.parent.children:
                try:
                    if child.id == "InputLabel":
                    # Invalid input
                        if text and not boolean_value:
                            child.update_text(text)
                            child.disable_text(True)

                        elif boolean_value and text:
                            self.text = constants.new_server_info['version']
                            child.update_text(text, warning=True)
                            child.disable_text(True)

                    # Valid input
                        else:
                            child.clear_text()
                            child.disable_text(False)

                        break

                except AttributeError:
                    pass


    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        if not constants.version_loading:

            super().keyboard_on_key_down(window, keycode, text, modifiers)

            if keycode[1] == "backspace":
                # Add name to current config
                self.valid(True, True)

                if self.text:
                    constants.new_server_info['version'] = (self.text).strip()
                else:
                    constants.new_server_info['version'] = constants.latestMC[constants.new_server_info['type']]


    # Input validation
    def insert_text(self, substring, from_undo=False):

        if not constants.version_loading:

            if not self.text and substring == " ":
                substring = ""

            elif len(self.text) < 10:
                self.valid(True, True)

                s = re.sub('[^a-eA-e0-9 .wpreWPRE-]', '', substring.splitlines()[0]).lower()

                # Add name to current config
                if self.text + s:
                    constants.new_server_info['version'] = (self.text + s).strip()
                else:
                    constants.new_server_info['version'] = constants.latestMC[constants.new_server_info['type']]

                return super().insert_text(s, from_undo=from_undo)


# Auto-complete directory content
class DirectoryInput(BaseInput):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.recommended_folders = ["Users", "AppData", "Roaming", ".minecraft", "saves", "home"]

        # Create suggestion text
        with self.canvas.after:
            self.text_hint = RelativeLayout()
            self.text_hint.text = Label()
            self.text_hint.text.halign = "left"
            self.text_hint.text.valign = "middle"
            self.text_hint.text.color = (0.6, 0.6, 1, 0.4)
            self.text_hint.text.font_name = self.font_name
            self.text_hint.text.font_size = self.font_size
            self.text_hint.text.max_lines = 1
            self.text_hint.text.size_hint = (None, None)
            self.suggestion_index = 0
            self.bind(pos=self.update_suggestion)
            self.bind(focus=self.update_suggestion)
            self.bind(text=self.update_suggestion)
            self.bind(scroll_x=self.update_suggestion)

            # Cover suggestion text on sides
            self.focus_images = RelativeLayout()
            self.focus_images.ghost_cover_left = Image(source=os.path.join(constants.gui_assets, f'text_input_ghost_cover.png'))
            self.focus_images.ghost_cover_right = Image(source=os.path.join(constants.gui_assets, f'text_input_ghost_cover.png'))
            self.focus_images.ghost_image = Image(source=os.path.join(constants.gui_assets, f'text_input_ghost_selected.png'))
            self.focus_images.ghost_image.allow_stretch = True
            self.focus_images.ghost_image.keep_ratio = False
            self.focus_images.ghost_cover_left.allow_stretch = True
            self.focus_images.ghost_cover_left.keep_ratio = False
            self.focus_images.ghost_cover_right.allow_stretch = True
            self.focus_images.ghost_cover_right.keep_ratio = False
            self.focus_images.ghost_image.opacity = 0
            self.focus_images.ghost_cover_left.opacity = 0
            self.focus_images.ghost_cover_right.opacity = 0
            self.focus_images.ghost_cover_left.color = constants.background_color
            self.focus_images.ghost_cover_right.color = constants.background_color

        self.word_list = []
        self.suggestion = (0.6, 0.6, 1, 0.4)
        self.bind(text=self.on_text)

    def update_suggestion(self, *args):
        self.focus_images.ghost_image.size = (self.width+4, self.height+4)
        self.focus_images.ghost_image.pos = (self.x-2, self.y-2)
        self.focus_images.ghost_cover_left.pos = (0, self.y-(self.height/2))
        self.focus_images.ghost_cover_left.width = ((Window.size[0]/2)-(self.width/2)+self.padding_x[0])
        self.focus_images.ghost_cover_right.pos = (self.x+self.width-self.padding_x[0], self.y-(self.height/2))
        self.focus_images.ghost_cover_right.width = ((Window.size[0]/2)-(self.width/2)+self.padding_x[0])
        self.focus_images.ghost_image.opacity = 1 if self.focus else 0
        self.focus_images.ghost_cover_left.opacity = 1 if self.focus else 0
        self.focus_images.ghost_cover_right.opacity = 1 if self.focus else 0

        Animation(opacity=(1 if self.focus else 0), duration=0.05).start(self.text_hint.text)

        self.text_hint.size = self.size

        if self.focus:
            self.text_hint.text.text_size = (self.size[0] * 12, self.size[1])
            self.text_hint.text.pos = (self.x + self.padding[0] + (self.size[0] * 5.5), self.y - self.font_size)
            self.text_hint.text.width = (self.width) - (self.scroll_x * 2)

            # Gather word list
            if len(self.text) > 0:
                if (self.text[0] != ".") and (('\\' in self.text) or ('/' in self.text)):
                    self.word_list = constants.hidden_glob(self.text)
                    self.on_text(None, self.text)

    def on_text(self, instance, value):
        # Prevent extra slashes in file name

        if self.text.startswith('"') and self.text.endswith('"'):
            self.text = self.text[1:-1]

        self.text = self.text.replace("\\\\", "\\").replace("//", "/").replace("\\/", "\\").replace("/\\", "/")
        self.text = self.text.replace("/", "\\") if constants.os_name == "windows" else self.text.replace("\\", "/")
        self.text = self.text.replace("*", "")

        """ Include all current text from textinput into the word list to
        emulate the same kind of behavior as sublime text has.
        """
        self.text_hint.text.text = ''

        # for item in self.word_list:
        #     print(os.path.split(item)[1] in self.recommended_folders)
        #     if os.path.split(item)[1] in self.recommended_folders:
        #         self.suggestion_index = self.word_list.index(item)
        #         print(self.suggestion_index)
        #         break

        word_list = constants.rotate_array(sorted(list(set(
            self.word_list + value[:value.rfind('     ')].split('     ')))), self.suggestion_index)

        word_list = [item for item in word_list if not (len(item) == 3 and ":\\" in item)
                     and not (len(item) == 2 and ":" in item)
                     and item]

        val = value[value.rfind('     ') + 1:]
        if not val:
            return
        try:
            # grossly inefficient just for demo purposes
            word = [word for word in word_list
                    if word.startswith(val)][0][len(val):]
            if not word:
                return
            self.text_hint.text.text = self.text + word
        except IndexError:
            # No matches found
            pass

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        # Add support for tab as an 'autocomplete' using the suggestion text.
        hint_text = self.text_hint.text.text[len(self.text):] + ''

        if self.text_hint.text.text and keycode[1] in ['tab', 'right']:
            self.insert_text(hint_text)

            # Automatically add slash to directory
            if os.path.isdir(self.text) and not (os.path.isfile(os.path.join(self.text, "level.dat")) or os.path.isfile(os.path.join(self.text, 'special_level.dat'))):
                self.insert_text("\\" if constants.os_name == "windows" else "/")

                if self.cursor_pos[0] > (self.x + self.width) - (self.width * 0.33):
                    self.scroll_x += self.cursor_pos[0] - ((self.x + self.width) - (self.width * 0.33))

            self.do_cursor_movement('cursor_end', True)
            Clock.schedule_once(functools.partial(self.do_cursor_movement, 'cursor_end', True), 0.01)
            Clock.schedule_once(functools.partial(self.select_text, 0), 0.01)
            self.suggestion_index = 0
            return True

        elif keycode[1] == 'backspace':
            self.suggestion_index = 0
            self.on_text(None, self.text)

        elif keycode[1] == 'tab':
            return

        elif keycode[1] == 'up':
            self.suggestion_index += 1
            if self.suggestion_index >= len(self.word_list):
                self.suggestion_index = 0
            self.on_text(None, self.text)

        elif keycode[1] == 'down':
            self.suggestion_index -= 1
            if self.suggestion_index < 0:
                self.suggestion_index = len(self.word_list)-1
            self.on_text(None, self.text)

        else:
            self.suggestion_index = 0

        return super().keyboard_on_key_down(window, keycode, text, modifiers)


class ServerWorldInput(DirectoryInput):

    # Hide input_button on focus
    def _on_focus(self, *args):
        super()._on_focus(*args)

        for child in self.parent.children:
            for child_item in child.children:
                try:
                    if child_item.id == "input_button":

                        if constants.new_server_info['server_settings']['world'] == "world":
                            self.hint_text = "type a directory, or click browse..." if self.focus else "create a new world"

                        # Run input validation on focus change
                        if self.focus:
                            self.valid(True, True)

                        # If unfocused, validate text
                        if not self.focus and self.text and child_item.height == 0:
                            self.on_enter(self.text)

                        # If box deleted and unfocused, set back to previous text
                        elif not self.focus and not self.text and constants.new_server_info['server_settings']['world'] != "world":
                            self.text = self.cache_text

                        # If box filled in and text box clicked
                        if self.focus and self.text:
                            self.text = constants.new_server_info['server_settings']['world']
                            self.do_cursor_movement('cursor_end', True)
                            Clock.schedule_once(functools.partial(self.do_cursor_movement, 'cursor_end', True), 0.01)
                            Clock.schedule_once(functools.partial(self.select_text, 0), 0.01)

                        [constants.hide_widget(item, self.focus) for item in child.children]

                        return

                except AttributeError:
                    continue

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.halign = "left"
        self.padding_x = 25
        self.size_hint_max = (528, 54)
        self.title_text = "world file"
        self.hint_text = "create a new world"
        self.cache_text = ""
        world = constants.new_server_info['server_settings']['world']
        self.selected_world = None if world == 'world' else world
        self.world_verified = False
        self.update_world(hide_popup=True)

    def on_enter(self, value):

        if constants.os_name == "windows" and "\\" not in self.text:
            self.text = os.path.join(constants.saveFolder, self.text)

        elif constants.os_name != "windows" and "/" not in self.text:
            self.text = os.path.join(constants.saveFolder, self.text)

        self.selected_world = self.text.replace("~", constants.home)
        self.update_world()

    # Input validation and server selection
    def valid_text(self, boolean_value, text):
        if not constants.version_loading:

            for child in self.parent.children:
                try:
                    if child.id == "InputLabel":
                    # Invalid input
                        if not boolean_value:
                            child.update_text('This world is invalid or corrupt')
                            self.text = ""
                    # Valid input
                        else:
                            child.clear_text()
                        break
                except AttributeError:
                    pass

    def update_world(self, force_ignore=False, hide_popup=False):
        if self.selected_world == "world":
            self.text = ''

        self.scroll_x = 0

        if self.selected_world:
            self.selected_world = os.path.abspath(self.selected_world)

            # Check if the selected world is invalid
            if not (os.path.isfile(os.path.join(self.selected_world, 'level.dat')) or os.path.isfile(os.path.join(self.selected_world, 'special_level.dat'))):
                if self.selected_world != os.path.abspath(os.curdir):
                    try:
                        constants.new_server_info['server_settings']['world'] = 'world'
                        if not force_ignore:
                            self.valid_text(False, False)
                        self.parent.parent.toggle_new(False)
                    except AttributeError:
                        pass

            # If world is valid, do this
            else:
                if constants.new_server_info['server_settings']['world'] != "world":
                    box_text = os.path.join(
                        *Path(os.path.abspath(constants.new_server_info['server_settings']['world'])).parts[-2:])
                    self.cache_text = self.text = box_text[:30] + "..." if len(box_text) > 30 else box_text

                def world_valid():
                    box_text = os.path.join(*Path(os.path.abspath(self.selected_world)).parts[-2:])
                    self.cache_text = self.text = box_text[:30] + "..." if len(box_text) > 30 else box_text
                    try:
                        constants.new_server_info['server_settings']['world'] = self.selected_world
                        self.valid_text(True, True)
                        self.parent.parent.toggle_new(True)
                    except AttributeError:
                        pass


                # When valid world selected, check if it matches server version
                check_world = constants.check_world_version(self.selected_world, constants.new_server_info['version'])

                if check_world[0] or hide_popup:
                    world_valid()

                else:
                    content = None
                    basename = os.path.basename(self.selected_world)
                    basename = basename[:30] + "..." if len(basename) > 30 else basename

                    if check_world[1]:
                        content = f"'{basename}' was created in\
 version {check_world[1]}, which is newer than your server. This may cause a crash.\
\n\nWould you like to use this world anyway?"
                    elif constants.version_check(constants.new_server_info['version'], "<", "1.9"):
                        content = f"'{basename}' was created in a version prior to 1.9 and may be incompatible.\
\n\nWould you like to use this world anyway?"

                    if content:
                        screen_manager.current_screen.show_popup(
                            "query",
                            "Potential Incompatibility",
                            content,
                            [None, functools.partial(world_valid)]
                        )

                    else:
                        world_valid()


class ServerImportPathInput(DirectoryInput):

    # Hide input_button on focus
    def _on_focus(self, *args):
        super()._on_focus(*args)

        for child in self.parent.children:
            for child_item in child.children:
                try:
                    if child_item.id == "input_button":

                        if not self.text:
                            self.hint_text = "type a path, or click browse..."

                        # Run input validation on focus change
                        if self.focus:
                            self.valid(True, True)

                        # If unfocused, validate text
                        if not self.focus and self.text and child_item.height == 0:
                            self.on_enter(self.text)

                        # If box deleted and unfocused, set back to previous text
                        elif not self.focus and not self.text:
                            self.text = self.cache_text

                        # If box filled in and text box clicked
                        if self.focus and self.text:
                            self.text = self.selected_server
                            self.do_cursor_movement('cursor_end', True)
                            Clock.schedule_once(functools.partial(self.do_cursor_movement, 'cursor_end', True), 0.01)
                            Clock.schedule_once(functools.partial(self.select_text, 0), 0.01)

                        [constants.hide_widget(item, self.focus) for item in child.children]

                        return

                except AttributeError:
                    continue

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.halign = "left"
        self.padding_x = 25
        self.size_hint_max = (528, 54)
        self.title_text = "server path"
        self.hint_text = "type a path, or click browse..."
        self.cache_text = ""
        server = ""
        self.selected_server = None if server == '' else server
        self.server_verified = False
        self.update_server(hide_popup=True)

    def on_enter(self, value):
        self.selected_server = self.text.replace("~", constants.home)
        self.update_server()

    # Input validation and server selection
    def valid_text(self, boolean_value, text):
        for child in self.parent.children:
            try:
                if child.id == "InputLabel":
                # Invalid input
                    if not boolean_value:
                        if isinstance(text, str) and text:
                            child.update_text(text)
                        else:
                            child.update_text('This server is invalid or corrupt')
                        self.text = ""
                # Valid input
                    else:
                        child.clear_text()
                    break
            except AttributeError:
                pass


    def update_server(self, force_ignore=False, hide_popup=False):

        def disable_next(disable=False):
            for item in screen_manager.current_screen.next_button.children:
                try:
                    if item.id == "next_button":
                        item.disable(disable)
                        break
                except AttributeError:
                    pass

        self.scroll_x = 0

        if self.selected_server:
            self.selected_server = os.path.abspath(self.selected_server)

            # Check if the selected server is invalid
            if not (os.path.isfile(os.path.join(self.selected_server, 'server.properties'))):
                if self.selected_server != os.path.abspath(os.curdir):
                    try:
                        self.selected_server = ''
                        if not force_ignore:
                            self.valid_text(False, False)
                        disable_next(True)
                    except AttributeError:
                        pass


            # Don't allow import of already imported servers
            elif os.path.join(constants.applicationFolder, 'Servers') in self.selected_server or constants.server_path(os.path.basename(self.selected_server)):
                self.valid_text(False, "This server already exists!")
                disable_next(True)


            # If server is valid, do this
            else:
                constants.import_data = {'name': re.sub('[^a-zA-Z0-9 _().-]', '', os.path.basename(self.selected_server).splitlines()[0])[:25], 'path': self.selected_server}
                box_text = os.path.join(*Path(os.path.abspath(self.selected_server)).parts[-2:])
                self.cache_text = self.text = box_text[:30] + "..." if len(box_text) > 30 else box_text
                self.valid_text(True, True)
                disable_next(False)

class ServerImportBackupInput(DirectoryInput):

    # Hide input_button on focus
    def _on_focus(self, *args):
        super()._on_focus(*args)

        for child in self.parent.children:
            for child_item in child.children:
                try:
                    if child_item.id == "input_button":

                        if not self.text:
                            self.hint_text = "type a path, or click browse..."

                        # Run input validation on focus change
                        if self.focus:
                            self.valid(True, True)

                        # If unfocused, validate text
                        if not self.focus and self.text and child_item.height == 0:
                            self.on_enter(self.text)

                        # If box deleted and unfocused, set back to previous text
                        elif not self.focus and not self.text:
                            self.text = self.cache_text

                        # If box filled in and text box clicked
                        if self.focus and self.text:
                            self.text = self.selected_server
                            self.do_cursor_movement('cursor_end', True)
                            Clock.schedule_once(functools.partial(self.do_cursor_movement, 'cursor_end', True), 0.01)
                            Clock.schedule_once(functools.partial(self.select_text, 0), 0.01)

                        [constants.hide_widget(item, self.focus) for item in child.children]

                        return

                except AttributeError:
                    continue

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.halign = "left"
        self.padding_x = 25
        self.size_hint_max = (528, 54)
        self.title_text = "server path"
        self.hint_text = "type a path, or click browse..."
        self.cache_text = ""
        server = ""
        self.selected_server = None if server == '' else server
        self.server_verified = False
        self.update_server(hide_popup=True)

    def on_enter(self, value):
        self.selected_server = self.text.replace("~", constants.home)
        self.update_server()

    # Input validation and server selection
    def valid_text(self, boolean_value, text):
        for child in self.parent.children:
            try:
                if child.id == "InputLabel":
                # Invalid input
                    if not boolean_value:
                        if isinstance(text, str) and text:
                            child.update_text(text)
                        else:
                            child.update_text('This server is invalid or corrupt')
                        self.text = ""
                # Valid input
                    else:
                        child.clear_text()
                    break
            except AttributeError:
                pass


    def update_server(self, force_ignore=False, hide_popup=False):

        def disable_next(disable=False):
            for item in screen_manager.current_screen.next_button.children:
                try:
                    if item.id == "next_button":
                        item.disable(disable)
                        break
                except AttributeError:
                    pass

        self.scroll_x = 0

        if self.selected_server:
            self.selected_server = os.path.abspath(self.selected_server)

            # Extract auto-mcs.ini and server.properties
            file_failure = True
            server_name = None
            new_path = None
            test_path = constants.tempDir
            cwd = os.path.abspath(os.curdir)
            print(self.selected_server)
            if (self.selected_server.endswith(".tgz") or self.selected_server.endswith(".amb") and os.path.isfile(self.selected_server)):
                constants.folder_check(test_path)
                os.chdir(test_path)
                constants.run_proc(f'tar -xf "{self.selected_server}"{"" if constants.os_name == "windows" else " --wildcards"} *auto-mcs.ini')
                constants.run_proc(f'tar -xf "{self.selected_server}" server.properties')
                if (os.path.exists(os.path.join(test_path, "auto-mcs.ini")) or os.path.exists(os.path.join(test_path, ".auto-mcs.ini"))) and os.path.exists(os.path.join(test_path, "server.properties")):
                    if os.path.exists(os.path.join(test_path, "auto-mcs.ini")):
                        new_path = os.path.join(test_path, "auto-mcs.ini")
                    elif os.path.exists(os.path.join(test_path, ".auto-mcs.ini")):
                        new_path = os.path.join(test_path, ".auto-mcs.ini")
                    if new_path:
                        try:
                            config_file = constants.server_config(server_name=None, config_path=new_path)
                            server_name = config_file.get('general', 'serverName')
                        except:
                            pass
                        file_failure = False
                        # print(server_name, file_failure)

                os.chdir(cwd)
                constants.safe_delete(test_path)


            # Check if the selected server is invalid
            if file_failure:
                if self.selected_server != os.path.abspath(os.curdir):
                    try:
                        self.selected_server = ''
                        if not force_ignore:
                            self.valid_text(False, False)
                        disable_next(True)
                    except AttributeError:
                        pass


            # Don't allow import of already imported servers
            elif constants.server_path(server_name):
                self.valid_text(False, "This server already exists!")
                disable_next(True)


            # If server is valid, do this
            else:
                constants.import_data = {'name': re.sub('[^a-zA-Z0-9 _().-]', '', server_name.splitlines()[0])[:25], 'path': self.selected_server}
                box_text = os.path.join(*Path(os.path.abspath(self.selected_server)).parts[-2:-1], server_name)
                self.cache_text = self.text = box_text[:30] + "..." if len(box_text) > 30 else box_text
                self.valid_text(True, True)
                disable_next(False)



class ServerSeedInput(BaseInput):

    # Hide input_button on focus
    def _on_focus(self, *args):
        try:
            super()._on_focus(*args)

            if constants.version_check(constants.new_server_info['version'], '>=', "1.1"):
                for child in self.parent.children:
                    for child_item in child.children:
                        try:
                            if "drop_button" in child_item.id:

                                # If box filled in and text box clicked
                                if self.focus and self.text:
                                    self.text = constants.new_server_info['server_settings']['seed']
                                    self.do_cursor_movement('cursor_end', True)
                                    Clock.schedule_once(functools.partial(self.do_cursor_movement, 'cursor_end', True), 0.01)
                                    Clock.schedule_once(functools.partial(self.select_text, 0), 0.01)

                                if not self.focus:
                                    # If text under button, cut it off temporarily
                                    self.scroll_x = 0
                                    self.cursor = (len(self.text), 0)
                                    if self.cursor_pos[0] > (self.x + self.width) - (self.width * 0.38):
                                        self.text = constants.new_server_info['server_settings']['seed'][:16] + "..."
                                    self.scroll_x = 0
                                    Clock.schedule_once(functools.partial(self.select_text, 0), 0.01)

                                [constants.hide_widget(item, self.focus) for item in child.children]

                                return

                        except AttributeError:
                            continue

        except Exception as e:
            print(f"Warning: Failed to focus input box ({e})")

    def on_enter(self, value):

        constants.new_server_info['server_settings']['seed'] = (self.text).strip()

        break_loop = False
        for child in self.parent.children:
            if break_loop:
                break
            for item in child.children:
                try:
                    if item.id == "next_button":
                        item.force_click()
                        break
                except AttributeError:
                    pass

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.size_hint_max = (528, 54)
        self.padding_x = 25
        self.title_text = "world seed"
        self.hint_text = "enter a seed..."
        self.text = constants.new_server_info['server_settings']['seed']
        self.bind(on_text_validate=self.on_enter)

        if constants.new_server_info['server_settings']['world'] == "world":
            if constants.version_check(constants.new_server_info['version'], '>=', "1.1"):
                self.halign = "left"
                Clock.schedule_once(functools.partial(self._on_focus, self, True), 0.0)
                Clock.schedule_once(functools.partial(self._on_focus, self, False), 0.0)


    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        super().keyboard_on_key_down(window, keycode, text, modifiers)

        # if constants.version_check(constants.new_server_info['version'], '>=', "1.1"):
        #     if self.cursor_pos[0] > (self.x + self.width) - (self.width * 0.38):
        #         self.scroll_x += self.cursor_pos[0] - ((self.x + self.width) - (self.width * 0.38))

        if keycode[1] == "backspace":
            # Add seed to current config
            constants.new_server_info['server_settings']['seed'] = (self.text).strip()

    # Input validation
    def insert_text(self, substring, from_undo=False):

        if not self.text and substring == " ":
            substring = ""

        elif len(self.text) < 32:
            s = re.sub('[^a-zA-Z0-9 _/{}=+|"\'()*&^%$#@!?;:,.-]', '', substring.splitlines()[0])

            # Add name to current config
            constants.new_server_info['server_settings']['seed'] = (self.text + s).strip()

            return super().insert_text(s, from_undo=from_undo)



class CreateServerPortInput(BaseInput):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.size_hint_max = (528, 54)
        self.title_text = "IPv4/port"
        self.hint_text = "enter IPv4 or port  (localhost:25565)"
        self.stinky_text = ""
        self.bind(on_text_validate=self.on_enter)


    def on_enter(self, value):
        self.process_text()

        break_loop = False
        for child in self.parent.children:
            if break_loop:
                break
            for item in child.children:
                try:
                    if item.id == "next_button":
                        if not item.disabled:
                            item.force_click()
                        break_loop = True
                        break
                except AttributeError:
                    pass


    def valid_text(self, boolean_value, text):
        for child in self.parent.children:
            try:
                if child.id == "InputLabel":

                # Valid input
                    if boolean_value:
                        child.clear_text()
                        child.disable_text(False)

                # Invalid input
                    else:
                        child.update_text(self.stinky_text)
                        child.disable_text(True)
                    break

            except AttributeError:
                pass


    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        super().keyboard_on_key_down(window, keycode, text, modifiers)

        if keycode[1] == "backspace":
            self.process_text()


    # Input validation
    def insert_text(self, substring, from_undo=False):

        if not self.text and substring == " ":
            substring = ""

        elif len(self.text) < 21:
            s = re.sub('[^0-9:.]', '', substring.splitlines()[0])

            if ":" in self.text and ":" in s:
                s = ''
            if ("." in s and ((self.cursor_col > self.text.find(":")) and (self.text.find(":") > -1))) or ("." in s and self.text.count(".") >= 3):
                s = ''

            # Add name to current config
            def process(*a):
                self.process_text(text=(self.text))
            Clock.schedule_once(process, 0)

            return super().insert_text(s, from_undo=from_undo)


    def process_text(self, text=''):

        typed_info = text if text else self.text

        # interpret typed information
        if ":" in typed_info:
            constants.new_server_info['ip'], constants.new_server_info['port'] = typed_info.split(":")
        else:
            if "." in typed_info:
                constants.new_server_info['ip'] = typed_info.replace(":", "")
                constants.new_server_info['port'] = "25565"
            else:
                constants.new_server_info['port'] = typed_info.replace(":", "")

        if not constants.new_server_info['port']:
            constants.new_server_info['port'] = "25565"

        # print("ip: " + constants.new_server_info['ip'], "port: " + constants.new_server_info['port'])

        # Input validation
        port_check = ((int(constants.new_server_info['port']) < 1024) or (int(constants.new_server_info['port']) > 65535))
        ip_check = (constants.check_ip(constants.new_server_info['ip']) and '.' in typed_info)
        self.stinky_text = ''

        if typed_info:

            if not ip_check and ("." in typed_info or ":" in typed_info):
                self.stinky_text = 'Invalid IPv4 address' if not port_check else 'Invalid IPv4 and port'

            elif port_check:
                self.stinky_text = ' Invalid port  (use 1024-65535)'

        else:
            constants.new_server_info['ip'] = ''
            constants.new_server_info['port'] = '25565'

        process_ip_text()
        self.valid(not self.stinky_text)

class ServerPortInput(CreateServerPortInput):
    def process_text(self, text=''):
        server_obj = constants.server_manager.current_server
        new_ip = ''
        default_port = "25565"
        new_port = default_port

        typed_info = text if text else self.text

        # interpret typed information
        if ":" in typed_info:
            new_ip, new_port = typed_info.split(":")
        else:
            if "." in typed_info or not new_port:
                new_ip = typed_info.replace(":", "")
                new_port = default_port
            else:
                new_port = typed_info.replace(":", "")

        if not str(server_obj.port) or not new_port:
            new_port = default_port

        # Input validation
        port_check = ((int(new_port) < 1024) or (int(new_port) > 65535))
        ip_check = (constants.check_ip(new_ip) and '.' in typed_info)
        self.stinky_text = ''
        fail = False

        if typed_info:

            if not ip_check and ("." in typed_info or ":" in typed_info):
                self.stinky_text = 'Invalid IPv4 address' if not port_check else 'Invalid IPv4 and port'
                fail = True

            elif port_check:
                self.stinky_text = ' Invalid port  (use 1024-65535)'
                fail = True

        else:
            new_ip = ''
            new_port = '25565'

        if not fail:
            server_obj.ip = new_ip
            server_obj.server_properties['server-ip'] = new_ip

        if new_port and not fail:
            server_obj.port = int(new_port)
            server_obj.server_properties['server-port'] = new_port

        if (new_ip or new_port) and not fail:
            constants.server_properties(server_obj.name, write_object=server_obj.server_properties)
            server_obj.reload_config()

        process_ip_text(server_obj=server_obj)
        self.valid(not self.stinky_text)



class ServerMOTDInput(BaseInput):

    def on_enter(self, value):

        constants.new_server_info['server_settings']['motd'] = (self.text).strip() if self.text else "A Minecraft Server"

        break_loop = False
        for child in self.parent.children:
            if break_loop:
                break
            for item in child.children:
                try:
                    if item.id == "next_button":
                        item.force_click()
                        break
                except AttributeError:
                    pass

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.size_hint_max = (528, 54)
        self.title_text = "MOTD"
        self.hint_text = "enter a message of the day..."
        self.text = constants.new_server_info['server_settings']['motd'] if constants.new_server_info['server_settings']['motd'] != "A Minecraft Server" else ""
        self.bind(on_text_validate=self.on_enter)

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        super().keyboard_on_key_down(window, keycode, text, modifiers)

        if keycode[1] == "backspace" and len(self.text):
            # Add name to current config
            constants.new_server_info['server_settings']['motd'] = (self.text).strip() if self.text else "A Minecraft Server"


    # Input validation
    def insert_text(self, substring, from_undo=False):

        if not self.text and substring == " ":
            substring = ""

        elif len(self.text) < 32:
            s = re.sub('[^a-zA-Z0-9 _/{}=+|"\'()*&^%$#@!?;:,.-]', '', substring.splitlines()[0])

            # Add name to current config
            constants.new_server_info['server_settings']['motd'] = (self.text + s).strip() if self.text + s else "A Minecraft Server"

            return super().insert_text(s, from_undo=from_undo)



class ServerPlayerInput(BaseInput):

    def on_enter(self, value):
        constants.new_server_info['server_settings']['max_players'] = (self.text).strip() if self.text else "20"


    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.size_hint_max = (440, 54)
        self.title_text = " max players "
        self.hint_text = "max players  (20)"
        self.text = constants.new_server_info['server_settings']['max_players'] if constants.new_server_info['server_settings']['max_players'] != "20" else ""
        self.bind(on_text_validate=self.on_enter)

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        super().keyboard_on_key_down(window, keycode, text, modifiers)

        if keycode[1] == "backspace" and len(self.text):
            # Add name to current config
            constants.new_server_info['server_settings']['max_players'] = (self.text).strip() if self.text else "20"

    # Input validation
    def insert_text(self, substring, from_undo=False):

        if not self.text and substring in [" ", "0"]:
            substring = ""

        elif len(self.text) < 7:
            s = re.sub('[^0-9]', '', substring.splitlines()[0])

            # Add name to current config
            constants.new_server_info['server_settings']['max_players'] = (self.text + s).strip() if self.text + s else "20"

            return super().insert_text(s, from_undo=from_undo)



class ServerTickSpeedInput(BaseInput):

    def on_enter(self, value):
        constants.new_server_info['server_settings']['random_tick_speed'] = (self.text).strip() if self.text else "3"


    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.size_hint_max = (440, 54)
        self.title_text = "tick speed"
        self.hint_text = "random tick speed  (3)"
        self.text = constants.new_server_info['server_settings']['random_tick_speed'] if constants.new_server_info['server_settings']['random_tick_speed'] != "3" else ""
        self.bind(on_text_validate=self.on_enter)

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        super().keyboard_on_key_down(window, keycode, text, modifiers)

        if keycode[1] == "backspace" and len(self.text):
            # Add name to current config
            constants.new_server_info['server_settings']['random_tick_speed'] = (self.text).strip() if self.text else "3"

    # Input validation
    def insert_text(self, substring, from_undo=False):

        if not self.text and substring in [" "]:
            substring = ""

        elif len(self.text) < 5:
            s = re.sub('[^0-9]', '', substring.splitlines()[0])

            # Add name to current config
            constants.new_server_info['server_settings']['random_tick_speed'] = (self.text + s).strip() if self.text + s else "3"

            return super().insert_text(s, from_undo=from_undo)



class AclInput(BaseInput):

    # Hide input_button on focus
    def _on_focus(self, *args):
        super()._on_focus(*args)

        for child in self.parent.children:
            for child_item in child.children:
                try:
                    if child_item.id == "input_button":

                        # self.hint_text = "search for rules, press 'ENTER' to add..." if self.focus else "search for rules..."

                        # If box filled in and text box clicked
                        if self.focus and self.text:
                            self.text = self.actual_text
                            self.do_cursor_movement('cursor_end', True)
                            Clock.schedule_once(functools.partial(self.do_cursor_movement, 'cursor_end', True), 0.01)
                            Clock.schedule_once(functools.partial(self.select_text, 0), 0.01)

                        if not self.focus:
                            # If text under button, cut it off temporarily
                            self.scroll_x = 0
                            self.cursor = (len(self.text), 0)
                            if self.cursor_pos[0] > (self.x + self.width) - (self.width * 0.38):
                                self.text = self.text[:16] + "..."
                            self.scroll_x = 0
                            Clock.schedule_once(functools.partial(self.select_text, 0), 0.01)

                        [constants.hide_widget(item, self.focus) for item in child.children]

                        return

                except AttributeError:
                    continue

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.halign = "left"
        self.padding_x = 25
        self.size_hint_max = (528, 54)
        self.title_text = ""
        self.hint_text = "search for rules..."
        self.actual_text = ""

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        super().keyboard_on_key_down(window, keycode, text, modifiers)
        # self.actual_text = self.text + ('' if not text else text)
        # Backspace
        if keycode[0] == 8:
            self.actual_text = self.text + ('' if not text else text)
            screen_manager.current_screen.search_filter(self.actual_text)

    def insert_text(self, substring, from_undo=False):
        if not self.text and substring in [" "]:
            substring = ""

        else:
            s = re.sub('[^a-zA-Z0-9 _().!/,-]', '', substring.splitlines()[0])

            # Filter input, and process data to search_filter function in AclScreen
            self.actual_text = (self.text + s).strip() if self.text + s else ""
            screen_manager.current_screen.search_filter(self.actual_text)

            return super().insert_text(s, from_undo=from_undo)

class AclRuleInput(BaseInput):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.title_text = "enter rules"
        self.hint_text = "enter rules..."
        self.halign = "left"
        self.padding_x = 25
        self.bind(on_text_validate=self.on_enter)


    def on_enter(self, value):

    # Invalid input
        if not self.text or str.isspace(self.text):
            self.valid(True, False)

    # Valid input
        else:
            break_loop = False
            for child in self.parent.children:
                if break_loop:
                    break
                for item in child.children:
                    try:
                        if item.id == "next_button":
                            item.force_click()
                            break
                    except AttributeError:
                        pass


    def valid_text(self, boolean_value, text):
        for child in self.parent.children:
            try:
                if child.id == "InputLabel":

                # Empty input
                    if not text:
                        child.clear_text()
                        child.disable_text(True)

                # Valid input
                    elif boolean_value:
                        child.clear_text()
                        child.disable_text(False)

            except AttributeError:
                pass


    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        super().keyboard_on_key_down(window, keycode, text, modifiers)

        if not self.text or str.isspace(self.text):
            self.valid(True, False)


    # Input validation
    def insert_text(self, substring, from_undo=False):

        if not self.text and substring == " ":
            substring = ""

        else:

            if screen_manager.current_screen.current_list == "bans":
                reg_exp = '[^a-zA-Z0-9 _.,!/-]'
            else:
                reg_exp = '[^a-zA-Z0-9 _,!]'

            s = re.sub(reg_exp, '', substring.splitlines()[0])

            original_rule = self.text.split(",")[:self.text[:self.cursor_index()].count(",") + 1][-1]
            rule = original_rule + s.replace(",","")

            # Format pasted text
            if len(s) > 3:
                s = ', '.join([item.strip()[:16].strip() if not (item.count(".") >= 3) else item.strip() for item in s.split(",")])
                if len(s.split(", ")[0].strip() + original_rule) > 16 and not (original_rule.count(".") >= 3):
                    s = ", " + s + ", "


            # Format typed text
            elif len(rule.strip()) > 16 and not (rule.count(".") >= 3):
                s = ""

            if s == ",":
                s = ", "


            self.valid(True, ((len(self.text + s) > 0) and not (str.isspace(self.text))))

            return super().insert_text(s, from_undo=from_undo)



class NgrokAuthInput(BaseInput):

    def check_next(self):
        break_loop = False
        for child in self.parent.children:
            if break_loop:
                break
            for item in child.children:
                try:
                    if item.id == "next_button":
                        item.disable(self.text == '')
                        break
                except AttributeError:
                    pass

    def on_enter(self, value):
        break_loop = False
        for child in self.parent.children:
            if break_loop:
                break
            for item in child.children:
                try:
                    if item.id == "next_button":
                        item.force_click()
                        break
                except AttributeError:
                    pass

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.size_hint_max = (528, 54)
        self.padding_x = 25
        self.title_text = "authtoken"
        self.hint_text = "paste your ngrok authtoken..."
        self.padding_y = (14, 0)
        self.text = ''
        self.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["mono-medium"]}.otf')
        self.bind(on_text_validate=self.on_enter)

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        super().keyboard_on_key_down(window, keycode, text, modifiers)

        if keycode[1] == "backspace":
            self.text = ''

        self.check_next()

    # Input validation
    def insert_text(self, substring, from_undo=False):
        if not self.text and len(substring) > 10 and '\n' not in substring:
            self.text = substring
        self.check_next()




class BlankInput(BaseInput):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.halign = "left"
        self.padding_x = 25
        self.size_hint_max = (440, 54)
        self.hint_text_color = (0.6, 0.6, 1, 0.8)
        self.title_text = ""
        self.hint_text = ""
        self.bind(on_text_validate=self.on_enter)


    # Make the text box non-interactive
    def on_enter(self, value):
        return

    def on_touch_down(self, touch):
        self.focus = False

    def disable(self, boolean):
        self.opacity = 0.4 if boolean else 1

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        return

    def insert_text(self, substring, from_undo=False):
        return
def blank_input(pos_hint, hint_text, disabled=False):
    blank = BlankInput()
    blank.pos_hint = pos_hint
    blank.hint_text = hint_text
    blank.disable(disabled)
    return blank



# --------------------------------------------------  File chooser  ----------------------------------------------------

def file_popup(ask_type, start_dir=constants.home, ext=[], input_name=None, select_multiple=False, title=None):
    final_path = ""
    file_icon = os.path.join(constants.gui_assets, "small-icon.ico")

    # Will find the first file start_dir to auto select
    def iter_start_dir(directory):
        end_dir = directory

        for dir_item in glob(os.path.join(start_dir, "*")):
            end_dir = dir_item
            break

        return end_dir


    # Make sure that ask_type file can dynamically choose between a list and a single file
    if ask_type == "file":
        final_path = filechooser.open_file(title=title, filters=ext, path=iter_start_dir(start_dir), multiple=select_multiple, icon=file_icon)
        # Ext = [("Comma-separated Values", "*.csv")]

    elif ask_type == "dir":
        if constants.os_name == "windows":
            root = tk.Tk()
            root.withdraw()
            root.iconbitmap(file_icon)
            final_path = filedialog.askdirectory(initialdir=start_dir, title=title)
            Window.raise_window()
        else:
            final_path = filechooser.choose_dir(path=iter_start_dir(start_dir), title=title, icon=file_icon, multiple=False)
            final_path = final_path[0] if final_path else None

    # World screen
    if input_name:
        break_loop = False
        for item in screen_manager.current_screen.children:
            if break_loop:
                break
            for child in item.children:
                if break_loop:
                    break
                if child.__class__.__name__ == input_name:
                    if input_name == "ServerWorldInput":
                        if final_path:
                            child.selected_world = os.path.abspath(final_path)
                            child.update_world()
                    break_loop = True
                    break

    # Import screen
    if input_name:
        break_loop = False
        for child in screen_manager.current_screen.walk():
            if break_loop:
                break
            if child.__class__.__name__ == input_name:
                if input_name.startswith("ServerImport"):
                    if final_path:
                        child.selected_server = os.path.abspath(final_path) if isinstance(final_path, str) else os.path.abspath(final_path[0])
                        child.update_server()
                break_loop = True
                break

    return final_path

# ----------------------------------------------------------------------------------------------------------------------



class HeaderBackground(Widget):

    y_offset = dp(62)

    def update_rect(self, *args):
        self.rect.size = self.size[0], self.y_offset
        self.rect.pos = (self.pos[0], round(Window.height) - self.rect.size[1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas.before:
            self.rect = Image(pos=self.pos, size=self.size, allow_stretch=True, keep_ratio=False, source=os.path.join(constants.gui_assets, 'header_background.png'))

        with self.canvas.after:
            self.canvas.clear()

        self.bind(pos=self.update_rect)
        self.bind(size=self.update_rect)



class FooterBackground(Widget):

    y_offset = dp(50)

    def update_rect(self, *args):
        self.rect.size = self.size[0], self.y_offset
        self.rect.pos = self.pos

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas.before:
            self.rect = Image(pos=self.pos, size=self.size, allow_stretch=True, keep_ratio=False, source=os.path.join(constants.gui_assets, 'footer_background.png'))
            self.rect.color = (constants.background_color[0] - 0.02, constants.background_color[1] - 0.02, constants.background_color[2] - 0.02, 1)

        with self.canvas.after:
            self.canvas.clear()

        self.bind(pos=self.update_rect)
        self.bind(size=self.update_rect)



class AlignLabel(Label):
    def on_size(self, *args):
        self.text_size = self.size



def generate_title(title):
    header = FloatLayout()

    text_layout = BoxLayout()
    text_layout.pos = (0, -8)

    background = HeaderBackground()
    label = AlignLabel(color=(0.2, 0.2, 0.4, 0.8), font_name=os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["very-bold"]}.ttf'), font_size=sp(25), size_hint=(1.0, 1.0), halign="center", valign="top")
    label.text = title
    text_layout.add_widget(label)

    header.add_widget(background)
    header.add_widget(text_layout)
    return header



def footer_label(path, color):

    def fit_to_window(label_widget, path_string, *args):
        x = 1
        text = ""
        shrink_value = round(Window.width / 25)
        if len(path_list) > 2:
            shrink_value -= (len("".join(path_list[2:])))

        for item in path_list:
            if x == 2 and len(item) > shrink_value and len(path_list) > 2:
                item = item[:shrink_value - 4] + f"...{item[-1]}" if (item.endswith("'") or item.endswith("\"")) else item[:shrink_value - 5] + "..."

            text += f'[color={"555599" if x < len(path_list) else color}]' + item + '[/color]'
            if x < len(path_list):
                text += f"[size={round(sp(22))}][font={arrow_font}]  ▸  [/font][/size]"
            x += 1

        label.text = text

    arrow_font = os.path.join(constants.gui_assets, 'fonts', 'DejaVuSans.otf')

    path_list = path.split(', ')
    path_list.insert(0, "       ")

    final_layout = FloatLayout()

    text_layout = BoxLayout()
    text_layout.pos = (20, 12)
    version_layout = BoxLayout()

    version_layout.pos = (-10, 13)

    label = AlignLabel(color=(0.6, 0.6, 1, 0.2), font_name=os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["bold"]}.ttf'), font_size=sp(22), markup=True, size_hint=(1.0, 1.0), halign="left", valign="bottom")
    version = AlignLabel(text=f"auto-mcs[size={round(sp(18))}]  [/size]v{constants.app_version}", color=(0.6, 0.6, 1, 0.2), font_name=os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf'), font_size=sp(23), markup=True, size_hint=(1.0, 1.0), halign="right", valign="bottom")

    text_layout.bind(pos=functools.partial(fit_to_window, label, path_list))
    text_layout.bind(size=functools.partial(fit_to_window, label, path_list))

    text_layout.add_widget(label)
    version_layout.add_widget(version)

    final_layout.add_widget(text_layout)
    final_layout.add_widget(version_layout)

    return final_layout



def generate_footer(menu_path, color="9999FF", progress_screen=False):

    constants.footer_path = " > ".join(menu_path.split(", "))

    footer = FloatLayout()

    if menu_path == 'splash':

        if constants.app_online:
            footer.add_widget(IconButton('connected', {}, (0, 5), (None, None), 'wifi-sharp.png', clickable=False))

            if constants.app_latest:
                footer.add_widget(IconButton('up to date', {}, (51, 5), (None, None), 'checkmark-sharp.png', clickable=False))
            else:
                footer.add_widget(IconButton('update now', {}, (51, 5), (None, None), 'sync.png', clickable=True, force_color=[[(0.05, 0.08, 0.07, 1), (0.5, 0.9, 0.7, 1)], 'green']))

            footer.add_widget(IconButton('view changelog', {}, (102, 5), (None, None), 'document-text-outline.png', clickable=True))

        else:
            footer.add_widget(IconButton('no connection', {}, (0, 5), (None, None), 'ban.png', clickable=True, force_color=[[(0.07, 0.07, 0.07, 1), (0.7, 0.7, 0.7, 1)], 'gray']))

    else:
        footer.add_widget(FooterBackground())
        footer.add_widget(footer_label(path=menu_path, color=color)) # menu_path
        if not progress_screen:
            footer.add_widget(IconButton('main menu', {}, (0, 0), (None, None), 'home-sharp.png', clickable=True))
        else:
            footer.add_widget(AnimButton('please wait...', {}, (0, 0), (None, None), 'loading_pickaxe.gif', clickable=False))

    return footer



def page_counter(index, total, pos):
    layout = FloatLayout()
    label = Label(halign="center")
    label.size_hint = (None, None)
    label.pos_hint = {"center_x": 0.5, "center_y": pos[1] - 0.07}
    label.markup = True
    label.font_name = os.path.join(constants.gui_assets, 'fonts', 'DejaVuSans.otf')
    label.font_size = sp(9)
    label.opacity = 1

    text = ''

    for x in range(0, total):
        if x == index - 1:
            text += f'[color=8B8BF9]{"⬤   " if x + 1 != total else "⬤"}[/color]'
        else:
            text += f'[color=292942]{"⬤   " if x + 1 != total else "⬤"}[/color]'

    label.text = text

    layout.add_widget(label)
    return layout



class PageButton(HoverButton):

    # Execute page swap on click
    def on_touch_down(self, touch):
        if not self.disabled and self.click_function and self.hovered and self.parent.total_pages > 1:
            self.click_function()

        return super().on_touch_down(touch)

    def __init__(self, facing="left", **kwargs):
        super().__init__(**kwargs)

        # Comments for build script;
        # "caret-back-sharp.png"
        # "caret-forward-sharp.png"
        self.icon = os.path.join(constants.gui_assets, 'icons', f'caret-{"back" if facing == "left" else "forward"}-sharp.png')
        self.facing = facing
        self.id = "page_button"
        self.border = (0, 0, 0, 0)
        self.background_normal = self.icon
        self.background_down = self.icon
        self.color_id = [(0.3, 0.3, 0.53, 1), (0.542, 0.577, 0.918, 1), (0.3, 0.3, 0.53, 0.4)]
        self.background_color = self.color_id[0]
        self.disabled = False
        self.click_function = None
        self.original_size = (22, 22)
        self.size_hint_max = (22, 22)
        self.size_offset = 5
        self.pos_hint = {"center_y": 0.5}
        self.original_x = None

    def on_enter(self, *args):
        if not self.ignore_hover and not self.disabled and self.parent.total_pages > 1:
            new_x = (self.x - self.size_offset / 2)
            new_hint = (self.original_size[0] + self.size_offset, self.original_size[1] + self.size_offset)
            Animation(background_color=self.color_id[1], size_hint_max=new_hint, x=new_x, duration=0.11).start(self)

    def on_leave(self, *args):
        if not self.ignore_hover and self.parent.total_pages > 1:
            Animation(background_color=self.color_id[0], size_hint_max=self.original_size, x=self.original_x, duration=0.11).start(self)

class PageSwitcher(RelativeLayout):

    def resize_self(self, *args):
        self.width = len(self.label.text) * 0.74 + 45

        # if not self.left_button.hovered:
        self.left_button.pos = (Window.center[0] - self.width / 2 - self.left_button.width, Window.center[1])
        self.left_button.original_x = self.left_button.x

        # if not self.right_button.hovered:
        self.right_button.pos = (Window.center[0] + self.width / 2, Window.center[1])
        self.right_button.original_x = self.right_button.x


    def update_index(self, index, total):
        text = ''
        self.total_pages = total

        if index > 0 and total > 0:

            for x in range(0, total):
                if x == index - 1:
                    text += f'[color=8B8BF9]{"⬤   " if x + 1 != total else "⬤"}[/color]'
                else:
                    text += f'[color=292942]{"⬤   " if x + 1 != total else "⬤"}[/color]'

            self.label.text = text
            constants.hide_widget(self, False)

            if not (self.left_button.hovered or self.right_button.hovered):
                self.resize_self()

        else:
            constants.hide_widget(self, True)

        # Update button colors if disabled
        Animation(background_color=self.left_button.color_id[(1 if (total > 1 and self.left_button.hovered) else 0 if (total > 1) else 2)], duration=0.2).start(self.left_button)
        Animation(background_color=self.right_button.color_id[(1 if (total > 1 and self.right_button.hovered) else 0 if (total > 1) else 2)], duration=0.2).start(self.right_button)


    def __init__(self, index, total, pos, function, **kwargs):
        super().__init__(**kwargs)

        self.total_pages = 0
        self.size_hint_max_y = 50
        self.pos_hint = {"center_x": 0.5, "center_y": pos[1] - 0.07}

        # Page dots
        self.label = Label(halign="center")
        self.label.size_hint = (None, None)
        self.label.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        self.label.markup = True
        self.label.font_name = os.path.join(constants.gui_assets, 'fonts', 'DejaVuSans.otf')
        self.label.font_size = sp(9)
        self.label.opacity = 1

        # Buttons
        self.left_button = PageButton(facing="left")
        self.left_button.click_function = functools.partial(function, "left")
        self.right_button = PageButton(facing="right")
        self.right_button.click_function = functools.partial(function, "right")

        self.add_widget(self.label)
        self.add_widget(self.left_button)
        self.add_widget(self.right_button)

        self.update_index(index, total)
        self.bind(pos=self.resize_self)
        Clock.schedule_once(self.resize_self, 0)



class ParagraphObject(RelativeLayout):

    def update_rect(self, *args):

        self.rect.source = os.path.join(constants.gui_assets, f'text_input_cover_fade.png')

        self.title.text = self.title_text
        self.rect.width = (len(self.title.text) * 16) + 116 if self.title.text else 0
        if self.width > 500:
            self.rect.width += (self.width - 500)
        self.rect.pos = self.pos[0] + (self.size[0] / 2) - (self.rect.size[0] / 2) - 1, self.pos[1] + 45 + self.height-56
        self.title.pos = self.pos[0] + (self.size[0] / 2) - (self.title.size[0] / 2), self.pos[1] + 4 + self.height-56

        # Background sizes
        body_offset = 29

        self.background_top.width = self.width
        self.background_top.height = body_offset
        self.background_top.x = self.x
        self.background_top.y = self.y + self.height - self.background_top.height

        self.background_bottom.width = self.width
        self.background_bottom.height = 0 - body_offset
        self.background_bottom.x = self.x
        self.background_bottom.y = self.y

        self.background.width = self.width
        self.background.x = self.x
        self.background.y = self.background_bottom.y + abs(self.background_bottom.height) - body_offset
        self.background.height = self.height - abs(self.background_bottom.height) - abs(self.background_top.height) + body_offset

        self.text_content.y = self.background.y - 25
        self.text_content.x = self.x + 25
        self.text_content.size = self.size
        self.text_content.width = self.width

    def __init__(self, font, **kwargs):
        super().__init__(**kwargs)

        self.title_text = "Paragraph"
        self.size_hint = (None, None)
        self.size_hint_max = (None, None)

        with self.canvas.after:
            # Top
            self.background_top = Image(source=os.path.join(constants.gui_assets, "paragraph_edge.png"))
            self.background_top.allow_stretch = True
            self.background_top.keep_ratio = False

            # Body
            self.background = Image(source=os.path.join(constants.gui_assets, "paragraph_background.png"))
            self.background.allow_stretch = True
            self.background.keep_ratio = False

            # Top
            self.background_bottom = Image(source=os.path.join(constants.gui_assets, "paragraph_edge.png"))
            self.background_bottom.allow_stretch = True
            self.background_bottom.keep_ratio = False

            # Title
            self.rect = Image(size=(110, 15), color=constants.background_color, allow_stretch=True, keep_ratio=False)
            self.title = AlignLabel(halign="center", text=self.title_text, color=(0.6, 0.6, 1, 1), font_size=sp(17), font_name=os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["regular"]}.ttf'))
            self.bind(pos=self.update_rect)
            self.bind(size=self.update_rect)

            # Text content
            self.text_content = AlignLabel(halign="left", valign="top", color=(0.65, 0.65, 1, 1), font_name=font if font else os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["regular"]}.ttf'), markup=True)
            self.text_content.line_height = 1.3

def paragraph_object(size, name, content, font_size, font):
    paragraph_obj = ParagraphObject(font)
    paragraph_obj.pos_hint = {"center_x": 0.5} # , "center_y": 0.5
    paragraph_obj.width = size[0]
    paragraph_obj.height = size[1] + 10
    paragraph_obj.title_text = name
    paragraph_obj.text_content.text = content
    paragraph_obj.text_content.font_size = font_size
    return paragraph_obj



# Scroll View Items
class ScrollViewWidget(ScrollView):
    def __init__(self, position=(0.5, 0.52), **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, None)
        self.size = (Window.width, Window.height // 2)
        self.do_scroll_x = False
        self.pos_hint = {"center_x": position[0], "center_y": position[1]}
        self.bar_width = 6
        self.drag_pad = self.bar_width * 15
        self.bar_color = (0.6, 0.6, 1, 1)
        self.bar_inactive_color = (0.6, 0.6, 1, 0.25)
        self.scroll_wheel_distance = dp(55)
        self.scroll_timeout = 250

    # Allow scroll bar to be dragged
    def on_touch_move(self, touch, *args):
        if touch.pos[0] > self.x + (self.width - self.drag_pad):
            try:
                new_scroll = ((touch.pos[1] - self.y) / (self.height - (self.height * (self.vbar[1])))) - (self.vbar[1])
                self.scroll_y = 1 if new_scroll > 1 else 0 if new_scroll < 0 else new_scroll
                return True
            except ZeroDivisionError:
                pass
        return super().on_touch_move(touch)

    def on_touch_down(self, touch, *args):
        if touch.pos[0] > self.x + (self.width - self.drag_pad):
            try:
                new_scroll = ((touch.pos[1] - self.y) / (self.height - (self.height * (self.vbar[1])))) - (self.vbar[1])
                self.scroll_y = 1 if new_scroll > 1 else 0 if new_scroll < 0 else new_scroll
                return True
            except ZeroDivisionError:
                pass
        return super().on_touch_down(touch)

    # def __del__(self):
    #     for widget in self.walk():
    #         self.remove_widget(widget)
    #         del widget
    #
    #     self.clear_widgets()
    #     gc.collect()

class ScrollItem(RelativeLayout):
    def __init__(self, widget=None, **kwargs):
        super().__init__(**kwargs)
        self.height = 85
        self.size_hint_y = None

        if widget:
            self.add_widget(widget)

def scroll_background(pos_hint, pos, size, highlight=False):

    class ScrollBackground(Image):

        def resize(self, *args):
            self.width = Window.width-20

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.allow_stretch = True
            self.keep_ratio = False
            self.size_hint = (None, None)
            self.color = (1, 1, 1, 1) if highlight else constants.background_color
            self.source = os.path.join(constants.gui_assets, 'scroll_gradient.png')
            Window.bind(on_resize=self.resize)

    img = ScrollBackground()
    img.pos = pos
    img.pos_hint = pos_hint
    img.size = size
    img.width = 830

    Clock.schedule_once(img.resize, 0)

    return img


# Recycle View Items
# Scroll View Items
class RecycleViewWidget(RecycleView):
    def __init__(self, position=(0.5, 0.52), view_class=None, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, None)
        self.size = (Window.width, Window.height // 2)
        self.do_scroll_x = False
        if position:
            self.pos_hint = {"center_x": position[0], "center_y": position[1]}
        self.bar_width = 6
        self.drag_pad = self.bar_width * 15
        self.bar_color = (0.6, 0.6, 1, 1)
        self.bar_inactive_color = (0.6, 0.6, 1, 0.25)
        self.scroll_wheel_distance = dp(55)
        Clock.schedule_once(functools.partial(self.assign_viewclass, view_class), 0)


    # Allow scroll bar to be dragged
    def on_touch_move(self, touch, *args):
        if touch.pos[0] > self.x + (self.width - self.drag_pad):
            try:
                new_scroll = ((touch.pos[1] - self.y) / (self.height - (self.height * (self.vbar[1])))) - (self.vbar[1])
                self.scroll_y = 1 if new_scroll > 1 else 0 if new_scroll < 0 else new_scroll
                return True
            except ZeroDivisionError:
                pass
        return super().on_touch_move(touch)

    def on_touch_down(self, touch, *args):
        if touch.pos[0] > self.x + (self.width - self.drag_pad):
            try:
                new_scroll = ((touch.pos[1] - self.y) / (self.height - (self.height * (self.vbar[1])))) - (self.vbar[1])
                self.scroll_y = 1 if new_scroll > 1 else 0 if new_scroll < 0 else new_scroll
                return True
            except ZeroDivisionError:
                pass
        return super().on_touch_down(touch)

    def assign_viewclass(self, view_class, *args):
        self.viewclass = view_class

    # def __del__(self):
    #     for widget in self.walk():
    #         self.remove_widget(widget)
    #         del widget
    #
    #     self.clear_widgets()
    #     gc.collect()



# Banner layout with random ID
class BannerLayout(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.id = constants.gen_rstring(10)

# Notification banner object
class BannerObject(RelativeLayout):

    def resize_self(self, *args):
        self.left_side.x = 0
        self.right_side.x = self.size[0]
        self.middle.x = self.left_side.x + self.left_side.width

        if self.icon:
            self.icon.pos_hint = {"center_y": 0.5}

            if self.icon_side == "left":
                self.icon.x = (self.height - 105) * 0.5

            else:
                self.icon.x = self.width - ((self.height + 95) * 0.5)


    def show_animation(self, show=True, *args):

        # On show
        if show:
            for widget in self.children:

                if widget == self.text_object:
                    text_size = self.text_object.font_size
                    self.text_object.font_size = text_size - 12
                    Animation(font_size=text_size, duration=0.15).start(widget)

                if self.icon:
                    if widget == self.icon:
                        original_size = (self.icon.width, self.icon.height)
                        self.icon.size = (self.icon.width - 9, self.icon.height - 9)
                        Animation(size=original_size, duration=0.2).start(widget)

                Animation(opacity=1, duration=0.3).start(widget)

        # On hide
        else:
            for widget in self.children:

                if widget == self.text_object:
                    Animation(font_size=self.text_object.font_size - 15, duration=0.15).start(widget)

                if self.icon:
                    if widget == self.icon:
                        new_size = (self.icon.width - 6, self.icon.height - 6)
                        Animation(size=new_size, duration=0.2).start(widget)

                Animation(opacity=0, duration=0.3).start(widget)


    def __init__(self, pos_hint={"center_x": 0.5, "center_y": 0.5}, size=(200,50), color=(1,1,1,1), text="", icon=None, icon_side="left", animate=False, **kwargs):
        super().__init__(**kwargs)

        self.size = size
        self.size_hint_max = size
        self.pos_hint = pos_hint
        self.icon_side = icon_side


        # Text
        self.text_object = Label()
        self.text_object.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
        self.text_object.font_size = sp(round(self.height / 1.8))
        self.text_object.color = (0, 0, 0, 0.75)
        self.text_object.markup = True
        if icon:
            self.text_object.text = ("    " + text) if self.icon_side == "left" else (text + "    ")
        else:
            self.text_object.text = "    " + text + "    "

        # Readjust width to fit text if it's too small
        if text:
            new_width = (((len(self.text_object.text) - 4) * (self.text_object.font_size - 8)) / 1.09)

            if new_width > self.width:
                size = (new_width, size[1])
                self.size = size
                self.size_hint_max = size


        # Left side
        self.left_side = Image()
        self.left_side.source = os.path.join(constants.gui_assets, "banner_edge.png")
        self.left_side.color = color
        self.left_side.allow_stretch = True
        self.left_side.keep_ratio = False
        self.left_side.size_hint = (None, None)
        self.left_side.height = size[1]
        self.left_side.width = (size[1] / 2.2)

        # Middle stretched image
        self.middle = Image()
        self.middle.source = os.path.join(constants.gui_assets, "banner_middle.png")
        self.middle.color = color
        self.middle.allow_stretch = True
        self.middle.keep_ratio = False
        self.middle.size_hint = (None, None)
        self.middle.height = size[1]
        self.middle.width = size[0] - ((size[1] / 2.2) * 2)

        # Right side
        self.right_side = Image()
        self.right_side.source = os.path.join(constants.gui_assets, "banner_edge.png")
        self.right_side.color = color
        self.right_side.allow_stretch = True
        self.right_side.keep_ratio = False
        self.right_side.size_hint = (None, None)
        self.right_side.height = size[1]
        self.right_side.width = -(size[1] / 2.2)


        self.add_widget(self.left_side)
        self.add_widget(self.middle)
        self.add_widget(self.right_side)
        self.add_widget(self.text_object)


        # If icon is specified
        if icon:
            self.icon = Image()
            self.icon.source = os.path.join(constants.gui_assets, 'icons', icon)
            self.icon.color = (0, 0, 0, 0.8)
            self.icon.size_hint = (None, None)
            self.icon.allow_stretch = True
            self.icon.height = size[1] / 1.6

            self.add_widget(self.icon)
        else:
            self.icon = None


        self.bind(pos=self.resize_self)
        Clock.schedule_once(self.resize_self, 0)

        if animate:
            for widget in self.children:
                widget.opacity = 0
            Clock.schedule_once(functools.partial(self.show_animation, True), 0)



# ----------------------------------------------------  Buttons  -------------------------------------------------------
def main_button(name, position, icon_name=None, width=None, icon_offset=None, auto_adjust_icon=False, click_func=None):

    def repos_icon(icon_widget, button_widget, *args):

        def resize(*args):
            pos_calc = ((button_widget.width/2 - 35) if button_widget.center[0] > 0 else (-button_widget.width/2 + 35))
            icon_widget.center[0] = button_widget.center[0] + pos_calc

        Clock.schedule_once(resize, 0)

    final = FloatLayout()
    final.id = name

    button = HoverButton()
    button.id = 'main_button'
    button.color_id = [(0.05, 0.05, 0.1, 1), (0.6, 0.6, 1, 1)]

    button.size_hint = (None, None)
    button.size = (dp(450 if not width else width), dp(72))
    button.pos_hint = {"center_x": position[0], "center_y": position[1]}
    button.border = (30, 30, 30, 30)
    button.background_normal = os.path.join(constants.gui_assets, 'main_button.png')
    button.background_down = os.path.join(constants.gui_assets, 'main_button_click.png')

    text = Label()
    text.id = 'text'
    text.size_hint = (None, None)
    text.pos_hint = {"center_x": position[0], "center_y": position[1]}
    text.text = name.upper()
    text.font_size = sp(19)
    text.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["bold"]}.ttf')
    text.color = (0.6, 0.6, 1, 1)


    # Button click behavior
    button.on_release = functools.partial(button_action, name, button)
    final.add_widget(button)

    if icon_name:
        icon = Image()
        icon.id = 'icon'
        icon.source = icon_path(icon_name)
        icon.size = (dp(1), dp(1))
        icon.color = (0.6, 0.6, 1, 1)
        icon.pos_hint = {"center_y": position[1]}
        icon.pos = (icon_offset if icon_offset else -190 if not width else (-190 - (width / 13)), 200)
        final.add_widget(icon)

    final.add_widget(text)

    if auto_adjust_icon and icon_name:
        Clock.schedule_once(functools.partial(repos_icon, icon, button), 0)

    if click_func:
        button.bind(on_press=click_func)

    return final


def color_button(name, position, icon_name=None, width=None, icon_offset=None, auto_adjust_icon=False, click_func=None, color=(1, 1, 1, 1)):

    def repos_icon(icon_widget, button_widget, *args):

        def resize(*args):
            pos_calc = ((button_widget.width/2 - 35) if button_widget.center[0] > 0 else (-button_widget.width/2 + 35))
            icon_widget.center[0] = button_widget.center[0] + pos_calc

        Clock.schedule_once(resize, 0)

    final = FloatLayout()
    final.id = name

    final.button = HoverButton()
    final.button.id = 'color_button'
    final.button.color_id = [constants.brighten_color(color, -0.9), color]

    final.button.size_hint = (None, None)
    final.button.size = (dp(450 if not width else width), dp(72))
    final.button.pos_hint = {"center_x": position[0], "center_y": position[1]}
    final.button.border = (30, 30, 30, 30)
    final.button.background_normal = os.path.join(constants.gui_assets, 'color_button.png')
    final.button.background_down = os.path.join(constants.gui_assets, 'color_button_click.png')
    final.button.background_disabled_normal = os.path.join(constants.gui_assets, 'color_button.png')
    final.button.background_disabled_down = os.path.join(constants.gui_assets, 'color_button_click.png')
    final.button.background_color = final.button.color_id[1]

    text = Label()
    text.id = 'text'
    text.size_hint = (None, None)
    text.pos_hint = {"center_x": position[0], "center_y": position[1]}
    text.text = name.upper()
    text.font_size = sp(19)
    text.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["bold"]}.ttf')
    text.color = final.button.color_id[1]


    # Button click behavior
    final.button.on_release = functools.partial(button_action, name, final.button)
    final.add_widget(final.button)

    if icon_name:
        icon = Image()
        icon.id = 'icon'
        icon.source = icon_path(icon_name)
        icon.size = (dp(1), dp(1))
        icon.color = final.button.color_id[1]
        icon.pos_hint = {"center_y": position[1]}
        icon.pos = (icon_offset if icon_offset else -190 if not width else (-190 - (width / 13)), 200)
        final.add_widget(icon)

    final.add_widget(text)

    if auto_adjust_icon and icon_name:
        Clock.schedule_once(functools.partial(repos_icon, icon, final.button), 0)

    if click_func:
        final.button.bind(on_press=click_func)

    return final


class WaitButton(FloatLayout):

    def repos_icon(self, *args):

        def resize(*args):
            pos_calc = ((self.button.width/2 - 35) if self.button.center[0] > 0 else (-self.button.width/2 + 35))
            self.icon.center[0] = self.button.center[0] + pos_calc
            self.load_icon.center[0] = self.button.center[0] + pos_calc

        Clock.schedule_once(resize, 0)

    def loading(self, boolean_value, *args):
        self.button.on_leave()
        self.disable(boolean_value)
        self.load_icon.color = (0.6, 0.6, 1, 1) if boolean_value else (0.6, 0.6, 1, 0)

    def disable(self, disable=False, animate=True):
        self.button.disabled = disable
        duration = (0.12 if animate else 0)
        Animation(color=(0.6, 0.6, 1, 0.4) if self.button.disabled else (0.6, 0.6, 1, 1), duration=duration).start(self.text)
        Animation(color=(0.6, 0.6, 1, 0) if self.button.disabled else (0.6, 0.6, 1, 1), duration=duration).start(self.icon)

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
        self.button.background_normal = os.path.join(constants.gui_assets, 'main_button.png')
        self.button.background_down = os.path.join(constants.gui_assets, 'main_button_click.png')
        self.button.background_disabled_normal = os.path.join(constants.gui_assets, 'main_button_disabled.png')
        self.button.background_disabled_down = os.path.join(constants.gui_assets, 'main_button_disabled.png')

        self.text = Label()
        self.text.id = 'text'
        self.text.size_hint = (None, None)
        self.text.pos_hint = {"center_x": position[0], "center_y": position[1]}
        self.text.text = name.upper()
        self.text.font_size = sp(19)
        self.text.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["bold"]}.ttf')
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
        self.load_icon.source = os.path.join(constants.gui_assets, 'animations', 'loading_pickaxe.gif')
        self.load_icon.size_hint_max_y = 40
        self.load_icon.color = (0.6, 0.6, 1, 0)
        self.load_icon.pos_hint = {"center_y": position[1]}
        self.load_icon.pos = (icon_offset if icon_offset else -190 if not width else (-190 - (width / 13)), 200)
        self.load_icon.allow_stretch = True
        self.load_icon.anim_delay = 0.02
        self.add_widget(self.load_icon)


        self.add_widget(self.text)

        if auto_adjust_icon and icon_name:
            Clock.schedule_once(self.repos_icon, 0)

        if click_func:
            self.button.bind(on_press=click_func)

        if disabled:
            self.disable(True, False)

        if start_loading:
            self.loading(True)



class IconButton(FloatLayout):

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


    def __init__(self, name, pos_hint, position, size_hint, icon_name=None, clickable=True, force_color=None, anchor='left', click_func=None, text_offset=(0, 0), **kwargs):
        super().__init__(**kwargs)

        self.default_pos = position
        self.anchor = anchor

        self.button = HoverButton()
        self.button.id = 'icon_button'
        self.button.color_id = [(0.05, 0.05, 0.1, 1), (0.6, 0.6, 1, 1)] if not force_color else force_color[0]

        if force_color and force_color[1]:
            self.button.alt_color = "_" + force_color[1]

        self.button.size_hint = size_hint
        self.button.size = (dp(50), dp(50))
        self.button.pos_hint = pos_hint

        if position:
            self.button.pos = (position[0] + 11, position[1])

        self.button.border = (0, 0, 0, 0)
        self.button.background_normal = os.path.join(constants.gui_assets, f'{self.button.id}.png')

        if not force_color or not force_color[1]:
            self.button.background_down = os.path.join(constants.gui_assets, f'{self.button.id}_click.png' if clickable else f'{self.button.id}_hover.png')
        else:
            self.button.background_down = os.path.join(constants.gui_assets, f'{self.button.id}_click_{force_color[1]}.png' if clickable else f'{self.button.id}_hover_{force_color[1]}.png')

        self.text = Label()
        self.text.id = 'text'
        self.text.size_hint = size_hint
        self.text.pos_hint = pos_hint
        self.text.text = name.lower()
        self.text.font_size = sp(19)
        self.text.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
        self.text.color = (0, 0, 0, 0)
        self.text.offset = text_offset

        if position:
            self.text.pos = (position[0] - 10, position[1] + 17)

        if self.text.pos[0] <= 0:
            self.text.pos[0] += sp(len(self.text.text) * 3)

        if self.text.offset[0] != 0 or self.text.offset[1] != 0:
            self.text.pos[0] = self.text.pos[0] - self.text.offset[0]
            self.text.pos[1] = self.text.pos[1] - self.text.offset[1]


        if clickable:
            # Button click behavior
            if click_func:
                self.button.on_release = functools.partial(click_func)
            else:
                self.button.on_release = functools.partial(button_action, name, self.button)


        self.add_widget(self.button)

        if icon_name:
            self.icon = Image()
            self.icon.id = 'icon'
            self.icon.size_hint = size_hint
            self.icon.source = icon_path(icon_name)
            self.icon.size = (dp(72), dp(72))
            self.icon.color = self.button.color_id[1]
            self.icon.pos_hint = pos_hint

            if position:
                self.icon.pos = (position[0], position[1] - 11)

            self.add_widget(self.icon)

        self.add_widget(self.text)

        # Check for right float
        if anchor == "right":
            self.bind(size=self.resize)
            self.bind(pos=self.resize)

class RelativeIconButton(RelativeLayout):

    def __init__(self, name, pos_hint, position, size_hint, icon_name=None, clickable=True, force_color=None, anchor='left', click_func=None, text_offset=(0, 0), **kwargs):
        super().__init__(**kwargs)

        self.default_pos = position
        self.anchor = anchor

        self.button = HoverButton()
        self.button.id = 'icon_button'
        self.button.color_id = [(0.05, 0.05, 0.1, 1), (0.6, 0.6, 1, 1)] if not force_color else force_color[0]

        if force_color and force_color[1]:
            self.button.alt_color = "_" + force_color[1]

        self.button.size_hint = size_hint
        self.button.size = (dp(50), dp(50))
        self.button.pos_hint = pos_hint

        if position:
            self.button.pos = (position[0] + 11, position[1])

        self.button.border = (0, 0, 0, 0)
        self.button.background_normal = os.path.join(constants.gui_assets, f'{self.button.id}.png')

        if not force_color or not force_color[1]:
            self.button.background_down = os.path.join(constants.gui_assets, f'{self.button.id}_click.png' if clickable else f'{self.button.id}_hover.png')
        else:
            self.button.background_down = os.path.join(constants.gui_assets, f'{self.button.id}_click_{force_color[1]}.png' if clickable else f'{self.button.id}_hover_{force_color[1]}.png')

        self.text = Label()
        self.text.id = 'text'
        self.text.size_hint = size_hint
        if pos_hint:
            self.text.pos_hint = pos_hint
        self.text.text = name.lower()
        self.text.font_size = sp(19)
        self.text.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
        self.text.color = (0, 0, 0, 0)
        self.text.offset = text_offset

        if position:
            self.text.pos = (position[0] - 10, position[1] + 17)

        if self.text.pos[0] <= 0:
            self.text.pos[0] += sp(len(self.text.text) * 3)

        self.text.original_pos = self.text.pos

        if self.text.offset[0] != 0 or self.text.offset[1] != 0:
            self.text.pos[0] = self.text.original_pos[0] - self.text.offset[0]
            self.text.pos[1] = self.text.original_pos[1] - self.text.offset[1]


        if clickable:
            # Button click behavior
            if click_func:
                self.button.on_release = functools.partial(click_func)
            else:
                self.button.on_release = functools.partial(button_action, name, self.button)


        self.add_widget(self.button)

        if icon_name:
            self.icon = Image()
            self.icon.id = 'icon'
            self.icon.size_hint = size_hint
            self.icon.source = icon_path(icon_name)
            self.icon.size = (dp(72), dp(72))
            self.icon.color = self.button.color_id[1]
            if pos_hint:
                self.icon.pos_hint = pos_hint

            if position:
                self.icon.pos = (position[0], position[1] - 11)

            self.add_widget(self.icon)

        self.add_widget(self.text)

class AnimButton(FloatLayout):

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

    def __init__(self, name, pos_hint, position, size_hint, icon_name=None, clickable=True, force_color=None, anchor='left', click_func=None, **kwargs):
        super().__init__(**kwargs)

        self.default_pos = position
        self.anchor = anchor

        self.button = HoverButton()
        self.button.id = 'icon_button'
        self.button.color_id = [(0.05, 0.05, 0.1, 1), (0.6, 0.6, 1, 1)] if not force_color else force_color[0]

        if force_color:
            self.button.alt_color = "_" + force_color[1]

        self.button.size_hint = size_hint
        self.button.size = (dp(50), dp(50))
        self.button.pos_hint = pos_hint

        if position:
            self.button.pos = (position[0] + 11, position[1])

        self.button.border = (0, 0, 0, 0)
        self.button.background_normal = os.path.join(constants.gui_assets, f'{self.button.id}.png')

        if not force_color:
            self.button.background_down = os.path.join(constants.gui_assets, f'{self.button.id}_click.png' if clickable else f'{self.button.id}_hover.png')
        else:
            self.button.background_down = os.path.join(constants.gui_assets, f'{self.button.id}_click_{force_color[1]}.png' if clickable else f'{self.button.id}_hover_{force_color[1]}.png')

        self.text = Label()
        self.text.id = 'text'
        self.text.size_hint = size_hint
        self.text.pos_hint = pos_hint
        self.text.text = name.lower()
        self.text.font_size = sp(19)
        self.text.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
        self.text.color = (0, 0, 0, 0)

        if position:
            self.text.pos = (position[0] - 10, position[1] + 17)

        if self.text.pos[0] <= 0:
            self.text.pos[0] += sp(len(self.text.text) * 3)

        if clickable:
            # Button click behavior
            if click_func:
                self.button.on_release = functools.partial(click_func)
            else:
                self.button.on_release = functools.partial(button_action, name, self.button)

        self.add_widget(self.button)

        if icon_name:
            self.icon = AsyncImage()
            self.icon.id = 'icon'
            self.icon.source = os.path.join(constants.gui_assets, 'animations', icon_name)
            self.icon.size_hint_max = (dp(45), dp(45))
            self.icon.color = self.button.color_id[1]
            self.icon.pos_hint = pos_hint
            self.icon.allow_stretch = True
            self.icon.anim_delay = 0.02

            if position:
                self.icon.texture_update()
                self.icon.pos = (self.button.pos[0] + 2.2, self.button.pos[1] + 2.2)

            self.add_widget(self.icon)

        self.add_widget(self.text)

        # Check for right float
        if anchor == "right":
            self.bind(size=self.resize)
            self.bind(pos=self.resize)

class BigIcon(HoverButton):

    def on_click(self):
        for item in self.parent.parent.parent.children:
            for child_item in item.children:
                for child_button in child_item.children:
                    if child_button.id == 'big_icon_button':

                        if child_button.hovered is True:
                            child_button.selected = True
                            child_button.on_enter()
                            child_button.background_down = os.path.join(constants.gui_assets, f'{child_button.id}_selected.png')
                            constants.new_server_info['type'] = child_button.type

                        else:
                            child_button.selected = False
                            for child in [x for x in child_button.parent.children if x.id == "icon"]:
                                if child.type == child_button.type:
                                    child_button.on_leave()
                            child_button.background_normal = os.path.join(constants.gui_assets, f'{child_button.id}.png')
                            child_button.background_down = os.path.join(constants.gui_assets, f'{child_button.id}_click.png')
                            child_button.background_hover = os.path.join(constants.gui_assets, f'{child_button.id}_hover.png')

                        break



def big_icon_button(name, pos_hint, position, size_hint, icon_name=None, clickable=True, force_color=None, selected=False):

    final = FloatLayout()

    button = BigIcon()
    button.selected = selected
    button.id = 'big_icon_button'
    button.color_id = [(0.47, 0.52, 1, 1), (0.6, 0.6, 1, 1)] if not force_color else force_color[0]
    button.type = icon_name

    if force_color:
        button.alt_color = "_" + force_color[1]

    button.size_hint = size_hint
    button.size = (dp(150), dp(150))
    button.pos_hint = pos_hint

    if position:
        button.pos = (position[0] + 11, position[1])

    button.border = (0, 0, 0, 0)
    button.background_normal = os.path.join(constants.gui_assets, f'{button.id}{"_selected" if selected else ""}.png')

    if not force_color:
        if button.selected:
            button.background_down = os.path.join(constants.gui_assets, f'{button.id}_selected.png')
        else:
            button.background_down = os.path.join(constants.gui_assets, f'{button.id}_click.png' if clickable else f'{button.id}_hover.png')
    else:
        button.background_down = os.path.join(constants.gui_assets, f'{button.id}_click_{force_color[1]}.png' if clickable else f'{button.id}_hover_{force_color[1]}.png')

    text = Label()
    text.id = 'text'
    text.size_hint = size_hint
    text.pos_hint = {'center_x': pos_hint['center_x'], 'center_y': pos_hint['center_y'] - 0.11}
    text.text = name.lower()
    text.font_size = sp(19)
    text.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
    text.color = (0, 0, 0, 0)

    if position:
        text.pos = (position[0] - 10, position[1] - 17)

    if text.pos[0] <= 0:
        text.pos[0] += sp(len(text.text) * 3)


    if clickable:
        # Button click behavior
        button.on_release = functools.partial(button.on_click)


    final.add_widget(button)

    if icon_name:
        icon = Image()
        icon.id = 'icon'
        icon.type = button.type
        icon.size_hint = size_hint
        icon.source = icon_path(os.path.join('big', f'{icon_name}.png'))
        icon.size = (dp(125), dp(125))
        icon.color = button.color_id[1] if not selected else (0.05, 0.05, 0.1, 1)
        icon.pos_hint = pos_hint

        if position:
            icon.pos = (position[0], position[1] - 11)

        final.add_widget(icon)

    final.add_widget(text)

    return final



def exit_button(name, position, cycle=False):

    final = FloatLayout()

    button = HoverButton()
    button.id = 'exit_button'
    button.color_id = [(0.1, 0.05, 0.05, 1), (0.6, 0.6, 1, 1)]

    button.size_hint = (None, None)
    button.size = (dp(195), dp(55))
    button.pos_hint = {"center_x": position[0], "center_y": position[1]}
    button.border = (-10, -10, -10, -10)
    button.background_normal = os.path.join(constants.gui_assets, 'exit_button.png')
    button.background_down = os.path.join(constants.gui_assets, 'exit_button_click.png')

    text = Label()
    text.id = 'text'
    text.size_hint = (None, None)
    text.pos_hint = {"center_x": position[0], "center_y": position[1]}
    text.text = name.upper()
    text.font_size = sp(19)
    text.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["bold"]}.ttf')
    text.color = (0.6, 0.6, 1, 1)

    icon = Image()
    icon.id = 'icon'
    icon.source = icon_path('close-circle-outline.png' if name.lower() == "quit" else 'back-outline.png')
    icon.size = (dp(1), dp(1))
    icon.color = (0.6, 0.6, 1, 1)
    icon.pos_hint = {"center_y": position[1]}
    icon.pos = (-70, 200)


    # Button click behavior
    button.on_release = functools.partial(button_action, name, button)


    final.add_widget(button)
    final.add_widget(icon)
    final.add_widget(text)

    return final



class NextButton(HoverButton):

    def disable(self, disable):

        self.disabled = disable
        for item in self.parent.children:
            try:
                if item.id == 'text':
                    Animation(color=(0.6, 0.6, 1, 0.4) if self.disabled else (0.6, 0.6, 1, 1), duration=0.12).start(item)
                elif item.id == 'icon':
                    Animation(color=(0.6, 0.6, 1, 0) if self.disabled else (0.6, 0.6, 1, 1), duration=0.12).start(item)

            except AttributeError:
                pass

    def loading(self, boolean_value):
        self.on_leave()

        for child in self.parent.children:
            if child.id == "load_icon":
                self.disable(boolean_value)
                if boolean_value:
                    child.color = (0.6, 0.6, 1, 1)
                else:
                    child.color = (0.6, 0.6, 1, 0)
                break

    def update_next(self, boolean_value, message):

        if message:
            for child in self.parent.parent.children:
                if "ServerVersionInput" in child.__class__.__name__:
                    child.focus = False
                    child.valid(boolean_value, message)

        self.disable(not boolean_value)

    def on_press(self):
        super().on_press()
        if self.click_func:
            self.click_func()
        for child in self.parent.parent.children:
            if "ServerVersionInput" in child.__class__.__name__:
                # Reset geyser_selected if version is less than 1.13.2
                if constants.version_check(child.text, "<", "1.13.2") or constants.new_server_info['type'] not in ['spigot', 'paper', 'fabric']:
                    constants.new_server_info['server_settings']['geyser_support'] = False

                # Reset gamerule settings if version is less than 1.4.2
                if constants.version_check(child.text, "<", "1.4.2"):
                    constants.new_server_info['server_settings']['keep_inventory'] = False
                    constants.new_server_info['server_settings']['daylight_weather_cycle'] = True
                    constants.new_server_info['server_settings']['command_blocks'] = False
                    constants.new_server_info['server_settings']['random_tick_speed'] = "3"

                # Reset level_type if level type not supported
                if constants.version_check(child.text, "<", "1.1"):
                    constants.new_server_info['server_settings']['level_type'] = "default"
                elif constants.version_check(child.text, "<", "1.3.1") and constants.new_server_info['server_settings']['level_type'] not in ['default', 'flat']:
                    constants.new_server_info['server_settings']['level_type'] = "default"
                elif constants.version_check(child.text, "<", "1.7.2") and constants.new_server_info['server_settings']['level_type'] not in ['default', 'flat', 'large_biomes']:
                    constants.new_server_info['server_settings']['level_type'] = "default"

                # Disable chat reporting
                if constants.version_check(child.text, "<", "1.19") or constants.new_server_info['type'] == "vanilla":
                    constants.new_server_info['server_settings']['disable_chat_reporting'] = False
                else:
                    constants.new_server_info['server_settings']['disable_chat_reporting'] = True

                # Check for potential world incompatibilities
                if constants.new_server_info['server_settings']['world'] != "world":
                    check_world = constants.check_world_version(constants.new_server_info['server_settings']['world'], constants.new_server_info['version'])
                    if not check_world[0] and check_world[1]:
                        constants.new_server_info['server_settings']['world'] = "world"

                child.valid_text(True, True)

            if "Input" in child.__class__.__name__:
                child.focus = False
def next_button(name, position, disabled=False, next_screen="MainMenuScreen", show_load_icon=False, click_func=None):

    final = FloatLayout()

    button = NextButton(disabled=disabled)
    button.id = 'next_button'
    button.color_id = [(0.05, 0.05, 0.1, 1), (0.6, 0.6, 1, 1)]

    button.click_func = click_func
    button.size_hint = (None, None)
    button.size = (dp(240), dp(67))
    button.pos_hint = {"center_x": position[0], "center_y": position[1]}
    button.border = (-25, -25, -25, -25)
    button.background_normal = os.path.join(constants.gui_assets, 'next_button.png')
    button.background_down = os.path.join(constants.gui_assets, 'next_button_click.png')
    button.background_disabled_normal = os.path.join(constants.gui_assets, 'next_button_disabled.png')
    button.background_disabled_down = os.path.join(constants.gui_assets, 'next_button_disabled.png')

    text = Label()
    text.id = 'text'
    text.size_hint = (None, None)
    text.pos_hint = {"center_x": position[0], "center_y": position[1]}
    text.text = name.upper()
    text.font_size = sp(19)
    text.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["bold"]}.ttf')
    text.color = (0.6, 0.6, 1, 0.4) if disabled else (0.6, 0.6, 1, 1)

    # Button click behavior
    if not click_func:
        button.on_release = functools.partial(button_action, name, button, next_screen)

    icon = Image()
    icon.id = 'icon'
    icon.source = icon_path('arrow-forward-circle-outline.png')
    icon.size = (dp(1), dp(1))
    icon.color = (0.6, 0.6, 1, 0) if disabled else (0.6, 0.6, 1, 1)
    icon.pos_hint = {"center_y": position[1]}
    icon.pos = (-90, 200)

    if show_load_icon:
        load_icon = AsyncImage()
        load_icon.id = 'load_icon'
        load_icon.source = os.path.join(constants.gui_assets, 'animations', 'loading_pickaxe.gif')
        load_icon.size_hint_max_y = 40
        load_icon.color = (0.6, 0.6, 1, 0)
        load_icon.pos_hint = {"center_y": position[1]}
        load_icon.pos = (-87, 200)
        load_icon.allow_stretch = True
        load_icon.anim_delay = 0.02
        final.add_widget(load_icon)

    final.add_widget(button)
    final.add_widget(icon)

    final.add_widget(text)

    return final


class HeaderText(FloatLayout):

    def __init__(self, display_text, more_text, position, fixed_x=False, no_line=False, **kwargs):
        super().__init__(**kwargs)

        self.text = Label()
        self.text.id = 'text'
        self.text.size_hint = (None, None)
        self.text.markup = True
        if not fixed_x:
            self.text.pos_hint = {"center_x": 0.5, "center_y": position[1]}
        else:
            self.text.pos_hint = {"center_y": position[1]}
        self.text.text = display_text
        self.text.font_size = sp(23)
        self.text.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
        self.text.color = (0.6, 0.6, 1, 1)

        self.lower_text = Label()
        self.lower_text.id = 'lower_text'
        self.lower_text.size_hint = (None, None)
        self.lower_text.markup = True
        self.lower_text.pos_hint = {"center_x": 0.5, "center_y": position[1] - 0.07}
        self.lower_text.text = more_text
        self.lower_text.font_size = sp(19)
        self.lower_text.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
        self.lower_text.color = (0.6, 0.6, 1, 0.6)

        self.separator = Label(text="_" * 48, pos_hint={"center_y": position[1] - 0.025}, color=(0.6, 0.6, 1, 0.1), font_name=os.path.join(constants.gui_assets, 'fonts', 'LLBI.otf'), font_size=sp(25))
        self.separator.id = 'separator'
        if not no_line:
            self.add_widget(self.separator)
        self.add_widget(self.text)

        if self.lower_text:
            self.add_widget(self.lower_text)



def input_button(name, position, file=(), input_name=None, title=None, ext_list=[], offset=0):

    final = FloatLayout()
    final.x += (190 + offset)

    button = HoverButton()
    button.id = 'input_button'
    button.color_id = [(0.05, 0.05, 0.1, 1), (0.6, 0.6, 1, 1)]

    button.size_hint_max = (151, 58)
    button.pos_hint = {"center_x": position[0], "center_y": position[1]}
    button.border = (0, 0, 0, 0)
    button.background_normal = os.path.join(constants.gui_assets, 'input_button.png')
    button.background_down = os.path.join(constants.gui_assets, 'input_button_click.png')

    text = Label()
    text.id = 'text'
    text.size_hint = (None, None)
    text.pos_hint = {"center_x": position[0], "center_y": position[1]}
    text.text = name.upper()
    text.font_size = sp(17)
    text.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["bold"]}.ttf')
    text.color = (0.6, 0.6, 1, 1)

    # Button click behavior
    if file:
        button.on_release = functools.partial(file_popup, file[0], file[1], ext_list, input_name, title=title)
    else:
        button.on_release = functools.partial(button_action, name, button)

    final.add_widget(button)
    final.add_widget(text)

    return final


# Facing: left, right, center
class DropButton(FloatLayout):

    def __init__(self, name, position, options_list, input_name=None, x_offset=0, facing='left', custom_func=None, change_text=True, **kwargs):
        super().__init__(**kwargs)

        text_padding = 5
        self.facing = facing
        self.options_list = options_list

        self.x += 133 + x_offset

        self.button = HoverButton()
        self.id = self.button.id = 'drop_button' if facing == 'center' else f'drop_button_{self.facing}'
        self.button.color_id = [(0.05, 0.05, 0.1, 1), (0.6, 0.6, 1, 1)]

        self.button.size_hint_max = (182, 58)
        self.button.pos_hint = {"center_x": position[0], "center_y": position[1]}
        self.button.border = (0, 0, 0, 0)
        self.button.background_normal = os.path.join(constants.gui_assets, f'{self.id}.png')
        self.button.background_down = os.path.join(constants.gui_assets, f'{self.id}_click.png')

        # Change background when expanded - A
        def toggle_background(boolean, *args):

            self.button.ignore_hover = boolean

            for child in self.button.parent.children:
                if child.id == 'icon':
                    Animation(height=-abs(child.init_height) if boolean else abs(child.init_height), duration=0.15).start(child)

            if boolean:
                Animation(opacity=1, duration=0.13).start(self.dropdown)
                self.button.background_normal = os.path.join(constants.gui_assets, f'{self.id}_expand.png')
            else:
                self.button.on_mouse_pos(None, Window.mouse_pos)
                if self.button.hovered:
                    self.button.on_enter()
                else:
                    self.button.on_leave()

        self.text = Label()
        self.text.id = 'text'
        self.text.size_hint = (None, None)
        self.text.pos_hint = {"center_x": position[0], "center_y": position[1]}
        self.text.text = name.upper() + (" " * text_padding)
        self.text.font_size = sp(17)
        self.text.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["bold"]}.ttf')
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
                constants.new_server_info['server_settings']['gamemode'] = result
            elif var == 'ServerDiffInput':
                constants.new_server_info['server_settings']['difficulty'] = result
            elif var == 'ServerLevelTypeInput':
                result = result.replace("normal", "default").replace("superflat", "flat").replace("large biomes", "large_biomes")
                constants.new_server_info['server_settings']['level_type'] = result


        self.button.on_release = functools.partial(lambda: self.dropdown.open(self.button))

        if change_text:
            self.dropdown.bind(on_select=lambda instance, x: setattr(self.text, 'text', x.upper() + (" " * text_padding)))

        if custom_func:
            self.dropdown.bind(on_select=lambda instance, x: custom_func(x))
        else:
            self.dropdown.bind(on_select=lambda instance, x: set_var(input_name, x))

        # Change background when expanded - B
        self.button.bind(on_release=functools.partial(toggle_background, True))
        self.dropdown.bind(on_dismiss=functools.partial(toggle_background, False))


        self.add_widget(self.button)
        self.add_widget(self.text)

        # dropdown arrow
        self.icon = Image()
        self.icon.id = 'icon'
        self.icon.source = os.path.join(constants.gui_assets, 'drop_arrow.png')
        self.icon.init_height = 14
        self.icon.size = (14, self.icon.init_height)
        self.icon.allow_stretch = True
        self.icon.keep_ratio = True
        self.icon.size_hint_y = None
        self.icon.color = (0.6, 0.6, 1, 1)
        self.icon.pos_hint = {"center_y": position[1]}
        self.icon.pos = (195 + x_offset, 200)

        self.add_widget(self.icon)


    # Create button in drop-down list
    def list_button(self, sub_name, sub_id):

        sub_final = AnchorLayout()
        sub_final.id = sub_name
        sub_final.size_hint_y = None
        sub_final.height = 42 if "mid" in sub_id else 46

        sub_button = HoverButton()
        sub_button.id = sub_id
        sub_button.color_id = [(0.05, 0.05, 0.1, 1), (0.6, 0.6, 1, 1)]

        sub_button.border = (0, 0, 0, 0)
        sub_button.background_normal = os.path.join(constants.gui_assets, f'{sub_id}.png')
        sub_button.background_down = os.path.join(constants.gui_assets, f'{sub_id}_click.png')

        sub_text = Label()
        sub_text.id = 'text'
        sub_text.text = sub_name
        sub_text.font_size = sp(19)
        sub_text.padding_y = 100
        sub_text.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
        sub_text.color = (0.6, 0.6, 1, 1)

        sub_button.bind(on_release=lambda btn: self.dropdown.select(sub_name))

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


def toggle_button(name, position, default_state=True, x_offset=0, custom_func=None, disabled=False):

    knob_limits = (156.4 + x_offset, 193 + x_offset) # (Left, Right) (156.7 on left, 191 on right with border)
    bgc = constants.background_color
    color_id = [(bgc[0] - 0.021, bgc[1] - 0.021, bgc[2] - 0.021, bgc[3]), (0.6, 0.6, 1, 1)]

    # When switch is toggled
    def on_active(button_name, *args):
        if disabled:
            return

        state = args[0].state == "down"

        for child in args[0].parent.children:
            if child.id == "knob":
                Animation(x=knob_limits[1] if state else knob_limits[0], color=color_id[0] if state else color_id[1], duration=0.12).start(child)
                child.source = os.path.join(constants.gui_assets, f'toggle_button_knob{"_enabled" if state else ""}.png')

        if custom_func:
            custom_func(state)

        # Change settings of ID
        elif button_name == "geyser_support":
            constants.new_server_info['server_settings']['geyser_support'] = state
        elif button_name == 'chat_report':
            constants.new_server_info['server_settings']['disable_chat_reporting'] = state
        elif button_name == "pvp":
            constants.new_server_info['server_settings']['pvp'] = state
        elif button_name == "spawn_protection":
            constants.new_server_info['server_settings']['spawn_protection'] = state
        elif button_name == "keep_inventory":
            constants.new_server_info['server_settings']['keep_inventory'] = state
        elif button_name == "daylight_weather_cycle":
            constants.new_server_info['server_settings']['daylight_weather_cycle'] = state
        elif button_name == "spawn_creatures":
            constants.new_server_info['server_settings']['spawn_creatures'] = state
        elif button_name == "command_blocks":
            constants.new_server_info['server_settings']['command_blocks'] = state


    final = FloatLayout()
    final.x += 174 + x_offset

    button = ToggleButton(state='down' if default_state else 'normal')
    button.id = 'toggle_button'
    button.pos_hint = {"center_x": position[0], "center_y": position[1]}
    button.size_hint_max = (82, 42)
    button.border = (0, 0, 0, 0)
    button.background_normal = os.path.join(constants.gui_assets, 'toggle_button.png')
    button.background_down = button.background_normal if disabled else os.path.join(constants.gui_assets, 'toggle_button_enabled.png')
    button.bind(on_press=functools.partial(on_active, name))

    knob = Image()
    knob.id = 'knob'
    knob.source = os.path.join(constants.gui_assets, f'toggle_button_knob{"_enabled" if default_state else ""}.png')
    knob.size = (30, 30)
    knob.pos_hint = {"center_y": position[1]}
    knob.x = knob_limits[1] if default_state else knob_limits[0]
    knob.color = color_id[0] if default_state else color_id[1]

    if disabled:
        final.opacity = 0.4

    final.add_widget(button)
    final.add_widget(knob)
    return final


class NumberSlider(FloatLayout):

    def on_value(self, *args):
        spos = self.slider.value_pos
        lpos = self.label.size_hint_max
        self.label.pos = (spos[0] - (lpos[0]/2) + 0.7, spos[1] + lpos[1] + 1)

        if self.max_icon or self.min_icon:
            ipos = self.icon_widget.size_hint_max
            self.icon_widget.pos = (spos[0] - (ipos[0] / 2), spos[1] + ipos[1])

        self.slider_val = self.slider.value.__floor__()
        self.label.text = str(self.slider_val)


        if (self.slider_val != self.last_val) or self.init:

            # Show self.icon_widget if maximum or minimum value
            if self.max_icon:
                if (self.slider_val == self.slider.range[1]):
                    self.label.opacity = 0
                    self.icon_widget.opacity = 1
                else:
                    self.label.opacity = 1
                    self.icon_widget.opacity = 0
            elif self.min_icon:
                if (self.slider_val == self.slider.range[0]):
                    self.label.opacity = 0
                    self.icon_widget.opacity = 1
                else:
                    self.label.opacity = 1
                    self.icon_widget.opacity = 0


        self.last_val = self.slider_val
        self.init = False

    def __init__(self, default_value, position, input_name, limits=(0, 100), max_icon=None, min_icon=None, function=None, **kwargs):
        super().__init__(**kwargs)

        self.x += 125
        self.function = function
        self.last_val = default_value
        self.slider_val = default_value
        self.init = True
        self.max_icon = max_icon
        self.min_icon = min_icon

        # Main slider widget
        self.slider = Slider(value=default_value, value_track=True, range=limits)
        self.slider.background_width = 12
        self.slider.border_horizontal = [6, 6, 6, 6]
        self.slider.value_track_width = 5
        self.slider.value_track_color = (0.6, 0.6, 1, 1)
        self.slider.cursor_size = (42, 42)
        self.slider.cursor_image = os.path.join(constants.gui_assets, 'slider_knob.png')
        self.slider.background_horizontal = os.path.join(constants.gui_assets, 'slider_rail.png')
        self.slider.size_hint_max_x = 205
        self.slider.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        self.slider.padding = 30
        self.add_widget(self.slider)

        # Kivy spams this function 3 times because it can't return the touch properly
        def on_touch_up(touch):

            # Execute function with value if it's added
            if self.function and not self.init and touch.button == 'left' and self.slider.parent.collide_point(*touch.pos):
                self.function(self.slider_val)

            return super(type(self.slider), self.slider).on_touch_up(touch)

        self.slider.on_touch_up = on_touch_up

        # Number label
        self.label = AlignLabel()
        self.label.text = str(default_value)
        self.label.halign = "center"
        self.label.valign = "center"
        self.label.size_hint_max = (30, 28)
        self.label.color = (0.15, 0.15, 0.3, 1)
        self.label.font_size = sp(20)
        self.label.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["very-bold"]}.ttf')
        self.add_widget(self.label)

        # Infinity label
        if self.max_icon or self.min_icon:
            self.icon_widget = Image()
            self.icon_widget.size_hint_max = (28, 28)
            self.icon_widget.color = (0.15, 0.15, 0.3, 1)
            self.icon_widget.source = os.path.join(constants.gui_assets, 'icons', self.max_icon if self.max_icon else self.min_icon)
            self.icon_widget.opacity = 0
            self.add_widget(self.icon_widget)
        

        # Bind to number change
        self.slider.bind(value=self.on_value, pos=self.on_value)
        Clock.schedule_once(self.on_value, 0)



# ---------------------------------------------------- Screens ---------------------------------------------------------

# Popup widgets
popup_blur_amount = 7  # Originally 5
class PopupWindow(RelativeLayout):

    def generate_blur_background(self, *args):
        image_path = os.path.join(constants.gui_assets, 'live', 'blur_background.png')
        constants.folder_check(os.path.join(constants.gui_assets, 'live'))

        # Prevent this from running every resize
        def reset_activity(*args):
            self.generating_background = False

        if not self.generating_background:
            self.generating_background = True

            if self.shown:
                for widget in self.window.children:
                    widget.opacity = 0
                self.blur_background.opacity = 0

            screen_manager.current_screen.export_to_png(image_path)
            im = PILImage.open(image_path)
            im1 = im.filter(GaussianBlur(popup_blur_amount))
            im1.save(image_path)
            self.blur_background.reload()

            if self.shown:
                for widget in self.window.children:
                    widget.opacity = 1
                self.blur_background.opacity = 1

            self.resize_window()
            Clock.schedule_once(reset_activity, 0.5)

    # Annoying hack to fix canvas lag
    def resize_window(*args):
        Window.on_resize(*Window.size)


    def click_event(self, *args):
        if not self.clicked:

            rel_coord = (args[1].pos[0] - self.x - self.window.x, args[1].pos[1] - self.y - self.window.y)
            rel_color = self.window_background.color

            # Single, wide button
            if self.ok_button:
                if rel_coord[0] < self.ok_button.width and rel_coord[1] < self.ok_button.height:
                    self.ok_button.background_color = tuple([px + 0.12 if px < 0.88 else px for px in rel_color])
                    self.resize_window()

                    if self.callback:
                        self.callback()
                        self.clicked = True

                    Clock.schedule_once(functools.partial(self.self_destruct, True), 0.1)


            elif self.no_button and self.yes_button:

                # Right button
                if rel_coord[0] > self.no_button.width + 5 and rel_coord[1] < self.yes_button.height:
                    self.yes_button.background_color = tuple([px + 0.12 if px < 0.88 else px for px in rel_color])
                    self.resize_window()

                    if self.callback:
                        callback = self.callback[1]
                        if callback:
                            callback()
                            self.clicked = True

                    Clock.schedule_once(functools.partial(self.self_destruct, True), 0.1)

                # Left button
                elif rel_coord[0] < self.no_button.width - 5 and rel_coord[1] < self.no_button.height:
                    self.no_button.background_color = tuple([px + 0.12 if px < 0.88 else px for px in rel_color])
                    self.resize_window()

                    if self.callback:
                        callback = self.callback[0]
                        if callback:
                            callback()
                            self.clicked = True

                    Clock.schedule_once(functools.partial(self.self_destruct, True), 0.1)


    def resize(self):
        self.window.size = self.window_background.size
        self.window.pos = (Window.size[0]/2 - self.window_background.width/2, Window.size[1]/2 - self.window_background.height/2)
        if self.shown:
            Clock.schedule_once(self.generate_blur_background, 0.1)


    def animate(self, show=True, *args):
        window_func = functools.partial(self.resize_window)
        Clock.schedule_interval(window_func, 0.015)

        def is_shown(*args):
            self.shown = True

        if show:
            for widget in self.window.children:
                original_size = (widget.width, widget.height)
                widget.size = (original_size[0] * 0.8, original_size[1] * 0.8)
                anim = Animation(size=original_size, duration=0.05)
                anim &= Animation(opacity=1, duration=0.25)
                anim.start(widget)
            Animation(opacity=1, duration=0.25).start(self.blur_background)
            Clock.schedule_once(functools.partial(is_shown), 0.5)
        else:
            for widget in self.window.children:
                if "button" in widget.id:
                    widget.opacity = 0

            image_path = os.path.join(constants.gui_assets, 'live', 'popup.png')
            self.window.export_to_png(image_path)

            for widget in self.window.children:
                if widget != self.window_background and "button" not in widget.id:
                    widget.opacity = 0
                else:
                    if widget == self.window_background:
                        widget.color = (1,1,1,1)
                        widget.source = image_path
                        widget.reload()
                    original_size = (widget.width, widget.height)
                    new_size = (original_size[0] * 0.85, original_size[1] * 0.85)
                    anim = Animation(size=new_size, duration=0.08)
                    anim &= Animation(opacity=0, duration=0.25)

                    if "ok_button" in widget.id:
                        widget.opacity = 1
                        original_pos = (widget.pos[0], widget.pos[1] + 28)
                        anim &= Animation(font_size=widget.font_size-3.5, pos=original_pos, duration=0.08)

                    elif "button" in widget.id:
                        widget.opacity = 1
                        original_pos = (widget.pos[0] + (-34.25 if "yes" in widget.id else +34.25 if "no" in widget.id else 0), widget.pos[1] + 28)
                        anim &= Animation(font_size=widget.font_size-3.5, pos=original_pos, duration=0.08)

                    anim.start(widget)

            Animation(opacity=0, duration=0.28).start(self.blur_background)

        Clock.schedule_once(functools.partial(Clock.unschedule, window_func), 0.35)


    # Delete popup bind
    def self_destruct(self, animate, *args):

        def delete(*args):

            try:
                for widget in self.parent.children:
                    if "Popup" in widget.__class__.__name__:
                        self.parent.popup_widget = None
                        self.parent.canvas.after.clear()
                        self.parent.remove_widget(widget)
                        self.canvas.after.clear()
            except AttributeError:
                if constants.debug:
                    print("Window Popup Error: Failed to delete popup as the parent window doesn't exist")

        if animate:
            self.animate(False)
            Clock.schedule_once(delete, 0.36)
        else:
            delete()


    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Popup window layout
        self.window = RelativeLayout()
        self.callback = None
        self.window_sound = None
        self.shown = False
        self.clicked = False

        with self.canvas.after:
            # Blurred background
            self.blur_background = Image()
            self.blur_background.opacity = 0
            self.blur_background.id = "blur_background"
            self.blur_background.source = os.path.join(constants.gui_assets, 'live', 'blur_background.png')
            self.blur_background.allow_stretch = True
            self.blur_background.keep_ratio = False
            self.generating_background = False


            # Popup window background
            self.window_background = Image(source=os.path.join(constants.gui_assets, "popup_background.png"))
            self.window_background.id = "window_background"
            self.window_background.size_hint = (None, None)
            self.window_background.allow_stretch = True
            self.window_background.keep_ratio = False
            self.window_background.color = self.window_color
            self.window_background.size = (460, 360)
            self.window_background.pos_hint = {"center_x": 0.5, "center_y": 0.5}


            # Popup window title
            self.window_icon = Image(source=self.window_icon_path)
            self.window_icon.id = "window_icon"
            self.window_icon.size_hint = (None, None)
            self.window_icon.allow_stretch = True
            self.window_icon.color = self.window_text_color
            self.window_icon.size = (36, 36)
            self.window_icon.pos = (self.window.x + 13, self.window.y + self.window_background.height - 48)

            self.window_title = Label()
            self.window_title.id = "window_title"
            self.window_title.color = self.window_text_color
            self.window_title.font_size = sp(25)
            self.window_title.y = (self.window_background.height / 3 + 30)
            self.window_title.pos_hint = {"center_x": 0.5}
            self.window_title.font_name = os.path.join(constants.gui_assets,'fonts',f'{constants.fonts["italic"]}.ttf')
            self.window_title.text_size[0] = (self.window_background.size[0] * 0.7)
            self.window_title.halign = "center"
            self.window_title.shorten = True
            self.window_title.markup = True
            self.window_title.shorten_from = "right"


            # Popup window content
            self.window_content = Label()
            self.window_content.id = "window_content"
            self.window_content.color = tuple([px * 1.5 if px < 1 else px for px in self.window_text_color])
            self.window_content.font_size = sp(23)
            self.window_content.line_height = 1.15
            self.window_content.halign = "center"
            self.window_content.valign = "center"
            self.window_content.text_size = (self.window_background.width - 40, self.window_background.height - 25)
            self.window_content.pos_hint = {"center_x": 0.5, "center_y": 0.52}
            self.window_content.font_name = os.path.join(constants.gui_assets,'fonts',f'{constants.fonts["bold"]}.ttf')


        self.add_widget(self.blur_background)
        self.window.add_widget(self.window_background)
        self.window.add_widget(self.window_icon)
        self.window.add_widget(self.window_title)
        self.window.add_widget(self.window_content)

# Normal info
class PopupInfo(PopupWindow):
    def __init__(self, **kwargs):
        self.window_color = (0.42, 0.475, 1, 1)
        self.window_text_color = (0.1, 0.1, 0.2, 1)
        self.window_icon_path = os.path.join(constants.gui_assets, 'icons', 'information-circle.png')
        super().__init__(**kwargs)

        # Modal specific settings
        self.window_sound = sa.WaveObject.from_wave_file(os.path.join(constants.gui_assets, 'sounds', 'popup_normal.wav'))
        self.no_button = None
        self.yes_button = None
        with self.canvas.after:
            self.ok_button = Button()
            self.ok_button.id = "ok_button"
            self.ok_button.size_hint = (None, None)
            self.ok_button.size = (459, 65)
            self.ok_button.border = (0, 0, 0, 0)
            self.ok_button.background_color = self.window_color
            self.ok_button.background_normal = os.path.join(constants.gui_assets, "popup_full_button.png")
            self.ok_button.pos_hint = {"center_x": 0.5}
            self.ok_button.text = "OKAY"
            self.ok_button.color = self.window_text_color
            self.ok_button.font_name = os.path.join(constants.gui_assets,'fonts',f'{constants.fonts["very-bold"]}.ttf')
            self.ok_button.font_size = sp(22)
            self.bind(on_touch_down=self.click_event)

        self.window.add_widget(self.ok_button)
        self.canvas.after.clear()

        self.blur_background.opacity = 0
        for widget in self.window.children:
            widget.opacity = 0

# Warning
class PopupWarning(PopupWindow):
    def __init__(self, **kwargs):
        self.window_color = (1, 0.56, 0.6, 1)
        self.window_text_color = (0.2, 0.1, 0.1, 1)
        self.window_icon_path = os.path.join(constants.gui_assets, 'icons', 'alert-circle-sharp.png')
        super().__init__(**kwargs)

        # Modal specific settings
        self.window_sound = sa.WaveObject.from_wave_file(os.path.join(constants.gui_assets, 'sounds', 'popup_warning.wav'))
        self.no_button = None
        self.yes_button = None
        with self.canvas.after:
            self.ok_button = Button()
            self.ok_button.id = "ok_button"
            self.ok_button.size_hint = (None, None)
            self.ok_button.size = (459, 65)
            self.ok_button.border = (0, 0, 0, 0)
            self.ok_button.background_color = self.window_color
            self.ok_button.background_normal = os.path.join(constants.gui_assets, "popup_full_button.png")
            self.ok_button.pos_hint = {"center_x": 0.5}
            self.ok_button.text = "OKAY"
            self.ok_button.color = self.window_text_color
            self.ok_button.font_name = os.path.join(constants.gui_assets,'fonts',f'{constants.fonts["very-bold"]}.ttf')
            self.ok_button.font_size = sp(22)
            self.bind(on_touch_down=self.click_event)

        self.window.add_widget(self.ok_button)
        self.canvas.after.clear()

        self.blur_background.opacity = 0
        for widget in self.window.children:
            widget.opacity = 0

# Yes/No
class PopupQuery(PopupWindow):
    def __init__(self, **kwargs):
        self.window_color = (0.42, 0.475, 1, 1)
        self.window_text_color = (0.1, 0.1, 0.2, 1)
        self.window_icon_path = os.path.join(constants.gui_assets, 'icons', 'question-circle.png')
        super().__init__(**kwargs)

        # Modal specific settings
        self.window_sound = sa.WaveObject.from_wave_file(os.path.join(constants.gui_assets, 'sounds', 'popup_normal.wav'))
        self.ok_button = None
        with self.canvas.after:
            self.no_button = Button()
            self.no_button.id = "no_button"
            self.no_button.size_hint = (None, None)
            self.no_button.size = (229.5, 65)
            self.no_button.border = (0, 0, 0, 0)
            self.no_button.background_color = self.window_color
            self.no_button.background_normal = os.path.join(constants.gui_assets, "popup_half_button.png")
            self.no_button.pos = (0.5, -0.3)
            self.no_button.text = "NO"
            self.no_button.color = self.window_text_color
            self.no_button.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["very-bold"]}.ttf')
            self.no_button.font_size = sp(22)


            self.yes_button = Button()
            self.yes_button.id = "yes_button"
            self.yes_button.size_hint = (None, None)
            self.yes_button.size = (-229.5, 65)
            self.yes_button.border = (0, 0, 0, 0)
            self.yes_button.background_color = self.window_color
            self.yes_button.background_normal = os.path.join(constants.gui_assets, "popup_half_button.png")
            self.yes_button.pos = (self.window_background.size[0] - 0.5, -0.3)
            self.yes_button.text = "YES"
            self.yes_button.color = self.window_text_color
            self.yes_button.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["very-bold"]}.ttf')
            self.yes_button.font_size = sp(22)
            self.bind(on_touch_down=self.click_event)


        self.window.add_widget(self.no_button)
        self.window.add_widget(self.yes_button)
        self.canvas.after.clear()

        self.blur_background.opacity = 0
        for widget in self.window.children:
            widget.opacity = 0

# Yes/No
class PopupWarningQuery(PopupWindow):
    def __init__(self, **kwargs):
        self.window_color = (1, 0.56, 0.6, 1)
        self.window_text_color = (0.2, 0.1, 0.1, 1)
        self.window_icon_path = os.path.join(constants.gui_assets, 'icons', 'question-circle.png')
        super().__init__(**kwargs)

        # Modal specific settings
        self.window_sound = sa.WaveObject.from_wave_file(os.path.join(constants.gui_assets, 'sounds', 'popup_warning.wav'))
        self.ok_button = None
        with self.canvas.after:
            self.no_button = Button()
            self.no_button.id = "no_button"
            self.no_button.size_hint = (None, None)
            self.no_button.size = (229.5, 65)
            self.no_button.border = (0, 0, 0, 0)
            self.no_button.background_color = self.window_color
            self.no_button.background_normal = os.path.join(constants.gui_assets, "popup_half_button.png")
            self.no_button.pos = (0.5, -0.3)
            self.no_button.text = "NO"
            self.no_button.color = self.window_text_color
            self.no_button.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["very-bold"]}.ttf')
            self.no_button.font_size = sp(22)


            self.yes_button = Button()
            self.yes_button.id = "yes_button"
            self.yes_button.size_hint = (None, None)
            self.yes_button.size = (-229.5, 65)
            self.yes_button.border = (0, 0, 0, 0)
            self.yes_button.background_color = self.window_color
            self.yes_button.background_normal = os.path.join(constants.gui_assets, "popup_half_button.png")
            self.yes_button.pos = (self.window_background.size[0] - 0.5, -0.3)
            self.yes_button.text = "YES"
            self.yes_button.color = self.window_text_color
            self.yes_button.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["very-bold"]}.ttf')
            self.yes_button.font_size = sp(22)
            self.bind(on_touch_down=self.click_event)


        self.window.add_widget(self.no_button)
        self.window.add_widget(self.yes_button)
        self.canvas.after.clear()

        self.blur_background.opacity = 0
        for widget in self.window.children:
            widget.opacity = 0


# Big popup widgets
class BigPopupWindow(RelativeLayout):

    def generate_blur_background(self, *args):
        image_path = os.path.join(constants.gui_assets, 'live', 'blur_background.png')
        constants.folder_check(os.path.join(constants.gui_assets, 'live'))

        # Prevent this from running every resize
        def reset_activity(*args):
            self.generating_background = False

        if not self.generating_background:
            self.generating_background = True

            if self.shown:
                for widget in self.window.children:
                    widget.opacity = 0
                self.blur_background.opacity = 0

            screen_manager.current_screen.export_to_png(image_path)
            im = PILImage.open(image_path)
            im1 = im.filter(GaussianBlur(popup_blur_amount))
            im1.save(image_path)
            self.blur_background.reload()

            if self.shown:
                for widget in self.window.children:
                    widget.opacity = 1
                self.blur_background.opacity = 1

            self.resize_window()
            Clock.schedule_once(reset_activity, 0.5)

    # Annoying hack to fix canvas lag
    def resize_window(*args):
        Window.on_resize(*Window.size)


    def click_event(self, *args):

        if not self.clicked:

            rel_coord = (args[1].pos[0] - self.x - self.window.x, args[1].pos[1] - self.y - self.window.y)
            rel_color = self.window_background.color

            # Single, wide button
            if self.ok_button:
                if rel_coord[0] < self.ok_button.width and rel_coord[1] < self.ok_button.height:
                    self.ok_button.background_color = tuple([px + 0.12 if px < 0.88 else px for px in rel_color])
                    self.resize_window()

                    if self.callback:
                        self.callback()
                        self.clicked = True

                    Clock.schedule_once(functools.partial(self.self_destruct, True), 0.1)


            elif self.no_button and self.yes_button:

                # Right button
                if rel_coord[0] > self.no_button.width + 5 and rel_coord[1] < self.yes_button.height:
                    self.yes_button.background_color = tuple([px + 0.12 if px < 0.88 else px for px in rel_color])
                    self.resize_window()

                    if self.callback:
                        callback = self.callback[1]
                        if callback:
                            callback()
                            self.clicked = True

                    Clock.schedule_once(functools.partial(self.self_destruct, True), 0.1)

                # Left button
                elif rel_coord[0] < self.no_button.width - 5 and rel_coord[1] < self.no_button.height:
                    self.no_button.background_color = tuple([px + 0.12 if px < 0.88 else px for px in rel_color])
                    self.resize_window()

                    if self.callback:
                        callback = self.callback[0]
                        if callback:
                            callback()
                            self.clicked = True

                    Clock.schedule_once(functools.partial(self.self_destruct, True), 0.1)


                # Body button if it exists
                elif self.body_button:
                    if (self.body_button.x < rel_coord[0] < self.body_button.x + self.body_button.width) and (self.body_button.y < rel_coord[1] < self.body_button.y + self.body_button.height):
                        Animation.stop_all(self.body_button)
                        self.body_button.background_color = (self.window_text_color[0], self.window_text_color[1], self.window_text_color[2], 0.3)
                        Animation(background_color=self.window_text_color, duration=0.3).start(self.body_button)

                        # Open link in browser
                        if self.addon_object:
                            if self.addon_object.type in ["forge", "fabric"]:
                                url = "https://www.curseforge.com" + self.addon_object.url
                            else:
                                url = "https://dev.bukkit.org" + self.addon_object.url

                            webbrowser.open_new_tab(url)


    def resize(self):
        self.window.size = self.window_background.size
        self.window.pos = (Window.size[0]/2 - self.window_background.width/2, Window.size[1]/2 - self.window_background.height/2)
        if self.shown:
            Clock.schedule_once(self.generate_blur_background, 0.1)


    def animate(self, show=True, *args):
        window_func = functools.partial(self.resize_window)
        Clock.schedule_interval(window_func, 0.015)

        def is_shown(*args):
            self.shown = True

        if show:
            for widget in self.window.children:
                original_size = (widget.width, widget.height)
                widget.size = (original_size[0] * 0.8, original_size[1] * 0.8)
                anim = Animation(size=original_size, duration=0.05)
                anim &= Animation(opacity=1, duration=0.25)
                anim.start(widget)
            Animation(opacity=1, duration=0.25).start(self.blur_background)
            Clock.schedule_once(functools.partial(is_shown), 0.5)
        else:
            for widget in self.window.children:
                if "button" in widget.id:
                    widget.opacity = 0

            image_path = os.path.join(constants.gui_assets, 'live', 'popup.png')
            self.window.export_to_png(image_path)

            for widget in self.window.children:
                if widget != self.window_background and "button" not in widget.id:
                    widget.opacity = 0
                else:
                    if widget == self.window_background:
                        widget.color = (1,1,1,1)
                        widget.source = image_path
                        widget.reload()
                    original_size = (widget.width, widget.height)
                    new_size = (original_size[0] * 0.85, original_size[1] * 0.85)
                    anim = Animation(size=new_size, duration=0.08)
                    anim &= Animation(opacity=0, duration=0.25)

                    if widget.id == "body_button":
                        widget.opacity = 1
                        original_pos = (widget.pos[0] + 13, widget.pos[1] + 45)
                        anim &= Animation(font_size=widget.font_size-3.5, pos=original_pos, duration=0.08)

                    elif "ok_button" in widget.id:
                        widget.opacity = 1
                        original_pos = (widget.pos[0], widget.pos[1] + 49.25)
                        anim &= Animation(font_size=widget.font_size-3.5, pos=original_pos, duration=0.08)

                    elif "button" in widget.id:
                        widget.opacity = 1
                        original_pos = (widget.pos[0] + (-49.25 if widget.id.replace("_button", "") in ["yes", "install"] else +49.25 if "no" in widget.id else 0), widget.pos[1] + 48)
                        anim &= Animation(font_size=widget.font_size-3.5, pos=original_pos, duration=0.08)

                    anim.start(widget)

            Animation(opacity=0, duration=0.28).start(self.blur_background)

        Clock.schedule_once(functools.partial(Clock.unschedule, window_func), 0.35)


    # Delete popup bind
    def self_destruct(self, animate, *args):

        def delete(*args):

            try:
                for widget in self.parent.children:
                    if "Popup" in widget.__class__.__name__:
                        self.parent.popup_widget = None
                        self.parent.canvas.after.clear()
                        self.parent.remove_widget(widget)
                        self.canvas.after.clear()
            except AttributeError:
                if constants.debug:
                    print("Window Popup Error: Failed to delete popup as the parent window doesn't exist")

        if animate:
            self.animate(False)
            Clock.schedule_once(delete, 0.36)
        else:
            delete()


    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Popup window layout
        self.window = RelativeLayout()
        self.callback = None
        self.window_sound = None
        self.shown = False
        self.clicked = False

        with self.canvas.after:
            # Blurred background
            self.blur_background = Image()
            self.blur_background.opacity = 0
            self.blur_background.id = "blur_background"
            self.blur_background.source = os.path.join(constants.gui_assets, 'live', 'blur_background.png')
            self.blur_background.allow_stretch = True
            self.blur_background.keep_ratio = False
            self.generating_background = False


            # Popup window background
            self.window_background = Image(source=os.path.join(constants.gui_assets, "big_popup_background.png"))
            self.window_background.id = "window_background"
            self.window_background.size_hint = (None, None)
            self.window_background.allow_stretch = True
            self.window_background.keep_ratio = False
            self.window_background.color = self.window_color
            self.window_background.size = (650, 650)
            self.window_background.pos_hint = {"center_x": 0.5, "center_y": 0.5}


            # Popup window title
            self.window_icon = Image(source=self.window_icon_path)
            self.window_icon.id = "window_icon"
            self.window_icon.size_hint = (None, None)
            self.window_icon.allow_stretch = True
            self.window_icon.color = self.window_text_color
            self.window_icon.size = (32, 32)
            self.window_icon.pos = (self.window.x + 20, self.window.y + self.window_background.height - 44.5)

            self.window_title = Label()
            self.window_title.id = "window_title"
            self.window_title.color = self.window_text_color
            self.window_title.font_size = sp(25)
            self.window_title.y = (self.window_background.height / 3 + 80)
            self.window_title.pos_hint = {"center_x": 0.5}
            self.window_title.font_name = os.path.join(constants.gui_assets,'fonts',f'{constants.fonts["italic"]}.ttf')


            # Popup window content
            self.window_content = Label()
            self.window_content.id = "window_content"
            self.window_content.color = tuple([px * 1.5 if px < 1 else px for px in self.window_text_color])
            self.window_content.font_size = sp(23)
            self.window_content.line_height = 1.15
            self.window_content.halign = "center"
            self.window_content.valign = "center"
            self.window_content.text_size = (self.window_background.width - 40, self.window_background.height - 25)
            self.window_content.pos_hint = {"center_x": 0.5, "center_y": 0.52}
            self.window_content.font_name = os.path.join(constants.gui_assets,'fonts',f'{constants.fonts["bold"]}.ttf')


        self.add_widget(self.blur_background)
        self.window.add_widget(self.window_background)
        self.window.add_widget(self.window_icon)
        self.window.add_widget(self.window_title)
        self.window.add_widget(self.window_content)

# Controls popup for biggg stuff
class PopupControls(BigPopupWindow):
    def __init__(self, **kwargs):
        self.window_color = (0.42, 0.475, 1, 1)
        self.window_text_color = (0.1, 0.1, 0.2, 1)
        self.window_icon_path = os.path.join(constants.gui_assets, 'icons', 'information-circle.png')
        super().__init__(**kwargs)

        # Modal specific settings
        self.window_sound = None
        self.no_button = None
        self.yes_button = None
        with self.canvas.after:
            self.ok_button = Button()
            self.ok_button.id = "ok_button"
            self.ok_button.size_hint = (None, None)
            self.ok_button.size = (650.6, 65)
            self.ok_button.border = (0, 0, 0, 0)
            self.ok_button.background_color = self.window_color
            self.ok_button.background_normal = os.path.join(constants.gui_assets, "big_popup_full_button.png")
            self.ok_button.pos_hint = {"center_x": 0.5006}
            self.ok_button.text = "OKAY"
            self.ok_button.color = self.window_text_color
            self.ok_button.font_name = os.path.join(constants.gui_assets,'fonts',f'{constants.fonts["very-bold"]}.ttf')
            self.ok_button.font_size = sp(22)
            self.bind(on_touch_down=self.click_event)

        self.window.add_widget(self.ok_button)
        self.canvas.after.clear()

        self.blur_background.opacity = 0
        for widget in self.window.children:
            widget.opacity = 0

# Addon popup
class PopupAddon(BigPopupWindow):
    def __init__(self, addon_object=None, **kwargs):
        self.window_color = (0.42, 0.475, 1, 1)
        self.window_text_color = (0.1, 0.1, 0.2, 1)
        self.window_icon_path = os.path.join(constants.gui_assets, 'icons', 'extension-puzzle-sharp.png')
        self.installed = False

        # Assign addon info to popup
        if addon_object:
            if addon_object.__class__.__name__ == "partial":
                addon_info = addon_object()
                self.addon_object = addon_info[0]
                self.installed = addon_info[1]
        else:
            self.addon_object = None

        # If addon is unavailable, show info
        if not self.addon_object:
            del self
            return


        super().__init__(**kwargs)


        # Title
        self.window_title.text_size[0] = (self.window_background.size[0] * 0.7)
        self.window_title.halign = "center"
        self.window_title.shorten = True
        self.window_title.markup = True
        self.window_title.shorten_from = "right"
        self.window_title.text = f"{self.addon_object.name}  [color=#3E4691]-[/color]  {self.addon_object.author if self.addon_object.author else 'Unknown'}"


        # Description
        self.window_content.text = "" if not addon_object else self.addon_object.description
        if not self.window_content.text.strip():
            self.window_content.text = "description unavailable"
        else:
            self.window_content.halign = "left"
            self.window_content.valign = "top"
            self.window_content.pos_hint = {"center_x": 0.5, "center_y": 0.4}
        self.window_content.max_lines = 14 # Cuts off the beginning of content??


        # Modal specific settings
        self.window_sound = None
        self.ok_button = None
        with self.canvas.after:

            # Body Button (Open in browser)
            self.body_button = Button()
            self.body_button.id = "body_button"
            self.body_button.size_hint = (None, None)
            self.body_button.size = (200, 40)
            self.body_button.border = (0, 0, 0, 0)
            self.body_button.background_color = self.window_text_color
            self.body_button.background_normal = os.path.join(constants.gui_assets, "addon_view_button.png")
            self.body_button.pos = ((self.window_background.size[0] / 2) - (self.body_button.size[0] / 2), 77)
            self.body_button.text = "click to view more"
            self.body_button.color = self.window_color
            self.body_button.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
            self.body_button.font_size = sp(20)



            self.no_button = Button()
            self.no_button.id = "no_button"
            self.no_button.size_hint = (None, None)
            self.no_button.size = (327, 65)
            self.no_button.border = (0, 0, 0, 0)
            self.no_button.background_color = self.window_color
            self.no_button.background_normal = os.path.join(constants.gui_assets, "big_popup_half_button.png")
            self.no_button.pos = (0, -0.3)
            self.no_button.text = "BACK"
            self.no_button.color = self.window_text_color
            self.no_button.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["very-bold"]}.ttf')
            self.no_button.font_size = sp(22)

            self.yes_button = Button()
            self.yes_button.id = "install_button"
            self.yes_button.size_hint = (None, None)
            self.yes_button.size = (-327, 65)
            self.yes_button.border = (0, 0, 0, 0)
            self.yes_button.background_color = self.window_color
            self.yes_button.background_normal = os.path.join(constants.gui_assets, "big_popup_half_button.png")
            self.yes_button.pos = (self.window_background.size[0] + 1, -0.3)
            self.yes_button.text = "INSTALL" if not self.installed else "UNINSTALL"
            self.yes_button.color = self.window_text_color
            self.yes_button.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["very-bold"]}.ttf')
            self.yes_button.font_size = sp(22)


            # Version Banner
            addon_supported = False
            if not self.addon_object.versions:
                addon_versions = "None"

            elif len(self.addon_object.versions) == 1:
                addon_versions = self.addon_object.versions[0]

            else:
                addon_versions = f"{self.addon_object.versions[-1]}-{self.addon_object.versions[0]}"

            if screen_manager.current_screen.name == "CreateServerAddonSearchScreen":
                server_version = constants.new_server_info['version']
            else:
                server_version = constants.server_manager.current_server.version

            if self.addon_object.versions:
                addon_supported = constants.version_check(server_version, ">=", self.addon_object.versions[-1]) and constants.version_check(server_version, "<=", self.addon_object.versions[0])

            version_text = f"{'Supported' if addon_supported else 'Unsupported'}:  {addon_versions}"

            self.version_banner = BannerObject(
                pos_hint = {"center_x": (0.5 if not self.installed else 0.36), "center_y": 0.877},
                size = (250, 40),
                color = (0.4, 0.682, 1, 1) if addon_supported else (1, 0.53, 0.58, 1),
                text = version_text,
                icon = "information-circle.png"
            )
            self.version_banner.id = "version_banner"


            # Installed banner
            if self.installed:
                self.installed_banner = BannerObject(
                    pos_hint = {"center_x": 0.74, "center_y": 0.877},
                    size = (150, 40),
                    color = (0.553, 0.902, 0.675, 1),
                    text = "installed",
                    icon = "checkmark-circle.png",
                    icon_side = "right"
                )
                self.installed_banner.id = "installed_banner"



        self.window.add_widget(self.no_button)
        self.window.add_widget(self.yes_button)
        self.window.add_widget(self.body_button)
        self.window.add_widget(self.version_banner)
        if self.installed:
            self.window.add_widget(self.installed_banner)

        self.bind(on_touch_down=self.click_event)

        self.canvas.after.clear()

        self.blur_background.opacity = 0
        for widget in self.window.children:
            widget.opacity = 0




# Screen widgets
def previous_screen(*args):
    screen_manager.current = constants.screen_tree.pop(-1)
    # print(constants.screen_tree)



# Call function when any button is pressed
def button_action(button_name, button, specific_screen=''):

    # print(button_name)
    # print(button.button_pressed)

    if button.button_pressed == "left":

        if button_name.lower() == "quit":
            sys.exit()
        elif button_name.lower() == "back":
            constants.back_clicked = True
            previous_screen()
            constants.back_clicked = False

        elif "manage" in button_name.lower() and "servers" in button_name.lower():
            screen_manager.current = "ServerManagerScreen"

        # Return to main menu, prompt user if inside of progressive function
        elif "main menu" in button_name.lower():
            def return_to_main(*argies):
                screen_manager.current = 'MainMenuScreen'

            # Warn user if creating server, or updating server etc...
            if "CreateServer" in str(screen_manager.current_screen) or "ServerImport" in str(screen_manager.current_screen):
                screen_manager.current_screen.show_popup(
                    "query",
                    "Main Menu",
                    "Would you like to return to the main menu?\n\nYour progress will not be saved",
                    [None, functools.partial(Clock.schedule_once, return_to_main, 0.25)])
            else:
                return_to_main()

        elif "create a new server" in button_name.lower():
            constants.new_server_init()
            screen_manager.current = 'CreateServerNameScreen'

        elif "import a server" in button_name.lower():
            constants.new_server_init()
            screen_manager.current = 'ServerImportScreen'

        elif "create new world instead" in button_name.lower():
            break_loop = False
            for item in screen_manager.current_screen.children:
                if item.id == 'content':
                    for child_item in item.children:
                        if break_loop:
                            break
                        if child_item.__class__.__name__ == 'ServerWorldInput':
                            child_item.selected_world = constants.new_server_info['server_settings']['world'] = 'world'
                            child_item.update_world(force_ignore=True)

        # Different behavior depending on the page
        elif "next" in button_name.lower() and not button.disabled:

            def change_screen(name, *args, **kwargs):
                screen_manager.current = name

            if screen_manager.current == 'CreateServerVersionScreen':

                def check_version(*args, **kwargs):
                    break_loop = False
                    for item in screen_manager.current_screen.children:
                        if break_loop:
                            break
                        for child_item in item.children:
                            if break_loop:
                                break
                            for child in child_item.children:

                                if child.__class__.__name__ == "NextButton":

                                    child.loading(True)
                                    version_data = constants.search_version(constants.new_server_info)
                                    constants.new_server_info['version'] = version_data[1]['version']
                                    constants.new_server_info['build'] = version_data[1]['build']
                                    constants.new_server_info['jar_link'] = version_data[3]
                                    child.loading(False)
                                    child.update_next(version_data[0], version_data[2])

                                    # Continue to next screen if valid input, and back button not pressed
                                    if version_data[0] and not version_data[2] and screen_manager.current == 'CreateServerVersionScreen':
                                        Clock.schedule_once(functools.partial(change_screen, specific_screen), 0)

                                    break_loop = True
                                    break

                timer = threading.Timer(0, function=check_version)
                timer.start()  # Checks for potential crash

            elif screen_manager.current == 'CreateServerOptionsScreen':
                if not constants.new_server_info['acl_object']:
                    while not constants.new_server_info['acl_object']:
                        time.sleep(0.2)
                change_screen(specific_screen)

            else:
                change_screen(specific_screen)

            print(constants.new_server_info)

        # Main menu reconnect button
        elif "no connection" in button_name.lower():
            try:
                constants.check_app_updates()
                constants.find_latest_mc()
            except:
                pass
            screen_manager.current_screen.reload_menu()


        elif "CreateServerNetwork" in str(screen_manager.current_screen):
            if "access control manager" in button_name.lower():
                if not constants.new_server_info['acl_object']:
                    while not constants.new_server_info['acl_object']:
                        time.sleep(0.2)
                screen_manager.current = 'CreateServerAclScreen'


        elif "add rules" in button_name.lower() and "CreateServerAclScreen" in str(screen_manager.current_screen):
            screen_manager.current = 'CreateServerAclRuleScreen'

        elif "add rules" in button_name.lower() and "ServerAclScreen" in str(screen_manager.current_screen):
            screen_manager.current = 'ServerAclRuleScreen'

        elif "add rules" in button_name.lower() and "ServerAclRuleScreen" in str(screen_manager.current_screen):
            screen_manager.current_screen.apply_rules()


        elif "CreateServerOptions" in str(screen_manager.current_screen) or "CreateServerAddon" in str(screen_manager.current_screen):

            # If creating a new server, use CreateServerAddonScreen
            if "add-on manager" in button_name.lower():
                screen_manager.current = 'CreateServerAddonScreen'

            elif "download" in button_name.lower():
                screen_manager.current = 'CreateServerAddonSearchScreen'

            elif "import" in button_name.lower():
                title = "Select Add-on Files (.jar)"
                selection = file_popup("file", start_dir=constants.userDownloads, ext=["*.jar"], input_name=None, select_multiple=True, title=title)

                if selection:
                    banner_text = ''
                    for addon in selection:
                        if addon.endswith(".jar") and os.path.isfile(addon):
                            addon = addons.get_addon_file(addon, constants.new_server_info)
                            constants.new_server_info['addon_objects'].append(addon)
                            screen_manager.current_screen.gen_search_results(constants.new_server_info['addon_objects'])

                            # Switch pages if page is full
                            if (len(screen_manager.current_screen.scroll_layout.children) == 0) and (len(constants.new_server_info['addon_objects']) > 0):
                                screen_manager.current_screen.switch_page("right")

                            # Show banner
                            if len(selection) == 1:
                                if len(addon.name) < 26:
                                    addon_name = addon.name
                                else:
                                    addon_name = addon.name[:23] + "..."

                                banner_text = f"Added '{addon_name}' to the queue"
                            else:
                                banner_text = f"Added {len(selection)} add-ons to the queue"

                    if banner_text:
                        Clock.schedule_once(
                            functools.partial(
                                screen_manager.current_screen.show_banner,
                                (0.553, 0.902, 0.675, 1),
                                banner_text,
                                "add-circle-sharp.png",
                                2.5,
                                {"center_x": 0.5, "center_y": 0.965}
                            ), 0
                        )


        elif "ServerAddonScreen" in str(screen_manager.current_screen):
            addon_manager = constants.server_manager.current_server.addon

            if "download" in button_name.lower():
                screen_manager.current = 'ServerAddonSearchScreen'

            elif "import" in button_name.lower():
                title = "Select Add-on Files (.jar)"
                selection = file_popup("file", start_dir=constants.userDownloads, ext=["*.jar"], input_name=None, select_multiple=True, title=title)

                if selection:
                    banner_text = ''
                    for addon in selection:
                        if addon.endswith(".jar") and os.path.isfile(addon):
                            addon = addon_manager.import_addon(addon)
                            addon_list = addon_manager.return_single_list()
                            screen_manager.current_screen.gen_search_results(addon_manager.return_single_list(), fade_in=False, highlight=addon.hash, animate_scroll=True)

                            # Switch pages if page is full
                            if (len(screen_manager.current_screen.scroll_layout.children) == 0) and (len(addon_list) > 0):
                                screen_manager.current_screen.switch_page("right")

                            # Show banner
                            if len(selection) == 1:
                                if len(addon.name) < 26:
                                    addon_name = addon.name
                                else:
                                    addon_name = addon.name[:23] + "..."

                                banner_text = f"Imported '{addon_name}'"
                            else:
                                banner_text = f"Imported {len(selection)} add-ons"

                    if banner_text:

                        # Show banner if server is running
                        if addon_manager.hash_changed():
                            Clock.schedule_once(
                                functools.partial(
                                    screen_manager.current_screen.show_banner,
                                    (0.937, 0.831, 0.62, 1),
                                    f"A server restart is required to apply changes",
                                    "sync.png",
                                    3,
                                    {"center_x": 0.5, "center_y": 0.965}
                                ), 0.25
                            )

                        else:
                            Clock.schedule_once(
                                functools.partial(
                                    screen_manager.current_screen.show_banner,
                                    (0.553, 0.902, 0.675, 1),
                                    banner_text,
                                    "add-circle-sharp.png",
                                    2.5,
                                    {"center_x": 0.5, "center_y": 0.965}
                                ), 0
                            )


        elif "ServerBackupScreen" in str(screen_manager.current_screen) and "restore" in button_name.lower():
            screen_manager.current = "ServerBackupRestoreScreen"


        elif "CreateServerReview" in str(screen_manager.current_screen) and "create server" in button_name.lower():
            screen_manager.current = "CreateServerProgressScreen"




# =============================================== Screen Templates =====================================================
# <editor-fold desc="Screen Templates">

# Template for any screen
class MenuBackground(Screen):

    reload_page = True

    def on_pre_leave(self, *args):
        super().on_pre_leave()
        if not constants.back_clicked and not self._ignore_tree:
            constants.screen_tree.append(self.__class__.__name__)

        # Close keyboard listener on current screen
        if self._keyboard:
            self._keyboard_closed()

    # Reset page on screen load
    def on_pre_enter(self, *args):
        if self.reload_page and constants.app_loaded:
            self.reload_menu()

            # Remove popup
            if self.popup_widget:
                self.popup_widget.self_destruct(self, False)
                self.popup_widget = None
                self.canvas.after.clear()

            # Add global banner object if one exists
            def revive_banner(*args):
                if constants.global_banner:
                    if constants.global_banner.parent:
                        constants.global_banner.parent.remove_widget(constants.global_banner)
                self.banner_widget = constants.global_banner if constants.global_banner else BannerLayout()
                self.add_widget(self.banner_widget)

            Clock.schedule_once(revive_banner, 0.12)

        # Keyboard yumminess
        self._input_focused = False
        self._keyboard = Window.request_keyboard(None, self, 'text')
        self._keyboard.bind(on_key_down=self._on_keyboard_down)


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
        # gc.collect()


    def reload_menu(self, *args):
        self.clear_widgets()
        self.generate_menu()


    def generate_menu(self, *args):
        pass

    # Fit background color across screen for transitions
    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

        # Resize popup if it exists
        if self.popup_widget:
            self.popup_widget.resize()

        # Repos page switcher
        if self.page_switcher:
            self.page_switcher.resize_self()

    # Ignore touch events when popup is present
    def on_touch_down(self, touch):
        if self.popup_widget:
            if self.popup_widget.window.collide_point(*touch.pos):
                return super().on_touch_down(touch)
            else:
                return
        else:
            return super().on_touch_down(touch)

    # Show popup; popup_type can be "info", "warning", "query"
    def show_popup(self, popup_type, title, content, callback=None, *args):
        if title and content and popup_type in ["info", "warning", "query", "warning_query", "controls", "addon"] and (self == screen_manager.current_screen):

            # self.show_popup("info", "Title", "This is an info popup!", functools.partial(callback_func))
            # self.show_popup("warning", "Title", "This is a warning popup!", functools.partial(callback_func))
            # self.show_popup("query", "Title", "Yes or no?", (functools.partial(callback_func_no), functools.partial(callback_func_yes)))
            # self.show_popup("warning_query", "Title", "Yes or no?", (functools.partial(callback_func_no), functools.partial(callback_func_yes)))
            # self.show_popup("controls", "Title", "Press X to do Y", functools.partial(callback_func))
            # self.show_popup("addon", "Title", "Description", (functools.partial(callback_func_web), functools.partial(callback_func_install)), addon_object)

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
                    try:
                        self.popup_widget.window_content
                    except AttributeError:
                        title = args[0].args[0].name[0:30]
                        content = "There is no data available for this add-on"
                        callback = None
                        self.popup_widget = PopupWarning()

            self.popup_widget.generate_blur_background()

            if title.strip():
                self.popup_widget.window_title.text = title

            if content.strip():
                self.popup_widget.window_content.text = content

            self.popup_widget.callback = callback

            def show(*argies):
                self.add_widget(self.popup_widget)
                self.popup_widget.resize()
                self.popup_widget.animate(True)

            if self.popup_widget.window_sound:
                # Fix popping sound when sounds are played
                try:
                    self.popup_widget.window_sound.play()
                except:
                    pass
            Clock.schedule_once(show, 0.3)

    # Show banner; pass in color, text, icon name, and duration
    @staticmethod
    def show_banner(color, text, icon, duration=5, pos_hint={"center_x": 0.5, "center_y": 0.895}, *args):

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
        banner_shadow.source = os.path.join(constants.gui_assets, 'banner_shadow.png')
        banner_shadow.keep_ratio = False
        banner_shadow.allow_stretch = True
        banner_shadow.size_hint_max = (banner_size[0] + 150, banner_size[1] * 2)
        banner_shadow.pos_hint = pos_hint
        banner_shadow.opacity = 0
        Animation(opacity=1, duration=0.5).start(banner_shadow)

        # Banner progress bar
        banner_progress_bar = Image()
        banner_progress_bar.source = os.path.join(constants.gui_assets, 'banner_progress_bar.png')
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
        if constants.global_banner:
            if constants.global_banner.parent:
                constants.hide_widget(constants.global_banner)
                constants.global_banner.parent.remove_widget(constants.global_banner)

        screen_manager.current_screen.banner_widget = banner_layout
        constants.global_banner = banner_layout

        screen_manager.current_screen.add_widget(screen_manager.current_screen.banner_widget)

        # Deletes banner object after duration
        def hide_banner(widget, *args):

            if constants.global_banner.id == widget.id:

                if constants.global_banner:
                    if constants.global_banner.parent:
                        constants.global_banner.parent.remove_widget(constants.global_banner)

                constants.global_banner = None
                for screen in screen_manager.children:
                    screen.banner_widget = None

        def hide_widgets(shadow, progress_bar, *args):
            Animation(opacity=0, duration=0.5).start(shadow)
            Animation(opacity=0, duration=0.1).start(progress_bar)


        Clock.schedule_once(functools.partial(banner_object.show_animation, False), duration)
        Clock.schedule_once(functools.partial(hide_widgets, banner_shadow, banner_progress_bar), duration)
        Clock.schedule_once(functools.partial(hide_banner, banner_layout), duration + 0.32)


    # Keyboard listeners
    def _keyboard_closed(self):
        # print('Keyboard has been closed')
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        # print('The key', keycode, 'have been pressed')
        # print(' - text is %r' % text)
        # print(' - modifiers are %r' % modifiers)

        # Ignore key presses when popup is visible
        if self.popup_widget:
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

        # Ignore ESC commands while input focused
        if not self._input_focused and self.name == screen_manager.current_screen.name:

            # Keycode is composed of an integer + a string
            # If we hit escape, release the keyboard
            # On ESC, click on back button if it exists
            if keycode[1] == 'escape' and 'escape' not in self._ignore_keys:
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


        # On TAB/Shift+TAB, cycle through elements
        if keycode[1] == 'tab' and 'tab' not in self._ignore_keys:
            pass
            # for widget in self.walk():
            #     try:
            #         if "button" in widget.id or "input" in widget.id:
            #             print(widget)
            #             break
            #     except AttributeError:
            #         continue


        # Return True to accept the key. Otherwise, it will be used by the system.
        return True


    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Screen won't get added to screen tree on leave
        self._ignore_tree = False

        self.banner_widget = None
        self.popup_widget = None
        self.page_switcher = None

        self._input_focused = False
        self._keyboard = None

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
        if diff > 5:
            Clock.schedule_once(self.percentage.texture_update, -1)
        self.percentage.size_hint_max = self.percentage.texture_size
        self.percentage.text = original_text

        # Actually animate schennanies LOL fuck kivy holy shit
        def anim(*args):

            thread = threading.Timer(0, update_text)
            thread.start()

            text_x = new_x if self.value == 0 else (new_x - self.percentage.width / 2)
            if text_x < self.rail.x:
                text_x = self.rail.x
            overshoot = (new_x + (self.percentage.width / 1.5)) - self.size_hint_max[0]
            if overshoot > 0:
                text_x -= overshoot

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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.size_hint_max = (540, 28)
        self.value = 0

        # Frame of progress bar
        self.rail = Image()
        self.rail.allow_stretch = True
        self.rail.keep_ratio = False
        self.rail.source = os.path.join(constants.gui_assets, 'progress_bar_empty.png')

        # Cover of progress bar (to simulate horizontal movement)
        self.cover = Image()
        self.cover.allow_stretch = True
        self.cover.keep_ratio = False
        self.cover.size_hint_max_x = self.size_hint_max_x
        self.cover.color = constants.background_color
        self.cover.pos_hint = {'center_y': 0.5}

        # Progress bar animation
        self.bar = Image()
        self.bar.allow_stretch = True
        self.bar.keep_ratio = False
        self.bar.source = os.path.join(constants.gui_assets, 'animations', 'bar_full.gif')
        self.bar.anim_delay = 0.025

        # Progress bar Static
        self.static_bar = Image()
        self.static_bar.allow_stretch = True
        self.static_bar.keep_ratio = False
        self.static_bar.source = os.path.join(constants.gui_assets, 'progress_bar_full.png')
        self.static_bar.color = (0.58, 0.6, 1, 1)
        self.static_bar.opacity = 0

        # Percentage text
        self.percentage = Label()
        self.percentage.text = "0%"
        self.percentage.font_name = os.path.join(constants.gui_assets, 'fonts', constants.fonts['medium'])
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

        self.update_progress(self.value)
class ProgressScreen(MenuBackground):

    # Returns current progress bar value
    def get_progress(self):
        return self.progress_bar.value

    # Only replace this function when making a child screen
    # Set fail message in child functions to trigger an error
    def contents(self):
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
                ('Step 1', functools.partial(time.sleep, 3), 30),
                ('Step 2', functools.partial(time.sleep, 3), 30),
                ('Step 3', functools.partial(time.sleep, 0.1), 30),
                ('Step 4', functools.partial(time.sleep, 0.1), 10)
            ),

            # Function to run before steps (like checking for an internet connection)
            'before_function': functools.partial(time.sleep, 0),

            # Function to run after everything is complete (like cleaning up the screen tree) will only run if no error
            'after_function': functools.partial(time.sleep, 0),

            # Screen to go to after complete
            'next_screen': 'MainMenuScreen'
        }


    def execute_steps(self):
        icons = os.path.join(constants.gui_assets, 'fonts', constants.fonts['icons'])

        constants.ignore_close = True

        # Execute before function
        if self.page_contents['before_function']:
            self.page_contents['before_function']()
            if self.error:
                return

        # Go over every step in function_list
        for x, step in enumerate(self.page_contents['function_list']):

            # Close thread if error occurred
            if self.error:
                return

            if x != 0:
                if "[font=" not in self.steps.label_2.text:
                    self.steps.label_2.text = self.steps.label_2.text.split('(')[0].strip() + f"   [font={icons}]å[/font]"
                time.sleep(0.6)
            self.update_steps(step[0], x)

            # Execute function and check for completion
            self.last_progress = self.progress_bar.value
            test = step[1]()
            time.sleep(0.27)

            # If it failed, execute default error
            if not test:
                self.execute_error(self.page_contents['default_error'])
                return

            self.progress_bar.update_progress(self.progress_bar.value + step[2])

        # Execute after_function
        time.sleep(0.5)
        if "[font=" not in self.steps.label_2.text:
            self.steps.label_2.text = self.steps.label_2.text.split('(')[0].strip() + f"   [font={icons}]å[/font]"
        time.sleep(0.19)
        Animation(color=(0.3, 1, 0.6, 1), duration=0.2, transition='out_sine').start(self.steps.label_2)

        # Execute after function on if there was no error
        if self.page_contents['after_function'] and not self.error:
            self.page_contents['after_function']()

        # Switch to next_page after it's done
        constants.ignore_close = False
        if not self.error and self.page_contents['next_screen']:
            def next_screen(*args):
                screen_manager.current = self.page_contents['next_screen']
            Clock.schedule_once(next_screen, 0.8)


    def execute_error(self, msg, *args):
        constants.ignore_close = False
        self.error = True

        def close(*args):
            Clock.schedule_once(previous_screen, 0.25)
            self.error = False
            self.timer = None

        def function(*args):
            self.timer.cancel()
            self.show_popup('warning', 'Error', msg, (close))

        Clock.schedule_once(function, 0)


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'

        self._ignore_tree = True

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

        print(f"Progress {current} {num}")

        icons = os.path.join(constants.gui_assets, 'fonts', constants.fonts['icons'])
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
                self.steps.label_2.text = self.steps.label_2.text.split('(')[0].strip() + f"   [font={icons}]å[/font]"
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
                    except IndexError:
                        pass
                    self.steps.label_1.y = self.steps.label_1.original_y


                # Label 2
                try:
                    self.steps.label_2.text = current + yummy_label
                    self.steps.label_2.opacity = 1
                except IndexError:
                    pass
                self.steps.label_2.y = self.steps.label_2.original_y


                # Label 3
                try:
                    self.steps.label_3.text = self.page_contents['function_list'][num+1][0]
                    self.steps.label_3.opacity = 0.3
                except IndexError:
                    self.steps.label_3.text = ""
                self.steps.label_3.y = self.steps.label_3.original_y


                # Label 4
                try:
                    self.steps.label_4.text = self.page_contents['function_list'][num+2][0]
                    self.steps.label_4.opacity = 0.3
                except IndexError:
                    self.steps.label_4.text = ""
                self.steps.label_4.y = self.steps.label_4.original_y

            Clock.schedule_once(delayed_func, anim_duration+0.01 if self.start else 0)
            self.start = True


    def generate_menu(self, **kwargs):
        # Generate buttons on page load
        self.contents()
        self.start = False
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
                self.font_name = os.path.join(constants.gui_assets, 'fonts', constants.fonts['medium'])
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
        self.steps.scroll_top = scroll_background(pos_hint={'center_x': 0.5}, pos=(0, self.steps.size_hint_max[1] * 1.7), size=(Window.width // 1.5, 60))
        self.steps.scroll_bottom = scroll_background(pos_hint={'center_x': 0.5}, pos=(0, (self.steps.size_hint_max[1] / 3.5)), size=(Window.width // 1.5, -60))
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

        self.timer = threading.Timer(0, self.execute_steps)
        self.timer.start()

# </editor-fold> ///////////////////////////////////////////////////////////////////////////////////////////////////////




# ================================================== Main Menu =========================================================
# <editor-fold desc="Main Menu">

class MainMenuScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__

    def generate_menu(self, **kwargs):
        # Generate buttons on page load
        buttons = []
        float_layout = FloatLayout()

        constants.screen_tree = []
        constants.generate_server_list()

        splash = FloatLayout()

        logo = Image(source=os.path.join(constants.gui_assets, 'logo.png'), allow_stretch=True, size_hint=(None, None), width=dp(550), pos_hint={"center_x": 0.5, "center_y": 0.77})

        splash.add_widget(logo)
        splash.add_widget(Label(text=f"v{constants.app_version}{(8 - len(constants.app_version)) * '  '}", pos=(330, 200), pos_hint={"center_y": 0.77}, color=(0.6, 0.6, 1, 0.5), font_name=os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf'), font_size=sp(23)))
        splash.add_widget(Label(text="_" * 50, pos_hint={"center_y": 0.7}, color=(0.6, 0.6, 1, 0.1), font_name=os.path.join(constants.gui_assets, 'fonts', 'LLBI.otf'), font_size=sp(25)))
        splash.add_widget(Label(text=constants.session_splash, pos_hint={"center_y": 0.65}, color=(0.6, 0.6, 1, 0.5), font_name=os.path.join(constants.gui_assets, 'fonts', 'LLBI.otf'), font_size=sp(25)))

        float_layout.add_widget(splash)

        if not constants.server_list:
            buttons.append(main_button('Import a server', (0.5, 0.42), 'download-outline.png'))
        else:
            buttons.append(main_button('Manage Auto-MCS servers', (0.5, 0.42), 'settings-outline.png'))
        buttons.append(main_button('Create a new server', (0.5, 0.32), 'duplicate-outline.png'))
        buttons.append(exit_button('Quit', (0.5, 0.17)))

        for button in buttons:
            float_layout.add_widget(button)

        float_layout.add_widget(generate_footer('splash'))

        self.add_widget(float_layout)

# </editor-fold> ///////////////////////////////////////////////////////////////////////////////////////////////////////




#  =============================================== Create Server =======================================================
# <editor-fold desc="Create Server">

# Create Server Step 1:  Server Name -----------------------------------------------------------------------------------

class CreateServerNameScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'

    def generate_menu(self, **kwargs):
        # Generate buttons on page load
        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'

        # Prevent server creation if offline
        if not constants.app_online:
            float_layout.add_widget(HeaderText("Server creation requires an internet connection", '', (0, 0.6)))
            buttons.append(exit_button('Back', (0.5, 0.35)))

        # Regular menus
        else:
            float_layout.add_widget(InputLabel(pos_hint={"center_x": 0.5, "center_y": 0.58}))
            float_layout.add_widget(HeaderText("What would you like to name your server?", '', (0, 0.76)))
            name_input = ServerNameInput(pos_hint={"center_x": 0.5, "center_y": 0.5}, text=constants.new_server_info['name'])
            float_layout.add_widget(name_input)
            buttons.append(next_button('Next', (0.5, 0.24), not constants.new_server_info['name'], next_screen='CreateServerTypeScreen'))
            buttons.append(exit_button('Back', (0.5, 0.14), cycle=True))
            float_layout.add_widget(page_counter(1, 7, (0, 0.768)))

        for button in buttons:
            float_layout.add_widget(button)

        float_layout.add_widget(generate_title('Create New Server'))
        float_layout.add_widget(generate_footer('Create new server'))

        self.add_widget(float_layout)

        if constants.app_online:
            name_input.grab_focus()



# Create Server Step 2:  Server Type -----------------------------------------------------------------------------------

class CreateServerTypeScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'

    def generate_menu(self, **kwargs):
        # Generate buttons on page load
        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'

        float_layout.add_widget(HeaderText("What type of server do you wish to create?", '', (0, 0.86)))

        # Create UI buttons
        buttons.append(next_button('Next', (0.5, 0.21), False, next_screen='CreateServerVersionScreen'))
        buttons.append(exit_button('Back', (0.5, 0.12), cycle=True))

        # Create type buttons
        content_layout = FloatLayout()
        content_layout.current_selection = constants.new_server_info['type']
        row_top = BoxLayout()
        row_bottom = BoxLayout()
        row_top.pos_hint = {"center_y": 0.66, "center_x": 0.5}
        row_bottom.pos_hint = {"center_y": 0.405, "center_x": 0.5}
        row_bottom.size_hint_max_x = row_top.size_hint_max_x = dp(1000)
        row_top.orientation = row_bottom.orientation = "horizontal"
        row_top.add_widget(big_icon_button('runs most plug-ins, optimized', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None), 'paper', clickable=True, selected=('paper' == constants.new_server_info['type'])))
        row_top.add_widget(big_icon_button('default, stock experience', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None), 'vanilla', clickable=True, selected=('vanilla' == constants.new_server_info['type'])))
        row_top.add_widget(big_icon_button('modded experience', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None), 'forge', clickable=True, selected=('forge' == constants.new_server_info['type'])))
        row_bottom.add_widget(big_icon_button('requires tuning, but efficient', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None), 'spigot', clickable=True, selected=('spigot' == constants.new_server_info['type'])))
        row_bottom.add_widget(big_icon_button('legacy, supports plug-ins', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None), 'craftbukkit', clickable=True, selected=('craftbukkit' == constants.new_server_info['type'])))
        row_bottom.add_widget(big_icon_button('experimental mod platform', {"center_y": 0.5, "center_x": 0.5}, (0, 0), (None, None), 'fabric', clickable=True, selected=('fabric' == constants.new_server_info['type'])))

        for button in buttons:
            float_layout.add_widget(button)

        content_layout.add_widget(row_top)
        content_layout.add_widget(row_bottom)
        float_layout.add_widget(content_layout)
        menu_name = f"Create '{constants.new_server_info['name']}'"

        float_layout.add_widget(page_counter(2, 7, (0, 0.868)))
        float_layout.add_widget(generate_title(menu_name))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)



# Create Server Step 3:  Server Version --------------------------------------------------------------------------------

class CreateServerVersionScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'

    def generate_menu(self, **kwargs):

        # Generate buttons on page load
        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'

        # Prevent server creation if offline
        if not constants.app_online:
            float_layout.add_widget(HeaderText("Server creation requires an internet connection", '', (0, 0.6)))
            buttons.append(exit_button('Back', (0.5, 0.35)))

        # Regular menus
        else:
            float_layout.add_widget(InputLabel(pos_hint={"center_x": 0.5, "center_y": 0.58}))
            float_layout.add_widget(page_counter(3, 7, (0, 0.768)))
            float_layout.add_widget(HeaderText("What version of Minecraft do you wish to play?", '', (0, 0.76)))
            float_layout.add_widget(ServerVersionInput(pos_hint={"center_x": 0.5, "center_y": 0.5}, text=constants.new_server_info['version']))
            buttons.append(next_button('Next', (0.5, 0.24), False, next_screen='CreateServerWorldScreen', show_load_icon=True))
            buttons.append(exit_button('Back', (0.5, 0.14), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)

        menu_name = f"Create '{constants.new_server_info['name']}'"
        float_layout.add_widget(generate_title(menu_name))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)



# Create Server Step 4:  Server Name -----------------------------------------------------------------------------------
# Note:  Also generates ACL object after name/version are decided
class CreateServerWorldScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'

    def generate_menu(self, **kwargs):

        # Generate ACL in new_server_info
        def create_acl():
            if not constants.new_server_info['acl_object']:
                constants.new_server_info['acl_object'] = acl.AclObject(constants.new_server_info['name'])
            else:
                constants.new_server_info['acl_object'].server = acl.dump_config(constants.new_server_info['name'], True)

            # acl.print_acl(constants.new_server_info['acl_object'])

        thread = threading.Timer(0, create_acl)
        thread.start()


        # Generate buttons on page load
        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'
        float_layout.add_widget(InputLabel(pos_hint={"center_x": 0.5, "center_y": 0.62}))
        float_layout.add_widget(HeaderText("What world would you like to use?", '', (0, 0.76)))
        float_layout.add_widget(ServerWorldInput(pos_hint={"center_x": 0.5, "center_y": 0.55}))
        float_layout.add_widget(ServerSeedInput(pos_hint={"center_x": 0.5, "center_y": 0.442}))
        buttons.append(input_button('Browse...', (0.5, 0.55), ('dir', constants.saveFolder if os.path.isdir(constants.saveFolder) else constants.userDownloads), input_name='ServerWorldInput', title='Select a World File'))

        server_version = constants.new_server_info['version']
        if constants.version_check(server_version, '>=', "1.1"):
            options = ['normal', 'superflat']
            if constants.version_check(server_version, '>=', "1.3.1"):
                options.append('large biomes')
            if constants.version_check(server_version, '>=', "1.7.2"):
                options.append('amplified')
            default_name = constants.new_server_info['server_settings']['level_type'].replace("default", "normal").replace("flat", "superflat").replace("large_biomes", "large biomes")
            float_layout.add_widget(DropButton(default_name, (0.5, 0.442), options_list=options, input_name='ServerLevelTypeInput', x_offset=41))

        buttons.append(next_button('Next', (0.5, 0.24), False, next_screen='CreateServerNetworkScreen'))
        buttons.append(exit_button('Back', (0.5, 0.14), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)

        menu_name = f"Create '{constants.new_server_info['name']}'"
        float_layout.add_widget(page_counter(4, 7, (0, 0.768)))
        float_layout.add_widget(generate_title(menu_name))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)

    def on_pre_enter(self, *args):
        super().on_pre_enter()
        self.toggle_new(constants.new_server_info['server_settings']['world'] != 'world')

    # Call this when world loaded, and when the 'create new world instead' button is clicked. Fix overlapping when added/removed multiple times
    def toggle_new(self, boolean_value):

        current_input = ''
        server_version = constants.new_server_info['version']

        for child in self.children:
            try:
                if child.id == 'content':
                    for item in child.children:
                        try:
                            if item.__class__.__name__ == 'ServerSeedInput':
                                current_input = 'input'
                                if constants.new_server_info['server_settings']['world'] != 'world':
                                    child.remove_widget(item)

                                    try:
                                        if constants.version_check(server_version, '>=', "1.1"):
                                            child.remove_widget([relative for relative in child.children if relative.__class__.__name__ == 'DropButton'][0])
                                    except IndexError:
                                        if constants.debug:
                                            print("Error: 'DropButton' does not exist, can't remove")

                            elif item.id == 'Create new world instead':
                                current_input = 'button'
                                if constants.new_server_info['server_settings']['world'] == 'world':
                                    child.remove_widget(item)
                        except AttributeError:
                            continue

                    # Show button if true
                    if boolean_value and constants.new_server_info['server_settings']['world'] != 'world' and current_input == 'input':
                        child.add_widget(main_button('Create new world instead', (0.5, 0.442), 'add-circle-outline.png', width=530))

                    # Show seed input, and clear world text
                    elif constants.new_server_info['server_settings']['world'] == 'world' and current_input == 'button':
                        child.add_widget(ServerSeedInput(pos_hint={"center_x": 0.5, "center_y": 0.442}))

                        if constants.version_check(server_version, '>=', "1.1"):
                            options = ['normal', 'superflat']
                            if constants.version_check(server_version, '>=', "1.3.1"):
                                options.append('large biomes')
                            if constants.version_check(server_version, '>=', "1.7.2"):
                                options.append('amplified')
                            default_name = constants.new_server_info['server_settings']['level_type'].replace("default", "normal").replace("flat", "superflat").replace("large_biomes", "large biomes")
                            child.add_widget(DropButton(default_name, (0.5, 0.442), options_list=options, input_name='ServerLevelTypeInput', x_offset=41))
                    break

            except AttributeError:
                pass



# Create Server Step 5:  Server Network --------------------------------------------------------------------------------
def process_ip_text(server_obj=None):

    if server_obj:
        start_text = ''
        if not str(server_obj.port) == '25565' or server_obj.ip:
            if server_obj.ip:
                start_text = server_obj.ip
            if str(server_obj.port) != '25565':
                start_text = start_text + ':' + str(server_obj.port) if start_text else str(server_obj.port)

    else:
        start_text = ''
        if not str(constants.new_server_info['port'] == '25565') or constants.new_server_info['ip']:
            if constants.new_server_info['ip']:
                start_text = constants.new_server_info['ip']
            if str(constants.new_server_info['port']) != '25565':
                start_text = start_text + ':' + constants.new_server_info['port'] if start_text else constants.new_server_info['port']

    return start_text

class CreateServerNetworkScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'

    def generate_menu(self, **kwargs):

        # Generate buttons on page load
        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'

        float_layout.add_widget(InputLabel(pos_hint={"center_x": 0.5, "center_y": 0.685}))
        float_layout.add_widget(HeaderText("Do you wish to configure network information?", '', (0, 0.8)))
        float_layout.add_widget(CreateServerPortInput(pos_hint={"center_x": 0.5, "center_y": 0.62}, text=process_ip_text()))
        float_layout.add_widget(ServerMOTDInput(pos_hint={"center_x": 0.5, "center_y": 0.515}))
        float_layout.add_widget(main_button('Access Control Manager', (0.5, 0.4), 'shield-half-small.png', width=531))
        buttons.append(next_button('Next', (0.5, 0.24), False, next_screen='CreateServerOptionsScreen'))
        buttons.append(exit_button('Back', (0.5, 0.14), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)

        menu_name = f"Create '{constants.new_server_info['name']}'"
        float_layout.add_widget(page_counter(5, 7, (0, 0.808)))
        float_layout.add_widget(generate_title(menu_name))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)



# Create Server Step 5:  ACL Options -----------------------------------------------------------------------------------

class RuleButton(FloatLayout):

    def __setattr__(self, attr, value):

        # Change attributes dynamically based on rule
        if attr == "rule" and value:
            self.text.text = value.rule.replace("!w", "")
            self.change_properties(value)

        super().__setattr__(attr, value)


    # Modifies rule attributes based on rule.list_enabled status
    def change_properties(self, rule):

        # Prevent crash from spamming the back button
        if "Acl" not in screen_manager.current_screen.name:
            return

        Animation.cancel_all(self.button)
        Animation.cancel_all(self.text)
        Animation.cancel_all(self.icon)

        self.button.id = f'rule_button{"_enabled" if rule.list_enabled else ""}'
        self.button.background_normal = os.path.join(constants.gui_assets, f'{self.button.id}.png')
        self.button.background_down = os.path.join(constants.gui_assets, f'{self.button.id}_click.png')

        # Change color attributes
        if screen_manager.current_screen.current_list == "ops":
            self.color_id = self.button.color_id = [(0, 0, 0, 0.85), (0.439, 0.839, 1, 1)] if rule.list_enabled else [(0, 0, 0, 0.85), (0.6, 0.5, 1, 1)]
            self.hover_attr = (icon_path("close-circle.png"), 'DEMOTE', (1, 0.5, 0.65, 1)) if rule.list_enabled else (icon_path("promote.png"), 'PROMOTE', (0.3, 1, 0.6, 1))
        elif screen_manager.current_screen.current_list == "bans":
            if rule.rule_type == "ip":
                self.color_id = self.button.color_id = [(0, 0, 0, 0.85), (1, 0.45, 0.85, 1)] if rule.list_enabled else [(0, 0, 0, 0.85), (0.4, 0.8, 1, 1)]
            else:
                self.color_id = self.button.color_id = [(0, 0, 0, 0.85), (1, 0.5, 0.65, 1)] if rule.list_enabled else [(0, 0, 0, 0.85), (0.3, 1, 0.6, 1)]
            if rule.list_enabled:
                self.hover_attr = (icon_path("lock-open.png"), 'PARDON', (0.3, 1, 0.6, 1))
            else:
                self.hover_attr = (icon_path("close-circle.png"), 'BAN' if rule.rule_type == 'player' else 'REMOVE', (1, 0.5, 0.65, 1))
        elif screen_manager.current_screen.current_list == "wl":
            if screen_manager.current_screen.acl_object.server['whitelist']:
                self.color_id = self.button.color_id = [(0, 0, 0, 0.85), (0.3, 1, 0.6, 1)] if rule.list_enabled else [(0, 0, 0, 0.85), (1, 0.5, 0.65, 1)]
            else:
                self.color_id = self.button.color_id = [(0, 0, 0, 0.85), (0.3, 1, 0.6, 1)] if rule.list_enabled else [(0, 0, 0, 0.85), (0.7, 0.7, 0.7, 1)]
            self.hover_attr = (icon_path("close-circle.png"), 'RESTRICT', (1, 0.5, 0.65, 1)) if rule.list_enabled else (icon_path("checkmark-circle-sharp.png"), 'PERMIT', (0.3, 1, 0.6, 1))

        new_color_id = (self.color_id[1][0], self.color_id[1][1], self.color_id[1][2], 1 if rule.list_enabled else 0.95)
        self.color_id[1] = new_color_id
        self.button.color_id[1] = new_color_id
        self.text.color = constants.brighten_color(new_color_id, 0.2)
        self.icon.color = constants.brighten_color(new_color_id, 0.2)
        self.icon.source = icon_path("earth-sharp.png")
        self.button.background_color = new_color_id


        # Change scope attributes
        if rule.rule_scope == "global":
            self.text.pos_hint["center_x"] = 0.5 + round(len(self.text.text) * 0.01, 2)
            self.icon.opacity = 1
            self.icon.color = self.global_icon_color
            if rule.rule_type == "player" or "/" in rule.rule:
                self.text.font_size = sp(19 - (0 if len(self.text.text) < 11 else (len(self.text.text) // 5)))

        else:
            self.text.pos_hint["center_x"] = 0.5
            self.icon.opacity = 0
            self.icon.color = self.color_id[1]
            if rule.rule_type == "player" or "/" in rule.rule:
                self.text.font_size = sp(19 - (0 if len(self.text.text) < 11 else (len(self.text.text) // 7)))

        if rule.rule_type == "ip" and "/" not in rule.rule:
            self.text.font_size = sp(19)

        self.original_font_size = self.text.font_size


    def highlight(self, original_color, original_text_color, original_hover_color):
        self.button.background_color = constants.brighten_color(original_hover_color, -0.15)
        self.text.color = constants.brighten_color(original_hover_color, -0.15)
        Animation(background_color=original_color, duration=1).start(self.button)
        Animation(color=original_text_color, duration=1).start(self.text)


    def __init__(self, name='', icon_name=None, width=None, icon_offset=None, auto_adjust_icon=False, **kwargs):
        super().__init__(**kwargs)

        position = (0.5, 0.5)
        self.size_hint_max_y = dp(60)
        self.rule = None
        self.id = 'rule_button'
        self.enabled = True
        self.original_font_size = None


        # Hover button object
        self.button = HoverButton()

        def on_enter(*args):

            Animation.cancel_all(self.button)
            Animation.cancel_all(self.text)

            if not self.button.ignore_hover:
                animate_button(self.button, image=os.path.join(constants.gui_assets, f'{self.button.id}_hover.png'), color=self.button.color_id[0])
                self.text.font_size = sp(18)

                if self.rule.rule_scope == "global":
                    self.icon.source = icon_path("earth-strike.png")
                    self.text.text = "LOCALIZE"
                    Animation(background_color=self.global_icon_color, duration=0.05).start(self.button)

                else:
                    self.icon.source = self.hover_attr[0]
                    self.text.text = "   " + self.hover_attr[1]
                    Animation(background_color=self.hover_attr[2], duration=0.05).start(self.button)
                    Animation(opacity=1, duration=0.05).start(self.icon)

        def on_leave(*args):
            if not self.button.ignore_hover:
                animate_button(self.button, image=os.path.join(constants.gui_assets, f'{self.button.id}.png'), color=constants.brighten_color(self.button.color_id[1], 0.2))
                self.text.font_size = self.original_font_size
                self.text.text = self.rule.rule.replace("!w", "")
                new_color_id = (self.color_id[1][0], self.color_id[1][1], self.color_id[1][2], 1 if self.rule.list_enabled else 0.95)
                Animation(background_color=new_color_id, duration=0.1).start(self.button)

                if self.rule.rule_scope == "global":
                    Animation(color=self.global_icon_color,duration=0.07).start(self.icon)
                    self.icon.source = icon_path("earth-sharp.png")
                else:
                    Animation(opacity=0, duration=0.05).start(self.icon)

        def click_func(button_pressed=None, *args):

            if not button_pressed or not isinstance(button_pressed, str):
                button_pressed = self.button.button_pressed.lower().strip()

            button_text = self.text.text.lower().strip()
            current_list = screen_manager.current_screen.current_list.lower().strip()
            acl_object = screen_manager.current_screen.acl_object
            original_name = self.rule.rule
            filtered_name = self.rule.rule.replace("!w", "").replace("!g", "").strip()
            original_hover_attr = self.hover_attr
            new_scope = self.rule.rule_scope
            banner_text = ""
            reload_page = False
            localize = False


            # Left click on button (Local)
            if button_pressed == "left" and self.rule.rule_scope == "local":

                # Modify 'ops' list
                if current_list == "ops" and button_text in ['promote', 'demote']:
                    acl_object.op_player(self.rule.rule, remove=(button_text == "demote"))
                    banner_text = f"'{filtered_name}' was {'demoted' if (button_text == 'demote') else 'promoted'}"
                    reload_page = True

                # Modify 'bans' list
                elif current_list == "bans" and button_text in ['ban', 'pardon', 'remove']:
                    acl_object.ban_player(self.rule.rule, remove=(button_text == "pardon") or ("!w" in self.rule.rule))

                    if button_text == "pardon":
                        try:
                            ip_addr = acl.get_uuid(self.rule.rule)['latest-ip'].split(":")[0].strip()
                        except KeyError:
                            ip_addr = ""

                        if ip_addr:
                            # Whitelist IP if it's still in the rule list
                            if ip_addr in acl.gen_iplist(acl_object.rules['subnets']):
                                acl_object.ban_player(f"!w{ip_addr}", remove=False)

                    banner_text = f"'{filtered_name}' was removed" if button_text == 'remove' else f"'{filtered_name}' is {'pardoned' if (button_text == 'pardon') else 'banned'}"
                    reload_page = True

                # Modify 'wl' list
                elif current_list == "wl" and button_text in ['permit', 'restrict']:
                    acl_object.whitelist_player(self.rule.rule, remove=(button_text == "restrict"))
                    banner_text = f"'{filtered_name}' is {'restricted' if (button_text == 'restrict') else 'permitted'}"
                    reload_page = True


            # Left click on button (global)
            elif button_pressed == "left" and self.rule.rule_scope == "global" and button_text == "localize":
                acl_object.add_global_rule(self.rule.rule, current_list, remove=True)
                original_hover_attr = (
                    icon_path("earth-strike.png"),
                    original_hover_attr[1],
                    self.color_id[1]
                )
                banner_text = f"'{filtered_name}' rule is now locally applied"
                localize = True
                new_scope = "local"
                reload_page = True


            # Middle click on button
            elif button_pressed == "middle":
                acl_object.add_global_rule(self.rule.rule, current_list, remove=(button_text == 'localize'))
                original_hover_attr = (
                    icon_path(f"earth-{'strike' if (self.rule.rule_scope == 'global') else 'sharp'}.png"),
                    original_hover_attr[1],
                    self.global_icon_color if (self.rule.rule_scope == 'local') else self.color_id[1]
                )
                banner_text = f"'{filtered_name}' is now {'local' if (self.rule.rule_scope == 'global') else 'global'}ly applied"
                localize = self.rule.rule_scope == "global"
                new_scope = "local" if localize else "global"
                reload_page = True



            if reload_page:
                # print(button_text, button_pressed, current_list)

                # If rule localized, enable on current list
                if localize:
                    if current_list == "ops":
                        acl_object.op_player(self.rule.rule)
                    elif current_list == "bans":
                        acl_object.ban_player(self.rule.rule)
                    elif current_list == "wl":
                        acl_object.whitelist_player(self.rule.rule)


                self.button.on_leave()
                self.change_properties(self.rule)
                self.button.state = "normal"

                Animation.cancel_all(self.button)
                Animation.cancel_all(self.text)
                Animation.cancel_all(self.icon)

                screen_manager.current_screen.update_list(current_list, reload_children=False)

                Clock.schedule_once(
                    functools.partial(
                        screen_manager.current_screen.show_banner,
                        original_hover_attr[2],
                        banner_text,
                        original_hover_attr[0],
                        2,
                        {"center_x": 0.5, "center_y": 0.965}
                    ), 0
                )

                def trigger_highlight(*args):
                    for rule_button in screen_manager.current_screen.scroll_layout.children:

                        if rule_button.rule.rule == original_name:
                            rule_button.highlight(rule_button.button.background_color, rule_button.text.color, original_hover_attr[2])

                        else:
                            rule_button.button.on_leave()
                            Animation.cancel_all(rule_button.button)
                            Animation.cancel_all(rule_button.text)
                            Animation.cancel_all(rule_button.icon)
                            rule_button.change_properties(rule_button.rule)

                        rule_button.button.ignore_hover = False

                Clock.schedule_once(trigger_highlight, 0)

            # Update display rule regardless of button pressed
            screen_manager.current_screen.update_user_panel(self.rule.rule, new_scope)



        self.button.on_enter = on_enter
        self.button.on_leave = on_leave
        self.button.bind(on_press=click_func)
        self.button.id = 'rule_button'
        self.color_id = self.button.color_id = [(0.03, 0.03, 0.03, 1), (1, 1, 1, 1)] # [(0.05, 0.05, 0.1, 1), (0.6, 0.6, 1, 1)]
        self.hover_attr = (icon_path('close-circle.png'), 'hover text', (1, 1, 1, 1)) # Icon, Text, Hover color
        self.global_icon_color = (0.953, 0.929, 0.38, 1)

        self.button.size_hint = (None, None)
        self.button.size = (dp(190 if not width else width), self.size_hint_max_y)
        self.button.pos_hint = {"center_x": position[0], "center_y": position[1]}
        self.button.border = (-3, -3, -3, -3)
        self.button.background_normal = os.path.join(constants.gui_assets, 'rule_button.png')
        self.button.background_down = os.path.join(constants.gui_assets, 'rule_button_click.png')
        self.button.always_release = True

        self.text = Label()
        self.text.id = 'text'
        self.text.size_hint = (None, None)
        self.text.pos_hint = {"center_x": position[0], "center_y": position[1]}
        self.text.text = name
        self.text.font_size = sp(19)
        self.text.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["bold"]}.ttf')
        self.text.color = self.color_id[1]


        # Button click behavior
        self.button.on_release = functools.partial(button_action, name, self.button)
        self.add_widget(self.button)


        # Icon thingy
        self.icon = Image()
        self.icon.id = 'icon'
        self.icon.source = icon_path("earth-sharp.png") if not icon_name else icon_path(icon_name)
        self.icon.size = (25, 25)
        self.icon.size_hint = (None, None)
        self.icon.opacity = 0
        self.icon.color = self.color_id[1]
        self.icon.pos_hint = {"center_x": -0.2, "center_y": 0.5}


        self.add_widget(self.icon)
        self.add_widget(self.text)

class AclRulePanel(RelativeLayout):

    def __init__(self, **kw):
        super().__init__(**kw)

        class HeaderLabel(Label):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.size_hint = (None, None)
                self.markup = True
                self.font_size = sp(22)
                self.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
                self.color = (0.6, 0.6, 1, 1)

        class ParagraphLabel(Label, HoverBehavior):

            def on_mouse_pos(self, *args):

                if "AclScreen" in screen_manager.current_screen.name:

                    try:
                        super().on_mouse_pos(*args)
                    except:
                        pass

                    if self.text.count(".") > 3 and "IP" in self.text:
                        rel_y = args[1][1] - screen_manager.current_screen.user_panel.y
                        if self.hovered and rel_y < 190:
                            self.on_leave()
                            self.hovered = False


            # Hover stuffies
            def on_enter(self, *args):

                # Change size of IP text
                if self.text.count(".") > 3 and "IP" in self.text:
                    rel_y = self.border_point[1] - screen_manager.current_screen.user_panel.y
                    if rel_y < 190:
                        self.hovered = False
                        return None

                if self.copyable:
                    self.outline_width = 0
                    self.outline_color = constants.brighten_color(self.color, 0.05)
                    Animation(outline_width=1, duration=0.03).start(self)


            def on_leave(self, *args):

                if self.copyable:
                    Animation.stop_all(self)
                    self.outline_width = 0


            # Normal stuffies
            def on_ref_press(self, *args):
                if not self.disabled:

                    Clock.schedule_once(
                        functools.partial(
                            screen_manager.current_screen.show_banner,
                            (0.85, 0.65, 1, 1),
                            "Copied text to clipboard",
                            "link-sharp.png",
                            2,
                            {"center_x": 0.5, "center_y": 0.965}
                        ), 0
                    )

                    Clipboard.copy(re.sub("\[.*?\]","",self.text))


            def ref_text(self, *args):

                self.copyable = not (("unknown" in self.text.lower()) or ("online" in self.text.lower()) or (("access") in self.text.lower()))

                if '[ref=' not in self.text and '[/ref]' not in self.text and self.copyable:
                    self.text = f'[ref=none]{self.text}[/ref]'
                elif '[/ref]' in self.text:
                    self.text = self.text.replace("[/ref]","") + "[/ref]"

                self.texture_update()
                self.size = self.texture_size

                if self.text.count(".") > 3 and "IP" in self.text:
                    self.width = self.texture_size[0] / 1.5


            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.size_hint = (None, None)
                self.markup = True
                self.font_size = sp(18)
                self.copyable = True
                self.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["regular"]}.ttf')
                self.default_color = (0.6, 0.6, 1, 1)
                self.color = self.default_color
                self.bind(text=self.ref_text)


        self.color_dict = {
            "blue":    "#70E6FF",
            "red":     "#FF8793",
            "green":   "#4CFF99",
            "white":   "#FFFFFF",
            "gray":    "#A0A0A0",
            "yellow":  "#F3ED61",
            "purple":  "#A699FF"
        }


        self.displayed_type = ""
        self.displayed_scope = "local"

        # User panel (I'm sorry in advance)
        # <editor-fold desc="User Panel SUFFERING">
        self.pos_hint = {"center_y": 0.42}
        self.size_hint_max = (500, 600)

        # Background image
        self.background = Image()
        self.background.id = 'background'
        self.background.source = os.path.join(constants.gui_assets, 'user_panel.png')
        self.background.color = (0.65, 0.6, 1, 1)
        self.background.opacity = 0

        # Label when no rule is displayed
        self.blank_label = Label()
        self.blank_label.id = 'blank_label'
        self.blank_label.text = "Right-click a rule to view"
        self.blank_label.font_name = os.path.join(constants.gui_assets, 'fonts', constants.fonts['italic'])
        self.blank_label.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        self.blank_label.font_size = sp(26)
        self.blank_label.color = (0.6, 0.6, 1, 0.4)
        self.blank_label.opacity = 0

        # Drop down options button
        self.options = DropButton('OPTIONS', (0.5, 0.192), options_list=['operators', 'bans', 'whitelist'], input_name='ServerAclOptionsInput', x_offset=-33, facing='center', custom_func=self.modify_rule, change_text=False)
        self.add_widget(self.options)


        # Player Layout
        # <editor-fold desc="Player Layout Widgets">
        self.player_layout = RelativeLayout()
        self.player_layout.id = 'player_layout'

        self.player_layout.header_icon = Image()
        self.player_layout.header_icon.source = icon_path('person-circle-sharp.png')
        self.player_layout.header_icon.allow_stretch = True
        self.player_layout.header_icon.size_hint_max = (36, 36)
        self.player_layout.header_icon.pos_hint = {"center_x": 0.5, "center_y": 0.808}
        self.player_layout.add_widget(self.player_layout.header_icon)

        # Make this copyable text
        self.player_layout.name_label = HeaderLabel()
        self.player_layout.name_label.pos_hint = {"center_x": 0.54, "center_y": 0.81}
        self.player_layout.name_label.font_size = sp(25)
        self.player_layout.add_widget(self.player_layout.name_label)

        self.player_layout.online_icon = Image()
        self.player_layout.online_icon.source = icon_path('radio-button-off-sharp.png')
        self.player_layout.online_icon.allow_stretch = True
        self.player_layout.online_icon.size_hint_max = (15, 15)
        self.player_layout.online_icon.pos_hint = {"center_x": 0.5, "center_y": 0.752}
        self.player_layout.add_widget(self.player_layout.online_icon)

        self.player_layout.online_label = ParagraphLabel()
        self.player_layout.online_label.font_size = sp(19)
        self.player_layout.online_label.pos_hint = {"center_x": 0.523, "center_y": 0.755}
        self.player_layout.add_widget(self.player_layout.online_label)

        self.player_layout.uuid_header = HeaderLabel()
        self.player_layout.uuid_header.pos_hint = {"center_x": 0.5, "center_y": 0.66}
        self.player_layout.add_widget(self.player_layout.uuid_header)

        # Make this copyable text
        self.player_layout.uuid_label = ParagraphLabel()
        self.player_layout.uuid_label.pos_hint = {"center_x": 0.5, "center_y": 0.619}
        self.player_layout.add_widget(self.player_layout.uuid_label)

        self.player_layout.ip_header = HeaderLabel()
        self.player_layout.ip_header.pos_hint = {"center_x": 0.28, "center_y": 0.54}
        self.player_layout.add_widget(self.player_layout.ip_header)

        # Make this copyable text
        self.player_layout.ip_label = ParagraphLabel()
        self.player_layout.ip_label.font_size = sp(20)
        self.player_layout.ip_label.pos_hint = {"center_x": 0.28, "center_y": 0.499}
        self.player_layout.add_widget(self.player_layout.ip_label)

        self.player_layout.geo_header = HeaderLabel()
        self.player_layout.geo_header.pos_hint = {"center_x": 0.7, "center_y": 0.54}
        self.player_layout.add_widget(self.player_layout.geo_header)

        self.player_layout.geo_label = ParagraphLabel()
        self.player_layout.geo_label.halign = "center"
        self.player_layout.geo_label.pos_hint = {"center_x": 0.7, "center_y": 0.499}
        self.player_layout.add_widget(self.player_layout.geo_label)

        self.player_layout.access_header = HeaderLabel()
        self.player_layout.access_header.pos_hint = {"center_x": 0.5, "center_y": 0.4}
        self.player_layout.access_header.font_size = sp(20)
        self.player_layout.add_widget(self.player_layout.access_header)

        self.player_layout.access_label = ParagraphLabel()
        self.player_layout.access_label.halign = "left"
        self.player_layout.access_label.valign = "top"
        self.player_layout.access_label.text_size = (250, 300)
        self.player_layout.access_label.font_size = sp(19)
        self.player_layout.access_label.line_height = sp(1.4)
        self.player_layout.access_label.pos_hint = {"center_x": 0.465, "center_y": 0.11}
        self.player_layout.add_widget(self.player_layout.access_label)

        self.player_layout.access_line_1 = Image()
        self.player_layout.access_line_1.size_hint_max = (35, 35)
        self.player_layout.access_line_1.pos_hint = {"center_x": 0.165, "center_y": 0.29}
        self.player_layout.access_line_1.allow_stretch = True
        self.player_layout.access_line_1.source = os.path.join(constants.gui_assets, "access_active.png")
        self.player_layout.add_widget(self.player_layout.access_line_1)

        self.player_layout.access_line_2 = Image()
        self.player_layout.access_line_2.size_hint_max = (35, 35)
        self.player_layout.access_line_2.pos_hint = {"center_x": 0.165, "center_y": 0.24}
        self.player_layout.access_line_2.allow_stretch = True
        self.player_layout.access_line_2.source = os.path.join(constants.gui_assets, "access_active.png")
        self.player_layout.add_widget(self.player_layout.access_line_2)

        self.player_layout.access_line_3 = Image()
        self.player_layout.access_line_3.size_hint_max = (35, 35)
        self.player_layout.access_line_3.pos_hint = {"center_x": 0.165, "center_y": 0.19}
        self.player_layout.access_line_3.allow_stretch = True
        self.player_layout.access_line_3.source = os.path.join(constants.gui_assets, "access_active.png")
        self.player_layout.add_widget(self.player_layout.access_line_3)

        self.player_layout.access_icon = Image()
        self.player_layout.access_icon.size_hint_max = (30, 30)
        self.player_layout.access_icon.pos_hint = {"center_x": 0.165, "center_y": 0.338}
        self.player_layout.add_widget(self.player_layout.access_icon)
        # </editor-fold>


        # IP Layout
        # <editor-fold desc="IP Layout Widgets">
        self.ip_layout = RelativeLayout()
        self.ip_layout.id = 'ip_layout'

        self.ip_layout.header_icon = Image()
        self.ip_layout.header_icon.source = icon_path('ethernet.png')
        self.ip_layout.header_icon.allow_stretch = True
        self.ip_layout.header_icon.size_hint_max = (36, 36)
        self.ip_layout.header_icon.pos_hint = {"center_x": 0.5, "center_y": 0.808}
        self.ip_layout.add_widget(self.ip_layout.header_icon)

        # Make this copyable text
        self.ip_layout.name_label = HeaderLabel()
        self.ip_layout.name_label.pos_hint = {"center_x": 0.54, "center_y": 0.81}
        self.ip_layout.name_label.font_size = sp(25)
        self.ip_layout.add_widget(self.ip_layout.name_label)

        self.ip_layout.type_header = HeaderLabel()
        self.ip_layout.type_header.pos_hint = {"center_x": 0.28, "center_y": 0.64}
        self.ip_layout.add_widget(self.ip_layout.type_header)

        # Make ip copyable text
        self.ip_layout.type_label = ParagraphLabel()
        self.ip_layout.type_label.font_size = sp(20)
        self.ip_layout.type_label.pos_hint = {"center_x": 0.28, "center_y": 0.598}
        self.ip_layout.add_widget(self.ip_layout.type_label)

        self.ip_layout.affected_header = HeaderLabel()
        self.ip_layout.affected_header.pos_hint = {"center_x": 0.7, "center_y": 0.64}
        self.ip_layout.add_widget(self.ip_layout.affected_header)

        # Make ip copyable text
        self.ip_layout.affected_label = ParagraphLabel()
        self.ip_layout.affected_label.halign = "center"
        self.ip_layout.affected_label.font_size = sp(20)
        self.ip_layout.affected_label.pos_hint = {"center_x": 0.7, "center_y": 0.598}
        self.ip_layout.add_widget(self.ip_layout.affected_label)

        self.ip_layout.network_header = HeaderLabel()
        self.ip_layout.network_header.pos_hint = {"center_x": 0.5, "center_y": 0.458}
        self.ip_layout.add_widget(self.ip_layout.network_header)

        # Make ip copyable text
        self.ip_layout.network_label = ParagraphLabel()
        self.ip_layout.network_label.halign = "center"
        self.ip_layout.network_label.valign = "top"
        self.ip_layout.network_label.text_size = (400, 150)
        self.ip_layout.network_label.font_size = sp(20)
        self.ip_layout.network_label.line_height = sp(1.4)
        self.ip_layout.network_label.pos_hint = {"center_x": 0.5, "center_y": 0.3}
        self.ip_layout.add_widget(self.ip_layout.network_label)
        # </editor-fold>


        for widget in self.player_layout.children:
            constants.hide_widget(widget, True)
        for widget in self.ip_layout.children:
            constants.hide_widget(widget, True)

        self.add_widget(self.background)
        self.add_widget(self.blank_label)
        self.add_widget(self.player_layout)
        self.add_widget(self.ip_layout)
        # </editor-fold>


    # Actually updates data in panel based off of rule
    def update_panel(self, displayed_rule: acl.AclRule, rule_scope: str):

        self.displayed_scope = rule_scope
        filtered_name = displayed_rule.rule.replace("!g", "").replace("!w", "")
        panel_options = []

        # Player layout ------------------------------------------------------------------------------------------------
        if displayed_rule.rule_type == "player":

            # Effective access colors
            if displayed_rule.display_data['effective_access'] == "Operator access":
                widget_color = self.color_dict['blue']
                self.player_layout.access_icon.source = icon_path('promote.png')
            elif displayed_rule.display_data['effective_access'] == "No access":
                widget_color = self.color_dict['red']
                self.player_layout.access_icon.source = icon_path('close-circle-outline.png')
            else:
                widget_color = self.color_dict['purple']
                self.player_layout.access_icon.source = icon_path('chevron-up-circle-sharp.png')


            if self.displayed_type != "player":
                for widget in self.player_layout.children:
                    constants.hide_widget(widget, False)
                for widget in self.ip_layout.children:
                    constants.hide_widget(widget, True)


            # Change panel attributes ----------------------------------------------------------------------------------


            # Change name in header
            self.player_layout.name_label.text = filtered_name
            self.player_layout.name_label.texture_update()
            texture_size = 0.001 * self.player_layout.name_label.texture_size[0]
            self.player_layout.header_icon.pos_hint = {"center_x": 0.485 - texture_size, "center_y": 0.808}


            # Online status
            if acl.check_online(displayed_rule.rule):
                self.player_layout.online_label.color = self.color_dict['green']
                self.player_layout.online_icon.color = self.color_dict['green']
                self.player_layout.online_label.text = "Currently online"
                self.player_layout.online_icon.source = icon_path('radio-button-on-sharp.png')

            else:
                self.player_layout.online_label.color = self.color_dict['gray']
                self.player_layout.online_icon.color = self.color_dict['gray']
                try:
                    last_login = (dt.now() - dt.strptime(displayed_rule.extra_data['latest-login'], '%Y-%m-%d %H:%M:%S'))
                    d = {"days": last_login.days}
                    d["years"], rem = divmod(last_login.days, 365)
                    d["months"], rem = divmod(last_login.days, 30)
                    d["hours"], rem = divmod(last_login.seconds, 3600)
                    d["minutes"], d["seconds"] = divmod(rem, 60)

                    if d['years'] > 0:
                        time_formatted = (f"{d['years']} year{'s' if d['years'] > 1 else ''} " if d['years'] > 0 else "")
                    elif d['months'] > 0:
                        time_formatted = (f"{d['months']} month{'s' if d['months'] > 1 else ''} " if d['months'] > 0 else "")
                    else:
                        time_formatted = (f"{d['days']}d " if d['days'] > 0 else "") + (f"{d['hours']}h " if d['hours'] > 0 else "") + (f"{d['minutes']}m " if d['minutes'] > 0 and d['days'] == 0 else "")

                    if not time_formatted:
                        time_formatted = 'seconds '

                    self.player_layout.online_label.text = f"Last online {time_formatted}ago"

                except ValueError:
                    self.player_layout.online_label.text = "Last online unknown"

                self.player_layout.online_icon.source = icon_path('radio-button-off-sharp.png')

            self.player_layout.online_label.texture_update()
            texture_size = 0.001 * self.player_layout.online_label.texture_size[0]
            self.player_layout.online_icon.pos_hint = {"center_x": 0.492 - texture_size, "center_y": 0.752}


            # Change UUID
            self.player_layout.uuid_label.text = displayed_rule.extra_data['uuid']


            # Change last IP
            if displayed_rule.extra_data['latest-ip'].startswith("127."):
                self.player_layout.ip_label.text = displayed_rule.extra_data['latest-ip']
            else:
                self.player_layout.ip_label.text = displayed_rule.extra_data['latest-ip'].split(":")[0]


            # Change location
            if " - " in displayed_rule.extra_data['ip-geo']:
                self.player_layout.geo_label.text = displayed_rule.extra_data['ip-geo'].replace(" - ", "\n")
                self.player_layout.geo_label.pos_hint = {"center_x": 0.7, "center_y": 0.48}
            else:
                self.player_layout.geo_label.text = displayed_rule.extra_data['ip-geo']
                self.player_layout.geo_label.pos_hint = {"center_x": 0.7, "center_y": 0.499}
            self.player_layout.geo_label.font_size = sp(20) if len(displayed_rule.extra_data['ip-geo']) < 15 else sp(18)


            # Change effective access
            very_bold_font = os.path.join(constants.gui_assets, 'fonts', constants.fonts["bold"])
            final_text = f"[color={widget_color}][font={very_bold_font}][size={round(sp(21))}]{displayed_rule.display_data['effective_access']}[/size][/font][/color]"
            banned = False

            # Display ban data
            if displayed_rule.display_data['ip_ban'] and displayed_rule.display_data['ban']:
                final_text += f"\n[color={self.color_dict['red']}]Banned IP & user[/color]"
                banned = True
            elif displayed_rule.display_data['ip_ban']:
                final_text += f"\n[color={self.color_dict['red']}]Banned IP[/color]"
                banned = True
            elif displayed_rule.display_data['ban']:
                final_text += f"\n[color={self.color_dict['red']}]Banned user[/color]"
                banned = True
            else:
                final_text += "\n"

            # Display OP data
            final_text += (f"\n[color={self.color_dict['blue']}]Operator[/color]" if displayed_rule.display_data['op'] else "\n")

            # Whitelist data
            if screen_manager.current_screen.acl_object.server['whitelist']:
                self.player_layout.access_line_3.opacity = 1
                final_text += ("\n[color=" + (f"{self.color_dict['green']}]Whitelisted" if displayed_rule.display_data['wl'] else f"{self.color_dict['red']}]Not whitelisted") + "[/color]")
            else:
                self.player_layout.access_line_3.opacity = 0
                self.player_layout.access_line_1.source = os.path.join(constants.gui_assets, "access_active.png")
                self.player_layout.access_line_2.source = os.path.join(constants.gui_assets, "access_active.png")
                self.player_layout.access_line_3.source = os.path.join(constants.gui_assets, "access_active.png")

            self.player_layout.access_label.text = final_text


            # Adjust graphic data for access
            if screen_manager.current_screen.acl_object.server['whitelist']:
                if displayed_rule.display_data['wl']:
                    self.player_layout.access_line_1.source = os.path.join(constants.gui_assets, "access_active.png")
                    self.player_layout.access_line_2.source = os.path.join(constants.gui_assets, "access_active.png")
                    self.player_layout.access_line_3.source = os.path.join(constants.gui_assets, "access_active.png")
                else:
                    self.player_layout.access_line_1.source = os.path.join(constants.gui_assets, "access_inactive.png")
                    self.player_layout.access_line_2.source = os.path.join(constants.gui_assets, "access_inactive.png")
                    self.player_layout.access_line_3.source = os.path.join(constants.gui_assets, "access_inactive.png")

            if banned:
                self.player_layout.access_line_1.source = os.path.join(constants.gui_assets, "access_inactive.png")
            elif displayed_rule.display_data['wl']:
                self.player_layout.access_line_1.source = os.path.join(constants.gui_assets, "access_active.png")


            # Set header names
            self.player_layout.uuid_header.text = "UUID"
            self.player_layout.ip_header.text = "IP"
            self.player_layout.geo_header.text = "Location"
            self.player_layout.access_header.text = f"Access to '{screen_manager.current_screen.acl_object.server['name']}':"



            # Change colors based on rule access attributes ------------------------------------------------------------
            self.background.color = widget_color
            for widget in self.player_layout.children:

                if widget is self.player_layout.online_label or widget is self.player_layout.online_icon:
                    continue

                if widget.__class__.__name__ in ['Image', 'HeaderLabel']:
                    if widget in [self.player_layout.header_icon, self.player_layout.name_label]:
                        widget.color = constants.brighten_color(widget_color, 0.12)
                    elif widget in [self.player_layout.access_icon, self.player_layout.access_line_1, self.player_layout.access_line_2, self.player_layout.access_line_3]:
                        widget.color = constants.brighten_color(widget_color, 0.2)
                    else:
                        widget.color = constants.brighten_color(widget_color, 0.34)

                elif widget.__class__.__name__ == "ParagraphLabel":
                    widget.color = self.color_dict['gray'] if "unknown" in widget.text.lower() else widget.default_color



            # Generate panel options -----------------------------------------------------------------------------------
            if screen_manager.current_screen.current_list == "ops":
                panel_options.append("demote" if displayed_rule.display_data['op'] else "promote")

            elif screen_manager.current_screen.current_list == "bans":
                if displayed_rule.display_data['ip_ban'] and displayed_rule.display_data['ban']:
                    panel_options.append("pardon IP & user")
                elif displayed_rule.display_data['ip_ban']:
                    if not displayed_rule.display_data['ban']:
                        panel_options.append("ban user")
                    panel_options.append("pardon IP")
                elif displayed_rule.display_data['ban']:
                    panel_options.append("pardon user")
                else:
                    panel_options.append("ban user")

                if displayed_rule.extra_data['latest-ip'] != "Unknown" and not displayed_rule.display_data['ip_ban']:
                    panel_options.append("ban IP")

            elif screen_manager.current_screen.current_list == "wl":
                panel_options.append("restrict" if displayed_rule.display_data['wl'] else "permit")

            panel_options.append("localize rule" if rule_scope == "global" else "globalize rule")


        # IP Layout ----------------------------------------------------------------------------------------------------
        else:

            # Effective access colors
            if "whitelist" in displayed_rule.display_data['rule_info'].lower():
                widget_color = self.color_dict['blue']
            else:
                widget_color = self.color_dict['red']

            if not screen_manager.current_screen.acl_object.rule_in_acl('subnets', displayed_rule.rule):
                displayed_rule.display_data['rule_info'] = "Unaffected " + displayed_rule.display_data['rule_info'].split(" ")[0]
                displayed_rule.rule = displayed_rule.rule.replace("!w", "").replace("!g", "").strip()
                screen_manager.current_screen.displayed_rule = displayed_rule
                widget_color = self.color_dict['purple']

            if self.displayed_type != "ip":
                for widget in self.player_layout.children:
                    constants.hide_widget(widget, True)
                for widget in self.ip_layout.children:
                    constants.hide_widget(widget, False)



            # Change panel attributes ----------------------------------------------------------------------------------


            # Change IP address in header
            self.ip_layout.name_label.text = filtered_name
            self.ip_layout.name_label.texture_update()
            texture_size = 0.001 * self.ip_layout.name_label.texture_size[0]
            self.ip_layout.header_icon.pos_hint = {"center_x": 0.485 - texture_size, "center_y": 0.808}


            # Change rule type
            self.ip_layout.type_label.text = displayed_rule.display_data['rule_info']


            # Change affected users
            users = displayed_rule.display_data['affected_users']
            if users == 0:
                self.ip_layout.affected_label.text = "0 users"
                self.ip_layout.affected_label.color = self.color_dict['gray']
            else:
                self.ip_layout.affected_label.text = f"{users:,} user{'s' if users > 1 else ''}"
                self.ip_layout.affected_label.color = self.color_dict['green'] if "whitelist" in displayed_rule.display_data['rule_info'].lower() else self.color_dict['red']


            # Change network info
            ip_count = acl.count_subnet(displayed_rule.rule.replace("!w", "").replace("!g", "").strip())
            ips = displayed_rule.display_data['ip_range'].split(" - ")
            self.ip_layout.network_label.text = f"{ips[0]} [color=#696997]-[/color] {ips[1]}"
            self.ip_layout.network_label.text += f"\n[color={self.color_dict['gray']}]{displayed_rule.display_data['subnet_mask']}"
            self.ip_layout.network_label.text += f"  ({ip_count:,} IP{'s' if ip_count > 1 else ''})[/color]"



            # Set header names
            self.ip_layout.type_header.text = "Rule Type"
            self.ip_layout.affected_header.text = "Affected"
            self.ip_layout.network_header.text = "Network"


            # Change colors based on rule access attributes ------------------------------------------------------------
            self.background.color = widget_color
            for widget in self.ip_layout.children:
                if widget.__class__.__name__ in ['Image', 'HeaderLabel']:
                    if widget in [self.ip_layout.header_icon, self.ip_layout.name_label]:
                        widget.color = constants.brighten_color(widget_color, 0.12)
                    else:
                        widget.color = constants.brighten_color(widget_color, 0.34)


            # Generate panel options -----------------------------------------------------------------------------------
            if screen_manager.current_screen.current_list == "bans":
                after_text = 'subnet' if 'subnet' in displayed_rule.display_data['rule_info'].lower() else 'IP'
                if "unaffected" in displayed_rule.display_data['rule_info'].lower():
                    panel_options.append(f"ban {after_text}")
                    panel_options.append(f"whitelist {after_text}")

                else:
                    if "whitelist" in displayed_rule.display_data['rule_info'].lower():
                        panel_options.append("remove rule")
                        panel_options.append(f"ban {after_text}")
                    else:
                        panel_options.append(f"pardon {after_text}")
                        panel_options.append(f"whitelist {after_text}")

                    panel_options.append("localize rule" if rule_scope == "global" else "globalize rule")

        panel_options = panel_options if panel_options else ['no options']
        self.options.change_options(panel_options)
        self.displayed_type = displayed_rule.rule_type


    # Changes rule attributes from options drop-down
    def modify_rule(self, option: str):

        current_list = screen_manager.current_screen.current_list.lower().strip()
        acl_object = screen_manager.current_screen.acl_object
        original_name = acl_object.displayed_rule.rule
        filtered_name = acl_object.displayed_rule.rule.replace("!w", "").replace("!g", "").strip()
        new_name = original_name
        new_scope = self.displayed_scope
        banner_text = ""
        hover_attr = None
        reload_page = False
        localize = False

        try:
            ip_addr = acl_object.displayed_rule.extra_data['latest-ip'].split(":")[0].strip()
        except KeyError:
            ip_addr = ""


        # Global options
        if "local" in option or "global" in option:
            if "localize" in option:
                acl_object.add_global_rule(original_name, current_list, remove=True)

                # If rule localized, enable on current list
                if current_list == "ops":
                    acl_object.op_player(acl_object.displayed_rule.rule)
                elif current_list == "bans":
                    acl_object.ban_player(acl_object.displayed_rule.rule)
                elif current_list == "wl":
                    acl_object.whitelist_player(acl_object.displayed_rule.rule)

                hover_attr = (
                    icon_path("earth-strike.png"), 'LOCALIZE',
                    (0.439, 0.839, 1, 1) if current_list == "ops" else
                    (1, 0.5, 0.65, 1) if current_list == "bans" else
                    (0.3, 1, 0.6, 1)
                )
                banner_text = f"'{filtered_name}' is now locally applied"
                new_scope = "local"
                reload_page = True

            elif "globalize" in option:
                acl_object.add_global_rule(original_name, current_list, remove=False)
                hover_attr = (icon_path("earth-sharp.png"), 'GLOBALIZE', (0.953, 0.929, 0.38, 1))
                banner_text = f"'{filtered_name}' is now globally applied"
                new_scope = "global"
                reload_page = True


        # Operator options
        elif current_list == "ops":
            if "demote" in option:
                if self.displayed_scope == "global":
                    acl_object.add_global_rule(original_name, current_list, remove=True)
                else:
                    acl_object.op_player(original_name, remove=True)

                hover_attr = (icon_path("close-circle.png"), 'DEMOTE', (1, 0.5, 0.65, 1))
                banner_text = f"'{filtered_name}' was demoted"
                new_scope = "local"
                reload_page = True

            elif "promote" in option:
                acl_object.op_player(original_name, remove=False)
                hover_attr = (icon_path("promote.png"), 'PROMOTE', (0.3, 1, 0.6, 1))
                banner_text = f"'{filtered_name}' was promoted"
                reload_page = True


        # Ban options Player/IP
        elif current_list == "bans":
            if acl_object.displayed_rule.rule_type == "player":
                if "ban user" in option:
                    acl_object.ban_player(original_name, remove=False)
                    hover_attr = (icon_path("close-circle.png"), 'BAN', (1, 0.5, 0.65, 1))
                    banner_text = f"'{filtered_name}' is banned"
                    reload_page = True

                elif "ban IP" in option:
                    acl_object.ban_player(ip_addr, remove=False)

                    if self.displayed_scope == "global":
                        acl_object.add_global_rule(original_name, current_list, remove=True)

                    acl_object.ban_player(f"!w{ip_addr}", remove=True)
                    hover_attr = (icon_path("close-circle.png"), 'BAN', (1, 0.5, 0.65, 1))
                    banner_text = f"'{filtered_name}' is banned"
                    reload_page = True

                if "pardon IP" in option and "user" in option:
                    acl_object.ban_player([original_name, ip_addr], remove=True)

                    if self.displayed_scope == "global":
                        acl_object.add_global_rule(original_name, current_list, remove=True)

                    # Whitelist IP if it's still in the rule list
                    if ip_addr in acl.gen_iplist(acl_object.rules['subnets']):
                        acl_object.ban_player(f"!w{ip_addr}", remove=False)

                    hover_attr = (icon_path("lock-open.png"), 'PARDON', (0.3, 1, 0.6, 1))
                    banner_text = f"'{filtered_name}' is pardoned"
                    new_scope = "local"
                    reload_page = True

                elif "pardon user" in option:
                    if self.displayed_scope == "global":
                        acl_object.add_global_rule(original_name, current_list, remove=True)
                    else:
                        acl_object.ban_player(original_name, remove=True)

                    hover_attr = (icon_path("lock-open.png"), 'PARDON', (0.3, 1, 0.6, 1))
                    banner_text = f"'{filtered_name}' is pardoned"
                    new_scope = "local"
                    reload_page = True

                elif "pardon IP" in option:
                    acl_object.ban_player(ip_addr, remove=True)

                    # Whitelist IP if it's still in the rule list
                    if ip_addr in acl.gen_iplist(acl_object.rules['subnets']):
                        acl_object.ban_player(f"!w{ip_addr}", remove=False)

                    hover_attr = (icon_path("lock-open.png"), 'PARDON', (0.3, 1, 0.6, 1))
                    banner_text = f"'{filtered_name}' is pardoned"
                    new_scope = "local"
                    reload_page = True


            # IP rules
            else:
                if "ban" in option:
                    # If rule is global and ban is added, switch scope to local
                    if "whitelist" in acl_object.displayed_rule.display_data['rule_info'] and self.displayed_scope == "global":
                        new_scope = "local"

                    if "!w" in original_name:
                        acl_object.ban_player(original_name, remove=True)
                        acl_object.ban_player(filtered_name, remove=False)
                    else:
                        acl_object.ban_player(original_name, remove=False)
                    hover_attr = (icon_path("close-circle.png"), 'BAN', (1, 0.5, 0.65, 1))
                    banner_text = f"'{filtered_name}' is banned"
                    new_name = filtered_name
                    reload_page = True

                elif "pardon" in option:
                    if self.displayed_scope == "global":
                        acl_object.add_global_rule(original_name, current_list, remove=True)
                    else:
                        acl_object.ban_player(original_name, remove=True)

                    hover_attr = (icon_path("lock-open.png"), 'PARDON', (0.3, 1, 0.6, 1))
                    banner_text = f"'{filtered_name}' is pardoned"
                    new_scope = "local"
                    reload_page = True

                elif "remove" in option:
                    if self.displayed_scope == "global":
                        acl_object.add_global_rule(original_name, current_list, remove=True)
                    else:
                        acl_object.ban_player(original_name, remove=True)

                    hover_attr = (icon_path("shield-disabled-outline.png"), 'REMOVE', (0.7, 0.7, 1, 1))
                    banner_text = f"'{filtered_name}' was removed"
                    new_scope = "local"
                    reload_page = True

                elif "whitelist" in option:
                    # If rule is global and whitelist is added, switch scope to local
                    if "ban" in acl_object.displayed_rule.display_data['rule_info'] and self.displayed_scope == "global":
                        new_scope = "local"

                    acl_object.ban_player(original_name, remove=True)
                    acl_object.ban_player(f"!w{filtered_name}", remove=False)
                    hover_attr = (icon_path("shield-checkmark-outline.png"), 'WHITELIST', (0.439, 0.839, 1, 1))
                    banner_text = f"'{filtered_name}' is whitelisted"
                    new_name = f"!w{filtered_name}"
                    reload_page = True


        # Whitelist options
        elif current_list == "wl":
            if "restrict" in option:
                if self.displayed_scope == "global":
                    acl_object.add_global_rule(original_name, current_list, remove=True)
                else:
                    acl_object.whitelist_player(original_name, remove=True)

                hover_attr = (icon_path("close-circle.png"), 'RESTRICT', (1, 0.5, 0.65, 1))
                banner_text = f"'{filtered_name}' is restricted"
                new_scope = "local"
                reload_page = True

            elif "permit" in option:
                acl_object.whitelist_player(original_name, remove=False)
                hover_attr = (icon_path("checkmark-circle-sharp.png"), 'PERMIT', (0.3, 1, 0.6, 1))
                banner_text = f"'{filtered_name}' is permitted"
                reload_page = True


        if reload_page:

            screen_manager.current_screen.update_list(current_list, reload_children=False)

            Clock.schedule_once(
                functools.partial(
                    screen_manager.current_screen.show_banner,
                    hover_attr[2],
                    banner_text,
                    hover_attr[0],
                    2,
                    {"center_x": 0.5, "center_y": 0.965}
                ), 0
            )

            def trigger_highlight(*args):
                for rule_button in screen_manager.current_screen.scroll_layout.children:

                    if rule_button.rule.rule == original_name:
                        rule_button.highlight(rule_button.button.background_color, rule_button.text.color, hover_attr[2])

                    else:
                        rule_button.button.on_leave()
                        Animation.cancel_all(rule_button.button)
                        Animation.cancel_all(rule_button.text)
                        Animation.cancel_all(rule_button.icon)
                        rule_button.change_properties(rule_button.rule)

                    rule_button.button.ignore_hover = False

            Clock.schedule_once(trigger_highlight, 0)

        # Update display rule regardless of button pressed
        screen_manager.current_screen.update_user_panel(new_name, new_scope)

        # print(option)

class CreateServerAclScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'
        self._ignore_keys = ['tab']
        self.header = None
        self.search_bar = None
        self.whitelist_toggle = None
        self.scroll_widget = None
        self.scroll_layout = None
        self.blank_label = None
        self.search_label = None
        self.list_header = None
        self.controls_button = None
        self.user_panel = None
        self.show_panel = False

        self.acl_object = None
        self._hash = None
        self.current_list = None

        self.filter_text = ""
        self.currently_filtering = False


    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        super()._on_keyboard_down(keyboard, keycode, text, modifiers)

        if keycode[1] == 'h' and 'ctrl' in modifiers and not self.popup_widget:
            self.controls_button.button.trigger_action()

        # Press
        if keycode[1] == 'tab' and not self._input_focused and self.name == screen_manager.current_screen.name:
            for button in self.walk():
                try:
                    if button.id == "input_button":
                        button.force_click()
                        break
                except AttributeError:
                    continue


    def update_user_panel(self, rule_name: str, rule_scope: str):

        # Generate rule list count
        rule_count = len(self.scroll_widget.data)
        panel_check = rule_count > 0


        # Hide user panel if there are no items
        if panel_check != self.show_panel:

            for child in self.user_panel.children:

                # Figure out how to make this not bug out when transitioning between rules, specifically with blank_text
                if child.__class__.__name__ == "Label":
                    child.opacity = (1 if panel_check else 0)
                else:
                    Animation(opacity=(1 if panel_check else 0), duration=0.3).start(child)

                # Make sure self.options shows and hides properly
                for widget in self.user_panel.options.children:
                    constants.hide_widget(widget, panel_check)

            self.show_panel = panel_check


        # Update displayed data on user panel
        if rule_name:
            self.acl_object.display_rule(rule_name)
            self.user_panel.update_panel(self.acl_object.displayed_rule, rule_scope)


        # If rule is displayed
        if self.acl_object.displayed_rule:

            if self.user_panel.blank_label.opacity > 0:
                Animation.stop_all(self.user_panel.blank_label)
                constants.hide_widget(self.user_panel.blank_label, True)
                for child in self.user_panel.options.children:
                    constants.hide_widget(child, False)

        # If rule is not displayed
        else:

            if self.user_panel.blank_label.opacity == 0:
                constants.hide_widget(self.user_panel.blank_label, False)
                for child in self.user_panel.options.children:
                    constants.hide_widget(child, True)


        if not panel_check:
            for widget in self.user_panel.options.children:
                constants.hide_widget(widget, True)


        if self.acl_object.displayed_rule:
            Animation.stop_all(self.user_panel.blank_label)
            constants.hide_widget(self.user_panel.blank_label, True)
            self.user_panel.blank_label.opacity = 0


    # Filter data from search box
    def search_filter(self, query):

        def lock(*args):
            self.currently_filtering = False
            if self.filter_text != self.search_bar.text:
                self.search_filter(self.search_bar.text)

        # Prevent refreshes shorter than 0.5s
        if not self.currently_filtering:
            self.currently_filtering = True
            self.filter_text = query

            # Filter data

            # Reset scroll
            self.scroll_widget.scroll_y = 1

            total_list = [{'rule': rule} for rule in self.acl_object.list_items[self.current_list]['enabled']]
            total_list.extend([{'rule': rule} for rule in self.acl_object.list_items[self.current_list]['disabled']])

            original_len = len(total_list)

            if query:
                filtered_list = []
                for rule in total_list:
                    rule_obj = rule['rule']

                    # Name matches query
                    if query.lower().replace("!w", "").replace("!g", "") in rule_obj.rule.lower():
                        filtered_list.append(rule)

                    # Scope matches query
                    elif query.lower() == rule_obj.rule_scope:
                        filtered_list.append(rule)

                    # Rule type matches query
                    elif query.lower() == rule_obj.rule_type:
                        filtered_list.append(rule)

                    # Location matches query
                    else:
                        try:
                            location = acl.get_uuid(rule_obj.rule)['ip-geo']
                            if query.lower() in location.lower().replace(" - ", " ") and location != "Unknown":
                                filtered_list.append(rule)
                        except KeyError:
                            pass


                total_list = filtered_list
                del filtered_list

            # Show hint text if there are no rules

            self.set_data(total_list)


            # Show search label if it exists
            Animation.stop_all(self.search_label)
            if self.filter_text and len(self.scroll_widget.data) == 0 and original_len > 0:
                self.search_label.text = f"No results for '{self.filter_text}'"
                Animation(opacity=1, duration=0.2).start(self.search_label)
            else:
                Animation(opacity=0, duration=0.05).start(self.search_label)


            # Unlock the lock
            timer = threading.Timer(0.5, function=lock)
            timer.start()


    # ops, bans, wl
    def update_list(self, list_type: str, reload_children=True, reload_panel=False):

        if "op" in list_type:
            list_type = "ops"
        elif "ban" in list_type:
            list_type = "bans"
        else:
            list_type = "wl"

        # Reset scroll
        list_changed = False
        if self.current_list != list_type:
            list_changed = True
            self.scroll_widget.scroll_y = 1

        # Create list data with list type
        self.current_list = list_type

        # Check if there's an active filter
        if self.filter_text:
            self.search_filter(self.filter_text)
        else:
            total_list = [{'rule': rule} for rule in self.acl_object.list_items[list_type]['enabled']]
            total_list.extend([{'rule': rule} for rule in self.acl_object.list_items[list_type]['disabled']])

            self.set_data(total_list)

        rule_count = len(self.acl_object.rules[list_type])
        if list_type == "bans":
            rule_count += len(self.acl_object.rules['subnets'])


        # Modify header content
        very_bold_font = os.path.join(constants.gui_assets, 'fonts', constants.fonts["very-bold"])
        header_content = ('[color=#6A6ABA]No rules[/color]' if rule_count == 0 else f'[font={very_bold_font}]1[/font] rule' if rule_count == 1 else f'[font={very_bold_font}]{rule_count:,}[/font] rules')
        if list_type == "wl" and not self.acl_object.server['whitelist']:
            header_content += " (inactive)"

        # header_content = (" "*(len(header_content) - (55 if 'inactive' not in header_content else 50))) + header_content

        for child in self.header.children:
            if child.id == "text":
                child.text = header_content
                child.halign = "left"
                child.text_size[0] = 500
                child.x = Window.width / 2 + 240
                break

        # If there are no rules, say as much with a label
        constants.hide_widget(self.list_header.global_rule, rule_count == 0)
        constants.hide_widget(self.list_header.enabled_rule, rule_count == 0)
        constants.hide_widget(self.list_header.disabled_rule, rule_count == 0)

        if rule_count == 0:
            if self.blank_label.opacity < 1:
                self.blank_label.text = "No rules available, add them above"
                constants.hide_widget(self.blank_label, False)
                self.blank_label.opacity = 0
                Animation(opacity=1, duration=0.2).start(self.blank_label)
                Animation(opacity=0, duration=0.2).start(self.search_label)

        # If there are rules, display them here
        else:
            # Show search label if it exists
            Animation.stop_all(self.search_label)
            # print(len(self.scroll_widget.data))
            if self.filter_text and len(self.scroll_widget.data) == 0:
                self.search_label.text = f"No results for '{self.filter_text}'"
                Animation(opacity=1, duration=0.2).start(self.search_label)
            else:
                Animation(opacity=0, duration=0.2).start(self.search_label)

            self.list_header.remove_widget(self.list_header.enabled_rule)
            self.list_header.enabled_rule = RelativeLayout()
            self.list_header.enabled_rule.add_widget(
                BannerObject(
                    size=(120, 32),
                    color=(0.439, 0.839, 1, 1) if list_type == 'ops'
                    else (1, 0.5, 0.65, 1) if list_type == 'bans'
                    else (0.3, 1, 0.6, 1),

                    text="operator" if list_type == 'ops'
                    else "banned" if list_type == 'bans'
                    else "allowed",

                    icon="settings-sharp.png" if list_type == 'ops'
                    else "close-circle-sharp.png" if list_type == 'bans'
                    else "checkmark-circle-sharp.png"
                )
            )
            self.list_header.add_widget(self.list_header.enabled_rule)


            self.list_header.remove_widget(self.list_header.disabled_rule)
            self.list_header.disabled_rule = RelativeLayout()
            self.list_header.disabled_rule.add_widget(
                BannerObject(
                    size=(125, 32),
                    color=(0.6, 0.5, 1, 1) if list_type == 'ops'
                    else (0.3, 1, 0.6, 1) if list_type == 'bans'
                    else (1, 0.5, 0.65, 1) if self.acl_object.server['whitelist'] else(0.7, 0.7, 0.7, 1),

                    text="standard" if list_type == 'ops'
                    else "allowed" if list_type == 'bans'
                    else "restricted",

                    icon="person-circle-sharp.png" if list_type == 'ops'
                    else "checkmark-circle-sharp.png" if list_type == 'bans'
                    else "close-circle-sharp.png"
                )
            )
            self.list_header.add_widget(self.list_header.disabled_rule)

            constants.hide_widget(self.blank_label, True)

        # Change whitelist toggle visibility based on list_type
        constants.hide_widget(self.whitelist_toggle, list_type != 'wl')

        # Refresh all buttons
        if reload_children:
            for rule_button in self.scroll_layout.children:
                rule_button.change_properties(rule_button.rule)

            # gc.collect()

            # Dirty fix to hide grid resize that fixes RuleButton text.pos_hint x
            if list_changed:
                self.scroll_widget.opacity = 0
                self.scroll_layout.cols = 1
                self.resize_bind()
                def animate_grid(*args):
                    Animation.stop_all(self.scroll_widget)
                    Animation(opacity=1, duration=0.3).start(self.scroll_widget)
                Clock.schedule_once(animate_grid, 0)


        # Update displayed rule options
        if (self.acl_object.displayed_rule and list_changed) or (reload_panel and self.acl_object.displayed_rule):
            global_rules = acl.load_global_acl()
            self.acl_object.displayed_rule.acl_group = list_type
            rule_scope = acl.check_global_acl(global_rules, self.acl_object.displayed_rule).rule_scope
            self.update_user_panel(self.acl_object.displayed_rule.rule, rule_scope)


    def set_data(self, data):

        if self.scroll_layout:
            self.scroll_layout.rows = None

        self.scroll_widget.data = data

        if self.resize_bind:
            self.resize_bind()


    def generate_menu(self, **kwargs):

        # If self._hash doesn't match, set list to ops by default
        if self._hash != constants.new_server_info['_hash']:
            self.acl_object = constants.new_server_info['acl_object']
            self._hash = constants.new_server_info['_hash']
            self.current_list = 'ops'

        self.show_panel = False

        self.filter_text = ""
        self.currently_filtering = False


        # Scroll list
        self.scroll_widget = RecycleViewWidget(position=(0.5, 0.43), view_class=RuleButton)
        self.scroll_layout = RecycleGridLayout(spacing=[110, -15], size_hint_y=None, padding=[60, 20, 0, 30])
        test_rule = RuleButton()

        # Bind / cleanup height on resize
        def resize_scroll(*args):
            self.scroll_widget.height = Window.height // 1.65
            rule_width = test_rule.width + self.scroll_layout.spacing[0] + 2
            rule_width = int(((Window.width // rule_width) // 1) - 2)

            self.scroll_layout.cols = rule_width
            self.scroll_layout.rows = 2 if len(self.scroll_widget.data) <= rule_width else None

            self.user_panel.x = Window.width - (self.user_panel.size_hint_max[0] * 0.93)

            # Reposition header
            for child in self.header.children:
                if child.id == "text":
                    child.halign = "left"
                    child.text_size[0] = 500
                    child.x = Window.width / 2 + 240
                    break

            self.search_label.pos_hint = {"center_x": (0.28 if Window.width < 1300 else 0.5), "center_y": 0.42}
            self.search_label.text_size = (Window.width / 3, 500)


        self.resize_bind = lambda*_: Clock.schedule_once(functools.partial(resize_scroll), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        self.scroll_layout.bind(minimum_height=self.scroll_layout.setter('height'))
        self.scroll_layout.id = 'scroll_content'


        # Scroll gradient
        scroll_top = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.735}, pos=self.scroll_widget.pos, size=(self.scroll_widget.width // 1.5, 60))
        scroll_bottom = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.14}, pos=self.scroll_widget.pos, size=(self.scroll_widget.width // 1.5, -60))

        # Generate buttons on page load
        very_bold_font = os.path.join(constants.gui_assets, 'fonts', constants.fonts["very-bold"])
        selector_text = "operators" if self.current_list == "ops" else "bans" if self.current_list == "bans" else "whitelist"
        page_selector = DropButton(selector_text, (0.5, 0.89), options_list=['operators', 'bans', 'whitelist'], input_name='ServerAclTypeInput', x_offset=-210, facing='center', custom_func=self.update_list)
        header_content = ""
        self.header = HeaderText(header_content, '', (0, 0.89), fixed_x=True, no_line=True)


        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'
        float_layout.add_widget(self.header)


        # Search bar
        self.search_bar = AclInput(pos_hint={"center_x": 0.5, "center_y": 0.815})
        buttons.append(input_button('Add Rules...', (0.5, 0.815), input_name='AclInput'))


        # Whitelist toggle button
        def toggle_whitelist(boolean):
            self.acl_object.toggle_whitelist(boolean)

            Clock.schedule_once(
                functools.partial(
                    self.show_banner,
                    (0.553, 0.902, 0.675, 1) if boolean else (0.937, 0.831, 0.62, 1),
                    f"Server whitelist {'en' if boolean else 'dis'}abled",
                    "shield-checkmark-outline.png" if boolean else "shield-disabled-outline.png",
                    2,
                    {"center_x": 0.5, "center_y": 0.965}
                ), 0
            )

            # Update list
            self.update_list('wl', reload_children=True, reload_panel=True)

        self.whitelist_toggle = toggle_button('whitelist', (0.5, 0.89), default_state=self.acl_object.server['whitelist'], x_offset=-395, custom_func=toggle_whitelist)


        # Legend for rule types
        self.list_header = BoxLayout(orientation="horizontal", pos_hint={"center_x": 0.5, "center_y": 0.749}, size_hint_max=(400, 100))
        self.list_header.global_rule = RelativeLayout()
        self.list_header.global_rule.add_widget(BannerObject(size=(125, 32), color=test_rule.global_icon_color, text="global rule", icon="earth-sharp.png", icon_side="left"))
        self.list_header.add_widget(self.list_header.global_rule)

        self.list_header.enabled_rule = RelativeLayout()
        self.list_header.enabled_rule.add_widget(BannerObject(size=(120, 32), color=(1,1,1,1), text=" ", icon="add.png"))
        self.list_header.add_widget(self.list_header.enabled_rule)

        self.list_header.disabled_rule = RelativeLayout()
        self.list_header.disabled_rule.add_widget(BannerObject(size=(120, 32), color=(1,1,1,1), text=" ", icon="add.png"))
        self.list_header.add_widget(self.list_header.disabled_rule)


        # Add blank label to the center, then load self.gen_search_results()
        self.blank_label = Label()
        self.blank_label.text = ""
        self.blank_label.font_name = os.path.join(constants.gui_assets, 'fonts', constants.fonts['italic'])
        self.blank_label.pos_hint = {"center_x": 0.5, "center_y": 0.48}
        self.blank_label.font_size = sp(23)
        self.blank_label.opacity = 0
        self.blank_label.color = (0.6, 0.6, 1, 0.35)
        float_layout.add_widget(self.blank_label)


        # Lol search label idek
        self.search_label = Label()
        self.search_label.text = ""
        self.search_label.halign = "center"
        self.search_label.valign = "center"
        self.search_label.font_name = os.path.join(constants.gui_assets, 'fonts', constants.fonts['italic'])
        self.search_label.pos_hint = {"center_x": 0.28, "center_y": 0.42}
        self.search_label.font_size = sp(25)
        self.search_label.color = (0.6, 0.6, 1, 0.35)
        float_layout.add_widget(self.search_label)


        # Controls button
        def show_controls():

            controls_text = """This menu shows enabled rules from files like 'ops.json', and disabled rules as others who have joined. Global rules are applied to every server. Rules can be modified in a few different ways:
            
• Right-click a rule to view, and more options

• Left-click a rule to toggle permission

• Press middle-mouse to toggle globally

Rules can be filtered with the search box, and can be added with the 'ADD RULES' button or by pressing 'TAB'. The visible list can be switched between operators, bans, and the whitelist from the drop-down at the top."""

            Clock.schedule_once(
                functools.partial(
                    self.show_popup,
                    "controls",
                    "Controls",
                    controls_text,
                    (None)
                ),
                0
            )
        self.controls_button = IconButton('controls', {}, (70, 110), (None, None), 'question.png', clickable=True, anchor='right', click_func=show_controls)
        float_layout.add_widget(self.controls_button)


        # User panel
        self.user_panel = AclRulePanel()


        # Append scroll view items
        self.scroll_widget.add_widget(self.scroll_layout)
        float_layout.add_widget(self.scroll_widget)
        float_layout.add_widget(scroll_top)
        float_layout.add_widget(scroll_bottom)
        float_layout.add_widget(page_selector)
        float_layout.add_widget(self.list_header)
        float_layout.add_widget(self.search_bar)
        float_layout.add_widget(self.whitelist_toggle)
        float_layout.add_widget(self.user_panel)

        buttons.append(exit_button('Back', (0.5, 0.099), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)

        menu_name = f"Create '{constants.new_server_info['name']}', Access Control"
        float_layout.add_widget(generate_title(f"Access Control Manager: '{constants.new_server_info['name']}'"))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)

        # Generate page content
        self.update_list(self.current_list, reload_children=True)


        # Generate user panel info
        current_list = acl.deepcopy(self.acl_object.rules[self.current_list])
        if self.current_list == "bans":
            current_list.extend(acl.deepcopy(self.acl_object.rules['subnets']))

        if self.acl_object.displayed_rule and current_list:
            self.update_user_panel(self.acl_object.displayed_rule.rule, self.user_panel.displayed_scope)
        else:
            self.update_user_panel(None, None)

class CreateServerAclRuleScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'

        self._ignore_tree = True

        self.acl_input = None
        self.current_list = None
        self.acl_object = None


    def apply_rules(self):

        # Actually apply rules
        original_list = self.acl_object.process_query(self.acl_input.text, self.current_list)

        applied_list = []
        applied_list.extend(original_list['global'])
        applied_list.extend(original_list['local'])


        # Generate banner
        banner_text = "Added "

        if len(applied_list) == 1:
            banner_text += f"'{acl.get_uuid(applied_list[0])['name'] if applied_list[0].count('.') < 3 else applied_list[0]}'"
        elif len(applied_list) < 3:
            banner_text += f"'{', '.join([(acl.get_uuid(x)['name'] if x.count('.') < 3 else x) for x in applied_list[0:2]])}'"
        else:
            banner_text += f"'{acl.get_uuid(applied_list[0])['name'] if applied_list[0].count('.') < 3 else applied_list[0]}' and {len(applied_list) - 1:,} more"


        Clock.schedule_once(
            functools.partial(
                screen_manager.current_screen.show_banner,
                (0.553, 0.902, 0.675, 1),
                banner_text,
                "add-circle-sharp.png",
                2.5,
                {"center_x": 0.5, "center_y": 0.965}
            ), 0
        )

        # Return to previous screen
        self.acl_object.display_rule(applied_list[0])
        previous_screen()

        def update_panel(*args):
            screen_manager.current_screen.update_user_panel(applied_list[0], applied_list[0] in original_list['global'])

        Clock.schedule_once(update_panel, 0)

        # Prevent back button from going back to this screen
        for screen in constants.screen_tree:
            if screen == self.name:
                constants.screen_tree.remove(self.name)


    def generate_menu(self, **kwargs):
        # Generate buttons on page load

        class HintLabel(RelativeLayout):

            def icon_pos(self, *args):
                self.text.texture_update()
                self.icon.pos_hint = {"center_x": 0.57 - (0.005 * self.text.texture_size[0]), "center_y": 0.95}

            def __init__(self, pos, label, **kwargs):
                super().__init__(**kwargs)

                self.pos_hint = {"center_x": 0.5, "center_y": pos}
                self.size_hint_max = (100, 50)

                self.text = Label()
                self.text.id = 'text'
                self.text.size_hint = (None, None)
                self.text.markup = True
                self.text.halign = "center"
                self.text.valign = "center"
                self.text.text = "        " + label
                self.text.font_size = sp(22)
                self.text.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
                self.text.color = (0.6, 0.6, 1, 0.55)

                self.icon = Image()
                self.icon.id = 'icon'
                self.icon.source = os.path.join(constants.gui_assets, 'icons', 'information-circle-outline.png')
                self.icon.pos_hint = {"center_y": 0.95}
                self.icon.color = (0.6, 0.6, 1, 1)

                self.add_widget(self.text)
                self.add_widget(self.icon)

                self.bind(size=self.icon_pos)
                self.bind(pos=self.icon_pos)


        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'

        self.current_list = screen_manager.get_screen("CreateServerAclScreen").current_list
        self.acl_object = screen_manager.get_screen("CreateServerAclScreen").acl_object

        if self.current_list == "bans":
            header_message = "Enter usernames/IPs delimited, by, commas"
            float_layout.add_widget(HintLabel(0.464, "Use   [color=#FFFF33]!g <rule>[/color]   to apply globally on all servers"))
            float_layout.add_widget(HintLabel(0.374, "You can ban IP ranges/whitelist:   [color=#FF6666]192.168.0.0-150[/color], [color=#66FF88]!w 192.168.1.1[/color]"))
        else:
            header_message = "Enter usernames delimited, by, commas"
            float_layout.add_widget(HintLabel(0.425, "Use   [color=#FFFF33]!g <rule>[/color]   to apply globally on all servers"))

        float_layout.add_widget(InputLabel(pos_hint={"center_x": 0.5, "center_y": 0.72}))
        float_layout.add_widget(HeaderText(header_message, '', (0, 0.8)))
        self.acl_input = AclRuleInput(pos_hint={"center_x": 0.5, "center_y": 0.64}, text="")
        float_layout.add_widget(self.acl_input)

        buttons.append(next_button('Add Rules', (0.5, 0.24), True, next_screen='CreateServerAclScreen'))
        buttons.append(exit_button('Back', (0.5, 0.14), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)

        menu_name = f"Create '{constants.new_server_info['name']}', Access Control"
        list_name = "Operators" if self.current_list == "ops" else "Bans" if self.current_list == "bans" else "Whitelist"
        float_layout.add_widget(generate_title(f"Access Control Manager: Add {list_name}"))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)
        self.acl_input.grab_focus()



# Create Server Step 6:  Server Options --------------------------------------------------------------------------------

# Create ACL options, and Addon Options
class CreateServerOptionsScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'

    def generate_menu(self, **kwargs):

        # Scroll list
        scroll_widget = ScrollViewWidget()
        scroll_anchor = AnchorLayout()
        scroll_layout = GridLayout(cols=1, spacing=10, size_hint_max_x=1050, size_hint_y=None, padding=[0, 16, 0, 30])


        # Bind / cleanup height on resize
        def resize_scroll(call_widget, grid_layout, anchor_layout, *args):
            call_widget.height = Window.height // 2
            grid_layout.cols = 2 if Window.width > grid_layout.size_hint_max_x else 1

            def update_grid(*args):
                anchor_layout.size_hint_min_y = grid_layout.height

            Clock.schedule_once(update_grid, 0)


        self.resize_bind = lambda*_: Clock.schedule_once(functools.partial(resize_scroll, scroll_widget, scroll_layout, scroll_anchor), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        scroll_layout.bind(minimum_height=scroll_layout.setter('height'))
        scroll_layout.id = 'scroll_content'

        # Scroll gradient
        scroll_top = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.77}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, 60))
        scroll_bottom = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.272}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, -60))

        # Generate buttons on page load
        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'
        float_layout.add_widget(HeaderText(f"Optionally, configure additional properties", '', (0, 0.86)))

        # If server type != vanilla, append addon manger button and extend float_layout widget
        if constants.new_server_info['type'] != 'vanilla':
            sub_layout = ScrollItem()
            sub_layout.add_widget(main_button('Add-on Manager', (0.5, 0.5), 'extension-puzzle-sharp.png'))
            scroll_layout.add_widget(sub_layout)

        # Gamemode dropdown
        sub_layout = ScrollItem()
        sub_layout.add_widget(blank_input(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="gamemode"))
        sub_layout.add_widget(DropButton(constants.new_server_info['server_settings']['gamemode'], (0.5, 0.5), options_list=['survival', 'adventure', 'creative'], input_name='ServerModeInput'))
        scroll_layout.add_widget(sub_layout)

        # Difficulty dropdown
        sub_layout = ScrollItem()
        sub_layout.add_widget(blank_input(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="difficulty"))
        sub_layout.add_widget(DropButton(constants.new_server_info['server_settings']['difficulty'], (0.5, 0.5), options_list=['peaceful', 'easy', 'normal', 'hard', 'hardcore'], input_name='ServerDiffInput'))
        scroll_layout.add_widget(sub_layout)

        # Geyser switch for bedrock support
        if constants.version_check(constants.new_server_info['version'], ">=", "1.13.2")\
        and constants.new_server_info['type'].lower() in ['spigot', 'paper', 'fabric']:
            sub_layout = ScrollItem()
            sub_layout.add_widget(blank_input(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="bedrock support (geyser)"))
            sub_layout.add_widget(toggle_button('geyser_support', (0.5, 0.5), default_state=constants.new_server_info['server_settings']['geyser_support']))
            scroll_layout.add_widget(sub_layout)

        # Disable chat reporting by default
        if constants.version_check(constants.new_server_info['version'], ">=", "1.19")\
        and constants.new_server_info['type'].lower() != "vanilla":
            sub_layout = ScrollItem()
            sub_layout.add_widget(blank_input(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="disable chat reporting"))
            sub_layout.add_widget(toggle_button('chat_report', (0.5, 0.5), default_state=constants.new_server_info['server_settings']['disable_chat_reporting']))
            scroll_layout.add_widget(sub_layout)

        # PVP switch button
        sub_layout = ScrollItem()
        sub_layout.add_widget(blank_input(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="enable PVP"))
        sub_layout.add_widget(toggle_button('pvp', (0.5, 0.5), default_state=constants.new_server_info['server_settings']['pvp']))
        scroll_layout.add_widget(sub_layout)

        # Enable keep inventory
        if constants.version_check(constants.new_server_info['version'], ">=", "1.4.2"):
            sub_layout = ScrollItem()
            sub_layout.add_widget(blank_input(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="keep inventory"))
            sub_layout.add_widget(toggle_button('keep_inventory', (0.5, 0.5), default_state=constants.new_server_info['server_settings']['keep_inventory']))
            scroll_layout.add_widget(sub_layout)

        # Spawn protection switch button
        sub_layout = ScrollItem()
        sub_layout.add_widget(blank_input(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="enable spawn protection"))
        sub_layout.add_widget(toggle_button('spawn_protection', (0.5, 0.5), default_state=constants.new_server_info['server_settings']['spawn_protection']))
        scroll_layout.add_widget(sub_layout)

        # Enable daylight cycle
        if constants.version_check(constants.new_server_info['version'], ">=", "1.4.2"):
            label = "daylight & weather cycle" if constants.version_check(constants.new_server_info['version'], ">=", "1.11") else "daylight cycle"
            sub_layout = ScrollItem()
            sub_layout.add_widget(blank_input(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text=label))
            sub_layout.add_widget(toggle_button('daylight_weather_cycle', (0.5, 0.5), default_state=constants.new_server_info['server_settings']['daylight_weather_cycle']))
            scroll_layout.add_widget(sub_layout)

        # Spawn creatures switch button
        sub_layout = ScrollItem()
        sub_layout.add_widget(blank_input(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="spawn creatures"))
        sub_layout.add_widget(toggle_button('spawn_creatures', (0.5, 0.5), default_state=constants.new_server_info['server_settings']['spawn_creatures']))
        scroll_layout.add_widget(sub_layout)

        # Enable command blocks switch button
        if constants.version_check(constants.new_server_info['version'], ">=", "1.4.2"):
            sub_layout = ScrollItem()
            sub_layout.add_widget(blank_input(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="enable command blocks"))
            sub_layout.add_widget(toggle_button('command_blocks', (0.5, 0.5), default_state=constants.new_server_info['server_settings']['command_blocks']))
            scroll_layout.add_widget(sub_layout)

        # Random tick speed input
        if constants.version_check(constants.new_server_info['version'], ">=", "1.4.2"):
            sub_layout = ScrollItem()
            sub_layout.add_widget(ServerTickSpeedInput(pos_hint={"center_x": 0.5, "center_y": 0.5}, text=constants.new_server_info['server_settings']['random_tick_speed']))
            scroll_layout.add_widget(sub_layout)

        # Max player input
        sub_layout = ScrollItem()
        sub_layout.add_widget(ServerPlayerInput(pos_hint={"center_x": 0.5, "center_y": 0.5}, text=constants.new_server_info['server_settings']['max_players']))
        scroll_layout.add_widget(sub_layout)

        # Append scroll view items
        scroll_anchor.add_widget(scroll_layout)
        scroll_widget.add_widget(scroll_anchor)
        float_layout.add_widget(scroll_widget)
        float_layout.add_widget(scroll_top)
        float_layout.add_widget(scroll_bottom)

        buttons.append(next_button('Next', (0.5, 0.21), False, next_screen='CreateServerReviewScreen'))
        buttons.append(exit_button('Back', (0.5, 0.12), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)

        menu_name = f"Create '{constants.new_server_info['name']}'"
        float_layout.add_widget(page_counter(6, 7, (0, 0.868)))
        float_layout.add_widget(generate_title(menu_name))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)



# Create Server Step 6:  Add-on Options --------------------------------------------------------------------------------

class AddonButton(HoverButton):

    def toggle_installed(self, installed, *args):
        self.installed = installed
        self.install_image.opacity = 1 if installed and not self.show_type else 0
        self.install_label.opacity = 1 if installed and not self.show_type else 0
        self.title.text_size = (self.size_hint_max[0] * (0.7 if installed else 0.94), self.size_hint_max[1])
        self.background_normal = os.path.join(constants.gui_assets, f'{self.id}{"_installed" if self.installed and not self.show_type else ""}.png')
        self.resize_self()

    def animate_addon(self, image, color, **kwargs):
        image_animate = Animation(duration=0.05)

        def f(w):
            w.background_normal = image

        Animation(color=color, duration=0.06).start(self.title)
        Animation(color=color, duration=0.06).start(self.subtitle)

        a = Animation(duration=0.0)
        a.on_complete = functools.partial(f)

        image_animate += a

        image_animate.start(self)

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
        self.background_normal = os.path.join(constants.gui_assets, f'{self.id}.png')
        self.background_down = os.path.join(constants.gui_assets, f'{self.id}_click.png')


        # Loading stuffs
        self.original_subtitle = self.properties.subtitle if self.properties.subtitle else "Description unavailable"
        self.original_font = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["regular"]}.ttf')


        # Title of Addon
        self.title = Label()
        self.title.id = "title"
        self.title.halign = "left"
        self.title.color = self.color_id[1]
        self.title.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
        self.title.font_size = sp(25)
        self.title.text_size = (self.size_hint_max[0] * 0.94, self.size_hint_max[1])
        self.title.shorten = True
        self.title.markup = True
        self.title.shorten_from = "right"
        self.title.max_lines = 1
        self.title.text = f"{self.properties.name}  [color=#434368]-[/color]  {self.properties.author if self.properties.author else 'Unknown'}"
        self.add_widget(self.title)


        # Description of Addon
        self.subtitle = Label()
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
        self.install_image.source = os.path.join(constants.gui_assets, 'installed.png')
        self.install_image.opacity = 0
        self.add_widget(self.install_image)

        self.install_label = AlignLabel()
        self.install_label.halign = "right"
        self.install_label.valign = "middle"
        self.install_label.font_size = sp(18)
        self.install_label.color = self.color_id[1]
        self.install_label.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
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
            self.animate_addon(image=os.path.join(constants.gui_assets, f'{self.id}_hover.png'), color=self.color_id[0], hover_action=True)

    def on_leave(self, *args):
        if not self.ignore_hover:
            self.animate_addon(image=os.path.join(constants.gui_assets, f'{self.id}{"_installed" if self.installed and not self.show_type else ""}.png'), color=self.color_id[1], hover_action=False)

    def loading(self, load_state, *args):
        if load_state:
            self.subtitle.text = "Loading add-on info..."
            self.subtitle.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
        else:
            self.subtitle.text = self.original_subtitle
            self.subtitle.font_name = self.original_font

class CreateServerAddonScreen(MenuBackground):

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

        # Update page counter
        results = list(sorted(results, key=lambda d: d.name.lower()))
        self.last_results = results
        self.max_pages = (len(results) / self.page_size).__ceil__()
        self.current_page = 1 if self.current_page == 0 or new_search else self.current_page

        self.page_switcher.update_index(self.current_page, self.max_pages)
        page_list = results[(self.page_size * self.current_page) - self.page_size:self.page_size * self.current_page]

        self.scroll_layout.clear_widgets()
        # gc.collect()

        # Generate header
        addon_count = len(results)
        very_bold_font = os.path.join(constants.gui_assets, 'fonts', constants.fonts["very-bold"])
        header_content = "Add-on Queue  [color=#494977]-[/color]  " + ('[color=#6A6ABA]No items[/color]' if addon_count == 0 else f'[font={very_bold_font}]1[/font] item' if addon_count == 1 else f'[font={very_bold_font}]{addon_count:,}[/font] items')

        for child in self.header.children:
            if child.id == "text":
                child.text = header_content
                break


        # If there are no addons, say as much with a label
        if addon_count == 0:
            self.blank_label.text = "Import or Download add-ons below"
            constants.hide_widget(self.blank_label, False)
            self.blank_label.opacity = 0
            Animation(opacity=1, duration=0.2).start(self.blank_label)
            self.max_pages = 0
            self.current_page = 0

        # If there are addons, display them here
        else:
            constants.hide_widget(self.blank_label, True)

            # Create list of addon names
            installed_addon_names = [addon.name for addon in constants.new_server_info["addon_objects"]]

            # Clear and add all addons
            for x, addon_object in enumerate(page_list, 1):

                # Function to remove addon
                def remove_addon(index):
                    selected_button = [item for item in self.scroll_layout.walk() if item.__class__.__name__ == "AddonButton"][index-1]
                    addon = selected_button.properties

                    if len(addon.name) < 26:
                        addon_name = addon.name
                    else:
                        addon_name = addon.name[:23] + "..."

                    Clock.schedule_once(
                        functools.partial(
                            self.show_banner,
                            (0.937, 0.831, 0.62, 1),
                            f"Removed '{addon_name}' from the queue",
                            "remove-circle-sharp.png",
                            2.5,
                            {"center_x": 0.5, "center_y": 0.965}
                        ), 0.25
                    )

                    if addon in constants.new_server_info['addon_objects']:
                        constants.new_server_info['addon_objects'].remove(addon)
                        self.gen_search_results(constants.new_server_info['addon_objects'])

                        # Switch pages if page is empty
                        if (len(self.scroll_layout.children) == 0) and (len(constants.new_server_info['addon_objects']) > 0):
                            self.switch_page("left")

                    return addon, selected_button.installed


                # Activated when addon is clicked
                def view_addon(addon, index, *args):
                    selected_button = [item for item in self.scroll_layout.walk() if item.__class__.__name__ == "AddonButton"][index - 1]

                    # Possibly make custom popup that shows differently for Web and File addons
                    Clock.schedule_once(
                        functools.partial(
                            self.show_popup,
                            "query",
                            addon.name,
                            "Do you want to remove this add-on from the queue?",
                            (None, functools.partial(remove_addon, index))
                        ),
                        0
                    )


                # Add-on button click function
                self.scroll_layout.add_widget(
                    ScrollItem(
                        widget = AddonButton(
                            properties = addon_object,
                            installed = True,
                            fade_in = ((x if x <= 8 else 8) / self.anim_speed),

                            show_type = BannerObject(
                                pos_hint = {"center_x": 0.5, "center_y": 0.5},
                                size = (125 if addon_object.addon_object_type == "web" else 100, 32),
                                color = (0.647, 0.839, 0.969, 1) if addon_object.addon_object_type == "web" else (0.6, 0.6, 1, 1),
                                text = "download" if addon_object.addon_object_type == "web" else "import",
                                icon = "cloud-download-sharp.png" if addon_object.addon_object_type == "web" else "download.png",
                                icon_side = "right"
                            ),

                            click_function = functools.partial(
                                view_addon,
                                addon_object,
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
        self.page_switcher = None

        self.last_results = []
        self.page_size = 20
        self.current_page = 0
        self.max_pages = 0
        self.anim_speed = 10

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        super()._on_keyboard_down(keyboard, keycode, text, modifiers)

        # Press arrow keys to switch pages
        if keycode[1] in ['right', 'left'] and self.name == screen_manager.current_screen.name:
            self.switch_page(keycode[1])

    def generate_menu(self, **kwargs):

        # Scroll list
        scroll_widget = ScrollViewWidget(position=(0.5, 0.52))
        scroll_anchor = AnchorLayout()
        self.scroll_layout = GridLayout(cols=1, spacing=15, size_hint_max_x=1250, size_hint_y=None, padding=[0, 30, 0, 30])


        # Bind / cleanup height on resize
        def resize_scroll(call_widget, grid_layout, anchor_layout, *args):
            call_widget.height = Window.height // 1.85
            grid_layout.cols = 2 if Window.width > grid_layout.size_hint_max_x else 1
            self.anim_speed = 13 if Window.width > grid_layout.size_hint_max_x else 10

            def update_grid(*args):
                anchor_layout.size_hint_min_y = grid_layout.height

            Clock.schedule_once(update_grid, 0)


        self.resize_bind = lambda*_: Clock.schedule_once(functools.partial(resize_scroll, scroll_widget, self.scroll_layout, scroll_anchor), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        self.scroll_layout.bind(minimum_height=self.scroll_layout.setter('height'))
        self.scroll_layout.id = 'scroll_content'


        # Scroll gradient
        scroll_top = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.795}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, 60))
        scroll_bottom = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.27}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, -60))

        # Generate buttons on page load
        addon_count = len(constants.new_server_info['addon_objects'])
        very_bold_font = os.path.join(constants.gui_assets, 'fonts', constants.fonts["very-bold"])
        header_content = "Add-on Queue  [color=#494977]-[/color]  " + ('[color=#6A6ABA]No items[/color]' if addon_count == 0 else f'[font={very_bold_font}]1[/font] item' if addon_count == 1 else f'[font={very_bold_font}]{addon_count}[/font] items')
        self.header = HeaderText(header_content, '', (0, 0.89))

        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'
        float_layout.add_widget(self.header)


        # Add blank label to the center, then load self.gen_search_results()
        self.blank_label = Label()
        self.blank_label.text = "Import or Download add-ons below"
        self.blank_label.font_name = os.path.join(constants.gui_assets, 'fonts', constants.fonts['italic'])
        self.blank_label.pos_hint = {"center_x": 0.5, "center_y": 0.55}
        self.blank_label.font_size = sp(24)
        self.blank_label.color = (0.6, 0.6, 1, 0.35)
        float_layout.add_widget(self.blank_label)

        self.page_switcher = PageSwitcher(0, 0, (0.5, 0.887), self.switch_page)


        # Append scroll view items
        scroll_anchor.add_widget(self.scroll_layout)
        scroll_widget.add_widget(scroll_anchor)
        float_layout.add_widget(scroll_widget)
        float_layout.add_widget(scroll_top)
        float_layout.add_widget(scroll_bottom)
        float_layout.add_widget(self.page_switcher)

        bottom_buttons = RelativeLayout()
        bottom_buttons.size_hint_max_x = 312
        bottom_buttons.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        bottom_buttons.add_widget(main_button('Import', (0, 0.202), 'download-outline.png', width=300, icon_offset=-115, auto_adjust_icon=True))
        bottom_buttons.add_widget(main_button('Download', (1, 0.202), 'cloud-download-outline.png', width=300, icon_offset=-115, auto_adjust_icon=True))
        buttons.append(exit_button('Back', (0.5, 0.11), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)
        float_layout.add_widget(bottom_buttons)

        menu_name = f"Create '{constants.new_server_info['name']}', Add-ons"
        float_layout.add_widget(generate_title(f"Add-on Manager: '{constants.new_server_info['name']}'"))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)

        # Automatically generate results (installed add-ons) on page load
        self.gen_search_results(constants.new_server_info['addon_objects'])

class CreateServerAddonSearchScreen(MenuBackground):

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
            # gc.collect()


            # Generate header
            addon_count = len(results)
            very_bold_font = os.path.join(constants.gui_assets, 'fonts', constants.fonts["very-bold"])
            search_text = self.search_bar.previous_search if (len(self.search_bar.previous_search) <= 25) else self.search_bar.previous_search[:22] + "..."
            header_content = f"Search for '{search_text}'  [color=#494977]-[/color]  " + ('[color=#6A6ABA]No results[/color]' if addon_count == 0 else f'[font={very_bold_font}]1[/font] item' if addon_count == 1 else f'[font={very_bold_font}]{addon_count:,}[/font] items')

            for child in self.header.children:
                if child.id == "text":
                    child.text = header_content
                    break


            # If there are no addons, say as much with a label
            if addon_count == 0:
                self.blank_label.text = "there are no items to display"
                constants.hide_widget(self.blank_label, False)
                self.blank_label.opacity = 0
                Animation(opacity=1, duration=0.2).start(self.blank_label)
                self.max_pages = 0
                self.current_page = 0

            # If there are addons, display them here
            else:
                constants.hide_widget(self.blank_label, True)

                # Create list of addon names
                installed_addon_names = [addon.name for addon in constants.new_server_info["addon_objects"]]

                # Clear and add all addons
                for x, addon_object in enumerate(page_list, 1):


                    # Function to download addon info
                    def load_addon(addon, index):
                        selected_button = [item for item in self.scroll_layout.walk() if item.__class__.__name__ == "AddonButton"][index-1]

                        # Cache updated addon info into button, or skip if it's already cached
                        if selected_button.properties:
                            if not selected_button.properties.versions or not selected_button.properties.description:
                                new_addon_info = addons.get_addon_info(addon, constants.new_server_info)
                                selected_button.properties = new_addon_info

                        Clock.schedule_once(functools.partial(selected_button.loading, False), 1)

                        return selected_button.properties, selected_button.installed


                    # Function to install addon
                    def install_addon(index):
                        selected_button = [item for item in self.scroll_layout.walk() if item.__class__.__name__ == "AddonButton"][index-1]
                        addon = selected_button.properties
                        selected_button.toggle_installed(not selected_button.installed)

                        if len(addon.name) < 26:
                            addon_name = addon.name
                        else:
                            addon_name = addon.name[:23] + "..."

                        # Install
                        if selected_button.installed:
                            constants.new_server_info["addon_objects"].append(addons.get_addon_url(addon, constants.new_server_info))

                            Clock.schedule_once(
                                functools.partial(
                                    self.show_banner,
                                    (0.553, 0.902, 0.675, 1),
                                    f"Added '{addon_name}' to the queue",
                                    "add-circle-sharp.png",
                                    2.5,
                                    {"center_x": 0.5, "center_y": 0.965}
                                ), 0.25
                            )

                        # Uninstall
                        else:
                            for installed_addon_object in constants.new_server_info["addon_objects"]:
                                if installed_addon_object.name == addon.name:
                                    constants.new_server_info["addon_objects"].remove(installed_addon_object)

                                    Clock.schedule_once(
                                        functools.partial(
                                            self.show_banner,
                                            (0.937, 0.831, 0.62, 1),
                                            f"Removed '{addon_name}' from the queue",
                                            "remove-circle-sharp.png",
                                            2.5,
                                            {"center_x": 0.5, "center_y": 0.965}
                                        ), 0.25
                                    )

                                    break

                        return addon, selected_button.installed


                    # Activated when addon is clicked
                    def view_addon(addon, index, *args):
                        selected_button = [item for item in self.scroll_layout.walk() if item.__class__.__name__ == "AddonButton"][index - 1]

                        selected_button.loading(True)

                        Clock.schedule_once(
                            functools.partial(
                                self.show_popup,
                                "addon",
                                " ",
                                " ",
                                (None, functools.partial(install_addon, index)),
                                functools.partial(load_addon, addon, index)
                            ),
                            0
                        )


                    # Add-on button click function
                    self.scroll_layout.add_widget(
                        ScrollItem(
                            widget = AddonButton(
                                properties = addon_object,
                                installed = addon_object.name in installed_addon_names,
                                fade_in = ((x if x <= 8 else 8) / self.anim_speed),
                                click_function = functools.partial(
                                    view_addon,
                                    addon_object,
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
        if keycode[1] in ['right', 'left'] and self.name == screen_manager.current_screen.name:
            self.switch_page(keycode[1])
        elif keycode[1] == "tab" and self.name == screen_manager.current_screen.name:
            for widget in self.search_bar.children:
                try:
                    if widget.id == "search_input":
                        widget.grab_focus()
                        break
                except AttributeError:
                    pass


    def generate_menu(self, **kwargs):

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

            Clock.schedule_once(update_grid, 0)


        self.resize_bind = lambda*_: Clock.schedule_once(functools.partial(resize_scroll, scroll_widget, self.scroll_layout, scroll_anchor), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        self.scroll_layout.bind(minimum_height=self.scroll_layout.setter('height'))
        self.scroll_layout.id = 'scroll_content'

        # Scroll gradient
        scroll_top = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.715}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, 60))
        scroll_bottom = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.17}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, -60))

        # Generate buttons on page load
        addon_count = 0
        very_bold_font = os.path.join(constants.gui_assets, 'fonts', constants.fonts["very-bold"])
        header_content = "Add-on Search"
        self.header = HeaderText(header_content, '', (0, 0.89))

        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'
        float_layout.add_widget(self.header)

        # Add blank label to the center
        self.blank_label = Label()
        self.blank_label.text = "search for add-ons above"
        self.blank_label.font_name = os.path.join(constants.gui_assets, 'fonts', constants.fonts['italic'])
        self.blank_label.pos_hint = {"center_x": 0.5, "center_y": 0.48}
        self.blank_label.font_size = sp(24)
        self.blank_label.color = (0.6, 0.6, 1, 0.35)
        float_layout.add_widget(self.blank_label)


        search_function = addons.search_addons
        self.search_bar = search_input(return_function=search_function, server_info=constants.new_server_info, pos_hint={"center_x": 0.5, "center_y": 0.795})
        self.page_switcher = PageSwitcher(0, 0, (0.5, 0.805), self.switch_page)


        # Append scroll view items
        scroll_anchor.add_widget(self.scroll_layout)
        scroll_widget.add_widget(scroll_anchor)
        float_layout.add_widget(scroll_widget)
        float_layout.add_widget(scroll_top)
        float_layout.add_widget(scroll_bottom)
        float_layout.add_widget(self.search_bar)
        float_layout.add_widget(self.page_switcher)

        buttons.append(exit_button('Back', (0.5, 0.12), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)

        menu_name = f"Create '{constants.new_server_info['name']}', Add-ons, Download"
        float_layout.add_widget(generate_title(f"Add-on Manager: '{constants.new_server_info['name']}'"))
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



# Create Server Step 7 (end):  Server Review ---------------------------------------------------------------------------

# Create demo of how the server will appear in the Server Manager:
class ServerDemoInput(BaseInput):

    def resize_self(self, *args):
        offset = 9.45 if self.type_image.type_label.text in ["vanilla", "paper"]\
            else 9.6 if self.type_image.type_label.text == "forge"\
            else 9.35 if self.type_image.type_label.text == "craftbukkit"\
            else 9.55

        self.type_image.image.x = self.width+self.x-self.type_image.image.width-self.padding_x[0]+10
        self.type_image.image.y = self.y+(self.padding_y[0]/2.7)

        self.type_image.type_label.x = self.width+self.x-(self.padding_x[0]*offset)
        self.type_image.type_label.y = self.y+(self.padding_y[0]/6.9)

        self.type_image.version_label.x = self.width+self.x-(self.padding_x[0]*offset)
        self.type_image.version_label.y = self.y-(self.padding_y[0]*0.85)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.halign = "left"
        self.properties = {"type": "", "version": "", "name": ""}
        self.padding_x = 30
        self.padding_y = 24.5
        self.font_size = sp(25)
        self.size_hint_max = (580, 80)
        self.hint_text_color = (0.65, 0.65, 1, 1)
        self.background_normal = os.path.join(constants.gui_assets, 'server_preview.png')
        self.title_text = ""
        self.hint_text = ""

        # Type icon and info
        with self.canvas.after:
            self.type_image = RelativeLayout()
            self.type_image.image = Image(source=None)
            self.type_image.image.allow_stretch = True
            self.type_image.image.size = (62, 62)
            self.type_image.image.color = (0.65, 0.65, 1, 1)

            def TemplateLabel():
                template_label = AlignLabel()
                template_label.halign = "right"
                template_label.valign = "middle"
                template_label.text_size = template_label.size
                template_label.font_size = sp(18)
                template_label.color = self.foreground_color
                template_label.font_name = self.font_name
                template_label.width = 200
                return template_label

            self.type_image.version_label = TemplateLabel()
            self.type_image.version_label.color = (0.6, 0.6, 1, 0.6)
            self.type_image.type_label = TemplateLabel()
            self.type_image.type_label.font_size = sp(22)

            self.bind(pos=self.resize_self)

    # Make the text box non-interactive
    def on_enter(self, value):
        return

    def on_touch_down(self, touch):
        self.focus = False

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        return

    def insert_text(self, substring, from_undo=False):
        return
def server_demo_input(pos_hint, properties):
    demo_input = ServerDemoInput()
    demo_input.properties = properties
    demo_input.pos_hint = pos_hint
    demo_input.hint_text = properties['name']
    demo_input.type_image.version_label.text = properties['version']
    demo_input.type_image.type_label.text = properties['type'].lower().replace("craft", "")
    demo_input.type_image.image.source = os.path.join(constants.gui_assets, 'icons', 'big', f'{properties["type"]}_small.png')
    return demo_input

class CreateServerReviewScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'

    def generate_menu(self, **kwargs):

        # Scroll list
        scroll_widget = ScrollViewWidget()
        scroll_anchor = AnchorLayout()
        scroll_layout = GridLayout(cols=1, spacing=10, size_hint_max_x=1050, size_hint_y=None, padding=[0, -10, 0, 60])


        # Bind / cleanup height on resize
        def resize_scroll(call_widget, grid_layout, anchor_layout, *args):
            call_widget.height = Window.height // 2.05
            call_widget.pos_hint = {"center_y": 0.51}
            grid_layout.cols = 2 if Window.width > grid_layout.size_hint_max_x else 1

            def update_grid(*args):
                anchor_layout.size_hint_min_y = grid_layout.height

            Clock.schedule_once(update_grid, 0)


        self.resize_bind = lambda*_: Clock.schedule_once(functools.partial(resize_scroll, scroll_widget, scroll_layout, scroll_anchor), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        scroll_layout.bind(minimum_height=scroll_layout.setter('height'))
        scroll_layout.id = 'scroll_content'

        # Scroll gradient
        scroll_top = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.735}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, 60))
        scroll_bottom = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.272}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, -60))

        # Generate buttons on page load
        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'
        float_layout.add_widget(HeaderText(f"Please verify your configuration", '', (0, 0.89), no_line=True))

        pgh_font = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["mono-medium"]}.otf')


        # Create and add paragraphs to GridLayout
        def create_paragraph(name, text, cid):

            # Dirty fix to anchor paragraphs to the top
            def repos(p, s, *args):
                if scroll_layout.cols == 2:
                    if s.height != scroll_layout._rows[cid]:
                        p.y = scroll_layout._rows[cid] - s.height

                    if cid == 0:
                        for child in scroll_layout.children:
                            if child != s and child.x == s.x:
                                p2 = child.children[0]
                                p2.y = p.y
                                break
                else:
                    p.y = 0

            sub_layout = ScrollItem()
            content_size = sp(22)
            content_height = len(text.splitlines()) * (content_size + sp(9))
            paragraph = paragraph_object(size=(485, content_height), name=name, content=text, font_size=content_size, font=pgh_font)
            sub_layout.height = paragraph.height + 60

            sub_layout.bind(pos=functools.partial(repos, paragraph, sub_layout, cid))
            sub_layout.bind(size=functools.partial(repos, paragraph, sub_layout, cid))

            sub_layout.add_widget(paragraph)
            scroll_layout.add_widget(sub_layout)



        # ----------------------------------------------- General ------------------------------------------------------
        content = ""
        content += f"[color=6666AA]Name:      [/color]{constants.new_server_info['name']}\n"
        content += f"[color=6666AA]Type:      [/color]{constants.new_server_info['type'].title()}\n"
        content += f"[color=6666AA]Version:   [/color]{constants.new_server_info['version']}"
        if constants.new_server_info['build']:
            content += f" ({constants.new_server_info['build']})"
        content += "\n\n"
        if constants.new_server_info['server_settings']['world'] == "world":
            content += f"[color=6666AA]World:     [/color]Create a new world\n"
            if constants.new_server_info['server_settings']['level_type']:
                content += f"[color=6666AA]Type:      [/color]{constants.new_server_info['server_settings']['level_type'].title()}\n"
            if constants.new_server_info['server_settings']['seed']:
                content += f"[color=6666AA]Seed:      [/color]{constants.new_server_info['server_settings']['seed']}\n"
        else:
            box_text = os.path.join(*Path(os.path.abspath(constants.new_server_info['server_settings']['world'])).parts[-2:])
            box_text = box_text[:30] + "..." if len(box_text) > 30 else box_text
            content += f"[color=6666AA]World:     [/color]{box_text}\n"

        create_paragraph('general', content, 0)
        # --------------------------------------------------------------------------------------------------------------



        # ----------------------------------------------- Options ------------------------------------------------------
        content = ""
        content += f"[color=6666AA]Gamemode:             [/color]{constants.new_server_info['server_settings']['gamemode'].title()}\n"
        content += f"[color=6666AA]Difficulty:           [/color]{constants.new_server_info['server_settings']['difficulty'].title()}\n"
        content += f"[color=6666AA]PVP:                  {'[/color]Enabled' if constants.new_server_info['server_settings']['pvp'] else 'Disabled[/color]'}\n"
        content += f"[color=6666AA]Spawn protection:     {'[/color]Enabled' if constants.new_server_info['server_settings']['spawn_protection'] else 'Disabled[/color]'}"

        content += "\n\n"

        if constants.version_check(constants.new_server_info['version'], ">=", "1.4.2"):
            content += f"[color=6666AA]Keep inventory:       {'[/color]Enabled' if constants.new_server_info['server_settings']['keep_inventory'] else 'Disabled[/color]'}\n"

        content += f"[color=6666AA]Spawn creatures:      {'[/color]Enabled' if constants.new_server_info['server_settings']['spawn_creatures'] else 'Disabled[/color]'}\n"

        if constants.version_check(constants.new_server_info['version'], ">=", "1.4.2"):
            if constants.version_check(constants.new_server_info['version'], ">=", "1.11"):
                content += f"[color=6666AA]Daylight/weather:     {'[/color]Enabled' if constants.new_server_info['server_settings']['daylight_weather_cycle'] else 'Disabled[/color]'}\n"
            else:
                content += f"[color=6666AA]Daylight cycle:       {'[/color]Enabled' if constants.new_server_info['server_settings']['daylight_weather_cycle'] else 'Disabled[/color]'}\n"

        content += f"[color=6666AA]Command blocks:       {'[/color]Enabled' if constants.new_server_info['server_settings']['command_blocks'] else 'Disabled[/color]'}\n"

        if constants.version_check(constants.new_server_info['version'], ">=", "1.19") and constants.new_server_info['type'].lower() != "vanilla":
            content += f"[color=6666AA]Chat reporting:       {'[/color]Enabled' if constants.new_server_info['server_settings']['disable_chat_reporting'] else 'Disabled[/color]'}\n"

        if constants.version_check(constants.new_server_info['version'], ">=", "1.4.2"):
            content += f"[color=6666AA]Random tick speed:    [/color]{constants.new_server_info['server_settings']['random_tick_speed']} ticks"

        create_paragraph('options', content, 0)
        # --------------------------------------------------------------------------------------------------------------



        # ----------------------------------------------- Network ------------------------------------------------------
        formatted_ip = ("localhost" if not constants.new_server_info['ip'] else constants.new_server_info['ip']) + f":{constants.new_server_info['port']}"
        max_plr = constants.new_server_info['server_settings']['max_players']
        formatted_players = (max_plr + (' players' if int(max_plr) != 1 else ' player'))
        content = ""
        content += f"[color=6666AA]Server IP:      [/color]{formatted_ip}\n"
        content += f"[color=6666AA]Max players:    [/color]{formatted_players}\n"
        if constants.new_server_info['server_settings']['geyser_support']:
            content += f"[color=6666AA]Geyser:         [/color]Enabled"

        content += "\n\n"

        content += f"[color=6666AA]MOTD:\n[/color]{constants.new_server_info['server_settings']['motd']}"

        content += "\n\n\n"

        rule_count = constants.new_server_info['acl_object'].count_rules()
        if rule_count['total'] > 0:
            content += f"[color=6666AA]          Access Control Rules[/color]"

            if rule_count['ops'] > 0:
                content += "\n\n"
                content += f"[color=6666AA]Operators ({rule_count['ops']:,}):[/color]\n"
                content += '    ' + '\n    '.join([rule.rule for rule in constants.new_server_info['acl_object'].rules['ops']])

            if rule_count['bans'] > 0:
                content += "\n\n"
                content += f"[color=6666AA]Bans ({rule_count['bans']:,}):[/color]\n"
                bans = acl.deepcopy(constants.new_server_info['acl_object'].rules['bans'])
                bans.extend(acl.deepcopy(constants.new_server_info['acl_object'].rules['subnets']))
                content += '    ' + '\n    '.join([rule.rule if '!w' not in rule.rule else rule.rule.replace('!w','').strip()+' (whitelist)' for rule in bans])

            if rule_count['wl'] > 0:
                content += "\n\n"
                content += f"[color=6666AA]Whitelist ({rule_count['wl']:,}):[/color]\n"
                content += '    ' + '\n    '.join([rule.rule for rule in constants.new_server_info['acl_object'].rules['wl']])

        create_paragraph('network', content, 1)
        # --------------------------------------------------------------------------------------------------------------



        # ------------------------------------------------ Addons ------------------------------------------------------
        if len(constants.new_server_info['addon_objects']) > 0:
            content = ""
            addons_sorted = {'import': [], 'download': []}
            [addons_sorted['import' if addon.addon_object_type == 'file' else 'download'].append(addon.name) for addon in constants.new_server_info['addon_objects']]

            if len(addons_sorted['download']) > 0:
                content += f"[color=6666AA]Add-ons to download ({len(addons_sorted['download']):,}):[/color]\n"
                content += '    ' + '\n    '.join([(item[:32]+'...' if len(item) > 35 else item) for item in addons_sorted['download']])

                if len(addons_sorted['import']) > 0:
                    content += "\n\n"

            if len(addons_sorted['import']) > 0:
                content += f"[color=6666AA]Add-ons to import ({len(addons_sorted['import']):,}):[/color]\n"
                content += '    ' + '\n    '.join([(item[:32]+'...' if len(item) > 35 else item) for item in addons_sorted['import']])

            create_paragraph('add-ons', content, 1)
        # --------------------------------------------------------------------------------------------------------------



        # Append scroll view items
        scroll_anchor.add_widget(scroll_layout)
        scroll_widget.add_widget(scroll_anchor)
        float_layout.add_widget(scroll_widget)
        float_layout.add_widget(scroll_top)
        float_layout.add_widget(scroll_bottom)


        # Server Preview Box
        float_layout.add_widget(server_demo_input(pos_hint={"center_x": 0.5, "center_y": 0.81}, properties=constants.new_server_info))


        buttons.append(main_button('Create Server', (0.5, 0.22), 'checkmark-circle-outline.png'))
        buttons.append(exit_button('Back', (0.5, 0.12), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)

        menu_name = f"Create '{constants.new_server_info['name']}'"
        float_layout.add_widget(page_counter(7, 7, (0, 0.815)))
        float_layout.add_widget(generate_title(menu_name))
        float_layout.add_widget(generate_footer(f"{menu_name}, Verify"))

        self.add_widget(float_layout)


# Create Server Progress Screen ----------------------------------------------------------------------------------------
class CreateServerProgressScreen(ProgressScreen):

    # Only replace this function when making a child screen
    # Set fail message in child functions to trigger an error
    def contents(self):

        def before_func(*args):

            # First, clean out any existing server in temp folder
            constants.safe_delete(constants.tmpsvr)

            if not constants.app_online:
                self.execute_error("An internet connection is required to continue\n\nVerify connectivity and try again")
            else:
                constants.folder_check(constants.tmpsvr)

        # Original is percentage before this function, adjusted is a percent of hooked value
        def adjust_percentage(*args):
            original = self.last_progress
            adjusted = args[0]
            total = args[1] * 0.01
            final = original + round(adjusted * total)
            if final < 0:
                final = original
            self.progress_bar.update_progress(final)


        self.page_contents = {

            # Page name
            'title': f"Creating '{constants.new_server_info['name']}'",

            # Header text
            'header': "Sit back and relax, it's automation time...",

            # Tuple of tuples for steps (label, function, percent)
            # Percent of all functions must total 100
            # Functions must return True, or default error will be executed
            'default_error': 'There was an issue, please try again later',

            'function_list': (),

            # Function to run before steps (like checking for an internet connection)
            'before_function': before_func,

            # Function to run after everything is complete (like cleaning up the screen tree) will only run if no error
            'after_function': functools.partial(open_server, constants.new_server_info['name'], True, f"'{constants.new_server_info['name']}' was created successfully"),

            # Screen to go to after complete
            'next_screen': None
        }

        # Create function list
        function_list = [
            ('Verifying Java installation', functools.partial(constants.java_check, functools.partial(adjust_percentage, 30)), 0),
            ("Downloading 'server.jar'", functools.partial(constants.download_jar, functools.partial(adjust_percentage, 30)), 0)
        ]

        download_addons = False
        needs_installed = False

        if constants.new_server_info['type'] != 'vanilla':
            download_addons = constants.new_server_info['addon_objects'] or constants.new_server_info['server_settings']['disable_chat_reporting'] or constants.new_server_info['server_settings']['geyser_support'] or (constants.new_server_info['type'] == 'fabric')
            needs_installed = constants.new_server_info['type'] in ['forge', 'fabric']

        if needs_installed:
            function_list.append((f'Installing {constants.new_server_info["type"].title()}', functools.partial(constants.install_server), 10 if download_addons else 20))

        if download_addons:
            function_list.append(('Add-oning add-ons', functools.partial(constants.iter_addons, functools.partial(adjust_percentage, 10 if needs_installed else 20)), 0))

        function_list.append(('Applying server configuration', functools.partial(constants.generate_server_files), 10 if (download_addons or needs_installed) else 20))


        function_list.append(('Creating initial back-up', functools.partial(constants.create_backup), 10 if (download_addons or needs_installed) else 20))


        self.page_contents['function_list'] = tuple(function_list)

# </editor-fold> ///////////////////////////////////////////////////////////////////////////////////////////////////////




# =============================================== Server Manager =======================================================
# <editor-fold desc="Server Manager">

# Import Server --------------------------------------------------------------------------------------------------------

class ServerImportScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'

        self.layout = None
        self.button_layout = None
        self.page_counter = None
        self.input_type = None
        self.input = None
        self.next_button = None


    def load_input(self, input_type, *args):
        self.input_type = input_type
        self.button_layout.clear_widgets()
        self.page_counter.clear_widgets()
        self.layout.remove_widget(self.page_counter)

        # Change the input based on input_type
        self.page_counter = page_counter(2, 2, (0, 0.768))
        self.button_layout.opacity = 0
        self.add_widget(self.page_counter)


        if input_type == "external":
            self.button_layout.add_widget(ServerImportPathInput(pos_hint={"center_x": 0.5, "center_y": 0.47}))
            self.button_layout.add_widget(input_button('Browse...', (0.5, 0.47), ('dir', constants.userDownloads if os.path.isdir(constants.userDownloads) else constants.home), input_name='ServerImportPathInput', title='Select a Server Folder'))

        elif input_type == "backup":
            self.button_layout.add_widget(ServerImportBackupInput(pos_hint={"center_x": 0.5, "center_y": 0.47}))
            start_path = constants.backupFolder if os.path.isdir(constants.backupFolder) else constants.userDownloads if os.path.isdir(constants.userDownloads) else constants.home
            self.button_layout.add_widget(input_button('Browse...', (0.5, 0.47), ('file', start_path), input_name='ServerImportBackupInput', title='Select an Auto-MCS back-up file', ext_list=['*.amb', '*.tgz']))


        # Auto-launch popup
        try:
            for item in self.button_layout.children[0].children:
                if item.id == "input_button":
                    Clock.schedule_once(item.force_click, 0)
                    Clock.schedule_once(item.on_leave, 0.01)
                    break
        except AttributeError:
            pass


        # def set_import_path(*args):
        #     for item in self.button_layout.children:
        #         if "ServerImport" in item.__class__.__name__:
        #             constants.import_data['path'] = item.selected_server


        self.button_layout.add_widget(InputLabel(pos_hint={"center_x": 0.5, "center_y": 0.56}))
        self.next_button = next_button('Next', (0.5, 0.24), True, next_screen='ServerImportProgressScreen')
        # self.next_button.children[2].bind(on_press=set_import_path)
        self.button_layout.add_widget(self.next_button)
        Animation(opacity=1, duration=0.5).start(self.button_layout)


    def generate_menu(self, **kwargs):

        # Reset import path
        constants.import_data = {'name': None, 'path': None}
        constants.safe_delete(constants.tempDir)

        # Generate buttons on page load
        buttons = []
        self.layout = FloatLayout()
        self.layout.id = 'content'

        # Prevent server creation if offline
        if not constants.app_online:
            self.layout.add_widget(HeaderText("Importing a server requires an internet connection", '', (0, 0.6)))
            buttons.append(exit_button('Back', (0.5, 0.35)))

        # Regular menus
        else:
            self.layout.add_widget(HeaderText("Which server do you wish to import?", '', (0, 0.76)))
            buttons.append(main_button('Import external server', (0.5, 0.5), 'folder-outline.png', click_func=functools.partial(self.load_input, 'external')))
            buttons.append(main_button('Import Auto-MCS back-up', (0.5, 0.38), 'backup-icon.png', click_func=functools.partial(self.load_input, 'backup')))
            self.layout.add_widget(exit_button('Back', (0.5, 0.14), cycle=True))
            self.page_counter = page_counter(1, 2, (0, 0.768))
            self.add_widget(self.page_counter)

        self.button_layout = FloatLayout()
        for button in buttons:
            self.button_layout.add_widget(button)

        self.layout.add_widget(self.button_layout)
        self.layout.add_widget(generate_title('Server Manager: Import Server'))
        self.layout.add_widget(generate_footer('Server Manager, Import server'))

        self.add_widget(self.layout)

class ServerImportProgressScreen(ProgressScreen):

    # Only replace this function when making a child screen
    # Set fail message in child functions to trigger an error
    def contents(self):

        def before_func(*args):

            # First, clean out any existing server in temp folder
            constants.safe_delete(constants.tempDir)

            if not constants.app_online:
                self.execute_error("An internet connection is required to continue\n\nVerify connectivity and try again")
            else:
                constants.folder_check(constants.tmpsvr)

        # Original is percentage before this function, adjusted is a percent of hooked value
        def adjust_percentage(*args):
            original = self.last_progress
            adjusted = args[0]
            total = args[1] * 0.01
            final = original + round(adjusted * total)
            if final < 0:
                final = original
            self.progress_bar.update_progress(final)


        self.page_contents = {

            # Page name
            'title': f"Importing '{constants.import_data['name']}'",

            # Header text
            'header': "Sit back and relax, it's automation time...",

            # Tuple of tuples for steps (label, function, percent)
            # Percent of all functions must total 100
            # Functions must return True, or default error will be executed
            'default_error': 'There was an issue, please try again later',

            'function_list': (),

            # Function to run before steps (like checking for an internet connection)
            'before_function': before_func,

            # Function to run after everything is complete (like cleaning up the screen tree) will only run if no error
            'after_function': functools.partial(open_server, constants.import_data['name'], True, f"'{constants.import_data['name']}' was imported successfully"),

            # Screen to go to after complete
            'next_screen': None
        }

        is_backup_file = ((constants.import_data['path'].endswith(".tgz") or constants.import_data['path'].endswith(".amb")) and os.path.isfile(constants.import_data['path']))

        # Create function list
        function_list = [
            ('Verifying Java installation', functools.partial(constants.java_check, functools.partial(adjust_percentage, 30)), 0),
            ('Importing server', functools.partial(constants.scan_import, is_backup_file, functools.partial(adjust_percentage, 30)), 0),
            ('Validating configuration', functools.partial(constants.finalize_import, functools.partial(adjust_percentage, 20)), 0),
            ('Creating initial back-up', functools.partial(constants.create_backup, True), 20)
        ]

        self.page_contents['function_list'] = tuple(function_list)



# Server Manager Overview ----------------------------------------------------------------------------------------------

# Opens server in panel, and updates Server Manager current_server
def open_server(server_name, wait_page_load=False, show_banner='', *args):
    def next_screen(*args):
        print(vars(constants.server_manager.current_server))
        if constants.server_manager.current_server.name != server_name:
            while constants.server_manager.current_server.name != server_name:
                time.sleep(0.005)
        screen_manager.current = 'ServerViewScreen'

        if show_banner:
            Clock.schedule_once(
                functools.partial(
                    screen_manager.current_screen.show_banner,
                    (0.553, 0.902, 0.675, 1),
                    show_banner,
                    "checkmark-circle-sharp.png",
                    2.5,
                    {"center_x": 0.5, "center_y": 0.965}
                ), 0
            )

        constants.screen_tree = ['MainMenuScreen', 'ServerManagerScreen']

    constants.server_manager.open_server(server_name)
    Clock.schedule_once(next_screen, 0.8 if wait_page_load else 0)

class ServerButton(HoverButton):

    class ParagraphLabel(Label, HoverBehavior):

        def on_mouse_pos(self, *args):

            if "ServerViewScreen" in screen_manager.current_screen.name and self.copyable:
                try:
                    super().on_mouse_pos(*args)
                except:
                    pass

        # Hover stuffies
        def on_enter(self, *args):

            if self.copyable:
                self.outline_width = 0
                self.outline_color = constants.brighten_color(self.color, 0.05)
                Animation(outline_width=1, duration=0.03).start(self)

        def on_leave(self, *args):

            if self.copyable:
                Animation.stop_all(self)
                self.outline_width = 0

        # Normal stuffies
        def on_ref_press(self, *args):
            if not self.disabled:
                Clock.schedule_once(
                    functools.partial(
                        screen_manager.current_screen.show_banner,
                        (0.85, 0.65, 1, 1),
                        "Copied IP address to clipboard",
                        "link-sharp.png",
                        2,
                        {"center_x": 0.5, "center_y": 0.965}
                    ), 0
                )

                Clipboard.copy(re.sub("\[.*?\]","",self.text.split(" ")[-1].strip()))


        def ref_text(self, *args):

            if '[ref=' not in self.text and '[/ref]' not in self.text and self.copyable:
                self.text = f'[ref=none]{self.text.strip()}[/ref]'
            elif '[/ref]' in self.text:
                self.text = self.text.replace("[/ref]", "") + "[/ref]"


        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.markup = True
            self.copyable = True
            self.bind(text=self.ref_text)

    def toggle_favorite(self, favorite, *args):
        self.favorite = favorite
        self.color_id = [(0.05, 0.05, 0.1, 1), constants.brighten_color((0.85, 0.6, 0.9, 1) if self.favorite else (0.65, 0.65, 1, 1), 0.07)]
        self.title.text_size = (self.size_hint_max[0] * (0.7 if favorite else 0.94), self.size_hint_max[1])
        self.background_normal = os.path.join(constants.gui_assets, f'{self.id}{"_favorite" if self.favorite else ""}.png')
        self.resize_self()

    def animate_button(self, image, color, **kwargs):
        image_animate = Animation(duration=0.05)

        def f(w):
            w.background_normal = image

        Animation(color=color, duration=0.06).start(self.title)
        Animation(color=self.run_color if (self.running and not self.hovered) else color, duration=0.06).start(self.subtitle)
        Animation(color=color, duration=0.06).start(self.type_image.image)
        if self.type_image.version_label.__class__.__name__ == "AlignLabel":
            Animation(color=color, duration=0.06).start(self.type_image.version_label)
        Animation(color=color, duration=0.06).start(self.type_image.type_label)

        a = Animation(duration=0.0)
        a.on_complete = functools.partial(f)

        image_animate += a

        image_animate.start(self)

    def resize_self(self, *args):

        # Title and description
        padding = 2.17
        self.title.pos = (self.x + (self.title.text_size[0] / padding) - (6 if self.favorite else 0) + 30, self.y + 31)
        self.subtitle.pos = (self.x + (self.subtitle.text_size[0] / padding) - 1 + 30 - 100, self.y + 8)


        offset = 9.45 if self.type_image.type_label.text in ["vanilla", "paper"]\
            else 9.6 if self.type_image.type_label.text == "forge"\
            else 9.35 if self.type_image.type_label.text == "craftbukkit"\
            else 9.55


        self.type_image.image.x = self.width + self.x - (self.type_image.image.width) - 13
        self.type_image.image.y = self.y + ((self.height / 2) - (self.type_image.image.height / 2))

        self.type_image.type_label.x = self.width + self.x - (self.padding_x * offset) - self.type_image.width - 83
        self.type_image.type_label.y = self.y + (self.height * 0.05)

        # Update label
        if self.type_image.version_label.__class__.__name__ == "AlignLabel":
            self.type_image.version_label.x = self.width + self.x - (self.padding_x * offset) - self.type_image.width - 83
            self.type_image.version_label.y = self.y - (self.height / 3.2)

        # Banner version object
        else:
            self.type_image.version_label.x = self.width + self.x - (self.padding_x * offset) - self.type_image.width - 130
            self.type_image.version_label.y = self.y - (self.height / 3.2) - 2


        # Favorite button
        self.favorite_layout.size_hint_max = (self.size_hint_max[0], self.size_hint_max[1])
        self.favorite_layout.pos = (self.pos[0] - 6, self.pos[1] + 13)


        # Highlight border
        self.highlight_border.pos = self.pos

    def highlight(self):
        def next_frame(*args):
            Animation.stop_all(self.highlight_border)
            self.highlight_border.opacity = 1
            Animation(opacity=0, duration=0.7).start(self.highlight_border)

        Clock.schedule_once(next_frame, 0)

    def update_subtitle(self, run_data=None, last_modified=None):
        if run_data:
            self.running = True
            self.subtitle.copyable = True
            self.subtitle.color = self.run_color
            self.subtitle.default_opacity = 0.8
            self.subtitle.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
            if 'ngrok' in run_data['network']['address']['ip'].lower():
                text = run_data['network']['address']['ip']
            else:
                text = ':'.join(run_data['network']['address'].values())
            self.subtitle.text = f"Running  [font={self.icons}]N[/font]  {text.replace('127.0.0.1', 'localhost')}"
        else:
            self.running = False
            self.subtitle.copyable = False
            if last_modified:
                self.original_subtitle = backup.convert_date(last_modified)
            self.subtitle.color = self.color_id[1]
            self.subtitle.default_opacity = 0.56
            self.subtitle.font_name = self.original_font
            self.subtitle.text = self.original_subtitle

        self.subtitle.opacity = self.subtitle.default_opacity

    def __init__(self, server_object, click_function=None, fade_in=0.0, highlight=None, update_banner="", view_only=False, **kwargs):
        super().__init__(**kwargs)

        self.view_only = view_only

        if self.view_only:
            self.ignore_hover = True

        self.favorite = server_object.favorite
        self.properties = server_object
        self.border = (-5, -5, -5, -5)
        self.color_id = [(0.05, 0.05, 0.1, 1), constants.brighten_color((0.85, 0.6, 0.9, 1) if self.favorite else (0.65, 0.65, 1, 1), 0.07)]
        self.run_color = (0.529, 1, 0.729, 1)
        self.running = server_object.running and server_object.run_data
        self.pos_hint = {"center_x": 0.5, "center_y": 0.6}
        self.size_hint_max = (580, 80)
        self.id = "server_button"

        if not self.view_only:
            self.background_normal = os.path.join(constants.gui_assets, f'{self.id}.png')
            self.background_down = os.path.join(constants.gui_assets, f'{self.id}{"_favorite" if self.favorite else ""}_click.png')
        else:
            self.background_normal = os.path.join(constants.gui_assets, f'{self.id}_ro.png')
            self.background_down = os.path.join(constants.gui_assets, f'{self.id}{"_favorite" if self.favorite else "_ro"}.png')

        self.icons = os.path.join(constants.gui_assets, 'fonts', constants.fonts['icons'])


        # Loading stuffs
        self.original_subtitle = backup.convert_date(server_object.last_modified)
        self.original_font = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["regular"]}.ttf')


        # Title of Server
        self.title = Label()
        self.title.id = "title"
        self.title.halign = "left"
        self.title.color = self.color_id[1]
        self.title.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
        self.title.font_size = sp(25)
        self.title.text_size = (self.size_hint_max[0] * 0.94, self.size_hint_max[1])
        self.title.shorten = True
        self.title.markup = True
        self.title.shorten_from = "right"
        self.title.max_lines = 1
        self.title.text = server_object.name
        self.add_widget(self.title)


        # Server last modified date formatted
        if self.view_only:
            self.subtitle = self.ParagraphLabel()
        else:
            self.subtitle = Label()
        self.subtitle.size = (300, 30)
        self.subtitle.id = "subtitle"
        self.subtitle.halign = "left"
        self.subtitle.valign = "center"
        self.subtitle.font_size = sp(21)
        self.subtitle.text_size = (self.size_hint_max[0] * 0.91, self.size_hint_max[1])
        self.subtitle.shorten = True
        self.subtitle.markup = True
        self.subtitle.shorten_from = "right"
        self.subtitle.max_lines = 1

        if self.running:
            self.subtitle.copyable = True
            self.subtitle.color = self.run_color
            self.subtitle.default_opacity = 0.8
            self.subtitle.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
            if 'ngrok' in server_object.run_data['network']['address']['ip'].lower():
                text = server_object.run_data['network']['address']['ip']
            else:
                text = ':'.join(server_object.run_data['network']['address'].values())
            self.subtitle.text = f"Running  [font={self.icons}]N[/font]  {text.replace('127.0.0.1', 'localhost')}"
        else:
            self.subtitle.copyable = False
            self.subtitle.color = self.color_id[1]
            self.subtitle.default_opacity = 0.56
            self.subtitle.font_name = self.original_font
            self.subtitle.text = self.original_subtitle

        self.subtitle.opacity = self.subtitle.default_opacity

        self.add_widget(self.subtitle)



        # Type icon and info
        self.type_image = RelativeLayout()
        self.type_image.width = 400
        self.type_image.image = Image(source=os.path.join(constants.gui_assets, 'icons', 'big', f'{server_object.type}_small.png'))
        self.type_image.image.allow_stretch = True
        self.type_image.image.size_hint_max = (65, 65)
        self.type_image.image.color = self.color_id[1]
        self.type_image.add_widget(self.type_image.image)

        def TemplateLabel():
            template_label = AlignLabel()
            template_label.halign = "right"
            template_label.valign = "middle"
            template_label.text_size = template_label.size
            template_label.font_size = sp(19)
            template_label.color = self.color_id[1]
            template_label.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
            template_label.width = 150
            return template_label


        if update_banner:
            self.type_image.version_label = RelativeLayout()
            self.type_image.version_label.add_widget(
                BannerObject(
                    pos_hint={"center_x": 1, "center_y": 0.5},
                    size=(100, 30),
                    color=(0.647, 0.839, 0.969, 1),
                    text= ('   ' + update_banner + '  ') if update_banner.startswith('b-') else update_banner,
                    icon="arrow-up-circle.png",
                    icon_side="left"
                )
            )

        else:
            self.type_image.version_label = TemplateLabel()
            self.type_image.version_label.color = self.color_id[1]
            self.type_image.version_label.text = server_object.version.lower()
            self.type_image.version_label.opacity = 0.6


        self.type_image.type_label = TemplateLabel()
        self.type_image.type_label.text = server_object.type.lower().replace("craft", "")
        self.type_image.type_label.font_size = sp(23)
        self.type_image.add_widget(self.type_image.version_label)
        self.type_image.add_widget(self.type_image.type_label)
        self.add_widget(self.type_image)


        # Favorite button
        self.favorite_layout = RelativeLayout()
        favorite = None
        if not view_only:
            try:
                favorite = functools.partial(screen_manager.current_screen.favorite, server_object.name)
            except AttributeError:
                pass

        if self.favorite:
            self.favorite_button = IconButton('', {}, (0, 0), (None, None), 'heart-sharp.png', clickable=not self.view_only, force_color=[[(0.05, 0.05, 0.1, 1), (0.85, 0.6, 0.9, 1)], 'pink'], anchor='right', click_func=favorite)
        else:
            self.favorite_button = IconButton('', {}, (0, 0), (None, None), 'heart-outline.png', clickable=not self.view_only, anchor='right', click_func=favorite)

        self.favorite_layout.add_widget(self.favorite_button)
        self.add_widget(self.favorite_layout)


        # Highlight border
        self.highlight_layout = RelativeLayout()
        self.highlight_border = Image()
        self.highlight_border.keep_ratio = False
        self.highlight_border.allow_stretch = True
        self.highlight_border.color = constants.brighten_color(self.color_id[1], 0.1)
        self.highlight_border.opacity = 0
        self.highlight_border.source = os.path.join(constants.gui_assets, 'server_button_highlight.png')
        self.highlight_layout.add_widget(self.highlight_border)
        self.highlight_layout.width = self.size_hint_max[0]
        self.highlight_layout.height = self.size_hint_max[1]
        self.add_widget(self.highlight_layout)



        # Toggle favorite stuffies
        self.bind(pos=self.resize_self)
        if self.favorite:
            self.toggle_favorite(self.favorite)

        # If click_function
        if click_function and not view_only:
            self.bind(on_press=click_function)



        # Animate opacity
        if fade_in > 0:
            self.opacity = 0
            self.title.opacity = 0

            Animation(opacity=1, duration=fade_in).start(self)
            Animation(opacity=1, duration=fade_in).start(self.title)
            Animation(opacity=self.subtitle.default_opacity, duration=fade_in).start(self.subtitle)

        if highlight:
            self.highlight()

    def on_enter(self, *args):
        if not self.ignore_hover:
            self.animate_button(image=os.path.join(constants.gui_assets, f'{self.id}{"_favorite" if self.favorite else ""}_hover.png'), color=self.color_id[0], hover_action=True)

    def on_leave(self, *args):
        if not self.ignore_hover:
            self.animate_button(image=os.path.join(constants.gui_assets, f'{self.id}{"_favorite" if self.favorite else ""}.png'), color=self.color_id[1], hover_action=False)

class ServerManagerScreen(MenuBackground):

    # Toggles favorite of item, and reload list
    def favorite(self, server_name):
        config_file = constants.server_config(server_name)
        config_file.set('general', 'isFavorite', ('false' if config_file.get('general', 'isFavorite') == 'true' else 'true'))
        constants.server_config(server_name, config_file)


        # Show banner
        bool_favorite = bool(config_file.get('general', 'isFavorite') == 'true')

        Clock.schedule_once(
            functools.partial(
                screen_manager.current_screen.show_banner,
                (0.85, 0.65, 1, 1) if bool_favorite else (0.68, 0.68, 1, 1),
                f"'{server_name}'" + (" marked as favorite" if bool_favorite else " is no longer marked as favorite"),
                "heart-sharp.png" if bool_favorite else "heart-dislike-outline.png",
                2,
                {"center_x": 0.5, "center_y": 0.965}
            ), 0
        )


        constants.server_manager.refresh_list()
        self.gen_search_results(constants.server_manager.server_list, fade_in=False, highlight=server_name)

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

    def gen_search_results(self, results, new_search=False, fade_in=True, highlight=None, animate_scroll=True, *args):

        # Set to proper page on favorite/unfavorite
        default_scroll = 1
        if highlight:
            def divide_chunks(l, n):
                final_list = []

                for i in range(0, len(l), n):
                    final_list.append(l[i:i + n])

                return final_list

            for x, l in enumerate(divide_chunks([x.name for x in results], self.page_size), 1):
                if highlight in l:
                    if self.current_page != x:
                        self.current_page = x

                    # Update scroll when page is bigger than list
                    if Window.height < self.scroll_layout.height:
                        default_scroll = 1 - round(l.index(highlight) / len(l), 2)
                        if default_scroll < 0.2:
                            default_scroll = 0
                        if default_scroll > 0.97:
                            default_scroll = 1
                    break


        # Update page counter
        self.last_results = results
        self.max_pages = (len(results) / self.page_size).__ceil__()
        self.current_page = 1 if self.current_page == 0 or new_search else self.current_page


        self.page_switcher.update_index(self.current_page, self.max_pages)
        page_list = results[(self.page_size * self.current_page) - self.page_size:self.page_size * self.current_page]

        self.scroll_layout.clear_widgets()
        # gc.collect()

        # Generate header
        server_count = len(constants.server_manager.server_list)
        header_content = "Select a server to manage"

        for child in self.header.children:
            if child.id == "text":
                child.text = header_content
                break


        # Show servers if they exist
        if server_count != 0:

            # Create list of server names
            server_names = [server.name for server in constants.server_manager.server_list]

            # Clear and add all ServerButtons
            for x, server_object in enumerate(page_list, 1):

                # Activated when addon is clicked
                def view_server(server, index, *args):
                    selected_button = [item for item in self.scroll_layout.walk() if item.__class__.__name__ == "ServerButton"][index - 1]

                    # View Server
                    if selected_button.last_touch.button == "left":
                        open_server(server.name)

                    # Favorite
                    elif selected_button.last_touch.button == "middle":
                        self.favorite(server.name)


                # Check if updates are available
                update_banner = ""
                if server_object.auto_update == 'true':
                    update_banner = server_object.update_string


                # Add-on button click function
                self.scroll_layout.add_widget(
                    ScrollItem(
                        widget = ServerButton(
                            server_object = server_object,
                            fade_in = ((x if x <= 8 else 8) / self.anim_speed) if fade_in else 0,
                            highlight = (highlight == server_object.name),
                            update_banner = update_banner,
                            click_function = functools.partial(
                                view_server,
                                server_object,
                                x
                            )
                        )
                    )
                )

            self.resize_bind()

        # Animate scrolling
        def set_scroll(*args):
            Animation.stop_all(self.scroll_layout.parent.parent)
            if animate_scroll:
                Animation(scroll_y=default_scroll, duration=0.1).start(self.scroll_layout.parent.parent)
            else:
                self.scroll_layout.parent.parent.scroll_y = default_scroll
        Clock.schedule_once(set_scroll, 0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'
        self.header = None
        self.scroll_layout = None
        self.blank_label = None
        self.page_switcher = None

        self.last_results = []
        self.page_size = 10
        self.current_page = 0
        self.max_pages = 0
        self.anim_speed = 10

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        super()._on_keyboard_down(keyboard, keycode, text, modifiers)

        # Press arrow keys to switch pages
        if keycode[1] in ['right', 'left'] and self.name == screen_manager.current_screen.name:
            self.switch_page(keycode[1])

    def generate_menu(self, **kwargs):

        # Scroll list
        scroll_widget = ScrollViewWidget(position=(0.5, 0.52))
        scroll_anchor = AnchorLayout()
        self.scroll_layout = GridLayout(cols=1, spacing=15, size_hint_max_x=1250, size_hint_y=None, padding=[0, 30, 0, 30])


        # Bind / cleanup height on resize
        def resize_scroll(call_widget, grid_layout, anchor_layout, *args):
            call_widget.height = Window.height // 1.82
            grid_layout.cols = 2 if Window.width > grid_layout.size_hint_max_x else 1
            self.anim_speed = 13 if Window.width > grid_layout.size_hint_max_x else 10

            def update_grid(*args):
                anchor_layout.size_hint_min_y = grid_layout.height

            Clock.schedule_once(update_grid, 0)


        self.resize_bind = lambda*_: Clock.schedule_once(functools.partial(resize_scroll, scroll_widget, self.scroll_layout, scroll_anchor), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        self.scroll_layout.bind(minimum_height=self.scroll_layout.setter('height'))
        self.scroll_layout.id = 'scroll_content'


        # Scroll gradient
        scroll_top = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.795}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, 60))
        scroll_bottom = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.26}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, -60))

        # Generate buttons on page load
        header_content = "Select a server in which to manage"
        self.header = HeaderText(header_content, '', (0, 0.89))

        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'
        float_layout.add_widget(self.header)

        self.page_switcher = PageSwitcher(0, 0, (0.5, 0.887), self.switch_page)


        # Append scroll view items
        scroll_anchor.add_widget(self.scroll_layout)
        scroll_widget.add_widget(scroll_anchor)
        float_layout.add_widget(scroll_widget)
        float_layout.add_widget(scroll_top)
        float_layout.add_widget(scroll_bottom)
        float_layout.add_widget(self.page_switcher)

        buttons.append(main_button('Import a server', (0.5, 0.202), 'download-outline.png'))
        buttons.append(exit_button('Back', (0.5, 0.11), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)

        menu_name = "Server Manager"
        float_layout.add_widget(generate_title("Server Manager"))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)

        # Automatically generate results on page load
        constants.server_manager.refresh_list()
        highlight = False
        self.gen_search_results(constants.server_manager.server_list)

        # Highlight the last server that was last selected
        def highlight_last_server(*args):
            if constants.server_manager.current_server:
                highlight = constants.server_manager.current_server.name
                self.gen_search_results(constants.server_manager.server_list, highlight=highlight, animate_scroll=False)
        Clock.schedule_once(highlight_last_server, 0)

class MenuTaskbar(RelativeLayout):

    def resize(self, *args):

        # Resize background
        self.bg_left.x = 0
        self.bg_right.x = self.width
        self.bg_center.x = 0 + self.bg_left.width
        self.bg_center.size_hint_max_x = self.width - (self.bg_left.width * 2)

    def __init__(self, selected_item=None, animate=False, **kwargs):
        super().__init__(**kwargs)

        show_addons = (constants.server_manager.current_server.type != 'vanilla')
        self.pos_hint = {"center_x": 0.5}

        # Layout for icon object
        class TaskbarItem(AnchorLayout):

            def __init__(self, item_info, selected=False, **kwargs):
                super().__init__(**kwargs)
                new_color = constants.convert_color(item_info[2])['rgb']


                # Icon and listed functions
                class Icon(AnchorLayout, HoverBehavior):

                    # Pretty animation if specified
                    def animate(self, *args):
                        def anim_in(*args):
                            Animation(size_hint_max=(self.default_size + 6, self.default_size + 6), duration=0.15, transition='in_out_sine').start(self.icon)
                            if self.selected:
                                Animation(opacity=1, duration=0.3, transition='in_out_sine').start(self.background)
                                Animation(color=constants.brighten_color(self.hover_color, -0.87), duration=0.2, transition='in_out_sine').start(self.icon)

                        def anim_out(*args):
                            Animation(size_hint_max=(self.default_size, self.default_size), duration=0.15, transition='in_out_sine').start(self.icon)

                        Clock.schedule_once(anim_in, 0.1)
                        Clock.schedule_once(anim_out, 0.25)


                    # Execute click function
                    def on_touch_down(self, touch):
                        if self.hovered and not self.selected and not screen_manager.current_screen.popup_widget:

                            # Animate button
                            self.icon.color = constants.brighten_color(self.hover_color, 0.2)
                            Animation(color=self.hover_color, duration=0.3).start(self.icon)

                            constants.back_clicked = True

                            # Return if back is clicked
                            if self.data[0] == 'back':

                                previous_screen()


                            # If not back, proceed to next screen
                            else:
                                # Wait for data to exist on ServerAclScreen, ServerBackupScreen, And ServerAddonScreen
                                if self.data[-1] == 'ServerAclScreen':
                                    if not constants.server_manager.current_server.acl:
                                        while not constants.server_manager.current_server.acl:
                                            time.sleep(0.2)

                                if self.data[-1] == 'ServerBackupScreen':
                                    if not constants.server_manager.current_server.backup:
                                        while not constants.server_manager.current_server.backup:
                                            time.sleep(0.2)

                                if self.data[-1] == 'ServerAddonScreen':
                                    if not constants.server_manager.current_server.addon:
                                        while not constants.server_manager.current_server.addon:
                                            time.sleep(0.2)

                                screen_manager.current = self.data[-1]

                            constants.back_clicked = False

                        # If no button is matched, return touch to super
                        else:
                            super().on_touch_down(touch)


                    # Change attributes when hovered
                    def on_enter(self):
                        if self.ignore_hover:
                            return

                        if not self.selected:
                            Animation(size_hint_max=(self.default_size + 6, self.default_size + 6), duration=0.15, transition='in_out_sine', color=self.hover_color).start(self.icon)
                        Animation(opacity=1, duration=0.25, transition='in_out_sine').start(self.parent.text)

                    def on_leave(self):
                        self.ignore_hover = False
                        if not self.selected:
                            Animation(size_hint_max=(self.default_size, self.default_size), duration=0.15, transition='in_out_sine', color=self.default_color).start(self.icon)
                        Animation(opacity=0, duration=0.25, transition='in_out_sine').start(self.parent.text)

                    def __init__(self, **kwargs):
                        super().__init__(**kwargs)

                        self.data = item_info
                        self.default_size = 40
                        self.default_color = (0.8, 0.8, 1, 1)
                        self.selected = selected
                        self.hover_color = new_color
                        self.size_hint_max = (self.default_size + 23, self.default_size + 23)
                        self.icon = Image()
                        self.icon.size_hint_max = (self.default_size, self.default_size)
                        self.icon.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
                        self.icon.source = item_info[1]
                        self.icon.color = self.default_color


                        # Add background and change color if selected
                        if self.selected:
                            self.background = Image(source=os.path.join(constants.gui_assets, 'icons', 'sm', 'selected.png'))
                            self.background.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
                            self.background.size_hint_max = self.size_hint_max
                            self.background.color = self.hover_color
                            self.add_widget(self.background)
                            if animate:
                                self.background.opacity = 0
                            else:
                                self.icon.color = constants.brighten_color(self.hover_color, -0.87)

                        self.add_widget(self.icon)


                        # Ignore on_hover when selected widget is already selected on page load
                        self.ignore_hover = False
                        def check_prehover(*args):
                            if self.collide_point(*self.to_widget(*Window.mouse_pos)) and self.selected:
                                self.ignore_hover = True
                        Clock.schedule_once(check_prehover, 0)


                self.icon = Icon()
                self.add_widget(self.icon)

                self.text = RelativeLayout(size_hint_min=(300, 50))
                self.text.add_widget(BannerObject(pos_hint={'center_x': 0.5, 'center_y': 1.25}, text=item_info[0], size=(70, 30), color=new_color))
                self.text.pos_hint = {'center_x': 0.5, 'center_y': 1}
                self.text.opacity = 0
                self.add_widget(self.text)


        # Icon list  (name, path, color, next_screen)
        icon_path = os.path.join(constants.gui_assets, 'icons', 'sm')
        self.item_list = [
            ('back',            os.path.join(icon_path, 'back-outline.png'),  '#FF6FB4'),
            ('launch',          os.path.join(icon_path, 'terminal.png'),      '#817EFF',  'ServerViewScreen'),
            ('back-ups',        os.path.join(icon_path, 'backup.png'),        '#56E6FF',  'ServerBackupScreen'),
            ('access control',  os.path.join(icon_path, 'acl.png'),           '#00FFB2',  'ServerAclScreen'),
            ('add-ons',         os.path.join(icon_path, 'addon.png'),         '#42FF5E',  'ServerAddonScreen'),
            ('amscript',        os.path.join(icon_path, 'amscript.png'),      '#BFFF2B',  'ServerAmscriptScreen'),
            ('advanced',        os.path.join(icon_path, 'advanced.png'),      '#FFFF44',  'ServerAdvancedScreen')
        ]


        self.y = 65
        self.size_hint_max = (500 if show_addons else 430, 64)
        self.side_width = self.size_hint_max[1] * 0.55
        self.background_color = (0.063, 0.067, 0.141, 1)


        # Define resizable background
        self.bg_left = Image()
        self.bg_left.keep_ratio = False
        self.bg_left.allow_stretch = True
        self.bg_left.size_hint_max = (self.side_width, self.size_hint_max[1])
        self.bg_left.source = os.path.join(constants.gui_assets, 'taskbar_edge.png')
        self.bg_left.color = self.background_color
        self.add_widget(self.bg_left)

        self.bg_right = Image()
        self.bg_right.keep_ratio = False
        self.bg_right.allow_stretch = True
        self.bg_right.size_hint_max = (-self.side_width, self.size_hint_max[1])
        self.bg_right.source = os.path.join(constants.gui_assets, 'taskbar_edge.png')
        self.bg_right.color = self.background_color
        self.add_widget(self.bg_right)

        self.bg_center = Image()
        self.bg_center.keep_ratio = False
        self.bg_center.allow_stretch = True
        self.bg_center.source = os.path.join(constants.gui_assets, 'taskbar_center.png')
        self.bg_center.color = self.background_color
        self.add_widget(self.bg_center)


        # Taskbar layout
        self.taskbar = BoxLayout(orientation='horizontal', padding=[5,0,5,0])
        for x, item in enumerate(self.item_list):

            if item[0] == 'add-ons' and not show_addons:
                continue

            selected = (selected_item == item[0])
            item = TaskbarItem(item, selected=selected)
            self.taskbar.add_widget(item)
            if animate:
                Clock.schedule_once(item.icon.animate, x / 15)

        self.add_widget(self.taskbar)


        self.bind(pos=self.resize, size=self.resize)
        Clock.schedule_once(self.resize, 0)



# Server Manager Launch ------------------------------------------------------------------------------------------------

# Prompt for backups and updates on new server config
def prompt_new_server(server_obj, *args):

    # Step 3 - prompt for updates
    def set_update(boolean):
        server_obj.enable_auto_update(boolean)
        server_obj.reload_config()

    def prompt_updates(*args):
        screen_manager.current_screen.show_popup(
            "query",
            "Automatic Updates",
            f"Would you like to enable automatic updates for '{server_obj.name}'?\n\nIf an update is available, Auto-MCS will update this server on launch",
            [functools.partial(set_update, False),
             functools.partial(set_update, True)]
        )

    # Step 2 - apply settings from backup popup and prompt for updates
    def set_bkup_and_prompt_update(boolean):
        server_obj.backup.enable_auto_backup(boolean)
        if boolean:
            threading.Timer(0, server_obj.backup.save_backup).start()
        Clock.schedule_once(prompt_updates, 0.5)

    # Step 1 - prompt for backups
    def prompt_backup(*args):
        screen_manager.current_screen.show_popup(
            "query",
            "Automatic Back-ups",
            f"Would you like to enable automatic back-ups for '{server_obj.name}'?\n\nAuto-MCS will back up this server when closed",
            [functools.partial(set_bkup_and_prompt_update, False),
             functools.partial(set_bkup_and_prompt_update, True)]
        )

    prompt_backup()

class PerformancePanel(RelativeLayout):

    def update_rect(self, *args):
        texture_offset = 70

        # Resize panel
        console_panel = screen_manager.current_screen.console_panel
        self.y = console_panel.default_y + (Window.height - console_panel.size_offset[1]) - 24
        self.width = Window.width - console_panel.size_offset[0] + texture_offset
        self.height = 240

        # Repos panel widgets
        overview_max = (Window.width * 0.2)
        self.overview_widget.size_hint_max_x = overview_max if overview_max >= self.overview_min else self.overview_min

        meter_max = (Window.width * 0.32)
        self.meter_layout.size_hint_max_x = meter_max if meter_max >= self.meter_min else self.meter_min
        for child in self.meter_layout.children:
            Clock.schedule_once(child.recalculate_size, 0)

        self.meter_layout.x = self.width - self.meter_layout.width
        self.player_widget.x = self.overview_widget.x + self.overview_widget.width - texture_offset + 12
        self.player_widget.size_hint_max_x = (self.width) - self.meter_layout.width - self.overview_widget.width + (texture_offset * 2) - 24
        Clock.schedule_once(self.player_widget.recalculate_size, 0)

    # Updates data in panel while the server is running
    def refresh_data(self, interval=0.5, *args):

        # Get performance stats
        threading.Timer(0, functools.partial(constants.server_manager.current_server.performance_stats, interval, (self.player_clock == 3))).start()

        def update_data(*args):
            try:
                perf_data = constants.server_manager.current_server.run_data['performance']
            except KeyError or AttributeError:
                return

            # Update meter
            self.cpu_meter.set_percent(perf_data['cpu'])
            self.ram_meter.set_percent(perf_data['ram'])

            # Update up-time
            formatted_color = '[color=#737373]'
            found = False
            for x, item in enumerate(perf_data['uptime'].split(":")):
                if x == 0 and item != '00':
                    formatted_color += '[/color]'
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

                # Colors
                if percent == 0:
                    color = (0.45, 0.45, 0.45, 1)
                elif percent < 50:
                    color = (0.92, 0.92, 0.92, 1)
                elif percent < 75:
                    color = (1, 0.9, 0.5, 1)
                else:
                    color = (1, 0.53, 0.58, 1)

                Animation(color=color, duration=0.4, transition='in_out_sine').start(self.overview_widget.player_label.label)
                self.overview_widget.player_label.label.text = f'{len(perf_data["current-players"])}[color=#737373] / [/color]{total_count}'

            self.overview_widget.uptime_label.text = formatted_color[:-1]
            Animation(color=(0.92, 0.92, 0.92, 1), duration=0.4, transition='in_out_sine').start(self.overview_widget.uptime_label.label)

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
                self.label.texture_update()
                self.size_hint_max = self.label.texture_size
                self.label.size_hint_max = self.label.texture_size

                self.shadow.texture_update()
                self.shadow.size_hint_max = self.shadow.texture_size
                self.shadow.pos = (self.label.x + self.offset, self.label.y - self.offset)


            def __init__(self, text, font, size, color, align='left', offset=2, shadow_color=dark_accent, **kwargs):
                super().__init__(**kwargs)

                self.offset = offset

                # Shadow
                self.shadow = AlignLabel(text=text)
                self.shadow.font_name = font
                self.shadow.font_size = size
                self.shadow.color = shadow_color
                self.shadow.halign = align
                self.add_widget(self.shadow)

                # Main label
                self.label = AlignLabel(text=text)
                self.label.font_name = font
                self.label.font_size = size
                self.label.color = color
                self.label.halign = align
                self.label.markup = True
                self.add_widget(self.label)

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

                self.background_normal = os.path.join(constants.gui_assets, 'performance_panel.png')
                self.background_down = os.path.join(constants.gui_assets, 'performance_panel.png')
                self.background_color = constants.convert_color("#232439")['rgb']
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
                        Animation(color=color, size_hint_max_x=new_size, duration=0.4, transition='in_out_sine').start(self.progress_bar)
                    else:
                        Animation(size_hint_max_x=new_size, duration=0.99, transition='in_out_sine').start(self.progress_bar)
                else:
                    self.percentage_label.label.color = self.progress_bar.color = color
                    self.progress_bar.size_hint_max_x = new_size

            def recalculate_size(self, *args):

                # Update bar size
                padding = (self.width - self.meter_min) * 0.03
                self.progress_bg.pos = (45 + padding, 52)
                self.progress_bg.size_hint_max = (self.width - 145 - (padding * 2), 7)
                self.progress_bar.pos = (self.progress_bg.x, self.progress_bg.y + self.progress_bar.size_hint_max[1] + 1)
                self.set_percent(self.percent, animate=False)

                # Set text position
                text_x = self.width - self.percentage_label.width - 45 - padding
                self.name.pos = (text_x, self.progress_bg.pos[1] - (self.progress_bar.size_hint_max[1] / 2))
                self.percentage_label.pos = (text_x, self.progress_bar.pos[1] + 12)

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
                    text = meter_name,
                    font = os.path.join(constants.gui_assets, 'fonts', constants.fonts["medium"]),
                    size = sp(22),
                    color = normal_accent,
                    align = 'right',
                    shadow_color = (0, 0, 0, 0)
                )
                self.add_widget(self.name)


                # Percent text
                self.percentage_label = ShadowLabel(
                    text = f'{self.percent} %',
                    font = os.path.join(constants.gui_assets, 'fonts', constants.fonts["bold"]),
                    size = sp(30),
                    color = gray_accent,
                    offset = 3,
                    align = 'right',
                    shadow_color = (0, 0, 0, 0)
                )
                self.add_widget(self.percentage_label)

                self.recalculate_size()


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

                self.max_players = constants.server_manager.current_server.server_properties['max-players']

                self.background = PanelFrame()
                self.size_hint_max_x = overview_min
                self.overview_min = overview_min
                self.add_widget(self.background)


                # Up-time title
                self.uptime_title = ShadowLabel(
                    text = f'up-time',
                    font = os.path.join(constants.gui_assets, 'fonts', constants.fonts["italic"]),
                    size = sp(23),
                    color = normal_accent,
                    offset = 3,
                    align = 'center',
                    shadow_color = constants.brighten_color(dark_accent, 0.04)
                )
                self.uptime_title.pos_hint = {'center_x': 0.5}
                self.uptime_title.y = 170
                self.add_widget(self.uptime_title)

                # Up-time label
                self.uptime_label = ShadowLabel(
                    text = f'00:00:00:00',
                    font = os.path.join(constants.gui_assets, 'fonts', constants.fonts["mono-bold"]) + '.otf',
                    size = sp(30),
                    color = gray_accent,
                    offset = 3,
                    align = 'center',
                    shadow_color = (0, 0, 0, 0)
                )
                self.uptime_label.pos_hint = {'center_x': 0.5}
                self.uptime_label.y = 135
                self.add_widget(self.uptime_label)



                # Player count title
                self.player_title = ShadowLabel(
                    text = f'capacity',
                    font = os.path.join(constants.gui_assets, 'fonts', constants.fonts["italic"]),
                    size = sp(23),
                    color = normal_accent,
                    offset = 3,
                    align = 'center',
                    shadow_color = constants.brighten_color(dark_accent, 0.04)
                )
                self.player_title.pos_hint = {'center_x': 0.5}
                self.player_title.y = 80
                self.add_widget(self.player_title)

                # Player count label
                self.player_label = ShadowLabel(
                    text = f'0 / {self.max_players}',
                    font = os.path.join(constants.gui_assets, 'fonts', constants.fonts["bold"]),
                    size = sp(26),
                    color = gray_accent,
                    offset = 3,
                    align = 'center',
                    shadow_color = (0, 0, 0, 0)
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
                text_width = int(((self.scroll_layout.width // text_width) // 1))
                self.player_list.cols = text_width
                self.player_list.rows = round(data_len / text_width) + 3
                # print(text_width, self.player_list.cols, self.player_list.rows, data_len)

                # Dirty fix to circumvent RecycleView missing data: https://github.com/kivy/kivy/pull/7262
                try:
                    if ((data_len <= self.player_list.cols) and self.player_list.rows <= 5) or data_len + 1 == self.player_list.cols:
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
                self.layout.size_hint_max = (self.width - texture_offset, self.height - texture_offset - (list_offset * 3.5))
                self.scroll_layout.size = self.layout.size

                Clock.schedule_once(self.resize_list, 0)

            def __init__(self, **kwargs):
                super().__init__(**kwargs)

                class PlayerLabel(AlignLabel, HoverBehavior):

                    # Hover stuffies
                    def on_enter(self, *args):
                        if self.copyable:
                            self.outline_width = 0
                            self.outline_color = constants.brighten_color(self.color, 0.05)
                            Animation(outline_width=1, duration=0.03).start(self)

                    def on_leave(self, *args):

                        if self.copyable:
                            Animation.stop_all(self)
                            self.outline_width = 0

                    # Normal stuffies
                    def on_ref_press(self, *args):
                        if not self.disabled and self.text:
                            if constants.server_manager.current_server.acl:
                                constants.server_manager.current_server.acl.display_rule(re.sub("\[.*?\]", "", self.text))
                                constants.back_clicked = True
                                screen_manager.current = 'ServerAclScreen'
                                constants.back_clicked = False

                    def ref_text(self, *args):
                        if '[ref=' not in self.text and '[/ref]' not in self.text and self.copyable:
                            self.text = f'[ref=none]{self.text}[/ref]'
                        elif '[/ref]' in self.text:
                            self.text = self.text.replace("[/ref]", "") + "[/ref]"

                    def __init__(self, **kwargs):
                        super().__init__(**kwargs)
                        self.size_hint = (240, 39)
                        self.pos = (0, 0)
                        self.markup = True
                        self.font_size = sp(25)
                        self.copyable = True
                        self.halign = 'left'
                        self.valign = 'center'
                        self.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
                        self.default_color = (0.6, 0.6, 1, 1)
                        self.color = self.default_color
                        self.bind(text=self.ref_text)

                self.background = PanelFrame()
                self.add_widget(self.background)

                self.current_players = None
                self.padding = 15


                # List layout
                self.layout = RelativeLayout()
                self.layout.opacity = 0
                self.layout_bg = Image(source=os.path.join(constants.gui_assets, 'performance_panel_background.png'))
                self.layout_bg.allow_stretch = True
                self.layout_bg.keep_ratio = False
                self.layout_bg.color = constants.brighten_color(constants.convert_color("#232439")['rgb'], -0.015)
                self.layout.add_widget(self.layout_bg)


                # Player layout
                self.scroll_layout = RecycleViewWidget(position=None, view_class=PlayerLabel)
                self.scroll_layout.always_overscroll = False
                self.scroll_layout.scroll_wheel_distance = dp(50)
                self.player_list = RecycleGridLayout(size_hint_y=None, default_size=(240, 39), padding=[self.padding, 0, self.padding, 0])
                self.player_list.bind(minimum_height=self.player_list.setter('height'))
                self.scroll_layout.add_widget(self.player_list)
                self.layout.add_widget(self.scroll_layout)

                # Test stuffs
                # def test(*args):
                #     data = [{'text':str(x)} for x in range(3)]
                #     self.update_data(data)
                # Clock.schedule_once(test, 3)

                self.add_widget(self.layout)


                # List shadow
                self.layout_shadow = Image(source=os.path.join(constants.gui_assets, 'performance_panel_shadow.png'))
                self.layout_shadow.allow_stretch = True
                self.layout_shadow.keep_ratio = False
                self.layout.add_widget(self.layout_shadow)


                # Player title
                self.title = ShadowLabel(
                    text = f'connected players',
                    font = os.path.join(constants.gui_assets, 'fonts', constants.fonts["italic"]),
                    size = sp(23),
                    color = normal_accent,
                    offset = 3,
                    align = 'center',
                    shadow_color = constants.brighten_color(dark_accent, 0.04)
                )
                self.title.pos_hint = {'center_x': 0.5}
                self.title.y = 170
                self.add_widget(self.title)


                # Empty label
                self.empty_label = ShadowLabel(
                    text = f'*crickets*',
                    font = os.path.join(constants.gui_assets, 'fonts', constants.fonts["italic"]),
                    size = sp(24),
                    color = gray_accent,
                    offset = 3,
                    align = 'center',
                    shadow_color = (0, 0, 0, 0)
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
        if self.update_text not in self.run_data['process-hooks']:
            self.run_data['process-hooks'].append(self.update_text)

        if self.reset_panel not in self.run_data['close-hooks']:
            self.run_data['close-hooks'].append(self.reset_panel)

        self.update_text(self.run_data['log'])

        def update_scroll(*args):
            if (self.console_text.height > self.scroll_layout.height - self.console_text.padding[-1]):
                self.scroll_layout.scroll_y = 0
        Clock.schedule_once(update_scroll, 0)


    # Updates RecycleView text with console text
    def update_text(self, text, force_scroll=False, *args):
        original_scroll = self.scroll_layout.scroll_y
        original_len = len(self.scroll_layout.data)
        self.scroll_layout.data = text
        if (self.console_text.height > self.scroll_layout.height - self.console_text.padding[-1] - self.console_text.padding[1]) and ((original_scroll == 0 or not self.auto_scroll) or force_scroll):
            self.scroll_layout.scroll_y = 0
            self.auto_scroll = True

        def fade_animation(*args):
            for label in self.console_text.children:
                Animation.stop_all(label.anim_cover)
                Animation.stop_all(label.main_label)
                label.main_label.opacity = 1
                label.anim_cover.opacity = 0
                if label.original_text == self.scroll_layout.data[-1]['text']:
                    label.main_label.opacity = 0
                    label.anim_cover.opacity = 1
                    Animation(opacity=1, duration = 0.3).start(label.main_label)
                    Animation(opacity=0, duration=0.3).start(label.anim_cover)
        if len(text) > original_len:
            Clock.schedule_once(fade_animation, 0)


    # Fit background color across screen for transitions, and fix position
    def update_size(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

        self.scroll_layout.height = self.height - self.input.height
        self.scroll_layout.width = self.width
        self.scroll_layout.x = self.x
        self.scroll_layout.y = self.y + self.input.height

        self.console_text.width = self.width

        self.input.pos = self.pos

        self.gradient.pos = (self.input.pos[0], self.pos[1] + (self.input.height * 1.2))
        self.gradient.width = self.scroll_layout.width - self.scroll_layout.bar_width
        self.gradient.height = 0-(self.input.height*0.5)

        self.input_background.pos = (self.pos[0] - 22, self.pos[1] + 8)


        # Corner resize
        offset = self.corner_size
        self.corner_mask.size_hint_max = (self.size[0] - offset, self.size[1] - offset)
        self.corner_mask.pos = (self.x + (offset/2), self.y + (offset/2))
        self.corner_mask.sl.size_hint_max_y = self.height - (self.corner_size*2)
        self.corner_mask.sr.size_hint_max_y = self.height - (self.corner_size*2)
        self.corner_mask.sb.size_hint_max_x = self.width - (self.corner_size*2)
        self.corner_mask.st.size_hint_max_x = self.width - (self.corner_size*2)


        # Console panel resize:
        texture = self.controls.background.texture_size
        self.controls.background.size_hint_max = (texture[0] + (self.height - texture[1]) + 200, texture[1] + (self.height - texture[1]))
        if self.full_screen == "animate":
            pass
        elif self.full_screen:
            self.size_hint_max = (Window.width, Window.height - self.full_screen_offset)
            self.y = 47
        else:
            self.size_hint_max = (Window.width - self.size_offset[0], Window.height - self.size_offset[1])
            self.y = self.default_y

        # Console controls resize
        self.controls.size = self.size
        self.controls.pos = self.pos

        shadow_size = self.controls.control_shadow.size
        self.controls.control_shadow.pos = (self.width - shadow_size[0], self.height - shadow_size[1])

        # Control buttons
        if self.controls.maximize_button and self.controls.stop_button and not self.full_screen:
            self.controls.maximize_button.pos = (self.width - 90, self.height - 80)
            self.controls.stop_button.pos = (self.width - 142, self.height - 80)

        # Fullscreen shadow
        self.fullscreen_shadow.y = self.height + self.x - 3
        self.fullscreen_shadow.width = Window.width

        # Controls background
        def resize_background(*args):
            self.controls.background_ext.x = self.controls.background.width
            self.controls.background_ext.size_hint_max_x = self.width - self.controls.background.width
        Clock.schedule_once(resize_background, 0)


    # Launch server and update properties
    def launch_server(self, animate=True, *args):
        self.update_size()

        for k in self.parent._ignore_keys:
            if k == 'f':
                self.parent._ignore_keys.remove(k)

        anim_speed = 0.15 if animate else 0
        self.scroll_layout.scroll_y = 1
        self.auto_scroll = False

        # Animate panel
        self.controls.launch_button.disabled = True
        self.controls.log_button.disabled = True
        constants.hide_widget(self.controls.maximize_button, False)
        constants.hide_widget(self.controls.stop_button, False)
        self.controls.maximize_button.opacity = 0
        self.controls.stop_button.opacity = 0

        self.controls.crash_text.clear_text()

        Animation(opacity=0, duration=anim_speed).start(self.controls.button_shadow)
        Animation(opacity=0, duration=anim_speed).start(self.controls.background)
        Animation(opacity=0, duration=anim_speed).start(self.controls.background_ext)
        Animation(opacity=0, duration=(anim_speed*1.5) if animate else 0).start(self.controls.launch_button)
        Animation(opacity=0, duration=(anim_speed*1.5) if animate else 0).start(self.controls.log_button)
        Animation(opacity=1, duration=(anim_speed*2) if animate else 0).start(self.controls.maximize_button)

        def after_anim(*a):
            self.controls.maximize_button.disabled = False
            self.controls.stop_button.disabled = False
            self.controls.remove_widget(self.controls.launch_button)
            self.controls.remove_widget(self.controls.log_button)
            self.controls.launch_button.button.on_leave()
            self.controls.log_button.button.on_leave()
            Animation(opacity=1, duration=(anim_speed*2) if animate else 0).start(self.controls.stop_button)

        def update_launch_data(*args):
            if self.server_button:
                self.server_button.update_subtitle(self.run_data)
        Clock.schedule_once(update_launch_data, 3)

        Clock.schedule_once(after_anim, (anim_speed*1.51) if animate else 0)


        # Actually launch server
        constants.java_check()
        self.update_process(screen_manager.current_screen.server.launch())

        # Start performance counter
        screen_manager.current_screen.set_timer(True)

        self.input.disabled = False
        constants.server_manager.current_server.run_data['console-panel'] = self
        constants.server_manager.current_server.run_data['performance-panel'] = screen_manager.current_screen.performance_panel


    # Send '/stop' command to server console
    @staticmethod
    def stop_server(*args):
        screen_manager.current_screen.server.silent_command("stop")


    # Called from ServerObject when process stops
    def reset_panel(self, crash=None):

        def reset(*args):

            # Show crash banner if not on server screen
            def show_crash_banner(*args):
                if crash:
                    Clock.schedule_once(
                        functools.partial(
                            screen_manager.current_screen.show_banner,
                            (1, 0.5, 0.65, 1),
                            f"'{self.server_name}' has crashed",
                            "close-circle-sharp.png",
                            2.5,
                            {"center_x": 0.5, "center_y": 0.965}
                        ), 0.25
                    )

            # Ignore if screen isn't visible or a different server
            if not (screen_manager.current_screen.name == 'ServerViewScreen'):
                show_crash_banner()

                # Update caption on list if user is staring at it for some reason
                if (screen_manager.current_screen.name == 'ServerManagerScreen'):
                    for button in screen_manager.current_screen.scroll_layout.children:
                        button = button.children[0]
                        if button.title.text.strip() == self.server_name:
                            button.update_subtitle(None, dt.now())
                            break
                return

            if screen_manager.current_screen.server.name != self.server_name or not self.run_data:
                show_crash_banner()
                return


            # Do things when on server launch screen
            screen_manager.current_screen.set_timer(False)
            screen_manager.current_screen.performance_panel.reset_panel()
            if 'f' not in self.parent._ignore_keys:
                self.parent._ignore_keys.append('f')

            self.run_data = None
            self.ignore_keypress = True

            if self.parent.server_button:
                self.parent.server_button.update_subtitle(self.run_data, dt.now())


            # Else, reset it back to normal
            self.maximize(False)
            constants.hide_widget(self.controls.maximize_button, True)
            constants.hide_widget(self.controls.stop_button, True)


            def after_anim(*a):
                anim_speed = 0.15

                # Update crash widgets
                if crash:
                    self.controls.log_button.disabled = False
                    self.controls.log_button.opacity = 0
                    self.controls.add_widget(self.controls.log_button)
                    Animation(opacity=1, duration=anim_speed).start(self.controls.log_button)
                    self.controls.crash_text.update_text(f"Uh oh, '{self.server_name}' has crashed", False)


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

                def after_anim2(*a):
                    self.controls.maximize_button.disabled = False
                    self.controls.stop_button.disabled = False
                    self.scroll_layout.data = {}

                Clock.schedule_once(after_anim2, (anim_speed * 1.51))

            Clock.schedule_once(after_anim, 1.5)

        Clock.schedule_once(reset, 0)

        # Prompt new server to enable automatic backups and updates
        if not crash and (self.server_obj.auto_update == 'prompt' or self.server_obj.backup.backup_stats['auto-backup'] == 'prompt'):
            Clock.schedule_once(functools.partial(prompt_new_server, self.server_obj))


    # Toggles full screen on the console
    def maximize(self, maximize=True, *args):

        # Make sure the buttons exist
        if 'f' in self.parent._ignore_keys and maximize:
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
            Animation(size_hint_max=(Window.width, Window.height - self.full_screen_offset), y=47, duration=anim_speed, transition='out_sine').start(self)

            # Full screen button
            self.controls.remove_widget(self.controls.maximize_button)
            del self.controls.maximize_button
            self.controls.maximize_button = IconButton('minimize', {}, (71, 150), (None, None), 'minimize.png', clickable=True, anchor='right', force_color=self.button_colors['maximize'], click_func=functools.partial(self.maximize, False))
            self.controls.maximize_button.opacity = 0
            self.controls.add_widget(self.controls.maximize_button)

            # Stop server button
            self.controls.remove_widget(self.controls.stop_button)
            del self.controls.stop_button
            self.controls.stop_button = IconButton('stop server', {}, (123, 150), (None, None), 'stop-circle-outline-big.png', clickable=True, anchor='right', text_offset=(13, 50), force_color=self.button_colors['stop'], click_func=self.stop_server)
            self.controls.stop_button.opacity = 0
            self.controls.add_widget(self.controls.stop_button)

            def after_anim(*a):
                self.full_screen = True
                self.ignore_keypress = False
                Animation(opacity=0, duration=(anim_speed*0.1), transition='out_sine').start(self.corner_mask)
                Animation(opacity=1, duration=(anim_speed * 0.1), transition='out_sine').start(self.fullscreen_shadow)
                Animation(opacity=1, duration=anim_speed, transition='out_sine').start(self.controls.maximize_button)
                Animation(opacity=1, duration=anim_speed, transition='out_sine').start(self.controls.stop_button)
                fix_scroll()

            Clock.schedule_once(after_anim, (anim_speed*1.1))


        # Exiting full screen
        else:
            Animation(size_hint_max=(Window.width - self.size_offset[0], Window.height - self.size_offset[1]), y=self.default_y, duration=anim_speed, transition='out_sine').start(self)
            Animation(opacity=1, duration=(anim_speed*0.1), transition='out_sine').start(self.corner_mask)
            Animation(opacity=0, duration=(anim_speed*0.1), transition='out_sine').start(self.fullscreen_shadow)

            # Full screen button
            self.controls.remove_widget(self.controls.maximize_button)
            del self.controls.maximize_button
            self.controls.maximize_button = RelativeIconButton('maximize', {}, (20, 20), (None, None), 'maximize.png', clickable=True, anchor='right', text_offset=(24, 80), force_color=self.button_colors['maximize'], click_func=functools.partial(self.maximize, True))
            self.controls.maximize_button.opacity = 0
            self.controls.add_widget(self.controls.maximize_button)

            # Stop server button
            self.controls.remove_widget(self.controls.stop_button)
            del self.controls.stop_button
            self.controls.stop_button = RelativeIconButton('stop server', {}, (20, 20), (None, None), 'stop-circle-outline-big.png', clickable=True, anchor='right', text_offset=(8, 80), force_color=self.button_colors['stop'], click_func=self.stop_server)
            self.controls.stop_button.opacity = 0
            self.controls.add_widget(self.controls.stop_button)

            if not self.run_data:
                constants.hide_widget(self.controls.maximize_button, True)
                constants.hide_widget(self.controls.stop_button, True)

            def after_anim(*a):
                self.full_screen = False
                self.ignore_keypress = False
                if self.run_data:
                    self.update_size()
                    Animation(opacity=1, duration=anim_speed, transition='out_sine').start(self.controls.maximize_button)
                    Animation(opacity=1, duration=anim_speed, transition='out_sine').start(self.controls.stop_button)
                fix_scroll()

            Clock.schedule_once(after_anim, (anim_speed*1.1))


    # Opens crash log in default text editor
    def open_log(self, *args):
        data_dict = {
            'app_title': constants.app_title,
            'gui_assets': constants.gui_assets,
            'background_color': constants.background_color,
            'sub_processes': constants.sub_processes
        }
        Clock.schedule_once(functools.partial(logviewer.open_log, self.server_name, constants.server_manager.current_server.crash_log, data_dict), 0.1)
        self.controls.log_button.button.on_leave()
        self.controls.log_button.button.on_release()


    def __init__(self, server_name, server_button=None, **kwargs):
        super().__init__(**kwargs)

        self.server_name = server_name
        self.server_obj = None
        self.server_button = server_button
        self.full_screen = False
        self.full_screen_offset = 95
        self.size_offset = (70, 550)
        self.ignore_keypress = False
        self.pos_hint = {"center_x": 0.5}
        self.default_y = 170
        self.y = self.default_y

        self.button_colors = {
            'maximize': [[(0.05, 0.08, 0.07, 1), (0.8, 0.8, 1, 1)], ''],
            'stop': [[(0.05, 0.08, 0.07, 1), (0.8, 0.8, 1, 1)], 'pink']
        }


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

                if text and screen_manager.current_screen.name == 'ServerViewScreen':
                    self.date_label.text = text[0]
                    self.type_label.text = text[1]
                    self.main_label.text = text[2]
                    type_color = text[3]


                    # Log text section formatting
                    width = screen_manager.current_screen.console_panel.console_text.width
                    self.width = width
                    self.main_label.width = width - (self.section_size * 2) - 3
                    self.main_label.text_size = (width - (self.section_size * 2) - 3, None)
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


            def __init__(self, **kwargs):
                super().__init__(**kwargs)

                self.original_text = None
                self.line_spacing = 20
                self.font_size = sp(17)
                self.section_size = 110


                # Main text
                self.main_label = Label()
                self.main_label.markup = True
                self.main_label.shorten = True
                self.main_label.shorten_from = 'right'
                self.main_label.font_size = sp(20)
                self.main_label.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["mono-bold"]}.otf')
                self.main_label.halign = 'left'
                self.add_widget(self.main_label)


                # Type label/banner
                self.type_banner = Image()
                self.type_banner.source = os.path.join(constants.gui_assets, 'console_banner.png')
                self.type_banner.allow_stretch = True
                self.type_banner.keep_ratio = False
                self.add_widget(self.type_banner)

                self.type_label = Label()
                self.type_label.font_size = self.font_size
                self.type_label.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["mono-bold"]}.otf')
                self.add_widget(self.type_label)


                # Date label/banner
                self.date_banner1 = Image()
                self.date_banner1.source = os.path.join(constants.gui_assets, 'console_banner.png')
                self.date_banner1.allow_stretch = True
                self.date_banner1.keep_ratio = False
                self.add_widget(self.date_banner1)
                self.date_banner2 = Image()
                self.date_banner2.source = os.path.join(constants.gui_assets, 'console_banner.png')
                self.date_banner2.allow_stretch = True
                self.date_banner2.keep_ratio = False
                self.date_banner2.x = 27
                self.add_widget(self.date_banner2)

                self.date_label = Label()
                self.date_label.font_size = self.font_size
                self.date_label.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["mono-medium"]}.otf')
                self.date_label.halign = 'left'
                self.add_widget(self.date_label)


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

                # Update screen focus value on next frame
                def update_focus(*args):
                    screen_manager.current_screen._input_focused = self.focus

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
                self.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["mono-bold"]}.otf')
                self.font_size = sp(22)
                self.padding_y = (12, 12)
                self.padding_x = (70, 12)
                self.cursor_color = (0.55, 0.55, 1, 1)
                self.cursor_width = dp(3)
                self.selection_color = (0.5, 0.5, 1, 0.4)

                self.bind(on_text_validate=self.on_enter)

            def grab_focus(self):
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
                if screen_manager.current_screen.popup_widget:
                    return None

                if not self.text and substring in [' ', '/']:
                    substring = ""

                else:
                    s = substring.replace("§", "[_color_]").encode("ascii", "ignore").decode().replace("\n","").replace("\r","").replace("[_color_]", "§")
                    self.original_text = self.text + s
                    self.history_index = 0
                    return super().insert_text(s, from_undo=from_undo)


            # Manipulate command history
            def keyboard_on_key_down(self, window, keycode, text, modifiers):
                super().keyboard_on_key_down(window, keycode, text, modifiers)

                if self.parent.run_data:

                    if keycode[1] == "backspace" and "ctrl" in modifiers:
                        if " " not in self.text:
                            self.text = ""
                        else:
                            self.text = self.text.rsplit(" ", 1)[0]


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
                self.background.source = os.path.join(constants.gui_assets, f'console_preview_{randrange(3)}.png')
                self.background_ext = Image(size_hint_max=(None, None))
                self.add_widget(self.background_ext)
                self.add_widget(self.background)

                # Button shadow
                self.button_shadow = Image(pos_hint={'center_x': 0.5, 'center_y': 0.5})
                self.button_shadow.allow_stretch = True
                self.button_shadow.keep_ratio = False
                self.button_shadow.size_hint_max = (580, 250)
                self.button_shadow.source = os.path.join(constants.gui_assets, 'banner_shadow.png')
                self.add_widget(self.button_shadow)

                # Launch button
                self.launch_button = color_button("LAUNCH", position=(0.5, 0.5), icon_name='play-circle-sharp.png', click_func=self.panel.launch_server)
                self.launch_button.disabled = False
                self.add_widget(self.launch_button)

                # Open log button
                self.log_button = color_button("VIEW CRASH LOG", position=(0.5, 0.22), icon_name='document-text-outline-sharp.png', click_func=self.panel.open_log, color=(1,0.65,0.75,1))
                self.log_button.disabled = False
                if constants.server_manager.current_server.crash_log:
                    self.add_widget(self.log_button)

                # Crash text
                self.crash_text = InputLabel(pos_hint={'center_y': 0.78})
                self.add_widget(self.crash_text)
                if constants.server_manager.current_server.crash_log:
                    self.crash_text.update_text(f"Uh oh, '{self.panel.server_name}' has crashed", False)


                # Button shadow in the top right
                self.control_shadow = Image()
                self.control_shadow.allow_stretch = True
                self.control_shadow.keep_ratio = False
                self.control_shadow.color = background_color
                self.control_shadow.source = os.path.join(constants.gui_assets, 'console_control_shadow.png')
                self.control_shadow.size_hint_max = (200, 120)
                self.add_widget(self.control_shadow)


                # Full screen button
                self.maximize_button = RelativeIconButton('maximize', {}, (20, 20), (None, None), 'maximize.png', clickable=True, anchor='right', text_offset=(24, 80), force_color=self.panel.button_colors['maximize'], click_func=functools.partial(self.panel.maximize, True))
                constants.hide_widget(self.maximize_button)
                self.add_widget(self.maximize_button)

                # Stop server button
                self.stop_button = RelativeIconButton('stop server', {}, (20, 20), (None, None), 'stop-circle-outline-big.png', clickable=True, anchor='right', text_offset=(8, 80), force_color=self.panel.button_colors['stop'], click_func=self.panel.stop_server)
                constants.hide_widget(self.stop_button)
                self.add_widget(self.stop_button)


        # Popen object reference
        self.run_data = None
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
        self.add_widget(self.scroll_layout)


        # Log gradient
        self.gradient = Image()
        self.gradient.allow_stretch = True
        self.gradient.keep_ratio = False
        self.gradient.size_hint = (None, None)
        self.gradient.color = background_color
        self.gradient.opacity = 0.9
        self.gradient.source = os.path.join(constants.gui_assets, 'scroll_gradient.png')
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
        self.input_background.source = os.path.join(constants.gui_assets, 'console_input_banner.png')
        self.add_widget(self.input_background)


        # Fullscreen shadow
        self.fullscreen_shadow = Image()
        self.fullscreen_shadow.allow_stretch = True
        self.fullscreen_shadow.keep_ratio = False
        self.fullscreen_shadow.size_hint_max = (None, 50)
        self.fullscreen_shadow.color = (0, 0, 0, 1)
        self.fullscreen_shadow.opacity = 0
        self.fullscreen_shadow.source = os.path.join(constants.gui_assets, 'control_fullscreen_gradient.png')
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
                self.source = os.path.join(constants.gui_assets, 'console_border.png')
                self.color = constants.background_color
                self.allow_stretch = True
                self.keep_ratio = False

        class Side(Image):
            def __init__(self, vertical=True, **kwargs):
                super().__init__(**kwargs)
                self.source = os.path.join(constants.gui_assets, f'control_gradient_{"vertical" if vertical else "horizontal"}.png')
                self.allow_stretch = True
                self.keep_ratio = False

        self.corner_mask = RelativeLayout()
        self.corner_mask.tl = Corner(pos_hint={'center_x': 0, 'center_y': 1}, size_hint_max=(self.corner_size, self.corner_size))
        self.corner_mask.tr = Corner(pos_hint={'center_x': 1, 'center_y': 1}, size_hint_max=(-self.corner_size, self.corner_size))
        self.corner_mask.bl = Corner(pos_hint={'center_x': 0, 'center_y': 0}, size_hint_max=(self.corner_size, -self.corner_size))
        self.corner_mask.br = Corner(pos_hint={'center_x': 1, 'center_y': 0}, size_hint_max=(-self.corner_size, -self.corner_size))
        self.corner_mask.add_widget(self.corner_mask.tl)
        self.corner_mask.add_widget(self.corner_mask.tr)
        self.corner_mask.add_widget(self.corner_mask.bl)
        self.corner_mask.add_widget(self.corner_mask.br)

        self.corner_mask.sl = Side(pos_hint={'center_x': 0, 'center_y': 0.5}, size_hint_max=(self.corner_size, None), vertical=False)
        self.corner_mask.sr = Side(pos_hint={'center_x': 1, 'center_y': 0.5}, size_hint_max=(-self.corner_size, None), vertical=False)
        self.corner_mask.st = Side(pos_hint={'center_x': 0.5, 'center_y': 1}, size_hint_max=(None, self.corner_size))
        self.corner_mask.sb = Side(pos_hint={'center_x': 0.5, 'center_y': 0}, size_hint_max=(None, -self.corner_size))
        self.corner_mask.add_widget(self.corner_mask.sl)
        self.corner_mask.add_widget(self.corner_mask.sr)
        self.corner_mask.add_widget(self.corner_mask.st)
        self.corner_mask.add_widget(self.corner_mask.sb)

        self.add_widget(self.corner_mask)


        self.bind(pos=self.update_size)
        self.bind(size=self.update_size)
        Clock.schedule_once(self.update_size, 0)

class ServerViewScreen(MenuBackground):

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

    def set_timer(self, start=True):
        if start:
            try:
                if self.server.run_data:
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

        # Ignore ESC commands while input focused
        if not self._input_focused and self.name == screen_manager.current_screen.name:

            # Keycode is composed of an integer + a string
            # If we hit escape, release the keyboard
            # On ESC, click on back button if it exists
            if keycode[1] == 'escape' and 'escape' not in self._ignore_keys:

                if self.console_panel.full_screen:
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
                self.console_panel.controls.launch_button.button.on_enter()
                Clock.schedule_once(self.console_panel.launch_server, 0.1)


            # Use 'F' to toggle fullscreen
            if keycode[1] == 'f' and 'f' not in self._ignore_keys and self.server.run_data:
                self.console_panel.maximize(not self.console_panel.full_screen)
                self.console_panel.ignore_keypress = True


            # Focus text input if server is started
            if (keycode[1] == 'tab' and 'tab' not in self._ignore_keys) and self.server.run_data:
                self.console_panel.input.grab_focus()



        # Capture keypress on current screen no matter what
        if self.name == screen_manager.current_screen.name:

            # Stop the server if it's currently running
            if ((keycode[1] == 'q' and 'ctrl' in modifiers) and ('q' not in self._ignore_keys)) and self.server.run_data:
                stop_button = self.console_panel.controls.stop_button
                if stop_button.opacity == 1:
                    stop_button.button.trigger_action(0.1)



        # Return True to accept the key. Otherwise, it will be used by the system.
        return True

    def generate_menu(self, **kwargs):

        # If a new server is selected, animate the taskbar
        animate_taskbar = False
        try:
            if self.server.name != constants.server_manager.current_server.name:
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
        buttons.append(exit_button('Back', (0.5, -1), cycle=True))
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
        if self.server.run_data:
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
        if self.server.run_data:
            self.console_panel = self.server.run_data['console-panel']
        else:
            self.console_panel = ConsolePanel(self.server.name, self.server_button)

        self.add_widget(self.console_panel)
        self.console_panel.server_obj = self.server



# Server Back-up Manager -----------------------------------------------------------------------------------------------

class ServerBackupScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'

        self.save_backup_button = None
        self.restore_backup_button = None
        self.open_path_button = None
        self.migrate_path_button = None

        self.header = None
        self.menu_taskbar = None

    def solo_button(self, button_name, loading=True, *args):
        server_obj = constants.server_manager.current_server

        button_dict = {
            'save': self.save_backup_button,
            'restore': self.restore_backup_button,
            'migrate': self.migrate_path_button
        }

        for k, v in button_dict.items():
            print(server_obj.backup.backup_stats['backup-list'])
            if k == 'restore' and ((server_obj.running) or (not server_obj.backup.backup_stats['backup-list'])):
                v.disable(True)
                continue

            if k == button_name:
                v.loading(True) if loading else v.loading(False)
            else:
                v.disable(True) if loading else v.disable(False)

    def generate_menu(self, **kwargs):
        server_obj = constants.server_manager.current_server
        server_obj.backup.update_data()
        backup_stats = server_obj.backup.backup_stats
        very_bold_font = os.path.join(constants.gui_assets, 'fonts', constants.fonts["very-bold"])

        # Retain button persistence when disabled
        if server_obj.name in constants.backup_lock:
            Clock.schedule_once(functools.partial(self.solo_button, constants.backup_lock[server_obj.name], True), 0)
        else:
            Clock.schedule_once(functools.partial(self.solo_button, None, False), 0)


        # Scroll list
        scroll_widget = ScrollViewWidget(position=(0.5, 0.485))
        scroll_anchor = AnchorLayout()
        scroll_layout = GridLayout(cols=1, spacing=10, size_hint_max_x=1050, size_hint_y=None, padding=[0, 16, 0, 30])


        # Bind / cleanup height on resize
        def resize_scroll(call_widget, grid_layout, anchor_layout, *args):
            call_widget.height = Window.height // 1.6
            grid_layout.cols = 2 if Window.width > grid_layout.size_hint_max_x else 1
            scroll_layout.spacing = 30 if grid_layout.cols == 2 else 10

            def update_grid(*args):
                anchor_layout.size_hint_min_y = grid_layout.height

            Clock.schedule_once(update_grid, 0)


        self.resize_bind = lambda*_: Clock.schedule_once(functools.partial(resize_scroll, scroll_widget, scroll_layout, scroll_anchor), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        scroll_layout.bind(minimum_height=scroll_layout.setter('height'))
        scroll_layout.id = 'scroll_content'

        # Scroll gradient
        scroll_top = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.8}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, 60))
        scroll_bottom = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.17}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, -60))


        # Generate buttons on page load
        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'


        # Save back-up button
        def save_backup(*args):

            def run_backup(*args):

                # Run back-up
                Clock.schedule_once(functools.partial(self.solo_button, 'save', True), 0)
                server_obj.backup.save_backup()

                # Update header
                def change_header(*args):
                    backup_stats = server_obj.backup.backup_stats
                    backup_count = len(backup_stats['backup-list'])
                    header_content = "Latest Back-up  [color=#494977]-[/color]  " + ('[color=#6A6ABA]Never[/color]' if not backup_stats['latest-backup'] else f'[font={very_bold_font}]{backup_stats["latest-backup"]}[/font]')
                    sub_header_content = f"{backup_count:,}  back-up" + ("" if backup_count == 1 else "s") + (f"   ({backup_stats['total-size']})" if backup_count > 0 else "")
                    self.header.text.text = header_content
                    self.header.lower_text.text = sub_header_content

                Clock.schedule_once(change_header, 0)

                # Show banner and update button
                Clock.schedule_once(functools.partial(self.solo_button, 'save', False), 0)

                Clock.schedule_once(
                    functools.partial(
                        self.show_banner,
                        (0.553, 0.902, 0.675, 1),
                        f"Backed up '{server_obj.name}' successfully",
                        "checkmark-circle-sharp.png",
                        2.5,
                        {"center_x": 0.5, "center_y": 0.965}
                    ), 0
                )

            threading.Timer(0, run_backup).start()

        sub_layout = ScrollItem()
        self.save_backup_button = WaitButton('Save Back-up Now', (0.5, 0.5), 'save-sharp.png', click_func=save_backup)
        sub_layout.add_widget(self.save_backup_button)
        scroll_layout.add_widget(sub_layout)


        # Restore back-up button
        sub_layout = ScrollItem()
        self.restore_backup_button = WaitButton('Restore From Back-up', (0.5, 0.5), 'reload-sharp.png', disabled=server_obj.running)
        sub_layout.add_widget(self.restore_backup_button)
        scroll_layout.add_widget(sub_layout)


        # Auto-backup toggle
        start_value = False if str(backup_stats['auto-backup']) == 'prompt' else str(backup_stats['auto-backup']) == 'true'

        def toggle_auto(var):
            server_obj.backup.enable_auto_backup(var)

            Clock.schedule_once(
                functools.partial(
                    self.show_banner,
                    (0.553, 0.902, 0.675, 1) if var else (0.937, 0.831, 0.62, 1),
                    f"Automatic back-ups {'en' if var else 'dis'}abled",
                    "checkmark-circle-sharp.png" if var else "close-circle-sharp.png",
                    2,
                    {"center_x": 0.5, "center_y": 0.965}
                ), 0
            )

        sub_layout = ScrollItem()
        sub_layout.add_widget(blank_input(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="automatic back-ups"))
        sub_layout.add_widget(toggle_button('auto-backup', (0.5, 0.5), default_state=start_value, custom_func=toggle_auto))
        scroll_layout.add_widget(sub_layout)


        # Maximum back-up slider
        max_limit = 11
        start_value = max_limit if str(backup_stats['max-backup']) == 'unlimited' else int(backup_stats['max-backup'])

        def change_limit(val):
            server_obj.backup.set_backup_amount('unlimited' if val == max_limit else val)

        sub_layout = ScrollItem()
        sub_layout.add_widget(blank_input(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="maximum back-ups"))
        sub_layout.add_widget(NumberSlider(start_value, (0.5, 0.5), input_name='BackupMaxInput', limits=(2, max_limit), max_icon='infinite-bold.png', function=change_limit))
        scroll_layout.add_widget(sub_layout)


        # Open back-up directory
        def open_backup_dir(*args):
            backup_stats = server_obj.backup.backup_stats
            constants.open_folder(backup_stats['backup-path'])
            Clock.schedule_once(self.open_path_button.button.on_leave, 0.5)

        sub_layout = ScrollItem()
        self.open_path_button = WaitButton('Open Back-up Directory', (0.5, 0.5), 'folder-outline.png', click_func=open_backup_dir)
        sub_layout.add_widget(self.open_path_button)
        scroll_layout.add_widget(sub_layout)


        # Migrate back-up directory
        def change_backup_dir(*args):
            backup_stats = server_obj.backup.backup_stats
            current_path = backup_stats['backup-path']
            new_path = file_popup("dir", start_dir=(current_path if os.path.exists(current_path) else constants.home), input_name='migrate_backup_button', select_multiple=False, title="Select a New Back-up Directory")
            Clock.schedule_once(self.open_path_button.button.on_leave, 0.5)

            def run_migrate(*args):
                Clock.schedule_once(functools.partial(self.solo_button, 'migrate', True), 0)
                final_path = server_obj.backup.set_backup_directory(new_path)

                # Show banner and update button
                Clock.schedule_once(functools.partial(self.solo_button, 'migrate', False), 0)

                if final_path:
                    Clock.schedule_once(
                        functools.partial(
                            self.show_banner,
                            (0.553, 0.902, 0.675, 1),
                            "Migrated back-up directory successfully",
                            "checkmark-circle-sharp.png",
                            2.5,
                            {"center_x": 0.5, "center_y": 0.965}
                        ), 0
                    )
                else:
                    Clock.schedule_once(
                        functools.partial(
                            self.show_banner,
                            (1, 0.53, 0.58, 1),
                            "Failed to migrate back-up directory",
                            "close-circle.png",
                            2.5,
                            {"center_x": 0.5, "center_y": 0.965}
                        ), 0
                    )


            # If path was selected, migrate folder
            if new_path:
                threading.Timer(0, run_migrate).start()

        sub_layout = ScrollItem()
        self.migrate_path_button = WaitButton('Migrate Back-up Directory', (0.5, 0.5), 'migrate.png', click_func=change_backup_dir)
        sub_layout.add_widget(self.migrate_path_button)
        scroll_layout.add_widget(sub_layout)


        # Append scroll view items
        scroll_anchor.add_widget(scroll_layout)
        scroll_widget.add_widget(scroll_anchor)
        float_layout.add_widget(scroll_widget)
        float_layout.add_widget(scroll_top)
        float_layout.add_widget(scroll_bottom)


        # Configure header
        # print(backup_stats)
        backup_count = len(backup_stats['backup-list'])
        header_content = "Latest Back-up  [color=#494977]-[/color]  " + ('[color=#6A6ABA]Never[/color]' if not backup_stats['latest-backup'] else f'[font={very_bold_font}]{backup_stats["latest-backup"]}[/font]')
        sub_header_content = f"{backup_count:,}  back-up" + ("" if backup_count == 1 else "s") + (f"   ({backup_stats['total-size']})" if backup_count > 0 else "")
        self.header = HeaderText(header_content, sub_header_content, (0, 0.89))
        float_layout.add_widget(self.header)


        buttons.append(exit_button('Back', (0.5, -1), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)

        float_layout.add_widget(generate_title(f"Back-up Manager: '{server_obj.name}'"))
        float_layout.add_widget(generate_footer(f"{server_obj.name}, Back-ups"))

        self.add_widget(float_layout)

        # Add ManuTaskbar
        self.menu_taskbar = MenuTaskbar(selected_item='back-ups')
        self.add_widget(self.menu_taskbar)

class BackupButton(HoverButton):

    def animate_button(self, image, color, **kwargs):
        image_animate = Animation(duration=0.05)

        def f(w):
            w.background_normal = image

        Animation(color=color, duration=0.06).start(self.title)
        Animation(color=color, duration=0.06).start(self.index_icon)
        Animation(color=color, duration=0.06).start(self.index_label)
        Animation(color=color, duration=0.06).start(self.subtitle)
        Animation(color=color, duration=0.06).start(self.type_image.image)
        if self.type_image.version_label.__class__.__name__ == "AlignLabel":
            Animation(color=color, duration=0.06).start(self.type_image.version_label)
        Animation(color=color, duration=0.06).start(self.type_image.type_label)

        a = Animation(duration=0.0)
        a.on_complete = functools.partial(f)

        image_animate += a

        image_animate.start(self)

    def resize_self(self, *args):

        # Title and description
        padding = 2.17
        self.title.pos = (self.x + (self.title.text_size[0] / padding) - (0) + 30, self.y + 31) # - (6)
        self.subtitle.pos = (self.x + (self.subtitle.text_size[0] / padding) - 1 + 30 - 100, self.y + 8)
        self.index_label.pos = (self.x - 19, self.y + 2.5)
        self.index_icon.pos = (self.x + 8, self.y + 18)

        offset = 9.45 if self.type_image.type_label.text in ["vanilla", "paper"]\
            else 9.6 if self.type_image.type_label.text == "forge"\
            else 9.35 if self.type_image.type_label.text == "craftbukkit"\
            else 9.55


        self.type_image.image.x = self.width + self.x - (self.type_image.image.width) - 13
        self.type_image.image.y = self.y + ((self.height / 2) - (self.type_image.image.height / 2))

        self.type_image.type_label.x = self.width + self.x - (self.padding_x * offset) - self.type_image.width - 83
        self.type_image.type_label.y = self.y + (self.height * 0.05)

        # Update label
        if self.type_image.version_label.__class__.__name__ == "AlignLabel":
            self.type_image.version_label.x = self.width + self.x - (self.padding_x * offset) - self.type_image.width - 83
            self.type_image.version_label.y = self.y - (self.height / 3.2)

        # Banner version object
        else:
            self.type_image.version_label.x = self.width + self.x - (self.padding_x * offset) - self.type_image.width - 130
            self.type_image.version_label.y = self.y - (self.height / 3.2) - 2

    def __init__(self, backup_object, click_function=None, fade_in=0.0, index=0, **kwargs):
        super().__init__(**kwargs)

        self.properties = backup_object
        self.border = (-5, -5, -5, -5)
        self.color_id = [(0.05, 0.05, 0.1, 1), constants.brighten_color((0.65, 0.65, 1, 1), 0.07)]
        self.pos_hint = {"center_x": 0.5, "center_y": 0.6}
        self.size_hint_max = (580, 80)
        self.id = "server_button"
        self.index = index
        self.newest = (index == 1)

        self.background_normal = os.path.join(constants.gui_assets, f'{self.id}{"_ro" if self.newest else ""}.png')
        self.background_down = os.path.join(constants.gui_assets, f'{self.id}_click.png')

        # Loading stuffs
        self.original_subtitle = backup_object.date
        self.original_font = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["regular"]}.ttf')


        # Title of Server
        self.title = Label()
        self.title.id = "title"
        self.title.halign = "left"
        self.title.color = self.color_id[1]
        self.title.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
        self.title.font_size = sp(25)
        self.title.text_size = (self.size_hint_max[0] * 0.94, self.size_hint_max[1])
        self.title.shorten = True
        self.title.markup = True
        self.title.shorten_from = "right"
        self.title.max_lines = 1
        self.title.text = backup_object.name
        self.add_widget(self.title)


        # Index Icon
        self.index_icon = Image()
        self.index_icon.id = "index_icon"
        self.index_icon.source = os.path.join(constants.gui_assets, 'icons', 'index-fade.png')
        self.index_icon.keep_ratio = False
        self.index_icon.allow_stretch = True
        self.index_icon.size = (44, 44)
        self.index_icon.color = self.color_id[1]
        self.index_icon.opacity = 0.4 if self.newest else 0.2
        self.add_widget(self.index_icon)


        # Index label
        self.index_label = Label()
        self.index_label.id = "index_label"
        self.index_label.halign = "center"
        self.index_label.color = self.color_id[1]
        self.index_label.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
        self.index_label.font_size = sp(23)
        self.index_label.text_size = (50, 50)
        self.index_label.markup = True
        self.index_label.max_lines = 1
        self.index_label.text = str(self.index)
        self.index_label.opacity = 0.8 if self.newest else 0.5
        self.add_widget(self.index_label)


        # Server last modified date formatted
        self.subtitle = Label()
        self.subtitle.size = (300, 30)
        self.subtitle.id = "subtitle"
        self.subtitle.halign = "left"
        self.subtitle.valign = "center"
        self.subtitle.font_size = sp(21)
        self.subtitle.text_size = (self.size_hint_max[0] * 0.91, self.size_hint_max[1])
        self.subtitle.shorten = True
        self.subtitle.markup = True
        self.subtitle.shorten_from = "right"
        self.subtitle.max_lines = 1
        self.subtitle.color = self.color_id[1]
        self.subtitle.default_opacity = 0.56
        self.subtitle.font_name = self.original_font
        self.subtitle.text = self.original_subtitle
        self.subtitle.opacity = self.subtitle.default_opacity
        self.add_widget(self.subtitle)


        # Type icon and info
        self.type_image = RelativeLayout()
        self.type_image.width = 400
        self.type_image.image = Image(source=os.path.join(constants.gui_assets, 'icons', 'big', f'{backup_object.type}_small.png'))
        self.type_image.image.allow_stretch = True
        self.type_image.image.size_hint_max = (65, 65)
        self.type_image.image.color = self.color_id[1]
        self.type_image.add_widget(self.type_image.image)

        def TemplateLabel():
            template_label = AlignLabel()
            template_label.halign = "right"
            template_label.valign = "middle"
            template_label.text_size = template_label.size
            template_label.font_size = sp(19)
            template_label.color = self.color_id[1]
            template_label.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
            template_label.width = 150
            return template_label

        self.type_image.version_label = TemplateLabel()
        self.type_image.version_label.color = self.color_id[1]
        self.type_image.version_label.text = backup_object.version.lower()
        self.type_image.version_label.opacity = 0.6

        self.type_image.type_label = TemplateLabel()
        self.type_image.type_label.text = backup_object.type.lower().replace("craft", "")
        self.type_image.type_label.font_size = sp(23)
        self.type_image.add_widget(self.type_image.version_label)
        self.type_image.add_widget(self.type_image.type_label)
        self.add_widget(self.type_image)

        self.bind(pos=self.resize_self)

        # If click_function
        if click_function:
            self.bind(on_press=click_function)

        # Animate opacity
        if fade_in > 0:
            self.opacity = 0
            self.title.opacity = 0

            Animation(opacity=1, duration=fade_in).start(self)
            Animation(opacity=1, duration=fade_in).start(self.title)
            Animation(opacity=self.subtitle.default_opacity, duration=fade_in).start(self.subtitle)


    def on_enter(self, *args):
        if not self.ignore_hover:
            self.animate_button(image=os.path.join(constants.gui_assets, f'{self.id}_hover.png'), color=self.color_id[0], hover_action=True)

    def on_leave(self, *args):
        if not self.ignore_hover:
            self.animate_button(image=os.path.join(constants.gui_assets, f'{self.id}{"_ro" if self.newest else ""}.png'), color=self.color_id[1], hover_action=False)

class ServerBackupRestoreScreen(MenuBackground):

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

    def gen_search_results(self, results, new_search=False, fade_in=True, animate_scroll=True, *args):

        # Set to proper page on favorite/unfavorite
        default_scroll = 1


        # Update page counter
        self.last_results = results
        self.max_pages = (len(results) / self.page_size).__ceil__()
        self.current_page = 1 if self.current_page == 0 or new_search else self.current_page


        self.page_switcher.update_index(self.current_page, self.max_pages)
        page_list = results[(self.page_size * self.current_page) - self.page_size:self.page_size * self.current_page]

        self.scroll_layout.clear_widgets()
        # gc.collect()

        # Generate header
        backup_count = len(results)
        header_content = "Select a back-up to restore"

        for child in self.header.children:
            if child.id == "text":
                child.text = header_content
                break


        # Show back-ups if they exist
        if backup_count != 0:

            # Clear and add all ServerButtons
            for x, backup_object in enumerate(page_list, 1):

                # Activated when addon is clicked
                def restore_backup(backup_obj, index, *args):

                    def restore_screen(file, *args):
                        constants.server_manager.current_server.backup.restore_file = file
                        screen_manager.current = 'ServerBackupRestoreProgressScreen'

                    selected_button = [item for item in self.scroll_layout.walk() if item.__class__.__name__ == "BackupButton"][index - 1]
                    screen_manager.current_screen.show_popup(
                        "query",
                        "Restore Back-up",
                        f"Are you sure you want to revert '{backup_obj.name}' to {backup_obj.date}?\n\nThis action can't be undone",
                        [None, functools.partial(Clock.schedule_once, functools.partial(restore_screen, backup_obj), 0.25)]
                    )


                # Add-on button click function
                self.scroll_layout.add_widget(
                    ScrollItem(
                        widget = BackupButton(
                            backup_object = backup_object,
                            fade_in = ((x if x <= 8 else 8) / self.anim_speed) if fade_in else 0,
                            index = x + ((self.current_page - 1) * self.page_size),
                            click_function = functools.partial(
                                restore_backup,
                                backup_object,
                                x
                            )
                        )
                    )
                )

            self.resize_bind()

        # Animate scrolling
        def set_scroll(*args):
            Animation.stop_all(self.scroll_layout.parent.parent)
            if animate_scroll:
                Animation(scroll_y=default_scroll, duration=0.1).start(self.scroll_layout.parent.parent)
            else:
                self.scroll_layout.parent.parent.scroll_y = default_scroll
        Clock.schedule_once(set_scroll, 0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'
        self.header = None
        self.scroll_layout = None
        self.blank_label = None
        self.page_switcher = None

        self.last_results = []
        self.page_size = 10
        self.current_page = 0
        self.max_pages = 0
        self.anim_speed = 10

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        super()._on_keyboard_down(keyboard, keycode, text, modifiers)

        # Press arrow keys to switch pages
        if keycode[1] in ['right', 'left'] and self.name == screen_manager.current_screen.name:
            self.switch_page(keycode[1])

    def generate_menu(self, **kwargs):
        server_obj = constants.server_manager.current_server
        backup_list = [backup.BackupObject(server_obj.name, file) for file in server_obj.backup.backup_stats['backup-list']]

        # Scroll list
        scroll_widget = ScrollViewWidget(position=(0.5, 0.52))
        scroll_anchor = AnchorLayout()
        self.scroll_layout = GridLayout(cols=1, spacing=15, size_hint_max_x=1250, size_hint_y=None, padding=[0, 30, 0, 30])


        # Bind / cleanup height on resize
        def resize_scroll(call_widget, grid_layout, anchor_layout, *args):
            call_widget.height = Window.height // 1.82
            grid_layout.cols = 2 if Window.width > grid_layout.size_hint_max_x else 1
            self.anim_speed = 13 if Window.width > grid_layout.size_hint_max_x else 10

            def update_grid(*args):
                anchor_layout.size_hint_min_y = grid_layout.height

            Clock.schedule_once(update_grid, 0)


        self.resize_bind = lambda*_: Clock.schedule_once(functools.partial(resize_scroll, scroll_widget, self.scroll_layout, scroll_anchor), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        self.scroll_layout.bind(minimum_height=self.scroll_layout.setter('height'))
        self.scroll_layout.id = 'scroll_content'


        # Scroll gradient
        scroll_top = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.795}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, 60))
        scroll_bottom = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.26}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, -60))

        # Generate buttons on page load
        header_content = "Select a back-up to restore"
        self.header = HeaderText(header_content, '', (0, 0.89))

        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'
        float_layout.add_widget(self.header)

        self.page_switcher = PageSwitcher(0, 0, (0.5, 0.887), self.switch_page)


        # Append scroll view items
        scroll_anchor.add_widget(self.scroll_layout)
        scroll_widget.add_widget(scroll_anchor)
        float_layout.add_widget(scroll_widget)
        float_layout.add_widget(scroll_top)
        float_layout.add_widget(scroll_bottom)
        float_layout.add_widget(self.page_switcher)

        buttons.append(exit_button('Back', (0.5, 0.11), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)

        float_layout.add_widget(generate_title(f"Back-up Manager: '{server_obj.name}'"))
        float_layout.add_widget(generate_footer(f"{server_obj.name}, Back-ups"))

        self.add_widget(float_layout)

        # Automatically generate results on page load
        constants.server_manager.refresh_list()
        self.gen_search_results(backup_list)

class ServerBackupRestoreProgressScreen(ProgressScreen):

    # Only replace this function when making a child screen
    # Set fail message in child functions to trigger an error
    def contents(self):

        def before_func(*args):

            # First, clean out any existing server in temp folder
            constants.safe_delete(constants.tempDir)
            constants.folder_check(constants.tmpsvr)

        # Original is percentage before this function, adjusted is a percent of hooked value
        def adjust_percentage(*args):
            original = self.last_progress
            adjusted = args[0]
            total = args[1] * 0.01
            final = original + round(adjusted * total)
            if final < 0:
                final = original
            self.progress_bar.update_progress(final)

        server_obj = constants.server_manager.current_server
        restore_date = server_obj.backup.restore_file.date
        restore_path = server_obj.backup.restore_file.path
        self.page_contents = {

            # Page name
            'title': f"Restoring '{server_obj.name}'",

            # Header text
            'header': "Sit back and relax, it's automation time...",

            # Tuple of tuples for steps (label, function, percent)
            # Percent of all functions must total 100
            # Functions must return True, or default error will be executed
            'default_error': 'There was an issue, please try again later',

            'function_list': (),

            # Function to run before steps (like checking for an internet connection)
            'before_function': before_func,

            # Function to run after everything is complete (like cleaning up the screen tree) will only run if no error
            'after_function': functools.partial(open_server, server_obj.name, True, f"'{server_obj.name}' was restored to {restore_date}"),

            # Screen to go to after complete
            'next_screen': None
        }

        # Create function list
        function_list = [
            ('Verifying Java installation', functools.partial(constants.java_check, functools.partial(adjust_percentage, 30)), 0),
            ('Restoring back-up', functools.partial(constants.restore_server, restore_path, functools.partial(adjust_percentage, 70)), 0),
        ]

        self.page_contents['function_list'] = tuple(function_list)



# Server Access Control ------------------------------------------------------------------------------------------------

class ServerAclScreen(CreateServerAclScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.menu_taskbar = None

    def generate_menu(self, **kwargs):

        # If self._hash doesn't match, set list to ops by default
        if self._hash != constants.server_manager.current_server._hash:
            self.acl_object = constants.server_manager.current_server.acl
            self._hash = constants.server_manager.current_server._hash
            self.current_list = 'ops'

        self.show_panel = False

        self.filter_text = ""
        self.currently_filtering = False

        # Scroll list
        self.scroll_widget = RecycleViewWidget(position=(0.5, 0.455), view_class=RuleButton)
        self.scroll_layout = RecycleGridLayout(spacing=[110, -15], size_hint_y=None, padding=[60, 20, 0, 30])
        test_rule = RuleButton()

        # Bind / cleanup height on resize
        def resize_scroll(*args):
            self.scroll_widget.height = Window.height // 1.69
            rule_width = test_rule.width + self.scroll_layout.spacing[0] + 2
            rule_width = int(((Window.width // rule_width) // 1) - 2)

            self.scroll_layout.cols = rule_width
            self.scroll_layout.rows = 2 if len(self.scroll_widget.data) <= rule_width else None

            self.user_panel.x = Window.width - (self.user_panel.size_hint_max[0] * 0.93)

            # Reposition header
            for child in self.header.children:
                if child.id == "text":
                    child.halign = "left"
                    child.text_size[0] = 500
                    child.x = Window.width / 2 + 240
                    break

            self.search_label.pos_hint = {"center_x": (0.28 if Window.width < 1300 else 0.5), "center_y": 0.42}
            self.search_label.text_size = (Window.width / 3, 500)

        self.resize_bind = lambda *_: Clock.schedule_once(functools.partial(resize_scroll), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        self.scroll_layout.bind(minimum_height=self.scroll_layout.setter('height'))
        self.scroll_layout.id = 'scroll_content'

        # Scroll gradient
        scroll_top = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.735}, pos=self.scroll_widget.pos, size=(self.scroll_widget.width // 1.5, 60))
        scroll_bottom = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.175}, pos=self.scroll_widget.pos, size=(self.scroll_widget.width // 1.5, -60))

        # Generate buttons on page load
        selector_text = "operators" if self.current_list == "ops" else "bans" if self.current_list == "bans" else "whitelist"
        page_selector = DropButton(selector_text, (0.5, 0.89), options_list=['operators', 'bans', 'whitelist'], input_name='ServerAclTypeInput', x_offset=-210, facing='center', custom_func=self.update_list)
        header_content = ""
        self.header = HeaderText(header_content, '', (0, 0.89), fixed_x=True, no_line=True)

        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'
        float_layout.add_widget(self.header)

        # Search bar
        self.search_bar = AclInput(pos_hint={"center_x": 0.5, "center_y": 0.815})
        buttons.append(input_button('Add Rules...', (0.5, 0.815), input_name='AclInput'))

        # Whitelist toggle button
        def toggle_whitelist(boolean):
            self.acl_object.toggle_whitelist(boolean)

            Clock.schedule_once(
                functools.partial(
                    self.show_banner,
                    (0.553, 0.902, 0.675, 1) if boolean else (0.937, 0.831, 0.62, 1),
                    f"Server whitelist {'en' if boolean else 'dis'}abled",
                    "shield-checkmark-outline.png" if boolean else "shield-disabled-outline.png",
                    2,
                    {"center_x": 0.5, "center_y": 0.965}
                ), 0
            )

            # Update list
            self.update_list('wl', reload_children=True, reload_panel=True)

        self.whitelist_toggle = toggle_button('whitelist', (0.5, 0.89), default_state=self.acl_object.server['whitelist'], x_offset=-395, custom_func=toggle_whitelist)

        # Legend for rule types
        self.list_header = BoxLayout(orientation="horizontal", pos_hint={"center_x": 0.5, "center_y": 0.749}, size_hint_max=(400, 100))
        self.list_header.global_rule = RelativeLayout()
        self.list_header.global_rule.add_widget(BannerObject(size=(125, 32), color=test_rule.global_icon_color, text="global rule", icon="earth-sharp.png", icon_side="left"))
        self.list_header.add_widget(self.list_header.global_rule)

        self.list_header.enabled_rule = RelativeLayout()
        self.list_header.enabled_rule.add_widget(BannerObject(size=(120, 32), color=(1, 1, 1, 1), text=" ", icon="add.png"))
        self.list_header.add_widget(self.list_header.enabled_rule)

        self.list_header.disabled_rule = RelativeLayout()
        self.list_header.disabled_rule.add_widget(BannerObject(size=(120, 32), color=(1, 1, 1, 1), text=" ", icon="add.png"))
        self.list_header.add_widget(self.list_header.disabled_rule)

        # Add blank label to the center, then load self.gen_search_results()
        self.blank_label = Label()
        self.blank_label.text = ""
        self.blank_label.font_name = os.path.join(constants.gui_assets, 'fonts', constants.fonts['italic'])
        self.blank_label.pos_hint = {"center_x": 0.5, "center_y": 0.48}
        self.blank_label.font_size = sp(23)
        self.blank_label.opacity = 0
        self.blank_label.color = (0.6, 0.6, 1, 0.35)
        float_layout.add_widget(self.blank_label)

        # Lol search label idek
        self.search_label = Label()
        self.search_label.text = ""
        self.search_label.halign = "center"
        self.search_label.valign = "center"
        self.search_label.font_name = os.path.join(constants.gui_assets, 'fonts', constants.fonts['italic'])
        self.search_label.pos_hint = {"center_x": 0.28, "center_y": 0.42}
        self.search_label.font_size = sp(25)
        self.search_label.color = (0.6, 0.6, 1, 0.35)
        float_layout.add_widget(self.search_label)

        # Controls button
        def show_controls():

            controls_text = """This menu shows enabled rules from files like 'ops.json', and disabled rules as others who have joined. Global rules are applied to every server. Rules can be modified in a few different ways:

• Right-click a rule to view, and more options

• Left-click a rule to toggle permission

• Press middle-mouse to toggle globally

Rules can be filtered with the search box, and can be added with the 'ADD RULES' button or by pressing 'TAB'. The visible list can be switched between operators, bans, and the whitelist from the drop-down at the top."""

            Clock.schedule_once(
                functools.partial(
                    self.show_popup,
                    "controls",
                    "Controls",
                    controls_text,
                    (None)
                ),
                0
            )

        self.controls_button = IconButton('controls', {}, (70, 110), (None, None), 'question.png', clickable=True, anchor='right', click_func=show_controls)

        # User panel
        self.user_panel = AclRulePanel()
        self.user_panel.pos_hint = {"center_y": 0.44}

        # Append scroll view items
        self.scroll_widget.add_widget(self.scroll_layout)
        float_layout.add_widget(self.scroll_widget)
        float_layout.add_widget(scroll_top)
        float_layout.add_widget(scroll_bottom)
        float_layout.add_widget(page_selector)
        float_layout.add_widget(self.list_header)
        float_layout.add_widget(self.search_bar)
        float_layout.add_widget(self.whitelist_toggle)
        float_layout.add_widget(self.user_panel)

        buttons.append(exit_button('Back', (0.5, -1), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)

        menu_name = f"{constants.server_manager.current_server.name}, Access Control"
        float_layout.add_widget(generate_title(f"Access Control Manager: '{constants.server_manager.current_server.name}'"))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)


        # Add ManuTaskbar
        self.menu_taskbar = MenuTaskbar(selected_item='access control')
        self.add_widget(self.menu_taskbar)

        # Add controls after taskbar because it's unclickable for some reason
        float_layout.add_widget(self.controls_button)


        # Generate page content
        self.update_list(self.current_list, reload_children=True)

        # Generate user panel info
        current_list = acl.deepcopy(self.acl_object.rules[self.current_list])
        if self.current_list == "bans":
            current_list.extend(acl.deepcopy(self.acl_object.rules['subnets']))

        if self.acl_object.displayed_rule and current_list:
            self.update_user_panel(self.acl_object.displayed_rule.rule, self.user_panel.displayed_scope)
        else:
            self.update_user_panel(None, None)

class ServerAclRuleScreen(CreateServerAclRuleScreen):

    def generate_menu(self, **kwargs):
        # Generate buttons on page load

        class HintLabel(RelativeLayout):

            def icon_pos(self, *args):
                self.text.texture_update()
                self.icon.pos_hint = {"center_x": 0.57 - (0.005 * self.text.texture_size[0]), "center_y": 0.95}

            def __init__(self, pos, label, **kwargs):
                super().__init__(**kwargs)

                self.pos_hint = {"center_x": 0.5, "center_y": pos}
                self.size_hint_max = (100, 50)

                self.text = Label()
                self.text.id = 'text'
                self.text.size_hint = (None, None)
                self.text.markup = True
                self.text.halign = "center"
                self.text.valign = "center"
                self.text.text = "        " + label
                self.text.font_size = sp(22)
                self.text.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
                self.text.color = (0.6, 0.6, 1, 0.55)

                self.icon = Image()
                self.icon.id = 'icon'
                self.icon.source = os.path.join(constants.gui_assets, 'icons', 'information-circle-outline.png')
                self.icon.pos_hint = {"center_y": 0.95}
                self.icon.color = (0.6, 0.6, 1, 1)

                self.add_widget(self.text)
                self.add_widget(self.icon)

                self.bind(size=self.icon_pos)
                self.bind(pos=self.icon_pos)


        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'

        self.current_list = screen_manager.get_screen("ServerAclScreen").current_list
        self.acl_object = screen_manager.get_screen("ServerAclScreen").acl_object

        if self.current_list == "bans":
            header_message = "Enter usernames/IPs delimited, by, commas"
            float_layout.add_widget(HintLabel(0.464, "Use   [color=#FFFF33]!g <rule>[/color]   to apply globally on all servers"))
            float_layout.add_widget(HintLabel(0.374, "You can ban IP ranges/whitelist:   [color=#FF6666]192.168.0.0-150[/color], [color=#66FF88]!w 192.168.1.1[/color]"))
        else:
            header_message = "Enter usernames delimited, by, commas"
            float_layout.add_widget(HintLabel(0.425, "Use   [color=#FFFF33]!g <rule>[/color]   to apply globally on all servers"))

        float_layout.add_widget(InputLabel(pos_hint={"center_x": 0.5, "center_y": 0.72}))
        float_layout.add_widget(HeaderText(header_message, '', (0, 0.8)))
        self.acl_input = AclRuleInput(pos_hint={"center_x": 0.5, "center_y": 0.64}, text="")
        float_layout.add_widget(self.acl_input)

        buttons.append(next_button('Add Rules', (0.5, 0.24), True, next_screen='ServerAclScreen'))
        buttons.append(exit_button('Back', (0.5, 0.14), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)

        menu_name = f"{constants.server_manager.current_server.name}, Access Control"
        list_name = "Operators" if self.current_list == "ops" else "Bans" if self.current_list == "bans" else "Whitelist"
        float_layout.add_widget(generate_title(f"Access Control Manager: Add {list_name}"))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)
        self.acl_input.grab_focus()



# Server Add-on Manager ------------------------------------------------------------------------------------------------

class AddonListButton(HoverButton):

    def toggle_enabled(self, enabled, *args):
        self.enabled = enabled
        self.title.text_size = (self.size_hint_max[0] * (0.7 if enabled else 0.94), self.size_hint_max[1])
        self.background_normal = os.path.join(constants.gui_assets, f'{self.id}{"" if self.enabled else "_disabled"}.png')

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

    def animate_addon(self, image, color, **kwargs):
        image_animate = Animation(duration=0.05)

        def f(w):
            w.background_normal = image

        Animation(color=color, duration=0.06).start(self.title)
        Animation(color=color, duration=0.06).start(self.subtitle)

        a = Animation(duration=0.0)
        a.on_complete = functools.partial(f)

        image_animate += a

        image_animate.start(self)

    def resize_self(self, *args):

        # Title and description
        padding = 2.17
        self.title.pos = (self.x + (self.title.text_size[0] / padding), self.y + 31)
        self.subtitle.pos = (self.x + (self.subtitle.text_size[0] / padding) - 1, self.y)
        self.hover_text.pos = (self.x + (self.title.text_size[0] / padding) - 15, self.y + 15)

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

    def __init__(self, properties, click_function=None, enabled=False, fade_in=0.0, highlight=False, **kwargs):
        super().__init__(**kwargs)

        self.enabled = enabled
        self.properties = properties
        self.border = (-5, -5, -5, -5)
        self.color_id = [(0.05, 0.05, 0.1, 1), (0.65, 0.65, 1, 1)] if self.enabled else [(0.05, 0.1, 0.1, 1), (1, 0.6, 0.7, 1)]
        self.pos_hint = {"center_x": 0.5, "center_y": 0.6}
        self.size_hint_max = (580, 80)
        self.id = "addon_button"
        self.background_normal = os.path.join(constants.gui_assets, f'{self.id}.png')
        self.background_down = os.path.join(constants.gui_assets, f'{self.id}_click_white.png')
        self.disabled_banner = None


        # Delete button
        def delete_hover(*args):
            def change_color(*args):
                if self.hovered:
                    self.hover_text.text = 'UNINSTALL ADD-ON'
                    self.background_normal = os.path.join(constants.gui_assets, "server_button_favorite_hover.png")
                    self.background_color = (1, 1, 1, 1)
            Clock.schedule_once(change_color, 0.07)
        def delete_on_leave(*args):
            def change_color(*args):
                self.hover_text.text = ('DISABLE ADD-ON' if self.enabled else 'ENABLE ADD-ON')
                if self.hovered:
                    self.background_normal = os.path.join(constants.gui_assets, "addon_button_hover_white.png")
                    self.background_color = ((1, 0.5, 0.65, 1) if self.enabled else (0.3, 1, 0.6, 1))
            Clock.schedule_once(change_color, 0.15)
        def delete_click(*args):
            # Delete addon and reload list
            def reprocess_page(*args):
                addon_manager = constants.server_manager.current_server.addon
                addon_manager.delete_addon(self.properties)
                addon_screen = screen_manager.current_screen
                addon_screen.gen_search_results(addon_manager.return_single_list(), fade_in=True)

                # Show banner if server is running
                if addon_manager.hash_changed():
                    Clock.schedule_once(
                        functools.partial(
                            screen_manager.current_screen.show_banner,
                            (0.937, 0.831, 0.62, 1),
                            f"A server restart is required to apply changes",
                            "sync.png",
                            3,
                            {"center_x": 0.5, "center_y": 0.965}
                        ), 0.25
                    )

                else:
                    Clock.schedule_once(
                        functools.partial(
                            screen_manager.current_screen.show_banner,
                            (1, 0.5, 0.65, 1),
                            f"'{self.properties.name}' was uninstalled",
                            "trash-sharp.png",
                            2.5,
                            {"center_x": 0.5, "center_y": 0.965}
                        ), 0.25
                    )

                # Switch pages if page is empty
                if (len(addon_screen.scroll_layout.children) == 0) and (len(constants.new_server_info['addon_objects']) > 0):
                    addon_screen.switch_page("left")


            Clock.schedule_once(
                functools.partial(
                    screen_manager.current_screen.show_popup,
                    "warning_query",
                    f'Uninstall {self.properties.name}',
                    "Do you want to permanently uninstall this add-on?\n\nYou'll need to re-import or download it again",
                    (None, functools.partial(reprocess_page))
                ),
                0
            )
        self.delete_layout = RelativeLayout(opacity=0)
        self.delete_button = IconButton('', {}, (0, 0), (None, None), 'trash-sharp.png', clickable=True, force_color=[[(0.05, 0.05, 0.1, 1), (0.01, 0.01, 0.01, 1)], 'pink'], anchor='right', click_func=delete_click)
        self.delete_button.button.bind(on_enter=delete_hover)
        self.delete_button.button.bind(on_leave=delete_on_leave)
        self.delete_layout.add_widget(self.delete_button)
        self.add_widget(self.delete_layout)


        # Hover text
        self.hover_text = Label()
        self.hover_text.id = 'hover_text'
        self.hover_text.size_hint = (None, None)
        self.hover_text.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        self.hover_text.text = ('DISABLE ADD-ON' if self.enabled else 'ENABLE ADD-ON')
        self.hover_text.font_size = sp(23)
        self.hover_text.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["bold"]}.ttf')
        self.hover_text.color = (0.1, 0.1, 0.1, 1)
        self.hover_text.halign = "center"
        self.hover_text.text_size = (self.size_hint_max[0] * 0.94, self.size_hint_max[1])
        self.hover_text.opacity = 0
        self.add_widget(self.hover_text)


        # Loading stuffs
        self.original_subtitle = self.properties.subtitle if self.properties.subtitle else "Description unavailable"
        self.original_font = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["regular"]}.ttf')


        # Title of Addon
        self.title = Label()
        self.title.id = "title"
        self.title.halign = "left"
        self.title.color = self.color_id[1]
        self.title.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
        self.title.font_size = sp(25)
        self.title.text_size = (self.size_hint_max[0] * 0.94, self.size_hint_max[1])
        self.title.shorten = True
        self.title.markup = True
        self.title.shorten_from = "right"
        self.title.max_lines = 1
        self.title.text = f"{self.properties.name}  [color=#434368]-[/color]  {self.properties.author if self.properties.author else 'Unknown'}"
        self.add_widget(self.title)


        # Description of Addon
        self.subtitle = Label()
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
        self.highlight_border.source = os.path.join(constants.gui_assets, 'server_button_highlight.png')
        self.highlight_layout.add_widget(self.highlight_border)
        self.highlight_layout.width = self.size_hint_max[0]
        self.highlight_layout.height = self.size_hint_max[1]
        self.add_widget(self.highlight_layout)

        if highlight:
            self.highlight()


        # If self.enabled is false, and self.properties.version, display version where "enabled" logo is
        self.bind(pos=self.resize_self)
        if not enabled:
            self.toggle_enabled(enabled)

        # If click_function
        if click_function:
            self.bind(on_press=click_function)

        # Animate opacity
        if fade_in > 0:
            self.opacity = 0
            self.title.opacity = 0

            Animation(opacity=1, duration=fade_in).start(self)
            Animation(opacity=1, duration=fade_in).start(self.title)
            Animation(opacity=0.56, duration=fade_in).start(self.subtitle)

    def on_enter(self, *args):
        if not self.ignore_hover:

            # Hide disabled banner if it exists
            if self.disabled_banner:
                Animation.stop_all(self.disabled_banner)
                Animation(opacity=0, duration=0.13).start(self.disabled_banner)

            # Fade button to hover state
            if not self.delete_button.button.hovered:
                self.animate_addon(image=os.path.join(constants.gui_assets, f'{self.id}_hover_white.png'), color=self.color_id[0], hover_action=True)

            # Show delete button
            Animation.stop_all(self.delete_layout)
            Animation(opacity=1, duration=0.13).start(self.delete_layout)

            # Hide text
            Animation(opacity=0, duration=0.13).start(self.title)
            Animation(opacity=0, duration=0.13).start(self.subtitle)
            Animation(opacity=1, duration=0.13).start(self.hover_text)

            # Change button color based on state
            self.background_color = ((1, 0.5, 0.65, 1) if self.enabled else (0.3, 1, 0.6, 1))

    def on_leave(self, *args):
        if not self.ignore_hover:

            # Hide disabled banner if it exists
            if self.disabled_banner:
                Animation.stop_all(self.disabled_banner)
                Animation(opacity=1, duration=0.13).start(self.disabled_banner)

            # Fade button to default state
            self.animate_addon(image=os.path.join(constants.gui_assets, f'{self.id}{"" if self.enabled else "_disabled"}.png'), color=self.color_id[1], hover_action=False)

            # Hide delete button
            Animation.stop_all(self.delete_layout)
            Animation(opacity=0, duration=0.13).start(self.delete_layout)

            # Show text
            Animation(opacity=1, duration=0.13).start(self.title)
            Animation(opacity=self.default_subtitle_opacity, duration=0.13).start(self.subtitle)
            Animation(opacity=0, duration=0.13).start(self.hover_text)

            # Reset button color
            def reset_color(*args):
                self.background_color = (1, 1, 1, 1)
            Clock.schedule_once(reset_color, 0.1)

    def loading(self, load_state, *args):
        if load_state:
            self.subtitle.text = "Loading add-on info..."
            self.subtitle.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
        else:
            self.subtitle.text = self.original_subtitle
            self.subtitle.font_name = self.original_font

class ServerAddonScreen(MenuBackground):

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

        addon_manager = constants.server_manager.current_server.addon
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
                        if default_scroll < 0.21:
                            default_scroll = 0
                        if default_scroll > 0.97:
                            default_scroll = 1
                    break


        self.last_results = results
        self.max_pages = (len(results) / self.page_size).__ceil__()
        self.current_page = 1 if self.current_page == 0 or new_search else self.current_page

        self.page_switcher.update_index(self.current_page, self.max_pages)
        page_list = results[(self.page_size * self.current_page) - self.page_size:self.page_size * self.current_page]

        self.scroll_layout.clear_widgets()
        # gc.collect()


        # Animate scrolling
        def set_scroll(*args):
            Animation.stop_all(self.scroll_layout.parent.parent)
            if animate_scroll:
                Animation(scroll_y=default_scroll, duration=0.1).start(self.scroll_layout.parent.parent)
            else:
                self.scroll_layout.parent.parent.scroll_y = default_scroll
        Clock.schedule_once(set_scroll, 0)


        # Generate header
        addon_count = len(results)
        enabled_count = len([addon for addon in addon_manager.installed_addons['enabled'] if (addon.author != 'GeyserMC' and not (addon.name.startswith('Geyser') or addon.name == 'floodgate'))])
        disabled_count = len(addon_manager.installed_addons['disabled'])
        very_bold_font = os.path.join(constants.gui_assets, 'fonts', constants.fonts["very-bold"])
        header_content = "Installed Add-ons  [color=#494977]-[/color]  " + ('[color=#6A6ABA]No items[/color]' if addon_count == 0 else f'[font={very_bold_font}]1[/font] item' if addon_count == 1 else f'[font={very_bold_font}]{enabled_count:,}{("/[color=#FF8793]" + str(disabled_count) + "[/color]") if disabled_count > 0 else ""}[/font] items')

        if addon_manager.hash_changed():
            icons = os.path.join(constants.gui_assets, 'fonts', constants.fonts['icons'])
            header_content = f"[color=#EFD49E][font={icons}]y[/font] " + header_content + "[/color]"


        for child in self.header.children:
            if child.id == "text":
                child.text = header_content
                break


        # If there are no addons, say as much with a label
        if addon_count == 0:
            self.blank_label.text = "Import or Download add-ons below"
            constants.hide_widget(self.blank_label, False)
            self.blank_label.opacity = 0
            Animation(opacity=1, duration=0.2).start(self.blank_label)
            self.max_pages = 0
            self.current_page = 0

        # If there are addons, display them here
        else:
            constants.hide_widget(self.blank_label, True)

            # Create list of addon names
            installed_addon_names = [addon.name for addon in self.server.addon.return_single_list()]

            # Clear and add all addons
            for x, addon_object in enumerate(page_list, 1):

                # Activated when addon is clicked
                def toggle_addon(index, *args):
                    addon = index

                    if len(addon.name) < 26:
                        addon_name = addon.name
                    else:
                        addon_name = addon.name[:23] + "..."


                    # Toggle addon state
                    addon_manager.addon_state(addon, enabled=not addon.enabled)
                    addon_list = [addon for addon in addon_manager.return_single_list() if (addon.author != 'GeyserMC' and not (addon.name.startswith('Geyser') or addon.name == 'floodgate'))]
                    self.gen_search_results(addon_list, fade_in=False, highlight=addon.hash, animate_scroll=True)


                    # Show banner if server is running
                    if addon_manager.hash_changed():
                        Clock.schedule_once(
                            functools.partial(
                                self.show_banner,
                                (0.937, 0.831, 0.62, 1),
                                f"A server restart is required to apply changes",
                                "sync.png",
                                3,
                                {"center_x": 0.5, "center_y": 0.965}
                            ), 0.25
                        )

                    else:
                        Clock.schedule_once(
                            functools.partial(
                                self.show_banner,
                                (1, 0.5, 0.65, 1) if addon.enabled else (0.553, 0.902, 0.675, 1),
                                f"'{addon_name}' is now {'disabled' if addon.enabled else 'enabled'}",
                                "close-circle-sharp.png" if addon.enabled else "checkmark-circle-sharp.png",
                                2.5,
                                {"center_x": 0.5, "center_y": 0.965}
                            ), 0.25
                        )


                # Add-on button click function
                self.scroll_layout.add_widget(
                    ScrollItem(
                        widget = AddonListButton(
                            properties = addon_object,
                            enabled = addon_object.enabled,
                            fade_in = ((x if x <= 8 else 8) / self.anim_speed) if fade_in else 0,
                            highlight = (highlight == addon_object.hash),
                            click_function = functools.partial(
                                toggle_addon,
                                addon_object,
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
        self.page_switcher = None
        self.menu_taskbar = None

        self.last_results = []
        self.page_size = 20
        self.current_page = 0
        self.max_pages = 0
        self.anim_speed = 10

        self.server = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        super()._on_keyboard_down(keyboard, keycode, text, modifiers)

        # Press arrow keys to switch pages
        if keycode[1] in ['right', 'left'] and self.name == screen_manager.current_screen.name:
            self.switch_page(keycode[1])

    def generate_menu(self, **kwargs):
        self.server = constants.server_manager.current_server

        # Scroll list
        scroll_widget = ScrollViewWidget(position=(0.5, 0.52))
        scroll_anchor = AnchorLayout()
        self.scroll_layout = GridLayout(cols=1, spacing=15, size_hint_max_x=1250, size_hint_y=None, padding=[0, 30, 0, 30])


        # Bind / cleanup height on resize
        def resize_scroll(call_widget, grid_layout, anchor_layout, *args):
            call_widget.height = Window.height // 1.85
            grid_layout.cols = 2 if Window.width > grid_layout.size_hint_max_x else 1
            self.anim_speed = 13 if Window.width > grid_layout.size_hint_max_x else 10

            def update_grid(*args):
                anchor_layout.size_hint_min_y = grid_layout.height

            Clock.schedule_once(update_grid, 0)


        self.resize_bind = lambda*_: Clock.schedule_once(functools.partial(resize_scroll, scroll_widget, self.scroll_layout, scroll_anchor), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        self.scroll_layout.bind(minimum_height=self.scroll_layout.setter('height'))
        self.scroll_layout.id = 'scroll_content'


        # Scroll gradient
        scroll_top = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.795}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, 60))
        scroll_bottom = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.27}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, -60))

        # Generate buttons on page load
        addon_count = len(self.server.addon.return_single_list())
        very_bold_font = os.path.join(constants.gui_assets, 'fonts', constants.fonts["very-bold"])
        header_content = "Installed Add-ons  [color=#494977]-[/color]  " + ('[color=#6A6ABA]No items[/color]' if addon_count == 0 else f'[font={very_bold_font}]1[/font] item' if addon_count == 1 else f'[font={very_bold_font}]{addon_count}[/font] items')
        self.header = HeaderText(header_content, '', (0, 0.89))

        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'
        float_layout.add_widget(self.header)


        # Add blank label to the center, then load self.gen_search_results()
        self.blank_label = Label()
        self.blank_label.text = "Import or Download add-ons below"
        self.blank_label.font_name = os.path.join(constants.gui_assets, 'fonts', constants.fonts['italic'])
        self.blank_label.pos_hint = {"center_x": 0.5, "center_y": 0.55}
        self.blank_label.font_size = sp(24)
        self.blank_label.color = (0.6, 0.6, 1, 0.35)
        float_layout.add_widget(self.blank_label)

        self.page_switcher = PageSwitcher(0, 0, (0.5, 0.887), self.switch_page)


        # Append scroll view items
        scroll_anchor.add_widget(self.scroll_layout)
        scroll_widget.add_widget(scroll_anchor)
        float_layout.add_widget(scroll_widget)
        float_layout.add_widget(scroll_top)
        float_layout.add_widget(scroll_bottom)
        float_layout.add_widget(self.page_switcher)

        bottom_buttons = RelativeLayout()
        bottom_buttons.size_hint_max_x = 312
        bottom_buttons.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        bottom_buttons.add_widget(main_button('Import', (0, 0.202), 'download-outline.png', width=300, icon_offset=-115, auto_adjust_icon=True))
        bottom_buttons.add_widget(main_button('Download', (1, 0.202), 'cloud-download-outline.png', width=300, icon_offset=-115, auto_adjust_icon=True))
        buttons.append(exit_button('Back', (0.5, -1), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)
        float_layout.add_widget(bottom_buttons)

        menu_name = f"{self.server.name}, Add-ons"
        float_layout.add_widget(generate_title(f"Add-on Manager: '{self.server.name}'"))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)


        # Add ManuTaskbar
        self.menu_taskbar = MenuTaskbar(selected_item='add-ons')
        self.add_widget(self.menu_taskbar)


        # Automatically generate results (installed add-ons) on page load
        addon_list = [addon for addon in self.server.addon.return_single_list() if (addon.author != 'GeyserMC' and not (addon.name.startswith('Geyser') or addon.name == 'floodgate'))]
        self.gen_search_results(addon_list)

        # Show banner if server is running
        if constants.server_manager.current_server.addon.hash_changed():
            Clock.schedule_once(
                functools.partial(
                    self.show_banner,
                    (0.937, 0.831, 0.62, 1),
                    f"A server restart is required to apply changes",
                    "sync.png",
                    3,
                    {"center_x": 0.5, "center_y": 0.965}
                ), 0.25
            )

class ServerAddonSearchScreen(MenuBackground):

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
        addon_manager = constants.server_manager.current_server.addon

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
            # gc.collect()


            # Generate header
            addon_count = len(results)
            very_bold_font = os.path.join(constants.gui_assets, 'fonts', constants.fonts["very-bold"])
            search_text = self.search_bar.previous_search if (len(self.search_bar.previous_search) <= 25) else self.search_bar.previous_search[:22] + "..."
            header_content = f"Search for '{search_text}'  [color=#494977]-[/color]  " + ('[color=#6A6ABA]No results[/color]' if addon_count == 0 else f'[font={very_bold_font}]1[/font] item' if addon_count == 1 else f'[font={very_bold_font}]{addon_count:,}[/font] items')

            for child in self.header.children:
                if child.id == "text":
                    child.text = header_content
                    break


            # If there are no addons, say as much with a label
            if addon_count == 0:
                self.blank_label.text = "there are no items to display"
                constants.hide_widget(self.blank_label, False)
                self.blank_label.opacity = 0
                Animation(opacity=1, duration=0.2).start(self.blank_label)
                self.max_pages = 0
                self.current_page = 0

            # If there are addons, display them here
            else:
                constants.hide_widget(self.blank_label, True)

                # Create list of addon names
                installed_addon_names = [addon.name for addon in addon_manager.return_single_list()]

                # Clear and add all addons
                for x, addon_object in enumerate(page_list, 1):


                    # Function to download addon info
                    def load_addon(addon, index):
                        selected_button = [item for item in self.scroll_layout.walk() if item.__class__.__name__ == "AddonButton"][index-1]

                        # Cache updated addon info into button, or skip if it's already cached
                        if selected_button.properties:
                            if not selected_button.properties.versions or not selected_button.properties.description:
                                new_addon_info = addons.get_addon_info(addon, constants.server_manager.current_server.properties_dict())
                                selected_button.properties = new_addon_info

                        Clock.schedule_once(functools.partial(selected_button.loading, False), 1)

                        return selected_button.properties, selected_button.installed


                    # Function to install addon
                    def install_addon(index):

                        selected_button = [item for item in self.scroll_layout.walk() if item.__class__.__name__ == "AddonButton"][index-1]
                        addon = selected_button.properties
                        selected_button.toggle_installed(not selected_button.installed)

                        if len(addon.name) < 26:
                            addon_name = addon.name
                        else:
                            addon_name = addon.name[:23] + "..."

                        # Install
                        if selected_button.installed:
                            threading.Timer(0, functools.partial(addon_manager.download_addon, addon)).start()

                            # Show banner if server is running
                            if addon_manager.hash_changed():
                                Clock.schedule_once(
                                    functools.partial(
                                        self.show_banner,
                                        (0.937, 0.831, 0.62, 1),
                                        f"A server restart is required to apply changes",
                                        "sync.png",
                                        3,
                                        {"center_x": 0.5, "center_y": 0.965}
                                    ), 0.25
                                )

                            else:
                                Clock.schedule_once(
                                    functools.partial(
                                        self.show_banner,
                                        (0.553, 0.902, 0.675, 1),
                                        f"Installed '{addon_name}'",
                                        "checkmark-circle-sharp.png",
                                        2.5,
                                        {"center_x": 0.5, "center_y": 0.965}
                                    ), 0.25
                                )

                        # Uninstall
                        else:
                            for installed_addon in addon_manager.return_single_list():
                                if installed_addon.name == addon.name:
                                    addon_manager.delete_addon(installed_addon)

                                    # Show banner if server is running
                                    if addon_manager.hash_changed():
                                        Clock.schedule_once(
                                            functools.partial(
                                                self.show_banner,
                                                (0.937, 0.831, 0.62, 1),
                                                f"A server restart is required to apply changes",
                                                "sync.png",
                                                3,
                                                {"center_x": 0.5, "center_y": 0.965}
                                            ), 0.25
                                        )

                                    else:
                                        Clock.schedule_once(
                                            functools.partial(
                                                self.show_banner,
                                                (1, 0.5, 0.65, 1),
                                                f"'{addon_name}' was uninstalled",
                                                "trash-sharp.png",
                                                2.5,
                                                {"center_x": 0.5, "center_y": 0.965}
                                            ), 0.25
                                        )

                                    break

                        return addon, selected_button.installed


                    # Activated when addon is clicked
                    def view_addon(addon, index, *args):
                        selected_button = [item for item in self.scroll_layout.walk() if item.__class__.__name__ == "AddonButton"][index - 1]

                        selected_button.loading(True)

                        Clock.schedule_once(
                            functools.partial(
                                self.show_popup,
                                "addon",
                                " ",
                                " ",
                                (None, functools.partial(install_addon, index)),
                                functools.partial(load_addon, addon, index)
                            ),
                            0
                        )


                    # Add-on button click function
                    self.scroll_layout.add_widget(
                        ScrollItem(
                            widget = AddonButton(
                                properties = addon_object,
                                installed = addon_object.name in installed_addon_names,
                                fade_in = ((x if x <= 8 else 8) / self.anim_speed),
                                click_function = functools.partial(
                                    view_addon,
                                    addon_object,
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
        if keycode[1] in ['right', 'left'] and self.name == screen_manager.current_screen.name:
            self.switch_page(keycode[1])
        elif keycode[1] == "tab" and self.name == screen_manager.current_screen.name:
            for widget in self.search_bar.children:
                try:
                    if widget.id == "search_input":
                        widget.grab_focus()
                        break
                except AttributeError:
                    pass

    def generate_menu(self, **kwargs):

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

            Clock.schedule_once(update_grid, 0)


        self.resize_bind = lambda*_: Clock.schedule_once(functools.partial(resize_scroll, scroll_widget, self.scroll_layout, scroll_anchor), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        self.scroll_layout.bind(minimum_height=self.scroll_layout.setter('height'))
        self.scroll_layout.id = 'scroll_content'

        # Scroll gradient
        scroll_top = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.715}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, 60))
        scroll_bottom = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.17}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, -60))

        # Generate buttons on page load
        addon_count = 0
        very_bold_font = os.path.join(constants.gui_assets, 'fonts', constants.fonts["very-bold"])
        header_content = "Add-on Search"
        self.header = HeaderText(header_content, '', (0, 0.89))

        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'
        float_layout.add_widget(self.header)

        # Add blank label to the center
        self.blank_label = Label()
        self.blank_label.text = "search for add-ons above"
        self.blank_label.font_name = os.path.join(constants.gui_assets, 'fonts', constants.fonts['italic'])
        self.blank_label.pos_hint = {"center_x": 0.5, "center_y": 0.48}
        self.blank_label.font_size = sp(24)
        self.blank_label.color = (0.6, 0.6, 1, 0.35)
        float_layout.add_widget(self.blank_label)


        search_function = addons.search_addons
        self.search_bar = search_input(return_function=search_function, server_info=constants.server_manager.current_server.properties_dict(), pos_hint={"center_x": 0.5, "center_y": 0.795})
        self.page_switcher = PageSwitcher(0, 0, (0.5, 0.805), self.switch_page)


        # Append scroll view items
        scroll_anchor.add_widget(self.scroll_layout)
        scroll_widget.add_widget(scroll_anchor)
        float_layout.add_widget(scroll_widget)
        float_layout.add_widget(scroll_top)
        float_layout.add_widget(scroll_bottom)
        float_layout.add_widget(self.search_bar)
        float_layout.add_widget(self.page_switcher)

        buttons.append(exit_button('Back', (0.5, 0.12), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)

        server_name = constants.server_manager.current_server.name
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



# Server Advanced Settings ---------------------------------------------------------------------------------------------

class EditorLine(RelativeLayout):

    def on_resize(self, *args):
        self.key_label.size_hint_max = self.key_label.texture_size
        self.eq_label.size_hint_max = self.eq_label.texture_size

        self.key_label.x = self.line_number.x + self.line_number.size_hint_max[0] + (self.spacing * 1.4) + 10
        self.eq_label.x = self.key_label.x + self.key_label.size_hint_max[0] + (self.spacing * 1.05)
        self.value_label.x = self.eq_label.x + self.eq_label.size_hint_max[0] + (self.spacing * 0.67)
        self.value_label.y = -6
        self.value_label.search.x = self.value_label.x + 5.3
        self.value_label.search.y = self.value_label.y + (5 if 'italic' in self.value_label.font_name.lower() else 7)

        self.value_label.size_hint_min_x = Window.width - self.value_label.x - 30
        self.value_label.size_hint_max_x = self.value_label.size_hint_min_x

        try:
            self.ghost_cover_left.x = -10
            self.ghost_cover_left.size_hint_max_x = self.value_label.x + 14
            self.ghost_cover_right.x = Window.width - 33
            self.ghost_cover_right.size_hint_max_x = 33
        except AttributeError:
            pass

    def highlight_text(self, text):
        self.last_search = text
        self.key_label.text = self.key_label.original_text
        self.line_matched = False

        # Draws highlight around a match
        def draw_highlight_box(label, *args):
            def get_x(lb, ref_x):
                """ Return the x value of the ref/anchor relative to the canvas """
                return lb.center_x - lb.texture_size[0] * 0.5 + ref_x
            def get_y(lb, ref_y):
                """ Return the y value of the ref/anchor relative to the canvas """
                # Note the inversion of direction, as y values start at the top of
                # the texture and increase downwards
                return lb.center_y + lb.texture_size[1] * 0.5 - ref_y

            # Draw a green surround around the refs. Note the sizes y inversion
            label.canvas.before.clear()
            for name, boxes in label.refs.items():
                for box in boxes:
                    with label.canvas.before:
                        Color(*self.select_color)
                        Rectangle(pos=(get_x(label, box[0]), get_y(label, box[1])), size=(box[2] - box[0], box[1] - box[3]))

        if text.strip():
            text = text.strip()

            if "=" in text:
                key_text, value_text = [x.strip() for x in text.split("=", 1)]
            else:
                key_text = ''
                value_text = ''

            # Check if search matches in key label
            if text in self.key_label.text:
                self.key_label.text = f'[color=#000000][ref=0]{text}[/ref][/color]'.join([x for x in self.key_label.original_text.split(text)])
                self.line_matched = True
            elif key_text and self.key_label.text.endswith(key_text) and self.value_label.original_text.startswith(value_text):
                self.key_label.text = f'[color=#000000][ref=0]{key_text}[/ref][/color]'.join([x for x in self.key_label.original_text.rsplit(key_text, 1)])
                self.line_matched = True
            else:
                self.key_label.text = self.key_label.original_text
                Clock.schedule_once(functools.partial(draw_highlight_box, self.key_label), 0)


            # Check if search matches in value input/ghost label
            if text in self.value_label.text:
                self.value_label.search.text = f'[color=#000000][ref=0]{text}[/ref][/color]'.join([x for x in self.value_label.text.split(text)])
                self.line_matched = True
            elif value_text and self.value_label.text.startswith(value_text) and self.key_label.original_text.endswith(key_text):
                self.value_label.search.text = f'[color=#000000][ref=0]{value_text}[/ref][/color]'.join([x for x in self.value_label.text.split(value_text, 1)])
                self.line_matched = True
            else:
                self.value_label.search.text = self.value_label.text
                Clock.schedule_once(functools.partial(draw_highlight_box, self.value_label.search), 0)

        # Highlight matches
        if self.line_matched and self.animate:
            self.line_number.text = f'[color=#4CFF99]{self.line}[/color]'
            self.line_number.opacity = 1

            Clock.schedule_once(functools.partial(draw_highlight_box, self.value_label.search), 0)
            Clock.schedule_once(functools.partial(draw_highlight_box, self.key_label), 0)
            self.value_label.foreground_color = (0, 0, 0, 0)
            self.value_label.search.opacity = 1

        # Reset labels
        else:
            self.line_number.text = str(self.line)
            self.line_number.opacity = 1 if self.value_label.focused and self.animate else 0.35

            self.value_label.search.opacity = 0
            self.value_label.foreground_color = self.value_label.last_color

            # Reset labels
            Clock.schedule_once(functools.partial(draw_highlight_box, self.value_label.search), 0)
            Clock.schedule_once(functools.partial(draw_highlight_box, self.key_label), 0)
            self.value_label.search.text = self.value_label.text
            self.key_label.text = self.key_label.original_text

        return self.line_matched

    def allow_animation(self, *args):
        self.animate = True

    def __init__(self, line, key, value, max_value, index_func, undo_func, **kwargs):
        super().__init__(**kwargs)

        background_color = constants.brighten_color(constants.background_color, -0.1)

        # Defaults
        self.line = line
        self.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["mono-medium"]}.otf')
        self.font_size = dp(25)
        self.spacing = dp(16)
        self.size_hint_min_y = 35
        self.last_search = ''
        self.line_matched = False
        self.select_color = (0.3, 1, 0.6, 1)
        self.animate = False

        # Create main text input
        class EditorInput(TextInput):

            def grab_focus(self):
                def focus_later(*args):
                    self.focus = True

                Clock.schedule_once(focus_later, 0)

            def on_focus(self, *args):
                Animation.stop_all(self.eq)
                Animation(opacity=(1 if self.focused else 0.5), duration=0.15).start(self.eq)
                try:
                    Animation(opacity=(1 if self.focused or self.parent.line_matched else 0.35), duration=0.15).start(self.line)
                except AttributeError:
                    pass

                if self.focused:
                    self.index_func(self.index)

                    if (len(self.text) * (self.font_size/1.85)) > self.width:
                        self.cursor = (len(self.text), self.cursor[1])
                        Clock.schedule_once(functools.partial(self.do_cursor_movement, 'cursor_end', True), 0)
                        Clock.schedule_once(functools.partial(self.select_text, 0), 0.01)
                else:
                    self.scroll_x = 0

            # Type color and prediction
            def on_text(self, *args):
                Animation.stop_all(self)
                Animation.stop_all(self.search)
                self.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["mono-medium"]}.otf')
                self.font_size = dp(25)
                self.foreground_color = (0.408, 0.889, 1, 1)
                self.cursor_color = (0.358, 0.839, 1, 1)
                self.selection_color = (0.308, 0.789, 1, 0.4)

                # Input validation
                self.text = self.text.replace("\n","").replace("\r","")

                # Boolean type prediction
                if self.text.lower() in ['true', 'false']:
                    self.text = self.text.lower()
                    self.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["mono-italic"]}')
                    self.foreground_color = (1, 0.451, 1, 1)
                    self.cursor_color = (1, 0.401, 1, 1)
                    self.selection_color = (0.955, 0.351, 1, 0.4)
                    self.font_size = dp(23.8)

                # Float type prediction
                elif self.text.replace(".", "").isnumeric():
                    self.foreground_color = (0.989, 0.591, 0.254, 1)
                    self.cursor_color = (0.939, 0.541, 0.254, 1)
                    self.selection_color = (0.889, 0.511, 0.254, 0.4)

                self.last_color = self.foreground_color
                self.original_text = str(self.text)
                self.search.text = str(self.text)
                self.search.color = self.foreground_color
                self.search.font_size = self.font_size
                self.search.font_name = self.font_name
                self.search.text_size = self.search.size
                if self.scroll_x == 0:
                    self.search.x = self.x + 5.3
                self.search.y = self.y + (5 if 'italic' in self.font_name.lower() else 7)

                if self.search.opacity == 1:
                    self.foreground_color = (0, 0, 0, 0)

                def highlight(*args):
                    try:
                        self.parent.highlight_text(self.parent.last_search)
                    except AttributeError:
                        pass
                Clock.schedule_once(highlight, 0)

            # Ignore keypresses when popup exists
            def insert_text(self, substring, from_undo=False):
                if screen_manager.current_screen.popup_widget:
                    return None

                super().insert_text(substring, from_undo)

            # Add in special key presses
            def keyboard_on_key_down(self, window, keycode, text, modifiers):

                # Ignore undo and redo for global effect
                if keycode[1] in ['r', 'z', 'y'] and 'ctrl' in modifiers:
                    return None

                # Undo functionality
                elif (not modifiers and (text or keycode[1] in ['backspace', 'delete'])) or (keycode[1] == 'v' and 'ctrl' in modifiers) or (keycode[1] == 'backspace' and 'ctrl' in modifiers):
                    self.undo_func(save=True)

                # Toggle boolean values with space
                def replace_text(val, *args):
                    self.text = val

                if keycode[1] == "spacebar" and self.text == 'true':
                    Clock.schedule_once(functools.partial(replace_text, 'false'), 0)
                    return
                elif keycode[1] == "spacebar" and self.text == 'false':
                    Clock.schedule_once(functools.partial(replace_text, 'true'), 0)
                    return


                super().keyboard_on_key_down(window, keycode, text, modifiers)

                if keycode[1] == "backspace" and "ctrl" in modifiers:
                    if " " not in self.text:
                        self.text = ""
                    else:
                        self.text = self.text.rsplit(" ", 1)[0]

                # # Fix overscroll
                # if self.cursor_pos[0] > (self.x + self.width) - (self.width * 0.05):
                #     self.scroll_x += self.cursor_pos[0] - ((self.x + self.width) - (self.width * 0.05))

                # Fix overscroll
                if self.cursor_pos[0] < (self.x):
                    self.scroll_x = 0

            def scroll_search(self, *a):
                offset = 12
                if self.cursor_offset() - self.width + offset > 0 and self.scroll_x > 0:
                    offset = self.cursor_offset() - self.width + offset
                else:
                    offset = 0

                self.search.x = (self.x + 5.3) - offset

                def highlight(*args):
                    try:
                        self.parent.highlight_text(self.parent.last_search)
                    except AttributeError:
                        pass
                Clock.schedule_once(highlight, 0)

            def __init__(self, default_value, line, index, index_func, undo_func, **kwargs):
                super().__init__(**kwargs)

                with self.canvas.after:
                    self.search = AlignLabel()
                    self.search.halign = "left"
                    self.search.color = (1, 1, 1, 1)
                    self.search.markup = True
                    self.search.font_name = self.font_name
                    self.search.font_size = self.font_size
                    self.search.text_size = self.search.size
                    self.search.width = 10000
                    self.search.font_kerning = False

                self.bind(scroll_x=self.scroll_search)

                self.font_kerning = False
                self.index = index
                self.index_func = index_func
                self.undo_func = undo_func
                self.text = str(default_value)
                self.original_text = str(default_value)
                self.multiline = False
                self.background_color = (0, 0, 0, 0)
                self.cursor_width = dp(3)
                self.eq = line.eq_label
                self.line = line.line_number
                self.last_color = (0, 0, 0, 0)
                self.valign = 'center'

                self.bind(text=self.on_text)
                self.bind(focused=self.on_focus)
                Clock.schedule_once(self.on_text, 0)

                self.size_hint_max = (None, None)
                self.size_hint_min_y = 40

                def set_scroll(*a):
                    if self.text:
                        self.grab_focus()
                        self.focused = False
                        self.on_focus()
                        def scroll(*b):
                            self.focused = False
                            screen_manager.current_screen.current_line = None
                        Clock.schedule_once(scroll, 0)
                Clock.schedule_once(set_scroll, 0.1)

            # Ignore touch events when popup is present
            def on_touch_down(self, touch):
                popup_widget = screen_manager.current_screen.popup_widget
                if popup_widget:
                    return
                else:
                    return super().on_touch_down(touch)


        # Line number
        self.line_number = AlignLabel()
        self.line_number.text = str(line)
        self.line_number.halign = 'right'
        self.line_number.markup = True
        self.line_number.size_hint_max_x = (self.spacing * len(str(max_value)))
        self.line_number.font_name = self.font_name
        self.line_number.font_size = self.font_size
        self.line_number.opacity = 0.35
        self.line_number.color = (0.7, 0.7, 1, 1)


        # Key label
        self.key_label = Label()
        self.key_label.text = ('# ' + key[1:].strip()) if key.startswith('#') else key
        self.key_label.original_text = ('# ' + key[1:].strip()) if key.startswith('#') else key
        self.key_label.font_name = self.font_name
        self.key_label.font_size = self.font_size
        self.key_label.markup = True
        self.key_label.default_color = "#636363" if key.startswith('#') else "#5E6BFF"
        self.key_label.color = self.key_label.default_color


        # '=' sign
        self.eq_label = Label()
        self.eq_label.text = '='
        self.eq_label.halign = 'left'
        self.eq_label.font_name = self.font_name
        self.eq_label.font_size = self.font_size
        self.eq_label.color = (1, 1, 1, 1)
        self.eq_label.opacity = 0.5


        # Value label
        self.value_label = EditorInput(default_value=value, line=self, index=(line-1), index_func=index_func, undo_func=undo_func)
        if not key.startswith('#'):
            self.add_widget(self.value_label)
            self.ghost_cover_left = Image(color=background_color)
            self.ghost_cover_right = Image(color=background_color)
            self.add_widget(self.ghost_cover_left)
            self.add_widget(self.ghost_cover_right)

        # Add everything after value
        self.add_widget(self.line_number)
        self.add_widget(self.key_label)
        if not key.startswith('#'):
            self.add_widget(self.eq_label)


        Clock.schedule_once(self.key_label.texture_update, -1)
        Clock.schedule_once(self.eq_label.texture_update, -1)

        self.bind(size=self.on_resize, pos=self.on_resize)

        Clock.schedule_once(self.on_resize, 0)
        Clock.schedule_once(self.allow_animation, 1)

class ServerPropertiesEditScreen(MenuBackground):

    # Search bar input at the bottom
    class PropertiesSearchInput(TextInput):

        def _on_focus(self, instance, value, *largs):

            # Update screen focus value on next frame
            def update_focus(*args):
                screen_manager.current_screen._input_focused = self.focus

            Clock.schedule_once(update_focus, 0)

            super(type(self), self)._on_focus(instance, value)
            Animation.stop_all(self.parent.input_background)
            Animation(opacity=0.9 if self.focus else 0.35, duration=0.2, step=0).start(self.parent.input_background)

        def __init__(self, **kwargs):
            super().__init__(**kwargs)

            self.original_text = ''
            self.history_index = 0

            self.multiline = False
            self.halign = "left"
            self.hint_text = "search for text..."
            self.hint_text_color = (0.6, 0.6, 1, 0.4)
            self.foreground_color = (0.6, 0.6, 1, 1)
            self.background_color = (0, 0, 0, 0)
            self.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["mono-bold"]}.otf')
            self.font_size = sp(24)
            self.padding_y = (12, 12)
            self.padding_x = (70, 12)
            self.cursor_color = (0.55, 0.55, 1, 1)
            self.cursor_width = dp(3)
            self.selection_color = (0.5, 0.5, 1, 0.4)

            self.bind(on_text_validate=self.on_enter)

        def grab_focus(self):
            def focus_later(*args):
                self.focus = True

            Clock.schedule_once(focus_later, 0)

        def on_enter(self, value):
            self.grab_focus()

        # Input validation
        def insert_text(self, substring, from_undo=False):
            if screen_manager.current_screen.popup_widget:
                return None

            substring = substring.replace("\n", "").replace("\r", "")
            return super().insert_text(substring, from_undo=from_undo)

        def keyboard_on_key_down(self, window, keycode, text, modifiers):

            # Ignore undo and redo for global effect
            if keycode[1] in ['r', 'z', 'y'] and 'ctrl' in modifiers:
                return None

            super().keyboard_on_key_down(window, keycode, text, modifiers)

            if keycode[1] == "backspace" and "ctrl" in modifiers:
                if " " not in self.text:
                    self.text = ""
                else:
                    self.text = self.text.rsplit(" ", 1)[0]

            # Fix overscroll
            if self.cursor_pos[0] > (self.x + self.width) - (self.width * 0.05):
                self.scroll_x += self.cursor_pos[0] - ((self.x + self.width) - (self.width * 0.05))

            # Fix overscroll
            if self.cursor_pos[0] < (self.x):
                self.scroll_x = 0

        def fix_overscroll(self, *args):

            if self.cursor_pos[0] < (self.x):
                self.scroll_x = 0

        # Ignore touch events when popup is present
        def on_touch_down(self, touch):
            popup_widget = screen_manager.current_screen.popup_widget
            if popup_widget:
                return
            else:
                return super().on_touch_down(touch)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'

        self.header = None
        self.line_list = None
        self.search_bar = None
        self.scroll_widget = None
        self.scroll_layout = None
        self.input_background = None
        self.fullscreen_shadow = None
        self.match_label = None
        self.server_properties = None
        self.controls_button = None

        self.undo_history = []
        self.redo_history = []
        self.last_search = ''
        self.match_list = []
        self.modified = False
        self.current_line = None

        self.background_color = constants.brighten_color(constants.background_color, -0.1)

        # Background
        with self.canvas.before:
            self.color = Color(*self.background_color, mode='rgba')
            self.rect = Rectangle(pos=self.pos, size=self.size)

    # index_func
    def set_index(self, index, **kwargs):
        self.current_line = index

    def focus_input(self, new_input=None, highlight=False):
        if not new_input:
            new_input = self.line_list[self.current_line]

        # Highlight focused input
        if highlight:
            original_color = constants.convert_color(new_input.key_label.default_color)['rgb']
            new_input.key_label.color = constants.brighten_color(original_color, 0.2)
            Animation.stop_all(new_input.key_label)
            Animation(color=original_color, duration=0.5).start(new_input.key_label)

        new_input.value_label.grab_focus()
        self.scroll_widget.scroll_to(new_input.value_label, padding=30, animate=True)

    # Changes input on different keypresses
    def switch_input(self, position):
        if self.current_line is None:
            self.set_index(0)

        index = 0

        # Set initial index
        if position == 'up':
            index = self.current_line - 1

        elif position == 'down':
            index = self.current_line + 1

        elif position in ['pagedown', 'end']:
            position = 'pagedown'
            index = len(self.line_list) - 1

        elif position in ['pageup', 'home']:
            position = 'pageup'
            index = 0


        # Loop over indexes until next match to support rollover
        found_input = False
        while not found_input:
            ignore_input = False

            # Rollover indexes
            if index >= len(self.line_list):
                index = 0
            elif index <= 0 and 'page' not in position:
                index = len(self.line_list) - 1

            new_input = self.line_list[index]


            # Ignore result if not a search match
            if self.match_list and self.last_search:
                if not new_input.line_matched:
                    ignore_input = True


            if not new_input.key_label.text.startswith("#") and not ignore_input:

                try:
                    self.focus_input(new_input)
                    break

                except AttributeError:
                    pass

            index = index + (-1 if position == 'up' else 1)

    def search_text(self, obj, text, *args):
        self.last_search = text
        self.match_list = []
        first_match = None

        for line in self.line_list:
            result = line.highlight_text(text)
            if result:
                self.match_list.append(line)

            if result and not first_match:
                first_match = line

        if first_match:
            self.set_index(first_match.line-1)
            self.scroll_widget.scroll_to(first_match, padding=30, animate=True)

        # Handle match text
        try:
            Animation.stop_all(self.match_label)
            Animation(opacity=(1 if text and self.match_list else 0.35 if text else 0), duration=0.1).start(self.match_label)
            if "=" in text:
                new_text = '='.join([x.strip() for x in text.split("=", 1)]).strip()
            else:
                new_text = text.strip()
            matches = sum([f'{x.key_label.text}={x.value_label.text}'.count(new_text) for x in self.match_list])
            self.match_label.text = f'{matches} match{"" if matches == 1 else "es"}'
        except AttributeError:
            pass

    # Saves info to self.undo/redo_history, and handles changing values
    def undo(self, save=False, undo=False):
        if save:
            self.redo_history = []
            line = self.line_list[self.current_line]
            same_line = False

            if self.undo_history:
                if self.undo_history[-1][0] == line.line:
                    same_line = True

            if not same_line:
                self.undo_history.append((line.line, line.value_label.original_text))

        else:
            if undo:
                line = self.undo_history[-1]
                line_obj = self.line_list[line[0]-1]
                self.redo_history.append([line[0], line_obj.value_label.original_text])
                line_obj.value_label.text = line[1]
                self.undo_history.pop(-1)

            else:
                line = self.redo_history[-1]
                line_obj = self.line_list[line[0]-1]
                self.undo_history.append([line[0], line_obj.value_label.original_text])
                line_obj.value_label.text = line[1]
                self.redo_history.pop(-1)
            self.focus_input(line_obj, highlight=True)

        # print(self.undo_history, self.redo_history)

    def generate_menu(self, **kwargs):
        server_obj = constants.server_manager.current_server
        server_obj.reload_config()

        # Reset values
        self.match_label = None
        self.undo_history = []
        self.redo_history = []
        self.last_search = ''
        self.match_list = []
        self.modified = False

        with open(constants.server_path(server_obj.name, 'server.properties'), 'r') as f:
            self.server_properties = f.read().strip().splitlines()


        # Scroll list
        self.scroll_widget = ScrollViewWidget(position=(0.5, 0.5))
        self.scroll_layout = GridLayout(cols=1, size_hint_max_x=1250, size_hint_y=None, padding=[10, 30, 0, 30])


        # Bind / cleanup height on resize
        def resize_scroll(call_widget, grid_layout, *args):
            call_widget.height = Window.height // 1.23

            self.fullscreen_shadow.y = self.height + self.x - 3
            self.fullscreen_shadow.width = Window.width

            search_pos = 47

            self.search_bar.pos = (self.x, search_pos)
            self.input_background.pos = (self.search_bar.pos[0] - 15, self.search_bar.pos[1] + 8)

            self.search_bar.size_hint_max_x = Window.width - self.search_bar.x - 200



        self.resize_bind = lambda*_: Clock.schedule_once(functools.partial(resize_scroll, self.scroll_widget, self.scroll_layout), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        self.scroll_layout.bind(minimum_height=self.scroll_layout.setter('height'))
        self.scroll_layout.id = 'scroll_content'


        # Scroll gradient
        scroll_top = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.9}, pos=self.scroll_widget.pos, size=(self.scroll_widget.width // 1.5, 60))
        scroll_top.color = self.background_color
        scroll_bottom = scroll_background(pos_hint={"center_x": 0.5}, pos=self.scroll_widget.pos, size=(self.scroll_widget.width // 1.5, -60))
        scroll_bottom.color = self.background_color
        scroll_bottom.y = 115


        # Generate buttons on page load
        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'


        # Generate editor content
        props = server_obj.server_properties
        self.current_line = None
        self.undo_history = []
        self.redo_history = []
        self.line_list = []
        for x, pair in enumerate(props.items(), 1):
            line = EditorLine(line=x, key=pair[0], value=pair[1], max_value=len(props), index_func=self.set_index, undo_func=self.undo)
            self.line_list.append(line)
            self.scroll_layout.add_widget(line)


        # Append scroll view items
        self.scroll_widget.add_widget(self.scroll_layout)
        float_layout.add_widget(self.scroll_widget)
        float_layout.add_widget(scroll_top)
        float_layout.add_widget(scroll_bottom)


        # # Configure header
        # header_content = "Editing 'server.properties'"
        # self.header = HeaderText(header_content, '', (0, 0.89))
        # float_layout.add_widget(self.header)


        # Fullscreen shadow
        self.fullscreen_shadow = Image()
        self.fullscreen_shadow.allow_stretch = True
        self.fullscreen_shadow.keep_ratio = False
        self.fullscreen_shadow.size_hint_max = (None, 50)
        self.fullscreen_shadow.color = (0, 0, 0, 1)
        self.fullscreen_shadow.opacity = 0
        self.fullscreen_shadow.source = os.path.join(constants.gui_assets, 'control_fullscreen_gradient.png')
        float_layout.add_widget(self.fullscreen_shadow)


        buttons.append(exit_button('Back', (0.5, -1), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)

        float_layout.add_widget(generate_title(f"Advanced Settings: '{server_obj.name}'"))
        float_layout.add_widget(generate_footer(f"{server_obj.name}, Advanced, Edit 'server.properties'"))

        self.add_widget(float_layout)


        # Add search bar
        self.search_bar = self.PropertiesSearchInput(size_hint_max_y=50)
        self.search_bar.bind(text=self.search_text)
        self.add_widget(self.search_bar)

        # Match label
        self.match_label = AlignLabel()
        self.match_label.text = '0 matches'
        self.match_label.halign = "right"
        self.match_label.color = (0.6, 0.6, 1, 1)
        self.match_label.font_name = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["mono-bold"]}.otf')
        self.match_label.font_size = sp(24)
        self.match_label.y = 60
        self.match_label.padding_x = 10
        self.match_label.opacity = 0
        self.add_widget(self.match_label)


        # Input icon
        self.input_background = Image()
        self.input_background.default_opacity = 0.35
        self.input_background.color = self.search_bar.foreground_color
        self.input_background.opacity = self.input_background.default_opacity
        self.input_background.allow_stretch = True
        self.input_background.size_hint = (None, None)
        self.input_background.height = self.search_bar.size_hint_max_y / 1.45
        self.input_background.source = os.path.join(constants.gui_assets, 'icons', 'search.png')
        self.add_widget(self.input_background)

        # Controls button
        def show_controls():

            controls_text = """This menu allows you to edit additional configuration options provided by the 'server.properties' file. Refer to the Minecraft Wiki for more information. Shortcuts are provided for ease of use:


• Press 'CTRL+Z' to undo, and 'CTRL+R'/'CTRL+Y' to redo

• Press 'CTRL+S' to save modifications

• Press 'CTRL-Q' to quit the editor

• Press 'CTRL+F' to search for data

• Press 'SPACE' to toggle boolean values (e.g. true, false)"""

            Clock.schedule_once(
                functools.partial(
                    self.show_popup,
                    "controls",
                    "Controls",
                    controls_text,
                    (None)
                ),
                0
            )

        self.controls_button = IconButton('controls', {}, (70, 110), (None, None), 'question.png', clickable=True, anchor='right', click_func=show_controls)
        float_layout.add_widget(self.controls_button)


        # Header
        self.header = BannerObject(
            pos_hint = {"center_x": (0.5), "center_y": 0.9},
            size = (250, 40),
            color = (0.4, 0.682, 1, 1),
            text = "Viewing 'server.properties'",
            icon = "eye-outline.png"
        )
        self.add_widget(self.header)


    # Writes config to server.properties file, and reloads it in the server manager if the server is not running
    def save_config(self):
        server_obj = constants.server_manager.current_server
        final_config = {}

        for line in self.line_list:
            key = line.key_label.original_text
            value = line.value_label.text

            if not (key or value):
                continue

            if key.startswith("# "):
                final_config["#" + key[1:].strip()] = ''
            else:
                final_config[key] = value.strip()

        constants.server_properties(server_obj.name, write_object=final_config)
        server_obj.reload_config()

        # Reload config
        with open(constants.server_path(server_obj.name, 'server.properties'), 'r') as f:
            self.server_properties = f.read().strip().splitlines()

        self.set_banner_status(False)

        # Show banner if server is running
        if server_obj.running:
            Clock.schedule_once(
                functools.partial(
                    screen_manager.current_screen.show_banner,
                    (0.937, 0.831, 0.62, 1),
                    f"A server restart is required to apply changes",
                    "sync.png",
                    3,
                    {"center_x": 0.5, "center_y": 0.965}
                ), 0.25
            )

        else:
            Clock.schedule_once(
                functools.partial(
                    screen_manager.current_screen.show_banner,
                    (0.553, 0.902, 0.675, 1),
                    "'server.properties' was saved successfully",
                    "checkmark-circle-sharp.png",
                    2.5,
                    {"center_x": 0.5, "center_y": 0.965}
                ), 0
            )

    # Reset results of all cells
    def reset_data(self):
        server_obj = constants.server_manager.current_server
        props = server_obj.server_properties
        self.undo_history = []

        for x, pair in enumerate(props.items(), 0):
            line = self.line_list[x]
            key, value = pair
            if key.startswith("#"):
                key = key.replace("#", "# ", 1)
                line.key_label.text = key.strip()
            else:
                line.key_label.text = key.strip()
                if isinstance(value, bool):
                    value = str(value).lower().strip()

                if line.value_label.text != str(value):
                    self.redo_history.append((x+1, line.value_label.text))

                line.value_label.text = str(value)

        self.set_banner_status(False)

    # Checks if data in editor matches saved file
    def check_data(self):

        for line in self.line_list:
            key = line.key_label.original_text
            value = line.value_label.text

            if not (key or value):
                continue

            if key.startswith("# "):
                line = "#" + key[1:].strip()
            else:
                line = f"{key}={value}"

            if line not in self.server_properties:
                return False

        return True

    def set_banner_status(self, changed=False):

        if changed != self.modified:
            # Change header
            self.remove_widget(self.header)
            del self.header

            if changed:
                self.header = BannerObject(
                    pos_hint = {"center_x": (0.5), "center_y": 0.9},
                    size = (250, 40),
                    color = "#F3ED61",
                    text = "Editing 'server.properties'",
                    icon = "pencil-sharp.png",
                    animate = True
                )
                self.add_widget(self.header)
            else:
                self.header = BannerObject(
                    pos_hint = {"center_x": (0.5), "center_y": 0.9},
                    size = (250, 40),
                    color = (0.4, 0.682, 1, 1),
                    text = "Viewing 'server.properties'",
                    icon = "eye-outline.png",
                    animate = True
                )
                self.add_widget(self.header)

        self.modified = changed

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        # print('The key', keycode, 'have been pressed')
        # print(' - text is %r' % text)
        # print(' - modifiers are %r' % modifiers)

        # Ignore key presses when popup is visible
        if self.popup_widget:
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
            return False

        def quit_to_menu(*a):
            for button in self.walk():
                try:
                    if button.id == "exit_button":
                        button.force_click()
                        break
                except AttributeError:
                    continue
            keyboard.release()

        def save_and_quit(*a):
            self.save_config()
            quit_to_menu()

        def return_to_input():
            if self.current_line is not None:
                self.focus_input()

        # Keycode is composed of an integer + a string
        # If we hit escape, release the keyboard
        # On ESC, click on back button if it exists
        if not self._input_focused:
            # if keycode[1] == 'escape' and 'escape' not in self._ignore_keys:
            #     quit_to_menu()
            pass


        if keycode[1] == 'h' and 'ctrl' in modifiers and not self.popup_widget:
            self.controls_button.button.trigger_action()


        # Exiting search bar
        elif keycode[1] == 'escape' and 'escape' not in self._ignore_keys:
            return_to_input()


        # Quit and prompt to save if file was changed
        if keycode[1] == 'q' and 'ctrl' in modifiers:
            if self.modified:
                self.show_popup(
                    "query",
                    "Unsaved Changes",
                    'There are unsaved changes in your configuration.\n\nWould you like to save the file before quitting?',
                    [functools.partial(Clock.schedule_once, quit_to_menu, 0.25), functools.partial(Clock.schedule_once, save_and_quit, 0.25)]
                )
            else:
                quit_to_menu()


        # Focus text input if server is started
        if (keycode[1] in ['down', 'up', 'pagedown', 'pageup']):
            self.switch_input(keycode[1])


        # Ctrl-F to search
        if keycode[1] == 'f' and 'ctrl' in modifiers:
            if not self.search_bar.focused:
                self.search_bar.grab_focus()
            else:
                return_to_input()


        # Save config file
        if keycode[1] == 's' and 'ctrl' in modifiers and self.modified:
            self.save_config()


        # Undo / Redo functionality
        if keycode[1] == 'z' and 'ctrl' in modifiers and self.undo_history:
            self.undo(save=False, undo=True)

        elif keycode[1] == 'z' and 'ctrl' in modifiers and not self.undo_history:
            if not self.check_data():
                self.reset_data()

        if keycode[1] in ['r', 'y'] and 'ctrl' in modifiers and self.redo_history:
            self.undo(save=False, undo=False)


        # Check if data is updated on keypress
        def set_banner(*a):
            self.set_banner_status(not self.check_data())
        Clock.schedule_once(set_banner, 0)


        # Return True to accept the key. Otherwise, it will be used by the system.
        return True

def toggle_ngrok(boolean, *args):
    server_obj = constants.server_manager.current_server

    if boolean:
        # Switch to screen to authenticate ngrok if toggled and authtoken is missing
        if not constants.check_ngrok_creds():
            screen_manager.current = "NgrokAuthScreen"
            return

    # Show banner if server is running
    if server_obj.running:
        Clock.schedule_once(
            functools.partial(
                screen_manager.current_screen.show_banner,
                (0.937, 0.831, 0.62, 1),
                f"A server restart is required to apply changes",
                "sync.png",
                3,
                {"center_x": 0.5, "center_y": 0.965}
            ), 0.25
        )

    else:
        Clock.schedule_once(
            functools.partial(
                screen_manager.current_screen.show_banner,
                (0.553, 0.902, 0.675, 1) if boolean else (0.937, 0.831, 0.62, 1),
                f"ngrok proxy is {'en' if boolean else 'dis'}abled",
                "checkmark-circle-outline.png" if boolean else "close-circle-outline.png",
                2.5,
                {"center_x": 0.5, "center_y": 0.965}
            ), 0
        )

    server_obj.config_file.set("general", "enableNgrok", str(boolean).lower())
    constants.server_config(server_obj.name, server_obj.config_file)
    server_obj.ngrok_enabled = boolean

class NgrokAuthScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.authtoken_input = None
        self.menu = 'init'

    def generate_menu(self, **kwargs):

        # Generate buttons on page load
        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'

        def open_ngrok_site(*a):
            url = 'https://dashboard.ngrok.com/get-started/your-authtoken'
            webbrowser.open_new_tab(url)

        def authorize_ngrok(*a):
            constants.run_proc(f'"{os.path.join(constants.applicationFolder, "Tools", constants.ngrok_exec)}" config add-authtoken {self.authtoken_input.text}')
            if constants.check_ngrok_creds():
                toggle_ngrok(True)
            previous_screen()
            constants.screen_tree.pop(-1)



        float_layout.add_widget(HeaderText("Login to ngrok and paste your authtoken below", '', (0, 0.8)))
        float_layout.add_widget(WaitButton('Login to ngrok', (0.5, 0.555), 'ngrok.png', width=531, click_func=open_ngrok_site))
        self.authtoken_input = NgrokAuthInput(pos_hint={"center_x": 0.5, "center_y": 0.45})
        float_layout.add_widget(self.authtoken_input)
        buttons.append(next_button('Next', (0.5, 0.24), True, next_screen='ServerAdvancedScreen', click_func=authorize_ngrok))
        buttons.append(exit_button('Back', (0.5, 0.14), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)

        menu_name = f"Login to ngrok"
        float_layout.add_widget(generate_title(menu_name))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)

class ServerAdvancedScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'

        self.header = None
        self.menu_taskbar = None

        self.edit_properties_button = None
        self.open_path_button = None
        self.ngrok_button = None

    def generate_menu(self, **kwargs):
        server_obj = constants.server_manager.current_server
        server_obj.reload_config()
        constants.check_ngrok()

        # Scroll list
        scroll_widget = ScrollViewWidget()
        scroll_anchor = AnchorLayout()
        scroll_layout = GridLayout(cols=1, spacing=10, size_hint_max_x=1175, size_hint_y=None, padding=[0, -50, 0, 60])


        # Bind / cleanup height on resize
        def resize_scroll(call_widget, grid_layout, anchor_layout, *args):
            call_widget.height = Window.height // 1.5
            call_widget.pos_hint = {"center_y": 0.5}
            grid_layout.cols = 2 if Window.width > grid_layout.size_hint_max_x else 1

            def update_grid(*args):
                anchor_layout.size_hint_min_y = grid_layout.height

            Clock.schedule_once(update_grid, 0)


        self.resize_bind = lambda*_: Clock.schedule_once(functools.partial(resize_scroll, scroll_widget, scroll_layout, scroll_anchor), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        scroll_layout.bind(minimum_height=scroll_layout.setter('height'))
        scroll_layout.id = 'scroll_content'

        # Scroll gradient
        scroll_top = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.84}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, 60))
        scroll_bottom = scroll_background(pos_hint={"center_x": 0.5, "center_y": 0.17}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, -60))

        # Generate buttons on page load
        buttons = []
        float_layout = FloatLayout()
        float_layout.id = 'content'

        pgh_font = os.path.join(constants.gui_assets, 'fonts', f'{constants.fonts["mono-medium"]}.otf')

        # Create and add paragraphs to GridLayout
        def create_paragraph(name, layout, cid):

            # Dirty fix to anchor paragraphs to the top
            def repos(p, s, *args):
                if scroll_layout.cols == 2:
                    if s.height != scroll_layout._rows[cid]:
                        p.y = scroll_layout._rows[cid] - s.height

                    if cid == 0:
                        for child in scroll_layout.children:
                            if child != s and child.x == s.x:
                                p2 = child.children[0]
                                p2.y = p.y
                                break
                else:
                    p.y = 0

            sub_layout = ScrollItem()
            content_size = sp(22)
            content_height = sum([(child.height + (layout.spacing[0]*2)) for child in layout.children])
            paragraph = paragraph_object(size=(530, content_height), name=name, content=' ', font_size=content_size, font=pgh_font)
            sub_layout.height = paragraph.height + 80

            sub_layout.bind(pos=functools.partial(repos, paragraph, sub_layout, cid))
            sub_layout.bind(size=functools.partial(repos, paragraph, sub_layout, cid))

            sub_layout.add_widget(paragraph)
            sub_layout.add_widget(layout)
            layout.pos_hint = {'center_x': 0.5, 'center_y': 0.555}
            scroll_layout.add_widget(sub_layout)


        # ----------------------------------------------- General ------------------------------------------------------

        general_layout = GridLayout(cols=1, spacing=10, size_hint_max_x=1050, size_hint_y=None, padding=[0, 0, 0, 0])

        # Edit properties button
        def edit_server_properties(*args):
            screen_manager.current = 'ServerPropertiesEditScreen'

        sub_layout = ScrollItem()
        self.edit_properties_button = WaitButton("Edit 'server.properties'", (0.5, 0.5), 'document-text-outline.png', click_func=edit_server_properties)
        sub_layout.add_widget(self.edit_properties_button)
        general_layout.add_widget(sub_layout)


        # RAM allocation slider (Max limit = 75% of memory capacity)
        max_limit = constants.max_memory
        min_limit = 0
        start_value = min_limit if str(server_obj.dedicated_ram) == 'auto' else int(server_obj.dedicated_ram)

        def change_limit(val):
            server_obj.set_ram_limit('auto' if val == min_limit else val)

        sub_layout = ScrollItem()
        sub_layout.add_widget(blank_input(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="allocated memory"))
        sub_layout.add_widget(NumberSlider(start_value, (0.5, 0.5), input_name='RamInput', limits=(min_limit, max_limit), min_icon='auto-icon.png', function=change_limit))
        general_layout.add_widget(sub_layout)


        # Open server directory
        def open_server_dir(*args):
            constants.open_folder(server_obj.server_path)
            Clock.schedule_once(self.open_path_button.button.on_leave, 0.5)

        sub_layout = ScrollItem()
        self.open_path_button = WaitButton('Open Server Directory', (0.5, 0.5), 'folder-outline.png', click_func=open_server_dir)
        sub_layout.add_widget(self.open_path_button)
        general_layout.add_widget(sub_layout)

        create_paragraph('general', general_layout, 0)

        # --------------------------------------------------------------------------------------------------------------



        # ----------------------------------------------- Network ------------------------------------------------------

        network_layout = GridLayout(cols=1, spacing=10, size_hint_max_x=1050, size_hint_y=None, padding=[0, 0, 0, 0])

        # Edit IP/Port input
        sub_layout = ScrollItem()
        sub_layout.add_widget(InputLabel(pos_hint={"center_x": 0.5, "center_y": 1.2}))
        port_input = ServerPortInput(pos_hint={'center_x': 0.5, 'center_y': 0.5}, text=process_ip_text(server_obj=server_obj))
        port_input.size_hint_max_x = 435
        sub_layout.add_widget(port_input)
        network_layout.add_widget(sub_layout)

        def add_switch(index=0, fade=False, *a):
            sub_layout = ScrollItem()
            state = server_obj.ngrok_enabled
            input_border = blank_input(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text='enable proxy (ngrok)', disabled=(not constants.app_online))
            sub_layout.add_widget(input_border)
            sub_layout.add_widget(toggle_button('ngrok', (0.5, 0.5), custom_func=toggle_ngrok, default_state=server_obj.ngrok_enabled, disabled=(not constants.app_online)))
            network_layout.add_widget(sub_layout, index)
            if fade:
                input_border.opacity = 0
                Animation(opacity=1, duration=0.5).start(input_border)

        if not constants.ngrok_installed:
            def prompt_install(*args):
                def install_wrapper(*a):
                    Clock.schedule_once(functools.partial(self.ngrok_button.loading, True), 0)
                    boolean = constants.install_ngrok()

                    def add_widgets(*b):
                        self.ngrok_button.loading(False)
                        network_layout.remove_widget(self.ngrok_button.parent)
                        add_switch(1, True)
                        Clock.schedule_once(
                            functools.partial(
                                screen_manager.current_screen.show_banner,
                                (0.553, 0.902, 0.675, 1) if boolean else (0.937, 0.831, 0.62, 1),
                                f"ngrok was {'installed successfully' if boolean else 'not installed'}",
                                "checkmark-circle-outline.png" if boolean else "close-circle-outline.png",
                                2.5,
                                {"center_x": 0.5, "center_y": 0.965}
                            ), 0
                        )
                    Clock.schedule_once(add_widgets, 0)

                if constants.app_online:
                    Clock.schedule_once(
                        functools.partial(
                            self.show_popup,
                            "query",
                            "Install ngrok",
                            "ngrok is a free proxy service that creates a tunnel to the internet. It can be used to bypass ISP port blocking or conflicts in which the client refuses to connect (e.g. strict NAT).\n\nWould you like to install ngrok?",
                            (None, threading.Timer(0, install_wrapper).start)
                        ),
                        0
                    )
                else:
                    self.show_popup('warning', 'Error', 'An internet connection is required to install ngrok\n\nPlease check your connection and try again', (None))

            sub_layout = ScrollItem()
            self.ngrok_button = WaitButton('Install Ngrok', (0.5, 0.5), 'ngrok.png', click_func=prompt_install)
            sub_layout.add_widget(self.ngrok_button)
            network_layout.add_widget(sub_layout)
        else:
            add_switch()


        # Enable Geyser toggle switch
        def toggle_geyser(boolean, install=True):
            if install:
                addon_manager = server_obj.addon
                if boolean:
                    with ThreadPoolExecutor(max_workers=3) as pool:
                        pool.map(addon_manager.download_addon, addons.geyser_addons(server_obj.properties_dict()))
                else:
                    for a in [a for a in addon_manager.return_single_list() if (a.author == 'GeyserMC' and (a.name.startswith('Geyser') or a.name == 'floodgate'))]:
                        addon_manager.delete_addon(a)

                # Show banner if server is running
                if addon_manager.hash_changed():
                    Clock.schedule_once(
                        functools.partial(
                            screen_manager.current_screen.show_banner,
                            (0.937, 0.831, 0.62, 1),
                            f"A server restart is required to apply changes",
                            "sync.png",
                            3,
                            {"center_x": 0.5, "center_y": 0.965}
                        ), 0.25
                    )

                else:
                    Clock.schedule_once(
                        functools.partial(
                            screen_manager.current_screen.show_banner,
                            (0.553, 0.902, 0.675, 1) if boolean else (0.937, 0.831, 0.62, 1),
                            f"Bedrock support {'en' if boolean else 'dis'}abled",
                            "checkmark-circle-outline.png" if boolean else "close-circle-outline.png",
                            2.5,
                            {"center_x": 0.5, "center_y": 0.965}
                        ), 0
                    )

            server_obj.config_file.set("general", "enableGeyser", str(boolean).lower())
            constants.server_config(server_obj.name, server_obj.config_file)

        # Geyser switch for bedrock support
        sub_layout = ScrollItem()
        disabled = not (constants.version_check(server_obj.version, ">=", "1.13.2") and server_obj.type.lower() in ['spigot', 'paper', 'fabric'])
        hint_text = "bedrock (unsupported server)" if disabled else "bedrock support (geyser)"
        if not constants.app_online:
            disabled = True
        sub_layout.add_widget(blank_input(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text=hint_text, disabled=disabled))
        sub_layout.add_widget(toggle_button('geyser', (0.5, 0.5), custom_func=toggle_geyser, disabled=disabled, default_state=(server_obj.geyser_enabled) and not disabled))
        network_layout.add_widget(sub_layout)


        create_paragraph('network', network_layout, 1)

        # --------------------------------------------------------------------------------------------------------------



        # ------------------------------------------------ Updates -----------------------------------------------------

        update_layout = GridLayout(cols=1, spacing=10, size_hint_max_x=1050, size_hint_y=None, padding=[0, 0, 0, 0])

        # Edit properties button
        def edit_server_properties(*args):
            screen_manager.current = 'ServerPropertiesEditScreen'

        sub_layout = ScrollItem()
        self.edit_properties_button = WaitButton("Edit 'server.properties'", (0.5, 0.5), 'document-text-outline.png', click_func=edit_server_properties)
        sub_layout.add_widget(self.edit_properties_button)
        update_layout.add_widget(sub_layout)


        # RAM allocation slider (Max limit = 75% of memory capacity)
        max_limit = constants.max_memory
        min_limit = 0
        start_value = min_limit if str(server_obj.dedicated_ram) == 'auto' else int(server_obj.dedicated_ram)

        def change_limit(val):
            server_obj.set_ram_limit('auto' if val == min_limit else val)

        sub_layout = ScrollItem()
        sub_layout.add_widget(blank_input(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="allocated memory"))
        sub_layout.add_widget(NumberSlider(start_value, (0.5, 0.5), input_name='RamInput', limits=(min_limit, max_limit), min_icon='auto-icon.png', function=change_limit))
        update_layout.add_widget(sub_layout)


        # Open server directory
        def open_server_dir(*args):
            constants.open_folder(server_obj.server_path)
            Clock.schedule_once(self.open_path_button.button.on_leave, 0.5)

        sub_layout = ScrollItem()
        self.open_path_button = WaitButton('Open Server Directory', (0.5, 0.5), 'folder-outline.png', click_func=open_server_dir)
        sub_layout.add_widget(self.open_path_button)
        update_layout.add_widget(sub_layout)

        create_paragraph('updates', update_layout, 0)

        # --------------------------------------------------------------------------------------------------------------



        # ----------------------------------------------- Transilience -------------------------------------------------

        transilience_layout = GridLayout(cols=1, spacing=10, size_hint_max_x=1050, size_hint_y=None, padding=[0, 0, 0, 0])

        # Edit properties button
        def edit_server_properties(*args):
            screen_manager.current = 'ServerPropertiesEditScreen'

        sub_layout = ScrollItem()
        self.edit_properties_button = WaitButton("Edit 'server.properties'", (0.5, 0.5), 'document-text-outline.png', click_func=edit_server_properties)
        sub_layout.add_widget(self.edit_properties_button)
        transilience_layout.add_widget(sub_layout)


        # RAM allocation slider (Max limit = 75% of memory capacity)
        max_limit = constants.max_memory
        min_limit = 0
        start_value = min_limit if str(server_obj.dedicated_ram) == 'auto' else int(server_obj.dedicated_ram)

        def change_limit(val):
            server_obj.set_ram_limit('auto' if val == min_limit else val)

        sub_layout = ScrollItem()
        sub_layout.add_widget(blank_input(pos_hint={"center_x": 0.5, "center_y": 0.5}, hint_text="allocated memory"))
        sub_layout.add_widget(NumberSlider(start_value, (0.5, 0.5), input_name='RamInput', limits=(min_limit, max_limit), min_icon='auto-icon.png', function=change_limit))
        transilience_layout.add_widget(sub_layout)


        # Open server directory
        def open_server_dir(*args):
            constants.open_folder(server_obj.server_path)
            Clock.schedule_once(self.open_path_button.button.on_leave, 0.5)

        sub_layout = ScrollItem()
        self.open_path_button = WaitButton('Open Server Directory', (0.5, 0.5), 'folder-outline.png', click_func=open_server_dir)
        sub_layout.add_widget(self.open_path_button)
        transilience_layout.add_widget(sub_layout)

        create_paragraph('transilience', transilience_layout, 0)

        # --------------------------------------------------------------------------------------------------------------



        # Append scroll view items
        scroll_anchor.add_widget(scroll_layout)
        scroll_widget.add_widget(scroll_anchor)
        float_layout.add_widget(scroll_widget)
        float_layout.add_widget(scroll_top)
        float_layout.add_widget(scroll_bottom)


        # Server Preview Box
        # float_layout.add_widget(server_demo_input(pos_hint={"center_x": 0.5, "center_y": 0.81}, properties=constants.new_server_info))

        # Configure header
        header_content = "Modify advanced server configuration"
        self.header = HeaderText(header_content, '', (0, 0.89))
        float_layout.add_widget(self.header)

        # if server_obj.advanced_hash_changed():
        #     icons = os.path.join(constants.gui_assets, 'fonts', constants.fonts['icons'])
        #     header_content = f"[color=#EFD49E][font={icons}]y[/font] " + header_content + "[/color]"


        buttons.append(exit_button('Back', (0.5, -1), cycle=True))

        for button in buttons:
            float_layout.add_widget(button)

        float_layout.add_widget(generate_title(f"Advanced Settings: '{server_obj.name}'"))
        float_layout.add_widget(generate_footer(f"{server_obj.name}, Advanced", color='EFD49E'))

        self.add_widget(float_layout)

        # Add ManuTaskbar
        self.menu_taskbar = MenuTaskbar(selected_item='advanced')
        self.add_widget(self.menu_taskbar)



# </editor-fold> ///////////////////////////////////////////////////////////////////////////////////////////////////////




# ======================================================================================================================
screen_manager = ScreenManager()
# ======================================================================================================================


# .kv file
kv_file = '''
'''


# Run application and startup preferences
class MainApp(App):

    # Disable F1 menu when compiled
    if constants.app_compiled and constants.debug is False:
        def open_settings(self, *largs):
            pass

    # Window size
    size = (850, 850)

    # Get pos and knowing the old size calculate the new one
    top = dp((Window.top * Window.size[1] / size[1])) - dp(50)
    left = dp(Window.left * Window.size[0] / size[0])

    Window.size = (dp(size[0]), dp(size[1]))
    Window.top = top
    Window.left = left
    Window.on_request_close = functools.partial(sys.exit)

    Window.minimum_width, Window.minimum_height = Window.size
    Window.clearcolor = constants.background_color
    Builder.load_string(kv_file)

    # Prevent window from closing during certain situations
    def exit_check(*args):
        if constants.ignore_close:
            return True
        else:
            # Put function here to prompt user when a server is running, backing up, or updating
            return False

    Window.bind(on_request_close=exit_check)


    def build(self):
        self.icon = os.path.join(constants.gui_assets, "big-icon.png")
        Loader.loading_pickaxe = os.path.join(constants.gui_assets, 'animations', 'loading_pickaxe.gif')

        # Dynamically add every class with the name '*Screen' to ScreenManager
        screen_list = [x[0] for x in inspect.getmembers(sys.modules[__name__], inspect.isclass) if x[0].endswith('Screen') and x[0] != 'Screen']
        # print(screen_list)
        for screen in screen_list:
            screen_manager.add_widget(globals()[screen]())

        constants.app_loaded = True
        screen_manager.transition = NoTransition()
        screen_manager.current = constants.startup_screen

        # Screen manager override
        if not constants.app_compiled:
            pass
            # constants.safe_delete(constants.server_path("test 1.6"))
            # constants.new_server_init()
            # constants.new_server_info['name'] = "test 1.6"
            # constants.new_server_info['type'] = "forge"
            # constants.new_server_info['version'] = "1.6.4"
            # constants.new_server_info['build'] = "283"
            # constants.new_server_info['server_settings']['seed'] = "loll"
            # constants.new_server_info['acl_object'] = acl.AclObject(constants.new_server_info['name'])
            # # constants.new_server_info['server_settings']['world'] = r"C:\Users\macarooni machine\AppData\Roaming\.minecraft\saves\Mob Apocalypse"
            # constants.new_server_info['server_settings']['geyser_support'] = True
            # constants.new_server_info['addon_objects'] = [item for item in [addons.get_addon_url(addons.get_addon_info(addon, constants.new_server_info), constants.new_server_info, compat_mode=True) for addon in addons.search_addons("worldedit", constants.new_server_info) if "Regions"] if item]
            # # constants.new_server_info['addon_objects'].extend([addons.get_addon_file(addon, constants.new_server_info) for addon in glob(r'C:\Users\macarooni machine\AppData\Roaming\.auto-mcs\Servers\pluginupdate test\plugins\*.jar')])
            # screen_manager.current = "CreateServerReviewScreen"

            screen_manager.current = "ServerManagerScreen"
            open_server("test 1.8.9")
            def open_menu(*args):
                screen_manager.current = "ServerAdvancedScreen"
                # Clock.schedule_once(screen_manager.current_screen.edit_properties_button.button.trigger_action, 0.5)
            Clock.schedule_once(open_menu, 3)


        screen_manager.transition = FadeTransition(duration=0.115)

        # Close splash screen if compiled
        if constants.app_compiled:
            import pyi_splash
            pyi_splash.close()

        Window.show()
        return screen_manager


def run_application():
    main_app = MainApp(title=constants.app_title)
    try:
        main_app.run()
    except ArgumentError:
        pass

if constants.app_compiled and constants.debug is True:
    sys.stderr = open("error.log", "a")
