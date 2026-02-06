# -------------------------------------------------- Console Panel -----------------------------------------------------

player_counter = 0
class ConsolePanel():

    class Panels():

        class PerformancePanel:
            def __init__(self, parent, label, percent):
                self.parent = parent
                self.bar_width = 20

                # Percentage bar
                bar_active_length = int((percent / 100) * self.bar_width)
                bar_inactive_length = self.bar_width - bar_active_length
                self.bar = urwid.Text([
                    ('bar_inactive', '▄' * bar_active_length),
                    ('bar_inactive', ' ' * bar_inactive_length),
                    ('bar_inactive', '\n'),
                    ('bar_inactive', '▀' * self.bar_width)
                ])
                bar_pile = urwid.Pile([self.bar])

                # Performance label
                self.label = urwid.Text(('bar_label', f"{percent}%"), align='right')
                progress_label = urwid.Text(('bar_label', f"{label}"), align='right')
                label_pile = urwid.Pile([self.label, progress_label])

                # Create columns with bar and labels
                self.widgets = urwid.Columns([
                    bar_pile,
                    ('fixed', 6, label_pile)
                ], dividechars=0)

            def set_percent(self, percent):
                color = self.parent.get_percent_color(percent, 5)
                fraction = (percent / 100) * self.bar_width
                full_steps = int(fraction)
                fractional = fraction - full_steps

                active_bars = ''
                bar_inactive_length = 0

                # If no full steps and percent > 0.5, display a half-step
                if full_steps == 0 and percent > 0.5:
                    active_bars = '▖'
                    bar_inactive_length = self.bar_width - 1

                # If fractional part > 0.5, add a half-step
                elif fractional > 0.5:
                    active_bars = '▄' * full_steps + '▖'
                    bar_inactive_length = self.bar_width - full_steps - 1

                # Otherwise, only full steps
                else:
                    active_bars = '▄' * full_steps
                    bar_inactive_length = self.bar_width - full_steps

                # Update the progress bar, and text
                self.bar.set_text([
                    (color, active_bars),
                    ('bar_inactive', ' ' * bar_inactive_length),
                    ('bar_inactive', '\n'),
                    ('bar_inactive', '▀' * self.bar_width)
                ])
                number = '0' if float(percent) == 0 else round(float(percent), 1)
                self.label.set_text((color, f"{number}%"))

        @staticmethod
        def get_percent_color(percent, min_limit=0):
            if percent <= min_limit:
                color = 'bar_label'
            elif percent < 50:
                color = 'perf_normal'
            elif percent < 75:
                color = 'perf_warn'
            else:
                color = 'perf_critical'

            return color

        def __init__(self, parent):
            self.parent = parent
            self.uptime = "00:00:00:00"
            self.player_count = "0 / 20"
            self.cpu_percent = 0
            self.ram_percent = 0

            # Stats panel
            self.stats = urwid.Text([
                ('stat', "up-time:\n"),
                ('bar_label', f"{self.uptime}\n\n"),
                ('stat', "players:\n"),
                ('bar_label', self.player_count)
            ], align='center')
            left_box = urwid.AttrMap(urwid.LineBox(urwid.Padding(self.stats, left=2, right=2)), 'linebox')

            # Center overview panel
            self.overview = urwid.Text([('bar_label', '\n\n< not running >\n\n')], align='center')
            middle_panel = urwid.Padding(self.overview, left=2, right=2)
            middle_box = urwid.AttrMap(
                urwid.LineBox(middle_panel, title=self.parent.server_name, title_attr='box_title'), 'linebox')
            middle_box_filled = urwid.Filler(middle_box, valign='top')

            # Performance panel
            self.cpu_panel = self.PerformancePanel(self, "CPU", self.cpu_percent)
            self.ram_panel = self.PerformancePanel(self, "RAM", self.ram_percent)

            right_panel = urwid.Pile([
                urwid.Padding(self.cpu_panel.widgets, left=2, right=2),
                urwid.Text(''),
                urwid.Padding(self.ram_panel.widgets, left=2, right=2)
            ])
            right_box = urwid.AttrMap(urwid.LineBox(urwid.Padding(right_panel, min_width=30)), 'linebox')

            # Compile the panels
            self.widgets = urwid.Columns([
                ('pack', urwid.Padding(left_box, left=1, right=1)),  # Left side: Uptime and Player Count
                ('weight', 1, urwid.Padding(middle_box_filled, left=1, right=1)),
                ('pack', urwid.Padding(right_box, left=1, right=1))  # Right side: CPU and RAM with 40% width
            ])

        def refresh_data(self, refresh_players=False, *a):
            server_obj = self.parent.server
            server_obj.performance_stats(0.005, update_players=refresh_players)

            try:
                perf_data = constants.server_manager.current_server.run_data['performance']
            except KeyError:
                return
            except AttributeError:
                return

            if not perf_data:
                return

            try:

                # Update up-time
                formatted_color = ''
                found = False
                for x, item in enumerate(perf_data['uptime'].split(":")):
                    if x == 0 and len(item) > 2:
                        formatted_color = f'{item}:'
                        found = True
                        continue
                    if x == 0 and item != '00':
                        item = int(item)
                        formatted_color += '|' if len(str(item)) >= 2 else '0|'
                        found = True
                    if item != "00" and not found:
                        found = True
                        item = int(item)
                        formatted_color += f'|{item}:' if len(str(item)) == 2 else f'0|{item}:'
                    else:
                        formatted_color += f'{item}:'

                formatted_color = formatted_color.strip(':')
                if '|' in formatted_color:
                    empty, full = formatted_color.split('|')
                else:
                    empty = ''
                    full = formatted_color

                # Update player count
                total_count = int(server_obj.server_properties['max-players'])
                count = len(perf_data['current-players'])
                percent = (count / total_count)
                color = self.get_percent_color(percent).replace('perf_normal', 'box_title')
                end_color = 'bar_label' if full == self.uptime else 'white'

                self.stats.set_text([
                    ('stat', "up-time:\n"),
                    ('bar_label', f"{empty}"), (end_color, f"{full}\n\n"),
                    ('stat', "players:\n"),
                    (color, str(count)), ('bar_label', ' / '), (color, str(total_count)),
                ])

                # Update server overview
                self.parent.ip_address = f"{server_obj.run_data['network']['address']['ip']}:{server_obj.run_data['network']['address']['port']}"
                self.overview.set_text([
                    ("white", f"\n{self.parent.motd}"),
                    ("stat", f"\n{self.parent.server_version}"),
                    ("ip", f"\n\n> {self.parent.ip_address}")
                ])

                # Update CPU/RAM stats
                self.cpu_panel.set_percent(perf_data['cpu'])
                self.ram_panel.set_percent(perf_data['ram'])

            except KeyError:
                return

    class Log():

        class ScrollBar(urwid.WidgetWrap):
            def __init__(self, parent, listbox):
                self.parent = parent
                self.listbox = listbox
                self.scrollbar = urwid.Text('')
                self.thumb_char = '▐'

                # Create a Columns widget with ListBox and ScrollBar
                columns = urwid.Columns([
                    ('weight', 1, listbox),
                    ('fixed', 2, self.scrollbar)
                ], dividechars=1)
                super().__init__(columns)

            def render(self, size, focus=False):

                # Calculate scrollbar based on size
                maxcol, maxrow = size
                total_items = len(self.listbox.body)
                if total_items <= 0:
                    bar = ' ' * maxrow
                else:

                    # Calculate thumb size, make it at least 2 rows and proportional to the content
                    thumb_size = max(2, int((maxrow / total_items) * maxrow * 0.6))
                    thumb_size = min(thumb_size, maxrow)

                    # Calculate thumb position based on focus
                    thumb_pos = int(
                        (self.listbox.focus_position / max(max(total_items - 1, 1), 1)) * (maxrow - thumb_size))
                    thumb_pos = max(0, min(thumb_pos, maxrow - thumb_size))
                    thumb_size = max(2, thumb_size)

                    # Build scrollbar lines
                    bar_lines = [' ' for _ in range(maxrow)]
                    for i in range(thumb_pos, thumb_pos + thumb_size):
                        if i < maxrow:
                            bar_lines[i] = self.thumb_char
                    bar = '\n'.join(bar_lines)

                    if bar.count(self.thumb_char) == maxrow:
                        bar = ' ' * maxrow

                self.scrollbar.set_text(('scrollbar_thumb', bar))
                return super().render(size, focus)

        @staticmethod
        def console_event(date, log_type, color, message):
            def get_log_color(c, background=False):
                new_color = 'console_purple'
                if c == (0.7, 0.7, 0.7, 1):
                    new_color = 'console_gray'
                elif c == (0.3, 1, 0.6, 1):
                    new_color = 'console_green'
                elif c == (1, 0.5, 0.65, 1):
                    new_color = 'console_red'
                elif c == (1, 0.804, 0.42, 1):
                    new_color = 'console_orange'
                elif c == (0.953, 0.929, 0.38, 1):
                    new_color = 'console_yellow'
                elif c == (0.439, 0.839, 1, 1):
                    new_color = 'console_blue'
                elif c == (1, 0.298, 0.6, 1):
                    new_color = 'console_pink'

                if background:
                    new_color += '_bg'

                return new_color

            # Make it fancy if the terminal supports it
            if advanced_term:
                line = urwid.Columns([
                    ('fixed', 13,
                     urwid.AttrMap(urwid.Text(f"{date} ", align='right'), get_log_color(color, True))),
                    ('fixed', 7, urwid.AttrMap(urwid.Text(log_type, align='center'), get_log_color(color, True))),
                    urwid.Text(f"{'█' if advanced_term else ''}  {message}\n", wrap='ellipsis')
                ])
                return urwid.AttrMap(line, get_log_color(color, False))

            # Basic view
            else:
                line = urwid.Columns([
                    ('fixed', 12, urwid.Text(f" {date}", align='right')),
                    ('fixed', 10, urwid.Text(log_type, align='center')),
                    urwid.Text(f"{message}\n", wrap='ellipsis')
                ])
                return urwid.AttrMap(line, get_log_color(color, False))

        def __init__(self, parent):
            self.parent = parent
            self.log = []

            self.data = urwid.SimpleFocusListWalker(self.log)
            list_box = urwid.ListBox(self.data)

            # Store a reference to list_box for scrolling
            self.list_box = list_box

            # Wrap the ListBox with ScrollBar
            self.scroll_bar = self.ScrollBar(self, list_box)

            # Wrap everything in a LineBox
            log_box = urwid.LineBox(self.scroll_bar)
            self.widget = urwid.AttrMap(urwid.Padding(log_box, left=1, right=1), 'linebox')  # Padding on the outside only

        def update_text(self, text, refresh=False, force_scroll=False):

            # Check if the scrollbar is at the bottom before adding new text
            at_bottom = False
            if force_scroll or (len(self.list_box.body) == 0 or self.list_box.focus_position == len(self.list_box.body) - 1):
                at_bottom = True


            # Update existing log
            if (len(text) == len(self.log)) and not refresh:
                last_entry = text[-1]['text']
                time_stamp, log_type, message, color = last_entry
                new_widget = self.console_event(time_stamp, log_type, color, message)
                self.log[-1] = new_widget
                self.data[-1] = new_widget

            # Add entries to the log
            else:
                if refresh:
                    self.log.clear()
                    self.data.clear()

                for line in text[len(self.log):]:
                    time_stamp, log_type, message, color = line["text"]
                    new_widget = self.console_event(time_stamp, log_type, color, message)
                    self.log.append(new_widget)
                    self.data.append(new_widget)


            # If it was at the bottom before, scroll to the bottom again
            if at_bottom:
                self.list_box.set_focus(len(self.list_box.body) - 1)

    class Input():

        class ValidatedEdit(urwid.Edit):
            def __init__(self, exec_func, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.command_history = []
                self.history_index = 0
                self.exec_func = exec_func
                self.hint_text = "enter command, or 'ESC' to detach..."

            def render(self, size, focus=False):
                if not self.get_edit_text():
                    # Display the hint text in dark gray when input is empty
                    hint = urwid.Text(('bar_label', self.hint_text))
                    return hint.render(size, focus)
                else:
                    # Display the regular input when there is text
                    return super().render(size, focus)

            def keypress(self, size, key):
                if not self.get_edit_text() and key == '/':
                    urwid.emit_signal(self, 'invalid_key', key)
                    return None

                elif key == 'enter':
                    command = self.get_edit_text().strip()

                    if command not in self.command_history[:1]:
                        self.command_history.insert(0, command)

                        # Limit size of command history
                        if len(self.command_history) > 100:
                            self.command_history.pop()

                    self.exec_func(command)

                    self.set_edit_text('')

                # Modulate command history with arrow keys
                elif key in ['up', 'down'] and self.command_history:

                    if key == 'down':
                        if self.history_index > 0:
                            self.history_index -= 1
                        else:
                            self.set_edit_text('')
                            return

                    # Constrain history_index to valid range
                    self.history_index = max(0, min(self.history_index, len(self.command_history) - 1))

                    # Set the command text based on the updated index
                    new_text = self.command_history[self.history_index]
                    self.set_edit_text(new_text)
                    self.set_edit_pos(len(new_text))

                    if key == 'up':
                        if self.history_index < len(self.command_history) - 1:
                            self.history_index += 1

                return super().keypress(size, key)

        def send_command(self, command):
            if self.parent.server.run_data:
                self.parent.server.run_data['send-command'](command)
                self.parent.log.update_text(self.parent.server.run_data['log'], force_scroll=True)

        def __init__(self, parent):
            self.parent = parent
            self.command_header = ' ❯❯  ' if advanced_term else ' >>  '
            prompt = urwid.Text(('input_header', self.command_header), align='left')
            edit = urwid.AttrMap(self.ValidatedEdit(self.send_command), 'input')

            self.widgets = urwid.Columns([('fixed', 5, prompt), edit])

    def __init__(self, server_name: str):
        # Initialize server
        self.is_visible = True

        self.server = constants.server_manager.open_server(server_name)

        # Wait for server to actually initialize, up to timeout
        max_timeout = 10  # seconds
        start_time = time.monotonic()
        while not all(self.server._check_object_init().values()):

            if time.monotonic() - start_time >= max_timeout:
                self.reset_panel()
                update_console([('normal', f"'{self.server.name}' failed to start")])
                return

            time.sleep(0.05)

        time.sleep(0.1)

        # Initialize IP address and server info for the middle box
        self.server_name = server_name
        self.motd = self.server.motd
        self.server_version = f'{self.server.type.title()} {self.server.version}'
        self.ip_address = '0.0.0.0:0'

        # Performance panel
        self.panels = self.Panels(self)

        # Log panel
        self.log = self.Log(self)

        # Create the input field
        self.input = self.Input(self)

        # Widget layout
        self.widgets = self.build_layout()

        # Launch the actual server (after init to redraw screen)
        loop.set_alarm_in(0.01, lambda *_: self.launch_server())

    def handle_input(self, key):
        if key == 'esc':
            self.reset_panel(show_attach=True)

    def start_update_loop(self, *a):
        global player_counter, loop
        player_counter += 1

        loop.set_alarm_in(0, functools.partial(self.panels.refresh_data, player_counter == 3))
        if self.server.running and self.is_visible:
            loop.set_alarm_in(1, self.start_update_loop)

        if player_counter > 3:
            player_counter = 0

    def reset_panel(self, show_attach=False, *a):
        if self.server.restart_flag:
            return

        self.is_visible = False
        screen_manager.current_screen('MainMenuScreen')

        if not show_attach:
            update_console([('info', response_header), ('normal', "Type a command, ?, or "), ('command', 'help')])

    def launch_server(self):

        # Update log with initial message
        now_formatted = dt.now().strftime(constants.fmt_date("%#I:%M:%S %p")).rjust(11)
        boot_text = f"Launching '{self.server_name}', please wait..."
        text_list = [{'text': (now_formatted, 'INIT', boot_text, (0.7, 0.7, 0.7, 1))}]


        # Display pre-launch warnings
        java_data = self.server.java_installed()
        to_install_java = java_data[1] is False
        to_init_playit = self.server.proxy_enabled and self.server.proxy_installed()

        # Check if Java version is not installed to display a message
        if to_install_java and not to_init_playit:
            text_list.append({'text': (now_formatted, 'INFO', f"Installing '{java_data[0]}'...", (0.6, 0.6, 1, 1))})

        # Check if playit is enabled to display a message
        elif to_init_playit and not to_install_java:
            text_list.append({'text': (now_formatted, 'INFO', 'Initializing playit agent...', (0.6, 0.6, 1, 1))})

        # Display a combo message
        elif to_init_playit and to_install_java:
            text_list.append({'text': (now_formatted, 'INFO', f"Installing '{java_data[0]}', and initializing playit agent...", (0.6, 0.6, 1, 1))})

        self.log.update_text(text_list)
        loop.draw_screen()


        # Launch the server
        self.server.launch()
        self.log.update_text(self.server.run_data['log'], refresh=True)


        # Map update functions to run_data hooks
        if self.log.update_text not in self.server.run_data.get('process-hooks', []):
            self.server.run_data.setdefault('process-hooks', []).append(self.log.update_text)

        if self.reset_panel not in self.server.run_data.get('close-hooks', []):
            self.server.run_data.setdefault('close-hooks', []).append(self.reset_panel)

        self.server.run_data['console-panel'] = self


        # Start timer to update performance stats
        self.start_update_loop()

    def open_panel(self):
        self.is_visible = True
        self.start_update_loop()
        return self

    def build_layout(self):
        title_text = urwid.Text(('title', f"auto-mcs v{constants.app_version} (headless)"), align='center')
        top_content = urwid.Pile([
            urwid.AttrMap(urwid.Filler(urwid.Padding(title_text, left=0, right=0), valign='top'), 'title'),
            urwid.AttrMap(urwid.Filler(urwid.Padding(urwid.Text(''), left=0, right=0), valign='top'), '')
        ])

        layout = urwid.Frame(
            self.log.widget,
            footer=self.input.widgets,
            header=urwid.Pile([top_content, self.panels.widgets]),
            focus_part='footer'
        )
        return layout

console = None
def open_console(server_name: str, force_start=False):
    global console, player_counter
    console = None
    if not force_start:

        # First, check if the server exists
        if server_name.lower() not in constants.server_manager.server_list_lower:
            return [('parameter', server_name), ('info', ' does not exist')], 'fail'

        # Check if the server is running
        elif server_name not in constants.server_manager.running_servers:
            return [
                ("info", "Run "),
                ("command", "server "),
                ("sub_command", "launch "),
                ("parameter", server_name),
                ("info", " to start the server")
            ], 'fail'


    # Attempt to re-attach to the console if it's already available
    try:
        if server_name in constants.server_manager.running_servers:
            console = constants.server_manager.running_servers[server_name].run_data['console-panel'].open_panel()
    except:
        pass

    if not console:
        console = ConsolePanel(server_name)

    screen_manager.screens['ServerViewScreen'] = (console.widgets, console.handle_input)
    screen_manager.current_screen('ServerViewScreen')

    return [
        ("info", "Run "),
        ("command", "console "),
        ("parameter", server_name),
        ("info", " to re-attach to the console")
    ]
