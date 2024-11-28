# Use an official Python runtime as a parent image
FROM python:3.11-slim-bullseye

# Install system dependencies
RUN apt-get update && \
    apt-get install -y ffmpeg curl && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --upgrade pip

# Install yt-dlp using pip
RUN pip install --no-cache-dir yt-dlp

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Ensure scripts are executable
RUN chmod +x yt.dip.sh
RUN chmod +x get.filename.sh

# Create downloads directory
RUN mkdir -p /downloads

# Set the downloads directory as a volume
VOLUME ["/downloads"]

# Expose the application port
EXPOSE 4999

# Run the Flask application
CMD ["python", "app.py"]