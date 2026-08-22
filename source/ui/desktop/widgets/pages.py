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
class ParagraphObject(RelativeLayout):

    def update_rect(self, *args):

        self.rect.source = os.path.join(paths.ui_assets, f'text_input_cover_fade.png')

        self.title.text = self.title_text
        self.rect.width = (len(self.title.text) * 16) + 116 if self.title.text else 0
        if self.width > 500: self.rect.width += (self.width - 500)
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

    def __init__(self, size, name, content, font_size, font, **kwargs):
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
    class ProjectIcon(Widget):
        load_timeout = 8

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

    # Paragraph composition isolated behind panel contents
    class Background(RelativeLayout):

        def __init__(self, **kwargs):
            super().__init__(**kwargs)

            self.size_hint = (None, None)

            with self.canvas.after:
                self.background_top = Image(
                    source = os.path.join(paths.ui_assets, 'paragraph_edge.png'),
                    allow_stretch = True,
                    keep_ratio = False
                )

                self.background = Image(
                    source = os.path.join(paths.ui_assets, 'paragraph_background.png'),
                    allow_stretch = True,
                    keep_ratio = False
                )

                self.background_bottom = Image(
                    source = os.path.join(paths.ui_assets, 'paragraph_edge.png'),
                    allow_stretch = True,
                    keep_ratio = False
                )

            self.bind(pos=self.resize_background, size=self.resize_background)
            Clock.schedule_once(self.resize_background, 0)

        def resize_background(self, *args):
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

        def set_opacity(self, opacity):
            self.background_top.opacity = opacity
            self.background.opacity = opacity
            self.background_bottom.opacity = opacity


    def __init__(self, close_func=None, action_func=None, **kwargs):
        super().__init__(**kwargs)

        self.size_hint = (None, None)
        self.close_func = close_func
        self.data = None
        self._active = False


        # Background
        self.panel_background = self.Background()
        self.add_widget(self.panel_background)


        # Empty state
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


        # Project image
        self.icon = self.ProjectIcon(icon_path('extension-puzzle.png'))
        self.add_widget(self.icon)


        # Project title / author
        self.title = Label(
            size_hint = (None, None),
            font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf'),
            font_size = sp(24),
            color = (0.6, 0.6, 1, 1),
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
            color = (0.42, 0.42, 0.72, 1),
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
        self.add_widget(self.close_button)


        # Version + contextual install/delete action
        self.action_bar = DropActionBar(action_func=action_func)
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
            color = (0.6, 0.6, 1, 0.9),
            halign = 'left',
            valign = 'top'
        )
        self.description.__translate__ = False
        self.description.line_height = 1.2

        self.scroll.add_widget(self.description)
        self.add_widget(self.scroll)

        self.bind(size=self.resize_panel)
        self.clear()

    def resize_text(self, *args):
        self.description.text_size = (max(self.description.width - 10, 0), None)
        self.description.texture_update()
        self.description.height = self.description.texture_size[1] + 25

    def resize_panel(self, *args):

        # Background
        self.panel_background.pos = (0, 0)
        self.panel_background.size = self.size
        self.panel_background.resize_background()

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

        # Description starts immediately below the header
        self.scroll.pos = (padding, padding)
        self.scroll.size = (
            max(self.width - (padding * 2), 0),
            max(header_y - (padding * 2) + 4, 0)
        )

        self.description.width = self.scroll.width
        self.resize_text()

        self.placeholder.pos = (0, 0)
        self.placeholder.size = self.size
        self.placeholder.text_size = (
            max(self.width - 80, 0),
            self.height
        )

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

        for widget in [
            self.icon,
            self.title,
            self.author,
            self.close_button,
            self.action_bar,
            self.scroll
        ]:
            widget.opacity = opacity

        self.close_button.disabled = not active
        self.action_bar.disabled = not active
        self.scroll.disabled = not active

        self.placeholder.opacity = 0 if active else 1
        self.panel_background.set_opacity(1 if active else 0.48)

    def reset_scroll(self, *args):
        Animation.stop_all(self.scroll)
        self.scroll.scroll_y = 1

    def clear(self):
        self.data = None
        self._set_active(False)

        self.icon.reset()
        self.title.text = ''
        self.author.text = ''
        self.description.text = ''

        self.action_bar.set_data([])
        self.action_bar.opacity = 0

    def preview(self, data):
        self.data = None
        self.reset_close_button()
        self._set_active(True)

        self.icon.load(data.get('icon_url'), self._fallback_icon(data.get('fallback_icon')))
        self.title.text = data.get('title') or ''
        self.author.text = data.get('author') or 'Unknown'
        self.description.text = ''
        self.reset_scroll()

        self.action_bar.opacity = 0
        self.resize_panel()

    def set_data(self, data, reset_scroll=True):
        last_scroll = self.scroll.scroll_y

        self.data = data
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
            allow_remove = data.get('allow_remove', True)
        )

        self.resize_panel()

        if reset_scroll:
            self.reset_scroll()
            Clock.schedule_once(self.reset_scroll, 0)

        else:
            self.scroll.scroll_y = last_scroll
            Clock.schedule_once(lambda *_: setattr(self.scroll, 'scroll_y', last_scroll), 0)

        self.loading(False)

    def loading(self, value, *args):
        self.action_bar.loading(value)



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
