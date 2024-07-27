import os

# try:
#     test = os.environ['DISPLAY']
# except:
    # Suppress splash if headless
print('TEST')
os.environ['PYINSTALLER_SUPPRESS_SPLASH_SCREEN'] = '1'
