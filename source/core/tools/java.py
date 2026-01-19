from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time
import os

from source.core import constants
from source.core.constants import (

    # Directories
    paths,

    # General methods
    folder_check, safe_delete, run_proc, download_url, extract_archive, format_traceback,
    dTimer,

    # Constants
    os_name
)


# Auto-MCS Java integration
# ---------------------------------------------- Java Integration ------------------------------------------------------

# Abstracts and combines network/disk operations for a single Java version
class JavaVersion():
    _lock: threading.Lock

    # Java version/vendor type
    version:       int
    type:          str

    # Paths where this version should be installed
    directory:     str
    _bin_dir:      str

    # Path to 'java' executable
    exec_path:     str

    # Path to 'jar' executable
    jar_exec_path: str

    # Legacy auto-mcs tag name
    _legacy_name:  str

    # Store the correct download link for arch/OS
    _download_url: str
    _install_pct:  float

    # Store the Alpine apk package name
    _apk_name:     str


    # Full usage name for directory/firewall
    @property
    def full_name(self) -> str:
        return f'{self.type}-java{self.version}'

    # Legacy string for launch flags
    @property
    def flag_name(self) -> str: return f'<java{self.version}>'

    # Internal log wrapper
    def _send_log(self, message: str, level: str = None):
        from source.core import logger
        return logger.send_log(f'{__name__}.{self.__class__.__name__}', message, level, 'java')

    def __init__(self):

        # Version must be set prior to init
        if not hasattr(self, 'version'):
            raise ValueError(f'{type(self).__name__} must define class attribute: version')

        # For tracking download progress
        self._lock = threading.Lock()
        self._install_pct = 0.0


        # Gather paths to where Java is installed internally
        self.directory = os.path.join(paths.java, self.full_name)
        if constants.is_docker:
            # /usr/lib/jvm/java-21-openjdk
            # /usr/lib/jvm/java-1.8-openjdk
            version_name: str = f'1.{self.version}' if self.version <= 8 else str(self.version)
            self.directory    = f'/usr/lib/jvm/java-{version_name}-openjdk'


        # Set expected executable paths directly
        if os_name == 'macos':
            self._bin_dir     = os.path.join(self.directory, 'Contents', 'Home', 'bin')
            self.exec_path     = os.path.join(self._bin_dir, 'java')
            self.jar_exec_path = os.path.join(self._bin_dir, 'jar')

        elif os_name == 'linux':
            self._bin_dir     = os.path.join(self.directory, 'bin')
            self.exec_path     = os.path.join(self._bin_dir, 'java')
            self.jar_exec_path = os.path.join(self._bin_dir, 'jar')

        else:  # Windows
            self._bin_dir     = os.path.join(self.directory, 'bin')
            self.exec_path     = os.path.join(self._bin_dir, 'java.exe')
            self.jar_exec_path = os.path.join(self._bin_dir, 'jar.exe')

    def __repr__(self): return f'<JavaVersion-{self.version}>'


    # ----- OS/filesystem handling -----
    # Check if the version is installed
    def _is_installed(self) -> bool:
        return os.path.isfile(self.exec_path)

    # Ensures that the primary Java binary is installed properly and CLI accessible
    def validate(self) -> bool:
        return self._is_installed() and run_proc(f'"{os.path.abspath(self.exec_path)}" -version') == 0

    # Download and install the version (make sure apk/Docker doesn't install concurrently)
    def install(self, progress_func: callable = None) -> bool:
        with self._lock:

            # No-op if installation validates successfully
            if self.validate():
                self._install_pct = 100
                if progress_func: progress_func(100)
                return True


            self._send_log(f"installing Java {self.version} from '{self._download_url}' to '{self.directory}'...")
            self._install_pct = 0.0

            # Install via apk; do not run concurrently
            if constants.is_docker:
                run_proc(f"apk add {self._apk_name}", True)
                return self.validate()

            if not constants.app_online:
                log_content = "Downloading Java requires an internet connection"
                self._send_log(log_content, 'error')
                raise ConnectionError(log_content)

            # If legacy path is present, delete it
            if getattr(self, '_legacy_name', ''):
                legacy_path = os.path.join(paths.java, self._legacy_name)
                if os.path.exists(legacy_path):
                    self._send_log(f"removing legacy version in '{legacy_path}'", 'info')
                    safe_delete(legacy_path)

            # Delete current version first
            if os.path.exists(self.directory): safe_delete(self.directory)


            # Download determined URL to downloads folder first
            def download_hook(a, b, c):
                if not c: return
                self._install_pct = max(min(round(100 * a * b / c), 100), 0)
                if progress_func: progress_func(self._install_pct)
            file_name = f'{self.full_name}.{os.path.basename(self._download_url).split(".", 1)[1]}'
            folder_check(paths.downloads)
            download_url(self._download_url, file_name, paths.downloads, download_hook)

            # Extract to position
            folder_check(self.directory)
            extract_archive(os.path.join(paths.downloads, file_name), self.directory, True)


            # chmod if UNIX-based
            if os_name != 'windows':
                run_proc(f'chmod +x "{self.exec_path}"')
                run_proc(f'chmod +x "{self.jar_exec_path}"')

            if progress_func: progress_func(100)

            success = self.validate()
            if success: self._send_log(f"successfully installed Java {self.version} to '{self.directory}'")
            else:       self._send_log(f"something went wrong installing Java {self.version} from '{self._download_url}'", 'error')

            return success

    # Removes the version from the filesystem
    def uninstall(self) -> bool:
        with self._lock:

            if not os.path.exists(self.directory):
                self._send_log(f"can't uninstall as Java {self.version} isn't installed")
                return True

            self._send_log(f"deleting Java {self.version} from '{self.directory}'", 'info')

            # Remove via apk; do not run concurrently
            if constants.is_docker:
                run_proc(f"apk del {self._apk_name}", True)
                return not self.validate()

            if os.path.exists(self.directory):
                safe_delete(self.directory)

            return not self.validate()

    # Updates the version to latest
    def update(self) -> bool:
        success = False

        if os.path.exists(self.directory):
            try:
                uninstalled = self.uninstall()
                installed   = self.install()
                success = uninstalled and installed

            except Exception as e:
                self._send_log(f'failed to update Java {self.version}: {format_traceback(e)}', 'error')

            if success: self._send_log(f'successfully updated Java {self.version}')

        return success


# Manages installations, and chooses a Java runtime version for each Minecraft version
class JavaManager():

    # Max download retries on failure
    _max_retries: int = 3
    _retries:     int = 0

    # List of all installable versions
    versions: list[JavaVersion]

    # List of all valid versions
    @property
    def valid_versions(self) -> list[JavaVersion]:
        return [v for v in self.versions if v.validate()]

    @property
    def latest(self) -> JavaVersion:
        latest = self.versions[0]
        if not latest.validate(): latest.install()
        return latest

    # Internal log wrapper
    def _send_log(self, message: str, level: str = None):
        from source.core import logger
        return logger.send_log(f'{__name__}.{self.__class__.__name__}', message, level, 'java')

    def __init__(self):
        self.versions: list[JavaVersion] = sorted(
            (cls() for cls in JavaVersion.__subclasses__()),
            key = lambda j: j.version,
            reverse = True
        )

        print(self.versions)


    # Attempt to resolve a <java> launch flag string or number to a JavaVersion object
    def resolve(self, name: str | int) -> JavaVersion | None:
        for version in self.versions:
            if str(name) in [str(version.version), version.flag_name]:
                return version

    # Accepts a list, or several JavaVersions to download concurrently
    def check_installed(self, to_check: list[JavaVersion] = None, progress_func: callable = None) -> bool:

        # List of versions to install
        to_install: list[JavaVersion] = to_check if to_check else self.versions
        def success() -> bool: return all([v.validate() for v in to_install])
        self._send_log(f"validating Java installations...", 'info')


        while True:

            # Delete downloads folder
            safe_delete(paths.downloads)

            # If max_retries exceeded, give up
            if self._retries > self._max_retries:
                self._send_log(f"{to_install} failed to download or install", 'error')
                return False

            # Check if the installations function before doing anything else
            if success():
                self._send_log(f"valid Java installations detected", 'info')
                if progress_func: progress_func(100)
                return True



            # Java isn't installed or can't execute
            self._send_log(f"Java is not detected, installing {to_install}...", 'info')

            # On Docker, use apk to install all Java versions instead
            if constants.is_docker:
                version_str: str = ' '.join([v._apk_name for v in to_install])
                run_proc(f'apk add {version_str}', True)
                continue


            # Use built-in installer method for all versions
            else:

                # Sum total completion percent for all versions
                def avg_total(*args):
                    while True:
                        total_progress: float = max(min(round(
                            sum([v._install_pct for v in to_install]) / len(to_install)
                        ), 100), 0)

                        progress_func(total_progress)
                        time.sleep(0.2)

                        if total_progress == 100: break

                if progress_func:
                    timer = dTimer(0, function=avg_total)
                    timer.start()

                with ThreadPoolExecutor(max_workers=len(to_install)) as pool:
                    futures = [pool.submit(v.install) for v in to_install]

                    # Raise if install() raised
                    for f in as_completed(futures): f.result()

                if progress_func:
                    timer.cancel()

            self._retries += 1

# Global Java manager
manager: JavaManager | None = None

def init_manager():
    global manager
    if not manager: manager = JavaManager()



# ----------------------------------------- Supported Oracle Versions --------------------------------------------------

class OracleJava25(JavaVersion):

    # Java version/vendor type
    version:       int = 25
    type:          str = 'oracle'

    # Legacy auto-mcs tag name
    _legacy_name:  str = ''

    # Store the Alpine apk package name
    _apk_name:     str = 'openjdk25'

    def __init__(self):
        super().__init__()

        # Automatically parse the correct link for arch/OS
        url_base: str = f'https://download.oracle.com/java/{self.version}/latest/jdk-{self.version}'
        self._download_url: str = {

            # Windows x64 binary
            'windows':               f'{url_base}_windows-x64_bin.zip',

            # macOS x64 binary
            'macos':                 f'{url_base}_macos-x64_bin.tar.gz',

            # Linux arm64 binary
            'linux':                 f'{url_base}_linux-aarch64_bin.tar.gz'

            # Linux x64 binary
            if constants.is_arm else f'{url_base}_linux-x64_bin.tar.gz',

        }[os_name]


class OracleJava21(JavaVersion):

    # Java version/vendor type
    version:       int = 21
    type:          str = 'oracle'

    # Legacy auto-mcs tag name
    _legacy_name:  str = 'modern'

    # Store the Alpine apk package name
    _apk_name:     str = 'openjdk21'

    # Set up version-specific data
    def __init__(self):
        super().__init__()

        # Automatically parse the correct link for arch/OS
        url_base: str = f'https://download.oracle.com/java/{self.version}/latest/jdk-{self.version}'
        self._download_url: str = {

            # Windows x64 binary
            'windows':               f'{url_base}_windows-x64_bin.zip',

            # macOS x64 binary
            'macos':                 f'{url_base}_macos-x64_bin.tar.gz',

            # Linux arm64 binary
            'linux':                 f'{url_base}_linux-aarch64_bin.tar.gz'

            # Linux x64 binary
            if constants.is_arm else f'{url_base}_linux-x64_bin.tar.gz',

        }[os_name]


class OracleJava17(JavaVersion):

    # Java version/vendor type
    version:       int = 17
    type:          str = 'oracle'

    # Legacy auto-mcs tag name
    _legacy_name:  str = 'lts'

    # Store the Alpine apk package name
    _apk_name:     str = 'openjdk17'

    # Set up version-specific data
    def __init__(self):
        super().__init__()

        # Automatically parse the correct link for arch/OS
        url_base: str = f'https://download.oracle.com/java/{self.version}/archive/jdk-{self.version}.0.12'
        self._download_url: str = {

            # Windows x64 binary
            'windows':               f'{url_base}_windows-x64_bin.zip',

            # macOS x64 binary
            'macos':                 f'{url_base}_macos-x64_bin.tar.gz',

            # Linux arm64 binary
            'linux':                 f'{url_base}_linux-aarch64_bin.tar.gz'

            # Linux x64 binary
            if constants.is_arm else f'{url_base}_linux-x64_bin.tar.gz',

        }[os_name]


class OracleJava8(JavaVersion):

    # Java version/vendor type
    version:       int = 8
    type:          str = 'oracle'

    # Legacy auto-mcs tag name
    _legacy_name:  str = 'legacy'

    # Store the Alpine apk package name
    _apk_name:     str = 'openjdk8'

    # Set up version-specific data
    def __init__(self):
        super().__init__()

        # Automatically parse the correct link for arch/OS
        url_base: str = 'https://javadl.oracle.com/webapps/download/GetFile/1.8.0_331-b09/165374ff4ea84ef0bbd821706e29b123'
        self._download_url: str = {

            # Windows x64 binary
            'windows':               f'{url_base}/windows-i586/jre-8u331-windows-x64.tar.gz',

            # macOS x64 binary
            'macos':                 f'{url_base}/unix-i586/jre-8u331-macosx-x64.tar.gz',

            # Linux arm64 binary
            'linux':                 f'{url_base}/linux-i586/jdk-8u331-linux-aarch64.tar.gz'

            # Linux x64 binary
            if constants.is_arm else f'{url_base}/linux-i586/jre-8u331-linux-x64.tar.gz'

        }[os_name]
