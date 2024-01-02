#!/bin/bash

# Required for installation (Ubuntu):
# build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev xz-utils tk-dev liblzma-dev tk-dev python3-dev portaudio19-dev


# Global variables
shopt -s expand_aliases
python_path="/opt/python/3.9.18"
python=$python_path"/bin/python3.9"
venv_path="./venv"
current=$( pwd )


# Check for a set DISPLAY variable
if [ ${DISPLAY:-"unset"} == "unset" ]; then
	echo A desktop environment is required to proceed
	exit 1
fi


# First, check if a valid version of Python 3.9 is installed
version=$( $python --version )
errorlevel=$?
if [ $errorlevel -ne 0 ]; then
    echo Installing Python 3.9

	cd /tmp/
	wget https://www.python.org/ftp/python/3.9.18/Python-3.9.18.tgz
	tar xzf Python-3.9.18.tgz
	cd Python-3.9.18

	sudo ./configure --prefix=$python_path --enable-optimizations --with-lto --with-computed-gotos --with-system-ffi --enable-shared LDFLAGS="-Wl,-rpath $python_path/lib"
	sudo make -j "$(nproc)"

	sudo ./python3.9 -m test -j "$(nproc)"
	sudo make altinstall
	sudo rm /tmp/Python-3.9.18.tgz

	sudo $python -m pip install --upgrade pip setuptools wheel

	errorlevel=$?
	if [ $errorlevel -ne 0 ]; then
    	echo Something went wrong installing Python, please try again
    	exit 1
   	fi

fi

# If Python 3.9 is installed and a DE is present, check for a virtual environment
cd $current
echo Detected $version

if ! [ -d $venv_path ]; then
	echo "A virtual environment was not detected"
	$python -m venv $venv_path

else
	echo "Detected virtual environment"
fi


# Install/Upgrade packages
echo "Installing packages"
source $venv_path/bin/activate
pip install --upgrade -r ./reqs-linux.txt


# Patch and install Kivy hook for Pyinstaller
kivy_path=$venv_path"/lib64/python3.9/site-packages/kivy/tools/packaging/pyinstaller_hooks"
sed 's/from PyInstaller.compat import modname_tkinter/#/' $kivy_path/__init__.py > tmp.txt && mv tmp.txt $kivy_path/__init__.py
sed 's/excludedimports = [modname_tkinter, ]/excludedimports = [/' $kivy_path/__init__.py > tmp.txt && mv tmp.txt $kivy_path/__init__.py
python -m kivy.tools.packaging.pyinstaller_hooks hook $kivy_path/kivy-hook.py


# Build
export KIVY_AUDIO=ffpyplayer
pyinstaller ./auto-mcs.linux.spec --upx-dir ./upx/linux --clean
deactivate
echo Done! Compiled binary:  \"./dist/auto-mcs\"
