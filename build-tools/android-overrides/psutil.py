"""
Custom psutil implementation for Android.
This module provides a minimal compatibility layer that implements the following functions:
  - virtual_memory()        (returns an object with attributes: total, available, percent, used, free)
  - cpu_count()
and a Process class with methods:
  - name()
  - children(recursive: bool)
  - cpu_percent(interval: float)
  - memory_info()

This implementation is pure Python and uses basic Linux interfaces (e.g. /proc) so it avoids native code issues.
"""

import os
import sys
import time
from collections import namedtuple

__version__ = "0.1.0"

# Named tuples for memory and process memory info
svmem = namedtuple("svmem", ["total", "available", "percent", "used", "free"])
pmem = namedtuple("pmem", ["rss", "vms"])

# ------------------------------------------------------------------------------
# Functions
# ------------------------------------------------------------------------------

def cpu_count(logical=True):
    """Return the number of logical CPUs."""
    try:
        return os.cpu_count() or 1
    except Exception:
        return 1

def virtual_memory():
    """
    Return virtual memory statistics by reading /proc/meminfo.
    Returns an svmem namedtuple with total, available, percent, used, free.
    """
    try:
        meminfo = {}
        with open("/proc/meminfo", "r") as f:
            for line in f:
                parts = line.split()
                key = parts[0].rstrip(':')
                # values are in kB; convert to bytes
                meminfo[key] = int(parts[1]) * 1024

        total = meminfo.get("MemTotal", 0)
        free = meminfo.get("MemFree", 0)
        # Prefer MemAvailable if available; otherwise approximate.
        available = meminfo.get("MemAvailable", free)
        used = total - free
        percent = (used / total * 100) if total > 0 else 0.0
        return svmem(total, available, percent, used, free)
    except Exception:
        return svmem(0, 0, 0.0, 0, 0)

def process_iter():
    """
    Return a list of process IDs by listing the /proc directory.
    """
    if sys.platform.startswith("linux"):
        try:
            return [int(pid) for pid in os.listdir("/proc") if pid.isdigit()]
        except Exception:
            return []
    return []

# ------------------------------------------------------------------------------
# Process class
# ------------------------------------------------------------------------------

class Process:
    """
    Minimal Process class for Android.
    """
    def __init__(self, pid):
        self.pid = pid

    def name(self):
        """
        Return the process name by reading /proc/<pid>/comm.
        """
        try:
            with open(f"/proc/{self.pid}/comm", "r") as f:
                return f.read().strip()
        except Exception:
            return ""

    def _get_ppid(self):
        """
        Return the parent process ID by reading /proc/<pid>/status.
        """
        try:
            with open(f"/proc/{self.pid}/status", "r") as f:
                for line in f:
                    if line.startswith("PPid:"):
                        return int(line.split()[1])
        except Exception:
            return None

    def children(self, recursive=False):
        """
        Return a list of Process objects that are direct children of this process.
        If recursive is True, return all descendants.
        """
        children_list = []
        my_pid = self.pid
        for pid in process_iter():
            # Read /proc/<pid>/status to get PPid
            try:
                with open(f"/proc/{pid}/status", "r") as f:
                    for line in f:
                        if line.startswith("PPid:"):
                            ppid = int(line.split()[1])
                            if ppid == my_pid:
                                children_list.append(Process(pid))
                            break
            except Exception:
                continue

        if recursive:
            all_children = []
            for child in children_list:
                all_children.append(child)
                all_children.extend(child.children(recursive=True))
            return all_children
        else:
            return children_list

    def cpu_percent(self, interval=0.1):
        """
        Return a simple approximation of process CPU usage as a percentage over the interval.
        This function reads /proc/<pid>/stat to get user and system times, waits, then measures the difference.
        Note: This is a minimal implementation and may not be as accurate as psutil's native version.
        """
        clock_ticks = os.sysconf("SC_CLK_TCK")
        def get_cpu_times():
            try:
                with open(f"/proc/{self.pid}/stat", "r") as f:
                    content = f.read()
                # The process name is enclosed in parentheses.
                # Find the last ')' and then split the remaining fields.
                end = content.rfind(")")
                if end == -1:
                    return 0
                fields = content[end+2:].split()
                # utime is field 14 and stime is field 15 (0-indexed: 13 and 14)
                utime = float(fields[11])
                stime = float(fields[12])
                return utime + stime
            except Exception:
                return 0

        start = get_cpu_times()
        # Also record total CPU time from /proc/stat
        def get_total_cpu_time():
            try:
                with open("/proc/stat", "r") as f:
                    line = f.readline()
                # line starts with "cpu " followed by user, nice, system, idle, ...
                parts = line.split()[1:]
                return sum(float(p) for p in parts)
            except Exception:
                return 0

        total_start = get_total_cpu_time()
        time.sleep(interval)
        end = get_cpu_times()
        total_end = get_total_cpu_time()

        delta_proc = end - start
        delta_total = total_end - total_start

        # Scale percentage by number of CPUs.
        ncpu = cpu_count()
        try:
            percent = (delta_proc / delta_total) * 100 * ncpu
        except ZeroDivisionError:
            percent = 0.0
        return percent

    def memory_info(self):
        """
        Return process memory information by reading /proc/<pid>/statm.
        Returns a pmem namedtuple with rss and vms in bytes.
        """
        try:
            with open(f"/proc/{self.pid}/statm", "r") as f:
                parts = f.readline().split()
            # statm: size, resident, shared, text, lib, data, dt (all in pages)
            page_size = os.sysconf("SC_PAGE_SIZE")
            vms = int(parts[0]) * page_size
            rss = int(parts[1]) * page_size
            return pmem(rss, vms)
        except Exception:
            return pmem(0, 0)


def Process_iter():
    """
    Return an iterator of Process objects for all running processes.
    """
    for pid in process_iter():
        yield Process(pid)

# ------------------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------------------
__all__ = [
    "cpu_count", "virtual_memory", "process_iter",
    "Process", "Process_iter", "__version__"
]
