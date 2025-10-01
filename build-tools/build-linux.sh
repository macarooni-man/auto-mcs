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
python_path="/opt/python/3.12.8"

# Locate python3.12 if it exists, otherwise set the default dir for building from source
if [[ -n "${pythonLocation:-}" && -x "$pythonLocation/bin/python3.12" ]]; then
  python="$pythonLocation/bin/python3.12"
elif command -v python3.12 >/dev/null 2>&1; then
  python="$(command -v python3.12)"
elif [[ -x /usr/bin/python3.12 ]]; then
  python="/usr/bin/python3.12"
elif ls /opt/hostedtoolcache/Python/3.12.*/x64/bin/python3.12 >/dev/null 2>&1; then
  python="$(ls -d /opt/hostedtoolcache/Python/3.12.*/x64/bin/python3.12 | head -n1)"
else
  python="/opt/python/3.12.8/bin/python3.12"
fi

library_path=$( ldconfig -v 2>/dev/null | cut -d'/' -f1-3 | head -n1 )
ssl_path="/opt/openssl"
tk_path="/opt/tk"
tcl_path="/opt/tcl"
venv_path="./venv"
spec_file="auto-mcs.linux.spec"

# Overwrite current directory
cd "$(cd -P -- "$(dirname -- "$0")" && pwd -P)"
current=$( pwd )



error () {
    { printf '\E[31m'; echo "$@"; printf '\E[0m'; } >&2
    cd $current
    exit 1
}

runas() {
	# Run command as the current user in CI, or when not running as root
    if [[ "${CI:-}" == "true" ]] || ! whoami | grep -q "root"; then
        "$@"
    
	# Run command as the login user outside CI
    else
        local cmd
        cmd=$(printf '%q ' "$@")
        su "$(logname)" -c "$cmd"
    fi
}



# Check for a set DISPLAY variable
if [ ${DISPLAY:-"unset"} == "unset" ]; then
	error "A desktop environment is required to proceed"
fi


# First, check if a valid version of Python 3.12 is installed
version=$( $python --version )
errorlevel=$?
if [ $errorlevel -ne 0 ]; then

	# Force script to be run as root if it requires an installation
	if ! whoami | grep -q "root"; then
		error "This script requires root privileges to install Python"
	fi


	echo Obtaining packages to build Python from source

	# Determine system package manager and install appropriate packages
	if [ -x "$(command -v apt)" ];       then apt install -y build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev xz-utils liblzma-dev python3-dev libfreetype-dev libfreetype6 libasound2 libasound-dev libasound2-dev portaudio19-dev
	elif [ -x "$(command -v dnf)" ];     then dnf -y groupinstall "Development Tools" && sudo dnf -y install wget gcc bzip2-devel libffi-devel xz-devel freetype-devel portaudio-devel
	elif [ -x "$(command -v yum)" ];     then yum -y groupinstall "Development Tools" && sudo dnf -y install wget gcc bzip2-devel libffi-devel xz-devel freetype-devel portaudio-devel
	elif [ -x "$(command -v pacman)" ];  then pacman -S --noconfirm base-devel wget openssl-1.1 tk freetype2 portaudio
	else echo "[WARNING] Package manager not found: You must manually install the Python 3.12 source dependencies">&2; fi



	# Download and compile OpenSSL from source
	echo Installing OpenSSL 1.1.1

	cd /tmp/
	wget https://www.openssl.org/source/openssl-1.1.1g.tar.gz --no-check-certificate
	tar xzf openssl-1.1.1g.tar.gz
	cd openssl-1.1.1g

	mkdir -p $ssl_path/lib
	./config --prefix=$ssl_path --openssldir=$ssl_path shared zlib
	make
	make install



	# Download and compile Tk/TCL from source
	echo Installing Tk/TCL

	cd /tmp/
	wget http://prdownloads.sourceforge.net/tcl/tcl8.6.13-src.tar.gz --no-check-certificate
	wget http://prdownloads.sourceforge.net/tcl/tk8.6.13-src.tar.gz --no-check-certificate
	tar xzf tcl8.6.13-src.tar.gz
	tar xzf tk8.6.13-src.tar.gz
	cp -R /tmp/tcl8.6.13 $tcl_path
	cp -R /tmp/tk8.6.13 $tk_path

	cd $tcl_path/unix
	./configure --prefix=$tcl_path --exec-prefix=$tcl_path --with-freetype=$library_path/libfreetype.so.6
	make
	make install

	cd $tk_path/unix
	./configure --prefix=$tk_path --exec-prefix=$tk_path --with-tcl=$tcl_path/unix --with-freetype=$library_path/libfreetype.so.6



	# Finally, download and compile Python from source
	echo Installing Python 3.12

	cd /tmp/
	wget https://www.python.org/ftp/python/3.12.8/Python-3.12.8.tgz
	tar xzf Python-3.12.8.tgz
	cd Python-3.12.8

	mkdir -p $python_path/lib

	# Configure Python with correct OpenSSL paths
	./configure --prefix=$python_path \
	            --enable-optimizations \
	            --with-lto \
	            --with-computed-gotos \
	            --with-system-ffi \
	            --with-openssl=$ssl_path \
	            --enable-shared \
	            LDFLAGS="-Wl,-rpath,$python_path/lib -L$ssl_path/lib" \
	            CPPFLAGS="-I$ssl_path/include"

	make -j "$(nproc)"
	make altinstall
	rm /tmp/Python-3.12.8.tgz

	errorlevel=$?
	if [ $errorlevel -ne 0 ]; then
    	error "Something went wrong installing Python, please try again (did you install all the packages?)"
   	fi

fi



# If Python 3.12 is installed and a DE is present, check for a virtual environment
cd $current
echo Detected $version

runas $python -m pip install --upgrade pip setuptools wheel

if ! [ -d $venv_path ]; then
	echo "A virtual environment was not detected"
	runas $python -m venv "$venv_path"

else
	echo "Detected virtual environment"
fi



# Install/Upgrade packages
echo "Installing packages"
source $venv_path/bin/activate
runas pip install --upgrade -r ./reqs-linux.txt


# Patch and install Kivy hook for Pyinstaller
patch() {
	kivy_path=$1"/python3.12/site-packages/kivy/tools/packaging/pyinstaller_hooks"
	sed -i 's/from PyInstaller.compat import modname_tkinter/#/' $kivy_path/__init__.py
	sed -i 's/excludedimports = \[modname_tkinter, /excludedimports = [/' $kivy_path/__init__.py
	runas "$venv_path/bin/python3.12" -m kivy.tools.packaging.pyinstaller_hooks hook "$kivy_path/kivy-hook.py"
}
patch $venv_path"/lib"
patch $venv_path"/lib64"


# Patch plyer (pull #822)
FILECHOOSER="$venv_path/lib/python3.12/site-packages/plyer/platforms/linux/filechooser.py"
sed -i 's/--confirm-overwrite//g' "$FILECHOOSER"
sed -i '/self\.title/d' "$FILECHOOSER"
sed -i '/self\.icon/d' "$FILECHOOSER"


# Install Consolas if it doesn't exist and reload font cache
if ! ls /usr/share/fonts/Consolas* 1> /dev/null 2>&1; then
    echo Installing Consolas font
    cp -f ../source/ui/assets/fonts/Consolas* /usr/share/fonts
	fc-cache -f
fi


# Rebuild locales.json
# runas python locale-gen.py


# Build
echo Compiling auto-mcs
export KIVY_AUDIO=ffpyplayer
cd $current
cp $spec_file ../source
cd ../source
chmod +x $current/upx/linux/*
runas pyinstaller "$spec_file" --upx-dir "$current/upx/linux" --clean --log-level INFO
cd $current
rm -rf ../source/$spec_file
mv -f ../source/dist .
deactivate


# Check if compiled
if ! [ -f $current/dist/auto-mcs ]; then
	error "[FAIL] Something went wrong during compilation"
else
	chmod +x $current/dist/auto-mcs
	echo [SUCCESS] Compiled binary:  \"$current/dist/auto-mcs\"
fi


# Patch the binary with a C shim that prevents splash screen from loading on headless
cat > dist/.loader.c <<'EOF'
#define _GNU_SOURCE
#include <fcntl.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <unistd.h>
extern char **environ;
#ifndef MFD_CLOEXEC
#define MFD_CLOEXEC 0x0001U
#endif
static int mfd(const char *n, unsigned f){
#ifdef SYS_memfd_create
  return syscall(SYS_memfd_create,n,f);
#else
  return -1;
#endif
}
static void die(const char *m){ perror(m); _exit(1); }
static bool headless(int ac,char**av){
  const char*d=getenv("DISPLAY"); if(!d||!*d) return true;
  for(int i=1;i<ac;i++) if(!strcmp(av[i],"--headless")||!strcmp(av[i],"-s")) return true;
  return false;
}
int main(int ac,char**av){
  if(headless(ac,av)) setenv("PYINSTALLER_SUPPRESS_SPLASH_SCREEN","1",1);
  else { const char*v=getenv("PYINSTALLER_SUPPRESS_SPLASH_SCREEN"); if(v&&strcmp(v,"1")==0) unsetenv("PYINSTALLER_SUPPRESS_SPLASH_SCREEN"); }

  int exe=open("/proc/self/exe",O_RDONLY); if(exe<0) die("open self");
  off_t sz=lseek(exe,0,SEEK_END); if(sz<0) die("size");
  if(lseek(exe,0,SEEK_SET)<0) die("seek");
  char *buf=(char*)mmap(NULL,(size_t)sz,PROT_READ,MAP_PRIVATE,exe,0); if(buf==MAP_FAILED) die("mmap");
  close(exe);

  const char *mk = "\n__EMBEDDED_ELF_FOLLOWS__\n";
  size_t mklen = strlen(mk);

  /* find the marker followed by ELF magic */
  char *found = NULL, *scan = buf;
  while (1) {
    size_t remain = (size_t)sz - (size_t)(scan - buf);
    char *q = memmem(scan, remain, mk, mklen);
    if (!q) break;
    if ((size_t)sz - (size_t)(q - buf) >= mklen + 4 &&
        memcmp(q + mklen, "\x7F""ELF", 4) == 0) { found = q; break; }
    scan = q + 1;
  }
  if (!found) { (void)!write(2,"marker not found\n",17); _exit(1); }

  size_t off = (size_t)(found - buf) + mklen;
  size_t plen = (size_t)sz - off;
  if (plen < 4) { (void)!write(2,"no ELF payload\n",15); _exit(1); }

  int fd=mfd("embed",MFD_CLOEXEC); if(fd==-1) die("memfd_create");
  ssize_t w=write(fd,buf+off,plen); if(w<0 || (size_t)w!=plen) die("write memfd");
  fexecve(fd,av,environ); die("fexecve");
}
EOF

echo "Building splash handler wrapper"
gcc -O2 -s -o dist/.loader dist/.loader.c || error "Failed to build wrapper"

( cat dist/.loader; printf "\n__EMBEDDED_ELF_FOLLOWS__\n"; cat dist/auto-mcs ) > dist/.auto-mcs.single || error "Failed to assemble binary"
mv -f dist/.auto-mcs.single dist/auto-mcs
chmod +x dist/auto-mcs
rm -f dist/.loader dist/.loader.c
echo "[SUCCESS] Patched binary: \"$current/dist/auto-mcs\""
