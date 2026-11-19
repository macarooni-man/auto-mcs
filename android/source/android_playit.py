"""Android-only Playit process adapter. The desktop PlayitManager is unchanged."""
import os
import subprocess as _subprocess

from jnius import autoclass

from android_java import native_library
from android_process import Popen as _RemotePopen, _request, _start_service


# Keep in sync with the pinned upstream Git SHA in android/build.sh.
PLAYIT_VERSION = '2.0.2'


class PlayitProcess(_RemotePopen):
    """The poll/kill/wait/PID interface used by PlayitManager._start_agent()."""

    def __init__(self, args, **kwargs):
        if len(args) != 7 or args[1::2] != ['--secret-path', '--socket-path', '--log-path']:
            raise ValueError('Unexpected Android Playit daemon arguments')

        cwd = kwargs.get('cwd')
        if not cwd or not os.path.isdir(cwd):
            raise FileNotFoundError(f'Invalid Playit working directory: {cwd}')

        if os.path.realpath(args[0]) != os.path.realpath(native_library('libautomcsplayit.so')):
            raise ValueError('Playit must use the bundled Android executable')

        _start_service()
        activity = autoclass('org.kivy.android.PythonActivity').mActivity

        result = _request({
            'action': 'playit_start',
            'cwd': cwd,
            'native_dir': str(activity.getApplicationInfo().nativeLibraryDir),
            'secret_path': args[2],
            'socket_path': args[4],
            'log_path': args[6],
        })

        self.pid = result['pid']
        self._id = result['id']
        self.returncode = None
        self.stdin = None
        self.stdout = None
        self.stderr = None


class _AndroidSubprocess:
    """Replace only the subprocess import inside the staged Playit module."""

    Popen = PlayitProcess
    DEVNULL = _subprocess.DEVNULL
    PIPE = _subprocess.PIPE


subprocess = _AndroidSubprocess()
