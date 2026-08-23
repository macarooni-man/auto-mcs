from source.ui.desktop.widgets.menus import DropActionBar
from source.ui.desktop.widgets.buttons import *
from source.ui.desktop.widgets.base import *



# ----------------------------------------------  General Menu Features  -----------------------------------------------

class HeaderText(FloatLayout):

    def __init__(self, display_text, more_text, position, fixed_x=False, no_line=False, __translate__ = (True, True), **kwargs):
        super().__init__(**kwargs)

        self.text = Label()
        self.text.__translate__ = __translate__[0]
        self.text.id = 'text'
        self.text.size_hint = (None, None)
        self.text.markup = True
        if not fixed_x: self.text.pos_hint = {"center_x": 0.5, "center_y": position[1]}
        else: self.text.pos_hint = {"center_y": position[1]}
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
        if not no_line: self.add_widget(self.separator)
        self.add_widget(self.text)

        if self.lower_text: self.add_widget(self.lower_text)

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

# Generates colored header at the top of the pages
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

    if not found_server: title = translate(title)


    label.__translate__ = False
    label.text = title
    text_layout.add_widget(label)

    header.add_widget(background)
    header.add_widget(text_layout)
    return header

# Generates the text used in the footer
def footer_label(path, color, progress_screen=False, full_version=False):

    # If remote server, put the instance name behind it
    if constants.server_manager.current_server:
        server_obj = constants.server_manager.current_server
        data = server_obj._telepath_data
        try:
            if data and path.strip().startswith(server_obj.name):
                path = f'[color=#353565]{data["display-name"]}/[/color]{path}'
        except: pass

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
            if x < len(path_list): text += f"[size={round(sp(22))}][font={arrow_font}]  ▸  [/font][/size]"
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

# Generates the entire footer
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
        if not progress_screen: footer.add_widget(IconButton('main menu', {}, (-5, 0), (None, None), 'home-sharp.png', clickable=True))
        else:                   footer.add_widget(AnimButton('please wait...', {}, (0, 0), (None, None), 'loading_pickaxe.gif', clickable=False))

    return footer



# --------------------------------------------  Page Construction Helpers  ---------------------------------------------

# Pagination button & display logic
class PageCounter(FloatLayout):
    def __init__(self, index, total, pos, **kwargs):
        super().__init__(**kwargs)

        self.label = Label(halign="center")
        self.label.__translate__ = False
        self.label.size_hint = (None, None)
        self.label.pos_hint = {"center_x": 0.5, "center_y": pos[1] - 0.07}
        self.label.markup = True
        self.label.font_name = os.path.join(paths.ui_assets, 'fonts', 'DejaVuSans.otf')
        self.label.font_size = sp(9)
        self.label.opacity = 1

        text = ''
        for x in range(0, total):
            if x == index - 1: text += f'[color=8B8BF9]{"⬤   " if x + 1 != total else "⬤"}[/color]'
            else:              text += f'[color=292942]{"⬤   " if x + 1 != total else "⬤"}[/color]'

        self.label.text = text
        self.add_widget(self.label)

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
                if x == index - 1: text += f'[color=8B8BF9]{"⬤   " if x + 1 != total else "⬤"}[/color]'
                else:              text += f'[color=292942]{"⬤   " if x + 1 != total else "⬤"}[/color]'

            self.label.text = text
            utility.hide_widget(self, False)

            if not (self.left_button.hovered or self.right_button.hovered):
                self.resize_self()

        else: utility.hide_widget(self, True)

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



# Creates a visual border around content (used in settings menus)
class ParagraphBackground(Widget):
    corner_size = 34
    line_size = 2
    outer_padding = 3
    body_offset = 29

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.size_hint = (None, None)
        self.opacity = 0.85

        corner = CoreImage(os.path.join(paths.ui_assets, 'paragraph_corner.png')).texture
        side = CoreImage(os.path.join(paths.ui_assets, 'paragraph_side.png')).texture

        coords = [corner.tex_coords[x:x + 2] for x in range(0, 8, 2)]

        def corner_coords(order):
            return tuple(value for index in order for value in coords[index])

        with self.canvas:
            self.background_color = Color(1, 1, 1, 1)

            # Rectangle vertices are BL, BR, TR, TL
            self.top_left = Rectangle(texture=corner, tex_coords=corner_coords((0, 1, 2, 3)))
            self.top_right = Rectangle(texture=corner, tex_coords=corner_coords((1, 0, 3, 2)))
            self.bottom_left = Rectangle(texture=corner, tex_coords=corner_coords((3, 2, 1, 0)))
            self.bottom_right = Rectangle(texture=corner, tex_coords=corner_coords((2, 3, 0, 1)))

            self.top_edge = Rectangle(texture=side)
            self.bottom_edge = Rectangle(texture=side)
            self.left_edge = Rectangle(texture=side)
            self.right_edge = Rectangle(texture=side)

        self.bind(pos=self.resize_background, size=self.resize_background)
        self.resize_background()

    def resize_background(self, *args):
        corner = self.corner_size
        line = self.line_size
        padding = self.outer_padding

        left = self.x + padding
        right = self.right - padding
        bottom = self.y + padding
        top = self.top - padding

        width = max((right - left) - (corner * 2), 0)
        height = max((top - bottom) - (corner * 2), 0)

        self.top_left.pos = (left, top - corner)
        self.top_left.size = (corner, corner)

        self.top_right.pos = (right - corner, top - corner)
        self.top_right.size = (corner, corner)

        self.bottom_left.pos = (left, bottom)
        self.bottom_left.size = (corner, corner)

        self.bottom_right.pos = (right - corner, bottom)
        self.bottom_right.size = (corner, corner)

        self.top_edge.pos = (left + corner, top - line)
        self.top_edge.size = (width, line)

        self.bottom_edge.pos = (left + corner, bottom)
        self.bottom_edge.size = (width, line)

        self.left_edge.pos = (left, bottom + corner)
        self.left_edge.size = (line, height)

        self.right_edge.pos = (right - line, bottom + corner)
        self.right_edge.size = (line, height)

    def set_opacity(self, opacity):
        self.background_color.a = opacity

class ParagraphObject(RelativeLayout):

    def update_rect(self, *args):
        self.rect.source = os.path.join(paths.ui_assets, 'text_input_cover_fade.png')

        self.title.text = self.title_text
        self.rect.width = (len(self.title.text) * 16) + 116 if self.title.text else 0
        if self.width > 500: self.rect.width += self.width - 500

        offset = self.background.body_offset
        self.background.pos = (0, -offset)
        self.background.size = (self.width, self.height + offset)

        self.rect.pos = (
            self.x + (self.width / 2) - (self.rect.width / 2) - 1,
            self.y + self.height - 11
        )
        self.title.pos = (
            self.x + (self.width / 2) - (self.title.width / 2),
            self.y + self.height - 52
        )

        self.text_content.y = self.y - 25
        self.text_content.x = self.x + 25
        self.text_content.size = self.size
        self.text_content.width = self.width

    def __init__(self, size, name, content, font_size, font, **kwargs):
        super().__init__(**kwargs)

        self.background = ParagraphBackground()
        self.background.pos = (0, 0)
        self.add_widget(self.background)

        self.title_text = "Paragraph"
        self.size_hint = (None, None)
        self.size_hint_max = (None, None)

        with self.canvas.after:

            # Title
            self.rect = Image(size=(110, 15), color=constants.background_color, allow_stretch=True, keep_ratio=False)
            self.title = AlignLabel(halign="center", text=self.title_text, color=(0.6, 0.6, 1, 1), font_size=sp(17), font_name=os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["regular"]}.ttf'))
            self.bind(pos=self.update_rect)
            self.bind(size=self.update_rect)

            # Text content
            self.text_content = AlignLabel(halign="left", valign="top", color=(0.65, 0.65, 1, 1), font_name=font if font else os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["regular"]}.ttf'), markup=True)
            self.text_content.line_height = 1.3


        # Initialize custom properties
        self.pos_hint = {"center_x": 0.5}  # , "center_y": 0.5
        self.width = size[0]
        self.height = size[1] + 10
        self.title_text = name
        self.text_content.__translate__ = False
        self.text_content.text = content
        self.text_content.font_size = font_size



# Inline details panel for ListDiscoverLayout
class DiscoverPanel(RelativeLayout):
    collapsed_scale = 0.983
    collapsed_opacity = 0.7

    class ProjectIcon(Widget):
        load_timeout = 8
        cache_limit = 48
        texture_cache = {}
        cache_order = []

        def __init__(self, fallback, **kwargs):
            super().__init__(**kwargs)

            self.size_hint = (None, None)
            self.size = (46, 46)

            self.fallback = fallback
            self._source = None
            self._state = 'fallback'
            self._timeout_event = None

            background_color = constants.background_color

            # Circular backing & remote icon
            with self.canvas:
                Color(*background_color[:3], 1)
                self.background = Ellipse()

                self.image_color = Color(1, 1, 1, 0)
                self.project_image = Ellipse()

            # Local fallback icon
            self.fallback_image = Image(
                source = fallback,
                size_hint = (None, None),
                size = (40, 40),
                allow_stretch = True,
                keep_ratio = True,
                color = (0.6, 0.6, 1, 1)
            )
            self.add_widget(self.fallback_image)

            # Hidden AsyncImage only fetches the remote icon
            self.image = AsyncImage(size_hint=(None, None), opacity=0)
            self.image.bind(on_load=self.image_loaded, on_error=self.image_error)
            self.add_widget(self.image)

            # Loading animation
            self.loader = AsyncImage(
                source = os.path.join(paths.ui_assets, 'animations', 'loading_pickaxe.gif'),
                size_hint = (None, None),
                size = (36, 36),
                allow_stretch = True,
                color = (0.6, 0.6, 1, 1),
                opacity = 0
            )
            self.loader.anim_delay = utility.anim_speed * 0.02
            self.add_widget(self.loader)

            self.bind(pos=self.resize_icon, size=self.resize_icon)
            self.resize_icon()

        @classmethod
        def cache_texture(cls, source, texture):
            if not source or not texture:
                return

            cls.texture_cache[source] = texture

            try: cls.cache_order.remove(source)
            except ValueError: pass

            cls.cache_order.append(source)

            while len(cls.cache_order) > cls.cache_limit:
                cls.texture_cache.pop(cls.cache_order.pop(0), None)

        def resize_icon(self, *args):
            self.background.pos = self.project_image.pos = self.pos
            self.background.size = self.project_image.size = self.size

            self.fallback_image.size = (40, 40)
            self.fallback_image.center = self.center

            self.loader.center = self.center

            self.image.pos = self.pos
            self.image.size = self.size

        def cancel_timeout(self):
            if self._timeout_event:
                self._timeout_event.cancel()
                self._timeout_event = None

        def show_fallback(self, *args):
            self.cancel_timeout()

            self._state = 'fallback'
            self.image_color.a = 0
            self.loader.opacity = 0
            self.fallback_image.opacity = 1

        def reset(self):
            self.cancel_timeout()

            self._source = None
            self._state = 'fallback'

            self.project_image.texture = None
            self.image_color.a = 0
            self.loader.opacity = 0
            self.fallback_image.opacity = 1

        def load(self, source=None, fallback=None):
            if fallback and fallback != self.fallback:
                self.fallback = fallback
                self.fallback_image.source = fallback

            if not source:
                self.reset()
                return

            # preview() -> set_data() shouldn't restart the same request
            if source == self._source and self._state in ('loading', 'loaded'):
                return

            cached = self.texture_cache.get(source)
            if cached:
                self.cancel_timeout()
                self.cache_texture(source, cached)

                self._source = source
                self._state = 'loaded'

                self.project_image.texture = cached
                self.image_color.a = 1
                self.loader.opacity = 0
                self.fallback_image.opacity = 0
                return

            self.cancel_timeout()

            self._source = source
            self._state = 'loading'

            self.image_color.a = 0
            self.fallback_image.opacity = 0
            self.loader.opacity = 1

            if self.image.source == source:
                self.image.reload()
            else:
                self.image.source = source

            self._timeout_event = Clock.schedule_once(functools.partial(self.image_timeout, source), self.load_timeout)

        def image_loaded(self, instance, *args):
            if instance.source != self._source or self._state != 'loading':
                return

            # AsyncImage's actual source texture is now available
            if not instance.texture:
                return Clock.schedule_once(functools.partial(self.image_loaded, instance), 0)

            self.cancel_timeout()
            self.cache_texture(instance.source, instance.texture)

            self._state = 'loaded'
            self.project_image.texture = instance.texture
            self.image_color.a = 1

            self.loader.opacity = 0
            self.fallback_image.opacity = 0

        def image_error(self, instance, *args):
            if instance.source == self._source:
                self.show_fallback()

        def image_timeout(self, source, *args):
            if source == self._source and self._state == 'loading':
                self.show_fallback()

    class ProjectButton(RelativeLayout):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

            self.size_hint = (None, None)
            self.size = (135 if constants.app_config.locale == 'en' else 155, 30)

            self.button = HoverButton()
            self.button.id = 'project_button'
            self.button.hover_scale = 1.025
            self.button.size_hint = (None, None)
            self.button.size = self.size
            self.button.pos = (0, 0)
            self.button.border = (0, 0, 0, 0)
            self.button.background_color = (0.6, 0.6, 1, 0.45)
            self.button.background_normal = os.path.join(paths.ui_assets, 'addon_view_button.png')
            self.button.background_down = self.button.background_normal
            self.button.background_disabled_normal = self.button.background_normal
            self.button.background_disabled_down = self.button.background_normal
            self.button.text = 'view project'
            self.button.color = constants.brighten_color(constants.background_color, -0.01)
            self.button.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
            self.button.font_size = sp(16)

            def on_enter(*args):
                if not self.button.ignore_hover:
                    animate_background(self.button, self.button.background_normal, True, 1.025, _no_bg_change=True)
                    Animation(background_color=(0.65, 0.65, 1, 0.65), duration=0.1).start(self.button)

            def on_leave(*args):
                if not self.button.ignore_hover:
                    animate_background(self.button, self.button.background_normal, False, 1.025, _no_bg_change=True)
                    Animation(background_color=(0.6, 0.6, 1, 0.45), duration=0.1).start(self.button)

            self.button.on_enter = on_enter
            self.button.on_leave = on_leave
            self.add_widget(self.button)

    def __init__(self, close_func=None, action_func=None, select_func=None, **kwargs):
        super().__init__(**kwargs)

        self.size_hint = (None, None)
        self.close_func = close_func
        self.data = None
        self._active = False
        self._transitioning = False
        self.banners = []
        self.project_url = None

        with self.canvas.before:
            self.anim_push = PushMatrix()
            self.anim_scale = Scale(0.96, 0.96, 1, origin=(self.width / 2, self.height / 2))

        with self.canvas.after:
            self.anim_pop = PopMatrix()


        # Background
        self.panel_background = ParagraphBackground()
        self.add_widget(self.panel_background)


        # Empty state/loading icon
        self.placeholder = Label(
            text = translate('select an item to view details'),
            size_hint = (None, None),
            font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf'),
            font_size = sp(21),
            color = (0.6, 0.6, 1, 0.35),
            halign = 'center',
            valign = 'middle'
        )
        self.add_widget(self.placeholder)

        self.loading_icon = AsyncImage(
            source = os.path.join(paths.ui_assets, 'animations', 'loading_pickaxe.gif'),
            size_hint = (None, None),
            size = (42, 42),
            allow_stretch = True,
            color = (0.6, 0.6, 1, 1),
            opacity = 0
        )
        self.loading_icon.anim_delay = utility.anim_speed * 0.02
        self.loading_label = Label(
            text = translate('loading details'),
            size_hint = (None, None),
            size = (180, 24),
            font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf'),
            font_size = sp(20),
            color = (0.6, 0.6, 1, 0.7),
            halign = 'center',
            opacity = 0
        )
        self.add_widget(self.loading_label)
        self.add_widget(self.loading_icon)


        # Project image
        self.icon = self.ProjectIcon(icon_path('extension-puzzle.png'))
        self.add_widget(self.icon)


        # Project title / author
        self.title = Label(
            size_hint = (None, None),
            font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf'),
            font_size = sp(24),
            color = (0.65, 0.65, 1, 1),
            halign = 'left',
            valign = 'middle',
            shorten = True,
            shorten_from = 'right',
            max_lines = 1
        )
        self.title.__translate__ = False
        self.add_widget(self.title)

        self.author = Label(
            size_hint = (None, None),
            font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf'),
            font_size = sp(19),
            color = (0.65, 0.65, 1, 0.56),
            halign = 'left',
            valign = 'middle',
            shorten = True,
            shorten_from = 'right',
            max_lines = 1
        )
        self.author.__translate__ = False
        self.add_widget(self.author)


        # Close button
        self.close_button = RelativeIconButton(
            '',
            {"center_x": 0.5, "center_y": 0.5},
            None,
            (None, None),
            'close-sharp.png',
            click_func = lambda *_: self.close_func() if self.close_func else None
        )
        self.close_button.size_hint = (None, None)
        self.close_button.size = (40, 40)
        self.close_button.button.size = (40, 40)
        self.close_button.icon.size = (20, 20)
        self.close_button.button.background_disabled_normal = self.close_button.button.background_normal
        self.close_button.button.background_disabled_down = self.close_button.button.background_normal
        self.add_widget(self.close_button)


        # Version + contextual install/delete action
        self.action_bar = DropActionBar(action_func=action_func, select_func=select_func)
        self.add_widget(self.action_bar)


        # Scrollable description
        self.scroll = ScrollView(size_hint=(None, None))
        self.scroll.do_scroll_x = False
        self.scroll.bar_width = 5
        self.scroll.bar_color = (0.6, 0.6, 1, 1)
        self.scroll.bar_inactive_color = (0.6, 0.6, 1, 0.25)
        self.scroll.scroll_wheel_distance = dp(55)

        self.description = Label(
            size_hint = (None, None),
            font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["regular"]}.ttf'),
            font_size = sp(18),
            color = (0.65, 0.65, 1, 0.85),
            halign = 'left',
            valign = 'top'
        )
        self.description.__translate__ = False
        self.description.line_height = 1.2

        self.scroll.add_widget(self.description)
        self.add_widget(self.scroll)


        self.scroll_top = Image(source=os.path.join(paths.ui_assets, 'scroll_gradient.png'), size_hint=(None, None), allow_stretch=True, keep_ratio=False, color=constants.background_color, opacity=0)
        self.scroll_bottom = Image(source=os.path.join(paths.ui_assets, 'scroll_gradient.png'), size_hint=(None, None), allow_stretch=True, keep_ratio=False, color=constants.background_color, opacity=0)
        self.add_widget(self.scroll_top)
        self.add_widget(self.scroll_bottom)


        # Project button
        self.project_button = self.ProjectButton()
        self.project_button.opacity = 0
        self.project_button.disabled = True
        self.project_button.button.bind(on_release=self.open_project)
        self.add_widget(self.project_button)


        self.bind(pos=self.resize_animation, size=self.resize_animation)
        self.bind(size=self.resize_panel)
        self.clear()

    def resize_animation(self, *args):
        self.anim_scale.origin = (self.width / 2, self.height / 2)

    def animate_panel(self):
        Animation.stop_all(self)
        try: Animation.cancel_all(self.anim_scale)
        except: pass

        self.opacity = self.collapsed_opacity
        self.anim_scale.x = self.anim_scale.y = self.collapsed_scale

        Animation(opacity=1, duration=0.13, t='out_cubic').start(self)
        Animation(x=1, y=1, duration=0.13, t='out_cubic').start(self.anim_scale)

    def hide_panel(self, callback=None):
        if self._transitioning:
            return

        self._transitioning = True

        Animation.stop_all(self)
        try: Animation.cancel_all(self.anim_scale)
        except: pass

        duration = 0.13
        fade = Animation(opacity=self.collapsed_opacity, duration=duration, t='out_cubic')
        scale = Animation(x=self.collapsed_scale, y=self.collapsed_scale, duration=duration, t='out_cubic')

        def _finish(*args):
            self._transitioning = False
            if callback: callback()

        scale.bind(on_complete=_finish)

        fade.start(self)
        scale.start(self.anim_scale)

    def resize_text(self, *args):
        self.description.text_size = (max(self.description.width - 12, 0), None)
        self.description.texture_update()
        self.description.height = self.description.texture_size[1] + 45

    def resize_panel(self, *args):

        # Background
        self.panel_background.pos = (0, 0)
        self.panel_background.size = self.size

        # Compact 58px header
        padding = 18
        header_y = self.height - self.action_bar.height - padding

        self.icon.pos = (
            padding,
            header_y + ((self.action_bar.height - self.icon.height) / 2)
        )

        action_x = self.width - self.action_bar.width - 58
        self.action_bar.pos = (action_x, header_y)

        self.close_button.pos = (self.width - 52, self.height - 52)

        title_x = self.icon.right + 12
        title_width = max(action_x - title_x - 12, 100)

        self.title.pos = (title_x, header_y + 29)
        self.title.size = (title_width, 26)
        self.title.text_size = self.title.size

        self.author.pos = (title_x, header_y + 4)
        self.author.size = (title_width, 23)
        self.author.text_size = self.author.size


        # Banners
        if self.banners:
            banner_y = header_y - 40
            banner_gap = 10
            banner_width = sum(banner.width for banner in self.banners) + ((len(self.banners) - 1) * banner_gap)
            banner_x = (self.width - banner_width) / 2

            for banner in self.banners:
                banner.pos = (banner_x, banner_y)
                banner_x += banner.width + banner_gap

            content_top = banner_y - 2

        else:
            content_top = header_y - 4

        # Project link
        self.project_button.pos = ((self.width - self.project_button.width) / 2, 15)
        content_bottom = self.project_button.top if self.project_url else padding

        # Description
        self.scroll.pos = (padding, content_bottom)
        self.scroll.size = (max(self.width - (padding * 2), 0), max(content_top - content_bottom, 0))

        self.description.width = self.scroll.width
        self.resize_text()

        # Description fade edges
        fade_height = 30
        scrollbar_width = 5
        self.scroll_top.pos = (self.scroll.x, self.scroll.top - (fade_height / 1.5))
        self.scroll_top.size = (self.scroll.width - scrollbar_width, fade_height)
        self.scroll_bottom.pos = (self.scroll.x, self.scroll.y + (fade_height / 1.5))
        self.scroll_bottom.size = (self.scroll.width - scrollbar_width, -fade_height)

        self.placeholder.pos = (0, 0)
        self.placeholder.size = self.size
        self.placeholder.text_size = (max(self.width - 80, 0), self.height)

        self.loading_icon.center = (self.width / 2, (self.height / 2) + 14)
        self.loading_label.center = (self.width / 2, (self.height / 2) - 24)

    def reset_close_button(self):
        button = self.close_button.button
        button.on_leave(duration=0)
        button.hovered = False
        button.state = 'normal'

    def _fallback_icon(self, name=None):
        path = icon_path(name or 'extension-puzzle.png')
        return path if os.path.isfile(path) else icon_path('extension-puzzle.png')

    def _set_active(self, active):
        self._active = active

        if not active:
            self.reset_close_button()

        opacity = 1 if active else 0

        for widget in [self.icon, self.title, self.author, self.close_button, self.action_bar, self.scroll]:
            widget.opacity = opacity

        for banner in self.banners:
            banner.opacity = opacity

        self.project_button.opacity = opacity if self.project_url else 0
        self.close_button.button.disabled = not active
        self.scroll.do_scroll_y = active
        self.project_button.disabled = not active or not bool(self.project_url)

        self.placeholder.opacity = 0 if active else 1
        self.panel_background.set_opacity(1 if active else 0.48)
        self.scroll_top.opacity = self.scroll_bottom.opacity = opacity

    def reset_scroll(self, *args):
        Animation.stop_all(self.scroll)
        self.scroll.scroll_y = 1

    def clear(self):
        Animation.stop_all(self)
        try: Animation.cancel_all(self.anim_scale)
        except: pass

        self.data = None
        self.set_banners([])
        self.set_project_url(None)
        self._set_active(False)

        self.icon.reset()
        self.title.text = ''
        self.author.text = ''
        self.description.text = ''
        self.loading_icon.opacity = 0
        self.loading_label.opacity = 0

        self.action_bar.set_data([])
        self.action_bar.opacity = 0

        self.opacity = self.collapsed_opacity
        self.anim_scale.x = self.anim_scale.y = self.collapsed_scale
        self._transitioning = False

    def preview(self, data):
        Animation.stop_all(self)
        try: Animation.cancel_all(self.anim_scale)
        except: pass

        self.data = None
        self.set_banners([])
        self.set_project_url(None)
        self.reset_close_button()
        self.reset_scroll()
        self._set_active(False)

        self.icon.reset()
        self.title.text = ''
        self.author.text = ''
        self.description.text = ''

        self.placeholder.opacity = 0
        self.close_button.opacity = 1
        self.close_button.button.disabled = False
        self.action_bar.opacity = 0

        self.loading_icon.opacity = 0
        self.loading_label.opacity = 0

        self.opacity = self.collapsed_opacity
        self.anim_scale.x = self.anim_scale.y = self.collapsed_scale
        self.resize_panel()

    def set_data(self, data, reset_scroll=True):
        last_scroll = self.scroll.scroll_y
        self.loading_icon.opacity = 0
        self.loading_label.opacity = 0

        self.data = data
        self.set_banners(data.get('banners'))
        self.set_project_url(data.get('project_url'))
        self._set_active(True)

        self.icon.load(data.get('icon_url'), self._fallback_icon(data.get('fallback_icon')))
        self.title.text = data.get('title') or ''
        self.author.text = data.get('author') or 'Unknown'
        self.description.text = (data.get('description') or '').strip() or translate('description unavailable')

        options = data.get('versions') or []
        self.action_bar.opacity = 1 if options else 0
        self.action_bar.set_data(
            options,
            selected = data.get('selected'),
            installed_version = data.get('installed_version'),
            allow_remove = data.get('allow_remove', True),
            action_icon = data.get('action_icon', 'arrow-down.png')
        )

        self.resize_panel()

        if reset_scroll:
            self.reset_scroll()
            Clock.schedule_once(self.reset_scroll, 0)
        else:
            self.scroll.scroll_y = last_scroll
            Clock.schedule_once(lambda *_: setattr(self.scroll, 'scroll_y', last_scroll), 0)

        self.loading(False)

        if reset_scroll:
            self.animate_panel()

    def loading(self, value, *args):
        self.action_bar.loading(value)

        show_loader = value and self.data is None
        self.loading_icon.opacity = 1 if show_loader else 0
        self.loading_label.opacity = 1 if show_loader else 0

    def set_banners(self, banners):
        for banner in self.banners:
            if banner.parent is self: self.remove_widget(banner)

        self.banners = []

        for data in banners or []:
            banner = BannerObject(pos_hint={}, **data)
            banner.opacity = 1 if self._active else 0
            self.banners.append(banner)
            self.add_widget(banner)

        if hasattr(self, 'scroll'):
            self.resize_panel()

    def set_project_url(self, url):
        self.project_url = url
        self.project_button.opacity = 1 if self._active and url else 0
        self.project_button.disabled = not bool(url)

        if hasattr(self, 'scroll'):
            self.resize_panel()

    def open_project(self, *args):
        if self.project_url:
            webbrowser.open_new_tab(self.project_url)



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
        self.scroll_wheel_distance = dp(30)
        self.scroll_timeout = 250

    # Allow scroll bar to be dragged
    def on_touch_move(self, touch, *args):
        if touch.pos[0] > self.x + (self.width - self.drag_pad) and (self.y + self.height > touch.pos[1] > self.y):
            try:
                new_scroll = ((touch.pos[1] - self.y) / (self.height - (self.height * (self.vbar[1])))) - (self.vbar[1])
                self.scroll_y = 1 if new_scroll > 1 else 0 if new_scroll < 0 else new_scroll
                return True
            except ZeroDivisionError: pass
        return super().on_touch_move(touch)

    def on_touch_down(self, touch, *args):
        if touch.pos[0] > self.x + (self.width - self.drag_pad) and (self.y + self.height > touch.pos[1] > self.y):
            try:
                new_scroll = ((touch.pos[1] - self.y) / (self.height - (self.height * (self.vbar[1])))) - (self.vbar[1])
                self.scroll_y = 1 if new_scroll > 1 else 0 if new_scroll < 0 else new_scroll
                return True
            except ZeroDivisionError: pass
        return super().on_touch_down(touch)

class ScrollItem(RelativeLayout):
    def __init__(self, widget=None, **kwargs):
        super().__init__(**kwargs)
        self.height = 85
        self.size_hint_y = None

        if widget: self.add_widget(widget)

class ScrollBackground(Image):

    def resize(self, *args):
        self.width = Window.width-20

    def __init__(self, pos_hint, pos, size, highlight=False, color=None, **kwargs):
        super().__init__(**kwargs)
        self.allow_stretch = True
        self.keep_ratio = False
        self.size_hint = (None, None)

        if color: self.color = color
        else:     self.color = (1, 1, 1, 1) if highlight else constants.background_color

        self.source = os.path.join(paths.ui_assets, 'scroll_gradient.png')

        self.pos = pos
        self.pos_hint = pos_hint
        self.size = size
        self.width = 830

        # Forcibly update these later
        # Window.bind(on_resize=self.resize)
        Clock.schedule_once(self.resize, 0)
