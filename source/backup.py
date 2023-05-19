from datetime import datetime as dt
from functools import reduce
from glob import glob
import constants
import os


# Auto-MCS Backup API
# ------------------------------------------------- Backup Object ------------------------------------------------------

# Instantiate class with "server_name" (case-sensitive)
# Houses backup functions in class
class BackupObject():

    def __init__(self, server_name: str):

        self.server, self.backup_stats = dump_config(server_name)

    # Refreshes self.backup_stats
    def update_data(self):
        self.server, self.backup_stats = dump_config(self.server['name'])


    # Backup functions

    # Backs up server to the backup directory in auto-mcs.ini
    def save_backup(self):
        backup = backup_server(self.server['name'], self.backup_stats)
        self.update_data()
        return backup

    # Restores server from file name
    def restore_backup(self, backup_name: str):
        backup = restore_server(self.server['name'], backup_name, self.backup_stats)
        self.update_data()
        return backup

    # Moves backup directory to new_path
    def set_backup_directory(self, new_path: str):
        path = set_backup_directory(self.server['name'], new_path)
        self.update_data()
        return path

    # Sets maximum backup limit
    # amount: <int> or 'unlimited'
    def set_backup_amount(self, amount):
        new_amt = set_backup_amount(self.server['name'], amount)
        self.update_data()
        return new_amt

    # Toggle auto backup status
    def enable_auto_backup(self, enabled=True):
        status = enable_auto_backup(self.server['name'], enabled)
        self.update_data()
        return status

# ---------------------------------------------- General Functions -----------------------------------------------------

# Converts os.mtime to readable format
def convert_date(m_time: int or float):
    dt_obj = dt.fromtimestamp(float(m_time))
    days = (dt.now().date() - dt_obj.date()).days
    if days == 0:
        fmt = "Today %#I:%M %p"
    elif days == 1:
        fmt = "Yesterday %#I:%M %p"
    else:
        fmt = "%a %#I:%M %p %#m/%#d/%Y"
    return dt_obj.strftime(fmt)


# Convert string to date
def convert_date_str(file_name: str):
    if file_name.endswith('.tgz'):
        return dt.strptime(file_name.split("__")[1].split(".tgz")[0], "%H.%M %m-%d-%y")
    else:
        return dt.strptime(file_name.split("__")[1].split(".amb")[0], "%H.%M %m-%d-%y")


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
        'path': os.path.join(constants.applicationFolder, 'Servers', server_name)
    }

    backup_stats = {
        'backup_path': constants.backupFolder,
        'auto_backup': 'prompt',
        'max_backup': '5',
        'latest_backup': None,
        'total_size': convert_size(0),
        'backup_list': []
    }


    config_file = constants.server_path(server_name, constants.server_ini)

    # Check auto-mcs.ini for info
    if config_file and os.path.isfile(config_file):
        server_config = constants.server_config(server_name)

        # Only pickup server as valid with good config
        if server_name == server_config.get("general", "serverName"):
            server_dict['version'] = server_config.get("general", "serverVersion")
            backup_stats['backup_path'] = str(server_config.get("bkup", "bkupDir"))
            backup_stats['auto_backup'] = str(server_config.get("bkup", "bkupAuto").lower())
            backup_stats['max_backup'] = str(server_config.get("bkup", "bkupMax"))


    # Generate backup list and metadata
    if constants.server_path(server_name):

        backup_stats['backup_list'] = sorted([[file, os.stat(file).st_size, convert_date_str(file)] for file in glob(os.path.join(backup_stats['backup_path'], f'{server_dict["name"]}__*'))], key=lambda x: x[2], reverse=True)

        try:
            backup_stats['latest_backup'] = backup_stats['backup_list'][0][2].strftime("%a %#I:%M %p %#m/%#d/%Y")
            backup_stats['total_size'] = convert_size(reduce(lambda x, y: x+y, [z[1] for z in backup_stats['backup_list']]))
        except IndexError:
            pass

        backup_stats['backup_list'] = [[file[0], convert_size(file[1]), file[2].strftime("%a %#I:%M %p %#m/%#d/%Y")] for file in backup_stats['backup_list']]


    return server_dict, backup_stats



# ---------------------------------------------- Backup Functions ------------------------------------------------------

# name --> backup to directory
def backup_server(name: str, backup_stats=None):

    if not backup_stats:
        backup_stats = dump_config(name)[1]

    cwd = os.path.abspath(os.curdir)
    time = dt.now().strftime("%H.%M %m-%d-%y")
    backup_path = backup_stats["backup_path"]
    file_name = f"{name}__{time}.amb"
    backup_file = os.path.join(backup_path, file_name)

    constants.folder_check(backup_path)
    os.chdir(constants.server_path(name))

    # Create backup
    constants.run_proc(f'tar -cvf \"{os.path.join(backup_path, "bkup.amb")}\" {"*" if constants.os_name == "windows" else "* .??*"}')
    if os.path.exists(backup_file):
        os.remove(backup_file)
    os.rename(os.path.join(backup_path, "bkup.amb"), backup_file)



    # Clear old backups if there's a limit in auto-mcs.ini
    if backup_stats['max_backup'] != "unlimited":

        keep = int(backup_stats['max_backup'])
        backup_list = sorted([[file, os.stat(file).st_mtime] for file in glob(os.path.join(backup_path, f'{name}__*'))], key=lambda x: x[1])

        delete = len(backup_list) - keep
        for y in range(0, delete):
            os.remove(backup_list[y][0])


    os.chdir(cwd)

    return [file_name, convert_size(os.stat(backup_file).st_size), time]


# name, index --> restore from file
def restore_server(name: str, backup_name: str, backup_stats=None):

    constants.java_check()

    if not backup_stats:
        backup_stats = dump_config(name)[1]

    cwd = os.path.abspath(os.curdir)
    backup_path = backup_stats["backup_path"]

    # Reset backup path if imported to another OS
    if (':\\' in backup_path and constants.os_name != 'windows') or '/' in backup_path and constants.os_name == 'windows':
        backup_path = constants.backupFolder


    # If there are backups listed, restore to server
    if (len(backup_stats['backup_list']) > 0) and (os.path.basename(backup_name) in [os.path.basename(backup[0]) for backup in backup_stats['backup_list']]):

        os.chdir(constants.server_path(name))
        file_path = os.path.join(backup_path, os.path.basename(backup_name))


        # Delete all files in server directory
        if constants.os_name == 'windows':
            constants.run_proc(f'del /q /s /f *')
        else:
            constants.run_proc('rm -rf -- ..?* .[!.]* *')


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
        config_file = constants.server_config(name)
        config_file.set("general", "updateAuto", "false")
        config_file.set("bkup", "bkupDir", backup_path)
        constants.server_config(name, config_file)


        # Fix start.bat/start.sh
        if os.path.exists(f'{constants.start_script_name}.bat'):
            os.remove(f'{constants.start_script_name}.bat')
        if os.path.exists(f'{constants.start_script_name}.sh'):
            os.remove(f'{constants.start_script_name}.sh')

        properties = {'name': name, 'type': config_file.get('general', 'serverType'), 'version': config_file.get('general', 'serverVersion')}
        constants.generate_run_script(properties)



        os.chdir(cwd)

        return [os.path.basename(backup_name), convert_size(os.stat(file_path).st_size), convert_date(os.stat(file_path).st_mtime)]


# Migrate backup directory and backups
def set_backup_directory(name: str, new_dir: str):

    cwd = os.path.abspath(os.curdir)
    config_file = constants.server_config(name)
    current_dir = config_file.get('bkup', 'bkupDir')

    # Don't allow any folders inside of app path unless it's the Backups directory
    if not (constants.applicationFolder in new_dir and new_dir != os.path.join(constants.applicationFolder, 'Backups') and new_dir != current_dir):

        # Check if folder exists and is writeable
        constants.folder_check(new_dir)
        if os.access(new_dir, os.W_OK):

            # Migrate backup directory and backups
            for file in glob(os.path.join(current_dir, "*")):
                if name in file:
                    constants.copy(file, new_dir)
                    os.remove(file)

            # Update bkupDir
            config_file.set('bkup', 'bkupDir', new_dir)
            constants.server_config(name, config_file)


            return new_dir

    return current_dir


# Sets maximum backup limit
# amount: <int> or 'unlimited'
def set_backup_amount(name: str, amount: int or str):
    if str(amount) == "unlimited" or isinstance(amount, int):
        config_file = constants.server_config(name)
        config_file.set("bkup", "bkupMax", str(amount))
        constants.server_config(name, config_file)

        return amount

    else:
        return constants.server_config(name).get("bkup", "bkupMax")


# Toggle auto backup status
def enable_auto_backup(name: str, enabled=True):
    config_file = constants.server_config(name)
    config_file.set("bkup", "bkupAuto", str(enabled).lower())
    constants.server_config(name, config_file)

    return enabled



# ----------------------------------------------- Usage Examples -------------------------------------------------------

# backup_obj = BackupObject('1.17.1 Server')
# backup_obj.save_backup()
# backup_obj.restore_backup(r"1.17.1 Server__00.30 04-26-23.amb")
# backup_obj.enable_auto_backup(True)
# backup_obj.set_backup_directory("C:\Users\...\BackupFolder")
