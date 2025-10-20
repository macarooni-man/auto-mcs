from source.ui.desktop.widgets.buttons import HoverButton
from source.ui.desktop.widgets.base import *



# -----------------------------------------  Base Text Input Functionality  --------------------------------------------

# Root TextInput for global behavior
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
                if self.title.text: interaction += f" ({self.title.text.title()})"
                constants.last_widget = interaction + f" @ {constants.format_now()}"
                send_log('navigation', f"interaction: '{interaction}'")
            except: pass

        # Update screen focus value on next frame
        def update_focus(*args): utility.screen_manager.current_screen._input_focused = self.focus
        Clock.schedule_once(update_focus, 0)


    def grab_focus(self, *a):
        def focus_later(*args): self.focus = True
        Clock.schedule_once(focus_later, 0)


    def fix_overscroll(self, *args):
        if self.cursor_pos[0] < (self.x): self.scroll_x = 0


    def update_rect(self, *args):
        self.rect.source = os.path.join(paths.ui_assets, f'text_input_cover{"" if self.focused else "_fade"}.png')

        self.title.text = self.title_text
        self.rect.width = (len(self.title.text) * 16) + 116 if self.title.text else 0
        if self.width > 500: self.rect.width += (self.width - 500)
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
        if popup_widget: return
        else: return super().on_touch_down(touch)

    # Special keypress behaviors
    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        if keycode[1] == "backspace" and control in modifiers:
            original_index = self.cursor_col
            new_text, index = constants.control_backspace(self.text, original_index)
            self.select_text(original_index - index, original_index)
            self.delete_selection()
        else: super().keyboard_on_key_down(window, keycode, text, modifiers)


# Should be placed on the same page, status text to be updated by BaseInput
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
        try: utility.screen_manager.current_screen.next_button.disable(disable)
        except AttributeError: pass


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

            def reset_color(item, *args): item.color = (1, 0.53, 0.58, 0)
            Clock.schedule_once(functools.partial(reset_color, child), 0.12)



# ---------------------------------------------- Utility Text Inputs  --------------------------------------------------

# Search bar widget group for updating a layout/data
class SearchBar(FloatLayout):
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

    class SearchButton(HoverButton):

        # Execute search on click
        def on_touch_down(self, touch):
            if self.collide_point(touch.x, touch.y):
                for child in self.parent.children:
                    if child.id == "search_input":
                        child.focus = False
                        if not child.text or self.parent.previous_search != child.text:
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

    def __init__(self, return_function=None, server_info=None, pos_hint={"center_x": 0.5, "center_y": 0.5}, allow_empty=False, **kwargs):
        super().__init__(**kwargs)
        self.previous_search = ""
        self.return_function = return_function
        self.server_info     = server_info

        # Input box
        self.search_input = self.SearchInput(return_function, allow_empty)
        self.search_input.pos_hint = pos_hint

        # Search icon on the right of box
        self.search_button = self.SearchButton()
        self.search_button.pos_hint = {"center_y": pos_hint['center_y']}
        self.search_button.size_hint_max = (self.search_input.height / 3.6, self.search_input.height / 3.6)

        # Loading icon to swap button
        self.load_icon = AsyncImage()
        self.load_icon.id = "load_icon"
        self.load_icon.source = os.path.join(paths.ui_assets, 'animations', 'loading_pickaxe.gif')
        self.load_icon.size_hint_max = (self.search_input.height / 3, self.search_input.height / 3)
        self.load_icon.color = (0.6, 0.6, 1, 0)
        self.load_icon.pos_hint = {"center_y": pos_hint['center_y']}
        self.load_icon.allow_stretch = True
        self.load_icon.anim_delay = utility.anim_speed * 0.02

        # Assemble layout
        self.bind(pos=self.repos_button)
        self.bind(size=self.repos_button)

        self.add_widget(self.search_input)
        self.add_widget(self.search_button)
        self.add_widget(self.load_icon)


    def repos_button(self, *args):
        def after_window(*args):
            self.search_button.x = self.search_input.x + self.search_input.width - self.search_button.width - 18
            self.load_icon.x     = self.search_input.x + self.search_input.width - self.load_icon.width - 14

        Clock.schedule_once(after_window, 0)

    # Gather search results from passed in function
    def execute_search(self, query, *a):
        self.previous_search = query

        def execute():
            current_screen = utility.screen_manager.current_screen.name
            self.loading(True)
            results = False

            try: results = self.return_function(query) if not self.server_info else \
                           self.return_function(query, self.server_info)
            except ConnectionRefusedError: pass

            if not results and isinstance(results, bool): self.previous_search = ""

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
                    if boolean_value: Animation(color=(0.6, 0.6, 1, 1), duration=0.05).start(child)
                    else:             Animation(color=(0.6, 0.6, 1, 0), duration=0.2).start(child)

                if child.id == "search_button": utility.hide_widget(child, boolean_value)

        Clock.schedule_once(main_thread, 0)


# TextInput that supports auto-complete when typing filesystem paths
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

        word_list = [item for item in word_list if not (len(item) == 3 and ":\\" in item) and not (len(item) == 2 and ":" in item) and item]

        val = value[value.rfind('     ') + 1:]
        if not val: return
        try:
            # grossly inefficient just for demo purposes
            word = [word for word in word_list if word.startswith(val)][0][len(val):]
            if not word: return
            self.text_hint.text.text = self.text + word
        except IndexError: pass

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

        else: self.suggestion_index = 0

        return super().keyboard_on_key_down(window, keycode, text, modifiers)


# A taller and bigger font input (Used for the Telepath pair code)
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
        if self.width > 500: self.rect.width += (self.width - 500)
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


# Creates an BaseInput that is disabled for displaying text in the same style
class BlankInput(BaseInput):

    def __init__(self, pos_hint, hint_text, disabled=False, **kwargs):
        super().__init__(**kwargs)
        self.halign = "left"
        self.padding_x = 25
        self.size_hint_max = (440, 54)
        self.hint_text_color = (0.6, 0.6, 1, 0.8)
        self.title_text = ""
        self.hint_text = ""
        self.bind(on_text_validate=self.on_enter)

        self.pos_hint = pos_hint
        self.hint_text = hint_text
        self.disable(disabled)


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



# ---------------------------------------------  Specific Text Inputs  -------------------------------------------------

class ServerNameInput(BaseInput):

    def get_server_list(self):
        try:
            telepath_data = foundry.new_server_info['_telepath_data']
            if telepath_data:
                self.server_list = constants.get_remote_var('server_manager.server_list_lower', telepath_data)
                return True
        except: pass
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
        if click_next:
            try:
                next_button = utility.screen_manager.current_screen.next_button
                if not next_button.disabled: next_button.force_click()
            except AttributeError: pass


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
            if '\n' in substring: substring = substring.splitlines()[0]
            s = re.sub('[^a-zA-Z0-9 _().-]', '', substring)

            is_valid = (self.text + s).lower().strip() not in self.server_list
            self.valid(is_valid, ((len(self.text + s) > 0) and not (str.isspace(self.text))))

            # Add name to current config
            def get_text(*a): foundry.new_server_info['name'] = self.text.strip()
            Clock.schedule_once(get_text, 0)

            return super().insert_text(s, from_undo=from_undo)



    def update_server(self, force_ignore=False, hide_popup=False):

        def disable_next(disable=False):
            try: utility.screen_manager.current_screen.next_button.children.disable(disable)
            except AttributeError: pass

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
        except: pass
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

            except AttributeError: pass


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
            if '\n' in substring: substring = substring.splitlines()[0]
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
        if not constants.version_loading: super().on_touch_down(touch)
        else: self.focus = False


    def on_enter(self, value):
        if not constants.version_loading:
            if self.text: foundry.new_server_info['version'] = (self.text).strip()
            else:         foundry.new_server_info['version'] = foundry.latestMC[foundry.new_server_info['type']]

            if self.enter_func: self.enter_func()

            try:
                next_button = utility.screen_manager.current_screen.next_button
                if not next_button.disabled: next_button.force_click()
            except AttributeError: pass


    def valid_text(self, boolean_value, text):
        if not constants.version_loading:
            if isinstance(text, bool): text = ''

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

                except AttributeError: pass


    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        if not constants.version_loading:

            super().keyboard_on_key_down(window, keycode, text, modifiers)

            if keycode[1] == "backspace":
                # Add name to current config
                self.valid(True, True)

                if self.text: foundry.new_server_info['version'] = (self.text).strip()
                else:         foundry.new_server_info['version'] = foundry.latestMC[foundry.new_server_info['type']]


    # Input validation
    def insert_text(self, substring, from_undo=False):

        if not constants.version_loading:

            if not self.text and substring == " ":
                substring = ""

            elif len(self.text) < 10:
                self.valid(True, True)

                if '\n' in substring: substring = substring.splitlines()[0]
                s = re.sub('[^a-eA-E0-9 .wpreWPRE-]', '', substring).lower()

                # Add name to current config
                if self.text + s:
                    def get_text(*a): foundry.new_server_info['version'] = self.text.strip()
                    Clock.schedule_once(get_text, 0)
                else: foundry.new_server_info['version'] = foundry.latestMC[foundry.new_server_info['type']]

                return super().insert_text(s, from_undo=from_undo)


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

                except AttributeError: continue

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

                if check_world[0] or hide_popup: world_valid()
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

                    else: world_valid()


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

                except AttributeError: continue

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
                    box_text = os.path.join(*Path(os.path.abspath(utility.screen_manager.current_screen.new_world)).parts[-2:])
                    self.cache_text = self.text = box_text[:30] + "..." if len(box_text) > 30 else box_text

                def world_valid():
                    def execute(*a):
                        box_text = os.path.join(*Path(os.path.abspath(self.selected_world)).parts[-2:])
                        self.cache_text = self.text = box_text[:30] + "..." if len(box_text) > 30 else box_text
                        try:
                            utility.screen_manager.current_screen.new_world = self.selected_world
                            self.valid_text(True, True)
                            self.parent.parent.toggle_new(True)
                        except AttributeError: pass
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

                if check_world[0] or hide_popup: world_valid()
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

                    else: world_valid()


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

                        except AttributeError: continue

        except Exception as e:
            send_log(self.__class__.__name__, f"failed to focus input box: {constants.format_traceback(e)}", 'warning')

    def on_enter(self, value):

        foundry.new_server_info['server_settings']['seed'] = (self.text).strip()

        try:
            next_button = utility.screen_manager.current_screen.next_button
            if not next_button.disabled: next_button.force_click()
        except AttributeError: pass

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

                        except AttributeError: continue

        except Exception as e:
            send_log(self.__class__.__name__, f"failed to focus input box: {constants.format_traceback(e)}", 'warning')

    def on_enter(self, value):

        utility.screen_manager.current_screen.new_seed = (self.text).strip()

        try:
            next_button = utility.screen_manager.current_screen.next_button
            if not next_button.disabled: next_button.force_click()
        except AttributeError: pass

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
            if '\n' in substring: substring = substring.splitlines()[0]
            s = re.sub('[^a-zA-Z0-9 _/{}=+|"\'()*&^%$#@!?;:,.-]', '', substring)

            # Add name to current config
            def get_text(*a): utility.screen_manager.current_screen.new_seed = self.text.strip()
            Clock.schedule_once(get_text, 0)

            return super().insert_text(s, from_undo=from_undo)


class ServerImportPathInput(DirectoryInput):

    def get_server_list(self):
        try:
            telepath_data = foundry.new_server_info['_telepath_data']
            if telepath_data:
                self.server_list = constants.get_remote_var('server_manager.server_list_lower', telepath_data)
                return True
        except: pass
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

                except AttributeError: continue

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
                        if isinstance(text, str) and text: child.update_text(text)
                        else: child.update_text('This server is invalid or corrupt')
                        self.text = ""
                # Valid input
                    else: child.clear_text()
                    break

            except AttributeError: pass


    def update_server(self, force_ignore=False, hide_popup=False):

        def disable_next(disable=False):
            try: utility.screen_manager.current_screen.next_button.disable(disable)
            except AttributeError: pass

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
                    except AttributeError: pass


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
        except: pass
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
                    else: child.clear_text()
                    break
            except AttributeError: pass


    def update_server(self, force_ignore=False, hide_popup=False):

        def disable_next(disable=False):
            try: utility.screen_manager.current_screen.next_button.disable(disable)
            except AttributeError: pass

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
                        except: pass
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
                    except AttributeError: pass


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

                except AttributeError: continue

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
                    else: child.clear_text()
                    break

            except AttributeError: pass

    def update_server(self, force_ignore=False, hide_popup=False):

        def disable_next(disable=False):
            try: utility.screen_manager.current_screen.next_button.disable(disable)
            except AttributeError: pass

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
                    except AttributeError: pass


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

        try:
            next_button = utility.screen_manager.current_screen.next_button
            if not next_button.disabled: next_button.force_click()
        except AttributeError: pass


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

            except AttributeError: pass


    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        super().keyboard_on_key_down(window, keycode, text, modifiers)

        if keycode[1] == "backspace":
            self.process_text()


    # Input validation
    def insert_text(self, substring, from_undo=False):

        if not self.text and substring == " ":
            substring = ""

        elif len(self.text) < 21:
            if '\n' in substring: substring = substring.splitlines()[0]
            s = re.sub('[^0-9:.]', '', substring)

            if ":" in self.text and ":" in s:
                s = ''
            if ("." in s and ((self.cursor_col > self.text.find(":")) and (self.text.find(":") > -1))) or ("." in s and self.text.count(".") >= 3):
                s = ''

            # Add name to current config
            def process(*a): self.process_text(text=(self.text))
            Clock.schedule_once(process, 0)

            return super().insert_text(s, from_undo=from_undo)


    def process_text(self, text=''):

        typed_info = text if text else self.text

        # interpret typed information
        if ":" in typed_info: foundry.new_server_info['ip'], foundry.new_server_info['port'] = typed_info.split(":")[-2:]
        else:
            if "." in typed_info:
                foundry.new_server_info['ip'] = typed_info.replace(":", "")
                foundry.new_server_info['port'] = "25565"
            else: foundry.new_server_info['port'] = typed_info.replace(":", "")

        if not foundry.new_server_info['port']: foundry.new_server_info['port'] = "25565"

        # print("ip: " + foundry.new_server_info['ip'], "port: " + foundry.new_server_info['port'])

        # Input validation
        try: port_check = ((int(foundry.new_server_info['port']) < 1024) or (int(foundry.new_server_info['port']) > 65535))
        except ValueError: port_check = False
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
            try: utility.screen_manager.current_screen.check_changes(server_obj, force_banner=True)
            except AttributeError: pass
            server_obj.write_config()
            server_obj.reload_config()
            change_timeout = None

        if self.change_timeout: self.change_timeout.cancel()
        self.change_timeout = Clock.schedule_once(write, 0.7)

    def process_text(self, text=''):
        server_obj = constants.server_manager.current_server
        new_ip = ''
        default_port = "25565"
        new_port = default_port

        typed_info = text if text else self.text

        # interpret typed information
        if ":" in typed_info: new_ip, new_port = typed_info.split(":")[-2:]
        else:
            if "." in typed_info or not new_port:
                new_ip = typed_info.replace(":", "")
                new_port = default_port
            else: new_port = typed_info.replace(":", "")

        if not str(server_obj.port) or not new_port: new_port = default_port

        # Input validation
        try: port_check = ((int(new_port) < 1024) or (int(new_port) > 65535))
        except ValueError: port_check = False
        ip_check = (constants.check_ip(new_ip) and '.' in typed_info) and self._allow_ip
        self.stinky_text = ''
        fail = False

        if typed_info:

            if not ip_check and ("." in typed_info or ":" in typed_info):
                if not self._allow_ip: self.stinky_text = "Can't use IP with proxy"
                else: self.stinky_text = 'Invalid IPv4 address' if not port_check else 'Invalid IPv4 and port'
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
            try: utility.screen_manager.current_screen.check_changes(server_obj, force_banner=True)
            except AttributeError: pass

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

        try:
            next_button = utility.screen_manager.current_screen.next_button
            if not next_button.disabled: next_button.force_click()
        except AttributeError: pass

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
            if '\n' in substring: substring = substring.splitlines()[0]
            s = re.sub('[^a-zA-Z0-9 _/{}=+|"\'()*&^%$#@!?;:,.-]', '', substring)

            # Add name to current config
            def get_text(*a): foundry.new_server_info['server_settings']['motd'] = self.text.strip() if self.text else "A Minecraft Server"
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

        if self.change_timeout: self.change_timeout.cancel()
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
            if '\n' in substring: substring = substring.splitlines()[0]
            s = re.sub('[^a-zA-Z0-9 _/{}=+|"\'()*&^%$#@!?;:,.-]', '', substring)

            # Add name to current config
            def get_text(*a): self.update_text(self.text.strip() if self.text else "A Minecraft Server")
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
            if '\n' in substring: substring = substring.splitlines()[0]
            s = re.sub('[^0-9]', '', substring)

            # Add name to current config
            def get_text(*a): foundry.new_server_info['server_settings']['max_players'] = self.text.strip() if self.text else "20"
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
            if '\n' in substring: substring = substring.splitlines()[0]
            s = re.sub('[^0-9]', '', substring)

            # Add name to current config
            def get_text(*a): foundry.new_server_info['server_settings']['random_tick_speed'] = self.text.strip() if self.text else "3"
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

                except AttributeError: continue

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
            if '\n' in substring: substring = substring.splitlines()[0]
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
            try:
                next_button = utility.screen_manager.current_screen.next_button
                if not next_button.disabled: next_button.force_click()
            except AttributeError: pass


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

            except AttributeError: pass


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

            if '\n' in substring: substring = substring.splitlines()[0]
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

        if self.change_timeout: self.change_timeout.cancel()
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

        if self.server_obj.custom_flags: self.text = self.server_obj.custom_flags

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

            except AttributeError: pass


    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        super().keyboard_on_key_down(window, keycode, text, modifiers)

        if keycode[1] == "backspace":
            self.process_text()


    # Input validation
    def insert_text(self, substring, from_undo=False):

        if not self.text and substring[0] not in ['-', '@', '<']:
            substring = ""

        elif len(self.text) < 5000:
            if '\n' in substring:  substring = ' '.join(substring.splitlines())
            if len(substring) > 2: substring = substring.strip()
            s = substring

            # Add name to current config
            def process(*a): self.process_text(text=(self.text))
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
            if space_check or not flag_check: self.stinky_text = 'Invalid formatting'
            elif memory_check:                self.stinky_text = '   Configure memory above'
            else:                             self.write_config(typed_info.strip())

        else: self.write_config('')

        self.valid(not self.stinky_text)
