#!/usr/bin/env bash
set -euo pipefail

ANDROID_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$ANDROID_DIR/.." && pwd)"
BUILD_DIR="$ANDROID_DIR/build"
STAGE_DIR="$BUILD_DIR/app"
VENV_DIR="$ANDROID_DIR/.venv"
P4A_DIR="$BUILD_DIR/python-for-android"
P4A_COMMIT="58d21141f17c889bf8585f5665921d72028f8831"
MODE="${1:-debug}"

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
    cp "$ANDROID_DIR/source/android_runtime.py" "$STAGE_DIR/android_runtime.py"
    cp "$ANDROID_DIR/source/psutil.py" "$STAGE_DIR/psutil.py"
    cp "$ANDROID_DIR/source/bcrypt.py" "$STAGE_DIR/bcrypt.py"

    # Build metadata remains inside the generated source tree.
    BRANCH="$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || printf 'unknown')"
    COMMIT="$(git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null || printf 'unknown')"
    REPO="$(git -C "$REPO_ROOT" config --get remote.origin.url 2>/dev/null || printf 'macarooni-man/auto-mcs')"
    REPO="${REPO%.git}"
    REPO="${REPO#https://github.com/}"
    REPO="${REPO#http://github.com/}"
    REPO="${REPO#git@github.com:}"

    python3 - "$STAGE_DIR/source/build-data.json" "$BRANCH" "$COMMIT" "$REPO" <<'PY'
import json
import sys

path, branch, commit, repo = sys.argv[1:]
data = {
    "type": "development",
    "version": None,
    "branch": branch,
    "commit": commit,
    "repo": repo,
}
with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
PY

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

        cd "$ANDROID_DIR"
        echo "[android] Running Buildozer ($MODE)..."

        # Buildozer 1.6 checks VIRTUAL_ENV before installing python-for-android's
        # host dependencies. Invoking the venv binary directly is not enough:
        # without activation it calls the venv's pip with --user, which pip
        # rejects. Activation also makes Buildozer find the pinned Cython from
        # this environment instead of /usr/bin/cython.
        (
            source "$VENV_DIR/bin/activate"
            buildozer -v android "$MODE"
        )
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
        die "Usage: ./build.sh [stage|debug|release|clean|clean-all]"
        ;;
esac
