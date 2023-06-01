from tkinter import Tk, Text, Entry, Label, Scrollbar, RIGHT, BOTTOM, X, Y, BOTH, DISABLED, END, IntVar, Frame, PhotoImage
from PIL import ImageTk, Image
import multiprocessing
import functools
import os


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
            x = f"0{x}" if len(x) == 1 else x
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

    # Get text
    crash_data = ''
    if path:

        with open(path, 'r') as f:
            crash_data = f.read()


        # Init Tk window
        background_color = convert_color(brighten_color(data['background_color'], -0.1))['hex']
        text_color = convert_color((0.6, 0.6, 1))['hex']
        file_icon = os.path.join(data['gui_assets'], "big-icon.png")
        min_size = (950, 600)

        root = Tk()
        root.geometry(f"{min_size[0]}x{min_size[1]}")
        root.minsize(width=min_size[0], height=min_size[1])
        root.title(f'{data["app_title"]} - {server_name} ({os.path.basename(path)})')
        img = PhotoImage(file=file_icon)
        root.tk.call('wm', 'iconphoto', root._w, img)
        root.configure(bg=background_color)
        root.close = False


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

        search_frame = Frame(root, height=1)
        search_frame.pack(fill=X, side=BOTTOM)
        search_frame.configure(bg=background_color, borderwidth=0, highlightthickness=0)
        search = EntryPlaceholder(search_frame, placeholder='search for text')
        search.pack(fill=BOTH, expand=True, padx=(55, 5), pady=(10, 3), side=BOTTOM, ipady=5)
        search.configure(
            bg = background_color,
            borderwidth = 0,
            highlightthickness=0,
            selectforeground = convert_color((0.75, 0.75, 1))['hex'],
            selectbackground = convert_color((0.2, 0.2, 0.4))['hex'],
            insertwidth = 3,
            insertbackground = convert_color((0.55, 0.55, 1, 1))['hex'],
            font = "Courier 16 bold",
        )

        # Bind CTRL-F to focus search box
        root.bind('<Control-f>', lambda x: search.focus_force())


        # Add scrollbar
        scrollbar = Scrollbar(root)
        scrollbar.pack(side=RIGHT, fill=Y)


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
                    font = "Courier 14 bold"
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
                        index = self.search(pattern, "matchEnd", "searchLimit", count=count, regexp=regexp)
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
                    text_info.match_counter.configure(
                        text=f'{x} result(s)',
                        fg = text_color if x > 0 else convert_color((0.3, 0.3, 0.65))['hex']
                    )
                else:
                    text_info.match_counter.configure(text='')

        text_info = HighlightText(root, yscrollcommand=scrollbar.set)
        text_info.pack(fill=BOTH, expand=True, padx=(10, 5), pady=(5, 5))
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
            font = "Courier 14",
            state = DISABLED,
            spacing1 = 10
        )

        # Highlight stuffies
        text_info.tag_configure("highlight", foreground="white", background=convert_color((0.2, 0.2, 0.4))['hex'])


        def highlight_search():
            if root.close:
                return

            if root.state() == "normal":
                search_text = search.get()
                if text_info.last_search != search_text:
                    text_info.tag_remove("highlight", "1.0", "end")
                    text_info.highlight_pattern(search.get(), "highlight", regexp=False)

                root.after(250, highlight_search)
        highlight_search()


        # Search icon
        icon = ImageTk.PhotoImage(Image.open(os.path.join(data['gui_assets'], 'color-search.png')))
        search_icon = Label(image=icon, bg=background_color)
        search_icon.place(anchor='nw', in_=search, x=-45, y=0)

        scrollbar.config(command=text_info.yview)

        def on_closing():
            root.close = True
            root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_closing)

        root.mainloop()



def open_log(server_name: str, path: str, data: dict):
    if path:
        process = multiprocessing.Process(target=functools.partial(launch_window, server_name, path, data))
        process.start()
