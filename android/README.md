# auto-mcs Android build overlay

This directory builds the Android Telepath client from the normal auto-mcs source tree without modifying `../source`.

The Android build is generated into `./build/app` every time. Android-specific source replacements and build-time patches are applied only to that generated copy.

## Baseline

This overlay was written against:

- branch: `dev`
- commit: `16c06e6a4e11f31c0dbf45a6c702cf98addc1cd5`
- auto-mcs: `2.4`

The patcher is intentionally strict. If a source block it expects has changed, staging fails instead of silently producing a partially patched Android build.

## Layout

```text
android/
├── build.sh
├── buildozer.spec
├── patches/
│   └── apply.py
├── source/
│   ├── main.py
│   ├── android_runtime.py
│   └── psutil.py
└── build/                  generated, gitignored
    ├── app/
    │   ├── main.py
    │   ├── android_runtime.py
    │   ├── psutil.py
    │   ├── source/         generated copy of ../source
    │   └── locales/        generated copy of ../locales
    ├── .buildozer/
    └── bin/
```

Nothing under the repository's real `/source` directory is modified.

## Usage

Stage only:

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

Clear the generated Android build:

```sh
./build.sh clean
```

Also remove the local Buildozer virtual environment:

```sh
./build.sh clean-all
```

`build.sh` creates `./.venv` and installs Buildozer 1.6.0, setuptools 81.0.0, and Cython 0.29.34 the first time it is needed. The spec pins python-for-android stable commit `58d2114` (`v2026.05.09`) on `master`.

Artifacts are written under `./build/bin`.

## Debugging

The Android runtime redirects Python stdout/stderr to Logcat with the tag `telepath-remote`.

```sh
adb logcat -s telepath-remote
```

For the wider Kivy/Python log:

```sh
adb logcat | grep -E 'telepath-remote|python|SDL|kivy'
```

## What is intentionally preserved from dev-android

The display/input path intentionally retains the old Android workaround:

1. Read the physical Android display metrics.
2. Normalize them to landscape.
3. Use a logical height of 720 pixels.
4. Resize SDL's backing `SurfaceView` with `SurfaceHolder.setFixedSize()`.
5. Stretch that surface to the physical display.
6. Apply the inverse scale to SDL2 touch coordinates before Kivy sees them.

That is ugly, but it is the path that previously produced a usable auto-mcs UI on Android. It lives entirely in `source/android_runtime.py` now rather than being spread through the desktop code.

The logical height can be changed without editing the file:

```sh
export AUTO_MCS_ANDROID_HEIGHT=720
```

The value is read at application runtime, not build time.

## Scope

This build is intended to be a Telepath client.

The normal server-management code is still packaged because remote `ServerObject`/manager abstractions depend on it, but the Android entrypoint does not run the desktop launcher's update/version-cache/Java/Playit background bootstrap.

Java and Playit manager objects are initialized only as lightweight compatibility objects so UI modules that expect them do not immediately fail. Android does not attempt to install or launch a Minecraft JVM or Playit agent.

Automatic auto-mcs self-updates and Discord Rich Presence are disabled in the Android app configuration.

## Known rough edges

- Long-press-to-right-click/context-menu behavior is not reintroduced yet. Every Android SDL touch is normalized to a left click, matching the last reliably working behavior from the old branch.
- Android file selection uses Plyer. Modern Android may return `content://` URIs for some providers; callers that require a normal filesystem path can still need a content resolver bridge.
- Tk-based amscript editor/logviewer/crash UI are replaced by runtime no-op/logcat shims. They are not packaged as working Android UIs.
- Audio is currently a no-op backend. This avoids all desktop subprocess audio providers while keeping UI calls intact.
- Local Minecraft server creation/launch is outside the scope of this build.


## Toolchain notes

The spec targets Android API 36, minimum API 24, and NDK r28c. Display cutout mode is `shortEdges`; this replaces the unfinished camera-cutout TODO from the original `dev-android` branch without adding another source patch.

If a failed/interrupted python-for-android build leaves a broken internal build environment, run:

```sh
./build.sh clean
./build.sh debug
```

That removes the generated p4a/Buildozer tree while retaining the small host-side `./.venv`.


## Buildozer virtualenv detail

`build.sh` activates its host virtualenv before invoking Buildozer. Buildozer 1.6 only suppresses `pip --user` for python-for-android host dependencies when `VIRTUAL_ENV` is actually present in the environment; executing `./.venv/bin/buildozer` directly does not set it.
