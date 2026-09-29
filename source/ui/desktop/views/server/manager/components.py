from source.ui.desktop.views.templates import *
from source.ui.desktop.widgets.base import *
from source.ui.desktop.utility import *
from source.ui.desktop import utility



# =============================================== Server Manager =======================================================
# <editor-fold desc="Server Manager">

# Server Manager Overview ----------------------------------------------------------------------------------------------

class ServerButton(ListInstanceButton):

    class ParagraphLabel(TextButton):

        class Button(TextButton.Button):

            def _hover_collide(self, me):
                return (
                    self.parent.copyable
                    and "ServerViewScreen" in utility.screen_manager.current_screen.name
                    and super()._hover_collide(me)
                )

        # Copy public/LAN IP
        def on_click(self, *args):
            if not self.disabled and self.copyable:

                def click(*args):
                    clipboard_text = re.sub(r"\[.*?\]", "", self.text.split(" ")[-1].strip())

                    if self.button.button_pressed == "left":
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

        def __init__(self, **kwargs):
            super().__init__('', min_width=0, height=30, horizontal_padding=0, auto_resize=True, **kwargs)

            self.markup = True
            self.copyable = True
            self.button.on_release = self.on_click

    class ChangeIconButton(HoverBehavior, Button):

        # Show menu to replace icon
        def on_click(self, *args):

            def apply_new_icon(path: str = None, *args):

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

                        # Refresh local Telepath icon cache
                        if self.server_obj._telepath_data:
                            telepath_data = constants.deepcopy(self.server_obj._telepath_data)
                            telepath_data['icon-path'] = icon_path
                            manager.get_server_icon(self.server_obj.name, telepath_data, overwrite=True)

                        # Remove the cached image and texture
                        Cache.remove('kv.image')
                        Cache.remove('kv.texture')

                        for item in glob(os.path.join(paths.ui_assets, 'live', 'blur_icon_*.png')):
                            try:
                                os.remove(item)
                            except:
                                pass

                    return success, message

                # Actually change the server icon
                success, message = do_change()

                # Change header and footer text to reflect change
                def reload_page(*args):
                    def go_back(*args): utility.screen_manager.current = 'ServerViewScreen'

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
                selection = file_popup("file", start_dir=paths.user_downloads, ext=constants.valid_image_formats,
                                       select_multiple=False, title="Select an image")

                if selection and selection[0]:
                    BlurredLoadingScreen.run_task(apply_new_icon, selection[0])

            # Delete icon with right click
            elif self.last_touch.button == 'right' and self.is_custom:
                Clock.schedule_once(
                    functools.partial(
                        utility.screen_manager.current_screen.show_popup,
                        "warning_query",
                        'Remove Icon',
                        "Do you want to remove this icon?\n\nYou'll need to re-import it again later",
                        (None, functools.partial(BlurredLoadingScreen.run_task, apply_new_icon))
                    ), 0
                )

        def on_enter(self, *args):
            Animation.stop_all(self)
            Animation.stop_all(self.type_image)

            Animation(opacity=1, duration=self.anim_duration).start(self)
            Animation(opacity=0, duration=self.anim_duration).start(self.type_image.image)

            if self.server_obj._telepath_data and self.type_image.tp_shadow:
                Animation(opacity=0, duration=self.anim_duration).start(self.type_image.tp_shadow)
                Animation(opacity=0, duration=self.anim_duration).start(self.type_image.tp_icon)

        def on_leave(self, *args):
            Animation.stop_all(self)
            Animation.stop_all(self.type_image)

            Animation(opacity=0, duration=self.anim_duration).start(self)
            Animation(opacity=1, duration=self.anim_duration).start(self.type_image.image)

            if self.server_obj._telepath_data and self.type_image.tp_shadow:
                Animation(opacity=1, duration=self.anim_duration).start(self.type_image.tp_shadow)
                Animation(opacity=1, duration=self.anim_duration).start(self.type_image.tp_icon)

        def generate_blur_background(self, *args, _iter=0):

            # A normal Image can exist before its texture has loaded.
            # CustomServerIcon is canvas-based and doesn't have this delay.
            if not self.is_custom and not getattr(self.type_image.image, 'texture', None) and _iter < 5:
                Clock.schedule_once(functools.partial(self.generate_blur_background, _iter=_iter + 1), 0)
                return

            def run_in_foreground(*args):
                self.blur_background.source = image_path
                self.canvas.ask_update()

            try:
                # Attempt to remove existing icon temp, who even cares lol
                for item in glob(os.path.join(paths.ui_assets, 'live', 'blur_icon_*.png')):
                    if self.server_obj.name in item:
                        image_path = item
                        return run_in_foreground()

                    os.remove(item)

            except:
                pass

            image_path = os.path.join(paths.ui_assets, 'live',
                                      f'blur_icon_{self.server_obj.name}_{constants.gen_rstring(4)}.png')
            constants.folder_check(os.path.join(paths.ui_assets, 'live'))

            self.type_image.image.export_to_png(image_path)

            # Convert the image in the background
            def convert(*args):
                im = PILImage.open(image_path)

                # Center and resize icon when custom
                if self.is_custom:
                    im = im.convert('RGBA')
                    left = 4
                    upper = im.height - 65
                    right = left + 65
                    lower = upper + 65
                    im = im.crop((left, upper, right, lower))

                # Blur and darken the icon
                im = ImageEnhance.Brightness(im)
                im = im.enhance(0.75)
                im = im.filter(GaussianBlur(3))
                im.save(image_path)

                Clock.schedule_once(run_in_foreground, 0)

            dTimer(0, convert).start()

        def resize_self(self, *args):
            for child in self.children: child.pos = self.pos

            offset = (self.pos[0] + 17.5, self.pos[1] + 16.5)

            self.background_ellipse.pos = offset
            self.blur_background.pos = offset
            self.background_outline.ellipse = (*offset, 66, 66)

        def __init__(self, type_image, **kwargs):
            super().__init__(**kwargs)

            self.type_image = type_image
            self.server_obj = constants.server_manager.current_server

            # This button is always designed around the 65px server icon.
            # Do not inherit type_image.image.size here; that may not have laid out yet.
            self.size_hint = (None, None)
            self.size = (65, 65)

            self.is_custom = self.type_image.image.__class__.__name__ == 'CustomServerIcon'

            self.background_normal = os.path.join(paths.ui_assets, 'empty.png')
            self.background_down = os.path.join(paths.ui_assets, 'empty.png')

            self.anim_duration = 0.1
            self.fg = self.type_image.version_label.color
            self.bc = constants.brighten_color(constants.background_color, -0.1)

            with self.canvas.before:
                # Background ellipse (drawn first)
                Color(self.bc[0], self.bc[1], self.bc[2], 0.3)
                self.background_ellipse = Ellipse(size=(66, 66), angle_start=0, angle_end=360)

            with self.canvas:
                # Blur background ellipse (drawn after background ellipse)
                Color(*self.fg)
                self.blur_background = Ellipse(size=(66, 66), angle_start=0, angle_end=360)

                # Outline of the ellipse
                Color(*self.fg[:3], 0)
                self.background_outline = Line(ellipse=(0, 0, 66, 66), width=2)

            self.shadow = Image(source=icon_path('shadow.png'), color="#111122")
            self.shadow.opacity = 0.5

            self.icon = Image(source=icon_path('pencil-sharp.png'), color=constants.brighten_color(self.fg, 0.15))

            self.add_widget(self.shadow)
            self.add_widget(self.icon)

            # Bind and initialize
            self.bind(size=self.resize_self, pos=self.resize_self)
            self.bind(on_press=self.on_click)

            # Wait until the selected icon has actually rendered.
            Clock.schedule_once(self.generate_blur_background, 0)

            self.opacity = 0

    class CustomServerIcon(RelativeLayout):

        def change_source(self, source):
            self.ellipse.source = source or ''

        def __init__(self, server_icon, **kwargs):
            super().__init__(**kwargs)

            self.size_hint = (None, None)
            self.size = (65, 65)

            with self.canvas:
                Color(1, 1, 1, 1)
                self.shadow = Ellipse(pos=(-23.5, -27.5), size=(120, 120),
                                      source=os.path.join(paths.ui_assets, 'icon_shadow.png'), angle_start=0,
                                      angle_end=360)
                self.ellipse = Ellipse(pos=(4, 0), size=(65, 65), source=server_icon, angle_start=0, angle_end=360)

    def _create_subtitle(self):
        if not self.view_only:
            return super()._create_subtitle()

        subtitle = self.ParagraphLabel()
        subtitle.__translate__ = False
        subtitle.id = 'subtitle'
        subtitle.halign = 'left'
        subtitle.valign = 'center'
        subtitle.font_size = sp(21)
        subtitle.shorten = True
        subtitle.markup = True
        subtitle.shorten_from = 'right'
        subtitle.max_lines = 1
        subtitle.copyable = False
        subtitle.color = self.color_id[1]
        subtitle.default_opacity = 0.56
        subtitle.opacity = subtitle.default_opacity
        subtitle.font_name = self.regular_font
        subtitle.bind(size=self.resize_self)

        return subtitle

    def _reset_extra(self):
        self.telepath_data = None
        self.favorite = False
        self.running = False
        self.custom_icon = False
        self.server_icon = None

        # Restore the normal shared image before ListInstanceButton resets it
        if self.default_image:
            self.type_image.image = self.default_image
            self.default_image.opacity = 0

        if self.custom_image:
            Animation.stop_all(self.custom_image)
            self.custom_image.opacity = 0

        if self.type_image.tp_shadow:
            Animation.stop_all(self.type_image.tp_shadow)
            Animation.stop_all(self.type_image.tp_icon)

            self.type_image.tp_shadow.opacity = 0
            self.type_image.tp_icon.opacity = 0

        if self.version_banner:
            Animation.stop_all(self.version_banner)

        if self.version_banner_layout:
            self.version_banner_layout.clear_widgets()
            self.version_banner_layout.opacity = 0

        self.version_banner = None

    def _load_server_icon(self, server_obj, display_type):

        # Check for custom server icon
        if self.telepath_data:
            if server_obj.server_icon:
                telepath_data = constants.deepcopy(self.telepath_data)
                telepath_data['icon-path'] = server_obj.server_icon
                self.server_icon = manager.get_server_icon(server_obj.name, telepath_data, cached_only=True)

            else:
                self.server_icon = None

        else:
            self.server_icon = server_obj.server_icon

        def load_icon(_iter=0):
            if self.server_icon and _iter <= 1:
                self.custom_icon = True

                try:
                    if not self.custom_image:
                        self.custom_image = self.CustomServerIcon(self.server_icon)
                        self.type_image.add_widget(self.custom_image)

                    else:
                        self.custom_image.change_source(self.server_icon)

                    self.custom_image.opacity = 1
                    self.default_image.opacity = 0
                    self.type_image.image = self.custom_image
                    return

                # If the icon is invalid, try to convert it
                except Exception as e:
                    send_log('ServerButton.CustomServerIcon',
                             f"failed to load 'server-icon.png', attempting to convert: {constants.format_traceback(e)}",
                             'error')

                    # Remote cache is entirely local; remove the bad cached file
                    # and let the next background server refresh fetch it again
                    if self.telepath_data:
                        try:
                            os.remove(self.server_icon)
                        except:
                            pass

                        self.server_icon = None

                    # If this is a local server, try to fix it by reconverting the icon
                    else:
                        try:
                            renamed = f'{self.server_icon.replace(".png", ".invalid.png")}'
                            os.rename(self.server_icon, renamed)
                            manager.update_server_icon(server_obj.name, renamed)

                            if not os.path.isfile(self.server_icon):
                                self.server_icon = None

                        except:
                            self.server_icon = None

                    return load_icon(_iter=_iter + 1)

            self.custom_icon = False

            if self.custom_image:
                self.custom_image.opacity = 0

            if display_type == 'modpack':
                self.server_icon = os.path.join(paths.ui_assets, 'icons', 'big', 'modpack.png')
            else:
                self.server_icon = os.path.join(paths.ui_assets, 'icons', 'big', f'{server_obj.type.lower()}_small.png')

            self.default_image.source = self.server_icon
            self.default_image.color = self.color_id[1]
            self.default_image.opacity = 1

            self.type_image.image = self.default_image

        load_icon()

    def _load_telepath_badge(self):
        if not self.telepath_data:
            return

        # Show icon on self.type_image to specify
        if not self.type_image.tp_shadow:
            self.type_image.tp_shadow = Image(source=icon_path('shadow.png'))
            self.type_image.tp_shadow.allow_stretch = True
            self.type_image.tp_shadow.size_hint_max = (33, 33)

            self.type_image.tp_icon = Image(source=icon_path('telepath.png'))
            self.type_image.tp_icon.allow_stretch = True
            self.type_image.tp_icon.size_hint_max = (33, 33)

            self.type_image.add_widget(self.type_image.tp_shadow)
            self.type_image.add_widget(self.type_image.tp_icon)

        self.type_image.tp_shadow.color = self.color_id[0]
        self.type_image.tp_icon.color = self.color_id[1]
        self.type_image.tp_shadow.opacity = 1
        self.type_image.tp_icon.opacity = 1

    def _load_update_banner(self, update_banner):

        # Update label
        if not update_banner:
            self.type_image.version_label.opacity = 0.6
            return

        if not self.version_banner_layout:
            self.version_banner_layout = RelativeLayout()
            self.type_image.add_widget(self.version_banner_layout)

        self.version_banner_layout.clear_widgets()

        self.version_banner = BannerObject(
            pos_hint = {"center_x": 1, "center_y": 0.5},
            size = (100, 30),
            color = (0.647, 0.839, 0.969, 1),
            text = ('   ' + update_banner + '  ') if update_banner.startswith('b-') else update_banner,
            icon = 'arrow-up-circle.png',
            icon_side = 'left'
        )

        self.version_banner_layout.add_widget(self.version_banner)
        self.version_banner_layout.opacity = 1
        self.type_image.version_label.opacity = 0

    def _view_server(self, row, button_pressed, *args):
        owner = self.recycle_owner
        if owner: owner.view_server(self.properties, row, button_pressed)

    def _favorite(self, *args):
        owner = self.recycle_owner
        if owner: owner.favorite(self.properties.name, self.properties)

    def generate_name(self, color='#7373A2'):
        if self.telepath_data:
            tld = self.telepath_data['nickname'] if self.telepath_data['nickname'] else self.telepath_data['host']
            return f'[color={color}]{tld}/[/color]{self.properties.name}'

        return self.properties.name.strip()

    def update_data(self, server_obj, index):

        # Check if server is remote
        self.telepath_data = server_obj._telepath_data
        self.favorite = server_obj.favorite

        self.button.properties = server_obj

        self.color_id = [(0.05, 0.05, 0.1, 1),
                         constants.brighten_color((0.85, 0.6, 0.9, 1) if self.favorite else (0.65, 0.65, 1, 1), 0.07)]
        self.run_color = (0.529, 1, 0.729, 1)

        # Resolve display type/version
        if server_obj.is_modpack:
            display_type = 'modpack'
            display_version = getattr(server_obj, 'modpack_version', None) or server_obj.version

        else:
            display_type = server_obj.type.lower().replace('craft', '')
            display_version = server_obj.version

        # Button background
        if self.view_only:
            self.button.background_normal = os.path.join(paths.ui_assets, 'server_button_ro.png')
            self.button.background_down = os.path.join(paths.ui_assets,
                                                       f'server_button{"_favorite" if self.favorite else "_ro"}.png')
            self.hover_background = self.button.background_normal
            self.button.ignore_hover = True

        else:
            suffix = '_favorite' if self.favorite else ''

            self.button.background_normal = os.path.join(paths.ui_assets, f'server_button{suffix}.png')
            self.button.background_down = os.path.join(paths.ui_assets, f'server_button{suffix}_click.png')
            self.hover_background = os.path.join(paths.ui_assets, f'server_button{suffix}_hover.png')

        # Title of Server
        self.normal_title = self.generate_name()
        self.hover_title = self.generate_name('#2D2D4E')

        self.title.text = self.normal_title
        self._set_title_color(self.color_id[1])
        self.title.text_size = (
        self.button.size_hint_max[0] * (0.7 if self.favorite else 0.58), self.button.size_hint_max[1])

        # Server last modified date formatted
        self.icons = os.path.join(paths.ui_assets, 'fonts', constants.fonts['icons'])
        self.original_font = self.regular_font
        self.original_subtitle = backup.convert_date(server_obj.last_modified)

        self.running = False
        self.update_subtitle(server_obj.run_data if server_obj.running and server_obj.run_data else None,
                             server_obj.last_modified)

        # Type icon and info
        self._load_server_icon(server_obj, display_type)
        self._load_telepath_badge()

        self.type_image.type_label.text = display_type
        self.type_image.type_label.color = self.color_id[1]
        self.type_image.type_label.opacity = 1

        self.type_image.version_label.text = str(display_version).lower()
        self.type_image.version_label.color = self.color_id[1]
        self.type_image.version_label.opacity = 0.6

        update_banner = self.static_update_banner

        if not update_banner and server_obj.auto_update == 'true':
            update_banner = server_obj.update_string

        self._load_update_banner(update_banner)

        # Favorite button
        self.set_icon_button(
            'heart-sharp.png' if self.favorite else 'heart-outline.png',
            self._favorite,
            force_color=[[(0.05, 0.05, 0.1, 1), (0.85, 0.6, 0.9, 1)], 'pink'] if self.favorite else None,
            clickable=not self.view_only
        )

        # Server Manager click function
        if not self.view_only:
            self.click_function = self._view_server

        # Change icon button on ServerView
        elif not self.change_icon_button:
            self.change_icon_button = self.ChangeIconButton(self.type_image)
            self.button.add_widget(self.change_icon_button)

    def animate_button(self, image, color, hover_action, **kwargs):
        self._animate_title(color)

        Animation(color=self.run_color if self.running and not self.button.hovered else color, duration=0.06).start(
            self.subtitle)

        if not self.custom_icon:
            Animation(color=color, duration=0.06).start(self.type_image.image)

        Animation(color=color, duration=0.06).start(self.type_image.version_label)
        Animation(color=color, duration=0.06).start(self.type_image.type_label)

        animate_background(self.button, image, hover_action)

        # Telepath icon
        if self.telepath_data and self.type_image.tp_shadow:
            if hover_action:
                new_color = constants.convert_color('#E865D4' if self.favorite else '#6769D9')['rgb']

                Animation(color=new_color, duration=0.1).start(self.type_image.tp_shadow)
                Animation(color=constants.brighten_color(self.color_id[0], -0.1), duration=0.1).start(
                    self.type_image.tp_icon)

            else:
                Animation(color=self.color_id[0], duration=0.1).start(self.type_image.tp_shadow)
                Animation(color=self.color_id[1], duration=0.1).start(self.type_image.tp_icon)

    def resize_self(self, *args):
        super().resize_self(*args)

        button = self.button

        # Server-specific title/description offsets
        padding = 2.17

        self.title.pos = (
        button.x + (self.title.text_size[0] / padding) - (5.3 if self.favorite else 8.3) + 30, button.y + 31)

        subtitle_offset = 3 if self.running else 0

        if self.view_only:
            self.title.texture_update()
            title_x = self.title.x + ((self.title.width - self.title.texture_size[0]) / 2)
            self.subtitle.pos = (title_x - subtitle_offset, button.y + 8)

        else:
            self.subtitle.pos = (button.x + (self.subtitle.text_size[0] / padding) - 78 - subtitle_offset, button.y + 8)

        offset = 9.45 if self.type_image.type_label.text in ['vanilla', 'paper', 'purpur'] \
            else 9.6 if self.type_image.type_label.text == 'forge' \
            else 9.35 if self.type_image.type_label.text == 'craftbukkit' \
            else 9.55

        self.type_image.image.x = button.width + button.x - self.type_image.image.width - 13
        self.type_image.image.y = button.y + ((button.height / 2) - (self.type_image.image.height / 2))

        # Telepath icon
        if self.telepath_data and self.type_image.tp_shadow:
            self.type_image.tp_shadow.pos = (self.type_image.image.x - 2, self.type_image.image.y)
            self.type_image.tp_icon.pos = (self.type_image.image.x - 2, self.type_image.image.y)

        self.type_image.type_label.x = button.width + button.x - (
                    button.padding_x * offset) - self.type_image.width - 83
        self.type_image.type_label.y = button.y + (button.height * 0.05)

        self.type_image.version_label.x = button.width + button.x - (
                    button.padding_x * offset) - self.type_image.width - 83
        self.type_image.version_label.y = button.y - (button.height / 3.2)

        # Banner version object
        if self.version_banner:
            self.version_banner_layout.x = button.width + button.x - (
                        button.padding_x * offset) - self.type_image.width - 130
            self.version_banner_layout.y = button.y - (button.height / 3.2) - 2

        # Change Icon button pos
        if self.change_icon_button:
            half = self.type_image.image.width / 4
            offset = 2.5 if self.type_image.image.__class__.__name__ == 'CustomServerIcon' else -1

            self.change_icon_button.pos = (
                self.type_image.image.x - half + offset,
                self.type_image.image.y - half
            )

    def update_subtitle(self, run_data=None, last_modified=None):

        def reset(*args):
            self.running = False
            self.subtitle.copyable = False

            if last_modified:
                self.original_subtitle = backup.convert_date(last_modified)

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

            else:
                reset()

        except KeyError:
            reset()

        self.subtitle.color = self.color_id[0] if self.button.hovered else (self.run_color if self.running else self.color_id[1])
        self.subtitle.opacity = self.subtitle.default_opacity
        Clock.schedule_once(self.resize_self, 0)

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

            else:
                return constants.server_manager.open_server(name)

        # Functions for context menu
        def launch(*args):
            if self.telepath_data: open_remote_server(self.telepath_data, self.properties.name, launch=True)
            else:                  open_server(self.properties.name, launch=True)

        def restart(*args): _open_server(self.properties.name).restart()
        def stop(*args):    _open_server(self.properties.name).stop()

        def settings(*args):
            _open_server(self.properties.name)
            utility.screen_manager.current = 'ServerSettingsScreen'

        def update(*args):
            settings()
            utility.screen_manager.current_screen.update_button.button.trigger_action()

        def rename(*args):
            settings()
            rename_input = utility.screen_manager.current_screen.rename_input
            utility.screen_manager.current_screen.scroll_widget.scroll_to(rename_input)
            Clock.schedule_once(rename_input.grab_focus, 0.2)

        def delete(*args):
            settings()
            delete_button = utility.screen_manager.current_screen.delete_button
            utility.screen_manager.current_screen.scroll_widget.scroll_to(delete_button, animate=False)
            Clock.schedule_once(delete_button.button.trigger_action, 0.1)

        def copy_ip(local, *args):

            def click(*args):
                clipboard_text = re.sub(r"\[.*?\]", "", self.subtitle.text.split(" ")[-1].strip())

                if not local:
                    banner_text = "Copied IP address"

                else:
                    if self.properties.running:
                        clipboard_text = self.properties.run_data['network']['private_ip'] + ':' + self.properties.run_data['network']['address']['port']

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

        elif self.properties.running:
            self.context_options = [
                {'name': 'Restart', 'icon': 'restart-server.png', 'action': restart},
                {'name': 'Stop', 'icon': 'stop-server.png', 'action': stop},
                {'name': 'Copy IP', 'icon': 'wifi-sharp.png', 'action': functools.partial(copy_ip, False)},
                {'name': 'Settings', 'icon': os.path.join('sm', 'advanced.png'), 'action': settings}
            ]

        else:
            if self.properties.is_modpack == 'unknown': u = None
            else:                                       u = self.properties.update_string

            self.context_options = [
                {'name': 'Launch', 'icon': 'start-server.png', 'action': launch} if utility.screen_manager.current_screen.name != "ServerViewScreen" else None,
                {'name': f'Update {"build" if u.startswith("b-") else f"{u}"}', 'icon': 'arrow-up.png', 'action': update} if u else None,
                {'name': 'Rename', 'icon': 'rename.png', 'action': rename},
                {'name': 'Settings', 'icon': os.path.join('sm', 'advanced.png'), 'action': settings},
                {'name': 'Delete', 'icon': 'trash-sharp.png', 'action': delete, 'color': 'red'}
            ]

    def __init__(self, server_object=None, click_function=None, fade_in=0.0, highlight=None, update_banner='', view_only=False, **kwargs):
        self.view_only = view_only
        self.static_update_banner = update_banner

        self.telepath_data = None
        self.favorite = False
        self.running = False
        self.run_color = (0.529, 1, 0.729, 1)

        self.default_image = None
        self.custom_image = None
        self.custom_icon = False
        self.server_icon = None

        self.version_banner_layout = None
        self.version_banner = None
        self.change_icon_button = None

        super().__init__(**kwargs)

        self.default_image = self.type_image.image

        self.type_image.tp_shadow = None
        self.type_image.tp_icon = None

        # Preserve direct construction for ServerViewScreen
        if server_object:
            self.properties = server_object
            self.button.properties = server_object

            self._reset_visuals()
            self.update_data(server_object, 0)
            self.resize_self()

            if click_function and not self.view_only:
                self.click_function = lambda *_: click_function()

            if fade_in > 0:
                self.opacity = 0
                Clock.schedule_once(lambda *_: Animation(opacity=1, duration=fade_in).start(self), 0)

            if highlight:
                self.highlight()



class ServerManagerScreen(ListLayout, MenuBackground):

    scroll_position = (0.5, 0.48)
    scroll_divisor = 1.82
    scroll_top = 0.755
    scroll_bottom = 0.22

    header_position = (0, 0.89)
    blank_position = 0.48
    page_position = (0.5, 0.887)

    list_view_class = ServerButton


    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._opening_server = False
        self._polling = False
        self._poll_event = None
        self._poll_interval = 3


    def get_list_key(self, item):
        return getattr(item, '_view_name', None)


    def on_empty_list(self):
        utility.screen_manager.current = 'MainMenuScreen'
        utility.screen_manager.screen_tree = []
        return True


    def _poll_servers(self, *args):
        if self._polling or utility.screen_manager.current_screen is not self:
            return

        self._polling = True

        def poll():
            try:
                state, complete = constants.server_manager.poll_runtime_state()
                current_names = {server._view_name for server in constants.server_manager.menu_view_list}

                # Only rebuild when the actual server set changed, or no cache exists yet
                rebuild = complete and (
                    not constants.server_manager.menu_view_list
                    or current_names != set(state)
                )

                results = constants.server_manager.create_view_list(constants.server_manager.online_telepath_servers) if rebuild else None

                Clock.schedule_once(functools.partial(self._apply_server_poll, state, results), 0)

            finally:
                self._polling = False

        dTimer(0, poll).start()


    def _apply_server_poll(self, state, results=None, *args):
        if utility.screen_manager.current_screen is not self:
            return

        # Server added/deleted/renamed somewhere
        if results is not None:

            # Animate initial screen load, but not background rebuilds
            fade_in = not bool(self.scroll_widget.data)

            # Preserve current server highlight across rebuilds
            server_obj = constants.server_manager.current_server
            highlight = server_obj._view_name if server_obj else None

            constants.server_manager.menu_view_list = results
            self.gen_search_results(results, fade_in=fade_in, highlight=highlight, animate_scroll=False)
            return

        # Otherwise just patch dynamic state into the existing snapshots
        constants.server_manager.update_runtime_state(state)

        # Refresh currently visible buttons
        for button in self.scroll_layout.children:
            try: data = state.get(button.properties._view_name)
            except AttributeError: continue

            if not data:
                continue

            button.update_subtitle(data['run_data'] if data['running'] else None, data['last_modified'])


    def on_pre_enter(self, *args):
        self._opening_server = False
        super().on_pre_enter(*args)

        self._poll_servers()

        if not self._poll_event:
            self._poll_event = Clock.schedule_interval(self._poll_servers, self._poll_interval)


    def on_pre_leave(self, *args):
        if self._poll_event:
            self._poll_event.cancel()

        self._poll_event = None
        super().on_pre_leave(*args)


    # Toggles favorite of item, and reload list
    def favorite(self, server_name, properties):
        if properties._telepath_data:
            properties.toggle_favorite()
            bool_favorite = properties.favorite

        else:
            bool_favorite = manager.toggle_favorite(server_name)
            properties.favorite = bool_favorite

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

        # Re-sort existing ViewObjects instead of rebuilding every object
        favorite_list = sorted([server for server in constants.server_manager.menu_view_list if server.favorite], key=lambda x: x.last_modified, reverse=True)
        normal_list = sorted([server for server in constants.server_manager.menu_view_list if not server.favorite], key=lambda x: x.last_modified, reverse=True)

        constants.server_manager.menu_view_list = favorite_list + normal_list
        self.gen_search_results(constants.server_manager.menu_view_list, fade_in=False, highlight=properties._view_name, animate_scroll=False)


    def view_server(self, server, row, button_pressed, *args):
        telepath_data = constants.deepcopy(row.telepath_data)
        server_name = server.name

        # View Server
        if button_pressed == 'left':
            if self._opening_server:
                return

            self._opening_server = True

            def open_selected():
                try:

                    # Local server
                    if not telepath_data:
                        open_server(server_name, ignore_update=False)
                        return

                    # Remote server/check for disconnect since load
                    remote_obj = open_remote_server(telepath_data, server_name, ignore_update=False)

                    if not remote_obj:
                        constants.server_manager.check_telepath_servers()
                        constants.server_manager.refresh_list()

                        def disconnected(*args):
                            self._opening_server = False

                            if utility.screen_manager.current_screen is not self:
                                return

                            self.gen_search_results(constants.server_manager.menu_view_list, fade_in=False, animate_scroll=False)

                            server_host = telepath_data['nickname'] if telepath_data['nickname'] else telepath_data['host']
                            telepath_banner(f"Lost connection to $'{server_host}'$", False)

                        Clock.schedule_once(disconnected, 0)

                except Exception:
                    self._opening_server = False
                    raise

            dTimer(0, open_selected).start()

        # Favorite
        elif button_pressed == 'middle':
            self.favorite(server_name, server)


    def generate_menu(self, **kwargs):
        float_layout = self.generate_list('Select a server in which to manage', 'No servers available')
        float_layout.add_widget(ExitButton('Back', (0.5, 0.12), cycle=True))

        menu_name = "Server Manager"
        float_layout.add_widget(generate_title(menu_name))
        float_layout.add_widget(generate_footer(menu_name))

        self.add_widget(float_layout)

        # Immediately display cached results while polling for changes
        server_obj = constants.server_manager.current_server
        highlight = server_obj._view_name if server_obj else None

        if constants.server_manager.menu_view_list:
            self.gen_search_results(constants.server_manager.menu_view_list, highlight=highlight, animate_scroll=False)


class MenuTaskbar(RelativeLayout):

    # Layout for icon object
    class TaskbarItem(RelativeLayout):

        class Icon(HoverBehavior, AnchorLayout):

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

            def __init__(self, item_info, selected=False, new_color=None, animate=False, **kwargs):
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


        def show_notification(self, show=True, animate=True):
            if animate:
                Animation(opacity=(1 if show else 0), duration=0.25, transition='in_out_sine').start(self.notification)

                def fade_in(*a): Animation(opacity=(0.5 if show else 0), duration=0.15, transition='in_out_sine').start(self.notification_glow)
                Clock.schedule_once(fade_in, 0.1)

                def fade_out(*a): Animation(opacity=0, duration=0.5, transition='in_out_sine').start(self.notification_glow)
                Clock.schedule_once(fade_out, 0.35)

            else: self.notification.opacity = (1 if show else 0)

        def __init__(self, item_info, selected=False, animate=False, **kwargs):
            super().__init__(**kwargs)

            new_color = constants.convert_color(item_info[2])['rgb']
            self.name = item_info[0]

            self.icon = self.Icon(
                item_info,
                selected=selected,
                new_color=new_color,
                animate=animate
            )
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
            item = self.TaskbarItem(item, selected=selected, animate=animate)
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
