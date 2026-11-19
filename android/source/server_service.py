"""Foreground-service owner of Android Minecraft server subprocesses.

Only the UI's android_process.Popen adapter talks to this Unix socket. All
processes and stdout pipes live here, not in the Kivy Activity's process.
"""
from collections import deque
from pathlib import Path
import base64
import json
import os
import re
import signal
import socket
import subprocess
import threading
import time
import uuid


root = os.environ.get('ANDROID_PRIVATE') or os.environ.get('HOME')
work = Path(root) / 'tmp'
work.mkdir(parents=True, exist_ok=True)
ADDRESS = str(work / 'auto-mcs-server.sock')

# These environment settings are required even when the UI process is gone.
os.environ['HOME'] = root
os.environ['TMPDIR'] = str(work)
os.environ['AUTO_MCS_JAVA_ROOT'] = str(Path(root) / 'auto-mcs' / 'Tools' / 'java')

sessions = {}
lock = threading.RLock()
wake_lock = None


def _update_wake_lock():
    global wake_lock
    try:
        from jnius import autoclass, cast
        service = autoclass('org.kivy.android.PythonService').mService
        power = cast('android.os.PowerManager', service.getSystemService('power'))
        active = any(s['process'].poll() is None for s in sessions.values())
        if active and wake_lock is None:
            wake_lock = power.newWakeLock(
                autoclass('android.os.PowerManager').PARTIAL_WAKE_LOCK,
                'auto-mcs:minecraft-server'
            )
            wake_lock.acquire()
        elif not active and wake_lock is not None:
            if wake_lock.isHeld(): wake_lock.release()
            wake_lock = None
    except Exception as exc:
        print('[Android server] Wake lock:', exc, flush=True)


def _send(connection, data):
    connection.sendall((json.dumps(data, separators=(',', ':')) + '\n').encode('utf-8'))


def _pump(session):
    process = session['process']
    try:
        while True:
            chunk = os.read(process.stdout.fileno(), 65536)
            if not chunk: break
            with session['lock']:
                session['buffer'].append(chunk)
                session['buffer_size'] += len(chunk)
                while session['buffer_size'] > 2 * 1024 * 1024:
                    session['buffer_size'] -= len(session['buffer'].popleft())
                for client in list(session['streams']):
                    try: client.sendall(chunk)
                    except OSError:
                        session['streams'].remove(client)
                        client.close()
    finally:
        process.wait()
        with session['lock']:
            for client in session['streams']:
                try: client.shutdown(socket.SHUT_WR)
                except OSError: pass
                client.close()
            session['streams'].clear()
        with lock:
            _update_wake_lock()


def _stop(session, hard=False):
    process = session['process']
    if process.poll() is not None: return
    try:
        os.killpg(process.pid, signal.SIGKILL if hard else signal.SIGTERM)
    except ProcessLookupError:
        pass


def _handle(connection):
    keep_stream = False
    try:
        reader = connection.makefile('rb')
        line = reader.readline(256 * 1024)
        if not line:
            return
        request = json.loads(line)
        action = request.get('action')

        if action == 'ping':
            _send(connection, {'ok': True})
            return

        if action == 'start':
            command = request['command']
            cwd = request['cwd']
            if not isinstance(command, str) or not isinstance(cwd, str):
                raise ValueError('Missing command or working directory')
            if not os.path.isdir(cwd):
                raise FileNotFoundError(cwd)
            environment = os.environ.copy()
            version = re.search(r'libautomcsjava(8|17|21|25)\.so', command)
            if version:
                home = os.path.join(environment['AUTO_MCS_JAVA_ROOT'], f'android-java{version.group(1)}')
                folders = [
                    'lib/jli', 'lib/server', 'lib', 'lib/aarch64/jli',
                    'lib/aarch64/server', 'lib/aarch64',
                    'jre/lib/aarch64/jli', 'jre/lib/aarch64/server', 'jre/lib/aarch64'
                ]
                environment['JAVA_HOME'] = home
                # Android Python service threads cannot reliably resolve
                # org.kivy.android.PythonService with PyJNIus. The Activity
                # provides the APK native library directory over our private socket.
                native_dir = request.get('native_dir')
                if not isinstance(native_dir, str) or not os.path.isdir(native_dir):
                    raise RuntimeError('Missing Android native library directory')
                vm_dir = next(
                    (os.path.join(home, folder) for folder in folders
                     if os.path.isfile(os.path.join(home, folder, 'libjvm.so'))),
                    None
                )
                if vm_dir is None:
                    raise FileNotFoundError(f'Missing JVM library in {home}')

                environment['LD_LIBRARY_PATH'] = os.pathsep.join(
                    [vm_dir, native_dir]
                    + [os.path.join(home, folder) for folder in folders]
                    + [environment.get('LD_LIBRARY_PATH', '')]
                )
            process = subprocess.Popen(
                command, cwd=cwd, env=environment, shell=True, stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                start_new_session=True, bufsize=0
            )
            identifier = uuid.uuid4().hex
            session = {'process': process, 'cwd': os.path.realpath(cwd), 'lock': threading.RLock(),
                       'buffer': deque(), 'buffer_size': 0, 'streams': []}
            with lock:
                sessions[identifier] = session
                _update_wake_lock()
            threading.Thread(target=_pump, args=(session,), daemon=True).start()
            _send(connection, {'ok': True, 'id': identifier, 'pid': process.pid})
            return

        if action == 'list':
            cwd = os.path.realpath(request['cwd'])
            with lock:
                pids = [s['process'].pid for s in sessions.values()
                        if s['cwd'] == cwd and s['process'].poll() is None]
            _send(connection, {'ok': True, 'pids': pids})
            return

        if action == 'kill_pid':
            pid = int(request['pid'])
            with lock:
                match = next((s for s in sessions.values()
                              if s['process'].pid == pid), None)
            if not match:
                raise ProcessLookupError(f'No managed Java process with PID {pid}')
            _stop(match)
            duration = max(0.0, min(30.0, float(request.get('timeout', 10))))
            try: match['process'].wait(timeout=duration)
            except subprocess.TimeoutExpired:
                _stop(match, hard=True)
                match['process'].wait(timeout=5)
            _send(connection, {'ok': True})
            return

        identifier = request['id']
        with lock:
            session = sessions.get(identifier)
        if session is None:
            raise ProcessLookupError('Unknown Android Java process')
        process = session['process']

        if action == 'poll':
            _send(connection, {'ok': True, 'returncode': process.poll()})
        elif action == 'stdin':
            data = base64.b64decode(request['data'], validate=True)
            process.stdin.write(data)
            process.stdin.flush()
            _send(connection, {'ok': True})
        elif action == 'signal':
            _stop(session, request.get('signal') == 'KILL')
            _send(connection, {'ok': True})
        elif action == 'stream':
            with session['lock']:
                _send(connection, {'ok': True})
                for chunk in session['buffer']:
                    connection.sendall(chunk)
                if process.poll() is None:
                    session['streams'].append(connection)
                    keep_stream = True
        else:
            raise ValueError(f'Unknown command: {action}')

    except Exception as exc:
        try: _send(connection, {'ok': False, 'error': str(exc)})
        except OSError: pass
    finally:
        if not keep_stream:
            connection.close()


def main():
    try: os.unlink(ADDRESS)
    except FileNotFoundError: pass

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(ADDRESS)
    os.chmod(ADDRESS, 0o600)
    server.listen(8)
    print('[Android server] Hosting service listening at', ADDRESS, flush=True)

    try:
        while True:
            conn, _ = server.accept()
            threading.Thread(target=_handle, args=(conn,), daemon=True).start()
    finally:
        server.close()
        try: os.unlink(ADDRESS)
        except FileNotFoundError: pass


if __name__ == '__main__':
    main()
