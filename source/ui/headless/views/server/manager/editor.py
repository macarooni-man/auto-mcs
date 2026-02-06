# ------------------------------------------- 'server.properties' Editor -----------------------------------------------

class PropertiesEditor():

    # Custom ListBox to handle focus movement and wrapping
    class SearchListBox(urwid.ListBox):
        def __init__(self, body, editor):
            super().__init__(body)
            self.editor = editor

        def keypress(self, size, key):
            if key in ('up', 'down'):
                if self.editor.search_mode:
                    self.editor.handle_search_navigation(key)
                    return None  # Consume the key event
                else:
                    self.editor.handle_navigation(key)
                    return None  # Consume the key event
            return super().keypress(size, key)

        def mouse_event(self, size, event, button, col, row, focus):
            if event == 'mouse press' and button in (4, 5):  # Scroll up/down
                key = 'up' if button == 4 else 'down'
                if self.editor.search_mode:
                    self.editor.handle_search_navigation(key)
                    return True  # Consume the event
                else:
                    self.editor.handle_navigation(key)
                    return True  # Consume the event
            return super().mouse_event(size, event, button, col, row, focus)

    class Scrollbar(urwid.WidgetWrap):
        def __init__(self, listbox):
            self.listbox = listbox  # This is the ListBox
            self.scrollbar = urwid.WidgetPlaceholder(urwid.SolidFill(' '))  # Placeholder for the scrollbar
            self.thumb_char = '▐'
            # Combine the ListBox and the scrollbar
            self.widget = urwid.Columns([
                ('weight', 1, self.listbox),
                ('fixed', 1, self.scrollbar)
            ], focus_column=0)
            super().__init__(self.widget)

        def render(self, size, focus=False):
            # size is a tuple (maxcol, maxrow)
            maxcol, maxrow = size
            # Update the scrollbar with the current size
            self._update_scrollbar(size)
            # Render the widget
            return self.widget.render(size, focus=focus)

        def _update_scrollbar(self, size):
            maxcol, maxrow = size
            listbox = self.listbox

            total_lines = len(listbox.body)
            if total_lines == 0:
                thumb_size = maxrow
                thumb_position = 0
            else:
                # Calculate the visible portion
                focus_position = listbox.body.focus
                if focus_position is None:
                    focus_position = 0

                # Estimate the number of lines per screen
                lines_per_screen = maxrow
                thumb_size = max(1, round(int(lines_per_screen * maxrow / total_lines) / 2))
                thumb_position = int(
                    focus_position * (maxrow - thumb_size) / (max(1, total_lines - lines_per_screen) * 1.8))

                # Clamp thumb_position to ensure it stays within the scrollbar
                thumb_position = max(0, min(thumb_position, maxrow - thumb_size))

            # Create the scrollbar thumb using the "▐" character
            scrollbar_thumb = urwid.AttrMap(urwid.SolidFill(self.thumb_char), 'scrollbar_thumb')

            # Create spaces above and below the thumb
            scrollbar_top = urwid.SolidFill(' ')
            scrollbar_bottom = urwid.SolidFill(' ')

            # Build the scrollbar pile
            scrollbar_pile = urwid.Pile([
                ('fixed', thumb_position, scrollbar_top),
                ('fixed', thumb_size, scrollbar_thumb),
                ('weight', 1, scrollbar_bottom)
            ])

            self.scrollbar.original_widget = scrollbar_pile

        def keypress(self, size, key):
            return self.widget.keypress(size, key)

        def mouse_event(self, size, event, button, col, row, focus):
            return self.widget.mouse_event(size, event, button, col, row, focus)

    def __init__(self, server_name: str):
        self.server_name = server_name
        self.file_path = manager.server_path(server_name, 'server.properties')
        self.properties = self.load_properties()
        self.search_mode = False
        self.search_term = ""
        self.search_results = []
        self.focused_result = 0
        self.previous_focus = None
        self.current_index = 0

        self.widget_info = []  # Store references to widgets
        self.loop = None  # Will be set later

        self.list_walker = urwid.SimpleFocusListWalker(self.build_ui())
        self.listbox = self.SearchListBox(self.list_walker, self)
        self.search_edit = urwid.Edit(('search_bar', "Search: "))
        self.matches_display = urwid.Text("", align='right')
        search_columns = urwid.Columns([
            ('weight', 1, self.search_edit),
            ('pack', self.matches_display)
        ], dividechars=1)
        self.search_widget = urwid.AttrMap(search_columns, 'search_bar')

        # Help text to be displayed when search bar is hidden
        self.help_text = urwid.Text(('search_bar', " ESC - save & quit, CTRL+F - search "), align='center')

        # Wrap the ListBox with the Scrollbar
        self.scrollbar = self.Scrollbar(self.listbox)

        # Initially show the help text at the footer
        self.main_widget = urwid.Frame(
            body=self.scrollbar,
            footer=self.help_text  # Show help text by default
        )

    def connect_signals(self):
        urwid.connect_signal(self.list_walker, 'modified', self.render_focus)
        urwid.connect_signal(self.search_edit, 'change', self.on_search_edit_change)

    # Load server.properties file
    def load_properties(self):
        properties = []

        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as f:
                content = f.read()
                if content.strip():

                    for line in content.splitlines():

                        if line.startswith("#"):
                            properties.append(('comment', line.strip().replace('# ', '#'), None))

                        elif '=' in line:
                            key, value = line.strip().split('=', 1)
                            properties.append(('entry', key, value))

                        else:
                            properties.append(('raw', line.strip(), None))

        if not properties:
            manager.fix_empty_properties(self.server_name)
            return self.load_properties()

        return properties

    # Save properties back to the file
    def save_properties(self):
        final_text = []
        for i, widget in enumerate(self.list_walker):

            # Skip divider lines
            if isinstance(widget, urwid.Divider):
                continue

            # Normal line
            if isinstance(widget, urwid.Columns) and len(widget.contents) >= 4:
                key_widget = widget.contents[1][0]
                key = urwid.Text.get_text(key_widget)[0]
                value_placeholder = widget.contents[3][0]
                value_widget = value_placeholder.original_widget

                if isinstance(value_widget, urwid.AttrMap):
                    value_widget = value_widget.original_widget

                if isinstance(value_widget, urwid.Edit):
                    value = value_widget.get_edit_text()
                elif isinstance(value_widget, urwid.Text):
                    value = ''.join([t for attr, t in value_widget.text])
                else:
                    value = ''

                final_text.append(f'{key}={value}\n')

            # Comment
            elif isinstance(widget, urwid.Columns):
                comment = widget.contents[1][0].get_text()[0]
                final_text.append(f'{comment.replace("# ", "#")}\n')

        if final_text:
            with open(self.file_path, 'w') as f:
                f.writelines(final_text)

    def build_ui(self):
        widgets = []
        self.editable_indices = []  # Indices of editable lines
        for i, (entry_type, key, value) in enumerate(self.properties):

            # Comments
            if entry_type == 'comment':
                line_number_widget = urwid.Text(('line', f"{i + 1:3} "), align='right')
                comment_widget = urwid.Text(('comment', key.replace('#', '# ')))
                line_widget = urwid.Columns([
                    ('fixed', 4, line_number_widget),
                    comment_widget
                ], dividechars=1)
                widgets.append(line_widget)
                widgets.append(urwid.Divider())

            # Key and Value entries
            elif entry_type == 'entry':
                line_number_widget = urwid.Text(('line_number', f"{i + 1:3} "), align='right')
                key_widget = urwid.Text(('key', key))
                equal_sign_widget = urwid.Text(('line', '= '))

                # Define the value widget
                value_widget = urwid.Edit('', value)
                value_wrapper = urwid.AttrMap(value_widget, self.value_type(value))
                value_wrapper.edit = value_widget
                urwid.connect_signal(value_widget, 'change', functools.partial(self.on_edit, value_wrapper))

                # Wrap the value widget in a WidgetPlaceholder
                value_placeholder = urwid.WidgetPlaceholder(value_wrapper)

                # Assemble the columns
                columns = urwid.Columns([
                    ('fixed', 4, line_number_widget),
                    ('fixed', 20, key_widget),
                    ('fixed', 2, equal_sign_widget),
                    ('weight', 1, value_placeholder)
                ], dividechars=1)

                # Store the index before appending the widget
                widget_index = len(widgets)

                widgets.append(columns)
                widgets.append(urwid.Divider())

                self.editable_indices.append(widget_index)

                # Store references for later use
                self.widget_info.append({
                    'index': widget_index,
                    'entry_type': entry_type,
                    'key': key,
                    'value': value,
                    'key_widget': key_widget,
                    'value_widget': value_widget,
                    'value_placeholder': value_placeholder,
                    'value_wrapper': value_wrapper,
                    'line_widget': columns
                })

            else:
                widgets.append(urwid.Text(key))
                widgets.append(urwid.Divider())

        return widgets

    def toggle_search(self):
        if self.search_mode:
            self.search_mode = False
            self.main_widget.footer = self.help_text  # Show the help text again
            self.reset_highlighting()
            self.matches_display.set_text("")

            # Restore focus and explicitly set the cursor position after a short delay
            self.loop.set_alarm_in(0.01, self.restore_focus_and_cursor)
        else:
            self.search_mode = True
            self.previous_focus = self.listbox.get_focus()[1]  # Save current focus
            self.main_widget.footer = self.search_widget  # Show the search bar
            self.main_widget.set_focus('footer')
            if self.search_term:
                self.perform_search()

    def restore_focus_and_cursor(self, loop=None, user_data=None):
        focus_widget, focus_position = self.listbox.get_focus()

        # Explicitly set focus to the current line
        if focus_widget:
            self.listbox.set_focus(focus_position)

            # Ensure the cursor is placed at the end of the Edit widget if applicable
            self.set_cursor_to_end()

            # Force a screen redraw to ensure the cursor is visible
            self.loop.draw_screen()

    def set_cursor_to_end(self):
        focus_widget, focus_position = self.listbox.get_focus()

        # Ensure that we are focusing on an editable line
        if focus_position is not None and isinstance(self.list_walker[focus_position], urwid.Columns):
            value_placeholder = self.list_walker[focus_position].contents[3][0]
            value_widget = value_placeholder.original_widget

            if isinstance(value_widget, urwid.AttrMap):
                value_widget = value_widget.original_widget

            if isinstance(value_widget, urwid.Edit):
                # Explicitly move cursor to the end of the line
                value_widget.set_edit_pos(len(value_widget.get_edit_text()))

    def reset_highlighting(self):
        for info in self.widget_info:
            if info['entry_type'] == 'entry':
                key = info['key']
                key_widget = info['key_widget']
                value_placeholder = info['value_placeholder']
                value_wrapper = info['value_wrapper']

                # Reset key_widget text
                key_widget.set_text(('key', key))

                # Reset value_placeholder to original value_wrapper if needed
                if value_placeholder.original_widget != value_wrapper:
                    value_placeholder.original_widget = value_wrapper

    def on_search_edit_change(self, edit, new_edit_text):
        self.search_term = new_edit_text
        self.loop.set_alarm_in(0, lambda *_: self.perform_search())

    def perform_search(self):
        self.search_results = []
        self.search_term = self.search_edit.get_edit_text()
        if not self.search_term:
            self.reset_highlighting()
            self.matches_display.set_text("")
            return

        for info in self.widget_info:
            if info['entry_type'] == 'entry':
                key = info['key']
                value_widget = info['value_widget']
                value = value_widget.get_edit_text()
                key_widget = info['key_widget']
                value_placeholder = info['value_placeholder']
                value_wrapper = info['value_wrapper']

                # Reset key_widget text
                key_widget.set_text(('key', key))

                # Reset value_placeholder to original value_wrapper if needed
                if value_placeholder.original_widget != value_wrapper:
                    value_placeholder.original_widget = value_wrapper

                # Now, check for matches
                key_matches = self.search_term.lower() in key.lower()
                value_matches = self.search_term.lower() in value.lower()

                # For key
                if key_matches:
                    highlighted_key = self.highlight_text(key, self.search_term, default_attr='key')
                    key_widget.set_text(highlighted_key)
                else:
                    key_widget.set_text(('key', key))

                # For value
                if value_matches:
                    # Determine the value_type attribute
                    value_type_attr = self.value_type(value)
                    highlighted_value = self.highlight_text(value, self.search_term, default_attr=value_type_attr)
                    highlighted_value_widget = urwid.Text(highlighted_value)
                    value_placeholder.original_widget = highlighted_value_widget
                else:
                    # Restore the value_placeholder to the Edit widget if it was replaced
                    if value_placeholder.original_widget != value_wrapper:
                        value_placeholder.original_widget = value_wrapper

                # Add to search results if either key or value matches
                if key_matches or value_matches:
                    self.search_results.append(info['index'])

        if self.search_results:
            self.focused_result = 0
            self.focus_search_result(self.focused_result)
        else:
            # No results, update matches display
            self.matches_display.set_text("No Results")

    def highlight_text(self, text, term, default_attr=None):
        # Split the text into parts where the term occurs (case-insensitive)
        regex = re.compile('(' + re.escape(term) + ')', flags=re.IGNORECASE)
        parts = regex.split(text)
        # Apply highlighting to the matched terms
        result = []
        for part in parts:
            if not part:
                continue  # Skip empty strings
            if regex.fullmatch(part):
                result.append(('search_highlight', part))
            else:
                if default_attr:
                    result.append((default_attr, part))
                else:
                    result.append(part)
        return result

    def focus_search_result(self, index):
        if self.search_results:
            self.focused_result = index % len(self.search_results)
            self.loop.set_alarm_in(0, lambda *_: self.listbox.set_focus(self.search_results[self.focused_result]))
            # Update matches display
            self.matches_display.set_text(f"{self.focused_result + 1} / {len(self.search_results)} Results")
        else:
            self.matches_display.set_text("No Results")

    @staticmethod
    def return_to_menu():
        screen_manager.current_screen('MainMenuScreen')

    def handle_input(self, key):
        # Ignore mouse events
        if isinstance(key, tuple):
            return

        # Close search or save & quit
        if key == 'esc':
            if self.search_mode:
                self.toggle_search()
            else:
                self.save_properties()
                self.return_to_menu()

        # Quit without saving
        elif key in ['ctrl c', 'ctrl q']:
            self.return_to_menu()

        # Toggle search
        elif key == 'ctrl f':
            self.toggle_search()
        elif self.search_mode:
            if key == 'esc':
                self.toggle_search()
            elif key in ('up', 'down', 'page up', 'page down', 'n', 'p'):
                # Handle navigation keys in search mode
                self.handle_search_navigation(key)
            else:
                # Allow the search_edit widget to handle the key
                maxcol = self.loop.screen_size[0]
                self.search_edit.keypress((maxcol,), key)
        else:
            # Handle navigation keys
            if key in ('up', 'down', 'page up', 'page down'):
                self.handle_navigation(key)
            else:
                # Let the ListBox handle other keys
                self.listbox.keypress(self.loop.screen_size, key)

    def handle_navigation(self, key):
        if isinstance(key, tuple):
            return

        if key in ('up', 'down'):
            self.move_focus_to_next_editable_line(key)
        elif key == 'page up':
            # Move up several lines
            for _ in range(5):  # Adjust as needed
                self.move_focus_to_next_editable_line('up')
        elif key == 'page down':
            for _ in range(5):
                self.move_focus_to_next_editable_line('down')

    def move_focus_to_next_editable_line(self, direction):
        current_focus = self.listbox.get_focus()[1]
        if current_focus is None:
            # No focus, start from 0 or max_index depending on direction
            current_focus = 0 if direction == 'down' else len(self.list_walker) - 1

        index = current_focus
        max_index = len(self.list_walker) - 1

        while True:
            if direction == 'up':
                index -= 1
                if index < 0:
                    index = max_index  # Wrap around to bottom
            elif direction == 'down':
                index += 1
                if index > max_index:
                    index = 0  # Wrap around to top

            if index == current_focus:
                # We've looped all the way around
                return

            if index in self.editable_indices:
                self.listbox.set_focus(index)
                break

    def handle_search_navigation(self, key):
        if not self.search_results:
            return  # No matches to navigate

        if key in ('down', 'n', 'page down'):
            self.focus_search_result(self.focused_result + 1)
        elif key in ('up', 'p', 'page up'):
            self.focus_search_result(self.focused_result - 1)
        else:
            pass  # Ignore other keys

    def on_edit(self, edit_widget, widget, value):
        def change(*a):
            value_type = self.value_type(value)

            # Toggle boolean values
            if value.endswith(' ') and value_type == 'boolean':
                edit_widget.edit.set_edit_text('false' if value.strip() == 'true' else 'true')
            else:
                edit_widget.attr_map = {None: value_type}
        self.loop.set_alarm_in(0, change)

    @staticmethod
    def value_type(value):
        value_type = 'string'
        if value.strip().lower() in ['true', 'false']:
            value_type = 'boolean'
        elif value.strip().isdigit():
            value_type = 'integer'
        return value_type

    def set_cursor_to_end(self):
        focus_widget, focus_position = self.listbox.get_focus()
        if focus_position is None or focus_position >= len(self.list_walker):
            return
        # Use focus_position instead of self.current_index
        if isinstance(self.list_walker[focus_position], urwid.Columns) and len(self.list_walker[focus_position].contents) >= 4:
            value_placeholder = self.list_walker[focus_position].contents[3][0]
            value_widget = value_placeholder.original_widget
            if isinstance(value_widget, urwid.AttrMap):
                value_widget = value_widget.original_widget
            if isinstance(value_widget, urwid.Edit):
                self.loop.set_alarm_in(0, lambda *_: value_widget.set_edit_pos(len(value_widget.get_edit_text())))

    def render_line(self):
        for i, widget in enumerate(self.list_walker):
            if isinstance(widget, urwid.Columns):
                if len(widget.contents) > 2:
                    line_number_widget = widget.contents[0][0]
                    equal_sign_widget = widget.contents[2][0]

                    # Highlight the selected line number and '=' sign
                    if i == self.current_index:
                        line_number_widget.set_text(('selected_line', line_number_widget.get_text()[0]))
                        equal_sign_widget.set_text(('selected_eq', equal_sign_widget.get_text()[0]))
                    else:
                        line_number_widget.set_text(('line', line_number_widget.get_text()[0]))
                        equal_sign_widget.set_text(('eq', equal_sign_widget.get_text()[0]))

    def render_focus(self):
        if getattr(self, '_adjusting_focus', False):
            return

        focused_widget, focus_position = self.listbox.get_focus()

        # Loop through the list_walker to find the index of the focused widget
        for i, widget in enumerate(self.list_walker):
            if widget == focused_widget:
                # Update the current index
                self.current_index = i
                self.render_line()
                self.set_cursor_to_end()

                # If in search mode, ensure focus is on a matching line
                if self.search_mode:
                    if self.current_index in self.search_results:
                        # Update the focused_result index
                        self.focused_result = self.search_results.index(self.current_index)
                        self.matches_display.set_text(f"{self.focused_result + 1} / {len(self.search_results)} Results")
                    else:
                        # Adjust focus to the nearest matching line
                        self.adjust_focus_to_match(self.current_index)
                break

    def adjust_focus_to_match(self, index):
        if getattr(self, '_adjusting_focus', False):
            return
        self._adjusting_focus = True

        if not self.search_results:
            self._adjusting_focus = False
            return

        # Find the matching index closest to 'index'
        distances = [(abs(i - index), i) for i in self.search_results]
        distances.sort()
        _, closest_index = distances[0]

        if closest_index != index:
            def set_focus(*args):
                self.listbox.set_focus(closest_index)
                self._adjusting_focus = False  # Reset after focus change
            self.loop.set_alarm_in(0, set_focus)
        else:
            self._adjusting_focus = False  # No need to adjust focus

editor = None
def edit_properties(server_name: str):
    global loop, editor

    if server_name.lower() in constants.server_manager.server_list_lower:
        editor = PropertiesEditor(server_name)
        editor.loop = loop
        editor.connect_signals()
        screen_manager.screens['ServerPropertiesEditScreen'] = (editor.main_widget, editor.handle_input)
        screen_manager.current_screen('ServerPropertiesEditScreen')
        return [("normal", "Successfully saved 'server.properties'")]

    # If server doesn't exist
    else:
        return [('parameter', server_name), ('info', ' does not exist')], 'fail'
