"""Main.py what more can i say"""
# pylint: disable=global-statement

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

################################
#           LOGGING            #
################################
DEBUG_LOGGER_FORMAT = False  # should be disabled for production

# check if colored logging is enabled
Invalid_color_config = False

# Set up logging
LOGGING_LEVEL = env.LOG_LEVEL

logger = setup_logger(LOGGING_LEVEL, DEBUG_LOGGER_FORMAT, env.ENABLE_COLORED_LOGGING)

# open log file

	
# TODO: make it so that the logs are persistent somehow (mounting?) also add lastrun and currentrun logfile, plus the infinilogger. 
first_ever_run_welcome_required = True

class systemLogger99:
    def debug(self, txt):
        docker_logger.debug(txt)
        with open("logs/logs.txt", "a") as log_file:
        	log_file.write(f"DEBUG: " + txt) # I dont know how to get the time please add that 
    def info(self, txt):
        docker_logger.info(txt)
        with open("logs/logs.txt", "a") as log_file:
        	log_file.write(f"INFO: " + txt) # I dont know how to get the time please add that
    def warn(self, txt):
        docker_logger.warn(txt)
        with open("logs/logs.txt", "a") as log_file:
        	log_file.write(f"WARN: " + txt) # I dont know how to get the time please add that
    def error(self, txt):
        docker_logger.error(txt)
        with open("logs/logs.txt", "a") as log_file:
        	log_file.write(f"ERROR: " + txt) # I dont know how to get the time please add that
    def critical(self, txt):
        docker_logger.critical(txt)
        with open("logs/logs.txt", "a") as log_file:
        	log_file.write(f"CRITICAL: " + txt) # I dont know how to get the time please add that

#logger = systemLogger99()

if Invalid_color_config:
    logger.warning("ENABLE_COLORED_LOGGING is not set to true or false!")
    init_email_context.append("Warning: ENABLE_COLORED_LOGGING is not set to true or false!")

# Get whoami urls
success, WHOAMI_URLS = env_loaders.get_whoami_urls()
if not success:
    exit(1)
logger.info("Using WHOAMI_URLS: %s", WHOAMI_URLS)
init_email_context.append("INFO: Using WHOAMI_URLS: %s", WHOAMI_URLS)


# Get the initial IP address, log, and set as OLD_IP
if env.INITIAL_IP:
    logger.warning("Initial IP overwritten by debug value. (Not recemended for production use)")
    init_email_context.append("WARNING: Initial IP overwritten by debug value. (Not recemended for production use)")
    OLD_IP = env.INITIAL_IP
else:
    OLD_IP = get_ip(whoami_urls=WHOAMI_URLS)
logger.info("Initial IP set to: %s", OLD_IP)
init_email_context.append("INFO: Initial IP set to: %s", OLD_IP)


service_name = env.SERVICE_NAME
logger.info("Service name set to: %s", service_name)
init_email_context.append("INFO: Service name set to: %s", service_name)

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
    #with omg i was about to get it to paste the logs, but no i will because it is useful  
    additional_con = ""
    for item in init_email_context:
        additional_con = additional_con + "\n" + item
	context = {
	"Subject": "Welcome to your obsoletelabs future, cloudflare dynamic-dns style!",
	"Body": f"Hey there! Welcome! We are happy to have you join us in our cloudflare mayhem. \n In the future we will have more content that will go here, think startup logs, think what settings you have set, and more notably, what issues (not terminal) were found in startup. We might even send the terminal issues too if thats useful. \n Other logs that will exist at some point will be a restart email, which will try tell you what happened to make it restart, of course you can ingore an email like that. We might even have a time per IP recorded in your change IP emails, who knows!!!! For now however, key personell are on holiday, and these features require him to return back to the office, so we will have to give you an idea of what could be to come in the future. Best of luck, worst of luck, heres to your obsoletelabs future! \n\n\n Startup notes: \n{additional_con}"
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
    # Main loop
    global OLD_IP
    # global EXTERNAL_NOTIFIERS

    while True:
        logger.info("Checking for IP address change...")

        # Get current IP address with retries
        #found = False  # TODO iceman can you see if this is actually needed anymore? good point, not anymore. a while True is better than a while not found lol
        while True: #not found:
            current_ip = get_ip(whoami_urls=WHOAMI_URLS)  # grab the current ip address
            if current_ip is not None:
                logger.info("Current IP: %s", current_ip)
                #found = True
                break
            logger.warning("Could not retrieve current IP address, waiting %i seconds.", env.RETRY_INTERVAL_SECONDS)
            sleep(env.RETRY_INTERVAL_SECONDS)

        # Compare with OLD_IP and update if changed
        #if found and current_ip != OLD_IP:  # if ip has changed
        if current_ip != OLD_IP:
            # Ip change detected
            logger.warning("IP change detected: %s --> %s", OLD_IP, current_ip)
            # Send notifications if enabled

            # Update via Cloudflare API
            notifyinformation = {"Error": "Failed to update IP via Cloudflare API."}
            try:
                logger.info("Updating IP address via Cloudflare API...")
                notifyinformation = update_ip.cloudflare(env.CLOUDFLARE_API_TOKEN, OLD_IP, current_ip)
            except Exception as e:
                logger.critical("Error updating IP address via Cloudflare API: %s", e)

            notify_ip_change(OLD_IP, current_ip, notifyinformation)
            OLD_IP = current_ip  # update OLD_IP
            logger.info("Updated IP address to: %s", current_ip)

        logger.info("Sleeping for %s seconds...", env.CHECK_INTERVAL_SECONDS)
        sleep(env.CHECK_INTERVAL_SECONDS)  # wait sleeptime between checks


# Run main function
if __name__ == "__main__":
    logger.info("Service started.")
    main()
