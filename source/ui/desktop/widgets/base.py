from kivy.clock import Clock
from kivy.cache import Cache
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.animation import Animation
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.recycleview import RecycleView
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.relativelayout import RelativeLayout
from kivy.input.providers.mouse import MouseMotionEvent
from kivy.uix.recyclegridlayout import RecycleGridLayout
from kivy.graphics import Color, Rectangle, Ellipse, Line, RoundedRectangle, InstructionGroup


import kivy
kivy.require('2.0.0')
from kivy.app import App
from kivy.metrics import sp, dp
from kivy.uix.slider import Slider
from kivy.core.window import Window
from kivy.uix.dropdown import DropDown
from kivy.core.clipboard import Clipboard
from kivy.uix.image import Image, AsyncImage
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import BooleanProperty, ObjectProperty, ListProperty


from source.ui.desktop.utility import *
from source.ui.desktop import utility



# Widget hover detection and custom event registration
class HoverBehavior():
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
        self.id = ''

    def on_mouse_pos(self, *args):

        # Ignore if context menu is visible
        context_menu = utility.screen_manager.current_screen.context_menu
        if context_menu and not (self.id.startswith('list_') and self.id.endswith('_button')): return

        # Don't proceed if I'm not displayed <=> If there's no parent
        if not self.get_root_window(): return
        pos = args[1]

        # Next line to_widget allow to compensate for relative layout
        inside = self.collide_point(*self.to_widget(*pos))

        if self.hovered == inside: return
        self.border_point = pos
        self.hovered = inside

        # Update state, but don't launch events when disabled
        if not self.disabled:
            if inside: self.dispatch('on_enter')
            else:      self.dispatch('on_leave')

    def on_enter(self): pass
    def on_leave(self): pass

from kivy.factory import Factory
from kivy.graphics import PushMatrix, PopMatrix, Scale
Factory.register('HoverBehavior', HoverBehavior)
default_scale = 1.025



# Recycle View Items
class RecycleViewWidget(RecycleView):
    def __init__(self, position=(0.5, 0.52), view_class=None, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, None)
        self.size = (Window.width, Window.height // 2)
        self.do_scroll_x = False
        if position: self.pos_hint = {"center_x": position[0], "center_y": position[1]}
        self.bar_width = 6
        self.drag_pad = self.bar_width * 15
        self.bar_color = (0.6, 0.6, 1, 1)
        self.bar_inactive_color = (0.6, 0.6, 1, 0.25)
        self.scroll_wheel_distance = dp(55)
        Clock.schedule_once(functools.partial(self.assign_viewclass, view_class), 0)

    # Allow scroll bar to be dragged
    def on_touch_move(self, touch, *args):
        if (touch.pos[0] > self.x + (self.width - self.drag_pad) and (self.y + self.height > touch.pos[1] > self.y)) and touch.button in ['left', 'right']:
            try:
                new_scroll = ((touch.pos[1] - self.y) / (self.height - (self.height * (self.vbar[1])))) - (self.vbar[1])
                self.scroll_y = 1 if new_scroll > 1 else 0 if new_scroll < 0 else new_scroll
                return True
            except ZeroDivisionError:
                pass
        return super().on_touch_move(touch)

    def on_touch_down(self, touch, *args):
        if (touch.pos[0] > self.x + (self.width - self.drag_pad) and (self.y + self.height > touch.pos[1] > self.y)) and touch.button in ['left', 'right']:
            try:
                new_scroll = ((touch.pos[1] - self.y) / (self.height - (self.height * (self.vbar[1])))) - (self.vbar[1])
                self.scroll_y = 1 if new_scroll > 1 else 0 if new_scroll < 0 else new_scroll
                return True
            except ZeroDivisionError:
                pass
        return super().on_touch_down(touch)

    def assign_viewclass(self, view_class, *args):
        self.viewclass = view_class



# Label that fits its own TextSize to the widget size
class AlignLabel(Label):
    def on_size(self, *args):
        self.text_size = self.size
