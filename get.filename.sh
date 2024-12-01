#!/bin/bash

URL=$1
FILE_TYPE=$2



# Use yt-dlp to get the filename
if [ "$FILE_TYPE" == "video" ]; then
FILENAME=$(yt-dlp -x --get-filename -o "%(title)s.%(ext)s" "$URL")
fi

if [ "$FILE_TYPE" == "audio" ]; then
FILENAME=$(yt-dlp -x --get-filename -o "%(title)s.%(ext)s" "$URL")
FILENAME="${FILENAME%.*}.mp3"
fi

# Output only the filename
echo "$FILENAME"