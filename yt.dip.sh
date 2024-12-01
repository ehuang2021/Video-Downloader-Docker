#!/bin/bash

# Capture the first argument as the URL
URL=$1
DOWNLOAD_DIR=$2
FILE_TYPE=$3
FILE_QUALITY=$4

# Check if URL is provided
if [ -z "$URL" ]; then
    echo "No URL provided."
    exit 1
fi


# Use yt-dlp to get the filename without downloading
FILENAME=$(yt-dlp --get-filename -o "%(title)s.%(ext)s" "$URL")

if [ "$FILE_TYPE" == "audio" ]; then
FILENAME="${FILENAME%.*}.mp3"
fi

# Perform basic download (best video quality, video file)
if [ "$FILE_TYPE" == "video" ] && [ "$FILE_QUALITY" == "best" ]; then
OUTPUT=$(yt-dlp "$URL" -o "$DOWNLOAD_DIR/$FILENAME" 2>&1)
EXIT_CODE=$?
fi

# Perform download with only audio
if [ "$FILE_TYPE" == "audio" ] && [ "$FILE_QUALITY" == "best" ]; then
OUTPUT=$(yt-dlp -x -o "$DOWNLOAD_DIR/$FILENAME" "$URL" 2>&1)
fi


if [ $EXIT_CODE -ne 0 ]; then
    echo "Error: yt-dlp failed with exit code $EXIT_CODE"
    echo "Error Message: $OUTPUT" | grep "ERROR:"  # Filter and display only error messages
    exit $EXIT_CODE
fi
# Echo the filename back to the caller
echo "$FILENAME"