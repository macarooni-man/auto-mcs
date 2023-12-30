#!/bin/bash

export KIVY_AUDIO=ffpyplayer
pyinstaller ./auto-mcs.linux.spec --upx-dir ./upx/linux --clean
