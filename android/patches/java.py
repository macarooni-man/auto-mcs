# Android-only Java and server process patches. Desktop source is never modified.

def register(source, SourcePatch):
    java = SourcePatch(source / 'core' / 'tools' / 'java.py')

    java.prepend(
        'JavaManager.set_vendor',
        """if constants.is_android:
    from android_java import AndroidJavaVersion
    self.supported_vendors = ['android']
    self.versions = [AndroidJavaVersion(version) for version in (25, 21, 17, 8)]
    constants.app_config.java_vendor = 'android'
    self._send_log(f"Loaded Android Java providers: {self.versions}")
    return True""",
        'use Android Java 8/17/21/25 providers',
    )

    java.prepend(
        'kill_process',
        """if constants.is_android:
    from android_process import kill_pid
    return kill_pid(pid, timeout)""",
        'stop Android Java processes through the hosting service',
    )

    java.prepend(
        'get_java_processes',
        """if constants.is_android:
    from android_process import java_processes
    return java_processes(path)""",
        'find Android Java processes by their service-managed working directory',
    )

    manager = SourcePatch(source / 'core' / 'server' / 'manager.py')

    manager.before(
        'ServerObject',
        """if constants.is_android:
    from android_process import Popen""",
        'use the foreground-service Popen adapter for local Android servers',
    )

    manager.prepend(
        'ServerObject.performance_stats',
        """if constants.is_android and (
    not self.run_data.get('process') or self.run_data.get('launch-time') is None
):
    return False""",
        'skip Android performance polling until a Java process is launched',
    )

    manager.before(
        'ServerManager',
        """if constants.is_android:
    _original_android_launch = ServerObject.launch

    def _android_launch(self, *args, **kwargs):
        try:
            return _original_android_launch(self, *args, **kwargs)
        except Exception:
            if not self.run_data.get('process'):
                self.running = False
                self.is_ready = False
                self.run_data.clear()
            raise

    ServerObject.launch = _android_launch""",
        'restore Android server launch state after an early subprocess failure',
    )

    manager.after_assignment(
        'generate_run_script',
        'runtime_flags',
        """if constants.is_android:
    os.makedirs(paths.os_temp, exist_ok=True)
    runtime_flags.extend([
        f'-Djava.io.tmpdir={paths.os_temp}',
        f'-Djna.tmpdir={paths.os_temp}'
    ])

    if properties['type'].lower() in ['paper', 'purpur']:
        runtime_flags.append('-DPaper.IgnoreJavaVersion=true')""",
        'inject Android temporary directory and Paper JVM compatibility flags',
        recursive=True,
    )
