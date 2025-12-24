"""Code to import environment variables and verify them"""

import logging
from os import environ
import requests

logger = logging.getLogger(__name__)


def get_cloudflare_api_token():
    """Get API token from environment variable, check if valid"""

    CLOUDFLARE_API_TOKEN = environ.get("CLOUDFLARE_API_TOKEN", None)
    if CLOUDFLARE_API_TOKEN:
        r = requests.get("https://api.cloudflare.com/client/v4/user/tokens/verify", timeout=3, headers={"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}"}).json()

        if r.get("success") is False: # check if api key is invalid
            logger.error("Cloudflare API token is invalid, please double check and try again. Exiting.")
            logger.error(r.get("errors"))
            return(False, None)
        return (True, CLOUDFLARE_API_TOKEN)
    else:
        logger.error("CLOUDFLARE_API_TOKEN environment variable not set. Exiting.")
        return(False, None)
    logger.info("Cloudflare API token validated.")

def get_whoami_urls():
    """Get WHOAMI_URLS from environment variable or use default"""

    WHOAMI_URLS = environ.get("WHOAMI_URLS", "").split(",")
    if environ.get("OVERRIDE_OBSOLETE_WHOAMI", "false").lower() == "false":
        WHOAMI_URLS.append("http://whoami.obsoletelabs.org:12345/") # default fallback
    else:
        logger.info("Obsolete WHOAMI URL NOT appended due to OVERRIDE_OBSOLETE_WHOAMI setting.")

    if WHOAMI_URLS == [""]:
        logger.error("WHOAMI_URLS environment variable empty and obsolete fallback disabled. Exiting.")
        return(False, None)

    # Validate WHOAMI_URLS
    for URL in WHOAMI_URLS:
        if URL == "":
            WHOAMI_URLS.remove(URL)
        elif not URL.startswith("http://") and not URL.startswith("https://"):
            logger.warning("Invalid WHOAMI_URL detected and removed: %s", URL)
            WHOAMI_URLS.remove(URL)

    return(True, WHOAMI_URLS)
