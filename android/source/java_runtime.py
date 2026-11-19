"""Android-only Java runtime provider. The desktop JavaManager stays unchanged."""
from pathlib import Path
import hashlib
import os
import re
import ssl
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request
import certifi

from source.core.tools.java import JavaVersion
from source.core.constants import paths


# GitHub release assets published by AngelAuraMC. Pin digests, not just URLs.
SHA256 = {
    8:  "9a59124d9791957d55c68be664ab76831f336cf2e1e1cd4414220c6fdbf0e06d",
    17: "e162c860fe05ee4a4e4af7606437419879f6c748386a7b09fa77d10db6a64091",
    21: "8d41ec401ee59f7722df60ed991f81ad146e130452804bfdd8a05d3436f7bbfe",
    25: "d3eb7afe2240c26728a1bb440502c5f18ac3883e932d202dd7f0c9bcbbce4c37",
}


def native_library(name):
    from jnius import autoclass
    activity = autoclass('org.kivy.android.PythonActivity').mActivity
    return os.path.join(str(activity.getApplicationInfo().nativeLibraryDir), name)


def java_environment(version: int):
    env = os.environ.copy()
    home = os.path.join(paths.java, f'android-java{version}')
    folders = [
        'lib/jli', 'lib/server', 'lib', 'lib/aarch64/jli',
        'lib/aarch64/server', 'lib/aarch64',
        'jre/lib/aarch64/jli', 'jre/lib/aarch64/server', 'jre/lib/aarch64'
    ]
    env['AUTO_MCS_JAVA_ROOT'] = paths.java
    env['JAVA_HOME'] = home
    env['LD_LIBRARY_PATH'] = os.pathsep.join(
        [os.path.join(home, folder) for folder in folders]
        + [env.get('LD_LIBRARY_PATH', '')]
    )
    env.setdefault('TMPDIR', paths.os_temp)
    return env


class AndroidJavaVersion(JavaVersion):
    vendor = 'android'
    _legacy_name = ''
    _apk_name = ''

    def __init__(self, version: int):
        if version not in SHA256:
            raise ValueError(f'Unsupported Android Java version: {version}')

        self.version = version
        super().__init__()

        self.exec_path = native_library(f'libautomcsjava{version}.so')
        self.jar_exec_path = self.exec_path
        self._download_url = (
            'https://github.com/AngelAuraMC/angelauramc-openjdk-build/'
            f'releases/download/download_jre{version}/jre{version}-android-arm64.tar.xz'
        )
        self._validated = False

    def _runtime_library(self, name: str) -> str | None:
        for parent in (
            'lib', 'lib/jli', 'lib/server', 'lib/aarch64', 'lib/aarch64/jli',
            'lib/aarch64/server', 'jre/lib/aarch64', 'jre/lib/aarch64/jli',
            'jre/lib/aarch64/server'
        ):
            path = os.path.join(self.directory, parent, name)
            if os.path.isfile(path):
                return path
        return None

    @property
    def is_installed(self) -> bool:
        return (
            os.path.isfile(self.exec_path)
            and os.path.isfile(os.path.join(self.directory, 'release'))
            and self._runtime_library('libjvm.so') is not None
            and self._runtime_library('libjli.so') is not None
        )

    def validate(self) -> bool:
        if not self.is_installed:
            self._validated = False
            return False
        if self._validated:
            return True

        try:
            result = subprocess.run(
                [self.exec_path, '-version'],
                env=java_environment(self.version), stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, timeout=30, check=False
            )
            output = result.stdout.decode('utf-8', errors='replace')
            match = re.search(r'(?:java|openjdk) version "([^"]+)"', output, re.I)
            if not match:
                match = re.search(r'openjdk\s+(\d+(?:\.\d+)*)', output, re.I)
            if match:
                major = match.group(1).split('.')
                installed = int(major[1] if major[0] == '1' else major[0])
                self._validated = result.returncode == 0 and installed == self.version
            else:
                self._send_log(f"Java {self.version} launcher returned: {output[-1500:]}", 'warning')
        except (OSError, subprocess.TimeoutExpired) as exc:
            self._send_log(f"Could not execute Android Java {self.version}: {exc}", 'warning')
        return self._validated

    def _unpack_java8(self, folder: Path):
        packed = sorted(folder.rglob('*.pack'))
        if not packed:
            return

        executable = native_library('libunpack200.so')
        if not os.path.isfile(executable):
            raise RuntimeError('Java 8 needs the bundled Android unpack200 executable')

        for path in packed:
            output = path.with_suffix('.jar')
            result = subprocess.run(
                [executable, '-r', str(path), str(output)],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120
            )
            if result.returncode != 0 or not output.is_file():
                message = result.stdout.decode('utf-8', errors='replace')
                raise RuntimeError(f'Failed to unpack Java 8 {path.name}: {message[-1000:]}')

    def install(self, progress_func: callable = None) -> bool:
        with self._lock:
            if self.validate():
                self._install_pct = 100
                if progress_func: progress_func(100)
                return True

            os.makedirs(paths.java, exist_ok=True)
            self._install_pct = 0
            working = Path(tempfile.mkdtemp(prefix=f'.android-java{self.version}-', dir=paths.java))
            archive = working / 'runtime.tar.xz'
            extract = working / 'extract'
            extract.mkdir()
            try:
                digest = hashlib.sha256()
                request = urllib.request.Request(self._download_url, headers={'User-Agent': 'auto-mcs Android'})
                with urllib.request.urlopen(request, timeout=45, context=ssl.create_default_context(cafile=certifi.where())) as response, archive.open('wb') as output:
                    length = int(response.headers.get('Content-Length') or 0)
                    received = 0
                    while True:
                        chunk = response.read(1024 * 512)
                        if not chunk: break
                        output.write(chunk)
                        digest.update(chunk)
                        received += len(chunk)
                        if length:
                            self._install_pct = min(90, (received * 90 / length))
                            if progress_func: progress_func(self._install_pct)

                if digest.hexdigest() != SHA256[self.version]:
                    raise RuntimeError('Android JRE download failed SHA-256 validation')

                with tarfile.open(archive, mode='r:xz') as package:
                    package.extractall(extract, filter='data')

                # Upstream archives may contain an enclosing top-level directory.
                if not (extract / 'release').is_file():
                    candidates = list(extract.rglob('release'))
                    if len(candidates) != 1:
                        raise RuntimeError('Android JRE archive has no unambiguous release file')
                    extract = candidates[0].parent

                release = (extract / 'release').read_text(encoding='utf-8', errors='replace')
                match = re.search(r'^JAVA_VERSION="([^"]+)"', release, re.M)
                if not match:
                    raise RuntimeError('Android JRE release metadata is missing JAVA_VERSION')
                version = match.group(1).split('.')
                major = int(version[1] if version[0] == '1' else version[0])
                if major != self.version:
                    raise RuntimeError(f'Expected Java {self.version}, got {match.group(1)}')

                if self.version == 8:
                    self._unpack_java8(extract)

                # Swap in a complete verified runtime, never a partially downloaded one.
                if os.path.exists(self.directory):
                    shutil.rmtree(self.directory)
                shutil.move(str(extract), self.directory)
                self._validated = False
                if not self.validate():
                    raise RuntimeError(f'Android Java {self.version} files installed but JVM launch failed')

                self._install_pct = 100
                if progress_func: progress_func(100)
                self._send_log(f'Installed Android Java {self.version}', 'info')
                return True
            except Exception as exc:
                self._validated = False
                self._send_log(f'Unable to install Android Java {self.version}: {exc}', 'error')
                raise
            finally:
                shutil.rmtree(working, ignore_errors=True)

    def uninstall(self) -> bool:
        with self._lock:
            if os.path.isdir(self.directory):
                shutil.rmtree(self.directory)
            self._validated = False
            return not self.is_installed
