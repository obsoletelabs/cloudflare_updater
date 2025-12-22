from time import sleep
import os
from pathlib import Path

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


old_ip = None # initialize old_ip variable

try:
    sleep_time = int(os.environ.get("INTERVAL_SECONDS")) # check interval from environment variable
except:
    sleep_time = 300 # Set default to 5 minutes
logger.info(f"Check interval set to {sleep_time} seconds.")

# Get API token from environment variable
try:
    API_TOKEN = os.environ.get("API_TOKEN")
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

def main():
    # Main loop
    while True:
        logger.info("Checking for IP address change...")

        #API_TOKEN = os.environ.get("API_TOKEN")
        #FILE_PATH = Path("/ip.txt") # location to cache ip addresses

        found, ip = get_ip(WHOAMI_URLS=WHOAMI_URLS) # grab the current ip address
        #print(f"Current IP: {ip}")
        if found:
            logger.info(f"Current IP: {ip}")
        else:
            logger.warning("Could not retrieve current IP address.")

        try:
            if found and ip != old_ip: # if ip has changed
                new_ip = ip
                #print(f"IP change detected: {old_ip} --> {new_ip}")
                logger.info(f"IP change detected: {old_ip} --> {new_ip}")
                update_ip.cloudflare(API_TOKEN, old_ip, new_ip)
                old_ip = ip
                #print(f"Updated cached IP to: {new_ip}")
                logger.info(f"Updated IP address to: {new_ip}")
        except:
            #print("Error updating IP address.")
            logger.error("Error updating IP address.")
        
        logger.info(f"Sleeping for {sleep_time} seconds...")
        sleep(sleep_time)  # wait 5 minutes between checks

    


if __name__ == "__main__": 
    logger.info("Service running")
    main()