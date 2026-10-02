from types import ModuleType
from threading import Event
from glob import glob
import traceback
import time
import sys
import os


IS_ANDROID = True
LOG_TAG = "telepath-remote"

MIN_LOGICAL_HEIGHT = int(os.environ.get("AUTO_MCS_ANDROID_HEIGHT", "720"))
SCALE_FACTOR = 1.0
PHYSICAL_SIZE = (0, 0)
WINDOW_SIZE = (1280, MIN_LOGICAL_HEIGHT)

_activity = None
_android_log = None
_surface_scaled = False


def _jnius():
    from jnius import autoclass, PythonJavaClass, java_method
    return autoclass, PythonJavaClass, java_method


def activity():
    global _activity
    if _activity is None:
        autoclass, _, _ = _jnius()
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        _activity = PythonActivity.mActivity
    return _activity


def _log_object():
    global _android_log
    if _android_log is None:
        try:
            autoclass, _, _ = _jnius()
            _android_log = autoclass("android.util.Log")
        except Exception:
            _android_log = False
    return _android_log


def log(message, level="d"):
    message = str(message)
    target = _log_object()

    if target:
        method = getattr(target, level if level in ("d", "i", "w", "e") else "d", target.d)
        for line in message.splitlines() or [""]:
            if line:
                try:
                    method(LOG_TAG, line)
                except Exception:
                    pass

    try:
        stream = sys.__stderr__
        if stream:
            stream.write(message + ("\n" if not message.endswith("\n") else ""))
            stream.flush()
    except Exception:
        pass


def log_exception(prefix="Unhandled Android exception"):
    log(f"{prefix}:\n{traceback.format_exc()}", "e")


class LogcatStream:
    def __init__(self, level="d"):
        self.level = level
        self.buffer = ""

    def write(self, message):
        if not message:
            return 0

        self.buffer += str(message)
        while "\n" in self.buffer:
            line, self.buffer = self.buffer.split("\n", 1)
            if line.strip():
                log(line, self.level)

        return len(message)

    def flush(self):
        if self.buffer.strip():
            log(self.buffer, self.level)
        self.buffer = ""


def install_logcat():
    sys.stdout = LogcatStream("d")
    sys.stderr = LogcatStream("e")

    def handle_exception(exc_type, exc_value, exc_traceback):
        content = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        log(f"[EXC] {content}", "e")

    sys.excepthook = handle_exception


def private_root():
    return os.environ.get("ANDROID_PRIVATE") or os.environ.get("HOME") or os.getcwd()


def prepare_environment():
    root = private_root()

    os.environ["AUTO_MCS_ANDROID"] = "1"
    os.environ["HOME"] = root
    os.environ["TMPDIR"] = os.path.join(root, "tmp")
    os.environ["SDL_VIDEO_SCALE_MODE"] = "stretch"
    os.environ["SDL_TOUCH_MOUSE_EVENTS"] = "0"
    os.environ["SDL_MOUSE_TOUCH_EVENTS"] = "0"
    os.environ["KIVY_NO_ARGS"] = "1"
    os.environ["KIVY_METRICS_DENSITY"] = "1"

    os.makedirs(os.environ["TMPDIR"], exist_ok=True)

    install_logcat()
    configure_surface()


def configure_surface():
    global SCALE_FACTOR, PHYSICAL_SIZE, WINDOW_SIZE, _surface_scaled

    autoclass, PythonJavaClass, java_method = _jnius()
    act = activity()

    # SCREEN_ORIENTATION_LANDSCAPE. This is deliberately retained from the
    # old dev-android implementation because orientation could initially be
    # reported as portrait before the scaling calculation.
    try:
        act.setRequestedOrientation(0)
    except Exception:
        log_exception("Failed to force landscape orientation")

    DisplayMetrics = autoclass("android.util.DisplayMetrics")
    dm = DisplayMetrics()
    act.getWindowManager().getDefaultDisplay().getMetrics(dm)

    raw_width = max(int(dm.widthPixels), 1)
    raw_height = max(int(dm.heightPixels), 1)

    # Normalize the metrics even if Android still reports the pre-rotation
    # portrait dimensions for the first frame.
    physical_width = max(raw_width, raw_height)
    physical_height = min(raw_width, raw_height)

    PHYSICAL_SIZE = (physical_width, physical_height)
    SCALE_FACTOR = physical_height / max(MIN_LOGICAL_HEIGHT, 1)

    if SCALE_FACTOR <= 0:
        SCALE_FACTOR = 1.0

    virtual_width = round(physical_width / SCALE_FACTOR)
    virtual_height = round(physical_height / SCALE_FACTOR)
    WINDOW_SIZE = (virtual_width, virtual_height)

    last_error = None

    # PythonActivity and SDL's SurfaceView can become available a little after
    # Python starts. The old branch was sensitive to this race, so retry the
    # exact surface operation rather than falling through with mismatched input.
    for attempt in range(30):
        done = Event()
        error = []

        class Runnable(PythonJavaClass):
            __javainterfaces__ = ["java/lang/Runnable"]
            __javacontext__ = "app"

            @java_method("()V")
            def run(self):
                try:
                    SDLActivity = autoclass("org.libsdl.app.SDLActivity")
                    surface = SDLActivity.mSurface

                    if surface is None:
                        raise RuntimeError("SDLActivity.mSurface is not ready")

                    holder = surface.getHolder()
                    holder.setFixedSize(virtual_width, virtual_height)

                    LayoutParams = autoclass("android.view.ViewGroup$LayoutParams")
                    params = surface.getLayoutParams()
                    params.width = LayoutParams.MATCH_PARENT
                    params.height = LayoutParams.MATCH_PARENT
                    surface.setLayoutParams(params)

                except Exception as exc:
                    error.append(exc)

                finally:
                    done.set()

        runnable = Runnable()

        try:
            act.runOnUiThread(runnable)
            done.wait(1)

            if done.is_set() and not error:
                _surface_scaled = True
                break

            if error:
                last_error = error[0]

        except Exception as exc:
            last_error = exc

        time.sleep(0.1)

    if not _surface_scaled:
        raise RuntimeError(
            f"Unable to configure the scaled SDL surface after 30 attempts: {last_error}"
        )

    log(
        f"Android display: physical={PHYSICAL_SIZE}, logical={WINDOW_SIZE}, "
        f"scale={SCALE_FACTOR:.4f}"
    )


def configure_image_loader():
    from kivy.core.image.img_sdl2 import ImageLoaderSDL2

    original_extensions = ImageLoaderSDL2.extensions()

    if "webp" in original_extensions:
        ImageLoaderSDL2.extensions = staticmethod(
            lambda: tuple(ext for ext in original_extensions if ext != "webp")
        )

    log("Routed WebP images through Pillow")


def configure_kivy(Config):
    if not _surface_scaled:
        raise RuntimeError("Android SDL surface scaling was not initialized")

    Config.set("graphics", "width", str(WINDOW_SIZE[0]))
    Config.set("graphics", "height", str(WINDOW_SIZE[1]))
    Config.set("graphics", "fullscreen", "auto")
    Config.set("graphics", "resizable", "0")

    configure_image_loader()
    install_scaled_touch_provider()


def install_scaled_touch_provider():
    from functools import partial
    from kivy.input.providers.mouse import MouseMotionEventProvider
    from kivy.core.window.window_sdl2 import SDL2MotionEventProvider, SDL2MotionEvent
    from kivy.core.window import Window
    from kivy.base import EventLoop
    from kivy.clock import Clock

    if getattr(SDL2MotionEventProvider, "_auto_mcs_android_scaled", False):
        return

    original_update = SDL2MotionEventProvider.update
    pending_begins = {}
    pending_ends = set()
    begun = set()

    def update_mouse(dispatch_fn, x, y):
        Window.mouse_pos = (x * WINDOW_SIZE[0], y * WINDOW_SIZE[1])

        # Window.mouse_pos queues Kivy's hover event. Flush the mouse provider
        # immediately so the hover is processed during this frame.
        for provider in EventLoop.input_providers:
            if isinstance(provider, MouseMotionEventProvider):
                provider.update(dispatch_fn)

    def begin_touch(fid, me, dispatch_fn, *args):
        pending_begins.pop(fid, None)

        if fid not in touchmap:
            return

        begun.add(fid)
        dispatch_fn("begin", me)

        # Very short taps may have released before the delayed begin.
        if fid in pending_ends:
            pending_ends.discard(fid)
            me.update_time_end()
            dispatch_fn("end", me)
            begun.discard(fid)
            touchmap.pop(fid, None)

    def update(self, dispatch_fn):
        nonlocal touchmap
        touchmap = self.touchmap

        while True:
            try:
                value = self.q.pop()
            except IndexError:
                return

            try:
                action, fid, x, y, pressure = value[:5]
            except Exception:
                self.q.append(value)
                return original_update(self, dispatch_fn)

            y = 1 - (y / SCALE_FACTOR)
            x = x / SCALE_FACTOR

            if fid not in touchmap:
                me = SDL2MotionEvent("sdl", fid, (x, y, pressure))
                me.sx = x
                me.sy = y
                me.x = x * WINDOW_SIZE[0]
                me.y = y * WINDOW_SIZE[1]
                me.pos = (me.x, me.y)
                me.button = "left"
                touchmap[fid] = me

            else:
                me = touchmap[fid]
                me.move((x, y, pressure))
                me.button = "left"

            update_mouse(dispatch_fn, x, y)

            if action == "fingerdown":
                if fid not in pending_begins:
                    pending_begins[fid] = Clock.schedule_once(partial(begin_touch, fid, me, dispatch_fn), 0)

            elif action == "fingerup":
                if fid in pending_begins:
                    pending_ends.add(fid)

                elif fid in begun:
                    me.update_time_end()
                    dispatch_fn("end", me)
                    begun.discard(fid)
                    touchmap.pop(fid, None)

                else:
                    touchmap.pop(fid, None)

            elif fid in begun:
                dispatch_fn("update", me)

    touchmap = SDL2MotionEventProvider.touchmap

    SDL2MotionEventProvider._auto_mcs_android_scaled = True
    SDL2MotionEventProvider._auto_mcs_android_original_update = original_update
    SDL2MotionEventProvider.update = update

    log("Installed scaled SDL2 touch provider")


def bind_utility(utility):
    utility._default_size = WINDOW_SIZE
    utility.window_size = WINDOW_SIZE


def android_id():
    try:
        autoclass, _, _ = _jnius()
        SettingsSecure = autoclass("android.provider.Settings$Secure")
        return SettingsSecure.getString(
            activity().getContentResolver(),
            SettingsSecure.ANDROID_ID
        ) or "android"

    except Exception:
        log_exception("Failed to retrieve ANDROID_ID")
        return "android"


def hostname():
    try:
        autoclass, _, _ = _jnius()
        SettingsSecure = autoclass("android.provider.Settings$Secure")
        name = SettingsSecure.getString(
            activity().getContentResolver(),
            "bluetooth_name"
        )
        if name:
            return str(name)
    except Exception:
        pass

    try:
        autoclass, _, _ = _jnius()
        Build = autoclass("android.os.Build")
        if Build.MODEL:
            return str(Build.MODEL)
    except Exception:
        pass

    return "android"


def locale_code():
    try:
        autoclass, _, _ = _jnius()
        code = autoclass("java.util.Locale").getDefault().getLanguage()
        if code:
            return str(code)
    except Exception:
        log_exception("Failed to retrieve Android locale")

    return "en"


def network_available():
    try:
        autoclass, _, _ = _jnius()
        Context = autoclass("android.content.Context")
        manager = activity().getSystemService(Context.CONNECTIVITY_SERVICE)

        # Works across the older API range and is enough for the client's
        # coarse online/offline state.
        info = manager.getActiveNetworkInfo()
        return bool(info and info.isConnected())

    except Exception:
        return True


class NullSound:
    def __init__(self, name=""):
        self.name = name
        self.path = name
        self.blocking = False
        self._process = None
        self._provider = None


class NullAudioPlayer:
    def load(self, file_name, *args, **kwargs):
        return NullSound(file_name)

    def play(self, *args, **kwargs):
        return False

    def stop(self, *args, **kwargs):
        return True

    def close(self, *args, **kwargs):
        return True


def install_null_audio(audio_module):
    player = NullAudioPlayer()
    audio_module.player = player

    def init_player():
        audio_module.player = player
        return player

    audio_module.init_player = init_player


class AndroidAudioPlayer:
    providers = {'wav': True, 'mp3': True, 'ogg': True}
    sample_rates = (8000, 16000, 22050, 32000, 44100, 48000, 88200, 96000, 176400, 192000)

    def __init__(self, audio_module):
        self.audio = audio_module
        self._samples = {}
        self._ready = set()
        self._pending = {}

        autoclass, PythonJavaClass, java_method = _jnius()

        AudioAttributes = autoclass("android.media.AudioAttributes")
        AudioAttributesBuilder = autoclass("android.media.AudioAttributes$Builder")
        SoundPoolBuilder = autoclass("android.media.SoundPool$Builder")

        attributes = AudioAttributesBuilder().setUsage(AudioAttributes.USAGE_GAME).setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build()
        self.pool = SoundPoolBuilder().setMaxStreams(audio_module.polyphony_limit).setAudioAttributes(attributes).build()

        owner = self

        class LoadListener(PythonJavaClass):
            __javainterfaces__ = ["android/media/SoundPool$OnLoadCompleteListener"]
            __javacontext__ = "app"

            @java_method("(Landroid/media/SoundPool;II)V")
            def onLoadComplete(self, sound_pool, sample_id, status):
                owner._on_load(sample_id, status)

        self._listener = LoadListener()
        self.pool.setOnLoadCompleteListener(self._listener)

        # Preload every UI sound so the first interaction has no decode delay.
        for path in glob(os.path.join(audio_module.paths.ui_assets, 'sounds', '**', '*.mp3'), recursive=True):
            self._load_sample(path)

        log(f"Android audio: preloading {len(self._samples)} sounds")

    def _load_sample(self, path):
        if path not in self._samples:
            self._samples[path] = self.pool.load(path, 1)
        return self._samples[path]

    def _on_load(self, sample_id, status):
        if status != 0:
            log(f"Android audio failed to load sample {sample_id}: status {status}", "e")
            self._pending.pop(sample_id, None)
            return

        self._ready.add(sample_id)

        for file, volume, rate in self._pending.pop(sample_id, []):
            self._play_loaded(file, volume, rate)

    def _play_loaded(self, file, volume, rate):
        stream_id = self.pool.play(file._sample_id, volume, volume, 1, 0, rate)
        file._stream_id = stream_id
        file._provider = "android-soundpool"
        return stream_id > 0

    def load(self, file_name, audio_format='mp3'):
        try:
            file = self.audio.SoundFile(self, file_name, audio_format)
            file._sample_id = self._load_sample(file.path)
            file._stream_id = 0
            file._provider = "android-soundpool"
            return file

        except Exception as exc:
            log(f"Android audio failed to load '{file_name}': {exc}", "e")
            return None

    def play(self, file, after=0, volume=None, pitch=None, jitter=None):
        if isinstance(file, str):
            file = self.load(file)

        if not isinstance(file, self.audio.SoundFile):
            return False

        volume = self.audio.normalize_volume(volume)
        if volume <= 0:
            return False

        pitch_data = self.audio.normalize_pitch(pitch, jitter)
        rate = max(0.5, min(2.0, pitch_data['rate']))

        def execute(*args):
            if file._sample_id in self._ready:
                return self._play_loaded(file, volume, rate)

            self._pending.setdefault(file._sample_id, []).append((file, volume, rate))
            return True

        if after and after > 0:
            self.audio.dTimer(after, execute).start()
            return True

        return execute()

    def stop(self, file):
        try:
            if file._stream_id:
                self.pool.stop(file._stream_id)
            file._stream_id = 0
            return True
        except Exception:
            return False

    def close(self):
        try:
            self.pool.release()
            return True
        except Exception:
            return False


def install_android_audio(audio_module):
    try:
        player = AndroidAudioPlayer(audio_module)

    except Exception:
        log_exception("Failed to initialize Android audio")
        return install_null_audio(audio_module)

    audio_module.player = player

    def init_player():
        audio_module.player = player
        return player

    audio_module.init_player = init_player
    log("Installed Android SoundPool audio backend")


def _stub_module(name, attributes):
    module = ModuleType(name)
    for key, value in attributes.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


def install_desktop_stubs():
    def log_stub(name):
        def stub(*args, **kwargs):
            log(f"Ignored desktop-only action: {name}", "w")
            return None
        return stub

    _stub_module(
        "source.ui.amseditor",
        {
            "quit_ipc": False,
            "edit_script": log_stub("amseditor.edit_script"),
        },
    )

    _stub_module(
        "source.ui.logviewer",
        {
            "open_log": log_stub("logviewer.open_log"),
            "launch_window": log_stub("logviewer.launch_window"),
        },
    )

    _stub_module(
        "source.ui.crashmgr",
        {
            "open_log": log_stub("crashmgr.open_log"),
            "launch_window": log_stub("crashmgr.launch_window"),
        },
    )
