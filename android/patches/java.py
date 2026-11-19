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
