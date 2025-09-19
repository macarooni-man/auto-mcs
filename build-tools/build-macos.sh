#!/bin/bash



# Global variables
shopt -s expand_aliases

# Use different paths for different architectures
if [ "$(uname -m)" = "x86_64" ]; then
	python="/usr/local/bin/python3.9"
	brew="/usr/local/bin/brew"
else
	python="/opt/homebrew/opt/python@3.9/libexec/bin/python3"
	brew="/opt/homebrew/bin/brew"
fi
venv_path="./venv"
spec_file="auto-mcs.macos.spec"



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
version=$( $python --version )
errorlevel=$?
if [ $errorlevel -ne 0 ]; then


	# Check if brew is installed
	brewversion=$( $brew --version )
	errorlevel=$?
	if [ $errorlevel -ne 0 ]; then
		echo Installing the homebrew package manager
		/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
	fi

	brewversion=$( $brew --version )
	errorlevel=$?
	if [ $errorlevel -ne 0 ]; then
		error "This script requires the homebrew package manager to run"
	fi

	echo Detected $brewversion

	echo Obtaining packages to install Python

	# Install appropriate packages
	eval $brew" install python@3.9 python-tk@3.9"

	errorlevel=$?
	if [ $errorlevel -ne 0 ]; then
    	error "Something went wrong installing Python, please try again (did you install all the packages?)"
   	fi

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
pip install --upgrade -r ./reqs-macos.txt

# Remove Kivy icons to prevent dock flickering
rm -rf $venv_path/lib/python3.9/site-packages/kivy/data/logo/*


# Rebuild locales.json
# python locale-gen.py


# Build
echo Compiling auto-mcs
export KIVY_AUDIO=ffpyplayer
cd $current
cp $spec_file ../source
cd ../source
rm -rf build/
rm -rf dist/
pyinstaller "$spec_file" --clean
cd $current
rm -rf ../source/$spec_file
rm -rf ../source/dist/auto-mcs
rm -rf ./dist
mv -f ../source/dist .
deactivate

# Check if compiled
if ! [ -d $current/dist/auto-mcs.app ]; then
	error "[FAIL] Something went wrong during compilation"
else
	chmod +x $current/dist/auto-mcs.app/Contents/MacOS/auto-mcs
	echo [SUCCESS] Compiled binary:  \"$current/dist/auto-mcs.app\"
fi
