"""Main.py what more can i say"""

from time import sleep
import os
import logging
import sys

import requests

import update_ip
from check_ip import get_ip
import webhooks

# Set up logging, default to INFO level
LOGGING_LEVEL = os.environ.get("LOG_LEVEL", "INFO").strip().upper()

if LOGGING_LEVEL == "DEBUG":
    LOG_LEVEL = logging.DEBUG
elif LOGGING_LEVEL == "WARNING":
    LOG_LEVEL = logging.WARNING
elif LOGGING_LEVEL == "ERROR":
    LOG_LEVEL = logging.ERROR
elif LOGGING_LEVEL == "CRITICAL":
    LOG_LEVEL = logging.CRITICAL
else:
    LOG_LEVEL = logging.INFO
    LOGGING_LEVEL = "INFO"

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)
logger.critical(f"Logging level set to {LOGGING_LEVEL}") # log the logging level as critical to ensure logged.


logger.info("Service starting up...") # log startup


# Get sleep time from environment variable or use default
sleep_time = int(os.environ.get("CHECK_INTERVAL_SECONDS", 600)) 
logger.info("Check interval set to %s seconds.", sleep_time)

# Get retry interval from environment variable or use default
retry_interval = int(os.environ.get("RETRY_INTERVAL_SECONDS", 10)) # retry interval from environment variable
logger.info("Retry interval set to %s seconds.", retry_interval)


# Get API token from environment variable, check if valid
CLOUDFLARE_API_TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN", None)
if CLOUDFLARE_API_TOKEN:
    r = requests.get("https://api.cloudflare.com/client/v4/user/tokens/verify", timeout=3, headers={"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}"}).json()

    if r.get("success") is False: # check if api key is invalid
        logger.error("Cloudflare API token is invalid, please double check and try again. Exiting.")
        logger.error(r.get("errors"))
        exit(1)
else:
    logger.error("CLOUDFLARE_API_TOKEN environment variable not set. Exiting.")
    exit(1)


# Get WHOAMI_URLS from environment variable or use default
WHOAMI_URLS = os.environ.get("WHOAMI_URLS", "").split(",")
if os.environ.get("OVERRIDE_OBSOLETE_WHOAMI", "false").lower() != "false":
    WHOAMI_URLS.append("http://whoami.obsoletelabs.org:12345/") # default fallback
if not WHOAMI_URLS or WHOAMI_URLS == [""]:
    logger.error("WHOAMI_URLS environment variable empty and obsolete fallback disabled. Exiting.")
    exit(1)
logger.info("Using WHOAMI_URLS: %s", WHOAMI_URLS)


# Get the initial IP address, log, and set as OLD_IP
initial_ip = os.environ.get("INITIAL_IP", get_ip(whoami_urls=WHOAMI_URLS)[1])
logger.info("Initial IP set to: %s", initial_ip)
OLD_IP = initial_ip

# NOTIFIERS!!!
exernal_notifiers = False

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", False)
SMTP_NOTIFIER_ENABLED = os.environ.get("SMTP_NOTIFIER_ENABLED", "false").lower() == "true"

if DISCORD_WEBHOOK_URL:
    exernal_notifiers = True
    logger.info("Discord webhook notifier enabled.")
elif SMTP_NOTIFIER_ENABLED:
    exernal_notifiers = True
    logger.info("SMTP email notifier enabled.")
else:
    logger.info("No external notifiers enabled.")


def notify_ip_change(old_ip, new_ip):
    """Notify IP change via enabled notifiers"""
    if DISCORD_WEBHOOK_URL:
        webhooks.discord(DISCORD_WEBHOOK_URL, f"# WARNING ip {old_ip} CHANGED to {new_ip}!", username="IP notifier")
    # Add other notifiers here as needed


# Notifier debugger
#if DISCORD_WEBHOOK_URL: webhooks.discord(DISCORD_WEBHOOK_URL, f"# WARNING ip DEBUG CHANGED to OTHER DEBUG!", username="IP notifier")


def main():
    """The Main Function"""
    # Main loop
    global OLD_IP
    global exernal_notifiers

    while True:
        logger.info("Checking for IP address change...")

        # Get current IP address with retries
        found = False
        while not found:
            found, current_ip = get_ip(whoami_urls=WHOAMI_URLS) # grab the current ip address
            if found:
                logger.info("Current IP: %s", current_ip)
                break
            logger.warning(f"Could not retrieve current IP address, waiting {retry_interval} seconds.")
            sleep(retry_interval)
        
        # Compare with OLD_IP and update if changed
        try:
            if found and current_ip != OLD_IP: # if ip has changed

                # Ip change detected
                logger.info("IP change detected: %s --> %s", OLD_IP, current_ip)
                # Send notifications if enabled
                if exernal_notifiers:
                    notify_ip_change(OLD_IP, current_ip)

                # Update via Cloudflare API
                try:
                    logger.info("Updating IP address via Cloudflare API...")
                    update_ip.cloudflare(CLOUDFLARE_API_TOKEN, OLD_IP, current_ip)
                except Exception as e:
                    logger.error("Error updating IP address via Cloudflare API: %s", e)

                OLD_IP = current_ip # update OLD_IP
                logger.info("Updated IP address to: %s", current_ip)
        except Exception as e:
            logger.error("Error updating IP address. %s", e)

        logger.info("Sleeping for %s seconds...", sleep_time)
        sleep(sleep_time)  # wait sleeptime between checks



# Run main function
if __name__ == "__main__":
    logger.info("Service running") # log running
    main()
