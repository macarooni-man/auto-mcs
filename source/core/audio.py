from datetime import datetime as dt
from random import choice, uniform
from shutil import which
from glob import glob
import subprocess
import threading
import queue
import math
import time
import os

from source.core import constants
from source.core.constants import (

    # Directories
    paths,

    # Classes
    dTimer,

    # General methods
    format_traceback,

    # Constants
    os_name
)


# UI sound backend
# ---------------------------------------------- Global Variables ------------------------------------------------------

# Max amount of concurrent sounds without queueing
polyphony_limit:    int = 10

# Higher numbers drop off volume faster with fader
volume_curve:     float = 1.5

# Anything here or below is effectively inaudible
db_floor:         float = -80

# Used to calculate master volume scale based on the fader
db_floor_scalar:  float = 10 ** (db_floor / 20)

# Cache dB normalization when master volume changes as calculation is quite expensive
master_scalar_cache:    dict[str, float] = {

    # 1-based value (note that app_config is scaled * 100)
    'volume': None,

    # Cached scale to use for the above volume
    'scale': None
}



# --------------------------------------------- General Functions ------------------------------------------------------

# Log wrapper
def send_log(object_data, message, level=None, *a):
    try: from source.core import logger
    except: return
    return logger.send_log(f'{__name__}.{object_data}', message, level, 'core')


# Ensures X is within bounds
def clamp(x: float, low: float, high: float) -> float:
    return max(low, min(high, x))


# Standardizes volume & applies user-specified master volume scaling
def normalize_volume(volume: float = None):
    global master_scalar_cache, db_floor_scalar, volume_curve

    master_volume = clamp(constants.app_config.master_volume, 0, 100) / 100
    new_volume    = clamp(volume, 0, 1) if (volume is not None) else 1

    # Don't do fun calculations if master volume is maxed
    if master_volume >= 1: return new_volume

    # Lookup cached values so this isn't calculated every play
    if master_volume != master_scalar_cache['volume']:

        # Map master scalar (0–1) to amplitude using a power-law curve
        if master_volume <= 0: master_normalized = 0.0
        else:
            master_normalized = master_volume ** volume_curve
            if master_normalized < db_floor_scalar:
                master_normalized = db_floor_scalar

        # Cache for future lookups
        master_scalar_cache.update({'volume': master_volume, 'scale': master_normalized})

    else: master_normalized = master_scalar_cache['scale']

    # Combine master & specified volume
    total_volume = new_volume * master_normalized
    return round(total_volume, 3)


# Standardizes pitch & applies pitch jitter if configured
# Jitter can either be a single float (+/-X), or a defined tuple range from a deviance of 0
def normalize_pitch(pitch: float = 0, jitter: float | tuple[float, float] = None, use_cents: bool = False):

    # Playback speed multiplier (1 is unchanged from original sample)
    rate = max(0.01, float(pitch or 1))

    # apply jitter J in [-x, +x]
    if isinstance(jitter, tuple):
        j = uniform(clamp(jitter[0], 0, 0.99), clamp(jitter[1], 0, 0.99))
    else:
        j = uniform(-clamp(float(jitter or 0), 0, 0.99), clamp(float(jitter or 0), 0, 0.99))

    rate *= (1 + j)
    if use_cents: cents = 0 if abs(rate - 1) < 1e-6 else 1200.0 * math.log(rate, 2)
    else:         cents = None
    return {"rate": round(rate, 3), "cents": cents}



# ------------------------------------------------ Audio Engine --------------------------------------------------------

# Loads a sound for the desktop UI (pass in a relative file name)
# Blocking will halt further sound execution until the sound has finished (only blocks the SoundPlayer 'audio' thread)
# File name can't have '*.ext', the format needs to be passed in separately
class SoundFile():
    _player:     'SoundPlayer' = None
    _process: subprocess.Popen = None
    _provider:             str = None

    # Defaults (configurable from '__init__')
    file:                  str = None
    format:                str = 'mp3'
    sample_rate:           int = 44100
    base_path:             str = os.path.join(paths.ui_assets, 'sounds')
    blocking:             bool = False

    def __repr__(self):
        if self._provider: provider_str = f"{self.format}: {self._provider}"
        else:              provider_str = self.format
        return f"<{self.__class__.__name__} '{self.name}' {provider_str}>"

    def __init__(self, player: 'SoundPlayer', file_name: str, audio_format: str = None, sample_rate: int = None):
        self._player = player

        # Override default audio format if it's supported
        if audio_format and isinstance(audio_format, str):

            audio_format = audio_format.strip(' .').lower()
            if audio_format not in self._player.providers.keys():
                raise self._player.AudioFormatError(audio_format)

            self.format = audio_format


        # Override default sample rate if it's supported
        if sample_rate and isinstance(sample_rate, int):

            if sample_rate not in self._player.sample_rates:
                raise self._player.AudioFormatError(sample_rate)

            self.sample_rate = sample_rate


        # Load specified sound file
        if '/' in file_name: file_name = os.path.join(*file_name.split('/')).strip()
        else:                file_name = file_name.strip()
        file = f'{file_name}.{self.format}'
        self.path = os.path.join(self.base_path, file)

        # Cycle randomized sounds from wildcard
        _matches_list = glob(self.path)
        if not _matches_list: raise FileNotFoundError(f"'{self.path}' does not exist")

        if '*' in self.path: self.path = choice(_matches_list)
        else:                self.path = _matches_list[0]
        self.name = file_name

        # Override file format with file name if unspecified
        if not audio_format: self.format = self.path.rsplit('.', 1)[-1].strip(' .').lower()


    # Plays selected sound (wrapper for 'SoundPlayer.play()'):
    #   after:   delays the sound playback, in seconds
    #   volume:  amplitude of the sound from 0-1, where 1 is the default of the sample (not normalized)
    #   pitch:   effectively the speed of the sample playback, 0-2, 1 is unaffected
    #   jitter:  add/subtract a random value of 0-1 to the pitch
    #
    # Backends are chosen via spray and pray. The ones that support volume/pitch are prioritized
    def play(self, *args, **kwargs) -> bool:
        return self._player.play(self, *args, **kwargs)

    def stop(self) -> bool:
        return self._player.stop(self)


# Handles all backends and queueing for sound loading and playback
class SoundPlayer():

    class AudioFormatError(Exception):
        def __init__(self, data: str | int):
            if isinstance(data, str):   self._message = f"Can't load unsupported audio format '*.{data.strip(' .').lower()}'"
            elif isinstance(data, int): self._message = f"Can't load unsupported sample rate '{data}'"
            super().__init__(self._message)

    class NoProviderError(Exception):
        def __init__(self, data: str):
            self._message = f"No provider was detected for audio format '*.{data.strip(' .')}'"
            super().__init__(self._message)

    OUT:                       int = subprocess.DEVNULL

    # Configure primary backend bin paths, and init caching checks
    sample_rates:       tuple[int] = (8000, 16000, 22050, 32000, 44100, 48000, 88200, 96000, 176400, 192000)
    providers: dict[str, callable] = {'wav': None, 'mp3': None, 'ogg': None}
    _player_fail_logged:      bool = False

    _mpg_bin_windows:          str = os.path.join(paths.bundled_utils, 'mpg', 'windows', 'mpg.exe')
    _sox_bin_macos:            str = os.path.join(paths.bundled_utils, 'sox', 'macos', 'play')
    _arch_path_linux:          str = 'arm64' if constants.is_arm else 'x64'
    _sox_bin_linux:            str = os.path.join(paths.bundled_utils, 'sox', 'linux', _arch_path_linux, 'play')


    # Internal log wrapper
    def _send_log(self, message: str, level: str = None):
        return send_log(self.__class__.__name__, message, level)

    def __init__(self):
        if constants.headless:
            if constants.debug: self._send_log("sound playback is disabled in headless", 'warning')
            return

        # Async pipeline
        self._q: 'queue.Queue[tuple[SoundFile, float, float, float, float | tuple[float, float]]]' = queue.Queue(maxsize=polyphony_limit)
        self._stop    = threading.Event()
        self._player  = threading.Thread(target=self._worker, name="audio", daemon=True)
        self._player.start()

        self._load_providers()



    # Background player thread, all audio gets enqueued and sent here for execution
    def _worker(self):

        # Drain until stop is set and queue is empty
        while not self._stop.is_set() or not self._q.empty():
            try: args = self._q.get(timeout=0.2)
            except queue.Empty: continue

            try:
                # Build the entry on the worker thread
                self._process_audio(*args)

            except Exception as e: self._send_log(f"audio thread worker error: {format_traceback(e)}", 'error')
            finally: self._q.task_done()

    # Pushes entry to worker
    def _dispatch(self, file: SoundFile, after: float, volume: float, pitch: float, jitter: float | tuple[float, float]):
        payload = (file, after, volume, pitch, jitter)

        # Enqueue sound for background playback
        try:
            if self._q.full():
                try: self._q.get_nowait(); self._q.task_done()
                except queue.Empty: pass
            self._q.put_nowait(payload)

        except queue.Full:

            # Block briefly to avoid dispatch loss
            try: self._q.put(payload, timeout=0.25)

            # Last resort: block until there is space
            except queue.Full: self._q.put(payload)

    # Heavy work happens here on the worker thread; processes and runs specified audio from the selected provider
    def _process_audio(self, file: SoundFile, after: float, volume: float, pitch: float, jitter: float | tuple[float, float]):
        start = dt.now()

        # These normalize internal values, not the audio itself
        volume = normalize_volume(volume)
        if volume <= 0:
            self._send_log(f"ignoring '{file}': sound playback is muted")
            return False

        pitch  = normalize_pitch(pitch, jitter)
        change_volume = abs(volume - 1.0) > 1e-6
        change_pitch  = abs(pitch['rate'] - 1.0) > 1e-6

        end = dt.now()


        # Compensate the delay from parameter processing
        delay = (after or 0) - (end - start).total_seconds()

        # Execute command from preselected audio format provider
        def _exec(*_):
            providers = self.providers
            runner    = providers.get(file.format, None)
            if callable(runner): return runner(file, volume, pitch, change_pitch, change_volume)
            else: raise self.NoProviderError(file.format)

        if delay > 0 and not file.blocking: dTimer(delay, _exec).start()
        elif delay > 0 and file.blocking: time.sleep(delay); _exec()
        else: _exec()

    # Executes chosen provider for the specified sound
    def _run(self, file: SoundFile, cmd: list[str], **kwargs) -> bool:
        try:
            if file.blocking:
                success = subprocess.run(cmd, stdout=self.OUT, stderr=self.OUT, **kwargs).returncode == 0
                return self._playback_log(file, success, cmd)

            else:
                file._process = subprocess.Popen(cmd, stdout=self.OUT, stderr=self.OUT, **kwargs)
                return self._playback_log(file, True, cmd)

        except Exception as e:
            if constants.debug: self._send_log(f"backend {cmd[0]} failed: {e}", 'warning')
            return False

    # Log if the file played back
    def _playback_log(self, file: SoundFile, success: bool, cmd: list | tuple = None) -> bool:
        blocking = 'blocking' if file.blocking else 'non-blocking'
        cmd_text = ' '.join(cmd).strip()

        if success:
            message = f"played {blocking} sound '{file}'"
            if cmd: message = f"{message}:\n{cmd_text}"
            self._send_log(message)

        else:
            message = f"failed to play sound '{file}'"
            if cmd: message = f"{message}:\n{cmd_text}"
            self._send_log(message, 'error')

        return success

    # Map callables to audio providers, per OS, for each file type
    def _load_providers(self) -> bool:

        # Helper to apply 'method' to providers (None is default, maps all free keys to 'method')
        def _set_provider(method: callable, ext_list: list | tuple = None):
            if not ext_list: ext_list = list(self.providers.keys())
            for ext in ext_list:
                if self.providers[ext] is None: self.providers[ext] = method



        # Run initial compatibility check to map 'self.providers' for each filetype
        try:

            if os_name == 'windows':

                # Prefer bundled mpg123 provider (Windows only)
                def _mpg_available() -> bool:
                    if os_name != 'windows':                      return False
                    if not os.path.isfile(self._mpg_bin_windows): return False
                    error: Exception = None
                    available = False

                    # Check if bundled mpg provider is available (it ALWAYS should be on Windows)
                    try:
                        test = subprocess.run([self._mpg_bin_windows, "--version"],
                            capture_output=True, text=True, timeout=1.5,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
                        if test.returncode == 0 and "mpg123" in (test.stdout or "").lower(): available = True

                    except Exception as e:
                        available = False
                        error = e

                    # Log error only the first time this is attempted
                    if not available and not self._player_fail_logged:
                        message = "the bundled 'mpg' provider is unavailable, this error should never happen"
                        if error: message += f':\n{format_traceback(error)}'
                        self._send_log(message, 'error')
                        self._player_fail_logged = True

                    return available



                # Bundled mpg123 for '*.mp3' with pitch/volume support
                def _run_mpg(file: SoundFile, volume: float, pitch: float, change_pitch: bool, change_volume: bool) -> bool:
                    file._provider = 'mpg123'
                    pitch_delta = f"{pitch['rate'] - 1.0:.3f}"          # 1.14 -> 0.14
                    scale_val = str(int(round(32768 * float(volume))))  # 0.80 -> 26214

                    cmd = [self._mpg_bin_windows, "-q", "-o", "win32"]
                    if change_pitch:  cmd.extend(["-e", "s16", "-r", str(file.sample_rate), "--pitch", pitch_delta])
                    if change_volume: cmd.extend(["--scale", scale_val])
                    cmd.append(file.path)

                    return self._run(file, cmd, creationflags=subprocess.CREATE_NO_WINDOW)
                if _mpg_available(): _set_provider(_run_mpg, ['mp3'])

                # Default '*.wav' provider on Windows
                def _run_winsound(file: SoundFile, *_) -> bool:
                    file._provider = 'winsound'
                    import winsound
                    flags = winsound.SND_FILENAME | (0 if file.blocking else winsound.SND_ASYNC)
                    winsound.PlaySound(file.path, flags)
                    return self._playback_log(file, True)
                _set_provider(_run_winsound, ['wav'])



            elif os_name == 'macos':

                # Prefer bundled SoX provider (macOS only)
                def _sox_available() -> bool:
                    if os_name != 'macos':                      return False
                    if not os.path.isfile(self._sox_bin_macos): return False
                    error: Exception = None
                    available = False

                    # Check if bundled SoX provider is available (it ALWAYS should be on macOS)
                    try:
                        test = subprocess.run([self._sox_bin_macos, "--version"], capture_output=True, text=True, timeout=1.5)
                        if test.returncode == 0 and "sox" in (test.stdout or "").lower(): available = True

                    except Exception as e:
                        available = False
                        error = e

                    # Log error only the first time this is attempted
                    if not available and not self._player_fail_logged:
                        message = "the bundled 'sox' provider is unavailable, this error should never happen"
                        if error: message += f':\n{format_traceback(error)}'
                        self._send_log(message, 'error')
                        self._player_fail_logged = True

                    return available



                # Bundled SoX for proper pitch/volume support (custom compiled binary for *.wav/*.mp3 only)
                def _run_sox(file: SoundFile, volume: float, pitch: float, change_pitch: bool, change_volume: bool) -> bool:
                    file._provider = 'sox'
                    cmd = [self._sox_bin_macos, "--no-show-progress", file.path]
                    if change_pitch:  cmd.extend(["speed", str(pitch['rate'])])
                    if change_volume: cmd.extend(["vol", str(volume)])
                    return self._run(file, cmd)
                if _sox_available(): _set_provider(_run_sox, ['wav', 'mp3'])

                # CoreAudio wrapper without true pitch changes (CoreAudio just stretches and resamples)
                def _run_afplay(file: SoundFile, volume: float, pitch: float, change_pitch: bool, change_volume: bool) -> bool:
                    file._provider = 'afplay'
                    cmd = ["afplay"]
                    if change_pitch:  cmd.extend(["-r", str(pitch['rate']), "-q", "1"])
                    if change_volume: cmd.extend(["-v", str(volume)])
                    cmd.append(file.path)
                    return self._run(file, cmd)
                _set_provider(_run_afplay)



            # Linux...
            else:

                # Prefer bundled SoX provider (Linux only)
                def _sox_available() -> bool:
                    if os_name != 'linux':                      return False
                    if not os.path.isfile(self._sox_bin_linux): return False
                    error: Exception = None
                    available = False

                    # Check if bundled SoX provider is available (it ALWAYS should be on Linux)
                    try:
                        test = subprocess.run([self._sox_bin_linux, "--version"], capture_output=True, text=True, timeout=1.5)
                        if test.returncode == 0 and "sox" in (test.stdout or "").lower(): available = True

                    except Exception as e:
                        available = False
                        error = e

                    # Log error only the first time this is attempted
                    if not available and not self._player_fail_logged:
                        message = "the bundled 'sox' provider is unavailable, this error should never happen"
                        if error: message += f':\n{format_traceback(error)}'
                        self._send_log(message, 'error')
                        self._player_fail_logged = True

                    return available

                # Prefer JACK backend when installed (Linux only)
                def _jack_available() -> bool:
                    if os_name != 'linux': return False
                    error: Exception = None
                    available = False

                    # Check if JACK server is available
                    jack = which('jack_lsp')
                    if jack:
                        try: available = subprocess.run([jack], stdout=self.OUT, stderr=self.OUT).returncode == 0
                        except Exception as e: error = e

                    if not available: available = bool(os.environ.get('JACK_DEFAULT_SERVER'))

                    # Log warning only the first time this is attempted
                    if not available:
                        message = "the 'JACK' server backend is unavailable"
                        if error: message += f':\n{format_traceback(error)}'
                        self._send_log(message, 'warning')
                        self._player_fail_logged = True

                    return available

                # Prefer PulseAudio backend when JACK is unavailable (Linux only)
                def _pulse_available() -> bool:
                    if os_name != 'linux': return False
                    error: Exception = None
                    available = False

                    # Check if PulseAudio server is available
                    pulse = which('pactl')
                    if pulse:
                        try: available = subprocess.run([pulse, 'info'], stdout=self.OUT, stderr=self.OUT).returncode == 0
                        except Exception as e: error = e

                    if not available: available = bool(os.environ.get('PULSE_SERVER'))

                    # Log warning only the first time this is attempted
                    if not available:
                        message = "the 'PulseAudio' server backend is unavailable"
                        if error: message += f':\n{format_traceback(error)}'
                        self._send_log(message, 'warning')
                        self._player_fail_logged = True

                    return available

                # Don't use backends for now as they seem to cause compatibility issues
                jack_available  = _jack_available()
                pulse_available = _pulse_available()
                if not (jack_available and pulse_available): self._player_fail_logged = True



                # Prefer providers with pitch/volume support when possible

                # Bundled SoX for proper pitch/volume support (custom compiled binary for *.wav/*.mp3 only)
                def _run_sox(file: SoundFile, volume: float, pitch: float, change_pitch: bool, change_volume: bool) -> bool:
                    file._provider = 'sox'
                    cmd = [self._sox_bin_linux, "--no-show-progress", file.path]
                    if change_pitch:  cmd.extend(["speed", str(pitch['rate'])])
                    if change_volume: cmd.extend(["vol", str(volume)])
                    return self._run(file, cmd)
                if _sox_available(): _set_provider(_run_sox, ['wav', 'mp3'])

                # mpg123 ('*.mp3' only)
                def _run_mpg(file: SoundFile, volume: float, pitch: float, change_pitch: bool, change_volume: bool) -> bool:
                    file._provider = 'mpg123'
                    cmd = ["mpg123", "-q"]
                    if jack_available:    cmd += ["-o", "jack"]
                    elif pulse_available: cmd += ["-o", "pulse"]
                    if change_pitch:  cmd += ["-r", str(file.sample_rate), "--pitch", f"{pitch['rate'] - 1.0:.4f}"]
                    if change_volume: cmd += ["--scale", str(int(round(32768 * volume)))]
                    cmd.append(file.path)
                    return self._run(file, cmd)
                if which('mpg123'): _set_provider(_run_mpg, ['mp3'])

                # MPV (all)
                def _run_mpv(file: SoundFile, volume: float, pitch: float, change_pitch: bool, change_volume: bool) -> bool:
                    file._provider = 'mpv'
                    cmd = ["mpv", "--no-video", "--really-quiet"]
                    if jack_available:    cmd.extend(["--ao=jack"])
                    elif pulse_available: cmd.extend(["--ao=pulse"])
                    if change_pitch:   cmd.extend(["--speed", str(pitch['rate'])])
                    if change_volume:  cmd.extend(["--volume", f"{20 * math.log10(volume):.2f}"])
                    cmd.append(file.path)
                    return self._run(file, cmd)
                if which('mpv'): _set_provider(_run_mpv)

                # VLC Media Player (all)
                def _run_vlc(file: SoundFile, volume: float, pitch: float, change_pitch: bool, change_volume: bool) -> bool:
                    file._provider = 'vlc'
                    cmd = ["cvlc", "--play-and-exit", "--intf", "dummy"]
                    if jack_available:    cmd.extend(["--aout", "jack"])
                    elif pulse_available: cmd.extend(["--aout", "pulse"])
                    if change_pitch:   cmd.extend(["--rate", str(pitch['rate'])])
                    if change_volume:  cmd.extend(["--volume", str(round(volume * 256))])
                    cmd.append(file.path)
                    return self._run(file, cmd)
                if which('cvlc'): _set_provider(_run_vlc)

                # ffmpeg (all)
                def _run_ffmpeg(file: SoundFile, volume: float, pitch: float, change_pitch: bool, change_volume: bool) -> bool:
                    file._provider = 'ffmpeg'
                    cmd = ["ffplay", "-v", "quiet", "-nodisp", "-autoexit"]
                    af = []

                    if change_pitch:
                        af.append(f"asetrate={file.sample_rate}*{pitch['rate']}")
                        af.append(f"aresample={file.sample_rate}")

                    if change_volume:
                        af.append(f"volume={volume}")

                    if af: cmd.extend(["-af", ",".join(af)])
                    cmd.append(file.path)

                    return self._run(file, cmd)
                if which('ffplay'): _set_provider(_run_ffmpeg)


                # Fallbacks (no pitch/volume control)

                # aplay (all)
                def _run_aplay(file: SoundFile, *_) -> bool:
                    file._provider = 'aplay'
                    cmd = ['aplay']
                    if jack_available:    cmd.extend(["-D", "jack"])
                    elif pulse_available: cmd.extend(["-D", "pulse"])
                    cmd.append(file.path)
                    return self._run(file, cmd)
                if which('aplay'): _set_provider(_run_aplay, ['wav'])


                # If there's still no providers, spray and pray until something works, lol
                if not all(list(self.providers.values())):
                    candidates = [
                        ["pw-play"],
                        ["paplay"],
                        ["pw-cat", "--playback"],
                        ["canberra-gtk-play", "-f"]
                    ]

                    def _make_cmd_runner(base_cmd: list[str]):
                        def _runner(file: SoundFile, *_, _base=tuple(base_cmd)):
                            file._provider = _base[0]
                            return self._run(file, list(_base) + [file.path])
                        return _runner

                    [_set_provider(_make_cmd_runner(cmd)) for cmd in candidates if which(cmd[0])]


            # Success any format providers are satisfied
            loaded  = [f'*.{k}' for k, v in self.providers.items() if v]
            success = len(loaded) > 0
            header  = f'initialized {self.__class__.__name__}'

            if constants.debug:
                if success: self._send_log(f"{header}: loaded all providers: {self.providers}", 'info')
                else:       self._send_log(f"{header}: couldn't load any providers: {self.providers}", 'error')
            else:
                if success: self._send_log(f"{header} with providers for {', '.join(loaded)}", 'info')
                else:       self._send_log(f"{header} with no available providers", 'error')

            return success


        except Exception as e:
            self._send_log(f"error while loading audio providers: {format_traceback(e)}", 'error')
            return False



    # Load a 'SoundFile' from a string
    def load(self, file_name: str, audio_format: str = SoundFile.format) -> SoundFile | None:
        try: return SoundFile(self, file_name, audio_format)
        except Exception as e: self._send_log(f"unable to load sound: {e}", 'error')


    # Plays selected sound:
    #   after:   delays the sound playback, in seconds
    #   volume:  amplitude of the sound from 0-1, where 1 is the default of the sample (not normalized)
    #   pitch:   effectively the speed of the sample playback, 0-2, 1 is unaffected
    #   jitter:  add/subtract a random value of 0-1 to the pitch
    #
    # Backends are chosen via spray and pray. The ones that support volume/pitch are prioritized
    def play(self, file: str | SoundFile, after: float = 0, volume: float = None, pitch: float = None, jitter: float | tuple[float, float] = None) -> None | bool:
        if isinstance(file, str): file = self.load(file)
        if not isinstance(file, SoundFile): raise TypeError(f"Expected 'str | SoundFile' for 'file', but got '{type(file)}'")

        # Ignore if no sound was found/provided
        if not file.path:
            if constants.debug: self._send_log('no sound is loaded, skipping playback', 'warning')
            return False

        # Ignore sound playback on the CLI
        if constants.headless:
            if constants.debug: self._send_log("sound playback is disabled in headless", 'warning')
            return False

        # If the sound is muted, there's no point in enqueuing to the worker
        if volume == 0 or constants.app_config.master_volume == 0:
            self._send_log(f"ignoring '{file}': sound playback is muted")
            return False

        # Send to background thread
        self._dispatch(file, after, volume, pitch, jitter)

    # Stops selected SoundFile
    def stop(self, file: SoundFile) -> bool:
        try:
            # If Windows and didn't use a CLI provider
            if file._provider == 'winsound':
                import winsound
                flag = winsound.SND_PURGE if file.blocking else winsound.SND_ASYNC
                winsound.PlaySound(None, flag)
                file._process = None
                return True

            # Kill the player process if it's still running
            elif file._process and file._process.poll() is None:
                file._process.terminate()
                try: file._process.wait(timeout=0.5)
                except subprocess.TimeoutExpired: file._process.kill()

            file._process = None
            return True

        except Exception as e:
            if constants.debug: self._send_log(f"error stopping sound: {format_traceback(e)}", 'warning')
            return False



# --------------------------------------------- Runtime Singleton ------------------------------------------------------

# Disabled by default since this only needs to be loaded for the desktop UI
player: SoundPlayer | None = None

def init_player():
    global player
    if not player: player = SoundPlayer()



# ---------------------------------------------- Usage Examples --------------------------------------------------------

# player = SoundPlayer()
# player.play('interaction/click_*', jitter=(0, 0.15))
#
# sound = player.load('popup/notification')
# sound.play(volume=0.5, after=3)
#
# # Block so the thread doesn't close instantly
# time.sleep(10)
