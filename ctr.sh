#!/bin/bash

# Script to copy the contents of the CIRCUITPY drive into the current repository

# Define the CIRCUITPY mount point
CIRCUITPY_MOUNT="/Volumes/CIRCUITPY"

# Check if CIRCUITPY is mounted
if [ ! -d "$CIRCUITPY_MOUNT" ]; then
  echo "Error: CIRCUITPY drive is not mounted at $CIRCUITPY_MOUNT."
  exit 1
fi

# Confirm action with the user
echo "This will copy the contents of CIRCUITPY into the current repository, overwriting existing files. Do you want to continue? (y/n)"
read -r CONFIRM
if [ "$CONFIRM" != "y" ]; then
  echo "Operation cancelled."
  exit 0
fi

# Copy the contents of CIRCUITPY to the repository
echo "Copying CIRCUITPY contents to the repository..."
rsync -av --exclude="certs/" --exclude="settings.toml" "$CIRCUITPY_MOUNT/" ./
if [ $? -eq 0 ]; then
  echo "CIRCUITPY contents successfully copied to the repository."
else
  echo "Error: Failed to copy files. Check permissions and available space."
  exit 1
fi
