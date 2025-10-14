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



# Custom widget attributes
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



# Recycle View Items
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



class AlignLabel(Label):
    def on_size(self, *args):
        self.text_size = self.size
