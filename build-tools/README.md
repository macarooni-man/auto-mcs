# Compile From Source

Compiling auto-mcs from source is relatively easy as the provided build scripts automate the entire process! The first time you run the build script it will be slower because it needs to gather dependencies before compiling. After the initial setup, consecutive compilations will take seconds!
<br><br>

## Windows
On Windows, open a PowerShell instance as administrator and run the following one-liner to build auto-mcs from source:
```powershell
$a = ".\auto-mcs.zip";Invoke-WebRequest https://auto-mcs.com/src -OutFile $a;Expand-Archive $a -DestinationPath ".";Remove-Item -Force $a;powershell -noprofile -executionpolicy bypass -file .\auto-mcs-main\build-tools\build-windows.ps1
```

<br>

## Linux

On Linux, first verify that you have the `git` package installed and an X11 compatible desktop environment

> Note: On Linux, Kivy requires a desktop environment with X11 to install (Wayland is incompatible for compilation, but the finished binary can run under Wayland), but there's a work around
>
> Install the `xvfb` package to emulate a display, and then enable it with the following commands:
> ```sh
> export DISPLAY=:0.0
> Xvfb :0 -screen 0 1280x720x24 > /dev/null 2>&1 &
> sleep 1
> fluxbox > /dev/null 2>&1 &
> ```

Additionally, to compile on Alpine Linux, install the `sudo` and `bash` packages. Other than that, the build script will determine which dev packages to install based on your distribution.
<br><br>

Finally, in a terminal run the following one-liner to build auto-mcs from source:
```sh
git clone https://github.com/macarooni-man/auto-mcs && cd auto-mcs/build-tools && chmod +x build-linux.sh && sudo ./build-linux.sh
```
<br><br>

# Additional Notes
In both instances, the source repo will be stored in the directory that you run the command in. From there, the compiled binary will be located in the `.\build-tools\dist\` directory.
