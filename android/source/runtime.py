from functools import partial
from types import ModuleType
from threading import Event
import traceback
import hashlib
import shutil
import time
import sys
import os


# ---------------------------------------------- Global Variables ------------------------------------------------------
# <editor-fold desc="Global Variables">

log_tag:                 str = 'telepath-remote'
scale_factor:          float = 1.0
window_size: tuple[int, int] = (1280, int(os.environ.get('AUTO_MCS_ANDROID_HEIGHT', '720')))

_activity          = None
_logcat            = None
_surface_scaled    = False

_keyboard_listener = None
_keyboard_target   = None
_keyboard_target_y = None
_keyboard_offset   = 0.0
_keyboard_scale    = 1.0

# </editor-fold>



# ----------------------------------------------- Java Interfaces ------------------------------------------------------
# <editor-fold desc="Java Interface">

def _java_class(name: str):
    from jnius import autoclass  # type: ignore[PyUnresolvedReferences]
    return autoclass(name)


def _get_activity():
    global _activity
    if _activity is None:
        PythonActivity = _java_class('org.kivy.android.PythonActivity')
        _activity = PythonActivity.mActivity
    return _activity


def _run_on_ui_thread(function, timeout=1):
    from jnius import PythonJavaClass, java_method  # type: ignore[PyUnresolvedReferences]

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
    os.environ['KIVY_IMAGE'] = 'pil,sdl2'

    os.makedirs(os.environ['TMPDIR'], exist_ok=True)
    shutil.rmtree(os.path.join(os.environ['TMPDIR'], 'picker'), ignore_errors=True)

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
    _install_keyboard_pan()


def _install_touch_provider():
    from kivy.input.providers.mouse import MouseMotionEventProvider
    from kivy.core.window.window_sdl2 import SDL2MotionEventProvider, SDL2MotionEvent
    from kivy.core.window import Window
    from kivy.base import EventLoop
    from kivy.clock import Clock

    if getattr(SDL2MotionEventProvider, '_auto_mcs_scaled_touch', False): return

    original_update = SDL2MotionEventProvider.update

    # Give the hover enough time to visibly animate before dispatching the press
    tap_delay = (1 / 60) * 5

    # Hold a stationary touch to dispatch a normal right click
    hold_delay = 0.25
    touch_slop = 12

    pending = {}
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

    def begin_touch(fid, me, dispatch_fn, button):
        if fid in begun or touchmap.get(fid) is not me: return

        me.button = button
        begun.add(fid)
        dispatch_fn('begin', me)

        # The hover got its own rendered delay before the press
        # After press, kill the virtual cursor hover
        clear_hover(dispatch_fn)

    def hold_touch(fid, me, dispatch_fn, *args):
        state = pending.pop(fid, None)
        if not state or touchmap.get(fid) is not me: return

        begin_touch(fid, me, dispatch_fn, 'right')

    def tap_touch(fid, me, dispatch_fn, *args):
        if touchmap.get(fid) is not me: return

        begin_touch(fid, me, dispatch_fn, 'left')

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

            if action == 'fingerdown':
                update_hover(dispatch_fn, x, y)

                event = Clock.schedule_once(
                    partial(hold_touch, fid, me, dispatch_fn), hold_delay
                )

                pending[fid] = {
                    'event': event,
                    'time': Clock.get_time(),
                    'pos': (x, y)
                }

            elif action == 'fingerup':
                state = pending.pop(fid, None)

                # Released before the hold threshold: normal left click
                if state:
                    state['event'].cancel()

                    elapsed = Clock.get_time() - state['time']
                    delay = max(tap_delay - elapsed, 0)

                    if delay:
                        Clock.schedule_once(
                            partial(tap_touch, fid, me, dispatch_fn), delay
                        )

                    else:
                        tap_touch(fid, me, dispatch_fn)

                # A drag or long press already dispatched its begin event
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
                state = pending.get(fid)

                # Movement outside the hold threshold means this is a drag/scroll
                if state:
                    dx = (x - state['pos'][0]) * window_size[0]
                    dy = (y - state['pos'][1]) * window_size[1]

                    if (dx * dx) + (dy * dy) >= touch_slop * touch_slop:
                        state['event'].cancel()
                        pending.pop(fid, None)

                        begin_touch(fid, me, dispatch_fn, 'left')

                elif fid in begun:
                    dispatch_fn('update', me)

                if fid not in begun:
                    update_hover(dispatch_fn, x, y)

    SDL2MotionEventProvider._auto_mcs_scaled_touch = True
    SDL2MotionEventProvider._auto_mcs_original_update = original_update
    SDL2MotionEventProvider.update = update

    log('Installed scaled SDL2 touch provider')


def _install_keyboard_pan():
    global _keyboard_listener

    if _keyboard_listener: return

    from jnius import PythonJavaClass, java_method, cast  # type: ignore[PyUnresolvedReferences]

    PythonActivity = _java_class('org.kivy.android.PythonActivity')
    LayoutParams = _java_class('android.view.WindowManager$LayoutParams')
    BuildVersion = _java_class('android.os.Build$VERSION')
    DecelerateInterpolator = _java_class('android.view.animation.DecelerateInterpolator')
    Rect = _java_class('android.graphics.Rect')
    Color = _java_class('android.graphics.Color')

    activity = _get_activity()
    layout = PythonActivity.getLayout()
    surface = PythonActivity.getSurface()
    decor = activity.getWindow().getDecorView()

    if layout is None: raise RuntimeError('Android SDL layout is not ready')
    if surface is None: raise RuntimeError('Android SDL surface is not ready')
    if decor is None: raise RuntimeError('Android decor view is not ready')

    parent = layout.getParent()
    container = cast('android.view.View', parent) if parent is not None else None

    sdk = int(BuildVersion.SDK_INT)
    ime_type = None

    animation_time = 100
    keyboard_zoom = 1.3
    keyboard_y_offset = 75
    interpolator = DecelerateInterpolator()

    if sdk >= 30:
        WindowInsetsType = _java_class('android.view.WindowInsets$Type')
        ime_type = WindowInsetsType.ime()


    class KeyboardLayoutListener(PythonJavaClass):
        __javainterfaces__ = ['android/view/ViewTreeObserver$OnGlobalLayoutListener']
        __javacontext__ = 'app'

        def __init__(self):
            super().__init__()
            self.background_color = None

        def set_background(self, color):
            if not color: return

            r = max(0, min(255, round(color[0] * 255)))
            g = max(0, min(255, round(color[1] * 255)))
            b = max(0, min(255, round(color[2] * 255)))
            a = max(0, min(255, round(color[3] * 255)))

            self.background_color = Color.argb(a, r, g, b)

        @java_method('()V')
        def onGlobalLayout(self):
            global _keyboard_offset, _keyboard_scale

            try:
                width = max(int(decor.getWidth()), 1)
                height = max(int(decor.getHeight()), 1)
                surface_width = int(surface.getWidth()) or width
                surface_height = int(surface.getHeight()) or height
                keyboard_top = height
                keyboard_visible = False
                target_y = None

                # Android 11+ exposes the IME directly through WindowInsets
                if sdk >= 30:
                    insets = decor.getRootWindowInsets()

                    if insets and insets.isVisible(ime_type):
                        ime = insets.getInsets(ime_type)
                        keyboard_height = max(int(ime.bottom), 0)

                        if keyboard_height:
                            keyboard_top = max(height - keyboard_height, 0)
                            keyboard_visible = True

                # Older Android versions expose the usable display frame instead
                else:
                    rect = Rect()
                    decor.getWindowVisibleDisplayFrame(rect)

                    keyboard_height = max(height - int(rect.bottom), 0)

                    if keyboard_height > height * 0.15:
                        keyboard_top = max(int(rect.bottom), 0)
                        keyboard_visible = True


                if keyboard_visible and _keyboard_target_y is not None:
                    target_y = _keyboard_target_y * height
                    center_y = (keyboard_top / 2) + keyboard_y_offset
                    scale = keyboard_zoom

                    # Account for zoom around the center of the physical display
                    pivot_y = surface_height / 2
                    scaled_target_y = pivot_y + ((target_y - pivot_y) * scale)
                    offset = max(scaled_target_y - center_y, 0)

                else:
                    offset = 0
                    scale = 1.0


                if self.background_color is not None:
                    if container is not None:
                        container.setBackgroundColor(self.background_color)
                    decor.setBackgroundColor(self.background_color)

                current_offset = max(-float(layout.getTranslationY()), 0)
                current_scale = float(surface.getScaleX())
                if abs(offset - current_offset) >= 1 or abs(scale - current_scale) >= 0.001:
                    surface.setPivotX(surface_width / 2)
                    surface.setPivotY(surface_height / 2)

                    layout.animate().cancel()
                    surface.animate().cancel()

                    layout.animate().translationY(-float(offset)).setDuration(animation_time).setInterpolator(
                        interpolator).start()
                    surface.animate().scaleX(float(scale)).scaleY(float(scale)).setDuration(
                        animation_time).setInterpolator(interpolator).start()

                    if keyboard_visible and target_y is not None:
                        log(f'Android keyboard: top={keyboard_top}, target={target_y:.1f}, offset={offset:.1f}, scale={scale:.3f}')
                    elif current_offset or abs(current_scale - 1) >= 0.001:
                        log('Android keyboard hidden')

                    _keyboard_offset = offset
                    _keyboard_scale = scale

            except Exception:
                log_exception('Failed to update Android keyboard position')


    listener = KeyboardLayoutListener()

    def install():
        activity.getWindow().setSoftInputMode(LayoutParams.SOFT_INPUT_ADJUST_NOTHING)
        decor.getViewTreeObserver().addOnGlobalLayoutListener(listener)

    if not _run_on_ui_thread(install):
        raise RuntimeError('Unable to install Android keyboard layout listener')

    _keyboard_listener = listener
    log('Installed Android keyboard layout listener')


def set_keyboard_target(widget, focused, background_color=None):
    global _keyboard_target, _keyboard_target_y
    if not _keyboard_listener: return

    from kivy.clock import Clock

    if focused:
        _keyboard_target = widget
        _keyboard_target_y = None
        _keyboard_listener.set_background(background_color)

        # Wait for programmatically-focused inputs to actually enter the Window
        # before calculating their position
        def wait_target(attempt=0, *args):
            if _keyboard_target is not widget or not widget.focus: return

            if widget.get_root_window():
                Clock.schedule_once(resolve_target, 0)

            elif attempt < 40:
                Clock.schedule_once(partial(wait_target, attempt + 1), 0.05)

        # Wait one additional frame after attachment so its layout has settled
        def resolve_target(*args):
            global _keyboard_target_y
            if _keyboard_target is not widget or not widget.focus: return

            try:
                _, target_y = widget.to_window(*widget.center)

                _keyboard_target_y = 1 - (target_y / max(window_size[1], 1))
                _keyboard_target_y = max(0, min(1, _keyboard_target_y))

                _run_on_ui_thread(lambda: _keyboard_listener.onGlobalLayout())

            except Exception:
                log_exception('Failed to calculate Android keyboard target')

        Clock.schedule_once(wait_target, 0)
        return


    if _keyboard_target is widget:
        _keyboard_target = None
        _keyboard_target_y = None

    _run_on_ui_thread(lambda: _keyboard_listener.onGlobalLayout())


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


def telepath_id(app_title, username, id_hash):
    prefs = _get_activity().getSharedPreferences('auto_mcs', 0)

    value = prefs.getString('telepath_id', '')
    if value and len(str(value)) == 64:
        return str(value)

    value = hashlib.sha256(f"{app_title}::{username}::{id_hash}::{machine_id()}".encode()).hexdigest()

    if not prefs.edit().putString('telepath_id', value).commit():
        raise RuntimeError('Unable to persist Telepath identity')

    return value


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



# ------------------------------------------------ File Selection ------------------------------------------------------
# <editor-fold desc="File Selection">

def file_popup(ask_type, start_dir=None, ext=None, select_multiple=False, title=None):
    from android import activity   # type: ignore[PyUnresolvedReferences]
    from jnius import cast         # type: ignore[PyUnresolvedReferences]

    Intent = _java_class('android.content.Intent')
    Activity = _java_class('android.app.Activity')
    String = _java_class('java.lang.String')

    resolver = _get_activity().getContentResolver()


    def uri_name(uri):
        OpenableColumns = _java_class('android.provider.OpenableColumns')
        cursor = None

        try:
            cursor = resolver.query(uri, [OpenableColumns.DISPLAY_NAME], None, None, None)
            if cursor:
                index = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)

                if index >= 0 and cursor.moveToFirst():
                    name = cursor.getString(index)
                    if name: return str(name)

        except Exception:
            pass

        finally:
            if cursor:
                try: cursor.close()
                except Exception: pass

        try:
            name = uri.getLastPathSegment()
            if name: return str(name).rsplit('/', 1)[-1]
        except Exception: pass

        return 'selection'


    def copy_uri(uri, directory, name=None):
        name = os.path.basename(str(name or uri_name(uri)).replace('\x00', '')) or 'selection'
        target = os.path.join(directory, name)

        if os.path.exists(target):
            stem, extension = os.path.splitext(name)
            index = 2

            while os.path.exists(target):
                target = os.path.join(directory, f'{stem} ({index}){extension}')
                index += 1

        descriptor = resolver.openFileDescriptor(uri, 'r')
        if descriptor is None:
            raise RuntimeError(f"Unable to open Android document '{uri}'")

        fd = descriptor.detachFd()

        try:
            with os.fdopen(fd, 'rb') as source, open(target, 'wb') as output:
                shutil.copyfileobj(source, output, 1024 * 1024)

        finally:
            try: descriptor.close()
            except Exception: pass

        return target


    def copy_tree(tree_uri, directory):
        DocumentsContract = _java_class('android.provider.DocumentsContract')
        Document = _java_class('android.provider.DocumentsContract$Document')

        root_id = str(DocumentsContract.getTreeDocumentId(tree_uri))
        root_uri = DocumentsContract.buildDocumentUriUsingTree(tree_uri, root_id)

        root_name = os.path.basename(uri_name(root_uri).replace('\x00', '')) or 'selection'
        root = os.path.join(directory, root_name)
        os.makedirs(root)

        def copy_children(document_id, destination):
            children_uri = DocumentsContract.buildChildDocumentsUriUsingTree(tree_uri, document_id)
            projection = [Document.COLUMN_DOCUMENT_ID, Document.COLUMN_DISPLAY_NAME, Document.COLUMN_MIME_TYPE]

            cursor = resolver.query(children_uri, projection, None, None, None)
            rows = []

            try:
                while cursor and cursor.moveToNext():
                    rows.append((
                        str(cursor.getString(0)),
                        str(cursor.getString(1) or 'selection'),
                        str(cursor.getString(2) or '')
                    ))

            finally:
                if cursor:
                    try: cursor.close()
                    except Exception: pass

            for child_id, name, mime_type in rows:
                child_uri = DocumentsContract.buildDocumentUriUsingTree(tree_uri, child_id)

                if mime_type == Document.MIME_TYPE_DIR:
                    child_path = os.path.join(destination, os.path.basename(name) or 'selection')
                    os.makedirs(child_path, exist_ok=True)
                    copy_children(child_id, child_path)

                else:
                    copy_uri(child_uri, destination, name)

        copy_children(root_id, root)
        return root


    if ask_type == 'file':
        intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
        intent.addCategory(Intent.CATEGORY_OPENABLE)
        intent.setType('*/*')

        if select_multiple:
            intent.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, True)

        default_title = 'Select Files' if select_multiple else 'Select File'

    elif ask_type == 'dir':
        intent = Intent(Intent.ACTION_OPEN_DOCUMENT_TREE)
        default_title = 'Select Folder'

    else:
        raise ValueError(f"Unsupported Android picker type '{ask_type}'")

    intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
    intent.addFlags(Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION)
    intent.addFlags(Intent.FLAG_GRANT_PREFIX_URI_PERMISSION)

    chooser = Intent.createChooser(
        intent,
        cast('java.lang.CharSequence', String(title or default_title))
    )

    request_code = 10000 + (int.from_bytes(os.urandom(2), 'big') % 50000)
    result = {}
    completed = Event()

    def on_activity_result(request, result_code, data):
        if request != request_code: return

        result['code'] = result_code
        result['data'] = data
        completed.set()

    activity.bind(on_activity_result=on_activity_result)

    try:
        launched = _run_on_ui_thread(lambda: _get_activity().startActivityForResult(chooser, request_code))
        if not launched:
            raise RuntimeError('Unable to launch Android document picker')

        completed.wait()

    finally:
        try: activity.unbind(on_activity_result=on_activity_result)
        except Exception: pass

    data = result.get('data')
    if result.get('code') != Activity.RESULT_OK or data is None:
        return [] if ask_type == 'file' else ''

    root = os.path.join(os.environ['TMPDIR'], 'picker')
    os.makedirs(root, exist_ok=True)

    session = os.path.join(root, hashlib.sha1(os.urandom(32)).hexdigest()[:16])
    os.makedirs(session)

    if ask_type == 'dir':
        uri = data.getData()
        return copy_tree(uri, session) if uri else ''

    uris = []
    clip = data.getClipData()

    if clip:
        for index in range(clip.getItemCount()):
            uri = clip.getItemAt(index).getUri()
            if uri: uris.append(uri)

    else:
        uri = data.getData()
        if uri: uris.append(uri)

    return [copy_uri(uri, session) for uri in uris]

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
