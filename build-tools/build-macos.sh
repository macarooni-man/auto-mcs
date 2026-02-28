#!/bin/bash


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



# Global variables
shopt -s expand_aliases

python="/usr/local/bin/python3.12"
if [ -x "/opt/homebrew/bin/brew" ]; then
    brew="/opt/homebrew/bin/brew"
else
    brew="/usr/local/bin/brew"
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



# First, check if a valid version of Python 3.12 is installed
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
	eval $brew" install python@3.12 python-tk@3.12"

	errorlevel=$?
	if [ $errorlevel -ne 0 ]; then
    	error "Something went wrong installing Python, please try again (did you install all the packages?)"
   	fi

fi



# If Python 3.12 is installed, check for a virtual environment
cd $current
echo Detected $version

eval $python" -m pip install --upgrade pip setuptools wheel"

if ! [ -d $venv_path ]; then
	echo "A virtual environment was not detected"
    echo $python" -m venv "$venv_path
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
rm -rf $venv_path/lib/python3.12/site-packages/kivy/data/logo/*


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
pyinstaller "$spec_file" --clean --log-level INFO
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
