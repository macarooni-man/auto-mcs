from tkinter import Tk, Entry, Label, SUNKEN, Frame, PhotoImage, Button, CENTER, END, BOTH, X, Y
from platform import platform, architecture
from traceback import format_exc
from operator import itemgetter
from PIL import ImageTk, Image
from glob import glob
import datetime
import textwrap
import hashlib
import psutil
import os

import constants
import logviewer


# Generates crash report
def generate_log(exception):

    # Remove file paths from exception
    trimmed_exception = []
    skip = False
    exception_lines = exception.splitlines()
    for item in exception_lines:

        if skip is True or "Traceback" in item:
            skip = False
            continue

        if "File \"C:\\" in item:
            indent = item.split("File \"", 1)[0]
            eol = "," + item.split(",", 1)[1]
            lib_path = ""

            if "Python\\Python" in item:
                file = item.split("File \"", 1)[1].split("\"")[0]
                file = os.path.basename("C:\\" + file)
                lib_path = item.split("lib\\", 1)[1].split(file)[0]

            else:
                file = item.split("File \"", 1)[1].split("\"")[0]
                file = os.path.basename("C:\\" + file)

            line = indent + f"File \"{lib_path}{file}\""
            skip = True

        else:
            line = item.split(",")[0]

        if "File" in line:
            line += "," + item.split(",")[2]

        trimmed_exception.append(line)

    trimmed_exception = "\n".join(trimmed_exception[-2:])

    # Create AME code
    # Generate code with last application path and last widget interaction
    path = " > ".join(constants.footer_path) if isinstance(constants.footer_path, list) else constants.footer_path
    ame = (hashlib.shake_128(path.encode()).hexdigest(1) if path else "00") + "-" + hashlib.shake_128(trimmed_exception.encode()).hexdigest(3)

    # Check for 'Logs' folder in application directory
    # If it doesn't exist, create a new folder called 'Logs'
    log_dir = os.path.join(constants.applicationFolder, "Logs")

    # Timestamp
    time_stamp = datetime.datetime.now().strftime("%#H-%M-%S_%#m-%#d-%y" if constants.os_name == "windows" else "%-H-%M-%S_%-m-%-d-%y")
    time_formatted = datetime.datetime.now().strftime("%#I:%M:%S %p  %#m/%#d/%Y" if constants.os_name == "windows" else "%-I:%M:%S %p  %-m/%-d/%Y")

    # Header
    header = f'Auto-MCS Exception:    {ame}  '

    if not os.path.isdir(log_dir):
        os.makedirs(log_dir)

    cpu_arch = architecture()
    if len(cpu_arch) > 1:
        cpu_arch = cpu_arch[0]

    log = f"""{'=' * (42 * 3)}
    {"||" + (' ' * round((42 * 1.5) - (len(header) / 2) - 1)) + header + (' ' * round((42 * 1.5) - (len(header)) + 14)) + "||"}
    {'=' * (42 * 3)}


    General Info:

        Version:           {constants.app_version} - {constants.os_name.title()} ({platform()})
        Online:            {constants.app_online}
        Sub-servers:       {', '.join([f"{x}: {y.type} {y.version}" for x, y in enumerate(constants.server_manager.running_servers.values(), 1)]) if constants.server_manager.running_servers else "None"}
        ngrok:             {"Inactive" if constants.ngrok_ip['ip'] == "" else "Active"}

        Processor info:    {psutil.cpu_count(False)} ({psutil.cpu_count()}) C/T @ {round((psutil.cpu_freq().max) / 1000, 2)} GHz ({cpu_arch})
        Used memory:       {round(psutil.virtual_memory().used / 1073741824) / round(psutil.virtual_memory().total / 1073741824)} GB



    Time of AME:

    {textwrap.indent(time_formatted, "    ")}



    Application path at time of AME:

    {textwrap.indent(path, "    ")}

    
    
    Last interaction at time of AME:

    {textwrap.indent(path, "    ")}
    
    

    AME traceback:

    {textwrap.indent(exception, "    ")}"""

    with open(os.path.abspath(os.path.join(log_dir, f"ame-fatal_{time_stamp}.log")), "w") as log_file:
        log_file.write(log)

    # Remove old logs
    keep = 50

    fileData = {}
    for file in glob(os.path.join(log_dir, "ame-fatal*.log")):
        fileData[file] = os.stat(file).st_mtime

    sortedFiles = sorted(fileData.items(), key=itemgetter(1))

    delete = len(sortedFiles) - keep
    for x in range(0, delete):
        os.remove(sortedFiles[x][0])


    return ame, log_file

    # f"Uh oh, it appears that Auto-MCS has crashed."
    # f"   Auto-MCS: Crash"
    # f" AME code:  {ame}\n\n\n"
    # buttons.append("Restart Auto-MCS")
    # buttons.append("Open crash log")
    # buttons.append("Quit...")
    # main.footer_text = ['Auto-MCS Crash']


#     if "Open crash log":
#         latest_file = max(glob.glob(log_dir + "\\*"), key=os.path.getctime)
#         Popen(f"notepad.exe \"{os.path.abspath(latest_file)}\"")
#
#     elif "Restart":
#         exeName = os.path.basename(sys.executable)  # if this breaks, change exeName back to fileName
#
#         myBat = open(f'{log_dir}\\auto-mcs-reboot.bat', 'w+')
#
#         if getattr(sys, 'frozen', False):  # Running as compiled
#             myBat.write(f"""taskkill /f /im \"{exeName}\"
#
# cd \"{currentDir}\"
# start \"\" \"{exeName}\"
#
# del \"{log_dir}\\auto-mcs-reboot.bat\"""")
#
#             else:
#                 myBat.write(f"""taskkill /f /im \"{exeName}\"
#
# cd \"{currentDir}\"
# start \"\" cmd /c \"Launch.bat\"
#
# del \"{log_dir}\\auto-mcs-reboot.bat\"""")
#
#             myBat.close()
#             os.chdir(log_dir)
#             os.system("start /b cmd \"\" /C auto-mcs-reboot.bat > nul 2>&1")
#             b.join()
#             f.join()
#             sys.exit()
#
#         elif "Quit..." in buttonClicked:
#             break


# Launches Tk window to provide crash information
def launch_window(exc_code, log_path):

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


    # Crash banner
    img = Image.open(os.path.join(crash_assets, 'crash_banner.png'))
    img = ImageTk.PhotoImage(img)
    banner = Label(image=img, fg=background_color, bg=background_color, borderwidth=0)
    banner.pack(pady=10)


    # Exception label
    exception_label = Label(root, font="Courier 14 bold", fg=text_color, bg=background_color, text="Exception code:")
    exception_label.place(rely=0.25, relx=0.5, anchor=CENTER)

    # Exception layout
    entry_frame = Frame(root, width=400,height=100, background=background_color)
    entry_frame.place(rely=0.38, relx=0.5, anchor=CENTER)

    # Exception background
    exc = Image.open(os.path.join(crash_assets, 'exception.png'))
    exc = ImageTk.PhotoImage(exc)
    background = Label(
        entry_frame,
        image = exc,
        fg = background_color,
        bg = background_color,
        borderwidth = 0,
        compound = "center",
    )
    background.place(rely=0.5, relx=0.5, anchor=CENTER)


    # Exception text
    text_info = Entry(entry_frame)
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
        font = "Courier 16 bold",
        state = "readonly",
        justify = "center"
    )
    text_info.place(rely=0.5, relx=0.5, anchor=CENTER)

    button = HoverButton('quit_button', click_func=lambda *_: root.destroy())
    button.pack(pady=(15, 20), anchor='s', side='bottom')

    # Restart button
    button = HoverButton('restart_button', click_func=constants.restart_app)
    button.pack(pady=12, anchor='s', side='bottom')

    # Log button
    button = HoverButton('log_button', click_func=constants.show_crash_log)
    button.pack(pady=0, anchor='s', side='bottom')

    root.mainloop()


launch_window("a0-a3e08d", None)