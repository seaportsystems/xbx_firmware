#!/bin/bash

# Script to copy the current repository to the CIRCUITPY drive

# Define the CIRCUITPY mount point
CIRCUITPY_MOUNT="/Volumes/CIRCUITPY"

# Check if CIRCUITPY is mounted
if [ ! -d "$CIRCUITPY_MOUNT" ]; then
  echo "Error: CIRCUITPY drive is not mounted at $CIRCUITPY_MOUNT."
  exit 1
fi

# Confirm action with the user
echo "This will overwrite files on the CIRCUITPY drive except the certs/ folder and the settings.toml file. Do you want to continue? (y/n)"
read -r CONFIRM
if [ "$CONFIRM" != "y" ]; then
  echo "Operation cancelled."
  exit 0
fi

# Remove all files on CIRCUITPY except certs/ folder and settings.toml
echo "Clearing the CIRCUITPY drive except certs/ folder and settings.toml..."
find "$CIRCUITPY_MOUNT" -mindepth 1 \( ! -path "$CIRCUITPY_MOUNT/certs" ! -path "$CIRCUITPY_MOUNT/certs/*" ! -name "settings.toml" \) -exec rm -rf {} +
if [ $? -ne 0 ]; then
  echo "Error: Failed to clear the CIRCUITPY drive. Check permissions."
  exit 1
fi

# Copy the repository to CIRCUITPY using rsync
echo "Copying repository files to CIRCUITPY..."
rsync -av --exclude="certs/" --exclude="settings.toml" ./ "$CIRCUITPY_MOUNT/"
if [ $? -eq 0 ]; then
  echo "Repository successfully copied to CIRCUITPY."
else
  echo "Error: Failed to copy files. Check permissions and available space."
  exit 1
fi

