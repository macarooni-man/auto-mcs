from source.ui.headless.utility import *
from source.ui.headless import utility

import os
import time
import functools
from datetime import datetime as dt


# ----------------------------------------------- App Log Panel --------------------------------------------------------

class LogPanel:

    class Log:

        class ScrollBar(urwid.WidgetWrap):
            def __init__(self, parent, listbox):
                self.parent = parent
                self.listbox = listbox
                self.scrollbar = urwid.Text('')
                self.thumb_char = '▐'

                columns = urwid.Columns([
                    ('weight', 1, listbox),
                    ('fixed', 2, self.scrollbar)
                ], dividechars=1)
                super().__init__(columns)

            def render(self, size, focus=False):
                maxcol, maxrow = size
                total_items = len(self.listbox.body)

                if total_items <= 0: bar = ' ' * maxrow
                else:
                    thumb_size = max(2, int((maxrow / total_items) * maxrow * 0.6))
                    thumb_size = min(thumb_size, maxrow)

                    thumb_pos = int((self.listbox.focus_position / max(max(total_items - 1, 1), 1)) * (maxrow - thumb_size))
                    thumb_pos = max(0, min(thumb_pos, maxrow - thumb_size))
                    thumb_size = max(2, thumb_size)

                    bar_lines = [' ' for _ in range(maxrow)]
                    for i in range(thumb_pos, thumb_pos + thumb_size):
                        if i < maxrow: bar_lines[i] = self.thumb_char
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

            if advanced_term:
                line = urwid.Columns([
                    ('fixed', 13,
                     urwid.AttrMap(urwid.Text(f"{date} ", align='right'), get_log_color(color, True))),
                    ('fixed', 7, urwid.AttrMap(urwid.Text(log_type, align='center'), get_log_color(color, True))),
                    urwid.Text(f"{'█' if advanced_term else ''}  {message}\n", wrap='ellipsis')
                ])
                return urwid.AttrMap(line, get_log_color(color, False))
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

            self.list_box = list_box
            self.scroll_bar = self.ScrollBar(self, list_box)

            log_box = urwid.LineBox(self.scroll_bar)
            self.widget = urwid.AttrMap(urwid.Padding(log_box, left=1, right=1), 'linebox')

        def update_text(self, entries, refresh=False, force_scroll=False):
            at_bottom = False
            if force_scroll or (len(self.list_box.body) == 0 or self.list_box.focus_position == len(self.list_box.body) - 1):
                at_bottom = True

            if refresh:
                self.log.clear()
                self.data.clear()

            def unpack(item):
                if isinstance(item, dict) and "text" in item:
                    return item["text"]
                return item

            start_idx = 0 if refresh else len(self.log)
            for item in entries[start_idx:]:
                time_stamp, log_type, message, color = unpack(item)
                new_widget = self.console_event(time_stamp, log_type, color, message)
                self.log.append(new_widget)
                self.data.append(new_widget)

            if at_bottom and len(self.list_box.body) > 0:
                self.list_box.set_focus(len(self.list_box.body) - 1)

    def __init__(self):
        self.is_visible = True

        self._header_widget: urwid.Text | None = None
        self.log_name = None
        self.log_path = None

        # File polling state
        self._last_mtime = None
        self._last_size = None
        self._last_memory_size = None

        # Create log panel
        self.log = self.Log(self)
        self.widgets = self.build_layout()
        utility.screen_manager._loop.set_alarm_in(0.01, lambda *_: self._initial_load())

    def handle_input(self, key):
        if key == 'esc':
            self.reset_panel()

    def reset_panel(self, *a):
        self.is_visible = False
        utility.screen_manager.current = 'MainMenuScreen'

    def _initial_load(self):
        self._reload_file(force_scroll=True)
        self.start_update_loop()

    def start_update_loop(self, *a):
        if not self.is_visible:
            return

        self._reload_file(force_scroll=False)

        # Poll log content every 5 seconds
        utility.screen_manager._loop.set_alarm_in(5, self.start_update_loop)

    def _reload_file(self, force_scroll=False):
        from source.core.logger import log_manager
        log_name  = log_manager._get_file_name()
        directory = log_manager.path
        self.log_name = log_name
        self.log_path = os.path.join(directory, log_name)

        # Update header
        hint = "press 'ESC' to leave"
        self._header_widget.set_text(('bar_label', f"{self.log_path}   ({hint})"))
        st    = None
        mtime = None
        size  = None

        try:
            st    = os.stat(self.log_path)
            mtime = st.st_mtime
            size  = st.st_size
        except FileNotFoundError:
            if not list(log_manager._log_db):
                now_formatted = dt.now().strftime(constants.fmt_date("%#I:%M:%S %p")).rjust(11)
                entries = [{'text': (now_formatted, 'INFO', f"Waiting for log file: {self.log_path}", (0.7, 0.7, 0.7, 1))}]
                self.log.update_text(entries, refresh=True, force_scroll=True)
                utility.screen_manager._loop.draw_screen()
                self._last_mtime = None
                self._last_size = None
                self._last_memory_size = None
                return
        except Exception as e:
            if not list(log_manager._log_db):
                now_formatted = dt.now().strftime(constants.fmt_date("%#I:%M:%S %p")).rjust(11)
                entries = [{'text': (now_formatted, 'WARN', f"Failed reading log: {e}", (1, 0.804, 0.42, 1))}]
                self.log.update_text(entries, refresh=True, force_scroll=True)
                utility.screen_manager._loop.draw_screen()
                return

        changed = (
            (self._last_mtime != mtime) or
            (self._last_size != size) or
            (len(list(log_manager._log_db)) != self._last_memory_size)
        )
        if not changed and self._last_mtime is not None:
            return

        self._last_mtime = mtime
        self._last_size = size
        self._last_memory_size = len(list(log_manager._log_db))

        try:
            # First, read through the log written to disk
            with open(self.log_path, "r", encoding="utf-8", errors="replace") as f:
                raw_lines = f.read().splitlines()

            # Second, scrape unwritten lines from the logger
            for e in list(log_manager._log_db):
                time_obj = e["time"]
                object_data = e["object_data"]
                message = e["message"]
                level = e["level"]
                stack = e["stack"]

                # Format lines like print method
                object_width = log_manager._object_width - len(level)
                timestamp = time_obj.strftime("%I:%M:%S %p")
                block = f"{stack}: {object_data}".ljust(object_width)

                lines = str(message).splitlines() or [""]
                for i, line in enumerate(lines):
                    if i == 0: raw_lines.append(f"[{timestamp}] [{level.upper()}] [{block}] {line.rstrip()}\n")
                    else: raw_lines.append(f"{log_manager._line_header}{line.rstrip()}\n")

        except Exception as e:
            now_formatted = dt.now().strftime(constants.fmt_date("%#I:%M:%S %p")).rjust(11)
            entries = [{'text': (now_formatted, 'WARN', f"Failed opening log: {e}", (1, 0.804, 0.42, 1))}]
            self.log.update_text(entries, refresh=True, force_scroll=True)
            utility.screen_manager._loop.draw_screen()
            return

        # Convert log lines to widgets
        now_color = (0.7, 0.7, 0.7, 1)
        entries = []

        for line in raw_lines:
            now_formatted = dt.now().strftime(constants.fmt_date("%#I:%M:%S %p"))
            entries.append({'text': (now_formatted, 'LOG', line, now_color)})

        if not entries:
            now_formatted = dt.now().strftime(constants.fmt_date("%#I:%M:%S %p")).rjust(11)
            entries = [{'text': (now_formatted, 'INFO', "< log file is empty >", now_color)}]

        self.log.update_text(entries, refresh=True, force_scroll=force_scroll)
        utility.screen_manager._loop.draw_screen()


    def build_layout(self):
        title_text = urwid.Text(('title', f"auto-mcs v{constants.app_version} (headless)"), align='center')
        top_content = urwid.Pile([
            urwid.AttrMap(urwid.Filler(urwid.Padding(title_text, left=0, right=0), valign='top'), 'title'),
            urwid.AttrMap(urwid.Filler(urwid.Padding(urwid.Text(''), left=0, right=0), valign='top'), '')
        ])

        self._header_widget = urwid.Text('Loading...', align='center')
        header_box  = urwid.AttrMap(
            urwid.LineBox(urwid.Padding(self._header_widget, left=2, right=2), title_attr='box_title'),
            'linebox'
        )

        header = urwid.Pile([
            top_content,
            urwid.Padding(header_box, left=1, right=1)
        ])

        layout = urwid.Frame(
            self.log.widget,
            header=header,
            footer=None,
            focus_part='body'
        )
        return layout


class LogViewScreen(MenuBackground):
    _panel: LogPanel | None
    def __init__(self):
        self._panel = None

    def open_log(self):
        self._panel = LogPanel()
        self.menu = self._panel.widgets
        self.handle_input = self._panel.handle_input
        utility.screen_manager.current = self.name
