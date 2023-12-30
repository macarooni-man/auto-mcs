CALL .\venv\Scripts\activate.bat

pyinstaller .\auto-mcs.windows.spec --upx-dir .\upx\windows --clean
