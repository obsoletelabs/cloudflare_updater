from time import sleep
import os
from pathlib import Path
import requests

import update_ip
from check_ip import get_ip 

import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

logger.info("Service starting up...")

try:
    sleep_time = int(os.environ.get("INTERVAL_SECONDS")) # check interval from environment variable
except:
    sleep_time = 300 # Set default to 5 minutes
logger.info(f"Check interval set to {sleep_time} seconds.")

# Get API token from environment variable
try:
    API_TOKEN = os.environ.get("API_TOKEN")

    r = requests.get("https://api.cloudflare.com/client/v4/user/tokens/verify", timeout=3, headers="Authorization": f"Bearer {API_TOKEN}").json()

    if data.get("success") is False: # check if api key is invalid
        logger.error("Token is invalid")
        logger.error(data.get("errors"))
        exit(1)
except:
    #print("API_TOKEN environment variable not set. Exiting.")
    logger.error("API_TOKEN environment variable not set. Exiting.")
    exit(1)

try:
    WHOAMI_URLS = os.environ.get("WHOAMI_URLS").split(",")
except:
    WHOAMI_URLS = [
        "http://whoami.obsoletelabs.org:12345/"
    ]
logger.info(f"Using WHOAMI_URLS: {WHOAMI_URLS}")

logger.info("Retrieving initial IP address...")
found, initial_ip = get_ip(WHOAMI_URLS=WHOAMI_URLS)
if found:
    logger.info(f"Initial IP: {initial_ip}")
    old_ip = initial_ip
else:
    logger.warning("Could not retrieve initial IP address. Will default to 0.0.0.0, will update on first successful check.")
    old_ip = "0.0.0.0" # initialize old_ip variable

def main():
    # Main loop
    global old_ip

    while True:
        logger.info("Checking for IP address change...")

        #API_TOKEN = os.environ.get("API_TOKEN")
        #FILE_PATH = Path("/ip.txt") # location to cache ip addresses

        found, current_ip = get_ip(WHOAMI_URLS=WHOAMI_URLS) # grab the current ip address
        #print(f"Current IP: {ip}")
        if found:
            logger.info(f"Current IP: {current_ip}")
        else:
            logger.warning("Could not retrieve current IP address.")

        try:
            #logger.info(f"Old IP: {old_ip}")
            if found and current_ip != old_ip: # if ip has changed

                logger.info(f"IP change detected: {old_ip} --> {current_ip}")
                try:
                    logger.info("Updating IP address via Cloudflare API...")
                    #print("Updating IP address via Cloudflare API...")
                    update_ip.cloudflare(API_TOKEN, old_ip, current_ip)
                except Exception as e:
                    logger.error(f"Error updating IP address via Cloudflare API: {e}")
                    #print(f"Error updating IP address via Cloudflare API: {e}")

                old_ip = current_ip
                #print(f"Updated cached IP to: {new_ip}")
                logger.info(f"Updated IP address to: {current_ip}")
        except:
            #print("Error updating IP address.")
            logger.error("Error updating IP address.")
        
        logger.info(f"Sleeping for {sleep_time} seconds...")
        sleep(sleep_time)  # wait 5 minutes between checks

    


if __name__ == "__main__": 
    logger.info("Service running")
    main()