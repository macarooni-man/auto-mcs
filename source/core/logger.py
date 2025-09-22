from datetime import datetime as dt
from colorama import Fore, Style
from operator import itemgetter
from collections import deque
from copy import deepcopy
from glob import glob
import traceback
import threading
import textwrap
import logging
import hashlib
import queue
import time
import sys
import os

from source.core import constants
from source.core.constants import (

    # Directories
    logsDir,

    # General methods
    folder_check, fmt_date, format_traceback, get_locale_string,
    format_os, format_cpu, format_ram, is_admin, generate_splash,

    # Constants
    app_title, app_version, os_name, text_logo,
)


# ---------------------------------------------- Global Variables ------------------------------------------------------

# Globally enable or disable logging
enable_logging:  bool = True

# Maximum amount of logs to be stored per folder
max_log_count:    int = 25

# Level like: 'INFO' text color
level_color = {
    'debug': Fore.MAGENTA,
    'info': Fore.GREEN,
    'warning': Fore.YELLOW,
    'error': Fore.RED,
    'critical': Fore.RED,
    'fatal': Fore.RED,
}

# Object/module reference color: 'core: test.TestObject'
object_color = {
    'debug': Fore.CYAN,
    'info': Fore.CYAN,
    'warning': Fore.LIGHTYELLOW_EX,
    'error': Fore.LIGHTRED_EX,
    'critical': Fore.LIGHTRED_EX,
    'fatal': Fore.LIGHTRED_EX,
}

# Actual log message at the end
text_color = {
    'debug': Fore.RESET,
    'info': Fore.RESET,
    'warning': Fore.YELLOW,
    'error': Fore.RED,
    'critical': Fore.RED,
    'fatal': Fore.RED,
}



# -------------------------------------------- Submodule Helpers -------------------------------------------------------

# Generates a boot log with system information
def create_boot_log(object_data: str):
    log_args = ' '.join([
        (f'--{k}' if isinstance(v, bool) else f'--{k} "{v}"')
        for k, v in vars(deepcopy(constants.boot_arguments)).items() if v
    ])

    data_list = [
        f'Version:           {app_version} - {format_os()}',
        f'Launch flags:      {log_args if log_args else None}',
        f'Online:            {constants.app_online}',
        f'Permissions:       {"Admin-level" if is_admin() else "User-level"}',
        f'UI Language:       {get_locale_string(True)}',
        f'Headless:          {"True" if constants.headless else "False"}',
        f'Telepath server:   {"Active" if constants.api_manager.running else "Inactive"}',
        f'Processor info:    {format_cpu()}',
        f'Used memory:       {format_ram()}'
    ]

    formatted_properties = "\n".join(data_list)
    send_log(object_data, f'initializing {app_title} with the following properties:\n{formatted_properties}', 'info', 'ui')

# Generates a crash or error report
def create_error_log(exception, error_info=None):

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
    exception_code    = trimmed_exception[-1].strip() + f' ({last_line.split(",", 1)[0].strip()} - {last_line.split(",")[-1].strip()})'
    trimmed_exception = "\n".join(trimmed_exception)
    # print(exception_code)


    # Create AME code
    # Generate code with last application path and last widget interaction
    path = constants.footer_path
    interaction = constants.last_widget
    ame = (hashlib.shake_128(path.split("@")[0].strip().encode()).hexdigest(1) if path else "00") + "-" + hashlib.shake_128(exception_code.encode()).hexdigest(3)


    # Check for 'Logs' folder in application directory
    # If it doesn't exist, create a new folder called 'Logs'
    folder = 'errors' if crash_type == 'error' else 'crashes'
    log_dir = os.path.join(logsDir, folder)
    constants.folder_check(log_dir)


    # Timestamp
    time_stamp = dt.now().strftime(constants.fmt_date("%#H-%M-%S_%#m-%#d-%y"))
    time_formatted = dt.now().strftime(constants.fmt_date("%#I:%M:%S %p  %#m/%#d/%Y"))


    # Header
    header = f'Auto-MCS Exception:    {ame}  '
    splash = generate_splash(True)

    header_len = 42
    calculated_space = 0
    splash_line = ("||" + (' ' * (round((header_len * 1.5) - (len(splash) / 2)) - 2)) + splash)


    # Last interaction
    last_interaction = '\n'.join(i.strip() for i in log_manager.since_last_interaction())

    try:    is_telepath = bool(constants.server_manager.current_server._telepath_data)
    except: is_telepath = False


    # Format running servers
    def format_servers():
        return ', '.join([
            f"{i}: {server.type} {server.version}"
            for i, server in enumerate(constants.server_manager.running_servers.values(), 1)
        ])


    log = f"""{'=' * (header_len * 3)}
{"||" + (' ' * round((header_len * 1.5) - (len(header) / 2) - 1)) + header + (' ' * round((header_len * 1.5) - (len(header)) + 14)) + "||"}
{splash_line + (((header_len * 3) - len(splash_line) - 2) * " ") + "||"}
{'=' * (header_len * 3)}


    General Info:

        Severity:          {crash_type.title()}

        Version:           {app_version} - {format_os()}
        Online:            {constants.app_online}
        Permissions:       {"Admin-level" if is_admin() else "User-level"}
        UI Language:       {get_locale_string(True)}
        Headless:          {"True" if constants.headless else "False"}
        Active servers:    {format_servers() if constants.server_manager.running_servers else "None"}
        Proxy (playit):    {"Active" if constants.playit._tunnels_in_use() else "Inactive"}
        Telepath client:   {"Active" if is_telepath else "Inactive"}
        Telepath server:   {"Active" if constants.api_manager.running else "Inactive"}

        Processor info:    {format_cpu()}
        Used memory:       {format_ram()}



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

{textwrap.indent(trimmed_exception, "        ")}


    Logging since last interaction:

{textwrap.indent(last_interaction, "        ")}"""

    # Only write to disk if the app is compiled and logging is enabled
    if enable_logging:
        file_name = os.path.abspath(os.path.join(log_dir, f"ame-{crash_type}_{time_stamp}.log"))
        with open(file_name, "w") as log_file:
            log_file.write(log)

        # Remove old logs
        file_data = {}
        for file in glob(os.path.join(log_dir, "ame-*.log")):
            file_data[file] = os.stat(file).st_mtime

        sorted_files = sorted(file_data.items(), key=itemgetter(1))

        delete = len(sorted_files) - max_log_count
        for x in range(0, delete):
            os.remove(sorted_files[x][0])

    else:
        file_name = None

    return ame, file_name

# Kivy forwarder to AppLogger
class KivyToLoggerHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.mgr = log_manager
    def emit(self, record: logging.LogRecord):
        try:
            msg = record.getMessage()
            level = (record.levelname or "INFO").lower()

            if msg.startswith("stderr: ") or "Traceback (most recent call last):" in msg:
                level = "error"

            tag = getattr(record, "tag", None) or getattr(record, "ctx", None)
            obj = tag or (f"{record.module}.{record.funcName}" if record.funcName and record.module else record.name)
            self.mgr._dispatch(obj.replace("__init__.", ""), msg, level=level, stack="kivy", _raw=False)
        except Exception:
            self.handleError(record)

# Uvicorn forwarder to AppLogger
class UvicornToLoggerHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.mgr = log_manager
    def emit(self, record: logging.LogRecord):
        try:
            msg = record.getMessage()
            if record.exc_info: msg += "\n" + "".join(traceback.format_exception(*record.exc_info))
            elif record.stack_info: msg += "\n" + str(record.stack_info)
            level = (record.levelname or "INFO").lower()
            tag = getattr(record, "tag", None) or getattr(record, "ctx", None)
            obj = tag or (f"{record.module}.{record.funcName}" if record.funcName and record.module else record.name)
            self.mgr._dispatch(obj.replace("__init__.", ""), msg, level=level, stack="uvicorn", _raw=False)
        except Exception:
            self.handleError(record)



# -------------------------------------------- Logging Managers --------------------------------------------------------

# Main app Logger
class AppLogger():

    # Internal log wrapper
    def _send_log(self, message: str, level: str = None, **kw):
        return self._dispatch(self.__class__.__name__, message, level, **kw)

    def __init__(self):
        self._line_header = '   >  '
        self._max_run_logs = 3
        self._object_width = 40
        self.path = os.path.join(logsDir, "application")

        # Identify this launch (timestamp + pid -> short hash)
        self._launch_ts  = dt.now()
        self._launch_id  = hashlib.sha1(f"{self._launch_ts.isoformat()}-{os.getpid()}".encode("utf-8")).hexdigest()[:6]

        # Initialize db stuff
        self._log_db = deque(maxlen=2500)
        self._db_lock = threading.Lock()  # protect _log_db
        self._io_lock = threading.Lock()  # serialize stdout writes to avoid interweaving

        # Log since last UI action
        self._since_ui = deque(maxlen=1000)

        # Async pipeline
        self._q: 'queue.Queue[tuple[str, str, str, str, bool]]' = queue.Queue(maxsize=100)
        self._stop = threading.Event()
        self._writer = threading.Thread(target=self._worker, name="log-writer", daemon=True)
        self._writer.setDaemon(True)
        self._writer.start()

        # All stacks listed here are not logged unless "debug" is enabled
        self.debug_stacks = ('kivy', 'uvicorn')


        # Branding banner
        self._title = self._generate_title()
        self._send_log(f'{Style.BRIGHT}{self._title}{Style.RESET_ALL}', 'info', _raw=True)

    def _generate_title(self, box_drawing=True):
        self.header_len = 50
        box = ('┃', '━', '┏', '┓', '┗', '┛') if box_drawing else ('│', '—', '—', '—', '—', '—')
        header = f"{box[2]}{box[1] * round(self.header_len / 2)}  auto-mcs v{app_version}  {box[1]* round(self.header_len / 2)}{box[3]}"
        logo   = '\n'.join([f'{box[0]}   {i.ljust(len(header) - 5, " ")}{box[0]}' for i in text_logo])
        footer = f"{box[4]}{box[1] * (len(header) - 2)}{box[5]}"
        return f'{header}\n{logo}\n{footer}'

    # Receive from the rest of the app
    def _dispatch(self, object_data: str, message: str, level: str = None, stack: str = None, _raw=False):
        if '.' not in object_data and object_data not in ['main', 'telepath']:
            object_data = f'{__name__}.{object_data}'
        if any([object_data.startswith(i) for i in ('source.core.', 'source.ui.')]):
            object_data = object_data.split('.', 2)[-1]
        object_data = object_data.strip('. \n')
        if not level: level = 'debug'
        if not stack: stack = 'core'


        # Reject debug log stacks
        if stack in self.debug_stacks and level == 'debug':
            return



        # Enqueue raw fields
        payload = (str(object_data), str(message), str(level), str(stack), _raw)

        # Enqueue line for background write
        try:
            # Prefer dropping general level data if the queue is full
            if self._q.full() and level in ('debug', 'info'):
                try: self._q.get_nowait(); self._q.task_done()
                except queue.Empty: pass
            self._q.put_nowait(payload)

        except queue.Full:

            # For warnings/errors/fatal, block briefly to avoid loss
            try: self._q.put(payload, timeout=0.25)

            # Last resort: block until there is space so critical logs still go through the worker
            except queue.Full: self._q.put(payload)

    def _add_entry(self, object_data: str, message: str, level: str, stack: str):
        data = {'time': dt.now(), 'object_data': object_data, 'level': level, 'stack': stack, 'message': message}
        with self._db_lock:
            self._log_db.append(data)

            # Reset the "since UI" window only on UI actions
            if stack == 'ui' and ('interaction:' in message or 'view:' in message):
                self._since_ui.clear()
            self._since_ui.append(data)

        return data

    def _worker(self):

        # Drain until stop is set and queue is empty
        while not self._stop.is_set() or not self._q.empty():
            try: object_data, message, level, stack, _raw = self._q.get(timeout=0.2)
            except queue.Empty: continue

            try:
                # Build the entry on the worker thread
                data = self._add_entry(object_data, message, level, stack)
                self._print(data, _raw)

            except Exception as e: sys.__stderr__.write(f"Logging worker error: {format_traceback(e)}")
            finally: self._q.task_done()

    def _prune_logs(self):
        files = sorted(
            (p for p in glob(os.path.join(self.path, "auto-mcs_*.log")) if os.path.isfile(p)),
            key = os.path.getmtime,
            reverse = True
        )
        for p in files[self._max_run_logs:]:
            try: os.remove(p)
            except OSError: pass

    def _get_file_name(self):
        time_stamp = self._launch_ts.strftime(fmt_date("%#H-%M-%S_%#m-%#d-%y"))
        file_name  = f"auto-mcs_{time_stamp}.log"
        return os.path.join(self.path, file_name)

    def _print(self, data: dict, _raw: bool = False):

        object_data = data['object_data']
        message = data['message']
        level = data['level']
        stack = data['stack']
        time_obj = data['time']


        # Only send messages if logging is enabled, and only log debug messages in debug mode
        if not (enable_logging and not (not constants.debug and level == 'debug')):
            return

        # Treat low-priority stack logs as "debug"
        if stack in self.debug_stacks and (not constants.debug and level in ('debug', 'info', 'warning')):
            return

        def fmt_block(text: str, color: Fore = Fore.CYAN):
            return f'{Style.BRIGHT}{Fore.LIGHTBLACK_EX}[{color}{text}{Fore.LIGHTBLACK_EX}]{Style.RESET_ALL}'

        with self._io_lock:

            # Make sure start logo displays correctly on Windows
            if _raw and (f' {app_title} v{app_version} ' in message) and (os_name == 'windows'):
                message = self._generate_title(False)

            for x, line in enumerate(message.splitlines(), 0):

                if not _raw:
                    object_width = self._object_width - len(level)
                    timestamp = time_obj.strftime('%I:%M:%S %p')
                    tc = text_color.get(level, Fore.CYAN)
                    content = f'{tc}{line.strip()}' if x == 0 else f'{Fore.LIGHTBLACK_EX}{self._line_header}{tc}{line.rstrip()}'
                    line = (
                        f"{fmt_block(timestamp, Fore.WHITE)} "
                        f"{fmt_block(level.upper(), level_color.get(level, Fore.CYAN))} "
                        f"{fmt_block(f'{stack}: {object_data}'.ljust(object_width), object_color.get(level, Fore.CYAN))} "
                        f"{content}"
                    ) if x == 0 else content

                else: line = line.strip()

                encoding = (sys.stdout and sys.stdout.encoding) or "utf-8"
                formatted = line.encode(encoding, errors="ignore").decode(encoding, errors="ignore")
                print(formatted)


    # Wait until all queued logs are written
    def flush(self, timeout: float = None):
        start = time.monotonic()
        self._q.join()
        if timeout is not None and (time.monotonic() - start) > timeout:
            return False
        return True

    # Stop the writer thread and flush
    def close(self, graceful: bool = True):
        if graceful:
            self._stop.set()
            self.flush()
        else:
            self._stop.set()

    # Flush the queue and write the entire in-memory log to a file, and clear the db
    def dump_to_disk(self) -> str:

        # Ensure background thread has printed/added everything it has
        self.flush()
        path = self._get_file_name()

        # Don’t write if logging is disabled or deque is empty, but still return the path for consistency
        if not enable_logging or not self._log_db:
            with self._db_lock: self._log_db.clear()
            return path


        self._send_log(f"flushing logger to '{path}'")

        # Snapshot and clear
        with self._db_lock:
            entries = list(self._log_db)
            self._log_db.clear()

        # Write plain text, no ANSI
        if not os.path.exists(path):
            folder_check(self.path)
            with open(path, "a+", encoding="utf-8", newline="\n") as f:
                launch_stamp = self._launch_ts.strftime(fmt_date("%#I:%M:%S %p %#m/%#d/%Y"))
                f.write(f"# {launch_stamp} (pid {os.getpid()}) id={self._launch_id}\n\n")

        with open(path, "a+", encoding="utf-8", newline="\n") as f:
            for e in entries:

                time_obj    = e["time"]
                object_data = e["object_data"]
                message     = e["message"]
                level       = e["level"]
                stack       = e["stack"]

                # Replace title log with formatting-free one
                if f' {app_title} v{app_version} ' in message and "█" in message:
                    f.write(self._title + '\n')
                    continue

                # Only log debug messages in debug mode
                if not constants.debug and level == 'debug':
                    continue

                # Treat low-priority stack logs as "debug"
                if stack in self.debug_stacks and (not constants.debug and level in ('debug', 'info', 'warning')):
                    continue


                # Format lines like print method
                object_width = self._object_width - len(level)
                timestamp = time_obj.strftime("%I:%M:%S %p")
                block = f"{stack}: {object_data}".ljust(object_width)

                lines = str(message).splitlines() or [""]
                for i, line in enumerate(lines):
                    if i == 0: f.write(f"[{timestamp}] [{level.upper()}] [{block}] {line.rstrip()}\n")
                    else: f.write(f"{self._line_header}{line.rstrip()}\n")

        self._prune_logs()
        constants.api_manager.logger.dump_to_disk()
        return path

    # Get everything since the last UI action
    def since_last_interaction(self) -> list:

        # Ensure background thread has printed/added everything it has
        self.flush()

        # Snapshot and clear
        with self._db_lock:
            entries = list(self._since_ui)

        log_list = []
        for e in entries:

            time_obj    = e["time"]
            object_data = e["object_data"]
            message     = e["message"]
            level       = e["level"]
            stack       = e["stack"]

            # Skip title log with formatting-free one
            if self._title in message:
                continue


            # Format lines like print method
            object_width = 37 - len(level)
            timestamp = time_obj.strftime("%I:%M:%S %p")
            block = f"{stack}: {object_data}".ljust(object_width)

            lines = str(message).splitlines() or [""]
            for i, line in enumerate(lines):
                if i == 0: log_line = f"[{timestamp}] [{level.upper()}] [{block}] {line.strip()}\n"
                else:      log_line = f"{self._line_header}{line.strip()}\n"
                log_list.append(log_line)

        return log_list

# Telepath API logger
class AuditLogger():

    # Internal log wrapper
    def _send_log(self, message: str, level: str = None):
        return send_log(self.__class__.__name__, message, level)

    def __init__(self):
        self.path = os.path.join(logsDir, 'telepath')
        self.current_users = {}
        self.max_logs = max_log_count
        self.tags = {
            'ignore': ['_sync_attr', '_sync_telepath_stop', '_telepath_run_data', 'return_single_list', 'hash_changed',
                       '_view_notif', 'reload_config', 'retrieve_suggestions', 'get_rule', 'properties_dict'
            ],
            'auth': ['login', 'logout', 'get_public_key', 'request_pair', 'confirm_pair'],
            'warn': ['save', 'restore'],
            'high': ['delete', 'import_script', 'script_state']
        }

        # Initialize db stuff
        self._db_lock = threading.Lock()  # protects _audit_db
        self._io_lock = threading.Lock()  # serialize stdout writes to avoid interweaving
        self._audit_db = deque(maxlen=2500)

        # Async pipeline
        self._q: 'queue.Queue[tuple[str, str, str, str]]' = queue.Queue(maxsize=100)
        self._stop = threading.Event()
        self._writer = threading.Thread(target=self._worker, name="audit-writer", daemon=True)
        self._writer.setDaemon(True)
        self._writer.start()
        self._send_log('initialized AuditLogger')

    # Prune old logs
    def _prune_logs(self):
        file_list = glob(os.path.join(self.path, "session-audit_*.log"))
        if len(file_list) > self.max_logs:

            file_data = {}
            for file in file_list:
                file_data[file] = os.stat(file).st_mtime

            sorted_files = sorted(file_data.items(), key=itemgetter(1))

            delete = len(sorted_files) - self.max_logs
            for x in range(0, delete):
                os.remove(sorted_files[x][0])

    # Returns formatted name of file, with the date
    def _get_file_name(self):
        time_stamp = dt.now().strftime(constants.fmt_date("%#m-%#d-%y"))
        file_name  = f"session-audit_{time_stamp}.log"
        return os.path.abspath(os.path.join(self.path, file_name))

    # Used for reporting internal events; now a thin wrapper that just enqueues raw fields
    def _dispatch(self, event: str, host: str = '', extra_data: str = '', server_name: str = ''):
        payload = (str(event), host, str(extra_data), str(server_name))

        # Enqueue line for background write
        try:
            # Prefer dropping general level data if the queue is full
            if self._q.full():
                try: self._q.get_nowait(); self._q.task_done()
                except queue.Empty: pass
            self._q.put_nowait(payload)

        except queue.Full:

            # For warnings/errors/fatal, block briefly to avoid loss
            try: self._q.put(payload, timeout=0.25)

            # Last resort: block until there is space so critical logs still go through the worker
            except queue.Full: self._q.put(payload)

    # Heavy work happens here on the worker thread; returns a fully formatted line or None to drop
    def _add_entry(self, event: str, host, extra_data: str, server_name: str):
        threat = False
        event_tag = 'info'

        # Prioritize threats
        if isinstance(extra_data, str) and extra_data.lower().strip().startswith('potential threat blocked:'):
            threat = True
            event_tag = 'high'

        # Ignore hidden events
        elif '._' in event and event not in ['acl._process_query']:
            return

        # Format host
        if isinstance(host, str) and host in self.current_users:
            host = self.current_users[host]

        if host: formatted_host = f"{host['host']}/{host['user']} | {host['ip']}"
        else:    formatted_host = 'Unknown host'

        # Format date and event
        date_label = dt.now().strftime(constants.fmt_date("%#I:%M:%S %p")).rjust(11)
        formatted_event = event.replace('.', ' > ').replace('_', ' ').replace('  ', ' ').title()
        if server_name:
            formatted_event = f'Server: "{server_name}" > {formatted_event.replace("Server > ", "", 1)}'
            formatted_event = formatted_event.replace('object', ' Object', 1)

        # Get tag level from tag list if it's not a threat
        if not threat:
            for t, events in self.tags.items():
                for e in events:
                    if event.endswith(e.lower()):
                        if t == 'ignore': return
                        event_tag = t
                        break

        no_date_message = f'[{event_tag.upper()}] [user: {formatted_host}] {formatted_event}'
        formatted_message = f'[{date_label}] {no_date_message}'
        if extra_data: formatted_message += f' > {extra_data}'


        # Format sessions
        if (event.endswith('login') or event.endswith('submit_pair')) and isinstance(extra_data, str) and 'success' in extra_data.lower():
            formatted_message = f'<< Session Start - {formatted_host} >>\n{formatted_message}'
        elif event.endswith('logout') and not threat:
            formatted_message = f'{formatted_message}\n-- Session End - {formatted_host} --'

        self._send_log(no_date_message)
        return formatted_message

    def _worker(self):

        # Drain until stop is set and queue is empty
        while not self._stop.is_set() or not self._q.empty():
            try: payload = self._q.get(timeout=0.2)
            except queue.Empty: continue

            try:
                # Handle tuple payloads from _dispatch
                if isinstance(payload, tuple) and len(payload) == 4:
                    event, host, extra_data, server_name = payload
                    line = self._add_entry(event, host, extra_data, server_name)
                    if not line: continue

                # If a preformatted string ever gets enqueued
                elif isinstance(payload, str): line = payload
                else: continue

                # Append to in-memory buffer
                with self._db_lock: self._audit_db.append({'time': dt.now(), 'line': line})

            except Exception as e: self._send_log(f"Audit logging worker error: {constants.format_traceback(e)}", 'error')
            finally: self._q.task_done()


    # Format list of dictionaries for UI
    def read(self):

        # Make sure background enqueues are flushed or processed to disk before reading
        self.flush()

        log_data = []
        file_name = self._get_file_name()
        if os.path.exists(file_name):
            with open(file_name, 'r') as f:
                log_data = f.readlines()
        return log_data

    # Wait until all queued audit lines are in _audit_db
    def flush(self, timeout: float = None):
        start = time.monotonic()
        self._q.join()
        if timeout is not None and (time.monotonic() - start) > timeout:
            return False
        return True

    # Stop the writer thread
    def close(self, graceful: bool = True):
        if graceful:
            self._stop.set()
            self.flush()
        else:
            self._stop.set()

    # Flush queue and write the entire in-memory audit buffer to disk and clear the buffer
    def dump_to_disk(self) -> str:

        # Ensure background thread has appended everything to _audit_db
        self.flush()
        path = self._get_file_name()

        # Don’t write if logging is disabled or deque is empty, but still return the path for consistency
        if not enable_logging or not self._audit_db:
            with self._db_lock: self._audit_db.clear()
            return path


        self._send_log(f"flushing logger to '{path}'")

        # Ensure file/dir exists
        mode = 'a+'
        if not os.path.exists(path):
            constants.folder_check(os.path.dirname(path))
            mode = 'w+'

        # Snapshot & clear buffer
        with self._db_lock:
            entries = list(self._audit_db)
            self._audit_db.clear()

        # Write plain text (your messages are already formatted)
        constants.folder_check(self.path)
        with open(path, mode, encoding="utf-8", newline="\n", errors='ignore') as f:
            for e in entries:
                f.write(f"{e['line'].rstrip()}\n")

        self._prune_logs()
        return path



# ------------------------------------------- Initialize Manager -------------------------------------------------------

# Global logger wrapper
# Levels: 'debug', 'info', 'warning', 'error', 'fatal'
# Stacks: 'core', 'ui', 'api', 'amscript'
if not constants.is_child_process:
    log_manager: AppLogger = AppLogger()
    send_log = log_manager._dispatch

# Only load the logger in the main process
else:
    log_manager = None
    send_log = lambda *_: None
