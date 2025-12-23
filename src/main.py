from time import sleep
import os
import logging
import sys

import requests

import update_ip
from check_ip import get_ip 
import webhooks


LOGGING_LEVEL = os.environ.get("LOGGING_LEVEL", None).strip()

if LOGGING_LEVEL == "DEBUG": LOG_LEVEL = logging.DEBUG
elif LOGGING_LEVEL == "INFO": LOG_LEVEL = logging.INFO
elif LOGGING_LEVEL == "WARNING": LOG_LEVEL = logging.WARNING
elif LOGGING_LEVEL == "ERROR": LOG_LEVEL = logging.ERROR
elif LOGGING_LEVEL == "CRITICAL": LOG_LEVEL = logging.CRITICAL

else:
    print("Log level not set defaulting to WARNING") 
    LOG_LEVEL = logging.WARNING
print(f"Logging level set to {LOGGING_LEVEL}")

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

logger.info("Service starting up...")


sleep_time = int(os.environ.get("INTERVAL_SECONDS", 300)) # check interval from environment variable

logger.info("Check interval set to %s seconds.", sleep_time)

# Get API token from environment variable
CLOUDFLARE_API_TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN", None)
if CLOUDFLARE_API_TOKEN:
    r = requests.get("https://api.cloudflare.com/client/v4/user/tokens/verify", timeout=3, headers={"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}"}).json()

    if r.get("success") is False: # check if api key is invalid
        logger.error("Token is invalid")
        logger.error(r.get("errors"))
        exit(1)
else:
    logger.error("CLOUDFLARE_API_TOKEN environment variable not set. Exiting.")
    exit(1)


# NOTIFIERS!!!
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", None)



WHOAMI_URLS = os.environ.get("WHOAMI_URLS", "http://whoami.obsoletelabs.org:12345").split(",")
logger.info("Using WHOAMI_URLS: %s", WHOAMI_URLS)


logger.info("Retrieving initial IP address...")
foundIP, initial_ip = get_ip(whoami_urls=WHOAMI_URLS)
if foundIP:
    logger.info("Initial IP: %s", initial_ip)
    old_ip = initial_ip
else:
    logger.warning("Could not retrieve initial IP address. Will default to 0.0.0.0, will update on first successful check.")
    old_ip = "0.0.0.0" # initialize old_ip variable


# Notifier debugger
#if DISCORD_WEBHOOK_URL: webhooks.discord(DISCORD_WEBHOOK_URL, f"# WARNING ip DEBUG CHANGED to OTHER DEBUG!", username="IP notifier")

DEBUG_IP = os.environ.get("DEBUG_IP", None)


def main():
    # Main loop
    global old_ip # is this needed?
    if DEBUG_IP: old_ip = DEBUG_IP # A special debug ip used to verify ip change logic

    while True:
        logger.info("Checking for IP address change...")

        #CLOUDFLARE_API_TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN")
        #FILE_PATH = Path("/ip.txt") # location to cache ip addresses

        found, current_ip = get_ip(whoami_urls=WHOAMI_URLS) # grab the current ip address
        if found:
            logger.info("Current IP: %s", current_ip)
        else:
            logger.warning("Could not retrieve current IP address.")

        try:
            logger.debug("Old IP: %s", old_ip)
            if found and current_ip != old_ip: # if ip has changed

                # Ip change detected
                logger.info("IP change detected: %s --> %s", old_ip, current_ip)

                if DISCORD_WEBHOOK_URL:
                    webhooks.discord(DISCORD_WEBHOOK_URL, f"# WARNING ip {old_ip} CHANGED to {current_ip}!", username="IP notifier")


                try:
                    logger.info("Updating IP address via Cloudflare API...")
                    update_ip.cloudflare(CLOUDFLARE_API_TOKEN, old_ip, current_ip)
                except Exception as e:
                    logger.error("Error updating IP address via Cloudflare API: %s", e)

                old_ip = current_ip
                logger.info("Updated IP address to: %s", current_ip)
        except Exception as e:
            logger.error("Error updating IP address. %s", e)

        logger.info("Sleeping for %s seconds...", sleep_time)
        sleep(sleep_time)  # wait 5 minutes between checks




if __name__ == "__main__": 
    logger.info("Service running")
    main()
