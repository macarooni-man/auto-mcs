#!/bin/sh


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

        # Path of this script when executed directly
        here=$(cd "$(dirname "$0")" && pwd)
        repo_root=$(cd "$here/.." && pwd)
        out="$repo_root/source/build-data.json"

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



# Use a fixed Python 3.12 path for Alpine
python="/usr/bin/python3.12"
venv_path="./venv"
spec_file="auto-mcs.docker.spec"


# Overwrite current directory
cd "$(cd -P -- "$(dirname -- "$0")" && pwd -P)"
current=$( pwd )


error ()
{
    { printf '\E[31m'; echo "$@"; printf '\E[0m'; } >&2
    cd $current
    exit 1
}



# First, check if a valid version of Python 3.12 is installed
version=$( $python --version 2>/dev/null )
errorlevel=$?
if [ $errorlevel -ne 0 ]; then

    # Check for apk
    apkver=$( apk --version 2>/dev/null )
    errorlevel=$?
    if [ $errorlevel -ne 0 ]; then
        error "This script requires Alpine (apk) or a preinstalled Python 3.12"
    fi

    echo "Obtaining packages to install Python and build tools"
    # Install appropriate packages
    # (X server bits for PyInstaller, toolchain for building wheels)
    apk add --no-cache \
        bash coreutils \
        python3=3.12.8-r* python3-dev=3.12.8-r* py3-pip=22.* \
        gcc g++ make musl-dev linux-headers \
        zlib-dev libffi-dev \
        pangomm-dev pkgconfig \
        mtdev-dev mtdev \
        xvfb fluxbox

    errorlevel=$?
    if [ $errorlevel -ne 0 ]; then
        error "Something went wrong installing packages, please try again"
    fi

    # After install, prefer python3.12 explicitly
    python="/usr/bin/python3.12"
    version=$( $python --version 2>/dev/null ) || true
fi



# If Python 3.12 is installed, check for a virtual environment
cd $current
echo Detected $version

eval $python" -m pip install --upgrade pip setuptools wheel"

if ! [ -d $venv_path ]; then
    echo "A virtual environment was not detected"
    eval $python" -m venv "$venv_path

else
    echo "Detected virtual environment"
fi



# Install/Upgrade packages
echo "Installing packages"
source $venv_path/bin/activate
pip install --upgrade pip setuptools wheel

# Alpine/Docker requirements (same list used in CI previously)
if ! [ -f ./reqs-docker.txt ]; then
    error "Missing ./reqs-docker.txt"
fi
pip install --upgrade -r ./reqs-docker.txt



# Rebuild locales.json
# python locale-gen.py


# Build
echo Compiling auto-mcs
export KIVY_AUDIO=ffpyplayer
cd $current
cp $spec_file ../source
cd ../source
pyinstaller "$spec_file" --noupx --clean --log-level INFO
cd $current
rm -rf ../source/$spec_file
rm -rf ./dist
mv -f ../source/dist .
deactivate


# Check if compiled
if ! [ -f $current/dist/auto-mcs ]; then
    error "[FAIL] Something went wrong during compilation"
else
    chmod +x $current/dist/auto-mcs
    echo [SUCCESS] Compiled binary:  \"$current/dist/auto-mcs\"
fi
