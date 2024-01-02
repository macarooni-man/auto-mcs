#!/bin/bash

# Required for installation:
# python3.9, python3-tkinter, python3-dev, portaudio-dev, 


# Global variables
shopt -s expand_aliases
alias python="/usr/bin/python3.9"
version=$( python --version )
errorlevel=$?
venv_path="./venv"


# First, check if a valid version of Python 3.9 is installed
if [ $errorlevel -ne 0 ]; then
    echo Please install Python 3.9 to proceed
    exit 1

else

	# Check for a set DISPLAY variable
	if [ ${DISPLAY:-"unset"} == "unset" ]; then
		echo A desktop environment is required to proceed
    	exit 1
	fi


	# If Python 3.9 is installed and a DE is present, check for a virtual environment
    echo Detected $version

	if ! [ -d $venv_path ]; then
		echo "A virtual environment was not detected"
		python -m venv $venv_path

	else
		echo "Detected virtual environment"
	fi


	# Install/Upgrade packages
	echo "Installing packages"
	source $venv_path/bin/activate
	python -m pip install --upgrade -r ./reqs-linux.txt


	# Patch and install Kivy hook for Pyinstaller
	kivy_path=$venv_path"/lib64/python3.9/site-packages/kivy/tools/packaging/pyinstaller_hooks"
	sed 's/from PyInstaller.compat import modname_tkinter/#/' $kivy_path/__init__.py
	sed 's/excludedimports = [modname_tkinter, ]/excludedimports = [/' $kivy_path/__init__.py
	python3.9 -m kivy.tools.packaging.pyinstaller_hooks hook $kivy_path/kivy-hook.py


	# Build
	export KIVY_AUDIO=ffpyplayer
    pyinstaller ./auto-mcs.linux.spec --upx-dir ./upx/linux --clean
    deactivate
    echo Done! Compiled binary:  \"./dist/auto-mcs\"
fi
