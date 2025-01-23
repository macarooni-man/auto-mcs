from platform import platform, architecture
from operator import itemgetter
from glob import glob
import functools
import datetime
import textwrap
import hashlib
import psutil
import os

import constants



# Import Tk if not headless
if not constants.headless:
    from tkinter import Tk, Entry, SUNKEN, Canvas, PhotoImage, CENTER, END
    from PIL import ImageTk, Image
    import simpleaudio as sa

    import logviewer


    # Remove border on macOS buttons
    if constants.os_name == 'macos':
        import tkmacosx
        class Button(tkmacosx.Button):
            def __init__(self, **args):
                super().__init__(**args)
                self.config(borderless=1, focusthickness=0, state='active')
    else:
        from tkinter import Button



# Generates crash report
def generate_log(exception, error_info=None):

    # No error info can be provided with a hard crash
    if error_info:
        crash_type = 'error'
        error_info = f'''
        Error information:
        
            {error_info}
            
'''
    else:
        crash_type = 'fatal'
        error_info = ''


    # Remove file paths from exception
    trimmed_exception = []
    exception_lines = exception.splitlines()
    last_line = None
    for line in exception_lines:
        if ("192.168" in line or "auto-mcs-gui" in line) and 'File "' in line:
            indent, line_end = line.split('File "', 1)
            path, line_end = line_end.split('"', 1)
            line = f'{indent}File "{os.path.basename(path.strip())}"{line_end.strip()}'

        elif "site-packages" in line.lower() and 'File "' in line:
            indent, line_end = line.split('File "', 1)
            path, line_end = line_end.split('"', 1)
            line = f'{indent}File "site-packages{path.split("site-packages", 1)[1]}"{line_end.strip()}'

        if ", line" in line:
            last_line = line

        trimmed_exception.append(line)

    exception_summary = trimmed_exception[-1].strip() + f'\n    ({last_line.strip()})'
    exception_code = trimmed_exception[-1].strip() + f' ({last_line.split(",", 1)[0].strip()} - {last_line.split(",")[-1].strip()})'
    # print(exception_code)
    trimmed_exception = "\n".join(trimmed_exception)


    # Create AME code
    # Generate code with last application path and last widget interaction
    path = constants.footer_path
    interaction = constants.last_widget
    ame = (hashlib.shake_128(path.split("@")[0].strip().encode()).hexdigest(1) if path else "00") + "-" + hashlib.shake_128(exception_code.encode()).hexdigest(3)

    # Check for 'Logs' folder in application directory
    # If it doesn't exist, create a new folder called 'Logs'
    log_dir = os.path.join(constants.applicationFolder, "Logs")
    constants.folder_check(log_dir)

    # Timestamp
    time_stamp = datetime.datetime.now().strftime(constants.fmt_date("%#H-%M-%S_%#m-%#d-%y"))
    time_formatted = datetime.datetime.now().strftime(constants.fmt_date("%#I:%M:%S %p  %#m/%#d/%Y"))

    # Header
    header = f'Auto-MCS Exception:    {ame}  '
    splash = constants.generate_splash(True)

    cpu_arch = architecture()
    if len(cpu_arch) > 1:
        cpu_arch = cpu_arch[0]

    header_len = 42
    calculated_space = 0
    splash_line = ("||" + (' ' * (round((header_len * 1.5) - (len(splash) / 2)) - 2)) + splash)

    formatted_os_name = constants.os_name.title() if constants.os_name != 'macos' else 'macOS'
    try:
        is_telepath = bool(constants.server_manager.current_server._telepath_data)
    except:
        is_telepath = False

    log = f"""{'=' * (header_len * 3)}
{"||" + (' ' * round((header_len * 1.5) - (len(header) / 2) - 1)) + header + (' ' * round((header_len * 1.5) - (len(header)) + 14)) + "||"}
{splash_line + (((header_len * 3) - len(splash_line) - 2) * " ") + "||"}
{'=' * (header_len * 3)}


    General Info:
        
        Severity:          {crash_type.title()}
        
        Version:           {constants.app_version} - {formatted_os_name} ({"Docker, " if constants.is_docker else ""}{platform()})
        Online:            {constants.app_online}
        UI Language:       {constants.get_locale_string(True)}
        Headless:          {constants.headless}
        Active servers:    {', '.join([f"{x}: {y.type} {y.version}" for x, y in enumerate(constants.server_manager.running_servers.values(), 1)]) if constants.server_manager.running_servers else "None"}
        Proxy (playit):    {"Active" if constants.playit._tunnels_in_use() else "Inactive"}
        Telepath client:   {"Active" if is_telepath else "Inactive"}
        Telepath server:   {"Active" if constants.api_manager.running else "Inactive"}

        Processor info:    {psutil.cpu_count(False)} ({psutil.cpu_count()}) C/T @ {round((psutil.cpu_freq().max) / 1000, 2)} GHz ({cpu_arch.replace('bit', '-bit')})
        Used memory:       {round(psutil.virtual_memory().used / 1073741824, 2)} / {round(psutil.virtual_memory().total / 1073741824)} GB



    Time of AME:

    {textwrap.indent(time_formatted, "    ")}



    Application path at time of AME:

    {textwrap.indent(str(path), "    ")}

    
    
    Last interaction at time of AME:

    {textwrap.indent(str(interaction), "    ")}
    
    

    AME traceback:
        {'' if not error_info else error_info}
        Exception Summary:
    {textwrap.indent(exception_summary, "        ")}

{textwrap.indent(trimmed_exception, "        ")}"""


    file_name = os.path.abspath(os.path.join(log_dir, f"ame-{crash_type}_{time_stamp}.log"))
    with open(file_name, "w") as log_file:
        log_file.write(log)

    # Remove old logs
    keep = 50

    file_data = {}
    for file in glob(os.path.join(log_dir, "ame-*.log")):
        file_data[file] = os.stat(file).st_mtime

    sorted_files = sorted(file_data.items(), key=itemgetter(1))

    delete = len(sorted_files) - keep
    for x in range(0, delete):
        os.remove(sorted_files[x][0])


    return ame, file_name


# Opens crash log
def open_log(log_path):

    # Don't attempt to open a log that doesn't exist
    if log_path:
        if not os.path.exists(log_path):
            return

    data_dict = {
        'app_title': constants.app_title,
        'gui_assets': constants.gui_assets,
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
        print(f'(!)  Uh oh, auto-mcs has crashed:  {exc_code}\n\n> Crash log:  {log_path}')
        return


    # Init Tk window
    crash_sound = sa.WaveObject.from_wave_file(os.path.join(constants.gui_assets, 'sounds', 'crash.wav'))
    background_color = constants.convert_color(constants.background_color)['hex']
    crash_assets = os.path.join(constants.gui_assets, 'crash-assets')
    text_color = constants.convert_color((0.6, 0.6, 1))['hex']
    file_icon = os.path.join(constants.gui_assets, "big-icon.png")
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
    except:
        pass

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


    # Quit button (Bottom to top)
    button = HoverButton('quit_button', click_func=root.destroy)
    button.pack(pady=(20, 35), anchor='s', side='bottom')

    # Restart button
    button = HoverButton('restart_button', click_func=constants.restart_app)
    button.pack(pady=20, anchor='s', side='bottom')

    # Log button
    button = HoverButton('log_button', click_func=functools.partial(open_log, log_path))
    button.pack(pady=0, anchor='s', side='bottom')

    # Play crash sound
    try:
        crash_sound.play()
    except:
        pass

    # When window is closed
    def on_closing():
        root.close = True
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    root.mainloop()



# if constants.os_name == "windows":
#     from ctypes import windll, c_int64
#     windll.user32.SetProcessDpiAwarenessContext(c_int64(-4))
#
# launch_window("a0-a3e08d", r"C:\Users\macarooni machine\AppData\Roaming\.auto-mcs\Logs\ame-fatal_23-11-04_9-23-23.log")
