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


    # -------------------------------------------- Android Overlay -----------------------------------------------------

    echo "[android] Applying Android-only patches to generated source..."
    python3 "$ANDROID_DIR/patches/apply.py" "$STAGE_DIR"
    echo "[android] Staged build tree: $STAGE_DIR"
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
        setup_buildozer
        setup_p4a
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
