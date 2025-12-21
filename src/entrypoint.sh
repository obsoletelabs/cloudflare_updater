#!/bin/bash
set -e

# Remove quotes if present
CRON_INTERVAL=${CRON_INTERVAL//\"/}

# Default to every 5 minutes if empty
if [ -z "$CRON_INTERVAL" ]; then
    CRON_INTERVAL="*/5 * * * *"
fi

# Write cron job with user field and newline
echo "$CRON_INTERVAL root python3 /app/main.py >> /app/cron.log 2>&1" > /etc/cron.d/mycron
chmod 0644 /etc/cron.d/mycron
crontab /etc/cron.d/mycron

# Show crontab for debugging
crontab -l

# Start cron in foreground
exec cron -f
