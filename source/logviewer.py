from tkinter import Tk, Text, Scrollbar, RIGHT, Y, BOTH, DISABLED, END
import constants
import os


# Opens a crash log in a read-only text editor
def open_log(server_name: str, path: str):

    # Get text
    crash_data = ''
    if path:
        with open(path, 'r') as f:
            crash_data = f.read()

        # Init Tk window
        background_color = constants.convert_color(constants.brighten_color(constants.background_color, -0.1))['hex']
        text_color = constants.convert_color((0.6, 0.6, 1))['hex']
        file_icon = os.path.join(constants.gui_assets, "small-icon.ico")
        min_size = (800, 500)

        root = Tk()
        root.geometry(f"{min_size[0]}x{min_size[1]}")
        root.minsize(width=min_size[0], height=min_size[1])
        root.title(f'{constants.app_title} - {server_name} ({os.path.basename(path)})')
        root.iconbitmap(file_icon)
        root.configure(bg=background_color)

        # Add scrollbar
        scrollbar = Scrollbar(root)
        scrollbar.pack(side=RIGHT, fill=Y)

        text_info = Text(root, yscrollcommand=scrollbar.set)
        text_info.pack(fill=BOTH, expand=True, padx=(10, 5), pady=(5, 5))
        text_info.insert(END, crash_data)
        text_info.configure(
            fg = text_color,
            bg = background_color,
            borderwidth = 0,
            selectforeground = text_color,
            selectbackground = constants.convert_color((0.2, 0.2, 0.4))['hex'],
            insertwidth = 3,
            insertbackground = constants.convert_color((0.55, 0.55, 1, 1))['hex'],
            font = "Courier 15",
            state = DISABLED,
            spacing1 = 10

        )

        # configuring the scrollbar
        scrollbar.config(command=text_info.yview)

        root.mainloop()


open_log('test', r"C:\Users\macarooni machine\AppData\Roaming\.auto-mcs\Servers\Spigot Test\crash-reports\crash-2022-03-26_18.00.43-server.txt")
