#!/bin/bash

export KIVY_AUDIO=ffpyplayer
pyinstaller ./auto-mcs.windows.spec --clean
