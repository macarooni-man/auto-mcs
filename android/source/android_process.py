"""Popen-compatible client for the foreground Android Minecraft hosting service."""
import base64
import json
import os
import socket
import time

from jnius import autoclass


def socket_path():
    root = os.environ.get('ANDROID_PRIVATE') or os.environ.get('HOME')
    return os.path.join(root, 'tmp', 'auto-mcs-server.sock')


def _request(message, streaming=False):
    conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    conn.settimeout(10)
    try:
        conn.connect(socket_path())
        conn.sendall((json.dumps(message, separators=(',', ':')) + '\n').encode('utf-8'))
        header = b''
        while not header.endswith(b'\n'):
            byte = conn.recv(1)
            if not byte or len(header) > 65536:
                raise OSError('Invalid response from Android server service')
            header += byte
        result = json.loads(header)
        if not result.get('ok'):
            raise RuntimeError(result.get('error', 'Android server service failed'))
        if streaming:
            conn.settimeout(None)
            return result, conn
        conn.close()
        return result
    except Exception:
        conn.close()
        raise


def _start_service():
    try:
        _request({'action': 'ping'})
        return
    except (OSError, RuntimeError):
        pass

    service = autoclass('com.macarooniman.automcs.ServiceMinecraft')
    activity = autoclass('org.kivy.android.PythonActivity').mActivity
    service.start(activity, '', 'Minecraft server', 'auto-mcs is hosting a local server', '')
    for _ in range(100):
        try:
            _request({'action': 'ping'})
            return
        except (OSError, RuntimeError):
            time.sleep(0.1)
    raise RuntimeError('Android Minecraft hosting service did not become ready')


class _Input:
    def __init__(self, owner):
        self.owner = owner

    def write(self, data):
        if isinstance(data, str): data = data.encode('utf-8')
        _request({'action': 'stdin', 'id': self.owner._id,
                  'data': base64.b64encode(data).decode('ascii')})
        return len(data)

    def flush(self):
        pass

    def close(self):
        pass


class Popen:
    """The subset of subprocess.Popen consumed by ServerObject.launch()."""

    def __init__(self, args, **kwargs):
        if not kwargs.get('shell'):
            raise ValueError('Android server Popen currently requires shell=True')
        _start_service()
        result = _request({'action': 'start', 'command': args,
                           'cwd': kwargs.get('cwd')})
        self.pid = result['pid']
        self._id = result['id']
        self.returncode = None
        self.stdin = _Input(self)
        _, self._stream = _request({'action': 'stream', 'id': self._id}, streaming=True)
        self.stdout = self._stream.makefile('rb', buffering=0)
        self.stderr = None

    def poll(self):
        result = _request({'action': 'poll', 'id': self._id})
        self.returncode = result['returncode']
        return self.returncode

    def wait(self, timeout=None):
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            code = self.poll()
            if code is not None:
                return code
            if deadline is not None and time.monotonic() >= deadline:
                from subprocess import TimeoutExpired
                raise TimeoutExpired('Android Java', timeout)
            time.sleep(0.1)

    def terminate(self):
        _request({'action': 'signal', 'id': self._id, 'signal': 'TERM'})

    def kill(self):
        _request({'action': 'signal', 'id': self._id, 'signal': 'KILL'})

    def send_signal(self, signal):
        import signal as signals
        _request({'action': 'signal', 'id': self._id,
                  'signal': 'KILL' if signal == signals.SIGKILL else 'TERM'})

    def communicate(self, input=None, timeout=None):
        if input: self.stdin.write(input)
        output = self.stdout.read()
        self.wait(timeout)
        return output, None


def kill_pid(pid, timeout=10):
    _start_service()
    try:
        _request({'action': 'kill_pid', 'pid': int(pid), 'timeout': timeout})
        return True
    except (OSError, RuntimeError):
        return False


def java_processes(path):
    """Return service-owned Java processes launched in a server directory."""
    import psutil
    _start_service()
    result = _request({'action': 'list', 'cwd': os.path.realpath(path)})
    return [psutil.Process(pid) for pid in result['pids']]
