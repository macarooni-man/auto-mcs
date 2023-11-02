from __future__ import annotations

from tkinter import Tk, Text, Entry, Label, Canvas, RIGHT, BOTTOM, X, Y, BOTH, DISABLED, END, IntVar, Frame, PhotoImage, font, ttk, INSERT, BaseWidget, Event, Misc, TclError, Text, ttk, RIGHT, Y, getboolean
from typing import Any, Callable, Optional, Type, Union
from contextlib import suppress
from PIL import ImageTk, Image
from tkinter.font import Font
import pygments.lexers
import multiprocessing
import pygments.lexers
import pygments.lexer
import functools
import pygments
import inspect
import os

LexerType = Union[Type[pygments.lexer.Lexer], pygments.lexer.Lexer]
tab_str = '    '

# Converts between HEX and RGB decimal colors
def convert_color(color: str or tuple):

    # HEX
    if isinstance(color, str):
        color = color.replace("#", "")
        if len(color) == 6:
            split_color = (color[0:2], color[2:4], color[4:6])
        else:
            split_color = (color[0]*2, color[1]*2, color[2]*2)

        new_color = [0, 0, 0]

        for x, item in enumerate(split_color):
            item = round(int(item, 16) / 255, 3)
            new_color[x] = int(item) if item in [0, 1] else item

        new_color.append(1)

        return {'hex': '#'+''.join(split_color).upper(), 'rgb': tuple(new_color)}


    # RGB decimal
    else:

        new_color = "#"

        for item in color[0:3]:
            x = str(hex(round(item * 255)).split("0x")[1]).upper()
            x = f"0{x}" if len(x) == 1 else "FF" if len(x) > 2 else x
            new_color += x

        rgb_color = list(color[0:3])
        rgb_color.append(1)

        return {'hex': new_color, 'rgb': tuple(rgb_color)}


# Returns modified color tuple
def brighten_color(color: tuple or str, amount: float):

    # If HEX, convert to decimal RGB
    hex_input = False
    if isinstance(color, str):
        color = convert_color(color)['rgb']
        hex_input = True


    color = list(color)

    for x, y in enumerate(color):
        if x < 3:
            new_amount = y + amount
            new_amount = 1 if new_amount > 1 else 0 if new_amount < 0 else new_amount
            color[x] = new_amount

    return convert_color(color)['hex'] if hex_input else tuple(color)


# Taken from TkLineNums library
def scroll_fix(delta: int, num: bool = False) -> int:
    """Corrects scrolling numbers across platforms"""

    # The scroll events passed by macOS are different from Windows and Linux
    # so it must to be rectified to work properly when dealing with the events.
    # Originally found here: https://stackoverflow.com/a/17457843/17053202
    if delta in (4, 5) and num:  # X11 (maybe macOS with X11 too)
        return 1 if delta == 4 else -1

    # Windows, needs to be divided by 120
    return -(delta // 120)


# Taken from Chlorophyll library and modified
def _parse_scheme(color_scheme: dict[str, dict[str, str | int]]) -> tuple[dict, dict]:
    _editor_keys_map = {
        "background": "bg",
        "foreground": "fg",
        "selectbackground": "select_bg",
        "selectforeground": "select_fg",
        "inactiveselectbackground": "inactive_select_bg",
        "insertbackground": "caret",
        "insertwidth": "caret_width",
        "borderwidth": "border_width",
        "highlightthickness": "focus_border_width",
    }

    _extras = {
        "Error": "error",
        "Literal.Date": "date",
    }

    _keywords = {
        "Keyword.Constant": "constant",
        "Keyword.Declaration": "declaration",
        "Keyword.Namespace": "namespace",
        "Keyword.Pseudo": "pseudo",
        "Keyword.Reserved": "reserved",
        "Keyword.Type": "type",
    }

    _names = {
        "Name.Attribute": "attr",
        "Name.Builtin": "builtin",
        "Name.Builtin.Pseudo": "builtin_pseudo",
        "Name.Class": "class",
        "Name.Constant": "constant",
        "Name.Decorator": "decorator",
        "Name.Entity": "entity",
        "Name.Exception": "exception",
        "Name.Function": "function",
        "Name.Function.Magic": "magic_function",
        "Name.Label": "label",
        "Name.Namespace": "namespace",
        "Name.Tag": "tag",
        "Name.Variable": "variable",
        "Name.Variable.Class": "class_variable",
        "Name.Variable.Global": "global_variable",
        "Name.Variable.Instance": "instance_variable",
        "Name.Variable.Magic": "magic_variable",
    }

    _strings = {
        "Literal.String.Affix": "affix",
        "Literal.String.Backtick": "backtick",
        "Literal.String.Char": "char",
        "Literal.String.Delimeter": "delimeter",
        "Literal.String.Doc": "doc",
        "Literal.String.Double": "double",
        "Literal.String.Escape": "escape",
        "Literal.String.Heredoc": "heredoc",
        "Literal.String.Interpol": "interpol",
        "Literal.String.Regex": "regex",
        "Literal.String.Single": "single",
        "Literal.String.Symbol": "symbol",
    }

    _numbers = {
        "Literal.Number.Bin": "binary",
        "Literal.Number.Float": "float",
        "Literal.Number.Hex": "hex",
        "Literal.Number.Integer": "integer",
        "Literal.Number.Integer.Long": "long",
        "Literal.Number.Oct": "octal",
    }

    _comments = {
        "Comment.Hashbang": "hashbang",
        "Comment.Multiline": "multiline",
        "Comment.Preproc": "preproc",
        "Comment.PreprocFile": "preprocfile",
        "Comment.Single": "single",
        "Comment.Special": "special",
    }

    _generic = {
        "Generic.Emph": "emphasis",
        "Generic.Error": "error",
        "Generic.Heading": "heading",
        "Generic.Strong": "strong",
        "Generic.Subheading": "subheading",
    }

    def _parse_table(
        source: dict[str, str | int] | None,
        map_: dict[str, str],
        fallback: str | int | None = None,
    ) -> dict[str, str | int | None]:
        result: dict[str, str | int | None] = {}

        if source is not None:
            for token, key in map_.items():
                value = source.get(key)
                if value is None:
                    value = fallback
                result[token] = value
        elif fallback is not None:
            for token in map_:
                result[token] = fallback

        return result

    editor = {}
    if "editor" in color_scheme:
        editor_settings = color_scheme["editor"]
        for tk_name, key in _editor_keys_map.items():
            editor[tk_name] = editor_settings.get(key)

    assert "general" in color_scheme, "General table must present in color scheme"
    general = color_scheme["general"]

    error = general.get("error")
    escape = general.get("escape")
    punctuation = general.get("punctuation")
    general_comment = general.get("comment")
    general_keyword = general.get("keyword")
    general_name = general.get("name")
    general_string = general.get("string")

    tags = {
        "Error": error,
        "Escape": escape,
        "Punctuation": punctuation,
        "Comment": general_comment,
        "Keyword": general_keyword,
        "Keyword.Other": general_keyword,
        "Literal.String": general_string,
        "Literal.String.Other": general_string,
        "Name.Other": general_name,
    }

    tags.update(**_parse_table(color_scheme.get("keyword"), _keywords, general_keyword))
    tags.update(**_parse_table(color_scheme.get("name"), _names, general_name))
    tags.update(
        **_parse_table(
            color_scheme.get("operator"),
            {"Operator": "symbol", "Operator.Word": "word"},
        )
    )
    tags.update(**_parse_table(color_scheme.get("string"), _strings, general_string))
    tags.update(**_parse_table(color_scheme.get("number"), _numbers))
    tags.update(**_parse_table(color_scheme.get("comment"), _comments, general_comment))
    tags.update(**_parse_table(color_scheme.get("generic"), _generic))
    tags.update(**_parse_table(color_scheme.get("extras"), _extras))

    return editor, tags


# Opens a crash log in a read-only text editor
def launch_window(path: str, data: dict):

    # Get text
    ams_data = ''
    if path:

        with open(path, 'r') as f:
            ams_data = f.read().replace('\t', tab_str)

        # Init Tk window
        background_color = '#040415'
        text_color = convert_color((0.6, 0.6, 1))['hex']
        file_icon = os.path.join(data['gui_assets'], "big-icon.png")
        min_size = (950, 600)

        root = Tk()
        width = root.winfo_screenwidth()
        height = root.winfo_screenheight()
        x = int((width / 2) - (min_size[0] / 2))
        y = int((height / 2) - (min_size[1] / 2)) - 15
        root.geometry(f"{min_size[0]}x{min_size[1]}+{x}+{y}")
        root.minsize(width=min_size[0], height=min_size[1])
        root.title(f'{data["app_title"]} - amscript ({os.path.basename(path)})')
        img = PhotoImage(file=file_icon)
        root.tk.call('wm', 'iconphoto', root._w, img)
        root.configure(bg=background_color)
        root.close = False

        style = {
            'editor': {'bg': background_color, 'fg': '#b3b1ad', 'select_bg': convert_color((0.2, 0.2, 0.4))['hex'], 'inactive_select_bg': '#1b2733',
                'caret': convert_color((0.7, 0.7, 1, 1))['hex'], 'caret_width': '3', 'border_width': '0', 'focus_border_width': '0', 'font': "Consolas 15 italic"},
            'general': {'comment': '#626a73', 'error': '#ff3333', 'escape': '#b3b1ad', 'keyword': '#FB71FB',
                'name': '#819CE6', 'string': '#95e6cb', 'punctuation': '#68E3FF'},
            'keyword': {'constant': '#FB71FB', 'declaration': '#FB71FB', 'namespace': '#FB71FB', 'pseudo': '#FB71FB',
                'reserved': '#FB71FB', 'type': '#FB71FB'},
            'name': {'attr': '#819CE6', 'builtin': '#819CE6', 'builtin_pseudo': '#e6b450', 'class': '#819CE6',
                'class_variable': '#819CE6', 'constant': '#ffee99', 'decorator': '#68E3FF', 'entity': '#819CE6',
                'exception': '#819CE6', 'function': '#819CE6', 'global_variable': '#819CE6',
                'instance_variable': '#819CE6', 'label': '#819CE6', 'magic_function': '#819CE6',
                'magic_variable': '#819CE6', 'namespace': '#b3b1ad', 'tag': '#819CE6', 'variable': '#819CE6'},
            'operator': {'symbol': '#68E3FF', 'word': '#68E3FF'},
            'string': {'affix': '#68E3FF', 'char': '#95e6cb', 'delimeter': '#c2d94c', 'doc': '#c2d94c',
                'double': '#c2d94c', 'escape': '#68E3FF', 'heredoc': '#c2d94c', 'interpol': '#68E3FF',
                'regex': '#95e6cb', 'single': '#c2d94c', 'symbol': '#c2d94c'},
            'number': {'binary': '#FC9741', 'float': '#FC9741', 'hex': '#FC9741', 'integer': '#FC9741', 'long': '#FC9741',
                'octal': '#FC9741'},
            'comment': {'hashbang': '#636363', 'multiline': '#636363', 'preproc': '#ff7700', 'preprocfile': '#c2d94c',
                'single': '#636363', 'special': '#636363'}
        }

        # Configure search box
        class EntryPlaceholder(Entry):
            def __init__(self, master=None, placeholder="PLACEHOLDER", color=convert_color((0.3, 0.3, 0.65))['hex']):
                super().__init__(master)

                self.placeholder = placeholder
                self.placeholder_color = color
                self.default_fg_color = text_color
                self.has_focus = False

                self.bind("<FocusIn>", self.foc_in)
                self.bind("<FocusOut>", self.foc_out)
                self.bind("<Control-BackSpace>", self.ctrl_bs)

                self.put_placeholder()

            def put_placeholder(self):
                self.insert(0, self.placeholder)
                self['fg'] = self.placeholder_color

            def foc_in(self, *args):
                if self['fg'] == self.placeholder_color:
                    self.delete('0', 'end')
                    self['fg'] = self.default_fg_color
                self.has_focus = True

            def foc_out(self, *args):
                if not self.get():
                    self.put_placeholder()
                self.has_focus = False

            def ctrl_bs(self, event, *_):
                ent = event.widget
                end_idx = ent.index(INSERT)
                start_idx = ent.get().rfind(" ", None, end_idx)
                ent.selection_range(start_idx, end_idx)

        search_frame = Frame(root, height=1)
        search_frame.pack(fill=X, side=BOTTOM)
        search_frame.configure(bg=background_color, borderwidth=0, highlightthickness=0)
        search = EntryPlaceholder(search_frame, placeholder='search for text')
        search.pack(fill=BOTH, expand=True, padx=(60, 5), pady=(0, 10), side=BOTTOM, ipady=0, anchor='s')
        search.configure(
            bg = background_color,
            borderwidth = 0,
            highlightthickness = 0,
            selectforeground = convert_color((0.75, 0.75, 1))['hex'],
            selectbackground = convert_color((0.2, 0.2, 0.4))['hex'],
            insertwidth = 3,
            insertbackground = convert_color((0.55, 0.55, 1, 1))['hex'],
            font = "Consolas 15",
        )

        # Bind CTRL-F to focus search box
        root.bind('<Control-f>', lambda x: search.focus_force())


        class Scrollbar(Canvas):

            def __init__(self, parent, orient='vertical', hideable=False, **kwargs):
                self.command = kwargs.pop('command', None)
                Canvas.__init__(self, parent, **kwargs)

                self.orient = orient
                self.hideable = hideable

                self.new_start_y = 0
                self.new_start_x = 0
                self.first_y = 0
                self.first_x = 0
                self.hidden = False

                self.last_scrolled = 4

                self.slidercolor = text_color
                self.troughcolor = background_color

                self.config(bg=self.troughcolor, bd=0, highlightthickness=0)

                # coordinates are irrelevant; they will be recomputed
                #   in the 'set' method
                self.create_rectangle(
                    0, 0, 1, 1,
                    fill=self.slidercolor,
                    width=2,  # this is border width
                    outline=self.slidercolor,
                    tags=('slider',))
                self.bind('<ButtonPress-1>', self.move_on_click)

                self.bind('<ButtonPress-1>', self.start_scroll, add='+')
                self.bind('<B1-Motion>', self.move_on_scroll)
                self.bind('<ButtonRelease-1>', self.end_scroll)

            def set(self, lo, hi):
                lo = float(lo)
                hi = float(hi)

                self.last_scrolled = 0
                color = self.slidercolor
                self.itemconfig('slider', fill=color, outline=color)

                if self.hideable is True:
                    if lo <= 0.0 and hi >= 1.0:
                        self.grid_remove()
                        return
                    else:
                        self.grid()

                height = self.winfo_height()
                width = self.winfo_width()

                if self.orient == 'vertical':
                    x0 = 2
                    y0 = max(int(height * lo), 0)
                    x1 = width - 2
                    y1 = min(int(height * hi), height)

                elif self.orient == 'horizontal':
                    x0 = max(int(width * lo), 0)
                    y0 = 2
                    x1 = min(int(width * hi), width)
                    y1 = height

                self.coords('slider', x0, y0, x1, y1)
                self.x0 = x0
                self.y0 = y0
                self.x1 = x1
                self.y1 = y1

                # Hide scrollbar if it's the same size as the screen
                def check_hidden(*args):
                    if (y1 - y0) == height:
                        self.hidden = True
                        self.fade_out()
                        color = background_color
                        self.itemconfig('slider', fill=color, outline=color)
                    else:
                        self.hidden = False

                root.after(0, lambda *_: check_hidden())

            def move_on_click(self, event):
                if self.orient == 'vertical':
                    # don't scroll on click if mouse pointer is w/in slider
                    y = event.y / self.winfo_height()
                    if event.y < self.y0 or event.y > self.y1:
                        self.command('moveto', y)
                    # get starting position of a scrolling event
                    else:
                        self.first_y = event.y
                elif self.orient == 'horizontal':
                    # do nothing if mouse pointer is w/in slider
                    x = event.x / self.winfo_width()
                    if event.x < self.x0 or event.x > self.x1:
                        self.command('moveto', x)
                    # get starting position of a scrolling event
                    else:
                        self.first_x = event.x

            def start_scroll(self, event):
                if self.orient == 'vertical':
                    self.last_y = event.y
                    self.y_move_on_click = int(event.y - self.coords('slider')[1])
                elif self.orient == 'horizontal':
                    self.last_x = event.x
                    self.x_move_on_click = int(event.x - self.coords('slider')[0])

            def end_scroll(self, event):
                if self.orient == 'vertical':
                    self.new_start_y = event.y
                elif self.orient == 'horizontal':
                    self.new_start_x = event.x

            def move_on_scroll(self, event):

                # Only scroll if the mouse moves a few pixels. This makes
                #   the click-in-trough work right even if the click smears
                #   a little. Otherwise, a perfectly motionless mouse click
                #   is the only way to get the trough click to work right.
                #   Setting jerkiness to 5 or more makes very sloppy trough
                #   clicking work, but then scrolling is not smooth. 3 is OK.

                jerkiness = 3

                if self.orient == 'vertical':
                    if abs(event.y - self.last_y) < jerkiness:
                        return
                    # scroll the scrolled widget in proportion to mouse motion
                    #   compute whether scrolling up or down
                    delta = 1 if event.y > self.last_y else -1
                    #   remember this location for the next time this is called
                    self.last_y = event.y
                    #   do the scroll
                    self.command('scroll', delta, 'units')
                    # afix slider to mouse pointer
                    mouse_pos = event.y - self.first_y
                    if self.new_start_y != 0:
                        mouse_pos = event.y - self.y_move_on_click
                    self.command('moveto', mouse_pos / self.winfo_height())
                elif self.orient == 'horizontal':
                    if abs(event.x - self.last_x) < jerkiness:
                        return
                    # scroll the scrolled widget in proportion to mouse motion
                    #   compute whether scrolling left or right
                    delta = 1 if event.x > self.last_x else -1
                    #   remember this location for the next time this is called
                    self.last_x = event.x
                    #   do the scroll
                    self.command('scroll', delta, 'units')
                    # afix slider to mouse pointer
                    mouse_pos = event.x - self.first_x
                    if self.new_start_x != 0:
                        mouse_pos = event.x - self.x_move_on_click
                    self.command('moveto', mouse_pos / self.winfo_width())

            def fade_out(self):
                if self.hidden:
                    return

                max_frames = 20

                def reduce_opacity(frame):
                    color = convert_color((0.6 - (frame / (max_frames * 2.3)), 0.6 - (frame / (max_frames * 2.3)),
                                           1 - (frame / (max_frames * 1.4))))['hex']
                    self.itemconfig('slider', fill=color, outline=color)
                    if frame <= max_frames:
                        root.after(10, lambda *_: reduce_opacity(frame + 1))

                root.after(10, lambda *_: reduce_opacity(1))

        # Configure background text
        class TkLineNumbers(Canvas):
            """
            Creates a line number widget for a text widget. Options are the same as a tkinter Canvas widget and add the following:
                * -textwidget (Text): The text widget to attach the line numbers to. (Required) (Second argument after master)
                * -justify (str): The justification of the line numbers. Can be "left", "right", or "center". Default is "left".

            Methods to be used outside externally:
                * .redraw(): Redraws the widget (to be used when the text widget is modified)
            """

            def __init__(
                self: TkLineNumbers,
                master: Misc,
                textwidget: Text,
                justify: str = "left",
                # None means take colors from text widget (default).
                # Otherwise it is a function that takes no arguments and returns (fg, bg) tuple.
                colors: Callable[[], tuple[str, str]] | tuple[str, str] | None = None,
                *args,
                **kwargs,
            ) -> None:
                """Initializes the widget -- Internal use only"""

                # Initialize the Canvas widget
                Canvas.__init__(
                    self,
                    master,
                    width=kwargs.pop("width", 40),
                    highlightthickness=kwargs.pop("highlightthickness", 0),
                    borderwidth=kwargs.pop("borderwidth", 2),
                    relief=kwargs.pop("relief", "ridge"),
                    *args,
                    **kwargs,
                )

                # Set variables
                self.textwidget = textwidget
                self.master = master
                self.justify = justify
                self.colors = colors
                self.cancellable_after: Optional[str] = None
                self.click_pos: None = None
                self.x: int | None = None
                self.y: int | None = None

                # Set style and its binding
                self.set_colors()
                self.bind("<<ThemeChanged>>", self.set_colors, add=True)

                # Mouse scroll binding
                self.bind("<MouseWheel>", self.mouse_scroll, add=True)
                self.bind("<Button-4>", self.mouse_scroll, add=True)
                self.bind("<Button-5>", self.mouse_scroll, add=True)

                # Click bindings
                self.bind("<Button-1>", self.click_see, add=True)
                self.bind("<ButtonRelease-1>", self.unclick, add=True)
                self.bind("<Double-Button-1>", self.double_click, add=True)

                # Mouse drag bindings
                self.bind("<Button1-Motion>", self.in_widget_select_mouse_drag, add=True)
                self.bind("<Button1-Leave>", self.mouse_off_screen_scroll, add=True)
                self.bind("<Button1-Enter>", self.stop_mouse_off_screen_scroll, add=True)

                # Set the yscrollcommand of the text widget to redraw the widget
                textwidget["yscrollcommand"] = self.redraw

                # Redraw the widget
                self.redraw()

            def redraw(self, *_) -> None:
                """Redraws the widget"""

                # Resize the widget based on the number of lines in the textwidget and set colors
                self.resize()
                self.set_colors()

                # Delete all the old line numbers
                self.delete("all")

                # Get the first and last line numbers for the textwidget (all other lines are in between)
                first_line = int(self.textwidget.index("@0,0").split(".")[0])
                last_line = int(
                    self.textwidget.index(f"@0,{self.textwidget.winfo_height()}").split(".")[0]
                )

                # Draw the line numbers looping through the lines
                for lineno in range(first_line, last_line + 1):
                    # Check if line is elided
                    tags: tuple[str] = self.textwidget.tag_names(f"{lineno}.0")
                    elide_values: tuple[str] = (self.textwidget.tag_cget(tag, "elide") for tag in tags)

                    # elide values can be empty
                    line_elided: bool = any(getboolean(v or "false") for v in elide_values)

                    # If the line is not visible, skip it
                    dlineinfo: tuple[
                                   int, int, int, int, int
                               ] | None = self.textwidget.dlineinfo(f"{lineno}.0")
                    if dlineinfo is None or line_elided:
                        continue

                    # Create the line number
                    self.create_text(
                        0
                        if self.justify == "left"
                        else int(self["width"])
                        if self.justify == "right"
                        else int(self["width"]) / 2,
                        dlineinfo[1],
                        text=f" {lineno} " if self.justify != "center" else f"{lineno}",
                        anchor={"left": "nw", "right": "ne", "center": "n"}[self.justify],
                        font=self.textwidget.cget("font"),
                        fill=self.foreground_color,
                    )

            def mouse_scroll(self, event: Event) -> None:
                """Scrolls the text widget when the mouse wheel is scrolled -- Internal use only"""

                # Scroll the text widget and then redraw the widget
                self.textwidget.yview_scroll(
                    int(
                        scroll_fix(
                            event.delta if event.delta else event.num,
                            True if event.num != "??" else False,
                        )
                    ),
                    "units",
                )
                self.redraw()

            def click_see(self, event: Event) -> None:
                """When clicking on a line number it scrolls to that line if not shifting -- Internal use only"""

                # If the shift key is down, redirect to self.shift_click()
                if event.state == 1:
                    self.shift_click(event)
                    return

                # Remove the selection tag from the text widget
                self.textwidget.tag_remove("sel", "1.0", "end")

                line: str = self.textwidget.index(f"@{event.x},{event.y}").split(".")[0]
                click_pos = f"{line}.0"

                # Set the insert position to the line number clicked
                self.textwidget.mark_set("insert", click_pos)

                # Scroll to the location of the insert position
                self.textwidget.see("insert")

                self.click_pos: str = click_pos
                self.redraw()

            def unclick(self, _: Event) -> None:
                """When the mouse button is released it removes the selection -- Internal use only"""

                self.click_pos = None

            def double_click(self, _: Event) -> None:
                """Selects the line when double clicked -- Internal use only"""

                # Remove the selection tag from the text widget and select the line
                self.textwidget.tag_remove("sel", "1.0", "end")
                self.textwidget.tag_add("sel", "insert", "insert + 1 line")
                self.redraw()

            def mouse_off_screen_scroll(self, event: Event) -> None:
                """Automatically scrolls the text widget when the mouse is near the top or bottom,
                similar to the in_widget_select_mouse_drag function -- Internal use only"""

                self.x = event.x
                self.y = event.y
                self.text_auto_scan(event)

            def text_auto_scan(self, event):
                if self.click_pos is None:
                    return

                # Taken from the Text source: https://github.com/tcltk/tk/blob/main/library/text.tcl#L676
                # Scrolls the widget if the cursor is off of the screen
                if self.y >= self.winfo_height():
                    self.textwidget.yview_scroll(1 + self.y - self.winfo_height(), "pixels")
                elif self.y < 0:
                    self.textwidget.yview_scroll(-1 + self.y, "pixels")
                elif self.x >= self.winfo_width():
                    self.textwidget.xview_scroll(2, "units")
                elif self.x < 0:
                    self.textwidget.xview_scroll(-2, "units")
                else:
                    return

                # Select the text
                self.select_text(self.x - self.winfo_width(), self.y)

                # After 50ms, call this function again
                self.cancellable_after = self.after(50, self.text_auto_scan, event)
                self.redraw()

            def stop_mouse_off_screen_scroll(self, _: Event) -> None:
                """Stops the auto scroll when the cursor re-enters the line numbers -- Internal use only"""

                # If the after has not been cancelled, cancel it
                if self.cancellable_after is not None:
                    self.after_cancel(self.cancellable_after)
                    self.cancellable_after = None

            def check_side_scroll(self, event: Event) -> None:
                """Detects if the mouse is off the screen to the sides \
        (a case not covered in mouse_off_screen_scroll) -- Internal use only"""

                # Determine if the mouse is off the sides of the widget
                off_side = (
                    event.x < self.winfo_x() or event.x > self.winfo_x() + self.winfo_width()
                )
                if not off_side:
                    return

                # Determine if its above or below the widget
                if event.y >= self.winfo_height():
                    self.textwidget.yview_scroll(1, "units")
                elif event.y < 0:
                    self.textwidget.yview_scroll(-1, "units")
                else:
                    return

                # Select the text
                self.select_text(event.x - self.winfo_width(), event.y)

                # Redraw the widget
                self.redraw()

            def in_widget_select_mouse_drag(self, event: Event) -> None:
                """When click in_widget_select_mouse_dragging it selects the text -- Internal use only"""

                # If the click position is None, return
                if self.click_pos is None:
                    return

                self.x = event.x
                self.y = event.y

                # Select the text
                self.select_text(event.x - self.winfo_width(), event.y)
                self.redraw()

            def select_text(self, x, y) -> None:
                """Selects the text between the start and end positions -- Internal use only"""

                drag_pos = self.textwidget.index(f"@{x}, {y}")
                if self.textwidget.compare(drag_pos, ">", self.click_pos):
                    start = self.click_pos
                    end = drag_pos
                else:
                    start = drag_pos
                    end = self.click_pos

                self.textwidget.tag_remove("sel", "1.0", "end")
                self.textwidget.tag_add("sel", start, end)
                self.textwidget.mark_set("insert", drag_pos)

            def shift_click(self, event: Event) -> None:
                """When shift clicking it selects the text between the click and the cursor -- Internal use only"""

                # Add the selection tag to the text between the click and the cursor
                start_pos: str = self.textwidget.index("insert")
                end_pos: str = self.textwidget.index(f"@0,{event.y}")
                self.textwidget.tag_remove("sel", "1.0", "end")
                if self.textwidget.compare(start_pos, ">", end_pos):
                    start_pos, end_pos = end_pos, start_pos
                self.textwidget.tag_add("sel", start_pos, end_pos)
                self.redraw()

            def resize(self) -> None:
                """Resizes the widget to fit the text widget -- Internal use only"""

                # Get amount of lines in the text widget
                end: str = self.textwidget.index("end").split(".")[0]

                # Set the width of the widget to the required width to display the biggest line number
                temp_font = Font(font=self.textwidget.cget("font"))
                measure_str = " 1234 " if int(end) <= 1000 else f" {end} "
                self.config(width=temp_font.measure(measure_str))

            def set_colors(self, _: Event | None = None) -> None:
                """Sets the colors of the widget according to self.colors - Internal use only"""

                # If the color provider is None, set the foreground color to the Text widget's foreground color
                if self.colors is None:
                    self.foreground_color: str = self.textwidget["fg"]
                    self["bg"]: str = self.textwidget["bg"]
                elif isinstance(self.colors, tuple):
                    self.foreground_color: str = self.colors[0]
                    self["bg"]: str = self.colors[1]
                else:
                    returned_colors: tuple[str, str] = self.colors()
                    self.foreground_color: str = returned_colors[0]
                    self["bg"]: str = returned_colors[1]
        class CodeView(Text):
            _w: str

            def __init__(
                self,
                master: Misc | None = None,
                lexer: LexerType = pygments.lexers.TextLexer,
                color_scheme: dict[str, dict[str, str | int]] | str | None = None,
                tab_width: int = 4,
                linenums_theme: Callable[[], tuple[str, str]] | tuple[str, str] | None = None,
                scrollbar=ttk.Scrollbar,
                **kwargs,
            ) -> None:
                self._frame = ttk.Frame(master)
                self._frame.grid_rowconfigure(0, weight=1)
                self._frame.grid_columnconfigure(1, weight=1)

                kwargs.setdefault("wrap", "none")
                kwargs.setdefault("font", ("monospace", 11))

                super().__init__(self._frame, **kwargs)
                super().grid(row=0, column=1, sticky="nswe")

                self._line_numbers = TkLineNumbers(
                    self._frame, self, justify=kwargs.get("justify", "right"), colors=linenums_theme
                )

                self._vs = scrollbar(master, width=7, command=self.yview)
                # self._hs = ttk.Scrollbar(self._frame, orient="horizontal", command=self.xview)

                self._line_numbers.grid(row=0, column=0, sticky="ns", ipadx=20)
                self._vs.pack(side=RIGHT, fill=Y, padx=(6, 0))
                # self._hs.grid(row=1, column=1, sticky="we")

                super().configure(
                    yscrollcommand=self.vertical_scroll,
                    xscrollcommand=self.horizontal_scroll,
                    tabs=Font(font=kwargs["font"]).measure(" " * tab_width),
                )

                self.bind(f"<Control-c>", self._copy, add=True)
                self.bind(f"<Control-v>", self._paste, add=True)
                self.bind(f"<Control-a>", self._select_all, add=True)
                self.bind(f"<Control-z>", self.undo, add=True)
                self.bind(f"<Control-r>", self.redo, add=True)
                self.bind(f"<Control-y>", self.redo, add=True)
                self.bind("<<ContentChanged>>", self.scroll_line_update, add=True)
                self.bind("<Button-1>", self._line_numbers.redraw, add=True)
                self.bind("<Control-BackSpace>", self.ctrl_bs)

                self._orig = f"{self._w}_widget"
                self.tk.call("rename", self._w, self._orig)
                self.tk.createcommand(self._w, self._cmd_proxy)

                self._set_lexer(lexer)
                self._set_color_scheme(color_scheme)

            def _select_all(self, *_) -> str:
                self.tag_add("sel", "1.0", "end")
                self.mark_set("insert", "end")
                return "break"

            def redo(self, *_):
                self.edit_redo()
                self.highlight_all()
                self.scroll_line_update()

            def undo(self, *_):
                self.edit_undo()
                self.highlight_all()
                self.scroll_line_update()

            def ctrl_bs(self, event, *_):
                self.delete("insert-1c wordstart", "insert")
                self.highlight_all()
                self.scroll_line_update()
                return "break"

            def _paste(self, *_):
                insert = self.index(f"@0,0 + {self.cget('height') // 2} lines")

                with suppress(TclError):
                    self.delete("sel.first", "sel.last")
                    self.tag_remove("sel", "1.0", "end")
                    self.insert("insert", self.clipboard_get())

                self.see(insert)

                return "break"

            def _copy(self, *_):
                text = self.get("sel.first", "sel.last")
                if not text:
                    text = self.get("insert linestart", "insert lineend")

                root.clipboard_clear()
                root.clipboard_append(text)
                root.update()

                return "break"

            def _cmd_proxy(self, command: str, *args) -> Any:
                try:
                    if command in {"insert", "delete", "replace"}:
                        start_line = int(str(self.tk.call(self._orig, "index", args[0])).split(".")[0])
                        end_line = start_line
                        if len(args) == 3:
                            end_line = int(str(self.tk.call(self._orig, "index", args[1])).split(".")[0]) - 1
                    result = self.tk.call(self._orig, command, *args)
                except TclError as e:
                    error = str(e)
                    if 'tagged with "sel"' in error or "nothing to" in error:
                        return ""
                    raise e from None

                if command == "insert":
                    if not args[0] == "insert":
                        start_line -= 1
                    lines = args[1].count("\n")
                    if lines == 1:
                        self.highlight_line(f"{start_line}.0")
                    else:
                        self.highlight_area(start_line, start_line + lines)
                    self.event_generate("<<ContentChanged>>")
                elif command in {"replace", "delete"}:
                    if start_line == end_line:
                        self.highlight_line(f"{start_line}.0")
                    else:
                        self.highlight_area(start_line, end_line)
                    self.event_generate("<<ContentChanged>>")

                return result

            def _setup_tags(self, tags: dict[str, str]) -> None:
                for key, value in tags.items():
                    if isinstance(value, str):
                        # Italicize certain values
                        if key.lower().startswith('keyword'):
                            self.tag_configure(f"Token.{key}", foreground=value, font=self['font'] + ' italic')
                        else:
                            self.tag_configure(f"Token.{key}", foreground=value)

            def highlight_line(self, index: str) -> None:
                line_num = int(self.index(index).split(".")[0])
                for tag in self.tag_names(index=None):
                    if tag.startswith("Token"):
                        self.tag_remove(tag, f"{line_num}.0", f"{line_num}.end")

                line_text = self.get(f"{line_num}.0", f"{line_num}.end")
                start_col = 0

                for token, text in pygments.lex(line_text, self._lexer):
                    token = str(token)
                    end_col = start_col + len(text)
                    if token not in {"Token.Text.Whitespace", "Token.Text"}:
                        self.tag_add(token, f"{line_num}.{start_col}", f"{line_num}.{end_col}")
                    start_col = end_col

            def highlight_all(self) -> None:
                for tag in self.tag_names(index=None):
                    if tag.startswith("Token"):
                        self.tag_remove(tag, "1.0", "end")

                lines = self.get("1.0", "end")
                line_offset = lines.count("\n") - lines.lstrip().count("\n")
                start_index = str(self.tk.call(self._orig, "index", f"1.0 + {line_offset} lines"))

                for token, text in pygments.lex(lines, self._lexer):
                    token = str(token)
                    end_index = self.index(f"{start_index} + {len(text)} chars")
                    if token not in {"Token.Text.Whitespace", "Token.Text"}:
                        self.tag_add(token, start_index, end_index)
                    start_index = end_index

            def highlight_area(self, start_line: int | None = None, end_line: int | None = None) -> None:
                for tag in self.tag_names(index=None):
                    if tag.startswith("Token"):
                        self.tag_remove(tag, f"{start_line}.0", f"{end_line}.end")

                text = self.get(f"{start_line}.0", f"{end_line}.end")
                line_offset = text.count("\n") - text.lstrip().count("\n")
                start_index = str(self.tk.call(self._orig, "index", f"{start_line}.0 + {line_offset} lines"))
                for token, text in pygments.lex(text, self._lexer):
                    token = str(token)
                    end_index = self.index(f"{start_index} + {len(text)} indices")
                    if token not in {"Token.Text.Whitespace", "Token.Text"}:
                        self.tag_add(token, start_index, end_index)
                    start_index = end_index

            def _set_color_scheme(self, color_scheme: dict[str, dict[str, str | int]] | str | None) -> None:
                assert isinstance(color_scheme, dict), "Must be a dictionary or a built-in color scheme"

                config, tags = _parse_scheme(color_scheme)
                self.configure(**config)
                self._setup_tags(tags)

                self.highlight_all()

            def _set_lexer(self, lexer: LexerType) -> None:
                self._lexer = lexer() if inspect.isclass(lexer) else lexer
                self.highlight_all()

            def __setitem__(self, key: str, value) -> None:
                self.configure(**{key: value})

            def __getitem__(self, key: str) -> Any:
                return self.cget(key)

            def configure(self, **kwargs) -> None:
                lexer = kwargs.pop("lexer", None)
                color_scheme = kwargs.pop("color_scheme", None)

                if lexer is not None:
                    self._set_lexer(lexer)

                if color_scheme is not None:
                    self._set_color_scheme(color_scheme)

                super().configure(**kwargs)

            config = configure

            def pack(self, *args, **kwargs) -> None:
                self._frame.pack(*args, **kwargs)

            def grid(self, *args, **kwargs) -> None:
                self._frame.grid(*args, **kwargs)

            def place(self, *args, **kwargs) -> None:
                self._frame.place(*args, **kwargs)

            def pack_forget(self) -> None:
                self._frame.pack_forget()

            def grid_forget(self) -> None:
                self._frame.grid_forget()

            def place_forget(self) -> None:
                self._frame.place_forget()

            def destroy(self) -> None:
                for widget in self._frame.winfo_children():
                    BaseWidget.destroy(widget)
                BaseWidget.destroy(self._frame)

            def horizontal_scroll(self, first: str | float, last: str | float) -> CodeView:
                # self._hs.set(first, last)
                pass

            def vertical_scroll(self, first: str | float, last: str | float) -> CodeView:
                self._vs.set(first, last)
                self._line_numbers.redraw()

            def scroll_line_update(self, event: Event | None = None) -> CodeView:
                self.horizontal_scroll(*self.xview())
                self.vertical_scroll(*self.yview())
        class HighlightText(CodeView):

            def __init__(self, *args, **kwargs):
                CodeView.__init__(self, *args, **kwargs)
                self.last_search = ""
                self.match_counter = Label(justify='right', anchor='se')
                self.match_counter.place(in_=search, relwidth=0.2, relx=0.8, rely=0.2)
                self.match_counter.configure(
                    fg = convert_color((0.3, 0.3, 0.65))['hex'],
                    bg = background_color,
                    borderwidth = 0,
                    font = "Consolas 14 bold"
                )

                # self.bind("<<ContentChanged>>", self.fix_tabs)
                self.bind("<BackSpace>", self.delete_spaces)
                self.bind('<KeyPress>', self.insert_spaces)

            # Replaces all tabs with 4 spaces
            def fix_tabs(self, *_):
                self.replace_all('\t', tab_str)

            # Replaces all occurrences of target with replacement
            def replace_all(self, target, replacement):
                start = "1.0"
                while True:
                    start = self.search(target, start, stopindex=END)
                    if not start:
                        break
                    end = f"{start}+{len(target)}c"
                    self.delete(start, end)
                    self.insert(start, replacement)
                    start = f"{start}+1c"

            # Deletes spaces when backspacing
            def delete_spaces(self, *_):
                current_pos = self.index(INSERT)
                line_start = self.index(f"{current_pos} linestart")
                line_text = self.get(line_start, current_pos)

                if len(line_text) >= 4:
                    compare = line_text[-4:]
                    length = 4
                else:
                    compare = line_text
                    length = len(line_text)

                if compare == (' '*length) and line_text:
                    self.delete(f"{current_pos}-{length}c", current_pos)
                    return 'break'


            # Insert spaces instead of tab character
            def insert_spaces(self, event):
                if event.keysym == 'Tab':
                    self.insert(INSERT, tab_str)
                    return 'break'  # Prevent default behavior of the Tab key

            def highlight_pattern(self, pattern, tag, start="1.0", end="end", regexp=False):
                start = self.index(start)
                end = self.index(end)
                self.mark_set("matchStart", start)
                self.mark_set("matchEnd", start)
                self.mark_set("searchLimit", end)

                count = IntVar()
                x = 0
                while True:
                    try:
                        index = self.search(pattern, "matchEnd", "searchLimit", count=count, regexp=regexp, nocase=True)
                    except:
                        break

                    if index == "":
                        break

                    self.mark_set("matchStart", index)
                    self.mark_set("matchEnd", "%s+%sc" % (index, count.get()))
                    self.tag_add(tag, "matchStart", "matchEnd")

                    if index == "1.0":
                        break

                    if x == 0:
                        self.see(index)
                        self.last_search = search.get()
                    x += 1

                if search.has_focus or x > 0:
                    self.match_counter.configure(
                        text=f'{x} result(s)',
                        fg = text_color if x > 0 else convert_color((0.3, 0.3, 0.65))['hex']
                    )
                else:
                    self.match_counter.configure(text='')

        code_editor = HighlightText(
            root,
            lexer = pygments.lexers.PythonLexer,
            color_scheme = style,
            font = "Consolas 15",
            linenums_theme = ('#3E3E63', background_color),
            scrollbar=Scrollbar
        )
        code_editor.pack(fill="both", expand=True, pady=10)
        code_editor.config(autoseparator=False, maxundo=0, undo=False)
        code_editor.insert(END, ams_data)
        code_editor.config(autoseparator=True, maxundo=-1, undo=True)
        code_editor._line_numbers.config(borderwidth=0, highlightthickness=0)


        # Highlight stuffies
        code_editor.tag_configure("highlight", foreground="black", background="#4CFF99")

        def highlight_search():
            if root.close:
                return

            if code_editor._vs.last_scrolled < 4:
                code_editor._vs.last_scrolled += 1
                if code_editor._vs.last_scrolled == 4:
                    code_editor._vs.fade_out()

            search_text = search.get()
            if search_text:
                code_editor.tag_remove("highlight", "1.0", "end")
                code_editor.highlight_pattern(search.get(), "highlight", regexp=False)

            root.after(250, highlight_search)
        highlight_search()

        # Search icon
        icon = ImageTk.PhotoImage(Image.open(os.path.join(data['gui_assets'], 'color-search.png')))
        search_icon = Label(image=icon, bg=background_color)
        search_icon.place(anchor='nw', in_=search, x=-50, y=-2)


        # # When window is closed
        # def on_closing():
        #     root.close = True
        #     root.destroy()
        #
        # root.protocol("WM_DELETE_WINDOW", on_closing)

        root.mainloop()



def open_log(path: str, data: dict, *args):
    if path:
        process = multiprocessing.Process(target=functools.partial(launch_window, path, data), daemon=True)
        process.start()
        data['sub_processes'].append(process.pid)



if __name__ == '__main__':
    import constants

    from ctypes import windll, c_int64
    windll.user32.SetProcessDpiAwarenessContext(c_int64(-4))

    data_dict = {
        'app_title': constants.app_title,
        'gui_assets': constants.gui_assets,
        'background_color': constants.background_color
    }
    path = r"C:\Users\macarooni machine\AppData\Roaming\.auto-mcs\Tools\amscript\test2.ams"
    launch_window(path, data_dict)
