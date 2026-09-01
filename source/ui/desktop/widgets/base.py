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
from kivy.core.image import Image as CoreImage
from kivy.uix.relativelayout import RelativeLayout
from kivy.input.providers.mouse import MouseMotionEvent
from kivy.uix.recyclegridlayout import RecycleGridLayout
from kivy.graphics import (
    Color, Rectangle, Ellipse, Line, RoundedRectangle, InstructionGroup,
    StencilPush, StencilUse, StencilUnUse, StencilPop
)

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
from kivy.effects.scroll import ScrollEffect
from kivy.properties import BooleanProperty, ObjectProperty, ListProperty


from source.ui.desktop.utility import *
from source.ui.desktop import utility
from threading import Event



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



# Shared smooth scroll behavior
class ScrollBehavior:

    scroll_amount = 0.1
    scroll_speed = 1.225
    scroll_smoothing = 0.000001

    def __init__(self, smooth_wheel=True, **kwargs):
        super().__init__(**kwargs)

        self.smooth_wheel = smooth_wheel
        self.smooth_scrolling = False
        self._scroll_target = self.scroll_y
        self._scroll_clock = None
        self._scroll_callback = None


    @staticmethod
    def wheel_direction(button):
        if button == 'scrolldown': return 1
        if button == 'scrollup':   return -1
        return 0


    def _scroll_amount(self):
        try:
            scroll_range = self._viewport.height - self.height
            return min(1, (self.height * self.scroll_amount * self.scroll_speed) / scroll_range) if scroll_range > 0 else 0
        except:
            return 0


    def cancel_smooth_scroll(self):
        if self._scroll_clock:
            self._scroll_clock.cancel()

        self._scroll_clock = None
        self._scroll_callback = None
        self._scroll_target = self.scroll_y
        self.smooth_scrolling = False


    def smooth_scroll_to(self, position, animate=True, callback=None):
        self._scroll_target = max(0, min(float(position), 1))
        self._scroll_callback = callback

        if not animate:
            if self._scroll_clock:
                self._scroll_clock.cancel()

            self._scroll_clock = None
            self.smooth_scrolling = False
            self.scroll_y = self._scroll_target

            if callback:
                self._scroll_callback = None
                callback()

            return

        self.smooth_scrolling = True

        if not self._scroll_clock:
            self._scroll_clock = Clock.schedule_interval(self._smooth_scroll, 0)


    def smooth_scroll_by(self, amount):
        if not self.smooth_scrolling:
            self._scroll_target = self.scroll_y

        target = max(0, min(self._scroll_target + amount, 1))

        if target == self._scroll_target:
            return self.smooth_scrolling

        self.smooth_scroll_to(target)
        return True


    def _smooth_scroll(self, dt):
        error = self._scroll_target - self.scroll_y
        dt = max(0, min(dt, 0.05))

        if abs(error) > 0.0001:
            blend = 1 - pow(self.scroll_smoothing, dt)
            self.scroll_y += error * blend
            return True

        self.scroll_y = self._scroll_target
        self._scroll_clock = None
        self.smooth_scrolling = False

        callback, self._scroll_callback = self._scroll_callback, None
        if callback:
            callback()

        return False


    def _drag_scrollbar(self, touch):
        drag_pad = getattr(self, 'drag_pad', 0)

        if touch.pos[0] > self.x + (self.width - drag_pad) and (self.y + self.height > touch.pos[1] > self.y):
            self.cancel_smooth_scroll()

            try:
                new_scroll = ((touch.pos[1] - self.y) / (self.height - (self.height * self.vbar[1]))) - self.vbar[1]
                self.scroll_y = 1 if new_scroll > 1 else 0 if new_scroll < 0 else new_scroll
                return True

            except ZeroDivisionError:
                pass

        return False


    def on_touch_down(self, touch, *args):
        if getattr(touch, 'button', None) not in ('scrollup', 'scrolldown') and self._drag_scrollbar(touch):
            return True

        return super().on_touch_down(touch, *args)


    def on_touch_move(self, touch, *args):
        if self._drag_scrollbar(touch):
            return True

        return super().on_touch_move(touch, *args)


    def on_scroll_start(self, touch, check_children=True):
        button = getattr(touch, 'button', None)

        if self.smooth_wheel and button in ('scrollup', 'scrolldown'):

            # Preserve nested ScrollView behavior
            if check_children:
                touch.push()
                touch.apply_transform_2d(self.to_local)

                if self.dispatch_children('on_scroll_start', touch):
                    touch.pop()
                    return True

                touch.pop()

            if not self.collide_point(*touch.pos) or not self.do_scroll_y:
                return False

            amount = self._scroll_amount()
            if not amount:
                return False

            handled = self.smooth_scroll_by(self.wheel_direction(button) * amount)

            if handled:
                touch.ud[self._get_uid('svavoid')] = True

            return handled

        if self.smooth_scrolling:
            self.cancel_smooth_scroll()

        return super().on_scroll_start(touch, check_children)



# Label that fits its own TextSize to the widget size
class AlignLabel(Label):
    def on_size(self, *args):
        self.text_size = self.size
