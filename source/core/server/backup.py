from datetime import datetime as dt
from functools import reduce
from glob import glob
import time
import os

from source.core.server import manager
from source.core import constants


# Auto-MCS Back-up API
# ----------------------------------------------- Backup Objects -------------------------------------------------------

# Log wrapper
def send_log(object_data, message, level=None):
    return constants.send_log(f'{__name__}.{object_data}', message, level, 'core')


# Instantiate backup object from file (backup_info is data from self._backup_stats['backup-list'])
# server_name, file_path --> BackupObject
class BackupObject():

    def _grab_config(self):
        cwd = constants.get_cwd()
        extract_folder = os.path.join(constants.tempDir, 'bkup_tmp')
        constants.folder_check(extract_folder)
        os.chdir(extract_folder)

        # Extract auto-mcs.ini from back-up file to grab version information
        constants.run_proc(f'tar -xvf "{self.path}" auto-mcs.ini')
        constants.run_proc(f'tar -xvf "{self.path}" .auto-mcs.ini')

        cfg_list = glob(os.path.join(extract_folder, 'auto-mcs.ini'))
        cfg_list.extend(glob(os.path.join(extract_folder, '.auto-mcs.ini')))

        for cfg in cfg_list:
            config = constants.configparser.ConfigParser(allow_no_value=True, comment_prefixes=';')
            config.optionxform = str
            config.read(cfg)
            if config:

                # If auto-mcs.ini exists, grab version and type information
                if config.get('general', 'serverName') == self.name:
                    self.type = config.get('general', 'serverType')
                    self.version = config.get('general', 'serverVersion')
                    try:
                        self.build = config.get('general', 'serverBuild')
                    except:
                        self.build = None

                os.remove(cfg)
                break

        os.chdir(cwd)
        constants.safe_delete(extract_folder)

    def __init__(self, server_name: str, backup_info: list, no_fetch=False):
        self.name = server_name

        self.path = backup_info[0]
        self.size = backup_info[1]
        self.date = backup_info[2]

        self.type = 'Unknown'
        self.version = 'Unknown'
        self.build = None

        if not no_fetch:
            self._grab_config()

    def __repr__(self):
        return f"<{__name__}.{self.__class__.__name__} '{self.name}' at '{self.date}'>"


# Instantiate class with "server_name" (case-sensitive)
# Houses backup functions in class
class BackupManager():

    # Internal log wrapper
    def _send_log(self, message: str, level: str = None):
        return send_log(self.__class__.__name__, f"'{self._server['name']}': {message}", level)

    def __init__(self, server_name: str):
        self._server, self._backup_stats = dump_config(server_name)
        self.directory = self._backup_stats['backup-path']
        self.auto_backup = self._backup_stats['auto-backup']
        self.maximum = self._backup_stats['max-backup']
        self.total_size = self._backup_stats['total-size-bytes']
        self.list = [BackupObject(self._server['name'], file, no_fetch=True) for file in self._backup_stats['backup-list']]
        if self.list:
            self.latest = self.list[0]
        else:
            self.latest = None
        self._restore_file = None

        # Add path to download whitelist
        if self.directory not in constants.telepath_download_whitelist['paths']:
            constants.telepath_download_whitelist['paths'].append(self.directory)

    # Returns the value of the requested attribute (for remote)
    def _sync_attr(self, name):
        return constants.sync_attr(self, name)

    # Refreshes self._backup_stats
    def _update_data(self):
        self._server, self._backup_stats = dump_config(self._server['name'])
        self.directory = self._backup_stats['backup-path']
        self.auto_backup = self._backup_stats['auto-backup']
        self.maximum = self._backup_stats['max-backup']
        self.total_size = self._backup_stats['total-size-bytes']
        self.list = [BackupObject(self._server['name'], file, no_fetch=True) for file in self._backup_stats['backup-list']]
        if self.list:
            self.latest = self.list[0]
        else:
            self.latest = None

        # Add path to download whitelist
        if self.directory not in constants.telepath_download_whitelist['paths']:
            constants.telepath_download_whitelist['paths'].append(self.directory)

    # Retrieves data from local back-up file
    # name --> dict
    def _retrieve_telepath_backup(self, file_path: str):
        for backup in self.list:
            if file_path == backup.path:
                return backup

    # Retrieves deep scan of all back-up files
    def return_backup_list(self):
        self.list = [BackupObject(self._server['name'], file) for file in self._backup_stats['backup-list']]
        self._send_log(f"generated new back-up list:\n{self.list}")
        return self.list


    # Backup functions

    # Backs up server to the backup directory in auto-mcs.ini
    def save(self, ignore_running=False):
        backup = backup_server(self._server['name'], self._backup_stats, ignore_running)
        self._update_data()
        return backup

    # Restores server from file name
    def restore(self, backup_obj: BackupObject):
        if self._server['name'] not in constants.server_manager.running_servers:
            backup = restore_server(self._server['name'], backup_obj.path, self._backup_stats)
            self._update_data()
            return backup
        else:
            self._send_log("unable to restore while this server is running", 'warning')
            return None

    # Moves backup directory to new_path
    def set_directory(self, new_directory: str):
        path = set_backup_directory(self._server['name'], new_directory, self.maximum)
        self._update_data()
        return path

    # Sets maximum backup limit
    # amount: <int> or 'unlimited'
    def set_amount(self, amount):
        new_amt = None

        try:
            new_amt = set_backup_amount(self._server['name'], amount)
            self._update_data()
            self._send_log(f"successfully set maximum back-ups to '{amount}'", 'info')

        except Exception as e:
            self._send_log(f"error setting maximum back-ups to '{amount}': {constants.format_traceback(e)}")

        return new_amt

    # Toggle auto backup status
    def enable_auto_backup(self, enabled=True):
        log_verb = 'en' if enabled else 'dis'
        status = None

        try:
            status = enable_auto_backup(self._server['name'], enabled)
            self._update_data()
            self._send_log(f"successfully {log_verb}abled automatic back-ups", 'info')

        except Exception as e:
            self._send_log(f"error {log_verb}abling automatic back-ups: {constants.format_traceback(e)}")

        return status



# ---------------------------------------------- General Functions -----------------------------------------------------

# Converts os.mtime to readable format
def convert_date(m_time: int or float):
    if isinstance(m_time, (int, float)):
        dt_obj = dt.fromtimestamp(float(m_time))
    else:
        dt_obj = m_time
    days = (dt.now().date() - dt_obj.date()).days
    if days == 0:
        fmt = f"{constants.translate('Today')} {constants.fmt_date('%#I:%M %p')}"
    elif days == 1:
        fmt = f"{constants.translate('Yesterday')} {constants.fmt_date('%#I:%M %p')}"
    else:
        fmt = constants.fmt_date("%a %#I:%M %p %#m/%#d/%y")

    # Translate day
    if constants.app_config.locale != 'en':
        date = dt_obj.strftime(fmt)
        for day in ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']:
            if day.startswith(date[:3]):
                return constants.translate(day)[:3] + date[3:]

    return dt_obj.strftime(fmt)


# Convert string to date
def convert_date_str(file_name: str):
    if "- Copy" in file_name:
        file_name = file_name.split("- Copy")[0].strip()
    if file_name.endswith('.tgz'):
        return dt.strptime(file_name.split("__")[1].split(".tgz")[0], "%H.%M %m-%d-%y" + (",%S" if "," in file_name else ""))
    else:
        return dt.strptime(file_name.split("__")[1].split(".amb")[0], "%H.%M %m-%d-%y" + (",%S" if "," in file_name else ""))


# Converts os.st_time to readable format
def convert_size(size: int):
    size_str = ""

    if (len(str(size)) > 3) and (len(str(size)) < 7):
        size /= 1024
        size = round(size, 2)
        size_str = f"{size} K"

    elif (len(str(size)) > 6) and (len(str(size)) < 10):
        size /= 1048576
        size = round(size, 2)
        size_str = f"{size} M"

    elif (len(str(size)) > 9) and (len(str(size)) < 13):
        size /= 1073741824
        size = round(size, 2)
        size_str = f"{size} G"

    elif len(str(size)) > 12:
        size /= 1099511627776
        size = round(size, 2)
        size_str = f"{size} T"

    size_str += "B"

    if size_str == "B":
        size_str = f"0 B"

    return size_str


# name --> version, path
def dump_config(server_name: str, new_server=False):

    server_dict = {
        'name': server_name,
        'version': None,
        'path': os.path.join(constants.serverDir, server_name)
    }

    backup_stats = {
        'backup-path': constants.backupFolder,
        'auto-backup': 'prompt',
        'max-backup': '5',
        'latest-backup': None,
        'total-size': convert_size(0),
        'total-size-bytes': 0,
        'backup-list': []
    }


    config_file = manager.server_path(server_name, constants.server_ini)

    # Check auto-mcs.ini for info
    if config_file and os.path.isfile(config_file):
        server_config = manager.server_config(server_name)

        # Only pickup server as valid with good config
        if server_name == server_config.get("general", "serverName"):
            server_dict['version'] = server_config.get("general", "serverVersion")
            backup_stats['backup-path'] = str(server_config.get("bkup", "bkupDir"))
            backup_stats['auto-backup'] = str(server_config.get("bkup", "bkupAuto").lower())
            backup_stats['max-backup'] = str(server_config.get("bkup", "bkupMax"))


    # Generate backup list and metadata
    if manager.server_path(server_name):

        backup_stats['backup-list'] = sorted([[file, os.stat(file).st_size, os.stat(file).st_mtime] for file in glob(os.path.join(backup_stats['backup-path'], f'{server_dict["name"]}__*'))], key=lambda x: x[2], reverse=True)

        try:
            backup_stats['latest-backup'] = convert_date(backup_stats['backup-list'][0][2])
            backup_stats['total-size-bytes'] = reduce(lambda x, y: x+y, [z[1] for z in backup_stats['backup-list']])
            backup_stats['total-size'] = convert_size(backup_stats['total-size-bytes'])
        except IndexError:
            pass

        backup_stats['backup-list'] = [[file[0], convert_size(file[1]), convert_date(file[2])] for file in backup_stats['backup-list']]


    return server_dict, backup_stats



# ---------------------------------------------- Backup Functions ------------------------------------------------------


# name --> backup to directory
def backup_server(name: str, backup_stats=None, ignore_running=False):

    if set_lock(name, True, 'save'):

        try:
            if not backup_stats:
                backup_stats = dump_config(name)[1]

            # If the server is running, force a save first
            server_obj = None
            if name in constants.server_manager.running_servers and not ignore_running:
                server_obj = constants.server_manager.running_servers[name]
                server_obj.silent_command('save-all flush')
                server_obj.silent_command('save-off')
                time.sleep(3)

            cwd = constants.get_cwd()
            bkup_time = dt.now().strftime("%H.%M %m-%d-%y")
            backup_path = backup_stats["backup-path"]
            file_name = f"{name}__{bkup_time}.amb"
            backup_file = os.path.join(backup_path, file_name)
            if os.path.exists(backup_file):
                bkup_time = dt.now().strftime("%H.%M %m-%d-%y,%S")
                file_name = f"{name}__{bkup_time}.amb"
                backup_file = os.path.join(backup_path, file_name)

            temp_backup = os.path.join(backup_path, f'{name}-bkup')
            constants.folder_check(backup_path)
            server_path = manager.server_path(name)

            failed = True
            while failed:
                if os.path.exists(temp_backup):
                    constants.safe_delete(temp_backup)
                    constants.folder_check(temp_backup)
                try: constants.copy_to(server_path, backup_path, f'{name}-bkup')
                except: continue
                os.chdir(temp_backup)

                # Create backup
                code = constants.run_proc(f'tar --exclude="*session.lock" -cvf \"{os.path.join(backup_path, f"{name}-bkup.amb")}\" {"*" if constants.os_name == "windows" else "* .??*"}')
                if code != 0: continue

                failed = False

            if os.path.exists(backup_file): os.remove(backup_file)
            os.rename(os.path.join(backup_path, f"{name}-bkup.amb"), backup_file)


            # Clear old backups if there's a limit in auto-mcs.ini
            if backup_stats['max-backup'] != "unlimited":

                keep = int(backup_stats['max-backup'])
                backup_list = sorted([[file, os.stat(file).st_mtime] for file in glob(os.path.join(backup_path, f'{name}__*'))], key=lambda x: x[1])

                delete = len(backup_list) - keep
                if delete > 0:
                    for y in range(0, delete):
                        os.remove(backup_list[y][0])


            os.chdir(cwd)
            if os.path.exists(temp_backup):
                constants.safe_delete(temp_backup)

            # Enable auto save if server is running
            if server_obj: server_obj.silent_command('save-on')

            set_lock(name, False)
            send_log('backup_server', f"successfully saved a back-up of '{name}' to '{backup_file}'", 'info')
            return [file_name, convert_size(os.stat(backup_file).st_size), bkup_time]

        except Exception as e:
            send_log('backup_server', f"error saving a back-up of '{name}': {constants.format_traceback(e)}", 'error')


# name, index --> restore from file
def restore_server(name: str, backup_name: str, backup_stats=None):

    if set_lock(name, True, 'restore'):

        try:
            send_log('restore_server', f"restoring '{name}' to '{backup_name}'...", 'info')
            constants.java_check()

            if not backup_stats:
                backup_stats = dump_config(name)[1]

            cwd = constants.get_cwd()
            backup_path = backup_stats["backup-path"]

            # Reset backup path if imported to another OS
            if (':\\' in backup_path and constants.os_name != 'windows') or '/' in backup_path and constants.os_name == 'windows':
                backup_path = constants.backupFolder


            # If there are backups listed, restore to server
            if (len(backup_stats['backup-list']) > 0) and (os.path.basename(backup_name) in [os.path.basename(backup[0]) for backup in backup_stats['backup-list']]):

                os.chdir(manager.server_path(name))
                file_path = os.path.join(backup_path, os.path.basename(backup_name))


                # Delete all files in server directory
                for f in glob(os.path.join(manager.server_path(name), '*')):
                    try:
                        if os.path.isdir(f):
                            constants.safe_delete(f)
                        else:
                            os.remove(f)

                    # Log issues to console during debug
                    except Exception as e:
                        if constants.debug:
                            print(f'Error deleting file/folder during restore: {e}')



                # Restore backup
                constants.run_proc(f'tar -xf "{file_path}"')


                # Rename auto-mcs.ini to provide xplat support
                if constants.os_name == 'windows':
                    if os.path.exists('.auto-mcs.ini'):
                        os.rename('.auto-mcs.ini', 'auto-mcs.ini')
                        constants.run_proc(f"attrib +H \"{constants.server_ini}\"")
                else:
                    if os.path.exists('auto-mcs.ini'):
                        os.rename('auto-mcs.ini', '.auto-mcs.ini')


                # Disable auto-updates to prevent the backup from getting overwritten immediately, also keep backup path
                config_file = manager.server_config(name)
                config_file.set("general", "updateAuto", "false")
                config_file.set("bkup", "bkupDir", backup_path)
                manager.server_config(name, config_file)


                # Fix start.bat/start.sh
                if os.path.exists(f'{constants.start_script_name}.bat'):
                    os.remove(f'{constants.start_script_name}.bat')
                if os.path.exists(f'{constants.start_script_name}.sh'):
                    os.remove(f'{constants.start_script_name}.sh')

                properties = {'name': name, 'type': config_file.get('general', 'serverType'), 'version': config_file.get('general', 'serverVersion')}
                manager.generate_run_script(properties)

                os.chdir(cwd)
                set_lock(name, False)

                # Reload update_list
                constants.server_manager.check_for_updates()

                send_log('restore_server', f"successfully restored '{name}' to '{backup_name}'", 'info')
                return [os.path.basename(backup_name), convert_size(os.stat(file_path).st_size), convert_date(os.stat(file_path).st_mtime)]

        except Exception as e:
            send_log('restore_server', f"error restoring '{name}' to '{backup_name}': {constants.format_traceback(e)}", 'error')


# Migrate backup directory and backups
def set_backup_directory(name: str, new_dir: str, new_amount: str):

    cwd = constants.get_cwd()
    config_file = manager.server_config(name)
    current_dir = config_file.get('bkup', 'bkupDir')
    current_dir = current_dir.replace(r"/","\\") if constants.os_name == 'windows' else current_dir
    new_dir = new_dir.replace(r"/","\\") if constants.os_name == 'windows' else new_dir

    if set_lock(name, True, 'migrate'):

        # Don't allow any folders inside of app path unless it's the Backups directory
        send_log('set_backup_directory', f"changing back-up directory for '{name}' to '{new_dir}'...", 'info')
        try:
            if ((constants.applicationFolder not in new_dir) or (new_dir == os.path.join(constants.applicationFolder, 'Backups'))) and (new_dir != current_dir):

                # Check if folder exists and is writeable
                constants.folder_check(new_dir)
                if os.access(new_dir, os.W_OK):

                    # Migrate backup directory and backups
                    extract_folder = os.path.join(constants.tempDir, 'bkup_tmp')

                    # Iterate over each back-up that could be a match in current back-up directory
                    for file in glob(os.path.join(current_dir, f"{name}__*")):
                        constants.folder_check(extract_folder)
                        os.chdir(extract_folder)

                        # Extract auto-mcs.ini from each match and check the server name just to be sure
                        constants.run_proc(f'tar -xvf "{file}"')  # *auto-mcs.ini

                        configs = glob(os.path.join(extract_folder, 'auto-mcs.ini'))
                        configs.extend(glob(os.path.join(extract_folder, '.auto-mcs.ini')))
                        for cfg in configs:
                            config = constants.configparser.ConfigParser(allow_no_value=True, comment_prefixes=';')
                            config.optionxform = str
                            config.read(cfg)
                            if config:
                                if config.get('general', 'serverName') == name:

                                    # Update bkupDir with new_dir in the back-ups' auto-mcs.ini
                                    config.set('bkup', 'bkupDir', new_dir)
                                    with open(cfg, 'w') as f:
                                        config.write(f)

                                    constants.run_proc(f'tar -cvf \"{os.path.join(new_dir, os.path.basename(file))}\" {"*" if constants.os_name == "windows" else "* .??*"}')

                                    # constants.copy(file, new_dir)
                                    os.remove(file)
                                    break

                        os.chdir(constants.tempDir)
                        constants.safe_delete(extract_folder)


                    # Update bkupDir
                    os.chdir(cwd)
                    constants.safe_delete(constants.tempDir)
                    config_file.set('bkup', 'bkupDir', new_dir)
                    config_file.set('bkup', 'bkupMax', str(new_amount))
                    manager.server_config(name, config_file)

                    send_log('set_backup_directory', f"successfully changed back-up directory for '{name}' to '{new_dir}'", 'info')
                    set_lock(name, False)
                    return new_dir

        except Exception as e:
            send_log('set_backup_directory', f"error changing back-up directory for '{name}' to '{new_dir}': {constants.format_traceback(e)}", 'error')

    set_lock(name, False)
    return None


# Migrate backup names when server is renamed
def rename_backups(name: str, new_name: str):
    if set_lock(name, True, 'migrate'):
        config_file = manager.server_config(new_name)
        current_dir = config_file.get('bkup', 'bkupDir')
        current_dir = current_dir.replace(r"/", "\\") if constants.os_name == 'windows' else current_dir
        file_list   = glob(os.path.join(current_dir, f"{name}__*"))
        failure     = False

        if file_list:
            send_log('rename_backups', f"renaming all back-ups for '{name}' to '{new_name}'...", 'info')

            # Iterate over each back-up that could be a match in current back-up directory
            for file in file_list:
                if not rename_backup(file, new_name): failure = True

            # Cleanup
            constants.safe_delete(constants.tempDir)
            set_lock(name, False)

            if failure: send_log('rename_backups', f"there were errors while renaming all back-ups for '{name}' to '{new_name}'", 'error')
            else:       send_log('rename_backups', f"successfully renamed all back-ups for '{name}' to '{new_name}'", 'info')
            return not failure

    send_log('rename_backups', f"skipped renaming back-ups due to an active back-up lock for '{name}'", 'warning')
    set_lock(name, False)
    return None
def rename_backup(file: str, new_name: str):
    cwd = constants.get_cwd()
    current_dir = os.path.dirname(file)
    name = os.path.basename(file).split('__')[0].strip()

    # Migrate backup directory and backups
    extract_folder = os.path.join(constants.tempDir, 'bkup_tmp')
    new_path = None
    send_log('rename_backup', f"renaming back-up '{file}' to '{new_name}'...", 'info')

    try:
        constants.folder_check(extract_folder)
        os.chdir(extract_folder)

        # Extract auto-mcs.ini from each match and check the server name just to be sure
        constants.run_proc(f'tar -xvf "{file}"')  # *auto-mcs.ini

        config_files = []
        config_files.extend(glob(os.path.join(extract_folder, 'auto-mcs.ini')))
        config_files.extend(glob(os.path.join(extract_folder, '.auto-mcs.ini')))

        for cfg in config_files:
            config = constants.configparser.ConfigParser(allow_no_value=True, comment_prefixes=';')
            config.optionxform = str
            config.read(cfg)

            if config:
                if config.get('general', 'serverName') == name:

                    # Update bkupDir with new_dir in the back-ups' auto-mcs.ini
                    config.set('general', 'serverName', new_name)
                    with open(cfg, 'w') as f:
                        config.write(f)

                    os.remove(file)
                    new_path = os.path.join(current_dir, os.path.basename(file).replace(f"{name}__", f"{new_name}__"))
                    constants.run_proc(f'tar -cvf \"{new_path}\" {"*" if constants.os_name == "windows" else "* .??*"}')
                    break

    except Exception as e:
        send_log('rename_backup', f"error renaming back-up '{file}' to '{new_name}': {constants.format_traceback(e)}", 'error')

    if new_path: send_log('rename_backup', f"successfully renamed back-up '{file}' to '{new_name}'", 'info')

    os.chdir(cwd)
    constants.safe_delete(extract_folder)
    return new_path


# Sets maximum backup limit
# amount: <int> or 'unlimited'
def set_backup_amount(name: str, amount: int or str):

    # Try to convert to an integer if possible
    try: amount = int(amount)
    except: pass

    if str(amount) == "unlimited" or isinstance(amount, int):
        config_file = manager.server_config(name)
        config_file.set("bkup", "bkupMax", str(amount))
        manager.server_config(name, config_file)

        return amount

    else: return manager.server_config(name).get("bkup", "bkupMax")


# Toggle auto backup status
def enable_auto_backup(name: str, enabled=True):
    config_file = manager.server_config(name)
    config_file.set("bkup", "bkupAuto", str(enabled).lower())
    manager.server_config(name, config_file)

    return enabled


# Set back-up lock to prevent collisions or corruption
def set_lock(name: str, add=True, reason=None) -> bool:

    # Add lock record for server
    if add:
        timeout = 20
        while timeout > 0:

            if name not in constants.backup_lock:
                constants.backup_lock[name] = reason
                send_log('set_lock', f"added lock for '{name}': {reason}")
                return True

            time.sleep(1)
            timeout -= 1

        send_log('set_lock', f"failed to acquire lock for '{name}': {reason}", 'error')
        return False


    # Remove lock record for server
    else:
        if name in constants.backup_lock:
            del constants.backup_lock[name]
            send_log('set_lock', f"removed lock from '{name}'")
        return name not in constants.backup_lock



# ----------------------------------------------- Usage Examples -------------------------------------------------------

# backup_obj = BackupManager('1.17.1 Server')
# backup_obj.save_backup()
# backup_obj.restore_backup(r"1.17.1 Server__00.30 04-26-23.amb")
# backup_obj.enable_auto_backup(True)
# backup_obj.set_backup_directory("C:\Users\...\BackupFolder")
