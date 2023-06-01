from tkinter import Tk, Text, Entry, Label, Scrollbar, RIGHT, BOTTOM, X, Y, BOTH, DISABLED, END, IntVar, Frame, PhotoImage
from PIL import ImageTk, Image
import multiprocessing
import constants
import functools
import os



# Opens a crash log in a read-only text editor
def launch_window(server_name: str, path: str, assets: str):

    # Get text
    crash_data = ''
    if path:

        with open(path, 'r') as f:
            crash_data = f.read()


        # Init Tk window
        background_color = constants.convert_color(constants.brighten_color(constants.background_color, -0.1))['hex']
        text_color = constants.convert_color((0.6, 0.6, 1))['hex']
        file_icon = os.path.join(assets, "big-icon.png")
        min_size = (950, 600)

        root = Tk()
        root.geometry(f"{min_size[0]}x{min_size[1]}")
        root.minsize(width=min_size[0], height=min_size[1])
        root.title(f'{constants.app_title} - {server_name} ({os.path.basename(path)})')
        img = PhotoImage(file=file_icon)
        root.tk.call('wm', 'iconphoto', root._w, img)
        root.configure(bg=background_color)
        root.close = False


        # Configure search box
        class EntryPlaceholder(Entry):
            def __init__(self, master=None, placeholder="PLACEHOLDER", color=constants.convert_color((0.3, 0.3, 0.65))['hex']):
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
            selectforeground = constants.convert_color((0.75, 0.75, 1))['hex'],
            selectbackground = constants.convert_color((0.2, 0.2, 0.4))['hex'],
            insertwidth = 3,
            insertbackground = constants.convert_color((0.55, 0.55, 1, 1))['hex'],
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
                    fg = constants.convert_color((0.3, 0.3, 0.65))['hex'],
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
                        fg = text_color if x > 0 else constants.convert_color((0.3, 0.3, 0.65))['hex']
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
            inactiveselectbackground = constants.convert_color((0.2, 0.2, 0.4))['hex'],
            selectforeground = constants.convert_color((0.75, 0.75, 1))['hex'],
            selectbackground = constants.convert_color((0.2, 0.2, 0.4))['hex'],
            insertwidth = 3,
            insertbackground = constants.convert_color((0.55, 0.55, 1, 1))['hex'],
            font = "Courier 14",
            state = DISABLED,
            spacing1 = 10
        )

        # Highlight stuffies
        text_info.tag_configure("highlight", foreground="white", background=constants.convert_color((0.2, 0.2, 0.4))['hex'])


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
        icon = ImageTk.PhotoImage(Image.open(os.path.join(assets, 'color-search.png')))
        search_icon = Label(image=icon, bg=background_color)
        search_icon.place(anchor='nw', in_=search, x=-45, rely=0.1)

        scrollbar.config(command=text_info.yview)

        def on_closing():
            root.close = True
            root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_closing)

        root.mainloop()



def open_log(server_name: str, path: str):
    if path:
        process = multiprocessing.Process(target=functools.partial(launch_window, server_name, path, constants.gui_assets))
        process.start()
