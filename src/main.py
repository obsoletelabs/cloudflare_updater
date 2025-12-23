from time import sleep
import os
import logging
import sys

import requests

import update_ip
from check_ip import get_ip 
import webhooks



logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

logger.info("Service starting up...")


sleep_time = int(os.environ.get("INTERVAL_SECONDS", 300)) # check interval from environment variable

logger.info(f"Check interval set to {sleep_time} seconds.")

# Get API token from environment variable
API_TOKEN = os.environ.get("API_TOKEN", None)
if API_TOKEN:
    r = requests.get("https://api.cloudflare.com/client/v4/user/tokens/verify", timeout=3, headers={"Authorization": f"Bearer {API_TOKEN}"}).json()

    if r.get("success") is False: # check if api key is invalid
        logger.error("Token is invalid")
        logger.error(r.get("errors"))
        exit(1)
else:
    logger.error("API_TOKEN environment variable not set. Exiting.")
    exit(1)


# NOTIFIERS!!!
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", None)



WHOAMI_URLS = os.environ.get("WHOAMI_URLS", "http://whoami.obsoletelabs.org:12345").split(",")
logger.info(f"Using WHOAMI_URLS: {WHOAMI_URLS}")


logger.info("Retrieving initial IP address...")
foundIP, initial_ip = get_ip(WHOAMI_URLS=WHOAMI_URLS)
if foundIP:
    logger.info(f"Initial IP: {initial_ip}")
    old_ip = initial_ip
else:
    logger.warning("Could not retrieve initial IP address. Will default to 0.0.0.0, will update on first successful check.")
    old_ip = "0.0.0.0" # initialize old_ip variable


# Notifier debugger
#if DISCORD_WEBHOOK_URL: webhooks.discord(DISCORD_WEBHOOK_URL, f"# WARNING ip DEBUG CHANGED to OTHER DEBUG!", username="IP notifier")




def main():
    # Main loop
    global old_ip

    while True:
        logger.info("Checking for IP address change...")

        #API_TOKEN = os.environ.get("API_TOKEN")
        #FILE_PATH = Path("/ip.txt") # location to cache ip addresses

        found, current_ip = get_ip(WHOAMI_URLS=WHOAMI_URLS) # grab the current ip address
        if found:
            logger.info(f"Current IP: {current_ip}")
        else:
            logger.warning("Could not retrieve current IP address.")

        try:
            #logger.info(f"Old IP: {old_ip}")
            if found and current_ip != old_ip: # if ip has changed

                # Ip change detected
                logger.info(f"IP change detected: {old_ip} --> {current_ip}")

                if DISCORD_WEBHOOK_URL: webhooks.discord(DISCORD_WEBHOOK_URL, f"# WARNING ip {old_ip} CHANGED to {current_ip}!", username="IP notifier")


                try:
                    logger.info("Updating IP address via Cloudflare API...")
                    update_ip.cloudflare(API_TOKEN, old_ip, current_ip)
                except Exception as e:
                    logger.error(f"Error updating IP address via Cloudflare API: {e}")

                old_ip = current_ip
                logger.info(f"Updated IP address to: {current_ip}")
        except:
            logger.error("Error updating IP address.")

        logger.info(f"Sleeping for {sleep_time} seconds...")
        sleep(sleep_time)  # wait 5 minutes between checks




if __name__ == "__main__": 
    logger.info("Service running")
    main()
