from source.ui.desktop.widgets.base import *



# ----------------------------------------  Notification Banner Functionality  -----------------------------------------

# Banner layout with random ID to prevent collisions
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
