from tkinter import Tk, Text, SUNKEN, PhotoImage, Button
from PIL import ImageTk, Image
import constants
import os


# Init Tk window
background_color = constants.convert_color(constants.background_color)['hex']
crash_assets = os.path.join(constants.gui_assets, 'crash-assets')
text_color = constants.convert_color((0.6, 0.6, 1))['hex']
file_icon = os.path.join(constants.gui_assets, "big-icon.png")
min_size = (500, 500)

root = Tk()
width = root.winfo_screenwidth()
height = root.winfo_screenheight()
x = int((width / 2) - (min_size[0] / 2))
y = int((height / 2) - (min_size[1] / 2)) - 15
root.geometry(f"{min_size[0]}x{min_size[1]}+{x}+{y}")
root.minsize(width=min_size[0], height=min_size[1])
root.title(f'{constants.app_title} - Crash Report')
img = PhotoImage(file=file_icon)
root.tk.call('wm', 'iconphoto', root._w, img)
root.configure(bg=background_color)
root.resizable(False, False)
root.close = False


# Button class
class HoverButton(Button):

    def click_func(self, *a):
        self.config(image=self.background_click)
        self.function()

    def on_enter(self, event):
        self.config(image=self.background_hover)

    def on_leave(self, event):
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



# Restart button
Button()
button = HoverButton('restart_button', click_func=constants.restart_app)
button.pack(pady=(30, 55), anchor='s', side='bottom')
button = HoverButton('log_button', click_func=constants.show_crash_log)
button.pack(pady=0, anchor='s', side='bottom')

root.mainloop()
