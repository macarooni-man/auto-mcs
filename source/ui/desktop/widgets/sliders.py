from source.ui.desktop.widgets.base import *



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
                    except: pass

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
