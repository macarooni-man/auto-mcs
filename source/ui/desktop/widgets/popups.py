from source.ui.desktop.widgets.banners import BannerObject
from source.ui.desktop.widgets.inputs import BaseInput
from source.ui.desktop.widgets.base import *



# --------------------------------------------  Base Popup Functionality  ----------------------------------------------

# 0-10: Higher int is blurrier (originally 5 in old versions)
popup_blur_amount: int     = 7

# 0-1:  Smaller float makes the background darker
popup_blur_darkness: float = 0.9


# Normal bite-sized popup menu
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
        if self.shown: Clock.schedule_once(self.generate_blur_background, 0.1)


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
        else: delete()


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


# Big oversized SMELLY window
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

                else: check_body_button()


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
                elif self.body_button: check_body_button()


    def resize(self):
        self.window.size = self.window_background.size
        self.window.pos = (Window.size[0]/2 - self.window_background.width/2, Window.size[1]/2 - self.window_background.height/2)
        if self.shown: Clock.schedule_once(self.generate_blur_background, 0.1)


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
        else: delete()


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



# ---------------------------------------------  Purpose-specific Popups  ----------------------------------------------

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

            else: self.close_pair()

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

        if self.is_modpack: self.window_content.max_lines = 15 # Cuts off the beginning of content??
        else:               self.window_content.max_lines = 13 if self.installed else 14  # Cuts off the beginning of content??


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
            if self.installed: self.window.add_widget(self.installed_banner)

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



# ----------------------------------------------  Global App Search Bar  -----------------------------------------------

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
                    if self.search_obj._telepath_data: open_remote_server(self.search_obj._telepath_data, self.search_obj._telepath_data['name'])
                    else:                              open_server(self.search_obj.title)

                # Otherwise, launch web URL or go to screen
                elif self.search_obj.target:
                    if self.search_obj.target.startswith('http'):
                        webbrowser.open_new_tab(self.search_obj.target)
                    else: utility.screen_manager.current = self.search_obj.target

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

            try: animate = search_obj.title != self.title.text
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

                    else: Animation(opacity=0, duration=0.13).start(button)


    def resize(self):
        self.window.size = self.window_background.size

        # Shift the popup upward at smaller window heights
        offset_y = 0
        if Window.size[1] < 900: offset_y = 75
        if Window.size[1] < 800: offset_y = 100

        # Add offset_y to the original y-position
        self.window.pos = (
            Window.size[0] / 2 - self.window_background.width / 2,
            Window.size[1] / 2 - self.window_background.height / 2 + offset_y
        )

        if self.shown: Clock.schedule_once(self.generate_blur_background, 0.1)


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
        else: delete()


    # Generate search results when typing
    def on_search(self, force=None, fun_anim=False, *a):

        # Set lock for a timeout
        if not self.search_lock and (self.window_input.text or force):
            self.search_lock = True

            # Update results with query
            if force: self.search_text = force
            else:     self.search_text = self.window_input.text

            try:
                results = constants.search_manager.execute_search(utility.screen_manager.current, self.search_text)

                complete_list = [results['guide']]
                complete_list.extend(results['server'])
                complete_list.extend(results['setting'])
                complete_list.extend(results['screen'])
                complete_list = tuple(sorted(complete_list, key=lambda x: x.score, reverse=True))

                for x, button in enumerate(reversed(self.results.children), 0):
                    if fun_anim: Clock.schedule_once(functools.partial(button.refresh_data, complete_list[x], True), (x*0.1))
                    else: button.refresh_data(complete_list[x])

            except: pass

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
        if screen_name == 'MainMenuScreen':     query = 'getting started'
        elif screen_name == 'ServerViewScreen': query = 'help server manager'
        elif 'Acl' in screen_name:              query = 'help access control'
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
