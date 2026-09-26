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
from kivy.graphics.texture import Texture
from kivy.core.clipboard import Clipboard
from kivy.uix.image import Image, AsyncImage
from kivy.uix.floatlayout import FloatLayout
from kivy.effects.scroll import ScrollEffect
from kivy.eventmanager import EventManagerBase
from kivy.graphics import PushMatrix, PopMatrix, Rotate, Mesh
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.properties import BooleanProperty, ObjectProperty, NumericProperty, ListProperty


from source.ui.desktop.utility import *
from source.ui.desktop import utility
from collections import defaultdict
from PIL import Image as PILImage
from math import sin, cos, pi
from threading import Event
from io import BytesIO
import weakref



# Widget hover detection and custom event registration
class HoverManager(EventManagerBase):
    type_ids = ('hover',)
    event_repeat_timeout = 1 / 60

    def __init__(self, **kwargs):
        super().__init__()
        self.event_repeat_timeout = kwargs.get('event_repeat_timeout', self.event_repeat_timeout)
        self._events = defaultdict(list)
        self._event_times = {}
        self._clock_event = None

    def start(self):
        self.event_repeat_timeout = 1 / max(1, utility.refresh_rate)
        if self.event_repeat_timeout >= 0 and not self._clock_event:
            self._clock_event = Clock.schedule_interval(self._dispatch_from_clock, self.event_repeat_timeout)
    def stop(self):
        for event_list in self._events.values():
            me, grab_list = event_list[0]
            self._dispatch_to_grabbed_widgets(me, grab_list)

        self._events.clear()
        self._event_times.clear()

        if self._clock_event:
            self._clock_event.cancel()
            self._clock_event = None

    def dispatch(self, etype, me):
        original_grab_list = me.grab_list[:]
        del me.grab_list[:]

        accepted = self._dispatch_to_widgets(etype, me)

        self._events[me.uid].insert(0, (me, me.grab_list[:]))
        self._event_times[me.uid] = Clock.get_time()

        if len(self._events[me.uid]) == 2:
            _, previous_grab_list = self._events[me.uid].pop()
            self._dispatch_to_grabbed_widgets(me, previous_grab_list)

        if etype == 'end':
            self._events.pop(me.uid, None)
            self._event_times.pop(me.uid, None)

        me.grab_list[:] = original_grab_list
        return accepted

    def _dispatch_to_widgets(self, etype, me):
        accepted = False

        me.push()
        self.window.transform_motion_event_2d(me)

        for widget in self.window.children[:]:
            if widget.dispatch('on_motion', etype, me):
                accepted = True
                break

        me.pop()
        return accepted

    def _dispatch_to_grabbed_widgets(self, me, previous_grab_list):
        original_grab_state = me.grab_state
        original_time_end = me.time_end
        original_grab_list = me.grab_list[:]

        me.grab_list[:] = previous_grab_list
        me.update_time_end()
        me.grab_state = True

        for weak_widget in previous_grab_list:
            if weak_widget not in original_grab_list:
                widget = weak_widget()

                if widget:
                    self._dispatch_to_widget('end', me, widget)

        me.grab_list[:] = original_grab_list
        me.grab_state = original_grab_state
        me.time_end = original_time_end

    def _dispatch_to_widget(self, etype, me, widget):
        root_window = widget.get_root_window()

        if root_window and root_window != widget:
            me.push()

            try:
                self.window.transform_motion_event_2d(me, widget)

            except AttributeError:
                me.pop()
                return

        original_grab_current = me.grab_current
        me.grab_current = widget

        widget._context.push()

        if widget._context.sandbox:
            with widget._context.sandbox:
                widget.dispatch('on_motion', etype, me)

        else:
            widget.dispatch('on_motion', etype, me)

        widget._context.pop()
        me.grab_current = original_grab_current

        if root_window and root_window != widget:
            me.pop()

    def _repeat_event(self, me):
        psx, psy, psz = me.psx, me.psy, me.psz
        dsx, dsy, dsz = me.dsx, me.dsy, me.dsz

        me.psx, me.psy, me.psz = me.sx, me.sy, me.sz
        me.dsx = me.dsy = me.dsz = 0

        try:
            self.dispatch('update', me)

        finally:
            me.psx, me.psy, me.psz = psx, psy, psz
            me.dsx, me.dsy, me.dsz = dsx, dsy, dsz

    def refresh(self):
        events = [event_list[0][0] for event_list in self._events.values() if event_list]

        for me in events:
            self._repeat_event(me)

    def _dispatch_from_clock(self, *args):
        now = Clock.get_time()
        events = []

        for uid, event_list in self._events.items():
            me, _ = event_list[0]

            if now - self._event_times[uid] >= self.event_repeat_timeout:
                events.append(me)

        for me in events:
            self._repeat_event(me)
hover_manager = HoverManager()

# Widget hover detection and custom event registration
class HoverBehavior():
    hovered = BooleanProperty(False)
    border_point = ObjectProperty(None)
    hover_owner = None

    def __init__(self, *args, **kwargs):
        self.register_event_type('on_enter')
        self.register_event_type('on_leave')
        self.register_for_motion_event('hover')

        self._hover_ids = set()

        super().__init__(**kwargs)
        self.id = ''

    def _set_hover(self, me, inside):
        was_hovered = self.hovered
        if inside: self._hover_ids.add(me.uid)
        else:      self._hover_ids.discard(me.uid)

        self.border_point = Window.mouse_pos
        self.hovered = bool(self._hover_ids)
        if self.hovered != was_hovered and not self.disabled:
            if self.hovered: self.dispatch('on_enter')
            else:            self.dispatch('on_leave')

    def _hover_collide(self, me):
        return self.collide_point(*me.pos)

    def refresh_hover(self, force=False):
        was_hovered = self.hovered
        hover_manager.refresh()
        if force and self.hovered == was_hovered and not self.disabled:
            if self.hovered: self.dispatch('on_enter')
            else:            self.dispatch('on_leave')

    def on_motion(self, etype, me):
        if me.type_id != 'hover' or 'pos' not in me.profile:
            return super().on_motion(etype, me)

        # Grabbed widgets need to clean themselves up directly
        # It may have already been removed from the widget tree
        if etype == 'end' and me.grab_current is self:
            self._set_hover(me, False)
            me.ungrab(self)
            return True

        # Let hoverable children process the event too
        accepted = super().on_motion(etype, me) or False

        # Preserve context menu behavior
        if etype != 'end':
            context_menu = utility.screen_manager.current_screen.context_menu
            if context_menu and not (self.id.startswith('list_') and self.id.endswith('_button')):
                return accepted

        if etype in ('begin', 'update'):

            if me.grab_current is self:
                return True

            if self._hover_collide(me):
                me.grab(self)
                self._set_hover(me, True)

                if self.hover_owner:
                    me.grab(self.hover_owner)
                    self.hover_owner._set_hover(me, True)

                return True

        return accepted

    def on_enter(self): pass
    def on_leave(self): pass
class HoverBlockBehavior:

    hover_block_padding = (0, 0, 0, 0)

    def __init__(self, **kwargs):
        self.register_for_motion_event('hover')
        super().__init__(**kwargs)

    def _hover_block_collide(self, pos):
        x, y = pos
        left, bottom, right, top = self.hover_block_padding

        return (
            min(self.x, self.right) - left <= x <= max(self.x, self.right) + right and
            min(self.y, self.top) - bottom <= y <= max(self.y, self.top) + top
        )

    def on_motion(self, etype, me):
        if me.type_id == 'hover' and 'pos' in me.profile and self._hover_block_collide(me.pos):
            return True

        return super().on_motion(etype, me)
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
        self.smooth_scroll_end = None

        self.smooth_scrolling = False
        self._scroll_target = self.scroll_y
        self._scroll_clock = None
        self._scroll_callback = None
        self._smooth_scroll_write = False

        self._bar_drag_touch = None
        self._bar_drag_offset = 0
        self.drag_outer_pad = 10

        self.bind(
            scroll_y=self._scroll_y_changed,
            viewport_size=self._scroll_viewport_changed
        )

    @staticmethod
    def wheel_direction(button):
        if button == 'scrolldown': return 1
        if button == 'scrollup':   return -1
        return 0

    def _scroll_y_changed(self, *args):
        if self.smooth_scrolling and not self._smooth_scroll_write:
            self.cancel_smooth_scroll()

    def _scroll_viewport_changed(self, *args):
        if self.smooth_scrolling and not self._scroll_amount():
            self.cancel_smooth_scroll()

    def _set_smooth_scroll_y(self, value):
        self._smooth_scroll_write = True
        try: self.scroll_y = value
        finally: self._smooth_scroll_write = False

    def _scroll_amount(self):
        try:
            scroll_range = self._viewport.height - self.height
            return min(1, (self.height * self.scroll_amount * self.scroll_speed) / scroll_range) if scroll_range > 0 else 0
        except: return 0

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
            self._set_smooth_scroll_y(self.scroll_y + (error * blend))
            return True

        self._set_smooth_scroll_y(self._scroll_target)
        self._scroll_clock = None
        self.smooth_scrolling = False

        callback, self._scroll_callback = self._scroll_callback, None
        if callback:
            callback()

        return False

    def _scrollbar_hit(self, touch):
        if not self.do_scroll_y or self.vbar[1] >= 1:
            return False

        drag_pad = min(getattr(self, 'drag_pad', 0), self.width)
        outer_pad = getattr(self, 'drag_outer_pad', 0)

        if not self.y < touch.y < self.top:
            return False

        if self.bar_pos_y == 'left':
            return self.x - outer_pad <= touch.x <= self.x + drag_pad

        return self.right - drag_pad <= touch.x <= self.right + outer_pad

    def _drag_scrollbar(self, touch):
        bar_height = self.height * self.vbar[1]
        track_height = self.height - bar_height

        if track_height <= 0:
            return False

        center_y = touch.y - self._bar_drag_offset
        new_scroll = (center_y - self.y - (bar_height / 2)) / track_height
        self.scroll_y = max(0, min(new_scroll, 1))

        return True

    def on_touch_down(self, touch, *args):
        if getattr(touch, 'button', None) in ('left', 'right') and self._scrollbar_hit(touch):
            self.cancel_smooth_scroll()

            bar_y = self.y + (self.height * self.vbar[0])
            bar_height = self.height * self.vbar[1]

            if bar_y <= touch.y <= bar_y + bar_height:
                self._bar_drag_offset = touch.y - (bar_y + (bar_height / 2))
            else:
                self._bar_drag_offset = 0

            self._bar_drag_touch = touch
            touch.grab(self)

            self._drag_scrollbar(touch)
            return True

        return super().on_touch_down(touch, *args)

    def on_touch_move(self, touch, *args):
        if touch is self._bar_drag_touch:
            self._drag_scrollbar(touch)
            return True
        return super().on_touch_move(touch, *args)

    def on_touch_up(self, touch, *args):
        if touch is self._bar_drag_touch:
            touch.ungrab(self)
            self._bar_drag_touch = None
            self._bar_drag_offset = 0
            return True
        return super().on_touch_up(touch, *args)

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



# Add weakref support to RecycleView items
class RecycleViewItemBehavior(RecycleDataViewBehavior):
    _recycle_view_ref = None

    @property
    def recycle_view(self):
        return self._recycle_view_ref() if self._recycle_view_ref else None

    @property
    def recycle_owner(self):
        rv = self.recycle_view
        return getattr(rv, 'owner', None) if rv else None

    def refresh_view_attrs(self, rv, index, data):
        # Never retain the RecycleView itself from a globally pooled view.
        self._recycle_view_ref = weakref.ref(rv)

        # Owner/context is now available before RV data is applied.
        return super().refresh_view_attrs(rv, index, data)



# Label that fits its own TextSize to the widget size
class AlignLabel(Label):
    def on_size(self, *args):
        self.text_size = self.size
