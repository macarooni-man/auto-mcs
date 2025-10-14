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

from kivy.lang import Builder
from kivy.factory import Factory
from kivy.graphics import PushMatrix, PopMatrix, Scale
Factory.register('HoverBehavior', HoverBehavior)
default_scale = 1.025

def _animate_background(self, image, hover_action, do_scale=default_scale, _new_color: tuple = None, _no_bg_change: bool = False):
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

    _animate_background(self, image, hover_action, do_scale, _new_color, (_no_bg_change or duration == 0))

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

    _animate_background(self, image, hover_action, do_scale, _new_color, (_no_bg_change or duration == 0))

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

# -----------------------------------------------------  Labels  -------------------------------------------------------
class InputLabel(RelativeLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.id = 'InputLabel'
        self.text_size = sp(21)

        self.text = Label()
        self.text.id = 'text'
        self.text.text = "Invalid input"
        self.text.font_size = self.text_size
        self.text_x = self.text.x
        self.text.x += dp(15)
        self.text.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
        self.text.color = (1, 0.53, 0.58, 0)

        self.icon = Image()
        self.icon.id = 'icon'
        self.icon.source = os.path.join(paths.ui_assets, 'icons', 'alert-circle-outline.png')
        self.icon.color = (1, 0.53, 0.58, 0)
        self.icon_x = self.icon.x
        self.icon.x -= dp((len(self.text.text) * (self.text_size - 8)) / 3) - dp(20)

        self.add_widget(self.text)
        self.add_widget(self.icon)


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
                child.source = os.path.join(paths.ui_assets, 'icons', 'alert-circle-outline.png')
                child.x = self.icon_x - dp((len(text) * (self.text_size - 8)) / 3) - dp(20)

                if [round(x, 2) for x in child.color] != [round(x, 2) for x in chosen_color]:
                    change_color(child)


    def clear_text(self):
        for child in self.children:
            new_color = (child.color[0], child.color[1], child.color[2], 0)
            Animation(color=new_color, duration=0.12).start(child)

            def reset_color(item, *args):
                item.color = (1, 0.53, 0.58, 0)

            Clock.schedule_once(functools.partial(reset_color, child), 0.12)


class BaseInput(TextInput):

    # Sound when pressing ENTER
    @staticmethod
    def _enter_sound(): audio.player.play('interaction/click_*', jitter=(0, 0.15))


    def _on_focus(self, instance, value, *largs):
        super()._on_focus(instance, value, *largs)

        # Log for crash info
        if value:
            try:
                interaction = str(self.__class__.__name__)
                if self.title.text:
                    interaction += f" ({self.title.text.title()})"
                constants.last_widget = interaction + f" @ {constants.format_now()}"
                send_log('navigation', f"interaction: '{interaction}'")
            except:
                pass

        # Update screen focus value on next frame
        def update_focus(*args):
            utility.screen_manager.current_screen._input_focused = self.focus
        Clock.schedule_once(update_focus, 0)


    def grab_focus(self, *a):
        def focus_later(*args):
            self.focus = True
        Clock.schedule_once(focus_later, 0)


    def fix_overscroll(self, *args):

        if self.cursor_pos[0] < (self.x):
            self.scroll_x = 0


    def update_rect(self, *args):
        self.rect.source = os.path.join(paths.ui_assets, f'text_input_cover{"" if self.focused else "_fade"}.png')

        self.title.text = self.title_text
        self.rect.width = (len(self.title.text) * 16) + 116 if self.title.text else 0
        if self.width > 500:
            self.rect.width += (self.width - 500)
        self.rect.pos = self.pos[0] + (self.size[0] / 2) - (self.rect.size[0] / 2) - 1, self.pos[1] + 45
        self.title.pos = self.pos[0] + (self.size[0] / 2) - (self.title.size[0] / 2), self.pos[1] + 4
        Animation(opacity=(0.85 if self.text and self.title_text else 0), color=self.foreground_color, duration=0.06).start(self.title)
        Animation(opacity=(1 if self.text and self.title_text else 0), duration=0.08).start(self.rect)

        if self.disabled:
            Animation.stop_all(self.title)
            c = self.foreground_color
            self.title.opacity = 0.85
            self.title.color = (c[0], c[1], c[2], 0.4)

        # Auto position cursor at end if typing
        if self.cursor_index() == len(self.text) - 1:
            self.do_cursor_movement('cursor_end', True)
            Clock.schedule_once(functools.partial(self.do_cursor_movement, 'cursor_end', True), 0.01)


    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.title_text = "InputTitle"
        self.is_valid = True

        self.multiline = False
        self.size_hint_max = (500, 54)
        self.border = (-15, -15, -15, -15)
        self.background_normal = os.path.join(paths.ui_assets, f'text_input.png')
        self.background_active = os.path.join(paths.ui_assets, f'text_input_selected.png')
        self.background_disabled_normal = self.background_normal

        self.halign = "center"
        self.hint_text_color = (0.6, 0.6, 1, 0.4)
        self.foreground_color = (0.6, 0.6, 1, 1)
        self.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
        self.font_size = sp(22)
        self.padding_y = (12, 12)
        self.cursor_color = (0.55, 0.55, 1, 1)
        self.cursor_width = dp(3)
        self.selection_color = (0.5, 0.5, 1, 0.4)

        with self.canvas.after:
            self.rect = Image(size=(100, 15), color=utility.screen_manager.current_screen.background_color, opacity=0, allow_stretch=True, keep_ratio=False)
            self.title = AlignLabel(halign="center", text=self.title_text, color=self.foreground_color, opacity=0, font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["regular"]}.ttf'))
            self.bind(pos=self.update_rect)
            self.bind(size=self.update_rect)
            self.bind(text=self.update_rect)
            self.bind(foreground_color=self.update_rect)
            self.bind(focused=self.update_rect)

        if self.disabled:
            c = self.foreground_color
            self.disabled_foreground_color = (c[0], c[1], c[2], 0.4)
            self.background_color = (1, 1, 1, 0.4)

        self.bind(cursor_pos=self.fix_overscroll)


    # Ignore popup text
    def insert_text(self, substring, from_undo=False):
        if utility.screen_manager.current_screen.popup_widget:
            return None

        super().insert_text(substring, from_undo)


    def valid_text(self, boolean_value, text):
        pass

    #               if error       visible text
    def valid(self, boolean_value, text=True):

        if boolean_value:

            # Hide text
            self.valid_text(boolean_value, text)
            self.is_valid = True

            self.background_normal = os.path.join(paths.ui_assets, f'text_input.png')
            self.background_active = os.path.join(paths.ui_assets, f'text_input_selected.png')
            self.hint_text_color = (0.6, 0.6, 1, 0.4)
            self.foreground_color = (0.6, 0.6, 1, 1)
            self.cursor_color = (0.55, 0.55, 1, 1)
            self.selection_color = (0.5, 0.5, 1, 0.4)

        else:

            # Show error
            self.valid_text(boolean_value, text)
            self.is_valid = False

            self.background_normal = os.path.join(paths.ui_assets, f'text_input_invalid.png')
            self.background_active = os.path.join(paths.ui_assets, f'text_input_invalid_selected.png')
            self.hint_text_color = (1, 0.6, 0.6, 0.4)
            self.foreground_color = (1, 0.56, 0.6, 1)
            self.cursor_color = (1, 0.52, 0.55, 1)
            self.selection_color = (1, 0.5, 0.5, 0.4)

    # Ignore touch events when popup is present
    def on_touch_down(self, touch):
        popup_widget = utility.screen_manager.current_screen.popup_widget
        if popup_widget:
            return
        else:
            return super().on_touch_down(touch)

    # Special keypress behaviors
    def keyboard_on_key_down(self, window, keycode, text, modifiers):

        if keycode[1] == "backspace" and control in modifiers:
            original_index = self.cursor_col
            new_text, index = constants.control_backspace(self.text, original_index)
            self.select_text(original_index - index, original_index)
            self.delete_selection()
        else:
            super().keyboard_on_key_down(window, keycode, text, modifiers)

class BigBaseInput(BaseInput):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.title_text = "InputTitle"
        self.is_valid = True

        self.multiline = False
        self.size_hint_max = (400, 100)
        self.border = (-15, -15, -15, -15)
        self.background_normal = os.path.join(paths.ui_assets, f'big_input.png')
        self.background_active = os.path.join(paths.ui_assets, f'big_input_selected.png')
        self.background_disabled_normal = self.background_normal

        self.halign = "center"
        self.hint_text_color = (0.6, 0.6, 1, 0.4)
        self.foreground_color = (0.6, 0.6, 1, 1)
        self.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
        self.font_size = sp(22)
        self.padding_y = (12, 12)
        self.cursor_color = (0.55, 0.55, 1, 1)
        self.cursor_width = dp(3)
        self.selection_color = (0.5, 0.5, 1, 0.4)

        with self.canvas.after:
            self.rect = Image(size=(100, 15), color=utility.screen_manager.current_screen.background_color, opacity=0, allow_stretch=True, keep_ratio=False)
            self.title = AlignLabel(halign="center", text=self.title_text, color=self.foreground_color, opacity=0, font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["regular"]}.ttf'))
            self.bind(pos=self.update_rect)
            self.bind(size=self.update_rect)
            self.bind(text=self.update_rect)
            self.bind(foreground_color=self.update_rect)
            self.bind(focused=self.update_rect)

        if self.disabled:
            c = self.foreground_color
            self.disabled_foreground_color = (c[0], c[1], c[2], 0.4)
            self.background_color = (1, 1, 1, 0.4)

        self.bind(cursor_pos=self.fix_overscroll)


    def update_rect(self, *args):
        self.rect.source = os.path.join(paths.ui_assets, f'text_input_cover{"" if self.focused else "_fade"}.png')

        self.title.text = self.title_text
        self.rect.width = (len(self.title.text) * 16) + 116 if self.title.text else 0
        if self.width > 500:
            self.rect.width += (self.width - 500)
        self.rect.pos = self.pos[0] + (self.size[0] / 2) - (self.rect.size[0] / 2) - 1, self.pos[1] + 43 + 50
        self.title.pos = self.pos[0] + (self.size[0] / 2) - (self.title.size[0] / 2), self.pos[1] + 2 + 50
        Animation(opacity=(0.85 if self.text and self.title_text else 0), color=self.foreground_color, duration=0.06).start(self.title)
        Animation(opacity=(1 if self.text and self.title_text else 0), duration=0.08).start(self.rect)

        if self.disabled:
            Animation.stop_all(self.title)
            c = self.foreground_color
            self.title.opacity = 0.85
            self.title.color = (c[0], c[1], c[2], 0.4)

        # Auto position cursor at end if typing
        if self.cursor_index() == len(self.text) - 1:
            self.do_cursor_movement('cursor_end', True)
            Clock.schedule_once(functools.partial(self.do_cursor_movement, 'cursor_end', True), 0.01)

    #               if error       visible text
    def valid(self, boolean_value, text=True):

        if boolean_value:

            # Hide text
            self.valid_text(boolean_value, text)
            self.is_valid = True

            self.background_normal = os.path.join(paths.ui_assets, f'big_input.png')
            self.background_active = os.path.join(paths.ui_assets, f'big_input_selected.png')
            self.hint_text_color = (0.6, 0.6, 1, 0.4)
            self.foreground_color = (0.6, 0.6, 1, 1)
            self.cursor_color = (0.55, 0.55, 1, 1)
            self.selection_color = (0.5, 0.5, 1, 0.4)

        else:

            # Show error
            self.valid_text(boolean_value, text)
            self.is_valid = False

            self.background_normal = os.path.join(paths.ui_assets, f'big_input_invalid.png')
            self.background_active = os.path.join(paths.ui_assets, f'big_input_invalid_selected.png')
            self.hint_text_color = (1, 0.6, 0.6, 0.4)
            self.foreground_color = (1, 0.56, 0.6, 1)
            self.cursor_color = (1, 0.52, 0.55, 1)
            self.selection_color = (1, 0.5, 0.5, 0.4)


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

        self.icon = os.path.join(paths.ui_assets, 'icons', 'search-sharp.png')
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

    def __init__(self, return_function, allow_empty=False, **kwargs):
        super().__init__(**kwargs)
        self.allow_empty = allow_empty
        self.id = "search_input"
        self.title_text = ""
        self.hint_text = "enter a query..."
        self.halign = "left"
        self.padding_x = 24
        self.background_normal = os.path.join(paths.ui_assets, f'search_input.png')
        self.background_active = os.path.join(paths.ui_assets, f'search_input_selected.png')
        self.bind(on_text_validate=self.on_enter)


    def on_enter(self, value):
        if (self.text or self.allow_empty) and self.parent.previous_search != self.text:
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

        self.background_normal = os.path.join(paths.ui_assets, f'search_input.png')
        self.background_active = os.path.join(paths.ui_assets, f'search_input_selected.png')
        self.hint_text_color = (0.6, 0.6, 1, 0.4)
        self.foreground_color = (0.6, 0.6, 1, 1)
        self.cursor_color = (0.55, 0.55, 1, 1)
        self.selection_color = (0.5, 0.5, 1, 0.4)

def search_input(return_function=None, server_info=None, pos_hint={"center_x": 0.5, "center_y": 0.5}, allow_empty=False):
    class SearchLayout(FloatLayout):

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.previous_search = ""

        # Gather search results from passed in function
        def execute_search(self, query, *a):
            self.previous_search = query

            def execute():
                current_screen = utility.screen_manager.current_screen.name
                self.loading(True)
                results = False

                try:
                    results = return_function(query) if not server_info else return_function(query, server_info)
                except ConnectionRefusedError:
                    pass

                if not results and isinstance(results, bool):
                    self.previous_search = ""

                if utility.screen_manager.current_screen.name == current_screen:
                    update_screen = functools.partial(utility.screen_manager.current_screen.gen_search_results, results, True)
                    Clock.schedule_once(update_screen, 0)

                    self.loading(False)

            timer = dTimer(0, function=execute)
            timer.start()  # Checks for potential crash


        def loading(self, boolean_value):

            def main_thread(*a):

                for child in self.children:
                    if child.id == "load_icon":
                        if boolean_value:
                            Animation(color=(0.6, 0.6, 1, 1), duration=0.05).start(child)
                        else:
                            Animation(color=(0.6, 0.6, 1, 0), duration=0.2).start(child)

                    if child.id == "search_button":
                        utility.hide_widget(child, boolean_value)

            Clock.schedule_once(main_thread, 0)

    def repos_button(bar, button, load, *args):
        def after_window(*args):
            button.x = bar.x + bar.width - button.width - 18
            load.x = bar.x + bar.width - load.width - 14

        Clock.schedule_once(after_window, 0)

    final_layout = SearchLayout()

    # Input box
    search_bar = SearchInput(return_function, allow_empty)
    search_bar.pos_hint = pos_hint

    # Search icon on the right of box
    search_button = SearchButton()
    search_button.pos_hint = {"center_y": pos_hint['center_y']}
    search_button.size_hint_max = (search_bar.height / 3.6, search_bar.height / 3.6)

    # Loading icon to swap button
    load_icon = AsyncImage()
    load_icon.id = "load_icon"
    load_icon.source = os.path.join(paths.ui_assets, 'animations', 'loading_pickaxe.gif')
    load_icon.size_hint_max = (search_bar.height / 3, search_bar.height / 3)
    load_icon.color = (0.6, 0.6, 1, 0)
    load_icon.pos_hint = {"center_y": pos_hint['center_y']}
    load_icon.allow_stretch = True
    load_icon.anim_delay = utility.anim_speed * 0.02

    # Assemble layout
    final_layout.bind(pos=functools.partial(repos_button, search_bar, search_button, load_icon))
    final_layout.bind(size=functools.partial(repos_button, search_bar, search_button, load_icon))
    final_layout.add_widget(search_bar)
    final_layout.add_widget(search_button)
    final_layout.add_widget(load_icon)

    return final_layout



class ServerNameInput(BaseInput):

    def get_server_list(self):
        try:
            telepath_data = foundry.new_server_info['_telepath_data']
            if telepath_data:
                self.server_list = constants.get_remote_var('server_manager.server_list_lower', telepath_data)
                return True
        except:
            pass
        self.server_list = constants.server_manager.server_list_lower

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.title_text = "name"
        self.hint_text = "enter a name..."
        self.bind(on_text_validate=self.on_enter)
        self.server_list = []
        self.get_server_list()


    def on_enter(self, value, click_next=True, *args):

        foundry.new_server_info['name'] = (self.text).strip()

    # Invalid input
        if not self.text or str.isspace(self.text):
            self.valid(True, False)

        elif self.text.lower().strip() in self.server_list:
            self.valid(False)

    # Valid input
        elif click_next:
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
            foundry.new_server_info['name'] = (self.text).strip()

            self.valid((self.text).lower().strip() not in self.server_list)

        def check_validity(*a):
            if not self.text or str.isspace(self.text):
                self.valid(True, False)
        Clock.schedule_once(check_validity, 0)


    # Input validation
    def insert_text(self, substring, from_undo=False):

        if not self.text and substring == " ":
            substring = ""

        elif len(self.text) < 25:
            if '\n' in substring:
                substring = substring.splitlines()[0]
            s = re.sub('[^a-zA-Z0-9 _().-]', '', substring)

            is_valid = (self.text + s).lower().strip() not in self.server_list
            self.valid(is_valid, ((len(self.text + s) > 0) and not (str.isspace(self.text))))

            # Add name to current config
            def get_text(*a):
                foundry.new_server_info['name'] = self.text.strip()
            Clock.schedule_once(get_text, 0)

            return super().insert_text(s, from_undo=from_undo)



    def update_server(self, force_ignore=False, hide_popup=False):

        def disable_next(disable=False):
            for item in utility.screen_manager.current_screen.next_button.children:
                try:
                    if item.id == "next_button":
                        item.disable(disable)
                        break
                except AttributeError:
                    pass

        self.scroll_x = 0

        if self.text:
            if self.text.lower().strip() in self.server_list:
                self.valid(False)
                disable_next(True)

            # If server is valid, do this
            else:
                self.valid(True)
                disable_next(False)


class ServerRenameInput(BaseInput):

    def get_server_list(self):
        try:
            telepath_data = constants.server_manager.current_server._telepath_data
            if telepath_data:
                self.server_list = constants.get_remote_var('server_manager.server_list_lower', telepath_data)
                return True
        except:
            pass
        self.server_list = constants.server_manager.server_list_lower

    def _on_focus(self, instance, value, *largs):
        super()._on_focus(instance, value)
        if not self.focus and self.text != self.starting_text.strip():
            self.text = self.starting_text
            self.valid(True, True)

    def __init__(self, on_validate, **kwargs):
        super().__init__(**kwargs)

        self.validate = on_validate
        self.title_text = "rename"
        self.hint_text = "enter a new name..."
        self.bind(on_text_validate=self.on_enter)
        self.is_valid = False
        self.starting_text = self.text
        self.server_list = []
        self.get_server_list()


    def on_enter(self, value):

        # Invalid input
        if not self.text or str.isspace(self.text):
            self.valid(True, False)
            self._enter_sound()

        elif (self.text.lower().strip() in self.server_list) and (self.text.lower().strip() != self.starting_text.lower().strip()):
            self.valid(False)

        if self.is_valid and self.text.strip() and (self.text.lower().strip() != self.starting_text.lower().strip()):
            self.starting_text = self.text.strip()
            self.validate((self.text).strip())
            self._enter_sound()

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
            text_check = (self.text.lower().strip())
            self.valid((text_check not in self.server_list) or (text_check == self.starting_text.lower().strip()))

        def check_validity(*a):
            if not self.text or str.isspace(self.text):
                self.valid(True, False)
        Clock.schedule_once(check_validity, 0)


    # Input validation
    def insert_text(self, substring, from_undo=False):

        if not self.text and substring == " ":
            substring = ""

        elif len(self.text) < 25:
            if '\n' in substring:
                substring = substring.splitlines()[0]
            s = re.sub('[^a-zA-Z0-9 _().-]', '', substring)

            text_check = (self.text + s).lower().strip()
            self.valid((text_check not in self.server_list) or (text_check == self.starting_text.lower().strip()), ((len(self.text + s) > 0) and not (str.isspace(self.text))))

            return super().insert_text(s, from_undo=from_undo)


class ScriptNameInput(BaseInput):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.title_text = "name"
        self.hint_text = "enter a name..."
        self.bind(on_text_validate=self.on_enter)
        self.script_list = []


    def update_script_list(self, s_list):
        self.script_list = [x.file_name.lower() for x in s_list]

    @staticmethod
    def convert_name(name):
        return name.lower().strip().replace(' ', '-') + '.ams'


    def on_enter(self, value):

    # Invalid input
        if not self.text or str.isspace(self.text):
            self.valid(True, False)

        elif self.convert_name(self.text) in self.script_list:
            self.valid(False)

    # Valid input
        else:
            break_loop = False
            for child in self.parent.children:
                if break_loop:
                    break
                for item in child.children:
                    try:
                        if item.id == "main_button":
                            item.force_click()
                            break_loop = True
                            break
                    except AttributeError:
                        pass


    def valid_text(self, boolean_value, text):
        create_button = utility.screen_manager.current_screen.create_button
        for child in self.parent.children:
            try:
                if child.id == "InputLabel":

                # Empty input
                    if not text:
                        child.clear_text()
                        child.disable_text(True)
                        create_button.disable(True)


                # Valid input
                    elif boolean_value:
                        child.clear_text()
                        child.disable_text(False)
                        create_button.disable(False)

                # Invalid input
                    else:
                        child.update_text("This script already exists")
                        child.disable_text(True)
                        create_button.disable(True)
                    break

            except AttributeError:
                pass


    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        super().keyboard_on_key_down(window, keycode, text, modifiers)

        if keycode[1] == "backspace" and len(self.text) >= 1:
            self.valid(self.convert_name(self.text) not in self.script_list)

        def check_validity(*a):
            if not self.text or str.isspace(self.text):
                self.valid(True, False)
        Clock.schedule_once(check_validity, 0)


    # Input validation
    def insert_text(self, substring, from_undo=False):

        if not self.text and substring == " ":
            substring = ""

        elif len(self.text) < 25:
            if '\n' in substring:
                substring = substring.splitlines()[0]
            s = re.sub('[^a-zA-Z0-9 _().-]', '', substring)

            self.valid(self.convert_name(self.text + s) not in self.script_list, ((len(self.text + s) > 0) and not (str.isspace(self.text))))

            return super().insert_text(s, from_undo=from_undo)


class ServerVersionInput(BaseInput):

    def __init__(self, enter_func=None, **kwargs):
        super().__init__(**kwargs)
        self.enter_func = enter_func
        self.title_text = "version"
        server_type = foundry.latestMC[foundry.new_server_info['type']]
        self.hint_text = f"click 'next' for latest  (${server_type}$)"
        self.bind(on_text_validate=self.on_enter)


    def on_touch_down(self, touch):
        if not constants.version_loading:
            super().on_touch_down(touch)

        else:
            self.focus = False


    def on_enter(self, value):

        if not constants.version_loading:

            if self.text:
                foundry.new_server_info['version'] = (self.text).strip()
            else:
                foundry.new_server_info['version'] = foundry.latestMC[foundry.new_server_info['type']]

            if self.enter_func:
                self.enter_func()

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
                            self.text = foundry.new_server_info['version']
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
                    foundry.new_server_info['version'] = (self.text).strip()
                else:
                    foundry.new_server_info['version'] = foundry.latestMC[foundry.new_server_info['type']]


    # Input validation
    def insert_text(self, substring, from_undo=False):

        if not constants.version_loading:

            if not self.text and substring == " ":
                substring = ""

            elif len(self.text) < 10:
                self.valid(True, True)

                if '\n' in substring:
                    substring = substring.splitlines()[0]
                s = re.sub('[^a-eA-E0-9 .wpreWPRE-]', '', substring).lower()

                # Add name to current config
                if self.text + s:
                    def get_text(*a):
                        foundry.new_server_info['version'] = self.text.strip()
                    Clock.schedule_once(get_text, 0)
                else:
                    foundry.new_server_info['version'] = foundry.latestMC[foundry.new_server_info['type']]

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
            self.focus_images.ghost_cover_left = Image(source=os.path.join(paths.ui_assets, f'text_input_ghost_cover.png'))
            self.focus_images.ghost_cover_right = Image(source=os.path.join(paths.ui_assets, f'text_input_ghost_cover.png'))
            self.focus_images.ghost_image = Image(source=os.path.join(paths.ui_assets, f'text_input_ghost_selected.png'))
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


class CreateServerWorldInput(DirectoryInput):

    # Hide input_button on focus
    def _on_focus(self, *args):
        super()._on_focus(*args)

        for child in self.parent.children:
            for child_item in child.children:
                try:
                    if child_item.id == "input_button":

                        if foundry.new_server_info['server_settings']['world'] == "world":
                            self.hint_text = "type a directory, or click browse..." if self.focus else "create a new world"

                        # Run input validation on focus change
                        if self.focus:
                            self.valid(True, True)

                        # If unfocused, validate text
                        if not self.focus and self.text and child_item.height == 0:
                            self.on_enter(self.text)

                        # If box deleted and unfocused, set back to previous text
                        elif not self.focus and not self.text and foundry.new_server_info['server_settings']['world'] != "world":
                            self.text = self.cache_text

                        # If box filled in and text box clicked
                        if self.focus and self.text:
                            self.text = foundry.new_server_info['server_settings']['world']
                            self.do_cursor_movement('cursor_end', True)
                            Clock.schedule_once(functools.partial(self.do_cursor_movement, 'cursor_end', True), 0.01)
                            Clock.schedule_once(functools.partial(self.select_text, 0), 0.01)

                        [utility.hide_widget(item, self.focus) for item in child.children]

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
        world = foundry.new_server_info['server_settings']['world']
        self.selected_world = None if world == 'world' else world
        self.world_verified = False
        self.update_world(hide_popup=True)

    def on_enter(self, value):

        if constants.os_name == "windows" and "\\" not in self.text:
            self.text = os.path.join(paths.minecraft_saves, self.text)

        elif constants.os_name != "windows" and "/" not in self.text:
            self.text = os.path.join(paths.minecraft_saves, self.text)

        self.selected_world = self.text.replace("~", paths.user_home)
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
                        foundry.new_server_info['server_settings']['world'] = 'world'
                        if not force_ignore:
                            self.valid_text(False, False)
                        self.parent.parent.toggle_new(False)
                    except AttributeError:
                        pass

            # If world is valid, do this
            else:
                if foundry.new_server_info['server_settings']['world'] != "world":
                    box_text = os.path.join(
                        *Path(os.path.abspath(foundry.new_server_info['server_settings']['world'])).parts[-2:])
                    self.cache_text = self.text = box_text[:30] + "..." if len(box_text) > 30 else box_text

                def world_valid():
                    def execute(*a):
                        box_text = os.path.join(*Path(os.path.abspath(self.selected_world)).parts[-2:])
                        self.cache_text = self.text = box_text[:30] + "..." if len(box_text) > 30 else box_text
                        try:
                            foundry.new_server_info['server_settings']['world'] = self.selected_world
                            self.valid_text(True, True)
                            self.parent.parent.toggle_new(True)
                        except AttributeError:
                            pass
                    Clock.schedule_once(execute, 0)

                def clear_world():
                    def execute(*a):
                        foundry.new_server_info['server_settings']['world'] = 'world'
                        self.hint_text = "create a new world"
                        self.text = ""
                        self.cache_text = ""
                        self.selected_world = None
                        self.world_verified = False
                        self.update_world(hide_popup=True)
                    Clock.schedule_once(execute, 0)



                # When valid world selected, check if it matches server version
                check_world = constants.check_world_version(self.selected_world, foundry.new_server_info['version'])

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
                    elif constants.version_check(foundry.new_server_info['version'], "<", "1.9"):
                        content = f"'{basename}' was created in a version prior to 1.9 and may be incompatible.\
\n\nWould you like to use this world anyway?"

                    if content:
                        Clock.schedule_once(
                            functools.partial(
                                utility.screen_manager.current_screen.show_popup,
                                "query",
                                "Potential Incompatibility",
                                content,
                                [functools.partial(clear_world), functools.partial(world_valid)]
                            ), 0
                        )

                    else:
                        world_valid()

class ServerWorldInput(DirectoryInput):

    # Hide input_button on focus
    def _on_focus(self, *args):
        super()._on_focus(*args)

        for child in self.parent.children:
            for child_item in child.children:
                try:
                    if child_item.id == "input_button":

                        if utility.screen_manager.current_screen.new_world == "world":
                            self.hint_text = "type a directory, or click browse..." if self.focus else "create a new world"

                        # Run input validation on focus change
                        if self.focus:
                            self.valid(True, True)

                        # If unfocused, validate text
                        if not self.focus and self.text and child_item.height == 0:
                            self.on_enter(self.text)

                        # If box deleted and unfocused, set back to previous text
                        elif not self.focus and not self.text and utility.screen_manager.current_screen.new_world != "world":
                            self.text = self.cache_text

                        # If box filled in and text box clicked
                        if self.focus and self.text:
                            self.text = utility.screen_manager.current_screen.new_world
                            self.do_cursor_movement('cursor_end', True)
                            Clock.schedule_once(functools.partial(self.do_cursor_movement, 'cursor_end', True), 0.01)
                            Clock.schedule_once(functools.partial(self.select_text, 0), 0.01)

                        [utility.hide_widget(item, self.focus) for item in child.children]

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
        world = utility.screen_manager.current_screen.new_world
        self.selected_world = None if world == 'world' else world
        self.world_verified = False
        self.update_world(hide_popup=True)

    def on_enter(self, value):

        if constants.os_name == "windows" and "\\" not in self.text:
            self.text = os.path.join(paths.minecraft_saves, self.text)

        elif constants.os_name != "windows" and "/" not in self.text:
            self.text = os.path.join(paths.minecraft_saves, self.text)

        self.selected_world = self.text.replace("~", paths.user_home)
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
                        utility.screen_manager.current_screen.new_world = 'world'
                        if not force_ignore:
                            self.valid_text(False, False)
                        self.parent.parent.toggle_new(False)
                    except AttributeError:
                        pass

            # If world is valid, do this
            else:
                if utility.screen_manager.current_screen.new_world != "world":
                    box_text = os.path.join(
                        *Path(os.path.abspath(utility.screen_manager.current_screen.new_world)).parts[-2:])
                    self.cache_text = self.text = box_text[:30] + "..." if len(box_text) > 30 else box_text

                def world_valid():
                    def execute(*a):
                        box_text = os.path.join(*Path(os.path.abspath(self.selected_world)).parts[-2:])
                        self.cache_text = self.text = box_text[:30] + "..." if len(box_text) > 30 else box_text
                        try:
                            utility.screen_manager.current_screen.new_world = self.selected_world
                            self.valid_text(True, True)
                            self.parent.parent.toggle_new(True)
                        except AttributeError:
                            pass
                    Clock.schedule_once(execute, 0)

                def clear_world():
                    def execute(*a):
                        utility.screen_manager.current_screen.new_world = 'world'
                        self.hint_text = "create a new world"
                        self.text = ""
                        self.cache_text = ""
                        self.selected_world = None
                        self.world_verified = False
                        self.update_world(hide_popup=True)
                    Clock.schedule_once(execute, 0)


                # When valid world selected, check if it matches server version
                check_world = constants.check_world_version(self.selected_world, constants.server_manager.current_server.version)

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
                    elif constants.version_check(constants.server_manager.current_server.version, "<", "1.9"):
                        content = f"'{basename}' was created in a version prior to 1.9 and may be incompatible.\
\n\nWould you like to use this world anyway?"

                    if content:
                        Clock.schedule_once(
                            functools.partial(
                                utility.screen_manager.current_screen.show_popup,
                                "query",
                                "Potential Incompatibility",
                                content,
                                [functools.partial(clear_world), functools.partial(world_valid)]
                            ), 0
                        )

                    else:
                        world_valid()


class CreateServerSeedInput(BaseInput):

    # Hide input_button on focus
    def _on_focus(self, *args):
        try:
            super()._on_focus(*args)

            if constants.version_check(foundry.new_server_info['version'], '>=', "1.1"):
                for child in self.parent.children:
                    for child_item in child.children:
                        try:
                            if "drop_button" in child_item.id:

                                # If box filled in and text box clicked
                                if self.focus and self.text:
                                    self.text = foundry.new_server_info['server_settings']['seed']
                                    self.do_cursor_movement('cursor_end', True)
                                    Clock.schedule_once(functools.partial(self.do_cursor_movement, 'cursor_end', True), 0.01)
                                    Clock.schedule_once(functools.partial(self.select_text, 0), 0.01)

                                if not self.focus:
                                    # If text under button, cut it off temporarily
                                    self.scroll_x = 0
                                    self.cursor = (len(self.text), 0)
                                    if self.cursor_pos[0] > (self.x + self.width) - (self.width * 0.38):
                                        self.text = foundry.new_server_info['server_settings']['seed'][:16] + "..."
                                    self.scroll_x = 0
                                    Clock.schedule_once(functools.partial(self.select_text, 0), 0.01)

                                [utility.hide_widget(item, self.focus) for item in child.children]

                                return

                        except AttributeError:
                            continue

        except Exception as e:
            send_log(self.__class__.__name__, f"failed to focus input box: {constants.format_traceback(e)}", 'warning')

    def on_enter(self, value):

        foundry.new_server_info['server_settings']['seed'] = (self.text).strip()

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
        self.text = foundry.new_server_info['server_settings']['seed']
        self.bind(on_text_validate=self.on_enter)

        if foundry.new_server_info['server_settings']['world'] == "world":
            if constants.version_check(foundry.new_server_info['version'], '>=', "1.1"):
                self.halign = "left"
                Clock.schedule_once(functools.partial(self._on_focus, self, True), 0.0)
                Clock.schedule_once(functools.partial(self._on_focus, self, False), 0.0)


    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        super().keyboard_on_key_down(window, keycode, text, modifiers)

        # if constants.version_check(foundry.new_server_info['version'], '>=', "1.1"):
        #     if self.cursor_pos[0] > (self.x + self.width) - (self.width * 0.38):
        #         self.scroll_x += self.cursor_pos[0] - ((self.x + self.width) - (self.width * 0.38))

        if keycode[1] == "backspace":
            # Add seed to current config
            foundry.new_server_info['server_settings']['seed'] = (self.text).strip()

    # Input validation
    def insert_text(self, substring, from_undo=False):

        if not self.text and substring == " ":
            substring = ""

        elif len(self.text) < 32:
            if '\n' in substring:
                substring = substring.splitlines()[0]
            s = re.sub('[^a-zA-Z0-9 _/{}=+|"\'()*&^%$#@!?;:,.-]', '', substring)

            # Add name to current config
            def get_text(*a):
                foundry.new_server_info['server_settings']['seed'] = self.text.strip()
            Clock.schedule_once(get_text, 0)

            return super().insert_text(s, from_undo=from_undo)

class ServerSeedInput(BaseInput):

    # Hide input_button on focus
    def _on_focus(self, *args):
        try:
            super()._on_focus(*args)

            if constants.version_check(constants.server_manager.current_server.version, '>=', "1.1"):
                for child in self.parent.children:
                    for child_item in child.children:
                        try:
                            if "drop_button" in child_item.id:

                                # If box filled in and text box clicked
                                if self.focus and self.text:
                                    self.text = utility.screen_manager.current_screen.new_seed
                                    self.do_cursor_movement('cursor_end', True)
                                    Clock.schedule_once(functools.partial(self.do_cursor_movement, 'cursor_end', True), 0.01)
                                    Clock.schedule_once(functools.partial(self.select_text, 0), 0.01)

                                if not self.focus:
                                    # If text under button, cut it off temporarily
                                    self.scroll_x = 0
                                    self.cursor = (len(self.text), 0)
                                    if self.cursor_pos[0] > (self.x + self.width) - (self.width * 0.38):
                                        self.text = utility.screen_manager.current_screen.new_seed[:16] + "..."
                                    self.scroll_x = 0
                                    Clock.schedule_once(functools.partial(self.select_text, 0), 0.01)

                                [utility.hide_widget(item, self.focus) for item in child.children]

                                return

                        except AttributeError:
                            continue

        except Exception as e:
            send_log(self.__class__.__name__, f"failed to focus input box: {constants.format_traceback(e)}", 'warning')

    def on_enter(self, value):

        utility.screen_manager.current_screen.new_seed = (self.text).strip()

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
        self.text = utility.screen_manager.current_screen.new_seed
        self.bind(on_text_validate=self.on_enter)

        if utility.screen_manager.current_screen.new_world == "world":
            if constants.version_check(constants.server_manager.current_server.version, '>=', "1.1"):
                self.halign = "left"
                Clock.schedule_once(functools.partial(self._on_focus, self, True), 0.0)
                Clock.schedule_once(functools.partial(self._on_focus, self, False), 0.0)


    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        super().keyboard_on_key_down(window, keycode, text, modifiers)

        # if constants.version_check(constants.server_manager.current_server.version, '>=', "1.1"):
        #     if self.cursor_pos[0] > (self.x + self.width) - (self.width * 0.38):
        #         self.scroll_x += self.cursor_pos[0] - ((self.x + self.width) - (self.width * 0.38))

        if keycode[1] == "backspace":
            # Add seed to current config
            utility.screen_manager.current_screen.new_seed = (self.text).strip()

    # Input validation
    def insert_text(self, substring, from_undo=False):

        if not self.text and substring == " ":
            substring = ""

        elif len(self.text) < 32:
            if '\n' in substring:
                substring = substring.splitlines()[0]
            s = re.sub('[^a-zA-Z0-9 _/{}=+|"\'()*&^%$#@!?;:,.-]', '', substring)

            # Add name to current config
            def get_text(*a):
                utility.screen_manager.current_screen.new_seed = self.text.strip()
            Clock.schedule_once(get_text, 0)

            return super().insert_text(s, from_undo=from_undo)


class ServerImportPathInput(DirectoryInput):

    def get_server_list(self):
        try:
            telepath_data = foundry.new_server_info['_telepath_data']
            if telepath_data:
                self.server_list = constants.get_remote_var('server_manager.server_list_lower', telepath_data)
                return True
        except:
            pass
        self.server_list = constants.server_manager.server_list_lower

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

                        [utility.hide_widget(item, self.focus) for item in child.children]

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
        self.server_list = []
        self.get_server_list()

    def on_enter(self, value):
        self.selected_server = self.text.replace("~", paths.user_home)
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
            for item in utility.screen_manager.current_screen.next_button.children:
                try:
                    if item.id == "next_button":
                        item.disable(disable)
                        break
                except AttributeError:
                    pass

        self.scroll_x = 0

        if self.selected_server:
            self.get_server_list()

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
            elif paths.servers in self.selected_server and os.path.basename(self.selected_server).lower() in self.server_list:
                self.valid_text(False, "This server already exists!")
                disable_next(True)


            # If server is valid, do this
            else:
                foundry.import_data = {'name': re.sub('[^a-zA-Z0-9 _().-]', '', os.path.basename(self.selected_server).splitlines()[0])[:25], 'path': self.selected_server}
                box_text = os.path.join(*Path(os.path.abspath(self.selected_server)).parts[-2:])
                self.cache_text = self.text = box_text[:30] + "..." if len(box_text) > 30 else box_text
                self.valid_text(True, True)
                disable_next(False)

class ServerImportBackupInput(DirectoryInput):

    def get_server_list(self):
        try:
            telepath_data = foundry.new_server_info['_telepath_data']
            if telepath_data:
                self.server_list = constants.get_remote_var('server_manager.server_list_lower', telepath_data)
                return True
        except:
            pass
        self.server_list = constants.server_manager.server_list_lower

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

                        [utility.hide_widget(item, self.focus) for item in child.children]

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

        self.server_list = []
        self.get_server_list()

    def on_enter(self, value):
        self.selected_server = self.text.replace("~", paths.user_home)
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
            for item in utility.screen_manager.current_screen.next_button.children:
                try:
                    if item.id == "next_button":
                        item.disable(disable)
                        break
                except AttributeError:
                    pass

        self.scroll_x = 0

        if self.selected_server:
            self.get_server_list()
            self.selected_server = os.path.abspath(self.selected_server)

            # Extract auto-mcs.ini and server.properties
            file_failure = True
            server_name = None
            new_path = None
            test_path = paths.temp
            cwd = constants.get_cwd()
            if (self.selected_server.endswith(".tgz") or self.selected_server.endswith(".amb") and os.path.isfile(self.selected_server)):
                constants.folder_check(test_path)
                os.chdir(test_path)
                constants.run_proc(f'tar -xf "{self.selected_server}" auto-mcs.ini')
                constants.run_proc(f'tar -xf "{self.selected_server}" .auto-mcs.ini')
                constants.run_proc(f'tar -xf "{self.selected_server}" server.properties')
                if (os.path.exists(os.path.join(test_path, "auto-mcs.ini")) or os.path.exists(os.path.join(test_path, ".auto-mcs.ini"))) and os.path.exists(os.path.join(test_path, "server.properties")):
                    if os.path.exists(os.path.join(test_path, "auto-mcs.ini")):
                        new_path = os.path.join(test_path, "auto-mcs.ini")
                    elif os.path.exists(os.path.join(test_path, ".auto-mcs.ini")):
                        new_path = os.path.join(test_path, ".auto-mcs.ini")
                    if new_path:
                        try:
                            config_file = manager.server_config(server_name=None, config_path=new_path)
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
            elif server_name.lower() in self.server_list:
                self.valid_text(False, "This server already exists!")
                disable_next(True)


            # If server is valid, do this
            else:
                foundry.import_data = {'name': re.sub('[^a-zA-Z0-9 _().-]', '', server_name.splitlines()[0])[:25], 'path': self.selected_server}
                box_text = os.path.join(*Path(os.path.abspath(self.selected_server)).parts[-2:-1], server_name)
                self.cache_text = self.text = box_text[:30] + "..." if len(box_text) > 30 else box_text
                self.valid_text(True, True)
                disable_next(False)

class ServerImportModpackInput(DirectoryInput):

    # Hide input_button on focus
    def _on_focus(self, *args):
        super()._on_focus(*args)

        for child in self.parent.children:
            for child_item in child.children:
                try:
                    if child_item.id == "input_button":

                        if not self.text:
                            self.hint_text = "type a path..." if self.focused else "import from a file..."

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

                        [utility.hide_widget(item, self.focus) for item in child.children]

                        return

                except AttributeError:
                    continue

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.halign = "left"
        self.padding_x = 25
        self.size_hint_max = (528, 54)
        self.title_text = "modpack"
        self.hint_text = "import from a file..."
        self.cache_text = ""
        server = ""
        self.selected_server = None if server == '' else server
        self.server_verified = False
        self.update_server(hide_popup=True)

    def on_enter(self, value):
        self.selected_server = self.text.replace("~", paths.user_home)
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
            for item in utility.screen_manager.current_screen.next_button.children:
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

            if os.path.exists(self.selected_server) and (os.path.basename(self.selected_server).endswith('.zip') or os.path.basename(self.selected_server).endswith('.mrpack')):
                foundry.import_data = {'name': None, 'path': self.selected_server}
                box_text = os.path.join(*Path(os.path.abspath(self.selected_server)).parts[-2:-1], os.path.basename(self.selected_server))
                self.cache_text = self.text = box_text[:27] + "..." if len(box_text) > 30 else box_text
                self.valid_text(True, True)
                disable_next(False)

            else:

                if self.selected_server != os.path.abspath(os.curdir):
                    try:
                        self.selected_server = ''
                        if not force_ignore:
                            self.valid_text(False, False)
                        disable_next(True)
                    except AttributeError:
                        pass





class CreateServerPortInput(BaseInput):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.change_timeout = None
        self.size_hint_max = (445, 54)
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
            if '\n' in substring:
                substring = substring.splitlines()[0]
            s = re.sub('[^0-9:.]', '', substring)

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
            foundry.new_server_info['ip'], foundry.new_server_info['port'] = typed_info.split(":")[-2:]
        else:
            if "." in typed_info:
                foundry.new_server_info['ip'] = typed_info.replace(":", "")
                foundry.new_server_info['port'] = "25565"
            else:
                foundry.new_server_info['port'] = typed_info.replace(":", "")

        if not foundry.new_server_info['port']:
            foundry.new_server_info['port'] = "25565"

        # print("ip: " + foundry.new_server_info['ip'], "port: " + foundry.new_server_info['port'])

        # Input validation
        try:
            port_check = ((int(foundry.new_server_info['port']) < 1024) or (int(foundry.new_server_info['port']) > 65535))
        except ValueError:
            port_check = False
        ip_check = (constants.check_ip(foundry.new_server_info['ip']) and '.' in typed_info)
        self.stinky_text = ''

        if typed_info:

            if not ip_check and ("." in typed_info or ":" in typed_info):
                self.stinky_text = 'Invalid IPv4 address' if not port_check else 'Invalid IPv4 and port'

            elif port_check:
                self.stinky_text = ' Invalid port  (use 1024-65535)'

        else:
            foundry.new_server_info['ip'] = ''
            foundry.new_server_info['port'] = '25565'

        process_ip_text()
        self.valid(not self.stinky_text)

class ServerPortInput(CreateServerPortInput):
    _allow_ip = True

    def update_config(self, *a):
        def write(*a):
            server_obj = constants.server_manager.current_server
            server_obj.properties_hash = server_obj._get_properties_hash()
            try:
                utility.screen_manager.current_screen.check_changes(server_obj, force_banner=True)
            except AttributeError:
                pass
            server_obj.write_config()
            server_obj.reload_config()
            change_timeout = None

        if self.change_timeout:
            self.change_timeout.cancel()
        self.change_timeout = Clock.schedule_once(write, 0.7)

    def process_text(self, text=''):
        server_obj = constants.server_manager.current_server
        new_ip = ''
        default_port = "25565"
        new_port = default_port

        typed_info = text if text else self.text

        # interpret typed information
        if ":" in typed_info:
            new_ip, new_port = typed_info.split(":")[-2:]
        else:
            if "." in typed_info or not new_port:
                new_ip = typed_info.replace(":", "")
                new_port = default_port
            else:
                new_port = typed_info.replace(":", "")

        if not str(server_obj.port) or not new_port:
            new_port = default_port

        # Input validation
        try:
            port_check = ((int(new_port) < 1024) or (int(new_port) > 65535))
        except ValueError:
            port_check = False
        ip_check = (constants.check_ip(new_ip) and '.' in typed_info) and self._allow_ip
        self.stinky_text = ''
        fail = False

        if typed_info:

            if not ip_check and ("." in typed_info or ":" in typed_info):
                if not self._allow_ip:
                    self.stinky_text = "Can't use IP with proxy"
                else:
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
            server_obj.properties_hash = server_obj._get_properties_hash()
            try:
                utility.screen_manager.current_screen.check_changes(server_obj, force_banner=True)
            except AttributeError:
                pass

        if new_port and not fail:
            server_obj.port = int(new_port)
            server_obj.server_properties['server-port'] = new_port

        if (new_ip or new_port) and not fail:
            self.update_config()

        process_ip_text(server_obj=server_obj)
        self.valid(not self.stinky_text)



class CreateServerMOTDInput(BaseInput):

    def on_enter(self, value):

        foundry.new_server_info['server_settings']['motd'] = (self.text).strip() if self.text else "A Minecraft Server"

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

        self.size_hint_max = (445, 54)
        self.title_text = "MOTD"
        self.hint_text = "enter a message of the day..."
        self.text = foundry.new_server_info['server_settings']['motd'] if foundry.new_server_info['server_settings']['motd'] != "A Minecraft Server" else ""
        self.bind(on_text_validate=self.on_enter)

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        super().keyboard_on_key_down(window, keycode, text, modifiers)

        if keycode[1] == "backspace" and len(self.text):
            # Add name to current config
            foundry.new_server_info['server_settings']['motd'] = (self.text).strip() if self.text else "A Minecraft Server"


    # Input validation
    def insert_text(self, substring, from_undo=False):

        if not self.text and substring == " ":
            substring = ""

        elif len(self.text) < 32:
            if '\n' in substring:
                substring = substring.splitlines()[0]
            s = re.sub('[^a-zA-Z0-9 _/{}=+|"\'()*&^%$#@!?;:,.-]', '', substring)

            # Add name to current config
            def get_text(*a):
                foundry.new_server_info['server_settings']['motd'] = self.text.strip() if self.text else "A Minecraft Server"
            Clock.schedule_once(get_text, 0)

            return super().insert_text(s, from_undo=from_undo)

class ServerMOTDInput(BaseInput):

    def update_text(self, text):
        def write(*a):
            if self.screen_name == utility.screen_manager.current_screen.name:
                if text != self.server_obj.server_properties['motd'] and text:
                    self.server_obj.server_properties['motd'] = text
                    self.server_obj.properties_hash = self.server_obj._get_properties_hash()
                    utility.screen_manager.current_screen.check_changes(self.server_obj, force_banner=True)
                    self.server_obj.write_config()
                    self.server_obj.reload_config()
                    self.change_timeout = None

        if self.change_timeout:
            self.change_timeout.cancel()
        self.change_timeout = Clock.schedule_once(write, 0.5)

    def on_enter(self, value):
        self.update_text((self.text).strip() if self.text else "A Minecraft Server")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.change_timeout = None
        self.screen_name = utility.screen_manager.current_screen.name
        self.server_obj = constants.server_manager.current_server
        self.size_hint_max = (528, 54)
        self.title_text = "MOTD"
        self.hint_text = "enter a message of the day..."
        self.text = self.server_obj.server_properties['motd'] if self.server_obj.server_properties['motd'] != "A Minecraft Server" else ""
        self.bind(on_text_validate=self.on_enter)

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        super().keyboard_on_key_down(window, keycode, text, modifiers)

        if keycode[1] == "backspace":
            # Add name to current config
            self.update_text((self.text).strip() if self.text else "A Minecraft Server")


    # Input validation
    def insert_text(self, substring, from_undo=False):

        if not self.text and substring == " ":
            substring = ""

        elif len(self.text) < 32:
            if '\n' in substring:
                substring = substring.splitlines()[0]
            s = re.sub('[^a-zA-Z0-9 _/{}=+|"\'()*&^%$#@!?;:,.-]', '', substring)

            # Add name to current config
            def get_text(*a):
                self.update_text(self.text.strip() if self.text else "A Minecraft Server")
            Clock.schedule_once(get_text, 0)

            return super().insert_text(s, from_undo=from_undo)



class ServerPlayerInput(BaseInput):

    def on_enter(self, value):
        foundry.new_server_info['server_settings']['max_players'] = (self.text).strip() if self.text else "20"


    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.size_hint_max = (440, 54)
        self.title_text = " max players "
        self.hint_text = "max players  (20)"
        self.text = foundry.new_server_info['server_settings']['max_players'] if foundry.new_server_info['server_settings']['max_players'] != "20" else ""
        self.bind(on_text_validate=self.on_enter)

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        super().keyboard_on_key_down(window, keycode, text, modifiers)

        if keycode[1] == "backspace" and len(self.text):
            # Add name to current config
            foundry.new_server_info['server_settings']['max_players'] = (self.text).strip() if self.text else "20"

    # Input validation
    def insert_text(self, substring, from_undo=False):

        if not self.text and substring in [" ", "0"]:
            substring = ""

        elif len(self.text) < 7:
            if '\n' in substring:
                substring = substring.splitlines()[0]
            s = re.sub('[^0-9]', '', substring)

            # Add name to current config
            def get_text(*a):
                foundry.new_server_info['server_settings']['max_players'] = self.text.strip() if self.text else "20"
            Clock.schedule_once(get_text, 0)

            return super().insert_text(s, from_undo=from_undo)



class ServerTickSpeedInput(BaseInput):

    def on_enter(self, value):
        foundry.new_server_info['server_settings']['random_tick_speed'] = (self.text).strip() if self.text else "3"


    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.size_hint_max = (440, 54)
        self.title_text = "tick speed"
        self.hint_text = "random tick speed  (3)"
        self.text = foundry.new_server_info['server_settings']['random_tick_speed'] if foundry.new_server_info['server_settings']['random_tick_speed'] != "3" else ""
        self.bind(on_text_validate=self.on_enter)

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        super().keyboard_on_key_down(window, keycode, text, modifiers)

        if keycode[1] == "backspace" and len(self.text):
            # Add name to current config
            foundry.new_server_info['server_settings']['random_tick_speed'] = (self.text).strip() if self.text else "3"

    # Input validation
    def insert_text(self, substring, from_undo=False):

        if not self.text and substring in [" "]:
            substring = ""

        elif len(self.text) < 5:
            if '\n' in substring:
                substring = substring.splitlines()[0]
            s = re.sub('[^0-9]', '', substring)

            # Add name to current config
            def get_text(*a):
                foundry.new_server_info['server_settings']['random_tick_speed'] = self.text.strip() if self.text else "3"
            Clock.schedule_once(get_text, 0)

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

                        [utility.hide_widget(item, self.focus) for item in child.children]

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
            utility.screen_manager.current_screen.search_filter(self.actual_text)

    def insert_text(self, substring, from_undo=False):
        if not self.text and substring in [" "]:
            substring = ""

        else:
            if '\n' in substring:
                substring = substring.splitlines()[0]
            s = re.sub('[^a-zA-Z0-9 _().!/,-]', '', substring)

            # Filter input, and process data to search_filter function in AclScreen
            def get_text(*a):
                self.actual_text = self.text.strip() if self.text else ""
                utility.screen_manager.current_screen.search_filter(self.actual_text)
            Clock.schedule_once(get_text, 0)

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

            if utility.screen_manager.current_screen.current_list == "bans":
                reg_exp = '[^a-zA-Z0-9 _.,!/-]'
            else:
                reg_exp = '[^a-zA-Z0-9 _.,!]'

            if '\n' in substring:
                substring = substring.splitlines()[0]
            s = re.sub(reg_exp, '', substring)

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



class ServerFlagInput(BaseInput):

    def write_config(self, text):
        def write(*a):
            self.server_obj.update_flags(text)
            if self.screen_name == utility.screen_manager.current_screen.name:
                utility.screen_manager.current_screen.check_changes(self.server_obj, force_banner=True)

        if self.change_timeout:
            self.change_timeout.cancel()
        self.change_timeout = Clock.schedule_once(write, 0.5)


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.change_timeout = None
        self.screen_name = utility.screen_manager.current_screen.name
        self.server_obj = constants.server_manager.current_server
        self.size_hint_max = (528, 54)
        self.title_text = "flags"
        self.halign = "left"
        self.padding_x = 25
        self.hint_text = "enter custom launch flags..." if constants.app_config.locale == 'en' else 'launch flags...'

        if self.server_obj.custom_flags:
            self.text = self.server_obj.custom_flags

        self.bind(on_text_validate=self.on_enter)


    def on_enter(self, value):
        self.process_text()


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

        if not self.text and substring[0] not in ['-', '@', '<']:
            substring = ""

        elif len(self.text) < 5000:
            if '\n' in substring:
                substring = ' '.join(substring.splitlines())
            if len(substring) > 2:
                substring = substring.strip()
            s = substring

            # Add name to current config
            def process(*a):
                self.process_text(text=(self.text))
            Clock.schedule_once(process, 0)

            return super().insert_text(s, from_undo=from_undo)


    def process_text(self, text=''):

        typed_info = (text if text else self.text).strip()

        # Input validation
        flag_check = all([
            f.strip().startswith('-') or
            f.strip().startswith('@') or
            (f.strip().startswith('<java') and f.strip().endswith('>'))
            for f in typed_info.split(' ')
        ])
        space_check = re.search(r'(-\s|\w-\s|\d-| \s+|-+$)', typed_info, flags=re.IGNORECASE)
        memory_check = re.search(r'-xm(x|s)\d+(b|k|m|g|t)', typed_info, flags=re.IGNORECASE)
        self.stinky_text = ''

        if typed_info:

            if space_check or not flag_check:
                self.stinky_text = 'Invalid formatting'

            elif memory_check:
                self.stinky_text = '   Configure memory above'

            else:
                self.write_config(typed_info.strip())

        else:
            self.write_config('')


        self.valid(not self.stinky_text)



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



class HeaderBackground(Widget):

    y_offset = dp(62)

    def update_rect(self, *args):
        self.rect.size = self.size[0], self.y_offset
        self.rect.pos = (self.pos[0], round(Window.height) - self.rect.size[1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas.before:
            self.rect = Image(pos=self.pos, size=self.size, allow_stretch=True, keep_ratio=False, source=os.path.join(paths.ui_assets, 'header_background.png'))

        with self.canvas.after:
            self.canvas.clear()

        self.bind(pos=self.update_rect)
        self.bind(size=self.update_rect)



class FooterBackground(Widget):

    y_offset = dp(50)

    def update_rect(self, *args):
        self.rect.size = self.size[0], self.y_offset
        self.rect.pos = self.pos

    def __init__(self, no_background=False, **kwargs):
        super().__init__(**kwargs)

        if no_background:
            source = os.path.join(paths.ui_assets, 'no_background_footer.png')
            color = utility.screen_manager.current_screen.background_color
        else:
            source = os.path.join(paths.ui_assets, 'footer_background.png')
            color = self.background_color = constants.brighten_color(constants.background_color, -0.02)

        with self.canvas.before:
            self.rect = Image(pos=self.pos, size=self.size, allow_stretch=True, keep_ratio=False, source=source)
            self.rect.color = color

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
    label = AlignLabel(color=(0.2, 0.2, 0.4, 0.8), font_name=os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["very-bold"]}.ttf'), font_size=sp(25), size_hint=(1.0, 1.0), halign="center", valign="top")


    # Split title to check for server name before translation
    found_server = False
    if ":" in title:
        title_start, possible_server_name = title.split(':', 1)
        if possible_server_name.strip()[1:-1].lower() in constants.server_manager.server_list_lower:
            title = f"{translate(title_start)}:{possible_server_name}"
            found_server = True
    if not found_server:
        title = translate(title)


    label.__translate__ = False
    label.text = title
    text_layout.add_widget(label)

    header.add_widget(background)
    header.add_widget(text_layout)
    return header



def footer_label(path, color, progress_screen=False, full_version=False):

    # If remote server, put the instance name behind it
    if constants.server_manager.current_server:
        server_obj = constants.server_manager.current_server
        data = server_obj._telepath_data
        try:
            if data and path.strip().startswith(server_obj.name):
                path = f'[color=#353565]{data["display-name"]}/[/color]{path}'
        except:
            pass

    # Translate footer paths that don't include the server name
    t_path = []
    for i in path.split(', '):
        if '/' in i.lower():
            t_path.append(i)
        elif i.lower() in constants.server_manager.server_list_lower:
            t_path.append(i)
        else:
            t_path.append(translate(i))
    path = ', '.join(t_path)


    def fit_to_window(label_widget, path_string, *args):
        x = 1
        text = ""
        shrink_value = round(Window.width / 20)
        if len(path_list) > 2:
            shrink_value -= (len("".join(path_list[2:])))

        for item in path_list:
            item_no_tag = item.strip('[color=#353565]').replace('[/color]','')
            if x == 2 and len(item_no_tag) > shrink_value and len(path_list) > 2:
                item = item_no_tag
                item = item[:shrink_value - 4] + f"...{item[-1]}" if (item.endswith("'") or item.endswith("\"")) else item[:shrink_value - 5] + "..."

            text += f'[color={"555599" if x < len(path_list) else color}]' + item + '[/color]'
            if x < len(path_list):
                text += f"[size={round(sp(22))}][font={arrow_font}]  ▸  [/font][/size]"
            x += 1

        label.text = text

    arrow_font = os.path.join(paths.ui_assets, 'fonts', 'DejaVuSans.otf')

    path_list = path.split(', ')
    path_list.insert(0, "       ")

    final_layout = FloatLayout()

    text_layout = BoxLayout()
    text_layout.pos = (15, 12)
    version_layout = BoxLayout()
    search_layout = RelativeLayout()

    version_layout.pos = (-10 if progress_screen else -60, 13) # x=-10
    label = AlignLabel(color=(0.6, 0.6, 1, 0.2), font_name=os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["bold"]}.ttf'), font_size=sp(22), markup=True, size_hint=(1.0, 1.0), halign="left", valign="bottom")
    label.__translate__ = False
    version_text = f"{constants.app_version}{' (dev)' if constants.dev_version else ''}"
    version = AlignLabel(color=(0.6, 0.6, 1, 0.2), font_name=os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf'), font_size=sp(23), markup=True, size_hint=(1.0, 1.0), halign="right", valign="bottom")
    version.__translate__ = False

    if full_version: version.text = f"[size={round(sp(20))}]auto-mcs  {constants.format_version()}"
    else:            version.text = f"auto-mcs[size={round(sp(18))}]  [/size]v{version_text}"

    if constants.is_admin() and constants.bypass_admin_warning:
        version.text = f"[color=#FF8793]{version.text}[/color]"

    text_layout.bind(pos=functools.partial(fit_to_window, label, path_list))
    text_layout.bind(size=functools.partial(fit_to_window, label, path_list))

    text_layout.add_widget(label)
    version_layout.add_widget(version)

    final_layout.add_widget(text_layout)
    final_layout.add_widget(version_layout)

    if not progress_screen:
        search_button = IconButton('search', {}, (-40, 0), (None, None), 'global-search.png', clickable=True, text_offset=(30, 0), click_func=utility.screen_manager.current_screen.show_search)
        search_layout.add_widget(search_button)
        search_layout.pos_hint = {'center_x': 1}
        search_layout.size_hint_max = (50, 50)
        final_layout.add_widget(search_layout)

    return final_layout

def generate_footer(menu_path, color="9999FF", func_dict=None, progress_screen=False, no_background=False, full_version=False):

    # Sanitize footer path for crash logs to remove server name
    if ", Launch" in menu_path or ", Access Control" in menu_path or ", Back-ups" in menu_path or ", Add-ons" in menu_path or ", amscript" in menu_path or ", Settings" in menu_path:
        constants.footer_path = "Server Manager > " + " > ".join(menu_path.split(", ")[1:])
    elif menu_path.startswith('Create'):
        constants.footer_path = "Create new server"
    elif menu_path.startswith('Import'):
        constants.footer_path = "Import server"
    elif menu_path.split(", ")[0].count("'") == 2:
        constants.footer_path = menu_path.split(", ")[0].split("'")[0] + "Server" + " > ".join(menu_path.split(", ")[1:])
    else:
        constants.footer_path = " > ".join(menu_path.split(", "))
    constants.footer_path = constants.footer_path.replace('$', '')

    # Update Discord rich presence
    constants.discord_presence.update_presence(constants.footer_path)

    # Log menu change
    send_log('navigation', f"view: '{constants.footer_path}'")

    # Add time modified
    constants.footer_path += f" @ {constants.format_now()}"


    footer = FloatLayout()

    if menu_path == 'splash':
        constants.footer_path = 'Main Menu'

        if constants.app_online:
            footer.add_widget(IconButton('connected', {}, (0, 5), (None, None), 'wifi-sharp.png', clickable=False))

            if constants.app_latest:
                footer.add_widget(IconButton('up to date', {}, (51, 5), (None, None), 'checkmark-sharp.png', clickable=False))
            else:
                click_func = None
                try:
                    if func_dict: click_func = func_dict['update']
                except: pass
                footer.add_widget(IconButton('update now', {}, (51, 5), (None, None), 'sync.png', clickable=True, click_func=click_func, force_color=[[(0.05, 0.08, 0.07, 1), (0.5, 0.9, 0.7, 1)], 'green']))

            click_func = None
            try:
                if func_dict: click_func = func_dict['donate']
            except: pass
            footer.add_widget(IconButton('support us', {}, (102, 5), (None, None), 'sponsor.png', clickable=True, force_color=[[(0.05, 0.08, 0.07, 1), (0.6, 0.6, 1, 1)], 'pink'], click_func=click_func, text_hover_color=(0.85, 0.6, 0.95, 1)))

        else:
            footer.add_widget(IconButton('no connection', {}, (0, 5), (None, None), 'ban.png', clickable=True, force_color=[[(0.07, 0.07, 0.07, 1), (0.7, 0.7, 0.7, 1)], 'gray']))

        # Settings button
        def open_settings(*a): setattr(utility.screen_manager, 'current', 'AppSettingsScreen')
        settings_button = RelativeIconButton('settings', {'center_x': 1}, (0, 5), (None, None), 'settings-sharp.png', anchor='right', clickable=True, click_func=open_settings, anchor_text='right', text_offset=(-73, 40))
        settings_button.x = -35
        footer.add_widget(settings_button)

    else:
        footer.add_widget(FooterBackground(no_background=no_background))
        footer.add_widget(footer_label(path=menu_path, color=color, progress_screen=progress_screen, full_version=full_version)) # menu_path
        if not progress_screen:
            footer.add_widget(IconButton('main menu', {}, (-5, 0), (None, None), 'home-sharp.png', clickable=True))
        else:
            footer.add_widget(AnimButton('please wait...', {}, (0, 0), (None, None), 'loading_pickaxe.gif', clickable=False))

    return footer



def page_counter(index, total, pos):
    layout = FloatLayout()
    label = Label(halign="center")
    label.__translate__ = False
    label.size_hint = (None, None)
    label.pos_hint = {"center_x": 0.5, "center_y": pos[1] - 0.07}
    label.markup = True
    label.font_name = os.path.join(paths.ui_assets, 'fonts', 'DejaVuSans.otf')
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
        self.icon = os.path.join(paths.ui_assets, 'icons', f'caret-{"back" if facing == "left" else "forward"}-sharp.png')
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
            utility.hide_widget(self, False)

            if not (self.left_button.hovered or self.right_button.hovered):
                self.resize_self()

        else:
            utility.hide_widget(self, True)

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
        self.label.__translate__ = False
        self.label.size_hint = (None, None)
        self.label.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        self.label.markup = True
        self.label.font_name = os.path.join(paths.ui_assets, 'fonts', 'DejaVuSans.otf')
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

        self.rect.source = os.path.join(paths.ui_assets, f'text_input_cover_fade.png')

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
            self.background_top = Image(source=os.path.join(paths.ui_assets, "paragraph_edge.png"))
            self.background_top.allow_stretch = True
            self.background_top.keep_ratio = False

            # Body
            self.background = Image(source=os.path.join(paths.ui_assets, "paragraph_background.png"))
            self.background.allow_stretch = True
            self.background.keep_ratio = False

            # Top
            self.background_bottom = Image(source=os.path.join(paths.ui_assets, "paragraph_edge.png"))
            self.background_bottom.allow_stretch = True
            self.background_bottom.keep_ratio = False

            # Title
            self.rect = Image(size=(110, 15), color=constants.background_color, allow_stretch=True, keep_ratio=False)
            self.title = AlignLabel(halign="center", text=self.title_text, color=(0.6, 0.6, 1, 1), font_size=sp(17), font_name=os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["regular"]}.ttf'))
            self.bind(pos=self.update_rect)
            self.bind(size=self.update_rect)

            # Text content
            self.text_content = AlignLabel(halign="left", valign="top", color=(0.65, 0.65, 1, 1), font_name=font if font else os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["regular"]}.ttf'), markup=True)
            self.text_content.line_height = 1.3

def paragraph_object(size, name, content, font_size, font):
    paragraph_obj = ParagraphObject(font)
    paragraph_obj.pos_hint = {"center_x": 0.5} # , "center_y": 0.5
    paragraph_obj.width = size[0]
    paragraph_obj.height = size[1] + 10
    paragraph_obj.title_text = name
    paragraph_obj.text_content.__translate__ = False
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
        if touch.pos[0] > self.x + (self.width - self.drag_pad) and (self.y + self.height > touch.pos[1] > self.y):
            try:
                new_scroll = ((touch.pos[1] - self.y) / (self.height - (self.height * (self.vbar[1])))) - (self.vbar[1])
                self.scroll_y = 1 if new_scroll > 1 else 0 if new_scroll < 0 else new_scroll
                return True
            except ZeroDivisionError:
                pass
        return super().on_touch_move(touch)

    def on_touch_down(self, touch, *args):
        if touch.pos[0] > self.x + (self.width - self.drag_pad) and (self.y + self.height > touch.pos[1] > self.y):
            try:
                new_scroll = ((touch.pos[1] - self.y) / (self.height - (self.height * (self.vbar[1])))) - (self.vbar[1])
                self.scroll_y = 1 if new_scroll > 1 else 0 if new_scroll < 0 else new_scroll
                return True
            except ZeroDivisionError:
                pass
        return super().on_touch_down(touch)

class ScrollItem(RelativeLayout):
    def __init__(self, widget=None, **kwargs):
        super().__init__(**kwargs)
        self.height = 85
        self.size_hint_y = None

        if widget:
            self.add_widget(widget)

def scroll_background(pos_hint, pos, size, highlight=False, color=None):

    class ScrollBackground(Image):

        def resize(self, *args):
            self.width = Window.width-20

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.allow_stretch = True
            self.keep_ratio = False
            self.size_hint = (None, None)
            if color:
                self.color = color
            else:
                self.color = (1, 1, 1, 1) if highlight else constants.background_color
            self.source = os.path.join(paths.ui_assets, 'scroll_gradient.png')
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


    def __init__(self, pos_hint={"center_x": 0.5, "center_y": 0.5}, size=(200,50), color=(1,1,1,1), text="", icon=None, icon_side="left", animate=False, __translate__=True, **kwargs):
        super().__init__(**kwargs)

        self.size = size
        self.size_hint_max = size
        self.pos_hint = pos_hint
        self.icon_side = icon_side


        # Text
        self.text_object = Label()
        self.text_object.__translate__ = __translate__
        self.text_object.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
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
        self.left_side.source = os.path.join(paths.ui_assets, "banner_edge.png")
        self.left_side.color = color
        self.left_side.allow_stretch = True
        self.left_side.keep_ratio = False
        self.left_side.size_hint = (None, None)
        self.left_side.height = size[1]
        self.left_side.width = (size[1] / 2.2)

        # Middle stretched image
        self.middle = Image()
        self.middle.source = os.path.join(paths.ui_assets, "banner_middle.png")
        self.middle.color = color
        self.middle.allow_stretch = True
        self.middle.keep_ratio = False
        self.middle.size_hint = (None, None)
        self.middle.height = size[1]
        self.middle.width = size[0] - ((size[1] / 2.2) * 2)

        # Right side
        self.right_side = Image()
        self.right_side.source = os.path.join(paths.ui_assets, "banner_edge.png")
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
            self.icon.source = os.path.join(paths.ui_assets, 'icons', icon)
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
            if position[0] >= 0.5:
                text = name.upper() + (int(round(len(translated)*.7))*' ')
            else:
                text = (int(round(len(translated)*.7))*' ') + name.upper()
        elif len(translated) > 28:
            text = (int(round(len(translated)*.2))*' ') + name.upper()
        else:
            text = name.upper()
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

        if auto_adjust_icon and icon_name:
            Clock.schedule_once(self.repos_icon, 0)

        if click_func:
            self.button.bind(on_press=click_func)



def color_button(name, position, icon_name=None, width=None, icon_offset=None, auto_adjust_icon=False, click_func=None, color=(1, 1, 1, 1), disabled=False, hover_data={'color': None, 'image': None}):

    def repos_icon(icon_widget, button_widget, *args):

        def resize(*args):
            pos_calc = ((button_widget.width/2 - 35) if button_widget.center[0] > 0 else (-button_widget.width/2 + 35))
            icon_widget.center[0] = button_widget.center[0] + pos_calc

        Clock.schedule_once(resize, 0)

    final = FloatLayout()
    final.id = name

    class ColorButton(HoverButton):
        def on_enter(self, *args):
            if not self.ignore_hover:
                if hover_data['color'] or hover_data['image']:
                    animate_button(self, image=hover_data['image'], color=hover_data['color'], hover_action=True)
                else:
                    super().on_enter(*args)

    final.button = ColorButton()
    final.button.id = 'color_button'
    final.button.color_id = [constants.brighten_color(color, -0.9), color]

    final.button.size_hint = (None, None)
    final.button.size = (dp(450 if not width else width), dp(72))
    final.button.pos_hint = {"center_x": position[0], "center_y": position[1]}
    final.button.border = (30, 30, 30, 30)
    final.button.background_normal = os.path.join(paths.ui_assets, 'color_button.png')
    final.button.background_down = os.path.join(paths.ui_assets, 'color_button_click.png') if not disabled else final.button.background_normal
    final.button.background_disabled_normal = os.path.join(paths.ui_assets, 'color_button.png')
    final.button.background_disabled_down = os.path.join(paths.ui_assets, 'color_button_click.png')
    final.button.background_color = final.button.color_id[1]

    text = Label()
    text.id = 'text'
    text.size_hint = (None, None)
    text.pos_hint = {"center_x": position[0], "center_y": position[1]}
    text.text = name.upper()
    text.font_size = sp(19)
    text.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["bold"]}.ttf')
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
        if disabled:
            icon.opacity = 0
        final.add_widget(icon)

    final.add_widget(text)

    if auto_adjust_icon and icon_name:
        Clock.schedule_once(functools.partial(repos_icon, icon, final.button), 0)

    if click_func and not disabled:
        final.button.bind(on_press=click_func)

    final.button.ignore_hover = disabled
    if disabled:
        final.opacity = 0.4
        final.button.opacity = 0.5

    return final


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
        previously_disabled  = self.button.disabled
        self.button.disabled = disable
        duration = (0.12 if animate else 0)

        def _animate(*_):
            if (disable) or (not disable and not self.button.hovered):
                Animation(color=(0.6, 0.6, 1, 0.4) if self.button.disabled else (0.6, 0.6, 1, 1), duration=duration).start(self.text)
                Animation(color=(0.6, 0.6, 1, 0) if self.button.disabled else (0.6, 0.6, 1, 1), duration=duration).start(self.icon)
            elif previously_disabled and (not disable and self.button.hovered): self.button.on_enter()
        Clock.schedule_once(_animate, -1)

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

        if auto_adjust_icon and icon_name:
            Clock.schedule_once(self.repos_icon, 0)

        if click_func:
            self.button.bind(on_press=click_func)

        if disabled:
            self.disable(True, False)

        if start_loading:
            self.loading(True)



class IconButton(FloatLayout):

    def change_data(self, icon=None, text=None, click_func=None):
        if icon:
            self.icon.source = icon_path(icon)

        if text:
            self.text.text = text.lower()

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

        if force_color and force_color[1]:
            self.button.alt_color = "_" + force_color[1]

        self.button.size_hint = size_hint
        self.button.size = (dp(50), dp(50))
        self.button.pos_hint = pos_hint

        if position:
            self.button.pos = (position[0] + 11, position[1])

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

        if position:
            self.text.pos = (position[0] - 10, position[1] + 17)

        if self.text.pos[0] <= 0:
            self.text.pos[0] += sp(len(self.text.text) * 3)

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

            if position:
                self.icon.pos = (position[0], position[1] - 11)

            self.add_widget(self.icon)

        self.add_widget(self.text)

        # Check for right float
        if anchor == "right":
            self.bind(size=self.resize)
            self.bind(pos=self.resize)

class RelativeIconButton(RelativeLayout):

    def change_data(self, icon=None, text=None, click_func=None):
        if icon:
            self.icon.source = icon_path(icon)

        if text:
            self.text.text = text.lower()

        if click_func:
            def _check_disabled():
                if not self.disabled and not self.button.disabled: click_func()
            self.button.on_release = functools.partial(_check_disabled)

    def resize(self, *args):
        self.text.x = Window.width - self.text.texture_size[0] + 25
        if self.text_offset:
            self.text.x += self.text_offset[0]

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

        if force_color and force_color[1]:
            self.button.alt_color = "_" + force_color[1]

        self.button.size_hint = size_hint
        self.button.size = (dp(50), dp(50))
        self.button.pos_hint = pos_hint

        if position:
            self.button.pos = (position[0] + 11, position[1])

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
        if pos_hint and not anchor_text:
            self.text.pos_hint = pos_hint
        self.text.text = name.lower()
        self.text.hover_color = text_hover_color if text_hover_color else None
        self.text.font_size = sp(19)
        self.text.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
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

        if anchor_text == "right":
            self.bind(size=self.resize)
            self.bind(pos=self.resize)

        if utility.screen_manager.current_screen.name == 'MainMenuScreen':
            Clock.schedule_once(self.text.texture_update, 0)
            Clock.schedule_once(self.resize, 0)

        # Hover hook
        self.button.bind(on_enter=lambda *_: self.on_hover(True))
        self.button.bind(on_leave=lambda *_: self.on_hover(False))

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

    def __init__(self, name, pos_hint, position, size_hint, icon_name=None, clickable=True, force_color=None, anchor='left', click_func=None, text_hover_color=None, **kwargs):
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

        if position:
            self.text.pos = (position[0] - 10, position[1] + 17)

        if self.text.pos[0] <= 0:
            self.text.pos[0] += sp(len(self.text.text) * 3)

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
            if child.type == self.type:
                self.on_leave(duration=0)
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


def big_mode_button(name, pos_hint, position, size_hint, icon_name=None, clickable=True, force_color=None, text_hover_color=None, click_func=None):

    final = RelativeLayout()
    final.size_hint_max_y = dp(150)
    final.pos_hint = {'center_y': 0.5, 'center_x': 0.5}
    final.anchor_x = 'center'

    button = BigIcon()
    button.id = 'big_icon_button'
    button.color_id = [(0.47, 0.52, 1, 1), (0.6, 0.6, 1, 1)] if not force_color else force_color[0]
    button.type = icon_name

    if force_color: button.alt_color = "_" + force_color[1]

    button.size_hint = size_hint
    button.size = (dp(150), dp(150))
    button.pos_hint = pos_hint

    if position: button.pos = (position[0] + 11, position[1])

    button.border = (0, 0, 0, 0)
    button.background_normal = os.path.join(paths.ui_assets, f'{button.id}.png')

    if not force_color:
        if button.selected: button.background_down = os.path.join(paths.ui_assets, f'{button.id}_selected.png')
        else:               button.background_down = os.path.join(paths.ui_assets, f'{button.id}_click.png' if clickable else f'{button.id}_hover.png')

    else: button.background_down = os.path.join(paths.ui_assets, f'{button.id}_click_{force_color[1]}.png' if clickable else f'{button.id}_hover_{force_color[1]}.png')

    text = Label()
    text.id = 'text'
    text.size_hint = size_hint
    text.pos_hint = {'center_x': pos_hint['center_x'], 'center_y': pos_hint['center_y'] - 0.11}
    text.text = name.lower()
    text.hover_color = text_hover_color if text_hover_color else None
    text.font_size = sp(19)
    text.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
    text.color = (0, 0, 0, 0)

    if position: text.pos = (position[0] - 10, position[1] - 17)

    if text.pos[0] <= 0: text.pos[0] += sp(len(text.text) * 3)


    # Button click behavior
    if clickable and click_func: button.on_release = functools.partial(click_func)


    final.add_widget(button)

    if icon_name:
        icon = Image()
        icon.id = 'icon'
        icon.type = button.type
        icon.size_hint = size_hint
        icon.source = icon_path(os.path.join('big', 'modes', f'{icon_name}.png'))
        icon.size = (dp(125), dp(125))
        icon.color = button.color_id[1]
        icon.pos_hint = {'center_x': pos_hint['center_x'], 'center_y': pos_hint['center_y'] + 0.005}

        if position: icon.pos = (position[0], position[1] - 11)

        final.add_widget(icon)


        icon_text = Label()
        icon_text.id = 'icon'
        icon_text.size_hint_max = (130, 120)
        icon_text.text_size = (130, 120)
        icon_text.halign = 'center'
        icon_text.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        icon_text.text = icon_name.lower()
        icon_text.font_size = sp(23)
        icon_text.font_name = os.path.join(paths.ui_assets, 'fonts', 'CenturyGothic.ttf')
        icon_text.color = (0.6, 0.6, 1, 1)

        final.add_widget(icon_text)

    final.add_widget(text)

    return final


def big_icon_button(name, pos_hint, position, size_hint, icon_name=None, clickable=True, force_color=None, selected=False, text_hover_color=None):

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
    button.background_normal = os.path.join(paths.ui_assets, f'{button.id}{"_selected" if selected else ""}.png')

    if not force_color:
        if button.selected:
            button.background_down = os.path.join(paths.ui_assets, f'{button.id}_selected.png')
        else:
            button.background_down = os.path.join(paths.ui_assets, f'{button.id}_click.png' if clickable else f'{button.id}_hover.png')
    else:
        button.background_down = os.path.join(paths.ui_assets, f'{button.id}_click_{force_color[1]}.png' if clickable else f'{button.id}_hover_{force_color[1]}.png')

    text = Label()
    text.id = 'text'
    text.size_hint = size_hint
    text.pos_hint = {'center_x': pos_hint['center_x'], 'center_y': pos_hint['center_y'] - 0.11}
    text.text = name.lower()
    text.hover_color = text_hover_color if text_hover_color else None
    text.font_size = sp(19)
    text.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
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
        if len(translated) == len(name):
            text = name.upper()
        else:
            text = (int(round(len(translated)*.7))*' ') + name.upper()
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
            if self.custom_func:
                self.custom_func()
            else:
                button_action(name, self.button)

        self.button.on_release = execute


        self.add_widget(self.button)
        self.add_widget(self.icon)
        self.add_widget(self.text)



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

    def update_next(self, boolean_value, message, *a):

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
                if constants.version_check(child.text, "<", "1.13.2") or foundry.new_server_info['type'] not in ['spigot', 'paper', 'purpur', 'fabric', 'quilt', 'neoforge']:
                    foundry.new_server_info['server_settings']['geyser_support'] = False

                # Reset gamerule settings if version is less than 1.4.2
                if constants.version_check(child.text, "<", "1.4.2"):
                    foundry.new_server_info['server_settings']['keep_inventory'] = False
                    foundry.new_server_info['server_settings']['daylight_weather_cycle'] = True
                    foundry.new_server_info['server_settings']['command_blocks'] = False
                    foundry.new_server_info['server_settings']['random_tick_speed'] = "3"

                # Reset level_type if level type not supported
                if constants.version_check(child.text, "<", "1.1"):
                    foundry.new_server_info['server_settings']['level_type'] = "default"
                elif constants.version_check(child.text, "<", "1.3.1") and foundry.new_server_info['server_settings']['level_type'] not in ['default', 'flat']:
                    foundry.new_server_info['server_settings']['level_type'] = "default"
                elif constants.version_check(child.text, "<", "1.7.2") and foundry.new_server_info['server_settings']['level_type'] not in ['default', 'flat', 'large_biomes']:
                    foundry.new_server_info['server_settings']['level_type'] = "default"

                # Disable chat reporting
                if constants.version_check(child.text, "<", "1.19") or foundry.new_server_info['type'] == "vanilla":
                    foundry.new_server_info['server_settings']['disable_chat_reporting'] = False
                else:
                    foundry.new_server_info['server_settings']['disable_chat_reporting'] = True

                # Check for potential world incompatibilities
                if foundry.new_server_info['server_settings']['world'] != "world":
                    check_world = constants.check_world_version(foundry.new_server_info['server_settings']['world'], foundry.new_server_info['version'])
                    if not check_world[0] and check_world[1]:
                        foundry.new_server_info['server_settings']['world'] = "world"

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
    button.background_normal = os.path.join(paths.ui_assets, 'next_button.png')
    button.background_down = os.path.join(paths.ui_assets, 'next_button_click.png')
    button.background_disabled_normal = os.path.join(paths.ui_assets, 'next_button_disabled.png')
    button.background_disabled_down = os.path.join(paths.ui_assets, 'next_button_disabled.png')

    text = Label()
    text.id = 'text'
    text.size_hint = (None, None)
    text.pos_hint = {"center_x": position[0], "center_y": position[1]}
    text.text = name.upper()
    text.font_size = sp(19)
    text.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["bold"]}.ttf')
    text.color = (0.6, 0.6, 1, 0.4) if disabled else (0.6, 0.6, 1, 1)

    # Button click behavior
    if not click_func:
        button.on_release = functools.partial(button_action, name, button, next_screen)

    icon = Image()
    icon.id = 'icon'
    icon.source = icon_path('next-stylized.png')
    icon.size = (dp(1), dp(1))
    icon.color = (0.6, 0.6, 1, 0) if disabled else (0.6, 0.6, 1, 1)
    icon.pos_hint = {"center_y": position[1]}
    icon.pos = (-90, 200)

    if show_load_icon:
        load_icon = AsyncImage()
        load_icon.id = 'load_icon'
        load_icon.source = os.path.join(paths.ui_assets, 'animations', 'loading_pickaxe.gif')
        load_icon.size_hint_max_y = 40
        load_icon.color = (0.6, 0.6, 1, 0)
        load_icon.pos_hint = {"center_y": position[1]}
        load_icon.pos = (-87, 200)
        load_icon.allow_stretch = True
        load_icon.anim_delay = utility.anim_speed * 0.02
        final.add_widget(load_icon)

    final.add_widget(button)
    final.add_widget(icon)

    final.add_widget(text)

    return final


class HeaderText(FloatLayout):

    def __init__(self, display_text, more_text, position, fixed_x=False, no_line=False, __translate__ = (True, True), **kwargs):
        super().__init__(**kwargs)

        self.text = Label()
        self.text.__translate__ = __translate__[0]
        self.text.id = 'text'
        self.text.size_hint = (None, None)
        self.text.markup = True
        if not fixed_x:
            self.text.pos_hint = {"center_x": 0.5, "center_y": position[1]}
        else:
            self.text.pos_hint = {"center_y": position[1]}
        self.text.text = display_text
        self.text.font_size = sp(23)
        self.text.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
        self.text.color = (0.6, 0.6, 1, 1)

        self.lower_text = Label()
        self.lower_text.__translate__ = __translate__[1]
        self.lower_text.id = 'lower_text'
        self.lower_text.size_hint = (None, None)
        self.lower_text.markup = True
        self.lower_text.pos_hint = {"center_x": 0.5, "center_y": position[1] - 0.07}
        self.lower_text.text = more_text
        self.lower_text.font_size = sp(19)
        self.lower_text.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
        self.lower_text.color = (0.6, 0.6, 1, 0.6)

        self.separator = Label(pos_hint={"center_y": position[1] - 0.025}, color=(0.6, 0.6, 1, 0.1), font_name=os.path.join(paths.ui_assets, 'fonts', 'LLBI.otf'), font_size=sp(25))
        self.separator.__translate__ = False
        self.separator.text = "_" * 48
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
    button.background_normal = os.path.join(paths.ui_assets, 'input_button.png')
    button.background_down = os.path.join(paths.ui_assets, 'input_button_click.png')

    text = Label()
    text.id = 'text'
    text.size_hint = (None, None)
    text.pos_hint = {"center_x": position[0], "center_y": position[1]}
    text.text = name.upper()
    text.font_size = sp(17)
    text.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["bold"]}.ttf')
    text.color = (0.6, 0.6, 1, 1)

    # Button click behavior
    if file:
        button.on_release = functools.partial(file_popup, file[0], file[1], ext_list, input_name, title=title)
    else:
        button.on_release = functools.partial(button_action, name, button)

    final.add_widget(button)
    final.add_widget(text)

    return final


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
    def cols(self):
        return self._grid.cols
    @cols.setter
    def cols(self, v):
        self._grid.cols = v

    @property
    def spacing(self):
        return self._grid.spacing
    @spacing.setter
    def spacing(self, v):
        self._grid.spacing = v

    @property
    def minimum_height(self):
        return self._grid.minimum_height
    @property
    def minimum_width(self):
        return self._grid.minimum_width

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
        if options_list:
            self._change_options(options_list)
        self.visible = True
        self.play_sound()

        def wait(*a):
            self._update_pos()
            Animation(opacity=1, size_hint_max_x=200, duration=0.13, transition='in_out_sine').start(self)
            for x, b in enumerate(reversed(self._grid.children), 0):
                b.animate(True, (math.log(x + 1) / math.log(1.17)) / 70)
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
            for b in self._grid.children:
                b.animate(False)
            Clock.schedule_once(functools.partial(self._deselect_buttons), 0.14)
            Clock.schedule_once(delete, 0.141)
        else:
            delete()

    def _deselect_buttons(self, *args):
        for child in self._grid.children:
            child.button.on_leave()

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


# ToggleButton override to ignore clicks when there's a popup
class ToggleButton(ToggleButton):
    def on_touch_down(self, touch):
        if not utility.screen_manager.current_screen.popup_widget: return super().on_touch_down(touch)

def toggle_button(name, position, default_state=True, x_offset=0, custom_func=None, disabled=False):

    knob_limits = (156.4 + x_offset, 193 + x_offset) # (Left, Right) (156.7 on left, 191 on right with border)
    bgc = constants.background_color
    color_id = [(bgc[0] - 0.021, bgc[1] - 0.021, bgc[2] - 0.021, bgc[3]), (0.6, 0.6, 1, 1)]

    # When switch is toggled
    def on_active(button_name, *args):
        if disabled or utility.screen_manager.current_screen.popup_widget:
            return

        # Log for crash info
        try:
            interaction = "ToggleButton"
            if name: interaction += f" ({name})"
            constants.last_widget = interaction + f" @ {constants.format_now()}"
            send_log('navigation', f"interaction: '{interaction}'")
        except: pass

        state = args[0].state == "down"

        if custom_func: custom_func(state)

        # Change settings of ID
        elif button_name == "geyser_support":
            foundry.new_server_info['server_settings']['geyser_support'] = state
        elif button_name == 'chat_report':
            foundry.new_server_info['server_settings']['disable_chat_reporting'] = state
        elif button_name == "pvp":
            foundry.new_server_info['server_settings']['pvp'] = state
        elif button_name == "spawn_protection":
            foundry.new_server_info['server_settings']['spawn_protection'] = state
        elif button_name == "keep_inventory":
            foundry.new_server_info['server_settings']['keep_inventory'] = state
        elif button_name == "daylight_weather_cycle":
            foundry.new_server_info['server_settings']['daylight_weather_cycle'] = state
        elif button_name == "spawn_creatures":
            foundry.new_server_info['server_settings']['spawn_creatures'] = state
        elif button_name == "command_blocks":
            foundry.new_server_info['server_settings']['command_blocks'] = state


        # Play sassy sounds
        file_name = f'toggle_{"on" if state else "off"}'
        audio.player.play(f'interaction/{file_name}', jitter=(0, 0.125))

        # Animate sassy animations
        for child in args[0].parent.children:
            if child.id == "knob":
                Animation(x=knob_limits[1] if state else knob_limits[0], color=color_id[0] if state else color_id[1], duration=0.12).start(child)
                child.source = os.path.join(paths.ui_assets, f'toggle_button_knob{"_enabled" if state else ""}.png')

    final = FloatLayout()
    final.x += 174 + x_offset

    final.button = button = ToggleButton(state='down' if default_state else 'normal')
    button.id = 'toggle_button'
    button.pos_hint = {"center_x": position[0], "center_y": position[1]}
    button.size_hint_max = (82, 42)
    button.border = (0, 0, 0, 0)
    button.background_normal = os.path.join(paths.ui_assets, 'toggle_button.png')
    button.background_down = button.background_normal if disabled else os.path.join(paths.ui_assets, 'toggle_button_enabled.png')
    button.bind(on_press=functools.partial(on_active, name))

    final.knob = knob = Image()
    knob.id = 'knob'
    knob.source = os.path.join(paths.ui_assets, f'toggle_button_knob{"_enabled" if default_state else ""}.png')
    knob.size = (30, 30)
    knob.pos_hint = {"center_y": position[1]}
    knob.x = knob_limits[1] if default_state else knob_limits[0]
    knob.color = color_id[0] if default_state else color_id[1]

    if disabled: final.opacity = 0.4

    final.add_widget(button)
    final.add_widget(knob)
    return final


class NumberSlider(FloatLayout):

    class InternalSlider(Slider):
        def __init__(self, parent, sound, **kwargs):
            super().__init__(**kwargs)
            self._parent = parent
            self._sound  = sound
            self._invalid_buttons = ('scrollleft', 'scrollright', 'scrollup', 'scrolldown')

            # Cache last touch to reject repeat events
            self._last_touch = None

        def _pulse(self, *a):
            x = self.value_pos[0]
            y = self.center_y

            r0 = 16
            r1 = 22
            a0 = 0.4
            a1 = 0.0
            d  = 0.25
            width = 1.6

            ig = InstructionGroup()
            col = Color(0.8, 0.8, 1, a0)
            ln = Line(circle=(x, y, r0), width=width)

            ig.add(col)
            ig.add(ln)
            self.canvas.after.add(ig)

            t0 = [0.0]

            def step(dt):
                t0[0] += dt
                t = min(1, t0[0] / d)

                r = r0 + (r1 - r0) * t
                a = a0 + (a1 - a0) * t
                col.a = a
                ln.circle = (x, y, r)
                if t >= 1.0:
                    self.canvas.after.remove(ig)
                    return False

            Clock.schedule_interval(step, 0)

        def on_touch_down(self, touch):
            if not self.disabled:
                if not self._parent.init and touch.button not in self._invalid_buttons and self._parent.collide_point(*touch.pos):
                    audio.player.play('interaction/click_*', jitter=(0, 0.15))

            return Slider.on_touch_down(self, touch)

        def on_touch_up(self, touch):
            if not self.disabled and touch != self._last_touch:

                # Execute function with value if it's added
                if self._parent.function and not self._parent.init and touch.button not in self._invalid_buttons and self._parent.collide_point(*touch.pos):
                    self._last_touch = touch

                    self._parent.function(self._parent.slider_val)
                    audio.player.play(self._sound['file'], **self._sound.get('kwargs', {}))
                    self._pulse()

                    # Log for crash info
                    try:
                        interaction = "NumberSlider"
                        if self._parent.input_name: interaction += f" ({self._parent.input_name})"
                        constants.last_widget = interaction + f" @ {constants.format_now()}"
                        send_log('navigation', f"interaction: '{interaction}'")
                    except:
                        pass

                    return True

            return Slider.on_touch_up(self, touch)

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

            # Show icons at min/max if specified
            show_icon = False

            if self.max_icon and self.slider_val == self.slider.range[1]:
                self.icon_widget.source = os.path.join(paths.ui_assets, 'icons', self.max_icon)
                show_icon = True

            elif self.min_icon and self.slider_val == self.slider.range[0]:
                self.icon_widget.source = os.path.join(paths.ui_assets, 'icons', self.min_icon)
                show_icon = True

            self.icon_widget.opacity = 1 if show_icon else 0
            self.label.opacity = 0 if show_icon else 1


        self.last_val = self.slider_val
        self.init = False

    def __init__(self, default_value, position, input_name, limits=(0, 100), max_icon=None, min_icon=None, function=None, sound: dict = None, **kwargs):
        super().__init__(**kwargs)
        self._input_name = input_name

        self.x += 125
        self.function = function
        self.last_val = default_value
        self.slider_val = default_value
        self.init = True
        self.max_icon = max_icon
        self.min_icon = min_icon

        # Main slider widget
        if not sound: sound = {'file': 'interaction/gear_*', 'kwargs': {'jitter': (-0.3, 0.05), 'volume': 0.4}}
        self.slider = self.InternalSlider(self, value=default_value, value_track=True, range=limits, sound=sound)
        self.slider.background_width = 12
        self.slider.border_horizontal = [6, 6, 6, 6]
        self.slider.value_track_width = 5
        self.slider.value_track_color = (0.6, 0.6, 1, 1)
        self.slider.cursor_size = (42, 42)
        self.slider.cursor_image = os.path.join(paths.ui_assets, 'slider_knob.png')
        self.slider.background_horizontal = os.path.join(paths.ui_assets, 'slider_rail.png')
        self.slider.size_hint_max_x = 205
        self.slider.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        self.slider.padding = 30
        self.add_widget(self.slider)

        # Number label
        self.label = AlignLabel()
        self.label.text = str(default_value)
        self.label.halign = "center"
        self.label.valign = "center"
        self.label.size_hint_max = (30, 28)
        self.label.color = (0.15, 0.15, 0.3, 1)
        self.label.font_size = sp(20)
        self.label.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["very-bold"]}.ttf')
        self.add_widget(self.label)

        # Icon labels
        if self.max_icon or self.min_icon:
            self.icon_widget = Image()
            self.icon_widget.size_hint_max = (28, 28)
            self.icon_widget.color = (0.15, 0.15, 0.3, 1)
            self.icon_widget.opacity = 0
            self.add_widget(self.icon_widget)


        # Bind to number change
        self.slider.bind(value=self.on_value, pos=self.on_value)
        Clock.schedule_once(self.on_value, 0)


# ---------------------------------------------------- Screens ---------------------------------------------------------

# Popup widgets
popup_blur_amount = 7       # 0-10 int:   Higher is blurrier  (originally 5)
popup_blur_darkness = 0.9   # 0-1 float:  Lower is darker
class PopupWindow(RelativeLayout):
    @staticmethod
    def click_sound(): audio.player.play('interaction/click_*', jitter=(0, 0.15))

    def generate_blur_background(self, *args):
        image_path = os.path.join(paths.ui_assets, 'live', 'blur_background.png')
        try: constants.folder_check(os.path.join(paths.ui_assets, 'live'))
        except:
            self.blur_background.color = constants.background_color
            return

        # Prevent this from running every resize
        def reset_activity(*args):
            self.generating_background = False

        if not self.generating_background:
            self.generating_background = True

            if self.shown:
                for widget in self.window.children:
                    widget.opacity = 0
                self.blur_background.opacity = 0

            utility.screen_manager.current_screen.export_to_png(image_path)
            im = PILImage.open(image_path)
            im = ImageEnhance.Brightness(im)
            im = im.enhance(popup_blur_darkness)
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

        button_pressed = 'ignore'
        try: button_pressed = args[1].button
        except: pass

        if not self.clicked and button_pressed in ('left', 'ignore'):

            if isinstance(args[1], str):
                force_button = args[1]
                rel_coord = (0, Window.height)
            else:
                force_button = None
                rel_coord = (args[1].pos[0] - self.x - self.window.x, args[1].pos[1] - self.y - self.window.y)

            rel_color = self.window_background.color

            # Single, wide button
            if self.ok_button:
                if (force_button in ('ok', 'yes')) or (not force_button and (rel_coord[0] < self.ok_button.width and rel_coord[1] < self.ok_button.height)):
                    self.ok_button.background_color = tuple([px + 0.12 if px < 0.88 else px for px in rel_color])
                    self.resize_window()

                    if self.callback:
                        self.callback()
                        self.clicked = True

                    self.click_sound()
                    Clock.schedule_once(functools.partial(self.self_destruct, True), 0.1)


            elif self.no_button and self.yes_button:

                # Right button
                if force_button == 'yes' or (not force_button and (rel_coord[0] > self.no_button.width + 5 and rel_coord[1] < self.yes_button.height)):
                    self.yes_button.background_color = tuple([px + 0.12 if px < 0.88 else px for px in rel_color])
                    self.resize_window()

                    if self.callback:
                        callback = self.callback[1]
                        if callback:
                            callback()
                            self.clicked = True

                    self.click_sound()
                    Clock.schedule_once(functools.partial(self.self_destruct, True), 0.1)

                # Left button
                elif force_button == 'no' or (not force_button and (rel_coord[0] < self.no_button.width - 5 and rel_coord[1] < self.no_button.height)):
                    self.no_button.background_color = tuple([px + 0.12 if px < 0.88 else px for px in rel_color])
                    self.resize_window()

                    if self.callback:
                        callback = self.callback[0]
                        if callback:
                            callback()
                            self.clicked = True

                    self.click_sound()
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

            image_path = os.path.join(paths.ui_assets, 'live', 'popup.png')
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

        if not self.shown:
            return

        def delete(*args):
            if self.parent:
                try:
                    for widget in self.parent.children:
                        if "Popup" in widget.__class__.__name__:
                            self.parent.popup_widget = None
                            self.parent.canvas.after.clear()
                            self.parent.remove_widget(widget)
                            self.canvas.after.clear()
                except AttributeError as e:
                    send_log(self.__class__.__name__, f"failed to delete popup as the parent window doesn't exist: {constants.format_traceback(e)}", 'error')

        if animate:
            self.animate(False)
            Clock.schedule_once(delete, 0.4)
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
            self.blur_background.source = os.path.join(paths.ui_assets, 'live', 'blur_background.png')
            self.blur_background.allow_stretch = True
            self.blur_background.keep_ratio = False
            self.generating_background = False


            # Popup window background
            self.window_background = Image(source=os.path.join(paths.ui_assets, "popup_background.png"))
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
            self.window_title.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
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
            self.window_content.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["bold"]}.ttf')


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
        self.window_icon_path = os.path.join(paths.ui_assets, 'icons', 'information-circle.png')
        super().__init__(**kwargs)

        # Modal specific settings
        self.window_sound = audio.player.load('popup/normal')
        self.no_button = None
        self.yes_button = None
        with self.canvas.after:
            self.ok_button = Button()
            self.ok_button.id = "ok_button"
            self.ok_button.size_hint = (None, None)
            self.ok_button.size = (459, 65)
            self.ok_button.border = (0, 0, 0, 0)
            self.ok_button.background_color = self.window_color
            self.ok_button.background_normal = os.path.join(paths.ui_assets, "popup_full_button.png")
            self.ok_button.pos_hint = {"center_x": 0.5}
            self.ok_button.text = "OKAY"
            self.ok_button.color = self.window_text_color
            self.ok_button.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["very-bold"]}.ttf')
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
        self.window_icon_path = os.path.join(paths.ui_assets, 'icons', 'alert-circle-sharp.png')
        super().__init__(**kwargs)

        # Modal specific settings
        self.window_sound = audio.player.load('popup/warning')
        self.no_button = None
        self.yes_button = None
        with self.canvas.after:
            self.ok_button = Button()
            self.ok_button.id = "ok_button"
            self.ok_button.size_hint = (None, None)
            self.ok_button.size = (459, 65)
            self.ok_button.border = (0, 0, 0, 0)
            self.ok_button.background_color = self.window_color
            self.ok_button.background_normal = os.path.join(paths.ui_assets, "popup_full_button.png")
            self.ok_button.pos_hint = {"center_x": 0.5}
            self.ok_button.text = "OKAY"
            self.ok_button.color = self.window_text_color
            self.ok_button.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["very-bold"]}.ttf')
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
        self.window_icon_path = os.path.join(paths.ui_assets, 'icons', 'question-circle.png')
        super().__init__(**kwargs)

        # Modal specific settings
        self.window_sound = audio.player.load('popup/normal')
        self.ok_button = None
        with self.canvas.after:
            self.no_button = Button()
            self.no_button.id = "no_button"
            self.no_button.size_hint = (None, None)
            self.no_button.size = (229.5, 65)
            self.no_button.border = (0, 0, 0, 0)
            self.no_button.background_color = self.window_color
            self.no_button.background_normal = os.path.join(paths.ui_assets, "popup_half_button.png")
            self.no_button.pos = (0.5, -0.3)
            self.no_button.text = "NO"
            self.no_button.color = self.window_text_color
            self.no_button.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["very-bold"]}.ttf')
            self.no_button.font_size = sp(22)


            self.yes_button = Button()
            self.yes_button.id = "yes_button"
            self.yes_button.size_hint = (None, None)
            self.yes_button.size = (-229.5, 65)
            self.yes_button.border = (0, 0, 0, 0)
            self.yes_button.background_color = self.window_color
            self.yes_button.background_normal = os.path.join(paths.ui_assets, "popup_half_button.png")
            self.yes_button.pos = (self.window_background.size[0] - 0.5, -0.3)
            self.yes_button.text = "YES"
            self.yes_button.color = self.window_text_color
            self.yes_button.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["very-bold"]}.ttf')
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
        self.window_icon_path = os.path.join(paths.ui_assets, 'icons', 'alert-circle-sharp.png')
        super().__init__(**kwargs)

        # Modal specific settings
        self.window_sound = audio.player.load('popup/warning')
        self.ok_button = None
        with self.canvas.after:
            self.no_button = Button()
            self.no_button.id = "no_button"
            self.no_button.size_hint = (None, None)
            self.no_button.size = (229.5, 65)
            self.no_button.border = (0, 0, 0, 0)
            self.no_button.background_color = self.window_color
            self.no_button.background_normal = os.path.join(paths.ui_assets, "popup_half_button.png")
            self.no_button.pos = (0.5, -0.3)
            self.no_button.text = "NO"
            self.no_button.color = self.window_text_color
            self.no_button.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["very-bold"]}.ttf')
            self.no_button.font_size = sp(22)


            self.yes_button = Button()
            self.yes_button.id = "yes_button"
            self.yes_button.size_hint = (None, None)
            self.yes_button.size = (-229.5, 65)
            self.yes_button.border = (0, 0, 0, 0)
            self.yes_button.background_color = self.window_color
            self.yes_button.background_normal = os.path.join(paths.ui_assets, "popup_half_button.png")
            self.yes_button.pos = (self.window_background.size[0] - 0.5, -0.3)
            self.yes_button.text = "YES"
            self.yes_button.color = self.window_text_color
            self.yes_button.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["very-bold"]}.ttf')
            self.yes_button.font_size = sp(22)
            self.bind(on_touch_down=self.click_event)


        self.window.add_widget(self.no_button)
        self.window.add_widget(self.yes_button)
        self.canvas.after.clear()

        self.blur_background.opacity = 0
        for widget in self.window.children:
            widget.opacity = 0

# View/Back
class PopupErrorLog(PopupWindow):
    def __init__(self, **kwargs):
        self.window_color = (1, 0.56, 0.6, 1)
        self.window_text_color = (0.2, 0.1, 0.1, 1)
        self.window_icon_path = os.path.join(paths.ui_assets, 'icons', 'question-circle.png')
        super().__init__(**kwargs)

        # Modal specific settings
        self.window_sound = audio.player.load('popup/warning')
        self.ok_button = None
        with self.canvas.after:
            self.no_button = Button()
            self.no_button.id = "no_button"
            self.no_button.size_hint = (None, None)
            self.no_button.size = (229.5, 65)
            self.no_button.border = (0, 0, 0, 0)
            self.no_button.background_color = self.window_color
            self.no_button.background_normal = os.path.join(paths.ui_assets, "popup_half_button.png")
            self.no_button.pos = (0.5, -0.3)
            self.no_button.text = "BACK"
            self.no_button.color = self.window_text_color
            self.no_button.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["very-bold"]}.ttf')
            self.no_button.font_size = sp(22)


            self.yes_button = Button()
            self.yes_button.id = "yes_button"
            self.yes_button.size_hint = (None, None)
            self.yes_button.size = (-229.5, 65)
            self.yes_button.border = (0, 0, 0, 0)
            self.yes_button.background_color = self.window_color
            self.yes_button.background_normal = os.path.join(paths.ui_assets, "popup_half_button.png")
            self.yes_button.pos = (self.window_background.size[0] - 0.5, -0.3)
            self.yes_button.text = "VIEW LOG"
            self.yes_button.color = self.window_text_color
            self.yes_button.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["very-bold"]}.ttf')
            self.yes_button.font_size = sp(22)
            self.bind(on_touch_down=self.click_event)


        self.window.add_widget(self.no_button)
        self.window.add_widget(self.yes_button)
        self.canvas.after.clear()

        self.blur_background.opacity = 0
        for widget in self.window.children:
            widget.opacity = 0

# Telepath pop-up window
class PopupTelepathPair(PopupWindow):

    def close_pair(self, *a):
        self.self_destruct(True)
        constants.telepath_pair.close()

    def update_expiry_bar(self):
        pair_data = constants.api_manager.pair_data
        Animation(size_hint_max_x=0, duration=(pair_data['expire'] - dt.now()).seconds).start(self.pair_bar)

        def later(*a):
            pair_data = constants.api_manager.pair_data
            if pair_data:
                Clock.schedule_once(later, 0.2)

                # Resize bar based on time remaining
                remaining = (pair_data['expire'] - dt.now()).seconds / (telepath.PAIR_CODE_EXPIRE_MINUTES * 60)
                if remaining <= 1:

                    # Change color if the code is about to expire
                    if remaining < 0.2:
                        self.pair_bar.color = (1, 0.56, 0.6, 1)
                        self.pair_rail.color = (0.2, 0.1, 0.1, 0.3)

                    self.resize_window()

            else:
                self.close_pair()

        later()

    def __init__(self, prompt=False, **kwargs):
        self.window_color = (0.3, 1, 0.6, 1)
        self.window_text_color = (0.07, 0.2, 0.12, 1)
        self.window_icon_path = os.path.join(paths.ui_assets, 'icons', 'telepath.png')
        super().__init__(**kwargs)

        # Check if pair succeeded with an API call from constants.telepath_pair
        if prompt:
            window_sound = 'telepath/request'
            title = '$Telepath$ Pair Request'
            button_text = 'CANCEL'
            self.data = constants.deepcopy(constants.telepath_pair.pair_data)

            # Override to show pair code
            self.window_content.markup = True
            code = f"{self.data['code'][0:3]}-{self.data['code'][3:]}"
            user_string = f'{self.data["host"]["host"]}/{self.data["host"]["user"]}'
            very_bold = os.path.join(paths.ui_assets, 'fonts', constants.fonts["mono-bold"])
            self.window_content.text = f"Pair '${user_string}$' with[size={round(sp(13))}]\n\n[/size][font={very_bold}.otf][size={round(sp(70))}]{code}[/size][/font]\n\n"
            self.window_content.pos_hint = {'center_y': 0.47, 'center_x': 0.5}

            # Pair texture
            self.bar_width = 250
            self.bar_offset = 0.32 if len(user_string) > 25 else 0.35
            with self.canvas.after:
                self.pair_rail = Image()
                self.pair_rail.id = "pair_bar"
                self.pair_rail.allow_stretch = True
                self.pair_rail.keep_ratio = False
                self.pair_rail.color = (*self.window_text_color[:-1], 0.3)
                self.pair_rail.size_hint_max = (self.bar_width, 10)
                self.pair_rail.pos_hint = {"center_x": 0.5, "center_y": self.bar_offset}

                self.pair_bar = Image()
                self.pair_bar.id = "pair_bar"
                self.pair_bar.allow_stretch = True
                self.pair_bar.keep_ratio = False
                self.pair_bar.color = self.window_color
                self.pair_bar.size_hint_max = (self.bar_width, 10)
                self.pair_bar.pos_hint = {"center_x": 0.5, "center_y": self.bar_offset}
            self.window.add_widget(self.pair_rail)
            self.window.add_widget(self.pair_bar)
            self.update_expiry_bar()

        else:
            success = True
            if success:
                window_sound = 'telepath/telepath_success'
                title = 'Pair Success'
                button_text = 'OKAY'
            else:
                window_sound = 'popup/warning'
                title = 'Pair Failure'
                button_text = 'OKAY'

        # Modal specific settings
        self.window_title.text = title
        self.window_sound = audio.player.load(window_sound)
        self.no_button = None
        self.yes_button = None
        with self.canvas.after:
            self.ok_button = Button()
            self.ok_button.id = "ok_button"
            self.ok_button.size_hint = (None, None)
            self.ok_button.size = (459, 65)
            self.ok_button.border = (0, 0, 0, 0)
            self.ok_button.background_color = self.window_color
            self.ok_button.background_normal = os.path.join(paths.ui_assets, "popup_full_button.png")
            self.ok_button.pos_hint = {"center_x": 0.5}
            self.ok_button.text = button_text
            self.ok_button.color = self.window_text_color
            self.ok_button.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["very-bold"]}.ttf')
            self.ok_button.font_size = sp(22)
            self.bind(on_touch_down=self.click_event)

        self.window.add_widget(self.ok_button)
        self.canvas.after.clear()

        self.blur_background.opacity = 0
        for widget in self.window.children:
            widget.opacity = 0



# Big popup widgets
class BigPopupWindow(RelativeLayout):
    @staticmethod
    def click_sound(): audio.player.play('interaction/click_*', jitter=(0, 0.15))

    def generate_blur_background(self, *args):
        image_path = os.path.join(paths.ui_assets, 'live', 'blur_background.png')
        try: constants.folder_check(os.path.join(paths.ui_assets, 'live'))
        except:
            self.blur_background.color = constants.background_color
            return

        # Prevent this from running every resize
        def reset_activity(*args):
            self.generating_background = False

        if not self.generating_background:
            self.generating_background = True

            if self.shown:
                for widget in self.window.children:
                    widget.opacity = 0
                self.blur_background.opacity = 0

            utility.screen_manager.current_screen.export_to_png(image_path)
            im = PILImage.open(image_path)
            im = ImageEnhance.Brightness(im)
            im = im.enhance(popup_blur_darkness)
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

    def body_button_click(self):
        pass

    def click_event(self, *args):
        button_pressed = 'ignore'
        try: button_pressed = args[1].button
        except: pass

        if not self.clicked and button_pressed in ('left', 'ignore'):

            def check_body_button(*a):
                if self.body_button:
                    if force_button == 'body' or (not force_button and ((self.body_button.x < rel_coord[0] < self.body_button.x + self.body_button.width) and (self.body_button.y < rel_coord[1] < self.body_button.y + self.body_button.height))):
                        Animation.stop_all(self.body_button)
                        self.body_button.background_color = (
                        self.window_text_color[0], self.window_text_color[1], self.window_text_color[2], 0.3)
                        Animation(background_color=self.window_text_color, duration=0.3).start(self.body_button)
                        self.body_button_click()
                        self.click_sound()
                        for x in range(10): Clock.schedule_once(self.resize_window, x/30)

            if isinstance(args[1], str):
                force_button = args[1]
                rel_coord = (0, Window.height)
            else:
                force_button = None
                rel_coord = (args[1].pos[0] - self.x - self.window.x, args[1].pos[1] - self.y - self.window.y)

            rel_color = self.window_background.color

            # Single, wide button
            if self.ok_button:
                if (force_button in ('ok', 'yes')) or (not force_button and (rel_coord[0] < self.ok_button.width and rel_coord[1] < self.ok_button.height)):
                    self.ok_button.background_color = tuple([px + 0.12 if px < 0.88 else px for px in rel_color])
                    self.resize_window()

                    if self.callback:
                        self.callback()
                        self.clicked = True

                    self.click_sound()
                    Clock.schedule_once(functools.partial(self.self_destruct, True), 0.1)

                else:
                    check_body_button()


            elif (self.no_button and self.yes_button) or self.__class__.__name__ == 'PopupFile':

                # Right button
                if force_button == 'yes' or (not force_button and (rel_coord[0] > self.no_button.width + 5 and rel_coord[1] < self.yes_button.height)):
                    self.yes_button.background_color = tuple([px + 0.12 if px < 0.88 else px for px in rel_color])
                    self.resize_window()

                    if self.callback:
                        callback = self.callback[1]
                        if callback:
                            callback()
                            self.clicked = True

                    self.click_sound()
                    Clock.schedule_once(functools.partial(self.self_destruct, True), 0.1)

                # Left button
                elif force_button == 'no' or (not force_button and (rel_coord[0] < self.no_button.width - 5 and rel_coord[1] < self.no_button.height)):
                    self.no_button.background_color = tuple([px + 0.12 if px < 0.88 else px for px in rel_color])
                    self.resize_window()

                    if self.callback:
                        callback = self.callback[0]
                        if callback:
                            callback()
                            self.clicked = True

                    self.click_sound()
                    Clock.schedule_once(functools.partial(self.self_destruct, True), 0.1)

                # Body button if it exists
                elif self.body_button:
                    check_body_button()


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

            image_path = os.path.join(paths.ui_assets, 'live', 'popup.png')
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

        if not self.shown:
            return

        def delete(*args):
            if self.parent:
                try:
                    for widget in self.parent.children:
                        if "Popup" in widget.__class__.__name__:
                            self.parent.popup_widget = None
                            self.parent.canvas.after.clear()
                            self.parent.remove_widget(widget)
                            self.canvas.after.clear()
                except AttributeError as e:
                    send_log(self.__class__.__name__, f"failed to delete popup as the parent window doesn't exist: {constants.format_traceback(e)}", 'error')

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
        self.body_button = None

        with self.canvas.after:
            # Blurred background
            self.blur_background = Image()
            self.blur_background.opacity = 0
            self.blur_background.id = "blur_background"
            self.blur_background.source = os.path.join(paths.ui_assets, 'live', 'blur_background.png')
            self.blur_background.allow_stretch = True
            self.blur_background.keep_ratio = False
            self.generating_background = False


            # Popup window background
            self.window_background = Image(source=os.path.join(paths.ui_assets, "big_popup_background.png"))
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
            self.window_title.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')


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
            self.window_content.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["bold"]}.ttf')


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
        self.window_icon_path = os.path.join(paths.ui_assets, 'icons', 'information-circle.png')
        super().__init__(**kwargs)


        # Align window content
        self.window_content.halign = "left"
        self.window_content.valign = "top"
        self.window_content.pos_hint = {"center_x": 0.5, "center_y": 0.4}
        self.window_content.max_lines = 15 # Cuts off the beginning of content??


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
            self.ok_button.background_normal = os.path.join(paths.ui_assets, "big_popup_full_button.png")
            self.ok_button.pos_hint = {"center_x": 0.5006}
            self.ok_button.text = "OKAY"
            self.ok_button.color = self.window_text_color
            self.ok_button.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["very-bold"]}.ttf')
            self.ok_button.font_size = sp(22)
            self.bind(on_touch_down=self.click_event)

        self.window.add_widget(self.ok_button)
        self.canvas.after.clear()

        self.blur_background.opacity = 0
        for widget in self.window.children:
            widget.opacity = 0

# Popup for text files
class PopupFile(BigPopupWindow):
    def body_button_click(self):
        if self.file_path:
            view_file(self.file_path)

    def set_text(self, path: str, *a):
        if os.path.isfile(path):
            with open(path, 'r') as f:
                self.window_content.text = f.read()
                self.file_path = path
        else:
            self.window_content.text = 'No content available'

    def __init__(self, **kwargs):
        self.file_path = None

        self.window_color = (0.42, 0.475, 1, 1)
        self.window_text_color = (0.1, 0.1, 0.2, 1)
        self.window_icon_path = os.path.join(paths.ui_assets, 'icons', 'information-circle.png')
        super().__init__(**kwargs)


        # Align window content
        self.window_content.__translate__ = False
        self.window_content.halign = "left"
        self.window_content.valign = "top"
        self.window_content.pos_hint = {"center_x": 0.5, "center_y": 0.41}
        self.window_content.max_lines = 14 # Cuts off the beginning of content??


        # Modal specific settings
        self.window_sound = None
        self.no_button = None
        self.yes_button = None
        with self.canvas.after:

            # Body Button (Open in logviewer)
            self.body_button = Button()
            self.body_button.id = "body_button"
            self.body_button.size_hint = (None, None)
            self.body_button.size = (200 if constants.app_config.locale == 'en' else 260, 40)
            self.body_button.border = (0, 0, 0, 0)
            self.body_button.background_color = self.window_text_color
            self.body_button.background_normal = os.path.join(paths.ui_assets, "addon_view_button.png")
            self.body_button.pos = ((self.window_background.size[0] / 2) - (self.body_button.size[0] / 2), 77)
            self.body_button.text = "click to view more"
            self.body_button.color = self.window_color
            self.body_button.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
            self.body_button.font_size = sp(20)


            self.ok_button = Button()
            self.ok_button.id = "ok_button"
            self.ok_button.size_hint = (None, None)
            self.ok_button.size = (650.6, 65)
            self.ok_button.border = (0, 0, 0, 0)
            self.ok_button.background_color = self.window_color
            self.ok_button.background_normal = os.path.join(paths.ui_assets, "big_popup_full_button.png")
            self.ok_button.pos_hint = {"center_x": 0.5006}
            self.ok_button.text = "OKAY"
            self.ok_button.color = self.window_text_color
            self.ok_button.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["very-bold"]}.ttf')
            self.ok_button.font_size = sp(22)
            self.bind(on_touch_down=self.click_event)

        self.window.add_widget(self.ok_button)
        self.window.add_widget(self.body_button)
        self.canvas.after.clear()

        self.blur_background.opacity = 0
        for widget in self.window.children:
            widget.opacity = 0

# Addon popup
class PopupAddon(BigPopupWindow):
    def body_button_click(self):
        if self.addon_object: webbrowser.open_new_tab(self.addon_object.url)

    def __init__(self, addon_object=None, **kwargs):
        self.window_color = (0.42, 0.475, 1, 1)
        self.window_text_color = (0.1, 0.1, 0.2, 1)
        self.window_icon_path = os.path.join(paths.ui_assets, 'icons', 'extension-puzzle-sharp.png')
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

        self.is_modpack = utility.screen_manager.current_screen.name == "ServerImportModpackSearchScreen"


        # Title
        self.window_title.text_size[0] = (self.window_background.size[0] * 0.7)
        self.window_title.__translate__ = False
        self.window_title.halign = "center"
        self.window_title.shorten = True
        self.window_title.markup = True
        self.window_title.shorten_from = "right"
        self.window_title.text = f"{self.addon_object.name}  [color=#3E4691]-[/color]  {self.addon_object.author if self.addon_object.author else 'Unknown'}"


        # Description
        self.window_content.__translate__ = False
        self.window_content.text = "" if not addon_object else self.addon_object.description
        if not self.window_content.text.strip():
            self.window_content.text = "description unavailable"
        else:
            self.window_content.halign = "left"
            self.window_content.valign = "top"
            self.window_content.pos_hint = {"center_x": 0.5, "center_y": 0.465 if self.is_modpack else 0.4}

        if self.is_modpack:
            self.window_content.max_lines = 15 # Cuts off the beginning of content??
        else:
            self.window_content.max_lines = 13 if self.installed else 14  # Cuts off the beginning of content??


        # Modal specific settings
        self.window_sound = None
        self.ok_button = None
        with self.canvas.after:

            # Body Button (Open in browser)
            self.body_button = Button()
            self.body_button.id = "body_button"
            self.body_button.size_hint = (None, None)
            self.body_button.size = (200 if constants.app_config.locale == 'en' else 260, 40)
            self.body_button.border = (0, 0, 0, 0)
            self.body_button.background_color = self.window_text_color
            self.body_button.background_normal = os.path.join(paths.ui_assets, "addon_view_button.png")
            self.body_button.pos = ((self.window_background.size[0] / 2) - (self.body_button.size[0] / 2), 77)
            self.body_button.text = "click to view more"
            self.body_button.color = self.window_color
            self.body_button.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
            self.body_button.font_size = sp(20)



            self.no_button = Button()
            self.no_button.id = "no_button"
            self.no_button.size_hint = (None, None)
            self.no_button.size = (327, 65)
            self.no_button.border = (0, 0, 0, 0)
            self.no_button.background_color = self.window_color
            self.no_button.background_normal = os.path.join(paths.ui_assets, "big_popup_half_button.png")
            self.no_button.pos = (0, -0.3)
            self.no_button.text = "BACK"
            self.no_button.color = self.window_text_color
            self.no_button.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["very-bold"]}.ttf')
            self.no_button.font_size = sp(22)

            self.yes_button = Button()
            self.yes_button.id = "install_button"
            self.yes_button.size_hint = (None, None)
            self.yes_button.size = (-327, 65)
            self.yes_button.border = (0, 0, 0, 0)
            self.yes_button.background_color = self.window_color
            self.yes_button.background_normal = os.path.join(paths.ui_assets, "big_popup_half_button.png")
            self.yes_button.pos = (self.window_background.size[0] + 1, -0.3)
            self.yes_button.text = "INSTALL" if not self.installed else "UNINSTALL"
            self.yes_button.color = self.window_text_color
            self.yes_button.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["very-bold"]}.ttf')
            self.yes_button.font_size = sp(22)


            # Version Banner
            if not self.is_modpack:
                addon_supported = False
                if not self.addon_object.versions:
                    addon_versions = "None"

                elif len(self.addon_object.versions) == 1:
                    addon_versions = self.addon_object.versions[0]

                else:
                    addon_versions = f"{self.addon_object.versions[-1]}-{self.addon_object.versions[0]}"

                if utility.screen_manager.current_screen.name == "CreateServerAddonSearchScreen":
                    server_version = foundry.new_server_info['version']
                else:
                    server_version = constants.server_manager.current_server.version

                if self.addon_object.versions:
                    addon_supported = constants.version_check(server_version, ">=", self.addon_object.versions[-1]) and constants.version_check(server_version, "<=", self.addon_object.versions[0])

                version_text = f"{translate('Supported' if addon_supported else 'Unsupported')}:  {addon_versions}"

                self.version_banner = BannerObject(
                    __translate__ = False,
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

        if not self.is_modpack:
            self.window.add_widget(self.version_banner)
            if self.installed:
                self.window.add_widget(self.installed_banner)

        self.bind(on_touch_down=self.click_event)

        self.canvas.after.clear()

        self.blur_background.opacity = 0
        for widget in self.window.children:
            widget.opacity = 0

# Script popup
class PopupScript(BigPopupWindow):
    def body_button_click(self):
        if self.script_object:
            webbrowser.open_new_tab(self.script_object.url)

    def __init__(self, script_object=None, **kwargs):

        self.window_color = (0.42, 0.475, 1, 1)
        self.window_text_color = (0.1, 0.1, 0.2, 1)
        self.window_icon_path = os.path.join(paths.ui_assets, 'icons', 'amscript.png')
        self.installed = False

        # Assign addon info to popup
        if script_object:
            self.script_object = script_object[1]
            self.installed = script_object[0]
        else:
            self.script_object = None

        # If addon is unavailable, show info
        if not self.script_object:
            del self
            return


        super().__init__(**kwargs)


        # Title
        self.window_title.text_size[0] = (self.window_background.size[0] * 0.7)
        self.window_title.__translate__ = False
        self.window_title.halign = "center"
        self.window_title.shorten = True
        self.window_title.markup = True
        self.window_title.shorten_from = "right"
        self.window_title.text = f"{self.script_object.name}  [color=#3E4691]-[/color]  {self.script_object.author if self.script_object.author else 'Unknown'}"


        # Description
        self.window_content.__translate__ = False
        self.window_content.text = "" if not script_object else self.script_object.description
        if not self.window_content.text.strip():
            self.window_content.text = "description unavailable"
        else:
            self.window_content.halign = "left"
            self.window_content.valign = "top"
            self.window_content.pos_hint = {"center_x": 0.5, "center_y": 0.35 if self.installed else 0.4}

        self.window_content.max_lines = 13 if self.installed else 14 # Cuts off the beginning of content??


        # Modal specific settings
        self.window_sound = None
        self.ok_button = None
        with self.canvas.after:

            # Body Button (Open in browser)
            self.body_button = Button()
            self.body_button.id = "body_button"
            self.body_button.size_hint = (None, None)
            self.body_button.size = (200 if constants.app_config.locale == 'en' else 260, 40)
            self.body_button.border = (0, 0, 0, 0)
            self.body_button.background_color = self.window_text_color
            self.body_button.background_normal = os.path.join(paths.ui_assets, "addon_view_button.png")
            self.body_button.pos = ((self.window_background.size[0] / 2) - (self.body_button.size[0] / 2), 77)
            self.body_button.text = "click to view more"
            self.body_button.color = self.window_color
            self.body_button.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
            self.body_button.font_size = sp(20)



            self.no_button = Button()
            self.no_button.id = "no_button"
            self.no_button.size_hint = (None, None)
            self.no_button.size = (327, 65)
            self.no_button.border = (0, 0, 0, 0)
            self.no_button.background_color = self.window_color
            self.no_button.background_normal = os.path.join(paths.ui_assets, "big_popup_half_button.png")
            self.no_button.pos = (0, -0.3)
            self.no_button.text = "BACK"
            self.no_button.color = self.window_text_color
            self.no_button.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["very-bold"]}.ttf')
            self.no_button.font_size = sp(22)

            self.yes_button = Button()
            self.yes_button.id = "install_button"
            self.yes_button.size_hint = (None, None)
            self.yes_button.size = (-327, 65)
            self.yes_button.border = (0, 0, 0, 0)
            self.yes_button.background_color = self.window_color
            self.yes_button.background_normal = os.path.join(paths.ui_assets, "big_popup_half_button.png")
            self.yes_button.pos = (self.window_background.size[0] + 1, -0.3)
            self.yes_button.text = "INSTALL" if not self.installed else "UNINSTALL"
            self.yes_button.color = self.window_text_color
            self.yes_button.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["very-bold"]}.ttf')
            self.yes_button.font_size = sp(22)

            # Installed banner
            if self.installed:
                self.installed_banner = BannerObject(
                    pos_hint = {"center_x": 0.5, "center_y": 0.877},
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
        if self.installed:
            self.window.add_widget(self.installed_banner)

        self.bind(on_touch_down=self.click_event)

        self.canvas.after.clear()

        self.blur_background.opacity = 0
        for widget in self.window.children:
            widget.opacity = 0

# Update popup
class PopupUpdate(BigPopupWindow):
    def body_button_click(self):
        url = constants.update_data['web_url']
        if url: webbrowser.open_new_tab(url)

    def __init__(self, **kwargs):
        self.window_color = (0.42, 0.475, 1, 1)
        self.window_text_color = (0.1, 0.1, 0.2, 1)
        self.window_icon_path = os.path.join(paths.ui_assets, 'icons', 'cloud-download.png')

        # Assign update info to popup
        if constants.update_data:
            self.update_data = constants.update_data
        else:
            self.update_data = None
            del self
            return

        if not self.update_data['version']:
            del self
            return

        super().__init__(**kwargs)


        # Title
        self.window_title.text_size[0] = (self.window_background.size[0] * 0.7)
        self.window_title.halign = "center"
        self.window_title.shorten = True
        self.window_title.markup = True
        self.window_title.shorten_from = "right"
        self.window_title.text = f"Update Available"


        # Description
        self.window_content.__translate__ = False
        self.window_content.text = "" if not self.update_data['desc'] else ("\n\n" + self.update_data['desc'])
        if not self.window_content.text.strip():
            self.window_content.text = "description unavailable"
        else:
            self.window_content.halign = "left"
            self.window_content.valign = "top"
            self.window_content.pos_hint = {"center_x": 0.5, "center_y": 0.4}
        self.window_content.max_lines = 14 # Cuts off the beginning of content??


        # Modal specific settings
        self.window_sound = audio.player.load('popup/normal')
        self.ok_button = None
        with self.canvas.after:

            # Body Button (Open in browser)
            self.body_button = Button()
            self.body_button.id = "body_button"
            self.body_button.size_hint = (None, None)
            self.body_button.size = (200 if constants.app_config.locale == 'en' else 260, 40)
            self.body_button.border = (0, 0, 0, 0)
            self.body_button.background_color = self.window_text_color
            self.body_button.background_normal = os.path.join(paths.ui_assets, "addon_view_button.png")
            self.body_button.pos = ((self.window_background.size[0] / 2) - (self.body_button.size[0] / 2), 77)
            self.body_button.text = "click to view more"
            self.body_button.color = self.window_color
            self.body_button.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
            self.body_button.font_size = sp(20)


            self.no_button = Button()
            self.no_button.id = "no_button"
            self.no_button.size_hint = (None, None)
            self.no_button.size = (327, 65)
            self.no_button.border = (0, 0, 0, 0)
            self.no_button.background_color = self.window_color
            self.no_button.background_normal = os.path.join(paths.ui_assets, "big_popup_half_button.png")
            self.no_button.pos = (0, -0.3)
            self.no_button.text = "BACK"
            self.no_button.color = self.window_text_color
            self.no_button.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["very-bold"]}.ttf')
            self.no_button.font_size = sp(22)

            self.yes_button = Button()
            self.yes_button.id = "install_button"
            self.yes_button.size_hint = (None, None)
            self.yes_button.size = (-327, 65)
            self.yes_button.border = (0, 0, 0, 0)
            self.yes_button.background_color = self.window_color
            self.yes_button.background_normal = os.path.join(paths.ui_assets, "big_popup_half_button.png")
            self.yes_button.pos = (self.window_background.size[0] + 1, -0.3)
            self.yes_button.text = "INSTALL"
            self.yes_button.color = self.window_text_color
            self.yes_button.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["very-bold"]}.ttf')
            self.yes_button.font_size = sp(22)

            banner_text = f"v{self.update_data['version']}"
            if len(banner_text) > 6: banner_text = f" {banner_text} "

            self.version_banner = BannerObject(
                pos_hint = {"center_x": 0.5, "center_y": 0.877},
                size = (150, 40),
                color = (0.4, 0.682, 1, 1),
                text = banner_text,
                icon = "information-circle.png"
            )
            self.version_banner.id = "version_banner"


        self.window.add_widget(self.no_button)
        self.window.add_widget(self.yes_button)
        self.window.add_widget(self.body_button)
        self.window.add_widget(self.version_banner)

        self.bind(on_touch_down=self.click_event)

        self.canvas.after.clear()

        self.blur_background.opacity = 0
        for widget in self.window.children:
            widget.opacity = 0



# Global search bar
class PopupSearch(RelativeLayout):
    "play-circle-sharp.png"
    "newspaper.png"
    "terminal.png"
    "exit-sharp.png"

    class ResultButton(RelativeLayout):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

            self.size_hint_max = (600, 75)
            self.search_obj = None

            self.button = Button()
            self.button.border = (0, 0, 0, 0)
            self.button.background_normal = os.path.join(paths.ui_assets, 'global_search_button.png')
            self.add_widget(self.button)

            self.title = Label()
            self.title.text = 'Hello!'
            self.title.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["bold"]}.ttf')
            self.title.font_size = sp(30)
            self.title.pos_hint = {'center_x': 0.5, 'center_y': 0.75}
            self.title.markup = True
            self.add_widget(self.title)

            self.subtitle = Label()
            self.subtitle.text = "I'm a subtitle"
            self.subtitle.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
            self.subtitle.font_size = sp(22)
            self.subtitle.pos_hint = {'center_x': 0.5, 'center_y': 0.3}
            self.add_widget(self.subtitle)

            self.icon = Image(source=None)
            self.icon.id = "window_icon"
            self.icon.size_hint = (None, None)
            self.icon.allow_stretch = True
            self.icon.color = (1, 1, 1, 1)
            self.icon.size = (36, 36)
            self.icon.pos_hint = {'center_x': 0.05, 'center_y': 0.5}
            self.add_widget(self.icon)

            self.opacity = 0

        @staticmethod
        def fix_lag(t, *a):
            for x in range(t):
                Clock.schedule_once(utility.screen_manager.current_screen.popup_widget.resize_window, x / 100)

        # Contains all button overrides
        def animate_click(self):
            self.fix_lag(50)

            original_color = self.search_obj.color
            bright_color = constants.brighten_color(original_color, 0.15)

            new_original = constants.brighten_color(original_color, 0.25)
            new_bright = constants.brighten_color(bright_color, 0.1)

            self.title.color = new_bright
            self.icon.color = new_bright
            self.subtitle.color = new_original
            self.button.background_color = new_original

            Animation(color=bright_color, duration=0.5).start(self.title)
            Animation(color=bright_color, duration=0.5).start(self.icon)
            Animation(color=original_color, duration=0.5).start(self.subtitle)
            Animation(background_color=original_color, duration=0.5).start(self.button)

            # Process click with directed target
            def process_target(*b):

                # The following are overrides for extra functionality from the search bar
                def override_acl(list_type):
                    screen = utility.screen_manager.get_screen(self.search_obj.target)

                    if utility.screen_manager.current_screen.name == self.search_obj.target:
                        utility.screen_manager.current_screen.update_list(list_type)
                        text = 'OPERATORS' if list_type == 'ops' else 'WHITELIST' if list_type == 'wl' else 'BANS'
                        screen.page_selector.change_text(text)
                    else:
                        if self.search_obj.target.startswith('Server'):
                            screen.acl_object = constants.server_manager.current_server.acl
                            screen._hash = constants.server_manager.current_server._hash
                        else:
                            screen.acl_object = foundry.new_server_info['acl_object']
                            screen._hash = foundry.new_server_info['_hash']

                        screen.current_list = list_type
                        utility.screen_manager.current = self.search_obj.target

                # Override for launching the server
                if self.search_obj.title.lower() == 'launch server':
                    utility.screen_manager.current = self.search_obj.target
                    Clock.schedule_once(utility.screen_manager.current_screen.console_panel.launch_server, 0)

                elif self.search_obj.title.lower() == 'restart server':
                    constants.server_manager.current_server.restart()

                elif self.search_obj.title.lower() == 'stop server':
                    utility.screen_manager.current_screen.server.silent_command("stop")

                # Update server
                elif self.search_obj.title.lower() == 'update this server':
                    utility.screen_manager.current = self.search_obj.target
                    utility.screen_manager.current_screen.update_button.button.trigger_action()

                # Update auto-mcs
                elif self.search_obj.title.lower() == 'update auto-mcs':
                    utility.screen_manager.current = self.search_obj.target
                    Clock.schedule_once(utility.screen_manager.current_screen.prompt_update, 0)

                # ACL functions
                elif self.search_obj.title.lower() == 'configure bans':
                    override_acl('bans')

                elif self.search_obj.title.lower() == 'configure operators':
                    override_acl('ops')

                elif self.search_obj.title.lower() == 'configure the whitelist':
                    override_acl('wl')

                # Open directory functions
                elif self.search_obj.title.lower() == 'open server directory':
                    constants.open_folder(constants.server_manager.current_server.server_path)

                elif self.search_obj.title.lower() == 'open back-up directory':
                    constants.open_folder(constants.server_manager.current_server.backup.directory)

                elif self.search_obj.title.lower() == 'open script directory':
                    constants.open_folder(paths.scripts)

                # Save back-up
                elif self.search_obj.title.lower() == 'save a back-up now':
                    utility.screen_manager.current = self.search_obj.target
                    utility.screen_manager.current_screen.save_backup_button.button.trigger_action()

                # Create a new server
                elif self.search_obj.title.lower() == 'create a new server':
                    foundry.new_server_init()
                    utility.screen_manager.current = self.search_obj.target

                # Migrate server
                elif self.search_obj.title.lower() == "change 'server.jar'":
                    server_obj = constants.server_manager.current_server
                    foundry.new_server_init()
                    foundry.new_server_info['type'] = server_obj.type
                    foundry.new_server_info['version'] = server_obj.version
                    utility.screen_manager.current = self.search_obj.target

                # Transilience settings
                elif self.search_obj.title.lower() == 'rename this server':
                    utility.screen_manager.current = self.search_obj.target
                    rename_input = utility.screen_manager.current_screen.rename_input
                    utility.screen_manager.current_screen.scroll_widget.scroll_to(rename_input)
                    Clock.schedule_once(rename_input.grab_focus, 0.2)

                elif self.search_obj.title.lower() == 'delete this server':
                    utility.screen_manager.current = self.search_obj.target
                    delete_button = utility.screen_manager.current_screen.delete_button
                    utility.screen_manager.current_screen.scroll_widget.scroll_to(delete_button, animate=False)
                    Clock.schedule_once(delete_button.button.trigger_action, 0.1)

                # Install proxy
                elif self.search_obj.title.lower() == 'install proxy (playit)':
                    utility.screen_manager.current = self.search_obj.target
                    proxy_button = utility.screen_manager.current_screen.proxy_button
                    utility.screen_manager.current_screen.scroll_widget.scroll_to(proxy_button, animate=False)
                    Clock.schedule_once(proxy_button.button.trigger_action, 0.1)


                # Below is standard functionality for the server actions

                # Open server
                elif self.search_obj.type == 'server':
                    if self.search_obj._telepath_data:
                        open_remote_server(self.search_obj._telepath_data, self.search_obj._telepath_data['name'])
                    else:
                        open_server(self.search_obj.title)

                # Otherwise, launch web URL or go to screen
                elif self.search_obj.target:
                    if self.search_obj.target.startswith('http'):
                        webbrowser.open_new_tab(self.search_obj.target)
                    else:
                        utility.screen_manager.current = self.search_obj.target

            def do_things(*a):
                utility.screen_manager.current_screen.popup_widget.self_destruct(True)
                Clock.schedule_once(process_target, 0.4)
            Clock.schedule_once(do_things, 0.14)

        def refresh_data(self, search_obj, fun_anim=False, *a):

            def fade_out():
                Animation.stop_all(self)
                Animation(opacity=0, duration=0.2, transition='in_out_sine').start(self)

            if not search_obj:
                fade_out()
                return None

            try:
                animate = search_obj.title != self.title.text
            except AttributeError:
                fade_out()
                return None

            if animate:
                self.fix_lag(50)
                def change_data(*a):
                    self.title.__translate__ = not search_obj.type == 'server'

                    self.search_obj = search_obj
                    self.title.text = search_obj.title
                    self.subtitle.text = search_obj.subtitle
                    self.icon.source = search_obj.icon
                    self.title.font_size = sp(30 - (0 if len(self.title.text) < 30 else (len(self.title.text) / 7)))
                    self.title.pos_hint = {'center_x': (0.5 if len(self.title.text) < 30 else 0.51), 'center_y': 0.75}

                    # Change Colors
                    bright_color = constants.brighten_color(search_obj.color, 0.15)
                    self.title.color = bright_color
                    self.icon.color = bright_color
                    self.subtitle.color = search_obj.color
                    self.button.background_color = search_obj.color

                    Animation.stop_all(self)
                    Animation(opacity=1, duration=0.5 if fun_anim else 0.2, transition='in_out_sine').start(self)
                fade_out()
                Clock.schedule_once(change_data, 0.1)

    @staticmethod
    def click_sound(): audio.player.play('interaction/click_*', jitter=(0, 0.15))

    def generate_blur_background(self, *args):
        image_path = os.path.join(paths.ui_assets, 'live', 'blur_background.png')
        try: constants.folder_check(os.path.join(paths.ui_assets, 'live'))
        except:
            self.blur_background.color = constants.background_color
            return

        # Prevent this from running every resize
        def reset_activity(*args):
            self.generating_background = False

        if not self.generating_background:
            self.generating_background = True

            if self.shown:
                for widget in self.window.children:
                    widget.opacity = 0
                self.blur_background.opacity = 0

            utility.screen_manager.current_screen.export_to_png(image_path)
            im = PILImage.open(image_path)
            im = ImageEnhance.Brightness(im)
            im = im.enhance(popup_blur_darkness - 0.09)
            im1 = im.filter(GaussianBlur(popup_blur_amount + 5))
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

        button_pressed = 'ignore'
        try: button_pressed = args[1].button
        except: pass

        if not self.clicked and button_pressed == 'left':

            if isinstance(args[1], str):
                self.click_sound()
                self.self_destruct(True)
            else:
                rel_coord = (args[1].pos[0] - self.x - self.window.x, args[1].pos[1] - self.y - self.window.y)

            for button in self.results.children:
                if button.opacity == 1:
                    if button.width > rel_coord[0] > button.x and (button.height + button.y) > rel_coord[1] > button.y:
                        button.animate_click()
                        self.dont_hide = True
                        self.click_sound()
                    else:
                        Animation(opacity=0, duration=0.13).start(button)


    def resize(self):
        self.window.size = self.window_background.size

        # Shift the popup upward at smaller window heights
        offset_y = 0
        if Window.size[1] < 900:
            offset_y = 75
        if Window.size[1] < 800:
            offset_y = 100

        # Add offset_y to the original y-position
        self.window.pos = (
            Window.size[0] / 2 - self.window_background.width / 2,
            Window.size[1] / 2 - self.window_background.height / 2 + offset_y
        )

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

            image_path = os.path.join(paths.ui_assets, 'live', 'popup.png')
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

        if not self.shown:
            return

        def delete(*args):
            if self.parent:
                try:
                    for widget in self.parent.children:
                        if "Popup" in widget.__class__.__name__:
                            self.parent.popup_widget = None
                            self.parent.canvas.after.clear()
                            self.parent.remove_widget(widget)
                            self.canvas.after.clear()
                except AttributeError as e:
                    send_log(self.__class__.__name__, f"failed to delete popup as the parent window doesn't exist: {constants.format_traceback(e)}", 'error')

        if animate:
            self.animate(False)
            Clock.schedule_once(delete, 0.4)
        else:
            delete()


    # Generate search results when typing
    def on_search(self, force=None, fun_anim=False, *a):

        # Set lock for a timeout
        if not self.search_lock and (self.window_input.text or force):
            self.search_lock = True

            # Update results with query
            if force:
                self.search_text = force
            else:
                self.search_text = self.window_input.text
            try:
                results = constants.search_manager.execute_search(utility.screen_manager.current, self.search_text)

                complete_list = [results['guide']]
                complete_list.extend(results['server'])
                complete_list.extend(results['setting'])
                complete_list.extend(results['screen'])
                complete_list = tuple(sorted(complete_list, key=lambda x: x.score, reverse=True))

                for x, button in enumerate(reversed(self.results.children), 0):
                    if fun_anim:
                        Clock.schedule_once(functools.partial(button.refresh_data, complete_list[x], True), (x*0.1))
                    else:
                        button.refresh_data(complete_list[x])

            except:
                pass

            # print(vars(results['guide']))
            # for item in results['server'][:2]:
            #     print(vars(item))
            # for item in results['setting'][:2]:
            #     print(vars(item))
            # for item in results['screen'][:2]:
            #     print(vars(item))


            # Reset lock for a timeout
            def reset_lock(*a):
                self.search_lock = False
                if self.search_text != self.window_input.text:
                    self.on_search()
            Clock.schedule_once(reset_lock, 0.5)


    def hide_on_unfocus(self, *a):
        if not self.window_input.focused:
            def test_hide(*a):
                if not self.dont_hide:
                    self.self_destruct(True)
            Clock.schedule_once(test_hide, 0.1)


    def on_enter(self, *a):
        top_button = self.results.children[-1]
        Animation(opacity=0, duration=0.13).start(self.results.children[0])
        Animation(opacity=0, duration=0.13).start(self.results.children[1])
        if top_button.opacity > 0:
            top_button.animate_click()
            self.dont_hide = True


    def init_search(self, *a):
        screen_name = utility.screen_manager.current_screen.name

        # Help overrides
        if screen_name == 'MainMenuScreen':
            query = 'getting started'
        elif screen_name == 'ServerViewScreen':
            query = 'help server manager'
        elif 'Acl' in screen_name:
            query = 'help access control'
        else:
            filtered = ''.join(map(lambda x: x if x.islower() else " "+x, screen_name.replace('Screen','').replace('Server',''))).lower().strip()
            query = f'help {filtered}'
        self.on_search(force=query, fun_anim=True)


    def __init__(self, **kwargs):
        self.window_color = (0.42, 0.475, 1, 1)
        self.window_text_color = (0.78, 0.78, 1, 1)
        self.window_icon_path = os.path.join(paths.ui_assets, 'icons', 'information-circle.png')
        super().__init__(**kwargs)

        # Popup window layout
        self.window = RelativeLayout()
        self.callback = None
        self.shown = False
        self.clicked = False
        self.dont_hide = False

        self.max_results = 3
        self.search_lock = False
        self.search_text = ''

        with self.canvas.after:
            # Blurred background
            self.blur_background = Image()
            self.blur_background.opacity = 0
            self.blur_background.id = "blur_background"
            self.blur_background.source = os.path.join(paths.ui_assets, 'live', 'blur_background.png')
            self.blur_background.allow_stretch = True
            self.blur_background.keep_ratio = False
            self.generating_background = False


            # Popup window background
            self.window_background = Image(source=os.path.join(paths.ui_assets, "global_search.png"))
            self.window_background.id = "window_background"
            self.window_background.size_hint = (None, None)
            self.window_background.keep_ratio = False
            self.window_background.size = (600, 800)
            self.window_background.pos_hint = {"center_x": 0.5, "center_y": 0.5}


            # Input to type in
            self.window_input = BaseInput()
            self.window_input.__translate__ = False
            self.window_input.title_text = ""
            self.window_input.id = 'global_search_input'
            self.window_input.multiline = False
            self.window_input.size_hint_max = (600, 100)
            self.window_input.pos_hint = {"center_x": 0.5, "center_y": 0.5}
            self.window_input.padding_y = (30, 29)
            self.window_input.padding_x = (25, 25)
            self.window_input.halign = "left"
            self.window_input.hint_text_color = (0.6, 0.6, 1, 0.4)
            self.window_input.foreground_color = (0.78, 0.78, 1, 0.8)
            self.window_input.background_color = (0, 0, 0, 0)
            self.window_input.cursor_color = (0.78, 0.78, 1, 0.8)
            self.window_input.selection_color = (0.7, 0.7, 1, 0.4)
            self.window_input.cursor_width = 4
            self.window_input.font_size = sp(32)
            self.window_input.on_text_validate = self.on_enter
            self.window_input.bind(text=self.on_search)


            self.window_title = Label()
            self.window_title.id = "window_title"
            self.window_title.text = "search for anything"
            self.window_title.color = self.window_text_color
            self.window_title.font_size = sp(40)
            self.window_title.y = (self.window_background.height / 7.5)
            self.window_title.pos_hint = {"center_x": 0.5}
            self.window_title.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["bold"]}.ttf')
            self.window_title.text_size[0] = (self.window_background.size[0] * 0.7)
            self.window_title.halign = "center"
            self.window_title.shorten = True
            self.window_title.markup = True
            self.window_title.shorten_from = "right"


            # Popup window content
            self.window_content = Label()
            self.window_content.__translate__ = False
            self.window_content.id = "window_content"
            self.window_content.color = tuple([px * 1.5 if px < 1 else px for px in self.window_text_color])
            self.window_content.font_size = sp(23)
            self.window_content.line_height = 1.15
            self.window_content.halign = "center"
            self.window_content.valign = "center"
            self.window_content.text_size = (self.window_background.width - 40, self.window_background.height - 25)
            self.window_content.pos_hint = {"center_x": 0.5, "center_y": 1}
            self.window_content.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["bold"]}.ttf')


            # Results layout
            self.results = GridLayout(cols=1, spacing=30)
            self.results.id = 'search_results'
            self.results.size_hint_max = (600, 500)
            self.results.pos_hint = {'center_x': 0.5}
            self.results.y = -200

            for x in range(self.max_results):
                self.results.add_widget(self.ResultButton())


        self.add_widget(self.blur_background)
        self.window.add_widget(self.window_input)
        self.window.add_widget(self.results)
        self.window.add_widget(self.window_background)
        self.window.add_widget(self.window_title)
        self.window.add_widget(self.window_content)

        self.bind(on_touch_down=self.click_event)
        self.window_input.bind(focus=self.hide_on_unfocus)

        self.canvas.after.clear()

        self.blur_background.opacity = 0
        for widget in self.window.children:
            widget.opacity = 0

        Clock.schedule_once(self.window_input.grab_focus, 0)
        Clock.schedule_once(self.init_search, 0)



# Screen widgets

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
            else:
                return_to_main()

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

        # Different behavior depending on the page
        elif "next" in button_name.lower() and not button.disabled:

            def change_screen(name, *args, **kwargs):
                utility.screen_manager.current = name

            if utility.screen_manager.current == 'CreateServerVersionScreen':

                def check_version(*args, **kwargs):
                    break_loop = False
                    for item in utility.screen_manager.current_screen.children:
                        if break_loop:
                            break
                        for child_item in item.children:
                            if break_loop:
                                break
                            for child in child_item.children:

                                if child.__class__.__name__ == "NextButton":

                                    child.loading(True)
                                    version_data = foundry.search_version(foundry.new_server_info)
                                    foundry.new_server_info['version'] = version_data[1]['version']
                                    foundry.new_server_info['build'] = version_data[1]['build']
                                    foundry.new_server_info['jar_link'] = version_data[3]
                                    child.loading(False)
                                    Clock.schedule_once(functools.partial(child.update_next, version_data[0], version_data[2]), 0)

                                    # Continue to next screen if valid input, and back button not pressed
                                    if version_data[0] and not version_data[2] and utility.screen_manager.current == 'CreateServerVersionScreen':
                                        Clock.schedule_once(functools.partial(change_screen, specific_screen), 0)

                                    break_loop = True
                                    break

                timer = dTimer(0, function=check_version)
                timer.start()  # Checks for potential crash

            elif utility.screen_manager.current == 'CreateServerOptionsScreen':
                if not foundry.new_server_info['acl_object']:
                    while not foundry.new_server_info['acl_object']:
                        time.sleep(0.2)
                change_screen(specific_screen)

            else:
                change_screen(specific_screen)

            if utility.screen_manager.current.startswith('CreateServer'): send_log('CreateServer', f"menu progress:\n{foundry.new_server_info}", 'info')

        # Main menu reconnect button
        elif "no connection" in button_name.lower():
            try:
                constants.check_app_updates()
                foundry.find_latest_mc()
            except:
                pass
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
                                if len(addon.name) < 26:
                                    addon_name = addon.name
                                else:
                                    addon_name = addon.name[:23] + "..."

                                banner_text = f"Added '${addon_name}$' to the queue"
                            else:
                                banner_text = f"Added ${len(selection)}$ add-ons to the queue"

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
                                if len(addon.name) < 26:
                                    addon_name = addon.name
                                else:
                                    addon_name = addon.name[:23] + "..."

                                banner_text = f"Imported '${addon_name}$'"
                            else:
                                banner_text = f"Imported ${len(selection)}$ add-ons"

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
                                if len(script.title) < 26:
                                    script_name = script.title
                                else:
                                    script_name = script.title[:23] + "..."

                                banner_text = f"Imported '${script_name}$'"
                            else:
                                banner_text = f"Imported ${len(selection)}$ scripts"

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
