#!/bin/sh


# Use a fixed Python 3.9 path for Alpine
python="/usr/bin/python3.9"
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



# First, check if a valid version of Python 3.9 is installed
version=$( $python --version 2>/dev/null )
errorlevel=$?
if [ $errorlevel -ne 0 ]; then

    # Check for apk
    apkver=$( apk --version 2>/dev/null )
    errorlevel=$?
    if [ $errorlevel -ne 0 ]; then
        error "This script requires Alpine (apk) or a preinstalled Python 3.9"
    fi

    echo "Obtaining packages to install Python and build tools"
    # Install appropriate packages
    # (X server bits for Kivy/PyInstaller, toolchain for building wheels)
    apk add --no-cache \
        bash coreutils \
        python3=3.9.13-r* python3-dev=3.9.13-r* py3-pip=22.* \
        gcc g++ make musl-dev linux-headers \
        zlib-dev libffi-dev \
        pangomm-dev pkgconfig \
        mtdev-dev mtdev \
        xvfb fluxbox

    errorlevel=$?
    if [ $errorlevel -ne 0 ]; then
        error "Something went wrong installing packages, please try again"
    fi

    # After install, prefer python3.9 explicitly
    python="/usr/bin/python3.9"
    version=$( $python --version 2>/dev/null ) || true
fi



# If Python 3.9 is installed, check for a virtual environment
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

# Remove Kivy icons to prevent dock flickering (harmless if absent)
rm -rf $venv_path/lib/python3.9/site-packages/kivy/data/logo/*



# Start minimal X (best-effort, mirrors CI)
export DISPLAY=:0.0
Xvfb :0 -screen 0 1280x720x24 > /dev/null 2>&1 &
sleep 1
fluxbox > /dev/null 2>&1 &


# Rebuild locales.json
# python locale-gen.py


# Build
echo Compiling auto-mcs
export KIVY_AUDIO=ffpyplayer
cd $current
cp $spec_file ../source
cd ../source
pyinstaller "$spec_file" --clean
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
