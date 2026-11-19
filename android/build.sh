#!/usr/bin/env bash
set -euo pipefail

ANDROID_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$ANDROID_DIR/.." && pwd)"
BUILD_DIR="$ANDROID_DIR/build"
STAGE_DIR="$BUILD_DIR/app"
DIST_DIR="$ANDROID_DIR/dist"
VENV_DIR="$ANDROID_DIR/.venv"
P4A_DIR="$BUILD_DIR/python-for-android"
P4A_COMMIT="58d21141f17c889bf8585f5665921d72028f8831"

MODE="${1:-debug}"
if [ $# -gt 0 ]; then shift; fi


# Create CI 'build-data.json'
if [ "${CI:-}" = "true" ]; then

    BRANCH=""
    BUILD=""
    COMMIT=""
    REPO=""

    # Parse required parameters, ignore everything else
    while [ $# -gt 0 ]; do
        case "$1" in
            --branch)
                [ $# -ge 2 ] || { echo "missing value for --branch" >&2; break; }
                BRANCH=$2; shift 2 ;;
            --build)
                [ $# -ge 2 ] || { echo "missing value for --build" >&2; break; }
                BUILD=$2; shift 2 ;;
            --commit)
                [ $# -ge 2 ] || { echo "missing value for --commit" >&2; break; }
                COMMIT=$2; shift 2 ;;
            --repo)
                [ $# -ge 2 ] || { echo "missing value for --repo" >&2; break; }
                REPO=$2; shift 2 ;;
            *) shift ;;
        esac
    done

    write_build_json() {

        branch=$1
        build=$2
        commit=$3
        repo=$4

        # Don't create the file if parameters are missing
        if [ -z "$branch" ] || [ -z "$build" ] || [ -z "$commit" ] || [ -z "$repo" ]; then
            echo "Skipping 'build-data.json'"
            return 0
        fi

        type=development
        [ "$branch" = "main" ] && type=release

        out="$REPO_ROOT/source/build-data.json"

        # Ensure directory exists
        mkdir -p "$(dirname "$out")" || return 0

        # Use %s for version to avoid numeric-only constraint
        if printf '{"type":"%s","version":"%s","branch":"%s","commit":"%s","repo":"%s"}' \
            "$type" "$build" "$branch" "$commit" "$repo" >"$out"
        then
            echo "Wrote $out"
        fi
    }

    write_build_json "$BRANCH" "$BUILD" "$COMMIT" "$REPO"
fi


setup_p4a() {
    echo "[android] Preparing python-for-android..."

    if [ ! -d "$P4A_DIR/.git" ]; then
        git clone https://github.com/kivy/python-for-android.git "$P4A_DIR"
    fi

    git -C "$P4A_DIR" reset --hard "$P4A_COMMIT"
    git -C "$P4A_DIR" clean -dxf

    python3 "$ANDROID_DIR/patches/p4a.py" "$P4A_DIR"
}

die() {
    echo "[android] $*" >&2
    exit 1
}

clean_stage() {
    rm -rf "$STAGE_DIR"
    mkdir -p "$STAGE_DIR"
}

stage_source() {
    [ -d "$REPO_ROOT/source" ] || die "Missing '$REPO_ROOT/source'"
    [ -d "$REPO_ROOT/locales" ] || die "Missing '$REPO_ROOT/locales'"

    echo "[android] Staging pristine source..."
    clean_stage

    cp -a "$REPO_ROOT/source" "$STAGE_DIR/source"
    cp -a "$REPO_ROOT/locales" "$STAGE_DIR/locales"

    cp "$ANDROID_DIR/source/main.py" "$STAGE_DIR/main.py"
    cp "$ANDROID_DIR/source/runtime.py" "$STAGE_DIR/runtime.py"
    cp "$ANDROID_DIR/source/psutil.py" "$STAGE_DIR/psutil.py"
    cp "$ANDROID_DIR/source/bcrypt.py" "$STAGE_DIR/bcrypt.py"
    cp "$ANDROID_DIR/source/java_runtime.py" "$STAGE_DIR/android_java.py"
    cp "$ANDROID_DIR/source/android_process.py" "$STAGE_DIR/android_process.py"
    cp "$ANDROID_DIR/source/android_playit.py" "$STAGE_DIR/android_playit.py"
    mkdir -p "$STAGE_DIR/services"
    cp "$ANDROID_DIR/source/server_service.py" "$STAGE_DIR/services/server_service.py"


    # -------------------------------------------- Android Overlay -----------------------------------------------------

    echo "[android] Applying Android-only patches to generated source..."
    python3 "$ANDROID_DIR/patches/apply.py" "$STAGE_DIR"
    echo "[android] Staged build tree: $STAGE_DIR"
}

setup_java8_agent() {
    # JAR files are ZIP archives. The .zip suffix is included in buildozer.spec
    # and allows this Java 8 premain agent to be bundled without modifying p4a.
    command -v javac >/dev/null 2>&1 || die "javac is required for Java 8 stdin agent"
    command -v jar >/dev/null 2>&1 || die "jar is required for Java 8 stdin agent"

    local work="$BUILD_DIR/java8-stdin-agent"
    mkdir -p "$work/classes"
    printf 'Premain-Class: Java8StdinAgent\n\n' > "$work/manifest.mf"
    javac --release 8 -d "$work/classes" "$ANDROID_DIR/native/Java8StdinAgent.java"
    jar cfm "$STAGE_DIR/java8-stdin-agent.zip" "$work/manifest.mf" -C "$work/classes" .
}

setup_native() {
    local native_dir="$BUILD_DIR/native/arm64-v8a"
    local ndk_bin
    ndk_bin=$(find "$HOME/.buildozer/android/platform" -type d -path '*/toolchains/llvm/prebuilt/linux-x86_64/bin' -print 2>/dev/null | sort -V | tail -n 1 || true)
    if [ -z "$ndk_bin" ]; then
        echo "[android] Preparing SDK/NDK for native launcher..."
        (
            cd "$ANDROID_DIR"
            source "$VENV_DIR/bin/activate"
            buildozer -v android update
        )
        ndk_bin=$(find "$HOME/.buildozer/android/platform" -type d -path '*/toolchains/llvm/prebuilt/linux-x86_64/bin' -print 2>/dev/null | sort -V | tail -n 1 || true)
    fi
    [ -n "$ndk_bin" ] || die "Android NDK clang toolchain not found"

    mkdir -p "$native_dir"
    echo "[android] Compiling native Java command launcher..."
    "$ndk_bin/clang" --target=aarch64-linux-android24 \
        -O2 -fPIE -pie -Wl,-z,relro -Wl,-z,now \
        "$ANDROID_DIR/native/launcher.c" -ldl \
        -o "$native_dir/libautomcsjava8.so"
    for version in 17 21 25; do
        cp "$native_dir/libautomcsjava8.so" "$native_dir/libautomcsjava$version.so"
    done

    # Android OpenJDK's libjli.so depends on the NDK C++ shared runtime.
    # Package it beside our executable launchers in the APK's native library dir.
    local cxx="$ndk_bin/../sysroot/usr/lib/aarch64-linux-android/libc++_shared.so"
    [ -f "$cxx" ] || die "Android NDK libc++_shared.so not found at '$cxx'"
    cp "$cxx" "$native_dir/libc++_shared.so"

    # Java 8 JRE archives contain .pack files; use the Android unpack200 helper
    # pinned to Amethyst v3_openjdk's inspected Git object.
    local unpack="$native_dir/libunpack200.so"
    local download="https://raw.githubusercontent.com/AngelAuraMC/Amethyst-Android/166af615dbdca1a507b8c2d379822cca02795132/app_pojavlauncher/src/main/jniLibs/arm64-v8a/libunpack200.so"
    curl -fL --retry 3 --retry-delay 2 -o "$unpack" "$download"
    [ "$(git hash-object "$unpack")" = "50ea1bb7bafeca69449b5362e0afb69f2094b88a" ] \
        || die "Android unpack200 checksum mismatch"
}

setup_playit() {
    # Upstream Playit source and the Android-only CI cache share one lock file.
    local version revision
    version=$(sed -nE 's/^version=([^ ]+)$/\1/p' "$ANDROID_DIR/playit.lock")
    revision=$(sed -nE 's/^revision=([0-9a-f]{40})$/\1/p' "$ANDROID_DIR/playit.lock")
    [ -n "$version" ] && [ -n "$revision" ] || die "Invalid android/playit.lock"

    local runtime_version
    runtime_version=$(sed -nE "s/^PLAYIT_VERSION = '([^']+)'$/\1/p" "$ANDROID_DIR/source/android_playit.py")
    [ "$version" = "$runtime_version" ] || die "Playit lock version does not match android_playit.py"

    local native_dir="$BUILD_DIR/native/arm64-v8a"
    local cache_dir="$BUILD_DIR/playit-cache"
    local cached="$cache_dir/libautomcsplayit.so"
    local stamp="$cache_dir/revision"
    local checksum="$cache_dir/sha256"
    local ndk_bin
    ndk_bin=$(find "$HOME/.buildozer/android/platform" -type d -path '*/toolchains/llvm/prebuilt/linux-x86_64/bin' -print 2>/dev/null | sort -V | tail -n 1 || true)
    [ -n "$ndk_bin" ] || die "Android NDK clang toolchain not found for Playit"

    mkdir -p "$native_dir"

    # On a cache hit, skip checkout, Rust target installation, and Cargo.
    if [ -s "$cached" ] && [ -f "$stamp" ] && [ -f "$checksum" ] \
        && [ "$(cat "$stamp")" = "$revision" ] \
        && printf '%s  %s\n' "$(cat "$checksum")" "$cached" | sha256sum -c --status \
        && "$ndk_bin/llvm-readelf" -h "$cached" | grep -Eq 'Type:.*DYN'; then
        echo "[android] Using cached Playit v$version ($revision)"
    else
        echo "[android] Compiling upstream Playit v$version for Android ARM64..."
        local checkout="$BUILD_DIR/playit-agent"

        if [ -f "$HOME/.cargo/env" ]; then
            source "$HOME/.cargo/env"
        fi
        command -v cargo >/dev/null 2>&1 || die "Rust Cargo is required to compile Android Playit"

        if [ ! -d "$checkout/.git" ]; then
            rm -rf "$checkout"
            git clone --depth 1 --branch "v$version" https://github.com/playit-cloud/playit-agent.git "$checkout"
        fi

        git -C "$checkout" fetch --depth 1 origin "refs/tags/v$version"
        git -C "$checkout" checkout -f --detach "$revision"
        [ "$(git -C "$checkout" rev-parse HEAD)" = "$revision" ] || die "Playit source revision mismatch"

        rustup target add aarch64-linux-android

        (
            cd "$checkout"
            export CARGO_TARGET_DIR="$BUILD_DIR/playit-target"
            export CARGO_TARGET_AARCH64_LINUX_ANDROID_LINKER="$ndk_bin/aarch64-linux-android24-clang"
            export CC_aarch64_linux_android="$ndk_bin/aarch64-linux-android24-clang"
            export CXX_aarch64_linux_android="$ndk_bin/aarch64-linux-android24-clang++"
            export AR_aarch64_linux_android="$ndk_bin/llvm-ar"
            cargo build --release --locked --package playitd --target aarch64-linux-android
        )

        local binary="$BUILD_DIR/playit-target/aarch64-linux-android/release/playitd"
        [ -s "$binary" ] || die "Android Playit daemon was not built"
        "$ndk_bin/llvm-readelf" -h "$binary" | grep -Eq 'Type:.*DYN' || die "Android Playit daemon is not a PIE ELF"

        mkdir -p "$cache_dir"
        cp "$binary" "$cached"
        chmod 755 "$cached"
        sha256sum "$cached" | cut -d' ' -f1 > "$checksum"
        printf '%s\n' "$revision" > "$stamp"
    fi

    cp "$cached" "$native_dir/libautomcsplayit.so"
    chmod 755 "$native_dir/libautomcsplayit.so"
    echo "[android] Packaged Playit v$version into the APK native library directory"
}


setup_libdatachannel() {
    # Geyser's JNI wrapper comes from OpenCollab. Build its matching Android
    # native library, using a revision-pinned cache just like the Playit agent.
    local revision
    revision=$(sed -nE 's/^revision=([0-9a-f]{40})$/\1/p' "$ANDROID_DIR/libdatachannel.lock")
    [ -n "$revision" ] || die "Invalid android/libdatachannel.lock"

    local native_dir="$BUILD_DIR/native/arm64-v8a"
    local cache_dir="$BUILD_DIR/libdatachannel-cache"
    local cached="$cache_dir/libautomcsdatachannel.so"
    local stamp="$cache_dir/revision"
    local checksum="$cache_dir/sha256"
    local ndk_bin
    ndk_bin=$(find "$HOME/.buildozer/android/platform" -type d -path '*/toolchains/llvm/prebuilt/linux-x86_64/bin' -print 2>/dev/null | sort -V | tail -n 1 || true)
    [ -n "$ndk_bin" ] || die "Android NDK clang toolchain not found for libdatachannel"

    mkdir -p "$native_dir"

    if [ -s "$cached" ] && [ -f "$stamp" ] && [ -f "$checksum" ] \
        && [ "$(cat "$stamp")" = "$revision" ] \
        && printf '%s  %s\n' "$(cat "$checksum")" "$cached" | sha256sum -c --status \
        && "$ndk_bin/llvm-readelf" -h "$cached" | grep -q 'AArch64'; then
        echo "[android] Using cached OpenCollab libdatachannel ($revision)"
    else
        echo "[android] Compiling OpenCollab libdatachannel for Android ARM64..."
        command -v docker >/dev/null 2>&1 || die "Docker is required to cross-compile libdatachannel"
        command -v java >/dev/null 2>&1 || die "Java is required to run the libdatachannel Gradle build"

        local checkout="$BUILD_DIR/libdatachannel-java"
        if [ ! -d "$checkout/.git" ]; then
            rm -rf "$checkout"
            git clone --filter=blob:none https://github.com/opencollab-incubator/libdatachannel-java.git "$checkout"
        fi

        git -C "$checkout" fetch --depth 1 origin "$revision"
        git -C "$checkout" checkout --force --detach "$revision"
        [ "$(git -C "$checkout" rev-parse HEAD)" = "$revision" ] || die "OpenCollab libdatachannel revision mismatch"
        git -C "$checkout" submodule update --init --recursive --depth 1

        (
            cd "$checkout"
            ./gradlew --no-daemon --max-workers=2 compileNativeForAndroidArm64V8a \
                -Plibdatachannel.targets=android-arm64-v8a \
                -Plibdatachannel.build-release-binaries=true
        )

        local binary="$checkout/build/dockcross/android-arm64-v8a/native/libdatachannel-java.so"
        [ -s "$binary" ] || die "Android libdatachannel JNI library was not built"
        "$ndk_bin/llvm-readelf" -h "$binary" | grep -q 'AArch64' || die "libdatachannel JNI library is not ARM64"
        if "$ndk_bin/llvm-readelf" -d "$binary" | grep -q 'libc.so.6'; then
            die "libdatachannel JNI library was linked against glibc instead of Android Bionic"
        fi

        mkdir -p "$cache_dir"
        cp "$binary" "$cached"
        sha256sum "$cached" | cut -d' ' -f1 > "$checksum"
        printf '%s\n' "$revision" > "$stamp"
    fi

    cp "$cached" "$native_dir/libautomcsdatachannel.so"
    echo "[android] Packaged Android-native libdatachannel into the APK"
}

setup_buildozer() {
    if [ ! -x "$VENV_DIR/bin/buildozer" ]; then
        echo "[android] Creating Buildozer environment..."
        python3 -m venv "$VENV_DIR"
        "$VENV_DIR/bin/python" -m pip install --upgrade pip wheel
        "$VENV_DIR/bin/python" -m pip install "buildozer==1.6.0" "setuptools==81.0.0" "cython==0.29.34"
    fi
}

case "$MODE" in
    stage)
        stage_source
        ;;

    debug|release)
        stage_source
        setup_java8_agent
        setup_buildozer
        setup_p4a
        setup_native
        setup_playit
        setup_libdatachannel
        mkdir -p "$BUILD_DIR/bin"

        # Retrieve application version from constants
        APP_VERSION=$(python3 -c "with open('$REPO_ROOT/source/core/constants.py','r') as f: print([l for l in f.readlines() if 'app_version' in l][0].split(' = ',1)[1][1:-2].strip())")

        # Remove previous APK output
        rm -f "$BUILD_DIR/bin/"*.apk

        cd "$ANDROID_DIR"
        echo "[android] Running Buildozer ($MODE)..."

        # Buildozer 1.6 checks VIRTUAL_ENV before installing python-for-android's host dependencies
        # Invoking the venv binary directly calls the venv's pip with --user, which pip rejects
        # Activation makes Buildozer find Cython from this environment instead of /usr/bin/cython
        (
            source "$VENV_DIR/bin/activate"

            if [ -f "$HOME/.cargo/env" ]; then
                source "$HOME/.cargo/env"
            fi

            if ! command -v rustup >/dev/null 2>&1; then
                die "Rust is required by pydantic-core and cryptography"
            fi

            rm -rf "$BUILD_DIR/.buildozer/android/platform/build-arm64-v8a/build/venv"

            buildozer -v android "$MODE"
        )

        # Move final APK to dist
        APK=$(find "$BUILD_DIR/bin" -maxdepth 1 -type f -name '*.apk' -print -quit)
        [ -n "$APK" ] || die "Build completed without producing an APK"

        mkdir -p "$DIST_DIR"

        OUTPUT="$DIST_DIR/auto-mcs-android-$APP_VERSION.apk"
        mv -f "$APK" "$OUTPUT"

        echo "[android] Compiled APK: '$OUTPUT'"
        ;;

    clean)
        echo "[android] Removing generated build tree..."
        rm -rf "$BUILD_DIR"
        ;;

    clean-all)
        echo "[android] Removing generated build tree and Buildozer environment..."
        rm -rf "$BUILD_DIR" "$VENV_DIR"
        ;;

    *)
        die "Usage: ./build.sh [stage|debug|release|clean|clean-all] [--branch NAME] [--build NUMBER] [--commit SHA] [--repo OWNER/REPO]"
        ;;
esac
