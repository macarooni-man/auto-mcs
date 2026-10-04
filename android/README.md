# auto-mcs Android

This directory contains the Android build overlay for auto-mcs.

The Android app is built from the normal auto-mcs source tree, but Android-specific behavior stays under `android/` instead of being mixed into the desktop application.

The app currently functions as a Telepath client. It uses the normal server manager UI and backend objects, but does not run Minecraft servers, Java, or Playit locally.

## Structure

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
├── dist/
└── build/
    ├── app/
    ├── python-for-android/
    ├── .buildozer/
    └── bin/
```

`source/` contains Android-owned modules and compatibility replacements.

`patches/source.py` contains changes applied to the normal auto-mcs Python source during staging.

`patches/p4a.py` contains changes applied to python-for-android before compilation.

`patches/apply.py` implements the source patcher.

`build/` and `dist/` are generated.

## Build process

Every build starts by creating a fresh staged application under:

```text
android/build/app
```

The normal repository source and locales are copied into the staging directory:

```text
/source
/locales
    ↓
android/build/app
```

Android-owned files are then copied in and `patches/source.py` is applied to the staged source.

The original repository source is not modified.

APK builds also prepare a pinned python-for-android checkout:

```text
python-for-android
58d21141f17c889bf8585f5665921d72028f8831
```

`patches/p4a.py` resets the checkout to that commit and applies the required Android toolchain changes before Buildozer runs.

The final APK is placed in:

```text
android/dist/
```

## Building

Stage the application and validate the source patches without compiling:

```sh
./android/build.sh stage
```

Build a debug APK:

```sh
./android/build.sh debug
```

Build a release APK:

```sh
./android/build.sh release
```

Remove generated Android build data:

```sh
./android/build.sh clean
```

Remove generated build data and the Buildozer virtual environment:

```sh
./android/build.sh clean-all
```

`build.sh` creates `android/.venv` automatically and installs the required Buildozer, Cython, and setuptools versions.

The Android build also requires Java and Rust. Rust is required by native Python dependencies including `pydantic-core` and `cryptography`.

## Build configuration

The current build targets:

```text
Python:       3.12.8
Kivy:         2.3.1
Android API:  36
Minimum API:  24
NDK:          28c
Architecture: arm64-v8a
Bootstrap:    SDL2
```

The application is currently locked to landscape orientation.

Portrait support exists in the runtime but is disabled for now. The orientation configuration and rotation hooks are left beside the active landscape implementation so it can be restored without rebuilding the feature.

## Source patches

Android-specific changes to the normal application should generally be implemented through `patches/source.py`.

The patcher operates on Python syntax rather than line numbers. Patch targets are expected to resolve exactly; staging fails if a required function, class, assignment, import, or call can no longer be found safely.

Generated Python is syntax-checked before the staged files are written.

Android-specific implementation should remain under `android/` unless the behavior is genuinely useful to the normal application as well.

## Runtime

`source/runtime.py` contains the Android platform integration used by the staged application.

It handles:

- Android activity and Java access through PyJNIus
- SDL surface scaling
- touch coordinate correction
- native soft-keyboard behavior
- Android Back navigation
- system status/navigation bars
- Storage Access Framework file selection
- MediaStore downloads
- Android audio
- Logcat output
- desktop compatibility stubs

The normal UI still runs through Kivy and the existing desktop views.

## Display

auto-mcs uses a logical SDL surface rather than rendering the desktop UI directly at the device's native resolution.

The default logical short edge is:

```text
720
```

It can be overridden with:

```sh
AUTO_MCS_ANDROID_HEIGHT=720
```

The SDL surface is scaled to the physical display and incoming touch coordinates are adjusted back into logical coordinates before Kivy receives them.

The app is currently forced into landscape and normalizes the initial Android display metrics accordingly.

Runtime rotation support is retained but disabled while portrait layouts are unfinished.

## System bars

Android uses the normal system status and navigation bars rather than running as a completely fullscreen SDL application.

The runtime updates system-bar foreground colors based on the current auto-mcs page so icons remain visible against the UI.

The page header extends behind the status bar and Android-specific title sizing keeps the desktop header layout usable with the additional inset.

## Touch input

Touch input is translated into the existing desktop interaction model.

A normal tap produces a left click.

Holding a stationary touch produces a complete right click, which allows context menus and other right-click actions to work without a mouse.

Dragging cancels the pending click and becomes a normal scroll or drag operation.

A temporary hover is generated before taps so controls using desktop hover states still provide visual feedback.

Android scrolling uses Kivy's non-elastic `ScrollEffect` to avoid desktop-style overscroll.

## Android Back

Android Back is intercepted before Kivy backgrounds the Activity.

It is converted into the same ESC behavior used by the desktop UI, so existing popup, menu, and screen navigation continues to work without maintaining a separate Android navigation stack.

## Keyboard

Android uses the native IME instead of the desktop keyboard capture system.

When an input gains focus, the runtime tracks its position and adjusts the SDL content so the control remains visible above the keyboard.

The transform is removed when the keyboard closes.

Console input and normal auto-mcs text inputs use the same keyboard tracking.

## Files

File and directory selection uses Android's Storage Access Framework.

`content://` selections are copied into private application storage before being returned to auto-mcs, allowing the existing application code to continue working with normal filesystem paths.

Telepath downloads are first written into private storage and then exported through Android MediaStore into the user's Downloads directory.

No broad external-storage permission is required.

## Application storage

Android stores auto-mcs data inside the application's private storage rather than using the normal desktop home-directory layout.

Temporary picker data is cleared when the runtime starts.

The Telepath client identity is persisted so reconnecting to existing Telepath servers does not create a new client identity on every update.

## Compatibility

The Android app packages most of the normal auto-mcs backend because the Telepath client and server manager UI depend on the same objects used by desktop.

Java and Playit managers are initialized as compatibility objects only.

Desktop-only interfaces such as the amscript editor, log viewer, and crash manager are replaced with lightweight stubs where necessary.

`psutil.py` and `bcrypt.py` are Android-specific compatibility implementations.

Automatic self-updates and Discord Rich Presence are disabled on Android.

## Logging

Python stdout and stderr are redirected to Logcat with the tag:

```text
telepath-remote
```

Show only the auto-mcs Android log:

```sh
adb logcat -s telepath-remote
```

Show the wider Python/Kivy/SDL output:

```sh
adb logcat | grep -E 'telepath-remote|python|SDL|kivy'
```

## Troubleshooting

Run staging first when changing source patches:

```sh
./android/build.sh stage
```

This validates the patch targets and generated Python without compiling an APK.

If the Buildozer or python-for-android build tree becomes unusable:

```sh
./android/build.sh clean
./android/build.sh debug
```

If the host Buildozer virtual environment also needs to be recreated:

```sh
./android/build.sh clean-all
./android/build.sh debug
```

The python-for-android checkout itself is reset to the pinned commit before every APK build.