# auto-mcs Android build overlay

This directory builds the Android Telepath client from the normal auto-mcs source tree while keeping Android-specific implementation details isolated from the main desktop codebase.

The Android application is assembled into `./build/app` for every stage/build. The normal `/source` tree is copied first, then Android-only source transformations and runtime replacements are applied to that generated copy.

The repository's real source tree is never modified by the Android patcher.

## Baseline

The current overlay is based on:

- branch: `dev`
- commit: `05a8b03b72ace105ef4b85ebb49e8bd445445add`
- auto-mcs: `2.4`

The source patcher is intentionally strict. Patches target semantic Python structures rather than arbitrary text wherever possible.

If a required class, function, assignment, import, branch, or call no longer matches the expected source structure, staging fails instead of silently generating a partially patched application.

All registered source patches are prepared and syntax-validated before any transformed source file is written.

## Layout

```text
android/
├── README.md
├── build.sh
├── buildozer.spec
├── patches/
│   ├── apply.py
│   ├── p4a.py
│   └── source.py
├── source/
│   ├── bcrypt.py
│   ├── main.py
│   ├── psutil.py
│   ├── runtime.py
│   └── gui-assets/
│       └── android-splash.png
├── dist/                       generated APK output
└── build/                      generated, gitignored
    ├── app/
    │   ├── main.py
    │   ├── runtime.py
    │   ├── psutil.py
    │   ├── bcrypt.py
    │   ├── source/             patched copy of ../source
    │   └── locales/            copy of ../locales
    ├── python-for-android/
    ├── .buildozer/
    └── bin/
```

`android/source/` contains Android-owned runtime modules and replacements.

`android/patches/source.py` describes transformations applied only to the staged auto-mcs source tree.

`android/patches/p4a.py` contains build-time fixes applied to the pinned python-for-android source tree.

`android/patches/apply.py` implements and validates the staged-source patch framework.

## Source ownership

Android-specific behavior should normally live under `android/`.

Use `android/patches/source.py` when Android needs to alter a small part of the normal application source while preserving the desktop implementation.

Use `android/source/` when Android intentionally owns a complete runtime subsystem or compatibility module.

Use `android/patches/p4a.py` only for required python-for-android/toolchain fixes that cannot reasonably live in application code.

Changes to the real `/source` tree should remain platform-neutral.

A shared-source change is appropriate when the behavior belongs to the widget/application contract itself rather than Android specifically. For example, direct-touch detection and tap-to-reveal behavior are useful to any touchscreen-capable platform even though Android is currently the primary consumer.

Do not add `constants.is_android` branches to normal source merely to avoid writing an Android patch.

## Patch framework

`patches/source.py` registers transformations through `SourcePatch`.

Supported transformations currently include:

```text
before()             insert code immediately before a class or function
set()                replace an assignment value
after_assignment()   insert code after a named assignment
elif_()              add an elif branch after an existing condition
before_import()      insert code before an import
after_import()       insert code after an import
prepend()            insert code at the start of a function/class body
remove_call()        remove one specific function call
guard_call()         conditionally execute one specific call
guard_object()       conditionally execute an object's initialization block
platform()           inject Android ahead of an existing desktop OS branch
function()           replace an entire function
class_()             replace an entire class
```

Targets are resolved through Python's AST rather than line numbers.

Each patch must resolve its intended target unambiguously. A missing target or multiple unexpected matches fail staging.

The patch engine applies every transformation in memory, validates the resulting Python, and only writes transformed files after every registered patch has succeeded. This prevents a failed stage from leaving a half-patched generated tree.

## Build flow

`build.sh` performs three distinct jobs.

First, it stages the application:

```text
/source + /locales
        ↓
android/build/app
        ↓
Android-owned runtime files copied in
        ↓
patches/apply.py
        ↓
validated Android application tree
```

For APK builds it then prepares the pinned python-for-android checkout:

```text
python-for-android @ 58d21141f17c889bf8585f5665921d72028f8831
        ↓
patches/p4a.py
        ↓
Buildozer
        ↓
APK
```

The final APK is moved into `android/dist/`.

## Usage

Stage and validate the generated application without compiling an APK:

```sh
cd android
chmod +x build.sh
./build.sh stage
```

Build a debug APK:

```sh
./build.sh debug
```

Build a release APK:

```sh
./build.sh release
```

Remove generated Android build data:

```sh
./build.sh clean
```

Remove both generated build data and the local Buildozer virtual environment:

```sh
./build.sh clean-all
```

`build.sh` creates `./.venv` when necessary and installs:

```text
Buildozer 1.6.0
setuptools 81.0.0
Cython 0.29.34
```

Rust is also required by dependencies such as `pydantic-core` and `cryptography`.

## Android application model

The Android application is primarily a Telepath client.

The normal auto-mcs server-management source is still packaged because the remote `ServerObject`, manager, foundry, and UI abstractions depend on it.

Android does not attempt to run a local Minecraft JVM or Playit agent.

Java and Playit managers are initialized only as compatibility objects for source that expects those managers to exist.

Automatic auto-mcs self-updates and Discord Rich Presence are disabled.

Android stores application state in private app storage rather than attempting to reproduce the desktop filesystem layout.

The Telepath client identity is persisted independently of application updates.

## Display scaling

The Android runtime intentionally retains the proven logical-surface workaround from the older Android implementation.

At startup it:

1. Reads the Android display metrics.
2. Normalizes the display into landscape orientation.
3. Calculates a logical surface using a default height of 720 pixels.
4. Resizes SDL's backing `SurfaceView` with `SurfaceHolder.setFixedSize()`.
5. Stretches the logical surface across the physical display.
6. Applies the inverse physical/logical scale to incoming SDL touch coordinates before Kivy receives them.

The default logical height can be overridden at runtime:

```sh
export AUTO_MCS_ANDROID_HEIGHT=720
```

Changing this value affects the density of the entire desktop UI.

## Touch input

`runtime.py` replaces the normal SDL2 touch update path so coordinates correspond to the scaled logical surface.

Direct touch supports desktop-style hover affordances without leaving a permanent synthetic cursor behind.

A short tap:

```text
touch
→ synthetic hover
→ short visible hover delay
→ left click
→ synthetic hover cleared
```

A stationary hold becomes a right click, allowing normal auto-mcs context menus to remain usable on a touchscreen.

Moving farther than the touch-slop threshold converts the gesture into a normal drag/scroll instead.

Android list scrolling uses the non-elastic Kivy `ScrollEffect` so dragging stops at list boundaries instead of producing desktop-style overscroll.

## Android Back

Kivy normally maps Android's Back button/gesture to ESC and then backgrounds the Android Activity itself.

auto-mcs intercepts that key before Kivy's default Android handler and routes it through the normal screen ESC implementation instead.

This means Android Back follows the same application behavior as desktop ESC:

```text
open context menu  → close context menu
open popup         → dismiss/cancel popup
normal sub-screen  → activate its Back button
main screen        → follow that screen's normal ESC behavior
```

## Soft keyboard

Android uses the native soft keyboard instead of Kivy's desktop keyboard capture.

When a text input gains focus, `runtime.py` tracks its physical position and adjusts the SDL surface while the IME is visible.

The content can be translated and temporarily scaled so the focused control remains visible above the Android keyboard.

The normal surface transform is restored when the keyboard closes.

## File and directory selection

Android uses the Storage Access Framework rather than desktop filesystem dialogs.

Selected files are opened through Android's `ContentResolver` and materialized into the application's private temporary directory before they are returned to normal auto-mcs code.

This preserves the desktop `file_popup()` contract: callers receive ordinary filesystem paths and do not need to understand `content://` URIs.

Directory selections are recursively materialized for the same reason.

Temporary picker contents are discarded the next time the Android runtime starts.

This does mean selecting a very large directory requires enough temporary private storage to materialize that directory.

No broad external-storage permission is required for normal document-picker access.

## Audio

The Android compatibility layer routes auto-mcs audio through Kivy's `SoundLoader`.

Unsupported provider-specific features such as playback pitch adjustment are tolerated without breaking callers.

## Desktop compatibility

Some normal auto-mcs modules have no useful Android equivalent.

The Android runtime installs lightweight compatibility modules for desktop-only interfaces such as:

```text
amseditor
logviewer
crashmgr
```

Calls into those interfaces are logged or ignored rather than attempting to launch Tk/desktop subprocess UIs.

`psutil.py` and `bcrypt.py` are Android-owned compatibility replacements staged ahead of application startup.

## python-for-android patches

`patches/p4a.py` resets the local python-for-android checkout to the pinned commit before applying its changes.

The current patches handle Android/CPython build issues including extension linkage against `libpython`, Rust extension linkage, unavailable Bionic group APIs, and shared-library symbol visibility.

These changes intentionally live outside the application source patcher because they modify the Android Python toolchain itself.

## Debugging

Python stdout/stderr is redirected to Logcat using the tag:

```text
telepath-remote
```

Show only the Android runtime/application stream:

```sh
adb logcat -s telepath-remote
```

Show the wider Kivy/Python/SDL stream:

```sh
adb logcat | grep -E 'telepath-remote|python|SDL|kivy'
```

Running:

```sh
./build.sh stage
```

is also the fastest way to validate source patch targets and Python syntax without waiting for an APK build.

## Rebuilding after toolchain failures

If python-for-android or Buildozer is interrupted and leaves a broken generated environment:

```sh
./build.sh clean
./build.sh debug
```

For problems involving the host Buildozer virtual environment as well:

```sh
./build.sh clean-all
./build.sh debug
```

The p4a checkout itself is reset and cleaned to the pinned commit during every APK build before `patches/p4a.py` is applied.

## Buildozer virtual environment

`build.sh` activates its host virtual environment before invoking Buildozer.

Buildozer 1.6 checks the `VIRTUAL_ENV` environment variable before installing python-for-android host dependencies. Calling `./.venv/bin/buildozer` directly does not provide the same environment and can cause pip to attempt an invalid `--user` installation inside the virtual environment.