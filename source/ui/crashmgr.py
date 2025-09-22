import functools
import os

from source.core.constants import paths
from source.core import constants



# Import Tk if not headless
if not constants.headless:
    from tkinter import Tk, Entry, SUNKEN, Canvas, PhotoImage, CENTER, END
    from PIL import ImageTk, Image
    import simpleaudio as sa

    from source.ui import logviewer


    # Remove border on macOS buttons
    if constants.os_name == 'macos':
        import tkmacosx
        class Button(tkmacosx.Button):
            def __init__(self, **args):
                super().__init__(**args)
                self.config(borderless=1, focusthickness=0, state='active')
    else:
        from tkinter import Button


# Opens crash log
def open_log(log_path):

    # Don't attempt to open a log that doesn't exist
    if log_path:
        if not os.path.exists(log_path):
            return

    data_dict = {
        'app_title': constants.app_title,
        'gui_assets': paths.ui_assets,
        'background_color': constants.background_color,
        'sub_processes': constants.sub_processes,
        'os_name': constants.os_name,
        'translate': constants.translate
    }
    logviewer.open_log('Crash Report', log_path, data_dict)


# Launches Tk window to provide crash information
def launch_window(exc_code, log_path):

    # Override if headless
    if constants.headless:
        print(f'(!)  Uh oh, {constants.app_title} has crashed:  {exc_code}\n\n> Crash log:  {log_path}')
        return


    # Init Tk window
    crash_sound = sa.WaveObject.from_wave_file(os.path.join(paths.ui_assets, 'sounds', 'crash.wav'))
    background_color = constants.convert_color(constants.background_color)['hex']
    crash_assets = os.path.join(paths.ui_assets, 'crash-assets')
    text_color = constants.convert_color((0.6, 0.6, 1))['hex']
    file_icon = os.path.join(paths.ui_assets, "big-icon.png")
    min_size = (600, 600)

    root = Tk()
    width = root.winfo_screenwidth()
    height = root.winfo_screenheight()
    x = int((width / 2) - (min_size[0] / 2))
    y = int((height / 2) - (min_size[1] / 2)) - 15
    root.geometry(f"{min_size[0]}x{min_size[1]}+{x}+{y}")
    root.minsize(width=min_size[0], height=min_size[1])
    root.title(f'{constants.app_title} - Crash')

    # Attempt to use icon, ignore if it doesn't work
    try:
        img = PhotoImage(file=file_icon)
        root.tk.call('wm', 'iconphoto', root._w, img)
    except: pass

    root.configure(bg=background_color)
    root.resizable(False, False)
    root.attributes('-topmost', 1)
    root.attributes('-topmost', 0)
    root.close = False

    # Calculates relative font size based on OS
    def dp(font_size: int or float):
        return font_size if constants.os_name == "windows" else (font_size + 4)

    # Button class
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
            self.background_image = PhotoImage(file=os.path.join(crash_assets, f'{self.id}.png'))
            self.background_hover = PhotoImage(file=os.path.join(crash_assets, f'{self.id}_hover.png'))
            self.background_click = PhotoImage(file=os.path.join(crash_assets, f'{self.id}_click.png'))
            self.function = click_func
            self['image'] = self.background_image

            # Import the image using PhotoImage function
            self.config(
                command = self.click_func,
                borderwidth = 5,
                relief = SUNKEN,
                foreground = background_color,
                background = background_color,
                highlightthickness = 0,
                bd = 0,
                activebackground = background_color
            )

            # Bind hover events
            self.bind('<Enter>', self.on_enter)
            self.bind('<Leave>', self.on_leave)


    # Create background canvas
    canvas = Canvas(root, bg="black", width=min_size[0], height=min_size[1])
    canvas.place(rely=0.5, relx=0.5, anchor=CENTER)


    # Background gradient
    gradient = Image.open(os.path.join(crash_assets, 'gradient.png'))
    gradient = gradient.resize((min_size[0]+3, min_size[1]+4), Image.Resampling.LANCZOS)
    gradient = ImageTk.PhotoImage(gradient)
    canvas.create_image(min_size[0]/2, min_size[1]/2-1, image=gradient)


    # Crash banner
    banner = Image.open(os.path.join(crash_assets, 'crash_banner.png'))
    banner = ImageTk.PhotoImage(banner)
    canvas.create_image(min_size[0]/2, 35, image=banner)


    # Exception label
    canvas.create_text((min_size[0]/2)+2, 145, font=f"Courier {dp(14)} bold", fill=text_color, text="Exception code:")

    # Exception background
    exception = Image.open(os.path.join(crash_assets, 'exception.png'))
    exception = ImageTk.PhotoImage(exception)
    canvas.create_image(min_size[0]/2, 210, image=exception)

    # Exception text
    text_info = Entry(root)
    text_info.insert(END, exc_code)
    text_info.config(
        fg = constants.convert_color((0.937, 0.831, 0.62, 1))['hex'],
        bg = background_color,
        borderwidth = 0,
        highlightthickness = 0,
        selectforeground = constants.convert_color((1, 0.9, 0.8))['hex'],
        selectbackground = constants.convert_color((0.4, 0.4, 0.35))['hex'],
        insertbackground = constants.convert_color((0.55, 0.55, 1, 1))['hex'],
        readonlybackground = "#07071C",
        font = f"Courier {dp(16)} bold",
        state = "readonly",
        justify = "center",
        width=10
    )
    text_info.place(relx=0.5, y=210-(dp(16)/6), anchor=CENTER)

    # When window is closed
    def on_closing():
        root.close = True
        root.destroy()

    # Quit button (Bottom to top)
    button = HoverButton('quit_button', click_func=on_closing)
    button.pack(pady=(20, 35), anchor='s', side='bottom')

    # Restart button
    button = HoverButton('restart_button', click_func=lambda *_: (on_closing(), constants.restart_app()))
    button.pack(pady=20, anchor='s', side='bottom')

    # Log button
    button = HoverButton('log_button', click_func=functools.partial(open_log, log_path))
    button.pack(pady=0, anchor='s', side='bottom')

    # Play crash sound
    try: crash_sound.play()
    except: pass

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()



# if constants.os_name == "windows":
#     from ctypes import windll, c_int64
#     windll.user32.SetProcessDpiAwarenessContext(c_int64(-4))
#
# launch_window("a0-a3e08d", r"C:\Users\macarooni machine\AppData\Roaming\.auto-mcs\Logs\ame-fatal_23-11-04_9-23-23.log")
