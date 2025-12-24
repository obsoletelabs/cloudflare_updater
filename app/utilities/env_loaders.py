"""Code to import environment variables and verify them"""

import logging
from os import environ

import requests

logger = logging.getLogger(__name__)


def get_cloudflare_api_token():
    """Get API token from environment variable, check if valid"""

    cloudflare_api_token = environ.get("CLOUDFLARE_API_TOKEN", None)
    if cloudflare_api_token:
        r = requests.get("https://api.cloudflare.com/client/v4/user/tokens/verify",
            timeout=3, headers={"Authorization": f"Bearer {cloudflare_api_token}"}).json()

        if r.get("success") is False: # check if api key is invalid
            logger.error("Cloudflare API token is invalid, please double check and try again. Exiting.")
            logger.error(r.get("errors"))
            return(False, None)
        return (True, cloudflare_api_token)
    else:
        logger.error("CLOUDFLARE_API_TOKEN environment variable not set. Exiting.")
        return(False, None)
    logger.info("Cloudflare API token validated.")


def get_whoami_urls():
    """Get WHOAMI_URLS from environment variable or use default"""

    whoami_urls = environ.get("WHOAMI_URLS", "").split(",")
    if environ.get("OVERRIDE_OBSOLETE_WHOAMI", "false").lower() == "false":
        whoami_urls.append("http://whoami.obsoletelabs.org:12345/") # default fallback
    else:
        logger.info("Obsolete WHOAMI URL NOT appended due to OVERRIDE_OBSOLETE_WHOAMI setting.")

    if whoami_urls == [""]:
        logger.error("WHOAMI_URLS environment variable empty and obsolete fallback disabled. Exiting.")
        return(False, None)

    # Validate whoami_urls
    for url in whoami_urls:
        if url == "":
            whoami_urls.remove(url)
        elif not url.startswith("http://") and not url.startswith("https://"):
            logger.warning("Invalid WHOAMI_URL detected and removed: %s", url)
            whoami_urls.remove(url)

    return(True, whoami_urls)
