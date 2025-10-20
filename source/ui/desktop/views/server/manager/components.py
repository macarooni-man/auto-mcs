from source.ui.desktop.views.templates import *
from source.ui.desktop.widgets.base import *
from source.ui.desktop.utility import *
from source.ui.desktop import utility



# =============================================== Server Manager =======================================================
# <editor-fold desc="Server Manager">

# Server Manager Overview ----------------------------------------------------------------------------------------------

class ServerButton(HoverButton):
    class ParagraphLabel(Label, HoverBehavior):

        def on_mouse_pos(self, *args):

            if "ServerViewScreen" in utility.screen_manager.current_screen.name and self.copyable:
                try: super().on_mouse_pos(*args)
                except: pass

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
                def click(*a):
                    clipboard_text = re.sub(r"\[.*?\]", "", self.text.split(" ")[-1].strip())
                    if self.parent.button_pressed == "left":
                        banner_text = "Copied IP address  (right-click for LAN)"

                    else:
                        server_obj = self.parent.properties
                        if server_obj.running:
                            clipboard_text = server_obj.run_data['network']['private_ip'] + ':' + server_obj.run_data['network']['address']['port']

                        banner_text = "Copied LAN IP address  (left-click for public)"

                    Clock.schedule_once(
                        functools.partial(
                            utility.screen_manager.current_screen.show_banner,
                            (0.85, 0.65, 1, 1),
                            banner_text,
                            "link-sharp.png",
                            2,
                            {"center_x": 0.5, "center_y": 0.965}
                        ), 0
                    )

                    Clipboard.copy(clipboard_text)

                Clock.schedule_once(click, 0)

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

    class ChangeIconButton(Button, HoverBehavior):

        # Show menu to replace icon
        def on_click(self, *a):

            def apply_new_icon(path: str = None, *a):
                def do_change():
                    icon_path = False

                    # Upload to remote if Telepath
                    if path:
                        if self.server_obj._telepath_data:
                            icon_path = constants.telepath_upload(self.server_obj._telepath_data, path)['path']
                        else:
                            icon_path = path
                    success, message = self.server_obj.update_icon(icon_path)

                    # Reload page
                    if success:

                        # Override for Telepath
                        if self.server_obj._telepath_data:
                            manager.get_server_icon(self.server_obj.name, self.server_obj._telepath_data, overwrite=True)

                        # Remove the cached image and texture
                        Cache.remove('kv.image')
                        Cache.remove('kv.texture')
                        [os.remove(item) for item in glob(os.path.join(paths.ui_assets, 'live', 'blur_icon_*.png'))]

                    return success, message

                def loading_screen(*a): utility.screen_manager.current = 'BlurredLoadingScreen'
                Clock.schedule_once(loading_screen, 0)

                # Actually rename the server files
                time.sleep(0.5)
                success, message = do_change()

                # Change header and footer text to reflect change
                def reload_page(*a):
                    def go_back(*a): utility.screen_manager.current = 'ServerViewScreen'
                    Clock.schedule_once(go_back, 0)

                    # Display banner to show success
                    Clock.schedule_once(
                        functools.partial(
                            utility.screen_manager.current_screen.show_banner,
                            (0.553, 0.902, 0.675, 1) if success else (1, 0.5, 0.65, 1),
                            message,
                            "checkmark-circle-sharp.png" if success else "close-circle-sharp.png",
                            3,
                            {"center_x": 0.5, "center_y": 0.965}
                        ), 0.1
                    )

                Clock.schedule_once(reload_page, 0)

            # Add icon with left click
            if self.last_touch.button == 'left':
                title = "Select an image"
                selection = file_popup("file", start_dir=paths.user_downloads, ext=constants.valid_image_formats, input_name=None, select_multiple=False, title=title)
                if selection and selection[0]: dTimer(0, functools.partial(apply_new_icon, selection[0])).start()

            # Delete icon with right click
            elif self.last_touch.button == 'right' and self.is_custom:

                Clock.schedule_once(
                    functools.partial(
                        utility.screen_manager.current_screen.show_popup,
                        "warning_query",
                        'Remove Icon',
                        "Do you want to remove this icon?\n\nYou'll need to re-import it again later",
                        (None, functools.partial(dTimer(0, apply_new_icon).start))
                    ),
                    0
                )

        def on_enter(self, *args):
            Animation.stop_all(self)
            Animation.stop_all(self.type_image)
            Animation(opacity=1, duration=self.anim_duration).start(self)
            Animation(opacity=0, duration=self.anim_duration).start(self.type_image.image)
            if self.server_obj._telepath_data:
                Animation(opacity=0, duration=self.anim_duration).start(self.type_image.tp_shadow)
                Animation(opacity=0, duration=self.anim_duration).start(self.type_image.tp_icon)

        def on_leave(self, *args):
            Animation.stop_all(self)
            Animation.stop_all(self.type_image)
            Animation(opacity=0, duration=self.anim_duration).start(self)
            Animation(opacity=1, duration=self.anim_duration).start(self.type_image.image)
            if self.server_obj._telepath_data:
                Animation(opacity=1, duration=self.anim_duration).start(self.type_image.tp_shadow)
                Animation(opacity=1, duration=self.anim_duration).start(self.type_image.tp_icon)

        def generate_blur_background(self, *args):
            def run_in_foreground(*a):
                self.blur_background.source = image_path
                self.canvas.ask_update()

            try:
                # Attempt to remove existing icon temp, who even cares lol
                for item in glob(os.path.join(paths.ui_assets, 'live', 'blur_icon_*.png')):
                    if self.server_obj.name in item:
                        image_path = item
                        return run_in_foreground()
                    os.remove(item)
            except: pass
            image_path = os.path.join(paths.ui_assets, 'live', f'blur_icon_{self.server_obj.name}_{constants.gen_rstring(4)}.png')
            constants.folder_check(os.path.join(paths.ui_assets, 'live'))

            self.type_image.image.export_to_png(image_path)

            # Convert the image in the background
            def convert(*a):
                im = PILImage.open(image_path)

                # Center and resize icon when custom
                if self.is_custom:
                    im = im.convert('RGBA')
                    left = 4
                    upper = (im.height - 65)
                    right = left + 65
                    lower = upper + 65
                    im = im.crop((left, upper, right, lower))

                # Blur and darken the icon
                im = ImageEnhance.Brightness(im)
                im = im.enhance(0.75)
                im1 = im.filter(GaussianBlur(3))

                im1.save(image_path)

                Clock.schedule_once(run_in_foreground, 0)

            dTimer(0, convert).start()

        def resize_self(self, *a):
            for child in self.children: child.pos = self.pos
            offset = (self.pos[0] + 17.5, self.pos[1] + 16.5)
            self.background_ellipse.pos = offset
            self.blur_background.pos = offset
            self.background_outline.ellipse = (*offset, 66, 66)

        def __init__(self, type_image, **kwargs):
            super().__init__(**kwargs)
            self.type_image = type_image
            self.size_hint_max = self.type_image.image.size
            self.is_custom = self.type_image.image.__class__.__name__ == 'CustomServerIcon'
            self.background_normal = os.path.join(paths.ui_assets, 'empty.png')
            self.background_down = os.path.join(paths.ui_assets, 'empty.png')
            self.anim_duration = 0.1
            self.fg = self.type_image.version_label.color
            self.bc = constants.brighten_color(constants.background_color, -0.1)
            self.server_obj = constants.server_manager.current_server

            with self.canvas.before:
                # Background ellipse (drawn first)
                Color(self.bc[0], self.bc[1], self.bc[2], 0.3)  # Adjust alpha as needed
                self.background_ellipse = Ellipse(
                    size = (66, 66),
                    angle_start = 0,
                    angle_end = 360
                )

            with self.canvas:
                # Blur background ellipse (drawn after background ellipse)
                Color(*self.fg)
                self.blur_background = Ellipse(
                    size = (66, 66),
                    angle_start = 0,
                    angle_end = 360
                )

                # Outline of the ellipse
                Color(*self.fg[:3], 0.0)
                self.background_outline = Line(
                    ellipse = (0, 0, 66, 66),
                    width = 2
                )

            self.shadow = Image(source=icon_path('shadow.png'), color="#111122")
            self.shadow.opacity = 0.5
            self.icon = Image(source=icon_path('pencil-sharp.png'), color=constants.brighten_color(self.fg, 0.15))
            self.add_widget(self.shadow)
            self.add_widget(self.icon)

            # Bind and initialize
            self.bind(size=self.resize_self, pos=self.resize_self)
            self.bind(on_press=self.on_click)
            self.generate_blur_background()
            self.opacity = 0

    def toggle_favorite(self, favorite, *args):
        self.favorite = favorite
        self.color_id = [(0.05, 0.05, 0.1, 1), constants.brighten_color((0.85, 0.6, 0.9, 1) if self.favorite else (0.65, 0.65, 1, 1), 0.07)]
        self.title.text_size = (self.size_hint_max[0] * (0.7 if favorite else 0.94), self.size_hint_max[1])
        self.background_normal = os.path.join(paths.ui_assets, f'{self.id}{"_favorite" if self.favorite else ""}.png')
        self.resize_self()
        return favorite

    def animate_button(self, image, color, hover_action, **kwargs):
        image_animate = Animation(duration=0.05)

        Animation(color=color, duration=0.06).start(self.title)
        Animation(color=self.run_color if (self.running and not self.hovered) else color, duration=0.06).start(self.subtitle)

        if not self.custom_icon:
            Animation(color=color, duration=0.06).start(self.type_image.image)

        if self.type_image.version_label.__class__.__name__ == "AlignLabel":
            Animation(color=color, duration=0.06).start(self.type_image.version_label)

        Animation(color=color, duration=0.06).start(self.type_image.type_label)

        animate_background(self, image, hover_action)

        image_animate.start(self)

    def resize_self(self, *args):

        # Title and description
        padding = 2.17
        self.title.pos = (
        self.x + (self.title.text_size[0] / padding) - (5.3 if self.favorite else 8.3) + 30, self.y + 31)
        self.subtitle.pos = (self.x + (self.subtitle.text_size[0] / padding) - 78, self.y + 8)

        offset = 9.45 if self.type_image.type_label.text in ["vanilla", "paper", "purpur"] \
            else 9.6 if self.type_image.type_label.text == "forge" \
            else 9.35 if self.type_image.type_label.text == "craftbukkit" \
            else 9.55

        self.type_image.image.x = self.width + self.x - (self.type_image.image.width) - 13
        self.type_image.image.y = self.y + ((self.height / 2) - (self.type_image.image.height / 2))

        # Telepath icon
        if self.telepath_data:
            self.type_image.tp_shadow.pos = (self.type_image.image.x - 2, self.type_image.image.y)
            self.type_image.tp_icon.pos = (self.type_image.image.x - 2, self.type_image.image.y)

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

        # Change Icon button pos
        if self.icon_button:
            half = self.type_image.image.size_hint_max[0] / 4
            offset = 2.5 if self.type_image.image.__class__.__name__ == 'CustomServerIcon' else -1
            self.icon_button.pos = (self.type_image.image.x - half + offset, self.type_image.image.y - half)

        # Highlight border
        self.highlight_border.pos = self.pos

    def highlight(self):
        def next_frame(*args):
            Animation.stop_all(self.highlight_border)
            self.highlight_border.opacity = 1
            Animation(opacity=0, duration=0.7).start(self.highlight_border)

        Clock.schedule_once(next_frame, 0)

    def update_subtitle(self, run_data=None, last_modified=None):

        def reset(*a):
            self.running = False
            self.subtitle.copyable = False
            if last_modified: self.original_subtitle = backup.convert_date(last_modified)
            self.subtitle.color = self.color_id[1]
            self.subtitle.default_opacity = 0.56
            self.subtitle.font_name = self.original_font
            self.subtitle.text = self.original_subtitle

        try:
            if run_data:
                self.running = True
                self.subtitle.copyable = True
                self.subtitle.color = self.run_color
                self.subtitle.default_opacity = 0.8
                self.subtitle.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')

                if run_data.get('playit-tunnel', None) or 'ply.gg' in run_data['network']['address']['ip']:
                    text = run_data['network']['address']['ip']
                else:
                    text = ':'.join(run_data['network']['address'].values())

                self.subtitle.text = f"[font={self.icons}]N[/font]  {text.replace('127.0.0.1', 'localhost')}"

            else: reset()
        except KeyError: reset()

        self.subtitle.opacity = self.subtitle.default_opacity

    def generate_name(self, color='#7373A2'):
        if self.telepath_data:
            tld = self.telepath_data['host']
            if self.telepath_data['nickname']: tld = self.telepath_data['nickname']
            return f'[color={color}]{tld}/[/color]{self.properties.name}'
        else: return self.properties.name.strip()

    def __init__(self, server_object, click_function=None, fade_in=0.0, highlight=None, update_banner="", view_only=False, **kwargs):
        super().__init__(**kwargs)

        # Check if server is remote
        self.telepath_data = server_object._telepath_data

        self.view_only = view_only

        if self.view_only: self.ignore_hover = True

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
            self.background_normal = os.path.join(paths.ui_assets, f'{self.id}.png')
            self.background_down = os.path.join(paths.ui_assets, f'{self.id}{"_favorite" if self.favorite else ""}_click.png')
        else:
            self.background_normal = os.path.join(paths.ui_assets, f'{self.id}_ro.png')
            self.background_down = os.path.join(paths.ui_assets, f'{self.id}{"_favorite" if self.favorite else "_ro"}.png')

        self.icons = os.path.join(paths.ui_assets, 'fonts', constants.fonts['icons'])

        # Loading stuffs
        self.original_subtitle = backup.convert_date(server_object.last_modified)
        self.original_font = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["regular"]}.ttf')

        # Title of Server
        self.title = Label()
        self.title.__translate__ = False
        self.title.id = "title"
        self.title.halign = "left"
        self.title.color = self.color_id[1]
        self.title.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
        self.title.font_size = sp(25)
        self.title.text_size = (self.size_hint_max[0] * 0.58, self.size_hint_max[1])
        self.title.shorten = True
        self.title.markup = True
        self.title.shorten_from = "right"
        self.title.max_lines = 1
        self.title.text = self.generate_name()
        self.add_widget(self.title)

        # Server last modified date formatted
        if self.view_only: self.subtitle = self.ParagraphLabel()
        else:              self.subtitle = Label()
        self.subtitle.__translate__ = False
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
        self.subtitle.text_size[0] = 350

        if self.running:
            self.subtitle.copyable = True
            self.subtitle.color = self.run_color
            self.subtitle.default_opacity = 0.8
            self.subtitle.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')

            if server_object.run_data.get('playit-tunnel', None) or 'ply.gg' in server_object.run_data['network']['address']['ip']:
                text = server_object.run_data['network']['address']['ip']
            else:
                text = ':'.join(server_object.run_data['network']['address'].values())

            self.subtitle.text = f"[font={self.icons}]N[/font]  {text.replace('127.0.0.1', 'localhost')}"

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

        # Check for custom server icon
        if self.telepath_data:
            self.telepath_data['icon-path'] = server_object.server_icon
            self.server_icon = manager.get_server_icon(server_object.name, self.telepath_data)
        else:
            self.server_icon = server_object.server_icon

        if self.server_icon:
            self.custom_icon = True

            class CustomServerIcon(RelativeLayout):
                def __init__(self, server_icon, **kwargs):
                    super().__init__(**kwargs)
                    with self.canvas:
                        Color(1, 1, 1, 1)  # Set the color to white
                        self.shadow = Ellipse(pos=(-23.5, -27.5), size=(120, 120), source=os.path.join(paths.ui_assets, 'icon_shadow.png'), angle_start=0, angle_end=360)
                        self.ellipse = Ellipse(pos=(4, 0), size=(65, 65), source=server_icon, angle_start=0, angle_end=360)

            self.type_image.image = CustomServerIcon(self.server_icon)

        else:
            self.custom_icon = False
            self.server_icon = os.path.join(paths.ui_assets, 'icons', 'big', f'{server_object.type.lower()}_small.png')
            self.type_image.image = Image(source=self.server_icon)

        self.type_image.image.allow_stretch = True
        self.type_image.image.size_hint_max = (65, 65)
        self.type_image.image.color = self.color_id[1]
        self.type_image.add_widget(self.type_image.image)

        # Show icon on self.type_image to specify
        if self.telepath_data:
            self.type_image.tp_shadow = Image(source=icon_path('shadow.png'))
            self.type_image.tp_shadow.allow_stretch = True
            self.type_image.tp_shadow.size_hint_max = (33, 33)
            self.type_image.tp_shadow.color = self.color_id[0]
            self.type_image.add_widget(self.type_image.tp_shadow)

            self.type_image.tp_icon = Image(source=icon_path('telepath.png'))
            self.type_image.tp_icon.allow_stretch = True
            self.type_image.tp_icon.size_hint_max = (33, 33)
            self.type_image.tp_icon.color = self.color_id[1]
            self.type_image.add_widget(self.type_image.tp_icon)
        else:
            self.type_image.tp_shadow = None
            self.type_image.tp_icon = None

        def TemplateLabel():
            template_label = AlignLabel()
            template_label.__translate__ = False
            template_label.halign = "right"
            template_label.valign = "middle"
            template_label.text_size = template_label.size
            template_label.font_size = sp(19)
            template_label.color = self.color_id[1]
            template_label.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
            template_label.width = 150
            return template_label

        if update_banner:
            self.type_image.version_label = RelativeLayout()
            self.type_image.version_label.add_widget(
                BannerObject(
                    pos_hint = {"center_x": 1, "center_y": 0.5},
                    size = (100, 30),
                    color = (0.647, 0.839, 0.969, 1),
                    text = ('   ' + update_banner + '  ') if update_banner.startswith('b-') else update_banner,
                    icon = "arrow-up-circle.png",
                    icon_side = "left"
                )
            )

        else:
            self.type_image.version_label = TemplateLabel()
            self.type_image.version_label.text = server_object.version.lower()
            self.type_image.version_label.opacity = 0.6

        self.type_image.version_label.color = self.color_id[1]
        self.type_image.type_label = TemplateLabel()


        # Say modpack if such
        if self.properties.is_modpack: type_text = 'modpack'
        else:                          type_text = server_object.type.lower().replace("craft", "")

        self.type_image.type_label.text = type_text
        self.type_image.type_label.font_size = sp(23)
        self.type_image.add_widget(self.type_image.version_label)
        self.type_image.add_widget(self.type_image.type_label)
        self.add_widget(self.type_image)

        # Favorite button
        self.favorite_layout = RelativeLayout()
        favorite = None
        if not view_only:
            self.icon_button = None
            try: favorite = functools.partial(utility.screen_manager.current_screen.favorite, server_object.name, server_object)
            except AttributeError: pass

        else:
            self.icon_button = self.ChangeIconButton(self.type_image)
            self.add_widget(self.icon_button)

        if self.favorite: self.favorite_button = IconButton('', {}, (0, 0), (None, None), 'heart-sharp.png', clickable=not self.view_only, force_color=[[(0.05, 0.05, 0.1, 1), (0.85, 0.6, 0.9, 1)], 'pink'], anchor='right', click_func=favorite)
        else:             self.favorite_button = IconButton('', {}, (0, 0), (None, None), 'heart-outline.png', clickable=not self.view_only, anchor='right', click_func=favorite)

        self.favorite_layout.add_widget(self.favorite_button)
        self.add_widget(self.favorite_layout)

        # Highlight border
        self.highlight_layout = RelativeLayout()
        self.highlight_border = Image()
        self.highlight_border.keep_ratio = False
        self.highlight_border.allow_stretch = True
        self.highlight_border.color = constants.brighten_color(self.color_id[1], 0.1)
        self.highlight_border.opacity = 0
        self.highlight_border.source = os.path.join(paths.ui_assets, 'server_button_highlight.png')
        self.highlight_layout.add_widget(self.highlight_border)
        self.highlight_layout.width = self.size_hint_max[0]
        self.highlight_layout.height = self.size_hint_max[1]
        self.add_widget(self.highlight_layout)

        # Toggle favorite stuffies
        self.bind(pos=self.resize_self)
        if self.favorite: self.toggle_favorite(self.favorite)

        # If click_function
        if click_function and not view_only: self.bind(on_press=click_function)

        # Animate opacity
        if fade_in > 0:
            self.opacity = 0
            self.title.opacity = 0

            Animation(opacity=1, duration=fade_in).start(self)
            Animation(opacity=1, duration=fade_in).start(self.title)
            Animation(opacity=self.subtitle.default_opacity, duration=fade_in).start(self.subtitle)

        if highlight: self.highlight()

    def on_enter(self, *args):
        if not self.ignore_hover:
            self.animate_button(image=os.path.join(paths.ui_assets, f'{self.id}{"_favorite" if self.favorite else ""}_hover.png'), color=self.color_id[0], hover_action=True)

            self.title.text = self.generate_name('#2D2D4E')

            if self.telepath_data:
                new_color = constants.convert_color('#E865D4' if self.favorite else '#6769D9')['rgb']
                Animation(color=new_color, duration=0.1).start(self.type_image.tp_shadow)
                Animation(color=constants.brighten_color(self.color_id[0], -0.1), duration=0.1).start(self.type_image.tp_icon)

    def on_leave(self, *args):
        if not self.ignore_hover:
            self.animate_button(image=os.path.join(paths.ui_assets, f'{self.id}{"_favorite" if self.favorite else ""}.png'), color=self.color_id[1], hover_action=False)

            self.title.text = self.generate_name()

            if self.telepath_data:
                Animation(color=self.color_id[0], duration=0.1).start(self.type_image.tp_shadow)
                Animation(color=self.color_id[1], duration=0.1).start(self.type_image.tp_icon)

    def update_context_options(self):
        def _open_server(name):
            if self.telepath_data:
                constants.api_manager.request(
                    endpoint = f'/main/open_remote_server?name={constants.quote(name)}',
                    host = self.telepath_data['host'],
                    port = self.telepath_data['port'],
                    args = {'none': None}
                )
                new_data = constants.deepcopy(self.telepath_data)
                new_data['name'] = name
                return constants.server_manager._init_telepathy(new_data)

            else: return constants.server_manager.open_server(name)

        # Functions for context menu
        def launch(*a):
            if self.telepath_data: open_remote_server(self.telepath_data, self.properties.name, launch=True)
            else:                  open_server(self.properties.name, launch=True)

        def restart(*a): _open_server(self.properties.name).restart()
        def stop(*a):    _open_server(self.properties.name).stop()

        def settings(*a):
            _open_server(self.properties.name)
            utility.screen_manager.current = 'ServerSettingsScreen'

        def update(*a):
            settings()
            utility.screen_manager.current_screen.update_button.button.trigger_action()

        def rename(*a):
            settings()
            rename_input = utility.screen_manager.current_screen.rename_input
            utility.screen_manager.current_screen.scroll_widget.scroll_to(rename_input)
            Clock.schedule_once(rename_input.grab_focus, 0.2)

        def delete(*a):
            settings()
            delete_button = utility.screen_manager.current_screen.delete_button
            utility.screen_manager.current_screen.scroll_widget.scroll_to(delete_button, animate=False)
            Clock.schedule_once(delete_button.button.trigger_action, 0.1)

        def copy_ip(local, *a):
            def click(*a):
                clipboard_text = re.sub(r"\[.*?\]", "", self.subtitle.text.split(" ")[-1].strip())
                if not local: banner_text = "Copied IP address"

                else:
                    server_obj = self.properties
                    if server_obj.running: clipboard_text = server_obj.run_data['network']['private_ip'] + ':' + server_obj.run_data['network']['address']['port']
                    banner_text = "Copied LAN IP address"

                Clock.schedule_once(
                    functools.partial(
                        utility.screen_manager.current_screen.show_banner,
                        (0.85, 0.65, 1, 1),
                        banner_text,
                        "link-sharp.png",
                        2,
                        {"center_x": 0.5, "center_y": 0.965}
                    ), 0
                )

                Clipboard.copy(clipboard_text)

            Clock.schedule_once(click, 0)

        # Context menu buttons
        if self.view_only and self.properties.running:
            self.context_options = [
                {'name': 'Copy local IP', 'icon': 'ethernet.png', 'action': functools.partial(copy_ip, True)},
                {'name': 'Copy public IP', 'icon': 'wifi.png', 'action': functools.partial(copy_ip, False)}
            ]
        else:
            if self.properties.running:
                self.context_options = [
                    {'name': 'Restart', 'icon': 'restart-server.png', 'action': restart},
                    {'name': 'Stop', 'icon': 'stop-server.png', 'action': stop},
                    {'name': 'Copy IP', 'icon': 'wifi-sharp.png', 'action': functools.partial(copy_ip, False)},
                    {'name': 'Settings', 'icon': os.path.join('sm', 'advanced.png'), 'action': settings}
                ]
            else:
                if self.properties.is_modpack == 'zip': u = None
                else:                                   u = self.properties.update_string
                self.context_options = [
                    {'name': 'Launch', 'icon': 'start-server.png', 'action': launch} if utility.screen_manager.current_screen.name != "ServerViewScreen" else None,
                    {'name': f'Update {"build" if u.startswith("b-") else f"{u}"}', 'icon': 'arrow-up.png', 'action': update} if u else None,
                    {'name': 'Rename', 'icon': 'rename.png', 'action': rename},
                    {'name': 'Settings', 'icon': os.path.join('sm', 'advanced.png'), 'action': settings},
                    {'name': 'Delete', 'icon': 'trash-sharp.png', 'action': delete, 'color': 'red'}
                ]


class ServerManagerScreen(MenuBackground):

    # Toggles favorite of item, and reload list
    def favorite(self, server_name, properties):
        if properties._telepath_data:
            properties.toggle_favorite()
            bool_favorite = properties.favorite
        else: bool_favorite = manager.toggle_favorite(server_name)

        # Show banner
        if server_name in constants.server_manager.running_servers:
            constants.server_manager.running_servers[server_name].favorite = bool_favorite

        if bool_favorite: banner_message = f"'${server_name}$' marked as favorite"
        else:             banner_message = f"'${server_name}$' is no longer marked as favorite"

        Clock.schedule_once(
            functools.partial(
                utility.screen_manager.current_screen.show_banner,
                (0.85, 0.65, 1, 1) if bool_favorite else (0.68, 0.68, 1, 1),
                banner_message,
                "heart-sharp.png" if bool_favorite else "heart-dislike-outline.png",
                2,
                {"center_x": 0.5, "center_y": 0.965}
            ), 0
        )

        constants.server_manager.refresh_list()
        self.gen_search_results(constants.server_manager.menu_view_list, fade_in=False, highlight=properties._view_name)

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

        # Set to proper page on favorite/un-favorite
        default_scroll = 1
        if highlight:
            def divide_chunks(l, n):
                final_list = []

                for i in range(0, len(l), n):
                    final_list.append(l[i:i + n])

                return final_list

            for x, l in enumerate(divide_chunks([x._view_name for x in results], self.page_size), 1):
                if highlight in l:
                    if self.current_page != x:
                        self.current_page = x

                    # Update scroll when page is bigger than list
                    if Window.height < self.scroll_layout.height:
                        default_scroll = 1 - round(l.index(highlight) / len(l), 2)
                        if default_scroll < 0.2:  default_scroll = 0
                        if default_scroll > 0.97: default_scroll = 1
                    break

        # Update page counter
        self.last_results = results
        self.max_pages = (len(results) / self.page_size).__ceil__()
        self.current_page = 1 if self.current_page == 0 or new_search else self.current_page

        self.page_switcher.update_index(self.current_page, self.max_pages)
        page_list = results[(self.page_size * self.current_page) - self.page_size:self.page_size * self.current_page]

        self.scroll_layout.clear_widgets()

        # Generate header
        server_count = len(constants.server_manager.menu_view_list)
        header_content = "Select a server to manage"

        for child in self.header.children:
            if child.id == "text":
                child.text = header_content
                break

        # Show servers if they exist
        if server_count != 0:

            # Clear and add all ServerButtons
            for x, server_obj in enumerate(page_list, 1):

                # Activated when server is clicked
                def view_server(server, index, *args):
                    selected_button = [item for item in self.scroll_layout.walk() if item.__class__.__name__ == "ServerButton"][index - 1]

                    # View Server
                    if selected_button.last_touch.button == "left":
                        if not selected_button.telepath_data: open_server(server.name, ignore_update=False)
                        else:                                 open_remote_server(selected_button.telepath_data, server.name, ignore_update=False)

                    # Favorite
                    elif selected_button.last_touch.button == "middle": self.favorite(server.name)

                # Check if updates are available
                update_banner = ""
                if server_obj.auto_update == 'true': update_banner = server_obj.update_string

                # Add-on button click function
                self.scroll_layout.add_widget(
                    ScrollItem(
                        widget = ServerButton(
                            server_object=server_obj,
                            fade_in = ((x if x <= 8 else 8) / self.anim_speed) if fade_in else 0,
                            highlight = (highlight == server_obj._view_name),
                            update_banner = update_banner,
                            click_function = functools.partial(
                                view_server,
                                server_obj,
                                x
                            )
                        )
                    )
                )

            self.resize_bind()

        # Go back to main menu if they don't
        else:
            utility.screen_manager.current = 'MainMenuScreen'
            utility.screen_manager.screen_tree = []
            return

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
        if keycode[1] in ['right', 'left'] and self.name == utility.screen_manager.current_screen.name:
            self.switch_page(keycode[1])

    def generate_menu(self, **kwargs):

        # Scroll list
        scroll_widget = ScrollViewWidget(position=(0.5, 0.48))
        scroll_anchor = AnchorLayout()
        self.scroll_layout = GridLayout(cols=1, spacing=15, size_hint_max_x=1250, size_hint_y=None, padding=[0, 30, 0, 30])

        # Bind / cleanup height on resize
        def resize_scroll(call_widget, grid_layout, anchor_layout, *args):
            call_widget.height = Window.height // 1.82
            grid_layout.cols = 2 if Window.width > grid_layout.size_hint_max_x else 1
            self.anim_speed = 13 if Window.width > grid_layout.size_hint_max_x else 10

            def update_grid(*args):
                anchor_layout.size_hint_min_y = grid_layout.height
                scroll_top.resize(); scroll_bottom.resize()

            Clock.schedule_once(update_grid, 0)

        self.resize_bind = lambda *_: Clock.schedule_once(functools.partial(resize_scroll, scroll_widget, self.scroll_layout, scroll_anchor), 0)
        self.resize_bind()
        Window.bind(on_resize=self.resize_bind)
        self.scroll_layout.bind(minimum_height=self.scroll_layout.setter('height'))
        self.scroll_layout.id = 'scroll_content'

        # Scroll gradient
        scroll_top = ScrollBackground(pos_hint={"center_x": 0.5, "center_y": 0.755}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, 60))
        scroll_bottom = ScrollBackground(pos_hint={"center_x": 0.5, "center_y": 0.22}, pos=scroll_widget.pos, size=(scroll_widget.width // 1.5, -60))

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

        buttons.append(ExitButton('Back', (0.5, 0.12), cycle=True))

        for button in buttons: float_layout.add_widget(button)

        menu_name = "Server Manager"
        float_layout.add_widget(generate_title("Server Manager"))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)

        # Automatically generate results on page load
        constants.server_manager.refresh_list()
        highlight = False
        self.gen_search_results(constants.server_manager.menu_view_list)

        # Highlight the last server that was last selected
        def highlight_last_server(*args):
            server_obj = constants.server_manager.current_server
            if server_obj:
                highlight = server_obj._view_name
                self.gen_search_results(constants.server_manager.menu_view_list, highlight=highlight, animate_scroll=False)

        Clock.schedule_once(highlight_last_server, 0)


class MenuTaskbar(RelativeLayout):

    def resize(self, *args):

        # Resize background
        self.bg_left.x = 0
        self.bg_right.x = self.width
        self.bg_center.x = 0 + self.bg_left.width
        self.bg_center.size_hint_max_x = self.width - (self.bg_left.width * 2)

    def show_notification(self, tile_name, show=True):
        for tile in self.taskbar.children:
            if tile_name == tile.name:
                tile.show_notification(show=show)
                break

    def __init__(self, selected_item=None, animate=False, **kwargs):
        super().__init__(**kwargs)

        server_obj = constants.server_manager.current_server

        show_addons = (server_obj.type != 'vanilla')
        server_obj.taskbar = self
        self.pos_hint = {"center_x": 0.5}

        # Layout for icon object
        class TaskbarItem(RelativeLayout):

            def show_notification(self, show=True, animate=True):
                if animate:
                    Animation(opacity=(1 if show else 0), duration=0.25, transition='in_out_sine').start(self.notification)

                    def fade_in(*a): Animation(opacity=(0.5 if show else 0), duration=0.15, transition='in_out_sine').start(self.notification_glow)
                    Clock.schedule_once(fade_in, 0.1)
                    def fade_out(*a): Animation(opacity=0, duration=0.5, transition='in_out_sine').start(self.notification_glow)
                    Clock.schedule_once(fade_out, 0.35)

                else: self.notification.opacity = (1 if show else 0)

            def __init__(self, item_info, selected=False, **kwargs):
                super().__init__(**kwargs)
                new_color = constants.convert_color(item_info[2])['rgb']
                self.name = item_info[0]

                # Icon and listed functions
                class Icon(AnchorLayout, HoverBehavior):

                    # Pretty animation if specified
                    def animate(self, *args):
                        def anim_in(*args):
                            Animation(size_hint_max=(self.default_size + 6, self.default_size + 6), duration=0.15, transition='in_out_sine').start(self.icon)
                            if self.selected:
                                Animation(opacity=1, duration=0.3, transition='in_out_sine').start(self.background)
                                Animation(color=constants.brighten_color(self.hover_color, -0.87), duration=0.2, transition='in_out_sine').start(self.icon)

                        def anim_out(*args): Animation(size_hint_max=(self.default_size, self.default_size), duration=0.15, transition='in_out_sine').start(self.icon)
                        Clock.schedule_once(anim_in, 0.1)
                        Clock.schedule_once(anim_out, 0.25)

                    # Execute click function
                    def on_touch_down(self, touch):
                        if self.hovered and not self.selected and not utility.screen_manager.current_screen.popup_widget:

                            # Log for crash info
                            try:
                                interaction = f"TaskbarButton ({self.data[0].title()})"
                                constants.last_widget = interaction + f" @ {constants.format_now()}"
                                send_log('navigation', f"interaction: '{interaction}'")
                            except: pass

                            # Animate button
                            self.icon.color = constants.brighten_color(self.hover_color, 0.2)
                            Animation(color=self.hover_color, duration=0.3).start(self.icon)

                            utility.back_clicked = True

                            # Play yummy sound
                            audio.player.play('interaction/click_*', jitter=(0, 0.15))

                            # Return if back is clicked
                            if self.data[0] == 'back':
                                utility.screen_manager.current = 'ServerManagerScreen'
                                utility.screen_manager.screen_tree = ['MainMenuScreen']


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

                                if self.data[-1] == 'ServerAmscriptScreen':
                                    if not constants.server_manager.current_server.script_manager:
                                        while not constants.server_manager.current_server.script_manager:
                                            time.sleep(0.2)

                                utility.screen_manager.current = self.data[-1]

                            utility.back_clicked = False

                        # If no button is matched, return touch to super
                        else: super().on_touch_down(touch)

                    # Change attributes when hovered
                    def on_enter(self):
                        if self.ignore_hover:
                            return

                        if not self.selected: Animation(size_hint_max=(self.default_size + 6, self.default_size + 6), duration=0.15, transition='in_out_sine', color=self.hover_color).start(self.icon)
                        Animation(opacity=1, duration=0.25, transition='in_out_sine').start(self.parent.text)

                    def on_leave(self):
                        self.ignore_hover = False
                        if not self.selected: Animation(size_hint_max=(self.default_size, self.default_size), duration=0.15, transition='in_out_sine', color=self.default_color).start(self.icon)
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
                            self.background = Image(source=os.path.join(paths.ui_assets, 'icons', 'sm', 'selected.png'))
                            self.background.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
                            self.background.size_hint_max = self.size_hint_max
                            self.background.color = self.hover_color
                            self.add_widget(self.background)
                            if animate: self.background.opacity = 0
                            else:       self.icon.color = constants.brighten_color(self.hover_color, -0.87)

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
                self.text.add_widget(BannerObject(pos_hint={'center_x': 0.5, 'center_y': 0.75}, text=item_info[0], size=(70, 30), color=new_color))
                self.text.pos_hint = {'center_x': 0.5, 'center_y': 1}
                self.text.opacity = 0
                self.add_widget(self.text)

                # Notification icon
                self.notification_glow = Image(source=os.path.join(paths.ui_assets, 'icons', 'sm', 'notification-glow.png'))
                self.notification_glow.opacity = 0
                self.notification_glow.pos_hint = {'center_x': 0.7, 'center_y': 0.7}
                self.notification_glow.size_hint_max = (27, 27)
                self.notification_glow.color = constants.convert_color('#FFC175')['rgb']
                self.add_widget(self.notification_glow)

                self.notification = Image(source=os.path.join(paths.ui_assets, 'icons', 'sm', 'notification.png'))
                self.notification.opacity = 0
                self.notification.pos_hint = {'center_x': 0.7, 'center_y': 0.7}
                self.notification.size_hint_max = (20, 20)
                self.notification.color = constants.convert_color('#FFC175')['rgb']
                self.add_widget(self.notification)

        # Icon list  (name, path, color, next_screen)
        icon_path = os.path.join(paths.ui_assets, 'icons', 'sm')
        self.item_list = [
            ('back', os.path.join(icon_path, 'back-outline.png'), '#FF6FB4'),
            ('launch', os.path.join(icon_path, 'terminal.png'), '#817EFF', 'ServerViewScreen'),
            ('back-ups', os.path.join(icon_path, 'backup.png'), '#56E6FF', 'ServerBackupScreen'),
            ('access control', os.path.join(icon_path, 'acl.png'), '#00FFB2', 'ServerAclScreen'),
            ('add-ons', os.path.join(icon_path, 'addon.png'), '#42FF5E', 'ServerAddonScreen'),
            ('amscript', os.path.join(icon_path, 'amscript.png'), '#BFFF2B', 'ServerAmscriptScreen'),
            ('settings', os.path.join(icon_path, 'advanced.png'), '#FFFF44', 'ServerSettingsScreen')
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
        self.bg_left.source = os.path.join(paths.ui_assets, 'taskbar_edge.png')
        self.bg_left.color = self.background_color
        self.add_widget(self.bg_left)

        self.bg_right = Image()
        self.bg_right.keep_ratio = False
        self.bg_right.allow_stretch = True
        self.bg_right.size_hint_max = (-self.side_width, self.size_hint_max[1])
        self.bg_right.source = os.path.join(paths.ui_assets, 'taskbar_edge.png')
        self.bg_right.color = self.background_color
        self.add_widget(self.bg_right)

        self.bg_center = Image()
        self.bg_center.keep_ratio = False
        self.bg_center.allow_stretch = True
        self.bg_center.source = os.path.join(paths.ui_assets, 'taskbar_center.png')
        self.bg_center.color = self.background_color
        self.add_widget(self.bg_center)

        # Taskbar layout
        self.taskbar = BoxLayout(orientation='horizontal', padding=[5, 0, 5, 0])
        for x, item in enumerate(self.item_list):

            name = item[0]

            if name == 'add-ons' and not show_addons:
                continue

            selected = (selected_item == name)
            item = TaskbarItem(item, selected=selected)
            self.taskbar.add_widget(item)
            if animate: Clock.schedule_once(item.icon.animate, x / 15)

            # Show notification if appropriate
            show = False

            if name == 'settings' and server_obj.update_string:
                if 'settings' not in server_obj.viewed_notifs:
                    show = True
                elif server_obj.update_string != server_obj.viewed_notifs['settings']:
                    show = True

            elif name in server_obj.viewed_notifs:
                if not server_obj.viewed_notifs[name]:
                    show = True

            if show: item.show_notification(True, animate)

        self.add_widget(self.taskbar)

        self.bind(pos=self.resize, size=self.resize)
        Clock.schedule_once(self.resize, 0)

# </editor-fold> ///////////////////////////////////////////////////////////////////////////////////////////////////////
