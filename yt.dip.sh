#!/bin/bash

# Capture the first argument as the URL
URL=$1
DOWNLOAD_DIR=$2
# Check if URL is provided
if [ -z "$URL" ]; then
    echo "No URL provided."
    exit 1
fi


# Use yt-dlp to get the filename without downloading
FILENAME=$(yt-dlp --get-filename -o "%(title)s.%(ext)s" "$URL")

# Perform the actual download using the determined filename
OUTPUT=$(yt-dlp "$URL" -o "$DOWNLOAD_DIR/$FILENAME" 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo "Error: yt-dlp failed with exit code $EXIT_CODE"
    echo "Error Message: $OUTPUT" | grep "ERROR:"  # Filter and display only error messages
    exit $EXIT_CODE
fi
# Echo the filename back to the caller
echo "$FILENAME"