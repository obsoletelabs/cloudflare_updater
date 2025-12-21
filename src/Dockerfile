# Use an official lightweight Python image
FROM python:3.12-slim

# Prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set default cron interval (every 5 minutes)
ENV CRON_INTERVAL="*/5 * * * *"

# Set the working directory
WORKDIR /app

# Install system dependencies and cron
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       cron \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Add entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Run entrypoint
ENTRYPOINT ["/entrypoint.sh"]
