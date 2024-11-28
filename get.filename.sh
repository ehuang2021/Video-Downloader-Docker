#!/bin/bash

URL=$1

# Use yt-dlp to get the filename
FILENAME=$(yt-dlp --get-filename -o "%(title)s.%(ext)s" "$URL")

# Output only the filename
echo "$FILENAME"