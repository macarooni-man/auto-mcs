from source.ui.desktop.views.templates import *
from source.ui.desktop.widgets.base import *
from source.ui.desktop.utility import *
from source.core import constants



# ============================================= Telepath Utilities =====================================================
# <editor-fold desc="Telepath Utilities">

# Telepath instance screen (for a client to view servers it's connected to)
class InstanceButton(ListInstanceButton):

    class NameInput(TextInput):

        def update_config(self, *args):
            if self.change_timeout:
                self.change_timeout.cancel()

            properties = self.properties
            text = self.text

            def write(*args):
                constants.server_manager.rename_telepath_server(properties, text)

                if self.properties is properties:
                    self.original_text = text
                    self.change_timeout = None

            self.change_timeout = Clock.schedule_once(write, 0.7)


        def _on_focus(self, instance, value, *largs):
            super()._on_focus(instance, value, *largs)

            if not value and not self.text:
                self.text = constants.format_nickname(self.original_text)


        # Ignore popup text
        def insert_text(self, substring, from_undo=False):
            if utility.screen_manager.current_screen.popup_widget:
                return None

            # Input validation & formatting
            if len(substring) > 1 or (substring in [' ', '-', '.'] and (not self.text or self.cursor_col == 0 or self.text[self.cursor_col - 1] in ['-', '.'])):
                return

            if len(self.text) >= 20:
                return

            substring = substring.lower().replace(' ', '-')
            substring = re.sub('[^a-zA-Z0-9.-]', '', substring)

            super().insert_text(substring, from_undo)
            self.update_config()


        # Special keypress behaviors
        def keyboard_on_key_down(self, window, keycode, text, modifiers):
            if keycode[1] == 'backspace' and control in modifiers:
                original_index = self.cursor_col
                new_text, index = constants.control_backspace(self.text, original_index)

                self.select_text(original_index - index, original_index)
                self.delete_selection()

            else:
                super().keyboard_on_key_down(window, keycode, text, modifiers)

            if keycode[1] in ['backspace', 'delete']:
                self.update_config()


        def __init__(self, **kwargs):
            super().__init__(**kwargs)

            self.properties = None
            self.id = 'title'
            self.halign = 'left'
            self.foreground_color = constants.brighten_color((0.65, 0.65, 1, 1), 0.07)
            self.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
            self.background_color = (0, 0, 0, 0)
            self.size = (400, 50)
            self.font_size = sp(25)
            self.max_lines = 1
            self.multiline = False
            self.hint_text_color = (0.6, 0.6, 1, 0.4)
            self.cursor_color = (0.55, 0.55, 1, 1)
            self.cursor_width = dp(3)
            self.selection_color = (0.5, 0.5, 1, 0.4)
            self.hint_text = 'enter a nickname...'

            self.original_text = ''
            self.change_timeout = None


    def _create_title(self):
        return self.NameInput()


    def _unpair(self, *args):
        owner = self.recycle_owner

        if owner:
            owner.unpair_instance(self.properties)


    def update_data(self, instance, index):
        key = f"{instance['host']}:{instance['port']}"
        connected = key in constants.server_manager.online_telepath_servers

        self.button.ignore_hover = True
        self.click_function = None

        previous = self.title.properties
        if previous:
            previous_key = (previous['host'], previous['port'])
            current_key = (instance['host'], instance['port'])

            if previous_key != current_key:
                self.title.focus = False
                self.title.cancel_selection()

        self.title.properties = instance
        self.title.text = instance['nickname'] if instance['nickname'] else instance['host']
        self.title.original_text = self.title.text

        # Authentication status formatted
        if connected:
            self.color_id = [(0.05, 0.05, 0.1, 1), (0.65, 0.65, 1, 1)]

            self.subtitle.text = translate('Connected')
            self.subtitle.color = (0.529, 1, 0.729, 1)
            self.subtitle.default_opacity = 0.8

            background = os.path.join(paths.ui_assets, 'telepath_button_enabled.png')

        else:
            self.color_id = [(0.05, 0.1, 0.1, 1), (1, 0.6, 0.7, 1)]

            if instance.get('telepath-version') != constants.api_manager.version:
                self.subtitle.text = translate('API version mismatch')
            else:
                self.subtitle.text = translate('Authentication failure')

            self.subtitle.color = (1, 0.65, 0.65, 1)
            self.subtitle.default_opacity = 0.8
            background = os.path.join(paths.ui_assets, 'list_button_disabled.png')

        self.button.background_normal = background
        self.button.background_down = background
        self.hover_background = background

        # Instance name is independent of connection state
        self.title.foreground_color = constants.brighten_color((0.65, 0.65, 1, 1), 0.07)
        self.subtitle.opacity = self.subtitle.default_opacity
        self.subtitle.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')

        # Type icon and info
        self.type_image.image.source = os.path.join(paths.ui_assets, 'icons', 'big', f'{instance["os"]}.png')
        self.type_image.image.color = self.color_id[1]
        self.type_image.image.opacity = 1

        self.type_image.version_label.text = f'auto-mcs v{instance["app-version"]}'
        self.type_image.version_label.color = self.color_id[1]
        self.type_image.version_label.opacity = 0.6

        self.type_image.type_label.text = instance['os'].replace('macos', 'macOS')
        self.type_image.type_label.color = self.color_id[1]
        self.type_image.type_label.opacity = 1

        # Edit button
        self.set_icon_button('unpair.png', self._unpair)


    def resize_self(self, *args):
        super().resize_self(*args)

        button = self.button

        # Title and description
        self.title.pos = (button.x + 53, button.y + 26)
        self.subtitle.pos = (button.x + (self.subtitle.text_size[0] / 2.17) - 78, button.y + 8)

        self.type_image.image.x = button.width + button.x - self.type_image.image.width - 13
        self.type_image.image.y = button.y + ((button.height / 2) - (self.type_image.image.height / 2))

        self.type_image.type_label.x = button.width + button.x - (button.padding_x * 9.55) - self.type_image.width - 83
        self.type_image.type_label.y = button.y + (button.height * 0.05)

        self.type_image.version_label.x = button.width + button.x - (button.padding_x * 9.55) - self.type_image.width - 83
        self.type_image.version_label.y = button.y - (button.height / 3.2)


class TelepathInstanceScreen(ListLayout, MenuBackground):

    scroll_position = (0.5, 0.52)
    scroll_divisor = 1.82
    scroll_top = 0.795
    scroll_bottom = 0.26

    header_position = (0, 0.89)
    blank_position = 0.48
    page_position = (0.5, 0.887)

    list_view_class = InstanceButton


    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.background_color = constants.brighten_color(constants.background_color, -0.09)

        with self.canvas.before:
            self.color = Color(*self.background_color, mode='rgba')
            self.rect = Rectangle(pos=self.pos, size=self.size)


    def prepare_list_results(self, results):
        if isinstance(results, dict):
            return list(constants.deepcopy(results).values())

        return list(results)


    def get_list_key(self, item):
        return f"{item['host']}:{item['port']}"


    def on_empty_list(self):
        utility.screen_manager.current = 'TelepathManagerScreen'
        utility.screen_manager.screen_tree = ['MainMenuScreen']
        return True


    def unpair_instance(self, data):
        if data['nickname']: display_name = f"{data['host']} ({data['nickname']})"
        else:                display_name = data['host']

        desc = f"Un-pairing this instance will prevent you from accessing it via $Telepath$ until it's paired again.\n\nAre you sure you want to un-pair from '${display_name}$'?"

        def unpair(*args):

            def worker():

                # Log out if possible
                key = (data['host'], data['port'])

                if key in constants.api_manager.jwt_tokens:
                    constants.api_manager.logout(data['host'], data['port'])

                constants.server_manager.remove_telepath_server(data)

                def finish(*args):
                    if utility.screen_manager.current_screen is not self:
                        return

                    self.gen_search_results(constants.server_manager.telepath_servers, fade_in=False, animate_scroll=False)
                    telepath_banner(f"Un-paired from '${data['host']}$'", False)

                Clock.schedule_once(finish, 0)

            dTimer(0, worker).start()

        Clock.schedule_once(
            functools.partial(
                self.show_popup,
                "warning_query",
                "Un-pair Instance",
                desc,
                (None, unpair)
            ), 0
        )


    def _refresh_instances(self):
        constants.server_manager.check_telepath_servers()

        def finish(*args):
            if utility.screen_manager.current_screen is not self:
                return

            self.gen_search_results(constants.server_manager.telepath_servers, fade_in=False, animate_scroll=False)

        Clock.schedule_once(finish, 0)


    def generate_menu(self, **kwargs):
        float_layout = self.generate_list('Select an instance to manage', 'No paired instances')
        float_layout.add_widget(ExitButton('Back', (0.5, 0.11), cycle=True))

        menu_name = "Instance Manager"

        float_layout.add_widget(generate_title(menu_name))
        float_layout.add_widget(generate_footer(f'$Telepath$, {menu_name}', no_background=True))

        self.add_widget(float_layout)

        # Immediately display paired instances from local configuration
        if constants.server_manager.telepath_servers:
            self.gen_search_results(constants.server_manager.telepath_servers)

        # Reconcile current connectivity without blocking screen generation
        dTimer(0, self._refresh_instances).start()


# Telepath user screen (for a server to view connected clients)
class UserButton(ListInstanceButton):

    def _reset_extra(self):
        if self.disable_user:
            Animation.stop_all(self.disable_user)
            self.disable_user.disabled = True
            self.disable_user.button.disabled = True


    def _unpair(self, *args):
        owner = self.recycle_owner

        if owner:
            owner.unpair_user(self.properties)


    def _toggle_user(self, enabled=True, *args):
        owner = self.recycle_owner

        if owner:
            owner.toggle_user(self.properties, enabled)
            Clock.schedule_once(self.refresh_data, 0)


    def update_data(self, user, index):
        owner = self.recycle_owner
        user_key = owner.get_list_key(user) if owner else user.get('id') or f'{user["host"]}/{user["user"]}'

        # Only stop switch animation when recycled for another user
        if self._bound_user_key is not None and self._bound_user_key != user_key:
            Animation.stop_all(self.disable_user.knob)

        self._bound_user_key = user_key

        connected = owner._user_connected(user) if owner else False
        access_disabled = bool(user.get('disabled'))

        self.button.ignore_hover = True
        self.click_function = None

        # User is connected
        if connected:
            self.color_id = [(0.05, 0.05, 0.1, 1), (0.65, 0.65, 1, 1)]

            status_color = (0.529, 1, 0.729, 1)
            status = translate('connected')
            background = os.path.join(paths.ui_assets, 'telepath_button_enabled.png')

        # User is offline
        elif not access_disabled:
            self.color_id = [(0.05, 0.05, 0.1, 1), (0.65, 0.65, 1, 1)]

            status_color = (0.65, 0.65, 1, 1)
            status = translate('offline')
            background = os.path.join(paths.ui_assets, 'list_button.png')

        # User is restricted
        else:
            self.color_id = [(0.05, 0.1, 0.1, 1), (1, 0.6, 0.7, 1)]

            status_color = (1, 0.65, 0.65, 1)
            status = translate('restricted')
            background = os.path.join(paths.ui_assets, 'list_button_disabled.png')

        self.button.background_normal = background
        self.button.background_down = background
        self.hover_background = background

        # Title of user
        self.normal_title = user['user']
        self.hover_title = self.normal_title

        self.title.text = self.normal_title
        self.title.color = self.color_id[1]
        self.title.text_size = (self.button.size_hint_max[0] * 0.58, self.button.size_hint_max[1])

        # Hostname
        self.subtitle.text = user['host'] if user['host'] else user['ip']
        self.subtitle.color = self.color_id[1]
        self.subtitle.default_opacity = 0.65
        self.subtitle.opacity = self.subtitle.default_opacity
        self.subtitle.font_name = self.regular_font

        # Type icon and status
        self.type_image.image.source = os.path.join(paths.ui_assets, 'icons', 'big', 'telepath-user.png')
        self.type_image.image.color = status_color
        self.type_image.image.opacity = 1

        self.type_image.type_label.text = status
        self.type_image.type_label.color = status_color
        self.type_image.type_label.opacity = 0.8
        self.type_image.type_label.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')

        self.type_image.version_label.text = ''
        self.type_image.version_label.opacity = 0

        # Edit button
        self.set_icon_button('unpair.png', self._unpair)

        # Temporary disable switch
        state = not access_disabled

        self.disable_user.disabled = False
        self.disable_user.button.disabled = False
        self.disable_user.button.state = 'down' if state else 'normal'
        self.disable_user.knob.x = self.disable_user.knob_limits[1] if state else self.disable_user.knob_limits[0]
        self.disable_user.knob.color = self.disable_user.color_id[0] if state else self.disable_user.color_id[1]
        self.disable_user.knob.source = os.path.join(paths.ui_assets, f'toggle_button_knob{"_enabled" if state else ""}.png')


    def resize_self(self, *args):
        super().resize_self(*args)

        button = self.button

        # Preserve the original UserButton geometry
        self.title.pos = (button.x + (self.title.text_size[0] / 2.17) - 8.3 + 30, button.y + 31)
        self.subtitle.pos = (button.x + (self.subtitle.text_size[0] / 2.17) - 78, button.y + 8)

        self.type_image.image.x = button.width + button.x - self.type_image.image.width - 8
        self.type_image.image.y = button.y + ((button.height / 2) - (self.type_image.image.height / 2))

        self.type_image.type_label.x = button.width + button.x - (button.padding_x * 9.55) - self.type_image.width - 75
        self.type_image.type_label.y = button.y + (button.height * 0.15)

        if self.disable_layout:
            self.disable_layout.pos = (button.x + button.width + 57, button.y - 23)


    def __init__(self, **kwargs):
        self.disable_layout = None
        self.disable_user = None
        self._bound_user_key = None

        super().__init__(**kwargs)

        # Make this check eventual variable
        self.disable_layout = RelativeLayout(size_hint_max=(10, 10))
        self.disable_user = SwitchButton('telepath-disable', (0.5, 0.5), default_state=True, x_offset=-395, custom_func=self._toggle_user)

        self.disable_layout.add_widget(self.disable_user)
        self.button.add_widget(self.disable_layout)


class TelepathUserScreen(ListLayout, MenuBackground):

    scroll_position = (0.5, 0.52)
    scroll_divisor = 1.82
    scroll_top = 0.795
    scroll_bottom = 0.26

    header_position = (0, 0.89)
    blank_position = 0.48
    page_position = (0.5, 0.887)

    list_view_class = UserButton


    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.online_users = set()
        self.background_color = constants.brighten_color(constants.background_color, -0.09)

        with self.canvas.before:
            self.color = Color(*self.background_color, mode='rgba')
            self.rect = Rectangle(pos=self.pos, size=self.size)


    def on_empty_list(self):
        utility.screen_manager.current = 'TelepathManagerScreen'
        utility.screen_manager.screen_tree = ['MainMenuScreen']
        return True


    @staticmethod
    def _user_key(user):
        return f'{user["host"]}/{user["user"]}'


    def get_list_key(self, user):
        return user.get('id') or self._user_key(user)


    def _online_users(self):
        return {self._user_key(user) for user in constants.api_manager.current_users.values()}


    def prepare_list_results(self, results):
        self.online_users = self._online_users()

        return sorted(
            list(results),
            key = lambda user: self._user_key(user) in self.online_users,
            reverse = True
        )


    def _user_connected(self, user):
        return self._user_key(user) in self.online_users


    def _get_users(self):
        return list(constants.api_manager.authenticated_sessions)


    def unpair_user(self, data):
        if data['host']: display_name = f"{data['host']}/{data['user']}"
        else:            display_name = f"{data['ip']}/{data['user']}"

        desc = f"Un-pairing this user will prevent them from accessing this instance via $Telepath$ until paired again.\n\nAre you sure you want to un-pair '${display_name}$'?"

        def unpair(*args):

            def worker():

                # Log out if possible
                if data['ip'] in constants.api_manager.current_users:
                    constants.api_manager._force_logout(constants.api_manager.current_users[data['ip']]['session_id'])

                constants.api_manager._revoke_session(data['id'])

                def finish(*args):
                    if utility.screen_manager.current_screen is not self:
                        return

                    self.gen_search_results(self._get_users(), fade_in=False, animate_scroll=False)
                    telepath_banner(f"Un-paired '${display_name}$'", False)

                Clock.schedule_once(finish, 0)

            dTimer(0, worker).start()

        Clock.schedule_once(
            functools.partial(
                self.show_popup,
                "warning_query",
                "Un-pair Instance",
                desc,
                (None, unpair)
            ), 0
        )


    def toggle_user(self, user, enabled):
        constants.api_manager._disable_user(user['id'], not enabled)
        user['disabled'] = not enabled


    def generate_menu(self, **kwargs):
        float_layout = self.generate_list('Select a user to manage', 'No paired users')
        float_layout.add_widget(ExitButton('Back', (0.5, 0.12), cycle=True))

        menu_name = "User Manager"

        float_layout.add_widget(generate_title(menu_name))
        float_layout.add_widget(generate_footer(f'$Telepath$, {menu_name}', no_background=True))

        self.add_widget(float_layout)
        self.gen_search_results(self._get_users())


class TelepathHostInput(CreateServerPortInput):
    def __init__(self, **kwargs):
        self.ip = ''
        self.port = ''
        super().__init__(**kwargs)
        self.checking = False
        self.hint_text = f"enter host/IPv4  (default port :${constants.api_manager.default_port}$)"
        self.bind(on_text_validate=self.check_connection)

    def check_connection(self, *a):

        def change_icon(show=True, *a):
            try:
                load_icon = utility.screen_manager.current_screen.load_icon
                Animation.stop_all(load_icon)
                Animation(opacity=1 if show else 0, duration=0.15).start(load_icon)
            except AttributeError:
                pass

        def background(*a):
            self.checking = True
            try:
                data = {'detail': 'Failed to connect'}
                Clock.schedule_once(functools.partial(change_icon, True), 0)
                if constants.check_port(self.ip, int(self.port), timeout=5):
                    data = constants.api_manager.request_pair(self.ip, self.port)
            except: pass

            Clock.schedule_once(functools.partial(change_icon, False), 0)
            self.checking = False

            try:
                if 'detail' in data:
                    self.stinky_text = ' Unable to connect'
                    self.valid(False)
                    return
            except: pass

            if data and utility.screen_manager.current_screen.name == 'TelepathManagerScreen':
                Clock.schedule_once(functools.partial(utility.screen_manager.current_screen.confirm_pair_input, self.ip, self.port), 0)

        if not self.checking: dTimer(0, background).start()
        change_timeout = None

    def update_config(self, *a):
        if self.change_timeout:  self.change_timeout.cancel()
        self.change_timeout = Clock.schedule_once(self.check_connection, 2)

    # Input validation
    def insert_text(self, substring, from_undo=False):

        if not self.text and substring == " ":
            substring = ""

        elif len(self.text) < 30:
            if '\n' in substring: substring = substring.splitlines()[0]
            s = re.sub('[^a-z0-9-:.]', '', substring)

            if ":" in self.text and ":" in s:
                s = ''

            if ("." in s and ((self.cursor_col > self.text.find(":")) and (self.text.find(":") > -1))) or ("." in s and self.text.count(".") >= 3):
                s = ''

            # Add name to current config
            def process(*a): self.process_text(text=(self.text))
            Clock.schedule_once(process, 0)

            return BaseInput.insert_text(self, s, from_undo=from_undo)

    def process_text(self, text=''):
        new_ip = ''
        default_port = constants.api_manager.default_port
        new_port = default_port

        typed_info = text if text else self.text

        # interpret typed information
        if ":" in typed_info: new_ip, new_port = typed_info.split(":")[-2:]
        else:
            if "." in typed_info or not new_port:
                new_ip = typed_info.replace(":", "")
                new_port = default_port
            else:
                new_port = typed_info.replace(":", "")

        if not str(self.port) or not new_port:
            new_port = default_port

        if not str(new_port).isnumeric():
            new_port = default_port

        # Input validation
        try: port_check = ((int(new_port) < 1024 and int(new_port) != 443) or (int(new_port) > 65535))
        except: port_check = True
        ip_check = (constants.check_ip(new_ip) and '.' in typed_info) or new_ip.replace('-', '').replace('.', '').isalnum()
        self.stinky_text = ''
        fail = False

        if typed_info:

            key = f"{new_ip}:{new_port}"
            if key in constants.server_manager.telepath_servers:
                self.stinky_text = ' Host is already added'
                fail = True

            elif '.' not in typed_info and typed_info.isnumeric():
                self.stinky_text = ' Enter an IPv4 address'
                fail = True

            elif not ip_check and ("." in typed_info or ":" in typed_info):
                self.stinky_text = 'Invalid IPv4 address' if not port_check else 'Invalid IPv4 and port'
                fail = True

            elif port_check:
                self.stinky_text = ' Invalid port  (use 1024-65535)'
                fail = True

        else:
            new_ip = ''
            new_port = constants.api_manager.default_port

        if not fail:
            self.ip = new_ip

        if new_port and not fail:
            self.port = int(new_port)

        if fail:
            self.ip = ''
            self.port = default_port

        self.valid(not self.stinky_text)


class TelepathCodeInput(BigBaseInput):
    def __init__(self, ip: str, port: int, **kwargs):
        super().__init__(**kwargs)
        self.ip = ip
        self.port = port

        self.title_text = "pair code"
        self.hint_text = '000-000'
        self.is_valid = True
        self.stinky_text = ''

        self.valign = "center"
        self.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["mono-bold"]}.otf')
        self.font_size = sp(69)
        self.padding_y = (12, 9)
        self.cursor_width = dp(5)
        self.checking = False
        self.bind(on_text_validate=self.check_connection)
        self.fail_count = 0

    def check_connection(self, *a):
        code = self.text.replace('-', '').upper().strip()
        if len(code) != 6:
            self.stinky_text = 'Invalid code length'
            self.valid_text(False, True)
            self.valid(False)
            return
        else:
            self.valid(True)

        def change_icon(show=True, *a):
            try:
                load_icon = utility.screen_manager.current_screen.load_icon
                Animation.stop_all(load_icon)
                Animation(opacity=1 if show else 0, duration=0.15).start(load_icon)
            except AttributeError:
                pass

        def background(*a):
            self.checking = True
            data = None

            Clock.schedule_once(functools.partial(change_icon, True), 0)
            if constants.check_port(self.ip, int(self.port), timeout=5):
                data = constants.api_manager.submit_pair(self.ip, self.port, code)

            Clock.schedule_once(functools.partial(change_icon, False), 0)
            self.checking = False

            try:
                if not data or 'detail' in data:
                    self.stinky_text = '  Unable to connect or invalid code'
                    self.fail_count += 1
                    self.valid_text(False, True)
                    self.valid(False)
            except:
                pass

            if self.fail_count >= 3 and utility.screen_manager.current_screen.name == 'TelepathManagerScreen':
                Clock.schedule_once(functools.partial(utility.screen_manager.current_screen.show_pair_input, True), 0)
                return

            if data and utility.screen_manager.current_screen.name == 'TelepathManagerScreen':
                def back_to_menu(*a):
                    constants.server_manager.refresh_list()
                    utility.screen_manager.current = 'ServerManagerScreen'
                    utility.screen_manager.screen_tree = ['MainMenuScreen']
                    server_name = data['nickname'] if data['nickname'] else data['host']
                    telepath_banner(f"Successfully paired '${server_name}$'", True, play_sound='telepath/success')

                Clock.schedule_once(back_to_menu, 0)
                return

        if not self.checking: dTimer(0, background).start()

    # Ignore popup text
    def insert_text(self, substring, from_undo=False):
        substring = substring.upper()
        if len(substring) > 1:
            substring = ''

        if not self.text and substring == " ":
            substring = ""

        elif len(self.text) < 7:
            if '\n' in substring: substring = substring.splitlines()[0]
            s = re.sub('[^a-zA-Z0-9]', '', substring).upper().replace('O', '0')

            super().insert_text(s, from_undo)
            if len(self.text) == 3: super().insert_text('-')

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

    # Special keypress behaviors
    def keyboard_on_key_down(self, window, keycode, text, modifiers):

        def update_bar(*a):
            if (not self.text.endswith('-')) or keycode[1] == "backspace":
                self.text = self.text.replace('-', '')
            if len(self.text.replace('-', '')) > 3:
                self.text = self.text[:3] + '-' + self.text[3:]

        Clock.schedule_once(update_bar, 0)

        if keycode[1] == "backspace" and control in modifiers:
            original_index = self.cursor_col
            new_text, index = constants.control_backspace(self.text, original_index)
            self.select_text(original_index - index, original_index)
            self.delete_selection()

        else:
            super().keyboard_on_key_down(window, keycode, text, modifiers)


class ParticleMesh(Widget):
    points = ListProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.direction = []
        self._generated = False

        self.point_number = 50
        self.point_radius = 3
        self.line_width = 1
        self.speed = 0.05
        self.max_line_length = 200

        self.line_color = (0.55, 0.55, 0.8)
        self.point_color = (0.8, 0.8, 1)

        # Generate points and fade in
        self.opacity = 0
        self.bind(size=self.plot_points)

    def show(self, *a):
        Animation(opacity=1, duration=3, transition='out_sine').start(self)

    def plot_points(self, *a):
        if self.height > 200 and not self._generated:
            Clock.schedule_once(self.show, 0)
            self._generated = True
            for _ in range(self.point_number):
                x = random.randint(0, round(self.width))
                y = random.randint(0, round(self.height))
                self.points.extend([x, y])
                self.direction.append(random.randint(0, 300))
            Clock.schedule_interval(self.update_positions, self.speed)

    def draw_lines(self):
        self.canvas.after.clear()
        with self.canvas.after:
            for i in range(0, len(self.points), 2):
                for j in range(i + 2, len(self.points), 2):
                    d = self.distance_between_points(self.points[i], self.points[i + 1], self.points[j], self.points[j + 1])
                    if d > self.max_line_length: continue
                    opacity = 1 - (d / self.max_line_length)
                    Color(rgba=[*self.line_color, opacity])
                    Line(points=[self.points[i], self.points[i + 1], self.points[j], self.points[j + 1]], width=self.line_width)
                    Color(rgba=[*self.point_color, opacity])
                Ellipse(pos=(self.points[i] - self.point_radius, self.points[i + 1] - self.point_radius), size=(self.point_radius * 2, self.point_radius * 2))

    def update_positions(self, *args):
        step = 1
        for i, j in zip(range(0, len(self.points), 2), range(len(self.direction))):
            theta = self.direction[j]
            self.points[i] += step * math.cos(theta)
            self.points[i + 1] += step * math.sin(theta)

            if self.off_screen(self.points[i], self.points[i + 1]):
                self.direction[j] = 90 + self.direction[j]

        self.draw_lines()

    @staticmethod
    def distance_between_points(x1, y1, x2, y2):
        return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5

    def off_screen(self, x, y):
        return x < -5 or x > self.width + 5 or y < -5 or y > self.height + 5


class TelepathManagerScreen(MenuBackground):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.menu = 'init'
        self.background_color = constants.brighten_color(constants.background_color, -0.09)
        self.back_button = None
        self.help_button = None
        self.instances_button = None
        self.users_button = None
        self.pair_button = None
        self.api_input = None
        self.api_toggle = None
        self.host_input = None
        self.confirm_input = None
        self.load_icon = None
        self.page_speed = 0.15

        with self.canvas.before:
            self.canvas.clear()

        with self.canvas.before:
            self.color = Color(*self.background_color, mode='rgba')
            self.rect = Rectangle(pos=self.pos, size=self.size)

        # Layouts
        self.main_layout = None
        self.pair_layout = None
        self.confirm_layout = None

    def on_pre_enter(self, *args):
        constants.api_manager.pair_listen = True
        return super().on_pre_enter(*args)

    def on_pre_leave(self, *args):
        constants.api_manager.pair_listen = False
        return super().on_pre_leave(*args)

    def show_pair_input(self, back=False, show=True):
        self.pair_button.disabled = True
        if show:
            self.back_button.custom_func = self.main_menu
            if self.pair_layout:
                self.pair_layout.clear_widgets()

            self.pair_layout = FloatLayout()
            self.pair_layout.opacity = 0
            self.pair_layout.add_widget(InputLabel(pos_hint={"center_x": 0.5, "center_y": 0.55}))
            self.pair_layout.add_widget(HeaderText("Enter the host/port you wish to connect", 'make sure "share this instance" is enabled on the server', (0, 0.75)))
            self.host_input = TelepathHostInput(pos_hint={"center_x": 0.5, "center_y": 0.45}, text='')
            self.pair_layout.add_widget(self.host_input)

            # Spinning pickaxe
            load_icon = AsyncImage()
            load_icon.id = "load_icon"
            load_icon.source = os.path.join(paths.ui_assets, 'animations', 'loading_pickaxe.gif')
            load_icon.size_hint_max = (self.host_input.height / 2.5, self.host_input.height / 2.5)
            load_icon.color = (0.6, 0.6, 1, 1)
            load_icon.pos_hint = {"center_y": 0.45}
            load_icon.allow_stretch = True
            load_icon.anim_delay = utility.anim_speed * 0.02
            load_icon.opacity = 0
            if self.load_icon and self.confirm_layout:
                self.confirm_layout.remove_widget(self.load_icon)
            self.load_icon = load_icon
            self.pair_layout.add_widget(load_icon)

            def recenter(*a):
                def r(*a): load_icon.x = Window.center[0] - (self.host_input.width / 2) + 13
                Clock.schedule_once(r, 0)

            self.pair_layout.bind(pos=recenter, size=recenter)

            # Switch "screens"
            if back:
                def after(*a):
                    self.confirm_layout.opacity = 0
                    self.remove_widget(self.confirm_layout)
                    self.add_widget(self.pair_layout)
                    Animation(opacity=1, duration=self.page_speed).start(self.pair_layout)

                Animation.stop_all(self.confirm_layout)
                Animation(opacity=0, duration=self.page_speed).start(self.confirm_layout)
                Clock.schedule_once(after, self.page_speed + 0.05)

            else:
                def after(*a):
                    self.main_layout.opacity = 0
                    self.remove_widget(self.main_layout)
                    self.add_widget(self.pair_layout)
                    Animation(opacity=1, duration=self.page_speed).start(self.pair_layout)

                Animation.stop_all(self.main_layout)
                Animation(opacity=0, duration=self.page_speed).start(self.main_layout)
                Clock.schedule_once(after, self.page_speed + 0.05)

    def confirm_pair_input(self, ip: str, port: int, show=True):
        self.pair_button.disabled = True
        self.back_button.custom_func = functools.partial(self.show_pair_input, True)
        if show:
            if self.confirm_layout:
                self.confirm_layout.clear_widgets()

            self.confirm_layout = FloatLayout()
            self.confirm_layout.opacity = 0
            self.confirm_layout.add_widget(InputLabel(pos_hint={"center_x": 0.5, "center_y": 0.58}))
            self.confirm_layout.add_widget(HeaderText(f"Enter the pair code from:   $[color=#AAAAEE]{ip}[/color]$", 'if headless, use the "$telepath pair$" command', (0, 0.75)))
            self.confirm_input = TelepathCodeInput(ip, port, pos_hint={"center_x": 0.5, "center_y": 0.45}, text='')
            self.confirm_layout.add_widget(self.confirm_input)

            # Spinning pickaxe
            load_icon = AsyncImage()
            load_icon.id = "load_icon"
            load_icon.source = os.path.join(paths.ui_assets, 'animations', 'loading_pickaxe.gif')
            load_icon.size_hint_max = (self.host_input.height, self.host_input.height)
            load_icon.color = (0.6, 0.6, 1, 1)
            load_icon.pos_hint = {"center_y": 0.45}
            load_icon.allow_stretch = True
            load_icon.anim_delay = utility.anim_speed * 0.02
            load_icon.opacity = 0
            if self.load_icon and self.pair_layout: self.pair_layout.remove_widget(self.load_icon)
            self.load_icon = load_icon
            self.confirm_layout.add_widget(load_icon)

            def recenter(*a):
                def r(*a): load_icon.x = Window.center[0] - (self.host_input.width / 2) + 30
                Clock.schedule_once(r, 0)

            self.confirm_layout.bind(pos=recenter, size=recenter)

            # Switch "screens"
            def after(*a):
                self.pair_layout.opacity = 0
                self.remove_widget(self.pair_layout)
                self.add_widget(self.confirm_layout)
                Animation(opacity=1, duration=self.page_speed).start(self.confirm_layout)

            Animation.stop_all(self.pair_layout)
            Animation(opacity=0, duration=self.page_speed).start(self.pair_layout)
            self.confirm_input.grab_focus()
            Clock.schedule_once(after, self.page_speed + 0.05)

    def main_menu(self):
        # Switch "screens"
        def after(*a):
            self.back_button.custom_func = None
            self.pair_button.disabled = False
            self.pair_layout.opacity = 0
            self.remove_widget(self.pair_layout)
            self.add_widget(self.main_layout)
            Animation(opacity=1, duration=self.page_speed).start(self.main_layout)

        Animation.stop_all(self.pair_layout)
        Animation(opacity=0, duration=self.page_speed).start(self.pair_layout)
        Clock.schedule_once(after, self.page_speed + 0.05)

    def recalculate_buttons(self, *a):
        try: self.main_layout.remove_widget(self.users_button)
        except: pass

        try: self.main_layout.remove_widget(self.instances_button)
        except: pass

        if constants.api_manager.authenticated_sessions and constants.app_config.telepath_settings['enable-api']:
            self.main_layout.add_widget(self.users_button)

            pair_pos = (0.5, 0.42)
            enable_pos = (0.5, 0.29)
            back_pos = (0.5, 0.12)

        elif constants.server_manager.telepath_servers:
            self.main_layout.add_widget(self.instances_button)

            pair_pos = (0.5, 0.42)
            enable_pos = (0.5, 0.29)
            back_pos = (0.5, 0.12)

        else:
            pair_pos = (0.5, 0.5)
            enable_pos = (0.5, 0.35)
            back_pos = (0.5, 0.12)

        self.pair_button.pos_hint = {'center_x': pair_pos[0], 'center_y': pair_pos[1]}
        self.api_input.pos_hint = {'center_x': enable_pos[0], 'center_y': enable_pos[1]}
        self.api_toggle.button.pos_hint = {'center_x': enable_pos[0], 'center_y': enable_pos[1]}
        self.api_toggle.knob.pos_hint = {"center_y": enable_pos[1]}
        self.back_button.text.pos_hint = self.back_button.button.pos_hint = {'center_x': back_pos[0], 'center_y': back_pos[1]}
        self.back_button.icon.pos_hint = {'center_y': back_pos[1]}

    def generate_menu(self, **kwargs):
        self.main_layout = FloatLayout()
        self.main_layout.opacity = 0

        # Add particle background and gradient on top
        particles = ParticleMesh()
        self.add_widget(particles)

        # Menu shadow
        shadow = Image(source=os.path.join(paths.ui_assets, 'menu_shadow.png'))
        shadow.color = self.background_color
        shadow.opacity = 0.8
        shadow.size_hint_max = (600, 600)
        shadow.allow_stretch = True
        shadow.keep_ratio = False
        shadow.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        self.add_widget(shadow)

        gradient = Image(source=os.path.join(paths.ui_assets, 'telepath_gradient.png'))
        gradient.size_hint_max = (None, None)
        gradient.allow_stretch = True
        gradient.keep_ratio = False
        gradient.opacity = 0.6
        gradient.color = constants.brighten_color(self.background_color, 0.03)
        self.add_widget(gradient)

        # Help button
        def show_help():
            help_text = """$Telepath$ is an $auto-mcs$ protocol to control remote sessions seamlessly. For example, $Telepath$ can connect a local computer to an instance of $auto-mcs$ running on a different computer, or a VPS in the cloud.

To connect via $Telepath$, enable “share this instance” on the server you intend to connect. Then click “Pair a Server” on the client and follow the prompts.

Once paired, remote servers will appear in the Server Manager and can be interacted with like normal. You can also import or create a server on a $Telepath$ instance."""

            Clock.schedule_once(
                functools.partial(
                    self.show_popup,
                    "controls",
                    "About $Telepath$",
                    help_text,
                    (None)
                ),
                0
            )

        self.help_button = IconButton('help', {}, (70, 60), (None, None), 'question.png', clickable=True, anchor='right', click_func=show_help)
        self.add_widget(self.help_button)

        # Add telepath logo
        logo = Image(source=os.path.join(paths.ui_assets, 'telepath_logo.png'), allow_stretch=True, size_hint=(None, None), width=dp(400), pos_hint={"center_x": 0.5, "center_y": 0.77})
        logo.color = (0.8, 0.8, 1, 0.9)
        self.main_layout.add_widget(logo)

        session_splash = Label(pos_hint={"center_y": 0.7}, color=(0.7, 0.7, 1, 0.4), font_name=os.path.join(paths.ui_assets, 'fonts', constants.fonts['medium']), font_size=sp(25))
        session_splash.text = 'simplified remote access'
        self.main_layout.add_widget(session_splash)

        # Logic-driven button visibility
        def user_manager(*a): utility.screen_manager.current = "TelepathUserScreen"
        def instance_manager(*a): utility.screen_manager.current = "TelepathInstanceScreen"
        self.users_button = ColorButton("MANAGE USERS", position=(0.5, 0.55), icon_name='person-sharp.png', click_func=user_manager, color=(0.8, 0.8, 1, 1))
        self.instances_button = ColorButton("MANAGE INSTANCES", position=(0.5, 0.55), icon_name='settings-sharp.png', click_func=instance_manager, color=(0.8, 0.8, 1, 1))
        self.pair_button = ColorButton("PAIR A SERVER", position=(0.5, 0.5), icon_name='telepath.png', click_func=functools.partial(self.show_pair_input, False), color=(0.8, 0.8, 1, 1))
        self.main_layout.add_widget(self.pair_button)

        # Enable API toggle button
        def toggle_api(state, only_input=False, *a):
            if not only_input:
                constants.app_config.telepath_settings['enable-api'] = state
                constants.app_config.save_config()
                text = 'enabled' if state else 'disabled'
                constants.telepath_banner(f'$Telepath$ API is now {text}', state)

            # Update hint text
            if state:
                port = constants.api_manager.port
                ip = constants.api_manager.host

                if ip == '0.0.0.0':
                    ip = constants.get_private_ip()

                if constants.public_ip:
                    if constants.check_port(constants.public_ip, port, 0.05):
                        ip = constants.public_ip

                new_text = f">   {ip}:{port}"
                self.api_input.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["italic"]}.ttf')
                self.api_input.hint_text_color = (0.6, 0.9, 1, 1)
                constants.api_manager.start()

            else:
                new_text = 'share this instance'
                self.api_input.hint_text_color = (0.6, 0.6, 1, 0.8)
                self.api_input.font_name = os.path.join(paths.ui_assets, 'fonts', f'{constants.fonts["medium"]}.ttf')
                constants.api_manager.stop()

            self.api_input.hint_text = new_text

        sub_layout = RelativeLayout()
        self.api_input = BlankInput(pos_hint={"center_x": 0.5, "center_y": 0.35}, hint_text="share this instance")
        self.api_toggle = SwitchButton('api', (0.5, 0.35), default_state=constants.app_config.telepath_settings['enable-api'], custom_func=toggle_api)
        sub_layout.add_widget(self.api_input)
        sub_layout.add_widget(self.api_toggle)
        self.main_layout.add_widget(sub_layout)
        if constants.app_config.telepath_settings['enable-api']:
            toggle_api(True, True)

        Clock.schedule_once(self.recalculate_buttons, 0)

        # Static content on each page
        self.add_widget(generate_footer('$Telepath$', no_background=True))
        self.add_widget(self.main_layout)
        Animation(opacity=1, duration=1).start(self.main_layout)
        self.back_button = ExitButton('Back', (0.5, 0.12), cycle=True)
        self.add_widget(self.back_button)


# Telepath notifications and pairing
class TelepathPair():
    def __init__(self):
        self.is_open = False
        self.pair_data = {}

    def close(self):
        if not self.is_open:
            return

        # Normal operation
        try:
            current_user = constants.api_manager.current_users.get(self.pair_data['host']['ip'])
            if current_user and current_user['host'] == self.pair_data['host']['host'] and current_user['user'] == self.pair_data['host']['user']:
                message = f"Successfully paired with '${current_user['host']}/{current_user['user']}$'"
                color = (0.553, 0.902, 0.675, 1)
                sound = 'telepath/success'
            else:
                message = f'$Telepath$ pair request expired'
                color = (0.937, 0.831, 0.62, 1)
                sound = 'popup/warning'

        # Failed to pair
        except Exception as e:
            message = f'$Telepath$ pairing failed'
            color = (0.937, 0.831, 0.62, 1)
            sound = 'popup/warning'
            send_log(self.__class__.__name__, f'failed to pair: {constants.format_traceback(e)}', 'error')

        # Reset token if cancelled
        if constants.api_manager.pair_data:
            constants.api_manager.pair_data = {}

        Clock.schedule_once(
            functools.partial(
                utility.screen_manager.current_screen.show_banner,
                color,
                message,
                "telepath.png",
                2.5,
                {"center_x": 0.5, "center_y": 0.965},
                sound
            ), 0.1
        )

        self.is_open = False
        self.pair_data = {}

    def open(self, data: dict):
        if self.is_open:
            return

        self.pair_data = data

        # If the application is blocked, wait until it's not to show the pop-up
        def wait_thread(*a):
            self.is_open = True
            while constants.ignore_close or utility.screen_manager.current_screen.popup_widget:
                time.sleep(1)

            Clock.schedule_once(
                functools.partial(
                    utility.screen_manager.current_screen.show_popup,
                    "pair_request",
                    " ",
                    self.pair_data,
                    self.close
                ), 0
            )

        dTimer(0, wait_thread).start()


constants.telepath_pair = TelepathPair()

# </editor-fold> ///////////////////////////////////////////////////////////////////////////////////////////////////////
