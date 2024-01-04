# Global variables
$python = '"%localappdata%\Programs\Python\Python39\python.exe"'
$venv_path = ".\venv"
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
$version = cmd /c "$python --version" | Tee-Object -Variable result
if (!$version) {

    ## Define the download URL and the destination
    #$python_url = "https://www.python.org/ftp/python/3.9.18/python-3.9.18-amd64.exe"
    #$destination = "$env:TEMP\python-3.9.18.exe"
    #
    ## Download Python installer
    #Invoke-WebRequest -Uri $python_url -OutFile $destination
    #
    ## Install Python silently
    #Start-Process -FilePath "$env:TEMP\python_installer.exe" -ArgumentList "/S" -Wait
    #
    ## 

}


#:: CALL .\venv\Scripts\activate.bat
#
#:: Compile application
#pyinstaller .\auto-mcs.windows.spec --upx-dir .\upx\windows --clean