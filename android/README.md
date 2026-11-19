# auto-mcs Android

This directory contains the Android build overlay for auto-mcs.

The Android app is built from the normal auto-mcs source tree, but Android-specific behavior stays under `android/` instead of being mixed into the desktop application.

The Android build retains its Telepath client and adds **experimental local Java server hosting**. Local Playit integration is not yet available. The Android Java launch path has not been device-verified; the new launcher is intended for initial ARM64 APK testing.

## Structure

```text
android/
├── README.md
├── build.sh
├── buildozer.spec
├── patches/
│   ├── apply.py
│   ├── p4a.py
│   ├── java.py
│   └── source.py
├── source/
│   ├── bcrypt.py
│   ├── main.py
│   ├── psutil.py
│   ├── runtime.py
│   ├── java_runtime.py
│   ├── android_process.py
│   ├── server_service.py
│   └── gui-assets/
│       └── android-splash.png
├── native/
│   └── launcher.c
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

The app stores user-managed data in Android's accessible `Android/media` area:

```text
Internal storage/Android/media/com.macarooniman.automcs/auto-mcs/
├── Servers/
├── Backups/
├── Config/
├── Logs/
└── Tools/
```

This directory is accessible from a normal Android file manager (and often over USB/MTP), **without a debuggable APK, root, or broad storage permissions**. This location is managed by Android and can be deleted during app uninstall, so back up important worlds separately.

Android calls `getExternalMediaDirs()` to determine the actual storage path instead of assuming `/storage/emulated/0`. Existing user files are migrated from the former private `auto-mcs/` directory on startup, without overwriting files in the visible destination. The migration copies each file to a temporary destination before deleting the original; large existing worlds may therefore take time and need free space.

Java runtime files and Playit binaries remain in private storage because shared storage is unsuitable for loading native executables. Telepath keys are private too; `Tools/` in the visible directory contains only the remaining user-managed files.

Temporary picker data is cleared when the runtime starts.

The Telepath client identity is persisted so reconnecting to existing Telepath servers does not create a new client identity on every update.

## Compatibility

The Android app packages most of the normal auto-mcs backend because the Telepath client and server manager UI depend on the same objects used by desktop.

JavaManager is backed by an Android runtime provider for Java 8, 17, 21, and 25. Playit is still a compatibility object: its desktop Linux binary is not an Android agent.

Desktop-only interfaces such as the amscript editor, log viewer, and crash manager are replaced with lightweight stubs where necessary.

`psutil.py` and `bcrypt.py` are Android-specific compatibility implementations.

Automatic self-updates and Discord Rich Presence are disabled on Android.

## Logging

Python stdout and stderr are redirected to Logcat with the tag. The normal application log is also flushed to the user-visible `Logs/application/` directory approximately every 15 seconds while auto-mcs is running:

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

## Experimental local Java hosting

The Android staging patch `patches/java.py` replaces only the Java provider
selection and server process launch interface. The desktop Java manager and
server manager are not edited. The existing server creation screens and
launch scripts continue to select Java versions normally.

Java runtime downloads use verified ARM64 JRE archives from
[AngelAuraMC's Android OpenJDK builds](https://github.com/AngelAuraMC/angelauramc-openjdk-build).
The downloaded archives are checked against pinned SHA-256 hashes before
extraction into private application storage. The Java 8 archive may need
Amethyst's Android `unpack200` helper; the build script downloads and checks
a pinned version of that helper.

For each Java version, Buildozer packages the same native command-line shim
with the name `libautomcsjava<version>.so`. These files are PIE executables
installed in Android's native library directory, **not Java libraries**.
The corresponding `JavaVersion.exec_path` refers to that executable.
The shim finds the correct runtime in `Tools/java/android-java<version>`,
loads the JVM libraries, and invokes `JLI_Launch` with the original command-line
arguments. The first successful `validate()` requires actually running
the correct `-version`.

For local servers, `android_process.Popen` is substituted for the single
server-launch subprocess call using the staging patch. It forwards the
existing shell command to a sticky Android foreground service which starts
the native command-line JVM launcher. Input, output, exit codes, signals,
and process discovery travel over a private Unix socket. The service takes
a partial wake lock while Minecraft processes are running.

This is the first test implementation, not a verified always-on hosting
guarantee. Android may still stop the foreground service due to resource
pressure, battery management, policy, or user action. A service restart
after process death does not recover a terminated JVM.

### First on-device test

1. Build and install the APK from `android-dev`.
2. Open auto-mcs and create a **Vanilla** server without Playit.
3. Let the required Java version download and validate.
4. Start the server, accept Minecraft's EULA if prompted, and watch the console.
5. Connect from a device on the same local network using the phone's LAN IP.
6. Minimize auto-mcs and lock the phone to check whether the foreground hosting
   notification and server stay alive.

For diagnostics:

```sh
adb logcat -s telepath-remote python python-service
adb shell dumpsys activity services com.macarooniman.automcs
```

If Java installation fails, look for `[Android Java]`, `Android Java`,
or `[Android server]` in logs. A runtime can be fully downloaded without
being executable if the device's native linker rejects its libraries.

The current implementation deliberately leaves Playit disabled for local
hosting. Use LAN networking for the initial test. Android network and
storage restrictions, local server creation, modded installers, process
monitoring, and device/vendor-specific JVM compatibility still need actual
device testing.
