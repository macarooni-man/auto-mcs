from functools import partial
from types import ModuleType
from threading import Event
import traceback
import time
import sys
import os


# ---------------------------------------------- Global Variables ------------------------------------------------------
# <editor-fold desc="Global Variables">

log_tag:                 str = 'telepath-remote'
scale_factor:          float = 1.0
window_size: tuple[int, int] = (1280, int(os.environ.get('AUTO_MCS_ANDROID_HEIGHT', '720')))

_activity       = None
_logcat         = None
_surface_scaled = False

# </editor-fold>



# ----------------------------------------------- Java Interfaces ------------------------------------------------------
# <editor-fold desc="Java Interface">

def _java_class(name: str):
    from jnius import autoclass
    return autoclass(name)


def _get_activity():
    global _activity
    if _activity is None:
        PythonActivity = _java_class('org.kivy.android.PythonActivity')
        _activity = PythonActivity.mActivity
    return _activity


def _run_on_ui_thread(function, timeout=1):
    from jnius import PythonJavaClass, java_method

    done = Event()
    error = []

    class Runnable(PythonJavaClass):
        __javainterfaces__ = ['java/lang/Runnable']
        __javacontext__ = 'app'

        @java_method('()V')
        def run(self):
            try: function()
            except Exception as e: error.append(e)
            finally: done.set()

    runnable = Runnable()
    _get_activity().runOnUiThread(runnable)
    done.wait(timeout)

    if error: raise error[0]
    return done.is_set()

# </editor-fold>



# --------------------------------------------------- Logging ----------------------------------------------------------
# <editor-fold desc="Logging">

def _log_object():
    global _logcat
    if _logcat is None:
        try: _logcat = _java_class('android.util.Log')
        except Exception: _logcat = False
    return _logcat


def log(message, level='d'):
    message = str(message)
    target = _log_object()

    if target:
        method = getattr(target, level if level in ('d', 'i', 'w', 'e') else 'd', target.d)
        for line in message.splitlines() or ['']:
            if line:
                try: method(log_tag, line)
                except Exception: pass

    try:
        stream = sys.__stderr__
        if stream:
            stream.write(message + ('\n' if not message.endswith('\n') else ''))
            stream.flush()
    except Exception: pass


def log_exception(prefix='Unhandled Android exception'):
    log(f'{prefix}:\n{traceback.format_exc()}', 'e')


class LogcatStream():
    def __init__(self, level='d'):
        self.level = level
        self.buffer = ''

    def write(self, message):
        if not message: return 0

        self.buffer += str(message)
        while '\n' in self.buffer:
            line, self.buffer = self.buffer.split('\n', 1)
            if line.strip(): log(line, self.level)

        return len(message)

    def flush(self):
        if self.buffer.strip(): log(self.buffer, self.level)
        self.buffer = ''


def _install_logcat():
    sys.stdout = LogcatStream('d')
    sys.stderr = LogcatStream('e')

    def handle_exception(exc_type, exc_value, exc_traceback):
        content = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        log(f'[EXC] {content}', 'e')

    sys.excepthook = handle_exception

# </editor-fold>



# --------------------------------------------- Runtime Environment ----------------------------------------------------
# <editor-fold desc="Runtime Environment">

def _private_root():
    return os.environ.get('ANDROID_PRIVATE') or os.environ.get('HOME') or os.getcwd()


def prepare_environment():
    root = _private_root()

    os.environ['AUTO_MCS_ANDROID'] = '1'
    os.environ['HOME'] = root
    os.environ['TMPDIR'] = os.path.join(root, 'tmp')
    os.environ['SDL_VIDEO_SCALE_MODE'] = 'stretch'
    os.environ['SDL_TOUCH_MOUSE_EVENTS'] = '0'
    os.environ['SDL_MOUSE_TOUCH_EVENTS'] = '0'
    os.environ['KIVY_NO_ARGS'] = '1'
    os.environ['KIVY_METRICS_DENSITY'] = '1'

    os.makedirs(os.environ['TMPDIR'], exist_ok=True)

    _install_logcat()
    _configure_surface()

# </editor-fold>



# ------------------------------------------------ Display / Input ------------------------------------------------------
# <editor-fold desc="Display / Input">

def _set_surface_size(width, height):
    SDLActivity = _java_class('org.libsdl.app.SDLActivity')
    surface = SDLActivity.mSurface
    if surface is None: raise RuntimeError('SDLActivity.mSurface is not ready')

    holder = surface.getHolder()
    holder.setFixedSize(width, height)

    LayoutParams = _java_class('android.view.ViewGroup$LayoutParams')
    params = surface.getLayoutParams()
    params.width = LayoutParams.MATCH_PARENT
    params.height = LayoutParams.MATCH_PARENT
    surface.setLayoutParams(params)


def _configure_surface():
    global scale_factor, window_size, _surface_scaled

    act = _get_activity()

    # Orientation could initially be reported as portrait, attempt to force landscape
    try: act.setRequestedOrientation(0)
    except Exception: log_exception('Failed to force landscape orientation')

    DisplayMetrics = _java_class('android.util.DisplayMetrics')
    dm = DisplayMetrics()
    act.getWindowManager().getDefaultDisplay().getMetrics(dm)

    raw_width = max(int(dm.widthPixels), 1)
    raw_height = max(int(dm.heightPixels), 1)

    # Normalize display metrics
    physical_width = max(raw_width, raw_height)
    physical_height = min(raw_width, raw_height)
    physical_size = (physical_width, physical_height)

    min_height = window_size[1]
    scale_factor = physical_height / max(min_height, 1)
    if scale_factor <= 0: scale_factor = 1.0

    virtual_width = round(physical_width / scale_factor)
    virtual_height = round(physical_height / scale_factor)
    window_size = (virtual_width, virtual_height)

    last_error = None

    # PythonActivity and SDL's SurfaceView can become available a little after Python starts
    # Retry the surface operation rather than falling through with mismatched input
    for _ in range(30):
        try:
            if _run_on_ui_thread(lambda: _set_surface_size(virtual_width, virtual_height)):
                _surface_scaled = True
                break
        except Exception as e: last_error = e
        time.sleep(0.1)

    if not _surface_scaled:
        raise RuntimeError(f'Unable to configure the scaled SDL surface after 30 attempts: {last_error}')

    log(f'Android display: physical={physical_size}, logical={window_size}, scale={scale_factor:.4f}')


def configure_kivy(Config):
    if not _surface_scaled: raise RuntimeError('Android SDL surface scaling was not initialized')

    Config.set('graphics', 'width', str(window_size[0]))
    Config.set('graphics', 'height', str(window_size[1]))
    Config.set('graphics', 'fullscreen', 'auto')
    Config.set('graphics', 'resizable', '0')

    _install_touch_provider()


def _install_touch_provider():
    from kivy.input.providers.mouse import MouseMotionEventProvider
    from kivy.core.window.window_sdl2 import SDL2MotionEventProvider, SDL2MotionEvent
    from kivy.core.window import Window
    from kivy.base import EventLoop
    from kivy.clock import Clock

    if getattr(SDL2MotionEventProvider, '_auto_mcs_scaled_touch', False): return

    original_update = SDL2MotionEventProvider.update

    # Give the hover slightly more than one 60 Hz frame to render
    tap_delay = (1 / 60) * 1.35

    pending_begins = {}
    pending_ends = set()
    begun = set()
    touchmap = SDL2MotionEventProvider.touchmap

    def mouse_provider():
        for provider in EventLoop.input_providers:
            if isinstance(provider, MouseMotionEventProvider): return provider
        return None

    def update_hover(dispatch_fn, x, y):
        Window.mouse_pos = (x * window_size[0], y * window_size[1])
        provider = mouse_provider()
        if provider: provider.update(dispatch_fn)

    def clear_hover(dispatch_fn):
        provider = mouse_provider()
        if provider and provider.hover_event:
            provider.end_hover_event(Window)
            provider.update(dispatch_fn)

    def begin_touch(fid, me, dispatch_fn, *args):
        pending_begins.pop(fid, None)
        if fid not in touchmap: return

        begun.add(fid)
        dispatch_fn('begin', me)

        # The hover got its own rendered delay before the press
        # After press, kill the virtual cursor hover
        clear_hover(dispatch_fn)

        # Very short taps may already have released
        if fid in pending_ends:
            pending_ends.discard(fid)
            me.update_time_end()
            dispatch_fn('end', me)
            begun.discard(fid)
            touchmap.pop(fid, None)

    def update(self, dispatch_fn):
        while True:
            try: value = self.q.pop()
            except IndexError: return

            try: action, fid, x, y, pressure = value[:5]
            except Exception:
                self.q.append(value)
                return original_update(self, dispatch_fn)

            y = 1 - (y / scale_factor)
            x = x / scale_factor

            if fid not in touchmap:
                me = SDL2MotionEvent('sdl', fid, (x, y, pressure))
                me.sx = x
                me.sy = y
                me.x = x * window_size[0]
                me.y = y * window_size[1]
                me.pos = (me.x, me.y)
                me.button = 'left'
                touchmap[fid] = me

            else:
                me = touchmap[fid]
                me.move((x, y, pressure))
                me.button = 'left'

            if action == 'fingerdown':
                update_hover(dispatch_fn, x, y)
                if fid not in pending_begins:
                    pending_begins[fid] = Clock.schedule_once(
                        partial(begin_touch, fid, me, dispatch_fn), tap_delay
                    )

            elif action == 'fingerup':
                # Do NOT update the hover here
                if fid in pending_begins:
                    pending_ends.add(fid)

                elif fid in begun:
                    clear_hover(dispatch_fn)
                    me.update_time_end()
                    dispatch_fn('end', me)
                    begun.discard(fid)
                    touchmap.pop(fid, None)

                else:
                    clear_hover(dispatch_fn)
                    touchmap.pop(fid, None)

            else:
                update_hover(dispatch_fn, x, y)
                if fid in begun: dispatch_fn('update', me)

    SDL2MotionEventProvider._auto_mcs_scaled_touch = True
    SDL2MotionEventProvider._auto_mcs_original_update = original_update
    SDL2MotionEventProvider.update = update

    log('Installed scaled SDL2 touch provider')


def bind_utility(utility):
    utility._default_size = window_size
    utility.window_size = window_size

# </editor-fold>



# ----------------------------------------------- Device Information --------------------------------------------------
# <editor-fold desc="Device Information">

def machine_id():
    SettingsSecure = _java_class('android.provider.Settings$Secure')
    value = SettingsSecure.getString(_get_activity().getContentResolver(), SettingsSecure.ANDROID_ID)
    if not value: raise RuntimeError('Unable to retrieve ANDROID_ID')
    return str(value)


def hostname():
    try:
        SettingsSecure = _java_class('android.provider.Settings$Secure')
        name = SettingsSecure.getString(_get_activity().getContentResolver(), 'bluetooth_name')
        if name: return str(name)
    except Exception: pass

    try:
        Build = _java_class('android.os.Build')
        if Build.MODEL: return str(Build.MODEL)
    except Exception: pass

    return 'android'


def locale_code():
    try:
        code = _java_class('java.util.Locale').getDefault().getLanguage()
        if code: return str(code)
    except Exception: log_exception('Failed to retrieve Android locale')
    return 'en'


def network_available():
    try:
        Context = _java_class('android.content.Context')
        manager = _get_activity().getSystemService(Context.CONNECTIVITY_SERVICE)
        info = manager.getActiveNetworkInfo()
        return bool(info and info.isConnected())
    except Exception: return True


def os_version():
    try:
        BuildVersion = _java_class('android.os.Build$VERSION')
        return str(BuildVersion.RELEASE), int(BuildVersion.SDK_INT)
    except Exception: return None, None

# </editor-fold>



# ---------------------------------------------------- Audio -----------------------------------------------------------
# <editor-fold desc="Audio">

class AudioPlayer():

    def __init__(self, audio_module):
        self.audio = audio_module
        self.providers = {ext: True for ext in audio_module.SoundPlayer.providers}
        self.sample_rates = audio_module.SoundPlayer.sample_rates
        self.AudioFormatError = audio_module.SoundPlayer.AudioFormatError

        self._loaded = set()
        self._loader = None

        try:
            from kivy.core.audio import SoundLoader
            self._loader = SoundLoader
            log('Initialized Kivy audio backend')
        except Exception: log_exception('Failed to initialize audio backend')

    def load(self, file_name, audio_format='mp3'):
        try:
            file = self.audio.SoundFile(self, file_name, audio_format)
            if not self._loader: return file

            sound = self._loader.load(file.path)
            if sound is None: raise RuntimeError(f"Kivy couldn't load '{file.path}'")

            file._sound = sound
            file._provider = sound.__class__.__name__
            self._loaded.add(file)

            log(f"Loaded audio '{file.path}' with {file._provider}")
            return file

        except Exception as e:
            log(f"Failed to load audio '{file_name}': {e}", 'e')
            return None

    def play(self, file, after=0, volume=None, pitch=None, jitter=None):
        if isinstance(file, str): file = self.load(file)
        if not isinstance(file, self.audio.SoundFile): return False

        sound = getattr(file, '_sound', None)
        if sound is None: return False

        volume = self.audio.normalize_volume(volume)
        if volume <= 0: return False

        pitch_data = self.audio.normalize_pitch(pitch, jitter)

        def execute(*args):
            try:
                sound.volume = volume

                # Kivy exposes this property even though Android MediaPlayer
                # does not currently implement pitch adjustment.
                try: sound.pitch = pitch_data['rate']
                except Exception: pass

                if sound.state == 'play': sound.stop()
                sound.play()

                log(f"Playing audio '{file.path}' volume={volume} provider={file._provider}")
                return True

            except Exception:
                log_exception(f"Failed to play audio '{file.path}'")
                return False

        if after and after > 0:
            from kivy.clock import Clock
            Clock.schedule_once(execute, after)
            return True

        return execute()

    def stop(self, file):
        try:
            sound = getattr(file, '_sound', None)
            if sound: sound.stop()
            return True
        except Exception:
            log_exception('Failed to stop audio')
            return False

    def close(self):
        for file in tuple(self._loaded):
            try:
                sound = getattr(file, '_sound', None)
                if sound:
                    sound.stop()
                    sound.unload()
            except Exception: pass

        self._loaded.clear()
        return True


def configure_audio(audio_module):
    player = AudioPlayer(audio_module)
    audio_module.player = player

    def init_player():
        audio_module.player = player
        return player

    audio_module.init_player = init_player

# </editor-fold>



# -------------------------------------------- Desktop Compatibility --------------------------------------------------
# <editor-fold desc="Desktop Compatibility">

def _stub_module(name, attributes):
    module = ModuleType(name)
    for key, value in attributes.items(): setattr(module, key, value)
    sys.modules[name] = module
    return module


def _stub_action(name):
    def stub(*args, **kwargs):
        log(f'Ignored desktop-only action: {name}', 'w')
        return None
    return stub


def install_desktop_stubs():
    _stub_module('source.ui.amseditor', {'quit_ipc': False, 'edit_script': _stub_action('amseditor.edit_script')})
    _stub_module('source.ui.logviewer', {'open_log': _stub_action('logviewer.open_log'), 'launch_window': _stub_action('logviewer.launch_window')})
    _stub_module('source.ui.crashmgr', {'open_log': _stub_action('crashmgr.open_log'), 'launch_window': _stub_action('crashmgr.launch_window')})

# </editor-fold>
