# Global variables
$python = "$env:LOCALAPPDATA\Programs\Python\Python39\python.exe"
$venv_path = ".\venv"
$start_venv = "CALL $venv_path\Scripts\activate.bat"
$spec_file = "auto-mcs.windows.spec"

# Overwrite current directory
$current = Split-Path $MyInvocation.MyCommand.Path
cd $current



function error {
    param ([string]$message)
 
    Write-host -f Red $message
    exit 1
}
 


# Force script to be run as admin
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    error "This script requires administrator privileges to run"
}


# First, check if a valid version of Python 3.9 is installed
try { $version = Invoke-Command { cmd /c "`"$python`" --version 2> null" } -ErrorAction Stop | Tee-Object -Variable result } catch { $version = $null }
if (-not $version) {
    
    # Download and install C++ Build Tools
    echo "Downloading and installing C++ Build Tools"
    $bt_url = "https://aka.ms/vs/17/release/vs_BuildTools.exe/"
    $dest_bt = "$env:TEMP\build-tools.exe"
    $arguments = "--norestart --passive --wait --downloadThenInstall --includeRecommended --add Microsoft.VisualStudio.Workload.NativeDesktop --add Microsoft.VisualStudio.Workload.VCTools --add Microsoft.VisualStudio.Workload.MSBuildTools"
    echo "Downloading Build Tools to `"$dest_bt`""
    Invoke-WebRequest -Uri $bt_url -OutFile $dest_bt

    echo "Installing Build Tools"
    Start-Process -FilePath $dest_bt -ArgumentList $arguments -Wait


    # Download and install Python 3.9
    echo "Downloading and installing Python 3.9"
    $python_url = "https://www.python.org/ftp/python/3.9.13/python-3.9.13-amd64.exe"
    $dest_py = "$env:TEMP\python_installer-3.9.13.exe"
    echo "Downloading Python to `"$dest_py`""
    Invoke-WebRequest -Uri $python_url -OutFile $dest_py

    echo "Installing Python"
    Start-Process -FilePath $dest_py -ArgumentList "/S" -Wait

    if (-not (Test-Path $python)) {
        error "Something went wrong installing Python, please try again"
    }
}

# If Python 3.9 is installed and a DE is present, check for a virtual environment
cd $current
echo "Detected $version"

if (-not (Test-Path $venv_path)) {
    echo "A virtual environment was not detected"
    cmd /c "`"$python`" -m venv $venv_path"

} else { echo "Detected virtual environment" }


# Install/Upgrade packages
echo "Installing packages"
cmd /c "$start_venv && pip install --upgrade pip setuptools wheel"
cmd /c "$start_venv && pip install --upgrade -r ./reqs-windows.txt"


# Patch and install Kivy hook for Pyinstaller
.\venv\Scripts\Activate.ps1
$kivy_path= "$venv_path\Lib\site-packages\kivy\tools\packaging\pyinstaller_hooks"
((Get-Content -Path "$kivy_path/__init__.py" ) -replace "from PyInstaller.compat import modname_tkinter","#") | Set-Content -Path "$kivy_path/__init__.py"
((Get-Content -Path "$kivy_path/__init__.py" ) -replace "excludedimports = \[modname_tkinter, ","excludedimports = [") | Set-Content -Path "$kivy_path/__init__.py"
((Get-Content -Path "$kivy_path/__init__.py" ) -replace "from os import environ","from os import environ`nfrom kivy_deps import angle`nenviron['KIVY_GL_BACKEND'] = 'angle_sdl2'") | Set-Content -Path "$kivy_path/__init__.py"
python -m kivy.tools.packaging.pyinstaller_hooks hook "$kivy_path/kivy-hook.py"


# Rebuild locales.json
# python locale-gen.py


# Build
echo "Compiling auto-mcs"
cd $current
Copy-Item -Force $spec_file ..\source
cd ..\source
pyinstaller $spec_file --upx-dir $current\upx\windows --clean 2>&1
cd $current
Remove-Item -Force ..\source\$spec_file
Remove-Item -Force .\dist -ErrorAction SilentlyContinue -Recurse
Move-Item -Force ..\source\dist .
deactivate


# Check if compiled
if (-not (Test-Path "$current\dist\auto-mcs.exe")) {
	error "[FAIL] Something went wrong during compilation"
} else {
	echo "[SUCCESS] Compiled executable:  `"$current\dist\auto-mcs.exe`""
}
