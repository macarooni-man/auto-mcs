# Android-only Playit executable and process integration.

def register(source, SourcePatch):
    playit = SourcePatch(source / 'core' / 'tools' / 'playit.py')

    playit.before(
        'PlayitManager',
        """if constants.is_android:
    from android_playit import PLAYIT_VERSION, native_library, subprocess""",
        'use the Android Playit foreground-service process adapter',
    )

    playit.after_assignment(
        'PlayitManager.__init__',
        'self._process_lock',
        """if constants.is_android:
    self._filename = 'libautomcsplayit.so'
    self.exec_path = native_library(self._filename)
    self._pinned_version = PLAYIT_VERSION
    self._agent_version = PLAYIT_VERSION
    self._log_path = os.path.join(paths.logs, 'playit', 'playitd.log')
    folder_check(os.path.dirname(self._log_path))""",
        'use the APK-packaged Playit daemon and its pinned version',
    )

    playit.prepend(
        'PlayitManager._load_version',
        """if constants.is_android:
    self._agent_version = PLAYIT_VERSION
    return""",
        'report the APK-bundled Playit version without reading a downloaded binary',
    )

    playit.prepend(
        'PlayitManager.install_agent',
        """if constants.is_android:
    folder_check(self.directory)
    self._agent_version = PLAYIT_VERSION
    if not self._check_agent():
        raise FileNotFoundError(f'Android Playit daemon is missing from APK: {self.exec_path}')
    if progress_func: progress_func(100)
    return True""",
        'use the bundled Playit daemon without downloading executable code',
    )

    playit.prepend(
        'PlayitManager.uninstall_agent',
        """if constants.is_android:
    # The binary belongs to the APK; only the configuration can be cleared.
    if not keep_config:
        self._reset_config()
        self.tunnel_cache.clear_cache()
    return True""",
        'keep APK-packaged Playit executable immutable on Android',
    )

    playit.prepend(
        'PlayitManager.check_for_update',
        """if constants.is_android:
    return False""",
        'the APK-bundled Playit daemon is always the current Android version',
    )

    playit.prepend(
        'PlayitManager.update_agent',
        """if constants.is_android:
    self._agent_version = PLAYIT_VERSION
    return self._check_agent()""",
        'do not replace the packaged Android Playit daemon at runtime',
    )
