"""
Minimal psutil compatibility layer for the auto-mcs Android Telepath client.

This intentionally covers the psutil API currently referenced by auto-mcs dev.
It is not a general replacement for psutil.
"""

from collections import namedtuple
import signal
import time
import os


__version__ = "android-shim-1.0"
STATUS_ZOMBIE = "zombie"


class Error(Exception):
    pass


class NoSuchProcess(Error):
    pass


class AccessDenied(Error):
    pass


class ZombieProcess(Error):
    pass


class TimeoutExpired(Error):
    pass


_svmem = namedtuple(
    "svmem",
    "total available percent used free active inactive buffers cached shared slab"
)

_sswap = namedtuple(
    "sswap",
    "total used free percent sin sout"
)

_scputimes = namedtuple(
    "scpufreq",
    "current min max"
)

_base_pmem = namedtuple(
    "pmem",
    "rss vms shared text lib data dirty"
)


class pmem(_base_pmem):
    __slots__ = ()

    @property
    def private(self):
        return self.rss


def _read(path, default=""):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as file:
            return file.read()
    except Exception:
        return default


def _meminfo():
    result = {}

    for line in _read("/proc/meminfo").splitlines():
        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        parts = value.split()

        try:
            number = int(parts[0])
        except Exception:
            continue

        multiplier = 1024 if len(parts) > 1 and parts[1].lower() == "kb" else 1
        result[key] = number * multiplier

    return result


def cpu_count(logical=True):
    return os.cpu_count() or 1


def cpu_freq(percpu=False):
    def value(name):
        text = _read(
            f"/sys/devices/system/cpu/cpu0/cpufreq/{name}",
            "0"
        ).strip()
        try:
            return float(text) / 1000
        except Exception:
            return 0.0

    current = value("scaling_cur_freq")
    minimum = value("cpuinfo_min_freq")
    maximum = value("cpuinfo_max_freq")

    result = _scputimes(current, minimum, maximum)
    return [result for _ in range(cpu_count())] if percpu else result


def virtual_memory():
    data = _meminfo()

    total = data.get("MemTotal", 0)
    free = data.get("MemFree", 0)
    available = data.get("MemAvailable", free)
    buffers = data.get("Buffers", 0)
    cached = data.get("Cached", 0) + data.get("SReclaimable", 0)
    used = max(total - available, 0)
    percent = (used / total * 100) if total else 0.0

    return _svmem(
        total,
        available,
        percent,
        used,
        free,
        data.get("Active", 0),
        data.get("Inactive", 0),
        buffers,
        cached,
        data.get("Shmem", 0),
        data.get("Slab", 0),
    )


def swap_memory():
    data = _meminfo()
    total = data.get("SwapTotal", 0)
    free = data.get("SwapFree", 0)
    used = max(total - free, 0)
    percent = (used / total * 100) if total else 0.0
    return _sswap(total, used, free, percent, 0, 0)


def _iter_pids():
    try:
        for name in os.listdir("/proc"):
            if name.isdigit():
                yield int(name)
    except Exception:
        return


class Process:
    def __init__(self, pid=None):
        self.pid = int(os.getpid() if pid is None else pid)
        if not os.path.isdir(f"/proc/{self.pid}"):
            raise NoSuchProcess(self.pid)
        self.info = {}

    def __repr__(self):
        return f"psutil.Process(pid={self.pid}, name='{self.name()}')"

    def _status_data(self):
        data = {}

        for line in _read(f"/proc/{self.pid}/status").splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                data[key] = value.strip()

        return data

    def name(self):
        name = _read(f"/proc/{self.pid}/comm").strip()
        if name:
            return name

        data = self._status_data()
        return data.get("Name", "")

    def cwd(self):
        try:
            return os.readlink(f"/proc/{self.pid}/cwd")
        except FileNotFoundError:
            raise NoSuchProcess(self.pid)
        except PermissionError:
            raise AccessDenied(self.pid)

    def children(self, recursive=False):
        direct = []

        for pid in _iter_pids():
            try:
                status = Process(pid)._status_data()
                if int(status.get("PPid", -1)) == self.pid:
                    direct.append(Process(pid))
            except Exception:
                pass

        if not recursive:
            return direct

        result = []
        stack = direct[:]

        while stack:
            child = stack.pop()
            result.append(child)
            try:
                stack.extend(child.children(False))
            except Exception:
                pass

        return result

    def memory_info(self):
        try:
            parts = _read(f"/proc/{self.pid}/statm").split()
            if len(parts) < 2:
                raise NoSuchProcess(self.pid)

            page = os.sysconf("SC_PAGE_SIZE")
            vms = int(parts[0]) * page
            rss = int(parts[1]) * page
            shared = int(parts[2]) * page if len(parts) > 2 else 0
            text = int(parts[3]) * page if len(parts) > 3 else 0
            data = int(parts[5]) * page if len(parts) > 5 else 0
            return pmem(rss, vms, shared, text, 0, data, 0)

        except NoSuchProcess:
            raise
        except Exception:
            return pmem(0, 0, 0, 0, 0, 0, 0)

    def _cpu_ticks(self):
        content = _read(f"/proc/{self.pid}/stat")
        end = content.rfind(")")

        if end < 0:
            raise NoSuchProcess(self.pid)

        fields = content[end + 2:].split()
        return float(fields[11]) + float(fields[12])

    @staticmethod
    def _total_cpu_ticks():
        line = _read("/proc/stat").splitlines()[0]
        return sum(float(part) for part in line.split()[1:])

    def cpu_percent(self, interval=None):
        start_proc = self._cpu_ticks()
        start_total = self._total_cpu_ticks()

        delay = 0.1 if interval is None else max(float(interval), 0)
        if delay:
            time.sleep(delay)

        end_proc = self._cpu_ticks()
        end_total = self._total_cpu_ticks()

        delta_total = end_total - start_total
        if delta_total <= 0:
            return 0.0

        return ((end_proc - start_proc) / delta_total) * 100 * cpu_count()

    def is_running(self):
        return os.path.isdir(f"/proc/{self.pid}")

    def status(self):
        state = self._status_data().get("State", "")
        if not state:
            raise NoSuchProcess(self.pid)
        return STATUS_ZOMBIE if state.startswith("Z") else state.split()[0]

    def terminate(self):
        try:
            os.kill(self.pid, signal.SIGTERM)
        except ProcessLookupError:
            raise NoSuchProcess(self.pid)
        except PermissionError:
            raise AccessDenied(self.pid)

    def kill(self):
        try:
            os.kill(self.pid, signal.SIGKILL)
        except ProcessLookupError:
            raise NoSuchProcess(self.pid)
        except PermissionError:
            raise AccessDenied(self.pid)

    def wait(self, timeout=None):
        start = time.monotonic()

        while self.is_running():
            if timeout is not None and time.monotonic() - start >= timeout:
                raise TimeoutExpired(timeout)
            time.sleep(0.05)

        return 0


def process_iter(attrs=None, ad_value=None):
    attrs = attrs or []

    for pid in _iter_pids():
        try:
            process = Process(pid)

            if attrs:
                data = {}

                for attr in attrs:
                    try:
                        if attr == "pid":
                            data[attr] = pid
                        elif attr == "name":
                            data[attr] = process.name()
                        elif attr == "exe":
                            data[attr] = os.readlink(f"/proc/{pid}/exe")
                        elif attr == "cwd":
                            data[attr] = process.cwd()
                        else:
                            value = getattr(process, attr)
                            data[attr] = value() if callable(value) else value
                    except Exception:
                        data[attr] = ad_value

                process.info = data

            yield process

        except (NoSuchProcess, AccessDenied, ZombieProcess):
            continue


def wait_procs(procs, timeout=None, callback=None):
    gone = []
    alive = []
    deadline = None if timeout is None else time.monotonic() + timeout

    for process in procs:
        while process.is_running():
            if deadline is not None and time.monotonic() >= deadline:
                alive.append(process)
                break
            time.sleep(0.05)
        else:
            gone.append(process)
            if callback:
                callback(process)

    return gone, alive
