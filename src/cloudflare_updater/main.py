"""Main.py what more can i say"""

from time import sleep

import notify.send_email_notification as eemail
import update_ip
from check_ip import get_ip
from notify.send_email_notification import send_email_notification as send_email
from setup_logger import setup_logger
from utilities import env_handler, env_loaders
from utilities.send_webhooks import send as send_webhooks

env = env_handler.Env()
init_email_context = []

VERSION = "1.0.0"

################################
#           LOGGING            #
################################
DEBUG_LOGGER_FORMAT = False  # should be disabled for production

LOG_FILE_PATH = "/config/log.txt"

# Set up logging
LOGGING_LEVEL = env.LOG_LEVEL

logger = setup_logger(
    log_level=LOGGING_LEVEL,
    debug_logger_format=DEBUG_LOGGER_FORMAT,
    enable_color=env.ENABLE_COLORED_LOGGING,
    LogFilePath=LOG_FILE_PATH,
    MaxLogfileSizeBytes=env.MAX_LOG_BYTES,
)

# TODO: make it so that the logs are persistent somehow (mounting?) also add lastrun and currentrun logfile, plus the infinilogger.
# TODO not sure what you mean by this as for persistent they are being stored in a file within the config folder so it should be mounted already
first_ever_run_welcome_required = True


# Get whoami urls
success, WHOAMI_URLS = env_loaders.get_whoami_urls()
if not success:
    exit(1)
logger.info("Using WHOAMI_URLS: %s", WHOAMI_URLS)
init_email_submessage = f"INFO: Using WHOAMI_URLS: {WHOAMI_URLS}"
init_email_context.append(init_email_submessage)

# Get the initial IP address, log, and set as OLD_IP
OLD_IP: str
if env.INITIAL_IP:
    logger.warning("Initial IP overwritten by debug value. (Not recemended for production use)")
    init_email_context.append("WARNING: Initial IP overwritten by debug value. (Not recemended for production use)")
    OLD_IP = env.INITIAL_IP
else:
    OLD_IP = get_ip(whoami_urls=WHOAMI_URLS)
logger.info("Initial IP set to: %s", OLD_IP)
init_email_submessage = f"INFO: Initial IP set to: {OLD_IP}"
init_email_context.append(init_email_submessage)


service_name = env.SERVICE_NAME
logger.info("Service name set to: %s", service_name)
init_email_submessage = f"INFO: Service name set to: {service_name}"
init_email_context.append(init_email_submessage)

################################
#           Notify             #
################################
enable_email_notifications = False
if eemail.smtp_enabled:
    logger.info("SMTP Notifier is enabled.")
    init_email_context.append("INFO: SMTP Notifier is enabled.")
    enable_email_notifications = True


def notify_ip_change(old_ip, new_ip, notifyinformation):
    """Notify IP change via enabled notifiers"""
    logger.debug("Sending webhooks")
    send_webhooks(f"WARNING ip {old_ip} CHANGED to {new_ip}!")
    logger.debug("Done sending webhooks")
    # Add other notifiers here as needed
    if enable_email_notifications:
        logger.debug("Sending email notification")
        notifyinformation_str = "<br>".join(f"{k}: {v}" for k, v in notifyinformation.items())
        if notifyinformation_str == "":
            notifyinformation_str = "No additional information available - no updates occured."

        mail_context = {
            "Subject": "IP Address Change Detected for " + service_name,
            "Greeting": f"Message from {service_name},<br>",
            "Body": f"Your IP address has changed from {old_ip} to {new_ip}. "
            + "<br><br>Whilst updating zones avaliable to your API token, the updater has got the following information: <br><br>"
            + notifyinformation_str,
        }  # The body takes in HTML formatting
        send_email(mail_context, eemail.email_to)
        logger.debug("Done sending email notification")


# YOU SAID SOMEWHERE HERE U GO
if first_ever_run_welcome_required:
    # Build HTML-formatted startup notes
    additional_con = "<br>".join(str(item) for item in init_email_context)

    context = {
        "Subject": "Welcome to your obsoletelabs future, cloudflare dynamic-dns style!",
        "Body": (
            "Hey there! Welcome! We are happy to have you join us in our cloudflare mayhem. <br>"
            " Currently we have a key personell on holiday, and these startup emails require him to return back to the office, "
            "so we will have to give you an idea of what could be to come in our obsolete future. <br>"
            " Best of luck, worst of luck, heres to your obsoletelabs future! <br><br><br>"
            " Startup notes: <br>"
            f"{additional_con}"
        ),
    }

    if not env.DISABLE_WELCOME_EMAIL:
        send_email(context, eemail.email_to)
else:
    logger.critical("OH DEAR GOD THE PROGRAM RESTARTED!!! NO FUTHER CODE WAS WRITTEN TO HANDLE IT?")

################################
#          Main Loop           #
################################


def main():
    """The Main Function"""
    old_ip = OLD_IP  # copy OLD_IP to local namespace
    # Main loop

    while True:
        logger.info("Checking for IP address change...")

        while True:
            current_ip = get_ip(whoami_urls=WHOAMI_URLS)  # grab the current ip address
            if current_ip is not None:
                logger.info("Current IP: %s", current_ip)
                break
            logger.warning("Could not retrieve current IP address, waiting %i seconds.", env.RETRY_INTERVAL_SECONDS)
            sleep(env.RETRY_INTERVAL_SECONDS)

        # Compare with OLD_IP and update if changed
        if current_ip != old_ip:
            # Ip change detected
            logger.warning("IP change detected: %s --> %s", old_ip, current_ip)
            # Send notifications if enabled

            # Update via Cloudflare API
            notifyinformation = {"Error": "Failed to update IP via Cloudflare API."}
            try:
                logger.info("Updating IP address via Cloudflare API...")
                notifyinformation = update_ip.cloudflare(env.CLOUDFLARE_API_TOKEN, old_ip, current_ip)
            except Exception as e:
                logger.critical("Error updating IP address via Cloudflare API: %s", e)

            notify_ip_change(old_ip, current_ip, notifyinformation)
            old_ip = current_ip  # update OLD_IP
            logger.info("Updated IP address to: %s", current_ip)

        logger.info("Sleeping for %s seconds...", env.CHECK_INTERVAL_SECONDS)
        sleep(env.CHECK_INTERVAL_SECONDS)  # wait sleeptime between checks
        logger.info("-----------------------------------------------------------------------")


# Run main function
if __name__ == "__main__":
    logger.info("Service started.")
    main()
