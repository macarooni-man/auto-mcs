from source.ui.headless.utility import *
from source.ui.headless import utility

from datetime import datetime as dt
import re
import os


# ----------------------------------------------- App Log Panel --------------------------------------------------------

line_pattern = re.compile(
    r'^\[(?P<time>[^\]]+)\]\s+\[(?P<level>[^\]]+)\]\s+\[(?P<block>[^\]]+)\]\s*(?P<message>.*)$'
)

level_color = {
    "DEBUG":    "level_debug_bold",
    "INFO":     "level_info_bold",
    "WARN":     "level_warn_bold",
    "WARNING":  "level_warn_bold",
    "ERROR":    "level_error_bold",
    "CRITICAL": "level_error_bold",
    "FATAL":    "level_error_bold",
}

object_color = {
    "DEBUG":    "block_debug_bold",
    "INFO":     "block_info_bold",
    "WARN":     "block_warn_bold",
    "WARNING":  "block_warn_bold",
    "ERROR":    "block_error_bold",
    "CRITICAL": "block_error_bold",
    "FATAL":    "block_error_bold",
}

text_color = {
    "DEBUG":    "white",
    "INFO":     "white",
    "WARN":     "console_yellow",
    "WARNING":  "console_yellow",
    "ERROR":    "console_red",
    "CRITICAL": "console_red",
    "FATAL":    "console_red",
}



class LogPanel():

    class Log():

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

        def __init__(self, parent):
            self.parent = parent
            self.log = []

            self.data = urwid.SimpleFocusListWalker(self.log)
            list_box = urwid.ListBox(self.data)

            self.list_box = list_box
            self.scroll_bar = self.ScrollBar(self, list_box)

            log_box = urwid.LineBox(self.scroll_bar)
            self.widget = urwid.AttrMap(urwid.Padding(log_box, left=1, right=1), 'linebox')

            self._last_message_attr = "white"
            self._last_total_lines = 0
            self._last_focus_pos = 0

        def is_at_bottom(self) -> bool:
            return len(self.list_box.body) == 0 or self.list_box.focus_position == len(self.list_box.body) - 1

        def console_event(self, raw_line: str):
            s = raw_line.rstrip("\n")

            if s.startswith("   >"):
                prefix = "   >  "
                rest = s[len(prefix):] if s.startswith(prefix) else s.lstrip()[1:].lstrip()

                message_attr = self._last_message_attr or "white"
                return urwid.Text([
                    ("comment", prefix),
                    (message_attr, rest),
                ], wrap="ellipsis")

            match = line_pattern.match(s)
            if not match:
                self._last_message_attr = "white"
                return urwid.Text([("white", s)], wrap="ellipsis")

            timestamp = match.group("time")
            level = match.group("level").upper()
            block = match.group("block")
            message = match.group("message")

            # Make colors mirror colorama config from logger
            level_attr = level_color.get(level, "level_info_bold")
            message_attr = text_color.get(level, "white")
            blk_attr = object_color.get(level, "block_info_bold")

            self._last_message_attr = message_attr

            return urwid.Text([
                ("comment", "["), ("time_bold", timestamp),   ("comment", "] "),
                ("comment", "["), (level_attr, level), ("comment", "] "),
                ("comment", "["), (blk_attr, block), ("comment", "] "),
                (message_attr, message),
            ], wrap="ellipsis")

        def update_text(self, entries, refresh=False, force_scroll=False):
            at_bottom = force_scroll or self.is_at_bottom()

            old_focus = None
            if not at_bottom and len(self.list_box.body) > 0:
                old_focus = self.list_box.focus_position

            if refresh:
                self.log.clear()
                self.data.clear()

            def unpack(item):
                if isinstance(item, dict) and "text" in item:
                    return item["text"]
                return item

            index = 0 if refresh else len(self.log)

            for item in entries[index:]:
                _, _, message, _ = unpack(item)
                new_widget = self.console_event(message)
                self.log.append(new_widget)
                self.data.append(new_widget)

            # restore focus
            if at_bottom and len(self.list_box.body) > 0:
                self.list_box.set_focus(len(self.list_box.body) - 1)
            elif old_focus is not None and len(self.list_box.body) > 0:
                self.list_box.set_focus(min(old_focus, len(self.list_box.body) - 1))

            self._last_total_lines = len(self.list_box.body)

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
        raw_lines = []


        # First, read through the log written to disk
        try:
            with open(self.log_path, "r", encoding="utf-8", errors="replace") as f:
                raw_lines = f.read().splitlines()

        except Exception as e:
            if not list(log_manager._log_db):
                now_formatted = dt.now().strftime(constants.fmt_date("%#I:%M:%S %p")).rjust(11)
                entries = [{'text': (now_formatted, 'WARN', f"Failed opening log: {e}", (1, 0.804, 0.42, 1))}]
                self.log.update_text(entries, refresh=True, force_scroll=True)
                utility.screen_manager._loop.draw_screen()
                return

        # Second, scrape unwritten lines from the logger
        for line in log_manager._format_buffer(list(log_manager._log_db)):
            raw_lines.extend(line.splitlines())

        # Convert log lines to widgets
        now_color = (0.7, 0.7, 0.7, 1)
        entries = []

        for line in raw_lines:
            now_formatted = dt.now().strftime(constants.fmt_date("%#I:%M:%S %p"))
            entries.append({'text': (now_formatted, 'LOG', line.rstrip(), now_color)})

        if not entries:
            now_formatted = dt.now().strftime(constants.fmt_date("%#I:%M:%S %p")).rjust(11)
            entries = [{'text': (now_formatted, 'INFO', "< log is empty >", now_color)}]

        new_total = len(raw_lines)
        at_bottom = self.log.list_box.body and (self.log.list_box.focus_position == len(self.log.list_box.body) - 1)
        needs_refresh = (new_total < self.log._last_total_lines) or at_bottom or force_scroll
        self.log.update_text(entries, refresh=needs_refresh, force_scroll=force_scroll)
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
