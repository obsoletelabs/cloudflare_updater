"""Main.py what more can i say"""
# pylint: disable=global-statement

import os
from time import sleep

import update_ip
from check_ip import get_ip
from setup_logger import setup_logger
from utilities import env_loaders
from utilities.send_webhooks import send as send_webhooks

################################
#           LOGGING            #
################################
DEBUG_LOGGER_FORMAT = False  # should be disabled for production

# Set up logging, default to INFO level
LOGGING_LEVEL = os.environ.get("LOG_LEVEL", "INFO").strip().upper()

logger = setup_logger(LOGGING_LEVEL, DEBUG_LOGGER_FORMAT)


print("################################")
print("#          LOAD ENV            #")
print("################################")

# Get sleep time from environment variable or use default
sleep_time = int(os.environ.get("CHECK_INTERVAL_SECONDS", 600))
logger.info("Check interval set to %s seconds.", sleep_time)


# Get retry interval from environment variable or use default
retry_interval = int(os.environ.get("RETRY_INTERVAL_SECONDS", 10))  # retry interval from environment variable
logger.info("Retry interval set to %s seconds.", retry_interval)


# Get cloudflare api token
success, CLOUDFLARE_API_TOKEN = env_loaders.get_cloudflare_api_token()
if not success:
    exit(1)

# Get whoami urls
success, WHOAMI_URLS = env_loaders.get_whoami_urls()
if not success:
    exit(1)
logger.info("Using WHOAMI_URLS: %s", WHOAMI_URLS)


# Get the initial IP address, log, and set as OLD_IP
initial_ip = os.environ.get("INITIAL_IP", None)
if initial_ip:
    logger.warning("Initial IP overwritten by debug value (Not recemended for production use)")
else:
    initial_ip = get_ip(whoami_urls=WHOAMI_URLS)[1]
logger.info("Initial IP set to: %s", initial_ip)
OLD_IP = initial_ip

################################
#           Notify             #
################################
SMTP_NOTIFIER_ENABLED = os.environ.get("SMTP_NOTIFIER_ENABLED", "false").lower() == "true"


def notify_ip_change(old_ip, new_ip):
    """Notify IP change via enabled notifiers"""
    logger.debug("Sending webhooks")
    send_webhooks(f"WARNING ip {old_ip} CHANGED to {new_ip}!")
    logger.debug("Done sending webhooks")
    # Add other notifiers here as needed


################################
#          Main Loop           #
################################


def main():
    """The Main Function"""
    # Main loop
    global OLD_IP
    # global EXTERNAL_NOTIFIERS

    while True:
        logger.info("Checking for IP address change...")

        # Get current IP address with retries
        found = False  # TODO iceman can you see if this is actually needed anymore?
        while not found:
            current_ip = get_ip(whoami_urls=WHOAMI_URLS)  # grab the current ip address
            if current_ip is not None:
                logger.info("Current IP: %s", current_ip)
                found = True
                break
            logger.warning("Could not retrieve current IP address, waiting %i seconds.", retry_interval)
            sleep(retry_interval)

        # Compare with OLD_IP and update if changed
        if found and current_ip != OLD_IP:  # if ip has changed
            # Ip change detected
            logger.warning("IP change detected: %s --> %s", OLD_IP, current_ip)
            # Send notifications if enabled
            # if EXTERNAL_NOTIFIERS:
            notify_ip_change(OLD_IP, current_ip)

            # Update via Cloudflare API
            try:
                logger.info("Updating IP address via Cloudflare API...")
                update_ip.cloudflare(CLOUDFLARE_API_TOKEN, OLD_IP, current_ip)
            except Exception as e:
                logger.critical("Error updating IP address via Cloudflare API: %s", e)

            OLD_IP = current_ip  # update OLD_IP
            logger.info("Updated IP address to: %s", current_ip)

        logger.info("Sleeping for %s seconds...", sleep_time)
        sleep(sleep_time)  # wait sleeptime between checks


# Run main function
if __name__ == "__main__":
    print("################################")
    print("#      Service running         #")
    print("################################")
    main()
