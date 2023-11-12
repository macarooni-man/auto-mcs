from __future__ import annotations

from tkinter import Tk, Entry, Label, Canvas, BOTTOM, X, BOTH, END, FIRST, IntVar, Frame, PhotoImage, INSERT, BaseWidget,\
    Event, Misc, TclError, Text, ttk, RIGHT, Y, getboolean, SEL_FIRST, SEL_LAST, Button, SUNKEN

from typing import Any, Callable, Optional, Type, Union
from pygments.token import Keyword, Number, Name
from pygments.filters import NameHighlightFilter
from difflib import SequenceMatcher
from contextlib import suppress
from PIL import ImageTk, Image
from tkinter.font import Font
from threading import Timer
import multiprocessing
import pygments.lexers
import pygments.lexer
import functools
import pygments
import time
import os
import re



LexerType = Union[Type[pygments.lexer.Lexer], pygments.lexer.Lexer]
tab_str = '    '
suggestions = {}
font_size = 16


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
        "Keyword.Event": "event",
        "Keyword.MajorClass": "major_class",
        "Keyword.Argument": "argument"
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


# Checks for string similarity
def similarity(a, b):
    return round(SequenceMatcher(None, a, b).ratio(), 2)


# Gets list of functions and attributes
def iter_attr(obj, a_start=''):
    final_list = []
    for attr in dir(obj):
        if not attr.startswith('_'):
            if callable(getattr(obj, attr)):
                final_list.append(a_start + attr + '()')
            else:
                final_list.append(a_start + attr)
    final_list = sorted(final_list, key=lambda x: x.endswith('()'), reverse=True)
    return final_list


# Changes colors for specific attributes
class AmsLexer(pygments.lexers.PythonLexer):
    def __init__(self, data, **kwargs):
        super().__init__(**kwargs)

        hl_filter = NameHighlightFilter(
            names=[e.split('.')[1] for e in data['script_obj'].valid_events],
            tokentype=Keyword.Event,
        )

        var_filter = NameHighlightFilter(
            names=data['script_obj'].protected_variables,
            tokentype=Keyword.MajorClass,
        )

        self.add_filter(hl_filter)
        self.add_filter(var_filter)
AmsLexer.tokens['root'].insert(-2, (r'(?<!=)(\b(\d+\.?\d*?(?=\s*=[^,)]|\s*\)|\s*,)(?=.*\):))\b)', Number.Float))
AmsLexer.tokens['root'].insert(-2, (r'(?<!=)(\b(\w+(?=\s*=[^,)]|\s*\)|\s*,)(?=.*\):))\b)', Keyword.Argument))
AmsLexer.tokens['builtins'].insert(0, (r'(?=\s*?\w+?)(\.?\w*(?=\())(?=.*?$)', Name.Function))
# AmsLexer.tokens['classname'] = [('(?<=class ).+?(?=\()', Name.Class, '#pop')]


# Main window data
window = None
process = None
close_window = False
currently_open = []
open_frames = {}
background_color = '#040415'
frame_background = '#121223'
faded_text = '#4A4A70' # '#444477'
color_search = None
replace_shown = False


# Saves script to disk
def save_script(script_path, *a):
    global open_frames, currently_open
    script_name = os.path.basename(script_path)
    if script_path in currently_open:
        script_contents = open_frames[script_name].code_editor.get("1.0", 'end-1c')

        try:
            with open(script_path, 'w+') as f:
                f.write(script_contents)
        except Exception as e:
            print(e)


# Init Tk window
def create_root(data, wdata, name=''):
    global window, close_window, currently_open

    if not window:

        drag_code = """namespace eval tabdrag {}
bind TNotebook <Destroy> {+tabdrag::destroy %W}
bind TNotebook <Button-1> {+tabdrag::click %W %x %y}
bind TNotebook <ButtonRelease-1> {+tabdrag::release %W %x %y}
bind TNotebook <B1-Motion> {+tabdrag::move %W %x %y}

proc ::tabdrag::destroy {win} {
  variable winstate;

  array unset winstate ?,$win
}

proc ::tabdrag::click {win x y} {
  variable winstate;

  set what [$win identify tab $x $y]
  if { $what eq "" || [$win index end] <= 1} {
       return;
     }

  set winstate(x,$win) $x
  set winstate(t,$win) [lindex [$win tabs] $what]
  set winstate(e,$win) 0
}

proc ::tabdrag::release {win x y} {
  variable winstate;

  array unset winstate ?,$win
}

proc ::tabdrag::move {win x y} {
  variable winstate;

  if { ![info exists winstate(x,$win)] || ![info exists winstate(t,$win)] || $winstate(t,$win) eq "" } {
       return;
     }

  set where [$win identify tab $x $y]
  if { [info exists winstate(a,$win)] } {
       if { $x < $winstate(a,$win) && $where < $winstate(i,$win) } {
            unset -nocomplain winstate(a,$win) winstate(i,$win) winstate(j,$win)
          } elseif { $x > $winstate(a,$win) && $where > $winstate(i,$win) } {
            unset -nocomplain winstate(a,$win) winstate(i,$win) winstate(j,$win)
          }
     }
  if { $where ne "" } {
       set what [lindex [$win tabs] $where]
     } else {
       set what ""
     }
  if { $what eq $winstate(t,$win) } {
       return;
     }
  if { $what eq "" } {
       # Not over a tab - check to see if we're before or after where we started
       if { $winstate(e,$win) } {
            return;
          }
       set winstate(e,$win) 1
       if { $x < $winstate(x,$win) } {
            $win insert 0 $winstate(t,$win)
          } else {
            $win insert end $winstate(t,$win)
          }
       #unset -nocomplain winstate(j,$win) winstate(a,$win) winstate(i,$win)
       set winstate(x,$win) $x
     } else {
       set winstate(e,$win) 0
       if { [info exists winstate(j,$win)] && $what eq $winstate(j,$win) } {
            if { (($x > $winstate(x,$win) && $x > $winstate(a,$win)) || ($x < $winstate(x,$win) && $x < $winstate(a,$win))) } {
                 return;# avoid stuttering when jumping a bigger tab
               }
          }
       $win insert $what $winstate(t,$win)
       set winstate(j,$win) $what
       set winstate(a,$win) $x
       set winstate(i,$win) $where
     }
}"""

        file_icon = os.path.join(data['gui_assets'], "amscript-icon.png")
        min_size = (950, 600)
        start_size = (1100, 700)

        window = Tk()
        window.tk.eval(drag_code)
        width = window.winfo_screenwidth()
        height = window.winfo_screenheight()
        x = int((width / 2) - (start_size[0] / 2))
        y = int((height / 2) - (start_size[1] / 2)) - 15
        window.geometry(f"{start_size[0]}x{start_size[1]}+{x}+{y}")
        window.minsize(width=min_size[0], height=min_size[1])
        window.title(f'{data["app_title"]} - amscript IDE')
        img = PhotoImage(file=file_icon)
        window.tk.call('wm', 'iconphoto', window._w, img)
        window.configure(bg=background_color)
        close_window = False

        # When window is closed
        def on_closing():
            global close_window, currently_open, open_frames
            close_window = True
            for s in open_frames.values():
                s.save()
            window.destroy()

        window.protocol("WM_DELETE_WINDOW", on_closing)
        window.close = on_closing

        class CloseNotebook(ttk.Notebook):
            """A ttk Notebook with close buttons on each tab"""

            __initialized = False

            def __init__(self, *args, **kwargs):
                if not self.__initialized:
                    self.__initialize_custom_style()
                    self.__inititialized = True

                kwargs["style"] = "CustomNotebook"
                ttk.Notebook.__init__(self, *args, **kwargs)

                self._active = None

                self.bind("<ButtonPress-1>", self.on_close_press, True)
                self.bind("<ButtonRelease-1>", self.on_close_release)

            def remove_tab(self, tab):
                global currently_open, open_frames

                script_path = self.nametowidget(self.tabs()[tab]).path
                save_script(script_path)

                currently_open.remove(script_path)
                del open_frames[os.path.basename(script_path)]

            def on_close_press(self, event):
                """Called when the button is pressed over the close button"""

                element = self.identify(event.x, event.y)

                if "close" in element:
                    index = self.index("@%d,%d" % (event.x, event.y))
                    self.state(['pressed'])
                    self._active = index
                    return "break"

            def on_close_release(self, event):
                """Called when the button is released"""
                if not self.instate(['pressed']):
                    return

                element = self.identify(event.x, event.y)
                if "close" not in element:
                    # user moved the mouse off of the close button
                    return

                index = self.index("@%d,%d" % (event.x, event.y))

                if self._active == index:
                    self.remove_tab(index)
                    self.forget(index)
                    self.event_generate("<<NotebookTabClosed>>")

                self.state(["!pressed"])
                self._active = None

                if not self.tabs():
                    window.close()


            def __initialize_custom_style(self):
                style = ttk.Style()
                self.images = (
                    PhotoImage("img_close", data='''
                        iVBORw0KGgoAAAANSUhEUgAAAAsAAAALCAYAAACprHcmAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZ
                        cwAADsMAAA7DAcdvqGQAAACuSURBVChTfZCxDYMwEEUPVkiRBSKaFKlDixQpqzAQq6BYYogU6YKUloId8t/JQWCsfOn7
                        fPf/+WwbuN3bq3jwJAF1dPaFNrViEN9iE/puRgDxgEE8kZZaRvEjXsThN2FlpI4+FloQjgoIZ/EpNjHH+CLXxMnNINOw
                        MSraYgbJ6I0RcGdHxsiER6w73Jw7MUby5dHln9G7Bk6uRP5xbbSkAR2fX6MW+Y0dqKObmX0BAJRJ/Lu+BmEAAAAASUVO
                        RK5CYII=
                        '''),
                    PhotoImage("img_closeactive", data='''
                        iVBORw0KGgoAAAANSUhEUgAAAAsAAAALCAYAAACprHcmAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZ
                        cwAADsMAAA7DAcdvqGQAAADTSURBVChTY7S1tWVw88yyZGBguLVr+7S3QBoFAOWEgZQaUO44Y3PbcisgZxcQ3wFiZ2QN
                        UIV7gVgFxGUCEneB+AEQ6wPxXqgCZIUgcZD8XeY/v159VVY1XQvkeAKxLhC7A/mrgTRM4VUgBtn4EmQyA4gBEoBKgG2A
                        0nCFQJoBrBgEoAL2QHwRiDEUggBcMZobQQq1gXgnzA8gAFaMRSGKk2AamLApxOYHkDqQyWpADApHZIXongbJq4GC7gkw
                        qA4AOROQPQMCd++chgXr1l3bpx0HAEBwZFFBTrWkAAAAAElFTkSuQmCC
                        '''),
                    PhotoImage("img_closepressed", data='''
                        iVBORw0KGgoAAAANSUhEUgAAAAsAAAALCAYAAACprHcmAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZ
                        cwAADsMAAA7DAcdvqGQAAADdSURBVChTY6yqqmJw88yyZGBguLVr+7S3QBoFAOWEgZQaUO4444HDT6yAnF1AfAeInZE1
                        QBXuBWIVEJcJSNwF4gdArA/Ee6EKkBWCxEHyd5mlJDm+KquargVyPIFYF4jdgfzVQBqm8CoQg2x8CTKZAcQACUAlwDZA
                        abhCIM0AVgwCUAF7IL4IxBgKQQCuGM2NIIXaQLwT5gcQACvGohDFSTANoKDDUAiyGqhAHCoOsgHkNGeQyWpADApHFDdC
                        aZgNIHk1UNA9AQbVASBnArJnQODundOwYN26a/u04wCEqmHekyLrLQAAAABJRU5ErkJggg==
                        '''),
                    PhotoImage("img_divide", data='''
                        iVBORw0KGgoAAAANSUhEUgAAAAEAAAAQCAIAAABY/YLgAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZ
                        cwAADsMAAA7DAcdvqGQAAAAUSURBVBhXY2BlEWNiYGAgDzMwAAALcQA+nHogLQAAAABJRU5ErkJggg==
                        ''')
                )

                style.theme_create('flat', settings={
                    "CustomNotebook.Tab": {
                        "configure": {
                            "foreground": "#AAAADD",
                            "background": '#242435',  # tab color when not selected
                            "expand": [1, 1, 1, 0],
                            "padding": [15, 2, 10, 2],
                            # [space between text and horizontal tab-button border, space between text and vertical tab_button border]
                            "font": f"Verdana {font_size-3}",
                            "relief": "flat",
                            "borderwidth": 0
                        },
                        "map": {
                            "foreground": [("selected", "#AAAAFF")],
                            "background": [("selected", background_color)],  # Tab color when selected
                            # "expand": [("selected", [1, 1, 1, 0])],  # text margins
                            "relief": [("selected", SUNKEN)]
                        }
                    }
                })
                style.theme_use('flat')
                style.element_create("close", "image", "img_close", ("active", "pressed", "!disabled", "img_closepressed"), ("active", "!disabled", "img_closeactive"), sticky='e', padding=(35, 35, 0, 0))
                style.layout("CustomNotebook", [("CustomNotebook.client", {"sticky": "nswe"})])
                style.layout("CustomNotebook.Tab", [
                    ("CustomNotebook.tab", {
                        "sticky": "nswe",
                        "children": [
                            ("CustomNotebook.padding", {
                                "side": "top",
                                "sticky": "nswe",
                                "children": [
                                    ("CustomNotebook.focus", {
                                        "side": "top",
                                        "sticky": "nswe",
                                        "children": [
                                            ("CustomNotebook.label", {"side": "left", "sticky": ''}),
                                            ("CustomNotebook.close", {"side": "left", "sticky": ''})
                                        ]
                                    })
                                ]
                            })
                        ]
                    })
                ])
                style.layout("CustomNotebook", [])
                style.configure("CustomNotebook", tabmargins=(9, 9, 9, 7), borderwidth=0, highlightthickness=0, background=frame_background, relief=SUNKEN)

        window.root = CloseNotebook(window, takefocus=False)
        window.root.pack(expand=1, fill='both')

        # Add logo
        logo = ImageTk.PhotoImage(Image.open(os.path.join(data['gui_assets'], 'amscript-banner.png')))
        logo_frame = Label(window, image=logo, bg=frame_background)
        logo_frame.place(anchor='nw', in_=window, x=-174, rely=0, relx=1, y=7)

        def check_new():
            global close_window, currently_open, open_frames
            if close_window:
                return

            script_path = wdata.value
            if script_path and script_path not in currently_open:
                launch_window(script_path, data)
                currently_open.append(script_path)
                wdata.value = ''
            elif script_path and script_path in currently_open:
                window.root.select(open_frames[os.path.basename(script_path)])
                wdata.value = ''
            window.after(1000, check_new)

        check_new()
        window.mainloop()


# Opens the amscript editor with the specified path in a new tab
def launch_window(path: str, data: dict, *a):
    global window, color_search, open_frames, replace_shown

    # Get text
    ams_data = ''
    if path:

        with open(path, 'r') as f:
            ams_data = f.read().replace('\t', tab_str)

        error_bg = convert_color((0.3, 0.1, 0.13))['hex']
        text_color = convert_color((0.6, 0.6, 1))['hex']

        style = {
            'editor': {'bg': background_color, 'fg': '#b3b1ad', 'select_fg': "#DDDDFF", 'select_bg': convert_color((0.2, 0.2, 0.4))['hex'], 'inactive_select_bg': '#1b2733',
                'caret': convert_color((0.7, 0.7, 1, 1))['hex'], 'caret_width': '3', 'border_width': '0', 'focus_border_width': '0', 'font': f"Consolas {font_size} italic"},
            'general': {'comment': '#626a73', 'error': '#ff3333', 'escape': '#b3b1ad', 'keyword': '#FB71FB',
                'name': '#819CE6', 'string': '#c2d94c', 'punctuation': '#68E3FF'},
            'keyword': {'constant': '#FB71FB', 'declaration': '#FB71FB', 'namespace': '#FB71FB', 'pseudo': '#FB71FB',
                'reserved': '#FB71FB', 'type': '#FB71FB', 'event': "#FF00A8", 'major_class': '#6769F1', 'argument': '#FC9741'},
            'name': {'attr': '#819CE6', 'builtin': '#819CE6', 'builtin_pseudo': '#e6b450', 'class': '#FFCD38',
                'class_variable': '#819CE6', 'constant': '#ffee99', 'decorator': '#68E3FF', 'entity': '#819CE6',
                'exception': '#819CE6', 'function': '#819CE6', 'global_variable': '#819CE6',
                'instance_variable': '#819CE6', 'label': '#819CE6', 'magic_function': '#819CE6',
                'magic_variable': '#819CE6', 'namespace': '#b3b1ad', 'tag': '#819CE6', 'variable': '#819CE6'},
            'operator': {'symbol': '#68E3FF', 'word': '#FB71FB'},
            'string': {'affix': '#68E3FF', 'char': '#95e6cb', 'delimeter': '#c2d94c', 'doc': '#c2d94c',
                'double': '#c2d94c', 'escape': '#68E3FF', 'heredoc': '#c2d94c', 'interpol': '#68E3FF',
                'regex': '#95e6cb', 'single': '#c2d94c', 'symbol': '#c2d94c'},
            'number': {'binary': '#FC9741', 'float': '#FC9741', 'hex': '#FC9741', 'integer': '#FC9741', 'long': '#FC9741',
                'octal': '#FC9741'},
            'comment': {'hashbang': '#3F4875', 'multiline': '#3F4875', 'preproc': '#3F4875', 'preprocfile': '#3F4875',
                'single': '#3F4875', 'special': '#3F4875'}
        }

        root = Frame(padx=0, pady=0, bg=background_color)
        root.path = path
        root.save = functools.partial(save_script, root.path)

        def save_current(*a):
            current_tab_index = window.root.index(window.root.select())
            current_frame = list(open_frames.values())[current_tab_index]
            current_frame.save()

        root.bind_all('<Control-s>', save_current)

        placeholder_frame = Frame(root, height=40, highlightbackground=frame_background, background=frame_background)
        placeholder_frame.pack(fill=X, side=BOTTOM)
        placeholder_frame.configure(bg=frame_background, borderwidth=0, highlightthickness=0)

        # Configure search box
        class SearchBox(Entry):
            def __init__(self, master=None, placeholder="PLACEHOLDER", color=faded_text):
                super().__init__(master)

                self.placeholder = placeholder
                self.placeholder_color = color
                self.default_fg_color = text_color
                self.has_focus = False
                self.last_index = 0

                def hide_replace(*a):
                    if replace.visible:
                        replace.toggle_focus(False)
                    else:
                        self.toggle_focus(False)

                self.bind("<FocusIn>", self.foc_in)
                self.bind("<FocusOut>", self.foc_out)
                self.bind("<Control-BackSpace>", self.ctrl_bs)
                self.bind('<Escape>', lambda *_: hide_replace(), add=True)
                self.bind('<KeyPress>', self.process_keys)
                self.bind("<Control-h>", lambda *_: replace.toggle_focus(True))
                self.bind('<Shift-Return>', lambda *_: trigger_replace())

                self.put_placeholder()

            def toggle_focus(self, fs=True):

                # Get the currently selected tab index
                current_tab_index = window.root.index(window.root.select())

                # Get the currently visible frame
                current_frame = list(open_frames.values())[current_tab_index]

                s = current_frame.search
                c = current_frame.code_editor

                if s.has_focus or not fs:
                    c.focus_force()
                    c.see(c.index(INSERT))
                else:
                    s.focus_force()
                return 'break'

            def see_index(self, index):
                code_editor.see(f"{index}.0")
                self.last_index = index
                replace.last_index = index

            def iterate_selection(self, forward=True):
                if len(code_editor.match_list) > 1:
                    if forward:
                        for i in code_editor.match_list:
                            if i > self.last_index:
                                self.see_index(i)
                                break
                        else:
                            self.see_index(code_editor.match_list[0])

                    else:
                        for i in reversed(code_editor.match_list):
                            if i < self.last_index:
                                self.see_index(i)
                                break
                        else:
                            self.see_index(code_editor.match_list[-1])

            def process_keys(self, event):
                if event.keysym == "Return":
                    if event.state == 33:
                        self.iterate_selection(False)
                    else:
                        self.iterate_selection(True)

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
        search_frame.configure(bg=frame_background, borderwidth=0, highlightthickness=0)
        search_frame.place(rely=1, y=-45, relwidth=1, height=55)
        root.search = SearchBox(search_frame, placeholder='search for text')
        search = root.search
        search.pack(fill=BOTH, expand=True, padx=(60, 5), pady=(0, 10), side=BOTTOM, ipady=0, anchor='s')
        search.configure(
            bg = frame_background,
            borderwidth = 0,
            highlightthickness = 0,
            selectforeground = convert_color((0.75, 0.75, 1))['hex'],
            selectbackground = convert_color((0.2, 0.2, 0.4))['hex'],
            insertwidth = 3,
            insertbackground = convert_color((0.55, 0.55, 1, 1))['hex'],
            font = f"Consolas {font_size}",
        )
        window.bind('<Control-f>', lambda *_: search.toggle_focus(True))

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
                self.allow_highlight = False
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

                self.textwidget.bind("<<ContentChanged>>", self.get_cursor, add=True)

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

                index = -1
                if self.allow_highlight:
                    index = int(self.textwidget.index(INSERT).split(".")[0])

                err_index = -1
                try:
                    if code_editor.error:
                        line = code_editor.error['line']
                        if ":" in line:
                            err_index = int(line.split(':')[0].strip())
                        else:
                            err_index = int(line.strip())
                except:
                    pass


                # Draw the line numbers looping through the lines
                for lineno in range(first_line, last_line + 1):

                    # Check if it's searched
                    search_match = False
                    try:
                        search_match = lineno in code_editor.match_list
                    except:
                        pass

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
                        dlineinfo[1] + 5.5,
                        text=f" {lineno} " if self.justify != "center" else f"{lineno}",
                        anchor={"left": "nw", "right": "ne", "center": "n"}[self.justify],
                        font=f"Consolas {font_size}",
                        fill=convert_color((1, 0.65, 0.65))['hex'] if err_index == lineno
                        else '#4CFF99' if search_match
                        else '#AAAAFF' if index == lineno
                        else self.foreground_color
                    )

            def get_cursor(self, *a):
                if self.textwidget.index_label and self.allow_highlight:
                    self.textwidget.index_label.configure(text=self.textwidget.index(INSERT).replace('.',':'))

            def redraw_allow(self):
                ac.hide()
                self.allow_highlight = True
                self.redraw()
                self.get_cursor()

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

                self._line_numbers.grid(row=0, column=0, sticky="ns", ipadx=20)
                self._vs.pack(side=RIGHT, fill=Y, padx=(6, 0))

                super().configure(
                    yscrollcommand=self.vertical_scroll,
                    tabs=Font(font=kwargs["font"]).measure(" " * tab_width),
                )

                self.bind(f"<Control-a>", self._select_all, add=True)
                self.bind(f"<Control-z>", self.undo, add=True)
                self.bind(f"<Control-r>", self.redo, add=True)
                self.bind(f"<Control-y>", self.redo, add=True)
                self.bind("<<ContentChanged>>", self.scroll_line_update, add=True)
                self.bind("<Button-1>", self._line_numbers.redraw, add=True)

                self._orig = f"{self._w}_widget"
                self.tk.call("rename", self._w, self._orig)
                self.tk.createcommand(self._w, self._cmd_proxy)

                self._set_lexer()
                self._set_color_scheme(color_scheme)

            def _select_all(self, *_) -> str:
                self.tag_add("sel", "1.0", "end")
                self.mark_set("insert", "end")
                return "break"

            def recalc_lexer(self):
                self.after(0, self.highlight_all)
                self.after(0, self.scroll_line_update)

            def redo(self, *_):
                self.edit_redo()
                self.recalc_lexer()

            def undo(self, *_):
                self.edit_undo()

                def check_suggestions(*a):
                    current_pos = self.index(INSERT)
                    line_num = int(current_pos.split('.')[0])
                    last_line = self.get(f"{line_num}.0", f"{line_num}.end")
                    text = last_line.rsplit(' ', 1)[-1].strip()
                    for k, v in ac.suggestions.items():
                        if text.startswith(k):
                            x, y = self.bbox(INSERT)[:2]
                            ac.show(text, x, y)
                            ac.update_results(text)
                            break
                    else:
                        ac.hide()
                self.after(1, check_suggestions)

                self.recalc_lexer()

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
                        if key.lower().startswith('keyword') or "comment" in key.lower() or 'builtin' in key.lower():
                            self.tag_configure(f"Token.{key}", foreground=value, font=self['font'] + ' italic', selectforeground='#DDDDFF')
                        else:
                            self.tag_configure(f"Token.{key}", foreground=value, selectforeground='#DDDDFF')

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

            def _set_lexer(self) -> None:
                self._lexer = AmsLexer(data)
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

            def vertical_scroll(self, first: str | float, last: str | float) -> CodeView:
                self._vs.set(first, last)
                self._line_numbers.redraw()

            def scroll_line_update(self, event: Event | None = None) -> CodeView:
                self.vertical_scroll(*self.yview())
        class HighlightText(CodeView):

            def __init__(self, *args, **kwargs):
                CodeView.__init__(self, *args, **kwargs)
                self.content_changed = False
                self.last_search = ""
                self.match_list = []
                self.font_size = font_size - 1
                self.match_counter = Label(justify='right', anchor='se')
                self.match_counter.place(in_=search, relwidth=0.2, relx=0.795, rely=0, y=7)
                self.match_counter.configure(
                    fg = convert_color((0.3, 0.3, 0.65))['hex'],
                    bg = frame_background,
                    borderwidth = 0,
                    font = f"Consolas {self.font_size} bold"
                )

                self.index_label = Label(justify='right', anchor='se')
                self.index_label.place(in_=search, relwidth=0.2, relx=0.795, rely=0, y=7)
                self.index_label.configure(
                    fg = convert_color((0.6, 0.6, 1))['hex'],
                    bg = frame_background,
                    borderwidth = 0,
                    font = f"Consolas {self.font_size}"
                )

                self.error_label = Label(justify='right', anchor='se')
                self.error_label.configure(
                    fg = convert_color((1, 0.6, 0.6))['hex'],
                    bg = frame_background,
                    borderwidth = 0,
                    font = f"Consolas {self.font_size} bold"
                )


                # self.bind("<<ContentChanged>>", self.fix_tabs)
                self.bind("<BackSpace>", self.delete_spaces)
                self.bind('<KeyPress>', self.process_keys)
                self.bind('<Control-slash>', self.block_comment)
                self.bind('<Shift-Tab>', lambda *_: self.block_indent(False))
                self.bind("<Control-BackSpace>", self.ctrl_bs)

                # Redraw lineno
                self.bind("<Button-1>", lambda *_: self.after(0, self._line_numbers.redraw_allow), add=True)
                self.bind("<Up>", lambda *_: self.check_ac(False))
                self.bind("<Down>", lambda *_: self.check_ac(True))
                self.bind("<Up>", lambda *_: self.after(0, self._line_numbers.redraw_allow), add=True)
                self.bind("<Down>", lambda *_: self.after(0, self._line_numbers.redraw_allow), add=True)
                self.bind("<Left>", lambda *_: self.after(0, self._line_numbers.redraw_allow), add=True)
                self.bind("<Right>", lambda *_: self.after(0, self._line_numbers.redraw_allow), add=True)
                self.bind("<Control-Left>", self.scroll_text)
                self.bind("<Control-Right>", self.scroll_text)
                self.bind("<Control-h>", lambda *_: replace.toggle_focus(True))
                self.bind("<Control-k>", lambda *_: "break")
                self.bind("<<ContentChanged>>", self.check_syntax, add=True)
                self.bind("<<ContentChanged>>", self.autosave, add=True)
                self.bind("<<Selection>>", self.redo_search, add=True)
                self.bind("<<Selection>>", lambda *_: self.after(0, self.highlight_matching_parentheses), add=True)
                root.bind('<Configure>', self.set_error)
                self.error_label.bind("<Button-1>", lambda *_: self.after(0, self.view_error), add=True)
                self.bind("<KeyRelease>", lambda *_: self.after(0, self.highlight_matching_parentheses))
                self.bind("<Button-1>", lambda *_: self.after(0, self.highlight_matching_parentheses), add=True)
                self.hl_pair = (None, None)

                self.default_timer = 0.25
                self.error_timer = 0
                self.timer_lock = False
                self.error = None

                self.save_interval = 3
                self.save_timer = 0
                self.save_lock = False
                self.first_run = True

                self.bind(f"<Control-c>", self._copy, add=True)
                self.bind(f"<Control-v>", self._paste, add=True)

            @staticmethod
            def is_matching(opening, closing, invert=False):
                if invert:
                    return (opening == ")" and closing == "(" or
                            opening == "]" and closing == "[" or
                            opening == "}" and closing == "{")
                else:
                    return (opening == "(" and closing == ")" or
                            opening == "[" and closing == "]" or
                            opening == "{" and closing == "}")

            @staticmethod
            def get_opposite(char):
                if char == '(':
                    return ')'
                elif char == ')':
                    return '('
                elif char == '}':
                    return '{'
                elif char == '{':
                    return '}'
                elif char == ']':
                    return '['
                elif char == '[':
                    return ']'

            def autosave(self, event):
                if self.save_lock:
                    self.save_timer = self.save_interval
                    return None

                def wait_for_break(*a):
                    self.save_lock = True
                    while self.save_timer > 0:
                        time.sleep(1)
                        self.save_timer -= 1
                        if close_window:
                            return

                    self.save_timer = self.save_interval
                    self.save_lock = False

                    if self.first_run:
                        self.first_run = False
                        return

                    self.after(0, lambda *_: root.save())

                Timer(0, wait_for_break).start()

            def scroll_text(self, *args):
                sel_start = self.index(SEL_FIRST)
                sel_end = self.index(SEL_LAST)

                key = args[0].keysym.lower()
                select = args[0].state == 262181

                current_pos = self.index(INSERT)
                start_pos = current_pos

                while True:
                    index = self.index(f"{current_pos}{'-' if key == 'left' else '+'}1c")
                    if not index or not self.get(index).isspace():
                        break
                    else:
                        self.mark_set(INSERT, current_pos)
                    current_pos = index

                if key == "left":
                    self.mark_set(INSERT, "insert-1c wordstart")
                    current_pos = self.index(INSERT)
                    if select:
                        try:
                            if sel_end and self.compare(current_pos, "<=", sel_end) and self.compare(current_pos, ">=", sel_start):
                                self.tag_remove("sel", "1.0", "end")
                                self.tag_add("sel", sel_start, current_pos)
                                return "break"
                        except:
                            pass
                        self.tag_remove("sel", "1.0", "end")
                        self.tag_add("sel", current_pos, start_pos if not sel_end else sel_end)
                else:
                    self.mark_set(INSERT, "insert+1c wordend")
                    current_pos = self.index(INSERT)
                    if select:
                        try:
                            if sel_start and self.compare(current_pos, ">=", sel_start) and self.compare(current_pos, "<=", sel_end):
                                self.tag_remove("sel", "1.0", "end")
                                self.tag_add("sel", current_pos, sel_end)
                                return "break"
                        except:
                            pass
                        self.tag_remove("sel", "1.0", "end")
                        self.tag_add("sel", start_pos if not sel_start else sel_start, current_pos)
                return "break"

            def highlight_matching_parentheses(self, event=None):
                self.tag_remove("parentheses", "1.0", END)
                self.hl_pair = (None, None)
                cursor_pos = self.index(INSERT)

                stack = {"(": [], "{": [], "[": [], ")": [], "}": [], "]": []}
                levels = {"(": 0, "{": 0, "[": 0, ")": 0, "}": 0, "]": 0}

                looking_for = ''

                left = self.get(self.index(f"{cursor_pos}-1c"))
                right = self.get(cursor_pos)

                o = "({["
                c = ")}]"

                # Check for starting index
                if (left in o and right in c):
                    cursor_pos = self.index(f"{INSERT}-1c")
                    looking_for = left
                    invert = False

                elif (left in c and right in c):
                    looking_for = left
                    cursor_pos = self.index(f"{INSERT}-1c")
                    invert = True

                elif (right in o and left not in c):
                    looking_for = right
                    invert = False

                elif (right in c and left not in o):
                    looking_for = right
                    invert = True

                elif (left in o and right not in c):
                    looking_for = left
                    cursor_pos = self.index(f"{INSERT}-1c")
                    invert = False

                elif (left in c and right not in o):
                    looking_for = left
                    cursor_pos = self.index(f"{INSERT}-1c")
                    invert = True


                if looking_for:
                    for char, index in self.iterate_characters(cursor_pos, '1.0' if invert else END, invert):
                        if char == looking_for:
                            stack[char].append(index)
                            levels[char] += 1
                        elif char == self.get_opposite(looking_for):
                            if stack[looking_for] and self.is_matching(looking_for, char, invert):
                                if levels[looking_for] == 1:
                                    start_opening = stack[looking_for][0]
                                    start_closing = index
                                    end_opening = f"{start_opening}+1c"
                                    end_closing = f"{start_closing}+1c"
                                    try:
                                        o_tag = self.tag_names(start_opening)[0]
                                        c_tag = self.tag_names(start_closing)[0]
                                    except IndexError:
                                        continue
                                    for tag in ('Comment', 'String.Single', 'String.Double', 'String.Doc', 'String.Heredoc', 'sel'):
                                        if tag in o_tag or tag in c_tag:
                                            break
                                    else:
                                        self.tag_add("parentheses", start_opening, end_opening)
                                        self.tag_add("parentheses", start_closing, end_closing)
                                        self.hl_pair = (start_closing, start_opening) if invert else (start_opening, start_closing)
                                        stack[looking_for].pop()
                                        return
                                levels[looking_for] -= 1

            def iterate_characters(self, start, end, invert=False):
                while True:
                    char = self.get(start)
                    if char == "" or (start == '1.0' and invert):
                        break
                    yield char, start
                    start = self.index(f"{start}{'-' if invert else '+'}1c")

                    # Break if start exceeds end
                    s1, s2 = start.split('.', 1)
                    e1, e2 = self.index(end).split('.', 1)

                    if invert:
                        if int(e1) > int(s1):
                            break
                        elif (int(e1) >= int(s1)) and (int(e2) > int(s2)):
                            break
                    else:
                        if int(s1) > int(e1):
                            break
                        elif (int(s1) >= int(e1)) and (int(s2) > int(e2)):
                            break

            def redo_search(self, *a):
                self.content_changed = True

            def check_ac(self, key, *a):
                if ac.visible:
                    ac.iterate_selection(key)
                    return "break"

            def view_error(self, *a):
                self.see(self.error['line'].replace(':','.'))

            def set_error(self, *a):
                code_editor.tag_remove("error", "1.0", "end")

                if self.error:

                    # Update error label
                    self.error_label.place(in_=search, relwidth=0.7, relx=0.295, rely=0, y=5)
                    text = f"[Line {self.error['line']}] {self.error['message']}"
                    max_size = round((root.winfo_width() // self.font_size)*0.65)
                    if len(text) > max_size:
                        text = text[:max_size] + "..."
                    self.error_label.configure(text=text)

                    # Configure text highlighting
                    # print(self.error)
                    try:
                        pattern = self.error['object'].args[1][-1].rstrip()
                    except:
                        pattern = self.error['code']
                    regex = False
                    if pattern == 'Unknown':
                        pattern = ''
                    try:
                        # print(self.error)
                        line, char = self.error['line'].split(':')

                        # Reformat line to start at the beginning
                        if int(char) == 1:
                            char = 0

                        # Reformat pattern if it goes to the next line
                        elif int(char) > len(pattern):
                            pattern = r"( +)?\n"
                            regex = True

                        # Reformat index if pattern is in the middle of the line
                        elif int(char) > 1 and pattern:
                            test = pattern.startswith((int(char)) * ' ')
                            if test:
                                pattern = pattern.strip()
                            else:
                                char = int(char) - 1
                                pattern = pattern[int(char):]

                        # print(pattern)
                        # print(f"{line}.{char}", f"{int(line) + 1}.0")
                        code_editor.highlight_pattern(pattern, "error", start=f"{line}.{char}", end=f"{int(line) + 1}.0", regexp=regex)
                    except Exception as e:
                        print(e)
                else:
                    self.error_label.place_forget()
                    self.error_label.configure(text="")
                self._line_numbers.redraw()

            def check_syntax(self, event):
                self.content_changed = True

                if self.timer_lock:
                    self.error_timer = self.default_timer
                    return None

                def wait_for_break(*a):
                    self.timer_lock = True
                    while self.error_timer > 0:
                        time.sleep(0.25)
                        self.error_timer -= 0.25

                    self.error_timer = self.default_timer
                    self.error = data['script_obj'].is_valid([self.get("1.0",END), path])
                    self.after(0, lambda *_: self.set_error())
                    self.timer_lock = False

                Timer(0, wait_for_break).start()

            def _paste(self, *_):
                insert = self.index(f"@0,0 + {self.cget('height') // 2} lines")

                with suppress(TclError):
                    self.delete("sel.first", "sel.last")
                    self.tag_remove("sel", "1.0", "end")

                    line_num = int(self.index(INSERT).split('.')[0])
                    last_line = self.get(f"{line_num}.0", f"{line_num}.end")
                    indent = self.get_indent(last_line)
                    text = self.clipboard_get().replace('\t', tab_str).splitlines()

                    if len(text) == 1:
                        self.insert("insert", text[0].strip())
                    else:
                        indent_list = []
                        lowest_indent = 0

                        # First, get lowest indent of clipboard
                        for line in text:
                            if not line.strip():
                                continue
                            indent_list.append(self.get_indent(line))

                            # Get lowest indent
                            lowest_indent = min(indent_list)


                        final_text = []

                        if not last_line.strip():
                            self.delete(f'{line_num}.0', f'{line_num}.0 lineend')

                        for line in text:
                            line = line[lowest_indent*len(tab_str):]
                            li = self.get_indent(line)
                            if not last_line.strip():
                                final_indent = indent + li
                                if final_indent < 1:
                                    final_indent = 0
                                final_text.append((final_indent * tab_str) + line.strip())
                            else:
                                final_text.append(line)

                        self.insert("insert", '\n'.join(final_text))

                self.see(insert)
                self.recalc_lexer()
                return "break"

            def _copy(self, *_):
                text = self.get("sel.first", "sel.last")
                if not text:
                    text = self.get("insert linestart", "insert lineend")

                root.clipboard_clear()
                root.clipboard_append(text)
                root.update()

                return "break"

            # Delete things
            def ctrl_bs(self, event, *_):
                current_pos = self.index(INSERT)
                line_start = self.index(f"{current_pos} linestart")
                line_text = self.get(line_start, current_pos)

                # Check if @ was deleted to hide menu
                def test_at(*a):
                    line_num = int(current_pos.split('.')[0])
                    last_line = self.get(f"{line_num}.0", f"{line_num}.end")
                    if last_line.startswith("@"):
                        ac.update_results(last_line)
                    else:
                        ac.hide()
                self.after(0, test_at)

                if line_text.isspace():
                    self.delete(line_start, current_pos)

                else:
                    if not self.delete_spaces():
                        self.delete("insert-1c wordstart", "insert")

                self.recalc_lexer()
                return "break"

            # Gets text and range of line
            def get_line_text(self, l):
                line_start = f"{l}.0"
                line_end = self.index(f"{line_start} lineend")
                line_text = self.get(line_start, line_end)
                return (line_start, line_end), line_text

            @staticmethod
            def get_indent(line):
                count = 0
                for char in line:
                    if char == ' ':
                        count += 1
                    else:
                        break
                if count:
                    count = count // 4
                return count

            # Indent/Dedent block
            def block_indent(self, indent):
                ac.hide()

                sel_start = self.index(SEL_FIRST)
                sel_end = self.index(SEL_LAST)

                if not indent and not (sel_start and sel_end):
                    current_index = int(self.index(INSERT).split(".")[0])
                    self.tag_add("sel", f'{current_index}.0', f'{current_index}.0 lineend')
                    sel_start = self.index(SEL_FIRST)
                    sel_end = self.index(SEL_LAST)

                # If selection
                if sel_start and sel_end:

                    # Get selection range
                    line_range = range(int(sel_start.split(".")[0]), int(sel_end.split(".")[0]) + 1)

                    # Replace data in lines
                    for line in line_range:
                        lr, text = self.get_line_text(line)

                        # Process the line
                        if text.strip():
                            text = ((self.get_indent(text) + (1 if indent else -1)) * tab_str) + text.strip()
                            self.replace(lr[0], lr[1], text)

                    # Extend selection range
                    self.tag_remove("sel", "sel.first", "sel.last")
                    self.tag_add("sel", f'{int(sel_start.split(".")[0])}.0', f'{sel_end} lineend')
                    self.recalc_lexer()
                    return "break"

            # Comment/Uncomment selection
            def block_comment(self, *_):
                sel_start = self.index(SEL_FIRST)
                sel_end = self.index(SEL_LAST)

                # If selection
                if sel_start and sel_end:

                    # Get selection range
                    line_range = range(int(sel_start.split(".")[0]), int(sel_end.split(".")[0])+1)
                    is_comment = True
                    indent_list = []
                    lowest_indent = 0

                    # First, check if any lines start with a comment decorator
                    for line in line_range:
                        lr, text = self.get_line_text(line)
                        indent_list.append(self.get_indent(text))

                        if not text.strip():
                            continue

                        # Check if text is already commented
                        if not text.strip().startswith("#"):
                            is_comment = False

                        # Get lowest indent
                        lowest_indent = min(indent_list)

                    # Second, replace data in lines
                    for line in line_range:
                        lr, text = self.get_line_text(line)

                        # Process the line
                        if is_comment:
                            if text.strip() and "#" in text:
                                s_text = text.split("#", 1)
                                text = (self.get_indent(s_text[0])*tab_str) + (self.get_indent(s_text[1])*tab_str) + s_text[1].strip()
                                self.replace(lr[0], lr[1], text)
                        else:
                            self.replace(lr[0], lr[1], f"{lowest_indent * tab_str}# {text[lowest_indent*len(tab_str):]}")

                    # Extend selection range
                    self.tag_remove("sel", "sel.first", "sel.last")
                    self.tag_add("sel", f'{int(sel_start.split(".")[0])}.0', f'{sel_end} lineend')


                # If index and no selection
                else:
                    current_line = self.index(INSERT)
                    line = int(current_line.split(".")[0])

                    lr, text = self.get_line_text(line)
                    is_comment = text.strip().startswith("#")
                    indent = self.get_indent(text)

                    # Process the line
                    if is_comment:
                        if text.strip() and "#" in text:
                            s_text = text.split("#", 1)
                            text = (self.get_indent(s_text[0]) * tab_str) + (self.get_indent(s_text[1]) * tab_str) + s_text[1].strip()
                            self.replace(lr[0], lr[1], text)
                    else:
                        if text.strip():
                            self.replace(lr[0], lr[1], f"{indent * tab_str}# {text[indent * len(tab_str):]}")
                    self.mark_set(INSERT, self.index(f"{line}.0+1l"))
                    self.see(INSERT)

                self.recalc_lexer()
                return "break"

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
                self.after(0, self.recalc_lexer)


                # Check for docstring
                indexes = self.get(self.index(f'{current_pos}-3c'), self.index(f'{current_pos}+3c'))
                in_docstring = indexes in ('""""""', "''''''")
                if in_docstring:
                    self.delete(self.index(f'{current_pos}-3c'), self.index(f'{current_pos}+3c'))
                    return 'break'

                if len(line_text) >= 4:
                    compare = line_text[-4:]
                    length = 4
                else:
                    compare = line_text
                    length = len(line_text)

                if compare == (' '*length) and line_text:
                    self.delete(f"{current_pos}-{length}c", current_pos)
                    return 'break'

                else:
                    next_pos = self.index(f"{current_pos}+1c")
                    left = line_text[-1:]
                    right = self.get(current_pos, next_pos)

                    # Delete symbol pairs
                    if left == '(' and right == ')':
                        self.delete(current_pos, next_pos)

                    elif left == '{' and right == '}':
                        self.delete(current_pos, next_pos)

                    elif left == '[' and right == ']':
                        self.delete(current_pos, next_pos)

                    elif left == "'" and right == "'":
                        self.delete(current_pos, next_pos)

                    elif left == '"' and right == '"':
                        self.delete(current_pos, next_pos)

                # Check if @ was deleted to hide menu
                def check_suggestions(*a):
                    line_num = int(current_pos.split('.')[0])
                    last_line = self.get(f"{line_num}.0", f"{line_num}.end")
                    text = last_line.rsplit(' ', 1)[-1].strip()
                    for k, v in ac.suggestions.items():
                        if text.startswith(k):
                            ac.update_results(text)
                            break
                    else:
                        ac.hide()
                self.after(0, check_suggestions)

            def in_docstring(self):
                current_pos = self.index(INSERT)
                after = self.tag_nextrange(f'Token.Literal.String.Doc', current_pos)
                before = self.tag_prevrange(f'Token.Literal.String.Doc', current_pos)

                final_range = None

                if after and self.is_within_range(current_pos, after[0], after[1]):
                    final_range = after

                elif before and self.is_within_range(current_pos, before[0], before[1]):
                    final_range = before

                return bool(final_range)

            # Move cursor right
            def move_cursor_right(self):
                current_pos = self.index(INSERT)
                new_pos = self.index(f"{current_pos}+1c")
                self.mark_set(INSERT, new_pos)

            # Surrounds text in l, r
            def surround_text(self, current_pos, sel_start, sel_end, l, r):
                selected_text = self.get(sel_start, sel_end)
                modified_text = l + selected_text + r
                self.delete(sel_start, sel_end)
                self.insert(sel_start, modified_text)
                self.mark_set(INSERT, self.index(f"{current_pos}+1c"))
                self.tag_remove("sel", "sel.first", "sel.last")
                line_break = '\n'
                self.tag_add("sel", self.index(f"{current_pos}+1c"), f"{sel_end}{'+1c' if line_break not in selected_text else ''}")
                self.recalc_lexer()

            def is_within_range(self, index, start, end):
                comparison_start = self.compare(index, ">=", start)
                comparison_end = self.compare(index, "<=", end)
                return comparison_start and comparison_end

            # Process individual keypress rules
            def process_keys(self, event):
                sel_start = self.index(SEL_FIRST)
                sel_end = self.index(SEL_LAST)
                current_pos = self.index(INSERT)
                right = self.get(current_pos, self.index(f"{current_pos}+1c"))
                left = self.get(self.index(f"{current_pos}-1c"), current_pos)

                line_num = int(current_pos.split('.')[0])
                last_line = self.get(f"{line_num}.0", f"{line_num}.end")


                # Hide auto-complete menu
                if event.keysym == "Escape":
                    if ac.visible:
                        ac.hide()

                # Show suggestions
                if event.keysym in ("at", "period"):
                    x, y = self.bbox(INSERT)[:2]
                    if event.keysym == "period":
                        x += 15
                    def show_panel(*a):
                        line_num = int(current_pos.split('.')[0])
                        last_line = self.get(f"{line_num}.0", f"{line_num}.end")
                        text = last_line.rsplit(' ', 1)[-1].strip()
                        if text in ac.suggestions:
                            ac.show(text, x, y)
                    if not ac.visible:
                        self.after(0, show_panel)
                else:
                    def get_text(*a):
                        line_num = int(current_pos.split('.')[0])
                        last_line = self.get(f"{line_num}.0", f"{line_num}.end")
                        text = last_line.rsplit(' ', 1)[-1].strip()
                        for k, v in ac.suggestions.items():
                            if text.startswith(k):
                                ac.update_results(text)
                                break
                    if ac.visible:
                        self.after(0, get_text)

                if event.keysym == 'parenleft':
                    ac.hide()


                # Replace selected parentheses and quote pairs
                if sel_start and sel_end:
                    if len(self.get(sel_start, sel_end)) == 1:
                        self.after(0, self.recalc_lexer)
                        get_text = self.get(sel_start, sel_end)
                        if (get_text in "'\"") and (event.keysym in ('quotedbl', 'quoteright')):

                            name = "Single" if get_text == "'" else "Double"
                            replace_with = '"' if event.keysym == 'quotedbl' else "'"
                            after = self.tag_nextrange(f'Token.Literal.String.{name}', current_pos)
                            before = self.tag_prevrange(f'Token.Literal.String.{name}', current_pos)

                            final_range = None

                            if after and (self.is_within_range(sel_start, after[0], after[1]) or self.is_within_range(sel_end, after[0], after[1])):
                                final_range = after

                            elif before and (self.is_within_range(sel_start, before[0], before[1]) or self.is_within_range(sel_end, before[0], before[1])):
                                final_range = before

                            if final_range:
                                start = self.get(final_range[0])
                                end = self.get(f'{final_range[1]}-1c')
                                if start == end:
                                    text = self.get(final_range[0], final_range[1])
                                    self.delete(final_range[0], final_range[1])
                                    self.insert(final_range[0], replace_with + text[1:-1] + replace_with)
                                    self.mark_set(INSERT, current_pos)
                                    return 'break'
                        elif sel_start == self.hl_pair[0] or sel_end == self.hl_pair[0]:
                            text = self.get(self.hl_pair[0], f"{self.hl_pair[1]}+1c")
                            if event.keysym == 'parenleft':
                                self.delete(self.hl_pair[0], f"{self.hl_pair[1]}+1c")
                                self.insert(self.hl_pair[0], f'({text[1:-1]})')
                                self.mark_set(INSERT, current_pos)
                                return 'break'
                            elif event.keysym == 'braceleft':
                                self.delete(self.hl_pair[0], f"{self.hl_pair[1]}+1c")
                                self.insert(self.hl_pair[0], f'{{{text[1:-1]}}}')
                                self.mark_set(INSERT, current_pos)
                                return 'break'
                            elif event.keysym == 'bracketleft':
                                self.delete(self.hl_pair[0], f"{self.hl_pair[1]}+1c")
                                self.insert(self.hl_pair[0], f'[{text[1:-1]}]')
                                self.mark_set(INSERT, current_pos)
                                return 'break'
                        elif sel_start == self.hl_pair[1] or sel_end == self.hl_pair[1]:
                            text = self.get(self.hl_pair[0], f"{self.hl_pair[1]}+1c")
                            if event.keysym == 'parenright':
                                self.delete(self.hl_pair[0], f"{self.hl_pair[1]}+1c")
                                self.insert(self.hl_pair[0], f'({text[1:-1]})')
                                self.mark_set(INSERT, current_pos)
                                return 'break'
                            elif event.keysym == 'braceright':
                                self.delete(self.hl_pair[0], f"{self.hl_pair[1]}+1c")
                                self.insert(self.hl_pair[0], f'{{{text[1:-1]}}}')
                                self.mark_set(INSERT, current_pos)
                                return 'break'
                            elif event.keysym == 'bracketright':
                                self.delete(self.hl_pair[0], f"{self.hl_pair[1]}+1c")
                                self.insert(self.hl_pair[0], f'[{text[1:-1]}]')
                                self.mark_set(INSERT, current_pos)
                                return 'break'


                # Toggle suggestions
                if event.keysym == "Tab" and ac.visible:
                    ac.click()
                    return "break"


                # Add docstring
                if self.in_docstring():
                    self.recalc_lexer()
                else:
                    if last_line.strip().startswith('""') and event.keysym == 'quotedbl':
                        current = self.get(f'{current_pos}-2c') + left
                        if current == '""':
                            self.insert(current_pos, '"""')
                            self.mark_set(INSERT, current_pos)
                            self.recalc_lexer()

                    elif last_line.strip().startswith("''") and event.keysym == 'quoteright':
                        current = self.get(f'{current_pos}-2c') + left
                        if current == "''":
                            self.insert(current_pos, "'''")
                            self.mark_set(INSERT, current_pos)
                            self.recalc_lexer()


                # Checks if symbol exists for inserting pairs
                def check_text(char, ex=''):
                    pattern = f'[^a-zA-Z0-9.{ex}]'
                    match = re.sub(pattern, '', char)
                    return not match


                # Press return with last indent level
                if event.keysym == 'Return':
                    if ac.visible:
                        ac.click()
                        return "break"

                    line_num = int(current_pos.split('.')[0])
                    if line_num > 0:
                        last_line = self.get(f"{line_num}.0", f"{line_num}.end")
                        indent = self.get_indent(last_line)

                        # Indent rules
                        test = last_line.strip()
                        if test.endswith(":"):
                            indent += 1

                        for kw in ['return', 'continue', 'break', 'yield', 'raise', 'pass']:
                            if test.startswith(f"{kw} ") or test.endswith(kw):
                                indent -= 1
                                break

                        if indent > 0:
                            self.after(0, lambda *_: self.insert(INSERT, tab_str*indent))
                        self.after(0, lambda *_: self.recalc_lexer())
                        return "Return"


                # Insert spaces instead of tab character and finish brackets/quotes

                # If selection
                if sel_start and sel_end and event.keysym == 'Tab':
                    self.block_indent(True)
                    return "break"


                # Outline selection in symbols
                elif sel_start and sel_end and event.keysym == 'parenleft':
                    self.surround_text(current_pos, sel_start, sel_end, '(', ')')
                    return "break"
                elif sel_start and sel_end and event.keysym == 'braceleft':
                    self.surround_text(current_pos, sel_start, sel_end, '{', '}')
                    return "break"
                elif sel_start and sel_end and event.keysym == 'bracketleft':
                    self.surround_text(current_pos, sel_start, sel_end, '[', ']')
                    return "break"
                elif sel_start and sel_end and event.keysym == 'quoteright':
                    self.surround_text(current_pos, sel_start, sel_end, "'", "'")
                    return "break"
                elif sel_start and sel_end and event.keysym == 'quotedbl':
                    self.surround_text(current_pos, sel_start, sel_end, '"', '"')
                    return "break"


                # Check if bidirectional contiguous symbol pairs match from the cursor
                def equal_symbols(cr, lr, rr):
                    line = current_pos.split('.')[0]
                    before = self.get(f"{line}.0", current_pos) + cr
                    after = self.get(current_pos, self.index(f"{line}.end"))
                    pattern = f'\\{lr}*?\\{rr}*?'
                    before_matches = ''.join(reversed([z for z in re.findall(pattern, before[::-1]) if z]))
                    after_matches = ''.join([z for z in re.findall(pattern, after) if z])
                    final = before_matches + after_matches
                    return final.count(lr) == final.count(rr)

                # Skip right if pressed
                if event.keysym == 'parenright' and (right == ')' and not equal_symbols(')', '(', ')')):
                    self.move_cursor_right()
                    return 'break'
                elif event.keysym == 'braceright' and (right == '}' and not equal_symbols('}', '{', '}')):
                    self.move_cursor_right()
                    return 'break'
                elif event.keysym == 'bracketright' and (right == ']' and not equal_symbols(']', '[', ']')):
                    self.move_cursor_right()
                    return 'break'
                elif event.keysym == 'quoteright' and right == "'":
                    self.move_cursor_right()
                    return 'break'
                elif event.keysym == 'quotedbl' and right == '"':
                    self.move_cursor_right()
                    return 'break'


                # Insert symbol pairs
                elif event.keysym == 'parenleft' and (check_text(right) and equal_symbols('()', '(', ')')):
                    self.insert(INSERT, "()")
                    self.mark_set(INSERT, self.index(f"{current_pos}+1c"))
                    return 'break'
                elif event.keysym == 'braceleft' and (check_text(right) and equal_symbols('{}', '{', '}')):
                    self.insert(INSERT, "{}")
                    self.mark_set(INSERT, self.index(f"{current_pos}+1c"))
                    return 'break'
                elif event.keysym == 'bracketleft' and (check_text(right) and equal_symbols('[]', '[', ']')):
                    self.insert(INSERT, "[]")
                    self.mark_set(INSERT, self.index(f"{current_pos}+1c"))
                    return 'break'
                elif event.keysym == 'quoteright' and (check_text(right, "'") and check_text(left, "'")):
                    self.insert(INSERT, "''")
                    self.mark_set(INSERT, self.index(f"{current_pos}+1c"))
                    return 'break'
                elif event.keysym == 'quotedbl' and (check_text(right, '"') and check_text(left, '"')):
                    self.insert(INSERT, '""')
                    self.mark_set(INSERT, self.index(f"{current_pos}+1c"))
                    return 'break'
                elif event.keysym == 'Tab':
                    self.insert(INSERT, tab_str)
                    return 'break'  # Prevent default behavior of the Tab key

            # Highlight find text
            def highlight_pattern(self, pattern, tag, start="1.0", end="end", regexp=False):
                start = self.index(start)
                end = self.index(end)
                self.mark_set("matchStart", start)
                self.mark_set("matchEnd", start)
                self.mark_set("searchLimit", end)

                count = IntVar()
                x = 0
                if tag == "highlight":
                    self.match_list = []
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
                        if tag == "highlight":
                            self.match_list = []
                        break

                    if x == 0 and tag == 'highlight':
                        new_search = search.get()
                        if new_search != self.last_search:
                            self.see(index)
                            self.match_list = []
                        self.last_search = new_search
                    if tag == 'highlight':
                        index = int(self.index("matchStart").split(".")[0])
                        if index not in self.match_list:
                            self.match_list.append(index)
                    x += 1

                    if not pattern:
                        if tag == "highlight":
                            self.match_list = []
                        break

                if tag != 'highlight':
                    return

                if search.has_focus or replace.has_focus or x > 0:
                    self.match_counter.configure(
                        text=f'{x} result(s)',
                        fg = text_color if x > 0 else faded_text
                    )
                    self.index_label.place_forget()
                else:
                    self.index_label.place(in_=search, relwidth=0.2, relx=0.795, rely=0, y=7)
                    self.match_counter.configure(text='')
                self._line_numbers.redraw()

        root.code_editor = HighlightText(
            root,
            color_scheme = style,
            font = f"Consolas {font_size}",
            linenums_theme = ('#3E3E63', background_color),
            scrollbar=Scrollbar
        )
        code_editor = root.code_editor
        code_editor.pack(fill="both", expand=True, pady=10)
        code_editor.config(autoseparator=False, maxundo=0, undo=False)
        code_editor.insert(END, ams_data)
        code_editor.config(autoseparator=True, maxundo=-1, undo=True)
        code_editor._line_numbers.config(borderwidth=0, highlightthickness=0)
        code_editor.config(spacing1=5, spacing3=5, wrap='word')

        # Highlight stuffies
        code_editor.tag_configure("highlight", foreground="black", background="#4CFF99")
        code_editor.tag_configure("error", background=error_bg)
        code_editor.tag_configure("parentheses", background="#34344C", underline=True, underlinefg="yellow") # 2D2D42


        # Configure replace box
        class ReplaceBox(Entry):
            def __init__(self, master=None, placeholder="PLACEHOLDER", color=faded_text):
                super().__init__(master)

                self.placeholder = placeholder
                self.placeholder_color = color
                self.default_fg_color = text_color
                self.has_focus = False
                self.visible = False
                self.last_index = 0
                self.animating = False

                self.bind("<FocusIn>", self.foc_in)
                self.bind("<FocusOut>", self.foc_out)
                self.bind("<Control-BackSpace>", self.ctrl_bs)
                self.bind('<Escape>', lambda *_: self.toggle_focus(False))
                self.bind('<KeyPress>', self.process_keys)
                self.bind("<Control-h>", lambda *_: self.toggle_focus(False))
                self.bind('<Shift-Return>', lambda *_: trigger_replace())

                self.put_placeholder()

            def toggle_focus(self, fs=True, r=0, anim=True):
                global replace_shown

                def reset_animate(*a):
                    self.animating = False

                if self.animating:
                    return

                self.animating = True

                def animate(start, end, item):
                    max_frames = 12
                    def move(frame):
                        if frame <= max_frames:
                            new_y = start + ((frame / (max_frames)) * end)
                            item.place_configure(y=new_y)
                            root.after(10, lambda *_: move(frame + 1))

                    root.after(10, lambda *_: move(1))

                if r == 0:
                    replace_shown = self.visible or fs
                    for frame in open_frames.values():
                        if str(frame.replace) != str(self):
                            frame.replace.toggle_focus(replace_shown, r=1, anim=False)

                if self.visible or not fs:
                    if anim:
                        animate(-45, 40, replace_frame)
                        animate(-85, 40, search_frame)
                        self.after(130, replace_frame.place_forget)
                        self.after(200, reset_animate)
                    else:
                        replace_frame.place_forget()
                        search_frame.place_configure(y=-45)
                        reset_animate()
                    code_editor.focus_force()
                    code_editor.see(code_editor.index(INSERT))
                    self.visible = False
                else:
                    replace_frame.place(rely=1, y=(-5 if anim else -45), relwidth=1, height=50)
                    if anim:
                        animate(-5, -40, replace_frame)
                        animate(-45, -40, search_frame)
                        self.after(200, reset_animate)
                    else:
                        search_frame.place_configure(y=-85)
                        reset_animate()

                    if not search.has_focus:
                        root.focus_force()
                    self.visible = True
                return 'break'

            def see_index(self, index):
                code_editor.see(f"{index}.0")
                self.last_index = index
                search.last_index = index
                current_line = index
                pattern_text = search.get()
                replace_text = self.get()

                if replace_text in ('replace with...', ''):
                    return

                start = f"{current_line}.0"
                end = f"{current_line}.end"
                pos = code_editor.search(pattern_text, start, stopindex=end, nocase=True)

                if pos:
                    line_start = code_editor.index(f"{pos.split('.')[0]}.0")
                    line_end = code_editor.index(f"{line_start} lineend")
                    line = code_editor.get(line_start, line_end)
                    match = re.search(pattern_text, line, flags=re.IGNORECASE)

                    if match:
                        match_start = line_start + f"+{match.start()}c"
                        match_end = line_start + f"+{match.end()}c"
                        code_editor.delete(match_start, match_end)
                        code_editor.insert(match_start, replace_text)

            def iterate_selection(self, forward=True):
                if len(code_editor.match_list) > 1:
                    if forward:
                        for i in code_editor.match_list:
                            if i > self.last_index:
                                self.see_index(i)
                                break
                        else:
                            self.see_index(code_editor.match_list[0])

                    else:
                        for i in reversed(code_editor.match_list):
                            if i < self.last_index:
                                self.see_index(i)
                                break
                        else:
                            self.see_index(code_editor.match_list[-1])

                elif code_editor.match_list:
                    self.see_index(code_editor.match_list[0])
                code_editor.after(1, code_editor._line_numbers.redraw)
                code_editor.after(1, code_editor.recalc_lexer)

            def replace_all(self):
                replace_text = self.get()
                search_text = search.get()

                if replace_text in ('replace with...', ''):
                    return

                for x in code_editor.match_list:
                    for y in range(0, code_editor.get_line_text(x)[-1].lower().count(search_text.lower())):
                        self.see_index(x)

                update_search(search_text)
                code_editor.after(1, code_editor._line_numbers.redraw)
                code_editor.after(1, code_editor.recalc_lexer)

            def process_keys(self, event):
                if event.keysym == "Return":
                    if event.state == 33:
                        self.iterate_selection(False)
                    else:
                        self.iterate_selection(True)

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
        class HoverButton(Button):

            def click_func(self, *a):
                self.config(image=self.background_click)
                self.function()
                self.after(100, self.on_enter)

            def on_enter(self, *a):
                self.config(image=self.background_hover)

            def on_leave(self, *a):
                self.config(image=self.background_image)

            def __init__(self, button_id, click_func, **args):
                super().__init__(**args)
                self.master = root
                self.id = button_id
                self.background_image = PhotoImage(file=os.path.join(data['gui_assets'], f'{self.id}.png'))
                self.background_hover = PhotoImage(file=os.path.join(data['gui_assets'], f'{self.id}_hover.png'))
                self.background_click = PhotoImage(file=os.path.join(data['gui_assets'], f'{self.id}_click.png'))
                self.function = click_func
                self['image'] = self.background_image

                # Import the image using PhotoImage function
                self.config(
                    command=self.click_func,
                    borderwidth=5,
                    relief=SUNKEN,
                    foreground=frame_background,
                    background=frame_background,
                    highlightthickness=0,
                    bd=0,
                    activebackground=frame_background
                )

                # Bind hover events
                self.bind('<Enter>', self.on_enter)
                self.bind('<Leave>', self.on_leave)

        replace_frame = Frame(root, height=1)
        replace_frame.configure(bg=frame_background, borderwidth=0, highlightthickness=0)
        root.replace = ReplaceBox(replace_frame, placeholder='replace with...')
        replace = root.replace
        replace.pack(fill=BOTH, expand=True, padx=(60, 5), pady=(0, 10), side=BOTTOM, ipady=0, anchor='s')
        replace.bind('<Tab>', lambda *_: root.after(0, lambda *_: search.focus_force()))
        replace.configure(
            bg = frame_background,
            borderwidth = 0,
            highlightthickness = 0,
            selectforeground = convert_color((0.75, 0.75, 1))['hex'],
            selectbackground = convert_color((0.2, 0.2, 0.4))['hex'],
            insertwidth = 3,
            insertbackground = convert_color((0.55, 0.55, 1, 1))['hex'],
            font = f"Consolas {font_size}",
        )

        # Replace All Button
        replace_button = HoverButton('replace_button', click_func=replace.replace_all)
        replace_button.config(anchor='se')
        replace_button.place(in_=replace, relwidth=0.2, relx=0.798, x=-2, y=-4)

        def trigger_replace(*a):
            if replace.visible and replace.get() and search.get():
                replace_button.invoke()
                root.after(100, replace_button.on_leave)
                return "break"

        root.bind('<Control-h>', lambda *_: replace.toggle_focus())
        if replace_shown:
            replace.toggle_focus(True, r=1, anim=False)


        def update_search(search_text=None):
            if not search_text:
                search_text = search.get()
            search.last_index = 0
            code_editor.content_changed = False
            sel_start = code_editor.index(SEL_FIRST)
            sel_end = code_editor.index(SEL_LAST)
            code_editor.tag_remove("highlight", "1.0", "end")
            if sel_start and sel_end:
                code_editor.highlight_pattern(search.get(), "highlight", start=sel_start, end=sel_end, regexp=False)
            else:
                code_editor.highlight_pattern(search.get(), "highlight", regexp=False)
            code_editor.last_search = search_text
            code_editor._line_numbers.redraw()

        def highlight_search():
            global close_window
            if close_window:
                return

            if code_editor._vs.last_scrolled < 4:
                code_editor._vs.last_scrolled += 1
                if code_editor._vs.last_scrolled == 4:
                    code_editor._vs.fade_out()

            search_text = search.get()
            if code_editor.last_search != search_text or code_editor.content_changed:
                update_search(search_text)

            root.after(250, highlight_search)
        highlight_search()

        # Search icon
        if not color_search:
            color_search = ImageTk.PhotoImage(Image.open(os.path.join(data['gui_assets'], 'color-search.png')))
        search_icon = Label(image=color_search, bg=frame_background)
        search_icon.place(anchor='nw', in_=search, x=-47, y=3.5)
        search_frame.tkraise(code_editor)
        search_frame.tkraise(code_editor._vs)

        # Auto-complete widget
        class AutoComplete(Frame):
            def __init__(self):
                super().__init__()
                self.background = "#0C0C1F"
                self.configure(height=100, width=70, bg=self.background)
                self.button_list = []
                self.last_matches = []
                self.suggestions = data['suggestions']
                self.visible = False
                self.max_size = 5
                self.add_buttons()

            def update_buttons(self, matches):
                for x, b in enumerate(self.button_list, 0):
                    visible = b.winfo_ismapped()
                    try:
                        item = matches[x]
                        b.config(text=item, command=functools.partial(self.click_func, item))
                        if not visible:
                            b.grid(sticky="w")
                    except IndexError:
                        if visible:
                            b.grid_remove()

            def add_buttons(self):
                for item in range(self.max_size):
                    button = Button(self, text=item, font=f"Consolas {font_size} italic", background=self.background)
                    button.config(
                        command = functools.partial(self.click_func, item),
                        borderwidth = 5,
                        relief = SUNKEN,
                        foreground = text_color,
                        highlightthickness = 0,
                        bd = 0,
                        activebackground = "#AAAAFF",
                        width=18,
                        anchor='w',
                        padx=10,
                        pady=5
                    )
                    self.button_list.append(button)

            def show(self, start, x, y):
                self.last_matches = []
                self.visible = True
                self.update_results(start)
                self.place(in_=code_editor, x=x-13, y=y+(code_editor.font_size*2.3))

            def hide(self, *a):
                self.place_forget()
                self.visible = False

            def update_results(self, text):
                matches = None
                if text == '@':
                    matches = ["@player.on_alias", "@player.on_join", "@player.on_leave", "@server.on_loop", "@server.on_start"]
                else:
                    for k, v in self.suggestions.items():
                        if text.startswith(k):

                            # Check tags
                            if k == '@':
                                tag = text[1:]
                            else:
                                tag = text[len(k + '.')-1:]

                            # Get list of matches/partial matches
                            matches = []
                            for x in self.suggestions[k]:
                                if tag in x:
                                    matches.append((x, 1))
                                    continue

                                else:
                                    try:
                                        tag_index = x.index(tag)
                                    except ValueError:
                                        tag_index = 0

                                    sml = similarity(tag.lower(), x.lower()[tag_index:tag_index + len(tag)])
                                    if sml > 0.7:
                                        # print(tag.lower(), x.lower()[tag_index:tag_index + len(tag)], x, sml)
                                        matches.append((x, sml))

                            matches = sorted([x[0] for x in matches], key=lambda x: x[1], reverse=True)


                            # matches = [x for x in self.suggestions[k] if tag in x or similarity(tag.lower(), x.lower()[len(tag):]) > 0.5][:self.max_size]

                if not matches:
                    self.hide()
                if matches != self.last_matches:
                    self.update_buttons(matches)
                self.last_matches = matches

            def iterate_selection(self, forward=True):
                if self.visible:
                    active_x = -1
                    if forward:
                        for x, b in enumerate(ac.button_list, 0):
                            if b['state'] == "active":
                                active_x = x
                                b['state'] = "normal"
                                break

                        for x, b in enumerate(ac.button_list, 0):
                            if x > active_x:
                                b['state'] = "active"
                                break
                        else:
                            ac.button_list[0]['state'] = "active"

                    else:
                        for x, b in enumerate(reversed(ac.button_list), 0):
                            if b['state'] == "active":
                                active_x = x
                                b['state'] = "normal"
                                break

                        for x, b in enumerate(reversed(ac.button_list), 0):
                            if x > active_x:
                                b['state'] = "active"
                                break
                        else:
                            ac.button_list[-1]['state'] = "active"

            def click(self, *a):
                active_x = -1

                for b in self.button_list:
                    if b['state'] == "active":
                        b.invoke()
                        break
                else:
                    self.button_list[0].invoke()

            def click_func(self, val):
                self.hide()

                line_num = int(code_editor.index(INSERT).split('.')[0])

                if val.startswith("@"):
                    code_editor.delete(f'{line_num}.0', f'{line_num}.0 lineend')

                    if val == "@player.on_alias":
                        code_editor.insert(f'{line_num}.0', f"@player.on_alias(player, command='', arguments={{}}, permission='op', description=''):")

                    elif val == "@player.on_message":
                        code_editor.insert(f'{line_num}.0', f"@player.on_message(player, message):")

                    elif val == "@player.on_join":
                        code_editor.insert(f'{line_num}.0', f"@player.on_join(player, data):")

                    elif val == "@player.on_leave":
                        code_editor.insert(f'{line_num}.0', f"@player.on_leave(player, data):")

                    elif val == "@player.on_death":
                        code_editor.insert(f'{line_num}.0', f"@player.on_death(player, enemy, message):")

                    elif val == "@server.on_loop":
                        code_editor.insert(f'{line_num}.0', f"@server.on_loop(interval=1, unit='minute'):")

                    elif val == "@server.on_start":
                        code_editor.insert(f'{line_num}.0', f"@server.on_start(data, delay=0):")

                    elif val == "@server.on_stop":
                        code_editor.insert(f'{line_num}.0', f"@server.on_stop(data, delay=0):")

                    def newline(*a):
                        code_editor.insert(code_editor.index(INSERT), f'\n{tab_str}')
                        code_editor.recalc_lexer()
                    code_editor.after(1, newline)

                else:
                    cursor_pos = code_editor.index(INSERT)
                    last_line, delete = code_editor.get(f"{line_num}.0", cursor_pos).rsplit('.')
                    code_editor.delete(f'{cursor_pos}-{len(delete)}c', f'{line_num}.{len(delete)} lineend')
                    code_editor.insert(cursor_pos, val)

                    def newline(*a):
                        if val.endswith('()'):
                            code_editor.mark_set(INSERT, f'{code_editor.index(INSERT)}-1c')
                        code_editor.recalc_lexer()
                    code_editor.after(0, newline)

        root.ac = AutoComplete()
        ac = root.ac
        window.root.bind("<<NotebookTabChanged>>", ac.hide, add=True)

        # Add tab to window
        window.after(0, lambda *_: window.root.add(root, text=os.path.basename(path)))
        window.after(0, lambda *_: window.root.select(root))
        open_frames[os.path.basename(path)] = root


wlist = None
def edit_script(script_path: str, data: dict, *args):
    global suggestions, process, wlist

    if script_path:
        if suggestions:
            data['suggestions'] = suggestions
        else:
            data['suggestions'] = {
                '@': data['script_obj'].valid_events,
                'server.': iter_attr(data['server_script_obj']),
                'acl.': iter_attr(data['server_obj'].acl),
                'addon.': iter_attr(data['server_obj'].addon),
                'backup.': iter_attr(data['server_obj'].backup),
                'amscript.': iter_attr(data['server_obj'].script_manager)
            }

        try:
            running = process.is_alive()
        except:
            running = False

        if not running:
            mgr = multiprocessing.Manager()
            wlist = mgr.Value('window_list', [])
            process = multiprocessing.Process(target=functools.partial(create_root, data), args=(wlist, 'window_list'), daemon=False)
            process.start()

        wlist.value = script_path


if os.name == 'nt':
    from ctypes import windll, c_int64

    # Calculate screen width and disable DPI scaling if bigger than a certain resolution
    width = windll.user32.GetSystemMetrics(0)
    scale = windll.shcore.GetScaleFactorForDevice(0) / 100
    if (width * scale) < 2000:
        windll.user32.SetProcessDpiAwarenessContext(c_int64(-4))

    font_size = 14



if __name__ == '__main__':
    import constants
    import amscript

    from amscript import ScriptManager, ServerScriptObject, PlayerScriptObject
    from svrmgr import ServerObject
    server_obj = ServerObject('test')
    while not (server_obj.addon and server_obj.acl and server_obj.backup and server_obj.script_manager):
        time.sleep(0.2)

    # DELETE ABOVE


    data_dict = {
        'app_title': constants.app_title,
        'gui_assets': constants.gui_assets,
        'background_color': constants.background_color,
        'script_obj': amscript.ScriptObject(),
        'server_obj': server_obj,
        'suggestions': {}
    }

    server = ServerScriptObject(server_obj)
    data_dict['suggestions']['@'] = data_dict['script_obj'].valid_events
    data_dict['suggestions']['server.'] = iter_attr(server)
    data_dict['suggestions']['acl.'] = iter_attr(server_obj.acl)
    data_dict['suggestions']['addon.'] = iter_attr(server_obj.addon)
    data_dict['suggestions']['backup.'] = iter_attr(server_obj.backup)
    data_dict['suggestions']['amscript.'] = iter_attr(server_obj.script_manager)

    path = r"C:\Users\macarooni machine\AppData\Roaming\.auto-mcs\Tools\amscript"
    class Test():
        def __init__(self):
            self.value = os.path.join(path, 'test2.ams')
            import threading
            def test():
                self.value = os.path.join(path, 'custom-waypoints.ams')
            threading.Timer(1, test).start()
            def test():
                self.value = os.path.join(path, 'test.ams')
            threading.Timer(2, test).start()
            def test():
                self.value = os.path.join(path, 'test2.ams')
            threading.Timer(3, test).start()
    create_root(data_dict, Test())
