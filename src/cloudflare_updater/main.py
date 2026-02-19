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

VERSION = "1.1.0"

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

# TODO: Zings can you please explain the env handler so I can use that instead?
from os import environ
persistent_file_path = environ.get("PERSISTENT_FILE_PATH", "/config/persistent_ip.txt")

# persistent_file_path = env.PERSISTENT_FILE_PATH
try:
    with open(persistent_file_path, "r") as persistent_file:
        for line in persistent_file:
            persistent_ip = line.strip()
        
        if persistent_ip == "":
            first_ever_run_welcome_required = True
        else:
            first_ever_run_welcome_required = False
except:
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
if not first_ever_run_welcome_required:
    logger.info("Previous IP found in persistent storage: %s", persistent_ip)
    init_email_submessage = "INFO: Previous IP found in persistent storage."
    init_email_context.append(init_email_submessage)
    OLD_IP = persistent_ip
elif env.INITIAL_IP:
    logger.warning("Initial IP overwritten by debug value. (Not recemended for production use)")
    init_email_context.append("WARNING: Initial IP overwritten by debug value. (Not recemended for production use)")
    OLD_IP = env.INITIAL_IP
else:
    OLD_IP = get_ip(whoami_urls=WHOAMI_URLS)[0]
logger.info("Initial IP set to: %s", OLD_IP)
init_email_submessage = f"INFO: Initial IP set to: {OLD_IP}"
init_email_context.append(init_email_submessage)

def check_if_local_ip(ip_address):
    """Check if the given IP address is a local/private IP address."""
    import ipaddress

    try:
        ip = ipaddress.ip_address(ip_address)
        return ip.is_private
    except ValueError:
        logger.error("Invalid IP address format: %s", ip_address)
        return False

if check_if_local_ip(OLD_IP):
    local_ip_warning = f"WARNING: The initial IP address {OLD_IP} appears to be a local/private IP address. This may indicate a misconfiguration or an issue with retrieving the public IP address. Please verify your network settings and ensure that the whoami URLs are correctly configured to return the public IP address."
    logger.warning(local_ip_warning)
    init_email_context.append(local_ip_warning)





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


def notify_ip_change(old_ip, new_ip, whoami_name, notifyinformation):
    """Notify IP change via enabled notifiers"""
    logger.debug("Sending webhooks")
    send_webhooks(f"WARNING ip {old_ip} CHANGED to {new_ip}!")
    logger.debug("Done sending webhooks")
    # Add other notifiers here as needed
    if enable_email_notifications:

        critical_string = ""
        normal_string = ""

        for cf_domain, update_info in notifyinformation.items(): # loop through the update information and split it into critical and normal information, this is done to make the email notification look better by grouping successful updates together and failed updates together, rather than having them intermingled which can be hard to read.
            logger.debug(f"Cloudflare Update Info for {cf_domain}: {update_info}")
            if update_info == "Successfully updated.":
                normal_string += f"{cf_domain}: {update_info}<br>"
            else:
                critical_string += f"{cf_domain}: {update_info}<br>"

        if critical_string != "": # only add the header if there is critical information to show, otherwise it just looks bad with a header and no content.
            critical_string = "<br>The following issues were encountered while updating your Cloudflare zones:<br><br>" + critical_string + "<br><br>"
        if normal_string != "": # only add the header if there is normal information to show, otherwise it just looks bad with a header and no content.
            normal_string = "<br>The following zones were successfully updated:<br><br>" + normal_string + "<br><br>"

        notifyinformation_str = critical_string + normal_string # merge critical and normal info, prioritising critical info.

        logger.debug("Sending email notification")
        # notifyinformation_str = "<br>".join(f"{k}: {v}" for k, v in notifyinformation.items()) # replaced to prioritise
        if notifyinformation_str == "":
            notifyinformation_str = "No additional information available - no updates occured."

        mail_context = {
            "Subject": "IP Address Change Detected for " + service_name,
            "Greeting": f"Message from {service_name},<br>",
            "Body": f"Your IP address has changed from {old_ip} to {new_ip}. Whoami service {whoami_name} reported the new IP."
            + "<br><br>Whilst updating zones avaliable to your API token, the updater has got the following information: <br><br>"
            + notifyinformation_str,
        }  # The body takes in HTML formatting
        send_email(mail_context, eemail.email_to)
        logger.debug("Done sending email notification")


# YOU SAID SOMEWHERE HERE U GO
if first_ever_run_welcome_required:
    logger.info("No previous IP found in persistent storage, or no file exists, treating as first run.")
    with open(persistent_file_path, "w") as persistent_file:
        persistent_file.write(OLD_IP)  # write initial IP to persistent storage when first run, ensures restart triggered even if no ip change.
    
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
    logger.info("Previous IP found in persistent storage, treating as restart.")
    # Build HTML-formatted startup notes
    additional_con = "<br>".join(str(item) for item in init_email_context)

    context = {
        "Subject": "Notice of Service Restart for " + service_name,
        "Greeting": f"Message from {service_name},<br>",
        "Body": (
            "Your cloudflare updater service has restarted. Please see the startup notes for more information. <br>"
            " Startup notes: <br>"
            f"{additional_con}"
        ),
    }

    if not env.DISABLE_RESTART_EMAIL:
        send_email(context, eemail.email_to)

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
            current_ip, whoami_name = get_ip(whoami_urls=WHOAMI_URLS)  # grab the current ip address
            if current_ip is not None:
                logger.info("Current IP as reported by %s: %s", whoami_name, current_ip)
                break
            logger.warning("Could not retrieve current IP address, waiting %i seconds.", env.RETRY_INTERVAL_SECONDS)
            sleep(env.RETRY_INTERVAL_SECONDS)

        if check_if_local_ip(current_ip) != check_if_local_ip(old_ip):    
            ip_type_change_warning = f"ERROR: whoami service {whoami_name} reported an IP address type change from {'local/private' if check_if_local_ip(old_ip) else 'public'} ({old_ip}) to {'local/private' if check_if_local_ip(current_ip) else 'public'} ({current_ip}). Update aborted to prevent misconfiguration, will revert back to previous IP address. If this keeps happening, please verify your network settings and ensure that the whoami URLs are correctly configured to return the type of IP address if that is what you expect."
            logger.error(ip_type_change_warning)
            if enable_email_notifications:
                ip_type_change_warning = f"ERROR: whoami service {whoami_name} reported an IP address type change from {'local/private' if check_if_local_ip(old_ip) else 'public'} ({old_ip}) to {'local/private' if check_if_local_ip(current_ip) else 'public'} ({current_ip}). <br><br>Update has been aborted to prevent misconfiguration, and will be restored to previous the IP address ({old_ip}). <br><br>If this keeps happening, please verify your network settings and ensure that the whoami URLs are correctly configured to return the type of IP address if that is what you expect. <br><br>You may need to set (or remove) your INITIAL_IP environment variable to ensure the correct type."
                send_email(
                    {
                        "Subject": f"IP Address Type Change Detected for {service_name}",
                        "Greeting": f"Message from {service_name},<br>",
                        "Body": ip_type_change_warning,
                    },
                    eemail.email_to,
                )
            current_ip = old_ip  # revert back to previous IP to prevent misconfiguration


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

            notify_ip_change(old_ip, current_ip, whoami_name, notifyinformation)
            old_ip = current_ip  # update OLD_IP

            try:
                with open(persistent_file_path, "w") as persistent_file:
                    persistent_file.write(current_ip)  # update persistent storage
            except Exception as e:
                logger.error("Error writing current IP to persistent storage: %s", e)

            logger.info("Updated IP address to: %s", current_ip)

        logger.info("Sleeping for %s seconds...", env.CHECK_INTERVAL_SECONDS)
        sleep(env.CHECK_INTERVAL_SECONDS)  # wait sleeptime between checks
        logger.info("-----------------------------------------------------------------------")


# Run main function
if __name__ == "__main__":
    logger.info("Service started.")
    main()
