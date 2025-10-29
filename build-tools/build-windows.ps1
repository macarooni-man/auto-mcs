param(
  [string]$branch,
  [string]$build,
  [string]$commit,
  [string]$repo
)

# Create CI 'build-data.json'
if ($env:CI -eq $true) {

    function Write-BuildJson {
        param(
            [Parameter(Mandatory=$false)][string]$branch,
            [Parameter(Mandatory=$false)][string]$build,
            [Parameter(Mandatory=$false)][string]$commit,
            [Parameter(Mandatory=$false)][string]$repo
        )

        # Don't create the file if parameters are missing
        $missing = @()
        if ([string]::IsNullOrWhiteSpace($branch)) { $missing += "--branch" }
        if ([string]::IsNullOrWhiteSpace($build))  { $missing += "--build"  }
        if ([string]::IsNullOrWhiteSpace($commit)) { $missing += "--commit" }
        if ([string]::IsNullOrWhiteSpace($repo))   { $missing += "--repo" }

        if ($missing.Count -gt 0) {
            Write-Warning ("Missing value for: {0}. Skipping 'build-data.json'" -f ($missing -join ", "))
            return
        }

        $type = if ($branch -eq "main") { "release" } else { "development" }

        $script_dir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
        $repo_root  = Join-Path $script_dir ".."
        $out_path   = Join-Path $repo_root "source\build-data.json"

        # Ensure directory exists
        $out_dir = Split-Path -Parent $out_path
        if (-not (Test-Path -LiteralPath $out_dir)) {
            $null = New-Item -ItemType Directory -Path $out_dir -Force
        }

        # Keep version as string to avoid numeric-only constraint
        $obj = [ordered]@{
            type    = $type
            version = "$build"
            branch  = $branch
            commit  = $commit
            repo    = $repo
        }

        $json = $obj | ConvertTo-Json -Compress

        # Write UTF-8 without BOM via .NET
        $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
        [System.IO.File]::WriteAllText($out_path, $json, $utf8NoBom)

        Write-Host "Wrote $out_path"
    }

    Write-BuildJson -branch $branch -build $build -commit $commit -repo $repo
}



# Global variables
$python     = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
$venv_path  = ".\venv"
$start_venv = "CALL $venv_path\Scripts\activate.bat"
$spec_file  = "auto-mcs.windows.spec"

# Overwrite current directory
$current = Split-Path $MyInvocation.MyCommand.Path
cd $current



function error {
    param ([string]$message)
 
    Write-host -f Red $message
    exit 1
}



# First, check if a valid version of Python 3.12 is installed
try { $version = Invoke-Command { cmd /c "`"$python`" --version 2^> nul" } -ErrorAction Stop | Tee-Object -Variable result } catch { $version = $null }
if (-not $version) {

    # Force script to be run as admin if it requires an installation
    if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        error "This script requires administrator privileges to install Python"
    }

    
    # Download and install C++ Build Tools
    echo "Downloading and installing C++ Build Tools"
    $bt_url = "https://aka.ms/vs/17/release/vs_BuildTools.exe/"
    $dest_bt = "$env:TEMP\build-tools.exe"
    $arguments = "--norestart --passive --wait --downloadThenInstall --includeRecommended --add Microsoft.VisualStudio.Workload.NativeDesktop --add Microsoft.VisualStudio.Workload.VCTools --add Microsoft.VisualStudio.Workload.MSBuildTools"
    echo "Downloading Build Tools to `"$dest_bt`""
    Invoke-WebRequest -Uri $bt_url -OutFile $dest_bt

    echo "Installing Build Tools"
    Start-Process -FilePath $dest_bt -ArgumentList $arguments -Wait


    # Download and install Python 3.12
    $python_down_ver = "3.12.8"
    echo "Downloading and installing Python $python_down_ver"
    $python_url = "https://www.python.org/ftp/python/$python_down_ver/python-$python_down_ver-amd64.exe"
    $dest_py = "$env:TEMP\python_installer-$python_down_ver.exe"
    echo "Downloading Python to `"$dest_py`""
    Invoke-WebRequest -Uri $python_url -OutFile $dest_py

    echo "Installing Python"
    Start-Process -FilePath $dest_py -ArgumentList "/S" -Wait

    if (-not (Test-Path $python)) {
        error "Something went wrong installing Python, please try again"
    }
}

# If Python 3.12 is installed, check for a virtual environment
cd $current
echo "Detected $version"

cmd /c "`"$python`" -m pip install --upgrade pip setuptools wheel"

if (-not (Test-Path $venv_path)) {
    echo "A virtual environment was not detected"
    cmd /c "`"$python`" -m venv $venv_path"

} else { echo "Detected virtual environment" }


# Install/Upgrade packages
echo "Installing packages"
cmd /c "$start_venv && pip install --upgrade -r ./reqs-windows.txt"


# Patch and install Kivy hook for Pyinstaller
.\venv\Scripts\Activate.ps1
$kivy_path = "$venv_path\Lib\site-packages\kivy\tools\packaging\pyinstaller_hooks"
((Get-Content -Path "$kivy_path/__init__.py" ) -replace "from PyInstaller.compat import modname_tkinter","#") | Set-Content -Path "$kivy_path/__init__.py"
((Get-Content -Path "$kivy_path/__init__.py" ) -replace "excludedimports = \[modname_tkinter, ","excludedimports = [") | Set-Content -Path "$kivy_path/__init__.py"
((Get-Content -Path "$kivy_path/__init__.py" ) -replace "from os import environ","from os import environ`nfrom kivy_deps import angle`nenviron['KIVY_GL_BACKEND'] = 'angle_sdl2'") | Set-Content -Path "$kivy_path/__init__.py"
python -m kivy.tools.packaging.pyinstaller_hooks hook "$kivy_path/kivy-hook.py"


# Rebuild locales.json
# python locale-gen.py

# Overwrite PyInstaller bootloader with the custom built one
Copy-Item -Force "$PSScriptRoot\utils\bootloader\windows\runw.exe" "$venv_path\Lib\site-packages\PyInstaller\bootloader\Windows-64bit-intel"

# Build
echo "Compiling auto-mcs"
cd $current
Copy-Item -Force $spec_file ..\source
cd ..\source
pyinstaller $spec_file --clean --log-level INFO 2>&1
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