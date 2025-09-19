from tkinter import Tk, Text, Entry, Label, Canvas, RIGHT, BOTTOM, X, Y, BOTH, DISABLED, END, IntVar, Frame, PhotoImage, INSERT
from PIL import ImageTk, Image
import multiprocessing
import functools
import os


default_font_size = 15
control = 'Control'
font_name = 'Consolas'


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


# Opens a crash log in a read-only text editor
def launch_window(server_name: str, path: str, data: dict):
    global default_font_size, font_name, control

    # Increase font size on macOS
    if data['os_name'] == 'macos':
        default_font_size += 5
        control = 'Command'
        font_name = 'Menlo'

    # Get text
    crash_data = ''
    if path:
        if os.path.exists(path):
            with open(path, 'r') as f:
                crash_data = f.read()
        else:
            crash_data = path
            path = 'telepath'


        # Init Tk window
        background_color = convert_color(brighten_color(data['background_color'], -0.1))['hex']
        text_color = convert_color((0.6, 0.6, 1))['hex']
        file_icon = os.path.join(data['gui_assets'], "amscript-icon.png")
        min_size = (950, 600)

        root = Tk()
        width = root.winfo_screenwidth()
        height = root.winfo_screenheight()
        x = int((width / 2) - (min_size[0] / 2))
        y = int((height / 2) - (min_size[1] / 2)) - 15
        root.geometry(f"{min_size[0]}x{min_size[1]}+{x}+{y}")
        root.minsize(width=min_size[0], height=min_size[1])
        root.title(f'{data["app_title"]} - {server_name} ({os.path.basename(path)})')
        img = PhotoImage(file=file_icon)
        root.tk.call('wm', 'iconphoto', root._w, img)
        root.configure(bg=background_color)
        root.close = False


        # Configure search box
        class SearchBox(Entry):
            def __init__(self, master=None, placeholder="PLACEHOLDER", color='#444477'):
                super().__init__(master)

                self.placeholder = placeholder
                self.placeholder_color = color
                self.default_fg_color = text_color
                self.has_focus = False

                self.bind("<FocusIn>", self.foc_in)
                self.bind("<FocusOut>", self.foc_out)
                self.bind(f"<{control}-BackSpace>", self.ctrl_bs)

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
        search = SearchBox(search_frame, placeholder=data['translate']('search for text'))
        search.pack(fill=BOTH, expand=True, padx=(60, 5), pady=(0, 10), side=BOTTOM, ipady=0, anchor='s')
        search.configure(
            bg = background_color,
            borderwidth = 0,
            highlightthickness = 0,
            selectforeground = convert_color((0.75, 0.75, 1))['hex'],
            selectbackground = convert_color((0.2, 0.2, 0.4))['hex'],
            insertwidth = 3,
            insertbackground = convert_color((0.55, 0.55, 1, 1))['hex'],
            font = f"{font_name} {default_font_size + 2} bold",
        )

        # Bind CTRL-F to focus search box
        root.bind(f"<{control}-f>", lambda x: search.focus_force())


        # Add scrollbar
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
                    color = convert_color((0.6-(frame/(max_frames*2.3)), 0.6-(frame/(max_frames*2.3)), 1-(frame/(max_frames*1.4))))['hex']
                    self.itemconfig('slider', fill=color, outline=color)
                    if frame <= max_frames:
                        root.after(10, lambda *_: reduce_opacity(frame+1))
                root.after(10, lambda *_: reduce_opacity(1))

        scrollbar = Scrollbar(root, width=7)
        scrollbar.pack(side=RIGHT, fill=Y, padx=(6, 0))


        # Configure background text
        class HighlightText(Text):

            def __init__(self, *args, **kwargs):
                Text.__init__(self, *args, **kwargs)
                self.last_search = ""
                self.match_counter = Label(justify='right', anchor='se')
                self.match_counter.place(in_=search, relwidth=0.2, relx=0.8, rely=0.2)
                self.match_counter.configure(
                    fg = convert_color((0.3, 0.3, 0.65))['hex'],
                    bg = background_color,
                    borderwidth = 0,
                    font = f"{font_name} {default_font_size} bold"
                )

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
                        new_search = search.get()
                        if new_search != self.last_search:
                            self.see(index)
                        self.last_search = new_search
                    x += 1

                if search.has_focus or x > 0:
                    text_info.match_counter.configure(
                        text=f'{x} result(s)',
                        fg = text_color if x > 0 else '#444477'
                    )
                else:
                    text_info.match_counter.configure(text='')

        text_info = HighlightText(root, yscrollcommand=scrollbar.set)
        text_info.pack(fill=BOTH, expand=True, padx=(10, 0), pady=(5, 5))
        text_info.insert(END, crash_data)
        text_info.configure(
            fg = text_color,
            bg = background_color,
            borderwidth = 0,
            highlightthickness = 0,
            inactiveselectbackground = convert_color((0.2, 0.2, 0.4))['hex'],
            selectforeground = convert_color((0.75, 0.75, 1))['hex'],
            selectbackground = convert_color((0.2, 0.2, 0.4))['hex'],
            insertwidth = 3,
            insertbackground = convert_color((0.55, 0.55, 1, 1))['hex'],
            font = f"{font_name} {default_font_size}",
            state = DISABLED,
            spacing1 = 10
        )

        # Highlight stuffies
        text_info.tag_configure("highlight", foreground="black", background="#4CFF99")


        def highlight_search():
            if root.close:
                return

            if scrollbar.last_scrolled < 4:
                scrollbar.last_scrolled += 1
                if scrollbar.last_scrolled == 4:
                    scrollbar.fade_out()

            search_text = search.get()
            if text_info.last_search != search_text:
                text_info.tag_remove("highlight", "1.0", "end")
                text_info.highlight_pattern(search.get(), "highlight", regexp=False)

            root.after(250, highlight_search)
        highlight_search()


        # Search icon
        icon = ImageTk.PhotoImage(Image.open(os.path.join(data['gui_assets'], 'color-search.png')))
        search_icon = Label(image=icon, bg=background_color)
        search_icon.place(anchor='nw', in_=search, x=-50, y=-2)

        scrollbar.command = text_info.yview


        # When window is closed
        def on_closing():
            root.close = True
            root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_closing)

        root.mainloop()



def open_log(server_name: str, path: str, data: dict, *args):
    if path:
        process = multiprocessing.Process(target=functools.partial(launch_window, server_name, path, data), daemon=True)
        process.start()
        data['sub_processes'].append(process.pid)




if os.name == 'nt':
    from ctypes import windll, c_int64

    # Calculate screen width and disable DPI scaling if bigger than a certain resolution
    try:
        width = windll.user32.GetSystemMetrics(0)
        scale = windll.shcore.GetScaleFactorForDevice(0) / 100
        if (width * scale) < 2000:
            windll.user32.SetProcessDpiAwarenessContext(c_int64(-4))
    except:
        pass  # print('Error: failed to set DPI context')



# if __name__ == '__main__':
#     import constants
#
#     data_dict = {
#         'app_title': constants.app_title,
#         'gui_assets': constants.gui_assets,
#         'background_color': constants.background_color,
#         'os_name': 'macos'
#     }
#     path = '/Users/kaleb/Library/Application Support/auto-mcs/Logs/ame-fatal_20-27-33_2-18-24.log'
#     launch_window('test', path, data_dict)
