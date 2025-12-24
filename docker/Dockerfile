# Use an official lightweight Python image
FROM python:3.12-slim

# Prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first (better caching) 
COPY /requirements.txt /app/
# Install Python deps (cached unless requirements.txt changes) 
RUN pip install --upgrade pip \ 
    && pip install -r requirements.txt

COPY /src/cloudflare_updater/ /app/


# Run entrypoint
ENTRYPOINT ["python", "main.py"]
