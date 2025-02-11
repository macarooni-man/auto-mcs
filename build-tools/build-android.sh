#!/bin/bash


# Clean-up existing builds
rm rf ./bin/*.apk

# Activate virtual environment
source ./venv/bin/activate




# Copy override modules to the source directory
cp android-overrides/*.py ../source

# Build auto-mcs
buildozer android debug
# buildozer android release




# Remove copied override modules from the source directory
for file in android-overrides/*.py; do
    filename=$(basename "$file")
    rm -f ../source/$filename
done
